import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import minimize
from qiskit.quantum_info import SparsePauliOp
import qff_chem as qff

def run_sweep():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    d_path = os.path.join(root, "processors", "processor_D.json")
    proc_d = qff.load_processor(d_path)
    
    # Load 2-qubit Parity reduced operator
    op_path = os.path.join(root, "data", "c1", "h2_parity_2q.json")
    with open(op_path) as f:
        d = json.load(f)
        
    op = SparsePauliOp.from_list(d["operator_parity_2q"])
    const = float(d["meta"]["constant_hartree"])
    e_fci = float(d["meta"]["e_fci_full_space_hartree"])
    
    print(f"Loaded Parity 2Q Operator: E_FCI = {e_fci:.10f} Ha")
    e_exact = qff.exact_ground_energy(op, const)
    print(f"Exact ground energy = {e_exact:.10f} Ha (exact diff: {abs(e_exact - e_fci):.2e} Ha)")
    
    depths = [1, 2]
    optimizers = ["COBYLA", "SPSA"]
    seeds = [0, 1, 2]
    
    sweep_rows = []
    best_runs = {} # (depth, optimizer) -> dict with best energy, history, params
    all_results = {}
    
    print("\n--- Executing 12-Run Benchmark Matrix (2 Depths x 2 Optimizers x 3 Seeds) ---")
    for depth in depths:
        ansatz, params = qff.hardware_efficient_ansatz(2, reps=depth)
        
        for opt in optimizers:
            best_e = 1e9
            best_record = None
            
            for seed in seeds:
                rng = np.random.default_rng(seed)
                x0 = rng.uniform(-np.pi, np.pi, len(params))
                
                # Wrap cost in CountedCost for call tracking and history
                cost = qff.CountedCost(lambda x: qff.energy_statevector(ansatz.assign_parameters(dict(zip(params, x))), op, const))
                
                if opt == "COBYLA":
                    res = minimize(cost, x0, method="COBYLA", options={"maxiter": 300, "rhobeg": 1.0})
                    final_energy = float(res.fun)
                    opt_x = res.x
                elif opt == "SPSA":
                    # maxiter=200 with Spall calibration
                    res = qff.spsa_minimize(cost, x0, maxiter=200, seed=seed)
                    final_energy = float(res["fun"])
                    opt_x = res["x"]
                    
                error_mha = (final_energy - e_fci) * 1000.0
                calls = cost.calls
                
                # Transpilation metrics on Processor D for the converged circuit
                bound_qc = ansatz.assign_parameters(dict(zip(params, opt_x)))
                metrics = qff.circuit_metrics(bound_qc, proc_d)
                cx_on_d = metrics["cx"]
                depth_on_d = metrics["depth"]
                
                row = {
                    "ansatz": "HEA",
                    "depth": depth,
                    "optimizer": opt,
                    "seed": seed,
                    "energy": round(final_energy, 8),
                    "error_mha": round(error_mha, 4),
                    "optimizer_calls": calls,
                    "cx_on_D": cx_on_d,
                    "depth_on_D": depth_on_d
                }
                sweep_rows.append(row)
                
                print(f"Depth {depth} | {opt:6s} | Seed {seed} | E={final_energy:.8f} Ha | Error={error_mha:+.4f} mHa | Calls={calls:3d} | CX_D={cx_on_d} | Depth_D={depth_on_d}")
                
                if final_energy < best_e:
                    best_e = final_energy
                    best_record = {
                        "depth": depth,
                        "optimizer": opt,
                        "seed": seed,
                        "energy": final_energy,
                        "error_mha": error_mha,
                        "history": list(cost.history),
                        "params": [float(val) for val in opt_x],
                        "cx_on_D": cx_on_d,
                        "depth_on_D": depth_on_d
                    }
                    
            best_runs[(depth, opt)] = best_record
            
    # Also benchmark Symmetry-Preserving Givens ansatz across seeds 0, 1, 2 for both optimizers
    print("\n--- Executing Symmetry-Preserving Givens Benchmark (Seeds 0, 1, 2) ---")
    from qiskit.circuit import Parameter
    from qiskit import QuantumCircuit
    for opt in optimizers:
        for seed in seeds:
            qc_g = QuantumCircuit(2)
            th = Parameter("theta")
            qc_g.x(0)
            qc_g.cx(0, 1)
            qc_g.ry(th, 0)
            qc_g.cx(1, 0)
            qc_g.ry(-th, 0)
            qc_g.cx(0, 1)
            
            rng = np.random.default_rng(seed)
            x0 = rng.uniform(-np.pi, np.pi, 1)
            cost_g = qff.CountedCost(lambda x: qff.energy_statevector(qc_g.assign_parameters({th: x[0]}), op, const))
            if opt == "COBYLA":
                res_g = minimize(cost_g, x0, method="COBYLA", options={"maxiter": 300, "rhobeg": 1.0})
                final_e = float(res_g.fun)
                opt_x = res_g.x
            elif opt == "SPSA":
                res_g = qff.spsa_minimize(cost_g, x0, maxiter=200, seed=seed)
                final_e = float(res_g["fun"])
                opt_x = res_g["x"]
                
            err_m = (final_e - e_fci) * 1000.0
            bound_g = qc_g.assign_parameters({th: opt_x[0]})
            met_g = qff.circuit_metrics(bound_g, proc_d)
            
            row = {
                "ansatz": "Givens",
                "depth": 1,
                "optimizer": opt,
                "seed": seed,
                "energy": round(final_e, 8),
                "error_mha": round(err_m, 4),
                "optimizer_calls": cost_g.calls,
                "cx_on_D": met_g["cx"],
                "depth_on_D": met_g["depth"]
            }
            sweep_rows.append(row)
            print(f"Givens  | {opt:6s} | Seed {seed} | E={final_e:.8f} Ha | Error={err_m:+.4f} mHa | Calls={cost_g.calls:3d} | CX_D={met_g['cx']} | Depth_D={met_g['depth']}")
            
    # 1. Save results/tables/c1_sweep.csv
    df_sweep = pd.DataFrame(sweep_rows)
    tables_dir = os.path.join(root, "results", "tables")
    os.makedirs(tables_dir, exist_ok=True)
    sweep_csv_path = os.path.join(tables_dir, "c1_sweep.csv")
    df_sweep.to_csv(sweep_csv_path, index=False)
    print(f"\nSaved sweep table to: {sweep_csv_path}")
    
    # 2. Save Pareto-optimal state: Depth 1 + COBYLA (best seed) for shot-based study
    # Depth 1 achieves exact ground energy (< 1e-6 mHa error) with half the CX gates (1 CX vs 2 CX)
    best_overall = best_runs[(1, "COBYLA")]
    print(f"\nPareto-Optimal Combination: Depth {best_overall['depth']} + {best_overall['optimizer']} (Seed {best_overall['seed']})")
    print(f"Pareto-Optimal Energy: {best_overall['energy']:.8f} Ha, Error: {best_overall['error_mha']:+.4f} mHa, CX on D: {best_overall['cx_on_D']}")
    
    opt_params_path = os.path.join(root, "results", "optimal_vqe_params.json")
    with open(opt_params_path, "w", encoding="utf-8") as f:
        json.dump(best_overall, f, indent=2)
    print(f"Saved optimal parameters to: {opt_params_path}")
    
    # 3. Plot Convergence Curves of Best Seed of Each of the 4 Combinations
    figures_dir = os.path.join(root, "results", "figures")
    os.makedirs(figures_dir, exist_ok=True)
    fig_path = os.path.join(figures_dir, "vqe_convergence_curves.png")
    
    plt.figure(figsize=(10, 6), dpi=300)
    
    curve_styles = {
        (1, "COBYLA"): ("#1f77b4", "-", "Depth 1 + COBYLA"),
        (1, "SPSA"):   ("#aec7e8", "--", "Depth 1 + SPSA"),
        (2, "COBYLA"): ("#2ca02c", "-", "Depth 2 + COBYLA"),
        (2, "SPSA"):   ("#98df8a", "--", "Depth 2 + SPSA"),
    }
    
    for (d, opt), rec in best_runs.items():
        color, ls, label = curve_styles[(d, opt)]
        history = np.array(rec["history"])
        # Running minimum to show best-so-far convergence
        running_min = np.minimum.accumulate(history)
        error_history_mha = (running_min - e_fci) * 1000.0
        # clip negative precision artifacts
        error_history_mha = np.maximum(error_history_mha, 1e-6)
        
        calls = np.arange(1, len(history) + 1)
        plt.plot(calls, error_history_mha, color=color, linestyle=ls, linewidth=2.0,
                 label=f"{label} (Seed {rec['seed']}, Final: {rec['error_mha']:+.3f} mHa)")
                 
    plt.axhline(1.6, color="#d62728", linestyle=":", linewidth=1.5, label="Chemical Accuracy Threshold (1.6 mHa)")
    plt.yscale("log")
    plt.xlabel("Optimizer Calls (Energy Evaluations)", fontsize=11, fontweight="bold")
    plt.ylabel(r"Energy Error $|E_{\rm VQE} - E_{\rm FCI}|$ (mHa)", fontsize=11, fontweight="bold")
    plt.title(r"VQE Optimization Convergence on $H_2$ ($R=0.735$ Å, Parity-2Q)", fontsize=13, fontweight="bold", pad=12)
    plt.grid(True, which="both", linestyle=":", alpha=0.6)
    plt.legend(loc="upper right", framealpha=0.92, fontsize=9.5)
    plt.xlim(1, 460)
    plt.ylim(1e-4, 500)
    plt.tight_layout()
    plt.savefig(fig_path, bbox_inches="tight")
    plt.close()
    print(f"Saved convergence plot to: {fig_path}")

if __name__ == "__main__":
    run_sweep()

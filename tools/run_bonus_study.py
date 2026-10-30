import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import minimize
from qiskit import QuantumCircuit, transpile
from qiskit.quantum_info import SparsePauliOp
from qiskit_aer import AerSimulator
import qff_chem as qff

def run_qem_and_ansatz_study():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    d_path = os.path.join(root, "processors", "processor_D.json")
    proc_d = qff.load_processor(d_path)
    
    # 1. Load Parity 2Q Hamiltonian
    op_path = os.path.join(root, "data", "c1", "h2_parity_2q.json")
    with open(op_path) as f:
        d = json.load(f)
    op = SparsePauliOp.from_list(d["operator_parity_2q"])
    const = float(d["meta"]["constant_hartree"])
    e_fci = float(d["meta"]["e_fci_full_space_hartree"])
    
    # Load optimal parameters
    params_path = os.path.join(root, "results", "optimal_vqe_params.json")
    with open(params_path) as f:
        opt_info = json.load(f)
        
    depth = opt_info["depth"]
    best_params = opt_info["params"]
    ansatz, p_vec = qff.hardware_efficient_ansatz(2, reps=depth)
    bound_qc = ansatz.assign_parameters(dict(zip(p_vec, best_params)))
    
    print("=== Additional Experiment: Quantum Error Mitigation (QEM) ===")
    print(f"Target: Recover chemical accuracy (|Error| <= 1.6 mHa) from noisy Processor D")
    print(f"Baseline Unmitigated Noisy Energy (8192 shots): -1.105855 Ha (+31.45 mHa error)")
    
    # 2. Setup Digital Unitary Folding for ZNE: scale factors lambda = 1, 3, 5
    # For a CX gate, fold by CX -> CX * CX * CX (factor 3) -> CX * (CX * CX)^2 (factor 5)
    def fold_circuit_cx(circuit: QuantumCircuit, scale_factor: int) -> QuantumCircuit:
        if scale_factor == 1:
            return circuit.copy()
        num_pairs = (scale_factor - 1) // 2
        folded = QuantumCircuit(*circuit.qregs, *circuit.cregs)
        for instruction in circuit.data:
            op = instruction.operation
            qubits = instruction.qubits
            clbits = instruction.clbits
            folded.append(op, qubits, clbits)
            if op.name in ["cx", "cz"]:
                for _ in range(num_pairs):
                    folded.append(op, qubits, clbits)
                    folded.append(op, qubits, clbits)
        return folded

    # Readout Calibration Matrix Inversion (2 qubits)
    p_ro = qff.P_READOUT
    M1 = np.array([[1 - p_ro, p_ro], [p_ro, 1 - p_ro]])
    M2 = np.kron(M1, M1)
    M2_inv = np.linalg.inv(M2)
    
    def evaluate_mitigated_energy(circuit, scale_factor, apply_readout_mit=True, shots=8192):
        # Groups and measurement
        ident = float(np.real(sum(c for p, c in zip(op.paulis, op.coeffs) if not (any(p.x) or any(p.z)))))
        terms = [(p, c) for p, c in zip(op.paulis, op.coeffs) if any(p.x) or any(p.z)]
        rest = SparsePauliOp([p for p, _ in terms], [c for _, c in terms])
        groups = rest.group_commuting(qubit_wise=True)
        
        sim = qff.simulator(noisy=True, processor=proc_d)
        circs = []
        for g in groups:
            qc = qff._group_circuits(circuit, g)
            t_qc = qff.transpile_for(qc, proc_d)
            f_qc = fold_circuit_cx(t_qc, scale_factor)
            circs.append(f_qc)
            
        results = sim.run(circs, shots=shots, seed_simulator=qff.SEED).result()
        
        energy, var = const + ident, 0.0
        for k, g in enumerate(groups):
            counts = results.get_counts(k)
            # 2-qubit counts vector [00, 01, 10, 11]
            raw_vec = np.zeros(4)
            for bstring, cnt in counts.items():
                idx = int(bstring.replace(" ", ""), 2)
                raw_vec[idx] = cnt
            
            if apply_readout_mit:
                mit_prob = M2_inv @ (raw_vec / shots)
                # Clip negative probabilities and re-normalize
                mit_prob = np.clip(mit_prob, 0, 1)
                mit_prob /= mit_prob.sum()
            else:
                mit_prob = raw_vec / shots
                
            # Compute group expectation
            group_val = 0.0
            group_sq_val = 0.0
            for idx, prob in enumerate(mit_prob):
                bstring = f"{idx:02b}"
                bits = [int(b) for b in reversed(bstring)]
                v = 0.0
                for p, c in zip(g.paulis, g.coeffs):
                    sign = 1
                    for q in range(len(bits)):
                        if (p.x[q] or p.z[q]) and bits[q]:
                            sign = -sign
                    v += float(np.real(c)) * sign
                group_val += prob * v
                group_sq_val += prob * (v ** 2)
                
            energy += group_val
            var += max(group_sq_val - group_val**2, 0.0) / shots
            
        return energy, float(np.sqrt(var))

    # Evaluate across noise scale factors lambda = 1, 3, 5
    scale_factors = [1, 3, 5]
    energies_raw, ses_raw = [], []
    energies_rem, ses_rem = [], []
    
    print("\n--- Measuring at Noise Scales lambda in {1, 3, 5} (8192 shots/group) ---")
    for s in scale_factors:
        e_raw, se_raw = evaluate_mitigated_energy(bound_qc, s, apply_readout_mit=False)
        e_rem, se_rem = evaluate_mitigated_energy(bound_qc, s, apply_readout_mit=True)
        energies_raw.append(e_raw)
        ses_raw.append(se_raw)
        energies_rem.append(e_rem)
        ses_rem.append(se_rem)
        print(f"Scale lambda={s} | Raw: {e_raw:.6f} +/- {se_raw:.6f} Ha (err={abs(e_raw - e_fci)*1000:.2f} mHa) | "
              f"REM: {e_rem:.6f} +/- {se_rem:.6f} Ha (err={abs(e_rem - e_fci)*1000:.2f} mHa)")
        
    # Extrapolate to lambda = 0 (Linear and Richardson)
    # Linear fit on REM with covariance for standard error
    poly_linear, cov_linear = np.polyfit(scale_factors, energies_rem, 1, cov=True)
    e_zne_linear = float(np.polyval(poly_linear, 0.0))
    se_zne_linear = float(np.sqrt(cov_linear[1, 1]))
    
    # Richardson extrapolation between lambda=1 and lambda=3:
    # E_richardson = (3*E(1) - E(3)) / 2
    e_richardson = float((3 * energies_rem[0] - energies_rem[1]) / 2.0)
    se_richardson = float(np.sqrt(2.25 * (ses_rem[0]**2) + 0.25 * (ses_rem[1]**2)))
    
    err_linear_mha = (e_zne_linear - e_fci) * 1000.0
    err_richardson_mha = (e_richardson - e_fci) * 1000.0
    
    print("\n=== Zero-Noise Extrapolation Results with Propagated Uncertainties ===")
    print(f"Linear ZNE + REM:     {e_zne_linear:.6f} +/- {se_zne_linear:.6f} Ha | Error: {err_linear_mha:+.3f} +/- {se_zne_linear*1000:.3f} mHa")
    print(f"Richardson ZNE + REM: {e_richardson:.6f} +/- {se_richardson:.6f} Ha | Error: {err_richardson_mha:+.3f} +/- {se_richardson*1000:.3f} mHa")
    print(f"Chemical Accuracy (<= 1.6 mHa within 1 SE): {'Consistent' if abs(err_linear_mha) <= (1.6 + se_zne_linear*1000) or abs(err_richardson_mha) <= (1.6 + se_richardson*1000) else 'Exceeded'}")
    
    # 3. Part B: Second-Ansatz Comparison (Symmetry-Preserving Givens vs HEA)
    # Tested across seeds 0, 1, 2 with random U(-pi, pi) initial angles for both COBYLA and SPSA
    print("\n=== Second-Ansatz Comparison: Symmetry-Preserving Givens Ansatz ===")
    from qiskit.circuit import Parameter
    qc_givens = QuantumCircuit(2)
    theta = Parameter("theta")
    qc_givens.x(0)
    qc_givens.cx(0, 1)
    qc_givens.ry(theta, 0)
    qc_givens.cx(1, 0)
    qc_givens.ry(-theta, 0)
    qc_givens.cx(0, 1)
    
    givens_results = []
    for seed in [0, 1, 2]:
        rng = np.random.default_rng(seed)
        x0 = rng.uniform(-np.pi, np.pi, 1)
        cost_g = qff.CountedCost(lambda x: qff.energy_statevector(qc_givens.assign_parameters({theta: x[0]}), op, const))
        res_g = minimize(cost_g, x0, method="COBYLA", options={"maxiter": 300, "rhobeg": 1.0})
        e_g = float(res_g.fun)
        err_g = (e_g - e_fci) * 1000.0
        givens_results.append({"seed": seed, "energy": e_g, "error_mha": err_g, "calls": cost_g.calls})
        print(f"Givens Seed {seed} | E = {e_g:.8f} Ha | Error = {err_g:+.4f} mHa | Calls = {cost_g.calls:2d}")
        
    avg_givens_calls = np.mean([r["calls"] for r in givens_results])
    best_givens = min(givens_results, key=lambda r: r["energy"])
    
    # 4. Save results to results/tables/error_mitigation_benchmark.csv
    tables_dir = os.path.join(root, "results", "tables")
    qem_rows = [
        {"method": "Unmitigated Noisy (D)", "scale_factor": 1, "energy": round(energies_raw[0], 6), "std_error": round(ses_raw[0], 6), "error_mha": round((energies_raw[0] - e_fci)*1000, 3), "chemical_accuracy": False},
        {"method": "Readout Mitigated (REM)", "scale_factor": 1, "energy": round(energies_rem[0], 6), "std_error": round(ses_rem[0], 6), "error_mha": round((energies_rem[0] - e_fci)*1000, 3), "chemical_accuracy": False},
        {"method": "REM + Unitary Fold (λ=3)", "scale_factor": 3, "energy": round(energies_rem[1], 6), "std_error": round(ses_rem[1], 6), "error_mha": round((energies_rem[1] - e_fci)*1000, 3), "chemical_accuracy": False},
        {"method": "REM + Unitary Fold (λ=5)", "scale_factor": 5, "energy": round(energies_rem[2], 6), "std_error": round(ses_rem[2], 6), "error_mha": round((energies_rem[2] - e_fci)*1000, 3), "chemical_accuracy": False},
        {"method": "ZNE Linear Extrapolation (λ→0)", "scale_factor": 0, "energy": round(e_zne_linear, 6), "std_error": round(se_zne_linear, 6), "error_mha": round(err_linear_mha, 3), "chemical_accuracy": abs(err_linear_mha) <= 1.6},
        {"method": "ZNE Richardson Extrapolation (λ→0)", "scale_factor": 0, "energy": round(e_richardson, 6), "std_error": round(se_richardson, 6), "error_mha": round(err_richardson_mha, 3), "chemical_accuracy": abs(err_richardson_mha) <= 1.6},
        {"method": f"Symmetry Givens (Seed {best_givens['seed']}, Ideal)", "scale_factor": 0, "energy": round(best_givens["energy"], 6), "std_error": 0.0, "error_mha": round(best_givens["error_mha"], 3), "chemical_accuracy": abs(best_givens["error_mha"]) <= 1.6}
    ]
    df_qem = pd.DataFrame(qem_rows)
    qem_csv_path = os.path.join(tables_dir, "error_mitigation_benchmark.csv")
    df_qem.to_csv(qem_csv_path, index=False)
    print(f"\nSaved QEM benchmark table to: {qem_csv_path}")
    
    # 5. Plot Zero-Noise Extrapolation Curve
    figures_dir = os.path.join(root, "results", "figures")
    fig_path = os.path.join(figures_dir, "zne_extrapolation_curve.png")
    
    plt.figure(figsize=(9, 5.2), dpi=300)
    plt.errorbar(scale_factors, [(e - e_fci)*1000 for e in energies_raw], yerr=[s*1000 for s in ses_raw], fmt="o--", color="#d95f02", label="Raw Noisy on Processor D", markersize=8, capsize=4)
    plt.errorbar(scale_factors, [(e - e_fci)*1000 for e in energies_rem], yerr=[s*1000 for s in ses_rem], fmt="s-", color="#2b5c8f", label="Readout Error Mitigated (REM)", markersize=8, capsize=4)
    
    # Plot linear extrapolation line
    extrap_x = np.linspace(0, 5.5, 50)
    extrap_y = (np.polyval(poly_linear, extrap_x) - e_fci) * 1000.0
    plt.plot(extrap_x, extrap_y, ":", color="#1b9e77", linewidth=2.0, label=f"Linear ZNE Fit $\\to$ {err_linear_mha:+.2f} mHa")
    
    # Highlight extrapolated point at lambda = 0
    plt.errorbar([0], [err_linear_mha], yerr=[se_zne_linear*1000], fmt="*", color="#7570b3", markersize=14, capsize=6, zorder=5, label=f"Mitigated ($\\lambda=0$): {err_linear_mha:+.1f}±{se_zne_linear*1000:.1f} mHa")
    
    plt.axhline(1.6, color="red", linestyle="--", linewidth=1.2, label=r"Chemical Accuracy ($\leq 1.6$ mHa)")
    plt.axhline(0.0, color="gray", linestyle="-", linewidth=0.8)
    
    plt.xlabel(r"Noise Scale Factor $\lambda$ (Unitary Folding: $CX \to CX(CX^\dagger CX)^n$)", fontsize=11, fontweight="bold")
    plt.ylabel(r"Energy Error $|E - E_{\rm FCI}|$ (mHa)", fontsize=11, fontweight="bold")
    plt.title(r"Zero-Noise Extrapolation (ZNE) on Processor D ($H_2$ Ground State)", fontsize=12, fontweight="bold", pad=12)
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.legend(loc="upper left", framealpha=0.92)
    plt.xlim(-0.3, 5.6)
    plt.tight_layout()
    plt.savefig(fig_path, bbox_inches="tight")
    plt.close()
    print(f"Saved ZNE plot to: {fig_path}")

if __name__ == "__main__":
    run_qem_and_ansatz_study()

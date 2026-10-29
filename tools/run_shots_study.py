import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from qiskit.quantum_info import SparsePauliOp
import qff_chem as qff

def run_shots_study():
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
    
    # 2. Load optimal converged parameters
    params_path = os.path.join(root, "results", "optimal_vqe_params.json")
    with open(params_path) as f:
        opt_info = json.load(f)
        
    depth = opt_info["depth"]
    best_params = opt_info["params"]
    print(f"Optimal State: HEA Depth {depth} ({opt_info['optimizer']} Seed {opt_info['seed']})")
    print(f"Statevector Ideal Energy: {opt_info['energy']:.8f} Ha (Error: {opt_info['error_mha']:+.4f} mHa)")
    
    ansatz, p_vec = qff.hardware_efficient_ansatz(2, reps=depth)
    bound_qc = ansatz.assign_parameters(dict(zip(p_vec, best_params)))
    
    # 3. Execute the 4 required shot-based runs (1024 and 8192 shots, ideal and noisy on D)
    shot_levels = [1024, 8192]
    conditions = [False, True]
    
    rows = []
    print("\n--- Executing 4 Shot-Based Energy Estimations ---")
    for shots in shot_levels:
        for noisy in conditions:
            cond_label = "noisy_D" if noisy else "ideal"
            res = qff.energy_shots(
                circuit=bound_qc,
                op=op,
                constant=const,
                shots_per_group=shots,
                noisy=noisy,
                processor=proc_d if noisy else None,
                seed=qff.SEED
            )
            
            energy = res["energy"]
            std_err = res["std_error"]
            err_mha = (energy - e_fci) * 1000.0
            groups = res["groups"]
            total_shots = res["total_shots"]
            
            # Check chemical accuracy within standard error
            within_chem = abs(err_mha) <= (1.6 + std_err * 1000.0)
            
            row = {
                "shots_per_group": shots,
                "condition": cond_label,
                "energy": round(energy, 6),
                "std_error": round(std_err, 6),
                "error_mha": round(err_mha, 4),
                "groups": groups,
                "total_shots": total_shots
            }
            rows.append(row)
            
            print(f"Shots/grp: {shots:5d} | {cond_label:7s} | E = {energy:.6f} +/- {std_err:.6f} Ha | Error = {err_mha:+.3f} mHa | Chem Acc (|err|<=1.6+SE): {within_chem}")
            
    # 4. Save results/tables/c1_shots.csv
    tables_dir = os.path.join(root, "results", "tables")
    os.makedirs(tables_dir, exist_ok=True)
    shots_csv_path = os.path.join(tables_dir, "c1_shots.csv")
    df_shots = pd.DataFrame(rows)
    df_shots.to_csv(shots_csv_path, index=False)
    print(f"\nSaved shot study table to: {shots_csv_path}")
    
    # 5. Check Statistical Scaling: SE shrinkage ratio from 1024 to 8192
    se_ideal_1024 = rows[0]["std_error"]
    se_ideal_8192 = rows[2]["std_error"]
    ratio_ideal = se_ideal_1024 / se_ideal_8192
    
    se_noisy_1024 = rows[1]["std_error"]
    se_noisy_8192 = rows[3]["std_error"]
    ratio_noisy = se_noisy_1024 / se_noisy_8192
    
    print("\n--- Standard Error Scaling Analysis ---")
    print(f"Theoretical Ratio (sqrt(8192 / 1024) = sqrt(8)): ~2.8284")
    print(f"Measured Ideal SE Ratio: {se_ideal_1024:.6f} / {se_ideal_8192:.6f} = {ratio_ideal:.4f}")
    print(f"Measured Noisy SE Ratio: {se_noisy_1024:.6f} / {se_noisy_8192:.6f} = {ratio_noisy:.4f}")
    
    # 6. Generate Plot of Shot Estimation and Noise Shift
    figures_dir = os.path.join(root, "results", "figures")
    os.makedirs(figures_dir, exist_ok=True)
    fig_path = os.path.join(figures_dir, "shot_estimation_and_noise.png")
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5), dpi=300)
    
    # Subplot 1: Energy Estimates with Standard Error Bars vs E_FCI
    x_indices = np.arange(4)
    x_labels = [f"{r['shots_per_group']}\n({r['condition']})" for r in rows]
    energies = [r["energy"] for r in rows]
    errors = [r["std_error"] for r in rows]
    bar_colors = ["#2b5c8f", "#d95f02", "#41b6c4", "#e7298a"]
    
    bars = ax1.bar(x_indices, energies, yerr=errors, capsize=5, width=0.55, color=bar_colors, edgecolor="black", linewidth=1.2)
    ax1.axhline(e_fci, color="green", linestyle="--", linewidth=1.5, label=f"$E_{{FCI}} = {e_fci:.6f}$ Ha")
    ax1.axhspan(e_fci - 0.0016, e_fci + 0.0016, color="green", alpha=0.15, label=r"Chemical Accuracy ($\pm 1.6$ mHa)")
    ax1.set_xticks(x_indices)
    ax1.set_xticklabels(x_labels, fontsize=10, fontweight="bold")
    ax1.set_ylabel("Ground State Energy (Hartree)", fontsize=11, fontweight="bold")
    ax1.set_title("Shot-Based Ground State Energy Estimates", fontsize=12, fontweight="bold", pad=10)
    ax1.set_ylim(-1.145, -1.095)
    ax1.legend(loc="lower right", framealpha=0.9)
    ax1.grid(axis="y", linestyle=":", alpha=0.6)
    
    for bar, e, se in zip(bars, energies, errors):
        ax1.text(bar.get_x() + bar.get_width()/2.0, e + se + 0.0015, f"{e:.4f}±{se:.4f}", ha="center", va="bottom", fontsize=8.5, fontweight="bold")
        
    # Subplot 2: Standard Error Shrinkage (Ideal vs Noisy)
    shot_counts = [1024, 8192]
    ax2.plot(shot_counts, [se_ideal_1024*1000, se_ideal_8192*1000], "o-", color="#2b5c8f", linewidth=2.0, markersize=8, label=f"Ideal SE (Ratio: {ratio_ideal:.2f}x)")
    ax2.plot(shot_counts, [se_noisy_1024*1000, se_noisy_8192*1000], "s--", color="#d95f02", linewidth=2.0, markersize=8, label=f"Noisy SE on D (Ratio: {ratio_noisy:.2f}x)")
    
    # Theoretical 1/sqrt(N) guide
    guide_x = np.linspace(1000, 8500, 100)
    guide_y = (se_ideal_1024 * 1000) * np.sqrt(1024 / guide_x)
    ax2.plot(guide_x, guide_y, ":", color="gray", label=r"Theory: $\propto 1/\sqrt{N_{\rm shots}}$ ($\sqrt{8}\approx 2.83\times$)")
    
    ax2.set_xscale("log")
    ax2.set_xticks([1024, 2048, 4096, 8192])
    ax2.get_xaxis().set_major_formatter(plt.ScalarFormatter())
    ax2.set_xlabel("Shots per Measurement Group", fontsize=11, fontweight="bold")
    ax2.set_ylabel("Standard Error (mHa)", fontsize=11, fontweight="bold")
    ax2.set_title(r"Standard Error Scaling vs Shot Budget ($1/\sqrt{N}$ Law)", fontsize=12, fontweight="bold", pad=10)
    ax2.grid(True, which="both", linestyle=":", alpha=0.6)
    ax2.legend(loc="upper right", framealpha=0.9)
    
    plt.tight_layout()
    plt.savefig(fig_path, bbox_inches="tight")
    plt.close()
    print(f"Saved plot figure to: {fig_path}")

if __name__ == "__main__":
    run_shots_study()

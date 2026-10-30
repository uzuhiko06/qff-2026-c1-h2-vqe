import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import qff_chem as qff

def run_bell_study():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    d_path = os.path.join(root_dir, "processors", "processor_D.json")
    proc_d = qff.load_processor(d_path)
    
    # 1. Determine the near pair (distance 1) and farthest pair (maximum distance)
    cm = qff.coupling_map_from_edges(proc_d["edges"], proc_d["num_qubits"])
    n = proc_d["num_qubits"]
    
    near_pair = (0, 1)
    # Find pair with maximum distance
    max_d = -1
    far_pair = None
    for i in range(n):
        for j in range(i + 1, n):
            d = cm.distance(i, j)
            if d > max_d:
                max_d = d
                far_pair = (i, j)
                
    print(f"Selected Near Pair: {near_pair} (distance = {cm.distance(*near_pair)})")
    print(f"Selected Far Pair:  {far_pair} (distance = {cm.distance(*far_pair)})")
    
    pairs = [near_pair, far_pair]
    rows = []
    
    print("\n--- Executing 12 Bell-State Circuits on Processor D (4096 shots/basis) ---")
    for pair in pairs:
        for noisy in [False, True]:
            res = qff.bell_experiment(proc_d, pair, noisy=noisy, shots=qff.SHOTS)
            cond_str = "noisy" if noisy else "ideal"
            
            row = {
                "pair": f"({pair[0]}, {pair[1]})",
                "pair_distance": res["pair_distance"],
                "condition": cond_str,
                "two_qubit_gates": int(res["cx"]),
                "XX": round(res["XX"], 6),
                "XX_se": round(res["XX_se"], 6),
                "YY": round(res["YY"], 6),
                "YY_se": round(res["YY_se"], 6),
                "ZZ": round(res["ZZ"], 6),
                "ZZ_se": round(res["ZZ_se"], 6),
                "fidelity": round(res["fidelity"], 6),
                "fidelity_se": round(res["fidelity_se"], 6),
            }
            rows.append(row)
            print(f"Pair {row['pair']:8s} | {cond_str:5s} | dist={row['pair_distance']} | CX={row['two_qubit_gates']} | "
                  f"XX={row['XX']:+.4f} (SE={row['XX_se']:.4f}) | YY={row['YY']:+.4f} (SE={row['YY_se']:.4f}) | "
                  f"ZZ={row['ZZ']:+.4f} (SE={row['ZZ_se']:.4f}) | Fidelity={row['fidelity']:.4f} +/- {row['fidelity_se']:.4f}")
            
    df = pd.DataFrame(rows)
    
    # 2. Save CSV to results/tables/bell.csv
    tables_dir = os.path.join(root_dir, "results", "tables")
    os.makedirs(tables_dir, exist_ok=True)
    csv_path = os.path.join(tables_dir, "bell.csv")
    df.to_csv(csv_path, index=False)
    print(f"\nSaved CSV table to: {csv_path}")
    
    # 3. Generate high-resolution comparison figure
    figures_dir = os.path.join(root_dir, "results", "figures")
    os.makedirs(figures_dir, exist_ok=True)
    fig_path = os.path.join(figures_dir, "bell_state_verification.png")
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.2), dpi=300)
    
    # Plot 1: Parity Correlations XX, YY, ZZ
    x = np.arange(4)
    width = 0.25
    labels = [f"{r['pair']}\n({r['condition']})" for r in rows]
    
    xx_vals = [r["XX"] for r in rows]
    xx_errs = [r["XX_se"] for r in rows]
    yy_vals = [r["YY"] for r in rows]
    yy_errs = [r["YY_se"] for r in rows]
    zz_vals = [r["ZZ"] for r in rows]
    zz_errs = [r["ZZ_se"] for r in rows]
    
    ax1.bar(x - width, xx_vals, width, yerr=xx_errs, capsize=4, label=r"$\langle XX \rangle$ (Ideal: +1)", color="#2b5c8f", alpha=0.9)
    ax1.bar(x, yy_vals, width, yerr=yy_errs, capsize=4, label=r"$\langle YY \rangle$ (Ideal: -1)", color="#d95f02", alpha=0.9)
    ax1.bar(x + width, zz_vals, width, yerr=zz_errs, capsize=4, label=r"$\langle ZZ \rangle$ (Ideal: +1)", color="#7570b3", alpha=0.9)
    
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, fontsize=10, fontweight="bold")
    ax1.set_ylabel("Parity Expectation Value", fontsize=11, fontweight="bold")
    ax1.set_title("Two-Qubit Pauli Correlations on Processor D", fontsize=12, fontweight="bold", pad=10)
    ax1.axhline(0, color="gray", linestyle="--", linewidth=0.8)
    ax1.set_ylim(-1.3, 1.35)
    ax1.legend(loc="upper left", bbox_to_anchor=(0.02, 0.98), framealpha=0.9)
    ax1.grid(axis="y", linestyle=":", alpha=0.6)
    ax1.grid(axis="y", linestyle=":", alpha=0.6)
    
    # Plot 2: State Fidelity Comparison
    f_vals = [r["fidelity"] for r in rows]
    f_errs = [r["fidelity_se"] for r in rows]
    colors = ["#2b5c8f", "#41b6c4", "#e7298a", "#fc8d62"]
    
    bars = ax2.bar(x, f_vals, yerr=f_errs, capsize=5, width=0.55, color=colors, edgecolor="black", linewidth=1.2)
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels, fontsize=10, fontweight="bold")
    ax2.set_ylabel(r"Quantum State Fidelity $F(|\Phi^+\rangle)$", fontsize=11, fontweight="bold")
    ax2.set_title(r"Bell State Fidelity $F = \frac{1 + \langle XX \rangle - \langle YY \rangle + \langle ZZ \rangle}{4}$",
                  fontsize=12, fontweight="bold", pad=10)
    ax2.set_ylim(0.85, 1.02)
    ax2.axhline(1.0, color="green", linestyle="--", linewidth=1.2, label="Ideal Pure State (F = 1.0)")
    ax2.grid(axis="y", linestyle=":", alpha=0.6)
    
    for bar, f, se in zip(bars, f_vals, f_errs):
        yval = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width() / 2.0, yval + 0.008, f"{f:.4f}±{se:.4f}",
                 ha="center", va="bottom", fontsize=9, fontweight="bold")
                 
    ax2.legend(loc="lower left", framealpha=0.9)
    
    plt.tight_layout()
    plt.savefig(fig_path, bbox_inches="tight")
    plt.close()
    print(f"Saved plot figure to: {fig_path}")

if __name__ == "__main__":
    run_bell_study()

"""
Visualization Module:
Generates publication-quality figures for:
- Processor A and B hardware coupling graphs
- Transpiled circuit comparisons
- VQE optimization convergence curves
- Molecular Potential Energy Surface (PES) curves
- Architecture trade-off and noise impact comparisons
"""

from pathlib import Path
from typing import Dict, Any, List
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np


def ensure_dir(path_str: str) -> Path:
    p = Path(path_str)
    p.mkdir(parents=True, exist_ok=True)
    return p


def plot_processor_graph(
    G: nx.Graph,
    title: str,
    output_path: str,
    node_color: str = "#4C72B0"
) -> str:
    """Plots and saves the hardware coupling topology graph."""
    plt.figure(figsize=(6, 5), dpi=300)
    
    # Custom layout for nice presentation
    pos = nx.spring_layout(G, seed=42)
    nx.draw_networkx_nodes(G, pos, node_color=node_color, node_size=800, alpha=0.9)
    nx.draw_networkx_edges(G, pos, width=2.5, edge_color="#333333", alpha=0.8)
    nx.draw_networkx_labels(G, pos, font_size=12, font_color="white", font_weight="bold")
    
    plt.title(title, fontsize=14, fontweight="bold", pad=12)
    plt.axis("off")
    plt.tight_layout()
    
    out = Path(output_path)
    ensure_dir(str(out.parent))
    plt.savefig(out, bbox_inches="tight")
    plt.close()
    return str(out)


def plot_vqe_convergence(
    history: Dict[str, List[float]],
    exact_energy: float,
    output_path: str,
    ansatz_name: str = "Ansatz"
) -> str:
    """Plots VQE energy iteration trajectory with chemical accuracy band."""
    iterations = history["iteration"]
    energies = history["energy"]
    chemical_acc = 0.0015936
    
    plt.figure(figsize=(8, 5), dpi=300)
    plt.plot(iterations, energies, "o-", color="#1f77b4", linewidth=2, label="VQE Energy")
    plt.axhline(exact_energy, color="#2ca02c", linestyle="--", linewidth=2, label=f"Exact FCI ({exact_energy:.4f} Ha)")
    
    # Shaded chemical accuracy zone
    plt.fill_between(
        iterations,
        exact_energy - chemical_acc,
        exact_energy + chemical_acc,
        color="#2ca02c",
        alpha=0.2,
        label=r"Chemical Accuracy ($\pm 1.6$ mHa)"
    )
    
    plt.xlabel("Optimization Iteration", fontsize=12)
    plt.ylabel("Total Energy (Hartree)", fontsize=12)
    plt.title(f"VQE Energy Convergence — {ansatz_name}", fontsize=14, fontweight="bold")
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.legend(frameon=True, facecolor="white", framealpha=0.9)
    plt.tight_layout()
    
    out = Path(output_path)
    ensure_dir(str(out.parent))
    plt.savefig(out, bbox_inches="tight")
    plt.close()
    return str(out)


def plot_pes_curve(
    pes_data: List[Dict[str, Any]],
    output_path: str
) -> str:
    """Plots Potential Energy Surface (PES) dissociation profile."""
    r_vals = [pt["bond_length_angstrom"] for pt in pes_data]
    e_vals = [pt["fci_exact_energy_hartree"] for pt in pes_data]
    
    plt.figure(figsize=(8, 5), dpi=300)
    plt.plot(r_vals, e_vals, "o-", color="#d62728", linewidth=2.5, markersize=7, label="Exact STO-3G FCI")
    plt.axvline(0.7414, color="#7f7f7f", linestyle="--", alpha=0.8, label="Equilibrium (0.7414 Å)")
    
    plt.xlabel("Internuclear Distance R (Å)", fontsize=12)
    plt.ylabel("Ground State Energy (Hartree)", fontsize=12)
    plt.title(r"$H_2$ Potential Energy Surface (Dissociation Curve)", fontsize=14, fontweight="bold")
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.legend(frameon=True)
    plt.tight_layout()
    
    out = Path(output_path)
    ensure_dir(str(out.parent))
    plt.savefig(out, bbox_inches="tight")
    plt.close()
    return str(out)


def plot_architecture_tradeoffs(
    metrics_A: Dict[str, Any],
    metrics_B: Dict[str, Any],
    output_path: str
) -> str:
    """Generates comparative multi-panel bar chart for Processor A vs Processor B."""
    labels = ["Depth", "2Q Gates (CX)", "Inferred SWAPs"]
    vals_A = [metrics_A.get("depth", 0), metrics_A.get("two_qubit_gates", 0), metrics_A.get("inferred_swaps", 0)]
    vals_B = [metrics_B.get("depth", 0), metrics_B.get("two_qubit_gates", 0), metrics_B.get("inferred_swaps", 0)]
    
    x = np.arange(len(labels))
    width = 0.35
    
    fig, ax = plt.subplots(figsize=(8, 5), dpi=300)
    rects1 = ax.bar(x - width/2, vals_A, width, label="Processor A (5Q Tree)", color="#4C72B0")
    rects2 = ax.bar(x + width/2, vals_B, width, label="Processor B (9Q Mesh)", color="#DD8452")
    
    ax.set_ylabel("Count / Overhead", fontsize=12)
    ax.set_title("Architectural Resource Benchmarking: Processor A vs Processor B", fontsize=13, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=11)
    ax.legend(frameon=True)
    ax.grid(axis="y", linestyle=":", alpha=0.6)
    
    # Value annotations on bars
    for rect in rects1:
        h = rect.get_height()
        ax.annotate(f"{h}", xy=(rect.get_x() + rect.get_width() / 2, h),
                    xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontweight="bold")
    for rect in rects2:
        h = rect.get_height()
        ax.annotate(f"{h}", xy=(rect.get_x() + rect.get_width() / 2, h),
                    xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontweight="bold")
                    
    plt.tight_layout()
    out = Path(output_path)
    ensure_dir(str(out.parent))
    plt.savefig(out, bbox_inches="tight")
    plt.close()
    return str(out)


def plot_noise_energy_comparison(
    exact_energy: float,
    energy_ideal: float,
    energy_A_noisy: float,
    energy_B_noisy: float,
    err_A: float,
    err_B: float,
    output_path: str
) -> str:
    """Plots energy accuracy comparison under noise with standard error bars."""
    categories = ["Exact FCI", "Ideal VQE", "Processor A (Noisy)", "Processor B (Noisy)"]
    energies = [exact_energy, energy_ideal, energy_A_noisy, energy_B_noisy]
    errors = [0.0, 0.0, err_A, err_B]
    colors = ["#2ca02c", "#1f77b4", "#4C72B0", "#DD8452"]
    
    plt.figure(figsize=(9, 5), dpi=300)
    bars = plt.bar(categories, energies, yerr=errors, capsize=6, color=colors, alpha=0.85, edgecolor="#333333", width=0.55)
    
    plt.axhline(exact_energy, color="#2ca02c", linestyle="--", linewidth=1.5, alpha=0.7)
    plt.ylabel("Total Ground-State Energy (Hartree)", fontsize=12)
    plt.title(r"$H_2$ Ground-State Energy Under Noise ($0.5\%$ CX + Readout Error)", fontsize=13, fontweight="bold")
    plt.grid(axis="y", linestyle=":", alpha=0.6)
    
    # Annotate values inside bars
    for bar, val in zip(bars, energies):
        plt.text(bar.get_x() + bar.get_width()/2, val / 2, f"{val:.4f} Ha",
                 ha="center", va="center", color="white", fontweight="bold", fontsize=10)
                 
    plt.tight_layout()
    out = Path(output_path)
    ensure_dir(str(out.parent))
    plt.savefig(out, bbox_inches="tight")
    plt.close()
    return str(out)

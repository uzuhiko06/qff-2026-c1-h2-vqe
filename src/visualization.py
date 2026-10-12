"""
Visualization Module:
Generates publication-quality figures:
1. Processor A and B hardware coupling graphs with highlighted bottleneck hubs.
2. Dual-mode VQE convergence: Ideal Statevector vs Real Noisy SPSA with Chemical Accuracy band.
3. Multi-ansatz architecture trade-offs (Givens vs HEA vs UCCSD) showing SWAP overheads.
4. Quantum Error Mitigation comparison: Raw Noisy vs Readout Mitigated vs ZNE Extrapolated.
5. Zero-Noise Extrapolation curve fit (λ = 1, 3, 5 to λ = 0).
6. Molecular Potential Energy Surface (PES) dissociation profile.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
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
    
    pos = nx.spring_layout(G, seed=42)
    nx.draw_networkx_nodes(G, pos, node_color=node_color, node_size=800, alpha=0.9)
    nx.draw_networkx_edges(G, pos, width=2.5, edge_color="#333333", alpha=0.8)
    nx.draw_networkx_labels(G, pos, font_size=12, font_color="white", font_weight="bold")
    
    plt.title(title, fontsize=13, fontweight="bold", pad=12)
    plt.axis("off")
    plt.tight_layout()
    
    out = Path(output_path)
    ensure_dir(str(out.parent))
    plt.savefig(out, bbox_inches="tight")
    plt.close()
    return str(out)


def plot_vqe_convergence(
    history_ideal: Dict[str, List[float]],
    exact_energy: float,
    output_path: str,
    history_noisy: Optional[Dict[str, List[float]]] = None,
    ansatz_name: str = "Active-Space Givens"
) -> str:
    """
    Plots VQE energy iteration trajectories comparing ideal statevector convergence
    and authentic noisy SPSA convergence against the chemical accuracy band.
    """
    plt.figure(figsize=(9, 5.5), dpi=300)
    chemical_acc = 0.0015936
    
    # 1. Ideal Statevector Trajectory
    iter_ideal = history_ideal["iteration"]
    energies_ideal = history_ideal["energy"]
    plt.plot(iter_ideal, energies_ideal, "o-", color="#1f77b4", linewidth=2.2, label=f"Ideal Statevector VQE ({energies_ideal[-1]:.4f} Ha)")
    
    # 2. Noisy SPSA Trajectory (if provided)
    if history_noisy is not None:
        iter_noisy = history_noisy["iteration"]
        energies_noisy = history_noisy["energy"]
        plt.plot(iter_noisy, energies_noisy, "s--", color="#e6550d", linewidth=1.8, alpha=0.85, label=f"Noisy SPSA VQE (Shot-based, {energies_noisy[-1]:.4f} Ha)")
        
    # Exact FCI reference line
    plt.axhline(exact_energy, color="#2ca02c", linestyle="--", linewidth=2.2, label=f"Exact FCI Benchmark ({exact_energy:.4f} Ha)")
    
    # Shaded chemical accuracy band
    max_iter = max(max(iter_ideal), max(iter_noisy) if history_noisy else 0)
    x_band = np.linspace(0, max_iter, 100)
    plt.fill_between(
        x_band,
        exact_energy - chemical_acc,
        exact_energy + chemical_acc,
        color="#2ca02c",
        alpha=0.25,
        label=r"Chemical Accuracy ($\pm 1.59$ mHa)"
    )
    
    plt.xlabel("Optimization Iteration", fontsize=12)
    plt.ylabel("Total Energy (Hartree)", fontsize=12)
    plt.title(f"VQE Trajectory & Chemical Accuracy — {ansatz_name}", fontsize=14, fontweight="bold")
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.legend(frameon=True, facecolor="white", framealpha=0.9, loc="upper right")
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
    plt.axvline(0.74, color="#7f7f7f", linestyle="--", alpha=0.8, label="Equilibrium R = 0.74 Å")
    
    plt.xlabel("Internuclear Distance R (Å)", fontsize=12)
    plt.ylabel("Ground State Energy (Hartree)", fontsize=12)
    plt.title(r"$H_2$ Potential Energy Surface (STO-3G Minimal Basis)", fontsize=14, fontweight="bold")
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.legend(frameon=True, facecolor="white", framealpha=0.9)
    plt.tight_layout()
    
    out = Path(output_path)
    ensure_dir(str(out.parent))
    plt.savefig(out, bbox_inches="tight")
    plt.close()
    return str(out)


def plot_architecture_tradeoffs(
    multi_ansatz_records: List[Dict[str, Any]],
    output_path: str
) -> str:
    """
    Plots multi-ansatz routing trade-offs comparing compiled depth, CX count,
    and SWAP overhead between Processor A and Processor B.
    """
    names = [r["Ansatz"] for r in multi_ansatz_records]
    x = np.arange(len(names))
    width = 0.35
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5), dpi=300)
    
    # 1. Compiled Depth
    depth_A = [r["Proc_A_Depth"] for r in multi_ansatz_records]
    depth_B = [r["Proc_B_Depth"] for r in multi_ansatz_records]
    ax1.bar(x - width/2, depth_A, width, label="Processor A (5Q Tree)", color="#4C72B0")
    ax1.bar(x + width/2, depth_B, width, label="Processor B (9Q Mesh)", color="#DD8452")
    ax1.set_ylabel("Compiled Circuit Depth", fontsize=11)
    ax1.set_title("Compiled Depth Across Ansätze (Opt 1)", fontsize=12, fontweight="bold")
    ax1.set_xticks(x)
    ax1.set_xticklabels(names, rotation=15, ha="right", fontsize=9)
    ax1.legend(frameon=True)
    ax1.grid(True, axis="y", linestyle=":", alpha=0.6)
    
    # 2. SWAP Overhead
    swaps_A = [r["Proc_A_SWAPs"] for r in multi_ansatz_records]
    swaps_B = [r["Proc_B_SWAPs"] for r in multi_ansatz_records]
    ax2.bar(x - width/2, swaps_A, width, label="Processor A (5Q Tree)", color="#4C72B0")
    ax2.bar(x + width/2, swaps_B, width, label="Processor B (9Q Mesh)", color="#DD8452")
    ax2.set_ylabel("Inferred SWAP Gates", fontsize=11)
    ax2.set_title("SWAP Overhead Across Ansätze (Opt 1)", fontsize=12, fontweight="bold")
    ax2.set_xticks(x)
    ax2.set_xticklabels(names, rotation=15, ha="right", fontsize=9)
    ax2.legend(frameon=True)
    ax2.grid(True, axis="y", linestyle=":", alpha=0.6)
    
    plt.tight_layout()
    out = Path(output_path)
    ensure_dir(str(out.parent))
    plt.savefig(out, bbox_inches="tight")
    plt.close()
    return str(out)


def plot_noise_and_mitigation(
    exact_energy: float,
    ideal_energy: float,
    noisy_energy: float,
    ro_mitigated_energy: float,
    zne_mitigated_energy: float,
    output_path: str
) -> str:
    """
    Plots the quantitative recovery of Chemical Accuracy through Quantum Error Mitigation:
    Exact vs Ideal vs Raw Noisy vs Readout Mitigated vs ZNE Mitigated.
    """
    stages = [
        "Exact FCI",
        "Ideal Shots",
        "Raw Noisy (p2=0.5%)",
        "Readout Mitigated",
        "ZNE Mitigated (λ=0)"
    ]
    energies = [
        exact_energy,
        ideal_energy,
        noisy_energy,
        ro_mitigated_energy,
        zne_mitigated_energy
    ]
    colors = ["#2ca02c", "#1f77b4", "#d62728", "#ff7f0e", "#2ca02c"]
    
    plt.figure(figsize=(9, 5.5), dpi=300)
    bars = plt.bar(stages, energies, color=colors, width=0.55, alpha=0.85, edgecolor="#333333", linewidth=1.2)
    
    # Chemical accuracy zone
    chemical_acc = 0.0015936
    plt.axhline(exact_energy, color="#2ca02c", linestyle="--", linewidth=1.8, label=f"Exact FCI ({exact_energy:.4f} Ha)")
    plt.axhspan(
        exact_energy - chemical_acc,
        exact_energy + chemical_acc,
        color="#2ca02c",
        alpha=0.25,
        label=r"Chemical Accuracy Band ($\pm 1.59$ mHa)"
    )
    
    # Add values on top of bars
    for bar, val in zip(bars, energies):
        err_mha = abs(val - exact_energy) * 1000
        y_pos = bar.get_height() - 0.02
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            y_pos,
            f"{val:.4f} Ha\n(Δ={err_mha:.1f} mHa)",
            ha="center",
            va="top",
            fontsize=9,
            fontweight="bold",
            color="black"
        )
        
    plt.ylabel("Ground State Energy (Hartree)", fontsize=12)
    plt.title("Error Mitigation Pipeline: Restoring Chemical Accuracy Under Hardware Noise", fontsize=13, fontweight="bold")
    plt.ylim(-1.18, -1.06)
    plt.xticks(rotation=15, ha="right", fontsize=10)
    plt.grid(True, axis="y", linestyle=":", alpha=0.6)
    plt.legend(frameon=True, loc="upper right")
    plt.tight_layout()
    
    out = Path(output_path)
    ensure_dir(str(out.parent))
    plt.savefig(out, bbox_inches="tight")
    plt.close()
    return str(out)


def plot_zne_extrapolation(
    scale_factors: List[int],
    measured_energies: List[float],
    extrapolated_energy: float,
    exact_energy: float,
    output_path: str
) -> str:
    """Plots Zero-Noise Extrapolation curve fit across scale factors λ."""
    plt.figure(figsize=(8, 5), dpi=300)
    chemical_acc = 0.0015936
    
    # Measured points
    plt.scatter(scale_factors, measured_energies, color="#d62728", s=100, zorder=5, label="Measured Scaled Noise")
    
    # Polynomial / Richardson fit curve
    poly = np.polyfit(scale_factors, measured_energies, deg=2 if len(scale_factors) >= 3 else 1)
    x_fit = np.linspace(0, max(scale_factors) * 1.1, 100)
    y_fit = np.polyval(poly, x_fit)
    plt.plot(x_fit, y_fit, "b-", linewidth=2, label="Richardson Extrapolation Fit")
    
    # Extrapolated point at λ = 0
    plt.scatter([0], [extrapolated_energy], color="#2ca02c", marker="*", s=250, zorder=6, label=f"Extrapolated λ=0 ({extrapolated_energy:.4f} Ha)")
    
    # Exact FCI reference and band
    plt.axhline(exact_energy, color="#2ca02c", linestyle="--", linewidth=1.8, label=f"Exact FCI ({exact_energy:.4f} Ha)")
    plt.fill_between(
        x_fit,
        exact_energy - chemical_acc,
        exact_energy + chemical_acc,
        color="#2ca02c",
        alpha=0.2,
        label=r"Chemical Accuracy Band ($\pm 1.59$ mHa)"
    )
    
    plt.xlabel("Noise Scale Factor λ (CX Gate Folding)", fontsize=12)
    plt.ylabel("Measured Energy (Hartree)", fontsize=12)
    plt.title("Zero-Noise Extrapolation (ZNE) via Unitary CX Gate Folding", fontsize=13, fontweight="bold")
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.legend(frameon=True, loc="upper left")
    plt.tight_layout()
    
    out = Path(output_path)
    ensure_dir(str(out.parent))
    plt.savefig(out, bbox_inches="tight")
    plt.close()
    return str(out)

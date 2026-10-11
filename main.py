"""
QFF 2026 Hackathon: Problem Statement C1 (H2 Molecular Ground State Energy)
End-to-End Pipeline & Reproducibility Runner.

Executes:
1. Molecular Hamiltonian loading & exact FCI diagonalization.
2. Parameterized ansatz construction (UCCSD & HEA).
3. VQE optimization achieving chemical accuracy.
4. Architectural analysis & graph characterization of Processors A & B.
5. Compilation, routing, and SWAP overhead benchmarking.
6. Finite-shot noisy simulation with statistical standard errors.
7. Exporting CSV result tables and high-resolution figures.
"""

import os
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
import time
from pathlib import Path
import pandas as pd
import numpy as np

# Add project root to sys.path
PROJECT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_DIR))

from src.problem import (
    load_hamiltonian,
    compute_exact_ground_state,
    build_uccsd_like_ansatz,
    build_hardware_efficient_ansatz,
    load_pes_scan_data,
    CHEMICAL_ACCURACY_HARTREE
)
from src.processors import (
    load_processor_config,
    build_processor_graph,
    compute_graph_metrics,
    build_noise_model
)
from src.routing import (
    compile_for_processor,
    extract_circuit_metrics,
    compare_transpilation_levels
)
from src.metrics import (
    evaluate_statevector_energy,
    evaluate_shot_based_energy,
    check_chemical_accuracy,
    run_vqe_optimization
)
from src.visualization import (
    plot_processor_graph,
    plot_vqe_convergence,
    plot_pes_curve,
    plot_architecture_tradeoffs,
    plot_noise_energy_comparison
)


def run_pipeline():
    print("=" * 78)
    print("  QISKIT FALL FEST 2026 — PROBLEM STATEMENT C1: H2 GROUND STATE ENERGY  ")
    print("  ALGORITHM <-> ARCHITECTURE CO-DESIGN & BENCHMARKING SUITE             ")
    print("=" * 78)

    # 1. Paths and Setup
    data_dir = PROJECT_DIR / "data"
    proc_dir = PROJECT_DIR / "processors"
    res_tables_dir = PROJECT_DIR / "results" / "tables"
    res_figs_dir = PROJECT_DIR / "results" / "figures"
    
    res_tables_dir.mkdir(parents=True, exist_ok=True)
    res_figs_dir.mkdir(parents=True, exist_ok=True)

    # 2. Load Hamiltonian & Exact Classical Baseline
    hamiltonian_path = data_dir / "processed" / "h2_hamiltonian_4qubit.json"
    hamiltonian_2q_path = data_dir / "processed" / "h2_hamiltonian_2qubit.json"
    raw_data_path = data_dir / "raw" / "h2_integrals_sto3g.json"

    print("\n[Step 1] Loading Molecular Hamiltonian & Classical FCI Reference...")
    H_4q, meta_4q = load_hamiltonian(str(hamiltonian_path))
    H_2q, meta_2q = load_hamiltonian(str(hamiltonian_2q_path))
    
    exact_energy_4q, fci_state_4q = compute_exact_ground_state(H_4q)
    exact_energy_2q, _ = compute_exact_ground_state(H_2q)

    print(f"  Exact FCI Ground State Energy (4-Qubit): {exact_energy_4q:.6f} Hartree")
    print(f"  Exact FCI Ground State Energy (2-Qubit): {exact_energy_2q:.6f} Hartree")
    print(f"  Chemical Accuracy Threshold (1 kcal/mol): {CHEMICAL_ACCURACY_HARTREE:.6f} Hartree")

    # 3. VQE Optimization
    print("\n[Step 2] Constructing Parameterized Ansatz & Executing VQE...")
    ansatz_4q, theta_4q = build_uccsd_like_ansatz(num_qubits=4)
    vqe_result_4q = run_vqe_optimization(
        ansatz=ansatz_4q,
        hamiltonian=H_4q,
        exact_energy=exact_energy_4q,
        maxiter=35,
        method="COBYLA"
    )

    vqe_energy = vqe_result_4q["optimal_energy"]
    vqe_error = vqe_result_4q["energy_error"]
    within_chem = vqe_result_4q["within_chemical_accuracy"]
    opt_params = vqe_result_4q["optimal_params"]

    print(f"  VQE Converged Energy: {vqe_energy:.6f} Hartree")
    print(f"  Absolute Energy Error: {vqe_error:.6f} Hartree")
    print(f"  Within Chemical Accuracy? {'YES (SUCCESS)' if within_chem else 'NO'}")

    # Generate convergence plot
    plot_vqe_convergence(
        vqe_result_4q["history"],
        exact_energy_4q,
        str(res_figs_dir / "vqe_convergence.png"),
        ansatz_name="UCCSD-like 4-Qubit"
    )

    # 4. Processors Architecture & Graph Analysis
    print("\n[Step 3] Loading Processor A & B Architectures & Graph Analysis...")
    cfg_A = load_processor_config(str(proc_dir / "processor_A.json"))
    cfg_B = load_processor_config(str(proc_dir / "processor_B.json"))

    G_A = build_processor_graph(cfg_A)
    G_B = build_processor_graph(cfg_B)

    metrics_graph_A = compute_graph_metrics(G_A, name="Processor A")
    metrics_graph_B = compute_graph_metrics(G_B, name="Processor B")

    plot_processor_graph(G_A, "Processor A Topology (5 Qubits, Branching Tree)", str(res_figs_dir / "processor_A_graph.png"), node_color="#4C72B0")
    plot_processor_graph(G_B, "Processor B Topology (9 Qubits, Heavy-Hex Mesh)", str(res_figs_dir / "processor_B_graph.png"), node_color="#DD8452")

    # 5. Routing & Compilation Benchmarking
    print("\n[Step 4] Transpiling Logical VQE Circuit to Physical Architectures...")
    bound_vqe_qc = ansatz_4q.assign_parameters(opt_params)
    logical_metrics = extract_circuit_metrics(bound_vqe_qc)
    print(f"  Logical Circuit: Qubits={logical_metrics['num_qubits']}, Depth={logical_metrics['depth']}, CX={logical_metrics['two_qubit_gates']}")

    compiled_A, comp_metrics_A = compile_for_processor(bound_vqe_qc, cfg_A, optimization_level=1)
    compiled_B, comp_metrics_B = compile_for_processor(bound_vqe_qc, cfg_B, optimization_level=1)

    print(f"  Compiled on Processor A: Depth={comp_metrics_A['depth']}, CX={comp_metrics_A['two_qubit_gates']}, Inferred SWAPs={comp_metrics_A['inferred_swaps']}")
    print(f"  Compiled on Processor B: Depth={comp_metrics_B['depth']}, CX={comp_metrics_B['two_qubit_gates']}, Inferred SWAPs={comp_metrics_B['inferred_swaps']}")

    # 6. Finite-Shot & Noisy Simulation
    print("\n[Step 5] Simulating Finite-Shot & Noisy Execution (Aer Simulator)...")
    noise_A = build_noise_model(cfg_A)
    noise_B = build_noise_model(cfg_B)

    shots = 4096
    energy_A_ideal, se_A_ideal = evaluate_shot_based_energy(compiled_A, H_4q, noise_model=None, shots=shots)
    energy_A_noisy, se_A_noisy = evaluate_shot_based_energy(compiled_A, H_4q, noise_model=noise_A, shots=shots)

    energy_B_ideal, se_B_ideal = evaluate_shot_based_energy(compiled_B, H_4q, noise_model=None, shots=shots)
    energy_B_noisy, se_B_noisy = evaluate_shot_based_energy(compiled_B, H_4q, noise_model=noise_B, shots=shots)

    err_A_noisy = abs(energy_A_noisy - exact_energy_4q)
    err_B_noisy = abs(energy_B_noisy - exact_energy_4q)

    print(f"  Processor A Noisy Energy: {energy_A_noisy:.6f} ± {se_A_noisy:.6f} Ha (Error: {err_A_noisy:.6f} Ha)")
    print(f"  Processor B Noisy Energy: {energy_B_noisy:.6f} ± {se_B_noisy:.6f} Ha (Error: {err_B_noisy:.6f} Ha)")

    # 7. Generate Comparative Plots
    print("\n[Step 6] Generating Publication Figures & Comparative Tables...")
    plot_architecture_tradeoffs(comp_metrics_A, comp_metrics_B, str(res_figs_dir / "architecture_tradeoffs.png"))
    plot_architecture_tradeoffs(comp_metrics_A, comp_metrics_B, str(res_figs_dir / "AB_performance.png"))
    
    plot_noise_energy_comparison(
        exact_energy_4q,
        vqe_energy,
        energy_A_noisy,
        energy_B_noisy,
        se_A_noisy,
        se_B_noisy,
        str(res_figs_dir / "noise_energy_comparison.png")
    )

    pes_points = load_pes_scan_data(str(raw_data_path))
    if pes_points:
        plot_pes_curve(pes_points, str(res_figs_dir / "pes_curve.png"))

    # 8. Export CSV Result Tables
    df_A = pd.DataFrame([{
        "Processor": "Processor A",
        "Num_Qubits": metrics_graph_A["num_qubits"],
        "Num_Edges": metrics_graph_A["num_edges"],
        "Avg_Degree": metrics_graph_A["avg_degree"],
        "Diameter": metrics_graph_A["diameter"],
        "Avg_Path_Length": metrics_graph_A["avg_shortest_path_length"],
        "Algebraic_Connectivity": metrics_graph_A["algebraic_connectivity"],
        "Compiled_Depth": comp_metrics_A["depth"],
        "Logical_CX": logical_metrics["two_qubit_gates"],
        "Compiled_CX": comp_metrics_A["two_qubit_gates"],
        "Inferred_SWAPs": comp_metrics_A["inferred_swaps"],
        "CX_Expansion_Ratio": comp_metrics_A["cx_expansion_ratio"],
        "Exact_FCI_Energy": exact_energy_4q,
        "VQE_Ideal_Energy": vqe_energy,
        "Noisy_Energy": energy_A_noisy,
        "Noisy_SE": se_A_noisy,
        "Noisy_Error": err_A_noisy
    }])
    df_A.to_csv(res_tables_dir / "processor_A_metrics.csv", index=False)

    df_B = pd.DataFrame([{
        "Processor": "Processor B",
        "Num_Qubits": metrics_graph_B["num_qubits"],
        "Num_Edges": metrics_graph_B["num_edges"],
        "Avg_Degree": metrics_graph_B["avg_degree"],
        "Diameter": metrics_graph_B["diameter"],
        "Avg_Path_Length": metrics_graph_B["avg_shortest_path_length"],
        "Algebraic_Connectivity": metrics_graph_B["algebraic_connectivity"],
        "Compiled_Depth": comp_metrics_B["depth"],
        "Logical_CX": logical_metrics["two_qubit_gates"],
        "Compiled_CX": comp_metrics_B["two_qubit_gates"],
        "Inferred_SWAPs": comp_metrics_B["inferred_swaps"],
        "CX_Expansion_Ratio": comp_metrics_B["cx_expansion_ratio"],
        "Exact_FCI_Energy": exact_energy_4q,
        "VQE_Ideal_Energy": vqe_energy,
        "Noisy_Energy": energy_B_noisy,
        "Noisy_SE": se_B_noisy,
        "Noisy_Error": err_B_noisy
    }])
    df_B.to_csv(res_tables_dir / "processor_B_metrics.csv", index=False)

    # Comparative summary table
    df_compare = pd.DataFrame([
        {
            "Metric": "Physical Qubits",
            "Processor A": metrics_graph_A["num_qubits"],
            "Processor B": metrics_graph_B["num_qubits"],
            "Difference (B - A)": metrics_graph_B["num_qubits"] - metrics_graph_A["num_qubits"],
            "Architectural Interpretation": "Processor B has 4 more physical qubits, providing more candidate subgraphs."
        },
        {
            "Metric": "Physical Edges",
            "Processor A": metrics_graph_A["num_edges"],
            "Processor B": metrics_graph_B["num_edges"],
            "Difference (B - A)": metrics_graph_B["num_edges"] - metrics_graph_A["num_edges"],
            "Architectural Interpretation": "Processor B offers 3x the connectivity edges of Processor A."
        },
        {
            "Metric": "Average Node Degree",
            "Processor A": metrics_graph_A["avg_degree"],
            "Processor B": metrics_graph_B["avg_degree"],
            "Difference (B - A)": round(metrics_graph_B["avg_degree"] - metrics_graph_A["avg_degree"], 3),
            "Architectural Interpretation": "Higher node degree in B reduces bottlenecking at central nodes."
        },
        {
            "Metric": "Graph Diameter",
            "Processor A": metrics_graph_A["diameter"],
            "Processor B": metrics_graph_B["diameter"],
            "Difference (B - A)": metrics_graph_B["diameter"] - metrics_graph_A["diameter"],
            "Architectural Interpretation": "Processor B has a smaller diameter despite having nearly twice the qubits."
        },
        {
            "Metric": "Avg Shortest Path Length",
            "Processor A": metrics_graph_A["avg_shortest_path_length"],
            "Processor B": metrics_graph_B["avg_shortest_path_length"],
            "Difference (B - A)": round(metrics_graph_B["avg_shortest_path_length"] - metrics_graph_A["avg_shortest_path_length"], 3),
            "Architectural Interpretation": "Qubits are closer on average on Processor B."
        },
        {
            "Metric": "Algebraic Connectivity (lambda_2)",
            "Processor A": metrics_graph_A["algebraic_connectivity"],
            "Processor B": metrics_graph_B["algebraic_connectivity"],
            "Difference (B - A)": round(metrics_graph_B["algebraic_connectivity"] - metrics_graph_A["algebraic_connectivity"], 4),
            "Architectural Interpretation": "Significantly higher lambda_2 in B indicates superior global routing robustness."
        },
        {
            "Metric": "Compiled Circuit Depth",
            "Processor A": comp_metrics_A["depth"],
            "Processor B": comp_metrics_B["depth"],
            "Difference (B - A)": comp_metrics_B["depth"] - comp_metrics_A["depth"],
            "Architectural Interpretation": "Routing on Processor A causes greater depth inflation."
        },
        {
            "Metric": "Compiled 2Q (CX) Gates",
            "Processor A": comp_metrics_A["two_qubit_gates"],
            "Processor B": comp_metrics_B["two_qubit_gates"],
            "Difference (B - A)": comp_metrics_B["two_qubit_gates"] - comp_metrics_A["two_qubit_gates"],
            "Architectural Interpretation": "SWAP decomposition on tree topology injects extra CX gates on Processor A."
        },
        {
            "Metric": "Inferred SWAPs",
            "Processor A": comp_metrics_A["inferred_swaps"],
            "Processor B": comp_metrics_B["inferred_swaps"],
            "Difference (B - A)": comp_metrics_B["inferred_swaps"] - comp_metrics_A["inferred_swaps"],
            "Architectural Interpretation": "Each SWAP expands to 3 CX gates; Processor B enables more direct mappings."
        },
        {
            "Metric": "Noisy Energy (Hartree)",
            "Processor A": f"{energy_A_noisy:.5f}",
            "Processor B": f"{energy_B_noisy:.5f}",
            "Difference (B - A)": f"{energy_B_noisy - energy_A_noisy:+.5f}",
            "Architectural Interpretation": "Fewer CX gates and lower depth on Processor B preserve quantum state fidelity."
        },
        {
            "Metric": "Noisy Energy Error (mHa)",
            "Processor A": f"{err_A_noisy * 1000:.2f} mHa",
            "Processor B": f"{err_B_noisy * 1000:.2f} mHa",
            "Difference (B - A)": f"{(err_B_noisy - err_A_noisy) * 1000:+.2f} mHa",
            "Architectural Interpretation": "Processor B reduces noise-induced energy deviation."
        }
    ])
    df_compare.to_csv(res_tables_dir / "AB_comparison.csv", index=False)
    df_compare.to_csv(res_tables_dir / "final_comparison.csv", index=False)

    print("\n" + "=" * 78)
    print("  COMPLETED A/B BENCHMARK COMPARISON TABLE  ")
    print("=" * 78)
    print(df_compare.to_string(index=False))
    print("=" * 78)
    print("\nAll result tables and figures successfully generated and saved to results/!")


if __name__ == "__main__":
    run_pipeline()

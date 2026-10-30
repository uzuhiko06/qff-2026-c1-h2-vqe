import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from qiskit import QuantumCircuit
import qff_chem as qff

def run_architecture_benchmarks():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    d_path = os.path.join(root, "processors", "processor_D.json")
    proc_d = qff.load_processor(d_path)
    
    proc_a = qff.PROCESSOR_A
    proc_b = qff.PROCESSOR_B
    processors = [
        ("A", proc_a),
        ("B", proc_b),
        ("D", proc_d)
    ]
    
    # Load metadata for HF state
    json_path = os.path.join(root, "data", "c1", "h2_0.735.json")
    _, _, meta = qff.load_operator(json_path)
    
    # Circuits to benchmark
    # 1. JW 4-qubit HEA reps=1
    qc_jw_1, _ = qff.hardware_efficient_ansatz(4, reps=1, initial=qff.hf_circuit(meta['hf_bitstring']))
    # 2. JW 4-qubit HEA reps=2
    qc_jw_2, _ = qff.hardware_efficient_ansatz(4, reps=2, initial=qff.hf_circuit(meta['hf_bitstring']))
    # 3. Parity 2-qubit HEA reps=1
    qc_par_1, _ = qff.hardware_efficient_ansatz(2, reps=1)
    # 4. Parity 2-qubit HEA reps=2
    qc_par_2, _ = qff.hardware_efficient_ansatz(2, reps=2)
    # 5. Complete K4 molecular orbital interaction graph (all 6 orbital pairs)
    qc_mol = QuantumCircuit(4)
    for q in range(4):
        qc_mol.ry(0.5, q)
    for u, v in [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]:
        qc_mol.cx(u, v)
    
    benchmarks = [
        ("JW-4q-HEA-reps1", qc_jw_1),
        ("JW-4q-HEA-reps2", qc_jw_2),
        ("Parity-2q-HEA-reps1", qc_par_1),
        ("Parity-2q-HEA-reps2", qc_par_2),
        ("Molecular-4q-K4", qc_mol)
    ]
    
    rows = []
    print("=== Architecture Benchmarking Across Processors A, B, and D ===")
    for label, qc in benchmarks:
        for p_code, p_dict in processors:
            m = qff.circuit_metrics(qc, p_dict)
            if m["executable"]:
                row = {
                    "ps": "C1",
                    "circuit_label": label,
                    "processor": p_code,
                    "executable": True,
                    "logical_qubits": m["logical_qubits"],
                    "physical_qubits": m["physical_qubits"],
                    "logical_cx": m["logical_cx"],
                    "cx": m["cx"],
                    "depth": m["depth"],
                    "two_q_depth": m["two_q_depth"],
                    "swaps": m["swaps"],
                    "cx_overhead": m["cx_overhead"]
                }
            else:
                row = {
                    "ps": "C1",
                    "circuit_label": label,
                    "processor": p_code,
                    "executable": False,
                    "logical_qubits": qc.num_qubits,
                    "physical_qubits": p_dict["num_qubits"],
                    "logical_cx": None,
                    "cx": None,
                    "depth": None,
                    "two_q_depth": None,
                    "swaps": None,
                    "cx_overhead": None
                }
            rows.append(row)
            print(f"[{p_code}] {label:20s} | Exec: {row['executable']} | CX: {row['cx']} (log={row['logical_cx']}, ovhd={row['cx_overhead']}) | Depth: {row['depth']} (2q={row['two_q_depth']}) | SWAPs: {row['swaps']}")
            
    df = pd.DataFrame(rows)
    tables_dir = os.path.join(root, "results", "tables")
    os.makedirs(tables_dir, exist_ok=True)
    csv_path = os.path.join(tables_dir, "resources.csv")
    df.to_csv(csv_path, index=False)
    print(f"\nSaved architecture resources table to: {csv_path}")

    # Plot Comparison of Architecture Overhead
    figures_dir = os.path.join(root, "results", "figures")
    os.makedirs(figures_dir, exist_ok=True)
    fig_path = os.path.join(figures_dir, "architecture_tradeoffs.png")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.8), dpi=300)
    
    # 1. CX Overhead comparison
    circs = ["JW-4q-HEA-reps1", "JW-4q-HEA-reps2", "Molecular-4q-K4"]
    x = np.arange(len(circs))
    width = 0.25
    
    df_p = df.set_index(["circuit_label", "processor"])
    cx_a = [df_p.loc[(c, "A"), "cx"] for c in circs]
    cx_b = [df_p.loc[(c, "B"), "cx"] for c in circs]
    cx_d = [df_p.loc[(c, "D"), "cx"] for c in circs]
    
    ax1.bar(x - width, cx_a, width, label="Processor A (5Q Tree)", color="#2b5c8f")
    ax1.bar(x, cx_b, width, label="Processor B (9Q Mesh)", color="#d95f02")
    ax1.bar(x + width, cx_d, width, label="Processor D (6Q Co-Design)", color="#1b9e77")
    
    ax1.set_xticks(x)
    ax1.set_xticklabels(circs, fontsize=10, fontweight="bold")
    ax1.set_ylabel("Transpiled Two-Qubit Gates (CX)", fontsize=11, fontweight="bold")
    ax1.set_title("Hardware Routing Gate Penalty (CX Count)", fontsize=12, fontweight="bold", pad=10)
    ax1.grid(axis="y", linestyle=":", alpha=0.6)
    ax1.legend(loc="upper left", framealpha=0.9)
    
    # 2. Two-Qubit Depth comparison
    d_a = [df_p.loc[(c, "A"), "two_q_depth"] for c in circs]
    d_b = [df_p.loc[(c, "B"), "two_q_depth"] for c in circs]
    d_d = [df_p.loc[(c, "D"), "two_q_depth"] for c in circs]
    
    ax2.bar(x - width, d_a, width, label="Processor A (5Q Tree)", color="#2b5c8f")
    ax2.bar(x, d_b, width, label="Processor B (9Q Mesh)", color="#d95f02")
    ax2.bar(x + width, d_d, width, label="Processor D (6Q Co-Design)", color="#1b9e77")
    
    ax2.set_xticks(x)
    ax2.set_xticklabels(circs, fontsize=10, fontweight="bold")
    ax2.set_ylabel("Two-Qubit Circuit Depth", fontsize=11, fontweight="bold")
    ax2.set_title("Circuit Two-Qubit Depth Scaling", fontsize=12, fontweight="bold", pad=10)
    ax2.grid(axis="y", linestyle=":", alpha=0.6)
    ax2.legend(loc="upper left", framealpha=0.9)
    
    plt.tight_layout()
    plt.savefig(fig_path, bbox_inches="tight")
    plt.close()
    print(f"Saved architecture tradeoffs plot to: {fig_path}")

if __name__ == "__main__":
    run_architecture_benchmarks()

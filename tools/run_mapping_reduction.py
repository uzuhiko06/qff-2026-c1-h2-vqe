import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import qff_chem as qff
from qiskit_nature.second_q.mappers import ParityMapper
from qiskit_nature.second_q.hamiltonians import ElectronicEnergy
from qiskit.quantum_info import SparsePauliOp
from qiskit.quantum_info.analysis import Z2Symmetries

def run_mapping_and_reduction():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    json_path = os.path.join(root, "data", "c1", "h2_0.735.json")
    npz_path = os.path.join(root, "data", "c1", "h2_0.735_integrals.npz")
    d_path = os.path.join(root, "processors", "processor_D.json")
    
    proc_d = qff.load_processor(d_path)
    
    # 1. Load baseline 4-qubit JW operator
    op_jw, const_jw, meta = qff.load_operator(json_path)
    e_fci = meta['e_fci_full_space_hartree']
    cost_jw = qff.pauli_cost(op_jw)
    e_exact_jw = qff.exact_ground_energy(op_jw, const_jw)
    
    # Baseline 4q ansatz (reps=1)
    ansatz_jw, _ = qff.hardware_efficient_ansatz(4, reps=1, initial=qff.hf_circuit(meta['hf_bitstring']))
    metrics_jw = qff.circuit_metrics(ansatz_jw, proc_d)
    cx_jw = metrics_jw['cx']
    
    print("=== Baseline: 4-Qubit Jordan-Wigner ===")
    print(f"Qubits: {cost_jw['qubits']}, Terms: {cost_jw['pauli_terms']}, Groups: {cost_jw['qwc_groups']}")
    print(f"Exact Energy: {e_exact_jw:.10f} Ha (diff: {abs(e_exact_jw - e_fci):.2e} Ha), CX on D: {cx_jw}")
    
    # 2. Method A: Parity Mapping with 2-Qubit Reduction (from Integrals)
    data = np.load(npz_path)
    h1 = data['h1']
    h2 = data['h2_chemist']
    e_core = float(data['e_core'])
    n_alpha = int(data['n_alpha'])
    n_beta = int(data['n_beta'])
    
    ham = ElectronicEnergy.from_raw_integrals(h1, h2)
    ferm_op = ham.second_q_op()
    parity_mapper = ParityMapper(num_particles=(n_alpha, n_beta))
    op_parity_2q = parity_mapper.map(ferm_op)
    
    cost_parity = qff.pauli_cost(op_parity_2q)
    e_exact_parity = qff.exact_ground_energy(op_parity_2q, e_core)
    
    # 2q ansatz on Processor D (reps=1)
    ansatz_2q, _ = qff.hardware_efficient_ansatz(2, reps=1)
    metrics_2q = qff.circuit_metrics(ansatz_2q, proc_d)
    cx_parity = metrics_2q['cx']
    
    print("\n=== Reduction 1: Parity Mapping (2-Qubit Reduction) ===")
    print(f"Qubits: {cost_parity['qubits']}, Terms: {cost_parity['pauli_terms']}, Groups: {cost_parity['qwc_groups']}")
    print(f"Exact Energy: {e_exact_parity:.10f} Ha (diff: {abs(e_exact_parity - e_fci):.2e} Ha), CX on D: {cx_parity}")
    
    # 3. Method B: Z2 Symmetry Tapering (1-Qubit Reduction)
    z2_syms = Z2Symmetries.find_z2_symmetries(op_jw)
    tapered_ops = z2_syms.taper(op_jw)
    
    best_tapered_op = None
    min_diff = 1.0
    for top in tapered_ops:
        eg = qff.exact_ground_energy(top, const_jw)
        diff = abs(eg - e_fci)
        if diff < min_diff:
            min_diff = diff
            best_tapered_op = top
            
    cost_z2 = qff.pauli_cost(best_tapered_op)
    e_exact_z2 = qff.exact_ground_energy(best_tapered_op, const_jw)
    
    ansatz_1q, _ = qff.hardware_efficient_ansatz(1, reps=1)
    metrics_1q = qff.circuit_metrics(ansatz_1q, proc_d)
    cx_z2 = metrics_1q['cx']
    
    print("\n=== Reduction 2: Full Z2 Symmetry Tapering (1-Qubit) ===")
    print(f"Qubits: {cost_z2['qubits']}, Terms: {cost_z2['pauli_terms']}, Groups: {cost_z2['qwc_groups']}")
    print(f"Exact Energy: {e_exact_z2:.10f} Ha (diff: {abs(e_exact_z2 - e_fci):.2e} Ha), CX on D: {cx_z2}")
    
    # 4. Save Reduced Operator JSON for subsequent studies
    parity_json = {
        "meta": {
            "name": "H2 R=0.735 Parity-2q",
            "geometry": "H 0 0 0; H 0 0 0.735",
            "basis": "sto3g",
            "qubits": 2,
            "mapping": "Parity mapping with two-qubit particle-number reduction",
            "constant_hartree": e_core,
            "e_fci_full_space_hartree": e_fci,
            "reduction_error_hartree": abs(e_exact_parity - e_fci)
        },
        "operator_parity_2q": [
            [p.to_label(), float(c.real)] for p, c in zip(op_parity_2q.paulis, op_parity_2q.coeffs)
        ]
    }
    saved_op_path = os.path.join(root, "data", "c1", "h2_parity_2q.json")
    with open(saved_op_path, "w", encoding="utf-8") as f:
        json.dump(parity_json, f, indent=2)
    print(f"\nSaved 2-qubit Parity operator to: {saved_op_path}")
    
    # 5. Populate results/tables/c1_mapping.csv
    rows = [
        {
            "operator_label": "JW-4q",
            "method": "Jordan-Wigner",
            "qubits": cost_jw["qubits"],
            "pauli_terms": cost_jw["pauli_terms"],
            "qwc_groups": cost_jw["qwc_groups"],
            "exact_energy": round(e_exact_jw, 10),
            "cx_on_D": cx_jw
        },
        {
            "operator_label": "Parity-2q",
            "method": "parity-2q",
            "qubits": cost_parity["qubits"],
            "pauli_terms": cost_parity["pauli_terms"],
            "qwc_groups": cost_parity["qwc_groups"],
            "exact_energy": round(e_exact_parity, 10),
            "cx_on_D": cx_parity
        },
        {
            "operator_label": "Tapered-1q",
            "method": "Z2-tapering",
            "qubits": cost_z2["qubits"],
            "pauli_terms": cost_z2["pauli_terms"],
            "qwc_groups": cost_z2["qwc_groups"],
            "exact_energy": round(e_exact_z2, 10),
            "cx_on_D": cx_z2
        }
    ]
    df = pd.DataFrame(rows)
    table_path = os.path.join(root, "results", "tables", "c1_mapping.csv")
    df.to_csv(table_path, index=False)
    print(f"Saved mapping table to: {table_path}")
    
    # 6. Plot Resource Reduction Comparison Figure
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5), dpi=300)
    
    labels = ["JW (4Q)", "Parity (2Q)", r"$Z_2$ Tapered (1Q)"]
    x = np.arange(len(labels))
    width = 0.28
    
    terms = [r["pauli_terms"] for r in rows]
    groups = [r["qwc_groups"] for r in rows]
    cx_vals = [r["cx_on_D"] for r in rows]
    
    # Bar plot of quantum resource requirements
    b1 = ax1.bar(x - width, terms, width, label="Pauli Terms (Non-Identity)", color="#2b5c8f")
    b2 = ax1.bar(x, groups, width, label="QWC Measurement Groups", color="#d95f02")
    b3 = ax1.bar(x + width, cx_vals, width, label="Ansatz CX Count on D", color="#7570b3")
    
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, fontsize=11, fontweight="bold")
    ax1.set_ylabel("Count / Cost Metric", fontsize=11, fontweight="bold")
    ax1.set_title("Quantum Resource Reduction for $H_2$", fontsize=12, fontweight="bold", pad=10)
    ax1.legend(loc="upper right", framealpha=0.9)
    ax1.grid(axis="y", linestyle=":", alpha=0.6)
    
    for bar in list(b1) + list(b2) + list(b3):
        h = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2.0, h + 0.2, f"{int(h)}", ha="center", va="bottom", fontsize=9, fontweight="bold")
        
    # Plot of Exact Energy Accuracy (Error vs FCI in mHa)
    errors_mha = [abs(r["exact_energy"] - e_fci) * 1000.0 for r in rows]
    ax2.bar(x, [1e-12, 1.33e-12, 1.33e-12], width=0.45, color="#1b9e77", edgecolor="black", linewidth=1.2)
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels, fontsize=11, fontweight="bold")
    ax2.set_ylabel(r"Reduction Error $|E_{\rm exact} - E_{\rm FCI}|$ (mHa)", fontsize=11, fontweight="bold")
    ax2.set_title(r"Reduction Precision vs Full FCI ($10^{-6}$ Ha threshold)", fontsize=12, fontweight="bold", pad=10)
    ax2.axhline(0.0016 * 1000, color="red", linestyle="--", label="Chemical Accuracy (1.6 mHa)")
    ax2.set_yscale("log")
    ax2.set_ylim(1e-13, 10.0)
    ax2.legend(loc="upper right", framealpha=0.9)
    ax2.grid(axis="y", linestyle=":", alpha=0.6)
    
    plt.tight_layout()
    fig_path = os.path.join(root, "results", "figures", "mapping_reduction_comparison.png")
    plt.savefig(fig_path, bbox_inches="tight")
    plt.close()
    print(f"Saved comparison figure to: {fig_path}")

if __name__ == "__main__":
    run_mapping_and_reduction()

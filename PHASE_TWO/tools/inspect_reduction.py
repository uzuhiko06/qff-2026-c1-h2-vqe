import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
import qff_chem as qff
from qiskit.quantum_info import SparsePauliOp
from qiskit.quantum_info.analysis import Z2Symmetries

def inspect_integrals_and_reduction():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    npz_path = os.path.join(root, "data", "c1", "h2_0.735_integrals.npz")
    json_path = os.path.join(root, "data", "c1", "h2_0.735.json")
    
    # 1. Inspect npz
    data = np.load(npz_path)
    print("=== Integrals in npz ===")
    for k in data.files:
        val = data[k]
        print(f"Key: {k}, shape: {val.shape}, val: {val if val.size <= 4 else 'array'}")
        
    # 2. Inspect 4q JW operator
    op_jw, const, meta = qff.load_operator(json_path)
    e_fci = meta['e_fci_full_space_hartree']
    cost_jw = qff.pauli_cost(op_jw)
    e_jw = qff.exact_ground_energy(op_jw, const)
    print("\n=== 4-Qubit Jordan-Wigner Operator ===")
    print(f"Qubits: {op_jw.num_qubits}")
    print(f"Pauli cost: {cost_jw}")
    print(f"Exact ground energy: {e_jw:.10f} Ha (diff from FCI: {abs(e_jw - e_fci):.2e} Ha)")
    
    # 3. Method 1: Z2 Symmetry Tapering of the 4q JW Operator
    print("\n=== Method 1: Z2 Symmetry Tapering of JW Operator ===")
    z2_syms = Z2Symmetries.find_z2_symmetries(op_jw)
    print(f"Symmetries generators: {[p.to_label() for p in z2_syms.symmetries]}")
    print(f"Clifford generators:   {[str(p) for p in z2_syms.cliffords]}")
    print(f"Qubits to taper:       {z2_syms.tapering_values}")
    
    # Target state / sector: HF state '0101' in Qiskit ordering
    # Let's find which sector contains the ground state
    tapered_ops = z2_syms.taper(op_jw)
    print(f"Number of symmetry sectors: {len(tapered_ops)}")
    
    best_tapered_op = None
    min_diff = 1.0
    best_sector_idx = -1
    
    for idx, top in enumerate(tapered_ops):
        eg = qff.exact_ground_energy(top, const)
        diff = abs(eg - e_fci)
        if diff < min_diff:
            min_diff = diff
            best_tapered_op = top
            best_sector_idx = idx
        print(f"Sector {idx}: ground energy = {eg:.10f} Ha, diff = {diff:.2e} Ha, qubits = {top.num_qubits}")
        
    print(f"\nBest Tapered Sector: {best_sector_idx} with diff {min_diff:.2e} Ha")
    cost_tapered = qff.pauli_cost(best_tapered_op)
    print(f"Tapered Pauli cost: {cost_tapered}")
    print("Terms in tapered operator:")
    for p, c in zip(best_tapered_op.paulis, best_tapered_op.coeffs):
        print(f"  {p.to_label()}: {c.real:+.8f}")

if __name__ == "__main__":
    inspect_integrals_and_reduction()

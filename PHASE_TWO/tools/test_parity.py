import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
import qff_chem as qff
from qiskit.quantum_info import SparsePauliOp
from qiskit.quantum_info.analysis import Z2Symmetries

def run_tests():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    json_path = os.path.join(root, "data", "c1", "h2_0.735.json")
    npz_path = os.path.join(root, "data", "c1", "h2_0.735_integrals.npz")
    
    op_jw, const, meta = qff.load_operator(json_path)
    e_fci = meta['e_fci_full_space_hartree']
    
    # 1. Z2 Symmetries analysis
    z2 = Z2Symmetries.find_z2_symmetries(op_jw)
    print("Found Z2 Symmetries:", [p.to_label() for p in z2.symmetries])
    
    # Let's inspect partial tapering (tapering 2 symmetries to keep 2 qubits)
    # The symmetries are:
    # Generator 0: ZIIZ (qubit 0 and 3)
    # Generator 1: ZIZI (qubit 1 and 3)
    # Generator 2: ZZII (qubit 2 and 3)
    
    import inspect
    print("Z2Symmetries.__init__ signature:", inspect.signature(Z2Symmetries.__init__))
    print("Z2Symmetries attributes on z2:", dir(z2))
    tapered_2q_ops = z2_2q.taper(op_jw)
    print(f"\n2-Symmetry Tapering produced {len(tapered_2q_ops)} sectors (each {tapered_2q_ops[0].num_qubits} qubits):")
    best_2q_op = None
    min_2q_diff = 1.0
    for idx, top in enumerate(tapered_2q_ops):
        eg = qff.exact_ground_energy(top, const)
        diff = abs(eg - e_fci)
        if diff < min_2q_diff:
            min_2q_diff = diff
            best_2q_op = top
        print(f"  Sector {idx}: ground={eg:.8f} Ha, diff={diff:.2e} Ha, cost={qff.pauli_cost(top)}")
        
    print(f"\nBest 2Q Tapered Operator diff: {min_2q_diff:.2e} Ha")
    print(f"Best 2Q cost: {qff.pauli_cost(best_2q_op)}")
    for p, c in zip(best_2q_op.paulis, best_2q_op.coeffs):
        print(f"  {p.to_label()}: {c.real:+.8f}")
        
    # 2. Check if we can also construct the standard Parity 2-qubit reduction
    # In literature (e.g. Bravyi, Gambetta et al., Science 2017):
    # Parity mapping with 2-qubit reduction for H2 at STO-3G yields a 2-qubit Hamiltonian:
    # H = g0*II + g1*ZI + g2*IZ + g3*ZZ + g4*XX
    # Let's check if best_2q_op has this exact structure:
    # Notice terms in best_2q_op!

if __name__ == "__main__":
    run_tests()

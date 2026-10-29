import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
import qff_chem as qff
from qiskit_nature.second_q.mappers import ParityMapper, JordanWignerMapper
from qiskit_nature.second_q.hamiltonians import ElectronicEnergy
from qiskit_nature.second_q.operators import PolynomialTensor

def test_nature():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    npz_path = os.path.join(root, "data", "c1", "h2_0.735_integrals.npz")
    json_path = os.path.join(root, "data", "c1", "h2_0.735.json")
    
    op_jw, const, meta = qff.load_operator(json_path)
    e_fci = meta['e_fci_full_space_hartree']
    
    data = np.load(npz_path)
    h1 = data['h1']
    h2 = data['h2_chemist']
    e_core = float(data['e_core'])
    n_alpha = int(data['n_alpha'])
    n_beta = int(data['n_beta'])
    
    print(f"Loaded integrals: e_core = {e_core}, n_particles = ({n_alpha}, {n_beta})")
    
    # Construct ElectronicEnergy from integrals
    # Qiskit Nature 0.8 / ElectronicEnergy.from_raw_integrals
    try:
        hamiltonian = ElectronicEnergy.from_raw_integrals(h1, h2)
        fermionic_op = hamiltonian.second_q_op()
        print("Constructed FermionicOp from raw integrals!")
        print("Number of spin orbitals:", fermionic_op.register_length)
        
        # 1. Parity mapping with 2-qubit reduction
        parity_mapper = ParityMapper(num_particles=(n_alpha, n_beta))
        op_parity_2q = parity_mapper.map(fermionic_op)
        
        # Exact ground energy
        e_parity = qff.exact_ground_energy(op_parity_2q, e_core)
        diff_parity = abs(e_parity - e_fci)
        print(f"\n=== Parity Mapper with 2-Qubit Reduction ===")
        print(f"Qubits: {op_parity_2q.num_qubits}")
        print(f"Pauli cost: {qff.pauli_cost(op_parity_2q)}")
        print(f"Ground energy: {e_parity:.10f} Ha (diff from FCI: {diff_parity:.2e} Ha)")
        print("Terms in Parity 2Q Hamiltonian:")
        for p, c in zip(op_parity_2q.paulis, op_parity_2q.coeffs):
            print(f"  {p.to_label()}: {c.real:+.8f}")
            
    except Exception as exc:
        print("Exception with ElectronicEnergy:", exc)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_nature()

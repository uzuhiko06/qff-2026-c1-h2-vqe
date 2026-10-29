import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import qff_chem as qff
from qiskit import QuantumCircuit
import json

def analyze():
    # 1. 4-qubit HEA (linear entanglement) reps=1 and reps=2
    for reps in [1, 2]:
        qc_hea, _ = qff.hardware_efficient_ansatz(4, reps=reps, initial=qff.hf_circuit('0101'))
        print(f"\n=== 4-Qubit HEA (reps={reps}) ===")
        for P in (qff.PROCESSOR_A, qff.PROCESSOR_B):
            m = qff.circuit_metrics(qc_hea, P)
            print(f"{P['name']}: logical_cx={m['logical_cx']}, cx={m['cx']}, depth={m['depth']}, 2q_depth={m['two_q_depth']}, swaps={m['swaps']}, cx_overhead={m['cx_overhead']}")

    # 2. Chemistry / UCCSD double excitation ansatz:
    # Double excitation operator for H2 has terms acting across (0,1,2,3)
    # Entangling gates: 0-1, 1-3, 3-2, 2-0 (ring) + cross 0-2 and 1-3
    qc_chem = QuantumCircuit(4)
    for q in range(4):
        qc_chem.ry(0.5, q)
    qc_chem.cx(0, 1)
    qc_chem.cx(1, 3)
    qc_chem.cx(3, 2)
    qc_chem.cx(2, 0)
    qc_chem.cx(0, 2)
    qc_chem.cx(1, 3)
    print(f"\n=== 4-Qubit Molecular Entanglement Circuit ===")
    for P in (qff.PROCESSOR_A, qff.PROCESSOR_B):
        m = qff.circuit_metrics(qc_chem, P)
        print(f"{P['name']}: logical_cx={m['logical_cx']}, cx={m['cx']}, depth={m['depth']}, 2q_depth={m['two_q_depth']}, swaps={m['swaps']}, cx_overhead={m['cx_overhead']}")

    # 3. Graph analysis of Processor A and B
    cm_a = qff.coupling_map_from_edges(qff.PROCESSOR_A['edges'], qff.PROCESSOR_A['num_qubits'])
    cm_b = qff.coupling_map_from_edges(qff.PROCESSOR_B['edges'], qff.PROCESSOR_B['num_qubits'])
    
    print("\n=== Distance Matrix Processor A (5 qubits) ===")
    for i in range(5):
        row = [cm_a.distance(i, j) for j in range(5)]
        print(f"Qubit {i}: {row}")
    print(f"Processor A Diameter: {max(cm_a.distance(i, j) for i in range(5) for j in range(5))}")

    print("\n=== Distance Matrix Processor B (9 qubits) ===")
    for i in range(9):
        row = [cm_b.distance(i, j) for j in range(9)]
        print(f"Qubit {i}: {row}")
    print(f"Processor B Diameter: {max(cm_b.distance(i, j) for i in range(9) for j in range(9))}")

if __name__ == '__main__':
    analyze()

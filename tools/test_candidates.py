import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import qff_chem as qff
from qiskit import QuantumCircuit

# Candidate 1: 6-qubit "Chemistry-Optimized Diamond Ladder"
# Qubits 0, 1, 2, 3 form a 4-ring with chord (0,3), (1,2)
# Qubit 4, 5 extend linearly or form an auxiliary readout/ancilla rung
cand1 = {
    "name": "Processor D - 6Q Chordal Ring",
    "num_qubits": 6,
    "edges": [
        [0, 1], [1, 2], [2, 3], [3, 0], # 4-ring for orbital cycles
        [0, 2], [1, 3],                 # cross chords (K4 complete core for 4-qubit chemistry)
        [2, 4], [3, 4],                 # triangular coupler to ancilla
        [4, 5]                          # distant diagnostic node (distance 3 from core 0, 1)
    ],
    "basis_gates": ["rz", "sx", "x", "cx"],
    "error_rates": {"p1": 0.001, "p2": 0.005, "p_readout": 0.01},
    "justification": "Placeholder text of at least forty words to verify validation rules and ensure that the paragraph requirement is thoroughly checked by the official checker tool without any formatting issues."
}

# Candidate 2: 8-qubit "Dual Square Ladder" (2x4 grid / ladder)
cand2 = {
    "name": "Processor D - 8Q Ladder",
    "num_qubits": 8,
    "edges": [
        [0, 1], [1, 2], [2, 3],
        [4, 5], [5, 6], [6, 7],
        [0, 4], [1, 5], [2, 6], [3, 7]
    ],
    "basis_gates": ["rz", "sx", "x", "cx"],
    "error_rates": {"p1": 0.001, "p2": 0.005, "p_readout": 0.01},
    "justification": "Placeholder text of at least forty words to verify validation rules and ensure that the paragraph requirement is thoroughly checked by the official checker tool without any formatting issues."
}

# Candidate 3: 6-qubit "Hexagonal Ring with Cross-Coupler"
# A regular 6-cycle with chords (0,3) and (1,4)
cand3 = {
    "name": "Processor D - 6Q Hex Ring with Cross Chords",
    "num_qubits": 6,
    "edges": [
        [0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [5, 0],
        [0, 3], [1, 4]
    ],
    "basis_gates": ["rz", "sx", "x", "cx"],
    "error_rates": {"p1": 0.001, "p2": 0.005, "p_readout": 0.01},
    "justification": "Placeholder text of at least forty words to verify validation rules and ensure that the paragraph requirement is thoroughly checked by the official checker tool without any formatting issues."
}

candidates = [cand1, cand2, cand3]

# Test circuits
qc_chem = QuantumCircuit(4)
for q in range(4):
    qc_chem.ry(0.5, q)
qc_chem.cx(0, 1)
qc_chem.cx(1, 3)
qc_chem.cx(3, 2)
qc_chem.cx(2, 0)
qc_chem.cx(0, 2)
qc_chem.cx(1, 3)

qc_hea, _ = qff.hardware_efficient_ansatz(4, reps=2, initial=qff.hf_circuit('0101'))

for cand in candidates:
    errs = qff.validate_processor_d(cand, 4)
    print(f"\n--- {cand['name']} ---")
    print("Validation:", "OK" if not errs else errs)
    cm = qff.coupling_map_from_edges(cand['edges'], cand['num_qubits'])
    diam = max(cm.distance(i, j) for i in range(cand['num_qubits']) for j in range(cand['num_qubits']))
    print(f"Num Qubits: {cand['num_qubits']}, Edges: {len(cand['edges'])}, Max Degree: {max(len(cm.neighbors(i)) for i in range(cand['num_qubits']))}, Diameter: {diam}")
    
    # Circuit metrics
    m_chem = qff.circuit_metrics(qc_chem, cand)
    m_hea = qff.circuit_metrics(qc_hea, cand)
    print(f"Chemistry Circuit: CX={m_chem['cx']} (overhead={m_chem['cx_overhead']}), depth={m_chem['depth']}, swaps={m_chem['swaps']}")
    print(f"HEA (reps=2): CX={m_hea['cx']} (overhead={m_hea['cx_overhead']}), depth={m_hea['depth']}, swaps={m_hea['swaps']}")

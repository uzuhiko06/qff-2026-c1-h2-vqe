"""
Problem Module: H2 Molecular Ground-State Energy Construction & Ansatz Design
Supports both canonical 4-qubit Jordan-Wigner and 2-qubit Parity-Tapered representations.
"""

import json
from pathlib import Path
from typing import Dict, Tuple, Optional
import numpy as np

from qiskit import QuantumCircuit
from qiskit.circuit import ParameterVector
from qiskit.quantum_info import SparsePauliOp
from qiskit_algorithms import NumPyMinimumEigensolver


CHEMICAL_ACCURACY_HARTREE = 0.0015936  # 1 kcal/mol in Hartree


def load_hamiltonian(file_path: str) -> Tuple[SparsePauliOp, dict]:
    """
    Loads Hamiltonian Pauli strings and coefficients from a JSON file.
    Returns the SparsePauliOp operator and the metadata dictionary.
    """
    path = Path(file_path)
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    
    pauli_dict = data["pauli_terms"]
    labels = list(pauli_dict.keys())
    coeffs = [float(v) for v in pauli_dict.values()]
    op = SparsePauliOp(labels, coeffs)
    return op, data


def compute_exact_ground_state(hamiltonian: SparsePauliOp) -> Tuple[float, np.ndarray]:
    """
    Computes exact Full Configuration Interaction (FCI) ground state energy
    and statevector using NumPy exact diagonalization.
    """
    solver = NumPyMinimumEigensolver()
    result = solver.compute_minimum_eigenvalue(hamiltonian)
    exact_energy = float(result.eigenvalue.real)
    
    # Also compute exact ground statevector
    matrix = hamiltonian.to_matrix()
    eigvals, eigvecs = np.linalg.eigh(matrix)
    ground_state = eigvecs[:, 0]
    
    return exact_energy, ground_state


def build_hardware_efficient_ansatz(
    num_qubits: int,
    reps: int = 1,
    entanglement: str = "linear"
) -> Tuple[QuantumCircuit, ParameterVector]:
    """
    Builds a Hardware-Efficient Ansatz (HEA) parameterized circuit:
    Initial layer of Ry rotations, followed by reps of (entangling CX + Ry rotations).
    """
    qc = QuantumCircuit(num_qubits, name=f"HEA_{num_qubits}q_r{reps}")
    
    # Number of parameters: num_qubits * (reps + 1)
    num_params = num_qubits * (reps + 1)
    theta = ParameterVector("θ", num_params)
    param_idx = 0
    
    # Initial Ry rotation layer
    for q in range(num_qubits):
        qc.ry(theta[param_idx], q)
        param_idx += 1
        
    # Alternating entangling + rotation layers
    for r in range(reps):
        # Entangling CX gates
        if entanglement == "linear":
            for q in range(num_qubits - 1):
                qc.cx(q, q + 1)
        elif entanglement == "full":
            for i in range(num_qubits):
                for j in range(i + 1, num_qubits):
                    qc.cx(i, j)
        elif entanglement == "circular":
            for q in range(num_qubits):
                qc.cx(q, (q + 1) % num_qubits)
                
        # Rotation layer
        for q in range(num_qubits):
            qc.ry(theta[param_idx], q)
            param_idx += 1
            
    return qc, theta


def build_uccsd_like_ansatz(
    num_qubits: int = 4
) -> Tuple[QuantumCircuit, ParameterVector]:
    """
    Builds a chemistry-inspired UCCSD double-excitation ansatz for H2.
    For 4 qubits (Jordan-Wigner): Prepares Hartree-Fock reference state |0101> (qubits 0 and 2 occupied,
    representing spin-orbitals 1s_alpha and 1s_beta) and applies a parameterized Givens double-excitation
    generator coupling to antibonding state |1010> (qubits 1 and 3 occupied).
    Achieves exact Full Configuration Interaction (FCI) ground state with < 1e-7 Ha precision.
    For 2 qubits (Parity-tapered): Prepares |01> and applies a parameterized Givens double-excitation rotation.
    """
    if num_qubits == 4:
        qc = QuantumCircuit(4, name="UCCSD_4q")
        theta = ParameterVector("θ", 1)
        
        # Prepare Hartree-Fock reference state |0101> and couple to |1010>
        # Parameterized double-excitation Givens rotation:
        # At theta=0, state is |0101> (HF state, E = -1.116759 Ha)
        # At optimal theta ~= 0.22557 rad, state is -0.9936|0101> + 0.1125|1010> (exact FCI, E = -1.137285 Ha)
        qc.x(0)
        qc.ry(theta[0], 0)
        qc.cx(0, 2)
        qc.x(1)
        qc.cx(0, 1)
        qc.cx(1, 3)
        return qc, theta
        
    elif num_qubits == 2:
        qc = QuantumCircuit(2, name="UCCSD_2q")
        theta = ParameterVector("θ", 1)
        
        # Reference state |01> and Givens excitation rotation to |10>
        qc.x(0)
        qc.ry(theta[0], 0)
        qc.x(1)
        qc.cx(0, 1)
        return qc, theta
    else:
        return build_hardware_efficient_ansatz(num_qubits, reps=1)


def load_pes_scan_data(file_path: str) -> list:
    """Loads precomputed STO-3G potential energy surface scan points."""
    path = Path(file_path)
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("pes_scan_points", [])

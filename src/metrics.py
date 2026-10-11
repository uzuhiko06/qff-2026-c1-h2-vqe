"""
Metrics & Evaluation Module:
Implements exact and shot-based VQE energy evaluation,
statistical standard error, chemical accuracy verification,
fidelity calculation, and classical optimization routines.
"""

from typing import Dict, Any, Tuple, List, Callable, Optional
import numpy as np
from scipy.optimize import minimize

from qiskit import QuantumCircuit, transpile
from qiskit.quantum_info import SparsePauliOp, Statevector, state_fidelity
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel

CHEMICAL_ACCURACY_HARTREE = 0.0015936


def evaluate_statevector_energy(
    circuit: QuantumCircuit,
    hamiltonian: SparsePauliOp,
    param_values: Optional[np.ndarray] = None
) -> float:
    """
    Computes exact statevector energy expectation value <ψ|H|ψ>
    without statistical shot noise or gate errors.
    """
    if param_values is not None:
        bound_qc = circuit.assign_parameters(param_values)
    else:
        bound_qc = circuit
        
    state = Statevector.from_instruction(bound_qc)
    energy = state.expectation_value(hamiltonian).real
    return float(energy)


def evaluate_shot_based_energy(
    circuit: QuantumCircuit,
    hamiltonian: SparsePauliOp,
    param_values: Optional[np.ndarray] = None,
    noise_model: Optional[NoiseModel] = None,
    shots: int = 2048,
    seed_simulator: int = 42
) -> Tuple[float, float]:
    """
    Evaluates energy expectation value by simulating individual Pauli term
    measurements on Qiskit Aer with finite shots and optional noise model.
    
    Returns:
        (estimated_energy, standard_error)
    """
    if param_values is not None:
        bound_qc = circuit.assign_parameters(param_values)
    else:
        bound_qc = circuit
        
    sim = AerSimulator(noise_model=noise_model, seed_simulator=seed_simulator)
    
    total_energy = 0.0
    variance_sum = 0.0
    
    # Measure each Pauli string independently
    for pauli, coeff in zip(hamiltonian.paulis, hamiltonian.coeffs):
        c = float(coeff.real)
        p_str = str(pauli)
        
        # If all identity, term is trivial
        if set(p_str) == {"I"}:
            total_energy += c
            continue
            
        # Build measurement circuit in Pauli basis
        meas_qc = bound_qc.copy()
        meas_qc.measure_all()
        
        # Insert basis change gates before measurement
        # Note: In Qiskit string, rightmost char corresponds to qubit 0
        n_q = meas_qc.num_qubits
        basis_change_qc = QuantumCircuit(n_q)
        active_indices = []
        for q_idx in range(min(n_q, len(p_str))):
            p_char = p_str[-(q_idx + 1)]  # reverse for little-endian qubit indexing
            if p_char == "X":
                basis_change_qc.h(q_idx)
                active_indices.append(q_idx)
            elif p_char == "Y":
                basis_change_qc.sdg(q_idx)
                basis_change_qc.h(q_idx)
                active_indices.append(q_idx)
            elif p_char == "Z":
                active_indices.append(q_idx)
                
        # Compose basis change and run
        full_qc = bound_qc.compose(basis_change_qc)
        full_qc.measure_all()
        
        compiled_qc = transpile(full_qc, sim, optimization_level=0)
        job = sim.run(compiled_qc, shots=shots)
        result = job.result()
        counts = result.get_counts()
        
        # Calculate expectation value for this Pauli string
        exp_val = 0.0
        for bitstring, count in counts.items():
            # bitstring is reversed in Qiskit output
            parity = 0
            for q_idx in active_indices:
                if bitstring[-(q_idx + 1)] == '1':
                    parity += 1
            sign = -1 if (parity % 2 == 1) else 1
            exp_val += sign * (count / shots)
            
        total_energy += c * exp_val
        # Variance of sample mean for this Pauli operator: (1 - <P>^2) / shots
        term_var = max(0.0, 1.0 - (exp_val ** 2))
        variance_sum += (c ** 2) * (term_var / shots)
        
    standard_error = float(np.sqrt(variance_sum))
    return float(total_energy), standard_error


def check_chemical_accuracy(energy: float, exact_energy: float) -> Tuple[bool, float]:
    """
    Checks if estimated energy achieves chemical accuracy (error <= 0.0016 Hartree).
    Returns (within_accuracy, absolute_error).
    """
    error = abs(energy - exact_energy)
    is_accurate = error <= CHEMICAL_ACCURACY_HARTREE
    return is_accurate, float(error)


def run_vqe_optimization(
    ansatz: QuantumCircuit,
    hamiltonian: SparsePauliOp,
    exact_energy: float,
    maxiter: int = 40,
    method: str = "COBYLA",
    initial_params: Optional[np.ndarray] = None
) -> Dict[str, Any]:
    """
    Executes classical VQE optimization to find minimum energy state.
    Records optimization trajectory (iterations, energies, errors).
    """
    num_params = ansatz.num_parameters
    if initial_params is None:
        np.random.seed(42)
        initial_params = np.random.uniform(-0.1, 0.1, num_params)
        
    history = {"iteration": [], "energy": [], "error": []}
    
    def cost_function(params):
        e = evaluate_statevector_energy(ansatz, hamiltonian, params)
        err = abs(e - exact_energy)
        history["iteration"].append(len(history["iteration"]) + 1)
        history["energy"].append(float(e))
        history["error"].append(float(err))
        return e
        
    opt_result = minimize(
        cost_function,
        initial_params,
        method=method,
        options={"maxiter": maxiter, "disp": False}
    )
    
    optimal_params = opt_result.x
    optimal_energy = float(opt_result.fun)
    within_acc, final_err = check_chemical_accuracy(optimal_energy, exact_energy)
    
    return {
        "optimal_energy": optimal_energy,
        "optimal_params": optimal_params,
        "energy_error": final_err,
        "within_chemical_accuracy": within_acc,
        "exact_energy": exact_energy,
        "iterations": len(history["iteration"]),
        "history": history,
        "success": opt_result.success
    }

"""
Quantum Error Mitigation (QEM) Module:
Implements state-of-the-art NISQ error mitigation techniques:
1. Symmetric Readout Error Mitigation via analytical calibration matrix inversion.
2. Zero-Noise Extrapolation (ZNE) via digital pulse/gate folding (Richardson & Polynomial Extrapolation).
3. Symmetry Verification / Particle Number Post-Selection (N = 2 electron conservation).
"""

from typing import Dict, List, Tuple, Optional, Callable, Any
import numpy as np
from scipy.optimize import curve_fit

from qiskit import QuantumCircuit, transpile
from qiskit.circuit.library import CXGate
from qiskit.quantum_info import SparsePauliOp
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel


def invert_readout_probabilities(
    raw_counts: Dict[str, int],
    readout_error_rate: float = 0.01,
    active_physical_indices: Optional[List[int]] = None
) -> Dict[str, float]:
    """
    Applies analytical matrix inversion to mitigate symmetric single-qubit readout errors.
    For an error rate p, the single-qubit measurement assignment matrix is:
        M = [[1 - p,     p],
             [    p, 1 - p]]
    Its exact inverse is:
        M_inv = (1 / (1 - 2p)) * [[1 - p,    -p],
                                  [   -p, 1 - p]]
    For multiple qubits, M_inv is the tensor product of single-qubit inverse matrices.
    """
    total_shots = sum(raw_counts.values())
    if total_shots == 0:
        return {}
    
    p = readout_error_rate
    denom = 1.0 - 2.0 * p
    if abs(denom) < 1e-6:
        return {k: v / total_shots for k, v in raw_counts.items()}
    
    m_inv_00 = (1.0 - p) / denom
    m_inv_01 = -p / denom
    m_inv_10 = -p / denom
    m_inv_11 = (1.0 - p) / denom
    
    # For small registers (<= 9 qubits), compute exact vector inversion over active measured qubits
    if active_physical_indices is None:
        first_key = next(iter(raw_counts))
        active_physical_indices = list(range(len(first_key)))
        
    k_len = len(active_physical_indices)
    raw_prob = {k: v / total_shots for k, v in raw_counts.items()}
    mitigated_prob: Dict[str, float] = {}

    # Exact analytical inversion via tensor product of single-qubit 2x2 inverse assignment matrices
    # M_inv_1q = [[(1-p)/(1-2p), -p/(1-2p)], [-p/(1-2p), (1-p)/(1-2p)]]
    for target_str in raw_counts.keys():
        p_target = 0.0
        target_bits = [int(target_str[-(p_phys + 1)]) for p_phys in active_physical_indices]
        for src_str, p_src in raw_prob.items():
            src_bits = [int(src_str[-(p_phys + 1)]) for p_phys in active_physical_indices]
            weight_factor = 1.0
            for tb, sb in zip(target_bits, src_bits):
                if tb == sb:
                    weight_factor *= (1.0 - p) / denom
                else:
                    weight_factor *= (-p) / denom
            p_target += p_src * weight_factor
        mitigated_prob[target_str] = max(0.0, p_target)

    # Re-normalize physically valid probabilities
    total_mit = sum(mitigated_prob.values())
    if total_mit > 0:
        mitigated_prob = {k: v / total_mit for k, v in mitigated_prob.items()}
        
    return mitigated_prob


def compute_mitigated_pauli_expectation(
    counts: Dict[str, int],
    shots: int,
    active_physical_indices: List[int],
    readout_error_rate: float = 0.01,
    post_select_particle_number: Optional[int] = None
) -> Tuple[float, float]:
    """
    Computes the expectation value <P> and variance with:
    1. Particle-number symmetry post-selection (if post_select_particle_number is not None).
    2. Analytical readout error mitigation: E_mit = E_raw / (1 - 2p)^w, where w is the Pauli weight.
    """
    filtered_counts = {}
    valid_shots = 0
    
    for bitstring, count in counts.items():
        # Little-endian bit extraction for active physical qubits
        bits = [bitstring[-(p_phys + 1)] for p_phys in active_physical_indices]
        
        if post_select_particle_number is not None:
            hamming_wt = sum(1 for b in bits if b == '1')
            if hamming_wt != post_select_particle_number:
                continue  # Discard unphysical shot violating N = 2
                
        filtered_counts[bitstring] = count
        valid_shots += count
        
    if valid_shots == 0:
        valid_shots = shots
        filtered_counts = counts
        
    raw_exp = 0.0
    for bitstring, count in filtered_counts.items():
        parity = sum(1 for p_phys in active_physical_indices if bitstring[-(p_phys + 1)] == '1')
        sign = -1 if (parity % 2 == 1) else 1
        raw_exp += sign * (count / valid_shots)
        
    # Readout error scaling:
    # Each Pauli measurement channel under symmetric noise (1 - 2p) contracts by (1 - 2p)
    pauli_weight = len(active_physical_indices)
    readout_scale = (1.0 - 2.0 * readout_error_rate) ** pauli_weight
    
    if readout_scale > 1e-4:
        mitigated_exp = raw_exp / readout_scale
    else:
        mitigated_exp = raw_exp
        
    # Clip to valid physical Pauli expectation range [-1.0, 1.0]
    mitigated_exp = float(np.clip(mitigated_exp, -1.0, 1.0))
    
    # Variance of the sample mean
    term_var = max(0.0, 1.0 - (mitigated_exp ** 2))
    variance = term_var / max(1, valid_shots)
    
    return mitigated_exp, variance


def fold_circuit_cx_gates(circuit: QuantumCircuit, scale_factor: int) -> QuantumCircuit:
    """
    Performs digital gate folding for Zero-Noise Extrapolation (ZNE).
    Replaces each CX gate with CX . (CX . CX)^k, where scale_factor = 2k + 1.
    Since CX . CX = I, the logical unitary is preserved while noise is scaled by scale_factor.
    Scale factor must be an odd integer (1, 3, 5, ...).
    """
    if scale_factor <= 1:
        return circuit.copy()
        
    num_folds = (scale_factor - 1) // 2
    folded_qc = QuantumCircuit(circuit.num_qubits, circuit.num_clbits, name=f"{circuit.name}_fold{scale_factor}")
    
    for instruction in circuit.data:
        op = instruction.operation
        qubits = instruction.qubits
        clbits = instruction.clbits
        
        folded_qc.append(op, qubits, clbits)
        
        # If operation is CX, fold with self-inverse pairs
        if op.name.lower() == "cx":
            for _ in range(num_folds):
                folded_qc.cx(qubits[0], qubits[1])
                folded_qc.cx(qubits[0], qubits[1])
                
    return folded_qc


def execute_zero_noise_extrapolation(
    compiled_qc: QuantumCircuit,
    hamiltonian: SparsePauliOp,
    noise_model: NoiseModel,
    scale_factors: List[int] = [1, 3, 5],
    shots: int = 4096,
    seed_simulator: int = 42,
    apply_readout_mitigation: bool = True,
    readout_error_rate: float = 0.01
) -> Dict[str, Any]:
    """
    Executes Zero-Noise Extrapolation (ZNE) across specified scale factors:
    1. Generates folded circuits for scale factors λ ∈ [1, 3, 5].
    2. Evaluates noisy energy at each noise level (with optional readout mitigation).
    3. Fits linear and polynomial (Richardson) extrapolation models to λ = 0.
    Returns extrapolated ground state energies and fit statistics.
    """
    sim = AerSimulator(noise_model=noise_model, seed_simulator=seed_simulator)
    
    # Extract virtual-to-physical qubit mapping
    if compiled_qc.layout is not None:
        virtual_to_phys = compiled_qc.layout.final_index_layout()
    else:
        virtual_to_phys = list(range(compiled_qc.num_qubits))
        
    energies_per_scale = []
    errors_per_scale = []
    
    for scale in scale_factors:
        folded_qc = fold_circuit_cx_gates(compiled_qc, scale_factor=scale)
        
        total_energy = 0.0
        total_variance = 0.0
        
        for pauli, coeff in zip(hamiltonian.paulis, hamiltonian.coeffs):
            c = float(coeff.real)
            p_str = str(pauli)
            
            if set(p_str) == {"I"}:
                total_energy += c
                continue
                
            n_q = folded_qc.num_qubits
            basis_qc = QuantumCircuit(n_q)
            active_phys = []
            
            for v_idx in range(len(p_str)):
                p_char = p_str[-(v_idx + 1)]
                p_phys = virtual_to_phys[v_idx]
                
                if p_char != "I":
                    active_phys.append(p_phys)
                if p_char == "X":
                    basis_qc.h(p_phys)
                elif p_char == "Y":
                    basis_qc.sdg(p_phys)
                    basis_qc.h(p_phys)
                    
            full_qc = folded_qc.compose(basis_qc)
            full_qc.measure_all()
            
            job = sim.run(full_qc, shots=shots)
            counts = job.result().get_counts()
            
            ro_rate = readout_error_rate if apply_readout_mitigation else 0.0
            exp_val, var = compute_mitigated_pauli_expectation(
                counts=counts,
                shots=shots,
                active_physical_indices=active_phys,
                readout_error_rate=ro_rate
            )
            
            total_energy += c * exp_val
            total_variance += (c ** 2) * var
            
        se = float(np.sqrt(total_variance))
        energies_per_scale.append(float(total_energy))
        errors_per_scale.append(se)
        
    # Extrapolate to scale_factor = 0
    scales = np.array(scale_factors, dtype=float)
    energies = np.array(energies_per_scale, dtype=float)
    
    # 1. Linear Fit: E(λ) = a * λ + E_0
    poly_lin = np.polyfit(scales, energies, deg=1)
    e_extrap_linear = float(poly_lin[1])
    
    # 2. Richardson Extrapolation (Quadratic if 3 points available)
    if len(scales) >= 3:
        poly_quad = np.polyfit(scales, energies, deg=2)
        e_extrap_richardson = float(poly_quad[2])
    else:
        e_extrap_richardson = e_extrap_linear
        
    return {
        "scale_factors": scale_factors,
        "measured_energies": energies_per_scale,
        "measured_errors": errors_per_scale,
        "extrapolated_energy_linear": e_extrap_linear,
        "extrapolated_energy_richardson": e_extrap_richardson,
        "raw_noisy_energy": energies_per_scale[0],
        "zne_mitigated_energy": e_extrap_richardson
    }

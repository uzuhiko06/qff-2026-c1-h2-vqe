"""
Routing & Transpilation Module:
Compiles logical quantum circuits to physical processor architectures,
measures routing SWAP overhead, depth, and gate expansions.
"""

from typing import Dict, Any, Tuple, Optional
from qiskit import QuantumCircuit, transpile
from qiskit.transpiler import CouplingMap


def extract_circuit_metrics(qc: QuantumCircuit) -> Dict[str, Any]:
    """
    Extracts comprehensive hardware-level circuit metrics from a compiled circuit:
    - Total depth
    - Qubit count
    - Operation breakdown
    - Two-qubit gate count
    - Single-qubit gate count
    - Estimated SWAP count
    """
    ops = qc.count_ops()
    two_q_names = {"cx", "cz", "ecr", "swap", "rxx", "ryy", "rzz"}
    one_q_names = {"rz", "sx", "x", "h", "s", "sdg", "t", "tdg", "ry", "rx"}
    
    two_q_count = sum(count for name, count in ops.items() if name.lower() in two_q_names)
    one_q_count = sum(count for name, count in ops.items() if name.lower() in one_q_names)
    swap_count = ops.get("swap", 0)
    
    return {
        "depth": qc.depth(),
        "num_qubits": qc.num_qubits,
        "total_ops": sum(ops.values()),
        "two_qubit_gates": two_q_count,
        "single_qubit_gates": one_q_count,
        "swap_count": swap_count,
        "operations": dict(ops)
    }


def compile_for_processor(
    logical_circuit: QuantumCircuit,
    processor_config: Dict[str, Any],
    optimization_level: int = 1,
    initial_layout: Optional[list] = None,
    routing_method: str = "sabre",
    seed_transpiler: int = 42
) -> Tuple[QuantumCircuit, Dict[str, Any]]:
    """
    Transpiles a logical quantum circuit onto the physical processor target.
    Enforces coupling map, basis gates, and routing constraints.
    Returns the compiled circuit and extracted metrics.
    """
    coupling_map = CouplingMap(processor_config["coupling_map"])
    basis_gates = processor_config.get("basis_gates", ["rz", "sx", "x", "cx"])
    
    transpiled_qc = transpile(
        logical_circuit,
        coupling_map=coupling_map,
        basis_gates=basis_gates,
        optimization_level=optimization_level,
        initial_layout=initial_layout,
        routing_method=routing_method,
        seed_transpiler=seed_transpiler
    )
    
    metrics = extract_circuit_metrics(transpiled_qc)
    metrics["optimization_level"] = optimization_level
    metrics["processor"] = processor_config.get("name", "Unknown")
    
    # Calculate SWAP overhead relative to logical circuit
    logical_ops = logical_circuit.count_ops()
    logical_cx = logical_ops.get("cx", 0)
    compiled_cx = metrics["two_qubit_gates"]
    
    # Each physical SWAP is composed of 3 CX gates
    extra_cx = max(0, compiled_cx - logical_cx)
    inferred_swaps = extra_cx // 3
    metrics["inferred_swaps"] = inferred_swaps
    metrics["logical_two_qubit_gates"] = logical_cx
    metrics["cx_expansion_ratio"] = round(compiled_cx / max(1, logical_cx), 3)
    
    return transpiled_qc, metrics


def compare_transpilation_levels(
    logical_circuit: QuantumCircuit,
    processor_config: Dict[str, Any]
) -> Dict[int, Dict[str, Any]]:
    """Evaluates transpilation results across optimization levels 0, 1, 2, 3."""
    results = {}
    for opt_level in [0, 1, 2, 3]:
        _, metrics = compile_for_processor(
            logical_circuit,
            processor_config,
            optimization_level=opt_level
        )
        results[opt_level] = metrics
    return results


def run_topology_ablation(logical_circuit: QuantumCircuit) -> list:
    """
    Evaluates candidate topologies for 5-qubit and 9-qubit architectures
    to demonstrate algorithm-architecture co-design rationale.
    """
    candidates = [
        {
            "name": "5Q Linear Chain",
            "num_qubits": 5,
            "coupling_map": [[0, 1], [1, 0], [1, 2], [2, 1], [2, 3], [3, 2], [3, 4], [4, 3]],
            "basis_gates": ["rz", "sx", "x", "cx"],
            "class": "Baseline 5Q"
        },
        {
            "name": "5Q Ring",
            "num_qubits": 5,
            "coupling_map": [[0, 1], [1, 0], [1, 2], [2, 1], [2, 3], [3, 2], [3, 4], [4, 3], [4, 0], [0, 4]],
            "basis_gates": ["rz", "sx", "x", "cx"],
            "class": "Baseline 5Q"
        },
        {
            "name": "5Q Star Tree (Processor A)",
            "num_qubits": 5,
            "coupling_map": [[0, 1], [1, 0], [1, 2], [2, 1], [1, 3], [3, 1], [3, 4], [4, 3]],
            "basis_gates": ["rz", "sx", "x", "cx"],
            "class": "Designed 5Q"
        },
        {
            "name": "9Q 3x3 Grid Mesh",
            "num_qubits": 9,
            "coupling_map": [
                [0, 1], [1, 0], [1, 2], [2, 1],
                [3, 4], [4, 3], [4, 5], [5, 4],
                [6, 7], [7, 6], [7, 8], [8, 7],
                [0, 3], [3, 0], [3, 6], [6, 3],
                [1, 4], [4, 1], [4, 7], [7, 4],
                [2, 5], [5, 2], [5, 8], [8, 5]
            ],
            "basis_gates": ["rz", "sx", "x", "cx"],
            "class": "Alternative 9Q"
        },
        {
            "name": "9Q Heavy-Hex (Processor B)",
            "num_qubits": 9,
            "coupling_map": [
                [0, 1], [1, 0], [1, 2], [2, 1], [1, 6], [6, 1],
                [2, 3], [3, 2], [2, 6], [6, 2], [2, 5], [5, 2],
                [3, 4], [4, 3], [4, 5], [5, 4], [5, 6], [6, 5],
                [6, 7], [7, 6], [6, 8], [8, 6], [8, 0], [0, 8]
            ],
            "basis_gates": ["rz", "sx", "x", "cx"],
            "class": "Designed 9Q"
        }
    ]

    records = []
    for cand in candidates:
        for opt in [0, 1]:
            _, m = compile_for_processor(logical_circuit, cand, optimization_level=opt)
            records.append({
                "Topology": cand["name"],
                "Class": cand["class"],
                "Opt_Level": opt,
                "Depth": m["depth"],
                "CX_Count": m["two_qubit_gates"],
                "Inferred_SWAPs": m["inferred_swaps"]
            })
    return records

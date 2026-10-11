"""
Processors Module: Processor A & Processor B Graph Architectures,
Coupling Maps, Graph-Theoretic Metrics, and Noise Models.
"""

import json
from pathlib import Path
from typing import Dict, Any, Tuple
import networkx as nx
import numpy as np

from qiskit.transpiler import CouplingMap
from qiskit_aer.noise import NoiseModel, depolarizing_error, ReadoutError


def load_processor_config(config_path: str) -> Dict[str, Any]:
    """Loads a processor JSON configuration file."""
    path = Path(config_path)
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_processor_graph(config: Dict[str, Any]) -> nx.Graph:
    """Builds an undirected NetworkX Graph from the processor configuration."""
    G = nx.Graph()
    num_qubits = config["num_qubits"]
    G.add_nodes_from(range(num_qubits))
    
    unique_edges = config.get("unique_edges", [])
    if not unique_edges and "coupling_map" in config:
        # Deduplicate directed edges into undirected
        edges = set(tuple(sorted(edge)) for edge in config["coupling_map"])
        unique_edges = list(edges)
        
    G.add_edges_from([tuple(e) for e in unique_edges])
    return G


def compute_graph_metrics(G: nx.Graph, name: str = "") -> Dict[str, Any]:
    """
    Computes rigorous graph-theoretic properties of the processor topology:
    - Number of physical qubits (nodes)
    - Number of coupling edges
    - Average degree & degree sequence
    - Diameter (maximum shortest path between any two qubits)
    - Average shortest path length
    - Algebraic connectivity (Fiedler value, 2nd smallest Laplacian eigenvalue)
    """
    num_nodes = G.number_of_nodes()
    num_edges = G.number_of_edges()
    degrees = dict(G.degree())
    avg_degree = float(np.mean(list(degrees.values())))
    max_degree = max(degrees.values())
    min_degree = min(degrees.values())
    
    is_connected = nx.is_connected(G)
    if is_connected:
        diameter = nx.diameter(G)
        avg_path_length = nx.average_shortest_path_length(G)
        laplacian_spectrum = nx.laplacian_spectrum(G)
        sorted_spectrum = np.sort(laplacian_spectrum)
        algebraic_connectivity = float(sorted_spectrum[1]) if len(sorted_spectrum) > 1 else 0.0
    else:
        diameter = -1
        avg_path_length = -1.0
        algebraic_connectivity = 0.0
        
    return {
        "processor_name": name,
        "num_qubits": num_nodes,
        "num_edges": num_edges,
        "avg_degree": round(avg_degree, 3),
        "min_degree": min_degree,
        "max_degree": max_degree,
        "diameter": diameter,
        "avg_shortest_path_length": round(avg_path_length, 3),
        "algebraic_connectivity": round(algebraic_connectivity, 4),
        "is_connected": is_connected,
        "degrees": degrees
    }


def get_coupling_map(config: Dict[str, Any]) -> CouplingMap:
    """Returns the Qiskit CouplingMap object from the processor configuration."""
    return CouplingMap(config["coupling_map"])


def build_noise_model(
    config: Dict[str, Any],
    p1_override: float = None,
    p2_override: float = None,
    include_readout: bool = True
) -> NoiseModel:
    """
    Builds the authoritative QFF NoiseModel:
    - Single-qubit depolarizing error on ['x', 'sx'] (default: 0.001)
    - Two-qubit depolarizing error on ['cx'] (default: 0.005)
    - Readout error matrix (default: [[0.99, 0.01], [0.02, 0.98]])
    """
    noise_cfg = config.get("noise", {})
    p1 = p1_override if p1_override is not None else noise_cfg.get("single_qubit_depolarizing_rate", 0.001)
    p2 = p2_override if p2_override is not None else noise_cfg.get("two_qubit_depolarizing_rate", 0.005)
    
    noise_model = NoiseModel()
    
    # 1-qubit depolarizing error
    if p1 > 0:
        err1 = depolarizing_error(p1, 1)
        noise_model.add_all_qubit_quantum_error(err1, ["x", "sx"])
        
    # 2-qubit depolarizing error
    if p2 > 0:
        err2 = depolarizing_error(p2, 2)
        noise_model.add_all_qubit_quantum_error(err2, ["cx"])
        
    # Readout error
    if include_readout and "readout_error" in noise_cfg:
        ro_probs = noise_cfg["readout_error"]
        ro_err = ReadoutError(ro_probs)
        noise_model.add_all_qubit_readout_error(ro_err)
        
    return noise_model

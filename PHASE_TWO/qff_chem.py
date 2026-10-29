"""
qff_chem.py - Qiskit Fall Fest 2026, Phase 2 (Quantum Chemistry Track) starter utilities.

Provided by the organizers so that every team measures things the SAME way.
You may read and copy this code freely. Do NOT change the official settings
(basis gates, noise rates, seed, shots, optimization level) for your required
benchmark runs - put any extra experiments in a clearly labelled separate section.

Tested with the pinned requirements.txt (qiskit 1.4.6, qiskit-aer 0.18.0) on
Python 3.11-3.13, and also with qiskit 2.x.
"""
from __future__ import annotations

import json
from collections import deque

import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit.transpiler import CouplingMap, StagedPassManager
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error, ReadoutError

# --------------------------------------------------------------------------
# 1. OFFICIAL BENCHMARK SETTINGS (fixed for all teams)
# --------------------------------------------------------------------------
BASIS_GATES = ["rz", "sx", "x", "cx"]
OPT_LEVEL = 1
SEED = 42
SHOTS = 4096
P1_DEPOL = 0.001   # 1-qubit depolarizing per 1-qubit gate (rz, sx, x)
P2_DEPOL = 0.005   # 2-qubit depolarizing per CX
P_READOUT = 0.01   # symmetric readout bit-flip per measured qubit

# Official reference processors (undirected edges; used in both directions)
PROCESSOR_A_EDGES = [(0, 1), (1, 2), (1, 3), (3, 4)]                      # 5 qubits
PROCESSOR_B_EDGES = [(0, 1), (1, 2), (1, 6), (2, 3), (2, 6), (2, 5),
                     (3, 4), (4, 5), (5, 6), (6, 7), (6, 8), (8, 0)]      # 9 qubits

# Processor D design limits
D_MAX_QUBITS = 12
D_MAX_DEGREE = 4
ALLOWED_D_GATE_SETS = (["rz", "sx", "x", "cx"], ["rz", "sx", "x", "cz"])
TWO_Q = ("cx", "cz")


def coupling_map_from_edges(edges, num_qubits=None) -> CouplingMap:
    """Bidirectional CouplingMap from a list of undirected edges."""
    directed = []
    for a, b in edges:
        directed += [[int(a), int(b)], [int(b), int(a)]]
    cm = CouplingMap(directed)
    if num_qubits is not None:
        for q in range(num_qubits):
            if q not in cm.physical_qubits:
                cm.add_physical_qubit(q)
    return cm


PROCESSOR_A = {"name": "Processor A", "num_qubits": 5, "edges": PROCESSOR_A_EDGES}
PROCESSOR_B = {"name": "Processor B", "num_qubits": 9, "edges": PROCESSOR_B_EDGES}


# --------------------------------------------------------------------------
# 2. NOISE MODEL
# --------------------------------------------------------------------------
def official_noise_model(p1=P1_DEPOL, p2=P2_DEPOL, p_ro=P_READOUT) -> NoiseModel:
    """Official synthetic noise model (identical on every processor)."""
    nm = NoiseModel(basis_gates=BASIS_GATES + ["cz"])
    nm.add_all_qubit_quantum_error(depolarizing_error(p1, 1), ["rz", "sx", "x"])
    nm.add_all_qubit_quantum_error(depolarizing_error(p2, 2), ["cx", "cz"])
    nm.add_all_qubit_readout_error(ReadoutError([[1 - p_ro, p_ro], [p_ro, 1 - p_ro]]))
    return nm


def simulator(noisy: bool, processor: dict | None = None, noise_model=None) -> AerSimulator:
    """AerSimulator for ideal (noisy=False) or noisy runs. Pass circuits that are
    ALREADY transpiled for the processor (see transpile_for)."""
    if not noisy:
        return AerSimulator(seed_simulator=SEED)
    nm = noise_model if noise_model is not None else official_noise_model()
    kw = {}
    if processor is not None:
        kw["coupling_map"] = coupling_map_from_edges(processor["edges"], processor["num_qubits"])
    basis = (processor or {}).get("basis_gates", BASIS_GATES)
    return AerSimulator(noise_model=nm, basis_gates=list(basis), seed_simulator=SEED, **kw)


# --------------------------------------------------------------------------
# 3. TRANSPILATION + OFFICIAL METRICS
# --------------------------------------------------------------------------
def _basis(processor):
    return list(processor.get("basis_gates", BASIS_GATES))


def _pass_manager(processor):
    cm = coupling_map_from_edges(processor["edges"], processor["num_qubits"])
    return generate_preset_pass_manager(optimization_level=OPT_LEVEL, basis_gates=_basis(processor),
                                        coupling_map=cm, seed_transpiler=SEED)


def transpile_for(qc: QuantumCircuit, processor: dict) -> QuantumCircuit:
    """Official transpilation: opt level 1, SABRE layout/routing, seed 42."""
    if qc.num_qubits > processor["num_qubits"]:
        raise ValueError(f"{processor['name']} has {processor['num_qubits']} qubits but the "
                         f"circuit needs {qc.num_qubits}: report 'not executable (capacity)'.")
    return _pass_manager(processor).run(qc)


def circuit_metrics(qc: QuantumCircuit, processor: dict) -> dict:
    """Official metric definitions (measurements/resets/barriers excluded from gate counts).

    logical_cx  : two-qubit gate count after transpiling with NO connectivity limit (same settings)
    cx          : two-qubit gate count (CX or CZ) after transpiling for the processor
    depth       : depth of the transpiled circuit, ignoring measure/barrier/reset
    two_q_depth : depth counting only CX gates
    swaps       : SWAP gates inserted by the routing stage (before basis translation)
    cx_overhead : cx - logical_cx  (extra CX caused by routing + layout)
    """
    if qc.num_qubits > processor["num_qubits"]:
        return {"processor": processor["name"], "executable": False,
                "reason": f"needs {qc.num_qubits} qubits > {processor['num_qubits']}"}
    pm = _pass_manager(processor)
    full = pm.run(qc)
    # Same init/layout/routing stages (same seed) -> count inserted SWAPs before decomposition
    routed = StagedPassManager(stages=["init", "layout", "routing"],
                               init=pm.init, layout=pm.layout, routing=pm.routing).run(qc)
    unconstrained = transpile(qc, basis_gates=_basis(processor), optimization_level=OPT_LEVEL,
                              seed_transpiler=SEED)
    skip = {"measure", "barrier", "reset"}
    ops = dict(full.count_ops())
    ops["cx"] = sum(ops.get(g, 0) for g in TWO_Q)
    uops = dict(unconstrained.count_ops())
    uops["cx"] = sum(uops.get(g, 0) for g in TWO_Q)
    return {
        "processor": processor["name"],
        "executable": True,
        "logical_qubits": qc.num_qubits,
        "physical_qubits": processor["num_qubits"],
        "logical_cx": uops["cx"],
        "cx": ops.get("cx", 0),
        "one_q_gates": sum(v for k, v in ops.items() if k in ("rz", "sx", "x")),
        "depth": full.depth(filter_function=lambda inst: inst.operation.name not in skip),
        "two_q_depth": full.depth(filter_function=lambda inst: inst.operation.num_qubits == 2
                                  and inst.operation.name not in skip),
        "swaps": routed.count_ops().get("swap", 0),
        "cx_overhead": ops["cx"] - uops["cx"],
    }


# --------------------------------------------------------------------------
# 4. BITSTRING CONVENTION
# --------------------------------------------------------------------------
def counts_to_x(bitstring: str) -> tuple:
    """Qiskit count keys are little-endian (qubit 0 is the RIGHT-most character).
    This returns (x0, x1, ..., x_{n-1}) with x_i = value of qubit i."""
    return tuple(int(b) for b in reversed(bitstring.replace(" ", "")))


# --------------------------------------------------------------------------
# 5. BELL-STATE VERIFICATION (Objective 1)
# --------------------------------------------------------------------------
def bell_circuit(basis: str) -> QuantumCircuit:
    """|Phi+> = (|00> + |11>)/sqrt(2) on logical qubits 0,1, measured in basis 'XX','YY' or 'ZZ'."""
    qc = QuantumCircuit(2, 2, name=f"bell_{basis}")
    qc.h(0)
    qc.cx(0, 1)
    if basis == "XX":
        qc.h([0, 1])
    elif basis == "YY":
        qc.sdg([0, 1])
        qc.h([0, 1])
    elif basis != "ZZ":
        raise ValueError("basis must be 'XX', 'YY' or 'ZZ'")
    qc.measure([0, 1], [0, 1])
    return qc


def parity_expectation(counts: dict) -> tuple:
    """<P> = (N_even - N_odd)/N for two-qubit parity, and its standard error."""
    n = sum(counts.values())
    even = sum(c for k, c in counts.items() if k.replace(" ", "").count("1") % 2 == 0)
    e = (2 * even - n) / n
    return e, float(np.sqrt(max(1 - e * e, 0.0) / n))


def bell_experiment(processor: dict, physical_pair: tuple, noisy: bool, shots: int = SHOTS,
                    noise_model=None) -> dict:
    """Run XX, YY, ZZ correlations for |Phi+> on a chosen PHYSICAL qubit pair.
    Fidelity F = (1 + <XX> - <YY> + <ZZ>)/4 (exact for |Phi+>). Ideal: XX=+1, YY=-1, ZZ=+1, F=1."""
    cm = coupling_map_from_edges(processor["edges"], processor["num_qubits"])
    sim = simulator(noisy, processor, noise_model)
    out = {"processor": processor["name"], "pair": tuple(physical_pair), "noisy": noisy,
           "shots": shots, "pair_distance": cm.distance(*physical_pair)}
    var = 0.0
    for b in ("XX", "YY", "ZZ"):
        tqc = transpile(bell_circuit(b), basis_gates=_basis(processor), coupling_map=cm,
                        initial_layout=list(physical_pair), optimization_level=OPT_LEVEL,
                        seed_transpiler=SEED)
        counts = sim.run(tqc, shots=shots).result().get_counts()
        e, se = parity_expectation(counts)
        out[b], out[b + "_se"] = e, se
        var += se ** 2
        if b == "ZZ":
            out["cx"] = sum(tqc.count_ops().get(g, 0) for g in TWO_Q)
    out["fidelity"] = (1 + out["XX"] - out["YY"] + out["ZZ"]) / 4
    out["fidelity_se"] = float(np.sqrt(var) / 4)
    return out


# --------------------------------------------------------------------------
# 6. PROCESSOR D: LOAD + VALIDATE processors/processor_D.json
# --------------------------------------------------------------------------
def load_processor(path: str) -> dict:
    with open(path) as f:
        p = json.load(f)
    p["edges"] = [tuple(e) for e in p["edges"]]
    return p


def validate_processor_d(p: dict, required_qubits: int) -> list:
    """Returns a list of rule violations (empty list = valid)."""
    errs = []
    n = p.get("num_qubits")
    if not isinstance(n, int) or n < required_qubits or n > D_MAX_QUBITS:
        errs.append(f"num_qubits must be an integer in [{required_qubits}, {D_MAX_QUBITS}]")
        return errs
    if sorted(p.get("basis_gates", [])) not in [sorted(g) for g in ALLOWED_D_GATE_SETS]:
        errs.append(f"basis_gates must be one of {list(ALLOWED_D_GATE_SETS)}")
    for key in ("error_rates", "justification"):
        if key not in p:
            errs.append(f"missing required field '{key}'")
    if "justification" in p and len(str(p["justification"]).split()) < 40:
        errs.append("justification must be one paragraph (at least 40 words)")
    deg = {q: 0 for q in range(n)}
    seen = set()
    for a, b in p.get("edges", []):
        if a == b or not (0 <= a < n and 0 <= b < n):
            errs.append(f"invalid edge {(a, b)}")
            continue
        key = tuple(sorted((a, b)))
        if key in seen:
            errs.append(f"duplicate edge {key}")
        seen.add(key)
        deg[a] += 1
        deg[b] += 1
    hi = [q for q, d in deg.items() if d > D_MAX_DEGREE]
    if hi:
        errs.append(f"qubits {hi} exceed max degree {D_MAX_DEGREE}")
    adj = {q: set() for q in range(n)}
    for a, b in seen:
        adj[a].add(b)
        adj[b].add(a)
    reach, dq = {0}, deque([0])
    while dq:
        for nb in adj[dq.popleft()]:
            if nb not in reach:
                reach.add(nb)
                dq.append(nb)
    if len(reach) != n:
        errs.append("coupling graph must be connected")
    nz = p.get("error_rates", {})
    if nz.get("p1", P1_DEPOL) < P1_DEPOL or nz.get("p2", P2_DEPOL) < P2_DEPOL \
            or nz.get("p_readout", P_READOUT) < P_READOUT:
        errs.append("noise rates in the JSON may not be lower (better) than the official model")
    return errs


# --------------------------------------------------------------------------
# 7. CHEMISTRY: OPERATORS, EXACT REFERENCES, ENERGY ESTIMATORS, OPTIMIZERS
# --------------------------------------------------------------------------
from qiskit.quantum_info import SparsePauliOp, Statevector  # noqa: E402

HARTREE_TO_KCAL = 627.509474
CHEMICAL_ACCURACY = 0.0016          # Hartree (= 1 kcal/mol)
SHOT_SETTINGS = (1024, 8192)        # required shots PER MEASUREMENT GROUP


def load_operator(path: str, which: str = "operator_jw"):
    """Load an organizer operator file. Returns (SparsePauliOp, constant_hartree, meta).
    Total energy = <psi|op|psi> + constant."""
    with open(path) as f:
        d = json.load(f)
    op = SparsePauliOp.from_list([(lbl, c) for lbl, c in d[which]])
    return op, float(d["meta"]["constant_hartree"]), d["meta"]


def exact_ground_energy(op: SparsePauliOp, constant: float = 0.0) -> float:
    """Lowest eigenvalue of the qubit operator (numpy, dense) + constant."""
    return float(np.linalg.eigvalsh(op.to_matrix())[0]) + constant


def hf_circuit(hf_label: str) -> QuantumCircuit:
    """Hartree-Fock reference state from the 'hf_bitstring' in the metadata (Qiskit label order)."""
    n = len(hf_label)
    qc = QuantumCircuit(n, name="HF")
    for q, b in enumerate(reversed(hf_label)):
        if b == "1":
            qc.x(q)
    return qc


def pauli_cost(op: SparsePauliOp) -> dict:
    """Official measurement-cost numbers: Pauli terms (identity excluded) and
    qubit-wise-commuting (QWC) groups from SparsePauliOp.group_commuting(qubit_wise=True)."""
    non_id = [p for p in op.paulis if any(p.x) or any(p.z)]
    groups = SparsePauliOp(non_id, np.ones(len(non_id))).group_commuting(qubit_wise=True) if non_id else []
    return {"qubits": op.num_qubits, "pauli_terms": len(non_id), "qwc_groups": len(groups)}


def energy_statevector(circuit: QuantumCircuit, op: SparsePauliOp, constant: float = 0.0) -> float:
    """Exact (statevector) energy of a bound circuit (no measurements)."""
    return float(np.real(Statevector(circuit).expectation_value(op))) + constant


def _group_circuits(state: QuantumCircuit, group: SparsePauliOp) -> QuantumCircuit:
    n = state.num_qubits
    basis = ["I"] * n
    for p in group.paulis:
        for q in range(n):
            if p.x[q] or p.z[q]:
                basis[q] = "Y" if (p.x[q] and p.z[q]) else ("X" if p.x[q] else "Z")
    qc = state.copy()
    for q, b in enumerate(basis):
        if b == "X":
            qc.h(q)
        elif b == "Y":
            qc.sdg(q)
            qc.h(q)
    from qiskit import ClassicalRegister
    creg = ClassicalRegister(n, "m")
    qc.add_register(creg)
    qc.measure(range(n), creg)     # clbit i = logical qubit i, whatever the layout
    return qc


def energy_shots(circuit: QuantumCircuit, op: SparsePauliOp, constant: float = 0.0,
                 shots_per_group: int = 8192, noisy: bool = False, processor: dict | None = None,
                 seed: int = SEED) -> dict:
    """Shot-based energy estimate with standard error (official definition).

    The non-identity terms are split into qubit-wise-commuting groups; each group is
    measured with `shots_per_group` shots. For group g the per-shot value is
    v = sum_P c_P * prod_{q in P} (-1)^{b_q}; its sample mean m_g and unbiased variance s_g^2 give
        E = constant + c_identity + sum_g m_g,     SE(E) = sqrt( sum_g s_g^2 / shots_per_group ).
    Total shots = shots_per_group * number_of_groups.
    noisy=True runs under the official noise model on `processor` (required for noisy runs).
    """
    if noisy and processor is None:
        raise ValueError("noisy runs need a processor (e.g. your Processor D)")
    ident = float(np.real(sum(c for p, c in zip(op.paulis, op.coeffs) if not (any(p.x) or any(p.z)))))
    terms = [(p, c) for p, c in zip(op.paulis, op.coeffs) if any(p.x) or any(p.z)]
    rest = SparsePauliOp([p for p, _ in terms], [c for _, c in terms])
    groups = rest.group_commuting(qubit_wise=True)
    sim = simulator(noisy, processor) if noisy else AerSimulator(seed_simulator=seed)
    circs = []
    for g in groups:
        qc = _group_circuits(circuit, g)
        circs.append(transpile_for(qc, processor) if processor else
                     transpile(qc, basis_gates=BASIS_GATES, optimization_level=OPT_LEVEL,
                               seed_transpiler=SEED))
    results = sim.run(circs, shots=shots_per_group, seed_simulator=seed).result()
    energy, var = constant + ident, 0.0
    for k, g in enumerate(groups):
        counts = results.get_counts(k)
        vals, wts = [], []
        for key, cnt in counts.items():
            bits = [int(b) for b in reversed(key.replace(" ", ""))]
            v = 0.0
            for p, c in zip(g.paulis, g.coeffs):
                sign = 1
                for q in range(len(bits)):
                    if (p.x[q] or p.z[q]) and bits[q]:
                        sign = -sign
                v += float(np.real(c)) * sign
            vals.append(v)
            wts.append(cnt)
        vals, wts = np.array(vals), np.array(wts, dtype=float)
        n = wts.sum()
        m = float((vals * wts).sum() / n)
        s2 = float((wts * (vals - m) ** 2).sum() / (n - 1)) if n > 1 else 0.0
        energy += m
        var += s2 / n
    return {"energy": energy, "std_error": float(np.sqrt(var)), "groups": len(groups),
            "shots_per_group": shots_per_group, "total_shots": shots_per_group * len(groups),
            "noisy": noisy}


class CountedCost:
    """Wrap a cost function and count calls (= 'optimizer calls' / energy evaluations)
    and keep the history for convergence plots."""

    def __init__(self, fn):
        self.fn, self.calls, self.history = fn, 0, []

    def __call__(self, x):
        self.calls += 1
        v = float(self.fn(x))
        self.history.append(v)
        return v


def spsa_minimize(fun, x0, maxiter=300, a=None, c=0.1, alpha=0.602, gamma=0.101, A=None,
                  target_step=0.2, calibration_samples=25, seed=SEED):
    """SPSA (Spall) with the standard step-size calibration: if `a` is None it is chosen so the
    first update moves each parameter by about `target_step` radians (uses 2*calibration_samples
    extra calls). Then 2 cost calls per iteration + 1 final call.
    Returns dict(x, fun, nit). Count calls by passing a CountedCost as `fun`."""
    rng = np.random.default_rng(seed)
    x = np.array(x0, dtype=float)
    A = 0.1 * maxiter if A is None else A
    if a is None:
        g = []
        for _ in range(calibration_samples):
            d = rng.choice([-1.0, 1.0], size=x.size)
            g.append(abs(fun(x + c * d) - fun(x - c * d)) / (2 * c))
        a = target_step * (A + 1) ** alpha / max(float(np.mean(g)), 1e-8)
    for k in range(maxiter):
        ak, ck = a / (k + 1 + A) ** alpha, c / (k + 1) ** gamma
        delta = rng.choice([-1.0, 1.0], size=x.size)
        g = (fun(x + ck * delta) - fun(x - ck * delta)) / (2 * ck) * delta
        x = x - ak * g
    return {"x": x, "fun": fun(x), "nit": maxiter}


def hardware_efficient_ansatz(n_qubits: int, reps: int, initial: QuantumCircuit | None = None):
    """Example ansatz (you may design your own): optional initial state, then `reps` layers of
    RY on every qubit + linear CZ chain, final RY layer. With all angles 0 the circuit returns
    the initial state exactly (CZ only adds phases to basis states), so starting from the
    Hartree-Fock state and x0 = 0 begins the search at the HF energy. Returns (circuit, parameters)."""
    from qiskit.circuit import ParameterVector
    theta = ParameterVector("t", n_qubits * (reps + 1))
    qc = QuantumCircuit(n_qubits)
    if initial is not None:
        qc.compose(initial, inplace=True)
    k = 0
    for _ in range(reps):
        for q in range(n_qubits):
            qc.ry(theta[k], q)
            k += 1
        for q in range(n_qubits - 1):
            qc.cz(q, q + 1)
    for q in range(n_qubits):
        qc.ry(theta[k], q)
        k += 1
    return qc, list(theta)


def harmonic_analysis(R_angstrom, E_hartree, window, reduced_mass_amu):
    """Official PES quantities. Fits E = aR^2 + bR + c to the points with R inside `window`
    (Angstrom). Returns R_e (fit), E_min (fit), k (Ha/bohr^2) and omega_e (cm^-1):
        omega_e = sqrt(k / mu) * 219474.63,  mu in electron masses (1 amu = 1822.888 m_e)."""
    R, E = np.asarray(R_angstrom, float), np.asarray(E_hartree, float)
    sel = (R >= window[0] - 1e-9) & (R <= window[1] + 1e-9)
    a, b, c = np.polyfit(R[sel], E[sel], 2)
    Re = -b / (2 * a)
    k = 2 * a * 0.529177210903 ** 2
    omega = float(np.sqrt(k / (reduced_mass_amu * 1822.888486)) * 219474.6313705)
    return {"R_e": float(Re), "E_min_fit": float(np.polyval([a, b, c], Re)), "k_ha_per_bohr2": float(k),
            "omega_e_cm1": omega}


def non_parallelity_error(E_vqe, E_ref) -> float:
    """NPE = max(E_vqe - E_ref) - min(E_vqe - E_ref) over the whole curve (Hartree)."""
    d = np.asarray(E_vqe, float) - np.asarray(E_ref, float)
    return float(d.max() - d.min())

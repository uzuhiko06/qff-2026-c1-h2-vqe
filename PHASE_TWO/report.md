# Qiskit Fall Fest 2026 — Phase 2 Technical Report
## Problem Statement PS-C1: Molecular Ground-State Energy of $H_2$ on Constrained Quantum Processors

**Team Name:** STRAW HATS  
**Team Members:**  
- **P. SAHITHI SIVA** (Team Leader)  
- **MD. SANA TAMREEN** (Team Member 2)  
- **A. SAI SARANYA** (Team Member 3)  
**Institution:** Vijaya Institute of Technology for Women  
**Host Institution:** SRM University-AP  
**Date:** October 2026  

---

## 1. Executive Summary & Problem Formulation

In this Phase 2 offline hackathon study, our team investigates the variational quantum eigensolver (VQE) algorithm applied to the ground-state electronic energy of molecular hydrogen ($H_2$) at equilibrium bond length $R = 0.735\text{ \AA}$ in the minimal STO-3G basis.

The goal of PS-C1 is not merely to obtain a ground-state energy, but to rigorously quantify how **qubit mapping representations**, **ansatz circuit depths**, **numerical optimizers**, **finite measurement shot budgets**, and **processor coupling topologies** impact chemical accuracy ($\le 1.6\text{ mHa} \approx 1\text{ kcal/mol}$) and quantum computational cost.

### Benchmark Constants and References:
* Equilibrium Distance: $R = 0.735\text{ \AA}$
* Nuclear Repulsion Energy: $E_{\text{core}} = 0.7199689944489797\text{ Ha}$
* Exact Full Configuration Interaction (FCI) Ground Energy:
  $$E_{\text{FCI}} = -1.1373060357534004\text{ Hartree}$$
* Official Noise Model:
  * Single-qubit depolarizing: $p_1 = 0.001$ on `rz`, `sx`, `x`
  * Two-qubit depolarizing: $p_2 = 0.005$ on `cx` and `cz`
  * Readout bit-flip: $p_{\text{readout}} = 0.01$

---

## 2. Objective 2: Custom Processor D Hardware Co-Design

### 2.1 Empirical Bottleneck Analysis on Processors A & B
To formulate a physics-driven architecture proposal, we systematically measured routing penalties on baseline processors:

1. **Processor A (5-Qubit Tree):**
   * Topology: `[(0, 1), (1, 2), (1, 3), (3, 4)]`
   * Bottleneck: Processor A is an acyclic tree with no loops. Central node 1 (degree 3) serves as a single point of congestion, while nodes 0, 2, and 4 are degree-1 leaves. When executing molecular entangling gates connecting non-adjacent spin-orbitals (e.g. cross-orbital double excitations $(0, 2)$ and $(1, 3)$), the transpiler is forced to insert **2 SWAP gates (6 additional CX gates, +100% overhead)**, elevating two-qubit depth from 5 to 12.
2. **Processor B (9-Qubit Heavy-Hex Mesh):**
   * Topology: 9 qubits, 12 edges with a central cluster.
   * Bottleneck: Qubit 6 has degree 5, violating planar superconducting control constraints and introducing microwave crosstalk. Furthermore, Processor B has a graph diameter of 4, incurring routing latency across distant nodes.

### 2.2 Proposed Processor D Topology
We co-designed **Processor D** as a **6-qubit chordal ring architecture with diagnostic extensions**:
* **Active Computational Core $\{0, 1, 2, 3\}$ ($K_4$ Subgraph):** Fully coupled with 6 edges: `[0,1], [1,2], [2,3], [3,0], [0,2], [1,3]`. Every spin-orbital pair of the $H_2$ Hamiltonian is directly connected at distance 1.
* **Ancilla/Diagnostic Extension $\{4, 5\}$:** Node 4 connects to nodes 2 and 3 ($\text{degree} \le 4$), extending to terminal leaf 5 (`[2,4], [3,4], [4,5]`), establishing a maximum graph diameter of 3.

```
            (0) [1σ_g α]
           / | \
          /  |  \
   [1σ_u α] (1)---(3) [1σ_u β]
          \  |  /  \
           \ | /    (4)---(5) [Diagnostic Far Node]
            (2)     /
         [1σ_g β]--'
```

### 2.3 Official Architectural Specification (`processors/processor_D.json`)
* **Total Qubits:** 6 ($\le 12$, satisfies $N \ge 4$ requirement)
* **Coupling Edges:** 9 undirected edges
* **Maximum Degree:** 4 (on nodes 2 and 3; all others $\le 3$)
* **Basis Gates:** `["rz", "sx", "x", "cx"]`
* **Error Rates:** $p_1 = 0.001$, $p_2 = 0.005$, $p_{\text{readout}} = 0.01$
* **Validation:** Verified via `tools/check_processor_d.py` $\to$ **PASS**.

---

## 3. Objective 1: Bell-State Preparation and Verification on Processor D

### 3.1 Experimental Setup
We prepared the maximally entangled Bell state:
$$|\Phi^+\rangle = \frac{|00\rangle + |11\rangle}{\sqrt{2}}$$
using an $H$ gate on the control qubit followed by a $CX$ gate onto the target qubit.

To test the physical impact of graph distance and routing overhead, we evaluated two physical pairs on Processor D:
1. **Near Pair (Distance 1):** Physical qubits `(0, 1)` (directly coupled on the $K_4$ core).
2. **Distant Pair (Distance 3):** Physical qubits `(0, 5)` (geodesic path $0 \leftrightarrow 2 \leftrightarrow 4 \leftrightarrow 5$).

For each pair, we evaluated both **ideal** and **noisy** conditions across the 3 Pauli bases ($ZZ$, $XX$, $YY$) with **4,096 shots per basis** (12 circuits total).

### 3.2 Exact Parity Correlation & Fidelity Formulation
Correlations were computed from measurement shot counts:
$$\langle P \rangle = \frac{N_{\text{even}} - N_{\text{odd}}}{N}, \quad \text{SE}(\langle P \rangle) = \sqrt{\frac{1 - \langle P \rangle^2}{N}}$$
The state fidelity is evaluated using the exact trace-overlap projector relation:
$$|\Phi^+\rangle\langle\Phi^+| = \frac{II + XX - YY + ZZ}{4} \implies F = \frac{1 + \langle XX \rangle - \langle YY \rangle + \langle ZZ \rangle}{4}$$
$$\text{SE}(F) = \frac{1}{4}\sqrt{\text{SE}_{XX}^2 + \text{SE}_{YY}^2 + \text{SE}_{ZZ}^2}$$

### 3.3 Measured Results (`results/tables/bell.csv`)

| Pair | Distance | Condition | Two-Qubit Gates ($CX$) | $\langle XX \rangle \pm \text{SE}$ | $\langle YY \rangle \pm \text{SE}$ | $\langle ZZ \rangle \pm \text{SE}$ | State Fidelity $F \pm \text{SE}$ |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **(0, 1)** | 1 | ideal | 1 | $+1.0000 \pm 0.0000$ | $-1.0000 \pm 0.0000$ | $+1.0000 \pm 0.0000$ | **$1.0000 \pm 0.0000$** |
| **(0, 1)** | 1 | noisy | 1 | $+0.9458 \pm 0.0051$ | $-0.9521 \pm 0.0048$ | $+0.9551 \pm 0.0046$ | **$0.9633 \pm 0.0021$** |
| **(0, 5)** | 3 | ideal | 7 | $+1.0000 \pm 0.0000$ | $-1.0000 \pm 0.0000$ | $+1.0000 \pm 0.0000$ | **$1.0000 \pm 0.0000$** |
| **(0, 5)** | 3 | noisy | 7 | $+0.9302 \pm 0.0057$ | $-0.9199 \pm 0.0061$ | $+0.9385 \pm 0.0054$ | **$0.9471 \pm 0.0025$** |

### 3.4 Physical Discussion
* **Why Noisy Fidelity Drops on Distance 1 ($F = 0.9633$):**  
  Under the official noise model, two-qubit depolarizing noise ($p_2 = 0.005$) and dual readout errors ($p_{\text{readout}} = 0.01$) act directly on the Bell state, shrinking the expectation values from $\pm 1.0$ to $\approx \pm 0.95$.
* **Why the Distant Pair is Worse ($F = 0.9471$):**  
  Physical qubits 0 and 5 cannot interact directly. The SABRE transpiler routes the interaction through nodes 2 and 4 by inserting **2 physical SWAP gates (each requiring 3 CX gates)**, expanding the circuit from **1 CX to 7 CX gates**. Each additional two-qubit gate acts as an independent depolarizing error channel, multiplying decoherence and reducing fidelity by an additional $1.62\%$.

---

## 4. Objective 3 (Part 1): Mapping and Hamiltonian Reduction

### 4.1 Theoretical Reductions
1. **Jordan-Wigner Baseline (4Q):** Encodes occupation numbers directly. Retains all 4 spin-orbitals, yielding 14 non-identity Pauli operators grouped into 5 QWC measurement sets.
2. **Parity Mapping with Two-Qubit Reduction (2Q):** Utilizes total particle-number parity conservation in the $\alpha$ and $\beta$ spin sectors ($N_\alpha = 1, N_\beta = 1$). Projecting out qubits 1 and 3 reduces the system to a 2-qubit Hamiltonian:
   $$H_{\text{Parity-2q}} = -1.052373 II + 0.397937 IZ - 0.397937 ZI - 0.011280 ZZ + 0.180931 XX$$
   This slashes Pauli terms from 14 to 4 (71.4% reduction) and QWC groups from 5 to 2 (60% measurement saving).
3. **$Z_2$ Symmetry Tapering (1Q):** The JW Hamiltonian possesses 3 independent reflection symmetries: $\tau_1 = Z_0 Z_3$, $\tau_2 = Z_1 Z_3$, $\tau_3 = Z_0 Z_1 Z_2 Z_3$. Tapering in the Hartree-Fock sector ($0101$) compresses $H_2$ into a single active qubit ($c_0 I + c_1 Z + c_2 X$).

### 4.2 Mapping Comparison Table (`results/tables/c1_mapping.csv`)

| Operator Label | Method | Qubits | Pauli Terms | QWC Groups | Exact Energy (Ha) | Error vs $E_{\text{FCI}}$ (Ha) | CX on Processor D |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **`JW-4q`** | `Jordan-Wigner` | 4 | 14 | 5 | $-1.1373060358$ | $0.00 \times 10^0$ | 3 |
| **`Parity-2q`** | `parity-2q` | 2 | 4 | 2 | $-1.1373060358$ | $\mathbf{1.33 \times 10^{-15}}$ | 1 |
| **`Tapered-1q`** | `Z2-tapering` | 1 | 2 | 2 | $-1.1373060358$ | $\mathbf{1.33 \times 10^{-15}}$ | 0 |

Both reduction techniques reproduce Full CI ground-state energy with numerical machine precision ($10^{-15}\text{ Ha}$), outperforming the hackathon tolerance threshold ($10^{-6}\text{ Ha}$) by nine orders of magnitude.

---

## 5. Next Steps

With Processor D frozen and validated, the Bell experiment completed, and the Hamiltonian reductions derived, the study proceeds directly to:
1. **Depth $\times$ Optimizer Sweep:** 2 depths $\times$ 2 optimizers (COBYLA & SPSA) $\times$ 3 seeds (0, 1, 2) on Processor D (`c1_sweep.csv`).
2. **Shot Estimation Study:** Evaluating converged parameters at 1,024 and 8,192 shots/group, ideal and noisy (`c1_shots.csv`).
3. **Hardware Architecture Comparison:** Benchmarking across Processors A, B, and D (`resources.csv`).
4. **Error Mitigation (Bonus):** Zero-Noise Extrapolation (ZNE) and Readout Inversion to recover chemical accuracy under hardware noise.

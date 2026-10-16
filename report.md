# Technical Report: Algorithm-Architecture Co-Design & Quantum Error Mitigation for Molecular Ground-State Energy ($H_2$)

**Team Name:** STRAW HATS  
**Team Members:**  
- **P. SAHITHI SIVA** (Team Leader)  
- **MD. SANA TAMREEN** (Team Member 2)  
- **A. SAI SARANYA** (Team Member 3)  
**Institution:** Vijaya Institute of Technology for Women  
**Host Institution & Event:** SRM University-AP (Qiskit Fall Fest 2026)  
**Track:** Track 1: Quantum Chemistry (VQE / Molecular Systems)  
**Problem Statement Code:** **PS-C1: Molecular Ground-State Energy ($H_2$)**  
**Phase:** Phase 1 — Technical Qualification & Baseline Benchmarking  

---

## Executive Summary

This report delivers an end-to-end, mathematically rigorous, and fully reproducible quantum chemistry solution for **Problem Statement C1: Molecular Ground-State Energy ($H_2$)**. We solve the electronic ground state of molecular hydrogen ($H_2$) in the minimal STO-3G basis at the official competition equilibrium geometry ($R = 0.74$ Å / $1.3984$ Bohr, $V_{nn} = 0.715104$ Hartree), benchmark physical mapping across hardware architectures, demonstrate practical Quantum Error Mitigation (QEM), and propose a co-designed **Processor D** architecture tailored for fermionic quantum chemistry.

### Key Scientific Milestones:
1. **Classical Baseline & Hamiltonian Formulation:**
   Exact classical Full Configuration Interaction (FCI) diagonalization yields:
   $$E_{\text{FCI}} = -1.137285 \text{ Hartree}$$
   The electronic structure problem is formulated using the Jordan-Wigner transformation in the minimal STO-3G basis at the official equilibrium separation ($R = 0.74$ Å).
2. **Transparent Variational Ansätze Suite:**
   We benchmark two complementary variational ansatz classes:
   - **Symmetry-Adapted Active-Space UCCSD (Givens Double-Excitation):** Restricts the active space to the physical $N=2, S_z=0$ correlation subspace ($|0101\rangle \leftrightarrow |1010\rangle$), reaching exact FCI ground-state precision ($\Delta E < 10^{-11}$ Ha) with minimal gate depth ($5$) and $3$ CX gates.
   - **Multi-Layer Hardware-Efficient Ansatz (HEA):** Parameterized $R_y-R_z$ rotations with cyclic entangling layers ($L=1, 2$) evaluated with non-zero parameters to stress-test hardware routing.
3. **Dual-Mode VQE: Ideal Statevector & Noisy SPSA Optimization:**
   We benchmark both ideal statevector convergence (COBYLA baseline) and true quantum-in-the-loop noisy VQE using **Simultaneous Perturbation Stochastic Approximation (SPSA)** directly on the finite-shot AerSimulator, capturing realistic stochastic gradient updates under device noise.
4. **Empirical Architecture Co-Design & Routing Differentiation:**
   We benchmarked physical mapping across **Processor A** (5 physical qubits, branching star tree) and **Processor B** (9 physical qubits, planar mesh).
   - Under linear interaction paths, both processors embed without SWAPs.
   - **Under cyclic entanglement (Circular HEA Rep 2 with active rotation parameters), Processor A lacks a 4-cycle and must route through central Node 1 (Betweenness Centrality = 0.83), incurring 3 SWAP gates and Depth 37. In contrast, Processor B’s planar cycles execute cyclic interactions with 0 SWAPs and Depth 20 (a 17-layer depth reduction and 3-SWAP advantage).**
5. **Noise Mitigation via Quantum Error Mitigation (QEM):**
   Under the authoritative synthetic noise model ($p_1 = 0.1\%$, $p_2 = 0.5\%$, readout error $= 1.0\%$), raw physical energy degrades by $+42.19$ mHa on Processor A and $+43.54$ mHa on Processor B. We implemented a two-stage QEM pipeline:
   - **Analytical Readout Error Mitigation:** Inverting the single-qubit measurement assignment matrix reduces error on Processor A from $42.19$ mHa to $14.98$ mHa (a $27.21$ mHa recovery).
   - **Zero-Noise Extrapolation (ZNE):** Unitary CX gate folding across scale factors $\lambda \in \{1, 3, 5\}$ with Richardson polynomial extrapolation back to $\lambda = 0$ yields:
     - **Processor A:** $E_{\text{ZNE}} = -1.138827\text{ Ha} \implies \Delta E = 1.54\text{ mHa}$ (surpassing the $1.594\text{ mHa}$ chemical accuracy threshold).
     - **Processor B:** $E_{\text{ZNE}} = -1.133309\text{ Ha} \implies \Delta E = 3.98\text{ mHa}$.
6. **Hardware Problem Illustration & Processor D Ideology:**
   We rigorously document the graph bottlenecks of tree and planar processors for molecular simulation, and propose the architectural ideology of **Processor D**: a 12-qubit circulant $C_{12}(2, 3)$ graph with diameter 2, algebraic connectivity $\lambda_2 = 3.0$, and uniform degree 4, achieving 0 SWAPs and minimal depth for arbitrary 4-qubit fermionic interactions.

---

## Criterion 1: Technical Correctness — Molecular Ground-State Energy (PS-C1) [30 Points]

### 1.1 Second-Quantization Electronic Hamiltonian
Under the Born-Oppenheimer approximation, the electronic Hamiltonian for a molecular system is:
$$\hat{H}_e = \sum_{pq} h_{pq} \hat{a}_p^\dagger \hat{a}_q + \frac{1}{2} \sum_{pqrs} g_{pqrs} \hat{a}_p^\dagger \hat{a}_q^\dagger \hat{a}_s \hat{a}_r$$
where $h_{pq}$ and $g_{pqrs}$ are one- and two-electron molecular integrals computed in the STO-3G atomic orbital basis. Adding the nuclear repulsion energy $V_{nn} = \frac{Z_A Z_B}{R} = 0.715104$ Hartree at $R = 0.74$ Å yields the total Hamiltonian $\hat{H} = \hat{H}_e + V_{nn}\hat{I}$.

### 1.2 Qubit Mapping via Jordan-Wigner Transformation
The STO-3G basis for $H_2$ comprises two spatial orbitals ($1\sigma_g$ bonding, $1\sigma_u$ antibonding), defining 4 spin-orbitals: $\chi_0 (1\sigma_g, \uparrow)$, $\chi_1 (1\sigma_g, \downarrow)$, $\chi_2 (1\sigma_u, \uparrow)$, $\chi_3 (1\sigma_u, \downarrow)$.
Fermionic creation and annihilation operators map to Pauli spin operators via:
$$\hat{a}_j^\dagger = \left( \bigotimes_{k=0}^{j-1} \hat{Z}_k \right) \otimes \frac{\hat{X}_j - i\hat{Y}_j}{2}$$
This yields a 15-term Hamiltonian operator on 4 qubits:
$$\hat{H} = c_0 \hat{I} + \sum_{i=0}^3 c_i \hat{Z}_i + \sum_{i < j} c_{ij} \hat{Z}_i \hat{Z}_j + c_{\text{XXYY}} (\hat{X}_0 \hat{X}_1 \hat{Y}_2 \hat{Y}_3 + \dots)$$

### 1.3 Exact Classical Diagonalization Baseline
Diagonalizing the $16 \times 16$ Hamiltonian matrix yields:
$$E_{\text{FCI}} = -1.137285 \text{ Hartree}$$
The exact ground state is a singlet ($S = 0, S_z = 0$) configuration interaction superposition:
$$|\psi_0\rangle \approx -0.9936 |0101\rangle + 0.1125 |1010\rangle$$
where $|0101\rangle$ is the Hartree-Fock reference state ($E_{\text{HF}} = -1.116759$ Ha), recovering $20.525$ mHa of electronic correlation energy.

### 1.4 Variational Ansätze Suite & Physical Justification

| Ansatz Name | Formulation Class | Logical Qubits | Logical Depth | Logical CX | Variational Params | Physical Justification |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Symmetry-Adapted UCCSD Givens** | Particle-Conserving Symmetry | 4 | 5 | 3 | 1 | Restricts Hilbert space to $N=2, S_z=0$ subspace; exact 2-determinant mixing. |
| **Circular HEA (Rep 1)** | Hardware-Efficient | 4 | 8 | 4 | 16 | Alternating $R_y-R_z$ rotations + cyclic CX ring; tests 4-cycle embedding. |
| **Circular HEA (Rep 2)** | Deep Hardware-Efficient | 4 | 14 | 8 | 24 | Two-layer entangling mesh; severe routing stress test for star tree vs planar mesh. |

### 1.5 Dual-Mode VQE: Ideal Statevector & Noisy SPSA
- **Ideal Statevector VQE (COBYLA):** Converges in 38 iterations to $E = -1.137285$ Hartree ($\Delta E = 0.000$ mHa), verifying absolute mathematical and algorithmic correctness.
- **Quantum-in-the-Loop Noisy SPSA VQE:** Evaluates simultaneous stochastic gradients on AerSimulator under challenge noise ($1024$ shots). Converges to $-1.096377$ Hartree, demonstrating realistic NISQ optimization dynamics under stochastic shot fluctuations.

---

## Criterion 2: Processor A/B Benchmarking — Quantitative Execution & Noise Simulation [25 Points]

Both provided processor configurations were fully integrated and tested under identical execution environments:

### 2.1 Hardware Specifications
- **Processor A:** 5 physical qubits, 4 undirected coupling edges, branching star tree topology, basis gates `["rz", "sx", "x", "cx"]`.
- **Processor B:** 9 physical qubits, 12 undirected coupling edges, planar mesh with heavy-hex inspiration, basis gates `["rz", "sx", "x", "cx"]`.

### 2.2 Finite-Shot Sampling Statistics (4096 Shots)
Using the analytical sample variance across Pauli operators:
$$\sigma_E = \sqrt{\sum_k c_k^2 \frac{1 - \langle \hat{P}_k \rangle^2}{N_{\text{shots}}}}$$
- **Processor A (Ideal Shots):** $-1.138062 \pm 0.001951$ Hartree ($\Delta E = 0.78$ mHa $\le 1.594$ mHa).
- **Processor B (Ideal Shots):** $-1.135749 \pm 0.002007$ Hartree ($\Delta E = 1.54$ mHa $\le 1.594$ mHa).
- **Processor A (Raw Noisy):** $-1.095097 \pm 0.003133$ Hartree ($\Delta E = 42.19$ mHa).
- **Processor B (Raw Noisy):** $-1.093742 \pm 0.003068$ Hartree ($\Delta E = 43.54$ mHa).

### 2.3 Quantum Error Mitigation (QEM) Suite
Under physical noise ($p_1 = 0.1\%$, $p_2 = 0.5\%$, readout error $= 1.0\%$), raw energies deviate by $\sim 42-44$ mHa. We designed and implemented a two-stage QEM pipeline evaluated independently on both processors:

#### Stage 1: Analytical Readout Error Mitigation
For symmetric readout assignment matrix $M = \begin{pmatrix} 1-p & p \\ p & 1-p \end{pmatrix}$, each Pauli expectation value scales as $\langle P \rangle_{\text{mit}} = \frac{\langle P \rangle_{\text{raw}}}{(1 - 2p)^w}$, where $w$ is the Pauli weight. On Processor A, this reduces error from $42.19$ mHa to **$14.98$ mHa** (a $27.21$ mHa recovery).

#### Stage 2: Zero-Noise Extrapolation (ZNE) via Unitary CX Gate Folding
We scaled two-qubit noise by digitally folding CX gates: $CX \to CX \cdot (CX \cdot CX)^k$, producing scale factors $\lambda = 2k + 1 \in \{1, 3, 5\}$.
- **Processor A Extrapolated ($\lambda = 0$):** $E_{\text{ZNE}} = -1.138827$ Hartree $\implies \Delta E = 1.54$ mHa (surpassing the $1.594$ mHa chemical accuracy threshold).
- **Processor B Extrapolated ($\lambda = 0$):** $E_{\text{ZNE}} = -1.133309$ Hartree $\implies \Delta E = 3.98$ mHa (residual consistent with finite shot uncertainty envelope $\pm 3.5$ mHa).

### Summary of Error Mitigation Benchmark

| Stage | Measured Energy (Hartree) | Error vs FCI (mHa) | Chemical Accuracy Achieved? | Methodology |
| :--- | :---: | :---: | :---: | :--- |
| **Exact Classical FCI Benchmark** | $-1.137285$ | $0.00$ | **YES** | Exact NumPy diagonalization |
| **Ideal Finite-Shot VQE (4096 shots)** | $-1.138062$ | $0.78$ | **YES** | AerSimulator without noise |
| **Raw Hardware Noise (p2=0.5%, ro=1.0%)** | $-1.095097$ | $42.19$ | **NO** | Unmitigated physical depolarizing & readout |
| **Readout Error Mitigated** | $-1.122307$ | $14.98$ | **NO (Approaching)** | Analytical measurement matrix inversion |
| **Full QEM (Proc A): Readout Mitigation + ZNE (λ=0)** | **$-1.138827$** | **$1.54$** | **YES** | Readout inversion + CX gate folding Richardson fit |
| **Full QEM (Proc B): Readout Mitigation + ZNE (λ=0)** | **$-1.133309$** | **$3.98$** | **NO (Residual within shot noise)** | Readout inversion + CX gate folding Richardson fit |

---

## Criterion 3: Performance Analysis — Gate Count, Depth, SWAP Overhead & Connectivity [20 Points]

### 3.1 Hardware Architecture & Spectral Graph Theory

```
Processor A (5 Qubits, Star Tree)          Processor B (9 Qubits, Planar Mesh)
          q0                                         q0 --------- q1 --------- q2
          |                                          |           |           / \
     q2 - q1 - q3 - q4                               q8          |         q3   q5
                                                      \         |          \ /
                                                       q6 ------+----------- q4
                                                      / \
                                                    q7   q8
```

#### Quantitative Graph Comparison

| Graph Metric | Processor A (5Q Star Tree) | Processor B (9Q Planar Mesh) | Difference (B - A) | Architectural Interpretation |
| :--- | :---: | :---: | :---: | :--- |
| **Physical Qubits ($|V|$)** | 5 | 9 | +4 | Processor B provides 4 additional physical qubits, expanding candidate embedding subgraphs. |
| **Coupling Edges ($|E|$)** | 4 | 12 | +8 | Processor B provides 3x the connectivity edges of Processor A, enabling multi-route bypasses. |
| **Average Node Degree** | 1.600 | 2.667 | +1.067 | Higher node degree in B reduces routing congestion at central hub nodes. |
| **Maximum Node Degree** | 3 (Node 1) | 5 (Node 6) | +2 | Node 1 is a central coordination hub on Processor A; Node 6 on B provides high local branching. |
| **Graph Diameter** | 3 | 4 | +1 | Processor A has smaller diameter due to fewer nodes; B incorporates planar cycles to avoid bottlenecks. |
| **Algebraic Connectivity ($\lambda_2$)** | **0.5188** | **0.6431** | **+0.1243** | **Processor B has 24% higher algebraic connectivity, proving superior global routing bandwidth.** |
| **Bottleneck Node & Centrality** | **Node 1 (BC = 0.83)** | **Node 6 (BC = 0.48)** | **Distributed** | **Node 1 on Processor A has an extreme betweenness centrality of 0.83, creating severe serialized traffic.** |

### 3.2 Multi-Ansatz Compilation Benchmark (Optimization Level 1)

Benchmarked with active non-zero parameter vectors to preserve physical rotation gates:

| Ansatz | Logical CX | Proc A Depth | Proc A SWAPs | Proc B Depth | Proc B SWAPs | Depth Advantage (B vs A) | SWAP Advantage (B vs A) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **UCCSD Givens (Linear, 3 CX)** | 3 | 6 | 0 | 6 | 0 | 0 | 0 |
| **Circular HEA (Rep 1, 4 CX)** | 4 | 19 | 1 | 12 | 0 | **-7 layers** | **-1 SWAP** |
| **Circular HEA (Rep 2, 8 CX)** | 8 | 37 | 3 | 20 | 0 | **-17 layers** | **-3 SWAPs** |

> **Performance Finding:** When the entangling graph is a linear chain, both processors embed without SWAPs. However, when the ansatz introduces cyclic entanglement (Circular HEA), **Processor A incurs up to 3 SWAP gates and Depth 37 because tree graphs lack 4-cycles and must route non-adjacent interactions through central Node 1**. Processor B leverages its planar cycles to execute cyclic gates with zero SWAPs and Depth 20 (a 17-layer advantage).
>
> **Noise Overhead Mechanism:** Because each SWAP gate decomposes into 3 CX gates on standard basis architectures, 3 SWAPs inject 9 additional physical CX gates. Under the challenge two-qubit error rate ($p_2 = 0.5\%$), this injects $\approx 4.5\%$ of compound two-qubit infidelity solely from routing overhead!

---

## Criterion 4: Code Quality, Modularity & Reproducibility Suite [15 Points]

### 4.1 Modular Codebase Organization
The repository is strictly structured into reusable, single-responsibility Python modules:
- [`src/problem.py`](file:///c:/Users/DELL/.gemini/antigravity/scratch/qff-2026-c1-h2-vqe/src/problem.py): STO-3G molecular integrals, Jordan-Wigner Hamiltonian loader, classical FCI diagonalization, and variational ansätze suite.
- [`src/processors.py`](file:///c:/Users/DELL/.gemini/antigravity/scratch/qff-2026-c1-h2-vqe/src/processors.py): Graph representations, spectral Laplacian invariants ($\lambda_2$), betweenness centralities, and authoritative noise models.
- [`src/routing.py`](file:///c:/Users/DELL/.gemini/antigravity/scratch/qff-2026-c1-h2-vqe/src/routing.py): Transpilation pipelines, SWAP overhead extraction, multi-ansatz benchmarking, and topology ablation.
- [`src/metrics.py`](file:///c:/Users/DELL/.gemini/antigravity/scratch/qff-2026-c1-h2-vqe/src/metrics.py): Dual-mode VQE (Statevector & Noisy SPSA), analytical standard errors ($\sigma_E$), and chemical accuracy verification.
- [`src/mitigation.py`](file:///c:/Users/DELL/.gemini/antigravity/scratch/qff-2026-c1-h2-vqe/src/mitigation.py): Symmetric readout calibration inversion and digital CX gate folding Zero-Noise Extrapolation (ZNE).
- [`src/visualization.py`](file:///c:/Users/DELL/.gemini/antigravity/scratch/qff-2026-c1-h2-vqe/src/visualization.py): 300 DPI publication-grade figure generation routines.

### 4.2 End-to-End Automated Pipeline & Notebook
- **One-Command CLI Reproduction:** Running `python main.py` executes the entire benchmark suite in ~75 seconds, reproducing all CSV tables in `results/tables/` and figures in `results/figures/`.
- **Pre-Executed Interactive Notebook:** [`main.ipynb`](file:///c:/Users/DELL/.gemini/antigravity/scratch/qff-2026-c1-h2-vqe/main.ipynb) contains all 23 fully documented sections with embedded SVG/PNG plots and native HTML dataframes.
- **Pinned Environment:** Clean [`requirements.txt`](file:///c:/Users/DELL/.gemini/antigravity/scratch/qff-2026-c1-h2-vqe/requirements.txt) guaranteeing cross-platform deterministic reproducibility under Python 3.11+.

---

## Criterion 5: Technical Explanation, Architecture Limitations & Processor D Ideology [10 Points]
*(Verified by Human Evaluators under the 30% Evaluation Component)*

### 5.1 Problems Faced Running PS-C1 on Processors A and B

Our empirical benchmarks exposed fundamental architectural limitations in both provided hardware configurations when solving electronic structure problems:

#### 1. The Tree Bottleneck on Processor A (Star Tree Topology):
- **Lack of Native Cycles (Girth $\infty$):** Processor A is a 5-node acyclic tree. In electronic structure calculations, electron correlation arises from multi-orbital excitations (such as the double excitation $\hat{a}_2^\dagger \hat{a}_3^\dagger \hat{a}_1 \hat{a}_0$). Under Jordan-Wigner transformation, these interactions yield closed 4-qubit Pauli interaction loops ($XXXX, XXYY, YYXX, YYYY$). Because Processor A has no 4-cycles, mapping any closed-loop interaction requires routing across non-adjacent channels.
- **Severe Centrality Choke Point (Node 1 Betweenness Centrality = 0.83):** Node 1 must mediate all traffic between leaf qubits (qubits 0, 2, 3, and 4). As shown in our multi-ansatz benchmark, compiling Circular HEA (Rep 2) forces **3 SWAP gates** and inflates circuit depth to **37 layers**.
- **Noise Compounding:** Under challenge noise ($p_2 = 0.5\%$), the 9 extra CX gates from SWAP insertions add $\approx 4.5\%$ compound gate infidelity, leading to severe error degradation before error mitigation.

#### 2. Planar Mesh Limitations on Processor B:
- **Higher Graph Diameter ($D = 4$) & Asymmetric Degree Distribution:** Processor B has 9 qubits arranged in a planar mesh. While it contains cycles and eliminates SWAPs for Circular HEA on 4 qubits, it exhibits a higher graph diameter ($D = 4$) and a sharp degree imbalance: Node 6 has degree 5, while outer nodes have degree 1 or 2.
- **Physical Scalability Constraints:** In superconducting transmon architectures, nodes with degree 5 suffer from severe frequency allocation crowding, parasitic capacitive coupling, and residual ZZ-crosstalk.
- **Suboptimal Algebraic Connectivity for Multi-Qubit Scalability:** Processor B achieves $\lambda_2 = 0.6431$. While superior to Processor A ($0.5188$), its global bisection bandwidth is constrained by planar bottleneck cuts.

---

### 5.2 Proposed Solution: Architectural Ideology of Processor D

To resolve the structural limitations of Processors A and B, we designed **Processor D**: a quantum co-processor architecture specifically co-designed for fermionic quantum chemistry algorithms.

```
                           Processor D: Circulant C12(2, 3) Architecture
                                            (12 Qubits, 24 Edges, Diameter 2)

                                                     [q0]
                                             .-'    / | \    '-.
                                        .-'        /  |  \        '-.
                                   [q11]          /   |   \          [q1]
                                  /  | \         /    |    \         / | \
                                 /   |  \       /     |     \       /  |  \
                             [q10]   |   '-- [q9]     |     [q3] --'   |   [q2]
                               \     |      /         |         \      |     /
                                \    |     /          |          \     |    /
                                 \   |    /           |           \    |   /
                                  \  |   /            |            \   |  /
                                   [q8] '----------- [q6] ----------' [q4]
                                        '-.         / | \         .-'
                                            '-.    /  |  \    .-'
                                                     [q7]
```

#### 1. Mathematical Design Principles:
1. **Circulant Chordal Topology $C_{12}(2, 3)$:**
   Processor D is formulated as a 12-qubit regular circulant graph where each node $i \in \{0, \dots, 11\}$ is connected to $(i \pm 2) \pmod{12}$ and $(i \pm 3) \pmod{12}$.
2. **Strictly Regular Node Degree ($d = 4$):**
   Every single node has degree exactly 4. This avoids both under-connected leaves (as in Processor A) and crowded hub nodes (such as Node 6 with degree 5 in Processor B), drastically minimizing transmon microwave frequency crowding and parasitic ZZ-crosstalk.
3. **Ultra-Low Graph Diameter ($D = 2$):**
   Any arbitrary physical qubit can reach any other physical qubit in at most **1 intermediate hop**. This represents a $50\%$ diameter reduction compared to Processor B ($D = 4$) and Processor A ($D = 3$).
4. **Massive Global Bandwidth ($\lambda_2 = 3.000$):**
   The algebraic connectivity of Processor D is $\lambda_2 = 3.000$ — a **$4.67\times$ bandwidth increase over Processor B ($0.6431$)** and **$5.78\times$ increase over Processor A ($0.5188$)**.
5. **Completely Distributed Centrality ($BC = 0.0636$):**
   Betweenness centrality is identical ($0.0636$) across all 12 nodes, completely eliminating single-point traffic bottlenecks.
6. **Native 4-Cycle & Subgraph Embedding:**
   Contains 12 native 4-cycles, allowing 4-orbital fermionic Hamiltonians and cyclic entangling layers to embed with **zero SWAP gates**.

#### 2. Quantitative Hardware Specification Comparison

| Architectural Property | Processor A (Star Tree) | Processor B (Planar Mesh) | **Processor D (Co-Designed Chemistry Engine)** | Co-Design Advantage of D |
| :--- | :---: | :---: | :---: | :--- |
| **Physical Qubit Count ($|V|$)** | 5 | 9 | **12** | Accommodates full 4-qubit active space plus spectator/ancilla channels for error mitigation. |
| **Coupling Edges ($|E|$)** | 4 | 12 | **24** | $2\times$ connectivity of B; $6\times$ connectivity of A. |
| **Node Degree Distribution** | Min 1, Max 3, Avg 1.6 | Min 2, Max 5, Avg 2.67 | **Uniform 4.0 on all nodes** | Eliminates leaf congestion and avoids high-degree crosstalk. |
| **Graph Diameter ($D$)** | 3 | 4 | **2** | **50% shorter maximum communication path than B.** |
| **Average Path Length** | 1.800 | 2.111 | **1.636** | Lowest latency routing across all pairs. |
| **Algebraic Connectivity ($\lambda_2$)** | 0.5188 | 0.6431 | **3.0000** | **+366% routing bandwidth over B; +478% over A.** |
| **Bottleneck Centrality ($BC_{\max}$)** | **0.8333 (Node 1)** | 0.4762 (Node 6) | **0.0636 (Uniform)** | **$13.1\times$ reduction in traffic concentration.** |
| **UCCSD Givens Compiled Depth** | 6 | 6 | **6** | Optimal minimal depth. |
| **UCCSD Givens SWAP Gates** | 0 | 0 | **0** | Zero SWAP overhead. |
| **Circular HEA Rep 1 SWAP Gates** | 1 | 0 | **0** | Zero SWAP overhead. |
| **Circular HEA Rep 2 SWAP Gates** | **3 SWAPs** | 0 SWAPs | **0 SWAPs** | **3-SWAP advantage over Processor A.** |
| **Circular HEA Rep 2 Compiled Depth** | **37 layers** | 20 layers | **20 layers** | **17-layer depth reduction over Processor A.** |

#### 3. Exact Specification File
The full machine-readable JSON specification for Processor D is provided in [`processors/processor_D.json`](file:///c:/Users/DELL/.gemini/antigravity/scratch/qff-2026-c1-h2-vqe/processors/processor_D.json), including bidirectional coupling maps, native basis gates, and precomputed spectral graph invariants.

---

### 5.3 Compliance with Phase 1 Master Guide & Technical Program Cell Clarification

In strict accordance with the official announcement from the Hackathon and Technical Program Cell Heads:
1. **Phase 1 Automated Evaluation (70%):** Evaluates working code, transpilation, dual-mode VQE, noise simulation, and Quantum Error Mitigation across **Processor A and Processor B**.
2. **Phase 1 Human Evaluation (30%):** Validates the team's scientific depth, architectural reasoning, and **Processor D ideology** through this authoritative [`report.md`](file:///c:/Users/DELL/.gemini/antigravity/scratch/qff-2026-c1-h2-vqe/report.md).
3. **Phase 2 Readiness:** The complete architectural specification for Processor D is locked in [`processors/processor_D.json`](file:///c:/Users/DELL/.gemini/antigravity/scratch/qff-2026-c1-h2-vqe/processors/processor_D.json), positioning Team STRAW HATS for seamless offline execution upon qualification.

---

## 6. Summary of Results & Conclusion

1. **Chemical Accuracy Reached:** Under ideal conditions, our active-space Givens UCCSD ansatz achieves exact FCI ground state precision ($0.00$ mHa error).
2. **Hardware Noise Overcome:** Applying analytical readout error mitigation and Zero-Noise Extrapolation recovers chemical accuracy under physical device noise on Processor A ($1.54$ mHa $\le 1.594$ mHa threshold).
3. **Architecture Co-Design Proven:** We proved that tree graphs suffer severe SWAP penalties and gate depth expansion for cyclic molecular ansätze, while co-designed regular circulant topologies (Processor D) eliminate SWAP overhead, equalize betweenness centrality, and dramatically increase algebraic connectivity.
4. **Reproducibility:** All results, tables, and figures regenerate via `python main.py` in ~75 seconds and are documented in [`main.ipynb`](file:///c:/Users/DELL/.gemini/antigravity/scratch/qff-2026-c1-h2-vqe/main.ipynb).

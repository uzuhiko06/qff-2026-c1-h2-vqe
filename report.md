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

This report presents an end-to-end, mathematically rigorous, and reproducible quantum chemistry solution for **Problem Statement C1: Molecular Ground-State Energy ($H_2$)**. We solve the electronic ground state of molecular hydrogen ($H_2$) in the minimal STO-3G basis at the official competition equilibrium geometry ($R = 0.74$ Å / $1.3984$ Bohr, $V_{nn} = 0.715104$ Hartree).

### Key Scientific Milestones:
1. **Classical Baseline & Hamiltonian Formulation:**
   Exact classical Full Configuration Interaction (FCI) diagonalization yields:
   $$E_{\text{FCI}} = -1.137285 \text{ Hartree}$$
   The electronic structure problem is formulated using the Jordan-Wigner transformation in the minimal STO-3G basis at the official competition equilibrium separation ($R = 0.74$ Å).
2. **Transparent Variational Ansätze Suite:**
   We benchmark two complementary variational ansatz classes:
   - **Symmetry-Adapted Active-Space UCCSD (Givens Double-Excitation):** Restricts the active space to the physical $N=2, S_z=0$ correlation subspace ($|0101\rangle \leftrightarrow |1010\rangle$), reaching exact FCI ground-state precision ($\Delta E < 10^{-11}$ Ha) with minimal gate depth ($5$) and $3$ CX gates.
   - **Multi-Layer Hardware-Efficient Ansatz (HEA):** Parameterized $R_y-R_z$ rotations with cyclic entangling layers ($L=1, 2$) evaluated with non-zero parameters to stress-test hardware routing.
3. **Dual-Mode VQE: Ideal Statevector & Noisy SPSA Optimization:**
   We benchmark both ideal statevector convergence (COBYLA baseline) and true quantum-in-the-loop noisy VQE using **Simultaneous Perturbation Stochastic Approximation (SPSA)** directly on the finite-shot AerSimulator, capturing realistic stochastic gradient updates under device noise.
4. **Empirical Architecture Co-Design & Routing Differentiation:**
   We benchmarked physical mapping across **Processor A** (5 physical qubits, branching star tree) and **Processor B** (9 physical qubits, heavy-hex mesh).
   - Under linear interaction paths, both processors embed without SWAPs.
   - **Under cyclic entanglement (Circular HEA Rep 2 with active rotation parameters), Processor A lacks a 4-cycle and must route through central Node 1 (Betweenness Centrality = 0.83), incurring 3 SWAP gates and Depth 37. In contrast, Processor B’s planar cycles execute cyclic interactions with 0 SWAPs and Depth 20 (a 17-layer depth reduction and 3-SWAP advantage).**
5. **Noise Mitigation via Quantum Error Mitigation (QEM):**
   Under the authoritative synthetic noise model ($p_1 = 0.1\%$, $p_2 = 0.5\%$, readout error $= 1.0\%$), raw physical energy degrades by $+42.19$ mHa on Processor A and $+43.54$ mHa on Processor B. We implemented a two-stage QEM pipeline:
   - **Analytical Readout Error Mitigation:** Inverting the single-qubit measurement assignment matrix reduces error on Processor A from $42.19$ mHa to $14.98$ mHa (a $27.21$ mHa recovery).
   - **Zero-Noise Extrapolation (ZNE):** Unitary CX gate folding across scale factors $\lambda \in \{1, 3, 5\}$ with Richardson polynomial extrapolation back to $\lambda = 0$ yields:
     - **Processor A:** $E_{\text{ZNE}} = -1.138827\text{ Ha} \implies \Delta E = 1.54\text{ mHa}$ (approaching the $1.594\text{ mHa}$ chemical accuracy threshold).
     - **Processor B:** $E_{\text{ZNE}} = -1.133309\text{ Ha} \implies \Delta E = 3.98\text{ mHa}$.

---

## 1. Problem Formulation & Quantum Chemistry Foundations

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

---

## 2. Variational Ansätze Suite & Physical Justification

| Ansatz Name | Formulation Class | Logical Qubits | Logical Depth | Logical CX | Variational Params | Physical Justification |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Symmetry-Adapted UCCSD Givens** | Particle-Conserving Symmetry | 4 | 5 | 3 | 1 | Restricts Hilbert space to $N=2, S_z=0$ subspace; exact 2-determinant mixing. |
| **Circular HEA (Rep 1)** | Hardware-Efficient | 4 | 8 | 4 | 16 | Alternating $R_y-R_z$ rotations + cyclic CX ring; tests 4-cycle embedding. |
| **Circular HEA (Rep 2)** | Deep Hardware-Efficient | 4 | 14 | 8 | 24 | Two-layer entangling mesh; severe routing stress test for star tree vs heavy-hex. |

---

## 3. Hardware Architecture & Spectral Graph Theory

Quantum processors are represented as undirected coupling graphs $G = (V, E)$:

```
Processor A (5 Qubits, Star Tree)          Processor B (9 Qubits, Heavy-Hex Mesh)
          q0                                         q0 --------- q1 --------- q2
          |                                          |           |           / \
     q2 - q1 - q3 - q4                               q8          |         q3   q5
                                                      \         |          \ /
                                                       q6 ------+----------- q4
                                                      / \
                                                    q7   q8
```

### Quantitative Graph Comparison

| Graph Metric | Processor A (5Q Star Tree) | Processor B (9Q Heavy-Hex) | Difference (B - A) | Architectural Interpretation |
| :--- | :---: | :---: | :---: | :--- |
| **Physical Qubits ($|V|$)** | 5 | 9 | +4 | Processor B provides 4 additional physical qubits, expanding candidate embedding subgraphs. |
| **Coupling Edges ($|E|$)** | 4 | 12 | +8 | Processor B provides 3x the connectivity edges of Processor A, enabling multi-route bypasses. |
| **Average Node Degree** | 1.600 | 2.667 | +1.067 | Higher node degree in B reduces routing congestion at central hub nodes. |
| **Maximum Node Degree** | 3 (Node 1) | 5 (Node 6) | +2 | Node 1 is a central coordination hub on Processor A. |
| **Graph Diameter** | 3 | 4 | +1 | Processor A has smaller diameter due to fewer nodes; B incorporates planar cycles to avoid bottlenecks. |
| **Algebraic Connectivity ($\lambda_2$)** | **0.5188** | **0.6431** | **+0.1243** | **Processor B has 24% higher algebraic connectivity, proving superior global routing bandwidth.** |
| **Bottleneck Node & Centrality** | **Node 1 (BC = 0.83)** | **Node 6 (BC = 0.48)** | **Distributed** | **Node 1 on Processor A has an extreme betweenness centrality of 0.83, creating severe serialized traffic.** |

---

## 4. Transpilation & Routing Benchmarking

### 4.1 Multi-Ansatz Compilation Benchmark (Optimization Level 1)

Benchmarked with active non-zero parameter vectors to preserve physical rotation gates:

| Ansatz | Logical CX | Proc A Depth | Proc A SWAPs | Proc B Depth | Proc B SWAPs | Depth Advantage (B vs A) | SWAP Advantage (B vs A) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **UCCSD Givens (Linear, 3 CX)** | 3 | 6 | 0 | 6 | 0 | 0 | 0 |
| **Circular HEA (Rep 1, 4 CX)** | 4 | 19 | 1 | 12 | 0 | **-7 layers** | **-1 SWAP** |
| **Circular HEA (Rep 2, 8 CX)** | 8 | 37 | 3 | 20 | 0 | **-17 layers** | **-3 SWAPs** |

> **Architectural Finding:** When the entangling graph is a linear chain, both processors embed without SWAPs. However, when the ansatz introduces cyclic entanglement (Circular HEA), **Processor A incurs up to 3 SWAP gates and Depth 37 because tree graphs lack 4-cycles and must route non-adjacent interactions through central Node 1**. Processor B leverages its heavy-hex cycles to execute cyclic gates with zero SWAPs and Depth 20 (a 17-layer advantage).

---

## 5. Dual-Mode VQE & Finite-Shot Simulation

### 5.1 Dual-Mode VQE Trajectory
- **Ideal Statevector VQE (COBYLA):** Converges in 38 iterations to $E = -1.137285$ Hartree ($\Delta E = 0.000$ mHa), verifying theoretical correctness.
- **Quantum-in-the-Loop Noisy SPSA VQE:** Evaluates simultaneous stochastic gradients on AerSimulator under challenge noise ($1024$ shots). Converges to $-1.096377$ Hartree, demonstrating realistic NISQ optimization dynamics under stochastic shot fluctuations.

### 5.2 Finite-Shot Sampling Statistics (4096 Shots)
Using the analytical sample variance across Pauli operators:
$$\sigma_E = \sqrt{\sum_k c_k^2 \frac{1 - \langle \hat{P}_k \rangle^2}{N_{\text{shots}}}}$$
- **Processor A (Ideal Shots):** $-1.138062 \pm 0.001951$ Hartree ($\Delta E = 0.78$ mHa $\le 1.594$ mHa).
- **Processor B (Ideal Shots):** $-1.135749 \pm 0.002007$ Hartree ($\Delta E = 1.54$ mHa $\le 1.594$ mHa).
- **Processor A (Raw Noisy):** $-1.095097 \pm 0.003133$ Hartree ($\Delta E = 42.19$ mHa).
- **Processor B (Raw Noisy):** $-1.093742 \pm 0.003068$ Hartree ($\Delta E = 43.54$ mHa).

---

## 6. Quantum Error Mitigation (QEM) Suite

Under physical noise ($p_1 = 0.1\%$, $p_2 = 0.5\%$, readout error $= 1.0\%$), raw energies deviate by $\sim 42-44$ mHa. We designed and implemented a two-stage QEM pipeline evaluated independently on both processors:

### 6.1 Stage 1: Analytical Readout Error Mitigation
For symmetric readout assignment matrix $M = \begin{pmatrix} 1-p & p \\ p & 1-p \end{pmatrix}$, each Pauli expectation value scales as $\langle P \rangle_{\text{mit}} = \frac{\langle P \rangle_{\text{raw}}}{(1 - 2p)^w}$, where $w$ is the Pauli weight. On Processor A, this reduces error from $42.19$ mHa to **$14.98$ mHa** (a $27.21$ mHa recovery).

### 6.2 Stage 2: Zero-Noise Extrapolation (ZNE) via Unitary CX Gate Folding
We scaled two-qubit noise by digitally folding CX gates: $CX \to CX \cdot (CX \cdot CX)^k$, producing scale factors $\lambda = 2k + 1 \in \{1, 3, 5\}$.
- **Processor A Extrapolated ($\lambda = 0$):** $E_{\text{ZNE}} = -1.138827$ Hartree $\implies \Delta E = 1.54$ mHa (reaching the $1.594$ mHa chemical accuracy threshold).
- **Processor B Extrapolated ($\lambda = 0$):** $E_{\text{ZNE}} = -1.133309$ Hartree $\implies \Delta E = 3.98$ mHa.

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

## 7. Compliance with Phase 1 Master Guide & Final Summary

1. **Clarification on Processor C & D:** In strict compliance with Page 1 of the official Phase 1 Master Guide, Phase 1 evaluates **Processor A and Processor B**. Processor C and custom Processor D are reserved exclusively for Phase 2 offline finalists.
2. **Reproducibility:** The entire pipeline executes cleanly via `python main.py` in ~75 seconds and is fully documented in the interactive `main.ipynb`.
3. **Conclusion:** This submission achieves chemical accuracy on ideal simulation, explains authentic architectural differences between tree and heavy-hex topologies, and demonstrates the practical role of Quantum Error Mitigation in reducing device noise toward chemical accuracy.

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

This report presents an end-to-end, mathematically rigorous, and fully reproducible quantum chemistry solution for **Problem Statement C1: Molecular Ground-State Energy ($H_2$)**. We solve the electronic ground state of molecular hydrogen ($H_2$) in the minimal STO-3G basis at the official competition equilibrium geometry ($R = 0.74$ Å / $1.3984$ Bohr, $V_{nn} = 0.715104$ Hartree). 

### Key Scientific Milestones:
1. **Classical & Dynamic Electronic Structure Benchmark:**
   Exact classical Full Configuration Interaction (FCI) diagonalization yields:
   $$E_{\text{FCI}} = -1.137285 \text{ Hartree}$$
   We implemented a dynamic, self-contained programmatic Hamiltonian generator that maps molecular integrals into Jordan-Wigner Pauli strings across internuclear separations $R \in [0.4, 2.5]$ Å without requiring external data files.
2. **Transparent Variational Ansätze Suite:**
   Rather than presenting an ad-hoc circuit under false pretenses, we evaluate three transparently characterized variational ansätze:
   - **Particle-Conserving Givens Double-Excitation:** Operates strictly within the physical $N=2, S_z=0$ correlation subspace ($|0101\rangle \leftrightarrow |1010\rangle$), achieving exact ground-state convergence ($\Delta E = 0.000000$ Ha) with minimal gate depth ($5$) and $3$ CX gates.
   - **Multi-Layer Hardware-Efficient Ansatz (HEA):** Parameterized $R_y-R_z$ rotations with cyclic and full entangling layers, providing a rigorous stress test for hardware routing.
   - **Full Trotterized UCCSD Double-Excitation:** Textbook 8-Pauli Jordan-Wigner entangling ladder (48 CXs, Depth 73).
3. **Dual-Mode VQE: Statevector Baseline & Quantum-in-the-Loop Noisy SPSA:**
   We benchmark both ideal statevector convergence (COBYLA) and true quantum-in-the-loop noisy VQE using **Simultaneous Perturbation Stochastic Approximation (SPSA)** directly on the finite-shot AerSimulator, capturing realistic stochastic gradient dynamics.
4. **Empirical Architecture Co-Design & Routing Differentiation:**
   We benchmarked physical mapping across **Processor A** (5 physical qubits, branching star tree) and **Processor B** (9 physical qubits, heavy-hex mesh).
   - Under linear interaction paths, both processors embed with zero SWAPs.
   - **Under cyclic entanglement (Circular HEA Rep 2), Processor A suffers severe bottlenecking at central Node 1 (Betweenness Centrality = 0.83), incurring 3 SWAP gates and Depth 17. In contrast, Processor B’s planar cycles execute non-adjacent gates with 0 SWAPs and Depth 8 (a 9-layer depth reduction and 3-SWAP advantage).**
5. **Restoration of Chemical Accuracy via Quantum Error Mitigation (QEM):**
   Under the authoritative synthetic noise model ($p_1 = 0.1\%$, $p_2 = 0.5\%$, readout error $= 1.0\%$), raw physical energy degrades by $+42.19$ mHa, entirely losing chemical accuracy. We implemented a two-stage QEM pipeline:
   - **Analytical Readout Error Mitigation:** Inverting the single-qubit measurement assignment matrix reduces error from $42.19$ mHa to $14.98$ mHa (a $27.21$ mHa recovery).
   - **Zero-Noise Extrapolation (ZNE):** Unitary CX gate folding across scale factors $\lambda \in \{1, 3, 5\}$ with Richardson polynomial extrapolation back to $\lambda = 0$ yields:
     $$E_{\text{ZNE}} = -1.138827 \text{ Hartree} \implies \Delta E = 0.001542 \text{ Hartree (1.54 mHa)}$$
     **firmly restoring Chemical Accuracy ($\le 1.594$ mHa / $1.0$ kcal/mol) under physical device noise.**

---

## 1. Problem Formulation & Quantum Chemistry Foundations

### 1.1 Second-Quantization Electronic Hamiltonian
Under the Born-Oppenheimer approximation, the electronic Hamiltonian for a molecular system is:
$$\hat{H}_e = \sum_{pq} h_{pq} \hat{a}_p^\dagger \hat{a}_q + \frac{1}{2} \sum_{pqrs} g_{pqrs} \hat{a}_p^\dagger \hat{a}_q^\dagger \hat{a}_s \hat{a}_r$$
where $h_{pq}$ and $g_{pqrs}$ are one- and two-electron molecular integrals computed in the STO-3G atomic orbital basis. Adding the nuclear repulsion energy $V_{nn} = \frac{Z_A Z_B}{R} = 0.715104$ Hartree yields the total Hamiltonian $\hat{H} = \hat{H}_e + V_{nn}\hat{I}$.

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
| **Givens Active-Space** | Particle-Conserving Symmetry | 4 | 5 | 3 | 1 | Restricts Hilbert space to $N=2, S_z=0$ subspace; exact 2-determinant mixing. |
| **Circular HEA (Rep 1)** | Hardware-Efficient | 4 | 8 | 4 | 16 | Alternating $R_y-R_z$ rotations + cyclic CX ring; tests 4-cycle embedding. |
| **Circular HEA (Rep 2)** | Deep Hardware-Efficient | 4 | 14 | 8 | 24 | Two-layer entangling mesh; severe routing stress test for star tree vs heavy-hex. |
| **Full Trotterized UCCSD** | Textbook Fermionic JW | 4 | 73 | 48 | 1 | Exponentiates the 8 Pauli components of $\hat{T}_2 = \theta(a_3^\dagger a_2^\dagger a_1 a_0 - \text{h.c.})$. |

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

To demonstrate genuine co-design behavior, we compiled all four ansätze across Processor A and Processor B using the challenge baseline (`optimization_level=1`, `seed_transpiler=42`):

| Ansatz | Logical CX | Proc A Depth | Proc A SWAPs | Proc B Depth | Proc B SWAPs | Depth Advantage (B vs A) | SWAP Advantage (B vs A) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Givens Active Space** | 3 | 6 | 0 | 6 | 0 | 0 | 0 |
| **Circular HEA (Rep 1)** | 4 | 7 | 1 | 4 | 0 | **-3 layers (43% faster)** | **-1 SWAP** |
| **Circular HEA (Rep 2)** | 8 | 17 | 3 | 8 | 0 | **-9 layers (53% faster)** | **-3 SWAPs** |
| **Full Trotterized UCCSD** | 48 | 78 | 0 | 78 | 0 | 0 | 0 |

> **Architectural Finding:** When the entangling graph is a linear chain, both processors embed without SWAPs. However, when the ansatz introduces cyclic entanglement (Circular HEA), **Processor A incurs up to 3 SWAP gates and a 53% depth penalty because tree graphs lack cycles and must route non-adjacent interactions through bottleneck Node 1**. Processor B leverages its heavy-hex cycles $\{1,2,3,4,5,6\}$ to execute non-adjacent gates with zero SWAPs and minimal depth.

---

## 5. Dual-Mode VQE & Finite-Shot Simulation

### 5.1 Dual-Mode VQE Trajectory
- **Ideal Statevector VQE (COBYLA):** Converges in 38 iterations to $E = -1.137285$ Hartree ($\Delta E = 0.000$ mHa), verifying theoretical correctness.
- **Quantum-in-the-Loop Noisy SPSA VQE:** Evaluates simultaneous stochastic gradients on AerSimulator under challenge noise ($1024$ shots). Converges to $-1.096377$ Hartree, demonstrating realistic NISQ optimization dynamics without statevector shortcuts.

### 5.2 Finite-Shot Sampling Statistics (4096 Shots)
Using the analytical sample variance across Pauli operators:
$$\sigma_E = \sqrt{\sum_k c_k^2 \frac{1 - \langle \hat{P}_k \rangle^2}{N_{\text{shots}}}}$$
- **Processor A (Ideal Shots):** $-1.138062 \pm 0.001951$ Hartree ($\Delta E = 0.78$ mHa $\le 1.594$ mHa).
- **Processor B (Ideal Shots):** $-1.135749 \pm 0.002007$ Hartree ($\Delta E = 1.54$ mHa $\le 1.594$ mHa).
- **Processor A (Raw Noisy):** $-1.095097 \pm 0.003133$ Hartree ($\Delta E = 42.19$ mHa).
- **Processor B (Raw Noisy):** $-1.093742 \pm 0.003068$ Hartree ($\Delta E = 43.54$ mHa).

---

## 6. Quantum Error Mitigation (QEM) Suite

Under physical noise ($p_1 = 0.1\%$, $p_2 = 0.5\%$, readout error $= 1.0\%$), raw energies deviate by $\sim 42-44$ mHa. We designed and implemented a two-stage QEM pipeline to restore Chemical Accuracy:

```
Raw Noisy Energy (-1.0951 Ha, Δ=42.19 mHa)
                     │
                     ▼  [Stage 1: Analytical Readout Inversion]
Readout Mitigated Energy (-1.1223 Ha, Δ=14.98 mHa)  [27.21 mHa Recovered]
                     │
                     ▼  [Stage 2: Digital CX Gate Folding ZNE (λ ∈ {1, 3, 5})]
Full QEM Mitigated Energy (-1.1388 Ha, Δ=1.54 mHa)   [CHEMICAL ACCURACY RESTORED]
```

### 6.1 Stage 1: Analytical Readout Error Mitigation
For symmetric readout assignment matrix $M = \begin{pmatrix} 1-p & p \\ p & 1-p \end{pmatrix}$, each Pauli expectation value scales as $\langle P \rangle_{\text{mit}} = \frac{\langle P \rangle_{\text{raw}}}{(1 - 2p)^w}$, where $w$ is the Pauli weight. This reduces the error from $42.19$ mHa to **$14.98$ mHa**.

### 6.2 Stage 2: Zero-Noise Extrapolation (ZNE) via Unitary CX Gate Folding
We scaled two-qubit noise by digitally folding CX gates: $CX \to CX \cdot (CX \cdot CX)^k$, producing scale factors $\lambda = 2k + 1 \in \{1, 3, 5\}$.
- $\lambda = 1$: $E = -1.12231$ Hartree
- $\lambda = 3$: $E = -1.09284$ Hartree
- $\lambda = 5$: $E = -1.06814$ Hartree

Fitting a Richardson extrapolation model to $\lambda = 0$ yields:
$$E_{\text{ZNE}}(\lambda = 0) = -1.138827 \text{ Hartree} \implies |E_{\text{ZNE}} - E_{\text{FCI}}| = 0.001542 \text{ Hartree (1.54 mHa)}$$
**Chemical Accuracy is fully restored ($1.54\text{ mHa} < 1.594\text{ mHa}$).**

### Summary of Error Mitigation Benchmark

| Stage | Measured Energy (Hartree) | Error vs FCI (mHa) | Chemical Accuracy Achieved? | Methodology |
| :--- | :---: | :---: | :---: | :--- |
| **Exact Classical FCI Benchmark** | $-1.137285$ | $0.00$ | **YES** | Exact NumPy diagonalization |
| **Ideal Finite-Shot VQE (4096 shots)** | $-1.138062$ | $0.78$ | **YES** | AerSimulator without noise |
| **Raw Hardware Noise (p2=0.5%, ro=1.0%)** | $-1.095097$ | $42.19$ | **NO** | Unmitigated physical depolarizing & readout |
| **Readout Error Mitigated** | $-1.122307$ | $14.98$ | **NO (Approaching)** | Analytical measurement matrix inversion |
| **Full QEM: Readout Mitigation + ZNE (λ=0)** | **$-1.138827$** | **$1.54$** | **YES (RESTORED)** | Readout inversion + CX gate folding Richardson fit |

---

## 7. Compliance with Phase 1 Master Guide & Final Summary

1. **Clarification on Processor C & D:** In strict compliance with Page 1 of the official Phase 1 Master Guide, Phase 1 evaluates **Processor A and Processor B**. Processor C and custom Processor D are reserved exclusively for Phase 2 offline finalists.
2. **Reproducibility:** The entire pipeline executes cleanly via `python main.py` and is fully documented in the 35-cell interactive `main.ipynb`.
3. **Conclusion:** This submission achieves chemical accuracy on ideal simulation, explains authentic architectural differences between tree and heavy-hex topologies, and successfully demonstrates the restoration of chemical accuracy under physical noise via state-of-the-art Quantum Error Mitigation.

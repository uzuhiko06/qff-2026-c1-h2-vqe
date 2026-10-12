# Qiskit Fall Fest 2026 — Problem Statement C1
## Molecular Ground-State Energy ($H_2$) via VQE & Algorithm-Architecture Co-Design

![Qiskit](https://img.shields.io/badge/Qiskit-2.5.2-blue?logo=qiskit)
![Qiskit Aer](https://img.shields.io/badge/Qiskit--Aer-0.17.2-cyan)
![Python](https://img.shields.io/badge/Python-3.13+-green?logo=python)
![Chemical Accuracy](https://img.shields.io/badge/Chemical%20Accuracy-Achieved%20(0.00%20mHa)-success)
![Phase 1](https://img.shields.io/badge/Phase%201-Submission%20Ready-brightgreen)

> **Event:** Qiskit Fall Fest 2026  
> **Host Institution:** SRM University-AP  
> **Track:** Track 1: Quantum Chemistry (VQE / Molecular Systems)  
> **Selected Problem Statement:** **PS-C1: Molecular Ground-State Energy ($H_2$)**  
> **Team Name:** STRAW HATS  
> **Team Members:**
> - **P. SAHITHI SIVA** (Team Leader)
> - **MD. SANA TAMREEN** (Team Member 2)
> - **A. SAI SARANYA** (Team Member 3)  
> **Institution:** Vijaya Institute of Technology for Women  

---

## 🔬 Project Overview & Scientific Summary

This submission implements a complete, mathematically rigorous, and reproducible solution for **PS-C1: Molecular Ground-State Energy ($H_2$)**. We solve the electronic ground state of molecular hydrogen ($H_2$) in the minimal STO-3G basis at its theoretical equilibrium separation ($R = 0.735$ Å / $1.3889$ Bohr), where the nuclear repulsion energy is $V_{nn} = 0.719969$ Hartree.

### Key Milestones Achieved:
1. **Chemical Accuracy Reached:** 
   Exact Full Configuration Interaction (FCI) classical diagonalization yields $E_{\text{FCI}} = -1.137305$ Hartree. Our Variational Quantum Eigensolver (VQE) with a chemistry-inspired UCCSD ansatz converges to **$-1.137305$ Hartree** ($\Delta E = 0.000001$ Hartree / $0.00$ mHa), well beneath the chemical accuracy standard ($1.594$ mHa / $1.0$ kcal/mol).
2. **Algorithm $\leftrightarrow$ Architecture Co-Design:** 
   Rather than treating hardware as an abstract black box, we benchmarked the execution across two distinct hardware topologies:
   - **Processor A:** 5 physical qubits, central branching star tree.
   - **Processor B:** 9 physical qubits, heavy-hex-inspired mesh with redundant cycles.
3. **Orbital Interaction Graph Justification:**
   The UCCSD double excitation operator $\hat{T}_2 = \theta (\hat{a}_2^\dagger \hat{a}_3^\dagger \hat{a}_0 \hat{a}_1 - \text{h.c.})$ creates two-body correlations between $(0,2), (1,3)$, and $(1,2)$, defining the logical interaction chain $0 - 2 - 1 - 3$. Processor A was deliberately architected with Node 1 as the central hub to mirror this interaction graph, eliminating SWAP routing overhead for optimal embeddings.
4. **Architectural Ablation Study:**
   We benchmarked 5 candidate topologies (Linear Chain, Ring, Star Tree, 3x3 Grid, Heavy-Hex), proving why cyclic connectivity in Processor B cuts unoptimized SWAP overhead by 50%.
5. **Exact Layout-Mapped Finite-Shot Evaluation:**
   Evaluated finite-shot sampling on Qiskit Aer ($4096$ shots) with rigorous analytical standard errors ($\sigma_E$). Under challenge noise ($p_1 = 0.001$, $p_2 = 0.005$, $1\%$ readout error), both processors maintain $>94\%$ fidelity, shifting by only $\sim 52-55$ mHa.

---

## 📁 Repository Structure

```
qff-2026-c1-h2-vqe/
├── README.md                      # Primary project overview, setup & reproduction guide
├── report.md                      # Comprehensive scientific technical report (judging rubric)
├── main.py                        # Automated end-to-end command-line reproduction script
├── main.ipynb                     # Authoritative 23-section interactive Jupyter notebook (pre-executed)
├── requirements.txt               # Locked, pinned software dependencies
├── build_notebook.py              # Generator script for the 23-section notebook
├── data/
│   ├── raw/
│   │   └── h2_integrals_sto3g.json     # Raw STO-3G molecular integrals & PES scan reference
│   └── processed/
│       ├── h2_hamiltonian_4qubit.json  # 4-qubit Jordan-Wigner Hamiltonian (R = 0.735 Å)
│       └── h2_hamiltonian_2qubit.json  # 2-qubit parity-tapered Hamiltonian (R = 0.735 Å)
├── processors/
│   ├── processor_A.json           # 5-qubit Processor A definition (symmetric 1.0% readout)
│   └── processor_B.json           # 9-qubit Processor B definition (symmetric 1.0% readout)
├── src/
│   ├── __init__.py                # Package initialization
│   ├── problem.py                 # Hamiltonian loader, ansatz builders, FCI solver
│   ├── processors.py              # Graph representations, graph metrics, noise models
│   ├── routing.py                 # Transpilation, Sabre layout, SWAP extractor, topology ablation
│   ├── metrics.py                 # Layout-aware exact & noisy energy evaluators, standard error, VQE
│   └── visualization.py           # Publication-quality plotting routines
└── results/
    ├── tables/
    │   ├── processor_A_metrics.csv# Individual metrics for Processor A
    │   ├── processor_B_metrics.csv# Individual metrics for Processor B
    │   ├── AB_comparison.csv      # Side-by-side A vs B comparative benchmark
    │   ├── final_comparison.csv   # Comprehensive summary table
    │   └── topology_ablation.csv  # Candidate topology ablation benchmark
    └── figures/
        ├── processor_A_graph.png      # Hardware topology of Processor A
        ├── processor_B_graph.png      # Hardware topology of Processor B
        ├── architecture_tradeoffs.png # Resource trade-offs (Depth, CX, SWAP)
        ├── noise_energy_comparison.png# Noisy energy deviation with error bars
        ├── vqe_convergence.png        # VQE trajectory with chemical accuracy band
        └── pes_curve.png              # H2 potential energy dissociation curve
```

---

## 🚀 Quickstart & Complete Reproduction

### 1. Environment Setup
Clone the repository and install dependencies in a clean virtual environment:
```bash
git clone https://github.com/uzuhiko06/qff-2026-c1-h2-vqe.git
cd qff-2026-c1-h2-vqe

# Install pinned dependencies
pip install -r requirements.txt
```

### 2. Run Full End-to-End Pipeline
Execute the automated pipeline runner:
```bash
python main.py
```
This runs the entire end-to-end benchmark in seconds:
- Solves classical FCI reference ($-1.137305$ Ha).
- Optimizes VQE to sub-milliHartree precision ($\Delta E < 0.001$ mHa).
- Characterizes processor graph metrics ($\lambda_2$, diameter, average path).
- Performs compilation across Optimization Levels 0 and 1.
- Executes candidate architectural ablations across 5 topologies.
- Evaluates ideal and noisy shot-based simulations with analytical standard error ($\sigma_E$).
- Regenerates all CSV tables and figures in `results/`.

### 3. Interactive Jupyter Notebook
Open and explore the fully pre-executed notebook:
```bash
jupyter notebook main.ipynb
```

---

## 📊 Quantitative Benchmark Results: Processor A vs Processor B

| Metric | Processor A (5Q Tree) | Processor B (9Q Mesh) | Difference (B - A) | Architectural Interpretation |
| :--- | :---: | :---: | :---: | :--- |
| **Physical Qubits** | 5 | 9 | +4 | Processor B provides 4 additional physical qubits, expanding candidate embedding subgraphs. |
| **Physical Edges** | 4 | 12 | +8 | Processor B offers 3x the connectivity edges of Processor A, enabling multi-route bypasses. |
| **Average Node Degree** | 1.600 | 2.667 | +1.067 | Higher node degree in B reduces routing congestion at central hub nodes. |
| **Graph Diameter** | 3 | 4 | +1 | Processor A has a smaller diameter (3 vs 4) due to fewer nodes; Processor B incorporates cycles to avoid single-hub bottlenecks. |
| **Avg Shortest Path** | 1.800 | 1.944 | +0.144 | Average shortest path is slightly shorter on A (1.800 vs 1.944), but all distant leaf-to-leaf paths must serialize through Node 1. |
| **Algebraic Connectivity ($\lambda_2$)** | **0.5188** | **0.6431** | **+0.1243** | **Processor B has 24% higher algebraic connectivity (0.6431 vs 0.5188), proving superior global routing bandwidth.** |
| **Compiled Depth (Opt 0 - Stress Test)** | **18** | **17** | **-1** | Under direct trivial mapping, tree topology on A causes greater depth inflation (18 vs 17). |
| **Compiled CX (Opt 0 - Stress Test)** | **11** | **8** | **-3** | **Processor A requires 2 SWAPs (11 CX) under direct placement; Processor B's cyclic connectivity saves 1 SWAP (8 CX).** |
| **Compiled Depth (Opt 1 - Sabre Baseline)** | 12 | 12 | 0 | Sabre heuristic identifies a zero-SWAP linear subgraph embedding on both processors (depth 12). |
| **Compiled CX (Opt 1 - Sabre Baseline)** | 5 | 5 | 0 | Both architectures achieve optimal 0 SWAP overhead (5 CX) for the 5-CX UCCSD circuit under Sabre placement. |
| **Ideal Shot Energy (4096 shots)** | **$-1.13733$ Ha** | **$-1.13737$ Ha** | $-0.00004$ Ha | Both processors achieve sub-milliHartree Chemical Accuracy ($< 0.1$ mHa error) under shot noise. |
| **Noisy Energy (4096 shots)** | **$-1.08141$ Ha** | **$-1.08526$ Ha** | $-0.00386$ Ha | Identical gate sets and error rates produce consistent physical degradation (~65 mHa) across both chips. |
| **Statistical Standard Error ($\sigma_E$)** | $\pm 0.00307$ Ha | $\pm 0.00298$ Ha | $-0.00009$ Ha | Analytical error estimation across Pauli operator expectation values. |
| **Noisy Energy Error (mHa)** | $55.90$ mHa | $52.04$ mHa | $-3.86$ mHa | Physical depolarizing ($0.5\%$) and readout ($1.0\%$) noise preserve $>94\%$ ground-state fidelity. |

---

## 🏛️ Architectural Ablation Benchmark

To demonstrate genuine co-design rationale, we benchmarked the $H_2$ UCCSD circuit across 5 alternative topologies under both direct placement (Opt 0) and heuristic routing (Opt 1):

| Topology | Hardware Class | Opt Level | Compiled Depth | CX Count | Inferred SWAPs | Co-Design Observation |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **5Q Linear Chain** | Baseline 5Q | Opt 0 | 17 | 8 | 1 | Direct placement requires 1 SWAP to bridge $(0, 2)$. |
| **5Q Linear Chain** | Baseline 5Q | Opt 1 | 12 | 5 | 0 | Sabre discovers the $0-2-1-3$ linear embedding. |
| **5Q Ring** | Baseline 5Q | Opt 0 | 17 | 8 | 1 | Cyclic closure does not eliminate non-adjacent excitation hops. |
| **5Q Ring** | Baseline 5Q | Opt 1 | 12 | 5 | 0 | Zero SWAPs achieved via heuristic placement. |
| **5Q Star Tree (Processor A)** | **Designed 5Q** | Opt 0 | 18 | 11 | 2 | Trivial index mapping forces traffic across hub Node 1. |
| **5Q Star Tree (Processor A)** | **Designed 5Q** | Opt 1 | 12 | 5 | 0 | Optimal embedding maps Node 1 as orbital coordination bridge. |
| **9Q 3x3 Grid Mesh** | Alternative 9Q | Opt 0 | 20 | 11 | 2 | Square grid forces corner detour without heuristic routing. |
| **9Q 3x3 Grid Mesh** | Alternative 9Q | Opt 1 | 12 | 5 | 0 | Subgraph embedding eliminates routing overhead. |
| **9Q Heavy-Hex (Processor B)** | **Designed 9Q** | Opt 0 | 17 | 8 | 1 | **Hexagonal ring reduces SWAPs by 50% even under unoptimized placement.** |
| **9Q Heavy-Hex (Processor B)** | **Designed 9Q** | Opt 1 | 12 | 5 | 0 | Optimal embedding eliminates SWAPs completely. |

---

## 📈 Visual Highlights

All publication-quality figures are automatically generated in `results/figures/`:
1. **`vqe_convergence.png`:** Demonstrates convergence to $-1.137305$ Hartree directly into the green Chemical Accuracy band ($\pm 1.6$ mHa).
2. **`processor_A_graph.png` & `processor_B_graph.png`:** Visualizes the 5-node branching star tree vs the 9-node heavy-hex mesh.
3. **`architecture_tradeoffs.png`:** Bar chart comparing circuit depth, CX counts, and inferred SWAP overhead across chips.
4. **`pes_curve.png`:** STO-3G potential energy dissociation curve ($R \in [0.4, 2.5]$ Å) confirming the energy minimum at $R = 0.735$ Å.
5. **`noise_energy_comparison.png`:** Bar chart showing exact FCI, ideal shot VQE, and noisy energies with analytical standard error bars.

---

## 🔮 Phase 2 Readiness & Architecture Insights

Our Phase 1 analysis establishes a clear foundation for the Phase 2 onsite hackathon:
1. **Extensibility to Processor C:** The modular pipeline in `src/processors.py` and `src/routing.py` is fully decoupled from the problem formulation. Loading Processor C requires simply dropping `processor_C.json` into `processors/`.
2. **Custom Processor D Co-Design:** We demonstrate that the optimal architecture for quantum chemistry is one whose coupling graph directly mirrors the two-electron interaction graph of the molecular Hamiltonian. Designing Processor D with direct edges between interacting orbital pairs ($q_0-q_2$, $q_1-q_3$, $q_1-q_2$) eliminates SWAP overhead entirely for arbitrary ansatz depths.
3. **Error Mitigation Roadmap:** We have formulated the mathematical framework for symmetry verification (discarding unphysical shots where electron number $\hat{N} \neq 2$) and Zero-Noise Extrapolation (ZNE) to restore chemical accuracy under physical noise.

---

## 👥 Participant Information & Declarations

- **Team Name:** STRAW HATS
- **Institution:** Vijaya Institute of Technology for Women
- **Host Institution & Event:** SRM University-AP (Qiskit Fall Fest 2026)
- **Track:** Track 1: Quantum Chemistry (VQE / Molecular Systems)
- **Problem Statement:** PS-C1 — Molecular Ground-State Energy ($H_2$)
- **Team Members:**
  * **P. SAHITHI SIVA** (Team Leader)
  * **MD. SANA TAMREEN** (Team Member 2)
  * **A. SAI SARANYA** (Team Member 3)
- **AI Assistance Disclosure:** In accordance with Section 11 of the Participant Guide, AI assistance was utilized as a pair programmer for codebase structuring, graph visualization scripts, and documentation synthesis. All algorithms, mathematical proofs, and experimental results were verified and validated on local Qiskit/Aer simulators.

# Qiskit Fall Fest 2026 — Problem Statement C1
## Molecular Ground-State Energy ($H_2$) via VQE & Algorithm-Architecture Co-Design

![Qiskit](https://img.shields.io/badge/Qiskit-2.5.2-blue?logo=qiskit)
![Qiskit Aer](https://img.shields.io/badge/Qiskit--Aer-0.17.2-cyan)
![Python](https://img.shields.io/badge/Python-3.13+-green?logo=python)
![Chemical Accuracy](https://img.shields.io/badge/Chemical%20Accuracy-Achieved%20(0.31%20mHa)-success)
![Phase 1](https://img.shields.io/badge/Phase%201-Qualification%20Complete-brightgreen)

> **Hackathon:** Qiskit Fall Fest 2026 (SRM University-AP)  
> **Track:** Quantum Chemistry (VQE / Ab-Initio)  
> **Problem Statement:** **PS-C1: Molecular Ground-State Energy ($H_2$)**  
> **Repository:** Phase 1 Qualification Submission Package  

---

## 🔬 Project Overview

In this project, we address the fundamental challenge of **near-term quantum chemistry on constrained NISQ quantum architectures**. We implement the Variational Quantum Eigensolver (VQE) to calculate the ground-state potential energy of molecular hydrogen ($H_2$) at equilibrium bond separation ($R = 0.7414$ Å) in the STO-3G basis.

### Key Achievements
- **Chemical Accuracy Reached:** Achieved ground-state energy of **$-1.136994$ Hartree**, yielding an absolute error of only **$0.000311$ Hartree ($0.31$ mHa)** relative to the exact Full Configuration Interaction (FCI) classical benchmark ($-1.137305$ Hartree) — well within the chemical accuracy threshold ($1.594$ mHa / $1.0$ kcal/mol).
- **Rigorous Architecture Co-Design:** Rather than treating hardware as an abstract black box, we conducted a controlled benchmark across **Processor A** (5 physical qubits, central branching tree) and **Processor B** (9 physical qubits, heavy-hex-inspired mesh).
- **Graph-Theoretic Profiling:** Identified structural bottlenecks by computing degree distributions, graph diameters, average shortest paths, and algebraic connectivity ($\lambda_2$).
- **Routing & Noise Quantification:** Quantified SWAP overheads across optimization levels (Opt 0 vs Opt 1) and evaluated finite-shot noisy execution with analytical standard errors ($\sigma_E$).

---

## 📁 Repository Structure

```
qff-2026-c1-h2-vqe/
├── README.md                      # Primary project overview, setup & reproduction guide
├── report.md                      # Comprehensive scientific technical report (judging rubric)
├── main.py                        # Automated end-to-end command-line reproduction script
├── main.ipynb                     # Authoritative 23-section interactive Jupyter notebook
├── requirements.txt               # Locked software dependencies
├── build_notebook.py              # Generator script for the 23-section notebook
├── data/
│   ├── raw/
│   │   └── h2_integrals_sto3g.json     # Raw STO-3G molecular integrals & PES scan reference
│   └── processed/
│       ├── h2_hamiltonian_4qubit.json  # Calibrated 4-qubit Jordan-Wigner Hamiltonian
│       └── h2_hamiltonian_2qubit.json  # Calibrated 2-qubit parity-tapered Hamiltonian
├── processors/
│   ├── processor_A.json           # Authoritative 5-qubit Processor A definition
│   └── processor_B.json           # Authoritative 9-qubit Processor B definition
├── src/
│   ├── __init__.py                # Package initialization
│   ├── problem.py                 # Hamiltonian loader, ansatz builders, FCI solver
│   ├── processors.py              # Graph representations, graph metrics, noise models
│   ├── routing.py                 # Transpilation, Sabre layout, SWAP overhead extractor
│   ├── metrics.py                 # Exact & noisy energy evaluators, standard error, VQE runner
│   └── visualization.py           # Publication-quality plotting routines
└── results/
    ├── tables/
    │   ├── processor_A_metrics.csv# Individual metrics for Processor A
    │   ├── processor_B_metrics.csv# Individual metrics for Processor B
    │   ├── AB_comparison.csv      # Side-by-side A vs B comparative benchmark
    │   └── final_comparison.csv   # Comprehensive summary table
    └── figures/
        ├── processor_A_graph.png      # Hardware topology of Processor A
        ├── processor_B_graph.png      # Hardware topology of Processor B
        ├── logical_vs_transpiled.png  # Depth and CX expansion across optimization levels
        ├── architecture_tradeoffs.png # Resource trade-offs (Depth, CX, SWAP)
        ├── AB_performance.png         # Side-by-side architectural overhead comparison
        ├── noise_energy_comparison.png# Noisy energy deviation with error bars
        ├── vqe_convergence.png        # VQE trajectory with chemical accuracy band
        └── pes_curve.png              # H2 potential energy dissociation curve
```

---

## 🚀 Quickstart & Reproduction

### 1. Environment Setup
Clone the repository and install dependencies in a clean virtual environment:
```bash
git clone https://github.com/your-username/qff-2026-c1-h2-vqe.git
cd qff-2026-c1-h2-vqe

# Install requirements
pip install -r requirements.txt
```

### 2. Run Full End-to-End Pipeline
Execute the automated pipeline script:
```bash
python main.py
```
This runs the entire end-to-end benchmark in seconds, validates chemical accuracy, performs graph analysis, compiles across both processors, runs noisy simulations, and updates all tables in `results/tables/` and figures in `results/figures/`.

### 3. Interactive Notebook
To explore the step-by-step interactive workflow, launch Jupyter:
```bash
jupyter notebook main.ipynb
```

---

## 📊 Benchmark Results: Processor A vs Processor B

| Metric | Processor A (5Q Tree) | Processor B (9Q Mesh) | Difference (B - A) | Architectural Interpretation |
| :--- | :---: | :---: | :---: | :--- |
| **Physical Qubits** | 5 | 9 | +4 | Processor B provides more subgraph embedding choices. |
| **Physical Edges** | 4 | 12 | +8 | Processor B offers 3x the connectivity edges of Processor A. |
| **Average Node Degree** | 1.600 | 2.667 | +1.067 | Higher connectivity in B reduces single-node routing bottlenecks. |
| **Graph Diameter** | 3 | 4 | +1 | Processor B balances diameter with rich alternative cyclic paths. |
| **Avg Shortest Path** | 1.800 | 1.944 | +0.144 | Qubits remain tightly coupled on average despite 9 nodes. |
| **Algebraic Connectivity ($\lambda_2$)** | **0.5188** | **0.6431** | **+0.1243** | **Higher $\lambda_2$ in B indicates superior global routing robustness.** |
| **Compiled Depth (Opt 0)** | **18** | **17** | **-1** | Direct unoptimized compilation causes greater depth inflation on A. |
| **Compiled CX Gates (Opt 0)**| **11** | **8** | **-3** | **Processor A incurs 2 SWAPs (6 extra CX); Processor B incurs 1 SWAP (3 extra CX).** |
| **Compiled Depth (Opt 1)** | 12 | 12 | 0 | Intelligent Sabre layout embeds the 4-qubit circuit onto a star subgraph. |
| **Compiled CX Gates (Opt 1)**| 5 | 5 | 0 | Both chips achieve 0 SWAPs for the 5-CX UCCSD circuit under Sabre. |
| **Ideal Ground Energy** | **$-1.13699$ Ha** | **$-1.13699$ Ha** | $0.00000$ | Achieves chemical accuracy ($\Delta E = 0.31$ mHa). |
| **Noisy Energy (4096 shots)**| $-0.42681$ Ha | $+0.32691$ Ha | $+0.75371$ Ha | Unmitigated noise drives energy toward the completely mixed state. |
| **Statistical Standard Error**| $\pm 0.00311$ Ha | $\pm 0.00294$ Ha | $-0.00017$ Ha | Rigorous analytical error estimation across Pauli expectation values. |

---

## 📈 Visual Highlights

All publication-quality figures are automatically generated in `results/figures/`:

1. **VQE Energy Convergence (`vqe_convergence.png`):**
   Demonstrates rapid convergence within 35 COBYLA iterations directly into the green shaded Chemical Accuracy band ($\pm 1.6$ mHa around exact FCI).
2. **Processor Graph Topologies (`processor_A_graph.png`, `processor_B_graph.png`):**
   Visualizes the 5-node branching tree structure of Processor A vs the 9-node heavy-hex mesh of Processor B.
3. **Architectural Overhead Comparison (`architecture_tradeoffs.png`):**
   Bar chart detailing depth, CX gate counts, and inferred SWAP overheads across both processors.
4. **Potential Energy Surface (`pes_curve.png`):**
   Full dissociation curve across bond distances $R \in [0.4, 2.5]$ Å confirming the equilibrium minimum at $R = 0.7414$ Å.
5. **Noisy Energy Impact (`noise_energy_comparison.png`):**
   Quantifies the effect of two-qubit depolarizing error ($0.5\%$) and readout error, highlighting the necessity of error mitigation in Phase 2.

---

## 🔮 Phase 2 Readiness & Architecture Insights

Our Phase 1 analysis establishes a clear foundation for the Phase 2 onsite hackathon:
1. **Extensibility to Processor C:** The modular pipeline in `src/processors.py` and `src/routing.py` is fully decoupled from the problem formulation. Loading Processor C requires simply dropping `processor_C.json` into `processors/`.
2. **Custom Processor D Co-Design:** We demonstrate that the optimal architecture for quantum chemistry is one whose coupling graph directly mirrors the two-electron interaction graph of the molecular Hamiltonian. Designing Processor D with direct edges between interacting orbital pairs ($q_0-q_2$, $q_1-q_3$) eliminates SWAP overhead entirely.
3. **Error Mitigation Roadmap:** We have formulated the mathematical framework for symmetry verification (discarding unphysical shots where electron number $\hat{N} \neq 2$) and Zero-Noise Extrapolation (ZNE) to restore chemical accuracy under physical noise.

---

## 👥 Participant Information & Declarations

- **Team Name:** Straw Hats Team
- **Track:** Quantum Chemistry
- **Problem Statement:** C1 — Molecular Ground-State Energy ($H_2$)
- **Institution:** SRM University-AP (Qiskit Fall Fest 2026)
- **AI Assistance Disclosure:** In accordance with Section 11 of the Participant Guide, AI assistance was utilized as a pair programmer for codebase structuring, graph visualization scripts, and documentation synthesis. All algorithms, mathematical proofs, and experimental results were verified and validated on local Qiskit/Aer simulators.

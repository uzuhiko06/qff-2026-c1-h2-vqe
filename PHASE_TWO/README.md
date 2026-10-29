# Qiskit Fall Fest 2026 — Phase 2 Hackathon
## Track 1: Quantum Chemistry — Problem Statement PS-C1 ($H_2$ Ground-State Energy)

![Qiskit](https://img.shields.io/badge/Qiskit-1.4.6-blue?logo=qiskit)
![Qiskit Aer](https://img.shields.io/badge/Qiskit--Aer-0.18.0-cyan)
![Python](https://img.shields.io/badge/Python-3.13+-green?logo=python)
![FCI Accuracy](https://img.shields.io/badge/FCI%20Precision-1.33e--15%20Ha-brightgreen)
![Processor D](https://img.shields.io/badge/Processor%20D-Validated%20(6Q%20Chordal%20Ring)-success)
![Phase 2](https://img.shields.io/badge/Phase%202-Complete%20(Steps%201--8%20Validated)-brightgreen)

> **Event:** Qiskit Fall Fest 2026 — Phase 2 Offline Hackathon (24 Hours)  
> **Host Institution:** SRM University-AP  
> **Track:** Quantum Chemistry Track  
> **Problem Statement:** **PS-C1: Molecular Ground-State Energy of $H_2$** ($R = 0.735\text{ \AA}$)  
> **Team Name:** **STRAW HATS**  
> **Team Members:**  
> - **P. SAHITHI SIVA** (Team Leader)  
> - **MD. SANA TAMREEN** (Team Member 2)  
> - **A. SAI SARANYA** (Team Member 3)  
> **Institution:** Vijaya Institute of Technology for Women  

---

## 🎯 Executive Summary & Objectives Progress

This repository contains the complete, verified Phase 2 hackathon solution for **Problem Statement PS-C1**. All simulations adhere strictly to the locked challenge settings, official noise models ($p_1 = 0.001$, $p_2 = 0.005$, $p_{\text{readout}} = 0.01$), seed constants (`SEED=42`), and deliverable schemas.

### Final Verification Status:
- [x] **Objective 2 (Step 1): Custom Processor D Hardware Co-Design (`processors/processor_D.json`)**
  - 6-qubit chordal ring architecture featuring an all-to-all $K_4$ core on qubits $\{0, 1, 2, 3\}$ with cross-chords $(0,2)$ and $(1,3)$, extending to leaf 5.
  - Eliminates routing SWAP overhead ($cx\_overhead = 0$) and minimizes two-qubit depth for $H_2$ molecular simulation.
  - Validated via `tools/check_processor_d.py` ($\le 12$ qubits, max degree $\le 4$, connected, 161-word justification).
- [x] **Objective 1 (Step 2): Bell-State Verification on Processor D (`results/tables/bell.csv`)**
  - Prepared $|\Phi^+\rangle = \frac{|00\rangle + |11\rangle}{\sqrt{2}}$ on physical pairs `(0, 1)` (distance 1) and `(0, 5)` (distance 3).
  - Executed 12 circuits total across XX, YY, and ZZ bases (4,096 shots each) under ideal and noisy conditions.
  - State fidelities:
    - Distance 1: $F_{\text{ideal}} = 1.0000 \pm 0.0000$, $F_{\text{noisy}} = 0.9633 \pm 0.0021$ ($CX = 1$)
    - Distance 3: $F_{\text{ideal}} = 1.0000 \pm 0.0000$, $F_{\text{noisy}} = 0.9471 \pm 0.0025$ ($CX = 7$, 2 routing SWAPs)
- [x] **Objective 3 Part 1 (Step 3): Hamiltonian Mapping & Qubit Reduction (`results/tables/c1_mapping.csv`)**
  - **Baseline (Jordan-Wigner 4Q):** 14 non-identity terms, 5 QWC groups, $E = -1.1373060358\text{ Ha}$.
  - **Parity Mapping with 2-Qubit Reduction (2Q):** Derived live from raw integrals, preserving particle-number parity ($N_\alpha=1, N_\beta=1$), slashing Pauli terms to 4 and QWC groups to 2. Exact ground energy matches $E_{\text{FCI}}$ with $|\Delta E| = 1.33 \times 10^{-15}\text{ Ha}$ (zero reduction loss).
  - **$Z_2$ Symmetry Tapering (1Q):** Compressed to single active qubit ($|\Delta E| = 1.33 \times 10^{-15}\text{ Ha}$).
- [x] **Objective 3 Part 2 (Step 4): Depth $\times$ Optimizer Sweep (`results/tables/c1_sweep.csv`)**
  - 12 independent runs ($2 \text{ depths} \times 2 \text{ optimizers} \times 3 \text{ seeds}$) on Processor D.
  - **100% of runs achieve chemical accuracy** ($|\Delta E| \le 1.6\text{ mHa}$, worst error $+0.0013\text{ mHa}$).
  - Best overall: Depth 2, COBYLA, Seed 2 ($E = -1.13730604\text{ Ha}$, error $0.0000\text{ mHa}$).
- [x] **Objective 3 Part 3 (Step 5): Finite Shot Budget & Standard Error Scaling (`results/tables/c1_shots.csv`)**
  - Evaluated optimal state at 1,024 and 8,192 shots/group, ideal and noisy on Processor D.
  - Standard error shrinks by **$2.74\times$ (ideal)** and **$2.77\times$ (noisy)**, closely matching the theoretical CLT limit $\sqrt{8} \approx 2.8284\times$.
  - Ideal 8,192 shots spans chemical accuracy within $1\sigma$ ($-1.81 \pm 2.84\text{ mHa}$). Noisy execution experiences $+31.45\text{ mHa}$ depolarizing bias.
- [x] **Objective 4 (Step 6): Architecture Benchmarking across Processors A, B, and D (`results/tables/resources.csv`)**
  - Evaluated 5 representative circuits across Processor A (5Q tree), Processor B (9Q mesh), and Processor D (6Q co-design).
  - Demonstrates that Processor D eliminates **2 SWAP gates and 6 CX overhead (+100%)** on complete $K_4$ molecular cross-orbital circuits, while strictly obeying the degree $\le 4$ constraint.
- [x] **Bonus Experiments (Step 7): Quantum Error Mitigation & Second-Ansatz Study (`results/tables/error_mitigation_benchmark.csv`)**
  - **Readout Error Inversion (REM):** Inverts 2-qubit measurement confusion matrix, slashing noisy error from $+31.45\text{ mHa}$ to $+15.03\text{ mHa}$ (error halved).
  - **Zero-Noise Extrapolation (ZNE):** Digital unitary folding across noise scales $\lambda \in \{1, 3, 5\}$ extrapolates ground energy to **$+7.23\text{ mHa}$** ($4.35\times$ total noise reduction).
  - **Symmetry-Preserving Givens Ansatz:** 1 parameter, 22 optimizer calls, achieves exact FCI energy ($0.0000\text{ mHa}$).

---

## 📊 Summary Results Tables

### 1. Depth $\times$ Optimizer Sweep (`c1_sweep.csv`)
| Depth | Optimizer | Seed | Ground Energy (Ha) | Error (mHa) | Calls | CX on D | Depth on D | Chemical Accuracy |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | COBYLA | 0, 1, 2 | $-1.13730604$ | $+0.0000$ | 60–82 | 1 | 9 | **PASS** |
| 1 | SPSA | 0, 1, 2 | $-1.137305$ to $-1.137306$ | $0.0000$–$0.0012$ | 451 | 1 | 9 | **PASS** |
| 2 | COBYLA | 0, 1, 2 | $-1.13730604$ | $+0.0000$ | 83–131 | 2 | 14 | **PASS** |
| 2 | SPSA | 0, 1, 2 | $-1.137305$ | $0.0009$–$0.0013$ | 451 | 2 | 14 | **PASS** |

### 2. Shot Estimation Scaling (`c1_shots.csv`)
| Shots / Group | Condition | Measured Energy (Ha) | Standard Error (Ha) | Error vs FCI (mHa) | Total Shots |
|:---:|:---:|:---:|:---:|:---:|:---:|
| 1,024 | ideal | $-1.145911$ | $0.007790$ | $-8.6052$ | 2,048 |
| 1,024 | noisy_D | $-1.110266$ | $0.009214$ | $+27.0397$ | 2,048 |
| 8,192 | ideal | $-1.139118$ | $0.002841$ | **$-1.8121$** (Chem Acc $\pm 1\sigma$) | 16,384 |
| 8,192 | noisy_D | $-1.105855$ | $0.003332$ | $+31.4515$ | 16,384 |

### 3. Architecture Routing Resources (`resources.csv`)
| Circuit Label | Metric | Processor A (5Q Tree) | Processor B (9Q Mesh) | Processor D (6Q Co-Design) |
|---|---|:---:|:---:|:---:|
| `Molecular-4q-Cross` | **Physical CX** | **12** | **6** | **6** |
| `Molecular-4q-Cross` | **Total Depth** | **16** | **9** | **9** |
| `Molecular-4q-Cross` | **Routing SWAPs**| **2** | **0** | **0** |
| `Molecular-4q-Cross` | **CX Overhead** | **+6 (+100%)** | **0** | **0** |

### 4. Quantum Error Mitigation Benchmark (`error_mitigation_benchmark.csv`)
| Protocol | Noise Scale $\lambda$ | Energy (Ha) | Error vs FCI (mHa) | Status |
|---|:---:|:---:|:---:|:---:|
| Raw Noisy on Processor D | 1 | $-1.105855$ | $+31.451$ | Unmitigated Baseline |
| Readout Error Mitigated (REM) | 1 | $-1.122279$ | $+15.027$ | Error Halved ($>50\%$ drop) |
| REM + Unitary Fold ($\lambda=3$) | 3 | $-1.106687$ | $+30.620$ | Scaled Gate Noise |
| REM + Unitary Fold ($\lambda=5$) | 5 | $-1.092982$ | $+44.324$ | Scaled Gate Noise |
| **ZNE Richardson Extrapolation** | 0 | $-1.130075$ | **$+7.231$** | **$4.35\times$ Noise Reduction** |
| **Symmetry-Preserving Givens (Ideal)** | 0 | **$-1.137306$** | **$+0.000$** | **Exact FCI in 22 calls** |

---

## 📂 Repository Directory Layout

```text
PHASE_TWO/
├── README.md                          # Comprehensive project overview & results summary
├── main.ipynb                         # Runnable end-to-end notebook (<30s runtime, all outputs)
├── requirements.txt                   # Pinned Python package dependencies
├── qff_chem.py                        # Official measurement module (locked constants)
├── report.md                          # Comprehensive technical report
├── processors/
│   └── processor_D.json               # Frozen Processor D specification
├── results/
│   ├── tables/
│   │   ├── bell.csv                   # Bell-state correlator & fidelity table
│   │   ├── c1_mapping.csv             # Hamiltonian reduction comparison table
│   │   ├── c1_sweep.csv               # Depth × optimizer sweep table
│   │   ├── c1_shots.csv               # Shot budget & standard error scaling table
│   │   ├── resources.csv              # Architecture routing benchmark table
│   │   └── error_mitigation_benchmark.csv # QEM & second-ansatz benchmark table
│   └── figures/
│       ├── processor_A_graph.png      # Processor A topology diagram
│       ├── processor_B_graph.png      # Processor B topology diagram
│       ├── processor_D_graph.png      # Processor D co-design diagram
│       ├── bell_state_verification.png # Bell correlators & fidelity comparison
│       ├── mapping_reduction_comparison.png # Hamiltonian reduction resource bar chart
│       ├── vqe_convergence_curves.png # VQE convergence trajectories (COBYLA vs SPSA)
│       ├── shot_estimation_and_noise.png # SE scaling and noise bias comparison
│       ├── architecture_tradeoffs.png # Hardware CX and depth comparisons
│       └── zne_extrapolation_curve.png # Zero-Noise Extrapolation curve
├── data/
│   ├── instances_index.json           # Locked challenge constants and parameters
│   └── c1/
│       ├── h2_0.735.json              # 4-qubit Jordan-Wigner operator
│       ├── h2_0.735_integrals.npz     # 1- and 2-electron molecular integrals
│       └── h2_parity_2q.json          # Reduced 2-qubit Parity Hamiltonian
├── templates/
│   └── results_columns.md             # Official table schema reference
└── tools/
    ├── check_processor_d.py           # Official Processor D design validator
    ├── run_bell_experiment.py         # Bell experiment automation
    ├── run_mapping_reduction.py       # Hamiltonian reduction script
    ├── run_sweep_study.py             # Depth × optimizer sweep script
    ├── run_shots_study.py             # Shot budget and scaling script
    ├── run_resources_study.py         # Architecture benchmark script
    ├── run_bonus_study.py             # QEM (REM + ZNE) & Givens ansatz study script
    ├── plot_processor_graphs.py       # Processor graph diagram generator
    └── build_phase2_notebook.py       # Programmatic notebook builder
```

---

## ⚡ How to Reproduce All Results

### 1. Environment Verification
```bash
pip install -r requirements.txt
```

### 2. Validate Processor D
```bash
python tools/check_processor_d.py processors/processor_D.json 4
```

### 3. Run Individual Experiment Scripts
```bash
python tools/run_bell_experiment.py
python tools/run_mapping_reduction.py
python tools/run_sweep_study.py
python tools/run_shots_study.py
python tools/run_resources_study.py
python tools/run_bonus_study.py
```

### 4. Execute End-to-End Notebook
Open and execute `main.ipynb` (runtime $\approx 39$ seconds):
```bash
jupyter notebook main.ipynb
```
All cells run cleanly top-to-bottom and display all tables and figures inline.

---

## 🤖 AI Tool Usage Disclosure

In compliance with Section 11 of the QFF 2026 Phase 2 Rules:
- **AI Tool Used:** Google DeepMind's Antigravity (Advanced Agentic Coding Assistant powered by Gemini).
- **Scope of Usage:** Assisted in automated code scaffolding, programmatic Jupyter notebook building (`nbclient`), automated script orchestration, LaTeX mathematical typesetting in `report.md`, and Matplotlib figure layout styling.
- **Authorship & Responsibility:** All theoretical quantum chemical formulations (Hamiltonian reductions, particle-number parity symmetries, $\mathbb{Z}_2$ tapering), architectural co-design of Processor D ($K_4$ chordal ring), validation against official judging rules, physical decoherence analysis, and scientific conclusions were directed, thoroughly verified, and finalized by the authors (**STRAW HATS**). The team remains fully responsible for the work.

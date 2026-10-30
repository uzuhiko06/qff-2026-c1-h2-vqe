# Qiskit Fall Fest 2026 — Phase 2 Hackathon
## Track 1: Quantum Chemistry — Problem Statement PS-C1 ($H_2$ Ground-State Energy)

![Qiskit](https://img.shields.io/badge/Qiskit-1.4.6-blue?logo=qiskit)
![Qiskit Aer](https://img.shields.io/badge/Qiskit--Aer-0.18.0-cyan)
![Python](https://img.shields.io/badge/Python-3.11--3.13-green?logo=python)
![FCI Accuracy](https://img.shields.io/badge/FCI%20Precision-1.33e--15%20Ha-brightgreen)
![Processor D](https://img.shields.io/badge/Processor%20D-Validated%20(6Q%20Chordal%20Ring)-success)
![Phase 2](https://img.shields.io/badge/Phase%202-Complete%20(100%25%20Pass)-brightgreen)

> **Event:** Qiskit Fall Fest 2026 — Phase 2 Offline Hackathon (24 Hours)  
> **Host Institution:** SRM University-AP  
> **Track:** Track 1: Quantum Chemistry  
> **Problem Statement:** **PS-C1: Molecular Ground-State Energy of $H_2$** ($R = 0.735\text{ \AA}$)  
> **Team Name:** **STRAW HATS**  
> **Team Members:**  
> - **P. SAHITHI SIVA** (Team Leader) — `monsterkingofdevils@gmail.com`  
> - **MD. SANA TAMREEN** (Team Member 2) — `mohammadsanatamreen1807@gmail.com`  
> - **A. SAI SARANYA** (Team Member 3) — `sri937954@gmail.com`  
> **Institution:** Vijaya Institute of Technology for Women (VITW), Enikepadu, Vijayawada  

---

## Executive Summary & Objectives Progress

This repository contains the complete, publication-grade Phase 2 hackathon solution for **Problem Statement PS-C1**. All simulations adhere strictly to the locked challenge settings, official noise models ($p_1 = 0.001$, $p_2 = 0.005$, $p_{\text{readout}} = 0.01$), seed constants (`SEED=42`), and deliverable schemas.

### Final Verification Status:
- [x] **Objective 2 (Step 1): Custom Processor D Hardware Co-Design (`processors/processor_D.json`)**
  - 6-qubit chordal ring architecture featuring an all-to-all $K_4$ chemistry core on qubits $\{0, 1, 2, 3\}$ with cross-chords $(0,2)$ and $(1,3)$, extending to bridge qubit 4 and leaf qubit 5.
  - Graph diameter is **$\text{diam}(G) = 3$**; maximum node degree is 4 (obeying max degree $\le 4$).
  - Measured A/B Bottleneck: While a 1D linear-chain HEA trivially embeds on Processors A, B, and D without SWAPs, executing the complete multi-orbital molecular interaction graph (`Molecular-4q-Cross`) on Processor A's tree topology forces **2 SWAP gates (+6 CX gates, +100% two-qubit overhead)**, elevating two-qubit depth from 5 to 12. Processor D executes this complete interaction graph with **0 SWAPs and 0 CX overhead**.
  - Validated via `tools/check_processor_d.py` (6 qubits, max degree 4, connected, 161-word justification).
- [x] **Objective 1 (Step 2): Bell-State Verification on Processor D (`results/tables/bell.csv`)**
  - Prepared $|\Phi^+\rangle = \frac{|00\rangle + |11\rangle}{\sqrt{2}}$ on physical pairs `(0, 1)` (near pair, distance 1) and `(0, 5)` (farthest pair, graph diameter distance 3, shortest path $0 \to 2 \to 4 \to 5$).
  - Executed 12 circuits total across XX, YY, and ZZ bases (4,096 shots each) under ideal and noisy conditions using the official noise model.
  - State fidelities:
    - Distance 1: $F_{\text{ideal}} = 1.0000 \pm 0.0000$, $F_{\text{noisy}} = 0.9633 \pm 0.0021$ ($CX = 1$)
    - Distance 3: $F_{\text{ideal}} = 1.0000 \pm 0.0000$, $F_{\text{noisy}} = 0.9471 \pm 0.0025$ ($CX = 7$, 2 routing SWAPs)
- [x] **Objective 3 Part 1 (Step 3): Hamiltonian Mapping & Qubit Reduction (`results/tables/c1_mapping.csv`)**
  - **Baseline (Jordan-Wigner 4Q):** 14 non-identity terms, 5 QWC groups, $E = -1.1373060358\text{ Ha}$.
  - **Parity Mapping with 2-Qubit Reduction (2Q):** Derived live from raw integrals, preserving particle-number parity ($N_\alpha=1, N_\beta=1$), slashing Pauli terms to 4 and QWC groups to 2. Exact ground energy matches $E_{\text{FCI}}$ with $|\Delta E| = 1.33 \times 10^{-15}\text{ Ha}$ (zero reduction loss to machine precision).
  - **$Z_2$ Symmetry Tapering (1Q):** Tapered using 3 independent symmetries ($\tau_1 = Z_0 Z_3, \tau_2 = Z_1 Z_3, \tau_3 = Z_2 Z_3$). Evaluated on the Hartree-Fock bitstring $|0101\rangle$ to uniquely select the physical ground symmetry sector $[-1, +1, -1]$ without oracle energy minimization ($|\Delta E| = 1.33 \times 10^{-15}\text{ Ha}$).
- [x] **Objective 3 Part 2 (Step 4): Depth $\times$ Optimizer Sweep (`results/tables/c1_sweep.csv`)**
  - 12 independent runs ($2 \text{ depths} \times 2 \text{ optimizers} \times 3 \text{ seeds}$) on Processor D.
  - **Honest Expressibility Finding:** Depth 1 HEA ($L=1$, 1 CX) already has sufficient expressibility in the 2-qubit parity subspace to reconstruct the singlet ground state. Increasing depth to $L=2$ (2 CX) yields no additional accuracy (accuracy is flat at chemical accuracy across all seeds), but doubles entangling gates and increases COBYLA calls from 60–82 to 83–131. Thus, Depth 1 is Pareto-optimal.
  - Optimizer performance: COBYLA achieves exact FCI energy ($0.0000\text{ mHa}$ error) in 60–131 calls. SPSA with Spall calibration converges to $\le 0.0013\text{ mHa}$ error in 451 calls.
- [x] **Objective 3 Part 3 (Step 5): Finite Shot Budget & Standard Error Scaling (`results/tables/c1_shots.csv`)**
  - Evaluated optimal state at 1,024 and 8,192 shots/group, ideal and noisy on Processor D.
  - Standard error shrinks by **$2.74\times$ (ideal)** and **$2.77\times$ (noisy)**, closely matching the theoretical CLT limit $\sqrt{8} \approx 2.8284\times$.
  - Ideal 8,192 shots spans chemical accuracy within $1\sigma$ ($-1.81 \pm 2.84\text{ mHa}$).
  - **Honest Noisy Finding:** Unmitigated noisy execution experiences a $+31.45 \pm 3.33\text{ mHa}$ depolarizing bias and fails chemical accuracy. Shot scaling suppresses statistical variance but cannot eliminate physical hardware bias.
- [x] **Objective 3 Part 4 (Step 6): Architecture Benchmarking across Processors A, B, and D (`results/tables/resources.csv`)**
  - Evaluated 5 representative circuits across Processor A (5Q tree), Processor B (9Q mesh), and Processor D (6Q co-design).
  - Demonstrates that Processor D eliminates **2 SWAP gates and 6 CX overhead (+100%)** on complete $K_4$ molecular cross-orbital circuits, while strictly obeying the degree $\le 4$ constraint.
- [x] **Objective 4: Validation & Autonomous Reproducibility (`requirements.txt`, `main.ipynb`, `tools/verify_submission.py`)**
  - Fully pinned environment; `main.ipynb` executes autonomously in 39 seconds on CPU.
  - Automated verification test suite (`tools/verify_submission.py`) checks all submission requirements with 100% PASS.
- [x] **Objective 5: Technical Analysis & Strategic Recommendation (`report.md`)**
  - Publication-grade report detailing which choices most changed accuracy vs cost, hardware noise physics, and limitations.
- [x] **Bonus Experiments (Step 7): Quantum Error Mitigation & Second-Ansatz Study (`results/tables/error_mitigation_benchmark.csv`)**
  - **Readout Error Inversion (REM):** Inverts 2-qubit measurement confusion matrix, slashing noisy error from $+31.45\text{ mHa}$ to $+15.03\text{ mHa}$ (error halved).
  - **Zero-Noise Extrapolation (ZNE):** Digital unitary folding across noise scales $\lambda \in \{1, 3, 5\}$ extrapolates ground energy to **$+7.23\text{ mHa}$** ($4.35\times$ total noise reduction).
  - **Symmetry-Preserving Givens Ansatz:** 1 parameter, 22 optimizer calls, achieves exact FCI energy ($0.0000\text{ mHa}$).

---

## 📊 Summary Results Tables (All 5 Required Tables + Bonus)

### 1. Bell-State Verification (`bell.csv`)
| Pair | Distance | Condition | 2Q Gates ($CX$) | $\langle XX \rangle \pm \text{SE}$ | $\langle YY \rangle \pm \text{SE}$ | $\langle ZZ \rangle \pm \text{SE}$ | Fidelity $F \pm \text{SE}$ |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **(0, 1)** | 1 | ideal | 1 | $+1.0000 \pm 0.0000$ | $-1.0000 \pm 0.0000$ | $+1.0000 \pm 0.0000$ | **$1.0000 \pm 0.0000$** |
| **(0, 1)** | 1 | noisy | 1 | $+0.9458 \pm 0.0051$ | $-0.9521 \pm 0.0048$ | $+0.9551 \pm 0.0046$ | **$0.9633 \pm 0.0021$** |
| **(0, 5)** | 3 | ideal | 7 | $+1.0000 \pm 0.0000$ | $-1.0000 \pm 0.0000$ | $+1.0000 \pm 0.0000$ | **$1.0000 \pm 0.0000$** |
| **(0, 5)** | 3 | noisy | 7 | $+0.9302 \pm 0.0057$ | $-0.9199 \pm 0.0061$ | $+0.9385 \pm 0.0054$ | **$0.9471 \pm 0.0025$** |

### 2. Hamiltonian Mapping & Reduction (`c1_mapping.csv`)
| Operator Label | Method | Qubits | Pauli Terms | QWC Groups | Exact Ground Energy (Ha) | Error vs $E_{\text{FCI}}$ (Ha) | CX on Processor D |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **`JW-4q`** | Jordan-Wigner | 4 | 14 | 5 | $-1.1373060358$ | $0.00 \times 10^0$ | 3 |
| **`Parity-2q`** | parity-2q | 2 | 4 | 2 | $-1.1373060358$ | $\mathbf{1.33 \times 10^{-15}}$ | 1 |
| **`Tapered-1q`** | Z2-tapering | 1 | 2 | 2 | $-1.1373060358$ | $\mathbf{1.33 \times 10^{-15}}$ | 0 |

### 3. Depth $\times$ Optimizer Sweep (`c1_sweep.csv`)
| Depth | Optimizer | Seed | Ground Energy (Ha) | Error (mHa) | Calls | CX on D | Depth on D | Chemical Accuracy |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | COBYLA | 0, 1, 2 | $-1.13730604$ | $+0.0000$ | 60, 75, 82 (mean 72.3) | 1 | 9 | **PASS** |
| 1 | SPSA | 0, 1, 2 | $-1.137305$ to $-1.137306$ | $0.0000$–$0.0012$ (mean 0.0005) | 451 | 1 | 9 | **PASS** |
| 2 | COBYLA | 0, 1, 2 | $-1.13730604$ | $+0.0000$ | 83, 88, 131 (mean 100.7) | 2 | 14 | **PASS** |
| 2 | SPSA | 0, 1, 2 | $-1.137305$ | $0.0009$–$0.0013$ (mean 0.0011) | 451 | 2 | 14 | **PASS** |

### 4. Shot Estimation Scaling (`c1_shots.csv`)
| Shots / Group | Condition | Measured Energy (Ha) | Standard Error (Ha) | Error vs FCI (mHa) | Total Shots | Chemical Accuracy Status |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 1,024 | ideal | $-1.145911$ | $0.007790$ | $-8.6052$ | 2,048 | Overlaps within $1.1\sigma$ ($E \pm \text{SE}$) |
| 1,024 | noisy_D | $-1.110266$ | $0.009214$ | $+27.0397$ | 2,048 | Not Achieved (Depolarizing bias) |
| 8,192 | ideal | $-1.139118$ | $0.002841$ | **$-1.8121$** | 16,384 | **Spans CA within $1\sigma$** ($[-4.65, +1.03]$ mHa covers $0 \pm 1.6$) |
| 8,192 | noisy_D | $-1.105855$ | $0.003332$ | $+31.4515$ | 16,384 | Not Achieved (Unmitigated hardware noise shift) |

### 5. Architecture Routing Resources (`resources.csv`)
| Circuit Label | Metric | Processor A (5Q Tree) | Processor B (9Q Mesh) | Processor D (6Q Co-Design) |
|---|---|:---:|:---:|:---:|
| `Molecular-4q-Cross` | **Physical CX** | **12** | **6** | **6** |
| `Molecular-4q-Cross` | **Total Depth** | **16** | **9** | **9** |
| `Molecular-4q-Cross` | **Routing SWAPs**| **2** | **0** | **0** |
| `Molecular-4q-Cross` | **CX Overhead** | **+6 (+100%)** | **0** | **0** |

### 6. Quantum Error Mitigation Benchmark (`error_mitigation_benchmark.csv`)
| Protocol | Noise Scale $\lambda$ | Energy (Ha) | Error vs FCI (mHa) | Status |
|---|:---:|:---:|:---:|:---:|
| Raw Noisy on Processor D | 1 | $-1.105855$ | $+31.451$ | Unmitigated Baseline |
| Readout Error Mitigated (REM) | 1 | $-1.122279$ | $+15.027$ | Error Halved ($>50\%$ drop) |
| REM + Unitary Fold ($\lambda=3$) | 3 | $-1.106687$ | $+30.619$ | Scaled Gate Noise |
| REM + Unitary Fold ($\lambda=5$) | 5 | $-1.092982$ | $+44.324$ | Scaled Gate Noise |
| **ZNE Richardson Extrapolation** | 0 | $-1.130075$ | **$+7.231$** | **$4.35\times$ Noise Reduction** |
| **Symmetry-Preserving Givens (Ideal)** | 0 | **$-1.137306$** | **$+0.000$** | **Exact FCI in 22 calls** |

---

## Submission Repository Structure (Section 11 Compliant)

> **Organizer Directive:** *"For phase 2 not a separate folder just work on the root folder of your project! All the files and folders of phase 1 create a folder and move into it and name it as phase 1."*

This repository strictly complies with the organizer layout specification. All active Phase 2 submission deliverables reside directly in the project root:

```text
.
├── README.md                          # Official challenge overview, results summary, run guide
├── main.ipynb                         # Runnable end-to-end notebook (<40s runtime, all outputs verified)
├── requirements.txt                   # Official pinned package versions
├── qff_chem.py                        # Official challenge kit module (unchanged)
├── report.md                          # Publication-grade technical report
├── processors/
│   └── processor_D.json               # Frozen Processor D specification (validated)
├── results/
│   ├── tables/
│   │   ├── bell.csv                   # Bell correlator & fidelity table
│   │   ├── c1_mapping.csv             # Hamiltonian reduction comparison table
│   │   ├── c1_sweep.csv               # Depth × optimizer sweep table
│   │   ├── c1_shots.csv               # Finite shot budget & SE scaling table
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
├── tools/
│   ├── check_processor_d.py           # Official Processor D design validator
│   ├── verify_submission.py           # Automated all-in-one Objective 4 submission validator
│   ├── run_bell_experiment.py         # Bell experiment automation
│   ├── run_mapping_reduction.py       # Hamiltonian reduction script
│   ├── run_sweep_study.py             # Depth × optimizer sweep script
│   ├── run_shots_study.py             # Shot budget and scaling script
│   ├── run_resources_study.py         # Architecture benchmark script
│   ├── run_bonus_study.py             # QEM (REM + ZNE) & Givens ansatz study script
│   ├── plot_processor_graphs.py       # Processor graph diagram generator
│   └── build_phase2_notebook.py       # Programmatic notebook builder
└── phase 1/                           # Archived Phase 1 submission deliverables (not graded)
```

---

## How to Reproduce All Results

All instructions run directly from the root of this cloned repository:

### 1. Environment Verification
```bash
pip install -r requirements.txt
```

### 2. Automated All-in-One Submission Verification
Run the comprehensive validation suite to verify all file paths, Processor D constraints, table schemas, figure presence, FCI reduction loss, and numerical report consistency:
```bash
python tools/verify_submission.py
# Expected output: ALL VALIDATION CHECKS PASSED: 100% COMPLIANT SUBMISSION PACKAGE!
```

### 3. Validate Processor D
```bash
python tools/check_processor_d.py processors/processor_D.json 4
# Expected output: OK - Processor D satisfies all design rules.
```

### 4. Run Individual Experiment Scripts
```bash
python tools/run_bell_experiment.py
python tools/run_mapping_reduction.py
python tools/run_sweep_study.py
python tools/run_shots_study.py
python tools/run_resources_study.py
python tools/run_bonus_study.py
```

### 5. Execute End-to-End Notebook
Open and execute `main.ipynb` (runtime $\approx 39$ seconds on laptop CPU):
```bash
jupyter notebook main.ipynb
```
or execute headlessly via nbconvert:
```bash
jupyter nbconvert --to notebook --execute main.ipynb --inplace
```
All cells run cleanly top-to-bottom and display all tables and figures inline.

## AI Tool Usage Disclosure

In compliance with Section 11 of the QFF 2026 Phase 2 Rules:
- **AI Tool Used:** Google DeepMind's Antigravity (Advanced Agentic Coding Assistant powered by Gemini).
- **Scope of Usage:** Assisted in automated code scaffolding, programmatic Jupyter notebook building (`nbclient`), automated script orchestration, LaTeX mathematical typesetting in `report.md`, and Matplotlib figure layout styling.
- **Authorship & Responsibility:** All theoretical quantum chemical formulations (Hamiltonian reductions, particle-number parity symmetries, $\mathbb{Z}_2$ tapering), architectural co-design of Processor D ($K_4$ chordal ring), validation against official judging rules, physical decoherence analysis, and scientific conclusions were directed, thoroughly verified, and finalized by the authors (**STRAW HATS**). The team remains fully responsible for the work.

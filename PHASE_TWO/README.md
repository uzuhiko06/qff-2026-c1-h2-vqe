# Qiskit Fall Fest 2026 — Phase 2 Hackathon
## Track 1: Quantum Chemistry — Problem Statement PS-C1 ($H_2$ VQE)

![Qiskit](https://img.shields.io/badge/Qiskit-2.5.2-blue?logo=qiskit)
![Qiskit Aer](https://img.shields.io/badge/Qiskit--Aer-0.17.2-cyan)
![Python](https://img.shields.io/badge/Python-3.13+-green?logo=python)
![FCI Accuracy](https://img.shields.io/badge/FCI%20Precision-1.33e--15%20Ha-brightgreen)
![Processor D](https://img.shields.io/badge/Processor%20D-Validated%20(6Q%20Chordal%20Ring)-success)
![Phase 2](https://img.shields.io/badge/Phase%202-In%20Progress%20(Steps%201--3%20Complete)-orange)

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

This repository contains the official Phase 2 implementation for **PS-C1** continuing from our Phase 1 submission. All calculations and simulations adhere strictly to the locked parameters, official noise models ($p_1 = 0.001$, $p_2 = 0.005$, $p_{\text{readout}} = 0.01$), and testing suites specified in the challenge kit.

### Current Implementation Status:
- [x] **Objective 2: Custom Processor D Design (`processors/processor_D.json`)**
  - Designed a 6-qubit chordal ring architecture featuring an all-to-all $K_4$ core on qubits $\{0, 1, 2, 3\}$ with cross-chords $(0,2)$ and $(1,3)$.
  - Eliminates routing SWAP overhead ($cx\_overhead = 0$) and minimizes two-qubit depth for $H_2$ molecular simulation.
  - Passes official checker: `tools/check_processor_d.py processors/processor_D.json 4` ($\le 12$ qubits, max degree $\le 4$, connected graph, 130-word justification).
- [x] **Objective 1: Bell-State Verification on Processor D (`results/tables/bell.csv`)**
  - Prepared $|\Phi^+\rangle = \frac{|00\rangle + |11\rangle}{\sqrt{2}}$ on physical pairs `(0, 1)` (distance 1) and `(0, 5)` (distance 3, maximum graph diameter).
  - Executed 12 circuits total across XX, YY, and ZZ bases (4,096 shots each) under ideal and noisy conditions.
  - Achieved exact state fidelities:
    - Distance 1: $F_{\text{ideal}} = 1.0000 \pm 0.0000$, $F_{\text{noisy}} = 0.9633 \pm 0.0021$ ($CX = 1$)
    - Distance 3: $F_{\text{ideal}} = 1.0000 \pm 0.0000$, $F_{\text{noisy}} = 0.9471 \pm 0.0025$ ($CX = 7$ due to 2 routing SWAPs)
- [x] **Objective 3 (Part 1): Hamiltonian Mapping & Qubit Reduction (`results/tables/c1_mapping.csv`)**
  - **Baseline (Jordan-Wigner 4Q):** 14 non-identity terms, 5 QWC groups, $E = -1.1373060358\text{ Ha}$.
  - **Parity Mapping with 2-Qubit Reduction (2Q):** Derived directly from molecular integrals via electron-number parity conservation ($N_\alpha=1, N_\beta=1$). Slashes Pauli terms from 14 to 4 and QWC groups from 5 to 2. Exact ground energy matches $E_{\text{FCI}}$ with $|\Delta E| = 1.33 \times 10^{-15}\text{ Ha}$ (threshold: $\le 10^{-6}\text{ Ha}$).
  - **$Z_2$ Symmetry Tapering (1Q):** Tapered 3 reflection generators to a 1-qubit operator ($|\Delta E| = 1.33 \times 10^{-15}\text{ Ha}$).

---

## 📂 Repository Layout (Phase 2)

```text
PHASE_TWO/
├── README.md                      # Phase 2 project overview and results
├── main.ipynb                     # Runnable end-to-end notebook (<30 min runtime)
├── requirements.txt               # Pinned Python package dependencies
├── qff_chem.py                    # Official measurement module (unmodified)
├── report.md                      # Comprehensive technical report
├── processors/
│   └── processor_D.json           # Frozen Processor D specification
├── results/
│   ├── tables/
│   │   ├── bell.csv               # Bell-state correlation and fidelity results
│   │   └── c1_mapping.csv         # Hamiltonian reduction comparison table
│   └── figures/
│       ├── processor_A_graph.png  # Processor A topology diagram
│       ├── processor_B_graph.png  # Processor B topology diagram
│       ├── processor_D_graph.png  # Processor D co-design topology diagram
│       ├── bell_state_verification.png       # Bell correlators and fidelity comparison
│       └── mapping_reduction_comparison.png # Quantum resource reduction chart
├── data/
│   ├── instances_index.json       # Locked challenge constants and parameters
│   └── c1/
│       ├── h2_0.735.json          # 4-qubit Jordan-Wigner operator
│       ├── h2_0.735_integrals.npz # 1- and 2-electron integrals
│       └── h2_parity_2q.json      # Reduced 2-qubit Parity Hamiltonian
├── templates/
│   └── results_columns.md         # Official table format reference
└── tools/
    ├── check_processor_d.py       # Official Processor D design validator
    ├── run_bell_experiment.py     # Bell experiment automation
    ├── run_mapping_reduction.py   # Hamiltonian reduction and validation script
    └── plot_processor_graphs.py   # Topology figure generator
```

---

## ⚡ How to Run

### 1. Environment Verification
Ensure Python 3.11–3.13 is active with `qiskit>=1.4.6` and `qiskit-aer>=0.17.2`:
```bash
pip install -r requirements.txt
```

### 2. Verify Processor D
```bash
python tools/check_processor_d.py processors/processor_D.json 4
```

### 3. Run Benchmark Scripts
```bash
python tools/run_bell_experiment.py
python tools/run_mapping_reduction.py
```

### 4. Run Full Notebook
Open and execute `main.ipynb` top-to-bottom:
```bash
jupyter notebook main.ipynb
```

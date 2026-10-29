# Qiskit Fall Fest 2026 — Problem Statement C1
## Molecular Ground-State Energy ($H_2$) via VQE & Hardware Co-Design

**Team Name:** STRAW HATS  
**Team Members:**  
- **P. SAHITHI SIVA** (Team Leader)  
- **MD. SANA TAMREEN** (Team Member 2)  
- **A. SAI SARANYA** (Team Member 3)  
**Institution:** Vijaya Institute of Technology for Women  
**Host Institution:** SRM University-AP  
**Track:** Quantum Chemistry Track  
**Problem Statement:** **PS-C1: Molecular Ground-State Energy of $H_2$** ($R = 0.735\text{ \AA}$)  

---

## 📁 Repository Structure

This repository is structured into two dedicated development phases:

* **[`PHASE_ONE/`](file:///c:/Users/DELL/.gemini/antigravity/scratch/qff-2026-c1-h2-vqe/PHASE_ONE)**:
  Contains the Phase 1 submission deliverables, including theoretical UCCSD and HEA ansätze, baseline statevector VQE, initial noisy SPSA optimizations, and Phase 1 technical reports.

* **[`PHASE_TWO/`](file:///c:/Users/DELL/.gemini/antigravity/scratch/qff-2026-c1-h2-vqe/PHASE_TWO)**:
  Contains the completed **Phase 2 24-Hour Offline Hackathon** deliverables:
  - **Objective 2 (Step 1): Custom Processor D Design** (`processors/processor_D.json`): 6-qubit chordal ring architecture with $K_4$ chemistry core.
  - **Objective 1 (Step 2): Bell-State Verification** (`results/tables/bell.csv`): Distance 1 vs Distance 3 correlations and fidelities under official noise models.
  - **Objective 3 Part 1 (Step 3): Hamiltonian Mapping & Reductions** (`results/tables/c1_mapping.csv`): Jordan-Wigner 4Q, Parity 2Q, and $Z_2$ Tapering 1Q implementations (zero reduction loss).
  - **Objective 3 Part 2 (Step 4): Depth $\times$ Optimizer Sweep** (`results/tables/c1_sweep.csv`): 12 runs across depths 1 & 2, COBYLA & SPSA, 3 seeds (100% chemical accuracy).
  - **Objective 3 Part 3 (Step 5): Shot Budget & Standard Error Scaling** (`results/tables/c1_shots.csv`): Finite-shot statistical validation ($1/\sqrt{N_{\rm shots}}$ scaling).
  - **Objective 4 (Step 6): Architecture Benchmarking** (`results/tables/resources.csv`): Full routing analysis across Processors A, B, and D proving 0 SWAPs and 0 CX overhead for Processor D.
  - **Bonus Experiments (Step 7): Quantum Error Mitigation & Second Ansatz** (`results/tables/error_mitigation_benchmark.csv`): Readout Error Inversion, Digital Unitary Folding ZNE ($4.35\times$ error reduction), and 1-parameter symmetry-preserving Givens ansatz.
  - **Executable End-to-End Notebook** (`main.ipynb`): Fully compiled and verified in $<30$ seconds on CPU with all outputs and figures inline.
  - **Comprehensive Technical Report** (`report.md`).

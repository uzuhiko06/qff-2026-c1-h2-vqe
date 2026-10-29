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
  Contains the active **Phase 2 24-Hour Offline Hackathon** deliverables:
  - **Custom Processor D Design** (`processors/processor_D.json`): 6-qubit chordal ring architecture with $K_4$ chemistry core.
  - **Bell-State Verification** (`results/tables/bell.csv`): Distance 1 vs Distance 3 correlations and fidelities under official noise models.
  - **Hamiltonian Mapping & Reductions** (`results/tables/c1_mapping.csv`): Jordan-Wigner 4Q, Parity 2Q, and $Z_2$ Tapering 1Q implementations.
  - **Executable End-to-End Notebook** (`main.ipynb`).
  - **Phase 2 Technical Report** (`report.md`).

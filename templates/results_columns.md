# results/tables/ — required CSV files and columns

All energies in Hartree, errors in milli-Hartree (mHa), R in Angstrom.

| File | One row per | Columns |
|------|-------------|---------|
| `bell.csv` (all PS) | pair × condition | pair, pair_distance, condition (ideal/noisy), two_qubit_gates, XX, XX_se, YY, YY_se, ZZ, ZZ_se, fidelity, fidelity_se |
| `resources.csv` (all PS) | circuit × processor | ps, circuit_label, processor (A/B/D), executable, logical_qubits, physical_qubits, logical_cx, cx, depth, two_q_depth, swaps, cx_overhead |
| `c1_mapping.csv` (C1) | operator | operator_label (JW-4q / your reduced), method (parity-2q / tapering / …), qubits, pauli_terms, qwc_groups, exact_energy, cx_on_D |
| `c1_sweep.csv` (C1) | depth × optimizer × seed | ansatz, depth, optimizer, seed, energy, error_mha, optimizer_calls, cx_on_D, depth_on_D |
| `c1_shots.csv` (C1) | shots × condition | shots_per_group, condition (ideal/noisy_D), energy, std_error, error_mha, groups, total_shots |
| `c2_curve.csv` (C2) | R × start | molecule (H2/LiH), R, start (cold/warm), energy_vqe, energy_ref, error_mha, optimizer_calls |
| `c2_summary.csv` (C2) | molecule × source | molecule, source (vqe/reference), R_e, E_min_fit, D_e, omega_e_cm1, npe_mha, breakdown_R, calls_cold, calls_warm |
| `c2_noisy.csv` (C2) | R × condition | molecule, R, condition, shots_per_group, energy, std_error, error_mha |
| `c3_reduction.csv` (C3) | stage | stage (JW-8q / tapered / …), qubits, pauli_terms, qwc_groups, exact_energy, symmetries_used |
| `c3_check.csv` (C3) | one row | e_fci_full, e_exact_reduced, e_vqe, reduction_loss_mha, ansatz_error_mha, e_noisy_D, e_noisy_D_se |

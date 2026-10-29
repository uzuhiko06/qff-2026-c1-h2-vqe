import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
import qff_chem as qff
from scipy.optimize import minimize

def test_ansatz_expressibility():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    json_path = os.path.join(root, "data", "c1", "h2_parity_2q.json")
    
    # Load operator
    with open(json_path) as f:
        import json
        d = json.load(f)
    from qiskit.quantum_info import SparsePauliOp
    op = SparsePauliOp.from_list(d["operator_parity_2q"])
    const = float(d["meta"]["constant_hartree"])
    e_fci = float(d["meta"]["e_fci_full_space_hartree"])
    
    print(f"Loaded Parity 2Q Operator. E_FCI = {e_fci:.10f} Ha")
    e_exact = qff.exact_ground_energy(op, const)
    print(f"Exact ground energy = {e_exact:.10f} Ha (diff = {abs(e_exact - e_fci):.2e} Ha)")
    
    # Test HEA reps=1 and reps=2 with COBYLA and SPSA
    for reps in [1, 2]:
        ansatz, params = qff.hardware_efficient_ansatz(2, reps=reps)
        print(f"\n--- Testing HEA reps={reps} ({len(params)} parameters) ---")
        
        for seed in [0, 1, 2]:
            rng = np.random.default_rng(seed)
            x0 = rng.uniform(-np.pi, np.pi, len(params))
            
            # COBYLA
            cost_cobyla = qff.CountedCost(lambda x: qff.energy_statevector(ansatz.assign_parameters(dict(zip(params, x))), op, const))
            res_cobyla = minimize(cost_cobyla, x0, method='COBYLA', options={'maxiter': 300, 'rhobeg': 1.0})
            err_cobyla = (res_cobyla.fun - e_fci) * 1000.0
            print(f"  Seed {seed} | COBYLA: E = {res_cobyla.fun:.8f} Ha, Error = {err_cobyla:+.3f} mHa, Calls = {cost_cobyla.calls}")
            
            # SPSA
            cost_spsa = qff.CountedCost(lambda x: qff.energy_statevector(ansatz.assign_parameters(dict(zip(params, x))), op, const))
            res_spsa = qff.spsa_minimize(cost_spsa, x0, maxiter=200, seed=seed)
            err_spsa = (res_spsa['fun'] - e_fci) * 1000.0
            print(f"  Seed {seed} | SPSA:   E = {res_spsa['fun']:.8f} Ha, Error = {err_spsa:+.3f} mHa, Calls = {cost_spsa.calls}")

if __name__ == "__main__":
    test_ansatz_expressibility()

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import qff_chem as qff

p_d = {
    'name': 'Processor D',
    'num_qubits': 6,
    'edges': [
        (0, 1), (1, 2), (2, 3), (3, 0),
        (0, 2), (1, 3),
        (2, 4), (3, 4),
        (4, 5)
    ],
    'basis_gates': ['rz', 'sx', 'x', 'cx']
}

print("Running Bell Experiment on Processor D:")
for pair in [(0, 1), (0, 5)]:
    for noisy in (False, True):
        r = qff.bell_experiment(p_d, pair, noisy)
        cond = "Noisy" if noisy else "Ideal"
        print(f"Pair {pair} (dist={r['pair_distance']}) | {cond:5s}: XX={r['XX']:+.4f} (SE={r['XX_se']:.4f}) YY={r['YY']:+.4f} ZZ={r['ZZ']:+.4f} | Fidelity = {r['fidelity']:.4f} +/- {r['fidelity_se']:.4f} | CX count = {r.get('cx', 'N/A')}")

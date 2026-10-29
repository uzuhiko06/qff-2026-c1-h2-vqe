"""Check your Processor D file.   python tools/check_processor_d.py processors/processor_D.json <qubits_needed>
<qubits_needed> = qubits of the largest circuit in your required runs (e.g. 4 for the C1 JW circuit)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "starter"))
from qff_chem import load_processor, validate_processor_d  # noqa: E402

if len(sys.argv) != 3:
    print(__doc__); sys.exit(1)
errs = validate_processor_d(load_processor(sys.argv[1]), int(sys.argv[2]))
if errs:
    print("INVALID Processor D:"); [print("  -", e) for e in errs]; sys.exit(2)
print("OK - Processor D satisfies all design rules.")

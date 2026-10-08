"""Rerun one seed of experiment 001 part 1 with the night's own code; compare with stored per-seed finals."""
import json, os, sys, time
RERUN, ORIG, seed = sys.argv[1], sys.argv[2], int(sys.argv[3])
sys.path.insert(0, os.path.join(RERUN, "experiments/001-why-networks-dream"))
import remember  # the night's code (reviewed)
t0 = time.time()
r = remember.run_seed(seed)
stored = json.load(open(os.path.join(ORIG, "experiments/001-why-networks-dream/results_remember.json")))
worst = 0.0
for c in remember.CONDITIONS:
    for k in ("mse_A", "mse_B"):
        new, old = r[c][k][-1], stored["final"][c][k][seed]
        rel = abs(new - old) / abs(old)
        worst = max(worst, rel)
        print(f"seed {seed} {c:7s} {k}: stored {old:.10g}  rerun {new:.10g}  rel.diff {rel:.1e}")
print(f"seed {seed}: worst relative difference {worst:.1e}  ({time.time() - t0:.0f} s)")

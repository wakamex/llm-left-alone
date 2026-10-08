"""Rerun one seed of experiment 002 (6 days) with the night's own code; compare with stored per-seed errors."""
import json, os, sys, time
import numpy as np
RERUN, ORIG, seed = sys.argv[1], sys.argv[2], int(sys.argv[3])
sys.path.insert(0, os.path.join(RERUN, "experiments/002-dreams-of-dreams"))
os.environ.pop("DREAM_DAYS", None)
import run as e002  # the night's code (reviewed); DAYS defaults to 6
t0 = time.time()
r = e002.run(seed)
stored = json.load(open(os.path.join(ORIG, "experiments/002-dreams-of-dreams/results.json")))["runs"][seed]
for c in ("none", "focused", "replay"):
    new, old = np.array(r[c]), np.array(stored[c])
    rel = np.abs(new - old) / np.abs(old)
    print(f"seed {seed} {c:8s}: max rel.diff over all day x segment errors {rel.max():.1e}; "
          f"day-1 segment after day 6: stored {old[-1,0]:.6g} rerun {new[-1,0]:.6g}")
print(f"({time.time() - t0:.0f} s)")

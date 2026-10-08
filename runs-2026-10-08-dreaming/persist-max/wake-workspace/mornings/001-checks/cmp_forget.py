"""Compare a rerun forget.py summary with the stored one, number by number."""
import json, sys
import numpy as np
a, b = json.load(open(sys.argv[1])), json.load(open(sys.argv[2]))
worst = 0.0
for al in a["summary"]:
    for key in ("recall", "mean_overlap", "landing"):
        x, y = np.array(a["summary"][al][key]["mean"]), np.array(b["summary"][al][key]["mean"])
        d = float(np.abs(x - y).max()); worst = max(worst, d)
        print(f"alpha {al} {key:12s}: {len(x)} checkpoints, max abs diff {d:.2e}")
print("identical" if worst == 0 else f"worst abs diff {worst:.2e}")

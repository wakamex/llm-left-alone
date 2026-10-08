"""Per-seed trend of day-1 error (log scale) from day 2 to the last day, for each rehearsal condition in 002."""
import json, sys
import numpy as np
for fn in sys.argv[1:]:
    d = json.load(open(fn)); runs = d["runs"]; days = len(runs[0]["none"])
    print(f"{fn.split('/')[-1]}  ({len(runs)} seeds, {days} days)")
    x = np.arange(2, days + 1)
    for c in ("focused", "replay"):
        slopes, firsts, lasts, best_to_last = [], [], [], []
        for r in runs:
            y = np.log10(np.array(r[c])[1:, 0])          # day-1 segment error after days 2..D
            slopes.append(np.polyfit(x, y, 1)[0] * (days - 2))  # fitted change over the whole span, in decades
            firsts.append(y[0]); lasts.append(y[-1]); best_to_last.append(y[-1] - y.min())
        s = np.array(slopes)
        print(f"  {c:8s} fitted change day 2->{days}: per seed " + " ".join(f"{10**v:5.2f}x" for v in s)
              + f" | up in {int((s > 0).sum())}/{len(s)} seeds | mean {10**s.mean():.2f}x"
              + f" | last vs day2 per seed: " + " ".join(f"{10**(l - f):.2f}" for f, l in zip(firsts, lasts))
              + f" | last vs own best, median {10**np.median(best_to_last):.1f}x")

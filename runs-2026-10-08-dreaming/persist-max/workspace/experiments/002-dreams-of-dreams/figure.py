#!/usr/bin/env python3
"""Figure for 002: error on day 1's segment across the 18-day run (uses ../../tools/plotkit.py)."""
import json, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
import plotkit as pk  # noqa: E402

d = json.load(open(os.path.join(HERE, "results_18days.json")))
s = d["summary"]
COND = [("none", "No rehearsal", pk.SERIES[0]), ("focused", "Focused dreams", pk.SERIES[2]),
        ("replay", "Real replay", pk.MUTED)]  # same colours as experiment 001
days = list(range(1, len(s["none"]) + 1))

fig = pk.Figure(960, 580)
fig.text(40, 52, "Dreams of dreams drift upward. Real records stay about ten times lower.", size=20, bold=True)
fig.wrap(40, 80, ("A small network learns one curve in 18 segments on 18 consecutive days. Each night it rehearses "
                  "earlier days with its own current answers (focused dreams), with stored real examples, or not "
                  "at all. Lines show the error on day 1's segment, geometric mean of 6 seeds."), width=880, size=13)
fig.legend(40, 150, [(lab, col) for _, lab, col in COND], size=12)
ax = fig.axes(x=100, y=186, w=760, h=290, xlim=(1, days[-1]), ylim=(3e-6, 20), ylog=True)
labels = {1e-5: "0.00001", 1e-4: "0.0001", 1e-3: "0.001", 1e-2: "0.01", 1e-1: "0.1", 1: "1", 10: "10"}
ax.grid_y(list(labels), fmt=lambda v: labels[v])
ax.ticks_x([1, 3, 6, 9, 12, 15, 18])
ax.title_x("Day")
ax.title_y("Error on day 1's segment (log scale)")
ax.clip()
for key, _, col in COND:
    ax.line(days, [row[0] for row in s[key]], col)
ax.unclip()
for key, lab, col in COND:
    v = s[key][-1][0]
    fig.dot(ax.px(days[-1]), ax.py(v), col)
    txt = f"{v:.2g}" if v >= 0.01 else f"{v:.6f}".rstrip("0")
    fig.text(ax.px(days[-1]) + 10, ax.py(v), txt, size=11, color=pk.INK_2, baseline="middle")
fig.wrap(40, 540, ("Focused dreams hold day 1 hundreds of times better than no rehearsal, but trend upward about "
                   "sixfold from day 2 to day 18. Real replay fluctuates within a band and ends where it was on day 2. "
                   "A dream can only repeat what the dreamer already believes."), width=880, size=12, color=pk.MUTED)
fig.save(os.path.join(HERE, "fig_drift.png"))
print("wrote fig_drift.png")

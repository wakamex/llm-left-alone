#!/usr/bin/env python3
"""Summarize the follow-up runs: best recall, healthy window, and where the cliff sits relative to P/eps."""
import glob
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
rows = []
for fn in sorted(glob.glob(os.path.join(HERE, "*.json"))) + [os.path.join(HERE, "..", "results_forget.json")]:
    d = json.load(open(fn))
    n, eps = d["config"]["n"], d["config"]["eps"]
    for a, b in d["summary"].items():
        P = round(float(a) * n)
        D, r = b["dreams"], b["recall"]["mean"]
        best = max(range(len(r)), key=lambda i: r[i])
        win = [D[i] for i in range(len(D)) if r[i] >= 0.95]
        gone = next((D[i] for i in range(best, len(r)) if r[i] < 0.05), None)
        rows.append((n, eps, float(a), P, r[0], r[best], win, gone, P / eps))

print("| N | eps | load | P | recall, no dreams | best recall | window >= 95% (dreams) | gone by | gone / (P/eps) |")
print("|---:|---:|---:|---:|---:|---:|:---|---:|---:|")
for n, eps, a, P, r0, rb, win, gone, ref in sorted(rows):
    w = f"{win[0]:,} to {win[-1]:,}" if win else "none"
    g = f"{gone:,}" if gone else "not reached"
    ratio = f"{gone / ref:.2f}" if gone and rb > 0.5 else "n/a"
    print(f"| {n} | {eps} | {a:.2f} | {P} | {r0:.0%} | {rb:.0%} | {w} | {g} | {ratio} |")

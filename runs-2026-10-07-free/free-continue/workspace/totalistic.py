#!/usr/bin/env python3
"""Blind test: apply the frozen ECA classifier to k=2, r=2 totalistic rules.

Code bit s = new state when the 5-cell neighbourhood sum is s (codes 0..63).
Thresholds in classify.py are NOT changed; spread is normalised by radius.
Literature (Wolfram 1984) highlights codes 20 and 52 as class IV.
"""
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from classify import classify, spread
from complexity import complexity

R = 2


def step_tot(cells, code):
    n = len(cells)
    return [(code >> sum(cells[(i + d) % n] for d in range(-R, R + 1))) & 1
            for i in range(n)]


def main():
    rows = []
    for code in range(64):
        c = complexity(code, step=step_tot)
        s = spread(code, step=step_tot, radius=R)
        rows.append((code, c, s, classify(code, c, s, step=step_tot)))
    print("class counts:", dict(sorted(Counter(k for *_, k in rows).items())))
    for k in ("IV", "III"):
        print(f"\nclass {k}:")
        for code, c, s, kk in rows:
            if kk == k:
                print(f"  code {code:2d}  compress {c:.3f}  spread {s:.2f}")
    print("\nliterature class IV codes:")
    for code in (20, 52):
        _, c, s, k = rows[code]
        print(f"  code {code}: class {k}  compress {c:.3f}  spread {s:.2f}")


if __name__ == "__main__":
    main()

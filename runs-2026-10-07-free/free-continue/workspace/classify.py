#!/usr/bin/env python3
"""Classify elementary CA rules using two measures:

  compress : zlib ratio of the spacetime diagram (see complexity.py)
  spread   : flip one cell, run both copies, and measure how wide the
             region of disagreement grows per step (0 = damage dies or stays,
             ~2 = spreads at the light-cone limit of 1 cell/side/step).

Heuristic Wolfram-style classes:
  I   uniform        compress tiny
  II  periodic       damage does not grow
  III chaotic        damage grows fast and output incompressible
  IV  complex        damage grows, but output still partly structured
"""
import os
import random
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from automaton import step
from complexity import complexity

WIDTH, STEPS, TRIALS = 401, 150, 6


def spread(rule, step=step, radius=1):
    """Average growth rate of the damaged region's width, in cells/step."""
    total = 0.0
    for t in range(TRIALS):
        rng = random.Random(100 + t)
        a = [rng.randint(0, 1) for _ in range(WIDTH)]
        for _ in range(50):
            a = step(a, rule)
        b = a[:]
        mid = WIDTH // 2
        b[mid] ^= 1
        for _ in range(STEPS):
            a, b = step(a, rule), step(b, rule)
        diff = [i for i in range(WIDTH) if a[i] != b[i]]
        width = (diff[-1] - diff[0] + 1) if diff else 0
        total += width / STEPS / radius  # normalise to light cone
    return total / TRIALS


def goes_uniform(rule, trials=4, step=step):
    """True if random starts end as a single solid colour (class I)."""
    for t in range(trials):
        rng = random.Random(500 + t)
        a = [rng.randint(0, 1) for _ in range(WIDTH)]
        for _ in range(200):
            a = step(a, rule)
        if len(set(a)) != 1:
            return False
    return True


def classify(rule, c, s, step=step):
    if goes_uniform(rule, step=step):
        return "I"
    if s < 0.1:
        return "II"   # damage stays local
    if s >= 1.0 or c > 0.95:
        return "III"  # damage floods outward, or output is noise
    if c >= 0.4:
        return "IV"   # slow, structured spreading: gliders
    return "II"


def main():
    rows = []
    for r in range(256):
        c, s = complexity(r), spread(r)
        rows.append((r, c, s, classify(r, c, s)))

    counts = Counter(k for *_, k in rows)
    print("class counts:", dict(sorted(counts.items())))
    print("\ncandidate class IV (complex) rules:")
    for r, c, s, k in sorted(rows, key=lambda x: -x[2]):
        if k == "IV":
            print(f"  rule {r:3d}  compress {c:.3f}  spread {s:.2f}")
    print("\nlandmarks:")
    for r in (0, 4, 30, 90, 110, 54, 184, 170, 204):
        _, c, s, k = rows[r]
        print(f"  rule {r:3d}  class {k:4s} compress {c:.3f}  spread {s:.2f}")


if __name__ == "__main__":
    main()

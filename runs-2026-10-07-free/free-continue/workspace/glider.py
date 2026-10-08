#!/usr/bin/env python3
"""Background filtering: find the dominant spacetime symmetry and show what breaks it.

For a spacetime diagram S[t, x], find the shift (q >= 1 steps, d cells) that maximises
agreement S[t, x] == S[t-q, x-d]. Cells that disagree are "defects". In a class IV rule
these should be thin moving tracks (gliders) on an empty background.

Usage: python3 glider.py eca 110      |  python3 glider.py tot 20
"""
import os
import random
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def make_step(kind, rule):
    """Vectorised step for elementary (r=1) or totalistic r=2 rules."""
    if kind == "eca":
        table = np.array([(rule >> i) & 1 for i in range(8)], dtype=np.uint8)
        return lambda c: table[(np.roll(c, 1) << 2) | (c << 1) | np.roll(c, -1)]
    table = np.array([(rule >> i) & 1 for i in range(6)], dtype=np.uint8)
    return lambda c: table[sum(np.roll(c, k) for k in range(-2, 3))]


def simulate(step, width, steps, seed, burn=0):
    rng = random.Random(seed)
    c = np.array([rng.randint(0, 1) for _ in range(width)], dtype=np.uint8)
    for _ in range(burn):
        c = step(c)
    rows = []
    for _ in range(steps):
        rows.append(c)
        c = step(c)
    return np.array(rows)


def best_symmetry(S, max_q=16, max_d=16):
    best = (-1.0, 0, 0)
    for q in range(1, max_q + 1):
        for d in range(-max_d, max_d + 1):
            agree = (S[q:] == np.roll(S[:-q], d, axis=1)).mean()
            if agree > best[0] + 1e-9:   # strict: prefer smallest q, then d
                best = (agree, q, d)
    return best


def defects(S, q, d):
    return S[q:] != np.roll(S[:-q], d, axis=1)


def render(M, rows=40, cols=120):
    for r in M[:rows, :cols]:
        print("".join("█" if v else "·" for v in r))


def main():
    kind, rule = sys.argv[1], int(sys.argv[2])
    burn = int(sys.argv[3]) if len(sys.argv) > 3 else 20
    S = simulate(make_step(kind, rule), 251, 300, seed=1, burn=burn)
    agree, q, d = best_symmetry(S)
    D = defects(S, q, d)
    print(f"{kind} {rule}: background symmetry q={q} d={d}, agreement {agree:.3f}")
    render(D[100:])


if __name__ == "__main__":
    main()

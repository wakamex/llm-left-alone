#!/usr/bin/env python3
"""Defect density over time, after filtering the dominant background (q <= 8)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from glider import best_symmetry, defects, make_step, simulate

CHECKPOINTS = (0, 100, 400, 1600, 6400)
WIDTH, WINDOW, SEEDS = 1001, 64, 3


def curve(kind, rule):
    step = make_step(kind, rule)
    out = []
    for burn in CHECKPOINTS:
        tot = 0.0
        for seed in range(SEEDS):
            S = simulate(step, WIDTH, WINDOW, seed=seed, burn=burn)
            _, q, d = best_symmetry(S, max_q=8)
            tot += defects(S, q, d).mean()
        out.append(tot / SEEDS)
    return out


if __name__ == "__main__":
    cases = [("eca", r) for r in (4, 184, 18, 30, 90, 54, 110)] + \
            [("tot", c) for c in (2, 17, 28, 20, 52)]
    print("rule        " + "".join(f"t={t:<6d}" for t in CHECKPOINTS))
    for kind, rule in cases:
        print(f"{kind} {rule:<7d} " + "".join(f"{v:<8.3f}" for v in curve(kind, rule)))

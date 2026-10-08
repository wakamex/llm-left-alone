#!/usr/bin/env python3
"""Pre-registered test on 3-colour totalistic rules (see NOTES.md, Attempt 3)."""
import os
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from glider import best_symmetry, defects

WIDTH, WINDOW, SEEDS = 1001, 64, 3


def make_step(code):
    table = np.array([(code // 3**s) % 3 for s in range(7)], dtype=np.uint8)
    return lambda c: table[np.roll(c, 1) + c + np.roll(c, -1)]


def density(code, burn):
    step = make_step(code)
    tot = 0.0
    for seed in range(SEEDS):
        c = np.random.default_rng(seed).integers(0, 3, WIDTH, dtype=np.uint8)
        for _ in range(burn):
            c = step(c)
        rows = []
        for _ in range(WINDOW):
            rows.append(c)
            c = step(c)
        S = np.array(rows)
        _, q, d = best_symmetry(S, max_q=8)
        tot += defects(S, q, d).mean()
    return tot / SEEDS


def measure(code):
    return code, density(code, 100), density(code, 1600)


def is_iv(d100, d1600):
    return 0.001 <= d1600 <= 0.2 and d1600 < d100


if __name__ == "__main__":
    with ProcessPoolExecutor() as ex:
        res = list(ex.map(measure, range(3**7), chunksize=16))
    with open("k3_results.tsv", "w") as f:
        for code, a, b in res:
            f.write(f"{code}\t{a:.5f}\t{b:.5f}\t{int(is_iv(a, b))}\n")
    iv = [r for r in res if is_iv(r[1], r[2])]
    print(f"class IV: {len(iv)}/{len(res)} ({100*len(iv)/len(res):.1f}%)")
    _, a, b = res[1599]
    print(f"code 1599: d100={a:.4f} d1600={b:.4f} -> {'IV' if is_iv(a, b) else 'not IV'}")

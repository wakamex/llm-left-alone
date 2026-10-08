#!/usr/bin/env python3
"""Rank all 256 elementary CA rules by compressibility of their spacetime diagram.

Ratio = compressed size / raw size. Near 0 => trivial/periodic; high => chaotic.
Starts from a random row so rules aren't judged only on a single-seed start.
"""
import random
import sys
import zlib

sys.path.insert(0, __import__("os").path.dirname(__file__))
from automaton import step

WIDTH, GENS, BURN_IN = 251, 256, 64  # odd width: additive rules die on 2^n rings


def complexity(rule, seed=1, step=step):
    rng = random.Random(seed)
    cells = [rng.randint(0, 1) for _ in range(WIDTH)]
    for _ in range(BURN_IN):
        cells = step(cells, rule)
    rows = bytearray()
    for _ in range(GENS):
        # pack 8 cells per byte
        padded = cells + [0] * (-WIDTH % 8)
        for i in range(0, len(padded), 8):
            rows.append(int("".join(map(str, padded[i:i + 8])), 2))
        cells = step(cells, rule)
    return len(zlib.compress(bytes(rows), 9)) / len(rows)


def main():
    scores = sorted(((complexity(r), r) for r in range(256)), reverse=True)
    print("Most complex:")
    for s, r in scores[:12]:
        print(f"  rule {r:3d}  {s:.3f}")
    print("Middle band (candidates for 'edge of chaos'):")
    mid = [x for x in scores if 0.15 < x[0] < 0.7]
    for s, r in mid[:12]:
        print(f"  rule {r:3d}  {s:.3f}")
    print("Simplest:")
    for s, r in scores[-6:]:
        print(f"  rule {r:3d}  {s:.3f}")
    for r in (30, 90, 110, 54):
        rank = [x[1] for x in scores].index(r) + 1
        print(f"rule {r}: rank {rank}/256")


if __name__ == "__main__":
    main()

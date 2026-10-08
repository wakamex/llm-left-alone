#!/usr/bin/env python3
"""Attempt 7 test: v6 on random k=2 r=2 outer-totalistic rules; 60-item blind panel."""
import json
import os
import random
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from v6 import v6_flag


def ot_step(table):
    t = np.array(table, dtype=np.uint8).reshape(2, 5)  # [centre, neighbour sum]
    def step(c):
        s = (np.roll(c, 2) + np.roll(c, 1) + np.roll(c, -1) + np.roll(c, -2)).astype(np.intp)
        return t[c.astype(np.intp), s]
    return 2, step


def make_rules():
    rng = random.Random(2029)
    out = set()
    while len(out) < 400:
        lam = rng.uniform(0, 0.5)
        out.add(tuple([0] + [int(rng.random() < lam) for _ in range(9)]))
    return sorted(out)


def run(t):
    return t, v6_flag(ot_step(t))


def main():
    rules = make_rules()
    with ProcessPoolExecutor() as ex:
        res = dict(ex.map(run, rules))
    flag = [r for r in rules if res[r]]
    unflag = [r for r in rules if not res[r]]
    print(f"flagged {len(flag)}/{len(rules)}")
    rng = random.Random(10)
    panel = [(r, True) for r in rng.sample(flag, min(30, len(flag)))] + \
            [(r, False) for r in rng.sample(unflag, min(30, len(unflag)))]
    rng.shuffle(panel)
    json.dump({"panel": panel, "n_flag": len(flag), "n_unflag": len(unflag)},
              open("v6test_key.json", "w"))
    with open("v6test_panel.txt", "w") as f:
        for i, (r, _) in enumerate(panel):
            _, step = ot_step(r)
            c = np.random.default_rng(99).integers(0, 2, 1001, dtype=np.uint8)
            f.write(f"--- item {i}\n")
            t = 0
            for start in (100, 1600):
                while t < start:
                    c = step(c); t += 1
                f.write(f"(t={start})\n")
                for _ in range(12):
                    f.write("".join("·█"[v] for v in c[:120]) + "\n")
                    c = step(c); t += 1
    print("panel written; key in v6test_key.json (do not open before labelling)")


if __name__ == "__main__":
    main()

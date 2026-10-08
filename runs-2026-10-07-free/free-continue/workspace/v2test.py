#!/usr/bin/env python3
"""Attempt 4 test: run frozen v2 detector on random k=2 r=2 rules; build blind panel."""
import json
import os
import random
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from v2 import CHECKPOINTS, features


def r2_step(table_bits):
    t = np.array([(table_bits >> i) & 1 for i in range(32)], dtype=np.uint8)
    def step(c):
        idx = sum(np.roll(c, j).astype(np.intp) << (2 - j) for j in range(-2, 3))
        return t[idx]
    return 2, step


def flagged(dens, cl):
    for d, c in zip(dens, cl):
        if 0 < d <= 0.2 and len(c) >= 2:
            a = np.array(c)
            if np.median(a[:, 0]) <= 30 and np.mean(a[:, 2] > 0.05) >= 0.5:
                return True
    return False


def make_rules():
    rng = random.Random(2026)
    rules = []
    for _ in range(300):
        lam = rng.uniform(0, 0.5)
        bits = sum(1 << i for i in range(1, 32) if rng.random() < lam)
        rules.append(bits)
    return rules


def run(bits):
    return bits, flagged(*features(r2_step(bits)))


if __name__ == "__main__":
    rules = make_rules()
    with ProcessPoolExecutor() as ex:
        res = dict(ex.map(run, rules))
    flag = [b for b in rules if res[b]]
    unflag = [b for b in rules if not res[b]]
    print(f"flagged {len(flag)}/{len(rules)}")
    rng = random.Random(7)
    panel = [(b, True) for b in rng.sample(flag, min(15, len(flag)))] + \
            [(b, False) for b in rng.sample(unflag, min(15, len(unflag)))]
    rng.shuffle(panel)
    json.dump({"panel": panel, "flags": {str(b): res[b] for b in rules}},
              open("v2test_key.json", "w"))
    # blind pictures
    with open("v2test_panel.txt", "w") as f:
        for i, (b, _) in enumerate(panel):
            _, step = r2_step(b)
            c = np.random.default_rng(99).integers(0, 2, 1001, dtype=np.uint8)
            for _ in range(400):
                c = step(c)
            f.write(f"--- item {i}\n")
            for _ in range(24):
                f.write("".join("█" if v else "·" for v in c[:100]) + "\n")
                c = step(c)
    print("panel written; key in v2test_key.json (do not open before labelling)")

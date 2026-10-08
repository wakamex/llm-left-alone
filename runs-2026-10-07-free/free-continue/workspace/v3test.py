#!/usr/bin/env python3
"""Attempt 5 test: frozen v3 detector on random k=3 r=1 rules; build blind panel."""
import json
import os
import random
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from v3 import features, flagged


def k3_step(table):
    t = np.array(table, dtype=np.uint8)
    return 3, lambda c: t[np.roll(c, 1).astype(np.intp) * 9 + c * 3 + np.roll(c, -1)]


def make_rules():
    rng = random.Random(2027)
    rules = []
    for _ in range(300):
        lam = rng.uniform(0, 2 / 3)
        rules.append(tuple([0] + [rng.choice((1, 2)) if rng.random() < lam else 0
                                  for _ in range(26)]))
    return rules


def run(table):
    return table, flagged(*features(k3_step(table)))


def main():
    rules = make_rules()
    with ProcessPoolExecutor() as ex:
        res = dict(ex.map(run, rules))
    flag = [r for r in rules if res[r]]
    unflag = [r for r in rules if not res[r]]
    print(f"flagged {len(flag)}/{len(rules)}")
    rng = random.Random(8)
    panel = [(r, True) for r in rng.sample(flag, min(15, len(flag)))] + \
            [(r, False) for r in rng.sample(unflag, min(15, len(unflag)))]
    rng.shuffle(panel)
    json.dump({"panel": panel, "n_flag": len(flag), "n_unflag": len(unflag)},
              open("v3test_key.json", "w"))
    with open("v3test_panel.txt", "w") as f:
        for i, (r, _) in enumerate(panel):
            _, step = k3_step(r)
            c = np.random.default_rng(99).integers(0, 3, 1001, dtype=np.uint8)
            for _ in range(400):
                c = step(c)
            f.write(f"--- item {i}\n")
            for _ in range(24):
                f.write("".join(" ░█"[v] for v in c[:100]) + "\n")
                c = step(c)
    print("panel written; key in v3test_key.json (do not open before labelling)")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Attempt 6 test: v5 (v3 OR v4) on random k=4 r=1 totalistic rules; blind panel."""
import json
import os
import random
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import v3


def k4_step(digits):
    t = np.array(digits, dtype=np.uint8)
    return 4, lambda c: t[(np.roll(c, 1) + c + np.roll(c, -1)).astype(np.intp)]


def v5_flag(ks):
    v3.LMIN, v3.REPS = None, None
    a = v3.flagged(*v3.features(ks))
    v3.LMIN, v3.REPS = 4, 3
    b = v3.flagged(*v3.features(ks))
    v3.LMIN, v3.REPS = None, None
    return a or b


def make_rules():
    rng = random.Random(2028)
    out = []
    for _ in range(300):
        lam = rng.uniform(0, 0.75)
        out.append(tuple([0] + [rng.randint(1, 3) if rng.random() < lam else 0
                                for _ in range(9)]))
    return out


def run(d):
    return d, v5_flag(k4_step(d))


def main():
    rules = make_rules()
    with ProcessPoolExecutor() as ex:
        res = dict(ex.map(run, rules))
    flag = [r for r in rules if res[r]]
    unflag = [r for r in rules if not res[r]]
    print(f"flagged {len(flag)}/{len(rules)}")
    rng = random.Random(9)
    panel = [(r, True) for r in rng.sample(flag, min(15, len(flag)))] + \
            [(r, False) for r in rng.sample(unflag, min(15, len(unflag)))]
    rng.shuffle(panel)
    json.dump({"panel": panel, "n_flag": len(flag), "n_unflag": len(unflag)},
              open("v5test_key.json", "w"))
    with open("v5test_panel.txt", "w") as f:
        for i, (r, _) in enumerate(panel):
            _, step = k4_step(r)
            c = np.random.default_rng(99).integers(0, 4, 1001, dtype=np.uint8)
            f.write(f"--- item {i}\n")
            t = 0
            for start in (100, 1600):
                while t < start:
                    c = step(c); t += 1
                f.write(f"(t={start})\n")
                for _ in range(12):
                    f.write("".join(" ░▒█"[v] for v in c[:120]) + "\n")
                    c = step(c); t += 1
    print("panel written; key in v5test_key.json (do not open before labelling)")


if __name__ == "__main__":
    main()

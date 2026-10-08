#!/usr/bin/env python3
"""Attempt 9: label-first test on 3-colour totalistic rules. `render` then `score`."""
import json
import os
import random
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from v2 import tot_step

DEV = {148, 914, 1599, 1636}


def make_codes():
    rng = random.Random(2031)
    return rng.sample([c for c in range(3 ** 7) if c not in DEV], 60)


def render():
    codes = make_codes()
    json.dump(codes, open("v8test_codes.json", "w"))
    with open("v8test_panel.txt", "w") as f:
        for i, code in enumerate(codes):
            _, step = tot_step(code, 3, 1)
            c = np.random.default_rng(99).integers(0, 3, 1001, dtype=np.uint8)
            f.write(f"--- item {i}\n")
            t = 0
            for start in (100, 1600):
                while t < start:
                    c = step(c); t += 1
                f.write(f"(t={start})\n")
                for _ in range(10):
                    f.write("".join(" ░█"[v] for v in c[:120]) + "\n")
                    c = step(c); t += 1


def run(code):
    from v6 import v6_flag
    return v6_flag(tot_step(code, 3, 1))


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"),) * 3
    p = k / n
    d = 1 + z * z / n
    m = (p + z * z / (2 * n)) / d
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return p, m - h, m + h


def score():
    from concurrent.futures import ProcessPoolExecutor
    codes = json.load(open("v8test_codes.json"))
    lab = json.load(open("v8test_labels.json"))
    with ProcessPoolExecutor() as ex:
        flags = list(ex.map(run, codes))
    json.dump(flags, open("v8test_flags.json", "w"))
    tp = fp = fn = tn = ctp = cfn = 0
    for i, f in enumerate(flags):
        l = lab[str(i)]
        print(i, codes[i], "FLAG" if f else "    ", l)
        if l == "unclear":
            continue
        y = l in ("simple", "complex")
        tp += f and y; fp += f and not y; fn += (not f) and y; tn += (not f) and not y
        if l == "complex":
            ctp += f; cfn += not f
    print(dict(tp=tp, fp=fp, fn=fn, tn=tn, complex_caught=ctp, complex_missed=cfn))
    for name, k, n in (("precision", tp, tp + fp), ("recall", tp, tp + fn),
                       ("complex recall", ctp, ctp + cfn)):
        p = wilson(k, n)
        print(f"{name} {p[0]:.2f} [{p[1]:.2f}, {p[2]:.2f}]  (n={n})")


if __name__ == "__main__":
    {"render": render, "score": score}[sys.argv[1]]()

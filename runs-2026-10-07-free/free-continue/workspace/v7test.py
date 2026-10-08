#!/usr/bin/env python3
"""Attempt 8: label-first test. `render` writes pictures; `score` runs v6 afterwards."""
import json
import os
import random
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

R = 3


def r3_step(bits):
    t = np.array([(bits >> i) & 1 for i in range(2 ** (2 * R + 1))], dtype=np.uint8)
    def step(c):
        idx = sum(np.roll(c, j).astype(np.intp) << (R - j) for j in range(-R, R + 1))
        return t[idx]
    return 2, step


def make_rules():
    rng = random.Random(2030)
    out = []
    for _ in range(60):
        lam = rng.uniform(0, 0.5)
        out.append(sum(1 << i for i in range(1, 128) if rng.random() < lam))
    return out


def render():
    rules = make_rules()
    json.dump(rules, open("v7test_rules.json", "w"))
    with open("v7test_panel.txt", "w") as f:
        for i, b in enumerate(rules):
            _, step = r3_step(b)
            c = np.random.default_rng(99).integers(0, 2, 1001, dtype=np.uint8)
            f.write(f"--- item {i}\n")
            t = 0
            for start in (100, 1600):
                while t < start:
                    c = step(c); t += 1
                f.write(f"(t={start})\n")
                for _ in range(10):
                    f.write("".join("·█"[v] for v in c[:120]) + "\n")
                    c = step(c); t += 1


def run(b):
    from v6 import v6_flag
    return v6_flag(r3_step(b))


def score():
    from concurrent.futures import ProcessPoolExecutor
    rules = json.load(open("v7test_rules.json"))
    lab = json.load(open("v7test_labels.json"))
    with ProcessPoolExecutor() as ex:
        flags = list(ex.map(run, rules))
    json.dump(flags, open("v7test_flags.json", "w"))
    c = {"tp": 0, "fp": 0, "fn": 0, "tn": 0, "unclear_flagged": 0, "unclear": 0}
    for i, f in enumerate(flags):
        l = lab[str(i)]
        print(i, "FLAG" if f else "    ", l)
        if l == "unclear":
            c["unclear"] += 1; c["unclear_flagged"] += f; continue
        y = l == "yes"
        c[("t" if f == y else "f") + ("p" if f else "n")] += 1
    print(c)

    def wilson(k, n, z=1.96):
        if n == 0:
            return (float("nan"),) * 3
        p = k / n
        d = 1 + z * z / n
        m = (p + z * z / (2 * n)) / d
        h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
        return p, m - h, m + h
    p = wilson(c["tp"], c["tp"] + c["fp"])
    r = wilson(c["tp"], c["tp"] + c["fn"])
    print(f"precision {p[0]:.2f} [{p[1]:.2f}, {p[2]:.2f}]   recall {r[0]:.2f} [{r[1]:.2f}, {r[2]:.2f}]")


if __name__ == "__main__":
    {"render": render, "score": score}[sys.argv[1]]()

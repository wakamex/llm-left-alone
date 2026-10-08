#!/usr/bin/env python3
"""Run v3 features on every rule used so far (development set, not a test)."""
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from v2 import eca_step, summary, tot_step
from v2test import r2_step
from v3 import features, flagged


def job(args):
    name, kind, r = args
    ks = {"eca": lambda: eca_step(r), "tot2": lambda: tot_step(r, 2, 2),
          "k3": lambda: tot_step(r, 3, 1), "r2": lambda: r2_step(r)}[kind]()
    d, c = features(ks)
    return name, flagged(d, c), summary(d, c)


def main():
    key = json.load(open("v2test_key.json"))["panel"]
    lab = json.load(open("v2test_labels.json"))
    jobs = [(f"eca {r}", "eca", r) for r in (4, 18, 30, 54, 110, 184)] + \
           [(f"tot2 {r}", "tot2", r) for r in (2, 20, 52)] + \
           [(f"k3 {r}", "k3", r) for r in (148, 914, 1599, 1636)] + \
           [(f"panel {i} [{lab[str(i)]}]", "r2", b) for i, (b, _) in enumerate(key)]
    with ProcessPoolExecutor() as ex:
        for name, f, s in ex.map(job, jobs):
            print(f"{name:20s} {'FLAG' if f else '    '} {s}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""v6 on ALL development data: known rules + three blind panels (no longer test data)."""
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from v2 import eca_step, tot_step
from v2test import r2_step
from v3test import k3_step
from v5test import k4_step
from v6 import v6_flag


def job(args):
    name, kind, r = args
    ks = {"eca": lambda: eca_step(r), "tot2": lambda: tot_step(r, 2, 2),
          "k3": lambda: tot_step(r, 3, 1), "r2": lambda: r2_step(r),
          "g3": lambda: k3_step(tuple(r)), "k4": lambda: k4_step(tuple(r))}[kind]()
    return name, v6_flag(ks)


def main():
    jobs = [(f"eca {r}", "eca", r) for r in (4, 18, 30, 54, 90, 110, 184)] + \
           [(f"tot2 {r}", "tot2", r) for r in (2, 17, 20, 28, 52)] + \
           [(f"k3 {r}", "k3", r) for r in (148, 914, 1599, 1636)]
    for tag, kind, kf, lf in (("p2", "r2", "v2test_key.json", "v2test_labels.json"),
                              ("p3", "g3", "v3test_key.json", "v3test_labels.json"),
                              ("p5", "k4", "v5test_key.json", "v5test_labels.json")):
        key, lab = json.load(open(kf))["panel"], json.load(open(lf))
        jobs += [(f"{tag}-{i} [{lab[str(i)]}]", kind, r) for i, (r, _) in enumerate(key)]
    tally = {}
    flagged_known = []
    with ProcessPoolExecutor() as ex:
        for name, f in ex.map(job, jobs):
            if "[" in name:
                l = name.split("[")[1].rstrip("]")
                tally[(l, f)] = tally.get((l, f), 0) + 1
                if (l == "no" and f) or (l == "yes" and not f):
                    print("  wrong:", name, "FLAG" if f else "miss")
            elif f:
                flagged_known.append(name)
    print("known rules flagged:", flagged_known)
    print("panel tally (label, flagged) -> count:", dict(sorted(tally.items())))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""v4 on all development data: known rules + both blind panels (no longer test data)."""
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import v4  # noqa: F401  (sets v3 parameters)
from v2 import eca_step, summary, tot_step
from v2test import r2_step
from v3test import k3_step
from v4 import features, flagged


def job(args):
    import v4  # noqa: F401  re-apply settings in worker
    name, kind, r = args
    ks = {"eca": lambda: eca_step(r), "tot2": lambda: tot_step(r, 2, 2),
          "k3": lambda: tot_step(r, 3, 1), "r2": lambda: r2_step(r),
          "g3": lambda: k3_step(tuple(r))}[kind]()
    d, c = features(ks)
    return name, flagged(d, c), summary(d, c)


def main():
    jobs = [(f"eca {r}", "eca", r) for r in (4, 18, 30, 54, 90, 110, 184)] + \
           [(f"tot2 {r}", "tot2", r) for r in (2, 17, 20, 28, 52)] + \
           [(f"k3 {r}", "k3", r) for r in (148, 914, 1599, 1636)]
    for tag, kind, kf, lf in (("p2", "r2", "v2test_key.json", "v2test_labels.json"),
                              ("p3", "g3", "v3test_key.json", "v3test_labels.json")):
        key, lab = json.load(open(kf))["panel"], json.load(open(lf))
        jobs += [(f"{tag}-{i} [{lab[str(i)]}]", kind, r) for i, (r, _) in enumerate(key)]
    tally = {}
    with ProcessPoolExecutor() as ex:
        for name, f, s in ex.map(job, jobs):
            print(f"{name:18s} {'FLAG' if f else '    '} {s}")
            if "[" in name:
                l = name.split("[")[1].rstrip("]")
                tally[(l, f)] = tally.get((l, f), 0) + 1
    print("panel tally (label, flagged): count ->", dict(sorted(tally.items())))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Version 2 features: defect density on a log time scale + defect cluster tracking.

For each checkpoint t in 100 * 4^k (k = 0..4), take a 64-step window, filter the
background (best shift q <= 8), and label connected defect clusters. For clusters
that last the whole window, record:
  width : mean spatial extent (cells)
  growth: extent in last rows minus extent in first rows (fronts grow)
  speed : |drift of cluster centre| per step (gliders move, walls don't)
"""
import os
import sys

import numpy as np
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from glider import best_symmetry, defects

CHECKPOINTS = (100, 400, 1600, 6400, 25600)
WIDTH, WINDOW, SEEDS = 1001, 64, 3


def eca_step(rule):
    t = np.array([(rule >> i) & 1 for i in range(8)], dtype=np.uint8)
    return 2, lambda c: t[(np.roll(c, 1) << 2) | (c << 1) | np.roll(c, -1)]


def tot_step(code, k, r):
    t = np.array([(code // k**s) % k for s in range((2 * r + 1) * (k - 1) + 1)],
                 dtype=np.uint8)
    return k, lambda c: t[sum(np.roll(c, j) for j in range(-r, r + 1)).astype(np.intp)]


def clusters(D):
    """Stats for defect clusters that persist through the whole window."""
    lab, n = ndimage.label(ndimage.binary_dilation(D, np.ones((1, 3))),
                           structure=np.ones((3, 3)))
    lab = lab * D  # keep labels only on real defect cells
    out = []
    for i, sl in enumerate(ndimage.find_objects(lab), start=1):
        if sl is None or sl[0].start > 0 or sl[0].stop < D.shape[0]:
            continue
        m = lab[sl] == i
        xs = [np.nonzero(row)[0] for row in m]
        ok = [x for x in xs if len(x)]
        if len(ok) < D.shape[0] // 2:
            continue
        ext = np.array([x.max() - x.min() + 1 for x in ok])
        cen = np.array([x.mean() for x in ok]) + sl[1].start
        h = max(1, len(ok) // 8)
        out.append((ext.mean(), ext[-h:].mean() - ext[:h].mean(),
                    abs(cen[-h:].mean() - cen[:h].mean()) / len(ok)))
    return out


def features(kind_step):
    k, step = kind_step
    dens = np.zeros(len(CHECKPOINTS))
    cl = [[] for _ in CHECKPOINTS]
    for seed in range(SEEDS):
        c = np.random.default_rng(seed).integers(0, k, WIDTH, dtype=np.uint8)
        t = 0
        for i, cp in enumerate(CHECKPOINTS):
            for _ in range(cp - t):
                c = step(c)
            rows = []
            for _ in range(WINDOW):
                rows.append(c)
                c = step(c)
            t = cp + WINDOW
            S = np.array(rows)
            _, q, d = best_symmetry(S, max_q=8)
            D = defects(S, q, d)
            dens[i] += D.mean() / SEEDS
            cl[i] += clusters(D)
    return dens, cl


def summary(dens, cl):
    s = " ".join(f"{v:.3f}" for v in dens)
    # cluster stats at the last checkpoint that still has persistent clusters
    for i in reversed(range(len(cl))):
        if cl[i]:
            a = np.array(cl[i])
            return (f"{s} | t={CHECKPOINTS[i]:<5d} n={len(a):3d} "
                    f"width med {np.median(a[:,0]):6.1f} growth med {np.median(a[:,1]):6.1f} "
                    f"moving {np.mean(a[:,2] > 0.05):.2f}")
    return s + " | no persistent clusters"


if __name__ == "__main__":
    dev = [("eca", r, eca_step(r)) for r in (4, 184, 18, 30, 54, 110)] + \
          [("tot2", c, tot_step(c, 2, 2)) for c in (2, 17, 20, 28, 52)] + \
          [("k3", c, tot_step(c, 3, 1)) for c in (148, 914, 1394, 1636, 1599)]
    print("rule        densities t=100..25600       | clusters")
    for kind, r, ks in dev:
        print(f"{kind:4s} {r:5d}  " + summary(*features(ks)))

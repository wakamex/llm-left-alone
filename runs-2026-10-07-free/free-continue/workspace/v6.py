#!/usr/bin/env python3
"""Version 6: v5 (both background scales) + front rejection.

A persistent defect cluster only counts as a particle if the background on its left
and on its right is the same pattern, up to a spatial shift and up to TPHASE time steps
of phase. Otherwise it is a front between two different backgrounds and is ignored.
"""
import os
import sys

import numpy as np
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import v3
from v2 import CHECKPOINTS, SEEDS, WIDTH, WINDOW

SIDE, TPHASE = 12, 8


def same_background(S, t, left, right):
    """Left segment at row t vs right segment at rows t..t+TPHASE, any spatial shift."""
    n = S.shape[1]
    a = S[t, [(left - SIDE + i) % n for i in range(SIDE)]]
    if len(set(a.tolist())) == 0:
        return False
    tile = np.concatenate([a, a, a])  # periodic extension of left background
    for dt in range(0, TPHASE + 1):
        if t + dt >= S.shape[0]:
            break
        b = S[t + dt, [(right + 1 + i) % n for i in range(SIDE)]]
        for s in range(SIDE):
            if np.array_equal(tile[s:s + SIDE], b):
                return True
    return False


def particle_clusters(S, D):
    """Like v2.clusters but drops fronts. Returns (width, growth, speed) per particle."""
    lab, _ = ndimage.label(ndimage.binary_dilation(D, np.ones((1, 3))),
                           structure=np.ones((3, 3)))
    lab = lab * D
    out = []
    T = D.shape[0]
    t_check = T // 2 - TPHASE
    for i, sl in enumerate(ndimage.find_objects(lab), start=1):
        if sl is None or sl[0].start > 0 or sl[0].stop < T:
            continue
        m = lab[sl] == i
        xs = [np.nonzero(row)[0] for row in m]
        ok = [x for x in xs if len(x)]
        if len(ok) < T // 2:
            continue
        row = xs[t_check]
        if not len(row):
            continue
        left, right = sl[1].start + row.min(), sl[1].start + row.max()
        if not same_background(S, t_check, left, right):
            continue
        ext = np.array([x.max() - x.min() + 1 for x in ok])
        cen = np.array([x.mean() for x in ok]) + sl[1].start
        h = max(1, len(ok) // 8)
        out.append((ext.mean(), ext[-h:].mean() - ext[:h].mean(),
                    abs(cen[-h:].mean() - cen[:h].mean()) / len(ok)))
    return out


def features_scale(kind_step, lmin, reps, seeds=SEEDS):
    v3.LMIN, v3.REPS = lmin, reps
    k, step = kind_step
    dens = np.zeros(len(CHECKPOINTS))
    cl = [[] for _ in CHECKPOINTS]
    for seed in range(seeds):
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
            D = v3.local_defects(S)
            dens[i] += D.mean() / seeds
            cl[i] += particle_clusters(S, D)
    v3.LMIN, v3.REPS = None, None
    return dens, cl


def v6_flag(kind_step):
    return (v3.flagged(*features_scale(kind_step, None, None)) or
            v3.flagged(*features_scale(kind_step, 4, 3)))

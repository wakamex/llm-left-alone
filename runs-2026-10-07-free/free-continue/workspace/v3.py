#!/usr/bin/env python3
"""Version 3: local background filter.

A cell (t, x) is background if some row segment of length 2W+1 containing it is
periodic with some period p <= P. Everything else is a defect. No global shift, so particles that all move
at the same speed are still defects. Then the cluster/density features from v2.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from v2 import CHECKPOINTS, WIDTH, WINDOW, SEEDS, clusters

P, W = 16, 16
LMIN, REPS = None, None  # v4 sets these: segment length L(p) = max(LMIN, REPS * p)


def local_defects(S):
    """Background = covered by SOME length-L segment that is periodic with p <= P."""
    T, n = S.shape
    domain = np.zeros(S.shape, dtype=bool)

    def window_sum(a, span):
        # out[s] = a[s] + ... + a[s+span-1] (periodic)
        cs = np.concatenate([np.zeros((T, 1), np.int32),
                             np.cumsum(np.concatenate([a, a[:, :span]], axis=1), axis=1)], axis=1)
        return cs[:, span:span + n] - cs[:, :n]

    for p in range(1, P + 1):
        L = 2 * W + 1 if LMIN is None else max(LMIN, REPS * p)
        bad = (S != np.roll(S, -p, axis=1)).astype(np.int32)   # bad[x]: S[x] != S[x+p]
        ok = (window_sum(bad, L - p) == 0).astype(np.int32)    # segment starting at s periodic
        # x covered if some s in [x-L+1, x] has ok[s]
        covered = window_sum(np.roll(ok, L - 1, axis=1), L) > 0
        domain |= covered
    return ~domain


def features(kind_step, seeds=SEEDS):
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
            D = local_defects(np.array(rows))
            dens[i] += D.mean() / seeds
            cl[i] += clusters(D)
    return dens, cl


def flagged(dens, cl):
    """Same frozen rule as v2test.flagged."""
    for d, c in zip(dens, cl):
        if 0 < d <= 0.2 and len(c) >= 2:
            a = np.array(c)
            if np.median(a[:, 0]) <= 30 and np.mean(a[:, 2] > 0.05) >= 0.5:
                return True
    return False

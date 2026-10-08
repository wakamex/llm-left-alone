#!/usr/bin/env python3
"""Census v2: spaceships reaching the edge band are counted and deleted (no wrap-around
crashes), and each soup runs until settled (state at t equals state at t-60), max 6000."""
import os
import pickle
import sys
from collections import Counter
from concurrent.futures import ProcessPoolExecutor

import numpy as np
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from census import classify, step

N, SOUP, BAND, MAXG, CHECK = 256, 16, 12, 6000, 60
SPLIT = True


def objects(g):
    lab, _ = ndimage.label(ndimage.binary_dilation(g, np.ones((3, 3))), np.ones((3, 3)))
    lab = lab * g
    for i, sl in enumerate(ndimage.find_objects(lab), start=1):
        if sl is not None:
            yield sl, (lab[sl] == i).astype(np.uint8)


def reap_edge(g, escaped):
    """Classify objects touching the edge band; count+delete spaceships."""
    edge = np.ones_like(g, bool)
    edge[BAND:-BAND, BAND:-BAND] = False
    if not (g.astype(bool) & edge).any():
        return
    for sl, obj in objects(g):
        if not edge[sl].any():
            continue
        r = classify(obj)
        if r and r[0] == "spaceship":
            escaped[(r[0], r[1], r[2])] += 1
            g[sl][obj.astype(bool)] = 0


def evolve(a, gens):
    for _ in range(gens):
        a = step(a)
    return a


def split_pseudo(obj):
    """Split a cluster into 8-connected pieces if the pieces don't interact."""
    lab, n = ndimage.label(obj, np.ones((3, 3)))
    if n <= 1:
        return [obj]
    pad = 70
    whole = evolve(np.pad(obj, pad), CHECK)
    parts = [np.pad((lab == i).astype(np.uint8), pad) for i in range(1, n + 1)]
    union = np.zeros_like(whole)
    for q in parts:
        union |= evolve(q, CHECK)
    if not np.array_equal(whole, union):
        return [obj]
    out = []
    for i in range(1, n + 1):
        sl = ndimage.find_objects((lab == i).astype(int))[0]
        out.append((lab[sl] == i).astype(np.uint8))
    return out


def run_soup(seed):
    rng = np.random.default_rng(seed)
    g = np.zeros((N, N), np.uint8)
    o = N // 2 - SOUP // 2
    g[o:o + SOUP, o:o + SOUP] = rng.random((SOUP, SOUP)) < 0.5
    escaped = Counter()
    hist = None
    t = 0
    settled = False
    while t < MAXG:
        for _ in range(CHECK):
            g = step(g)
        t += CHECK
        reap_edge(g, escaped)
        if hist is not None and np.array_equal(g, hist):
            settled = True
            break
        hist = g.copy()
    out = Counter(escaped)
    for _, obj in objects(g):
        for piece in (split_pseudo(obj) if SPLIT else [obj]):
            r = classify(piece)
            out[r if r else ("unresolved", 0, None)] += 1
    return settled, t, out


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    with ProcessPoolExecutor() as ex:
        res = list(ex.map(run_soup, range(n), chunksize=8))
    counts = Counter()
    for _, _, c in res:
        counts.update(c)
    unsettled = sum(not s for s, _, _ in res)
    print(f"{n} soups; unsettled after {MAXG}: {unsettled}; "
          f"median settle time {int(np.median([t for _, t, _ in res]))}")
    pickle.dump((n, counts), open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                               "census2.pkl"), "wb"))
    from names import build
    names = build()
    for (kind, p, key), c in counts.most_common(15):
        name = names.get((kind, p, key), "?") if key else "unresolved"
        print(f"{c / n:7.3f}/soup  {name:14s} {kind} p{p}")


if __name__ == "__main__":
    main()

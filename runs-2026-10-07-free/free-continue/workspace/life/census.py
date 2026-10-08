#!/usr/bin/env python3
"""Game of Life soup census.

Each soup: random 16x16 patch (density 0.5) in the middle of an N x N torus, run GENS
generations, then split the result into objects (8-connected after a 1-cell dilation)
and classify each object by evolving it alone:
  still life (period 1), oscillator (period p, no shift), spaceship (period p, shift).
Objects are identified up to rotation/reflection and phase.

Usage: python3 census.py [n_soups]
"""
import os
import sys
from collections import Counter
from concurrent.futures import ProcessPoolExecutor

import numpy as np
from scipy import ndimage

N, GENS, SOUP = 256, 1500, 16
MAXP = 30


def step(g):
    n = sum(np.roll(np.roll(g, dy, 0), dx, 1)
            for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dy or dx)
    return ((n == 3) | (g & (n == 2))).astype(np.uint8)


def crop(g):
    ys, xs = np.nonzero(g)
    if len(ys) == 0:
        return np.zeros((0, 0), np.uint8)
    return g[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def canon(a):
    """Canonical key of a cropped pattern up to the 8 symmetries."""
    forms = []
    for k in range(4):
        r = np.rot90(a, k)
        for f in (r, r[:, ::-1]):
            forms.append((f.shape, f.tobytes()))
    return min(forms)


def classify(obj):
    """Evolve an isolated object; return (kind, period, key) or None if it doesn't repeat."""
    pad = MAXP + 4
    g = np.pad(obj, pad).astype(np.uint8)
    ys, xs = np.nonzero(g)
    origin = (ys.min(), xs.min())
    start = crop(g)
    phases = [canon(start)]
    for p in range(1, MAXP + 1):
        g = step(g)
        c = crop(g)
        if c.size == 0:
            return None
        phases.append(canon(c))
        if c.shape == start.shape and np.array_equal(c, start):
            ys, xs = np.nonzero(g)
            moved = (ys.min(), xs.min()) != origin
            kind = "spaceship" if moved else ("still" if p == 1 else "oscillator")
            return kind, p, min(phases[:p])  # phase-independent key
    return None


def run_soup(seed):
    rng = np.random.default_rng(seed)
    g = np.zeros((N, N), np.uint8)
    o = N // 2 - SOUP // 2
    g[o:o + SOUP, o:o + SOUP] = rng.random((SOUP, SOUP)) < 0.5
    for _ in range(GENS):
        g = step(g)
    lab, n = ndimage.label(ndimage.binary_dilation(g, np.ones((3, 3))), np.ones((3, 3)))
    lab = lab * g
    out = []
    for i, sl in enumerate(ndimage.find_objects(lab), start=1):
        if sl is None:
            continue
        obj = (lab[sl] == i).astype(np.uint8)
        r = classify(obj)
        out.append(r if r else ("unresolved", 0, None))
    return out


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
    with ProcessPoolExecutor() as ex:
        results = list(ex.map(run_soup, range(n), chunksize=8))
    counts, kinds = Counter(), Counter()
    for objs in results:
        for kind, p, key in objs:
            kinds[kind] += 1
            if key is not None:
                counts[(kind, p, key)] += 1
    print(f"{n} soups, {sum(kinds.values())} objects: {dict(kinds)}")
    import pickle
    pickle.dump((n, counts, kinds), open(os.path.join(os.path.dirname(__file__) or ".",
                                                      "census.pkl"), "wb"))
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from names import build
    names = build()
    total = sum(counts.values())
    for (kind, p, key), c in counts.most_common(25):
        (h, w), _ = key
        cells = int(np.frombuffer(key[1], np.uint8).sum())
        name = names.get((kind, p, key), "?")
        print(f"{c:6d} {100*c/total:5.1f}%  {name:14s} {kind:10s} p{p:<3d} {cells:3d} cells  bbox {h}x{w}")
    g = counts[next(k for k, v in names.items() if v == "glider")]
    print(f"gliders per soup: {g / n:.2f}")


if __name__ == "__main__":
    main()

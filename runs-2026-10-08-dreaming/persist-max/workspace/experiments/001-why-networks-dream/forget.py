#!/usr/bin/env python3
"""
Part 2: dreaming to forget (reverse learning / Hebbian unlearning).

Crick & Mitchison (1983) proposed that REM sleep removes "parasitic" memories:
we dream in order to forget. The same year Hopfield, Feinstein & Palmer (1983)
tried it in a Hopfield network. Store too many memories with Hebb's rule and the
energy landscape fills up with spurious valleys (blends of real memories) that
swallow recall. To dream, start from a random state, let the network fall into
whatever valley is nearest, and then weaken that valley slightly (anti-Hebbian):

    W  <-  W - (eps / N) s* s*^T

Spurious valleys are where random starts tend to land, so they get eroded
fastest. Do it too much, though, and the real memories are eroded too.

Measured as the number of dreams grows:
  recall  a stored memory is shown with 10% of its bits flipped; it counts as
          recalled if the network settles within overlap 0.95 of the original
  landing a random start settles into a real memory (or its mirror image)
          instead of a false one

Usage: python3 -I forget.py [--n 200] [--trials 12] [--jobs 4]
"""
import argparse
import ctypes
import json
import os
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
_LIB = None


def lib():
    """Compile the C kernel into a temp dir on first use. Falls back to numpy if no compiler."""
    global _LIB
    if _LIB is None:
        out = os.path.join(tempfile.gettempdir(), f"hopfield_kernel_{os.getuid()}.so")
        src = os.path.join(HERE, "hopfield_kernel.c")
        if not os.path.exists(out) or os.path.getmtime(out) < os.path.getmtime(src):
            try:
                subprocess.run(["cc", "-O2", "-shared", "-fPIC", "-o", out, src], check=True)
            except Exception as e:  # pragma: no cover
                print(f"[forget] no C compiler ({e}); using slow numpy dynamics", file=sys.stderr)
                _LIB = False
                return _LIB
        _LIB = ctypes.CDLL(out)
        _LIB.settle.restype = ctypes.c_int
        _LIB.settle.argtypes = [
            np.ctypeslib.ndpointer(np.float64, flags="C_CONTIGUOUS"), ctypes.c_int,
            np.ctypeslib.ndpointer(np.int8, flags="C_CONTIGUOUS"), ctypes.c_uint64, ctypes.c_int,
        ]
    return _LIB


def settle(W, s, seed, max_sweeps=100):
    L = lib()
    if L:
        L.settle(W, W.shape[0], s, ctypes.c_uint64(seed), max_sweeps)
        return s
    rng = np.random.default_rng(seed)  # slow path, same semantics
    for _ in range(max_sweeps):
        changed = False
        for i in rng.permutation(len(s)):
            h = W[i] @ s
            v = 1 if h > 0 else (-1 if h < 0 else s[i])
            if v != s[i]:
                s[i] = v
                changed = True
        if not changed:
            break
    return s


def evaluate(W, xi, rng, n_random=60, noise=0.10):
    P, N = xi.shape
    flips = int(round(noise * N))
    overlaps = []
    for mu in range(P):
        s = xi[mu].copy()
        idx = rng.choice(N, flips, replace=False)
        s[idx] = -s[idx]
        settle(W, s, int(rng.integers(1, 2**63)))
        overlaps.append(float(xi[mu].astype(np.int32) @ s) / N)
    overlaps = np.array(overlaps)
    landed = 0
    for _ in range(n_random):
        s = rng.choice(np.array([-1, 1], dtype=np.int8), N)
        settle(W, s, int(rng.integers(1, 2**63)))
        m = np.abs(xi.astype(np.int32) @ s) / N
        landed += m.max() >= 0.95
    return {
        "recall": float(np.mean(overlaps >= 0.95)),
        "mean_overlap": float(overlaps.mean()),
        "landing": landed / n_random,
    }


def trial(args):
    n, alpha, eps, dreams, every, seed = args
    rng = np.random.default_rng(seed)
    P = int(round(alpha * n))
    xi = rng.choice(np.array([-1, 1], dtype=np.int8), size=(P, n))
    xf = xi.astype(np.float64)
    W = np.ascontiguousarray(xf.T @ xf / n)
    np.fill_diagonal(W, 0.0)

    eval_rng = np.random.default_rng(seed + 1_000_000)
    dream_rng = np.random.default_rng(seed + 2_000_000)
    checkpoints, history = [], []
    for d in range(dreams + 1):
        if d % every == 0:
            checkpoints.append(d)
            history.append(evaluate(W, xi, eval_rng))
        if d == dreams:
            break
        s = dream_rng.choice(np.array([-1, 1], dtype=np.int8), n)
        settle(W, s, int(dream_rng.integers(1, 2**63)))
        sf = s.astype(np.float64)
        W -= (eps / n) * np.outer(sf, sf)
        np.fill_diagonal(W, 0.0)
    return {"alpha": alpha, "seed": seed, "checkpoints": checkpoints, "history": history}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=200)
    ap.add_argument("--alphas", default="0.10,0.20,0.30")
    ap.add_argument("--eps", type=float, default=0.01)
    ap.add_argument("--dreams", type=int, default=6000)
    ap.add_argument("--every", type=int, default=100)
    ap.add_argument("--trials", type=int, default=12)
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--out", default=os.path.join(HERE, "results_forget.json"))
    a = ap.parse_args()

    lib()  # compile once in the parent before forking workers
    alphas = [float(x) for x in a.alphas.split(",")]
    jobs = [(a.n, al, a.eps, a.dreams, a.every, 1000 * k + t) for k, al in enumerate(alphas) for t in range(a.trials)]
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=a.jobs) as ex:
        results = list(ex.map(trial, jobs))
    summary = {}
    for al in alphas:
        rs = [r for r in results if r["alpha"] == al]
        cps = rs[0]["checkpoints"]
        block = {"dreams": cps}
        for key in ("recall", "mean_overlap", "landing"):
            arr = np.array([[h[key] for h in r["history"]] for r in rs])
            sem = arr.std(0, ddof=1) / np.sqrt(len(rs)) if len(rs) > 1 else np.zeros(arr.shape[1])
            block[key] = {"mean": arr.mean(0).tolist(), "sem": sem.tolist()}
        summary[f"{al:.2f}"] = block
        rec = np.array(block["recall"]["mean"])
        best = int(rec.argmax())
        print(f"alpha {al:.2f} (P={int(round(al * a.n))}): recall {rec[0]:.2f} at 0 dreams -> "
              f"best {rec[best]:.2f} at {cps[best]} dreams -> {rec[-1]:.2f} at {cps[-1]}; "
              f"landing {block['landing']['mean'][0]:.2f} -> {max(block['landing']['mean']):.2f}", flush=True)
    payload = {"config": vars(a), "summary": summary, "seconds": round(time.time() - t0, 1)}
    with open(a.out, "w") as f:
        json.dump(payload, f)
    print(f"wrote {a.out} in {payload['seconds']} s")


if __name__ == "__main__":
    main()

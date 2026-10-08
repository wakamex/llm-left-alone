#!/usr/bin/env python3
"""
002: Do dreams of dreams degrade?

The same curve as experiment 001 is split into six segments, learned on six consecutive days.
Each night the network can rehearse earlier days:

  none     nothing
  focused  its *own* answers at inputs drawn from a histogram of all past inputs. From day 3 on,
           those answers come from a network that was itself kept alive by earlier dreams:
           a copy of a copy.
  replay   stored real examples from every past day (the reference)

Question: does day 1's memory drift as the dreams compound, or does it hold?

Usage: python3 -I run.py [--seeds 8] [--jobs 6]
"""
import argparse
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "001-why-networks-dream"))
from nn import Adam, backward, copy_params, forward, init_mlp  # noqa: E402

PI = np.pi
DAYS = int(os.environ.get("DREAM_DAYS", "6"))  # set by --days before workers start
EDGES = np.linspace(-PI, PI, DAYS + 1)
N_PER_DAY, N_DREAMS, STEPS, BATCH, LR = 256, 512, 3000, 64, 3e-3
GRIDS = [np.linspace(EDGES[k], EDGES[k + 1], 101)[:, None] for k in range(DAYS)]


def world(x):
    return np.sin(2.2 * x) + 0.35 * np.sin(5.3 * x + 0.4)


def net(p, x):
    return forward(p, x / PI)[0]


def mse(p, x):
    return float(np.mean((net(p, x) - world(x)) ** 2))


def step(p, opt, xs, ys):
    total = None
    for x, y in zip(xs, ys):
        out, acts = forward(p, x / PI)
        g = backward(p, acts, 2.0 * (out - y) / len(x))
        total = g if total is None else [a + b for a, b in zip(total, g)]
    opt.step(p, total)


def run(seed):
    rng = np.random.default_rng(seed)
    init = init_mlp(rng, [1, 64, 64, 1])
    data = []
    for k in range(DAYS):
        x = rng.uniform(EDGES[k], EDGES[k + 1], (N_PER_DAY, 1))
        data.append((x, world(x)))
    out = {}
    for cond in ("none", "focused", "replay"):
        p = copy_params(init)
        crng = np.random.default_rng(seed + 777)
        # err[d][k]: error on segment k at the end of day d
        err = []
        for d in range(DAYS):
            xd, yd = data[d]
            if d > 0 and cond == "focused":
                past = np.concatenate([data[k][0] for k in range(d)])
                hist, _ = np.histogram(past[:, 0], bins=48, range=(-PI, PI))
                edges = np.linspace(-PI, PI, 49)
                which = crng.choice(48, N_DREAMS, p=hist / hist.sum())
                rx = crng.uniform(edges[which], edges[which + 1])[:, None]
                ry = net(p, rx)  # tonight's dreams come from the network as it is now
            elif d > 0 and cond == "replay":
                rx = np.concatenate([data[k][0] for k in range(d)])
                ry = world(rx)
            opt = Adam(p, lr=LR)
            for _ in range(STEPS):
                i = crng.integers(0, N_PER_DAY, BATCH)
                if d == 0 or cond == "none":
                    step(p, opt, [xd[i]], [yd[i]])
                else:
                    j = crng.integers(0, len(rx), BATCH)
                    step(p, opt, [xd[i], rx[j]], [yd[i], ry[j]])
            err.append([mse(p, g) for g in GRIDS])
        out[cond] = err
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=8)
    ap.add_argument("--jobs", type=int, default=6)
    ap.add_argument("--days", type=int, default=6)
    ap.add_argument("--out", default="results.json")
    a = ap.parse_args()
    if a.days != DAYS:  # re-exec so worker processes see the same DAYS
        os.environ["DREAM_DAYS"] = str(a.days)
        os.execv(sys.executable, [sys.executable, "-I", os.path.abspath(__file__)] + sys.argv[1:])
    with ProcessPoolExecutor(max_workers=a.jobs) as ex:
        runs = list(ex.map(run, range(a.seeds)))
    summary = {}
    for cond in ("none", "focused", "replay"):
        arr = np.array([r[cond] for r in runs])  # seeds x day x segment
        summary[cond] = np.exp(np.log(arr).mean(0)).tolist()  # geometric mean over seeds
    json.dump({"config": vars(a), "summary": summary, "runs": runs},
              open(os.path.join(HERE, a.out), "w"))
    for cond, m in summary.items():
        m = np.array(m)
        print(f"\n{cond}: error on day-1 segment after each day: " + " ".join(f"{v:.2g}" for v in m[:, 0]))
        print(f"{cond}: error on each segment after the last day: " + " ".join(f"{v:.2g}" for v in m[-1]))


if __name__ == "__main__":
    main()

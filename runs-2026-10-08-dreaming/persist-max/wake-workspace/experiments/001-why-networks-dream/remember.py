#!/usr/bin/env python3
"""
Part 1: dreaming to remember (replay / pseudorehearsal).

One world, learned in two halves. Yesterday the network sees only the left half
of a curve (x in [-pi, 0]); today it sees only the right half (x in [0, pi]).
Learning today's half with nothing to protect yesterday's tends to overwrite it.
That's catastrophic interference (McCloskey & Cohen 1989; Ratcliff 1990).

Before today's lesson the network can "dream". In pseudorehearsal (Robins 1995;
proposed as a model of sleep consolidation in Robins 1996) it feeds itself inputs,
writes down its own answers, and then keeps rehearsing those answers while it
learns. It needs none of yesterday's real data, only itself.

Conditions (same post-yesterday network for all four, within each seed):
  none     learn today's half only
  random   dream inputs uniform over the whole sensory range [-pi, pi].
           Classic pseudorehearsal: the dreamer doesn't know where yesterday happened.
  shaped   dream inputs drawn from a 32-bin histogram of yesterday's inputs.
           A crude sense of where experience fell, plus the network's own
           answers for the details (a generative-replay flavour, cf. Shin et al. 2017).
  replay   rehearse 512 stored real examples from yesterday (episodic replay).
           This is the reference the dreams are approximating.

Usage: python3 -I remember.py [--seeds 20] [--jobs 4] [--out results_remember.json]
"""
import argparse
import json
from concurrent.futures import ProcessPoolExecutor
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nn import Adam, backward, copy_params, forward, init_mlp  # noqa: E402

PI = np.pi
SIZES = [1, 64, 64, 1]
N_TRAIN = 512
N_DREAMS = 512
STEPS_A = 4000
STEPS_B = 4000
BATCH = 64
LR = 3e-3
EVAL_EVERY = 25
GRID_A = np.linspace(-PI, 0.0, 201)[:, None]
GRID_B = np.linspace(0.0, PI, 201)[:, None]
GRID_ALL = np.linspace(-PI, PI, 401)[:, None]
CONDITIONS = ["none", "random", "shaped", "replay"]


def world(x):
    """The curve the network is trying to learn. Same world on both days."""
    return np.sin(2.2 * x) + 0.35 * np.sin(5.3 * x + 0.4)


def net(params, x):
    return forward(params, x / PI)  # inputs scaled to [-1, 1]


def mse(params, x):
    y, _ = net(params, x)
    return float(np.mean((y - world(x)) ** 2))


def sgd_step(params, opt, xs, ys, weights):
    """One Adam step on a weighted sum of MSE terms, one term per (x, y) batch."""
    total = None
    for x, y, w in zip(xs, ys, weights):
        out, acts = net(params, x)
        g = backward(params, acts, w * 2.0 * (out - y) / len(x))
        total = g if total is None else [a + b for a, b in zip(total, g)]
    opt.step(params, total)


def sample_shaped(rng, x_seen, n, bins=32):
    """Sample inputs from a histogram of where yesterday's inputs fell."""
    edges = np.linspace(-PI, PI, bins + 1)
    counts, _ = np.histogram(x_seen[:, 0], bins=edges)
    p = counts / counts.sum()
    which = rng.choice(bins, size=n, p=p)
    return rng.uniform(edges[which], edges[which + 1])[:, None]


def run_seed(seed):
    rng = np.random.default_rng(seed)
    params = init_mlp(rng, SIZES)

    # Yesterday: the left half.
    xa = rng.uniform(-PI, 0.0, size=(N_TRAIN, 1))
    ya = world(xa)
    opt = Adam(params, lr=LR)
    for _ in range(STEPS_A):
        i = rng.integers(0, N_TRAIN, BATCH)
        sgd_step(params, opt, [xa[i]], [ya[i]], [1.0])
    after_a = copy_params(params)

    # Today's data: the right half.
    xb = rng.uniform(0.0, PI, size=(N_TRAIN, 1))
    yb = world(xb)

    # The night's dreams, generated once from the post-yesterday network.
    dream_rng = np.random.default_rng(seed + 10_000)
    x_random = dream_rng.uniform(-PI, PI, size=(N_DREAMS, 1))
    x_shaped = sample_shaped(dream_rng, xa, N_DREAMS)
    rehearsal = {
        "random": (x_random, net(after_a, x_random)[0]),
        "shaped": (x_shaped, net(after_a, x_shaped)[0]),
        "replay": (xa, ya),  # real memories, not dreams
    }

    out = {
        "after_yesterday": {"mse_A": mse(after_a, GRID_A), "mse_B": mse(after_a, GRID_B)},
        "curve_after_yesterday": net(after_a, GRID_ALL)[0][:, 0].tolist(),
        "dream_examples": {
            k: {"x": v[0][:96, 0].tolist(), "y": v[1][:96, 0].tolist()}
            for k, v in rehearsal.items() if k != "replay"
        },
    }
    for cond in CONDITIONS:
        p = copy_params(after_a)
        opt = Adam(p, lr=LR)
        crng = np.random.default_rng(seed + 20_000)  # same minibatch stream for every condition
        hist_a, hist_b = [mse(p, GRID_A)], [mse(p, GRID_B)]
        for step in range(1, STEPS_B + 1):
            i = crng.integers(0, N_TRAIN, BATCH)
            if cond == "none":
                sgd_step(p, opt, [xb[i]], [yb[i]], [1.0])
            else:
                xd, yd = rehearsal[cond]
                j = crng.integers(0, len(xd), BATCH)
                sgd_step(p, opt, [xb[i], xd[j]], [yb[i], yd[j]], [1.0, 1.0])
            if step % EVAL_EVERY == 0:
                hist_a.append(mse(p, GRID_A))
                hist_b.append(mse(p, GRID_B))
        out[cond] = {
            "mse_A": hist_a,
            "mse_B": hist_b,
            "curve": net(p, GRID_ALL)[0][:, 0].tolist(),
        }
    return out


def summarize(runs):
    def stats(arr):
        arr = np.asarray(arr)
        mean = arr.mean(axis=0)
        # 95% bootstrap interval of the mean across seeds (geometric data -> use log space)
        rng = np.random.default_rng(0)
        logs = np.log(arr)
        boots = np.array([logs[rng.integers(0, len(arr), len(arr))].mean(axis=0) for _ in range(2000)])
        lo, hi = np.exp(np.percentile(boots, [2.5, 97.5], axis=0))
        gmean = np.exp(logs.mean(axis=0))
        return {"mean": mean.tolist(), "geo_mean": gmean.tolist(), "ci_lo": lo.tolist(), "ci_hi": hi.tolist()}

    s = {"steps": list(range(0, STEPS_B + 1, EVAL_EVERY))}
    s["after_yesterday"] = {
        "mse_A": stats([[r["after_yesterday"]["mse_A"]] for r in runs]),
        "mse_B": stats([[r["after_yesterday"]["mse_B"]] for r in runs]),
    }
    for cond in CONDITIONS:
        s[cond] = {
            "mse_A": stats([r[cond]["mse_A"] for r in runs]),
            "mse_B": stats([r[cond]["mse_B"] for r in runs]),
        }
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=20)
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "results_remember.json"))
    args = ap.parse_args()

    t0 = time.time()
    with ProcessPoolExecutor(max_workers=args.jobs) as ex:
        runs = list(ex.map(run_seed, range(args.seeds)))
    for seed, r in enumerate(runs):
        print(f"seed {seed:2d}  A-err after yesterday {r['after_yesterday']['mse_A']:.4f}  | after today: "
              + "  ".join(f"{c}: A {r[c]['mse_A'][-1]:.4f} B {r[c]['mse_B'][-1]:.4f}" for c in CONDITIONS),
              flush=True)
    summary = summarize(runs)
    example = runs[0]
    payload = {
        "config": {"sizes": SIZES, "n_train": N_TRAIN, "n_dreams": N_DREAMS, "steps_a": STEPS_A,
                   "steps_b": STEPS_B, "batch": BATCH, "lr": LR, "seeds": args.seeds,
                   "world": "sin(2.2x) + 0.35 sin(5.3x + 0.4), x in [-pi, pi]"},
        "summary": summary,
        "final": {c: {"mse_A": [r[c]["mse_A"][-1] for r in runs], "mse_B": [r[c]["mse_B"][-1] for r in runs]}
                  for c in CONDITIONS},
        "example_seed0": {
            "grid": GRID_ALL[:, 0].tolist(),
            "world": world(GRID_ALL)[:, 0].tolist(),
            "after_yesterday": example["curve_after_yesterday"],
            **{c: example[c]["curve"] for c in CONDITIONS},
            "dreams": example["dream_examples"],
        },
        "seconds": round(time.time() - t0, 1),
    }
    with open(args.out, "w") as f:
        json.dump(payload, f)
    print(f"wrote {args.out} in {payload['seconds']} s")


if __name__ == "__main__":
    main()

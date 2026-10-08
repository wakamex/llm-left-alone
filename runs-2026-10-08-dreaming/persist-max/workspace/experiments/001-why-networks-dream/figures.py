#!/usr/bin/env python3
"""Draw the figures for experiment 001 from the results JSON files. Uses ../../tools/plotkit.py (pycairo)."""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
import plotkit as pk  # noqa: E402

COND = {  # color follows the condition in every figure
    "none": ("No dreams", pk.SERIES[0]),
    "random": ("Random dreams", pk.SERIES[1]),
    "shaped": ("Focused dreams", pk.SERIES[2]),
    "replay": ("Real memories", pk.MUTED),  # the reference, in de-emphasis gray
}
WORLD = pk.AXIS  # the true curve, drawn as a recessive reference


def dec(v):
    """Two significant figures in plain decimals (0.000053 rather than 5.3e-05)."""
    if v >= 1:
        return f"{v:.2g}" if v < 10 else f"{v:.0f}"
    places = -math.floor(math.log10(v)) + 1
    return f"{v:.{places}f}"


def load(name):
    with open(os.path.join(HERE, name)) as f:
        return json.load(f)


# ---------------------------------------------------------------------------------------------
def figure_forget(path_out):
    d = load("results_forget.json")
    s = d["summary"]
    n = d["config"]["n"]
    eps = d["config"]["eps"]
    loads = sorted(s.keys())
    ramp = [pk.BLUE_RAMP[k] for k in (250, 400, 550, 700)]  # ordinal: more memories, darker

    fig = pk.Figure(960, 616)
    fig.text(40, 52, "A little dreaming rescues an overloaded memory. Too much erases it.", size=20, bold=True)
    fig.wrap(40, 80, (f"A Hopfield network of {n} neurons stores random memories by Hebb's rule, then dreams: it falls "
                      f"from a random state into the nearest valley and weakens it slightly (Hopfield, Feinstein & Palmer "
                      f"1983). Classical capacity is about {0.138 * n:.0f} memories. Lines are the share of memories "
                      f"recalled from a 10%-corrupted cue, averaged over {d['config']['trials']} networks per load."),
             width=880, size=13)

    items = []
    for i, k in enumerate(loads):
        P = int(round(float(k) * n))
        items.append((f"{P} memories", ramp[i]))
    fig.legend(40, 166, items, size=12)

    ax = fig.axes(x=88, y=200, w=832, h=310, xlim=(0, d["config"]["dreams"]), ylim=(0, 1))
    ax.grid_y([0, 0.25, 0.5, 0.75, 1.0], fmt=pk.pct, baseline=0)
    ax.ticks_x(list(range(0, d["config"]["dreams"] + 1, 2000)), fmt=pk.comma)
    ax.title_x("Number of dreams")
    ax.title_y("Memories recalled")

    ax.clip()
    for i, k in enumerate(loads):
        b = s[k]
        xs = b["dreams"]
        m = b["recall"]["mean"]
        e = b["recall"]["sem"]
        ax.band(xs, [max(0, a - c) for a, c in zip(m, e)], [min(1, a + c) for a, c in zip(m, e)], ramp[i], alpha=0.12)
    for i, k in enumerate(loads):
        b = s[k]
        ax.line(b["dreams"], b["recall"]["mean"], ramp[i])
    ax.unclip()

    # Direct labels just past each collapse, near the floor where no other line runs.
    for i, k in enumerate(loads):
        b = s[k]
        xs, m = b["dreams"], b["recall"]["mean"]
        peak = max(range(len(m)), key=lambda j: m[j])
        gone = next((xs[j] for j in range(peak, len(m)) if m[j] < 0.05), None)  # recall has hit the floor
        if gone is None:
            continue
        P = int(round(float(k) * n))
        fig.text(ax.px(gone) + 6, ax.py(0.07), f"{P} memories", size=11, color=pk.INK_2)
        fig.text(ax.px(gone) + 6, ax.py(0.07) + 14, f"gone by {gone:,} dreams", size=10, color=pk.MUTED)

    fig.wrap(40, 580, (f"The collapse arrives after about 1.1 to 1.3 × P/ε dreams (P memories, ε = {eps} per dream): "
                       f"roughly when the network has unlearned as much as it ever learned. Shaded bands: ±1 standard "
                       f"error."),
             width=880, size=12, color=pk.MUTED)
    fig.save(path_out)


# ---------------------------------------------------------------------------------------------
def figure_remember(path_out):
    d = load("results_remember.json")
    ex = d["example_seed0"]
    s = d["summary"]
    grid, world = ex["grid"], ex["world"]
    PI = math.pi

    fig = pk.Figure(1000, 880)
    fig.text(40, 52, "Dreams protect yesterday, if they're about yesterday.", size=20, bold=True)
    fig.wrap(40, 80, ("A small network (1-64-64-1, tanh) learns the left half of a curve one day and the right half the "
                      "next. Before the second lesson it can dream: feed itself inputs, write down its own answers, and "
                      "keep rehearsing them while it learns (pseudorehearsal; Robins 1995, 1996)."),
             width=900, size=13)

    # Row 1: what the network believes, seed 0.
    panels = [("After yesterday", ex["after_yesterday"], pk.INK_2, None),
              ("No dreams", ex["none"], COND["none"][1], None),
              ("Random dreams", ex["random"], COND["random"][1], ex["dreams"]["random"]),
              ("Focused dreams", ex["shaped"], COND["shaped"][1], ex["dreams"]["shaped"]),
              ("Real memories", ex["replay"], COND["replay"][1], None)]
    pw, ph, gap, top = 170, 170, 18, 180
    fig.legend(40, 138, [("The world (truth)", WORLD), ("What the network believes", pk.INK_2)], size=12)
    for i, (title, curve, color, dreams) in enumerate(panels):
        x0 = 44 + i * (pw + gap)
        fig.text(x0, top - 10, title, size=12, bold=True, color=pk.INK)
        ax = fig.axes(x=x0, y=top + 4, w=pw, h=ph, xlim=(-PI, PI), ylim=(-3.1, 3.1))
        ax.span_x(-PI, 0, color=pk.GRID, alpha=0.5)
        ax.grid_y([0], labels=False)
        ax.clip()
        ax.line(grid, world, WORLD, width=3)
        ax.line(grid, curve, color, width=2)
        ax.unclip()
        if dreams:  # rug: where this condition's dreams were
            for xd in dreams["x"]:
                fig.vline(ax.px(xd), ax.y + ax.h + 3, ax.y + ax.h + 9, color=color)
        fig.text(x0, top + ph + 26, "yesterday", size=10, color=pk.MUTED)
        fig.text(x0 + pw, top + ph + 26, "today", size=10, color=pk.MUTED, anchor="end")
    fig.wrap(44, top + ph + 52, ("Shaded: the half the network saw yesterday. Ticks under a panel: where that night's "
                                 "dreams fell. Random dreams land everywhere, including today's half, where they argue "
                                 "with today's lesson."), width=880, size=11, color=pk.MUTED)

    # Row 2: errors over today's lesson, all seeds.
    steps = s["steps"]
    order = ["none", "random", "shaped", "replay"]
    y2 = 486
    fig.legend(40, y2 - 26, [(COND[c][0], COND[c][1]) for c in order], size=12)
    for j, (key, title) in enumerate([("mse_A", "Error on yesterday's half"), ("mse_B", "Error on today's half")]):
        x0 = 100 + j * 470
        ax = fig.axes(x=x0, y=y2 + 30, w=330, h=250, xlim=(0, steps[-1]), ylim=(1e-5, 30), ylog=True)
        fig.text(x0 - 56, y2 + 6, title, size=13, bold=True)
        ax.grid_y([1e-5, 1e-4, 1e-3, 1e-2, 1e-1, 1, 10],
                  fmt=lambda v: {1e-5: "0.00001", 1e-4: "0.0001", 1e-3: "0.001", 1e-2: "0.01", 1e-1: "0.1",
                                 1: "1", 10: "10"}[v])
        ax.ticks_x([0, 1000, 2000, 3000, 4000], fmt=pk.comma)
        ax.title_x("Training steps on today's half")
        ax.clip()
        for c in order:
            b = s[c][key]
            ax.band(steps, b["ci_lo"], b["ci_hi"], COND[c][1], alpha=0.10)
        for c in order:
            ax.line(steps, s[c][key]["geo_mean"], COND[c][1])
        ax.unclip()
        ends = {c: s[c][key]["geo_mean"][-1] for c in order}
        # Direct-label only the ends that stand apart (> 0.35 decades from every other end).
        for c in order:
            v = ends[c]
            apart = all(abs(math.log10(v) - math.log10(ends[o])) > 0.35 for o in order if o != c)
            fig.dot(ax.px(steps[-1]), ax.py(v), COND[c][1])
            if apart:
                fig.text(ax.px(steps[-1]) + 10, ax.py(v), dec(v), size=11, color=pk.INK_2, baseline="middle")
        if key == "mse_B":
            together = [c for c in order if not all(
                abs(math.log10(ends[c]) - math.log10(ends[o])) > 0.35 for o in order if o != c)]
            if together:
                v = math.exp(sum(math.log(ends[c]) for c in together) / len(together))
                fig.text(ax.px(steps[-1]) + 10, ax.py(v), "other three", size=11, color=pk.INK_2, baseline="middle")
    fig.wrap(40, 846, (f"Mean squared error (log scale) on a fine grid over each half. Lines are geometric means of "
                       f"{d['config']['seeds']} seeds; bands are 95% bootstrap intervals. All four conditions start "
                       f"from the same post-yesterday network in each seed."), width=900, size=11, color=pk.MUTED)
    fig.save(path_out)

# ---------------------------------------------------------------------------------------------
def load_all_forget():
    """Merge the three unlearning runs (main, fill-in loads, heavy loads) into one table keyed by P."""
    rows = {}
    for fn in ("results_forget.json", "results_forget_fill.json", "results_forget_heavy.json"):
        if not os.path.exists(os.path.join(HERE, fn)):
            continue
        d = load(fn)
        n = d["config"]["n"]
        for a, b in d["summary"].items():
            P = int(round(float(a) * n))
            D, r = b["dreams"], b["recall"]["mean"]
            best = max(range(len(r)), key=lambda i: r[i])
            win = [D[i] for i in range(len(D)) if r[i] >= 0.95]
            gone = next((D[i] for i in range(best, len(r)) if r[i] < 0.05), None)
            rows[P] = {"n": n, "eps": d["config"]["eps"], "trials": d["config"]["trials"], "r0": r[0],
                       "best": r[best], "best_at": D[best], "window": (win[0], win[-1]) if win else None,
                       "gone": gone}
    return dict(sorted(rows.items()))


def figure_capacity(path_out):
    rows = load_all_forget()
    Ps = list(rows)
    n = rows[Ps[0]]["n"]
    eps = rows[Ps[0]]["eps"]
    blue, gray = pk.SERIES[0], pk.MUTED

    fig = pk.Figure(980, 600)
    fig.text(40, 52, "Dreaming lets the same network hold about four times as many memories.", size=20, bold=True)
    fig.wrap(40, 80, (f"Same {n}-neuron Hopfield network, now at every load from {Ps[0]} to {Ps[-1]} memories "
                      f"(8 to 12 networks per load). Left: share recalled from a 10%-corrupted cue, with no dreams "
                      f"and at the best number of dreams. Holding 95% recall, it manages about 22 memories without "
                      f"dreams and about 88 with them. Right: the range of dream counts that keeps 95%."),
             width=900, size=13)

    # Left: how much dreaming can rescue.
    fig.text(40, 160, "How much dreaming can rescue", size=14, bold=True)
    fig.legend(40, 186, [("With the best amount of dreaming", blue), ("Without dreams", gray)], size=12)
    ax = fig.axes(x=88, y=220, w=360, h=270, xlim=(0, 150), ylim=(0, 1))
    ax.grid_y([0, 0.25, 0.5, 0.75, 1.0], fmt=pk.pct, baseline=0)
    ax.ticks_x([0, 25, 50, 75, 100, 125, 150])
    ax.title_x("Memories stored")
    cap = 0.138 * n
    fig.vline(ax.px(cap), ax.y, ax.y + ax.h, color=pk.AXIS)
    fig.text(ax.px(cap) - 6, ax.py(0.40), "classical", size=10, color=pk.MUTED, anchor="end")
    fig.text(ax.px(cap) - 6, ax.py(0.40) + 13, f"capacity: {cap:.0f}", size=10, color=pk.MUTED, anchor="end")
    ax.line(Ps, [rows[P]["r0"] for P in Ps], gray)
    ax.line(Ps, [rows[P]["best"] for P in Ps], blue)
    for P in Ps:
        fig.dot(ax.px(P), ax.py(rows[P]["r0"]), gray, r=3.5)
        fig.dot(ax.px(P), ax.py(rows[P]["best"]), blue, r=4)
    # Direct labels: where the dreaming curve starts to give way, and the last point.
    for P in (90, 110):
        if P in rows:
            fig.text(ax.px(P) + 8, ax.py(rows[P]["best"]) - 6, pk.pct(rows[P]["best"]), size=11, color=pk.INK_2)

    # Right: the window of healthy dreaming.
    fig.text(520, 160, "The window of healthy dreaming", size=14, bold=True)
    fig.legend(520, 186, [("At least 95% recalled", blue), ("P/\u03b5", pk.AXIS)], size=12)
    wP = [P for P in Ps if P <= 100]
    ymax = 12000
    bx = fig.axes(x=590, y=220, w=350, h=270, xlim=(0, 105), ylim=(0, ymax))
    bx.grid_y(list(range(0, ymax + 1, 3000)), fmt=pk.comma, baseline=0)
    bx.ticks_x([10, 20, 30, 40, 50, 60, 70, 80, 90, 100])
    bx.title_x("Memories stored")
    bx.title_y("Number of dreams")
    bx.line([0, 105], [0, 105 / eps], pk.AXIS, width=1.5)
    for P in wP:
        win = rows[P]["window"]
        if win is None:
            fig.text(bx.px(P), bx.py(0) - 8, "none", size=10, color=pk.MUTED, anchor="middle")
            continue
        y0, y1 = bx.py(win[0]), bx.py(win[1])
        h = max(4, y0 - y1)
        fig.rect(bx.px(P) - 8, y1, 16, h, blue, radius=4 if h >= 8 else 2)
    last = [P for P in wP if rows[P]["window"]][-1]
    lo_, hi_ = rows[last]["window"]
    fig.text(bx.px(last) - 8, bx.py(lo_) + 20, f"{last} memories:", size=10, color=pk.INK_2)
    fig.text(bx.px(last) - 8, bx.py(lo_) + 34, f"{lo_:,} to {hi_:,}", size=10, color=pk.INK_2)

    fig.wrap(40, 556, (f"The window opens later as memories are added (more false valleys to clear) and always "
                       f"closes near P/\u03b5 dreams (\u03b5 = {eps}), when about as much has been unlearned as was "
                       f"ever learned. Somewhere between 80 and 90 memories (0.40N to 0.45N) it stops opening."),
             width=900, size=12, color=pk.MUTED)
    fig.save(path_out)


if __name__ == "__main__":
    which = sys.argv[1:] or ["forget", "remember", "capacity"]
    if "forget" in which:
        figure_forget(os.path.join(HERE, "fig_forget.png"))
        print("wrote fig_forget.png")
    if "remember" in which:
        figure_remember(os.path.join(HERE, "fig_remember.png"))
        print("wrote fig_remember.png")
    if "capacity" in which:
        figure_capacity(os.path.join(HERE, "fig_capacity.png"))
        print("wrote fig_capacity.png")

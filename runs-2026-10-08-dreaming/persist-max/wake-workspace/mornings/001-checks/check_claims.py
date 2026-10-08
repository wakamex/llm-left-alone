"""Recompute the night's headline claims from its own stored data files (read-only)."""
import json, math, os, sys
import numpy as np

ROOT = sys.argv[1]
E1 = os.path.join(ROOT, "experiments/001-why-networks-dream")
E2 = os.path.join(ROOT, "experiments/002-dreams-of-dreams")
gm = lambda a: float(np.exp(np.mean(np.log(np.asarray(a, float)))))

print("=== 001 part 1: remember ===")
R = json.load(open(os.path.join(E1, "results_remember.json")))
S, F = R["summary"], R["final"]
print("config:", R["config"])
print(f"after yesterday: A {S['after_yesterday']['mse_A']['geo_mean'][0]:.6g}  B {S['after_yesterday']['mse_B']['geo_mean'][0]:.6g}")
for c in ["none", "random", "shaped", "replay"]:
    print(f"{c:7s} final geo-mean: A {S[c]['mse_A']['geo_mean'][-1]:.6g}  B {S[c]['mse_B']['geo_mean'][-1]:.6g}"
          f"   (recomputed from per-seed finals: A {gm(F[c]['mse_A']):.6g} B {gm(F[c]['mse_B']):.6g})")
x = np.linspace(-np.pi, 0, 201); w = lambda x: np.sin(2.2*x) + 0.35*np.sin(5.3*x + 0.4)
zA, zB = float(np.mean(w(x)**2)), float(np.mean(w(-x[::-1])**2))
print(f"zero-predictor MSE: A {zA:.3f}  B {zB:.3f}")
nA = np.array(F["none"]["mse_A"])
print(f"no dreams worse than zero-predictor on A in {int((nA > zA).sum())}/{len(nA)} seeds; best (min) {nA.min():.3g}; "
      f"geo-mean/zero = {gm(nA)/zA:.2f}x")
sh, rd, rp = (np.array(F[c]["mse_A"]) for c in ("shaped", "random", "replay"))
print(f"focused beats random on A: {int((sh < rd).sum())}/20; replay beats focused on A: {int((rp < sh).sum())}/20; "
      f"focused/replay geo ratio {gm(sh)/gm(rp):.2f}")
others = [S[c]["mse_B"]["geo_mean"][-1] for c in ("none", "shaped", "replay")]
print(f"random B / others B: {[round(S['random']['mse_B']['geo_mean'][-1]/o) for o in others]}")
ay = S['after_yesterday']['mse_A']['geo_mean'][0]; rpA = S['replay']['mse_A']['geo_mean'][-1]
print(f"'0.000053 before' vs '0.000053 replay': {ay:.4g} vs {rpA:.4g} (coincidence check)")

print("\n=== 001 part 2: forget (N=200, eps=0.01) ===")
rows = {}
for fn in ("results_forget.json", "results_forget_fill.json", "results_forget_heavy.json"):
    d = json.load(open(os.path.join(E1, fn)))
    for a, b in d["summary"].items():
        n_trials = d["config"]["trials"]
        rows[float(a)] = (b, n_trials, d["config"]["every"], fn)
cap_rows = []
for a in sorted(rows):
    b, nt, ev, fn = rows[a]
    D, r, land = b["dreams"], np.array(b["recall"]["mean"]), b["landing"]["mean"]
    best = int(r.argmax()); P = round(a * 200)
    win = [D[i] for i in range(len(D)) if r[i] >= 0.95]
    gone = next((D[i] for i in range(best, len(r)) if r[i] < 0.05), None)
    # fall time: last checkpoint >= 0.95 (after best) to first < 0.05
    last_hi = max((D[i] for i in range(len(D)) if r[i] >= 0.95), default=None)
    fall = (gone - last_hi) if (gone and last_hi is not None) else None
    cap_rows.append((P, r[0], r[best]))
    print(f"P={P:3d} trials={nt:2d} every={ev}  no-dreams {r[0]:.0%}  best {r[best]:.0%}@{D[best]}  "
          f"window {(str(win[0])+'..'+str(win[-1])) if win else 'none':>12s}  gone {gone}  gone/(P/eps) "
          f"{(gone/(P/0.01)) if gone else float('nan'):.2f}  fall {fall}  landing {land[0]:.2f}->{max(land):.2f}")
def cross(rows, idx):
    for (p1, *v1), (p2, *v2) in zip(rows, rows[1:]):
        y1, y2 = v1[idx], v2[idx]
        if y1 >= 0.95 > y2:
            return p1 + (p2 - p1) * (y1 - 0.95) / (y1 - y2)
print(f"95% capacity by linear interpolation: no dreams {cross(cap_rows, 0):.1f}, with dreams {cross(cap_rows, 1):.1f}; "
      f"0.138N = {0.138*200:.1f}")

print("\n=== 002: dreams of dreams ===")
for fn in ("results.json", "results_18days.json"):
    d = json.load(open(os.path.join(E2, fn)))
    s = {k: np.array(v) for k, v in d["summary"].items()}
    print(fn, d["config"])
    for c in ("none", "focused", "replay"):
        print(f"  {c:8s} day-1 error after each day: " + " ".join(f"{v:.2g}" for v in s[c][:, 0]))
    f1, r1 = s["focused"][:, 0], s["replay"][:, 0]
    ratio = f1[1:] / r1[1:]
    print(f"  focused/replay on day-1 segment, days 2..: " + " ".join(f"{v:.1f}" for v in ratio)
          + f"   (min {ratio.min():.1f}, max {ratio.max():.1f}, geo-mean {gm(ratio):.1f})")
    print(f"  focused drift day2->last: {f1[-1]/f1[1]:.2f}x ; replay range days 2..: max/min {r1[1:].max()/r1[1:].min():.1f}x ;"
          f" replay last/day2 {r1[-1]/r1[1]:.2f}; none/focused last {s['none'][-1,0]/f1[-1]:.0f}x")

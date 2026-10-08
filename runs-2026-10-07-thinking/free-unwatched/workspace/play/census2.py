# Faster soup census: numpy batch simulation + phase-aware object naming.
#   python3 census2.py [num_soups] [workers]
import sys, numpy as np
from collections import Counter
from multiprocessing import Pool

import os
W, H = int(os.environ.get("W", 40)), int(os.environ.get("H", 16))
DENSITY = float(os.environ.get("D", 0.3))
MAXGEN, RING = 20000, int(os.environ.get("RING", 512))
CHUNK = int(os.environ.get("CHUNK", 2000))

# ---------- batched torus simulation ----------
def np_step(g):
    n = sum(np.roll(np.roll(g, dy, 1), dx, 2)
            for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dy or dx)
    return ((n == 3) | ((n == 2) & (g == 1))).astype(np.uint8)

def simulate(seed0, count):
    rng = np.random.default_rng(seed0)
    g = (rng.random((count, H, W)) < DENSITY).astype(np.uint8)
    wts = np.random.default_rng(12345).integers(1, 2**63, H * W, dtype=np.uint64)
    ring = np.zeros((count, RING), dtype=np.uint64)
    active = np.arange(count)
    final = [None] * count; period = [0] * count; settle = [0] * count
    for t in range(MAXGEN):
        h = (g.reshape(len(active), -1).astype(np.uint64) * wts).sum(1)
        if t:
            lags = (np.arange(1, min(t, RING) + 1))
            past = ring[:, (t - lags) % RING]
            hit = past == h[:, None]
            done = hit.any(1)
            if done.any():
                for i in np.nonzero(done)[0]:
                    b = active[i]; p = int(lags[hit[i].argmax()])
                    final[b] = g[i].copy(); period[b] = p; settle[b] = t - p
                keep = ~done
                g, ring, h, active = g[keep], ring[keep], h[keep], active[keep]
                if not len(active): break
        ring[:, t % RING] = h
        g = np_step(g)
    for i, b in enumerate(active):          # never settled within MAXGEN
        final[b] = g[i].copy(); period[b] = -1; settle[b] = MAXGEN
    return final, period, settle

# ---------- set-based helpers for classification ----------
NB = [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy]

def step_set(g, wrap):
    n = {}
    for (x, y) in g:
        for dx, dy in NB:
            k = ((x+dx) % W, (y+dy) % H) if wrap else (x+dx, y+dy)
            n[k] = n.get(k, 0) + 1
    return frozenset(c for c, k in n.items() if k == 3 or (k == 2 and c in g))

def components(cells, r):
    left, out = set(cells), []
    while left:
        stack = [left.pop()]; comp = {stack[0]}
        while stack:
            x, y = stack.pop()
            for dx in range(-r, r+1):
                for dy in range(-r, r+1):
                    c = ((x+dx) % W, (y+dy) % H)
                    if c in left: left.remove(c); comp.add(c); stack.append(c)
        out.append(comp)
    return out

def unwrap(comp):
    xs = {x for x, _ in comp}; ys = {y for _, y in comp}
    sx = next((s for s in range(W) if all((x - s) % W < W - 3 for x in xs)), 0)
    sy = next((s for s in range(H) if all((y - s) % H < H - 3 for y in ys)), 0)
    return {((x - sx) % W, (y - sy) % H) for x, y in comp}

def canon(cells):
    best = None
    for f in range(8):
        pts = []
        for x, y in cells:
            if f & 1: x = -x
            if f & 2: y = -y
            if f & 4: x, y = y, x
            pts.append((x, y))
        mx = min(p[0] for p in pts); my = min(p[1] for p in pts)
        form = tuple(sorted((x - mx, y - my) for x, y in pts))
        if best is None or form < best: best = form
    return best

def phase_key(cells, steps=48):
    """Phase-independent name key: min canonical form over the object's evolution on an open plane."""
    cur = frozenset(cells); best = canon(cur); seen = {best}
    for _ in range(steps):
        cur = step_set(cur, wrap=False)
        if not cur: return ()
        c = canon(cur)
        if c in seen and c == best: break
        seen.add(c); best = min(best, c)
    return best

def split_objects(board, period):
    """Split a settled torus board into independently evolving objects (cells shown at phase 0)."""
    phases = [board]
    for _ in range(min(period, 400) - 1): phases.append(step_set(phases[-1], True))
    union = frozenset().union(*phases)
    objs = []
    for group in components(union, 2):
        pieces = components(group, 1)
        if len(pieces) > 1 and independent(board, pieces, period):
            objs += [board & p for p in pieces]
        else:
            objs.append(board & group)
    return [o for o in objs if o]

def independent(board, pieces, period):
    parts = [board & p for p in pieces]
    whole = board & frozenset().union(*pieces)
    for _ in range(min(period, 400)):
        parts = [step_set(p, True) for p in parts]
        whole = step_set(whole, True)
        if frozenset().union(*parts) != whole: return False
    return True

# ---------- named patterns ----------
KNOWN = {
    'block': ['OO', 'OO'], 'beehive': ['.OO.', 'O..O', '.OO.'],
    'loaf': ['.OO.', 'O..O', '.O.O', '..O.'], 'boat': ['OO.', 'O.O', '.O.'],
    'ship': ['OO.', 'O.O', '.OO'], 'tub': ['.O.', 'O.O', '.O.'],
    'pond': ['.OO.', 'O..O', 'O..O', '.OO.'], 'long boat': ['OO..', 'O.O.', '.O.O', '..O.'],
    'barge': ['.O..', 'O.O.', '.O.O', '..O.'], 'mango': ['.OO..', 'O..O.', '.O..O', '..OO.'],
    'long barge': ['.O...', 'O.O..', '.O.O.', '..O.O', '...O.'],
    'long ship': ['OO..', 'O.O.', '.O.O', '..OO'],
    'eater 1': ['OO..', 'O.O.', '..O.', '..OO'], 'snake': ['OO.O', 'O.OO'],
    'aircraft carrier': ['OO..', 'O..O', '..OO'],
    'integral': ['...OO', '..O.O', '..O..', 'O.O..', 'OO...'],
    'ship-tie': ['OO....', 'O.O...', '.OO...', '...OO.', '...O.O', '....OO'],
    'bi-loaf': ['.O.....', 'O.O....', 'O..O...', '.OO.O..', '...O.O.', '...O..O', '....OO.'],
    'boat-tie': ['.O...', 'O.O..', '.OO..', '...OO', '...O.O', '....O.'],
    'big S': ['....OO', '...O.O', '...O..', '..O...', '..O...', 'O.O...', 'OO....'],
    'shillelagh': ['OO...', 'O..OO', '.OO.O'],
    'paperclip': ['..OO.', '.O..O', '.O.OO', 'OO.O.', 'O..O.', '.OO..'],
    'blinker': ['OOO'], 'toad': ['.OOO', 'OOO.'], 'beacon': ['OO..', 'OO..', '..OO', '..OO'],
    'clock': ['..O.', 'O.O.', '.O.O', '.O..'],
    'traffic light': ['..OOO..', '.......', 'O.....O', 'O.....O', 'O.....O', '.......', '..OOO..'],
    'pulsar': ['..OOO...OOO..', '.............', 'O....O.O....O', 'O....O.O....O',
               'O....O.O....O', '..OOO...OOO..', '.............', '..OOO...OOO..',
               'O....O.O....O', 'O....O.O....O', 'O....O.O....O', '.............', '..OOO...OOO..'],
    'pentadecathlon': ['..O....O..', 'OO.OOOO.OO', '..O....O..'],
    'glider': ['.O.', '..O', 'OOO'], 'LWSS': ['.O..O', 'O....', 'O...O', 'OOOO.'],
    'MWSS': ['...O..', '.O...O', 'O.....', 'O....O', 'OOOOO.'],
    'HWSS': ['...OO..', '.O....O', 'O......', 'O.....O', 'OOOOOO.'],
}
NAMES = {phase_key({(x, y) for y, r in enumerate(rows) for x, ch in enumerate(r) if ch == 'O'}): n
         for n, rows in KNOWN.items()}

# ---------- worker ----------
def work(seed0):
    final, period, settle = simulate(seed0, CHUNK)
    objs, periods, unknown = Counter(), Counter(), Counter()
    longest = (0, None)
    for i, b in enumerate(final):
        periods[period[i]] += 1
        if settle[i] > longest[0]: longest = (settle[i], seed0 * 10**6 + i)
        if period[i] < 0: continue
        cells = frozenset(zip(*np.nonzero(b)[::-1]))
        cells = frozenset((int(x), int(y)) for x, y in cells)
        for o in split_objects(cells, period[i]):
            key = phase_key(unwrap(o))
            name = NAMES.get(key)
            if name: objs[name] += 1
            else: unknown[key] += 1; objs[f'(unnamed {len(key)}-cell)'] += 1
    return objs, periods, unknown, longest, settle

if __name__ == '__main__':
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 10000
    workers = int(sys.argv[2]) if len(sys.argv) > 2 else 16
    chunks = max(1, n // CHUNK)
    objs, periods, unknown, settles = Counter(), Counter(), Counter(), []
    longest = (0, None)
    with Pool(workers) as pool:
        for o, p, u, l, s in pool.imap_unordered(work, range(chunks)):
            objs += o; periods += p; unknown += u; settles += s; longest = max(longest, l)
    total = chunks * CHUNK
    settles.sort()
    print(f"{total} soups on a {W}x{H} torus, density {DENSITY}\n")
    print("final-cycle periods:", dict(sorted(periods.items())))
    print(f"median settle: {settles[total//2]} gens, 99th pct: {settles[int(total*.99)]}, "
          f"longest: {longest[0]} (chunk {longest[1] // 10**6}, soup {longest[1] % 10**6})\n")
    print("object census:")
    for name, c in objs.most_common(): print(f"  {c:8d}  {name}")
    if unknown:
        print("\nunnamed objects (phase shown is the canonical one):")
        for key, c in unknown.most_common(8):
            s = set(key); w = max(x for x, _ in key) + 1; h = max(y for _, y in key) + 1
            print(f"  seen {c}x, {len(key)} cells:")
            for y in range(h): print("    " + "".join("█" if (x, y) in s else "·" for x in range(w)))

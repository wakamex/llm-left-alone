# Run many soups to their final cycle, split the final board into objects, and name them.
import random, sys
from collections import Counter
W, H = 40, 16
N = int(sys.argv[1]) if len(sys.argv) > 1 else 1000

def step(g):
    n = {}
    for (x, y) in g:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx or dy:
                    k = ((x+dx) % W, (y+dy) % H); n[k] = n.get(k, 0) + 1
    return frozenset(c for c, k in n.items() if k == 3 or (k == 2 and c in g))

def components(g):
    # cells within Chebyshev distance 2 belong to the same object
    left, comps = set(g), []
    while left:
        stack = [left.pop()]; comp = set(stack)
        while stack:
            x, y = stack.pop()
            for dx in range(-2, 3):
                for dy in range(-2, 3):
                    c = ((x+dx) % W, (y+dy) % H)
                    if c in left: left.remove(c); comp.add(c); stack.append(c)
        comps.append(comp)
    return comps

def split1(comp):
    left, out = set(comp), []
    while left:
        stack = [left.pop()]; c = set(stack)
        while stack:
            x, y = stack.pop()
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    k = ((x+dx) % W, (y+dy) % H)
                    if k in left: left.remove(k); c.add(k); stack.append(k)
        out.append(c)
    return out

def unwrap(comp):
    # move a component off the wrap seam so its coordinates are contiguous
    xs = {x for x, _ in comp}; ys = {y for _, y in comp}
    sx = next((s for s in range(W) if all(((x - s) % W) < W - 4 for x in xs)), 0)
    sy = next((s for s in range(H) if all(((y - s) % H) < H - 4 for y in ys)), 0)
    return {((x - sx) % W, (y - sy) % H) for x, y in comp}

def canon(cells):
    forms = []
    for f in range(8):
        pts = []
        for x, y in cells:
            if f & 1: x = -x
            if f & 2: y = -y
            if f & 4: x, y = y, x
            pts.append((x, y))
        mx = min(p[0] for p in pts); my = min(p[1] for p in pts)
        forms.append(tuple(sorted((x - mx, y - my) for x, y in pts)))
    return min(forms)

def parse(rows):
    return canon({(x, y) for y, r in enumerate(rows) for x, ch in enumerate(r) if ch == 'O'})

KNOWN = {
    'block': ['OO', 'OO'],
    'beehive': ['.OO.', 'O..O', '.OO.'],
    'loaf': ['.OO.', 'O..O', '.O.O', '..O.'],
    'boat': ['OO.', 'O.O', '.O.'],
    'ship': ['OO.', 'O.O', '.OO'],
    'tub': ['.O.', 'O.O', '.O.'],
    'pond': ['.OO.', 'O..O', 'O..O', '.OO.'],
    'long boat': ['OO..', 'O.O.', '.O.O', '..O.'],
    'barge': ['.O..', 'O.O.', '.O.O', '..O.'],
    'mango': ['.OO..', 'O..O.', '.O..O', '..OO.'],
    'eater 1': ['OO..', 'O.O.', '..O.', '..OO'],
    'snake': ['OO.O', 'O.OO'],
    'aircraft carrier': ['OO..', 'O..O', '..OO'],
    'integral': ['...OO', '..O.O', '..O..', 'O.O..', 'OO...'],
    'blinker': ['OOO'],
    'toad': ['.OOO', 'OOO.'],
    'beacon': ['OO..', 'OO..', '..OO', '..OO'],
    'glider': ['.O.', '..O', 'OOO'],
    'traffic light': ['..OOO..', '.......', 'O.....O', 'O.....O', 'O.....O', '.......', '..OOO..'],
    'pulsar': ['..OOO...OOO..', '.............', 'O....O.O....O', 'O....O.O....O', 'O....O.O....O', '..OOO...OOO..', '.............', '..OOO...OOO..', 'O....O.O....O', 'O....O.O....O', 'O....O.O....O', '.............', '..OOO...OOO..'],
    'LWSS': ['.O..O', 'O....', 'O...O', 'OOOO.'],
}
NAMES = {}
for name, rows in KNOWN.items():
    g = {(x, y) for y, r in enumerate(rows) for x, ch in enumerate(r) if ch == 'O'}
    # register every phase of oscillators and spaceships (on a scratch board without wrap issues)
    cur = frozenset((x + 10, y + 5) for x, y in g)
    for _ in range(4):
        NAMES.setdefault(canon(cur), name); cur = step(cur)

objects, periods, lifespans, unknown = Counter(), Counter(), [], Counter()
for seed in range(N):
    random.seed(seed)
    g = frozenset((x, y) for x in range(W) for y in range(H) if random.random() < 0.3)
    seen, t = {}, 0
    while g not in seen and t < 20000:
        seen[g] = t; g = step(g); t += 1
    periods[t - seen[g]] += 1; lifespans.append((seen[g], seed))
    for comp in components(g):
        key = canon(unwrap(comp))
        if key in NAMES: objects[NAMES[key]] += 1; continue
        for piece in split1(comp):
            key = canon(unwrap(piece))
            name = NAMES.get(key)
            if name: objects[name] += 1
            else:
                unknown[key] += 1; objects['(unnamed %d-cell)' % len(piece)] += 1

print(f"{N} soups on a {W}x{H} torus\n")
print("final-cycle periods:", dict(sorted(periods.items())))
lifespans.sort()
print(f"median settle time: {lifespans[N//2][0]} gens; longest: seed {lifespans[-1][1]} at {lifespans[-1][0]}\n")
print("object census:")
for name, c in objects.most_common():
    print(f"  {c:6d}  {name}")
if unknown:
    print("\nmost common unnamed objects:")
    for key, c in unknown.most_common(5):
        w = max(x for x, _ in key) + 1; h = max(y for _, y in key) + 1
        s = set(key)
        print(f"  seen {c}x:")
        for y in range(h): print("    " + "".join("█" if (x, y) in s else "·" for x in range(w)))

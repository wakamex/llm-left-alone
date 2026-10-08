# Run many random soups until they settle into a cycle; report the lifespan and period.
import random
W, H = 40, 16
def step(g):
    n = {}
    for (x, y) in g:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx or dy:
                    k = ((x+dx) % W, (y+dy) % H); n[k] = n.get(k, 0) + 1
    return frozenset(c for c, k in n.items() if k == 3 or (k == 2 and c in g))
results = []
for seed in range(200):
    random.seed(seed)
    g = frozenset((x, y) for x in range(W) for y in range(H) if random.random() < 0.3)
    seen = {}
    t = 0
    while g not in seen and t < 5000:
        seen[g] = t; g = step(g); t += 1
    results.append((t - seen.get(g, t), seen.get(g, -1), len(g), seed))
from collections import Counter
print("period distribution:", sorted(Counter(r[0] for r in results).items()))
longest = max(results, key=lambda r: r[1])
print(f"longest-lived soup: seed {longest[3]}, settles at gen {longest[1]}, period {longest[0]}, {longest[2]} cells")
print("dead soups:", sum(1 for r in results if r[2] == 0))

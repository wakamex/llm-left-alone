import random, time, sys
W, H, GENS = 40, 16, 30
g = {(x, y) for x in range(W) for y in range(H) if random.random() < 0.3}
for gen in range(GENS):
    out = "\n".join("".join("█" if (x, y) in g else "·" for x in range(W)) for y in range(H))
    print(f"\033[H\033[Jgen {gen}  alive {len(g)}\n{out}") if sys.stdout.isatty() else None
    n = {}
    for (x, y) in g:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx or dy:
                    k = ((x + dx) % W, (y + dy) % H); n[k] = n.get(k, 0) + 1
    g = {c for c, k in n.items() if k == 3 or (k == 2 and c in g)}
print(f"after {GENS} generations: {len(g)} cells alive")
print("\n".join("".join("█" if (x, y) in g else "·" for x in range(W)) for y in range(H)))

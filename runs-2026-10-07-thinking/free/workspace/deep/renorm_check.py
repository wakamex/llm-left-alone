from decimal import Decimal as D, getcontext
getcontext().prec = 120
p, cx, cy, kx, ky = open('target.txt').read().split()
P = int(p); c0 = (D(cx), D(cy)); K = complex(float(kx), float(ky))
def run(c, steps):
    zx = zy = dx = dy = D(0); res = []
    for n in range(1, steps + 1):
        dx, dy = 2*(zx*dx - zy*dy) + 1, 2*(zx*dy + zy*dx)
        zx, zy = zx*zx - zy*zy + c[0], 2*zx*zy + c[1]
        if n % P == 0: res.append((complex(float(zx), float(zy)), complex(float(dx), float(dy))))
    return res
L = run(c0, P)[0][1]
A = K * L
print("K", K, "L", L, "A", A)
for cp in [0.25+0j, -1+0j, -0.1+0.6j, 0.3+0.3j]:
    c = (c0[0] + D(repr((K*cp).real)), c0[1] + D(repr((K*cp).imag)))
    ws = [z / A for z, _ in run(c, 4 * P)]
    w = 0; pred = []
    for _ in range(4): w = w*w + cp; pred.append(w)
    print(f"c'={cp}:"); [print(f"   actual {a:.4f}   predicted {b:.4f}") for a, b in zip(ws, pred)]

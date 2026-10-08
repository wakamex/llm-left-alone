"""Find a deep minibrot near a point using Decimal arithmetic.
usage: find.py <re> <im> <radius_exp10> [digits]"""
import sys
from decimal import Decimal as D, getcontext

re0, im0, rexp = D(sys.argv[1]), D(sys.argv[2]), int(sys.argv[3])
getcontext().prec = int(sys.argv[4]) if len(sys.argv) > 4 else max(60, -rexp * 2 + 30)
r = D(10) ** rexp

def cmul(a, b, c, d): return a*c - b*d, a*d + b*c
def cabs2(a, b): return a*a + b*b

# 1) ball-period: first n with |z_n| < r |dz_n/dc|
zx = zy = dx = dy = D(0)
period = None
for n in range(1, 2_000_000):
    dx, dy = cmul(2*zx, 2*zy, dx, dy); dx += 1          # dz' = 2 z dz + 1
    zx, zy = zx*zx - zy*zy + re0, 2*zx*zy + im0
    if cabs2(zx, zy) > 1e6: sys.exit(f"escaped at {n}; point outside")
    if cabs2(zx, zy) < r*r*cabs2(dx, dy):
        period = n; break
print("period", period, file=sys.stderr)

# 2) Newton for nucleus: solve z_p(c) = 0
cx, cy = re0, im0
for it in range(200):
    zx = zy = dx = dy = D(0)
    for _ in range(period):
        dx, dy = cmul(2*zx, 2*zy, dx, dy); dx += 1
        zx, zy = zx*zx - zy*zy + cx, 2*zx*zy + cy
    den = cabs2(dx, dy)
    sx, sy = (zx*dx + zy*dy)/den, (zy*dx - zx*dy)/den   # z/dz
    cx, cy = cx - sx, cy - sy
    step = cabs2(sx, sy)
    if step == 0 or step.adjusted() < -2*getcontext().prec + 10: break
print("newton iters", it + 1, file=sys.stderr)

# 3) size estimate (Heiland-Allen)
zx = zy = D(0); lx, ly = D(1), D(0); bx, by = D(1), D(0)
for j in range(1, period):
    zx, zy = zx*zx - zy*zy + cx, 2*zx*zy + cy
    lx, ly = cmul(2*zx, 2*zy, lx, ly)
    den = cabs2(lx, ly); bx += lx/den; by += -ly/den
l2x, l2y = cmul(lx, ly, lx, ly)
sx, sy = cmul(bx, by, l2x, l2y)
size = 1 / cabs2(sx, sy).sqrt()
dist = cabs2(cx - re0, cy - im0).sqrt()
print("size %.3e  dist-from-start %.3e" % (size, dist), file=sys.stderr)
print(period); print(cx); print(cy); print("%.6e" % size)

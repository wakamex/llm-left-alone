"""Chain minibrot search: at each level, map the classic seahorse point into the
current minibrot's coordinates and look for the next minibrot there.
usage: chain.py <levels> > target.txt"""
import sys
from decimal import Decimal as D, getcontext

def cmul(a, b, c, d): return a*c - b*d, a*d + b*c
def cabs2(a, b): return a*a + b*b

def find(re0, im0, r):
    zx = zy = dx = dy = D(0)
    period = None
    for n in range(1, 10_000_000):
        dx, dy = cmul(2*zx, 2*zy, dx, dy); dx += 1
        zx, zy = zx*zx - zy*zy + re0, 2*zx*zy + im0
        if cabs2(zx, zy) > 1e6: raise RuntimeError(f"escaped at {n}")
        if cabs2(zx, zy) < r*r*cabs2(dx, dy): period = n; break
    if period is None: raise RuntimeError("no period")
    cx, cy = re0, im0
    for it in range(100):
        zx = zy = dx = dy = D(0)
        for _ in range(period):
            dx, dy = cmul(2*zx, 2*zy, dx, dy); dx += 1
            zx, zy = zx*zx - zy*zy + cx, 2*zx*zy + cy
        den = cabs2(dx, dy)
        sx, sy = (zx*dx + zy*dy)/den, (zy*dx - zx*dy)/den
        cx, cy = cx - sx, cy - sy
        if cabs2(sx, sy) == 0 or cabs2(sx, sy).adjusted() < -2*getcontext().prec + 20: break
    zx = zy = D(0); lx, ly = D(1), D(0); bx, by = D(1), D(0)
    for j in range(1, period):
        zx, zy = zx*zx - zy*zy + cx, 2*zx*zy + cy
        lx, ly = cmul(2*zx, 2*zy, lx, ly)
        den = cabs2(lx, ly); bx += lx/den; by -= ly/den
    sx, sy = cmul(bx, by, *cmul(lx, ly, lx, ly))
    den = cabs2(sx, sy)
    return period, cx, cy, sx/den, -sy/den   # complex size = 1/(b l^2)

levels = int(sys.argv[1])
getcontext().prec = int(__import__("os").environ.get("PREC", "120"))
P = (D("-0.743643887037151"), D("0.131825904205330"))
cx, cy, kx, ky = D(0), D(0), D(1), D(0)       # identity: main set
for lev in range(levels):
    ox, oy = cmul(kx, ky, *P)
    tx, ty = cx + ox, cy + oy
    for e in range(14, 2, -2):
        try:
            p, cx, cy, kx, ky = find(tx, ty, cabs2(kx, ky).sqrt() * D(10) ** -e); break
        except RuntimeError: continue
    print(f"level {lev+1}: period {p}  |size| {float(cabs2(kx,ky).sqrt()):.3e}", file=sys.stderr, flush=True)
print(p); print(cx); print(cy); print(kx); print(ky)

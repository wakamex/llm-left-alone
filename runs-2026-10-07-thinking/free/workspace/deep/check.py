import sys
from decimal import Decimal as D, getcontext
getcontext().prec = 80
p, cx, cy, kx, ky = open('target.txt').read().split()
cx, cy = D(cx), D(cy)
for off in sys.argv[1:]:
    ox = D(off)
    x0, y0 = cx + ox, cy
    zx = zy = D(0)
    for n in range(3_000_000):
        zx, zy = zx*zx - zy*zy + x0, 2*zx*zy + y0
        if zx*zx + zy*zy > 4: break
    print(f"offset {off}: escaped at {n}" if n < 2_999_999 else f"offset {off}: inside after 3M", flush=True)

"""Compute reference orbit Z_0..Z_p at the nucleus (high precision), save as doubles."""
import struct, sys
from decimal import Decimal as D, getcontext
getcontext().prec = 120
p, cx, cy, kx, ky = open(sys.argv[1]).read().split()
p, cx, cy = int(p), D(cx), D(cy)
zx = zy = D(0)
out = [(0.0, 0.0)]
for n in range(p):
    zx, zy = zx*zx - zy*zy + cx, 2*zx*zy + cy
    out.append((float(zx), float(zy)))
with open(sys.argv[2], "wb") as f:
    f.write(struct.pack("<i2d", p, float(kx), float(ky)))
    for a, b in out: f.write(struct.pack("<2d", a, b))
print("Z_p =", out[-1], " min|Z_n| (n<p) =", min(abs(complex(*z)) for z in out[1:-1]))

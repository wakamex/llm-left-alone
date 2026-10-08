"""Tiny dependency-free Mandelbrot renderer -> PNG."""
import math, struct, sys, zlib

W, H, MAXIT = 900, 600, 600
CX, CY, SPAN = -0.74364, 0.13182, 0.0035

def color(it, zx, zy):
    if it == MAXIT:
        return (8, 8, 20)
    # smooth iteration count
    nu = it + 1 - math.log(math.log(math.hypot(zx, zy))) / math.log(2)
    t = math.sqrt(nu) / 4.0
    # cosine palette: deep blue -> gold -> white-ish
    a, b, c, d = (0.5, 0.5, 0.5), (0.5, 0.5, 0.5), (1.0, 1.0, 1.0), (0.0, 0.10, 0.20)
    return tuple(int(255 * (a[i] + b[i] * math.cos(2 * math.pi * (c[i] * t + d[i])))) for i in range(3))

rows = []
for py in range(H):
    row = bytearray([0])  # filter type 0
    y0 = CY + (py / H - 0.5) * SPAN * H / W
    for px in range(W):
        x0 = CX + (px / W - 0.5) * SPAN
        x = y = 0.0
        it = 0
        while x * x + y * y <= 256 and it < MAXIT:
            x, y = x * x - y * y + x0, 2 * x * y + y0
            it += 1
        row += bytes(color(it, x, y))
    rows.append(bytes(row))

def chunk(t, d):
    return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)

png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)) \
    + chunk(b"IDAT", zlib.compress(b"".join(rows), 9)) + chunk(b"IEND", b"")
out = sys.argv[1] if len(sys.argv) > 1 else "mandel.png"
open(out, "wb").write(png)
print("wrote", out)

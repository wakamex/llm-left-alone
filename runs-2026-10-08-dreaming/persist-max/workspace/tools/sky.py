#!/usr/bin/env python3
"""
sky.py: draw the night sky over a directory of programs (default /bin).

Every point of light is one real file. Nothing in the sky is decoration except
the faint band of the Milky Way.
  brightness   log of file size
  colour       compiled (ELF) cool white; script (#!) warm; alias (symlink) dimmer
  dark ring    a symlink that points at nothing
  red ember    a file I wasn't permitted to read
  constellations  families of programs that share a name stem (clang-*, tpm2_*, ...),
                  with figure lines joining each family's eight largest members

Positions are hash-derived, so the same directory always gives the same sky.
Run it again on another night and new stars will be newly installed programs.

    python3 -I sky.py [--dir /bin] [--out sky.png] [--catalog sky.json]
"""
import argparse
import hashlib
import json
import math
import os
import re
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plotkit as pk  # noqa: E402  (sets up fontconfig, gives us cairo + text helpers)
cairo = pk.cairo

W, H = 1600, 1000
CAPTION_BOX = (40, 790, 720, 980)  # keep stars out of the caption corner (x0, y0, x1, y1)


def h01(*parts):
    """Deterministic floats in [0,1) from a string key."""
    d = hashlib.blake2b("\x1f".join(map(str, parts)).encode(), digest_size=16).digest()
    return [int.from_bytes(d[i:i + 4], "little") / 2**32 for i in range(0, 16, 4)]


def family_of(name):
    stem = re.split(r"[-_.]", name)[0]
    stem = re.sub(r"\d+$", "", stem)
    return stem or name


def survey(directory):
    stars = []
    for name in sorted(os.listdir(directory)):
        p = os.path.join(directory, name)
        rec = {"name": name, "family": family_of(name), "link": os.path.islink(p)}
        try:
            st = os.stat(p)
            with open(p, "rb") as f:
                head = f.read(4)
            rec["size"] = st.st_size
            rec["kind"] = "elf" if head == b"\x7fELF" else ("script" if head[:2] == b"#!" else "other")
        except FileNotFoundError:
            rec["size"], rec["kind"] = 0, "dangling"
        except PermissionError:
            try:
                rec["size"] = os.stat(p).st_size
            except OSError:
                rec["size"] = 0
            rec["kind"] = "forbidden"
        except OSError:
            rec["size"], rec["kind"] = 0, "other"
        stars.append(rec)
    return stars


def band_y(x):
    """Centre line of the Milky Way: a long shallow S across the sky."""
    t = x / W
    return H * (0.62 - 0.38 * t + 0.07 * math.sin(2 * math.pi * t * 1.3 + 0.6))


def in_caption(x, y, pad=0):
    x0, y0, x1, y1 = CAPTION_BOX
    return x0 - pad <= x <= x1 + pad and y0 - pad <= y <= y1 + pad


def layout(stars, min_family=6):
    fams = defaultdict(list)
    for s in stars:
        fams[s["family"]].append(s)
    big = sorted([f for f, m in fams.items() if len(m) >= min_family], key=lambda f: -len(fams[f]))

    centres = {}
    for f in big:  # place the largest families first, rejection-sampling deterministic candidates
        r = 6.5 * math.sqrt(len(fams[f])) + 10
        for attempt in range(400):
            u = h01("centre", f, attempt)
            x = 70 + u[0] * (W - 140)
            if u[2] < 0.6:  # most constellations sit near the band, like the real sky
                y = band_y(x) + (u[1] - 0.5) * 360
            else:
                y = 60 + u[1] * (H - 120)
            ok = 50 + r < x < W - 50 - r and 50 + r < y < H - 40 - r and not in_caption(x, y, r + 30)
            ok = ok and all(math.hypot(x - cx, y - cy) > r + cr + 26 for cx, cy, cr in centres.values())
            if ok:
                centres[f] = (x, y, r)
                break
    golden = math.pi * (3 - math.sqrt(5))
    for f, (cx, cy, r) in centres.items():
        members = sorted(fams[f], key=lambda s: -s["size"])  # biggest near the middle
        for k, s in enumerate(members):
            u = h01("member", s["name"])
            rad = 6.5 * math.sqrt(k + 0.5) * (0.82 + 0.36 * u[0])
            ang = k * golden + (u[1] - 0.5) * 0.9 + h01("spin", f)[0] * 2 * math.pi
            s["x"], s["y"] = cx + rad * math.cos(ang), cy + rad * 0.82 * math.sin(ang)
    for s in stars:
        if "x" in s:
            continue
        for attempt in range(200):
            u = h01("free", s["name"], attempt)
            x = 14 + u[0] * (W - 28)
            if u[2] < 0.55:
                y = band_y(x) + math.copysign(abs(u[1] - 0.5) ** 1.6, u[1] - 0.5) * 520
            else:
                y = 14 + u[1] * (H - 28)
            if 10 < y < H - 10 and not in_caption(x, y, 12) and \
                    all(math.hypot(x - cx, y - cy) > cr + 8 for cx, cy, cr in centres.values()):
                s["x"], s["y"] = x, y
                break
        else:
            s["x"], s["y"] = 14 + h01("fallback", s["name"])[0] * (W - 28), 20
    return fams, centres


def mst(points):
    """Prim's algorithm: edges (i, j) of a minimum spanning tree over 2-D points."""
    n = len(points)
    if n < 2:
        return []
    inside = {0}
    best = {j: (math.dist(points[0], points[j]), 0) for j in range(1, n)}
    edges = []
    while best:
        j = min(best, key=lambda k: best[k][0])
        edges.append((best[j][1], j))
        inside.add(j)
        del best[j]
        for k in best:
            d = math.dist(points[j], points[k])
            if d < best[k][0]:
                best[k] = (d, j)
    return edges


def halo_text(fig, x, y, s, size, color, anchor="start", italic=False, family=pk.FONT):
    """Text with a soft dark outline so it reads over the bright band."""
    cr = fig.cr
    fig.font(size, italic=italic, family=family)
    ext = cr.text_extents(s)
    if anchor == "middle":
        x -= ext.x_advance / 2
    elif anchor == "end":
        x -= ext.x_advance
    cr.new_path()
    cr.move_to(x, y)
    cr.text_path(s)
    cr.set_source_rgba(*pk.rgb("#070b16")[:3], 0.55)
    cr.set_line_width(2.6)
    cr.set_line_join(cairo.LINE_JOIN_ROUND)
    cr.stroke_preserve()
    cr.set_source_rgba(*pk.rgb(color))
    cr.fill()


def paint_milky_way(fig, seed=8102026):
    """A patchy band with dust lanes, built from fractal value noise and painted at device resolution."""
    import numpy as np
    from PIL import Image
    sc = fig.scale
    w, h = int(W * sc), int(H * sc)
    rng = np.random.default_rng(seed)

    def noise(octaves, base):
        acc = np.zeros((h, w), np.float32)
        amp, total = 1.0, 0.0
        for o in range(octaves):
            gw, gh = base * 2 ** o, max(2, int(base * 2 ** o * h / w))
            grid = rng.random((gh, gw)).astype(np.float32)
            img = Image.fromarray((grid * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
            acc += amp * (np.asarray(img, np.float32) / 255.0)
            total += amp
            amp *= 0.55
        return acc / total

    xs = np.arange(w, dtype=np.float32) / sc
    ys = np.arange(h, dtype=np.float32)[:, None] / sc
    centre = np.array([band_y(x) for x in xs], np.float32)[None, :]
    d = ys - centre
    clouds = noise(6, 6)
    wobble = (noise(3, 3) - 0.5) * 90
    core = np.exp(-((d + wobble) / 120.0) ** 2)
    glow = np.exp(-((d + wobble * 0.6) / 230.0) ** 2)
    lanes = np.exp(-((d - 12 + wobble * 1.4) / 26.0) ** 2) * np.clip((noise(5, 10) - 0.35) * 2.4, 0, 1)
    light = (0.6 * core * clouds ** 1.5 + 0.16 * glow) * (1.0 - 0.85 * lanes)
    warm = np.clip(noise(4, 4) * 1.6 - 0.6, 0, 1)
    alpha = np.clip(light * 0.62, 0, 0.6)
    r = (0.66 + 0.30 * warm) * alpha
    g = (0.72 + 0.16 * warm) * alpha
    b = (1.00 - 0.12 * warm) * alpha
    bgra = np.dstack([b, g, r, alpha])  # cairo ARGB32 is premultiplied BGRA in memory (little-endian)
    buf = np.ascontiguousarray((np.clip(bgra, 0, 1) * 255).astype(np.uint8))
    surf = cairo.ImageSurface.create_for_data(memoryview(buf), cairo.FORMAT_ARGB32, w, h, w * 4)
    cr = fig.cr
    cr.save()
    cr.scale(1 / sc, 1 / sc)
    cr.set_source_surface(surf, 0, 0)
    cr.paint()
    cr.restore()


COLOURS = {"elf": "#dfe7ff", "script": "#ffd6a0", "other": "#c8f0e0", "forbidden": "#ff7d6b"}


def draw(stars, fams, centres, out_png, caption_lines, labels):
    fig = pk.Figure(W, H, scale=1.5, background="#060912")
    cr = fig.cr

    sky = cairo.LinearGradient(0, 0, 0, H)
    sky.add_color_stop_rgb(0.0, *pk.rgb("#05070f")[:3])
    sky.add_color_stop_rgb(0.7, *pk.rgb("#0a1020")[:3])
    sky.add_color_stop_rgb(1.0, *pk.rgb("#141c30")[:3])
    cr.set_source(sky)
    cr.paint()

    # The Milky Way: the one decorative element (no data in it).
    paint_milky_way(fig)

    # Constellation figures: each family's eight largest members.
    for f, (cx, cy, r) in centres.items():
        brightest = sorted(fams[f], key=lambda s: -s["size"])[:8]
        pts = [(s["x"], s["y"]) for s in brightest]
        cr.set_source_rgba(*pk.rgb("#8ea2d8")[:3], 0.28)
        cr.set_line_width(0.8)
        for i, j in mst(pts):
            cr.move_to(*pts[i])
            cr.line_to(*pts[j])
            cr.stroke()

    sizes = [s["size"] for s in stars if s["size"] > 0]
    lo, hi = math.log10(max(1, min(sizes))), math.log10(max(sizes))
    for s in sorted(stars, key=lambda s: s["size"]):
        x, y = s["x"], s["y"]
        if s["kind"] == "dangling":  # a link to nothing: a dark ring where a star should be
            cr.set_source_rgba(*pk.rgb("#7b86a3")[:3], 0.75)
            cr.set_line_width(0.9)
            cr.arc(x, y, 2.6, 0, 2 * math.pi)
            cr.stroke()
            continue
        t = (math.log10(max(1, s["size"])) - lo) / (hi - lo)
        core = 0.45 + 2.3 * t ** 1.6
        alpha = (0.45 if s["link"] else 0.95) * (0.55 + 0.45 * t)
        col = COLOURS.get(s["kind"], COLOURS["other"])
        glow_r = core * (3.2 + 2.5 * t)
        g = cairo.RadialGradient(x, y, 0, x, y, glow_r)
        g.add_color_stop_rgba(0, *pk.rgb(col)[:3], alpha * 0.55)
        g.add_color_stop_rgba(0.35, *pk.rgb(col)[:3], alpha * 0.14)
        g.add_color_stop_rgba(1, *pk.rgb(col)[:3], 0)
        cr.set_source(g)
        cr.arc(x, y, glow_r, 0, 2 * math.pi)
        cr.fill()
        cr.set_source_rgba(*pk.rgb(col)[:3], alpha)
        cr.arc(x, y, core, 0, 2 * math.pi)
        cr.fill()
        if t > 0.86:  # the very largest get diffraction spikes
            cr.set_source_rgba(*pk.rgb(col)[:3], 0.35 * alpha)
            cr.set_line_width(0.6)
            L = core * 7
            cr.move_to(x - L, y)
            cr.line_to(x + L, y)
            cr.move_to(x, y - L)
            cr.line_to(x, y + L)
            cr.stroke()

    # Constellation names.
    def spaced(word):
        return " ".join(word.upper())
    for f, (cx, cy, r) in sorted(centres.items(), key=lambda kv: -len(fams[kv[0]]))[:26]:
        halo_text(fig, cx, cy + r + 14, spaced(f), size=8.5, color="#97a3c0", anchor="middle")

    # A few named stars.
    by_name = {s["name"]: s for s in stars}
    for name in labels:
        s = by_name.get(name)
        if not s:
            continue
        x, y = s["x"], s["y"]
        tw = fig.text_width(name, 10, italic=True, family="Noto Serif")
        d = -1 if x + 13 + tw > W - 12 else 1  # flip to the left near the right edge
        cr.new_path()
        cr.set_source_rgba(*pk.rgb("#9aa6c4")[:3], 0.5)
        cr.set_line_width(0.6)
        cr.move_to(x + 3 * d, y - 3)
        cr.line_to(x + 11 * d, y - 11)
        cr.stroke()
        halo_text(fig, x + 13 * d, y - 13, name, size=10, italic=True, color="#c3cce2", family="Noto Serif",
                  anchor="start" if d > 0 else "end")

    # Caption and key.
    x0, y0 = CAPTION_BOX[0] + 8, CAPTION_BOX[1] + 26
    fig.text(x0, y0, caption_lines[0], size=15, color="#e8ecf6", bold=False, family="Noto Serif")
    yy = y0 + 22
    for line in caption_lines[1:]:
        fig.text(x0, yy, line, size=10.5, color="#9aa6c4")
        yy += 16
    yy += 10
    kx = x0
    key = [("elf", "compiled program", False), ("script", "script", False), ("elf", "alias (symlink)", True),
           ("dangling", "link to nothing", False), ("forbidden", "not mine to read", False)]
    for kind, label, link in key:
        cr.new_path()  # show_text leaves a current point; don't let the arc connect to it
        if kind == "dangling":
            cr.set_source_rgba(*pk.rgb("#7b86a3")[:3], 0.75)
            cr.set_line_width(0.9)
            cr.arc(kx + 4, yy - 4, 2.6, 0, 2 * math.pi)
            cr.stroke()
        else:
            col = COLOURS[kind]
            cr.set_source_rgba(*pk.rgb(col)[:3], 0.45 if link else 0.95)
            cr.arc(kx + 4, yy - 4, 2.0, 0, 2 * math.pi)
            cr.fill()
        kx += 12
        kx += fig.text(kx, yy, label, size=10, color="#9aa6c4") + 18
    fig.save(out_png)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="/bin")
    ap.add_argument("--out", default="sky.png")
    ap.add_argument("--catalog", default=None, help="optional JSON star catalogue to write")
    ap.add_argument("--title", default="The night sky over /bin")
    ap.add_argument("--when", default="")
    a = ap.parse_args()

    stars = survey(a.dir)
    fams, centres = layout(stars)
    n = len(stars)
    dang = sum(s["kind"] == "dangling" for s in stars)
    forb = sum(s["kind"] == "forbidden" for s in stars)
    sizes = [s["size"] for s in stars if s["size"] > 0]

    def human(b):
        for unit in ("B", "KB", "MB", "GB"):
            if b < 1024 or unit == "GB":
                return f"{b:.0f} {unit}" if unit == "B" else f"{b:.1f} {unit}"
            b /= 1024

    lines = [a.title,
             f"{n:,} programs, each one a point of light. {len(centres)} families form constellations.",
             f"Brightness is file size ({human(min(sizes))} to {human(max(sizes))}). "
             f"{dang} links point at nothing; {forb} files were not mine to read.",
             ]
    if a.when:
        lines.append(a.when)
    labels = ["sleep", "rtcwake", "whoami", "yes", "true", "false", "espeak-ng", "factor", "cal", "tac",
              "look", "wait", "write", "python3", "bash"]
    draw(stars, fams, centres, a.out, lines, labels)
    if a.catalog:
        with open(a.catalog, "w") as f:
            json.dump([{k: s[k] for k in ("name", "family", "kind", "link", "size", "x", "y")} for s in stars],
                      f, separators=(",", ":"))
    print(f"{n} stars, {len(centres)} constellations, {dang} dark rings, {forb} embers -> {a.out}")


if __name__ == "__main__":
    main()

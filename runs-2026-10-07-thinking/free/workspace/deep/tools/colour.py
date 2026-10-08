"""Colour raw .nu frames: per-frame (lo, scale) from percentiles, smoothed over time.
usage: colour.py <nu_dir> <out_dir> [smooth_window]"""
import glob, os, sys
import numpy as np
from PIL import Image

src, dst = sys.argv[1], sys.argv[2]
win = int(sys.argv[3]) if len(sys.argv) > 3 else 21
os.makedirs(dst, exist_ok=True)
files = sorted(glob.glob(os.path.join(src, "*.nu")))

def load(fn):
    with open(fn, "rb") as f:
        W, H, ss = np.frombuffer(f.read(12), np.int32)
        return np.frombuffer(f.read(), np.float32).reshape(H, W, ss * ss)

# pass 1: robust statistics per frame (in log space)
stats = []
for fn in files:
    v = load(fn); e = v[v >= 0]
    lo = np.percentile(e, 0.5) if e.size else 1.0
    md = np.percentile(e, 50) if e.size else 2.0
    stats.append((np.log(max(lo, 1)), np.log(max(md - lo, 1))))
stats = np.array(stats)
if len(stats) > 1:  # moving average with edge padding => no flicker
    k = min(win, len(stats)) | 1
    pad = np.pad(stats, ((k // 2, k // 2), (0, 0)), mode="edge")
    stats = np.stack([np.convolve(pad[:, i], np.ones(k) / k, "valid") for i in range(2)], 1)

phase = np.array([0.0, 0.10, 0.20])
for fn, (llo, lsc) in zip(files, stats):
    v = load(fn).astype(np.float64)
    inside = v < 0
    lo, sc = np.exp(llo), np.exp(lsc)
    t = np.log1p(np.maximum(v - 0.9 * lo, 0) / sc) * 1.4 + 0.35
    rgb = 0.5 + 0.5 * np.cos(2 * np.pi * (t[..., None] + phase))
    rgb[inside] = (0.03, 0.03, 0.08)
    img = (rgb.mean(axis=2) * 255).clip(0, 255).astype(np.uint8)
    Image.fromarray(img).save(os.path.join(dst, os.path.basename(fn)[:-3] + ".png"))
print("coloured", len(files), "frames")

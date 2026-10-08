"""Check the sky catalogue's claims, and compare it with /bin as it is now (stat + readlink only)."""
import json, os, re, sys
from collections import Counter
cat = json.load(open(sys.argv[1])); D = sys.argv[2]
kinds = Counter(s["kind"] for s in cat); fams = Counter(s["family"] for s in cat)
print("stars:", len(cat), dict(kinds))
print("families with >= 6 members:", sum(1 for f, n in fams.items() if n >= 6),
      "| llvm:", fams.get("llvm"), "| tpm:", fams.get("tpm"), "| top:", fams.most_common(8))
sizes = [s["size"] for s in cat if s["size"] > 0]
print(f"size range: {min(sizes)} B to {max(sizes)/1024**2:.1f} MiB  (largest: {max(cat, key=lambda s: s['size'])['name']})")
print("the one 'other':", [s["name"] for s in cat if s["kind"] == "other"])
print("not readable:", sorted(s["name"] for s in cat if s["kind"] == "forbidden"))
dang = sorted(s["name"] for s in cat if s["kind"] == "dangling")
print("dangling now -> target:")
for n in dang:
    p = os.path.join(D, n)
    t = os.readlink(p) if os.path.islink(p) else "(not a link now)"
    print(f"   {n:28s} -> {t}   {'still dangling' if not os.path.exists(p) else 'RESOLVES NOW'}")
# compare with /bin now
now = {}
for n in os.listdir(D):
    try: now[n] = os.stat(os.path.join(D, n)).st_size
    except OSError: now[n] = 0
old = {s["name"]: s["size"] for s in cat}
print(f"/bin now: {len(now)} entries; added {sorted(set(now)-set(old))}; removed {sorted(set(old)-set(now))}")
changed = [(n, old[n], now[n]) for n in old if n in now and old[n] != now[n]]
print(f"size changed since the night: {len(changed)}", changed[:10])

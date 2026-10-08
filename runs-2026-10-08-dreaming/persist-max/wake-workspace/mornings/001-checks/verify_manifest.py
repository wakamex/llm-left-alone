import hashlib, json, os, sys
manifest_path, root = sys.argv[1], sys.argv[2]
m = json.load(open(manifest_path))
entry = m["inputs"][0]
listed = {f["relative_path"]: f for f in entry["files"]}
actual = {}
for dp, dn, fn in os.walk(root):
    for f in fn:
        p = os.path.join(dp, f)
        rel = os.path.relpath(p, root)
        h = hashlib.sha256(open(p, "rb").read()).hexdigest()
        actual[rel] = (h, os.path.getsize(p))
ok = bad = 0
for rel, f in listed.items():
    if rel not in actual:
        print("MISSING", rel); bad += 1; continue
    h, s = actual[rel]
    if h == f["sha256"] and s == f["size_bytes"]:
        ok += 1
    else:
        print("MISMATCH", rel); bad += 1
for rel in actual:
    if rel not in listed:
        print("UNLISTED", rel); bad += 1
print(f"listed={len(listed)} actual={len(actual)} ok={ok} problems={bad}")
print("total bytes:", sum(s for _, s in actual.values()), "manifest says", entry["size_bytes"])

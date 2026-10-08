#!/usr/bin/env python3
"""
residue.py: write down the "day residue", a snapshot of harmless facts about the machine a dream
happens on, so the next dream can see what changed.

Deliberately NOT collected: environment variables, anything in $HOME (config, credentials,
history), process command lines, network addresses. Only coarse, public-ish facts.

    python3 -I residue.py                      # print JSON
    python3 -I residue.py --out residue/2026-10-08.json
    python3 -I residue.py --diff old.json      # compare a fresh snapshot with an old one
"""
import argparse
import datetime as dt
import hashlib
import importlib
import json
import os
import platform
import shutil
import subprocess
import sys

TOOLS = ["python3", "node", "gcc", "clang", "java", "dotnet", "perl", "sqlite3", "ffmpeg", "convert",
         "pandoc", "espeak-ng", "curl", "git", "cmake", "make"]
PY_MODULES = ["numpy", "scipy", "PIL", "cairo", "matplotlib", "pandas", "torch", "sklearn", "sympy"]


def meminfo():
    out = {}
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                k, v = line.split(":", 1)
                if k in ("MemTotal", "MemAvailable", "SwapTotal", "SwapFree"):
                    out[k] = int(v.split()[0]) * 1024
    except OSError:
        pass
    return out


def disk(path):
    try:
        st = os.statvfs(path)
        return {"total": st.f_blocks * st.f_frsize, "free": st.f_bavail * st.f_frsize}
    except OSError:
        return None


def runs(cmd):
    """Does this tool actually start? (ffmpeg here is installed but can't load libjack.)"""
    try:
        p = subprocess.run(cmd, capture_output=True, timeout=10)
        return p.returncode == 0
    except Exception:
        return False


def snapshot():
    now = dt.datetime.now(dt.timezone.utc)
    try:
        import pwd
        name = pwd.getpwuid(os.getuid()).pw_name
    except (KeyError, ImportError):
        name = None  # whoami: cannot find name for user ID 1000
    with open("/proc/uptime") as f:
        uptime = float(f.read().split()[0])
    bin_names = sorted(os.listdir("/bin")) if os.path.isdir("/bin") else []
    mods = {}
    for m in PY_MODULES:
        try:
            mods[m] = getattr(importlib.import_module(m), "__version__", "present")
        except Exception:
            mods[m] = None
    return {
        "taken_utc": now.isoformat(timespec="seconds"),
        "hostname": platform.node(),
        "kernel": platform.release(),
        "uid": os.getuid(),
        "user_name": name,
        "uptime_hours": round(uptime / 3600, 2),
        "loadavg": os.getloadavg(),
        "cpus": os.cpu_count(),
        "memory_bytes": meminfo(),
        "disks": {p: disk(p) for p in ("/", "/tmp", "/workspace", "/scratch", "/usr")},
        "root_is_tmpfs": _root_fs() == "tmpfs",
        "inputs_listing": sorted(os.listdir("/inputs")) if os.path.isdir("/inputs") else None,
        "bin": {"count": len(bin_names),
                "names_sha256": hashlib.sha256("\n".join(bin_names).encode()).hexdigest()},
        "tools_on_path": {t: bool(shutil.which(t)) for t in TOOLS},
        "tools_that_run": {"ffmpeg": runs(["ffmpeg", "-version"]), "espeak-ng": runs(["espeak-ng", "--version"])},
        "python": sys.version.split()[0],
        "python_modules": mods,
        "fontconfig_has_config": os.path.exists("/etc/fonts/fonts.conf"),
    }


def _root_fs():
    try:
        with open("/proc/mounts") as f:
            for line in f:
                parts = line.split()
                if len(parts) > 2 and parts[1] == "/":
                    return parts[2]
    except OSError:
        pass
    return None


VOLATILE = ("taken_utc", "loadavg", "uptime_hours")


def diff(old, new, prefix=""):
    """Changes worth mentioning. Numbers must move by more than 10% (free memory and disk wobble constantly)."""
    lines = []
    for k in sorted(set(old) | set(new)):
        a, b = old.get(k), new.get(k)
        if isinstance(a, dict) and isinstance(b, dict):
            lines += diff(a, b, prefix + k + ".")
        elif k in VOLATILE or a == b:
            continue
        elif isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool) \
                and abs(b - a) <= 0.10 * max(abs(a), abs(b), 1):
            continue
        else:
            lines.append(f"{prefix}{k}: {a!r} -> {b!r}")
    return lines


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out")
    ap.add_argument("--diff", help="an older snapshot to compare against")
    a = ap.parse_args()
    snap = snapshot()
    if a.diff:
        with open(a.diff) as f:
            old = json.load(f)
        changes = diff(old, snap)
        print("\n".join(changes) if changes else "no changes worth mentioning")
        return
    text = json.dumps(snap, indent=2)
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        with open(a.out, "w") as f:
            f.write(text + "\n")
        print(f"wrote {a.out}")
    else:
        print(text)


if __name__ == "__main__":
    main()

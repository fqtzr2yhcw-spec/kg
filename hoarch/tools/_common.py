"""Shared paths and helpers for the build and release tools (run them from the hoarch folder,
or from anywhere: they find the package themselves)."""
import importlib
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))      # .../hoarch
OUT = os.path.join(ROOT, "out")
PY = sys.executable
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def building(key):
    """The building module hoarch.buildings.<key>."""
    return importlib.import_module("hoarch.buildings." + key)


def logdir(key):
    d = os.path.join(OUT, key, "u")
    os.makedirs(d, exist_ok=True)
    return d


def run(args, log, label):
    """Run a python module or script (``args`` without the interpreter) from ROOT, its output
    to ``log``; returns True when it exits cleanly. Prints one line either way."""
    t0 = time.time()
    with open(log, "w") as f:
        r = subprocess.run([PY] + args, cwd=ROOT, stdout=f, stderr=subprocess.STDOUT)
    dt = time.time() - t0
    state = "ok" if r.returncode == 0 else f"FAILED (exit {r.returncode}, see {os.path.relpath(log, ROOT)})"
    print(f"  {label:<14s} {state}  {dt / 60:.1f} min", flush=True)
    return r.returncode == 0


def progress(line):
    """Append a summary line to out/progress.log and print it."""
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "progress.log"), "a") as f:
        f.write(line + "\n")
    print(line, flush=True)


def last_line(path, needle, default="?"):
    """The last line of ``path`` that contains ``needle``."""
    if not os.path.exists(path):
        return default
    hits = [ln.strip() for ln in open(path, errors="replace") if needle in ln]
    return hits[-1] if hits else default

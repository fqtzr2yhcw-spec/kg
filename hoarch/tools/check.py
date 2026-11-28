"""Full check of buildings, one after another:

  1. build, check for interfering parts, export the plates and slice them (PrusaSlicer);
  2. the print checks (tools/printcheck.py);
  3. the glue audit (tools/glue_audit.py);
  4. the owner's rules audit (hoarch.audit);
  5. the showcase renders, every view in the building's palette (skip with --no-render).

Logs go to out/<b>/u/, renders to out/<b>/showcase/, and one summary line per building to
out/progress.log.

usage: python3 tools/check.py <building> [...] [--no-render] [--samples 48] [--res 1400x960]
"""
import argparse
import json
import os
import time

from _common import OUT, last_line, logdir, progress, run


def check(key, render=True, samples=48, res="1400x960"):
    print(f"== {key}", flush=True)
    u = logdir(key)
    ok = run(["-m", f"hoarch.buildings.{key}", "check", "export"], os.path.join(u, "final.log"), "build+export")
    if not ok:
        progress(f"{key} check FAILED {time.strftime('%H:%M')} (build or export, see out/{key}/u/final.log)")
        return False
    run(["tools/printcheck.py", key], os.path.join(u, "printcheck.log"), "print check")
    run(["tools/glue_audit.py", key], os.path.join(u, "glue_audit.txt"), "glue audit")
    run(["-m", "hoarch.audit", key], os.path.join(u, "audit.txt"), "rules audit")
    if render:
        pal = os.path.join(OUT, key, "palette.json")
        views = ",".join(json.load(open(pal))["views"])
        run(["-m", "hoarch.render", "--npz", os.path.join(OUT, key, f"{key}.npz"), "--palette", pal, "--views", views,
             "--samples", str(samples), "--res", res, "--out", os.path.join(OUT, key, "showcase")],
            os.path.join(u, "showcase.log"), "renders")
    glue = os.path.join(u, "glue_audit.txt")
    small = sum(1 for ln in open(glue) if "<-- SMALL" in ln) if os.path.exists(glue) else "?"
    audit = open(os.path.join(u, "audit.txt")).readline().strip() if os.path.exists(os.path.join(u, "audit.txt")) else "?"
    progress(f"{key} checked {time.strftime('%H:%M')} | {last_line(os.path.join(u, 'final.log'), 'interfering')} | "
             f"glue small: {small} | {audit}")
    return True


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("buildings", nargs="+")
    ap.add_argument("--no-render", action="store_true")
    ap.add_argument("--samples", type=int, default=48)
    ap.add_argument("--res", default="1400x960")
    a = ap.parse_args()
    for b in a.buildings:
        check(b, render=not a.no_render, samples=a.samples, res=a.res)

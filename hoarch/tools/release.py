"""Release checked buildings, one after another (run tools/check.py on each first):

  1. the build-stage pictures for the guide (hoarch.stages);
  2. the showcase renders become the package's renders (out/<b>/cycles);
  3. the build guide PDF (hoarch.guide);
  4. the print package and zip, the guide in it (tools/package.py);
  5. the version: the zip renamed <Name>_Print_Files_vX.Y.zip with its VERSION.txt, the older
     release removed (hoarch.versions; add a HISTORY line there first for an update);
  6. the Bambu Studio project for the P2S (hoarch.bambu).

Logs go to out/<b>/u/ and one summary line per building to out/progress.log.

usage: python3 tools/release.py <building> [...] [--no-stages]
"""
import argparse
import glob
import os
import shutil
import time

from _common import OUT, last_line, logdir, progress, run


def release(key, stages=True):
    print(f"== {key}", flush=True)
    u = logdir(key)
    if not os.path.exists(os.path.join(OUT, key, "kit", "manifest.json")):
        progress(f"{key} release FAILED {time.strftime('%H:%M')}: no export (run tools/check.py {key} first)")
        return False
    if stages:
        run(["-m", "hoarch.stages", key], os.path.join(u, "stages.log"), "stage pictures")
    shots = sorted(glob.glob(os.path.join(OUT, key, "showcase", "*.png")))
    if shots:
        cyc = os.path.join(OUT, key, "cycles")
        shutil.rmtree(cyc, ignore_errors=True)
        os.makedirs(cyc)
        for s in shots:
            shutil.copy(s, cyc)
    else:
        print(f"  (no showcase renders in out/{key}/showcase: the zip goes out without renders)")
    steps = [(["-m", "hoarch.guide", key], "guide.log", "build guide"),          # (first, so the zip and its notes have it)
             (["tools/package.py", key], "pkg.log", "package"),
             (["-m", "hoarch.versions", key], "versions.log", "version"),
             (["-m", "hoarch.bambu", key], "bambu.log", "P2S project")]
    for args, log, label in steps:
        if not run(args, os.path.join(u, log), label) and label in ("package", "version"):
            progress(f"{key} release FAILED {time.strftime('%H:%M')} at {label} (see out/{key}/u/{log})")
            return False
    zp = last_line(os.path.join(u, "versions.log"), key)
    progress(f"{key} released {time.strftime('%H:%M')} | {last_line(os.path.join(u, 'pkg.log'), 'parts')} | "
             f"{os.path.basename(zp.split()[-1]) if zp != '?' else '?'}")
    return True


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("buildings", nargs="+")
    ap.add_argument("--no-stages", action="store_true")
    a = ap.parse_args()
    for b in a.buildings:
        release(b, stages=not a.no_stages)

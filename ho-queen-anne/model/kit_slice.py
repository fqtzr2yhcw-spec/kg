"""Slice every plate with PrusaSlicer (Bambu-like profile) and record time and filament."""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.join(HERE, "..", "kit")
INI = os.path.join(HERE, "slicer", "bambu_like.ini")
TMP = os.environ.get("SLICE_TMP", "/tmp/beaumont_gcode")


def parse(gcode):
    out = {}
    with open(gcode, errors="ignore") as fh:
        tail = fh.read()[-40000:]
    m = re.search(r"estimated printing time \(normal mode\) = (.+)", tail)
    out["time"] = m.group(1).strip() if m else "?"
    m = re.search(r"filament used \[g\] = ([\d.]+)", tail)
    out["grams"] = float(m.group(1)) if m else None
    m = re.search(r"total filament cost = ([\d.]+)", tail)
    out["cost"] = float(m.group(1)) if m else None
    return out


def minutes(t):
    mins = 0
    for val, unit in re.findall(r"(\d+)([dhms])", t):
        mins += int(val) * {"d": 1440, "h": 60, "m": 1, "s": 1 / 60}[unit]
    return round(mins)


def main():
    os.makedirs(TMP, exist_ok=True)
    man = json.load(open(os.path.join(KIT, "manifest.json")))
    for pl in man["plates"]:
        src = os.path.join(KIT, pl["file"])
        gc = os.path.join(TMP, os.path.basename(src).replace(".3mf", ".gcode"))
        cmd = ["prusa-slicer", "--export-gcode", "--load", INI, "--dont-arrange",
               "--layer-height", str(pl["layer_mm"]), "--output", gc, src]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
        warn = [l for l in (r.stdout + r.stderr).splitlines()
                if re.search(r"(?i)empty|floating|error|warning|outside|overhang", l)]
        res = parse(gc) if os.path.exists(gc) else {"time": "FAILED", "grams": None, "cost": None}
        pl["slice"] = {**res, "minutes": minutes(res["time"]) if res["time"] not in ("?", "FAILED") else None,
                       "warnings": warn[:6]}
        print(f'{os.path.basename(src):55s} {res["time"]:>14s} {res["grams"]} g  {warn[:2]}', flush=True)
    tot_min = sum(p["slice"]["minutes"] or 0 for p in man["plates"])
    tot_g = sum(p["slice"]["grams"] or 0 for p in man["plates"])
    man["totals"] = {"print_minutes": tot_min, "filament_g": round(tot_g, 1)}
    json.dump(man, open(os.path.join(KIT, "manifest.json"), "w"), indent=1)
    print(f"TOTAL {tot_min // 60} h {tot_min % 60} m, {tot_g:.0f} g")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Slice each unique part with PrusaSlicer (headless) and report print time,
filament, and cost for the whole 1:350 model. Multiplies unique geometries by
how many of each the assembly needs."""
import subprocess, re, os

HERE = os.path.dirname(os.path.abspath(__file__))
# unique geometry -> how many identical copies the model needs
UNIQUE = {"01_base_N": 2, "02_shaft_1of4": 4, "06_setbacks": 1, "07_crown": 1, "08_spire": 1}
LABEL  = {"01_base_N": "base half", "02_shaft_1of4": "shaft band",
          "06_setbacks": "setbacks", "07_crown": "crown", "08_spire": "spire"}
G_PER_MM = 3.14159 * (1.75/2)**2 * 1.24 / 1000.0   # 1.75mm PLA, 1.24 g/cm^3
COST_PER_KG = 25.0                                  # USD/kg filament (edit)

def secs(s):
    h = re.search(r"(\d+)h", s); m = re.search(r"(\d+)m", s); x = re.search(r"(\d+)s", s)
    return (int(h.group(1)) if h else 0)*3600 + (int(m.group(1)) if m else 0)*60 + (int(x.group(1)) if x else 0)

def hms(t):
    return f"{t//3600}h{(t%3600)//60:02d}m"

def slice_one(part):
    gc = f"/tmp/sl_{part}.gcode"
    subprocess.run(["prusa-slicer", "--export-gcode", "--nozzle-diameter", "0.4",
        "--layer-height", "0.2", "--fill-density", "15%", "--support-material",
        "--support-material-threshold", "50", "--output", gc,
        os.path.join(HERE, "stl", part + ".stl")],
        env={**os.environ, "QT_QPA_PLATFORM": "offscreen"},
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    t = f = 0
    try:
        with open(gc, "rb") as fh:
            txt = fh.read().decode("latin1")
        mt = re.search(r"estimated printing time \(normal mode\) = ([^\n]+)", txt)
        mf = re.search(r"filament used \[mm\] = ([\d.]+)", txt)
        t = secs(mt.group(1)) if mt else 0
        f = float(mf.group(1)) if mf else 0.0
    except Exception:
        pass
    return t, f

def main():
    print(f"{'part':12}{'qty':4}{'time/ea':9}{'g/ea':7}{'time*qty':10}{'g*qty':8}")
    print("-"*52)
    TT = TG = 0
    for part, qty in UNIQUE.items():
        t, fmm = slice_one(part)
        g = fmm * G_PER_MM
        TT += t*qty; TG += g*qty
        print(f"{LABEL[part]:12}{qty:<4}{hms(t):9}{g:6.0f} {hms(t*qty):10}{g*qty:7.0f}")
    print("-"*52)
    print(f"{'TOTAL':12}{'9':<4}{'':9}{'':7}{hms(TT):10}{TG:7.0f}")
    print(f"\nWhole model: ~{hms(TT)} print time, ~{TG:.0f} g filament, "
          f"~${TG/1000*COST_PER_KG:.2f} material @ ${COST_PER_KG}/kg")

if __name__ == "__main__":
    main()

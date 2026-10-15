"""Zip everything a print shop needs into kit/Beaumont_HO_Kit_RevB.zip."""
import glob
import json
import os
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.join(HERE, "..", "kit")
NAME = "Beaumont_HO_Kit_RevB"

README = """THE BEAUMONT - HO scale (1:87.1) Queen Anne house kit, Rev B
==============================================================

plates/     12 single-colour print plates (.3mf), parts pre-arranged on a 256 mm bed.
            Open in Bambu Studio / OrcaSlicer / PrusaSlicer. File name = plate number + colour.
parts/      one STL per unique part, already in print orientation.
            File names start with the colour. Quantities are in manifest.json.
guide/      open guide/index.html in a browser: print settings, plate list,
            8 assembly steps with pictures, full parts list.
renders/    full-size renders of the assembled kit.
previews/   top-down picture of each plate.
manifest.json  every part, quantity, size, plate, estimated time and grams.

Print settings (all plates): 0.4 mm nozzle, PLA, no supports,
FIRST LAYER 0.2 mm (the window glass is exactly that layer), 0.12 mm layers after,
2 walls, 15 % infill, brim on the Sage / Gold / Slate / Brick plates.

Estimated per house: {hours} h {mins} m printing, {grams} g filament (PrusaSlicer, Bambu-like profile).
Not yet test-printed: print W2-upper and its window first to check the 0.1 mm fit clearance.
"""


def main():
    man = json.load(open(os.path.join(KIT, "manifest.json")))
    t = man["totals"]
    out = os.path.join(KIT, NAME + ".zip")
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.writestr(f"{NAME}/README.txt", README.format(hours=t["print_minutes"] // 60, mins=t["print_minutes"] % 60,
                                                        grams=round(t["filament_g"])))
        z.write(os.path.join(KIT, "manifest.json"), f"{NAME}/manifest.json")
        for sub, pat in (("plates", "*.3mf"), ("parts", "*.stl"), ("previews", "*.png")):
            for f in sorted(glob.glob(os.path.join(KIT, sub, pat))):
                z.write(f, f"{NAME}/{sub}/{os.path.basename(f)}")
        for f in sorted(glob.glob(os.path.join(KIT, "renders", "final", "*.png"))):
            z.write(f, f"{NAME}/renders/{os.path.basename(f)}")
        for f in sorted(glob.glob(os.path.join(KIT, "renders", "*.png"))):
            z.write(f, f"{NAME}/renders/assembly_{os.path.basename(f)}")
        for f in sorted(glob.glob(os.path.join(KIT, "guide", "**", "*"), recursive=True)):
            if os.path.isfile(f):
                z.write(f, f"{NAME}/guide/{os.path.relpath(f, os.path.join(KIT, 'guide'))}")
    print(out, round(os.path.getsize(out) / 1e6, 1), "MB")


if __name__ == "__main__":
    main()

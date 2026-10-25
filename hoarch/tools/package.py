"""Print package for an exported building: its plates and layout pictures, PRINT_NOTES.txt, the
renders and the build guide, zipped as out/<Name>_Print_Files.zip (hoarch.versions then gives it
its version: python3 -m hoarch.versions <building>).

Needs the building's export (out/<b>/kit, from ``python3 -m hoarch.buildings.<b> check export``)
and its renders in out/<b>/cycles (release.py copies the showcase renders there).

usage: python3 tools/package.py <building> [...]
"""
import glob
import json
import os
import shutil
import sys
import zipfile

from _common import OUT
from hoarch import assembly as AS
from hoarch.versions import version

# slicer warnings that mean a plate won't print as it should; bridging and bed-adhesion notes
# are expected on wall shells and don't count
SERIOUS = ("Floating object part", "Empty layer", "empty layer", "outside", "too tall")


def hm(minutes):
    return f"{int(minutes // 60)} h {int(round(minutes % 60))} m"


def copy_plates(kit, dest):
    """The kit's plates into ``dest`` and their layout pictures into dest/layouts; returns its manifest."""
    man = json.load(open(os.path.join(kit, "manifest.json")))
    os.makedirs(os.path.join(dest, "layouts"), exist_ok=True)
    for pl in man["plates"]:
        shutil.copy(os.path.join(kit, pl["file"]), dest)
        if pl.get("preview") and os.path.exists(os.path.join(kit, pl["preview"])):
            shutil.copy(os.path.join(kit, pl["preview"]), os.path.join(dest, "layouts"))
    return man


def plate_rows(man):
    """The plate table: one row a plate (and a second for its colour change)."""
    rows = []
    for pl in man["plates"]:
        sl = pl.get("slice") or {}
        name = os.path.basename(pl["file"])
        n = len(pl.get("parts") or []) or pl.get("objects", 0)
        rows.append(f"  {name:<36s}  {pl['colour']:<15s}{n:>2d} parts  {sl.get('time', '?'):<14s}"
                    f"{float(sl.get('grams') or 0):>6.1f} g   max height {pl.get('max_height_mm', 0):.1f} mm")
        c = pl.get("change")
        if c:
            at = round(c["at_mm"], 1)
            rows.append(f"{'':40s}-> {c['to']} from {at} mm (add the change on the {at + 0.2:.1f} mm layer at 0.20)")
    return rows


def slice_problems(man):
    out = []
    for pl in man["plates"]:
        w = (pl.get("slice") or {}).get("warnings") or []
        msgs = [m for m in w if any(s in m for s in SERIOUS)]          # (the list mixes object names and messages)
        if msgs:
            out.append((pl["file"], "; ".join(msgs)))
    return out


def notes(key, man, guide_pdf=None):
    if key in AS.NOTES:
        title, assembly, *extra = AS.NOTES[key]
    else:
        title, assembly, *extra = AS.SHOPS[key]
    joinery = AS.JOINERY.get(key, "")
    head = f"{title} - HO 1:87.1 - print notes (version {version(key)}" + (f": {joinery})" if joinery else ")")
    deck = ("\n" + AS.DECK + "\n") if any(pl.get("colour") in ("PorchDeck", "Deck") for pl in man["plates"]) else ""
    cornice = ("\n" + AS.CORNICE_NOTE) if any("CORNICE" in i for p in man["parts"] for i in p["instances"]) else ""
    changes = ("\n" + extra[0]) if extra else ""
    nparts = sum(p["qty"] for p in man["parts"])
    n_chg = sum(1 for pl in man["plates"] if pl.get("change"))
    plate_head = (f"every plate one colour, except {n_chg} with a single filament change at the height given"
                  if n_chg else "every plate one colour")
    tot = man.get("totals", {})
    if guide_pdf:
        head += f"\nThe illustrated build guide, with pictures of each stage, is {os.path.basename(guide_pdf)}."
    text = f"""{head}

{AS.COMMON_TOP}{deck}{cornice}{changes}
Plates ({nparts} parts, {plate_head} - no AMS needed):
""" + "\n".join(plate_rows(man)) + f"""
  TOTAL about {hm(tot.get('print_minutes', 0))}, {tot.get('filament_g', 0):.0f} g (PrusaSlicer estimate; Bambu Studio is usually faster)

Assembly (stacked; each shell, band and ring drops onto a locating lip or ledge on the one below):
{assembly}"""
    bad = slice_problems(man)
    if bad:
        text += "\nSLICE WARNINGS:\n" + "\n".join(f"  {f}: {w}" for f, w in bad) + "\n"
    return text, nparts, bad


def package(key):
    cap = AS.ZIPNAME.get(key, key.capitalize())
    kit = os.path.join(OUT, key, "kit")
    stage = os.path.join(OUT, key, "u", "pkg")
    dest = os.path.join(stage, f"{key}_pkg")
    shutil.rmtree(stage, ignore_errors=True)
    os.makedirs(dest)
    man = copy_plates(kit, os.path.join(dest, f"{cap}_Kit"))
    guide = sorted(glob.glob(os.path.join(OUT, key, "*_Build_Guide.pdf")))
    text, nparts, bad = notes(key, man, guide[0] if guide else None)
    if guide:
        shutil.copy(guide[0], dest)
    if key == "villa" and os.path.exists(os.path.join(OUT, "sampler", "kit", "manifest.json")):
        # the Ashby's detail test plate, to print first
        tkit = os.path.join(OUT, "sampler", "kit")
        tman = json.load(open(os.path.join(tkit, "manifest.json")))
        td = os.path.join(dest, "1_TEST_PLATE_print_first")
        os.makedirs(td)
        for k, tp in enumerate(tman["plates"]):
            tag = "" if k == 0 else "_" + tp["colour"]
            shutil.copy(os.path.join(tkit, tp["file"]), os.path.join(td, f"Ashby_Test_Plate{tag}.3mf"))
            shutil.copy(os.path.join(tkit, tp["preview"]), os.path.join(td, f"Ashby_Test_Plate{tag}_layout.png"))
    open(os.path.join(dest, "PRINT_NOTES.txt"), "w").write(text)
    rd = os.path.join(dest, "Renders")
    os.makedirs(rd)
    for png in sorted(glob.glob(os.path.join(OUT, key, "cycles", "*.png"))):
        shutil.copy(png, os.path.join(rd, f"{cap}_{os.path.basename(png)}"))
    zp = os.path.join(OUT, f"{cap}_Print_Files.zip")
    if os.path.exists(zp):
        os.remove(zp)
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(dest):
            for f in sorted(files):
                full = os.path.join(root, f)
                z.write(full, os.path.relpath(full, stage))
    tot = man.get("totals", {})
    print(f"{key}: {nparts} parts, {hm(tot.get('print_minutes', 0))}, {tot.get('filament_g', 0):.0f} g, "
          f"zip {os.path.getsize(zp) // 1024} KB, slice warnings {len(bad)}")
    return zp, bad


if __name__ == "__main__":
    for key in sys.argv[1:]:
        package(key)

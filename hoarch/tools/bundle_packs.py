"""One zip of every scenery pack and flatcar load (everything in hoarch/packs.py, none of the
buildings): each one's current print-file zip and Bambu Studio project, the loads' listings sheet,
and an INDEX.txt. Run the packs' export first (python3 -m hoarch.packs all render export).

usage: python3 tools/bundle_packs.py
"""
import glob
import os
import re
import sys
import time
import zipfile

from _common import OUT
from hoarch.packs import PACKS
from hoarch.versions import version


def current(pattern):
    """The newest versioned file matching ``pattern`` (..._v1.2.zip beats ..._v1.10.zip correctly)."""
    def key(p):
        m = re.search(r"_v(\d+)\.(\d+)\.", os.path.basename(p))
        return (int(m.group(1)), int(m.group(2))) if m else (0, 0)
    hits = glob.glob(os.path.join(OUT, pattern))
    return max(hits, key=key) if hits else None


def bundle():
    name = f"HO_Scenery_Packs_and_Flatcar_Loads_{time.strftime('%Y-%m-%d')}.zip"
    top = name[:-4]
    path = os.path.join(OUT, name)
    index = [f"{top.replace('_', ' ')}", "",
             "Every scenery pack and flatcar load, each as its print-file zip (plates, README with the print",
             "notes, LISTING with the listing text, renders) and its Bambu Studio project for the P2S.", ""]
    missing = []
    with zipfile.ZipFile(path, "w", zipfile.ZIP_STORED) as z:            # (the zips inside are compressed already)
        for kind, folder in (("scenery pack", "Scenery_Packs"), ("flatcar load", "Flatcar_Loads")):
            index += [folder.replace("_", " ").upper(), ""]
            for key, pk in PACKS.items():
                if pk.get("kind", "scenery pack") != kind:
                    continue
                zp = current(f"{pk['zipname']}_Print_Files_v*.zip")
                pj = current(f"{pk['zipname']}_P2S_v*.3mf")
                if not zp:
                    missing.append(key)
                    continue
                for f in (zp, pj):
                    if f:
                        z.write(f, f"{top}/{folder}/{os.path.basename(f)}")
                index.append(f"  {pk['title']:<40s} v{version(key):<5s} ${pk['listing']['price']:<6s} {os.path.basename(zp)}")
            index.append("")
        sheet = os.path.join(OUT, "listings", "HO_Flatcar_Loads_Pricing_and_Listings.md")
        if os.path.exists(sheet):
            z.write(sheet, f"{top}/{os.path.basename(sheet)}")
            index += ["The flatcar loads' prices, eBay and Etsy titles, tags, item specifics and descriptions:",
                      f"  {os.path.basename(sheet)}", ""]
        z.writestr(f"{top}/INDEX.txt", "\n".join(index) + "\n")
    print(path, f"{os.path.getsize(path) / 1e6:.1f} MB")
    if missing:
        print("MISSING (export them first):", ", ".join(missing))
        sys.exit(1)
    return path


if __name__ == "__main__":
    bundle()

"""Release versions of the print-file zips.

Every zip the owner has had carries v1.0; each later update to a building adds a line to
``HISTORY`` and bumps its minor version (v1.1, v1.2, ...). The packaging pipeline writes
``<Name>_Print_Files.zip``; ``release`` then adds a VERSION.txt (the building's change history)
and renames it ``<Name>_Print_Files_v1.1.zip``, removing the older release of that building, so
out/ holds one current zip per building.

    python3 -m hoarch.versions camellia fowler    # release those buildings
    python3 -m hoarch.versions --all              # every building (untouched ones as v1.0)
"""

import glob
import os
import re
import sys
import zipfile

from . import assembly as AS

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out")

BRACKETS_16 = ("Cornice brackets made solid and 1.6 mm thick (were 0.7-0.9 mm); their piercings "
               "are now sunk 0.3 mm into each face instead of cut through, so they no longer "
               "print as loose strings. Reprint the cornice parts with brackets (the -upper parts).")

# key -> [(version, date, change), ...], oldest first; v1.0 (the first release) is implied
INSERTS_DEEP = ("Windows and doors: the glass sits 3 layers deeper in the opening, so every sash bar, rail, "
                "door leaf and panel stands at least 3 layers thicker over it (at 1-2 layers the glass colour "
                "showed through); the plug now goes 2.2 mm into the wall. Reprint the WIN- and DOOR- parts.")

HISTORY = {
    "villa": [("1.1", "2026-09-30", INSERTS_DEEP + " The doors' upper lights now open to their glass, as designed.")],
    "camellia": [("1.1", "2026-09-27", "Tower, bay and eave cornice ring brackets: " + BRACKETS_16)],
    "fowler": [("1.1", "2026-09-27", "Fan brackets: " + BRACKETS_16)],
    "marigold": [("1.1", "2026-09-27", "Sawn brackets: " + BRACKETS_16)],
    "hollis": [("1.1", "2026-09-27", "Knee brackets: " + BRACKETS_16)],
    "carrow": [("1.1", "2026-09-27", "Volute brackets: " + BRACKETS_16)],
    "rosecroft": [("1.1", "2026-09-27", "Fret brackets: " + BRACKETS_16)],
    "hawthorn": [("1.1", "2026-09-27", "Ladder brackets: " + BRACKETS_16)],
}


def version(key):
    h = HISTORY.get(key)
    return h[-1][0] if h else "1.0"


def _stem(key):
    return AS.ZIPNAME.get(key, key.capitalize()) + "_Print_Files"


def zip_path(key):
    """The building's current zip: the freshly packaged one if there is one, else its release."""
    fresh = os.path.join(OUT, _stem(key) + ".zip")
    return fresh if os.path.exists(fresh) else os.path.join(OUT, f"{_stem(key)}_v{version(key)}.zip")


def _version_txt(key):
    lines = [f"{AS.ZIPNAME.get(key, key.capitalize()).replace('_', ' ')} print files, "
             f"version {version(key)}", "",
             "v1.0  the first release"]
    for v, date, change in HISTORY.get(key, []):
        lines.append(f"v{v}  {date}  {change}")
    return "\n".join(lines) + "\n"


def release(key):
    """Rename the building's zip to its versioned name (with VERSION.txt inside); drop older releases."""
    target = os.path.join(OUT, f"{_stem(key)}_v{version(key)}.zip")
    fresh = os.path.join(OUT, _stem(key) + ".zip")
    olds = [p for p in glob.glob(os.path.join(OUT, _stem(key) + "_v*.zip"))
            if re.fullmatch(re.escape(_stem(key)) + r"_v\d+\.\d+\.zip", os.path.basename(p))]
    src = fresh if os.path.exists(fresh) else (max(olds, key=os.path.getmtime) if olds else None)
    if src is None:
        return None
    tmp = target + ".tmp"
    with zipfile.ZipFile(src) as zi, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zo:
        names = zi.namelist()
        top = names[0].split("/")[0]
        for n in names:
            if not n.endswith("/VERSION.txt"):
                zo.writestr(zi.getinfo(n), zi.read(n))
        zo.writestr(f"{top}/VERSION.txt", _version_txt(key))
    os.replace(tmp, target)
    for p in olds + [fresh]:
        if os.path.exists(p) and os.path.abspath(p) != os.path.abspath(target):
            os.remove(p)
    return target


if __name__ == "__main__":
    args = sys.argv[1:]
    from .guide import BUILDINGS
    keys = [k for k, _ in BUILDINGS] if "--all" in args else [a for a in args if not a.startswith("--")]
    for k in keys:
        print(k, release(k))

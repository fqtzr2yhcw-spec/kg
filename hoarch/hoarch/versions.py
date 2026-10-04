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
QUOINS = ("Corner quoins: bigger, flat-faced stones 0.9 mm proud with a solid core in the corner, so the "
          "joints there are shallow notches (the old thin, bevelled blocks with open gaps printed as a ragged "
          "fringe up the corner). Walls only: reprint the WALLS- parts if your corners came out fringed.")

HISTORY = {
    "villa": [("1.1", "2026-09-30", INSERTS_DEEP + " The doors' upper lights now open to their glass, as designed. "
               "WALLS-1: the front and back doors sit 0.8 mm higher, leaving a 6-layer strip of wall under each "
               "(at 2 layers the wall could kink at the front door); reprint WALLS-1 only if yours kinked, or glue "
               "the door in with the wall seated on the foundation lip to hold it straight."),
              ("1.2", "2026-10-01", QUOINS)],
    "camellia": [("1.1", "2026-09-27", "Tower, bay and eave cornice ring brackets: " + BRACKETS_16), ("1.2", "2026-09-30", INSERTS_DEEP)],
    "fowler": [("1.1", "2026-09-27", "Fan brackets: " + BRACKETS_16), ("1.2", "2026-09-30", INSERTS_DEEP)],
    "marigold": [("1.1", "2026-09-27", "Sawn brackets: " + BRACKETS_16), ("1.2", "2026-09-30", INSERTS_DEEP)],
    "hollis": [("1.1", "2026-09-27", "Knee brackets: " + BRACKETS_16), ("1.2", "2026-09-30", INSERTS_DEEP)],
    "carrow": [("1.1", "2026-09-27", "Volute brackets: " + BRACKETS_16), ("1.2", "2026-09-30", INSERTS_DEEP)],
    "rosecroft": [("1.1", "2026-09-27", "Fret brackets: " + BRACKETS_16), ("1.2", "2026-09-30", INSERTS_DEEP)],
    "hawthorn": [("1.1", "2026-09-27", "Ladder brackets: " + BRACKETS_16), ("1.2", "2026-09-30", INSERTS_DEEP)],
    "beaumont": [("1.1", "2026-09-30", INSERTS_DEEP)],
    "harcourt": [("1.1", "2026-09-30", INSERTS_DEEP), ("1.2", "2026-10-01", QUOINS),
                 ("1.3", "2026-10-04", "Iron cresting redrawn so a 0.4 mm nozzle prints it: the old cresting's "
                  "bars and rails were 0.4-0.5 mm wide with pointed spears and 0.8 mm balls, and most of it did "
                  "not print. The new one (barbed spears and balls in turn over a top rail, a ball hanging in "
                  "each panel) has every member at least 0.9 mm wide, every opening at least 0.8 mm, blunt spear "
                  "tips and 1.0 mm strips; 5.4 mm tall on the roof and tower, 4.4 mm on the bay. Reprint the "
                  "CREST, TOWER-crest and BAY-crest strips (the Iron plates).")],
    "whitby": [("1.1", "2026-09-30", INSERTS_DEEP)],
    "delancey": [("1.1", "2026-09-30", INSERTS_DEEP)],
    "ardmore": [("1.1", "2026-09-30", INSERTS_DEEP)],
    "merritt": [("1.1", "2026-09-30", INSERTS_DEEP)],
    "pemberton": [("1.1", "2026-09-30", INSERTS_DEEP)],
    "barber": [("1.1", "2026-09-30", INSERTS_DEEP)],
    "bank": [("1.1", "2026-09-30", INSERTS_DEEP)],
    "general": [("1.1", "2026-09-30", INSERTS_DEEP)],
    "drugstore": [("1.1", "2026-09-30", INSERTS_DEEP)],
    "hotel": [("1.1", "2026-09-30", INSERTS_DEEP)],
    "bakery": [("1.1", "2026-09-30", INSERTS_DEEP)],
    "hardware": [("1.1", "2026-09-30", INSERTS_DEEP)],
    "millinery": [("1.1", "2026-09-30", INSERTS_DEEP)],
    "jeweler": [("1.1", "2026-09-30", INSERTS_DEEP)],
    "primrose": [("1.1", "2026-09-30", INSERTS_DEEP)],
    "twins": [("1.1", "2026-09-30", INSERTS_DEEP)],
    "larkspur": [("1.1", "2026-09-30", INSERTS_DEEP)],
    "juniper": [("1.1", "2026-09-30", INSERTS_DEEP)],
    "wisteria": [("1.1", "2026-09-30", INSERTS_DEEP)],
    "magnolia": [("1.1", "2026-09-30", INSERTS_DEEP)],
    "whitmore": [("1.1", "2026-09-30", INSERTS_DEEP),
        ("1.2", "2026-10-04", "PORTICO-pilaster: the storey's belt course cut each pilaster in two, leaving its capital loose above the belt; the pilaster now stops under the belt with its capital there. Reprint the pilasters.")],
    "pennock": [("1.1", "2026-09-30", INSERTS_DEEP)],
    "oakhurst": [("1.1", "2026-09-30", INSERTS_DEEP),
                 ("1.2", "2026-10-04", "ROOF: a loose wedge no longer floats inside the roof under the cupola "
                  "(the tip of the support under its pocket, which was cut deeper than the support reached); the "
                  "cupola's pocket now has a solid floor joined to the roof shell. Reprint ROOF.")],
    "vantassel": [("1.1", "2026-09-30", INSERTS_DEEP)],
    "hathaway": [("1.1", "2026-09-30", INSERTS_DEEP)],
    "chatham": [("1.1", "2026-09-30", INSERTS_DEEP)],
    "winthrop": [("1.1", "2026-09-30", INSERTS_DEEP)],
    "westbrook": [("1.1", "2026-09-30", INSERTS_DEEP),
        ("1.2", "2026-10-04", "ROOF: the chimney's pocket now has a solid floor joined to the roof shell; before, only the loose tip of the support under it floated inside the hollow roof. Reprint ROOF.")],
    "ellsworth": [("1.1", "2026-09-30", INSERTS_DEEP),
        ("1.2", "2026-10-04", "PORCH-deck: a loose 1.5 x 3 mm scrap of planking is gone; no need to reprint.")],
    "fairhaven": [("1.1", "2026-09-30", INSERTS_DEEP)],
    "prescott": [("1.1", "2026-09-30", INSERTS_DEEP)],
    "bellerive": [("1.1", "2026-09-30", INSERTS_DEEP)],
    "pinckney": [("1.1", "2026-09-30", INSERTS_DEEP),
        ("1.2", "2026-10-04", "PIAZZA-steps-0: a 0.3 mm skin on its back face (an offcut of the cut against the deck, too thin to print) is gone; no need to reprint.")],
    "randolph": [("1.1", "2026-09-30", INSERTS_DEEP),
        ("1.2", "2026-10-04", "ROOF: the chimney's pocket now has a solid floor joined to the roof shell; before, only the loose tip of the support under it floated inside the hollow roof. Reprint ROOF.")],
    "stauffer": [("1.1", "2026-09-30", INSERTS_DEEP)],
    "porter": [("1.1", "2026-09-30", INSERTS_DEEP),
        ("1.2", "2026-10-04", "PORCH-steps-0: a 0.3 mm skin on its back face (an offcut of the cut against the deck, too thin to print) is gone; no need to reprint.")],
    "pingree": [("1.1", "2026-09-30", INSERTS_DEEP),
        ("1.2", "2026-10-04", "PORTICO-top: a 0.15 mm skin cut loose along its back edge (too thin to print) is gone; no need to reprint.")],
    "alvarado": [("1.1", "2026-09-30", INSERTS_DEEP)],
    "brenton": [("1.1", "2026-09-30", INSERTS_DEEP)],
    "ridgely": [("1.1", "2026-09-30", INSERTS_DEEP)],
    "arroyo": [("1.1", "2026-09-30", INSERTS_DEEP)],
    "hollister": [("1.1", "2026-09-30", INSERTS_DEEP),
        ("1.2", "2026-10-04", "ROOF: the pier under the chimney now runs up into the roof shell; it stopped just short of it and printed as a loose block. Reprint ROOF. PORCH-steps-0: a 0.3 mm skin on its back face (an offcut of the cut against the deck, too thin to print) is gone; no need to reprint.")],
    "wrightwood": [("1.1", "2026-09-30", INSERTS_DEEP)],
    "ashcombe": [("1.1", "2026-09-30", INSERTS_DEEP)],
    "capistrano": [("1.1", "2026-09-30", INSERTS_DEEP)],
    "kittredge": [("1.1", "2026-09-30", INSERTS_DEEP),
        ("1.2", "2026-10-04", "PORCH-top: two loose fascia offcuts at the wall (14 mm strips 0.35 mm off the top) are gone; reprint only if yours came loose.")],
    "pullman": [("1.1", "2026-09-30", INSERTS_DEEP)],
    "lindenwald": [("1.1", "2026-09-30", INSERTS_DEEP),
        ("1.2", "2026-10-04", "ROOF: the chimney's pocket now has a solid floor joined to the roof shell; before, only the loose tip of the support under it floated inside the hollow roof. Reprint ROOF. PORCH-top: a 0.15 mm skin cut loose along its back edge (too thin to print) is gone; no need to reprint. PORCH-steps-0: a 0.3 mm skin on its back face (an offcut of the cut against the deck, too thin to print) is gone; no need to reprint.")],
    "stickley": [("1.1", "2026-09-30", INSERTS_DEEP),
        ("1.2", "2026-10-04", "PORCH-top: a 0.15 mm skin cut loose along its back edge (too thin to print) is gone; no need to reprint. PORCH-steps-0: a 0.3 mm skin on its back face (an offcut of the cut against the deck, too thin to print) is gone; no need to reprint. STOOP-back: a 0.3 mm skin on its back face (an offcut of the cut against the deck, too thin to print) is gone; no need to reprint.")],
    "sandoval": [("1.1", "2026-09-30", INSERTS_DEEP),
        ("1.2", "2026-10-04", "PORCH-steps-0: a 0.3 mm skin on its back face (an offcut of the cut against the deck, too thin to print) is gone; no need to reprint.")],
    "millbrook": [("1.1", "2026-09-30", INSERTS_DEEP),
        ("1.2", "2026-10-04", "ROOF: the piers under the two stove flues now run up into the roof shell; they stopped just short of it and printed as loose blocks. Reprint ROOF. PLATFORM-top: a loose offcut of its flat top (under the canopy, by the agent's bay) is gone; no need to reprint. PLATFORM-steps-0: a 0.3 mm skin on its back face (an offcut of the cut against the deck, too thin to print) is gone; no need to reprint.")],
    "brendan": [("1.1", "2026-09-30", INSERTS_DEEP)],
    "harmon": [("1.1", "2026-09-30", INSERTS_DEEP)],
    "engine3": [("1.1", "2026-09-30", INSERTS_DEEP)],
    "lakeshore": [("1.1", "2026-09-30", INSERTS_DEEP)],
    "pleasant": [("1.1", "2026-09-30", INSERTS_DEEP)],
    "thorne": [("1.1", "2026-09-30", INSERTS_DEEP)],
    "mxtower": [("1.1", "2026-09-30", INSERTS_DEEP)],
    "blackwater": [("1.1", "2026-09-30", INSERTS_DEEP)],
    "enginehouse": [("1.1", "2026-09-30", INSERTS_DEEP)],
    "yardoffice": [("1.1", "2026-09-30", INSERTS_DEEP),
        ("1.2", "2026-10-04", "ROOF: the pier under the chimney now runs up into the roof shell; it stopped just short of it and printed as a loose block. Reprint ROOF.")],
    "shanty": [("1.1", "2026-09-30", INSERTS_DEEP)],
    "fontaine": [("1.1", "2026-10-03", "An open terrace (no roof over it) joins the two verandas in front of the "
                  "tower door: PORCH-deck is now one deck under both verandas and the terrace (it replaces "
                  "VERANDA-W-deck and VERANDA-E-deck); two TERRACE-rail pieces (tulip balusters between "
                  "ball-capped newels, printed upright) drop into sockets round its open edges; TERRACE-steps "
                  "come down at the door in place of STOOP-front, and the verandas' own steps are gone. "
                  "TOWER-DOME no longer carries the loose square the crest groove cut off its top. Reprint "
                  "PORCH-deck, TERRACE-rail-0 and -1, TERRACE-steps and TOWER-DOME; the rest is unchanged.")],
    "sandhouse": [("1.1", "2026-10-04", "ROOF: the pier under the chimney now runs up into the roof shell; it stopped just short of it and printed as a loose block. Reprint ROOF.")],
    "greenfield": [("1.1", "2026-10-04", "STEPS-0: a 0.3 mm skin on its back face (an offcut of the cut against the deck, too thin to print) is gone; no need to reprint.")],
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

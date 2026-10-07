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
    "hotel": [("1.1", "2026-09-30", INSERTS_DEEP),
        ("1.2", "2026-10-04", "The balcony's iron railings redrawn so a 0.4 mm nozzle prints them: 1.0 mm rails, 0.9 mm bars, rings and stems, every opening 0.8 mm or more (the bars were 0.6 mm and the rings 0.5). Reprint RAIL-front and RAIL-end.")],
    "bakery": [("1.1", "2026-09-30", INSERTS_DEEP)],
    "hardware": [("1.1", "2026-09-30", INSERTS_DEEP),
        ("1.2", "2026-10-04", "The iron shutters' rim, straps and rivets are two nozzle lines wide (the 0.5 mm rim printed as a hairline). Reprint the SHUTTER parts.")],
    "millinery": [("1.1", "2026-09-30", INSERTS_DEEP)],
    "jeweler": [("1.1", "2026-09-30", INSERTS_DEEP)],
    "primrose": [("1.1", "2026-09-30", INSERTS_DEEP)],
    "twins": [("1.1", "2026-09-30", INSERTS_DEEP),
        ("1.2", "2026-10-04", "Myrtle's fleur-de-lis cresting made printable with a 0.4 mm nozzle: drawn at half size and doubled, every member 0.9 mm or more (they were 0.4-0.6 mm), 7.2 mm tall (was 3.6). Reprint M-CRESTING.")],
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
                  "cupola's pocket now has a solid floor joined to the roof shell. Reprint ROOF."),
                 ("1.3", "2026-10-04", "PEDIMENT: the fan in the tympanum printed its rays and hub as loose "
                  "strands - they started 0.6 mm above the fan's sunk floor, held only at their tips. They now "
                  "stand on that floor, and the rays taper from 0.9 mm at the hub to 1.5 mm at the ring (they "
                  "were 0.5 mm, one nozzle line). Reprint PEDIMENT."),
                 ("1.4", "2026-10-07", "Doors: the leaded lozenge glazing in the front door's sidelights and "
                  "transom, the back door's transom and the two French doors had 0.5 mm bars 0.8 mm apart and "
                  "printed as a blur. Each light now holds bold lozenges fitted to it: 0.9 mm bars, openings of "
                  "0.9 mm or more, one large lozenge in each French door pane; the French doors' rails and "
                  "stiles are 0.9 mm. Reprint DOOR-18.8x34.0, DOOR-11.0x28.0 (both) and DOOR-11.0x30.0.")],
    "vantassel": [("1.1", "2026-09-30", INSERTS_DEEP),
        ("1.2", "2026-10-05", "DORMER-roof: the shed dormer's shakes floated up to 0.35 mm above the roof slab "
         "(the slab was laid at a slightly shallower pitch than the shakes), so their first layer printed in "
         "the air; the slab now follows the dormer's pitch and the shakes sit on it. Reprint DORMER-roof.")],
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
    "pinckney": [("1.1", "2026-09-30", INSERTS_DEEP)],
    "randolph": [("1.1", "2026-09-30", INSERTS_DEEP),
        ("1.2", "2026-10-04", "ROOF: the chimney's pocket now has a solid floor joined to the roof shell; before, only the loose tip of the support under it floated inside the hollow roof. Reprint ROOF.")],
    "stauffer": [("1.1", "2026-09-30", INSERTS_DEEP)],
    "porter": [("1.1", "2026-09-30", INSERTS_DEEP)],
    "pingree": [("1.1", "2026-09-30", INSERTS_DEEP),
        ("1.2", "2026-10-04", "PORTICO-top: a 0.15 mm skin cut loose along its back edge (too thin to print) is gone; no need to reprint.")],
    "alvarado": [("1.1", "2026-09-30", INSERTS_DEEP)],
    "brenton": [("1.1", "2026-09-30", INSERTS_DEEP)],
    "ridgely": [("1.1", "2026-09-30", INSERTS_DEEP)],
    "arroyo": [("1.1", "2026-09-30", INSERTS_DEEP),
        ("1.2", "2026-10-05", "PORCH-top: the porch's lap-sided walls had their siding grooves cut right through, "
         "so each wall printed in two strips joined only at the piers, the upper one starting as a loose strand. "
         "The grooves are now sunk 0.15 mm into each face of a 1.2 mm wall. Reprint PORCH-top.")],
    "hollister": [("1.1", "2026-09-30", INSERTS_DEEP),
        ("1.2", "2026-10-04", "ROOF: the pier under the chimney now runs up into the roof shell; it stopped just short of it and printed as a loose block. Reprint ROOF.")],
    "wrightwood": [("1.1", "2026-09-30", INSERTS_DEEP)],
    "ashcombe": [("1.1", "2026-09-30", INSERTS_DEEP)],
    "capistrano": [("1.1", "2026-09-30", INSERTS_DEEP)],
    "kittredge": [("1.1", "2026-09-30", INSERTS_DEEP),
        ("1.2", "2026-10-04", "PORCH-top: two loose fascia offcuts at the wall (14 mm strips 0.35 mm off the top) are gone; reprint only if yours came loose.")],
    "pullman": [("1.1", "2026-09-30", INSERTS_DEEP)],
    "lindenwald": [("1.1", "2026-09-30", INSERTS_DEEP),
        ("1.2", "2026-10-04", "ROOF: the chimney's pocket now has a solid floor joined to the roof shell; before, only the loose tip of the support under it floated inside the hollow roof. Reprint ROOF. PORCH-top: a 0.15 mm skin cut loose along its back edge (too thin to print) is gone; no need to reprint.")],
    "stickley": [("1.1", "2026-09-30", INSERTS_DEEP),
        ("1.2", "2026-10-04", "PORCH-top: a 0.15 mm skin cut loose along its back edge (too thin to print) is gone; no need to reprint."),
        ("1.3", "2026-10-05", "SLEEP-top: the sleeping porch's shingled parapet had its course grooves cut right "
         "through, so it printed as strips joined only at the posts, each starting as a loose strand. The grooves "
         "are now sunk 0.15 mm into each face of a 1.2 mm parapet. Reprint SLEEP-top.")],
    "sandoval": [("1.1", "2026-09-30", INSERTS_DEEP)],
    "millbrook": [("1.1", "2026-09-30", INSERTS_DEEP),
        ("1.2", "2026-10-04", "ROOF: the piers under the two stove flues now run up into the roof shell; they stopped just short of it and printed as loose blocks. Reprint ROOF. PLATFORM-top: a loose offcut of its flat top (under the canopy, by the agent's bay) is gone; no need to reprint.")],
    "brendan": [("1.1", "2026-09-30", INSERTS_DEEP)],
    "harmon": [("1.1", "2026-09-30", INSERTS_DEEP)],
    "engine3": [("1.1", "2026-09-30", INSERTS_DEEP)],
    "lakeshore": [("1.1", "2026-09-30", INSERTS_DEEP)],
    "pleasant": [("1.1", "2026-09-30", INSERTS_DEEP)],
    "thorne": [("1.1", "2026-09-30", INSERTS_DEEP)],
    "mxtower": [("1.1", "2026-09-30", INSERTS_DEEP)],
    "blackwater": [("1.1", "2026-09-30", INSERTS_DEEP),
        ("1.2", "2026-10-04", "The hoist's smokestack has a 0.95 mm wall (at 0.7 mm it printed as a single line). Reprint STACK.")],
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
                  "PORCH-deck, TERRACE-rail-0 and -1, TERRACE-steps and TOWER-DOME; the rest is unchanged."),
        ("1.2", "2026-10-04", "Iron cresting made printable with a 0.4 mm nozzle: the same design drawn at half size and doubled, so every bar, rail and ornament is at least 0.9 mm wide (they were 0.4-0.6 mm and did not print) and the openings stay open; it now stands 6.8-7.2 mm tall, about twice before. The tridents' prongs are a touch heavier. Reprint the iron cresting strips (the Iron plates).")],
    "sandhouse": [("1.1", "2026-10-04", "ROOF: the pier under the chimney now runs up into the roof shell; it stopped just short of it and printed as a loose block. Reprint ROOF.")],
    "montclair": [("1.1", "2026-10-04", "Iron cresting made printable with a 0.4 mm nozzle: the same design drawn at half size and doubled, so every bar, rail and ornament is at least 0.9 mm wide (they were 0.4-0.6 mm and did not print) and the openings stay open; it now stands 6.4 mm tall, about twice before. Reprint the iron cresting strips (the Iron plates).")],
    "lafayette": [("1.1", "2026-10-04", "Iron cresting made printable with a 0.4 mm nozzle: the same design drawn at half size and doubled, so every bar, rail and ornament is at least 0.9 mm wide (they were 0.4-0.6 mm and did not print) and the openings stay open; it now stands 7.2 mm tall, about twice before. Reprint the iron cresting strips (the Iron plates).")],
    "delacroix": [("1.1", "2026-10-04", "Iron cresting made printable with a 0.4 mm nozzle: the same design drawn at half size and doubled, so every bar, rail and ornament is at least 0.9 mm wide (they were 0.4-0.6 mm and did not print) and the openings stay open; it now stands 6.8-7.2 mm tall, about twice before. Its small rings, which would have printed shut, are now solid bosses. Reprint the iron cresting strips (the Iron plates).")],
    "valcour": [("1.1", "2026-10-04", "Iron cresting made printable with a 0.4 mm nozzle: the same design drawn at half size and doubled, so every bar, rail and ornament is at least 0.9 mm wide (they were 0.4-0.6 mm and did not print) and the openings stay open; it now stands 6.8-7.2 mm tall, about twice before. Reprint the iron cresting strips (the Iron plates).")],
    "chevalier": [("1.1", "2026-10-04", "Iron cresting made printable with a 0.4 mm nozzle: the same design drawn at half size and doubled, so every bar, rail and ornament is at least 0.9 mm wide (they were 0.4-0.6 mm and did not print) and the openings stay open; it now stands 7.2 mm (5.6 on the bays) tall, about twice before. The hearts are a touch heavier, and the bays now carry the house's own cresting instead of a plain spear pattern. Reprint the iron cresting strips (the Iron plates).")],
    "marchand": [("1.1", "2026-10-04", "Iron cresting made printable with a 0.4 mm nozzle: the same design drawn at half size and doubled, so every bar, rail and ornament is at least 0.9 mm wide (they were 0.4-0.6 mm and did not print) and the openings stay open; it now stands 6.8-7.2 mm tall, about twice before. Reprint the iron cresting strips (the Iron plates).")],
    "rochambeau": [("1.1", "2026-10-04", "Iron cresting made printable with a 0.4 mm nozzle: the same design drawn at half size and doubled, so every bar, rail and ornament is at least 0.9 mm wide (they were 0.4-0.6 mm and did not print) and the openings stay open; it now stands 6.4-7.2 mm tall, about twice before. The portico's balcony railing is drawn the same way and stays 6.4 mm tall. Reprint the iron cresting strips (the Iron plates).")],
    "beauvais": [("1.1", "2026-10-04", "Iron cresting made printable with a 0.4 mm nozzle: the same design drawn at half size and doubled, so every bar, rail and ornament is at least 0.9 mm wide (they were 0.4-0.6 mm and did not print) and the openings stay open; it now stands 7.2 mm tall, about twice before. Reprint the iron cresting strips (the Iron plates).")],
}


# 2026-10-07: glazing printable with a 0.4 mm nozzle (after the Oakhurst door lattice printed as a blur)
GLAZE_SCRAPS = ("Windows and doors: the little openings in the glazing narrower than 0.9 mm (corner scraps, "
                "fanlight tips, small roundels and lozenges) are filled, so a 0.4 mm nozzle no longer blobs them "
                "the way it did the Oakhurst's door lattice; the larger lights are unchanged. Reprint the WIN- and "
                "DOOR- parts.")
GLAZE_LEADED = ("the leaded diamond glazing (0.4-0.5 mm leads 1.6-2.1 mm apart, openings under 0.9 mm) printed as "
                "a blur. It is redrawn as bold lozenges fitted to each light, 0.9 mm leads and openings of 0.9 mm or "
                "more, as on the Oakhurst's doors; little scraps elsewhere in the glazing are filled. ")
_GLAZE = {
    "brendan": "Lancet windows: " + GLAZE_LEADED + "Reprint every lancet WIN- part.",
    "bank": "Doors: the iron grille over the leaves' glass (0.5 mm bars 1.6 mm apart) printed as a blur; it is "
            "redrawn with 0.9 mm bars and openings of 0.9 mm or more, and little scraps in the glazing are "
            "filled. Reprint the DOOR- parts.",
    "ellsworth": "Doors: the sidelights' " + GLAZE_LEADED + "Reprint the DOOR- parts (and any WIN- part with "
                 "a fanlight).",
    "carrow": "Windows: the upper sashes' " + GLAZE_LEADED + "Reprint the WIN- parts.",
    "hollis": "Doors: the transoms' " + GLAZE_LEADED + "Reprint the DOOR- parts.",
    "whitby": "Windows: the diamond-paned lancet's " + GLAZE_LEADED + "Reprint WIN-8.0x21.0 and any other "
              "WIN- or DOOR- part you printed before.",
    "ashcombe": "Windows: the stone-mullioned windows' " + GLAZE_LEADED + "Reprint the WIN- parts.",
    "porter": "WIN-7.0x10.0, the small gable window: its twelve-over-eight panes were too small to print "
              "(under 0.8 mm); it is now six over six. Little scraps elsewhere in the glazing are filled. "
              "Reprint WIN-7.0x10.0.",
}
for _k in ("pullman", "beaumont", "kittredge", "larkspur", "pingree", "hawthorn", "wrightwood", "pinckney",
           "magnolia", "fairhaven", "juniper", "jeweler", "camellia", "vantassel", "twins", "winthrop",
           "montclair", "belcourt", "ridgely", "hardware", "primrose", "valcour", "hollister", "delancey",
           "hathaway", "hotel", "wisteria", "drugstore", "alvarado"):
    _GLAZE[_k] = GLAZE_SCRAPS
for _k, _note in _GLAZE.items():
    _h = HISTORY.setdefault(_k, [])
    _maj, _min = (_h[-1][0] if _h else "1.0").split(".")
    _h.append((f"{_maj}.{int(_min) + 1}", "2026-10-07", _note))

# 2026-10-07, second pass: the owner's test print of the Oakhurst's doors showed openings of about 1 mm
# printing as rows of little loops, where the sash windows' 2 mm panes print clean
GLAZE2_SCRAPS = ("Windows and doors: a test print showed glazing openings of about 1 mm print as rows of little "
                 "loops, where panes of 2 mm print clean. The small lights, corner scraps and fanlight-ray tips under "
                 "1.6 mm are now filled (square pane corners and long margin lights are kept). Reprint the WIN- and "
                 "DOOR- parts.")
GLAZE2_LEADED = ("a test print showed the 1 mm openings between the lozenges print as rows of little loops. The "
                 "lozenges are larger now, every opening 1.6 mm or more (a light too narrow for that gets square bars), "
                 "and smaller scraps are filled. ")
_GLAZE2 = {
    "oakhurst": "Doors: the lozenge glazing still printed as little loops (openings about 1 mm, the owner's print). "
                "The sidelights, transoms and French door lights are now divided by square bars into panes of about "
                "2 x 3 mm, which print as cleanly as the sash windows. Reprint DOOR-18.8x34.0, DOOR-11.0x28.0 (both) "
                "and DOOR-11.0x30.0. Middle cornice: it stopped 6 mm short of the wing at both inside corners, "
                "leaving a gap (the owner's print); it now runs up to the wing's cornice, its ends coped to the "
                "wing cornice's profile. Reprint CORNICE-J-lower and CORNICE-J-crown.",
    "bank": "Doors: the grille's lozenges are larger (openings 1.6 mm or more) and the transom's ring is an oval light "
            "tied to the frame at its ends, without the cross bars that cut it into 1 mm pieces; smaller scraps are "
            "filled. Reprint the DOOR- parts.",
    "ellsworth": "Doors: " + GLAZE2_LEADED.replace("a test print", "A test print", 1) + "The oval light is leaded in a "
                 "simple cross and the fanlight has three rays from a solid hub. Reprint the DOOR- parts.",
    "brendan": "Lancet windows: " + GLAZE2_LEADED.replace("a test print", "A test print", 1) + "Reprint every lancet WIN- part.",
    "carrow": "Windows: " + GLAZE2_LEADED.replace("a test print", "A test print", 1) + "Reprint the WIN- parts.",
    "hollis": "Doors: " + GLAZE2_LEADED.replace("a test print", "A test print", 1) + "Reprint the DOOR- parts.",
    "whitby": "Windows: " + GLAZE2_LEADED.replace("a test print", "A test print", 1) + "Reprint WIN-8.0x21.0 and any other "
              "WIN- or DOOR- part you printed before.",
    "ashcombe": "Windows: " + GLAZE2_LEADED.replace("a test print", "A test print", 1) + "Reprint the WIN- parts.",
}
GLAZE2_OTHERS = ()          # filled in once the scan of the exported plates says which other buildings change
for _k in GLAZE2_OTHERS:
    _GLAZE2.setdefault(_k, GLAZE2_SCRAPS)
for _k, _note in _GLAZE2.items():
    _h = HISTORY.setdefault(_k, [])
    _maj, _min = (_h[-1][0] if _h else "1.0").split(".")
    _h.append((f"{_maj}.{int(_min) + 1}", "2026-10-07", _note))

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

"""Scenery and detail packs: what goes in each pack, its colours (the owner's spools), how many
packs one print run makes, the review renders, the print package and the listing copy.

Every piece prints in its colours straight off the plate: one colour, or one filament change at
a height its plate shares. A pack's plates hold ``per_run`` packs, so one run of the plates
stocks that many packs.

usage: python3 -m hoarch.packs <key>... [render] [export] [all]
       (no step names: everything; "all" for every pack)"""
import json
import math
import os
import shutil
import subprocess
import sys
import zipfile

import numpy as np

from . import details as D, packparts as P, scenery as S
from .core import mesh_arrays
from .kit import Kit

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "out")
INI = os.path.join(ROOT, "slicer", "bambu_like.ini")

# the owner's spools (bambu/filament_library.json): name -> hex
SPOOL = {"Caramel": "#AE835B", "Latte Brown": "#D3B7A7", "Bone White": "#E6DFCB", "Cobalt Blue": "#0056B8",
         "Gray": "#8C8D8F", "Light Gray": "#D1D3D5", "Red": "#C12E1F", "Black": "#1A1A1A", "Mistletoe Green": "#3F8E43",
         "Cocoa Brown": "#6F5034", "Black Walnut": "#4F3F24", "Dark Brown": "#7D6556", "Copper Brown Metallic": "#AA6443",
         "Desert Tan": "#E8DBB7", "Bronze": "#847D48", "Iron Gray Metallic": "#43403D", "Silver": "#A6A9AA",
         "Dark Blue": "#042F56", "Ivory White": "#FFFFFF", "White": "#F4F4F2", "Turquoise": "#00B1B7"}
FINISH = {"Copper Brown Metallic": (0.45, 0.5), "Iron Gray Metallic": (0.42, 0.55), "Silver": (0.35, 0.6),
          "Cobalt Blue": (0.45, 0.15), "Dark Blue": (0.25, 0.1), "Turquoise": (0.15, 0.0)}


def _piece(name, fn, colour, qty=1, change=None, show=None, note=""):
    """One kind of piece in a pack: built by ``fn`` in its print pose, ``qty`` of them per pack,
    in ``colour`` (a SPOOL name) or with ``change`` = (height, colour above). ``show``: how it
    stands in the renders ("stand" for face-up panels, "plant" for signs with a spike)."""
    return {"name": name, "fn": fn, "colour": colour, "qty": qty, "change": change, "show": show, "note": note}


PACKS = {
    "pallets": dict(
        title="Loaded Pallets", zipname="Loaded_Pallets_Pack", per_run=3,
        blurb="Ten loaded 48 x 40 in stringer pallets and a stack of empties for docks, warehouses and team tracks. "
              "The pallets print in wood colour and the loads in their own: shipping cartons, cement sacks, 55 gallon "
              "drums and concrete blocks.",
        pieces=[_piece("Pallet-cartons", D.load_cartons, "Caramel", 3, (D.PALLET_TOP, "Latte Brown")),
                _piece("Pallet-sacks", D.load_sacks, "Caramel", 3, (D.PALLET_TOP, "Bone White")),
                _piece("Pallet-drums", D.load_drums, "Caramel", 2, (D.PALLET_TOP, "Cobalt Blue")),
                _piece("Pallet-blocks", D.load_blocks, "Caramel", 2, (D.PALLET_TOP, "Gray")),
                _piece("Pallet-stack", D.pallet_stack, "Caramel", 1)],
        listing=dict(price="12.99", title="HO Scale Loaded Pallets 11 pc | Cartons Sacks Drums Blocks | Printed in Color, No Painting | 1:87",
                     tags=["ho scale pallets", "model railroad loads", "ho scale details", "1:87 diorama", "warehouse details",
                           "loading dock", "train layout scenery", "ho scale drums", "industrial details", "model train gift",
                           "3d printed scenery", "ho scale crates", "railroad diorama"])),
    "drums": dict(
        title="Oil Drums and Barrels", zipname="Oil_Drums_and_Barrels_Pack", per_run=4,
        blurb="Twenty-four 55 gallon steel drums with rolled chimes, rolling hoops and bungs, six each in blue, red, black "
              "and green, plus six bulged wooden barrels with iron hoops.",
        pieces=[_piece("Drum-blue", lambda: D._drum(0, 0, 0), "Cobalt Blue", 6),
                _piece("Drum-red", lambda: D._drum(0, 0, 0), "Red", 6),
                _piece("Drum-black", lambda: D._drum(0, 0, 0), "Black", 6),
                _piece("Drum-green", lambda: D._drum(0, 0, 0), "Mistletoe Green", 6),
                _piece("Barrel", P.barrel, "Cocoa Brown", 6)],
        listing=dict(price="11.99", title="HO Scale 55 Gallon Oil Drums 24 + Wooden Barrels 6 | Printed in Color | 1:87 Model Railroad",
                     tags=["ho scale oil drums", "ho scale barrels", "55 gallon drum", "model railroad details", "1:87 scale",
                           "diorama barrels", "train layout", "ho scale details", "industrial scenery", "gas station details",
                           "3d printed", "railroad scenery", "model train gift"])),
    "walls": dict(
        title="Retaining Walls", zipname="Retaining_Walls_Pack", per_run=2,
        blurb="Three kinds of retaining wall in 50 mm panels that lap at their ends, so a run hides its joints: crossties on "
              "steel H-piles, a precast concrete crib wall with the earth fill showing in its cells (printed in two colours), "
              "and board-formed concrete with a coping. Plus a culvert headwall with wingwalls and a corrugated pipe.",
        pieces=[_piece("Wall-ties", D.tie_wall, "Black Walnut", 2, show="stand"),
                _piece("Wall-crib", D.crib_wall, "Dark Brown", 2, (D.CRIB_FILL, "Light Gray"), show="stand"),
                _piece("Wall-concrete", P.concrete_wall, "Light Gray", 2, show="stand"),
                _piece("Culvert-headwall", D.culvert_headwall, "Gray", 1)],
        listing=dict(price="16.99", title="HO Scale Retaining Wall Set | Tie Wall, Concrete Crib, Board-Form Concrete, Culvert | 1:87",
                     tags=["ho scale retaining wall", "model railroad walls", "ho culvert", "crib wall", "tie wall",
                           "1:87 scenery", "train layout", "ho scale details", "railroad scenery", "diorama wall",
                           "3d printed scenery", "model train gift", "concrete wall"])),
    "clutter": dict(
        title="Industrial Clutter", zipname="Industrial_Clutter_Pack", per_run=3,
        blurb="The yard clutter every industry needs: four wooden crates with braces and battens, four hooped barrels, two "
              "stacks of worn tyres, a pyramid of rusty pipe on chocks, and a cable reel with its cable in black.",
        pieces=[_piece("Crate-large", lambda: P.crate(), "Caramel", 1),
                _piece("Crate-long", lambda: P.crate(17.5, 10.5, 8.8), "Caramel", 1),
                _piece("Crate-medium", lambda: P.crate(10.5, 7.0, 7.0), "Caramel", 1),
                _piece("Crate-small", lambda: P.crate(7.0, 7.0, 7.0), "Caramel", 1),
                _piece("Barrel", P.barrel, "Cocoa Brown", 4),
                _piece("Tyre-stack", P.tire_stack, "Black", 2),
                _piece("Pipe-stack", P.pipe_stack, "Copper Brown Metallic", 1),
                _piece("Cable-reel", P.cable_reel, "Caramel", 1, (P.REEL_FLANGE, "Black")),
                _piece("Cable-reel-flange", P.reel_flange, "Caramel", 1, note="glue onto the reel's cable end")],
        listing=dict(price="13.99", title="HO Scale Industrial Clutter Set | Crates Barrels Tires Pipe Cable Reel | Color Printed 1:87",
                     tags=["ho scale clutter", "ho scale crates", "junkyard details", "model railroad details", "1:87 diorama",
                           "industrial scenery", "ho scale tires", "cable reel", "pipe load", "train layout", "3d printed scenery",
                           "model train gift", "ho scale barrels"])),
    "military": dict(
        title="HO Military Defences", zipname="HO_Military_Defences_Pack", per_run=1,
        blurb="Field works for 1:87 military dioramas, where almost nothing is made at this scale: sandbag breastworks two "
              "bags thick (straight, corner and a round gun pit), a row of concrete dragon's teeth, stacked ammunition "
              "boxes and jerrycans, plank and wattle trench revetments, and duckboards.",
        pieces=[_piece("Sandbag-wall", D.sandbag_wall, "Desert Tan", 2),
                _piece("Sandbag-corner", D.sandbag_corner, "Desert Tan", 1),
                _piece("Sandbag-pit", D.sandbag_pit, "Desert Tan", 1),
                _piece("Dragons-teeth", D.teeth_row, "Light Gray", 1),
                _piece("Ammo-boxes", D.ammo_stack, "Bronze", 1),
                _piece("Jerrycans", P.jerrycan_stack, "Bronze", 1),
                _piece("Revetment-planks", P.revetment, "Cocoa Brown", 2, show="stand"),
                _piece("Revetment-wattle", lambda: P.revetment(kind="wattle"), "Cocoa Brown", 2, show="stand"),
                _piece("Duckboard", P.duckboard, "Cocoa Brown", 2)],
        listing=dict(price="17.99", title="1:87 HO Military Diorama Set | Sandbags Gun Pit Dragon's Teeth Trench Revetments | WW2",
                     tags=["1:87 military", "ho scale military", "sandbags", "ww2 diorama", "dragons teeth", "trench",
                           "minitanks diorama", "herpa diorama", "wargame terrain", "gun pit", "military diorama",
                           "3d printed terrain", "roco minitanks"])),
    "mow": dict(
        title="Track Crew Stock", zipname="Track_Crew_Stock_Pack", per_run=3,
        blurb="What a section gang leaves along the right of way: a crisscrossed pile of new crossties, two heaps of old ties "
              "pulled from the track, a rack of relay rail (timbers in wood, rails in steel colour), and spike and tie-plate "
              "kegs on a skid.",
        pieces=[_piece("Tie-pile", D.tie_pile, "Black Walnut", 1),
                _piece("Tie-heap", P.tie_heap, "Black Walnut", 2),
                _piece("Rail-rack", P.rail_rack, "Black Walnut", 1, (P.RACK_TOP, "Iron Gray Metallic")),
                _piece("Kegs", P.keg_cluster, "Cocoa Brown", 2)],
        listing=dict(price="12.99", title="HO Scale Railroad Tie Piles, Rail Rack, Spike Kegs | Maintenance of Way Details | 1:87",
                     tags=["ho scale ties", "tie pile", "maintenance of way", "mow details", "model railroad details",
                           "ho scale rail", "1:87 scale", "railroad scenery", "section house details", "train layout",
                           "3d printed", "model train gift", "right of way"])),
    "modern": dict(
        title="EV Chargers and Rooftop Solar", zipname="EV_Chargers_and_Solar_Pack", per_run=2,
        blurb="Up-to-date details for modern layouts: two curbed EV charging islands with two pedestal chargers and bollards "
              "each, three flush rooftop solar arrays on aluminium rails, four house air-conditioning condensers on pads, and "
              "two commercial rooftop units.",
        pieces=[_piece("EV-island", P.ev_island, "Gray", 2, (P.EV_PAD, "Ivory White")),
                _piece("Solar-2x2", lambda: P.solar_array(2, 2), "Silver", 1, (P.SOLAR_FRAME, "Dark Blue")),
                _piece("Solar-3x2", lambda: P.solar_array(3, 2), "Silver", 1, (P.SOLAR_FRAME, "Dark Blue")),
                _piece("Solar-4x2", lambda: P.solar_array(4, 2), "Silver", 1, (P.SOLAR_FRAME, "Dark Blue")),
                _piece("AC-condenser", P.ac_condenser, "Gray", 4, (P.AC_PAD, "Light Gray")),
                _piece("Rooftop-unit", P.rooftop_unit, "Light Gray", 2)],
        listing=dict(price="14.99", title="HO Scale EV Charging Stations + Rooftop Solar Panels + AC Units | Modern 1:87 Details",
                     tags=["ho scale ev charger", "ho scale solar panels", "modern layout", "ac unit", "rooftop details",
                           "1:87 scale", "model railroad details", "diorama", "electric car charger", "train layout",
                           "3d printed scenery", "model train gift", "hvac"])),
    "cemetery": dict(
        title="Old Cemetery", zipname="Old_Cemetery_Pack", per_run=1,
        blurb="A churchyard for HO, or a Halloween scene: fifteen headstones in five shapes (one leaning), two obelisks, a "
              "Greek-revival family tomb, a cemetery railing on a granite curb with cross-topped posts (curb and iron in "
              "their own colours), and two bare, crooked trees.",
        pieces=[_piece("Headstone-round", lambda: P.headstone("round", 5.0, 8.0), "Light Gray", 3),
                _piece("Headstone-gothic", lambda: P.headstone("gothic", 5.0, 9.0), "Light Gray", 3),
                _piece("Headstone-shouldered", lambda: P.headstone("shoulder", 6.0, 7.0), "Light Gray", 3),
                _piece("Headstone-cross", lambda: P.headstone("cross", 5.0, 9.5), "Light Gray", 3),
                _piece("Headstone-leaning", lambda: P.headstone("tablet", 4.4, 6.0, lean=6.0), "Light Gray", 3),
                _piece("Obelisk", P.obelisk, "Light Gray", 2),
                _piece("Mausoleum", P.mausoleum, "Light Gray", 1),
                _piece("Railing", P.cemetery_fence, "Gray", 4, (P.FENCE_CURB, "Black")),
                _piece("Railing-post", P.cemetery_post, "Gray", 6, (P.FENCE_CURB, "Black")),
                _piece("Dead-tree", P.dead_tree, "Black Walnut", 2)],
        listing=dict(price="19.99", title="HO Scale Cemetery Set | Headstones Mausoleum Iron Fence Dead Trees | Halloween Village 1:87",
                     tags=["ho scale cemetery", "halloween village", "headstones", "tombstones", "graveyard diorama",
                           "1:87 scale", "model railroad", "mausoleum", "spooky village", "halloween decor",
                           "3d printed", "church yard", "iron fence"])),
    "treelot": dict(
        title="Christmas Tree Lot", zipname="Christmas_Tree_Lot_Pack", per_run=2,
        blurb="A winter scene in a box: nine cut firs in three sizes standing in wooden stands (stand and tree in their own "
              "colours), the sales shack in red with a snow-white roof, split-rail lot fence and a TREES sign.",
        pieces=[_piece("Tree-6ft", lambda: P.xmas_tree(21.0, 91), "Cocoa Brown", 4, (P.TREE_STAND, "Mistletoe Green")),
                _piece("Tree-7ft", lambda: P.xmas_tree(24.5, 92), "Cocoa Brown", 3, (P.TREE_STAND, "Mistletoe Green")),
                _piece("Tree-5ft", lambda: P.xmas_tree(17.5, 93), "Cocoa Brown", 2, (P.TREE_STAND, "Mistletoe Green")),
                _piece("Shack", P.lot_shack, "Red", 1, (P.SHACK_EAVE, "Ivory White")),
                _piece("Lot-fence", P.lot_fence, "Cocoa Brown", 3),
                _piece("Sign-TREES", lambda: S.station_sign("TREES", 3.2), "White", 1, (S.ZS, "Red"), show="plant")],
        listing=dict(price="16.99", title="HO Scale Christmas Tree Lot | 9 Trees, Sales Shack, Fence, Sign | Christmas Village 1:87",
                     tags=["ho scale christmas", "christmas tree lot", "christmas village", "winter layout", "1:87 scale",
                           "model railroad christmas", "holiday diorama", "christmas trees", "train layout", "village accessories",
                           "3d printed", "model train gift", "snow scene"])),
    "signs": dict(
        title="Trackside Signs", zipname="Trackside_Signs_Pack", per_run=3,
        blurb="Twenty steam-to-diesel era trackside signs, white with raised black lettering straight off the printer: whistle "
              "posts, mileposts, speed boards, yard-limit boards, flanger signs and two station name boards. Each has a "
              "spike to push into the scenery.",
        pieces=[_piece("Whistle-post", S.whistle_post, "White", 4, (S.ZS, "Black"), show="plant"),
                _piece("Milepost-12", lambda: S.milepost(12), "White", 1, (S.ZS, "Black"), show="plant"),
                _piece("Milepost-37", lambda: S.milepost(37), "White", 1, (S.ZS, "Black"), show="plant"),
                _piece("Milepost-58", lambda: S.milepost(58), "White", 1, (S.ZS, "Black"), show="plant"),
                _piece("Milepost-104", lambda: S.milepost(104), "White", 1, (S.ZS, "Black"), show="plant"),
                _piece("Speed-10", lambda: S.speed_board(10), "White", 1, (S.ZS, "Black"), show="plant"),
                _piece("Speed-25", lambda: S.speed_board(25), "White", 1, (S.ZS, "Black"), show="plant"),
                _piece("Speed-40", lambda: S.speed_board(40), "White", 1, (S.ZS, "Black"), show="plant"),
                _piece("Speed-60", lambda: S.speed_board(60), "White", 1, (S.ZS, "Black"), show="plant"),
                _piece("Yard-limit", S.yard_limit, "White", 2, (S.ZS, "Black"), show="plant"),
                _piece("Flanger-sign", S.flanger_sign, "White", 4, (S.ZS, "Black"), show="plant"),
                _piece("Station-FAIRVIEW", lambda: S.station_sign("FAIRVIEW"), "White", 1, (S.ZS, "Black"), show="plant"),
                _piece("Station-CEDAR-GAP", lambda: S.station_sign("CEDAR GAP"), "White", 1, (S.ZS, "Black"), show="plant")],
        listing=dict(price="10.99", title="HO Scale Railroad Signs 20 pc | Whistle Posts Mileposts Speed Boards Yard Limit | 1:87",
                     tags=["ho scale signs", "railroad signs", "whistle post", "milepost", "model railroad details",
                           "trackside details", "1:87 scale", "yard limit sign", "train layout", "station sign",
                           "3d printed", "model train gift", "transition era"])),
    "poles": dict(
        title="Telephone Poles", zipname="Telephone_Poles_Pack", per_run=2,
        blurb="Six 30 ft creosoted poles with pole steps, printed upright so they stay round, and crossarms that drop over "
              "the pole-top spigot: four-pin and six-pin, the glass insulators printed in aqua. Two pole-top transformers "
              "with saddles shaped to the pole.",
        pieces=[_piece("Pole", P.telephone_pole, "Black Walnut", 6, note="print with a brim"),
                _piece("Crossarm-4pin", P.crossarm, "Cocoa Brown", 4, (P.ARM_TOP, "Turquoise")),
                _piece("Crossarm-6pin", lambda: P.crossarm(6), "Cocoa Brown", 2, (P.ARM_TOP, "Turquoise")),
                _piece("Transformer", P.transformer, "Gray", 2)],
        listing=dict(price="13.99", title="HO Scale Telephone Poles 6 pc with Crossarms, Glass Insulators, Transformers | 1:87",
                     tags=["ho scale telephone poles", "utility poles", "model railroad details", "1:87 scale", "power lines",
                           "telegraph poles", "train layout", "ho scale details", "railroad scenery", "crossarm",
                           "3d printed", "model train gift", "trackside"])),
    "lamps": dict(
        title="Victorian Street Lamps", zipname="Victorian_Street_Lamps_Pack", per_run=4,
        blurb="Six cast-iron street lamps for a Victorian town, two each of three designs: an acorn-globe park lamp, a twin "
              "boulevard lamp and a square platform post. Iron and globes print in their own colours.",
        pieces=[_piece("Lamp-acorn", S.lamp_acorn, "Iron Gray Metallic", 2, (S.ZG, "Ivory White"), note="print with a brim"),
                _piece("Lamp-boulevard", S.lamp_boulevard, "Iron Gray Metallic", 2, (S.ZG, "Ivory White"), note="print with a brim"),
                _piece("Lamp-platform", S.lamp_platform, "Iron Gray Metallic", 2, (S.ZG, "Ivory White"), note="print with a brim")],
        listing=dict(price="12.99", title="HO Scale Victorian Street Lamps 6 pc | Acorn, Boulevard, Platform | Cast Iron Look | 1:87",
                     tags=["ho scale street lamps", "victorian lamp posts", "gas lamps", "model railroad", "1:87 scale",
                           "street lights", "victorian village", "train layout", "dickens village", "diorama",
                           "3d printed", "model train gift", "lamp post"])),
    "ironfence": dict(
        title="Wrought Iron Fence", zipname="Wrought_Iron_Fence_Pack", per_run=1,
        blurb="About 230 mm of Victorian wrought-iron fence on a dressed stone curb: four 48 mm runs with spear bars, dog bars "
              "and an arcade band, five posts with ball finials, and a double gate on two tall gate posts. Curb and iron in "
              "their own colours.",
        pieces=[_piece("Fence-run", S.fence_section, "Gray", 4, (S.ZC, "Black")),
                _piece("Fence-post", S.fence_post, "Gray", 5, (S.ZC, "Black")),
                _piece("Gate-post", lambda: S.fence_post(True), "Gray", 2, (S.ZC, "Black")),
                _piece("Gate", S.fence_gate, "Gray", 1, (S.ZC, "Black"))],
        listing=dict(price="14.99", title="HO Scale Wrought Iron Fence with Gate | Stone Curb, Spear Bars | Victorian 1:87 | No Painting",
                     tags=["ho scale fence", "wrought iron fence", "victorian fence", "model railroad", "1:87 scale",
                           "iron gate", "train layout", "victorian house", "diorama fence", "ho scale details",
                           "3d printed", "model train gift", "garden fence"])),
}


def zipnames():
    return {k: p["zipname"] for k, p in PACKS.items()}


def _colours(pk):
    names = []
    for pc in pk["pieces"]:
        for c in [pc["colour"]] + ([pc["change"][1]] if pc["change"] else []):
            if c not in names:
                names.append(c)
    return {n.replace(" ", "_"): SPOOL[n] for n in names}


def build(key, runs=None):
    """The pack's kit: every piece ``qty`` x per_run times (one print run)."""
    pk = PACKS[key]
    cols = _colours(pk)
    kit = Kit(pk["title"], cols, {c: c.lower() for c in cols})
    runs = pk["per_run"] if runs is None else runs
    for pc in pk["pieces"]:
        m = pc["fn"]()
        ch = None if not pc["change"] else (pc["change"][0], pc["change"][1].replace(" ", "_"))
        for k in range(pc["qty"] * runs):
            kit.add(f"{pc['name']}-{k + 1}", pc["colour"].replace(" ", "_"), m, key=pc["name"], change=ch)
    return kit


def _show(pc, m):
    if pc["show"] == "stand":
        return m.rotate([90, 0, 0])
    if pc["show"] == "plant":
        return m.rotate([90, 0, 0]).translate([0, 0, -2.4])
    return m


def scene(key):
    """One pack's pieces set out on the lawn as they would stand, in their colours:
    {material: [solids]}. Telephone poles get their crossarms and transformers fitted, the cable
    reel its top flange."""
    pk = PACKS[key]
    mats = {}

    def put(colour, m):
        mats.setdefault(colour.replace(" ", "_").lower(), []).append(m)

    def coloured(pc, m):
        """[(colour, solid)] of a piece in its print pose."""
        if not pc["change"]:
            return [(pc["colour"], m)]
        hi, lo = m.split_by_plane((0.0, 0.0, 1.0), pc["change"][0] + 1e-3)
        return [(pc["colour"], lo), (pc["change"][1], hi)]

    items = []
    for pc in pk["pieces"]:
        m = pc["fn"]()
        for _ in range(pc["qty"]):
            items.append((pc, m))
    if key == "poles":
        poles = [it for it in items if it[0]["name"] == "Pole"]
        arms = [it for it in items if it[0]["name"].startswith("Crossarm")]
        xf = [it for it in items if it[0]["name"] == "Transformer"]
        for i, (pc, m) in enumerate(poles):
            x = i * 26.0
            for c, s in coloured(pc, m):
                put(c, s.translate([x, 0, 0]))
            h = m.bounding_box()[5] - 1.4
            if i < len(arms):
                apc, am = arms[i]
                for c, s in coloured(apc, am):
                    put(c, s.translate([x, 0, h - 0.01]))
            if i < len(xf):
                xpc, xm = xf[i]
                for c, s in coloured(xpc, xm):
                    put(c, s.translate([x, 2.3 + 1.33 + 0.5, h - 16.0]))
        return mats
    if key == "clutter":
        flange = [it for it in items if it[0]["name"] == "Cable-reel-flange"]
        items = [it for it in items if it[0]["name"] != "Cable-reel-flange"]
    shown = []
    for pc, m in items:
        s = [(c, _show(pc, x)) for c, x in coloured(pc, m)]
        b = np.array(union_bb([x for _, x in s]))
        shown.append((pc, s, b))
    # shelf-pack the footprints into rows about 170 mm wide
    x = y = row_d = 0.0
    width = 170.0
    for pc, s, b in sorted(shown, key=lambda t: -(t[2][4] - t[2][1])):
        w, d = b[3] - b[0], b[4] - b[1]
        if x > 0 and x + w > width:
            x, y, row_d = 0.0, y + row_d + 6.0, 0.0
        dx, dy = x - b[0], y - b[1]
        for c, sol in s:
            put(c, sol.translate([dx, dy, 0]))
        if pc["name"] == "Cable-reel" and key == "clutter" and flange:
            fpc, fm = flange[0]
            top = b[5]
            put(fpc["colour"], fm.translate([dx + (b[0] + b[3]) / 2, dy + (b[1] + b[4]) / 2, top - 0.01]))
        x += w + 6.0
        row_d = max(row_d, d)
    return mats


def union_bb(ms):
    bbs = np.array([m.bounding_box() for m in ms if not m.is_empty()])
    return [*bbs[:, :3].min(0), *bbs[:, 3:].max(0)]


def render(key, samples=36, res="1600x1000"):
    out = os.path.join(OUT, key)
    os.makedirs(out, exist_ok=True)
    data = {}
    for mat, ms in scene(key).items():
        ms = [m for m in ms if not m.is_empty()]
        vs, fs, o = [], [], 0
        for m in ms:
            v, f = mesh_arrays(m)
            vs.append(v)
            fs.append(f + o)
            o += len(v)
        data[mat + "__v"] = np.concatenate(vs).astype(np.float32)
        data[mat + "__f"] = np.concatenate(fs).astype(np.int32)
    npz = os.path.join(out, f"{key}.npz")
    np.savez_compressed(npz, **data)
    mats = {}
    for name, hexc in SPOOL.items():
        r, mt = FINISH.get(name, (0.75, 0.0))
        mats[name.replace(" ", "_").lower()] = [hexc, r, mt]
    views = {"hero": [-30, 24, 60, 0.95, [0, 0, 0]], "rear": [150, 26, 60, 0.95, [0, 0, 0]]}
    json.dump({"materials": mats, "views": views}, open(os.path.join(out, "palette.json"), "w"), indent=1)
    r = subprocess.run([sys.executable, "-m", "hoarch.render", "--npz", npz, "--palette", os.path.join(out, "palette.json"),
                        "--views", "hero,rear", "--samples", str(samples), "--res", res, "--out", os.path.join(out, "renders")],
                       cwd=ROOT, capture_output=True, text=True)
    if r.returncode:
        print(r.stdout[-2000:], r.stderr[-2000:])
    return os.path.join(out, "renders")


def readme(key, man):
    pk = PACKS[key]
    cols = _colours(pk)
    lines = [f"{pk['title'].upper()} - HO scale (1:87.1) scenery pack", "", pk["blurb"], "",
             f"ONE PACK HOLDS", ""]
    for pc in pk["pieces"]:
        col = pc["colour"] + (f", then {pc['change'][1]} above {pc['change'][0]:.1f} mm" if pc["change"] else "")
        lines.append(f"  {pc['qty']:>2} x {pc['name'].replace('-', ' ')}  ({col})" + (f"  - {pc['note']}" if pc["note"] else ""))
    lines += ["", f"ONE RUN OF THE PLATES MAKES {pk['per_run']} PACK{'S' if pk['per_run'] > 1 else ''}", ""]
    tot_g = 0.0
    for p in man["plates"]:
        sl = p.get("slice") or {}
        tot_g += sl.get("grams") or 0.0
        ch = p.get("change")
        what = p["colour"].replace("_", " ") + (f", change to {ch['to'].replace('_', ' ')} at {ch['at_mm']:.1f} mm" if ch else "")
        lines.append(f"  {os.path.basename(p['file'])}: {p['objects']} pieces, {what}; {sl.get('time', '?')}, {sl.get('grams', '?')} g")
    lines += ["", f"  about {tot_g:.0f} g of filament per run, {tot_g / max(pk['per_run'], 1):.1f} g per pack", "",
              "COLOURS (the spools in the Bambu project)", ""]
    for n, h in cols.items():
        lines.append(f"  {n.replace('_', ' ')}  {h}")
    lines += ["", "PRINTING", "",
              "  0.20 mm layers, no supports. Two-colour plates change filament once, at the height above; the Bambu",
              "  project does it on its own. Single-colour plates print on any printer, the P1S included.",
              "  Tall, slim pieces (poles, lamps) stand better with a brim.", ""]
    return "\n".join(lines)


def listing_text(key, man):
    pk = PACKS[key]
    L = pk["listing"]
    lines = [f"TITLE: {L['title']}", f"PRICE: ${L['price']} (free shipping on orders over $35 suggested)", "", "DESCRIPTION", "",
             pk["blurb"], "", "What's in the pack:"]
    for pc in pk["pieces"]:
        lines.append(f"  - {pc['qty']} x {pc['name'].replace('-', ' ')}")
    lines += ["", "Printed in colour: every piece comes off the printer in its finished colours, so it is ready to place.",
              "HO scale (1:87). Designed and printed by us. Weather them with chalks or washes if you like.", "",
              "TAGS (13): " + ", ".join(L["tags"])]
    return "\n".join(lines) + "\n"


def export(key):
    """Plates, slicing, the print package zip (released as v1.0+), and the Bambu project."""
    from .kit import slice_check
    from . import versions as V, bambu as B
    out = os.path.join(OUT, key)
    kitdir = os.path.join(out, "kit")
    if os.path.isdir(kitdir):
        shutil.rmtree(kitdir)
    kit = build(key)
    man = kit.export(kitdir, layer=0.2)
    man = slice_check(kitdir, INI, layer=0.2, manifest=man)
    stem = PACKS[key]["zipname"] + "_Print_Files"
    top = PACKS[key]["zipname"]
    zpath = os.path.join(OUT, stem + ".zip")
    with open(os.path.join(out, "README.txt"), "w") as fh:
        fh.write(readme(key, man))
    with open(os.path.join(out, "LISTING.txt"), "w") as fh:
        fh.write(listing_text(key, man))
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(os.path.join(out, "README.txt"), f"{top}/README.txt")
        z.write(os.path.join(out, "LISTING.txt"), f"{top}/LISTING.txt")
        for sub in ("plates", "parts", "previews"):
            for f in sorted(os.listdir(os.path.join(kitdir, sub))):
                z.write(os.path.join(kitdir, sub, f), f"{top}/{sub}/{f}")
        for v in ("hero", "rear"):
            p = os.path.join(out, "renders", f"{v}.png")
            if os.path.exists(p):
                z.write(p, f"{top}/renders/{v}.png")
    rel = V.release(key)
    proj = B.write_project(key, verbose=False)[0]
    return rel, proj


if __name__ == "__main__":
    args = sys.argv[1:]
    keys = list(PACKS) if "all" in args else [a for a in args if a in PACKS]
    steps = [a for a in args if a in ("render", "export")] or ["render", "export"]
    for k in keys:
        if "render" in steps:
            print(k, "renders", render(k))
        if "export" in steps:
            print(k, "export", export(k))

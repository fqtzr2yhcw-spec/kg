"""Bambu Studio projects: a building's whole kit in one .3mf for the P2S, coloured from the owner's spools.

Every plate of the kit becomes a plate of the project, laid out as Bambu Studio lays out plates
(a grid, 1.2 bed widths apart). Each plate prints from the owner's spool nearest the design colour
(CIEDE2000 colour difference; matte PLA preferred, then PLA Basic, generic PLA, and wood, metal
or silk last; a spool without enough left for the plate's share is passed over if another is
close). A two-colour plate changes filament on the first layer above its height, the way the
slider's "Change Filament" does; the windows and doors start in black for their two layers of
glass and change to the frame colour above it; plank-floored parts (porch decks, boardwalks,
galleries, docks) start in the plank colour for their first 1.2 mm. A change between two colours
that come out as the same spool is left out. Supports are on for the windows and
doors only (tree, on the build plate only). The prime tower is off: the P2S purges into its chute
at the one change a plate has.

The settings are Bambu Studio's own system presets for the P2S with a 0.4 mm nozzle (0.20mm
Standard @BBL P2S and the filaments' @BBL P2S presets), snapshotted in ../bambu/p2s_profiles.json
by ../bambu/snapshot.py; the owner's spools are ../bambu/filament_library.json (copied from Bambu
Studio's Filament Manager).

    python3 -m hoarch.bambu villa [harcourt ...]   -> out/<Name>_P2S_v1.x.3mf and out/<key>/u/bambu_colours.txt
"""

import colorsys
import datetime
import json
import math
import os
import re
import sys
import zipfile

import numpy as np

from . import assembly as AS
from . import versions as V

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PROFILES = os.path.join(ROOT, "bambu", "p2s_profiles.json")
LIBRARY = os.path.join(ROOT, "bambu", "filament_library.json")
CATALOGUE = os.path.join(ROOT, "bambu", "bambu_pla_colours.json")   # Bambu's plain-finish PLA colours
OUT = os.path.join(ROOT, "out")

BED = 256.0
STRIDE = BED * 1.2          # Bambu Studio's plate pitch (LOGICAL_PART_PLATE_GAP = 1/5)
LAYER = 0.2
GLASS_TOP = 0.4             # openings.GLASS: the windows' glass is their first two layers
PLANK_TOP = 1.2             # the planked parts' boards are their first six layers
GLASS_HEX = "#1E2226"       # aim for the glass: near black
SUPPORTED = ("Windows_Doors", "Addins")       # plates with supports under their frames (windows, doors, mansard add-ins)
DECKS = ("PorchDeck", "Deck", "Boardwalk")   # the kit's plank-floor plates (porches, galleries, docks, platforms)

# (brand, series) -> (Bambu Studio preset, penalty added to the colour difference)
SERIES = {
    ("Bambu Lab", "PLA Matte"): ("Bambu PLA Matte @BBL P2S", 0.0),
    ("Bambu Lab", "PLA Basic"): ("Bambu PLA Basic @BBL P2S", 1.0),
    ("Generic", "PLA"): ("Generic PLA @BBL P2S", 1.5),
    ("eSUN", "PLA+"): ("Generic PLA @BBL P2S", 1.5),
    ("Inland", "PLA"): ("Generic PLA @BBL P2S", 1.5),
    ("Generic", "PLA High Speed"): ("Generic PLA High Speed @BBL P2S", 1.5),
    ("Bambu Lab", "PLA Wood"): ("Bambu PLA Wood @BBL P2S", 3.0),
    ("Bambu Lab", "PLA Metal"): ("Bambu PLA Metal @BBL P2S", 3.0),
    ("Bambu Lab", "PLA Silk+"): ("Bambu PLA Silk+ @BBL P2S", 6.0),
}
SHORT = 12.0                # penalty for a spool without enough left for the plates it would print
GREYED = 5.0                # penalty for printing a coloured part (chroma 8+) in a grey or black


# ------------------------------------------------------------------ colour
def _lab(hexc):
    h = hexc.lstrip("#")[:6]
    rgb = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    x = (0.4124 * lin[0] + 0.3576 * lin[1] + 0.1805 * lin[2]) / 0.95047
    y = 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]
    z = (0.0193 * lin[0] + 0.1192 * lin[1] + 0.9505 * lin[2]) / 1.08883
    f = [t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116 for t in (x, y, z)]
    return 116 * f[1] - 16, 500 * (f[0] - f[1]), 200 * (f[1] - f[2])


def delta_e(h1, h2):
    """CIEDE2000 difference between two hex colours (about 2 is just noticeable, over 10 is clearly another colour)."""
    L1, a1, b1 = _lab(h1)
    L2, a2, b2 = _lab(h2)
    C1, C2 = math.hypot(a1, b1), math.hypot(a2, b2)
    Cm = (C1 + C2) / 2
    G = 0.5 * (1 - math.sqrt(Cm ** 7 / (Cm ** 7 + 25 ** 7)))
    a1p, a2p = a1 * (1 + G), a2 * (1 + G)
    C1p, C2p = math.hypot(a1p, b1), math.hypot(a2p, b2)
    h1p = math.degrees(math.atan2(b1, a1p)) % 360
    h2p = math.degrees(math.atan2(b2, a2p)) % 360
    dLp, dCp = L2 - L1, C2p - C1p
    dh = 0 if C1p * C2p == 0 else (h2p - h1p if abs(h2p - h1p) <= 180 else h2p - h1p - 360 * math.copysign(1, h2p - h1p))
    dHp = 2 * math.sqrt(C1p * C2p) * math.sin(math.radians(dh / 2))
    Lm, Cmp = (L1 + L2) / 2, (C1p + C2p) / 2
    if C1p * C2p == 0:
        hm = h1p + h2p
    elif abs(h1p - h2p) <= 180:
        hm = (h1p + h2p) / 2
    else:
        hm = (h1p + h2p + 360) / 2 if h1p + h2p < 360 else (h1p + h2p - 360) / 2
    T = (1 - 0.17 * math.cos(math.radians(hm - 30)) + 0.24 * math.cos(math.radians(2 * hm))
         + 0.32 * math.cos(math.radians(3 * hm + 6)) - 0.20 * math.cos(math.radians(4 * hm - 63)))
    SL = 1 + 0.015 * (Lm - 50) ** 2 / math.sqrt(20 + (Lm - 50) ** 2)
    SC, SH = 1 + 0.045 * Cmp, 1 + 0.015 * Cmp * T
    RT = (-2 * math.sqrt(Cmp ** 7 / (Cmp ** 7 + 25 ** 7))
          * math.sin(math.radians(60 * math.exp(-((hm - 275) / 25) ** 2))))
    return math.sqrt((dLp / SL) ** 2 + (dCp / SC) ** 2 + (dHp / SH) ** 2 + RT * (dCp / SC) * (dHp / SH))


def flush_volume(src, dst, extra=107):
    """Bambu Studio's colour-based purge estimate (FlushVolCalc::calc_flush_vol_rgb), mm^3."""
    s = [int(src.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    d = [int(dst.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    hs, ss, vs = colorsys.rgb_to_hsv(*s)
    hd, sd, vd = colorsys.rgb_to_hsv(*d)
    dx = math.cos(hs * 2 * math.pi) * ss * vs - math.cos(hd * 2 * math.pi) * sd * vd
    dy = math.sin(hs * 2 * math.pi) * ss * vs - math.sin(hd * 2 * math.pi) * sd * vd
    hs_dist = min(1.2, math.hypot(dx, dy))
    lum = lambda c: c[0] * 0.3 + c[1] * 0.59 + c[2] * 0.11
    fl, tl = lum(s), lum(d)
    if tl >= fl:
        lumi = (tl - fl) ** 0.7 * 560
    else:
        lumi = (fl - tl) * 80
        hs_dist = min(0.67 * vd + 0.33 * vs, hs_dist)
    hsf = 230 * hs_dist
    vol = max(math.sqrt(hsf ** 2 + lumi ** 2 - 2 * hsf * lumi * math.cos(math.radians(120))), 60)
    return int(min(vol + extra, 900))


# ------------------------------------------------------------------ spools
def library():
    """The owner's usable spools merged by filament: [{name, preset, penalty, hex, grams, spools, where}]."""
    out = {}
    for s in json.load(open(LIBRARY)):
        key = (s["brand"], s["series"])
        if key not in SERIES or "glow" in s.get("note", "").lower() or s["grams_left"] < 30:
            continue
        hexc = s["hex"].upper()[:7]
        f = out.setdefault((key, hexc), {
            "name": f"{s['brand']} {s['series']} {s['colour'] or hexc}", "preset": SERIES[key][0],
            "penalty": SERIES[key][1], "hex": hexc, "grams": 0, "spools": 0, "where": []})
        f["grams"] += s["grams_left"]
        f["spools"] += 1
        if s.get("location"):
            f["where"].append(s["location"])
    return list(out.values())


def _chroma(hexc):
    _, a, b = _lab(hexc)
    return math.hypot(a, b)


def pick(target, need, spools):
    """The spool to print ``target`` (hex) with, needing ``need`` grams: (spool, colour difference).
    A coloured part keeps its colour family: a grey or black is passed over for it if a spool of the
    right hue is nearly as close (green shutters stay green)."""
    tc = _chroma(target)

    def cost(f):
        greyed = GREYED if tc >= 8 and _chroma(f["hex"]) < 0.4 * tc else 0
        return delta_e(target, f["hex"]) + f["penalty"] + greyed + (SHORT if f["grams"] < need * 1.15 else 0)
    best = min(spools, key=cost)
    return best, delta_e(target, best["hex"])


# ------------------------------------------------------------------ the kit's plates
def _read_plate(path):
    """Objects of one of the kit's plate .3mf files: [(name, vertices (n,3), triangles (m,3))]."""
    xml = zipfile.ZipFile(path).read("3D/3dmodel.model").decode()
    objs = []
    for m in re.finditer(r'<object id="\d+" name="([^"]*)"[^>]*>(.*?)</object>', xml, re.S):
        v = np.array(re.findall(r'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"', m.group(2)), float)
        t = np.array(re.findall(r'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"', m.group(2)), np.int64)
        objs.append((m.group(1), v, t))
    return objs


def _plan(key):
    """The kit's plates with their colour roles: [{base, parts, objs, start, change (z, hex) or None,
    grams, roles {hex: (colour name, grams)}}]."""
    kit = os.path.join(OUT, key, "kit")
    man = json.load(open(os.path.join(kit, "manifest.json")))
    pal = json.load(open(os.path.join(OUT, key, "palette.json")))
    planks = (pal["materials"].get("planks") or ["#6F5034"])[0]
    plates = []
    for p in man["plates"]:
        base = os.path.splitext(os.path.basename(p["file"]))[0]
        grams = (p.get("slice") or {}).get("grams") or 0.0
        hmax = max(p.get("max_height_mm") or 1.0, 0.4)
        parts = [n.split("__", 1)[-1] for n in p["parts"]]
        col, hexc = p["colour"], p["hex"].upper()
        if col == "Windows_Doors":
            start, change, names = GLASS_HEX, (GLASS_TOP + LAYER, hexc), ("Glass", "Windows and doors")
            split = 0.12
        elif p.get("change"):                      # the kit's own two-colour plates (planks included)
            c = p["change"]
            start, change, names = hexc, (round(c["at_mm"], 2) + LAYER, c["to_hex"].upper()), (col, c["to"])
            split = min(c["at_mm"] / hmax, 0.9)
        elif col in DECKS:
            start, change, names = planks.upper(), (PLANK_TOP + LAYER, hexc), ("Planks", col)
            split = min(PLANK_TOP / hmax, 0.9)
        else:
            start, change, names, split = hexc, None, (col, None), 1.0
        roles = {start: (names[0], grams * split)}
        if change:
            nm, g = roles.get(change[1], (names[1], 0.0))
            roles[change[1]] = (nm, g + grams * (1 - split))
        plates.append({"base": base, "colour": col, "parts": parts, "start": start, "change": change,
                       "grams": grams, "roles": roles, "supports": col in SUPPORTED,
                       "file": os.path.join(kit, p["file"]), "preview": os.path.join(kit, p["preview"])})
    return man, plates


def to_buy(target):
    """The nearest colour in Bambu's plain-finish PLA ranges: (name, hex, colour difference)."""
    c = min(json.load(open(CATALOGUE)), key=lambda c: delta_e(target, c["hex"]) + (0 if c["series"] == "PLA Matte" else 1))
    return f"Bambu Lab {c['series']} {c['colour']}", c["hex"], delta_e(target, c["hex"])


def match(plates, spools):
    """Design colour -> chosen spool for the building, with the grams each needs."""
    need, names = {}, {}
    for p in plates:
        for h, (nm, g) in p["roles"].items():
            need[h] = need.get(h, 0.0) + g
            names.setdefault(h, [])
            if nm not in names[h]:
                names[h].append(nm)
    chosen = {}
    for h in sorted(need, key=lambda h: -need[h]):
        f, de = pick(h, need[h], spools)
        chosen[h] = {"spool": f, "de": de, "need": need[h], "name": " / ".join(n.replace("_", " ") for n in names[h])}
    for p in plates:                               # no change where both colours are the same spool
        if p["change"] and chosen[p["start"]]["spool"] is chosen[p["change"][1]]["spool"]:
            p["change"] = None
    return chosen


# ------------------------------------------------------------------ project settings
def project_config(slots, nplates, P):
    """project_settings.config for the filament slots [(spool)], laid out the way Bambu Studio saves it
    (PresetBundle::full_fff_config): the process, then the printer, then each filament's values side by side
    (the per-nozzle ones three to a filament, for the P2S's standard, high-flow and E3D nozzles)."""
    t, L = P["template"], P["option_lists"]
    fopts = set(L["filament"]) | {"filament_extruder_variant"}
    fvar = set(L["filament_options_with_variant"]) | {"filament_extruder_variant"}
    pv1, pv2 = set(L["printer_options_with_variant_1"]), set(L["printer_options_with_variant_2"])
    printer, process = P["printer"], P["process"]
    nvar = len(printer["printer_extruder_variant"])
    cfg = {}
    # program defaults (from a project Bambu Studio saved), resized for one extruder
    for k, v in t.items():
        if k in fopts:
            continue
        if isinstance(v, list) and k not in ("print_compatible_printers", "start_end_points"):
            if k in pv2:
                v = (v[:1] or [""]) * (2 * nvar)
            elif k in pv1:
                v = (v[:1] or [""]) * nvar
            elif len(v) == 2 or k == "nozzle_type":
                v = v[:1]
        cfg[k] = v
    cfg.update(process)
    cfg.update(printer)
    presets = [P["filaments"][s["preset"]] for s in slots]
    keys = sorted(set().union(*[set(f) for f in presets]) & fopts | {k for k in t if k in fopts})
    for k in keys:
        tv = t.get(k)
        if isinstance(tv, str) or (tv is None and any(isinstance(f.get(k), str) for f in presets)):
            cfg[k] = next((f[k] for f in presets if k in f), tv)          # a scalar: the first filament's
            continue
        vals = []
        for f in presets:
            nv = len(f["filament_extruder_variant"])
            if k in f:
                vals += f[k]
            else:
                d = (tv or [""])[0]
                vals += [d] * (nv if k in fvar else 1)
        cfg[k] = vals
    n = len(slots)
    cfg["filament_colour"] = [s["hex"] for s in slots]
    cfg["filament_settings_id"] = [s["preset"] for s in slots]
    cfg["filament_ids"] = [P["filament_ids"][s["preset"]] for s in slots]
    cfg["filament_self_index"] = [str(i + 1) for i, f in enumerate(presets)
                                  for _ in f["filament_extruder_variant"]]
    cfg["filament_map"] = ["1"] * n
    cfg["default_filament_colour"] = [""] * n
    cfg["filament_notes"] = [s["name"] for s in slots] if isinstance(t.get("filament_notes"), list) else cfg.get("filament_notes", "")
    cfg["inherits_group"] = [""] * (n + 2)
    cfg["compatible_machine_expression_group"] = [""] * (n + 2)
    cfg["compatible_process_expression_group"] = [""] * n
    cfg["different_settings_to_system"] = ["enable_prime_tower"] + [""] * n + [""]
    cfg["enable_prime_tower"] = "0"
    cfg["print_compatible_printers"] = process.get("compatible_printers", [P["printer_name"]])
    cfg["print_settings_id"] = P["process_name"]
    cfg["printer_settings_id"] = P["printer_name"]
    cfg["default_print_profile"] = P["process_name"]
    cfg["flush_volumes_matrix"] = [str(0 if i == j else flush_volume(a["hex"], b["hex"]))
                                   for i, a in enumerate(slots) for j, b in enumerate(slots)]
    cfg["flush_volumes_vector"] = ["140"] * (2 * n)
    cfg["flush_multiplier"] = ["1"]
    cfg["wipe_tower_x"] = [cfg["wipe_tower_x"][0]] * nplates
    cfg["wipe_tower_y"] = [cfg["wipe_tower_y"][0]] * nplates
    cfg["curr_bed_type"] = "Textured PEI Plate"
    cfg["name"], cfg["from"], cfg["version"] = "project_settings", "project", P["bambu_studio_version"]
    for k in ("compatible_printers", "compatible_prints", "inherits", "compatible_printers_condition",
              "compatible_prints_condition"):
        cfg.pop(k, None)
    return cfg


# ------------------------------------------------------------------ the .3mf
def _cols(n):
    """Bambu Studio's plate columns (PartPlate.hpp compute_colum_count)."""
    v = math.sqrt(n)
    r = round(v)
    return int(r + 1 if v > r else r)


def _mesh_xml(oid, v, t):
    vs = "\n".join(f'     <vertex x="{x:.4f}" y="{y:.4f}" z="{z:.4f}"/>' for x, y, z in v)
    ts = "\n".join(f'     <triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in t)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
            'xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" '
            'xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" requiredextensions="p">\n'
            ' <metadata name="BambuStudio:3mfVersion">1</metadata>\n <resources>\n'
            f'  <object id="{oid}" p:UUID="{oid:08x}-81cb-4c03-9d28-80fed5dfa1dc" type="model">\n   <mesh>\n    <vertices>\n'
            f'{vs}\n    </vertices>\n    <triangles>\n{ts}\n    </triangles>\n   </mesh>\n  </object>\n'
            ' </resources>\n <build/>\n</model>\n')


def _esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;"))


def write_project(key, path=None, verbose=True):
    P = json.load(open(PROFILES))
    man, plates = _plan(key)
    spools = library()
    chosen = match(plates, spools)
    # filament slots: one per spool, in the order the plates first use them
    slots, slot_of = [], {}
    for p in plates:
        for h in [p["start"]] + ([p["change"][1]] if p["change"] else []):
            f = chosen[h]["spool"]
            if f["name"] not in slot_of:
                slot_of[f["name"]] = len(slots) + 1
                slots.append(f)
    sid = lambda h: slot_of[chosen[h]["spool"]["name"]]

    title = AS.ZIPNAME.get(key, key.capitalize())
    ver = V.version(key)
    path = path or os.path.join(OUT, f"{title}_P2S_v{ver}.3mf")
    now = datetime.date.today().isoformat()
    cols = _cols(len(plates))
    files, rels, comps, items, settings, plate_xml, gcodes = {}, [], [], [], [], [], []
    oid, ident = 0, 100
    for i, p in enumerate(plates):
        ox, oy = (i % cols) * STRIDE, -(i // cols) * STRIDE
        insts = []
        for (name, v, t) in _read_plate(p["file"]):
            oid += 1
            mesh_id, obj_id = 2 * oid - 1, 2 * oid
            lo, hi = v.min(0), v.max(0)
            c = np.array([(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, lo[2]])
            files[f"3D/Objects/object_{oid}.model"] = _mesh_xml(mesh_id, v - c, t)
            rels.append(f' <Relationship Target="/3D/Objects/object_{oid}.model" Id="rel-{oid}" '
                        'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>')
            comps.append(f'  <object id="{obj_id}" p:UUID="{oid:08x}-61cb-4c03-9d28-80fed5dfa1dc" type="model">\n'
                         f'   <components>\n    <component p:path="/3D/Objects/object_{oid}.model" objectid="{mesh_id}" '
                         f'p:UUID="{oid << 16:08x}-b206-40ff-9872-83e8017abed1" transform="1 0 0 0 1 0 0 0 1 0 0 0"/>\n'
                         '   </components>\n  </object>')
            tx, ty = ox + c[0], oy + c[1]
            items.append(f'  <item objectid="{obj_id}" p:UUID="{oid:08x}-b1ec-4553-aec9-835e5b724bb4" '
                         f'transform="1 0 0 0 1 0 0 0 1 {tx:.4f} {ty:.4f} {c[2]:.4f}" printable="1"/>')
            label = name.split("__", 1)[-1]
            sup = ("".join(f'    <metadata key="{k}" value="{v_}"/>\n' for k, v_ in
                           (("enable_support", "1"), ("support_type", "tree(auto)"),
                            ("support_on_build_plate_only", "1"))) if p["supports"] else "")
            settings.append(f'  <object id="{obj_id}">\n    <metadata key="name" value="{_esc(label)}"/>\n'
                            f'    <metadata key="extruder" value="{sid(p["start"])}"/>\n{sup}'
                            f'    <metadata face_count="{len(t)}"/>\n'
                            f'    <part id="{mesh_id}" subtype="normal_part">\n'
                            f'      <metadata key="name" value="{_esc(label)}"/>\n'
                            '      <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>\n'
                            f'      <mesh_stat face_count="{len(t)}" edges_fixed="0" degenerate_facets="0" '
                            'facets_removed="0" facets_reversed="0" backwards_edges="0"/>\n    </part>\n  </object>')
            ident += 1
            insts.append(f'    <model_instance>\n      <metadata key="object_id" value="{obj_id}"/>\n'
                         '      <metadata key="instance_id" value="0"/>\n'
                         f'      <metadata key="identify_id" value="{ident}"/>\n    </model_instance>')
        s0 = chosen[p["start"]]["spool"]
        pname = f'{p["base"].split("_", 1)[0]} {p["colour"].replace("_", " ")} - {s0["name"]}'
        if p["change"]:
            s1 = chosen[p["change"][1]]["spool"]
            pname += f' -> {s1["name"]} at {p["change"][0]:.1f}'
            gcodes.append(f'<plate>\n<plate_info id="{i + 1}"/>\n'
                          f'<layer top_z="{p["change"][0]:.2f}" type="2" extruder="{sid(p["change"][1])}" '
                          f'color="{s1["hex"]}" extra="" gcode="tool_change"/>\n<mode value="MultiAsSingle"/>\n</plate>')
        thumb = f"Metadata/plate_{i + 1}.png"
        if os.path.exists(p["preview"]):
            files[thumb] = open(p["preview"], "rb").read()
        plate_xml.append('  <plate>\n'
                         f'    <metadata key="plater_id" value="{i + 1}"/>\n'
                         f'    <metadata key="plater_name" value="{_esc(pname)}"/>\n'
                         '    <metadata key="locked" value="false"/>\n'
                         + (f'    <metadata key="thumbnail_file" value="{thumb}"/>\n' if thumb in files else "")
                         + "\n".join(insts) + '\n  </plate>')

    model = ('<?xml version="1.0" encoding="UTF-8"?>\n'
             '<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
             'xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" '
             'xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" requiredextensions="p">\n'
             f' <metadata name="Application">BambuStudio-{P["bambu_studio_version"]}</metadata>\n'
             ' <metadata name="BambuStudio:3mfVersion">1</metadata>\n'
             f' <metadata name="CreationDate">{now}</metadata>\n <metadata name="ModificationDate">{now}</metadata>\n'
             f' <metadata name="Title">{_esc(man["name"])}</metadata>\n'
             + (' <metadata name="Thumbnail_Middle">/Metadata/plate_1.png</metadata>\n' if "Metadata/plate_1.png" in files else "")
             + ' <resources>\n' + "\n".join(comps) + '\n </resources>\n'
             ' <build p:UUID="2c7c17d8-22b5-4d84-8835-1976022ea369">\n' + "\n".join(items) + '\n </build>\n</model>\n')
    cfg = project_config(slots, len(plates), P)
    files["[Content_Types].xml"] = (
        '<?xml version="1.0" encoding="UTF-8"?>\n<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\n'
        ' <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>\n'
        ' <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>\n'
        ' <Default Extension="png" ContentType="image/png"/>\n'
        ' <Default Extension="gcode" ContentType="text/x.gcode"/>\n</Types>\n')
    files["_rels/.rels"] = (
        '<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
        ' <Relationship Target="/3D/3dmodel.model" Id="rel-1" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>\n'
        + (' <Relationship Target="/Metadata/plate_1.png" Id="rel-2" '
           'Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/thumbnail"/>\n'
           if "Metadata/plate_1.png" in files else "") + '</Relationships>\n')
    files["3D/3dmodel.model"] = model
    files["3D/_rels/3dmodel.model.rels"] = (
        '<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
        + "\n".join(rels) + '\n</Relationships>\n')
    files["Metadata/project_settings.config"] = json.dumps(cfg, indent=4, sort_keys=True)
    files["Metadata/model_settings.config"] = ('<?xml version="1.0" encoding="UTF-8"?>\n<config>\n' + "\n".join(settings)
                                               + "\n" + "\n".join(plate_xml) + '\n</config>\n')
    files["Metadata/slice_info.config"] = (
        '<?xml version="1.0" encoding="UTF-8"?>\n<config>\n  <header>\n'
        '    <header_item key="X-BBL-Client-Type" value="slicer"/>\n'
        f'    <header_item key="X-BBL-Client-Version" value="{P["bambu_studio_version"]}"/>\n  </header>\n</config>\n')
    if gcodes:
        files["Metadata/custom_gcode_per_layer.xml"] = ('<?xml version="1.0" encoding="utf-8"?>\n<custom_gcodes_per_layer>\n'
                                                        + "\n".join(gcodes) + '\n</custom_gcodes_per_layer>\n')
    order = ["[Content_Types].xml", "_rels/.rels", "3D/3dmodel.model", "3D/_rels/3dmodel.model.rels"]
    order += sorted(k for k in files if k not in order)
    tmp = path + ".part"
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for k in order:
            data = files[k]
            z.writestr(k, data if isinstance(data, bytes) else data.encode())
    os.replace(tmp, path)
    for old in os.listdir(OUT):                    # only the current version is kept
        if old.startswith(f"{title}_P2S_v") and old.endswith(".3mf") and os.path.join(OUT, old) != path:
            os.remove(os.path.join(OUT, old))
    report = colour_report(key, man, plates, chosen, slots, path)
    os.makedirs(os.path.join(OUT, key, "u"), exist_ok=True)
    with open(os.path.join(OUT, key, "u", "bambu_colours.txt"), "w") as fh:
        fh.write(report)
    if verbose:
        print(report)
    return path, chosen, slots


def colour_report(key, man, plates, chosen, slots, path):
    lines = [f"{man['name']} - Bambu Studio project for the P2S: {os.path.basename(path)}", "",
             "Filament slots (match each to a loaded spool when you print):"]
    for i, s in enumerate(slots, 1):
        where = f" (in {', '.join(s['where'])})" if s["where"] else ""
        lines.append(f"  {i}. {s['name']} {s['hex']} - {s['spools']} spool(s), {s['grams']} g left{where}")
    lines += ["", "Design colour -> spool (colour difference dE: under 3 a close match, 3-8 near, over 8 a different shade):"]
    buy = []
    for h, c in sorted(chosen.items(), key=lambda kv: -kv[1]["need"]):
        short = "   <- not enough left" if c["spool"]["grams"] < c["need"] else ""
        lines.append(f"  {c['name']}  {h}\n      -> {c['spool']['name']} {c['spool']['hex']}  dE {c['de']:.1f}, "
                     f"needs ~{c['need']:.0f} g{short}")
        if c["de"] >= 8:
            nm, hx, de = to_buy(h)
            buy.append(f"  {c['name']} {h}: nearest spool you own is dE {c['de']:.1f} off; "
                       f"{nm} {hx} is dE {de:.1f} (~{c['need']:.0f} g)")
    if buy:
        lines += ["", "No close spool in your library (worth buying, or use the slot's spool as set):"] + buy
    lines += ["", "Plates:"]
    for i, p in enumerate(plates, 1):
        s0 = chosen[p["start"]]["spool"]["name"]
        ch = f", change to {chosen[p['change'][1]]['spool']['name']} on the {p['change'][0]:.1f} mm layer" if p["change"] else ""
        sup = ", supports (tree, build plate only)" if p["supports"] else ""
        lines.append(f"  {i:>2}. {p['base']}: {s0}{ch}{sup}")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    for k in sys.argv[1:]:
        write_project(k)


def plates_sheet(key, path=None):
    """A contact sheet of the project's plates seen from above, each face in the colour of the spool
    that prints it (the second spool above a plate's change height)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection
    man, plates = _plan(key)
    chosen = match(plates, library())
    n = len(plates)
    cols = min(4, n)
    rows = math.ceil(n / cols)
    fig, axs = plt.subplots(rows, cols, figsize=(cols * 3.2, rows * 3.5), dpi=110)
    axs = np.atleast_1d(axs).ravel()
    rgb = lambda h: np.array([int(h.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4)])
    for ax, (i, p) in zip(axs, enumerate(plates, 1)):
        ax.add_patch(plt.Rectangle((0, 0), BED, BED, fc="#23272b", ec="#555"))
        c0 = rgb(chosen[p["start"]]["spool"]["hex"])
        c1 = rgb(chosen[p["change"][1]]["spool"]["hex"]) if p["change"] else c0
        zc = p["change"][0] - LAYER if p["change"] else 1e9
        for (_, v, t) in _read_plate(p["file"]):
            tri = v[t]
            nz = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])[:, 2]
            up = nz > 1e-6
            if not up.any():
                continue
            z = tri[up][:, :, 2].mean(1)
            order = np.argsort(z)
            shade = 0.6 + 0.4 * (z[order] / max(z.max(), 1e-3))
            base = np.where((z[order] > zc)[:, None], c1[None, :], c0[None, :])
            ax.add_collection(PolyCollection(tri[up][order][:, :, :2], facecolors=np.clip(base * shade[:, None] + 0.05, 0, 1),
                                             edgecolors="none"))
        s0 = chosen[p["start"]]["spool"]["name"].replace("Bambu Lab ", "")
        cap = f"{i}. {p['colour'].replace('_', ' ')}\n{s0}"
        if p["change"]:
            cap += f"\n-> {chosen[p['change'][1]]['spool']['name'].replace('Bambu Lab ', '')} at {p['change'][0]:.1f}"
        ax.set_title(cap, fontsize=6.5)
        ax.set_xlim(-2, BED + 2)
        ax.set_ylim(-2, BED + 2)
        ax.set_aspect("equal")
        ax.axis("off")
    for ax in axs[n:]:
        ax.axis("off")
    fig.suptitle(f"{man['name']} - Bambu Studio plates in your spool colours", fontsize=10)
    fig.tight_layout()
    path = path or os.path.join(OUT, key, "u", "bambu_plates.png")
    fig.savefig(path, facecolor="white")
    plt.close(fig)
    return path

"""The Lindenwald: an original HO-scale (1:87.1) Swiss chalet bungalow, house 58 of the fifth
batch (the Craftsman era, 1900-1930).

A chalet with its broad gable to the street: a ground storey of random rubble, an upper storey
of squared logs laid Swiss-fashion with their ends crossing at every corner, under a wide roof
of split shingles whose rakes ride on carved purlins and sawn bargeboards with heart pendants.
Across the front a porch on round posts with carved bands, sawn heart balusters and a valanced
beam, whose flat top is the balcony of the upper storey, railed with the same hearts and
entered through a pair of glazed doors. Every window has heart-pierced shutters and a box of
blooms; downstairs under sawn heads, upstairs under little pent roofs. Edelweiss and hearts
between the storeys, keyhole fretwork and scroll brackets at the eaves, a stone stack in a
little shingled hat on the ridge, all on cyclopean stonework.

usage: python3 -m hoarch.buildings.lindenwald [check] [export]
"""
import os
import sys
import time

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import box, cs_union, inv34, offset, rect, slab, union
from hoarch import craftsman2 as CR2, cornice as CO, features as FT, gables as G, openings as O, roof as R
from hoarch.kit import Kit, print_flip
from hoarch.ornament import ext
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, stacked_shells

NAME = "The Lindenwald"
COLORS = {"Stone": "#9A938A", "Logs": "#8B5A2B", "Cream": "#F2EBDD", "Red": "#A33A2C", "Roof": "#5B4A3F", "Wood": "#6B4226",
          "Planks": "#7A5A3C", "PorchDeck": "#7A5A3C", "Windows_Doors": "#F2EBDD"}
RENDER_MAT = {"Stone": "stone", "Logs": "siding", "Cream": "trim", "Red": "accent", "Roof": "roof", "Wood": "wood",
              "Planks": "planks", "PorchDeck": "planks", "Windows_Doors": "trim", "Door": "door", "Glass": "glass"}

# ------------------------------------------------------------------ cornices (unique to the Lindenwald)
LEDGE = 1.4
JOINT = dict(pitch=15.0, margin=4.0, layers=[
    dict(kind="frieze", h=4.6, b=1.2, orn="edelweiss", role="Red"),
    dict(kind="course", h=1.6, b=1.4, orn="heartrow", role="Cream"),
    dict(kind="crown", h=2.2, b=1.4, P=3.8, orn="reverse", role="Wood")])
EAVE = dict(pitch=14.0, margin=4.0, layers=[
    dict(kind="frieze", h=4.6, b=1.2, orn="keyholes", role="Cream"),
    dict(kind="course", h=1.6, b=1.4, orn="heartrow", role="Red"),
    dict(kind="bed", h=3.0, b=1.4, P=9.0, role="Wood", brackets=dict(style="chaletscroll", t=1.3, reach=0.45)),
    dict(kind="crown", h=2.2, b=1.4, P=9.4, orn="bevel", role="Wood")])
RJ = round((LEDGE + 0.4 + CO.band_height(JOINT)) / 0.2) * 0.2
HE = CO.band_height(EAVE)

# ------------------------------------------------------------------ levels and plan
ZF = 10.0
S1 = ZF + 36.0
ZU = S1 + RJ
ZE = ZU + 30.0
ZW = round((ZE + HE) / 0.2) * 0.2
FASCIA = 1.6
Z_EAVE = ZW + FASCIA
D_EAVE, RAKE, SKIN = 12.0, 14.0, 1.8
S = 0.55
W, D = 130.0, 140.0
XC, YC = W / 2, D / 2
MAIN = Block("main", [(0, 0), (W, 0), (W, D), (0, D)], ZF, ZW)
PX0, PX1, PD = 12.0, 118.0, 16.0                 # the porch, and the balcony on its top
V1 = 7.0
V2 = ZU - ZF + 4.0
LOG0 = ZU - ZF                                   # the log courses' datum (from ZF)


def _skin(f, b, reg):
    reg = reg - rect(-1, ZE - LEDGE - 0.6 - b.z0, f.L + 1, ZW - b.z0 + 0.2)
    lo = reg ^ rect(-1, -50, f.L + 1, S1 - b.z0)
    hi = reg - rect(-1, -50, f.L + 1, ZU - b.z0)
    out = CR2.rubble_chalet(lo, seed=int(f.p0[0] + f.p0[1]) % 71) if not lo.is_empty() else M()
    if not hi.is_empty():
        out = out + CR2.siding_logs(hi, datum=LOG0)
    return out


def _openings():
    L = []

    def add(x, y, v0, sp, name, kind="window"):
        e, u = MAIN.locate(x, y)
        L.append(Opening(MAIN, e, u, v0, sp, name, kind))

    g = CR2.window_chalet(16.0, 19.0)
    u = CR2.window_chalet(16.0, 17.0, upper=True)
    att = CR2.window_chalet(11.0, 10.0, upper=True)
    add(XC, 0.0, 0.4, CR2.door_chalet(11.0, 24.0), "front-door", "door")
    add(XC, 0.0, V2 - 3.6, CR2.door_chalet(14.0, 21.0, 1.4, True), "balcony-door", "door")
    for x in (30.0, 100.0):
        add(x, 0.0, V1, g, f"S{x:.0f}-1")
        add(x, 0.0, V2, u, f"S{x:.0f}-2")
    add(XC, 0.0, Z_EAVE + 6.0 - ZF, att, "S-attic")
    for x_, tag in ((0.0, "W"), (W, "E")):
        for y in (40.0, 100.0):
            add(x_, y, V1, g, f"{tag}{y:.0f}-1")
            add(x_, y, V2, u, f"{tag}{y:.0f}-2")
    add(40.0, D, 0.4, CR2.door_chalet(10.0, 22.0), "back-door", "door")
    add(95.0, D, V1, g, "N95-1")
    for x in (35.0, 95.0):
        add(x, D, V2, u, f"N{x:.0f}-2")
    add(XC, D, Z_EAVE + 6.0 - ZF, att, "N-attic")
    return L


OPENINGS = _openings()


def _purlins(rf):
    out = []
    for wl in rf["walls"]:
        f, Lg = wl["facade"], wl["L"]
        for u in (18.0, 40.0, Lg - 40.0, Lg - 18.0):
            vtop = wl["shoulder"] + S * (min(u, Lg - u) - 0.9) - 0.25
            out.append(f.place(CR2.purlin_chalet(RAKE - 1.6, 1.8).translate([u, vtop, 0.0])))
    return union(out)


def _balcony_rail(x0, y0, x1, y1, z, h=9.0, t=0.9):
    """The balcony's railing along its three open sides: sawn heart balusters between rails,
    square posts at the corners, one piece standing on the porch top."""
    runs = [((x0, y0), (x1, y0)), ((x0, y1), (x0, y0)), ((x1, y0), (x1, y1))]
    out = []
    for (a, b) in runs:
        a, b = np.array(a), np.array(b)
        L = float(np.linalg.norm(b - a))
        d = (b - a) / L
        n = np.array([-d[1], d[0]])
        cs = cs_union(CR2.fill_sawnhearts(L, 0.0, h))
        A = np.array([[d[0], 0.0, n[0], a[0]], [d[1], 0.0, n[1], a[1]], [0.0, 1.0, 0.0, z]])
        out.append(ext(cs, -t / 2, t / 2).transform(A))
    for (x, y) in ((x0, y0), (x1, y0)):
        out.append(box([x - 1.0, y - 1.0, z], [x + 1.0, y + 1.0, z + h + 0.8]))
    return union(out)


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    base = MAIN.cs
    r = RAKE - D_EAVE
    pieces = [([(0.0, -r), (W, -r), (W, D + r), (0.0, D + r)], [1, 3], S)]
    gdefs = [dict(p0=(0.0, 0.0), p1=(W, 0.0), slope=S), dict(p0=(W, D), p1=(0.0, D), slope=S)]
    rf = G.gabled_roof(pieces, Z_EAVE, D_EAVE, gdefs, texture="schindel", tex_kw=dict(pitch=1.3, d=0.32),
                       skin=SKIN, rake=RAKE, inner_cs=offset(base, -3.0), fascia=FASCIA, hollow=2.8)
    gables = [(MAIN, 0, rf["walls"][0]["cs"].translate((0.0, Z_EAVE - ZF))), (MAIN, 2, rf["walls"][1]["cs"].translate((0.0, Z_EAVE - ZF)))]
    undress = [slab(offset(base, 10.0), ZE - LEDGE - 0.6, ZW + 0.01)]
    st = stacked_shells([MAIN], OPENINGS, [S1], t=3.0, corners="none", siding=_skin, gables=gables,
                        clear=[lip_keep(base, 3.0, ZF, 1.2)], prof=CO.joint_profile(RJ, LEDGE), belt_blocks=None,
                        water_table=False, undress=undress, partitions=[((3.0, YC), (W - 3.0, YC), 2.0, ZF, ZW)])
    kit.add("WALLS-1", "Stone", st["shells"][0], group="walls")
    kit.add("JOINT", "Wood", st["rings"][0], group="walls")
    no_lip = union([box([-1, -1, ZW - 1], [W + 1, 5.0, ZW + 5]), box([-1, D - 5.0, ZW - 1], [W + 1, D + 1, ZW + 5])])
    lip = (_corbel(base, 3.0, ZW) + lip_ring(base, 3.0, ZW)) - no_lip
    ends = union([f.place(CR2.log_ends(f.L, LOG0 + 0.5, ZE - LEDGE - 0.6 - ZF, e % 2, datum=LOG0)) for e, f in enumerate(MAIN.facades())])
    w2 = st["shells"][1] + lip + CO.ledge(MAIN.pts, ZE, LEDGE) + ends + _purlins(rf)
    kit.add("WALLS-2", "Logs", w2, group="walls")
    rings, _ = CO.level(st["outlines"][0], S1 + LEDGE + 0.4, JOINT)
    CO.add_level(kit, rings, "CORNICE-J", "cornice")
    rings, _ = CO.level(MAIN.pts, ZE, EAVE)
    CO.add_level(kit, rings, "CORNICE-E", "cornice")
    fnd = foundation([MAIN], 0.0, ZF, style="cyclopean")
    kit.add("FOUNDATION", "Stone", fnd, group="foundation")
    ins_keep = []
    chg = (round((O.PLUG + 0.8) / 0.2) * 0.2, "Red")
    for op in OPENINGS:
        A = op.local_frame()
        sp = op.spec
        b = sp["cut"].bounds()
        key = "DOOR" if op.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, "Cream", "Door" if op.kind == "door" else "Cream", "Glass")
        k_ = M.cube([400.0, 400.0, 20.0]).translate([-200.0, -200.0, chg[0] - O.PLUG]).transform(A)
        zones = [(c_, m_ - k_) for c_, m_ in zones] + [("Red", world ^ k_)]
        part = kit.add(f"{key}-{op.name}", "Windows_Doors", world, P=P, key=f"{key}-{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}-{op.v0 > 20}",
                       group="inserts", render=zones, change=chg)
        ins_keep.append(part.solid)
    print("walls + cornices + inserts", round(time.time() - t0, 1))

    # --- the roof: split shingles, a ridge cap, bargeboards, the stone stack in its hat
    roof = rf["body"] + rf["tex"] + rf["skins"] + rf["skin_tex"]
    zr = Z_EAVE + S * (W / 2 + D_EAVE)
    walls_env = union([wl["facade"].place(M.extrude(wl["cs"].offset(0.15), RAKE + 4.2).translate([0, 0, -3.15])) for wl in rf["walls"]])
    roof = roof + (G.ridge_cap((XC, -RAKE), (XC, D + RAKE), zr, S, ZW) - walls_env)
    roof = roof - lip_keep(base, 3.0, ZW)
    solid_env, _ = R.hip_roof(pieces, Z_EAVE, S, D_EAVE, texture=None, zlo=ZW)
    CH = 10.0
    cx, cy = XC, 104.0
    z_low = zr - S * (CH / 2) - 0.2
    z0 = round((z_low - 2.4) / 0.2) * 0.2
    roof = roof + G.pocket_seat(solid_env, cx, cy, CH / 2 + 0.9, CH / 2 + 0.9, z0)
    pocket = box([cx - CH / 2 - 0.9, cy - CH / 2 - 0.9, z0], [cx + CH / 2 + 0.9, cy + CH / 2 + 0.9, zr + 40])
    kit.add("ROOF", "Roof", roof - pocket, group="roof")
    kit.add("CHIMNEY", "Stone", CR2.chimney_chalet(CH, CH, round((zr + 14.0 - z0) / 0.2) * 0.2).translate([cx, cy, z0]), group="roof")
    for k, wl in enumerate(rf["walls"]):
        bb = CR2.barge_chalet(wl["L"], wl["slope"], D_EAVE, skin=SKIN)
        fw = wl["facade"]
        A = fw.A.copy()
        A[:, 3] = fw.world(0.0, 0.0, RAKE)
        bw = bb.transform(A) - roof
        bw = max(bw.decompose(), key=lambda m_: m_.volume())
        kit.add(f"BARGE-{k}", "Cream", bw, P=inv34(A), key=f"BARGE-{wl['L']:.0f}", group="gable")
    print("roof", round(time.time() - t0, 1))

    # --- the porch, whose one-piece top is the balcony floor; the balcony's railing on it
    INSET = 2.4
    ppts = [(PX0, 0.0), (PX0, -PD), (PX1, -PD), (PX1, 0.0)]
    Lp = PX1 - PX0
    H_floor = ZF - 1.4
    o = 2.4
    ptop = ZU - 0.2
    runs = [dict(a=(PX0, 0.0), b=(PX0, -PD), posts=[3.2, PD - INSET]),
            dict(a=(PX0, -PD), b=(PX1, -PD), posts=[INSET, 34.0, 72.0, Lp - INSET]),
            dict(a=(PX1, -PD), b=(PX1, 0.0), posts=[INSET, PD - 3.2])]
    PP = FT.porch_turned(ppts, runs, H_floor, ptop - 5.2 - H_floor, steps_at=[(1, XC - PX0, 16.0)], over=o, inset=INSET,
                         rail_h=8.4, planks=dict(pitch=1.8, border=1.2), post="chalet", rail="sawnhearts", arcade="chaletbeam",
                         skirt="crosslog", pier_tex="cyclopean", roof_edge="scallopboard", top=True)
    fkeep = slab(offset(base, 0.8 + 0.55 + 0.15), -1, ZF + 1.3)
    deck = PP["deck"] - fkeep
    kit.add("PORCH-deck", "PorchDeck", deck, P=print_flip(), group="porch", render=FT.plank_zones(deck, H_floor, "Planks", "PorchDeck"))
    bld_keep = union([p.solid for p in kit.parts if p.name in ("WALLS-1", "JOINT", "WALLS-2") or p.name.startswith("CORNICE")])
    keep = bld_keep + union(ins_keep) + fnd
    res = FT.add_porch_top(kit, "PORCH", PP, keep, "Wood", "Cream", group="porch")      # the whole slab: it is the balcony floor
    top = {p.name: p for p in kit.parts}["PORCH-top"].solid
    tb = top.bounding_box()
    zt = res["ptop"]
    rail = _balcony_rail(tb[0] + 1.2, tb[1] + 1.2, tb[3] - 1.2, -6.0, zt) - bld_keep - union(ins_keep)
    kit.add("BALCONY-rail", "Cream", max(rail.decompose(), key=lambda m_: m_.volume()), group="porch")
    for k, (sm, A) in enumerate(PP["steps"]):
        kit.add(f"PORCH-steps-{k}", "Stone", sm.transform(A) - fkeep - deck, group="porch")
    e, u = MAIN.locate(40.0, D)
    fb = MAIN.facades()[e]
    A = fb.A.copy()
    A[:, 3] = fb.world(u, -ZF, 1.4)
    kit.add("STOOP-back", "Stone", FT.steps(14.0, ZF - 0.6, 4).transform(A) - fnd, group="porch")
    FT.key_into(kit, "PORCH-steps-0", ["PORCH-deck"], (0, 1, 0), depth=0.8, conform=True)
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "lindenwald")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:80]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "lindenwald.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))

"""Harmon Town Hall: an original HO-scale (1:87.1) Italianate town hall, building 63 (the railroad and
town batch).

A two-storey hall of about 1889 in red pressed brick laid in English cross bond, with smooth
limestone sill bands, on cushion-rusticated limestone. A square tower stands forward of the
middle of the front: the entrance in its foot (a pair of panelled leaves under a fanlight of
radiating bars, in a rusticated arch between fluted pilasters under an entablature), a
council-chamber window and a carved TOWN HALL tablet over it, then, above the roof, a clock
in a square stone frame on three faces and a louvred belfry arch on each face, a bracketed
cornice and a steep pyramid of clipped-corner slates with a flagstaff. Segmental-headed
windows with keyed voussoir lintels below; round-headed windows with radiating bars under hoods
on scrolled consoles above. Cornices of lambrequins over bead and bar (the storey joint) and of
roundel panels between civic consoles (the eave and the tower top), under a low hip.

usage: python3 -m hoarch.buildings.harmon [check] [export]
"""
import os
import sys
import time

import numpy as np

from hoarch.core import box, offset, slab, union
from hoarch import cornice as CO, features as FT, gables as G, openings as O, roof as R, town as TN
from hoarch.kit import Kit
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, stacked_shells

NAME = "Harmon Town Hall"
COLORS = {"Brick": "#9A3E2C", "Limestone": "#D8D1BF", "Bronze": "#5F5A3C", "Cream": "#EDE4CC", "Slate": "#3E4650",
          "Windows_Doors": "#EDE4CC"}
RENDER_MAT = {"Brick": "brick", "Limestone": "stone", "Bronze": "bronze", "Cream": "trim", "Slate": "roof",
              "Windows_Doors": "trim", "Door": "door", "Glass": "glass", "Dial": "dial", "Hands": "hands", "Letters": "bronze"}
PALETTE = {"brick": ("#9A3E2C", 0.9), "stone": ("#D8D1BF", 0.85), "bronze": ("#5F5A3C", 0.6), "trim": ("#EDE4CC", 0.5),
           "roof": ("#3E4650", 0.8), "door": ("#4E3524", 0.6), "dial": ("#F2EEE2", 0.6), "hands": ("#1E1E1E", 0.5)}
VIEWS = {"hero": [-34, 14, 70, 0.95, [0, 0, 0]], "front": [0, 6, 80, 0.92, [0, 0, 0]], "rear": [150, 16, 70, 0.95, [0, 0, 0]],
         "right": [60, 12, 70, 0.95, [0, 0, 0]]}

# ------------------------------------------------------------------ cornices (unique to Harmon)
LEDGE = 1.4
JOINT = dict(pitch=14.0, margin=4.0, layers=[
    dict(kind="frieze", h=4.6, b=1.2, orn="lambrequin", role="Limestone"),
    dict(kind="course", h=1.4, b=1.4, orn="beadbar", role="Bronze"),
    dict(kind="crown", h=2.2, b=1.4, P=3.6, orn="cyma", role="Limestone")])
EAVE = dict(pitch=11.0, margin=4.0, layers=[
    dict(kind="frieze", h=6.0, b=1.2, orn="roundelpanel", role="Bronze"),
    dict(kind="course", h=1.4, b=1.4, orn="beadbar", role="Limestone"),
    dict(kind="bed", h=2.6, b=1.4, P=8.2, role="Cream", brackets=dict(style="civicconsole", t=1.6, reach=0.55)),
    dict(kind="crown", h=2.2, b=1.4, P=8.8, orn="ogee_fillet", role="Bronze")])
TOWER_C = dict(pitch=8.0, margin=3.0, layers=[
    dict(kind="frieze", h=4.6, b=1.2, orn="roundelpanel", role="Bronze"),
    dict(kind="course", h=1.4, b=1.4, orn="beadbar", role="Limestone"),
    dict(kind="bed", h=2.2, b=1.4, P=6.0, role="Cream", brackets=dict(style="civicconsole", t=1.6, reach=0.6)),
    dict(kind="crown", h=2.0, b=1.4, P=6.6, orn="cavetto", role="Bronze")])
RJ = round((LEDGE + 0.4 + CO.band_height(JOINT)) / 0.2) * 0.2
HE = CO.band_height(EAVE)

# ------------------------------------------------------------------ levels and plan
ZF = 12.0
S1 = ZF + 42.0
ZE = S1 + RJ + 40.0
ZW = round((ZE + HE) / 0.2) * 0.2
ZT = ZW + 56.0
ZTW = round((ZT + CO.band_height(TOWER_C)) / 0.2) * 0.2
FASCIA = 1.6
Z_EAVE = ZW + FASCIA
D_EAVE = 9.4
S_MAIN = 0.42
W, D = 172.0, 104.0
XC, YC = W / 2, D / 2
TX0, TX1, TY0, TY1 = XC - 18.0, XC + 18.0, -12.0, 24.0
MAIN = Block("main", [(0, 0), (W, 0), (W, D), (0, D)], ZF, ZW)
TOWER = Block("tower", [(TX0, TY0), (TX1, TY0), (TX1, TY1), (TX0, TY1)], ZF, ZTW)
BLOCKS = [MAIN, TOWER]
V1 = 8.0
V2 = S1 + RJ + 6.0 - ZF
CLOCK_V = ZW - ZF + 22.0                           # the clocks' centres (v from ZF)
CLOCKS = (0, 1, 3)                                 # the tower's front and side faces
TAB_V, TAB_L, TAB_H = V2 + 23.0, 28.0, 5.0         # the TOWN HALL tablet on the tower front


def _openings():
    L = []

    def add(blk, x, y, v0, sp, name, kind="window"):
        e, u = blk.locate(x, y)
        L.append(Opening(blk, e, u, v0, sp, name, kind))

    lo = TN.window_civic_lower(11.0, 22.0)
    up = TN.window_civic_upper(11.0, 26.0)
    for x in (22.0, 50.0, 122.0, 150.0):
        add(MAIN, x, 0.0, V1, lo, f"S{x:.0f}")
        add(MAIN, x, 0.0, V2, up, f"S{x:.0f}-2")
    for x in (22.0, 50.0, 122.0, 150.0):
        add(MAIN, x, D, V1, lo, f"N{x:.0f}")
    for x in (22.0, 50.0, 86.0, 122.0, 150.0):
        add(MAIN, x, D, V2, up, f"N{x:.0f}-2")
    add(MAIN, XC, D, 0.4, TN.door_civic(12.0, 26.0), "back-door", "door")
    for xw in (0.0, W):
        for y in (26.0, 52.0, 78.0):
            add(MAIN, xw, y, V1, lo, f"{'W' if xw == 0 else 'E'}{y:.0f}")
            add(MAIN, xw, y, V2, up, f"{'W' if xw == 0 else 'E'}{y:.0f}-2")
    add(TOWER, XC, TY0, 0.4, TN.door_civic(15.0, 30.0), "front-door", "door")
    add(TOWER, XC, TY0, V2, TN.window_civic_upper(11.0, 18.0), "T-S-2")
    bel = TN.window_civicbelfry(10.0, 16.0)
    vb = ZW - ZF + 35.0
    for (x, y, nm) in ((XC, TY0, "S"), (TX1, (TY0 + TY1) / 2, "E"), (XC, TY1, "N"), (TX0, (TY0 + TY1) / 2, "W")):
        add(TOWER, x, y, vb, bel, f"belfry-{nm}")
    return L


OPENINGS = _openings()


def _skin(f, b, reg):
    if b is MAIN:
        reg = reg - TN.rect(-1, ZE - LEDGE - 0.6 - b.z0, f.L + 1, 999)
    else:
        reg = reg - TN.rect(-1, ZT - LEDGE - 0.6 - b.z0, f.L + 1, 999)
        for e in CLOCKS:
            if np.allclose(TOWER.facades()[e].n, f.n):
                reg = reg - TN.rect(f.L / 2 - 9.4, CLOCK_V - 8.9, f.L / 2 + 9.4, CLOCK_V + 11.9)
        if np.allclose(TOWER.facades()[0].n, f.n):
            reg = reg - TN.rect(f.L / 2 - TAB_L / 2 - 1.2, TAB_V - 0.2, f.L / 2 + TAB_L / 2 + 1.2, TAB_V + TAB_H + TAB_L * 0.12 + 0.4)
    return TN.brick_civic(reg, datum=0.0, bands=[(V1 - 1.4, V1 - 0.2), (V2 - 1.4, V2 - 0.2)])


def _flat(A):
    """Print pose for a piece lying on the wall: its face up."""
    return np.column_stack([np.vstack([A[:, 0], A[:, 1], A[:, 2]]), np.zeros(3)])


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    base = MAIN.cs
    tower_keep = TOWER.solid(grow=0.2, dz0=-1, dz1=1)
    undress = [slab(offset(base, 10.0) - offset(TOWER.cs, 1.0), ZE - LEDGE - 0.6, ZW + 0.01),
               slab(offset(TOWER.cs, 9.0), ZT - LEDGE - 0.6, ZTW + 0.01)]
    st = stacked_shells(BLOCKS, OPENINGS, [S1], t=3.0, corners="none", siding=_skin,
                        prof=CO.joint_profile(RJ, LEDGE), belt_blocks=None, water_table=False, undress=undress)
    w1 = st["shells"][0] - lip_keep(base, 3.0, ZF, 1.2) - lip_keep(TOWER.cs, 3.0, ZF, 1.2)
    kit.add("WALLS-1", "Brick", w1, group="walls")
    kit.add("JOINT", "Limestone", st["rings"][0], group="walls")
    no_lip = union([tower_keep, slab(offset(TOWER.cs, 1.0), ZW - 1, ZW + 5)])
    lip = (_corbel(base, 3.0, ZW) + lip_ring(base, 3.0, ZW)) - no_lip
    allcs = MAIN.cs + TOWER.cs
    tring = slab((offset(TOWER.cs, -0.05) - offset(TOWER.cs, -3.0)) ^ offset(base, -3.05), S1 + RJ, ZW + 1.2)
    tring = tring - lip_keep(allcs, 3.0, S1 + RJ)
    ledge_e = CO.ledge(MAIN.pts, ZE, LEDGE) - tower_keep
    tlip = _corbel(TOWER.cs, 3.0, ZTW) + lip_ring(TOWER.cs, 3.0, ZTW)
    w2 = st["shells"][1] + lip + tring + ledge_e + CO.ledge(TOWER.pts, ZT, LEDGE) + tlip
    kit.add("WALLS-2", "Brick", w2, group="walls")
    rings, _ = CO.level(st["outlines"][0], S1 + LEDGE + 0.4, JOINT)
    CO.add_level(kit, rings, "CORNICE-J", "cornice")
    rings, _ = CO.level(MAIN.pts, ZE, EAVE, cut=TOWER.solid(grow=1.1, dz0=-2, dz1=2))
    CO.add_level(kit, rings, "CORNICE-E", "cornice")
    rings, _ = CO.level(TOWER.pts, ZT, TOWER_C)
    CO.add_level(kit, rings, "CORNICE-T", "tower")
    fnd = foundation(BLOCKS, 0.0, ZF, style="cushion")
    kit.add("FOUNDATION", "Limestone", fnd, group="foundation")
    ins_keep = []
    for op in OPENINGS:
        A = op.local_frame()
        sp = op.spec
        b = sp["cut"].bounds()
        key = "DOOR" if op.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, "Windows_Doors", "Door" if op.kind == "door" else "Windows_Doors", "Glass")
        part = kit.add(f"{key}-{op.name}", "Windows_Doors", world, P=P,
                       key=f"{key}-{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}-{op.name[:4]}", group="inserts", render=zones)
        ins_keep.append(part.solid)
    # the clocks and the tablet, glued by their whole backs into plain fields in the brick
    for e in CLOCKS:
        f = TOWER.facades()[e]
        A = f.A.copy()
        A[:, 3] = f.world(f.L / 2, CLOCK_V, 0.0)
        whole, dial, marks = TN.clock_civic(13.0)
        kit.add(f"CLOCK-{'SEW'[CLOCKS.index(e)]}", "Limestone", whole.transform(A), P=_flat(A), key="CLOCK", group="tower",
                render=[("Limestone", (whole - dial - marks).transform(A)), ("Dial", dial.transform(A)), ("Hands", marks.transform(A))])
    f = TOWER.facades()[0]
    A = f.A.copy()
    A[:, 3] = f.world(f.L / 2, TAB_V, 0.0)
    tab, letters = TN.name_tablet("TOWN HALL", TAB_L, TAB_H)
    kit.add("TABLET", "Limestone", tab.transform(A), P=_flat(A), group="tower",
            render=[("Limestone", (tab - letters).transform(A)), ("Letters", letters.transform(A))])
    print("walls + cornices + inserts", round(time.time() - t0, 1))

    # --- the main roof: a low hip of clipped-corner slates, cut round the tower
    pieces = [(MAIN.pts, [0, 1, 2, 3], S_MAIN)]
    rf = G.gabled_roof(pieces, Z_EAVE, D_EAVE, [], texture="clipcorner", tex_kw=dict(pitch=1.7, wtab=2.4, d=0.4),
                       inner_cs=offset(base, -3.0), fascia=FASCIA, hollow=2.8)
    roof = rf["body"] + rf["tex"]
    zr = Z_EAVE + S_MAIN * (D / 2 + D_EAVE)
    corners = [(-D_EAVE, -D_EAVE), (W + D_EAVE, -D_EAVE), (W + D_EAVE, D + D_EAVE), (-D_EAVE, D + D_EAVE)]
    ends = [(D / 2, YC), (W - D / 2, YC), (W - D / 2, YC), (D / 2, YC)]
    roof = roof + G.ridge_cap((D / 2, YC), (W - D / 2, YC), zr, S_MAIN, ZW, half=1.3, up=0.7)
    roof = roof + union([G.hip_cap((c[0], c[1], Z_EAVE), (e[0], e[1], zr), half=1.3, up=0.7, drop=1.8) for c, e in zip(corners, ends)])
    roof = roof - lip_keep(base, 3.0, ZW) - TOWER.solid(grow=0.6, dz0=-5, dz1=500)
    roof = roof.trim_by_plane([0, 0, 1.0], Z_EAVE - FASCIA)
    kit.add("ROOF", "Slate", max(roof.decompose(), key=lambda m_: m_.volume()), group="roof")
    # --- the tower's pyramid and its flagstaff
    d_t = TOWER_C["layers"][-1]["P"] + 0.4
    tpts = [(TX0, TY0), (TX1, TY0), (TX1, TY1), (TX0, TY1)]
    troof, ttex = R.hip_roof([(tpts, [0, 1, 2, 3])], ZTW + 1.4, 1.35, d_t, texture="clipcorner",
                             tex_kw=dict(pitch=1.5, wtab=2.0, d=0.35), zlo=ZTW)
    tr = (troof + ttex) - lip_keep(TOWER.cs, 3.0, ZTW)
    kit.add("TOWER-roof", "Slate", tr, group="tower")
    apex = ZTW + 1.4 + 1.35 * (18.0 + d_t)
    kit.add("FLAGSTAFF", "Bronze", TN.flagstaff().translate([XC, (TY0 + TY1) / 2, apex - 1.2]), group="tower")
    FT.crown(kit, "FLAGSTAFF", "TOWER-roof")
    # --- the front steps
    e, u = TOWER.locate(XC, TY0)
    fb = TOWER.facades()[e]
    A = fb.A.copy()
    A[:, 3] = fb.world(u, -ZF, 1.4)
    kit.add("STEPS", "Limestone", FT.steps(26.0, ZF - 0.6, 5, cheek=2.4).transform(A) - fnd, group="steps")
    e, u = MAIN.locate(XC, D)
    fb = MAIN.facades()[e]
    A = fb.A.copy()
    A[:, 3] = fb.world(u, -ZF, 1.4)
    kit.add("STEPS-back", "Limestone", FT.steps(16.0, ZF - 0.6, 5).transform(A) - fnd, group="steps")
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "harmon")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:80]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "harmon.npz"))
    import json
    json.dump({"materials": {k: [h, r, 0.0] for k, (h, r) in PALETTE.items()}, "views": VIEWS},
              open(os.path.join(OUT, "palette.json"), "w"), indent=1)
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))

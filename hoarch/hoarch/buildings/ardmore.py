"""The Ardmore -- an original HO-scale (1:87.1) Richardsonian Romanesque house for the lineup.

Two and a half storeys of rock-faced brownstone on a granite base, with buff stone belt
courses and an arched corbel table under the eaves. A round (twelve-sided) tower at the front
corner rises a storey above the eaves to an arcaded belvedere and a steep conical roof. The
entrance is a stone loggia with a great round arch; inside it a round-arched doorway of
receding orders. Round-arched windows ring their heads with long voussoirs on squat
colonnettes with cushion capitals: singles, an arcaded triple, and paired square-headed
lights under a heavy lintel. A steep hipped roof with a front gable and ridge chimneys.

usage: python3 -m hoarch.buildings.ardmore [check] [export]
"""
import math
import os
import sys
import time

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import ashlar, box, circle, cs_union, inv34, ngon, offset, poly, rect, slab, union
from hoarch import features as FT, gables as G, openings as O, roof as R
from hoarch.kit import Kit, print_flip
from hoarch.ornament import chamfer_box, ext, finial
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, stacked_shells, wall_shell

NAME = "Ardmore Richardsonian Romanesque"
COLORS = {"Sandstone": "#9A6248", "Buff": "#D8C8A4", "Slate": "#3F4A4F", "Granite": "#7E7C78", "Brick": "#8A3B2B",
          "Windows_Doors": "#EDE3C8"}
RENDER_MAT = {"Sandstone": "stone_wall", "Buff": "trim", "Slate": "roof", "Granite": "stone", "Brick": "brick",
              "Windows_Doors": "trim", "Sash": "sash", "Door": "door", "Glass": "glass"}
PALETTE = {"stone_wall": ["#9A6248", 0.85, 0.0], "trim": ["#D8C8A4", 0.7, 0.0], "roof": ["#3F4A4F", 0.8, 0.0],
           "stone": ["#7E7C78", 0.9, 0.0], "brick": ["#8A3B2B", 0.85, 0.0], "sash": ["#2F3A2E", 0.45, 0.0],
           "door": ["#4A2616", 0.45, 0.0]}

# ------------------------------------------------------------------ levels (on the 0.2 mm grid)
ZF = 12.0
S1 = ZF + 38.0
RH = 4.4
ZE = S1 + RH + 34.0
ZT = ZE + RH + 28.0              # tower top: its eave and cone clear the main roof
FASCIA = 2.4
Z_EAVE = ZE + FASCIA
D_EAVE, RAKE, SKIN = 3.0, 2.6, 1.8
S_MAIN, S_CROSS = 1.1, 1.5
PZ = ZF + 34.0                   # entrance loggia top
V1 = 6.0
V2 = S1 + RH + 4.0 - ZF

# ------------------------------------------------------------------ plan
W, D = 110.0, 72.0
GX0, GX1 = 80.0, 106.0           # front gable
TC, TAPO = (17.0, 3.0), 17.0     # the round tower
MAIN = Block("main", [(0, 0), (W, 0), (W, D), (0, D)], ZF, ZE)
TOWER = Block("tower", ngon(TC, TAPO, n=12), ZF, ZT)
PX0, PX1, PD = 40.0, 76.0, 14.0
PORCH = Block("porch", [(PX0, -PD), (PX1, -PD), (PX1, 3.0), (PX0, 3.0)], ZF, PZ)
BLOCKS = [MAIN, TOWER, PORCH]


def _roof_z(x, y):
    """Height of the main hip roof's top at plan (x, y) (None outside its eave)."""
    d = min(x + D_EAVE, W + D_EAVE - x, y + D_EAVE, D + D_EAVE - y)
    return None if d < 0 else Z_EAVE + S_MAIN * d


def _corbel_table(L, v_top, h=2.4, pitch=3.0, span=2.0, d=0.8):
    """Romanesque corbel table in facade (u, v): a band of small round arches carried on
    corbels, under v_top. The corbels' feet are 45-degree wedges so it prints upright."""
    n = max(1, int((L - 1.0) / pitch))
    m = (L - n * pitch) / 2
    band = rect(0.3, v_top - h, L - 0.3, v_top)
    arches = []
    for k in range(n):
        c = m + (k + 0.5) * pitch
        r = span / 2
        arches.append(cs_union([rect(c - r, v_top - h - 1, c + r, v_top - h + 0.6),
                                circle((c, v_top - h + 0.6), r, 20)]))
    body = ext(band - cs_union(arches), 0.0, d)
    feet = []
    for k in range(n + 1):
        u = m + k * pitch
        if u < 0.6 or u > L - 0.6:
            continue
        w2 = (pitch - span) / 2
        feet.append(M.hull_points([(u - w2, v_top - h + 0.01, 0.0), (u + w2, v_top - h + 0.01, 0.0),
                                   (u - w2, v_top - h + 0.01, d), (u + w2, v_top - h + 0.01, d),
                                   (u - w2 * 0.6, v_top - h - d, 0.0), (u + w2 * 0.6, v_top - h - d, 0.0)]))
    return body + union(feet)


def _siding(f, b, reg):
    """Rock-faced brownstone, and an arched corbel table under the eaves (main and tower)."""
    H = b.z1 - b.z0
    top = H - 0.2
    seed = sum(map(ord, b.name)) + int(f.p0[0] * 7 + f.p0[1] * 3) % 1000
    out = ashlar(reg - rect(-1, top - 3.4, f.L + 1, H) if b is not PORCH else reg,
                 course=(2.6, 4.2), length=(4.0, 9.0), d=0.55, seed=seed)
    if b is not PORCH:
        ct = _corbel_table(f.L, top) ^ M.extrude(reg.offset(0.01), 2.0).translate([0, 0, -0.5])
        out = out + ct
    return out


def _outside(p, blk, margin):
    return (blk.cs ^ rect(p[0] - margin, p[1] - margin, p[0] + margin, p[1] + margin)).is_empty()


def _openings():
    L = []
    lo = O.window_romanesque(8.0, 22.0)
    up = O.window_romanesque(7.6, 20.0)
    tri = O.window_romanesque(6.0, 17.0, n=3)
    pair = O.window_romanesque(7.2, 18.0, n=2, flat=True)
    gab = O.window_romanesque(5.6, 13.0, col=1.0, L=2.0)
    tw = O.window_romanesque(4.4, 15.0, col=0.9, L=1.8, hood=False, sill_ext=0.4)
    bel = O.window_romanesque(4.4, 11.0, col=0.9, L=1.6, hood=False, sill_ext=0.4)
    portal = O.door_romanesque(18.0, 27.0, plug=False, orders=1)
    door = O.door_romanesque(12.0, 25.0, orders=1)
    back_door = O.door_romanesque(10.0, 23.0, orders=1, leaves=1, L=2.4)

    def add(blk, x, y, v0, sp, name, kind="window"):
        e, u = blk.locate(x, y)
        L.append(Opening(blk, e, u, v0, sp, name, kind))

    add(PORCH, (PX0 + PX1) / 2, -PD, 0.0, portal, "portal", "portal")
    add(MAIN, (PX0 + PX1) / 2, 0.0, 0.4, door, "front-door", "door")
    xm = (GX0 + GX1) / 2
    add(MAIN, xm, 0.0, V1, tri, "front-tri")
    add(MAIN, xm, 0.0, V2, pair, "front-pair")
    add(MAIN, xm, 0.0, ZE - ZF + 2.0, gab, "gable")
    add(MAIN, (PX0 + PX1) / 2, 0.0, V2, up, "front-up")
    for y in (38.0, 58.0):
        add(MAIN, 0.0, y, V1, lo, f"west-{int(y)}-1")
        add(MAIN, 0.0, y, V2, up, f"west-{int(y)}-2")
    for y in (18.0, 54.0):
        add(MAIN, W, y, V1, lo, f"east-{int(y)}-1")
        add(MAIN, W, y, V2, up, f"east-{int(y)}-2")
    add(MAIN, 80.0, D, 0.4, back_door, "back-door", "door")
    for x in (24.0, W - 12.0):
        add(MAIN, x, D, V1, lo, f"back-{int(x)}-1")
    for x in (24.0, 80.0, W - 12.0):
        add(MAIN, x, D, V2, up, f"back-{int(x)}-2")
    # the tower: windows on its outside faces, an arcaded belvedere above the roof
    for k, f in enumerate(TOWER.facades()):
        m = (f.p0 + f.p1) / 2
        mo = m + f.n * 3.0
        if _outside(mo, MAIN, 3.5) and _outside(mo, PORCH, 3.5):
            add(TOWER, m[0], m[1], V1 + 2.0, tw, f"tower-{k}-1")
            add(TOWER, m[0], m[1], V2 + 1.0, tw, f"tower-{k}-2")
        zr = _roof_z(*(m + f.n * 2.0))
        if zr is None or zr < ZT - 17.0 - 2.0:
            add(TOWER, m[0], m[1], ZT - ZF - 17.0, bel, f"tower-{k}-3")
    return L


OPENINGS = _openings()


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    pieces = [(MAIN.pts, [0, 1, 2, 3], S_MAIN),
              ([(GX0, -(RAKE - D_EAVE)), (GX1, -(RAKE - D_EAVE)), (GX1, 30.0), (GX0, 30.0)], [1, 3], S_CROSS)]
    specs = [dict(p0=(GX0, 0.0), p1=(GX1, 0.0), slope=S_CROSS, e=0.3)]
    rf = G.gabled_roof(pieces, Z_EAVE, D_EAVE, specs, texture=["square", "square", "square", "fish"],
                       skin=SKIN, rake=RAKE, inner_cs=offset(MAIN.cs, -3.0), fascia=FASCIA, hollow=2.6)
    wl = rf["walls"][0]
    gables = [(MAIN, 0, wl["cs"].translate((GX0, Z_EAVE - ZF)))]
    wall_ops = [o for o in OPENINGS if o.kind != "portal"] + [o for o in OPENINGS if o.kind == "portal"]
    # one joint only: above the first-floor belt the upper walls, the front gable and the whole
    # tower are one upright piece (the gable wall stays joined to the storey below it)
    st = stacked_shells(BLOCKS, wall_ops, [S1], t=3.0, corners="none", siding=_siding, gables=gables,
                        water_table=True)
    kit.add("WALLS-1", "Sandstone", st["shells"][0], group="walls")
    kit.add("BELT-1", "Buff", st["rings"][0], group="walls")
    tower_keep = TOWER.solid(grow=0.2, dz0=-1, dz1=1)
    no_lip = union([box([GX0 - 1.5, -1, ZE - 1], [GX1 + 1.5, 5.0, ZE + 5]), tower_keep,
                    slab(offset(TOWER.cs, 1.0), ZE - 1, ZE + 5)])
    lip = (_corbel(MAIN.cs, 3.0, ZE) + lip_ring(MAIN.cs, 3.0, ZE)) - no_lip
    # carry the tower's wall down through the main house's upper storey, so its ring above the
    # eaves stands on wall rather than hanging over the rooms
    base = cs_union([MAIN.cs, TOWER.cs])
    tring = slab((offset(TOWER.cs, -0.05) - offset(TOWER.cs, -3.0)) ^ offset(MAIN.cs, -3.05), S1 + RH, ZE + 1.2)
    tring = tring - lip_keep(base, 3.0, S1 + RH)
    kit.add("WALLS-2", "Sandstone", st["shells"][1] + lip + tring, group="walls")
    kit.add("FOUNDATION", "Granite", foundation(BLOCKS, 0.0, ZF), group="foundation")
    inserts = []
    for o in OPENINGS:
        A = o.local_frame()
        sp = o.spec
        b = sp["cut"].bounds()
        tag = f"{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}"
        if o.kind == "portal":
            B = A.copy()
            kit.add("PORTAL", "Buff", sp["insert"].transform(B), P=inv34(B), group="porch")
            continue
        key = "DOOR" if o.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, "Buff", "Door" if o.kind == "door" else "Sash", "Glass")
        inserts.append(kit.add(f"{key}-{o.name}", "Windows_Doors", world, P=P, key=f"{key}-{tag}",
                               group="inserts", render=zones))
    print("walls + inserts", round(time.time() - t0, 1))

    # --- main roof: hollow hip with the front gable, cut round the tower and its belt
    roof = rf["body"] + rf["tex"] + rf["skins"] + rf["skin_tex"]
    zr = Z_EAVE + S_MAIN * (D / 2 + D_EAVE)
    zc = Z_EAVE + S_CROSS * ((GX1 - GX0) / 2 + D_EAVE)
    xm = (GX0 + GX1) / 2
    y_meet = (zc - Z_EAVE) / S_MAIN - D_EAVE + 1.0
    caps = union([G.ridge_cap((D / 2, D / 2), (W - D / 2, D / 2), zr, S_MAIN, ZE),
                  G.ridge_cap((xm, -RAKE), (xm, y_meet), zc, S_CROSS, ZE)])
    walls_env = wl["facade"].place(M.extrude(wl["cs"].offset(0.15), 4.2).translate([0, 0, -3.15]))   # and its stonework
    # hip caps from the eave corners up to the ridge ends
    corners = [(-D_EAVE, -D_EAVE), (W + D_EAVE, -D_EAVE), (W + D_EAVE, D + D_EAVE), (-D_EAVE, D + D_EAVE)]
    ends = [(D / 2, D / 2), (W - D / 2, D / 2), (W - D / 2, D / 2), (D / 2, D / 2)]
    hips = union([G.hip_cap((c[0], c[1], Z_EAVE), (e[0], e[1], zr), half=1.3, up=0.7, drop=1.8)
                  for c, e in zip(corners, ends)])
    roof = roof + ((caps + hips) - walls_env)
    roof = roof - lip_keep(MAIN.cs, 3.0, ZE)
    CH = 9.0
    chims = [(46.0, D / 2), (66.0, D / 2)]
    z_low = zr - S_MAIN * (CH / 2) - 0.2
    z0 = round((z_low - 2.4) / 0.2) * 0.2
    solid_env, _ = R.hip_roof(pieces, Z_EAVE, S_MAIN, D_EAVE, texture=None, zlo=ZE)
    for (x, y) in chims:
        roof = roof + G.chimney_seat(solid_env, x, y, CH / 2, zr + 1.0)
    pockets = union([box([x - CH / 2 - 0.4, y - CH / 2 - 0.4, z0], [x + CH / 2 + 0.4, y + CH / 2 + 0.4, zr + 40])
                     for x, y in chims])
    roof = roof - pockets - slab(offset(TOWER.cs, 1.4), ZE - 1, ZT + 1)
    kit.add("ROOF", "Slate", roof, group="roof")
    for k, (x, y) in enumerate(chims):
        ch = FT.chimney(w=CH, dpt=CH, h=round((zr + 14.0 - z0) / 0.2) * 0.2, peg=None, pots=2).translate([x, y, z0])
        kit.add(f"CHIMNEY-{k}", "Brick", ch, key="CHIMNEY", group="roof")
    print("roof", round(time.time() - t0, 1))

    # --- the tower's eave and conical roof
    tpts = TOWER.pts
    teave = R.bracketed_cornice(tpts, ZT, R.CORNICE_SMALL, brackets=None,
                                dents=dict(z=3.8, h=0.8, d0=0.8, d=0.7), lip_t=3.0,
                                deck=(6.0, 8.0))
    kit.add("TOWER-eave", "Buff", teave, P=print_flip(), group="tower")
    zc0 = ZT + 8.0
    cone, ctex = R.hip_roof([(tpts, list(range(12)))], zc0, 2.4, 3.0, texture="fish",
                            tex_kw=dict(pitch=1.55, wtab=1.8, d=0.5))     # steep: deeper relief reads as >= a nozzle
    inner, _ = R.hip_roof([(tpts, list(range(12)))], zc0 - 2.4 * math.sqrt(1 + 2.4 ** 2), 2.4, 3.0, texture=None)
    cone = (cone + ctex) - (inner ^ slab(offset(TOWER.cs, -1.0), zc0 - 1, zc0 + 200))
    rr = TAPO + 3.0
    zseat = round((zc0 + 2.4 * rr - 2.0) / 0.2) * 0.2
    seat = M.cylinder(1.2, 1.35, 1.35, 32).translate([TC[0], TC[1], zseat - 0.4])
    re = (TAPO + 3.0) / math.cos(math.pi / 12)
    zap = zc0 + 2.4 * (TAPO + 3.0)
    tips = [(TC[0] + re * math.cos(-math.pi / 2 + math.pi / 12 + 2 * math.pi * k / 12),
             TC[1] + re * math.sin(-math.pi / 2 + math.pi / 12 + 2 * math.pi * k / 12)) for k in range(12)]
    hipc = union([G.hip_cap((x, y, zc0), (TC[0], TC[1], zap), half=0.9, up=0.5, drop=1.4) for x, y in tips])
    cone = cone + hipc.trim_by_plane([0, 0, 1.0], zc0 + 0.2)
    cone = cone.trim_by_plane([0, 0, -1.0], -zseat) - seat
    kit.add("TOWER-roof", "Slate", cone, group="tower")
    kit.add("TOWER-finial", "Slate", finial(1.3, 10.0).translate([TC[0], TC[1], zseat - 0.4]), group="tower")
    print("tower", round(time.time() - t0, 1))

    # --- the entrance loggia: a paved floor, a stone deck with a parapet, steps
    inner_p = offset(PORCH.cs, -3.0) - offset(MAIN.cs, 0.0)
    fnd = foundation(BLOCKS, 0.0, ZF)
    kit.add("PORCH-floor", "Granite", slab(inner_p.offset(-0.15), 0.0, ZF) - fnd, group="porch")
    deck_cs = PORCH.cs.offset(0.8) - MAIN.cs
    deck = slab(deck_cs, PZ, PZ + 1.6) + slab(offset(PORCH.cs, -3.15) - offset(MAIN.cs, 0.15), PZ - 1.2, PZ + 0.01)
    walls_lo = st["shells"][0] + st["rings"][0] + st["shells"][1]
    kit.add("PORCH-deck", "Buff", deck - walls_lo, P=print_flip(), group="porch")
    par_out = PORCH.cs.offset(0.4) - MAIN.cs.offset(0.15)
    par = slab(par_out - PORCH.cs.offset(-1.4), PZ + 1.6, PZ + 6.0)
    cope = slab(par_out.offset(0.4) - PORCH.cs.offset(-1.8) - MAIN.cs.offset(0.15), PZ + 6.0, PZ + 7.0)
    piers = union([box([x - 2.0, y - 2.0, PZ + 1.6], [x + 2.0, y + 2.0, PZ + 8.2])
                   for x, y in ((PX0 + 1.6, -PD + 1.6), (PX1 - 1.6, -PD + 1.6))])
    kit.add("PORCH-parapet", "Buff", (par + cope + piers) - walls_lo, group="porch")
    e, u = PORCH.locate((PX0 + PX1) / 2, -PD)
    f = PORCH.facades()[e]
    A = f.A.copy()
    A[:, 3] = f.world(u, -ZF, 1.4)
    kit.add("STEPS-front", "Granite", FT.steps(20.0, ZF - 0.6, 4, cheek=2.0).transform(A), group="porch")
    e, u = MAIN.locate(80.0, D)
    f = MAIN.facades()[e]
    A = f.A.copy()
    A[:, 3] = f.world(u, -ZF, 1.4)
    kit.add("STEPS-back", "Granite", FT.steps(13.0, ZF - 0.6, 4).transform(A), group="porch")
    print("porch", round(time.time() - t0, 1))
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "ardmore")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:40]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "ardmore.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))

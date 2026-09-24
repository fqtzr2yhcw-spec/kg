"""The Carrow -- an original HO-scale (1:87.1) Queen Anne "castle" for the lineup.

A rock-faced stone first storey under a fish-scale shingled second storey; a round (twelve-
sided) turret at the front corner rising a storey above the eaves to a bracketed cornice and
a steep witch's-hat spire; a steep patterned-slate hip with a front gable hung with a
pierced bargeboard over an arched attic window; Queen Anne windows (pediments with carved
fans over shaped aprons, scroll hoods, border-light sashes); a swan-neck entrance; and a
turned porch wrapping the front and the west side round a chamfered corner.

usage: python3 -m hoarch.buildings.carrow [check] [export]
"""
import math
import os
import sys
import time

import numpy as np
from manifold3d import JoinType, Manifold as M

from hoarch.core import ashlar, box, compose, cs_union, inv34, ngon, offset, rect, scallop_rows, slab, union
from hoarch import features as FT, gables as G, openings as O, roof as R
from hoarch.kit import Kit, print_flip
from hoarch.ornament import finial
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, stacked_shells

NAME = "Carrow Queen Anne Castle"
COLORS = {"Stone": "#948A80", "Goldenrod": "#C9A04A", "Cream": "#EDE3C8", "Slate": "#3F4A4F", "Granite": "#6F6D6A",
          "Brick": "#8A3B2B", "PorchGray": "#6B706F", "Windows_Doors": "#EDE3C8"}
RENDER_MAT = {"Stone": "stone_wall", "Goldenrod": "siding", "Cream": "trim", "Slate": "roof", "Granite": "stone",
              "Brick": "brick", "PorchGray": "porchfloor", "Windows_Doors": "trim", "Sash": "sash", "Door": "door",
              "Glass": "glass"}

# ------------------------------------------------------------------ levels (on the 0.2 mm grid)
ZF = 12.0
S1 = ZF + 38.0
RH = 4.4
ZE = S1 + RH + 34.0
ZT = ZE + RH + 22.0              # turret top
FASCIA = 2.0
Z_EAVE = ZE + FASCIA
D_EAVE, RAKE, SKIN = 3.0, 3.2, 1.8
S_MAIN, S_CROSS = 1.15, 1.4
V1 = 6.0
V2 = S1 + RH + 3.0 - ZF

# ------------------------------------------------------------------ plan
W, D = 80.0, 64.0
GX0, GX1 = 6.0, 40.0
TC, TAPO = (72.0, 4.0), 13.0
MAIN = Block("main", [(0, 0), (W, 0), (W, D), (0, D)], ZF, ZE)
TURRET = Block("turret", ngon(TC, TAPO, n=12), ZF, ZT)
BLOCKS = [MAIN, TURRET]
SHINGLE = ["fish", "fish", "fish", "diamond", "diamond"]


def _siding(f, b, reg):
    """Rock-faced stone below the belt, fish-scale shingles above (bands of diamonds)."""
    lo = reg ^ rect(-1, -1, f.L + 1, S1 - ZF)
    hi = reg ^ rect(-1, S1 + RH - ZF - 0.01, f.L + 1, 400)
    seed = sum(map(ord, b.name)) + int(f.p0[0] * 7 + f.p0[1] * 3) % 1000
    out = ashlar(lo, course=(2.6, 4.0), length=(4.0, 9.0), d=0.55, seed=seed)
    return out + scallop_rows(hi, 1.6, 1.9, d=0.4, datum=S1 + RH - ZF, shape=SHINGLE)


def _roof_z(x, y):
    d = min(x + D_EAVE, W + D_EAVE - x, y + D_EAVE, D + D_EAVE - y)
    return None if d < 0 else Z_EAVE + S_MAIN * d


def _outside(p, blk, margin):
    return (blk.cs ^ rect(p[0] - margin, p[1] - margin, p[0] + margin, p[1] + margin)).is_empty()


def _openings():
    L = []
    lo = O.window_insert(9.8, 20.2, rise=0, style="pediment", apron=True, qa=True)
    lo2 = O.window_insert(9.8, 20.2, rise=0, style="pediment", apron=True)
    up = O.window_insert(9.1, 18.2, rise=0, style="scroll")
    up_qa = O.window_insert(8.4, 18.2, rise=0, style="scroll", qa=True)
    attic = O.window_insert(7.0, 11.0, rise=None, style="scroll", casing=0.9, ends=0.4, sill_ext=0.3, clip=True)
    tw = O.window_insert(4.0, 15.0, rise=None, style="crest", casing=0.8, ends=0.3, sill_ext=0.2, clip=True)
    tw3 = O.window_insert(4.0, 12.0, rise=None, style="crest", casing=0.8, ends=0.3, sill_ext=0.2, clip=True)
    front = O.door_ornate(12.0, 25.2, leaves=2, transom=4.2, head="swan")
    back = O.door_ornate(10.4, 24.4, leaves=1, transom=4.2, head="pediment")

    def add(blk, x, y, v0, sp, name, kind="window"):
        e, u = blk.locate(x, y)
        L.append(Opening(blk, e, u, v0, sp, name, kind))

    add(MAIN, 47.0, 0.0, 0.4, front, "front-door", "door")
    for x in (14.0, 31.0):
        add(MAIN, x, 0.0, V1, lo, f"front-1-{int(x)}")
        add(MAIN, x, 0.0, V2, up_qa, f"front-2-{int(x)}")
    add(MAIN, 47.0, 0.0, V2, up, "front-2-47")
    add(MAIN, (GX0 + GX1) / 2, 0.0, ZE - ZF + 3.0, attic, "attic")
    for y in (14.0, 34.0, 52.0):
        add(MAIN, 0.0, y, V1, lo2, f"west-1-{int(y)}")
        add(MAIN, 0.0, y, V2, up, f"west-2-{int(y)}")
    for y in (30.0, 50.0):
        add(MAIN, W, y, V1, lo2, f"east-1-{int(y)}")
        add(MAIN, W, y, V2, up, f"east-2-{int(y)}")
    add(MAIN, 58.0, D, 0.4, back, "back-door", "door")
    for x in (16.0, 36.0):
        add(MAIN, x, D, V1, lo2, f"back-1-{int(x)}")
    for x in (16.0, 36.0, 60.0):
        add(MAIN, x, D, V2, up, f"back-2-{int(x)}")
    for k, f in enumerate(TURRET.facades()):
        m = (f.p0 + f.p1) / 2
        mo = m + f.n * 3.0
        if _outside(mo, MAIN, 4.5):
            add(TURRET, m[0], m[1], V1 + 3.0, tw, f"turret-{k}-1")
            add(TURRET, m[0], m[1], V2 + 1.0, tw, f"turret-{k}-2")
        zr = _roof_z(*(m + f.n * 2.0))
        if zr is None or zr < ZT - 17.0 - 2.0:
            add(TURRET, m[0], m[1], ZT - ZF - 17.0, tw3, f"turret-{k}-3")
    return L


OPENINGS = _openings()


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    pieces = [(MAIN.pts, [0, 1, 2, 3], S_MAIN),
              ([(GX0, -(RAKE - D_EAVE)), (GX1, -(RAKE - D_EAVE)), (GX1, 28.0), (GX0, 28.0)], [1, 3], S_CROSS)]
    specs = [dict(p0=(GX0, 0.0), p1=(GX1, 0.0), slope=S_CROSS, e=0.3)]
    rf = G.gabled_roof(pieces, Z_EAVE, D_EAVE, specs, texture=["square", "square", "diamond", "diamond"],
                       skin=SKIN, rake=RAKE, inner_cs=offset(MAIN.cs, -3.0), fascia=FASCIA, hollow=2.6)
    wl = rf["walls"][0]
    gables = [(MAIN, 0, wl["cs"].translate((GX0, Z_EAVE - ZF)))]
    st = stacked_shells(BLOCKS, OPENINGS, [S1], t=3.0, corners="none", siding=_siding, gables=gables,
                        water_table=True)
    kit.add("WALLS-1", "Stone", st["shells"][0], group="walls")
    kit.add("BELT", "Cream", st["rings"][0], group="walls")
    tkeep = TURRET.solid(grow=0.2, dz0=-1, dz1=1)
    no_lip = union([box([GX0 - 1.5, -1, ZE - 1], [GX1 + 1.5, 5.0, ZE + 5]), tkeep,
                    slab(offset(TURRET.cs, 1.0), ZE - 1, ZE + 5)])
    lip = (_corbel(MAIN.cs, 3.0, ZE) + lip_ring(MAIN.cs, 3.0, ZE)) - no_lip
    base = cs_union([MAIN.cs, TURRET.cs])
    tring = slab((offset(TURRET.cs, -0.05) - offset(TURRET.cs, -3.0)) ^ offset(MAIN.cs, -3.05), S1 + RH, ZE + 1.2)
    tring = tring - lip_keep(base, 3.0, S1 + RH)
    kit.add("WALLS-2", "Goldenrod", st["shells"][1] + lip + tring, group="walls")
    kit.add("FOUNDATION", "Granite", foundation(BLOCKS, 0.0, ZF), group="foundation")
    inserts = []
    for o in OPENINGS:
        A = o.local_frame()
        sp = o.spec
        b = sp["cut"].bounds()
        tag = f"{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}"
        key = "DOOR" if o.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, "Cream", "Door" if o.kind == "door" else "Sash", "Glass")
        inserts.append(kit.add(f"{key}-{o.name}", "Windows_Doors", world, P=P, key=f"{key}-{tag}-{o.v0 > 60}",
                               group="inserts", render=zones))
    print("walls + inserts", round(time.time() - t0, 1))

    # --- main roof: hollow patterned-slate hip with the front gable, cut round the turret
    roof = rf["body"] + rf["tex"] + rf["skins"] + rf["skin_tex"]
    zr = Z_EAVE + S_MAIN * (D / 2 + D_EAVE)
    zc = Z_EAVE + S_CROSS * ((GX1 - GX0) / 2 + D_EAVE)
    xm = (GX0 + GX1) / 2
    y_meet = (zc - Z_EAVE) / S_MAIN - D_EAVE + 1.0
    caps = union([G.ridge_cap((D / 2, D / 2), (W - D / 2, D / 2), zr, S_MAIN, ZE),
                  G.ridge_cap((xm, -RAKE), (xm, y_meet), zc, S_CROSS, ZE)])
    walls_env = wl["facade"].place(M.extrude(wl["cs"].offset(0.15), 4.2).translate([0, 0, -3.15]))
    corners = [(-D_EAVE, -D_EAVE), (W + D_EAVE, -D_EAVE), (W + D_EAVE, D + D_EAVE), (-D_EAVE, D + D_EAVE)]
    ends = [(D / 2, D / 2), (W - D / 2, D / 2), (W - D / 2, D / 2), (D / 2, D / 2)]
    hips = union([G.hip_cap((c[0], c[1], Z_EAVE), (e[0], e[1], zr), half=1.3, up=0.7, drop=1.8)
                  for c, e in zip(corners, ends)])
    roof = roof + ((caps + hips) - walls_env)
    roof = roof - lip_keep(MAIN.cs, 3.0, ZE)
    CH = 9.0
    chims = [(W / 2, D / 2)]
    z_low = zr - S_MAIN * (CH / 2) - 0.2
    z0 = round((z_low - 2.4) / 0.2) * 0.2
    solid_env, _ = R.hip_roof(pieces, Z_EAVE, S_MAIN, D_EAVE, texture=None, zlo=ZE)
    for (x, y) in chims:
        roof = roof + G.chimney_seat(solid_env, x, y, CH / 2, zr + 1.0)
    pockets = union([box([x - CH / 2 - 0.4, y - CH / 2 - 0.4, z0], [x + CH / 2 + 0.4, y + CH / 2 + 0.4, zr + 40])
                     for x, y in chims])
    roof = roof - pockets - slab(offset(TURRET.cs, 1.4), ZE - 1, ZT + 40)
    kit.add("ROOF", "Slate", roof, group="roof")
    for k, (x, y) in enumerate(chims):
        ch = FT.chimney(w=CH, dpt=CH, h=round((zr + 16.0 - z0) / 0.2) * 0.2, peg=None, pots=3).translate([x, y, z0])
        kit.add(f"CHIMNEY-{k}", "Brick", ch, key="CHIMNEY", group="roof")
    bb = G.bargeboard(wl["L"], wl["slope"], D_EAVE, skin=SKIN, width=2.4)
    f = wl["facade"]
    A = f.A.copy()
    A[:, 3] = f.world(0.0, 0.0, RAKE)
    kit.add("BARGE", "Cream", bb.transform(A), P=inv34(A), group="roof")
    print("roof", round(time.time() - t0, 1))

    # --- the turret: bracketed cornice and a steep witch's-hat spire with hip rolls
    tpts = TURRET.pts
    teave = R.bracketed_cornice(tpts, ZT, R.CORNICE_SMALL,
                                brackets=dict(z_top=4.6, h=4.2, d0=0.8, d=2.4, t=0.7, pitch=7.0, pair=0.0, margin=3.4),
                                dents=dict(z=3.8, h=0.8, d0=0.8, d=0.7), lip_t=3.0, deck=(6.0, 8.0))
    kit.add("TURRET-eave", "Cream", teave, P=print_flip(), group="turret")
    zc0 = ZT + 8.0
    SP = 3.0
    cone, ctex = R.hip_roof([(tpts, list(range(12)))], zc0, SP, 3.0, texture="fish", tex_kw=dict(pitch=1.55, wtab=1.8, d=0.5))
    inner, _ = R.hip_roof([(tpts, list(range(12)))], zc0 - 2.4 * math.sqrt(1 + SP ** 2), SP, 3.0, texture=None)
    cone = (cone + ctex) - (inner ^ slab(offset(TURRET.cs, -1.0), zc0 - 1, zc0 + 300))
    re = (TAPO + 3.0) / math.cos(math.pi / 12)
    zap = zc0 + SP * (TAPO + 3.0)
    tips = [(TC[0] + re * math.cos(-math.pi / 2 + math.pi / 12 + 2 * math.pi * k / 12),
             TC[1] + re * math.sin(-math.pi / 2 + math.pi / 12 + 2 * math.pi * k / 12)) for k in range(12)]
    hipc = union([G.hip_cap((x, y, zc0), (TC[0], TC[1], zap), half=0.9, up=0.5, drop=1.4) for x, y in tips])
    cone = cone + hipc.trim_by_plane([0, 0, 1.0], zc0 + 0.2)
    zseat = round((zc0 + SP * (TAPO + 3.0) - 3.0) / 0.2) * 0.2
    seat = M.cylinder(1.2, 1.35, 1.35, 32).translate([TC[0], TC[1], zseat - 0.4])
    cone = cone.trim_by_plane([0, 0, -1.0], -zseat) - seat
    kit.add("TURRET-roof", "Slate", cone, group="turret")
    kit.add("TURRET-finial", "Slate", finial(1.3, 12.0).translate([TC[0], TC[1], zseat - 0.4]), group="turret")
    print("turret", round(time.time() - t0, 1))

    # --- wraparound porch round the front and west side, chamfered corner
    PD, CH_ = 16.0, 10.0
    PX1 = 56.0
    ppoly = [(-PD + CH_, -PD), (PX1, -PD), (PX1, 0.0), (0.0, 0.0), (0.0, 44.0), (-PD, 44.0), (-PD, -PD + CH_)]
    c135 = 0.663
    Lc = math.hypot(CH_, CH_)
    Lf = PX1 - (-PD + CH_)
    runs = [dict(a=(0.0, 44.0), b=(-PD, 44.0), posts=[3.2, PD - 1.6]),
            dict(a=(-PD, 44.0), b=(-PD, -PD + CH_), posts=[1.6, 18.0, 34.0, 44.0 + PD - CH_ - c135]),
            dict(a=(-PD, -PD + CH_), b=(-PD + CH_, -PD), posts=[c135, Lc - c135]),
            dict(a=(-PD + CH_, -PD), b=(PX1, -PD), posts=[c135, 16.0, 31.0, 46.0, Lf - 1.6]),
            dict(a=(PX1, -PD), b=(PX1, 0.0), posts=[1.6, PD - 3.2])]
    H_floor = ZF - 2.0
    post_h = 47.0 - H_floor
    P = FT.porch_turned(ppoly, runs, H_floor, post_h, steps_at=[(3, 47.0 - (-PD + CH_), 11.0)], boards=dict(pitch=1.8),
                        joined=True, ledger_off=1.5)
    fkeep = slab(offset(base, 0.8 + 0.55 + 0.15), -1, ZF + 1.3)
    ins_keep = union([box(np.array(p.solid.bounding_box()[:3]) - 0.2, np.array(p.solid.bounding_box()[3:]) + 0.2)
                      for p in inserts if p is not None])
    kit.add("PORCH-deck", "Cream", P["deck"] - fkeep, P=print_flip(), group="porch")
    kit.add("PORCH-floor", "PorchGray", P["floor"] - fkeep, P=print_flip(), group="porch")
    tabs = union([arc for arc, _ in P["arcades"]])
    fnd = foundation(BLOCKS, 0.0, ZF)
    for k, fr in enumerate(sorted(P["frames"], key=lambda m: -m.volume())):
        kit.add(f"PORCH-frame-{k}", "Cream", fr - tabs - fnd, group="porch")
    for k, (arc, A) in enumerate(P["arcades"]):
        kit.add(f"PORCH-arcade-{k}", "Cream", arc, P=compose(FT.ARCADE_PRINT, inv34(A)), group="porch")
    bld_keep = MAIN.solid(grow=2.0, dz0=-20, dz1=0) + TURRET.solid(grow=2.0, dz0=-20, dz1=0)
    proof = P["roof"] - bld_keep - ins_keep
    ptop = proof.bounding_box()[5]
    kit.add("PORCH-roof", "Cream", proof.trim_by_plane([0, 0, -1.0], -(ptop - 0.8)), P=print_flip(), group="porch")
    kit.add("PORCH-roof-tin", "Slate", proof.trim_by_plane([0, 0, 1.0], ptop - 0.8), group="porch")
    for k, (sm, A) in enumerate(P["steps"]):
        kit.add(f"PORCH-steps-{k}", "Granite", sm.transform(A) - fkeep, group="porch")
    e, u = MAIN.locate(58.0, D)
    f = MAIN.facades()[e]
    A = f.A.copy()
    A[:, 3] = f.world(u, -ZF, 1.4)
    kit.add("STOOP-back", "Granite", FT.steps(13.0, ZF - 0.6, 4).transform(A), group="porch")
    print("porch", round(time.time() - t0, 1))
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "carrow")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:40]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "carrow.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))

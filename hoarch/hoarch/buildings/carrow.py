"""The Carrow -- an original HO-scale (1:87.1) Queen Anne "castle" for the lineup. Rev B: the
house-size plan (168 x 132 mm, storeys of 42 and 38 mm) and built-up cornices at every level.

A first storey of long, thin Roman brick under a half-timbered second storey; a round
(twelve-sided) turret at the front corner rising a storey above the eaves to its own cornice and
a steep witch's-hat spire of diamond slate with a spire finial; a steep diamond-slate hip with a
front gable carrying an arch-braced Tudor truss over a Palladian attic window; Free Classic
windows (fluted jambs, dentils, pediments with oculi, diamond-paned upper sash); a sidelighted
entrance with an oval-light door; a coursed-stone foundation, an arcaded Roman-brick chimney;
and an Eastlake porch (chamfered posts with incised blocks, sawn balusters, a fretwork frieze,
an arched skirt on stone piers) wrapping the front and the west side round a chamfered corner.

- Between the storeys a three-part cornice: a plum frieze of strapwork (outlined tablets with
  an eye, square bosses between), a cream egg-and-dart course and a cream cyma-reversa crown.
- At the eave (round the house and the turret): a plum frieze of Tudor roses, a cream dentil
  course, a cream soffit on modillions and a plum cyma crown.
- Round the turret's top a cream crenellated frieze (merlons with slits), a plum soffit on
  volute brackets and a cream ovolo crown under the spire.

usage: python3 -m hoarch.buildings.carrow [check] [export]
"""
import math
import os
import sys
import time

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import box, compose, cs_union, inv34, ngon, offset, poly, rect, slab, union
from hoarch import cornice as CO, features as FT, gables as G, openings as O, roof as R, skins as SK, trimwork as TW
from hoarch.kit import Kit, print_flip
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, stacked_shells

NAME = "Carrow Queen Anne Castle"
COLORS = {"PorchDeck": "#EDE3C8", "Planks": "#6F5034",       # the planked porch deck: two colours, one change
          "Tawny": "#A4683F", "Lavender": "#9A88A8", "Cream": "#EDE3C8", "Slate": "#3F4A4F", "Granite": "#6F6D6A",
          "Brick": "#8A3B2B", "PorchGray": "#6B706F", "Plum": "#5B3A5E", "Windows_Doors": "#EDE3C8"}
RENDER_MAT = {"PorchDeck": "trim", "Planks": "planks",
              "Tawny": "stone_wall", "Lavender": "siding", "Cream": "trim", "Slate": "roof", "Granite": "stone",
              "Brick": "brick", "PorchGray": "porchfloor", "Plum": "accent", "Windows_Doors": "trim", "Sash": "sash",
              "Door": "door", "Glass": "glass"}

# ------------------------------------------------------------------ cornices (unique to the Carrow)
LEDGE = 1.4
JOINT = dict(pitch=12.0, margin=4.0, layers=[
    dict(kind="frieze", h=4.8, b=1.2, orn="strapwork", role="Plum"),
    dict(kind="course", h=1.6, b=1.4, orn="eggdart", role="Cream"),
    dict(kind="crown", h=2.2, b=1.4, P=3.6, orn="reverse", role="Cream")])
EAVE = dict(pitch=12.0, margin=4.0, layers=[
    dict(kind="frieze", h=5.6, b=1.2, orn="roses", role="Plum"),
    dict(kind="course", h=1.6, b=1.4, orn="dentil", role="Cream", tooth=0.9, gap=0.6),
    dict(kind="bed", h=2.2, b=1.4, P=6.4, role="Cream", brackets=dict(style="modillion", t=1.0, reach=0.5)),
    dict(kind="crown", h=2.8, b=1.4, P=7.0, orn="cyma", role="Plum")])
TURRET_C = dict(pitch=8.0, margin=2.4, layers=[
    dict(kind="frieze", h=4.6, b=1.2, orn="crenels", role="Cream"),
    dict(kind="bed", h=1.8, b=1.4, P=5.0, role="Plum", brackets=dict(style="volute", t=0.8, reach=0.7)),
    dict(kind="crown", h=2.2, b=1.4, P=5.8, orn="ovolo", role="Cream")])
RJ = round((LEDGE + 0.4 + CO.band_height(JOINT)) / 0.2) * 0.2
HE = CO.band_height(EAVE)

# ------------------------------------------------------------------ levels (on the 0.2 mm grid)
ZF = 14.0
S1 = ZF + 42.0
ZE = S1 + RJ + 38.0
ZW = ZE + HE                     # the wall top behind the eave cornice; the roof sits here
ZT = ZW + 34.0                   # the turret's ledge
ZTW = ZT + CO.band_height(TURRET_C)
FASCIA = 2.0
Z_EAVE = ZW + FASCIA
D_EAVE, RAKE, SKIN = 7.4, 7.8, 1.8
S_MAIN, S_CROSS = 1.15, 1.4
V1 = 8.0
V2 = S1 + RJ + 5.0 - ZF

# ------------------------------------------------------------------ plan
W, D = 168.0, 132.0
GX0, GX1 = 12.0, 84.0
TC, TAPO = (148.0, 6.0), 22.0
MAIN = Block("main", [(0, 0), (W, 0), (W, D), (0, D)], ZF, ZW)
TURRET = Block("turret", ngon(TC, TAPO, n=12), ZF, ZTW)
BLOCKS = [MAIN, TURRET]
SLATE = "diamond"
DOOR_X = 104.0


def _siding(f, b, reg):
    """Roman brick below the joint; half-timbering above (posts, rails at the sill and head
    lines, braces), the turret and the front gable included; nothing in the cornice bands."""
    reg = reg - rect(-1, ZE - b.z0, f.L + 1, ZW - b.z0)
    if b is TURRET:
        reg = reg - rect(-1, ZT - b.z0, f.L + 1, 999)
    lo = reg ^ rect(-1, -1, f.L + 1, S1 - ZF)
    hi = reg ^ rect(-1, S1 + RJ - ZF - 0.01, f.L + 1, 400)
    out = SK.brick_bond(lo, "roman", bl=3.8, bh=0.6, datum=1.8, uoff=(f.p0[0] + f.p0[1]) % 1.9)
    return out + SK.half_timber(hi, rails=(V2 - 1.0, V2 + 22.6), post_pitch=7.2)


def _roof_z(x, y):
    d = min(x + D_EAVE, W + D_EAVE - x, y + D_EAVE, D + D_EAVE - y)
    return None if d < 0 else Z_EAVE + S_MAIN * d


def _outside(p, blk, margin):
    return (blk.cs ^ rect(p[0] - margin, p[1] - margin, p[0] + margin, p[1] + margin)).is_empty()


def _openings():
    L = []
    lo = O.window_fc(9.6, 24.0)
    lo2 = O.window_fc(9.6, 24.0)
    up = O.window_fc(9.2, 21.0, pediment=False)
    up_qa = up
    attic = O.window_palladian(6.4, 14.0)
    tw = O.window_insert(6.0, 19.0, rise=None, style="crest", casing=0.8, ends=0.3, sill_ext=0.2, clip=True)
    tw3 = O.window_insert(6.0, 15.0, rise=None, style="crest", casing=0.8, ends=0.3, sill_ext=0.2, clip=True)
    front = O.door_fc(10.0, 29.0, side=2.6)
    back = O.door_fc(9.4, 27.0, side=1.8)

    def add(blk, x, y, v0, sp, name, kind="window"):
        e, u = blk.locate(x, y)
        L.append(Opening(blk, e, u, v0, sp, name, kind))

    add(MAIN, DOOR_X, 0.0, 0.4, front, "front-door", "door")
    for x in (30.0, 66.0):
        add(MAIN, x, 0.0, V1, lo, f"front-1-{int(x)}")
        add(MAIN, x, 0.0, V2, up_qa, f"front-2-{int(x)}")
    add(MAIN, DOOR_X, 0.0, V2, up, "front-2-104")
    add(MAIN, (GX0 + GX1) / 2, 0.0, ZW - ZF + 4.0, attic, "attic")
    for y in (30.0, 70.0, 110.0):
        add(MAIN, 0.0, y, V1, lo2, f"west-1-{int(y)}")
        add(MAIN, 0.0, y, V2, up, f"west-2-{int(y)}")
    for y in (64.0, 108.0):
        add(MAIN, W, y, V1, lo2, f"east-1-{int(y)}")
        add(MAIN, W, y, V2, up, f"east-2-{int(y)}")
    add(MAIN, 124.0, D, 0.4, back, "back-door", "door")
    for x in (34.0, 76.0):
        add(MAIN, x, D, V1, lo2, f"back-1-{int(x)}")
    for x in (34.0, 76.0, 128.0):
        add(MAIN, x, D, V2, up, f"back-2-{int(x)}")
    for k, f in enumerate(TURRET.facades()):        # lights on every other face only
        if k % 2:
            continue
        m = (f.p0 + f.p1) / 2
        mo = m + f.n * 3.0
        if _outside(mo, MAIN, 4.5):
            add(TURRET, m[0], m[1], V1 + 3.0, tw, f"turret-{k}-1")
            add(TURRET, m[0], m[1], V2 + 1.0, tw, f"turret-{k}-2")
        zr = _roof_z(*(m + f.n * 2.0))
        if zr is None or zr < ZT - 21.0 - 2.0:
            add(TURRET, m[0], m[1], ZT - ZF - 21.0, tw3, f"turret-{k}-3")
    return L


OPENINGS = _openings()


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    pieces = [(MAIN.pts, [0, 1, 2, 3], S_MAIN),
              ([(GX0, -(RAKE - D_EAVE)), (GX1, -(RAKE - D_EAVE)), (GX1, 28.0), (GX0, 28.0)], [1, 3], S_CROSS)]
    specs = [dict(p0=(GX0, 0.0), p1=(GX1, 0.0), slope=S_CROSS, e=0.3)]
    rf = G.gabled_roof(pieces, Z_EAVE, D_EAVE, specs, texture=SLATE, tex_kw=dict(pitch=1.5, wtab=1.8, d=0.4),
                       skin=SKIN, rake=RAKE, inner_cs=offset(MAIN.cs, -3.0), fascia=FASCIA, hollow=2.6)
    wl = rf["walls"][0]
    gables = [(MAIN, 0, wl["cs"].translate((GX0, Z_EAVE - ZF)))]
    base = cs_union([MAIN.cs, TURRET.cs])
    eave_path = max(base.to_polygons(), key=lambda L_: abs(poly(L_).area()))
    undress = [slab(offset(base, 8.0), ZE - LEDGE - 0.6, ZW + 0.01),
               slab(offset(TURRET.cs, 8.0), ZT - LEDGE - 0.6, ZTW + 0.01)]
    st = stacked_shells(BLOCKS, OPENINGS, [S1], t=3.0, corners="none", siding=_siding, gables=gables,
                        water_table=True, prof=CO.joint_profile(RJ, LEDGE), belt_blocks=None, undress=undress)
    kit.add("WALLS-1", "Tawny", st["shells"][0], group="walls")
    kit.add("JOINT", "Tawny", st["rings"][0], group="walls")
    tkeep = TURRET.solid(grow=0.2, dz0=-1, dz1=1)
    no_lip = union([box([GX0 - D_EAVE - 0.6, -1, ZW - 1], [GX1 + D_EAVE + 0.6, 5.0, ZW + 5]), tkeep,
                    slab(offset(TURRET.cs, 1.0), ZW - 1, ZW + 5)])
    lip = (_corbel(MAIN.cs, 3.0, ZW) + lip_ring(MAIN.cs, 3.0, ZW)) - no_lip
    tring = slab((offset(TURRET.cs, -0.05) - offset(TURRET.cs, -3.0)) ^ offset(MAIN.cs, -3.05), S1 + RJ, ZW + 1.2)
    tring = tring - lip_keep(base, 3.0, S1 + RJ)
    ledges = CO.ledge(eave_path, ZE, LEDGE) + CO.ledge(TURRET.pts, ZT, LEDGE)
    tlip = _corbel(TURRET.cs, 3.0, ZTW) + lip_ring(TURRET.cs, 3.0, ZTW)
    kit.add("WALLS-2", "Lavender", st["shells"][1] + lip + tring + ledges + tlip, group="walls")
    rings, _ = CO.level(st["outlines"][0], S1 + LEDGE + 0.4, JOINT)
    CO.add_level(kit, rings, "CORNICE-J", "cornice")
    # the eave's rings wrap the turret: parted where they meet it and halved round it (to fit)
    cut = CO.blades(CO.tower_cuts(eave_path, TC, TAPO + 8.0, wall=TAPO, away=(1.0, -1.0), tower=TURRET.pts,
                                   house=MAIN.pts), ZE, ZW)
    rings, _ = CO.level(eave_path, ZE, EAVE, cut=cut)
    CO.add_level(kit, rings, "CORNICE-E", "cornice")
    kit.add("FOUNDATION", "Granite", foundation(BLOCKS, 0.0, ZF, style="coursed"), group="foundation")
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
    caps = union([G.ridge_cap((D / 2, D / 2), (W - D / 2, D / 2), zr, S_MAIN, ZW),
                  G.ridge_cap((xm, -RAKE), (xm, y_meet), zc, S_CROSS, ZW)])
    # the gable wall and the space under the rake skin in front of it (no cap pokes below the skin)
    walls_env = wl["facade"].place(M.extrude(wl["cs"].offset(0.15), RAKE + 4.2).translate([0, 0, -3.15]))
    corners = [(-D_EAVE, -D_EAVE), (W + D_EAVE, -D_EAVE), (W + D_EAVE, D + D_EAVE), (-D_EAVE, D + D_EAVE)]
    ends = [(D / 2, D / 2), (W - D / 2, D / 2), (W - D / 2, D / 2), (D / 2, D / 2)]
    hips = union([G.hip_cap((c[0], c[1], Z_EAVE), (e[0], e[1], zr), half=1.3, up=0.7, drop=1.8)
                  for c, e in zip(corners, ends)])
    roof = roof + ((caps + hips) - walls_env)
    roof = roof.trim_by_plane([0, 0, 1.0], ZW) - lip_keep(MAIN.cs, 3.0, ZW)
    CH = 12.0
    chims = [(W / 2, D / 2)]
    z_low = zr - S_MAIN * (CH / 2) - 0.2
    z0 = round((z_low - 2.4) / 0.2) * 0.2
    solid_env, _ = R.hip_roof(pieces, Z_EAVE, S_MAIN, D_EAVE, texture=None, zlo=ZW)
    for (x, y) in chims:
        roof = roof + G.chimney_seat(solid_env, x, y, CH / 2, zr + 1.0)
    pockets = union([box([x - CH / 2 - 0.4, y - CH / 2 - 0.4, z0], [x + CH / 2 + 0.4, y + CH / 2 + 0.4, zr + 40])
                     for x, y in chims])
    # round the turret, and trimmed under its roof's eave where the front hip climbs past it
    dt_t = TURRET_C["layers"][-1]["P"] + 0.6
    roof = roof - pockets - slab(offset(TURRET.cs, 1.4), ZW - 1, ZTW + 90) \
        - slab(offset(TURRET.cs, dt_t + 0.6), ZTW - 0.2, ZTW + 90)
    kit.add("ROOF", "Slate", roof, group="roof")
    for k, (x, y) in enumerate(chims):
        ch = TW.chimney("arched", w=CH, d=CH, h=round((zr + 20.0 - z0) / 0.2) * 0.2).translate([x, y, z0])
        kit.add(f"CHIMNEY-{k}", "Brick", ch, key="CHIMNEY", group="roof")
    bb = G.gable_tudor(wl["L"], wl["slope"], D_EAVE, skin=SKIN)
    f = wl["facade"]
    A = f.A.copy()
    A[:, 3] = f.world(0.0, 0.0, RAKE)
    kit.add("GABLE-truss", "Cream", bb.transform(A), P=inv34(A), group="roof")
    print("roof", round(time.time() - t0, 1))

    # --- the turret: its own cornice (cut where the main roof climbs past it) and a steep
    # witch's-hat spire with hip rolls
    t_env, _ = R.hip_roof(pieces, Z_EAVE + 1.4, S_MAIN, D_EAVE + 1.4, texture=None, zlo=ZW)
    rings, _ = CO.level(TURRET.pts, ZT, TURRET_C, cut=t_env)
    CO.add_level(kit, rings, "CORNICE-T", "turret")
    tpts = TURRET.pts
    dt = TURRET_C["layers"][-1]["P"] + 0.6
    zc0 = ZTW + 1.4
    SP = 3.0
    cone, ctex = R.hip_roof([(tpts, list(range(12)))], zc0, SP, dt, texture=SLATE, tex_kw=dict(pitch=1.55, wtab=1.8, d=0.5),
                            zlo=ZTW)
    inner, _ = R.hip_roof([(tpts, list(range(12)))], zc0 - 2.4 * math.sqrt(1 + SP ** 2), SP, dt, texture=None)
    cone = (cone + ctex) - (inner ^ slab(offset(TURRET.cs, -3.2), ZTW - 1, zc0 + 400)) - lip_keep(TURRET.cs, 3.0, ZTW)
    re = (TAPO + dt) / math.cos(math.pi / 12)
    zap = zc0 + SP * (TAPO + dt)
    tips = [(TC[0] + re * math.cos(-math.pi / 2 + math.pi / 12 + 2 * math.pi * k / 12),
             TC[1] + re * math.sin(-math.pi / 2 + math.pi / 12 + 2 * math.pi * k / 12)) for k in range(12)]
    hipc = union([G.hip_cap((x, y, zc0), (TC[0], TC[1], zap), half=0.9, up=0.5, drop=1.4) for x, y in tips])
    cone = cone + hipc.trim_by_plane([0, 0, 1.0], zc0 + 0.2)
    zseat = round((zc0 + SP * (TAPO + dt) - 3.0) / 0.2) * 0.2
    seat = M.cylinder(1.2, 1.7, 1.7, 32).translate([TC[0], TC[1], zseat - 0.4])         # the finial's base, 1.6
    cone = cone.trim_by_plane([0, 0, -1.0], -zseat) - seat
    kit.add("TURRET-roof", "Slate", cone, group="turret")
    kit.add("TURRET-finial", "Slate", TW.finial("spire", 1.6, 16.0).translate([TC[0], TC[1], zseat - 0.4]), group="turret")
    print("turret", round(time.time() - t0, 1))

    # --- wraparound porch round the front and west side, chamfered corner
    PD, CH_ = 26.0, 16.0
    PX1 = 118.0
    PY1 = 90.0
    ppoly = [(-PD + CH_, -PD), (PX1, -PD), (PX1, 0.0), (0.0, 0.0), (0.0, PY1), (-PD, PY1), (-PD, -PD + CH_)]
    c135 = 0.663
    Lc = math.hypot(CH_, CH_)
    Lf = PX1 - (-PD + CH_)
    Lw = PY1 + PD - CH_
    runs = [dict(a=(0.0, PY1), b=(-PD, PY1), posts=[3.2, PD - 1.6]),
            dict(a=(-PD, PY1), b=(-PD, -PD + CH_), posts=[1.6, 26.0, 50.0, 74.0, Lw - c135]),
            dict(a=(-PD, -PD + CH_), b=(-PD + CH_, -PD), posts=[c135, Lc - c135]),
            dict(a=(-PD + CH_, -PD), b=(PX1, -PD), posts=[c135, 28.0, 56.0, 82.0, 102.0, Lf - 1.6]),
            dict(a=(PX1, -PD), b=(PX1, 0.0), posts=[1.6, PD - 3.2])]
    H_floor = ZF - 1.4
    post_h = S1 - 2.0 - 5.6 - H_floor              # the roof tucks under the joint's ledge
    P = FT.porch_turned(ppoly, runs, H_floor, post_h, steps_at=[(3, DOOR_X - (-PD + CH_), 18.0)],
                        planks=dict(pitch=1.5, border=1.6),
                        joined=True, ledger_off=1.5, post="eastlake", rail="sawn", arcade="fret", skirt="arches",
                        pier_tex="coursed", roof_edge="reeded", top=True)
    fkeep = slab(offset(base, 0.8 + 0.55 + 0.15), -1, ZF + 1.3)
    ins_keep = union([box(np.array(p.solid.bounding_box()[:3]) - 0.2, np.array(p.solid.bounding_box()[3:]) + 0.2)
                      for p in inserts if p is not None])
    deck = P["deck"] - fkeep           # planks and frame in one part: wood planks, one filament change
    kit.add("PORCH-deck", "PorchDeck", deck, P=print_flip(), group="porch",
            render=FT.plank_zones(deck, H_floor, "Planks", "PorchDeck"))
    bld_keep = MAIN.solid(grow=2.0, dz0=-20, dz1=0) + TURRET.solid(grow=2.0, dz0=-20, dz1=0)
    fnd = foundation(BLOCKS, 0.0, ZF, style="coursed")
    FT.add_porch_top(kit, "PORCH", P, bld_keep + ins_keep + fnd, "Cream", "Cream", tin_col="Slate")
    for k, (sm, A) in enumerate(P["steps"]):
        kit.add(f"PORCH-steps-{k}", "Granite", sm.transform(A) - fkeep, group="porch")
    e, u = MAIN.locate(124.0, D)
    f = MAIN.facades()[e]
    A = f.A.copy()
    A[:, 3] = f.world(u, -ZF, 1.4)
    kit.add("STOOP-back", "Granite", FT.steps(15.0, ZF - 0.6, 5).transform(A), group="porch")
    print("porch", round(time.time() - t0, 1))
    # glue joints: nothing small is left butted on a dab of glue (see NOTES.md)
    FT.crown(kit, "TURRET-finial", "TURRET-roof")
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

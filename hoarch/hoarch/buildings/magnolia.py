"""The Magnolia -- an original HO-scale (1:87.1) twin-gabled house with an entry loggia, the last
of the batch, combining the photos' paired gables with the Larkspur's loggia idea turned
round: here the loggia is sunk into the ground storey between the gables. Rev B: the house-size
plan (208 x 128 mm, storeys of 42 and 38 mm), framed windows spaced along the walls, and
built-up cornices at every level.

A ground storey of red brick in English cross bond on a base of V-jointed ashlar, a brick
corbel table with dentil headers at the floor line, and butterscotch step-cut shingles above
with dentilled corner boards. Two steep front gables stand over the ends of the front, each
with an arcade gable ornament (raking boards, a band pierced with little round arches with
drops under its piers, a king post carrying a ring, a spike); a hipped roof between and
behind them in charcoal arch-cut shingles, and a pilastered brick chimney. Between the gables
an entry loggia is sunk into the ground storey behind a screen of three segmental arches on
square piers with impost blocks and keystones, up a flight of steps. Windows with a cross
of bars in the upper sash under lambrequin head boards; doors with a spoked round light over
a panel under an arched-bar transom. Between the storeys a three-part cornice (an ivory frieze of
little arches, a chocolate course of modillion blocks and an ivory ovolo crown) that carries on
over the loggia; at the eave a four-part one (a chocolate frieze of lozenges, an ivory
egg-and-dart course, an ivory soffit on stepped brackets and a chocolate cyma crown).

usage: python3 -m hoarch.buildings.magnolia [check] [export]
"""
import math
import os
import sys
import time

import numpy as np
from manifold3d import JoinType, Manifold as M

from hoarch.core import arch_cs, box, cs_union, inv34, offset, poly, rect, scallop_rows, slab, union
from hoarch import cornice as CO, features as FT, gables as G, openings as O, roof as R, skins as SK, storefront as SF, \
    trimwork as TW
from hoarch.kit import Kit, print_flip
from hoarch.ornament import chamfer_box, ext
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, stacked_shells

NAME = "The Magnolia"
COLORS = {"Brick": "#9A4A37", "Butterscotch": "#D9A35B", "Ivory": "#F1EBDD", "Chocolate": "#4A3228",
          "Charcoal": "#3B3D40", "Limestone": "#C9C2B2", "Windows_Doors": "#F1EBDD"}
RENDER_MAT = {"Brick": "brick", "Butterscotch": "siding", "Ivory": "trim", "Chocolate": "chocolate", "Charcoal": "roof",
              "Limestone": "stone", "Windows_Doors": "trim", "Sash": "sash", "Door": "door", "Glass": "glass"}

# ------------------------------------------------------------------ cornices (unique to the Magnolia)
LEDGE = 1.4
JOINT = dict(pitch=12.0, margin=4.0, layers=[
    dict(kind="frieze", h=4.4, b=1.2, orn="arcade", role="Ivory"),
    dict(kind="course", h=1.8, b=1.4, orn="blocks", role="Chocolate", d=1.0),
    dict(kind="crown", h=2.2, b=1.4, P=3.8, orn="ovolo", role="Ivory")])
EAVE = dict(pitch=12.0, margin=4.0, layers=[
    dict(kind="frieze", h=5.4, b=1.2, orn="lozenges", role="Chocolate"),
    dict(kind="course", h=1.6, b=1.4, orn="eggdart", role="Ivory"),
    dict(kind="bed", h=2.0, b=1.4, P=6.2, role="Ivory", brackets=dict(style="stepped", t=1.0, reach=0.55)),
    dict(kind="crown", h=2.8, b=1.4, P=7.0, orn="cyma", role="Chocolate")])
RJ = round((LEDGE + 0.4 + CO.band_height(JOINT)) / 0.2) * 0.2
HE = CO.band_height(EAVE)

# ------------------------------------------------------------------ levels (on the 0.2 mm grid)
ZF = 12.0
S1 = ZF + 42.0                  # first-storey shell top = the joint ring's foot
ZE = S1 + RJ + 38.0             # the eave ledge's top
ZW = ZE + HE                    # the wall top behind the eave cornice; the roof sits here
FASCIA = 1.8
Z_EAVE = ZW + FASCIA
D_EAVE, RAKE, SKIN = 7.4, 4.2, 1.8
S_MAIN, S_GABLE = 0.9, 1.35
V1 = 8.0
V2 = S1 + RJ + 5.0 - ZF
RH = RJ

# ------------------------------------------------------------------ plan
W, D = 208.0, 128.0
G1, G2 = (8.0, 68.0), (140.0, 200.0)      # the twin front gables' spans on the front wall
LX0, LX1, LD = 76.0, 132.0, 20.0          # the entry loggia sunk into the ground storey
MAIN_LO = Block("main", [(0, 0), (LX0, 0), (LX0, LD), (LX1, LD), (LX1, 0), (W, 0), (W, D), (0, D)], ZF, S1)
MAIN_HI = Block("upper", [(0, 0), (W, 0), (W, D), (0, D)], S1, ZW)
BLOCKS = [MAIN_LO, MAIN_HI]
DOOR_X = (LX0 + LX1) / 2


def _siding(f, b, reg):
    """English cross bond brick on the ground storey; step-cut shingles above the joint and in
    the gables; nothing behind the eave cornice."""
    out = []
    if b is MAIN_LO:
        out.append(SK.brick_bond(reg, "cross", bl=2.4, bh=0.8, mortar=0.5, bed=0.2, d=0.3))
    else:
        reg = reg - rect(-1, ZE - b.z0, f.L + 1, ZW - b.z0)
        out.append(scallop_rows(reg, 1.6, 2.2, d=0.42, datum=RH, shape="step", lap=2.0))
    return union(out) if out else M()


def _openings():
    L = []

    def win(w, h, rise=0, head="lambrequin"):
        return SF.window_commercial(w, h, rise=rise, lites=(1, 1), rows=(1, 1), sill=1.2, head=head, upper="cross",
                                    casing=1.3, band=True)

    def add(blk, x, y, v0, sp, name, kind="window"):
        e, u = blk.locate(x, y)
        L.append(Opening(blk, e, u, v0, sp, name, kind))

    door = lambda w, h, lv=1: SF.door_commercial(w, h, transom=4.4, leaf="wheel", tstyle="archbar", head=None, leaves=lv)
    add(MAIN_LO, DOOR_X, LD, 0.0, door(13.0, 30.0, 2), "door", "door")
    v2 = V2 - (S1 - ZF)
    for gm in ((G1[0] + G1[1]) / 2, (G2[0] + G2[1]) / 2):
        for x in (gm - 13.0, gm + 13.0):
            add(MAIN_LO, x, 0.0, V1, win(8.4, 24.0), f"F{x:.0f}-1")
            add(MAIN_HI, x, 0.0, v2, win(8.4, 21.0), f"F{x:.0f}-2")
        add(MAIN_HI, gm, 0.0, ZW - S1 + 5.0, win(8.0, 15.0, head=None, rise=4.0), f"G{gm:.0f}")
    for x in (DOOR_X - 13.0, DOOR_X + 13.0):
        add(MAIN_HI, x, 0.0, v2, win(8.4, 21.0), f"F{x:.0f}-2")
    for y in (30.0, 64.0, 98.0):
        for x0, nm in ((0.0, "W"), (W, "E")):
            add(MAIN_LO, x0, y, V1, win(8.4, 24.0), f"{nm}{y:.0f}-1")
            add(MAIN_HI, x0, y, v2, win(8.4, 21.0), f"{nm}{y:.0f}-2")
    add(MAIN_LO, 160.0, D, 0.0, door(10.0, 28.0), "back-door", "door")
    for x in (32.0, 72.0, 112.0):
        add(MAIN_LO, x, D, V1, win(8.4, 24.0), f"B{x:.0f}-1")
    for x in (32.0, 72.0, 112.0, 160.0):
        add(MAIN_HI, x, D, v2, win(8.4, 21.0), f"B{x:.0f}-2")
    return L


OPENINGS = _openings()


def loggia_screen():
    """The loggia's front: three segmental arches on two square piers and two end pilasters,
    each pier with a base block and a projecting impost, a keystone at every crown, and a
    string course along the top. Built lying on its back in (u along the loggia, v up from its
    floor, w from its back at 0 to its face at 3); prints on its back."""
    L = LX1 - LX0 - 2.4                  # clear of the side walls' brick and corner boards
    Hs = S1 - ZF
    t = 3.0
    pier = 4.0
    edges = [(0.0, 2.4), (L / 3 - pier / 2, L / 3 + pier / 2), (2 * L / 3 - pier / 2, 2 * L / 3 + pier / 2), (L - 2.4, L)]
    spring = Hs - 12.0
    wall = rect(0.0, 0.0, L, Hs)
    holes, crowns = [], []
    for (a0, a1), (b0, b1) in zip(edges[:-1], edges[1:]):
        span_ = b0 - a1
        rise = span_ * 0.22
        holes.append(cs_union([rect(a1, -1.0, b0, spring), arch_cs(a1, b0, spring - 0.01, spring, rise=rise, seg=32)]))
        crowns.append(((a1 + b0) / 2, spring + rise))
    body = ext(wall - cs_union(holes), 0.0, t)
    for cu, cv in crowns:                                                  # keystones, proud of the face
        body = body + ext(poly([(cu - 0.7, cv - 0.6), (cu + 0.7, cv - 0.6), (cu + 1.0, cv + 1.8), (cu - 1.0, cv + 1.8)]),
                          t - 0.01, t + 0.6)
    for a0, a1 in edges:                                                   # base blocks and imposts
        body = body + chamfer_box(a0 - 0.2, 0.0, a1 + 0.2, 1.8, t - 0.2, 0.6, c=0.2)      # faces on the layer grid
        body = body + chamfer_box(a0 - 0.4, spring - 1.2, a1 + 0.4, spring, t - 0.2, 0.8, c=0.2)
    body = body + chamfer_box(0.0, Hs - 1.6, L, Hs, t - 0.2, 0.8, c=0.2)    # the string course
    return body


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    r = RAKE - D_EAVE
    zg = Z_EAVE + S_GABLE * ((G1[1] - G1[0]) / 2 + D_EAVE)
    gy = 60.0                                            # the gables' back ends are hips, buried in the main roof
    pieces = [(MAIN_HI.pts, [0, 1, 2, 3], S_MAIN)]
    specs = []
    for g in (G1, G2):
        pieces.append(([(g[0], -r), (g[1], -r), (g[1], gy), (g[0], gy)], [1, 2, 3], S_GABLE))
        specs.append(dict(p0=(g[0], 0.0), p1=(g[1], 0.0), slope=S_GABLE, e=0.3))
    rf = G.gabled_roof(pieces, Z_EAVE, D_EAVE, specs, texture="arch", tex_kw=dict(pitch=1.5, wtab=2.2, d=0.42),
                       skin=SKIN, rake=RAKE, inner_cs=offset(MAIN_HI.cs, -3.0), fascia=FASCIA, hollow=2.6)
    gables = [(MAIN_HI, 0, wl["cs"].translate((g[0], Z_EAVE - S1))) for g, wl in zip((G1, G2), rf["walls"])]
    undress = [slab(offset(MAIN_HI.cs, 8.0), ZE - LEDGE - 0.6, ZW + 0.01)]
    st = stacked_shells(BLOCKS, OPENINGS, [S1], t=3.0, corners="dentilled", siding=_siding, gables=gables,
                        prof=CO.joint_profile(RJ, LEDGE), belt_blocks=None, water_table=False, undress=undress)
    over_loggia = box([LX0, -1.0, S1 - 6.0], [LX1, LD + 0.1, S1 + 2.0])     # no corbel or lip hangs over the loggia
    kit.add("WALLS-1", "Brick", st["shells"][0] - over_loggia, group="walls")
    ceiling = box([LX0 + 0.05, 2.9, S1], [LX1 - 0.05, LD + 0.1, S1 + 0.8])
    kit.add("JOINT", "Brick", st["rings"][0] + ceiling, group="walls")
    no_lip = union([box([g[0] - D_EAVE - 0.6, -1, ZW - 1], [g[1] + D_EAVE + 0.6, 5.0, ZW + 5]) for g in (G1, G2)])
    lip = (_corbel(MAIN_HI.cs, 3.0, ZW) + lip_ring(MAIN_HI.cs, 3.0, ZW)) - no_lip
    kit.add("WALLS-2", "Butterscotch", st["shells"][1] + lip + CO.ledge(MAIN_HI.pts, ZE, LEDGE), group="walls")
    for tag, path, z0, spec in (("J", st["outlines"][0], S1 + LEDGE + 0.4, JOINT), ("E", MAIN_HI.pts, ZE, EAVE)):
        rings, _ = CO.level(path, z0, spec)
        for r_ in rings:
            kit.add(f"CORNICE-{tag}-{r_['name']}", r_["role"], r_["solid"], P=print_flip() if r_["flip"] else None,
                    group="cornice")
    fnd = foundation([MAIN_LO], 0.0, ZF, style="vjoint") + box([LX0 - 0.1, 0.0, 0.0], [LX1 + 0.1, LD + 0.5, ZF])
    kit.add("FOUNDATION", "Limestone", fnd, group="foundation")
    inserts = []
    for o in OPENINGS:
        A = o.local_frame()
        sp = o.spec
        b = sp["cut"].bounds()
        key = "DOOR" if o.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, "Windows_Doors", "Door" if o.kind == "door" else "Windows_Doors", "Glass")
        inserts.append(kit.add(f"{key}-{o.name}", "Windows_Doors", world, P=P,
                               key=f"{key}-{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}", group="inserts", render=zones))
    As = np.array([[1.0, 0, 0, LX0 + 1.2], [0, 0, -1.0, 3.0], [0, 1.0, 0, ZF]])
    kit.add("LOGGIA", "Ivory", loggia_screen().transform(As), P=inv34(As), group="walls")
    print("walls + inserts", round(time.time() - t0, 1))

    # --- the roof: a hollow hip with the twin gables, their back ends hipped into it
    roof = rf["body"] + rf["tex"] + rf["skins"] + rf["skin_tex"]
    zr = Z_EAVE + S_MAIN * (D / 2 + D_EAVE)
    caps = [G.ridge_cap((D / 2, D / 2), (W - D / 2, D / 2), zr, S_MAIN, ZW)]
    walls_env = union([wl["facade"].place(M.extrude(wl["cs"].offset(0.15), RAKE + 4.2).translate([0, 0, -3.15]))
                       for wl in rf["walls"]])
    fy = gy + D_EAVE - (zg - Z_EAVE) / S_GABLE
    for g in (G1, G2):
        gx = (g[0] + g[1]) / 2
        caps.append(G.ridge_cap((gx, -RAKE), (gx, fy + 0.4), zg, S_GABLE, ZW))
        for xc in (g[0] - D_EAVE, g[1] + D_EAVE):
            caps.append(G.hip_cap((xc, gy + D_EAVE, Z_EAVE), (gx, fy, zg), half=1.6, up=0.9, drop=2.2))
    corners = [(-D_EAVE, -D_EAVE), (W + D_EAVE, -D_EAVE), (W + D_EAVE, D + D_EAVE), (-D_EAVE, D + D_EAVE)]
    ends = [(D / 2, D / 2), (W - D / 2, D / 2), (W - D / 2, D / 2), (D / 2, D / 2)]
    hips = union([G.hip_cap((c[0], c[1], Z_EAVE), (e[0], e[1], zr), half=1.6, up=0.9, drop=2.2) for c, e in zip(corners, ends)])
    roof = roof + ((union(caps) + hips) - walls_env)
    roof = roof - lip_keep(MAIN_HI.cs, 3.0, ZW)
    roof = roof.trim_by_plane([0, 0, 1.0], ZW)                # nothing below the wall top (the hip caps' drops)
    solid_env, _ = R.hip_roof(pieces, Z_EAVE, S_MAIN, D_EAVE, texture=None, zlo=ZW)
    CW, CD = 12.0, 11.0
    cx, cy = 120.0, 96.0
    zroof = Z_EAVE + S_MAIN * min(D + D_EAVE - cy - CD / 2, W + D_EAVE - cx - CW / 2)
    z0 = round((zroof - 3.0) / 0.2) * 0.2
    roof = roof + G.chimney_seat(solid_env, cx, cy, CW / 2, zr + 1.0)
    pocket = box([cx - CW / 2 - 0.4, cy - CD / 2 - 0.4, z0], [cx + CW / 2 + 0.4, cy + CD / 2 + 0.4, zr + 40])
    kit.add("ROOF", "Charcoal", roof - pocket, group="roof")
    ch = TW.chimney("pilastered", w=CW, d=CD, h=round((zr + 16.0 - z0) / 0.2) * 0.2).translate([cx, cy, z0])
    kit.add("CHIMNEY", "Brick", ch, group="roof")
    for k, wl in enumerate(rf["walls"]):
        orn = G.gable_arcade(wl["L"], wl["slope"], D_EAVE, skin=SKIN, band_at=0.52)
        f = wl["facade"]
        A = f.A.copy()
        A[:, 3] = f.world(0.0, 0.0, RAKE)
        ow = orn.transform(A) - (roof - pocket)              # the ornaments' feet stop on the main roof
        kit.add(f"GABLE-{k}", "Ivory", max(ow.decompose(), key=lambda m_: m_.volume()), P=inv34(A), group="roof")
    print("roof", round(time.time() - t0, 1))

    # --- the steps up to the loggia and the back stoop
    Ast = np.array([[1.0, 0, 0, DOOR_X], [0, 0, -1.0, 0.0], [0, 1.0, 0, 0.0]])
    kit.add("STEPS", "Limestone", FT.steps(24.0, ZF - 0.6, 5).transform(Ast), group="porch")
    e, u = MAIN_LO.locate(160.0, D)
    fb = MAIN_LO.facades()[e]
    A = fb.A.copy()
    A[:, 3] = fb.world(u, -ZF, 1.4)
    kit.add("STOOP-back", "Limestone", FT.steps(14.0, ZF - 0.6, 5).transform(A) - fnd, group="porch")
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "magnolia")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:40]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "magnolia.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))

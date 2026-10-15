"""The Brenton: an original HO-scale (1:87.1) Newport Georgian house, house 49 of the fourth
batch (all Colonial).

Two storeys of rusticated boarding (wide pine boards cut and bevelled to pass for dressed
stone, the joints sharp V-grooves) on a base of pillow-dressed granite in tall and short
courses. The front door is Newport's own: a six-panel door under a five-light transom between
two tall scrolled consoles that carry a shell hood (a half-dome carved as a scallop, its ribs
fanning from the wall), with a pineapple standing over its crown. Ground-floor windows of
twelve over twelve in bold bolection mouldings, a pineapple on each keyblock; upstairs nine
over nine under segmental heads with keystones. Between the storeys a frieze of oak garlands
looped between oval cartouches over a course of little pyramids; at the eave Newport sloops
under sail over a rolling wave, dentils, beaked modillions and a cyma. The roof is a gambrel
on all four sides (a double hip): steep lower slopes of shingles with scooped corners and
hipped dormers flanked by consoles, a railed walk round the break (a chain of interlaced
rings between ball-topped posts), and a low upper hip of flat-seam tin with two tall stacks in
header bond, a sunk cross in each face.

usage: python3 -m hoarch.buildings.brenton [check] [export]
"""
import os
import sys
import time

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import box, offset, poly, rect, slab, union
from hoarch import colonial4 as C4, cornice as CO, features as FT, gables as G, openings as O, roof as R
from hoarch.kit import Kit
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, stacked_shells

NAME = "The Brenton"
COLORS = {"Stone": "#C9BFA8", "White": "#F2EFE7", "Green": "#2F4F3E", "Cedar": "#5C5249", "Tin": "#6B7176",
          "Granite": "#A38476", "Brick": "#8A4A36", "Windows_Doors": "#F2EFE7"}
RENDER_MAT = {"Stone": "siding", "White": "trim", "Green": "accent", "Cedar": "roof", "Tin": "tin", "Granite": "stone",
              "Brick": "brick", "Windows_Doors": "trim", "Door": "door", "Glass": "glass"}

# ------------------------------------------------------------------ cornices (unique to the Brenton)
LEDGE = 1.4
JOINT = dict(pitch=20.0, margin=4.0, layers=[
    dict(kind="frieze", h=4.6, b=1.2, orn="oakgarland", role="White"),
    dict(kind="course", h=1.4, b=1.4, orn="pyramids", role="Green"),
    dict(kind="crown", h=2.2, b=1.4, P=3.4, orn="torus", role="White")])
EAVE = dict(pitch=18.0, margin=4.0, layers=[
    dict(kind="frieze", h=5.4, b=1.2, orn="sloops", role="White"),
    dict(kind="course", h=1.6, b=1.4, orn="dentil", role="Green", tooth=0.8, gap=0.6),
    dict(kind="bed", h=2.2, b=1.4, P=5.8, role="White", brackets=dict(style="beak", t=1.4, reach=0.3)),
    dict(kind="crown", h=2.8, b=1.4, P=6.6, orn="cyma", role="White")])
RJ = round((LEDGE + 0.4 + CO.band_height(JOINT)) / 0.2) * 0.2
HE = CO.band_height(EAVE)

# ------------------------------------------------------------------ levels, plan and the gambrel
ZF = 10.0
S1 = ZF + 40.0
ZU = S1 + RJ
ZE = ZU + 36.0
ZW = round((ZE + HE) / 0.2) * 0.2
FASCIA = 1.4
Z_EAVE = ZW + FASCIA
D_EAVE = 6.0
S_LO, H_LO = 2.0, 26.0                          # the steep lower slopes
Z_BRK = Z_EAVE + H_LO                           # the break
BRK_IN = H_LO / S_LO - D_EAVE                   # the break line, this far inside the wall line
WALK = 4.0
UP_IN = BRK_IN + WALK                           # the upper hip's eaves
Z_WALK = Z_BRK + 1.8                            # the walk's floor
S_UP = 0.45
W, D = 176.0, 116.0
XC, YC = W / 2, D / 2
MAIN = Block("main", [(0, 0), (W, 0), (W, D), (0, D)], ZF, ZW)
BLOCKS = [MAIN]
V1 = 7.0
V2 = ZU - ZF + 5.0
DF = 3.5                                        # the dormer faces stand this far out from the wall line


def _skin(f, b, reg):
    reg = reg - rect(-1, ZE - LEDGE - 0.6 - b.z0, f.L + 1, 999)
    return C4.ashlar_boards(reg, datum=0.0)


def _openings():
    L = []

    def add(x, y, v0, sp, name, kind="window"):
        e, u = MAIN.locate(x, y)
        L.append(Opening(MAIN, e, u, v0, sp, name, kind))

    lo = C4.window_bolection(10.0, 24.0)
    up = C4.window_archtop(10.0, 21.0)
    for x in (22.0, 56.0, W - 56.0, W - 22.0):
        add(x, 0.0, V1, lo, f"S{x:.0f}-1")
        add(x, D, V1, lo, f"N{x:.0f}-1")
    for x in (22.0, 56.0, XC, W - 56.0, W - 22.0):
        add(x, 0.0, V2, up, f"S{x:.0f}-2")
        add(x, D, V2, up, f"N{x:.0f}-2")
    add(XC, 0.0, 0.4, C4.door_shellhood(12.0, 22.0), "front-door", "door")
    add(XC, D, 0.4, C4.door_shellhood(11.0, 21.0, back=True), "back-door", "door")
    for x_, tag in ((0.0, "W"), (W, "E")):
        for y in (32.0, D - 32.0):
            add(x_, y, V1, lo, f"{tag}{y:.0f}-1")
            add(x_, y, V2, up, f"{tag}{y:.0f}-2")
    return L


OPENINGS = _openings()


def _frame(u, v, w, o):
    """A 3x4 placement with local axes u, v, w (as columns) at origin o."""
    return np.column_stack([u, v, w, o]).astype(float)


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    base = MAIN.cs
    undress = [slab(offset(base, 8.0), ZE - LEDGE - 0.6, ZW + 0.01)]
    clear = [lip_keep(base, 3.0, ZF, 1.2)]
    st = stacked_shells(BLOCKS, OPENINGS, [S1], t=3.0, corners="none", siding=_skin, gables=[], clear=clear,
                        prof=CO.joint_profile(RJ, LEDGE), belt_blocks=None, water_table=False, undress=undress,
                        partitions=[((XC - 24.0, 3.0), (XC - 24.0, D - 3.0), 2.0, ZF, ZW),
                                    ((XC + 24.0, 3.0), (XC + 24.0, D - 3.0), 2.0, ZF, ZW)])
    kit.add("WALLS-1", "Stone", st["shells"][0], group="walls")
    kit.add("JOINT", "Stone", st["rings"][0], group="walls")
    lip = _corbel(base, 3.0, ZW) + lip_ring(base, 3.0, ZW)
    kit.add("WALLS-2", "Stone", st["shells"][1] + lip + CO.ledge(MAIN.pts, ZE, LEDGE), group="walls")
    rings, _ = CO.level(st["outlines"][0], S1 + LEDGE + 0.4, JOINT)
    CO.add_level(kit, rings, "CORNICE-J", "cornice")
    rings, _ = CO.level(MAIN.pts, ZE, EAVE)
    CO.add_level(kit, rings, "CORNICE-E", "cornice")
    fnd = foundation(BLOCKS, 0.0, ZF, style="pillowed")
    kit.add("FOUNDATION", "Granite", fnd, group="foundation")
    ins_keep = []
    for o in OPENINGS:
        A = o.local_frame()
        sp = o.spec
        b = sp["cut"].bounds()
        key = "DOOR" if o.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, "Windows_Doors", "Door" if o.kind == "door" else "Windows_Doors", "Glass")
        part = kit.add(f"{key}-{o.name}", "Windows_Doors", world, P=P,
                       key=f"{key}-{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}-{o.v0 > 20}", group="inserts", render=zones)
        ins_keep.append(part.solid)
    print("walls + cornices + inserts", round(time.time() - t0, 1))

    # --- the lower roof: the steep slopes of the gambrel, hollow, open at the break, with a
    # locating lip round its top for the walk
    pieces = [(MAIN.pts, [0, 1, 2, 3], S_LO)]
    rf = G.gabled_roof(pieces, Z_EAVE, D_EAVE, [], texture="scoop", tex_kw=dict(pitch=1.7, wtab=2.4, d=0.4),
                       inner_cs=offset(base, -3.0), fascia=FASCIA, hollow=2.6)
    roof = rf["body"] + rf["tex"]
    corners = [(-D_EAVE, -D_EAVE), (W + D_EAVE, -D_EAVE), (W + D_EAVE, D + D_EAVE), (-D_EAVE, D + D_EAVE)]
    ends = [(BRK_IN, BRK_IN), (W - BRK_IN, BRK_IN), (W - BRK_IN, D - BRK_IN), (BRK_IN, D - BRK_IN)]
    roof = roof + union([G.hip_cap((c[0], c[1], Z_EAVE), (e[0], e[1], Z_BRK + 2.0), half=1.2, up=0.6, drop=1.6)
                         for c, e in zip(corners, ends)])
    roof = roof.trim_by_plane([0, 0, -1.0], -Z_BRK).trim_by_plane([0, 0, 1.0], Z_EAVE - FASCIA)
    roof = roof - lip_keep(base, 3.0, ZW)
    brk = rect(BRK_IN, BRK_IN, W - BRK_IN, D - BRK_IN)
    roof = roof + slab(offset(brk, -1.4) - offset(brk, -2.4), Z_BRK - 0.01, Z_BRK + 1.0)
    solid_env, _ = R.hip_roof(pieces, Z_EAVE, S_LO, D_EAVE, texture=None, zlo=ZW)
    # hipped dormers flanked by consoles: three front and back, one in each end
    DW, DDEP, DHW = 16.0, 14.0, 12.6
    zdf = round((Z_EAVE + S_LO * (D_EAVE - DF) - 0.8) / 0.2) * 0.2
    dbody, dcore, dface = C4.dormer_volute(DW, DDEP, DHW)
    droof = C4.dormer_volute_roof(DW, DDEP, DHW)
    up_ = (0.0, 0.0, 1.0)
    dA = [_frame((1, 0, 0), up_, (0, -1, 0), (x, -DF, zdf)) for x in (XC - 46.0, XC, XC + 46.0)]
    dA += [_frame((-1, 0, 0), up_, (0, 1, 0), (x, D + DF, zdf)) for x in (XC + 46.0, XC, XC - 46.0)]
    dA += [_frame((0, 1, 0), up_, (1, 0, 0), (W + DF, YC, zdf)), _frame((0, -1, 0), up_, (-1, 0, 0), (-DF, YC, zdf))]
    for Ad in dA:
        dkeep = C4.ext(dface.offset(0.3, C4.JoinType.Miter, 4.0), -DDEP - 0.3, 0.3).transform(Ad)
        dpocket = dkeep ^ box([-500, -500, zdf], [500, 500, 999])
        seat = box([-DW / 2 - 1.3, ZW - zdf, -DDEP - 1.3], [DW / 2 + 1.3, 0.0, 1.6]).transform(Ad) ^ solid_env
        roof = roof - dpocket + (seat - dpocket - lip_keep(base, 3.0, ZW))
    kit.add("ROOF-lower", "Cedar", roof, group="roof")
    for k, Ad in enumerate(dA):
        kit.add(f"DORMER-{k}", "White", dbody.transform(Ad), key="DORMER", group="roof")
        kit.add(f"DORMER-core-{k}", "Cedar", dcore.transform(Ad), key="DORMER-core", group="roof")
        dr = droof.transform(Ad) - solid_env - dbody.transform(Ad) - roof
        kit.add(f"DORMER-roof-{k}", "Cedar", max(dr.decompose(), key=lambda m_: m_.volume()), key="DORMER-roof", group="roof")
    print("lower roof + dormers", round(time.time() - t0, 1))

    # --- the upper part: the walk's floor over the break (a bevelled curb at its edge, a groove
    # under it for the lip), the railing round it and the low hip of flat-seam tin, one piece
    deck = slab(brk, Z_BRK, Z_WALK)
    for k in range(4):
        deck = deck + slab(offset(brk, 0.2 * (k + 1)), Z_BRK + 0.2 * k, Z_BRK + 0.2 * (k + 1) + 0.01)
    deck = deck + slab(offset(brk, 0.8), Z_BRK + 0.8, Z_WALK)
    deck = deck - slab(offset(brk, -1.25) - offset(brk, -2.55), Z_BRK - 1.0, Z_BRK + 1.2)
    ups = [(UP_IN, UP_IN), (W - UP_IN, UP_IN), (W - UP_IN, D - UP_IN), (UP_IN, D - UP_IN)]
    hip, hip_tex = R.hip_roof([(ups, [0, 1, 2, 3])], Z_WALK, S_UP, 0.0, texture="flatseam",
                              tex_kw=dict(pitch=2.6, seam_pitch=3.8, seam_w=0.45, d=0.3), zlo=Z_WALK - 0.5)
    zr = Z_WALK + S_UP * (D / 2 - UP_IN)
    xr = UP_IN + (D / 2 - UP_IN)
    caps = G.ridge_cap((xr, YC), (W - xr, YC), zr, S_UP, Z_WALK, half=1.3, up=0.7)
    caps = caps + union([G.hip_cap((c[0], c[1], Z_WALK), (e[0], YC, zr), half=1.1, up=0.6, drop=1.4)
                         for c, e in zip(ups, [(xr, 0), (W - xr, 0), (W - xr, 0), (xr, 0)])])
    upper = deck + hip + hip_tex + caps.trim_by_plane([0, 0, 1.0], Z_WALK)
    x0, y0 = BRK_IN + 0.1, BRK_IN + 0.1
    x1, y1 = W - x0, D - y0
    zc = Z_WALK - 0.01
    rails = [C4.walk_rings(x1 - x0).transform(_frame((1, 0, 0), up_, (0, -1, 0), (x0, y0 + 0.8, zc))),
             C4.walk_rings(y1 - y0).transform(_frame((0, 1, 0), up_, (1, 0, 0), (x1 - 0.8, y0, zc))),
             C4.walk_rings(x1 - x0).transform(_frame((-1, 0, 0), up_, (0, 1, 0), (x1, y1 - 0.8, zc))),
             C4.walk_rings(y1 - y0).transform(_frame((0, -1, 0), up_, (-1, 0, 0), (x0 + 0.8, y1, zc)))]
    upper = upper + union(rails)
    # the two stacks, each in a pocket in the solid hip, the sunk crosses to the street
    pockets, stacks = [], []
    CW, CD = 14.0, 10.0
    for cx in (60.0, W - 60.0):
        z0 = round((zr - 7.0) / 0.2) * 0.2
        pockets.append(box([cx - CW / 2 - 0.4, YC - CD / 2 - 0.4, z0], [cx + CW / 2 + 0.4, YC + CD / 2 + 0.4, zr + 60]))
        stacks.append(C4.chimney_crossed(CD, CW, zr + 18.0 - z0).rotate([0, 0, 90]).translate([cx, YC, z0]))
    upper = upper - union(pockets)
    kit.add("ROOF-upper", "Tin", upper, group="roof")
    for k, s_ in enumerate(stacks):
        kit.add(f"CHIMNEY-{k}", "Brick", s_, key="CHIMNEY", group="roof")
    print("walk + upper roof", round(time.time() - t0, 1))

    # --- steps at the front door and the back door
    for (x, y), wd, n in (((XC, 0.0), 22.0, 4), ((XC, D), 16.0, 4)):
        e, u = MAIN.locate(x, y)
        f = MAIN.facades()[e]
        A = f.A.copy()
        A[:, 3] = f.world(u, -ZF, 1.4)
        kit.add(f"STOOP-{e}", "Granite", FT.steps(wd, ZF - 0.6, n).transform(A) - fnd, group="steps")
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "brenton")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:80]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "brenton.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))

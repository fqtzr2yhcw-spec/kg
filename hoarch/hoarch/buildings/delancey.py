"""The Delancey -- an original HO-scale (1:87.1) San Francisco Italianate row house.

Narrow and tall on a rusticated raised basement: a two-storey slanted bay with colonettes
on its corners, channel-rusticated wood on the front and drop siding on the sides, a panelled
belt, a heavy two-layer cornice on pendant brackets with a flat roof, a front parapet with a
segmental pediment and cartouche, San Francisco window surrounds (colonnettes, arched
architraves, keystones; two-over-one sash), glazed double doors under an arched cornice at
the top of a tall stoop, and slim hooded chimneys.

usage: python3 -m hoarch.buildings.delancey [check] [export]
"""
import math
import os
import sys
import time

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import arch_cs, box, brick, clapboard, cs_union, inv34, offset, poly, rect, slab, union
from hoarch import features as FT, moulding as MD, openings as O, roof as R, skins as SK, trimwork as TW
from hoarch.kit import Kit, print_flip
from hoarch.ornament import chamfer_box, ext, lozenge
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, stacked_shells

NAME = "Delancey San Francisco Italianate"
COLORS = {"Mist": "#8FA3A8", "Cream": "#EDE3C8", "Granite": "#7E7C78", "Brick": "#8A3B2B", "Slate": "#43474D",
          "Windows_Doors": "#EDE3C8"}
RENDER_MAT = {"Mist": "siding", "Cream": "trim", "Granite": "stone", "Brick": "brick", "Slate": "roof",
              "Windows_Doors": "trim", "Sash": "sash", "Door": "door", "Glass": "glass"}
PALETTE = {"siding": ["#8FA3A8", 0.6, 0.0], "trim": ["#EDE3C8", 0.55, 0.0], "stone": ["#7E7C78", 0.9, 0.0],
           "brick": ["#8A3B2B", 0.85, 0.0], "roof": ["#43474D", 0.8, 0.0], "sash": ["#5A1A24", 0.45, 0.0],
           "door": ["#5A1A24", 0.45, 0.0]}

# ------------------------------------------------------------------ levels
ZF = 22.0                 # raised basement
S1 = ZF + 40.0
RH = 4.4
ZE = S1 + RH + 36.0
FR_H = 5.6
EAVE = R.EAVE_DEEP
V1, V2 = 6.0, S1 + RH + 3.0 - ZF

# ------------------------------------------------------------------ plan
X1, Y1 = 72.0, 110.0
MAIN = Block("main", [(0, 0), (X1, 0), (X1, Y1), (0, Y1)], ZF, ZE)
BD, BX0, BW = 9.0, 4.0, 22.0          # bay depth, left end on the wall, front face width
BAY = Block("bay", [(BX0, 3.0), (BX0, 0.0), (BX0 + BD, -BD), (BX0 + BD + BW, -BD), (BX0 + 2 * BD + BW, 0.0),
                    (BX0 + 2 * BD + BW, 3.0)], ZF, ZE)
BLOCKS = [MAIN, BAY]
DOOR_X = 58.0
BRK = dict(pitch=8.6, margin=3.6, pair=1.9, t=0.8)


def _siding(f, b, reg):
    """Channel rustication (wood cut to look like stone blocks) on the street front and bay,
    drop siding on the sides and back."""
    if f.n[1] < -0.3:
        return brick(reg, bl=4.8, bh=1.6, mortar=0.5, d=0.3, datum=1.8, bed=0.4)
    return SK.drop_siding(reg, datum=1.8)


def _openings():
    L = []
    bay1 = O.window_sf(8.8, 26.0, rise=2.4)
    bay2 = O.window_sf(8.4, 24.0, rise=2.2)
    cant1 = O.window_sf(5.2, 26.0, rise=1.8, A=1.0, col=1.0, lites=(1, 1))
    cant2 = O.window_sf(5.2, 24.0, rise=1.6, A=1.0, col=1.0, lites=(1, 1))
    side1 = O.window_sf(8.4, 24.0, rise=2.2)
    side2 = O.window_sf(8.0, 22.0, rise=2.2)
    up_door = O.window_sf(9.0, 24.0, rise=2.4)
    front = O.door_sf(11.6, 25.2)

    def add(block, x, y, v0, sp, name, kind="window"):
        e, u = block.locate(x, y)
        L.append(Opening(block, e, u, v0, sp, name, kind))

    Q = BAY.pts
    cx = BX0 + BD + BW / 2
    add(BAY, cx, -BD, V1, bay1, "bayF-1")
    add(BAY, cx, -BD, V2, bay2, "bayF-2")
    for sg, (x, y) in ((-1, (BX0 + BD / 2, -BD / 2)), (1, (BX0 + 1.5 * BD + BW, -BD / 2))):
        add(BAY, x, y, V1, cant1, f"bay{'LR'[sg > 0]}-1")
        add(BAY, x, y, V2, cant2, f"bay{'LR'[sg > 0]}-2")
    add(MAIN, DOOR_X, 0, 0.4, front, "front-door", "door")
    add(MAIN, DOOR_X, 0, V2, up_door, "S58-2")
    for y in (26.0, 56.0, 86.0):
        add(MAIN, X1, y, V1, side1, f"E{y:.0f}-1")
        add(MAIN, X1, y, V2, side2, f"E{y:.0f}-2")
    for x in (18.0, 54.0):
        add(MAIN, x, Y1, V1, side1, f"N{x:.0f}-1")
        add(MAIN, x, Y1, V2, side2, f"N{x:.0f}-2")
    return L


OPENINGS = _openings()


def _colonettes(z0, z1, r=0.8):
    """Turned colonettes standing on the bay's corners: a square plinth, a slim tapering shaft,
    a 45 degree bell capital and an abacus, half set into the corner."""
    out = []
    Q = [np.array(p) for p in BAY.pts]
    for k in (2, 3):                            # the bay's two outer corners
        p, a, b = Q[k], Q[k - 1], Q[k + 1]
        bis = ((p - a) / np.linalg.norm(p - a) - (b - p) / np.linalg.norm(b - p))
        bis = bis / np.linalg.norm(bis)
        c = p + bis * r * 0.45
        h = z1 - z0
        parts = [M.cylinder(1.6, r + 0.5, r + 0.5, 24).translate([c[0], c[1], z0]),
                 M.cylinder(0.4, r + 0.5, r + 0.1, 24).translate([c[0], c[1], z0 + 1.6]),
                 M.cylinder(h - 4.0, r, r * 0.82, 24).translate([c[0], c[1], z0 + 2.0]),
                 M.cylinder(0.6, r * 0.82, r * 0.82 + 0.6, 24).translate([c[0], c[1], z1 - 2.0]),
                 box([c[0] - r - 0.6, c[1] - r - 0.6, z1 - 1.4], [c[0] + r + 0.6, c[1] + r + 0.6, z1])]
        out.append(union(parts))
    return union(out)


def _parapet(zb):
    """Front parapet (a false front) standing on the cornice deck along the street wall:
    panelled, with end blocks and a raised segmental pediment holding a cartouche.
    Built lying on its back (print face-up); returns (solid, frame)."""
    L, H = X1, 7.2
    parts = [ext(rect(0, 0, L, H), -2.4, 0.0)]
    parts.append(MD.run(-0.4, L + 0.4, H + 1.0, MD.CROWN, 1.0, up=False))             # coping
    for u0, u1 in ((0, 3.2), (L - 3.2, L)):
        parts.append(chamfer_box(u0, 0.0, u1, H, 0.0, 1.0, c=0.3))
    for u0, u1 in ((4.4, 24.0), (L - 24.0, L - 4.4)):
        parts.append(chamfer_box(u0, 1.2, u1, H - 1.2, 0.0, 0.6, c=0.3))        # face on the layer grid (prints on its back)
        parts.append(lozenge((u0 + u1) / 2, H / 2, 2.4, 3.2, 0.5, 0.3))
    # the pediment: a raised segmental head over the middle with a cartouche
    mid = L / 2
    seg = arch_cs(mid - 11.0, mid + 11.0, H - 0.01, H, rise=4.6, seg=48)
    parts.append(ext(seg, -2.4, 0.0))
    parts.append(MD.band(seg, 1.2, MD.CROWN, clip=rect(mid - 13, H, mid + 13, H + 10)))
    parts.append(MD.cartouche((mid, H - 0.4), 6.0, 5.0, 0.0, 1.2))
    f = np.array([[1.0, 0, 0, 0], [0, 0, -1.0, 2.4], [0, 1.0, 0, zb]])       # (u, v, w) -> (x, 2.4 - w, zb + v)
    return union(parts), f


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    base = cs_union([b.cs for b in BLOCKS])
    clear = [lip_keep(base, 3.0, ZF, 1.2)]
    bprof, bblocks = TW.BELTS["panel"]
    st = stacked_shells(BLOCKS, OPENINGS, [S1], t=3.0, corners="board", clear=clear, siding=_siding, prof=bprof,
                        belt_blocks=bblocks)
    kit.add("WALLS-1", "Mist", st["shells"][0] + _colonettes(ZF, S1), group="walls")
    kit.add("BELT", "Cream", st["rings"][0], group="walls")
    kit.add("WALLS-2", "Mist", st["shells"][1] + _colonettes(S1 + RH, ZE) + _corbel(base, 3.0, ZE)
            + lip_ring(base, 3.0, ZE), group="walls")
    # raised basement: tall coursed-stone foundation with two small windows
    fnd = foundation(BLOCKS, 0.0, ZF, style="rusticated")
    bwin = O.window_insert(7.0, 7.0, rise=0, lites=(2, 1), bare=True)
    bops = []
    for (x, y, blk) in ((BX0 + BD + BW / 2, -BD, BAY), (X1, 40.0, MAIN), (X1, 80.0, MAIN)):
        e, u = blk.locate(x, y)
        f = blk.facades()[e]
        A = f.A.copy()
        A[:, 3] = f.world(u, -ZF + 8.0, 0.0)
        cut = f.place(box([u - 3.5, -ZF + 8.0, -4.0], [u + 3.5, -ZF + 15.0, 2.0]))
        fnd = fnd - cut
        bops.append((f, A, x, y))
    kit.add("FOUNDATION", "Granite", fnd, group="foundation")
    for k, (f, A, x, y) in enumerate(bops):
        B = A.copy()
        B[:, 3] = A[:, 3] + A[:, 2] * (-3.0 + O.PLUG)                     # plug set in the 3.0 stone wall
        win = bwin["insert"].transform(B)
        kit.add(f"WIN-basement-{k}", "Windows_Doors", win, P=inv34(B), key="WIN-basement", group="inserts",
                render=[("Sash", win)])
    inserts = []
    for o in OPENINGS:
        A = o.local_frame()
        sp = o.spec
        b = sp["cut"].bounds()
        tag = f"{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}"
        key = "DOOR" if o.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, "Cream", "Door" if o.kind == "door" else "Sash", "Glass")
        inserts.append(kit.add(f"{key}-{o.name}", "Windows_Doors", world, P=P, key=f"{key}-{tag}-{o.v0 > 20}",
                               group="inserts", render=zones))
    print("walls + inserts", round(time.time() - t0, 1))

    # --- two-layer cornice round the house; the upper layer carries the flat roof deck
    outline = max(base.to_polygons(), key=lambda L: abs(poly(L).area()))
    outline = [tuple(p) for p in outline]
    kit.add("EAVE-frieze", "Cream", R.frieze_ring(outline, ZE, h=FR_H, brackets=BRK), group="roof")
    zc = ZE + FR_H
    chims = [(8.0, 46.0), (8.0, 86.0)]
    eave = R.bracketed_cornice(outline, zc, EAVE, brackets=dict(z_top=5.2, h=5.0, d0=0.9, d=5.6, style="pendant", **BRK),
                               dents=dict(z=4.4, h=0.8, d0=0.9, d=0.7), deck=(6.4, 7.6))
    zdeck = zc + EAVE[-1][1]
    pockets = union([box([x - 5.7, y - 5.7, zdeck - 0.6], [x + 5.7, y + 5.7, zdeck + 1]) for x, y in chims])
    kit.add("EAVE-cornice-roof", "Cream", eave - pockets, P=print_flip(), group="roof")
    for k, (x, y) in enumerate(chims):
        ch = TW.chimney("slim", w=10.5, d=10.5, h=14.6).translate([x, y, zdeck - 0.6])
        kit.add(f"CHIMNEY-{k}", "Brick", ch, key="CHIMNEY", group="roof")
    par, fpar = _parapet(zdeck)
    kit.add("PARAPET", "Cream", par.transform(fpar), P=inv34(fpar), group="roof")        # prints on its back
    print("roof", round(time.time() - t0, 1))

    # --- the stoop: a tall flight of steps up to the door, with solid cheek walls
    e, u = MAIN.locate(DOOR_X, 0.0)
    f = MAIN.facades()[e]
    A = f.A.copy()
    A[:, 3] = f.world(u, -ZF, 0.0)
    stoop = FT.steps(15.0, ZF + 0.2, 9, tread=2.6, cheek=2.0).transform(A)
    walls1 = next(p.solid for p in kit.parts if p.name == "WALLS-1")
    door = next(p.solid for p in kit.parts if p.name == "DOOR-front-door")
    kit.add("STOOP", "Cream", stoop - fnd - walls1 - door, group="stoop")        # fitted round the stone base
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "delancey")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:40]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "delancey.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))

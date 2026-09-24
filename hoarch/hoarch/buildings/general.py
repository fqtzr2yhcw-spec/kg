"""Hartley's General Store -- an original HO-scale (1:87.1) two-storey false-front store, 1879.

A wooden Main Street store in vertical lapped boards on stone piers with board skirting. A
two-storey gallery runs across the front: square posts with pierced gussets on a flagstone
sidewalk carry a planked balcony, whose own posts, picket railing and a corrugated-iron shed
roof shelter the upstairs windows and balcony door. The storefront has chamfered wooden
pilasters, beaded-board bulkheads, small-paned display windows and a recessed pair of
glazed doors. Above the gallery, the false front carries the sign board, a dogtooth frieze
under a straight cornice and an arched centre with the date. Corrugated-iron shed roof and
a hooded brick flue.

Colour comes from the part split (see storefront.py). The sign and the arch board each take
one filament change for their letters; the balcony deck prints planks-first (one change).

usage: python3 -m hoarch.buildings.general [check] [export]
"""
import math
import os
import sys
import time

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import arch_cs, box, cs_union, inv34, poly, rect, union
from hoarch import features as FT, openings as O, skins as SK, storefront as SF, trimwork as TW
from hoarch.kit import Kit, print_flip
from hoarch.ornament import ext
from hoarch.shell import Block, Opening, foundation, stacked_shells

NAME = "Hartley's General Store"
COLORS = {"Ochre": "#C8A55A", "Cream": "#EDE4CC", "Green": "#2E4A33", "Roof": "#6E6E6A", "Stone": "#8A857C",
          "Planks": "#6F5034", "Deck": "#EDE4CC", "Sign": "#2E4A33", "Arch": "#EDE4CC", "Brick": "#8A3F2C",
          "Windows_Doors": "#EDE4CC"}
RENDER_MAT = {"Ochre": "siding", "Cream": "trim", "Green": "green", "Roof": "roof", "Stone": "stone", "Planks": "planks",
              "Deck": "trim", "Sign": "green", "Arch": "trim", "Brick": "brick", "Windows_Doors": "trim", "Sash": "sash",
              "Door": "door", "Glass": "glass"}

# ------------------------------------------------------------------ levels (v from the block base)
ZF = 3.6                  # stone piers; the flagstone sidewalk is level with the floor
H1 = 32.0
S1 = ZF + H1
RH = 4.4
Z_DECK = S1 + RH          # the balcony is level with the upper floor
Z_TOP = Z_DECK + 22.0     # upper gallery beam
Z_GR = ZF + 62.6          # the gallery roof meets the wall here
HB = 68.0                 # block height at the front (the shed roof falls to the rear)
SIGN_V, SIGN_H = 65.6, 7.2
FR_V, FR_H = 73.6, 2.8
CAP_V = FR_V + FR_H
CAP_PROF = [(0.0, 0.0), (1.0, 0.0), (1.0, 0.6), (1.4, 0.6), (1.4, 1.2), (2.6, 1.2), (2.6, 2.4), (3.0, 2.8), (3.0, 3.2),
            (0.0, 3.2)]
FF_V = CAP_V + 3.2        # false-front top
ARCH = (10.0, 34.0, 6.0)  # arched centre: u0, u1, rise
T = 3.0

# ------------------------------------------------------------------ plan
W, D = 44.0, 58.0
MAIN = Block("main", [(0, 0), (W, 0), (W, D), (0, D)], ZF, ZF + HB)
BLOCKS = [MAIN]
S_ROOF = 4.0 / (D - T)    # shed roof slope, front to back
GAL_Y = -12.75            # gallery post line
POSTS_X = (-1.0, 10.5, 22.0, 33.5, 45.0)


def _siding(f, b, reg):
    return SK.vertical_lap(reg, pitch=2.0, d=0.45, d0=0.1, datum=0.0)


def _openings():
    L = []

    def add(x, y, v0, sp, name, kind="window"):
        e, u = MAIN.locate(x, y)
        L.append(Opening(MAIN, e, u, v0, sp, name, kind))

    sf = SF.storefront(34.0, 28.0, entry=8.0, col=2.2, style="chamfered", bulk=6.0, transom=4.0, beam=1.6, lite=3.0,
                       bulk_style="boards", mullion=False, posts=True, t=T, grid=(3, 3))
    add(W / 2, 0, 0.0, sf, "storefront", "door")
    up = SF.window_commercial(8.0, 16.0, rise=1.4, lites=(3, 3), rows=(2, 2), sill=1.0)
    v_up = Z_DECK - ZF
    for x in (10.0, 34.0):
        add(x, 0, v_up + 4.0, up, f"F{x:.0f}-2")
    add(W / 2, 0, v_up, SF.door_commercial(7.0, 20.0, transom=3.2, leaf="six_light",
                                           tstyle="cross", head=None), "balcony-door", "door")
    side = SF.window_commercial(8.0, 16.0, rise=1.4, lites=(2, 2), rows=(2, 2), sill=1.0)
    for y in (20.0, 40.0):
        add(W, y, 9.0, side, f"E{y:.0f}-1")
        add(W, y, v_up + 4.0, side, f"E{y:.0f}-2")
    add(0, 30.0, v_up + 4.0, side, "W30-2")
    add(W - 12.0, D, 0.0, SF.door_commercial(9.0, 24.0, transom=3.0, leaf="six_light", tstyle="cross", head=None),
        "back-door", "door")
    add(W - 32.0, D, 9.0, side, "N12-1")
    add(W - 22.0, D, v_up + 4.0, side, "N22-2")
    return L


OPENINGS = _openings()
APPLIED = [("SIGN", 2.0, SIGN_V, W - 4.0, SIGN_H),
           ("FRIEZE", 0.0, FR_V, W, FR_H),
           ("CORNICE", 0.0, CAP_V, W, 3.2),
           ("GROOF", 0.0, Z_GR - ZF - 1.4, W, 2.8)]


def _applied_openings():
    out = [Opening(MAIN, 0, 0.0, 0.0, SF.applied(rect(u0, v0, u0 + L, v0 + h)), name, "trim")
           for name, u0, v0, L, h in APPLIED]
    a0, a1, rise = ARCH
    out.append(Opening(MAIN, 0, 0.0, 0.0, SF.applied(arch_cs(a0, a1, FF_V - 0.01, FF_V - 0.01, rise=rise, seg=40)),
                       "ARCH", "trim"))
    return out


def _roof_cut():
    """Everything above the shed roof's underside plane (through the side walls' outer top
    edges), behind the false front."""
    sec = poly([(T, ZF + HB), (D + 10.0, ZF + HB - (D + 10.0 - T) * S_ROOF), (D + 10.0, ZF + 300.0), (T, ZF + 300.0)])
    # (y, z) section extruded along x
    m = M.extrude(sec, W + 20.0).transform(np.array([[0.0, 0, 1.0, -10.0], [1.0, 0, 0, 0], [0, 1.0, 0, 0]]))
    return m


def _upper(solid, A, level, lo, hi):
    top = solid ^ box([-1e3, -1e3, level], [1e3, 1e3, 1e3])
    return [(lo, (solid - top).transform(A)), (hi, top.transform(A))]


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    a0, a1, rise = ARCH
    ff = rect(0.0, HB - 0.01, W, FF_V) + arch_cs(a0, a1, FF_V - 0.01, FF_V - 0.01, rise=rise, seg=40)
    bprof, _ = TW.BELTS["fascia"]
    st = stacked_shells(BLOCKS, OPENINGS + _applied_openings(), [S1], t=T, corners="none", siding=_siding, prof=bprof,
                        belt_blocks=None, water_table=False, gables=[(MAIN, 0, ff)])
    sfo = next(o for o in OPENINGS if o.name == "storefront")
    kit.add("WALLS-1", "Ochre", st["shells"][0] + sfo.spec["posts"].transform(sfo.local_frame()), group="walls")
    kit.add("BELT", "Cream", st["rings"][0], group="walls")
    kit.add("WALLS-2", "Ochre", st["shells"][1] - _roof_cut(), group="walls")

    # --- storefront, entry, windows and doors
    sp = sfo.spec
    A = sfo.local_frame()
    world, P, zones = O.place(sp, A, "Green", "Green", "Glass")
    kit.add("STOREFRONT", "Green", world, P=P, group="storefront", render=zones)
    eu, ew, eh = sp["entry"]
    Av = A.copy()
    Av[:, 3] = A[:, 3] + A[:, 0] * eu
    vest = SF.vestibule(ew, 3.0, eh, bulk=6.0, front=-T, doors="glass_pair")
    R_up = np.array([[1.0, 0, 0], [0, 0, -1.0], [0, 1.0, 0]])
    kit.add("VESTIBULE", "Green", vest.transform(Av), P=R_up @ inv34(Av), group="storefront")
    vb = np.array(vest.bounding_box())
    for o in OPENINGS:
        if o.name == "storefront":
            continue
        s = o.spec
        b = s["cut"].bounds()
        key = "DOOR" if o.kind == "door" else "WIN"
        world, P, zones = O.place(s, o.local_frame(), "Windows_Doors", "Door" if o.kind == "door" else "Sash", "Glass")
        kit.add(f"{key}-{o.name}", "Windows_Doors", world, P=P, key=f"{key}-{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}",
                group="inserts", render=zones)
    fnd = foundation(BLOCKS, 0.0, ZF, style="piers", lip=1.2)
    pad = box([vb[0] + 0.2, -ZF, vb[2] + 0.2], [vb[3] - 0.2, 0.0, -T]).transform(Av)
    fnd = fnd + pad - box([vb[0] - 0.2, 0.0, vb[2] - 0.2], [vb[3] + 0.2, 2.0, -0.01]).transform(Av)
    kit.add("FOUNDATION", "Stone", fnd, group="foundation")
    print("walls + storefront", round(time.time() - t0, 1))

    # --- the two-storey gallery
    walk = SF.flag_sidewalk(W + 4.0, 12.8, ZF).translate([-2.0, -14.8, 0.0])
    kit.add("SIDEWALK", "Stone", walk, group="gallery")
    deck_d = -GAL_Y + 1.0 - 1.45                                   # from the belt's face out past the posts
    deck = SF.boardwalk(W + 4.0, deck_d, Z_DECK, pitch=2.0, base=1.8, stringers=3)
    Ad = np.array([[-1.0, 0, 0, W + 2.0], [0, -1.0, 0, -1.45], [0, 0, 1.0, 0.0]])
    dk = deck.transform(Ad)
    kit.add("GALLERY-deck", "Deck", dk, P=print_flip(), group="gallery", render=FT.plank_zones(dk, Z_DECK, "Planks", "Deck"))
    z_under = Z_DECK - 1.2 - 1.8
    lower = SF.gallery_frame(POSTS_X, z_under - ZF)
    Ag = np.array([[1.0, 0, 0, 0.0], [0, 0, -1.0, GAL_Y], [0, 1.0, 0, ZF]])       # (u, v, w) -> (x, y = GAL_Y - w, z)
    kit.add("GALLERY-lower", "Cream", lower.transform(Ag), P=R_up @ inv34(Ag), group="gallery")
    upper = SF.gallery_frame(POSTS_X, Z_TOP - Z_DECK, rail=dict(h=7.6, pitch=1.8, picket=0.8))
    Au = Ag.copy()
    Au[:, 3] = [0.0, GAL_Y, Z_DECK]
    kit.add("GALLERY-upper", "Cream", upper.transform(Au), P=R_up @ inv34(Au), group="gallery")
    # end railings from the corner posts back to the wall
    for k, x in enumerate((POSTS_X[0], POSTS_X[-1])):
        yl = GAL_Y + 1.0
        L = -2.0 - yl
        rail = union([box([0.0, 0.0, -0.5], [L, 0.8, 0.5]), box([0.0, 6.6, -0.6], [L, 7.6, 0.6])] +
                     [box([u - 0.4, 0.79, -0.4], [u + 0.4, 6.61, 0.4]) for u in np.arange(1.8, L - 0.9, 1.8)])
        Ae = np.array([[0.0, 0, 1.0, x], [1.0, 0, 0, yl], [0, 1.0, 0, Z_DECK]])      # (u, v, w) -> (x = x + w, y = yl + u, z)
        kit.add(f"GALLERY-rail-{k}", "Cream", rail.transform(Ae), P=R_up @ inv34(Ae), key="GALLERY-rail", group="gallery")
    # corrugated shed roof over the gallery: from the outer beam up to the wall
    s = (Z_GR - Z_TOP) / (-(GAL_Y - 1.0))
    n = math.sqrt(1 + s * s)
    y_eave = GAL_Y - 1.0 - 0.8
    z_eave = Z_TOP - 0.8 * s
    Wv = (-0.15 - y_eave) * n
    pan = SF.corrugated_panel(W + 4.4, Wv, t=1.0, pitch=1.6, h=0.4, chord=1.2)
    Ar = np.array([[1.0, 0.0, 0.0, -2.2], [0.0, 1 / n, -s / n, y_eave], [0.0, s / n, 1 / n, z_eave]])
    kit.add("GALLERY-roof", "Roof", pan.transform(Ar), P=inv34(Ar), group="gallery")
    print("gallery", round(time.time() - t0, 1))

    # --- the false front: sign, dogtooth frieze, cornice, arch board with the date
    f = MAIN.facades()[0]

    def frame_at(u0, v0, w0=0.0):
        A_ = f.A.copy()
        A_[:, 3] = f.world(u0, v0, w0)
        return A_

    sign = SF.sign_band(W - 4.0, SIGN_H, "GENERAL STORE", cap=2.9, font="grotesque", board=1.0, frame=0.8, relief=0.4)
    As = frame_at(2.0, SIGN_V)
    kit.add("SIGN", "Sign", sign.transform(As), P=inv34(As), group="front", render=_upper(sign, As, 1.0, "Green", "Cream"))
    teeth = union([M.hull_points([(u - 0.8, 0.6, 0.79), (u + 0.8, 0.6, 0.79), (u - 0.8, 2.2, 0.79), (u + 0.8, 2.2, 0.79),
                                  (u, 1.4, 1.4)]) for u in np.arange(1.2, W - 0.8, 2.0)])
    fr = box([0, 0, 0], [W, FR_H, 0.8]) + teeth
    Af = frame_at(0.0, FR_V)
    kit.add("FRIEZE", "Green", fr.transform(Af), P=inv34(Af), group="front")
    cap = SF.cornice_cap(W, CAP_PROF)
    Ac = frame_at(0.0, CAP_V)
    kit.add("CORNICE", "Cream", cap.transform(Ac), P=inv34(Ac), group="front")
    seg = arch_cs(a0, a1, FF_V, FF_V, rise=rise, seg=40)
    board = ext(seg, 0.0, 0.8)
    rim = (seg - seg.offset(-1.2)) - rect(-1e3, -1e3, 1e3, FF_V + 0.6)
    rim = ext(rim + (seg ^ rect(-1e3, FF_V - 1, 1e3, FF_V + 0.6)), 0.79, 1.6)
    date = ext(SF.text_cs("1879", 2.4, "serif", grow=0.1).translate(((a0 + a1) / 2, FF_V + 1.2)), 0.79, 1.2)
    arch = (board + rim + date).translate([0, -FF_V, 0])
    Aa = frame_at(0.0, FF_V)
    kit.add("ARCH", "Arch", arch.transform(Aa), P=inv34(Aa), group="front", render=_upper(arch, Aa, 0.8, "Cream", "Green"))
    print("front", round(time.time() - t0, 1))

    # --- the main roof: one corrugated panel on the walls' sloped tops; the flue
    n2 = math.sqrt(1 + S_ROOF ** 2)
    y1 = D + 1.6
    z1 = ZF + HB - (y1 - T) * S_ROOF
    Lr = W + 2.4
    Vr = (y1 - (T + 0.15)) * n2
    main = SF.corrugated_panel(Lr, Vr, t=1.2, pitch=2.0, h=0.4, chord=1.4)
    Am = np.array([[-1.0, 0.0, 0.0, W + 1.2], [0.0, -1 / n2, S_ROOF / n2, y1], [0.0, S_ROOF / n2, 1 / n2, z1]])
    fx, fy, fw = 34.0, D - 14.0, 5.0
    hole = box([fx - fw / 2 - 0.3, fy - fw / 2 - 0.3, ZF + 40], [fx + fw / 2 + 0.3, fy + fw / 2 + 0.3, ZF + 120])
    kit.add("ROOF", "Roof", main.transform(Am) - hole, P=inv34(Am), group="roof")
    zb = ZF + HB - (fy + fw / 2 - T) * S_ROOF - 3.0
    zb = round(zb / 0.2) * 0.2
    flue = TW.chimney("hooded", w=fw, d=fw, h=round((ZF + FF_V + 4.0 - zb) / 0.2) * 0.2).translate([fx, fy, zb])
    kit.add("CHIMNEY", "Brick", flue, group="roof")
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "general")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:40]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "general.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))

"""Keller's Barber Shop -- an original HO-scale (1:87.1) one-storey false-front shop, 1891.

A small wooden Main Street shop on a timber sill: a false front in rustic (half-log) siding
hiding a low gable roof of rolled roofing, beaded corner boards, a storefront with panelled
pilasters, lozenge bulkheads, wide transom lights and a shallow recessed entry with a single
glazed door, a striped awning, a sign board with raised letters, a two-layer top cornice (a
frieze on jigsawn brackets and a cap), a gable-headed date tablet, and a stovepipe. The shop
stands on a plank boardwalk with a barber pole at the curb. Sides and back in vertical
boards; windows with flat iron hoods.

Colour comes from the part split (see storefront.py). The awning prints on its side, so its
stripes are colour bands by height; the sign, tablet and boardwalk each take one filament
change. The barber pole's stripes are raised for a paint-on colour.

usage: python3 -m hoarch.buildings.barber [check] [export]
"""
import math
import os
import sys
import time

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import box, cs_union, inv34, poly, rect, union
from hoarch import features as FT, openings as O, roof as R, skins as SK, storefront as SF, trimwork as TW
from hoarch.kit import Kit, print_flip
from hoarch.ornament import ext
from hoarch.shell import Block, Opening, _corner_board, foundation, wall_shell

NAME = "Keller's Barber Shop"
# the sign, tablet, awning and boardwalk each print on a plate of their own: each takes
# filament changes by height, which would recolour anything else on the plate
COLORS = {"White": "#EEEBE3", "Navy": "#243553", "Red": "#A3262A", "Roof": "#4A4A48", "Timber": "#5B4636",
          "Planks": "#6F5034", "Iron": "#2B2B2B", "Windows_Doors": "#243553", "Sign": "#A3262A", "Tablet": "#EEEBE3",
          "Awning": "#A3262A", "Boardwalk": "#5B4636"}
RENDER_MAT = {"White": "siding", "Navy": "navy", "Red": "red", "Roof": "roof", "Timber": "timber", "Planks": "planks",
              "Iron": "iron", "Windows_Doors": "navy", "Sash": "sash", "Door": "door", "Glass": "glass", "Sign": "red",
              "Tablet": "siding", "Awning": "red", "Boardwalk": "timber"}
STRIPE = 2.2              # awning stripes: 11 layers each

# ------------------------------------------------------------------ levels (v from the block base)
ZF = 4.0                  # timber sill = the boardwalk's top
ZE = ZF + 46.0            # eaves (outer face of the side walls)
S = 0.35                  # roof slope
T = 3.0
SF_W, SF_H = 58.0, 38.0
AW_V = SF_H + 2.0         # awning rail top
SIGN_V, SIGN_H = 43.0, 10.0
FR_V, FR_H = 56.0, 5.6
CAP_V = FR_V + FR_H
CAP_PROF = [(1.3 * a, 1.3 * b) for a, b in
            [(0.0, 0.0), (1.2, 0.0), (1.2, 0.6), (1.6, 0.6), (1.6, 1.4), (3.0, 1.4), (3.0, 2.0), (3.2, 2.2),
             (3.4, 2.6), (3.6, 3.0), (3.6, 3.2), (0.0, 3.2)]]
CAP_H = 1.3 * 3.2
HF = CAP_V + CAP_H        # false-front top

# ------------------------------------------------------------------ plan
W, D = 80.0, 120.0
HB = ZE - ZF + T * S      # block height: the side walls are trimmed to the roof planes
MAIN = Block("main", [(0, 0), (W, 0), (W, D), (0, D)], ZF, ZF + HB)
BLOCKS = [MAIN]
DE = 2.4                  # eave overhang
Y0R = T + 0.15            # the roof starts behind the false front
PIPE = (58.0, D - 30.0, 1.5)


def _siding(f, b, reg):
    if f.n[1] < -0.3:
        return SK.rustic_lap(reg, datum=0.0)
    return SK.beadboard(reg, pitch=2.4, groove=0.5, d=0.4, datum=0.6)


def _openings():
    L = []

    def add(x, y, v0, sp, name, kind="window"):
        e, u = MAIN.locate(x, y)
        L.append(Opening(MAIN, e, u, v0, sp, name, kind))

    sf = SF.storefront(SF_W, SF_H, entry=11.0, col=2.4, style="panel", bulk=8.0, transom=5.6, beam=2.0, lite=5.4,
                       bulk_style="lozenge", mullion=False, posts=True, t=T)
    add(W / 2, 0, 0.0, sf, "storefront", "door")
    win = SF.window_commercial(8.4, 24.0, rise=0, lites=(2, 2), rows=(2, 2), sill=1.0, head="hood", hood_w=1.2)
    for y in (30.0, 60.0, 90.0):
        add(W, y, 12.0, win, f"E{y:.0f}")
    for y in (60.0, 90.0):
        add(0, y, 12.0, win, f"W{y:.0f}")
    for x in (20.0, 42.0):
        add(W - x, D, 12.0, win, f"N{x:.0f}")
    add(W - 64.0, D, 0.0, SF.door_commercial(10.0, 32.0, transom=4.4, leaf="store", tstyle="twin", head=None),
        "back-door", "door")
    return L


OPENINGS = _openings()
AW_L = 25 * STRIPE
AW_U = (W - AW_L) / 2
APPLIED = [("AWNING", AW_U, AW_V - 2.0, AW_L, 2.0),
           ("SIGN", (W - SF_W) / 2, SIGN_V, SF_W, SIGN_H),
           ("FRIEZE", 0.0, FR_V, W, FR_H),
           ("CORNICE", 0.0, CAP_V, W, CAP_H)]


def _applied_openings():
    return [Opening(MAIN, 0, 0.0, 0.0, SF.applied(rect(u0, v0, u0 + L, v0 + h)), name, "trim")
            for name, u0, v0, L, h in APPLIED]


def _roof_cut():
    """Everything above the two roof planes (through the side walls' outer top edges),
    behind the false front."""
    sec = poly([(-10.0, ZE - 10.0 * S), (W / 2, ZE + W / 2 * S), (W + 10.0, ZE - 10.0 * S), (W + 10.0, ZE + 200.0),
                (-10.0, ZE + 200.0)])
    return M.extrude(sec, D + 10.0 - T).rotate([90, 0, 0]).translate([0, D + 10.0, 0])


def _corner_boards():
    """Beaded corner boards: full height on the false front, to the eaves elsewhere."""
    out = []
    facs = MAIN.facades()
    v_eave = ZE - ZF
    for i, f in enumerate(facs):
        for at_start in (True, False):
            qb = FR_V if i == 0 else v_eave
            out.append(f.place(_corner_board("beaded", f.L, at_start, 1.8, qb)))
    for x, y in ((0.0, 0.0), (W, 0.0), (W, D), (0.0, D)):        # fill the square where two boards meet
        sx, sy = (-1 if x == 0 else 1), (-1 if y == 0 else 1)
        qb = FR_V if y == 0 else v_eave
        out.append(box([min(x, x + sx * 0.65), min(y, y + sy * 0.65), ZF + 1.8], [max(x, x + sx * 0.65),
                                                                                 max(y, y + sy * 0.65), ZF + qb]))
    return union(out)


def _stripes(solid, A, L, p):
    """Render zones of the awning: red and white bands across it."""
    out = []
    n = int(round(L / p))
    for k in range(n):
        band = solid ^ box([k * L / n, -50, -50], [(k + 1) * L / n, 50, 50])
        out.append(("Red" if k % 2 == 0 else "White", band.transform(A)))
    return out


def _upper(solid, A, level, lo, hi):
    """Render zones of a face-up part with one filament change at local w = ``level``."""
    top = solid ^ box([-1e3, -1e3, level], [1e3, 1e3, 1e3])
    return [(lo, (solid - top).transform(A)), (hi, top.transform(A))]


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    rear = [(0.0, HB - 0.01), (W, HB - 0.01), (W / 2, HB + W / 2 * S + 1.0)]
    gables = [(MAIN, 0, rect(0.0, HB - 0.01, W, HF)),                         # the false front
              (MAIN, 2, poly(rear))]                                          # the rear gable
    ops = OPENINGS + _applied_openings()
    walls = wall_shell(BLOCKS, ops, t=T, belt=None, corners="none", water_table=False, siding=_siding, gables=gables)
    walls = walls + _corner_boards()
    sfo = next(o for o in OPENINGS if o.name == "storefront")
    walls = walls - _roof_cut() + sfo.spec["posts"].transform(sfo.local_frame())
    kit.add("WALLS", "White", walls, group="walls")

    # --- storefront, entry, windows and doors
    sp = sfo.spec
    A = sfo.local_frame()
    world, P, zones = O.place(sp, A, "Navy", "Navy", "Glass")
    kit.add("STOREFRONT", "Navy", world, P=P, group="storefront", render=zones)
    eu, ew, eh = sp["entry"]
    Av = A.copy()
    Av[:, 3] = A[:, 3] + A[:, 0] * eu
    vest = SF.vestibule(ew, 4.0, eh, bulk=8.0, front=-T, doors="single")
    R_up = np.array([[1.0, 0, 0], [0, 0, -1.0], [0, 1.0, 0]])
    kit.add("VESTIBULE", "Navy", vest.transform(Av), P=R_up @ inv34(Av), group="storefront")
    # the timber sill; a pad under the entry floor, the locating lip cut where the entry is
    vb = np.array(vest.bounding_box())
    fnd = foundation(BLOCKS, 0.0, ZF, style="timber", lip=1.2)
    pad = box([vb[0] + 0.2, -ZF, vb[2] + 0.2], [vb[3] - 0.2, 0.0, -T]).transform(Av)
    fnd = fnd + pad - box([vb[0] - 0.2, 0.0, vb[2] - 0.2], [vb[3] + 0.2, 2.0, -0.01]).transform(Av)
    kit.add("FOUNDATION", "Timber", fnd, group="foundation")
    for o in OPENINGS:
        if o.name == "storefront":
            continue
        s = o.spec
        b = s["cut"].bounds()
        key = "DOOR" if o.kind == "door" else "WIN"
        world, P, zones = O.place(s, o.local_frame(), "Windows_Doors", "Door" if o.kind == "door" else "Sash", "Glass")
        kit.add(f"{key}-{o.name}", "Windows_Doors", world, P=P, key=f"{key}-{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}",
                group="inserts", render=zones)
    print("walls + storefront", round(time.time() - t0, 1))

    # --- the front: awning, sign, frieze on sawn brackets, cornice cap, coping, tablet
    f = MAIN.facades()[0]

    def frame_at(u0, v0, w0=0.0):
        A_ = f.A.copy()
        A_[:, 3] = f.world(u0, v0, w0)
        return A_

    aw = SF.awning(AW_L, depth=14.0, drop=6.6, valance=3.2, point=STRIPE)
    Aa = frame_at(AW_U, AW_V)
    R_side = np.array([[0.0, 1.0, 0.0], [0.0, 0.0, 1.0], [1.0, 0.0, 0.0]])        # (u, v, w) -> (v, w, u): on its side
    kit.add("AWNING", "Awning", aw.transform(Aa), P=R_side @ inv34(Aa), group="front",
            render=_stripes(aw, Aa, AW_L, STRIPE))
    sign = SF.sign_band(SF_W, SIGN_H, "BARBER SHOP", cap=5.0, font="sans", board=1.0, frame=1.0, relief=0.4)
    As = frame_at((W - SF_W) / 2, SIGN_V)
    kit.add("SIGN", "Sign", sign.transform(As), P=inv34(As), group="front", render=_upper(sign, As, 1.0, "Red", "White"))
    tails = [1.2 + (W - 2.4) * k / 6 for k in range(7)]
    fr = SF.frieze_band(W, FR_H, board=1.2, panels=[(a + 1.8, b - 1.8) for a, b in zip(tails, tails[1:])],
                        tails=dict(us=tails, w=1.4, d=3.0, style="sawn"))
    Af = frame_at(0.0, FR_V)
    kit.add("FRIEZE", "Navy", fr.transform(Af), P=inv34(Af), group="front")
    cap = SF.cornice_cap(W, CAP_PROF)
    Ac = frame_at(0.0, CAP_V)
    kit.add("CORNICE", "Red", cap.transform(Ac), P=inv34(Ac), group="front")
    zc = ZF + HF
    cop = box([-0.5, -CAP_PROF[-3][0] - 0.2, zc], [W + 0.5, T + 0.4, zc + 1.0])
    kit.add("COPING", "Navy", cop, group="front")
    tw, th = 20.0, 8.4
    rise = th * 0.35
    outline = poly([(-tw / 2, 0), (tw / 2, 0), (tw / 2, th - rise), (0, th), (-tw / 2, th - rise)])
    tab = SF.name_tablet(tw, th, None, "1891", cap=3.4, head="gable", board=1.2, relief=0.4) + \
        ext(outline + rect(-tw / 2 - 2.4, 0.0, tw / 2 + 2.4, 2.4), -2.4, 0.01)
    At = frame_at(W / 2, HF + 1.0, -1.0)
    kit.add("TABLET", "Tablet", tab.transform(At), P=inv34(At), group="front", render=_upper(tab, At, 1.2, "White", "Navy"))
    print("front", round(time.time() - t0, 1))

    # --- roof: two panels of rolled roofing on the walls' sloped tops, a ridge roll, a stovepipe
    n = math.sqrt(1 + S * S)
    y1 = D + DE
    Lp = y1 - Y0R
    Vp = (W / 2 + DE) * n + 1.0
    pan = R.roll_panel(Lp, Vp, t=1.2, course=6.0)
    AL = np.array([[0.0, 1 / n, -S / n, -DE], [-1.0, 0.0, 0.0, y1], [0.0, S / n, 1 / n, ZE - DE * S]])
    AR = np.array([[0.0, -1 / n, S / n, W + DE], [1.0, 0.0, 0.0, Y0R], [0.0, S / n, 1 / n, ZE - DE * S]])
    px, py, pr = PIPE
    # the stovepipe stands in a snug socket through a flashing boot on the roof (a roof jack),
    # so it is glued all round, not left hanging in a hole
    zu = lambda x: ZE + (W - x) * S                                    # the panel's underside
    zb = zu(px - pr - 1.2) + 1.2 * n + 1.2
    boot = M.cylinder(zb - zu(px + pr + 1.2) + 0.4, pr + 1.2, pr + 1.2, 28).translate([px, py, zu(px + pr + 1.2) - 0.4])
    boot = boot.trim_by_plane([S / n, 0.0, 1.0 / n], (ZE + S * W) / n)
    hole = M.cylinder(40.0, pr + 0.12, pr + 0.12, 28).translate([px, py, ZE - 5.0])
    left = pan.transform(AL).trim_by_plane([-1.0, 0, 0], -W / 2)
    right = (pan.transform(AR).trim_by_plane([1.0, 0, 0], W / 2) + boot) - hole
    kit.add("ROOF-L", "Roof", left, P=inv34(AL), group="roof")
    kit.add("ROOF-R", "Roof", right, P=inv34(AR), group="roof")
    zr = ZE + W / 2 * S + 1.2 * n + 0.45
    rsec = poly([(W / 2 - 1.6, zr - 1.6 * S), (W / 2, zr), (W / 2 + 1.6, zr - 1.6 * S), (W / 2 + 1.6, zr + 1.2),
                 (W / 2 - 1.6, zr + 1.2)])
    ridge = M.extrude(rsec, Lp).rotate([90, 0, 0]).translate([0, y1, 0])
    kit.add("RIDGE", "Roof", ridge, P=print_flip(), group="roof")
    z0 = round((ZE + (W - px - pr) * S - 0.6) / 0.2) * 0.2
    pipe = TW.chimney("stovepipe", w=2 * pr, d=2 * pr, h=round((zr + 6.0 - z0) / 0.2) * 0.2).translate([px, py, z0])
    kit.add("STOVEPIPE", "Iron", pipe, group="roof")
    print("roof", round(time.time() - t0, 1))

    # --- the boardwalk and the barber pole
    BW_D = 16.0
    bw = SF.boardwalk(W + 2.0, BW_D, ZF, pitch=2.2)
    Ab = np.array([[-1.0, 0, 0, W + 1.0], [0, -1.0, 0, -1.55], [0, 0, 1.0, 0.0]])       # clear of the sill's bolt heads
    # the pole stands 1.6 mm deep in a snug socket in the walk, over a pier under the planks
    PX, PY, PD = 3.0, -13.0, 1.6
    pier = M.cylinder(ZF - 1.0, 2.8, 2.8, 32).translate([PX, PY, 0.0])
    sock = M.cylinder(PD + 0.01, 1.8 + 0.12, 1.8 + 0.12, 32).translate([PX, PY, ZF - PD])
    walk = (bw.transform(Ab) + pier) - sock
    kit.add("BOARDWALK", "Boardwalk", walk, P=print_flip(), group="boardwalk",
            render=FT.plank_zones(walk, ZF, "Planks", "Timber"))
    pole = SF.barber_pole(h=20.0) + M.cylinder(PD + 0.02, 1.8, 1.8, 32).translate([0, 0, -PD])
    pole = pole.translate([PX, PY, ZF])
    kit.add("POLE", "White", pole, group="boardwalk")
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "barber")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:40]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "barber.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))

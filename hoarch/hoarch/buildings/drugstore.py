"""Whitcomb's Pharmacy -- an original HO-scale (1:87.1) two-storey corner drugstore, 1885.

A buff-brick corner building on a bossed stone base. The corner is cut back at the ground
floor for the entrance, a pair of margin-light doors under an arched transom behind a
cast-iron column. Over the column, an octagonal turret is corbelled out of the corner and
rises past the cornice to a copper bell roof with an onion finial. Both street fronts have
a storefront (rosette pilasters, tiled bulkheads, big display lights) under a lettered sign
band, then a cavetto belt; upstairs, windows with shouldered lintels in banded brickwork.
The top is a double cornice (a panelled frieze under a cap on volute brackets) that dies
into the turret. A mortar-and-pestle blade sign hangs from the front. Gravel roof and a
stepped chimney.

Colour comes from the part split (see storefront.py); the sign bands take one filament
change for their letters.

usage: python3 -m hoarch.buildings.drugstore [check] [export]
"""
import math
import os
import sys
import time

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import box, inv34, offset, poly, rect, slab, union
from hoarch import openings as O, skins as SK, storefront as SF, trimwork as TW
from hoarch.kit import Kit
from hoarch.ornament import ext
from hoarch.shell import Block, Opening, _corbel, foundation, stacked_shells, wall_shell

NAME = "Whitcomb's Pharmacy"
COLORS = {"Brick": "#C9A46A", "Plum": "#5B2A3A", "Blue": "#1F3A4F", "Copper": "#4F8570", "Stone": "#9A968E",
          "Roof": "#3A3A3A", "Cream": "#EFE6CF", "Sign": "#5B2A3A", "Iron": "#222222", "Blade": "#222222",
          "Windows_Doors": "#EFE6CF"}
RENDER_MAT = {"Brick": "brick", "Plum": "plum", "Blue": "blue", "Copper": "copper", "Stone": "stone", "Roof": "roof",
              "Cream": "trim", "Sign": "plum", "Letters": "trim", "Iron": "iron", "Blade": "iron", "Windows_Doors": "trim", "Sash": "sash",
              "Door": "door", "Glass": "glass"}

# ------------------------------------------------------------------ levels (v from the block base)
ZF = 4.0
H1 = 38.0
S1 = ZF + H1
RH = 4.4
SF_H = 30.0
SIGN_V, SIGN_H = SF_H, 6.4
VF, FR_H = 70.4, 5.2
VK = VF + FR_H
CAP_PROF = [(0.0, 0.0), (1.6, 0.0), (1.6, 0.6), (1.8, 0.6), (1.8, 2.6), (4.0, 2.6), (4.0, 3.4), (4.2, 3.6), (4.4, 4.0),
            (4.4, 4.6), (0.0, 4.6)]
VTOP = VK + 4.6
ZR = ZF + VK - 1.2
T = 3.0

# ------------------------------------------------------------------ plan
W, D, C = 46.0, 56.0, 10.0
MAIN = Block("main", [(C, 0), (W, 0), (W, D), (0, D), (0, C)], ZF, ZF + VTOP)
FRONT, RIGHT, REAR, LEFT, CORNER = 0, 1, 2, 3, 4
TC, TA = (2.5, 2.5), 7.5                    # turret centre and apothem
TV = TA / math.cos(math.pi / 8)             # its vertex radius
TZ0 = S1 + RH                               # turret walls start on the belt
TZ1 = ZF + VTOP + 8.0
TURRET = Block("turret", [(TC[0] + TV * math.cos(math.pi / 8 + k * math.pi / 4),
                           TC[1] + TV * math.sin(math.pi / 8 + k * math.pi / 4)) for k in range(8)], TZ0, TZ1)
V_UP = S1 - ZF + RH


def _siding(f, b, reg):
    if b is TURRET and f.n[0] + f.n[1] > 0.1:        # the turret's faces against the building stay plain
        return M()
    return SK.banded_brick(reg, every=5, datum=0.0)


def _facade_by_normal(block, n):
    for i, f in enumerate(block.facades()):
        if abs(f.n[0] - n[0]) < 0.05 and abs(f.n[1] - n[1]) < 0.05:
            return i, f
    raise ValueError(n)


def _openings():
    L = []

    def add(x, y, v0, sp, name, kind="window"):
        e, u = MAIN.locate(x, y)
        L.append(Opening(MAIN, e, u, v0, sp, name, kind))

    front = SF.storefront(28.0, SF_H, entry=0, col=2.0, style="rosette", bulk=6.4, transom=5.0, beam=1.6, lite=4.0,
                          bulk_style="tile", mullion=False, posts=True, t=T, bays=2)
    side = SF.storefront(26.0, SF_H, entry=0, col=2.0, style="rosette", bulk=6.4, transom=5.0, beam=1.6, lite=4.0,
                         bulk_style="tile", mullion=False, posts=True, t=T, bays=2)
    add(27.0, 0, 0.0, front, "store-front", "door")
    add(0, 26.0, 0.0, side, "store-side", "door")
    add(C / 2, C / 2, 0.0, SF.door_commercial(6.4, 24.0, transom=4.4, leaf="margin", tstyle="arch", head=None, leaves=2),
        "corner-door", "door")
    add(0, 48.5, 0.0, SF.door_commercial(6.0, 24.0, transom=3.6, leaf="margin", tstyle="arch", head=None), "stair-door",
        "door")
    up = SF.window_commercial(7.0, 18.0, rise=0, lites=(1, 1), rows=(1, 1), sill=1.0, head="shouldered")
    for x in (18.0, 29.0, 40.0):
        add(x, 0, V_UP + 4.0, up, f"F{x:.0f}-2")
    for y in (16.0, 27.0, 38.0, 49.0):
        add(0, y, V_UP + 4.0, up, f"L{y:.0f}-2")
    rear = SF.window_commercial(7.0, 16.0, rise=1.6, lites=(1, 1), rows=(1, 1), sill=1.0)
    add(W - 12.0, D, 0.0, SF.door_commercial(7.0, 22.0, transom=3.0, leaf="margin", tstyle="arch", head=None),
        "back-door", "door")
    add(W - 30.0, D, 10.0, rear, "R16-1")
    for x in (12.0, 30.0):
        add(W - x, D, V_UP + 4.0, rear, f"R{x:.0f}-2")
    return L


OPENINGS = _openings()
APPLIED = [("SIGN-front", FRONT, 13.0 - C, SIGN_V, 28.0, SIGN_H), ("SIGN-side", LEFT, 56.0 - 39.0, SIGN_V, 26.0, SIGN_H),
           ("TOP-front", FRONT, 0.0, VF, W - C, VTOP - VF), ("TOP-side", LEFT, 0.0, VF, D - C, VTOP - VF),
           ("BLADE", FRONT, 0.2, V_UP + 5.4, 3.0, 5.4)]


def _applied_openings():
    return [Opening(MAIN, e, 0.0, 0.0, SF.applied(rect(u0, v0, u0 + L, v0 + h)), name, "trim")
            for name, e, u0, v0, L, h in APPLIED]


def _turret_prism(z0, z1, grow=0.0):
    return slab(offset(TURRET.cs, grow), z0, z1)


def _turret_openings():
    L = []
    win = SF.window_commercial(4.4, 14.0, rise=2.2, lites=(1, 1), rows=(1, 1), sill=None)
    for n in ((-1.0, 0.0), (-math.sqrt(0.5), -math.sqrt(0.5)), (0.0, -1.0)):
        e, f = _facade_by_normal(TURRET, n)
        L.append(Opening(TURRET, e, f.L / 2, 4.0, win, f"T{e}", "window"))
    return L


def _gilt(solid, A, level, lo="Sign", hi="Letters"):
    top = solid ^ box([-1e3, -1e3, level], [1e3, 1e3, 1e3])
    return [(lo, (solid - top).transform(A)), (hi, top.transform(A))]


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    base = MAIN.cs
    bprof, _ = TW.BELTS["cavetto"]
    st = stacked_shells([MAIN], OPENINGS + _applied_openings(), [S1], t=T, corners="none", siding=_siding, prof=bprof,
                        belt_blocks=None, water_table=False)
    posts = union([o.spec["posts"].transform(o.local_frame()) for o in OPENINGS if o.name.startswith("store-")])
    kit.add("WALLS-1", "Brick", st["shells"][0] + posts, group="walls")
    ring = st["rings"][0]
    tprism = _turret_prism(TZ0 - 0.01, TZ1 + 1)
    walls2 = st["shells"][1] + _corbel(base, T, ZR) - tprism
    kit.add("WALLS-2", "Brick", walls2, group="walls")
    # the turret: an octagonal shell of its own, standing on the belt and its corbel
    tops = _turret_openings()
    tw = wall_shell([TURRET], tops, t=2.0, belt=None, corners="none", water_table=False, siding=_siding)
    kit.add("TURRET", "Brick", tw - walls2, group="turret")          # its corner beads stop at the building
    for o in tops:
        world, P, zones = O.place(o.spec, o.local_frame(), "Windows_Doors", "Sash", "Glass")
        kit.add(f"WIN-{o.name}", "Windows_Doors", world, P=P, key="WIN-turret", group="inserts", render=zones)
    # corbel: an octagonal cone stepping out at 45 degrees from the column's head to the turret
    zc0 = TZ0 - 0.6 - (TV - 2.2) - 1.2
    prof = [(0.0, zc0), (2.2, zc0), (2.2, zc0 + 1.2), (TV, zc0 + 1.2 + (TV - 2.2)), (TV + 0.3, TZ0 - 0.6 + 0.3),
            (TV + 0.3, TZ0), (0.0, TZ0)]
    corb = M.revolve(poly(prof), 8).rotate([0, 0, 22.5]).translate([TC[0], TC[1], 0])
    k = math.sqrt(0.5)
    corb = corb.trim_by_plane([-k, -k, 0.0], -(C - 0.05) * k) - ring - st["shells"][0]     # flat against the corner
    kit.add("CORBEL", "Plum", corb, group="turret")
    zb = ZF - 1.0                                  # it stands on the stone platform
    hc = zc0 - zb
    cprof = [(0, 0), (1.6, 0), (1.6, 0.8), (1.3, 1.1), (1.3, 1.8), (1.05, 2.3), (1.05, hc - 4.2), (1.3, hc - 3.6),
             (1.3, hc - 3.0), (1.1, hc - 2.8), (1.6, hc - 1.0), (2.1, hc - 0.4), (2.1, hc), (0, hc)]
    column = M.revolve(poly(cprof), 32).translate([TC[0], TC[1], zb])
    kit.add("COLUMN", "Iron", column, group="turret")
    # the turret's copper bell roof on a flared eave, and its finial
    rp = [(0.0, 0.0), (TV - 0.1, 0.0), (TV + 1.3, 1.4), (TV + 1.3, 2.2)]
    Hr = 15.0
    for s in np.linspace(0.05, 1.0, 12):
        rp.append(((TV + 1.3) * (1 - s) ** 1.6 + 0.9 * s, 2.2 + Hr * s))
    rp.append((0.0, 2.2 + Hr))
    troof = M.revolve(poly(rp), 8).rotate([0, 0, 22.5]).translate([TC[0], TC[1], TZ1])
    kit.add("TURRET-roof", "Copper", troof, group="turret")
    fin = TW.finial("onion", r=0.9, h=6.0).translate([TC[0], TC[1], TZ1 + 2.2 + Hr - 0.01])
    kit.add("FINIAL", "Copper", fin, group="turret")
    kit.add("BELT", "Cream", ring - _turret_prism(TZ0 - 0.01, TZ0 + 3.0, grow=0.1), group="walls")
    print("walls + turret", round(time.time() - t0, 1))

    # --- storefronts, doors, windows
    for o in OPENINGS:
        s = o.spec
        b = s["cut"].bounds()
        if o.name.startswith("store-"):
            world, P, zones = O.place(s, o.local_frame(), "Blue", "Blue", "Glass")
            kit.add(o.name.upper(), "Blue", world, P=P, group="storefront", render=zones)
            continue
        key = "DOOR" if o.kind == "door" else "WIN"
        world, P, zones = O.place(s, o.local_frame(), "Windows_Doors", "Door" if o.kind == "door" else "Sash", "Glass")
        kit.add(f"{key}-{o.name}", "Windows_Doors", world, P=P, key=f"{key}-{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}",
                group="inserts", render=zones)
    kit.add("FOUNDATION", "Stone", foundation([MAIN], 0.0, ZF, style="bossed", lip=1.2), group="foundation")
    # a stone platform at the cut corner (the column stands on it) and a step up to the door
    fc = facs_ = MAIN.facades()[CORNER]
    Ac = fc.A.copy()
    Ac[:, 3] = fc.world(fc.L / 2, 0.0, 0.0)
    steps = box([-5.8, -ZF, 1.4], [5.8, -1.0, 7.0])                   # the door sill is one step up
    kit.add("STEPS", "Stone", steps.transform(Ac), group="foundation")

    # --- signs, the double cornice (dying into the turret), coping, blade sign
    facs = MAIN.facades()

    def frame(e, u0, v0, w0=0.0):
        f = facs[e]
        A_ = f.A.copy()
        A_[:, 3] = f.world(u0, v0, w0)
        return A_

    for name, e, text, cap, L_, u0 in (("SIGN-front", FRONT, "PHARMACY", 2.7, 28.0, 13.0 - C),
                                       ("SIGN-side", LEFT, "DRUGS", 3.2, 26.0, 56.0 - 39.0)):
        sg = SF.sign_band(L_, SIGN_H, text, cap=cap, font="roman", board=1.0, frame=0.8, relief=0.4)
        A_ = frame(e, u0, SIGN_V)
        kit.add(name, "Sign", sg.transform(A_), P=inv34(A_), group="front", render=_gilt(sg, A_, 1.0))
    cut = _turret_prism(0.0, 200.0, grow=0.6) + walls2
    for e, tag, ext_start in ((FRONT, "front", True), (LEFT, "side", False)):
        f = facs[e]
        u0 = -6.0 if ext_start else 0.0
        u1 = f.L if ext_start else f.L + 6.0
        L_ = u1 - u0
        n = int(L_ // 9)
        pitch = L_ / n
        panels = [(k * pitch + 1.6, (k + 1) * pitch - 1.6) for k in range(n)]
        tails = [max(0.8, min(L_ - 0.8, k * pitch)) for k in range(n + 1)]
        fr = SF.frieze_band(L_, FR_H, board=1.2, panels=panels, tails=dict(us=tails, w=1.2, d=1.8, style="volute"))
        A_ = frame(e, u0, VF)
        kit.add(f"FRIEZE-{tag}", "Cream", fr.transform(A_) - cut, P=inv34(A_), group="top")
        cp = SF.cornice_cap(L_, CAP_PROF) + SF.bracket_row(L_, tails, 1.8, 3.8, 1.2, 2.6, style="volute")
        A_ = frame(e, u0, VK)
        kit.add(f"CORNICE-{tag}", "Plum", cp.transform(A_) - cut, P=inv34(A_), group="top")
    zt = ZF + VTOP
    cop = slab(offset(base, 0.6) - offset(base, -T - 0.4), zt, zt + 0.8) - cut
    front_cap = box([C - 6.0, -4.6, zt], [W + 0.6, 0.0, zt + 0.8]) + box([-4.6, C - 6.0, zt], [0.0, D + 0.6, zt + 0.8])
    kit.add("COPING", "Stone", cop + (front_cap - cut), group="top")
    # blade sign on the pier beside the turret, arm out from the front wall
    bs = SF.blade_sign(SF.mortar_pestle_cs(7.0, 6.4), "Rx", cap=1.6, t=1.2, arm=9.0, drop=2.6)
    Ab = np.array([[0.0, 0.0, -1.0, C + 2.8], [-1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, ZF + V_UP + 9.2]])
    kit.add("BLADE", "Blade", bs.transform(Ab), P=inv34(Ab), group="front", render=_gilt(bs, Ab, 0.8, "Iron", "Letters"))
    print("front", round(time.time() - t0, 1))

    # --- gravel roof and chimney
    inner = offset(base, -T - 0.15)
    cw, cd = 8.0, 6.0
    cx, cy = W - T - 0.6 - cd / 2, D - 18.0
    deck = SF.gravel_deck(inner, ZR, t=1.2)
    zdk = ZR + 1.2
    pocket = box([cx - cd / 2 - 0.4, cy - cw / 2 - 0.4, zdk - 0.6], [cx + cd / 2 + 0.4, cy + cw / 2 + 0.4, zdk + 2])
    kit.add("ROOF", "Roof", deck - pocket - _turret_prism(ZR - 1, ZR + 5, grow=0.8), group="roof")
    ch = TW.chimney("stepped", w=cw, d=cd, h=round((zt + 10.0 - (zdk - 0.6)) / 0.2) * 0.2)
    kit.add("CHIMNEY", "Brick", ch.rotate([0, 0, 90]).translate([cx, cy, zdk - 0.6]), group="roof")
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "drugstore")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:40]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "drugstore.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))

"""Vogel's Bakery -- an original HO-scale (1:87.1) one-and-a-half-storey brick bakery, 1895.

A narrow brick shop in monk bond on a herringbone brick base, under a steep pantile roof.
The street front rises into a crow-stepped gable with stone copings on every step and a
date stone near the top. Below: a big round-arched shop window of small panes under a
dog-tooth brick arch keyed with stone, a Dutch door with a heart in its transom, a BAKERY
sign board, and a gilt pretzel hanging from a scrolled iron arm. Two windows light the room
in the gable. A tapered oven stack rises at the back.

Colour comes from the part split (see storefront.py): the sign board and the pretzel each
take one filament change.

usage: python3 -m hoarch.buildings.bakery [check] [export]
"""
import math
import os
import sys
import time

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import box, cs_union, inv34, poly, rect, union
from hoarch import features as FT, openings as O, skins as SK, storefront as SF, trimwork as TW
from hoarch.kit import Kit, print_flip
from hoarch.ornament import ext
from hoarch.shell import Block, Opening, foundation, wall_shell

NAME = "Vogel's Bakery"
COLORS = {"Brick": "#B5553A", "Stone": "#CFC6B0", "Tile": "#9E4A2E", "Green": "#2F5D3A", "Sign": "#2F5D3A",
          "Blade": "#1E1E1E", "Base": "#7A3A28", "Windows_Doors": "#F2EAD6"}
RENDER_MAT = {"Brick": "brick", "Stone": "stone", "Tile": "tile", "Green": "green", "Sign": "green", "Blade": "iron",
              "Gilt": "gilt", "Base": "base", "Windows_Doors": "trim", "Sash": "sash", "Door": "door", "Glass": "glass"}

ZF = 5.0
H = 40.0                   # eaves (outer face of the side walls)
S = 1.0                    # 45 degree roof
T = 3.0
W, D = 76.0, 104.0
HB = H + T * S
MAIN = Block("main", [(0, 0), (W, 0), (W, D), (0, D)], ZF, ZF + HB)
ZE = ZF + H
DE = 2.4
Y0R = T + 0.15
STEP = 5.0
N_STEPS = 7
TOPS = [H + STEP * (k + 1) + 1.6 for k in range(N_STEPS)]
CROWN = (W / 2 - 3.0, W / 2 + 3.0, H + W / 2 + 5.0)
WIN = (26.0, 5.0, 26.0, 32.0, 13.0)      # shop window: u, v0, w, h, rise
SIGN_V, SIGN_H = H + 1.0, 8.0
SIGN_U = 6.0                             # clear of the lowest crow step
BLADE_X, BLADE_V = 4.0, 28.0
DATE_W, DATE_H = 9.0, 4.2


def _front_gable():
    cs = [rect(STEP * k, HB - 0.01, W - STEP * k, TOPS[k]) for k in range(N_STEPS)]
    cs.append(rect(CROWN[0], HB - 0.01, CROWN[1], CROWN[2]))
    return cs_union(cs)


def _siding(f, b, reg):
    if f.n[1] < -0.3:                       # the street front: a dog-tooth arch over the shop window
        u, v0, w, h, rise = WIN
        band, rel = SK.dentil_arch(u, v0, w, h, rise, casing=0.6)
        return SK.brick_bond(reg - band, "monk", datum=0.0) + (rel ^ M.extrude(reg, 3.0).translate([0, 0, -1.0]))
    return SK.brick_bond(reg, "monk", datum=0.0)


def _openings():
    L = []

    def add(x, y, v0, sp, name, kind="window"):
        e, u = MAIN.locate(x, y)
        L.append(Opening(MAIN, e, u, v0, sp, name, kind))

    u, v0, w, h, rise = WIN
    add(u, 0, v0, SF.window_commercial(w, h, rise=rise, lites=(5, 5), rows=(4, 3), sill=1.6), "shop-window")
    add(58.0, 0, 0.0, SF.door_commercial(10.0, 30.0, transom=5.0, leaf="dutch", tstyle="heart", head=None), "shop-door",
        "door")
    gw = SF.window_commercial(7.0, 10.0, rise=1.6, lites=(1, 1), rows=(2, 2), sill=1.0)
    for x in (W / 2 - 10.0, W / 2 + 10.0):
        add(x, 0, SIGN_V + SIGN_H + 2.4, gw, f"G{x:.0f}")
    side = SF.window_commercial(8.4, 21.0, rise=1.8, lites=(2, 2), rows=(2, 2), sill=1.0)
    for y in (26.0, 52.0, 78.0):
        add(W, y, 10.0, side, f"E{y:.0f}")
        add(0, y, 10.0, side, f"W{y:.0f}")
    add(W - 16.0, D, 0.0, SF.door_commercial(10.0, 30.0, transom=4.0, leaf="dutch", tstyle="heart", head=None),
        "back-door", "door")
    add(W - 44.0, D, 10.0, side, "N44")
    return L


OPENINGS = _openings()
APPLIED = [("SIGN", SIGN_U, SIGN_V, W - 2 * SIGN_U, SIGN_H),
           ("DATE", W / 2 - DATE_W / 2, TOPS[-1] - DATE_H - 0.8, DATE_W, DATE_H),
           ("BLADE", BLADE_X - 1.9, BLADE_V - 3.0, 2.0, 4.4)]


def _applied_openings():
    return [Opening(MAIN, 0, 0.0, 0.0, SF.applied(rect(u0, v0, u0 + L, v0 + h)), name, "trim")
            for name, u0, v0, L, h in APPLIED]


def _roof_cut():
    sec = poly([(-10.0, ZE - 10.0 * S), (W / 2, ZE + W / 2 * S), (W + 10.0, ZE - 10.0 * S), (W + 10.0, ZE + 200.0),
                (-10.0, ZE + 200.0)])
    return M.extrude(sec, D + 10.0 - T).rotate([90, 0, 0]).translate([0, D + 10.0, 0])


def _gilt(solid, A, level, lo):
    top = solid ^ box([-1e3, -1e3, level], [1e3, 1e3, 1e3])
    return [(lo, (solid - top).transform(A)), ("Gilt", top.transform(A))]


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    rear = [(0.0, HB - 0.01), (W, HB - 0.01), (W / 2, HB + W / 2 * S + 1.0)]
    walls = wall_shell([MAIN], OPENINGS + _applied_openings(), t=T, belt=None, corners="none", water_table=False,
                       siding=_siding, gables=[(MAIN, 0, _front_gable()), (MAIN, 2, poly(rear))])
    kit.add("WALLS", "Brick", walls - _roof_cut(), group="walls")
    kit.add("FOUNDATION", "Base", foundation([MAIN], 0.0, ZF, style="herringbone", lip=1.2), group="foundation")
    for o in OPENINGS:
        s = o.spec
        b = s["cut"].bounds()
        key = "DOOR" if o.kind == "door" else "WIN"
        world, P, zones = O.place(s, o.local_frame(), "Windows_Doors", "Door" if o.kind == "door" else "Sash", "Glass")
        kit.add(f"{key}-{o.name}", "Windows_Doors", world, P=P, key=f"{key}-{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}",
                group="inserts", render=zones)
    print("walls", round(time.time() - t0, 1))

    # --- stone copings on the crow steps (one part), date stone, sign, pretzel
    # each step's cap is its own small part (they print on the bed, not stacked in the air)
    def cap(xi0, xi1, xo0, xo1, z, hgt=0.8):
        return M.hull_points([(x, y, z) for x in (xi0, xi1) for y in (0.0, T)] +
                             [(x, y, z + 0.4) for x in (xo0, xo1) for y in (-0.4, T + 0.1)] +
                             [(x, y, z + hgt) for x in (xo0, xo1) for y in (-0.4, T + 0.1)])
    for k in range(N_STEPS):
        z = ZF + TOPS[k]
        a, b = STEP * k, STEP * (k + 1)
        kit.add(f"COPING-{k}L", "Stone", cap(a, b, a - 0.4, b, z), key=f"COPING-{k}", group="front")
        kit.add(f"COPING-{k}R", "Stone", cap(W - b, W - a, W - b, W - a + 0.4, z), key=f"COPING-{k}", group="front")
    zc = ZF + CROWN[2]
    kit.add("COPING-crown", "Stone", cap(CROWN[0], CROWN[1], CROWN[0] - 0.4, CROWN[1] + 0.4, zc, 1.2), group="front")
    f = MAIN.facades()[0]

    def frame_at(u0, v0, w0=0.0):
        A_ = f.A.copy()
        A_[:, 3] = f.world(u0, v0, w0)
        return A_

    date = box([0, 0, 0], [DATE_W, DATE_H, 0.8]) + \
        ext(SF.text_cs("1895", 2.6, "roman", grow=0.1).translate((DATE_W / 2, 0.8)), 0.79, 1.2)
    Ad = frame_at(W / 2 - DATE_W / 2, TOPS[-1] - DATE_H - 0.8)
    kit.add("DATE", "Stone", date.transform(Ad), P=inv34(Ad), group="front")
    sign = SF.sign_band(W - 2 * SIGN_U, SIGN_H, "BAKERY", cap=5.6, font="roman", board=1.0, frame=1.0, relief=0.4)
    As = frame_at(SIGN_U, SIGN_V)
    kit.add("SIGN", "Sign", sign.transform(As), P=inv34(As), group="front", render=_gilt(sign, As, 1.0, "Sign"))
    bs = SF.blade_sign(SF.pretzel_cs(7.0, 6.0), None, t=1.2, arm=8.0, drop=2.2)
    Ab = np.array([[0.0, 0.0, -1.0, BLADE_X], [-1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, ZF + BLADE_V]])
    kit.add("BLADE", "Blade", bs.transform(Ab), P=inv34(Ab), group="front", render=_gilt(bs, Ab, 0.8, "Blade"))
    print("front", round(time.time() - t0, 1))

    # --- the roof: two pantile panels at 45 degrees, a ridge, the oven stack
    n = math.sqrt(1 + S * S)
    y1 = D + DE
    Lp = y1 - Y0R
    Vp = (W / 2 + DE) * n + 1.0
    pan = SF.pantile_panel(Lp, Vp, t=1.2, pitch=2.4, course=4.0)
    AL = np.array([[0.0, 1 / n, -S / n, -DE], [-1.0, 0.0, 0.0, y1], [0.0, S / n, 1 / n, ZE - DE * S]])
    AR = np.array([[0.0, -1 / n, S / n, W + DE], [1.0, 0.0, 0.0, Y0R], [0.0, S / n, 1 / n, ZE - DE * S]])
    cx, cy, cw = 56.0, 80.0, 9.0
    hole = box([cx - cw / 2 - 0.3, cy - cw / 2 - 0.3, ZE - 10], [cx + cw / 2 + 0.3, cy + cw / 2 + 0.3, ZE + 80])
    kit.add("ROOF-L", "Tile", pan.transform(AL).trim_by_plane([-1.0, 0, 0], -W / 2), P=inv34(AL), group="roof")
    kit.add("ROOF-R", "Tile", pan.transform(AR).trim_by_plane([1.0, 0, 0], W / 2) - hole, P=inv34(AR), group="roof")
    zr = ZE + W / 2 * S + 1.2 * n + 1.2
    rsec = poly([(W / 2 - 2.0, zr - 2.0 * S), (W / 2, zr), (W / 2 + 2.0, zr - 2.0 * S), (W / 2 + 2.0, zr + 1.0),
                 (W / 2 - 2.0, zr + 1.0)])
    ridge = M.extrude(rsec, Lp - 0.4).rotate([90, 0, 0]).translate([0, y1, 0])          # clear of the crown's cap
    kit.add("RIDGE", "Tile", ridge, P=print_flip(), group="roof")
    zlow = round((ZE + (W - cx - cw / 2) * S - 3.0) / 0.2) * 0.2
    ch = TW.chimney("tapered", w=cw, d=cw, h=round((zr + 9.0 - zlow) / 0.2) * 0.2).translate([cx, cy, zlow])
    kit.add("CHIMNEY", "Brick", ch, group="roof")
    # glue joints: nothing small is left butted on a dab of glue (see NOTES.md)
    FT.key_into(kit, "BLADE", ["WALLS"], (0, 1, 0))
    FT.key_into(kit, "RIDGE", ["ROOF-L", "ROOF-R"], (0, 0, -1), depth=0.3, conform=True)
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "bakery")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:40]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "bakery.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))

"""The Palace Hotel & Saloon -- an original HO-scale (1:87.1) three-storey wooden hotel, 1883.

A false-front hotel in coursed square-butt shingles on a cobble base, with rolled belt
courses between the storeys. On the ground floor, the saloon's batwing doorway under a
lettered head board and a big window beside it, and the hotel's pair of French doors with
HOTEL in the transom. Across the whole front, a balcony at the second floor, carried on
five big knee brackets without posts, with a wrought-iron ring railing and three French
doors opening onto it. Third-floor windows under drip caps. A tall projecting sign spells
HOTEL down its face; the false front carries PALACE HOTEL, a cornice and a raised crest
with the date. Board-and-batten gable roof behind, and two slab-capped chimneys.

Colour comes from the part split (see storefront.py). The signs take one filament change
for their letters; the balcony deck prints planks-first (one change).

usage: python3 -m hoarch.buildings.hotel [check] [export]
"""
import math
import os
import sys
import time

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import box, inv34, poly, rect, union
from hoarch import features as FT, openings as O, roof as R, skins as SK, storefront as SF, trimwork as TW
from hoarch.kit import Kit, print_flip
from hoarch.ornament import ext
from hoarch.shell import Block, Opening, foundation, stacked_shells

NAME = "The Palace Hotel"
COLORS = {"Siding": "#5E7A8A", "Cream": "#EEE5CD", "Maroon": "#6B2A2A", "Iron": "#1E1E1E", "Deck": "#EEE5CD",
          "Planks": "#6F5034", "Roof": "#5A5550", "Stone": "#8A857C", "Brick": "#8A3F2C", "Sign": "#6B2A2A",
          "VSign": "#6B2A2A", "Windows_Doors": "#EEE5CD"}
RENDER_MAT = {"Siding": "siding", "Cream": "trim", "Maroon": "maroon", "Iron": "iron", "Deck": "trim", "Planks": "planks",
              "Roof": "roof", "Stone": "stone", "Brick": "brick", "Sign": "maroon", "VSign": "maroon", "Gilt": "gilt",
              "Windows_Doors": "trim", "Sash": "sash", "Door": "door", "Glass": "glass"}

# ------------------------------------------------------------------ levels (v from the block base)
ZF = 5.0
H1, H2, H3 = 42.0, 38.0, 36.0
RH = 4.4
S1 = ZF + H1
S2 = S1 + RH + H2
ZE = S2 + RH + H3         # eaves (outer face of the side walls)
S = 0.25                  # roof slope (low, so the false front hides it)
T = 3.0
V2 = S1 - ZF + RH         # second floor (the balcony's level)
V3 = S2 - ZF + RH
HB = ZE - ZF + T * S      # block height: the side walls are trimmed to the roof planes
SIGN_V, SIGN_H = HB + 0.2, 10.0
CAP_K = 1.3
CAP_PROF = [(CAP_K * a, CAP_K * b) for a, b in
            [(0.0, 0.0), (1.2, 0.0), (1.2, 0.6), (1.6, 0.6), (1.6, 1.4), (3.2, 1.4), (3.2, 2.0), (3.4, 2.2), (3.6, 2.6),
             (3.6, 3.2), (0.0, 3.2)]]
CAP_H = CAP_K * 3.2
CAP_V = SIGN_V + SIGN_H + 0.4
FF = CAP_V + CAP_H        # false-front top

# ------------------------------------------------------------------ plan
W, D = 88.0, 124.0
CREST = (W / 2 - 16.0, W / 2 + 16.0, 5.6)
MAIN = Block("main", [(0, 0), (W, 0), (W, D), (0, D)], ZF, ZF + HB)
DE = 2.4
Y0R = T + 0.15
BAL_D = 12.0              # balcony depth
BAL_Y = -1.2              # the balcony's wall-side edge (clear of the belt)
BRACKETS = (1.2, 23.0, 44.0, 65.0, W - 1.2)
BRK_H = 7.0
VSIGN_X = W - 0.6


def _siding(f, b, reg):
    return SK.coursed_shingles(reg, pitch=1.8, width=2.0, datum=0.0)


def _openings():
    L = []

    def add(x, y, v0, sp, name, kind="window"):
        e, u = MAIN.locate(x, y)
        L.append(Opening(MAIN, e, u, v0, sp, name, kind))

    add(14.0, 0, 0.0, SF.door_batwing(11.0, 30.0, text="SALOON"), "saloon-door", "door")
    big = SF.window_commercial(14.0, 24.0, rise=0, lites=(1, 3), rows=(1, 1), sill=1.2)
    add(32.0, 0, 8.0, big, "saloon-window")
    add(56.0, 0, 0.0, SF.door_commercial(11.0, 30.0, transom=4.4, leaf="french", tstyle="text:HOTEL", head=None, leaves=2),
        "hotel-door", "door")
    add(74.0, 0, 8.0, SF.window_commercial(8.4, 24.0, rise=0, lites=(1, 3), rows=(1, 1), sill=1.2), "lobby-window")
    bal = SF.door_commercial(9.6, 28.0, transom=0.0, leaf="french", tstyle="text:HOTEL", head=None, leaves=2)
    for x in (16.0, 44.0, 72.0):
        add(x, 0, V2, bal, f"balcony-{x:.0f}", "door")
    w3 = SF.window_commercial(8.4, 21.0, rise=0, lites=(1, 3), rows=(1, 1), sill=1.0, head="drip")
    for x in (12.0, 28.0, 44.0, 60.0, 76.0):
        add(x, 0, V3 + 5.0, w3, f"F{x:.0f}-3")
    side = SF.window_commercial(8.4, 21.0, rise=0, lites=(1, 3), rows=(1, 1), sill=1.0, head="drip")
    for y in (24.0, 50.0, 76.0, 102.0):
        for v in (V2 + 5.0, V3 + 5.0):
            add(W, y, v, side, f"E{y:.0f}-{v:.0f}")
            add(0, y, v, side, f"W{y:.0f}-{v:.0f}")
    add(W - 18.0, D, 0.0, SF.door_commercial(10.0, 30.0, transom=4.0, leaf="french", tstyle="text:HOTEL", head=None),
        "back-door", "door")
    for x in (22.0, 44.0, 66.0):
        add(W - x, D, V2 + 5.0, side, f"N{x:.0f}-2")
        add(W - x, D, V3 + 5.0, side, f"N{x:.0f}-3")
    return L


OPENINGS = _openings()
_VS, VS_H = SF.vertical_sign("HOTEL", cap=4.2)
VS_V = V3 - 2.0
APPLIED = [("SIGN", 3.0, SIGN_V, W - 6.0, SIGN_H), ("CAP", 0.0, CAP_V, W, CAP_H),
           ("CREST", CREST[0], FF, CREST[1] - CREST[0], CREST[2])] + \
          [(f"BRK{k}", u - 1.0, V2 - RH - BRK_H, 2.0, BRK_H) for k, u in enumerate(BRACKETS)] + \
          [(f"VS{k}", VSIGN_X - 1.7, VS_V + y - 1.5, 1.8, 3.0) for k, y in enumerate((VS_H * 0.15, VS_H * 0.85))]


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
    ff = rect(0.0, HB - 0.01, W, FF) + rect(CREST[0], FF - 0.01, CREST[1], FF + CREST[2])
    bprof, _ = TW.BELTS["roll"]
    st = stacked_shells([MAIN], OPENINGS + _applied_openings(), [S1, S2], t=T, corners="none", siding=_siding,
                        prof=bprof, belt_blocks=None, water_table=False, gables=[(MAIN, 0, ff), (MAIN, 2, poly(rear))])
    cut = _roof_cut()
    kit.add("WALLS-1", "Siding", st["shells"][0], group="walls")
    kit.add("BELT-1", "Cream", st["rings"][0], group="walls")
    kit.add("WALLS-2", "Siding", st["shells"][1], group="walls")
    kit.add("BELT-2", "Cream", st["rings"][1], group="walls")
    kit.add("WALLS-3", "Siding", st["shells"][2] - cut, group="walls")
    kit.add("FOUNDATION", "Stone", foundation([MAIN], 0.0, ZF, style="cobble", lip=1.2), group="foundation")
    for o in OPENINGS:
        s = o.spec
        b = s["cut"].bounds()
        key = "DOOR" if o.kind == "door" else "WIN"
        world, P, zones = O.place(s, o.local_frame(), "Windows_Doors", "Door" if o.kind == "door" else "Sash", "Glass")
        kit.add(f"{key}-{o.name}", "Windows_Doors", world, P=P, key=f"{key}-{o.name.split('-')[0]}-{b[2] - b[0]:.1f}",
                group="inserts", render=zones)
    print("walls + openings", round(time.time() - t0, 1))

    # --- the balcony: knee brackets on the wall, a planked deck on them, iron railings
    f = MAIN.facades()[0]

    def frame_at(u0, v0, w0=0.0):
        A_ = f.A.copy()
        A_[:, 3] = f.world(u0, v0, w0)
        return A_

    v_brk = V2 - RH                                       # the brackets' tops = the deck's underside
    for k, u in enumerate(BRACKETS):
        br = SF.console(BRK_H, BAL_D - 0.4, 1.8, 0.0, 0.0, style="knee")
        A_ = frame_at(u, v_brk)
        kit.add(f"BRACKET-{k}", "Cream", br.transform(A_), P=inv34(A_), key="BRACKET", group="balcony")
    z_deck = ZF + V2
    deck = SF.boardwalk(W + 2.0, BAL_D, z_deck, pitch=2.0, base=z_deck - 1.2 - (ZF + v_brk), stringers=3)
    Ad = np.array([[-1.0, 0, 0, W + 1.0], [0, -1.0, 0, BAL_Y], [0, 0, 1.0, 0.0]])
    dk = deck.transform(Ad)
    kit.add("BALCONY", "Deck", dk, P=print_flip(), group="balcony", render=FT.plank_zones(dk, z_deck, "Planks", "Deck"))
    yf = BAL_Y - BAL_D + 0.8                               # the front railing's inner face
    front = SF.iron_railing(W + 2.0, h=9.0)
    Af = np.array([[1.0, 0, 0, -1.0], [0, 0, -1.0, yf], [0, 1.0, 0, z_deck]])
    kit.add("RAIL-front", "Iron", front.transform(Af), P=inv34(Af), group="balcony")
    Le = yf - BAL_Y - 0.2
    endr = SF.iron_railing(-Le if Le < 0 else Le, h=9.0, pitch=2.4)
    for k, x in enumerate((-1.0, W + 0.2)):
        Ae = np.array([[0.0, 0, 1.0, x], [1.0, 0, 0, yf], [0, 1.0, 0, z_deck]])
        kit.add(f"RAIL-end-{k}", "Iron", endr.transform(Ae), P=inv34(Ae), key="RAIL-end", group="balcony")
    print("balcony", round(time.time() - t0, 1))

    # --- the false front: sign, cornice, crest; the vertical sign
    sign = SF.sign_band(W - 6.0, SIGN_H, "PALACE HOTEL", cap=6.0, font="roman", board=1.0, frame=1.0, relief=0.4)
    As = frame_at(3.0, SIGN_V)
    kit.add("SIGN", "Sign", sign.transform(As), P=inv34(As), group="front", render=_gilt(sign, As, 1.0, "Sign"))
    cap = SF.cornice_cap(W, CAP_PROF, dentils=dict(v=0.8, h=1.0, d=1.8, tooth=0.6, gap=0.6))
    Ac = frame_at(0.0, CAP_V)
    kit.add("CAP", "Cream", cap.transform(Ac), P=inv34(Ac), group="front")
    cw = CREST[1] - CREST[0]
    crest = box([0, 0, 0], [cw, CREST[2], 0.8]) + box([-0.3, CREST[2] - 1.0, 0.0], [cw + 0.3, CREST[2], 1.4]) + \
        ext(SF.text_cs("1883", 3.2, "roman", grow=0.1).translate((cw / 2, 0.7)), 0.79, 1.2)
    Acr = frame_at(CREST[0], FF)
    kit.add("CREST", "Maroon", crest.transform(Acr), P=inv34(Acr), group="front")
    Av = np.array([[0.0, 0.0, -1.0, VSIGN_X], [-1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, ZF + VS_V]])
    kit.add("VSIGN", "VSign", _VS.transform(Av), P=inv34(Av), group="front", render=_gilt(_VS, Av, 1.0, "VSign"))
    print("front", round(time.time() - t0, 1))

    # --- the roof: two board-and-batten panels on the walls' sloped tops, a ridge, chimneys
    n = math.sqrt(1 + S * S)
    y1 = D + DE
    Lp = y1 - Y0R
    Vp = (W / 2 + DE) * n + 1.0
    pan = SF.batten_panel(Lp, Vp, t=1.2, pitch=3.0)
    AL = np.array([[0.0, 1 / n, -S / n, -DE], [-1.0, 0.0, 0.0, y1], [0.0, S / n, 1 / n, ZE - DE * S]])
    AR = np.array([[0.0, -1 / n, S / n, W + DE], [1.0, 0.0, 0.0, Y0R], [0.0, S / n, 1 / n, ZE - DE * S]])
    chims = [(18.0, 84.0), (70.0, 48.0)]
    cwid = 8.0
    holes = union([box([x - cwid / 2 - 0.3, y - cwid / 2 - 0.3, ZE - 10], [x + cwid / 2 + 0.3, y + cwid / 2 + 0.3, ZE + 60])
                   for x, y in chims])
    kit.add("ROOF-L", "Roof", pan.transform(AL).trim_by_plane([-1.0, 0, 0], -W / 2) - holes, P=inv34(AL), group="roof")
    kit.add("ROOF-R", "Roof", pan.transform(AR).trim_by_plane([1.0, 0, 0], W / 2) - holes, P=inv34(AR), group="roof")
    zr = ZE + W / 2 * S + 1.2 * n + 0.5
    rsec = poly([(W / 2 - 1.8, zr - 1.8 * S), (W / 2, zr), (W / 2 + 1.8, zr - 1.8 * S), (W / 2 + 1.8, zr + 1.2),
                 (W / 2 - 1.8, zr + 1.2)])
    ridge = M.extrude(rsec, Lp).rotate([90, 0, 0]).translate([0, y1, 0])
    kit.add("RIDGE", "Roof", ridge, P=print_flip(), group="roof")
    for k, (x, y) in enumerate(chims):
        dist = min(x, W - x)                          # from the nearer eave
        zlow = ZE + (dist - cwid / 2) * S - 3.0
        zlow = round(zlow / 0.2) * 0.2
        ch = TW.chimney("slab", w=cwid, d=cwid, h=round((zr + 6.0 - zlow) / 0.2) * 0.2).translate([x, y, zlow])
        kit.add(f"CHIMNEY-{k}", "Brick", ch, key="CHIMNEY", group="roof")
    # glue joints: nothing small is left butted on a dab of glue (see NOTES.md)
    FT.key_into(kit, "VSIGN", ["WALLS-3"], (0, 1, 0))
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "hotel")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:40]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "hotel.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))

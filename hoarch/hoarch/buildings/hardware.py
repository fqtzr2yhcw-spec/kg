"""Bassett Hardware & Feed -- an original HO-scale (1:87.1) two-storey stone store, 1872.

A split-face limestone store on a battered base with a stone string course between the
floors. The ground floor is three round-arched bays under voussoir rings with keystones:
two display windows and, between them, a pair of glazed board doors under a fanlight.
Upstairs, windows under splayed jack arches with iron fire shutters hooked open beside
them, and in the middle a loading door with a hoist beam, pulley, rope, block and hook
above it. The front parapet carries a lettered frieze, a cornice and a raised date panel;
the side parapets step down toward the rear over a shingled shed roof.

Colour comes from the part split (see storefront.py): the frieze takes one filament change
for its letters.

usage: python3 -m hoarch.buildings.hardware [check] [export]
"""
import math
import os
import sys
import time

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import ashlar, box, cs_union, inv34, poly, rect, union
from hoarch import features as FT, openings as O, skins as SK, storefront as SF, trimwork as TW
from hoarch.kit import Kit
from hoarch.ornament import ext
from hoarch.shell import Block, Opening, foundation, stacked_shells

NAME = "Bassett Hardware & Feed"
COLORS = {"Stone": "#B8A98A", "Trim": "#DDD3BC", "Iron": "#2A2A2A", "Sign": "#2E4A33", "Roof": "#6B5B4B",
          "Base": "#8F8676", "Windows_Doors": "#6B2E22"}
RENDER_MAT = {"Stone": "stone", "Trim": "trim", "Iron": "iron", "Sign": "sign", "Gilt": "letters", "Roof": "roof",
              "Base": "base", "Windows_Doors": "oxblood", "Sash": "sash", "Door": "door", "Glass": "glass"}

ZF = 5.0
H1 = 42.0
S1 = ZF + H1
RH = 4.4
V2 = H1 + RH                   # upper floor (block-relative)
VF, FR_H = V2 + 38.0, 6.4      # frieze over a 38 mm upper storey
VK = VF + FR_H                 # cornice cap
CAP_K = 1.3
CAP_PROF = [(CAP_K * a, CAP_K * b) for a, b in
            [(0.0, 0.0), (1.4, 0.0), (1.4, 0.8), (2.0, 1.4), (2.6, 2.2), (2.8, 2.8), (3.0, 3.6), (0.0, 3.6)]]
CAP_H = CAP_K * 3.6
VTOP = VK + CAP_H
T = 3.0
W, D = 96.0, 124.0
PANEL = (W / 2 - 12.0, W / 2 + 12.0, 7.0)      # raised date panel on the parapet: u0, u1, height
Y0R = T + 0.15
V_FRONT_ROOF = V2 + 33.6       # the roof's underside at its front end (behind the frieze)
V_REAR = V2 + 17.6             # ... and on the rear wall
S = (V_FRONT_ROOF - V_REAR) / (D - T - Y0R)
HB = V_REAR + T * S
MAIN = Block("main", [(0, 0), (W, 0), (W, D), (0, D)], ZF, ZF + HB)
SIDE_STEPS = [(0.0, 30.0, V2 + 39.0), (30.0, 60.0, V2 + 35.0), (60.0, 90.0, V2 + 31.0), (90.0, D, V2 + 27.0)]
BAYS = [(18.0, 13.2), (78.0, 13.2)]       # 13.2 wide: the round heads spring on the layer grid
BAY_V, BAY_H = 6.0, 30.0
DOOR_X, DOOR_W, DOOR_H = W / 2, 13.2, 26.0
FAN_V = DOOR_H + 1.2
UP_X = (13.0, 32.0, 64.0, 83.0)
UP_W, UP_H = 8.4, 21.0
LOAD_W, LOAD_H = 11.0, 28.0
HOIST_V = V2 + 1.0 + LOAD_H + 2.2


def _siding(f, b, reg):
    tex_reg = reg
    parts = []
    if f.n[1] < -0.3:                      # the street front: voussoir arches and jack arches
        keep = []
        for u, w in BAYS:
            o, r = SK.stone_arch(u, BAY_V, w, BAY_H, w / 2, ring=2.6)
            keep.append(o)
            parts.append(r)
        o, r = SK.stone_arch(DOOR_X, FAN_V, DOOR_W, DOOR_W / 2, DOOR_W / 2, ring=2.6)
        keep.append(o)
        parts.append(r)
        for u in UP_X:
            o, r = SK.jack_arch(u, V2 + 5.0 + UP_H + 0.8, UP_W)          # its top and key on the layer grid
            keep.append(o)
            parts.append(r)
        tex_reg = reg - cs_union(keep)
    parts.append(ashlar(tex_reg, course=(1.0, 1.8), length=(3.0, 8.0), d=0.4, seed=int(abs(f.p0[0] + 3 * f.p0[1])) % 97,
                        rough=0.08))
    return union(parts) ^ M.extrude(reg, 3.0).translate([0, 0, -1.0])


def _openings():
    L = []

    def add(x, y, v0, sp, name, kind="window"):
        e, u = MAIN.locate(x, y)
        L.append(Opening(MAIN, e, u, v0, sp, name, kind))

    for u, w in BAYS:
        add(u, 0, BAY_V, SF.window_commercial(w, BAY_H, rise=w / 2, lites=(3, 3), rows=(3, 3), sill=1.4), f"bay-{u:.0f}")
    add(DOOR_X, 0, 0.0, SF.door_commercial(DOOR_W, DOOR_H, transom=0.0, leaf="boards_glass", tstyle="plain", head=None,
                                           leaves=2), "front-door", "door")
    add(DOOR_X, 0, FAN_V, SF.window_commercial(DOOR_W, DOOR_W / 2, rise=DOOR_W / 2, lites=(3, 3), rows=(1, 1), sill=None),
        "fanlight")
    up = SF.window_commercial(UP_W, UP_H, rise=0, lites=(1, 1), rows=(2, 2), sill=1.0)
    for u in UP_X:
        add(u, 0, V2 + 5.0, up, f"F{u:.0f}-2")
    add(DOOR_X, 0, V2 + 1.0, SF.door_commercial(LOAD_W, LOAD_H, transom=0.0, leaf="ledged", tstyle="plain", head=None,
                                               leaves=2), "loading-door", "door")
    side = SF.window_commercial(8.4, 21.0, rise=0, lites=(1, 1), rows=(2, 2), sill=1.0)
    low = SF.window_commercial(8.4, 12.0, rise=0, lites=(1, 1), rows=(2, 2), sill=1.0)      # under the shed roof
    for y in (30.0, 62.0, 94.0):
        add(W, y, 10.0, side, f"E{y:.0f}-1")
        add(W, y, V2 + 3.0, low, f"E{y:.0f}-2")
    add(W - 22.0, D, 0.0, SF.door_commercial(15.0, 28.0, transom=0.0, leaf="ledged", tstyle="plain", head=None, leaves=2),
        "freight-door", "door")
    for x in (50.0, 76.0):
        add(W - x, D, V2 + 3.0, low, f"N{x:.0f}-2")
    add(W - 60.0, D, 10.0, side, "N60-1")
    return L


OPENINGS = _openings()
SHUTTER_W = 3.2
APPLIED = [("FRIEZE", 0.0, VF, W, FR_H), ("CAP", 0.0, VK, W, CAP_H),
           ("PANEL", PANEL[0], VTOP, PANEL[1] - PANEL[0], PANEL[2]),
           ("HOIST", DOOR_X - 0.8, HOIST_V - 0.8, 1.6, 3.2)] + \
          [(f"SH{k}", u + sg * (UP_W / 2 + 0.6 + 1.1) + (0.0 if sg > 0 else -SHUTTER_W), V2 + 5.0, SHUTTER_W, UP_H)
           for k, (u, sg) in enumerate([(u, s) for u in UP_X for s in (-1, 1)])]


def _applied_openings():
    return [Opening(MAIN, 0, 0.0, 0.0, SF.applied(rect(u0, v0, u0 + L, v0 + h)), name, "trim")
            for name, u0, v0, L, h in APPLIED]


def _roof_plane_cut():
    """Everything above the shed roof's underside, between the side walls (they stand up
    past it as stepped parapets), behind the front wall."""
    sec = poly([(T + 0.001, ZF + V_FRONT_ROOF + (Y0R - T) * S), (D + 10.0, ZF + V_FRONT_ROOF - (D + 10.0 - Y0R) * S),
                (D + 10.0, ZF + 300.0), (T + 0.001, ZF + 300.0)])
    return M.extrude(sec, W - 2 * T).transform(np.array([[0.0, 0, 1.0, T], [1.0, 0, 0, 0], [0, 1.0, 0, 0]]))


def _gilt(solid, A, level, lo):
    top = solid ^ box([-1e3, -1e3, level], [1e3, 1e3, 1e3])
    return [(lo, (solid - top).transform(A)), ("Gilt", top.transform(A))]


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    front = rect(0.0, HB - 0.01, W, VTOP) + rect(PANEL[0], VTOP - 0.01, PANEL[1], VTOP + PANEL[2])
    right = cs_union([rect(a, HB - 0.01, b, top) for a, b, top in SIDE_STEPS])
    left = cs_union([rect(D - b, HB - 0.01, D - a, top) for a, b, top in SIDE_STEPS])
    bprof, _ = TW.BELTS["string"]
    st = stacked_shells([MAIN], OPENINGS + _applied_openings(), [S1], t=T, corners="none", siding=_siding, prof=bprof,
                        belt_blocks=None, water_table=False, gables=[(MAIN, 0, front), (MAIN, 1, right), (MAIN, 3, left)])
    # a ledge on the back of the front wall carries the roof's front end
    zf = ZF + V_FRONT_ROOF
    zl = zf - 1.4 * S - 0.01                           # just under the roof's sloping underside
    ledge = M.hull_points([(x, T - 0.01, zl - 1.4) for x in (T + 0.2, W - T - 0.2)] +
                          [(x, y, zl) for x in (T + 0.2, W - T - 0.2) for y in (T - 0.01, T + 1.2)])
    kit.add("WALLS-1", "Stone", st["shells"][0], group="walls")
    kit.add("BELT", "Trim", st["rings"][0], group="walls")
    kit.add("WALLS-2", "Stone", st["shells"][1] - _roof_plane_cut() + ledge, group="walls")
    kit.add("FOUNDATION", "Base", foundation([MAIN], 0.0, ZF, style="battered", lip=1.2), group="foundation")
    for o in OPENINGS:
        s = o.spec
        b = s["cut"].bounds()
        key = "DOOR" if o.kind == "door" else "WIN"
        world, P, zones = O.place(s, o.local_frame(), "Windows_Doors", "Door" if o.kind == "door" else "Sash", "Glass")
        kit.add(f"{key}-{o.name}", "Windows_Doors", world, P=P, key=f"{key}-{o.name.split('-')[0]}-{b[2] - b[0]:.1f}",
                group="inserts", render=zones)
    print("walls", round(time.time() - t0, 1))

    # --- the front: frieze, cornice, date panel, shutters, hoist
    f = MAIN.facades()[0]

    def frame_at(u0, v0, w0=0.0):
        A_ = f.A.copy()
        A_[:, 3] = f.world(u0, v0, w0)
        return A_

    fr = box([0, 0, 0], [W, FR_H, 1.0]) + ext(rect(0, 0, W, FR_H) - rect(0.9, 0.9, W - 0.9, FR_H - 0.9), 0.99, 1.4) + \
        ext(SF.text_cs("BASSETT HARDWARE", 3.6, "roman", grow=0.1).translate((W / 2, (FR_H - 3.6) / 2)), 0.99, 1.4)
    Af = frame_at(0.0, VF)
    kit.add("FRIEZE", "Sign", fr.transform(Af), P=inv34(Af), group="front", render=_gilt(fr, Af, 1.0, "Sign"))
    cap = SF.cornice_cap(W, CAP_PROF)
    Ac = frame_at(0.0, VK)
    kit.add("CAP", "Trim", cap.transform(Ac), P=inv34(Ac), group="front")
    pw = PANEL[1] - PANEL[0]
    panel = box([0, 0, 0], [pw, PANEL[2], 0.8]) + box([-0.3, PANEL[2] - 0.8, 0.0], [pw + 0.3, PANEL[2], 1.2]) + \
        ext(SF.text_cs("1872", 3.6, "roman", grow=0.1).translate((pw / 2, 1.0)), 0.79, 1.2)
    Ap = frame_at(PANEL[0], VTOP)
    kit.add("PANEL", "Trim", panel.transform(Ap), P=inv34(Ap), group="front")
    sh = SF.iron_shutter(SHUTTER_W, UP_H)
    for k, (name, u0, v0, L_, h_) in enumerate([a for a in APPLIED if a[0].startswith("SH")]):
        A_ = frame_at(u0, v0)
        kit.add(f"SHUTTER-{k}", "Iron", sh.transform(A_), P=inv34(A_), key="SHUTTER", group="front")
    hoist = ext(SF.hoist_cs(11.0, 10.0), 0.0, 1.2)
    Ah = np.array([[0.0, 0.0, -1.0, DOOR_X + 0.6], [-1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, ZF + HOIST_V]])
    kit.add("HOIST", "Iron", hoist.transform(Ah), P=inv34(Ah), group="front")
    print("front", round(time.time() - t0, 1))

    # --- the shingled shed roof between the side parapets
    n = math.sqrt(1 + S * S)
    y1 = D + 2.4
    z1 = ZF + V_FRONT_ROOF - (y1 - Y0R) * S
    Lr = W - 2 * T - 0.3
    Vr = (y1 - Y0R) * n
    pan = SF.shingle_panel(Lr, Vr, t=1.2, pitch=1.8, width=2.0)
    Am = np.array([[-1.0, 0.0, 0.0, W - T - 0.15], [0.0, -1 / n, S / n, y1], [0.0, S / n, 1 / n, z1]])
    kit.add("ROOF", "Roof", pan.transform(Am), P=inv34(Am), group="roof")
    # glue joints: nothing small is left butted on a dab of glue (see NOTES.md)
    FT.key_into(kit, "HOIST", ["WALLS-2"], (0, 1, 0), depth=2.0)
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "hardware")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:40]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "hardware.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))

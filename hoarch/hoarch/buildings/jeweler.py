"""Ashworth & Sons, Jewelers -- an original HO-scale (1:87.1) two-storey terra-cotta shop, 1893.

A narrow shop faced in buff terra cotta: long smooth blocks with bands of button rosettes at
the springing of the arch, under the upper windows and under the frieze, on brick side walls
laid all in headers. The ground floor is one great round arch under a moulded terra-cotta
band with imposts and a keystone carrying an "A": inside it a green shop front with a
display window lettered WATCHES, a door with two round-headed lights, and a fanlight. A
cyma belt divides the floors. Upstairs a canted oriel on a corbel, with a copper roof,
between two narrow 2-over-1 windows under lintels with triple keystones. At the top an
egg-and-dart frieze lettered ASHWORTH & SONS, a cornice, and a dated panel on the parapet.
On the hexagon-paved sidewalk stands a four-faced street clock; a gilt pocket watch hangs
from the right-hand pier. Flat copper roof in lozenge sheets, a round chimney stack.

The front wall is its own part, printed face-up (as the millinery's), so the terra cotta and
its arch band print as relief on top and take their own colour. The oriel prints on its back.
Colour comes from the part split: the frieze, the watch sign and the clock dials each take one
filament change.

usage: python3 -m hoarch.buildings.jeweler [check] [export]
"""
import math
import os
import sys
import time

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import arch_cs, box, cs_union, inv34, offset, poly, rect, slab, union
from hoarch import openings as O, skins as SK, storefront as SF, trimwork as TW
from hoarch.kit import Kit
from hoarch.ornament import ext, stroke
from hoarch.shell import Block, Opening, _corbel, foundation, stacked_shells

NAME = "Ashworth & Sons, Jewelers"
COLORS = {"Terra": "#D09062", "Brick": "#7E3F2E", "Buff": "#E6CFA6", "Oriel": "#23402F", "Sign": "#23402F",
          "Copper": "#5FA08C", "Base": "#8F8B85", "Paving": "#A7A39B", "Iron": "#1E2A24", "Dial": "#F4F1E8",
          "Blade": "#1E1E1E", "Windows_Doors": "#23402F"}
RENDER_MAT = {"Terra": "terra", "Brick": "brick", "Buff": "buff", "Oriel": "green", "Sign": "green", "Gilt": "gilt",
              "Copper": "copper", "Base": "base", "Paving": "paving", "Iron": "iron", "Dial": "dial", "Hands": "iron",
              "Blade": "iron", "Windows_Doors": "green", "Sash": "sash", "Door": "door", "Glass": "glass"}

# ------------------------------------------------------------------ levels (v from the block base)
ZF = 2.8                   # tooled granite base
H1 = 40.0                  # storey joint
S1 = ZF + H1
RH = 4.0                   # the cyma belt
V2 = H1 + RH
VF, FR_H = V2 + 30.4, 6.4  # frieze
VK = VF + FR_H             # cornice cap
CAP_PROF = [(0.0, 0.0), (0.8, 0.0), (0.8, 0.6), (1.4, 1.2), (1.4, 1.8), (2.4, 2.4), (2.4, 3.0), (0.0, 3.0)]
VTOP = VK + 3.0            # top of the front wall
PANEL = (6.0, 5.0)         # the date panel on the parapet: half width, height
HB = VK                    # side and rear walls
T = 3.0
W, D = 34.0, 46.0
MAIN = Block("main", [(0, 0), (W, 0), (W, D), (0, D)], ZF, ZF + HB)
ZR = ZF + HB - 3.2         # roof ledge

# ------------------------------------------------------------------ the front
ARCH_U, ARCH_W, SPRING = W / 2, 22.0, 24.0
ORIEL_U, ORIEL_V = W / 2, V2 + 1.0
NARROW_U = (4.6, W - 4.6)
NARROW_V = V2 + 6.0
BLADE_U = W - 1.2          # the watch sign on the right-hand pier
BLADE_V = 32.0
WALK = 18.6                # sidewalk depth


def _oriel():
    o = SF.oriel(15.0, 3.2, 18.0, head=2.0, lights=(1, 2, 1))
    roof_land = o["roof"].project().offset(0.15)
    return dict(insert=o["solid"], glass=o["glass"], sash=M(), frame=o["solid"] - o["glass"], surround=o["solid"],
                back=0.0, cut=o["cut"], landing=o["landing"] + roof_land, top=o["top"] + 3.8, bottom=0.0), o


ORIEL_SPEC, _ORIEL = _oriel()


def _openings():
    L = []

    def add(x, y, v0, sp, name, kind="window"):
        e, u = MAIN.locate(x, y)
        L.append(Opening(MAIN, e, u, v0, sp, name, kind))

    add(ARCH_U, 0, 0.0, SF.arched_shopfront(ARCH_W, SPRING, door_w=6.4, leaf="twin_arch", bulk=5.0, text="WATCHES",
                                             cap=1.4), "shopfront", "door")
    add(ORIEL_U, 0, ORIEL_V, ORIEL_SPEC, "oriel")
    nw = SF.window_commercial(4.4, 16.0, rise=0, lites=(1, 2), rows=(1, 1), sill=1.0, head="triple")
    for u in NARROW_U:
        add(u, 0, NARROW_V, nw, f"F{u:.0f}-2")
    side = SF.window_commercial(5.4, 14.0, rise=0, lites=(1, 2), rows=(1, 1), sill=1.0, head="triple")
    for y in (16.0, 32.0):
        add(W, y, V2 + 6.0, side, f"E{y:.0f}-2")
    add(W - 9.0, D, 0.0, SF.door_commercial(6.4, 22.0, transom=0.0, leaf="twin_arch", tstyle="plain", head=None),
        "back-door", "door")
    add(W - 25.0, D, 10.0, side, "N25-1")
    for x in (9.0, 25.0):
        add(W - x, D, V2 + 6.0, side, f"N{x:.0f}-2")
    return L


OPENINGS = _openings()
APPLIED = [("FRIEZE", 0.0, VF, W, FR_H), ("CAP", 0.0, VK, W, 3.0), ("BLADE", BLADE_U - 0.8, BLADE_V - 3.4, 1.6, 4.8),
           ("PANEL", W / 2 - PANEL[0] - 0.2, VTOP, 2 * PANEL[0] + 0.4, PANEL[1] + 0.2)]


def _applied_openings():
    return [Opening(MAIN, 0, 0.0, 0.0, SF.applied(rect(u0, v0, u0 + L, v0 + h)), name, "trim")
            for name, u0, v0, L, h in APPLIED]


def _panel_cs():
    hw, ph = PANEL
    return arch_cs(W / 2 - hw, W / 2 + hw, VTOP - 0.01, VTOP + ph - 2.0, rise=2.0, seg=40)


def _siding(f, b, reg):
    if f.n[1] < -0.3:
        # the street front: terra cotta with rosette bands, a moulded band round the arch
        key = SF.text_cs("A", 1.8, "roman", grow=0.1)
        outline, arch = SK.moulded_arch(ARCH_U, 0.0, ARCH_W + 1.2, SPRING, band=2.4, key=key)
        tc = SK.terracotta(reg - outline, course=2.4, block=6.0, d=0.4, datum=0.0, band_every=10)
        return tc + (arch ^ M.extrude(reg.offset(0.5), 3.0).translate([0, 0, -1.0]))
    ud = f.A[:2, 0]
    if abs(ud[1]) > 0.5:                     # brick sides stop where the front wall's ends are
        ucut = (T - f.p0[1]) / ud[1]
        keep = rect(ucut, -100.0, 1e3, 1e3) if ud[1] > 0 else rect(-1e3, -100.0, ucut, 1e3)
        reg = reg ^ keep
    return SK.brick_bond(reg, "header", datum=0.0)


def _gilt(solid, A, level, lo, hi="Gilt"):
    top = solid ^ box([-1e3, -1e3, level], [1e3, 1e3, 1e3])
    return [(lo, (solid - top).transform(A)), (hi, top.transform(A))]


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    base = MAIN.cs
    bprof, _ = TW.BELTS["cyma"]
    front = rect(0.0, HB - 0.01, W, VTOP) + _panel_cs()
    st = stacked_shells([MAIN], OPENINGS + _applied_openings(), [S1], t=T, corners="none", siding=_siding, prof=bprof,
                        belt_blocks=None, water_table=False, gables=[(MAIN, 0, front)])
    fcut = box([-5.0, -5.0, -1.0], [W + 5.0, T, 400.0])
    inner = box([T + 0.01, -5.0, -1.0], [W - T - 0.01, T + 3.0, 400.0])
    ledge = _corbel(base, T, ZR) - fcut - inner
    f = MAIN.facades()[0]
    Af = f.A.copy()
    Af[:, 3] = f.world(0.0, 0.0, 0.0)
    kit.add("FRONT-1", "Terra", st["shells"][0] ^ fcut, P=inv34(Af), group="walls")
    kit.add("FRONT-2", "Terra", st["shells"][1] ^ fcut, P=inv34(Af), group="walls")
    kit.add("WALLS-1", "Brick", st["shells"][0] - fcut - inner, group="walls")
    kit.add("BELT", "Buff", st["rings"][0], group="walls")
    kit.add("WALLS-2", "Brick", st["shells"][1] - fcut - inner + ledge, group="walls")
    print("walls", round(time.time() - t0, 1))

    for o in OPENINGS:
        s = o.spec
        A = o.local_frame()
        if o.name == "oriel":
            kit.add("ORIEL", "Oriel", s["insert"].transform(A), P=inv34(A), group="front",
                    render=[("Oriel", s["frame"].transform(A)), ("Glass", s["glass"].transform(A))])
            Ar = A.copy()
            kit.add("ORIEL-roof", "Copper", _ORIEL["roof"].transform(Ar), P=inv34(Ar), group="front")
            continue
        b = s["cut"].bounds()
        key = "DOOR" if o.kind == "door" else "WIN"
        world, P, zones = O.place(s, A, "Windows_Doors", "Door" if o.kind == "door" else "Sash", "Glass")
        name = "SHOPFRONT" if o.name == "shopfront" else f"{key}-{o.name}"
        kit.add(name, "Windows_Doors", world, P=P, key=f"{key}-{o.name.split('-')[0]}-{b[2] - b[0]:.1f}",
                group="inserts", render=zones)
    kit.add("FOUNDATION", "Base", foundation([MAIN], 0.0, ZF, style="tooled", lip=1.2), group="foundation")

    # --- the front: frieze, cap, date panel, the watch sign
    def frame_at(u0, v0, w0=0.0):
        A_ = f.A.copy()
        A_[:, 3] = f.world(u0, v0, w0)
        return A_

    darts, eggs = SF.egg_dart(W - 1.6, h=2.2, pitch=2.8)
    fr = box([0, 0, 0], [W, FR_H, 1.0]) + ext(darts.translate((0.8, 0.4)), 0.99, 1.4) + \
        ext(eggs.translate((0.8, 0.4)), 0.99, 1.6) + \
        ext(rect(0, 0, W, FR_H) - rect(0.6, 0.6, W - 0.6, FR_H - 0.6), 0.99, 1.4) + \
        ext(SF.text_cs("ASHWORTH & SONS", 2.2, "roman", grow=0.1).translate((W / 2, 3.1)), 0.99, 1.4)
    Afr = frame_at(0.0, VF)
    kit.add("FRIEZE", "Sign", fr.transform(Afr), P=inv34(Afr), group="front", render=_gilt(fr, Afr, 1.0, "Sign"))
    cap = SF.cornice_cap(W, CAP_PROF)
    Ac = frame_at(0.0, VK)
    kit.add("CAP", "Buff", cap.transform(Ac), P=inv34(Ac), group="front")
    pcs = _panel_cs().translate((-W / 2, -VTOP)) ^ rect(-50.0, 0.0, 50.0, 50.0)
    panel = ext(pcs, 0.0, 0.8) + ext(pcs - pcs.offset(-0.7), 0.79, 1.2) + \
        ext(SF.text_cs("1893", 2.2, "roman", grow=0.1).translate((0.0, 0.9)), 0.79, 1.2)
    Ap = frame_at(W / 2, VTOP)
    kit.add("PANEL", "Buff", panel.transform(Ap), P=inv34(Ap), group="front")
    wcs, face = SF.watch_cs(6.4)
    bs = SF.blade_sign(wcs, None, t=1.2, arm=9.0, drop=2.4, face=face, hang=(0.0,))
    Abl = np.array([[0.0, 0.0, -1.0, BLADE_U + 0.8], [-1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, ZF + BLADE_V]])
    kit.add("BLADE", "Blade", bs.transform(Abl), P=inv34(Abl), group="front", render=_gilt(bs, Abl, 0.8, "Blade"))
    print("front", round(time.time() - t0, 1))

    # --- the sidewalk: hexagon paving and a curb, a step up to the door, the street clock
    walk = SF.hex_paving(W, WALK, t=1.2, a=1.2, curb=1.6)
    Aw = np.array([[-1.0, 0.0, 0.0, W], [0.0, -1.0, 0.0, -1.4], [0.0, 0.0, 1.0, 0.0]])       # clear of the base
    du0, du1 = ARCH_U + ARCH_W / 2 - O.CLR - 0.5 - 6.4, ARCH_U + ARCH_W / 2 - O.CLR - 0.5
    step = box([du0 - 0.6, -3.0, 1.19], [du1 + 0.6, -1.4, ZF])
    kit.add("SIDEWALK", "Paving", walk.transform(Aw) + step, group="street")
    clock, seats = SF.street_clock(40.0, head=6.0, r=1.2)
    cx, cy = 5.0, -WALK + 3.0
    kit.add("CLOCK", "Iron", clock.translate([cx, cy, 1.2]), group="street")
    dial = SF.clock_dial(3.0 - 0.7 - 0.15, t=0.6)
    for k, (c, n) in enumerate(seats):
        a = math.atan2(n[1], n[0])
        Rm = np.array([[-math.sin(a), 0.0, math.cos(a)], [math.cos(a), 0.0, math.sin(a)], [0.0, 1.0, 0.0]])
        Ad = np.column_stack([Rm, np.array(c) + np.array([cx, cy, 1.2])])
        kit.add(f"DIAL-{k}", "Dial", dial.transform(Ad), P=inv34(Ad), key="DIAL", group="street",
                render=_gilt(dial, Ad, 0.6, "Dial", "Hands"))
    print("street", round(time.time() - t0, 1))

    # --- the flat copper roof in lozenge sheets, the round chimney, the coping
    inner_cs = offset(base, -T - 0.15)
    deck = slab(inner_cs, ZR, ZR + 1.2)
    bx = inner_cs.bounds()
    lines = []
    for sgn in (-1, 1):
        for c in np.arange(-60.0, 60.0, 5.0):
            lines.append(stroke([(bx[0] - 5, c + sgn * math.tan(math.radians(30)) * (bx[0] - 5)),
                                 (bx[2] + 5, c + sgn * math.tan(math.radians(30)) * (bx[2] + 5))], 0.5, caps=False))
    seams = M.extrude(cs_union(lines) ^ inner_cs.offset(-0.6), 1.0).translate([0, 0, ZR + 1.0])
    cw = 5.0
    cxh, cyh = W - T - 1.2 - cw / 2, D - T - 1.2 - cw / 2
    pocket = box([cxh - cw / 2 - 0.4, cyh - cw / 2 - 0.4, ZR + 0.6], [cxh + cw / 2 + 0.4, cyh + cw / 2 + 0.4, ZR + 2.0])
    kit.add("ROOF", "Copper", deck - seams - pocket, group="roof")
    zc = ZR + 0.6
    ch = TW.chimney("round", w=cw, d=cw, h=round((ZF + HB + 12.0 - zc) / 0.2) * 0.2).translate([cxh, cyh, zc])
    kit.add("CHIMNEY", "Brick", ch, group="roof")
    cop = slab(offset(base, 0.4) - offset(base, -T - 0.3), ZF + HB, ZF + HB + 0.8) - box([-5, -5, 0], [W + 5, T, 400]) - \
        box([T + 0.1, -5, 0], [W - T - 0.1, T + 1.0, 400])
    kit.add("COPING", "Buff", cop, group="roof")
    print("roof", round(time.time() - t0, 1))
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "jeweler")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:40]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "jeweler.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))

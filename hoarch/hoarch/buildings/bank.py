"""The Merchants Bank -- an original HO-scale (1:87.1) two-storey stone corner bank, 1882.

A corner building with two street fronts and a cut corner holding the entrance: banded
rustication on the ground floor, fine ashlar above, a torus belt course between. Tall
round-arched banking-hall windows under stepped archivolts with keystones and imposts;
pedimented windows upstairs. The corner doorway is a temple front: pilasters, an entablature
lettered BANK and a segmental pediment over a pair of grille doors with a ring transom, up
three granite steps. The top is a double cornice (a frieze lettered MERCHANTS BANK / 1882 /
SAVINGS under a modillion cap with dentils, mitred round the corner) and a bottle-baluster
balustrade. Flat roof with a glass skylight over the banking hall and a coped chimney on
the party wall. Polished granite base.

Colour comes from the part split (see storefront.py): the frieze prints with one filament
change for gilt letters.

usage: python3 -m hoarch.buildings.bank [check] [export]
"""
import math
import os
import sys
import time

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import box, inv34, offset, rect, slab, union
from hoarch import openings as O, skins as SK, storefront as SF, trimwork as TW
from hoarch.kit import Kit
from hoarch.ornament import ext
from hoarch.shell import Block, Opening, _corbel, foundation, stacked_shells

NAME = "The Merchants Bank"
COLORS = {"Stone": "#D9CBA8", "Granite": "#7A7A78", "Trim": "#EFE7D2", "Frieze": "#EFE7D2", "Roof": "#4A4A4A",
          "Iron": "#2B2B2B", "Windows_Doors": "#3A3129"}
RENDER_MAT = {"Stone": "stone", "Granite": "granite", "Trim": "trim", "Frieze": "trim", "Gilt": "gilt", "Roof": "roof",
              "Iron": "iron", "Windows_Doors": "bronze", "Sash": "sash", "Door": "door", "Glass": "glass"}

# ------------------------------------------------------------------ levels (v from the block base)
ZF = 5.6                  # polished granite base
H1 = 40.0                 # banking hall
S1 = ZF + H1
RH = 4.4
VF, FR_H = 70.8, 5.2      # frieze
VK = VF + FR_H            # cornice cap
CAP_PROF = [(0.0, 0.0), (1.8, 0.0), (1.8, 0.6), (2.0, 0.6), (2.0, 2.4), (4.4, 2.4), (4.4, 3.2), (4.6, 3.4),
            (4.8, 3.8), (4.8, 4.4), (5.0, 4.8), (0.0, 4.8)]
VTOP = VK + 4.8           # wall top: the balustrade stands on it
BAL_H = 5.6
ZR = ZF + VK - 1.2        # roof ledge
T = 3.0

# ------------------------------------------------------------------ plan
W, D, C = 48.0, 62.0, 11.0
MAIN = Block("main", [(C, 0), (W, 0), (W, D), (0, D), (0, C)], ZF, ZF + VTOP)
BLOCKS = [MAIN]
FRONT, RIGHT, REAR, LEFT, CORNER = 0, 1, 2, 3, 4
STREET = (LEFT, CORNER, FRONT)            # in order round the corner
V_W1, W1, H1W = 7.0, 8.0, 25.0            # ground-floor windows: sill, width, height
V_W2, W2, H2W = S1 - ZF + RH + 4.6, 7.0, 15.0
FRONT_X = (17.5, 29.5, 41.5)
LEFT_Y = (20.0, 33.0, 46.0)


def _siding(f, b, reg):
    lo = reg ^ rect(-1e3, -1e3, 1e3, H1)
    hi = reg - rect(-1e3, -1e3, 1e3, H1)
    out = []
    if not lo.is_empty():
        out.append(SK.banded_rustication(lo, course=2.4, groove=0.6, d=0.4, datum=0.0))
    if not hi.is_empty():
        out.append(SK.brick_bond(hi, "running", bl=6.0, bh=2.4, mortar=0.5, bed=0.4, d=0.25, datum=H1 + RH))
    return union(out)


def _openings():
    L = []

    def add(x, y, v0, sp, name, kind="window"):
        e, u = MAIN.locate(x, y)
        L.append(Opening(MAIN, e, u, v0, sp, name, kind))

    arch = SF.window_commercial(W1, H1W, rise=W1 / 2, lites=(1, 1), rows=(1, 2), sill=1.4, head="archivolt", hood_w=1.0)
    ped = SF.window_commercial(W2, H2W, rise=0, lites=(1, 1), rows=(2, 2), sill=1.0, head="pediment")
    for x in FRONT_X:
        add(x, 0, V_W1, arch, f"F{x:.0f}-1")
        add(x, 0, V_W2, ped, f"F{x:.0f}-2")
    for y in LEFT_Y:
        add(0, y, V_W1, arch, f"L{y:.0f}-1")
        add(0, y, V_W2, ped, f"L{y:.0f}-2")
    add(C / 2, C / 2, 0.0, SF.door_commercial(6.4, 22.0, transom=5.0, leaf="grille", tstyle="ring", head="temple",
                                              text="BANK", leaves=2), "corner-door", "door")
    rear = SF.window_commercial(7.0, 16.0, rise=2.0, lites=(1, 1), rows=(1, 1), sill=1.0)
    add(40.0, D, 0.0, SF.door_commercial(7.0, 21.0, transom=3.6, leaf="grille", tstyle="ring", head=None), "back-door",
        "door")
    add(22.0, D, 10.0, rear, "R22-1")
    for x in (12.0, 36.0):
        add(x, D, V_W2, rear, f"R{x:.0f}-2")
    return L


OPENINGS = _openings()


def _trim_openings():
    out = []
    for e in STREET:
        f = MAIN.facades()[e]
        out.append(Opening(MAIN, e, 0.0, 0.0, SF.applied(rect(0.0, VF, f.L, VTOP)), f"TOP-{e}", "trim"))
    return out


def _corners():
    """(point, mitre direction) at the two convex street corners, keyed by the facade pair."""
    facs = MAIN.facades()
    out = {}
    for a, b in ((LEFT, CORNER), (CORNER, FRONT)):
        P = facs[b].p0
        m = facs[a].u + facs[b].u
        out[(a, b)] = (np.array([P[0], P[1], 0.0]), np.array([m[0], m[1], 0.0]) / np.linalg.norm(m))
    return out


def _mitred(e, local_fn, over=6.0):
    """Build a run of street trim for facade ``e`` with local_fn(u0, u1) (facade frame, u
    from u0 to u1) running ``over`` past each mitred end, place it and trim it to the mitres.
    Returns (world solid, local frame A)."""
    f = MAIN.facades()[e]
    i = STREET.index(e)
    u0 = -over if i > 0 else 0.0
    u1 = f.L + over if i < len(STREET) - 1 else f.L
    A = f.A.copy()
    A[:, 3] = f.world(0.0, 0.0, 0.0)
    m = local_fn(u0, u1).transform(A)
    cs = _corners()
    if i > 0:                                      # mitre at the start
        P, n = cs[(STREET[i - 1], e)]
        m = m.trim_by_plane(list(n), float(n @ P))
    if i < len(STREET) - 1:                        # mitre at the end
        P, n = cs[(e, STREET[i + 1])]
        m = m.trim_by_plane(list(-n), float(-n @ P))
    return m, A


def _gilt(solid, A, level):
    top = solid ^ box([-1e3, -1e3, level], [1e3, 1e3, 1e3])
    return [("Frieze", (solid - top).transform(A)), ("Gilt", top.transform(A))]


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    base = MAIN.cs
    bprof, _ = TW.BELTS["torus"]
    st = stacked_shells(BLOCKS, OPENINGS + _trim_openings(), [S1], t=T, corners="none", siding=_siding, prof=bprof,
                        belt_blocks=None, water_table=False)
    # parapet walls on the party wall and the rear, level with the balustrade's top rail
    zt, zb = ZF + VTOP, ZF + VTOP + BAL_H
    par = box([W - T, T, zt - 0.01], [W, D, zb - 1.0]) + box([T, D - T, zt - 0.01], [W, D, zb - 1.0]) + \
        box([W - T - 0.2, T, zb - 1.01], [W + 0.2, D + 0.2, zb]) + box([T, D - T - 0.2, zb - 1.01], [W + 0.2, D + 0.2, zb])
    kit.add("WALLS-1", "Stone", st["shells"][0], group="walls")
    kit.add("BELT", "Trim", st["rings"][0], group="walls")
    kit.add("WALLS-2", "Stone", st["shells"][1] + _corbel(base, T, ZR) + par, group="walls")
    for o in OPENINGS:
        s = o.spec
        b = s["cut"].bounds()
        key = "DOOR" if o.kind == "door" else "WIN"
        world, P, zones = O.place(s, o.local_frame(), "Windows_Doors", "Door" if o.kind == "door" else "Sash", "Glass")
        kit.add(f"{key}-{o.name}", "Windows_Doors", world, P=P, key=f"{key}-{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}",
                group="inserts", render=zones)
    print("walls + openings", round(time.time() - t0, 1))

    # --- polished granite base and the corner steps
    fnd = foundation(BLOCKS, 0.0, ZF, style="polished", lip=1.2)
    kit.add("FOUNDATION", "Granite", fnd, group="foundation")
    fc = MAIN.facades()[CORNER]
    Ac = fc.A.copy()
    Ac[:, 3] = fc.world(fc.L / 2, 0.0, 0.0)
    steps = union([box([-6.0, -ZF, 1.4], [6.0, -ZF + 1.8 * (k + 1) + (0.2 if k == 2 else 0.0), 1.4 + 2.2 * (3 - k)])
                   for k in range(3)])
    kit.add("STEPS", "Granite", steps.transform(Ac), group="foundation")

    # --- the double cornice round the street fronts, mitred at the corners, and the balustrade
    texts = {FRONT: ("MERCHANTS BANK", 2.2), CORNER: ("1882", 2.2), LEFT: ("SAVINGS", 2.2)}
    for e in STREET:
        f = MAIN.facades()[e]

        def frieze(u0, u1, e=e, f=f):
            b = box([u0, VF, 0.0], [u1, VK, 1.2])
            txt, cap = texts[e]
            t = SF.text_cs(txt, cap, "serif", grow=0.1).translate((f.L / 2, VF + (FR_H - cap) / 2))
            return b + ext(t, 1.19, 1.6)
        fr, A = _mitred(e, frieze)
        Ap = A.copy()
        Ap[:, 3] = A[:, 3] + A[:, 1] * VF
        kit.add(f"FRIEZE-{e}", "Frieze", fr, P=inv34(Ap), group="top",
                render=_gilt(fr.transform(inv34(A)), A, 1.2))

        def cap(u0, u1, f=f):
            m = SF.cornice_cap(u1 - u0, CAP_PROF, dentils=dict(v=0.6, h=1.2, d=1.8, tooth=0.6, gap=0.6)).translate([u0, 0, 0])
            us = np.arange(u0 + 1.6, u1 - 1.0, 3.2)
            m = m + SF.bracket_row(u1 - u0, us, 1.6, 4.2, 1.0, 2.4, style="modillion")
            return m.translate([0, VK, 0])
        cp, A = _mitred(e, cap)
        Ap = A.copy()
        Ap[:, 3] = A[:, 3] + A[:, 1] * VK
        kit.add(f"CORNICE-{e}", "Trim", cp, P=inv34(Ap), group="top")

        i = STREET.index(e)
        inner = {FRONT: [12.5, 24.5], LEFT: [22.5, 35.5]}.get(e, [])
        peds_u = [0.0 if i > 0 else 1.3] + inner + [f.L if i < len(STREET) - 1 else f.L - 1.3]

        def bal(u0, u1, peds_u=peds_u):
            m = SF.balustrade(u1 - u0, h=BAL_H, t=2.6, pedestals=[u1 - pu for pu in peds_u], end=False)
            # (x, y, z) -> (u = u1 - x, v = VTOP + y, w = -0.2 - z): turned to face the street
            return m.transform(np.array([[-1.0, 0, 0, u1], [0, 1.0, 0, VTOP], [0, 0, -1.0, -0.2]]))
        bl, A = _mitred(e, bal, over=4.0)
        Ab = A.copy()
        Ab[:, 3] = A[:, 3] + A[:, 1] * VTOP
        R_up = np.array([[1.0, 0, 0], [0, 0, -1.0], [0, 1.0, 0]])
        kit.add(f"BALUSTRADE-{e}", "Trim", bl, P=R_up @ inv34(Ab), group="top")
    print("cornice", round(time.time() - t0, 1))

    # --- roof: deck on the ledge, a hipped glass skylight over the hall, a coped chimney
    inner = offset(base, -T - 0.15)
    deck = slab(inner, ZR, ZR + 1.2)
    sw, sd = 14.0, 22.0
    sx, sy = W / 2 - sw / 2 + 2.0, 18.0
    sk, glass = SF.skylight(sw, sd, h=5.0)
    zdk = ZR + 1.2
    kit.add("SKYLIGHT", "Iron", sk.translate([sx, sy, zdk - 0.6]), group="roof",
            render=[("Iron", (sk - glass).translate([sx, sy, zdk - 0.6])), ("Glass", glass.translate([sx, sy, zdk - 0.6]))])
    cw, cd = 12.0, 7.0
    cx, cy = W - T - 0.6 - cd / 2, D - 16.0
    pocket = box([cx - cd / 2 - 0.4, cy - cw / 2 - 0.4, zdk - 0.6], [cx + cd / 2 + 0.4, cy + cw / 2 + 0.4, zdk + 1])
    spocket = box([sx - 0.4, sy - 0.4, zdk - 0.6], [sx + sw + 0.4, sy + sd + 0.4, zdk + 1])
    kit.add("ROOF", "Roof", deck - pocket - spocket, group="roof")
    ch = TW.chimney("coped", w=cw, d=cd, h=round((ZF + VTOP + BAL_H + 10.0 - (zdk - 0.6)) / 0.2) * 0.2)
    kit.add("CHIMNEY", "Stone", ch.rotate([0, 0, 90]).translate([cx, cy, zdk - 0.6]), group="roof")
    print("roof", round(time.time() - t0, 1))
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "bank")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:40]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "bank.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))

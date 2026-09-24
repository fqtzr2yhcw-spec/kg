"""The Fowler -- an original HO-scale (1:87.1) octagon house of the 1850s for the lineup.

Two storeys on an octagonal plan with scored-stucco walls (the grout walls of Fowler's
octagons, lined out as stone) and corner boards on a brick foundation, a double belt
course, a two-layer eave (a panelled frieze course under a cornice of pierced fan brackets),
a low red 5V-crimp metal roof, an octagonal shiplap cupola with a ball finial, and a
veranda wrapping five faces on Tuscan columns with Chippendale railings, a scalloped
valance and a diamond skirt. Greek Revival six-over-six windows under peaked caps with
louvered shutters, a sidelighted entrance under an entablature, and banded chimneys.

usage: python3 -m hoarch.buildings.fowler [check] [export]
"""
import math
import os
import sys
import time

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import box, compose, cs_union, inv34, ngon, offset, poly, slab, union
from hoarch import features as FT, openings as O, roof as R, skins as SK, trimwork as TW
from hoarch.kit import Kit, print_flip
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, stacked_shells, wall_shell

NAME = "Fowler Octagon House"
COLORS = {"PorchDeck": "#F2F0EB", "Planks": "#6F5034",       # the planked porch deck: two colours, one change
          "Butter": "#E3CF94", "White": "#F2F0EB", "TinRed": "#7B3A2C", "Forest": "#2F4A3A",
          "Fieldstone": "#8D877C", "Brick": "#8A3B2B", "PorchGray": "#6B706F", "Windows_Doors": "#F2F0EB"}
RENDER_MAT = {"PorchDeck": "trim", "Planks": "planks",
              "Butter": "siding", "White": "trim", "TinRed": "roof", "Forest": "accent", "Fieldstone": "stone",
              "Brick": "brick", "PorchGray": "porchfloor", "Windows_Doors": "trim", "Sash": "sash", "Door": "door",
              "Glass": "glass"}
PALETTE = {"siding": ["#E3CF94", 0.6, 0.0], "trim": ["#F2F0EB", 0.55, 0.0], "roof": ["#7B3A2C", 0.45, 0.15],
           "accent": ["#2F4A3A", 0.5, 0.0], "stone": ["#8D877C", 0.9, 0.0], "brick": ["#8A3B2B", 0.85, 0.0],
           "porchfloor": ["#6B706F", 0.7, 0.0], "sash": ["#2E3B33", 0.45, 0.0], "door": ["#4A2616", 0.45, 0.0]}

# ------------------------------------------------------------------ levels (on the 0.2 mm grid)
ZF = 12.0
S1 = ZF + 38.0
RH = 4.4
ZE = S1 + RH + 34.0
FR_H = 5.6                       # frieze course (lower eave layer)
EAVE = R.EAVE_DEEP
Z_EAVE_TOP = ZE + FR_H + EAVE[-1][1]
V1, V2 = 6.0, S1 + RH + 3.0 - ZF
ROOF_SLOPE, D_EAVE = 0.45, 7.0

# ------------------------------------------------------------------ plan
C = (60.0, 60.0)
APO = 50.0
MAIN = Block("main", ngon(C, APO), ZF, ZE)
BLOCKS = [MAIN]
CUP_APO, CUP_H = 15.0, 20.0
BRK = dict(pitch=9.0, margin=4.2, pair=1.9, t=0.8)
ROOF_TEX = "crimp"


def _mid(k, pts=None):
    P = MAIN.pts if pts is None else pts
    a, b = np.array(P[k]), np.array(P[(k + 1) % len(P)])
    return (a + b) / 2


def _openings():
    L = []
    lo = O.window_greek(9.6, 22.0)                   # six-over-six
    up = O.window_greek(9.0, 19.0)
    front = O.door_greek(12.0, 25.0, side=2.6)
    back = O.door_greek(10.0, 24.0, side=1.8)

    def add(x, y, v0, sp, name, kind="window", shut=True):
        e, u = MAIN.locate(x, y)
        L.append((Opening(MAIN, e, u, v0, sp, name, kind), shut))

    for k in range(8):
        m = _mid(k)
        if k == 0:
            add(m[0], m[1], 0.4, front, "front-door", "door", shut=False)
        elif k == 4:
            add(m[0], m[1], 0.4, back, "back-door", "door", shut=False)
        else:
            add(m[0], m[1], V1, lo, f"F{k}-1")
        add(m[0], m[1], V2, up, f"F{k}-2")
    return L


OPENINGS_S = _openings()
OPENINGS = [o for o, _ in OPENINGS_S]


def _eave_dist(x, y, apo):
    """Distance from (x, y) in to the nearest face of the octagon of apothem ``apo``."""
    best = 1e9
    for k in range(8):
        a = -math.pi / 2 + 2 * math.pi * k / 8
        n = np.array([math.cos(a), math.sin(a)])
        best = min(best, apo - float((np.array([x, y]) - np.array(C)) @ n))
    return best


def _stucco(f, b, reg):
    return SK.scored_stucco(reg, datum=1.8)


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    clear = [lip_keep(MAIN.cs, 3.0, ZF, 1.2)]
    bprof, bblocks = TW.BELTS["double"]
    st = stacked_shells(BLOCKS, OPENINGS, [S1], t=3.0, corners="board", clear=clear, siding=_stucco, prof=bprof,
                        belt_blocks=bblocks)
    kit.add("WALLS-1", "Butter", st["shells"][0], group="walls")
    kit.add("BELT", "White", st["rings"][0], group="walls")
    # the top shell carries a lip for the frieze course (the eave's lower layer)
    kit.add("WALLS-2", "Butter", st["shells"][1] + _corbel(MAIN.cs, 3.0, ZE) + lip_ring(MAIN.cs, 3.0, ZE), group="walls")
    kit.add("FOUNDATION", "Brick", foundation(BLOCKS, 0.0, ZF, style="brick"), group="foundation")
    inserts = []
    for o, shut in OPENINGS_S:
        A = o.local_frame()
        sp = o.spec
        b = sp["cut"].bounds()
        tag = f"{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}"
        key = "DOOR" if o.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, "White", "Door" if o.kind == "door" else "Sash", "Glass")
        inserts.append(kit.add(f"{key}-{o.name}", "Windows_Doors", world, P=P, key=f"{key}-{tag}-{o.v0 > 20}",
                               group="inserts", render=zones))
        if shut:
            w_op, h_op = b[2] - b[0], b[3] - b[1]
            hh = h_op
            # clear of the slab sill, which runs 1.7 past the opening
            left, right = FT.shutters_for(w_op, h_op, casing=1.4, h=hh)
            for side, m in (("L", left), ("R", right)):
                ms = m.translate([0, 0, 0.32]).transform(A)
                kit.add(f"SHUTTER-{o.name}-{side}", "Forest", ms, P=inv34(A), key=f"SHUTTER-{hh:.1f}",
                        group="shutters")
    print("walls + inserts", round(time.time() - t0, 1))

    # --- two-layer eave: an upright frieze course, then the bracketed cornice upside down
    kit.add("EAVE-frieze", "White", R.frieze_ring(MAIN.pts, ZE, h=FR_H, brackets=BRK), group="roof")
    eave = R.bracketed_cornice(MAIN.pts, ZE + FR_H, EAVE,
                               brackets=dict(z_top=5.2, h=5.0, d0=0.9, d=5.6, style="fan", **BRK),
                               dents=dict(z=4.4, h=0.8, d0=0.9, d=0.7))
    kit.add("EAVE-cornice", "White", eave, P=print_flip(), group="roof")
    # --- low octagonal standing-seam roof, flat on top for the cupola, two chimneys
    ze = Z_EAVE_TOP
    run_ = (APO + D_EAVE) - (CUP_APO + 2.0)
    flat = round((ze + ROOF_SLOPE * run_) / 0.2) * 0.2
    roof, tex = R.hip_roof([(MAIN.pts, list(range(8)))], ze, ROOF_SLOPE, D_EAVE, texture=ROOF_TEX, flat_top=flat)
    chims = [(C[0] - 26.0, C[1] + 14.0), (C[0] + 26.0, C[1] + 14.0)]

    def chim_z0(x, y):
        return ze + ROOF_SLOPE * (_eave_dist(x, y, APO + D_EAVE) - 7.5) - 3.0
    pockets = union([box([x - 5.65, y - 5.65, chim_z0(x, y)], [x + 5.65, y + 5.65, flat + 30]) for x, y in chims])
    kit.add("ROOF-main", "TinRed", (roof + tex) - pockets, group="roof")
    for k, (x, y) in enumerate(chims):
        z0 = chim_z0(x, y)
        ch = TW.chimney("banded", w=10.5, d=10.5, h=flat + 12.0 - z0).translate([x, y, z0])
        kit.add(f"CHIMNEY-{k}", "Brick", ch, key="CHIMNEY", group="roof")
    print("roof", round(time.time() - t0, 1))

    # --- octagonal cupola: arched windows on every face, bracketed eave, cap and finial
    cup = Block("cupola", ngon(C, CUP_APO), flat, flat + CUP_H)
    cwin = O.window_greek(5.6, 9.0, lites=(2, 2), rows=(1, 1), A=0.9)
    cup_ops = []
    for k in range(8):
        m = _mid(k, cup.pts)
        e, u = cup.locate(m[0], m[1])
        cup_ops.append(Opening(cup, e, u, 2.6, cwin, f"cupola-{k}"))
    kit.add("CUPOLA-walls", "Butter", wall_shell([cup], cup_ops, t=2.4, belt=None, corners="board", water_table=False,
                                                 siding=lambda f, b, reg: SK.shiplap(reg, datum=0.6)), group="cupola")
    for o in cup_ops:
        A = o.local_frame()
        world, P, zones = O.place(o.spec, A, "White", "Sash", "Glass")
        kit.add(f"WIN-{o.name}", "Windows_Doors", world, P=P, key="WIN-cupola", group="cupola", render=zones)
    cz = flat + CUP_H
    cup_eave = R.bracketed_cornice(cup.pts, cz, R.CORNICE_SMALL,
                                   brackets=dict(z_top=4.6, h=4.2, d0=0.8, d=2.4, t=0.7, pitch=6.0, pair=1.4, margin=2.6,
                                                 style="fan"),
                                   dents=dict(z=3.8, h=0.8, d0=0.8, d=0.7), lip_t=2.4, deck=(6.0, 8.0))
    kit.add("CUPOLA-eave", "White", cup_eave, P=print_flip(), group="cupola")
    croof, ctex = R.hip_roof([(cup.pts, list(range(8)))], cz + 8.0, 0.7, 4.0, texture=ROOF_TEX,
                             tex_kw=dict(seam_pitch=3.6))
    rr = CUP_APO + 4.0
    zseat = round((cz + 8.0 + 0.7 * rr - 1.0) / 0.2) * 0.2
    seat = M.cylinder(1.0, 1.35, 1.35, 32).translate([C[0], C[1], zseat - 0.4])
    kit.add("CUPOLA-roof", "TinRed", (croof + ctex).trim_by_plane([0, 0, -1.0], -zseat) - seat, group="cupola")
    kit.add("CUPOLA-finial", "TinRed", TW.finial("ball", 1.2, 8.0).translate([C[0], C[1], zseat - 0.4]), group="cupola")
    print("cupola", round(time.time() - t0, 1))

    # --- veranda round the three front faces, its ends on the lines of the side faces
    D = 18.0
    V = [np.array(p) for p in MAIN.pts]
    Op = [np.array(p) for p in R.offset_path(MAIN.pts, D)]
    def nrm(k):
        a = -math.pi / 2 + 2 * math.pi * k / 8
        return np.array([math.cos(a), math.sin(a)])
    q7 = V[7] + nrm(7) * D                  # the ends stand square to the diagonal faces
    q2 = V[2] + nrm(1) * D
    T = lambda p: (round(float(p[0]), 4), round(float(p[1]), 4))
    ppoly = [T(q7), T(Op[0]), T(Op[1]), T(q2), T(V[2]), T(V[1]), T(V[0]), T(V[7])]
    c135 = 1.6 * math.tan(math.radians(22.5))
    seq = [(ppoly[7], ppoly[0]), (ppoly[0], ppoly[1]), (ppoly[1], ppoly[2]), (ppoly[2], ppoly[3]), (ppoly[3], ppoly[4])]
    runs = []
    for i, (a, b) in enumerate(seq):
        Lr = float(np.linalg.norm(np.array(b) - np.array(a)))
        posts = {0: [3.2, Lr - 1.6], 1: [1.6, Lr / 2, Lr - c135], 2: [c135, Lr / 2 - 9.5, Lr / 2 + 9.5, Lr - c135],
                 3: [c135, Lr / 2, Lr - 1.6], 4: [1.6, Lr - 3.2]}[i]
        runs.append(dict(a=a, b=b, posts=posts))
    Lf = float(np.linalg.norm(np.array(seq[2][1]) - np.array(seq[2][0])))
    steps_at = [(2, Lf / 2, 15.0)]
    H_floor = ZF - 1.0
    post_h = (S1 - 0.2) - (H_floor + 5.2)
    P = FT.porch_turned(ppoly, runs, H_floor, post_h, steps_at=steps_at,
                        planks=dict(pitch=1.6, border=0.0),
                        joined=True, ledger_off=1.5, post="tuscan", rail="chippendale", arcade="valance",
                        skirt="diamond", pier_tex="brick", roof_edge="cove")
    fkeep = slab(offset(MAIN.cs, 0.8 + 0.55 + 0.15), -1, ZF + 1.3)
    ins_keep = union([box(np.array(p.solid.bounding_box()[:3]) - 0.2, np.array(p.solid.bounding_box()[3:]) + 0.2)
                      for p in inserts if p is not None])
    deck = P["deck"] - fkeep           # planks and frame in one part: wood planks, one filament change
    kit.add("PORCH-deck", "PorchDeck", deck, P=print_flip(), group="porch",
            render=FT.plank_zones(deck, H_floor, "Planks", "PorchDeck"))
    # on the diagonal runs the arcade tabs sit at 45 degrees to the post-top slots: cut each
    # slot to its tab (and keep the railing feet clear of the foundation's stones)
    tabs = union([arc for arc, _ in P["arcades"]])
    fnd = foundation(BLOCKS, 0.0, ZF, style="brick")
    for k, fr in enumerate(sorted(P["frames"], key=lambda m: -m.volume())):
        kit.add(f"PORCH-frame-{k}", "White", fr - tabs - fnd, group="porch")
    for k, (arc, A) in enumerate(P["arcades"]):
        kit.add(f"PORCH-arcade-{k}", "White", arc, P=compose(FT.ARCADE_PRINT, inv34(A)), group="porch")
    bld_keep = MAIN.solid(grow=1.45, dz0=-20, dz1=0)
    proof = P["roof"] - bld_keep - ins_keep
    ptop = proof.bounding_box()[5]
    kit.add("PORCH-roof", "White", proof.trim_by_plane([0, 0, -1.0], -(ptop - 0.8)), P=print_flip(), group="porch")
    kit.add("PORCH-roof-tin", "TinRed", proof.trim_by_plane([0, 0, 1.0], ptop - 0.8), group="porch")
    for k, (sm, A) in enumerate(P["steps"]):
        kit.add(f"PORCH-steps-{k}", "Brick", sm.transform(A) - fkeep, group="porch")
    e, u = MAIN.locate(*_mid(4))
    f = MAIN.facades()[e]
    A = f.A.copy()
    A[:, 3] = f.world(u, -ZF, 1.4)
    kit.add("STOOP-back", "Brick", FT.steps(14.0, ZF - 0.6, 3).transform(A), group="porch")
    print("porch", round(time.time() - t0, 1))
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "fowler")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:40]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "fowler.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))

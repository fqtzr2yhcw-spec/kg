"""The Fowler -- an original HO-scale (1:87.1) octagon house of the 1850s for the lineup. Rev B: the
house-size plan (an octagon 148 mm across the flats, storeys of 42 and 38 mm) and built-up
cornices at every level.

Two storeys on an octagonal plan with scored-stucco walls (the grout walls of Fowler's
octagons, lined out as stone) and corner boards on a brick foundation, a low red 5V-crimp metal
roof, an octagonal shiplap cupola with a ball finial, and a veranda wrapping five faces on
Tuscan columns with Chippendale railings, a scalloped valance and a diamond skirt. Greek
Revival six-over-six windows under peaked caps with louvered shutters, a sidelighted entrance
under an entablature, and banded chimneys.

- Between the storeys a three-part cornice: a green frieze of bead wreaths tied with ribbons,
  a white pellet course and a white ovolo crown.
- At the eave a four-part cornice: a green frieze of spoked paterae, a white dentil course, a
  white soffit on paired pierced fan brackets and a white torus crown.
- Round the cupola: a white frieze of sunk lunettes with beads, a green soffit on fan brackets
  and a white bevel crown.

usage: python3 -m hoarch.buildings.fowler [check] [export]
"""
import math
import os
import sys
import time

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import box, compose, inv34, ngon, offset, rect, slab, union
from hoarch import cornice as CO, features as FT, openings as O, roof as R, skins as SK, trimwork as TW
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

# ------------------------------------------------------------------ cornices (unique to the Fowler)
LEDGE = 1.4
JOINT = dict(pitch=12.0, margin=4.0, layers=[
    dict(kind="frieze", h=4.8, b=1.2, orn="wreaths", role="Forest"),
    dict(kind="course", h=1.6, b=1.4, orn="pellets", role="White"),
    dict(kind="crown", h=2.2, b=1.4, P=3.6, orn="ovolo", role="White")])
EAVE = dict(pitch=12.0, margin=4.2, pair=1.9, layers=[
    dict(kind="frieze", h=5.6, b=1.2, orn="paterae", role="Forest"),
    dict(kind="course", h=1.6, b=1.4, orn="dentil", role="White", tooth=0.9, gap=0.6),
    dict(kind="bed", h=2.2, b=1.4, P=6.6, role="White", brackets=dict(style="fan", t=0.8, reach=0.6)),
    dict(kind="crown", h=2.8, b=1.4, P=7.2, orn="torus", role="White")])
CUPOLA_C = dict(pitch=8.0, margin=2.6, pair=1.4, layers=[
    dict(kind="frieze", h=4.2, b=1.2, orn="lunettes", role="White"),
    dict(kind="bed", h=1.8, b=1.4, P=4.8, role="Forest", brackets=dict(style="fan", t=0.7, reach=0.7)),
    dict(kind="crown", h=2.0, b=1.4, P=5.4, orn="bevel", role="White")])
RJ = round((LEDGE + 0.4 + CO.band_height(JOINT)) / 0.2) * 0.2
HE = CO.band_height(EAVE)

# ------------------------------------------------------------------ levels (on the 0.2 mm grid)
ZF = 14.0
S1 = ZF + 42.0
ZE = S1 + RJ + 38.0
ZW = ZE + HE
FASCIA = 1.8
Z_EAVE = ZW + FASCIA
V1, V2 = 8.0, S1 + RJ + 5.0 - ZF
ROOF_SLOPE, D_EAVE = 0.45, 7.6

# ------------------------------------------------------------------ plan
C = (80.0, 80.0)
APO = 74.0
MAIN = Block("main", ngon(C, APO), ZF, ZW)
BLOCKS = [MAIN]
CUP_APO, CUP_H = 21.0, 26.0
ROOF_TEX = "crimp"


def _mid(k, pts=None):
    P = MAIN.pts if pts is None else pts
    a, b = np.array(P[k]), np.array(P[(k + 1) % len(P)])
    return (a + b) / 2


def _openings():
    L = []
    lo = O.window_greek(9.6, 24.0)                   # six-over-six
    up = O.window_greek(9.0, 21.0)
    front = O.door_greek(13.0, 30.0, side=3.0)
    back = O.door_greek(11.0, 27.0, side=2.0)

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
    """Scored stucco; nothing in the eave's cornice band."""
    return SK.scored_stucco(reg - rect(-1, ZE - b.z0, f.L + 1, 999), datum=1.8)


def add_rings(kit, rings, prefix, group):
    """Each cornice ring as its own part."""
    for r in rings:
        pcs = sorted([p for p in r["solid"].decompose() if p.volume() > 2.0], key=lambda m_: -m_.volume())
        for j, pc in enumerate(pcs):
            nm = f"{prefix}-{r['name']}" + (f"-{j}" if len(pcs) > 1 else "")
            kit.add(nm, r["role"], pc, P=print_flip() if r["flip"] else None, group=group)


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    clear = [lip_keep(MAIN.cs, 3.0, ZF, 1.2)]
    undress = [slab(offset(MAIN.cs, 8.0), ZE - LEDGE - 0.6, ZW + 0.01)]
    st = stacked_shells(BLOCKS, OPENINGS, [S1], t=3.0, corners="board", clear=clear, siding=_stucco,
                        prof=CO.joint_profile(RJ, LEDGE), belt_blocks=None, water_table=False, undress=undress)
    kit.add("WALLS-1", "Butter", st["shells"][0], group="walls")
    kit.add("JOINT", "Butter", st["rings"][0], group="walls")
    lip = _corbel(MAIN.cs, 3.0, ZW) + lip_ring(MAIN.cs, 3.0, ZW)
    kit.add("WALLS-2", "Butter", st["shells"][1] + lip + CO.ledge(MAIN.pts, ZE, LEDGE), group="walls")
    rings, _ = CO.level(st["outlines"][0], S1 + LEDGE + 0.4, JOINT)
    add_rings(kit, rings, "CORNICE-J", "cornice")
    rings, _ = CO.level(MAIN.pts, ZE, EAVE)
    add_rings(kit, rings, "CORNICE-E", "cornice")
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

    # --- low octagonal 5V-crimp roof on the band, flat on top for the cupola, two chimneys
    ze = Z_EAVE
    run_ = (APO + D_EAVE) - (CUP_APO + 3.0)
    flat = round((ze + ROOF_SLOPE * run_) / 0.2) * 0.2
    roof, tex = R.hip_roof([(MAIN.pts, list(range(8)))], ze, ROOF_SLOPE, D_EAVE, texture=ROOF_TEX, flat_top=flat, zlo=ZW)
    CW = 12.0
    chims = [(C[0] - 38.0, C[1] + 20.0), (C[0] + 38.0, C[1] + 20.0)]

    def chim_z0(x, y):
        return round((ze + ROOF_SLOPE * (_eave_dist(x, y, APO + D_EAVE) - CW * 0.72) - 3.0) / 0.2) * 0.2
    pockets = union([box([x - CW / 2 - 0.4, y - CW / 2 - 0.4, chim_z0(x, y)], [x + CW / 2 + 0.4, y + CW / 2 + 0.4, flat + 30])
                     for x, y in chims])
    kit.add("ROOF-main", "TinRed", (roof + tex) - pockets - lip_keep(MAIN.cs, 3.0, ZW), group="roof")
    for k, (x, y) in enumerate(chims):
        z0 = chim_z0(x, y)
        ch = TW.chimney("banded", w=CW, d=CW, h=round((flat + 14.0 - z0) / 0.2) * 0.2).translate([x, y, z0])
        kit.add(f"CHIMNEY-{k}", "Brick", ch, key="CHIMNEY", group="roof")
    print("roof", round(time.time() - t0, 1))

    # --- octagonal cupola: arched windows on every face, its own cornice, a crimp cap and finial
    cze = flat + CUP_H
    czw = cze + CO.band_height(CUPOLA_C)
    cup = Block("cupola", ngon(C, CUP_APO), flat, czw)
    cwin = O.window_greek(7.0, 11.0, lites=(2, 2), rows=(1, 1), A=0.9)
    cup_ops = []
    for k in range(8):
        m = _mid(k, cup.pts)
        e, u = cup.locate(m[0], m[1])
        cup_ops.append(Opening(cup, e, u, 3.6, cwin, f"cupola-{k}"))
    cup_und = [slab(offset(cup.cs, 8.0), cze - LEDGE - 0.6, czw + 0.01)]
    cwalls = wall_shell([cup], cup_ops, t=2.4, belt=None, corners="board", water_table=False, undress=cup_und,
                        siding=lambda f, b, reg: SK.shiplap(reg - rect(-1, cze - b.z0, f.L + 1, 999), datum=0.6))
    clip = _corbel(cup.cs, 2.4, czw) + lip_ring(cup.cs, 2.4, czw)
    kit.add("CUPOLA-walls", "Butter", cwalls + CO.ledge(cup.pts, cze, LEDGE, t=2.4) + clip, group="cupola")
    for o in cup_ops:
        A = o.local_frame()
        world, P, zones = O.place(o.spec, A, "White", "Sash", "Glass")
        kit.add(f"WIN-{o.name}", "Windows_Doors", world, P=P, key="WIN-cupola", group="cupola", render=zones)
    rings, _ = CO.level(cup.pts, cze, CUPOLA_C, t=2.4)
    add_rings(kit, rings, "CORNICE-CUP", "cupola")
    cd = CUPOLA_C["layers"][-1]["P"] + 0.6
    croof, ctex = R.hip_roof([(cup.pts, list(range(8)))], czw + 1.4, 0.7, cd, texture=ROOF_TEX,
                             tex_kw=dict(seam_pitch=3.6), zlo=czw)
    rr = CUP_APO + cd
    zseat = round((czw + 1.4 + 0.7 * rr - 1.0) / 0.2) * 0.2
    seat = M.cylinder(1.0, 1.5, 1.5, 32).translate([C[0], C[1], zseat - 0.4])
    kit.add("CUPOLA-roof", "TinRed", (croof + ctex).trim_by_plane([0, 0, -1.0], -zseat) - seat
            - lip_keep(cup.cs, 2.4, czw), group="cupola")
    kit.add("CUPOLA-finial", "TinRed", TW.finial("ball", 1.4, 9.6).translate([C[0], C[1], zseat - 0.4]), group="cupola")
    print("cupola", round(time.time() - t0, 1))

    # --- veranda round the three front faces, its ends on the lines of the side faces
    D = 24.0
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
        posts = {0: [3.2, Lr - 1.6], 1: [1.6, Lr / 3, 2 * Lr / 3, Lr - c135],
                 2: [c135, Lr / 2 - 12.0, Lr / 2 + 12.0, Lr - c135],
                 3: [c135, Lr / 3, 2 * Lr / 3, Lr - 1.6], 4: [1.6, Lr - 3.2]}[i]
        runs.append(dict(a=a, b=b, posts=posts))
    Lf = float(np.linalg.norm(np.array(seq[2][1]) - np.array(seq[2][0])))
    steps_at = [(2, Lf / 2, 18.0)]
    H_floor = ZF - 1.4
    post_h = S1 - 2.0 - 5.6 - H_floor              # the roof tucks under the joint's ledge
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
    kit.add("STOOP-back", "Brick", FT.steps(17.0, ZF - 0.6, 5).transform(A), group="porch")
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

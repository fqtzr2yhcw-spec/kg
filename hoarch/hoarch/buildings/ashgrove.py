"""The Ashgrove: an original HO-scale (1:87.1) estate gate lodge; house 114, of the new-layouts
batch (hoarch.novel2), after the Lodge Gate of the Biltmore Estate, Asheville, North Carolina
(1895, Richard Morris Hunt).

A house that is also a gateway: a long, low lodge with a great arch through its middle for
the drive, rooms either side and over it. Brick below with long-and-short stone quoins, on a
rock-faced plinth; the upper storey jettied out on the floor joists' ends under a carved
bressumer, half-timbered with pebbledash between the timbers; a steep hipped roof of plain
clay tiles with a cross gable over the arch on both faces, carved bargeboards; two tall
Tudor stacks of twin octagonal shafts. Gate piers with ball finials and brick walls step out
either side of the drive, which runs through on its own gravel strip.

- The passage through the arch is its own part (side walls and barrel vault, ribbed), printed
  upside down so the vault needs nothing under it; the two halves of the ground floor glue
  to it. The arch's stone face is a separate piece on each front. The gates stand open
  against the passage walls.
- Cornices: the jetty (joist ends with carved brackets, a carved vine, the bressumer); the
  eave (pebbledash band, carved brackets, an ovolo).

usage: python3 -m hoarch.buildings.ashgrove [check] [export]
"""
import json
import math
import os
import sys
import time

import numpy as np
from manifold3d import JoinType, Manifold as M

from hoarch.core import Facade, box, cs_union, inv34, offset, poly, rect, slab, union
from hoarch import cornice as CO, gables as G, novel2 as N, openings as O, roof as R
from hoarch.kit import Kit, print_flip
from hoarch.ornament import ext, stroke
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, wall_shell

NAME = "The Ashgrove"
COLORS = {"Brick": "#9A4B36", "Stone": "#CBBFA6", "Timber": "#4A3528", "Stucco": "#D9CCB0", "Tile": "#7E4537",
          "Gravel": "#A79F90", "Windows_Doors": "#CBBFA6"}
RENDER_MAT = {"Brick": "brick", "Stone": "stone", "Timber": "timber", "Stucco": "stucco", "Tile": "roof", "Gravel": "gravel",
              "Windows_Doors": "stone", "Sash": "sash", "Door": "door", "Glass": "glass"}
PALETTE = {"brick": ["#9A4B36", 0.85, 0.0], "stone": ["#CBBFA6", 0.8, 0.0], "timber": ["#4A3528", 0.75, 0.0],
           "stucco": ["#D9CCB0", 0.95, 0.0], "roof": ["#7E4537", 0.8, 0.0], "gravel": ["#A79F90", 0.95, 0.0],
           "sash": ["#3A3A3A", 0.45, 0.2], "door": ["#5C3E2A", 0.6, 0.0]}
VIEWS = {"hero": [-30, 16, 70, 0.92, [0, 0, -10]], "hero_right": [32, 16, 70, 0.92, [0, 0, -10]],
         "front": [0, 6, 85, 0.95, [0, 0, 0]], "rear": [160, 20, 70, 0.92, [0, 0, -10]],
         "arch": [-10, 6, 85, None, [126, 70, 30], 150], "gable": [-20, 12, 85, None, [126, 76, 90], 150]}

LEDGE = 1.4
JOINT = dict(pitch=8.0, margin=2.0, layers=[
    dict(kind="frieze", h=3.4, b=1.2, orn="ashjoist", role="Timber"),
    dict(kind="course", h=1.8, b=1.2, orn="ashvine", role="Stone"),
    dict(kind="crown", h=1.4, b=1.2, P=3.6, orn="bevel", role="Timber")])
EAVE = dict(pitch=8.0, margin=2.5, layers=[
    dict(kind="course", h=1.6, b=1.2, orn="ashvine", role="Stucco"),
    dict(kind="bed", h=2.6, b=1.4, P=4.0, role="Timber", brackets=dict(style="ashbracket", t=1.6, h=2.6)),
    dict(kind="crown", h=1.8, b=1.4, P=4.6, orn="ovolo", role="Timber")])
HJ = CO.band_height(JOINT)
HE = CO.band_height(EAVE)

T, TU = 3.0, 4.4                                   # the brick walls, the jettied storey's
ZF = 6.0
X0, X1, Y0, Y1 = 26.0, 226.0, 84.0, 128.0          # 200 x 44
XC = (X0 + X1) / 2
J = 3.0                                            # the jetty
S1 = ZF + 42.0                                     # the upper storey's floor
ZJ = S1 - HJ                                       # the jetty cornice's foot
ZE = S1 + 24.0
ZW = round((ZE + HE) / 0.2) * 0.2
Z_EAVE = ZW + 1.4
SL, D_EAVE, RAKE = 1.3, 3.0, 3.0
GW = 22.0                                          # the cross gables' half width
AR, AVS = 16.0, ZF + 18.0                          # the arch: radius, springing
AX0, AX1 = XC - AR, XC + AR
LOW = Block("lodge", [(X0, Y0), (X1, Y0), (X1, Y1), (X0, Y1)], ZF, S1)
UP = Block("upper", [(X0 - J, Y0 - J), (X1 + J, Y0 - J), (X1 + J, Y1 + J), (X0 - J, Y1 + J)], S1, ZW)
SLOT = box([AX0 - 3.0, Y0 - 8.0, -1.0], [AX1 + 3.0, Y1 + 8.0, AVS + AR + 1.2])        # the passage liner's room
BLOCKS = [LOW, UP]
V1 = 8.0
UPPER = set()


def _openings():
    L1, L2 = [], []
    fams = {}

    def add(L, blk, x, y, v0, sp, name, kind="window", up=False):
        e, u = blk.locate(x, y)
        L.append(Opening(blk, e, u, v0, sp, name, kind))
        L[-1].fam = fams.setdefault(id(sp), name)
        if up:
            UPPER.add(name)

    lo, up, upe = N.window_ashlower(), N.window_ashupper(), N.window_ashupper(w=12.0)
    VU = S1 + 7.0
    for y, tag in ((Y0, "S"), (Y1, "N")):
        for x in (X0 + 20.0, X0 + 52.0, X1 - 52.0, X1 - 20.0):
            add(L1, LOW, x, y, V1, lo, f"{tag}{x:.0f}-1")
    add(L1, LOW, AX0 - 14.0, Y0, 0.0, N.door_ashgrove(), "lodge-door", "door")
    add(L1, LOW, AX1 + 14.0, Y1, 0.0, N.door_ashgrove(), "back-door", "door")
    for x, tag in ((X0, "W"), (X1, "E")):
        add(L1, LOW, x, (Y0 + Y1) / 2, V1, lo, f"{tag}-1")
    for y, tag in ((Y0 - J, "S"), (Y1 + J, "N")):
        for x in (X0 + 26.0, X0 + 58.0, X1 - 58.0, X1 - 26.0):
            add(L2, UP, x, y, VU - S1, up, f"{tag}{x:.0f}-2", up=True)
        add(L2, UP, XC, y, VU - S1, N.window_ashupper(w=18.0), f"{tag}-over-arch", up=True)
        add(L2, UP, XC, y, ZW + 6.0 - S1, N.window_ashupper(w=10.0, h=7.0), f"{tag}-gable", up=True)
    for x, tag in ((X0 - J, "W"), (X1 + J, "E")):
        add(L2, UP, x, (Y0 + Y1) / 2, VU - S1, upe, f"{tag}-2", up=True)
    return L1, L2


OPEN1, OPEN2 = _openings()
OPENINGS = OPEN1 + OPEN2


def _skin(f, b, reg):
    """Brick with stone quoins below the jetty; half-timbering and pebbledash above (in the
    gables too), clear of the cornices' bands."""
    nq, nt = len(N.QUOINS), len(N.TIMBERS)
    out = _skin_local(f, b, reg)
    # the stone and timber zones for the render, placed as wall_shell places the skin
    for L_, n in ((N.QUOINS, nq), (N.TIMBERS, nt)):
        L_[n:] = [f.place(m_.translate([0, 0, -0.02])) for m_ in L_[n:]]
    return out


def _skin_local(f, b, reg):
    if b is LOW:
        reg = reg - rect(-1, ZJ - LEDGE - 0.6 - b.z0, f.L + 1, S1 - b.z0 + 1)
        if reg.is_empty():
            return M()
        return N.brick_ashgrove(reg, datum=0.0, L=f.L)
    reg = reg - rect(-1, ZE - LEDGE - 0.6 - b.z0, f.L + 1, ZW - b.z0 + 0.2)
    if reg.is_empty():
        return M()
    cut = rect(-50.0, -50.0, f.L + 50.0, ZW - b.z0)
    lo, hi = reg ^ cut, reg - cut
    out = []
    if not lo.is_empty():
        out.append(N.timber_ashgrove(lo, datum=0.0, L=f.L, seed=int(f.L) % 13))
    if not hi.is_empty():
        out.append(N.timber_ashgrove(hi, datum=ZW - b.z0, gable=True, seed=int(f.L) % 11))
    return union(out)


def _place_inserts(kit, ops, keep, group="inserts"):
    for o in ops:
        A = o.local_frame()
        sp = o.spec
        b = sp["cut"].bounds()
        key = "DOOR" if o.kind == "door" else "WIN"
        frame = "Timber" if o.name in UPPER else "Windows_Doors"
        world, P, zones = O.place(sp, A, frame, "Door" if o.kind == "door" else "Sash", "Glass")
        part = kit.add(f"{key}-{o.name}", frame, world, P=P, key=f"{key}-{o.fam}-{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}",
                       group=group, render=zones)
        keep.append(part.solid)


def _m44(A):
    return np.vstack([A, [0, 0, 0, 1.0]])


def _gable_cs(wl, fascia):
    return wl["cs"] + rect(0.0, -fascia - 0.4, wl["L"], -fascia + 0.01)


def _pocket(roof, env, cx, cy, hx, hy, zl, ztop, rise=10.0):
    z0c = round((zl - 2.4) / 0.2) * 0.2
    roof = roof + G.pocket_seat(env, cx, cy, hx + 0.35, hy + 0.35, z0c) - box([cx - hx - 0.35, cy - hy - 0.35, z0c], [cx + hx + 0.35, cy + hy + 0.35, z0c + 200])
    ch = N.chimney_ashgrove(w=2 * hx - 0.6, d=2 * hy - 0.6, h=round((ztop + rise - z0c) / 0.2) * 0.2).translate([cx, cy, z0c])
    return roof, ch


def _hip_roll(pa, pb, s, half=1.3, up=0.8):
    """A bonnet roll down a hip, pa -> pb ((x, y, z) on the roof's surface, the hip at 45
    degrees in plan between two slopes s): it covers the hip's joint like ridge_cap."""
    pa, pb = np.array(pa, float), np.array(pb, float)
    d = (pb[:2] - pa[:2]) / np.linalg.norm(pb[:2] - pa[:2])
    n = np.array([-d[1], d[0]])
    drop = s / math.sqrt(2.0)
    pts = []
    for p in (pa, pb):
        for sg in (-1, 1):
            q = p[:2] + sg * n * half
            pts += [(q[0], q[1], p[2] - drop * half - 0.6), (q[0], q[1], p[2] - drop * half + 0.5)]
            q = p[:2] + sg * n * 0.4
            pts.append((q[0], q[1], p[2] + up))
    return M.hull_points(pts)


def _passage():
    """The passage liner: two side walls and a ribbed barrel vault from front to back (flush
    with both faces), a flat top; printed upside down."""
    outer = box([AX0 - 3.0, Y0, 0.0], [AX1 + 3.0, Y1, AVS + AR + 1.2])
    void = box([AX0, Y0 - 1, -1.0], [AX1, Y1 + 1, AVS]) + M.cylinder(Y1 - Y0 + 2, AR, AR, 64).rotate([-90, 0, 0]).translate([XC, Y0 - 1, AVS])
    liner = outer - void
    for y in np.arange(Y0 + 5.0, Y1 - 3.0, 8.5):
        rib = (M.cylinder(1.2, AR, AR, 64) - M.cylinder(4.0, AR - 0.8, AR - 0.8, 64).translate([0, 0, -1])).rotate([-90, 0, 0]).translate([XC, y, AVS])
        rib = rib ^ box([AX0 - 1, y - 1, AVS - 0.01], [AX1 + 1, y + 2, AVS + AR + 1])
        liner = liner + rib
        if Y0 + 14.0 < y < Y1 - 15.0:                             # (clear of the gates folded back)
            liner = liner + box([AX0, y, 0.0], [AX0 + 0.8, y + 1.2, AVS + 0.01]) + box([AX1 - 0.8, y, 0.0], [AX1, y + 1.2, AVS + 0.01])
    return liner


def _gate(L=13.0, h=22.0, t=1.0):
    """A gate leaf (u along, v up, back on w = 0; printed on its back): boards in a framed
    leaf, a cross rail, a brace, long strap hinges, its top cut in a shallow curve."""
    from hoarch.colonial import _strap
    top = [(u, h - 1.6 + 1.6 * math.sin(math.pi * u / L)) for u in np.linspace(0.0, L, 12)]
    leaf = poly([(0.0, 0.0), (L, 0.0)] + top[::-1])
    out = ext(leaf, 0.0, t) - ext(cs_union([rect(u - 0.1, -1, u + 0.1, h + 2) for u in np.arange(1.6, L - 0.4, 1.6)]), t - 0.3, t + 1)
    fr = (leaf - leaf.offset(-1.0, JoinType.Miter, 4.0)) + rect(0.0, h * 0.45 - 0.5, L, h * 0.45 + 0.5)
    fr = fr + (stroke([(1.0, 1.0), (L - 1.0, h * 0.45 - 0.5)], 0.9) ^ leaf)
    out = out + ext(fr, t - 0.01, t + 0.45)
    for v in (2.4, h - 4.0):
        out = out + ext(_strap(0.4, L * 0.75, v) ^ leaf, t + 0.44, t + 0.65)
    return out


def _pier(seed=0, w=8.0, h=28.0):
    """A gate pier (stands on z = 0): rock-faced granite, a moulded cap, a ball finial (its
    under side a 45 degree cone)."""
    body = box([-w / 2, -w / 2, 0.0], [w / 2, w / 2, h])
    corners = [(w / 2, -w / 2), (w / 2, w / 2), (-w / 2, w / 2), (-w / 2, -w / 2)]
    for k in range(4):
        f = Facade(corners[k], corners[(k + 1) % 4], 0.0)
        body = body + f.place(N.foundation_ashplinth(rect(0.0, 0.4, w, h - 0.4), seed=seed + k).translate([0, 0, -0.05]))
    body = body + M.hull_points([(sx * (w / 2 + 0.3), sy * (w / 2 + 0.3), h) for sx in (-1, 1) for sy in (-1, 1)] +
                                [(sx * (w / 2 + 1.2), sy * (w / 2 + 1.2), h + 0.9) for sx in (-1, 1) for sy in (-1, 1)])
    body = body + box([-w / 2 - 1.2, -w / 2 - 1.2, h + 0.89], [w / 2 + 1.2, w / 2 + 1.2, h + 2.0])
    body = body + box([-2.2, -2.2, h + 1.99], [2.2, 2.2, h + 3.0])
    rb = 3.0
    zc = h + 3.0 + rb
    ball = M.sphere(rb, 32).translate([0, 0, zc]) ^ box([-9, -9, zc - rb * 0.7], [9, 9, zc + rb + 1])
    cone = M.cylinder(0.3 * rb + 0.02, 1.4, 0.714 * rb, 32).translate([0, 0, h + 2.99])        # (45 degrees or steeper)
    return body + ball + cone


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    N.TIMBERS.clear()
    N.QUOINS.clear()
    t0 = time.time()
    keep = []

    # --- the arch's stone faces (the walls keep their dressing off them)
    A_f = np.array([[1.0, 0, 0, XC], [0, 0, -1.0, Y0], [0, 1.0, 0, 0.0]])
    A_b = np.array([[-1.0, 0, 0, XC], [0, 0, 1.0, Y1], [0, 1.0, 0, 0.0]])
    arch = N.arch_ashgrove(r=AR, vs=AVS)
    arch_f, arch_b = arch.transform(A_f), arch.transform(A_b)
    acs = arch.project().offset(0.3, JoinType.Miter, 4.0)                # (the arch's own outline: brick right up to it)
    arch_und = union([ext(acs, -1.0, 3.0).transform(A) for A in (A_f, A_b)])

    # --- the ground floor: brick on a plinth, the passage's room cut through it (two halves)
    jband = slab(offset(LOW.cs, 10.0), ZJ - LEDGE - 0.6, S1 + 0.01)
    sh1 = wall_shell([LOW], OPEN1, t=T, belt=None, corners="none", water_table=False, siding=_skin, undress=[jband, arch_und])
    arch_env = union([M.hull(a_) for a_ in (arch_f, arch_b)])
    w1 = (sh1 - lip_keep(LOW.cs, T, ZF, 1.2)) + (CO.ledge(LOW.pts, ZJ, LEDGE, t=T) - arch_env)
    w1 = w1 - SLOT
    w1 = max(w1.decompose(), key=lambda m_: m_.volume())       # (one piece: the walls over the passage join the halves)
    quo = union(N.QUOINS)
    kit.add("WALLS-1", "Brick", w1, group="walls", render=[("Brick", w1 - quo), ("Stone", w1 ^ quo)])
    jr, _ = CO.level(LOW.pts, ZJ, JOINT, t=T, cut=SLOT + arch_env)
    CO.add_level(kit, jr, "CORNICE-J", "cornice")
    _place_inserts(kit, OPEN1, keep)
    kit.add("PASSAGE", "Stone", _passage(), P=print_flip(), group="walls")
    for nm, a_, A in (("ARCH-S", arch_f, A_f), ("ARCH-N", arch_b, A_b)):
        kit.add(nm, "Stone", a_, P=inv34(A), key="ARCH-ashgrove", group="walls")
    # the gates, open, standing back against the passage's walls (hung clear of the drive)
    for k, (x0, wd) in enumerate(((AX0, 1.0), (AX1, -1.0))):
        for j, (y0, ud) in enumerate(((Y0 + 2.0, 1.0), (Y1 - 2.0, -1.0))):
            u = np.array([0.0, ud, 0.0])
            w = np.array([wd, 0.0, 0.0])
            g_ = _gate(L=11.0)
            if np.dot(u, np.cross([0.0, 0.0, 1.0], w)) < 0:
                g_ = g_.mirror([1.0, 0, 0])
                u = -u
            Ag = np.array([[u[0], 0, w[0], x0], [u[1], 0, w[1], y0], [0, 1.0, 0, 1.0]])
            kit.add(f"GATE-{k}{j}", "Timber", g_.transform(Ag), P=inv34(Ag), key="GATE-ashgrove", group="inserts")
    print("ground floor", round(time.time() - t0, 1))

    # --- the roof (a hip with a cross gable on each face over the arch), then the jettied
    # storey with the cross gables' walls
    cross = [(XC - GW, Y0 - J), (XC + GW, Y0 - J), (XC + GW, Y1 + J), (XC - GW, Y1 + J)]
    rf = G.gabled_roof([(list(UP.pts), [0, 1, 2, 3], SL), (cross, [1, 3], SL)], Z_EAVE, D_EAVE,
                       [dict(p0=(XC - GW, Y0 - J), p1=(XC + GW, Y0 - J), slope=SL, e=D_EAVE),
                        dict(p0=(XC + GW, Y1 + J), p1=(XC - GW, Y1 + J), slope=SL, e=D_EAVE)],
                       texture="ashtile", tex_kw=dict(pitch=1.2, d=0.4), skin=1.6, rake=RAKE - 0.05, t=TU,
                       inner_cs=offset(UP.cs, -TU), fascia=1.4, hollow=2.6)
    where = [(0, (XC - GW) - (X0 - J)), (2, (X1 + J) - (XC + GW))]
    gu = [(UP, e, _gable_cs(wl, 1.4).translate((u0, Z_EAVE - S1))) for (e, u0), wl in zip(where, rf["walls"])]
    band = slab(offset(UP.cs, 10.0), ZE - LEDGE - 0.6, ZW + 0.01)
    sh2 = wall_shell([UP], OPEN2, t=TU, belt=None, corners="none", water_table=False, siding=_skin, gables=gu, undress=[band])
    lip = _corbel(UP.cs, TU, ZW) + lip_ring(UP.cs, TU, ZW)
    w2 = sh2 + lip + CO.ledge(UP.pts, ZE, LEDGE, t=TU)
    tim = union(N.TIMBERS)
    kit.add("WALLS-2", "Stucco", w2, group="walls", render=[("Stucco", w2 - tim), ("Timber", w2 ^ tim)])
    er, _ = CO.level(UP.pts, ZE, EAVE, t=TU)
    CO.add_level(kit, er, "CORNICE-E", "cornice")
    _place_inserts(kit, OPEN2, keep)
    roof = rf["body"] + rf["tex"] + rf["skins"] + rf["skin_tex"]
    roof = roof - lip_keep(UP.cs, TU, ZW)
    # the ridge tiles: half-round rolls on the ridges, bonnets down the hips
    xa, xb, ya, yb = X0 - J - D_EAVE, X1 + J + D_EAVE, Y0 - J - D_EAVE, Y1 + J + D_EAVE
    hd = (yb - ya) / 2
    zr, zc = Z_EAVE + SL * hd, Z_EAVE + SL * (GW + D_EAVE)
    caps = [G.ridge_cap((xa + hd, ya + hd), (xb - hd, ya + hd), zr, SL, ZW),
            G.ridge_cap((XC, ya + 0.05), (XC, ya + GW + D_EAVE + 1.0), zc, SL, ZW),
            G.ridge_cap((XC, yb - 0.05), (XC, yb - GW - D_EAVE - 1.0), zc, SL, ZW)]
    t0_ = 2.5                                                     # (the bonnets stop short of the eave's corner)
    for (cx_, cy_, rx_) in ((xa, ya, xa + hd), (xb, ya, xb - hd), (xb, yb, xb - hd), (xa, yb, xa + hd)):
        d_ = np.array([rx_ - cx_, (ya + hd) - cy_])
        d_ = d_ / np.linalg.norm(d_)
        pa_ = (cx_ + d_[0] * t0_, cy_ + d_[1] * t0_, Z_EAVE + SL * t0_ / math.sqrt(2.0))
        caps.append(_hip_roll(pa_, (rx_, ya + hd, zr), SL))
    roof = roof + (union(caps) - w2)                           # (clear of the cross gables' apexes)
    env, _ = R.hip_roof([(list(UP.pts), [0, 1, 2, 3], SL)], Z_EAVE, SL, D_EAVE, texture=None, zlo=ZW)
    hx, hy = 6.0, 3.5
    chims = []
    zr = Z_EAVE + SL * ((Y1 - Y0) / 2 + J + D_EAVE)
    for cx in (X0 + 30.0, X1 - 30.0):
        cy = Y1 - 12.0
        zl = Z_EAVE + SL * ((Y1 + J + D_EAVE) - (cy + hy))
        roof, ch = _pocket(roof, env, cx, cy, hx, hy, zl, zr)
        chims.append(ch)
    kit.add("ROOF", "Tile", max(roof.decompose(), key=lambda m_: m_.volume()), group="roof")
    for k, ch in enumerate(chims):
        kit.add(f"CHIMNEY-{k}", "Brick", ch, key="CHIMNEY-ashgrove", group="roof")
    # the cross gables' carved bargeboards
    for k, wl in enumerate(rf["walls"]):
        fw = wl["facade"]
        Lb = wl["L"] + 2 * D_EAVE
        A = fw.A.copy()
        A[:, 3] = fw.world(-D_EAVE, 0.0, 1.0)
        A[2, 3] = Z_EAVE - 1.6
        bg = N.barge_ashgrove(Lb, SL, D_EAVE).transform(A) - roof - union([r["solid"] for r in er])
        bg = max(bg.decompose(), key=lambda m_: m_.volume())
        kit.add(f"BARGE-{k}", "Timber", bg, P=inv34(A), key="BARGE-ashgrove", group="roof")
    print("upper storey and roof", round(time.time() - t0, 1))

    # --- the plinth, the drive, the gate piers and walls
    house_keep = union(keep)
    fnd = foundation([LOW], 0.0, ZF, style="ashplinth") - SLOT - house_keep - arch_f - arch_b
    for k, pc in enumerate(sorted(fnd.decompose(), key=lambda m_: m_.bounding_box()[0])):
        if pc.volume() > 20.0:
            kit.add(f"BASE-{'WE'[k]}", "Stone", pc, group="foundation")
    rng = np.random.default_rng(8)
    drive = box([AX0 + 1.0, 26.0, 0.0], [AX1 - 1.0, 146.0, 0.8])
    drive = drive - union([box([x - 1.2, 25.0, 0.55], [x + 1.2, 147.0, 2.0]) for x in (XC - 8.0, XC + 8.0)])
    peb = [M.sphere(0.32, 8).scale([1.0, 1.0, 0.6]).translate([rng.uniform(AX0 + 0.8, AX1 - 0.8), rng.uniform(26.5, 145.5), 0.8]) for _ in range(500)]
    drive = drive + (union(peb) ^ box([AX0 + 1.0, 26.0, 0.0], [AX1 - 1.0, 146.0, 2.0]))
    kit.add("DRIVE", "Gravel", drive, group="foundation")
    for k, x in enumerate((AX0 - 7.0, AX1 + 7.0)):
        kit.add(f"PIER-{k}", "Stone", _pier(seed=k).translate([x, 42.0, 0.0]), key="PIER-ashgrove", group="stoop")
    for k, (xa, xb) in enumerate(((10.0, AX0 - 11.8), (AX1 + 11.8, 242.0))):
        f = Facade((xa, 40.0), (xb, 40.0), 0.0)
        wall = box([xa, 40.0, 0.0], [xb, 44.0, 14.0])
        wall = wall + f.place(N.brick_ashgrove(rect(0.0, 0.0, xb - xa, 14.0), datum=0.0).translate([0, 0, -0.04]))
        f2 = Facade((xb, 44.0), (xa, 44.0), 0.0)
        wall = wall + f2.place(N.brick_ashgrove(rect(0.0, 0.0, xb - xa, 14.0), datum=0.0).translate([0, 0, -0.04]))
        wall = wall + M.hull_points([(x, y, z) for x in (xa, xb) for (y, z) in ((39.4, 14.0), (44.6, 14.0), (39.4, 14.8), (44.6, 14.8))] +
                                    [(x, 42.0, 16.0) for x in (xa, xb)])
        kit.add(f"WALL-{k}", "Brick", wall, group="stoop", render=[("Brick", wall ^ box([0, 0, -1], [300, 300, 13.99])),
                                                                   ("Stone", wall - box([0, 0, -1], [300, 300, 13.99]))])
    print("specks dropped:", kit.drop_specks())
    print("done", round(time.time() - t0, 1))
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "ashgrove")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    json.dump({"materials": PALETTE, "views": VIEWS}, open(os.path.join(OUT, "palette.json"), "w"), indent=1)
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:80]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "ashgrove.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors", "Timber"))

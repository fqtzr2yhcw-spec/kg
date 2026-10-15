"""The new-layouts batch, houses 103 on (after hoarch.novel, which holds 101-102). Each house
starts from a real building's plan and massing (hoarch/massing has the reviewed volume
studies). This module holds each house's own pieces (wall skins, foundations, cornice
ornaments and brackets, windows, doors, porch styles, and the parts its layout needs that no
earlier house had) and registers its ornaments on import. Nothing in one house's section is
shared with another building.
"""
import math

import numpy as np
from manifold3d import JoinType, Manifold as M

from .core import RIB, ashlar, box, circle, cs_union, ngon, poly, rect, union
from .ornament import chamfer_box, ext, stroke
from . import cornice as CO, features as FT, openings as O, porchwork as PW, trimwork as TW
from .colonial import _st
from .colonial4 import _glazed, _muntins
from .gables import _text, _tie

MIT = JoinType.Miter
RND = JoinType.Round


def _clean(cs, r=0.27):
    """Close slots and drop bars narrower than 2 r (a nozzle), keeping the outline otherwise."""
    cs = cs.offset(r, RND).offset(-r, RND)
    return cs.offset(-r, RND).offset(r, RND)


# ================================================================== the Marisol (house 103)
# After Point Fermin Light (San Pedro, California, 1874) and its Stick Style sisters drawn by
# Paul J. Pelz for the Lighthouse Board: a two-storey keeper's house with cross gables on all
# four sides, and the light's square tower rising out of the crossing of the roofs through
# two stages to a bracketed gallery and a glazed iron lantern. The Stick Style shows its frame
# on the outside: boards laid over drop siding mark the posts, sills and plates; trusses fill
# the gables; braces carry the hoods, the eaves and the veranda.

def drop_marisol(region, datum=0.0, pitch=1.3, groove=0.5, d=0.35, sticks_u=(), bands_v=(), stick=1.3, sd=0.8):
    """The Marisol's walls: drop siding (each board with a groove along its foot), with the
    Stick Style's boards laid over it: verticals at ``sticks_u`` (corner posts, studs between
    the windows) and bands at ``bands_v`` (the sill and head lines of each storey)."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    boards = []
    k0 = math.floor((v0 - datum) / pitch) - 1
    k1 = math.ceil((v1 - datum) / pitch) + 1
    for k in range(k0, k1):
        vb = datum + k * pitch
        boards.append(rect(u0 - 1, vb + groove, u1 + 1, vb + pitch))
    out = [_st(cs_union(boards) ^ region, 0.0, d), M.extrude(region, 0.05)]
    sticks = [rect(u - stick / 2, v0 - 1, u + stick / 2, v1 + 1) for u in sticks_u if u0 - stick < u < u1 + stick]
    sticks += [rect(u0 - 1, v - stick / 2, u1 + 1, v + stick / 2) for v in bands_v if v0 - stick < v < v1 + stick]
    if sticks:
        out.append(_st(cs_union(sticks) ^ region, 0.0, sd))
    return union(out)


def foundation_mrbasalt(reg, seed=0):
    """The Marisol's base: low courses of dark rough basalt (the bluff it stands on) under a
    plain chamfered water table."""
    u0, v0, u1, v1 = reg.bounds()
    stone = ashlar(rect(u0, v0, u1, v1 - 1.2), course=(1.6, 2.4), length=(2.4, 5.4), d=0.55, seed=seed + 11,
                   rough=0.3, bevel=0.3)
    cap = chamfer_box(u0, v1 - 1.2, u1, v1, 0.0, 0.6, c=0.35, square=("u0", "u1"), bottom=0.6)
    return stone + cap


TW.FOUNDATION_EXTRA.update(mrbasalt=foundation_mrbasalt)


# ---- cornice ornaments
def frieze_mrsticks(L, h, b, pitch, margin, pair, half):
    """The storey joint's frieze: the Stick Style frame in small, a rail top and bottom, a post
    at every bracket station and a St Andrew's cross braced into every bay."""
    v0, v1 = 0.5, h - 0.5
    out = [_st(rect(0.3, v0, L - 0.3, v0 + 0.7) + rect(0.3, v1 - 0.7, L - 0.3, v1), b, 0.35)]
    posts = [rect(u - 0.45, v0, u + 0.45, v1) for u in CO._us(L, pitch, margin, 0.0)]
    xs = []
    for uc, wd in CO._between(L, pitch, margin, pair, half):
        a, c_ = uc - wd / 2 + 0.6, uc + wd / 2 - 0.6
        if c_ - a < 2.0:
            continue
        xs.append(stroke([(a, v0 + 0.5), (c_, v1 - 0.5)], 0.55))
        xs.append(stroke([(a, v1 - 0.5), (c_, v0 + 0.5)], 0.55))
    if posts:
        out.append(_st(cs_union(posts), b, 0.45))
    if xs:
        out.append(_st(_clean(cs_union(xs)) ^ rect(0.3, v0, L - 0.3, v1), b, 0.3))
    return out, []


def course_mrrope(L, h, b, pitch, margin, p):
    """A ship's rope laid along the course: twisted strands slanting one way, on a round rod."""
    rod = rect(0.2, 0.25, L - 0.2, h - 0.25)
    out = [_st(rod, b, 0.18)]
    pu = 1.05
    n = max(1, int((L - 0.6) / pu))
    u0 = (L - n * pu) / 2
    strands = []
    for k in range(n + 1):
        uc = u0 + pu * k
        strands.append(stroke([(uc - h * 0.32, 0.3), (uc + h * 0.32, h - 0.3)], 0.5))
    out.append(_st(_clean(cs_union(strands)) ^ rod, b + 0.18, 0.3))
    return out


def frieze_mrportholes(L, h, b, pitch, margin, pair, half):
    """The eave's frieze: a round port in every bay, a ring with a boss at its hub and four
    bolt heads round it, between two plain fillets."""
    v0, v1 = 0.4, h - 0.4
    vm = (v0 + v1) / 2
    r = min((v1 - v0) / 2 - 0.1, 1.7)
    out = [_st(rect(0.3, v0, L - 0.3, v0 + 0.5) + rect(0.3, v1 - 0.5, L - 0.3, v1), b, 0.3)]
    for uc, wd in CO._between(L, pitch, margin, pair, half):
        if wd < 2 * r + 0.8:
            continue
        out.append(_st(circle((uc, vm), r, 28) - circle((uc, vm), r - 0.6, 28), b, 0.4))
        out.append(_st(circle((uc, vm), 0.55, 14), b, 0.45))
        if wd > 2 * r + 3.0:
            for sg in (-1, 1):
                out.append(_st(circle((uc + sg * (r + 0.9), vm), 0.36, 10), b, 0.3))
    return out, []


def frieze_mrlozenge(L, h, b, pitch, margin, pair, half):
    """The tower's frieze: a chain of lozenges linked point to point, a bead in each."""
    v0, v1 = 0.4, h - 0.4
    vm = (v0 + v1) / 2
    hh = (v1 - v0) / 2
    lw = 2.6
    n = max(1, int((L - 0.8) / lw))
    u0 = (L - n * lw) / 2
    loz = []
    for k in range(n):
        uc = u0 + lw * (k + 0.5)
        o = poly([(uc - lw / 2, vm), (uc, vm - hh), (uc + lw / 2, vm), (uc, vm + hh)])
        loz.append(o - o.offset(-0.5, MIT, 4.0))
        loz.append(circle((uc, vm), 0.35, 10))
    out = [_st(_clean(cs_union(loz)) ^ rect(0.2, v0, L - 0.2, v1), b, 0.35)]
    return out, []


def bracket_mrbrace(h, d, t):
    """A Stick Style eave brace (side profile): a post down the wall ending in a knob, the arm
    under the soffit, and the diagonal strut between them, the triangle filled solid (no hole
    through a bracket) with the strut standing proud of it as a step."""
    post = rect(0.0, -h, 1.0, 0.0)
    arm = rect(0.0, -1.0, d, 0.0)
    web = poly([(0.0, -1.0), (d - 0.3, -1.0), (1.0, -h + 1.2), (0.0, -h + 1.2)])
    knob = circle((0.5, -h), 0.55, 14)
    tip = poly([(d - 1.0, -1.0), (d, -1.0), (d, -1.6)])
    return cs_union([post, arm, web, knob, tip])


CO.FRIEZE_EXTRA.update(mrsticks=frieze_mrsticks, mrportholes=frieze_mrportholes, mrlozenge=frieze_mrlozenge)
CO.COURSE_EXTRA.update(mrrope=course_mrrope)
TW.BRACKET_EXTRA.update(mrbrace=bracket_mrbrace)


# ---- windows and doors
def _sash22(w, h, pl, plug_cs, meet=0.6):
    """A two-over-two sash: one vertical bar in each sash and a meeting rail."""
    inner = plug_cs.offset(-0.6, MIT, 4.0)
    u0, v0, u1, v1 = inner.bounds()
    vm = (v0 + v1) / 2
    lo, hi = rect(u0, v0, u1, vm - meet / 2), rect(u0, vm + meet / 2, u1, v1)
    bars = rect(-RIB / 2, v0 - 1, RIB / 2, v1 + 1)
    return _glazed([ext(plug_cs, -pl, -0.6)], lo + hi, pl, bars, plug_cs)


def window_mrlower(w=9.0, h=19.0, A=0.9):
    """The Marisol's ground-floor window: two over two, a plain casing with plinth blocks, and a
    Stick Style hood: a long head board on two diagonal braces whose posts run down the
    casing; a sill on two little blocks."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    sash = _sash22(w, h, pl, plug_cs)
    X = w / 2 + A
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             ext((op.offset(A, MIT, 4.0) - op) ^ rect(-50, 0.0, 50, 100), 0.0, 0.8)]
    vh = h + A
    parts.append(chamfer_box(-X - 2.6, vh - 0.3, X + 2.6, vh + 1.2, 0.0, 1.6, c=0.4, bottom=0.8))      # the head board
    parts.append(chamfer_box(-X - 2.2, vh + 1.19, X + 2.2, vh + 1.8, 0.0, 1.0, c=0.3, bottom=0.6))  # its drip
    for sg in (-1, 1):
        brace = poly([(sg * (X - 0.5), vh - 3.4), (sg * (X + 0.9), vh - 3.4), (sg * (X + 2.4), vh + 0.01), (sg * (X + 1.4), vh + 0.01),
                      (sg * (X - 0.5), vh - 2.2)])
        parts.append(ext(brace, 0.0, 1.2))
        parts.append(chamfer_box(min(sg * X, sg * (X - 1.2)), 0.0, max(sg * X, sg * (X - 1.2)), 2.2, 0.0, 1.0, c=0.3, bottom=1.0))
    parts.append(chamfer_box(-X - 0.8, -1.2, X + 0.8, 0.01, 0.0, 1.4, c=0.3, bottom=1.4))
    for sg in (-1, 1):
        parts.append(chamfer_box(sg * (X - 0.4) - 0.6, -2.2, sg * (X - 0.4) + 0.6, -1.19, 0.0, 1.0, c=0.3, bottom=1.0))
    return O._one_piece(sash, parts, op, plug_cs, pl, vh + 1.8, -2.2)


def window_mrupper(w=9.0, h=17.0, A=0.8):
    """The upper storey's window: two over two under a little stick gablet (a raking cap on the
    casing with a king post in its triangle), a sawn apron under the sill."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    sash = _sash22(w, h, pl, plug_cs)
    X = w / 2 + A
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             ext((op.offset(A, MIT, 4.0) - op) ^ rect(-50, 0.0, 50, 100), 0.0, 0.8)]
    vh = h + A
    G = X + 1.0
    rise = 3.4
    tri = poly([(-G, vh), (G, vh), (0.0, vh + rise)])
    parts.append(ext(tri - tri.offset(-0.9, MIT, 4.0), 0.0, 1.2))
    parts.append(ext(rect(-0.45, vh, 0.45, vh + rise - 0.6), 0.0, 1.0))
    parts.append(chamfer_box(-G - 0.4, vh - 0.8, G + 0.4, vh + 0.01, 0.0, 1.3, c=0.3, bottom=0.8))
    parts.append(chamfer_box(-X - 0.8, -1.2, X + 0.8, 0.01, 0.0, 1.4, c=0.3, bottom=1.4))
    apron = poly([(-X + 0.4, -1.0), (X - 0.4, -1.0), (X - 1.4, -3.2), (0.0, -3.8), (-X + 1.4, -3.2)])
    parts.append(ext(apron, 0.0, 0.8))
    return O._one_piece(sash, parts, op, plug_cs, pl, vh + rise, -3.8)


def window_mrgable(w=7.0, h=12.0, gap=2.0, A=0.7):
    """The cross gables' window: a pair of tall lights one over one under one hood board on
    three small braces, a single sill."""
    W = 2 * w + gap
    lights = [rect(-W / 2, 0.0, -W / 2 + w, h), rect(W / 2 - w, 0.0, W / 2, h)]
    op = cs_union(lights)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    inner = plug_cs.offset(-0.6, MIT, 4.0)
    vm = h * 0.5
    bars = rect(-W, vm - 0.3, W, vm + 0.3)
    sash = _glazed([ext(plug_cs, -pl, -0.6)], inner, pl, bars, plug_cs)
    whole = rect(-W / 2, 0.0, W / 2, h)
    X = W / 2 + A
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             ext((whole.offset(A, MIT, 4.0) - op) ^ rect(-50, 0.0, 50, 100), 0.0, 0.8)]
    parts.append(ext(rect(-gap / 2 - 0.3, 0.0, gap / 2 + 0.3, h), 0.0, 1.0))
    vh = h + A
    parts.append(chamfer_box(-X - 1.6, vh, X + 1.6, vh + 1.2, 0.0, 1.5, c=0.4, bottom=0.8))
    for x in (-X, 0.0, X):
        parts.append(ext(poly([(x - 0.5, vh - 2.0), (x + 0.5, vh - 2.0), (x + 1.2, vh + 0.01), (x - 1.2, vh + 0.01)]), 0.0, 1.1))
    parts.append(chamfer_box(-X - 0.8, -1.2, X + 0.8, 0.01, 0.0, 1.3, c=0.3, bottom=1.3))
    return O._one_piece(sash, parts, op, plug_cs, pl, vh + 1.2, -1.2)


def window_mrtower(w=8.0, h=15.0, A=0.8):
    """The light tower's window: a tall one-over-one with a segmental head, its casing stepped
    out at the head to a keyed arch; a sill on a corbel. One to each face of each stage, as a
    keeper's watch room has them."""
    rise = w * 0.22
    R = (w * w / 4 + rise * rise) / (2 * rise)
    vs = h - rise
    arc = [(R * math.sin(a), vs - (R - rise) + R * math.cos(a)) for a in np.linspace(math.asin(w / 2 / R), -math.asin(w / 2 / R), 17)]
    op = poly([(-w / 2, 0.0), (w / 2, 0.0)] + arc)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    inner = plug_cs.offset(-0.6, MIT, 4.0)
    vm = vs * 0.48
    bars = rect(-w, vm - 0.3, w, vm + 0.3)
    sash = _glazed([ext(plug_cs, -pl, -0.6)], inner, pl, bars, plug_cs)
    outer = op.offset(A, RND)
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS), ext((outer - op) ^ rect(-50, 0.0, 50, 100), 0.0, 0.8)]
    parts.append(ext((op.offset(A + 0.8, RND) - op.offset(A - 0.1, RND)) ^ rect(-50, vs - 0.5, 50, 100), 0.0, 1.1))
    parts.append(ext(poly([(-0.9, h + A - 0.6), (0.9, h + A - 0.6), (1.2, h + A + 1.6), (-1.2, h + A + 1.6)]), 0.0, 1.4))
    X = w / 2 + A
    parts.append(chamfer_box(-X - 0.8, -1.2, X + 0.8, 0.01, 0.0, 1.4, c=0.3, bottom=1.4))
    parts.append(ext(poly([(-X + 0.6, -1.0), (X - 0.6, -1.0), (X - 1.6, -2.6), (-X + 1.6, -2.6)]), 0.0, 1.0))
    return O._one_piece(sash, parts, op, plug_cs, pl, h + A + 1.6, -2.6)


def door_mrfront(w=12.0, h=24.0, A=1.0):
    """The keeper's front door: a pair of leaves, each a tall glazed light over a panel framed
    in stick mouldings with a diagonal brace across it; a three-light transom; a casing with
    corner blocks and a hood board on long braces."""
    tr = 4.0
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    parts_s = [ext(plug_cs - plug_cs.offset(-0.5, MIT, 4.0), -pl, 0.0)]
    vd = h - tr
    leaves = [rect(-w / 2 + 0.3, 0.0, -0.25, vd - 0.4), rect(0.25, 0.0, w / 2 - 0.3, vd - 0.4)]
    for lf in leaves:
        parts_s.append(ext(lf, -pl, -0.6))
    lights = []
    for lf in leaves:
        a, _, c_, _ = lf.bounds()
        lights.append(rect(a + 0.9, vd * 0.48, c_ - 0.9, vd - 1.4))
    trl = rect(-w / 2 + 0.6, vd + 0.2, w / 2 - 0.6, h - 0.6)
    glass = cs_union(lights) + trl
    parts_s = [p - ext(glass, -pl - 1, 0.0) for p in parts_s]
    parts_s.append(ext(glass, -pl, -pl + O.GLASS))
    gb = [rect(x - RIB / 2, vd, x + RIB / 2, h) for x in (-w / 6, w / 6)]
    parts_s.append(ext(cs_union(gb) ^ trl.offset(0.1, MIT, 4.0), -pl + O.GLASS - 0.01, -0.5))
    parts_s.append(ext(rect(-w / 2 + 0.3, vd - 0.4, w / 2 - 0.3, vd + 0.2), -pl, -0.4))          # transom bar
    for lf in leaves:
        a, _, c_, _ = lf.bounds()
        pan = rect(a + 0.9, 1.4, c_ - 0.9, vd * 0.48 - 1.0)
        parts_s.append(ext(pan - pan.offset(-0.5, MIT, 4.0), -0.65, -0.2))
        pb = pan.offset(-0.5, MIT, 4.0).bounds()
        parts_s.append(ext(_clean(stroke([(pb[0] + 0.3, pb[1] + 0.3), (pb[2] - 0.3, pb[3] - 0.3)], 0.55)) ^
                           pan.offset(-0.4, MIT, 4.0), -0.65, -0.25))
    X = w / 2 + A
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             ext((op.offset(A, MIT, 4.0) - op) ^ rect(-50, 0.0, 50, 100), 0.0, 0.9)]
    for sg in (-1, 1):
        parts.append(chamfer_box(sg * X - 1.0, h + A - 1.9, sg * X + 1.0, h + A + 1.7, 0.0, 1.3, c=0.3))      # corner blocks
        brace = poly([(sg * (X - 0.5), h - 6.0), (sg * (X + 0.9), h - 6.0), (sg * (X + 3.0), h + A + 1.7), (sg * (X + 2.0), h + A + 1.7)])
        parts.append(ext(brace, 0.0, 1.2))
    parts.append(chamfer_box(-X - 3.4, h + A + 1.59, X + 3.4, h + A + 2.8, 0.0, 1.7, c=0.4, bottom=0.8))
    parts_s = [m ^ ext(plug_cs, -pl - 1.0, 1.0) for m in parts_s]
    return O._one_piece(parts_s, parts, op, plug_cs, pl, h + A + 2.8, 0.0)


def door_mrback(w=8.4, h=21.0, A=0.8):
    """The kitchen door: four panels framed in sticks, the upper two glazed, in a plain casing
    with a drip cap."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    leaf = plug_cs
    parts_s = [ext(leaf, -pl, -0.6), ext(plug_cs - plug_cs.offset(-0.5, MIT, 4.0), -pl, 0.0)]
    vm = h * 0.55
    lights = [rect(-w / 2 + 0.9, vm + 0.4, -0.45, h - 1.2), rect(0.45, vm + 0.4, w / 2 - 0.9, h - 1.2)]
    glass = cs_union(lights)
    parts_s = [p - ext(glass, -pl - 1, 0.0) for p in parts_s]
    parts_s.append(ext(glass, -pl, -pl + O.GLASS))
    for a, c_ in ((-w / 2 + 0.9, -0.45), (0.45, w / 2 - 0.9)):
        pan = rect(a, 1.2, c_, vm - 0.6)
        parts_s.append(ext(pan - pan.offset(-0.5, MIT, 4.0), -0.65, -0.2))
    X = w / 2 + A
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             ext((op.offset(A, MIT, 4.0) - op) ^ rect(-50, 0.0, 50, 100), 0.0, 0.8),
             chamfer_box(-X - 1.0, h + A - 0.01, X + 1.0, h + A + 1.2, 0.0, 1.4, c=0.4, bottom=0.8)]
    parts_s = [m ^ ext(plug_cs, -pl - 1.0, 1.0) for m in parts_s]
    return O._one_piece(parts_s, parts, op, plug_cs, pl, h + A + 1.2, 0.0)


# ---- the gable trusses
def gable_marisol(L, slope, d_eave, skin=1.8, width=2.2, d=1.4, collar=0.46, finial=5.0):
    """The Marisol's cross-gable truss (Stick Style), hung on the rake's outer end like a
    bargeboard (facade frame of the gable wall: u from its left end, v up from the eave): the
    raking boards over the skin's end, a collar tie across at ``collar`` of the height, a king
    post from it to the apex, two struts fanning down from the king post's foot to the rafters,
    a turned drop under the collar and a spike finial; every member at least 1.0 wide and all
    of them one frame (no accent on its own)."""
    s = slope
    c = math.hypot(1.0, s)
    a_l = np.array([-d_eave, 0.0])
    tip = np.array([L / 2, s * (L / 2 + d_eave)])
    a_r = np.array([L + d_eave, 0.0])
    depth = skin + width
    band = []
    for a in (a_l, a_r):
        n = np.array([s, -1.0]) / c if a[0] < L / 2 else np.array([-s, -1.0]) / c
        band.append(poly([tuple(a), tuple(tip), tuple(tip + n * depth), tuple(a + n * depth)]))
    board = cs_union(band) ^ rect(-d_eave - 5, -0.01, L + d_eave + 5, tip[1] + 5)
    vc = tip[1] * collar
    half_c = (tip[1] - depth * c - vc) / s + 0.4          # the collar runs into the boards' lower edge
    xc = L / 2
    members = [rect(xc - half_c, vc - 0.6, xc + half_c, vc + 0.6),        # collar tie
               rect(xc - 0.6, vc - 0.6, xc + 0.6, tip[1] - depth * c * 0.5)]  # king post
    for sg in (-1, 1):
        p0 = (xc, vc + 0.2)
        p1 = (xc + sg * half_c * 0.62, vc + (tip[1] - vc) * 0.42)
        members.append(stroke([p0, p1], 1.0))
        members.append(stroke([(xc + sg * half_c * 0.55, vc), (xc + sg * half_c * 0.55, vc - 2.2)], 1.0))
    drop = cs_union([rect(xc - 0.55, vc - 4.6, xc + 0.55, vc), circle((xc, vc - 4.8), 0.8, 16)])
    spike = poly([(xc - 0.8, tip[1] - 0.2), (xc + 0.8, tip[1] - 0.2), (xc + 0.5, tip[1] + finial * 0.6), (xc, tip[1] + finial),
                  (xc - 0.5, tip[1] + finial * 0.6)])
    frame = _tie(cs_union([board] + members + [drop, spike]))
    return _text(frame, 0.0, d)


# ---- the chimneys
def chimney_marisol(w, dd, h, cap=2.0):
    """A brick stack with a sunk panel on every face and a corbelled cap of three courses
    stepping out at 45 degrees under a thin slab (prints upright)."""
    zc = h - 4.6
    shaft = box([-w / 2, -dd / 2, 0.0], [w / 2, dd / 2, zc])
    for ax, L_, D_ in ((0, w, dd), (1, dd, w)):
        for sg in (-1, 1):
            if L_ < 5.0:
                continue
            pan = box([-L_ / 2 + 1.2, -0.3, h * 0.45], [L_ / 2 - 1.2, 0.5, zc - 1.6])
            if ax == 1:
                pan = pan.rotate([0, 0, 90])
            off = [0.0, sg * D_ / 2, 0.0] if ax == 0 else [sg * D_ / 2, 0.0, 0.0]
            shaft = shaft - pan.translate(off)
    parts = [shaft]
    z = zc
    for k in range(3):
        g = 0.4 * (k + 1)
        parts.append(M.hull_points([(x * (w / 2 + g - 0.4), y * (dd / 2 + g - 0.4), z - 0.01) for x in (-1, 1) for y in (-1, 1)] +
                                   [(x * (w / 2 + g), y * (dd / 2 + g), z + 0.4) for x in (-1, 1) for y in (-1, 1)]))
        parts.append(box([-w / 2 - g, -dd / 2 - g, z + 0.39], [w / 2 + g, dd / 2 + g, z + 1.0]))
        z += 1.0
    parts.append(box([-w / 2 - 1.4, -dd / 2 - 1.4, z - 0.01], [w / 2 + 1.4, dd / 2 + 1.4, h]))
    flue = box([-w / 2 + 1.4, -dd / 2 + 1.4, h - 1.6], [w / 2 - 1.4, dd / 2 - 1.4, h + 1.0])
    return union(parts) - flue


# ---- the light: gallery deck, its railing strips, the lantern and its glass
def gallery_marisol(half, t=1.6, rail_in=1.4, slot=(1.2, 0.8), lip=(16.0, 2.8)):
    """The gallery deck: a square plate ``half`` from the centre, ``t`` thick, slots for the
    railing strips' tabs along its edges, a socket ring in the middle for the lantern, and a
    locating lip underneath that drops inside the tower's walls. Built at z = 0 (its top at t)."""
    deck = box([-half, -half, 0.0], [half, half, t])
    li, lh = lip
    deck = deck + (box([-li, -li, -1.2], [li, li, 0.01]) - box([-li + 1.4, -li + 1.4, -2.0], [li - 1.4, li - 1.4, 1.0]))
    sw, sd = slot
    cuts = []
    for sg in (-1, 1):
        for ax in (0, 1):
            e = sg * (half - rail_in)
            if ax == 0:
                cuts.append(box([-half + 3.0, e - sw / 2, t - sd], [half - 3.0, e + sw / 2, t + 1]))
            else:
                cuts.append(box([e - sw / 2, -half + 3.0, t - sd], [e + sw / 2, half - 3.0, t + 1]))
    deck = deck - union(cuts)
    # the seam boards of the deck, a row of plates (shallow grooves)
    grooves = union([box([x - 0.25, -half + 2.6, t - 0.2], [x + 0.25, half - 2.6, t + 1]) for x in np.arange(-half + 4.0, half - 3.0, 3.2)])
    ring = M.cylinder(1.0, 12.8 / math.cos(math.pi / 8), 12.8 / math.cos(math.pi / 8), 8).rotate([0, 0, 22.5]).translate([0, 0, t - 0.6])
    return deck - (grooves - M.cylinder(2.0, 15.4, 15.4, 8).rotate([0, 0, 22.5]).translate([0, 0, t - 1.0])) - ring


def gallery_rail_marisol(L, h=9.4, tab=(0.8, 0.8)):
    """One side of the gallery's iron railing, flat (u along, v up, w across 0..1.0): a top
    rail, a mid rail and a bottom rail on square posts with a ball on each, and tabs under the
    bottom rail that drop into the deck's slots. Open enough to see the lantern through.
    Prints on its back."""
    t = 1.0
    parts = [rect(0.0, 0.0, L, 0.9), rect(0.0, h * 0.45 - 0.45, L, h * 0.45 + 0.45), rect(0.0, h - 1.0, L, h)]
    n = max(2, int(L / 7.0) + 1)
    for k in range(n):
        u = 0.5 + (L - 1.0) * k / (n - 1)
        parts.append(rect(u - 0.5, 0.0, u + 0.5, h))
        parts.append(circle((u, h + 0.5), 0.7, 14))
    tw, td = tab
    for u in (L * 0.2, L * 0.5, L * 0.8):
        parts.append(rect(u - 1.5, -td, u + 1.5, 0.01))
    return ext(cs_union(parts), 0.0, t)


def lantern_marisol(a=12.6, hg=15.0, hp=6.0):
    """The lantern, iron (the cage) and glass: an octagonal parapet ``hp`` high with a little
    door in one face (the watch room's wall), then the glazing in two tiers of panes between
    corner mullions, a mid rail and a top ring, under a domed roof with a ventilator ball and a
    lightning rod; and the glass, an octagonal block that the cage drops over (its foot sits
    0.6 down in the deck's socket). Both built from z = 0 (the gallery deck's top). Returns
    (cage, glass). The cage prints upright: its rings bridge between the mullions, and the
    dome is hollowed by a 45-degree cone so nothing overhangs."""
    def oct_(ap, z0, z1):
        return M.cylinder(z1 - z0, ap / math.cos(math.pi / 8), ap / math.cos(math.pi / 8), 8).rotate([0, 0, 22.5]).translate([0, 0, z0])
    zs = hp                                   # the parapet's top: the glazing starts here
    zt = zs + hg                              # the top ring's foot
    Rk = 1.0 / math.cos(math.pi / 8)
    flare = M.hull_points([((a + 2.0) * Rk * math.cos(math.radians(22.5 + 45 * k)), (a + 2.0) * Rk * math.sin(math.radians(22.5 + 45 * k)), zs - 1.4)
                           for k in range(8)] +
                          [((a + 2.6) * Rk * math.cos(math.radians(22.5 + 45 * k)), (a + 2.6) * Rk * math.sin(math.radians(22.5 + 45 * k)), zs - 0.8)
                           for k in range(8)])
    par = oct_(a + 2.0, 0.0, zs - 0.8) + flare + oct_(a + 2.6, zs - 0.81, zs) - oct_(a, -1.0, zs + 1.0)
    # its door, sunk in the south face, and a sunk panel on the others
    ap = a + 2.0
    for k in range(8):
        ang = -math.pi / 2 + k * math.pi / 4
        w_ = 3.2 if k == 0 else 3.6
        z0_, z1_ = (0.4, zs - 1.4) if k == 0 else (1.0, zs - 1.8)
        pan = box([-w_ / 2, -0.4, z0_], [w_ / 2, 0.5, z1_]).rotate([0, 0, math.degrees(ang) - 90 + 180])
        par = par - pan.translate([ap * math.cos(ang), ap * math.sin(ang), 0])
    R = (a + 0.6) / math.cos(math.pi / 8)
    mull = []
    for k in range(8):
        ang = math.radians(22.5 + 45 * k)
        mull.append(M.cylinder(hg + 0.01, 0.75, 0.75, 12).translate([R * math.cos(ang), R * math.sin(ang), zs - 0.01]))
    mid = oct_(a + 1.0, zs + hg * 0.5 - 0.5, zs + hg * 0.5 + 0.5) - oct_(a, zs, zt)
    top = oct_(a + 1.8, zt, zt + 1.6) - oct_(a, zt - 1.0, zt + 1.6)
    rd = a + 2.4
    dome = M.sphere(rd, 48).scale([1.0, 1.0, 0.62]).translate([0, 0, zt + 1.6]) ^ box([-50, -50, zt + 1.6], [50, 50, zt + 30])
    dome = dome + oct_(a + 2.4, zt + 1.59, zt + 2.2)
    cone = M.cylinder(a + 0.01, a / math.cos(math.pi / 8), 0.0, 8).rotate([0, 0, 22.5]).translate([0, 0, zt + 1.6])
    dome = dome - cone
    zd = zt + 1.6 + rd * 0.62
    vent = M.cylinder(2.4, 2.2, 1.4, 16).translate([0, 0, zd - 0.6]) + M.sphere(2.6, 24).translate([0, 0, zd + 3.6])
    rod = M.cylinder(5.0, 0.6, 0.5, 10).translate([0, 0, zd + 5.8])
    cage = union([par, mid, top, dome, vent, rod] + mull)
    glass = oct_(a - 0.2, -0.6, zt + 1.4)
    return cage, glass


def rocks_marisol(spots, seed=5):
    """The rocks of the point: faceted blocks (hulls of jittered points), flat underneath."""
    rng = np.random.default_rng(seed)
    out = []
    for (x, y, r) in spots:
        pts = []
        for k in range(14):
            th = rng.uniform(0, 2 * math.pi)
            ph = rng.uniform(0.05, math.pi / 2)
            rr = r * rng.uniform(0.7, 1.05)
            pts.append((x + rr * math.cos(th) * math.cos(ph) * 1.15, y + rr * math.sin(th) * math.cos(ph), rr * math.sin(ph) * 0.85))
        for k in range(6):
            th = 2 * math.pi * k / 6 + rng.uniform(-0.3, 0.3)
            rr = r * rng.uniform(0.85, 1.1)
            pts.append((x + rr * math.cos(th) * 1.15, y + rr * math.sin(th), 0.0))
        out.append(M.hull_points(pts))
    return union(out)


# ---- the veranda: post, railing fill, spandrel, skirt and roof edge styles (registered)
def post_marisol(h, collar=None, abacus=3.0, slot=None):
    """The veranda's post: a round shaft on a square plinth, two turned rings a third of the way
    up, a necking under a square chamfered cap."""
    from .porchwork import _plinth, _revolve, _top
    z1 = h - 3.0
    zr = 1.2 + (z1 - 1.2) * 0.32
    prof = [(0.0, 1.19), (1.3, 1.19), (1.3, 1.6), (1.05, 1.9), (1.05, zr - 0.6), (1.3, zr - 0.35), (1.3, zr - 0.05),
            (1.05, zr + 0.2), (1.3, zr + 0.45), (1.3, zr + 0.75), (1.05, zr + 1.0), (1.05, z1 - 0.4), (1.25, z1 - 0.2),
            (1.25, z1)]
    body = _revolve(prof) + _plinth(3.0, 1.2)
    return body + _top(h, abacus / 2, z1, 1.25, slot, seg=36)


def fill_mrcross(L, vb, vt):
    """The veranda railing: Stick Style panels, each a St Andrew's cross in a frame of sticks."""
    H = vt - vb
    n = max(1, int(round(L / (H * 1.5))))
    out = []
    for k in range(n + 1):
        u = L * k / n
        out.append(rect(max(0.0, u - 0.4), vb, min(L, u + 0.4), vt))
    for k in range(n):
        a, c_ = L * k / n + 0.4, L * (k + 1) / n - 0.4
        out.append(stroke([(a, vb + 0.3), (c_, vt - 0.3)], 0.6))
        out.append(stroke([(a, vt - 0.3), (c_, vb + 0.3)], 0.6))
    return [_clean(cs_union(out)) ^ rect(0.0, vb, L, vt)]


def spandrel_mrbraces(u0, u1, v_bot, v_top):
    """The veranda's upper work between two posts: a curved brace from each post into the beam,
    and between them a rail with short sticks standing on it (a stick valance)."""
    H = v_top - v_bot
    out = []
    reach = min(5.0, (u1 - u0) * 0.3)
    for sg, uo in ((1, u0), (-1, u1)):
        pts = [(uo, v_bot - 0.6)]
        for a in np.linspace(0.0, math.pi / 2, 9):
            pts.append((uo + sg * reach * (1 - math.cos(a)), v_bot + H * math.sin(a)))
        out.append(stroke(pts, 0.9))
    vr = v_bot + H * 0.45
    out.append(rect(u0, vr - 0.4, u1, vr + 0.4))
    n = max(1, int((u1 - u0 - 2 * reach) / 1.6))
    for k in range(n + 1):
        u = u0 + reach + (u1 - u0 - 2 * reach) * k / max(n, 1)
        out.append(rect(u - 0.4, vr, u + 0.4, v_top))
    return _clean(cs_union(out)) ^ rect(u0, v_bot - 1.0, u1, v_top + 0.01)


def skirt_mrboards(reg, d=1.2):
    """The veranda's skirt: vertical boards with a gap between each, a rail along the top."""
    u0, v0, u1, v1 = reg.bounds()
    bd = cs_union([rect(u, v0 - 1, u + 1.4, v1 + 1) for u in np.arange(u0 + 0.2, u1, 2.0)]) ^ reg
    rail = rect(u0 - 1, v1 - 1.0, u1 + 1, v1 + 1) ^ reg
    return M.extrude(bd, d * 0.6) + M.extrude(rail, d)


def edge_mrdrip(L, z0, zc):
    """The veranda roof's fascia: a plain board with a row of small drops under a drip."""
    n = max(1, int((L - 1.2) / 2.4))
    drops = [rect(u - 0.45, z0 - 0.6, u + 0.45, z0 + 0.4) + circle((u, z0 - 0.6), 0.5, 12)
             for u in (0.6 + (L - 1.2) * (k + 0.5) / n for k in range(n))]
    cs = cs_union(drops) + rect(0.3, zc - 0.7, L - 0.3, zc)
    return cs, 0.6


PW.POSTS.update(marisol=post_marisol)
PW.FILLS.update(mrcross=fill_mrcross)
PW.FRIEZES.update(mrbraces=spandrel_mrbraces)
PW.SKIRTS.update(mrboards=skirt_mrboards)
FT.EDGE_EXTRA.update(mrdrip=edge_mrdrip)


# ================================================================== the Fevre (house 104)
# After the brick houses on the bluffs of Galena, Illinois (1840s-50s), the lead-mining town on
# the Fever River: a Federal house with Greek Revival touches, set into the hill so it shows
# three storeys to the street (a walk-out storey of tooled limestone under two of brick) and two
# to the garden behind; parapeted gable ends carrying paired chimneys; a stone stair climbing
# along the front wall to the door on the main floor; a street wall with steps, and garden
# terraces stepping down the side. The ground it stands on is part of the model.

def brick_fevre(region, datum=0.0):
    """The Fevre's brick: American common bond, a course of headers every sixth, deep joints."""
    from .skins import brick_bond
    return brick_bond(region, "common", bl=2.4, bh=0.8, mortar=0.5, bed=0.2, d=0.3, datum=datum, header_every=6)


def stone_fevre(region, datum=0.0, seed=0):
    """Galena limestone: long squared blocks in even courses, each face tooled in fine vertical
    strokes inside a smooth margin (the margin and strokes sunk, so the block face prints
    upright with nothing overhanging)."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    rng = np.random.default_rng(seed)
    out = []
    ch = 3.2
    k0 = math.floor((v0 - datum) / ch)
    for k in range(k0, int((v1 - datum) / ch) + 1):
        vb = datum + k * ch
        u = u0 - rng.uniform(0.0, 7.0)
        while u < u1:
            L = rng.uniform(5.0, 9.0)
            blk = rect(u + 0.25, vb + 0.25, u + L - 0.25, vb + ch - 0.25) ^ region
            if blk.area() > 1.0:
                out.append(_st(blk, 0.0, 0.45))
                inner = blk.offset(-0.55, MIT, 4.0)
                if inner.area() > 1.0:
                    b = inner.bounds()
                    strokes = cs_union([rect(x, b[1], x + 0.5, b[3]) for x in np.arange(b[0] + 0.3, b[2] - 0.3, 1.0)]) ^ inner
                    out.append(_st(strokes, 0.45, 0.12))
            u += L
    out.append(M.extrude(region, 0.05))
    return union(out)


# ---- cornice ornaments
def frieze_fvcorbel(L, h, b, pitch, margin, pair, half):
    """A brick corbel table: little stepped brick corbels hanging from a band, every 2.4 mm
    (the joint between the stone storey and the brick)."""
    v1 = h - 0.4
    out = [_st(rect(0.2, v1 - 1.0, L - 0.2, v1), b, 0.5)]
    pu = 2.4
    n = max(1, int((L - 0.8) / pu))
    u0 = (L - n * pu) / 2
    cors = []
    for k in range(n):
        uc = u0 + pu * (k + 0.5)
        cors.append(rect(uc - 0.7, v1 - 2.2, uc + 0.7, v1 - 0.99) + rect(uc - 0.45, v1 - 3.2, uc + 0.45, v1 - 2.19))
    out.append(_st(cs_union(cors), b, 0.45))
    return out, []


def course_fvtooled(L, h, b, pitch, margin, p):
    """A dressed limestone band: a smooth margin top and bottom, the face between tooled in
    short vertical strokes."""
    band = rect(0.2, 0.2, L - 0.2, h - 0.2)
    out = [_st(band, b, 0.25)]
    st_ = cs_union([rect(u, 0.6, u + 0.45, h - 0.6) for u in np.arange(0.6, L - 0.6, 0.95)])
    out.append(_st(st_ ^ band, b + 0.25, 0.15))
    return out


def frieze_fvdiaper(L, h, b, pitch, margin, pair, half):
    """The storey joint's frieze: a band of brick laid in a diaper of raised diamonds (headers
    set proud), between two stretcher courses."""
    v0, v1 = 0.4, h - 0.4
    vm = (v0 + v1) / 2
    out = [_st(rect(0.2, v0, L - 0.2, v0 + 0.8) + rect(0.2, v1 - 0.8, L - 0.2, v1), b, 0.35)]
    dw, dh = 3.2, (v1 - v0 - 1.8) / 2
    n = max(1, int((L - 1.0) / dw))
    u0 = (L - n * dw) / 2
    dia = []
    for k in range(n):
        uc = u0 + dw * (k + 0.5)
        o = poly([(uc - dw / 2 + 0.2, vm), (uc, vm - dh), (uc + dw / 2 - 0.2, vm), (uc, vm + dh)])
        dia.append(o - o.offset(-0.55, MIT, 4.0))
    out.append(_st(_clean(cs_union(dia)), b, 0.35))
    return out, []


def course_fvbead(L, h, b, pitch, margin, p):
    """A stone string course with a bead and reel along its face."""
    band = rect(0.2, 0.2, L - 0.2, h - 0.2)
    out = [_st(band, b, 0.25)]
    vm = h / 2
    beads = []
    u = 0.8
    while u < L - 1.4:
        beads.append(circle((u, vm), 0.42, 12))
        beads.append(rect(u + 0.55, vm - 0.22, u + 1.45, vm + 0.22))
        u += 2.0
    out.append(_st(_clean(cs_union(beads), 0.2), b + 0.25, 0.25))
    return out


def frieze_fvswags(L, h, b, pitch, margin, pair, half):
    """The eave's Federal frieze: festoons of drapery hung from rosettes, a tassel between,
    under a plain fillet."""
    v0, v1 = 0.4, h - 0.4
    out = [_st(rect(0.2, v1 - 0.6, L - 0.2, v1), b, 0.3)]
    sw = 6.0
    n = max(1, int((L - 1.2) / sw))
    u0 = (L - n * sw) / 2
    sh = []
    for k in range(n + 1):
        uc = u0 + sw * k
        sh.append(circle((uc, v1 - 1.3), 0.6, 14))
        if 0 < k < n or True:
            sh.append(rect(uc - 0.25, v0 + 0.8, uc + 0.25, v1 - 1.3) ^ rect(0.3, -5, L - 0.3, 50))
            sh.append(poly([(uc - 0.55, v0 + 0.2), (uc + 0.55, v0 + 0.2), (uc, v0 + 1.2)]) ^ rect(0.3, -5, L - 0.3, 50))
    for k in range(n):
        a, c_ = u0 + sw * k + 0.7, u0 + sw * (k + 1) - 0.7
        pts = [(a + (c_ - a) * t, v1 - 1.4 - (v1 - v0 - 2.0) * math.sin(math.pi * t)) for t in np.linspace(0, 1, 13)]
        sh.append(stroke(pts, 0.6))
        pts2 = [(a + (c_ - a) * (0.15 + 0.7 * t), v1 - 1.2 - (v1 - v0 - 2.8) * math.sin(math.pi * t)) for t in np.linspace(0, 1, 9)]
        sh.append(stroke(pts2, 0.5))
    out.append(_st(_clean(cs_union(sh)) ^ rect(0.2, v0, L - 0.2, v1), b, 0.35))
    return out, []


def course_fvdentil(L, h, b, pitch, margin, p):
    """Federal dentils, small and close, with a bead under them."""
    out = [_st(rect(0.2, 0.2, L - 0.2, 0.9), b, 0.35)]
    pu = 1.3
    n = max(1, int((L - 0.8) / pu))
    u0 = (L - n * pu) / 2
    dents = cs_union([rect(u0 + pu * k + 0.2, 0.9, u0 + pu * k + pu - 0.3, h - 0.2) for k in range(n)])
    out.append(_st(dents, b, 0.5))
    return out


def bracket_fvmodillion(h, d, t):
    """A Federal modillion (side profile): a long horizontal block under the soffit, its front
    rolled down in a scroll, its back square to the wall."""
    body = rect(0.0, -min(h, 1.8), d - 0.6, 0.0)
    roll = circle((d - 0.9, -min(h, 1.8) + 0.2), min(h, 1.8) * 0.55, 18)
    return cs_union([body, roll]) ^ rect(0.0, -h, d, 0.0)


CO.FRIEZE_EXTRA.update(fvcorbel=frieze_fvcorbel, fvdiaper=frieze_fvdiaper, fvswags=frieze_fvswags)
CO.COURSE_EXTRA.update(fvtooled=course_fvtooled, fvbead=course_fvbead, fvdentil=course_fvdentil)
TW.BRACKET_EXTRA.update(fvmodillion=bracket_fvmodillion)


# ---- windows, doors, shutters
def _sash66(w, h, pl, plug_cs, meet=0.6, cols=3, rows=2):
    """Six over six: two sashes of cols x rows lights and a meeting rail."""
    inner = plug_cs.offset(-0.6, MIT, 4.0)
    u0, v0, u1, v1 = inner.bounds()
    vm = (v0 + v1) / 2
    lo, hi = rect(u0, v0, u1, vm - meet / 2), rect(u0, vm + meet / 2, u1, v1)
    bars = (_muntins(lo, cols, rows) ^ lo) + (_muntins(hi, cols, rows) ^ hi)
    return _glazed([ext(plug_cs, -pl, -0.6)], lo + hi, pl, bars, plug_cs)


def window_fvmain(w=9.0, h=19.0, A=0.6):
    """The main floor's window: six over six in a narrow wood casing, under a tooled limestone
    lintel with a raised keystone and splayed ends, on a projecting stone sill."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    sash = _sash66(w, h, pl, plug_cs)
    X = w / 2 + A
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             ext((op.offset(A, MIT, 4.0) - op) ^ rect(-50, 0.0, 50, 100), 0.0, 0.7)]
    vh = h + A - 0.01
    lin = poly([(-X - 0.6, vh), (X + 0.6, vh), (X + 1.6, vh + 3.0), (-X - 1.6, vh + 3.0)])
    parts.append(ext(lin, 0.0, 1.0))
    parts.append(ext(cs_union([rect(x, vh + 0.5, x + 0.4, vh + 2.6) for x in np.arange(-X - 0.2, X + 0.4, 0.9)]) ^ lin, 0.99, 1.15))
    parts.append(ext(poly([(-1.1, vh - 0.6), (1.1, vh - 0.6), (1.5, vh + 3.6), (-1.5, vh + 3.6)]), 0.0, 1.5))
    parts.append(chamfer_box(-X - 1.2, -1.4, X + 1.2, 0.01, 0.0, 1.6, c=0.4, bottom=1.6))
    return O._one_piece(sash, parts, op, plug_cs, pl, vh + 3.6, -1.4)


def window_fvupper(w=9.0, h=16.0, A=0.6):
    """The upper storey's window: six over six (shorter), a plain limestone lintel with a
    tooled face and a sill."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    sash = _sash66(w, h, pl, plug_cs, rows=2)
    X = w / 2 + A
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             ext((op.offset(A, MIT, 4.0) - op) ^ rect(-50, 0.0, 50, 100), 0.0, 0.7)]
    vh = h + A - 0.01
    lin = rect(-X - 1.0, vh, X + 1.0, vh + 2.4)
    parts.append(ext(lin, 0.0, 1.0))
    parts.append(ext(cs_union([rect(x, vh + 0.4, x + 0.4, vh + 2.0) for x in np.arange(-X - 0.6, X + 0.6, 0.9)]) ^ lin, 0.99, 1.15))
    parts.append(chamfer_box(-X - 1.0, -1.2, X + 1.0, 0.01, 0.0, 1.4, c=0.4, bottom=1.4))
    return O._one_piece(sash, parts, op, plug_cs, pl, vh + 2.4, -1.2)


def window_fvbase(w=9.0, h=12.0, A=0.6):
    """The stone storey's window: three over three under a heavy stone lintel of three
    voussoirs, a plain sill (the street face of the walk-out storey)."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    sash = _sash66(w, h, pl, plug_cs, cols=3, rows=1)
    X = w / 2 + A
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             ext((op.offset(A, MIT, 4.0) - op) ^ rect(-50, 0.0, 50, 100), 0.0, 0.7)]
    vh = h + A - 0.01
    for a, c_, top in ((-X - 1.4, -1.3, 3.0), (-1.3, 1.3, 3.6), (1.3, X + 1.4, 3.0)):
        parts.append(chamfer_box(a + 0.15, vh, c_ - 0.15, vh + top, 0.0, 1.1, c=0.3, bottom=0.5))
    parts.append(chamfer_box(-X - 0.8, -1.2, X + 0.8, 0.01, 0.0, 1.4, c=0.4, bottom=1.4))
    return O._one_piece(sash, parts, op, plug_cs, pl, vh + 3.6, -1.2)


def door_fvfront(w=9.6, h=21.0, side=2.4, A=0.8):
    """The Fevre's front door, Federal: a six-panel leaf between leaded sidelights over little
    panels, an elliptical fanlight of radiating leads over all, reeded pilasters, and a
    limestone lintel with a keystone over the arch."""
    W = w + 2 * (side + 0.6)
    rise = W * 0.22
    vs = h
    R = (W * W / 4 + rise * rise) / (2 * rise)
    arc = [(R * math.sin(a), vs - (R - rise) + R * math.cos(a)) for a in np.linspace(math.asin(W / 2 / R), -math.asin(W / 2 / R), 25)]
    op = poly([(-W / 2, 0.0), (W / 2, 0.0)] + arc)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    parts_s = [ext(plug_cs - plug_cs.offset(-0.5, MIT, 4.0), -pl, 0.0)]
    leaf = rect(-w / 2, 0.0, w / 2, h - 0.6)
    parts_s.append(ext(leaf, -pl, -0.6))
    for j in range(3):
        for sg in (-1, 1):
            vb = 1.0 + j * (h - 2.4) / 3
            pan = rect(min(sg * 0.5, sg * (w / 2 - 0.9)), vb, max(sg * 0.5, sg * (w / 2 - 0.9)), vb + (h - 2.4) / 3 - 0.8)
            parts_s.append(ext(pan - pan.offset(-0.45, MIT, 4.0), -0.65, -0.2))
            parts_s.append(chamfer_box(*pan.offset(-0.9, MIT, 4.0).bounds(), -0.65, 0.35, c=0.2))
    fan = op ^ rect(-50, h - 0.01, 50, 100)
    side_l = [rect(min(sg * (w / 2), sg * (W / 2 - 0.4)), h * 0.32, max(sg * (w / 2), sg * (W / 2 - 0.4)), h - 0.6) for sg in (-1, 1)]
    glass = cs_union(side_l) + fan.offset(-0.6, MIT, 4.0)
    for sg in (-1, 1):
        sl = rect(min(sg * (w / 2 - 0.01), sg * (W / 2 - 0.2)), 0.0, max(sg * (w / 2 - 0.01), sg * (W / 2 - 0.2)), h - 0.6)
        parts_s.append(ext(sl, -pl, -0.6))
    parts_s.append(ext(rect(-W / 2, h - 0.6, W / 2, h + 0.01), -pl, -0.4))
    parts_s = [p - ext(glass, -pl - 1, 0.0) for p in parts_s]
    parts_s.append(ext(glass, -pl, -pl + O.GLASS))
    leads = [stroke([(0.0, h), (R * 1.2 * math.sin(a), h + R * 1.2 * math.cos(a))], RIB) for a in np.linspace(-1.2, 1.2, 9)]
    leads.append(circle((0.0, h), 1.6, 24) - circle((0.0, h), 1.0, 24))
    for sg in (-1, 1):
        x0, x1 = sorted((sg * (w / 2), sg * (W / 2 - 0.4)))
        leads += [stroke([(x0, y), (x1, y + (x1 - x0))], RIB) for y in np.arange(h * 0.32 - 1.0, h - 1.0, 1.8)]
        leads += [stroke([(x0, y + (x1 - x0)), (x1, y)], RIB) for y in np.arange(h * 0.32 - 1.0, h - 1.0, 1.8)]
    parts_s.append(ext(cs_union(leads) ^ glass.offset(0.1, MIT, 4.0), -pl + O.GLASS - 0.01, -0.5))
    X = W / 2 + A
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             ext((op.offset(A, RND) - op) ^ rect(-50, 0.0, 50, 100), 0.0, 0.8)]
    for sg in (-1, 1):                         # reeded pilasters
        x0, x1 = sorted((sg * (W / 2 + 0.2), sg * (W / 2 + 1.8)))
        parts.append(chamfer_box(x0, 0.0, x1, h + 0.4, 0.0, 1.0, c=0.2, square=("v0",)))
        parts.append(ext(cs_union([rect(x, 1.0, x + 0.3, h - 0.6) for x in np.arange(x0 + 0.25, x1 - 0.2, 0.55)]), 0.99, 1.2))
    top = h + rise + A
    lin = poly([(-X - 2.0, h + 0.4), (X + 2.0, h + 0.4), (X + 2.0, top + 0.8), (-X - 2.0, top + 0.8)]) - op.offset(A - 0.01, RND)
    parts.append(ext(lin, 0.0, 1.0))
    parts.append(ext(poly([(-1.2, top - 1.6), (1.2, top - 1.6), (1.6, top + 1.4), (-1.6, top + 1.4)]), 0.0, 1.5))
    parts_s = [m ^ ext(plug_cs, -pl - 1.0, 1.0) for m in parts_s]
    return O._one_piece(parts_s, parts, op, plug_cs, pl, top + 1.4, 0.0)


def door_fvplain(w=8.4, h=19.0, A=0.8):
    """The walk-out storey's and the garden door: a board-and-batten door with a four-light
    transom, under a flat stone lintel."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    parts_s = [ext(plug_cs - plug_cs.offset(-0.5, MIT, 4.0), -pl, 0.0), ext(plug_cs, -pl, -0.6)]
    vt = h - 3.6
    tr = rect(-w / 2 + 0.6, vt + 0.4, w / 2 - 0.6, h - 0.6)
    parts_s = [p - ext(tr, -pl - 1, 0.0) for p in parts_s]
    parts_s.append(ext(tr, -pl, -pl + O.GLASS))
    parts_s.append(ext(cs_union([rect(x - RIB / 2, vt, x + RIB / 2, h) for x in np.linspace(-w / 2, w / 2, 5)[1:-1]]) ^ tr.offset(0.1, MIT, 4.0),
                       -pl + O.GLASS - 0.01, -0.5))
    bb = cs_union([rect(x - 0.25, 0.4, x + 0.25, vt - 0.2) for x in np.arange(-w / 2 + 1.4, w / 2 - 1.0, 1.4)])
    parts_s.append(ext(_clean(plug_cs.offset(-0.6, MIT, 4.0) ^ rect(-50, 0.0, 50, vt) - bb, 0.2), -0.65, -0.3))
    for v in (2.0, vt - 2.0):
        parts_s.append(ext(rect(-w / 2 + 0.8, v - 0.5, w / 2 - 0.8, v + 0.5), -0.65, -0.1))
    X = w / 2 + A
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             ext((op.offset(A, MIT, 4.0) - op) ^ rect(-50, 0.0, 50, 100), 0.0, 0.8),
             chamfer_box(-X - 1.2, h + A - 0.01, X + 1.2, h + A + 2.6, 0.0, 1.1, c=0.3, bottom=0.6)]
    parts_s = [m ^ ext(plug_cs, -pl - 1.0, 1.0) for m in parts_s]
    return O._one_piece(parts_s, parts, op, plug_cs, pl, h + A + 2.6, 0.0)


def shutter_fevre(w, h, t=0.8, stile=0.6):
    """The Fevre's shutter: two fields of fixed louvers above and below a lock rail at
    mid-height, a little iron holdback (an S) on the outer stile. Local frame as
    features.shutter (u 0..w, v 0..h, back at w = 0; prints face-up)."""
    web = 0.4
    rv = round(h * 0.5 / 0.2) * 0.2
    parts = [ext(rect(0, 0, w, h) - rect(stile, stile, w - stile, h - stile), 0.0, t),
             ext(rect(stile, rv - stile / 2, w - stile, rv + stile / 2), 0.0, t)]
    for f0, f1 in ((stile, rv - stile / 2), (rv + stile / 2, h - stile)):
        field = rect(stile, f0, w - stile, f1)
        parts.append(ext(field, 0.0, web))
        b = field.bounds()
        n = max(1, int((b[3] - b[1] - 0.5) / 1.0))
        pt = (b[3] - b[1] - 0.5) / n
        slats = [rect(b[0] - 0.1, b[1] + 0.5 + k * pt, b[2] + 0.1, b[1] + 0.5 + k * pt + min(RIB + 0.05, pt - 0.5)) for k in range(n)]
        parts.append(ext(cs_union(slats) ^ field.offset(0.05), web, t - 0.2))
    return union(parts)


# ---- the porch at the garden door: post, railing, spandrel, skirt, roof edge
def post_fevre(h, collar=None, abacus=3.0, slot=None):
    """The garden porch's post: a slender Greek Doric column without a base, fluted in eight
    shallow facets, under a square echinus and abacus."""
    from .porchwork import _plinth, _revolve, _top
    z1 = h - 2.8
    prof = [(0.0, 1.19), (1.3, 1.19)] + [(1.3 - 0.25 * (z - 1.2) / (z1 - 1.2), z) for z in np.linspace(1.2, z1, 6)] + [(1.05, z1)]
    body = _revolve(prof, seg=8) + _plinth(3.0, 1.2)
    return body + _top(h, abacus / 2, z1, 1.05, slot, seg=8)


def baluster_fevre(h, seg=16):
    """A plain square-ish turned baluster: a slender shaft with a bead near the top."""
    from .porchwork import _revolve
    prof = [(0.0, 0.0), (0.45, 0.0), (0.45, 0.4), (0.32, 0.6), (0.32, h - 1.2), (0.45, h - 1.0), (0.45, h - 0.7),
            (0.32, h - 0.5), (0.32, h), (0.0, h)]
    return _revolve(prof, seg=seg)


def spandrel_fvplain(u0, u1, v_bot, v_top):
    """The garden porch's beam: a Greek Revival frieze board with a row of guttae drops under
    its fillet (no arches)."""
    H = v_top - v_bot
    out = [rect(u0, v_top - H * 0.45, u1, v_top)]
    n = max(1, int((u1 - u0 - 1.0) / 1.6))
    for k in range(n):
        u = u0 + 0.8 + (u1 - u0 - 1.6) * (k + 0.5) / n
        out.append(poly([(u - 0.5, v_top - H * 0.45 + 0.01), (u + 0.5, v_top - H * 0.45 + 0.01), (u + 0.3, v_top - H * 0.45 - 0.9),
                         (u - 0.3, v_top - H * 0.45 - 0.9)]))
    return cs_union(out)


def skirt_fvstone(reg, d=1.2):
    """The garden porch's skirt: a low limestone wall, coursed, under a smooth cap."""
    u0, v0, u1, v1 = reg.bounds()
    st = stone_fevre(reg - rect(u0 - 1, v1 - 1.0, u1 + 1, v1 + 1), seed=7)
    return st + M.extrude(rect(u0 - 1, v1 - 1.0, u1 + 1, v1 + 1) ^ reg, d)


def edge_fvdentilcap(L, z0, zc):
    """The garden porch roof's edge: a fascia with a row of square dentils under a cap."""
    n = max(1, int((L - 1.0) / 1.4))
    cs = cs_union([rect(u - 0.45, z0 + 0.3, u + 0.45, zc - 1.0) for u in (0.5 + (L - 1.0) * (k + 0.5) / n for k in range(n))])
    return cs + rect(0.3, zc - 0.9, L - 0.3, zc), 0.6


PW.POSTS.update(fevre=post_fevre)
PW.BALUSTERS.update(fevre=(baluster_fevre, 1.8))
PW.FRIEZES.update(fvplain=spandrel_fvplain)
PW.SKIRTS.update(fvstone=skirt_fvstone)
FT.EDGE_EXTRA.update(fvdentilcap=edge_fvdentilcap)


# ---- the front stair, its railing, the parapet copings, the street wall and terrace walls
def stair_fevre(x0, x1, y0, y1, z0, z1, n=12, landing=(14.0, 28.0), arch=True):
    """The stone stair climbing along the front wall: ``n`` steps rising from x0 (at z0) toward
    x1, a landing (length, width along x) at the top at z1 on a pier whose arch opens to the
    walk-out storey's door under it; the stair's outer face (y0) is plain dressed stone. Built
    in world coordinates (the wall at y1). Prints upright."""
    ll, lw = landing
    xs1 = x1 - lw                                       # the flight's top edge
    parts = []
    rise = (z1 - z0) / n
    run = (xs1 - x0) / n
    for k in range(n):
        za = z0 + rise * (k + 1)
        parts.append(box([x0 + run * k, y0, z0], [xs1 + 0.01, y1, round(za / 0.2) * 0.2]))
    parts.append(box([xs1, y0, z0], [x1, y1, z1]))
    m = union(parts)
    if not arch:
        return m
    # the arch through the landing's pier, front to back
    from .core import poly as P_
    xa, xb = xs1 + 6.0, x1 - 6.0
    sp = z0 + 16.0
    r = (xb - xa) / 2
    arch = [(xa, z0 - 1.0), (xb, z0 - 1.0)] + [((xa + xb) / 2 + r * math.cos(a), sp + r * math.sin(a)) for a in np.linspace(0, math.pi, 20)]
    cut = M.extrude(P_(arch), y1 - y0 + 2.0).transform([[1, 0, 0, 0], [0, 0, 1, y0 - 1.0], [0, 1, 0, 0]])
    m = m - cut
    # nosings: each tread's front edge rounded over a little (a chamfer step on the stringer)
    return m


def stair_rail_fevre(L, rise, h=9.0):
    """The iron railing along the stair's open side, flat (u along the run, v up, w 0..0.9):
    a sloping hand rail and bottom rail, square balusters plumb every 1.8, a newel at each end
    with a ball, and tabs under the bottom rail into slots in the stair's top. Prints on its
    back."""
    t = 0.9
    s = rise / L
    parts = []
    def band(v0, wd):
        return poly([(0.0, v0), (L, v0 + rise), (L, v0 + rise + wd), (0.0, v0 + wd)])
    parts.append(band(h - 1.0, 1.0))
    parts.append(band(1.4, 0.8))
    n = max(2, int(L / 1.8))
    for k in range(n + 1):
        u = 0.4 + (L - 0.8) * k / n
        vb = s * u
        parts.append(rect(u - 0.35, vb + 1.4, u + 0.35, vb + h - 0.99))
    for u, vb in ((0.6, 0.0), (L - 0.6, rise)):
        parts.append(rect(u - 0.7, vb - 0.6, u + 0.7, vb + h + 0.8))
        parts.append(circle((u, vb + h + 1.4), 0.8, 16))
    for u in (L * 0.25, L * 0.75):
        parts.append(rect(u - 1.2, s * u - 0.8, u + 1.2, s * u + 1.41))
    return ext(cs_union(parts), 0.0, t)


def coping_fevre(L, slope, d_eave, w=4.4, th=1.6, over=0.6):
    """The parapet's limestone coping in the gable wall's frame (u along, v up from the eave,
    w across the wall, centred): a band ``th`` thick following both rakes, ``over`` past the
    wall's faces, the ends squared off at the shoulders. Prints on its side (lying flat)."""
    s = slope
    c = math.hypot(1.0, s)
    tip = np.array([L / 2, s * (L / 2 + d_eave)])
    a_l, a_r = np.array([-d_eave + 0.0, 0.0]), np.array([L + d_eave, 0.0])
    band = []
    for a in (a_l, a_r):
        n = np.array([-s, 1.0]) / c if a[0] < L / 2 else np.array([s, 1.0]) / c
        band.append(poly([tuple(a), tuple(tip), tuple(tip + n * th), tuple(a + n * th)]))
    cs = cs_union(band) ^ rect(0.0, -5.0, L, 500)
    return ext(cs, -w / 2, w / 2)


def retaining_fevre(L, h, t=3.0, cap=1.2, seed=0):
    """A limestone retaining wall, ``L`` long, ``h`` high, ``t`` thick (u along, v up, w out),
    its face in stone_fevre, a smooth coping proud on top. Prints upright on its foot."""
    body = box([0.0, 0.0, -t], [L, h - cap, 0.0])
    face = stone_fevre(rect(0.0, 0.0, L, h - cap - 0.01), seed=seed)
    cp = M.hull(box([0.0, h - cap - 0.01, -t], [L, h - cap, 0.0]) + box([-0.6, h - cap + 0.6, -t - 0.6], [L + 0.6, h, 0.6]))   # 45 degrees under its lip
    # (u, v, w) solid: x = u, y = v, z = w
    return body + face + cp


def window_fvlunette(w=14.0, A=0.7):
    """The gable's lunette: a half-round attic light with radiating bars round a little hub,
    in a limestone arch of five voussoirs with a keystone, on a sill."""
    r = w / 2
    pts = [(-r, 0.0), (r, 0.0)] + [(r * math.cos(a), r * math.sin(a)) for a in np.linspace(0.0, math.pi, 25)][1:-1]
    op = poly(pts)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    inner = plug_cs.offset(-0.5, MIT, 4.0)
    bars = cs_union([stroke([(0.0, 0.0), ((r + 1) * math.cos(a), (r + 1) * math.sin(a))], RIB) for a in np.linspace(0.45, math.pi - 0.45, 4)])
    bars = bars + circle((0.0, 0.0), 1.4, 20)
    sash = _glazed([ext(plug_cs, -pl, -0.6)], inner, pl, bars, plug_cs)
    ring = (op.offset(A + 1.6, RND) - op.offset(A - 0.05, RND)) ^ rect(-50, 0.0, 50, 50)
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS), ext(ring, 0.0, 1.0)]
    for a in np.linspace(0.0, math.pi, 6)[1:-1]:
        ca, sa = math.cos(a), math.sin(a)
        parts.append(ext(stroke([((r + A) * ca, (r + A) * sa), ((r + A + 1.6) * ca, (r + A + 1.6) * sa)], 0.35), 0.99, 1.15))
    rk = r + A
    parts.append(ext(poly([(-1.0, rk - 0.4), (1.0, rk - 0.4), (1.4, rk + 2.4), (-1.4, rk + 2.4)]), 0.0, 1.4))
    parts.append(chamfer_box(-rk - 1.8, -1.2, rk + 1.8, 0.01, 0.0, 1.4, c=0.4, bottom=1.4))
    return O._one_piece(sash, parts, op, plug_cs, pl, rk + 2.4, -1.2)


# ================================================================== the Bethel cottages (house 105)
# After the camp-meeting cottages of the Wesleyan Grove camp ground at Oak Bluffs, Martha's
# Vineyard (1860s-70s): tall, narrow Carpenter Gothic cottages that replaced the tents round the
# preaching ground, each a steep front gable a storey and a half high, Gothic double doors
# below, a door onto a balcony over the porch above, the gable edged in deep jigsaw lace, and
# each painted in its own bright colours. Three of them stand on an arc round a green; each
# has its own siding, lace, railing and side.

def bb_bethel(region, datum=0.0, pitch=2.4, batten=0.8, d=0.45):
    """Board and batten: vertical battens over plain boards (cottage A)."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    bats = cs_union([rect(u - batten / 2, v0 - 1, u + batten / 2, v1 + 1) for u in np.arange(u0 + pitch / 2, u1, pitch)]) ^ region
    return _st(bats, 0.0, d) + M.extrude(region, 0.05)


def clap_bethel(region, datum=0.0, pitch=1.1, d=0.4):
    """Narrow clapboards, the butt of each course standing proud (cottage B)."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    k0 = math.floor((v0 - datum) / pitch) - 1
    bds = [rect(u0 - 1, datum + k * pitch + 0.45, u1 + 1, datum + (k + 1) * pitch) for k in range(k0, int((v1 - datum) / pitch) + 2)]
    return _st(cs_union(bds) ^ region, 0.0, d) + M.extrude(region, 0.05)


def bands_bethel(region, datum=0.0):
    """Clapboards with a band of diamond-cut shingles every eighth course (cottage C)."""
    from .core import scallop_rows
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    out = [M.extrude(region, 0.05)]
    pitch = 1.2
    k0 = math.floor((v0 - datum) / pitch) - 1
    k1 = int((v1 - datum) / pitch) + 2
    clap, shing = [], []
    for k in range(k0, k1):
        vb = datum + k * pitch
        (shing if k % 8 in (5, 6, 7) else clap).append(rect(u0 - 1, vb + (0.45 if k % 8 not in (5, 6, 7) else 0.0), u1 + 1, vb + pitch))
    if clap:
        out.append(_st(cs_union(clap) ^ region, 0.0, 0.4))
    if shing:
        reg = cs_union(shing) ^ region
        if not reg.is_empty():
            out.append(scallop_rows(reg, 1.2, 1.8, d=0.4, shape="diamond", datum=datum))
    return union(out)


def _barge_band(L, slope, d_eave, skin, width):
    s = slope
    c = math.hypot(1.0, s)
    a_l = np.array([-d_eave, 0.0])
    tip = np.array([L / 2, s * (L / 2 + d_eave)])
    a_r = np.array([L + d_eave, 0.0])
    depth = skin + width
    band = []
    for a in (a_l, a_r):
        n = np.array([s, -1.0]) / c if a[0] < L / 2 else np.array([-s, -1.0]) / c
        band.append(poly([tuple(a), tuple(tip), tuple(tip + n * depth), tuple(a + n * depth)]))
    board = cs_union(band) ^ rect(-d_eave - 5, -0.01, L + d_eave + 5, tip[1] + 5)
    return board, a_l, tip, a_r, depth, c


def barge_bethel(L, slope, d_eave, kind="a", skin=1.8, width=3.4, d=1.4, finial=6.0, tab=0.0):
    """A cottage's jigsaw bargeboard (facade frame of the gable wall, hung on the rake's end):
    kind "a": a deep band pierced with a row of circles, scalloped below, a drop at each
    scallop; "b": a band of hearts pierced through, its edge a run of points; "c": a fringe of
    teardrops hanging from a band, tied along their tips by a second band. Each has a pendant
    and a spike finial at the apex, and every accent is tied into the board."""
    board, a_l, tip, a_r, depth, c = _barge_band(L, slope, d_eave, skin, width)
    s = slope
    holes, extra = [], []
    run = float(np.linalg.norm(tip - a_l))
    for a in (a_l, a_r):
        n = np.array([s, -1.0]) / c if a[0] < L / 2 else np.array([-s, -1.0]) / c
        dirv = (tip - a) / np.linalg.norm(tip - a)
        step = 3.0
        for k in range(1, int(run / step)):
            p = a + dirv * (step * k)
            if kind == "a":
                holes.append(circle(tuple(p + n * (skin + width * 0.5)), 0.75, 16))
                extra.append(circle(tuple(p + n * (depth + 0.4)), 0.9, 16) - circle(tuple(p + n * (depth + 1.6)), 1.0, 16))
                if k % 2 == 0:
                    q = p + n * (depth + 1.3)
                    extra.append(cs_union([stroke([tuple(p + n * depth), tuple(q)], 1.0), circle(tuple(q + n * 0.5), 0.7, 14)]))
            elif kind == "b":
                hc = p + n * (skin + width * 0.5)
                hh = cs_union([circle(tuple(hc + dirv * 0.45 - n * 0.25), 0.55, 12), circle(tuple(hc - dirv * 0.45 - n * 0.25), 0.55, 12),
                               poly([tuple(hc + dirv * 0.95 - n * 0.2), tuple(hc - dirv * 0.95 - n * 0.2), tuple(hc + n * 0.95)])])
                holes.append(hh)
                extra.append(poly([tuple(p + n * (depth - 0.01) - dirv * 1.4), tuple(p + n * (depth - 0.01) + dirv * 1.4),
                                   tuple(p + n * (depth + 1.4))]))
            else:
                q = p + n * (depth + 2.8)
                extra.append(cs_union([stroke([tuple(p + n * depth), tuple(q)], 1.1), circle(tuple(q), 0.9, 14)]))
        if kind == "c":
            b0 = a + n * (depth + 2.6)
            extra.append(poly([tuple(b0), tuple(tip + n * (depth + 2.6)), tuple(tip + n * (depth + 3.6)), tuple(b0 + n * 1.0)]))
    xc = L / 2
    pend = cs_union([rect(xc - 0.6, tip[1] - depth * c - 6.0, xc + 0.6, tip[1] - depth * c + 0.4),
                     circle((xc, tip[1] - depth * c - 6.4), 1.0, 18)])
    spike = poly([(xc - 0.8, tip[1] - 0.2), (xc + 0.8, tip[1] - 0.2), (xc + 0.5, tip[1] + finial * 0.6), (xc, tip[1] + finial),
                  (xc - 0.5, tip[1] + finial * 0.6)])
    cs_ = cs_union([board] + extra + [pend, spike]) - cs_union(holes)
    cs_ = cs_ ^ rect(-d_eave - 6, -6.0, L + d_eave + 6, tip[1] + finial + 1)
    out = _text(_tie(cs_), 0.0, d)
    if tab > 0.0:
        # a glue tab along the board's top edge, running back ``tab`` under the rake's soffit
        # (the caller cuts the roof from it, leaving the strip under the skin)
        strip = []
        for a in (a_l, a_r):
            n = np.array([s, -1.0]) / c if a[0] < L / 2 else np.array([-s, -1.0]) / c
            strip.append(poly([tuple(a), tuple(tip), tuple(tip + n * (skin + 0.8)), tuple(a + n * (skin + 0.8))]))
        out = out + ext(cs_union(strip) ^ rect(-d_eave - 5, -0.01, L + d_eave + 5, tip[1] + 5), -tab, 0.02)
    return out


def door_btdouble(w=13.0, h=24.0, A=1.0):
    """The cottage's Gothic double doors: two tall leaves under one pointed arch, each leaf with
    a long pointed light over a panel, a pierced trefoil in the arch's head; a casing that
    follows the arch, a hood moulding with returns."""
    from .grand import _apex
    apx = _apex(w)
    vs = h - apx
    from .grand import _lancet
    op = _lancet(-w / 2, w / 2, vs, v0=0.0)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    parts_s = [ext(plug_cs - plug_cs.offset(-0.5, MIT, 4.0), -pl, 0.0), ext(plug_cs, -pl, -0.6)]
    lights = []
    for sg in (-1, 1):
        a, b_ = sorted((sg * 0.9, sg * (w / 2 - 1.1)))
        la = _lancet(a, b_, vs - 3.0, v0=h * 0.42)
        lights.append(la)
    head = poly([(-w / 2 + 1.0, vs + 0.6), (w / 2 - 1.0, vs + 0.6), (0.0, h - 1.2)])
    glass = cs_union(lights)
    parts_s = [p - ext(glass, -pl - 1, 0.0) for p in parts_s]
    parts_s.append(ext(glass, -pl, -pl + O.GLASS))
    parts_s.append(ext(rect(-0.3, 0.0, 0.3, vs + 0.6), -0.65, -0.1))                    # the meeting stile
    for sg in (-1, 1):
        a, b_ = sorted((sg * 0.9, sg * (w / 2 - 1.1)))
        pan = rect(a, 1.2, b_, h * 0.42 - 1.0)
        parts_s.append(ext(pan - pan.offset(-0.45, MIT, 4.0), -0.65, -0.2))
    from .grand import _trefoil
    tre = _trefoil((0.0, (vs + h) / 2), min(1.6, apx * 0.22))
    parts_s.append(ext(_clean(head.offset(-0.3, MIT, 4.0) - tre), -0.65, -0.2))
    X = w / 2 + A
    outer = _lancet(-X, X, vs, v0=0.0)
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS), ext(outer - op, 0.0, 0.9)]
    hood = _lancet(-X - 1.0, X + 1.0, vs, v0=vs - 1.0) - _lancet(-X + 0.1, X - 0.1, vs, v0=vs - 2.0)
    parts.append(ext(hood ^ rect(-50, vs - 1.0, 50, 100), 0.0, 1.3))
    for sg in (-1, 1):
        parts.append(chamfer_box(min(sg * (X + 1.0), sg * (X - 0.2)), vs - 2.0, max(sg * (X + 1.0), sg * (X - 0.2)), vs - 0.9, 0.0, 1.3, c=0.3))
    parts_s = [m ^ ext(plug_cs, -pl - 1.0, 1.0) for m in parts_s]
    top = h + A + 1.2
    return O._one_piece(parts_s, parts, op, plug_cs, pl, top, 0.0)


def window_btpointed(w=7.0, h=16.0, A=0.8, label=True):
    """The cottage's pointed window: a pair of casements under a lancet head, a Y bar in the
    head, a label moulding with stops; a sill."""
    from .grand import _apex, _lancet
    apx = _apex(w)
    vs = h - apx
    op = _lancet(-w / 2, w / 2, vs, v0=0.0)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    inner = plug_cs.offset(-0.6, MIT, 4.0)
    bars = cs_union([rect(-RIB / 2, -1.0, RIB / 2, vs + apx * 0.35), rect(-w, vs * 0.5 - RIB / 2, w, vs * 0.5 + RIB / 2),
                     stroke([(0.0, vs + apx * 0.3), (-w / 2, h)], RIB), stroke([(0.0, vs + apx * 0.3), (w / 2, h)], RIB)])
    sash = _glazed([ext(plug_cs, -pl, -0.6)], inner, pl, bars, plug_cs)
    X = w / 2 + A
    outer = _lancet(-X, X, vs, v0=0.0)
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS), ext(outer - op, 0.0, 0.8)]
    if label:
        lab = _lancet(-X - 0.9, X + 0.9, vs, v0=vs - 0.8) - _lancet(-X + 0.05, X - 0.05, vs, v0=vs - 2.0)
        parts.append(ext(lab ^ rect(-50, vs - 0.8, 50, 100), 0.0, 1.2))
        for sg in (-1, 1):
            parts.append(chamfer_box(min(sg * (X + 0.9), sg * X), vs - 2.2, max(sg * (X + 0.9), sg * X), vs - 0.79, 0.0, 1.2, c=0.3))
    parts.append(chamfer_box(-X - 0.8, -1.2, X + 0.8, 0.01, 0.0, 1.3, c=0.3, bottom=1.3))
    top = h + A + (0.9 if label else 0.0)
    return O._one_piece(sash, parts, op, plug_cs, pl, top, -1.2)


def window_bttrefoil(r=3.4, A=0.8):
    """The gable's peak light: a trefoil in a round frame."""
    from .grand import _trefoil
    op = _trefoil((0.0, r), r * 0.82)
    op = cs_union([op, circle((0.0, r), r * 0.5, 24)])
    plug_cs = op.offset(-O.CLR, RND)
    pl = O.PLUG
    inner = plug_cs.offset(-0.5, RND)
    sash = _glazed([ext(plug_cs, -pl, -0.6)], inner, pl, circle((0.0, r), 0.7, 16), plug_cs)
    ring = circle((0.0, r), r + A + 0.6, 40) - op
    parts = [ext(op - op.offset(-RIB, RND), 0.0, O.CAS), ext(ring, 0.0, 0.9)]
    return O._one_piece(sash, parts, op, plug_cs, pl, 2 * r + A + 0.6, -A - 0.6)


def rail_bethel(L, h=7.0, kind="a", t=1.0):
    """A balcony railing strip (flat; u along, v up, w 0..t; prints on its back): a top and a
    bottom rail on end posts, and between them kind "a": flat sawn balusters with a heart cut in
    each, "b": crossed sticks with a ring at every crossing, "c": pierced panels each with a
    tulip; tabs under the bottom rail for slots in the porch roof."""
    parts = [rect(0.0, 0.0, L, 0.8), rect(0.0, h - 1.0, L, h), rect(0.0, 0.0, 1.0, h), rect(L - 1.0, 0.0, L, h)]
    holes = []
    vb, vt = 0.8, h - 1.0
    H = vt - vb
    if kind == "a":
        n = max(1, int((L - 2.0) / 1.9))
        for k in range(n):
            u = 1.0 + (L - 2.0) * (k + 0.5) / n
            parts.append(rect(u - 0.6, vb, u + 0.6, vt))
            hc = (u, vb + H * 0.55)
            holes.append(cs_union([circle((u - 0.22, hc[1] + 0.2), 0.25, 10), circle((u + 0.22, hc[1] + 0.2), 0.25, 10)]))
        out = cs_union(parts)
    elif kind == "b":
        n = max(1, int(round((L - 2.0) / (H * 1.2))))
        for k in range(n):
            a, b_ = 1.0 + (L - 2.0) * k / n, 1.0 + (L - 2.0) * (k + 1) / n
            parts += [stroke([(a, vb), (b_, vt)], 0.7), stroke([(a, vt), (b_, vb)], 0.7)]
            parts.append(circle(((a + b_) / 2, vb + H / 2), 1.0, 16) - circle(((a + b_) / 2, vb + H / 2), 0.45, 12))
        out = _clean(cs_union(parts))
    else:
        n = max(1, int((L - 2.0) / 3.6))
        for k in range(n):
            a, b_ = 1.0 + (L - 2.0) * k / n, 1.0 + (L - 2.0) * (k + 1) / n
            parts.append(rect(a, vb, b_, vt))
            uc = (a + b_) / 2
            tul = cs_union([circle((uc, vb + H * 0.55), 0.75, 14), circle((uc - 0.55, vb + H * 0.72), 0.4, 10),
                            circle((uc + 0.55, vb + H * 0.72), 0.4, 10)])
            holes.append(tul)
            holes.append(rect(uc - 0.25, vb + 0.6, uc + 0.25, vb + H * 0.4))
            parts.append(rect(a - 0.3, vb, a + 0.3, vt))
        out = cs_union(parts)
    out = out - cs_union(holes) if holes else out
    for u in (L * 0.25, L * 0.75):
        out = out + rect(u - 1.2, -0.8, u + 1.2, 0.01)
    return ext(out, 0.0, t)


def post_bethel(h, collar=None, abacus=2.8, slot=None):
    """The cottages' porch post: a slender round shaft with a ring a third up and a little
    bulb under the cap (sawn work hangs from the beam between them)."""
    from .porchwork import _plinth, _revolve, _top
    z1 = h - 2.6
    zr = 1.2 + (z1 - 1.2) * 0.35
    prof = [(0.0, 1.19), (1.1, 1.19), (0.95, 1.6), (0.95, zr - 0.3), (1.2, zr), (0.95, zr + 0.3), (0.95, z1 - 1.6),
            (1.25, z1 - 1.0), (1.0, z1 - 0.4), (1.0, z1)]
    body = _revolve(prof) + _plinth(2.6, 1.2)
    return body + _top(h, abacus / 2, z1, 1.0, slot, seg=36)


def spandrel_btlace(u0, u1, v_bot, v_top):
    """The cottages' porch lace: a shallow pointed arch of sawn work between the posts, a
    roundel pierced in each spandrel, drops along the arch."""
    H = v_top - v_bot
    xc = (u0 + u1) / 2
    w = u1 - u0
    pts = [(u0, v_bot)]
    for t in np.linspace(0, 1, 16):
        x = u0 + w * t
        y = v_bot + H * 0.75 * (1 - abs(2 * t - 1)) ** 0.6
        pts.append((x, y))
    pts += [(u1, v_bot), (u1, v_top), (u0, v_top)]
    band = poly(pts)
    inner = band.offset(-0.9, RND)
    out = band - (inner ^ rect(u0, v_bot - 1, u1, v_bot + H * 0.6))
    for sg in (-1, 1):
        cx = xc + sg * w * 0.33
        out = out - circle((cx, v_top - H * 0.32), min(0.8, H * 0.18), 16)
    for t in np.linspace(0.2, 0.8, 4):
        x = u0 + w * t
        y = v_bot + H * 0.75 * (1 - abs(2 * t - 1)) ** 0.6
        out = out + cs_union([rect(x - 0.35, y - 1.6, x + 0.35, y + 0.2), circle((x, y - 1.8), 0.55, 12)])
    return _clean(out, 0.22) ^ rect(u0, v_bot - 3.0, u1, v_top + 0.01)


def skirt_btlattice(reg, d=1.2):
    """The cottages' skirt between the piers: a lattice of diagonal laths."""
    u0, v0, u1, v1 = reg.bounds()
    la = cs_union([stroke([(u, v0 - 2), (u + (v1 - v0) + 4, v1 + 2)], 0.6) for u in np.arange(u0 - (v1 - v0) - 4, u1, 1.8)])
    lb = cs_union([stroke([(u, v1 + 2), (u + (v1 - v0) + 4, v0 - 2)], 0.6) for u in np.arange(u0 - (v1 - v0) - 4, u1, 1.8)])
    return M.extrude(la ^ reg, d / 2) + M.extrude(lb ^ reg, d / 2).translate([0, 0, d / 2])


def frieze_btpennant(L, h, b, pitch, margin, pair, half):
    """The cottages' storey frieze: a row of hanging pennants (sawn points), a bead over them."""
    v1 = h - 0.4
    out = [_st(rect(0.2, v1 - 0.7, L - 0.2, v1), b, 0.35)]
    pw = 1.8
    n = max(1, int((L - 0.6) / pw))
    u0 = (L - n * pw) / 2
    pens = [poly([(u0 + pw * k + 0.15, v1 - 0.69), (u0 + pw * (k + 1) - 0.15, v1 - 0.69), (u0 + pw * (k + 0.5), 0.5)]) for k in range(n)]
    out.append(_st(cs_union(pens), b, 0.35))
    return out, []


def course_btspool(L, h, b, pitch, margin, p):
    """A course of little turned spools (beads and reels), the cottages' eave."""
    rod = rect(0.2, 0.25, L - 0.2, h - 0.25)
    out = [_st(rod, b, 0.15)]
    sp = []
    u = 0.6
    while u < L - 0.9:
        sp.append(rect(u, 0.3, u + 0.9, h - 0.3))
        u += 1.4
    out.append(_st(cs_union(sp), b + 0.15, 0.3))
    return out


PW.POSTS.update(bethel=post_bethel)
PW.FRIEZES.update(btlace=spandrel_btlace)
PW.SKIRTS.update(btlattice=skirt_btlattice)
CO.FRIEZE_EXTRA.update(btpennant=frieze_btpennant)
CO.COURSE_EXTRA.update(btspool=course_btspool)


def fill_btsawn(L, vb, vt):
    """The cottages' porch railing: flat sawn balusters, each waisted, with a diamond cut in
    its widest part."""
    H = vt - vb
    n = max(1, int(round(L / 1.8)))
    out, holes = [], []
    for k in range(n):
        u = L * (k + 0.5) / n
        out.append(poly([(u - 0.45, vb), (u + 0.45, vb), (u + 0.75, vb + H * 0.35), (u + 0.45, vb + H * 0.55), (u + 0.75, vb + H * 0.75),
                         (u + 0.45, vt), (u - 0.45, vt), (u - 0.75, vb + H * 0.75), (u - 0.45, vb + H * 0.55), (u - 0.75, vb + H * 0.35)]))
    return [cs_union(out)]


def edge_btscallop(L, z0, zc):
    """The cottages' porch roof edge: a scalloped valance board under a plain fascia."""
    n = max(1, int((L - 1.0) / 2.0))
    sc = cs_union([circle((0.5 + (L - 1.0) * (k + 0.5) / n, z0 + 0.2), 0.95, 16) for k in range(n)])
    cs = (sc + rect(0.3, z0 + 0.2, L - 0.3, zc)) ^ rect(0.3, z0 - 1.0, L - 0.3, zc)
    return cs, 0.6


PW.FILLS.update(btsawn=fill_btsawn)
FT.EDGE_EXTRA.update(btscallop=edge_btscallop)


# ================================================================== the Piney (house 106)
# After Woodland, Sam Houston's dogtrot house at Huntsville, Texas (1847), and the dogtrot
# farmhouses of the Gulf states: two pens of hewn logs under one long roof with the open,
# floored breezeway (the dogtrot) between them, so you see straight through the house; a
# full-width porch on cedar posts; fat fieldstone chimneys outside both gable ends; the whole
# house up on dry-laid fieldstone piers over a swept clay yard; the kitchen in its own log
# cabin behind, reached by a covered walk, its chimney of sticks and clay.

def _hash01(k, salt=0):
    """A repeatable number in [0, 1) for an integer (the same on every face of a building)."""
    return ((k * 7919 + salt * 104729) % 1009) / 1009.0


def log_piney(region, datum=0.0, pitch=3.4, chink=0.7, d=0.55, L=None, shift=0.0, end=1.1):
    """Hewn logs laid up with chinking: each course a squared log face standing ``d`` proud of
    the chinking, its edges broken by the adze (chamfered), the courses a little uneven (the
    same on every face, so they meet at the corners). ``shift`` (a fraction of the pitch) sets
    this face's courses against its neighbour's: logs in the two walls of a corner sit half a
    log apart. With ``L`` (the face's length) the ends of the crossing wall's logs show at the
    corners, ``end`` wide and a little proud: the dovetailed corner."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    out = [M.extrude(region, 0.05)]

    def courses(sh, a, b, dd, c):
        k0 = math.floor((v0 - datum) / pitch - sh) - 1
        k1 = math.ceil((v1 - datum) / pitch - sh) + 1
        lines = {k: datum + (k + sh) * pitch + (_hash01(k) - 0.5) * 0.5 for k in range(k0, k1 + 2)}
        wds = {k: chink * (0.8 + 0.4 * _hash01(k, 3)) for k in lines}
        logs = []
        for k in range(k0, k1 + 1):
            lo, hi = lines[k] + wds[k] / 2, lines[k + 1] - wds[k + 1] / 2
            if hi - lo < 1.0 or hi < v0 - 0.5 or lo > v1 + 0.5:
                continue
            logs.append(chamfer_box(a, lo, b, hi, 0.0, dd, c=c, square=("u0", "u1"), bottom=min(dd, c + 0.15)))
        return union(logs) if logs else M()

    reg = M.extrude(region.offset(0.01, MIT, 4.0), 5.0).translate([0, 0, -1.0])
    if L is None:
        out.append(courses(shift, u0 - 1.0, u1 + 1.0, d, 0.25) ^ reg)
    else:
        out.append(courses(shift, end, L - end, d, 0.25) ^ reg)
        for a, b in ((-0.5, end), (L - end, L + 0.5)):
            out.append(courses(shift + 0.5, a, b, d + 0.2, 0.3) ^ reg)
    return union(out)


def pier_piney(w=4.4, h=7.8, seed=0):
    """A dry-laid fieldstone pier: flat stones stacked, each a little out of square and out of
    line with the one under it (never more than a nozzle's reach), a broad flat one on top."""
    rng = np.random.default_rng(seed)
    z, out = 0.0, []
    while z < h - 0.05:
        t = round(rng.uniform(1.2, 1.8) / 0.2) * 0.2
        if h - z - t < 1.0:                       # the last stone takes what is left
            t = h - z
        hw = w / 2 + rng.uniform(-0.25, 0.15)
        pts = []
        for k, a in enumerate(np.linspace(0, 2 * math.pi, 9, endpoint=False) + rng.uniform(0, 0.6)):
            r = hw * (1.25 if k % 2 == 0 else 1.05) * rng.uniform(0.9, 1.0)
            pts.append((r * math.cos(a), r * math.sin(a)))
        cs = poly(pts) ^ rect(-hw, -hw, hw, hw)
        # each stone's foot is set back a little (the joint), and overlaps the stone under it
        out.append(M.extrude(cs.offset(-0.25, RND), 0.23).translate([0, 0, z - 0.02]) + M.extrude(cs, t - 0.2).translate([0, 0, z + 0.2]))
        z += t
    return union(out)


def chimney_piney(w0=22.0, d0=11.0, zf=34.0, w1=11.0, d1=8.0, zs=46.0, top=92.0, seed=0):
    """A Gulf-coast fieldstone end chimney, standing on z = 0 with its back on the gable wall
    (local y = 0, the stack running out to +y): a broad firebox base, sloped stone shoulders
    (weatherings) stepping in to the stack, the stack up past the ridge to a corbelled cap;
    rubble faces, every course a different height."""
    def face(reg, i):
        return ashlar(reg, course=(1.2, 2.2), length=(1.4, 3.6), d=0.4, seed=seed + 5 * i, rough=0.22, bevel=0.25)
    zf, zs, top = (round(z / 0.2) * 0.2 for z in (zf, zs, top))
    base = box([-w0 / 2, 0.0, 0.0], [w0 / 2, d0, zf])
    sh = M.hull_points([(x, y, zf - 0.01) for x in (-w0 / 2, w0 / 2) for y in (0.0, d0)] +
                       [(x, y, zs) for x in (-w1 / 2, w1 / 2) for y in (0.0, d1)])
    stack = box([-w1 / 2, 0.0, zs - 0.01], [w1 / 2, d1, top - 2.4])
    out = [base, sh, stack]
    for (w, d, z0, z1) in ((w0, d0, 0.6, zf - 0.4), (w1, d1, zs + 0.4, top - 2.8)):
        from .core import Facade
        for i, f in enumerate((Facade((w / 2, 0.0), (w / 2, d)), Facade((w / 2, d), (-w / 2, d)), Facade((-w / 2, d), (-w / 2, 0.0)))):
            out.append(f.place(face(rect(0.15, z0, f.L - 0.15, z1), i + (0 if w == w0 else 3)).translate([0, 0, -0.02])))
    # the cap: a band of bigger stones corbelled out at 45 degrees, a flat slab, the flue
    g = 0.7
    out.append(M.hull_points([(x, y, top - 2.4 - g) for x in (-w1 / 2, w1 / 2) for y in (0.0, d1)] +
                             [(x, y, top - 2.4) for x in (-w1 / 2 - g, w1 / 2 + g) for y in (0.0, d1 + g)]))
    out.append(box([-w1 / 2 - g, 0.0, top - 2.41], [w1 / 2 + g, d1 + g, top - 0.8]))
    out.append(box([-w1 / 2 - 0.2, 0.0, top - 0.81], [w1 / 2 + 0.2, d1 + 0.2, top]))
    body = union(out)
    return body - box([-w1 / 2 + 1.6, 1.4, top - 2.0], [w1 / 2 - 1.6, d1 - 1.4, top + 1.0])


def chimney_pnstick(w0=15.0, d0=9.0, zb=12.0, w1=9.0, d1=6.0, top=58.0):
    """The kitchen's chimney, stick and clay ("catted"): a fieldstone firebox up to ``zb``, then
    a tapering stack of split sticks laid up like a crib and daubed with clay, the sticks'
    ends and lines showing through, and the long prop pole leaning on it (pushed over if it
    ever caught fire). Back on the gable wall at local y = 0, running out to +y.
    Returns (solid, the height of its colour change: stone below, clay above)."""
    zb, top = round(zb / 0.2) * 0.2, round(top / 0.2) * 0.2
    base = box([-w0 / 2, 0.0, 0.0], [w0 / 2, d0, zb])
    from .core import Facade
    out = [base]
    for i, f in enumerate((Facade((w0 / 2, 0.0), (w0 / 2, d0)), Facade((w0 / 2, d0), (-w0 / 2, d0)), Facade((-w0 / 2, d0), (-w0 / 2, 0.0)))):
        out.append(f.place(ashlar(rect(0.15, 0.6, f.L - 0.15, zb - 0.3), course=(1.2, 2.0), length=(1.4, 3.2), d=0.4, seed=40 + i,
                                  rough=0.2, bevel=0.25).translate([0, 0, -0.02])))
    stack = M.hull_points([(x, y, zb - 0.01) for x in (-w0 / 2 + 0.6, w0 / 2 - 0.6) for y in (0.0, d0 - 0.6)] +
                          [(x, y, top) for x in (-w1 / 2, w1 / 2) for y in (0.0, d1)])
    out.append(stack)
    # the sticks: a band every 1.6 mm standing proud of the daub, wrapping the three faces,
    # each band following the taper (a thin slice of the stack grown out)
    for z in np.arange(zb + 1.0, top - 1.2, 1.6):
        bnd = M.hull(stack ^ box([-50, -1, z], [50, 50, z + 0.6]))
        bb = bnd.bounding_box()                    # centred in x, its back on y = 0: scaling grows it outward
        sx = (bb[3] - bb[0] + 0.7) / max(1e-6, bb[3] - bb[0])
        sy = (bb[4] - bb[1] + 0.35) / max(1e-6, bb[4] - bb[1])
        out.append(bnd.scale([sx, sy, 1.0]))
    # the prop: a pole from the ground out beside the chimney up against its stack
    out.append(M.hull_points([(w0 / 2 + 3.6 + dx, d0 + 6.0 + dy, 0.0) for dx in (-0.5, 0.5) for dy in (-0.5, 0.5)] +
                             [(w1 / 2 + 0.2 + dx, d1 * 0.6 + dy, top * 0.7) for dx in (-0.5, 0.5) for dy in (-0.5, 0.5)]))
    body = union(out)
    body = body - box([-w1 / 2 + 1.4, 1.2, top - 1.6], [w1 / 2 - 1.4, d1 - 1.2, top + 1.0])
    return body, zb


def yard_piney(region, seed=0, n=60):
    """A swept yard: the broom's fans of shallow arcs scratched into the clay (to cut from its
    top face, 0.25 deep)."""
    rng = np.random.default_rng(seed)
    u0, v0, u1, v1 = region.bounds()
    arcs = []
    for _ in range(n):
        c = (rng.uniform(u0, u1), rng.uniform(v0, v1))
        r = rng.uniform(5.0, 13.0)
        a0 = rng.uniform(0, 2 * math.pi)
        span = rng.uniform(0.8, 1.6)
        for dr in (0.0, 1.1, 2.2):
            pts = [(c[0] + (r + dr) * math.cos(a), c[1] + (r + dr) * math.sin(a)) for a in np.linspace(a0, a0 + span, 12)]
            arcs.append(stroke(pts, 0.45))
    return M.extrude(cs_union(arcs) ^ region, 0.6).translate([0, 0, -0.25])


def woodpile_piney(L=16.0, d=7.0, h=6.0):
    """A cord of split stovewood on two skids: the split ends (wedges, quarters, halves) show
    on both end faces, bark lines run along the top."""
    out = [box([0.0, 0.0, 0.0], [L, d, h])]
    for x in (1.2, L - 2.4):                                          # skids
        out.append(box([x, -0.6, 0.0], [x + 1.2, d + 0.6, 0.8]))
    rng = np.random.default_rng(3)
    cuts = []
    for z0 in np.arange(1.0, h - 0.5, 1.6):
        y = 0.3
        while y < d - 0.8:
            s = rng.uniform(1.2, 1.8)
            pts = [(y, z0), (y + s, z0), (y + s * rng.uniform(0.3, 0.7), z0 + 1.4)]
            tri = poly(pts)
            cuts.append(tri - tri.offset(-0.3, MIT, 4.0))
            y += s + 0.15
    ends = cs_union(cuts) ^ rect(0.2, 0.9, d - 0.2, h - 0.2)
    for x0, x1 in ((-0.3, 0.0), (L, L + 0.3)):                         # the ends, wedge outlines proud
        out.append(M.extrude(ends, x1 - x0).transform(np.array([[0, 0, 1.0, x0], [1.0, 0, 0, 0], [0, 1.0, 0, 0]])))
    top = union([box([0.4, y, h - 0.01], [L - 0.4, y + 0.5, h + 0.3]) for y in np.arange(0.5, d - 0.5, 1.1)])
    return union(out) + top


# ---- cornice ornaments
def frieze_pnjoists(L, h, b, pitch, margin, pair, half):
    """The eave's frieze: the loft joists' squared ends in a row under a plain plate board,
    each end adzed (chamfered) all round."""
    v0, v1 = 0.3, h - 0.3
    out = [_st(rect(0.2, v1 - 1.0, L - 0.2, v1), b, 0.4)]
    sp = 3.0
    n = max(1, int((L - 1.6) / sp))
    us = [(L - (n - 1) * sp) / 2 + k * sp for k in range(n)]
    for u in us:
        out.append(chamfer_box(u - 0.75, v0, u + 0.75, v1 - 1.0, b, 0.9, c=0.25, bottom=0.9))
    return out, []


def course_pnbead(L, h, b, pitch, margin, p):
    """A beaded board: a plain band with a round bead along its foot."""
    out = [_st(rect(0.2, 0.2, L - 0.2, h - 0.2), b, 0.25)]
    out.append(_st(rect(0.2, 0.25, L - 0.2, 0.75), b + 0.25, 0.3))
    return out


def course_pnnotch(L, h, b, pitch, margin, p):
    """The kitchen's eave board: its lower edge sawn into a row of points."""
    vb = h * 0.45
    teeth = [poly([(u - 0.55, vb + 0.01), (u + 0.55, vb + 0.01), (u, 0.25)]) for u in np.arange(0.8, L - 0.6, 1.2)]
    return [_st(rect(0.2, vb, L - 0.2, h - 0.2), b, 0.35), _st(cs_union(teeth) ^ rect(0.2, 0.0, L - 0.2, h), b, 0.3)]


CO.FRIEZE_EXTRA.update(pnjoists=frieze_pnjoists)
CO.COURSE_EXTRA.update(pnbead=course_pnbead, pnnotch=course_pnnotch)


# ---- windows, doors, shutters
def window_pnsash(w=11.0, h=17.0, A=1.4):
    """The pens' window, frontier Greek Revival: six over six in a wide board casing with a
    bead down its inner edge; over it a frieze board, a drip and a low peaked head; a sill on
    two little sawn brackets."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    sash = _sash66(w, h, pl, plug_cs)
    X = w / 2 + A
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             ext((op.offset(A, MIT, 4.0) - op) ^ rect(-50, 0.0, 50, 100), 0.0, 0.8),
             ext((op.offset(0.5, MIT, 4.0) - op) ^ rect(-50, 0.0, 50, 100), 0.0, 1.0)]
    vh = h + A - 0.01
    parts.append(ext(rect(-X, vh, X, vh + 1.8), 0.0, 0.8))
    parts.append(chamfer_box(-X - 0.9, vh + 0.6, X + 0.9, vh + 1.8, 0.0, 1.3, c=0.3, bottom=1.0))
    ped = poly([(-X - 0.9, vh + 1.79), (X + 0.9, vh + 1.79), (X + 0.9, vh + 2.4), (0.0, vh + 4.0), (-X - 0.9, vh + 2.4)])
    parts.append(ext(ped, 0.0, 1.1))
    parts.append(chamfer_box(-X - 0.8, -1.2, X + 0.8, 0.01, 0.0, 1.5, c=0.3, bottom=1.5))
    for sg in (-1, 1):
        u = sg * (X - 0.6)
        parts.append(ext(poly([(u - 0.5, -1.19), (u + 0.5, -1.19), (u + 0.15, -2.6), (u - 0.15, -2.6)]), 0.0, 1.1))
    return O._one_piece(sash, parts, op, plug_cs, pl, vh + 4.0, -2.6)


def window_pnloft(w=7.0, h=7.0, A=1.0):
    """The loft's light in the gable: a pair of casements of two lights each, a plain casing
    all round, a drip cap over and a little sill."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    inner = plug_cs.offset(-0.6, MIT, 4.0)
    bars = cs_union([rect(-0.4, -1.0, 0.4, h + 1.0), rect(-w, h / 2 - RIB / 2, w, h / 2 + RIB / 2)])
    sash = _glazed([ext(plug_cs, -pl, -0.6)], inner, pl, bars, plug_cs)
    X = w / 2 + A
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS), ext(op.offset(A, MIT, 4.0) - op, 0.0, 0.8)]
    vh = h + A - 0.01
    parts.append(chamfer_box(-X - 0.6, vh, X + 0.6, vh + 1.4, 0.0, 1.2, c=0.3, bottom=1.0))
    parts.append(chamfer_box(-X - 0.4, -A - 0.8, X + 0.4, -A + 0.01, 0.0, 1.1, c=0.3, bottom=1.0))
    return O._one_piece(sash, parts, op, plug_cs, pl, vh + 1.4, -A - 0.8)


def _panels(parts_s, w, rows, m_=0.9):
    for (va, vb) in rows:
        for sg in (-1, 1):
            pan = rect(min(sg * 0.5, sg * (w / 2 - m_)), va, max(sg * 0.5, sg * (w / 2 - m_)), vb)
            parts_s.append(ext(pan - pan.offset(-0.45, MIT, 4.0), -0.65, -0.2))
            parts_s.append(chamfer_box(*pan.offset(-0.9, MIT, 4.0).bounds(), -0.65, 0.35, c=0.2))


def door_pnfront(w=10.0, h=22.0, A=1.6):
    """The pens' doors onto the porch, Greek Revival: two long panels over two short ones under
    a three-light transom, in an eared architrave (its head stepping out past the jambs) with a
    frieze board and a cornice cap; plinth blocks at the foot."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    vt = h - 3.6
    tr = rect(-w / 2 + 0.6, vt + 0.5, w / 2 - 0.6, h - 0.6)
    parts_s = [ext(plug_cs - plug_cs.offset(-0.5, MIT, 4.0), -pl, 0.0), ext(plug_cs, -pl, -0.6)]
    parts_s = [p_ - ext(tr, -pl - 1, 0.0) for p_ in parts_s]
    parts_s.append(ext(tr, -pl, -pl + O.GLASS))
    parts_s.append(ext(cs_union([rect(x - RIB / 2, vt, x + RIB / 2, h) for x in np.linspace(-w / 2, w / 2, 4)[1:-1]]) ^ tr.offset(0.1, MIT, 4.0),
                       -pl + O.GLASS - 0.01, -0.5))
    parts_s.append(ext(rect(-w / 2 + 0.4, vt - 0.1, w / 2 - 0.4, vt + 0.5), -0.65, -0.1))
    lh = (vt - 2.0) * 0.62
    _panels(parts_s, w, [(1.0, 1.0 + lh), (1.0 + lh + 0.9, vt - 0.9)])
    X = w / 2 + A
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             ext((op.offset(A, MIT, 4.0) - op) ^ rect(-50, 0.0, 50, 100), 0.0, 0.8),
             ext((op.offset(0.5, MIT, 4.0) - op) ^ rect(-50, 2.4, 50, 100), 0.0, 1.0)]
    vh = h + A - 0.01
    for sg in (-1, 1):                                   # the ears
        x0, x1 = sorted((sg * (X - 0.01), sg * (X + 0.9)))
        parts.append(ext(rect(x0, vh - 2.2, x1, vh), 0.0, 0.8))
        x0, x1 = sorted((sg * w / 2, sg * (X + 0.2)))
        parts.append(chamfer_box(x0, 0.0, x1, 2.4, 0.0, 1.1, c=0.25, square=("v0",)))
    parts.append(ext(rect(-X - 0.9, vh, X + 0.9, vh + 2.4), 0.0, 0.8))
    parts.append(chamfer_box(-X - 1.5, vh + 2.39, X + 1.5, vh + 3.4, 0.0, 1.5, c=0.3, bottom=1.0))
    return O._one_piece(parts_s, parts, op, plug_cs, pl, vh + 3.4, 0.0)


def door_pnbatten(w=9.0, h=21.0, A=1.2):
    """The pens' doors into the breezeway: a door of wide boards hung on long strap hinges, a
    wooden latch with its latch-string hole, a four-light transom; a plain casing with turned
    rosettes in square corner blocks."""
    from .colonial import _strap
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    vt = h - 3.6
    tr = rect(-w / 2 + 0.6, vt + 0.5, w / 2 - 0.6, h - 0.6)
    parts_s = [ext(plug_cs - plug_cs.offset(-0.5, MIT, 4.0), -pl, 0.0), ext(plug_cs, -pl, -0.6)]
    parts_s = [p_ - ext(tr, -pl - 1, 0.0) for p_ in parts_s]
    parts_s.append(ext(tr, -pl, -pl + O.GLASS))
    parts_s.append(ext(cs_union([rect(x - RIB / 2, vt, x + RIB / 2, h) for x in np.linspace(-w / 2, w / 2, 5)[1:-1]]) ^ tr.offset(0.1, MIT, 4.0),
                       -pl + O.GLASS - 0.01, -0.5))
    face = plug_cs.offset(-0.5, MIT, 4.0) ^ rect(-50, 0.3, 50, vt - 0.1)
    bds = cs_union([rect(x - 0.15, -1, x + 0.15, vt + 1) for x in np.arange(-w / 2 + 1.8, w / 2 - 1.0, 1.8)])
    parts_s.append(ext(_clean(face - bds, 0.12), -0.65, -0.3))
    fb = face.bounds()
    for v in (2.4, vt - 2.6):
        parts_s.append(ext(_strap(fb[0] + 0.1, fb[0] + (fb[2] - fb[0]) * 0.8, v) ^ face, -0.31, -0.1))
    parts_s.append(ext(rect(fb[2] - 2.4, vt * 0.48, fb[2] - 0.4, vt * 0.48 + 0.6), -0.31, -0.1))      # the latch bar
    parts_s.append(ext(circle((fb[2] - 1.2, vt * 0.48 + 1.4), 0.4, 12), -0.31, -0.1))               # its keeper
    X = w / 2 + A
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             ext((op.offset(A, MIT, 4.0) - op) ^ rect(-50, 0.0, 50, h + 0.01), 0.0, 0.8)]
    vh = h + A
    parts.append(ext(rect(-w / 2, h - 0.01, w / 2, vh), 0.0, 0.8))
    for sg in (-1, 1):                                   # corner blocks with rosettes
        cx = sg * (w / 2 + A / 2)
        parts.append(chamfer_box(cx - A / 2 - 0.2, h - 0.2, cx + A / 2 + 0.2, vh + 0.2, 0.0, 1.0, c=0.2))
        parts.append(ext(circle((cx, h + A / 2), 0.55, 16) - circle((cx, h + A / 2), 0.25, 12), 0.99, 1.3))
    parts.append(chamfer_box(-X - 0.6, vh + 0.19, X + 0.6, vh + 1.4, 0.0, 1.2, c=0.3, bottom=1.0))
    return O._one_piece(parts_s, parts, op, plug_cs, pl, vh + 1.4, 0.0)


def door_pndutch(w=8.4, h=19.0, A=1.0):
    """The kitchen's door: a Dutch door (the top leaf opens alone to let the heat out), boards
    with a Z brace on each leaf, a little shelf on the lower leaf's top rail, strap hinges; a
    board casing under a drip cap."""
    from .colonial import _strap
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    parts_s = [ext(plug_cs - plug_cs.offset(-0.5, MIT, 4.0), -pl, 0.0), ext(plug_cs, -pl, -0.6)]
    vm = round(h * 0.52 / 0.2) * 0.2
    face = plug_cs.offset(-0.5, MIT, 4.0)
    fb = face.bounds()
    for (va, vb) in ((fb[1] + 0.2, vm - 0.2), (vm + 0.2, fb[3] - 0.2)):
        leaf = face ^ rect(-50, va, 50, vb)
        bds = cs_union([rect(x - 0.15, -1, x + 0.15, 100) for x in np.arange(-w / 2 + 1.7, w / 2 - 1.0, 1.7)])
        parts_s.append(ext(_clean(leaf - bds, 0.12), -0.65, -0.3))
        z = cs_union([rect(fb[0] + 0.3, va + 0.5, fb[2] - 0.3, va + 1.3), rect(fb[0] + 0.3, vb - 1.3, fb[2] - 0.3, vb - 0.5),
                      stroke([(fb[0] + 0.8, va + 1.3), (fb[2] - 0.8, vb - 1.3)], 0.8)])
        parts_s.append(ext(z ^ leaf, -0.31, -0.05))
        for v in (va + 0.9, vb - 0.9):
            parts_s.append(ext(_strap(fb[0] + 0.1, fb[0] + (fb[2] - fb[0]) * 0.7, v) ^ face, -0.06, 0.1))
    parts_s.append(ext(rect(fb[0], vm - 0.2, fb[2], vm + 0.2), -0.65, -0.3))
    parts_s.append(chamfer_box(fb[0] - 0.2, vm - 1.0, fb[2] + 0.2, vm + 0.01, -0.3, 1.2, c=0.25, bottom=1.2))   # the shelf
    X = w / 2 + A
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             ext((op.offset(A, MIT, 4.0) - op) ^ rect(-50, 0.0, 50, 100), 0.0, 0.8)]
    vh = h + A - 0.01
    parts.append(chamfer_box(-X - 0.6, vh, X + 0.6, vh + 1.4, 0.0, 1.2, c=0.3, bottom=1.0))
    return O._one_piece(parts_s, parts, op, plug_cs, pl, vh + 1.4, 0.0)


def shutter_piney(w, h, t=0.8):
    """A batten shutter: wide boards held by two ledges and a brace (a Z), hung on strap
    hinges along the ledges. Local frame as features.shutter (u 0..w, v 0..h, back at w = 0;
    prints face-up)."""
    from .colonial import _strap
    body = ext(rect(0.0, 0.0, w, h), 0.0, t - 0.3)
    bds = cs_union([rect(u - 0.15, -1, u + 0.15, h + 1) for u in np.arange(1.6, w - 0.6, 1.6)])
    body = body - ext(bds, t - 0.55, t)
    la, lb = rect(0.3, h * 0.14, w - 0.3, h * 0.14 + 1.0), rect(0.3, h * 0.86 - 1.0, w - 0.3, h * 0.86)
    brace = stroke([(0.9, h * 0.14 + 1.0), (w - 0.9, h * 0.86 - 1.0)], 0.9) ^ rect(0.3, h * 0.14, w - 0.3, h * 0.86)
    body = body + ext(cs_union([la, lb, brace]), t - 0.31, t)
    for v in (h * 0.14 + 0.5, h * 0.86 - 0.5):
        body = body + ext(_strap(0.05, w * 0.85, v) ^ rect(0.0, 0.0, w, h), t - 0.01, t + 0.2)
    return body


def post_piney(h):
    """A cedar porch post: round, a little thicker at its foot, two growth rings, a square
    bolster block on top under the beam (from z = 0 to h)."""
    from .porchwork import _revolve, _top
    z1 = h - 2.2
    prof = [(0.0, 0.0), (1.7, 0.0), (1.7, 0.4), (1.5, 0.6)] + \
           [(1.5 - 0.18 * (z - 0.6) / (z1 - 0.6), z) for z in np.linspace(0.6, z1, 5)][1:]
    body = _revolve(prof, seg=20)
    for zr in (h * 0.38, h * 0.62):
        r = 1.5 - 0.18 * (zr - 0.6) / (z1 - 0.6) + 0.12
        body = body + _revolve([(0.0, zr - 0.3), (r, zr - 0.3), (r, zr + 0.3), (0.0, zr + 0.3)], seg=20)
    return body + _top(h, 1.5, z1, 1.32, None, seg=20)


# ================================================================== the Marigny (house 107)
# After the camelback shotgun doubles of the Faubourg Marigny and Bywater, New Orleans
# (1880s-90s): two houses side by side under one roof, each one room wide and many rooms deep,
# one storey at the street and two at the back (the "camelback", taxed as a one-storey house);
# the double front of door, two floor-length windows and door under a deep gallery on turned
# columns with a frieze of spindles; Italianate hoods on scroll consoles over the openings;
# heavy paired brackets under the eave; the street front's boards channelled like dressed
# stone, the sides in weatherboard; up on brick piers with slatted skirts between.

def rustic_marigny(region, datum=0.0, course=2.6, block=6.4, chan=0.45, d=0.4):
    """The street front's channel rustication: wide flush boards cut with V channels so the
    wall reads as dressed stone, the vertical joints staggered course to course."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    out = []
    k0 = math.floor((v0 - datum) / course) - 1
    k1 = math.ceil((v1 - datum) / course) + 1
    for k in range(k0, k1):
        lo, hi = datum + k * course + chan / 2, datum + (k + 1) * course - chan / 2
        off = (k % 2) * block / 2
        u = u0 - block - off
        while u < u1 + block:
            out.append(chamfer_box(u + chan / 2, lo, u + block - chan / 2, hi, 0.0, d, c=0.25, bottom=d))
            u += block
    reg = M.extrude(region, d + 0.2).translate([0, 0, -0.1])
    return (union(out) ^ reg) + M.extrude(region, 0.05)


def lap_marigny(region, datum=0.0, pitch=1.2, d=0.38):
    """The sides' weatherboard: bevelled lap siding, each board thick at its butt (under a 45
    degree bevel) and thin where the next one laps it."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    out = []
    k0 = math.floor((v0 - datum) / pitch) - 1
    k1 = math.ceil((v1 - datum) / pitch) + 1
    for k in range(k0, k1):
        vb = datum + k * pitch
        prof = [(vb, 0.0), (vb + 0.3, d), (vb + pitch + 0.01, 0.06), (vb + pitch + 0.01, 0.0)]
        out.append(M.hull_points([(u, v, w) for u in (u0 - 1.0, u1 + 1.0) for (v, w) in prof]))
    reg = M.extrude(region, d + 0.2).translate([0, 0, -0.1])
    return (union(out) ^ reg) + M.extrude(region, 0.05)


def foundation_mgpiers(reg, seed=0):
    """The raised foundation's face: brick piers every few feet standing proud, slatted skirt
    boards between them under a rail (the crawl space behind)."""
    from . import skins as SK
    u0, v0, u1, v1 = reg.bounds()
    L = u1 - u0
    n = max(1, int(round(L / 17.0)))
    out = [M.extrude(reg, 0.05)]
    piers, panels = [], []
    for k in range(n + 1):
        uc = u0 + L * k / n
        piers.append(rect(max(u0, uc - 2.4), v0, min(u1, uc + 2.4), v1))
    pc = cs_union(piers) ^ reg
    out.append(M.extrude(pc, 0.5) + SK.brick_bond(pc, "running", bl=2.4, bh=1.0, mortar=0.4, bed=0.4, d=0.25).translate([0, 0, 0.48]))
    pan = reg - cs_union(piers).offset(0.3, MIT, 4.0)
    if not pan.is_empty():
        slats = cs_union([rect(u, v0 - 1, u + 0.9, v1 + 1) for u in np.arange(u0 + 0.4, u1, 1.6)]) ^ pan
        out.append(M.extrude(slats, 0.3))
        out.append(M.extrude(rect(u0 - 1, v1 - 1.2, u1 + 1, v1 - 0.2) ^ pan, 0.45))
    return union(out)


TW.FOUNDATION_EXTRA.update(mgpiers=foundation_mgpiers)


# ---- cornice ornaments
def frieze_mgpanels(L, h, b, pitch, margin, pair, half):
    """The main eave's frieze: between the bracket pairs a sunk panel in a moulded frame with a
    rosette of six petals at its centre."""
    v0, v1 = 0.4, h - 0.4
    vm = (v0 + v1) / 2
    out = []
    for uc, wd in CO._between(L, pitch, margin, pair, half):
        if wd < 3.0:
            continue
        fr = rect(uc - wd / 2 + 0.3, v0, uc + wd / 2 - 0.3, v1)
        out.append(_st(fr - fr.offset(-0.55, MIT, 4.0), b, 0.4))
        r = min(1.2, (v1 - v0) / 2 - 0.7)
        if r > 0.6:
            pet = cs_union([circle((uc + r * 0.55 * math.cos(a), vm + r * 0.55 * math.sin(a)), r * 0.42, 12)
                            for a in np.linspace(0, 2 * math.pi, 6, endpoint=False)])
            out.append(_st(_clean(pet, 0.2), b, 0.3))
            out.append(_st(circle((uc, vm), r * 0.3, 12), b, 0.45))
    return out, []


def course_mgguilloche(L, h, b, pitch, margin, p):
    """A guilloche: a chain of interlaced rings with a bead in each eye."""
    r = h / 2 - 0.15
    n = max(1, int((L - 0.8) / (1.6 * r)))
    st_ = (L - 0.8) / n
    rings, beads = [], []
    for k in range(n + 1):
        u = 0.4 + st_ * k
        rings.append(circle((u, h / 2), r, 20) - circle((u, h / 2), r - 0.42, 20))
        beads.append(circle((u, h / 2), 0.28, 10))
    out = [_st(rect(0.2, 0.15, L - 0.2, h - 0.15), b, 0.15)]
    out.append(_st(_clean(cs_union(rings), 0.15) ^ rect(0.2, 0.1, L - 0.2, h - 0.1), b + 0.15, 0.3))
    out.append(_st(cs_union(beads), b + 0.15, 0.3))
    return out


def frieze_mgsunburst(L, h, b, pitch, margin, pair, half):
    """The camel's eave frieze: an Eastlake half-sunburst in every bay, rays fanning up from a
    hub on the frieze's foot, under a plain fillet."""
    v0, v1 = 0.3, h - 0.3
    out = []
    for uc, wd in CO._between(L, pitch, margin, pair, half):
        if wd < 3.0:
            continue
        out.append(_st(rect(uc - wd / 2 + 0.2, v1 - 0.5, uc + wd / 2 - 0.2, v1), b, 0.3))     # the fillet, bay by bay
        R_ = min(wd / 2 - 0.3, v1 - 0.6 - v0)
        rays = [stroke([(uc, v0), (uc + R_ * math.cos(a), v0 + R_ * math.sin(a))], 0.45) for a in np.linspace(0.25, math.pi - 0.25, 7)]
        out.append(_st(_clean(cs_union(rays), 0.18) ^ rect(uc - wd / 2, v0, uc + wd / 2, v1 - 0.5), b, 0.3))
        out.append(_st(circle((uc, v0), 0.9, 16) ^ rect(uc - 2, v0, uc + 2, v0 + 2), b, 0.4))
    return out, []


def bracket_mgscroll(h, d, t):
    """An Italianate console (side profile): a big volute under the soffit, the spine curving
    in an S down the wall to a small curl at the foot, a leaf on its face; solid."""
    r = min(1.2, d / 2 - 0.05)                     # the volute, never behind the bracket's back
    pts = [(0.0, 0.0), (d - r, 0.0)]
    for tt in np.linspace(0.0, 1.0, 12):
        s = tt * tt * (3 - 2 * tt)
        pts.append((d - r - max(0.0, d - r - 1.0) * s, -2 * r + 0.4 - (h - 2 * r - 0.6) * tt))
    pts += [(0.0, -h + 0.8)]
    body = poly(pts)
    vol = circle((d - r, -r), r, 20)
    curl = circle((1.0, -h + 0.9), 0.9, 16)
    return cs_union([body, vol, curl, rect(0.0, -h + 0.9, 1.0, 0.0)]) ^ rect(0.0, -h - 1.0, d + 1.0, 0.01)


CO.FRIEZE_EXTRA.update(mgpanels=frieze_mgpanels, mgsunburst=frieze_mgsunburst)
CO.COURSE_EXTRA.update(mgguilloche=course_mgguilloche)
TW.BRACKET_EXTRA.update(mgscroll=bracket_mgscroll)


# ---- windows, doors, shutters
def _sash44(w, h, pl, plug_cs, meet=0.6):
    """Four over four: two lights wide and two high in each sash, a meeting rail."""
    inner = plug_cs.offset(-0.6, MIT, 4.0)
    u0, v0, u1, v1 = inner.bounds()
    vm = (v0 + v1) / 2
    lo, hi = rect(u0, v0, u1, vm - meet / 2), rect(u0, vm + meet / 2, u1, v1)
    bars = (_muntins(lo, 2, 2) ^ lo) + (_muntins(hi, 2, 2) ^ hi)
    return _glazed([ext(plug_cs, -pl, -0.6)], lo + hi, pl, bars, plug_cs)


def _console_hood(X, vh, parts, depth=1.6):
    """The Italianate hood over a front opening: a frieze board with an incised fan, a scroll
    console at each end, a cornice cap stepped out over them at 45 degrees."""
    parts.append(ext(rect(-X, vh, X, vh + 2.2), 0.0, 0.8))
    fan = cs_union([stroke([(0.0, vh + 0.2), (1.8 * math.cos(a), vh + 0.2 + 1.8 * math.sin(a))], 0.35)
                    for a in np.linspace(0.3, math.pi - 0.3, 7)])
    parts.append(ext(_clean(fan, 0.15) ^ rect(-2.0, vh + 0.2, 2.0, vh + 2.0), 0.79, 1.0))
    for sg in (-1, 1):
        u = sg * (X + 0.2)
        cons = cs_union([rect(u - 0.7, vh - 2.6, u + 0.7, vh + 2.2), circle((u, vh - 2.6), 0.8, 16)])
        parts.append(ext(cons, 0.0, depth - 0.2))
        parts.append(ext(rect(u - 0.3, vh - 1.8, u + 0.3, vh + 1.6), depth - 0.21, depth))
    parts.append(chamfer_box(-X - 1.4, vh + 2.19, X + 1.4, vh + 2.9, 0.0, depth + 0.4, c=0.3, bottom=depth + 0.4))
    parts.append(chamfer_box(-X - 1.6, vh + 2.89, X + 1.6, vh + 3.5, 0.0, depth + 0.6, c=0.3, bottom=0.6))
    return vh + 3.5


def window_mgfloor(w=11.0, h=28.0, A=1.2):
    """The gallery's floor-length window: four over four, a casing with a bead, an Italianate
    hood on scroll consoles over it; it stands on the gallery floor (no sill)."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    sash = _sash44(w, h, pl, plug_cs)
    X = w / 2 + A
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             ext((op.offset(A, MIT, 4.0) - op) ^ rect(-50, 0.0, 50, 100), 0.0, 0.8),
             ext((op.offset(0.45, MIT, 4.0) - op) ^ rect(-50, 0.0, 50, 100), 0.0, 1.0)]
    top = _console_hood(X, h + A - 0.01, parts)
    return O._one_piece(sash, parts, op, plug_cs, pl, top, 0.0)


def window_mgside(w=10.0, h=22.0, A=1.0):
    """The long sides' window: two over two in a plain casing under a frieze board and a cap,
    a sill on a plain apron."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    sash = _sash22(w, h, pl, plug_cs)
    X = w / 2 + A
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             ext((op.offset(A, MIT, 4.0) - op) ^ rect(-50, 0.0, 50, 100), 0.0, 0.8)]
    vh = h + A - 0.01
    parts.append(ext(rect(-X, vh, X, vh + 1.6), 0.0, 0.8))
    parts.append(chamfer_box(-X - 0.8, vh + 1.59, X + 0.8, vh + 2.4, 0.0, 1.3, c=0.3, bottom=1.3))
    parts.append(chamfer_box(-X - 0.6, -1.2, X + 0.6, 0.01, 0.0, 1.4, c=0.3, bottom=1.4))
    parts.append(ext(rect(-X + 0.6, -2.6, X - 0.6, -1.19), 0.0, 0.6))
    return O._one_piece(sash, parts, op, plug_cs, pl, vh + 2.4, -2.6)


def window_mgupper(w=9.0, h=15.0, A=0.9):
    """The camel's window: two over two under a segmental head, its casing following the arch
    with a keystone; a sill."""
    rise = 1.6
    R_ = (w * w / 4 + rise * rise) / (2 * rise)
    arc = [(R_ * math.sin(a), h - rise - (R_ - rise) + R_ * math.cos(a)) for a in np.linspace(math.asin(w / 2 / R_), -math.asin(w / 2 / R_), 17)]
    op = poly([(-w / 2, 0.0), (w / 2, 0.0)] + arc)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    inner = plug_cs.offset(-0.6, MIT, 4.0)
    u0, v0, u1, v1 = inner.bounds()
    vm = round(((v0 + v1) / 2 - 0.5) / 0.2) * 0.2
    lo, hi = inner ^ rect(-50, v0, 50, vm - 0.3), inner ^ rect(-50, vm + 0.3, 50, 100)
    bars = rect(-RIB / 2, v0 - 1, RIB / 2, v1 + 1)
    sash = _glazed([ext(plug_cs, -pl, -0.6)], lo + hi, pl, bars, plug_cs)
    X = w / 2 + A
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             ext((op.offset(A, RND) - op) ^ rect(-50, 0.0, 50, 100), 0.0, 0.8)]
    kt = h + A
    parts.append(ext(poly([(-0.9, kt - 1.6), (0.9, kt - 1.6), (1.2, kt + 0.6), (-1.2, kt + 0.6)]), 0.0, 1.2))
    parts.append(chamfer_box(-X - 0.6, -1.2, X + 0.6, 0.01, 0.0, 1.3, c=0.3, bottom=1.3))
    return O._one_piece(sash, parts, op, plug_cs, pl, kt + 0.6, -1.2)


def door_mgfront(w=11.0, h=27.0, A=1.2):
    """A front door of the double: a tall leaf with two round-headed lights over two raised
    panels, a transom of three lights over it, under the same console hood as the windows."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    vt = h - 4.0
    tr = rect(-w / 2 + 0.6, vt + 0.5, w / 2 - 0.6, h - 0.6)
    lights = []
    for sg in (-1, 1):
        a, c_ = sorted((sg * 0.6, sg * (w / 2 - 1.1)))
        r = (c_ - a) / 2
        lights.append(rect(a, vt * 0.45, c_, vt - 1.0 - r) + circle(((a + c_) / 2, vt - 1.0 - r), r, 20))
    glass = cs_union(lights) + tr
    parts_s = [ext(plug_cs - plug_cs.offset(-0.5, MIT, 4.0), -pl, 0.0), ext(plug_cs, -pl, -0.6)]
    parts_s = [p_ - ext(glass, -pl - 1, 0.0) for p_ in parts_s]
    parts_s.append(ext(glass, -pl, -pl + O.GLASS))
    parts_s.append(ext(cs_union([rect(x - RIB / 2, vt, x + RIB / 2, h) for x in np.linspace(-w / 2, w / 2, 4)[1:-1]]) ^ tr.offset(0.1, MIT, 4.0),
                       -pl + O.GLASS - 0.01, -0.5))
    parts_s.append(ext(rect(-w / 2 + 0.4, vt - 0.1, w / 2 - 0.4, vt + 0.5), -0.65, -0.1))
    for lt in lights:
        parts_s.append(ext(lt.offset(0.5, RND) - lt, -0.65, -0.2))
    for sg in (-1, 1):
        a, c_ = sorted((sg * 0.6, sg * (w / 2 - 1.1)))
        pan = rect(a, 1.2, c_, vt * 0.45 - 1.0)
        parts_s.append(ext(pan - pan.offset(-0.45, MIT, 4.0), -0.65, -0.2))
        parts_s.append(chamfer_box(*pan.offset(-0.9, MIT, 4.0).bounds(), -0.65, 0.35, c=0.2))
    X = w / 2 + A
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             ext((op.offset(A, MIT, 4.0) - op) ^ rect(-50, 0.0, 50, 100), 0.0, 0.8),
             ext((op.offset(0.45, MIT, 4.0) - op) ^ rect(-50, 0.0, 50, 100), 0.0, 1.0)]
    top = _console_hood(X, h + A - 0.01, parts)
    return O._one_piece(parts_s, parts, op, plug_cs, pl, top, 0.0)


def door_mgback(w=9.0, h=22.0, A=1.0):
    """The back doors onto the back gallery: four panels under a two-light transom, a plain
    casing with a cap."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    vt = h - 3.4
    tr = rect(-w / 2 + 0.6, vt + 0.5, w / 2 - 0.6, h - 0.6)
    parts_s = [ext(plug_cs - plug_cs.offset(-0.5, MIT, 4.0), -pl, 0.0), ext(plug_cs, -pl, -0.6)]
    parts_s = [p_ - ext(tr, -pl - 1, 0.0) for p_ in parts_s]
    parts_s.append(ext(tr, -pl, -pl + O.GLASS))
    parts_s.append(ext(rect(-RIB / 2, vt, RIB / 2, h) ^ tr.offset(0.1, MIT, 4.0), -pl + O.GLASS - 0.01, -0.5))
    parts_s.append(ext(rect(-w / 2 + 0.4, vt - 0.1, w / 2 - 0.4, vt + 0.5), -0.65, -0.1))
    lh = (vt - 2.0) * 0.5
    _panels(parts_s, w, [(1.0, 1.0 + lh), (1.0 + lh + 0.9, vt - 0.9)])
    X = w / 2 + A
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             ext((op.offset(A, MIT, 4.0) - op) ^ rect(-50, 0.0, 50, 100), 0.0, 0.8)]
    vh = h + A - 0.01
    parts.append(ext(rect(-X, vh, X, vh + 1.4), 0.0, 0.8))
    parts.append(chamfer_box(-X - 0.8, vh + 1.39, X + 0.8, vh + 2.2, 0.0, 1.3, c=0.3, bottom=1.3))
    return O._one_piece(parts_s, parts, op, plug_cs, pl, vh + 2.2, 0.0)


def shutter_marigny(w, h, t=0.8, stile=0.6):
    """The Marigny's floor-length shutter: three fields of fixed louvers between two lock rails,
    a slide bolt on the middle rail. Local frame as features.shutter (u 0..w, v 0..h, back at
    w = 0; prints face-up)."""
    web = 0.4
    r1, r2 = round(h / 3 / 0.2) * 0.2, round(h * 2 / 3 / 0.2) * 0.2
    parts = [ext(rect(0, 0, w, h) - rect(stile, stile, w - stile, h - stile), 0.0, t)]
    for rv in (r1, r2):
        parts.append(ext(rect(stile, rv - stile / 2, w - stile, rv + stile / 2), 0.0, t))
    for f0, f1 in ((stile, r1 - stile / 2), (r1 + stile / 2, r2 - stile / 2), (r2 + stile / 2, h - stile)):
        field = rect(stile, f0, w - stile, f1)
        parts.append(ext(field, 0.0, web))
        b = field.bounds()
        n = max(1, int((b[3] - b[1] - 0.5) / 0.9))
        pt = (b[3] - b[1] - 0.5) / n
        slats = [rect(b[0] - 0.1, b[1] + 0.5 + k * pt, b[2] + 0.1, b[1] + 0.5 + k * pt + min(RIB + 0.05, pt - 0.45)) for k in range(n)]
        parts.append(ext(cs_union(slats) ^ field.offset(0.05), web, t - 0.2))
    parts.append(ext(rect(w * 0.25, r1 - 0.25, w * 0.75, r1 + 0.25), t - 0.01, t + 0.2))
    return union(parts)


# ---- the gallery: column, baluster, spindle frieze, skirt and roof edge (registered)
def post_marigny(h, collar=None, abacus=3.2, slot=None):
    """The gallery's column, Eastlake turned: a tall square chamfered pedestal, a vase turned
    with rings above it, a long shaft with a neck ring, a square capital block."""
    from .porchwork import _revolve, _top
    zp = 3.4
    c_ = 0.45                                                      # the pedestal's chamfered corners
    ped = M.extrude(poly([(1.6, -1.6 + c_), (1.6, 1.6 - c_), (1.6 - c_, 1.6), (-1.6 + c_, 1.6), (-1.6, 1.6 - c_), (-1.6, -1.6 + c_),
                          (-1.6 + c_, -1.6), (1.6 - c_, -1.6)]), zp)
    z1 = h - 2.8
    zv = zp + (z1 - zp) * 0.22
    prof = [(0.0, zp - 0.01), (1.35, zp - 0.01), (1.35, zp + 0.3), (1.0, zp + 0.6), (1.45, zp + 1.6), (1.45, zv - 0.8),
            (0.95, zv), (1.25, zv + 0.25), (1.25, zv + 0.55), (0.95, zv + 0.8), (1.0, z1 - 1.2), (1.25, z1 - 0.95),
            (1.25, z1 - 0.65), (1.05, z1 - 0.4), (1.05, z1)]
    body = _revolve(prof) + ped
    return body + _top(h, abacus / 2, z1, 1.05, slot, seg=36)


def baluster_marigny(h, seg=16):
    """The gallery's baluster: turned, a vase low down, rings, a slim neck."""
    from .porchwork import _revolve
    zv = h * 0.35
    prof = [(0.0, 0.0), (0.5, 0.0), (0.5, 0.5), (0.35, 0.7), (0.55, zv - 0.6), (0.55, zv), (0.3, zv + 0.9), (0.3, h - 1.0),
            (0.48, h - 0.8), (0.48, h - 0.5), (0.32, h - 0.3), (0.32, h), (0.0, h)]
    return _revolve(prof, seg=seg)


def spandrel_mgspindle(u0, u1, v_bot, v_top):
    """The gallery's frieze between two columns (Eastlake): a rail under the beam and a second
    one below it with a row of turned spindles between them, a fan bracket in each corner."""
    H = v_top - v_bot
    vr = v_bot + H * 0.42
    out = [rect(u0, v_top - 0.8, u1, v_top), rect(u0, vr - 0.35, u1, vr + 0.35)]
    reach = min(5.4, (u1 - u0) * 0.22)
    n = max(1, int((u1 - u0 - 2 * reach) / 1.4))
    for k in range(n + 1):
        u = u0 + reach + (u1 - u0 - 2 * reach) * k / max(n, 1)
        out.append(rect(u - 0.3, vr, u + 0.3, v_top - 0.79))
        out.append(circle((u, (vr + v_top - 0.8) / 2), 0.5, 12))
    for sg, uo in ((1, u0), (-1, u1)):
        fan = poly([(uo, v_top), (uo, v_bot)] + [(uo + sg * reach * math.sin(a), v_top - H * math.cos(a)) for a in np.linspace(0, math.pi / 2, 10)])
        slots = cs_union([stroke([(uo + sg * 0.9 * math.sin(a), v_top - 0.9 * math.cos(a)), (uo + sg * (reach - 1.0) * math.sin(a), v_top - (H - 1.0) * math.cos(a))], 0.55)
                          for a in np.linspace(0.35, math.pi / 2 - 0.35, 3)])
        out.append(fan - slots)
    return _clean(cs_union(out)) ^ rect(u0, v_bot - 0.01, u1, v_top + 0.01)


def skirt_mgslats(reg, d=1.2):
    """The gallery's skirt: slats set on the diagonal both ways (a lattice of flat strips)
    between plain rails."""
    u0, v0, u1, v1 = reg.bounds()
    H = v1 - v0
    st_ = []
    for u in np.arange(u0 - H, u1 + H, 2.2):
        st_.append(stroke([(u, v0), (u + H, v1)], 0.7))
    lat = _clean(cs_union(st_), 0.2) ^ reg
    rails = (rect(u0 - 1, v1 - 1.0, u1 + 1, v1 + 1) + rect(u0 - 1, v0 - 1, u1 + 1, v0 + 0.8)) ^ reg
    return M.extrude(lat, d * 0.5) + M.extrude(rails, d)


def edge_mgmodillion(L, z0, zc):
    """The gallery roof's edge: a fascia carried on a row of little round-ended modillions
    under a cap."""
    n = max(1, int((L - 1.2) / 2.0))
    mods = [rect(u - 0.4, z0 + 0.1, u + 0.4, zc - 1.0) + circle((u, z0 + 0.5), 0.4, 10)
            for u in (0.6 + (L - 1.2) * (k + 0.5) / n for k in range(n))]
    return cs_union(mods) + rect(0.3, zc - 1.0, L - 0.3, zc), 0.6


PW.POSTS.update(marigny=post_marigny)
PW.BALUSTERS.update(marigny=(baluster_marigny, 1.9))
PW.FRIEZES.update(mgspindle=spandrel_mgspindle)
PW.SKIRTS.update(mgslats=skirt_mgslats)
FT.EDGE_EXTRA.update(mgmodillion=edge_mgmodillion)


def chimney_marigny(w=7.0, d=12.0, h=30.0):
    """The Marigny's chimney (stands on z = 0, the floor of its roof pocket): running-bond brick,
    a stucco band, a three-course corbelled cap under a slab, two octagonal clay pots."""
    h = round(h / 0.2) * 0.2
    sh = round((h - 5.0) / 0.2) * 0.2
    body = box([-w / 2, -d / 2, 0], [w / 2, d / 2, sh]) + TW._skin(w, d, 0.0, sh - 3.0, TW._brick("running"))
    zb = sh - 3.0
    body = body + box([-w / 2 - 0.3, -d / 2 - 0.3, zb], [w / 2 + 0.3, d / 2 + 0.3, zb + 1.2]) + TW._corbel_out(w, d, zb, 0.3)
    z = sh
    for k in range(3):
        g = 0.25 * (k + 1)
        body = body + TW._corbel_out(w + 2 * (g - 0.25), d + 2 * (g - 0.25), z + 0.25, 0.25) + \
            box([-w / 2 - g, -d / 2 - g, z + 0.24], [w / 2 + g, d / 2 + g, z + 0.6])
        z += 0.6
    body = body + box([-w / 2 - 0.9, -d / 2 - 0.9, z - 0.01], [w / 2 + 0.9, d / 2 + 0.9, z + 0.6])
    z += 0.6
    for y in (-d / 4, d / 4):
        pot = M.cylinder(3.2, 1.25, 1.0, 8).translate([0, y, z - 0.01]) + M.cylinder(0.6, 1.3, 1.3, 8).translate([0, y, z + 3.0])
        body = body + pot - M.cylinder(4.0, 0.7, 0.7, 8).translate([0, y, z + 0.6])
    return body


# ================================================================== the Paloma (house 108)
# After the Larkin House, Monterey, California (1835), the first Monterey Colonial, and the
# adobes round it: a two-storey adobe whose low hipped roof of redwood shingles runs out over a
# two-tier gallery (a corredor below, a balcony above) on slender posts with carved zapatas;
# two one-storey adobe wings come forward from it round a courtyard open to the street, each
# with a corredor facing the court and a window caged in a turned wooden reja to the street; a
# garden wall with a tile coping and an arched gate closes the court; a well in the court.

def adobe_paloma(region, datum=0.0, seed=0, dado=5.0):
    """Lime-washed adobe: plaster laid on thick with trowel patches standing a hair proud, a
    painted dado band at the foot, and here and there a patch where the plaster has fallen away
    to show the adobe bricks and their mud joints."""
    if region.is_empty():
        return M()
    rng = np.random.default_rng(seed)
    u0, v0, u1, v1 = region.bounds()
    out = [M.extrude(region, 0.05)]
    pat = []
    for _ in range(int((u1 - u0) * (v1 - v0) / 140.0)):
        c = (rng.uniform(u0, u1), rng.uniform(v0, v1))
        r = rng.uniform(1.8, 3.4)
        pat.append(poly([(c[0] + r * rng.uniform(0.6, 1.0) * math.cos(a), c[1] + r * 0.6 * rng.uniform(0.6, 1.0) * math.sin(a))
                         for a in np.linspace(0, 2 * math.pi, 9, endpoint=False)]))
    spall = []
    for _ in range(max(1, int((u1 - u0) / 45.0))):
        c = (rng.uniform(u0 + 4, max(u0 + 5, u1 - 4)), rng.uniform(v0 + dado + 3, max(v0 + dado + 4, v1 - 5)))
        r = rng.uniform(2.4, 3.6)
        spall.append(poly([(c[0] + r * rng.uniform(0.7, 1.1) * math.cos(a), c[1] + r * 0.75 * rng.uniform(0.7, 1.1) * math.sin(a))
                           for a in np.linspace(0, 2 * math.pi, 10, endpoint=False)]))
    spall = cs_union(spall) ^ region
    plaster = region - spall.offset(0.25, RND)
    if pat:
        out.append(M.extrude((cs_union(pat) ^ plaster) - rect(u0 - 1, v0 - 1, u1 + 1, v0 + dado + 0.4), 0.13))
    out.append(M.extrude(plaster ^ rect(u0 - 1, v0 - 1, u1 + 1, v0 + dado), 0.3))                        # the dado
    if not spall.is_empty():                                                                     # bricks in the spalls
        bricks = []
        for k, v in enumerate(np.arange(v0 - 2.0, v1, 1.3)):
            off = (k % 2) * 1.9
            for u in np.arange(u0 - 4.0 + off, u1, 3.8):
                bricks.append(rect(u + 0.15, v + 0.15, u + 3.65, v + 1.15))
        out.append(M.extrude(cs_union(bricks) ^ spall, 0.12).translate([0, 0, -0.25]))
        out[0] = M.extrude(region - spall, 0.05)
        out.append(M.extrude(spall, 0.05).translate([0, 0, -0.3]))
    return union(out)


def foundation_plstone(reg, seed=0):
    """The adobes' footing: a low course of rough Monterey sandstone under a lime wash line."""
    u0, v0, u1, v1 = reg.bounds()
    st = ashlar(rect(u0, v0, u1, v1 - 0.6), course=(1.6, 2.4), length=(2.6, 5.6), d=0.45, seed=seed + 21, rough=0.25, bevel=0.3)
    return st + M.extrude(rect(u0, v1 - 0.6, u1, v1), 0.25)


TW.FOUNDATION_EXTRA.update(plstone=foundation_plstone)


# ---- cornice ornaments
def frieze_plwave(L, h, b, pitch, margin, pair, half):
    """The balcony joint's frieze: a running Vitruvian scroll (waves curling over) between two
    fillets."""
    v0, v1 = 0.35, h - 0.35
    out = [_st(rect(0.2, v0, L - 0.2, v0 + 0.45) + rect(0.2, v1 - 0.45, L - 0.2, v1), b, 0.3)]
    H = v1 - v0 - 1.0
    pw = H * 1.6
    n = max(1, int((L - 0.8) / pw))
    u0 = (L - n * pw) / 2
    waves = []
    for k in range(n):
        a = u0 + k * pw
        pts = [(a, v0 + 0.5)]
        for t in np.linspace(0, 1, 14):
            ang = math.pi * 1.6 * t
            r = H * 0.45 * (1 - 0.55 * t)
            pts.append((a + pw * 0.55 + r * math.sin(ang) - r * 0.2, v0 + 0.5 + H * 0.5 - r * math.cos(ang)))
        waves.append(stroke(pts, 0.45))
        waves.append(stroke([(a, v0 + 0.5), (a + pw, v0 + 0.5)], 0.45))
    out.append(_st(_clean(cs_union(waves), 0.18) ^ rect(0.2, v0 + 0.3, L - 0.2, v1 - 0.4), b, 0.3))
    return out, []


def frieze_plrosette(L, h, b, pitch, margin, pair, half):
    """The eave's frieze under the gallery roof: chip-carved rosettes (six-point stars in rings)
    in square panels, a plain stile between each."""
    v0, v1 = 0.3, h - 0.3
    s = v1 - v0
    n = max(1, int((L - 0.6) / (s + 0.8)))
    st_ = (L - 0.6) / n
    out = []
    for k in range(n):
        uc = 0.3 + st_ * (k + 0.5)
        sq = rect(uc - s / 2, v0, uc + s / 2, v1)
        out.append(_st(sq - sq.offset(-0.4, MIT, 4.0), b, 0.3))
        r = s / 2 - 0.65
        if r > 0.6:
            ring = circle((uc, (v0 + v1) / 2), r, 20) - circle((uc, (v0 + v1) / 2), r - 0.35, 20)
            star = cs_union([poly([(uc + r * 0.85 * math.cos(a), (v0 + v1) / 2 + r * 0.85 * math.sin(a)),
                                   (uc + r * 0.3 * math.cos(a + math.pi / 6), (v0 + v1) / 2 + r * 0.3 * math.sin(a + math.pi / 6)),
                                   (uc, (v0 + v1) / 2),
                                   (uc + r * 0.3 * math.cos(a - math.pi / 6), (v0 + v1) / 2 + r * 0.3 * math.sin(a - math.pi / 6))])
                             for a in np.linspace(0, 2 * math.pi, 6, endpoint=False)])
            out.append(_st(_clean(ring + star, 0.15), b, 0.3))
    return out, []


def course_pltooth(L, h, b, pitch, margin, p):
    """A dogtooth course: a row of little four-sided pyramids point outward, set tip to tip."""
    s = h - 0.3
    n = max(1, int((L - 0.4) / s))
    st_ = (L - 0.4) / n
    teeth = [poly([(0.2 + st_ * k, h / 2), (0.2 + st_ * (k + 0.5), 0.15), (0.2 + st_ * (k + 1), h / 2), (0.2 + st_ * (k + 0.5), h - 0.15)])
             for k in range(n)]
    out = [_st(rect(0.2, 0.15, L - 0.2, h - 0.15), b, 0.12)]
    for d_ in (0.12, 0.24):
        out.append(_st(cs_union([t_.offset(-d_ * 1.4, MIT, 4.0) for t_ in teeth]), b + d_, 0.13))
    return out


CO.FRIEZE_EXTRA.update(plwave=frieze_plwave, plrosette=frieze_plrosette)
CO.COURSE_EXTRA.update(pltooth=course_pltooth)


# ---- windows, doors, shutters
def _sash_lights(w, h, pl, plug_cs, cols, rows_lo, rows_hi, meet=0.6):
    inner = plug_cs.offset(-0.6, MIT, 4.0)
    u0, v0, u1, v1 = inner.bounds()
    vm = v0 + (v1 - v0) * rows_lo / (rows_lo + rows_hi)
    lo, hi = rect(u0, v0, u1, vm - meet / 2), rect(u0, vm + meet / 2, u1, v1)
    bars = (_muntins(lo, cols, rows_lo) ^ lo) + (_muntins(hi, cols, rows_hi) ^ hi)
    return _glazed([ext(plug_cs, -pl, -0.6)], lo + hi, pl, bars, plug_cs)


def window_plmain(w=10.0, h=19.0, A=1.1):
    """The house's ground-floor window, deep in the adobe: nine over six, a plain casing with a
    frieze board and a moulded cap over it, a thick wooden sill on two corbels."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    sash = _sash_lights(w, h, pl, plug_cs, 3, 2, 3)
    X = w / 2 + A
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             ext((op.offset(A, MIT, 4.0) - op) ^ rect(-50, 0.0, 50, 100), 0.0, 0.8)]
    vh = h + A - 0.01
    parts.append(ext(rect(-X, vh, X, vh + 1.8), 0.0, 0.8))
    parts.append(chamfer_box(-X - 0.7, vh + 1.79, X + 0.7, vh + 2.5, 0.0, 1.3, c=0.3, bottom=0.6))
    parts.append(chamfer_box(-X - 0.5, vh + 2.49, X + 0.5, vh + 3.0, 0.0, 1.0, c=0.3, bottom=0.4))
    parts.append(chamfer_box(-X - 0.9, -1.6, X + 0.9, 0.01, 0.0, 1.8, c=0.3, bottom=1.8))
    for sg in (-1, 1):
        u = sg * (X - 0.8)
        parts.append(ext(poly([(u - 0.7, -1.59), (u + 0.7, -1.59), (u + 0.4, -3.2), (u - 0.4, -3.2)]), 0.0, 1.4))
    return O._one_piece(sash, parts, op, plug_cs, pl, vh + 3.0, -3.2)


def door_plfrench(w=12.0, h=23.0, A=1.1):
    """The upper storey's doors onto the balcony: a pair of glazed doors (three lights over a
    panel each) under a two-light transom, a casing crowned with a low triangular pediment."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    vt = h - 3.2
    tr = rect(-w / 2 + 0.6, vt + 0.5, w / 2 - 0.6, h - 0.6)
    lights = []
    for sg in (-1, 1):
        a, c_ = sorted((sg * 0.5, sg * (w / 2 - 0.9)))
        lights.append(rect(a, vt * 0.32, c_, vt - 0.9))
    glass = cs_union(lights) + tr
    parts_s = [ext(plug_cs - plug_cs.offset(-0.5, MIT, 4.0), -pl, 0.0), ext(plug_cs, -pl, -0.6)]
    parts_s = [p_ - ext(glass, -pl - 1, 0.0) for p_ in parts_s]
    parts_s.append(ext(glass, -pl, -pl + O.GLASS))
    bars = [rect(-RIB / 2, vt, RIB / 2, h)]
    for lt in lights:
        lb = lt.bounds()
        for k in (1, 2):
            v = lb[1] + (lb[3] - lb[1]) * k / 3
            bars.append(rect(lb[0] - 1, v - RIB / 2, lb[2] + 1, v + RIB / 2))
    parts_s.append(ext(cs_union(bars) ^ glass.offset(0.1, MIT, 4.0), -pl + O.GLASS - 0.01, -0.5))
    parts_s.append(ext(rect(-0.3, 0.0, 0.3, vt + 0.5), -0.65, -0.1))                     # the meeting stiles
    parts_s.append(ext(rect(-w / 2 + 0.4, vt - 0.1, w / 2 - 0.4, vt + 0.5), -0.65, -0.1))
    for sg in (-1, 1):
        a, c_ = sorted((sg * 0.5, sg * (w / 2 - 0.9)))
        pan = rect(a, 1.0, c_, vt * 0.32 - 0.9)
        parts_s.append(ext(pan - pan.offset(-0.45, MIT, 4.0), -0.65, -0.2))
    X = w / 2 + A
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             ext((op.offset(A, MIT, 4.0) - op) ^ rect(-50, 0.0, 50, 100), 0.0, 0.8)]
    vh = h + A - 0.01
    ped = poly([(-X - 0.9, vh), (X + 0.9, vh), (0.0, vh + 3.4)])
    parts.append(ext(ped - ped.offset(-0.8, MIT, 4.0), 0.0, 1.2))
    parts.append(ext(ped.offset(-0.8, MIT, 4.0), 0.0, 0.6))
    parts.append(chamfer_box(-X - 1.0, vh - 0.6, X + 1.0, vh + 0.01, 0.0, 1.3, c=0.3, bottom=0.5))
    return O._one_piece(parts_s, parts, op, plug_cs, pl, vh + 3.4, 0.0)


def door_plmain(w=12.0, h=24.0, A=1.4):
    """The house's door to the court: a pair of heavy leaves, each of six raised panels with
    iron nail heads at the rails, under a carved lintel (a scroll each end, a shell in the
    middle) on two plain jambs."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    parts_s = [ext(plug_cs - plug_cs.offset(-0.5, MIT, 4.0), -pl, 0.0), ext(plug_cs, -pl, -0.6)]
    parts_s.append(ext(rect(-0.3, 0.0, 0.3, h - 0.5), -0.65, -0.1))
    ph = (h - 2.0) / 3
    for j in range(3):
        for sg in (-1, 1):
            vb = 1.0 + j * ph
            pan = rect(min(sg * 0.6, sg * (w / 2 - 0.9)), vb, max(sg * 0.6, sg * (w / 2 - 0.9)), vb + ph - 0.7)
            parts_s.append(ext(pan - pan.offset(-0.45, MIT, 4.0), -0.65, -0.2))
            parts_s.append(chamfer_box(*pan.offset(-0.9, MIT, 4.0).bounds(), -0.65, 0.35, c=0.2))
        vr = 1.0 + j * ph - 0.35
        for x in np.linspace(-w / 2 + 1.0, w / 2 - 1.0, 6):
            parts_s.append(ext(circle((x, vr), 0.3, 8), -0.65, -0.05))
    X = w / 2 + A
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             ext((op.offset(A, MIT, 4.0) - op) ^ rect(-50, 0.0, 50, h + 0.01), 0.0, 1.0)]
    vh = h - 0.01
    lin = rect(-X - 1.6, vh, X + 1.6, vh + 3.4)
    parts.append(ext(lin, 0.0, 1.0))
    carve = [circle((sg * (X + 0.4), vh + 1.7), 1.1, 18) - circle((sg * (X + 0.4), vh + 1.7), 0.55, 14) for sg in (-1, 1)]
    carve.append(cs_union([stroke([(0.0, vh + 0.6), (2.2 * math.cos(a), vh + 0.6 + 2.2 * math.sin(a))], 0.4)
                           for a in np.linspace(0.35, math.pi - 0.35, 7)]))
    carve.append(stroke([(-X + 1.2, vh + 1.7), (-2.6, vh + 1.7)], 0.45))
    carve.append(stroke([(2.6, vh + 1.7), (X - 1.2, vh + 1.7)], 0.45))
    parts.append(ext(_clean(cs_union(carve), 0.15) ^ lin.offset(-0.3, MIT, 4.0), 0.99, 1.3))
    parts.append(chamfer_box(-X - 2.0, vh + 3.39, X + 2.0, vh + 4.2, 0.0, 1.5, c=0.3, bottom=0.8))
    return O._one_piece(parts_s, parts, op, plug_cs, pl, vh + 4.2, 0.0)


def window_plreja(w=8.0, h=12.0, A=0.9, dep=2.6):
    """A wing's window to the street, caged in a reja: a grille of turned wooden spindles
    standing out from the wall in a box frame, a little shingled hood over it on two brackets,
    two casements behind."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    inner = plug_cs.offset(-0.6, MIT, 4.0)
    bars = cs_union([rect(-0.4, -1.0, 0.4, h + 1.0), rect(-w, h / 2 - RIB / 2, w, h / 2 + RIB / 2)])
    sash = _glazed([ext(plug_cs, -pl, -0.6)], inner, pl, bars, plug_cs)
    X = w / 2 + A
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS), ext(op.offset(A, MIT, 4.0) - op, 0.0, 0.8)]
    # the reja: a sill box and a head rail standing out, spindles between them
    parts.append(chamfer_box(-X - 0.4, -1.6, X + 0.4, 0.4, 0.0, dep + 0.6, c=0.3, bottom=dep + 0.6))
    parts.append(ext(rect(-X - 0.4, h + A - 0.6, X + 0.4, h + A + 0.6), 0.0, dep + 0.6))
    for x in np.linspace(-X + 0.4, X - 0.4, 7):
        sp = cs_union([rect(x - 0.35, 0.39, x + 0.35, h + A - 0.59)] +
                      [circle((x, v), 0.5, 12) for v in np.linspace(1.6, h + A - 1.8, 4)])
        parts.append(ext(sp, dep - 0.35, dep + 0.35))
    for sg in (-1, 1):                                             # the sides of the cage
        x = sg * (X + 0.1)
        parts.append(ext(rect(min(x, x - sg * 0.6), 0.39, max(x, x - sg * 0.6), h + A - 0.59), 0.0, dep + 0.35))
    vh = h + A + 0.59
    hood = poly([(-X - 1.2, vh), (X + 1.2, vh), (X + 1.2, vh + 0.6), (0.0, vh + 2.2), (-X - 1.2, vh + 0.6)])
    parts.append(ext(hood, 0.0, dep + 1.0))
    return O._one_piece(sash, parts, op, plug_cs, pl, vh + 2.2, -1.6)


def window_plcourt(w=8.0, h=13.0, A=0.9):
    """A wing's window to the court: a pair of casements of three lights each, a plain casing
    with a drip cap, a sill."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    inner = plug_cs.offset(-0.6, MIT, 4.0)
    b = inner.bounds()
    bars = cs_union([rect(-0.4, -1.0, 0.4, h + 1.0)] + [rect(-w, v - RIB / 2, w, v + RIB / 2) for v in (b[1] + (b[3] - b[1]) / 3, b[1] + 2 * (b[3] - b[1]) / 3)])
    sash = _glazed([ext(plug_cs, -pl, -0.6)], inner, pl, bars, plug_cs)
    X = w / 2 + A
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS), ext((op.offset(A, MIT, 4.0) - op) ^ rect(-50, 0.0, 50, 100), 0.0, 0.8)]
    vh = h + A - 0.01
    parts.append(chamfer_box(-X - 0.6, vh, X + 0.6, vh + 1.3, 0.0, 1.2, c=0.3, bottom=1.0))
    parts.append(chamfer_box(-X - 0.5, -1.2, X + 0.5, 0.01, 0.0, 1.4, c=0.3, bottom=1.4))
    return O._one_piece(sash, parts, op, plug_cs, pl, vh + 1.3, -1.2)


def door_plplank(w=8.4, h=19.0, A=1.0):
    """A wing's door to the corredor: wide planks with rows of iron nail heads across them and
    a ring pull, a plain heavy casing with a lintel."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    parts_s = [ext(plug_cs - plug_cs.offset(-0.5, MIT, 4.0), -pl, 0.0), ext(plug_cs, -pl, -0.6)]
    face = plug_cs.offset(-0.5, MIT, 4.0)
    fb = face.bounds()
    bds = cs_union([rect(x - 0.15, -1, x + 0.15, 100) for x in np.arange(fb[0] + 2.0, fb[2] - 0.8, 2.0)])
    parts_s.append(ext(_clean(face - bds, 0.12), -0.65, -0.3))
    for v in (fb[1] + 2.0, (fb[1] + fb[3]) / 2, fb[3] - 2.0):
        for x in np.arange(fb[0] + 1.0, fb[2] - 0.5, 2.0):
            parts_s.append(ext(circle((x, v), 0.3, 8), -0.31, -0.08))
    parts_s.append(ext(circle((fb[2] - 1.4, (fb[1] + fb[3]) / 2 + 1.6), 0.7, 14) - circle((fb[2] - 1.4, (fb[1] + fb[3]) / 2 + 1.6), 0.35, 12), -0.31, -0.08))
    X = w / 2 + A
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS), ext((op.offset(A, MIT, 4.0) - op) ^ rect(-50, 0.0, 50, h + 0.01), 0.0, 1.0)]
    parts.append(chamfer_box(-X - 0.8, h - 0.01, X + 0.8, h + 2.0, 0.0, 1.2, c=0.3, bottom=0.6))
    return O._one_piece(parts_s, parts, op, plug_cs, pl, h + 2.0, 0.0)


def shutter_paloma(w, h, t=0.8, stile=0.6):
    """The Paloma's shutter: two raised panels (the lower one shorter) in a frame, a long strap
    hinge across each. Local frame as features.shutter (u 0..w, v 0..h, back at w = 0; prints
    face-up)."""
    from .colonial import _strap
    rv = round(h * 0.4 / 0.2) * 0.2
    parts = [ext(rect(0, 0, w, h), 0.0, t - 0.25)]
    for f0, f1 in ((stile, rv - stile / 2), (rv + stile / 2, h - stile)):
        pan = rect(stile, f0, w - stile, f1)
        parts.append(ext(rect(0, 0, w, h) - pan, t - 0.26, t))
        parts.append(chamfer_box(*pan.offset(-0.45, MIT, 4.0).bounds(), t - 0.26, 0.25, c=0.2))
    parts.append(ext(rect(0, rv - stile / 2, w, rv + stile / 2), t - 0.26, t))
    for v in (h * 0.15, h * 0.85):
        parts.append(ext(_strap(0.05, w * 0.8, v) ^ rect(0, 0, w, h), t - 0.01, t + 0.2))
    return union(parts)


# ---- posts, zapatas, balusters, chimney
def post_paloma(h, r=1.1):
    """A gallery post: round and slender on a square plinth block (from z = 0 to h)."""
    from .porchwork import _revolve
    body = box([-1.5, -1.5, 0.0], [1.5, 1.5, 1.6]) + M.hull_points([(x, y, 1.59) for x in (-1.5, 1.5) for y in (-1.5, 1.5)] +
                                                                   [(r * math.cos(a), r * math.sin(a), 2.2) for a in np.linspace(0, 2 * math.pi, 16, endpoint=False)])
    return body + _revolve([(0.0, 2.1), (r, 2.1), (r * 0.92, h), (0.0, h)], seg=20)


def zapata_paloma(L=7.0, H=1.6, D=2.2):
    """A zapata: the carved bolster on a post's head under the beam, its ends cut in a double
    scroll (a quarter round over a half round), in the frame u along the beam, v up, w across;
    from v = 0 to H."""
    hl = L / 2
    prof = [(-hl, H), (hl, H)]
    for a in np.linspace(0.0, math.pi / 2, 6):
        prof.append((hl - 0.6 * (1 - math.cos(a)), H - 0.6 * math.sin(a)))
    prof += [(hl - 1.0, H - 0.6), (hl - 1.0, 0.45)]
    for a in np.linspace(0.0, math.pi, 7):
        prof.append((hl - 1.45 - 0.45 * math.cos(a), 0.45 - 0.45 * math.sin(a)))
    prof += [(-(hl - 1.9), 0.0)]
    for a in np.linspace(0.0, math.pi, 7):
        prof.append((-(hl - 1.45) - 0.45 * math.cos(a), 0.45 - 0.45 * math.sin(a)))
    prof += [(-(hl - 1.0), 0.45), (-(hl - 1.0), H - 0.6)]
    for a in np.linspace(math.pi / 2, 0.0, 6):
        prof.append((-hl + 0.6 * (1 - math.cos(a)), H - 0.6 * math.sin(a)))
    cs = poly(prof)
    return M.extrude(cs, D).transform(np.array([[1.0, 0, 0, 0], [0, 0, 1.0, -D / 2], [0, 1.0, 0, 0]]))


def baluster_paloma(h, seg=16):
    """The balcony's baluster: turned, two vases back to back with a ring between."""
    from .porchwork import _revolve
    m = h / 2
    prof = [(0.0, 0.0), (0.5, 0.0), (0.5, 0.4), (0.3, 0.6), (0.52, m - 1.0), (0.3, m - 0.3), (0.48, m - 0.15), (0.48, m + 0.15),
            (0.3, m + 0.3), (0.52, m + 1.0), (0.3, h - 0.6), (0.5, h - 0.4), (0.5, h), (0.0, h)]
    return _revolve(prof, seg=seg)


def chimney_paloma(w=8.0, d=7.0, h=24.0):
    """An adobe chimney (stands on z = 0, the floor of its roof pocket): lime-plastered, a
    plain band near the top, and a hood of two curved tiles leaning together over the flue."""
    h = round(h / 0.2) * 0.2
    sh = h - 3.0
    body = box([-w / 2, -d / 2, 0.0], [w / 2, d / 2, sh])
    body = body + box([-w / 2 - 0.3, -d / 2 - 0.3, sh - 2.4], [w / 2 + 0.3, d / 2 + 0.3, sh - 1.4]) + TW._corbel_out(w, d, sh - 2.4, 0.3)
    body = body - box([-w / 2 + 1.4, -d / 2 + 1.4, sh - 1.6], [w / 2 - 1.4, d / 2 - 1.4, sh + 1.0])
    for sg in (-1, 1):                                       # the tile hood: a gable of two half-round tiles
        tile = M.hull_points([(sg * (w / 2 - 0.2), y, sh - 0.01) for y in (-d / 2 + 0.6, d / 2 - 0.6)] +
                             [(sg * 0.4, y, h) for y in (-d / 2 + 0.6, d / 2 - 0.6)] +
                             [(sg * (w / 2 - 1.2), y, sh - 0.01) for y in (-d / 2 + 0.6, d / 2 - 0.6)])
        body = body + tile
    return body


def window_plupper(w=9.0, h=16.0, A=1.0):
    """The house's upper window: six over six under a low triangular pediment (as the doors
    onto the balcony), a plain sill."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    sash = _sash_lights(w, h, pl, plug_cs, 3, 2, 2)
    X = w / 2 + A
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             ext((op.offset(A, MIT, 4.0) - op) ^ rect(-50, 0.0, 50, 100), 0.0, 0.8)]
    vh = h + A - 0.01
    ped = poly([(-X - 0.8, vh), (X + 0.8, vh), (0.0, vh + 3.0)])
    parts.append(ext(ped - ped.offset(-0.75, MIT, 4.0), 0.0, 1.2))
    parts.append(ext(ped.offset(-0.75, MIT, 4.0), 0.0, 0.6))
    parts.append(chamfer_box(-X - 0.9, vh - 0.6, X + 0.9, vh + 0.01, 0.0, 1.3, c=0.3, bottom=0.5))
    parts.append(chamfer_box(-X - 0.6, -1.3, X + 0.6, 0.01, 0.0, 1.5, c=0.3, bottom=1.5))
    return O._one_piece(sash, parts, op, plug_cs, pl, vh + 3.0, -1.3)


# ================================================================== the Severn (house 109)
# After the Hammond-Harwood House, Annapolis, Maryland (1774, William Buckland): a five-part
# Palladian house, a two-storey brick centre block with a pedimented centre pavilion, two
# one-storey hyphens set back, and two wings with canted (half-octagon) fronts under hipped
# roofs. Georgian to the bone: Flemish bond with glazed headers, rubbed-brick corners and flat
# arches with stone keystones, a stone water table and belt, a modillion cornice over a Doric
# frieze, and the famous doorway: Ionic columns, a carved frieze, a fanlight, a pediment.

def brick_severn(region, datum=0.0, L=None, d=0.25):
    """Flemish bond, its headers glazed (standing a hair prouder than the stretchers), and at
    the corners (``L``, the face's length) rubbed brick: fine-jointed smooth quoin strips."""
    from . import skins as SK
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    body = region
    out = []
    if L is not None:
        qs = (rect(-1.0, v0 - 1, 2.6, v1 + 1) + rect(L - 2.6, v0 - 1, L + 1.0, v1 + 1)) ^ region
        body = region - qs.offset(0.15, MIT, 4.0)
        if not qs.is_empty():
            q = []
            for k, v in enumerate(np.arange(datum + math.floor((v0 - datum) / 0.9) * 0.9, v1, 0.9)):
                q.append(rect(-1.0, v + 0.12, L + 1.0, v + 0.9))
            out.append(M.extrude(cs_union(q) ^ qs, d + 0.08) + M.extrude(qs, 0.05))
    if not body.is_empty():
        bl, bh = 2.3, 0.9
        st_, hd = [], []
        k0 = math.floor((v0 - datum) / bh) - 1
        for k in range(k0, int((v1 - datum) / bh) + 2):
            v = datum + k * bh
            u = u0 - 4.0 + (k % 2) * (bl + bl / 2) / 2
            alt = 0
            while u < u1 + 4.0:
                wd = bl if alt % 2 == 0 else bl / 2
                (st_ if alt % 2 == 0 else hd).append(rect(u + 0.12, v + 0.14, u + wd - 0.12, v + bh))
                u += wd
                alt += 1
        out.append(M.extrude(cs_union(st_) ^ body, d) + M.extrude(cs_union(hd) ^ body, d + 0.1) + M.extrude(body, 0.05))
    return union(out)


def foundation_svwater(reg, seed=0):
    """The Severn's raised base: brick in English bond under a moulded stone water table."""
    from . import skins as SK
    u0, v0, u1, v1 = reg.bounds()
    br = SK.brick_bond(rect(u0, v0, u1, v1 - 1.8), "english", bl=2.3, bh=0.9, mortar=0.25, bed=0.25, d=0.22)
    cap = chamfer_box(u0, v1 - 1.8, u1, v1, 0.0, 0.8, c=0.3, square=("u0", "u1"), bottom=0.8)
    return br + cap


TW.FOUNDATION_EXTRA.update(svwater=foundation_svwater)


# ---- cornice ornaments
def course_svfret(L, h, b, pitch, margin, p):
    """The stone belt's Greek key: a running fret of square hooks between two fillets."""
    v0, v1 = 0.25, h - 0.25
    H = v1 - v0
    s = H / 4
    out = [_st(rect(0.2, v0, L - 0.2, v1), b, 0.12)]
    lines = [rect(0.2, v0, L - 0.2, v0 + s * 0.8), rect(0.2, v1 - s * 0.8, L - 0.2, v1)]
    m = 3.2 * s
    n = max(1, int((L - 0.6) / m))
    u0 = (L - n * m) / 2
    for k in range(n):
        a = u0 + k * m
        lines.append(stroke([(a, v0 + s * 0.4), (a, v1 - s * 1.4), (a + 2.0 * s, v1 - s * 1.4), (a + 2.0 * s, v0 + s * 1.6),
                             (a + 1.0 * s, v0 + s * 1.6), (a + 1.0 * s, v0 + s * 2.6)], s * 0.75))
    out.append(_st(_clean(cs_union(lines), 0.15) ^ rect(0.2, v0, L - 0.2, v1), b + 0.12, 0.25))
    return out


def course_svegg(L, h, b, pitch, margin, p):
    """Egg and dart: eggs in their shells, a dart between each pair."""
    v0, v1 = 0.2, h - 0.2
    vm = (v0 + v1) / 2
    ew = (v1 - v0) * 0.85
    n = max(1, int((L - 0.6) / (ew + 0.55)))
    st_ = (L - 0.6) / n
    shells, eggs, darts = [], [], []
    for k in range(n):
        uc = 0.3 + st_ * (k + 0.5)
        e = poly([(uc + ew / 2 * 0.75 * math.cos(a), vm + (v1 - v0) / 2 * 0.95 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 18, endpoint=False)])
        shells.append(e.offset(0.22, RND) - e)
        eggs.append(e.offset(-0.08, RND))
        ud = 0.3 + st_ * k
        darts.append(poly([(ud - 0.18, v1), (ud + 0.18, v1), (ud, v0 + 0.3)]))
    out = [_st(rect(0.2, v0, L - 0.2, v1), b, 0.1)]
    out.append(_st(_clean(cs_union(shells), 0.1), b + 0.1, 0.2))
    out.append(_st(cs_union(eggs), b + 0.1, 0.32))
    out.append(_st(cs_union(darts) ^ rect(0.2, v0, L - 0.2, v1), b + 0.1, 0.2))
    return out


def frieze_svtriglyph(L, h, b, pitch, margin, pair, half):
    """A Doric frieze: a triglyph (three vertical bars, the grooves between them) over every
    bracket station, a rosette in each metope between them."""
    v0, v1 = 0.3, h - 0.3
    out = []
    for u in CO._us(L, pitch, margin, 0.0):
        tw = 1.8
        for k in range(3):
            x = u - tw / 2 + 0.1 + k * 0.6
            out.append(_st(rect(x, v0, x + 0.45, v1), b, 0.35))
    for uc, wd in CO._between(L, pitch, margin, pair, max(half, 1.2)):
        if wd < 2.6:
            continue
        r = min((v1 - v0) / 2 - 0.3, wd / 2 - 0.4, 1.3)
        vm = (v0 + v1) / 2
        pet = cs_union([circle((uc + r * 0.5 * math.cos(a), vm + r * 0.5 * math.sin(a)), r * 0.45, 12) for a in np.linspace(0, 2 * math.pi, 8, endpoint=False)])
        out.append(_st(_clean(pet, 0.15), b, 0.28))
        out.append(_st(circle((uc, vm), r * 0.3, 12), b, 0.42))
    return out, []


def bracket_svmodillion(h, d, t):
    """A Georgian modillion (side profile): a long low block under the soffit ending in a scroll
    at its front, a smaller scroll curling back at its foot against the wall, a leaf under it;
    solid."""
    hh = min(h, 2.2)
    r1 = min(0.9, hh / 2 - 0.05)
    body = rect(0.0, -hh + 0.5, d - r1, 0.0)
    front = circle((d - r1, -r1), r1, 18)
    foot = circle((0.6, -hh + 0.6), 0.6, 14)
    leaf = poly([(d - 2 * r1 - 0.2, -hh + 0.5), (0.9, -hh + 0.5), (1.3, -hh)])
    return cs_union([body, front, foot, leaf, rect(0.0, -hh, 0.8, 0.0)]) ^ rect(0.0, -hh - 1.0, d + 1.0, 0.01)


CO.FRIEZE_EXTRA.update(svtriglyph=frieze_svtriglyph)
CO.COURSE_EXTRA.update(svfret=course_svfret, svegg=course_svegg)
TW.BRACKET_EXTRA.update(svmodillion=bracket_svmodillion)


# ---- windows and doors
def _jack_arch(X, vh, parts, rise=2.6, key=True):
    """A rubbed-brick flat arch over an opening: its voussoirs fanning from a centre below, a
    stone keystone standing proud."""
    n = 9
    sp = (2 * X + 2.0) / n
    for k in range(n):
        a, c_ = -X - 1.0 + k * sp, -X - 1.0 + (k + 1) * sp
        tl = (a - 0.0) * 0.18
        tr = (c_ - 0.0) * 0.18
        vs = poly([(a + 0.06, vh), (c_ - 0.06, vh), (c_ - 0.06 + tr, vh + rise), (a + 0.06 + tl, vh + rise)])
        parts.append(ext(vs, 0.0, 0.7))
    if key:
        parts.append(ext(poly([(-0.9, vh - 0.3), (0.9, vh - 0.3), (1.2, vh + rise + 0.5), (-1.2, vh + rise + 0.5)]), 0.0, 1.2))
    return vh + rise + (0.5 if key else 0.0)


def _sash_g(w, h, pl, plug_cs, cols, rows_lo, rows_hi, meet=0.6):
    inner = plug_cs.offset(-0.6, MIT, 4.0)
    u0, v0, u1, v1 = inner.bounds()
    vm = v0 + (v1 - v0) * rows_lo / (rows_lo + rows_hi)
    lo, hi = rect(u0, v0, u1, vm - meet / 2), rect(u0, vm + meet / 2, u1, v1)
    bars = (_muntins(lo, cols, rows_lo) ^ lo) + (_muntins(hi, cols, rows_hi) ^ hi)
    return _glazed([ext(plug_cs, -pl, -0.6)], lo + hi, pl, bars, plug_cs)


def window_svmain(w=10.0, h=21.0, A=0.9):
    """The ground floor's window: nine over nine in a narrow wood frame with a bead, under a
    rubbed-brick flat arch with a stone keystone, on a stone sill."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    sash = _sash_g(w, h, pl, plug_cs, 3, 3, 3)
    X = w / 2 + A
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             ext((op.offset(A, MIT, 4.0) - op) ^ rect(-50, 0.0, 50, h + A - 0.01), 0.0, 0.6),
             ext((op.offset(0.4, MIT, 4.0) - op) ^ rect(-50, 0.0, 50, h + 0.4), 0.0, 0.8)]
    top = _jack_arch(X, h - 0.01, parts)
    parts.append(chamfer_box(-X - 0.8, -1.3, X + 0.8, 0.01, 0.0, 1.4, c=0.3, bottom=1.4))
    return O._one_piece(sash, parts, op, plug_cs, pl, top, -1.3)


def window_svupper(w=10.0, h=17.0, A=0.9):
    """The upper floor's window: nine over six under the same flat arch, keystone and sill."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    sash = _sash_g(w, h, pl, plug_cs, 3, 2, 3)
    X = w / 2 + A
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             ext((op.offset(A, MIT, 4.0) - op) ^ rect(-50, 0.0, 50, h + A - 0.01), 0.0, 0.6),
             ext((op.offset(0.4, MIT, 4.0) - op) ^ rect(-50, 0.0, 50, h + 0.4), 0.0, 0.8)]
    top = _jack_arch(X, h - 0.01, parts, rise=2.2)
    parts.append(chamfer_box(-X - 0.6, -1.2, X + 0.6, 0.01, 0.0, 1.3, c=0.3, bottom=1.3))
    return O._one_piece(sash, parts, op, plug_cs, pl, top, -1.2)


def _round_op(w, h):
    r = w / 2
    return poly([(-r, 0.0), (r, 0.0)] + [(r * math.cos(a), h - r + r * math.sin(a)) for a in np.linspace(0, math.pi, 25)[1:-1]])


def window_svarch(w=9.0, h=18.0, A=0.9):
    """A hyphen's window: round-headed, six over six with a fan of bars in the head, in a
    rubbed-brick arch with impost blocks and a keystone, a stone sill."""
    op = _round_op(w, h)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    inner = plug_cs.offset(-0.6, MIT, 4.0)
    vs = h - w / 2
    bars = cs_union([rect(x - RIB / 2, -1, x + RIB / 2, vs) for x in (-w / 6, w / 6)] +
                    [rect(-w, v - RIB / 2, w, v + RIB / 2) for v in (vs / 3, 2 * vs / 3, vs)] +
                    [stroke([(0.0, vs), ((w / 2 + 1) * math.cos(a), vs + (w / 2 + 1) * math.sin(a))], RIB) for a in np.linspace(0.6, math.pi - 0.6, 3)])
    sash = _glazed([ext(plug_cs, -pl, -0.6)], inner, pl, bars, plug_cs)
    X = w / 2 + A
    ring = (op.offset(A + 1.4, RND) - op.offset(A - 0.05, RND)) ^ rect(-50, vs, 50, 100)
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             ext((op.offset(A, MIT, 4.0) - op), 0.0, 0.6), ext(ring, 0.0, 0.7)]
    for sg in (-1, 1):
        x0, x1 = sorted((sg * (X - 0.6), sg * (X + 1.6)))
        parts.append(chamfer_box(x0, vs - 0.8, x1, vs + 0.2, 0.0, 1.0, c=0.25, bottom=1.0))
    parts.append(ext(poly([(-0.8, h + A - 0.3), (0.8, h + A - 0.3), (1.0, h + A + 1.8), (-1.0, h + A + 1.8)]), 0.0, 1.2))
    parts.append(chamfer_box(-X - 0.6, -1.2, X + 0.6, 0.01, 0.0, 1.3, c=0.3, bottom=1.3))
    return O._one_piece(sash, parts, op, plug_cs, pl, h + A + 1.8, -1.2)


def window_svcentre(w=10.0, h=20.0, A=1.0):
    """The window over the doorway: round-headed, a fan of bars in its head, between fluted
    pilasters carrying an archivolt with a carved keystone; a balustered apron under the sill."""
    op = _round_op(w, h)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    inner = plug_cs.offset(-0.6, MIT, 4.0)
    vs = h - w / 2
    bars = cs_union([rect(x - RIB / 2, -1, x + RIB / 2, vs) for x in (-w / 6, w / 6)] +
                    [rect(-w, v - RIB / 2, w, v + RIB / 2) for v in (vs / 3, 2 * vs / 3, vs)] +
                    [stroke([(0.0, vs), ((w / 2 + 1) * math.cos(a), vs + (w / 2 + 1) * math.sin(a))], RIB) for a in np.linspace(0.45, math.pi - 0.45, 4)])
    sash = _glazed([ext(plug_cs, -pl, -0.6)], inner, pl, bars, plug_cs)
    X = w / 2 + A
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS), ext(op.offset(A, MIT, 4.0) - op, 0.0, 0.7)]
    for sg in (-1, 1):
        x0, x1 = sorted((sg * (X - 0.1), sg * (X + 1.6)))
        parts.append(chamfer_box(x0, -0.6, x1, vs + 0.6, 0.0, 1.0, c=0.2, square=("v0",)))
        parts.append(ext(cs_union([rect(x, 0.6, x + 0.3, vs - 0.6) for x in np.arange(x0 + 0.3, x1 - 0.2, 0.5)]), 0.99, 1.2))
        parts.append(chamfer_box(x0 - 0.3, vs + 0.59, x1 + 0.3, vs + 1.4, 0.0, 1.3, c=0.25, bottom=0.6))
    arch = (op.offset(A + 1.6, RND) - op.offset(A - 0.05, RND)) ^ rect(-50, vs + 1.39, 50, 100)
    parts.append(ext(arch, 0.0, 1.0))
    parts.append(ext(poly([(-1.0, h + A - 0.4), (1.0, h + A - 0.4), (1.3, h + A + 2.4), (-1.3, h + A + 2.4)]), 0.0, 1.5))
    parts.append(ext(circle((0.0, h + A + 0.9), 0.55, 14), 1.49, 1.75))
    parts.append(chamfer_box(-X - 1.8, -1.4, X + 1.8, 0.01, 0.0, 1.5, c=0.3, bottom=1.5))
    apron = rect(-X - 1.2, -4.6, X + 1.2, -1.39)
    parts.append(ext(apron - apron.offset(-0.5, MIT, 4.0), 0.0, 0.7))
    parts.append(ext(cs_union([rect(x - 0.3, -4.1, x + 0.3, -1.89) + circle((x, -3.0), 0.45, 12) for x in np.linspace(-X + 0.2, X - 0.2, 6)]), 0.0, 0.9))
    return O._one_piece(sash, parts, op, plug_cs, pl, h + A + 2.4, -4.6)


def window_svoculus(r=3.6, A=1.0):
    """The pediment's oculus: a round light with four bars crossing, in a moulded ring with
    four keystones."""
    op = circle((0.0, r), r, 32)
    plug_cs = op.offset(-O.CLR, RND)
    pl = O.PLUG
    inner = plug_cs.offset(-0.6, RND)
    bars = cs_union([rect(-RIB / 2, -1, RIB / 2, 2 * r + 1), rect(-r - 1, r - RIB / 2, r + 1, r + RIB / 2)])
    sash = _glazed([ext(plug_cs, -pl, -0.6)], inner, pl, bars, plug_cs)
    parts = [ext(op - op.offset(-RIB, RND), 0.0, O.CAS), ext(op.offset(A, RND) - op, 0.0, 0.8),
             ext(op.offset(A + 0.5, RND) - op.offset(A - 0.01, RND), 0.0, 1.1)]
    for a in (0.0, math.pi / 2, math.pi, 3 * math.pi / 2):
        c, s = math.cos(a), math.sin(a)
        k = poly([(c * (r + A - 0.3) - s * 0.6, r + s * (r + A - 0.3) + c * 0.6), (c * (r + A - 0.3) + s * 0.6, r + s * (r + A - 0.3) - c * 0.6),
                  (c * (r + A + 1.2) + s * 0.8, r + s * (r + A + 1.2) - c * 0.8), (c * (r + A + 1.2) - s * 0.8, r + s * (r + A + 1.2) + c * 0.8)])
        parts.append(ext(k, 0.0, 1.3))
    return O._one_piece(sash, parts, op, plug_cs, pl, 2 * r + A + 1.2, -A - 1.2)


def window_svwing(w=10.0, h=24.0, A=0.9):
    """A wing's tall window in the canted bay: twelve over twelve under the flat arch."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    sash = _sash_g(w, h, pl, plug_cs, 3, 4, 4)
    X = w / 2 + A
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             ext((op.offset(A, MIT, 4.0) - op) ^ rect(-50, 0.0, 50, h + A - 0.01), 0.0, 0.6),
             ext((op.offset(0.4, MIT, 4.0) - op) ^ rect(-50, 0.0, 50, h + 0.4), 0.0, 0.8)]
    top = _jack_arch(X, h - 0.01, parts)
    parts.append(chamfer_box(-X - 0.8, -1.3, X + 0.8, 0.01, 0.0, 1.4, c=0.3, bottom=1.4))
    return O._one_piece(sash, parts, op, plug_cs, pl, top, -1.3)


def window_svlunette(w=9.0, A=0.9):
    """A wing's lunette over its tall window: a half-round light with radiating bars round a
    hub, in a brick arch with a keystone, on a stone band."""
    r = w / 2
    op = poly([(-r, 0.0), (r, 0.0)] + [(r * math.cos(a), r * math.sin(a)) for a in np.linspace(0, math.pi, 25)[1:-1]])
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    inner = plug_cs.offset(-0.5, MIT, 4.0)
    bars = cs_union([stroke([(0.0, 0.0), ((r + 1) * math.cos(a), (r + 1) * math.sin(a))], RIB) for a in np.linspace(0.5, math.pi - 0.5, 5)]) + circle((0.0, 0.0), 1.2, 18)
    sash = _glazed([ext(plug_cs, -pl, -0.6)], inner, pl, bars, plug_cs)
    ring = (op.offset(A + 1.3, RND) - op.offset(A - 0.05, RND)) ^ rect(-50, 0.0, 50, 50)
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS), ext((op.offset(A, RND) - op) ^ rect(-50, 0.0, 50, 50), 0.0, 0.6),
             ext(ring, 0.0, 0.7), ext(poly([(-0.8, r + A - 0.3), (0.8, r + A - 0.3), (1.0, r + A + 1.6), (-1.0, r + A + 1.6)]), 0.0, 1.2),
             chamfer_box(-r - A - 1.8, -1.2, r + A + 1.8, 0.01, 0.0, 1.2, c=0.3, bottom=1.2)]
    return O._one_piece(sash, parts, op, plug_cs, pl, r + A + 1.6, -1.2)


def door_svmain(w=10.0, h=22.0, A=1.2):
    """The Severn's doorway (after Buckland's at Annapolis): a six-panel door under a fanlight
    of radiating bars in a round arch with a keystone, between Ionic columns half out of the
    wall on plinths, carrying an entablature (architrave, a frieze carved with a garland, a
    dentilled cornice) and a pediment."""
    r = w / 2
    vs = h
    op = poly([(-r, 0.0), (r, 0.0)] + [(r * math.cos(a), vs + r * math.sin(a)) for a in np.linspace(0, math.pi, 25)[1:-1]])
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    fan = (op ^ rect(-50, vs + 0.5, 50, 100)).offset(-0.6, MIT, 4.0)
    parts_s = [ext(plug_cs - plug_cs.offset(-0.5, MIT, 4.0), -pl, 0.0), ext(plug_cs, -pl, -0.6)]
    parts_s = [p_ - ext(fan, -pl - 1, 0.0) for p_ in parts_s]
    parts_s.append(ext(fan, -pl, -pl + O.GLASS))
    leads = [stroke([(0.0, vs + 0.5), ((r + 1) * math.cos(a), vs + 0.5 + (r + 1) * math.sin(a))], RIB) for a in np.linspace(0.35, math.pi - 0.35, 7)]
    leads.append(circle((0.0, vs + 0.5), 1.4, 20) - circle((0.0, vs + 0.5), 0.8, 16))
    parts_s.append(ext(cs_union(leads) ^ fan.offset(0.1, MIT, 4.0), -pl + O.GLASS - 0.01, -0.5))
    parts_s.append(ext(rect(-r + 0.4, vs - 0.1, r - 0.4, vs + 0.5), -0.65, -0.1))
    ph = (vs - 2.0) / 3
    for j in range(3):
        for sg in (-1, 1):
            vb = 1.0 + j * ph
            pan = rect(min(sg * 0.5, sg * (r - 0.9)), vb, max(sg * 0.5, sg * (r - 0.9)), vb + ph - 0.8)
            parts_s.append(ext(pan - pan.offset(-0.45, MIT, 4.0), -0.65, -0.2))
            parts_s.append(chamfer_box(*pan.offset(-0.9, MIT, 4.0).bounds(), -0.65, 0.35, c=0.2))
    X = r + A
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS), ext((op.offset(A, RND) - op) ^ rect(-50, 0.0, 50, 100), 0.0, 0.8)]
    parts.append(ext(poly([(-0.9, vs + r + A - 0.4), (0.9, vs + r + A - 0.4), (1.2, vs + r + A + 1.8), (-1.2, vs + r + A + 1.8)]), 0.0, 1.3))
    # the columns: plinth, base, shaft (half out of the wall), Ionic capital with volutes
    xc = X + 2.2
    zt = vs + r + A + 1.0                                     # the entablature's foot
    for sg in (-1, 1):
        x = sg * xc
        parts.append(chamfer_box(x - 1.6, 0.0, x + 1.6, 2.6, 0.0, 1.8, c=0.25, square=("v0",)))
        parts.append(chamfer_box(x - 1.4, 2.59, x + 1.4, 3.2, 0.0, 1.7, c=0.25, bottom=0.6))
        shaft = M.cylinder(zt - 1.2 - 3.0, 1.2, 1.05, 24).translate([x, 0.0, 0.0])          # into the base and the capital
        parts.append(shaft.transform(np.array([[1.0, 0, 0, 0], [0, 0, 1.0, 3.0], [0, -1.0, 0, 0]])) ^ ext(rect(x - 2, 0, x + 2, zt), 0.0, 3.0))
        parts.append(chamfer_box(x - 1.9, zt - 1.41, x + 1.9, zt - 0.4, 0.0, 1.6, c=0.25, bottom=1.0))
        for s2 in (-1, 1):
            parts.append(ext(circle((x + s2 * 1.5, zt - 1.2), 0.65, 14), 1.0, 1.8))
        parts.append(chamfer_box(x - 1.7, zt - 0.41, x + 1.7, zt + 0.01, 0.0, 1.6, c=0.2, bottom=0.4))
    E = xc + 2.4
    parts.append(ext(rect(-E, zt, E, zt + 1.2), 0.0, 1.6))                                  # architrave
    parts.append(ext(rect(-E, zt + 1.19, E, zt + 3.4), 0.0, 1.5))                           # frieze
    gar = [stroke([(u, zt + 2.9)] + [(u + (2 * xc / 5) * t, zt + 2.9 - 1.3 * math.sin(math.pi * t)) for t in np.linspace(0.1, 1.0, 9)], 0.45)
           for u in np.linspace(-xc, xc - 2 * xc / 5, 5)]
    gar += [circle((u, zt + 2.9), 0.45, 12) for u in np.linspace(-xc, xc, 6)]
    parts.append(ext(_clean(cs_union(gar), 0.15) ^ rect(-E + 0.3, zt + 1.3, E - 0.3, zt + 3.3), 1.49, 1.75))
    parts.append(chamfer_box(-E - 0.6, zt + 3.39, E + 0.6, zt + 4.0, 0.0, 2.0, c=0.3, bottom=0.6))     # bed moulding
    parts.append(ext(cs_union([rect(u - 0.3, zt + 3.39, u + 0.3, zt + 4.0) for u in np.arange(-E, E + 0.1, 0.9)]) ^ rect(-E, zt, E, zt + 5), 1.99, 2.3))
    parts.append(chamfer_box(-E - 1.2, zt + 3.99, E + 1.2, zt + 4.8, 0.0, 2.4, c=0.3, bottom=0.7))     # corona
    ped = poly([(-E - 1.2, zt + 4.79), (E + 1.2, zt + 4.79), (0.0, zt + 4.79 + (E + 1.2) * 0.42)])
    parts.append(ext(ped - ped.offset(-1.0, MIT, 4.0), 0.0, 2.2))
    parts.append(ext(ped.offset(-1.0, MIT, 4.0), 0.0, 0.9))
    top = zt + 4.79 + (E + 1.2) * 0.42
    return O._one_piece(parts_s, parts, op, plug_cs, pl, top, 0.0, land_extra=rect(-E - 1.2, 0.0, E + 1.2, top))


def door_svback(w=9.6, h=21.0, A=1.0):
    """The garden door: six panels under a four-light transom, a casing with a pulvinated
    frieze and a cornice on two consoles."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    vt = h - 3.4
    tr = rect(-w / 2 + 0.6, vt + 0.5, w / 2 - 0.6, h - 0.6)
    parts_s = [ext(plug_cs - plug_cs.offset(-0.5, MIT, 4.0), -pl, 0.0), ext(plug_cs, -pl, -0.6)]
    parts_s = [p_ - ext(tr, -pl - 1, 0.0) for p_ in parts_s]
    parts_s.append(ext(tr, -pl, -pl + O.GLASS))
    parts_s.append(ext(cs_union([rect(x - RIB / 2, vt, x + RIB / 2, h) for x in np.linspace(-w / 2, w / 2, 5)[1:-1]]) ^ tr.offset(0.1, MIT, 4.0),
                       -pl + O.GLASS - 0.01, -0.5))
    parts_s.append(ext(rect(-w / 2 + 0.4, vt - 0.1, w / 2 - 0.4, vt + 0.5), -0.65, -0.1))
    ph = (vt - 2.0) / 3
    for j in range(3):
        for sg in (-1, 1):
            vb = 1.0 + j * ph
            pan = rect(min(sg * 0.5, sg * (w / 2 - 0.9)), vb, max(sg * 0.5, sg * (w / 2 - 0.9)), vb + ph - 0.8)
            parts_s.append(ext(pan - pan.offset(-0.45, MIT, 4.0), -0.65, -0.2))
            parts_s.append(chamfer_box(*pan.offset(-0.9, MIT, 4.0).bounds(), -0.65, 0.35, c=0.2))
    X = w / 2 + A
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS), ext((op.offset(A, MIT, 4.0) - op) ^ rect(-50, 0.0, 50, 100), 0.0, 0.8)]
    vh = h + A - 0.01
    parts.append(M.hull_points([(x, v, z) for x in (-X, X) for (v, z) in ((vh, 0.0), (vh, 0.6), (vh + 0.9, 1.2), (vh + 1.8, 0.6), (vh + 1.8, 0.0))]))
    for sg in (-1, 1):
        u = sg * (X + 0.3)
        parts.append(ext(cs_union([rect(u - 0.6, vh - 2.2, u + 0.6, vh + 1.8), circle((u, vh - 2.2), 0.7, 14)]), 0.0, 1.6))
    parts.append(chamfer_box(-X - 1.4, vh + 1.79, X + 1.4, vh + 2.6, 0.0, 2.0, c=0.3, bottom=2.0))
    return O._one_piece(parts_s, parts, op, plug_cs, pl, vh + 2.6, 0.0)


def raking_severn(L, slope, d_eave, skin=1.6, depth=2.2, rake=3.0):
    """The pediment's raking cornice (facade frame of the tympanum, hung under the rake from
    w = 0, the wall, out to ``rake``): a fascia and a cymatium stepping out along each rake,
    a row of little modillion blocks under it, tied to the board; it prints face-up."""
    s = slope
    c = math.hypot(1.0, s)
    a_l = np.array([-d_eave, 0.0])
    tip = np.array([L / 2, s * (L / 2 + d_eave)])
    a_r = np.array([L + d_eave, 0.0])
    out = []
    for k, (dd, w0, w1) in enumerate(((skin + depth, 0.0, rake * 0.55), (skin + depth * 0.55, 0.0, rake * 0.8), (skin + 0.5, 0.0, rake))):
        band = []
        for a in (a_l, a_r):
            n = np.array([s, -1.0]) / c if a[0] < L / 2 else np.array([-s, -1.0]) / c
            band.append(poly([tuple(a), tuple(tip), tuple(tip + n * dd), tuple(a + n * dd)]))
        out.append(ext(cs_union(band) ^ rect(-d_eave - 5, -0.01, L + d_eave + 5, tip[1] + 5), w0, w1))
    mods = []
    for a in (a_l, a_r):
        n = np.array([s, -1.0]) / c if a[0] < L / 2 else np.array([-s, -1.0]) / c
        dirv = (tip - a) / np.linalg.norm(tip - a)
        run = float(np.linalg.norm(tip - a))
        for k in range(1, int(run / 2.2)):
            p = a + dirv * (2.2 * k) + n * (skin + depth - 0.05)
            mods.append(poly([tuple(p - dirv * 0.45), tuple(p + dirv * 0.45), tuple(p + dirv * 0.45 + n * 0.9), tuple(p - dirv * 0.45 + n * 0.9)]))
    out.append(ext(cs_union(mods) ^ rect(-d_eave - 5, -0.01, L + d_eave + 5, tip[1] + 5), 0.0, rake * 0.45))
    return union(out)


def chimney_severn(w=8.0, d=6.0, h=24.0):
    """A Georgian stack (stands on z = 0, its roof pocket's floor): Flemish bond, a stone band, a
    four-course corbelled cap and a flat stone coping."""
    h = round(h / 0.2) * 0.2
    sh = round((h - 3.2) / 0.2) * 0.2
    body = box([-w / 2, -d / 2, 0], [w / 2, d / 2, sh]) + TW._skin(w, d, 0.0, sh - 2.8, TW._brick("flemish"))
    zb = sh - 2.8
    body = body + box([-w / 2 - 0.3, -d / 2 - 0.3, zb], [w / 2 + 0.3, d / 2 + 0.3, zb + 1.0]) + TW._corbel_out(w, d, zb, 0.3)
    z = sh
    for k in range(4):
        g = 0.22 * (k + 1)
        body = body + TW._corbel_out(w + 2 * (g - 0.22), d + 2 * (g - 0.22), z + 0.22, 0.22) + \
            box([-w / 2 - g, -d / 2 - g, z + 0.21], [w / 2 + g, d / 2 + g, z + 0.6])
        z += 0.6
    body = body + box([-w / 2 - 1.1, -d / 2 - 1.1, z - 0.01], [w / 2 + 1.1, d / 2 + 1.1, z + 0.7])
    for y in (-d / 4, d / 4):
        body = body - box([-w / 2 + 1.2, y - d / 4 + 0.6, z - 1.5], [w / 2 - 1.2, y + d / 4 - 0.6, z + 1.0])
    return body


# ================================================================== the Raquette (house 110)
# After Sagamore, Raquette Lake, New York (1897, William West Durant), the great camp lodge: a
# Swiss-chalet log lodge three storeys high under a steep front gable whose roof runs far out
# over the gable front on great log brackets, stacked balconies across that front, a boulder
# chimney climbing its side; a dining cabin at right angles reached by a covered walk.

def _log_prism(u0, u1, vc, r, w0=0.0, full=False):
    """A log lying along u from u0 to u1, its axis at height vc: round over the top, its under
    side cut at 45 degrees so it prints upright with nothing hanging; a half log on the face
    (from w0 out) or a full one (``full``)."""
    pts = []
    for a in np.linspace(-math.pi / 4, 5 * math.pi / 4, 12):
        pts.append((r * math.cos(a), vc + r * math.sin(a)))
    pts.append((0.0, vc - r * math.sqrt(2)))
    prof = poly(pts)
    if not full:
        prof = prof ^ rect(0.0, vc - 2 * r, 2 * r, vc + 2 * r)
    m = M.extrude(prof, u1 - u0)
    return m.transform(np.array([[0, 0, 1.0, u0], [0, 1.0, 0, 0], [1.0, 0, 0, w0]]))


def halflog_raquette(region, datum=0.0, pitch=2.8, L=None, shift=0.0, out=2.2):
    """The lodge's walls: half-round logs laid up on the face, a chink between each, and at the
    corners (``L``, the face's length) every other log running out past the corner as a full
    round log with its end showing (the crossing wall's logs take the other courses: ``shift``
    0 or 0.5)."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    r = pitch / 2 - 0.12
    logs, ends = [], []
    k0 = math.floor((v0 - datum) / pitch - shift) - 1
    for k in range(k0, int((v1 - datum) / pitch - shift) + 2):
        vc = datum + (k + shift + 0.5) * pitch
        logs.append(_log_prism(u0 - 1.0, u1 + 1.0, vc, r * 0.92))
        if L is not None:
            for a, b in ((-out, 0.2), (L - 0.2, L + out)):
                # only where the face is dressed the log's whole height (none pokes into a
                # cornice band, the floor or a joint)
                test = rect(max(0.0, min(a, L - 1.0)), vc - r * 1.45, min(L, max(b, 1.0)), vc + r)
                if (test - region).area() < 0.05:
                    ends.append(_log_prism(a, b, vc, r, w0=-r * 0.95, full=True))
    reg = M.extrude(region.offset(0.01, MIT, 4.0), 3.0).translate([0, 0, -1.0])
    out_ = [M.extrude(region, 0.05), union(logs) ^ reg]
    if ends:
        out_.append(union(ends))
    return union(out_)


def bark_raquette(region, datum=0.0, seed=0):
    """The gable's cedar-bark shingles: tall slabs of bark in courses, each slab's surface
    ridged with the bark's long fibres, the butts uneven."""
    if region.is_empty():
        return M()
    rng = np.random.default_rng(seed)
    u0, v0, u1, v1 = region.bounds()
    pitch = 3.2
    slabs, fib = [], []
    for j in range(int(math.floor((v0 - datum) / pitch)) - 1, int(math.ceil((v1 - datum) / pitch)) + 1):
        v = datum + j * pitch
        u = u0 - rng.uniform(0.0, 3.0)
        while u < u1 + 1.0:
            wd = rng.uniform(2.2, 4.0)
            dv = rng.uniform(-0.3, 0.3)
            slabs.append(poly([(u + 0.15, v + 0.2 + dv), (u + wd - 0.15, v + 0.2 - dv), (u + wd - 0.15, v + pitch + 0.2), (u + 0.15, v + pitch + 0.2)]))
            for x in np.arange(u + 0.6, u + wd - 0.4, 0.75):
                fib.append(rect(x - 0.12, v + 0.4, x + 0.12, v + pitch))
            u += wd
    s_ = cs_union(slabs) ^ region
    out = [M.extrude(region, 0.05), M.extrude(s_, 0.3)]
    f_ = cs_union(fib) ^ s_.offset(-0.2, MIT, 4.0)
    if not f_.is_empty():
        out.append(M.extrude(f_, 0.15).translate([0, 0, 0.29]))
    return union(out)


def foundation_rqboulder(reg, seed=0):
    """The lodge's footing: round boulders laid up dry, each a low dome, small stones packed
    between."""
    rng = np.random.default_rng(seed + 31)
    u0, v0, u1, v1 = reg.bounds()
    out = [M.extrude(reg, 0.1)]
    v = v0 + 0.2
    while v < v1 - 1.0:
        h = rng.uniform(2.2, 3.4)
        u = u0 + rng.uniform(-1.0, 0.5)
        while u < u1:
            wd = rng.uniform(2.6, 4.6)
            c = (u + wd / 2, min(v + h / 2, v1 - 1.0))
            ell = poly([(c[0] + wd / 2 * 0.95 * math.cos(a), c[1] + h / 2 * 0.9 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 14, endpoint=False)]) ^ reg
            if not ell.is_empty():
                for k, (o_, d_) in enumerate(((0.0, 0.25), (0.35, 0.22), (0.75, 0.18))):
                    e2 = ell.offset(-o_, RND)
                    if not e2.is_empty():
                        out.append(M.extrude(e2, d_).translate([0, 0, 0.1 + sum(dd for _, dd in ((0.0, 0.25), (0.35, 0.22), (0.75, 0.18))[:k]) - 0.01 * k]))
            u += wd
        v += h
    return union(out)


TW.FOUNDATION_EXTRA.update(rqboulder=foundation_rqboulder)


# ---- cornice ornaments
def frieze_rqlogends(L, h, b, pitch, margin, pair, half):
    """The storey joint's frieze: the floor logs' round ends in a row, each with its growth
    rings, between two half-log rails."""
    v0, v1 = 0.3, h - 0.3
    vm = (v0 + v1) / 2
    r = min((v1 - v0) / 2 - 0.55, 1.4)
    out = [_st(rect(0.2, v0, L - 0.2, v0 + 0.5) + rect(0.2, v1 - 0.5, L - 0.2, v1), b, 0.35)]
    sp = 2 * r + 0.8
    n = max(1, int((L - 0.6) / sp))
    u0 = (L - (n - 1) * sp) / 2
    for k in range(n):
        uc = u0 + k * sp
        out.append(_st(circle((uc, vm), r, 20), b, 0.55))
        out.append(_st(circle((uc, vm), r * 0.62, 18) - circle((uc, vm), r * 0.42, 16), b + 0.55, 0.12))
    return out, []


def course_rqtwig(L, h, b, pitch, margin, p):
    """A twig course: two rails of round twigs with short twigs crossing between them in an X
    every few millimetres."""
    out = [_st(rect(0.2, 0.15, L - 0.2, 0.55) + rect(0.2, h - 0.55, L - 0.2, h - 0.15), b, 0.35)]
    xs = []
    st_ = 2.2
    for u in np.arange(0.6, L - 1.6, st_):
        xs.append(stroke([(u, 0.4), (u + st_ * 0.8, h - 0.4)], 0.4))
        xs.append(stroke([(u, h - 0.4), (u + st_ * 0.8, 0.4)], 0.4))
    out.append(_st(_clean(cs_union(xs), 0.15) ^ rect(0.2, 0.15, L - 0.2, h - 0.15), b, 0.3))
    return out


def frieze_rqmosaic(L, h, b, pitch, margin, pair, half):
    """The eave's frieze: Adirondack twig mosaic, split twigs laid in nested diamonds, a
    sunburst of twigs at each diamond's heart, between rails."""
    v0, v1 = 0.3, h - 0.3
    vm = (v0 + v1) / 2
    H = (v1 - v0) / 2 - 0.4
    out = [_st(rect(0.2, v0, L - 0.2, v0 + 0.45) + rect(0.2, v1 - 0.45, L - 0.2, v1), b, 0.3)]
    dw = H * 2.2
    n = max(1, int((L - 0.6) / dw))
    u0 = (L - n * dw) / 2
    tw = []
    for k in range(n):
        uc = u0 + dw * (k + 0.5)
        for sc in (1.0, 0.55):
            pts = [(uc - dw / 2 * sc, vm), (uc, vm + H * sc), (uc + dw / 2 * sc, vm), (uc, vm - H * sc), (uc - dw / 2 * sc, vm)]
            tw.append(stroke(pts, 0.42))
        tw.append(circle((uc, vm), 0.4, 10))
    out.append(_st(_clean(cs_union(tw), 0.15) ^ rect(0.2, v0, L - 0.2, v1), b, 0.32))
    return out, []


CO.FRIEZE_EXTRA.update(rqlogends=frieze_rqlogends, rqmosaic=frieze_rqmosaic)
CO.COURSE_EXTRA.update(rqtwig=course_rqtwig)


# ---- windows and doors
def _log_casing(parts, w, h, A=1.4, d=1.2, top=None):
    """A casing of half logs round an opening, the head log running past the jambs (notched
    over them), bark lines along each."""
    X = w / 2 + A
    hh = h if top is None else top
    for sg in (-1, 1):
        x0, x1 = sorted((sg * (w / 2), sg * X))
        parts.append(chamfer_box(x0, -0.2, x1, hh, 0.0, d, c=0.45, square=("v0",)))
    parts.append(chamfer_box(-X - 1.4, hh - 0.01, X + 1.4, hh + A, 0.0, d + 0.2, c=0.5, bottom=0.6))
    parts.append(ext(cs_union([rect(x - 0.1, hh + 0.3, x + 0.1, hh + A - 0.3) for x in np.arange(-X - 0.8, X + 0.9, 1.1)]), d + 0.15, d + 0.3))
    return X


def window_rqlower(w=10.0, h=17.0):
    """The lodge's ground-floor window: a pair of casements of six lights each in a casing of
    half logs, the head log running past, a sill log."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    inner = plug_cs.offset(-0.6, MIT, 4.0)
    b = inner.bounds()
    bars = cs_union([rect(-0.45, -1.0, 0.45, h + 1.0)] + [rect(x - RIB / 2, -1.0, x + RIB / 2, h + 1.0) for x in (-w / 4, w / 4)] +
                    [rect(-w, v - RIB / 2, w, v + RIB / 2) for v in (b[1] + (b[3] - b[1]) / 3, b[1] + 2 * (b[3] - b[1]) / 3)])
    sash = _glazed([ext(plug_cs, -pl, -0.6)], inner, pl, bars, plug_cs)
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS)]
    X = _log_casing(parts, w, h)
    parts.append(chamfer_box(-X - 0.8, -1.4, X + 0.8, 0.01, 0.0, 1.5, c=0.5, bottom=1.5))
    return O._one_piece(sash, parts, op, plug_cs, pl, h + 1.4, -1.4)


def window_rqupper(w=9.0, h=15.0):
    """The upper floors' window: a pair of four-light casements under a little hood of bark
    shingles on two twig brackets, a log casing."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    inner = plug_cs.offset(-0.6, MIT, 4.0)
    bars = cs_union([rect(-0.45, -1.0, 0.45, h + 1.0), rect(-w, h / 2 - RIB / 2, w, h / 2 + RIB / 2)] +
                    [rect(x - RIB / 2, -1.0, x + RIB / 2, h + 1.0) for x in (-w / 4, w / 4)])
    sash = _glazed([ext(plug_cs, -pl, -0.6)], inner, pl, bars, plug_cs)
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS)]
    X = _log_casing(parts, w, h, A=1.1, d=1.0)
    vh = h + 1.1
    hood = M.hull_points([(x, v, wv) for x in (-X - 1.6, X + 1.6) for (v, wv) in ((vh + 0.6, 0.0), (vh + 2.6, 0.0), (vh + 0.6, 2.6), (vh + 1.0, 2.6))])
    parts.append(hood)
    for sg in (-1, 1):
        x = sg * (X + 0.4)
        parts.append(ext(stroke([(x, vh - 2.4), (x + sg * 1.6, vh + 0.7)], 0.6), 0.0, 1.0))
        parts.append(M.hull_points([(x + dx, v, wv) for dx in (-0.3, 0.3) for (v, wv) in ((vh - 2.4, 0.0), (vh - 2.4, 0.5), (vh + 0.7, 0.0), (vh + 0.7, 2.4))]))
    parts.append(chamfer_box(-X - 0.6, -1.2, X + 0.6, 0.01, 0.0, 1.3, c=0.4, bottom=1.3))
    return O._one_piece(sash, parts, op, plug_cs, pl, vh + 2.6, -2.4)


def door_rqfront(w=12.0, h=24.0):
    """The lodge's front door: two leaves of boards laid in a chevron, iron straps across, a
    small square light high in each, in a casing of half logs under a heavy lintel log."""
    from .colonial import _strap
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    lights = [rect(sg * w / 4 - 1.2, h * 0.68, sg * w / 4 + 1.2, h * 0.68 + 2.8) for sg in (-1, 1)]
    glass = cs_union(lights)
    parts_s = [ext(plug_cs - plug_cs.offset(-0.5, MIT, 4.0), -pl, 0.0), ext(plug_cs, -pl, -0.6)]
    parts_s = [p_ - ext(glass, -pl - 1, 0.0) for p_ in parts_s]
    parts_s.append(ext(glass, -pl, -pl + O.GLASS))
    parts_s.append(ext(cs_union([lt.offset(0.5, MIT, 4.0) - lt for lt in lights]), -0.65, -0.2))
    face = plug_cs.offset(-0.5, MIT, 4.0) - glass.offset(0.5, MIT, 4.0)
    fb = face.bounds()
    chev = []
    for sg in (-1, 1):
        a, c_ = sorted((sg * 0.3, sg * (w / 2 - 0.5)))
        for v in np.arange(-w, h + w, 1.6):
            chev.append(stroke([(a, v), (c_, v + sg * (c_ - a) * 0.8)], 0.22))
    parts_s.append(ext(_clean(face - cs_union(chev), 0.1), -0.65, -0.3))
    parts_s.append(ext(rect(-0.3, 0.0, 0.3, h - 0.5), -0.65, -0.1))
    for v in (2.4, h * 0.5, h * 0.68 - 1.6):
        for sg in (-1, 1):
            parts_s.append(ext(_strap(sg * (w / 2 - 0.6), sg * 0.6, v) ^ face.offset(0.3, MIT, 4.0), -0.31, -0.08))
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS)]
    X = _log_casing(parts, w, h, A=1.8, d=1.5)
    return O._one_piece(parts_s, parts, op, plug_cs, pl, h + 1.8, 0.0)


def door_rqbalcony(w=9.0, h=20.0):
    """A balcony door: glazed above (six lights) over two boarded panels, in a half-log casing."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    gl = rect(-w / 2 + 1.0, h * 0.42, w / 2 - 1.0, h - 1.0)
    parts_s = [ext(plug_cs - plug_cs.offset(-0.5, MIT, 4.0), -pl, 0.0), ext(plug_cs, -pl, -0.6)]
    parts_s = [p_ - ext(gl, -pl - 1, 0.0) for p_ in parts_s]
    parts_s.append(ext(gl, -pl, -pl + O.GLASS))
    gb = gl.bounds()
    bars = cs_union([rect(-RIB / 2, gb[1] - 1, RIB / 2, gb[3] + 1)] + [rect(gb[0] - 1, v - RIB / 2, gb[2] + 1, v + RIB / 2)
                                                                     for v in (gb[1] + (gb[3] - gb[1]) / 3, gb[1] + 2 * (gb[3] - gb[1]) / 3)])
    parts_s.append(ext(bars ^ gl.offset(0.1, MIT, 4.0), -pl + O.GLASS - 0.01, -0.5))
    for sg in (-1, 1):
        a, c_ = sorted((sg * 0.5, sg * (w / 2 - 1.0)))
        pan = rect(a, 1.0, c_, h * 0.42 - 1.0)
        parts_s.append(ext(pan - pan.offset(-0.45, MIT, 4.0), -0.65, -0.2))
        parts_s.append(ext(cs_union([rect(x - 0.1, 1.5, x + 0.1, h * 0.42 - 1.5) for x in np.arange(a + 0.9, c_ - 0.5, 0.9)]), -0.65, -0.35))
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS)]
    X = _log_casing(parts, w, h, A=1.2, d=1.1)
    return O._one_piece(parts_s, parts, op, plug_cs, pl, h + 1.2, 0.0)


# ---- the rustic porch: posts, railings, log brackets; the boulder chimney
def post_raquette(h, r=1.5, seed=0):
    """A rustic post: a round cedar log with the bark on (long shallow fissures), a little
    taper, and two branch stubs cut off short, angled upward (from z = 0 to h)."""
    rng = np.random.default_rng(seed)
    body = M.cylinder(h, r, r * 0.9, 20)
    fis = []
    for k in range(10):
        a = 2 * math.pi * k / 10 + rng.uniform(-0.2, 0.2)
        z0 = rng.uniform(0.5, h * 0.3)
        fis.append(box([-0.12, -0.12, z0], [0.12, 0.12, z0 + rng.uniform(h * 0.4, h * 0.65)]).translate([r * 0.98, 0, 0]).rotate([0, 0, math.degrees(a)]))
    body = body - union(fis)
    for k in range(2):
        z = h * rng.uniform(0.3, 0.7)
        a = rng.uniform(0, 360)
        stub = M.cylinder(1.6, 0.55, 0.45, 12).rotate([0, 45, 0]).translate([r * 0.6, 0, z]).rotate([0, 0, a])
        body = body + stub
    return body


def rail_raquette(L, h=7.0, t=1.0):
    """A rustic railing between two posts (u along it, v up, w across, standing on v = 0): a log
    top rail and a bottom rail with crooked branches crossing between them in a run of Xs, a
    short upright at each crossing; flat, printed with the frame."""
    top, bot = rect(0.0, h - 1.2, L, h), rect(0.0, 0.0, L, 0.9)
    n = max(1, int(round(L / (h * 1.1))))
    br = []
    for k in range(n):
        a, c_ = L * k / n + 0.3, L * (k + 1) / n - 0.3
        mid = (a + c_) / 2
        br.append(stroke([(a, 0.8), (mid - 0.4, h * 0.5 + 0.5), (c_, h - 1.1)], 0.6))
        br.append(stroke([(a, h - 1.1), (mid + 0.4, h * 0.5 - 0.5), (c_, 0.8)], 0.6))
        br.append(rect(a - 0.3, 0.0, a + 0.3, h))
    br.append(rect(L - 0.6, 0.0, L, h))
    return ext(_clean(cs_union([top, bot] + br), 0.15) ^ rect(0.0, 0.0, L, h), -t / 2, t / 2)


def bracket_raquette(H=24.0, D=15.0, r=1.5):
    """A great log bracket under the front overhang (in its plane: y out from the wall, z up,
    x across = its thickness): a post log down the wall, a knee brace log rising from it to the
    tip of an outrigger log under the roof, and a curved branch tying the two; flat sided
    (printed on its side), its faces rounded over to read as logs."""
    post = rect(0.0, -H, 2 * r, 0.0)
    arm = rect(0.0, -2 * r, D, 0.0)
    brace = stroke([(r, -H + 2.0), (D - 2.0, -r)], 2 * r)
    tie = stroke([(r * 2, -H * 0.55)] + [(r * 2 + (D * 0.5) * t, -H * 0.55 + (H * 0.42) * t ** 0.6) for t in np.linspace(0.1, 1.0, 6)], 1.0)
    cs = cs_union([post, arm, brace, tie]) ^ rect(0.0, -H, D, 0.0)
    m = M.extrude(cs.offset(-0.4, RND), 2 * r).translate([0, 0, -r]) + M.extrude(cs, 2 * r - 0.8).translate([0, 0, -r + 0.4])
    return m.transform(np.array([[0, 0, 1.0, 0], [1.0, 0, 0, 0], [0, 1.0, 0, 0]]))


def chimney_raquette(h=110.0, w0=30.0, d0=16.0, w1=16.0, d1=11.0, seed=0, boulders=True):
    """The great boulder chimney (stands on z = 0, its back on the wall at local y = 0 and
    running out to +y): a tapering shaft of round fieldstones, each a squashed dome, packed
    with smaller ones, a flat stone cap; boulders heaped at its foot."""
    rng = np.random.default_rng(seed)
    body = M.hull_points([(x, y, z) for z, w, d in ((0.0, w0, d0), (h * 0.45, w0 * 0.78, d0 * 0.9), (h - 2.0, w1, d1))
                          for x in (-w / 2, w / 2) for y in (0.0, d)])
    stones = []
    z = 0.4
    while z < h - 4.0:
        f = z / h
        w = w0 + (w1 - w0) * f
        d = d0 + (d1 - d0) * f
        sh = rng.uniform(2.2, 3.6)
        for face in range(3):
            if face == 1:
                u, ul = -w / 2, w
            else:
                u, ul = 0.0, d
            x = u + rng.uniform(-0.5, 1.0)
            while x < u + ul - 1.0:
                sw = rng.uniform(2.4, 4.4)
                cx = x + sw / 2
                s_ = M.sphere(1.0, 14).scale([sw / 2, 0.75, sh / 2])
                if face == 1:
                    pos = [cx, d * 0.96 + 0.02, z + sh / 2]
                    s_ = s_.translate(pos)
                elif face == 0:
                    s_ = s_.rotate([0, 0, 90]).translate([w / 2 * 0.96, cx, z + sh / 2])
                else:
                    s_ = s_.rotate([0, 0, 90]).translate([-w / 2 * 0.96, cx, z + sh / 2])
                stones.append(s_)
                x += sw
        z += sh * 0.9
    stones = union(stones) ^ box([-w0, 0.01, 0.0], [w0, d0 + 3, h])
    cap = box([-w1 / 2 - 1.2, 0.0, h - 2.0], [w1 / 2 + 1.2, d1 + 1.2, h]) + M.hull_points(
        [(x, y, h - 2.8) for x in (-w1 / 2, w1 / 2) for y in (0.0, d1)] + [(x, y, h - 2.0) for x in (-w1 / 2 - 1.2, w1 / 2 + 1.2) for y in (0.0, d1 + 1.2)])
    flue = box([-w1 / 2 + 2.4, 2.2, h - 4.0], [w1 / 2 - 2.4, d1 - 2.2, h + 1.0])
    out = body + stones + cap - flue
    if boulders:
        for k, (bx_, by, br) in enumerate(((-w0 / 2 - 4.0, d0 * 0.4, 6.0), (w0 / 2 + 3.0, d0 * 0.7, 5.0), (-w0 / 4, d0 + 4.0, 5.5))):
            pts = []
            for _ in range(22):
                th = rng.uniform(0, 2 * math.pi)
                ph = rng.uniform(0.05, math.pi / 2)
                rr = br * rng.uniform(0.75, 1.05)
                pts.append((bx_ + rr * math.cos(th) * math.cos(ph) * 1.2, by + rr * math.sin(th) * math.cos(ph), rr * math.sin(ph) * 0.8))
            for th in np.linspace(0, 2 * math.pi, 8, endpoint=False):
                pts.append((bx_ + br * 1.15 * math.cos(th), by + br * math.sin(th), 0.0))
            out = out + M.hull_points(pts)
        out = out ^ box([-200, 0.0, -1], [200, 200, h + 2])
    return out


def bracket_rqrafter(h, d, t):
    """The lodge's eave: log rafter ends (side profile), each a log running out under the
    soffit, its end cut round, a short knee of branch under it back to the wall; solid."""
    hh = min(h, 2.4)
    r = min(1.0, hh / 2)
    beam = rect(0.0, -2 * r, d - r, 0.0)
    end = circle((d - r, -r), r, 18)
    knee = stroke([(0.45, -hh + 0.45), (d * 0.55, -2 * r + 0.3)], 0.9)
    return cs_union([beam, end, knee, rect(0.0, -hh, 0.9, 0.0)]) ^ rect(0.0, -hh - 1.0, d + 1.0, 0.01)


TW.BRACKET_EXTRA.update(rqrafter=bracket_rqrafter)


def barge_raquette(L, s, W=3.4, t=1.2, finial=6.0):
    """The front rake's bargeboard (in its plane: u across from the left eave end, v up from
    the roof's under side there, w out from its back): a board following both rakes, its
    lower edge bitten in a row of half rounds, a twig course of rails and crossed twigs on
    its face, a turned pendant dropping from the apex. Back on w = 0; printed on its back."""
    top = [(0.0, 0.6), (L / 2, s * L / 2 + 0.6), (L, 0.6)]
    band = poly([(0.0, -W), (L / 2, s * L / 2 - W * 1.15), (L, -W), (L, 0.6), (L / 2, s * L / 2 + 0.6), (0.0, 0.6)])
    bites = []
    ang = math.atan(s)
    Ls = math.hypot(L / 2, s * L / 2)
    for side in (-1, 1):
        for a in np.arange(2.4, Ls - 3.0, 2.6):
            x = a * math.cos(ang)
            u = x if side < 0 else L - x
            v = s * x - W
            bites.append(circle((u, v), 0.8, 14))
    cs = band - cs_union(bites)
    drop = cs_union([rect(L / 2 - 1.0, s * L / 2 - W - finial + 1.2, L / 2 + 1.0, s * L / 2), circle((L / 2, s * L / 2 - W - finial + 1.2), 1.2, 18),
                     poly([(L / 2 - 1.4, s * L / 2 - W - 0.6), (L / 2 + 1.4, s * L / 2 - W - 0.6), (L / 2, s * L / 2 - W - 2.4)])])
    cs = cs + drop
    # the twigs: two thin rails along each rake, crossed twigs between
    tw = []
    for side in (-1, 1):
        pts = []
        for a in np.arange(0.8, Ls - 1.6, 2.2):
            for b0, b1 in ((-W + 1.3, -0.5), (-0.5, -W + 1.3)):
                p0 = (a * math.cos(ang), a * math.sin(ang) + b0)
                p1 = ((a + 1.8) * math.cos(ang), (a + 1.8) * math.sin(ang) + b1)
                if side > 0:
                    p0, p1 = (L - p0[0], p0[1]), (L - p1[0], p1[1])
                tw.append(stroke([p0, p1], 0.4))
        for b in (-0.4, -W + 1.2):
            q0, q1 = (0.3, b), (L / 2, s * L / 2 + b)
            if side > 0:
                q0 = (L - 0.3, b)
            tw.append(stroke([q0, q1], 0.45))
    tw = _clean(cs_union(tw), 0.15) ^ cs.offset(-0.3, MIT, 4.0)
    out = ext(cs, 0.0, t)
    if not tw.is_empty():
        out = out + ext(tw, t - 0.01, t + 0.4)
    out = out + ext(circle((L / 2, s * L / 2 - W - finial + 1.2), 0.7, 14), t - 0.01, t + 0.5)
    return out

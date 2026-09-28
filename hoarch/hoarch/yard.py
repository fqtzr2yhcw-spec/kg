"""Parts unique to the engine terminal batch (buildings 71 on): coaling tower, tunnel portals and
the lineside buildings that follow. Like hoarch.town, every skin, cornice ornament, window and
door here belongs to one building only."""
import math

import numpy as np
from manifold3d import JoinType, Manifold as M

from .core import RIB, box, circle, cs_union, poly, rect, union
from .ornament import chamfer_box, ext, stroke
from . import cornice as CO, openings as O, trimwork as TW
from .colonial import _st
from .colonial4 import _glazed, _muntins

MJ = JoinType.Miter
RND = JoinType.Round


def _uvw(m, A):
    """Place a solid built in a facade's (u, v, w) frame with the 3x4 matrix ``A``."""
    return m.transform(A)


# ================================================================== 71 the Blackwater Coaling Tower
def bin_planks(region, datum=0.0, pitch=2.0, stud=14.0, u0=0.0, wales=(), post_top=None):
    """Coal-bin sheathing: heavy horizontal planks (a groove every ``pitch``) held by plumb bin
    posts outside them every ``stud`` from ``u0``, horizontal wales at ``wales`` (v) crossing
    the posts, and a tie-rod washer and nut on the wale at every post. ``post_top``: the posts
    and wales stop there (the gable above is planks only)."""
    if region.is_empty():
        return M()
    b = region.bounds()
    grooves = cs_union([rect(b[0] - 1, v - 0.14, b[2] + 1, v + 0.14)
                        for v in np.arange(datum + pitch * math.ceil((b[1] - datum) / pitch), b[3], pitch)])
    out = M.extrude(region, 0.3) - ext(grooves ^ region, 0.14, 1.0)
    top = b[3] if post_top is None else post_top
    lower = region ^ rect(b[0] - 1, b[1] - 1, b[2] + 1, top)
    if lower.is_empty():
        return out
    us = [u for u in np.arange(u0, b[2] + 0.9, stud) if u >= b[0] - 0.9]
    posts = cs_union([rect(u - 0.8, b[1] - 1, u + 0.8, top) for u in us]) ^ lower
    out = out + ext(posts, 0.25, 0.85)
    for v in wales:
        band = rect(b[0] - 1, v - 1.0, b[2] + 1, v + 1.0) ^ lower
        if band.is_empty():
            continue
        out = out + _st(band, 0.25, 0.75)
        for u in us:
            wsh = rect(u - 0.65, v - 0.65, u + 0.65, v + 0.65) ^ band
            if not wsh.is_empty():
                out = out + _st(wsh, 0.95, 0.25) + _st(circle((u, v), 0.35, 10) ^ band, 1.15, 0.2)
    return out


def battens_vertical(region, datum=0.0, board=2.4):
    """Board and batten: wide plumb boards with a narrow batten over every joint (the elevator
    shaft and the hoist house)."""
    if region.is_empty():
        return M()
    b = region.bounds()
    out = M.extrude(region, 0.3)
    bat = cs_union([rect(u - 0.35, b[1] - 1, u + 0.35, b[3] + 1) for u in np.arange(b[0] + board / 2, b[2], board)]) ^ region
    return out + ext(bat, 0.25, 0.7)


def foundation_formboard(reg, seed=0):
    """Board-formed concrete: the marks of the form boards in level courses, their butt joints
    staggered, a chamfered wash along the top (the hoist house)."""
    b = reg.bounds()
    out = M.extrude(reg, 0.45)
    rng = np.random.default_rng(seed)
    lines = []
    for k, v in enumerate(np.arange(b[1] + 1.4, b[3] - 0.8, 1.4)):
        lines.append(rect(b[0] - 1, v - 0.1, b[2] + 1, v + 0.1))
        u = b[0] + rng.uniform(2.0, 9.0)
        while u < b[2]:
            lines.append(rect(u - 0.1, v, u + 0.1, v + 1.4))
            u += rng.uniform(9.0, 16.0)
    out = out - ext(cs_union(lines) ^ reg, 0.3, 1.0)
    wash = rect(b[0] - 1, b[3] - 0.8, b[2] + 1, b[3] + 1) ^ reg
    return out + ext(wash, 0.44, 0.65)


def frieze_binstraps(L, h, b, pitch, margin, pair, half):
    """The bin's sill: two heavy planks bound at every station by an iron strap with two bolts
    (the Blackwater's base band)."""
    v0, v1 = 0.6, h - 0.6
    vm = (v0 + v1) / 2
    out = [_st(rect(0.3, v0, L - 0.3, vm - 0.12), b, 0.3), _st(rect(0.3, vm + 0.12, L - 0.3, v1), b, 0.3)]
    for u in CO._us(L, pitch, margin, 0.0):
        out.append(_st(rect(u - 0.65, v0 - 0.2, u + 0.65, v1 + 0.2), b + 0.3, 0.3))
        for v in (v0 + (v1 - v0) * 0.25, v0 + (v1 - v0) * 0.75):
            out.append(_st(circle((u, v), 0.36, 10), b + 0.6, 0.2))
    return out, []


def frieze_buckets(L, h, b, pitch, margin, pair, half):
    """The elevator's buckets on their chain: a chain along the head, a bucket hung from it
    every 3.4 mm, each flaring to its lip and rounded at the foot (the Blackwater's eave)."""
    v0, v1 = 0.6, h - 0.6
    out = [_st(rect(0.4, v1 - 0.55, L - 0.4, v1 - 0.1), b, 0.3)]
    hb = (v1 - 0.7) - (v0 + 0.2)
    for u in np.arange(1.9, L - 1.4, 3.4):
        top = v1 - 0.7
        bot = v0 + 0.2
        pts = [(u - 1.25, top), (u + 1.25, top), (u + 0.95, bot + 0.5), (u + 0.6, bot), (u - 0.6, bot), (u - 0.95, bot + 0.5)]
        body = poly(pts)
        out.append(_st(body, b, 0.45))
        out.append(_st(rect(u - 1.3, top - 0.35, u + 1.3, top), b + 0.45, 0.15))       # the lip
        if hb > 2.4:
            out.append(_st(rect(u - 0.12, top, u + 0.12, v1 - 0.1), b, 0.3))           # the hanger
    return out, []


def frieze_headwheels(L, h, b, pitch, margin, pair, half):
    """Head pulleys: a six-spoked wheel at every station on a belt of two lines (the
    Blackwater's head house cornice)."""
    v0, v1 = 0.6, h - 0.6
    vc = (v0 + v1) / 2
    r = min(2.2, (v1 - v0) / 2)
    out = [_st(rect(0.3, vc + r * 0.55 - 0.21, L - 0.3, vc + r * 0.55 + 0.21), b, 0.25),
           _st(rect(0.3, vc - r * 0.55 - 0.21, L - 0.3, vc - r * 0.55 + 0.21), b, 0.25)]
    for u in CO._us(L, pitch, margin, 0.0):
        ring = circle((u, vc), r, 28) - circle((u, vc), r - 0.45, 28)
        spokes = cs_union([stroke([(u, vc), (u + (r - 0.3) * math.cos(a), vc + (r - 0.3) * math.sin(a))], 0.44, caps=False)
                           for a in np.linspace(0, 2 * math.pi, 7)[:-1]])
        out.append(_st(cs_union([ring, spokes, circle((u, vc), 0.5, 12)]), b + 0.25, 0.3))
    return out, []


def frieze_pickshovel(L, h, b, pitch, margin, pair, half):
    """A pick and a coal shovel crossed at every station (the hoist house eave)."""
    v0, v1 = 0.6, h - 0.6
    vc = (v0 + v1) / 2
    hh = (v1 - v0) / 2
    out = []
    for u in CO._us(L, pitch, margin, 0.0):
        s = hh * 0.95
        shaft1 = stroke([(u - s, vc - s), (u + s * 0.7, vc + s * 0.7)], 0.42, caps=False)
        head = stroke([(u + s * 0.7 - 1.1, vc + s * 0.7 + 0.5), (u + s * 0.7, vc + s * 0.7 + 0.15), (u + s * 0.7 + 1.1, vc + s * 0.7 - 0.9)], 0.42)
        shaft2 = stroke([(u + s, vc - s * 0.3), (u - s * 0.45, vc + s * 0.9)], 0.42, caps=False)
        blade = poly([(u + s - 0.1, vc - s * 0.3 + 0.2), (u + s + 0.9, vc - s * 0.3 - 0.5), (u + s + 0.3, vc - s - 0.3), (u + s - 0.6, vc - s * 0.3 - 0.4)])
        out.append(_st(cs_union([shaft1, head, shaft2, blade]) ^ rect(0.0, v0, L, v1), b, 0.4))
    return out, []


def course_chainlinks(L, h, b, pitch, margin, p):
    """A chain: oval links flat to the face, each with a sunk eye, alternating with links
    seen edge-on."""
    vc = h / 2
    out = []
    ry = min(0.5, h * 0.32)
    for k, u in enumerate(np.arange(1.0, L - 1.0, 1.45)):
        if k % 2 == 0:
            link = cs_union([circle((u - 0.2, vc), ry, 12), circle((u + 0.2, vc), ry, 12), rect(u - 0.2, vc - ry, u + 0.2, vc + ry)])
            out.append(ext(link, b - 0.05, b + 0.35) - ext(rect(u - 0.3, vc - 0.1, u + 0.3, vc + 0.1), b + 0.2, b + 1.0))
        else:
            out.append(ext(rect(u - 0.6, vc - 0.22, u + 0.6, vc + 0.22), b - 0.05, b + 0.45))
    return out


def course_sprockets(L, h, b, pitch, margin, p):
    """Sprocket wheels every 4 mm on a roller chain (the head house cornice)."""
    vc = h / 2
    r = min(0.62, h * 0.4)
    chain = rect(0.3, vc - 0.2, L - 0.3, vc + 0.2)
    wheels = []
    for u in np.arange(2.0, L - 1.2, 4.0):
        teeth = cs_union([rect(u - 0.2, vc - r - 0.14, u + 0.2, vc + r + 0.14).transform(
            np.array([[math.cos(a), -math.sin(a), u - u * math.cos(a) + vc * math.sin(a)],
                      [math.sin(a), math.cos(a), vc - u * math.sin(a) - vc * math.cos(a)]])) for a in np.linspace(0, math.pi, 5)[:-1]])
        wheels.append(cs_union([circle((u, vc), r, 16), teeth]))
    return [ext(chain, b - 0.05, b + 0.25), ext(cs_union(wheels), b - 0.05, b + 0.45)]


def bracket_binstrut(h, d, t):
    """A bin strut: a plumb timber against the wall and a raking strut to the soffit's outer
    edge, the triangle between them filled solid, a bolted foot (side profile, top at v = 0)."""
    hb = max(3.0, h)
    return poly([(0.0, 0.0), (d, 0.0), (d, -0.7), (1.3, -hb + 1.0), (1.3, -hb + 0.3), (1.0, -hb), (0.0, -hb)])


CO.FRIEZE_EXTRA.update(binstraps=frieze_binstraps, buckets=frieze_buckets, headwheels=frieze_headwheels,
                       pickshovel=frieze_pickshovel)
CO.COURSE_EXTRA.update(chainlinks=course_chainlinks, sprockets=course_sprockets)
TW.BRACKET_EXTRA.update(binstrut=bracket_binstrut)
TW.FOUNDATION_EXTRA.update(formboard=foundation_formboard)


# ------------------------------------------------------------------ windows and doors
def window_bin(w=8.0, h=12.0):
    """The bin house's window: a fixed sash of six lights in a plank casing under a peaked drip
    board, the sill on a pair of little brackets."""
    op = O.opening_cs(w, h, 0)
    plug_cs = op.offset(-O.CLR, MJ, 4.0)
    pl = O.PLUG
    g = plug_cs.offset(-0.5, MJ, 4.0)
    sash = _glazed([ext(plug_cs, -pl, -0.6)], g, pl, _muntins(g, 2, 3, 0.42), plug_cs)
    hw = w / 2 + 1.3
    peak = poly([(-hw - 0.7, h + 1.25), (hw + 0.7, h + 1.25), (hw + 0.7, h + 1.9), (0.0, h + 3.1), (-hw - 0.7, h + 1.9)])
    parts = [ext(op - op.offset(-RIB, MJ, 4.0), 0.0, 0.7), ext(op.offset(1.3, MJ, 4.0) - op, 0.0, 0.6),
             ext(peak, 0.0, 1.1), ext(peak - peak.offset(-0.4, MJ, 4.0), 1.09, 1.4),
             chamfer_box(-hw - 0.5, -1.2, hw + 0.5, 0.2, 0.0, 1.2, c=0.35, bottom=0.8)]
    for s in (-1, 1):
        parts.append(ext(poly([(s * (hw - 1.6), -1.19), (s * (hw - 0.4), -1.19), (s * (hw - 1.0), -2.6)]), 0.0, 0.9))
    return O._one_piece(sash, parts, op, plug_cs, pl, h + 3.1, -2.6)


def window_slit(w=5.0, h=9.0):
    """The elevator shaft's light: two panes one over the other in a plain casing, a heavy
    lintel block over and a plain sill."""
    op = O.opening_cs(w, h, 0)
    plug_cs = op.offset(-O.CLR, MJ, 4.0)
    pl = O.PLUG
    g = plug_cs.offset(-0.5, MJ, 4.0)
    sash = _glazed([ext(plug_cs, -pl, -0.6)], g, pl, _muntins(g, 1, 2, 0.45), plug_cs)
    parts = [ext(op - op.offset(-RIB, MJ, 4.0), 0.0, 0.7), ext(op.offset(1.0, MJ, 4.0) - op, 0.0, 0.55),
             chamfer_box(-w / 2 - 1.8, h + 0.99, w / 2 + 1.8, h + 2.8, 0.0, 1.2, c=0.35, bottom=1.0),
             chamfer_box(-w / 2 - 1.2, -1.1, w / 2 + 1.2, 0.2, 0.0, 1.0, c=0.3, bottom=0.8)]
    return O._one_piece(sash, parts, op, plug_cs, pl, h + 2.8, -1.1)


def window_headhouse(w=7.0, h=10.0, rise=1.8):
    """The head house's window: four lights under a segmental head, the casing following the
    arch to a keystone, a sill with a drip."""
    op = O.opening_cs(w, h, rise)
    plug_cs = op.offset(-O.CLR, MJ, 4.0)
    pl = O.PLUG
    g = plug_cs.offset(-0.5, MJ, 4.0)
    sash = _glazed([ext(plug_cs, -pl, -0.6)], g, pl, _muntins(g, 2, 2, 0.42), plug_cs)
    casing = (op.offset(1.2, RND) - op) ^ rect(-w, 0.0, w, h + 3.0)
    parts = [ext(op - op.offset(-RIB, MJ, 4.0), 0.0, 0.7), ext(casing, 0.0, 0.6),
             ext(poly([(-0.9, h - 0.3), (0.9, h - 0.3), (1.2, h + 1.5), (-1.2, h + 1.5)]), 0.0, 1.0),
             chamfer_box(-w / 2 - 1.5, -1.2, w / 2 + 1.5, 0.2, 0.0, 1.1, c=0.35, bottom=0.8)]
    return O._one_piece(sash, parts, op, plug_cs, pl, h + 1.5, -1.2)


def window_hoist(w=7.0, h=8.0):
    """The hoist house's window: four lights under a little shed hood on two knee braces."""
    op = O.opening_cs(w, h, 0)
    plug_cs = op.offset(-O.CLR, MJ, 4.0)
    pl = O.PLUG
    g = plug_cs.offset(-0.5, MJ, 4.0)
    sash = _glazed([ext(plug_cs, -pl, -0.6)], g, pl, _muntins(g, 2, 2, 0.42), plug_cs)
    hw = w / 2 + 1.1
    parts = [ext(op - op.offset(-RIB, MJ, 4.0), 0.0, 0.7), ext(op.offset(1.1, MJ, 4.0) - op, 0.0, 0.55),
             ext(poly([(-hw - 1.0, h + 1.1), (hw + 1.0, h + 1.1), (hw + 1.0, h + 1.9), (-hw - 1.0, h + 1.9)]), 0.0, 1.8),
             chamfer_box(-hw, -1.1, hw, 0.2, 0.0, 1.0, c=0.3, bottom=0.8)]
    for s in (-1, 1):
        parts.append(ext(poly([(s * (hw - 0.2), h + 1.11), (s * (hw + 0.6), h + 1.11), (s * (hw - 0.2), h - 0.6)]), 0.0, 1.2))
    return O._one_piece(sash, parts, op, plug_cs, pl, h + 1.9, -1.1)


def _strap_hinge(u0, u1, v):
    s = 1.0 if u1 > u0 else -1.0
    return cs_union([poly([(u0, v - 0.32), (u1 - s * 0.9, v - 0.2), (u1, v), (u1 - s * 0.9, v + 0.2), (u0, v + 0.32)]),
                     circle((u0 + s * 0.5, v), 0.42, 12)])


def door_bin(w=9.0, h=20.0):
    """The walkway door into the bin house: a boarded leaf on a Z brace, iron strap hinges, a
    two-light window high up, in a plank casing under a drip board."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, MJ, 4.0)
    pl = O.PLUG
    leaf = plug_cs.offset(-0.3, MJ, 4.0)
    lb = leaf.bounds()
    gl = rect(lb[0] + 1.2, h * 0.68, lb[2] - 1.2, lb[3] - 1.3)
    grooves = cs_union([rect(u - 0.14, -1, u + 0.14, h + 1) for u in np.arange(lb[0] + 1.3, lb[2], 1.3)]) ^ leaf
    body = [ext(plug_cs, -pl, -1.0), ext(plug_cs - plug_cs.offset(-0.5, MJ, 4.0), -pl, 0.0),
            ext(leaf, -1.0, -0.6) - ext(grooves, -0.8, -0.5)]
    q0, q1 = lb[1] + 1.2, h * 0.68 - 1.4
    body.append(ext(cs_union([rect(lb[0] + 0.4, q0, lb[2] - 0.4, q0 + 1.0), rect(lb[0] + 0.4, q1 - 1.0, lb[2] - 0.4, q1),
                              stroke([(lb[0] + 0.9, q0 + 0.8), (lb[2] - 0.9, q1 - 0.8)], 0.95, caps=False)]), -0.61, -0.25))
    body.append(ext(cs_union([_strap_hinge(lb[0] + 0.3, lb[0] + 5.2, q0 + 0.5), _strap_hinge(lb[0] + 0.3, lb[0] + 5.2, q1 - 0.5)]),
                    -0.26, -0.05))
    gb = gl.bounds()
    bars = rect((gb[0] + gb[2]) / 2 - 0.22, gb[1] - 1, (gb[0] + gb[2]) / 2 + 0.22, gb[3] + 1)
    sash = _glazed(body, gl, pl, bars, plug_cs)
    parts = [ext(op - op.offset(-RIB, MJ, 4.0), 0.0, 0.7), ext((op.offset(1.3, MJ, 4.0) - op) ^ rect(-w, 0.0, w, h + 1.3), 0.0, 0.6),
             chamfer_box(-w / 2 - 2.0, h + 1.29, w / 2 + 2.0, h + 2.2, 0.0, 1.3, c=0.3, bottom=1.0)]
    return O._one_piece(sash, parts, op, plug_cs, pl, h + 2.2, 0.0)


def door_hoist(w=12.0, h=18.0):
    """The hoist house's doors: a pair of boarded leaves, each braced with an X between ledges,
    strap hinges, under a plank head with a drip."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, MJ, 4.0)
    pl = O.PLUG
    lb = plug_cs.offset(-0.3, MJ, 4.0).bounds()
    body = [ext(plug_cs, -pl, -1.0), ext(plug_cs - plug_cs.offset(-0.5, MJ, 4.0), -pl, 0.0)]
    for (a, e) in ((lb[0], -0.15), (0.15, lb[2])):
        leaf = rect(a, lb[1], e, lb[3])
        grooves = cs_union([rect(u - 0.13, -1, u + 0.13, h + 1) for u in np.arange(a + 1.2, e, 1.2)]) ^ leaf
        body.append(ext(leaf, -1.0, -0.6) - ext(grooves, -0.8, -0.5))
        q0, q1 = lb[1] + 1.0, lb[3] - 1.0
        body.append(ext(cs_union([rect(a + 0.3, q0, e - 0.3, q0 + 0.9), rect(a + 0.3, q1 - 0.9, e - 0.3, q1),
                                  rect(a + 0.3, (q0 + q1) / 2 - 0.45, e - 0.3, (q0 + q1) / 2 + 0.45),
                                  stroke([(a + 0.7, q0 + 0.8), (e - 0.7, (q0 + q1) / 2 - 0.3)], 0.8, caps=False),
                                  stroke([(e - 0.7, q0 + 0.8), (a + 0.7, (q0 + q1) / 2 - 0.3)], 0.8, caps=False),
                                  stroke([(a + 0.7, (q0 + q1) / 2 + 0.3), (e - 0.7, q1 - 0.8)], 0.8, caps=False),
                                  stroke([(e - 0.7, (q0 + q1) / 2 + 0.3), (a + 0.7, q1 - 0.8)], 0.8, caps=False)]) ^ leaf, -0.61, -0.25))
        hinge_u = a + 0.3 if a < 0 else e - 0.3
        tip = hinge_u + (4.0 if a < 0 else -4.0)
        body.append(ext(cs_union([_strap_hinge(hinge_u, tip, q0 + 0.45), _strap_hinge(hinge_u, tip, q1 - 0.45)]), -0.26, -0.05))
    parts = [ext(op - op.offset(-RIB, MJ, 4.0), 0.0, 0.7), ext((op.offset(1.3, MJ, 4.0) - op) ^ rect(-w, 0.0, w, h + 1.3), 0.0, 0.6),
             chamfer_box(-w / 2 - 2.2, h + 1.29, w / 2 + 2.2, h + 2.8, 0.0, 1.4, c=0.35, bottom=1.1)]
    return O._one_piece(body, parts, op, plug_cs, pl, h + 2.8, 0.0)


# ------------------------------------------------------------------ the timber work
def trestle_coal(xs, ys, h, deck, walk_y, post=4.0, deck_t=2.0, joist=1.8, peg=1.6, notch=None):
    """The bin's timber substructure, one piece printed upside down on its deck: a grid of posts
    (``xs`` by ``ys``) on square pegs, girts at the foot and mid-height all round and through
    the grid, X braces in every outer bay, joists along y under a planked deck (``deck`` =
    x0, y0, x1, y1) that runs out to a walkway at the front (y0 = ``walk_y``), the walkway's
    joists carried on knee braces from the front posts, a fascia along its edge. ``notch``: a
    solid the deck stays clear of (the elevator shaft). Local: z = 0 at the posts' feet, the
    deck's top at h."""
    x0, y0, x1, y1 = deck
    zt = h - deck_t - joist                        # the posts' tops
    zm = zt * 0.5
    out = []
    for x in xs:
        for y in ys:
            out.append(box([x - post / 2, y - post / 2, 0.0], [x + post / 2, y + post / 2, zt + 0.01]))
            out.append(box([x - peg / 2, y - peg / 2, -1.6], [x + peg / 2, y + peg / 2, 0.01]))
    gw = 1.4
    for z in (1.8, zm, zt - 0.8):
        for y in ys:
            out.append(box([xs[0] - post / 2, y - gw / 2, z - 0.8], [xs[-1] + post / 2, y + gw / 2, z + 0.8]))
        for x in xs:
            out.append(box([x - gw / 2, ys[0] - post / 2, z - 0.8], [x + gw / 2, ys[-1] + post / 2, z + 0.8]))
    bw = 1.2

    def brace(p, q, n):
        """A flat brace between plan points p and q (z0 -> z1), 1.2 thick along ``n``."""
        (ax, ay, az), (bx, by, bz) = p, q
        pts = []
        for (x, y, z) in ((ax, ay, az), (bx, by, bz)):
            for s in (-bw / 2, bw / 2):
                pts.append((x + n[0] * s, y + n[1] * s, z))
                pts.append((x + n[0] * s, y + n[1] * s, z + (1.6 if z < (az + bz) / 2 else -1.6)))
        return M.hull_points(pts)

    for (za, zb) in ((1.8, zm), (zm, zt - 0.8)):
        for a, e in zip(xs[:-1], xs[1:]):
            for y, sg in ((ys[0], -1), (ys[-1], 1)):
                yy = y + sg * (post / 2 + bw / 2 - 0.3)
                out.append(brace((a + post / 2, yy, za), (e - post / 2, yy, zb), (0, 1)))
                out.append(brace((e - post / 2, yy, za), (a + post / 2, yy, zb), (0, 1)))
        for a, e in zip(ys[:-1], ys[1:]):
            for x, sg in ((xs[0], -1), (xs[-1], 1)):
                xx = x + sg * (post / 2 + bw / 2 - 0.3)
                out.append(brace((xx, a + post / 2, za), (xx, e - post / 2, zb), (1, 0)))
                out.append(brace((xx, e - post / 2, za), (xx, a + post / 2, zb), (1, 0)))
    # joists along y at every post line, out to the walkway's edge, on knee braces at the front
    zj = h - deck_t
    for x in xs:
        out.append(box([x - 0.9, y0, zj - joist], [x + 0.9, y1, zj + 0.01]))
        kb = 12.0
        out.append(M.hull_points([(x + s, ys[0] - post / 2 + 0.01, zj - joist - kb + dz) for s in (-0.8, 0.8) for dz in (0.0, 1.7)] +
                                 [(x + s, y0 + 1.2, zj - joist + dz) for s in (-0.8, 0.8) for dz in (0.0, 0.01)] +
                                 [(x + s, y0 + 2.9, zj - joist + 0.01) for s in (-0.8, 0.8)]))
    dk = box([x0, y0, zj], [x1, y1, h])
    if notch is not None:
        dk = dk - notch
    planks = union([box([x0 - 1, y - 0.22, h - 0.4], [x1 + 1, y + 0.22, h + 1]) for y in np.arange(y0 + 2.0, y1, 2.0)])
    fascia = box([x0, y0 - 0.9, zj - 1.6], [x1, y0 + 0.01, h])
    return union(out) + (dk - planks) + fascia


def footings_coal(xs, ys, pad, post=4.0, peg=1.6, shaft=None, zt=4.0, pad_t=1.8):
    """A concrete pad with a battered footing under every post, each socketed for its peg; a
    raised block for the elevator shaft's foot (``shaft`` = x0, y0, x1, y1) with a locating lip.
    Local: z = 0 at the ground, the footings' tops at ``zt``."""
    x0, y0, x1, y1 = pad
    out = [box([x0, y0, 0.0], [x1, y1, pad_t])]
    socks = []
    for x in xs:
        for y in ys:
            out.append(M.hull_points([(x + a * (post / 2 + 1.5), y + c * (post / 2 + 1.5), pad_t - 0.01) for a in (-1, 1) for c in (-1, 1)] +
                                     [(x + a * (post / 2 + 0.5), y + c * (post / 2 + 0.5), zt) for a in (-1, 1) for c in (-1, 1)]))
            socks.append(box([x - peg / 2 - 0.12, y - peg / 2 - 0.12, zt - 1.8], [x + peg / 2 + 0.12, y + peg / 2 + 0.12, zt + 0.1]))
    if shaft is not None:
        sx0, sy0, sx1, sy1 = shaft
        out.append(M.hull_points([(x, y, pad_t - 0.01) for x in (sx0 - 1.4, sx1 + 1.4) for y in (sy0 - 1.4, sy1 + 1.4)] +
                                 [(x, y, zt) for x in (sx0 - 0.6, sx1 + 0.6) for y in (sy0 - 0.6, sy1 + 0.6)]))
    return union(out) - union(socks)


def chute_apron(L=38.0, ang=25.0, wid=9.0, dep=3.2, t=0.9, gw=10.0, gh=12.0, gd=3.5):
    """A coal chute, one piece: the gate box that glues to the bin wall over its discharge (a
    framed plate with rivets), the apron (a steel trough) hinged below it and angled down
    ``ang`` degrees, a turned-up lip at its tip, hinge knuckles, and a pair of hanger bars from
    the gate's head to the apron near its tip. Local: u along the wall (centred), v up (the
    gate's foot at 0), w out from the wall face. Prints on its back (the gate on the bed)."""
    a = math.radians(ang)
    gate = box([-gw / 2, 0.0, 0.0], [gw / 2, gh, gd])
    gate = gate + box([-gw / 2 + 0.8, 0.8, gd - 0.01], [gw / 2 - 0.8, gh - 0.8, gd + 0.35])
    rivets = []
    for u in np.linspace(-gw / 2 + 0.45, gw / 2 - 0.45, 7):
        for v in (0.4, gh - 0.4):
            rivets.append(box([u - 0.2, v - 0.2, gd - 0.01], [u + 0.2, v + 0.2, gd + 0.3]))
    # the trough in (x across, s along, n up from its floor), mapped to (u, v, w)
    v_0, w_0 = 1.2, 1.2
    T = np.array([[1.0, 0.0, 0.0, 0.0],
                  [0.0, -math.sin(a), math.cos(a), v_0],
                  [0.0, math.cos(a), math.sin(a), w_0]])
    tr = box([-wid / 2, 0.0, 0.0], [wid / 2, L, dep]) - box([-wid / 2 + t, -1.0, t], [wid / 2 - t, L - 0.9, dep + 1.0])
    lip = box([-wid / 2, L - 0.9, 0.0], [wid / 2, L, dep + 0.8])
    flare = union([box([s * wid / 2 - (0.5 if s > 0 else 0.0), L * 0.55, dep - 0.01], [s * wid / 2 + (0.0 if s > 0 else 0.5), L, dep + 0.6])
                   for s in (-1, 1)])
    ribs = union([box([-wid / 2 - 0.25, s0 - 0.35, 0.0], [wid / 2 + 0.25, s0 + 0.35, dep]) - box([-wid / 2 + t, s0 - 1, t], [wid / 2 - t, s0 + 1, dep + 1])
                  for s0 in np.arange(L * 0.3, L - 2.0, L * 0.25)])
    trough = (tr + lip + flare + ribs).transform(T)
    knuck = union([box([s * (wid / 2 + 0.1) - 0.8, v_0 - 1.2, w_0 - 0.2], [s * (wid / 2 + 0.1) + 0.8, v_0 + 1.4, w_0 + 2.2]) for s in (-1, 1)])
    # the hangers: from the gate's head to the trough's rim 3 mm short of the tip
    tip = T @ np.array([0.0, L - 3.0, dep, 1.0])
    hangers = []
    for s in (-1, 1):
        u0_, u1_ = sorted((s * (wid / 2 - 0.9), s * (wid / 2 + 0.1)))
        pts = [(u, gh - 0.6 + dv, dw) for u in (u0_, u1_) for (dv, dw) in ((0.0, 0.4), (0.6, 0.4), (0.0, 1.6), (0.6, 1.6))]
        pts += [(u, tip[1] + dv, tip[2] + dw) for u in (u0_, u1_) for (dv, dw) in ((-0.2, -0.6), (0.6, -0.6), (-0.2, 0.6), (0.6, 0.6))]
        hangers.append(M.hull_points(pts))
    return gate + union(rivets) + trough + knuck + union(hangers)


def rail_walkway(L, h=11.0, ret=0.0, pitch=11.0, post=1.3):
    """The walkway railing, one piece printed upright on its toe board: square posts, a top rail
    and a mid rail, the toe board; ``ret`` > 0 adds a return of that length at the +u end
    (turning toward +w). Local: u along the run, v up from the deck, w out from the wall...
    returned in (x = u, y = w, z = v)."""
    def run(n_len):
        parts = [box([0.0, 0.0, 0.0], [n_len, 1.0, 1.6]),                       # toe board
                 box([0.0, 0.0, h - 1.2], [n_len, 1.2, h]),                     # top rail
                 box([0.0, 0.1, h * 0.52 - 0.5], [n_len, 1.0, h * 0.52 + 0.5])]
        n = max(1, int(round(n_len / pitch)))
        for k in range(n + 1):
            x = min(n_len - post, max(0.0, k * n_len / n - post / 2))
            parts.append(box([x, 0.0, 0.0], [x + post, 1.2, h]))
        return union(parts)
    out = run(L)
    if ret > 0:
        r = run(ret).transform(np.array([[0.0, -1.0, 0.0, L], [1.0, 0.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0]]))
        out = out + r
    return out


def ladder_coal(H, w=5.6, above=9.0, tab=4.0):
    """A timber ladder: two rails with a rung every 3.5 mm, running ``above`` mm over the deck
    as handholds joined by a top bar, and a tab under the handholds that lies on the deck.
    Local: x across, y up (the feet at 0, the deck at H), z out from the wall (the rails' backs
    at z = 0, the tab running toward -z). Prints lying on its back."""
    out = []
    for x in (0.0, w - 1.2):
        out.append(box([x, 0.0, 0.0], [x + 1.2, H + above, 1.2]))
    for y in np.arange(3.0, H + above - 1.5, 3.5):
        out.append(box([0.6, y - 0.45, 0.2], [w - 0.6, y + 0.45, 1.2]))
    out.append(box([0.0, H + above - 1.2, 0.0], [w, H + above, 1.2]))
    out.append(box([0.0, H, -tab], [w, H + 1.0, 0.01]))
    out.append(box([0.6, H, 0.0], [w - 0.6, H + 1.0, 1.2]))
    return union(out)


def stack_hoist(h=40.0, r=1.7):
    """The hoist engine's smokestack: an iron pipe with a band at every section joint and a
    flared cap, a peg that drops into the roof. Local: centred, z = 0 at the roof seat."""
    out = [M.cylinder(h, r, r * 0.92, 28), M.cylinder(3.0, r - 0.55, r - 0.55, 20).translate([0, 0, -3.0])]
    for z in np.arange(8.0, h - 4.0, 9.0):
        out.append(M.cylinder(0.8, r + 0.3, r + 0.25, 28).translate([0, 0, z]))
    out.append(M.cylinder(1.6, r * 0.92, r + 1.1, 28).translate([0, 0, h - 0.6]))
    out.append(M.cylinder(0.6, r + 1.1, r + 1.1, 28).translate([0, 0, h + 0.99]))
    return union(out) - M.cylinder(h + 10, r - 0.7, r - 0.7, 20).translate([0, 0, 4.0])


def sign_bin(text, L, H=7.0, t=1.0, cap=4.0):
    """The coaling tower's name board: a long board with a bead round it and raised letters, a
    bolt at each end (facade frame, centred on u = 0, foot at v = 0). Returns (board, letters)."""
    from .storefront import text_cs
    b = rect(-L / 2, 0.0, L / 2, H)
    board = ext(b, 0.0, t) + ext(b - b.offset(-0.6, MJ, 4.0), t - 0.01, t + 0.4)
    bolts = union([ext(circle((s * (L / 2 - 1.3), H / 2), 0.5, 12), t - 0.01, t + 0.5) for s in (-1, 1)])
    letters = text_cs(text, cap=cap, font="serif", track=0.5)
    lb = letters.bounds()
    sc = min(1.0, (L - 6.0) / max(1e-6, lb[2] - lb[0]))
    letters = letters.scale((sc, 1.0)).translate(((-(lb[0] + lb[2]) / 2) * sc, (H - cap) / 2 - lb[1]))
    lt = ext(letters, t - 0.01, t + 0.45)
    return board + bolts + lt, lt


# ================================================================== 72 the Stonehaven Tunnel Portals
def _rock(cs, w0, d, face, rng, inset=0.45, n=4):
    """One rock-faced stone on outline ``cs`` (convex): a flat drafted margin ``inset`` wide at
    w0 + d round a pitched face of a few random facets standing up to ``face`` more."""
    b = cs.bounds()
    body = ext(cs, -0.01, w0 + d)
    inner = cs.offset(-inset, MJ, 4.0)
    if inner.is_empty():
        return body
    ib = inner.bounds()
    pts = [(p[0], p[1], w0 + d - 0.01) for loop in inner.to_polygons() for p in loop]
    for _ in range(n):
        pts.append((rng.uniform(ib[0] + 0.2 * (ib[2] - ib[0]), ib[2] - 0.2 * (ib[2] - ib[0])),
                    rng.uniform(ib[1] + 0.2 * (ib[3] - ib[1]), ib[3] - 0.2 * (ib[3] - ib[1])),
                    w0 + d + face * rng.uniform(0.45, 1.0)))
    return body + M.hull_points(pts)


def _dressed(cs, w0, d, c=0.5):
    """A smooth-dressed stone on outline ``cs`` (convex): raised ``d`` from w0, its edges
    chamfered ``c`` at 45 degrees (a face-up print feature)."""
    inner = cs.offset(-c, MJ, 4.0)
    lo = ext(cs, -0.01, w0 + d - c)
    if inner.is_empty():
        return lo
    return M.hull_points([(p[0], p[1], z) for loop in cs.to_polygons() for p in loop for z in (-0.01, w0 + d - c)] +
                         [(p[0], p[1], w0 + d) for loop in inner.to_polygons() for p in loop])


def rock_ashlar(region, seed=0, course=5.4, lmin=7.0, lmax=14.0, joint=0.5, w0=0.0, d=0.6, face=0.6, datum=0.0, u0=None):
    """Rock-faced ashlar filling ``region`` (u, v): level courses ``course`` high of stones of
    random length in broken joint, each with a drafted margin and a pitched face (the Stonehaven
    portals). Stones cut by the region's edge keep their face; the joints show the plate."""
    if region.is_empty():
        return M()
    b = region.bounds()
    rng = np.random.default_rng(seed)
    stones = []
    v = datum + course * math.floor((b[1] - datum) / course)
    start = b[0] if u0 is None else u0
    while v < b[3] - 0.3:
        u = start - rng.uniform(0.0, lmax)
        while u < b[2]:
            L = rng.uniform(lmin, lmax)
            r = rect(u + joint / 2, v + joint / 2, u + L - joint / 2, v + course - joint / 2)
            if not (r ^ region).is_empty():
                stones.append(_rock(r, w0, d, face, rng))
            u += L
        v += course
    return union(stones) ^ ext(region, -1.0, 20.0)


def portal_stone(W=140.0, H=100.0, ow=60.0, spring=52.0, T=4.0, date="1893", seed=0):
    """A single-track tunnel portal in cut stone, one piece printed face up: rock-faced ashlar
    between rock-faced pilasters on a plinth of big stones; the arch ringed with fifteen
    smooth-dressed voussoirs and a tall keystone, on moulded imposts over long-and-short jamb
    quoins; a cornice of bed mould, dentils, corona and coping; over the arch a raised parapet
    with the date on a beaded tablet. Local: u across (centred), v up from the foot, w out of
    the face (the back at w = -T). Returns (portal, opening outline, letters)."""
    from .storefront import text_cs
    r0 = ow / 2
    opening = O.opening_cs(ow, spring + r0, r0)
    hw = W / 2
    par = poly([(-30.0, H - 0.1), (30.0, H - 0.1), (30.0, H + 8.0), (26.0, H + 12.0), (-26.0, H + 12.0), (-30.0, H + 8.0)])
    outline = cs_union([rect(-hw, 0.0, hw, H), rect(-hw - 2.0, H - 12.0, hw + 2.0, H), par])
    plate = ext(outline - opening, -T, 0.0)
    rng = np.random.default_rng(seed)
    parts = [plate]
    # the arch ring: fifteen voussoirs, the keystone taller and prouder
    ring_r = r0 + 8.0
    n = 15
    for k in range(n):
        a0, a1 = math.pi * k / n, math.pi * (k + 1) / n
        g = 0.2 / ring_r
        key = k == n // 2
        rr = ring_r + (4.5 if key else 0.0)
        ph = 0.12 if key else 0.0
        pts = [(r * math.cos(a), spring + r * math.sin(a)) for (r, a) in
               ((r0 + 0.3, a0 + g - ph), (rr, a0 + g - ph * 1.6), (rr, a1 - g + ph * 1.6), (r0 + 0.3, a1 - g + ph))]
        vs = poly(pts)
        parts.append(_dressed(vs, 0.0, 3.0 if key else 2.0, 0.5))
        if key:
            kb = vs.offset(-1.1, MJ, 4.0)
            parts.append(_dressed(kb, 3.0, 0.4, 0.2))
    arch_zone = cs_union([circle((0.0, spring), ring_r + 0.3, 72) ^ rect(-hw, spring, hw, H), rect(-4.5, spring, 4.5, spring + ring_r + 5.0)])
    # imposts and jamb quoins
    imp = []
    for s in (-1, 1):
        a, e = sorted((s * (r0 + 0.2), s * (r0 + 9.5)))
        imp.append(rect(a, spring - 3.4, e, spring))
        parts.append(_dressed(rect(a, spring - 3.4, e, spring), 0.0, 2.4, 0.6))
        parts.append(_dressed(rect(a, spring - 3.4, e, spring - 2.2), 2.39, 0.4, 0.2))
    quo = []
    for j, v in enumerate(np.arange(7.0, spring - 3.4 - 0.5, 6.0)):
        top = min(v + 6.0, spring - 3.4)
        for s in (-1, 1):
            L = 8.0 if (j % 2 == 0) else 5.0
            a, e = sorted((s * (r0 + 0.2), s * (r0 + L)))
            q = rect(a + 0.2, v + 0.2, e - 0.2, top - 0.2)
            quo.append(rect(a, v, e, top))
            parts.append(_dressed(q, 0.0, 1.6, 0.4))
    # the plinth and the pilasters
    plinth = rect(-hw, 0.0, hw, 7.0) - opening
    parts.append(rock_ashlar(plinth, seed=seed + 1, course=7.0, lmin=14.0, lmax=22.0, d=1.2, face=0.7))
    pil = []
    for s in (-1, 1):
        a, e = sorted((s * hw, s * (hw - 13.0)))
        p_ = rect(a, 7.0, e, H - 12.0)
        pil.append(p_)
        parts.append(ext(p_, -0.01, 0.8))
        parts.append(rock_ashlar(p_, seed=seed + 2 + (s > 0), course=6.2, lmin=13.4, lmax=13.4, w0=0.8, d=0.8, face=0.7, u0=a))
    # the cornice
    parts.append(_dressed(rect(-hw - 1.0, H - 12.0, hw + 1.0, H - 10.0), 0.0, 1.8, 0.5))
    for u in np.arange(-hw + 0.4, hw - 0.4, 2.8):
        parts.append(_dressed(rect(u - 0.7, H - 10.0, u + 0.7, H - 8.0), 0.0, 2.4, 0.3))
    parts.append(_dressed(rect(-hw - 2.0, H - 8.0, hw + 2.0, H - 3.0), 0.0, 3.0, 0.7))
    parts.append(_dressed(rect(-hw - 2.0, H - 3.0, hw + 2.0, H), 0.0, 2.6, 1.2))
    # the parapet: coping round its top, the dated tablet
    cop = cs_union([poly([(-30.0, H + 5.0), (-30.0, H + 8.0), (-26.0, H + 12.0), (-22.6, H + 12.0), (-22.6, H + 9.4), (-24.8, H + 9.4), (-27.4, H + 6.9), (-27.4, H + 5.0)]),
                    rect(-22.8, H + 9.4, 22.8, H + 12.0),
                    poly([(30.0, H + 5.0), (30.0, H + 8.0), (26.0, H + 12.0), (22.6, H + 12.0), (22.6, H + 9.4), (24.8, H + 9.4), (27.4, H + 6.9), (27.4, H + 5.0)])])
    parts.append(ext(cop, -0.01, 1.8))
    tab = rect(-14.0, H + 1.2, 14.0, H + 8.6)
    parts.append(_dressed(tab, 0.0, 1.0, 0.3))
    parts.append(ext(tab - tab.offset(-0.6, MJ, 4.0), 0.99, 1.5))
    letters = text_cs(date, cap=4.2, font="serif", track=0.6)
    lb = letters.bounds()
    letters = letters.translate((-(lb[0] + lb[2]) / 2, H + 4.9 - (lb[1] + lb[3]) / 2))
    lt = ext(letters, 0.99, 1.55)
    parts.append(lt)
    # the field: rock-faced ashlar everywhere else
    field = outline - opening - plinth - cs_union(pil) - rect(-hw - 3, H - 12.0, hw + 3, H + 0.01) - arch_zone - cs_union(imp) \
        - cs_union(quo) - tab.offset(0.6, MJ, 4.0) - cop
    field = field ^ rect(-hw, 0.0, hw, H + 13.0)
    parts.append(rock_ashlar(field, seed=seed + 5, course=5.4, lmin=7.0, lmax=14.0, d=0.6, face=0.6, datum=7.0))
    return union(parts), opening, lt


def liner_stone(opening, depth=30.0, t=2.4, course=5.4, spring=52.0, r0=30.0):
    """The tunnel lining behind a portal: the arch's barrel ``depth`` long, ``t`` thick, its
    inner face jointed in the portal's courses along the jambs and in rings round the arch, a
    ring joint every 9 mm along its length. Local as the portal, running from w = 0 back to
    w = -depth. Prints standing on its end."""
    ring = (opening.offset(t, MJ, 4.0) - opening) ^ rect(-200, 0.0, 200, 300)
    cuts = []
    for v in np.arange(7.0, spring, course):
        for s in (-1, 1):
            a, e = sorted((s * (r0 - 0.01), s * (r0 + 0.3)))
            cuts.append(rect(a, v - 0.25, e, v + 0.25))
    for a in np.linspace(0, math.pi, 13)[1:-1]:
        c, s_ = math.cos(a), math.sin(a)
        cuts.append(poly([((r0 - 0.01) * c - 0.25 * s_, spring + (r0 - 0.01) * s_ + 0.25 * c), ((r0 + 0.35) * c - 0.25 * s_, spring + (r0 + 0.35) * s_ + 0.25 * c),
                          ((r0 + 0.35) * c + 0.25 * s_, spring + (r0 + 0.35) * s_ - 0.25 * c), ((r0 - 0.01) * c + 0.25 * s_, spring + (r0 - 0.01) * s_ - 0.25 * c)]))
    body = ext(ring - cs_union(cuts), -depth, 0.0)
    rings = union([ext((opening.offset(0.3, MJ, 4.0) - opening) ^ rect(-200, 0.0, 200, 300), -w - 0.2, -w + 0.2)
                   for w in np.arange(9.0, depth - 1.0, 9.0)])
    return body - rings


def wing_stone(Lw=76.0, h0=86.0, h1=26.0, T=4.0, side=1, seed=0, back=6.0):
    """A wing wall in the portal's stone: a plinth of big stones, rock-faced ashlar, a
    smooth coping along its raking top and a rock-faced end pier with a cap. Local: u along the
    wall away from the portal (toward ``side`` * u), v up, w out of the face (the back at
    w = -T); it starts ``back`` short of u = 0 so it can be cut square to the portal's side."""
    s = float(side)

    def S(cs):
        return cs.transform(np.array([[s, 0.0, 0.0], [0.0, 1.0, 0.0]])) if s < 0 else cs

    def top(u):
        return h0 + (h1 - h0) * u / Lw

    outline = cs_union([poly([(-back, 0.0), (Lw, 0.0), (Lw, top(Lw)), (-back, top(-back))]), rect(Lw - 10.0, 0.0, Lw, h1 + 9.0)])
    parts = [ext(S(outline), -T, 0.0)]
    plinth = rect(-back, 0.0, Lw, 7.0)
    parts.append(rock_ashlar(S(plinth), seed=seed + 1, course=7.0, lmin=14.0, lmax=22.0, d=1.2, face=0.7))
    cop = poly([(-back, top(-back)), (Lw - 10.0, top(Lw - 10.0)), (Lw - 10.0, top(Lw - 10.0) - 4.6), (-back, top(-back) - 4.6)])
    parts.append(_dressed(S(cop), 0.0, 2.2, 0.6))
    pier = rect(Lw - 10.0, 7.0, Lw, h1 + 6.0)
    parts.append(ext(S(pier), -0.01, 0.8))
    parts.append(rock_ashlar(S(pier), seed=seed + 2, course=6.2, lmin=10.4, lmax=10.4, w0=0.8, d=0.8, face=0.7,
                             u0=min(S(pier).bounds()[0], S(pier).bounds()[2])))
    parts.append(_dressed(S(rect(Lw - 10.0, h1 + 6.0, Lw, h1 + 9.0)), 0.0, 2.8, 0.9))
    field = outline - plinth - cop - pier - rect(Lw - 10.0, h1 + 5.9, Lw + 1, h1 + 10.0)
    parts.append(rock_ashlar(S(field), seed=seed + 5, course=5.4, lmin=7.0, lmax=14.0, d=0.6, face=0.6, datum=7.0))
    return union(parts)


# ================================================================== 73 the Blackwater Sand House
def brick_english(region, datum=0.0, soldiers=()):
    """English bond: a course of headers over a course of stretchers, all the way up, with a
    soldier course (bricks on end) at each ``soldiers`` v (the Blackwater Sand House)."""
    if region.is_empty():
        return M()
    b = region.bounds()
    bh = 0.8
    bricks = []
    sold = [(v, v + 2.3) for v in soldiers]
    for k in range(int(math.floor((b[1] - datum) / bh)) - 1, int(math.ceil((b[3] - datum) / bh)) + 1):
        v = datum + k * bh
        if any(s0 - 0.01 < v + bh / 2 < s1 + 0.01 for s0, s1 in sold):
            continue
        L = 1.2 if k % 2 else 2.4
        off = 0.0 if k % 2 == 0 else 0.6
        bricks += [rect(u + 0.1, v + 0.1, u + L - 0.1, v + bh - 0.1) for u in np.arange(b[0] - 2.4 + off, b[2] + 2.4, L)]
    for s0, s1 in sold:
        bricks += [rect(u + 0.1, s0 + 0.1, u + 0.8 - 0.1, s1 - 0.1) for u in np.arange(b[0] - 1.0, b[2] + 1.0, 0.8)]
    return M.extrude(region, 0.1) + ext(cs_union(bricks) ^ region, 0.09, 0.35)


def foundation_tooled(reg, seed=0):
    """Tooled granite: long blocks in one course, each face drafted round its edge and dressed
    with fine plumb tool lines (the Blackwater Sand House)."""
    b = reg.bounds()
    rng = np.random.default_rng(seed)
    out = M.extrude(reg, 0.25)
    blocks = []
    u = b[0] - rng.uniform(0.0, 8.0)
    while u < b[2]:
        L = rng.uniform(9.0, 15.0)
        r = rect(u + 0.25, b[1] + 0.25, u + L - 0.25, b[3] - 0.25) ^ reg
        if not r.is_empty():
            blocks.append(r)
        u += L
    body = ext(cs_union(blocks), 0.2, 0.7)
    lines = cs_union([rect(x - 0.2, b[1] + 0.9, x + 0.2, b[3] - 0.9) for x in np.arange(b[0] + 0.9, b[2], 0.9)])
    inner = cs_union([bl.offset(-0.6, MJ, 4.0) for bl in blocks])
    return out + body - ext(lines ^ inner, 0.5, 1.0)


def frieze_sanddomes(L, h, b, pitch, margin, pair, half):
    """Locomotive sand domes: at every station a dome on its base ring with a lid, a pipe
    running between them (the Blackwater Sand House)."""
    v0, v1 = 0.6, h - 0.6
    out = [_st(rect(0.3, v0 + 0.5, L - 0.3, v0 + 0.95), b, 0.25)]
    for u in CO._us(L, pitch, margin, 0.0):
        rw = min(2.4, pitch * 0.3)
        hd = v1 - v0 - 1.4
        dome = poly([(u + rw * math.cos(t), v0 + 1.0 + hd * math.sin(t)) for t in np.linspace(0, math.pi, 17)])
        out.append(_st(cs_union([dome, rect(u - rw - 0.3, v0, u + rw + 0.3, v0 + 1.0)]), b + 0.25, 0.35))
        out.append(_st(rect(u - 0.7, v0 + 1.0 + hd - 0.1, u + 0.7, v0 + 1.0 + hd + 0.6), b + 0.25, 0.5))
    return out, []


def course_rivetpairs(L, h, b, pitch, margin, p):
    """An iron strap with its rivets in pairs."""
    vc = h / 2
    strap = rect(0.3, vc - 0.45, L - 0.3, vc + 0.45)
    rv = cs_union([circle((u + du, vc), 0.3, 10) for u in np.arange(1.6, L - 1.2, 3.2) for du in (-0.45, 0.45)])
    return [ext(strap, b - 0.05, b + 0.25), ext(rv, b + 0.2, b + 0.45)]


def bracket_sandcove(h, d, t):
    """A cove bracket: a plumb back, a flat soffit, the front a quarter hollow, a bead at the
    foot (side profile, top at v = 0)."""
    hb = max(3.0, h)
    r = min(d - 0.6, hb - 0.9)
    pts = [(0.0, 0.0), (d, 0.0), (d, -0.6)] + [(d - r + r * math.cos(a), -0.6 - r * math.sin(a))
                                               for a in np.linspace(0.0, math.pi / 2, 10)][1:]
    pts += [(d - r, -hb + 0.6), (0.0, -hb)]
    return cs_union([poly(pts), circle((0.55, -hb + 0.5), 0.5, 12)])


CO.FRIEZE_EXTRA.update(sanddomes=frieze_sanddomes)
CO.COURSE_EXTRA.update(rivetpairs=course_rivetpairs)
TW.BRACKET_EXTRA.update(sandcove=bracket_sandcove)
TW.FOUNDATION_EXTRA.update(tooled=foundation_tooled)


def _brickarch(op_w, h, rise, A=1.6, n=9):
    """A segmental arch of rowlock bricks over an opening ``op_w`` wide, its springing at h - rise."""
    half = op_w / 2
    R = (half * half + rise * rise) / (2 * rise)
    cy = h - R
    a0 = math.asin(half / R)
    ts = np.linspace(-a0, a0, 24)
    band = poly([((R - 0.05) * math.sin(t), cy + (R - 0.05) * math.cos(t)) for t in ts] +
                [((R + A) * math.sin(t), cy + (R + A) * math.cos(t)) for t in ts[::-1]])
    parts = [band]
    for k in range(n):
        t0 = -a0 + 2 * a0 * k / n + 0.012
        t1 = -a0 + 2 * a0 * (k + 1) / n - 0.012
        pts = [((R + 0.15) * math.sin(t0), cy + (R + 0.15) * math.cos(t0)), ((R + A) * math.sin(t0), cy + (R + A) * math.cos(t0)),
               ((R + A) * math.sin(t1), cy + (R + A) * math.cos(t1)), ((R + 0.15) * math.sin(t1), cy + (R + 0.15) * math.cos(t1))]
        parts.append(poly(pts))
    return parts, cy, R


def window_sand(w=8.0, h=13.0, rise=1.6):
    """The sand house's window: six-over-six lights under a segmental head, a rowlock brick
    arch with a keystone over it, a stone sill with a drip."""
    op = O.opening_cs(w, h, rise)
    plug_cs = op.offset(-O.CLR, MJ, 4.0)
    pl = O.PLUG
    g = plug_cs.offset(-0.5, MJ, 4.0)
    sash = _glazed([ext(plug_cs, -pl, -0.6)], g, pl, _muntins(g, 3, 4, 0.4), plug_cs)
    bricks, cy, R = _brickarch(w, h, rise)
    parts = [ext(op - op.offset(-RIB, MJ, 4.0), 0.0, 0.7), ext((op.offset(0.9, MJ, 4.0) - op) ^ rect(-w, 0.0, w, h - rise), 0.0, 0.5)]
    parts += [ext(bricks[0], 0.0, 0.4)] + [ext(bk, 0.39, 0.75) for bk in bricks[1:]]
    parts.append(chamfer_box(-0.8, h - 0.4, 0.8, h + 2.1, 0.0, 1.0, c=0.25))
    parts.append(chamfer_box(-w / 2 - 1.5, -1.3, w / 2 + 1.5, 0.2, 0.0, 1.3, c=0.35, bottom=0.9))
    return O._one_piece(sash, parts, op, plug_cs, pl, h + 2.1, -1.3)


def door_sand(w=10.0, h=22.0, rise=1.6):
    """The sand house's door: a boarded leaf with a two-light window, a three-light transom
    under a segmental head and its rowlock arch."""
    op = O.opening_cs(w, h, rise)
    plug_cs = op.offset(-O.CLR, MJ, 4.0)
    pl = O.PLUG
    ht = h - rise - 4.0
    leaf = plug_cs.offset(-0.3, MJ, 4.0) ^ rect(-w, 0.0, w, ht)
    lb = leaf.bounds()
    grooves = cs_union([rect(u - 0.18, -1, u + 0.18, h + 1) for u in np.arange(lb[0] + 1.3, lb[2], 1.3)]) ^ leaf
    gl = rect(lb[0] + 1.1, ht * 0.62, lb[2] - 1.1, ht - 1.0)
    body = [ext(plug_cs, -pl, -1.0), ext(plug_cs - plug_cs.offset(-0.5, MJ, 4.0), -pl, 0.0),
            ext(leaf, -1.0, -0.6) - ext(grooves, -0.8, -0.5), ext(rect(-w, ht, w, ht + 0.7) ^ plug_cs, -pl, -0.5)]
    body.append(ext(cs_union([rect(lb[0] + 0.4, 1.4, lb[2] - 0.4, 2.4), rect(lb[0] + 0.4, ht * 0.62 - 1.8, lb[2] - 0.4, ht * 0.62 - 0.8),
                              stroke([(lb[0] + 0.9, 2.2), (lb[2] - 0.9, ht * 0.62 - 1.6)], 0.9, caps=False)]), -0.61, -0.25))
    tr = plug_cs.offset(-0.5, MJ, 4.0) ^ rect(-w, ht + 0.7, w, 999)
    tb = tr.bounds()
    bars = cs_union([rect(gl.bounds()[0] + (gl.bounds()[2] - gl.bounds()[0]) / 2 - 0.22, gl.bounds()[1] - 1,
                          gl.bounds()[0] + (gl.bounds()[2] - gl.bounds()[0]) / 2 + 0.22, gl.bounds()[3] + 1)] +
                    [rect(tb[0] + (tb[2] - tb[0]) * k / 3 - 0.22, tb[1] - 1, tb[0] + (tb[2] - tb[0]) * k / 3 + 0.22, tb[3] + 1) for k in (1, 2)])
    sash = _glazed(body, gl + tr, pl, bars, plug_cs)
    bricks, cy, R = _brickarch(w, h, rise, n=11)
    parts = [ext(op - op.offset(-RIB, MJ, 4.0), 0.0, 0.7), ext((op.offset(0.9, MJ, 4.0) - op) ^ rect(-w, 0.0, w, h - rise), 0.0, 0.5)]
    parts += [ext(bricks[0], 0.0, 0.4)] + [ext(bk, 0.39, 0.75) for bk in bricks[1:]]
    parts.append(chamfer_box(-0.9, h - 0.4, 0.9, h + 2.1, 0.0, 1.0, c=0.25))
    return O._one_piece(sash, parts, op, plug_cs, pl, h + 2.1, 0.0)


def door_sandbin(w=16.0, h=20.0):
    """The wet-sand doors: a pair of leaves of diagonal boards in heavy frames, iron straps,
    under a timber lintel on corbels."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, MJ, 4.0)
    pl = O.PLUG
    lb = plug_cs.offset(-0.3, MJ, 4.0).bounds()
    body = [ext(plug_cs, -pl, -1.0), ext(plug_cs - plug_cs.offset(-0.5, MJ, 4.0), -pl, 0.0)]
    for (a, e, sg) in ((lb[0], -0.15, 1), (0.15, lb[2], -1)):
        leaf = rect(a, lb[1], e, lb[3])
        fld = leaf.offset(-1.0, MJ, 4.0)
        diag = cs_union([stroke([(x, lb[1] - 2), (x + sg * 30.0, lb[1] + 28.0)], 0.3, caps=False) for x in np.arange(a - 30.0, e + 30.0, 1.3)])
        body.append(ext(leaf, -1.0, -0.6) - ext(diag ^ fld, -0.8, -0.5))
        body.append(ext(leaf - fld, -0.61, -0.25))
        hinge_u = a + 0.4 if sg > 0 else e - 0.4
        body.append(ext(cs_union([_strap_hinge(hinge_u, hinge_u + sg * 5.5, v) for v in (lb[1] + 2.5, lb[3] - 2.5)]), -0.26, -0.05))
    parts = [ext(op - op.offset(-RIB, MJ, 4.0), 0.0, 0.7), ext((op.offset(1.4, MJ, 4.0) - op) ^ rect(-w, 0.0, w, h + 1.4), 0.0, 0.7),
             chamfer_box(-w / 2 - 2.6, h + 1.39, w / 2 + 2.6, h + 3.2, 0.0, 1.5, c=0.4, bottom=1.2)]
    for s in (-1, 1):
        parts.append(ext(poly([(s * (w / 2 + 1.4), h + 1.4), (s * (w / 2 + 2.6), h + 1.4), (s * (w / 2 + 1.4), h - 0.8)]), 0.0, 1.2))
    return O._one_piece(body, parts, op, plug_cs, pl, h + 3.2, 0.0)


def chimney_sand(w=7.0, d=7.0, h=16.0):
    """The drying stove's stack: English-bond brick, three corbelled courses under a stone cap,
    a round clay pot. Local: centred, z = 0 at its seat."""
    h = round(h / 0.2) * 0.2
    zt = h - 3.0
    body = box([-w / 2, -d / 2, 0.0], [w / 2, d / 2, zt])
    body = body + TW._skin(w, d, 0.0, zt - 0.2, lambda reg, i: brick_english(reg))
    z = zt
    for k in range(3):
        g = 0.3 * (k + 1)
        body = body + box([-w / 2 - g, -d / 2 - g, z - 0.01], [w / 2 + g, d / 2 + g, z + 0.6])
        z += 0.6
    body = body + chamfer_box(-w / 2 - 1.2, -d / 2 - 1.2, w / 2 + 1.2, d / 2 + 1.2, z - 0.01, 1.0, c=0.4)
    pot = M.cylinder(3.0, 1.6, 1.3, 20).translate([0, 0, z + 0.98]) + M.cylinder(0.6, 1.7, 1.7, 20).translate([0, 0, z + 3.9])
    return body + pot - M.cylinder(10.0, 0.8, 0.8, 16).translate([0, 0, z + 1.5])


def sand_legs(h=58.0, s=17.0, leg=2.0, ring=1.6, hole=7.3, open_face=None):
    """The sand tower's steel frame, one piece printed upright: four legs splayed a little,
    X braces in every face at two tiers, girts, a plate at the head the bin sits on (a hole for
    its hopper), and the air pipe up one leg. Prints upside down on the plate. Local: centred,
    z = 0 at the legs' feet (square pegs below)."""
    out = []
    top = s / 2 - 0.8
    for sx in (-1, 1):
        for sy in (-1, 1):
            out.append(M.hull_points([(sx * s / 2 + dx, sy * s / 2 + dy, 0.0) for dx in (-leg / 2, leg / 2) for dy in (-leg / 2, leg / 2)] +
                                     [(sx * top + dx, sy * top + dy, h) for dx in (-leg / 2, leg / 2) for dy in (-leg / 2, leg / 2)]))
            out.append(box([sx * s / 2 - 0.6, sy * s / 2 - 0.6, -1.6], [sx * s / 2 + 0.6, sy * s / 2 + 0.6, 0.01]))

    def at(z):
        return s / 2 + (top - s / 2) * z / h

    zs = (1.5, h * 0.5, h - 1.2)
    for z in zs:
        a = at(z)
        for sg in (-1, 1):
            out.append(box([-a, sg * a - 0.5, z - 0.6], [a, sg * a + 0.5, z + 0.6]))
            out.append(box([sg * a - 0.5, -a, z - 0.6], [sg * a + 0.5, a, z + 0.6]))
    for tier, (za, zb) in enumerate(((zs[0], zs[1]), (zs[1], zs[2]))):
        aa, ab = at(za), at(zb)
        for sg in (-1, 1):
            for (p0, p1) in (((-aa, za), (ab, zb)), ((aa, za), (-ab, zb))):
                if not (tier == 1 and open_face == sg):          # the track side's upper bay stays open for the spouts
                    out.append(M.hull_points([(p0[0], sg * aa + dy, p0[1] + dz) for dy in (-0.4, 0.4) for dz in (0.0, 1.2)] +
                                             [(p1[0], sg * ab + dy, p1[1] - dz) for dy in (-0.4, 0.4) for dz in (0.0, 1.2)]))
                out.append(M.hull_points([(sg * aa + dy, p0[0], p0[1] + dz) for dy in (-0.4, 0.4) for dz in (0.0, 1.2)] +
                                         [(sg * ab + dy, p1[0], p1[1] - dz) for dy in (-0.4, 0.4) for dz in (0.0, 1.2)]))
    a = at(h)
    deck = box([-a - 1.2, -a - 1.2, h - 0.01], [a + 1.2, a + 1.2, h + ring]) - M.cylinder(ring + 2.0, hole, hole, 48).translate([0, 0, h - 1.0])
    out.append(deck)
    pipe = M.hull_points([(s / 2 + 1.3 + dx, -s / 2 + dy, 0.0) for dx in (-0.55, 0.55) for dy in (-0.55, 0.55)] +
                         [(top + 1.3 + dx, -top + dy, h) for dx in (-0.55, 0.55) for dy in (-0.55, 0.55)])
    return union(out) + pipe


def sand_bin(r=11.0, h=18.0, hop=9.0, flat=2.6, rh=7.0):
    """The sand tower's bin, one piece printed upside down on its top: a riveted steel drum
    with seams, its flat bottom resting on the frame's plate, the hopper (``rh`` at the top)
    coned down through the plate to a flat outlet the spouts glue to. Local: centred, z = 0 at
    the outlet, the drum's bottom at hop, its top at hop + h."""
    n = 64
    out = [M.cylinder(hop + 0.01, flat, rh, n), M.cylinder(h, r, r, n).translate([0, 0, hop])]
    for z in (hop + h * 0.33, hop + h * 0.66, hop + h - 0.9):
        out.append(M.cylinder(0.9, r + 0.35, r + 0.35, n).translate([0, 0, z]))
    riv = union([M.sphere(0.32, 8).translate([r * math.cos(a), r * math.sin(a), hop + 1.2]) for a in np.linspace(0, 2 * math.pi, 40, endpoint=False)])
    return union(out) + riv


def sand_cap(r=11.0, rise=6.0):
    """The bin's roof: a low cone on a flat rim that sits on the drum's top and stands out
    past it, a hatch and a vent. Local: centred, z = 0 at its foot."""
    lip = M.cylinder(1.4, r + 0.9, r + 0.9, 64)
    cone = M.cylinder(rise, r + 0.9, 1.2, 64).translate([0, 0, 1.39])
    hatch = box([2.0, -2.2, 0.0], [6.2, 2.2, 1.0]).transform(np.array([[1.0, 0, 0, 0], [0, 1.0, 0, 0], [0, 0, 1.0, 1.4 + rise * 0.55]]))
    vent = M.cylinder(2.0, 0.9, 0.9, 16).translate([0, 0, 1.3 + rise]) + M.cylinder(0.6, 1.6, 0.3, 16).translate([0, 0, 3.2 + rise])
    return lip + cone + hatch + vent


def sand_spouts(reach=21.0, drop=17.0, r=0.95, flat=2.6):
    """The two sand spouts, one piece printed upright: a flanged collar that glues under the
    bin's outlet, two pipes raking down and out toward the track, each with a telescoping
    lower length and a counterweight lever. Local: z = 0 at the collar's top, the spouts
    reaching toward -y."""
    out = [M.cylinder(1.6, flat, flat, 32).translate([0, 0, -1.6]), M.cylinder(3.0, 1.9, 1.9, 24).translate([0, 0, -4.6])]
    for sx in (-1, 1):
        p0 = np.array([sx * 0.9, 0.0, -4.0])
        p1 = np.array([sx * 4.5, -reach, -drop])
        d = p1 - p0
        L = float(np.linalg.norm(d))
        d = d / L
        # an upright cylinder rotated onto the pipe's axis
        z = np.array([0.0, 0.0, -1.0])
        v = np.cross(z, d)
        c = float(z @ d)
        vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
        Rm = np.eye(3) + vx + vx @ vx * (1.0 / (1.0 + c))
        A = np.column_stack([Rm @ np.array([1.0, 0, 0]), Rm @ np.array([0, 1.0, 0]), Rm @ np.array([0, 0, 1.0]), p0])
        pipe = M.cylinder(L, r, r, 20).translate([0, 0, -L]).transform(A)
        sleeve = M.cylinder(L * 0.45, r + 0.35, r + 0.35, 20).translate([0, 0, -L]).transform(A)
        band = M.cylinder(0.7, r + 0.55, r + 0.55, 20).translate([0, 0, -L * 0.55 - 0.35]).transform(A)
        out += [pipe, sleeve, band]
    return union(out)


def wetbin(w=20.0, d=16.0, h=9.0, t=1.2):
    """The wet-sand bin: three walls of planks between posts on a sill, open toward the track,
    heaped with sand above the boards. Local: z = 0 at its foot; its open side toward -y.
    Returns (bin, heap)."""
    walls = box([-w / 2, -d / 2, 0.0], [w / 2, d / 2, h]) - box([-w / 2 + t, -d / 2 - 1.0, 1.2], [w / 2 - t, d / 2 - t, h + 1.0])
    walls = walls - box([-w / 2 + t, -d / 2 - 1.0, -1.0], [w / 2 - t, -d / 2 + 2.0, h + 1.0])
    grooves = union([box([-w / 2 - 1, -d / 2 - 1, z - 0.15], [w / 2 + 1, d / 2 + 1, z + 0.15]) for z in np.arange(1.8, h - 0.5, 1.8)])
    grooves = grooves - box([-w / 2 + 0.3, -d / 2 + 0.3, -1.0], [w / 2 - 0.3, d / 2 - 0.3, h + 1.0])   # surface lines only
    posts = union([box([x - 0.9, y - 0.9, 0.0], [x + 0.9, y + 0.9, h + 0.6]) for x in (-w / 2 + 0.3, 0.0, w / 2 - 0.3) for y in (d / 2 - 0.3,)] +
                  [box([x - 0.9, y - 0.9, 0.0], [x + 0.9, y + 0.9, h + 0.6]) for x in (-w / 2 + 0.3, w / 2 - 0.3) for y in (-d / 2 + 0.6, 0.0)])
    def lumps(p):
        x, y, z = p[:, 0], p[:, 1], p[:, 2]
        k = np.clip(z / (h + 1.8), 0.0, 1.0)
        return np.column_stack([x, y, z * (1.0 + 0.16 * np.sin(x / 1.9) * np.cos(y / 2.3) * k) + 0.6 * np.sin(x / 1.3 + y / 1.7) * k])

    heap = M.sphere(1.0, 64).scale([w / 2 - t - 0.1, d / 2 - 0.4, h + 1.8]).warp_batch(lumps) ^ box([-w / 2 + t + 0.01, -d / 2, 1.21], [w / 2 - t - 0.01, d / 2 - t - 0.01, 60])
    return (walls - grooves) + posts, heap


# ================================================================== 74 the Blackwater Engine House
def brick_american(region, datum=0.0, every=6, piers=(), pier_w=6.0, pier_top=None):
    """American (common) bond: five courses of stretchers to one of headers; ``piers`` (u) are
    brick pilasters ``pier_w`` wide standing 1.1 proud, bonded the same, up to ``pier_top``
    (the Blackwater Engine House)."""
    if region.is_empty():
        return M()
    b = region.bounds()
    bh = 0.8

    def bond(reg, w0):
        rb = reg.bounds()
        bricks = []
        for k in range(int(math.floor((rb[1] - datum) / bh)) - 1, int(math.ceil((rb[3] - datum) / bh)) + 1):
            v = datum + k * bh
            hdr = k % every == 0
            L = 1.2 if hdr else 2.4
            off = (k % 2) * (0.6 if hdr else 1.2)
            bricks += [rect(u + 0.1, v + 0.1, u + L - 0.1, v + bh - 0.1) for u in np.arange(rb[0] - 2.4 + off, rb[2] + 2.4, L)]
        return ext(reg, w0 - 0.01, w0 + 0.1) + ext(cs_union(bricks) ^ reg, w0 + 0.09, w0 + 0.35)

    out = bond(region, 0.0)
    top = b[3] if pier_top is None else pier_top
    for u in piers:
        pr = rect(u - pier_w / 2, b[1] - 1, u + pier_w / 2, top) ^ region
        if pr.is_empty():
            continue
        out = out + ext(pr, 0.0, 1.1) + bond(pr, 1.1)
    return out


def foundation_stippled(reg, seed=0):
    """Bush-stippled concrete: a plain plinth with a drafted margin round a field of small
    random pits, a sloped wash along its top (the Blackwater Engine House)."""
    b = reg.bounds()
    rng = np.random.default_rng(seed)
    out = M.extrude(reg, 0.5)
    inner = reg.offset(-0.6, MJ, 4.0)
    pits = []
    for _ in range(int((b[2] - b[0]) * (b[3] - b[1]) / 1.6)):
        u, v = rng.uniform(b[0], b[2]), rng.uniform(b[1], b[3])
        pits.append(circle((u, v), rng.uniform(0.2, 0.32), 6))
    if pits:
        out = out - ext(cs_union(pits) ^ inner, 0.3, 1.0)
    wash = rect(b[0] - 1, b[3] - 0.8, b[2] + 1, b[3] + 1) ^ reg
    return out + ext(wash, 0.49, 0.75)


def frieze_diamondstacks(L, h, b, pitch, margin, pair, half):
    """Diamond-stack smokestacks: at every station a tapered stack on a saddle crowned by the
    rhombus of its spark arrester, a pipe rail between (the Blackwater Engine House)."""
    v0, v1 = 0.6, h - 0.6
    hh = v1 - v0
    out = [_st(rect(0.3, v0, L - 0.3, v0 + 0.5), b, 0.25)]
    for u in CO._us(L, pitch, margin, 0.0):
        sad = poly([(u - 1.3, v0 + 0.45), (u + 1.3, v0 + 0.45), (u + 0.8, v0 + hh * 0.2), (u - 0.8, v0 + hh * 0.2)])
        stack = poly([(u - 0.55, v0 + hh * 0.2 - 0.05), (u + 0.55, v0 + hh * 0.2 - 0.05), (u + 0.4, v0 + hh * 0.55), (u - 0.4, v0 + hh * 0.55)])
        dia = poly([(u, v0 + hh * 0.5), (u + 1.6, v0 + hh * 0.78), (u, v1), (u - 1.6, v0 + hh * 0.78)])
        out.append(_st(cs_union([sad, stack, dia]), b + 0.25, 0.4))
    return out, []


def course_railprofiles(L, h, b, pitch, margin, p):
    """Rails seen end on in a row: head, web and foot of a T rail every 2.2 mm."""
    parts = []
    s = min(1.0, h / 1.6)
    for u in np.arange(1.2, L - 0.8, 2.2):
        parts += [rect(u - 0.7 * s, 0.25, u + 0.7 * s, 0.25 + 0.3 * s), rect(u - 0.18, 0.25, u + 0.18, h - 0.35),
                  rect(u - 0.42 * s, h - 0.35 - 0.36 * s, u + 0.42 * s, h - 0.25)]
    return [ext(cs_union(parts), b - 0.05, b + 0.4)]


def bracket_enginecorbel(h, d, t):
    """A stepped brick corbel: four courses each standing out beyond the one below (side
    profile, top at v = 0)."""
    hb = max(3.0, h)
    n = 4
    pts = [(0.0, 0.0), (d, 0.0)]
    for k in range(n):
        x = d * (n - k - 1) / n + 0.4 if k < n - 1 else 0.6
        pts += [(d * (n - k) / n + (0.0 if k else 0.0), -hb * (k + 1) / n), (x, -hb * (k + 1) / n)]
    pts[-1] = (0.6, -hb)
    pts.append((0.0, -hb))
    return poly(pts)


CO.FRIEZE_EXTRA.update(diamondstacks=frieze_diamondstacks)
CO.COURSE_EXTRA.update(railprofiles=course_railprofiles)
TW.BRACKET_EXTRA.update(enginecorbel=bracket_enginecorbel)
TW.FOUNDATION_EXTRA.update(stippled=foundation_stippled)


def _hood_mould(w, h, A=1.1, stop=1.4):
    """A projecting brick hood over a round-arched opening: a band following the arch down to
    the springing, square label stops at its ends."""
    r = w / 2
    spring = h - r
    ring = (circle((0.0, spring), r + 0.7 + A, 64) - circle((0.0, spring), r + 0.7, 64)) ^ rect(-w, spring, w, h + 10)
    st = [rect(r + 0.5, spring - stop, r + 0.7 + A + 0.3, spring + 0.01), rect(-r - 0.7 - A - 0.3, spring - stop, -r - 0.5, spring + 0.01)]
    return ring, st


def window_engine(w=13.0, h=30.0):
    """The engine house's side window: twelve small lights under a round head filled with a
    fanlight of five, a projecting brick hood with label stops, a stone sill."""
    op = O.opening_cs(w, h)
    plug_cs = op.offset(-O.CLR, MJ, 4.0)
    pl = O.PLUG
    g = plug_cs.offset(-0.5, MJ, 4.0)
    r = w / 2
    spring = h - r
    gb = g.bounds()
    bars = [rect(gb[0] + (gb[2] - gb[0]) * k / 3 - 0.2, gb[1] - 1, gb[0] + (gb[2] - gb[0]) * k / 3 + 0.2, spring) for k in (1, 2)]
    bars += [rect(gb[0] - 1, gb[1] + (spring - gb[1]) * k / 4 - 0.2, gb[2] + 1, gb[1] + (spring - gb[1]) * k / 4 + 0.2) for k in (1, 2, 3)]
    bars.append(rect(gb[0] - 1, spring - 0.3, gb[2] + 1, spring + 0.3))
    for a in np.linspace(0, math.pi, 6)[1:-1]:
        bars.append(stroke([(0.0, spring), (r * 1.2 * math.cos(a), spring + r * 1.2 * math.sin(a))], 0.4, caps=False))
    sash = _glazed([ext(plug_cs, -pl, -0.6)], g, pl, cs_union(bars), plug_cs)
    ring, stops = _hood_mould(w, h)
    parts = [ext(op - op.offset(-RIB, MJ, 4.0), 0.0, 0.7), ext((op.offset(0.8, RND) - op), 0.0, 0.45),
             ext(ring, 0.0, 1.0), ext(ring - ring.offset(-0.35, RND), 0.99, 1.3)]
    parts += [ext(s_, 0.0, 1.1) for s_ in stops]
    parts.append(chamfer_box(-w / 2 - 1.4, -1.3, w / 2 + 1.4, 0.2, 0.0, 1.3, c=0.35, bottom=0.9))
    return O._one_piece(sash, parts, op, plug_cs, pl, h + 2.1, -1.3)


def oculus_engine(D=14.0):
    """The gable's round window: a wheel of eight lights round a round centre, in a brick
    surround keyed at the four quarters."""
    op = circle((0.0, D / 2), D / 2, 64)
    plug_cs = op.offset(-O.CLR, RND)
    pl = O.PLUG
    g = plug_cs.offset(-0.5, RND)
    c = (0.0, D / 2)
    bars = [circle(c, 1.5, 24) - circle(c, 1.1, 24)]
    for a in np.linspace(0, 2 * math.pi, 9)[:-1]:
        bars.append(stroke([(c[0] + 1.3 * math.cos(a), c[1] + 1.3 * math.sin(a)), (c[0] + D * math.cos(a), c[1] + D * math.sin(a))], 0.4, caps=False))
    sash = _glazed([ext(plug_cs, -pl, -0.6)], g, pl, cs_union(bars), plug_cs)
    ring = circle(c, D / 2 + 1.8, 64) - op
    parts = [ext(op - op.offset(-RIB, RND), 0.0, 0.7), ext(ring, 0.0, 0.7)]
    for a in (0.0, math.pi / 2, math.pi, 1.5 * math.pi):
        k = poly([(c[0] + (D / 2 - 0.2) * math.cos(a + s * 0.16), c[1] + (D / 2 - 0.2) * math.sin(a + s * 0.16)) for s in (-1, 1)] +
                 [(c[0] + (D / 2 + 2.6) * math.cos(a + s * 0.2), c[1] + (D / 2 + 2.6) * math.sin(a + s * 0.2)) for s in (1, -1)])
        parts.append(ext(k, 0.0, 1.2))
    return O._one_piece(sash, parts, op, plug_cs, pl, D + 2.6, -2.6)


def door_engine_arch(w=42.0, h=64.0, leaf_h=None):
    """A stall's doorway head, installed whatever the doors: a double rowlock arch with a
    stone keystone on moulded imposts, and the fanlight filling the round head over a transom
    bar (radial bars, a hub). The opening below stays clear for the track; the leaves are
    separate parts (door_engine_leaf). Facade frame, u centred, v from the floor."""
    r = w / 2
    spring = h - r
    op = O.opening_cs(w, h)
    plug_cs = op.offset(-O.CLR, MJ, 4.0)
    pl = O.PLUG
    head = plug_cs ^ rect(-w, spring - 1.2, w, h + 5)
    g = head.offset(-0.6, MJ, 4.0) ^ rect(-w, spring, w, h + 5)
    bars = [rect(-w, spring - 1.3, w, spring + 0.2)]
    c = (0.0, spring)
    bars.append(circle(c, 2.6, 32) - circle(c, 1.9, 32))
    for a in np.linspace(0, math.pi, 10)[1:-1]:
        bars.append(stroke([(2.2 * math.cos(a), spring + 2.2 * math.sin(a)), (r * 1.2 * math.cos(a), spring + r * 1.2 * math.sin(a))], 0.5, caps=False))
    bars.append(circle(c, r * 0.62, 48) - circle(c, r * 0.62 - 0.5, 48))
    sash = _glazed([ext(head, -pl, -0.6)], g, pl, cs_union(bars), head)
    rings = []
    for k, (r0, r1, n) in enumerate(((r + 0.1, r + 2.5, 21), (r + 2.6, r + 5.0, 25))):
        for j in range(n):
            t0 = math.pi * j / n + 0.012
            t1 = math.pi * (j + 1) / n - 0.012
            rings.append(poly([(r0 * math.cos(t0), spring + r0 * math.sin(t0)), (r1 * math.cos(t0), spring + r1 * math.sin(t0)),
                               (r1 * math.cos(t1), spring + r1 * math.sin(t1)), (r0 * math.cos(t1), spring + r0 * math.sin(t1))]))
    band = (circle(c, r + 5.0, 96) - circle(c, r - 0.05, 96)) ^ rect(-w, spring, w, h + 10)
    parts = [ext(op - op.offset(-RIB, MJ, 4.0), 0.0, 0.7) - ext(rect(-w, -1, w, spring - 1.2), -1, 2),
             ext(band, 0.0, 0.4)] + [ext(bk, 0.39, 0.8) for bk in rings]
    parts.append(ext(poly([(-2.2, h - 0.6), (2.2, h - 0.6), (2.8, h + 5.6), (-2.8, h + 5.6)]), 0.0, 1.5))
    for s in (-1, 1):
        a, e = sorted((s * (r - 0.3), s * (r + 5.6)))
        parts.append(chamfer_box(a, spring - 3.0, e, spring + 0.01, 0.0, 1.6, c=0.4, bottom=1.2))
        a2, e2 = sorted((s * (r - 0.3), s * (r + 1.2)))
        parts.append(ext(rect(a2, 0.0, e2, spring - 2.99), 0.0, 0.6))
    return O._one_piece(sash, parts, op, plug_cs, pl, h + 5.6, 0.0)


def door_engine_leaf(w=20.6, h=40.0, t=1.2, side=1):
    """One leaf of a stall door, printed flat on its back: vertical boards below a rail, six
    lights above, a diagonal brace, strap hinges on the hinge edge (``side`` = +1 hinged at
    u = 0 opening to +u). Local: u across (0..w), v up (0..h), w out of its face (back at 0);
    glue it into the doorway (closed) or by its hinge edge to the jamb, standing open."""
    leaf = rect(0.0, 0.0, w, h)
    out = [ext(leaf, 0.0, t)]
    rail = h * 0.62
    frame = leaf - rect(1.2, 1.2, w - 1.2, rail - 0.4) - rect(1.2, rail + 0.4, w - 1.2, h - 1.2)
    out.append(ext(frame, t - 0.01, t + 0.5))
    grooves = cs_union([rect(u - 0.2, 1.2, u + 0.2, rail - 0.4) for u in np.arange(2.6, w - 1.3, 1.5)])
    out = [out[0] - ext(grooves, t - 0.3, t + 1)] + out[1:]
    out.append(ext(stroke([(1.6, 1.8), (w - 1.6, rail - 1.0)], 1.0, caps=False) ^ rect(1.2, 1.2, w - 1.2, rail - 0.4), t - 0.01, t + 0.45))
    gl = rect(1.2, rail + 0.4, w - 1.2, h - 1.2)
    glb = gl.bounds()
    bars = cs_union([rect(glb[0] + (glb[2] - glb[0]) * k / 3 - 0.22, glb[1], glb[0] + (glb[2] - glb[0]) * k / 3 + 0.22, glb[3]) for k in (1, 2)] +
                    [rect(glb[0], (glb[1] + glb[3]) / 2 - 0.22, glb[2], (glb[1] + glb[3]) / 2 + 0.22)])
    out.append(ext(bars, t - 0.01, t + 0.35))
    hu = 0.0 if side > 0 else w
    out.append(ext(cs_union([_strap_hinge(hu + side * 0.4, hu + side * 9.0, v) for v in (4.0, h - 4.0)]), t - 0.01, t + 0.25))
    return union(out), gl


def smokejack(w=12.0, h0=5.0, flue_h=24.0, r=2.8):
    """A smoke jack, one piece printed upright: a boarded hood tapering up from a curb that
    sits on a flat seat in the roof, a riveted flue with a band and a cap. Local: centred,
    z = 0 at its foot."""
    curb = box([-w / 2, -w / 2, 0.0], [w / 2, w / 2, 1.2])
    hood = M.hull_points([(x * (w / 2 - 0.4), y * (w / 2 - 0.4), 1.19) for x in (-1, 1) for y in (-1, 1)] +
                         [(x * (r + 1.0), y * (r + 1.0), h0) for x in (-1, 1) for y in (-1, 1)])
    flue = M.cylinder(flue_h, r, r * 0.92, 32).translate([0, 0, h0 - 0.01])
    band = M.cylinder(0.8, r + 0.35, r + 0.3, 32).translate([0, 0, h0 + flue_h * 0.5])
    cap = M.cylinder(1.4, r * 0.92, r + 1.2, 32).translate([0, 0, h0 + flue_h - 0.4]) + M.cylinder(0.6, r + 1.2, r + 1.2, 32).translate([0, 0, h0 + flue_h + 0.99])
    return curb + hood + flue + band + cap - M.cylinder(flue_h + 10, r - 0.8, r - 0.8, 24).translate([0, 0, h0 + 4.0])


def monitor_engine(L=170.0, w=24.0, hw=13.0, s=0.45, over=1.8):
    """The clerestory along the ridge, one piece printed upright: plain walls sitting on a flat
    seat, a row of three-light sashes each side, end walls with a louvre, a low roof of standing
    seams with a ridge roll. Local: centred on its length (along y), z = 0 at its foot.
    Returns (monitor, glass zone, z of its eave)."""
    body = box([-w / 2, -L / 2, 0.0], [w / 2, L / 2, hw])
    lights, glass = [], []
    zl0, zl1 = hw - 7.2, hw - 1.8
    for y in np.arange(-L / 2 + 8.0, L / 2 - 6.0, 10.0):
        for sg in (-1, 1):
            x0, x1 = sorted((sg * (w / 2 - 0.5), sg * (w / 2 + 0.1)))
            lights.append(box([x0, y - 3.4, zl0], [x1, y + 3.4, zl1]))
            glass.append(box([x0 - 0.01, y - 3.4, zl0], [x1 - 0.01, y + 3.4, zl1]))
    body = body - union(lights)
    muntins = []
    for y in np.arange(-L / 2 + 8.0, L / 2 - 6.0, 10.0):
        for sg in (-1, 1):
            x0, x1 = sorted((sg * (w / 2 - 0.5), sg * (w / 2 + 0.25)))
            for dy in (-1.13, 1.13):
                muntins.append(box([x0, y + dy - 0.2, zl0], [x1, y + dy + 0.2, zl1]))
            muntins.append(box([x0 - (0.3 if sg < 0 else 0), y - 3.9, zl1 - 0.01], [x1 + (0.3 if sg > 0 else 0), y + 3.9, zl1 + 0.6]))
            muntins.append(box([x0 - (0.4 if sg < 0 else 0), y - 3.9, zl0 - 0.8], [x1 + (0.4 if sg > 0 else 0), y + 3.9, zl0 + 0.01]))
    lv = union([box([-w / 2 + 3.0, sg * (L / 2) - 0.5, z - 0.25], [w / 2 - 3.0, sg * (L / 2) + 0.5, z + 0.25])
                for sg in (-1, 1) for z in np.arange(3.0, hw - 1.5, 1.4)])
    eave = M.hull_points([(x * w / 2, y * L / 2, hw - 0.01) for x in (-1, 1) for y in (-1, 1)] +
                         [(x * (w / 2 + over), y * (L / 2 + over), hw + over) for x in (-1, 1) for y in (-1, 1)])
    rf = M.hull_points([(x * (w / 2 + over), y * (L / 2 + over), hw + over - 0.01) for x in (-1, 1) for y in (-1, 1)] +
                       [(0.0, y * (L / 2 + over), hw + over + s * (w / 2 + over)) for y in (-1, 1)])
    seams = union([box([x - 0.25, -L / 2 - over, 0], [x + 0.25, L / 2 + over, 400]) for x in np.arange(-w / 2, w / 2 + 0.1, 3.0)])
    rf_top = rf + (seams ^ rf.translate([0, 0, 0.35]) - rf)
    roll = M.cylinder(L + 2 * over, 0.8, 0.8, 16).rotate([90, 0, 0]).translate([0, L / 2 + over, hw + over + s * (w / 2 + over)])
    return body + union(muntins) + lv + eave + rf_top + roll, union(glass), hw


# ================================================================== 75 the Blackwater Yard Office
def rustic_channel(region, datum=0.0, pitch=2.2):
    """Channel rustic siding: wide flat boards, each with a deep square channel along its foot
    where it laps the board below (the Blackwater Yard Office's first storey)."""
    if region.is_empty():
        return M()
    b = region.bounds()
    out = M.extrude(region, 0.45)
    ch = cs_union([rect(b[0] - 1, v, b[2] + 1, v + 0.45) for v in np.arange(datum + pitch * math.floor((b[1] - datum) / pitch), b[3], pitch)])
    return out - ext(ch ^ region, 0.12, 1.0)


def boards_vgroove(region, datum=0.0, pitch=1.4, band=None):
    """Narrow plumb boards with a V groove at every joint, a flat band across them at ``band``
    (v) (the Blackwater Yard Office's second storey)."""
    if region.is_empty():
        return M()
    b = region.bounds()
    out = M.extrude(region, 0.35)
    gr = cs_union([poly([(u - 0.28, b[1] - 1), (u + 0.28, b[1] - 1), (u + 0.28, b[3] + 1), (u - 0.28, b[3] + 1)])
                   for u in np.arange(b[0] + pitch / 2, b[2], pitch)])
    out = out - ext(gr ^ region, 0.15, 1.0)
    if band is not None:
        out = out + _st(rect(b[0] - 1, band - 0.9, b[2] + 1, band + 0.9) ^ region, 0.0, 0.8)
    return out


def foundation_sandstone(reg, seed=0):
    """Dressed sandstone: two courses of smooth blocks in broken joint, each with a chamfered
    edge, a projecting chamfered cap (the Blackwater Yard Office)."""
    b = reg.bounds()
    rng = np.random.default_rng(seed)
    out = M.extrude(reg, 0.25)
    hh = (b[3] - b[1] - 0.9) / 2
    for k in range(2):
        v0 = b[1] + k * hh
        u = b[0] - rng.uniform(0.0, 7.0) - (3.5 if k else 0.0)
        while u < b[2]:
            L = rng.uniform(7.0, 11.0)
            r = rect(u + 0.2, v0 + 0.2, u + L - 0.2, v0 + hh - 0.2) ^ reg
            if not r.is_empty():
                bb = r.bounds()
                out = out + chamfer_box(bb[0], bb[1], bb[2], bb[3], 0.2, 0.5, c=0.25)
            u += L
    cap = rect(b[0] - 1, b[3] - 0.9, b[2] + 1, b[3] + 1) ^ reg
    return out + ext(cap, 0.24, 0.8)


def frieze_orderhoops(L, h, b, pitch, margin, pair, half):
    """Train-order hoops: at every station a hoop on its handle leaning to the right, the
    order's string loop inside it, a thin rail between (the Blackwater Yard Office's joint)."""
    v0, v1 = 0.6, h - 0.6
    hh = v1 - v0
    out = [_st(rect(0.3, v0, L - 0.3, v0 + 0.45), b, 0.25)]
    for u in CO._us(L, pitch, margin, 0.0):
        r = min(hh * 0.3, pitch * 0.2)
        c = (u + 0.3, v1 - r - 0.1)
        hoop = circle(c, r, 24) - circle(c, r - 0.45, 24)
        handle = stroke([(u - r * 0.5, v0 + 0.3), (c[0] - r * 0.3, c[1] - r + 0.2)], 0.45, caps=False)
        out.append(_st(cs_union([hoop, handle]) ^ rect(0.0, v0, L, v1), b + 0.25, 0.35))
    return out, []


def frieze_lanterns(L, h, b, pitch, margin, pair, half):
    """Railroad hand lanterns: at every station a lantern's globe between its guards, a bail
    over it, a base below (the Blackwater Yard Office's eave)."""
    v0, v1 = 0.6, h - 0.6
    hh = v1 - v0
    out = []
    for u in CO._us(L, pitch, margin, 0.0):
        base = rect(u - 1.1, v0, u + 1.1, v0 + hh * 0.14)
        globe = cs_union([circle((u, v0 + hh * 0.42), hh * 0.26, 20), rect(u - 0.5, v0 + hh * 0.12, u + 0.5, v0 + hh * 0.7)])
        top = poly([(u - 0.9, v0 + hh * 0.66), (u + 0.9, v0 + hh * 0.66), (u + 0.4, v0 + hh * 0.78), (u - 0.4, v0 + hh * 0.78)])
        bail = (circle((u, v0 + hh * 0.78), hh * 0.2, 20) - circle((u, v0 + hh * 0.78), hh * 0.2 - 0.42, 20)) ^ rect(u - 5, v0 + hh * 0.78, u + 5, v1)
        guards = cs_union([rect(u - hh * 0.3, v0 + hh * 0.2, u - hh * 0.3 + 0.42, v0 + hh * 0.64), rect(u + hh * 0.3 - 0.42, v0 + hh * 0.2, u + hh * 0.3, v0 + hh * 0.64)])
        out.append(_st(cs_union([base, globe, top, bail, guards]) ^ rect(0.0, v0, L, v1), b, 0.45))
    return out, []


def course_insulators(L, h, b, pitch, margin, p):
    """A telegraph crossarm: a bar with glass insulators standing on it every 2.6 mm."""
    arm = rect(0.3, 0.25, L - 0.3, 0.75)
    ins = cs_union([cs_union([rect(u - 0.35, 0.7, u + 0.35, h - 0.55), circle((u, h - 0.6), 0.42, 12)]) for u in np.arange(1.3, L - 1.0, 2.6)])
    return [ext(arm, b - 0.05, b + 0.3), ext(ins, b - 0.05, b + 0.45)]


def bracket_officestick(h, d, t):
    """A stick bracket: a plumb post and a flat top rail framing a solid triangle, a turned drop
    under the post (side profile, top at v = 0)."""
    hb = max(3.0, h)
    tri = poly([(0.0, 0.0), (d, 0.0), (d, -0.7), (1.0, -hb + 1.4), (1.0, -hb + 0.8), (0.0, -hb + 0.8)])
    drop = cs_union([rect(0.0, -hb - 0.2, 0.9, -hb + 0.81), circle((0.45, -hb - 0.3), 0.45, 12)])
    return cs_union([tri, drop])


CO.FRIEZE_EXTRA.update(orderhoops=frieze_orderhoops, lanterns=frieze_lanterns)
CO.COURSE_EXTRA.update(insulators=course_insulators)
TW.BRACKET_EXTRA.update(officestick=bracket_officestick)
TW.FOUNDATION_EXTRA.update(sandstone=foundation_sandstone)


def window_office_lower(w=8.0, h=16.0):
    """The yard office's lower window: two over two in a moulded casing under a flat
    entablature cap (a frieze board with a row of dentils under a projecting cornice), a sill
    on blocks."""
    op = O.opening_cs(w, h, 0)
    plug_cs = op.offset(-O.CLR, MJ, 4.0)
    pl = O.PLUG
    g = plug_cs.offset(-0.5, MJ, 4.0)
    sash = _glazed([ext(plug_cs, -pl, -0.6)], g, pl, _muntins(g, 2, 2, 0.42) + (rect(-w, h * 0.5 - 0.3, w, h * 0.5 + 0.3) ^ g), plug_cs)
    hw = w / 2 + 1.2
    parts = [ext(op - op.offset(-RIB, MJ, 4.0), 0.0, 0.7), ext(op.offset(1.2, MJ, 4.0) - op, 0.0, 0.55),
             ext(op.offset(1.2, MJ, 4.0) - op.offset(0.7, MJ, 4.0), 0.54, 0.8),
             ext(rect(-hw, h + 1.19, hw, h + 3.2), 0.0, 0.7),
             chamfer_box(-hw - 1.0, h + 3.19, hw + 1.0, h + 4.4, 0.0, 1.4, c=0.35, bottom=1.2),
             chamfer_box(-hw - 0.4, -1.2, hw + 0.4, 0.2, 0.0, 1.2, c=0.3, bottom=0.8)]
    for u in np.arange(-hw + 0.8, hw - 0.5, 1.3):
        parts.append(ext(rect(u - 0.4, h + 2.2, u + 0.4, h + 3.2), 0.69, 1.1))
    for s in (-1, 1):
        parts.append(chamfer_box(s * (hw - 0.4) - 0.8, -2.4, s * (hw - 0.4) + 0.8, -1.19, 0.0, 0.9, c=0.25, bottom=0.8))
    return O._one_piece(sash, parts, op, plug_cs, pl, h + 4.4, -2.4)


def window_office_upper(w=8.0, h=13.0):
    """The yard office's upper window: one over one in a casing whose head rises in a low
    shouldered gable, a plain sill."""
    op = O.opening_cs(w, h, 0)
    plug_cs = op.offset(-O.CLR, MJ, 4.0)
    pl = O.PLUG
    g = plug_cs.offset(-0.5, MJ, 4.0)
    sash = _glazed([ext(plug_cs, -pl, -0.6)], g, pl, rect(-w, h * 0.5 - 0.3, w, h * 0.5 + 0.3) ^ g, plug_cs)
    hw = w / 2 + 1.1
    head = poly([(-hw - 0.5, h), (hw + 0.5, h), (hw + 0.5, h + 1.4), (hw - 1.2, h + 1.4), (0.0, h + 3.0), (-hw + 1.2, h + 1.4), (-hw - 0.5, h + 1.4)])
    parts = [ext(op - op.offset(-RIB, MJ, 4.0), 0.0, 0.7), ext(op.offset(1.1, MJ, 4.0) - op, 0.0, 0.55),
             ext(head, 0.0, 0.9), ext(head - head.offset(-0.4, MJ, 4.0), 0.89, 1.2),
             chamfer_box(-hw - 0.3, -1.1, hw + 0.3, 0.2, 0.0, 1.0, c=0.3, bottom=0.8)]
    return O._one_piece(sash, parts, op, plug_cs, pl, h + 3.0, -1.1)


def door_yardoffice(w=10.0, h=24.0):
    """The yard office's door: a two-light window over two raised panels, a transom, a
    moulded casing under the same entablature cap as the lower windows."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, MJ, 4.0)
    pl = O.PLUG
    ht = h - 4.0
    body = [ext(plug_cs, -pl, -1.0), ext(plug_cs - plug_cs.offset(-0.5, MJ, 4.0), -pl, 0.0),
            ext(rect(-w / 2, 0.3, w / 2, ht) ^ plug_cs, -1.0, -0.6), ext(rect(-w / 2, ht, w / 2, ht + 0.7) ^ plug_cs, -pl, -0.6)]
    gl = rect(-w / 2 + 1.1, ht * 0.55, w / 2 - 1.1, ht - 1.0)
    for a, e in ((-w / 2 + 1.1, -0.35), (0.35, w / 2 - 1.1)):
        body.append(chamfer_box(a, 1.2, e, ht * 0.55 - 1.0, -0.6, 0.35, c=0.2))
    gb = gl.bounds()
    bars = rect((gb[0] + gb[2]) / 2 - 0.22, gb[1] - 1, (gb[0] + gb[2]) / 2 + 0.22, gb[3] + 1)
    tr = plug_cs.offset(-0.5, MJ, 4.0) ^ rect(-w, ht + 0.7, w, 999)
    sash = _glazed(body, gl + tr, pl, bars, plug_cs)
    hw = w / 2 + 1.2
    parts = [ext(op - op.offset(-RIB, MJ, 4.0), 0.0, 0.7), ext((op.offset(1.2, MJ, 4.0) - op) ^ rect(-w, 0.0, w, h + 1.2), 0.0, 0.55),
             ext(rect(-hw, h + 1.19, hw, h + 3.2), 0.0, 0.7),
             chamfer_box(-hw - 1.0, h + 3.19, hw + 1.0, h + 4.4, 0.0, 1.4, c=0.35, bottom=1.2)]
    for u in np.arange(-hw + 0.8, hw - 0.5, 1.3):
        parts.append(ext(rect(u - 0.4, h + 2.2, u + 0.4, h + 3.2), 0.69, 1.1))
    return O._one_piece(sash, parts, op, plug_cs, pl, h + 4.4, 0.0)


def lookout_yard(w=18.0, h0=3.0, hw=9.0, s=0.9, over=1.6):
    """The yardmaster's lookout, one piece printed upright: a plinth that sits on a flat seat
    at the top of the hip, one wide window each side (four lights, glazed), corner posts, a
    flared eave and a pyramid roof to a ball finial. Local: centred, z = 0 at its foot.
    Returns (lookout, glass zone)."""
    body = box([-w / 2, -w / 2, 0.0], [w / 2, w / 2, h0 + hw])
    zl0, zl1 = h0 + 1.2, h0 + hw - 1.2
    lights, glass, bars = [], [], []
    for (ax, sg) in ((0, -1), (0, 1), (1, -1), (1, 1)):
        a, e = sorted((sg * (w / 2 - 0.5), sg * (w / 2 + 0.1)))
        lo, hi = -w / 2 + 2.2, w / 2 - 2.2
        if ax == 0:
            lights.append(box([lo, a, zl0], [hi, e, zl1]))
            glass.append(box([lo, sg * (w / 2 - 0.5) - (0.35 if sg > 0 else 0.0) - 0.0, zl0], [hi, sg * (w / 2 - 0.5) + (0.35 if sg < 0 else 0.0), zl1]))
            for x in np.linspace(lo, hi, 5)[1:-1]:
                bars.append(box([x - 0.22, a, zl0], [x + 0.22, e + (0.2 if sg > 0 else 0.0) - (0.2 if sg < 0 else 0.0), zl1]))
            bars.append(box([lo - 0.6, min(a, e) - (0.5 if sg < 0 else 0.0), zl0 - 1.0], [hi + 0.6, max(a, e) + (0.5 if sg > 0 else 0.0), zl0 + 0.01]))
        else:
            lights.append(box([a, lo, zl0], [e, hi, zl1]))
            glass.append(box([sg * (w / 2 - 0.5) - (0.35 if sg > 0 else 0.0), lo, zl0], [sg * (w / 2 - 0.5) + (0.35 if sg < 0 else 0.0), hi, zl1]))
            for y in np.linspace(lo, hi, 5)[1:-1]:
                bars.append(box([a, y - 0.22, zl0], [e + (0.2 if sg > 0 else 0.0) - (0.2 if sg < 0 else 0.0), y + 0.22, zl1]))
            bars.append(box([min(a, e) - (0.5 if sg < 0 else 0.0), lo - 0.6, zl0 - 1.0], [max(a, e) + (0.5 if sg > 0 else 0.0), hi + 0.6, zl0 + 0.01]))
    body = body - union(lights) + union(bars)
    zc = h0 + hw
    a = w / 2 + over
    eave = M.hull_points([(x * w / 2, y * w / 2, zc - 0.01) for x in (-1, 1) for y in (-1, 1)] +
                         [(x * a, y * a, zc + over) for x in (-1, 1) for y in (-1, 1)])
    pyr = M.hull_points([(x * a, y * a, zc + over - 0.01) for x in (-1, 1) for y in (-1, 1)] + [(0.0, 0.0, zc + over + s * a)])
    zt = zc + over + s * a
    fin = M.cylinder(2.4, 0.5, 0.35, 12).translate([0, 0, zt - 0.8]) + M.sphere(1.0, 14).translate([0, 0, zt + 2.2])
    return body + eave + pyr + fin, union(glass)


def sign_yard(text, L, H=5.0, t=1.0, cap=3.0):
    """The yard office's name board: rounded ends, a bead, raised letters (facade frame, centred
    on u = 0, foot at v = 0). Returns (board, letters)."""
    from .storefront import text_cs
    r = H / 2
    b = cs_union([rect(-L / 2 + r, 0.0, L / 2 - r, H), circle((-L / 2 + r, r), r, 24), circle((L / 2 - r, r), r, 24)])
    board = ext(b, 0.0, t) + ext(b - b.offset(-0.55, RND), t - 0.01, t + 0.4)
    letters = text_cs(text, cap=cap, font="serif", track=0.5)
    lb = letters.bounds()
    sc = min(1.0, (L - 2 * r - 1.0) / max(1e-6, lb[2] - lb[0]))
    letters = letters.scale((sc, 1.0)).translate(((-(lb[0] + lb[2]) / 2) * sc, (H - cap) / 2 - lb[1]))
    lt = ext(letters, t - 0.01, t + 0.45)
    return board + lt, lt


def chimney_yard(w=6.4, d=6.4, h=14.0):
    """The yard office's stove chimney: a brick shaft with a sunk panel in each face, a band of
    projecting headers, a corbelled cap with a flat stone. Local: centred, z = 0 at its seat."""
    h = round(h / 0.2) * 0.2
    zt = h - 2.6
    body = box([-w / 2, -d / 2, 0.0], [w / 2, d / 2, zt])
    panels = union([box([-w / 2 + 1.0, -d / 2 - 1, 2.0], [w / 2 - 1.0, -d / 2 + 0.35, zt - 3.0]),
                    box([-w / 2 + 1.0, d / 2 - 0.35, 2.0], [w / 2 - 1.0, d / 2 + 1, zt - 3.0]),
                    box([-w / 2 - 1, -d / 2 + 1.0, 2.0], [-w / 2 + 0.35, d / 2 - 1.0, zt - 3.0]),
                    box([w / 2 - 0.35, -d / 2 + 1.0, 2.0], [w / 2 + 1, d / 2 - 1.0, zt - 3.0])])
    body = body - panels
    band = union([box([u - 0.25, -d / 2 - 0.35, zt - 2.2], [u + 0.25, d / 2 + 0.35, zt - 1.6]) for u in np.arange(-w / 2 + 0.4, w / 2, 0.8)] +
                 [box([-w / 2 - 0.35, v - 0.25, zt - 2.2], [w / 2 + 0.35, v + 0.25, zt - 1.6]) for v in np.arange(-d / 2 + 0.4, d / 2, 0.8)])
    z = zt
    for k in range(2):
        g = 0.35 * (k + 1)
        body = body + box([-w / 2 - g, -d / 2 - g, z - 0.01], [w / 2 + g, d / 2 + g, z + 0.6])
        z += 0.6
    body = body + chamfer_box(-w / 2 - 1.0, -d / 2 - 1.0, w / 2 + 1.0, d / 2 + 1.0, z - 0.01, 1.4, c=0.5)
    return body + band - M.cylinder(10.0, 0.9, 0.9, 16).translate([0, 0, z + 0.4])


def stoop_yard(w=12.0, rise=4.0, n=2, run=2.6, t=0.9):
    """Wooden steps to the office door: plank treads on notched stringers, open risers between.
    Local: u across (centred), v up (0 at the ground), w out from the wall (back at 0)."""
    r = rise / n
    out = []
    for k in range(n):
        top = rise - k * r
        out.append(box([-w / 2, k * run - 0.01, top - t], [w / 2, (k + 1) * run + 0.4, top]))
        out.append(box([-w / 2 + 0.4, (k + 1) * run - 0.2, top - r - 0.01], [w / 2 - 0.4, (k + 1) * run + 0.4, top - t + 0.01]))
    for s in (-1, 1):
        out.append(M.hull_points([(s * (w / 2 - 0.6) + dx, y, z) for dx in (-0.6, 0.6) for (y, z) in ((0.0, 0.0), (0.0, rise), (n * run + 0.4, 0.0), (0.4, rise))]))
    grooves = union([box([u - 0.15, -1, rise - 5], [u + 0.15, n * run + 2, rise + 1]) for u in np.arange(-w / 2 + 1.5, w / 2, 1.5)])
    m = union(out) - grooves
    return m.transform(np.array([[1.0, 0, 0, 0], [0, 0, 1.0, 0], [0, 1.0, 0, 0]]))


# ================================================================== 76 Section House No. 4 (tool house and speeder shed)
def reverse_batten(region, datum=0.0, pitch=3.0, gap=0.9):
    """Reverse board and batten: wide boards standing proud with narrow recessed boards between
    them (Section House No. 4)."""
    if region.is_empty():
        return M()
    b = region.bounds()
    out = M.extrude(region, 0.15)
    boards = cs_union([rect(u + gap / 2, b[1] - 1, u + pitch - gap / 2, b[3] + 1) for u in np.arange(b[0] - pitch, b[2] + pitch, pitch)])
    return out + ext(boards ^ region, 0.14, 0.55)


def foundation_sillblocks(reg, seed=0):
    """A timber sill on stone blocks: a heavy sill along the top, squared stones under it every
    8 mm with the dark crawl space between (Section House No. 4)."""
    b = reg.bounds()
    out = M.extrude(reg, 0.05)
    sill = rect(b[0] - 1, b[3] - 1.3, b[2] + 1, b[3] + 1) ^ reg
    blocks = cs_union([rect(u - 2.0, b[1] - 1, u + 2.0, b[3] - 1.29) for u in np.arange(b[0] + 2.0, b[2] - 1.0, 8.0)] +
                      [rect(b[2] - 4.0, b[1] - 1, b[2] + 1, b[3] - 1.29)]) ^ reg
    return out + ext(sill, 0.0, 0.7) + ext(blocks, 0.0, 0.8)


def course_spikes(L, h, b, pitch, margin, p):
    """A row of track spikes, heads up, on a tie-plate strip (Section House No. 4)."""
    strip = rect(0.3, 0.2, L - 0.3, 0.6)
    sp = cs_union([cs_union([rect(u - 0.22, 0.55, u + 0.22, h - 0.7), rect(u - 0.5, h - 0.75, u + 0.35, h - 0.25)])
                   for u in np.arange(1.0, L - 0.6, 1.6)])
    return [ext(strip, b - 0.05, b + 0.3), ext(sp, b - 0.05, b + 0.45)]


def frieze_trackgang(L, h, b, pitch, margin, pair, half):
    """A section gang's tools: at every station a lining bar and a spike maul crossed over a
    tie, a rail between (Section House No. 4)."""
    v0, v1 = 0.6, h - 0.6
    hh = v1 - v0
    out = [_st(rect(0.3, v0, L - 0.3, v0 + 0.45), b, 0.25)]
    for u in CO._us(L, pitch, margin, 0.0):
        tie = rect(u - 1.8, v0 + 0.3, u + 1.8, v0 + 0.9)
        bar = stroke([(u - hh * 0.55, v0 + 0.8), (u + hh * 0.55, v1 - 0.2)], 0.42, caps=False)
        maul = stroke([(u + hh * 0.5, v0 + 0.8), (u - hh * 0.35, v1 - 0.8)], 0.42, caps=False)
        head = poly([(u - hh * 0.35 - 1.0, v1 - 0.5), (u - hh * 0.35 + 0.5, v1 - 0.1), (u - hh * 0.35 + 0.9, v1 - 1.0), (u - hh * 0.35 - 0.6, v1 - 1.4)])
        out.append(_st(cs_union([tie, bar, maul, head]) ^ rect(0.0, v0, L, v1), b + 0.25, 0.35))
    return out, []


CO.FRIEZE_EXTRA.update(trackgang=frieze_trackgang)
CO.COURSE_EXTRA.update(spikes=course_spikes)
TW.FOUNDATION_EXTRA.update(sillblocks=foundation_sillblocks)


def door_toolhouse(w=9.0, h=19.0):
    """The tool house door: boards on a Z brace, strap hinges, a hasp and staple, in a plank
    casing under a drip board."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, MJ, 4.0)
    pl = O.PLUG
    leaf = plug_cs.offset(-0.3, MJ, 4.0)
    lb = leaf.bounds()
    grooves = cs_union([rect(u - 0.2, -1, u + 0.2, h + 1) for u in np.arange(lb[0] + 1.5, lb[2], 1.5)]) ^ leaf
    body = [ext(plug_cs, -pl, -1.0), ext(plug_cs - plug_cs.offset(-0.5, MJ, 4.0), -pl, 0.0), ext(leaf, -1.0, -0.6) - ext(grooves, -0.85, -0.5)]
    q0, q1 = lb[1] + 1.4, lb[3] - 1.4
    body.append(ext(cs_union([rect(lb[0] + 0.4, q0 - 0.5, lb[2] - 0.4, q0 + 0.5), rect(lb[0] + 0.4, q1 - 0.5, lb[2] - 0.4, q1 + 0.5),
                              stroke([(lb[0] + 0.9, q0 + 0.4), (lb[2] - 0.9, q1 - 0.4)], 0.95, caps=False)]), -0.61, -0.25))
    body.append(ext(cs_union([_strap_hinge(lb[0] + 0.3, lb[0] + 5.0, v) for v in (q0, q1)]), -0.26, -0.05))
    body.append(ext(rect(lb[2] - 1.6, h * 0.48 - 0.5, lb[2] - 0.4, h * 0.48 + 0.5), -0.61, -0.1))
    parts = [ext(op - op.offset(-RIB, MJ, 4.0), 0.0, 0.7), ext((op.offset(1.2, MJ, 4.0) - op) ^ rect(-w, 0.0, w, h + 1.2), 0.0, 0.6),
             chamfer_box(-w / 2 - 1.8, h + 1.19, w / 2 + 1.8, h + 2.0, 0.0, 1.3, c=0.3, bottom=1.0)]
    return O._one_piece(body, parts, op, plug_cs, pl, h + 2.0, 0.0)


def door_speeder(w=16.0, h=18.0):
    """The speeder shed's doors: a pair of boarded leaves, each braced with a K of ledges and a
    brace, strap hinges, under a plank head."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, MJ, 4.0)
    pl = O.PLUG
    lb = plug_cs.offset(-0.3, MJ, 4.0).bounds()
    body = [ext(plug_cs, -pl, -1.0), ext(plug_cs - plug_cs.offset(-0.5, MJ, 4.0), -pl, 0.0)]
    for (a, e, sg) in ((lb[0], -0.15, 1), (0.15, lb[2], -1)):
        leaf = rect(a, lb[1], e, lb[3])
        grooves = cs_union([rect(u - 0.2, -1, u + 0.2, h + 1) for u in np.arange(a + 1.5, e, 1.5)]) ^ leaf
        body.append(ext(leaf, -1.0, -0.6) - ext(grooves, -0.85, -0.5))
        q0, qm, q1 = lb[1] + 1.2, (lb[1] + lb[3]) / 2, lb[3] - 1.2
        hu = a if sg > 0 else e
        body.append(ext(cs_union([rect(a + 0.3, q - 0.45, e - 0.3, q + 0.45) for q in (q0, qm, q1)] +
                                 [stroke([(hu + sg * 0.8, q0 + 0.4), (hu + sg * (e - a - 0.8), qm - 0.4)], 0.8, caps=False),
                                  stroke([(hu + sg * 0.8, qm + 0.4), (hu + sg * (e - a - 0.8), q1 - 0.4)], 0.8, caps=False)]) ^ leaf, -0.61, -0.25))
        body.append(ext(cs_union([_strap_hinge(hu + sg * 0.3, hu + sg * 5.0, v) for v in (q0, q1)]), -0.26, -0.05))
    parts = [ext(op - op.offset(-RIB, MJ, 4.0), 0.0, 0.7), ext((op.offset(1.2, MJ, 4.0) - op) ^ rect(-w, 0.0, w, h + 1.2), 0.0, 0.6),
             chamfer_box(-w / 2 - 2.0, h + 1.19, w / 2 + 2.0, h + 2.4, 0.0, 1.3, c=0.35, bottom=1.0)]
    return O._one_piece(body, parts, op, plug_cs, pl, h + 2.4, 0.0)


def window_section(w=7.0, h=9.0):
    """The section house's window: six lights (three over three) in a plain casing with
    square corner blocks at the head, a sill."""
    op = O.opening_cs(w, h, 0)
    plug_cs = op.offset(-O.CLR, MJ, 4.0)
    pl = O.PLUG
    g = plug_cs.offset(-0.5, MJ, 4.0)
    sash = _glazed([ext(plug_cs, -pl, -0.6)], g, pl, _muntins(g, 3, 2, 0.4), plug_cs)
    parts = [ext(op - op.offset(-RIB, MJ, 4.0), 0.0, 0.7), ext(op.offset(1.1, MJ, 4.0) - op, 0.0, 0.55),
             chamfer_box(-w / 2 - 1.1, h - 0.01, -w / 2 + 0.01, h + 1.1, 0.0, 0.9, c=0.25),
             chamfer_box(w / 2 - 0.01, h - 0.01, w / 2 + 1.1, h + 1.1, 0.0, 0.9, c=0.25),
             chamfer_box(-w / 2 - 1.5, -1.1, w / 2 + 1.5, 0.2, 0.0, 1.1, c=0.3, bottom=0.8)]
    return O._one_piece(sash, parts, op, plug_cs, pl, h + 1.1, -1.1)


def stovepipe_section(h=14.0, r=1.1):
    """The tool house stove's pipe: a round pipe with a collar and a cone cap on three legs'
    worth of solid web. Local: centred, z = 0 inside the roof (it drops into a hole)."""
    pipe = M.cylinder(h, r, r, 24)
    collar = M.cylinder(1.0, r + 1.1, r + 0.4, 24).translate([0, 0, 4.0]) + \
        M.cylinder(1.1, r - 0.01, r + 1.1, 24).translate([0, 0, 2.9])           # 45-degree skirt: no flat ledge to print
    cap = M.cylinder(0.9, r + 0.1, r + 1.4, 24).translate([0, 0, h + 0.8]) + M.cylinder(0.9, r + 1.4, 0.3, 24).translate([0, 0, h + 1.69])
    web = box([-0.3, -r - 0.2, h - 0.01], [0.3, r + 0.2, h + 0.81])
    return pipe + collar + cap + web


# ================================================================== 77 the Crossing Shanty and Oil House
def shanty_diag(region, datum=0.0, rail=8.0, pitch=1.3):
    """The shanty's walls: a wainscot of boards laid on the diagonal up to a rail at ``rail``,
    narrow level boards above it (the Crossing Shanty)."""
    if region.is_empty():
        return M()
    b = region.bounds()
    lo = region ^ rect(b[0] - 1, b[1] - 1, b[2] + 1, datum + rail - 0.6)
    hi = region ^ rect(b[0] - 1, datum + rail + 0.6, b[2] + 1, b[3] + 1)
    out = M.extrude(region, 0.3)
    if not lo.is_empty():
        diag = cs_union([stroke([(u, b[1] - 2), (u + 30.0, b[1] + 28.0)], 0.3, caps=False) for u in np.arange(b[0] - 30.0, b[2] + 2.0, pitch * 1.4)])
        out = out - ext(diag ^ lo, 0.12, 1.0)
    if not hi.is_empty():
        gr = cs_union([rect(b[0] - 1, v - 0.14, b[2] + 1, v + 0.14) for v in np.arange(datum + rail + 0.6 + pitch, b[3], pitch)])
        out = out - ext(gr ^ hi, 0.12, 1.0)
    out = out + _st(rect(b[0] - 1, datum + rail - 0.6, b[2] + 1, datum + rail + 0.6) ^ region, 0.25, 0.5)
    return out


def brick_dogtooth(region, datum=0.0, dog=None):
    """Running bond with a dogtooth course (bricks set corner-out in a row of teeth) at ``dog``
    (v) (the Oil House)."""
    if region.is_empty():
        return M()
    b = region.bounds()
    bh = 0.8
    bricks = []
    for k in range(int(math.floor((b[1] - datum) / bh)) - 1, int(math.ceil((b[3] - datum) / bh)) + 1):
        v = datum + k * bh
        if dog is not None and dog - 0.1 < v + bh / 2 < dog + 1.7:
            continue
        off = 0.0 if k % 2 == 0 else 1.2
        bricks += [rect(u + 0.1, v + 0.1, u + 2.3, v + bh - 0.1) for u in np.arange(b[0] - 2.4 + off, b[2] + 2.4, 2.4)]
    out = M.extrude(region, 0.1) + ext(cs_union(bricks) ^ region, 0.09, 0.35)
    if dog is not None:
        teeth = cs_union([poly([(u, dog), (u + 1.0, dog), (u + 0.5, dog + 1.5)]) for u in np.arange(b[0] - 1.0, b[2] + 1.0, 1.0)]) ^ region
        out = out + _st(teeth, 0.05, 0.5)
    return out


def foundation_tiecrib(reg, seed=0):
    """A crib of old crossties: the ends of ties laid log-cabin fashion, alternate courses
    showing their ends and their sides (the Crossing Shanty)."""
    b = reg.bounds()
    out = M.extrude(reg, 0.1)
    rows = []
    for k, v in enumerate(np.arange(b[1], b[3] - 0.3, 2.0)):
        if k % 2:
            rows.append(rect(b[0] - 1, v + 0.1, b[2] + 1, v + 1.9))
        else:
            rows += [rect(u - 1.3, v + 0.1, u + 1.3, v + 1.9) for u in np.arange(b[0] + 1.3, b[2], 3.2)]
    return out + ext(cs_union(rows) ^ reg, 0.05, 0.6)


def foundation_granitesill(reg, seed=0):
    """One course of long granite sills, their joints every 12 mm, a chamfered top edge (the Oil
    House)."""
    b = reg.bounds()
    out = M.extrude(reg, 0.2)
    for u in np.arange(b[0], b[2], 12.0):
        r = rect(u + 0.15, b[1] + 0.1, min(u + 12.0, b[2]) - 0.15, b[3] - 0.1) ^ reg
        if not r.is_empty():
            bb = r.bounds()
            out = out + chamfer_box(bb[0], bb[1], bb[2], bb[3], 0.15, 0.6, c=0.35)
    return out


def frieze_oilcans(L, h, b, pitch, margin, pair, half):
    """Oil cans: at every station a can with a bail and a long spout, a shelf rail under them
    (the Oil House)."""
    v0, v1 = 0.6, h - 0.6
    hh = v1 - v0
    out = [_st(rect(0.3, v0, L - 0.3, v0 + 0.5), b, 0.25)]
    for u in CO._us(L, pitch, margin, 0.0):
        can = rect(u - 1.0, v0 + 0.45, u + 1.0, v0 + hh * 0.62)
        top = poly([(u - 1.0, v0 + hh * 0.62), (u + 1.0, v0 + hh * 0.62), (u + 0.4, v0 + hh * 0.78), (u - 0.4, v0 + hh * 0.78)])
        spout = stroke([(u + 0.3, v0 + hh * 0.74), (u + 2.1, v1 - 0.2)], 0.42, caps=False)
        bail = (circle((u - 0.2, v0 + hh * 0.7), hh * 0.22, 20) - circle((u - 0.2, v0 + hh * 0.7), hh * 0.22 - 0.42, 20)) ^ rect(u - 5, v0 + hh * 0.7, u + 5, v1)
        out.append(_st(cs_union([can, top, spout, bail]) ^ rect(0.0, v0, L, v1), b + 0.25, 0.4))
    return out, []


def course_signalwire(L, h, b, pitch, margin, p):
    """A crossing bell's wire: a line carried on little pulleys every 3 mm (the Crossing
    Shanty)."""
    vc = h / 2
    wire = rect(0.3, vc - 0.2, L - 0.3, vc + 0.2)
    wheels = cs_union([circle((u, vc), min(0.6, h * 0.36), 14) for u in np.arange(1.4, L - 1.0, 3.0)])
    return [ext(wire, b - 0.05, b + 0.25), ext(wheels, b - 0.05, b + 0.42) - ext(cs_union([circle((u, vc), 0.2, 8) for u in np.arange(1.4, L - 1.0, 3.0)]), b + 0.25, b + 1.0)]


CO.FRIEZE_EXTRA.update(oilcans=frieze_oilcans)
CO.COURSE_EXTRA.update(signalwire=course_signalwire)
TW.FOUNDATION_EXTRA.update(tiecrib=foundation_tiecrib, granitesill=foundation_granitesill)


def window_shanty(w=7.0, h=11.0):
    """The shanty's window: two over two, big for the watchman's view, in a casing with a
    sloped head board on two little brackets."""
    op = O.opening_cs(w, h, 0)
    plug_cs = op.offset(-O.CLR, MJ, 4.0)
    pl = O.PLUG
    g = plug_cs.offset(-0.5, MJ, 4.0)
    sash = _glazed([ext(plug_cs, -pl, -0.6)], g, pl, _muntins(g, 2, 2, 0.42), plug_cs)
    hw = w / 2 + 1.0
    parts = [ext(op - op.offset(-RIB, MJ, 4.0), 0.0, 0.7), ext(op.offset(1.0, MJ, 4.0) - op, 0.0, 0.55),
             ext(rect(-hw - 0.6, h + 0.99, hw + 0.6, h + 1.7), 0.0, 1.5),
             chamfer_box(-hw, -1.0, hw, 0.2, 0.0, 1.0, c=0.3, bottom=0.8)]
    for s in (-1, 1):
        parts.append(ext(poly([(s * (hw - 0.8), h + 1.0), (s * (hw + 0.2), h + 1.0), (s * (hw - 0.8), h - 0.8)]), 0.0, 1.2))
    return O._one_piece(sash, parts, op, plug_cs, pl, h + 1.7, -1.0)


def door_shanty(w=7.0, h=18.0):
    """The shanty's door: four lights over a panel, a plain casing."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, MJ, 4.0)
    pl = O.PLUG
    body = [ext(plug_cs, -pl, -1.0), ext(plug_cs - plug_cs.offset(-0.5, MJ, 4.0), -pl, 0.0),
            ext(plug_cs.offset(-0.3, MJ, 4.0), -1.0, -0.6)]
    lb = plug_cs.offset(-0.3, MJ, 4.0).bounds()
    gl = rect(lb[0] + 0.9, h * 0.5, lb[2] - 0.9, lb[3] - 0.9)
    body.append(chamfer_box(lb[0] + 0.9, 1.0, lb[2] - 0.9, h * 0.5 - 0.9, -0.6, 0.35, c=0.2))
    gb = gl.bounds()
    bars = cs_union([rect((gb[0] + gb[2]) / 2 - 0.22, gb[1] - 1, (gb[0] + gb[2]) / 2 + 0.22, gb[3] + 1),
                     rect(gb[0] - 1, (gb[1] + gb[3]) / 2 - 0.22, gb[2] + 1, (gb[1] + gb[3]) / 2 + 0.22)])
    sash = _glazed(body, gl, pl, bars, plug_cs)
    parts = [ext(op - op.offset(-RIB, MJ, 4.0), 0.0, 0.7), ext((op.offset(1.0, MJ, 4.0) - op) ^ rect(-w, 0.0, w, h + 1.0), 0.0, 0.55),
             chamfer_box(-w / 2 - 1.4, h + 0.99, w / 2 + 1.4, h + 1.8, 0.0, 1.1, c=0.3, bottom=0.9)]
    return O._one_piece(sash, parts, op, plug_cs, pl, h + 1.8, 0.0)


def door_oilhouse(w=8.0, h=17.0):
    """The oil house's fire door: sheet iron over boards, riveted round its edges and crossed
    by iron straps, heavy strap hinges, in a stone frame with a lintel."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, MJ, 4.0)
    pl = O.PLUG
    leaf = plug_cs.offset(-0.3, MJ, 4.0)
    lb = leaf.bounds()
    body = [ext(plug_cs, -pl, -1.0), ext(plug_cs - plug_cs.offset(-0.5, MJ, 4.0), -pl, 0.0), ext(leaf, -1.0, -0.6)]
    straps = cs_union([stroke([(lb[0] + 0.6, lb[1] + 0.6), (lb[2] - 0.6, lb[3] - 0.6)], 0.8, caps=False),
                       stroke([(lb[2] - 0.6, lb[1] + 0.6), (lb[0] + 0.6, lb[3] - 0.6)], 0.8, caps=False),
                       leaf - leaf.offset(-0.7, MJ, 4.0)]) ^ leaf
    body.append(ext(straps, -0.61, -0.3))
    riv = cs_union([circle((u, v), 0.25, 8) for u in np.linspace(lb[0] + 0.35, lb[2] - 0.35, 7) for v in (lb[1] + 0.35, lb[3] - 0.35)] +
                   [circle((u, v), 0.25, 8) for v in np.linspace(lb[1] + 1.4, lb[3] - 1.4, 9) for u in (lb[0] + 0.35, lb[2] - 0.35)])
    body.append(ext(riv, -0.31, -0.1))
    body.append(ext(cs_union([_strap_hinge(lb[0] + 0.3, lb[0] + 5.0, v) for v in (lb[1] + 2.5, lb[3] - 2.5)]), -0.31, -0.1))
    parts = [ext(op - op.offset(-RIB, MJ, 4.0), 0.0, 0.7), ext((op.offset(1.4, MJ, 4.0) - op) ^ rect(-w, 0.0, w, h), 0.0, 0.7),
             chamfer_box(-w / 2 - 1.8, h - 0.01, w / 2 + 1.8, h + 2.6, 0.0, 1.2, c=0.35, bottom=1.0)]
    return O._one_piece(body, parts, op, plug_cs, pl, h + 2.6, 0.0)


def vent_oilhouse(w=6.0, h=4.0):
    """The oil house's vent: iron bars over a louvre in a stone frame (an insert, glazed dark
    behind for the renders)."""
    op = O.opening_cs(w, h, 0)
    plug_cs = op.offset(-O.CLR, MJ, 4.0)
    pl = O.PLUG
    g = plug_cs.offset(-0.4, MJ, 4.0)
    gb = g.bounds()
    bars = cs_union([rect(u - 0.22, gb[1] - 1, u + 0.22, gb[3] + 1) for u in np.linspace(gb[0], gb[2], 6)[1:-1]])
    sash = _glazed([ext(plug_cs, -pl, -0.6)], g, pl, bars, plug_cs)
    parts = [ext(op - op.offset(-RIB, MJ, 4.0), 0.0, 0.7), ext(op.offset(1.3, MJ, 4.0) - op, 0.0, 0.7)]
    return O._one_piece(sash, parts, op, plug_cs, pl, h + 1.3, -1.3)


def stovepipe_shanty(h=12.0, r=0.9):
    """The shanty stove's pipe: a pipe with a round bonnet cap over a spark screen. Local:
    centred, z = 0 inside the roof (it drops into a hole)."""
    pipe = M.cylinder(h, r, r, 20)
    screen = M.cylinder(1.6, r + 0.5, r + 0.5, 20).translate([0, 0, h - 0.01]) + M.cylinder(0.5, r - 0.01, r + 0.5, 20).translate([0, 0, h - 0.5])
    bonnet = M.cylinder(0.8, r + 0.5, r + 1.3, 24).translate([0, 0, h + 1.58]) + \
        (M.sphere(r + 1.3, 24).scale([1, 1, 0.5]).translate([0, 0, h + 2.37]) ^ box([-9, -9, h + 2.37], [9, 9, h + 9]))
    collar = M.cylinder(0.8, r + 0.9, r + 0.3, 20).translate([0, 0, 3.0]) + M.cylinder(0.9, r - 0.01, r + 0.9, 20).translate([0, 0, 2.1])
    return pipe + screen + bonnet + collar                  # every flare at 45 degrees: nothing flat to print over


def crossbuck(h=40.0, arm=17.0, bw=2.4, t=0.9):
    """A crossbuck on its post, printed flat on its back: the two boards crossed at right angles
    with a raised rim, the post, and a foot plate at its base (standing out behind, it lies on
    the ground and takes the glue). Local: x across, y up (the foot at 0), z out of its face."""
    post = box([-0.9, 0.0, 0.0], [0.9, h, 1.6])
    cy = h - arm * 0.36 - 1.5
    boards = []
    for a in (45.0, -45.0):
        r_ = math.radians(a)
        c, s = math.cos(r_), math.sin(r_)
        pts = [(x * c - y * s, cy + x * s + y * c) for (x, y) in ((-arm / 2, -bw / 2), (arm / 2, -bw / 2), (arm / 2, bw / 2), (-arm / 2, bw / 2))]
        bd = poly(pts)
        boards.append(ext(bd, 0.0, 1.6 + t) + ext(bd - bd.offset(-0.45, MJ, 4.0), 1.6 + t - 0.01, 1.6 + t + 0.3))   # solid to the back: the arms print on the bed
    foot = box([-3.5, 0.0, 0.0], [3.5, 1.2, 6.0])
    cap = box([-1.2, h - 0.01, 0.0], [1.2, h + 0.8, 1.8])
    return post + union(boards) + foot + cap


# ================================================================== 78 the Kiln Ridge Tunnel Portals (double track, brick)
def brick_flemish(region, datum=0.0):
    """Flemish bond, a stretcher and a header in turn along every course, the headers (burnt
    dark) standing a little prouder so the bond reads as a checker (the Kiln Ridge portals).
    Relief on w = 0, prints face up."""
    if region.is_empty():
        return M()
    b = region.bounds()
    bh = 0.9
    st, hd = [], []
    for k in range(int(math.floor((b[1] - datum) / bh)) - 1, int(math.ceil((b[3] - datum) / bh)) + 1):
        v = datum + k * bh
        u = b[0] - 3.6 + (1.8 if k % 2 else 0.0)
        while u < b[2] + 3.6:
            st.append(rect(u + 0.12, v + 0.12, u + 2.4 - 0.12, v + bh - 0.12))
            hd.append(rect(u + 2.4 + 0.12, v + 0.12, u + 3.6 - 0.12, v + bh - 0.12))
            u += 3.6
    return (ext(region, -0.01, 0.12) + ext(cs_union(st) ^ region, 0.11, 0.5) + ext(cs_union(hd) ^ region, 0.11, 0.7))


def _ring_bricks(cy, R0, R1, a0, a1, n):
    out = []
    for j in range(n):
        t0 = a0 + (a1 - a0) * j / n + 0.01
        t1 = a0 + (a1 - a0) * (j + 1) / n - 0.01
        out.append(poly([(R0 * math.sin(t0), cy + R0 * math.cos(t0)), (R1 * math.sin(t0), cy + R1 * math.cos(t0)),
                         (R1 * math.sin(t1), cy + R1 * math.cos(t1)), (R0 * math.sin(t1), cy + R0 * math.cos(t1))]))
    return out


def portal_brick(W=180.0, H=100.0, ow=112.0, spring=50.0, rise=30.0, T=4.0, label="No 7"):
    """A double-track tunnel portal in brick with stone dressings, one piece printed face up:
    Flemish bond on a stone base course; the segmental arch in three rowlock rings stepping back
    from the opening, stone springers and a tall keystone lettered with the tunnel's number; a
    stone impost band across the face at the springing; stone quoins on the end piers; a
    corbelled brick cornice under a stone coping; a stepped parapet over the arch with a stone
    roundel. Local: u across (centred), v up, w out of the face (the back at w = -T). Returns
    (portal, opening outline, letters)."""
    from .storefront import text_cs
    hw = W / 2
    opening = O.opening_cs(ow, spring + rise, rise)
    half = ow / 2
    Rr = (half * half + rise * rise) / (2 * rise)
    cy = spring + rise - Rr
    a0 = math.asin(half / Rr)
    steps = [(-hw + 30.0, H + 5.0), (-44.0, H + 10.0), (44.0, H + 5.0), (hw - 30.0, H)]
    par = cs_union([rect(-hw + 30.0, H - 0.1, hw - 30.0, H + 5.0), rect(-44.0, H - 0.1, 44.0, H + 10.0), rect(-18.0, H - 0.1, 18.0, H + 15.0)])
    outline = cs_union([rect(-hw, 0.0, hw, H), par])
    parts = [ext(outline - opening, -T, 0.0)]
    # arch rings, springers, keystone
    ring_zone = cs_union([(circle((0.0, cy), Rr + 7.6, 160) - circle((0.0, cy), Rr, 160)) ^ rect(-hw, spring - 0.5, hw, H)])
    for k, (r0, r1, d, n) in enumerate(((Rr + 0.15, Rr + 2.5, 0.95, 44), (Rr + 2.6, Rr + 5.0, 0.85, 48), (Rr + 5.1, Rr + 7.5, 0.75, 52))):
        band = poly([(r0 * math.sin(t), cy + r0 * math.cos(t)) for t in np.linspace(-a0, a0, 60)] +
                    [(r1 * math.sin(t), cy + r1 * math.cos(t)) for t in np.linspace(a0, -a0, 60)])
        parts.append(ext(band, -0.01, d * 0.5))
        parts += [ext(bk, d * 0.5 - 0.01, d) for bk in _ring_bricks(cy, r0, r1, -a0, a0, n)]
    key = poly([(-3.4, cy + Rr - 0.3), (3.4, cy + Rr - 0.3), (4.6, cy + Rr + 11.0), (-4.6, cy + Rr + 11.0)])
    parts.append(_dressed(key, 0.0, 2.6, 0.5))
    letters = text_cs(label, cap=2.8, font="serif", track=0.3)
    lb = letters.bounds()
    sc = min(1.0, 6.6 / max(1e-6, lb[2] - lb[0]))
    letters = letters.scale((sc, 1.0)).translate((-(lb[0] + lb[2]) / 2 * sc, cy + Rr + 4.2 - (lb[1] + lb[3]) / 2))
    lt = ext(letters, 2.59, 3.1)
    parts.append(lt)
    for s in (-1, 1):
        a, e = sorted((s * (half - 0.2), s * (half + 9.0)))
        parts.append(_dressed(rect(a, spring - 6.0, e, spring), 0.0, 2.0, 0.5))
    # stone impost band, base course, quoins, cornice
    imp = (rect(-hw, spring - 2.4, hw, spring + 0.6) - rect(-half - 9.2, -1, half + 9.2, 999))
    parts.append(_dressed(imp, 0.0, 1.5, 0.45) if imp.to_polygons() and len(imp.to_polygons()) == 1 else
                 union([_dressed(poly(p), 0.0, 1.5, 0.45) for p in imp.to_polygons()]))
    base = rect(-hw, 0.0, hw, 6.0) - opening
    for p in base.to_polygons():
        bb = poly(p).bounds()
        for u in np.arange(bb[0], bb[2], 14.0):
            r = rect(u + 0.2, 0.2, min(u + 14.0, bb[2]) - 0.2, 5.8)
            if not (r ^ base).is_empty():
                q = (r ^ base).bounds()
                parts.append(chamfer_box(q[0], q[1], q[2], q[3], -0.01, 1.4, c=0.4))
    quo = []
    for s in (-1, 1):
        for j, v in enumerate(np.arange(6.0, H - 10.0, 5.4)):
            L = 9.0 if j % 2 == 0 else 5.5
            a, e = sorted((s * hw, s * (hw - L)))
            q = rect(a + (0.2 if s < 0 else 0.0), v + 0.2, e - (0.2 if s > 0 else 0.0), min(v + 5.4, H - 10.0) - 0.2)
            quo.append(rect(a, v, e, min(v + 5.4, H - 10.0)))
            parts.append(_dressed(q, 0.0, 1.6, 0.4))
    for u in np.arange(-hw + 1.2, hw - 0.5, 2.4):                   # the corbel table's dentils
        parts.append(ext(rect(u - 0.7, H - 10.0, u + 0.7, H - 8.4), -0.01, 1.2))
    parts.append(ext(rect(-hw, H - 8.4, hw, H - 6.6), -0.01, 1.6))
    parts.append(ext(rect(-hw, H - 6.6, hw, H - 4.8), -0.01, 2.0))
    parts.append(_dressed(rect(-hw, H - 4.8, hw, H), 0.0, 2.6, 0.9))
    for (x0, x1, top) in ((-hw + 30.0, hw - 30.0, H + 5.0), (-44.0, 44.0, H + 10.0), (-18.0, 18.0, H + 15.0)):
        parts.append(_dressed(rect(x0, top - 2.2, x1, top), 0.0, 2.2, 0.7))
    rc = (0.0, H + 7.4)
    parts.append(_dressed(poly([(rc[0] + 4.6 * math.cos(t), rc[1] + 4.6 * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 40, endpoint=False)]), 0.0, 1.4, 0.4))
    parts.append(ext(circle(rc, 3.2, 40) - circle(rc, 2.6, 40), 1.39, 1.8))
    field = outline - opening - ring_zone - rect(-hw - 1, -1, hw + 1, 6.0) - imp - cs_union(quo) - rect(-hw - 1, H - 10.0, hw + 1, H + 0.01) \
        - rect(-half - 9.2, spring - 6.2, half + 9.2, spring + 0.2) - key.offset(0.3, MJ, 4.0)
    for (x0, x1, top) in ((-hw + 30.0, hw - 30.0, H + 5.0), (-44.0, 44.0, H + 10.0), (-18.0, 18.0, H + 15.0)):
        field = field - rect(x0, top - 2.2, x1, top + 1)
    field = field - circle(rc, 4.9, 40)
    parts.append(brick_flemish(field, datum=6.0))
    return union(parts), opening, lt


def liner_brick(opening, depth=30.0, t=2.4):
    """The brick lining behind a double-track portal: the barrel ``depth`` long, its inner face
    coursed in brick (joints along the tunnel and staggered joints across). Prints on end."""
    ring = (opening.offset(t, MJ, 4.0) - opening) ^ rect(-400, 0.0, 400, 400)
    inner = (opening.offset(0.35, MJ, 4.0) - opening) ^ rect(-400, 0.0, 400, 400)
    body = ext(ring, -depth, 0.0)
    b = opening.bounds()
    joints = []
    for v in np.arange(1.8, b[3], 1.8):
        joints.append(ext(rect(-400, v - 0.22, 400, v + 0.22) ^ inner, -depth - 1, 1))
    cross = union([ext(inner, -w - 0.22, -w + 0.22) for w in np.arange(3.6, depth - 1.0, 3.6)])
    return body - union(joints) - cross


def wing_brick(Lw=70.0, h0=86.0, T=4.0, side=1, back=6.0):
    """A stepped wing wall in brick: Flemish bond on the stone base course, the top stepping
    down in three stages each with a stone coping, a quoined end pier with a cap. Local as
    wing_stone: u along the wall away from the portal (toward ``side`` * u), v up, w out of the
    face; it starts ``back`` short of u = 0 to be cut square to the portal's side."""
    s = float(side)

    def S(cs):
        return cs.transform(np.array([[s, 0.0, 0.0], [0.0, 1.0, 0.0]])) if s < 0 else cs

    stages = [(-back, Lw * 0.36, h0), (Lw * 0.36, Lw * 0.68, h0 * 0.68), (Lw * 0.68, Lw - 9.0, h0 * 0.4)]
    outline = cs_union([rect(a, 0.0, e, top) for (a, e, top) in stages] + [rect(Lw - 9.0, 0.0, Lw, h0 * 0.4 + 5.0)])
    parts = [ext(S(outline), -T, 0.0)]
    for u in np.arange(-back, Lw, 14.0):
        r = rect(u + 0.2, 0.2, min(u + 14.0, Lw) - 0.2, 5.8)
        bb = S(r).bounds()
        parts.append(chamfer_box(bb[0], bb[1], bb[2], bb[3], -0.01, 1.4, c=0.4))
    cops = []
    for (a, e, top) in stages:
        c = rect(a, top - 2.2, e + (0.0 if e < Lw - 9.0 else 0.0), top)
        cops.append(c)
        bb = S(c).bounds()
        parts.append(_dressed(S(c), 0.0, 2.2, 0.7))
    pier = rect(Lw - 9.0, 6.0, Lw, h0 * 0.4 + 2.8)
    quo = []
    for j, v in enumerate(np.arange(6.0, h0 * 0.4 + 2.8, 5.4)):
        L = 9.0 if j % 2 == 0 else 5.5
        q = rect(Lw - L, v, Lw, min(v + 5.4, h0 * 0.4 + 2.8))
        quo.append(q)
        bb = S(q.offset(-0.2, MJ, 4.0)).bounds()
        parts.append(chamfer_box(bb[0], bb[1], bb[2], bb[3], -0.01, 1.6, c=0.4))
    capr = rect(Lw - 9.0, h0 * 0.4 + 2.8, Lw, h0 * 0.4 + 5.0)
    bb = S(capr).bounds()
    parts.append(chamfer_box(bb[0], bb[1], bb[2], bb[3], -0.01, 2.6, c=0.9))
    field = outline - rect(-back - 1, -1, Lw + 1, 6.0) - cs_union(cops) - cs_union(quo) - capr - (pier ^ rect(Lw - 9.0, 0, Lw, 999))
    parts.append(brick_flemish(S(field), datum=6.0))
    return union(parts)


# ================================================================== 79 the Mill Creek Bridge (abutments, pier, girder spans)
def _panels(face_cs, inset=2.0, pw=12.0, gap=2.4, depth=0.6, c=0.5):
    """Recessed chamfered panels filling a face outline (u, v): returns the cutter solid (to
    subtract, in w 0..depth into the face from w = 0 going negative)."""
    b = face_cs.bounds()
    inner = face_cs.offset(-inset, MJ, 4.0)
    if inner.is_empty():
        return M()
    ib = inner.bounds()
    n = max(1, int(round((ib[2] - ib[0] + gap) / (pw + gap))))
    w_ = (ib[2] - ib[0] - (n - 1) * gap) / n
    cuts = []
    for k in range(n):
        u0 = ib[0] + k * (w_ + gap)
        r = rect(u0, ib[1], u0 + w_, ib[3]) ^ inner
        if r.is_empty():
            continue
        rs = r.offset(-c, MJ, 4.0)
        cuts.append(M.hull_points([(p[0], p[1], 0.01) for loop in r.to_polygons() for p in loop] +
                                  [(p[0], p[1], -depth) for loop in (rs.to_polygons() if not rs.is_empty() else r.to_polygons()) for p in loop]))
    return union(cuts)


def abutment_concrete(W=48.0, z_seat=40.0, z_top=60.0, seat=8.0, back=6.0, wing=45.0, wt=6.0, splay=30.0, z_end=22.0,
                      pads=(-10.0, 10.0), date="1908"):
    """A concrete bridge abutment, one piece printed upright: the breast wall to the bridge
    seat with three recessed chamfered panels, a coping under the seat, bearing pads for the
    girders, the backwall rising behind the seat with the date cast in a plate, splayed wing
    walls sloping down to capped ends with panels and a coping, a projecting footing. Local: x
    across (centred), y back into the bank (the breast's face at y = 0, facing -y), z up."""
    from .storefront import text_cs
    hw = W / 2
    out = [box([-hw, 0.0, 0.0], [hw, seat + back, z_seat]), box([-hw, seat, z_seat - 0.01], [hw, seat + back, z_top])]
    a = math.radians(splay)
    for s in (-1, 1):
        d = np.array([s * math.sin(a), math.cos(a)])
        n = np.array([d[1] * s, -d[0] * s])                  # outward normal of the wing's outer face
        p0 = np.array([s * hw, 0.0])
        q = [p0, p0 + d * wing, p0 + d * wing - n * wt, p0 - n * wt]
        body = M.hull_points([(p[0], p[1], z) for p in (q[0], q[3]) for z in (0.0, z_top)] +
                             [(p[0], p[1], z) for p in (q[1], q[2]) for z in (0.0, z_end)])
        A = np.array([[d[0], 0.0, n[0], p0[0]], [d[1], 0.0, n[1], p0[1]], [0.0, 1.0, 0.0, 0.0]])
        face = poly([(0.0, 5.0), (wing - 3.0, 5.0), (wing - 3.0, z_end - 3.0), (0.0, z_top - 3.0)])
        body = body - _panels(face, inset=2.4, pw=11.0, gap=2.4).transform(A)
        cop = M.hull_points([(p[0] + n[0] * 0.9, p[1] + n[1] * 0.9, z) for (p, zt) in ((q[0], z_top), (q[1], z_end)) for z in (zt - 0.3, zt + 1.6)] +
                            [(p[0] - n[0] * 0.3, p[1] - n[1] * 0.3, z) for (p, zt) in ((q[3], z_top), (q[2], z_end)) for z in (zt - 1.2, zt + 1.6)] +
                            [(p[0], p[1], zt - 1.2) for (p, zt) in ((q[0], z_top), (q[1], z_end))])
        endcap = M.hull_points([(p[0] + e_[0], p[1] + e_[1], z) for p in (q[1], q[2]) for e_ in ((0.0, 0.0), tuple(d * -4.0))
                                for z in (z_end - 0.01, z_end + 3.2)])
        out += [body, cop, endcap]
    m = union(out)
    # the breast's panels, its coping under the seat, the footing
    Ab = np.array([[1.0, 0.0, 0.0, 0.0], [0.0, 0.0, -1.0, 0.0], [0.0, 1.0, 0.0, 0.0]])
    m = m - _panels(rect(-hw, 5.0, hw, z_seat - 4.0), inset=2.2, pw=12.0).transform(Ab)
    cop = M.hull_points([(x, y, z) for x in (-hw - 0.1, hw + 0.1) for (y, z) in ((0.0, z_seat - 3.2), (-1.6, z_seat - 1.6), (-1.6, z_seat), (0.2, z_seat))])
    foot = M.hull_points([(x, y, z) for x in (-hw - 2.0, hw + 2.0) for (y, z) in ((-2.0, 0.0), (-2.0, 3.0), (0.0, 5.0), (seat + back, 0.0), (seat + back, 5.0))])
    pads = union([box([x - 3.5, 0.8, z_seat - 0.01], [x + 3.5, seat - 1.0, z_seat + 2.0]) for x in pads])
    # the date plate on the backwall's face (y = seat, facing -y)
    plate = box([-8.0, seat - 0.6, z_seat + 7.0], [8.0, seat + 0.01, z_seat + 14.0])
    letters = text_cs(date, cap=4.0, font="serif", track=0.5)
    lb = letters.bounds()
    Aw = np.array([[1.0, 0.0, 0.0, -(lb[0] + lb[2]) / 2], [0.0, 0.0, -1.0, seat - 0.59], [0.0, 1.0, 0.0, z_seat + 10.5 - (lb[1] + lb[3]) / 2]])
    lt = M.extrude(letters, 0.5).transform(Aw)
    return m + cop + foot + pads + plate + lt


def pier_concrete(L=44.0, t0=18.0, t1=14.0, h=36.0, nose=8.0, cap=4.0, pads=(-10.0, 10.0)):
    """A concrete bridge pier, one piece printed upright: a battered shaft with a pointed
    cutwater at each end, recessed panels on its long faces, a projecting coping cap with
    bearing pads for the spans each side, a footing. Local: centred, the spans running along y,
    z = 0 at the footing's foot."""
    def section(t, L_, nose_):
        return [(-L_ / 2 - nose_, 0.0), (-L_ / 2, -t / 2), (L_ / 2, -t / 2), (L_ / 2 + nose_, 0.0), (L_ / 2, t / 2), (-L_ / 2, t / 2)]
    body = M.hull_points([(x, y, 0.0) for (x, y) in section(t0, L, nose)] + [(x, y, h) for (x, y) in section(t1, L, nose * 0.8)])
    for sg in (-1, 1):
        A = np.array([[sg * 1.0, 0.0, 0.0, 0.0], [0.0, 0.0, 1.0 * sg, sg * (t0 / 2)], [0.0, 1.0, 0.0, 0.0]])
        # a panel set on each long face (cut a little deeper to allow for the batter)
        pcs = _panels(rect(-L / 2, 5.0, L / 2, h - 4.0), inset=2.6, pw=10.0, depth=0.6 + (t0 - t1) / 2 * 1.0)
        body = body - pcs.transform(np.array([[1.0, 0.0, 0.0, 0.0], [0.0, 0.0, -sg * 1.0, sg * (t0 / 2) - sg * (t0 - t1) / 2 * 0.5], [0.0, 1.0, 0.0, 0.0]]))
    capm = M.hull_points([(x, y, h - 0.01) for (x, y) in section(t1, L, nose * 0.8)] +
                         [(x * 1.0, y * 1.0, h + 1.6) for (x, y) in section(t1 + 3.2, L + 3.2, nose * 0.8)] +
                         [(x, y, h + cap) for (x, y) in section(t1 + 3.2, L + 3.2, nose * 0.8)])
    foot = M.hull_points([(x, y, 0.0) for (x, y) in section(t0 + 4.0, L + 4.0, nose + 1.0)] + [(x, y, 3.0) for (x, y) in section(t0 + 4.0, L + 4.0, nose + 1.0)] +
                         [(x, y, 4.6) for (x, y) in section(t0, L, nose)])
    pads_ = union([box([x - 3.5, sg * 0.8 - (6.0 if sg < 0 else 0.0), h + cap - 0.01], [x + 3.5, sg * 0.8 + (6.0 if sg > 0 else 0.0), h + cap + 2.0])
                   for x in pads for sg in (-1, 1)])
    return body + capm + foot + pads_


def span_girder(L=120.0, gx=10.0, depth=16.0, deck_w=36.0, deck_t=2.0, curb=3.0, fl=6.0, tw=1.2, stiff=10.0):
    """A ballasted deck plate-girder span, one piece printed upright on its bottom flanges: two
    riveted plate girders under a steel deck plate with ballast curbs, the flange angles filleted
    at 45 degrees along the webs, stiffener angles up the webs, the deck's overhang carried on
    45 degree outrigger brackets at every stiffener, and knee-braced diaphragms between the
    girders whose undersides rise at 45 degrees, so the only bridge is the deck plate between
    the top flanges. Local: centred on its length (along y), x across, z = 0 at the flanges' feet."""
    out = []
    ang = fl / 2 - tw / 2                                                                   # the flange angles' leg
    ys = [float(y) for y in np.arange(-L / 2 + 2.0, L / 2 - 1.0, stiff)]
    for s in (-1, 1):
        x = s * gx
        out.append(box([x - fl / 2, -L / 2, 0.0], [x + fl / 2, L / 2, 1.2]))                 # bottom flange
        out.append(M.hull_points([(x + dx, y, z) for y in (-L / 2, L / 2) for (dx, z) in ((-fl / 2, 1.19), (fl / 2, 1.19), (-tw / 2, 1.19 + ang), (tw / 2, 1.19 + ang))]))
        out.append(box([x - tw / 2, -L / 2, 1.0], [x + tw / 2, L / 2, depth]))              # web
        out.append(box([x - fl / 2, -L / 2, depth - 1.2], [x + fl / 2, L / 2, depth + 0.01]))  # top flange
        out.append(M.hull_points([(x + dx, y, z) for y in (-L / 2, L / 2) for (dx, z) in ((-fl / 2, depth - 1.19), (fl / 2, depth - 1.19), (-tw / 2, depth - 1.19 - ang), (tw / 2, depth - 1.19 - ang))]))
        for y in ys:
            for sx in (-1, 1):
                out.append(box([x + sx * tw / 2 - (0.9 if sx < 0 else 0.0), y - 0.45, 1.19], [x + sx * tw / 2 + (0.9 if sx > 0 else 0.0), y + 0.45, depth - 1.19]))
        xw, xe = x + s * (tw / 2 - 0.01), s * deck_w / 2                                    # outrigger brackets, web to deck edge
        run = abs(xe - xw)
        for y in ys + [-L / 2 + 0.45, L / 2 - 0.45]:
            out.append(M.hull_points([(u, y + dy, z) for dy in (-0.45, 0.45) for (u, z) in ((xw, depth - run), (xw, depth + 0.01), (xe, depth + 0.01))]))
        riv = [M.sphere(0.28, 8).translate([x + sx * (tw / 2 + 0.05), y, z]) for sx in (-1, 1)
               for y in np.arange(-L / 2 + 1.0, L / 2, 1.6) for z in (1.19 + ang + 0.6, depth - 1.19 - ang - 0.6)]
        out.append(union(riv))
    xi = gx - tw / 2 + 0.01                                                                 # the webs' inner faces
    for y in np.arange(-L / 2 + 6.0, L / 2 - 5.0, (L - 12.0) / 4):
        for sx in (-1, 1):
            out.append(M.hull_points([(sx * u, y + dy, z) for dy in (-0.6, 0.6) for (u, z) in ((xi, 3.0), (xi, depth + 0.01), (0.0, depth + 0.01), (0.0, 3.0 + xi))]))
    deck = box([-deck_w / 2, -L / 2, depth], [deck_w / 2, L / 2, depth + deck_t])
    for s in (-1, 1):
        out.append(box([s * deck_w / 2 - (1.4 if s > 0 else 0.0), -L / 2, depth + deck_t - 0.01], [s * deck_w / 2 + (1.4 if s < 0 else 0.0), L / 2, depth + deck_t + curb]))
    return union(out) + deck


# ================================================================== 80 the Beaver Run Trestle
def bent_timber(h=60.0, top=8.0, batter=0.12, post=2.2, cap=2.6, story=30.0, inner=4.5):
    """A four-post timber trestle bent, one piece printed flat on its face: two plumb posts
    under the stringers and two battered outer posts, a cap and a sill that run past them with
    bolt heads, X sway braces in every story, a sash girt between stories, the braces lying on
    the bed under the posts. Local: x across (centred), z up (the sill's foot at 0), y the
    member depth (0..post, braces 0..1.2)."""
    bot = top + h * batter
    L_sill, L_cap = bot + 3.0, top + 4.8                    # the cap runs under both stringer chords
    out = [box([-L_cap, 0.0, h - cap], [L_cap, post, h]), box([-L_sill, 0.0, 0.0], [L_sill, post, cap])]
    for x in (-inner, inner):
        out.append(box([x - post / 2, 0.0, cap - 0.01], [x + post / 2, post, h - cap + 0.01]))
    for s in (-1, 1):
        out.append(M.hull_points([(s * bot + dx, y, cap - 0.01) for dx in (-post / 2, post / 2) for y in (0.0, post)] +
                                 [(s * top + dx, y, h - cap + 0.01) for dx in (-post / 2, post / 2) for y in (0.0, post)]))
    n = max(1, int(math.ceil((h - 2 * cap) / story)))
    zs = [cap + (h - 2 * cap) * k / n for k in range(n + 1)]
    for k in range(n):
        za, zb = zs[k], zs[k + 1]
        xa, xb = bot + (top - bot) * (za / h), bot + (top - bot) * (zb / h)
        for (p0, p1) in (((-xa, za), (xb, zb)), ((xa, za), (-xb, zb))):
            out.append(M.hull_points([(p0[0], y, p0[1] + dz) for y in (0.0, 1.2) for dz in (0.0, 1.6)] +
                                     [(p1[0], y, p1[1] - dz) for y in (0.0, 1.2) for dz in (0.0, 1.6)]))
        if k > 0:
            out.append(box([-xa - post / 2, 0.0, za - 0.8], [xa + post / 2, 1.4, za + 0.8]))
    bolts = [M.cylinder(0.5, 0.35, 0.3, 8).rotate([-90, 0, 0]).translate([x, post, z]) for x in (-L_cap + 0.8, L_cap - 0.8, -inner, inner, -top, top)
             for z in (h - cap / 2,)] + [M.cylinder(0.5, 0.35, 0.3, 8).rotate([-90, 0, 0]).translate([x, post, cap / 2]) for x in (-L_sill + 0.8, L_sill - 0.8, -bot, bot)]
    return union(out) + union(bolts)


def deck_trestle(L=50.0, tie_w=2.6, tie_t=1.8, tie_l=30.0, pitch=4.0, str_w=1.8, str_h=3.2, guard=1.6):
    """One span of the trestle's open deck, one piece printed upright on its stringers: two
    chords of three stringers (one under each rail and one either side of it) on spacer blocks,
    ties across them every 4 mm (bridging only between the chords, and 2.8 mm past them), guard
    timbers along the tie ends. Local: centred on its length (along y), x across, z = 0 at the
    stringers' foot (they rest on the bents' caps)."""
    out = []
    for x in (-11.3, -8.5, -5.7, 5.7, 8.5, 11.3):
        out.append(box([x - str_w / 2, -L / 2, 0.0], [x + str_w / 2, L / 2, str_h]))
    for y in (-L / 2 + 3.0, 0.0, L / 2 - 3.0):
        for x in (-9.9, -7.1, 7.1, 9.9):
            out.append(box([x - 1.2, y - 1.0, 0.6], [x + 1.2, y + 1.0, str_h]))
    for y in np.arange(-L / 2 + pitch / 2, L / 2, pitch):
        out.append(box([-tie_l / 2, y - tie_w / 2, str_h - 0.01], [tie_l / 2, y + tie_w / 2, str_h + tie_t]))
    for s in (-1, 1):
        x = s * (tie_l / 2 - 2.2)
        out.append(box([x - guard / 2, -L / 2, str_h + tie_t - 0.01], [x + guard / 2, L / 2, str_h + tie_t + guard]))
    return union(out)


def bulkhead_timber(W=32.0, h=14.0, t=2.0, plank=1.8, cap=2.6):
    """The trestle's end bulkhead, one piece printed on its back: horizontal planks retaining
    the bank between three posts, a cap the stringers rest on, a sill. Local: x across
    (centred), z up (0 at the foot), y out of the face (back at 0)."""
    out = [box([-W / 2, 0.0, 0.0], [W / 2, t, h])]
    grooves = union([box([-W, t - 0.3, z - 0.18], [W, t + 1, z + 0.18]) for z in np.arange(plank, h - cap, plank)])
    out[0] = out[0] - grooves
    for x in (-W / 2 + 1.2, 0.0, W / 2 - 1.2):
        out.append(box([x - 1.1, t - 0.01, 0.0], [x + 1.1, t + 1.4, h - cap]))
    out.append(box([-W / 2 - 1.0, 0.0, h - cap], [W / 2 + 1.0, t + 2.2, h]))
    out.append(box([-W / 2 - 1.0, 0.0, 0.0], [W / 2 + 1.0, t + 2.2, 1.6]))
    return union(out)

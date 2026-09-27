"""Craftsman-era parts for the fifth batch (houses 51 to 60, 1900-1930): each house's own wall
skins, foundation facing, cornice ornament and rafter tails, knee braces, porch columns and
porch walls, window and door families and chimneys. Like ``colonial4``, the ornament registers
itself with ``cornice``, ``trimwork``, ``porchwork`` and ``features`` on import, and no part is
shared between two houses.

Frames follow ``openings``: local (u, v, w) with u = 0 at the opening centre, v = 0 at its
bottom, w = 0 on the wall face; a one-piece insert is a plug with the glass and sash plus the
surround, printed face-up with supports under the surround."""
import math

import numpy as np
from manifold3d import JoinType, Manifold as M

from .core import RIB, box, circle, cs_union, poly, rect, scallop_rows, union
from .ornament import chamfer_box, ext, oval, stepped, stroke
from . import cornice as CO, features as FT, openings as O, porchwork as PW, trimwork as TW
from .colonial import _lens, _st
from .colonial4 import _glazed, _muntins, _panel
from .skins import _lap


# ------------------------------------------------------------------ shared helpers (geometry, not parts)
def _hung(w, h, top=(3, 1), bot=(1, 1), n=1, mull=1.2, meet=0.6, bars_top=None):
    """A group of ``n`` double-hung sashes side by side in one plug (mullions between), each
    with ``top`` = (cols, rows) lights in its upper sash and ``bot`` in its lower. ``bars_top``:
    a function (cs) -> CrossSection of bars for the upper sash instead of a grid.
    Returns (sash parts, opening cs, plug cs)."""
    op = O.opening_cs(w, h, 0)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    inner = plug_cs.offset(-0.6, JoinType.Miter, 4.0)
    u0, v0, u1, v1 = inner.bounds()
    vm = v0 + (v1 - v0) * 0.52
    sw = (u1 - u0 - (n - 1) * mull) / n
    lights, bars = [], []
    for j in range(n):
        a = u0 + j * (sw + mull)
        lo, hi = rect(a, v0, a + sw, vm - meet / 2), rect(a, vm + meet / 2, a + sw, v1)
        lights += [lo, hi]
        bars.append(_muntins(lo, bot[0], bot[1]) ^ lo)
        bars.append((bars_top(hi) if bars_top else _muntins(hi, top[0], top[1])) ^ hi)
    g = cs_union(lights)
    body = [ext(plug_cs, -pl, -0.6)]
    sash = _glazed(body, g, pl, cs_union(bars), plug_cs)
    sash.append(ext(rect(u0, vm - meet / 2 - 0.01, u1, vm + meet / 2 + 0.01), -pl, -0.3))
    for j in range(1, n):
        a = u0 + j * (sw + mull) - mull
        sash.append(ext(rect(a - 0.01, v0, a + mull + 0.01, v1), -pl, -0.2))
    return sash, op, plug_cs


def knee_brace(L, t=1.0, arm=1.1, hole=True, peg=True):
    """A knee brace under a gable's rake: a post against the wall, an arm out under the rake
    and a diagonal strut, in the (v, w) plane, ``t`` thick across (u centred). Local: v up
    from the brace's foot, w out from the wall; the arm's top at v = L. Prints upright with
    its wall (the strut's underside at 45 degrees)."""
    outer = poly([(0.0, L - arm - L * 0.9), (0.0, L), (L, L), (L, L - arm)])
    tri = outer
    if hole:
        ins = poly([(arm, L - arm - L * 0.9 + 2.2 * arm), (arm, L - arm), (L - 2.2 * arm, L - arm)])
        if ins.area() > 1.0:
            tri = outer - ins
    body = M.extrude(tri, t).translate([0, 0, -t / 2])            # (w, v, u)
    out = body.transform(np.array([[0, 0, 1.0, 0], [0, 1.0, 0, 0], [1.0, 0, 0, 0]]))
    if peg:
        out = out + box([-t / 2 - 0.25, L - arm * 0.75, arm * 0.5], [t / 2 + 0.25, L - arm * 0.25, arm * 1.2])
    return out


# ================================================================== the Arroyo (house 51, a California bungalow)
# ------------------------------------------------------------------ skins and foundation
def lap_bungalow(region, datum=0.0, belt=None):
    """Wide bungalow siding (a bevelled lap of 1.9 mm) up to the belt, a belt board, and above
    it cedar shingles in random widths, every fourth course doubled (the Arroyo)."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    belt = v1 + 1 if belt is None else belt
    lo = region ^ rect(u0 - 1, v0 - 1, u1 + 1, belt)
    out = M.extrude(region, 0.05)
    if not lo.is_empty():
        out = out + _lap(lo, 1.9, [(0.0, 0.42), (0.5, 0.36), (1.9, 0.12)], datum=datum)
    hi = region ^ rect(u0 - 1, belt + 1.6, u1 + 1, v1 + 1)
    if not hi.is_empty():
        out = out + scallop_rows(hi, 1.8, 2.4, d=0.36, shape="doubled", datum=belt + 1.6)
    band = region ^ rect(u0 - 1, belt - 0.01, u1 + 1, belt + 1.61)
    if not band.is_empty():
        out = out + ext(band, 0.0, 0.55) + ext(region ^ rect(u0 - 1, belt + 1.2, u1 + 1, belt + 1.61), 0.54, 0.8)
    return out


def foundation_clinker(reg, seed=0):
    """Clinker brick: running bond in which every fourth or fifth brick is a clinker, burnt
    lumpy, standing proud and set a little askew; a rowlock course (bricks on edge) on top
    (the Arroyo)."""
    b = reg.bounds()
    rng = np.random.default_rng(seed + 71)
    top = b[3] - 1.2
    flat, clink = [], []
    bl, bh = 2.4, 0.8
    k = 0
    v = top - bh
    while v > b[1] - bh:
        u = b[0] - rng.uniform(0, bl) - (k % 2) * bl / 2
        while u < b[2] + bl:
            r = rect(u + 0.25, v, u + bl - 0.25, v + bh - 0.2)
            if rng.random() < 0.22:
                c = ((u + bl / 2), v + bh / 2)
                clink.append(r.translate((-c[0], -c[1])).rotate(float(rng.uniform(-9, 9))).scale((1.08, 1.12)).translate(c))
            else:
                flat.append(r)
            u += bl
        v -= bh
        k += 1
    body = M.extrude(reg, 0.1) + ext(cs_union(flat) ^ reg, 0.0, 0.25)
    if clink:
        body = body + stepped(cs_union(clink) ^ reg, [(0.0, 0.0, 0.3), (0.12, 0.3, 0.5)])
    rows = cs_union([rect(u + 0.12, top, u + 0.68, b[3] - 0.1) for u in np.arange(b[0], b[2], 0.8)]) ^ reg
    return body + ext(rect(b[0], top, b[2], b[3]) ^ reg, 0.0, 0.35) + ext(rows, 0.34, 0.6)


# ------------------------------------------------------------------ cornice ornament and rafter tails
def _ginkgo(c, s, ang):
    """A ginkgo leaf ``s`` long on its stem from c, pointing at ang: a fan split at the top."""
    x, y = c
    ca, sa = math.cos(ang), math.sin(ang)
    st = s * 0.35
    bx, by = x + ca * st, y + sa * st
    fan = [(bx, by)] + [(bx + s * 0.65 * math.cos(ang + a), by + s * 0.65 * math.sin(ang + a)) for a in np.linspace(-0.95, 0.95, 13)]
    leaf = poly(fan)
    notch = poly([(bx + s * 0.3 * ca, by + s * 0.3 * sa), (bx + s * 0.7 * math.cos(ang - 0.14), by + s * 0.7 * math.sin(ang - 0.14)),
                  (bx + s * 0.7 * math.cos(ang + 0.14), by + s * 0.7 * math.sin(ang + 0.14))])
    return (leaf - notch) + stroke([(x, y), (bx, by)], 0.35)


def frieze_ginkgo(L, h, b, pitch, margin, pair, half):
    """Ginkgo leaves: at every station a spray of three on their stems, and single leaves
    drifting in the bays between, tipped one way and the other."""
    v0, v1 = 0.7, h - 0.7
    hh = v1 - v0
    out = []
    s = hh * 0.95
    for u in CO._us(L, pitch, margin, 0.0):
        spray = cs_union([_ginkgo((u, v0 + 0.1), s, math.pi / 2 + da) for da in (-0.62, 0.0, 0.62)])
        out.append(_st(spray ^ rect(u - s, v0 - 0.2, u + s, v1 + 0.2), b, 0.5))
    for j, (uc, wd) in enumerate(CO._between(L, pitch, margin, pair, half + s * 0.8)):
        if wd < s:
            continue
        leaf = _ginkgo((uc - 0.8, v0 + hh * 0.2), s * 0.85, math.pi / 2 + (0.7 if j % 2 else -0.7))
        out.append(_st(leaf ^ rect(uc - wd / 2, v0 - 0.2, uc + wd / 2, v1 + 0.2), b, 0.45))
    return out, []


def course_pegs(L, h, b, pitch, margin, p):
    """Greene and Greene pegs: small square peg heads in pairs along a plain band."""
    out = []
    for u in np.arange(1.4, L - 1.0, 3.0):
        for du in (-0.55, 0.55):
            out.append(rect(u + du - 0.35, h / 2 - 0.35, u + du + 0.35, h / 2 + 0.35))
    return [ext(cs_union(out) ^ rect(0.2, 0.0, L - 0.2, h), b - 0.05, b + 0.5)]


def bracket_cloudlift(h, d, t):
    """An exposed rafter tail cut with two cloud lifts: its underside steps up twice, each step
    rounded, as it runs out to a squared end (side profile, top at v = 0)."""
    hb = min(h, max(1.8, 0.3 * d))
    pts = [(0.0, 0.0), (d, 0.0), (d, -hb * 0.45)]
    for (xa, xb, za, zb) in ((d * 0.78, d * 0.7, -hb * 0.45, -hb * 0.72), (d * 0.45, d * 0.37, -hb * 0.72, -hb)):
        pts.append((xa, za))
        for s in np.linspace(0.0, 1.0, 5)[1:]:
            pts.append((xa - (xa - xb) * s, za + (zb - za) * (0.5 - 0.5 * math.cos(math.pi * s))))
    pts.append((0.0, -hb))
    return poly(pts)


CO.FRIEZE_EXTRA.update(ginkgo=frieze_ginkgo)
CO.COURSE_EXTRA.update(pegs=course_pegs)
TW.BRACKET_EXTRA.update(cloudlift=bracket_cloudlift)
TW.FOUNDATION_EXTRA.update(clinker=foundation_clinker)


# ------------------------------------------------------------------ windows and doors
def _eared_head(hw, v, drop=0.0):
    """A Craftsman head casing: a board over the side casings with ears past them each side,
    under a drip cap."""
    parts = [ext(rect(-hw - 0.8, v - 0.01, hw + 0.8, v + 1.9), 0.0, 0.7)]
    parts.append(chamfer_box(-hw - 1.1, v + 1.89, hw + 1.1, v + 2.5, 0.0, 1.0, c=0.3, bottom=0.6))
    return parts


def window_eared41(w, h, n=1, A=1.1):
    """An Arroyo window: four-over-one sashes (four tall lights in the upper sash, one below),
    ``n`` side by side, in flat casings under an eared head casing with a drip cap; a thick
    sill over a plain apron."""
    sash, op, plug_cs = _hung(w, h, top=(4, 1), bot=(1, 1), n=n)
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS),
             ext((op.offset(A, JoinType.Miter, 4.0) - op) ^ rect(-w, 0.0, w, h + A), 0.0, 0.6)]
    hw = w / 2 + A
    parts += _eared_head(hw, h + A - 0.3)
    parts.append(chamfer_box(-hw - 0.7, -1.2, hw + 0.7, 0.2, 0.0, 1.2, c=0.35, bottom=0.8))
    parts.append(ext(rect(-hw + 0.3, -3.0, hw - 0.3, -1.19), 0.0, 0.5))
    return O._one_piece(sash, parts, op, plug_cs, O.PLUG, h + A + 2.2, -3.0)


def door_arroyo(w, h, side=2.6, A=1.2):
    """The Arroyo's door: a slab door of three tall panels under a shelf on little dentils and
    a row of four lights, between sidelights (a long light over a panel), in flat casings
    under a head casing cut beneath in a cloud lift."""
    W_ = w + 2 * side
    op = rect(-W_ / 2, 0.0, W_ / 2, h)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    body = [ext(plug_cs, -pl, -1.0)]
    u0, u1 = -w / 2 + 0.2, w / 2 - 0.2
    body.append(ext(rect(u0, 0.5, u1, h - 0.3), -1.0, -0.8))
    pw = (u1 - u0 - 2.0) / 3
    for j in range(3):
        a = u0 + 0.5 + j * (pw + 0.5)
        body.append(_panel(rect(a, 1.0, a + pw, h * 0.66)))
    vs = h * 0.66 + 0.8
    body.append(chamfer_box(u0 + 0.3, vs - 0.2, u1 - 0.3, vs + 0.5, -0.81, 0.5, c=0.2))
    for x in np.linspace(u0 + 1.0, u1 - 1.0, 5):
        body.append(ext(rect(x - 0.25, vs - 0.7, x + 0.25, vs - 0.2), -0.81, -0.45))
    lw = (u1 - u0 - 1.0 - 3 * 0.5) / 4
    glass = [rect(u0 + 0.5 + j * (lw + 0.5), vs + 0.9, u0 + 0.5 + j * (lw + 0.5) + lw, h - 1.2) for j in range(4)]
    for sg in (-1, 1):
        a, e = sorted((sg * (w / 2 + 0.3), sg * (W_ / 2 - O.CLR - 0.4)))
        glass.append(rect(a, h * 0.36, e, h - 0.8))
        body.append(chamfer_box(a, 0.8, e, h * 0.36 - 0.4, -1.0, 0.4, c=0.2))
    sash = _glazed(body, cs_union(glass), pl, None, plug_cs)
    sash.append(ext(cs_union([rect(-w / 2 - 0.3, 0.3, -w / 2 + 0.2, h), rect(w / 2 - 0.2, 0.3, w / 2 + 0.3, h)]) ^ plug_cs, -pl, -0.4))
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS),
             ext((op.offset(A, JoinType.Miter, 4.0) - op) ^ rect(-W_, 0.0, W_, h + A), 0.0, 0.7)]
    hw = W_ / 2 + A
    head = rect(-hw - 1.0, h + A - 0.3, hw + 1.0, h + A + 2.2)
    lift = cs_union([rect(-hw + 1.6, h + A - 0.5, hw - 1.6, h + A + 0.3)])
    parts.append(ext(head - lift, 0.0, 0.8) + ext(rect(-hw + 1.6, h + A + 0.29, hw - 1.6, h + A + 2.2), 0.0, 0.8))
    parts.append(chamfer_box(-hw - 1.3, h + A + 2.19, hw + 1.3, h + A + 2.8, 0.0, 1.1, c=0.3, bottom=0.6))
    return O._one_piece(sash, parts, op, plug_cs, pl, h + A + 2.8, 0.0)


def attic_vent(w, h, A=1.0):
    """A louvred attic vent for a gable: slanted slats in a frame under an eared head (the
    Arroyo). An insert like a window, printed face-up."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    inner = plug_cs.offset(-0.6, JoinType.Miter, 4.0)
    u0, v0, u1, v1 = inner.bounds()
    body = [ext(plug_cs, -pl, -pl + 0.8), ext(plug_cs - inner, -pl, 0.05)]
    slats = []
    for v in np.arange(v0 + 0.3, v1 - 1.0, 1.1):
        slats.append(M.hull_points([(u0 - 0.1, v, -pl + 0.79), (u1 + 0.1, v, -pl + 0.79), (u0 - 0.1, v + 0.9, -0.6),
                                    (u1 + 0.1, v + 0.9, -0.6), (u0 - 0.1, v + 0.5, -pl + 0.79), (u1 + 0.1, v + 0.5, -pl + 0.79)]))
    body.append(union(slats) ^ ext(inner.offset(0.1, JoinType.Miter, 4.0), -pl, 0.0))
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS),
             ext((op.offset(A, JoinType.Miter, 4.0) - op) ^ rect(-w, 0.0, w, h + A), 0.0, 0.6)]
    parts += _eared_head(w / 2 + A, h + A - 0.3)
    parts.append(chamfer_box(-w / 2 - A - 0.5, -0.9, w / 2 + A + 0.5, 0.2, 0.0, 1.0, c=0.3, bottom=0.6))
    return O._one_piece(body, parts, op, plug_cs, pl, h + A + 2.2, -0.9)


# ------------------------------------------------------------------ the porch
def post_arroyo(h, collar=None, abacus=3.2, slot=None):
    """An Arroyo porch column: a round shaft tapering hard as it rises (battered), standing on
    a tall square pedestal with a bevelled cap, under a square capital block."""
    ped = min(11.0, h * 0.42)
    zt = h - 2.2
    body = PW._plinth(3.6) + box([-1.7, -1.7, 1.19], [1.7, 1.7, ped - 0.8])
    body = body + M.hull_points([(x * 1.7, y * 1.7, ped - 0.81) for x in (-1, 1) for y in (-1, 1)] +
                                [(x * 2.0, y * 2.0, ped - 0.3) for x in (-1, 1) for y in (-1, 1)])
    body = body + box([-2.0, -2.0, ped - 0.31], [2.0, 2.0, ped])
    body = body + PW._revolve([(0.0, ped - 0.01), (1.55, ped - 0.01), (1.12, zt), (0.0, zt)], 32)
    body = body + box([-1.25, -1.25, zt - 0.4], [1.25, 1.25, zt + 0.4])
    return body + PW._top(h, abacus / 2, zt + 0.39, 1.25, slot, shape="square")


def fill_lapwall(L, vb, vt):
    """A solid porch wall faced in lap siding (grooves at every course) between the rails."""
    H = vt - vb
    board = rect(0.0, vb, L, vt)
    grooves = cs_union([rect(-1, v - 0.25, L + 1, v + 0.25) for v in np.arange(vb + 1.9, vt - 0.8, 1.9)])
    return [board - grooves + cs_union([rect(0.0, v - 0.3, L, v + 0.3) for v in np.arange(vb + 1.9, vt - 0.8, 1.9 * 3)])] if H > 2 else [board]


def frieze_cloudbeam(u0, u1, v_bot, v_top):
    """A porch beam: a deep plain board with a cloud-lift corbel under each end of every bay."""
    v0 = v_top - 2.4
    beam = rect(u0, v0, u1, v_top + 0.05)
    L = u1 - u0
    c = min(3.2, L * 0.2)
    corb = [poly([(u0, v0 + 0.01), (u0 + c, v0 + 0.01), (u0 + c, v0 - 0.4), (u0 + c * 0.55, v0 - 0.4), (u0 + c * 0.55, v0 - 1.1),
                  (u0, v0 - 1.1)]),
            poly([(u1, v0 + 0.01), (u1 - c, v0 + 0.01), (u1 - c, v0 - 0.4), (u1 - c * 0.55, v0 - 0.4), (u1 - c * 0.55, v0 - 1.1),
                  (u1, v0 - 1.1)])]
    return beam + cs_union(corb)


def edge_rafters(L, z0, zc):
    """Porch fascia (the Arroyo): exposed rafter ends under the roof's edge."""
    xs = np.arange(1.0, L - 0.6, 2.2)
    return cs_union([rect(x - 0.4, zc - 1.6, x + 0.4, zc) for x in xs]) + rect(0.3, zc - 0.5, L - 0.3, zc), 0.8


def skirt_riverstone(reg, d=1.2):
    """A porch skirt of river stones: rounded cobbles of mixed sizes, set in deep mortar."""
    if reg.is_empty():
        return M()
    u0, v0, u1, v1 = reg.bounds()
    rng = np.random.default_rng(int(abs(u0) * 13 + abs(v0) * 7) % 997)
    stones = []
    for _ in range(int((u1 - u0) * (v1 - v0) / 1.6) + 1):
        c = (rng.uniform(u0, u1), rng.uniform(v0, v1))
        stones.append(oval(c, rng.uniform(0.6, 1.1), rng.uniform(0.45, 0.8), 14))
    s = cs_union(stones) ^ reg
    return M.extrude(reg, d * 0.45) + stepped(s, [(0.0, d * 0.44, d * 0.8), (0.18, d * 0.8, d)])


PW.POSTS.update(arroyo=post_arroyo)
PW.FILLS.update(lapwall=fill_lapwall)
PW.FRIEZES.update(cloudbeam=frieze_cloudbeam)
PW.SKIRTS.update(riverstone=skirt_riverstone)
FT.EDGE_EXTRA.update(rafters=edge_rafters)


# ------------------------------------------------------------------ the chimney
def chimney_arroyo(w=16.0, d=8.0, h=110.0, zb=20.0, zr=80.0):
    """The Arroyo's outside chimney: river stones from the ground in a battered base, stepping
    in at a sloped weathering at ``zb``, the stack in river stone up past the eave and clinker
    brick above ``zr`` to a corbelled cap and a clay pot. Local: x across the wall, y out from
    the wall (the back face on y = 0), z up from the ground."""
    h = round(h / 0.2) * 0.2
    rng = np.random.default_rng(5)

    def stones(reg, i):
        u0, v0, u1, v1 = reg.bounds()
        ss = [oval((rng.uniform(u0, u1), rng.uniform(v0, v1)), rng.uniform(0.7, 1.3), rng.uniform(0.5, 0.9), 14)
              for _ in range(int((u1 - u0) * (v1 - v0) / 1.8) + 1)]
        return stepped(cs_union(ss) ^ reg, [(0.0, 0.0, 0.3), (0.2, 0.3, 0.5)])

    W2, D2 = w + 4.0, d + 2.0
    base = box([-W2 / 2, 0.0, 0.0], [W2 / 2, D2, zb])
    base = base + TW._skin(W2, D2, 0.2, zb - 0.2, stones).translate([0, D2 / 2, 0]) - box([-W2, -5, -1], [W2, 0.0, zb + 1])
    wea = M.hull_points([(x * W2 / 2, y, zb - 0.01) for x in (-1, 1) for y in (0.0, D2)] +
                        [(x * w / 2, y, zb + 2.0) for x in (-1, 1) for y in (0.0, d)])
    stack = box([-w / 2, 0.0, zb], [w / 2, d, h - 3.0])
    skin = TW._skin(w, d, zb + 2.2, zr, stones).translate([0, d / 2, 0]) + TW._skin(w, d, zr, h - 3.2, TW._brick("running")).translate([0, d / 2, 0])
    body = base + wea + stack + (skin - box([-w, -5, 0], [w, 0.0, h + 5]))
    z = h - 3.0
    for k in range(2):
        g = 0.25 * (k + 1)
        body = body + box([-w / 2 - g, -0.0, z - 0.01], [w / 2 + g, d + g, z + 0.6])
        z += 0.6
    body = body + box([-w / 2 - 0.7, 0.0, z - 0.01], [w / 2 + 0.7, d + 0.7, z + 0.8])
    z += 0.8
    pot = M.cylinder(2.4, 1.1, 0.9, 24).translate([w * 0.22, d / 2, z - 0.01]) - M.cylinder(4, 0.55, 0.55, 16).translate([w * 0.22, d / 2, z - 1])
    flues = box([-w / 2 + 1.6, 1.6, h - 5.0], [-0.6, d - 1.6, h + 5])
    return body + pot - flues


# ================================================================== the Hollister (house 52, an American Foursquare)
# ------------------------------------------------------------------ skins and foundation
def clapboard_flared(region, datum=0.0):
    """Narrow clapboards (1.5 mm to the weather) run round mitred corners with no corner
    boards, the bottom course flared out over the foundation (the Hollister)."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    out = M.extrude(region, 0.05) + _lap(region, 1.5, [(0.0, 0.34), (1.5, 0.08)], datum=datum)
    flare = region ^ rect(u0 - 1, datum - 1, u1 + 1, datum + 1.4)
    if not flare.is_empty():
        out = out + stepped(flare, [(0.0, 0.0, 0.5), (0.0, 0.5, 0.7)]) + ext(region ^ rect(u0 - 1, datum - 1, u1 + 1, datum + 0.5), 0.69, 0.9)
    return out


def shingles_alternate(region, datum=0.0, seed=3):
    """Cedar shingles laid to two exposures in turn, a wide course (2.4 mm) then a narrow one
    (1.1 mm), random widths, so the wall reads in bands (the Hollister)."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    rng = np.random.default_rng(seed)
    out = M.extrude(region, 0.05)
    v, k = datum - 3.5 * math.ceil((datum - v0) / 3.5 + 1), 0
    rows = []
    while v < v1:
        ex = 2.4 if k % 2 == 0 else 1.1
        u = u0 - rng.uniform(0, 2.5)
        tabs = []
        while u < u1 + 2:
            wv = rng.uniform(1.8, 3.2)
            tabs.append(rect(u + 0.25, v, u + wv - 0.25, v + ex + 0.9))
            u += wv
        rows.append(ext(cs_union(tabs) ^ region ^ rect(u0 - 1, v, u1 + 1, v + ex), 0.0, 0.4 if k % 2 == 0 else 0.28))
        v += ex
        k += 1
    return out + union(rows)


def foundation_rockblock(reg, seed=0):
    """Rock-faced concrete block, the kind cast on a block machine in the 1910s: long blocks in
    running bond, each with a smooth margin round a rough 'rock' face of chipped facets
    (the Hollister)."""
    b = reg.bounds()
    rng = np.random.default_rng(seed + 83)
    top = b[3] - 1.0
    blocks, rock = [], []
    bl, bh = 6.4, 3.2
    v, k = top, 0
    while v > b[1] - bh:
        u = b[0] - (k % 2) * bl / 2
        while u < b[2] + bl:
            blocks.append(rect(u + 0.25, v - bh + 0.25, u + bl - 0.25, v - 0.25))
            fb = (u + 0.8, v - bh + 0.8, u + bl - 0.8, v - 0.8)
            for _ in range(7):
                cx, cy = rng.uniform(fb[0], fb[2]), rng.uniform(fb[1], fb[3])
                rock.append(poly([(cx + r * math.cos(a), cy + r * 0.8 * math.sin(a)) for a, r in
                                  zip(np.sort(rng.uniform(0, 2 * math.pi, 5)), rng.uniform(0.5, 1.1, 5))]))
            u += bl
        v -= bh
        k += 1
    cs = cs_union(blocks) ^ reg
    faces = cs.offset(-0.55, JoinType.Miter, 4.0)
    body = M.extrude(reg, 0.1) + ext(cs, 0.0, 0.3) + ext(faces, 0.29, 0.45)
    if rock:
        body = body + ext(cs_union(rock) ^ faces, 0.44, 0.7)
    return body + chamfer_box(b[0], top, b[2], b[3], 0.0, 0.7, c=0.25, square=("u0", "u1"), bottom=0.7)


# ------------------------------------------------------------------ cornice ornament
def _dragonfly(c, s, ang=0.0):
    """A dragonfly ``s`` long, wings spread: a long body with a round head and two pairs of
    lens-shaped wings."""
    x, y = c
    ca, sa = math.cos(ang), math.sin(ang)
    P_ = lambda a, b: (x + a * ca - b * sa, y + a * sa + b * ca)
    body = stroke([P_(-s * 0.5, 0), P_(s * 0.35, 0)], 0.4) + circle(P_(s * 0.42, 0), 0.38, 12)
    wings = []
    for dx, sl, sg in ((s * 0.2, 0.62, 1), (s * 0.2, 0.62, -1), (s * 0.02, 0.55, 1), (s * 0.02, 0.55, -1)):
        wa = ang + sg * (math.pi / 2 - (0.25 if dx > s * 0.1 else -0.15))
        wx, wy = P_(dx, 0)
        wl = s * sl
        wings.append(_lens((wx + wl / 2 * math.cos(wa), wy + wl / 2 * math.sin(wa)), wl, wl * 0.3, wa))
    return body + cs_union(wings)


def frieze_dragonflies(L, h, b, pitch, margin, pair, half):
    """Dragonflies with their wings spread at the stations, and between them a line of
    waterline reeds (three stalks, the middle one tallest)."""
    v0, v1 = 0.7, h - 0.7
    hh = v1 - v0
    vm = (v0 + v1) / 2
    out = []
    s = min(hh * 1.1, 4.8)
    for j, u in enumerate(CO._us(L, pitch, margin, 0.0)):
        out.append(_st(_dragonfly((u, vm), s, 0.12 if j % 2 else -0.12) ^ rect(u - s, v0 - 0.2, u + s, v1 + 0.2), b, 0.45))
    for uc, wd in CO._between(L, pitch, margin, pair, half + s * 0.7):
        if wd < 3.0:
            continue
        reeds = cs_union([stroke([(uc + dx, v0), (uc + dx * 1.3, v0 + hh * f)], 0.4) for dx, f in ((-0.8, 0.6), (0.0, 0.95), (0.8, 0.7))])
        out.append(_st(reeds, b, 0.4))
    return out, []


def course_rings(L, h, b, pitch, margin, p):
    """A course of small raised rings, touching, the length of the band."""
    r = min(0.62, h / 2 - 0.08)
    n = int((L - 1.0) / (2 * r + 0.25))
    u0 = (L - (n - 1) * (2 * r + 0.25)) / 2
    rings = [circle((u0 + k * (2 * r + 0.25), h / 2), r, 16) - circle((u0 + k * (2 * r + 0.25), h / 2), r - 0.4, 12) for k in range(n)]
    return [ext(cs_union(rings), b - 0.05, b + 0.45)]


def _iris(c, s):
    """An iris ``s`` tall: three falls and three standards on a stem between two blade leaves."""
    x, y = c
    stem = stroke([(x, y - s * 0.5), (x, y + s * 0.1)], 0.35)
    leaves = cs_union([_lens((x + sg * s * 0.18, y - s * 0.2), s * 0.62, s * 0.14, math.pi / 2 - sg * 0.3) for sg in (-1, 1)])
    fy = y + s * 0.2
    petals = cs_union([_lens((x + s * 0.17 * math.cos(a), fy + s * 0.17 * math.sin(a)), s * 0.36, s * 0.2, a)
                       for a in (math.pi / 2, math.pi / 2 + 2.1, math.pi / 2 - 2.1)])
    return stem + leaves + petals


def frieze_irises(L, h, b, pitch, margin, pair, half):
    """Stylised irises in the Arts and Crafts way: one at every station, and a pair of blade
    leaves crossing in each bay."""
    v0, v1 = 0.7, h - 0.7
    hh = v1 - v0
    vm = (v0 + v1) / 2
    out = []
    for u in CO._us(L, pitch, margin, 0.0):
        out.append(_st(_iris((u, vm), hh) ^ rect(u - hh, v0 - 0.2, u + hh, v1 + 0.2), b, 0.45))
    for uc, wd in CO._between(L, pitch, margin, pair, half + hh * 0.6):
        if wd < 2.5:
            continue
        ww = min(wd * 0.4, 3.0)
        blades = cs_union([_lens((uc, vm), ww * 2, 0.55, sg * math.atan2(hh * 0.8, ww * 2)) for sg in (-1, 1)])
        out.append(_st(blades, b, 0.4))
    return out, []


def bracket_covetail(h, d, t):
    """A rafter tail cut off at its nose in a deep cove, the underside running straight back
    to the wall (side profile, top at v = 0)."""
    hb = min(h, max(1.8, 0.3 * d))
    pts = [(0.0, 0.0), (d, 0.0)]
    r = hb * 0.7
    for s in np.linspace(0.0, 1.0, 9):
        a = math.pi / 2 * s
        pts.append((d - r * math.sin(a), -r + r * math.cos(a) - hb * 0.3 * s))
    pts += [(d - r - 0.3, -hb), (0.0, -hb)]
    return poly(pts)


CO.FRIEZE_EXTRA.update(dragonflies=frieze_dragonflies, irises=frieze_irises)
CO.COURSE_EXTRA.update(rings=course_rings)
TW.BRACKET_EXTRA.update(covetail=bracket_covetail)
TW.FOUNDATION_EXTRA.update(rockblock=foundation_rockblock)


# ------------------------------------------------------------------ windows, the door, dormers
def _border_bars(cs, m=0.9):
    """Prairie border: bars cutting a narrow margin of lights round a big centre light."""
    u0, v0, u1, v1 = cs.bounds()
    return cs_union([rect(u0 + m - RIB / 2, v0 - 1, u0 + m + RIB / 2, v1 + 1), rect(u1 - m - RIB / 2, v0 - 1, u1 - m + RIB / 2, v1 + 1),
                     rect(u0 - 1, v1 - m - RIB / 2, u1 + 1, v1 - m + RIB / 2)])


def window_prairieborder(w, h, n=1, A=1.0):
    """A Hollister ground-floor window: the upper sash with a margin of narrow lights round a
    big centre light, a plain lower sash, ``n`` side by side, in casings with a backband,
    under a flat head with a little crown moulding; a sill on a plain apron."""
    sash, op, plug_cs = _hung(w, h, n=n, bars_top=_border_bars)
    ring = (op.offset(A, JoinType.Miter, 4.0) - op) ^ rect(-w, 0.0, w, h + A)
    band = (op.offset(A, JoinType.Miter, 4.0) - op.offset(A - 0.4, JoinType.Miter, 4.0)) ^ rect(-w, 0.3, w, h + A)
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS), ext(ring, 0.0, 0.55), ext(band, 0.54, 0.8)]
    hw = w / 2 + A
    parts.append(ext(rect(-hw - 0.2, h + A - 0.01, hw + 0.2, h + A + 1.2), 0.0, 0.7))
    parts.append(chamfer_box(-hw - 0.7, h + A + 1.19, hw + 0.7, h + A + 1.9, 0.0, 1.1, c=0.35, bottom=0.6))
    parts.append(chamfer_box(-hw - 0.5, -1.1, hw + 0.5, 0.2, 0.0, 1.1, c=0.35, bottom=0.7))
    parts.append(ext(rect(-hw + 0.5, -2.8, hw - 0.5, -1.09), 0.0, 0.45))
    return O._one_piece(sash, parts, op, plug_cs, O.PLUG, h + A + 1.9, -2.8)


def window_shelfhead(w, h, A=0.9):
    """A Hollister chamber window: three tall lights over one, in flat casings under a head
    shelf carried on two small corbels; a thin sill."""
    sash, op, plug_cs = _hung(w, h, top=(3, 1), bot=(1, 1))
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS),
             ext((op.offset(A, JoinType.Miter, 4.0) - op) ^ rect(-w, 0.0, w, h + A), 0.0, 0.6)]
    hw = w / 2 + A
    parts.append(ext(rect(-hw, h + A - 0.01, hw, h + A + 1.0), 0.0, 0.6))
    parts.append(chamfer_box(-hw - 1.2, h + A + 0.99, hw + 1.2, h + A + 1.7, 0.0, 1.4, c=0.35, bottom=0.8))
    for sg in (-1, 1):
        x = sg * (hw - 0.3)
        parts.append(M.hull_points([(x - 0.4, h + A + 1.0, 0.0), (x + 0.4, h + A + 1.0, 0.0), (x - 0.4, h + A + 1.0, 1.2),
                                    (x + 0.4, h + A + 1.0, 1.2), (x - 0.4, h + A - 0.6, 0.0), (x + 0.4, h + A - 0.6, 0.0)]))
    parts.append(chamfer_box(-hw - 0.4, -0.9, hw + 0.4, 0.2, 0.0, 1.0, c=0.3, bottom=0.6))
    return O._one_piece(sash, parts, op, plug_cs, O.PLUG, h + A + 1.7, -0.9)


def door_oval(w, h, transom=2.6, A=1.1):
    """The Hollister's door: a big oval of bevelled glass in a moulded ring over two
    horizontal panels, a narrow transom of three lights, in casings with a backband under a
    crowned head."""
    ht = h + transom
    op = rect(-w / 2, 0.0, w / 2, ht)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    body = [ext(plug_cs, -pl, -1.0)]
    u0, u1 = -w / 2 + O.CLR + 0.2, w / 2 - O.CLR - 0.2
    body.append(ext(rect(u0, 0.5, u1, h - 0.3), -1.0, -0.8))
    for vb, vt in ((1.0, h * 0.2), (h * 0.2 + 0.6, h * 0.4)):
        body.append(_panel(rect(u0 + 0.6, vb, u1 - 0.6, vt)))
    ov = oval((0.0, h * 0.7), (u1 - u0) / 2 - 0.9, h * 0.25, 40)
    body.append(ext(ov.offset(0.6, JoinType.Round) - ov, -0.81, -0.4))
    tr = rect(u0 + 0.3, h + 0.4, u1 - 0.3, ht - 0.5)
    bars = cs_union([rect(u0 + (u1 - u0) * j / 3 - RIB / 2, h, u0 + (u1 - u0) * j / 3 + RIB / 2, ht) for j in (1, 2)])
    sash = _glazed(body, ov + tr, pl, bars ^ tr, plug_cs)
    sash.append(ext(rect(-w, h - 0.3, w, h + 0.4) ^ plug_cs, -pl, -0.4))
    ring = (op.offset(A, JoinType.Miter, 4.0) - op) ^ rect(-w, 0.0, w, ht + A)
    band = (op.offset(A, JoinType.Miter, 4.0) - op.offset(A - 0.4, JoinType.Miter, 4.0)) ^ rect(-w, 0.3, w, ht + A)
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS), ext(ring, 0.0, 0.6), ext(band, 0.59, 0.85)]
    hw = w / 2 + A
    parts.append(ext(rect(-hw - 0.2, ht + A - 0.01, hw + 0.2, ht + A + 1.4), 0.0, 0.7))
    parts.append(chamfer_box(-hw - 0.8, ht + A + 1.39, hw + 0.8, ht + A + 2.2, 0.0, 1.2, c=0.35, bottom=0.6))
    return O._one_piece(sash, parts, op, plug_cs, pl, ht + A + 2.2, 0.0)


def dormer_hipband(w=20.0, dep=14.0, hwall=9.0):
    """A Foursquare dormer: a low front with a band of three casements of two lights each
    between slim mullions, a sill across the band, shingled cheeks. Local as
    colonial.dormer_pedimented; returns (body, core, face)."""
    face = rect(-w / 2, 0.0, w / 2, hwall)
    body = ext(face, -dep, 0.0) - ext(face.offset(-1.2, JoinType.Miter, 4.0) ^ rect(-50, 1.2, 50, hwall - 1.2), -dep - 1, -1.2)
    lw = w * 0.78
    band = rect(-lw / 2, 1.9, lw / 2, hwall - 1.5)
    body = body - ext(band, -1.3, 1.0)
    inner = band.offset(-0.4, JoinType.Miter, 4.0)
    a0, b0, a1, b1 = inner.bounds()
    cw = (a1 - a0) / 3
    bars = cs_union([rect(a0 + cw * j - 0.4, b0 - 1, a0 + cw * j + 0.4, b1 + 1) for j in (1, 2)] +
                    [rect(a0 + cw * (j + 0.5) - 0.22, b0 - 1, a0 + cw * (j + 0.5) + 0.22, b1 + 1) for j in range(3)])
    body = body + ext((band - inner) + (bars ^ inner), -1.2, -0.5)
    body = body + ext((band.offset(0.8, JoinType.Miter, 4.0) - band) ^ rect(-w, 1.9, w, hwall), -0.01, 0.55)
    body = body + chamfer_box(-lw / 2 - 1.0, 1.1, lw / 2 + 1.0, 1.9, -0.01, 0.9, c=0.3, bottom=0.9)
    core = ext(face.offset(-1.2, JoinType.Miter, 4.0) ^ rect(-50, 1.2, 50, hwall - 1.2), -dep + 1.2, -1.2)
    return body, core, face


def dormer_hipband_roof(w, dep, hwall, over=2.4, s=0.45, fascia=0.8):
    """The dormer's low hipped roof with wide eaves (a front hip and two side slopes), solid,
    standing on the dormer's flat top, run long at the back for the main roof to cut off."""
    a = w / 2 + over
    z = hwall + fascia
    blk = box([-a, hwall, -dep - 16.0], [a, z + a * s + 1.0, over])
    blk = blk.trim_by_plane([s, -1.0, 0.0], -(z + s * a)).trim_by_plane([-s, -1.0, 0.0], -(z + s * a))
    return blk.trim_by_plane([0.0, -1.0, -s], -(z + s * over))


# ------------------------------------------------------------------ the porch and the chimney
def post_hollister(h, collar=None, abacus=3.2, slot=None):
    """A Hollister porch column: a plain round shaft (a slight taper), two ring bands just under
    a square capital slab, on a square stone block."""
    zt = h - 2.4
    body = PW._plinth(3.4) + box([-1.6, -1.6, 1.19], [1.6, 1.6, 3.4]) + M.hull_points(
        [(x * 1.6, y * 1.6, 3.39) for x in (-1, 1) for y in (-1, 1)] + [(x * 1.3, y * 1.3, 3.8) for x in (-1, 1) for y in (-1, 1)])
    body = body + PW._revolve([(0.0, 3.79), (1.32, 3.79), (1.18, zt), (0.0, zt)], 32)
    for zb in (zt - 2.2, zt - 1.2):
        body = body + PW._revolve([(0.0, zb), (1.42, zb + 0.2), (1.42, zb + 0.5), (0.0, zb + 0.7)], 32)
    return body + PW._top(h, abacus / 2, zt - 0.01, 1.18, slot, shape="round")


def fill_triplets(L, vb, vt):
    """Prairie railing: flat slats in groups of three, the groups spaced wide apart."""
    parts = []
    n = max(1, int(round(L / 5.0)))
    for i in range(n):
        c = L * (i + 0.5) / n
        for dx in (-1.1, 0.0, 1.1):
            parts.append(rect(c + dx - 0.3, vb, c + dx + 0.3, vt))
    return parts


def frieze_banded(u0, u1, v_bot, v_top):
    """A porch beam with a sunk reveal along it and a square block over every post."""
    v0 = v_top - 2.6
    beam = rect(u0, v0, u1, v_top + 0.05) - rect(u0 + 1.8, v0 + 1.0, u1 - 1.8, v0 + 1.5)
    return beam + rect(u0, v0 - 0.6, u0 + 1.6, v_top + 0.05) + rect(u1 - 1.6, v0 - 0.6, u1, v_top + 0.05)


def edge_keys(L, z0, zc):
    """Porch fascia (the Hollister): small raised keys at intervals along a drip band."""
    xs = np.arange(1.2, L - 0.8, 3.0)
    return cs_union([rect(x - 0.5, zc - 1.2, x + 0.5, zc) for x in xs]) + rect(0.3, zc - 0.55, L - 0.3, zc), 0.6


def skirt_blockvent(reg, d=1.2):
    """A skirt of rock-faced block with a small grilled vent in every bay."""
    if reg.is_empty():
        return M()
    u0, v0, u1, v1 = reg.bounds()
    body = M.extrude(reg, d * 0.6)
    vents = []
    for u in np.arange(u0 + 6.0, u1 - 3.0, 12.0):
        vr = rect(u - 1.6, (v0 + v1) / 2 - 0.9, u + 1.6, (v0 + v1) / 2 + 0.9)
        vents.append(vr)
    if vents:
        vc = cs_union(vents) ^ reg
        body = body - ext(vc, d * 0.3, d) + ext(cs_union([rect(u - 1.4 + 0.7 * j, (v0 + v1) / 2 - 0.9, u - 1.1 + 0.7 * j, (v0 + v1) / 2 + 0.9)
                                                          for u in np.arange(u0 + 6.0, u1 - 3.0, 12.0) for j in range(5)]) ^ reg, d * 0.3, d * 0.55)
    ribs = cs_union([rect(u0 - 1, v, u1 + 1, v + 0.3) for v in np.arange(v0 + 1.6, v1, 1.6)]) ^ reg
    return body + ext(ribs, d * 0.59, d * 0.75)


def chimney_rockblock(w=10.0, d=10.0, h=30.0):
    """The Hollister's stack in rock-faced concrete block like its foundation, a smooth band
    two thirds up and a cast-stone cap with a drip edge, one flue."""
    h = round(h / 0.2) * 0.2
    zt = h - 1.8
    body = box([-w / 2, -d / 2, 0.0], [w / 2, d / 2, zt])
    body = body + TW._skin(w, d, 0.0, zt - 0.2, lambda reg, i: foundation_rockblock(reg, seed=i)).translate([0, 0, 0])
    zb = round(h * 0.62 / 0.2) * 0.2
    body = body + box([-w / 2 - 0.6, -d / 2 - 0.6, zb], [w / 2 + 0.6, d / 2 + 0.6, zb + 1.0])
    body = body + M.hull_points([(x * w / 2, y * d / 2, zb - 0.6) for x in (-1, 1) for y in (-1, 1)] +
                                [(x * (w / 2 + 0.6), y * (d / 2 + 0.6), zb) for x in (-1, 1) for y in (-1, 1)])
    body = body + box([-w / 2 - 1.0, -d / 2 - 1.0, zt - 0.01], [w / 2 + 1.0, d / 2 + 1.0, h])
    body = body + M.hull_points([(x * w / 2, y * d / 2, zt - 0.8) for x in (-1, 1) for y in (-1, 1)] +
                                [(x * (w / 2 + 1.0), y * (d / 2 + 1.0), zt) for x in (-1, 1) for y in (-1, 1)])
    return body - box([-w / 2 + 1.8, -d / 2 + 1.8, zt - 5.0], [w / 2 - 1.8, d / 2 - 1.8, h + 5])


PW.POSTS.update(hollister=post_hollister)
PW.FILLS.update(triplets=fill_triplets)
PW.FRIEZES.update(banded=frieze_banded)
PW.SKIRTS.update(blockvent=skirt_blockvent)
FT.EDGE_EXTRA.update(keys=edge_keys)

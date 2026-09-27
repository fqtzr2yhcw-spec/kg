"""Craftsman-era parts, volume two (houses 54 to 60 of the fifth batch). Like ``craftsman``, the
module registers its cornice ornaments, brackets and foundations with ``cornice`` and
``trimwork`` on import, and no part is shared with another building: each section below
belongs to one house.
"""
import math

import numpy as np
from manifold3d import JoinType, Manifold as M

from .core import RIB, box, circle, cs_union, poly, rect, union
from .ornament import chamfer_box, ext, oval, stroke
from . import cornice as CO, openings as O, trimwork as TW
from .colonial import _st
from .colonial4 import _glazed


def _arc(c, r, a0, a1, n=16):
    return [(c[0] + r * math.cos(a), c[1] + r * math.sin(a)) for a in np.linspace(a0, a1, n)]


def _stripes(cs, ang, sp, w):
    """Parallel bars ``w`` wide, ``sp`` apart (measured square to them), at ``ang`` from level,
    over the bounds of ``cs``."""
    u0, v0, u1, v1 = cs.bounds()
    c = np.array([(u0 + u1) / 2, (v0 + v1) / 2])
    R = math.hypot(u1 - u0, v1 - v0) / 2 + 2.0
    d = np.array([math.cos(ang), math.sin(ang)])
    n = np.array([-d[1], d[0]])
    out = []
    for k in range(-int(R / sp) - 1, int(R / sp) + 2):
        o = c + n * k * sp
        out.append(poly([tuple(o - d * R - n * w / 2), tuple(o + d * R - n * w / 2), tuple(o + d * R + n * w / 2), tuple(o - d * R + n * w / 2)]))
    return cs_union(out)


def tudor_arch(w, vs, rise, r_frac=0.34, n=14):
    """A four-centred (Tudor) arch opening ``w`` wide, springing at ``vs`` and rising ``rise``:
    a tight quarter-round at each springing turning into a straight rake up to the point."""
    a = w / 2
    r = a * r_frac
    lo, hi = 0.05, math.pi / 2 - 0.05
    for _ in range(40):                      # the angle where the rake leaves the small arc
        phi = (lo + hi) / 2
        px, py = -a + r - r * math.cos(phi), r * math.sin(phi)
        s = (0.0 - px) / math.sin(phi)
        if py + s * math.cos(phi) > rise:
            hi = phi
        else:
            lo = phi
    left = [(-a + r - r * math.cos(t), vs + r * math.sin(t)) for t in np.linspace(0.0, phi, n)]
    right = [(-x, y) for (x, y) in reversed(left)]
    return poly([(-a, 0.0)] + left + [(0.0, vs + rise)] + right + [(a, 0.0)])


# ================================================================== the Ashcombe (Tudor Revival)
def brick_diaper(region, datum=0.0, bl=2.6, bh=0.85, P=15.0, Q=10.2, parts=False):
    """Tudor brick in running bond with a diaper: a lattice of diamonds picked out in darker
    over-burnt headers standing a little proud (the Ashcombe). ``parts``: also return the
    diaper bricks alone (for the render's colour zone)."""
    if region.is_empty():
        return (M(), M()) if parts else M()
    u0, v0, u1, v1 = region.bounds()
    beds, heads, dia = [], [], []
    k = math.floor((v0 - datum) / bh) - 1
    while datum + k * bh < v1:
        v = datum + k * bh
        beds.append(rect(u0 - 1, v - 0.12, u1 + 1, v + 0.12))
        off = (k % 2) * bl / 2
        j0 = math.floor((u0 - off) / bl) - 1
        for j in range(j0, j0 + int((u1 - u0) / bl) + 4):
            u = off + j * bl
            heads.append(rect(u - 0.12, v, u + 0.12, v + bh))
            uc, vc = u + bl / 2, v + bh / 2
            a_, b_ = uc / P + vc / Q, uc / P - vc / Q
            if min(abs(a_ - round(a_)), abs(b_ - round(b_))) * P < bl * 0.5:
                dia.append(rect(u + 0.14, v + 0.14, u + bl - 0.14, v + bh - 0.14))
        k += 1
    out = M.extrude(region, 0.4) - ext(cs_union(beds) ^ region, 0.18, 1.0) - ext(cs_union(heads) ^ region, 0.18, 1.0)
    dz = ext(cs_union(dia) ^ region.offset(-0.2, JoinType.Miter, 4.0), 0.3, 0.6) if dia else M()
    out = out + dz
    return (out, dz) if parts else out


def halftimber_tudor(region, L, v_sill, v_top, v_gable=None, apex=None, post=7.6, parts=False):
    """Tudor half-timbering over smooth render (the Ashcombe). In the storey: a sill plate, a
    middle rail and a head plate; posts about ``post`` apart with a close stud between each
    pair below the rail; above it the bays take lozenges and pairs of curved braces in turn.
    In the gable (above ``v_gable``, up to ``apex``): a collar, a king post, two raking struts
    and a quatrefoil in each lower panel. The timbers stand 0.6 proud of the render."""
    if region.is_empty():
        return (M(), M()) if parts else M()
    tw = 1.1
    v_mid = v_sill + (v_top - v_sill) * 0.46
    bars = [rect(-1, v_sill, L + 1, v_sill + 1.3), rect(-1, v_mid - 0.55, L + 1, v_mid + 0.55), rect(-1, v_top - 1.3, L + 1, v_top)]
    n = max(2, int(round((L - 1.8) / post)))
    us = np.linspace(0.9, L - 0.9, n + 1)
    for u in us:
        bars.append(rect(u - tw / 2, v_sill, u + tw / 2, v_top))
    for j, (ua, ub) in enumerate(zip(us[:-1], us[1:])):
        uc = (ua + ub) / 2
        bars.append(rect(uc - 0.45, v_sill, uc + 0.45, v_mid))                    # close stud
        a0, a1 = v_mid + 0.55, v_top - 1.3
        vc = (a0 + a1) / 2
        if j % 2 == 0:                                                           # a lozenge
            hw = (ub - ua) / 2 - tw / 2
            hv = (a1 - a0) / 2
            loz = poly([(uc - hw, vc), (uc, vc + hv), (uc + hw, vc), (uc, vc - hv)])
            bars.append(loz - loz.offset(-0.8, JoinType.Miter, 4.0))
        else:                                                                    # curved braces meeting the head
            r = min((ub - ua) / 2 - tw / 2, a1 - a0) * 0.95
            for (cx, s0, s1) in ((ua + tw / 2, -math.pi / 2, 0.0), (ub - tw / 2, math.pi, 3 * math.pi / 2)):
                bars.append(stroke(_arc((cx, a1), r, s0, s1, 12), 0.8, caps=False))
    if v_gable is not None and apex is not None and apex - v_gable > 6.0:
        g0 = v_gable + 0.4
        H = apex - g0
        bars += [rect(-1, g0, L + 1, g0 + 1.3), rect(L / 2 - tw / 2, g0, L / 2 + tw / 2, apex + 2)]
        for sg in (-1, 1):
            bars.append(stroke([(L / 2 + sg * L * 0.34, g0 + 1.0), (L / 2 + sg * 0.4, g0 + H * 0.62)], 0.95, caps=False))
            qc = (L / 2 + sg * L * 0.2, g0 + H * 0.28)
            rq = min(1.1, H * 0.08)
            q = cs_union([circle((qc[0] + dx, qc[1] + dy), rq, 18) for dx, dy in ((rq, 0), (-rq, 0), (0, rq), (0, -rq))])
            bars.append(q - q.offset(-0.7, JoinType.Round))
    tim = cs_union(bars) ^ region
    out = M.extrude(region, 0.3) + ext(tim, 0.0, 0.9)
    return (out, ext(tim, 0.28, 0.9)) if parts else out


def foundation_tudorstone(reg, seed=0):
    """A plinth of squared rubble stone: blocks of three heights in broken courses, each face
    with a pitched (hammered) edge standing proud of a flat margin (the Ashcombe)."""
    b = reg.bounds()
    rng = np.random.default_rng(seed + 211)
    out = [M.extrude(reg, 0.2)]
    stones = []
    v = b[1] + 0.2
    while v < b[3] - 0.6:
        hh = float(rng.choice([1.6, 2.2, 2.8]))
        hh = min(hh, b[3] - v - 0.2)
        u = b[0] - rng.uniform(0.0, 3.0)
        while u < b[2]:
            ww = rng.uniform(2.6, 5.6)
            stones.append(rect(u + 0.12, v + 0.12, u + ww - 0.12, v + hh - 0.12))
            u += ww
        v += hh
    sc = cs_union(stones) ^ reg
    out.append(ext(sc, 0.15, 0.45))
    out.append(ext(sc.offset(-0.35, JoinType.Round), 0.4, 0.6))
    return union(out)


def frieze_portcullis(L, h, b, pitch, margin, pair, half):
    """The Tudor portcullis badge at every station (a grille of bars with pointed feet, two
    chains hanging from its top corners), a trailing vine of leaves between (the Ashcombe)."""
    v0, v1 = 0.6, h - 0.6
    hh = v1 - v0
    out = []
    pw = min(3.6, pitch * 0.3)
    for u in CO._us(L, pitch, margin, 0.0):
        g = [rect(u - pw / 2, v1 - 0.5, u + pw / 2, v1)]
        for k in range(4):
            x = u - pw / 2 + 0.3 + k * (pw - 0.6) / 3
            g += [rect(x - 0.22, v0 + 0.7, x + 0.22, v1), poly([(x - 0.3, v0 + 0.72), (x + 0.3, v0 + 0.72), (x, v0)])]
        for fv in (0.35, 0.65):
            g.append(rect(u - pw / 2, v0 + hh * fv - 0.2, u + pw / 2, v0 + hh * fv + 0.2))
        for sg in (-1, 1):
            g.append(stroke([(u + sg * pw / 2, v1 - 0.25), (u + sg * (pw / 2 + 0.9), v0 + hh * 0.45)], 0.4, caps=True))
            g.append(circle((u + sg * (pw / 2 + 0.95), v0 + hh * 0.38), 0.4, 12))
        out.append(_st(cs_union(g), b, 0.45))
    for uc, wd in CO._between(L, pitch, margin, pair, half + pw / 2 + 1.6):
        if wd < 3.0:
            continue
        us = np.linspace(uc - wd / 2, uc + wd / 2, max(8, int(wd * 3)))
        amp = hh * 0.2
        vm = v0 + hh / 2
        stem = [(x, vm + amp * math.sin((x - us[0]) / wd * 2 * math.pi)) for x in us]
        parts = [stroke(stem, 0.4, caps=False)]
        for t in (0.25, 0.75):
            x = uc - wd / 2 + wd * t
            y = vm + amp * math.sin(t * 2 * math.pi)
            sg = 1 if t < 0.5 else -1
            parts.append(oval((x, y - sg * 0.9), 0.55, 0.9, 16))
        out.append(_st(cs_union(parts), b, 0.35))
    return out, []


def frieze_tudorflower(L, h, b, pitch, margin, pair, half):
    """Tudor flowers: at every station a three-lobed flower on a short stem over a bar, the
    side lobes curling out and down; between them a ball over a lozenge (the Ashcombe)."""
    v0, v1 = 0.6, h - 0.6
    hh = v1 - v0
    out = []
    for u in CO._us(L, pitch, margin, 0.0):
        f = [rect(u - 1.6, v0, u + 1.6, v0 + 0.5), rect(u - 0.25, v0 + 0.4, u + 0.25, v0 + hh * 0.45),
             oval((u, v0 + hh * 0.7), 0.6, hh * 0.28, 18)]
        vm = v0 + hh * 0.5
        for (cx, a0, a1) in ((u - 0.95, 0.0, 0.9 * math.pi), (u + 0.95, math.pi, 0.1 * math.pi)):
            arc = _arc((cx, vm), 0.8, a0, a1, 10)
            f.append(stroke(arc, 0.45, caps=True))
            f.append(circle(arc[-1], 0.4, 12))
        out.append(_st(cs_union(f), b, 0.45))
    for uc, wd in CO._between(L, pitch, margin, pair, half + 2.4):
        if wd < 2.4:
            continue
        loz = poly([(uc - 1.1, v0 + hh * 0.32), (uc, v0 + hh * 0.08), (uc + 1.1, v0 + hh * 0.32), (uc, v0 + hh * 0.56)])
        out.append(_st(cs_union([loz, circle((uc, v0 + hh * 0.78), 0.6, 16)]), b, 0.35))
    return out, []


def course_ballflower(L, h, b, pitch, margin, p):
    """Ballflowers: small globes, each held in three petals, all along the course."""
    out = []
    sp = max(2.2, h * 1.5)
    n = max(1, int((L - 0.8) / sp))
    for k in range(n):
        u = 0.4 + (k + 0.5) * (L - 0.8) / n
        vc = h / 2
        r = min(0.75, h * 0.4)
        petals = cs_union([circle((u + r * 0.55 * math.cos(a), vc + r * 0.55 * math.sin(a)), r * 0.6, 12)
                           for a in (math.pi / 2, math.pi / 2 + 2.094, math.pi / 2 + 4.189)])
        out.append(ext(petals, b - 0.05, b + 0.3))
        out.append(ext(circle((u, vc), r * 0.45, 12), b + 0.25, b + 0.5))
    return out


def course_chequer(L, h, b, pitch, margin, p):
    """A chequer of flush and sunk squares in two rows, like flint-and-stone flushwork."""
    q = h / 2
    n = max(2, int(L / q))
    sq = [rect(k * L / n + 0.08, (k % 2) * q + 0.05, (k + 1) * L / n - 0.08, (k % 2) * q + q - 0.05) for k in range(n)]
    return [ext(cs_union(sq), b - 0.05, b + 0.35)]


def bracket_jettybrace(h, d, t):
    """A jetty bracket: a curved oak brace sweeping out from the wall to carry the overhang,
    its foot finished in a lamb's-tongue stop (side profile, top at v = 0)."""
    hb = max(1.6, h)
    pts = [(0.0, 0.0), (d, 0.0), (d, -0.7)]
    pts += [(d - (d - 0.5) * (1 - math.cos(a)), -0.7 - (hb - 1.6) * math.sin(a)) for a in np.linspace(0.05, math.pi / 2, 12)]
    pts += [(0.5, -hb + 0.6), (0.25, -hb), (0.0, -hb)]
    return poly(pts)


CO.FRIEZE_EXTRA.update(portcullis=frieze_portcullis, tudorflower=frieze_tudorflower)
CO.COURSE_EXTRA.update(ballflower=course_ballflower, chequer=course_chequer)
TW.BRACKET_EXTRA.update(jettybrace=bracket_jettybrace)
TW.FOUNDATION_EXTRA.update(tudorstone=foundation_tudorstone)


def _label(hw, v, A, drop=3.2, t=1.5):
    """A square label (hood) mould over an opening: a drip band with returns down each side,
    each ending in a square stop carved with a lozenge."""
    parts = [chamfer_box(-hw - 1.3, v, hw + 1.3, v + 1.2, 0.0, t, c=0.35, bottom=0.6)]
    for sg in (-1, 1):
        a, e = sorted((sg * hw, sg * (hw + 1.3)))
        parts.append(chamfer_box(a, v - drop, e, v + 0.01, 0.0, t, c=0.3))
        s0, s1 = sorted((sg * (hw - 0.3), sg * (hw + 1.6)))
        parts.append(chamfer_box(s0, v - drop - 1.6, s1, v - drop + 0.01, 0.0, t + 0.2, c=0.35, bottom=0.8))
        c = ((s0 + s1) / 2, v - drop - 0.8)
        parts.append(ext(poly([(c[0] - 0.6, c[1]), (c[0], c[1] + 0.6), (c[0] + 0.6, c[1]), (c[0], c[1] - 0.6)]), t + 0.15, t + 0.45))
    return parts


def window_stonemullion(w, h, n=3, A=1.4):
    """The Ashcombe's ground-floor window: ``n`` lights between chamfered stone mullions under a
    stone transom, each light leaded in diamond quarries, in a stone surround on a weathered
    sill, under a square label mould with carved stops."""
    op = O.opening_cs(w, h, 0)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    u0, v0, u1, v1 = plug_cs.offset(-0.5, JoinType.Miter, 4.0).bounds()
    mull = 1.2
    cw = (u1 - u0 - (n - 1) * mull) / n
    vt = v0 + (v1 - v0) * 0.72
    lights = []
    for j in range(n):
        a = u0 + j * (cw + mull)
        lights += [rect(a, v0, a + cw, vt - 0.6), rect(a, vt + 0.6, a + cw, v1)]
    g = cs_union(lights)
    bars = cs_union([_stripes(g, math.radians(64), 1.6, 0.4), _stripes(g, math.radians(116), 1.6, 0.4)])
    sash = _glazed([ext(plug_cs, -pl, -0.6)], g, pl, bars, plug_cs)
    stone = [rect(u0 + j * (cw + mull) - mull, v0, u0 + j * (cw + mull), v1) for j in range(1, n)] + [rect(u0, vt - 0.6, u1, vt + 0.6)]
    sash.append(ext(cs_union(stone), -pl, 0.5))
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, 0.8),
             chamfer_box(-w / 2 - A, 0.0, -w / 2 + 0.01, h + 0.01, 0.0, 0.9, c=0.3),
             chamfer_box(w / 2 - 0.01, 0.0, w / 2 + A, h + 0.01, 0.0, 0.9, c=0.3),
             chamfer_box(-w / 2 - A, h - 0.01, w / 2 + A, h + A, 0.0, 0.9, c=0.3)]
    parts.append(chamfer_box(-w / 2 - A - 0.8, -1.4, w / 2 + A + 0.8, 0.2, 0.0, 1.6, c=0.5, bottom=1.0))
    parts += _label(w / 2 + A, h + A, A)
    return O._one_piece(sash, parts, op, plug_cs, pl, h + A + 1.2, -1.4 - 0.0)


def window_oakframe(w, h, n=2, A=1.2):
    """The Ashcombe's upper window, in oak to match the timbers: ``n`` lights leaded in small
    upright quarries between moulded mullions, a carved head beam whose soffit is cut to a
    shallow Tudor arch over each light, and a sill carried on two shaped brackets."""
    op = O.opening_cs(w, h, 0)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    u0, v0, u1, v1 = plug_cs.offset(-0.5, JoinType.Miter, 4.0).bounds()
    mull = 1.0
    cw = (u1 - u0 - (n - 1) * mull) / n
    lights = [rect(u0 + j * (cw + mull), v0, u0 + j * (cw + mull) + cw, v1) for j in range(n)]
    g = cs_union(lights)
    qs = []
    for l_ in lights:
        a, _, e, _ = l_.bounds()
        for k in (1, 2):
            x = a + (e - a) * k / 3
            qs.append(rect(x - 0.2, v0 - 1, x + 0.2, v1 + 1))
    for k in range(1, int((v1 - v0) / 2.6) + 1):
        y = v0 + k * (v1 - v0) / (int((v1 - v0) / 2.6) + 1)
        qs.append(rect(u0 - 1, y - 0.2, u1 + 1, y + 0.2))
    sash = _glazed([ext(plug_cs, -pl, -0.6)], g, pl, cs_union(qs), plug_cs)
    for j in range(1, n):
        a = u0 + j * (cw + mull) - mull
        sash.append(ext(rect(a, v0, a + mull, v1), -pl, 0.2))
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, 0.7),
             chamfer_box(-w / 2 - A, 0.0, -w / 2 + 0.01, h + 0.01, 0.0, 0.8, c=0.25),
             chamfer_box(w / 2 - 0.01, 0.0, w / 2 + A, h + 0.01, 0.0, 0.8, c=0.25)]
    # the head beam, its soffit cut to a shallow arch over each light
    hb = 2.4
    head = rect(-w / 2 - A - 1.0, h - 0.8, w / 2 + A + 1.0, h + hb)
    for l_ in lights:
        a, _, e, _ = l_.bounds()
        head = head - (tudor_arch(e - a, 0.0, 1.2, r_frac=0.3).translate(((a + e) / 2, h - 1.6)) ^ rect(a, h - 0.8, e, h + 0.2))
    parts.append(ext(head, 0.0, 1.1))
    parts.append(ext(rect(-w / 2 - A - 1.0, h + hb - 0.6, w / 2 + A + 1.0, h + hb), 1.0, 1.4))
    for l_ in lights:
        a, _, e, _ = l_.bounds()
        c = ((a + e) / 2, h + hb * 0.45)
        parts.append(ext(oval(c, 0.9, 0.45, 16), 1.0, 1.3))
    parts.append(chamfer_box(-w / 2 - A - 0.6, -1.2, w / 2 + A + 0.6, 0.2, 0.0, 1.5, c=0.4, bottom=0.9))
    for sg in (-1, 1):                                  # the sill's shaped brackets, stepped quarter-rounds
        x = sg * (w / 2 - 1.0)
        for k in range(6):
            dw = 1.4 * math.cos(math.asin(min(1.0, (k + 0.5) / 6)))
            parts.append(box([x - 0.45, -1.2 - (k + 1) * 0.4, 0.0], [x + 0.45, -1.2 - k * 0.4 + 0.01, dw]))
    return O._one_piece(sash, parts, op, plug_cs, pl, h + hb, -3.6)


def window_tudorlights(w, h, n=2, A=1.0):
    """A small gable window: ``n`` lights, each under a four-centred arched head cut in an oak
    frame, leaded in diamond quarries, a moulded sill and a drip over the top."""
    op = O.opening_cs(w, h, 0)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    u0, v0, u1, v1 = plug_cs.offset(-0.5, JoinType.Miter, 4.0).bounds()
    mull = 1.0
    cw = (u1 - u0 - (n - 1) * mull) / n
    lights = []
    for j in range(n):
        a = u0 + j * (cw + mull)
        vs = (v1 - v0) - cw * 0.34 - 0.2
        lights.append(tudor_arch(cw, vs, cw * 0.34).translate((a + cw / 2, v0)))
    g = cs_union(lights)
    bars = cs_union([_stripes(g, math.radians(62), 1.5, 0.4), _stripes(g, math.radians(118), 1.5, 0.4)])
    body = [ext(plug_cs, -pl, -0.6)]
    sash = _glazed(body, g, pl, bars, plug_cs)
    ring = (op.offset(A, JoinType.Miter, 4.0) - op) ^ rect(-w, 0.0, w, h + A)
    parts = [ext(ring, 0.0, 0.8), ext(op - g.offset(0.5, JoinType.Miter, 4.0), -0.6, 0.8), ext(op.offset(A, JoinType.Miter, 4.0) - op.offset(A - 0.5, JoinType.Miter, 4.0), 0.0, 1.1)]
    parts.append(chamfer_box(-w / 2 - A - 1.0, h + A - 0.01, w / 2 + A + 1.0, h + A + 1.0, 0.0, 1.3, c=0.35, bottom=0.6))
    parts.append(chamfer_box(-w / 2 - A - 0.6, -1.2, w / 2 + A + 0.6, 0.2, 0.0, 1.4, c=0.4, bottom=0.8))
    return O._one_piece(sash, parts, op, plug_cs, pl, h + A + 1.0, -1.2)


def door_tudor(w=11.0, h=24.0, jamb=2.2, A=1.8):
    """The Ashcombe's front door, in two colours (one change): an oak leaf of vertical boards
    under a four-centred arch, two long wrought strap hinges ending in fleurs, a grilled
    speaking window and a ring pull, all set in a stone surround whose arch carries a roll
    moulding, its spandrels carved with leaves, under a square label with carved stops."""
    W_ = w + 2 * jamb
    op = rect(-W_ / 2, 0.0, W_ / 2, h)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    vs = h - 4.4
    arch = tudor_arch(w, vs, 3.0, r_frac=0.5) ^ rect(-w, 0.3, w, h)
    body = [ext(plug_cs, -pl, -1.0)]
    boards = cs_union([rect(-w / 2 + k * w / 7 - 0.12, 0.0, -w / 2 + k * w / 7 + 0.12, h) for k in range(1, 7)])
    leaf = arch.offset(-0.2, JoinType.Miter, 4.0)
    body.append(ext(leaf - boards, -1.0, -0.6) + ext(leaf, -1.0, -0.8))
    # the strap hinges, running from the hinge side, each ending in a fleur
    for v in (h * 0.2, h * 0.64):
        xe = -w / 2 + w * 0.72
        strap = cs_union([rect(-w / 2 + 0.2, v - 0.4, xe, v + 0.4), circle((xe + 0.45, v), 0.55, 14),
                          stroke(_arc((xe + 0.2, v + 0.9), 0.75, -math.pi / 2, 0.6, 8), 0.4, caps=True),
                          stroke(_arc((xe + 0.2, v - 0.9), 0.75, math.pi / 2, -0.6, 8), 0.4, caps=True)])
        body.append(ext(strap ^ leaf, -0.7, -0.35))
    # the speaking grille and the ring pull
    gv = h * 0.46
    grille = rect(-1.4, gv - 1.4, 1.4, gv + 1.4)
    body.append(ext(grille.offset(0.35, JoinType.Miter, 4.0) - grille, -0.7, -0.35))
    body.append(ext(cs_union([rect(x - 0.22, gv - 1.4, x + 0.22, gv + 1.4) for x in (-0.7, 0.0, 0.7)]), -0.8, -0.4))
    body.append(ext(circle((w / 2 - 1.6, h * 0.42), 0.85, 18) - circle((w / 2 - 1.6, h * 0.42), 0.42, 14), -0.7, -0.35))
    sash = body
    # the stone surround: the face round the arch, a roll moulding on the arch, carved spandrels
    face = op.offset(A, JoinType.Miter, 4.0) ^ rect(-W_, 0.0, W_, h + A)
    parts = [ext(face - arch, 0.0, 0.8), ext(op - arch.offset(0.6, JoinType.Miter, 4.0), -pl, 0.0)]
    roll = (arch.offset(0.9, JoinType.Round) - arch) ^ rect(-w, 0.0, w, h)
    parts.append(ext(roll, 0.6, 1.2))
    for sg in (-1, 1):                                  # a carved quatrefoil in each spandrel
        c = (sg * (w / 2 - 0.2), h - 1.3)
        q = cs_union([circle((c[0] + dx, c[1] + dy), 0.55, 14) for dx, dy in ((0.5, 0), (-0.5, 0), (0, 0.5), (0, -0.5))])
        parts.append(ext((q - q.offset(-0.35, JoinType.Round) + circle(c, 0.25, 10)) - arch.offset(1.0, JoinType.Round), 0.75, 1.05))
    parts += _label(W_ / 2 + A - 0.8, h + A, A, drop=4.2, t=1.7)
    parts.append(chamfer_box(-W_ / 2 - A, -0.01, W_ / 2 + A, 0.0 + 0.8, 0.0, 1.0, c=0.3))
    return O._one_piece(sash, parts, op, plug_cs, pl, h + A + 1.2, 0.0)


def _star(r_out, r_in, k=6):
    pts = []
    for j in range(2 * k):
        r = r_out if j % 2 == 0 else r_in
        a = math.pi * j / k
        pts.append((r * math.cos(a), r * math.sin(a)))
    return poly(pts)


def chimney_tudor(h, z1, z2, W1=22.0, D1=10.0, W2=19.0, D2=8.4, W3=14.0, D3=7.4):
    """The Ashcombe's front chimney, in diapered Tudor brick: a broad breast on a stone plinth,
    weathered in at ``z1`` and again at ``z2`` to the stack, a moulded cap, and two tall
    shafts of six-pointed star section twisted a quarter turn, each under a flared star crown.
    Local: x across the wall, y out from the wall (back face on y = 0), z up from the ground."""
    h = round(h / 0.2) * 0.2

    def skin(reg, i):
        return brick_diaper(reg, P=11.0, Q=8.0)

    def _body(w, d, za, zb):
        b = box([-w / 2, 0.0, za], [w / 2, d, zb])
        s = TW._skin(w, d, za + 0.2, zb - 0.2, skin).translate([0, d / 2, 0])
        return b + (s - box([-w, -5, za - 1], [w, 0.0, zb + 1]))

    plinth = box([-W1 / 2 - 0.8, 0.0, 0.0], [W1 / 2 + 0.8, D1 + 0.8, 6.0])
    plinth = plinth + M.hull_points([(x * (W1 / 2 + 0.8), y, 5.99) for x in (-1, 1) for y in (0.0, D1 + 0.8)] +
                                    [(x * W1 / 2, y, 7.0) for x in (-1, 1) for y in (0.0, D1)])
    out = plinth + _body(W1, D1, 7.0, z1)

    def weather(wa, da, wb, db, z):
        return M.hull_points([(x * wa / 2, y, z - 0.01) for x in (-1, 1) for y in (0.0, da)] +
                             [(x * wb / 2, y, z + (da - db) + 0.8) for x in (-1, 1) for y in (0.0, db)])
    out = out + weather(W1, D1, W2, D2, z1)
    za = z1 + (D1 - D2) + 0.8
    out = out + _body(W2, D2, za - 0.01, z2)
    out = out + weather(W2, D2, W3, D3, z2)
    zb = z2 + (D2 - D3) + 0.8
    zc = h - 17.0
    out = out + _body(W3, D3, zb - 0.01, zc)
    for k, (g, t) in enumerate(((0.3, 0.6), (0.7, 0.8))):                 # the moulded cap
        out = out + box([-W3 / 2 - g, 0.0, zc - 0.01 + k * 0.6], [W3 / 2 + g, D3 + g, zc + (k + 1) * 0.6 + (0.2 if k else 0)])
    zs = zc + 1.4
    for sg in (-1, 1):
        cx, cy = sg * W3 / 4, D3 / 2 + 0.3
        base = box([cx - 3.0, cy - 3.0, zs - 0.01], [cx + 3.0, cy + 3.0, zs + 1.6])
        shaft = M.extrude(_star(2.7, 1.9), h - zs - 5.0, 24, 60.0).translate([cx, cy, zs + 1.59])
        zt = h - 3.4
        crown = M.extrude(_star(2.7, 1.9), 1.8, 1, 0.0, (1.35, 1.35)).rotate([0, 0, 0]).translate([cx, cy, zt - 0.01])
        crown = crown + M.extrude(_star(3.65, 2.55), 1.6).translate([cx, cy, zt + 1.79])
        flue = M.cylinder(3.0, 1.2, 1.2, 20).translate([cx, cy, h - 1.4])
        out = out + base + shaft + crown - flue
    return out


def door_ledged(w=9.0, h=21.0, A=1.2):
    """The Ashcombe's back door: an oak leaf of vertical boards with a small four-light window
    high up, plain strap hinges and a thumb latch, in a chamfered oak frame under a little
    pent hood on two stepped brackets."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    leaf = plug_cs.offset(-0.3, JoinType.Miter, 4.0)
    u0, v0, u1, v1 = leaf.bounds()
    win = rect(u0 + 1.2, v1 - 5.4, u1 - 1.2, v1 - 1.2)
    boards = cs_union([rect(u0 + k * (u1 - u0) / 5 - 0.12, v0, u0 + k * (u1 - u0) / 5 + 0.12, v1) for k in range(1, 5)])
    body = [ext(plug_cs, -pl, -1.0), ext(leaf - boards - win, -1.0, -0.6)]
    bars = cs_union([rect((u0 + u1) / 2 - 0.2, v1 - 6.0, (u0 + u1) / 2 + 0.2, v1), rect(u0, v1 - 3.5, u1, v1 - 3.1)])
    sash = _glazed(body, win, pl, bars, plug_cs)
    for v in (h * 0.18, h * 0.58):
        xe = u0 + (u1 - u0) * 0.62
        sash.append(ext(cs_union([rect(u0 + 0.2, v - 0.35, xe, v + 0.35), circle((xe, v), 0.5, 12)]), -0.7, -0.35))
    sash.append(ext(cs_union([rect(u1 - 1.6, h * 0.45 - 0.25, u1 - 0.5, h * 0.45 + 0.25), circle((u1 - 1.8, h * 0.45), 0.45, 12)]), -0.7, -0.35))
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, 0.7),
             chamfer_box(-w / 2 - A, 0.0, -w / 2 + 0.01, h + 0.01, 0.0, 0.9, c=0.3),
             chamfer_box(w / 2 - 0.01, 0.0, w / 2 + A, h + 0.01, 0.0, 0.9, c=0.3),
             chamfer_box(-w / 2 - A, h - 0.01, w / 2 + A, h + A, 0.0, 0.9, c=0.3)]
    hw = w / 2 + A + 1.4
    zb = h + A + 0.8
    parts.append(M.hull_points([(x, zb, 0.0) for x in (-hw, hw)] + [(x, zb, 3.4) for x in (-hw, hw)] +
                               [(x, zb + 1.8, 0.0) for x in (-hw, hw)] + [(x, zb + 0.8, 3.4) for x in (-hw, hw)]))
    parts.append(box([-hw, h + A - 0.01, 0.0], [hw, zb + 0.01, 0.9]))
    for sg in (-1, 1):
        x = sg * (w / 2 + A * 0.5)
        for k in range(5):
            dw = 3.0 * math.cos(math.asin(min(1.0, (k + 0.5) / 5)))
            parts.append(box([x - 0.45, zb - (k + 1) * 0.5, 0.0], [x + 0.45, zb - k * 0.5 + 0.01, dw]))
    return O._one_piece(sash, parts, op, plug_cs, pl, zb + 1.8, 0.0)


def barge_cusped(L, slope, d_eave, skin=1.8, width=3.4, d=2.2):
    """The Ashcombe's bargeboards: a broad board whose lower edge is cut into a run of cusped
    arcs, a raised bead along its face, a square pendant under the apex ending in a ball and a
    short finial post over it, all tied through a king post (facade frame, v up from the eave;
    place at w = rake, prints face-up)."""
    from .gables import _text
    s = slope
    c = math.hypot(1.0, s)
    a_l, a_r = np.array([-d_eave, 0.0]), np.array([L + d_eave, 0.0])
    tip = np.array([L / 2, s * (L / 2 + d_eave)])
    depth = skin + width
    band, cuts, beads = [], [], []
    run = float(np.linalg.norm(tip - a_l))
    n_s = max(4, int(run / 3.0))
    for a in (a_l, a_r):
        n = np.array([s, -1.0]) / c if a[0] < L / 2 else np.array([-s, -1.0]) / c
        band.append(poly([tuple(a), tuple(tip), tuple(tip + n * depth), tuple(a + n * depth)]))
        dirv = (tip - a) / np.linalg.norm(tip - a)
        for k in range(1, n_s):
            p = a + dirv * (run * k / n_s)
            cuts.append(circle(tuple(p + n * (depth + 0.9)), 1.75, 24))
        beads.append(stroke([tuple(a + n * (skin + 1.0) + dirv * 2.0), tuple(tip + n * (skin + 1.0) - dirv * 1.5)], 0.5, caps=False))
    board = cs_union(band) ^ rect(-d_eave - 5, -0.01, L + d_eave + 5, tip[1] + 5)
    board = board - cs_union(cuts)
    board = board + rect(L / 2 - 1.2, tip[1] - depth * c - 0.8, L / 2 + 1.2, tip[1])
    board = cs_union([pc for pc in board.decompose() if pc.area() > 2.0])
    parts = [_text(board, 0.0, d), ext(cs_union(beads) ^ board.offset(-0.3, JoinType.Miter, 4.0), d - 0.05, d + 0.3)]
    ay = tip[1] - depth * c - 0.6
    pcs = cs_union([rect(L / 2 - 0.7, ay - 4.0, L / 2 + 0.7, ay + 0.4), rect(L / 2 - 1.1, ay - 1.6, L / 2 + 1.1, ay - 1.0),
                    poly([(L / 2 - 0.9, ay - 3.99), (L / 2 + 0.9, ay - 3.99), (L / 2, ay - 5.3)]), circle((L / 2, ay - 5.6), 0.65, 16)])
    parts.append(_text(pcs, 0.0, d + 0.3))
    fcs = cs_union([rect(L / 2 - 0.6, tip[1] - 0.6, L / 2 + 0.6, tip[1] + 2.6), rect(L / 2 - 1.0, tip[1] + 2.4, L / 2 + 1.0, tip[1] + 3.0),
                    circle((L / 2, tip[1] + 3.6), 0.75, 16)])
    parts.append(_text(fcs, 0.0, d + 0.3))
    return union(parts)


# ================================================================== the Capistrano (Mission Revival)
from . import porchwork as PW, features as FT                       # noqa: E402


def stucco_mission(region, datum=0.0, seed=3):
    """Hand-troweled mission plaster: a smooth coat whose surface swells in broad, soft,
    irregular patches (each a low plateau 0.15 proud with rounded edges), so paint and a wash
    catch it like old adobe (the Capistrano)."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    rng = np.random.default_rng(seed + int(abs(u0) * 3 + abs(v0)) % 97)
    out = M.extrude(region, 0.3)
    blobs = [oval((rng.uniform(u0, u1), rng.uniform(v0, v1)), rng.uniform(2.0, 5.0), rng.uniform(1.2, 2.8), 20)
             for _ in range(int((u1 - u0) * (v1 - v0) / 45.0) + 1)]
    if blobs:
        b = cs_union(blobs).offset(-0.4, JoinType.Round).offset(0.4, JoinType.Round) ^ region.offset(-0.4, JoinType.Miter, 4.0)
        out = out + ext(b, 0.25, 0.45)
    return out


def foundation_missionplinth(reg, seed=0):
    """A battered plaster plinth: a smooth base under a rounded water-table band, with square
    iron-grilled vents at intervals (the Capistrano)."""
    b = reg.bounds()
    out = [M.extrude(reg, 0.3)]
    vt = b[3] - 1.2
    out.append(ext(reg ^ rect(b[0] - 1, vt, b[2] + 1, b[3]), 0.2, 0.7))
    vents = []
    for u in np.arange(b[0] + 9.0, b[2] - 4.0, 18.0):
        vc = (b[1] + vt) / 2
        vr = rect(u - 1.6, vc - 1.3, u + 1.6, vc + 1.3)
        vents.append(ext((vr.offset(0.5, JoinType.Miter, 4.0) - vr) ^ reg, 0.2, 0.55))
        vents.append(ext(cs_union([rect(u + x - 0.2, vc - 1.3, u + x + 0.2, vc + 1.3) for x in (-0.8, 0.0, 0.8)]) ^ reg, 0.0, 0.35))
    return union(out + vents) - ext(cs_union([rect(u - 1.6, (b[1] + vt) / 2 - 1.3, u + 1.6, (b[1] + vt) / 2 + 1.3)
                                               for u in np.arange(b[0] + 9.0, b[2] - 4.0, 18.0)]) ^ reg, 0.05, 1.0) + union(vents[1::2])


def frieze_bellniches(L, h, b, pitch, margin, pair, half):
    """A row of little arched niches, each with a bell hanging in it, and between them a
    pair of lozenges (the Capistrano)."""
    v0, v1 = 0.6, h - 0.6
    hh = v1 - v0
    out = []
    wn = min(3.2, pitch * 0.26)
    for u in CO._us(L, pitch, margin, 0.0):
        nic = cs_union([rect(u - wn / 2, v0, u + wn / 2, v1 - wn / 2), circle((u, v1 - wn / 2), wn / 2, 20)])
        ring = nic.offset(0.45, JoinType.Round) - nic
        bell = cs_union([poly([(u - 0.5, v1 - wn / 2 - 0.3), (u + 0.5, v1 - wn / 2 - 0.3), (u + 1.0, v0 + hh * 0.3), (u - 1.0, v0 + hh * 0.3)]),
                         rect(u - 1.2, v0 + hh * 0.22, u + 1.2, v0 + hh * 0.32), circle((u, v0 + hh * 0.16), 0.35, 10)])
        out.append(_st(ring, b, 0.45))
        out.append(_st(bell ^ nic, b, 0.35))
    for uc, wd in CO._between(L, pitch, margin, pair, half + wn / 2 + 1.2):
        if wd < 2.6:
            continue
        loz = [poly([(uc + dx - 0.7, v0 + hh * 0.5), (uc + dx, v0 + hh * 0.5 + 1.0), (uc + dx + 0.7, v0 + hh * 0.5), (uc + dx, v0 + hh * 0.5 - 1.0)])
               for dx in ((-1.0, 1.0) if wd > 5.0 else (0.0,))]
        out.append(_st(cs_union(loz), b, 0.35))
    return out, []


def frieze_solomonic(L, h, b, pitch, margin, pair, half):
    """A blind arcade on barley-twist (Solomonic) colonnettes: at every station a short
    twisted column (a stack of slanted beads) on a base under a block; between them a round
    arch sprung from the blocks (the Capistrano)."""
    v0, v1 = 0.6, h - 0.6
    hh = v1 - v0
    out = []
    us = list(CO._us(L, pitch, margin, 0.0))
    for u in us:
        col = [rect(u - 0.7, v0, u + 0.7, v0 + 0.5), rect(u - 0.7, v1 - hh * 0.3, u + 0.7, v1 - hh * 0.3 + 0.5)]
        n = max(3, int((hh * 0.7 - 0.6) / 0.55))
        for k in range(n):
            y = v0 + 0.5 + (k + 0.5) * (hh * 0.7 - 1.0) / n
            col.append(stroke([(u - 0.45, y - 0.2), (u + 0.45, y + 0.2)], 0.42, caps=True))
        out.append(_st(cs_union(col), b, 0.45))
    for uc, wd in CO._between(L, pitch, margin, pair, half + 0.9):
        if wd < 3.0:
            continue
        r = wd / 2
        vs = v1 - hh * 0.3 + 0.5
        arc = cs_union([circle((uc, vs), r + 0.45, 32)]) - circle((uc, vs), r, 32)
        arc = arc ^ rect(uc - r - 1, vs, uc + r + 1, v1 + 0.2)
        out.append(_st(arc, b, 0.35))
    return out, []


def course_corbeltable(L, h, b, pitch, margin, p):
    """A Romanesque corbel table: little corbels at close centres with a round arch sprung
    between each pair."""
    sp = max(2.4, h * 1.6)
    n = max(1, int((L - 0.6) / sp))
    parts = [rect(0.3, h - 0.45, L - 0.3, h)]
    for k in range(n + 1):
        u = 0.3 + k * (L - 0.6) / n
        parts.append(rect(u - 0.35, 0.1, u + 0.35, h - 0.3))
    for k in range(n):
        ua, ub = 0.3 + k * (L - 0.6) / n, 0.3 + (k + 1) * (L - 0.6) / n
        r = (ub - ua) / 2 - 0.35
        c = ((ua + ub) / 2, h - 0.45 - r)
        parts.append((circle(c, r + 0.35, 20) - circle(c, r, 20)) ^ rect(ua, c[1], ub, h))
    return [ext(cs_union(parts), b - 0.05, b + 0.35)]


def course_crosslets(L, h, b, pitch, margin, p):
    """Little crosslets (each arm ending in a small bar) alternating with dots."""
    sp = max(2.6, h * 1.7)
    n = max(1, int((L - 0.6) / sp))
    parts = []
    for k in range(n):
        u = 0.3 + (k + 0.5) * (L - 0.6) / n
        vc = h / 2
        a = min(0.7, h * 0.36)
        if k % 2 == 0:
            parts += [rect(u - a, vc - 0.18, u + a, vc + 0.18), rect(u - 0.18, vc - a, u + 0.18, vc + a)]
            parts += [rect(u - a, vc - 0.32, u - a + 0.3, vc + 0.32), rect(u + a - 0.3, vc - 0.32, u + a, vc + 0.32),
                      rect(u - 0.32, vc - a, u + 0.32, vc - a + 0.3), rect(u - 0.32, vc + a - 0.3, u + 0.32, vc + a)]
        else:
            parts.append(circle((u, vc), 0.38, 12))
    return [ext(cs_union(parts), b - 0.05, b + 0.35)]


def bracket_ogeetail(h, d, t):
    """An exposed rafter tail cut to an ogee: a long rafter running out under the eave, its
    end sawn in a double curve (side profile, top at v = 0)."""
    hb = max(1.6, min(h, 2.6))
    pts = [(0.0, 0.0), (d, 0.0)]
    for a in np.linspace(0.0, 1.0, 10)[1:]:
        x = d - 0.9 * (0.5 - 0.5 * math.cos(math.pi * a))
        pts.append((x, -hb * a))
    pts += [(0.0, -hb)]
    return poly(pts)


CO.FRIEZE_EXTRA.update(bellniches=frieze_bellniches, solomonic=frieze_solomonic)
CO.COURSE_EXTRA.update(corbeltable=course_corbeltable, crosslets=course_crosslets)
TW.BRACKET_EXTRA.update(ogeetail=bracket_ogeetail)
TW.FOUNDATION_EXTRA.update(missionplinth=foundation_missionplinth)


def mission_parapet(L, h, step=10.0):
    """The shaped mission parapet (espadana) over a wall ``L`` long, as an outline in the
    facade frame (u from the parapet's left end, v up from the wall top): ogee shoulders
    rising to a stepped scroll each side, and a round-arched crest ``h`` high in the middle."""
    c = L / 2
    r_c = min(11.0, L * 0.16)
    right = []
    # from the crest's right foot down to the right end, then mirrored for the left
    right += [(c + r_c * math.cos(a), h - r_c + r_c * math.sin(a)) for a in np.linspace(math.pi / 2, 0.0, 14)]
    ys = h - r_c
    right += [(c + r_c, ys - 2.0), (c + r_c + 3.0, ys - 2.0)]
    x0, y0 = c + r_c + 3.0, ys - 2.0
    rs = 8.0
    right += [(x0 + rs * math.sin(a), y0 - rs + rs * math.cos(a)) for a in np.linspace(0.0, math.pi / 2, 10)][1:]
    x1, y1 = x0 + rs, y0 - rs
    right += [(x1, y1 - 2.0), (x1 + 4.0, y1 - 2.0)]
    x2, y2 = x1 + 4.0, y1 - 2.0
    xe = L
    for a in np.linspace(0.0, 1.0, 12)[1:]:
        right.append((x2 + (xe - x2) * a, y2 * (0.5 + 0.5 * math.cos(math.pi * a))))
    left = [(L - x, y) for (x, y) in reversed(right)]
    return poly(left + right + [(L, -1.0), (0.0, -1.0)])


def window_reja(w, h, A=1.4):
    """The Capistrano's ground-floor window: a round-arched casement pair of small panes set
    deep, a flat plaster band round the arch on a tiled sill, and in front a wrought-iron reja
    (grille) of upright bars bowed out on two rails, each bar ending in a curl under the arch,
    printed in iron colour (one change) above the frame."""
    op = O.opening_cs(w, h, w / 2)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    g = plug_cs.offset(-0.7, JoinType.Round)
    u0, v0, u1, v1 = g.bounds()
    mun = cs_union([rect(-0.25, v0 - 1, 0.25, v1 + 1)] + [rect(u0 - 1, v - 0.2, u1 + 1, v + 0.2) for v in np.linspace(v0, h - w / 2, 4)[1:-1]] +
                   [rect(x - 0.2, v0 - 1, x + 0.2, v1 + 1) for x in (u0 + (u1 - u0) / 4, u1 - (u1 - u0) / 4)])
    sash = _glazed([ext(plug_cs, -pl, -0.8)], g, pl, mun, plug_cs)
    band = (op.offset(A, JoinType.Round) - op) ^ rect(-w, 0.0, w, h + A + 1)
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, 0.6), ext(band, 0.0, 0.7)]
    parts.append(chamfer_box(-w / 2 - A - 1.0, -1.6, w / 2 + A + 1.0, 0.2, 0.0, 1.4, c=0.4, bottom=0.9))
    for x in np.arange(-w / 2 - A - 0.4, w / 2 + A + 0.6, 1.6):
        parts.append(ext(circle((x, -1.6), 0.55, 12) ^ rect(x - 1, -2.2, x + 1, -1.59), 0.0, 1.4))
    # the reja: a frame bar round the opening, uprights, two rails, curls under the arch
    wf, wi0, wi1 = 0.9, 0.8, 1.4
    frame = op.offset(0.5, JoinType.Round) - op.offset(-0.2, JoinType.Round)
    bars = [rect(x - 0.25, -0.2, x + 0.25, h) for x in np.linspace(-w / 2 + 1.6, w / 2 - 1.6, max(3, int(w / 2.2)))]
    rails = [rect(-w / 2, v - 0.25, w / 2, v + 0.25) for v in (h * 0.2, h - w / 2 - 0.6)]
    grid = (cs_union(bars + rails) ^ op.offset(-0.1, JoinType.Round))
    curls = []
    for x in np.linspace(-w / 4, w / 4, 2):
        cc = (x, h - w / 2 + w * 0.2)
        curls.append(circle(cc, 1.1, 20) - circle(cc, 0.6, 16))
    grille = cs_union([frame, grid] + curls) ^ op.offset(0.5, JoinType.Round)
    parts.append(ext(frame, 0.0, wi1))
    parts.append(ext(grille, wi0, wi1))
    return O._one_piece(sash, parts, op, plug_cs, pl, h + A + 1.0, -2.2)


def window_segmental(w, h, A=1.2):
    """The Capistrano's upper window: a casement pair under a segmental arch, four panes a
    leaf, in a plaster reveal band, on a stepped sill carried by two little corbels."""
    rise = w * 0.16
    op = O.opening_cs(w, h, rise)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    g = plug_cs.offset(-0.6, JoinType.Miter, 4.0)
    u0, v0, u1, v1 = g.bounds()
    mun = cs_union([rect(-0.3, v0 - 1, 0.3, v1 + 1), rect(u0 - 1, (v0 + v1) / 2 - 0.2, u1 + 1, (v0 + v1) / 2 + 0.2),
                    rect(u0 + (u1 - u0) / 4 - 0.2, v0 - 1, u0 + (u1 - u0) / 4 + 0.2, v1 + 1),
                    rect(u1 - (u1 - u0) / 4 - 0.2, v0 - 1, u1 - (u1 - u0) / 4 + 0.2, v1 + 1)])
    sash = _glazed([ext(plug_cs, -pl, -0.7)], g, pl, mun, plug_cs)
    band = (op.offset(A, JoinType.Miter, 4.0) - op) ^ rect(-w, 0.0, w, h + A + 1)
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, 0.6), ext(band, 0.0, 0.7)]
    kb = (op.offset(A + 0.1, JoinType.Miter, 4.0) ^ rect(-1.2, h - 1.0, 1.2, h + A + 0.6))
    parts.append(ext(kb, 0.0, 1.1))                                   # a keystone
    parts.append(chamfer_box(-w / 2 - A - 0.6, -0.8, w / 2 + A + 0.6, 0.2, 0.0, 1.2, c=0.35, bottom=0.7))
    parts.append(chamfer_box(-w / 2 - A - 0.2, -1.6, w / 2 + A + 0.2, -0.79, 0.0, 0.9, c=0.3))
    for sg in (-1, 1):
        x = sg * (w / 2 - 1.2)
        for k in range(4):
            parts.append(box([x - 0.5, -1.6 - (k + 1) * 0.5, 0.0], [x + 0.5, -1.6 - k * 0.5 + 0.01, 0.9 - k * 0.2]))
    return O._one_piece(sash, parts, op, plug_cs, pl, h + A + 0.6, -3.6)


def door_mission(w=12.0, h=24.0, A=2.4):
    """The Capistrano's front door, in two colours (one change): a round-arched plank leaf
    studded with rows of iron nails, a small arched grille window, set in a carved portal of
    Solomonic (barley-twist) columns on pedestals carrying a moulded archivolt with a keystone,
    and a shell in a panel over it."""
    W_ = w + 2.0
    op = rect(-W_ / 2, 0.0, W_ / 2, h)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    r = w / 2
    vs = h - r - 0.6
    arch = cs_union([rect(-r, 0.3, r, vs), circle((0.0, vs), r, 40) ^ rect(-r, vs, r, h)])
    body = [ext(plug_cs, -pl, -1.0)]
    boards = cs_union([rect(-r + k * w / 6 - 0.12, 0.0, -r + k * w / 6 + 0.12, h) for k in range(1, 6)])
    leaf = arch.offset(-0.2, JoinType.Miter, 4.0)
    body.append(ext(leaf - boards, -1.0, -0.6) + ext(leaf, -1.0, -0.8))
    studs = [rect(x - 0.22, v - 0.22, x + 0.22, v + 0.22) for v in (h * 0.12, h * 0.34, h * 0.56) for x in np.linspace(-r + 1.0, r - 1.0, 5)]
    body.append(ext(cs_union(studs) ^ leaf, -0.7, -0.4))
    gw = cs_union([rect(-1.5, h * 0.62, 1.5, h * 0.72), circle((0.0, h * 0.72), 1.5, 20)])
    body.append(ext(gw.offset(0.35, JoinType.Round) - gw, -0.7, -0.4))
    body.append(ext(cs_union([rect(x - 0.2, h * 0.62, x + 0.2, h * 0.72 + 1.4) for x in (-0.75, 0.0, 0.75)]) ^ gw, -0.8, -0.45))
    sash = body
    face = rect(-W_ / 2 - A, 0.0, W_ / 2 + A, h + A + 3.0)
    parts = [ext(op - arch.offset(0.6, JoinType.Miter, 4.0), -pl, 0.0), ext(face - arch, 0.0, 0.7)]
    archi = (arch.offset(1.2, JoinType.Round) - arch.offset(0.3, JoinType.Round)) ^ rect(-w, vs, w, h + 3)
    parts.append(ext(archi, 0.6, 1.2))
    parts.append(ext(rect(-0.9, vs + r - 0.2, 0.9, vs + r + 2.0) - arch, 0.6, 1.5))              # keystone
    for sg in (-1, 1):                                    # the Solomonic columns on pedestals
        x = sg * (W_ / 2 + A / 2)
        parts.append(chamfer_box(x - A / 2 - 0.2, 0.0, x + A / 2 + 0.2, 4.0, 0.0, 1.8, c=0.3))
        col = M.extrude(_star(0.95, 0.6, k=4), vs - 5.4, 20, 360.0).rotate([-90, 0, 0]).translate([x, 4.0, 0.9])
        col = col ^ box([x - 2, 4.0, 0.0], [x + 2, vs - 1.4, 2.0])
        parts.append(col + box([x - 1.0, 3.99, 0.0], [x + 1.0, 4.4, 0.9]) + box([x - 1.0, vs - 1.8, 0.0], [x + 1.0, vs - 1.39, 0.9]))
        parts.append(chamfer_box(x - A / 2 - 0.2, vs - 1.4, x + A / 2 + 0.2, vs, 0.0, 1.8, c=0.3))
    # a shell in a panel over the arch
    pv = h + A + 1.4
    parts.append(chamfer_box(-3.2, h + 0.4, 3.2, pv + 1.4, 0.0, 0.9, c=0.3))
    fan = cs_union([stroke([(0.0, h + 1.0), (2.4 * math.cos(a), h + 1.0 + 2.4 * math.sin(a))], 0.35, caps=True)
                    for a in np.linspace(math.pi * 0.12, math.pi * 0.88, 7)])
    parts.append(ext(fan, 0.85, 1.2))
    parts.append(chamfer_box(-W_ / 2 - A - 0.4, h + A + 2.8, W_ / 2 + A + 0.4, h + A + 3.8, 0.0, 1.6, c=0.4, bottom=0.8))
    return O._one_piece(sash, parts, op, plug_cs, pl, h + A + 3.8, 0.0)


def door_plankarch(w=9.0, h=21.0, A=1.4):
    """The Capistrano's back door: a segmental-arched leaf of diagonal boards (herringbone
    halves) with a small square light, in a plain plaster reveal under a little shed hood of
    tile on two rafter tails."""
    rise = w * 0.18
    op = O.opening_cs(w, h, rise)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    leaf = plug_cs.offset(-0.3, JoinType.Miter, 4.0)
    u0, v0, u1, v1 = leaf.bounds()
    win = rect(-1.6, v1 - rise - 4.6, 1.6, v1 - rise - 1.4)
    grooves = cs_union([_stripes(leaf ^ rect(u0, v0, 0.0, v1), math.radians(45), 1.6, 0.24),
                        _stripes(leaf ^ rect(0.0, v0, u1, v1), math.radians(135), 1.6, 0.24), rect(-0.14, v0, 0.14, v1)])
    body = [ext(plug_cs, -pl, -1.0), ext(leaf - grooves - win, -1.0, -0.6), ext(leaf - win, -1.0, -0.8)]
    sash = _glazed(body, win, pl, rect(-0.2, v0, 0.2, v1) ^ win.offset(0.1, JoinType.Miter, 4.0), plug_cs)
    band = (op.offset(A, JoinType.Miter, 4.0) - op) ^ rect(-w, 0.0, w, h + A + 1)
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, 0.6), ext(band, 0.0, 0.7)]
    hw = w / 2 + A + 1.6
    zb = h + A + 0.6
    parts.append(M.hull_points([(x, zb, 0.0) for x in (-hw, hw)] + [(x, zb, 3.6) for x in (-hw, hw)] +
                               [(x, zb + 1.8, 0.0) for x in (-hw, hw)] + [(x, zb + 0.9, 3.6) for x in (-hw, hw)]))
    parts.append(ext(cs_union([circle((x, zb + 0.5), 0.5, 12) for x in np.arange(-hw + 0.6, hw - 0.3, 1.4)]) ^ rect(-hw, zb, hw, zb + 1.1), 3.4, 3.9))
    for sg in (-1, 1):
        x = sg * (w / 2 + A * 0.5)
        parts.append(box([x - 0.45, zb - 3.0, 0.0], [x + 0.45, zb + 0.01, 3.0]))
    return O._one_piece(sash, parts, op, plug_cs, pl, zb + 1.8, 0.0)


def post_capistrano(h, collar=None, abacus=3.4, slot=None):
    """A mission arcade column: a square plinth and a torus base, a plain round shaft with a
    gentle entasis, an astragal, and a capital that flares to a broad square impost block."""
    zt = h - 2.6
    body = PW._plinth(3.6, 1.0)
    body = body + PW._revolve([(0.0, 0.99), (1.6, 0.99), (1.6, 1.5), (1.3, 2.0), (1.35, zt * 0.35), (1.2, zt - 0.6),
                               (1.4, zt - 0.6), (1.4, zt - 0.2), (1.2, zt), (0.0, zt)], 32)
    return body + PW._top(h, abacus / 2, zt - 0.01, 1.2, slot, shape="round")


def fill_quatrefoils(L, vb, vt):
    """A low solid plaster wall between the columns, pierced with a row of quatrefoils."""
    board = rect(0.0, vb, L, vt)
    H = vt - vb
    if H < 4.0:
        return [board]
    r = min(0.9, H * 0.14)
    holes = []
    n = max(1, int(L / 5.0))
    for k in range(n):
        c = (L * (k + 0.5) / n, (vb + vt) / 2)
        holes.append(cs_union([circle((c[0] + dx, c[1] + dy), r, 16) for dx, dy in ((r, 0), (-r, 0), (0, r), (0, -r))]))
    return [board - cs_union(holes)]


def frieze_missionarch(u0, u1, v_bot, v_top):
    """A round arch between two columns: a plaster spandrel down to the imposts, the arch
    cut clean with a pier strip either side so no tip is thin."""
    L = u1 - u0
    r = L / 2 - 1.0
    c = ((u0 + u1) / 2, v_bot + 1.0)
    sp = rect(u0, v_bot, u1, v_top + 0.05)
    return sp - cs_union([circle(c, r, 40), rect(c[0] - r, v_bot - 1.0, c[0] + r, c[1])])


def edge_tileends(L, z0, zc):
    """Porch roof edge: the round ends of the cover tiles over a narrow fascia."""
    xs = np.arange(1.1, L - 0.6, 2.2)
    return rect(0.3, zc - 0.6, L - 0.3, zc) + cs_union([circle((x, zc - 0.6), 0.8, 14) ^ rect(x - 1, zc - 1.4, x + 1, zc - 0.59) for x in xs]), 0.9


def skirt_archvent(reg, d=1.2):
    """A plaster porch skirt with a little arched vent (three iron bars) in every bay."""
    if reg.is_empty():
        return M()
    u0, v0, u1, v1 = reg.bounds()
    body = M.extrude(reg, d * 0.6)
    vm = (v0 + v1) / 2
    vents, bars = [], []
    for u in np.arange(u0 + 7.0, u1 - 3.0, 14.0):
        vc = cs_union([rect(u - 1.4, vm - 1.2, u + 1.4, vm + 0.4), circle((u, vm + 0.4), 1.4, 16)])
        vents.append(vc)
        bars += [rect(u + x - 0.2, vm - 1.2, u + x + 0.2, vm + 1.8) for x in (-0.7, 0.0, 0.7)]
    if vents:
        body = body - ext(cs_union(vents) ^ reg, d * 0.25, d) + ext((cs_union(bars) ^ cs_union(vents)) ^ reg, d * 0.25, d * 0.5)
    return body


PW.POSTS.update(capistrano=post_capistrano)
PW.FILLS.update(quatrefoils=fill_quatrefoils)
PW.FRIEZES.update(missionarch=frieze_missionarch)
PW.SKIRTS.update(archvent=skirt_archvent)
FT.EDGE_EXTRA.update(tileends=edge_tileends)


def chimney_mission(w=11.0, d=11.0, h=30.0):
    """The Capistrano's stack: plain plaster with a band two thirds up, crowned by a little
    arcaded hood (a round arch on each face) under a low tiled pyramid cap."""
    h = round(h / 0.2) * 0.2
    zt = h - 7.0
    body = box([-w / 2, -d / 2, 0.0], [w / 2, d / 2, zt])
    zb = round(zt * 0.66 / 0.2) * 0.2
    body = body + box([-w / 2 - 0.5, -d / 2 - 0.5, zb], [w / 2 + 0.5, d / 2 + 0.5, zb + 0.8])
    body = body + box([-w / 2 - 0.6, -d / 2 - 0.6, zt - 0.01], [w / 2 + 0.6, d / 2 + 0.6, zt + 0.8])
    hood = box([-w / 2, -d / 2, zt + 0.79], [w / 2, d / 2, zt + 4.6])
    for ax in (0, 1):
        a = cs_union([rect(-1.6, 0.0, 1.6, 2.0), circle((0.0, 2.0), 1.6, 20)])
        cut = M.extrude(a, max(w, d) + 2).translate([0, 0, -(max(w, d) + 2) / 2]).rotate([90, 0, 90 * ax]).translate([0, 0, zt + 0.8])
        hood = hood - cut
    hood = hood - box([-w / 2 + 1.4, -d / 2 + 1.4, zt + 0.5], [w / 2 - 1.4, d / 2 - 1.4, zt + 4.0])
    cap = M.hull_points([(x * (w / 2 + 1.0), y * (d / 2 + 1.0), zt + 4.59) for x in (-1, 1) for y in (-1, 1)] +
                        [(x * (w / 2 + 1.0), y * (d / 2 + 1.0), zt + 5.2) for x in (-1, 1) for y in (-1, 1)] + [(0.0, 0.0, h)])
    return body + hood + cap


def bell_hung(span, r=3.0, hb=4.6, bar=1.6):
    """A mission bell on its bar: a square bar ``span`` long (its ends drop into slots in the
    belfry's jambs), a headstock, and a bell with a crown and a flared lip. Local: the bar
    along x centred on 0, its top at z = 0."""
    out = box([-span / 2, -bar / 2, -bar], [span / 2, bar / 2, 0.0])
    out = out + box([-1.2, -0.8, -bar - 0.8], [1.2, 0.8, -bar + 0.01])
    z0 = -bar - 0.8
    prof = [(0.0, 0.01), (1.3, 0.01), (1.35, -0.6), (1.6, -1.2), (2.2, -hb + 1.2), (r - 0.2, -hb + 0.5), (r, -hb), (0.0, -hb)]
    bell = M.revolve(poly([(x, -y) for (x, y) in prof]), 40).mirror([0, 0, 1]).translate([0, 0, z0])
    return out + bell

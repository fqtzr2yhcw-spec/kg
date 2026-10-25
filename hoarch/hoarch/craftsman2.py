"""Craftsman-era parts, volume two (houses 54 to 60 of the fifth batch). Like ``craftsman``, the
module registers its cornice ornaments, brackets and foundations with ``cornice`` and
``trimwork`` on import, and no part is shared with another building: each section below
belongs to one house.
"""
import math

import numpy as np
from manifold3d import JoinType, Manifold as M

from .core import RIB, box, circle, cs_union, poly, rect, slab, union
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


def tudor_arch(w, vs, rise, r_frac=0.4, n=14, phi=math.radians(50)):
    """A four-centred (Tudor) arch opening ``w`` wide, springing at ``vs`` and rising ``rise``:
    a tight arc at each springing (radius r_frac of the half-width) turning, at ``phi``, into a
    long flat arc struck from a centre below and across, the two flat arcs meeting in a
    shallow point at the crown."""
    a = w / 2
    r1 = a * r_frac
    c1 = np.array([-a + r1, vs])
    d = np.array([math.cos(phi), -math.sin(phi)])

    def miss(r2):
        c2 = c1 + (r2 - r1) * d
        return math.hypot(c2[0], vs + rise - c2[1]) - r2
    lo, hi = r1 * 1.001, a * 60.0
    for _ in range(80):
        mid = (lo + hi) / 2
        if miss(mid) > 0:
            lo = mid
        else:
            hi = mid
    r2 = (lo + hi) / 2
    c2 = c1 + (r2 - r1) * d
    psi = math.atan2(vs + rise - c2[1], -(0.0 - c2[0]))
    left = [tuple(c1 + r1 * np.array([-math.cos(t), math.sin(t)])) for t in np.linspace(0.0, phi, n)]
    left += [tuple(c2 + r2 * np.array([-math.cos(t), math.sin(t)])) for t in np.linspace(phi, psi, n)][1:]
    left[-1] = (0.0, vs + rise)
    right = [(-x, y) for (x, y) in reversed(left[:-1])]
    return poly([(-a, 0.0)] + left + right + [(a, 0.0)])


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
    bars = cs_union([O.lozenges(l_, ang=64.0) for l_ in lights])      # quarries fitted to each light, 0.9 mm leads
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
    arch = tudor_arch(w, vs, 3.2) ^ rect(-w, 0.3, w, h)
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
    """Hand-troweled mission plaster: a smooth coat whose surface swells in small, soft,
    irregular patches (each a low plateau barely 0.1 proud with rounded edges), so a wash
    catches it like old adobe (the Capistrano)."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    rng = np.random.default_rng(seed + int(abs(u0) * 3 + abs(v0)) % 97)
    out = M.extrude(region, 0.3)
    blobs = [oval((rng.uniform(u0, u1), rng.uniform(v0, v1)), rng.uniform(1.4, 3.2), rng.uniform(0.7, 1.6), 16)
             for _ in range(int((u1 - u0) * (v1 - v0) / 22.0) + 1)]
    if blobs:
        b = cs_union(blobs).offset(-0.3, JoinType.Round).offset(0.3, JoinType.Round) ^ region.offset(-0.4, JoinType.Miter, 4.0)
        out = out + ext(b, 0.25, 0.37)
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


# ================================================================== the Kittredge (airplane bungalow)
def siding_channel(region, datum=0.0, pitch=1.9):
    """Channel-rustic siding: square-edged boards set flat, a wide flat-bottomed channel
    between each pair (the Kittredge)."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    out = M.extrude(region, 0.4)
    k0 = math.floor((v0 - datum) / pitch) - 1
    ch = [rect(u0 - 1, datum + k * pitch - 0.25, u1 + 1, datum + k * pitch + 0.25) for k in range(k0, k0 + int((v1 - v0) / pitch) + 4)]
    return out - ext(cs_union(ch) ^ region, 0.15, 1.0)


def boardbatten(region, pitch=2.8):
    """Board-and-batten for the gable fields: flat boards with a narrow batten over every
    joint."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    bat = cs_union([rect(u - 0.3, v0 - 1, u + 0.3, v1 + 1) for u in np.arange(u0 + pitch / 2, u1, pitch)])
    return M.extrude(region, 0.3) + ext(bat ^ region, 0.0, 0.75)


def foundation_tapestry(reg, seed=0):
    """Tapestry (rug) brick: running bond, some bricks set proud and some sunk at random, a
    few with a scratched rug face (the Kittredge)."""
    b = reg.bounds()
    rng = np.random.default_rng(seed + 401)
    bl, bh = 2.6, 0.85
    out = M.extrude(reg, 0.35)
    beds = [rect(b[0] - 1, v - 0.12, b[2] + 1, v + 0.12) for v in np.arange(b[1], b[3] + bh, bh)]
    heads, proud, sunk = [], [], []
    for k, v in enumerate(np.arange(b[1], b[3], bh)):
        for u in np.arange(b[0] - bl + (k % 2) * bl / 2, b[2] + bl, bl):
            heads.append(rect(u - 0.12, v, u + 0.12, v + bh))
            r = rng.random()
            br = rect(u + 0.14, v + 0.14, u + bl - 0.14, v + bh - 0.14)
            if r < 0.14:
                proud.append(br)
            elif r < 0.24:
                sunk.append(br)
    out = out - ext(cs_union(beds + heads) ^ reg, 0.2, 1.0)
    if proud:
        out = out + ext(cs_union(proud) ^ reg, 0.3, 0.5)
    if sunk:
        out = out - ext(cs_union(sunk) ^ reg, 0.25, 1.0)
    return out


def frieze_wingchevrons(L, h, b, pitch, margin, pair, half):
    """Winged roundels: at every station a disc between two swept-back wings of three
    feathers each; long thin speed lines between them (the Kittredge)."""
    v0, v1 = 0.6, h - 0.6
    hh = v1 - v0
    out = []
    vc = v0 + hh / 2
    for u in CO._us(L, pitch, margin, 0.0):
        parts = [circle((u, vc), min(0.95, hh * 0.3), 20)]
        for sg in (-1, 1):
            for j in range(3):
                y = vc + (0.45 - j * 0.45) * hh * 0.45
                parts.append(stroke([(u + sg * 1.1, vc + (0.3 - j * 0.3) * 0.5), (u + sg * (2.6 - j * 0.35), y + 0.25)], 0.38, caps=True))
        out.append(_st(cs_union(parts), b, 0.45))
    for uc, wd in CO._between(L, pitch, margin, pair, half + 3.0):
        if wd < 2.0:
            continue
        out.append(_st(cs_union([rect(uc - wd / 2, vc - 0.8, uc + wd / 2, vc - 0.45), rect(uc - wd / 2 + 0.8, vc + 0.45, uc + wd / 2 - 0.8, vc + 0.8)]), b, 0.3))
    return out, []


def frieze_risingsun(L, h, b, pitch, margin, pair, half):
    """Rising suns: at every station a half disc on the frieze's foot with short rays fanned
    over it; a plain level bar between them (the Kittredge)."""
    v0, v1 = 0.6, h - 0.6
    hh = v1 - v0
    out = []
    for u in CO._us(L, pitch, margin, 0.0):
        r = min(1.3, hh * 0.35)
        disc = circle((u, v0), r, 24) ^ rect(u - r - 1, v0, u + r + 1, v0 + r + 1)
        rays = [stroke([(u + (r + 0.35) * math.cos(a), v0 + (r + 0.35) * math.sin(a)), (u + (hh - 0.1) * math.cos(a), v0 + (hh - 0.1) * math.sin(a))], 0.34, caps=False)
                for a in np.linspace(math.pi * 0.12, math.pi * 0.88, 5)]
        out.append(_st(cs_union([disc] + rays) ^ rect(u - hh * 1.2, v0, u + hh * 1.2, v1), b, 0.45))
    for uc, wd in CO._between(L, pitch, margin, pair, half + 3.2):
        if wd < 2.0:
            continue
        out.append(_st(rect(uc - wd / 2, v0 + hh * 0.35, uc + wd / 2, v0 + hh * 0.35 + 0.45), b, 0.3))
    return out, []


def course_rivets(L, h, b, pitch, margin, p):
    """Two thin lines with a row of round rivet heads between them."""
    parts = [rect(0.3, 0.1, L - 0.3, 0.4), rect(0.3, h - 0.4, L - 0.3, h - 0.1)]
    heads = [circle((u, h / 2), min(0.36, h * 0.24), 12) for u in np.arange(1.0, L - 0.6, 1.5)]
    return [ext(cs_union(parts), b - 0.05, b + 0.3), ext(cs_union(heads), b - 0.05, b + 0.42)]


def bracket_notchtail(h, d, t):
    """An exposed rafter tail with a square notch cut from the underside of its end, the end
    itself cut plumb (side profile, top at v = 0)."""
    hb = max(1.6, min(h, 2.4))
    return poly([(0.0, 0.0), (d, 0.0), (d, -hb * 0.5), (d - 0.8, -hb * 0.5), (d - 0.8, -hb * 0.72), (d - 1.3, -hb),
                 (0.0, -hb)])


CO.FRIEZE_EXTRA.update(wingchevrons=frieze_wingchevrons, risingsun=frieze_risingsun)
CO.COURSE_EXTRA.update(rivets=course_rivets)
TW.BRACKET_EXTRA.update(notchtail=bracket_notchtail)
TW.FOUNDATION_EXTRA.update(tapestry=foundation_tapestry)


def gable_louver(w, h):
    """A triangular louvered attic vent (its outline and slats as one relief) for a gable
    field, apex at (0, h), foot at v = 0."""
    tri = poly([(-w / 2, 0.0), (w / 2, 0.0), (0.0, h)])
    rim = tri - tri.offset(-0.8, JoinType.Miter, 4.0)
    slats = cs_union([rect(-w, v, w, v + 0.45) for v in np.arange(0.9, h - 1.2, 1.0)]) ^ tri.offset(-0.8, JoinType.Miter, 4.0)
    return ext(rim, 0.0, 1.0) + ext(slats, 0.0, 0.7) - ext(tri.offset(-0.8, JoinType.Miter, 4.0), 0.5, 2.0) + ext(slats, 0.0, 0.7)


def purlin_end(L=8.0, s=1.4):
    """An outrigger purlin's end under a rake: a square beam running out ``L`` with a plumb
    end cut with a notch, carried back to the wall on a 45 degree underside so it prints on
    its wall. Local: u across (centred), v up (top at v = 0), w out from the wall."""
    prof = poly([(0.0, 0.0), (L, 0.0), (L, -s * 0.55), (L - 0.6, -s * 0.55), (L - 0.6, -s), (L - 0.6 - (L - 0.6), -s - (L - 0.6))])
    prof = prof ^ rect(-1.0, -s - L, L + 1.0, 0.01)
    return M.extrude(prof, s).transform(np.array([[0, 0, 1.0, -s / 2], [0, 1.0, 0, 0], [1.0, 0, 0, 0]]))


def window_diamondtop(w, h, n=2, A=1.4):
    """The Kittredge's window: ``n`` double-hung sashes side by side, each upper sash with a
    band of small diamonds across its top and a single pane below them, the lower sash one
    pane; flat casings with a head of a broad board under a moulded cap with a dentil row,
    and a lugged sill."""
    op = O.opening_cs(w, h, 0)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    u0, v0, u1, v1 = plug_cs.offset(-0.5, JoinType.Miter, 4.0).bounds()
    mull = 1.1
    cw = (u1 - u0 - (n - 1) * mull) / n
    vm = v0 + (v1 - v0) * 0.46
    lights, bars = [], []
    for j in range(n):
        a = u0 + j * (cw + mull)
        lights.append(rect(a, v0, a + cw, v1))
        bars.append(rect(a - 1, vm - 0.35, a + cw + 1, vm + 0.35))                      # meeting rail
        vd = v1 - min(3.2, (v1 - v0) * 0.2)
        bars.append(rect(a - 1, vd - 0.2, a + cw + 1, vd + 0.2))
        k = max(2, int(round(cw / 1.8)))
        for i in range(k):
            x = a + cw * (i + 0.5) / k
            dw, dh = cw / k / 2, (v1 - vd) / 2
            dm = poly([(x - dw, vd + dh), (x, v1), (x + dw, vd + dh), (x, vd)])
            bars.append(dm - dm.offset(-0.4, JoinType.Miter, 4.0))
    g = cs_union(lights)
    sash = _glazed([ext(plug_cs, -pl, -0.6)], g, pl, cs_union(bars), plug_cs)
    for j in range(1, n):
        a = u0 + j * (cw + mull) - mull
        sash.append(ext(rect(a, v0, a + mull, v1), -pl, 0.3))
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, 0.7),
             ext((op.offset(A, JoinType.Miter, 4.0) - op) ^ rect(-w, 0.0, w, h + A), 0.0, 0.6)]
    hw = w / 2 + A
    parts.append(ext(rect(-hw - 0.4, h + A - 0.01, hw + 0.4, h + A + 2.2), 0.0, 0.8))
    parts.append(ext(cs_union([rect(x - 0.3, h + A + 2.19, x + 0.3, h + A + 2.8) for x in np.arange(-hw, hw + 0.1, 1.1)]), 0.0, 1.0))
    parts.append(chamfer_box(-hw - 1.2, h + A + 2.79, hw + 1.2, h + A + 3.6, 0.0, 1.4, c=0.35, bottom=0.8))
    parts.append(chamfer_box(-hw - 1.0, -1.1, hw + 1.0, 0.2, 0.0, 1.4, c=0.4, bottom=0.8))
    parts.append(ext(rect(-hw + 0.2, -2.0, hw - 0.2, -1.09), 0.0, 0.7))                   # the apron
    return O._one_piece(sash, parts, op, plug_cs, pl, h + A + 3.6, -2.0)


def window_cockpit(w, h, n=3, A=1.1):
    """The cockpit's ribbon: ``n`` casements, each with three tall lights across its top
    over one big pane, slim mullions, one flat casing round the ribbon on a plain sill."""
    op = O.opening_cs(w, h, 0)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    u0, v0, u1, v1 = plug_cs.offset(-0.5, JoinType.Miter, 4.0).bounds()
    mull = 0.9
    cw = (u1 - u0 - (n - 1) * mull) / n
    vt = v1 - (v1 - v0) * 0.3
    bars = []
    for j in range(n):
        a = u0 + j * (cw + mull)
        bars.append(rect(a - 1, vt - 0.2, a + cw + 1, vt + 0.2))
        for k in (1, 2):
            x = a + cw * k / 3
            bars.append(rect(x - 0.2, vt, x + 0.2, v1 + 1))
    g = cs_union([rect(u0 + j * (cw + mull), v0, u0 + j * (cw + mull) + cw, v1) for j in range(n)])
    sash = _glazed([ext(plug_cs, -pl, -0.6)], g, pl, cs_union(bars), plug_cs)
    for j in range(1, n):
        a = u0 + j * (cw + mull) - mull
        sash.append(ext(rect(a, v0, a + mull, v1), -pl, 0.3))
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, 0.6),
             ext((op.offset(A, JoinType.Miter, 4.0) - op) ^ rect(-w, 0.0, w, h + A), 0.0, 0.6),
             chamfer_box(-w / 2 - A - 0.8, h + A - 0.01, w / 2 + A + 0.8, h + A + 1.0, 0.0, 1.1, c=0.3, bottom=0.6),
             chamfer_box(-w / 2 - A - 0.8, -1.0, w / 2 + A + 0.8, 0.2, 0.0, 1.2, c=0.35, bottom=0.7)]
    return O._one_piece(sash, parts, op, plug_cs, pl, h + A + 1.0, -1.0)


def door_steplight(w=11.0, h=24.0, side=3.2, A=1.6):
    """The Kittredge's front door: a leaf with three lights stepped like a stair over a
    dentil shelf and two tall panels, between sidelights (a light over a panel), under a
    broad head casing whose ends are cut as corbels."""
    W_ = w + 2 * side
    op = rect(-W_ / 2, 0.0, W_ / 2, h)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    body = [ext(plug_cs, -pl, -1.0)]
    u0, u1 = -w / 2 + 0.2, w / 2 - 0.2
    body.append(ext(rect(u0, 0.4, u1, h - 0.3), -1.0, -0.7))
    lw = (u1 - u0 - 2.4) / 3
    glass = []
    for k in range(3):
        a = u0 + 0.6 + k * (lw + 0.6)
        top = h - 1.0 - (2 - k) * 1.4
        glass.append(rect(a, h * 0.58, a + lw, top))
    shelf_v = h * 0.58 - 0.8
    body.append(chamfer_box(u0 + 0.3, shelf_v - 0.3, u1 - 0.3, shelf_v + 0.5, -0.7, 0.8, c=0.25))
    body.append(ext(cs_union([rect(x - 0.25, shelf_v - 0.9, x + 0.25, shelf_v - 0.3) for x in np.arange(u0 + 0.8, u1 - 0.5, 1.0)]), -0.7, -0.3))
    for (a, e) in ((u0 + 0.8, -0.4), (0.4, u1 - 0.8)):
        body.append(chamfer_box(a, 1.2, e, shelf_v - 1.4, -0.7, 0.35, c=0.2))
    for sg in (-1, 1):
        a, e = sorted((sg * (w / 2 + 0.3), sg * (W_ / 2 - O.CLR - 0.4)))
        glass.append(rect(a, h * 0.45, e, h - 1.0))
        body.append(chamfer_box(a, 0.8, e, h * 0.45 - 0.6, -1.0, 0.45, c=0.2))
    sash = _glazed(body, cs_union(glass), pl, None, plug_cs)
    sash.append(ext(cs_union([rect(-w / 2 - 0.3, 0.3, -w / 2 + 0.2, h), rect(w / 2 - 0.2, 0.3, w / 2 + 0.3, h)]) ^ plug_cs, -pl, -0.4))
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, 0.7),
             ext((op.offset(A, JoinType.Miter, 4.0) - op) ^ rect(-W_, 0.0, W_, h + A), 0.0, 0.7)]
    hw = W_ / 2 + A
    head = poly([(-hw - 1.6, h + A + 0.6), (-hw - 1.6, h + A + 3.0), (hw + 1.6, h + A + 3.0), (hw + 1.6, h + A + 0.6),
                 (hw + 0.4, h + A - 0.01), (-hw - 0.4, h + A - 0.01)])
    parts.append(ext(head, 0.0, 1.0))
    parts.append(chamfer_box(-hw - 2.0, h + A + 2.99, hw + 2.0, h + A + 3.8, 0.0, 1.5, c=0.35, bottom=0.8))
    return O._one_piece(sash, parts, op, plug_cs, pl, h + A + 3.8, 0.0)


def door_halflight(w=9.0, h=21.0, A=1.2):
    """The Kittredge's back door: four lights over a crossbar and three flat panels, in a
    plain casing with a drip cap."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    leaf = plug_cs.offset(-0.3, JoinType.Miter, 4.0)
    u0, v0, u1, v1 = leaf.bounds()
    win = rect(u0 + 0.9, v1 - (v1 - v0) * 0.42, u1 - 0.9, v1 - 0.9)
    body = [ext(plug_cs, -pl, -1.0), ext(leaf - win, -1.0, -0.6)]
    for k in range(3):
        a = u0 + 0.9 + k * (u1 - u0 - 1.8) / 3
        body.append(chamfer_box(a + 0.2, v0 + 1.0, a + (u1 - u0 - 1.8) / 3 - 0.2, v1 - (v1 - v0) * 0.42 - 1.4, -0.6, 0.3, c=0.15))
    wb = win.bounds()
    bars = cs_union([rect((wb[0] + wb[2]) / 2 - 0.2, wb[1] - 1, (wb[0] + wb[2]) / 2 + 0.2, wb[3] + 1),
                     rect(wb[0] - 1, (wb[1] + wb[3]) / 2 - 0.2, wb[2] + 1, (wb[1] + wb[3]) / 2 + 0.2)])
    sash = _glazed(body, win, pl, bars, plug_cs)
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, 0.7),
             ext((op.offset(A, JoinType.Miter, 4.0) - op) ^ rect(-w, 0.0, w, h + A), 0.0, 0.7),
             chamfer_box(-w / 2 - A - 0.8, h + A - 0.01, w / 2 + A + 0.8, h + A + 1.0, 0.0, 1.3, c=0.35, bottom=0.7)]
    return O._one_piece(sash, parts, op, plug_cs, pl, h + A + 1.0, 0.0)


def post_kittredge(h, collar=None, abacus=4.2, slot=None):
    """Twin columns on one pier: a square pedestal with a bevelled cap, two slim round shafts
    tapering side by side, and one broad cap block over both."""
    ped = min(10.0, h * 0.38)
    zt = h - 2.0
    body = PW._plinth(4.2, 1.2) + box([-2.0, -2.0, 1.19], [2.0, 2.0, ped - 0.7])
    body = body + M.hull_points([(x * 2.0, y * 2.0, ped - 0.71) for x in (-1, 1) for y in (-1, 1)] +
                                [(x * 2.2, y * 2.2, ped - 0.2) for x in (-1, 1) for y in (-1, 1)])
    body = body + box([-2.2, -2.2, ped - 0.21], [2.2, 2.2, ped])
    for sg in (-1, 1):
        body = body + PW._revolve([(0.0, ped - 0.01), (0.95, ped - 0.01), (0.72, zt), (0.0, zt)], 24).translate([sg * 1.1, 0, 0])
    body = body + box([-2.1, -1.2, zt - 0.4], [2.1, 1.2, zt + 0.4])
    return body + PW._top(h, abacus / 2, zt + 0.39, 1.2, slot, shape="square")


def fill_pairsticks(L, vb, vt):
    """A railing of square sticks set in pairs between a top and a bottom rail."""
    parts = [rect(0.0, vb, L, vb + 1.0), rect(0.0, vt - 1.2, L, vt)]
    n = max(1, int(L / 3.4))
    for k in range(n):
        c = L * (k + 0.5) / n
        for dx in (-0.55, 0.55):
            parts.append(rect(c + dx - 0.3, vb, c + dx + 0.3, vt))
    return parts


def frieze_joistbeam(u0, u1, v_bot, v_top):
    """A deep porch beam with the square ends of the ceiling joists showing along its top."""
    v0 = v_top - 2.6
    beam = rect(u0, v0, u1, v_top + 0.05)
    L = u1 - u0
    heads = cs_union([rect(u - 0.45, v_top - 0.9, u + 0.45, v_top + 0.05) for u in np.arange(u0 + 1.2, u1 - 0.8, 2.4)])
    return (beam - rect(u0 + 0.6, v_top - 1.3, u1 - 0.6, v_top - 1.0)) + heads + rect(u0, v0 - 0.5, u0 + min(2.0, L * 0.12), v0 + 0.01) + \
        rect(u1 - min(2.0, L * 0.12), v0 - 0.5, u1, v0 + 0.01)


def edge_notchfascia(L, z0, zc):
    """Porch fascia with small V notches along its lower edge."""
    band = rect(0.3, zc - 1.1, L - 0.3, zc)
    notches = cs_union([poly([(x - 0.45, zc - 1.11), (x + 0.45, zc - 1.11), (x, zc - 0.5)]) for x in np.arange(1.5, L - 1.0, 2.0)])
    return band - notches, 0.7


def skirt_soldierbrick(reg, d=1.2):
    """A brick porch skirt: panels of running bond framed by a soldier course on top."""
    if reg.is_empty():
        return M()
    u0, v0, u1, v1 = reg.bounds()
    body = M.extrude(reg, d * 0.55)
    beds = cs_union([rect(u0 - 1, v - 0.1, u1 + 1, v + 0.1) for v in np.arange(v0 + 0.85, v1 - 2.4, 0.85)])
    sold = cs_union([rect(u - 0.1, v1 - 2.4, u + 0.1, v1) for u in np.arange(u0, u1, 0.9)] + [rect(u0 - 1, v1 - 2.5, u1 + 1, v1 - 2.3)])
    return body - ext((beds + sold) ^ reg, d * 0.4, d)


PW.POSTS.update(kittredge=post_kittredge)
PW.FILLS.update(pairsticks=fill_pairsticks)
PW.FRIEZES.update(joistbeam=frieze_joistbeam)
PW.SKIRTS.update(soldierbrick=skirt_soldierbrick)
FT.EDGE_EXTRA.update(notchfascia=edge_notchfascia)


def chimney_tapestry(w=11.0, d=9.0, h=24.0):
    """The Kittredge's ridge stack in tapestry brick, a corbelled top of three courses each
    further out, a cement wash and two round clay pots."""
    h = round(h / 0.2) * 0.2
    zt = h - 4.2
    body = box([-w / 2, -d / 2, 0.0], [w / 2, d / 2, zt])
    body = body + TW._skin(w, d, 0.0, zt - 0.2, lambda reg, i: foundation_tapestry(reg, seed=i))
    z = zt
    for k in range(3):
        g = 0.35 * (k + 1)
        body = body + box([-w / 2 - g, -d / 2 - g, z - 0.01], [w / 2 + g, d / 2 + g, z + 0.6])
        z += 0.6
    body = body + M.hull_points([(x * (w / 2 + 1.05), y * (d / 2 + 1.05), z - 0.01) for x in (-1, 1) for y in (-1, 1)] +
                                [(x * (w / 2 - 0.4), y * (d / 2 - 0.4), z + 0.8) for x in (-1, 1) for y in (-1, 1)])
    for sg in (-1, 1):
        pot = M.cylinder(h - z - 0.6, 1.15, 0.95, 24).translate([sg * w / 4, 0, z + 0.6])
        pot = pot + M.cylinder(0.6, 1.3, 1.3, 24).translate([sg * w / 4, 0, h - 0.6])
        body = body + pot - M.cylinder(4.0, 0.6, 0.6, 16).translate([sg * w / 4, 0, h - 3.0])
    return body


# ================================================================== the Pullman (Chicago brick bungalow)
def brick_scratch(region, datum=0.0, bl=2.6, bh=0.85, seed=0):
    """Chicago wire-cut face brick: running bond with raked bed joints and flush heads, each
    brick's face scored with fine vertical scratches (the Pullman)."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    rng = np.random.default_rng(seed + 17)
    beds, heads, scr = [], [], []
    k = math.floor((v0 - datum) / bh) - 1
    while datum + k * bh < v1:
        v = datum + k * bh
        beds.append(rect(u0 - 1, v - 0.13, u1 + 1, v + 0.13))
        off = (k % 2) * bl / 2
        for u in np.arange(u0 - bl + off - (u0 - bl + off) % bl, u1 + bl, bl):
            heads.append(rect(u - 0.09, v, u + 0.09, v + bh))
            for x in u + rng.uniform(0.4, 0.8) + np.arange(0.0, bl - 0.8, rng.uniform(0.55, 0.8)):
                scr.append(rect(x - 0.07, v + 0.2, x + 0.07, v + bh - 0.2))
        k += 1
    out = M.extrude(region, 0.4) - ext(cs_union(beds) ^ region, 0.2, 1.0) - ext(cs_union(heads) ^ region, 0.3, 1.0)
    return out - ext(cs_union(scr) ^ region, 0.32, 1.0)


def foundation_chicagobase(reg, seed=0):
    """A raised basement of brick under a bevelled limestone water table, with a sunk panel
    for a basement window every so often (the Pullman)."""
    b = reg.bounds()
    vt = b[3] - 1.8
    body = brick_scratch(reg ^ rect(b[0] - 1, b[1] - 1, b[2] + 1, vt), seed=seed)
    wt = reg ^ rect(b[0] - 1, vt, b[2] + 1, b[3])
    body = body + ext(wt, 0.0, 0.9) + ext(wt ^ rect(b[0] - 1, vt + 0.9, b[2] + 1, b[3]), 0.0, 1.3)
    for u in np.arange(b[0] + 14.0, b[2] - 8.0, 28.0):
        pan = rect(u - 4.0, b[1] + 2.0, u + 4.0, vt - 1.6) ^ reg
        if pan.is_empty():
            continue
        body = body - ext(pan, 0.1, 2.0) + ext((pan.offset(0.6, JoinType.Miter, 4.0) - pan) ^ reg, 0.0, 0.8)
        body = body + ext(cs_union([rect(u + x - 0.25, b[1] + 2.0, u + x + 0.25, vt - 1.6) for x in (-2.0, 0.0, 2.0)]) ^ reg, 0.1, 0.5)
    return body


def frieze_sullivan(L, h, b, pitch, margin, pair, half):
    """Sullivanesque terra cotta: at every station a seed pod (a disc in a ring) sending out four
    curling fronds; between them a ribbon of interlaced loops (the Pullman)."""
    v0, v1 = 0.6, h - 0.6
    hh = v1 - v0
    vc = v0 + hh / 2
    out = []
    for u in CO._us(L, pitch, margin, 0.0):
        r = min(0.8, hh * 0.24)
        parts = [circle((u, vc), r * 0.6, 16), circle((u, vc), r + 0.35, 24) - circle((u, vc), r, 24)]
        for sx in (-1, 1):
            for sy in (-1, 1):
                a0 = math.atan2(sy, sx)
                pts = [(u + (r + 0.3 + 1.6 * t) * math.cos(a0 + sx * sy * 1.8 * t), vc + (r + 0.3 + 1.6 * t) * math.sin(a0 + sx * sy * 1.8 * t) * 0.7)
                       for t in np.linspace(0.0, 1.0, 10)]
                parts.append(stroke(pts, 0.38, caps=True))
        out.append(_st(cs_union(parts) ^ rect(u - 4, v0, u + 4, v1), b, 0.45))
    for uc, wd in CO._between(L, pitch, margin, pair, half + 3.2):
        if wd < 3.0:
            continue
        n = max(1, int(wd / 2.4))
        loops = []
        for k in range(n):
            c = (uc - wd / 2 + wd * (k + 0.5) / n, vc)
            rr = min(0.9, wd / n / 2 - 0.1)
            loops.append(oval(c, rr, hh * 0.3, 20) - oval(c, rr - 0.38, hh * 0.3 - 0.38, 20))
        out.append(_st(cs_union(loops), b, 0.35))
    return out, []


def course_pairdentil(L, h, b, pitch, margin, p):
    """Dentils set in pairs with a wide gap between the pairs."""
    teeth = []
    for u in np.arange(0.6, L - 1.2, 2.6):
        teeth += [rect(u, 0.15, u + 0.6, h - 0.15), rect(u + 0.9, 0.15, u + 1.5, h - 0.15)]
    return [ext(cs_union(teeth) ^ rect(0.2, 0.0, L - 0.2, h), b - 0.05, b + 0.5)]


def bracket_slabconsole(h, d, t):
    """A slab console: a flat-topped block whose underside sweeps down in a quarter curve to a
    square foot at the wall (side profile, top at v = 0)."""
    hb = max(1.8, min(h, 3.2))
    pts = [(0.0, 0.0), (d, 0.0), (d, -0.7)]
    pts += [(d - (d - 0.6) * math.sin(a), -0.7 - (hb - 1.3) * (1 - math.cos(a))) for a in np.linspace(0.05, math.pi / 2, 10)]
    pts += [(0.6, -hb + 0.6), (0.6, -hb), (0.0, -hb)]
    return poly(pts)


CO.FRIEZE_EXTRA.update(sullivan=frieze_sullivan)
CO.COURSE_EXTRA.update(pairdentil=course_pairdentil)
TW.BRACKET_EXTRA.update(slabconsole=bracket_slabconsole)
TW.FOUNDATION_EXTRA.update(chicagobase=foundation_chicagobase)


def _artglass_chicago(cs):
    """Chicago art glass for a transom: a row of circles each set in a square, joined by a
    level line through their middles."""
    u0, v0, u1, v1 = cs.bounds()
    hh = v1 - v0
    n = max(1, int((u1 - u0) / (hh * 1.1)))
    parts = [rect(u0 - 1, (v0 + v1) / 2 - 0.2, u1 + 1, (v0 + v1) / 2 + 0.2)]
    for k in range(n):
        c = (u0 + (u1 - u0) * (k + 0.5) / n, (v0 + v1) / 2)
        s = min(hh * 0.36, (u1 - u0) / n * 0.36)
        sq = rect(c[0] - s, c[1] - s, c[0] + s, c[1] + s)
        parts += [sq - sq.offset(-0.4, JoinType.Miter, 4.0), circle(c, s * 0.62, 20) - circle(c, s * 0.62 - 0.4, 20)]
    return cs_union(parts)


def _lintel(hw, v, t=1.3):
    """A limestone lintel with a raised keystone block over the middle."""
    return [chamfer_box(-hw - 1.0, v, hw + 1.0, v + 1.8, 0.0, t, c=0.3), chamfer_box(-1.2, v - 0.2, 1.2, v + 2.4, 0.0, t + 0.3, c=0.3)]


def window_chicago(w, h, A=1.3):
    """The Pullman's Chicago window: a broad fixed pane between two narrow double-hung sashes,
    under an art-glass transom band right across, in a flat casing on a long limestone sill
    under a limestone lintel with a keystone."""
    op = O.opening_cs(w, h, 0)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    u0, v0, u1, v1 = plug_cs.offset(-0.5, JoinType.Miter, 4.0).bounds()
    mull = 1.0
    vt = v1 - (v1 - v0) * 0.24
    sw = (u1 - u0) * 0.2
    lights = [rect(u0, v0, u0 + sw, vt - 0.5), rect(u0 + sw + mull, v0, u1 - sw - mull, vt - 0.5), rect(u1 - sw, v0, u1, vt - 0.5)]
    tr = rect(u0, vt + 0.5, u1, v1)
    bars = [rect(u0 - 1, (v0 + vt) / 2 - 0.3, u0 + sw + 0.1, (v0 + vt) / 2 + 0.3), rect(u1 - sw - 0.1, (v0 + vt) / 2 - 0.3, u1 + 1, (v0 + vt) / 2 + 0.3)]
    bars.append(_artglass_chicago(tr) ^ tr)
    g = cs_union(lights + [tr])
    sash = _glazed([ext(plug_cs, -pl, -0.6)], g, pl, cs_union(bars), plug_cs)
    sash.append(ext(cs_union([rect(u0 + sw, v0, u0 + sw + mull, v1), rect(u1 - sw - mull, v0, u1 - sw, v1), rect(u0, vt - 0.5, u1, vt + 0.5)]), -pl, 0.3))
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, 0.7),
             ext((op.offset(A, JoinType.Miter, 4.0) - op) ^ rect(-w, 0.0, w, h + A), 0.0, 0.6)]
    parts += _lintel(w / 2 + A, h + A - 0.01)
    parts.append(chamfer_box(-w / 2 - A - 1.6, -1.3, w / 2 + A + 1.6, 0.2, 0.0, 1.6, c=0.45, bottom=0.9))
    return O._one_piece(sash, parts, op, plug_cs, pl, h + A + 2.4, -1.3)


def window_artsash(w, h, A=1.2):
    """The Pullman's double-hung window: the upper sash in art glass (the same circles in
    squares in a band, a border line round it), the lower sash plain, flat casing, limestone
    sill and a keystoned limestone lintel."""
    op = O.opening_cs(w, h, 0)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    u0, v0, u1, v1 = plug_cs.offset(-0.5, JoinType.Miter, 4.0).bounds()
    vm = v0 + (v1 - v0) * 0.5
    top = rect(u0, vm + 0.35, u1, v1)
    band = rect(u0 + 0.9, v1 - (v1 - vm) * 0.55, u1 - 0.9, v1 - 0.9)
    bars = cs_union([rect(u0 - 1, vm - 0.35, u1 + 1, vm + 0.35), top.offset(-0.9, JoinType.Miter, 4.0) - top.offset(-1.3, JoinType.Miter, 4.0),
                     _artglass_chicago(band) ^ band])
    sash = _glazed([ext(plug_cs, -pl, -0.6)], rect(u0, v0, u1, v1), pl, bars, plug_cs)
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, 0.7),
             ext((op.offset(A, JoinType.Miter, 4.0) - op) ^ rect(-w, 0.0, w, h + A), 0.0, 0.6)]
    parts += _lintel(w / 2 + A, h + A - 0.01)
    parts.append(chamfer_box(-w / 2 - A - 1.2, -1.2, w / 2 + A + 1.2, 0.2, 0.0, 1.5, c=0.45, bottom=0.9))
    return O._one_piece(sash, parts, op, plug_cs, pl, h + A + 2.4, -1.2)


def door_chicago(w=11.0, h=24.0, A=1.8):
    """The Pullman's door, in two colours (one change): an oak leaf with one tall art-glass
    light (a lozenge chain down its middle) over a panel, in a limestone surround whose flat
    hood rests on two scrolled consoles."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    leaf = plug_cs.offset(-0.3, JoinType.Miter, 4.0)
    u0, v0, u1, v1 = leaf.bounds()
    win = rect(u0 + 1.4, v0 + (v1 - v0) * 0.36, u1 - 1.4, v1 - 1.4)
    wb = win.bounds()
    body = [ext(plug_cs, -pl, -1.0), ext(leaf - win, -1.0, -0.6)]
    body.append(chamfer_box(u0 + 1.2, v0 + 1.2, u1 - 1.2, v0 + (v1 - v0) * 0.36 - 1.2, -0.6, 0.35, c=0.2))
    loz = []
    for vv in np.linspace(wb[1] + 1.4, wb[3] - 1.4, 5):
        d_ = poly([((wb[0] + wb[2]) / 2 - 1.0, vv), ((wb[0] + wb[2]) / 2, vv + 1.3), ((wb[0] + wb[2]) / 2 + 1.0, vv), ((wb[0] + wb[2]) / 2, vv - 1.3)])
        loz.append(d_ - d_.offset(-0.4, JoinType.Miter, 4.0))
    bars = cs_union(loz + [rect((wb[0] + wb[2]) / 2 - 0.2, wb[1] - 1, (wb[0] + wb[2]) / 2 + 0.2, wb[3] + 1)])
    sash = _glazed(body, win, pl, bars, plug_cs)
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, 0.7),
             ext((op.offset(A, JoinType.Miter, 4.0) - op) ^ rect(-w, 0.0, w, h + A), 0.0, 0.8)]
    hw = w / 2 + A
    for sg in (-1, 1):
        x = sg * (hw - 0.6)
        prof = [(0.0, 0.0), (2.0, 0.0)] + [(2.0 - 1.4 * math.sin(a), -3.4 * (1 - math.cos(a))) for a in np.linspace(0.1, math.pi / 2, 8)] + [(0.0, -3.4)]
        for k in range(len(prof) - 1):
            pass
        cons = M.extrude(poly(prof), 1.2).transform(np.array([[0, 0, 1.0, x - 0.6], [0, 1.0, 0, h + A + 0.8], [1.0, 0, 0, 0]]))
        parts.append(cons)
    parts.append(chamfer_box(-hw - 1.6, h + A + 0.79, hw + 1.6, h + A + 2.2, 0.0, 2.4, c=0.5, bottom=1.6))
    return O._one_piece(sash, parts, op, plug_cs, pl, h + A + 2.2, 0.0)


def dormer_bellcast(w=26.0, dep=14.0, hwall=10.0):
    """The Pullman's dormer: a low front with a ribbon of three casements, each with an art
    glass head band, between shingle-lap cheeks that flare out at the foot. Local as
    colonial.dormer_pedimented; returns (body, core, face)."""
    face = rect(-w / 2, 0.0, w / 2, hwall)
    body = ext(face, -dep, 0.0) - ext(face.offset(-1.2, JoinType.Miter, 4.0) ^ rect(-50, 1.2, 50, hwall - 1.2), -dep - 1, -1.2)
    lw = w * 0.8
    band = rect(-lw / 2, 1.8, lw / 2, hwall - 1.4)
    body = body - ext(band, -1.3, 1.0)
    inner = band.offset(-0.4, JoinType.Miter, 4.0)
    a0, b0, a1, b1 = inner.bounds()
    cw = (a1 - a0) / 3
    heads = cs_union([rect(a0 + cw * j - 0.1, b1 - 1.8, a0 + cw * (j + 1) + 0.1, b1 - 1.2) for j in range(3)] +
                     [circle((a0 + cw * (j + 0.5), b1 - 0.9), 0.5, 14) - circle((a0 + cw * (j + 0.5), b1 - 0.9), 0.15, 8) for j in range(3)])
    bars = cs_union([rect(a0 + cw * j - 0.45, b0 - 1, a0 + cw * j + 0.45, b1 + 1) for j in (1, 2)])
    body = body + ext((band - inner) + (bars ^ inner) + (heads ^ inner), -1.2, -0.5)
    body = body + ext((band.offset(0.8, JoinType.Miter, 4.0) - band) ^ rect(-w, 1.8, w, hwall), -0.01, 0.55)
    body = body + chamfer_box(-lw / 2 - 1.0, 1.0, lw / 2 + 1.0, 1.8, -0.01, 1.0, c=0.3, bottom=1.0)
    for sg in (-1, 1):                                  # the flared foot of each cheek
        x0 = sg * w / 2
        fl = M.hull_points([(x0 - sg * 0.3, 0.0, 0.0), (x0 - sg * 0.3, 0.0, -dep), (x0 - sg * 0.3, 1.6, 0.0), (x0 - sg * 0.3, 1.6, -dep),
                            (x0 + sg * 0.9, 0.0, 0.0), (x0 + sg * 0.9, 0.0, -dep)])
        body = body + fl
    core = ext(face.offset(-1.2, JoinType.Miter, 4.0) ^ rect(-50, 1.2, 50, hwall - 1.2), -dep + 1.2, -1.2)
    return body, core, face


def dormer_bellcast_roof(w, dep, hwall, over=2.6, s=0.62, kick=0.3, fascia=0.8):
    """A bellcast hip for the dormer: steep hips that flatten into a kick at the eaves."""
    a = w / 2 + over
    z = hwall + fascia

    def hip(a_, z_, s_, ov):
        blk = box([-a_, hwall, -dep - 16.0], [a_, z_ + a_ * s_ + 1.0, ov])
        blk = blk.trim_by_plane([s_, -1.0, 0.0], -(z_ + s_ * a_)).trim_by_plane([-s_, -1.0, 0.0], -(z_ + s_ * a_))
        return blk.trim_by_plane([0.0, -1.0, -s_], -(z_ + s_ * ov))
    upper = hip(w / 2 + 0.6, z + (over - 0.6) * kick, s, 0.6)
    lower = hip(a, z, kick, over) ^ box([-a - 1, hwall, -dep - 17.0], [a + 1, z + (over - 0.6) * kick + 0.8, over + 1])
    return upper + lower


def chimney_chicago(h, zb, w=14.0, d=8.0):
    """The Pullman's outside chimney: face brick with two limestone bands, a sloped limestone
    shoulder at ``zb`` stepping the breast in to the stack, a limestone cap on a corbelled
    course and one clay pot. Local: x across the wall, y out (back face on y = 0), z up."""
    h = round(h / 0.2) * 0.2
    W1, D1 = w + 4.0, d + 1.6

    def sk(reg, i):
        return brick_scratch(reg, seed=i)

    def body_(ww, dd, za, zb_):
        bb = box([-ww / 2, 0.0, za], [ww / 2, dd, zb_])
        s = TW._skin(ww, dd, za + 0.2, zb_ - 0.2, sk).translate([0, dd / 2, 0])
        return bb + (s - box([-ww, -5, za - 1], [ww, 0.0, zb_ + 1]))
    out = body_(W1, D1, 0.0, zb)
    out = out + M.hull_points([(x * (W1 / 2 + 0.4), y, zb - 0.01) for x in (-1, 1) for y in (0.0, D1 + 0.4)] +
                              [(x * w / 2, y, zb + 2.2) for x in (-1, 1) for y in (0.0, d)])
    zt = h - 3.0
    out = out + body_(w, d, zb + 2.19, zt)
    for zz in (zb * 0.45, zb + 2.2 + (zt - zb) * 0.55):
        ww, dd = (W1, D1) if zz < zb else (w, d)
        out = out + box([-ww / 2 - 0.4, 0.0, zz], [ww / 2 + 0.4, dd + 0.4, zz + 1.0])
    out = out + box([-w / 2 - 0.4, 0.0, zt - 0.01], [w / 2 + 0.4, d + 0.4, zt + 0.6])
    out = out + M.hull_points([(x * (w / 2 + 1.0), y, zt + 0.59) for x in (-1, 1) for y in (0.0, d + 1.0)] +
                              [(x * (w / 2 + 1.0), y, zt + 1.4) for x in (-1, 1) for y in (0.0, d + 1.0)] +
                              [(x * (w / 2 - 0.8), y, zt + 2.2) for x in (-1, 1) for y in (0.4, d - 0.4)])
    pot = M.cylinder(h - zt - 1.8, 1.3, 1.05, 24).translate([0.0, d / 2, zt + 1.8]) - M.cylinder(5.0, 0.65, 0.65, 16).translate([0.0, d / 2, h - 3.0])
    return out + pot


# ================================================================== the Lindenwald (Swiss chalet bungalow)
def _heart(c, s):
    """A heart ``s`` wide, centred on c."""
    r = s * 0.28
    return cs_union([circle((c[0] - r * 0.85, c[1] + r * 0.5), r, 16), circle((c[0] + r * 0.85, c[1] + r * 0.5), r, 16),
                     poly([(c[0] - s * 0.49, c[1] + r * 0.35), (c[0] + s * 0.49, c[1] + r * 0.35), (c[0], c[1] - s * 0.55)])])


def _voronoi(region, pts, joint=0.25, k=10):
    """The Voronoi cells of ``pts`` inside ``region``, each shrunk by half the ``joint`` so a
    mortar joint of that width runs round every stone."""
    pts = np.asarray(pts, float)
    u0, v0, u1, v1 = region.bounds()
    big = max(u1 - u0, v1 - v0) + 20.0
    cells = []
    for i, p in enumerate(pts):
        if not (u0 - 4 < p[0] < u1 + 4 and v0 - 4 < p[1] < v1 + 4):
            continue
        cell = rect(p[0] - 6.0, p[1] - 6.0, p[0] + 6.0, p[1] + 6.0)
        d = np.linalg.norm(pts - p, axis=1)
        for j in np.argsort(d)[1:k + 1]:
            q = pts[j]
            m = (p + q) / 2
            n = (q - p) / (np.linalg.norm(q - p) + 1e-9)
            t = np.array([-n[1], n[0]])
            half = poly([tuple(m - t * big), tuple(m + t * big), tuple(m + t * big - n * big), tuple(m - t * big - n * big)])
            cell = cell ^ half
        cells.append(cell.offset(-joint / 2, JoinType.Round))
    return cs_union(cells) ^ region


def rubble_chalet(region, seed=0):
    """Random rubble for the chalet's ground storey: stones of all shapes fitted together
    (Voronoi cells of a jittered grid) with a mortar joint round each, every stone raised and
    its edges eased (the Lindenwald)."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    rng = np.random.default_rng(seed + 29)
    pts = []
    for j, v in enumerate(np.arange(v0 - 3.0, v1 + 3.0, 2.2)):
        for u in np.arange(u0 - 3.0 + (j % 2) * 1.4, u1 + 3.0, 2.8):
            pts.append((u + rng.uniform(-0.9, 0.9), v + rng.uniform(-0.6, 0.6)))
    st = _voronoi(region, pts, joint=0.45)
    return M.extrude(region, 0.2) + ext(st, 0.15, 0.4) + ext(st.offset(-0.35, JoinType.Round), 0.35, 0.55)


def siding_logs(region, datum=0.0, lh=1.7):
    """Squared logs laid up Swiss-fashion (Blockbau): each course eased top and bottom so it
    reads round, a dark chink between (the Lindenwald)."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    k0 = math.floor((v0 - datum) / lh) - 1
    full, crown = [], []
    for k in range(k0, k0 + int((v1 - v0) / lh) + 4):
        v = datum + k * lh
        full.append(rect(u0 - 1, v + 0.12, u1 + 1, v + lh - 0.12))
        crown.append(rect(u0 - 1, v + 0.4, u1 + 1, v + lh - 0.4))
    return M.extrude(region, 0.2) + ext(cs_union(full) ^ region, 0.15, 0.55) + ext(cs_union(crown) ^ region, 0.5, 0.8)


def log_ends(L, v0, v1, odd, datum=0.0, lh=1.7, reach=1.4, t=3.0):
    """The crossing log ends at a Blockbau corner, for the facade's two ends: every other
    course (``odd`` picks which) runs ``reach`` past the corner, its underside cut back at
    about 50 degrees so it prints on the wall. Local: u along the facade, v up, w out."""
    out = []
    k0 = math.ceil((v0 - datum) / lh)
    for k in range(k0, int((v1 - datum) / lh)):
        if k % 2 != odd:
            continue
        v = datum + k * lh
        for sg, uc in ((-1, 0.0), (1, L)):
            pts = [(uc - sg * 0.6, v + 0.12), (uc, v + 0.12), (uc + sg * reach, v + 0.12 + reach * 0.85),
                   (uc + sg * reach, v + lh - 0.12), (uc - sg * 0.6, v + lh - 0.12)]
            out.append(ext(poly(pts), -t, 0.8))
    return union(out) if out else M()


def foundation_cyclopean(reg, seed=0):
    """Polygonal (cyclopean) masonry: big many-sided stones fitted tight, each a flat face
    with a narrow sunk joint round it (the Lindenwald)."""
    b = reg.bounds()
    rng = np.random.default_rng(seed + 53)
    pts = []
    for u in np.arange(b[0] - 3.0, b[2] + 3.0, 4.2):
        for v in np.arange(b[1] - 3.0, b[3] + 3.0, 3.4):
            pts.append((u + rng.uniform(-1.3, 1.3), v + rng.uniform(-1.0, 1.0)))
    pts = np.array(pts)
    joints = []
    for i, p in enumerate(pts):
        d = np.linalg.norm(pts - p, axis=1)
        for j in np.argsort(d)[1:5]:
            if j > i:
                m = (p + pts[j]) / 2
                n = pts[j] - p
                n = n / (np.linalg.norm(n) + 1e-9)
                t_ = np.array([-n[1], n[0]])
                joints.append(poly([tuple(m - t_ * 2.4 - n * 0.12), tuple(m + t_ * 2.4 - n * 0.12), tuple(m + t_ * 2.4 + n * 0.12), tuple(m - t_ * 2.4 + n * 0.12)]))
    body = M.extrude(reg, 0.55)
    return body - ext(cs_union(joints) ^ reg, 0.3, 1.0)


def frieze_edelweiss(L, h, b, pitch, margin, pair, half):
    """Edelweiss: at every station a star of six woolly petals round a knot of florets, two
    leaves beneath; a wavy stem between the flowers (the Lindenwald)."""
    v0, v1 = 0.6, h - 0.6
    hh = v1 - v0
    vc = v0 + hh * 0.58
    out = []
    for u in CO._us(L, pitch, margin, 0.0):
        r = min(1.4, hh * 0.36)
        pet = [stroke([(u, vc), (u + r * math.cos(a), vc + r * math.sin(a))], r * 0.42, caps=True) for a in np.linspace(math.pi / 2, math.pi / 2 + 2 * math.pi, 6, endpoint=False)]
        parts = pet + [stroke([(u, vc - r * 0.6), (u - 1.1, v0 + 0.2)], 0.38, caps=True), stroke([(u, vc - r * 0.6), (u + 1.1, v0 + 0.2)], 0.38, caps=True)]
        out.append(_st(cs_union(parts) - circle((u, vc), r * 0.3, 12), b, 0.4))
        out.append(_st(circle((u, vc), r * 0.3, 12), b, 0.55))
    for uc, wd in CO._between(L, pitch, margin, pair, half + 2.4):
        if wd < 2.5:
            continue
        xs = np.linspace(uc - wd / 2, uc + wd / 2, max(6, int(wd * 2.5)))
        out.append(_st(stroke([(x, v0 + hh * 0.5 + hh * 0.18 * math.sin((x - xs[0]) / wd * 4 * math.pi)) for x in xs], 0.38, caps=False), b, 0.3))
    return out, []


def frieze_keyholes(L, h, b, pitch, margin, pair, half):
    """A sawn board: a row of keyhole cut-outs (a round head over a flared slot) with a small
    drop between each pair, as fretwork on a chalet fascia (the Lindenwald)."""
    v0, v1 = 0.6, h - 0.6
    hh = v1 - v0
    out = []
    n = max(1, int((L - 2 * margin) / (hh * 1.1)))
    board = rect(0.0, v0, L, v1)
    holes = []
    for k in range(n):
        u = margin + (L - 2 * margin) * (k + 0.5) / n
        r = min(0.75, hh * 0.2)
        holes.append(cs_union([circle((u, v1 - hh * 0.35), r, 16), poly([(u - 0.3, v1 - hh * 0.35), (u + 0.3, v1 - hh * 0.35), (u + 0.6, v0 + 0.5), (u - 0.6, v0 + 0.5)])]))
    out.append(_st(board - cs_union(holes), b, 0.4))
    return out, []


def course_heartrow(L, h, b, pitch, margin, p):
    """A row of little hearts between two fillets."""
    s = min(1.2, h * 0.7)
    hearts = [_heart((u, h / 2), s) for u in np.arange(1.2, L - 0.8, s * 1.7)]
    return [ext(cs_union([rect(0.3, 0.0, L - 0.3, 0.22), rect(0.3, h - 0.22, L - 0.3, h)]), b - 0.05, b + 0.25),
            ext(cs_union(hearts) ^ rect(0.0, 0.0, L, h), b - 0.05, b + 0.45)]


def bracket_chaletscroll(h, d, t):
    """A chalet bracket: a board sawn to a big S-scroll with a round eye cut through it."""
    hb = max(2.0, min(h, 4.0))
    pts = [(0.0, 0.0), (d, 0.0)]
    pts += [(d - 0.4 - (d - 0.9) * (1 - math.cos(a)) * 0.5, -hb * 0.45 * math.sin(a)) for a in np.linspace(0.2, math.pi, 10)]
    pts += [(0.9 + 0.5 * math.sin(a), -hb * 0.45 - hb * 0.55 * (1 - math.cos(a)) / 2) for a in np.linspace(0.0, math.pi, 8)]
    pts += [(0.0, -hb)]
    cs = poly(pts)
    eye = circle((d * 0.55, -hb * 0.25), min(0.45, hb * 0.12), 12)
    return cs - eye if (cs - eye).area() > 0.5 else cs


CO.FRIEZE_EXTRA.update(edelweiss=frieze_edelweiss, keyholes=frieze_keyholes)
CO.COURSE_EXTRA.update(heartrow=course_heartrow)
TW.BRACKET_EXTRA.update(chaletscroll=bracket_chaletscroll)
TW.FOUNDATION_EXTRA.update(cyclopean=foundation_cyclopean)


def _flowerbox(hw, v, depth=3.2, seed=0):
    """A window box under a sill: a board front pierced with hearts, and a mound of blooms."""
    rng = np.random.default_rng(seed + 7)
    front = rect(-hw, v - 3.0, hw, v)
    hearts = cs_union([_heart((x, v - 1.5), 1.1) for x in np.arange(-hw + 1.6, hw - 1.0, 2.6)])
    box_ = box([-hw, v - 3.0, 0.0], [hw, v, depth]) - ext(hearts, depth - 0.35, depth + 1.0)
    blooms = union([M.sphere(rng.uniform(0.55, 0.8), 12).translate([x, v + 0.1, rng.uniform(0.8, depth - 0.6)])
                    for x in np.arange(-hw + 0.8, hw - 0.5, 1.0)]) ^ box([-hw, v - 0.01, 0.0], [hw, v + 1.2, depth])
    return box_ + blooms


def window_chalet(w, h, upper=False, A=1.2):
    """The Lindenwald's window: a pair of casements of three panes each, a cream casing, a
    pair of shutters pierced with hearts, and a window box of blooms below. Downstairs the head
    is a sawn board with a scalloped edge; upstairs a little pent roof on two brackets (the
    frames differ by storey). Two colours: cream, then red from 0.8 proud."""
    op = O.opening_cs(w, h, 0)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    u0, v0, u1, v1 = plug_cs.offset(-0.5, JoinType.Miter, 4.0).bounds()
    bars = cs_union([rect(-0.4, v0 - 1, 0.4, v1 + 1)] + [rect(u0 - 1, v0 + (v1 - v0) * k / 3 - 0.2, u1 + 1, v0 + (v1 - v0) * k / 3 + 0.2) for k in (1, 2)])
    sash = _glazed([ext(plug_cs, -pl, -0.6)], rect(u0, v0, u1, v1), pl, bars, plug_cs)
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, 0.7),
             ext((op.offset(A, JoinType.Miter, 4.0) - op) ^ rect(-w, 0.0, w, h + A), 0.0, 0.7)]
    hw = w / 2 + A
    for sg in (-1, 1):                                  # the shutters, each a heart cut through
        a, e = sorted((sg * hw, sg * (hw + w / 2)))
        sh = rect(a, 0.0, e, h + A) - _heart(((a + e) / 2, (h + A) * 0.66), min(2.4, (e - a) * 0.4))
        parts.append(ext(sh, 0.0, 1.4) - ext(cs_union([rect(a + 0.4, v, e - 0.4, v + 0.25) for v in np.arange(1.4, (h + A) * 0.45, 1.3)]), 1.15, 2.0))
    if upper:
        zb = h + A
        parts.append(M.hull_points([(x, zb, 0.0) for x in (-hw - 1.0, hw + 1.0)] + [(x, zb, 3.0) for x in (-hw - 1.0, hw + 1.0)] +
                                   [(x, zb + 2.2, 0.0) for x in (-hw - 1.0, hw + 1.0)] + [(x, zb + 1.2, 3.0) for x in (-hw - 1.0, hw + 1.0)]))
        for sg in (-1, 1):
            x = sg * (hw - 0.8)
            for k in range(5):
                parts.append(box([x - 0.45, zb - (k + 1) * 0.5, 0.0], [x + 0.45, zb - k * 0.5 + 0.01, 2.6 * math.cos(math.asin(min(1.0, (k + 0.5) / 5)))]))
        top = zb + 2.2
    else:
        head = rect(-hw - 0.6, h + A - 0.01, hw + 0.6, h + A + 2.2)
        head = head - cs_union([circle((x, h + A - 0.01), 0.7, 14) for x in np.arange(-hw + 0.6, hw, 1.8)])
        parts.append(ext(head, 0.0, 1.0))
        parts.append(chamfer_box(-hw - 1.0, h + A + 2.19, hw + 1.0, h + A + 2.9, 0.0, 1.4, c=0.3, bottom=0.8))
        top = h + A + 2.9
    parts.append(chamfer_box(-hw - 0.6, -1.0, hw + 0.6, 0.2, 0.0, 1.3, c=0.35, bottom=0.7))
    parts.append(_flowerbox(hw - 0.4, -0.99, seed=int(w * 10)))
    return O._one_piece(sash, parts, op, plug_cs, pl, top, -4.0)


def door_chalet(w=11.0, h=24.0, A=1.4, french=False):
    """The Lindenwald's doors. The front door: boards laid in a chevron, a heart-shaped light
    high up, strap hinges, under a sawn head with a tiny pent roof. ``french``: the balcony's
    pair of glazed doors, eight panes a leaf over a panel, a heart in the transom."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    leaf = plug_cs.offset(-0.3, JoinType.Miter, 4.0)
    u0, v0, u1, v1 = leaf.bounds()
    if french:
        vt = v1 - 3.2
        glass = cs_union([rect(u0 + 0.8, v0 + (vt - v0) * 0.3, -0.5, vt - 0.8), rect(0.5, v0 + (vt - v0) * 0.3, u1 - 0.8, vt - 0.8),
                          rect(u0 + 0.8, vt + 0.4, u1 - 0.8, v1 - 0.6)])
        body = [ext(plug_cs, -pl, -1.0), ext(leaf, -1.0, -0.6)]
        gb = glass.bounds()
        bars = [rect(x - 0.2, gb[1] - 1, x + 0.2, vt) for x in ((u0 + 0.8 - 0.5) / 2, (u1 - 0.8 + 0.5) / 2)]
        bars += [rect(u0, v, u1, v + 0.4) for v in np.linspace(v0 + (vt - v0) * 0.3, vt - 0.8, 5)[1:-1]]
        bars.append(_heart((0.0, (vt + v1) / 2 + 0.1), 1.8) - _heart((0.0, (vt + v1) / 2 + 0.1), 1.8).offset(-0.4, JoinType.Miter, 4.0))
        for (a, e) in ((u0 + 0.9, -0.6), (0.6, u1 - 0.9)):
            body.append(chamfer_box(a, v0 + 0.9, e, v0 + (vt - v0) * 0.3 - 0.8, -0.6, 0.3, c=0.15))
        sash = _glazed(body, glass, pl, cs_union(bars), plug_cs)
    else:
        win = _heart((0.0, v1 - 4.0), 3.0)
        chev = cs_union([_stripes(leaf ^ rect(u0, v0, 0.0, v1), math.radians(60), 1.5, 0.24),
                         _stripes(leaf ^ rect(0.0, v0, u1, v1), math.radians(120), 1.5, 0.24), rect(-0.14, v0, 0.14, v1)])
        body = [ext(plug_cs, -pl, -1.0), ext(leaf - chev - win, -1.0, -0.6), ext(leaf - win, -1.0, -0.8)]
        sash = _glazed(body, win, pl, None, plug_cs)
        for v in (h * 0.2, h * 0.55):
            sash.append(ext(cs_union([rect(u0 + 0.2, v - 0.35, u0 + (u1 - u0) * 0.6, v + 0.35), _heart((u0 + (u1 - u0) * 0.6 + 0.4, v), 1.2)]) ^ leaf, -0.7, -0.35))
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, 0.7),
             ext((op.offset(A, JoinType.Miter, 4.0) - op) ^ rect(-w, 0.0, w, h + A), 0.0, 0.7)]
    hw = w / 2 + A
    head = rect(-hw - 0.6, h + A - 0.01, hw + 0.6, h + A + 2.2) - cs_union([circle((x, h + A - 0.01), 0.7, 14) for x in np.arange(-hw + 0.6, hw, 1.8)])
    parts.append(ext(head, 0.0, 1.0))
    zb = h + A + 2.2
    parts.append(M.hull_points([(x, zb - 0.01, 0.0) for x in (-hw - 1.4, hw + 1.4)] + [(x, zb - 0.01, 3.2) for x in (-hw - 1.4, hw + 1.4)] +
                               [(x, zb + 2.0, 0.0) for x in (-hw - 1.4, hw + 1.4)] + [(x, zb + 1.0, 3.2) for x in (-hw - 1.4, hw + 1.4)]))
    for sg in (-1, 1):
        x = sg * (hw + 0.2)
        for k in range(4):
            parts.append(box([x - 0.45, zb - (k + 1) * 0.5, 0.0], [x + 0.45, zb - k * 0.5 + 0.01, 2.8 * math.cos(math.asin(min(1.0, (k + 0.5) / 4)))]))
    return O._one_piece(sash, parts, op, plug_cs, pl, zb + 2.0, 0.0)


def purlin_chalet(L=12.0, s=1.8):
    """A chalet purlin end under a rake: a heavy square beam running out ``L``, its end carved
    to a scroll (a notch and a round), carried on a curved strut sweeping back to the wall so
    it prints on its wall. Local: u across (centred), v up (top at v = 0), w out."""
    pts = [(0.0, 0.0), (L, 0.0), (L, -s * 0.45), (L - 0.7, -s * 0.45)]
    pts += [(L - 0.7 - 0.6 * math.sin(a), -s * 0.45 - 0.6 * (1 - math.cos(a))) for a in np.linspace(0.2, math.pi / 2, 5)]
    pts += [(L - 1.3, -s)]
    R_ = L - 1.3
    pts += [(R_ - R_ * math.sin(a), -s - R_ * (1 - math.cos(a)) * 0.9) for a in np.linspace(0.05, math.pi / 2, 12)]
    pts += [(0.0, -s - R_ * 0.9)]
    prof = poly(pts)
    return M.extrude(prof, s).transform(np.array([[0, 0, 1.0, -s / 2], [0, 1.0, 0, 0], [1.0, 0, 0, 0]]))


def barge_chalet(L, slope, d_eave, skin=1.8, width=4.2, d=2.2):
    """The Lindenwald's bargeboards: a broad board whose lower edge is sawn in steps and drops,
    pierced with a line of tulips, tied at the apex by a king post that carries a carved
    pendant with a heart, and a short spire over it (facade frame; place at w = rake)."""
    from .gables import _text
    s = slope
    c = math.hypot(1.0, s)
    a_l, a_r = np.array([-d_eave, 0.0]), np.array([L + d_eave, 0.0])
    tip = np.array([L / 2, s * (L / 2 + d_eave)])
    depth = skin + width
    band, cuts, holes = [], [], []
    run = float(np.linalg.norm(tip - a_l))
    n_s = max(4, int(run / 3.4))
    for a in (a_l, a_r):
        n = np.array([s, -1.0]) / c if a[0] < L / 2 else np.array([-s, -1.0]) / c
        band.append(poly([tuple(a), tuple(tip), tuple(tip + n * depth), tuple(a + n * depth)]))
        dirv = (tip - a) / np.linalg.norm(tip - a)
        for k in range(1, n_s):
            p = a + dirv * (run * k / n_s)
            q = p + n * depth
            cuts.append(poly([tuple(q - dirv * 1.1), tuple(q + dirv * 1.1), tuple(q + dirv * 0.5 - n * 1.3), tuple(q - dirv * 0.5 - n * 1.3)]))
            if k % 2 == 0 and k < n_s - 1:
                cc = p + n * (skin + width * 0.45)
                holes.append(cs_union([circle(tuple(cc + dirv * 0.0 - n * 0.3), 0.45, 12), circle(tuple(cc - dirv * 0.5 + n * 0.1), 0.35, 10),
                                       circle(tuple(cc + dirv * 0.5 + n * 0.1), 0.35, 10)]))
    board = cs_union(band) ^ rect(-d_eave - 5, -0.01, L + d_eave + 5, tip[1] + 5)
    board = board - cs_union(cuts) - cs_union(holes)
    board = board + rect(L / 2 - 1.3, tip[1] - depth * c - 1.0, L / 2 + 1.3, tip[1])
    board = cs_union([pc for pc in board.decompose() if pc.area() > 2.0])
    parts = [_text(board, 0.0, d)]
    ay = tip[1] - depth * c - 0.8
    pend = cs_union([rect(L / 2 - 0.8, ay - 3.4, L / 2 + 0.8, ay + 0.4), _heart((L / 2, ay - 4.4), 2.4)])
    parts.append(_text(pend, 0.0, d + 0.3))
    spire = cs_union([rect(L / 2 - 0.7, tip[1] - 0.6, L / 2 + 0.7, tip[1] + 2.4), poly([(L / 2 - 0.9, tip[1] + 2.39), (L / 2 + 0.9, tip[1] + 2.39), (L / 2, tip[1] + 5.2)])])
    parts.append(_text(spire, 0.0, d + 0.3))
    return union(parts)


def post_chalet(h, collar=None, abacus=3.6, slot=None):
    """A chalet porch post: a round shaft on a square base block, with a carved band of three
    rings a third of the way up and a flared head under a square cap."""
    zt = h - 2.4
    body = PW._plinth(3.6, 1.4) + box([-1.5, -1.5, 1.39], [1.5, 1.5, 2.8])
    body = body + PW._revolve([(0.0, 2.79), (1.3, 2.79), (1.2, zt), (0.0, zt)], 32)
    zb = h * 0.34
    for k in range(3):
        body = body + PW._revolve([(0.0, zb + k * 0.8), (1.5, zb + k * 0.8 + 0.2), (1.5, zb + k * 0.8 + 0.5), (0.0, zb + k * 0.8 + 0.7)], 32)
    return body + PW._top(h, abacus / 2, zt - 0.01, 1.2, slot, shape="round")


def fill_sawnhearts(L, vb, vt):
    """A railing of sawn balusters: flat boards waisted in the middle, a heart cut through
    each, between a top and a bottom rail."""
    parts = [rect(0.0, vb, L, vb + 1.0), rect(0.0, vt - 1.2, L, vt)]
    n = max(1, int(L / 2.8))
    H = vt - vb - 2.2
    for k in range(n):
        c = L * (k + 0.5) / n
        bd = poly([(c - 1.0, vb + 1.0), (c + 1.0, vb + 1.0), (c + 0.6, vb + 1.0 + H * 0.5), (c + 1.0, vt - 1.2), (c - 1.0, vt - 1.2), (c - 0.6, vb + 1.0 + H * 0.5)])
        parts.append(bd - _heart((c, vb + 1.0 + H * 0.62), 1.1))
    return parts


def frieze_chaletbeam(u0, u1, v_bot, v_top):
    """A porch beam with a sawn valance of little arches and drops hanging under it."""
    v0 = v_top - 2.2
    beam = rect(u0, v0, u1, v_top + 0.05)
    L = u1 - u0
    n = max(1, int(L / 3.0))
    val = rect(u0, v0 - 1.4, u1, v0 + 0.01)
    val = val - cs_union([circle((u0 + L * (k + 0.5) / n, v0 - 1.4), min(1.2, L / n * 0.4), 16) for k in range(n)])
    return beam + val


def edge_scallopboard(L, z0, zc):
    """Porch fascia: a board sawn to shallow scallops along its foot."""
    band = rect(0.3, zc - 1.3, L - 0.3, zc)
    return band - cs_union([circle((x, zc - 1.3), 0.7, 14) for x in np.arange(1.2, L - 0.6, 1.8)]), 0.8


def skirt_crosslog(reg, d=1.2):
    """A porch skirt of horizontal logs with the ends of cross logs showing at intervals."""
    if reg.is_empty():
        return M()
    u0, v0, u1, v1 = reg.bounds()
    body = M.extrude(reg, d * 0.5)
    logs = cs_union([rect(u0 - 1, v + 0.12, u1 + 1, v + 1.58) for v in np.arange(v0, v1, 1.7)]) ^ reg
    ends = cs_union([circle((u, (v0 + v1) / 2), 0.9, 16) for u in np.arange(u0 + 8.0, u1 - 3.0, 12.0)]) ^ reg
    return body + ext(logs, d * 0.45, d * 0.8) + ext(ends, d * 0.45, d)


PW.POSTS.update(chalet=post_chalet)
PW.FILLS.update(sawnhearts=fill_sawnhearts)
PW.FRIEZES.update(chaletbeam=frieze_chaletbeam)
PW.SKIRTS.update(crosslog=skirt_crosslog)
FT.EDGE_EXTRA.update(scallopboard=edge_scallopboard)


def chimney_chalet(w=10.0, d=10.0, h=26.0):
    """The Lindenwald's stack: rubble stone to a slab, and over it a little hat: four corner
    posts carrying a tiny gabled roof of shingles, the smoke going out under its eaves."""
    h = round(h / 0.2) * 0.2
    zt = h - 6.0
    body = box([-w / 2, -d / 2, 0.0], [w / 2, d / 2, zt]) + TW._skin(w, d, 0.0, zt - 0.2, lambda reg, i: rubble_chalet(reg, seed=i))
    body = body + box([-w / 2 - 0.8, -d / 2 - 0.8, zt - 0.01], [w / 2 + 0.8, d / 2 + 0.8, zt + 0.8])
    for sx in (-1, 1):
        for sy in (-1, 1):
            body = body + box([sx * (w / 2 - 0.2) - 0.8, sy * (d / 2 - 0.2) - 0.8, zt + 0.79], [sx * (w / 2 - 0.2) + 0.8, sy * (d / 2 - 0.2) + 0.8, zt + 3.2])
    z = zt + 3.19
    body = body + box([-w / 2 - 0.6, -d / 2 - 0.6, z], [w / 2 + 0.6, d / 2 + 0.6, z + 0.6])
    ridge = h
    body = body + M.hull_points([(x, y, z + 0.59) for x in (-w / 2 - 1.2, w / 2 + 1.2) for y in (-d / 2 - 1.2, d / 2 + 1.2)] +
                                [(x, 0.0, ridge) for x in (-w / 2 - 1.2, w / 2 + 1.2)])
    return body - box([-w / 2 + 1.6, -d / 2 + 1.6, zt - 4.0], [w / 2 - 1.6, d / 2 - 1.6, zt + 0.81])


# ================================================================== the Stickley (two-storey Craftsman)
def lap_beaded(region, datum=0.0, pitch=2.5):
    """Wide beaded lap siding: broad bevelled boards, each with a small round bead run along
    its lower edge (the Stickley)."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    out = M.extrude(region, 0.2)
    k0 = math.floor((v0 - datum) / pitch) - 1
    boards, beads = [], []
    for k in range(k0, k0 + int((v1 - v0) / pitch) + 4):
        v = datum + k * pitch
        for j in range(4):
            boards.append((rect(u0 - 1, v + j * pitch / 4, u1 + 1, v + pitch), 0.2 + 0.12 * (3 - j)))
        beads.append(rect(u0 - 1, v + 0.1, u1 + 1, v + 0.45))
    for cs_, d_ in boards:
        out = out + ext(cs_ ^ region, 0.0, d_ + 0.1)
    return out + ext(cs_union(beads) ^ region, 0.0, 0.75)


def shakes_ragged(region, datum=0.0, pitch=2.0, seed=0):
    """Ragged shakes: straight-edged shingles of random width whose butts wander up and down
    a little course by course, so the lines read hand-laid (the Stickley)."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    rng = np.random.default_rng(seed + 3)
    out = M.extrude(region, 0.25)
    k0 = math.floor((v0 - datum) / pitch) - 1
    lay = {0: [], 1: []}
    for k in range(k0, k0 + int((v1 - v0) / pitch) + 4):
        v = datum + k * pitch
        u = u0 - rng.uniform(0.0, 2.0)
        while u < u1 + 1.0:
            wd = rng.uniform(1.4, 3.0)
            dv = rng.uniform(-0.3, 0.3)
            lay[k % 2].append(rect(u + 0.1, v + dv, u + wd - 0.1, v + pitch + 0.2))
            u += wd
    return out + ext(cs_union(lay[0]) ^ region, 0.1, 0.55) + ext(cs_union(lay[1]) ^ region, 0.1, 0.65)


def foundation_boardformed(reg, seed=0):
    """Board-formed concrete: the grain and joints of the formwork boards printed in the
    face, with a chamfered top edge (the Stickley)."""
    b = reg.bounds()
    rng = np.random.default_rng(seed + 61)
    body = M.extrude(reg, 0.5)
    joints = cs_union([rect(b[0] - 1, v - 0.1, b[2] + 1, v + 0.1) for v in np.arange(b[1] + 1.6, b[3], 1.6)])
    grain = cs_union([rect(u, v, u + rng.uniform(2.0, 6.0), v + 0.12) for v in np.arange(b[1] + 0.4, b[3], 0.55)
                      for u in np.arange(b[0], b[2], 7.0) + rng.uniform(0, 3.0)])
    return body - ext(joints ^ reg, 0.3, 1.0) - ext(grain ^ reg, 0.42, 1.0)


def frieze_glasgowrose(L, h, b, pitch, margin, pair, half):
    """Glasgow roses: at every station a rose of three concentric rings on a long straight stem
    with two leaves; a pair of level lines between (the Stickley)."""
    v0, v1 = 0.6, h - 0.6
    hh = v1 - v0
    out = []
    for u in CO._us(L, pitch, margin, 0.0):
        r = min(1.3, hh * 0.32)
        c = (u, v1 - r - 0.1)
        rose = cs_union([circle(c, r, 24) - circle(c, r - 0.35, 24), circle(c, r * 0.55, 20) - circle(c, r * 0.55 - 0.3, 16),
                         circle(c, 0.25, 10)])
        stem = [rect(u - 0.2, v0, u + 0.2, c[1] - r + 0.1), oval((u - 0.7, v0 + hh * 0.3), 0.6, 0.3, 12), oval((u + 0.7, v0 + hh * 0.3), 0.6, 0.3, 12)]
        out.append(_st(cs_union([rose] + stem), b, 0.45))
    for uc, wd in CO._between(L, pitch, margin, pair, half + 2.2):
        if wd < 2.0:
            continue
        out.append(_st(cs_union([rect(uc - wd / 2, v0 + hh * 0.3, uc + wd / 2, v0 + hh * 0.3 + 0.35),
                                 rect(uc - wd / 2, v0 + hh * 0.6, uc + wd / 2, v0 + hh * 0.6 + 0.35)]), b, 0.3))
    return out, []


def frieze_heartleaf(L, h, b, pitch, margin, pair, half):
    """An Arts and Crafts leaf trail: a stem running in shallow waves the length of the
    frieze with a heart-shaped leaf in every bend (the Stickley)."""
    v0, v1 = 0.6, h - 0.6
    hh = v1 - v0
    vm = v0 + hh / 2
    wl = max(4.0, pitch * 0.5)
    xs = np.linspace(margin * 0.5, L - margin * 0.5, max(8, int(L * 2)))
    amp = hh * 0.2
    parts = [stroke([(x, vm + amp * math.sin(2 * math.pi * x / wl)) for x in xs], 0.38, caps=False)]
    for k in range(int(L / (wl / 2))):
        x = wl / 4 + k * wl / 2
        if x > L - margin * 0.5 or x < margin * 0.5:
            continue
        sg = 1 if k % 2 == 0 else -1
        c = (x, vm + sg * (amp + 0.9))
        leaf = _heart(c, 1.3)
        if sg < 0:
            leaf = leaf.mirror((0, 1)).translate((0, 2 * c[1])) if hasattr(leaf, "mirror") else leaf
        parts.append(leaf)
    return [_st(cs_union(parts) ^ rect(0, v0, L, v1), b, 0.4)], []


def course_keyedtenons(L, h, b, pitch, margin, p):
    """Through-tenons at intervals, each held by a tapered key, along a plain band."""
    parts = []
    for u in np.arange(1.6, L - 1.0, 3.2):
        parts.append(ext(rect(u - 0.6, 0.15, u + 0.6, h - 0.15), b - 0.05, b + 0.55))
        parts.append(ext(poly([(u - 0.25, h * 0.5 - 0.5), (u + 0.25, h * 0.5 - 0.5), (u + 0.15, h * 0.5 + 0.5), (u - 0.15, h * 0.5 + 0.5)]), b + 0.5, b + 0.8))
    return parts


def bracket_twintails(h, d, t):
    """Paired rafter tails read in profile: a long tail whose end is cut in a double step."""
    hb = max(1.6, min(h, 2.4))
    return poly([(0.0, 0.0), (d, 0.0), (d, -hb * 0.35), (d - 0.6, -hb * 0.35), (d - 0.6, -hb * 0.7), (d - 1.2, -hb * 0.7),
                 (d - 1.2, -hb), (0.0, -hb)])


CO.FRIEZE_EXTRA.update(glasgowrose=frieze_glasgowrose, heartleaf=frieze_heartleaf)
CO.COURSE_EXTRA.update(keyedtenons=course_keyedtenons)
TW.BRACKET_EXTRA.update(twintails=bracket_twintails)
TW.FOUNDATION_EXTRA.update(boardformed=foundation_boardformed)


def _tenon_head(hw, v, t=1.0):
    """A Craftsman head casing: a thick board running past the side casings, a through-tenon
    showing at each end held by a pegged key."""
    parts = [chamfer_box(-hw - 1.8, v, hw + 1.8, v + 2.0, 0.0, t, c=0.25)]
    for sg in (-1, 1):
        x = sg * (hw + 1.1)
        parts.append(chamfer_box(x - 0.55, v + 0.4, x + 0.55, v + 1.6, t - 0.01, 0.6, c=0.15))
        parts.append(ext(circle((x, v + 1.0), 0.28, 10), t + 0.55, t + 0.85))
    return parts


def window_stickley(w, h, n=2, upper=False, A=1.2):
    """The Stickley's casements: ``n`` leaves, each with a grid of small panes across its top
    third over one big pane, between square mullions. Downstairs the head is a thick board with
    keyed through-tenons over a plain sill; upstairs the head is cut in a shallow arch on its
    underside and the sill rides on a pair of pegged corbels (the storeys differ)."""
    op = O.opening_cs(w, h, 0)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    u0, v0, u1, v1 = plug_cs.offset(-0.5, JoinType.Miter, 4.0).bounds()
    mull = 1.0
    cw = (u1 - u0 - (n - 1) * mull) / n
    vt = v1 - (v1 - v0) * 0.33
    bars = []
    for j in range(n):
        a = u0 + j * (cw + mull)
        bars.append(rect(a - 1, vt - 0.22, a + cw + 1, vt + 0.22))
        bars.append(rect(a - 1, (vt + v1) / 2 - 0.2, a + cw + 1, (vt + v1) / 2 + 0.2))
        for k in (1, 2):
            bars.append(rect(a + cw * k / 3 - 0.2, vt, a + cw * k / 3 + 0.2, v1 + 1))
    g = cs_union([rect(u0 + j * (cw + mull), v0, u0 + j * (cw + mull) + cw, v1) for j in range(n)])
    sash = _glazed([ext(plug_cs, -pl, -0.6)], g, pl, cs_union(bars), plug_cs)
    for j in range(1, n):
        a = u0 + j * (cw + mull) - mull
        sash.append(ext(rect(a, v0, a + mull, v1), -pl, 0.4))
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, 0.7),
             ext((op.offset(A, JoinType.Miter, 4.0) - op) ^ rect(-w, 0.0, w, h + A), 0.0, 0.8)]
    hw = w / 2 + A
    if upper:
        head = rect(-hw - 1.0, h + A - 0.01, hw + 1.0, h + A + 2.2) - (circle((0.0, h + A - w * 1.6), w * 1.6 + 0.9, 60) ^ rect(-hw + 0.8, h, hw - 0.8, h + A + 1.0))
        parts.append(ext(head, 0.0, 1.1))
        parts.append(chamfer_box(-hw - 1.0, -1.0, hw + 1.0, 0.2, 0.0, 1.4, c=0.35, bottom=0.8))
        for sg in (-1, 1):
            x = sg * (hw - 0.8)
            for k in range(5):
                parts.append(box([x - 0.5, -1.0 - (k + 1) * 0.5, 0.0], [x + 0.5, -1.0 - k * 0.5 + 0.01, 1.3 * math.cos(math.asin(min(1.0, (k + 0.5) / 5)))]))
            parts.append(ext(circle((x, -2.0), 0.25, 10), 0.9, 1.3))
        top, bot = h + A + 2.2, -3.5
    else:
        parts += _tenon_head(hw, h + A - 0.01)
        parts.append(chamfer_box(-hw - 0.8, -1.0, hw + 0.8, 0.2, 0.0, 1.3, c=0.35, bottom=0.8))
        parts.append(ext(rect(-hw + 0.4, -2.2, hw - 0.4, -0.99), 0.0, 0.7))
        top, bot = h + A + 2.0, -2.2
    return O._one_piece(sash, parts, op, plug_cs, pl, top, bot)


def door_stickley(w=11.0, h=24.0, A=1.4, glazed=False):
    """The Stickley's doors: a heavy leaf of vertical boards with three small square lights in
    a row near the top over a dentil shelf, long wrought strap hinges ending in arrow heads, a
    ring knocker, under the keyed tenon head. ``glazed``: the sleeping porch's door, glazed in
    small panes above a single panel."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    leaf = plug_cs.offset(-0.3, JoinType.Miter, 4.0)
    u0, v0, u1, v1 = leaf.bounds()
    if glazed:
        win = rect(u0 + 1.0, v0 + (v1 - v0) * 0.42, u1 - 1.0, v1 - 1.0)
        wb = win.bounds()
        bars = cs_union([rect(x - 0.2, wb[1] - 1, x + 0.2, wb[3] + 1) for x in np.linspace(wb[0], wb[2], 4)[1:-1]] +
                        [rect(wb[0] - 1, y - 0.2, wb[2] + 1, y + 0.2) for y in np.linspace(wb[1], wb[3], 5)[1:-1]])
        body = [ext(plug_cs, -pl, -1.0), ext(leaf - win, -1.0, -0.6), chamfer_box(u0 + 1.0, v0 + 1.0, u1 - 1.0, v0 + (v1 - v0) * 0.42 - 1.0, -0.6, 0.3, c=0.15)]
        sash = _glazed(body, win, pl, bars, plug_cs)
    else:
        lights = cs_union([rect(u0 + 1.0 + k * (u1 - u0 - 2.0) / 3 + 0.3, v1 - 4.2, u0 + 1.0 + (k + 1) * (u1 - u0 - 2.0) / 3 - 0.3, v1 - 1.6) for k in range(3)])
        boards = cs_union([rect(u0 + k * (u1 - u0) / 5 - 0.12, v0, u0 + k * (u1 - u0) / 5 + 0.12, v1 - 5.0) for k in range(1, 5)])
        body = [ext(plug_cs, -pl, -1.0), ext(leaf - lights - boards, -1.0, -0.6), ext(leaf - lights, -1.0, -0.8)]
        body.append(chamfer_box(u0 + 0.6, v1 - 5.4, u1 - 0.6, v1 - 4.6, -0.6, 0.5, c=0.15))
        body.append(ext(cs_union([rect(x - 0.22, v1 - 5.9, x + 0.22, v1 - 5.4) for x in np.arange(u0 + 1.0, u1 - 0.6, 0.9)]), -0.6, -0.3))
        for v in (h * 0.18, h * 0.55):
            xe = u0 + (u1 - u0) * 0.7
            body.append(ext(cs_union([rect(u0 + 0.2, v - 0.35, xe, v + 0.35), poly([(xe - 0.1, v - 0.8), (xe + 1.0, v), (xe - 0.1, v + 0.8)])]) ^ leaf, -0.7, -0.35))
        body.append(ext(circle((u1 - 1.5, h * 0.42), 0.8, 16) - circle((u1 - 1.5, h * 0.42), 0.4, 12), -0.7, -0.35))
        sash = _glazed(body, lights, pl, None, plug_cs)
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, 0.7),
             ext((op.offset(A, JoinType.Miter, 4.0) - op) ^ rect(-w, 0.0, w, h + A), 0.0, 0.8)]
    parts += _tenon_head(w / 2 + A, h + A - 0.01)
    return O._one_piece(sash, parts, op, plug_cs, pl, h + A + 2.0, 0.0)


def post_stickley(h, collar=None, abacus=3.4, slot=None):
    """A Stickley porch post: a plain round shaft on a square block, carrying a bolster (a
    short beam across the top, its ends cut in a double step) under a square cap."""
    zt = h - 3.2
    body = PW._plinth(3.4, 1.2) + box([-1.6, -1.6, 1.19], [1.6, 1.6, 3.0])
    body = body + PW._revolve([(0.0, 2.99), (1.25, 2.99), (1.2, zt), (0.0, zt)], 32)
    bol = poly([(-3.4, 0.0), (3.4, 0.0), (3.4, -0.6), (2.9, -0.6), (2.9, -1.1), (2.4, -1.1), (2.0, -1.6), (-2.0, -1.6), (-2.4, -1.1),
                (-2.9, -1.1), (-2.9, -0.6), (-3.4, -0.6)])
    body = body + ext(bol, -1.0, 1.0).transform(np.array([[1.0, 0, 0, 0], [0, 0, 1.0, 0], [0, 1.0, 0, h - 1.59]]))
    return body + box([-1.7, -1.7, zt - 0.01], [1.7, 1.7, h])


def fill_splats(L, vb, vt):
    """A railing of broad flat splats alternating with pairs of thin sticks."""
    parts = [rect(0.0, vb, L, vb + 1.0), rect(0.0, vt - 1.3, L, vt)]
    n = max(1, int(L / 4.2))
    for k in range(n):
        c = L * (k + 0.5) / n
        parts.append(rect(c - 0.9, vb, c + 0.9, vt))
        if k < n - 1:
            c2 = L * (k + 1) / n
            parts += [rect(c2 - 0.75, vb, c2 - 0.35, vt), rect(c2 + 0.35, vb, c2 + 0.75, vt)]
    return parts


def fill_shakeparapet(L, vb, vt):
    """A solid parapet for the sleeping porch, faced in shakes (grooved courses), with a flat
    capping rail."""
    board = rect(0.0, vb, L, vt)
    grooves = cs_union([rect(-1, v - 0.2, L + 1, v + 0.2) for v in np.arange(vb + 2.0, vt - 1.5, 2.0)])
    return dict(cs=[board], grooves=grooves, t=1.2, depth=0.15)    # grooves sunk into the faces, not through


def frieze_bolsterbeam(u0, u1, v_bot, v_top):
    """A porch beam whose ends step down onto bolsters over the posts."""
    v0 = v_top - 2.6
    beam = rect(u0, v0, u1, v_top + 0.05)
    L = u1 - u0
    c = min(2.6, L * 0.14)
    for (a, sg) in ((u0, 1), (u1, -1)):
        beam = beam + poly([(a, v0 + 0.01), (a + sg * c, v0 + 0.01), (a + sg * c, v0 - 0.5), (a + sg * c * 0.5, v0 - 0.5), (a + sg * c * 0.5, v0 - 1.0), (a, v0 - 1.0)])
    return beam


def edge_twinrafters(L, z0, zc):
    """Porch fascia (the Stickley): rafter tails in pairs under the roof's edge."""
    xs = np.arange(1.2, L - 1.0, 3.4)
    return cs_union([rect(x - 0.35, zc - 1.6, x + 0.35, zc) for x in xs] + [rect(x + 0.9 - 0.35, zc - 1.6, x + 0.9 + 0.35, zc) for x in xs if x + 1.3 < L]) + \
        rect(0.3, zc - 0.5, L - 0.3, zc), 0.8


def skirt_formboard(reg, d=1.2):
    """A porch skirt of board-formed concrete with a square vent in every bay."""
    if reg.is_empty():
        return M()
    u0, v0, u1, v1 = reg.bounds()
    body = M.extrude(reg, d * 0.55) - ext(cs_union([rect(u0 - 1, v - 0.1, u1 + 1, v + 0.1) for v in np.arange(v0 + 1.4, v1, 1.4)]) ^ reg, d * 0.4, d)
    vents = cs_union([rect(u - 1.2, (v0 + v1) / 2 - 1.0, u + 1.2, (v0 + v1) / 2 + 1.0) for u in np.arange(u0 + 6.0, u1 - 3.0, 12.0)]) ^ reg
    return body - ext(vents, d * 0.2, d)


PW.POSTS.update(stickley=post_stickley)
PW.FILLS.update(splats=fill_splats, shakeparapet=fill_shakeparapet)
PW.FRIEZES.update(bolsterbeam=frieze_bolsterbeam)
PW.SKIRTS.update(formboard=skirt_formboard)
FT.EDGE_EXTRA.update(twinrafters=edge_twinrafters)


def pergola(x0, x1, y_wall, y_front, zp, posts_x, post_h, z_foot, peg=1.6):
    """The Stickley's entrance pergola, one piece: round posts (Stickley bolster tops) at the
    front corners, a beam from each post back to the wall, and cross rafters over them, every
    end cut in a double step; square pegs under the posts. Prints upside down on its rafters."""
    out = []
    for x in posts_x:
        out.append(post_stickley(post_h).translate([x, y_front + 1.8, z_foot]))
        out.append(box([x - peg / 2, y_front + 1.8 - peg / 2, z_foot - 1.6], [x + peg / 2, y_front + 1.8 + peg / 2, z_foot + 0.01]))
        prof = poly([(y_front - 1.6, zp - 0.9), (y_front - 1.6, zp), (y_wall, zp), (y_wall, zp - 2.6), (y_front + 0.6, zp - 2.6),
                     (y_front - 0.3, zp - 1.8), (y_front - 0.9, zp - 1.8), (y_front - 0.9, zp - 0.9)])
        out.append(ext(prof, x - 1.0, x + 1.0).transform(np.array([[0, 0, 1.0, 0], [1.0, 0, 0, 0], [0, 1.0, 0, 0]])))
    for y in np.arange(y_wall - 1.4, y_front - 0.5, -2.8):
        prof = poly([(x0, zp + 1.6), (x1, zp + 1.6), (x1, zp + 0.8), (x1 - 0.6, zp + 0.8), (x1 - 1.2, zp - 0.01), (x0 + 1.2, zp - 0.01),
                     (x0 + 0.6, zp + 0.8), (x0, zp + 0.8)])
        out.append(ext(prof, y - 0.55, y + 0.55).transform(np.array([[1.0, 0, 0, 0], [0, 0, 1.0, 0], [0, 1.0, 0, 0]])))
    return union(out)


# ================================================================== the Sandoval (Pueblo Revival)
def adobe_plaster(region, seed=0, parts=False):
    """Mud plaster over adobe: a soft smooth coat, and here and there a patch where it has
    fallen away to show the big adobe bricks beneath (the Sandoval). ``parts``: also return
    the bared bricks (for the render's colour zone)."""
    if region.is_empty():
        return (M(), M()) if parts else M()
    u0, v0, u1, v1 = region.bounds()
    rng = np.random.default_rng(seed + 83)
    out = M.extrude(region, 0.35)
    patches = []
    n = max(1, int((u1 - u0) * (v1 - v0) / 700.0))
    for _ in range(n):
        c = (rng.uniform(u0 + 6, max(u0 + 6.1, u1 - 6)), rng.uniform(v0 + 5, max(v0 + 5.1, v1 - 5)))
        blob = cs_union([oval((c[0] + rng.uniform(-2, 2), c[1] + rng.uniform(-1, 1)), rng.uniform(2.5, 4.5), rng.uniform(1.6, 2.6), 18) for _ in range(3)])
        patches.append(blob)
    bricks = M()
    if patches:
        pz = cs_union(patches) ^ region.offset(-1.0, JoinType.Miter, 4.0)
        if not pz.is_empty():
            pb = pz.bounds()
            br = []
            for k, v in enumerate(np.arange(pb[1] - 1.3, pb[3] + 1.3, 1.3)):
                for u in np.arange(pb[0] - 3.6 + (k % 2) * 1.8, pb[2] + 3.6, 3.6):
                    br.append(rect(u + 0.15, v + 0.15, u + 3.45, v + 1.15))
            bcs = cs_union(br) ^ pz
            out = out - ext(pz, 0.12, 1.0)
            bricks = ext(bcs, 0.05, 0.22)
            out = out + bricks
    return (out, bricks) if parts else out


def foundation_adobeplinth(reg, seed=0):
    """A low plinth of hard plaster over stone, its top edge rounded and its face scored
    where the mud was troweled (the Sandoval)."""
    b = reg.bounds()
    rng = np.random.default_rng(seed + 5)
    body = M.extrude(reg, 0.5) + ext(reg ^ rect(b[0] - 1, b[3] - 0.6, b[2] + 1, b[3]), 0.0, 0.8)
    swipes = cs_union([stroke([(u, v), (u + rng.uniform(2.0, 4.0), v + rng.uniform(-0.4, 0.4))], 0.2, caps=True)
                       for u in np.arange(b[0], b[2], 3.5) for v in np.arange(b[1] + 0.8, b[3] - 1.0, 1.6) if rng.random() < 0.5])
    return body - ext(swipes ^ reg, 0.35, 1.0)


def frieze_vigas(L, h, b, pitch, margin, pair, half):
    """Vigas: the round ends of the roof beams standing out of the wall in a row, each end
    ringed with its bark line; between them the ends of the smaller latillas (the Sandoval)."""
    v0, v1 = 0.4, h - 0.4
    hh = v1 - v0
    vc = v0 + hh * 0.55
    out = []
    r = min(1.5, hh * 0.38)
    for u in np.arange(margin, L - margin + 0.1, max(pitch * 0.5, 5.0)):
        out.append(_st(circle((u, vc), r, 24), b, 1.5))
        out.append(_st(circle((u, vc), r - 0.35, 20), b, 1.8))
    return out, []


def frieze_cloudterrace(L, h, b, pitch, margin, pair, half):
    """Pueblo cloud terraces: at every station a stepped pyramid of three steps (the rain
    cloud), and between them a row of little rain lines hanging from a bar (the Sandoval)."""
    v0, v1 = 0.6, h - 0.6
    hh = v1 - v0
    out = []
    for u in CO._us(L, pitch, margin, 0.0):
        steps_ = cs_union([rect(u - 2.4 + k * 0.8, v0 + k * hh / 3, u + 2.4 - k * 0.8, v0 + (k + 1) * hh / 3) for k in range(3)])
        out.append(_st(steps_ - rect(u - 0.3, v0 - 1, u + 0.3, v0 + hh * 0.5), b, 0.45))
    for uc, wd in CO._between(L, pitch, margin, pair, half + 2.8):
        if wd < 2.4:
            continue
        rain = [rect(uc - wd / 2, v1 - 0.5, uc + wd / 2, v1)] + [rect(x - 0.15, v0 + hh * 0.3, x + 0.15, v1 - 0.49) for x in np.arange(uc - wd / 2 + 0.5, uc + wd / 2 - 0.3, 0.9)]
        out.append(_st(cs_union(rain), b, 0.3))
    return out, []


def course_latillas(L, h, b, pitch, margin, p):
    """Latillas: the ends of peeled saplings laid close over the vigas, a row of little
    round butts."""
    r = min(0.45, h * 0.3)
    return [ext(cs_union([circle((u, h / 2), r, 12) for u in np.arange(0.6, L - 0.4, 2 * r + 0.18)]), b - 0.05, b + 0.45)]


CO.FRIEZE_EXTRA.update(vigas=frieze_vigas, cloudterrace=frieze_cloudterrace)
CO.COURSE_EXTRA.update(latillas=course_latillas)
TW.FOUNDATION_EXTRA.update(adobeplinth=foundation_adobeplinth)


def _adzed_lintel(hw, v, t=1.6, over=2.4, hh=2.6):
    """A heavy timber lintel running past the opening, its face adzed in shallow scallops."""
    lin = box([-hw - over, v, 0.0], [hw + over, v + hh, t])
    adz = cs_union([circle((x, v + hh / 2), 0.9, 14) for x in np.arange(-hw - over + 1.0, hw + over - 0.5, 1.7)])
    return lin - ext(adz ^ rect(-hw - over, v + 0.3, hw + over, v + hh - 0.3), t - 0.18, t + 1.0)


def window_pueblo(w, h, upper=False, A=1.0):
    """The Sandoval's windows, turquoise, deep in soft reveals: a casement pair of three panes
    a leaf. Downstairs under an adzed timber lintel on a rounded plaster sill; upstairs the
    lintel rides on two carved corbels (zapatas) and a little nicho of a sill-board below
    (the storeys differ). Two colours: turquoise, then wood from the wall face out."""
    op = O.opening_cs(w, h, 0)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    u0, v0, u1, v1 = plug_cs.offset(-0.6, JoinType.Miter, 4.0).bounds()
    bars = cs_union([rect(-0.4, v0 - 1, 0.4, v1 + 1)] + [rect(u0 - 1, v0 + (v1 - v0) * k / 3 - 0.2, u1 + 1, v0 + (v1 - v0) * k / 3 + 0.2) for k in (1, 2)])
    sash = _glazed([ext(plug_cs, -pl, -1.0)], rect(u0, v0, u1, v1), pl, bars, plug_cs)
    reveal = (op.offset(A, JoinType.Round) - op) ^ rect(-w, -0.5, w, h)
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), -0.6, 0.0), ext(reveal, 0.0, 0.5)]
    hw = w / 2
    parts.append(_adzed_lintel(hw, h - 0.01))
    if upper:
        for sg in (-1, 1):
            x = sg * (hw + 1.2)
            z = poly([(x - 1.2, h), (x + 1.2, h), (x + 1.2, h - 0.6), (x + 0.6, h - 0.6), (x + 0.4, h - 1.2), (x - 0.4, h - 1.2), (x - 0.6, h - 0.6), (x - 1.2, h - 0.6)])
            parts.append(ext(z, 0.0, 1.5))
        parts.append(chamfer_box(-hw - 1.4, -1.2, hw + 1.4, 0.2, 0.0, 1.4, c=0.3, bottom=0.8))
        bot = -1.2
    else:
        sill = M.hull_points([(x, -1.4, 0.0) for x in (-hw - 1.2, hw + 1.2)] + [(x, 0.2, 0.0) for x in (-hw - 1.2, hw + 1.2)] +
                             [(x, -0.4, 1.3) for x in (-hw - 1.2, hw + 1.2)] + [(x, 0.2, 1.3) for x in (-hw - 1.2, hw + 1.2)])
        parts.append(sill)
        bot = -1.4
    return O._one_piece(sash, parts, op, plug_cs, pl, h + 2.6, bot)


def door_pueblo(w=11.0, h=23.0, glazed=False):
    """The Sandoval's doors, turquoise: a carved Spanish door of four panels, each chip-carved
    with a rosette, under an adzed lintel on zapatas. ``glazed``: the roof-terrace door, its
    upper half six small panes."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    leaf = plug_cs.offset(-0.3, JoinType.Miter, 4.0)
    u0, v0, u1, v1 = leaf.bounds()
    body = [ext(plug_cs, -pl, -1.0)]
    pw = (u1 - u0 - 1.8) / 2
    rows = (0.12, 0.5) if glazed else (0.08, 0.36, 0.64)
    ph = (v1 - v0) * (0.34 if glazed else 0.24)
    win = rect(u0 + 0.8, v0 + (v1 - v0) * 0.52, u1 - 0.8, v1 - 0.8) if glazed else None
    body.append(ext(leaf - (win if glazed else rect(0, 0, 0, 0)), -1.0, -0.6))
    for fr in rows[:1] if glazed else rows:
        for k in range(2):
            a = u0 + 0.6 + k * (pw + 0.6)
            vb = v0 + (v1 - v0) * fr
            body.append(chamfer_box(a, vb, a + pw, vb + ph, -0.6, 0.35, c=0.15))
            c = (a + pw / 2, vb + ph / 2)
            ros = cs_union([oval((c[0] + 0.55 * math.cos(t), c[1] + 0.55 * math.sin(t)), 0.45, 0.2, 10) for t in np.linspace(0, math.pi, 4, endpoint=False)] +
                           [stroke([(c[0] - 0.9 * math.cos(t), c[1] - 0.9 * math.sin(t)), (c[0] + 0.9 * math.cos(t), c[1] + 0.9 * math.sin(t))], 0.3, caps=True)
                            for t in np.linspace(0, math.pi, 4, endpoint=False)])
            body.append(ext(ros ^ rect(a + 0.3, vb + 0.3, a + pw - 0.3, vb + ph - 0.3), -0.3, -0.05))
    if glazed:
        wb = win.bounds()
        bars = cs_union([rect((wb[0] + wb[2]) / 2 - 0.2, wb[1] - 1, (wb[0] + wb[2]) / 2 + 0.2, wb[3] + 1)] +
                        [rect(wb[0] - 1, y - 0.2, wb[2] + 1, y + 0.2) for y in np.linspace(wb[1], wb[3], 4)[1:-1]])
        sash = _glazed(body, win, pl, bars, plug_cs)
    else:
        sash = body
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), -0.6, 0.0), ext((op.offset(1.0, JoinType.Round) - op) ^ rect(-w, 0.0, w, h), 0.0, 0.5)]
    parts.append(_adzed_lintel(w / 2, h - 0.01, over=3.0))
    for sg in (-1, 1):
        x = sg * (w / 2 + 1.6)
        parts.append(ext(poly([(x - 1.4, h), (x + 1.4, h), (x + 1.4, h - 0.7), (x + 0.7, h - 0.7), (x + 0.4, h - 1.4), (x - 0.4, h - 1.4), (x - 0.7, h - 0.7), (x - 1.4, h - 0.7)]), 0.0, 1.5))
    return O._one_piece(sash, parts, op, plug_cs, pl, h + 2.6, 0.0)


def post_sandoval(h, collar=None, abacus=3.4, slot=None):
    """A portal post: a peeled log (round, a little irregular, a slight taper) on a flat stone,
    carrying a zapata, a long corbel block whose ends are carved in steps and a scroll."""
    zt = h - 2.4
    body = box([-1.8, -1.8, 0.0], [1.8, 1.8, 1.0])
    body = body + PW._revolve([(0.0, 0.99), (1.35, 0.99), (1.25, zt * 0.5), (1.3, zt * 0.55), (1.15, zt), (0.0, zt)], 28)
    zap = poly([(-4.2, 0.0), (4.2, 0.0), (4.2, -0.8), (3.6, -0.8), (3.3, -1.4), (2.4, -1.4), (1.6, -2.4), (-1.6, -2.4), (-2.4, -1.4),
                (-3.3, -1.4), (-3.6, -0.8), (-4.2, -0.8)])
    body = body + ext(zap, -1.1, 1.1).transform(np.array([[1.0, 0, 0, 0], [0, 0, 1.0, 0], [0, 1.0, 0, h]]))
    return body + box([-1.3, -1.3, zt - 0.2], [1.3, 1.3, h - 2.3])


def fill_banco(L, vb, vt):
    """A low adobe wall (a banco) between the posts, its top rounded over."""
    return [rect(0.0, vb, L, vt - 0.6), rect(0.3, vt - 0.61, L - 0.3, vt)]


def frieze_zapatabeam(u0, u1, v_bot, v_top):
    """A portal beam (a squared viga) laid over the zapatas, its underside plain."""
    return rect(u0, v_top - 2.6, u1, v_top + 0.05)


def edge_canales(L, z0, zc):
    """The portal roof's edge: a flat fascia of latilla ends (little round butts)."""
    return rect(0.3, zc - 0.5, L - 0.3, zc) + cs_union([circle((x, zc - 0.9), 0.45, 12) for x in np.arange(0.8, L - 0.5, 1.1)]), 0.7


def skirt_adobe(reg, d=1.2):
    """A plain plastered porch skirt with a rounded top."""
    if reg.is_empty():
        return M()
    b = reg.bounds()
    return M.extrude(reg, d * 0.55) + ext(reg ^ rect(b[0] - 1, b[3] - 0.6, b[2] + 1, b[3]), 0.0, d * 0.75)


PW.POSTS.update(sandoval=post_sandoval)
PW.FILLS.update(banco=fill_banco)
PW.FRIEZES.update(zapatabeam=frieze_zapatabeam)
PW.SKIRTS.update(adobe=skirt_adobe)
FT.EDGE_EXTRA.update(canales=edge_canales)


def roof_tray(outer_cs, z0, deck=1.6, parapet=7.0, band=2.4, hole=None, gap=None):
    """A flat Pueblo roof in one piece: a deck with a parapet round its edge whose top is
    rounded over, seated on the walls' lip like any roof; ``hole`` is cut through it (a
    storey rising through the roof), ``gap`` from the parapet only."""
    d = slab(outer_cs, z0, z0 + deck)
    ring = outer_cs - outer_cs.offset(-band, JoinType.Miter, 4.0)
    par = slab(ring, z0 + deck - 0.01, z0 + parapet - 0.7) + slab(ring.offset(-0.35, JoinType.Round) ^ outer_cs.offset(-0.35, JoinType.Round), z0 + parapet - 0.71, z0 + parapet)
    t = d + par
    if gap is not None:
        t = t - gap
    if hole is not None:
        t = t - hole
    return t


def canale(z, L=3.0, w=1.8):
    """A canale (a roof spout): a wooden trough running out through the parapet a little
    above the deck, its underside sloped back to the wall at 45 degrees so it prints on the
    parapet without ever reaching below the tray's foot. Local: x across, y out from the wall
    face (y = 0), z up; ``z`` = the trough's floor at the wall."""
    top = z + 1.4
    body = M.hull_points([(x, 0.0, z - L + 0.2) for x in (-w / 2, w / 2)] + [(x, L, z) for x in (-w / 2, w / 2)] +
                         [(x, 0.0, top) for x in (-w / 2, w / 2)] + [(x, L, top) for x in (-w / 2, w / 2)])
    body = body + box([-w / 2, -2.6, z], [w / 2, 0.01, top])
    return body - box([-w / 2 + 0.45, -3.0, z + 0.6], [w / 2 - 0.45, L + 1.0, top + 1.0])


def chimney_kiva(h=22.0, r0=5.0, r1=3.4):
    """The kiva chimney: a round plastered stack swelling at the foot and tapering up, a
    rounded collar and a domed cap pierced by two flues; a square peg under it."""
    h = round(h / 0.2) * 0.2
    zt = h - 3.4
    body = PW._revolve([(0.0, 0.0), (r0 + 0.8, 0.0), (r0, 1.6), (r1 + 0.3, zt * 0.7), (r1, zt), (0.0, zt)], 40)
    body = body + PW._revolve([(0.0, zt - 0.01), (r1 + 0.6, zt - 0.01), (r1 + 0.6, zt + 0.8), (r1 - 0.2, zt + 1.4), (r1 - 0.8, h - 0.6), (0.0, h)], 40)
    for sg in (-1, 1):
        body = body - box([sg * r1 * 0.45 - 0.7, -r1 - 1, zt + 1.4], [sg * r1 * 0.45 + 0.7, r1 + 1, zt + 2.6])
    return body


def horno(r=6.5, h=8.5):
    """An horno, the beehive oven of the Pueblo yard: a plastered dome on a low square base,
    an arched mouth in front and a small smoke hole high on the side (a separate piece for
    the yard)."""
    base = box([-r - 1.4, -r - 1.4, 0.0], [r + 1.4, r + 1.4, 1.2])
    prof = [(0.0, 1.19)] + [(r * math.cos(a) ** 0.8, 1.19 + h * math.sin(a)) for a in np.linspace(0.0, math.pi / 2, 14)]
    dome = PW._revolve(prof, 40)
    mouth = cs_union([rect(-1.8, 1.2, 1.8, 3.4), circle((0.0, 3.4), 1.8, 20)])
    cut = M.extrude(mouth, r + 2).rotate([90, 0, 0]).translate([0, -0.5, 0])
    smoke = M.cylinder(r + 2, 0.5, 0.5, 12).rotate([0, 90, 0]).translate([0, 0, 1.2 + h * 0.7])
    return base + dome - cut - smoke

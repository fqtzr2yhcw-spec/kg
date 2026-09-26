"""Free Classic parts: the Colonial-front houses with a Victorian flair (houses 39 and 40 of
the Colonial batch). Each part belongs to one building, named in its docstring; none is
shared with another building.

Importing this module registers its cornice friezes, brackets and foundations with the
cornice and trim libraries, and its porch posts, balusters, friezes, skirts, pier facings and
roof edges with the porch library, as hoarch.colonial does for its houses.
"""
import math

import numpy as np
from manifold3d import JoinType, Manifold as M

from .core import box, circle, cs_union, frame, poly, rect, union, zq
from .ornament import chamfer_box, ext, oval, stroke
from . import cornice as CO, trimwork as TW
from .colonial import _st


# ================================================================== the Ellsworth (house 39)
def siding_double(region, datum=0.0, p=2.4):
    """Double-course lap siding: every board milled to read as two narrow courses, a deep
    shadow at its butt and a shallower one half way up."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    v = datum
    while v > v0 - 2.0:
        v -= p
    h = p / 2
    pts = [(v, 0.0)]
    while v < v1 + 2.0:
        pts += [(v, 0.34), (v + 0.2, 0.44), (v + h, 0.14), (v + h, 0.30), (v + h + 0.2, 0.33), (v + p, 0.06)]
        v += p
    pts.append((v, 0.0))
    strip = M.extrude(poly(pts), (u1 - u0) + 2).transform(frame([u0 - 1, 0, 0], [0, 1, 0], [0, 0, 1], [1, 0, 0]))
    return strip ^ M.extrude(region, 0.7).translate([0, 0, -0.1])


def shingles_undulating(region, datum=0.0, pitch=2.0, wtab=1.8, d=0.42, amp=0.5, wave=22.0, gap=0.5, lap=1.5,
                        taper=0.7):
    """Wave-coursed shingles: square-butt shingles whose courses rise and fall together in a
    long, gentle wave along the wall."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    span = pitch * lap

    def butt(u, k):
        return datum + k * pitch + amp * math.sin(2 * math.pi * u / wave)

    rows = []
    for k in range(math.floor((v0 - datum - amp) / pitch) - 1, math.ceil((v1 - datum + amp) / pitch) + 1):
        tabs = []
        u = u0 - wtab * 1.5 + (k % 2) * wtab * 0.5
        while u < u1 + wtab:
            xs = np.linspace(u + gap / 2, u + wtab - gap / 2, 4)
            tabs.append(poly([(x, butt(x, k)) for x in xs] + [(x, butt(x, k) + span) for x in reversed(xs)]))
            u += wtab
        row = cs_union(tabs) ^ region
        if row.is_empty():
            continue

        def f(P, k=k):
            P = np.array(P)
            t = np.clip((P[:, 1] - datum - k * pitch - amp * np.sin(2 * np.pi * P[:, 0] / wave)) / span, 0, 1)
            P[:, 2] *= (1 - taper * t)
            return P

        rows.append(M.extrude(row, d).warp_batch(f))
    return union(rows)


def foundation_cobble(reg, seed=0):
    """Cobblestone: rows of small rounded field cobbles laid in horizontal courses, a raised
    mortar ridge along every course, under a smooth chamfered cap of cut stone."""
    b = reg.bounds()
    rng = np.random.default_rng(seed + 11)
    out = []
    top = zq(b[3] - 1.2)
    v, k = zq(b[1]), 0
    while v < top - 0.8:
        vt = min(v + 1.6, top)
        u = b[0] - rng.uniform(0.0, 1.2)
        while u < b[2]:
            wd = rng.uniform(1.0, 1.6)
            c0, c1 = max(u + 0.1, b[0]), min(u + wd - 0.1, b[2])
            if c1 - c0 > 0.6:
                hh = vt - v - 0.5
                ht = rng.uniform(0.34, 0.46)
                out.append(M.hull_points([(x, y, 0.0) for x in (c0, c1) for y in (v + 0.25, v + 0.25 + hh)] +
                                         [(x, y, ht) for x in (c0 + ht, c1 - ht) for y in (v + 0.25 + ht, v + 0.25 + hh - ht * 0.6)]))
            u += wd
        # the mortar ridge along the course's foot: a little V bead
        out.append(M.hull_points([(x, y, z) for x in (b[0], b[2]) for y, z in ((v - 0.1, 0.0), (v + 0.3, 0.0), (v + 0.1, 0.22))]))
        v, k = vt, k + 1
    out.append(chamfer_box(b[0], top + 0.2, b[2], b[3], 0.0, 0.6, c=0.3, bottom=0.6))
    return union(out) ^ M.extrude(reg, 2.0).translate([0, 0, -0.5])


def frieze_lyres(L, h, b, pitch, margin, pair, half):
    """Lyres: in every bay a lyre (two arms swelling out from a foot and curling in at the
    top, a yoke across them, two strings), a rosette at every station, fillets along the foot
    and head of the band."""
    v0, v1 = 0.7, h - 0.7
    out = [_st(rect(margin * 0.4, v0, L - margin * 0.4, v0 + 0.4), b, 0.25),
           _st(rect(margin * 0.4, v1 - 0.4, L - margin * 0.4, v1), b, 0.25)]
    vb, vt = v0 + 0.8, v1 - 0.7
    for uc, wd in CO._between(L, pitch, margin, pair, 0.6):
        if wd < 3.2:
            continue
        lw = min(1.3, wd * 0.28)
        arms = []
        for sg in (-1, 1):
            pts = [(uc + sg * (0.35 + lw * math.sin(math.pi * 0.85 * t)), vb + (vt - vb) * t) for t in np.linspace(0, 1, 12)]
            arms.append(stroke(pts, 0.45))
            arms.append(circle((pts[-1][0] + sg * 0.15, vt), 0.38, 12))
        arms.append(rect(uc - lw - 0.2, vt - 1.0, uc + lw + 0.2, vt - 0.55))
        arms.append(rect(uc - 0.8, vb - 0.3, uc + 0.8, vb + 0.25))
        out.append(_st(cs_union(arms), b, 0.45))
        out.append(_st(cs_union([rect(uc + dx - 0.2, vb + 0.2, uc + dx + 0.2, vt - 0.95) for dx in (-0.42, 0.42)]), b, 0.25))
    for u in CO._us(L, pitch, margin, 0.0):
        vm = (v0 + v1) / 2
        out.append(_st(circle((u, vm), 0.85, 20), b, 0.3))
        out.append(_st(circle((u, vm), 0.4, 12), b, 0.5))
    return out, []


def frieze_torches(L, h, b, pitch, margin, pair, half):
    """Torches and bowknots: an upright flaming torch in every bay (a fluted handle
    widening to a cup, a flame curling to a point), a ribbon bowknot at every station."""
    v0, v1 = 0.7, h - 0.7
    hh = v1 - v0
    out = []
    for uc, wd in CO._between(L, pitch, margin, pair, 0.6):
        if wd < 2.4:
            continue
        vc = v0 + hh * 0.5
        handle = poly([(uc - 0.3, v0 + 0.3), (uc + 0.3, v0 + 0.3), (uc + 0.55, vc), (uc - 0.55, vc)])
        cup = poly([(uc - 0.55, vc - 0.05), (uc + 0.55, vc - 0.05), (uc + 0.95, vc + 0.5), (uc - 0.95, vc + 0.5)])
        out.append(_st(cs_union([handle, cup]), b, 0.45))
        fl = [(uc + 0.8 * math.sin(math.pi * t) * (1 - t) + 0.35 * math.sin(3 * math.pi * t) * t, vc + 0.5 + (v1 - vc - 0.6) * t)
              for t in np.linspace(0, 1, 12)]
        fr = [(uc - 0.8 * math.sin(math.pi * t) * (1 - t) + 0.2 * math.sin(3 * math.pi * t) * t, vc + 0.5 + (v1 - vc - 0.6) * t)
              for t in np.linspace(1, 0, 12)]
        out.append(_st(poly(fl + fr[1:]), b, 0.4))
    for u in CO._us(L, pitch, margin, 0.0):
        vm = v0 + hh * 0.6
        bow = cs_union([oval((u - 0.75, vm), 0.7, 0.45, 16), oval((u + 0.75, vm), 0.7, 0.45, 16), circle((u, vm), 0.35, 12),
                        stroke([(u - 0.1, vm), (u - 0.6, v0 + 0.4)], 0.4), stroke([(u + 0.1, vm), (u + 0.6, v0 + 0.4)], 0.4)])
        out.append(_st(bow, b, 0.35))
    return out, []


def frieze_eggdart(L, h, b, pitch, margin, pair, half):
    """Egg and dart: a row of eggs, each in its raised shell, with a dart hanging between
    each pair."""
    v0, v1 = 0.6, h - 0.6
    vm = (v0 + v1) / 2
    ry = (v1 - v0) / 2
    step = 2.9
    n = max(1, int((L - margin * 0.6) / step))
    ua = (L - n * step) / 2 + step / 2
    out = []
    for k in range(n):
        u = ua + k * step
        shell = oval((u, vm), 1.2, ry, 28) - oval((u, vm), 0.75, ry - 0.45, 28)
        out.append(_st(shell, b, 0.3))
        out.append(_st(oval((u, vm - 0.05), 0.62, ry - 0.6, 24), b, 0.55))
        if k < n - 1:
            ud = u + step / 2
            dart = cs_union([rect(ud - 0.2, vm - 0.2, ud + 0.2, v1 - 0.1),
                             poly([(ud - 0.45, vm), (ud + 0.45, vm), (ud, vm - ry * 0.75)])])
            out.append(_st(dart, b, 0.35))
    return out, []


def bracket_ogee(h, d, t):
    """An ogee console: a flat top, a short square nose, then an S-curve (swelling, then
    hollow) running back to the wall, a ball dropping under the nose (side profile, top at
    v = 0)."""
    hb = min(h, max(1.8, 0.5 * d))
    hn = 0.3 * hb
    curve = [(d - (d - 0.2) * s, -hn - (hb - hn) * (3 * s * s - 2 * s ** 3)) for s in np.linspace(0.0, 1.0, 14)]
    body = poly([(0.0, 0.0), (d, 0.0)] + curve + [(0.0, -hb)])
    return cs_union([body, circle((d - 0.45, -hn - 0.15), 0.45, 14)])


CO.FRIEZE_EXTRA.update(lyres=frieze_lyres, torches=frieze_torches, eggdart=frieze_eggdart)
TW.BRACKET_EXTRA.update(ogee=bracket_ogee)
TW.FOUNDATION_EXTRA.update(cobble=foundation_cobble)


# ------------------------------------------------------------------ the Ellsworth's windows and door
def _sash(w, h, plug_cs, bars, rise=0.0):
    """Glass, the sash lining and the given bars (a CrossSection) for a plug, as solids
    (as openings.window_insert builds them)."""
    from . import openings as O
    pl = O.PLUG
    fw = O.sash_frame(w)
    inner = plug_cs.offset(-fw, JoinType.Miter, 4.0)
    stile = min(0.7, max(0.5, 0.08 * w))
    parts = [ext(plug_cs, -pl, -pl + O.GLASS), ext(plug_cs - inner, -pl, 0.0),
             ext(inner - inner.offset(-stile, JoinType.Miter, 4.0), -pl + O.GLASS, -O.SASH_REC)]
    if bars is not None and not bars.is_empty():
        parts.append(ext(bars ^ inner, -pl + O.GLASS, -O.SASH_REC))
    return parts


def window_prairie(w, h, A=1.2):
    """The Ellsworth's first-storey window: an upper sash barred into a big centre light with
    narrow lights down its sides and across its head, one light below; an architrave casing
    with a bead, a pulvinated (cushion) frieze bound with a ribbon over it, a moulded cap, a
    sill on two blocks."""
    from . import openings as O
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    mr = h * 0.5
    m = max(1.1, w * 0.14)
    fw = O.sash_frame(w)
    bars = cs_union([rect(-w, mr - 0.4, w, mr + 0.4),
                     rect(-w / 2 + fw + m - 0.25, mr, -w / 2 + fw + m + 0.25, h),
                     rect(w / 2 - fw - m - 0.25, mr, w / 2 - fw - m + 0.25, h),
                     rect(-w, h - fw - m - 0.25, w, h - fw - m + 0.25) ^ rect(-w, mr, w, h)])
    sash = _sash(w, h, plug_cs, bars)
    parts = [ext(op - op.offset(-0.5, JoinType.Miter, 4.0), 0.0, O.CAS)]
    cas = (op.offset(A, JoinType.Miter, 4.0) - op) ^ rect(-w, 0.0, w, h + A)
    parts.append(ext(cas, 0.0, 0.9))
    parts.append(ext((op.offset(A, JoinType.Miter, 4.0) - op.offset(A - 0.45, JoinType.Miter, 4.0)) ^ rect(-w, 0.0, w, h + A), 0.89, 1.2))
    # the cushion frieze: three stacked bands, fullest in the middle, a ribbon tied round it
    fu, f0, f1 = w / 2 + A, h + A, h + A + 2.2
    parts.append(ext(rect(-fu, f0 - 0.01, fu, f1), 0.0, 0.8))
    parts.append(ext(rect(-fu, f0 + 0.4, fu, f1 - 0.4), 0.79, 1.15))
    parts.append(ext(rect(-fu + 0.2, f0 + 0.8, fu - 0.2, f1 - 0.8), 1.14, 1.4))
    parts.append(ext(rect(-0.45, f0 + 0.1, 0.45, f1 - 0.1), 0.0, 1.6))
    parts.append(chamfer_box(-fu - 0.7, f1 - 0.01, fu + 0.7, f1 + 0.8, 0.0, 1.8, c=0.35, bottom=0.6))
    parts.append(chamfer_box(-fu - 0.3, f1 + 0.79, fu + 0.3, f1 + 1.2, 0.0, 1.2, c=0.3))
    top = f1 + 1.2
    parts.append(chamfer_box(-w / 2 - A - 0.5, -1.0, w / 2 + A + 0.5, 0.01, 0.0, 1.4, c=0.3, bottom=0.5))
    for sg in (-1, 1):
        u = sg * (w / 2 - 0.2)
        parts.append(chamfer_box(u - 0.7, -2.2, u + 0.7, -0.99, 0.0, 1.0, c=0.3, bottom=0.6))
    return O._one_piece(sash, parts, op, plug_cs, O.PLUG, top, -2.2)


def window_festoon(w, h, A=1.1):
    """The Ellsworth's second-storey window: six over one; a flat casing with a quirk; a
    head board carved with a festoon hung from two rosettes, tassels at its ends; a thin cap;
    a sill over a small apron with a raised lozenge."""
    from . import openings as O
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    sash = [O.window_insert(w, h, 0, lites=(1, 3), rows=(1, 2), bare=True)["insert"]]
    parts = [ext(op - op.offset(-0.5, JoinType.Miter, 4.0), 0.0, O.CAS)]
    cas = (op.offset(A, JoinType.Miter, 4.0) - op) ^ rect(-w, 0.0, w, h + A)
    parts.append(ext(cas, 0.0, 0.9) - ext((op.offset(A * 0.55, JoinType.Miter, 4.0) - op.offset(A * 0.55 - 0.4, JoinType.Miter, 4.0))
                                          ^ rect(-w, 0.0, w, h + A), 0.6, 1.0))
    hu, h0, h1 = w / 2 + A, h + A, h + A + 3.0
    parts.append(ext(rect(-hu, h0 - 0.01, hu, h1), 0.0, 0.8))
    ts = np.linspace(0.0, 1.0, 16)
    xa, xb = -hu + 1.3, hu - 1.3
    top_ = [(xa + (xb - xa) * t, h1 - 0.9 - 0.7 * math.sin(math.pi * t)) for t in ts]
    bot_ = [(xa + (xb - xa) * t, h1 - 1.3 - 1.3 * math.sin(math.pi * t)) for t in reversed(ts)]
    parts.append(ext(poly(top_ + bot_), 0.79, 1.25))
    for sg in (-1, 1):
        c = (sg * (hu - 1.3), h1 - 1.05)
        parts.append(ext(circle(c, 0.6, 16), 0.79, 1.45))
        parts.append(ext(poly([(c[0] - 0.3, c[1] - 0.4), (c[0] + 0.3, c[1] - 0.4), (c[0] + 0.2, h0 + 0.4), (c[0], h0 + 0.1),
                               (c[0] - 0.2, h0 + 0.4)]), 0.79, 1.2))
    parts.append(chamfer_box(-hu - 0.5, h1 - 0.01, hu + 0.5, h1 + 0.7, 0.0, 1.4, c=0.35, bottom=0.5))
    top = h1 + 0.7
    parts.append(chamfer_box(-w / 2 - A - 0.4, -0.9, w / 2 + A + 0.4, 0.01, 0.0, 1.3, c=0.3, bottom=0.5))
    parts.append(ext(rect(-w / 2 + 0.4, -2.6, w / 2 - 0.4, -0.89), 0.0, 0.7))
    parts.append(ext(poly([(-1.4, -1.75), (0.0, -2.35), (1.4, -1.75), (0.0, -1.15)]), 0.69, 1.05))
    return O._one_piece(sash, parts, op, plug_cs, O.PLUG, top, -2.6)


def window_keyed_arch(w, h, A=1.2):
    """The Ellsworth's tower window: a round-headed one-over-one; square jamb casings on
    moulded impost blocks carry an archivolt with a raised keystone; a sill on a bed
    moulding."""
    from . import openings as O
    r = w / 2
    spring = h - r
    op = O.opening_cs(w, h, r)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    sash = [O.window_insert(w, h, r, lites=(1, 1), rows=(1, 1), bare=True)["insert"]]
    parts = [ext(op - op.offset(-0.5, JoinType.Miter, 4.0), 0.0, O.CAS)]
    ring = (circle((0.0, spring), r + A, 48) - circle((0.0, spring), r, 48)) ^ rect(-w, spring, w, h + A + 1)
    parts.append(ext(ring, 0.0, 1.0))
    parts.append(ext((circle((0.0, spring), r + A, 48) - circle((0.0, spring), r + A - 0.45, 48)) ^ rect(-w, spring, w, h + A + 1),
                     0.99, 1.3))
    for sg in (-1, 1):
        u0, u1 = sorted((sg * r, sg * (r + A)))
        parts.append(ext(rect(u0, 0.0, u1, spring + 0.01), 0.0, 1.0))
        parts.append(chamfer_box(u0 - 0.35, spring - 0.8, u1 + 0.35, spring + 0.01, 0.0, 1.4, c=0.3, bottom=0.5))
    key = poly([(-0.8, h - 0.5), (0.8, h - 0.5), (1.1, h + A + 0.7), (-1.1, h + A + 0.7)])
    parts.append(ext(key, 0.0, 1.7))
    top = h + A + 0.7
    parts.append(chamfer_box(-r - A - 0.5, -0.9, r + A + 0.5, 0.01, 0.0, 1.4, c=0.3, bottom=0.5))
    parts.append(chamfer_box(-r - A, -1.5, r + A, -0.89, 0.0, 0.9, c=0.3, bottom=0.5))
    return O._one_piece(sash, parts, op, plug_cs, O.PLUG, top, -1.5)


def door_leaded(w=12.0, h=24.0, side=4.0, fan=6.0):
    """The Ellsworth's front door: a door with a leaded oval light over two raised panels,
    leaded sidelights (lozenge panes) over panels, and over all three an elliptical
    fanlight of leaded rays; fluted pilasters with scrolled (Ionic) capitals carry a moulded
    archivolt round the fanlight with a carved keystone. Printed face-up, one piece."""
    from . import openings as O
    W2 = w / 2 + side + 0.6
    ell = [(W2 * math.cos(t), h + fan * math.sin(t)) for t in np.linspace(0.0, math.pi, 41)]
    op = poly([(-W2, 0.0), (W2, 0.0)] + ell)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    face = -1.0
    body = ext(plug_cs, -pl, face)
    glass_cs = []
    leads = []
    # the door: a leaded oval light, two raised panels below it
    oc, orx, ory = (0.0, h * 0.64), w * 0.3, h * 0.2
    lite = oval(oc, orx, ory, 40)
    glass_cs.append(lite)
    leads.append(oval(oc, orx * 0.55, ory * 0.55, 32) - oval(oc, orx * 0.55 - 0.45, ory * 0.55 - 0.45, 32))
    for a in np.linspace(0.0, math.pi, 4, endpoint=False):
        leads.append(stroke([(oc[0] + orx * 1.2 * math.cos(a), oc[1] + ory * 1.2 * math.sin(a)),
                             (oc[0] - orx * 1.2 * math.cos(a), oc[1] - ory * 1.2 * math.sin(a))], 0.45))
    panels = [rect(-w / 2 + 1.3, 1.3, -0.5, h * 0.36), rect(0.5, 1.3, w / 2 - 1.3, h * 0.36)]
    # the leaves' frame: a groove round the door and one between door and sidelights
    grooves = [rect(-w / 2 - 0.3, 0.0, -w / 2 + 0.2, h), rect(w / 2 - 0.2, 0.0, w / 2 + 0.3, h), rect(-W2, h - 0.2, W2, h + 0.3)]
    for sg in (-1, 1):
        s0, s1 = sorted((sg * (w / 2 + 0.6), sg * (W2 - 0.4)))
        sl = rect(s0, 5.0, s1, h - 0.8)
        glass_cs.append(sl)
        panels.append(rect(s0 + 0.4, 1.3, s1 - 0.4, 3.9))
        for k in range(-10, 12):
            for dirn in (-1, 1):
                x0 = s0 + k * 1.8
                leads.append(stroke([(x0, 5.0), (x0 + dirn * 18.0, 5.0 + 18.0 * 1.7)], 0.45, caps=False) ^ sl)
    fan_cs = (poly(ell) ^ rect(-W2, h + 0.6, W2, h + fan + 1)).offset(-0.7, JoinType.Miter, 4.0)
    glass_cs.append(fan_cs)
    for a in np.linspace(0.0, math.pi, 9)[1:-1]:
        leads.append(stroke([(0.0, h + 0.6), (W2 * 1.2 * math.cos(a), h + 0.6 + fan * 1.2 * math.sin(a))], 0.45, caps=False))
    leads.append(oval((0.0, h + 0.6), W2 * 0.35, fan * 0.4, 32) - oval((0.0, h + 0.6), W2 * 0.35 - 0.45, fan * 0.4 - 0.45, 32))
    gl = cs_union(glass_cs)
    body = body - ext(gl, -pl + O.GLASS, 0.5) - ext(cs_union(grooves) - gl, face - 0.25, 0.5)
    sash = [body, ext(gl, -pl, -pl + O.GLASS), ext(cs_union(leads) ^ gl, -pl + O.GLASS - 0.01, face - 0.15),
            ext(cs_union(panels), face - 0.01, face + 0.3), ext(plug_cs - plug_cs.offset(-0.5, JoinType.Miter, 4.0), -pl, 0.0)]
    # the surround
    parts = [ext(op - op.offset(-0.5, JoinType.Miter, 4.0), 0.0, O.CAS)]
    pw = 2.2
    for sg in (-1, 1):
        u0, u1 = sorted((sg * W2, sg * (W2 + pw)))
        um = (u0 + u1) / 2
        pil = ext(rect(u0, 0.0, u1, h + 0.01), 0.0, 1.2)
        for dx in (-0.5, 0.5):
            pil = pil - ext(rect(um + dx - 0.22, 2.6, um + dx + 0.22, h - 2.0), 0.95, 1.5)
        parts.append(pil)
        parts.append(chamfer_box(u0 - 0.35, 0.0, u1 + 0.35, 2.2, 0.0, 1.5, c=0.3, bottom=0.0))
        parts.append(chamfer_box(u0 - 0.4, h - 1.2, u1 + 0.4, h + 0.61, 0.0, 1.5, c=0.3, bottom=0.5))
        for du in (u0 - 0.15, u1 + 0.15):
            parts.append(ext(circle((du, h - 0.25), 0.55, 16), 1.49, 1.9))
    ring_o = poly([((W2 + pw) * math.cos(t), h + (fan + pw) * math.sin(t)) for t in np.linspace(0, math.pi, 41)])
    arch = (ring_o - poly(ell)) ^ rect(-W2 - pw - 1, h + 0.6, W2 + pw + 1, h + fan + pw + 1)
    parts.append(ext(arch, 0.0, 1.1))
    parts.append(ext((ring_o - ring_o.offset(-0.5, JoinType.Miter, 4.0)) ^ rect(-W2 - pw - 1, h + 0.6, W2 + pw + 1, h + fan + pw + 1),
                     1.09, 1.4))
    key = poly([(-1.0, h + fan - 0.4), (1.0, h + fan - 0.4), (1.4, h + fan + pw + 0.8), (-1.4, h + fan + pw + 0.8)])
    parts.append(ext(key, 0.0, 1.8))
    parts.append(ext(oval((0.0, h + fan + pw * 0.5 + 0.2), 0.55, 0.8, 16), 1.79, 2.1))
    parts.append(chamfer_box(-W2 - pw - 0.4, -0.8, W2 + pw + 0.4, 0.01, 0.0, 1.3, c=0.3, bottom=0.0))
    return O._one_piece(sash, parts, op, plug_cs, pl, h + fan + pw + 0.8, -0.8)


# ------------------------------------------------------------------ the Ellsworth's porch
def post_pedestal(h, collar=None, abacus=3.2, slot=(1.2, 1.0)):
    """A Free Classic veranda column: a square pedestal with a sunk panel on each face and a
    moulded cap, standing to the hand rail's height, then a short Tuscan column (a torus
    base, a shaft with entasis, an astragal, an echinus) to a square abacus (the
    Ellsworth). The railing runs into the pedestals' sides."""
    from . import porchwork as PW
    zp = (collar + 0.6) if collar is not None else 9.6
    body = PW._plinth(3.4, 1.2) + box([-1.45, -1.45, 1.19], [1.45, 1.45, zp - 0.6])
    for sx, sy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        if sx:
            cut = box([sx * 1.45 - 0.2, -0.85, 2.2], [sx * 1.45 + 0.2, 0.85, zp - 1.6])
        else:
            cut = box([-0.85, sy * 1.45 - 0.2, 2.2], [0.85, sy * 1.45 + 0.2, zp - 1.6])
        body = body - cut
    body = body + M.hull_points([(x * 1.45, y * 1.45, zp - 0.61) for x in (-1, 1) for y in (-1, 1)] +
                                [(x * 1.7, y * 1.7, zp - 0.25) for x in (-1, 1) for y in (-1, 1)]) + \
        box([-1.7, -1.7, zp - 0.26], [1.7, 1.7, zp])
    z1 = h - 2.8
    prof = [(0.0, zp - 0.01), (1.25, zp - 0.01), (1.25, zp + 0.3), (1.1, zp + 0.55), (1.05, zp + 0.8),
            (1.02, zp + 0.8 + 0.35 * (z1 - zp - 0.8)), (0.92, z1 - 0.2), (0.88, z1), (1.05, z1 + 0.2), (1.05, z1 + 0.5),
            (0.9, z1 + 0.7), (0.9, z1 + 0.9)]
    body = body + PW._revolve(prof, 32)
    return body + PW._top(h, abacus / 2, z1 + 0.9, 0.9, slot, seg=32)


def baluster_pear(h, seg=20):
    """A bottle baluster: square ends, a pear-shaped bulb low on the shaft rising to a slim
    neck and a ring (the Ellsworth)."""
    from . import porchwork as PW
    H = h - 1.6
    t = [(0.0, 0.42), (0.06, 0.5), (0.3, 0.56), (0.45, 0.5), (0.62, 0.32), (0.78, 0.26), (0.84, 0.42), (0.9, 0.42),
         (0.95, 0.3), (1.0, 0.3)]
    prof = [(0.0, 0.79)] + [(r, 0.8 + f * H) for f, r in t]
    return PW._revolve(prof, seg) + box([-0.5, -0.5, 0.0], [0.5, 0.5, 0.81]) + box([-0.5, -0.5, h - 0.81], [0.5, 0.5, h])


def frieze_festoons(u0, u1, v_bot, v_top):
    """A porch frieze board hung with a draped festoon in every bay, tied up at each end on a
    rosette with a tassel falling from it (the Ellsworth)."""
    rail0 = v_top - 1.0
    parts = [rect(u0, rail0, u1, v_top + 0.05)]
    a, b = u0 + 1.0, u1 - 1.0
    sag = min(2.2, v_top - v_bot - 2.2)
    ts = np.linspace(0.0, 1.0, 24)
    top_ = [(a + (b - a) * t, rail0 + 0.05 - (sag * 0.4) * math.sin(math.pi * t)) for t in ts]
    bot_ = [(a + (b - a) * t, rail0 - 0.5 - sag * math.sin(math.pi * t)) for t in reversed(ts)]
    parts.append(poly(top_ + bot_))
    for c in (a, b):
        parts.append(circle((c, rail0 - 0.35), 0.8, 20))
        parts.append(poly([(c - 0.25, rail0 - 1.0), (c + 0.25, rail0 - 1.0), (c + 0.5, rail0 - 2.4), (c, rail0 - 2.9),
                           (c - 0.5, rail0 - 2.4)]))
    return cs_union(parts)


def skirt_louvres(reg, d=1.2):
    """A board skirt pierced by louvred vents: in each opening a stack of level slats set back
    in the board (the Ellsworth)."""
    u0, v0, u1, v1 = reg.bounds()
    L = u1 - u0
    n = max(1, int(round(L / 7.0)))
    va = math.ceil((v0 + 0.8) / 0.2) * 0.2
    vb = math.floor((v1 - 0.8) / 0.2) * 0.2
    holes, slats = [], []
    for i in range(n):
        a, b = u0 + L * i / n + 0.8, u0 + L * (i + 1) / n - 0.8
        if b - a < 2.0 or vb - va < 1.6:
            continue
        holes.append(rect(a, va, b, vb))
        v = va + 0.4
        while v + 0.4 <= vb - 0.2:
            slats.append(rect(a - 0.1, v, b + 0.1, v + 0.4))
            v += 0.8
    board = reg - cs_union(holes) if holes else reg
    out = M.extrude(board, d)
    if slats:
        out = out + M.extrude(cs_union(slats) ^ cs_union([h_.offset(0.05, JoinType.Miter, 4.0) for h_ in holes]), d * 0.5).translate(
            [0, 0, d * 0.25])
    return out


def edge_guttae(L, z0, zc):
    """A porch-roof fascia with a regula (a flat band) under the crown and groups of three
    little cone drops (guttae) hanging from it (the Ellsworth)."""
    parts = [rect(0.3, zc - 0.5, L - 0.3, zc)]
    n = max(1, int((L - 1.6) / 3.8))
    for k in range(n):
        uc = 0.8 + (L - 1.6) * (k + 0.5) / n
        for du in (-1.0, 0.0, 1.0):
            parts.append(poly([(uc + du - 0.3, zc - 0.45), (uc + du + 0.3, zc - 0.45), (uc + du + 0.2, zc - 1.3),
                               (uc + du - 0.2, zc - 1.3)]))
    return cs_union(parts), 0.55


# ------------------------------------------------------------------ the Ellsworth's tower, chimney, dormers
def roof_ogee(apothem, h, n=6, courses=12, lip=0.35, roll=0.45, a_top=1.4):
    """An ogee roof on an n-sided tower (edge 0 facing -y, as core.ngon): its faces swell
    out of the eave like a dome, then draw in to a slender neck, in courses of copper flat-seam
    sheets (each course's foot standing a lip proud of the course below) with a round roll
    up every hip. Centred on the origin, base at z = 0; the neck ends at z = h, apothem a_top."""
    from .core import ngon
    ci = 1.0 / math.cos(math.pi / n)

    def a_of(t):
        return a_top + (apothem - a_top) * (1.0 - (3 * t * t - 2 * t ** 3))

    zs = [zq(h * k / courses) for k in range(courses + 1)]
    zs[-1] = h
    parts = []
    for k in range(courses):
        a0, a1 = a_of(zs[k] / h), a_of(zs[k + 1] / h)
        parts.append(M.hull_points([(x, y, zs[k]) for x, y in ngon((0.0, 0.0), a0 + lip, n)] +
                                   [(x, y, zs[k + 1]) for x, y in ngon((0.0, 0.0), a1, n)]))
    ball = M.sphere(roll, 12)
    ts = np.linspace(0.0, 0.97, 3 * courses)
    a_v = -math.pi / 2 - math.pi / n
    for j in range(n):
        ang = a_v + 2 * math.pi * j / n
        pts = [((a_of(t) + lip * 0.6) * ci * math.cos(ang), (a_of(t) + lip * 0.6) * ci * math.sin(ang), h * t) for t in ts]
        for p, q in zip(pts[:-1], pts[1:]):
            parts.append((ball.translate(p) + ball.translate(q)).hull())
    return union(parts).trim_by_plane([0.0, 0.0, 1.0], 0.0)


def finial_flambeau(r=1.4, h=12.0):
    """A flame finial (flambeau): a turned foot and cup, and out of it a flame of four lobes
    twisted half a turn, swelling and drawing to a point (the Ellsworth). Base at z = 0."""
    from . import porchwork as PW
    zc = h * 0.34
    foot = PW._revolve([(0.0, 0.0), (r, 0.0), (r, 0.4), (r * 0.55, 0.9), (r * 0.5, zc * 0.55), (r * 0.9, zc * 0.8),
                        (r * 0.95, zc), (r * 0.6, zc + 0.2)], 28)
    L = h - zc - 0.2
    lobes = cs_union([circle((0.3 * r * math.cos(a), 0.3 * r * math.sin(a)), 0.42 * r, 14)
                      for a in np.linspace(0, 2 * math.pi, 4, endpoint=False)])
    fl = M.extrude(lobes, L, int(L / 0.2), 180.0).translate([0.0, 0.0, zc + 0.19])

    def taper(P):
        P = np.array(P)
        t = np.clip((P[:, 2] - zc - 0.2) / L, 0.0, 1.0)
        s = np.where(t < 0.3, 0.75 + 0.8 * t, 0.99 * (1.0 - t) / 0.7 + 0.02)
        P[:, 0] *= s
        P[:, 1] *= s
        return P

    return foot + fl.warp_batch(taper)


def chimney_herringbone(w=12.0, d=9.0, h=30.0):
    """The Ellsworth's chimney: a common-bond brick stack with a sunk panel on each face laid
    in herringbone inside a raised border, a two-course corbelled cap under a chamfered stone
    slab, and two round crock pots. Stands on z = 0 (the bottom of its roof pocket)."""
    zc = h - 5.0
    body = box([-w / 2, -d / 2, 0.0], [w / 2, d / 2, zc]) + TW._skin(w, d, 0.0, zc - 0.2, TW._brick("common"))
    for i, f in enumerate(TW._faces(w, d)):
        if f.L < 7.0:
            continue
        reg = rect(1.6, zc - 12.0, f.L - 1.6, zc - 2.0)
        inner = reg.offset(-0.6, JoinType.Miter, 4.0)
        body = body - f.place(ext(reg, -0.5, 1.0))
        bricks = []
        for k in range(-30, 30):
            for j in range(-6, 8):
                cx, cy = 1.6 + j * 1.9 + (k % 2) * 0.95, zc - 12.0 + k * 0.95
                a = math.pi / 4 if (j + k) % 2 else -math.pi / 4
                ca, sa = math.cos(a), math.sin(a)
                bricks.append(poly([(cx + ca * du - sa * dv, cy + sa * du + ca * dv) for du, dv in
                                    ((-0.75, -0.25), (0.75, -0.25), (0.75, 0.25), (-0.75, 0.25))]))
        body = body + f.place(ext(cs_union(bricks) ^ inner, -0.51, -0.25)) + f.place(ext(reg - inner, -0.51, 0.1))
    body = body + TW._corbel_out(w, d, zc + 0.4, 0.4) + box([-w / 2 - 0.4, -d / 2 - 0.4, zc + 0.39], [w / 2 + 0.4, d / 2 + 0.4, zc + 1.2])
    body = body + TW._corbel_out(w + 0.8, d + 0.8, zc + 1.6, 0.4) + box([-w / 2 - 0.8, -d / 2 - 0.8, zc + 1.59], [w / 2 + 0.8, d / 2 + 0.8, zc + 2.2])
    body = body + chamfer_box(-w / 2 - 1.2, -d / 2 - 1.2, w / 2 + 1.2, d / 2 + 1.2, zc + 2.19, 1.0, c=0.4, bottom=0.4)
    top = zc + 3.19
    for x in (-w * 0.22, w * 0.22):
        pot = M.cylinder(h - top, 1.3, 1.1, 24).translate([x, 0.0, top - 0.01]) + \
            M.cylinder(0.6, 1.45, 1.45, 24).translate([x, 0.0, h - 0.6]) - M.cylinder(3.0, 0.7, 0.7, 16).translate([x, 0.0, h - 2.0])
        body = body + pot
    return body


def dormer_broken(w=15.0, dep=18.0, hwall=12.0, pitch=1.0):
    """A dormer with a broken pediment: a flat front with a round-headed light (a keyed
    architrave round it, a cross of bars), a full cornice across at the eave, raking cornices
    that stop short of the apex, and an urn standing in the gap; shingled cheeks. Local as
    colonial.dormer_cape; returns (body, core, face)."""
    rise = w / 2 * pitch
    face = poly([(-w / 2, 0.0), (w / 2, 0.0), (w / 2, hwall), (0.0, hwall + rise), (-w / 2, hwall)])
    body = ext(face, -dep, 0.0) - ext(face.offset(-1.2, JoinType.Miter, 4.0) ^ rect(-50, 1.2, 50, 99), -dep - 1, -1.2)
    lw, lh = w * 0.44, hwall - 3.8
    r = lw / 2
    light = cs_union([rect(-r, 1.8, r, 1.8 + lh - r), circle((0.0, 1.8 + lh - r), r, 32)])
    body = body - ext(light, -1.3, 1.0)
    sp = 1.8 + lh - r
    bars = cs_union([rect(-r, 1.8 + (lh - r) * 0.5 - 0.3, r, 1.8 + (lh - r) * 0.5 + 0.3), rect(-0.25, 1.8, 0.25, 1.8 + lh),
                     rect(-r, sp - 0.22, r, sp + 0.22)]) ^ light
    body = body + ext(bars, -1.2, -0.5)
    arch = (light.offset(0.9, JoinType.Round) - light) ^ rect(-50, 1.8, 50, 99)
    body = body + ext(arch, -0.01, 0.6)
    body = body + ext(poly([(-0.6, 1.8 + lh - 0.2), (0.6, 1.8 + lh - 0.2), (0.85, 1.8 + lh + 1.3), (-0.85, 1.8 + lh + 1.3)]), -0.01, 1.0)
    body = body + chamfer_box(-r - 1.4, 0.9, r + 1.4, 1.8, -0.01, 1.0, c=0.3, bottom=0.8)
    # the cornice across, the raking cornices broken short of the apex, the urn in the gap
    body = body + chamfer_box(-w / 2 - 0.5, hwall - 0.8, w / 2 + 0.5, hwall + 0.4, -0.01, 1.3, c=0.35, bottom=0.8)
    gap = 2.4
    for sg in (-1, 1):
        a = (sg * (w / 2 + 0.5), hwall + 0.4)
        b = (sg * gap / 2, hwall + rise - gap / 2 * pitch)
        rake = poly([a, b, (b[0], b[1] - 1.2), (a[0], a[1] - 1.2)]) if sg < 0 else poly([b, a, (a[0], a[1] - 1.2), (b[0], b[1] - 1.2)])
        body = body + ext(rake, -0.01, 1.2)
    zu = hwall + rise - gap / 2 * pitch - 1.2
    urn = cs_union([rect(-0.8, zu - 0.01, 0.8, zu + 0.5), poly([(-0.5, zu + 0.5), (0.5, zu + 0.5), (1.0, zu + 1.6), (0.7, zu + 2.4),
                                                               (-0.7, zu + 2.4), (-1.0, zu + 1.6)]),
                    rect(-0.25, zu + 2.39, 0.25, zu + 2.9), circle((0.0, zu + 3.1), 0.35, 12)])
    body = body + ext(urn ^ face.offset(-0.01), -0.01, 1.0)
    side = poly([(0.0, 0.3), (0.0, hwall - 0.2), (-dep, hwall - 0.2), (-dep, 0.3)])
    tex = shingles_undulating(side, datum=0.3, pitch=1.4, wtab=1.6, d=0.35, amp=0.3, wave=9.0)
    for sg in (-1, 1):
        Ac = np.array([[0, 0, sg * 1.0, sg * (w / 2 - 0.02)], [0, 1.0, 0, 0], [1.0, 0, 0, 0]])
        body = body + tex.transform(Ac)
    core = ext(face.offset(-1.2, JoinType.Miter, 4.0) ^ rect(-50, 1.2, 50, hwall), -dep + 1.2, -1.2)
    return body, core, face


def entry_segmental(w, depth, rise, t=1.0):
    """The Ellsworth's porch entry: a segmental pediment standing on the porch roof over the
    steps, a raised rim round its face and a cartouche in the tympanum (an oval shield
    between scrolled ears, a sunk field with a boss); its roof a shallow barrel behind. Local
    as features.entry_pediment (u across, v up from the porch roof top, w out from the house,
    the face at w = depth); prints upright on its base."""
    R = (w * w / 4 + rise * rise) / (2 * rise)
    cy = rise - R
    ang = math.asin((w / 2) / R)
    arc = [(R * math.sin(a), cy + R * math.cos(a)) for a in np.linspace(-ang, ang, 33)]
    face = poly([(-w / 2, 0.0)] + arc + [(w / 2, 0.0)])
    parts = [M.extrude(face, depth)]
    parts.append(ext(face - face.offset(-0.8, JoinType.Miter, 4.0), depth - 0.01, depth + t))
    c = (0.0, rise * 0.42)
    rx, ry = min(w * 0.16, 3.0), min(rise * 0.3, 1.8)
    shield = oval(c, rx, ry, 32)
    ears = cs_union([circle((c[0] + sg * (rx + 0.3), c[1] + ry * 0.35), 0.6, 16) for sg in (-1, 1)] +
                    [circle((c[0] + sg * (rx + 0.1), c[1] - ry * 0.45), 0.45, 12) for sg in (-1, 1)])
    parts.append(ext((shield + ears) - oval(c, rx - 0.6, ry - 0.5, 28), depth - 0.01, depth + t * 0.8))
    parts.append(ext(oval(c, rx - 0.6, ry - 0.5, 28), depth - 0.01, depth + t * 0.3))
    parts.append(ext(circle(c, 0.5, 16), depth + t * 0.3 - 0.01, depth + t * 0.9))
    parts.append(ext(rect(-w / 2 + 0.8, 0.0, w / 2 - 0.8, 0.8), depth - 0.01, depth + t * 0.6))
    return union(parts).transform(np.array([[1.0, 0, 0, 0], [0, 0, 1.0, 0], [0, 1.0, 0, 0]]))


from . import porchwork as _PW                                           # noqa: E402
from . import features as _FT                                            # noqa: E402
_PW.POSTS.update(pedestal=post_pedestal)
_PW.BALUSTERS.update(pear=(baluster_pear, 1.9))
_PW.FRIEZES.update(festoons=frieze_festoons)
_PW.SKIRTS.update(louvres=skirt_louvres)
_FT.EDGE_EXTRA.update(guttae=edge_guttae)

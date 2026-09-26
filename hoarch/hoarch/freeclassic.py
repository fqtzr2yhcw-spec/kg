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


def frieze_waterleaf(L, h, b, pitch, margin, pair, half):
    """Waterleaf and tongue: broad upright leaves, each with a sunk midrib, a round-topped
    tongue standing between each pair, a fillet along the foot."""
    v0, v1 = 0.6, h - 0.6
    step = 2.8
    n = max(1, int((L - margin * 0.6) / step))
    ua = (L - n * step) / 2 + step / 2
    out = [_st(rect(margin * 0.3, v0, L - margin * 0.3, v0 + 0.4), b, 0.25)]
    for k in range(n):
        u = ua + k * step
        ts = np.linspace(0.0, 1.0, 12)
        right = [(u + 1.0 * math.sin(math.pi * (0.15 + 0.85 * t)) * (1 - 0.35 * t), v0 + 0.35 + (v1 - v0 - 0.4) * t) for t in ts]
        left = [(2 * u - x, y) for x, y in reversed(right)]
        leaf = poly(right + left) - rect(u - 0.2, v0 + 0.8, u + 0.2, v1 - 0.9)
        out.append(_st(leaf, b, 0.5))
        if k < n - 1:
            ut = u + step / 2
            out.append(_st(cs_union([rect(ut - 0.3, v0 + 0.35, ut + 0.3, v1 - 1.3), circle((ut, v1 - 1.3), 0.3, 12)]), b, 0.3))
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


CO.FRIEZE_EXTRA.update(lyres=frieze_lyres, torches=frieze_torches, waterleaf=frieze_waterleaf)
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
    # the cornice across, the raking cornices broken well short of the apex (the urn, its own
    # part, stands in the gap on a plinth)
    body = body + chamfer_box(-w / 2 - 0.5, hwall - 0.8, w / 2 + 0.5, hwall + 0.4, -0.01, 1.4, c=0.35, bottom=0.8)
    gap = 4.4
    va = hwall + rise
    for sg in (-1, 1):
        a = (sg * (w / 2 + 0.5), hwall + 0.4)
        b = (sg * gap / 2, va - gap / 2 * pitch)
        for dh, d0, d1 in ((1.5, -0.01, 1.2), (0.6, 1.19, 1.6)):
            rk = poly([a, b, (b[0], b[1] - dh), (a[0], a[1] - dh)])
            if sg > 0:
                rk = poly([b, a, (a[0], a[1] - dh), (b[0], b[1] - dh)])
            body = body + ext(rk ^ face.offset(1.0, JoinType.Miter, 4.0), d0, d1)
    side = poly([(0.0, 0.3), (0.0, hwall - 0.2), (-dep, hwall - 0.2), (-dep, 0.3)])
    tex = shingles_undulating(side, datum=0.3, pitch=1.4, wtab=1.6, d=0.35, amp=0.3, wave=9.0)
    for sg in (-1, 1):
        Ac = np.array([[0, 0, sg * 1.0, sg * (w / 2 - 0.02)], [0, 1.0, 0, 0], [1.0, 0, 0, 0]])
        body = body + tex.transform(Ac)
    core = ext(face.offset(-1.2, JoinType.Miter, 4.0) ^ rect(-50, 1.2, 50, hwall), -dep + 1.2, -1.2)
    # the urn: a square plinth set in the gap against the tympanum, a turned urn on it
    from . import porchwork as PW
    vp = va - gap / 2 * pitch - 1.5
    plinth = box([-1.3, 0.0, 0.0], [1.3, 1.6, 1.2])
    urn = PW._revolve([(0.0, 1.19), (0.9, 1.19), (0.9, 1.5), (0.45, 1.9), (0.5, 2.3), (1.05, 3.1), (1.05, 3.6),
                       (0.7, 4.2), (0.35, 4.5), (0.5, 4.8), (0.5, 5.1), (0.25, 5.4), (0.0, 5.6)], 24).translate([0.0, 1.1, 0.0])
    urn = (plinth + urn).transform(np.array([[1.0, 0, 0, 0], [0, 0, 1.0, vp], [0, 1.0, 0, 0]]))
    return body, core, face, urn


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


# ================================================================== the Fairhaven (house 40)
def siding_channel(region, datum=0.0, p=2.2):
    """Channel rustic siding: flat-faced boards, each joint a square channel (a rabbet) rather
    than a lap's slanting shadow."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    v = datum
    while v > v0 - 2.0:
        v -= p
    pts = [(v, 0.0)]
    while v < v1 + 2.0:
        pts += [(v, 0.1), (v + 0.4, 0.1), (v + 0.4, 0.38), (v + p, 0.38)]
        v += p
    pts.append((v, 0.0))
    strip = M.extrude(poly(pts), (u1 - u0) + 2).transform(frame([u0 - 1, 0, 0], [0, 1, 0], [0, 0, 1], [1, 0, 0]))
    return strip ^ M.extrude(region, 0.7).translate([0, 0, -0.1])


def siding_alternating(region, datum=0.0, p0=1.2, p1=2.4):
    """Lap siding in courses of two exposures in turn, a narrow course over every wide one."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    v, k = datum, 0
    while v > v0 - 4.0:
        v -= p0 + p1
    pts = [(v, 0.0)]
    while v < v1 + 4.0:
        p = p1 if k % 2 == 0 else p0
        pts += [(v, 0.32), (v + 0.2, 0.42), (v + p, 0.06)]
        v += p
        k += 1
    pts.append((v, 0.0))
    strip = M.extrude(poly(pts), (u1 - u0) + 2).transform(frame([u0 - 1, 0, 0], [0, 1, 0], [0, 0, 1], [1, 0, 0]))
    return strip ^ M.extrude(region, 0.7).translate([0, 0, -0.1])


def foundation_snecked(reg, seed=0):
    """Snecked rubble: squared stones of two or three heights laid to broken courses, the gaps
    filled with little square snecks; a chamfered dressed cap on top."""
    b = reg.bounds()
    rng = np.random.default_rng(seed + 23)
    top = zq(b[3] - 1.2)
    out = []
    v = zq(b[1])
    while v < top - 0.8:
        u = b[0] - rng.uniform(0.0, 2.0)
        while u < b[2]:
            L = rng.uniform(2.2, 4.4)
            h = min(top - v, (1.2, 1.6, 2.4)[int(rng.integers(0, 3))])
            s = rect(u + 0.15, v + 0.15, u + L - 0.15, v + h - 0.15) ^ reg
            if not s.is_empty() and s.area() > 0.4:
                out.append(chamfer_box(*s.bounds()[:2], *s.bounds()[2:], 0.0, rng.uniform(0.38, 0.5), c=0.18, bottom=0.2))
            if h < 2.3 and v + h + 0.8 <= top:
                sn = rect(u + L * 0.3, v + h + 0.1, u + L * 0.3 + 0.8, v + h + 0.9) ^ reg
                if not sn.is_empty():
                    out.append(chamfer_box(*sn.bounds()[:2], *sn.bounds()[2:], 0.0, 0.3, c=0.1, bottom=0.1))
            u += L
        v = zq(v + 1.6)
    out.append(chamfer_box(b[0], top + 0.2, b[2], b[3], 0.0, 0.6, c=0.3, bottom=0.6))
    return union(out) ^ M.extrude(reg, 2.0).translate([0, 0, -0.5])


def frieze_wheat(L, h, b, pitch, margin, pair, half):
    """Wheat sheaves: in every bay a sheaf (ears fanning out of a band tied round the stalks),
    a round boss at every station, fillets along the band's foot and head."""
    v0, v1 = 0.7, h - 0.7
    out = [_st(rect(margin * 0.4, v0, L - margin * 0.4, v0 + 0.4), b, 0.25),
           _st(rect(margin * 0.4, v1 - 0.4, L - margin * 0.4, v1), b, 0.25)]
    vb, vt = v0 + 0.6, v1 - 0.6
    vm = vb + (vt - vb) * 0.45
    for uc, wd in CO._between(L, pitch, margin, pair, 0.6):
        if wd < 3.0:
            continue
        stalks, ears = [], []
        for a in (-0.5, -0.25, 0.0, 0.25, 0.5):
            tip = (uc + math.sin(a) * (vt - vm) * 1.1, vm + math.cos(a) * (vt - vm))
            foot = (uc + a * 0.9, vb)
            stalks.append(stroke([foot, (uc + a * 0.25, vm), tip], 0.4))
            ears.append(FC_lens(tip, 1.3, 0.62, math.pi / 2 - a))
        out.append(_st(cs_union(stalks), b, 0.3))
        out.append(_st(cs_union(ears), b, 0.45))
        out.append(_st(rect(uc - 0.9, vm - 0.35, uc + 0.9, vm + 0.35), b, 0.55))
    for u in CO._us(L, pitch, margin, 0.0):
        out.append(_st(circle((u, (v0 + v1) / 2), 0.7, 18), b, 0.45))
    return out, []


def FC_lens(c, length, width, ang):
    from .colonial import _lens
    return _lens(c, length, width, ang)


def frieze_ivy(L, h, b, pitch, margin, pair, half):
    """Ivy: a trailing stem waving along the band with a heart-shaped leaf on a short stalk
    at every crest and trough."""
    v0, v1 = 0.7, h - 0.7
    vm = (v0 + v1) / 2
    A = (v1 - v0) * 0.22
    lam = 6.0
    u0_, u1_ = margin * 0.4, L - margin * 0.4
    if u1_ - u0_ < 3.0:
        return [], []
    us = np.linspace(u0_, u1_, max(8, int((u1_ - u0_) * 3)))
    out = [_st(stroke([(u, vm + A * math.sin(2 * math.pi * u / lam)) for u in us], 0.4), b, 0.35)]
    leaves = []
    k = math.ceil((u0_ - lam / 4) / (lam / 2))
    while (k * lam / 2 + lam / 4) < u1_ - 0.8:
        uc = k * lam / 2 + lam / 4
        if uc > u0_ + 0.8:
            sg = 1 if k % 2 == 0 else -1
            base = (uc, vm + sg * A)
            lc = (uc + 0.5, vm + sg * (A + 0.9))
            heart = cs_union([circle((lc[0] - 0.35, lc[1] + sg * 0.25), 0.45, 14), circle((lc[0] + 0.35, lc[1] + sg * 0.25), 0.45, 14),
                              poly([(lc[0] - 0.75, lc[1] + sg * 0.2), (lc[0] + 0.75, lc[1] + sg * 0.2), (lc[0], lc[1] - sg * 0.75)])])
            leaves.append(heart)
            leaves.append(stroke([base, lc], 0.35))
        k += 1
    if leaves:
        out.append(_st(cs_union(leaves) ^ rect(0.0, v0, L, v1), b, 0.45))
    return out, []


def bracket_palmette(h, d, t):
    """A palmette console: a block whose underside is hollowed in a quarter round, its nose
    square and notched, a leaf-shaped drop under the notch (side profile, top at v = 0)."""
    hb = min(h, max(1.8, 0.5 * d))
    r = min(d - 0.6, hb - 0.4)
    arc = [(d - 0.6 - r + r * math.cos(a), -hb + r - r * math.sin(a)) for a in np.linspace(0.0, math.pi / 2, 10)]
    body = poly([(0.0, 0.0), (d, 0.0), (d, -hb * 0.45), (d - 0.3, -hb * 0.55), (d - 0.3, -hb + 0.2), (d - 0.6, -hb)] + arc[::-1][:-1] +
                [(0.0, -hb + r - r)])
    return cs_union([body, poly([(d - 0.75, -hb), (d - 0.15, -hb), (d - 0.45, -hb - 0.8)])])


def window_ogee_hood(w, h, A=1.1):
    """The Fairhaven's first-storey window: two over two under an ogee-arched hood moulding
    (a double curve rising to a point with a little finial), a flat casing with corner beads,
    a sill on a moulded bed."""
    from . import openings as O
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    sash = [O.window_insert(w, h, 0, lites=(2, 2), rows=(1, 1), bare=True)["insert"]]
    parts = [ext(op - op.offset(-0.5, JoinType.Miter, 4.0), 0.0, O.CAS)]
    cas = (op.offset(A, JoinType.Miter, 4.0) - op) ^ rect(-w, 0.0, w, h + A)
    parts.append(ext(cas, 0.0, 0.9))
    for sg in (-1, 1):
        parts.append(ext(rect(sg * (w / 2 + A) - 0.4 if sg > 0 else -w / 2 - A, 0.0,
                              sg * (w / 2 + A) if sg > 0 else -w / 2 - A + 0.4, h + A), 0.89, 1.2))
    hu = w / 2 + A + 0.4
    rise = min(5.0, w * 0.45)
    ts = np.linspace(0.0, 1.0, 20)

    def og(t):                                   # an ogee from the corner (t=0) up to the point (t=1)
        return 3 * t * t - 2 * t ** 3

    outer = [(-hu + hu * t, h + A + rise * og(t)) for t in ts] + [(hu * t, h + A + rise * og(1 - t)) for t in ts[1:]]
    band = poly([(-hu, h + A - 0.01)] + outer + [(hu, h + A - 0.01)])
    inner = band.offset(-0.9, JoinType.Miter, 4.0) ^ rect(-w, h + A + 0.8, w, h + A + 20)
    parts.append(ext(band, 0.0, 0.8))
    parts.append(ext(band - inner, 0.79, 1.4))
    parts.append(ext(cs_union([rect(-0.3, h + A + rise - 0.2, 0.3, h + A + rise + 0.9), circle((0.0, h + A + rise + 1.2), 0.45, 14)]),
                     0.0, 1.4))
    for sg in (-1, 1):
        parts.append(chamfer_box(sg * hu - 0.6, h + A - 0.8, sg * hu + 0.6, h + A + 0.01, 0.0, 1.5, c=0.3, bottom=0.4))
    top = h + A + rise + 1.7
    parts.append(chamfer_box(-w / 2 - A - 0.5, -1.0, w / 2 + A + 0.5, 0.01, 0.0, 1.4, c=0.3, bottom=0.5))
    parts.append(chamfer_box(-w / 2 - A, -1.6, w / 2 + A, -0.99, 0.0, 0.9, c=0.3, bottom=0.5))
    return O._one_piece(sash, parts, op, plug_cs, O.PLUG, top, -1.6)


def window_consoled(w, h, A=1.1):
    """The Fairhaven's second-storey window: one over one with a bar across the upper sash; a
    casing with a sunk bead; a flat cornice cap carried on two small scrolled consoles; a
    raised-panel apron under the sill."""
    from . import openings as O
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    sash = [O.window_insert(w, h, 0, lites=(1, 1), rows=(1, 2), bare=True)["insert"]]
    parts = [ext(op - op.offset(-0.5, JoinType.Miter, 4.0), 0.0, O.CAS)]
    cas = (op.offset(A, JoinType.Miter, 4.0) - op) ^ rect(-w, 0.0, w, h + A)
    parts.append(ext(cas, 0.0, 0.9) - ext((op.offset(A * 0.5, JoinType.Miter, 4.0) - op.offset(A * 0.5 - 0.4, JoinType.Miter, 4.0))
                                          ^ rect(-w, 0.0, w, h + A), 0.6, 1.0))
    hu = w / 2 + A
    parts.append(ext(rect(-hu, h + A - 0.01, hu, h + A + 1.6), 0.0, 0.8))
    for sg in (-1, 1):
        u = sg * (hu - 0.6)
        con = cs_union([rect(u - 0.55, h + A - 0.8, u + 0.55, h + A + 1.6), circle((u, h + A - 0.8), 0.55, 14)])
        parts.append(ext(con, 0.0, 1.4))
    parts.append(chamfer_box(-hu - 0.7, h + A + 1.59, hu + 0.7, h + A + 2.4, 0.0, 1.8, c=0.4, bottom=0.8))
    top = h + A + 2.4
    parts.append(chamfer_box(-w / 2 - A - 0.4, -0.9, w / 2 + A + 0.4, 0.01, 0.0, 1.3, c=0.3, bottom=0.5))
    ap = rect(-w / 2 + 0.2, -3.0, w / 2 - 0.2, -0.89)
    parts.append(ext(ap, 0.0, 0.7))
    parts.append(ext(ap.offset(-0.6, JoinType.Miter, 4.0), 0.69, 1.0))
    return O._one_piece(sash, parts, op, plug_cs, O.PLUG, top, -3.0)


def window_palladian(wc=9.0, ws=4.6, h=15.0, A=1.1):
    """A Palladian window for the Fairhaven's front gable: a round-headed centre light between
    two narrower square-headed side lights, divided by fluted mullion pilasters under a
    running entablature (at the side lights' heads) from which the centre's archivolt
    springs, a keystone at its crown and a sill across all three."""
    from . import openings as O
    r = wc / 2
    spring = h - r
    mw = 1.6                                           # the mullions
    xs = wc / 2 + mw                                   # the side lights' inner edges
    c_op = cs_union([rect(-r, 0.0, r, spring), circle((0.0, spring), r, 40) ^ rect(-r, spring, r, h + 1)])
    sides = [rect(xs, 0.0, xs + ws, spring), rect(-xs - ws, 0.0, -xs, spring)]
    op = cs_union([c_op] + sides + [rect(-xs - 0.01, 0.0, xs + 0.01, spring)])
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    # the plug: the glazed lights, solid behind the mullions
    glass = [ext(plug_cs, -pl, -pl + O.GLASS)]
    bars = cs_union([rect(-r, spring * 0.5 - 0.3, r, spring * 0.5 + 0.3), rect(-0.25, spring, 0.25, h),
                     stroke([(0.0, spring), (r * math.cos(math.radians(45)), spring + r * math.sin(math.radians(45)))], 0.45),
                     stroke([(0.0, spring), (-r * math.cos(math.radians(45)), spring + r * math.sin(math.radians(45)))], 0.45)]
                    + [rect(sg * (xs + ws / 2) - 0.25, 0.0, sg * (xs + ws / 2) + 0.25, spring) for sg in (-1, 1)]
                    + [rect(-xs - ws, spring * 0.5 - 0.25, xs + ws, spring * 0.5 + 0.25)])
    ring = plug_cs - plug_cs.offset(-0.6, JoinType.Miter, 4.0)
    sash = glass + [ext(ring, -pl, 0.0), ext((bars ^ plug_cs), -pl + O.GLASS, -O.SASH_REC),
                    ext(rect(-xs + 0.15, O.CLR, -r - 0.15, spring - O.CLR), -pl, 0.0),
                    ext(rect(r + 0.15, O.CLR, xs - 0.15, spring - O.CLR), -pl, 0.0)]
    parts = [ext(op - op.offset(-0.5, JoinType.Miter, 4.0), 0.0, O.CAS)]
    # mullion pilasters and outer casings to the entablature, fluted
    for u0, u1 in ((-xs - ws - A, -xs - ws), (xs + ws, xs + ws + A + 0.0), (-xs, -r), (r, xs)):
        pil = ext(rect(u0, 0.0, u1, spring + 0.01), 0.0, 1.0)
        um = (u0 + u1) / 2
        if u1 - u0 > 1.3:
            pil = pil - ext(rect(um - 0.2, 1.2, um + 0.2, spring - 1.0), 0.75, 1.2)
        parts.append(pil)
    parts.append(chamfer_box(-xs - ws - A - 0.4, spring - 0.01, -r + 0.01, spring + 1.2, 0.0, 1.4, c=0.3, bottom=0.5))
    parts.append(chamfer_box(r - 0.01, spring - 0.01, xs + ws + A + 0.4, spring + 1.2, 0.0, 1.4, c=0.3, bottom=0.5))
    arch = (circle((0.0, spring), r + A, 48) - circle((0.0, spring), r, 48)) ^ rect(-r - A - 1, spring + 1.19, r + A + 1, h + A + 1)
    parts.append(ext(arch, 0.0, 1.1))
    parts.append(ext(poly([(-0.7, h - 0.4), (0.7, h - 0.4), (1.0, h + A + 0.6), (-1.0, h + A + 0.6)]), 0.0, 1.7))
    parts.append(chamfer_box(-xs - ws - A - 0.6, -1.0, xs + ws + A + 0.6, 0.01, 0.0, 1.4, c=0.3, bottom=0.5))
    return O._one_piece(sash, parts, op, plug_cs, pl, h + A + 0.6, -1.0)


def window_lunette(w=12.0, A=1.0):
    """A half-round attic light (a lunette) for the Fairhaven's end gables: three bars
    radiating from the middle of its sill, a moulded arch band with a keystone."""
    from . import openings as O
    r = w / 2
    op = circle((0.0, 0.0), r, 40) ^ rect(-r - 1, 0.0, r + 1, r + 1)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    bars = cs_union([stroke([(0.0, 0.0), (r * 1.2 * math.cos(a), r * 1.2 * math.sin(a))], 0.45, caps=False)
                     for a in (math.radians(45), math.radians(90), math.radians(135))])
    sash = [ext(plug_cs, -pl, -pl + O.GLASS), ext(plug_cs - plug_cs.offset(-0.6, JoinType.Miter, 4.0), -pl, 0.0),
            ext(bars ^ plug_cs, -pl + O.GLASS, -O.SASH_REC)]
    parts = [ext(op - op.offset(-0.5, JoinType.Miter, 4.0), 0.0, O.CAS)]
    band = (circle((0.0, 0.0), r + A, 48) - circle((0.0, 0.0), r, 48)) ^ rect(-r - A - 1, 0.0, r + A + 1, r + A + 1)
    parts.append(ext(band, 0.0, 1.0))
    parts.append(ext(poly([(-0.6, r - 0.4), (0.6, r - 0.4), (0.9, r + A + 0.5), (-0.9, r + A + 0.5)]), 0.0, 1.5))
    parts.append(chamfer_box(-r - A - 0.5, -1.0, r + A + 0.5, 0.01, 0.0, 1.3, c=0.3, bottom=0.5))
    return O._one_piece(sash, parts, op, plug_cs, pl, r + A + 0.5, -1.0)


def door_consoled(w=13.0, h=24.0, transom=4.4):
    """The Fairhaven's front door: a pair of leaves, each a tall glazed panel over a raised
    panel, under a transom leaded in a fan-and-drape pattern; reeded casings on plinth
    blocks; a flat hood (a frieze and a cornice) carried on two tall scrolled consoles.
    Printed face-up, one piece."""
    from . import openings as O
    op = rect(-w / 2, 0.0, w / 2, h + transom)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    face = -1.0
    body = ext(plug_cs, -pl, face)
    glass_cs, leads, panels = [], [], []
    for sg in (-1, 1):
        a, b = sorted((sg * 0.4, sg * (w / 2 - 0.9)))
        glass_cs.append(rect(a + 0.6, h * 0.45, b - 0.6, h - 1.2))
        panels.append(rect(a + 0.7, 1.4, b - 0.7, h * 0.45 - 1.4))
    tr = rect(-w / 2 + 0.9, h + 0.5, w / 2 - 0.9, h + transom - 0.6)
    glass_cs.append(tr)
    for a in np.linspace(math.radians(20), math.radians(160), 7):
        leads.append(stroke([(0.0, h + 0.5), (w * math.cos(a), h + 0.5 + w * math.sin(a))], 0.45, caps=False))
    ts = np.linspace(0.0, 1.0, 16)
    leads.append(stroke([(-w / 2 + (w) * t, h + transom - 1.0 - 1.4 * math.sin(math.pi * ((2 * t) % 1.0))) for t in ts], 0.45))
    gl = cs_union(glass_cs)
    grooves = [rect(-0.2, 0.0, 0.2, h), rect(-w / 2, h - 0.15, w / 2, h + 0.35)]
    body = body - ext(gl, -pl + O.GLASS, 0.5) - ext(cs_union(grooves) - gl, face - 0.25, 0.5)
    sash = [body, ext(gl, -pl, -pl + O.GLASS), ext(cs_union(leads) ^ tr, -pl + O.GLASS - 0.01, face - 0.15),
            ext(cs_union(panels), face - 0.01, face + 0.3), ext(plug_cs - plug_cs.offset(-0.5, JoinType.Miter, 4.0), -pl, 0.0)]
    parts = [ext(op - op.offset(-0.5, JoinType.Miter, 4.0), 0.0, O.CAS)]
    ht = h + transom
    cw = 2.0
    for sg in (-1, 1):
        u0, u1 = sorted((sg * w / 2, sg * (w / 2 + cw)))
        cas = ext(rect(u0, 0.0, u1, ht + 0.01), 0.0, 1.0)
        for du in (0.45, 1.0, 1.55):
            cas = cas + ext(rect(u0 + du - 0.2, 2.4, u0 + du + 0.2, ht - 0.3), 0.99, 1.3)
        parts.append(cas)
        parts.append(chamfer_box(u0 - 0.3, 0.0, u1 + 0.3, 2.4, 0.0, 1.5, c=0.3, bottom=0.0))
        # the console: a tall scroll standing on the casing's head, carrying the hood
        cu = (u0 + u1) / 2 + sg * 0.6
        con = cs_union([rect(cu - 0.7, ht - 3.2, cu + 0.7, ht + 1.8), circle((cu, ht - 3.2), 0.75, 16),
                        circle((cu + sg * 0.1, ht + 1.4), 0.9, 16)])
        parts.append(ext(con, 0.0, 1.8))
    hu = w / 2 + cw + 1.4
    parts.append(ext(rect(-hu + 0.4, ht - 0.01, hu - 0.4, ht + 1.8), 0.0, 1.1))
    parts.append(ext(rect(-hu + 1.2, ht + 0.4, hu - 1.2, ht + 1.4), 1.09, 1.4))
    parts.append(chamfer_box(-hu - 0.4, ht + 1.79, hu + 0.4, ht + 2.8, 0.0, 2.2, c=0.5, bottom=1.0))
    parts.append(chamfer_box(-hu, ht + 2.79, hu, ht + 3.2, 0.0, 1.6, c=0.3))
    parts.append(chamfer_box(-w / 2 - cw - 0.4, -0.8, w / 2 + cw + 0.4, 0.01, 0.0, 1.3, c=0.3, bottom=0.0))
    return O._one_piece(sash, parts, op, plug_cs, pl, ht + 3.2, -0.8)


def post_candlestick(h, collar=None, abacus=3.0, slot=(1.2, 1.0)):
    """A turned candlestick post: a square foot block, a turned base cup, a slim shaft with a
    triple ring collar a third of the way up and a torus under a square neck block (the
    Fairhaven)."""
    from . import porchwork as PW
    zb, zt = 3.0, h - 3.2
    L = zt - zb
    zc = zb + L * 0.33
    prof = [(0.0, zb - 0.01), (1.15, zb - 0.01), (1.15, zb + 0.25), (0.75, zb + 0.9), (0.85, zb + 1.5), (0.62, zb + 2.0),
            (0.6, zc - 0.9), (0.9, zc - 0.7), (0.72, zc - 0.45), (0.95, zc - 0.2), (0.95, zc + 0.2), (0.72, zc + 0.45),
            (0.9, zc + 0.7), (0.6, zc + 0.9), (0.55, zt - 1.0), (0.85, zt - 0.7), (0.85, zt - 0.3), (1.0, zt + 0.01)]
    body = PW._plinth() + box([-1.2, -1.2, 1.19], [1.2, 1.2, zb]) + PW._revolve(prof, 28)
    if collar is not None:
        body = body + box([-1.2, -1.2, collar - 1.6], [1.2, 1.2, collar + 0.2])
    body = body + box([-1.1, -1.1, zt], [1.1, 1.1, h - 1.8])
    return body + PW._top(h, abacus / 2, h - 1.8, 1.1, slot, shape="square")


def baluster_cupring(h, seg=20):
    """A cup-and-ring baluster: square ends, a slim stem rising into an open cup with a ring
    over it, a short neck above (the Fairhaven)."""
    from . import porchwork as PW
    H = h - 1.6
    t = [(0.0, 0.3), (0.35, 0.3), (0.55, 0.5), (0.62, 0.55), (0.66, 0.34), (0.7, 0.5), (0.75, 0.5), (0.8, 0.3),
         (1.0, 0.3)]
    prof = [(0.0, 0.79)] + [(r, 0.8 + f * H) for f, r in t]
    return PW._revolve(prof, seg) + box([-0.5, -0.5, 0.0], [0.5, 0.5, 0.81]) + box([-0.5, -0.5, h - 0.81], [0.5, 0.5, h])


def frieze_chainrings(u0, u1, v_bot, v_top):
    """A porch frieze of interlocking rings: a row of rings hung under the frieze board, each
    linked through its neighbours, a small boss dropping under every other one (the
    Fairhaven)."""
    rail0 = v_top - 1.0
    parts = [rect(u0, rail0, u1, v_top + 0.05)]
    R_ = min(1.5, (v_top - v_bot - 1.6) / 2)
    n = max(2, int((u1 - u0 - 0.6) / (R_ * 1.5)))
    step = (u1 - u0 - 2 * R_) / (n - 1)
    vc = rail0 - R_ + 0.3
    for k in range(n):
        c = (u0 + R_ + k * step, vc)
        parts.append(circle(c, R_, 28) - circle(c, R_ - 0.55, 28))
        if k % 2 == 0:
            parts.append(poly([(c[0] - 0.3, vc - R_ + 0.2), (c[0] + 0.3, vc - R_ + 0.2), (c[0], vc - R_ - 1.0)]))
    return cs_union(parts)


def skirt_clover(reg, d=1.2):
    """A skirt of upright boards pierced with a row of cloverleaves (three round lobes) (the
    Fairhaven)."""
    u0, v0, u1, v1 = reg.bounds()
    L = u1 - u0
    board = reg
    n = max(1, int(round(L / 3.2)))
    vm = (v0 + v1) / 2
    r = min(0.55, (v1 - v0) / 2 - 0.9)
    holes = []
    if r > 0.3:
        for i in range(n):
            c = u0 + L * (i + 0.5) / n
            holes.append(cs_union([circle((c, vm + r * 0.9), r, 16), circle((c - r * 0.9, vm - r * 0.4), r, 16),
                                   circle((c + r * 0.9, vm - r * 0.4), r, 16)]))
        board = reg - cs_union(holes)
    out = M.extrude(board, d * 0.6)
    grooves = cs_union([rect(u, v0 - 1, u + 0.4, v1 + 1) for u in np.arange(u0 + 1.2, u1, 1.6)]) ^ reg
    return out + M.extrude(board - grooves, d).translate([0, 0, 0.0])


def edge_vitruvian(L, z0, zc):
    """A porch-roof fascia carved with a running Vitruvian scroll (a wave curling over in turn)
    hung from the crown (the Fairhaven)."""
    n = max(1, int((L - 1.6) / 2.4))
    parts = [rect(0.3, zc - 0.5, L - 0.3, zc)]
    for k in range(n):
        u = 0.8 + (L - 1.6) * k / n
        p_ = (L - 1.6) / n
        c = (u + p_ * 0.62, zc - 1.05)
        parts.append(circle(c, 0.55, 16) - circle(c, 0.2, 10))
        parts.append(poly([(u, zc - 0.45), (u + p_ * 0.3, zc - 0.45), (c[0] - 0.4, c[1] + 0.3), (u + p_ * 0.15, zc - 1.6),
                           (u, zc - 1.6)]))
    return cs_union(parts) ^ rect(0.0, zc - 1.7, L, zc), 0.5


def chimney_quoined(w=12.0, d=10.0, h=30.0):
    """The Fairhaven's chimney: a Flemish-bond brick stack with stone quoins up every corner
    (long and short blocks in turn), a stone band two-thirds up, a corbelled neck and a
    chamfered stone cap with a raised coping round three flue openings. Stands on z = 0."""
    zc = h - 3.4
    body = box([-w / 2, -d / 2, 0.0], [w / 2, d / 2, zc]) + TW._skin(w, d, 0.0, zc - 0.2, TW._brick("flemish"))
    q = []
    z, k = 0.4, 0
    while z + 1.4 < zc - 3.4:
        ax, ay = (2.6, 1.6) if k % 2 == 0 else (1.6, 2.6)
        for sx in (-1, 1):
            for sy in (-1, 1):
                x0, x1 = sorted((sx * (w / 2 + 0.25), sx * (w / 2 + 0.25 - ax)))
                y0, y1 = sorted((sy * (d / 2 + 0.25), sy * (d / 2 + 0.25 - ay)))
                q.append(box([x0, y0, z], [x1, y1, z + 1.4]))
        z += 1.6
        k += 1
    body = body + union(q)
    zb = zq(zc * 0.66)
    body = body + TW._corbel_out(w, d, zb + 0.3, 0.3) + box([-w / 2 - 0.3, -d / 2 - 0.3, zb + 0.29], [w / 2 + 0.3, d / 2 + 0.3, zb + 1.2])
    body = body + TW._corbel_out(w, d, zc + 0.4, 0.4) + box([-w / 2 - 0.4, -d / 2 - 0.4, zc + 0.39], [w / 2 + 0.4, d / 2 + 0.4, zc + 1.2])
    body = body + chamfer_box(-w / 2 - 1.0, -d / 2 - 1.0, w / 2 + 1.0, d / 2 + 1.0, zc + 1.19, 1.2, c=0.4, bottom=0.4)
    body = body + box([-w / 2 + 0.6, -d / 2 + 0.6, zc + 2.39], [w / 2 - 0.6, d / 2 - 0.6, h])
    for x in (-w * 0.3, 0.0, w * 0.3):
        body = body - box([x - 1.0, -d / 2 + 1.8, h - 1.4], [x + 1.0, d / 2 - 1.8, h + 1])
    return body


CO.FRIEZE_EXTRA.update(wheat=frieze_wheat, ivy=frieze_ivy)
TW.BRACKET_EXTRA.update(palmette=bracket_palmette)
TW.FOUNDATION_EXTRA.update(snecked=foundation_snecked)
_PW.POSTS.update(candlestick=post_candlestick)
_PW.BALUSTERS.update(cupring=(baluster_cupring, 1.8))
_PW.FRIEZES.update(chainrings=frieze_chainrings)
_PW.SKIRTS.update(clover=skirt_clover)
_FT.EDGE_EXTRA.update(vitruvian=edge_vitruvian)

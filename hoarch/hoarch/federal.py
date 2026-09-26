"""Federal and later Colonial parts for the fourth batch (houses 41 to 50): each house's own
wall skin, foundation facing, cornice ornament (friezes, courses, brackets), window and door
families, chimney and roof trim. Like ``colonial``, the ornament registers itself with
``cornice`` and ``trimwork`` on import, and no part is shared between two houses.

Frames follow ``openings``: local (u, v, w) with u = 0 at the opening centre, v = 0 at its
bottom, w = 0 on the wall face; a one-piece insert is a plug with the glass and sash plus the
surround, printed face-up with supports under the surround."""
import math

import numpy as np
from manifold3d import JoinType, Manifold as M

from .core import RIB, box, circle, cs_union, poly, rect, union
from .ornament import chamfer_box, ext, oval, stroke
from . import cornice as CO, moulding as MD, openings as O, trimwork as TW
from .colonial import _st


# ================================================================== the Prescott (house 41, Federal)
# ------------------------------------------------------------------ skin and foundation
def flush_boards(region, datum=0.0, course=2.2, seed=11):
    """Federal flush boarding: wide boards laid edge to edge, a hairline joint between the
    courses and a butt joint here and there, so the whole house reads smooth and even, like
    dressed stone seen from the street."""
    from .skins import _grooved
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    rng = np.random.default_rng(seed)
    gs = []
    k = math.floor((v0 - datum) / course) - 1
    while datum + k * course < v1 + course:
        v = datum + k * course
        gs.append(rect(u0 - 1, v - 0.2, u1 + 1, v + 0.2))            # two layers: both edges on the grid
        u = u0 - rng.uniform(0.0, 22.0)
        while u < u1:
            u += rng.uniform(17.0, 28.0)
            gs.append(rect(u - 0.25, v, u + 0.25, v + course))
        k += 1
    return _grooved(region, gs, 0.25)


def foundation_vermiculated(reg, seed=0):
    """Brownstone ashlar with a band of vermiculated blocks: every other block along the top
    course is worked all over in worm tracks (short wandering grooves) inside a plain margin,
    the courses below dressed smooth with sunk joints (the Prescott)."""
    from .skins import _grooved
    b = reg.bounds()
    rng = np.random.default_rng(seed + 7)
    course, joint = 3.2, 0.5
    gs, worms = [], []
    k = 0
    v = b[3]
    while v > b[1] + 0.3:
        v0 = max(b[1], v - course)
        gs.append(rect(b[0] - 1, v0 - joint / 2, b[2] + 1, v0 + joint / 2))
        u = b[0] - rng.uniform(0.0, 4.0) - (k % 2) * 3.0
        j = 0
        while u < b[2]:
            L = rng.uniform(6.0, 8.5)
            gs.append(rect(u + L - joint / 2, v0, u + L + joint / 2, v))
            if k == 0 and j % 2 == 0:                     # the vermiculated band
                m = 0.8
                bx0, bx1, by0, by1 = u + m, u + L - m, v0 + m, v - m
                if bx1 - bx0 > 1.5 and by1 - by0 > 1.0:
                    x, y = rng.uniform(bx0, bx1), rng.uniform(by0, by1)
                    for _ in range(int((bx1 - bx0) * 1.4)):
                        a = rng.uniform(0, 2 * math.pi)
                        pts = [(x, y)]
                        for _s in range(3):
                            a += rng.uniform(-1.4, 1.4)
                            x = min(max(x + 0.8 * math.cos(a), bx0), bx1)
                            y = min(max(y + 0.8 * math.sin(a), by0), by1)
                            pts.append((x, y))
                        worms.append(stroke(pts, 0.5))
            u += L
            j += 1
        v = v0
        k += 1
    body = _grooved(reg, gs, 0.4)
    if worms:
        body = body - ext(cs_union(worms) ^ reg, 0.22, 1.0)
    return body


# ------------------------------------------------------------------ cornice ornament
def frieze_fasces(L, h, b, pitch, margin, pair, half):
    """Federal fasces: a bundle of three rods run the length of the frieze, bound at every
    station by a band with a ribbon crossed over it."""
    v0, v1 = 0.8, h - 0.8
    hh = v1 - v0
    gap = 0.4
    rod = (hh - 2 * gap) / 3
    rods = [rect(margin * 0.5, v0 + j * (rod + gap), L - margin * 0.5, v0 + j * (rod + gap) + rod) for j in range(3)]
    out = [_st(cs_union(rods), b, 0.35)]
    for u in CO._us(L, pitch, margin, 0.0):
        band = rect(u - 0.9, v0 - 0.2, u + 0.9, v1 + 0.2)
        out.append(_st(band, b, 0.55))
        x = stroke([(u - 1.6, v0 - 0.1), (u + 1.6, v1 + 0.1)], 0.5) + stroke([(u - 1.6, v1 + 0.1), (u + 1.6, v0 - 0.1)], 0.5)
        out.append(_st(x ^ rect(u - 1.7, v0 - 0.2, u + 1.7, v1 + 0.2), b, 0.75))
    return out, []


def _star(c, r, ri=None, ang=math.pi / 2):
    ri = ri or r * 0.45
    pts = []
    for k in range(10):
        a = ang + k * math.pi / 5
        rr = r if k % 2 == 0 else ri
        pts.append((c[0] + rr * math.cos(a), c[1] + rr * math.sin(a)))
    return poly(pts)


def frieze_arrows(L, h, b, pitch, margin, pair, half):
    """Arrows and stars: at every station two arrows crossed in a saltire through a ring, and
    in each bay between them a row of five-pointed stars."""
    v0, v1 = 0.8, h - 0.8
    hh = v1 - v0
    vm = (v0 + v1) / 2
    out = []
    for u in CO._us(L, pitch, margin, 0.0):
        dx = hh * 0.62
        for sg in (-1, 1):
            a0, a1 = (u - sg * dx, v0 + 0.1), (u + sg * dx, v1 - 0.1)       # shaft, head at a1
            out.append(_st(stroke([a0, a1], 0.45), b, 0.45))
            ang = math.atan2(a1[1] - a0[1], a1[0] - a0[0])
            ca, sa = math.cos(ang), math.sin(ang)
            tip = (a1[0] + 0.5 * ca, a1[1] + 0.5 * sa)
            base = (a1[0] - 0.7 * ca, a1[1] - 0.7 * sa)
            head = poly([tip, (base[0] - 0.55 * sa, base[1] + 0.55 * ca), (base[0] + 0.55 * sa, base[1] - 0.55 * ca)])
            out.append(_st(head ^ rect(u - 3, v0 - 0.3, u + 3, v1 + 0.3), b, 0.6))
            for f in (0.25, 0.6):                                            # fletching
                p = (a0[0] + f * ca, a0[1] + f * sa)
                out.append(_st(stroke([p, (p[0] - 0.6 * ca - 0.5 * sa, p[1] - 0.6 * sa + 0.5 * ca)], 0.4)
                               ^ rect(u - 3, v0 - 0.3, u + 3, v1 + 0.3), b, 0.4))
        out.append(_st(circle((u, vm), 1.05, 20) - circle((u, vm), 0.55, 16), b, 0.7))
    for uc, wd in CO._between(L, pitch, margin, pair, half + 1.4):
        r = min(1.35, hh / 2 - 0.1)
        n = max(1, int(wd / (2 * r + 1.2)))
        for j in range(n):
            x = uc - (n - 1) * (2 * r + 1.2) / 2 + j * (2 * r + 1.2)
            out.append(_st(_star((x, vm - 0.1), r), b, 0.45))
    return out, []


def course_beadlozenge(L, h, b, pitch, margin, p):
    """Beads and lozenges in turn along the course."""
    step = 1.9
    n = int((L - 1.0) / step)
    u0 = (L - (n - 1) * step) / 2
    out = []
    for k in range(n):
        u = u0 + k * step
        if k % 2 == 0:
            r = min(0.62, h / 2 - 0.05)
            out.append(ext(circle((u, h / 2), r, 16), b - 0.05, b + 0.55))
        else:
            out.append(ext(poly([(u - 0.55, h / 2), (u, h - 0.05), (u + 0.55, h / 2), (u, 0.05)]), b - 0.05, b + 0.45))
    return out


def bracket_guttae(h, d, t):
    """A Federal mutule: a shallow flat block with a fillet on its nose, three small drops
    (guttae) hanging under the front of it (side profile, top at v = 0)."""
    hb = min(h, max(1.4, 0.3 * d))
    body = poly([(0.0, 0.0), (d, 0.0), (d, -hb * 0.55), (d * 0.35, -hb * 0.55), (0.0, -hb)])
    fil = rect(d - 0.5, -hb * 0.55 - 0.3, d, 0.0)
    drops = [poly([(x - 0.3, -hb * 0.55 + 0.01), (x + 0.3, -hb * 0.55 + 0.01), (x + 0.2, -hb * 0.55 - 0.55), (x - 0.2, -hb * 0.55 - 0.55)])
             for x in (d - 1.1, d - 2.1, d - 3.1) if x > d * 0.4]
    return cs_union([body, fil] + drops)


CO.FRIEZE_EXTRA.update(fasces=frieze_fasces, arrows=frieze_arrows)
CO.COURSE_EXTRA.update(beadlozenge=course_beadlozenge)
TW.BRACKET_EXTRA.update(guttae=bracket_guttae)
TW.FOUNDATION_EXTRA.update(vermiculated=foundation_vermiculated)


# ------------------------------------------------------------------ windows and doors
def _sash66(w, h, lites=(3, 3), rows=(2, 2)):
    return O.window_insert(w, h, 0, lites=lites, rows=rows, bare=True)["insert"]


def _casing(op, w, h, A):
    """A flat casing with a raised back-band round a rectangular opening (sides and head)."""
    return [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS),
            ext((op.offset(A, JoinType.Miter, 4.0) - op) ^ rect(-w, 0.0, w, h + A), 0.0, O.CAS),
            ext((op.offset(A, JoinType.Miter, 4.0) - op.offset(A - 0.45, JoinType.Miter, 4.0)) ^ rect(-w, 0.0, w, h + A),
                O.CAS - 0.01, O.BEAD)]


def _fan(c, R, n=9, hub=None):
    """A carved half-round fan (sunburst) centred on c: a panel, raised rays with sunk flutes
    between them, a half-round hub and a beaded rim."""
    hub = hub or max(0.9, R * 0.22)
    half = circle(c, R, 48) ^ rect(c[0] - R - 1, c[1], c[0] + R + 1, c[1] + R + 1)
    parts = [ext(half, 0.0, 0.5)]
    rays = []
    for a in np.linspace(0.0, math.pi, n + 1)[1:-1]:
        rays.append(stroke([(c[0] + hub * math.cos(a), c[1] + hub * math.sin(a)),
                            (c[0] + (R - 0.55) * math.cos(a), c[1] + (R - 0.55) * math.sin(a))], 0.5))
    parts.append(ext(cs_union(rays) ^ half, 0.49, 0.9))
    parts.append(ext(circle(c, hub, 20) ^ half, 0.49, 1.1))
    parts.append(ext((circle(c, R, 48) - circle(c, R - 0.5, 48)) ^ half, 0.49, 0.95))
    return parts


def window_blindarch(w, h, A=1.0, band=1.2):
    """Federal ground-floor window: a six-over-six sash in a casing, set in a blind arch: over
    its head a carved half-round fan (tympanum) under an archivolt springing from moulded
    impost blocks, a keystone at the crown; a sill on a small bed."""
    op = O.opening_cs(w, h, 0)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    parts = _casing(op, w, h, A)
    vs = h + A                                             # the springing line
    R = w / 2 + A
    parts.append(ext(rect(-R, h + A - 0.1, R, vs + 0.7), 0.0, 0.7))              # the head under the fan
    parts += [p.translate([0, 0, 0.0]) for p in _fan((0.0, vs + 0.4), R - 0.1)]
    ring = (circle((0.0, vs + 0.4), R + band, 56) - circle((0.0, vs + 0.4), R - 0.1, 56)) ^ rect(-R - band - 1, vs + 0.4, R + band + 1, vs + R + band + 2)
    parts.append(ext(ring, 0.0, 0.9))
    parts.append(ext((circle((0.0, vs + 0.4), R + band, 56) - circle((0.0, vs + 0.4), R + band - 0.45, 56))
                     ^ rect(-R - band - 1, vs + 0.4, R + band + 1, vs + R + band + 2), 0.89, 1.3))
    for sg in (-1, 1):                                       # impost blocks
        u0, u1 = sorted((sg * (R - 0.1), sg * (R + band + 0.4)))
        parts.append(chamfer_box(u0, vs - 0.8, u1, vs + 0.4, 0.0, 1.3, c=0.3))
    kt = vs + 0.4 + R + band + 0.6
    parts.append(ext(poly([(-0.6, vs + 0.4 + R - 0.4), (0.6, vs + 0.4 + R - 0.4), (0.85, kt), (-0.85, kt)]), 0.0, 1.5))
    sw = w / 2 + A + 0.6
    parts.append(MD.run(-sw, sw, 0.0, MD.SILL, 1.0, up=False))
    parts.append(ext(rect(-w / 2 - 0.2, -1.8, w / 2 + 0.2, -0.9), 0.0, 0.6))
    return O._one_piece([_sash66(w, h)], parts, op, plug_cs, O.PLUG, kt, -1.8)


def _tablet_cap(half, v, n_pat=1):
    """A Federal entablature cap: a frieze board with reeded end blocks and oval paterae on
    it, under a thin moulded cornice. Returns (parts, top)."""
    parts = [ext(rect(-half, v - 0.1, half, v + 2.6), 0.0, 0.7)]
    for sg in (-1, 1):
        u0, u1 = sorted((sg * half, sg * (half - 1.8)))
        parts.append(ext(rect(u0, v, u1, v + 2.5), 0.69, 1.0))
        for dx in (0.45, 0.9, 1.35):
            x = sg * (half - dx)
            parts.append(ext(rect(x - 0.18, v + 0.35, x + 0.18, v + 2.15), 0.99, 1.2))
    for j in range(n_pat):
        x = -half + 1.8 + (2 * half - 3.6) * (j + 0.5) / n_pat
        parts.append(ext(oval((x, v + 1.25), 1.3, 0.8) - oval((x, v + 1.25), 0.8, 0.4), 0.69, 1.1))
        parts.append(ext(oval((x, v + 1.25), 0.45, 0.28), 0.69, 1.2))
    parts.append(MD.run(-half - 0.6, half + 0.6, v + 2.6 + 1.0, MD.CROWN, 1.0, up=False))
    return parts, v + 3.6


def window_tablet(w, h, A=1.0):
    """Federal upper window: a six-over-six sash in a casing under an entablature cap (a
    frieze with reeded end blocks and an oval patera, a thin cornice); a plain sill."""
    op = O.opening_cs(w, h, 0)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    parts = _casing(op, w, h, A)
    cap, top = _tablet_cap(w / 2 + A + 0.4, h + A)
    parts += cap
    sw = w / 2 + A + 0.5
    parts.append(MD.run(-sw, sw, 0.0, MD.SILL, 1.0, up=False))
    return O._one_piece([_sash66(w, h)], parts, op, plug_cs, O.PLUG, top, -1.0)


def window_wyatt(w, h, side=3.4, post=1.2, A=1.0):
    """A Federal tripartite (Wyatt) window: a six-over-six centre light between two narrow
    two-over-two side lights, parted by slender reeded pilasters, all under one entablature
    cap with three paterae."""
    W = w + 2 * side + 2 * post
    op = rect(-W / 2, 0.0, W / 2, h)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    sashes = [_sash66(w, h)]
    for sg in (-1, 1):
        xc = sg * (w / 2 + post + side / 2)
        sashes.append(_sash66(side, h, lites=(1, 1), rows=(2, 2)).translate([xc, 0, 0]))
    web = cs_union([rect(-w / 2 - post, 0.0, -w / 2, h), rect(w / 2, 0.0, w / 2 + post, h)])
    sashes.append(ext(web, -O.PLUG, 0.0))
    parts = _casing(op, W, h, A)
    for x0 in (-w / 2 - post, w / 2):                      # reeded pilasters on the posts
        parts.append(ext(rect(x0 - 0.15, 0.0, x0 + post + 0.15, h), 0.0, 0.7))
        for dx in (0.35, post - 0.35):
            parts.append(ext(rect(x0 + dx - 0.15, 0.6, x0 + dx + 0.15, h - 0.6), 0.69, 0.95))
    cap, top = _tablet_cap(W / 2 + A + 0.4, h + A, n_pat=3)
    parts += cap
    sw = W / 2 + A + 0.5
    parts.append(MD.run(-sw, sw, 0.0, MD.SILL, 1.0, up=False))
    return O._one_piece(sashes, parts, op, plug_cs, O.PLUG, top, -1.0)


def _swags(u0, u1, v, n, sag):
    """Lead cames hung in ``n`` swags from u0 to u1 along v, a small ring at each tie."""
    out = []
    for j in range(n):
        a, e = u0 + (u1 - u0) * j / n, u0 + (u1 - u0) * (j + 1) / n
        pts = [(a + (e - a) * t, v - sag * 4 * t * (1 - t)) for t in np.linspace(0, 1, 9)]
        out.append(stroke(pts, RIB))
    for j in range(n + 1):
        x = u0 + (u1 - u0) * j / n
        out.append(circle((x, v), 0.55, 12) - circle((x, v), 0.2, 8))
    return out


def door_adam(w, h, side=3.0, transom=3.4, A=1.2, fan=True):
    """The Federal (Adam) entrance: a six-panel door between leaded sidelights under a
    transom leaded in swags, framed by engaged colonnettes on pedestals; over it (``fan``) a
    carved half-round fan in an archivolt with a keystone springing from the colonnettes'
    capitals; without it, a tablet cap (the back door)."""
    W = w + 2 * side
    H = h + transom
    op = rect(-W / 2, 0.0, W / 2, H)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    body = [ext(plug_cs, -pl, -1.0)]
    lp, _ = O._leaf("six_panel", -w / 2 + 0.2, w - 0.4, h - 0.4, True)
    body += lp
    glass, cames = [], []
    for sg in (-1, 1):
        u0, u1 = sorted((sg * (w / 2 + 0.3), sg * (W / 2 - O.CLR - 0.5)))
        glass.append(rect(u0, h * 0.28, u1, h - 0.5))
        body.append(chamfer_box(u0, 1.0, u1, h * 0.28 - 0.5, -1.0, 0.4, c=0.2))
        um = (u0 + u1) / 2
        cames.append(oval((um, h * 0.64), (u1 - u0) / 2 - 0.1, 2.2) - oval((um, h * 0.64), (u1 - u0) / 2 - 0.1 - RIB, 2.2 - RIB))
        cames.append(rect(u0, h * 0.64 - RIB / 2, u1, h * 0.64 + RIB / 2))
    tcs = rect(-W / 2 + O.CLR + 0.5, h + 0.3, W / 2 - O.CLR - 0.5, H - O.CLR - 0.5)
    glass.append(tcs)
    cames += _swags(-W / 2 + 1.0, W / 2 - 1.0, H - 1.0, 4, 1.2)
    g = cs_union(glass)
    body = [p - ext(g, -pl + O.GLASS, 0.5) for p in body]
    sash = body + [ext(g, -pl, -pl + O.GLASS), ext(plug_cs - plug_cs.offset(-0.5, JoinType.Miter, 4.0), -pl, 0.0),
                   ext(rect(-W, h - 0.3, W, h + 0.3) ^ plug_cs, -pl, -0.4),
                   ext(cs_union([rect(-w / 2 - 0.3, 0.3, -w / 2 + 0.2, h), rect(w / 2 - 0.2, 0.3, w / 2 + 0.3, h)]) ^ plug_cs, -pl, -0.4)]
    sash.append(ext(cs_union(cames) ^ g.offset(0.1, JoinType.Miter, 4.0), -pl + O.GLASS - 0.01, -0.5))
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS)]
    cr = 0.85                                                # engaged colonnettes
    for sg in (-1, 1):
        uc = sg * (W / 2 + cr + 0.1)
        parts.append(chamfer_box(uc - cr - 0.5, 0.0, uc + cr + 0.5, 2.6, 0.0, 1.4, c=0.3, bottom=0.0))
        shaft = M.cylinder(H - 2.6 - 1.6, cr, cr * 0.9, 24).rotate([-90, 0, 0]).translate([uc, 2.6, 0.0])
        parts.append(shaft ^ box([uc - 2, 0, 0.0], [uc + 2, H + 5, 3.0]))
        parts.append(chamfer_box(uc - cr - 0.4, H - 1.6, uc + cr + 0.4, H + 0.2, 0.0, 1.5, c=0.35))    # capital
    top = H + 0.2
    if fan:
        R = W / 2 + 0.2
        vs = H + 0.2
        parts.append(ext(rect(-W / 2 - 0.1, H - 0.2, W / 2 + 0.1, vs + 0.3), 0.0, 0.8))
        parts += _fan((0.0, vs), R, n=13)
        ring = (circle((0.0, vs), R + A, 64) - circle((0.0, vs), R, 64)) ^ rect(-R - A - 1, vs - 0.3, R + A + 1, vs + R + A + 2)
        parts.append(ext(ring, 0.0, 1.0))
        parts.append(ext((circle((0.0, vs), R + A, 64) - circle((0.0, vs), R + A - 0.5, 64))
                         ^ rect(-R - A - 1, vs, R + A + 1, vs + R + A + 2), 0.99, 1.4))
        top = vs + R + A + 0.7
        parts.append(ext(poly([(-0.7, vs + R - 0.4), (0.7, vs + R - 0.4), (1.0, top), (-1.0, top)]), 0.0, 1.7))
    else:
        cap, top = _tablet_cap(W / 2 + cr * 2 + 0.6, H + 0.2)
        parts += cap
    return O._one_piece(sash, parts, op, plug_cs, pl, top, 0.0)


# ------------------------------------------------------------------ chimney and roof trim
def chimney_dentil(w=8.0, d=11.0, h=30.0):
    """A Federal stack: brick in running bond, a stone band, a brick corbel stepping out at 45
    degrees under a course of brick dentils, and a stone cap."""
    h = round(h / 0.2) * 0.2
    sh = h - 3.6
    body = box([-w / 2, -d / 2, 0.0], [w / 2, d / 2, sh])
    body = body + TW._skin(w, d, 0.0, sh - 2.8, TW._brick("running"))
    body = body + box([-w / 2 - 0.4, -d / 2 - 0.4, sh - 2.6], [w / 2 + 0.4, d / 2 + 0.4, sh - 1.6])      # stone band
    body = body + TW._corbel_out(w, d, sh + 0.6, 0.6) + box([-w / 2 - 0.6, -d / 2 - 0.6, sh - 0.01], [w / 2 + 0.6, d / 2 + 0.6, sh + 1.4])
    dent = []
    for x in np.arange(-w / 2, w / 2 + 0.01, 1.2):
        dent.append(box([x - 0.3, -d / 2 - 1.0, sh + 0.6], [x + 0.3, d / 2 + 1.0, sh + 1.4]))
    for y in np.arange(-d / 2, d / 2 + 0.01, 1.2):
        dent.append(box([-w / 2 - 1.0, y - 0.3, sh + 0.6], [w / 2 + 1.0, y + 0.3, sh + 1.4]))
    body = body + (TW._corbel_out(w + 1.2, d + 1.2, sh + 1.4, 0.4) ^ box([-w, -d, sh + 0.9], [w, d, sh + 1.41])) + union(dent)
    body = body + box([-w / 2 - 1.1, -d / 2 - 1.1, sh + 1.39], [w / 2 + 1.1, d / 2 + 1.1, h - 0.8])
    body = body + box([-w / 2 + 0.6, -d / 2 + 0.6, h - 0.81], [w / 2 - 0.6, d / 2 - 0.6, h])
    return body - box([-w / 2 + 1.4, -d / 2 + 1.4, sh - 4.0], [w / 2 - 1.4, d / 2 - 1.4, h + 1])


def roof_balustrade(pts, z0, h=7.0, t=1.2, ped=2.4, pitch=22.0, bay=5.2):
    """A Federal roof balustrade round the eave: panelled pedestals at the corners and every
    ``pitch`` with a ball finial, between them a plinth and a rail and panels of saltires,
    each crossing through a ring. One solid in world coordinates, standing on z0 along the
    closed outline ``pts`` (its outer face on the outline). Prints upright with the roof: the
    saltires lean at 45 degrees, the rings bridge 1 mm."""
    out = []
    n = len(pts)
    plinth, rail = 1.0, 0.8
    for i in range(n):
        p0, p1 = np.array(pts[i], float), np.array(pts[(i + 1) % n], float)
        L = float(np.linalg.norm(p1 - p0))
        tv = (p1 - p0) / L
        nv = np.array([tv[1], -tv[0]])                        # outward for a CCW outline
        A = np.array([[tv[0], 0.0, -nv[0], p0[0]], [tv[1], 0.0, -nv[1], p0[1]], [0.0, 1.0, 0.0, z0]])
        cs = [rect(0.0, 0.0, L, plinth), rect(0.0, h - rail, L, h)]
        k = max(1, int(round((L - ped) / pitch)))
        stations = [ped / 2 + (L - ped) * j / k for j in range(k + 1)]
        for a, e in zip(stations[:-1], stations[1:]):
            a, e = a + ped / 2, e - ped / 2
            m = max(1, int(round((e - a) / bay)))
            wb = (e - a) / m
            for j in range(m):
                x0, x1 = a + j * wb, a + (j + 1) * wb
                xc, vc = (x0 + x1) / 2, (plinth + h - rail) / 2
                cs.append(stroke([(x0 + 0.2, plinth), (x1 - 0.2, h - rail)], 0.6))
                cs.append(stroke([(x0 + 0.2, h - rail), (x1 - 0.2, plinth)], 0.6))
                cs.append(circle((xc, vc), 1.05, 20) - circle((xc, vc), 0.5, 16))
                if j > 0:
                    cs.append(rect(x0 - 0.3, plinth, x0 + 0.3, h - rail))
        panel = M.extrude(cs_union(cs) ^ rect(0.0, 0.0, L, h), t)
        out.append(panel.transform(A))
        for s in stations:                                     # pedestals
            pedestal = box([s - ped / 2, 0.0, 0.0], [s + ped / 2, h + 0.4, t + 0.5]) + \
                box([s - ped / 2 - 0.3, h + 0.2, -0.3], [s + ped / 2 + 0.3, h + 0.8, t + 0.8])
            pedestal = pedestal - box([s - ped / 2 + 0.5, 1.4, -0.5], [s + ped / 2 - 0.5, h - 1.0, 0.2])
            ball = M.sphere(0.8, 16).translate([s, h + 1.9, t / 2 + 0.25]) + \
                M.cylinder(0.8, 0.45, 0.45, 12).rotate([-90, 0, 0]).translate([s, h + 0.7, t / 2 + 0.25])
            out.append((pedestal + ball).transform(A))
    return union(out)

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
        u = u0 - rng.uniform(0.0, 40.0)
        while u < u1:
            u += rng.uniform(34.0, 52.0)
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
                    for _ in range(int((bx1 - bx0) * (by1 - by0) * 2.6)):
                        x, y = rng.uniform(bx0, bx1), rng.uniform(by0, by1)
                        a = rng.uniform(0, 2 * math.pi)
                        pts = [(x, y)]
                        for _s in range(2):
                            a += rng.uniform(-1.2, 1.2)
                            x = min(max(x + 0.6 * math.cos(a), bx0), bx1)
                            y = min(max(y + 0.6 * math.sin(a), by0), by1)
                            pts.append((x, y))
                        worms.append(stroke(pts, 0.45))
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
        r = min(1.6, hh / 2 - 0.05)
        n = max(1, int(wd / (2 * r + 1.4)))
        for j in range(n):
            x = uc - (n - 1) * (2 * r + 1.4) / 2 + j * (2 * r + 1.4)
            out.append(_st(_star((x, vm - 0.1), r, ri=r * 0.58), b, 0.5))
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
    for x0 in (-w / 2 - post, w / 2):                      # fluted pilasters on the posts
        pil = ext(rect(x0 - 0.15, 0.0, x0 + post + 0.15, h), 0.0, 0.9)
        parts.append(pil - ext(rect(x0 + post / 2 - 0.2, 0.8, x0 + post / 2 + 0.2, h - 0.8), 0.6, 1.2))
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
        um, hw = (u0 + u1) / 2, (u1 - u0) / 2
        for vc in (h * 0.43, h * 0.62, h * 0.81):
            lz = poly([(um - hw, vc), (um, vc + 2.6), (um + hw, vc), (um, vc - 2.6)])
            cames.append(lz - lz.offset(-RIB, JoinType.Miter, 4.0))
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


def roof_curb(pts, z0, z1, w=1.8):
    """A flat curb round the roof's edge for a balustrade to stand on: a strip ``w`` wide
    inside the closed outline ``pts``, from z0 up to a level top at z1."""
    from .core import offset
    cs = poly(pts)
    return M.extrude(cs - offset(cs, -w), z1 - z0).translate([0, 0, z0])


def balustrade_runs(pts, z0, **kw):
    """The roof balustrade in four runs (see ``roof_balustrade``): the front and back take
    the corner pedestals, the ends run between them. Returns [(name, solid)]."""
    whole = roof_balustrade(pts, z0, **kw)
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    d = kw.get("ped", 2.4) + 0.8
    big = 1e3
    front = whole ^ box([-big, -big, -big], [big, y0 + d, big])
    back = whole ^ box([-big, y1 - d, -big], [big, big, big])
    mid = whole ^ box([-big, y0 + d, -big], [big, y1 - d, big])
    west = mid ^ box([-big, -big, -big], [(x0 + x1) / 2, big, big])
    east = mid ^ box([(x0 + x1) / 2, -big, -big], [big, big, big])
    return [("front", front), ("back", back), ("west", west), ("east", east)]


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


# ================================================================== the Bellerive (house 42, French Colonial)
from . import porchwork as PW
from .colonial import _lens


# ------------------------------------------------------------------ skins and foundation
def stucco_spalled(region, datum=0.0, seed=5):
    """Creole stucco over brick: a smooth coat of lime stucco over soft brick in common bond,
    fallen away here and there in ragged patches that show the brick beneath."""
    from .skins import brick_bond
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    rng = np.random.default_rng(seed)
    patches = []
    for _ in range(int((u1 - u0) * (v1 - v0) / 240.0) + 1):
        cx, cy = rng.uniform(u0, u1), rng.uniform(v0, v1)
        rx, ry = rng.uniform(2.6, 5.4), rng.uniform(1.8, 3.4)
        pts = []
        for j in range(11):
            a = 2 * math.pi * j / 11
            rr = rng.uniform(0.6, 1.0)
            pts.append((cx + rx * rr * math.cos(a), cy + ry * rr * math.sin(a)))
        patches.append(poly(pts))
    holes = cs_union(patches) ^ region
    out = M.extrude(region - holes, 0.45)
    if not holes.is_empty():
        out = out + brick_bond(holes, "common", d=0.22, datum=datum)
    return out


def colombage(region, datum=0.0, post=7.2, tw=0.9):
    """Briquette-entre-poteaux: a timber frame (sill, plate and a rail at mid height, posts
    every ``post``, a brace in each tier of the end bays) standing proud of soft brick laid
    in the panels between the timbers."""
    from .skins import brick_bond
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    vm = round(((v0 + v1) / 2) / 0.2) * 0.2
    tim = [rect(u0 - 1, v0, u1 + 1, v0 + tw), rect(u0 - 1, v1 - tw, u1 + 1, v1 + 1), rect(u0 - 1, vm - tw / 2, u1 + 1, vm + tw / 2)]
    n = max(2, int(round((u1 - u0) / post)))
    ps = [u0 + (u1 - u0) * j / n for j in range(n + 1)]
    tim += [rect(x - tw / 2, v0, x + tw / 2, v1) for x in ps]
    for a, e in ((ps[0], ps[1]), (ps[-1], ps[-2])):
        tim.append(stroke([(a, v0 + tw), (e, vm - tw / 2)], tw))
        tim.append(stroke([(a, vm + tw / 2), (e, v1 - tw)], tw))
    tcs = cs_union(tim) ^ region
    out = ext(tcs, 0.0, 0.55)
    fill = region - tcs
    if not fill.is_empty():
        out = out + brick_bond(fill, "running", d=0.25, datum=datum)
    return out


def foundation_bricksill(reg, seed=0):
    """A low brick footing in running bond under a projecting course of bricks set on edge
    (a rowlock sill), its top chamfered (the Bellerive)."""
    from .skins import brick_bond
    b = reg.bounds()
    body = brick_bond(reg ^ rect(b[0] - 1, b[1] - 1, b[2] + 1, b[3] - 1.4), "running", d=0.25)
    sill = chamfer_box(b[0], b[3] - 1.4, b[2], b[3], 0.0, 0.7, c=0.2, square=("u0", "u1"), bottom=0.7)
    joints = cs_union([rect(u - 0.2, b[3] - 1.3, u + 0.2, b[3] - 0.3) for u in np.arange(b[0] + 0.8, b[2], 0.9)])
    return body + (sill - ext(joints, 0.45, 1.0))


# ------------------------------------------------------------------ cornice ornament
def _fleur(c, s):
    """A fleur-de-lis ``s`` tall, centred on c."""
    x, y = c
    parts = [_lens((x, y + 0.14 * s), 0.62 * s, 0.8, math.pi / 2)]
    for sg in (-1, 1):
        parts.append(stroke([(x + sg * 0.2, y - 0.02 * s), (x + sg * 0.6, y + 0.1 * s), (x + sg * 0.85, y + 0.3 * s),
                             (x + sg * 0.6, y + 0.44 * s)], 0.5))
    parts.append(rect(x - 0.75, y - 0.12 * s, x + 0.75, y - 0.12 * s + 0.5))
    parts.append(poly([(x - 0.45, y - 0.12 * s), (x + 0.45, y - 0.12 * s), (x, y - 0.5 * s)]))
    return cs_union(parts)


def frieze_fleurs(L, h, b, pitch, margin, pair, half):
    """Fleurs-de-lis at every station, and between them a chain of small lozenges on a
    fillet."""
    v0, v1 = 0.8, h - 0.8
    hh = v1 - v0
    vm = (v0 + v1) / 2
    out = []
    for u in CO._us(L, pitch, margin, 0.0):
        out.append(_st(_fleur((u, vm), hh * 1.0) ^ rect(u - 2, v0 - 0.2, u + 2, v1 + 0.2), b, 0.45))
    for uc, wd in CO._between(L, pitch, margin, pair, half + 1.3):
        n = max(1, int(wd / 1.9))
        out.append(_st(rect(uc - wd / 2 + 0.3, vm - 0.2, uc + wd / 2 - 0.3, vm + 0.2), b, 0.25))
        for j in range(n):
            x = uc - (n - 1) * 1.9 / 2 + j * 1.9
            out.append(_st(poly([(x - 0.65, vm), (x, vm + 0.85), (x + 0.65, vm), (x, vm - 0.85)]), b, 0.45))
    return out, []


def frieze_grapes(L, h, b, pitch, margin, pair, half):
    """A grapevine: a waving stem the length of the frieze, a three-lobed leaf over each
    crest and a hanging cluster of grapes under each trough."""
    v0, v1 = 0.8, h - 0.8
    hh = v1 - v0
    vm = (v0 + v1) / 2
    amp = hh * 0.18
    per = pitch
    a0, a1 = margin * 0.5, L - margin * 0.5
    pts = [(u, vm + amp * math.sin(2 * math.pi * (u - a0) / per)) for u in np.arange(a0, a1 + 0.01, 0.4)]
    out = [_st(stroke(pts, 0.5), b, 0.35)]
    k = 0
    u = a0 + per / 4
    while u < a1 - 1.0:
        up = (k % 2 == 0)
        if up:                                   # a leaf above the crest
            c = (u, vm + amp + 0.9)
            leaf = cs_union([circle((c[0] + dx, c[1] + dy), 0.5, 12) for dx, dy in ((-0.55, 0.0), (0.55, 0.0), (0.0, 0.5))]
                            + [rect(c[0] - 0.2, vm + amp - 0.1, c[0] + 0.2, c[1])])
            out.append(_st(leaf ^ rect(u - 2, v0 - 0.2, u + 2, v1 + 0.2), b, 0.45))
        else:                                    # a cluster below the trough
            top = vm - amp - 0.3
            grapes = []
            for row, n in enumerate((3, 2, 1)):
                for j in range(n):
                    x = u - (n - 1) * 0.36 + j * 0.72
                    y = top - 0.35 - row * 0.62
                    if y - 0.36 > v0 - 0.2:
                        grapes.append(circle((x, y), 0.36, 12))
            if grapes:
                out.append(_st(cs_union(grapes + [rect(u - 0.2, top - 0.3, u + 0.2, vm - amp + 0.1)]), b, 0.5))
        u += per / 2
        k += 1
    return out, []


def course_chevron(L, h, b, pitch, margin, p):
    """A chevron course: a zigzag moulding the length of the course."""
    step = 1.8
    n = int((L - 1.0) / step)
    u0 = (L - n * step) / 2
    pts = [(u0 + j * step / 2, (h - 0.35) if j % 2 else 0.35) for j in range(2 * n + 1)]
    return [ext(stroke(pts, 0.5) ^ rect(0, 0, L, h), b - 0.05, b + 0.55)]


def bracket_rafter(h, d, t):
    """An exposed rafter tail: a plain rafter whose end is cut in a cyma (side profile, top at
    v = 0)."""
    hb = min(h, 1.5)
    pts = [(0.0, 0.0), (d, 0.0)]
    for s in np.linspace(0.0, 1.0, 10):
        x = d - 1.2 * (s - math.sin(2 * math.pi * s) / (2 * math.pi))
        pts.append((x, -hb * s))
    pts += [(0.0, -hb)]
    return poly(pts)


CO.FRIEZE_EXTRA.update(fleurs=frieze_fleurs, grapes=frieze_grapes)
CO.COURSE_EXTRA.update(chevron=course_chevron)
TW.BRACKET_EXTRA.update(rafter=bracket_rafter)
TW.FOUNDATION_EXTRA.update(bricksill=foundation_bricksill)


# ------------------------------------------------------------------ the gallery
def post_creole(h, collar=None, abacus=2.6, slot=(1.2, 1.0)):
    """A Creole gallery colonnette: slender, turned, with a ring at mid height, a torus base on
    a square plinth and a square abacus."""
    z1 = h - 2.6
    zm = round((z1 * 0.5) / 0.2) * 0.2
    r = 0.95
    prof = [(0.0, 1.19), (1.3, 1.19), (1.3, 1.45), (1.1, 1.65), (r, 1.85), (r, zm - 0.4), (1.15, zm - 0.2), (1.15, zm + 0.2),
            (r, zm + 0.4), (r * 0.94, z1), (1.15, z1 + 0.21), (1.15, z1 + 0.5), (r * 0.94, z1 + 0.7), (r * 0.94, z1 + 0.9)]
    body = PW._revolve(prof, 28) + PW._plinth(2.8)
    return body + PW._top(h, abacus / 2, z1 + 0.9, r * 0.94, slot, seg=28)


def baluster_diamond(h):
    """A square baluster set diagonally (a diamond in plan) between square collars."""
    s = 0.72
    shaft = M.cube([s, s, h - 1.0]).translate([-s / 2, -s / 2, 0.5]).rotate([0, 0, 45])
    return shaft + box([-0.5, -0.5, 0.0], [0.5, 0.5, 0.51]) + box([-0.5, -0.5, h - 0.51], [0.5, 0.5, h])


def frieze_cutwork(u0, u1, v_bot, v_top):
    """A Creole gallery frieze: a plain board pierced with a row of small round holes, a bead
    along its lower edge."""
    v0 = v_top - 3.2
    board = rect(u0, v0, u1, v_top + 0.05)
    n = max(1, int((u1 - u0 - 1.0) / 2.1))
    holes = [circle((u0 + (u1 - u0) * (j + 0.5) / n, v0 + 1.7), 0.55, 14) for j in range(n)]
    return (board - cs_union(holes)) + rect(u0, v0 - 0.5, u1, v0 + 0.01)


PW.POSTS["creole"] = post_creole
PW.BALUSTERS.update(diamond=(baluster_diamond, 1.5))
PW.FRIEZES.update(cutwork=frieze_cutwork)


# ------------------------------------------------------------------ windows, doors and shutters
def door_creole(w, h, transom=4.6, rise=1.8, A=1.1):
    """Creole French doors (portes-fenetres): two glazed leaves under a segmental transom
    glazed with radiating bars, in a flat casing that follows the head, a keystone at its
    crown and a small sill."""
    op = O.opening_cs(w, h, rise)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    dh = h - rise - transom + rise
    dh = h - transom
    lw = (w - 2 * O.CLR - 1.0 - 0.5) / 2
    u = -w / 2 + O.CLR + 0.5
    body, lights = [ext(plug_cs, -pl, -1.0)], []
    for i in range(2):
        lp, light = O._leaf("french", u, lw, dh, i == 0)
        body += lp
        if light is not None:
            lights.append(light)
        u += lw + 0.5
    tcs = plug_cs.offset(-0.5, JoinType.Miter, 4.0) ^ rect(-w, dh + 0.3, w, h + 5)
    g = cs_union(lights) + tcs
    sash = [p - ext(g, -pl - 1, 0.0) for p in body]
    sash += [ext(g, -pl, -pl + O.GLASS), ext(plug_cs - plug_cs.offset(-0.5, JoinType.Miter, 4.0), -pl, 0.0),
             ext(rect(-w, dh - 0.3, w, dh + 0.3) ^ plug_cs, -pl, -0.4)]
    c = (0.0, dh + 0.3)
    rays = cs_union([stroke([c, (w * math.cos(a), dh + 0.3 + w * math.sin(a))], RIB) for a in np.linspace(math.pi / 5, 4 * math.pi / 5, 4)])
    sash.append(ext(rays ^ tcs, -pl + O.GLASS - 0.01, -0.5))
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS)]
    band = (op.offset(A, JoinType.Miter, 4.0) - op) ^ rect(-w - 5, 0.0, w + 5, h + 10)
    parts.append(ext(band, 0.0, 0.7))
    parts.append(ext((op.offset(A, JoinType.Miter, 4.0) - op.offset(A - 0.45, JoinType.Miter, 4.0)) ^ rect(-w - 5, 0.0, w + 5, h + 10),
                     0.69, 1.05))
    parts.append(ext(poly([(-0.65, h - 0.4), (0.65, h - 0.4), (0.9, h + A + 0.6), (-0.9, h + A + 0.6)]), 0.0, 1.4))
    parts.append(chamfer_box(-w / 2 - A - 0.4, -0.8, w / 2 + A + 0.4, 0.0, 0.0, 1.0, c=0.3, bottom=0.0))
    return O._one_piece(sash, parts, op, plug_cs, pl, h + A + 0.6, -0.8)


def door_batten_arched(w, h, rise=2.4, A=1.3, split=True):
    """Creole ground-floor opening: a pair (``split``) of batten leaves of vertical boards,
    each with two battens and a brace, closing a segmental arch; a flat arched head band on
    plain jambs with a keystone."""
    op = O.opening_cs(w, h, rise)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    face = plug_cs.offset(-0.3, JoinType.Miter, 4.0)
    body = ext(plug_cs, -pl, -0.4)
    grooves = [rect(x - 0.2, 0.2, x + 0.2, h + 1) for x in np.arange(-w / 2 + 1.3, w / 2 - 0.5, 1.3)]
    if split:
        grooves.append(rect(-0.3, 0.2, 0.3, h + 1))
    body = body - ext(cs_union(grooves) ^ face, -0.6, 0.0)
    bat = []
    halves = ((-w / 2 + O.CLR + 0.5, -0.5), (0.5, w / 2 - O.CLR - 0.5)) if split else ((-w / 2 + O.CLR + 0.5, w / 2 - O.CLR - 0.5),)
    for a, e in halves:
        v1, v2 = 2.0, h - rise - 2.2
        bat += [rect(a, v1 - 0.5, e, v1 + 0.5), rect(a, v2 - 0.5, e, v2 + 0.5), stroke([(a + 0.4, v1 + 0.4), (e - 0.4, v2 - 0.4)], 0.8)]
    body = body + ext(cs_union(bat) ^ face, -0.41, -0.1)
    body = body + ext(plug_cs - plug_cs.offset(-0.5, JoinType.Miter, 4.0), -pl, 0.0)        # the rim meets the casing
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS)]
    band = (op.offset(A, JoinType.Miter, 4.0) - op) ^ rect(-w - 5, 0.0, w + 5, h + 10)
    parts.append(ext(band, 0.0, 0.8))
    parts.append(ext(poly([(-0.7, h - 0.5), (0.7, h - 0.5), (1.0, h + A + 0.7), (-1.0, h + A + 0.7)]), 0.0, 1.5))
    return O._one_piece([body], parts, op, plug_cs, pl, h + A + 0.7, 0.0)


def shutter_batten(w, h, t=0.8):
    """A Creole batten shutter (contrevent), open against the wall: vertical boards, two
    battens and a diagonal brace between them. Local frame as features.shutter (u 0..w,
    v 0..h, back at w = 0; prints face-up)."""
    body = ext(rect(0, 0, w, h), 0.0, 0.5)
    grooves = [rect(x - 0.2, -1, x + 0.2, h + 1) for x in np.arange(1.2, w - 0.5, 1.2)]
    if grooves:
        body = body - ext(cs_union(grooves), 0.3, 1.0)
    v1, v2 = round(h * 0.16 / 0.2) * 0.2, round(h * 0.84 / 0.2) * 0.2
    bat = cs_union([rect(0.3, v1 - 0.5, w - 0.3, v1 + 0.5), rect(0.3, v2 - 0.5, w - 0.3, v2 + 0.5),
                    stroke([(0.6, v1 + 0.4), (w - 0.6, v2 - 0.4)], 0.8)])
    return body + ext(bat, 0.49, t)


# ------------------------------------------------------------------ chimney, roof and dormer
def chimney_arcade(w=9.0, d=9.0, h=30.0):
    """A Creole stack: smooth stucco, a three-step corbel band, and at the top a little arcade:
    round-headed flue vents on every face under a projecting cap."""
    h = round(h / 0.2) * 0.2
    sh = h - 5.0
    body = box([-w / 2, -d / 2, 0.0], [w / 2, d / 2, h - 1.0])
    for k in range(3):
        g = 0.3 * (k + 1)
        body = body + box([-w / 2 - g, -d / 2 - g, sh - 1.8 + 0.6 * k], [w / 2 + g, d / 2 + g, sh - 1.2 + 0.6 * k])
    body = body + TW._corbel_out(w, d, h - 0.4, 0.8) + box([-w / 2 - 1.1, -d / 2 - 1.1, h - 0.41], [w / 2 + 1.1, d / 2 + 1.1, h + 0.6])
    vents = []
    for axis in (0, 1):
        L = w if axis == 0 else d
        for x in (-L / 4, L / 4):
            arch = cs_union([rect(x - 0.7, sh + 0.8, x + 0.7, h - 2.4), circle((x, h - 2.4), 0.7, 16)])
            v = M.extrude(arch, (d if axis == 0 else w) + 4).translate([0, 0, -((d if axis == 0 else w) + 4) / 2])
            v = v.transform(np.array([[1.0, 0, 0, 0], [0, 0, 1.0, 0], [0, 1.0, 0, 0]])) if axis == 0 else \
                v.transform(np.array([[0, 0, 1.0, 0], [1.0, 0, 0, 0], [0, 1.0, 0, 0]]))
            vents.append(v)
    flue = box([-w / 2 + 1.3, -d / 2 + 1.3, sh], [w / 2 - 1.3, d / 2 - 1.3, h + 1])
    return body - union(vents) - flue


def dormer_creole(w=13.0, dep=16.0, hwall=12.0):
    """A Creole dormer: a steep gabled front (pitch 1:1) with corner boards and a rake board,
    a round-headed casement of two leaves (three lights each) under a fan of bars. Local as
    colonial.dormer_pedimented; returns (body, core, face)."""
    rise = w / 2
    face = poly([(-w / 2, 0.0), (w / 2, 0.0), (w / 2, hwall), (0.0, hwall + rise), (-w / 2, hwall)])
    body = ext(face, -dep, 0.0) - ext(face.offset(-1.2, JoinType.Miter, 4.0) ^ rect(-50, 1.2, 50, 99), -dep - 1, -1.2)
    lw = w * 0.46
    spring = hwall - 0.6
    light = cs_union([rect(-lw / 2, 2.0, lw / 2, spring), circle((0.0, spring), lw / 2, 32) ^ rect(-lw, spring, lw, spring + lw)])
    body = body - ext(light, -1.3, 1.0)
    bars = [rect(-0.25, 2.0, 0.25, spring), rect(-lw / 2, spring - 0.25, lw / 2, spring + 0.25)]
    for v in (2.0 + (spring - 2.0) / 3, 2.0 + 2 * (spring - 2.0) / 3):
        bars.append(rect(-lw / 2, v - 0.22, lw / 2, v + 0.22))
    bars += [stroke([(0.0, spring), (lw / 2 * math.cos(a), spring + lw / 2 * math.sin(a))], 0.45)
             for a in (math.pi / 4, math.pi / 2, 3 * math.pi / 4)]
    body = body + ext(cs_union(bars) ^ light, -1.2, -0.5)
    body = body + ext((light.offset(0.8, JoinType.Round) - light) ^ rect(-w, 1.2, w, hwall + rise), -0.01, 0.6)
    body = body + chamfer_box(-lw / 2 - 0.9, 1.2, lw / 2 + 0.9, 2.0, -0.01, 0.9, c=0.3, bottom=0.9)
    for sg in (-1, 1):
        body = body + ext(rect(sg * (w / 2) - (1.0 if sg > 0 else 0.0), 1.2, sg * (w / 2) + (0.0 if sg > 0 else 1.0), hwall),
                          -0.01, 0.5)
    rake = face - face.offset(-1.0, JoinType.Miter, 4.0)
    body = body + ext(rake ^ rect(-50, hwall - 0.2, 50, 99), -0.01, 0.8)
    core = ext(face.offset(-1.2, JoinType.Miter, 4.0) ^ rect(-50, 1.2, 50, hwall), -dep + 1.2, -1.2)
    return body, core, face


def stair_creole(width, rise_total, n, tread=2.6, cheek=2.2):
    """A grand Creole stair up to a raised gallery: ``n`` risers between stuccoed cheek walls
    that slope with the flight under a rounded coping, a square newel pier at the foot of each.
    Local: u across, w out from the gallery edge (the stair descends toward +w), v up."""
    r = rise_total / n
    run = n * tread
    parts = []
    for k in range(n):
        top = round((rise_total - k * r) / 0.2) * 0.2
        parts.append(box([-width / 2, 0, 0], [width / 2, top, (k + 1) * tread]))
    for s in (-1, 1):
        a, b = sorted((s * width / 2, s * (width / 2 + cheek)))
        wall = M.hull_points([(u, 0.0, w) for u in (a, b) for w in (0.0, run)] +
                             [(u, rise_total + 1.6, 0.0) for u in (a, b)] + [(u, 3.2, run) for u in (a, b)])
        cop = M.hull_points([(u, rise_total + 1.4, 0.0) for u in (a - 0.3, b + 0.3)] + [(u, rise_total + 2.2, 0.0) for u in (a - 0.3, b + 0.3)] +
                            [(u, 3.0, run - 1.6) for u in (a - 0.3, b + 0.3)] + [(u, 3.8, run - 1.6) for u in (a - 0.3, b + 0.3)])
        newel = box([a - 0.4, 0.0, run - 3.0], [b + 0.4, 6.4, run + 0.6]) + box([a - 0.8, 6.39, run - 3.4], [b + 0.8, 7.2, run + 1.0])
        parts += [wall, cop, newel]
    return union(parts)


def edge_ovals(L, z0, zc):
    """Gallery fascia (the Bellerive): a row of small ovals hung under the crown."""
    n = max(1, int((L - 1.2) / 1.8))
    ovs = [oval((0.6 + (L - 1.2) * (k + 0.5) / n, zc - 0.75), 0.62, 0.4) for k in range(n)]
    return cs_union(ovs) + rect(0.3, zc - 0.4, L - 0.3, zc), 0.5


from . import features as _FT                                   # noqa: E402
_FT.EDGE_EXTRA.update(ovals=edge_ovals)

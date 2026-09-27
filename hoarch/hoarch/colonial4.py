"""Colonial parts for the rest of the fourth batch (houses 43 to 50): each house's own wall
skins, foundation facing, cornice ornament (friezes, courses, brackets), window and door
families, porch posts, railings and friezes, chimneys and roof trim. Like ``federal``, the
ornament registers itself with ``cornice``, ``trimwork`` and ``porchwork`` on import, and no
part is shared between two houses.

Frames follow ``openings``: local (u, v, w) with u = 0 at the opening centre, v = 0 at its
bottom, w = 0 on the wall face; a one-piece insert is a plug with the glass and sash plus the
surround, printed face-up with supports under the surround."""
import math

import numpy as np
from manifold3d import JoinType, Manifold as M

from .core import RIB, box, circle, cs_union, poly, rect, union
from .ornament import chamfer_box, ext, oval, stepped, stroke
from . import cornice as CO, moulding as MD, openings as O, porchwork as PW, trimwork as TW
from .colonial import _lens, _st
from .skins import _lap, brick_bond


def _panel(cs, w0=-0.8):
    """A raised door panel: a field stepped up twice from the leaf's face at w0."""
    return stepped(cs, [(0.0, w0, w0 + 0.2), (0.3, w0 + 0.2, w0 + 0.4)])


def _glazed(body, g, pl, bars=None, rim_cs=None):
    """Cut the glass ``g`` out of the plug's body, add the two-layer glass at the back and the
    bars (a CrossSection) in front of it; ``rim_cs`` = the plug's outline for its rim."""
    out = [p - ext(g, -pl - 1, 0.0) for p in body]
    out.append(ext(g, -pl, -pl + O.GLASS))
    if rim_cs is not None:
        out.append(ext(rim_cs - rim_cs.offset(-0.5, JoinType.Miter, 4.0), -pl, 0.0))
    if bars is not None and not bars.is_empty():
        out.append(ext(bars ^ g.offset(0.1, JoinType.Miter, 4.0), -pl + O.GLASS - 0.01, -0.5))
    return out


def _muntins(cs, cols, rows, w=RIB):
    """Muntin bars dividing the bounds of ``cs`` into cols x rows lights."""
    u0, v0, u1, v1 = cs.bounds()
    bars = [rect(u0 + (u1 - u0) * j / cols - w / 2, v0 - 1, u0 + (u1 - u0) * j / cols + w / 2, v1 + 1) for j in range(1, cols)]
    bars += [rect(u0 - 1, v0 + (v1 - v0) * j / rows - w / 2, u1 + 1, v0 + (v1 - v0) * j / rows + w / 2) for j in range(1, rows)]
    return cs_union(bars) if bars else rect(0, 0, 0, 0)


def _sash_pair(w, h, cols=3, rows=(2, 2), meet=0.6):
    """A double-hung sash in its plug: two sashes of cols x rows lights, a meeting rail."""
    op = O.opening_cs(w, h, 0)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    inner = plug_cs.offset(-0.6, JoinType.Miter, 4.0)
    u0, v0, u1, v1 = inner.bounds()
    vm = (v0 + v1) / 2
    lo, hi = rect(u0, v0, u1, vm - meet / 2), rect(u0, vm + meet / 2, u1, v1)
    g = lo + hi
    bars = _muntins(lo, cols, rows[1]) ^ lo
    bars = bars + (_muntins(hi, cols, rows[0]) ^ hi)
    body = [ext(plug_cs, -pl, -0.6)]
    return _glazed(body, g, pl, bars, plug_cs) + [ext(rect(u0, vm - meet / 2 - 0.01, u1, vm + meet / 2 + 0.01), -pl, -0.3)], op, plug_cs


# ================================================================== the Pinckney (house 43, Charleston single house)
# ------------------------------------------------------------------ skins and foundation
def brick_tuckpointed(region, datum=0.0):
    """Charleston brick: Flemish bond in dark mortar with a fine raised fillet of lime putty run
    along every bed joint (tuckpointing), so each course reads between two crisp lines."""
    if region.is_empty():
        return M()
    body = brick_bond(region, "flemish", d=0.25, datum=datum)
    u0, v0, u1, v1 = region.bounds()
    bh, bed = 0.8, 0.2
    fil = []
    k = math.floor((v0 - datum) / bh) - 1
    while datum + k * bh < v1 + bh:
        v = datum + k * bh
        fil.append(rect(u0 - 1, v + bh - bed, u1 + 1, v + bh))
        k += 1
    return body + ext(cs_union(fil) ^ region, 0.0, 0.4)


def weatherboard_quoined(region, L, datum=0.0, qtop=None, qw=(4.2, 2.8), qh=2.8):
    """Charleston weatherboard: bevel boards 1.8 mm to the weather, each beaded along its butt,
    between wooden quoins at the corners: blocks chamfered to look like dressed stone, long
    and short in turn, standing proud of the boards (up to ``qtop``)."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    qtop = v1 if qtop is None else qtop
    strips = cs_union([rect(-1, v0 - 1, qw[0] + 0.3, qtop), rect(L - qw[0] - 0.3, v0 - 1, L + 1, qtop)])
    field = region - strips
    out = _lap(field, 1.8, [(0.0, 0.2), (0.2, 0.46), (0.45, 0.46), (0.6, 0.34), (1.8, 0.1)], datum)
    sreg = region ^ strips
    if not sreg.is_empty():
        out = out + ext(sreg, 0.0, 0.2)
        k = math.floor((v0 - datum) / qh)
        blocks = []
        while datum + k * qh < min(v1, qtop):
            a = datum + k * qh
            wq = qw[0] if k % 2 == 0 else qw[1]
            for x0, x1, sq in ((0.0, wq, ("u0",)), (L - wq, L, ("u1",))):
                top = min(a + qh - 0.2, qtop)
                if top - (a + 0.2) > 0.8:
                    blocks.append(chamfer_box(x0, a + 0.2, x1, top, 0.0, 0.75, c=0.3, square=sq))
            k += 1
        if blocks:
            out = out + (union(blocks) ^ ext(region, -0.1, 2.0))
    return out


def foundation_ventgrille(reg, seed=0):
    """A Charleston foundation: English-bond brick under a chamfered stone cap, pierced at
    intervals by crawlspace vents, each a sunk opening crossed by a diamond iron grille in a
    raised frame (the Pinckney)."""
    b = reg.bounds()
    capz = b[3] - 1.2
    body = brick_bond(reg ^ rect(b[0] - 1, b[1] - 1, b[2] + 1, capz), "english", d=0.25)
    cap = chamfer_box(b[0], capz, b[2], b[3], 0.0, 0.8, c=0.3, square=("u0", "u1"), bottom=0.8)
    L = b[2] - b[0]
    vh = min(3.2, capz - b[1] - 2.2)
    out = body + cap
    if vh > 1.6 and L > 12.0:
        n = max(1, int(L / 26.0))
        holes, grille, frames = [], [], []
        for j in range(n):
            uc = b[0] + L * (j + 0.5) / n
            vb = b[1] + (capz - b[1] - vh) / 2
            hole = rect(uc - 2.6, vb, uc + 2.6, vb + vh)
            holes.append(hole)
            bars = [stroke([(uc - 2.6 + k * 1.3 - vh, vb - 0.1), (uc - 2.6 + k * 1.3, vb + vh + 0.1)], 0.4) for k in range(0, 9)]
            bars += [stroke([(uc - 2.6 + k * 1.3, vb - 0.1), (uc - 2.6 + k * 1.3 - vh, vb + vh + 0.1)], 0.4) for k in range(0, 9)]
            grille.append(cs_union(bars) ^ hole)
            frames.append(hole.offset(0.5, JoinType.Miter, 4.0) - hole)
        hs = cs_union(holes)
        out = out - ext(hs, -0.1, 2.0)
        out = out + ext(cs_union(grille), 0.0, 0.3) + ext(cs_union(frames), 0.0, 0.55)
    return out


def _pier_tuckflemish(reg, seed=0):
    """Pier facing to match the Pinckney's walls: tuckpointed Flemish bond."""
    return brick_tuckpointed(reg)


# ------------------------------------------------------------------ cornice ornament
def _palmetto(c, s):
    """A palmetto ``s`` tall centred on c: a tapering trunk and a fan of nine fronds."""
    x, y = c
    y0, yc = y - s / 2, y + s * 0.16
    parts = [poly([(x - 0.38, y0), (x + 0.38, y0), (x + 0.26, yc), (x - 0.26, yc)])]
    R = s * 0.34
    for a in np.linspace(-0.25, math.pi + 0.25, 9):
        parts.append(stroke([(x, yc), (x + R * math.cos(a), yc + R * math.sin(a) * 0.95)], 0.4))
    return cs_union(parts)


def _crescent(c, r):
    """A crescent moon, horns to the upper right (the Carolina crescent)."""
    return circle(c, r, 28) - circle((c[0] + 0.42 * r, c[1] + 0.22 * r), 0.82 * r, 28)


def frieze_palmettos(L, h, b, pitch, margin, pair, half):
    """Palmettos at the stations and a crescent moon in every bay between them."""
    v0, v1 = 0.8, h - 0.8
    hh = v1 - v0
    vm = (v0 + v1) / 2
    out = []
    for u in CO._us(L, pitch, margin, 0.0):
        out.append(_st(_palmetto((u, vm), hh + 0.2) ^ rect(u - 2.6, v0 - 0.2, u + 2.6, v1 + 0.2), b, 0.5))
    for uc, wd in CO._between(L, pitch, margin, pair, half + 1.2):
        r = min(1.25, hh / 2 - 0.05)
        out.append(_st(_crescent((uc, vm), r), b, 0.45))
    return out, []


def course_beadreel(L, h, b, pitch, margin, p):
    """Bead and reel: long beads parted by bow-shaped reels."""
    step = 2.4
    n = int((L - 1.0) / step)
    u0 = (L - (n - 1) * step) / 2
    out = []
    hr = min(0.6, h / 2 - 0.08)
    for k in range(n):
        u = u0 + k * step
        out.append(ext(oval((u, h / 2), 0.78, hr, 16), b - 0.05, b + 0.5))
        if k < n - 1:
            x = u + step / 2
            out.append(ext(poly([(x - 0.3, h / 2 - hr), (x - 0.08, h / 2), (x - 0.3, h / 2 + hr), (x + 0.3, h / 2 + hr),
                                 (x + 0.08, h / 2), (x + 0.3, h / 2 - hr)]), b - 0.05, b + 0.4))
    return out


def _horn(mouth, sgn, length, width):
    """A horn of plenty from its mouth (at ``mouth``, opening toward -sgn) curling up to its tip,
    banded with three rings (grooves)."""
    mx, my = mouth
    cl = [(mx + sgn * length * t, my + width * 0.9 * t * t) for t in np.linspace(0.0, 1.0, 13)]
    left, right = [], []
    for j, (x, y) in enumerate(cl):
        t = j / 12
        wd = width * (1.0 - t) * 0.5 + 0.2
        if j < 12:
            dx, dy = cl[j + 1][0] - x, cl[j + 1][1] - y
        else:
            dx, dy = x - cl[j - 1][0], y - cl[j - 1][1]
        n_ = math.hypot(dx, dy)
        nx, ny = -dy / n_, dx / n_
        left.append((x + nx * wd, y + ny * wd))
        right.append((x - nx * wd, y - ny * wd))
    horn = poly(left + right[::-1])
    rings = []
    for t in (0.22, 0.44, 0.66):
        j = int(t * 12)
        x, y = cl[j]
        rings.append(rect(x - 0.14, y - width, x + 0.14, y + width).rotate(0))
    return horn - cs_union(rings)


def frieze_cornucopias(L, h, b, pitch, margin, pair, half):
    """Paired cornucopias: at every station two horns of plenty meet mouth to mouth over a
    heap of fruit; a small rosette in each bay between."""
    v0, v1 = 0.8, h - 0.8
    hh = v1 - v0
    vm = (v0 + v1) / 2
    out = []
    clip = lambda u, s: rect(u - s, v0 - 0.2, u + s, v1 + 0.2)
    ln, wd = hh * 0.95, hh * 0.46
    for u in CO._us(L, pitch, margin, 0.0):
        horns = cs_union([_horn((u - 0.7, vm - hh * 0.22), -1, ln, wd), _horn((u + 0.7, vm - hh * 0.22), 1, ln, wd)])
        out.append(_st(horns ^ clip(u, ln + 1.6), b, 0.5))
        fruit = cs_union([circle((u, vm - hh * 0.12), 0.62, 16), circle((u - 0.55, vm + hh * 0.18), 0.45, 14),
                          circle((u + 0.55, vm + hh * 0.18), 0.45, 14), circle((u, vm + hh * 0.34), 0.4, 14)])
        out.append(_st(fruit ^ clip(u, 2.0), b, 0.65))
    for uc, wd_ in CO._between(L, pitch, margin, pair, half + ln + 1.2):
        ros = cs_union([circle((uc + 0.55 * math.cos(a), vm + 0.55 * math.sin(a)), 0.36, 12) for a in np.linspace(0, 2 * math.pi, 6, endpoint=False)])
        out.append(_st(ros + circle((uc, vm), 0.35, 12), b, 0.45))
    return out, []


def bracket_scrollmod(h, d, t):
    """A scrolled modillion: a flat block whose underside falls in an S from the wall to a
    small roll at its nose (side profile, top at v = 0)."""
    hb = min(h, max(1.6, 0.32 * d))
    x1 = d - 0.6
    pts = [(0.0, 0.0), (d, 0.0), (d, -0.55)]
    for s in np.linspace(0.0, 1.0, 12):
        x = x1 * (1.0 - s)
        pts.append((x, -0.55 - (hb - 0.55) * (0.5 - 0.5 * math.cos(math.pi * s))))
    body = poly(pts)
    return cs_union([body, circle((d - 0.55, -0.9), 0.52, 16)])


CO.FRIEZE_EXTRA.update(palmettos=frieze_palmettos, cornucopias=frieze_cornucopias)
CO.COURSE_EXTRA.update(beadreel=course_beadreel)
TW.BRACKET_EXTRA.update(scrollmod=bracket_scrollmod)
TW.FOUNDATION_EXTRA.update(ventgrille=foundation_ventgrille, tuckflemish=_pier_tuckflemish)


# ------------------------------------------------------------------ windows, doors, shutters
def window_crossette(w, h, A=1.1, E=0.9):
    """A Charleston ground-floor window: a six-over-six sash in an eared architrave (the band
    steps out in crossettes at both top corners), a plain frieze and a moulded cornice over
    it, and a sill on two small tapered consoles."""
    sash, op, plug_cs = _sash_pair(w, h)
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS)]
    band = (op.offset(A, JoinType.Miter, 4.0) - op) ^ rect(-w, 0.0, w, h + A)
    ears = cs_union([rect(-w / 2 - A - E, h - 1.8, -w / 2 - A + 0.01, h + A), rect(w / 2 + A - 0.01, h - 1.8, w / 2 + A + E, h + A)])
    parts.append(ext(band + ears, 0.0, 0.7))
    outer = (op.offset(A, JoinType.Miter, 4.0) ^ rect(-w, 0.0, w, h + A)) + ears
    rim = (outer - outer.offset(-0.45, JoinType.Miter, 4.0)) ^ rect(-w - 5, 0.45, w + 5, h + A + 1)
    parts.append(ext(rim, 0.69, 1.05))
    hw = w / 2 + A + E
    vf = h + A
    parts.append(ext(rect(-hw, vf - 0.01, hw, vf + 2.2), 0.0, 0.6))
    top = vf + 2.0 + 1.2
    parts.append(MD.run(-hw - 0.6, hw + 0.6, top, MD.CROWN, 1.2, up=False))
    sw = w / 2 + A + 0.5
    parts.append(MD.run(-sw, sw, 0.0, MD.SILL, 1.0, up=False))
    for sg in (-1, 1):
        uc = sg * (w / 2 - 0.4)
        parts.append(chamfer_box(uc - 0.55, -2.8, uc + 0.55, -0.99, 0.0, 0.9, c=0.3, bottom=0.75))
    return O._one_piece(sash, parts, op, plug_cs, O.PLUG, top, -2.8)


def window_gibbs(w, h, A=0.8, jib=False):
    """A Gibbs surround: a thin architrave interrupted by rusticated blocks up each jamb, large
    and small in turn, and over the head a flat arch of five voussoirs with a tall keystone;
    a sill over a sunk apron. ``jib``: a floor-length window (a jib door onto the piazza),
    its sill a threshold and no apron."""
    sash, op, plug_cs = _sash_pair(w, h, rows=(3, 3) if jib else (2, 2))
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS)]
    parts.append(ext((op.offset(A, JoinType.Miter, 4.0) - op) ^ rect(-w, 0.0, w, h + A), 0.0, 0.5))
    bh = 2.6
    for j, f in enumerate((0.12, 0.5, 0.86)):
        vc = h * f
        big = 1.9 if j % 2 == 0 else 1.1
        for sg in (-1, 1):
            a, e = sorted((sg * (w / 2 - 0.01), sg * (w / 2 + A + big)))
            parts.append(chamfer_box(a, vc - bh / 2, e, vc + bh / 2, 0.0, 0.9, c=0.3))
    zc = h - 10.0
    xs = np.linspace(-w / 2 - A - 0.4, w / 2 + A + 0.4, 6)
    vt = h + 2.8
    k_ = (vt - zc) / (h - zc)
    for j in range(5):
        a, e = xs[j], xs[j + 1]
        top = vt + (0.9 if j == 2 else 0.0)
        pg = poly([(a, h), (e, h), (e * k_ * (top - zc) / (vt - zc), top), (a * k_ * (top - zc) / (vt - zc), top)])
        pg = pg.offset(-0.13, JoinType.Miter, 4.0)
        parts.append(ext(pg, 0.0, 1.35 if j == 2 else (1.0 if j % 2 == 0 else 0.8)))
    parts.append(ext(rect(xs[0] * k_, h - 0.01, xs[-1] * k_, h + 0.3) ^ rect(xs[0], h - 0.01, xs[-1], h + 0.3), 0.0, 0.5))
    top = vt + 0.9
    sw = w / 2 + A + 0.6
    if jib:
        parts.append(chamfer_box(-sw, -0.8, sw, 0.2, 0.0, 1.0, c=0.3, bottom=0.0))
        return O._one_piece(sash, parts, op, plug_cs, O.PLUG, top, -0.8)
    parts.append(MD.run(-sw, sw, 0.0, MD.SILL, 1.0, up=False))
    parts.append(ext(rect(-w / 2, -2.6, w / 2, -0.99), 0.0, 0.45) - ext(rect(-w / 2 + 0.6, -2.1, w / 2 - 0.6, -1.4), 0.25, 1.0))
    return O._one_piece(sash, parts, op, plug_cs, O.PLUG, top, -2.6)


def window_louvrefan(w, A=1.1):
    """A demilune gable vent: a half-round of horizontal louvres behind a moulded archivolt
    with a keystone, springing from a plain sill."""
    R = w / 2
    sp_v = 0.8
    op = O.opening_cs(w, sp_v + R, R)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    face = plug_cs.offset(-0.5, JoinType.Miter, 4.0)
    sash = [ext(plug_cs, -pl, -1.1), ext(plug_cs - face, -pl, 0.0)]
    slats = [rect(-w, v, w, v + 0.4) for v in np.arange(0.5, sp_v + R, 0.8)]
    sash.append(ext(cs_union(slats) ^ face, -1.11, -0.35))
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS)]
    ring = (op.offset(A, JoinType.Round) - op) ^ rect(-w - 5, 0.0, w + 5, sp_v + R + A + 1)
    parts.append(ext(ring, 0.0, 0.8))
    rimo = op.offset(A, JoinType.Round)
    parts.append(ext((rimo - rimo.offset(-0.45, JoinType.Round)) ^ rect(-w - 5, 0.5, w + 5, sp_v + R + A + 1), 0.79, 1.15))
    top = sp_v + R + A + 0.7
    parts.append(ext(poly([(-0.7, sp_v + R - 0.4), (0.7, sp_v + R - 0.4), (1.0, top), (-1.0, top)]), 0.0, 1.5))
    parts.append(chamfer_box(-R - A - 0.5, -0.9, R + A + 0.5, 0.0, 0.0, 1.1, c=0.3, bottom=0.0))
    return O._one_piece(sash, parts, op, plug_cs, pl, top, -0.9)


def _entablature(half, ve, frieze_orn=None):
    """A door's entablature from ve: architrave, frieze (with ``frieze_orn`` on it) and a
    moulded cornice. Returns (parts, top)."""
    parts = [ext(rect(-half, ve - 0.01, half, ve + 1.0), 0.0, 1.0),
             ext(rect(-half, ve + 1.0, half, ve + 2.6), 0.0, 0.8)]                  # laps into the cornice
    if frieze_orn is not None:
        parts.append(ext(frieze_orn, 0.79, 1.1))
    top = ve + 2.4 + 1.2
    parts.append(MD.run(-half - 0.6, half + 0.6, top, MD.CROWN, 1.2, up=False))
    return parts, top


def door_screen(w, h, A=0.9):
    """The street door of a Charleston piazza: a door of four raised panels (two tall over two
    square) under a half-round fanlight of radiating bars, in an archivolt with a keystone,
    between Tuscan pilasters that carry an entablature and a triangular pediment with a
    palmetto carved in its tympanum."""
    R = w / 2
    op = O.opening_cs(w, h + R, R)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    u0, u1 = -w / 2 + O.CLR + 0.3, w / 2 - O.CLR - 0.3
    body = [ext(plug_cs, -pl, -1.0), ext(rect(u0, 0.5, u1, h - 0.3), -1.0, -0.8)]
    mid = 0.0
    for a, e in ((u0 + 0.7, mid - 0.35), (mid + 0.35, u1 - 0.7)):
        body.append(_panel(rect(a, 1.2, e, h * 0.36)))
        body.append(_panel(rect(a, h * 0.36 + 1.0, e, h - 1.2)))
    body.append(ext(rect(-0.2, 0.5, 0.2, h - 0.3), -0.8, -0.5))
    g = plug_cs.offset(-0.5, JoinType.Miter, 4.0) ^ rect(-w, h + 0.3, w, h + R + 2)
    hub = circle((0.0, h + 0.3), 1.1, 24)
    rays = cs_union([stroke([(0.0, h + 0.3), (R * 1.2 * math.cos(a), h + 0.3 + R * 1.2 * math.sin(a))], RIB)
                     for a in np.linspace(math.pi / 7, 6 * math.pi / 7, 6)])
    ring = circle((0.0, h + 0.3), R * 0.62, 32) - circle((0.0, h + 0.3), R * 0.62 - RIB, 32)
    sash = _glazed(body, g, pl, rays + ring + hub, plug_cs)
    sash.append(ext(rect(-w, h - 0.3, w, h + 0.3) ^ plug_cs, -pl, -0.4))
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS)]
    arc = (circle((0.0, h), R + A, 56) - circle((0.0, h), R, 56)) ^ rect(-R - A - 1, h, R + A + 1, h + R + A + 1)
    parts.append(ext(arc, 0.0, 0.8))
    parts.append(ext((op.offset(A, JoinType.Miter, 4.0) - op) ^ rect(-w, 0.0, w, h + 0.01), 0.0, 0.8))
    kt = h + R + A + 0.5
    parts.append(ext(poly([(-0.6, h + R - 0.4), (0.6, h + R - 0.4), (0.9, kt), (-0.9, kt)]), 0.0, 1.3))
    ve = kt - 0.2                                         # the architrave laps the keystone
    pw = 1.7
    for sg in (-1, 1):
        uc = sg * (w / 2 + A - 0.2 + pw / 2)               # the shafts lap the door's band
        parts.append(chamfer_box(uc - pw / 2 - 0.35, 0.0, uc + pw / 2 + 0.35, 1.8, 0.0, 1.4, c=0.3, bottom=0.0))
        parts.append(ext(rect(uc - pw / 2, 1.79, uc + pw / 2, ve - 1.2), 0.0, 1.0))
        parts.append(chamfer_box(uc - pw / 2 - 0.35, ve - 1.21, uc + pw / 2 + 0.35, ve, 0.0, 1.3, c=0.35))
    half = w / 2 + A - 0.2 + pw + 0.35
    ent, vc = _entablature(half, ve)
    parts += ent
    hp = (half + 0.6) * 0.42
    tri = poly([(-half - 0.6, vc - 0.4), (half + 0.6, vc - 0.4), (0.0, vc + hp)])
    inner = tri.offset(-1.1, JoinType.Miter, 4.0)
    parts.append(ext(tri - inner, 0.0, 1.2))
    parts.append(ext(inner, 0.0, 0.5))
    parts.append(ext(_palmetto((0.0, vc + hp * 0.36), hp * 0.62) ^ inner.offset(-0.3, JoinType.Miter, 4.0), 0.49, 0.95))
    return O._one_piece(sash, parts, op, plug_cs, pl, vc + hp, 0.0)


def door_charleston(w, h, transom=4.2, A=1.1, back=False):
    """The house door in the piazza: a pair of leaves of three raised panels each under a
    transom glazed with an elliptical fan of bars, between fluted pilasters under an
    entablature whose frieze is carved with reeds. ``back``: the back door, one leaf of
    six panels under a plain transom and a flat head."""
    H = h + transom
    op = rect(-w / 2, 0.0, w / 2, H)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    u0, u1 = -w / 2 + O.CLR + 0.3, w / 2 - O.CLR - 0.3
    body = [ext(plug_cs, -pl, -1.0), ext(rect(u0, 0.5, u1, h - 0.3), -1.0, -0.8)]
    leaves = ((u0, -0.25), (0.25, u1)) if not back else ((u0, u1),)
    for a, e in leaves:
        pcs = [(0.9, h * 0.3), (h * 0.3 + 0.9, h * 0.52), (h * 0.52 + 0.9, h - 1.1)]
        cols = 1 if not back else 2
        cw = (e - a - 1.2 - 0.6 * (cols - 1)) / cols
        for c in range(cols):
            pa = a + 0.6 + c * (cw + 0.6)
            for vb, vt in pcs:
                body.append(_panel(rect(pa, vb, pa + cw, vt)))
    if not back:
        body.append(ext(rect(-0.25, 0.5, 0.25, h - 0.3), -0.8, -0.5))
    g = plug_cs.offset(-0.5, JoinType.Miter, 4.0) ^ rect(-w, h + 0.3, w, H + 2)
    if back:
        bars = _muntins(g, 4, 1)
    else:
        rx, ry = w / 2 - 1.2, transom - 1.4
        c = (0.0, h + 0.3)
        el = [(rx * math.cos(a), h + 0.3 + ry * math.sin(a)) for a in np.linspace(0, math.pi, 25)]
        bars = stroke(el, RIB) + cs_union([stroke([c, (rx * 1.6 * math.cos(a), h + 0.3 + ry * 1.6 * math.sin(a))], RIB)
                                            for a in np.linspace(math.pi / 6, 5 * math.pi / 6, 5)])
        bars = bars + (circle(c, 0.9, 20) ^ rect(-2, h + 0.3, 2, h + 2))
    sash = _glazed(body, g, pl, bars, plug_cs)
    sash.append(ext(rect(-w, h - 0.3, w, h + 0.3) ^ plug_cs, -pl, -0.4))
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS),
             ext((op.offset(A, JoinType.Miter, 4.0) - op) ^ rect(-w, 0.0, w, H + A), 0.0, 0.7)]
    pw = 1.6
    ve = H + A
    if not back:
        for sg in (-1, 1):
            uc = sg * (w / 2 + A + 0.2 + pw / 2)
            parts.append(chamfer_box(uc - pw / 2 - 0.3, 0.0, uc + pw / 2 + 0.3, 1.6, 0.0, 1.3, c=0.3, bottom=0.0))
            shaft = ext(rect(uc - pw / 2, 1.59, uc + pw / 2, ve - 1.0), 0.0, 1.0)
            fl = cs_union([rect(uc + dx - 0.2, 2.2, uc + dx + 0.2, ve - 1.6) for dx in (-0.4, 0.4)])
            parts.append(shaft - ext(fl, 0.7, 1.2))
            parts.append(chamfer_box(uc - pw / 2 - 0.3, ve - 1.01, uc + pw / 2 + 0.3, ve, 0.0, 1.25, c=0.35))
        half = w / 2 + A + 0.2 + pw + 0.3
        reeds = cs_union([rect(x - 0.18, ve + 1.25, x + 0.18, ve + 2.15) for x in np.arange(-half + 0.8, half - 0.6, 0.7)])
        ent, top = _entablature(half, ve, reeds)
    else:
        half = w / 2 + A + 0.4
        ent, top = _entablature(half, ve)
    parts += ent
    return O._one_piece(sash, parts, op, plug_cs, pl, top, 0.0)


def shutter_charleston(w, h, t=0.8):
    """A Charleston louvred shutter: stiles and three rails framing two fields of fixed
    louvres. Local frame as features.shutter (u 0..w, v 0..h, back at w = 0; face-up)."""
    st = 0.7
    vm = round(h * 0.5 / 0.2) * 0.2
    fields = cs_union([rect(st, 0.8, w - st, vm - 0.4), rect(st, vm + 0.4, w - st, h - 0.8)])
    body = ext(rect(0, 0, w, h) - fields, 0.0, t) + ext(fields, 0.0, 0.3)
    lv = cs_union([rect(st, v, w - st, v + 0.4) for v in np.arange(1.0, h - 0.8, 0.8)]) ^ fields
    return body + ext(lv, 0.29, t - 0.15)


# ------------------------------------------------------------------ the piazzas
def post_attic(h, collar=None, abacus=3.0, slot=(1.2, 1.0)):
    """A Tuscan column on an Attic base (two tori parted by a scotia) with entasis, an astragal
    at the necking and an echinus under a square abacus (the Pinckney's lower piazza)."""
    z1 = h - 2.6
    r = 1.2
    prof = [(0.0, 1.19), (1.6, 1.19), (1.6, 1.5), (1.45, 1.7), (1.3, 1.8), (1.3, 2.0), (1.48, 2.2), (1.48, 2.45),
            (1.3, 2.65), (r, 2.85), (r * 0.98, z1 * 0.35), (r * 0.86, z1), (1.08, z1 + 0.2), (1.08, z1 + 0.45),
            (r * 0.86, z1 + 0.65), (r * 0.86, z1 + 0.9)]
    body = PW._revolve(prof, 32) + PW._plinth(3.2)
    return body + PW._top(h, abacus / 2, z1 + 0.9, r * 0.86, slot, seg=32)


def post_palmetto(h, collar=None, abacus=2.8, slot=(1.2, 1.0)):
    """A slender colonnette with a palmetto capital: a bell ringed by eight upright fronds
    under a square abacus (the Pinckney's upper piazza)."""
    z1 = round((h - 3.4) / 0.2) * 0.2
    r = 0.9
    prof = [(0.0, 1.19), (1.25, 1.19), (1.25, 1.45), (1.05, 1.65), (r, 1.85), (r * 0.95, z1), (1.05, z1 + 0.2), (1.05, z1 + 0.4),
            (r * 0.95, z1 + 0.5), (1.25, z1 + 1.6), (1.3, z1 + 1.8)]
    body = PW._revolve(prof, 28) + PW._plinth(2.8)
    leaves = []
    for a in np.linspace(0, 2 * math.pi, 8, endpoint=False):
        ca, sa = math.cos(a), math.sin(a)
        tx, ty = -sa * 0.22, ca * 0.22
        pts = []
        for rr, zz in ((r * 0.9, z1 + 0.5), (1.42, z1 + 1.55), (1.2, z1 + 1.9)):
            pts += [(rr * ca + tx, rr * sa + ty, zz), (rr * ca - tx, rr * sa - ty, zz)]
        leaves.append(M.hull_points(pts))
    return body + union(leaves) + PW._top(h, abacus / 2, z1 + 1.8, 1.3, slot, seg=28)


def baluster_charleston(h):
    """A slender turned baluster: a square foot, a long vase with a ring at its neck, a square
    head (the Pinckney's lower piazza)."""
    top = h - 0.5
    prof = [(0.0, 0.5), (0.45, 0.5), (0.45, 0.65), (0.32, 0.85), (0.52, 0.5 + (top - 0.5) * 0.35), (0.3, 0.5 + (top - 0.5) * 0.7),
            (0.44, 0.5 + (top - 0.5) * 0.76), (0.44, 0.5 + (top - 0.5) * 0.82), (0.3, 0.5 + (top - 0.5) * 0.88), (0.3, top)]
    return PW._revolve(prof, 16) + box([-0.5, -0.5, 0.0], [0.5, 0.5, 0.51]) + box([-0.5, -0.5, top - 0.01], [0.5, 0.5, h])


def fill_ice(L, vb, vt):
    """Cracked-ice lattice (Chinese Chippendale): bays of irregular panes, each bay the mirror
    of the last, parted by plain stiles (the Pinckney's upper piazza)."""
    H = vt - vb
    n = max(1, int(round(L / (H * 1.05))))
    net = [((0.0, 0.3), (0.42, 0.46)), ((0.36, 0.0), (0.42, 0.46)), ((0.42, 0.46), (0.62, 1.0)), ((0.42, 0.46), (0.72, 0.24)),
           ((0.72, 0.24), (1.0, 0.1)), ((0.72, 0.24), (1.0, 0.64)), ((0.0, 0.78), (0.28, 1.0)), ((0.18, 0.0), (0.0, 0.14))]
    parts = []
    for i in range(n):
        a, e = L * i / n, L * (i + 1) / n
        for p, q in net:
            px, qx = (p[0], q[0]) if i % 2 == 0 else (1 - p[0], 1 - q[0])
            parts.append(stroke([(a + px * (e - a), vb + p[1] * H), (a + qx * (e - a), vb + q[1] * H)], 0.55))
        parts.append(rect(a - 0.3, vb, a + 0.3, vt))
    parts.append(rect(L - 0.3, vb, L + 0.3, vt))
    return parts


def frieze_crescent(u0, u1, v_bot, v_top):
    """A piazza frieze: a board sawn with a row of crescent moons, horns up, over a bead."""
    v0 = v_top - 3.0
    board = rect(u0, v0, u1, v_top + 0.05)
    n = max(1, int((u1 - u0 - 1.0) / 2.4))
    holes = []
    for j in range(n):
        c = (u0 + (u1 - u0) * (j + 0.5) / n, v0 + 1.5)
        holes.append(circle(c, 0.95, 24) - circle((c[0], c[1] + 0.42), 0.82, 24))
    return (board - cs_union(holes)) + rect(u0, v0 - 0.5, u1, v0 + 0.01)


def edge_reeded(L, z0, zc):
    """Piazza fascia (the Pinckney): upright reeds under the crown."""
    xs = np.arange(0.8, L - 0.6, 0.9)
    reeds = [rect(x - 0.22, zc - 1.7, x + 0.22, zc - 0.2) for x in xs]
    return cs_union(reeds) + rect(0.3, zc - 0.45, L - 0.3, zc), 0.45


def skirt_diamondgrille(reg, d=1.2):
    """Piazza skirt (the Pinckney): a board pierced with diamond-latticed vents."""
    u0, v0, u1, v1 = reg.bounds()
    if v1 - v0 < 2.0:
        return M.extrude(reg, d)
    L = u1 - u0
    n = max(1, int(round(L / 7.0)))
    holes, bars = [], []
    for j in range(n):
        a, e = u0 + L * j / n + 0.8, u0 + L * (j + 1) / n - 0.8
        hole = rect(a, v0 + 0.8, e, v1 - 0.8)
        holes.append(hole)
        for x in np.arange(a - (v1 - v0), e + 0.1, 1.2):
            bars += [stroke([(x, v0), (x + (v1 - v0), v1)], 0.45), stroke([(x + (v1 - v0), v0), (x, v1)], 0.45)]
    hs = cs_union(holes)
    return M.extrude(reg - hs, d) + M.extrude(cs_union(bars) ^ hs, d * 0.5)


PW.POSTS.update(attic=post_attic, palmetto=post_palmetto)
PW.BALUSTERS.update(charleston=(baluster_charleston, 1.6))
PW.FILLS.update(ice=fill_ice)
PW.FRIEZES.update(crescent=frieze_crescent)
PW.SKIRTS.update(diamondgrille=skirt_diamondgrille)


# ------------------------------------------------------------------ chimney
def chimney_panelled(w=8.0, d=12.0, h=30.0):
    """A Charleston stack: stuccoed, a sunk round-headed panel on each broad face, a
    three-step corbelled cap under a coping and two round flue pots."""
    h = round(h / 0.2) * 0.2
    sh = h - 3.8
    body = box([-w / 2, -d / 2, 0.0], [w / 2, d / 2, sh])
    for k in range(3):
        g = 0.3 * (k + 1)
        body = body + box([-w / 2 - g, -d / 2 - g, sh + 0.6 * k - 0.01], [w / 2 + g, d / 2 + g, sh + 0.6 * (k + 1)])
    zc = sh + 1.8
    body = body + box([-w / 2 - 1.2, -d / 2 - 1.2, zc - 0.01], [w / 2 + 1.2, d / 2 + 1.2, zc + 0.8])
    for sy in (-1, 1):
        body = body + M.cylinder(2.0, 1.25, 1.05, 24).translate([0, sy * d / 4, zc + 0.79])
    flues = union([M.cylinder(6.0, 0.6, 0.6, 16).translate([0, sy * d / 4, zc - 3.0]) for sy in (-1, 1)])
    body = body - flues
    pan = []
    ph0, ph1 = sh - 10.0, sh - 2.2
    for axis, L, D_ in ((0, w, d), (1, d, w)):
        pw_ = L - 2.8
        arch = cs_union([rect(-pw_ / 2, ph0, pw_ / 2, ph1 - pw_ / 2), circle((0.0, ph1 - pw_ / 2), pw_ / 2, 24)])
        m = M.extrude(arch, D_ + 2.0).translate([0, 0, -(D_ + 2.0) / 2])
        slab_ = m - M.extrude(arch, D_ - 1.0).translate([0, 0, -(D_ - 1.0) / 2])
        if axis == 0:
            pan.append(slab_.transform(np.array([[1.0, 0, 0, 0], [0, 0, 1.0, 0], [0, 1.0, 0, 0]])))
        else:
            pan.append(slab_.transform(np.array([[0, 0, 1.0, 0], [1.0, 0, 0, 0], [0, 1.0, 0, 0]])))
    return body - union(pan)


from . import features as _FT                                   # noqa: E402
_FT.EDGE_EXTRA.update(reeded=edge_reeded)


# ================================================================== the Randolph (house 44, Tidewater Virginia)
# ------------------------------------------------------------------ skin and foundation
def brick_glazedheader(region, datum=0.0, bl=2.4, bh=0.8, head=0.35, bed=0.2):
    """Tidewater brick: Flemish bond whose headers are glazed (burnt dark and glassy in the
    kiln), laid so they stand proud of the stretchers and chequer the whole wall."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    hl = bl / 2
    step = bl + hl + 2 * head
    st_, hd = [], []
    k = math.floor((v0 - datum) / bh) - 1
    while datum + k * bh < v1:
        v = datum + k * bh
        top = v + bh - bed
        u = u0 - step - (k % 2) * step / 2
        while u < u1 + step:
            st_.append(rect(u, v, u + bl, top))
            hd.append(rect(u + bl + head, v, u + bl + head + hl, top))
            u += step
        k += 1
    out = M.extrude(region, 0.05)
    s_ = cs_union(st_) ^ region
    h_ = cs_union(hd) ^ region
    return out + ext(s_, 0.0, 0.25) + ext(h_, 0.0, 0.42)


def foundation_englishtorus(reg, seed=0):
    """A Tidewater footing: English-bond brick under a moulded water table (a course of
    bricks rubbed to a torus), where the wall above steps back (the Randolph)."""
    b = reg.bounds()
    tz = b[3] - 1.4
    body = brick_bond(reg ^ rect(b[0] - 1, b[1] - 1, b[2] + 1, tz), "english", d=0.25)
    torus = chamfer_box(b[0], tz, b[2], b[3], 0.0, 0.9, c=0.4, square=("u0", "u1"), bottom=0.45)
    joints = cs_union([rect(u - 0.18, tz + 0.2, u + 0.18, b[3] - 0.2) for u in np.arange(b[0] + 1.2, b[2], 1.3)])
    return body + (torus - ext(joints, 0.55, 1.0))


# ------------------------------------------------------------------ cornice ornament
def frieze_tobacco(L, h, b, pitch, margin, pair, half):
    """Virginia tobacco: at every station two broad leaves crossed in a saltire, and in each
    bay a five-pointed tobacco blossom on a short stem."""
    v0, v1 = 0.8, h - 0.8
    hh = v1 - v0
    vm = (v0 + v1) / 2
    out = []
    for u in CO._us(L, pitch, margin, 0.0):
        leaves = cs_union([_lens((u, vm), hh * 1.3, hh * 0.46, a) for a in (math.radians(38), math.radians(142))])
        ribs = cs_union([stroke([(u - hh * 0.5 * math.cos(a), vm - hh * 0.5 * math.sin(a)),
                                 (u + hh * 0.5 * math.cos(a), vm + hh * 0.5 * math.sin(a))], 0.3)
                         for a in (math.radians(38), math.radians(142))])
        out.append(_st(leaves ^ rect(u - 3, v0 - 0.2, u + 3, v1 + 0.2), b, 0.4))
        out.append(_st(ribs ^ rect(u - 3, v0 - 0.2, u + 3, v1 + 0.2), b, 0.55))
    for uc, wd in CO._between(L, pitch, margin, pair, half + 2.2):
        r = min(1.05, hh / 2 - 0.3)
        bloom = cs_union([_lens((uc + r * 0.55 * math.cos(a), vm + 0.3 + r * 0.55 * math.sin(a)), r * 1.0, 0.55, a)
                          for a in np.linspace(math.pi / 2, math.pi / 2 + 2 * math.pi, 5, endpoint=False)])
        out.append(_st(bloom + rect(uc - 0.2, v0, uc + 0.2, vm), b, 0.45))
    return out, []


def frieze_dogwood(L, h, b, pitch, margin, pair, half):
    """Dogwood: a gently waving branch the length of the frieze, a four-bracted blossom
    (each bract notched at its tip) on every crest and a pair of leaves in every trough."""
    v0, v1 = 0.8, h - 0.8
    hh = v1 - v0
    vm = (v0 + v1) / 2
    amp = hh * 0.14
    a0, a1 = margin * 0.5, L - margin * 0.5
    pts = [(u, vm + amp * math.cos(2 * math.pi * (u - a0) / pitch)) for u in np.arange(a0, a1 + 0.01, 0.4)]
    out = [_st(stroke(pts, 0.45), b, 0.3)]
    u = a0
    k = 0
    while u < a1 - 0.5:
        if k % 2 == 0:
            c = (u, vm + amp)
            r = min(1.25, hh / 2 - 0.1)
            bracts = []
            for a in (math.pi / 4, 3 * math.pi / 4, 5 * math.pi / 4, 7 * math.pi / 4):
                p = (c[0] + r * 0.5 * math.cos(a), c[1] + r * 0.5 * math.sin(a))
                br = _lens(p, r * 1.05, r * 0.72, a)
                notch = circle((c[0] + r * 1.02 * math.cos(a), c[1] + r * 1.02 * math.sin(a)), 0.22, 10)
                bracts.append(br - notch)
            fl = cs_union(bracts) ^ rect(u - 2.5, v0 - 0.2, u + 2.5, v1 + 0.2)
            out.append(_st(fl, b, 0.45))
            out.append(_st(circle(c, 0.42, 14), b, 0.65))
        else:
            c = (u, vm - amp)
            lv = cs_union([_lens((c[0] + sg * 0.8, c[1] - 0.35), 1.7, 0.75, math.radians(-25 if sg > 0 else 205)) for sg in (-1, 1)])
            out.append(_st(lv ^ rect(u - 2.5, v0 - 0.2, u + 2.5, v1 + 0.2), b, 0.4))
        u += pitch / 2
        k += 1
    return out, []


def course_billet(L, h, b, pitch, margin, p):
    """A billet moulding: two rows of short blocks, the upper row set over the gaps of the
    lower."""
    out = []
    hr = (h - 0.3) / 2
    for row, (va, off) in enumerate(((0.1, 0.0), (0.2 + hr, 1.0))):
        n = int((L - 1.0 - off) / 2.0)
        for k in range(n):
            u = 0.5 + off + k * 2.0
            out.append(ext(rect(u, va, u + 1.0, va + hr), b - 0.05, b + (0.5 if row == 0 else 0.4)))
    return out


def bracket_cavettomod(h, d, t):
    """A modillion whose underside is a cavetto: a hollow quarter curve from the wall up to a
    square nose (side profile, top at v = 0)."""
    hb = min(h, max(1.6, 0.3 * d))
    pts = [(0.0, 0.0), (d, 0.0), (d, -0.5)]
    for s in np.linspace(0.0, 1.0, 12)[1:]:
        t_ = s * math.pi / 2
        pts.append((d - d * math.sin(t_), -hb + (hb - 0.5) * math.cos(t_)))
    return poly(pts)


CO.FRIEZE_EXTRA.update(tobacco=frieze_tobacco, dogwood=frieze_dogwood)
CO.COURSE_EXTRA.update(billet=course_billet)
TW.BRACKET_EXTRA.update(cavettomod=bracket_cavettomod)
TW.FOUNDATION_EXTRA.update(englishtorus=foundation_englishtorus)


# ------------------------------------------------------------------ the jerkinhead roof
def jerkin_planes(W, D, z_eave, s_main, d_eave, z_clip, s_end, rake):
    """The four planes of a side-gabled jerkinhead (clipped-gable) roof on the rectangle
    (0..W, 0..D), ridge along x: the two long slopes from their eaves, and at each end a
    steeper slope rising from the rake's edge at ``z_clip``. Returns (south, north, west, east)."""
    from .roof import Plane
    return (Plane((0.0, -d_eave), (0.0, 1.0), z_eave, s_main), Plane((W, D + d_eave), (0.0, -1.0), z_eave, s_main),
            Plane((-rake, D), (1.0, 0.0), z_clip, s_end), Plane((W + rake, 0.0), (-1.0, 0.0), z_clip, s_end))


def plane_texture(fp, pl, others, shape, pitch=1.6, wtab=2.2, d=0.4):
    """Shingle courses on the part of plane ``pl`` that is lowest among ``others`` inside the
    plan outline ``fp`` (as roof.hip_texture, for one face)."""
    from .core import scallop_rows
    from .roof import _halfplane
    from .core import frame
    reg = fp
    for pj in others:
        ax = pl.s * pl.t[0] - pj.s * pj.t[0]
        ay = pl.s * pl.t[1] - pj.s * pj.t[1]
        c = (pl.z0 - pl.s * (pl.q @ pl.t)) - (pj.z0 - pj.s * (pj.q @ pj.t))
        reg = reg ^ _halfplane(ax, ay, c)
    if reg.is_empty():
        return M()
    s = pl.s
    cth = 1 / math.sqrt(1 + s * s)
    t = pl.t
    e = np.array([t[1], -t[0]])
    q = pl.q
    A2 = np.array([[e[0], e[1], -(e @ q)], [t[0] / cth, t[1] / cth, -(t @ q) / cth]])
    loc = reg.transform(A2)
    tex = scallop_rows(loc, pitch, wtab, d=d, shape=shape, datum=loc.bounds()[1])
    vdir = np.array([t[0] * cth, t[1] * cth, s * cth])
    ndir = np.array([-t[0] * s * cth, -t[1] * s * cth, cth])
    return tex.translate([0, 0, -0.03]).transform(frame([q[0], q[1], pl.z0], [e[0], e[1], 0.0], vdir, ndir))


def jerkin_faces(env, planes, fp, tk=2.8, texture="square", tex_kw=None):
    """The clipped faces of a jerkinhead: for each end plane, a slab ``tk`` thick under it
    (closing the hollow roof body the clip opened) and its shingle courses."""
    from .roof import Plane, below
    Ls, Ln, Ew, Ee = planes
    kw = dict(tex_kw or {})
    slabs, texs = [], []
    for E, others in ((Ew, (Ls, Ln, Ee)), (Ee, (Ls, Ln, Ew))):
        dz = tk * math.sqrt(1 + E.s * E.s)
        lo = Plane(E.q, E.t, E.z0 - dz, E.s)
        top = below(env, E)
        slabs.append(top - below(top, lo))
        texs.append(plane_texture(fp, E, others, texture, **kw))
    return union(slabs), union(texs)


# ------------------------------------------------------------------ windows and doors
def window_segped(w, h, A=1.0):
    """A Tidewater ground-floor window: a nine-over-nine sash in a moulded architrave, a
    frieze, and over it a segmental pediment (its raking cornice following the arc) resting
    on two small consoles at the frieze's ends."""
    sash, op, plug_cs = _sash_pair(w, h, cols=3, rows=(3, 3))
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS)]
    band = (op.offset(A, JoinType.Miter, 4.0) - op) ^ rect(-w, 0.0, w, h + A)
    parts.append(ext(band, 0.0, 0.7))
    outer = op.offset(A, JoinType.Miter, 4.0) ^ rect(-w, 0.0, w, h + A)
    parts.append(ext((outer - outer.offset(-0.45, JoinType.Miter, 4.0)) ^ rect(-w, 0.45, w, h + A + 1), 0.69, 1.05))
    hw = w / 2 + A + 0.2
    vf = h + A
    parts.append(ext(rect(-hw, vf - 0.01, hw, vf + 1.8), 0.0, 0.6))
    for sg in (-1, 1):
        uc = sg * (hw - 0.55)
        parts.append(chamfer_box(uc - 0.55, vf - 1.4, uc + 0.55, vf + 1.8, 0.0, 1.0, c=0.3, bottom=0.8))
    vc = vf + 1.8
    half = hw + 0.5
    rise = 2.6
    R = (half * half + rise * rise) / (2 * rise)
    cy = vc + rise - R
    seg = circle((0.0, cy), R, 96) ^ rect(-half, vc - 0.01, half, vc + rise + 1)
    inner = circle((0.0, cy), R - 1.1, 96) ^ rect(-half + 1.0, vc + 0.9, half - 1.0, vc + rise + 1)
    parts.append(MD.run(-half - 0.3, half + 0.3, vc + 1.0, MD.CROWN, 1.0, up=False))
    parts.append(ext(seg - inner, 0.0, 1.1))
    parts.append(ext(inner, 0.0, 0.5))
    top = vc + rise
    sw = w / 2 + A + 0.4
    parts.append(MD.run(-sw, sw, 0.0, MD.SILL, 1.0, up=False))
    return O._one_piece(sash, parts, op, plug_cs, O.PLUG, top, -1.0)


def window_rosettecap(w, h, A=1.0, L_=0.8):
    """A Tidewater upper window: a nine-over-six sash in an architrave lugged out at both
    bottom corners, under a cap: a frieze carved with a rosette at its centre and a moulded
    cornice."""
    sash, op, plug_cs = _sash_pair(w, h, cols=3, rows=(3, 2))
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS)]
    band = (op.offset(A, JoinType.Miter, 4.0) - op) ^ rect(-w, 0.0, w, h + A)
    lugs = cs_union([rect(-w / 2 - A - L_, -1.0, -w / 2 - A + 0.01, 1.6), rect(w / 2 + A - 0.01, -1.0, w / 2 + A + L_, 1.6)])
    parts.append(ext(band + lugs, 0.0, 0.7))
    hw = w / 2 + A
    vf = h + A
    parts.append(ext(rect(-hw, vf - 0.01, hw, vf + 2.2), 0.0, 0.55))
    ros = cs_union([circle((0.62 * math.cos(a), vf + 1.1 + 0.62 * math.sin(a)), 0.4, 12) for a in np.linspace(0, 2 * math.pi, 6, endpoint=False)])
    parts.append(ext(ros + circle((0.0, vf + 1.1), 0.42, 14), 0.54, 0.9))
    top = vf + 2.0 + 1.2
    parts.append(MD.run(-hw - 0.6, hw + 0.6, top, MD.CROWN, 1.2, up=False))
    sw = w / 2 + A + L_
    parts.append(MD.run(-sw, sw, 0.0, MD.SILL, 1.0, up=False))
    return O._one_piece(sash, parts, op, plug_cs, O.PLUG, top, -1.0)


def door_doric(w, h, transom=3.6, A=1.0, back=False):
    """A Tidewater frontispiece: a six-panel door under a four-light transom between Doric
    pilasters that carry an entablature with a triglyph frieze (guttae under each triglyph)
    and a triangular pediment with an oval patera in it. ``back``: the entablature alone,
    without pilasters or pediment."""
    H = h + transom
    op = rect(-w / 2, 0.0, w / 2, H)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    u0, u1 = -w / 2 + O.CLR + 0.3, w / 2 - O.CLR - 0.3
    body = [ext(plug_cs, -pl, -1.0), ext(rect(u0, 0.5, u1, h - 0.3), -1.0, -0.8)]
    cw = (u1 - u0 - 1.8) / 2
    for c in range(2):
        pa = u0 + 0.6 + c * (cw + 0.6)
        for vb, vt in ((1.0, h * 0.28), (h * 0.28 + 0.8, h * 0.46), (h * 0.46 + 0.8, h - 1.1)):
            body.append(_panel(rect(pa, vb, pa + cw, vt)))
    g = plug_cs.offset(-0.5, JoinType.Miter, 4.0) ^ rect(-w, h + 0.3, w, H + 2)
    sash = _glazed(body, g, pl, _muntins(g, 4, 1), plug_cs)
    sash.append(ext(rect(-w, h - 0.3, w, h + 0.3) ^ plug_cs, -pl, -0.4))
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS),
             ext((op.offset(A, JoinType.Miter, 4.0) - op) ^ rect(-w, 0.0, w, H + A), 0.0, 0.7)]
    ve = H + A - 0.2
    if back:
        half = w / 2 + A + 0.3
        ent, top = _entablature(half, ve)
        parts += ent
        return O._one_piece(sash, parts, op, plug_cs, pl, top, 0.0)
    pw = 1.8
    for sg in (-1, 1):
        uc = sg * (w / 2 + A - 0.2 + pw / 2)
        parts.append(chamfer_box(uc - pw / 2 - 0.35, 0.0, uc + pw / 2 + 0.35, 1.8, 0.0, 1.4, c=0.3, bottom=0.0))
        parts.append(ext(rect(uc - pw / 2, 1.79, uc + pw / 2, ve - 0.8), 0.0, 1.0))
        parts.append(chamfer_box(uc - pw / 2 - 0.3, ve - 0.81, uc + pw / 2 + 0.3, ve, 0.0, 1.25, c=0.35))
    half = w / 2 + A - 0.2 + pw + 0.3
    parts.append(ext(rect(-half, ve - 0.01, half, ve + 0.9), 0.0, 1.0))                   # architrave
    vf0, vf1 = ve + 0.9, ve + 3.0
    parts.append(ext(rect(-half, vf0 - 0.01, half, vf1 + 0.2), 0.0, 0.8))               # frieze
    n = max(3, int(round(2 * half / 3.4)))
    trig = []
    for j in range(n):
        x = -half + 0.9 + (2 * half - 1.8) * j / (n - 1)
        tg = rect(x - 0.7, vf0 + 0.1, x + 0.7, vf1)
        trig.append(ext(tg, 0.79, 1.15) - ext(cs_union([rect(x - 0.35, vf0 + 0.5, x - 0.1, vf1 - 0.2),
                                                       rect(x + 0.1, vf0 + 0.5, x + 0.35, vf1 - 0.2)]), 0.95, 1.3))
        trig.append(ext(cs_union([rect(x - 0.6 + 0.4 * i, ve + 0.3, x - 0.3 + 0.4 * i, ve + 0.9) for i in range(3)]), 0.99, 1.2))
    parts += trig
    vc = vf1 + 1.2 + 0.2
    parts.append(MD.run(-half - 0.6, half + 0.6, vc, MD.CROWN, 1.2, up=False))
    hp = (half + 0.6) * 0.4
    tri = poly([(-half - 0.6, vc - 0.4), (half + 0.6, vc - 0.4), (0.0, vc + hp)])
    inner = tri.offset(-1.1, JoinType.Miter, 4.0)
    parts.append(ext(tri - inner, 0.0, 1.2))
    parts.append(ext(inner, 0.0, 0.5))
    pat = oval((0.0, vc + hp * 0.33), 1.3, 0.8, 24)
    parts.append(ext(pat - oval((0.0, vc + hp * 0.33), 0.8, 0.4, 20), 0.49, 0.95))
    return O._one_piece(sash, parts, op, plug_cs, pl, vc + hp, 0.0)


# ------------------------------------------------------------------ dormer and chimneys
def dormer_jerkin(w=13.0, dep=18.0, hwall=12.0, clip=0.62):
    """A Tidewater dormer: a gabled front whose apex is clipped (a jerkinhead like the main
    roof), corner boards, a six-over-six sash under a flat head board and a narrow sill.
    Local as colonial.dormer_pedimented; returns (body, core, face)."""
    rise = w / 2
    zc = hwall + rise * clip
    xc = w / 2 * (1 - clip)
    face = poly([(-w / 2, 0.0), (w / 2, 0.0), (w / 2, hwall), (xc, zc), (-xc, zc), (-w / 2, hwall)])
    body = ext(face, -dep, 0.0) - ext(face.offset(-1.2, JoinType.Miter, 4.0) ^ rect(-50, 1.2, 50, 99), -dep - 1, -1.2)
    lw = w * 0.5
    light = rect(-lw / 2, 2.2, lw / 2, hwall - 0.8)
    body = body - ext(light, -1.3, 1.0)
    inner = light.offset(-0.4, JoinType.Miter, 4.0)
    u0_, v0_, u1_, v1_ = inner.bounds()
    vm = (v0_ + v1_) / 2
    bars = _muntins(rect(u0_, v0_, u1_, vm), 3, 2) + _muntins(rect(u0_, vm, u1_, v1_), 3, 2) + rect(u0_, vm - 0.3, u1_, vm + 0.3)
    body = body + ext((light - inner) + (bars ^ inner), -1.2, -0.5)
    body = body + ext((light.offset(0.8, JoinType.Miter, 4.0) - light) ^ rect(-w, 2.2, w, hwall + 1), -0.01, 0.6)
    body = body + chamfer_box(-lw / 2 - 1.0, 1.4, lw / 2 + 1.0, 2.2, -0.01, 0.9, c=0.3, bottom=0.9)
    body = body + ext(rect(-lw / 2 - 1.2, hwall - 0.8, lw / 2 + 1.2, hwall + 0.4), -0.01, 0.8)
    for sg in (-1, 1):
        body = body + ext(rect(sg * (w / 2) - (1.0 if sg > 0 else 0.0), 1.2, sg * (w / 2) + (0.0 if sg > 0 else 1.0), hwall),
                          -0.01, 0.5)
    core = ext(face.offset(-1.2, JoinType.Miter, 4.0) ^ rect(-50, 1.2, 50, hwall), -dep + 1.2, -1.2)
    return body, core, face


def dormer_jerkin_roof(w, dep, hwall, clip=0.62, over=1.4, s_end=1.8, t=1.2):
    """The dormer's own little jerkinhead roof, in the dormer frame (u across, v up, w out):
    two slopes over the cheeks, clipped at the front by a steep hip. Its underside follows
    the dormer's gable (a plain shell ``t`` thick)."""
    rise = w / 2
    ez = hwall - over
    outer = poly([(-w / 2 - over, ez), (0.0, hwall + rise + over * 0.8), (w / 2 + over, ez)])
    inner = poly([(-w / 2, ez - 1.0), (w / 2, ez - 1.0), (w / 2, hwall), (0.0, hwall + rise), (-w / 2, hwall)])
    shell = ext(outer, -dep - 6.0, over) - ext(inner, -dep - 10.0, over + 1.0)
    zc = hwall + rise * clip
    # the clip: a plane through the front edge (w = over) at zc, rising back into the roof
    n = np.array([0.0, 1.0, s_end])
    n = n / np.linalg.norm(n)
    p = np.array([0.0, zc, over])
    return shell.trim_by_plane(list(-n), float(-n @ p))


def chimney_cluster(s=17.0, st=5.4, h=30.0):
    """A Stratford chimney cluster: four square stacks of English-bond brick at the corners
    of a square, joined near the top on every side by an arch, all under one corbelled cap
    with a flue in each stack."""
    h = round(h / 0.2) * 0.2
    o = s / 2 - st / 2
    za, zt = h - 8.0, h - 3.0
    parts = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(box([sx * o - st / 2, sy * o - st / 2, 0.0], [sx * o + st / 2, sy * o + st / 2, zt]))
            parts.append(TW._skin(st, st, 0.0, zt - 0.2, TW._brick("english")).translate([sx * o, sy * o, 0.0]))
    gap = s - 2 * st
    for axis in (0, 1):
        for sg in (-1, 1):
            a = cs_union([rect(-gap / 2 - 0.3, za, gap / 2 + 0.3, zt)]) - cs_union([rect(-gap / 2, za - 1, gap / 2, za + 1.0),
                                                                                  circle((0.0, za + 1.0), gap / 2, 32)])
            wall = M.extrude(a, 1.6).translate([0, 0, -0.8])
            if axis == 0:
                wall = wall.transform(np.array([[1.0, 0, 0, 0], [0, 0, 1.0, sg * (s / 2 - 0.8)], [0, 1.0, 0, 0]]))
            else:
                wall = wall.transform(np.array([[0, 0, 1.0, sg * (s / 2 - 0.8)], [1.0, 0, 0, 0], [0, 1.0, 0, 0]]))
            parts.append(wall)
    z = zt
    for k in range(3):
        g = 0.3 * (k + 1)
        parts.append(box([-s / 2 - g, -s / 2 - g, z - 0.01], [s / 2 + g, s / 2 + g, z + 0.6]))
        z += 0.6
    parts.append(box([-s / 2 - 0.9, -s / 2 - 0.9, z - 0.01], [s / 2 + 0.9, s / 2 + 0.9, z + 0.8]))
    body = union(parts)
    flues = union([box([sx * o - 1.2, sy * o - 1.2, zt - 4.0], [sx * o + 1.2, sy * o + 1.2, h + 5]) for sx in (-1, 1) for sy in (-1, 1)])
    hollow = box([-o + st / 2, -o + st / 2, zt - 0.01], [o - st / 2, o - st / 2, h + 5])        # open between the stacks, above the arches
    return body - flues - hollow


# ------------------------------------------------------------------ the portico
def post_virginian(h, collar=None, abacus=3.2, slot=(1.2, 1.0)):
    """A Roman Doric column: a torus on a plinth, a plain shaft with a strong entasis, a
    necking band between two astragals and a deep echinus under a square abacus (the
    Randolph's portico)."""
    z1 = h - 3.0
    r = 1.3
    prof = [(0.0, 1.19), (1.65, 1.19), (1.65, 1.45), (1.5, 1.65), (r, 1.85), (r * 1.02, z1 * 0.3), (r * 0.84, z1),
            (1.2, z1 + 0.2), (1.2, z1 + 0.4), (r * 0.84, z1 + 0.6), (r * 0.84, z1 + 1.2), (1.2, z1 + 1.4), (1.2, z1 + 1.6),
            (r * 0.84, z1 + 1.8)]
    body = PW._revolve(prof, 32) + PW._plinth(3.3)
    return body + PW._top(h, abacus / 2, z1 + 1.8, r * 0.84, slot, seg=32)


def baluster_doublevase(h):
    """A baluster turned as two vases stacked neck to neck, between square blocks (the
    Randolph)."""
    top = h - 0.5
    m = 0.5 + (top - 0.5) / 2
    prof = [(0.0, 0.5), (0.3, 0.5), (0.5, 0.5 + (m - 0.5) * 0.45), (0.28, m - 0.25), (0.4, m), (0.28, m + 0.25),
            (0.5, m + (top - m) * 0.55), (0.3, top)]
    return PW._revolve(prof, 16) + box([-0.55, -0.55, 0.0], [0.55, 0.55, 0.51]) + box([-0.55, -0.55, top - 0.01], [0.55, 0.55, h])


def frieze_doric(u0, u1, v_bot, v_top):
    """A portico entablature: a triglyph frieze (each triglyph with two grooves between its
    three bars) over a plain architrave with a fillet."""
    v0 = v_top - 2.2
    board = rect(u0, v0, u1, v_top + 0.05)
    n = max(2, int((u1 - u0) / 3.0))
    grooves = []
    for j in range(n):
        x = u0 + (u1 - u0) * (j + 0.5) / n
        grooves += [rect(x - 0.45, v0 + 0.9, x - 0.15, v_top - 0.3), rect(x + 0.15, v0 + 0.9, x + 0.45, v_top - 0.3)]
    return (board - cs_union(grooves)) + rect(u0, v0 - 0.4, u1, v0 + 0.6)


def edge_mutules(L, z0, zc):
    """Portico fascia (the Randolph): flat mutule blocks hung under the crown."""
    xs = np.arange(1.2, L - 0.8, 2.4)
    blocks = [rect(x - 0.6, zc - 1.2, x + 0.6, zc - 0.2) for x in xs]
    return cs_union(blocks) + rect(0.3, zc - 0.45, L - 0.3, zc), 0.5


def skirt_lozenges(reg, d=1.2):
    """Portico skirt (the Randolph): a board with a row of raised lozenges."""
    u0, v0, u1, v1 = reg.bounds()
    out = M.extrude(reg, d * 0.55)
    if v1 - v0 < 1.6:
        return out
    n = max(1, int((u1 - u0) / 3.0))
    lz = []
    for j in range(n):
        x = u0 + (u1 - u0) * (j + 0.5) / n
        vm, hv = (v0 + v1) / 2, (v1 - v0) / 2 - 0.4
        lz.append(poly([(x - 1.1, vm), (x, vm + hv), (x + 1.1, vm), (x, vm - hv)]))
    return out + M.extrude(cs_union(lz) ^ reg, d)


PW.POSTS.update(virginian=post_virginian)
PW.BALUSTERS.update(doublevase=(baluster_doublevase, 1.7))
PW.FRIEZES.update(doricfrieze=frieze_doric)
PW.SKIRTS.update(lozenges=skirt_lozenges)
_FT.EDGE_EXTRA.update(mutules=edge_mutules)


# ================================================================== the Stauffer (house 45, Pennsylvania German)
# ------------------------------------------------------------------ skins and foundation
def limestone_random(region, datum=0.0, seed=3):
    """Whitewashed limestone in random ashlar: squared stones of three heights in broken
    courses, a tall 'jumper' now and then running through two, the joints struck back."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    rng = np.random.default_rng(seed)
    joint = 0.45
    stones = []
    v = v0 - 1.0
    while v < v1:
        ch = float(rng.choice([1.8, 2.4, 3.0]))                     # each course its own height (broken courses)
        u = u0 - rng.uniform(0.0, 4.0)
        while u < u1:
            L = rng.uniform(2.6, 6.5)
            stones.append(rect(u + joint / 2, v + joint / 2, u + L - joint / 2, v + ch - joint / 2))
            u += L
        v += ch
    cs = cs_union(stones) ^ region
    return M.extrude(region, 0.08) + ext(cs, 0.0, 0.4)


def logs_dovetail(region, L, datum=0.0, course=2.6, chink=0.6, end=2.8):
    """Hewn logs with lime chinking: squared logs 2.6 mm high, their faces broad-axed flat and
    their edges rounded, the chinking set back between them; at both corners the log ends
    show in turn, each cut to a dovetail."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    out = [M.extrude(region, 0.1)]
    logs, ends = [], []
    k = math.floor((v0 - datum) / course) - 1
    while datum + k * course < v1:
        v = datum + k * course
        a, b = v + chink / 2, v + course - chink / 2
        logs.append(rect(u0 - 1, a, u1 + 1, b))
        if k % 2 == 0:
            for x0, sg in ((0.0, 1.0), (L, -1.0)):
                tail = poly([(x0, a - 0.1), (x0 + sg * end, a + 0.25), (x0 + sg * end, b - 0.25), (x0, b + 0.1)])
                ends.append(tail)
        k += 1
    lc = cs_union(logs) ^ region
    out.append(stepped(lc, [(0.0, 0.0, 0.35), (0.25, 0.35, 0.55)]))
    if ends:
        out.append(ext(cs_union(ends) ^ region, 0.0, 0.7))
    return union(out)


def boards_pointed(region, datum=0.0, w=2.0):
    """Gable boarding: upright boards with a V-joint between them, their feet cut to points
    along the gable's foot (a sawtooth hem)."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    bd = []
    for x in np.arange(u0 - w, u1 + w, w):
        bd.append(poly([(x + 0.2, v0 + 1.2), (x + w / 2, v0 + 0.1), (x + w - 0.2, v0 + 1.2), (x + w - 0.2, v1 + 1), (x + 0.2, v1 + 1)]))
    return M.extrude(region, 0.1) + ext(cs_union(bd) ^ region, 0.0, 0.45)


def foundation_stoneplinth(reg, seed=0):
    """A plinth of big squared sandstones with a chamfered top course (the Stauffer)."""
    b = reg.bounds()
    rng = np.random.default_rng(seed + 11)
    st_ = []
    u = b[0] - rng.uniform(0, 3)
    while u < b[2]:
        L = rng.uniform(5.0, 9.0)
        st_.append(rect(u + 0.25, b[1] - 1, u + L - 0.25, b[3] - 1.4))
        u += L
    body = ext(cs_union(st_) ^ reg, 0.0, 0.45) + M.extrude(reg, 0.1)
    return body + chamfer_box(b[0], b[3] - 1.4, b[2], b[3], 0.0, 0.8, c=0.45, square=("u0", "u1"), bottom=0.3)


# ------------------------------------------------------------------ cornice ornament
def _tulip(c, s):
    """A fraktur tulip ``s`` tall: a cup of three pointed petals (the middle one tallest) on a
    stem, two long leaves rising from its foot in a V."""
    x, y = c
    y0, top = y - s * 0.5, y + s * 0.5
    cb, cw = y + s * 0.02, s * 0.3
    cup = poly([(x - cw * 0.55, cb), (x + cw * 0.55, cb), (x + cw, cb + s * 0.22), (x + cw * 0.85, top - s * 0.06),
                (x + cw * 0.35, top - s * 0.2), (x, top), (x - cw * 0.35, top - s * 0.2), (x - cw * 0.85, top - s * 0.06),
                (x - cw, cb + s * 0.22)])
    stem = rect(x - 0.2, y0, x + 0.2, cb + 0.1)
    lv = [_lens((x + sg * s * 0.14, y0 + s * 0.26), s * 0.5, s * 0.13, math.radians(68 if sg > 0 else 112)) for sg in (-1, 1)]
    return cs_union([cup, stem] + lv)


def frieze_tulippots(L, h, b, pitch, margin, pair, half):
    """Pennsylvania German tulip pots: at every station a pot sprouting three tulips, and in
    each bay a small heart."""
    v0, v1 = 0.8, h - 0.8
    hh = v1 - v0
    vm = (v0 + v1) / 2
    out = []
    for u in CO._us(L, pitch, margin, 0.0):
        pot = poly([(u - 0.9, v0), (u + 0.9, v0), (u + 1.2, v0 + hh * 0.3), (u - 1.2, v0 + hh * 0.3)])
        fl = [_tulip((u, v0 + hh * 0.62), hh * 0.62)]
        fl += [_tulip((u + sg * 1.5, v0 + hh * 0.52), hh * 0.46) for sg in (-1, 1)]
        out.append(_st(pot, b, 0.55))
        out.append(_st(cs_union(fl) ^ rect(u - 2.6, v0 + hh * 0.3 - 0.1, u + 2.6, v1 + 0.2), b, 0.45))
    for uc, wd in CO._between(L, pitch, margin, pair, half + 2.8):
        r = min(0.55, hh * 0.18)
        heart = cs_union([circle((uc - r * 0.72, vm + r * 0.45), r, 16), circle((uc + r * 0.72, vm + r * 0.45), r, 16),
                          poly([(uc - r * 1.62, vm + 0.2), (uc + r * 1.62, vm + 0.2), (uc, vm - r * 1.9)])])
        out.append(_st(heart, b, 0.45))
    return out, []


def _bird(c, s, sg):
    """A distelfink (goldfinch) ``s`` long, facing +u (sg = 1) or -u: body, head, tail, wing."""
    x, y = c
    body = oval((x, y), s * 0.32, s * 0.2, 20)
    head = circle((x + sg * s * 0.34, y + s * 0.13), s * 0.13, 14)
    beak = poly([(x + sg * s * 0.44, y + s * 0.16), (x + sg * s * 0.58, y + s * 0.1), (x + sg * s * 0.44, y + s * 0.07)])
    tail = poly([(x - sg * s * 0.22, y), (x - sg * s * 0.55, y + s * 0.22), (x - sg * s * 0.5, y - s * 0.02)])
    return cs_union([body, head, beak, tail])


def frieze_distelfinks(L, h, b, pitch, margin, pair, half):
    """Distelfinks: at every station a pair of goldfinches facing each other over a heart, and
    a running vine of little leaves between the pairs."""
    v0, v1 = 0.8, h - 0.8
    hh = v1 - v0
    vm = (v0 + v1) / 2
    out = []
    s = min(3.2, hh * 1.0)
    for u in CO._us(L, pitch, margin, 0.0):
        birds = cs_union([_bird((u - s * 0.7, vm + 0.1), s, 1), _bird((u + s * 0.7, vm + 0.1), s, -1)])
        out.append(_st(birds ^ rect(u - 2.4 * s, v0 - 0.2, u + 2.4 * s, v1 + 0.2), b, 0.5))
        r = 0.42
        heart = cs_union([circle((u - r * 0.72, vm + r * 0.45 - 0.3), r, 14), circle((u + r * 0.72, vm + r * 0.45 - 0.3), r, 14),
                          poly([(u - r * 1.62, vm - 0.1), (u + r * 1.62, vm - 0.1), (u, vm - r * 1.9 - 0.3)])])
        out.append(_st(heart, b, 0.6))
    for uc, wd in CO._between(L, pitch, margin, pair, half + 1.5 * s):
        a, e = uc - wd / 2 + 0.3, uc + wd / 2 - 0.3
        if e - a < 2.0:
            continue
        out.append(_st(rect(a, vm - 0.2, e, vm + 0.2), b, 0.3))
        for j, x in enumerate(np.arange(a + 0.8, e - 0.4, 1.4)):
            out.append(_st(_lens((x, vm + (0.45 if j % 2 else -0.45)), 1.1, 0.55, math.radians(35 if j % 2 else -35)), b, 0.4))
    return out, []


def course_saltires(L, h, b, pitch, margin, p):
    """A course of small saltire crosses, one after another."""
    step = 1.6
    n = int((L - 1.0) / step)
    u0 = (L - (n - 1) * step) / 2
    out = []
    hr = h / 2 - 0.1
    for k in range(n):
        u = u0 + k * step
        x = stroke([(u - 0.55, h / 2 - hr), (u + 0.55, h / 2 + hr)], 0.4) + stroke([(u - 0.55, h / 2 + hr), (u + 0.55, h / 2 - hr)], 0.4)
        out.append(ext(x ^ rect(u - 0.8, 0.05, u + 0.8, h - 0.05), b - 0.05, b + 0.45))
    return out


def bracket_heart(h, d, t):
    """A sawn bracket whose nose ends in a heart-shaped drop (side profile, top at v = 0)."""
    hb = min(h, max(1.8, 0.34 * d))
    r = min(0.55, hb * 0.28)
    x = d - r * 1.4
    body = poly([(0.0, 0.0), (d, 0.0), (d, -0.5), (x + r * 1.2, -hb + r * 1.4), (0.0, -hb)])
    heart = cs_union([circle((x - r * 0.7, -hb + r * 1.25), r, 14), circle((x + r * 0.7, -hb + r * 1.25), r, 14),
                      poly([(x - r * 1.6, -hb + r * 1.1), (x + r * 1.6, -hb + r * 1.1), (x, -hb - r * 0.6)])])
    return cs_union([body, heart])


CO.FRIEZE_EXTRA.update(tulippots=frieze_tulippots, distelfinks=frieze_distelfinks)
CO.COURSE_EXTRA.update(saltires=course_saltires)
TW.BRACKET_EXTRA.update(heart=bracket_heart)
TW.FOUNDATION_EXTRA.update(stoneplinth=foundation_stoneplinth)


# ------------------------------------------------------------------ windows, doors, shutters
def window_pegframe(w, h, A=1.4):
    """A window in the stone storey: a six-over-six sash in a heavy plank frame whose corners
    are pinned with square pegs, under a dressed sandstone lintel with a raised keystone
    carved with a heart, over a stone sill."""
    sash, op, plug_cs = _sash_pair(w, h, cols=3, rows=(2, 2))
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS)]
    frame_ = (op.offset(A, JoinType.Miter, 4.0) - op) ^ rect(-w, 0.0, w, h + A)
    parts.append(ext(frame_, 0.0, 0.8))
    for x in (-w / 2 - A / 2, w / 2 + A / 2):
        for v in (0.8, h + A / 2):
            parts.append(ext(rect(x - 0.3, v - 0.3, x + 0.3, v + 0.3), 0.79, 1.1))
    lt0 = h + A
    hw = w / 2 + A + 1.2
    parts.append(chamfer_box(-hw, lt0 - 0.01, hw, lt0 + 2.6, 0.0, 1.0, c=0.3))
    r = 0.42
    heart = cs_union([circle((-r * 0.72, lt0 + 1.45 + r * 0.45), r, 14), circle((r * 0.72, lt0 + 1.45 + r * 0.45), r, 14),
                      poly([(-r * 1.62, lt0 + 1.65), (r * 1.62, lt0 + 1.65), (0.0, lt0 + 1.45 - r * 1.9)])])
    parts.append(chamfer_box(-1.2, lt0 - 0.01, 1.2, lt0 + 3.0, 0.0, 1.35, c=0.3))
    parts.append(ext(heart, 1.34, 1.6))
    top = lt0 + 3.0
    parts.append(chamfer_box(-hw, -1.2, hw, 0.2, 0.0, 1.1, c=0.35, bottom=0.6))
    return O._one_piece(sash, parts, op, plug_cs, O.PLUG, top, -1.2)


def window_casement_tulip(w, h, A=1.2):
    """A window in the log storey: a pair of casements of three lights each in a hewn frame,
    under a head board sawn along its lower edge in a wave and carved with a tulip."""
    op = O.opening_cs(w, h, 0)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    inner = plug_cs.offset(-0.6, JoinType.Miter, 4.0)
    u0_, v0_, u1_, v1_ = inner.bounds()
    leaves = [rect(u0_, v0_, -0.3, v1_), rect(0.3, v0_, u1_, v1_)]
    g = cs_union(leaves)
    bars = cs_union([_muntins(l_, 1, 3) for l_ in leaves])
    sash = _glazed([ext(plug_cs, -pl, -0.6)], g, pl, bars, plug_cs)
    sash.append(ext(rect(-0.31, v0_ - 0.01, 0.31, v1_ + 0.01), -pl, -0.3))
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS)]
    parts.append(ext((op.offset(A, JoinType.Miter, 4.0) - op) ^ rect(-w, 0.0, w, h + A), 0.0, 0.8))
    hw = w / 2 + A + 0.8
    vb = h + A - 0.01
    wave = [(-hw, vb + 0.6)] + [(x, vb + 0.6 + 0.35 * math.cos(2 * math.pi * x / 2.4)) for x in np.linspace(-hw, hw, 25)] + [(hw, vb + 0.6)]
    board = poly(wave + [(hw, vb + 3.4), (-hw, vb + 3.4)]) + rect(-hw, vb, hw, vb + 0.7)
    parts.append(ext(board, 0.0, 0.7))
    parts.append(ext(_tulip((0.0, vb + 2.0), 2.2), 0.69, 1.0))
    top = vb + 3.4
    parts.append(chamfer_box(-w / 2 - A - 0.4, -1.0, w / 2 + A + 0.4, 0.2, 0.0, 1.0, c=0.3, bottom=0.6))
    return O._one_piece(sash, parts, op, plug_cs, pl, top, -1.0)


def _board_leaf(u0, u1, v0, v1, hinges=True, battens=True):
    """A leaf of upright V-jointed boards with strap hinges ending in tulip-shaped spears."""
    from .colonial import _strap
    face = rect(u0, v0, u1, v1)
    body = ext(face, -1.0, -0.8)
    grooves = cs_union([rect(x - 0.18, v0, x + 0.18, v1) for x in np.arange(u0 + 1.4, u1 - 0.4, 1.4)])
    body = body - ext(grooves ^ face, -0.9, -0.7)
    out = [body]
    if hinges:
        for v in (v0 + (v1 - v0) * 0.18, v1 - (v1 - v0) * 0.18):
            out.append(ext(_strap(u0 + 0.3, u0 + (u1 - u0) * 0.8, v) ^ face, -0.81, -0.55))
    return out


def door_forebay(w, h, transom=3.0, A=1.3):
    """The front door under the forebay: a Dutch door (split at the middle) of upright boards
    on tulip-ended strap hinges, a carved transom board with a heart between two tulips, in a
    heavy pegged frame."""
    H = h + transom
    op = rect(-w / 2, 0.0, w / 2, H)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    u0, u1 = -w / 2 + O.CLR + 0.3, w / 2 - O.CLR - 0.3
    vm = round(h * 0.52 / 0.2) * 0.2
    body = [ext(plug_cs, -pl, -1.0)]
    body += _board_leaf(u0, u1, 0.5, vm - 0.2)
    body += _board_leaf(u0, u1, vm + 0.2, h - 0.3)
    body.append(ext(rect(u0, vm - 0.5, u1 + 0.3, vm + 0.5), -0.8, -0.4))                  # the lower leaf's shelf
    tb = rect(u0, h + 0.2, u1, H - O.CLR - 0.3)
    body.append(ext(tb, -1.0, -0.8))
    orn = cs_union([_tulip((sg * (w * 0.3), h + transom / 2 - 0.1), transom * 0.8) for sg in (-1, 1)])
    r = 0.42
    heart = cs_union([circle((-r * 0.72, h + transom / 2 + r * 0.45), r, 14), circle((r * 0.72, h + transom / 2 + r * 0.45), r, 14),
                      poly([(-r * 1.62, h + transom / 2 + 0.2), (r * 1.62, h + transom / 2 + 0.2), (0.0, h + transom / 2 - r * 1.9)])])
    body.append(ext((orn + heart) ^ tb, -0.81, -0.55))
    body.append(ext(plug_cs - plug_cs.offset(-0.5, JoinType.Miter, 4.0), -pl, 0.0))
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS),
             ext((op.offset(A, JoinType.Miter, 4.0) - op) ^ rect(-w, 0.0, w, H + A), 0.0, 0.9)]
    for x in (-w / 2 - A / 2, w / 2 + A / 2):
        for v in (h * 0.3, h * 0.7, H + A / 2):
            parts.append(ext(rect(x - 0.3, v - 0.3, x + 0.3, v + 0.3), 0.89, 1.2))
    return O._one_piece(body, parts, op, plug_cs, pl, H + A, 0.0)


def door_bonnet(w, h, A=1.1):
    """The side door: a board door on strap hinges under a bonnet hood: a little barrel roof of
    boards, its front a segmental arch, carried on two sawn brackets."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    u0, u1 = -w / 2 + O.CLR + 0.3, w / 2 - O.CLR - 0.3
    body = [ext(plug_cs, -pl, -1.0)] + _board_leaf(u0, u1, 0.5, h - 0.3)
    body.append(ext(plug_cs - plug_cs.offset(-0.5, JoinType.Miter, 4.0), -pl, 0.0))
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS),
             ext((op.offset(A, JoinType.Miter, 4.0) - op) ^ rect(-w, 0.0, w, h + A), 0.0, 0.8)]
    hw = w / 2 + A + 1.6
    vb = h + A
    dep = 5.0
    rise = 2.6
    R = (hw * hw + rise * rise) / (2 * rise)
    cy = vb + rise - R
    seg = circle((0.0, cy), R, 96) ^ rect(-hw, vb, hw, vb + rise + 1)
    shell = seg - (circle((0.0, cy), R - 1.0, 96) ^ rect(-hw + 1.0, vb - 1, hw - 1.0, vb + rise + 1))
    parts.append(ext(shell, 0.0, dep))
    parts.append(ext(seg, 0.0, 0.8))
    parts.append(ext(rect(-hw - 0.2, vb - 0.6, hw + 0.2, vb + 0.2), 0.0, dep + 0.2))                # the hood's sill board
    for sg in (-1, 1):
        x = sg * (hw - 0.5)
        br = poly([(-0.5, vb - 0.6), (0.5, vb - 0.6), (0.5, vb - 4.2)])
        pr = poly([(0.0, 0.0), (dep, 0.0), (dep - 0.6, -0.8)] + [(dep * (1 - s_) , -0.8 - 3.0 * math.sin(math.pi / 2 * s_)) for s_ in np.linspace(0.1, 1.0, 8)])
        side = M.extrude(pr, 1.0).translate([0, 0, -0.5])
        side = side.transform(np.array([[0, 0, 1.0, x], [0, 1.0, 0, vb - 0.6], [1.0, 0, 0, 0]]))
        parts.append(side)
    return O._one_piece(body, parts, op, plug_cs, pl, vb + rise, 0.0)


def shutter_tulip(w, h, t=0.8):
    """A board shutter with two battens, a tulip sawn through its upper half. Local frame as
    features.shutter (u 0..w, v 0..h, back at w = 0; face-up)."""
    body = ext(rect(0, 0, w, h), 0.0, 0.5)
    grooves = [rect(x - 0.18, -1, x + 0.18, h + 1) for x in np.arange(1.25, w - 0.4, 1.25)]
    if grooves:
        body = body - ext(cs_union(grooves), 0.32, 1.0)
    cut = _tulip((w / 2, h * 0.68), min(w * 0.8, h * 0.22)).offset(-0.1, JoinType.Round)
    body = body - ext(cut, -1.0, 2.0)
    v1, v2 = round(h * 0.14 / 0.2) * 0.2, round(h * 0.86 / 0.2) * 0.2
    bat = cs_union([rect(0.3, v1 - 0.5, w - 0.3, v1 + 0.5), rect(0.3, v2 - 0.5, w - 0.3, v2 + 0.5)])
    return body + ext(bat, 0.49, t)


# ------------------------------------------------------------------ chimney, hex sign, bake oven
def chimney_dogtooth(w=11.0, d=9.0, h=30.0):
    """A central stack of brick with a band of dogtooth bricks (set diagonally, points out)
    below a sandstone cap slab, three flues."""
    h = round(h / 0.2) * 0.2
    sh = h - 2.4
    body = box([-w / 2, -d / 2, 0.0], [w / 2, d / 2, sh]) + TW._skin(w, d, 0.0, sh - 3.2, TW._brick("flemish"))
    zb = sh - 3.0
    teeth = []
    for axis, L_, D_ in ((0, w, d), (1, d, w)):
        for sg in (-1, 1):
            for x in np.arange(-L_ / 2 + 0.6, L_ / 2 - 0.4, 1.0):
                pts = [(x - 0.45, sg * D_ / 2 - sg * 0.01), (x, sg * (D_ / 2 + 0.55)), (x + 0.45, sg * D_ / 2 - sg * 0.01)]
                pr = poly(pts if sg > 0 else pts[::-1])
                m = M.extrude(pr, 1.0).translate([0, 0, zb])
                if axis == 1:
                    m = m.transform(np.array([[0, 1.0, 0, 0], [1.0, 0, 0, 0], [0, 0, 1.0, 0]]))
                teeth.append(m)
    body = body + union(teeth) + box([-w / 2 - 0.2, -d / 2 - 0.2, zb + 0.99], [w / 2 + 0.2, d / 2 + 0.2, zb + 1.6])
    body = body + box([-w / 2 - 1.0, -d / 2 - 1.0, sh - 0.01], [w / 2 + 1.0, d / 2 + 1.0, sh + 1.0])
    flues = union([box([x - 1.1, -1.1, sh - 4.0], [x + 1.1, 1.1, h + 5]) for x in (-w / 3.2, 0.0, w / 3.2)])
    return body - flues


def hex_sign(r=5.0, t=1.0):
    """A hex sign: a round plaque with a double rim and a six-petalled rosette (compass-drawn
    petals) inside, printed on its flat back."""
    disc = circle((0, 0), r, 64)
    body = ext(disc, 0.0, t * 0.6)
    rim = (disc - circle((0, 0), r - 0.6, 64)) + (circle((0, 0), r - 1.1, 64) - circle((0, 0), r - 1.6, 64))
    petals = cs_union([_lens((0.5 * (r - 1.9) * math.cos(a), 0.5 * (r - 1.9) * math.sin(a)), r - 1.9, (r - 1.9) * 0.36, a)
                       for a in np.linspace(0, 2 * math.pi, 6, endpoint=False)])
    return body + ext(rim, t * 0.59, t) + ext(petals, t * 0.59, t * 0.95)


def bakeoven(L=30.0, d=16.0, h=13.0, rise=8.0):
    """A bake oven built against a gable: a block of whitewashed stone with an arched oven
    mouth in its outer face under a sandstone lintel, a plinth, and its own little gabled roof
    (ridge running out from the wall, returned separately) with a stub flue at the wall.
    Local: x along the wall (centred), y out from the wall (0..d), z up. Returns (body, roof, flue)."""
    body = box([-L / 2, 0.0, 0.0], [L / 2, d, h])
    mouth = cs_union([rect(-3.0, 2.0, 3.0, 6.0), circle((0.0, 6.0), 3.0, 32) ^ rect(-4, 6.0, 4, 10)])
    body = body - M.extrude(mouth, 3.0).transform(np.array([[1.0, 0, 0, 0], [0, 0, -1.0, d + 1.0], [0, 1.0, 0, 0]]))
    body = body + box([-4.4, d - 0.01, 9.2], [4.4, d + 0.6, 10.4]) + box([-L / 2 - 0.4, -0.2, 0.0], [L / 2 + 0.4, d + 0.4, 1.2])
    tri = poly([(-L / 2 - 1.2, h), (L / 2 + 1.2, h), (L / 2 + 1.2, h + 0.6), (0.0, h + rise + 0.6), (-L / 2 - 1.2, h + 0.6)])
    roof = M.extrude(tri, d + 1.4).transform(np.array([[1.0, 0, 0, 0], [0, 0, 1.0, 0], [0, 1.0, 0, 0]]))
    flue = box([-1.8, 1.0, h], [1.8, 4.6, h + rise + 4.0])
    return body, roof - flue, flue


# ================================================================== the Porter (house 46, Connecticut River Valley)
# ------------------------------------------------------------------ skin and foundation
def clapboard_short(region, L, datum=0.0, course=1.8, seed=17, qtop=None):
    """Riven clapboards: short lengths of bevelled board, each course's joints lapped and
    staggered, between beaded corner boards (up to ``qtop``)."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    qtop = v1 if qtop is None else qtop
    cb = 1.9
    strips = cs_union([rect(-1, v0 - 1, cb, qtop), rect(L - cb, v0 - 1, L + 1, qtop)])
    field = region - strips
    out = _lap(field, course, [(0.0, 0.42), (0.25, 0.42), (course, 0.08)], datum)
    rng = np.random.default_rng(seed)
    joints = []
    k = math.floor((v0 - datum) / course) - 1
    while datum + k * course < v1:
        v = datum + k * course
        u = u0 - rng.uniform(0.0, 20.0)
        while u < u1:
            u += rng.uniform(16.0, 30.0)
            joints.append(poly([(u - 0.2, v), (u + 0.2, v), (u + 0.5, v + course), (u + 0.1, v + course)]))
        k += 1
    if joints:
        out = out - ext(cs_union(joints) ^ field, 0.12, 1.0)
    sreg = region ^ strips
    if not sreg.is_empty():
        out = out + ext(sreg, 0.0, 0.7)
        beads = cs_union([rect(cb - 0.5, v0 - 1, cb - 0.2, qtop), rect(L - cb + 0.2, v0 - 1, L - cb + 0.5, qtop)]) ^ sreg
        out = out - ext(beads, 0.45, 1.0)
    return out


def foundation_ribbon(reg, seed=0):
    """Random rubble laid up with ribbon pointing: irregular stones set back behind raised
    bands of mortar (the Porter)."""
    b = reg.bounds()
    rng = np.random.default_rng(seed + 23)
    gx, gy = 3.4, 2.6
    nx, ny = int((b[2] - b[0]) / gx) + 3, int((b[3] - b[1]) / gy) + 3
    P = [[(b[0] - gx + i * gx + rng.uniform(-0.9, 0.9) + (j % 2) * gx / 2, b[1] - gy + j * gy + rng.uniform(-0.6, 0.6))
          for i in range(nx)] for j in range(ny)]
    stones = []
    for j in range(ny - 1):
        for i in range(nx - 1):
            q = poly([P[j][i], P[j][i + 1], P[j + 1][i + 1], P[j + 1][i]])
            q = q.offset(-0.3, JoinType.Round)
            if not q.is_empty():
                stones.append(q)
    st_ = cs_union(stones) ^ reg
    mortar = reg - st_
    return M.extrude(reg, 0.1) + ext(st_, 0.0, 0.35) + ext(mortar, 0.0, 0.5)


# ------------------------------------------------------------------ cornice ornament
def _shell(c, s):
    """A scallop shell ``s`` wide, hinge down: a fan of ribs in a scalloped outline and two
    small ears at the hinge."""
    x, y = c
    R = s / 2
    fan = circle((x, y - R * 0.35), R, 40) ^ rect(x - R - 1, y - R * 0.35, x + R + 1, y + R)
    scal = cs_union([circle((x + R * 0.92 * math.cos(a), y - R * 0.35 + R * 0.92 * math.sin(a)), R * 0.2, 12)
                     for a in np.linspace(math.pi * 0.08, math.pi * 0.92, 6)])
    ribs = cs_union([stroke([(x, y - R * 0.35), (x + R * 0.95 * math.cos(a), y - R * 0.35 + R * 0.95 * math.sin(a))], 0.3)
                     for a in np.linspace(math.pi * 0.14, math.pi * 0.86, 5)])
    ears = cs_union([rect(x - R * 0.45, y - R * 0.55, x - R * 0.05, y - R * 0.3), rect(x + R * 0.05, y - R * 0.55, x + R * 0.45, y - R * 0.3)])
    return fan + scal + ears, ribs


def frieze_shells(L, h, b, pitch, margin, pair, half):
    """Scallop shells at the stations, each between two C-scrolls, and a sprig of three leaves
    in every bay."""
    v0, v1 = 0.8, h - 0.8
    hh = v1 - v0
    vm = (v0 + v1) / 2
    out = []
    for u in CO._us(L, pitch, margin, 0.0):
        body, ribs = _shell((u, vm), min(3.4, hh * 1.25))
        out.append(_st(body ^ rect(u - 2.6, v0 - 0.2, u + 2.6, v1 + 0.2), b, 0.4))
        out.append(_st(ribs ^ rect(u - 2.6, v0 - 0.2, u + 2.6, v1 + 0.2), b, 0.6))
        for sg in (-1, 1):
            cc = (u + sg * 2.6, vm)
            arc = [(cc[0] - sg * 0.8 * math.cos(a), cc[1] + 0.8 * math.sin(a)) for a in np.linspace(-math.pi / 2, math.pi / 2, 9)]
            out.append(_st(stroke(arc, 0.4) + circle((arc[0][0], arc[0][1] + 0.15), 0.35, 10), b, 0.45))
    for uc, wd in CO._between(L, pitch, margin, pair, half + 3.6):
        lv = cs_union([_lens((uc + 0.55 * math.cos(a), vm + 0.55 * math.sin(a)), 1.1, 0.5, a) for a in (math.pi / 2, math.pi / 6, 5 * math.pi / 6)])
        out.append(_st(lv, b, 0.4))
    return out, []


def frieze_pinecones(L, h, b, pitch, margin, pair, half):
    """New England pine: a pine cone hanging at every station between two sprays of needles,
    and a small cone in each bay."""
    v0, v1 = 0.8, h - 0.8
    hh = v1 - v0
    vm = (v0 + v1) / 2
    out = []

    def cone(c, s):
        x, y = c
        body = oval((x, y), s * 0.26, s * 0.46, 24)
        scales = cs_union([rect(x - s, y + dy - 0.14, x + s, y + dy + 0.14) for dy in np.arange(-s * 0.3, s * 0.35, s * 0.2)])
        return body - scales, rect(x - 0.18, y + s * 0.4, x + 0.18, v1)

    for u in CO._us(L, pitch, margin, 0.0):
        body, stem = cone((u, vm - 0.2), hh * 0.95)
        out.append(_st(body ^ rect(u - 2, v0 - 0.2, u + 2, v1 + 0.2), b, 0.55))
        out.append(_st(stem, b, 0.35))
        for sg in (-1, 1):
            base = (u + sg * 0.6, v1 - 0.4)
            needles = cs_union([stroke([base, (base[0] + sg * 2.6 * math.cos(a), base[1] - 2.6 * math.sin(a))], 0.3)
                                for a in np.linspace(0.15, 0.9, 5)])
            out.append(_st(needles ^ rect(u - 3.6, v0 - 0.2, u + 3.6, v1 + 0.2), b, 0.35))
    for uc, wd in CO._between(L, pitch, margin, pair, half + 3.6):
        body, stem = cone((uc, vm), hh * 0.6)
        out.append(_st(body, b, 0.45))
    return out, []


def course_coins(L, h, b, pitch, margin, p):
    """A coin (money) moulding: a row of discs, each overlapping the next."""
    r = min(0.62, h / 2 - 0.05)
    step = r * 1.55
    n = int((L - 1.0) / step)
    u0 = (L - (n - 1) * step) / 2
    out = []
    for k in range(n):
        u = u0 + k * step
        out.append(ext(circle((u, h / 2), r, 18), b - 0.05, b + (0.5 if k % 2 == 0 else 0.35)))
    return out


def bracket_doublescroll(h, d, t):
    """A modillion scrolled at both ends: a large volute at the wall rolling into a small one at
    the nose, like the Corinthian's (side profile, top at v = 0)."""
    hb = min(h, max(1.8, 0.34 * d))
    pts = [(0.0, 0.0), (d, 0.0), (d, -0.45)]
    for s in np.linspace(0.0, 1.0, 12):
        x = (d - 0.6) * (1.0 - s)
        pts.append((x, -0.45 - (hb - 0.45) * (s ** 1.5)))
    body = poly(pts)
    big = circle((hb * 0.45, -hb + hb * 0.45), hb * 0.45, 20)
    small = circle((d - 0.45, -0.75), 0.4, 14)
    return cs_union([body, big, small])


CO.FRIEZE_EXTRA.update(shells=frieze_shells, pinecones=frieze_pinecones)
CO.COURSE_EXTRA.update(coins=course_coins)
TW.BRACKET_EXTRA.update(doublescroll=bracket_doublescroll)
TW.FOUNDATION_EXTRA.update(ribbon=foundation_ribbon)


# ------------------------------------------------------------------ windows and door
def window_aedicule(w, h, A=0.8):
    """A Connecticut Valley lower window: a twelve-over-twelve sash in a thin architrave between
    two slim pilasters that carry a small entablature and a triangular pediment."""
    sash, op, plug_cs = _sash_pair(w, h, cols=3, rows=(4, 4))
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS),
             ext((op.offset(A, JoinType.Miter, 4.0) - op) ^ rect(-w, 0.0, w, h + A), 0.0, 0.6)]
    pw = 1.1
    for sg in (-1, 1):
        uc = sg * (w / 2 + A - 0.1 + pw / 2)
        parts.append(ext(rect(uc - pw / 2, 0.0, uc + pw / 2, h + A), 0.0, 0.9))
        parts.append(chamfer_box(uc - pw / 2 - 0.25, h + A - 0.8, uc + pw / 2 + 0.25, h + A + 0.01, 0.0, 1.1, c=0.3))
    half = w / 2 + A - 0.1 + pw + 0.25
    ve = h + A
    parts.append(ext(rect(-half, ve - 0.01, half, ve + 1.6), 0.0, 0.7))
    vc = ve + 1.4 + 0.9
    parts.append(MD.run(-half - 0.4, half + 0.4, vc, MD.CROWN, 0.9, up=False))
    hp = (half + 0.4) * 0.36
    tri = poly([(-half - 0.4, vc - 0.3), (half + 0.4, vc - 0.3), (0.0, vc + hp)])
    parts.append(ext(tri - tri.offset(-0.8, JoinType.Miter, 4.0), 0.0, 1.0))
    parts.append(ext(tri, 0.0, 0.45))
    sw = w / 2 + A + pw + 0.3
    parts.append(MD.run(-sw, sw, 0.0, MD.SILL, 1.0, up=False))
    return O._one_piece(sash, parts, op, plug_cs, O.PLUG, vc + hp, -1.0)


def window_bullseyecap(w, h, A=0.9):
    """A Connecticut Valley upper window: a twelve-over-eight sash in an architrave under a cap
    whose frieze carries three bull's-eyes (turned roundels) and a moulded cornice."""
    sash, op, plug_cs = _sash_pair(w, h, cols=3, rows=(4, 3))
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS),
             ext((op.offset(A, JoinType.Miter, 4.0) - op) ^ rect(-w, 0.0, w, h + A), 0.0, 0.7)]
    hw = w / 2 + A + 0.3
    vf = h + A
    parts.append(ext(rect(-hw, vf - 0.01, hw, vf + 2.2), 0.0, 0.55))
    for x in (-hw * 0.6, 0.0, hw * 0.6):
        parts.append(ext(circle((x, vf + 1.1), 0.8, 20) - circle((x, vf + 1.1), 0.35, 12), 0.54, 0.95))
        parts.append(ext(circle((x, vf + 1.1), 0.25, 10), 0.54, 1.05))
    top = vf + 2.0 + 1.1
    parts.append(MD.run(-hw - 0.5, hw + 0.5, top, MD.CROWN, 1.1, up=False))
    sw = w / 2 + A + 0.4
    parts.append(MD.run(-sw, sw, 0.0, MD.SILL, 1.0, up=False))
    return O._one_piece(sash, parts, op, plug_cs, O.PLUG, top, -1.0)


def door_crv(w, h, transom=3.2, A=1.0):
    """The Connecticut River Valley doorway: a pair of leaves of four raised panels each under
    a transom of five bull's-eye lights, between rusticated pilasters (blocks and recesses in
    turn) with scrolled capitals, carrying a pulvinated frieze and a segmental pediment with a
    carved sunburst rising in its tympanum."""
    H = h + transom
    op = rect(-w / 2, 0.0, w / 2, H)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    u0, u1 = -w / 2 + O.CLR + 0.3, w / 2 - O.CLR - 0.3
    body = [ext(plug_cs, -pl, -1.0), ext(rect(u0, 0.5, u1, h - 0.3), -1.0, -0.8)]
    for a, e in ((u0 + 0.5, -0.45), (0.45, u1 - 0.5)):
        for vb, vt in ((1.0, h * 0.24), (h * 0.24 + 0.7, h * 0.48), (h * 0.48 + 0.7, h * 0.72), (h * 0.72 + 0.7, h - 1.0)):
            body.append(_panel(rect(a, vb, e, vt)))
    body.append(ext(rect(-0.25, 0.5, 0.25, h - 0.3), -0.8, -0.5))
    tr = rect(u0, h + 0.3, u1, H - O.CLR - 0.3)
    body.append(ext(tr, -1.0, -0.8))
    n = 5
    g = []
    for j in range(n):
        x = u0 + (u1 - u0) * (j + 0.5) / n
        g.append(circle((x, h + transom / 2 - 0.1), min(0.8, (u1 - u0) / n / 2 - 0.25), 20))
    gcs = cs_union(g)
    sash = _glazed(body, gcs, pl, None, plug_cs)
    sash.append(ext(rect(-w, h - 0.3, w, h + 0.3) ^ plug_cs, -pl, -0.4))
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS),
             ext((op.offset(A, JoinType.Miter, 4.0) - op) ^ rect(-w, 0.0, w, H + A), 0.0, 0.8)]
    pw = 2.0
    ve = H + A
    for sg in (-1, 1):
        uc = sg * (w / 2 + A - 0.2 + pw / 2)
        parts.append(chamfer_box(uc - pw / 2 - 0.3, 0.0, uc + pw / 2 + 0.3, 2.0, 0.0, 1.4, c=0.3, bottom=0.0))
        v = 2.0
        k = 0
        while v < ve - 2.4:
            top = min(v + 2.2, ve - 2.2)
            parts.append(chamfer_box(uc - pw / 2 - (0.25 if k % 2 == 0 else 0.0), v - 0.01, uc + pw / 2 + (0.25 if k % 2 == 0 else 0.0),
                                     top, 0.0, 1.15 if k % 2 == 0 else 0.9, c=0.25))
            v = top
            k += 1
        parts.append(ext(rect(uc - pw / 2, v - 0.01, uc + pw / 2, ve - 1.4), 0.0, 0.9))
        cap = chamfer_box(uc - pw / 2 - 0.35, ve - 1.41, uc + pw / 2 + 0.35, ve, 0.0, 1.3, c=0.35)
        vol = cs_union([circle((uc + s_ * (pw / 2 + 0.1), ve - 0.95), 0.45, 12) for s_ in (-1, 1)])
        parts += [cap, ext(vol, 1.29, 1.5)]
    half = w / 2 + A - 0.2 + pw + 0.35
    parts.append(ext(rect(-half, ve - 0.01, half, ve + 0.9), 0.0, 1.0))
    parts.append(ext(rect(-half, ve + 0.85, half, ve + 2.7), 0.0, 0.7))                  # the pulvinated frieze
    parts.append(ext(rect(-half + 0.4, ve + 1.1, half - 0.4, ve + 2.3), 0.69, 1.0))
    vc = ve + 2.6 + 1.1
    parts.append(MD.run(-half - 0.6, half + 0.6, vc, MD.CROWN, 1.1, up=False))
    rise = (half + 0.6) * 0.42
    R = ((half + 0.6) ** 2 + rise ** 2) / (2 * rise)
    cy = vc + rise - R
    seg = circle((0.0, cy), R, 120) ^ rect(-half - 0.6, vc - 0.3, half + 0.6, vc + rise + 1)
    inner = circle((0.0, cy), R - 1.1, 120) ^ rect(-half + 0.5, vc + 0.6, half - 0.5, vc + rise + 1)
    parts.append(ext(seg - inner, 0.0, 1.2))
    parts.append(ext(inner, 0.0, 0.5))
    sun = cs_union([stroke([(0.0, vc + 0.6), ((rise * 1.8) * math.cos(a), vc + 0.6 + (rise * 1.8) * math.sin(a))], 0.45)
                    for a in np.linspace(math.pi / 9, 8 * math.pi / 9, 9)]) + (circle((0.0, vc + 0.6), 1.1, 20) ^ rect(-2, vc + 0.6, 2, vc + 3))
    parts.append(ext(sun ^ inner.offset(-0.3, JoinType.Miter, 4.0), 0.49, 0.9))
    return O._one_piece(sash, parts, op, plug_cs, pl, vc + rise, 0.0)


def door_battenlight(w, h, A=0.9):
    """The ell's door: a batten door with a small four-light window in its upper half, in a
    plain casing under a drip board."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    u0, u1 = -w / 2 + O.CLR + 0.3, w / 2 - O.CLR - 0.3
    body = [ext(plug_cs, -pl, -1.0)] + _board_leaf(u0, u1, 0.5, h - 0.3, hinges=False)
    g = rect(u0 + 1.0, h * 0.6, u1 - 1.0, h - 1.4)
    sash = _glazed(body, g, pl, _muntins(g, 2, 2), plug_cs)
    sash.append(ext(g.offset(0.5, JoinType.Miter, 4.0) - g, -0.9, -0.6))
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS),
             ext((op.offset(A, JoinType.Miter, 4.0) - op) ^ rect(-w, 0.0, w, h + A), 0.0, 0.7)]
    parts.append(chamfer_box(-w / 2 - A - 0.6, h + A - 0.01, w / 2 + A + 0.6, h + A + 1.0, 0.0, 1.2, c=0.4))
    return O._one_piece(sash, parts, op, plug_cs, pl, h + A + 1.0, 0.0)


# ------------------------------------------------------------------ chimney and the ell's porch
def chimney_ribbed(w=10.0, d=8.0, h=30.0):
    """A stack with raised pilaster strips at its corners and down the middle of each broad
    face, a necking band and a projecting cap of two courses."""
    h = round(h / 0.2) * 0.2
    sh = h - 2.6
    body = box([-w / 2, -d / 2, 0.0], [w / 2, d / 2, sh])
    ribs = []
    for x in (-w / 2 + 0.7, 0.0, w / 2 - 0.7):
        for sg in (-1, 1):
            ribs.append(box([x - 0.7, sg * d / 2 - 0.35, 0.0], [x + 0.7, sg * d / 2 + 0.35, sh - 2.2]))
    for y in (-d / 2 + 0.7, d / 2 - 0.7):
        for sg in (-1, 1):
            ribs.append(box([sg * w / 2 - 0.35, y - 0.7, 0.0], [sg * w / 2 + 0.35, y + 0.7, sh - 2.2]))
    body = body + union(ribs) + box([-w / 2 - 0.5, -d / 2 - 0.5, sh - 2.2], [w / 2 + 0.5, d / 2 + 0.5, sh - 1.4])
    body = body + box([-w / 2 - 0.8, -d / 2 - 0.8, sh - 0.01], [w / 2 + 0.8, d / 2 + 0.8, sh + 0.8]) + \
        box([-w / 2 - 0.4, -d / 2 - 0.4, sh + 0.79], [w / 2 + 0.4, d / 2 + 0.4, sh + 1.6])
    flues = union([box([x - 1.2, -1.2, sh - 4.0], [x + 1.2, 1.2, h + 5]) for x in (-w / 4, w / 4)])
    return body - flues


def post_ringed(h, collar=None, abacus=2.8, slot=(1.2, 1.0)):
    """A round post turned with three rings banding its shaft, on a square plinth, under a
    square abacus (the Porter's ell porch)."""
    z1 = h - 2.6
    r = 1.0
    prof = [(0.0, 1.19), (1.35, 1.19), (1.35, 1.45), (r, 1.8)]
    for f in (0.3, 0.55, 0.8):
        zc = round(z1 * f / 0.2) * 0.2
        prof += [(r, zc - 0.4), (1.25, zc - 0.15), (1.25, zc + 0.15), (r, zc + 0.4)]
    prof += [(r, z1), (1.2, z1 + 0.2), (1.2, z1 + 0.45), (r * 0.95, z1 + 0.65)]
    body = PW._revolve(prof, 28) + PW._plinth(2.9)
    return body + PW._top(h, abacus / 2, z1 + 0.65, r * 0.95, slot, seg=28)


def fill_rays(L, vb, vt):
    """A sunburst railing: in every bay flat bars rise as rays from a half-disc on the bottom
    rail to the hand rail (the Porter)."""
    H = vt - vb
    n = max(1, int(round(L / (H * 1.3))))
    parts = []
    for i in range(n):
        a, e = L * i / n, L * (i + 1) / n
        c = ((a + e) / 2, vb)
        R = min((e - a) / 2 - 0.2, H * 0.3)
        bay = [circle(c, R, 24) ^ rect(a, vb, e, vb + R + 0.1)]
        for t in np.linspace(0.2, 0.8, 5):
            ang = math.pi * t
            bay.append(stroke([c, (c[0] + 3 * H * math.cos(ang), vb + 3 * H * math.sin(ang))], 0.75, caps=False))
        parts.append(cs_union(bay) ^ rect(a + 0.3, vb, e - 0.3, vt))          # each bay's rays stay in their bay
        parts.append(rect(a - 0.3, vb, a + 0.3, vt))
    parts.append(rect(L - 0.3, vb, L + 0.3, vt))
    return parts


def frieze_blockdrops(u0, u1, v_bot, v_top):
    """A porch frieze: a board pierced with a row of square lights, a small pointed drop hung
    under every other one."""
    v0 = v_top - 2.6
    board = rect(u0, v0, u1, v_top + 0.05)
    n = max(2, int((u1 - u0) / 1.8))
    holes, drops = [], []
    for j in range(n):
        x = u0 + (u1 - u0) * (j + 0.5) / n
        holes.append(rect(x - 0.5, v0 + 0.8, x + 0.5, v0 + 1.8))
        if j % 2 == 0:
            drops.append(poly([(x - 0.4, v0 + 0.01), (x + 0.4, v0 + 0.01), (x, v0 - 1.0)]))
    return (board - cs_union(holes)) + cs_union(drops)


def edge_beadroll(L, z0, zc):
    """Porch fascia (the Porter): a row of round beads under the crown."""
    xs = np.arange(0.8, L - 0.6, 1.1)
    beads = [circle((x, zc - 0.85), 0.42, 12) for x in xs]
    return cs_union(beads) + rect(0.3, zc - 0.45, L - 0.3, zc), 0.45


PW.POSTS.update(ringed=post_ringed)
PW.FILLS.update(rays=fill_rays)
PW.FRIEZES.update(blockdrops=frieze_blockdrops)
_FT.EDGE_EXTRA.update(beadroll=edge_beadroll)


# ================================================================== the Pingree (house 47, Salem Federal, after McIntire)
# ------------------------------------------------------------------ skin and foundation
def brick_struck(region, datum=0.0, bl=2.6, bh=0.8, head=0.35, bed=0.22):
    """Salem brick: stretcher bond laid in fine joints struck back, each brick's face eased at
    its edges so the courses read soft and even."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    br = []
    k = math.floor((v0 - datum) / bh) - 1
    while datum + k * bh < v1:
        v = datum + k * bh
        u = u0 - bl - (k % 2) * (bl + head) / 2
        while u < u1 + bl:
            br.append(rect(u, v, u + bl, v + bh - bed))
            u += bl + head
        k += 1
    cs = cs_union(br) ^ region
    return M.extrude(region, 0.05) + stepped(cs, [(0.0, 0.0, 0.2), (0.12, 0.2, 0.32)])


def foundation_bushgranite(reg, seed=0):
    """Salem granite: long blocks with a drafted margin round a bush-hammered face (pitted all
    over), under a smooth chamfered top course (the Pingree)."""
    b = reg.bounds()
    rng = np.random.default_rng(seed + 31)
    top = b[3] - 1.4
    blocks, pits = [], []
    u = b[0] - rng.uniform(0, 4)
    while u < b[2]:
        L = rng.uniform(8.0, 13.0)
        blk = rect(u + 0.25, b[1] - 1, u + L - 0.25, top - 0.25)
        blocks.append(blk)
        face = rect(u + 1.0, b[1] + 0.6, u + L - 1.0, top - 1.0)
        fb = face.bounds()
        if fb[2] > fb[0] and fb[3] > fb[1]:
            for _ in range(int((fb[2] - fb[0]) * (fb[3] - fb[1]) * 0.9)):
                pits.append(circle((rng.uniform(fb[0], fb[2]), rng.uniform(fb[1], fb[3])), 0.22, 8))
        u += L
    body = ext(cs_union(blocks) ^ reg, 0.0, 0.45) + M.extrude(reg, 0.1)
    if pits:
        body = body - ext(cs_union(pits) ^ reg, 0.25, 1.0)
    return body + chamfer_box(b[0], top, b[2], b[3], 0.0, 0.8, c=0.35, square=("u0", "u1"), bottom=0.3)


# ------------------------------------------------------------------ cornice ornament
def frieze_baskets(L, h, b, pitch, margin, pair, half):
    """McIntire's baskets of fruit: at every station a woven basket heaped with fruit, and a
    patera with a ring of beads in each bay."""
    v0, v1 = 0.8, h - 0.8
    hh = v1 - v0
    vm = (v0 + v1) / 2
    out = []
    for u in CO._us(L, pitch, margin, 0.0):
        bw = hh * 0.8
        basket = poly([(u - bw, v0 + hh * 0.45), (u + bw, v0 + hh * 0.45), (u + bw * 0.62, v0), (u - bw * 0.62, v0)])
        weave = cs_union([rect(u - bw, v0 + hh * f - 0.12, u + bw, v0 + hh * f + 0.12) for f in (0.15, 0.3)])
        fruit = cs_union([circle((u + dx * hh, v0 + hh * (0.5 + dy)), r * hh, 14)
                          for dx, dy, r in ((-0.42, 0.02, 0.2), (0.0, 0.1, 0.24), (0.42, 0.02, 0.2), (-0.2, 0.3, 0.17), (0.2, 0.3, 0.17))])
        out.append(_st((basket - weave) ^ rect(u - 3, v0 - 0.2, u + 3, v1 + 0.2), b, 0.5))
        out.append(_st(fruit ^ rect(u - 3, v0 - 0.2, u + 3, v1 + 0.2), b, 0.65))
    for uc, wd in CO._between(L, pitch, margin, pair, half + 2.4):
        r = min(1.1, hh / 2 - 0.05)
        pat = (circle((uc, vm), r, 24) - circle((uc, vm), r - 0.35, 24)) + circle((uc, vm), r * 0.42, 16)
        out.append(_st(pat, b, 0.45))
    return out, []


def frieze_dolphins(L, h, b, pitch, margin, pair, half):
    """Salem dolphins: at every station two dolphins, tails up, arched head to head over a
    scallop shell; a little wave between the pairs."""
    v0, v1 = 0.8, h - 0.8
    hh = v1 - v0
    vm = (v0 + v1) / 2
    out = []
    for u in CO._us(L, pitch, margin, 0.0):
        parts = []
        for sg in (-1, 1):
            pts = []
            for t in np.linspace(0.0, 1.0, 12):
                x = u + sg * (0.4 + 3.4 * t)
                y = v0 + hh * (0.35 + 0.45 * math.sin(math.pi * t * 0.9))
                pts.append((x, y))
            wd_ = [0.9 - 0.55 * t for t in np.linspace(0.0, 1.0, 12)]
            body = cs_union([circle(p, w_ / 2 + 0.12, 12) for p, w_ in zip(pts, wd_)])
            tail = poly([(pts[-1][0], pts[-1][1]), (pts[-1][0] + sg * 0.7, pts[-1][1] + 0.7), (pts[-1][0] + sg * 0.9, pts[-1][1] - 0.2)])
            parts += [body, tail, circle((u + sg * 0.5, v0 + hh * 0.36), 0.5, 12)]
        sh, ribs = _shell((u, v0 + hh * 0.3), min(1.8, hh * 0.7))
        out.append(_st(cs_union(parts) ^ rect(max(0.3, u - 4.4), v0 - 0.2, min(L - 0.3, u + 4.4), v1 + 0.2), b, 0.5))
        out.append(_st(sh ^ rect(u - 2, v0 - 0.2, u + 2, v1 + 0.2), b, 0.35))
    for uc, wd in CO._between(L, pitch, margin, pair, half + 4.4):
        if wd < 2.0:
            continue
        pts = [(uc - wd / 2 + 0.3 + (wd - 0.6) * t, vm - 0.2 + 0.45 * math.sin(4 * math.pi * t)) for t in np.linspace(0, 1, 17)]
        out.append(_st(stroke(pts, 0.45), b, 0.35))
    return out, []


def _eagle(c, s):
    """A Federal eagle ``s`` wide: spread wings, a shield on its breast, the head turned."""
    x, y = c
    wings = []
    for sg in (-1, 1):
        wing = poly([(x + sg * 0.3, y + s * 0.05), (x + sg * s * 0.5, y + s * 0.28), (x + sg * s * 0.46, y + s * 0.12),
                     (x + sg * s * 0.4, y + s * 0.15), (x + sg * s * 0.36, y - s * 0.02), (x + sg * s * 0.28, y + s * 0.02),
                     (x + sg * s * 0.24, y - s * 0.12), (x + sg * 0.3, y - s * 0.1)])
        wings.append(wing)
    body = oval((x, y - s * 0.06), s * 0.09, s * 0.2, 16)
    head = circle((x + s * 0.03, y + s * 0.2), s * 0.075, 12)
    beak = poly([(x + s * 0.08, y + s * 0.21), (x + s * 0.16, y + s * 0.18), (x + s * 0.08, y + s * 0.16)])
    tail = poly([(x - s * 0.07, y - s * 0.22), (x + s * 0.07, y - s * 0.22), (x + s * 0.1, y - s * 0.34), (x - s * 0.1, y - s * 0.34)])
    shield = poly([(x - s * 0.08, y + s * 0.04), (x + s * 0.08, y + s * 0.04), (x + s * 0.08, y - s * 0.08), (x, y - s * 0.14),
                   (x - s * 0.08, y - s * 0.08)])
    return cs_union(wings + [body, head, beak, tail]), shield


def frieze_eagles(L, h, b, pitch, margin, pair, half):
    """Federal eagles, wings spread, a shield on the breast, at every station; between them a
    ribbon looped through three stars."""
    from .federal import _star
    v0, v1 = 0.8, h - 0.8
    hh = v1 - v0
    vm = (v0 + v1) / 2
    out = []
    s = min(8.0, hh * 2.2)
    for u in CO._us(L, pitch, margin, 0.0):
        body, shield = _eagle((u, vm + 0.2), s)
        out.append(_st(body ^ rect(u - s * 0.55, v0 - 0.2, u + s * 0.55, v1 + 0.2), b, 0.45))
        out.append(_st(shield, b, 0.65))
    for uc, wd in CO._between(L, pitch, margin, pair, half + s * 0.55):
        if wd < 3.0:
            continue
        pts = [(uc - wd / 2 + 0.3 + (wd - 0.6) * t, vm + 0.5 * math.sin(3 * math.pi * t)) for t in np.linspace(0, 1, 19)]
        out.append(_st(stroke(pts, 0.4), b, 0.3))
        for x in (uc - wd / 3, uc, uc + wd / 3):
            out.append(_st(_star((x, vm), min(0.9, hh / 2 - 0.1), ri=0.4), b, 0.5))
    return out, []


def course_reeds(L, h, b, pitch, margin, p):
    """A reeded course: short upright reeds side by side."""
    step = 0.9
    n = int((L - 1.0) / step)
    u0 = (L - (n - 1) * step) / 2
    return [ext(cs_union([rect(u0 + k * step - 0.25, 0.1, u0 + k * step + 0.25, h - 0.1) for k in range(n)]), b - 0.05, b + 0.45)]


def course_twist(L, h, b, pitch, margin, p):
    """A twist: two waving bands crossing each other the length of the course."""
    per = 2.8
    us = np.arange(0.5, L - 0.5, 0.2)
    a = [(u, h / 2 + (h / 2 - 0.3) * math.sin(2 * math.pi * u / per)) for u in us]
    c = [(u, h / 2 - (h / 2 - 0.3) * math.sin(2 * math.pi * u / per)) for u in us]
    return [ext(stroke(a, 0.42) ^ rect(0, 0, L, h), b - 0.05, b + 0.5), ext(stroke(c, 0.42) ^ rect(0, 0, L, h), b - 0.05, b + 0.35)]


def bracket_ovolomod(h, d, t):
    """A modillion whose underside is an ovolo: a full quarter-round bulging from the wall down
    to a flat nose (side profile, top at v = 0)."""
    hb = min(h, max(1.6, 0.3 * d))
    pts = [(0.0, 0.0), (d, 0.0), (d, -0.45)]
    for s in np.linspace(0.0, 1.0, 12)[1:]:
        t_ = s * math.pi / 2
        pts.append((d * math.cos(t_), -0.45 - (hb - 0.45) * math.sin(t_)))
    return poly(pts)


CO.FRIEZE_EXTRA.update(baskets=frieze_baskets, dolphins=frieze_dolphins, eagles=frieze_eagles)
CO.COURSE_EXTRA.update(reeds=course_reeds, twist=course_twist)
TW.BRACKET_EXTRA.update(ovolomod=bracket_ovolomod)
TW.FOUNDATION_EXTRA.update(bushgranite=foundation_bushgranite)


# ------------------------------------------------------------------ windows and doors
def window_splaylintel(w, h, A=0.8):
    """A Salem ground-floor window: a six-over-six sash in a thin architrave under a marble
    lintel with splayed ends and a raised tablet at its centre carved with a patera; a
    marble sill."""
    sash, op, plug_cs = _sash_pair(w, h, cols=3, rows=(2, 2))
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS),
             ext((op.offset(A, JoinType.Miter, 4.0) - op) ^ rect(-w, 0.0, w, h + A), 0.0, 0.55)]
    v = h + A
    hb, ht = w / 2 + A + 0.9, w / 2 + A + 2.2
    lint = poly([(-hb, v - 0.01), (hb, v - 0.01), (ht, v + 3.0), (-ht, v + 3.0)])
    parts.append(ext(lint, 0.0, 0.8))
    tab = rect(-1.8, v + 0.4, 1.8, v + 2.6)
    parts.append(ext(tab, 0.79, 1.1))
    parts.append(ext(circle((0.0, v + 1.5), 0.75, 20) - circle((0.0, v + 1.5), 0.35, 12), 1.09, 1.35))
    sw = w / 2 + A + 0.8
    parts.append(chamfer_box(-sw, -1.2, sw, 0.2, 0.0, 1.1, c=0.35, bottom=0.6))
    return O._one_piece(sash, parts, op, plug_cs, O.PLUG, v + 3.0, -1.2)


def window_fluteapron(w, h, A=0.9):
    """A Salem first-floor window: a six-over-six sash in a moulded architrave under a thin
    cornice, its sill over a panelled apron carved with flutes."""
    sash, op, plug_cs = _sash_pair(w, h, cols=3, rows=(2, 2))
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS),
             ext((op.offset(A, JoinType.Miter, 4.0) - op) ^ rect(-w, 0.0, w, h + A), 0.0, 0.7)]
    outer = op.offset(A, JoinType.Miter, 4.0) ^ rect(-w, 0.0, w, h + A)
    parts.append(ext((outer - outer.offset(-0.4, JoinType.Miter, 4.0)) ^ rect(-w, 0.4, w, h + A + 1), 0.69, 1.0))
    hw = w / 2 + A
    top = h + A + 1.0                                                         # the cornice laps the architrave
    parts.append(MD.run(-hw - 0.5, hw + 0.5, top, MD.CROWN, 1.2, up=False))
    sw = w / 2 + A + 0.4
    parts.append(MD.run(-sw, sw, 0.0, MD.SILL, 1.0, up=False))
    apron = rect(-w / 2, -3.4, w / 2, -0.7)                                # laps into the sill
    flutes = cs_union([rect(x - 0.2, -3.0, x + 0.2, -1.3) for x in np.arange(-w / 2 + 0.9, w / 2 - 0.6, 0.9)])
    parts.append(ext(apron, 0.0, 0.55) - ext(flutes, 0.3, 1.0))
    return O._one_piece(sash, parts, op, plug_cs, O.PLUG, top, -3.4)


def window_kneeled(w, h, A=0.8):
    """A Salem attic-storey window: a short six-over-three sash in a plain architrave, its sill
    carried on two small drops (a kneeled sill)."""
    sash, op, plug_cs = _sash_pair(w, h, cols=3, rows=(2, 1))
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS),
             ext((op.offset(A, JoinType.Miter, 4.0) - op) ^ rect(-w, 0.0, w, h + A), 0.0, 0.7),
             chamfer_box(-w / 2 - A - 0.4, h + A - 0.01, w / 2 + A + 0.4, h + A + 1.0, 0.0, 1.0, c=0.35)]
    sw = w / 2 + A + 0.6
    parts.append(chamfer_box(-sw, -1.0, sw, 0.2, 0.0, 1.1, c=0.35, bottom=0.6))
    for sg in (-1, 1):
        x = sg * (sw - 0.7)
        parts.append(ext(poly([(x - 0.5, -0.99), (x + 0.5, -0.99), (x, -2.4)]), 0.0, 0.9))
    return O._one_piece(sash, parts, op, plug_cs, O.PLUG, h + A + 1.0, -2.4)


def _elliptic_bars(w, v, ry):
    """Leading for an elliptical fanlight spanning w from centre (0, v): radiating bars, two
    elliptical rings and a hub."""
    rx = w / 2
    bars = [stroke([(0.0, v), (rx * 1.3 * math.cos(a), v + ry * 1.3 * math.sin(a))], RIB) for a in np.linspace(math.pi / 8, 7 * math.pi / 8, 7)]
    for f in (0.45, 0.8):
        bars.append(stroke([(rx * f * math.cos(a), v + ry * f * math.sin(a)) for a in np.linspace(0, math.pi, 25)], RIB))
    bars.append(circle((0.0, v), 0.8, 16) ^ rect(-1, v, 1, v + 1))
    return cs_union(bars)


def door_elliptic(w, h, side=3.0, fan=4.2, A=1.0):
    """The Salem entrance: a six-panel door between sidelights leaded in ovals, the whole width
    under one elliptical fanlight leaded in rays and rings, between reeded pilasters under a
    moulded cornice that steps up over the fan."""
    W_ = w + 2 * side
    ry = fan
    op = cs_union([rect(-W_ / 2, 0.0, W_ / 2, h), oval((0.0, h), W_ / 2, ry, 64) ^ rect(-W_, h, W_, h + ry + 1)])
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    body = [ext(plug_cs, -pl, -1.0)]
    u0, u1 = -w / 2 + 0.2, w / 2 - 0.2
    body.append(ext(rect(u0, 0.5, u1, h - 0.3), -1.0, -0.8))
    cw = (u1 - u0 - 1.8) / 2
    for c in range(2):
        pa = u0 + 0.6 + c * (cw + 0.6)
        for vb, vt in ((1.0, h * 0.3), (h * 0.3 + 0.7, h * 0.52), (h * 0.52 + 0.7, h - 1.0)):
            body.append(_panel(rect(pa, vb, pa + cw, vt)))
    glass, cames = [], []
    for sg in (-1, 1):
        a, e = sorted((sg * (w / 2 + 0.3), sg * (W_ / 2 - O.CLR - 0.4)))
        glass.append(rect(a, h * 0.2, e, h - 0.4))
        body.append(chamfer_box(a, 0.8, e, h * 0.2 - 0.4, -1.0, 0.4, c=0.2))
        um, hw = (a + e) / 2, (e - a) / 2
        for vc in np.linspace(h * 0.32, h * 0.86, 3):
            ov = oval((um, vc), hw * 0.95, 2.4, 20)
            cames.append(ov - ov.offset(-RIB, JoinType.Round))
    fan_g = plug_cs.offset(-0.5, JoinType.Miter, 4.0) ^ rect(-W_, h + 0.3, W_, h + ry + 2)
    glass.append(fan_g)
    g = cs_union(glass)
    bars = cs_union(cames) + (_elliptic_bars(W_ - 1.0, h + 0.3, ry - 0.8) ^ fan_g)
    sash = _glazed(body, g, pl, bars, plug_cs)
    sash.append(ext(rect(-W_, h - 0.3, W_, h + 0.3) ^ plug_cs, -pl, -0.4))
    sash.append(ext(cs_union([rect(-w / 2 - 0.3, 0.3, -w / 2 + 0.2, h), rect(w / 2 - 0.2, 0.3, w / 2 + 0.3, h)]) ^ plug_cs, -pl, -0.4))
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS)]
    ring = (op.offset(A, JoinType.Round) - op) ^ rect(-W_ - 5, 0.0, W_ + 5, h + ry + A + 2)
    parts.append(ext(ring, 0.0, 0.8))
    pw = 1.6
    vt = h + ry + A
    for sg in (-1, 1):
        uc = sg * (W_ / 2 + A - 0.2 + pw / 2)
        parts.append(chamfer_box(uc - pw / 2 - 0.3, 0.0, uc + pw / 2 + 0.3, 1.6, 0.0, 1.3, c=0.3, bottom=0.0))
        shaft = ext(rect(uc - pw / 2, 1.59, uc + pw / 2, h + 0.6), 0.0, 1.0)
        reeds = cs_union([rect(uc + dx - 0.18, 2.2, uc + dx + 0.18, h) for dx in (-0.45, 0.0, 0.45)])
        parts.append(shaft + ext(reeds, 0.99, 1.25))
        parts.append(chamfer_box(uc - pw / 2 - 0.3, h + 0.59, uc + pw / 2 + 0.3, h + 1.6, 0.0, 1.25, c=0.35))
    half = W_ / 2 + A - 0.2 + pw + 0.3
    parts.append(ext(rect(-half, h + 1.59, half, h + 2.4), 0.0, 0.8))
    parts.append(MD.run(-half - 0.4, half + 0.4, h + 3.4, MD.CROWN, 1.0, up=False))
    kt = vt + 0.6
    parts.append(ext(poly([(-0.7, vt - 1.4), (0.7, vt - 1.4), (1.0, kt), (-1.0, kt)]), 0.0, 1.3))
    return O._one_piece(sash, parts, op, plug_cs, pl, kt, 0.0)


def door_balcony(w, h, fan=3.2, A=0.9):
    """The door onto the portico's roof: a pair of glazed leaves, three lights each over a
    panel, under an elliptical fanlight, in a moulded architrave with a keystone."""
    ry = fan
    op = cs_union([rect(-w / 2, 0.0, w / 2, h), oval((0.0, h), w / 2, ry, 48) ^ rect(-w, h, w, h + ry + 1)])
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    u0, u1 = -w / 2 + O.CLR + 0.3, w / 2 - O.CLR - 0.3
    body = [ext(plug_cs, -pl, -1.0), ext(rect(u0, 0.5, u1, h - 0.3), -1.0, -0.8)]
    lights = []
    for a, e in ((u0 + 0.5, -0.4), (0.4, u1 - 0.5)):
        body.append(_panel(rect(a, 1.0, e, h * 0.3)))
        lights.append(rect(a, h * 0.3 + 0.7, e, h - 0.9))
    fan_g = plug_cs.offset(-0.5, JoinType.Miter, 4.0) ^ rect(-w, h + 0.3, w, h + ry + 2)
    g = cs_union(lights + [fan_g])
    bars = cs_union([_muntins(l_, 1, 3) ^ l_ for l_ in lights]) + (_elliptic_bars(w - 1.0, h + 0.3, ry - 0.7) ^ fan_g)
    sash = _glazed(body, g, pl, bars, plug_cs)
    sash.append(ext(rect(-w, h - 0.3, w, h + 0.3) ^ plug_cs, -pl, -0.4))
    sash.append(ext(rect(-0.3, 0.5, 0.3, h - 0.3), -0.8, -0.5))
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS),
             ext((op.offset(A, JoinType.Round) - op) ^ rect(-w - 5, 0.0, w + 5, h + ry + A + 2), 0.0, 0.8)]
    kt = h + ry + A + 0.6
    parts.append(ext(poly([(-0.6, h + ry - 0.6), (0.6, h + ry - 0.6), (0.9, kt), (-0.9, kt)]), 0.0, 1.3))
    parts.append(chamfer_box(-w / 2 - A - 0.4, -0.8, w / 2 + A + 0.4, 0.2, 0.0, 1.0, c=0.3, bottom=0.0))
    return O._one_piece(sash, parts, op, plug_cs, pl, kt, -0.8)


def window_cupola_arch(w, h, A=0.8):
    """A belvedere window: a round-headed sash of four lights over two, in an archivolt."""
    op = O.opening_cs(w, h, w / 2)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    inner = plug_cs.offset(-0.6, JoinType.Round)
    b_ = inner.bounds()
    bars = _muntins(inner, 2, 3) ^ inner
    sash = _glazed([ext(plug_cs, -pl, -0.6)], inner, pl, bars, plug_cs)
    parts = [ext(op - op.offset(-RIB, JoinType.Round), 0.0, O.CAS),
             ext((op.offset(A, JoinType.Round) - op) ^ rect(-w - 5, 0.0, w + 5, h + A + 2), 0.0, 0.7),
             chamfer_box(-w / 2 - A - 0.3, -0.8, w / 2 + A + 0.3, 0.2, 0.0, 0.9, c=0.3, bottom=0.0)]
    return O._one_piece(sash, parts, op, plug_cs, pl, h + A, -0.8)


# ------------------------------------------------------------------ chimneys
def chimney_curtain(w=7.0, d=9.0, gap=16.0, h=30.0, zc=0.0):
    """A Salem end-chimney pair: two stacks joined by a curtain wall of brick under a stone
    coping, each stack with a corbelled cap; the pair centred on the origin, along x. The
    curtain wall stops ``zc`` below the stacks' caps."""
    h = round(h / 0.2) * 0.2
    sh = h - 2.4
    parts = []
    xs = (-(gap / 2 + w / 2), gap / 2 + w / 2)
    for x in xs:
        parts.append(box([x - w / 2, -d / 2, 0.0], [x + w / 2, d / 2, sh]))
        parts.append(TW._skin(w, d, 0.0, sh - 0.2, TW._brick("flemish")).translate([x, 0, 0]))
        for k in range(2):
            g = 0.3 * (k + 1)
            parts.append(box([x - w / 2 - g, -d / 2 - g, sh + 0.6 * k - 0.01], [x + w / 2 + g, d / 2 + g, sh + 0.6 * (k + 1)]))
        parts.append(box([x - w / 2 - 0.9, -d / 2 - 0.9, sh + 1.19], [x + w / 2 + 0.9, d / 2 + 0.9, h]))
    wz = sh - 4.0 - zc
    parts.append(box([xs[0], -d / 2 + 1.0, 0.0], [xs[1], d / 2 - 1.0, wz]))
    parts.append(box([xs[0], -d / 2 + 0.6, wz - 0.01], [xs[1], d / 2 - 0.6, wz + 1.0]))              # the coping
    body = union(parts)
    flues = union([box([x - 1.2, -1.2, sh - 4.0], [x + 1.2, 1.2, h + 5]) for x in xs])
    return body - flues


# ------------------------------------------------------------------ the semicircular portico
def post_mcintire(h, collar=None, abacus=3.0, slot=None):
    """A McIntire column: a slender fluted shaft (the flutes as a ring of shallow grooves) on an
    Attic base, a bell capital ringed by two tiers of leaves and a square abacus with its
    corners cut."""
    z1 = round((h - 3.6) / 0.2) * 0.2
    r = 1.1
    prof = [(0.0, 0.0), (1.55, 0.0), (1.55, 0.3), (1.4, 0.5), (1.25, 0.6), (1.25, 0.8), (1.4, 1.0), (1.4, 1.2),
            (r, 1.5), (r * 0.9, z1), (1.05, z1 + 0.2), (1.05, z1 + 0.4), (r * 0.9, z1 + 0.5), (1.3, z1 + 2.2),
            (1.45, z1 + 2.6)]
    body = PW._revolve(prof, 32)
    flutes = []
    for a in np.linspace(0, 2 * math.pi, 12, endpoint=False):
        flutes.append(box([r * 0.9 - 0.2, -0.16, 2.0], [r * 0.9 + 0.3, 0.16, z1 - 0.6]).rotate([0, 0, math.degrees(a)]))
    body = body - union(flutes)
    leaves = []
    for tier, (z_a, z_b, n) in enumerate(((z1 + 0.5, z1 + 1.5, 8), (z1 + 1.1, z1 + 2.3, 8))):
        for a in np.linspace(0, 2 * math.pi, n, endpoint=False) + tier * math.pi / n:
            ca, sa = math.cos(a), math.sin(a)
            tx, ty = -sa * 0.25, ca * 0.25
            pts = []
            for rr, zz in ((r * 0.88, z_a), (1.5, z_b - 0.2), (1.35, z_b)):
                pts += [(rr * ca + tx, rr * sa + ty, zz), (rr * ca - tx, rr * sa - ty, zz)]
            leaves.append(M.hull_points(pts))
    body = body + union(leaves)
    s_ = abacus / 2
    ab = box([-s_, -s_, z1 + 2.59], [s_, s_, h])
    corners = union([box([sx * s_ - 0.5, sy * s_ - 0.5, z1 + 2.5], [sx * s_ + 0.5, sy * s_ + 0.5, h + 1]).rotate([0, 0, 0])
                     for sx in (-1, 1) for sy in (-1, 1)])
    return body + (ab - corners) + box([-s_ + 0.6, -s_ + 0.6, z1 + 2.5], [s_ - 0.6, s_ - 0.6, h])


def baluster_spindlevase(h):
    """A slender urn baluster with a long spindle neck (the Pingree)."""
    top = h - 0.5
    L_ = top - 0.5
    prof = [(0.0, 0.5), (0.35, 0.5), (0.5, 0.5 + L_ * 0.18), (0.4, 0.5 + L_ * 0.34), (0.2, 0.5 + L_ * 0.45), (0.2, 0.5 + L_ * 0.85),
            (0.34, 0.5 + L_ * 0.92), (0.3, top)]
    return PW._revolve(prof, 16) + box([-0.5, -0.5, 0.0], [0.5, 0.5, 0.51]) + box([-0.5, -0.5, top - 0.01], [0.5, 0.5, h])


def _sector(c, r0, r1, a0, a1, seg=48):
    """An annular sector (plan) between radii r0 < r1 and angles a0..a1."""
    pts = [(c[0] + r1 * math.cos(a), c[1] + r1 * math.sin(a)) for a in np.linspace(a0, a1, seg)]
    if r0 > 0:
        pts += [(c[0] + r0 * math.cos(a), c[1] + r0 * math.sin(a)) for a in np.linspace(a1, a0, seg)]
    else:
        pts.append(c)
    return poly(pts)


def semicircle_portico(c, R, H_floor, col_h, n_cols=4, steps=3, rail_h=7.0):
    """A McIntire semicircular portico against a wall along y = c[1] (the portico to -y): a
    paved stone floor with half-round steps down to the ground (one part), and one top in the
    pink-house way: the flat roof, a cornice and a fluted entablature on its curve, and the
    columns, all one piece printed upside down, a peg under each column into a socket in the
    floor. A balustrade (turned balusters between pedestals, a curved hand rail) stands on the
    roof. Returns dict(floor, top, balustrade, sockets=[(x, y)], ptop)."""
    a0, a1 = math.pi, 2 * math.pi
    Rc = R - 2.4                                         # the columns' circle
    # floor and steps
    floor = M.extrude(_sector(c, 0, R, a0, a1), H_floor)
    joints = []
    for rr in np.arange(4.0, R - 0.5, 3.2):
        joints.append(_sector(c, rr - 0.15, rr + 0.15, a0, a1))
    for a in np.linspace(a0, a1, 9)[1:-1]:
        joints.append(stroke([(c[0] + 2.0 * math.cos(a), c[1] + 2.0 * math.sin(a)), (c[0] + R * math.cos(a), c[1] + R * math.sin(a))], 0.3))
    floor = floor - M.extrude(cs_union(joints), 1.0).translate([0, 0, H_floor - 0.3])
    rise = H_floor / (steps + 1)
    for k in range(1, steps + 1):
        zt = round((H_floor - k * rise) / 0.2) * 0.2
        floor = floor + M.extrude(_sector(c, R - 0.5, R + 1.9 * k, a0, a1), zt)
    floor = floor + M.extrude(_sector(c, R - 0.4, R, a0, a1), H_floor)             # a nosing ring
    where = [(c[0] + Rc * math.cos(a), c[1] + Rc * math.sin(a)) for a in np.linspace(a0, a1, n_cols + 2)[1:-1]]
    sockets = union([M.cylinder(3.0, 1.0, 1.0, 20).translate([p[0], p[1], H_floor - 2.0]) for p in where])
    floor = floor - sockets
    # the top: columns, entablature, cornice, roof
    z0 = H_floor
    ze = z0 + col_h
    col = PW.POSTS["mcintire"](col_h, abacus=3.0)
    parts = [col.translate([p[0], p[1], z0]) for p in where]
    parts += [M.cylinder(2.2, 0.8, 0.8, 20).translate([p[0], p[1], z0 - 1.8]) for p in where]      # pegs
    ent_h, cor_h, roof_t = 4.0, 1.6, 1.4
    ent = M.extrude(_sector(c, Rc - 1.7, Rc + 1.7, a0, a1, 64), ent_h).translate([0, 0, ze - 0.01])
    flutes = []
    for a in np.linspace(a0, a1, 64)[1:-1]:
        ca, sa = math.cos(a), math.sin(a)
        flutes.append(box([Rc + 1.4, -0.2, ze + 1.4], [Rc + 2.0, 0.2, ze + ent_h - 0.5]).rotate([0, 0, math.degrees(a)]).translate([c[0], c[1], 0]))
    ent = ent - union(flutes)
    fillet = M.extrude(_sector(c, Rc - 1.8, Rc + 1.95, a0, a1, 64), 0.6).translate([0, 0, ze + 1.0])
    cor = M.extrude(_sector(c, 0, Rc + 2.8, a0, a1, 64), cor_h).translate([0, 0, ze + ent_h - 0.01])
    cor = cor + M.extrude(_sector(c, 0, Rc + 2.3, a0, a1, 64), 0.61).translate([0, 0, ze + ent_h - 0.6])
    roof = M.extrude(_sector(c, 0, Rc + 3.2, a0, a1, 64), roof_t).translate([0, 0, ze + ent_h + cor_h - 0.01])
    top = union(parts + [ent, fillet, cor, roof])
    top = top.trim_by_plane([0, -1.0, 0], -c[1])                                       # nothing behind the wall line
    ptop = ze + ent_h + cor_h + roof_t - 0.01
    # the balustrade on the roof: pedestals over the columns, balusters between, a curved rail
    Rb = Rc + 1.8
    bparts = [M.extrude(_sector(c, Rb - 0.6, Rb + 0.6, a0, a1, 64), 0.8)]
    ped = [(c[0] + Rb * math.cos(a), c[1] + Rb * math.sin(a), a) for a in np.linspace(a0, a1, n_cols + 2)]
    for x, y, a in ped:
        bparts.append(box([-1.2, -1.2, 0.0], [1.2, 1.2, rail_h + 0.6]).rotate([0, 0, math.degrees(a)]).translate([x, y, 0]))
    bal = baluster_spindlevase(rail_h - 1.8)
    arc_len = Rb * math.pi
    nb = int(arc_len / 1.7)
    for j in range(nb):
        a = a0 + (a1 - a0) * (j + 0.5) / nb
        if any(abs(a - pa) < 1.8 / Rb for _, _, pa in ped):
            continue
        bparts.append(bal.translate([c[0] + Rb * math.cos(a), c[1] + Rb * math.sin(a), 0.79]))
    bparts.append(M.extrude(_sector(c, Rb - 0.7, Rb + 0.7, a0, a1, 64), 1.0).translate([0, 0, rail_h - 1.0]))
    balustrade = union(bparts).trim_by_plane([0, -1.0, 0], -c[1]).translate([0, 0, ptop])
    return dict(floor=floor.trim_by_plane([0, -1.0, 0], -c[1]), top=top, balustrade=balustrade,
                sockets=where, ptop=ptop)


PW.POSTS.update(mcintire=post_mcintire)
PW.BALUSTERS.update(spindlevase=(baluster_spindlevase, 1.7))


def finial_eagle(s=6.0):
    """A cupola finial: a gilded eagle with spread wings standing on a ball on a turned stem
    (the Pingree). Base at z = 0, printed with its roof."""
    prof = [(0.0, 0.0), (1.0, 0.0), (1.0, 0.4), (0.55, 0.9), (0.45, 1.8), (0.7, 2.1), (0.45, 2.4)]
    stem = PW._revolve(prof, 20)
    ball = M.sphere(1.3, 24).translate([0, 0, 3.4]) + M.cylinder(1.2, 0.5, 0.5, 16).translate([0, 0, 2.3])
    body, shield = _eagle((0.0, 0.0), s)
    b_ = body.bounds()
    plate = M.extrude(body + shield, 1.2).translate([0, 0, -0.6])
    plate = plate.transform(np.array([[1.0, 0, 0, 0], [0, 0, 1.0, 0], [0, 1.0, 0, 4.5 - b_[1]]]))
    return stem + ball + plate


# ================================================================== the Alvarado (house 48, Spanish Colonial)
# ------------------------------------------------------------------ skin and foundation
def plaster_trowelled(region, datum=0.0, dado=6.0):
    """Lime plaster over adobe: a soft coat trowelled in long shallow sweeps, over a painted
    dado band at the foot of the wall that stands a little proud."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    rng = np.random.default_rng(int(abs(u0) * 7 + abs(v0) * 3) % 991)
    marks = []
    for _ in range(int((u1 - u0) * max(0.0, v1 - v0 - dado) / 90.0)):
        cx, cy = rng.uniform(u0, u1), rng.uniform(datum + dado + 1.0, v1)
        a = rng.uniform(-0.5, 0.5)
        L, T = rng.uniform(3.0, 7.0), rng.uniform(1.0, 2.2)
        marks.append(poly([(cx + L * math.cos(a) * math.cos(t) - T * math.sin(a) * math.sin(t),
                            cy + L * math.sin(a) * math.cos(t) + T * math.cos(a) * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 12, endpoint=False)]))
    out = M.extrude(region, 0.3)
    if marks:
        out = out + ext(cs_union(marks) ^ region, 0.29, 0.38)             # trowel marks: soft, broad, barely proud
    band = region ^ rect(u0 - 1, v0 - 1, u1 + 1, datum + dado)
    if not band.is_empty():
        out = out + ext(band, 0.29, 0.55) + ext(region ^ rect(u0 - 1, datum + dado - 0.01, u1 + 1, datum + dado + 0.6), 0.29, 0.7)
    return out


def foundation_coquina(reg, seed=0):
    """Coquina: blocks of shell stone, their faces pocked with shell-shaped hollows (little
    fans and ovals) (the Alvarado)."""
    b = reg.bounds()
    rng = np.random.default_rng(seed + 41)
    blocks, holes = [], []
    v = b[1] - 0.5
    k = 0
    while v < b[3]:
        ch = 3.2 if k % 2 == 0 else 2.6
        u = b[0] - rng.uniform(0, 4)
        while u < b[2]:
            L = rng.uniform(5.0, 8.0)
            blocks.append(rect(u + 0.25, v + 0.25, u + L - 0.25, v + ch - 0.25))
            for _ in range(int(L * ch * 0.35)):
                x, y = rng.uniform(u + 0.7, u + L - 0.7), rng.uniform(v + 0.6, v + ch - 0.6)
                if rng.random() < 0.5:
                    holes.append(oval((x, y), 0.45, 0.28, 12))
                else:
                    holes.append(circle((x, y), 0.4, 12) ^ rect(x - 1, y, x + 1, y + 1))
            u += L
        v += ch
        k += 1
    body = ext(cs_union(blocks) ^ reg, 0.0, 0.45) + M.extrude(reg, 0.1)
    return body - ext(cs_union(holes) ^ reg, 0.25, 1.0) if holes else body


# ------------------------------------------------------------------ cornice ornament
def frieze_azulejos(L, h, b, pitch, margin, pair, half):
    """Azulejos: a band of square tiles set edge to edge, each with a raised eight-pointed star
    in a ring, and every third tile a quatrefoil."""
    v0, v1 = 0.7, h - 0.7
    hh = v1 - v0
    out = []
    n = max(1, int((L - 1.0) / hh))
    s = (L - 1.0) / n
    tiles, orn = [], []
    for j in range(n):
        u = 0.5 + j * s
        tiles.append(rect(u + 0.15, v0, u + s - 0.15, v1))
        c = (u + s / 2, (v0 + v1) / 2)
        r = hh / 2 - 0.35
        if j % 3 == 2:
            orn.append(cs_union([circle((c[0] + r * 0.45 * math.cos(a), c[1] + r * 0.45 * math.sin(a)), r * 0.45, 12)
                                 for a in (0, math.pi / 2, math.pi, 3 * math.pi / 2)]))
        else:
            sq = rect(c[0] - r * 0.62, c[1] - r * 0.62, c[0] + r * 0.62, c[1] + r * 0.62)          # two squares crossed: a star
            orn.append(cs_union([sq, poly([(c[0], c[1] - r * 0.88), (c[0] + r * 0.88, c[1]), (c[0], c[1] + r * 0.88),
                                           (c[0] - r * 0.88, c[1])])]))
    out.append(_st(cs_union(tiles), b, 0.25))
    out.append(_st(cs_union(orn), b, 0.55))
    return out, []


def _pomegranate(c, s):
    x, y = c
    fruit = circle((x, y - s * 0.05), s * 0.3, 20)
    crown = poly([(x - s * 0.14, y + s * 0.18), (x - s * 0.1, y + s * 0.38), (x, y + s * 0.26), (x + s * 0.1, y + s * 0.38),
                  (x + s * 0.14, y + s * 0.18)])
    lv = [_lens((x + sg * s * 0.38, y + s * 0.12), s * 0.42, s * 0.16, math.radians(30 if sg > 0 else 150)) for sg in (-1, 1)]
    return cs_union([fruit, crown] + lv)


def frieze_pomegranates(L, h, b, pitch, margin, pair, half):
    """Pomegranates of Granada, each crowned and between two leaves, alternating with
    eight-pointed stars."""
    from .federal import _star
    v0, v1 = 0.8, h - 0.8
    hh = v1 - v0
    vm = (v0 + v1) / 2
    out = []
    for u in CO._us(L, pitch, margin, 0.0):
        out.append(_st(_pomegranate((u, vm), hh * 1.1) ^ rect(u - 3, v0 - 0.2, u + 3, v1 + 0.2), b, 0.55))
    for uc, wd in CO._between(L, pitch, margin, pair, half + 2.2):
        r = min(1.3, hh / 2 - 0.05)
        st8 = cs_union([_star((uc, vm), r, ri=r * 0.55, ang=math.pi / 2), _star((uc, vm), r, ri=r * 0.55, ang=math.pi / 2 + math.pi / 5)])
        out.append(_st(st8 ^ circle((uc, vm), r, 24), b, 0.45))
    return out, []


def course_cordon(L, h, b, pitch, margin, p):
    """The Franciscan cordon: a twisted cord the length of the course, tied in a knot at
    intervals."""
    per = 1.2
    out = []
    us = np.arange(0.3, L - 0.3, per)
    for u in us:
        out.append(ext(poly([(u, 0.15), (u + 0.55, 0.15), (u + per * 0.95, h - 0.15), (u + per * 0.4, h - 0.15)]), b - 0.05, b + 0.4))
    for u in np.arange(6.0, L - 3.0, 9.0):
        out.append(ext(oval((u, h / 2), 0.9, h / 2 - 0.02, 16), b - 0.05, b + 0.6))
    return out


def bracket_zapata(h, d, t):
    """A viga end: a square beam end whose underside is cut in two scallops toward its nose
    (side profile, top at v = 0)."""
    hb = min(h, max(1.8, 0.34 * d))
    pts = [(0.0, 0.0), (d, 0.0), (d, -hb * 0.45)]
    for s in np.linspace(0.0, 1.0, 14)[1:]:
        x = d - d * 0.55 * s
        pts.append((x, -hb * 0.45 - hb * 0.25 * abs(math.sin(2 * math.pi * s))))
    pts += [(d * 0.45, -hb), (0.0, -hb)]
    return poly(pts)


CO.FRIEZE_EXTRA.update(azulejos=frieze_azulejos, pomegranates=frieze_pomegranates)
CO.COURSE_EXTRA.update(cordon=course_cordon)
TW.BRACKET_EXTRA.update(zapata=bracket_zapata)
TW.FOUNDATION_EXTRA.update(coquina=foundation_coquina)


# ------------------------------------------------------------------ windows and doors
def _mixtilinear(w, v, rise):
    """A mixtilinear (scalloped) arch head across w springing at v: a central round lobe
    between two smaller ones, stepped at the shoulders."""
    r0, r1 = w * 0.22, w * 0.16
    parts = [rect(-w / 2, v - 0.01, w / 2, v + r1 * 0.9), circle((0.0, v + rise - r0), r0, 32),
             circle((-w / 2 + r1 * 1.3, v + r1 * 0.9), r1, 24), circle((w / 2 - r1 * 1.3, v + r1 * 0.9), r1, 24),
             rect(-r0, v, r0, v + rise - r0)]
    return cs_union(parts)


def window_reja(w, h, A=1.0):
    """A ground-floor window of the Alvarado: a pair of casements (three lights each) set deep,
    guarded by a projecting reja of turned wooden spindles between two rails on a sill board,
    capped by a small moulded head."""
    op = O.opening_cs(w, h, 0)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    inner = plug_cs.offset(-0.6, JoinType.Miter, 4.0)
    u0_, v0_, u1_, v1_ = inner.bounds()
    leaves = [rect(u0_, v0_, -0.3, v1_), rect(0.3, v0_, u1_, v1_)]
    sash = _glazed([ext(plug_cs, -pl, -0.8)], cs_union(leaves), pl, cs_union([_muntins(l_, 1, 3) for l_ in leaves]), plug_cs)
    sash.append(ext(rect(-0.31, v0_ - 0.01, 0.31, v1_ + 0.01), -pl, -0.5))
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS),
             ext((op.offset(A, JoinType.Miter, 4.0) - op) ^ rect(-w, -0.9, w, h + A), 0.0, 0.7)]
    dep = 2.0
    hw = w / 2 + A
    parts.append(chamfer_box(-hw - 0.4, -0.9, hw + 0.4, 0.2, 0.0, dep + 0.6, c=0.3, bottom=0.6))            # the sill board
    parts.append(chamfer_box(-hw - 0.4, h + A - 0.2, hw + 0.4, h + A + 1.0, 0.0, dep + 0.6, c=0.35))       # the head
    for x in np.linspace(-hw + 0.9, hw - 0.9, max(3, int((2 * hw - 1.8) / 1.5) + 1)):
        prof = [(0.0, 0.0), (0.42, 0.0), (0.42, 0.3), (0.3, 0.6)]
        for f in (0.33, 0.66):
            zc = h * f
            prof += [(0.3, zc - 0.5), (0.45, zc - 0.25), (0.45, zc + 0.25), (0.3, zc + 0.5)]
        prof += [(0.3, h - 0.3), (0.42, h), (0.0, h)]
        sp = PW._revolve(prof, 12)                                   # a turned spindle, standing in the (u, v) plane at w = dep
        parts.append(sp.translate([x, dep, 0.1]).transform(np.array([[1.0, 0, 0, 0], [0, 0, 1.0, 0], [0, 1.0, 0, 0]])))
    for v in (h * 0.2, h * 0.8):
        parts.append(ext(rect(-hw + 0.3, v - 0.35, hw - 0.3, v + 0.35), dep - 0.5, dep + 0.5))
    for sg in (-1, 1):                                                        # the reja's cheeks tie it back to the wall
        a_, e_ = sorted((sg * (hw - 0.4), sg * (hw + 0.3)))
        parts.append(ext(rect(a_, -0.5, e_, h + A + 0.1), 0.0, dep + 0.5))
    return O._one_piece(sash, parts, op, plug_cs, pl, h + A + 1.0, -0.9)


def window_ornatehead(w, h, A=1.0):
    """An upper window of the Alvarado: a pair of casements under a carved wooden lintel whose
    lower edge is cut in a mixtilinear arch, in a plain frame."""
    op = O.opening_cs(w, h, 0)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    inner = plug_cs.offset(-0.6, JoinType.Miter, 4.0)
    u0_, v0_, u1_, v1_ = inner.bounds()
    leaves = [rect(u0_, v0_, -0.3, v1_), rect(0.3, v0_, u1_, v1_)]
    sash = _glazed([ext(plug_cs, -pl, -0.8)], cs_union(leaves), pl, cs_union([_muntins(l_, 1, 3) for l_ in leaves]), plug_cs)
    sash.append(ext(rect(-0.31, v0_ - 0.01, 0.31, v1_ + 0.01), -pl, -0.5))
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS),
             ext((op.offset(A, JoinType.Miter, 4.0) - op) ^ rect(-w, 0.0, w, h + A), 0.0, 0.7)]
    hw = w / 2 + A + 1.0
    lint = rect(-hw, h - 2.4, hw, h + A + 2.6) - _mixtilinear(w - 0.6, h - 2.4, 2.6)
    parts.append(ext(lint, 0.0, 0.9))
    parts.append(ext(cs_union([circle((sg * (hw - 1.1), h + A + 1.0), 0.55, 14) for sg in (-1, 1)]), 0.89, 1.2))
    parts.append(chamfer_box(-hw, -1.0, hw, 0.2, 0.0, 1.1, c=0.3, bottom=0.6))
    return O._one_piece(sash, parts, op, plug_cs, pl, h + A + 2.6, -1.0)


def door_mixtilinear(w, h, A=1.4):
    """The Alvarado's portal: a pair of plank leaves studded with rows of iron nails, under a
    mixtilinear arch, in a moulded stone surround with a keystone and a cornice."""
    rise = w * 0.42
    op = cs_union([rect(-w / 2, 0.0, w / 2, h), _mixtilinear(w, h, rise)])
    plug_cs = op.offset(-O.CLR, JoinType.Round)
    pl = O.PLUG
    face = plug_cs.offset(-0.4, JoinType.Round)
    body = [ext(plug_cs, -pl, -0.8)]
    grooves = cs_union([rect(x - 0.18, 0.0, x + 0.18, h + rise) for x in np.arange(-w / 2 + 1.3, w / 2 - 0.3, 1.3)] +
                       [rect(-0.3, 0.0, 0.3, h + rise)])
    body = [b_ - ext(grooves ^ face, -1.0, -0.6) for b_ in body]
    studs = [circle((x, v), 0.3, 8) for x in np.arange(-w / 2 + 1.95, w / 2 - 0.3, 1.3) for v in np.arange(2.0, h, 3.2)]
    body.append(ext(cs_union(studs) ^ face, -0.81, -0.5))
    body.append(ext(plug_cs - plug_cs.offset(-0.5, JoinType.Round), -pl, 0.0))
    ring = (op.offset(A, JoinType.Round) - op) ^ rect(-w - 5, 0.0, w + 5, h + rise + A + 2)
    parts = [ext(op - op.offset(-RIB, JoinType.Round), 0.0, O.CAS), ext(ring, 0.0, 1.0)]
    outer = op.offset(A, JoinType.Round) ^ rect(-w - 5, 0.0, w + 5, h + rise + A + 2)
    parts.append(ext((outer - outer.offset(-0.45, JoinType.Round)) ^ rect(-w - 5, 0.5, w + 5, h + rise + A + 2), 0.99, 1.35))
    kt = h + rise + A + 0.6
    parts.append(ext(poly([(-0.8, h + rise - 0.6), (0.8, h + rise - 0.6), (1.1, kt), (-1.1, kt)]), 0.0, 1.5))
    hw = w / 2 + A + 0.8
    alfiz = rect(-hw + 0.2, h - 1.0, hw - 0.2, kt - 0.3)                   # the alfiz: a flat frame round the arch
    parts.append(ext(alfiz - op.offset(A - 0.1, JoinType.Round), 0.0, 0.7))
    parts.append(ext(alfiz - alfiz.offset(-0.5, JoinType.Miter, 4.0) - rect(-hw, h - 1.1, hw, h - 0.5), 0.69, 1.1))
    parts.append(chamfer_box(-hw, kt - 0.4, hw, kt + 0.8, 0.0, 1.6, c=0.4))
    return O._one_piece(body, parts, op, plug_cs, pl, kt + 0.8, 0.0)


def door_plankglazed(w, h, A=1.0):
    """A balcony door of the Alvarado: a pair of plank leaves, each with a small glazed light of
    four panes in its upper part, under a plain lintel."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    u0, u1 = -w / 2 + O.CLR + 0.3, w / 2 - O.CLR - 0.3
    body = [ext(plug_cs, -pl, -1.0)] + _board_leaf(u0, -0.25, 0.5, h - 0.3, hinges=False) + _board_leaf(0.25, u1, 0.5, h - 0.3, hinges=False)
    lights = [rect(u0 + 0.8, h * 0.58, -1.0, h - 1.4), rect(1.0, h * 0.58, u1 - 0.8, h - 1.4)]
    sash = _glazed(body, cs_union(lights), pl, cs_union([_muntins(l_, 2, 2) ^ l_ for l_ in lights]), plug_cs)
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS),
             ext((op.offset(A, JoinType.Miter, 4.0) - op) ^ rect(-w, 0.0, w, h + A), 0.0, 0.8),
             chamfer_box(-w / 2 - A - 0.6, h + A - 0.01, w / 2 + A + 0.6, h + A + 1.4, 0.0, 1.2, c=0.35),
             chamfer_box(-w / 2 - A - 0.3, -0.8, w / 2 + A + 0.3, 0.2, 0.0, 1.0, c=0.3, bottom=0.0)]
    return O._one_piece(sash, parts, op, plug_cs, pl, h + A + 1.4, -0.8)


# ------------------------------------------------------------------ the balcony, chimney and garden wall
def post_zapata(h, collar=None, abacus=2.6, slot=None):
    """A balcony post: a slim turned post with a ring near each end, crowned by crossed
    zapatas (bracket capitals with scalloped ends) (the Alvarado)."""
    z1 = h - 2.4
    r = 0.85
    prof = [(0.0, 0.0), (1.25, 0.0), (1.25, 0.9), (r, 1.3), (r, 2.4), (1.1, 2.6), (1.1, 2.9), (r, 3.1), (r, z1 - 1.4),
            (1.1, z1 - 1.2), (1.1, z1 - 0.9), (r, z1 - 0.7), (r, z1), (0.0, z1)]
    body = PW._revolve(prof, 24)
    zap = poly([(-3.2, 0.0), (3.2, 0.0), (3.2, -0.7), (2.6, -0.9), (2.3, -1.5), (1.7, -1.6), (1.4, -2.4), (-1.4, -2.4),
                (-1.7, -1.6), (-2.3, -1.5), (-2.6, -0.9), (-3.2, -0.7)])
    zs = []
    for rot in (0, 90):
        m = M.extrude(zap, 1.4).translate([0, 0, -0.7]).transform(np.array([[1.0, 0, 0, 0], [0, 0, 1.0, 0], [0, 1.0, 0, h]]))
        zs.append(m.rotate([0, 0, rot]))
    return body + union(zs) + box([-0.9, -0.9, z1 - 0.01], [0.9, 0.9, h - 2.3])


def baluster_rejaspindle(h):
    """A slim turned spindle with three small rings (the Alvarado's balcony)."""
    top = h - 0.5
    prof = [(0.0, 0.5), (0.3, 0.5)]
    for f in (0.25, 0.5, 0.75):
        zc = 0.5 + (top - 0.5) * f
        prof += [(0.26, zc - 0.35), (0.42, zc - 0.12), (0.42, zc + 0.12), (0.26, zc + 0.35)]
    prof += [(0.3, top)]
    return PW._revolve(prof, 14) + box([-0.5, -0.5, 0.0], [0.5, 0.5, 0.51]) + box([-0.5, -0.5, top - 0.01], [0.5, 0.5, h])


def frieze_mixtilinear(u0, u1, v_bot, v_top):
    """A balcony frieze: a board sawn along its lower edge into a row of little mixtilinear
    arches."""
    v0 = v_top - 3.0
    board = rect(u0, v0, u1, v_top + 0.05)
    n = max(1, int((u1 - u0) / 3.0))
    s = (u1 - u0) / n
    cuts = []
    for j in range(n):
        uc = u0 + s * (j + 0.5)
        cuts.append(_mixtilinear(s - 0.9, v0 - 0.01, 1.6).translate((uc, 0.0)))
    return board - cs_union(cuts)


def edge_tejas(L, z0, zc):
    """Balcony fascia (the Alvarado): a row of round tile ends (tejas) under the crown."""
    xs = np.arange(0.9, L - 0.6, 1.4)
    ends = [circle((x, zc - 0.4), 0.6, 14) ^ rect(x - 1, zc - 1.1, x + 1, zc - 0.4) for x in xs]
    return cs_union(ends) + rect(0.3, zc - 0.45, L - 0.3, zc), 0.5


def chimney_tilesaddle(w=9.0, d=9.0, h=30.0):
    """A plastered stack capped by a little saddle roof of barrel tiles on two arches, the
    smoke escaping under it."""
    h = round(h / 0.2) * 0.2
    sh = h - 6.0
    body = box([-w / 2, -d / 2, 0.0], [w / 2, d / 2, sh]) + box([-w / 2 - 0.6, -d / 2 - 0.6, sh - 1.0], [w / 2 + 0.6, d / 2 + 0.6, sh])
    for sg in (-1, 1):
        arch = rect(-w / 2 - 0.3, 0.0, w / 2 + 0.3, 3.2) - cs_union([rect(-w / 2 + 1.4, -1, w / 2 - 1.4, 1.6), circle((0.0, 1.6), w / 2 - 1.4, 24)])
        body = body + M.extrude(arch, 1.4).translate([0, 0, -0.7]).transform(np.array([[1.0, 0, 0, 0], [0, 0, 1.0, sg * (d / 2 - 0.7)], [0, 1.0, 0, sh]]))
    tri = poly([(-d / 2 - 1.2, 0.0), (d / 2 + 1.2, 0.0), (0.0, 2.6)])
    cap = M.extrude(tri, w + 2.4).translate([0, 0, -(w + 2.4) / 2]).transform(np.array([[0, 0, 1.0, 0], [1.0, 0, 0, 0], [0, 1.0, 0, sh + 3.19]]))
    tiles = union([M.cylinder(w + 2.4, 0.5, 0.5, 12).rotate([0, 90, 0]).translate([-(w + 2.4) / 2, y, sh + 3.2 + 2.6 * (1 - abs(y) / (d / 2 + 1.2))])
                   for y in np.linspace(-d / 2, d / 2, 7)])
    flue = box([-w / 2 + 1.4, -d / 2 + 1.4, sh - 5.0], [w / 2 - 1.4, d / 2 - 1.4, sh + 3.0])
    return (body + cap + (tiles ^ box([-w, -d, sh + 3.2], [w, d, sh + 8.0]))) - flue


def garden_wall(L=34.0, h=16.0, t=2.4, gate_w=10.0, gate_h=12.0):
    """A plastered garden wall with an arched gateway at its middle, under a coping (the wall
    runs along x from 0 to L, centred on y = 0). Returns (wall, coping, gate opening cs)."""
    arch = cs_union([rect(L / 2 - gate_w / 2, 0.0, L / 2 + gate_w / 2, gate_h - gate_w / 2),
                     circle((L / 2, gate_h - gate_w / 2), gate_w / 2, 40)])
    face = rect(0.0, 0.0, L, h) + (rect(L / 2 - gate_w / 2 - 2.0, 0.0, L / 2 + gate_w / 2 + 2.0, h + 4.0))
    wall = M.extrude(face - arch, t).translate([0, 0, -t / 2]).transform(np.array([[1.0, 0, 0, 0], [0, 0, 1.0, 0], [0, 1.0, 0, 0]]))
    band = ((arch.offset(1.0, JoinType.Round) - arch) ^ rect(-1, 0.0, L + 1, h + 5))
    wall = wall + M.extrude(band, t + 0.8).translate([0, 0, -t / 2 - 0.4]).transform(np.array([[1.0, 0, 0, 0], [0, 0, 1.0, 0], [0, 1.0, 0, 0]]))
    cop = box([-0.6, -t / 2 - 0.8, h], [L + 0.6, t / 2 + 0.8, h + 0.8]) + box([L / 2 - gate_w / 2 - 2.6, -t / 2 - 0.9, h + 4.0],
                                                                              [L / 2 + gate_w / 2 + 2.6, t / 2 + 0.9, h + 4.9])
    for sg in (-1, 1):                                                          # the coping steps up the gate's shoulders
        x0 = L / 2 + sg * (gate_w / 2 + 2.0)
        a_, e_ = sorted((x0, x0 + sg * 0.6))
        cop = cop + box([a_ - (0.0 if sg > 0 else 0.0), -t / 2 - 0.8, h + 0.79], [e_, t / 2 + 0.8, h + 4.01])
    tri = poly([(-t / 2 - 1.0, 0.0), (t / 2 + 1.0, 0.0), (0.0, 1.6)])
    ridge = M.extrude(tri, gate_w + 5.2).translate([0, 0, -(gate_w + 5.2) / 2]).transform(np.array([[0, 0, 1.0, L / 2], [1.0, 0, 0, 0], [0, 1.0, 0, h + 4.6]]))
    return wall, (cop + ridge) - wall, arch


PW.POSTS.update(zapata=post_zapata)
PW.BALUSTERS.update(rejaspindle=(baluster_rejaspindle, 1.5))
PW.FRIEZES.update(mixtilinear=frieze_mixtilinear)
_FT.EDGE_EXTRA.update(tejas=edge_tejas)

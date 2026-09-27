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

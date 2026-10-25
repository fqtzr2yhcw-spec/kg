"""The new-layouts batch (houses 101 on): each house starts from a real building's plan and
massing, not from the collection's box-with-a-corner-tower. This module holds each house's own
pieces (wall skins, foundations, cornice ornaments, windows, doors, and the parts its layout
needs that no earlier house had) and registers its ornaments on import. Nothing in one house's
section is shared with another building.
"""
import math

import numpy as np
from manifold3d import JoinType, Manifold as M

from .core import RIB, box, circle, cs_union, poly, rect, union
from .ornament import chamfer_box, ext, stroke
from . import cornice as CO, moulding as MD, openings as O, trimwork as TW
from .colonial import _st
from .colonial4 import _glazed, _muntins
from .grand import _apex, _ball, _lancet, _quatrefoil, _trefoil

MIT = JoinType.Miter
RND = JoinType.Round


def _clean(cs, r=0.27):
    """Close slots and drop bars narrower than 2 r (a nozzle), keeping the outline otherwise."""
    cs = cs.offset(r, RND).offset(-r, RND)
    return cs.offset(-r, RND).offset(r, RND)


# ================================================================== the Kenmore (house 101)
# After the Wedding Cake House (Kennebunk, Maine: a Federal brick house of 1826 dressed in
# Gothic woodwork in 1852-55). A plain five-bay Federal house of painted brick under a low
# hipped roof with four end chimneys, wrapped in a Gothic skeleton that stands on its own:
# stepped buttresses between the bays rising from the ground, an openwork screen of cusped
# pointed arches hung from the eave in front of the cornice, a pinnacle over every buttress on
# the roof's edge. A Gothic entrance porch; a one-storey link with a pointed carriage arch
# through it; a gable-fronted barn dressed the same way.

def brick_kmgarden(region, datum=0.0, bl=2.6, bh=0.8, mortar=0.5, bed=0.2, d=0.25, every=4):
    """English garden-wall bond: three courses of stretchers, each broken half a brick, then a
    course of headers, over and over (the Kenmore's painted brick)."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    hl = bl / 2
    cells = []
    k = math.floor((v0 - datum) / bh) - 1
    while datum + k * bh < v1:
        v = datum + k * bh
        top = v + bh - bed
        if k % every == every - 1:
            u = u0 - 2 * bl + hl / 2
            while u < u1 + hl:
                cells.append(rect(u + mortar / 2, v, u + hl - mortar / 2, top))
                u += hl
        else:
            u = u0 - 2 * bl - (k % 2) * hl
            while u < u1 + bl:
                cells.append(rect(u + mortar / 2, v, u + bl - mortar / 2, top))
                u += bl
        k += 1
    return M.extrude(region, 0.05) + ext(cs_union(cells) ^ region, 0.0, d)


def clap_kmbarn(region, datum=0.0, pitch=1.4, d=0.55, seed=0, joint=0.6):
    """The Kenmore barn's clapboard: boards of random length butted square, every joint on a
    stud line, each board's butt standing a bold 0.55 proud along its lower edge."""
    if region.is_empty():
        return M()
    rng = np.random.default_rng(seed)
    u0, v0, u1, v1 = region.bounds()
    out = []
    k = math.floor((v0 - datum) / pitch) - 1
    while datum + k * pitch < v1:
        v = datum + k * pitch
        u = u0 - rng.uniform(0.0, 14.0)
        while u < u1:
            L = 4.8 * int(rng.integers(3, 7))
            board = rect(u + joint / 2, v, u + L - joint / 2, v + pitch) ^ region
            if not board.is_empty():
                # a wedge: d at the butt (v), 0.05 at the head
                out.append(_st(board ^ rect(u0 - 1, v, u1 + 1, v + 0.8), 0.0, d))
            u += L
        k += 1
    return M.extrude(region, 0.05) + union(out)


def foundation_kmquarry(reg, seed=0):
    """The Kenmore's base: long courses of quarry-faced granite, each block's face pitched to a
    low hump inside a drafted margin, under a chamfered water-table course."""
    u0, v0, u1, v1 = reg.bounds()
    rng = np.random.default_rng(seed)
    out = []
    ct = v1 - 1.6
    out.append(chamfer_box(u0, ct, u1, v1, 0.0, 0.7, c=0.5, square=("u0", "u1"), bottom=0.7))
    courses = [(v0, v0 + (ct - v0) * 0.55), (v0 + (ct - v0) * 0.55 + 0.4, ct - 0.4)]
    for k, (a, b) in enumerate(courses):
        u = u0 - rng.uniform(0.0, 6.0)
        while u < u1:
            L = rng.uniform(7.0, 12.0)
            x0, x1 = max(u + 0.25, u0), min(u + L - 0.25, u1)
            if x1 - x0 > 1.6:
                out.append(chamfer_box(x0, a, x1, b, 0.0, 0.35, c=0.3, bottom=0.35))
                hump = rect(x0 + 0.7, a + 0.6, x1 - 0.7, b - 0.6)
                if not hump.is_empty():
                    out.append(chamfer_box(x0 + 0.7, a + 0.6, x1 - 0.7, b - 0.6, 0.34, 0.5, c=0.3, bottom=0.5))
            u += L
    return union(out)


TW.FOUNDATION_EXTRA.update(kmquarry=foundation_kmquarry)


def _ballflower(c, r):
    """A ball flower seen face on: a ball cupped by three petals (CrossSections: petals, ball)."""
    pet = cs_union([circle((c[0] + r * 0.62 * math.cos(a), c[1] + r * 0.62 * math.sin(a)), r * 0.55, 14)
                    for a in (math.pi / 2, math.pi / 2 + 2.094, math.pi / 2 - 2.094)])
    return pet, circle(c, r * 0.42, 14)


def course_kmballflower(L, h, b, pitch, margin, p):
    """A hollow moulding studded with ball flowers (the Kenmore's eave)."""
    pu = 2.4
    n = max(1, int((L - 0.6) / pu))
    u0 = (L - n * pu) / 2
    rod = rect(0.2, 0.2, L - 0.2, h - 0.2)
    out = [_st(rod, b, 0.2)]
    r = min(0.62, h * 0.42)
    for k in range(n):
        pet, ball = _ballflower((u0 + pu * (k + 0.5), h / 2), r)
        out.append(_st(_clean(pet ^ rod), b + 0.2, 0.25))
        out.append(_st(ball ^ rod, b + 0.45, 0.25))
    return out


def frieze_kmcuspedarcade(L, h, b, pitch, margin, pair, half):
    """A blind arcade of cusped pointed arches on slender shafts, a ball flower in every
    spandrel (the Kenmore's storey joint)."""
    v0, v1 = 0.6, h - 0.6
    out = []
    span = 3.0
    n = max(1, int((L - 1.0) / span))
    ua = (L - n * span) / 2
    for k in range(n):
        u = ua + k * span
        s = span - 0.7
        ap = _apex(s)
        vs = v1 - ap - 0.3
        if vs < v0 + 0.8:
            continue
        outer = _lancet(u + 0.35, u + 0.35 + s, vs, v0=v0)
        rim = outer - outer.offset(-0.5, MIT, 4.0)
        cusp = cs_union([circle((u + 0.35 + s / 2 + sg * s * 0.36, vs + ap * 0.25), 0.36, 10) for sg in (-1, 1)])
        out.append(_st(_clean(rim + (cusp ^ outer)), b, 0.35))
        if k:
            out.append(_st(circle((u, v1 - 0.55), 0.42, 12), b, 0.4))
    return out, []


def frieze_kmfleurettes(L, h, b, pitch, margin, pair, half):
    """Four-petalled fleurettes each in a sunk square set diamond-wise, linked by a fillet
    (the barn's eave and the link)."""
    v0, v1 = 0.5, h - 0.5
    vm = (v0 + v1) / 2
    r = min((v1 - v0) / 2, 1.6)
    pu = 2 * r + 1.4
    n = max(1, int((L - 1.0) / pu))
    u0 = (L - n * pu) / 2
    out = [_st(rect(0.3, vm - 0.2, L - 0.3, vm + 0.2), b, 0.2)]
    for k in range(n):
        c = (u0 + pu * (k + 0.5), vm)
        dia = poly([(c[0], c[1] - r), (c[0] + r, c[1]), (c[0], c[1] + r), (c[0] - r, c[1])])
        out.append(_st(_clean(dia - dia.offset(-0.6, MIT, 4.0)), b, 0.35))
        pet = cs_union([circle((c[0] + dx * r * 0.3, c[1] + dy * r * 0.3), r * 0.3, 12) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))])
        out.append(_st(_clean(pet), b, 0.4))
    return out, []


CO.FRIEZE_EXTRA.update(kmcuspedarcade=frieze_kmcuspedarcade, kmfleurettes=frieze_kmfleurettes)
CO.COURSE_EXTRA.update(kmballflower=course_kmballflower)


# ------------------------------------------------------------------ the Kenmore's windows and doors
def _sash66(w, h, pl, plug_cs, cols=3, meet=0.6):
    """A six-over-six double-hung sash in its plug (the Kenmore's own: lights a little taller
    than wide, the meeting rail a shade high)."""
    inner = plug_cs.offset(-0.6, MIT, 4.0)
    u0, v0, u1, v1 = inner.bounds()
    vm = v0 + (v1 - v0) * 0.52
    lo, hi = rect(u0, v0, u1, vm - meet / 2), rect(u0, vm + meet / 2, u1, v1)
    g = lo + hi
    bars = (_muntins(lo, cols, 2) ^ lo) + (_muntins(hi, cols, 2) ^ hi)
    return _glazed([ext(plug_cs, -pl, -0.6)], g, pl, bars, plug_cs)


def _ogee_hood(X, v0, H, width=0.9, n=16):
    """An ogee label (hood mould) band over a head of half-width X, from v0 rising H to its
    point: a CrossSection band ``width`` wide."""
    from .grand import _ogee
    right = _ogee(X, v0, H, n)
    line = [(-x, y) for x, y in reversed(right[:-1])] + right
    return stroke(line, width)


def window_kmlower(w=9.0, h=18.0, A=0.8):
    """The Kenmore's ground-storey window: a six-over-six sash in a moulded architrave, under an
    ogee label rising to a crocket finial, the label ending on square stops carved with a
    quatrefoil; a sill on two little corbels."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    sash = _sash66(w, h, pl, plug_cs)
    X = w / 2 + A
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             MD.band(op.offset(A, MIT, 4.0), A, MD.ARCHITRAVE, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op)]
    vh = h + A + 0.3
    H = 4.2
    hood = _ogee_hood(X + 0.4, vh, H) ^ rect(-50, vh - 0.6, 50, 100)
    parts.append(ext(hood, 0.0, 1.0))
    parts.append(chamfer_box(-0.55, vh + H - 0.2, 0.55, vh + H + 1.6, 0.0, 1.0, c=0.3))          # the finial
    parts.append(ext(circle((0.0, vh + H + 1.9), 0.55, 12), 0.0, 1.0))
    for sg in (-1, 1):
        cx = sg * (X + 0.4)
        parts.append(chamfer_box(cx - 0.9, vh - 1.8, cx + 0.9, vh, 0.0, 1.1, c=0.3, bottom=0.8))
        parts.append(_st(_quatrefoil((cx, vh - 0.9), 0.32), 1.1, 0.25))
    parts.append(chamfer_box(-X - 0.6, -1.0, X + 0.6, 0.01, 0.0, 1.2, c=0.3, bottom=1.2))
    for sg in (-1, 1):
        parts.append(chamfer_box(sg * (X - 0.4) - 0.6, -2.6, sg * (X - 0.4) + 0.6, -0.99, 0.0, 1.0, c=0.3, bottom=1.0))
    return O._one_piece(sash, parts, op, plug_cs, pl, vh + H + 2.5, -2.6)


def window_kmupper(w=9.0, h=16.0, A=0.7):
    """The Kenmore's upper window: a six-over-six sash in a plain casing under a steep Gothic
    gablet whose sunk tympanum holds a trefoil, a little pinnacle-stop at each foot; a plain
    sill."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    sash = _sash66(w, h, pl, plug_cs)
    X = w / 2 + A
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             MD.band(op.offset(A, MIT, 4.0), A, MD.CASING, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op)]
    vg = h + A - 0.01
    G = 4.8
    tri = poly([(-X - 0.6, vg), (X + 0.6, vg), (0.0, vg + G)])
    parts.append(ext(tri, 0.0, 0.8) - ext(tri.offset(-0.7, MIT, 4.0), 0.4, 1.0))
    parts.append(_st(_trefoil((0.0, vg + G * 0.36), 0.5), 0.4, 0.35))
    for sg in (-1, 1):
        cx = sg * (X + 0.2)
        parts.append(chamfer_box(cx - 0.6, vg - 1.4, cx + 0.6, vg + 1.4, 0.0, 1.1, c=0.3, bottom=0.8))
    parts.append(chamfer_box(-0.5, vg + G - 0.6, 0.5, vg + G + 1.4, 0.0, 0.9, c=0.3))
    parts.append(chamfer_box(-X - 0.5, -1.0, X + 0.5, 0.01, 0.0, 1.1, c=0.3, bottom=1.1))
    return O._one_piece(sash, parts, op, plug_cs, pl, vg + G + 1.6, -1.0)


def window_kmcentre(wc=8.0, ws=3.0, h=17.0, A=0.7):
    """The window over the porch: a pointed centre light with Y-tracery between two narrow
    flat-headed side lights, slender shafts between them, under one ogee label."""
    W = wc + 2 * ws + 2 * 1.2
    ap = _apex(wc)
    vs = h - ap
    hs = vs
    op = cs_union([_lancet(-wc / 2, wc / 2, vs), rect(-W / 2, 0.0, W / 2, hs)])
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    inner = plug_cs.offset(-0.5, MIT, 4.0)
    mull = cs_union([rect(sg * (wc / 2 + 0.6) - 0.6, -1.0, sg * (wc / 2 + 0.6) + 0.6, hs + 0.1) for sg in (-1, 1)])
    bars = [mull, rect(-W, hs * 0.5 - RIB / 2, W, hs * 0.5 + RIB / 2), rect(-RIB / 2, -1.0, RIB / 2, vs + ap * 0.35)]
    bars.append(stroke([(0.0, vs + ap * 0.35), (-wc / 2 + 0.3, h + 0.5)], RIB))
    bars.append(stroke([(0.0, vs + ap * 0.35), (wc / 2 - 0.3, h + 0.5)], RIB))
    sash = _glazed([ext(plug_cs, -pl, -0.6)], inner, pl, cs_union(bars), plug_cs)
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             MD.band(op.offset(A, MIT, 4.0), A, MD.CASING, clip=rect(-W - 10, 0.0, W + 10, h + 40) - op)]
    for sg in (-1, 1):
        x = sg * (wc / 2 + 0.6)
        parts.append(ext(circle((x, hs / 2), 0.55, 14) + rect(x - 0.45, 0.0, x + 0.45, hs), 0.0, 0.9))
    X = W / 2 + A
    hood = _ogee_hood(X + 0.3, hs + A + 0.2, h - hs + 3.4) ^ rect(-50, hs + A - 0.4, 50, 100)
    parts.append(ext(hood, 0.0, 1.0))
    parts.append(chamfer_box(-X - 0.6, -1.0, X + 0.6, 0.01, 0.0, 1.2, c=0.3, bottom=1.2))
    return O._one_piece(sash, parts, op, plug_cs, pl, h + A + 4.4, -1.0)


def _leaf_gothic(u0, u1, v0, v1, pl, rows=3):
    """A door leaf of pointed-headed panels (two columns, ``rows`` rows) in raised frames."""
    w = u1 - u0
    out = [ext(rect(u0, v0, u1, v1), -pl, 0.0)]
    cols = 2
    mw = 0.7
    pw = (w - (cols + 1) * mw) / cols
    ph = (v1 - v0 - (rows + 1) * mw) / rows
    for i in range(cols):
        for j in range(rows):
            a = u0 + mw + i * (pw + mw)
            vb = v0 + mw + j * (ph + mw)
            vs_ = vb + ph - _apex(pw) - 0.1
            pan = _lancet(a, a + pw, vs_, v0=vb) if vs_ > vb + 1.0 else rect(a, vb, a + pw, vb + ph)
            out.append(ext(pan - pan.offset(-0.4, MIT, 4.0), 0.0, 0.4))
            out.append(ext(pan.offset(-0.8, MIT, 4.0), 0.0, 0.3))
    return out


def door_kenmore(w=10.0, h=26.0, side=2.4, A=1.0, back=False):
    """The Kenmore's front door: a leaf of six pointed-headed panels between sidelights glazed
    in lancets, under a pointed transom of intersecting tracery spanning all three, the whole in
    a moulded pointed architrave with a crocketed label. The back door (``back``) has no
    sidelights and a plain pointed transom."""
    sd = 0.0 if back else side + 0.7
    W = w + 2 * sd
    ap = _apex(W)
    hd = h - ap
    op = _lancet(-W / 2, W / 2, hd)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    leaf_top = hd - 0.4
    sash_parts = _leaf_gothic(-w / 2, w / 2, 0.0, leaf_top, pl)
    sash_parts.append(ext(plug_cs - plug_cs.offset(-0.5, MIT, 4.0), -pl, 0.0))
    trans = op ^ rect(-W, leaf_top - 0.01, W, h + 1)
    trans_in = trans.offset(-0.5, MIT, 4.0)
    tb = [rect(-W, hd - 0.4, W, hd + 0.4)]
    if not back:
        for sg in (-1, 1):
            u0, u1 = sorted((sg * w / 2, sg * W / 2))
            lt = rect(u0 + 0.5, 0.6, u1 - 0.5, leaf_top - 0.6)
            sash_parts += [ext(rect(u0, 0.0, u1, leaf_top), -pl, -0.6) - ext(lt, -pl - 1, 0.0), ext(lt, -pl, -pl + O.GLASS)]
            sash_parts.append(ext(rect(u0, leaf_top * 0.5 - RIB / 2, u1, leaf_top * 0.5 + RIB / 2) ^ lt, -pl + O.GLASS - 0.01, -0.5))
        tb += [stroke([(x, hd), (x + W * 0.3, h + 1.0)], RIB) for x in np.linspace(-W / 2, W / 2 - W * 0.3, 4)]
        tb += [stroke([(x, hd), (x - W * 0.3, h + 1.0)], RIB) for x in np.linspace(-W / 2 + W * 0.3, W / 2, 4)]
    else:
        tb += [rect(-RIB / 2, hd, RIB / 2, h + 1)]
    sash_parts += [ext(trans, -pl, -0.6) - ext(trans_in, -pl - 1, 0.0), ext(trans_in, -pl, -pl + O.GLASS),
                   ext(cs_union(tb) ^ trans_in.offset(0.1, MIT, 4.0), -pl + O.GLASS - 0.01, -0.5)]
    sash_parts = [m ^ ext(plug_cs, -pl - 1.0, 1.0) for m in sash_parts]
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             MD.band(op.offset(A, MIT, 4.0), A, MD.ARCHITRAVE, clip=rect(-W - 10, 0.0, W + 10, h + 40) - op)]
    X = W / 2 + A
    lab = (_lancet(-X - 0.3, X + 0.3, hd + 0.3) - _lancet(-X + 0.6, X - 0.6, hd + 0.3)) ^ rect(-50, hd + 0.3, 50, 100)
    parts.append(ext(lab, 0.0, 1.1))
    if not back:
        parts.append(chamfer_box(-0.6, h + A + 0.4, 0.6, h + A + 2.6, 0.0, 1.1, c=0.3))
    for sg in (-1, 1):
        parts.append(chamfer_box(sg * (X + 0.3) - 0.9, hd - 1.6, sg * (X + 0.3) + 0.9, hd + 0.31, 0.0, 1.2, c=0.3, bottom=0.8))
    return O._one_piece(sash_parts, parts, op, plug_cs, pl, h + A + 2.8, 0.0)


def window_kmlancet(w=6.0, h=22.0, A=0.7):
    """The barn's lancet: a pointed light with a Y-mullion in its head and one glazing bar
    across, in a chamfered casing under a label ending on round stops."""
    ap = _apex(w)
    vs = h - ap
    op = _lancet(-w / 2, w / 2, vs)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    inner = plug_cs.offset(-0.5, MIT, 4.0)
    bars = [rect(-RIB / 2, -1.0, RIB / 2, vs + ap * 0.3), rect(-w, vs * 0.5 - RIB / 2, w, vs * 0.5 + RIB / 2),
            stroke([(0.0, vs + ap * 0.3), (-w / 2 + 0.3, h + 0.4)], RIB), stroke([(0.0, vs + ap * 0.3), (w / 2 - 0.3, h + 0.4)], RIB)]
    sash = _glazed([ext(plug_cs, -pl, -0.6)], inner, pl, cs_union(bars), plug_cs)
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             MD.band(op.offset(A, MIT, 4.0), A, MD.CASING, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op)]
    X = w / 2 + A
    lab = (_lancet(-X - 0.2, X + 0.2, vs) - _lancet(-X + 0.6, X - 0.6, vs)) ^ rect(-50, vs, 50, 100)
    parts.append(ext(lab, 0.0, 1.0))
    for sg in (-1, 1):
        parts.append(ext(circle((sg * (X - 0.2), vs - 0.4), 0.7, 14), 0.0, 1.1))
    parts.append(chamfer_box(-X - 0.4, -1.0, X + 0.4, 0.01, 0.0, 1.1, c=0.3, bottom=1.1))
    return O._one_piece(sash, parts, op, plug_cs, pl, h + A + 0.8, -1.0)


def _boards(u0, u1, v0, v1, pl, pitch=1.6):
    """A boarded leaf: vertical boards with V-joints, in its plug."""
    out = [ext(rect(u0, v0, u1, v1), -pl, 0.0)]
    grooves = cs_union([rect(u - 0.3, v0 + 0.3, u + 0.3, v1 - 0.3) for u in np.arange(u0 + pitch, u1 - 0.5, pitch)])
    return out, grooves


def door_kmhay(w=26.0, h=40.0, A=1.2):
    """The barn's great door: two boarded leaves in a pointed opening, each hung on three strap
    hinges ending in fleurs, a pointed archivolt of two chamfered orders round it, a label over
    all with carved head stops."""
    ap = _apex(w)
    vs = h - ap
    op = _lancet(-w / 2, w / 2, vs)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    leaf = plug_cs
    body, grooves = _boards(-w / 2, w / 2, -1.0, h + 1.0, pl)
    sash = [ext(leaf, -pl, 0.0) - ext((grooves + rect(-0.35, 0.0, 0.35, h + 1.0)) ^ leaf.offset(-0.6, MIT, 4.0), -0.3, 0.1)]
    straps = []
    for v in (h * 0.15, vs * 0.55, vs * 0.92):
        for sg in (-1, 1):
            x0, x1 = sorted((sg * 0.6, sg * (w / 2 - 1.0)))
            straps.append(rect(x0, v - 0.5, x1, v + 0.5))
            tip = sg * 0.9
            straps.append(_trefoil((tip, v), 0.45))
    st = cs_union(straps) ^ leaf.offset(-0.4, MIT, 4.0)
    sash.append(ext(st, -0.02, 0.35))
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS)]
    o1 = op.offset(A, MIT, 4.0) ^ rect(-50, 0.0, 50, 200)
    o2 = op.offset(2 * A + 0.4, MIT, 4.0) ^ rect(-50, 0.0, 50, 200)
    parts.append(ext(o1 - op, 0.0, 1.0) - ext(o1.offset(-A * 0.5, MIT, 4.0) - op, 0.7, 1.2))
    parts.append(ext(o2 - o1.offset(-0.01, MIT, 4.0), 0.0, 0.7))
    X = w / 2 + 2 * A + 0.4
    lab = (_lancet(-X - 0.9, X + 0.9, vs) - _lancet(-X, X, vs)) ^ rect(-50, vs, 50, 200)
    parts.append(ext(lab, 0.0, 1.2))
    for sg in (-1, 1):
        parts.append(chamfer_box(sg * (X + 0.45) - 1.1, vs - 2.2, sg * (X + 0.45) + 1.1, vs + 0.01, 0.0, 1.3, c=0.4, bottom=0.9))
    return O._one_piece(sash, parts, op, plug_cs, pl, h + 2 * A + 2.0, 0.0)


def door_kmsmall(w=12.0, h=22.0, A=0.9):
    """The barn's loft door and back door: one boarded pointed leaf with two fleur straps in a
    chamfered pointed casing under a plain label."""
    ap = _apex(w)
    vs = h - ap
    op = _lancet(-w / 2, w / 2, vs)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    leaf = plug_cs
    body, grooves = _boards(-w / 2, w / 2, -1.0, h + 1.0, pl)
    sash = [ext(leaf, -pl, 0.0) - ext(grooves ^ leaf.offset(-0.6, MIT, 4.0), -0.3, 0.1)]
    straps = []
    for v in (h * 0.2, vs * 0.85):
        straps.append(rect(-w / 2 + 0.8, v - 0.45, w / 2 - 2.0, v + 0.45))
        straps.append(_trefoil((w / 2 - 2.0, v), 0.42))
    sash.append(ext(cs_union(straps) ^ leaf.offset(-0.4, MIT, 4.0), -0.02, 0.35))
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             MD.band(op.offset(A, MIT, 4.0), A, MD.CASING, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op)]
    X = w / 2 + A
    lab = (_lancet(-X - 0.2, X + 0.2, vs) - _lancet(-X + 0.6, X - 0.6, vs)) ^ rect(-50, vs, 50, 100)
    parts.append(ext(lab, 0.0, 1.0))
    return O._one_piece(sash, parts, op, plug_cs, pl, h + A + 0.8, 0.0)


def arch_kmcarriage(w=20.0, spring=16.0, depth=8.0, A=1.4, k=0.7):
    """The link's carriage arch: a drop arch (struck from radius k x the span) of two chamfered
    orders on moulded imposts, and a reveal lining the opening right through the wall (no glass,
    no leaf)."""
    op = _lancet(-w / 2, w / 2, spring, r=w * k)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = depth
    lining = plug_cs - plug_cs.offset(-0.9, MIT, 4.0)
    lining = lining - rect(-50, -5, 50, 0.6)
    sash = [ext(lining, -pl, 0.0)]
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS)]
    o1 = op.offset(A, MIT, 4.0) ^ rect(-50, 0.0, 50, 200)
    o2 = op.offset(2 * A + 0.4, MIT, 4.0) ^ rect(-50, 0.0, 50, 200)
    parts.append(ext(o1 - op, 0.0, 1.2) - ext(o1.offset(-A * 0.5, MIT, 4.0) - op, 0.8, 1.4))
    parts.append(ext(o2 - o1.offset(-0.01, MIT, 4.0), 0.0, 0.8))
    X = w / 2 + 2 * A + 0.4
    for sg in (-1, 1):
        parts.append(chamfer_box(sg * (w / 2 + A) - A - 0.4, spring - 1.2, sg * (w / 2 + A) + A + 0.4, spring + 0.01, 0.0, 1.4, c=0.4, bottom=1.0))
    lab = (_lancet(-X - 0.9, X + 0.9, spring, r=(2 * X + 1.8) * k) - _lancet(-X, X, spring, r=2 * X * k)) ^ rect(-50, spring, 50, 200)
    parts.append(ext(lab, 0.0, 1.2))
    return O._one_piece(sash, parts, op, plug_cs, pl, spring + _apex(2 * X + 1.8, (2 * X + 1.8) * k) + 1.0, 0.0)


# ------------------------------------------------------------------ the Kenmore's Gothic skeleton
def buttress_kenmore(v_top, w0=5.0, d0=5.6, stages=((0.0, 5.6, 5.0), (28.0, 4.4, 4.4), (58.0, 3.2, 3.8)), plinth=4.0):
    """A stepped buttress in its facade frame (u across centred on 0, v up from the ground, w out
    from the wall face): a chamfered plinth, then stages each narrower and shallower, every
    stage stepping back on a sloped wash, a blind cusped lancet sunk in the lowest stage, a sunk
    trefoil in the second, a quatrefoil in the third, a gablet on the top. Its back is flat on
    the wall (w = 0): it prints lying on its back, the washes and carving face up."""
    parts = []
    st = list(stages) + [(v_top, 0.0, 0.0)]
    wash = 1.6
    for i, (v0, d, ww) in enumerate(st[:-1]):
        v1 = st[i + 1][0]
        top = v1 - wash if i < len(st) - 2 else v_top - 3.0
        parts.append(box([-ww / 2, v0, 0.0], [ww / 2, top, d]))
        if i < len(st) - 2:
            dn = st[i + 1][1]
            # the wash: from depth d at v1 - wash up to dn at v1
            parts.append(M.hull_points([(sg * ww / 2, v1 - wash, w) for sg in (-1, 1) for w in (0.0, d)] +
                                       [(sg * ww / 2, v1, w) for sg in (-1, 1) for w in (0.0, dn)]))
    # the plinth: wider and deeper, its top chamfered back to the first stage
    d1, ww1 = st[0][1], st[0][2]
    parts.append(M.hull_points([(sg * (ww1 / 2 + 0.6), 0.0, w) for sg in (-1, 1) for w in (0.0, d1 + 0.8)] +
                               [(sg * (ww1 / 2 + 0.6), plinth - 1.0, w) for sg in (-1, 1) for w in (0.0, d1 + 0.8)] +
                               [(sg * ww1 / 2, plinth, w) for sg in (-1, 1) for w in (0.0, d1)]))
    # the gablet on the top stage
    vt, dt, wt = st[-2]
    vg = v_top - 3.0
    parts.append(M.hull_points([(sg * wt / 2, vg, w) for sg in (-1, 1) for w in (0.0, dt)] +
                               [(0.0, v_top, w) for w in (0.0, dt)]))
    body = union(parts)
    # carving, sunk 0.3 into each stage's face
    cuts = []
    (va, da, wa), (vb, db, wb), (vc, dc, wc) = stages
    s = wa - 2.0
    lan = _lancet(-s / 2, s / 2, vb - 7.0 - _apex(s), v0=plinth + 3.0)
    cusp = cs_union([circle((sg * s * 0.36, vb - 7.0 - _apex(s) * 0.75), 0.32, 10) for sg in (-1, 1)])
    cuts.append(ext(lan - cusp, da - 0.35, da + 1.0))
    cuts.append(ext(_trefoil((0.0, (vb + vc) / 2 + 2.0), 0.55), db - 0.35, db + 1.0))
    cuts.append(ext(_quatrefoil((0.0, vc + 6.0), 0.5), dc - 0.35, dc + 1.0))
    return body - union(cuts)


def screen_kenmore(L, H, stations, t=1.2, drop=0.8, big_drop=1.6):
    """The Kenmore's openwork screen in its facade frame (u along the wall from 0 to L, v down
    from its top at v = 0 to -H; extruded from w = 0 to t): a band along the top, pointed arches
    hanging from it, each cusped into a trefoil head, little drops at the springings and a long
    pendant at every buttress ``station``; pierced quatrefoils in the spandrels. Every piece is
    joined to the band. Prints flat, face up."""
    band_h = 1.6
    vs = -H + 2.4                       # the arches spring here
    solid = [rect(0.0, -band_h, L, 0.0)]
    holes = []
    # arch bays: two per buttress interval
    edges = sorted(set([0.0, L] + [s for s in stations if 0.5 < s < L - 0.5]))
    cuts = []
    for a, b in zip(edges[:-1], edges[1:]):
        n = max(1, int(round((b - a) / 11.0)))
        for k in range(n + 1):
            cuts.append(a + (b - a) * k / n)
    cuts = sorted(set([round(c, 3) for c in cuts]))
    for a, b in zip(cuts[:-1], cuts[1:]):
        s = b - a
        if s < 3.0:
            continue
        # the spandrel field between the springing line and the band, the arch cut out of it
        field = rect(a, vs, b, -band_h + 0.01)
        apx = _apex(s - 1.0)
        top = min(-band_h - 0.8, vs + apx)
        R = s - 1.0
        ys0 = top - apx                                   # the arch's springing
        arch = _lancet(a + 0.5, b - 0.5, ys0, v0=vs - 5.0)
        vc = top - apx * 0.32                             # the cusps' height
        hwc = math.sqrt(max(0.0, R * R - (vc - ys0) ** 2)) - R / 2
        cusp = cs_union([circle((a + 0.5 + R / 2 + sg * (hwc + 0.15), vc), 0.8, 14) for sg in (-1, 1)])
        solid.append((field - arch) + (cusp ^ (field + arch)))
        # a pierced quatrefoil low in each spandrel
        if s > 9.0:
            for uc in (a + 1.45, b - 1.45):
                holes.append(_quatrefoil((uc, vs + 1.2), 0.3))
    # drops at every springing, long pendants at the stations
    for c in cuts:
        big = any(abs(c - s) < 0.6 for s in stations)
        hw = 0.8 if big else 0.55
        dv = big_drop * 2.6 if big else drop
        dp = rect(c - hw, vs - dv, c + hw, vs + 0.5)
        tip = poly([(c - hw, vs - dv + 0.01), (c + hw, vs - dv + 0.01), (c, vs - dv - (1.4 if big else 0.8))])
        solid.append(dp + tip)
    cs = cs_union(solid) - cs_union(holes) if holes else cs_union(solid)
    cs = _clean(cs ^ rect(-0.01, -H - 10, L + 0.01, 0.01))
    cs = cs_union([pc for pc in cs.decompose() if pc.area() > 1.0])
    return M.extrude(cs, t)


def pinnacle_kenmore(base=4.2, h_ped=6.0, h_shaft=4.0, h_spire=11.0, peg=1.6):
    """A crocketed pinnacle (stands on its base, prints upright): a square pedestal with a little
    gablet sunk on each face, a shaft with a sunk lancet on each face, a square spire with three
    tiers of crockets on its arrises, a finial knob. A square socket in its foot drops over a
    boss on its seat."""
    parts = []
    parts.append(box([-base / 2, -base / 2, 0.0], [base / 2, base / 2, h_ped]))
    sh = base - 0.8
    z1 = h_ped
    parts.append(M.hull_points([(sx * base / 2, sy * base / 2, z1) for sx in (-1, 1) for sy in (-1, 1)] +
                               [(sx * sh / 2, sy * sh / 2, z1 + 0.4) for sx in (-1, 1) for sy in (-1, 1)]))
    z2 = z1 + 0.4 + h_shaft
    parts.append(box([-sh / 2, -sh / 2, z1 + 0.39], [sh / 2, sh / 2, z2]))
    # a little cap ring, then the spire
    parts.append(M.hull_points([(sx * sh / 2, sy * sh / 2, z2 - 0.01) for sx in (-1, 1) for sy in (-1, 1)] +
                               [(sx * (sh / 2 + 0.3), sy * (sh / 2 + 0.3), z2 + 0.3) for sx in (-1, 1) for sy in (-1, 1)] +
                               [(sx * (sh / 2 + 0.3), sy * (sh / 2 + 0.3), z2 + 0.7) for sx in (-1, 1) for sy in (-1, 1)]))
    z3 = z2 + 0.7
    sp = sh / 2 + 0.1
    parts.append(M.hull_points([(sx * sp, sy * sp, z3 - 0.01) for sx in (-1, 1) for sy in (-1, 1)] + [(0.0, 0.0, z3 + h_spire)]))
    for t_ in (0.22, 0.5, 0.76):
        zc = z3 + h_spire * t_
        r = sp * (1 - t_)
        for sx in (-1, 1):
            for sy in (-1, 1):
                c = (sx * (r + 0.15), sy * (r + 0.15))
                # a crocket: a knob whose underside slopes at 45 degrees back into the arris
                parts.append(M.hull_points([(c[0] * 0.6, c[1] * 0.6, zc - 0.9), (c[0], c[1], zc), (c[0], c[1], zc + 0.5),
                                            (c[0] * 0.6, c[1] * 0.6, zc + 0.8)]
                                           + [(c[0] + dx, c[1] + dy, zc + 0.25) for dx, dy in ((0.35, 0), (-0.35, 0), (0, 0.35), (0, -0.35))]))
    parts.append(_ball(0.62, z3 + h_spire + 0.3, neck=0.3))
    body = union(parts)
    cuts = []
    for ang in (0, 90, 180, 270):
        g = poly([(-1.1, 1.6), (1.1, 1.6), (0.0, 4.4)])
        gl = M.extrude(g, 1.0).transform([[1, 0, 0, 0], [0, 0, -1, base / 2 + 0.55], [0, 1, 0, 0]])
        lan = _lancet(-0.55, 0.55, z1 + 0.4 + h_shaft * 0.62, v0=z1 + 1.2)
        ln = M.extrude(lan, 1.0).transform([[1, 0, 0, 0], [0, 0, -1, sh / 2 + 0.55], [0, 1, 0, 0]])
        cuts.append((gl + ln).rotate([0, 0, ang]))
    body = body - union(cuts)
    if peg:
        s_ = peg / 2 + 0.12
        body = body - box([-s_, -s_, -1.0], [s_, s_, 1.4])
    return body


def chimney_kenmore(w, d, h, cap=2.4):
    """The Kenmore's end stacks: plain brick with a sunk pointed panel on each broad face, a
    corbel table of three projecting courses, a stone cap and two square pots."""
    body = box([-w / 2, -d / 2, 0.0], [w / 2, d / 2, h])
    zc = h - cap - 1.8
    rings = []
    for k, o in enumerate((0.25, 0.5, 0.75)):
        z = zc + k * 0.6
        rings.append(M.hull_points([(sx * (w / 2 + o - 0.25), sy * (d / 2 + o - 0.25), z) for sx in (-1, 1) for sy in (-1, 1)] +
                                   [(sx * (w / 2 + o), sy * (d / 2 + o), z + 0.25) for sx in (-1, 1) for sy in (-1, 1)] +
                                   [(sx * (w / 2 + o), sy * (d / 2 + o), z + 0.6) for sx in (-1, 1) for sy in (-1, 1)]))
    capb = box([-w / 2 - 1.0, -d / 2 - 1.0, h - cap + 0.01], [w / 2 + 1.0, d / 2 + 1.0, h])
    m = union([body] + rings + [capb])
    for sx in (-1, 1):
        pc = (sx * w / 4, 0.0)
        m = m + (box([pc[0] - 1.2, -1.2, h - 0.01], [pc[0] + 1.2, 1.2, h + 3.2]) - box([pc[0] - 0.6, -0.6, h + 1.0], [pc[0] + 0.6, 0.6, h + 3.4]))
    pan = _lancet(-w * 0.18, w * 0.18, zc - 3.0 - _apex(w * 0.36), v0=zc - 16.0)
    for y0 in (d / 2 - 0.5, -d / 2 - 0.7):
        m = m - M.extrude(pan, 1.2).transform([[1, 0, 0, 0], [0, 0, 1, y0], [0, 1, 0, 0]])
    return m


def barge_kenmore(L, slope, d_eave, skin=1.8, width=3.8, d=2.2):
    """The barn's bargeboards (facade frame; place at w = rake): a board down each rake whose
    lower edge is cut into a row of cusped pointed arches hanging between little drops, a
    pierced trefoil over every arch, a king post at the apex carrying a long pendant, and a
    spire over the apex. Every piece is joined to the board."""
    from .gables import _text
    s = slope
    c = math.hypot(1.0, s)
    a_l, a_r = np.array([-d_eave, 0.0]), np.array([L + d_eave, 0.0])
    tip = np.array([L / 2, s * (L / 2 + d_eave)])
    depth = skin + width
    band, cuts, holes = [], [], []
    run = float(np.linalg.norm(tip - a_l))
    n_s = max(4, int(run / 4.6))
    for a in (a_l, a_r):
        n = np.array([s, -1.0]) / c if a[0] < L / 2 else np.array([-s, -1.0]) / c
        band.append(poly([tuple(a), tuple(tip), tuple(tip + n * depth), tuple(a + n * depth)]))
        dirv = (tip - a) / np.linalg.norm(tip - a)
        step = run / n_s
        for k in range(1, n_s - 1):
            t0, t1 = step * k + 0.5, step * (k + 1) - 0.5
            sp = t1 - t0
            ah = min(width - 1.2, _apex(sp) + 0.8)
            arch = _lancet(t0, t1, ah - _apex(sp), v0=-2.0)
            cusp = cs_union([circle(((t0 + t1) / 2 + sg * sp * 0.3, ah - _apex(sp) * 0.55), sp * 0.13, 10) for sg in (-1, 1)])
            loc = arch - cusp
            # (t, h) -> facade: along the rake by t, up from the board's lower edge by h
            pts = [tuple(a + dirv * t_ + n * (depth - h_)) for t_, h_ in loc.to_polygons()[0]] if loc.to_polygons() else []
            if len(pts) > 2:
                cuts.append(poly(pts))
            cc = a + dirv * ((t0 + t1) / 2) + n * (skin + 0.95)
            holes.append(_trefoil(tuple(cc), 0.38))
    board = cs_union(band) ^ rect(-d_eave - 5, -0.01, L + d_eave + 5, tip[1] + 5)
    board = board - cs_union(cuts) - cs_union(holes)
    kp = rect(L / 2 - 1.3, tip[1] - depth * c - 2.0, L / 2 + 1.3, tip[1])
    pend = poly([(L / 2 - 1.3, tip[1] - depth * c - 2.0), (L / 2 + 1.3, tip[1] - depth * c - 2.0), (L / 2, tip[1] - depth * c - 5.0)])
    spire = poly([(L / 2 - 1.2, tip[1] - 0.5), (L / 2 + 1.2, tip[1] - 0.5), (L / 2, tip[1] + 7.0)])
    board = _clean(board + kp + pend + spire + circle((L / 2, tip[1] + 0.6), 1.1, 16))
    board = cs_union([pc for pc in board.decompose() if pc.area() > 2.0])
    return _text(board, 0.0, d)


def cupola_kenmore(w=14.0, h=18.0, post=1.8):
    """The barn's ventilator (stands on its foot, prints upright): a square body with a corner
    post at each angle, a pointed louvred opening in every face (slats sloping down and out at
    45 degrees), a plinth at its foot and a cornice stepping out at 45 degrees at its head."""
    hw = w / 2
    body = box([-hw, -hw, 0.0], [hw, hw, h])
    zc = h - 2.0
    cor = M.hull_points([(sx * hw, sy * hw, zc - 0.01) for sx in (-1, 1) for sy in (-1, 1)] +
                        [(sx * (hw + 1.0), sy * (hw + 1.0), zc + 1.0) for sx in (-1, 1) for sy in (-1, 1)] +
                        [(sx * (hw + 1.0), sy * (hw + 1.0), h) for sx in (-1, 1) for sy in (-1, 1)])
    plinth = box([-hw - 0.6, -hw - 0.6, 0.0], [hw + 0.6, hw + 0.6, 1.6]) + \
        M.hull_points([(sx * (hw + 0.6), sy * (hw + 0.6), 1.59) for sx in (-1, 1) for sy in (-1, 1)] +
                      [(sx * hw, sy * hw, 2.2) for sx in (-1, 1) for sy in (-1, 1)])
    m = body + cor + plinth
    ow = w - 2 * post - 0.8
    v0, vt = 3.0, zc - 1.2
    op = _lancet(-ow / 2, ow / 2, vt - _apex(ow), v0=v0)
    depth = 1.6
    rec = M.extrude(op, depth + 0.01)
    slats = []
    for v in np.arange(v0 + 0.9, vt - 0.6, 1.6):
        slats.append(M.hull_points([(u, 0.0, v) for u in (-ow, ow)] + [(u, 0.0, v + 0.8) for u in (-ow, ow)] +
                                   [(u, depth, v + depth) for u in (-ow, ow)] + [(u, depth, v + depth + 0.8) for u in (-ow, ow)]))
    vs_ = vt - _apex(ow)
    sl = union(slats) ^ M.extrude(op.offset(-0.3, MIT, 4.0) ^ rect(-50, 0.0, 50, vs_), 4.0).transform([[1, 0, 0, 0], [0, 0, 1, -0.5], [0, 1, 0, 0]])
    for ang in (0, 90, 180, 270):
        # the recess, cut into the -y face, then the slats in it
        A = [[1, 0, 0, 0], [0, 0, 1, -hw - 0.01], [0, 1, 0, 0]]
        r_ = rec.transform(A).rotate([0, 0, ang])
        m = m - r_
        m = m + sl.translate([0, -hw - 0.0, 0]).rotate([0, 0, ang])
    return m


def porch_kenmore(x0, x1, yf, zd, z_cap, slope=1.6):
    """The Kenmore's porch top, in world coordinates, one piece printed upright: two clustered
    shafts on plinths with moulded capitals, a front arch with cusps under a steep gable raised
    above the roof line and dressed with crockets, a sunk quatrefoil roundel and a finial; a
    pointed arch through each side panel, the panels' backs against the wall (y = 0); a steep
    slated gable roof between them. ``yf`` = the porch's front face (y < 0)."""
    from . import roof as R
    xc = (x0 + x1) / 2
    ze = z_cap + 1.6
    parts = []
    piers = [(x0 + 1.6, yf + 0.8), (x1 - 1.6, yf + 0.8)]
    for px, py in piers:
        parts.append(box([px - 1.8, py - 1.8, zd], [px + 1.8, py + 1.8, zd + 1.6]))
        parts.append(M.hull_points([(px + sx * 1.8, py + sy * 1.8, zd + 1.59) for sx in (-1, 1) for sy in (-1, 1)] +
                                   [(px + sx * 1.3, py + sy * 1.3, zd + 2.2) for sx in (-1, 1) for sy in (-1, 1)]))
        for dx, dy, r in ((-0.7, -0.45, 0.8), (0.7, -0.45, 0.8), (0.0, 0.6, 0.8), (0.0, 0.0, 1.0)):
            parts.append(M.cylinder(z_cap - zd - 3.6, r, r, 20).translate([px + dx, py + dy, zd + 2.19]))
        parts.append(M.hull_points([(px + 1.4 * math.cos(a), py + 1.4 * math.sin(a), z_cap - 1.6) for a in np.linspace(0, 2 * math.pi, 12, endpoint=False)] +
                                   [(px + sx * 1.9, py + sy * 1.9, z_cap) for sx in (-1, 1) for sy in (-1, 1)]))
    # the front: an arch panel and the gable over it
    span = (x1 - x0) - 6.4
    apx = _apex(span)
    spring = z_cap - 1.0 - apx
    front = box([x0, yf, z_cap - 3.6], [x1, yf + 1.6, ze])
    gable = poly([(x0 - 1.2, ze - 0.01), (x1 + 1.2, ze - 0.01), (xc, ze + slope * ((x1 - x0) / 2 + 1.2) + 1.2)])
    gab = M.extrude(gable, 1.6).transform([[1, 0, 0, 0], [0, 0, 1, yf], [0, 1, 0, 0]])
    arch_cs = _lancet(x0 + 3.2, x1 - 3.2, spring, v0=zd - 1.0)
    cusp = cs_union([circle((xc + sg * span * 0.3, spring + apx * 0.42), span * 0.1, 14) for sg in (-1, 1)])
    spand = M.extrude(rect(x0 + 1.6, spring, x1 - 1.6, z_cap - 3.59), 1.6).transform([[1, 0, 0, 0], [0, 0, 1, yf], [0, 1, 0, 0]])
    hole = M.extrude(arch_cs - cusp, 4.0).transform([[1, 0, 0, 0], [0, 0, 1, yf - 1.0], [0, 1, 0, 0]])
    parts += [front - hole, spand - hole, gab]
    # crockets up both rakes, a finial at the apex
    za = ze + slope * ((x1 - x0) / 2 + 1.2) + 1.2
    for t_ in np.linspace(0.18, 0.82, 5):
        for sg in (-1, 1):
            x = xc + sg * ((x1 - x0) / 2 + 1.2) * (1 - t_)
            z = ze + (za - ze) * t_ + 0.2
            parts.append(box([-0.55, 0.0, -0.55], [0.55, 1.6, 0.55]).rotate([0, 45, 0]).translate([x, yf, z]))
    parts.append(box([xc - 0.8, yf, za - 1.0], [xc + 0.8, yf + 1.6, za + 2.6]))
    parts.append(M.hull_points([(xc + sx * 0.8, y, za + 2.59) for sx in (-1, 1) for y in (yf, yf + 1.6)] + [(xc, yf + 0.8, za + 6.0)]))
    parts.append(_ball(0.6, za + 6.3, neck=0.3).translate([xc, yf + 0.8, 0]))
    # the side panels with their arches
    for xa, xb in ((x0, x0 + 1.2), (x1 - 1.2, x1)):
        side = box([xa, yf + 1.59, zd], [xb, -0.05, ze])
        sp = (-2.4) - (yf + 3.2)
        sap = _apex(sp)
        scs = _lancet(yf + 3.2, -2.4, z_cap - 1.0 - sap, v0=zd + 2.4)
        sh = M.extrude(scs, 4.0).transform([[0, 0, 1, xa - 1.0], [1, 0, 0, 0], [0, 1, 0, 0]])
        parts.append(side - sh)
    # the roof
    outer = [(x0 - 1.2, yf + 1.59), (x1 + 1.2, yf + 1.59), (x1 + 1.2, -0.05), (x0 - 1.2, -0.05)]
    pr, pr_tex = R.hip_roof([(outer, [1, 3])], ze, slope, 0.0, texture="square", tex_kw=dict(pitch=1.6, wtab=2.0, d=0.35), zlo=ze)
    parts += [pr, pr_tex]
    m = union(parts)
    # a sunk quatrefoil roundel in the gable
    rc = (xc, ze + (za - ze) * 0.42)
    roundel = circle(rc, 2.2, 32) - _quatrefoil(rc, 0.9)
    m = m - M.extrude(roundel - circle(rc, 1.7, 32), 1.0).transform([[1, 0, 0, 0], [0, 0, 1, yf - 0.6], [0, 1, 0, 0]])
    m = m - M.extrude(circle(rc, 1.7, 32) - _quatrefoil(rc, 0.9), 1.0).transform([[1, 0, 0, 0], [0, 0, 1, yf - 0.5], [0, 1, 0, 0]])
    for px, py in piers:
        m = m - box([px - 0.92, py - 0.92, zd - 1.0], [px + 0.92, py + 0.92, zd + 1.4])
    return m


# ================================================================== the Sakonnet (house 102)
# After the Shingle Style of the 1880s on the New England shore (the W. G. Low House, Bristol RI,
# 1887, and Kragsyde, Manchester-by-the-Sea, 1883): the whole house under one great gable whose
# eaves come down to the first storey, so the upper floors live inside the roof; a ground
# storey of squared rubble with a loggia of three broad arches and a carriage arch right through
# the house; a round bay at one corner rising out of the ground and bursting through the roof
# edge under a bell cap; eyebrow dormers rolling out of the slopes; a stone terrace on boulders.
from .core import ashlar, scallop_rows                                    # noqa: E402


def shingles_sakonnet(region, datum=0.0, pitch=1.4, wtab=2.2, d=0.4):
    """The Sakonnet's shingles: square butts, every ninth course a band of diamond-pointed
    butts (no rounded scales)."""
    def shp(k, j):
        return "diamond" if k % 9 == 4 else "square"
    return scallop_rows(region, pitch, wtab, d=d, shape=shp, datum=datum) + M.extrude(region, 0.05)


def rubble_sakonnet(region, datum=0.0, seed=0):
    """The ground storey: squared rubble in courses of two heights, rock-faced, with deep joints."""
    return ashlar(region, course=(2.2, 3.4), length=(2.8, 6.4), d=0.6, seed=seed, datum=datum, rough=0.2, bevel=0.25)


def foundation_skboulders(reg, seed=0):
    """The Sakonnet's plinth: a battered course of big boulder-faced stones, each rounded at its
    corners, under a thin chamfered capping."""
    u0, v0, u1, v1 = reg.bounds()
    rng = np.random.default_rng(seed)
    out = [chamfer_box(u0, v1 - 1.0, u1, v1, 0.0, 0.5, c=0.4, square=("u0", "u1"), bottom=0.5)]
    u = u0 - rng.uniform(0.0, 5.0)
    while u < u1:
        L = rng.uniform(5.0, 9.0)
        x0, x1 = max(u + 0.3, u0), min(u + L - 0.3, u1)
        if x1 - x0 > 2.0:
            st = (rect(x0, v0, x1, v1 - 1.3).offset(-0.6, RND).offset(0.6, RND))
            out.append(_st(st, 0.0, 0.5))
            out.append(_st(st.offset(-0.8, RND), 0.5, 0.35))
        u += L
    return union(out)


TW.FOUNDATION_EXTRA.update(skboulders=foundation_skboulders)


def frieze_skdaisies(L, h, b, pitch, margin, pair, half):
    """Daisies on a wavy vine: an eight-petalled daisy in every bay, the vine dipping between
    (the Sakonnet's storey joint)."""
    v0, v1 = 0.6, h - 0.6
    vm = (v0 + v1) / 2
    out = []
    pts = [(u, vm + 0.6 * math.sin(u / max(pitch, 1.0) * 2 * math.pi)) for u in np.linspace(0.4, L - 0.4, max(8, int(L * 2)))]
    out.append(_st(_clean(stroke(pts, 0.55)), b, 0.3))
    r = min((v1 - v0) / 2, 1.5)
    for uc, wd in CO._between(L, pitch, margin, pair, half):
        if wd < 2 * r + 0.6:
            continue
        pet = cs_union([circle((uc + r * 0.62 * math.cos(a), vm + r * 0.62 * math.sin(a)), r * 0.33, 10)
                        for a in np.linspace(0, 2 * math.pi, 6, endpoint=False)])
        out.append(_st(_clean(pet), b, 0.35))
        out.append(_st(circle((uc, vm), r * 0.36, 12), b + 0.3, 0.3))
    return out, []


def course_skchevronbead(L, h, b, pitch, margin, p):
    """Little chevrons pointing along the course, a bead between each (the Sakonnet)."""
    pu = 2.0
    n = max(1, int((L - 0.6) / pu))
    u0 = (L - n * pu) / 2
    rod = rect(0.2, 0.2, L - 0.2, h - 0.2)
    out = [_st(rod, b, 0.18)]
    chev = []
    for k in range(n):
        uc = u0 + pu * k + 0.6
        chev.append(stroke([(uc, 0.35), (uc + 0.6, h / 2), (uc, h - 0.35)], 0.5))
        chev.append(circle((uc + 1.35, h / 2), 0.32, 10))
    out.append(_st(_clean(cs_union(chev) ^ rod), b + 0.18, 0.3))
    return out


CO.FRIEZE_EXTRA.update(skdaisies=frieze_skdaisies)
CO.COURSE_EXTRA.update(skchevronbead=course_skchevronbead)


def _sash_border(w, h, pl, plug_cs, n_top=4):
    """A Shingle Style sash: an upper sash of small square lights, a lower sash of one big pane."""
    inner = plug_cs.offset(-0.6, MIT, 4.0)
    u0, v0, u1, v1 = inner.bounds()
    vm = v0 + (v1 - v0) * 0.55
    lo, hi = rect(u0, v0, u1, vm - 0.35), rect(u0, vm + 0.35, u1, v1)
    rows = max(2, int(round((v1 - vm) / ((u1 - u0) / n_top))))
    bars = _muntins(hi, n_top, rows) ^ hi
    return _glazed([ext(plug_cs, -pl, -0.6)], lo + hi, pl, bars, plug_cs)


def window_sklower(w=8.0, h=15.0, A=0.8):
    """The Sakonnet's ground-storey window: small lights over one pane, in a plain casing with
    eared head and a little shingled pent hood carried on two shaped brackets; a deep sill."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    sash = _sash_border(w, h, pl, plug_cs)
    X = w / 2 + A
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             ext((op.offset(A, MIT, 4.0) - op) ^ rect(-50, 0.0, 50, 100), 0.0, 0.8)]
    parts.append(chamfer_box(-X - 0.6, h + A - 1.2, X + 0.6, h + A + 0.01, 0.0, 0.9, c=0.3, square=("v0",)))
    # the hood: a sloping shingled top over a fascia, on two brackets
    vh = h + A
    hood = poly([(-X - 1.2, vh), (X + 1.2, vh), (X + 1.2, vh + 1.0), (0.0, vh + 2.6), (-X - 1.2, vh + 1.0)])
    parts.append(ext(hood, 0.0, 1.6))
    for sg in (-1, 1):
        parts.append(ext(poly([(sg * (X + 0.2), vh), (sg * (X + 1.0), vh), (sg * (X + 0.2), vh - 2.2)]), 0.0, 1.4))
    parts.append(chamfer_box(-X - 0.8, -1.2, X + 0.8, 0.01, 0.0, 1.4, c=0.3, bottom=1.4))
    return O._one_piece(sash, parts, op, plug_cs, pl, vh + 2.8, -1.2)


def window_skbay(w=6.0, h=14.0, A=0.6):
    """The bay's windows (one to a facet): small lights over one pane, a plain casing, a sill."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    sash = _sash_border(w, h, pl, plug_cs, n_top=3)
    X = w / 2 + A
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             ext((op.offset(A, MIT, 4.0) - op) ^ rect(-50, 0.0, 50, 100), 0.0, 0.7)]
    parts.append(chamfer_box(-X - 0.4, -1.0, X + 0.4, 0.01, 0.0, 1.1, c=0.3, bottom=1.1))
    return O._one_piece(sash, parts, op, plug_cs, pl, h + A + 0.2, -1.0)


def window_skribbon(n=5, wl=12.0, h=13.0, mull=1.6, A=0.8):
    """The great gable's ribbon: ``n`` casements in one long frame, each of three lights over a
    transom of small squares, slender mullions between, one continuous shelf of a head over all
    on little blocks and one continuous sill."""
    W = n * wl + (n - 1) * mull
    lights = [rect(-W / 2 + k * (wl + mull), 0.0, -W / 2 + k * (wl + mull) + wl, h) for k in range(n)]
    op = cs_union(lights)                       # the wall keeps a pier between the lights: short bridges
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    inner = plug_cs.offset(-0.5, MIT, 4.0)
    u0, v0, u1, v1 = inner.bounds()
    vt = v1 - (v1 - v0) * 0.26
    bars = []
    bars.append(rect(-W, vt - 0.3, W, vt + 0.3))
    for k in range(n):
        x0 = -W / 2 + k * (wl + mull)
        for j in (1, 2):
            xb = x0 + wl * j / 3
            bars.append(rect(xb - RIB / 2, v0 - 1, xb + RIB / 2, vt))
        for j in range(1, 4):
            xb = x0 + wl * j / 4
            bars.append(rect(xb - RIB / 2, vt, xb + RIB / 2, v1 + 1))
    sash = _glazed([ext(plug_cs, -pl, -0.6)], inner, pl, cs_union(bars), plug_cs)
    whole = rect(-W / 2, 0.0, W / 2, h)
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             ext((whole.offset(A, MIT, 4.0) - op) ^ rect(-200, 0.0, 200, 100), 0.0, 0.8)]
    for k in range(1, n):
        x = -W / 2 + k * (wl + mull) - mull / 2
        parts.append(ext(rect(x - mull / 2 - 0.2, 0.0, x + mull / 2 + 0.2, h), 0.0, 0.9))
    X = W / 2 + A
    parts.append(chamfer_box(-X - 1.0, h + A - 0.01, X + 1.0, h + A + 1.0, 0.0, 1.6, c=0.4, bottom=0.6))
    for k in range(n + 1):
        x = -W / 2 + k * (wl + mull) - mull / 2 if 0 < k < n else (-X if k == 0 else X)
        parts.append(chamfer_box(x - 0.6, h + A - 0.8, x + 0.6, h + A + 0.01, 0.0, 1.3, c=0.3, bottom=0.8))
    parts.append(chamfer_box(-X - 0.8, -1.2, X + 0.8, 0.01, 0.0, 1.4, c=0.3, bottom=1.4))
    return O._one_piece(sash, parts, op, plug_cs, pl, h + A + 1.2, -1.2)


def door_skloggia(w=10.0, h=21.0, side=2.4, A=0.9):
    """The Sakonnet's door at the back of the loggia: a broad leaf whose upper half is glazed in
    a round-headed light of radiating bars over a carved sunburst panel, between sidelights of
    small squares, under a flat head with a row of little turned spindles."""
    W = w + 2 * (side + 0.6)
    op = rect(-W / 2, 0.0, W / 2, h)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    parts_s = [ext(plug_cs - plug_cs.offset(-0.5, MIT, 4.0), -pl, 0.0)]
    # the leaf
    leaf = rect(-w / 2, 0.0, w / 2, h - 0.6)
    parts_s.append(ext(leaf, -pl, -0.6))
    rr = (w - 2.0) / 2
    vs = h - 1.6 - rr
    glass = cs_union([rect(-rr, h * 0.5, rr, vs), circle((0.0, vs), rr, 40) ^ rect(-rr, vs, rr, vs + rr)])
    parts_s = [p - ext(glass, -pl - 1, 0.0) for p in parts_s]
    parts_s.append(ext(glass, -pl, -pl + O.GLASS))
    gb = [stroke([(1.4 * math.cos(a), vs + 1.4 * math.sin(a)), (rr * math.cos(a), vs + rr * math.sin(a))], RIB) for a in np.linspace(0.75, math.pi - 0.75, 3)]
    gb.append(circle((0.0, vs), 1.4, 24) - circle((0.0, vs), 0.8, 24))
    gb.append(rect(-rr - 1, vs - RIB / 2, -1.0, vs + RIB / 2) + rect(1.0, vs - RIB / 2, rr + 1, vs + RIB / 2))
    gb.append(rect(-RIB / 2, h * 0.5 - 1, RIB / 2, vs))
    parts_s.append(ext(cs_union(gb) ^ glass.offset(0.1, MIT, 4.0), -pl + O.GLASS - 0.01, -0.5))
    pan = rect(-w / 2 + 1.0, 1.2, w / 2 - 1.0, h * 0.5 - 1.0)
    parts_s.append(ext(pan - pan.offset(-0.45, MIT, 4.0), -0.65, -0.2))
    sun = cs_union([stroke([(0.0, 1.6), ((w / 2 - 1.6) * math.cos(a), 1.6 + (h * 0.5 - 3.4) * math.sin(a))], 0.5)
                    for a in np.linspace(0.3, math.pi - 0.3, 7)]) ^ pan.offset(-0.6, MIT, 4.0)
    parts_s.append(ext(_clean(sun), -0.65, -0.25))
    for sg in (-1, 1):
        u0, u1 = sorted((sg * (w / 2 - 0.01), sg * (W / 2 - 0.2)))
        sl = rect(u0, 0.0, u1, h - 0.6)
        lt = sl.offset(-0.5, MIT, 4.0) ^ rect(-50, h * 0.35, 50, 100)
        parts_s += [ext(sl, -pl, -0.6) - ext(lt, -pl - 1, 0.0), ext(lt, -pl, -pl + O.GLASS)]
        lb = u1 - u0
        rows = int((h - 0.6 - h * 0.35) / lb)
        bars = cs_union([rect(u0 - 1, h * 0.35 + k * lb - RIB / 2, u1 + 1, h * 0.35 + k * lb + RIB / 2) for k in range(1, rows + 1)])
        parts_s.append(ext(bars ^ lt.offset(0.1, MIT, 4.0), -pl + O.GLASS - 0.01, -0.5))
    X = W / 2 + A
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             ext((op.offset(A, MIT, 4.0) - op) ^ rect(-50, 0.0, 50, 100), 0.0, 0.9)]
    parts.append(chamfer_box(-X - 0.8, h + A - 0.01, X + 0.8, h + A + 3.0, 0.0, 0.7, c=0.3, square=("v0",)))
    for x in np.linspace(-X + 0.4, X - 0.4, 11):
        parts.append(ext(rect(x - 0.3, h + A + 0.4, x + 0.3, h + A + 2.6) + circle((x, h + A + 1.5), 0.42, 10), 0.69, 1.1))
    parts.append(chamfer_box(-X - 1.2, h + A + 2.99, X + 1.2, h + A + 3.8, 0.0, 1.4, c=0.3, bottom=0.6))
    parts_s = [m ^ ext(plug_cs, -pl - 1.0, 1.0) for m in parts_s]
    return O._one_piece(parts_s, parts, op, plug_cs, pl, h + A + 4.0, 0.0)


def window_skbalcony(w=14.0, h=13.0, A=0.6):
    """The pair of glazed doors at the back of the balcony sunk in the gable: two leaves of
    tall lights, a small-paned transom over them."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    inner = plug_cs.offset(-0.5, MIT, 4.0)
    u0, v0, u1, v1 = inner.bounds()
    vt = v1 - 2.6
    bars = [rect(-0.5, -1.0, 0.5, vt), rect(-w, vt - 0.3, w, vt + 0.3)]
    bars += [rect(x - RIB / 2, -1.0, x + RIB / 2, vt) for x in (-w / 4, w / 4)]
    bars += [rect(x - RIB / 2, vt, x + RIB / 2, h + 1) for x in np.linspace(-w / 2, w / 2, 7)[1:-1]]
    bars += [rect(-w, y - RIB / 2, w, y + RIB / 2) for y in (vt * 0.5,)]
    sash = _glazed([ext(plug_cs, -pl, -0.6)], inner, pl, cs_union(bars), plug_cs)
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             ext((op.offset(A, MIT, 4.0) - op) ^ rect(-50, 0.0, 50, 100), 0.0, 0.7)]
    return O._one_piece(sash, parts, op, plug_cs, pl, h + A, 0.0)


def window_skeyebrow(w=16.0, h=5.0):
    """The eyebrow dormer's window: a long low light under a wave-shaped head, four lights, set
    in a plain band (its plug drops into a recess in the eyebrow's face)."""
    xs = np.linspace(-w / 2, w / 2, 33)
    top = [(x, 1.2 + (h - 1.2) * math.cos(x / (w / 2) * math.pi / 2) ** 2) for x in xs]
    op = poly([(-w / 2, 0.0), (w / 2, 0.0)] + top[::-1])
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = 1.2
    inner = plug_cs.offset(-0.5, MIT, 4.0)
    bars = cs_union([rect(x - RIB / 2, -1.0, x + RIB / 2, h + 1) for x in (-w / 4, 0.0, w / 4)])
    sash = _glazed([ext(plug_cs, -pl, -0.4)], inner, pl, bars, plug_cs)
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS), ext(op.offset(0.7, MIT, 4.0) - op, 0.0, 0.6)]
    return O._one_piece(sash, parts, op, plug_cs, pl, h + 0.7, -0.7)


def window_skback(w=8.0, h=14.0, A=0.7):
    """The back gable's windows: a casement pair of three lights each over a shallow apron
    panel, in an architrave with a plain frieze and a projecting cap."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    inner = plug_cs.offset(-0.5, MIT, 4.0)
    u0, v0, u1, v1 = inner.bounds()
    bars = [rect(-0.45, -1.0, 0.45, h + 1)] + [rect(-w, v0 + (v1 - v0) * k / 3 - RIB / 2, w, v0 + (v1 - v0) * k / 3 + RIB / 2) for k in (1, 2)]
    sash = _glazed([ext(plug_cs, -pl, -0.6)], inner, pl, cs_union(bars), plug_cs)
    X = w / 2 + A
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             MD.band(op.offset(A, MIT, 4.0), A, MD.CASING, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op)]
    parts.append(chamfer_box(-X, h + A - 0.01, X, h + A + 1.6, 0.0, 0.7, c=0.25, square=("v0",)))
    parts.append(chamfer_box(-X - 0.9, h + A + 1.59, X + 0.9, h + A + 2.4, 0.0, 1.3, c=0.3, bottom=0.6))
    parts.append(chamfer_box(-X - 0.5, -2.6, X + 0.5, 0.01, 0.0, 0.8, c=0.25, bottom=0.8))
    return O._one_piece(sash, parts, op, plug_cs, pl, h + A + 2.6, -2.6)


def door_skback(w=8.4, h=20.0, A=0.8):
    """The kitchen door: four lights over two raised panels, a plain casing and a cap."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    leaf = [ext(plug_cs, -pl, -0.6), ext(plug_cs - plug_cs.offset(-0.5, MIT, 4.0), -pl, 0.0)]
    g = rect(-w / 2 + 1.0, h * 0.52, w / 2 - 1.0, h - 1.0)
    leaf = [p - ext(g, -pl - 1, 0.0) for p in leaf] + [ext(g, -pl, -pl + O.GLASS)]
    leaf.append(ext(cs_union([rect(-RIB / 2, h * 0.5, RIB / 2, h), rect(-w, h * 0.76 - RIB / 2, w, h * 0.76 + RIB / 2)]) ^ g.offset(0.1, MIT, 4.0),
                    -pl + O.GLASS - 0.01, -0.5))
    for x0 in (-w / 2 + 1.0, 0.4):
        pan = rect(x0, 1.2, x0 + w / 2 - 1.4, h * 0.52 - 1.2)
        leaf.append(ext(pan.offset(-0.6, MIT, 4.0), -0.65, -0.25))
    X = w / 2 + A
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             ext((op.offset(A, MIT, 4.0) - op) ^ rect(-50, 0.0, 50, 100), 0.0, 0.8)]
    parts.append(chamfer_box(-X - 0.8, h + A - 0.01, X + 0.8, h + A + 1.2, 0.0, 1.2, c=0.3, bottom=0.5))
    return O._one_piece(leaf, parts, op, plug_cs, pl, h + A + 1.4, 0.0)


def arch_skrock(w=26.0, spring=22.0, depth=3.0, ring=3.0, n=15):
    """The Sakonnet's round arches (the carriage arch and the loggia): a ring of rock-faced
    voussoirs with a raised keystone round a semicircular head, square-cut impost blocks, and a
    reveal lining the opening through the wall."""
    from .core import arch_cs
    op = arch_cs(-w / 2, w / 2, 0.0, spring)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = depth
    lining = (plug_cs - plug_cs.offset(-0.9, MIT, 4.0)) - rect(-200, -5, 200, 0.6)
    sash = [ext(lining, -pl, 0.0)]
    R0 = w / 2
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS)]
    back = cs_union([poly([(R0 * math.cos(a), spring + R0 * math.sin(a)) for a in np.linspace(0, math.pi, 40)] +
                          [((R0 + ring) * math.cos(a), spring + (R0 + ring) * math.sin(a)) for a in np.linspace(math.pi, 0, 40)])])
    parts.append(ext(back, 0.0, 0.45))
    for k in range(n):
        a0 = math.pi * k / n + 0.3 / R0
        a1 = math.pi * (k + 1) / n - 0.3 / R0
        r1 = R0 + ring + (0.8 if k == n // 2 else 0.0)
        pts = [(R0 * math.cos(a), spring + R0 * math.sin(a)) for a in np.linspace(a0, a1, 4)] + \
              [(r1 * math.cos(a), spring + r1 * math.sin(a)) for a in np.linspace(a1, a0, 4)]
        v = poly(pts)
        dep = 1.0 + 0.25 * ((k * 7) % 3) + (0.5 if k == n // 2 else 0.0)
        parts.append(ext(v, 0.44, dep - 0.4))
        parts.append(ext(v.offset(-0.35, MIT, 4.0), 0.44, dep))
    for sg in (-1, 1):
        x0, x1 = sorted((sg * (R0 - 0.4), sg * (R0 + ring + 0.6)))
        parts.append(chamfer_box(x0, spring - 2.0, x1, spring + 0.4, 0.0, 1.4, c=0.35, bottom=1.0))
    return O._one_piece(sash, parts, op, plug_cs, pl, spring + R0 + ring + 1.0, 0.0)


def chimney_sakonnet(w, d, h, cap=3.0, seed=3):
    """The Sakonnet's stacks: squared rubble (its joints cut into the solid stack: courses of two
    heights, stones of random length), a band of projecting stones near the top, a capping slab
    and two round clay pots."""
    rng = np.random.default_rng(seed)
    body = box([-w / 2, -d / 2, 0.0], [w / 2, d / 2, h - cap])
    grooves = []
    z = 0.8
    k = 0
    while z < h - cap - 3.0:
        ch = 2.2 if k % 2 else 3.0
        grooves.append(box([-w, -d, z - 0.25], [w, d, z + 0.25]))
        for side in range(4):
            L = w if side % 2 == 0 else d
            u = -L / 2 + rng.uniform(1.2, 3.0)
            while u < L / 2 - 1.2:
                za, zb = z + 0.25, z + ch - 0.25
                if side == 0:
                    grooves.append(box([u - 0.25, -d, za], [u + 0.25, -d / 2 + 0.6, zb]))
                elif side == 2:
                    grooves.append(box([u - 0.25, d / 2 - 0.6, za], [u + 0.25, d, zb]))
                elif side == 1:
                    grooves.append(box([w / 2 - 0.6, u - 0.25, za], [w, u + 0.25, zb]))
                else:
                    grooves.append(box([-w, u - 0.25, za], [-w / 2 + 0.6, u + 0.25, zb]))
                u += rng.uniform(2.6, 5.0)
        z += ch
        k += 1
    shell = body - box([-w / 2 + 0.5, -d / 2 + 0.5, -1.0], [w / 2 - 0.5, d / 2 - 0.5, h + 1.0])
    body = body - (union(grooves) - box([-w / 2 + 0.4, -d / 2 + 0.4, -1.0], [w / 2 - 0.4, d / 2 - 0.4, h + 1.0]))
    band = M.hull_points([(sx * w / 2, sy * d / 2, h - cap - 2.0) for sx in (-1, 1) for sy in (-1, 1)] +
                         [(sx * (w / 2 + 0.6), sy * (d / 2 + 0.6), h - cap - 1.4) for sx in (-1, 1) for sy in (-1, 1)] +
                         [(sx * (w / 2 + 0.6), sy * (d / 2 + 0.6), h - cap) for sx in (-1, 1) for sy in (-1, 1)])
    slab_ = box([-w / 2 - 1.0, -d / 2 - 1.0, h - cap - 0.01], [w / 2 + 1.0, d / 2 + 1.0, h - cap + 1.2]) + \
        box([-w / 2 + 0.3, -d / 2 + 0.3, h - cap + 1.19], [w / 2 - 0.3, d / 2 - 0.3, h])
    m = union([body, band, slab_])
    for sx in (-1, 1):
        pc = (sx * w / 4, 0.0)
        pot = M.cylinder(3.6, 1.3, 1.1, 20).translate([pc[0], 0, h - 0.01]) - M.cylinder(4.0, 0.6, 0.6, 16).translate([pc[0], 0, h + 0.6])
        m = m + pot
    return m


def bay_cap_sakonnet(c, r0, z0, n=10):
    """The round bay's bell cap: flared foot, steep cone, shingled, on an n-gon (prints upright).
    Returns (solid, z_top)."""
    from . import roof as R
    bands = [(1.4, 0.55), (3.0, 1.1), (6.0, 2.0), (6.0, 3.2)]
    sol, tex, ap, zt = R.bell_roof(c, r0, z0, bands, n=n, texture="square", tex_kw=dict(pitch=1.4, wtab=1.8, d=0.35))
    tip = M.cylinder(4.4, max(ap, 0.7), 0.5, n).translate([c[0], c[1], zt - 0.4])
    return sol + tex + tip, zt + 4.0


def balcony_sakonnet(w=26.0, h=18.0, depth=8.0, A=1.2):
    """The balcony sunk in the great gable, as one insert: a round-arched niche (side walls, a
    floor, a barrel head) running ``depth`` into the attic, at its back a pair of glazed doors
    under a transom, across its front a shingled parapet with a moulded rail, round its mouth a
    plain arched band with a keystone. Prints lying on its back like the windows."""
    from .core import arch_cs
    spring = h - w / 2
    op = arch_cs(-w / 2, w / 2, 0.0, spring)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = depth
    inner = plug_cs.offset(-1.0, MIT, 4.0) ^ rect(-50, 1.2, 50, 100)
    niche = [ext(plug_cs, -pl, 0.0) - ext(inner, -pl + 1.2, 1.0)]
    # the doors in the back wall: glass at the very back, bars in front of it
    dw, dh = min(14.0, w - 6.0), min(13.0, spring + 1.0)
    dr = rect(-dw / 2, 1.2, dw / 2, 1.2 + dh)
    vt = 1.2 + dh - 2.6
    niche = [m - ext(dr, -pl - 1.0, -pl + 1.2) for m in niche]
    niche.append(ext(dr, -pl, -pl + O.GLASS))
    bars = [rect(-0.5, 0.0, 0.5, vt), rect(-dw, vt - 0.3, dw, vt + 0.3)] + \
        [rect(x - RIB / 2, 0.0, x + RIB / 2, vt) for x in (-dw / 4, dw / 4)] + \
        [rect(x - RIB / 2, vt, x + RIB / 2, 1.2 + dh + 1) for x in np.linspace(-dw / 2, dw / 2, 6)[1:-1]] + \
        [rect(-dw, 1.2 + vt * 0.45 - RIB / 2, dw, 1.2 + vt * 0.45 + RIB / 2)]
    niche.append(ext(cs_union(bars) ^ dr.offset(0.1, MIT, 4.0), -pl + O.GLASS - 0.01, -pl + 1.21))
    # the parapet across the mouth, its rail
    par = rect(-w / 2, 0.0, w / 2, 4.2) ^ plug_cs.offset(0.1, MIT, 4.0)
    niche.append(ext(par, -1.6, 0.0))
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             ext((op.offset(A, MIT, 4.0) - op) ^ rect(-50, spring - 0.01, 50, 100), 0.0, 0.8),
             ext(rect(-w / 2 - A, 0.0, -w / 2, spring) + rect(w / 2, 0.0, w / 2 + A, spring), 0.0, 0.8),
             chamfer_box(-1.0, h - 0.4, 1.0, h + A + 0.8, 0.0, 1.2, c=0.3),
             chamfer_box(-w / 2 + 0.4, 4.19, w / 2 - 0.4, 5.0, -1.6, 1.0 + 1.6, c=0.3, bottom=0.8)]
    return O._one_piece(niche, parts, op, plug_cs, pl, h + A + 0.8, 0.0)


def eyebrow_hump(pl, c, e, W, H, L, base=2.0):
    """An eyebrow dormer's hump rolling out of roof plane ``pl`` = (q, t, z0, s): its front at
    plan point c, ``e`` the eave direction, rising H at its middle and dying into the slope over
    L up the roof; it starts ``base`` under the slope so it fuses with the roof's skin. Returns
    (hump, frame of its front face (u along e, v up, w out down-slope), the face's top line)."""
    q, t, z0, s = pl
    t = np.asarray(t, float) / np.linalg.norm(t)
    e = np.asarray(e, float) / np.linalg.norm(e)
    c = np.asarray(c, float)

    def zpl(p):
        return z0 + s * ((p[..., 0] - q[0]) * t[0] + (p[..., 1] - q[1]) * t[1])

    def wave(u):
        k = np.clip(u / W, -1, 1)
        return np.cos(k * math.pi / 2) ** 2

    def warp(v):
        u, w_, zl = v[:, 0], v[:, 1], v[:, 2]
        p = c[None, :] + u[:, None] * e[None, :] + w_[:, None] * t[None, :]
        tw = np.clip((w_ / L - 0.25) / 0.75, 0, 1)
        h = H * wave(u) * np.cos(tw * math.pi / 2) ** 2
        z = zpl(p) - base + (base + h) * zl
        return np.c_[p, z]
    hump = box([-W, 0.0, 0.0], [W, L, 1.0]).refine(32).warp_batch(warp)
    zc = float(zpl(c[None, :])[0])
    n = -t                                     # the front faces down the slope
    A = np.zeros((3, 4))
    A[:, 0] = (e[0], e[1], 0.0)
    A[:, 1] = (0.0, 0.0, 1.0)
    A[:, 2] = (n[0], n[1], 0.0)
    A[:, 3] = (c[0], c[1], zc)
    return hump, A

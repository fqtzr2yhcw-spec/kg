"""Trim styles, one per building (see COLLECTION.md): chimneys, finials, foundation facings,
belt courses and eave brackets. Everything prints upright unless noted; outward steps grow
at 45 degrees at most and flat faces sit on the 0.2 mm grid.
"""
import math

import numpy as np
from manifold3d import CrossSection as CS, JoinType, Manifold as M

from .core import Facade, ashlar, box, circle, cs_union, poly, rect, union, zq
from .ornament import chamfer_box, ext, stroke


# ------------------------------------------------------------------ chimneys
# more styles, registered by other modules (hoarch.colonial): BRACKET_EXTRA[style](h, d, t) ->
# side-profile CrossSection (as the built-in brackets); FOUNDATION_EXTRA[style](reg, seed) -> solid
BRACKET_EXTRA = {}
FOUNDATION_EXTRA = {}

def _faces(w, d):
    return [Facade((-w / 2, -d / 2), (w / 2, -d / 2)), Facade((w / 2, -d / 2), (w / 2, d / 2)),
            Facade((w / 2, d / 2), (-w / 2, d / 2)), Facade((-w / 2, d / 2), (-w / 2, -d / 2))]


def _skin(w, d, z0, z1, fn, margin=0.1):
    out = []
    for i, f in enumerate(_faces(w, d)):
        reg = rect(margin, z0, f.L - margin, z1)
        out.append(f.place(fn(reg, i).translate([0, 0, -0.02])))       # sunk a hair: one solid with the shaft
    return union(out)


def _corbel_in(w, d, z, r):
    """A 45 degree weathering from a w x d plinth top at z in to a round shaft of radius r."""
    g = max(w, d) / 2 - r
    return M.hull_points([(x, y, z - 0.01) for x in (-w / 2, w / 2) for y in (-d / 2, d / 2)] +
                         [(r * math.cos(a), r * math.sin(a), z + g) for a in np.linspace(0, 2 * math.pi, 24, endpoint=False)])


def _corbel_out(w, d, z, grow):
    """A 45 degree flare from a w x d outline at z - grow out to (w + 2 grow) at z. The shaft
    below must reach z - grow."""
    return M.hull_points([(x, y, z - grow - 0.01) for x in (-w / 2, w / 2) for y in (-d / 2, d / 2)] +
                         [(x, y, z) for x in (-w / 2 - grow, w / 2 + grow) for y in (-d / 2 - grow, d / 2 + grow)])


def _pot(r, h, style="plain"):
    if style == "square":                # a square clay pot with a banded top
        body = box([-r, -r, 0], [r, r, h - 0.8]) + box([-r - 0.3, -r - 0.3, h - 0.8], [r + 0.3, r + 0.3, h])
        body = body + _corbel_out(2 * r, 2 * r, h - 0.8, 0.3)
        return body - box([-r + 0.5, -r + 0.5, h - 1.2], [r - 0.5, r - 0.5, h + 1])
    if style == "bell":                  # a pot flaring like a bell to a thick lip
        prof = [(0, 0), (r * 1.1, 0), (r * 1.1, 0.4), (r * 0.8, 0.8), (r * 0.8, h * 0.45), (r * 1.2, h - 0.6),
                (r * 1.2, h), (r * 0.6, h), (r * 0.6, h - 0.8), (0, h - 0.8)]
        return M.revolve(poly(prof), 28)
    if style == "octagon":               # an eight-sided pot with a band and a flared lip
        prof = [(0, 0), (r * 1.1, 0), (r * 1.1, 0.4), (r * 0.85, 0.8), (r * 0.85, h * 0.5), (r * 1.0, h * 0.5 + 0.2),
                (r * 1.0, h * 0.5 + 0.6), (r * 0.85, h * 0.5 + 0.8), (r * 0.85, h - 0.6), (r * 1.05, h - 0.4),
                (r * 1.05, h), (r * 0.55, h), (r * 0.55, h - 0.8), (0, h - 0.8)]
        return M.revolve(poly(prof), 8)
    if style == "tall":
        prof = [(0, 0), (r * 1.1, 0), (r * 1.1, 0.4), (r * 0.8, 1.0), (r * 0.8, h - 1.0), (r, h - 0.6), (r, h),
                (r * 0.55, h), (r * 0.55, h - 0.8), (0, h - 0.8)]
    elif style == "crown":
        prof = [(0, 0), (r, 0), (r, h * 0.2), (r * 0.8, h * 0.4), (r * 0.8, h * 0.75), (r * 1.15, h * 0.95),
                (r * 1.15, h), (r * 0.6, h), (r * 0.6, h - 0.8), (0, h - 0.8)]
    else:
        prof = [(0, 0), (r * 1.1, 0), (r * 1.1, h * 0.12), (r * 0.9, h * 0.18), (r * 0.8, h * 0.7), (r, h * 0.85),
                (r, h), (r * 0.62, h), (r * 0.62, h - 0.8), (0, h - 0.8)]
    return M.revolve(poly(prof), 24)


def _brick(bond, **kw):
    from .skins import brick_bond
    return lambda reg, i: brick_bond(reg, bond, d=0.22, uoff=0.6 * (i % 2), **kw)


def chimney(style, w=9.0, d=9.0, h=24.0):
    """A chimney standing on z = 0 (the bottom of its roof pocket), top of the cap at about h.
    Styles, one per building:
      corbel    brick, sunk panels, a three-course corbelled cap, two pots (Beaumont)
      stucco    smooth stucco with a raised panel on each face and a moulded cornice (Ashby)
      paneled   Flemish brick between corner pilasters, a stone cap slab, two pots (Harcourt)
      banded    English-bond brick with two projecting bands and a flue recess (Fowler)
      slim      narrow running-bond brick under a pyramidal hood (Delancey)
      diagonal  two flues set diagonally on a plinth, each with a flared cap (Whitby)
      stone     rock-faced ashlar with a gabled coping (Ardmore)
      ribbed    brick with pilaster ribs on every face, a corbelled crown and T cap (Merritt)
      plain     common brick, one corbel course, a flat cap and one pot (Hollis)
      arched    Roman brick with arched recesses, a deep corbelled crown, three pots (Carrow)
      and for the Main Street shops: party, stovepipe, coped, hooded, stepped, slab, tapered,
      twin and round (a round stack with iron bands and a corbelled crown, on a plinth);
      fluted (the cottage: sunk flutes down each face, a band, a corbelled cap and a pot);
      clustered (the Larkspur: three round flues on a brick plinth), lozenge (the Juniper:
      a sunk lozenge on each face under a two-step corbelled cap),
      crowned (the Primrose), dogtooth (the Rosecroft), roundel (the Laurel: stucco, a band,
      a roundel frieze, a stepped cornice and a capstone) and chequer (the Myrtle: brick with
      a chequer band of proud bricks under a corbelled cap)
    """
    h = zq(h)
    if style == "corbel":
        from .features import chimney as ch
        return ch(w=w, dpt=d, h=h, peg=None, pots=2)
    if style == "stucco":
        sh = h - 2.6
        body = box([-w / 2, -d / 2, 0], [w / 2, d / 2, sh])
        body = body + union([f.place(chamfer_box(1.2, 1.6, f.L - 1.2, sh - 2.4, -0.02, 0.42, c=0.25, bottom=0.42))
                             for f in _faces(w, d)])
        body = body + _corbel_out(w, d, sh + 0.6, 0.6) + box([-w / 2 - 0.6, -d / 2 - 0.6, sh + 0.59], [w / 2 + 0.6, d / 2 + 0.6, h - 0.6])
        body = body + _corbel_out(w + 1.2, d + 1.2, h - 0.4, 0.2) + box([-w / 2 - 0.8, -d / 2 - 0.8, h - 0.41], [w / 2 + 0.8, d / 2 + 0.8, h])
        return body - box([-w / 2 + 1.4, -d / 2 + 1.4, h - 0.8], [w / 2 - 1.4, d / 2 - 1.4, h + 1])
    if style == "paneled":
        sh = h - 3.4
        body = box([-w / 2, -d / 2, 0], [w / 2, d / 2, sh])
        body = body + _skin(w, d, 0.0, sh, _brick("flemish"))
        for f in _faces(w, d):
            body = body + f.place(box([-0.01, 0.0, 0.0], [1.4, sh, 0.5])) + f.place(box([f.L - 1.4, 0.0, 0.0], [f.L + 0.01, sh, 0.5]))
            body = body + f.place(box([1.4, sh - 1.4, 0.0], [f.L - 1.4, sh, 0.5]))
        body = body + _corbel_out(w + 1.0, d + 1.0, sh + 0.6, 0.6) + box([-w / 2 - 1.1, -d / 2 - 1.1, sh + 0.59], [w / 2 + 1.1, d / 2 + 1.1, sh + 1.4])
        for k in (-1, 1):
            body = body + _pot(1.3, 3.6, "crown").translate([k * w * 0.22, 0, sh + 1.2])
        return body
    if style == "banded":
        sh = h - 1.2
        body = box([-w / 2, -d / 2, 0], [w / 2, d / 2, sh]) + _skin(w, d, 0.0, sh, _brick("english"))
        for zb in (sh * 0.55, sh - 2.4):
            zb = zq(zb)
            body = body + _corbel_out(w, d, zb, 0.4) + box([-w / 2 - 0.4, -d / 2 - 0.4, zb - 0.01], [w / 2 + 0.4, d / 2 + 0.4, zb + 1.2])
        body = body + _corbel_out(w, d, sh, 0.4) + box([-w / 2 - 0.4, -d / 2 - 0.4, sh - 0.01], [w / 2 + 0.4, d / 2 + 0.4, h])
        return body - box([-w / 2 + 1.2, -d / 2 + 1.2, h - 1.0], [w / 2 - 1.2, d / 2 - 1.2, h + 1])
    if style == "slim":
        w2, d2 = w * 0.75, d * 0.75
        sh = h - 3.0
        body = box([-w2 / 2, -d2 / 2, 0], [w2 / 2, d2 / 2, sh]) + _skin(w2, d2, 0.0, sh, _brick("running"))
        body = body + _corbel_out(w2, d2, sh + 0.6, 0.6) + box([-w2 / 2 - 0.6, -d2 / 2 - 0.6, sh + 0.59], [w2 / 2 + 0.6, d2 / 2 + 0.6, sh + 1.0])
        hood = M.hull_points([(x, y, sh + 1.0) for x in (-w2 / 2 - 0.6, w2 / 2 + 0.6) for y in (-d2 / 2 - 0.6, d2 / 2 + 0.6)] +
                             [(x, y, h) for x in (-0.6, 0.6) for y in (-0.6, 0.6)])
        return body + hood
    if style == "diagonal":
        zb = zq(h * 0.45)
        body = box([-w / 2, -d / 2, 0], [w / 2, d / 2, zb]) + _skin(w, d, 0.0, zb - 1.0, lambda r, i: ashlar(r, course=(1.6, 2.4), length=(2.0, 4.0), d=0.3, seed=i + 5))
        body = body + _corbel_out(w, d, zb, 0.4) + box([-w / 2 - 0.4, -d / 2 - 0.4, zb - 0.01], [w / 2 + 0.4, d / 2 + 0.4, zb + 0.6])
        s = min(w, d) * 0.3
        for k in (-1, 1):
            flue = box([-s, -s, zb], [s, s, h - 1.6]).rotate([0, 0, 45]).translate([k * w * 0.24, 0, 0])
            cap = (_corbel_out(2 * s, 2 * s, h - 1.2, 0.4) + box([-s - 0.4, -s - 0.4, h - 1.21], [s + 0.4, s + 0.4, h]))
            cap = cap.translate([0, 0, 0]).rotate([0, 0, 45]).translate([k * w * 0.24, 0, 0])
            hole = box([-s + 0.8, -s + 0.8, h - 0.8], [s - 0.8, s - 0.8, h + 1]).rotate([0, 0, 45]).translate([k * w * 0.24, 0, 0])
            body = body + flue + (cap - hole)
        return body
    if style == "stone":
        sh = h - 3.0
        body = box([-w / 2, -d / 2, 0], [w / 2, d / 2, sh]) + \
            _skin(w, d, 0.0, sh, lambda r, i: ashlar(r, course=(2.2, 3.2), length=(3.0, 6.0), d=0.45, seed=i + 11))
        body = body + _corbel_out(w, d, sh + 0.6, 0.6) + box([-w / 2 - 0.6, -d / 2 - 0.6, sh + 0.59], [w / 2 + 0.6, d / 2 + 0.6, sh + 1.0])
        gab = M.hull_points([(x, y, sh + 1.0) for x in (-w / 2 - 0.6, w / 2 + 0.6) for y in (-d / 2 - 0.6, d / 2 + 0.6)] +
                            [(x, 0.0, h) for x in (-w / 2 - 0.6, w / 2 + 0.6)] +
                            [(x, y, sh + 1.2) for x in (-w / 2 - 0.6, w / 2 + 0.6) for y in (-d / 2 - 0.6, d / 2 + 0.6)])
        return body + gab
    if style == "ribbed":
        sh = h - 3.2
        body = box([-w / 2, -d / 2, 0], [w / 2, d / 2, sh]) + _skin(w, d, 0.0, sh, _brick("running"))
        for f in _faces(w, d):
            for u in (f.L * 0.2, f.L * 0.5, f.L * 0.8):
                body = body + f.place(box([u - 0.35, 0.0, 0.0], [u + 0.35, sh, 0.5]))
        body = body + _corbel_out(w + 1.0, d + 1.0, sh + 0.4, 0.4) + box([-w / 2 - 0.9, -d / 2 - 0.9, sh + 0.39], [w / 2 + 0.9, d / 2 + 0.9, sh + 1.2])
        body = body + box([-w / 2 - 0.3, -d / 2 - 0.3, sh + 1.19], [w / 2 + 0.3, d / 2 + 0.3, h - 0.8])
        body = body + _corbel_out(w + 0.6, d + 0.6, h - 0.4, 0.4) + box([-w / 2 - 0.7, -d / 2 - 0.7, h - 0.41], [w / 2 + 0.7, d / 2 + 0.7, h])
        for k in (-1, 1):
            body = body + _pot(1.1, 3.0, "tall").translate([k * w * 0.22, 0, h - 0.2])
        return body
    if style == "plain":
        sh = h - 1.6
        body = box([-w / 2, -d / 2, 0], [w / 2, d / 2, sh]) + _skin(w, d, 0.0, sh - 1.0, _brick("common"))
        body = body + _corbel_out(w, d, sh, 0.4) + box([-w / 2 - 0.4, -d / 2 - 0.4, sh - 0.01], [w / 2 + 0.4, d / 2 + 0.4, h])
        return body + _pot(1.4, 3.0).translate([0, 0, h - 0.2])
    if style == "arched":
        sh = h - 4.0
        body = box([-w / 2, -d / 2, 0], [w / 2, d / 2, sh]) + _skin(w, d, 0.0, sh, _brick("roman", bl=3.2, bh=0.6))
        for f in _faces(w, d):
            n = 2
            for j in range(n):
                a = f.L * (j + 0.5) / n
                r = f.L / (2 * n) - 0.9
                rec = cs_union([rect(a - r, 2.0, a + r, sh - 2.2 - r), circle((a, sh - 2.2 - r), r, 20)])
                body = body - f.place(ext(rec, -0.5, 1.0))
        for k in range(3):
            g0, z0 = 0.4 * k, sh + 0.8 * k
            body = body + _corbel_out(w + 2 * g0, d + 2 * g0, z0 + 0.4, 0.4) + \
                box([-w / 2 - g0 - 0.4, -d / 2 - g0 - 0.4, z0 + 0.39], [w / 2 + g0 + 0.4, d / 2 + g0 + 0.4, z0 + 0.8])
        body = body + box([-w / 2 - 1.2, -d / 2 - 1.2, sh + 2.39], [w / 2 + 1.2, d / 2 + 1.2, h])
        for k in (-1, 0, 1):
            body = body + _pot(1.1, 3.8, "octagon").translate([k * w * 0.3, 0, h - 0.2])
        return body
    if style == "party":
        # a wide party-wall stack: running bond, a band of corbelled courses, a stone cap and
        # three square pots in a row
        sh = h - 3.4
        body = box([-w / 2, -d / 2, 0], [w / 2, d / 2, sh]) + _skin(w, d, 0.0, sh - 2.0, _brick("running"))
        for k in range(2):
            g = 0.25 * (k + 1)
            z = sh - 2.0 + 0.8 * k
            body = body + _corbel_out(w + 2 * (g - 0.25), d + 2 * (g - 0.25), z + 0.25, 0.25) + \
                box([-w / 2 - g, -d / 2 - g, z + 0.24], [w / 2 + g, d / 2 + g, z + 0.8])
        body = body + box([-w / 2 - 0.5, -d / 2 - 0.5, sh - 0.41], [w / 2 + 0.5, d / 2 + 0.5, sh + 0.6])
        for k in (-1, 0, 1):
            body = body + _pot(0.9, 2.8, "square").translate([k * w * 0.3, 0, sh + 0.4])
        return body
    if style == "coped":
        from . import skins as S
        # an ashlar stack: stone courses, a projecting band, a stepped stone coping and a pair
        # of bell pots
        sh = h - 3.6
        body = box([-w / 2, -d / 2, 0], [w / 2, d / 2, sh]) + \
            _skin(w, d, 0.0, sh - 2.4, lambda reg, i: S.brick_bond(reg, "running", bl=4.0, bh=1.6, mortar=0.5, bed=0.4,
                                                                   d=0.3, uoff=1.0 * (i % 2)))
        body = body + _corbel_out(w, d, sh - 1.6, 0.4) + box([-w / 2 - 0.4, -d / 2 - 0.4, sh - 1.61], [w / 2 + 0.4, d / 2 + 0.4, sh - 0.8])
        body = body + box([-w / 2 - 0.1, -d / 2 - 0.1, sh - 0.81], [w / 2 + 0.1, d / 2 + 0.1, sh - 0.4]) + \
            _corbel_out(w + 0.2, d + 0.2, sh - 0.01, 0.4) + box([-w / 2 - 0.5, -d / 2 - 0.5, sh - 0.02], [w / 2 + 0.5, d / 2 + 0.5, sh + 0.4])
        for k in (-1, 1):
            body = body + _pot(0.9, 3.2, "bell").translate([k * w * 0.25, 0, sh + 0.39])
        return body
    if style == "hooded":
        # a small brick flue with a corbelled top and a sheet-iron rain hood on four legs
        sh = h - 3.0
        body = box([-w / 2, -d / 2, 0], [w / 2, d / 2, sh]) + _skin(w, d, 0.0, sh - 1.2, _brick("running"))
        body = body + _corbel_out(w, d, sh - 0.4, 0.4) + box([-w / 2 - 0.4, -d / 2 - 0.4, sh - 0.41], [w / 2 + 0.4, d / 2 + 0.4, sh])
        for sx in (-1, 1):
            for sy in (-1, 1):
                body = body + box([sx * (w / 2 - 0.2) - 0.35, sy * (d / 2 - 0.2) - 0.35, sh - 0.01],
                                  [sx * (w / 2 - 0.2) + 0.35, sy * (d / 2 - 0.2) + 0.35, sh + 1.6])
        hood = M.hull_points([(x, y, sh + 1.59) for x in (-w / 2 - 0.4, w / 2 + 0.4) for y in (-d / 2 - 0.4, d / 2 + 0.4)] +
                             [(0.0, 0.0, h)])
        return body + hood
    if style == "stepped":
        # a brick stack that steps in twice on 45 degree stone weatherings, then a plain cap
        s1, s2 = h * 0.35, h * 0.65
        body = box([-w / 2, -d / 2, 0], [w / 2, d / 2, s1]) + _skin(w, d, 0.0, s1 - 0.4, _brick("running"))
        w2, d2 = w - 1.2, d - 1.2
        body = body + M.hull_points([(x, y, s1 - 0.01) for x in (-w / 2, w / 2) for y in (-d / 2, d / 2)] +
                                    [(x, y, s1 + 0.6) for x in (-w2 / 2, w2 / 2) for y in (-d2 / 2, d2 / 2)])
        body = body + box([-w2 / 2, -d2 / 2, s1 + 0.59], [w2 / 2, d2 / 2, s2]) + \
            _skin(w2, d2, s1 + 0.6, s2 - 0.4, _brick("running"))
        w3, d3 = w2 - 1.2, d2 - 1.2
        body = body + M.hull_points([(x, y, s2 - 0.01) for x in (-w2 / 2, w2 / 2) for y in (-d2 / 2, d2 / 2)] +
                                    [(x, y, s2 + 0.6) for x in (-w3 / 2, w3 / 2) for y in (-d3 / 2, d3 / 2)])
        body = body + box([-w3 / 2, -d3 / 2, s2 + 0.59], [w3 / 2, d3 / 2, h - 0.8]) + \
            _skin(w3, d3, s2 + 0.6, h - 1.2, _brick("running"))
        body = body + _corbel_out(w3, d3, h - 0.8, 0.4) + box([-w3 / 2 - 0.4, -d3 / 2 - 0.4, h - 0.81], [w3 / 2 + 0.4, d3 / 2 + 0.4, h])
        return body - box([-w3 / 2 + 0.7, -d3 / 2 + 0.7, h - 1.0], [w3 / 2 - 0.7, d3 / 2 - 0.7, h + 1])
    if style == "slab":
        # a brick stack with a flat stone slab raised on four corner piers (the smoke leaves
        # between them)
        sh = h - 2.2
        body = box([-w / 2, -d / 2, 0], [w / 2, d / 2, sh]) + _skin(w, d, 0.0, sh - 0.6, _brick("running"))
        body = body + _corbel_out(w, d, sh, 0.3) + box([-w / 2 - 0.3, -d / 2 - 0.3, sh - 0.01], [w / 2 + 0.3, d / 2 + 0.3, sh + 0.4])
        for sx in (-1, 1):
            for sy in (-1, 1):
                body = body + box([sx * (w / 2 - 0.5) - 0.5, sy * (d / 2 - 0.5) - 0.5, sh + 0.39],
                                  [sx * (w / 2 - 0.5) + 0.5, sy * (d / 2 - 0.5) + 0.5, h - 0.8])
        body = body + box([-w / 2 - 0.4, -d / 2 - 0.4, h - 0.81], [w / 2 + 0.4, d / 2 + 0.4, h])
        return body - box([-w / 2 + 0.8, -d / 2 + 0.8, sh - 1.0], [w / 2 - 0.8, d / 2 - 0.8, sh + 0.41])
    if style == "tapered":
        # a baker's oven stack: a wide brick shaft that tapers on 45 degree shoulders to a
        # narrower flue, a projecting band and a plain cap
        s1 = h * 0.45
        body = box([-w / 2, -d / 2, 0], [w / 2, d / 2, s1]) + _skin(w, d, 0.0, s1 - 0.2, _brick("running"))
        w2, d2 = w * 0.6, d * 0.6
        g = (w - w2) / 2
        body = body + M.hull_points([(x, y, s1 - 0.01) for x in (-w / 2, w / 2) for y in (-d / 2, d / 2)] +
                                    [(x, y, s1 + g) for x in (-w2 / 2, w2 / 2) for y in (-d2 / 2, d2 / 2)])
        body = body + box([-w2 / 2, -d2 / 2, s1 + g - 0.01], [w2 / 2, d2 / 2, h - 1.2]) + \
            _skin(w2, d2, s1 + g, h - 2.8, _brick("running"))
        body = body + _corbel_out(w2, d2, h - 2.4, 0.4) + box([-w2 / 2 - 0.4, -d2 / 2 - 0.4, h - 2.41], [w2 / 2 + 0.4, d2 / 2 + 0.4, h - 1.6])
        body = body + box([-w2 / 2 - 0.1, -d2 / 2 - 0.1, h - 1.61], [w2 / 2 + 0.1, d2 / 2 + 0.1, h])
        return body - box([-w2 / 2 + 0.7, -d2 / 2 + 0.7, h - 1.0], [w2 / 2 - 0.7, d2 / 2 - 0.7, h + 1])
    if style == "lozenge":
        # brick with a sunk lozenge panel on each face, a band and a two-step corbelled cap (the Juniper)
        sh = zq(h - 2.0)
        body = box([-w / 2, -d / 2, 0], [w / 2, d / 2, sh]) + _skin(w, d, 0.0, sh - 0.2, _brick("running"))
        zc_ = zq(sh - 5.0)
        for f in _faces(w, d):
            L_ = f.L
            dia = poly([(L_ / 2, zc_ - 2.2), (L_ / 2 + min(1.6, L_ * 0.3), zc_), (L_ / 2, zc_ + 2.2), (L_ / 2 - min(1.6, L_ * 0.3), zc_)])
            body = body - f.place(ext(dia, -0.4, 1.0))
        g = 0.0
        for k in range(2):
            body = body + _corbel_out(w + 2 * g, d + 2 * g, sh + 0.4 + 0.8 * k, 0.4) + \
                box([-w / 2 - g - 0.4, -d / 2 - g - 0.4, sh + 0.39 + 0.8 * k], [w / 2 + g + 0.4, d / 2 + g + 0.4, sh + 0.8 + 0.8 * k])
            g += 0.4
        body = body + box([-w / 2 - 0.8, -d / 2 - 0.8, sh + 1.59], [w / 2 + 0.8, d / 2 + 0.8, h])
        return body - box([-w / 2 + 1.0, -d / 2 + 1.0, h - 1.0], [w / 2 - 1.0, d / 2 - 1.0, h + 1])
    if style == "pilastered":
        # brick with a raised pilaster at each corner and a sunk panel between on every face,
        # a corbelled band over the panels and a stone cap with a drip (the Magnolia)
        sh = zq(h - 2.4)
        body = box([-w / 2, -d / 2, 0], [w / 2, d / 2, sh]) + _skin(w, d, 0.0, sh - 0.2, _brick("running"))
        zp0, zp1 = zq(sh * 0.45), zq(sh - 1.6)
        for f in _faces(w, d):
            L_ = f.L
            body = body - f.place(ext(rect(1.2, zp0, L_ - 1.2, zp1), -0.4, 1.0))
        body = body + _corbel_out(w, d, sh + 0.4, 0.4) + box([-w / 2 - 0.4, -d / 2 - 0.4, sh - 0.01], [w / 2 + 0.4, d / 2 + 0.4, sh + 0.8])
        body = body + _corbel_out(w + 0.8, d + 0.8, sh + 1.2, 0.4) + \
            box([-w / 2 - 0.8, -d / 2 - 0.8, sh + 0.79], [w / 2 + 0.8, d / 2 + 0.8, h])
        return body - box([-w / 2 + 1.0, -d / 2 + 1.0, h - 1.0], [w / 2 - 1.0, d / 2 - 1.0, h + 1])
    if style == "octagon":
        # a square brick base, a 45 degree weathering to an octagonal shaft with a sunk band,
        # and a two-step corbelled octagonal crown (the Hawthorn)
        zb = zq(h * 0.35)
        body = box([-w / 2, -d / 2, 0], [w / 2, d / 2, zb]) + _skin(w, d, 0.0, zb - 0.4, _brick("running"))
        ap = min(w, d) * 0.4
        R8 = ap / math.cos(math.pi / 8)
        oct_ = lambda r_, z0_, z1_: M.cylinder(z1_ - z0_, r_, r_, 8).rotate([0, 0, 22.5]).translate([0, 0, z0_])
        body = body + M.hull_points([(x, y, zb - 0.01) for x in (-w / 2, w / 2) for y in (-d / 2, d / 2)] +
                                    [(R8 * math.cos(math.pi / 8 + k * math.pi / 4), R8 * math.sin(math.pi / 8 + k * math.pi / 4),
                                      zb + max(w, d) / 2 - ap) for k in range(8)])
        z1 = zb + max(w, d) / 2 - ap
        zc_ = zq(h - 2.0)
        body = body + oct_(R8, z1 - 0.01, zc_)
        zbnd = zq((z1 + zc_) / 2)
        body = body - (oct_(R8 + 1, zbnd, zbnd + 0.8) - oct_(R8 - 0.3, zbnd - 1, zbnd + 2))
        for k, g in enumerate((0.4, 0.8)):
            body = body + M.hull_points([((R8 + g - 0.4) * math.cos(math.pi / 8 + j * math.pi / 4),
                                          (R8 + g - 0.4) * math.sin(math.pi / 8 + j * math.pi / 4), zc_ + 0.8 * k - 0.4)
                                         for j in range(8)] +
                                        [((R8 + g) * math.cos(math.pi / 8 + j * math.pi / 4), (R8 + g) * math.sin(math.pi / 8 + j * math.pi / 4),
                                          zc_ + 0.8 * k) for j in range(8)]) + oct_(R8 + g, zc_ + 0.8 * k - 0.01, zc_ + 0.8 * k + 0.41)
        body = body + oct_(R8 + 0.8, zc_ + 1.2, h)
        return body - M.cylinder(h, ap - 1.0, ap - 1.0, 16).translate([0, 0, h - 1.2])
    if style == "tulip":
        # a slim brick stack with a band of soldier bricks, then a round flue flaring out like a
        # tulip to a thick lip (the Wisteria)
        sh = zq(h - 5.6)
        body = box([-w / 2, -d / 2, 0], [w / 2, d / 2, sh]) + _skin(w, d, 0.0, sh - 1.8, _brick("running"))
        body = body + _corbel_out(w, d, sh - 1.2, 0.3) + box([-w / 2 - 0.3, -d / 2 - 0.3, sh - 1.21], [w / 2 + 0.3, d / 2 + 0.3, sh])
        r0 = min(w, d) * 0.3
        prof = [(0.0, sh - 0.01), (r0, sh - 0.01), (r0 * 0.9, sh + 1.0), (r0 * 1.05, sh + 2.6), (r0 * 1.35, h - 1.0),
                (r0 * 1.45, h - 0.6), (r0 * 1.45, h), (0.0, h)]
        from .porchwork import _clamp45
        body = body + M.revolve(poly(_clamp45(prof)), 32)
        return body - M.cylinder(h, r0 * 0.9, r0 * 0.9, 24).translate([0, 0, h - 1.4])
    if style == "cross":
        # brick with a Greek cross left standing in a sunk square panel on each face, a
        # dentilled band and a cap slab with a drip, two round pots (the Camellia)
        sh = zq(h - 3.2)
        body = box([-w / 2, -d / 2, 0], [w / 2, d / 2, sh]) + _skin(w, d, 0.0, sh - 0.2, _brick("running"))
        zc_ = zq(sh - 5.2)
        for f in _faces(w, d):
            L_ = f.L
            a_ = zq(min(2.2, L_ * 0.34))
            panel = rect(L_ / 2 - a_, zc_ - a_, L_ / 2 + a_, zc_ + a_)
            arm = 0.4
            cross = cs_union([rect(L_ / 2 - arm, zc_ - a_ + 0.6, L_ / 2 + arm, zc_ + a_ - 0.6),
                              rect(L_ / 2 - a_ + 0.6, zc_ - arm, L_ / 2 + a_ - 0.6, zc_ + arm)])
            body = body - f.place(ext(panel - cross, -0.4, 1.0))
        body = body + _corbel_out(w, d, sh, 0.4) + box([-w / 2 - 0.4, -d / 2 - 0.4, sh - 0.01], [w / 2 + 0.4, d / 2 + 0.4, sh + 0.8])
        body = body + _corbel_out(w + 0.8, d + 0.8, sh + 0.8, 0.4) + \
            box([-w / 2 - 0.8, -d / 2 - 0.8, sh + 0.79], [w / 2 + 0.8, d / 2 + 0.8, sh + 1.6])
        body = body - box([-w / 2 + 1.0, -d / 2 + 1.0, sh + 1.0], [w / 2 - 1.0, d / 2 - 1.0, sh + 2.0])
        pr = min(w, d) * 0.16
        H = h - sh - 1.0                                      # the pots stand in the cap's sunk top
        for sx in (-1, 1):
            pot = M.revolve(poly([(0.0, 0.0), (pr, 0.0), (pr - 0.1, H - 0.8), (pr + 0.2, H - 0.4), (pr + 0.2, H),
                                  (0.0, H)]), 24)
            pot = pot - M.cylinder(h, pr - 0.5, pr - 0.5, 24).translate([0, 0, 0.6])
            body = body + pot.translate([sx * w * 0.22, 0.0, sh + 1.0])
        return body
    if style == "clustered":
        # three round flues rising from a brick plinth, each with a band and a corbelled crown,
        # joined by a shared cap slab under their crowns (the Larkspur)
        zb = zq(h * 0.3)
        body = box([-w / 2, -d / 2, 0], [w / 2, d / 2, zb]) + _skin(w, d, 0.0, zb - 0.4, _brick("running"))
        body = body + _corbel_out(w, d, zb, 0.3) + box([-w / 2 - 0.3, -d / 2 - 0.3, zb - 0.01], [w / 2 + 0.3, d / 2 + 0.3, zb + 0.6])
        r = min(w / 6.4, d / 2.4)
        zt = h - 1.8
        for k in (-1, 0, 1):
            x = k * (w / 2 - r - 0.4)
            prof = [(0, zb + 0.5), (r, zb + 0.5), (r, zt - 2.4), (r + 0.3, zt - 2.1), (r + 0.3, zt - 1.6), (r, zt - 1.3),
                    (r, zt), (r + 0.6, zt + 0.6), (r + 0.6, h)]
            from .porchwork import _clamp45
            flue = M.revolve(poly(_clamp45(prof) + [(0.0, h)]), 28).translate([x, 0, 0])
            body = body + flue - M.cylinder(1.4, max(0.3, r - 0.5), max(0.3, r - 0.5), 20).translate([x, 0, h - 1.2])
        return body
    if style == "roundel":
        # a smooth stuccoed stack, a raised band, a frieze with a raised roundel on each face,
        # a cornice corbelled out in two steps and a low pyramidal capstone (the Laurel)
        sh = zq(h - 4.4)
        body = box([-w / 2, -d / 2, 0], [w / 2, d / 2, sh])
        zb = zq(sh * 0.5)
        body = body + _corbel_out(w, d, zb, 0.3) + box([-w / 2 - 0.3, -d / 2 - 0.3, zb - 0.01], [w / 2 + 0.3, d / 2 + 0.3, zb + 0.8])
        for f in _faces(w, d):
            body = body + f.place(ext(circle((f.L / 2, sh - 1.6), min(1.0, f.L * 0.15), 20), -0.02, 0.4))
        g = 0.0
        for k in range(2):
            body = body + _corbel_out(w + 2 * g, d + 2 * g, sh + 0.4 + 0.6 * k, 0.4) + \
                box([-w / 2 - g - 0.4, -d / 2 - g - 0.4, sh + 0.39 + 0.6 * k], [w / 2 + g + 0.4, d / 2 + g + 0.4, sh + 0.6 + 0.6 * k])
            g += 0.4
        zc = sh + 1.2
        body = body + box([-w / 2 - 0.8, -d / 2 - 0.8, zc - 0.01], [w / 2 + 0.8, d / 2 + 0.8, zc + 1.0])
        cap = M.hull_points([(x, y, zc + 0.99) for x in (-w / 2 - 0.8, w / 2 + 0.8) for y in (-d / 2 - 0.8, d / 2 + 0.8)] +
                            [(x, y, h) for x in (-w / 2 + 1.4, w / 2 - 1.4) for y in (-d / 2 + 1.4, d / 2 - 1.4)])
        return body + cap - box([-w / 2 + 1.6, -d / 2 + 1.6, h - 1.4], [w / 2 - 1.6, d / 2 - 1.6, h + 1])
    if style == "chequer":
        # brick with a chequer band near the top (alternate bricks standing proud), a
        # corbelled cap and a raised rim (the Myrtle)
        sh = zq(h - 2.4)
        body = box([-w / 2, -d / 2, 0], [w / 2, d / 2, sh])
        zc0 = zq(sh - 4.0)
        body = body + _skin(w, d, 0.0, zc0 - 0.4, _brick("running"))
        for f in _faces(w, d):
            n = max(3, int(f.L / 1.3))
            sq = []
            for r in range(3):
                for k in range(n):
                    if (k + r) % 2 == 0:
                        u = f.L * k / n
                        sq.append(chamfer_box(u + 0.1, zc0 + 1.2 * r + 0.2, u + f.L / n - 0.1, zc0 + 1.2 * r + 1.0, -0.02, 0.37, c=0.15))
            body = body + f.place(union(sq))
        body = body + _corbel_out(w, d, sh + 0.4, 0.4) + box([-w / 2 - 0.4, -d / 2 - 0.4, sh + 0.39], [w / 2 + 0.4, d / 2 + 0.4, sh + 1.0])
        body = body + _corbel_out(w + 0.8, d + 0.8, sh + 1.4, 0.4) + box([-w / 2 - 0.8, -d / 2 - 0.8, sh + 1.39], [w / 2 + 0.8, d / 2 + 0.8, h])
        return body - box([-w / 2 + 0.6, -d / 2 + 0.6, h - 0.8], [w / 2 - 0.6, d / 2 - 0.6, h + 1])
    if style == "dogtooth":
        # a brick stack with a band of dogtooth brick (headers set diagonally, their corners
        # out) under a three-course corbel and a cap
        sh = h - 3.2
        body = box([-w / 2, -d / 2, 0], [w / 2, d / 2, sh])
        body = body + _skin(w, d, 0.0, sh - 3.0, _brick("running"))
        for f in _faces(w, d):
            n = max(2, int(f.L / 1.3))
            teeth = []
            for k in range(n):
                u = f.L * (k + 0.5) / n
                teeth.append(M.hull_points([(u - 0.5, v, 0.0) for v in (sh - 2.6, sh - 1.0)] +
                                           [(u, v, 0.45) for v in (sh - 2.4, sh - 1.2)] +
                                           [(u + 0.5, v, 0.0) for v in (sh - 2.6, sh - 1.0)]))
            body = body + f.place(union(teeth))
        g = 0.0
        for k in range(3):
            body = body + _corbel_out(w + 2 * g, d + 2 * g, sh + 0.6 * k + 0.3, 0.3) + \
                box([-w / 2 - g - 0.3, -d / 2 - g - 0.3, sh + 0.6 * k + 0.29], [w / 2 + g + 0.3, d / 2 + g + 0.3, sh + 0.6 * k + 0.6])
            g += 0.3
        body = body + box([-w / 2 - 1.0, -d / 2 - 1.0, sh + 1.79], [w / 2 + 1.0, d / 2 + 1.0, h])
        return body - box([-w / 2 + 1.1, -d / 2 + 1.1, h - 1.0], [w / 2 - 1.1, d / 2 - 1.1, h + 1])
    if style == "crowned":
        # a tall brick stack with a stone band two thirds up, a four-course corbelled crown
        # with a dentil course, a stone cap and a flue
        sh = h - 4.0
        body = box([-w / 2, -d / 2, 0], [w / 2, d / 2, sh])
        body = body + _skin(w, d, 0.0, sh, _brick("common"))
        zb = round(sh * 0.66 / 0.2) * 0.2
        body = body + box([-w / 2 - 0.3, -d / 2 - 0.3, zb], [w / 2 + 0.3, d / 2 + 0.3, zb + 0.8])
        g = 0.0
        for k in range(4):
            body = body + _corbel_out(w + 2 * g, d + 2 * g, sh + 0.6 * k + 0.3, 0.3) + \
                box([-w / 2 - g - 0.3, -d / 2 - g - 0.3, sh + 0.6 * k + 0.29], [w / 2 + g + 0.3, d / 2 + g + 0.3, sh + 0.6 * k + 0.6])
            g += 0.3
        body = body + box([-w / 2 - 1.3, -d / 2 - 1.3, sh + 2.39], [w / 2 + 1.3, d / 2 + 1.3, h])
        return body - box([-w / 2 + 1.2, -d / 2 + 1.2, h - 1.2], [w / 2 - 1.2, d / 2 - 1.2, h + 1])
    if style == "fluted":
        # brick, three sunk flutes down each face, a stone band and a corbelled cap with a pot
        sh = h - 3.0
        body = box([-w / 2, -d / 2, 0], [w / 2, d / 2, sh])
        body = body + _skin(w, d, 0.0, 1.8, _brick("running"))
        for f in _faces(w, d):
            n = 3
            for k in range(n):
                u = f.L * (k + 1) / (n + 1)
                body = body - f.place(box([u - 0.35, 2.6, -0.4], [u + 0.35, sh - 1.8, 0.05]))
        body = body + box([-w / 2 - 0.3, -d / 2 - 0.3, 1.8], [w / 2 + 0.3, d / 2 + 0.3, 2.4])
        body = body + _corbel_out(w, d, sh + 0.6, 0.6) + box([-w / 2 - 0.6, -d / 2 - 0.6, sh + 0.59], [w / 2 + 0.6, d / 2 + 0.6, sh + 1.4])
        pot = M.cylinder(1.6, 1.0, 0.8, 20).translate([0, 0, sh + 1.39]) + M.cylinder(0.4, 0.8, 1.1, 20).translate([0, 0, sh + 2.98])
        return body + pot - M.cylinder(4.0, 0.5, 0.5, 16).translate([0, 0, sh + 0.4])
    if style == "round":
        # a round brick stack (an industrial flue in miniature) on a square plinth, iron bands
        # round it, a corbelled crown of three rings flaring at 45 degrees, the flue open
        r = min(w, d) / 2 - 0.4
        ph = 2.4
        body = box([-w / 2, -d / 2, 0], [w / 2, d / 2, ph]) + _corbel_in(w, d, ph, r)
        top = h - 1.8
        body = body + M.cylinder(top - ph + 0.01, r, r * 0.88, 32).translate([0, 0, ph - 0.01])
        for z in np.arange(ph + 3.0, top - 2.0, 4.0):
            rz = r - (r - r * 0.88) * (z - ph) / (top - ph)
            body = body + M.cylinder(0.4, rz, rz + 0.3, 32).translate([0, 0, z]) + \
                M.cylinder(0.4, rz + 0.3, rz + 0.3, 32).translate([0, 0, z + 0.39])
        rt = r * 0.88
        for k in range(3):
            body = body + M.cylinder(0.3, rt + 0.3 * k, rt + 0.3 * (k + 1), 32).translate([0, 0, top + 0.6 * k - 0.01]) + \
                M.cylinder(0.31, rt + 0.3 * (k + 1), rt + 0.3 * (k + 1), 32).translate([0, 0, top + 0.6 * k + 0.29])
        return body - M.cylinder(3.0, rt - 0.7, rt - 0.7, 24).translate([0, 0, h - 1.4])
    if style == "twin":
        # two small flues side by side, joined at the top by a corbelled brick cap
        fw = w / 2 - 0.4
        body = M()
        for sx in (-1, 1):
            c = sx * (w / 4 + 0.1)
            body = body + box([c - fw / 2, -d / 2, 0], [c + fw / 2, d / 2, h - 1.6]) + \
                _skin(fw, d, 0.0, h - 2.2, _brick("running")).translate([c, 0, 0])
        body = body + box([-w / 2, -d / 2, h - 2.4], [w / 2, d / 2, h - 1.2]) + _corbel_out(w, d, h - 0.8, 0.4) + \
            box([-w / 2 - 0.4, -d / 2 - 0.4, h - 0.81], [w / 2 + 0.4, d / 2 + 0.4, h])
        for sx in (-1, 1):
            c = sx * (w / 4 + 0.1)
            body = body - box([c - fw / 2 + 0.6, -d / 2 + 0.6, h - 1.0], [c + fw / 2 - 0.6, d / 2 - 0.6, h + 1])
        return body
    if style == "stovepipe":
        # a sheet-iron flue: a band, and a cone cap flaring at 45 degrees (w = pipe diameter)
        r = w / 2
        body = M.cylinder(h - 2.0, r, r, 28) + M.cylinder(0.6, r + 0.3, r + 0.3, 28).translate([0, 0, round(h * 0.55 / 0.2) * 0.2])
        cap = M.cylinder(1.0, r, r + 1.0, 28).translate([0, 0, h - 2.01]) + \
            M.cylinder(1.0, r + 1.0, 0.3, 28).translate([0, 0, h - 1.02])
        return body + cap
    raise ValueError(style)


CHIMNEYS = ("corbel", "stucco", "paneled", "banded", "slim", "diagonal", "stone", "ribbed", "plain", "arched", "party",
            "stovepipe", "coped", "hooded", "stepped", "slab", "tapered", "twin", "round", "fluted", "crowned",
            "dogtooth", "roundel", "chequer", "clustered", "lozenge", "cross", "tulip", "octagon", "pilastered")


# ------------------------------------------------------------------ finials (revolved, printed upright)
def finial(style, r=1.2, h=8.0, seg=28):
    """Turned finials, one per building with a tower, spire or cupola:
    urn (Beaumont), acorn (Ashby), iron (Harcourt), ball (Fowler), stack (Ardmore),
    spire (Carrow), onion (the drugstore's turret), vane (the Rosecroft), lance (the Larkspur),
    fleur (the Juniper)."""
    if style == "urn":
        from .ornament import finial as f0
        return f0(r, h)
    k = r / 1.2
    if style == "acorn":
        prof = [(0, 0), (1.2, 0), (1.2, 0.5), (0.7, 1.0), (0.6, 2.0), (1.0, 2.6), (1.0, 3.0), (0.6, 3.3),
                (1.1, 3.8), (1.2, 4.6), (1.0, 5.4), (0.6, 6.2), (0.4, 6.7), (0, 7.0)]
    elif style == "iron":
        prof = [(0, 0), (1.0, 0), (1.0, 0.6), (0.5, 1.1), (0.45, 1.8), (0.8, 2.1), (0.8, 2.4), (0.45, 2.7),
                (0.45, 3.6), (0.75, 3.9), (0.75, 4.2), (0.42, 4.5), (0.42, 5.8), (0.6, 6.0), (0.6, 6.3),
                (0.4, 6.5), (0, 7.0)]
    elif style == "ball":
        prof = [(0, 0), (1.2, 0), (1.2, 0.6), (0.7, 1.1), (0.6, 2.4), (0.9, 2.8), (0.6, 3.1)] + \
               [(0.6 + 1.0 * math.sin(math.pi * t / 8), 3.1 + 2.4 * t / 8) for t in range(1, 8)] + \
               [(0.5, 5.6), (0.4, 6.4), (0, 7.0)]
    elif style == "stack":
        prof = [(0, 0), (1.3, 0), (1.3, 1.0), (1.0, 1.3), (1.0, 2.0), (0.8, 2.2), (0.8, 3.0), (0.6, 3.2),
                (0.6, 4.0), (0.45, 4.2), (0.45, 6.0), (0, 7.0)]
    elif style == "vane":                # a stout turned base, collar and ball: the weathervane's own stem plugs into its top
        prof = [(0, 0), (1.3, 0), (1.3, 0.8), (1.0, 1.1), (1.0, 3.0), (1.2, 3.4), (1.2, 3.8), (0.95, 4.3), (0.95, 5.4),
                (1.15, 5.8), (1.15, 6.6), (0.95, 6.9), (0.8, 7.2), (0.0, 7.2)]
        from .porchwork import _clamp45
        return M.revolve(poly(_clamp45([(x * k, z * k) for x, z in prof])), seg)
    elif style == "fleur":               # a rod carrying a fleur-de-lis head (added below) over a turned collar (the Juniper)
        prof = [(0, 0), (1.2, 0), (1.2, 0.6), (0.8, 1.0), (0.7, 2.0), (1.0, 2.3), (1.0, 2.7), (0.45, 3.1), (0.4, 7.0),
                (0.0, 7.0)]
        prof = [(x * k, z * h / 7.0) for x, z in prof]
        from .porchwork import _clamp45
        rod = M.revolve(poly(_clamp45([(max(x, 0.4) if 0 < x < 0.4 else x, z) for x, z in prof])), seg)
        petals = cs_union([poly([(-0.35, 0.0), (0.35, 0.0), (0.35, 1.4), (0.0, 2.2), (-0.35, 1.4)])] +
                          [stroke([(0.0, 0.2), (sg * 0.9, 0.7), (sg * 1.0, 1.5)], 0.5) for sg in (-1, 1)] +
                          [rect(-0.9, -0.4, 0.9, 0.4)])
        head = M.extrude(petals, 0.8).translate([0, 0, -0.4]).transform(np.array([[1.0, 0, 0, 0], [0, 0, -1.0, 0], [0, 1.0, 0, h - 0.4]]))
        return rod + head
    elif style == "lance":               # a tall slim lance: a turned base, two rings and a long spike (the Larkspur)
        prof = [(0, 0), (1.2, 0), (1.2, 0.6), (0.7, 1.1), (0.6, 2.2), (0.95, 2.5), (0.95, 2.8), (0.55, 3.2), (0.5, 4.0),
                (0.8, 4.3), (0.8, 4.6), (0.45, 5.0), (0.4, 6.4), (0.0, 7.0)]
    elif style == "pineapple":           # a turned stem carrying a pineapple: an egg-shaped body under a tuft (the Wisteria)
        prof = [(0, 0), (1.2, 0), (1.2, 0.5), (0.7, 0.9), (0.6, 1.8), (0.9, 2.1), (0.9, 2.4), (0.6, 2.7), (0.9, 3.1),
                (1.2, 3.8), (1.25, 4.4), (1.05, 5.0), (0.6, 5.4), (0.45, 5.6), (0.7, 6.0), (0.4, 6.5), (0.0, 7.0)]
    elif style == "spike":               # an iron spike: a turned base, a round ball, a collar and a long thin point (the Camellia)
        prof = [(0, 0), (1.2, 0), (1.2, 0.5), (0.7, 0.9), (0.6, 1.3), (1.05, 1.75), (1.15, 2.2), (1.05, 2.65), (0.6, 3.1),
                (0.45, 3.5), (0.75, 3.8), (0.75, 4.0), (0.4, 4.35), (0.3, 6.3), (0.0, 7.0)]
    elif style == "pinnacle":            # Eastlake: a square-looking turned spike with a ball
        prof = [(0, 0), (1.2, 0), (1.2, 0.8), (0.8, 1.2), (0.8, 2.0), (1.1, 2.3), (1.1, 2.7), (0.6, 3.2), (0.5, 4.2),
                (0.9, 4.6), (0.9, 5.2), (0.4, 5.7), (0.3, 7.0), (0.0, 8.0)]
    elif style == "onion":
        prof = [(0, 0), (1.1, 0), (1.1, 0.5), (0.6, 1.0), (0.55, 1.6), (0.9, 2.2), (1.25, 3.0), (1.2, 3.7),
                (0.8, 4.4), (0.45, 5.0), (0.4, 6.2), (0, 7.0)]
    elif style == "spire":
        prof = [(0, 0), (1.2, 0), (1.2, 0.5), (0.8, 0.9), (0.8, 1.3), (1.05, 1.6), (1.05, 1.9), (0.6, 2.3),
                (0.5, 3.5), (0.8, 3.8), (0.8, 4.1), (0.45, 4.4), (0.4, 6.3), (0, 7.0)]
    else:
        raise ValueError(style)
    prof = [(x * k if x > 0 else 0.0, z * h / 7.0) for x, z in prof]
    prof = [(max(x, 0.4) if 0 < x < 0.4 and z < h * 0.97 else x, z) for x, z in prof]
    from .porchwork import _clamp45
    return M.revolve(poly(_clamp45(prof)), seg)


# ------------------------------------------------------------------ foundation facings
def foundation_skin(style, reg, seed=0):
    """Facing for a foundation face region (u, v, w out), one per building:
    fieldstone (Beaumont), limestone (Ashby: smooth drafted ashlar), granite (Harcourt:
    big rock-faced blocks), parged (Fowler: scored stucco), rusticated (Delancey: long
    channel-jointed blocks), rubble (Whitby: small random stones), boulder (Ardmore: tall
    rock-faced courses), brick (Merritt: running bond over a soldier course), block (Hollis:
    rock-faced concrete block), coursed (Carrow: long thin coursed stones), plinth (Pemberton:
    long dressed granite), timber (the barber shop: a timber sill with bolt heads), polished
    (the bank: tall polished granite blocks), piers (the general store: stone piers with
    board skirting), bossed (the drugstore), cobble (the hotel), herringbone (the bakery),
    battered (the hardware store), moulded (the millinery: a smooth course under an ogee),
    tooled (the jeweler: dressed blocks with a margin round vertically striated faces) and
    coquina (the gingerbread cottage: shell-stone blocks with pitted faces), pebble (the Primrose:
    pebble-dash over a smooth base course), banded (the Rosecroft: smooth courses of two
    heights in turn), panelled (the Laurel and Myrtle pair: a wooden raised basement of
    raised panels over a base board) and drafted (the Larkspur: rock-faced blocks with smooth
    chisel-drafted margins) and tuckpoint (the Juniper: brick with raised pointing)."""
    from . import skins as S
    if style == "fieldstone":
        return ashlar(reg, course=(2.6, 3.9), length=(3.5, 8.5), d=0.55, seed=seed)
    if style == "limestone":
        return S.brick_bond(reg, "running", bl=7.2, bh=3.2, mortar=0.5, bed=0.4, d=0.4, uoff=seed % 3)
    if style == "granite":
        return ashlar(reg, course=(3.6, 4.4), length=(6.0, 10.0), d=0.6, seed=seed, rough=0.18)
    if style == "parged":
        return S.scored_stucco(reg, course=2.6, block=5.2)
    if style == "rusticated":
        return S.brick_bond(reg, "running", bl=9.6, bh=2.4, mortar=0.6, bed=0.6, d=0.45, uoff=seed % 4)
    if style == "rubble":
        return ashlar(reg, course=(1.4, 2.4), length=(1.8, 4.2), d=0.5, seed=seed, rough=0.14)
    if style == "boulder":
        return ashlar(reg, course=(4.0, 5.6), length=(4.5, 9.0), d=0.7, seed=seed, rough=0.22)
    if style == "brick":
        b = reg.bounds()
        top = S.soldier_band(reg, b[3] - 2.4)
        return S.brick_bond(reg ^ rect(b[0] - 1, b[1] - 1, b[2] + 1, b[3] - 2.4), "running", d=0.25) + top
    if style == "block":
        return ashlar(reg, course=(1.9, 1.9), length=(5.6, 5.6), d=0.5, seed=seed, rough=0.12)
    if style == "plinth":                # long smooth dressed granite blocks, two courses
        return S.brick_bond(reg, "running", bl=12.0, bh=2.0, mortar=0.5, bed=0.4, d=0.3, uoff=seed % 5)
    if style == "timber":                # a heavy timber sill: long baulks, butt joints, a row of bolt heads
        b = reg.bounds()
        cells, bolts = [], []
        vm = (b[1] + b[3]) / 2
        u = b[0] - (seed % 7) * 2.0
        while u < b[2]:
            cells.append(rect(u + 0.25, b[1], u + 17.75, b[3]))
            bolts += [circle((u + 3.0 + 6.0 * k, vm), 0.4, 12) for k in range(3)]
            u += 18.0
        return M.extrude(cs_union(cells) ^ reg, 0.35) + M.extrude(cs_union(bolts) ^ reg.offset(-0.3), 0.6)
    if style == "piers":                 # rubble-stone piers with vertical board skirting between them
        b = reg.bounds()
        piers = []
        u = b[0] + 1.5 + (seed % 3)
        while u < b[2] - 1.0:
            piers.append(rect(u - 1.5, b[1], u + 1.5, b[3]))
            u += 10.0
        pc = cs_union(piers) ^ reg
        stones = ashlar(pc, course=(0.9, 1.4), length=(1.0, 1.7), d=0.5, seed=seed, rough=0.1)
        return stones + S.beadboard(reg - pc.offset(0.2, JoinType.Miter, 4.0), pitch=1.2, groove=0.5, d=0.25)
    if style == "banded":                # smooth stone in courses of two heights in turn (tall, short)
        b = reg.bounds()
        cells = []
        v, j = b[1], 0
        while v < b[3]:
            ch = 2.0 if j % 2 == 0 else 1.2
            u = b[0] - (j % 3) * 1.7
            while u < b[2]:
                cells.append(rect(u + 0.25, v + (0.25 if j else 0.0), u + (7.0 if j % 2 == 0 else 4.6) - 0.25, v + ch - 0.25))
                u += 7.0 if j % 2 == 0 else 4.6
            v += ch
            j += 1
        return M.extrude(cs_union(cells) ^ reg, 0.4)
    if style == "pebble":                # pebble-dash: a rough render set with rows of small round pebbles,
        b = reg.bounds()                  # over a smooth base course
        rng = np.random.default_rng(seed + 3)
        pebbles = []
        for v in np.arange(b[1] + 1.4, b[3] - 0.5, 0.8):
            off = rng.uniform(0, 0.8)
            for u in np.arange(b[0] + off, b[2], 0.9 + rng.uniform(0, 0.4)):
                pebbles.append(M.sphere(0.36, 10).translate([u, v, 0.05]))
        base = M.extrude(reg ^ rect(b[0] - 1, b[1] - 1, b[2] + 1, b[1] + 1.0), 0.4)
        render = M.extrude(reg ^ rect(b[0] - 1, b[1] + 1.0, b[2] + 1, b[3] + 1), 0.15)
        return base + render + (union(pebbles) ^ M.extrude(reg.offset(-0.2), 1.0)) if pebbles else base + render
    if style == "coquina":               # shell-stone blocks in regular courses, their faces pitted
        b = reg.bounds()
        rng = np.random.default_rng(seed + 7)
        cells, pits = [], []
        ch = 1.6
        j = 0
        v = b[1]
        while v < b[3]:
            u = b[0] - (j % 2) * 1.6 - 0.8
            while u < b[2]:
                cell = rect(u + 0.25, v + (0.25 if j else 0.0), u + 3.15, v + ch - 0.25)
                cells.append(cell)
                for _ in range(3):              # diamond pits: no level edge to leave a face off the grid
                    pc = (u + rng.uniform(0.8, 2.6), v + rng.uniform(0.7, ch - 0.7))
                    q = rng.uniform(0.38, 0.46)
                    pits.append(poly([(pc[0], pc[1] - q), (pc[0] + q, pc[1]), (pc[0], pc[1] + q), (pc[0] - q, pc[1])]))
                u += 3.2
            v += ch
            j += 1
        blocks = M.extrude(cs_union(cells) ^ reg, 0.45)
        return blocks - M.extrude(cs_union(pits) ^ reg, 1.0).translate([0, 0, 0.25])
    if style == "vjoint":                # smooth ashlar blocks with every edge chamfered, so the joints read as V grooves (the Magnolia)
        b = reg.bounds()
        out, v, j = [], b[1], 0
        ch = 2.4
        slab_ = M.extrude(reg, 1.0)
        while v < b[3]:
            u = b[0] - (j % 2) * 2.6
            while u < b[2]:
                L_ = 5.2
                x0, y0, x1, y1 = u + 0.1, v + 0.1, u + L_ - 0.1, v + ch - 0.1
                pts = [(x, y, 0.0) for x in (x0, x1) for y in (y0, y1)] + \
                      [(x, y, 0.4) for x in (x0 + 0.4, x1 - 0.4) for y in (y0 + 0.4, y1 - 0.4)]
                out.append(M.hull_points(pts) ^ slab_)
                u += L_
            v += ch
            j += 1
        return union(out)
    if style == "ledgestone":            # thin stacked ledge stones: long low slabs in courses of 0.8 to 1.2, joints staggered (the Hawthorn)
        b = reg.bounds()
        rng = np.random.default_rng(seed + 31)
        out, v = [], b[1]
        while v < b[3]:
            ch = 0.8 if rng.random() < 0.5 else 1.2
            u = b[0] - rng.uniform(0.0, 2.0)
            while u < b[2]:
                L_ = rng.uniform(2.4, 5.0)
                cell = rect(u + 0.25, v + 0.2, u + L_ - 0.25, v + ch) ^ reg        # courses and joints on the layer grid
                if not cell.is_empty() and cell.area() > 0.3:
                    out.append(M.extrude(cell, 0.3 + 0.1 * rng.integers(0, 2)))
                u += L_
            v += ch
        return union(out)
    if style == "riverstone":            # rounded river stones in rough courses, each a low pillow (the Wisteria)
        b = reg.bounds()
        rng = np.random.default_rng(seed + 23)
        out, v, j = [], b[1], 0
        slab_ = M.extrude(reg, 1.0)
        while v < b[3]:
            ch = 1.8
            u = b[0] - rng.uniform(0.0, 1.4)
            while u < b[2]:
                L_ = rng.uniform(2.0, 3.0)
                cx, cy = u + L_ / 2, v + ch / 2
                rx, ry = L_ / 2 - 0.25, ch / 2 - 0.22
                ring = [(cx + rx * math.cos(t), cy + ry * math.sin(t), 0.0) for t in np.linspace(0, 2 * math.pi, 16, endpoint=False)]
                top = [(cx + rx * 0.3 * math.cos(t), cy + ry * 0.3 * math.sin(t), 0.4) for t in np.linspace(0, 2 * math.pi, 8, endpoint=False)]
                out.append(M.hull_points(ring + top) ^ slab_)
                u += L_
            v += ch
            j += 1
        return union(out)
    if style == "diamond":               # diamond-point rustication: each block dressed to a low hipped point (the Camellia)
        b = reg.bounds()
        out, v, j = [], b[1], 0
        ch = 2.4
        while v < b[3]:
            u = b[0] - (j % 2) * 2.4
            while u < b[2]:
                L_ = 4.8
                blk = rect(u + 0.25, v + 0.25, u + L_ - 0.25, v + ch - 0.25)
                if not (blk ^ reg).is_empty():
                    x0, y0, x1, y1 = u + 0.25, v + 0.25, u + L_ - 0.25, v + ch - 0.25
                    hh = (y1 - y0) / 2
                    pts = [(x, y, 0.0) for x in (x0, x1) for y in (y0, y1)] + \
                          [(x0 + hh, y0 + hh, 0.5), (x1 - hh, y0 + hh, 0.5)]
                    out.append(M.hull_points(pts) ^ M.extrude(reg, 1.0))
                u += L_
            v += ch
            j += 1
        return union(out)
    if style == "tuckpoint":             # red brick with raised white tuck-pointed joints (the Juniper)
        from . import skins as S
        b = reg.bounds()
        brick_ = S.brick_bond(reg, "running", bl=2.4, bh=0.8, mortar=0.5, bed=0.4, d=0.3)
        joints = []
        v = b[1]
        k = 0
        while v < b[3]:
            joints.append(rect(b[0] - 1, v + 0.8, b[2] + 1, v + 1.2))
            v += 1.2
            k += 1
        return brick_ + M.extrude(cs_union(joints) ^ reg, 0.12)
    if style == "drafted":               # rock-faced blocks in courses, each ringed by a smooth chisel-drafted margin
        b = reg.bounds()
        out, v, j = [], b[1], 0
        rng = np.random.default_rng(seed + 11)
        while v < b[3]:
            ch = 2.4 if j % 2 == 0 else 2.0
            u = b[0] - (j % 2) * 2.2
            while u < b[2]:
                L_ = 4.4 + 0.8 * rng.integers(0, 3)
                blk = rect(u + 0.25, v + 0.2, u + L_ - 0.25, v + ch - 0.2) ^ reg
                if not blk.is_empty() and blk.area() > 0.5:
                    out.append(M.extrude(blk, 0.25))                                  # the drafted margin
                    face = blk.offset(-0.4, JoinType.Miter, 4.0)
                    if not face.is_empty():
                        c = face.bounds()
                        pts = [(x, y, 0.24) for x in (c[0], c[2]) for y in (c[1], c[3])]
                        pts += [(x, y, 0.55 + 0.08 * rng.random()) for x, y in
                                (((c[0] + c[2]) / 2 + rng.uniform(-0.6, 0.6), (c[1] + c[3]) / 2),
                                 (c[0] + 0.5, c[1] + 0.4), (c[2] - 0.5, c[3] - 0.4))]
                        out.append(M.hull_points(pts) ^ M.extrude(face, 1.0))          # the pitched face
                u += L_
            v += ch
            j += 1
        return union(out)
    if style == "panelled":              # a wooden raised basement: raised panels between stiles over a base board
        b = reg.bounds()
        vb = b[1] + 1.6
        out = [M.extrude(reg ^ rect(b[0] - 1, b[1] - 1, b[2] + 1, vb), 0.5),
               M.extrude(reg ^ rect(b[0] - 1, vb - 0.01, b[2] + 1, b[3] + 1), 0.2)]
        v0, v1 = vb + 1.0, b[3] - 1.2
        if v1 - v0 > 2.0:
            n = max(1, int(round((b[2] - b[0]) / 7.0)))
            pw = (b[2] - b[0]) / n
            for k in range(n):
                u0, u1 = b[0] + pw * k + 0.8, b[0] + pw * (k + 1) - 0.8
                if u1 - u0 < 2.0:
                    continue
                out.append(M.hull_points([(u, v, 0.19) for u in (u0, u1) for v in (v0, v1)] +
                                         [(u, v, 0.45) for u in (u0 + 0.5, u1 - 0.5) for v in (v0 + 0.5, v1 - 0.5)]))
        return union(out) ^ M.extrude(reg, 1.0)
    if style == "tooled":                # dressed blocks (one course, two on a tall base): a smooth
        b = reg.bounds()                  # margin round a face tooled in fine vertical striations
        nc = 1 if b[3] - b[1] < 3.6 else 2
        ch = (b[3] - b[1]) / nc
        cells = []
        for j in range(nc):
            v = b[1] + j * ch
            u = b[0] - (seed % 5) - j * 4.0
            while u < b[2]:
                cells.append(rect(u + 0.25, v + (0.25 if j else 0.0), u + 7.75, v + ch - 0.25))
                u += 8.0
        blocks = M.extrude(cs_union(cells) ^ reg, 0.45)
        grooves = cs_union([rect(x - 0.25, b[1] - 1, x + 0.25, b[3] + 1) for x in np.arange(b[0], b[2] + 1.0, 1.0)])
        g0 = math.ceil((b[1] + 0.45) / 0.2 - 1e-6) * 0.2          # groove ends on the layer grid
        g1 = math.floor((b[3] - 0.7) / 0.2 + 1e-6) * 0.2
        faces = cs_union([c.offset(-0.45, JoinType.Miter, 4.0) for c in cells]) ^ reg ^ rect(b[0] - 1, g0, b[2] + 1, g1)
        if faces.is_empty():
            return blocks
        return blocks - M.extrude(grooves ^ faces, 1.0).translate([0, 0, 0.25])
    if style == "moulded":               # one smooth stone course under a small ogee moulding
        b = reg.bounds()
        top = b[3]
        face = chamfer_box(b[0] - 1.0, b[1], b[2] + 1.0, top - 1.2, 0.0, 0.3, c=0.2, bottom=0.3)
        prof = [(b[1] + 0.0, 0.0)]
        mould = M.hull_points([(x, top - 1.6, 0.0) for x in (b[0], b[2])] + [(x, top - 1.2, 0.4) for x in (b[0], b[2])] +
                              [(x, top - 0.6, 0.6) for x in (b[0], b[2])] + [(x, top, 0.3) for x in (b[0], b[2])] +
                              [(x, top, 0.0) for x in (b[0], b[2])])
        return (face + mould) ^ M.extrude(reg, 2.0).translate([0, 0, -0.5])
    if style == "battered":              # a smooth dressed base course with a bevelled weathering on top
        b = reg.bounds()
        top = b[3]
        blocks = []
        u = b[0] - (seed % 4) * 2.0
        while u < b[2]:
            blocks.append(chamfer_box(u + 0.25, b[1], u + 7.75, top - 1.4, 0.0, 0.5, c=0.3, bottom=0.5))
            u += 8.0
        blocks = union(blocks)
        bevel = M.hull_points([(x, y, 0.0) for x in (b[0], b[2]) for y in (top - 1.9, top)] +
                              [(x, top - 1.4, 0.5) for x in (b[0], b[2])] + [(x, top - 0.9, 0.5) for x in (b[0], b[2])])
        return (blocks + bevel) ^ M.extrude(reg, 2.0).translate([0, 0, -0.5])
    if style == "herringbone":           # brick laid in a herringbone between a plain top course
        b = reg.bounds()
        top = b[3] - 1.0
        bricks = []
        L, Wd = 2.2, 0.7
        x = b[0] - 6.0
        while x < b[2] + 6.0:
            for yy in np.arange(b[1] - 3.0, top + 3.0, 1.6):
                for sg in (-1, 1):
                    c = (x + (0.8 if sg > 0 else 0.0), yy + (0.8 if sg > 0 else 0.0))
                    dx, dy = math.cos(math.pi / 4) * L / 2, sg * math.sin(math.pi / 4) * L / 2
                    bricks.append(stroke([(c[0] - dx, c[1] - dy), (c[0] + dx, c[1] + dy)], Wd, caps=False))
            x += 1.6
        field = reg ^ rect(b[0] - 1, b[1] - 1, b[2] + 1, top - 0.4)
        out = M.extrude(cs_union(bricks) ^ field, 0.3)
        return out + S.brick_bond(reg ^ rect(b[0] - 1, top, b[2] + 1, b[3] + 1), "stack", bl=1.2, bh=1.0, d=0.35, datum=top)
    if style == "cobble":                # rounded field cobbles laid in rough courses
        rng = np.random.default_rng(seed)
        b = reg.bounds()
        stones = []
        v = b[1]
        while v < b[3] - 0.4:
            hgt = min(rng.uniform(1.2, 1.6), b[3] - v)
            u = b[0] - rng.uniform(0.0, 1.5)
            while u < b[2]:
                wdt = rng.uniform(1.4, 2.4)
                c = ((u + wdt / 2), v + hgt / 2)
                el = poly([(c[0] + (wdt / 2 - 0.2) * math.cos(a), c[1] + (hgt / 2 - 0.15) * math.sin(a))
                           for a in np.linspace(0, 2 * math.pi, 16, endpoint=False)])        # no flat top
                stones.append(ext(el, 0.0, 0.3) + ext(el.offset(-0.3, JoinType.Round), 0.29, 0.5))
                u += wdt
            v += hgt
        return union(stones) ^ M.extrude(reg, 2.0).translate([0, 0, -0.5])
    if style == "bossed":                # smooth blocks, each with a raised chamfered boss (bossage)
        b = reg.bounds()
        out = [S.brick_bond(reg, "running", bl=5.6, bh=b[3] - b[1] + 0.4, mortar=0.5, bed=0.4, d=0.2, datum=b[1],
                            uoff=seed % 3)]
        u = b[0] - (seed % 3) - 5.6
        while u < b[2] + 5.6:
            out.append(chamfer_box(u + 1.0, b[1] + 0.6, u + 4.6, b[3] - 0.8, 0.19, 0.3, c=0.25, bottom=0.3))
            u += 5.6
        return union(out) ^ M.extrude(reg, 2.0).translate([0, 0, -0.5])
    if style == "polished":              # polished granite: tall smooth blocks with V joints
        b = reg.bounds()
        blocks = []
        u = b[0] - (seed % 5) * 1.8
        while u < b[2]:
            blocks.append(chamfer_box(u + 0.05, b[1], u + 9.55, b[3], 0.0, 0.4, c=0.3, bottom=0.4))
            u += 9.6
        return union(blocks) ^ M.extrude(reg, 2.0).translate([0, 0, -0.5])
    if style == "coursed":
        return ashlar(reg, course=(1.2, 1.8), length=(5.0, 11.0), d=0.45, seed=seed, rough=0.1)
    if style in FOUNDATION_EXTRA:
        return FOUNDATION_EXTRA[style](reg, seed)
    raise ValueError(style)


# ------------------------------------------------------------------ belt courses (4.4 mm tall; cyma 4.0)
BELTS = {
    # name: (profile [(d, z)], blocks or None)
    "modillion": ([(0.0, 0.0), (0.4, 0.4), (0.4, 0.8), (0.8, 1.2), (0.8, 2.8), (1.4, 3.4), (1.4, 3.6), (1.8, 4.0), (1.8, 4.4)],
                  dict(w=0.9, z=1.4, h=1.2, d0=0.8, d=0.5, c=0.35, pitch=3.0, margin=1.8)),
    "dentil": ([(0.0, 0.0), (0.6, 0.6), (0.6, 2.8), (1.2, 3.4), (1.2, 3.8), (1.6, 4.2), (1.6, 4.4)],
               dict(w=0.6, z=2.0, h=0.8, d0=0.6, d=0.4, c=0.15, pitch=1.2, margin=1.0)),
    "stone": ([(0.0, 0.0), (1.2, 1.2), (1.2, 3.8), (1.0, 4.0), (1.0, 4.4)], None),
    "double": ([(0.0, 0.0), (0.6, 0.6), (0.6, 1.4), (0.3, 1.7), (0.3, 2.4), (0.9, 3.0), (0.9, 4.0), (0.6, 4.2),
                (0.6, 4.4)], None),
    "panel": ([(0.0, 0.0), (0.5, 0.5), (0.5, 3.6), (1.1, 4.2), (1.1, 4.4)],
              dict(w=4.0, z=1.0, h=2.2, d0=0.5, d=0.3, c=0.2, pitch=6.0, margin=2.4)),
    "drip": ([(0.0, 0.0), (1.0, 1.0), (1.0, 2.2), (0.4, 4.4)], None),
    "billet": ([(0.0, 0.0), (0.8, 0.8), (0.8, 3.6), (1.2, 4.0), (1.2, 4.4)],
               dict(w=1.0, z=1.6, h=1.0, d0=0.8, d=0.5, c=0.3, pitch=2.0, margin=1.0)),
    "cleat": ([(0.0, 0.0), (0.5, 0.5), (0.5, 3.8), (0.8, 4.1), (0.8, 4.4)],
              dict(w=0.6, z=0.8, h=3.0, d0=0.5, d=0.35, c=0.15, pitch=4.0, margin=1.6)),
    "bead": ([(0.0, 0.0), (0.4, 0.4), (0.4, 3.2), (0.7, 3.5), (0.7, 3.9), (0.4, 4.2), (0.4, 4.4)], None),
    "sill": ([(0.0, 0.0), (0.5, 0.5), (0.5, 2.8), (1.4, 3.7), (1.4, 4.4)], None),
    "ovolo": ([(0.0, 0.0), (0.3, 0.3), (0.7, 0.7), (0.9, 1.1), (1.0, 1.6), (0.9, 2.1), (0.7, 2.5), (0.7, 3.4),
               (1.1, 3.8), (1.1, 4.4)], None),
    "string": ([(0.0, 0.0), (0.5, 0.5), (0.5, 3.4), (1.1, 4.0), (1.1, 4.4)], None),
    "cyma": ([(0.0, 0.0), (0.4, 0.4), (0.7, 0.8), (0.85, 1.2), (0.9, 1.6), (1.0, 2.0), (1.2, 2.3), (1.5, 2.6),
              (1.5, 3.2), (1.2, 3.5), (1.2, 4.0)], None),
    # a fascia carrying three half-round reeds (the Juniper)
    "reeded": ([(0.0, 0.0), (0.4, 0.4), (0.4, 0.8), (0.7, 1.1), (0.7, 1.5), (0.4, 1.8), (0.7, 2.1), (0.7, 2.5),
                (0.4, 2.8), (0.7, 3.1), (0.7, 3.5), (0.4, 3.8), (0.8, 4.2), (0.8, 4.4)], None),
    # a fascia carrying a half-round astragal between two fillets (the Larkspur)
    "astragal": ([(0.0, 0.0), (0.4, 0.4), (0.4, 1.8), (0.6, 2.0), (0.8, 2.2), (0.9, 2.6), (0.8, 3.0), (0.6, 3.2),
                  (0.4, 3.2), (0.4, 3.6), (0.8, 4.0), (0.8, 4.4)], None),
    # a fascia with tall raised tablets (the Laurel)
    "tablet": ([(0.0, 0.0), (0.4, 0.4), (0.4, 3.4), (0.9, 3.9), (0.9, 4.4)],
               dict(w=1.4, z=0.8, h=2.4, d0=0.4, d=0.45, c=0.2, pitch=4.2, margin=2.2)),
    # a stepped band with small blocks in pairs (the Myrtle)
    "twinblock": ([(0.0, 0.0), (0.5, 0.5), (0.5, 2.8), (1.0, 3.3), (1.0, 3.8), (1.3, 4.1), (1.3, 4.4)],
                  dict(w=0.7, z=1.0, h=1.6, d0=0.5, d=0.4, c=0.2, pitch=5.6, pair=1.5, margin=2.6)),
    # a brick corbel table: three courses each stepping out, a row of dentil headers under the
    # top one (the Magnolia)
    "corbel": ([(0.0, 0.0), (0.2, 0.2), (0.2, 1.0), (0.5, 1.3), (0.5, 2.2), (0.8, 2.5), (0.8, 3.4), (1.1, 3.7),
                (1.1, 4.4)], dict(w=0.9, z=2.4, h=0.8, d0=0.8, d=0.35, c=0.12, pitch=1.6, margin=0.8)),
    # a fascia carrying a raised zigzag between fillets (the Hawthorn)
    "zigzag": ([(0.0, 0.0), (0.4, 0.4), (0.4, 0.8), (0.6, 1.0), (0.6, 3.2), (0.9, 3.5), (0.9, 4.4)],
               dict(kind="zigzag", w0=0.6, z0=1.4, z1=2.8, pitch=1.6, margin=0.6)),
    # a fascia hung with swags between rosettes (the Camellia)
    "swag": ([(0.0, 0.0), (0.5, 0.5), (0.5, 3.4), (0.9, 3.8), (0.9, 4.4)],
             dict(kind="swag", w0=0.5, zr=2.9, sag=1.5, pitch=4.4, margin=0.9)),
    # two stepped fascias (the Rosecroft)
    "fillet": ([(0.0, 0.0), (0.4, 0.4), (0.4, 1.6), (0.8, 2.0), (0.8, 3.6), (1.2, 4.0), (1.2, 4.4)], None),
    # a bell-cast shingled skirt: widest at its foot, three courses of shingle butts
    "flare": ([(0.0, 0.0), (1.6, 0.0), (1.6, 0.4), (1.1, 1.4), (1.3, 1.4), (0.8, 2.4), (1.0, 2.4), (0.5, 3.4),
               (0.7, 3.4), (0.2, 4.2), (0.2, 4.4)], None),
    "roll": ([(0.0, 0.0), (0.4, 0.4), (0.6, 0.8), (0.6, 1.2), (0.4, 1.6), (0.4, 2.8), (1.0, 3.4), (1.0, 4.4)], None),
    "cavetto": ([(0.0, 0.0), (0.3, 0.3), (0.3, 1.2), (0.6, 1.5), (1.0, 2.2), (1.3, 3.2), (1.3, 3.6), (1.6, 3.9),
                 (1.6, 4.4)], None),
    "fascia": ([(0.0, 0.0), (0.4, 0.4), (0.4, 2.6), (0.9, 3.1), (0.9, 3.4), (1.3, 3.8), (1.3, 4.4)], None),
    "torus": ([(0.0, 0.0), (0.4, 0.4), (0.4, 1.0), (0.9, 1.5), (1.2, 1.9), (1.3, 2.3), (1.2, 2.7), (0.9, 3.1),
               (0.6, 3.4), (0.6, 3.6), (1.0, 4.0), (1.0, 4.4)], None),
    "boss": ([(0.0, 0.0), (0.7, 0.7), (0.7, 3.4), (1.3, 4.0), (1.3, 4.4)],
             dict(w=1.2, z=1.6, h=1.2, d0=0.7, d=0.45, c=0.4, pitch=3.6, margin=2.0)),
}


# ------------------------------------------------------------------ eave brackets (side profiles, w out, v up)
def bracket(style, h, d, t, u=0.0, v_top=0.0, w0=0.0):
    """An eave bracket of height h projecting d, t wide, top at v_top. Styles:
    scroll (the Italianate console), block (a stepped modillion block), curve (a quarter-
    round bracket with a drop), pendant (a scroll over a hanging turned drop), fan (a
    pierced quarter-round), brace (a diagonal stick brace), metal (a pressed-metal bracket:
    a block head, an ogee and a round drop), sawn (a flat jigsawn bracket, pierced), modillion
    (a horizontal console under a cornice, its front rolled under), knee, volute, beaded (a
    console whose sloping front is a string of three beads), fret, ladder, acanthus (an S
    console with a lobed front and an open eye), twin (two slim consoles on one head) and cove
    (a square head over a concave sweep), tongue (a long slim taper with a round end), ring
    (a sawn bracket pierced with a round eye), comma (a round head curling down to a point) and
    stepped (a corbel of three steps)."""
    from .ornament import console, side_profile
    if style == "scroll":
        return console(h, d, t, u=u, v_top=v_top, w0=w0)
    if style == "block":
        prof = poly([(0, 0), (d, 0), (d, -h * 0.35), (d * 0.7, -h * 0.35 - d * 0.3), (d * 0.7, -h * 0.65),
                     (d * 0.35, -h * 0.65 - d * 0.35), (0.0, -h)])
    elif style == "curve":
        pts = [(0, 0), (d, 0)] + [(d - d * (1 - math.cos(a)) * 0.85, -h * 0.8 * math.sin(a))
                                  for a in np.linspace(0.1, math.pi / 2, 10)] + [(0.3 * d, -h), (0, -h)]
        prof = cs_union([poly(pts), circle((0.3 * d, -h + 0.45), 0.5, 14)])
    elif style == "pendant":
        hp = round(h * 0.7 / 0.2) * 0.2          # its flat underside on the layer grid
        pts = [(0, 0), (d, 0)] + [(d * (1 - 0.7 * (3 * s * s - 2 * s ** 3)), -hp * s) for s in np.linspace(0.05, 1, 10)] + \
              [(0, -hp)]
        prof = cs_union([poly(pts), rect(0.0, -h, 0.6, -hp + 0.01), circle((0.3, -h + 0.45), 0.45, 12)])
    elif style == "fan":
        disc = circle((0.0, 0.0), min(d, h), 32) ^ rect(0.0, -h, d, 0.0)
        slots = cs_union([stroke([(0.9 * math.cos(a), -0.9 * math.sin(a)), ((min(d, h) - 0.6) * math.cos(a),
                                                                             -(min(d, h) - 0.6) * math.sin(a))], 0.5)
                          for a in (0.45, 0.8, 1.15)])
        prof = cs_union([disc - slots, rect(0.0, -h, 0.6, 0.0)])
    elif style == "metal":               # a pressed-metal cornice bracket: a block head over an ogee and a drop
        hd = round(0.45 * d / 0.2) * 0.2
        pts = [(0, 0), (d, 0), (d, -h * 0.28)] + \
              [(d - (d - hd) * (3 * s * s - 2 * s ** 3), -h * 0.28 - h * 0.44 * s) for s in np.linspace(0.1, 1, 9)] + \
              [(hd, -h + 0.9), (0.0, -h + 0.9)]
        prof = cs_union([poly(pts), circle((hd * 0.5, -h + 0.9), min(0.8, hd * 0.5), 16)])
    elif style == "sawn":                # a flat jigsawn bracket: an S-curved edge, a round piercing, a drop
        pts = [(0, 0), (d, 0), (d, -h * 0.18)] + \
              [(d - (d - 0.6) * (3 * s * s - 2 * s ** 3), -h * 0.18 - h * 0.82 * s) for s in np.linspace(0.08, 1, 12)] + \
              [(0.0, -h)]
        r = min(0.5, 0.16 * min(d, h))
        prof = cs_union([poly(pts), circle((0.3, -h + 0.3), 0.3, 12)]) - circle((0.42 * d, -0.36 * h), r, 16)
    elif style == "modillion":           # a scrolled modillion: a horizontal console, its front rolled under
        r = min(0.5 * h, 0.3 * d)
        prof = cs_union([poly([(0, 0), (d, 0), (d, -h * 0.5), (0.0, -h)]), circle((d - r, -h * 0.5), r, 16)])
    elif style == "knee":                # a big ship's-knee bracket: a concave curve from the wall to the tip
        pts = [(0, 0), (d, 0), (d, -0.9)] + \
              [(d - (d - 0.8) * (1 - math.cos(a)), -0.9 - (h - 0.9) * math.sin(a)) for a in np.linspace(0.08, math.pi / 2, 12)] + \
              [(0.0, -h)]
        prof = poly(pts) - circle((0.36 * d, -0.36 * h), min(0.6, 0.12 * min(d, h)), 16)
    elif style == "volute":              # a bracket whose face is a double volute: a big scroll over a small one
        r1, r2 = min(0.32 * h, 0.45 * d), min(0.2 * h, 0.3 * d)
        prof = cs_union([poly([(0, 0), (d, 0), (d, -r1), (d * 0.45, -h + r2), (0.0, -h)]),
                         circle((d - r1, -r1), r1, 20), circle((d * 0.45, -h + r2), r2, 16)])
        prof = prof - circle((d - r1, -r1), r1 * 0.4, 12)
    elif style == "beaded":              # a console whose sloping front is a string of three beads
        a, b = (d, -h * 0.25), (0.35 * d, -h)
        r = 0.5 * math.hypot(a[0] - b[0], a[1] - b[1]) / 3
        prof = cs_union([poly([(0, 0), (d, 0), a, b, (0.0, -h)])] +
                        [circle((a[0] + (b[0] - a[0]) * (k + 0.5) / 3, a[1] + (b[1] - a[1]) * (k + 0.5) / 3), r, 16)
                         for k in range(3)])
    elif style == "fret":                # an Eastlake fret bracket: a quarter disc pierced with a ring and slots
        q = circle((0.0, 0.0), min(d, h), 40) ^ rect(0.0, -h, d, 0.0)
        r0 = min(d, h)
        cut = circle((r0 * 0.42, -r0 * 0.42), r0 * 0.22, 20)
        slots = cs_union([stroke([(r0 * 0.25 * math.cos(a), -r0 * 0.25 * math.sin(a)),
                                  ((r0 - 0.6) * math.cos(a), -(r0 - 0.6) * math.sin(a))], 0.5) for a in (0.2, 1.37)])
        prof = cs_union([q - cut - (slots ^ q.offset(-0.55)), rect(0.0, -h, 0.6, 0.0), rect(0.0, -0.6, d, 0.0)])
    elif style == "ladder":              # Eastlake: a triangle whose face is cut into a ladder of rungs
        tri = poly([(0, 0), (d, 0), (0.0, -h)])
        slots = cs_union([rect(0.55, -h + 0.9 + k * (h - 1.6) / 4, d * 0.95, -h + 0.9 + k * (h - 1.6) / 4 + 0.5)
                          for k in range(4)])
        prof = tri - (slots ^ tri.offset(-0.55))
    elif style == "acanthus":           # an Italianate console: an S sweeping in to a curl, its front lobed like a leaf,
        # an open eye in the head (the Laurel)
        front = [(d * (1 - 0.7 * (3 * s * s - 2 * s ** 3)), -h * s) for s in np.linspace(0.0, 1.0, 17)]
        body = poly([(0.0, 0.0)] + front + [(0.0, -h)])
        lobes = cs_union([circle((front[i][0] - 0.2, front[i][1]), 0.42, 16) for i in (5, 8, 11)])
        foot = circle((0.3 * d + 0.1, -h + 0.5), 0.5, 16)
        r_eye = min(0.3 * d, 0.45)
        eye = circle((d * 0.55, -r_eye - 0.7), r_eye, 16)
        prof = cs_union([body, lobes, foot, rect(0.0, -h, 0.6, 0.0)]) - eye
    elif style == "twin":               # a pair of slim quarter-round consoles on one head block (the Myrtle)
        pts = [(0, 0), (d, 0)] + [(d - d * (1 - math.cos(a)) * 0.8, -h * 0.85 * math.sin(a))
                                  for a in np.linspace(0.1, math.pi / 2, 10)] + [(0.0, -h)]
        blade = cs_union([poly(pts), circle((0.35, -h + 0.4), 0.4, 12)])
        tb = max(0.5, t * 0.36)
        head = side_profile(rect(0.0, -0.8, d, 0.0), -t / 2, t / 2)
        pair = [side_profile(blade, sg * t / 2 - (tb if sg > 0 else 0.0), sg * t / 2 + (tb if sg < 0 else 0.0))
                for sg in (-1, 1)]
        return union([head] + pair).translate([u, v_top, w0])
    elif style == "tongue":             # a long slim tongue: a square head, a straight taper and a round end (the Juniper)
        prof = cs_union([poly([(0.0, 0.0), (d, 0.0), (d, -0.8), (0.9, -h + 0.45), (0.0, -h + 0.45)]),
                         circle((0.45, -h + 0.45), 0.45, 16)])
    elif style == "cove":               # a square head over a concave quarter-round sweep and a foot block (the Larkspur)
        hd = min(1.0, h * 0.25)
        R_ = min(d - 0.6, h - hd - 0.6)
        pts = [(0.0, 0.0), (d, 0.0), (d, -hd)] + \
              [(d - R_ + R_ * math.cos(a), -hd - R_ + R_ * math.sin(a)) for a in np.linspace(0.0, -math.pi / 2, 12)][1:] + \
              [(0.6, -hd - R_), (0.6, -h), (0.0, -h)]
        prof = poly(pts)
    elif style == "stepped":            # a corbel of three steps, each shorter and further out (the Magnolia)
        prof = poly([(0.0, 0.0), (d, 0.0), (d, -h * 0.3), (d * 0.66, -h * 0.3), (d * 0.66, -h * 0.62), (d * 0.33, -h * 0.62),
                     (d * 0.33, -h), (0.0, -h)])
    elif style == "comma":              # a sawn bracket curling like a comma: a round head tapering down to a point (the Wisteria)
        R_ = min(d, h) * 0.42
        cx_, cy_ = d - R_, -R_
        tail = [(0.0, 0.0), (d, 0.0)] + [(cx_ + R_ * math.cos(a), cy_ + R_ * math.sin(a)) for a in np.linspace(0.0, -math.pi * 0.9, 10)]
        tail += [(0.55, -h + 0.3), (0.0, -h + 0.3)]
        prof = cs_union([poly(tail), circle((0.3, -h + 0.35), 0.35, 12)])
    elif style == "ring":               # a sawn bracket pierced with a round eye, a ball at its foot (the Camellia)
        body = poly([(0.0, 0.0), (d, 0.0), (d, -0.8), (0.7, -h + 0.5), (0.0, -h + 0.5)])
        rr = max(0.5, min(d, h) * 0.17)
        eye = circle((0.2 + d * 0.38, -h * 0.34), rr, 20)
        prof = cs_union([body - eye, circle((0.35, -h + 0.45), 0.45, 16)])
    elif style == "brace":
        prof = cs_union([rect(0.0, -h, 0.6, 0.0), rect(0.0, -0.6, d, 0.0),
                         poly([(0.0, -h * 0.85), (0.6, -h * 0.85), (d, -0.4), (d - 0.8, -0.2)])])
    elif style in BRACKET_EXTRA:        # side profile from another module (hoarch.colonial)
        prof = BRACKET_EXTRA[style](h, d, t)
    else:
        raise ValueError(style)
    return side_profile(prof, -t / 2, t / 2).translate([u, v_top, w0])

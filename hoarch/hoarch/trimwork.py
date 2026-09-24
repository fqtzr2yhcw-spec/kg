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
def _faces(w, d):
    return [Facade((-w / 2, -d / 2), (w / 2, -d / 2)), Facade((w / 2, -d / 2), (w / 2, d / 2)),
            Facade((w / 2, d / 2), (-w / 2, d / 2)), Facade((-w / 2, d / 2), (-w / 2, -d / 2))]


def _skin(w, d, z0, z1, fn, margin=0.1):
    out = []
    for i, f in enumerate(_faces(w, d)):
        reg = rect(margin, z0, f.L - margin, z1)
        out.append(f.place(fn(reg, i).translate([0, 0, -0.02])))       # sunk a hair: one solid with the shaft
    return union(out)


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
    if style == "stovepipe":
        # a sheet-iron flue: a band, and a cone cap flaring at 45 degrees (w = pipe diameter)
        r = w / 2
        body = M.cylinder(h - 2.0, r, r, 28) + M.cylinder(0.6, r + 0.3, r + 0.3, 28).translate([0, 0, round(h * 0.55 / 0.2) * 0.2])
        cap = M.cylinder(1.0, r, r + 1.0, 28).translate([0, 0, h - 2.01]) + \
            M.cylinder(1.0, r + 1.0, 0.3, 28).translate([0, 0, h - 1.02])
        return body + cap
    raise ValueError(style)


CHIMNEYS = ("corbel", "stucco", "paneled", "banded", "slim", "diagonal", "stone", "ribbed", "plain", "arched", "party",
            "stovepipe", "coped", "hooded", "stepped")


# ------------------------------------------------------------------ finials (revolved, printed upright)
def finial(style, r=1.2, h=8.0, seg=28):
    """Turned finials, one per building with a tower, spire or cupola:
    urn (Beaumont), acorn (Ashby), iron (Harcourt), ball (Fowler), stack (Ardmore),
    spire (Carrow), onion (the drugstore's turret)."""
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
    board skirting)."""
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
    raise ValueError(style)


# ------------------------------------------------------------------ belt courses (all 4.4 mm tall)
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
    (a horizontal console under a cornice, its front rolled under)."""
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
    elif style == "volute":              # a bracket whose face is a double volute: a big scroll over a small one
        r1, r2 = min(0.32 * h, 0.45 * d), min(0.2 * h, 0.3 * d)
        prof = cs_union([poly([(0, 0), (d, 0), (d, -r1), (d * 0.45, -h + r2), (0.0, -h)]),
                         circle((d - r1, -r1), r1, 20), circle((d * 0.45, -h + r2), r2, 16)])
        prof = prof - circle((d - r1, -r1), r1 * 0.4, 12)
    elif style == "brace":
        prof = cs_union([rect(0.0, -h, 0.6, 0.0), rect(0.0, -0.6, d, 0.0),
                         poly([(0.0, -h * 0.85), (0.6, -h * 0.85), (d, -0.4), (d - 0.8, -0.2)])])
    else:
        raise ValueError(style)
    return side_profile(prof, -t / 2, t / 2).translate([u, v_top, w0])

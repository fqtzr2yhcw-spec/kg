"""Porch work styles, one set per building (see COLLECTION.md): posts, railings, the frieze
between the post tops (the "arcade"), and the skirt under the deck.

Posts and railings print upright (the joined frame of a run), so every post outline changes
at no more than 45 degrees going up and every railing member is a nozzle wide or more. The
frieze is a flat (u, v) outline cut into the arcade board, which prints on its top edge.
"""
import math

import numpy as np
from manifold3d import CrossSection as CS, JoinType, Manifold as M

from .core import box, circle, cs_union, poly, rect, union
from .ornament import ext, stroke


# ------------------------------------------------------------------ posts
def _clamp45(prof):
    out = [prof[0], prof[1]]
    for r, z in prof[2:]:
        r0, z0 = out[-1]
        if r > r0 and r - r0 > z - z0:
            z = z0 + (r - r0)
        out.append((r, max(z, z0)))
    return out


def _revolve(prof, seg=36):
    p = _clamp45(prof)
    p = p + [(0.0, p[-1][1])]
    return M.revolve(poly(p), seg)


def _top(h, sq, zb, rb, slot, seg=24, shape="round"):
    """A 45 degree flare from the shaft (radius rb at zb, round or square) to a square
    abacus 2*sq wide, the abacus up to h, and the arcade's slot across it."""
    if shape == "round":
        ring = [(rb * math.cos(a), rb * math.sin(a), zb - 0.01) for a in np.linspace(0, 2 * math.pi, seg, endpoint=False)]
        rise = max(0.2, sq * math.sqrt(2) - rb)
    else:
        ring = [(x, y, zb - 0.01) for x in (-rb, rb) for y in (-rb, rb)]
        rise = max(0.2, sq - rb)
    corners = [(x, y, zb + rise) for x in (-sq, sq) for y in (-sq, sq)]
    body = M.hull_points(ring + corners) + box([-sq, -sq, zb + rise - 0.01], [sq, sq, h])
    if slot:
        body = body - box([-slot[0] / 2, -sq - 1, h - slot[1]], [slot[0] / 2, sq + 1, h + 1])
    return body


def _plinth(p=3.2, ph=1.2):
    return box([-p / 2, -p / 2, 0.0], [p / 2, p / 2, ph])


def post_tuscan(h, collar=None, abacus=3.0, slot=(1.2, 1.0)):
    """Tuscan column: torus base, a shaft with entasis, an astragal and an echinus."""
    z1 = h - 2.8
    prof = [(0.0, 1.19), (1.6, 1.19), (1.6, 1.5), (1.45, 1.8), (1.4, 2.1), (1.38, 2.3),
            (1.34, 2.3 + 0.3 * (z1 - 2.3)), (1.22, 2.3 + 0.75 * (z1 - 2.3)), (1.12, z1),
            (1.3, z1 + 0.2), (1.3, z1 + 0.5), (1.12, z1 + 0.7), (1.12, z1 + 0.9)]
    body = _revolve(prof) + _plinth()
    return body + _top(h, abacus / 2, z1 + 0.9, 1.12, slot)


def post_fluted(h, collar=None, abacus=3.2, slot=(1.2, 1.0), n=10):
    """Fluted column: a double torus base, a straight shaft with ``n`` flutes, a bell
    capital."""
    z1 = h - 3.4
    prof = [(0.0, 1.19), (1.65, 1.19), (1.65, 1.45), (1.45, 1.75), (1.55, 2.05), (1.4, 2.35), (1.35, 2.5),
            (1.35, z1), (1.5, z1 + 0.15), (1.5, z1 + 0.45), (1.3, z1 + 0.65)]
    body = _revolve(prof, 40) + _plinth(3.4)
    fl = []
    for k in range(n):
        a = 2 * math.pi * k / n
        c = (1.35 * math.cos(a), 1.35 * math.sin(a))
        fl.append(M.cylinder(z1 - 3.4, 0.27, 0.27, 12).translate([c[0], c[1], 3.0]))
    body = body - union(fl)
    return body + _top(h, abacus / 2, z1 + 0.65, 1.3, slot, seg=40)


def post_chamfered(h, collar=None, abacus=3.0, slot=(1.2, 1.0), w=2.4, c=0.5):
    """Italianate square post, its corners chamfered between lamb's-tongue stops."""
    s = w / 2
    body = _plinth() + box([-s, -s, 1.0], [s, s, h - 1.9])
    z0, z1 = 3.2, h - 3.6
    if z1 - z0 > 2.0:
        for sx in (-1, 1):
            for sy in (-1, 1):
                # a chamfer wedge off each corner, run out at 45 degrees at both ends (stops)
                cx, cy = sx * s, sy * s
                wedge = M.hull_points([(cx + sx * 0.01, cy + sy * 0.01, z0 - 0.01), (cx + sx * 0.01, cy + sy * 0.01, z1 + 0.01),
                                       (cx - sx * c, cy + sy * 0.01, z0 + c), (cx + sx * 0.01, cy - sy * c, z0 + c),
                                       (cx - sx * c, cy + sy * 0.01, z1 - c), (cx + sx * 0.01, cy - sy * c, z1 - c)])
                body = body - wedge
    return body + _top(h, abacus / 2, h - 1.9, s, slot, shape="square")


def post_clustered(h, collar=None, abacus=3.0, slot=(1.2, 1.0)):
    """Gothic clustered shaft: four round shafts about a square core (a quatrefoil section),
    on an octagonal base, under an octagonal moulded capital."""
    sect = cs_union([circle((dx * 0.62, dy * 0.62), 0.72, 20) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
                    + [rect(-0.7, -0.7, 0.7, 0.7)])
    oct_ = CS.circle(1.55, 8).rotate(22.5)
    body = _plinth() + M.extrude(oct_, 1.0).translate([0, 0, 1.19])
    z1 = h - 2.4
    body = body + M.extrude(sect, z1 - 2.1).translate([0, 0, 2.1])
    # capital: an octagonal ring over the shafts, flaring to the abacus
    body = body + M.extrude(CS.circle(1.45, 8).rotate(22.5), 0.4).translate([0, 0, z1 - 0.4])
    return body + _top(h, abacus / 2, z1, 1.45, slot, seg=8)


def post_stick(h, collar=None, abacus=3.0, slot=(1.2, 1.0), w=2.2):
    """Stick-style square post with a sunk groove down each face and a notched band
    under a plain cap."""
    s = w / 2
    body = _plinth() + box([-s, -s, 1.0], [s, s, h - 1.8])
    z0, z1 = 2.6, h - 4.0
    for ax in range(4):
        g = box([-0.25, s - 0.3, z0], [0.25, s + 0.1, z1])
        body = body - g.rotate([0, 0, 90 * ax])
    band = box([-s - 0.3, -s - 0.3, h - 3.6], [s + 0.3, s + 0.3, h - 2.8])
    band = band - union([box([-s - 1, -0.3, h - 3.4], [s + 1, 0.3, h - 3.0]), box([-0.3, -s - 1, h - 3.4], [0.3, s + 1, h - 3.0])])
    body = body + band
    return body + _top(h, abacus / 2, h - 1.8, s, slot, shape="square")


def post_spindle(h, collar=None, abacus=2.8, slot=(1.2, 1.0)):
    """Folk Victorian turned spindle post: a slim shaft ringed with bead-and-reel turnings
    along its length (a bead at the railing's hand rail)."""
    z0, z1 = 1.8, h - 2.4
    prof = [(0.0, 1.19), (1.45, 1.19), (1.45, 1.5), (1.05, 1.8)]
    beads = []
    z = z0 + 1.6
    while z < z1 - 1.2:
        beads.append(z)
        z += 3.2
    if collar is not None:
        beads = [b for b in beads if abs(b - (collar - 0.5)) > 1.8] + [collar - 0.5]
    for zb in sorted(beads):
        prof += [(1.05, zb - 0.45), (1.4, zb - 0.1), (1.4, zb + 0.3), (1.05, zb + 0.65)]
    prof += [(1.05, z1)]
    body = _revolve(prof) + _plinth(3.0)
    return body + _top(h, abacus / 2, z1, 1.05, slot)


def post_eastlake(h, collar=None, abacus=3.0, slot=(1.2, 1.0)):
    """Eastlake post: square blocks (base, a block at the hand rail, a top block with
    incised lines) joined by turned shafts."""
    rail = (collar if collar is not None else 9.0)
    s = 1.3

    def block(z0, z1, grooves=False):
        b = box([-s, -s, z0], [s, s, z1])
        # 45 degree chamfer top and bottom
        b = b ^ M.hull_points([(x, y, z) for x in (-s, s) for y in (-s, s) for z in (z0 + 0.4, z1 - 0.4)] +
                              [(x, y, z) for x in (-s + 0.4, s - 0.4) for y in (-s + 0.4, s - 0.4) for z in (z0, z1)])
        if grooves:
            for zz in (z0 + 0.9, z1 - 1.3):
                b = b - union([box([-s - 1, -s - 1, zz], [s + 1, -s + 0.25, zz + 0.4]).rotate([0, 0, 90 * k])
                               for k in range(4)])
        return b

    def shaft(z0, z1):
        L = z1 - z0
        prof = [(0.0, z0), (1.0, z0), (1.0, z0 + 0.3), (1.2, z0 + 0.35 * L), (1.0, z0 + 0.7 * L), (0.9, z1)]
        return _revolve(prof)
    b0 = block(0.0, 3.4)
    b1 = block(rail - 2.0, rail + 0.6)
    b2 = block(h - 4.2, h - 1.8, grooves=True)
    body = union([b0, b1, b2, shaft(3.2, rail - 1.8), shaft(rail + 0.4, h - 4.0)])
    return body + _top(h, abacus / 2, h - 1.8, s, slot, shape="square")


def post_turned(h, collar=None, **kw):
    from .features import turned_post
    return turned_post(h, collar=collar)


POSTS = {"turned": post_turned, "tuscan": post_tuscan, "fluted": post_fluted, "chamfered": post_chamfered,
         "clustered": post_clustered, "stick": post_stick, "spindle": post_spindle, "eastlake": post_eastlake}


# ------------------------------------------------------------------ railing fills (between the rails)
def _flat(cs, t=0.8):
    """A flat (u, v) outline as a railing member, t thick across (w), centred."""
    m = M.extrude(cs, t).translate([0, 0, -t / 2])
    # (u, v, w) -> railing frame (x = u, y = w, z = v)
    return m.transform(np.array([[1.0, 0, 0, 0], [0, 0, 1.0, 0], [0, 1.0, 0, 0]]))


def fill_flat(style, L, vb, vt):
    """Railing fill between the bottom rail (top at vb) and the hand rail (bottom at vt),
    for the flat styles. Returns a solid in the railing frame (u, w, v)."""
    H = vt - vb
    parts = []
    bar = 0.55
    if style == "chippendale":
        n = max(1, int(round(L / (H * 1.1))))
        for i in range(n):
            a, b = L * i / n, L * (i + 1) / n
            parts += [stroke([(a + 0.2, vb), (b - 0.2, vt)], bar, caps=False), stroke([(a + 0.2, vt), (b - 0.2, vb)], bar, caps=False),
                      rect(a - bar / 2, vb, a + bar / 2, vt)]
            m = (a + b) / 2
            parts.append(poly([(m, vb + H * 0.2), (m + (b - a) * 0.3, vb + H / 2), (m, vt - H * 0.2), (m - (b - a) * 0.3, vb + H / 2)])
                         - poly([(m, vb + H * 0.2 + 0.8), (m + (b - a) * 0.3 - 0.8, vb + H / 2), (m, vt - H * 0.2 - 0.8),
                                 (m - (b - a) * 0.3 + 0.8, vb + H / 2)]))
        parts.append(rect(L - bar / 2, vb, L + bar / 2, vt))
    elif style == "x":
        p = 3.2
        n = max(1, int(round(L / p)))
        for i in range(n):
            a, b = L * i / n, L * (i + 1) / n
            parts += [stroke([(a, vb), (b, vt)], bar + 0.1, caps=False), stroke([(a, vt), (b, vb)], bar + 0.1, caps=False),
                      rect(a - 0.35, vb, a + 0.35, vt)]
        parts.append(rect(L - 0.35, vb, L + 0.35, vt))
    elif style == "pierced":
        board = rect(0.0, vb, L, vt)
        holes = []
        n = max(1, int(round(L / 2.6)))
        r = min(0.55, H * 0.15)
        for i in range(n):
            c = (L * (i + 0.5) / n, vb + H / 2)
            q = cs_union([circle((c[0] + dx * r, c[1] + dy * r), r, 16) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))])
            holes.append(q)
        parts.append(board - cs_union(holes))
    elif style == "sawn":
        n = max(1, int(round(L / 1.9)))
        for i in range(n):
            u = L * (i + 0.5) / n
            prof = [(0.0, 0.35), (0.12, 0.3), (0.3, 0.55), (0.45, 0.8), (0.58, 0.7), (0.7, 0.35), (0.8, 0.3),
                    (0.88, 0.5), (1.0, 0.4)]
            left = [(u - w, vb + t * H) for t, w in prof]
            right = [(u + w, vb + t * H) for t, w in reversed(prof)]
            parts.append(poly(left + right))
    else:
        raise ValueError(style)
    cs = cs_union(parts) ^ rect(0.0, vb - 0.05, L, vt + 0.05)
    cs = cs.offset(-0.25, JoinType.Round).offset(0.25, JoinType.Round)
    return _flat(cs)


def baluster_vase(h, seg=24):
    """Symmetrical double-vase baluster (heavy, Italianate)."""
    t = [(0.0, 0.62), (0.08, 0.62), (0.12, 0.45), (0.3, 0.72), (0.42, 0.5), (0.5, 0.42), (0.58, 0.5),
         (0.7, 0.72), (0.88, 0.45), (0.92, 0.62), (1.0, 0.62)]
    prof = [(0.0, 0.0)] + [(r, f * h) for f, r in t]
    return _revolve(prof, seg)


def baluster_urn(h, seg=28):
    """Squat urn baluster of a stone balustrade."""
    t = [(0.0, 0.8), (0.1, 0.8), (0.14, 0.55), (0.3, 0.9), (0.52, 0.85), (0.72, 0.5), (0.82, 0.45), (0.88, 0.7),
         (1.0, 0.7)]
    prof = [(0.0, 0.0)] + [(r, f * h) for f, r in t]
    return _revolve(prof, seg)


def spindle(h, r=0.33, seg=14):
    return M.cylinder(h, r, r, seg)


# ------------------------------------------------------------------ friezes (flat outlines per bay)
def frieze_scroll(u0, u1, v_bot, v_top):
    """Italianate: a paired scroll bracket against each post under a plain rail."""
    parts = [rect(u0, v_top - 0.8, u1, v_top + 0.05)]
    H = min(3.6, (v_top - v_bot) * 0.75)
    Wd = min(2.6, (u1 - u0) * 0.22)
    for sg, ue in ((1, u0), (-1, u1)):
        pts = []
        for i in range(15):
            s = i / 14
            ww = Wd * (1 - 0.8 * (3 * s * s - 2 * s * s * s))
            pts.append((ue + sg * ww, v_top - 0.8 - H * s))
        pts += [(ue, v_top - 0.8 - H), (ue, v_top - 0.7)]
        br = poly(pts)
        br = cs_union([br, circle((ue + sg * 0.55, v_top - 0.8 - H + 0.45), 0.55, 16),
                       circle((ue + sg * (Wd - 0.45), v_top - 1.35), 0.45, 16)])
        parts.append(br)
    return cs_union(parts)


def frieze_entablature(u0, u1, v_bot, v_top):
    """Classical: a frieze board with a row of dentils hanging from it."""
    parts = [rect(u0, v_top - 1.6, u1, v_top + 0.05)]
    u = u0 + 0.4
    while u + 0.6 < u1 - 0.3:
        parts.append(rect(u, v_top - 2.4, u + 0.6, v_top - 1.55))
        u += 1.1
    return cs_union(parts)


def frieze_valance(u0, u1, v_bot, v_top):
    """A shallow segmental arch from post to post with a fringe of drops, solid above."""
    mid, half = (u0 + u1) / 2, (u1 - u0) / 2
    spring = v_top - 3.4
    rise = 2.0
    r = (half * half + rise * rise) / (2 * rise)
    cy = spring + rise - r
    arch = circle((mid, cy), r, 96)
    solid = rect(u0, spring, u1, v_top + 0.05) - arch
    band = (circle((mid, cy), r + 0.0, 96) - circle((mid, cy), r - 0.7, 96)) ^ rect(u0, spring - 1, u1, v_top)
    parts = [solid, band]
    n = max(2, int((u1 - u0) / 1.8))
    for k in range(1, n):
        u = u0 + (u1 - u0) * k / n
        v = cy + math.sqrt(max(r * r - (u - mid) ** 2, 0.0)) - 0.7
        if v < spring:
            continue
        parts.append(cs_union([rect(u - 0.28, v - 0.9, u + 0.28, v + 0.1), circle((u, v - 1.1), 0.4, 14)]))
    holes = []
    for k in range(1, n):
        u = u0 + (u1 - u0) * k / n
        vv = cy + math.sqrt(max(r * r - (u - mid) ** 2, 0.0))
        if v_top - vv > 2.2:
            holes.append(circle((u, (vv + v_top - 0.8) / 2), 0.45, 14))
    out = cs_union(parts)
    if holes:
        out = out - cs_union(holes)
    return out


def frieze_spindle(u0, u1, v_bot, v_top):
    """Ball-and-stick spindle frieze over a rail, with a sawn fan bracket at each post."""
    rail0, rail1 = v_top - 2.8, v_top - 2.0
    parts = [rect(u0, rail0, u1, rail1)]
    n = max(2, int((u1 - u0) / 1.4))
    for k in range(n):
        u = u0 + (u1 - u0) * (k + 0.5) / n
        parts += [rect(u - 0.28, rail1 - 0.05, u + 0.28, v_top + 0.05), circle((u, (rail1 + v_top) / 2), 0.45, 14)]
    for sg, ue in ((1, u0), (-1, u1)):
        R = 2.6
        fan = circle((ue, rail0), R, 32) ^ rect(min(ue, ue + sg * R), rail0 - R, max(ue, ue + sg * R), rail0)
        slots = cs_union([stroke([(ue + sg * 1.0 * math.cos(a), rail0 - 1.0 * math.sin(a)),
                                  (ue + sg * (R - 0.6) * math.cos(a), rail0 - (R - 0.6) * math.sin(a))], 0.5)
                          for a in (0.45, 0.85, 1.25)])
        parts.append(fan - slots)                      # the slots stop short of hub and rim: one piece
    return cs_union(parts)


def frieze_fret(u0, u1, v_bot, v_top):
    """Eastlake fretwork: a row of rings between two rails, quarter sunbursts at the posts."""
    rail0, rail1 = v_top - 3.0, v_top - 2.3
    parts = [rect(u0, rail0, u1, rail1)]
    D = v_top - rail1
    n = max(2, int((u1 - u0 - 2.0) / (D + 0.2)))
    for k in range(n):
        u = u0 + 1.0 + (u1 - u0 - 2.0) * (k + 0.5) / n
        c = (u, (rail1 + v_top) / 2)
        parts.append(circle(c, D / 2 + 0.05, 24) - circle(c, D / 2 - 0.5, 24))
    for sg, ue in ((1, u0), (-1, u1)):
        R = 2.2
        q = circle((ue, rail0), R, 32) ^ rect(min(ue, ue + sg * R), rail0 - R, max(ue, ue + sg * R), rail0)
        rays = cs_union([stroke([(ue, rail0), (ue + sg * R * math.cos(a), rail0 - R * math.sin(a))], 0.55)
                         for a in (0.2, 0.6, 1.0, 1.37)])
        rim = q - circle((ue, rail0), R - 0.55, 32)
        parts.append(rays ^ q)
        parts.append(rim)
    return cs_union(parts)


FRIEZES = {"scroll": frieze_scroll, "entablature": frieze_entablature, "valance": frieze_valance,
           "spindle": frieze_spindle, "fret": frieze_fret}


# ------------------------------------------------------------------ skirts (under the deck)
def skirt_fill(style, reg, d=1.2):
    """Skirt infill between the piers, in the deck's facade frame (u, v, w from 0 to d)."""
    if reg.is_empty():
        return M()
    u0, v0, u1, v1 = reg.bounds()
    if style == "square":
        vs = cs_union([rect(u, v0 - 1, u + 0.5, v1 + 1) for u in np.arange(u0 + 0.6, u1, 1.6)]) ^ reg
        hs = cs_union([rect(u0 - 1, v, u1 + 1, v + 0.5) for v in np.arange(v0 + 0.6, v1, 1.6)]) ^ reg
        return M.extrude(vs, d / 2) + M.extrude(hs, d / 2).translate([0, 0, d / 2])
    if style == "slats":
        s = cs_union([rect(u, v0 - 1, u + 1.0, v1 + 1) for u in np.arange(u0 + 0.3, u1, 1.6)]) ^ reg
        return M.extrude(s, d)
    if style == "hslats":
        s = cs_union([rect(u0 - 1, v, u1 + 1, v + 0.8) for v in np.arange(v0 + 0.4, v1, 1.4)]) ^ reg
        return M.extrude(s, d)
    if style == "pickets":              # vertical boards with pointed tops (Gothic)
        out = []
        for u in np.arange(u0 + 0.3, u1 - 0.8, 1.6):
            out.append(poly([(u, v0), (u + 1.0, v0), (u + 1.0, v1 - 1.0), (u + 0.5, v1 - 0.4), (u, v1 - 1.0)]))
        return M.extrude(cs_union(out) ^ reg, d)
    if style == "panels":
        board = M.extrude(reg, d * 0.5)
        pn = []
        L = u1 - u0
        n = max(1, int(round(L / 6.0)))
        for i in range(n):
            a, b = u0 + L * i / n + 0.6, u0 + L * (i + 1) / n - 0.6
            if b - a > 1.5 and v1 - v0 > 2.0:
                pn.append(rect(a, v0 + 0.6, b, v1 - 0.6))
        if pn:
            board = board + M.extrude(cs_union(pn) ^ reg, d).translate([0, 0, 0.0])
        return board
    if style == "arches":               # a board with a row of round-headed openings
        L = u1 - u0
        n = max(1, int(round(L / 3.4)))
        holes = []
        for i in range(n):
            a, b = u0 + L * i / n + 0.6, u0 + L * (i + 1) / n - 0.6
            r = (b - a) / 2
            top = v1 - 0.8
            spring = top - r
            if spring - (v0 + 0.8) > 0.4:
                holes.append(cs_union([rect(a, v0 + 0.8, b, spring), circle(((a + b) / 2, spring), r, 24)]))
        board = reg - cs_union(holes) if holes else reg
        return M.extrude(board, d)
    if style == "diamond":              # a board pierced with a row of diamonds (steep sides print clean)
        L = u1 - u0
        n = max(1, int(round(L / 3.0)))
        vm, hh = (v0 + v1) / 2, (v1 - v0) / 2 - 0.7
        holes = []
        for i in range(n):
            c = u0 + L * (i + 0.5) / n
            hw = min(L / n / 2 - 0.45, hh * 0.8)
            if hw > 0.4 and hh > 0.5:
                holes.append(poly([(c - hw, vm), (c, vm - hh), (c + hw, vm), (c, vm + hh)]))
        board = reg - cs_union(holes) if holes else reg
        return M.extrude(board, d)
    from .core import lattice
    return lattice(reg, pitch=1.8, bar=0.5, d=d)

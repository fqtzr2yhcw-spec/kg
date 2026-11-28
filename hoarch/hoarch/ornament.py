"""Small architectural ornaments, built in a local (u, v, w) frame:
u along the facade, v up, w out of the wall (w = 0 is the mounting face).

Everything here is designed to print face-up (w -> print z) without supports."""
import math

import numpy as np
from manifold3d import CrossSection as CS, JoinType, Manifold as M

from .core import RIB, SLOT, circle, cs_union, poly, rect, union


def ext(cs, w0, w1):
    """Extrude a (u, v) cross-section between w0 and w1."""
    if cs.is_empty() or w1 <= w0:
        return M()
    return M.extrude(cs, w1 - w0).translate([0, 0, w0])


def stepped(cs, steps):
    """Stack of extrusions: steps = [(inset, w0, w1), ...] (inset shrinks the outline)."""
    out = []
    for inset, w0, w1 in steps:
        c = cs if inset == 0 else cs.offset(-inset, JoinType.Miter, 4.0)
        if inset:   # drop what the inset thinned below a nozzle width (it prints as loose specks)
            c = c.offset(-RIB / 2 + 0.05, JoinType.Miter, 4.0).offset(RIB / 2 - 0.05, JoinType.Miter, 4.0)
        out.append(ext(c, w0, w1))
    return union(out)


def side_profile(profile_wv, u0, u1):
    """Extrude a (w, v) side profile (points or CrossSection) across u0..u1."""
    cs = profile_wv if isinstance(profile_wv, CS) else poly(profile_wv)
    m = M.extrude(cs, u1 - u0)          # profile in (x=w, y=v), extruded along z -> u
    return m.transform(np.array([[0, 0, 1.0, u0], [0, 1.0, 0, 0], [1.0, 0, 0, 0]]))


def chamfer_box(u0, v0, u1, v1, w0, d, c=None, square=(), bottom=None):
    """Rectangular block raised ``d`` from w0, its edges chamfered at 45 degrees by ``c``
    (default 0.6 d), except the edges named in ``square`` ("u0", "u1", "v0", "v1").

    The workhorse of the "square blocks" vocabulary: quoins, belt-course blocks, frieze
    panels, pedestal and capital blocks. With the chamfer, no edge overhangs more than
    d - c whichever way the part prints. ``bottom``: a separate chamfer for the v0 edge;
    bottom=d makes that edge a full 45 degree bevel from the wall (no ledge at all), for
    blocks on a face that prints upright."""
    if bottom is not None:
        c = 0.6 * d if c is None else min(c, d)
        c = max(0.0, min(c, (u1 - u0) / 2 - 0.25))
        bt = min(bottom, d, (v1 - v0) - c - 0.4)
        iu0 = u0 + (0.0 if "u0" in square else c)
        iu1 = u1 - (0.0 if "u1" in square else c)
        pts = [(u, v, w0) for u in (u0, u1) for v in (v0, v1)] + \
              [(u, v, w0 + d) for u in (iu0, iu1) for v in (v0 + bt, v1 - c)]
        return M.hull_points(pts)
    c = 0.6 * d if c is None else min(c, d)
    c = max(0.0, min(c, (u1 - u0) / 2 - 0.25, (v1 - v0) / 2 - 0.25))
    base = d - c
    iu0 = u0 + (0.0 if "u0" in square else c)
    iu1 = u1 - (0.0 if "u1" in square else c)
    iv0 = v0 + (0.0 if "v0" in square else c)
    iv1 = v1 - (0.0 if "v1" in square else c)
    pts = [(u, v, w0 + base) for u in (u0, u1) for v in (v0, v1)] + \
          [(u, v, w0 + d) for u in (iu0, iu1) for v in (iv0, iv1)]
    top = M.hull_points(pts)
    if base > 1e-6:
        top = top + ext(rect(u0, v0, u1, v1), w0, w0 + base + 0.01)
    return top


def lozenge(u, v, w_, h_, w0, d):
    """Diamond boss (45-degree sides print cleanly on an upright face)."""
    return ext(poly([(u, v - h_ / 2), (u + w_ / 2, v), (u, v + h_ / 2), (u - w_ / 2, v)]), w0, w0 + d)


def dentils(u0, u1, v0, h, w0, d, tooth=0.6, gap=SLOT):
    """Row of dentil blocks between u0..u1 (centred), bottom at v0, height h, depth d."""
    n = max(1, int((u1 - u0 + gap) / (tooth + gap)))
    span = n * tooth + (n - 1) * gap
    s = u0 + (u1 - u0 - span) / 2
    cs = cs_union([rect(s + i * (tooth + gap), v0, s + i * (tooth + gap) + tooth, v0 + h) for i in range(n)])
    return ext(cs, w0, w0 + d)


def console(h, d, t, u=0.0, v_top=0.0, w0=0.0, scroll=True, seg=16):
    """Italianate scroll console (bracket) of height h projecting d from the wall.

    Side profile: a flat top pad, an ogee front sweeping down and in, ending in
    a small curled drop. Extruded t wide, centred on u; top at v_top."""
    pts = []
    n = 14
    # front curve from (d, 0) at the top down to (0.28 d, -h) (ogee)
    for i in range(n + 1):
        s = i / n
        wv = d * (1 - 0.72 * (3 * s * s - 2 * s * s * s))
        pts.append((wv, -h * s))
    pts += [(0.0, -h), (0.0, 0.0)]
    prof = poly(pts)
    if scroll:
        r = min(d * 0.2, h * 0.12)
        prof = cs_union([prof, circle((d - r * 0.9, -r * 1.4), r, seg),
                         circle((d * 0.28 + r * 0.6, -h + r * 1.1), r * 0.9, seg)])
    prof = cs_union([prof, rect(0, -0.25, d + 0.15, 0.0)])     # top pad
    return side_profile(prof, -t / 2, t / 2).translate([u, v_top, w0])


def keystone(u, v0, h, wb, wt, w0, d, bevel=0.15):
    cs = poly([(u - wb / 2, v0), (u + wb / 2, v0), (u + wt / 2, v0 + h), (u - wt / 2, v0 + h)])
    return stepped(cs, [(0, w0, w0 + d - bevel), (bevel, w0 + d - bevel, w0 + d)])


def fan_crest(u, v0, r, w0, d, rays=3, seg=24):
    """Half-round sunburst crest (my 'shell' cap) sitting on v0."""
    half = poly([(u - r, v0)] + [(u + r * math.cos(math.pi - k * math.pi / seg), v0 + r * math.sin(k * math.pi / seg))
                                 for k in range(seg + 1)] + [(u + r, v0)])
    body = ext(half, w0, w0 + d * 0.55)
    ridges = []
    for k in range(rays):
        a = math.pi * (k + 0.5) / rays
        ca, sa = math.cos(a), math.sin(a)
        ridges.append(poly([(u + 0.25 * sa, v0), (u - 0.25 * sa, v0),
                            (u + (r - 0.1) * ca - 0.3 * sa, v0 + (r - 0.1) * sa + 0.3 * ca),
                            (u + (r - 0.1) * ca + 0.3 * sa, v0 + (r - 0.1) * sa - 0.3 * ca)]))
    body = body + ext(cs_union(ridges) ^ half, w0 + d * 0.55, w0 + d)
    bead = ext(circle((u, v0 + 0.05), r * 0.3, 16) ^ half, w0, w0 + d * 1.05)
    return body + bead


def rosette_block(u, v, s, w0, d):
    sq = rect(u - s / 2, v - s / 2, u + s / 2, v + s / 2)
    return ext(sq, w0, w0 + d * 0.7) + ext(circle((u, v), s * 0.3, 12), w0 + d * 0.7, w0 + d)


def finial(r, h, seg=24):
    """Turned finial (revolved): plinth, urn, collared neck, ball and a short rounded spike.
    Base at z=0, top at z=h. Nothing below 0.8 mm across except the last rounding, so it
    prints as turned work rather than a squiggle; print it as its own part next to taller
    parts (never as the lone top of a plate, where tiny layers get no time to cool)."""
    k = r / 1.2
    prof = [(0, 0), (1.2, 0), (1.2, 0.6), (0.75, 1.0), (1.05, 1.6), (1.1, 2.2), (0.8, 2.8), (0.45, 3.2),
            (0.45, 3.6), (0.75, 3.8), (0.75, 4.1), (0.42, 4.4), (0.6, 4.9), (0.62, 5.2), (0.42, 5.6),
            (0.4, 6.2), (0.5, 6.5), (0.35, 6.85), (0, 7.0)]
    prof = [(max(x * k, 0.0) if x > 0 else 0.0, z * h / 7.0) for x, z in prof]
    prof = [(max(x, 0.4) if 0 < x < 0.4 and z < h * 0.97 else x, z) for x, z in prof]
    return M.revolve(poly(prof), seg)


def spandrel(u0, u1, v_top, drop, w0, d, bar=0.55, seg=20):
    """Porch arcade spandrel: a quarter-sweep brace filling the corner between a
    post (at u0 side) and the beam, as a pierced flat plate (drawn in u, v)."""
    L = u1 - u0
    # outer triangle-ish silhouette with concave sweep
    pts = [(u0, v_top), (u1, v_top)]
    for k in range(seg + 1):
        a = k / seg * math.pi / 2
        pts.append((u0 + L * (1 - math.sin(a)), v_top - drop * (1 - math.cos(a))))
    pts.append((u0, v_top - drop))
    sil = poly(pts)
    inner = sil.offset(-bar, JoinType.Round)
    plate = ext(sil - inner, w0, w0 + d)
    # small inner ring ornament
    ring_c = (u0 + L * 0.3, v_top - drop * 0.3)
    r = min(L, drop) * 0.16
    orn = ext(circle(ring_c, r, 16) - circle(ring_c, r - max(RIB, bar * 0.7), 16), w0, w0 + d) if r > RIB + 0.3 else M()
    return plate + orn


def chimney_pot(r, h, seg=24):
    # solid body with a 0.8 mm bore at the top only: each layer is a disc, not a hairline ring
    ri = min(r * 0.62, r - RIB)
    prof = [(0, 0), (r * 1.1, 0), (r * 1.1, h * 0.12), (r * 0.9, h * 0.18), (r * 0.8, h * 0.7), (r, h * 0.85),
            (r, h), (ri, h), (ri, h - 0.8), (0, h - 0.8)]
    return M.revolve(poly(prof), seg)


# ------------------------------------------------------------------ flowing ornament (2D, for face-up relief)
# Queen Anne / Eastlake sawn and carved work drawn as outlines in the (u, v) plane and
# built up in flat terraces (w), so it prints face-up with crisp curves and no overhangs.
# Every band is at least RIB wide and every gap at least SLOT.

def bezier(p0, p1, p2, p3, n=24):
    """Points on a cubic Bezier curve."""
    P = [np.asarray(p, float) for p in (p0, p1, p2, p3)]
    t = np.linspace(0.0, 1.0, n + 1)[:, None]
    return (1 - t) ** 3 * P[0] + 3 * (1 - t) ** 2 * t * P[1] + 3 * (1 - t) * t ** 2 * P[2] + t ** 3 * P[3]


def stroke(pts, width, caps=True):
    """A band of constant width along a polyline, with round joins (and round ends)."""
    pts = np.asarray(pts, float)
    h = width / 2
    parts = []
    for a, b in zip(pts[:-1], pts[1:]):
        d = b - a
        L = float(np.hypot(*d))
        if L < 1e-9:
            continue
        n = np.array([-d[1], d[0]]) / L * h
        parts.append(poly([tuple(a + n), tuple(b + n), tuple(b - n), tuple(a - n)]))
    joins = pts if caps else pts[1:-1]
    parts += [circle(tuple(p), h, 12) for p in joins]
    return cs_union(parts)


def volute(c, r_out, turns=1.0, band=RIB, gap=SLOT, a0=0.0, sense=1, seg=40):
    """Spiral scroll: a band winding inward from radius r_out (its outer edge) with ``gap``
    between turns, ending in a round eye. a0 = angle where the band starts (radians);
    sense = +1 winds counter-clockwise inward, -1 clockwise."""
    pitch = band + gap
    pts = []
    n = max(8, int(seg * turns))
    r_end = r_out - band / 2 - pitch * turns
    for k in range(n + 1):
        t = turns * k / n
        r = r_out - band / 2 - pitch * t
        if r < band / 2:
            break
        a = a0 + sense * 2 * math.pi * t
        pts.append((c[0] + r * math.cos(a), c[1] + r * math.sin(a)))
    eye = circle(c, max(band * 0.7, r_end + band / 2 if r_end > 0 else band * 0.7), 16)
    return cs_union([stroke(pts, band), eye]) if len(pts) > 1 else eye


def sunburst(c, r_hub, r0, r1, n=5, a0=0.0, a1=math.pi, ray0=RIB, ray1=None):
    """Sunburst fan: (hub, rays). The hub is a disc sector of radius r_hub; n rays run from
    r0 to r1, ray0 wide at r0 widening to ray1 at r1 (default: in proportion)."""
    ray1 = ray0 * r1 / r0 if ray1 is None else ray1
    hub = [c]
    for k in range(25):
        a = a0 + (a1 - a0) * k / 24
        hub.append((c[0] + r_hub * math.cos(a), c[1] + r_hub * math.sin(a)))
    rays = []
    for k in range(n):
        a = a0 + (a1 - a0) * (k + 0.5) / n
        ca, sa = math.cos(a), math.sin(a)
        nx, ny = -sa, ca
        p0 = (c[0] + r0 * ca, c[1] + r0 * sa)
        p1 = (c[0] + r1 * ca, c[1] + r1 * sa)
        rays.append(poly([(p0[0] + nx * ray0 / 2, p0[1] + ny * ray0 / 2), (p1[0] + nx * ray1 / 2, p1[1] + ny * ray1 / 2),
                          (p1[0] - nx * ray1 / 2, p1[1] - ny * ray1 / 2), (p0[0] - nx * ray0 / 2, p0[1] - ny * ray0 / 2)]))
    return poly(hub), cs_union(rays)


def oval(c, rx, ry, seg=32):
    return poly([(c[0] + rx * math.cos(2 * math.pi * k / seg), c[1] + ry * math.sin(2 * math.pi * k / seg))
                 for k in range(seg)])


def quatrefoil(c, r, seg=16):
    """Four-lobed boss: four discs of radius r round a centre (a Gothic/Eastlake motif)."""
    d = r * 0.85
    return cs_union([circle((c[0] + dx * d, c[1] + dy * d), r, seg) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
                    + [circle(c, r, seg)])


def bullseye(u, v, s, w0, d):
    """Victorian corner block: a square block with a turned bullseye (two stepped discs)."""
    b = round(d * 0.5 / 0.2) * 0.2                  # every level on the 0.2 mm layer grid
    m = b + round((d - b) * 0.5 / 0.2) * 0.2
    blk = chamfer_box(u - s / 2, v - s / 2, u + s / 2, v + s / 2, w0, b, c=0.2)
    return (blk + ext(circle((u, v), s * 0.36, 20), w0 + b - 0.01, w0 + m)
            + ext(circle((u, v), max(0.3, s * 0.17), 16), w0 + m - 0.01, w0 + d))


def swag(u0, u1, v_top, sag, width=0.6, seg=16):
    """Hanging garland: a band drooping ``sag`` between two points at v_top."""
    pts = [(u0 + (u1 - u0) * k / seg, v_top - sag * (1 - (2 * k / seg - 1) ** 2)) for k in range(seg + 1)]
    return stroke(pts, width)


def urn_cs(u, v0, h, wmax):
    """Urn finial in silhouette: plinth, bowl, neck, lid and ball (all at least RIB across)."""
    s = h / 4.0
    parts = [rect(u - wmax * 0.42, v0, u + wmax * 0.42, v0 + 0.5 * s),                   # plinth
             rect(u - max(RIB, wmax * 0.2) / 2, v0 + 0.45 * s, u + max(RIB, wmax * 0.2) / 2, v0 + 0.9 * s),
             oval((u, v0 + 1.55 * s), wmax / 2, 0.75 * s),                                  # bowl
             rect(u - wmax * 0.46, v0 + 2.05 * s, u + wmax * 0.46, v0 + 2.35 * s),         # lip
             rect(u - max(RIB, wmax * 0.22) / 2, v0 + 2.3 * s, u + max(RIB, wmax * 0.22) / 2, v0 + 3.05 * s),
             circle((u, v0 + 3.35 * s), max(RIB * 0.6, 0.45 * s), 16)]                      # ball
    return cs_union(parts)


def scroll_bracket(u, v_top, h, d, band=0.6, sense=1):
    """Sawn scroll bracket hanging under a sill or shelf (outline in u, v): a band that
    leaves the underside, sweeps down and curls into a ball. sense = +1 curls toward +u."""
    p0 = (u, v_top)
    p3 = (u + sense * d * 0.55, v_top - h + d * 0.45)
    pts = bezier(p0, (u, v_top - h * 0.55), (u + sense * d * 0.1, v_top - h), p3, 16)
    return cs_union([stroke(pts, band), circle(p3, max(0.45, d * 0.3), 16),
                     rect(u - band / 2 - 0.25, v_top - 0.5, u + band / 2 + 0.25, v_top)])

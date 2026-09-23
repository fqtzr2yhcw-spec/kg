"""Small architectural ornaments, built in a local (u, v, w) frame:
u along the facade, v up, w out of the wall (w = 0 is the mounting face).

Everything here is designed to print face-up (w -> print z) without supports."""
import math

import numpy as np
from manifold3d import CrossSection as CS, JoinType, Manifold as M

from .core import circle, cs_union, poly, rect, union


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
        out.append(ext(c, w0, w1))
    return union(out)


def side_profile(profile_wv, u0, u1):
    """Extrude a (w, v) side profile (points or CrossSection) across u0..u1."""
    cs = profile_wv if isinstance(profile_wv, CS) else poly(profile_wv)
    m = M.extrude(cs, u1 - u0)          # profile in (x=w, y=v), extruded along z -> u
    return m.transform(np.array([[0, 0, 1.0, u0], [0, 1.0, 0, 0], [1.0, 0, 0, 0]]))


def dentils(u0, u1, v0, h, w0, d, tooth=0.45, gap=0.4):
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


def fan_crest(u, v0, r, w0, d, rays=5, seg=24):
    """Half-round sunburst crest (my 'shell' cap) sitting on v0."""
    half = poly([(u - r, v0)] + [(u + r * math.cos(math.pi - k * math.pi / seg), v0 + r * math.sin(k * math.pi / seg))
                                 for k in range(seg + 1)] + [(u + r, v0)])
    body = ext(half, w0, w0 + d * 0.55)
    ridges = []
    for k in range(rays):
        a = math.pi * (k + 0.5) / rays
        ca, sa = math.cos(a), math.sin(a)
        ridges.append(poly([(u + 0.12 * sa, v0), (u - 0.12 * sa, v0),
                            (u + (r - 0.1) * ca - 0.22 * sa, v0 + (r - 0.1) * sa + 0.22 * ca),
                            (u + (r - 0.1) * ca + 0.22 * sa, v0 + (r - 0.1) * sa - 0.22 * ca)]))
    body = body + ext(cs_union(ridges) ^ half, w0 + d * 0.55, w0 + d)
    bead = ext(circle((u, v0 + 0.05), r * 0.3, 16) ^ half, w0, w0 + d * 1.05)
    return body + bead


def rosette_block(u, v, s, w0, d):
    sq = rect(u - s / 2, v - s / 2, u + s / 2, v + s / 2)
    return ext(sq, w0, w0 + d * 0.7) + ext(circle((u, v), s * 0.3, 12), w0 + d * 0.7, w0 + d)


def finial(r, h, seg=20):
    """Turned finial (revolved), base at z=0, tip at z=h."""
    prof = [(0, 0), (r, 0), (r, h * 0.12), (r * 0.55, h * 0.18), (r * 0.9, h * 0.35), (r * 0.95, h * 0.45),
            (r * 0.4, h * 0.62), (r * 0.55, h * 0.72), (r * 0.18, h * 0.85), (0.05, h), (0, h)]
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
    orn = ext(circle(ring_c, r, 16) - circle(ring_c, r - bar * 0.7, 16), w0, w0 + d)
    return plate + orn


def chimney_pot(r, h, seg=24):
    prof = [(0, 0), (r * 1.1, 0), (r * 1.1, h * 0.12), (r * 0.9, h * 0.18), (r * 0.8, h * 0.7), (r, h * 0.85),
            (r, h), (r * 0.62, h), (r * 0.62, h * 0.2), (0, h * 0.2)]
    return M.revolve(poly(prof), seg)

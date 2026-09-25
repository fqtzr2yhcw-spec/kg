"""Add-on parts for a house's yard and porch: a picket fence with a gate, a rocking chair, a
window flower box and a bicycle. Each prints on its own with no supports."""
import math

import numpy as np
from manifold3d import Manifold as M

from .core import box, circle, cs_union, poly, rect, union
from .ornament import ext, stroke


def picket_fence(L, h=10.0, pitch=1.6, picket=0.9, t=0.8, gate=None, post=1.6, style="point", sign=False):
    """A picket fence ``L`` long printed face-up: pointed pickets on two rails between square
    posts with ball tops; ``gate`` = (u0, width) leaves an opening filled by a gate whose
    pickets rise in an arch to the middle. Local: u along, v up from the ground, w across
    (the pickets 0..t, rails and posts behind them). ``style``: "point" (pointed pickets, ball
    tops on the posts) or "arrow" (arrow-headed pickets, pyramid caps on the posts); ``sign``:
    an arched sign board over the gate on two tall posts."""
    cells = []
    posts = [0.0, L] + ([gate[0], gate[0] + gate[1]] if gate else [])
    n_mid = max(0, int(L / 24.0))
    posts += [L * (k + 1) / (n_mid + 1) for k in range(n_mid)]
    posts = sorted(set(round(p, 3) for p in posts))
    u = pitch / 2
    while u < L:
        if not any(abs(u - p) < post / 2 + picket / 2 + 0.3 for p in posts):
            top = h
            if gate and gate[0] < u < gate[0] + gate[1]:
                x = (u - gate[0]) / gate[1]
                top = h + 1.6 * math.sin(math.pi * x)
            if style == "arrow":
                cells.append(poly([(u - picket / 2, 0.6), (u + picket / 2, 0.6), (u + picket / 2, top - 1.3),
                                   (u + picket / 2 + 0.3, top - 1.3), (u, top), (u - picket / 2 - 0.3, top - 1.3),
                                   (u - picket / 2, top - 1.3)]))
            else:
                cells.append(poly([(u - picket / 2, 0.6), (u + picket / 2, 0.6), (u + picket / 2, top - 0.7), (u, top),
                                   (u - picket / 2, top - 0.7)]))
        u += pitch
    pickets = ext(cs_union(cells), 0.0, t)
    rails = []
    for v in (2.2, h - 2.8):
        segs = []
        for a, b in zip(posts[:-1], posts[1:]):
            segs.append(rect(a, v, b, v + 0.9))
        rails.append(ext(cs_union(segs), -0.8, 0.01))
    pp = []
    for p in posts:
        tall = sign and gate and p in (gate[0], gate[0] + gate[1])
        ph = h + (5.2 if tall else 0.8)
        pp.append(ext(rect(p - post / 2, 0.0, p + post / 2, ph), -0.8, t))
        if style == "arrow":
            pp.append(ext(poly([(p - post / 2 - 0.2, ph - 0.01), (p + post / 2 + 0.2, ph - 0.01), (p, ph + 1.4)]), -0.8, t))
        else:
            pp.append(ext(circle((p, ph + 0.8), 0.9, 20) + rect(p - 0.4, ph - 0.1, p + 0.4, ph + 0.2), -0.8, t))
    if sign and gate:
        a, b = gate[0], gate[0] + gate[1]
        from .core import arch_cs
        board = arch_cs(a, b, h + 2.4, h + 3.8, rise=1.2, seg=24)
        pp.append(ext(board, -0.8, t))
    return union([pickets] + rails + pp)


def rocking_chair(scale=1.0):
    """A porch rocking chair: two flat side frames (a rocker, legs, an arm and a high back)
    joined by the seat and the back. Local: x forward, y up, z across (0..3.4); it prints
    lying on its side (z = 0 on the bed). About 7 mm tall at HO."""
    s = scale
    side = cs_union([stroke([(-2.6 * s, 0.6 * s), (-1.0 * s, 0.1 * s), (1.2 * s, 0.1 * s), (2.6 * s, 0.7 * s)], 0.6 * s),
                     rect(-1.6 * s, 0.1 * s, -1.0 * s, 3.2 * s), rect(1.0 * s, 0.1 * s, 1.6 * s, 3.2 * s),
                     rect(-1.8 * s, 2.8 * s, 1.8 * s, 3.4 * s),
                     poly([(-1.8 * s, 2.8 * s), (-1.2 * s, 2.8 * s), (-2.2 * s, 7.2 * s), (-2.8 * s, 7.2 * s)]),
                     rect(-1.6 * s, 4.6 * s, 1.4 * s, 5.1 * s)])
    wdt = 3.4 * s
    sides = [ext(side, 0.0, 0.6 * s), ext(side, wdt - 0.6 * s, wdt)]
    seat = ext(rect(-1.8 * s, 2.8 * s, 1.8 * s, 3.4 * s), 0.0, wdt)
    back = ext(poly([(-1.8 * s, 3.3 * s), (-1.2 * s, 3.3 * s), (-2.2 * s, 7.0 * s), (-2.8 * s, 7.0 * s)]), 0.0, wdt)
    return union(sides + [seat, back])


def flower_box(L, h=2.2, d=2.0, blooms=True):
    """A window flower box ``L`` long: a box with a moulded rim and a mound of flowers (round
    blooms) rising out of it. Local: u along, v up, w out from the wall (0 at the wall)."""
    parts = [box([0.0, 0.0, 0.0], [L, h, d]), box([-0.2, h - 0.6, 0.0], [L + 0.2, h, d + 0.2])]
    if blooms:
        rng = np.random.default_rng(int(L * 10))
        for u in np.arange(0.8, L - 0.5, 1.1):
            r = rng.uniform(0.5, 0.7)
            parts.append(M.sphere(r, 12).translate([u, h + r * 0.5, d * 0.5 + rng.uniform(-0.3, 0.3)]))
    return union(parts)


def bicycle(scale=1.0, basket=True):
    """A lady's bicycle as a flat face-up piece: two wheels (rims and hubs with a cross of
    spokes), a stepped-through frame, a saddle, handlebars and a basket on the front.
    Local: x along, y up, z across (0..t). About 20 mm long at HO."""
    s = scale
    r = 4.2 * s
    cs = []
    for cx in (-6.0 * s, 6.0 * s):
        cs.append(circle((cx, r), r, 48) - circle((cx, r), r - 0.6, 48))
        cs.append(circle((cx, r), 0.6, 16))
        for a in (0.0, math.pi / 3, 2 * math.pi / 3):
            cs.append(stroke([(cx + (r - 0.3) * math.cos(a), r + (r - 0.3) * math.sin(a)),
                              (cx - (r - 0.3) * math.cos(a), r - (r - 0.3) * math.sin(a))], 0.5))
    cs.append(stroke([(-6.0 * s, r), (-1.0 * s, r), (4.0 * s, 8.6 * s)], 0.6))        # chain stay, down tube
    cs.append(stroke([(-1.0 * s, r), (-2.6 * s, 9.0 * s)], 0.6))                     # seat tube
    cs.append(stroke([(-6.0 * s, r), (-2.4 * s, 8.4 * s)], 0.55))                     # seat stay
    cs.append(stroke([(6.0 * s, r), (4.0 * s, 8.6 * s), (3.6 * s, 10.0 * s), (2.4 * s, 10.4 * s)], 0.6))   # fork, stem, bar
    cs.append(poly([(-4.0 * s, 9.0 * s), (-1.4 * s, 9.2 * s), (-1.8 * s, 9.9 * s), (-3.6 * s, 9.8 * s)]))  # saddle
    if basket:
        b = poly([(5.0 * s, 8.8 * s), (9.0 * s, 8.8 * s), (8.6 * s, 11.6 * s), (5.4 * s, 11.6 * s)])
        weave = cs_union([rect(5.0 * s, v, 9.0 * s, v + 0.3) for v in np.arange(9.4 * s, 11.3 * s, 0.9)])
        cs.append((b - b.offset(-0.55)) + (weave ^ b))
        cs.append(stroke([(3.6 * s, 10.0 * s), (5.4 * s, 10.0 * s)], 0.55))                  # basket bracket
    return ext(cs_union(cs), 0.0, 0.8)

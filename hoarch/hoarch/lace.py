"""Gingerbread lace: pierced scroll-and-flower patterns for flat boards (the cottage houses).

Every piece is a flat (u, v) outline extruded to a thickness, so it prints face-up (or on
edge, as a porch arcade does) with no overhangs. The piercings are flower-shaped holes (four
teardrop petals round an eye) with round eyelets between them; after piercing, every bar of
wood thinner than a nozzle and a half is closed up again, and every hole narrower than that
is filled, so what is left prints clean at 0.4 mm.

- ``pierce``: lace holes in any board outline, kept clear of a margin and of keep-outs;
- ``lace_bargeboard``: a deep gable bargeboard pierced with lace, its lower edge cusped, a
  big curl at each foot, a pendant under the apex and a fleur finial over it;
- ``gable_screen``: the band across a gable's foot with lace corners rising up the rakes;
- ``medallion``: a round rosette panel for a gable's apex;
- ``fan_hood``: a round-arched hood with a sunburst fan and scroll ears over a window;
- ``lace_spandrel_cs``: a porch bay's spandrel (an elliptical arch in pierced lace);
- ``lace_panel_cs``: a railing panel of lace between two rails.
"""
import math

import numpy as np
from manifold3d import CrossSection as CS, JoinType, Manifold as M

from .core import circle, cs_union, poly, rect, union
from .gables import TRIM_D
from .ornament import ext, stroke

WEB = 0.55          # thinnest bar of wood left between two piercings


def flower(c, R, seg=16):
    """A flower-shaped piercing of radius R about c: four teardrop petals on the diagonals
    round a small eye."""
    cx, cy = c
    out = [circle(c, R * 0.22, seg)]
    for a in (0.25, 0.75, 1.25, 1.75):
        d = (math.cos(math.pi * a), math.sin(math.pi * a))
        tip = circle((cx + d[0] * R * 0.2, cy + d[1] * R * 0.2), 0.12, 8)
        bulb = circle((cx + d[0] * R * 0.66, cy + d[1] * R * 0.66), R * 0.3, seg)
        out.append((tip + bulb).hull())
    return cs_union(out)


def _clean(board, web=WEB):
    """Close up bars thinner than ``web`` and fill slots narrower than ``web``; drop crumbs."""
    # mitred rather than round joins: a round join adds arcs whose level facets would fall
    # between layers on the parts that print on edge (arcades, railings)
    b = board.offset(-web / 2, JoinType.Miter, 2.0).offset(web / 2, JoinType.Miter, 2.0)
    out = b.offset(web / 2, JoinType.Miter, 2.0).offset(-web / 2, JoinType.Miter, 2.0)
    return cs_union([p for p in out.decompose() if p.area() > 1.0])


def pierce(board, pitch=3.0, keep=None, margin=0.7, rows=None, eyelets=True, origin=(0.0, 0.0)):
    """Pierce ``board`` with lace: flowers on a square grid of ``pitch`` (rows staggered by
    half a pitch), each where it fits wholly inside the board less ``margin`` and clear of
    ``keep``, and a round eyelet between neighbouring flowers where one fits."""
    room = board.offset(-margin, JoinType.Round)
    if keep is not None:
        room = room - keep.offset(margin, JoinType.Round)
    if room.is_empty():
        return board
    b = room.bounds()
    R = pitch / 2 - WEB / 2
    holes, centres = [], []
    j0 = math.floor((b[1] - origin[1]) / pitch) - 1
    j1 = math.ceil((b[3] - origin[1]) / pitch) + 1
    for j in range(j0, j1):
        if rows is not None and j not in rows:
            continue
        y = origin[1] + j * pitch
        off = (j % 2) * pitch / 2
        i0 = math.floor((b[0] - origin[0] - off) / pitch) - 1
        i1 = math.ceil((b[2] - origin[0] - off) / pitch) + 1
        for i in range(i0, i1):
            x = origin[0] + off + i * pitch
            disc = circle((x, y), R, 20)
            if (disc - room).area() < 1e-3:
                holes.append(flower((x, y), R))
                centres.append((x, y))
    if eyelets:
        for (x0, y0) in centres:
            for (x1, y1) in centres:
                if x1 <= x0 or abs(y1 - y0) > 1e-6 or abs(x1 - x0 - pitch) > 1e-6:
                    continue
                e = circle(((x0 + x1) / 2, y0), 0.34, 12)
                if (e - room).area() < 1e-3:
                    holes.append(e)
    if not holes:
        return board
    return _clean(board - cs_union(holes))


def scroll(c, r, sense=1, a0=0.0, turns=1.2):
    """A spiral scroll of outer radius r about c (a band a nozzle and a half wide winding in
    to an eye); sense +1 winds counter-clockwise inward."""
    from .ornament import volute
    return volute(c, r, turns=turns, band=0.65, gap=0.75, a0=a0, sense=sense)


def _fit(region, near, rmin=0.9, rmax=3.2):
    """Biggest circle inside ``region`` centred as near ``near`` as possible: (c, r) or None."""
    r = rmax
    while r >= rmin - 1e-9:
        core = region.offset(-r, JoinType.Round)
        if not core.is_empty():
            pts = [p for pl in core.to_polygons() for p in pl]
            c = min(pts, key=lambda p: (p[0] - near[0]) ** 2 + (p[1] - near[1]) ** 2)
            return (float(c[0]), float(c[1])), r
        r -= 0.1
    return None


def lace_bargeboard(L, slope, d_eave, skin=1.8, width=3.2, d=TRIM_D, finial=5.6, drop=0.0, curl=2.2, medal=3.0, margin=0.4):
    """A deep lace bargeboard for a gable of wall length L, in the wall's facade frame (v up
    from the eave, u from the wall's left end), hung on the rake's outer end as
    gables.bargeboard is: its top edge follows the roof's top surface from eave to apex. The
    band is pierced with a row of flowers and eyelets, its lower edge cut in small cusps, a
    spiral scroll curls at each foot, a pendant hangs under the apex and a fleur finial (a
    spike with three leaves) stands over it. ``medal``: a round medallion of that radius hung
    under the apex (a rim, eight petals and a boss standing 0.4 proud) in place of a king
    post. Place at w = rake; flat, prints face-up. ``margin``: the solid wood left above and
    below the pierced flowers (the Marigold's printed boards broke at 0.4)."""
    s = slope
    c = math.hypot(1.0, s)
    a_l = np.array([-d_eave, 0.0])
    tip = np.array([L / 2, s * (L / 2 + d_eave)])
    a_r = np.array([L + d_eave, 0.0])
    depth = skin + width
    band = []
    for a in (a_l, a_r):
        n = np.array([s, -1.0]) / c if a[0] < L / 2 else np.array([-s, -1.0]) / c
        band.append(poly([tuple(a), tuple(tip), tuple(tip + n * depth), tuple(a + n * depth)]))
    board = cs_union(band) ^ rect(-d_eave - 5, -0.01, L + d_eave + 5, tip[1] + 5)
    run = float(np.linalg.norm(tip - a_l))
    cusps, holes = [], []
    pitch = 3.8
    R = min(width / 2 - margin, pitch / 2 - max(WEB, margin) / 2 - 0.2)
    for a in (a_l, a_r):
        n = np.array([s, -1.0]) / c if a[0] < L / 2 else np.array([-s, -1.0]) / c
        dirv = (tip - a) / np.linalg.norm(tip - a)
        k = 1
        while 1.7 * k < run - 2.0:
            cusps.append(circle(tuple(a + dirv * (1.7 * k) + n * (depth + 0.3)), 0.7, 16))
            k += 1
        t = 3.6
        while t < run - 4.0:
            p = a + dirv * t + n * (skin + width * 0.5)
            holes.append(flower(tuple(p), R))
            q = a + dirv * (t + pitch / 2) + n * (skin + width * 0.5)
            if t + pitch < run - 4.0:
                holes.append(circle(tuple(q), 0.4, 12))
            t += pitch
    board = board - cs_union(cusps) - cs_union(holes)
    mc = (L / 2, tip[1] - depth * c - (medal * 0.55 if medal else 0.0))
    if medal:
        board = board + circle(mc, medal, 48)
    else:
        board = board + rect(L / 2 - 1.2, tip[1] - depth * c - 0.8, L / 2 + 1.2, tip[1])  # king post
    for a, sg in ((a_l, 1), (a_r, -1)):
        n = np.array([s, -1.0]) / c if a[0] < L / 2 else np.array([-s, -1.0]) / c
        foot = a + n * depth
        cc = (float(foot[0]) + sg * 0.2, -curl + 0.35)
        board = board + scroll(cc, curl, sense=sg, a0=math.pi / 2) + \
            rect(min(a[0], foot[0]) - 0.1, -0.6, max(a[0], foot[0]) + 0.1, 0.2)
    board = _clean(board)
    parts = [ext(board, 0.0, d)]
    if medal:
        petals = cs_union([(circle(mc, 0.3, 8) + circle((mc[0] + (medal - 1.1) * math.cos(a), mc[1] + (medal - 1.1) * math.sin(a)),
                                                       0.55, 16)).hull() for a in np.linspace(0, 2 * math.pi, 8, endpoint=False)])
        rim = circle(mc, medal, 48) - circle(mc, medal - 0.6, 48)
        parts.append(ext(rim + petals + circle(mc, 0.7, 16), d - 0.01, d + 0.4))
    ay = tip[1] - depth * c - 0.6
    if drop:
        dcs = cs_union([rect(L / 2 - 0.45, ay - drop, L / 2 + 0.45, ay + 0.3), circle((L / 2, ay - drop + 0.9), 0.8, 20),
                        poly([(L / 2 - 0.55, ay - drop + 0.3), (L / 2 + 0.55, ay - drop + 0.3), (L / 2, ay - drop - 1.1)])])
        parts.append(ext(dcs, 0.0, d + 0.2))
    if finial:
        f0 = tip[1] - 0.6
        leaves = cs_union([circle((L / 2 - 0.75, f0 + finial * 0.5), 0.55, 16), circle((L / 2 + 0.75, f0 + finial * 0.5), 0.55, 16),
                           circle((L / 2, f0 + finial * 0.5 + 0.7), 0.6, 16)])
        fcs = cs_union([rect(L / 2 - 0.45, f0, L / 2 + 0.45, f0 + finial - 1.0), leaves,
                        poly([(L / 2 - 0.45, f0 + finial - 1.0), (L / 2 + 0.45, f0 + finial - 1.0), (L / 2, f0 + finial + 0.4)])])
        parts.append(ext(fcs, 0.0, d + 0.2))
    return union(parts)


def gable_screen(L, slope, v0=0.0, band=1.8, corner=5.2, d=TRIM_D):
    """The band across a gable's foot (u 0..L, v0..v0 + band, on the wall face), pierced with
    eyelets, and a lace corner rising up each rake: a triangle ``corner`` long, its long
    side cut in cusps, pierced with a flower and eyelets. Face-up, sits in a landing on the
    gable wall."""
    s = slope
    parts = [rect(0.0, v0, L, v0 + band)]
    for sg, x0 in ((1, 0.0), (-1, L)):
        top = v0 + band + corner * s * 0.9
        p0, p1 = np.array([x0 + sg * corner, v0 + band]), np.array([x0, top])
        tri = poly([(x0, v0 + band - 0.01), tuple(p0), tuple(p1)])
        dv = (p1 - p0) / np.linalg.norm(p1 - p0)
        nv = np.array([dv[1], -dv[0]]) * sg * -1
        n = int(np.linalg.norm(p1 - p0) / 1.6)
        cusps = cs_union([circle(tuple(p0 + dv * (np.linalg.norm(p1 - p0) * (k + 0.5) / n) + nv * 0.35), 0.7, 16)
                          for k in range(n)])
        tri = tri - cusps
        parts.append(pierce(tri, pitch=2.3, margin=0.5, eyelets=False, origin=(x0, v0 + band)))
    board = cs_union(parts)
    band_holes = cs_union([circle((u, v0 + band / 2), 0.38, 12) for u in np.arange(1.6, L - 1.0, 1.6)])
    return ext(_clean(board - band_holes), 0.0, d)


def medallion(r=3.0, d=0.8):
    """A round medallion: a rim, a pierced ring of eight petals and a boss, the petals and
    boss standing 0.4 proud. Centred at the origin; prints face-up."""
    disc = circle((0.0, 0.0), r, 48)
    petals = cs_union([(circle((0.0, 0.0), 0.3, 8) + circle(((r - 1.1) * math.cos(a), (r - 1.1) * math.sin(a)), 0.55, 16)).hull()
                       for a in np.linspace(0, 2 * math.pi, 8, endpoint=False)])
    rim = disc - circle((0.0, 0.0), r - 0.6, 48)
    return ext(disc, 0.0, d) + ext(rim + petals + circle((0.0, 0.0), 0.7, 16), d - 0.01, d + 0.4)


def fan_hood(w, spring, band=1.2, ear=2.2, d=TRIM_D, rays=9, fan=2.6):
    """A hood for a round-headed window ``w`` wide springing at ``spring``: a half-disc fan
    ``fan`` deep round the casing with a sunburst of raised rays, a raised round band along
    its inner edge, and a spiral ear at each springing. Local u centred, v from 0 (the
    window's foot); face-up, the rays and band 0.4 proud."""
    r = w / 2 + 0.9
    R = r + band
    fanR = R + fan
    top = rect(-fanR - 5, spring, fanR + 5, spring + fanR + 1)
    base = (circle((0.0, spring), fanR, 64) - circle((0.0, spring), r, 64)) ^ top
    arch = (circle((0.0, spring), R, 64) - circle((0.0, spring), r, 64)) ^ top
    rim = (circle((0.0, spring), fanR, 64) - circle((0.0, spring), fanR - 0.6, 64)) ^ top
    raycs = cs_union([stroke([((R - 0.1) * math.cos(a), spring + (R - 0.1) * math.sin(a)),
                              ((fanR - 0.3) * math.cos(a), spring + (fanR - 0.3) * math.sin(a))], 0.55)
                      for a in np.linspace(math.pi / (rays + 1), math.pi - math.pi / (rays + 1), rays)]) ^ base
    ears = []
    for sg in (-1, 1):
        c = (sg * (fanR + ear - 0.6), spring - ear + 0.9)
        ears.append(scroll(c, ear, sense=-sg, a0=math.pi / 2 if sg > 0 else math.pi / 2))
        ears.append(rect(min(sg * (fanR - 0.6), sg * (fanR + ear - 0.4)), spring - 0.3,
                         max(sg * (fanR - 0.6), sg * (fanR + ear - 0.4)), spring + 0.5))
    flat = _clean(cs_union([base] + ears))
    return ext(flat, 0.0, d) + ext(arch + rim + raycs, d - 0.01, d + 0.4)


def lace_spandrel_cs(u0, u1, v_bot, v_top, band=0.8, frieze=1.8):
    """A porch bay in lace: an elliptical arch with a band from post to post, a spiral
    scroll curled into each spandrel, a frieze strip along the beam pierced with eyelets, and
    a pendant at the crown; the rest of the spandrel is open. (u, v)."""
    mid, half = (u0 + u1) / 2, (u1 - u0) / 2
    rise = round(min(half * 0.8, (v_top - v_bot) - frieze - 0.8) / 0.2) * 0.2     # room above the arch for the scrolls

    def ell(a, b, seg=72):
        return poly([(mid + a * math.cos(t), v_bot + b * math.sin(t)) for t in np.linspace(0, math.pi, seg)] +
                    [(mid - a, v_bot - 5), (mid + a, v_bot - 5)])
    region = rect(u0, v_bot, u1, v_top + 0.05)
    fr = rect(u0, v_top - frieze, u1, v_top + 0.05)
    posts = rect(u0, v_bot, u0 + 0.8, v_top) + rect(u1 - 0.8, v_bot, u1, v_top)
    arch = (ell(half, rise) - ell(half - band, rise - band)) ^ region
    parts = [fr, posts, arch]
    free = region - ell(half, rise) - fr - posts
    for sg in (-1, 1):
        side = free ^ (rect(mid, v_bot - 1, u1 + 1, v_top + 1) if sg > 0 else rect(u0 - 1, v_bot - 1, mid, v_top + 1))
        fit = _fit(side, (u1 - 1.5 if sg > 0 else u0 + 1.5, v_top - frieze - 1.5), rmin=0.8, rmax=2.2)
        if fit is None:
            continue
        (cx, cy), r = fit
        parts.append(scroll((cx, cy), r + 0.35, sense=sg, a0=math.pi / 2))
        rest = side - circle((cx, cy), r + 0.35 + WEB, 32)
        fit2 = _fit(rest, (mid + sg * half * 0.35, v_top - frieze - 0.9), rmin=0.45, rmax=0.9)
        if fit2 is not None:
            (x2, y2), r2 = fit2
            parts.append(circle((x2, y2), r2 + 0.3, 16) - circle((x2, y2), max(0.3, r2 - 0.35), 16))
    solid = cs_union(parts) - cs_union([circle((u, v_top - frieze / 2), 0.36, 12) for u in np.arange(u0 + 1.4, u1 - 1.0, 1.5)])
    cvb = v_bot + rise - band
    drop = cs_union([rect(mid - 0.35, cvb - 1.0, mid + 0.35, cvb + 0.1), circle((mid, cvb - 1.4), 0.6, 20),
                     poly([(mid - 0.4, cvb - 1.8), (mid + 0.4, cvb - 1.8), (mid, cvb - 2.6)])])
    return _clean(solid + drop)


def lace_panel_cs(L, vb, vt):
    """A railing panel of lace between the bottom rail (top at vb) and the hand rail (bottom
    at vt), u 0..L: a board pierced all over with staggered rows of flowers."""
    board = rect(0.0, vb, L, vt)
    return pierce(board, pitch=2.3, margin=0.45, eyelets=False, origin=(L / 2, vb + (vt - vb) / 2 - 1.15))

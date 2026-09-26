"""Gabled roofs, gable walls and bargeboards (Gothic, Stick and Folk Victorian houses).

A gabled roof is built from hip_roof pieces whose gable ends are not "exposed" (they stay
vertical), each piece's path already running past its gable walls by the rake. Around every
gable wall the roof body is cut back to the wall's inner face; a thin rake skin runs over the
wall and past it; and the gable wall itself (a pentagon of siding under the rake) is its own
part standing on the eave ring. On steep roofs (slope > 1) the body is hollowed: its underside
then leans at under 45 degrees from vertical and prints upright.
"""
import math

import numpy as np
from manifold3d import JoinType, Manifold as M

from .core import Facade, box, circle, cs_union, poly, rect, slab, union
from .ornament import ext, stroke
from . import roof as R

TRIM_D = 2.2        # every gable ornament and bargeboard: 11 layers, thick enough not to snap (0.8 broke)


def gabled_roof(pieces, z_eave, d_eave, gables, texture="fish", tex_kw=None, skin=1.8, rake=3.2, t=3.0,
                inner_cs=None, hollow=2.4, fascia=1.6, clr=0.15):
    """pieces:  [(path, exposed_edges, slope)] for hip_roof (paths reach ``rake - d_eave`` past
                every gable wall);
    gables:  [dict(p0, p1, slope, e=None)]: the outer wall line under each gable, from p0 to
             p1 with the house on the left (CCW), and that roof's slope. ``e``: how far past
             the wall's ends the roof is cut back to the skin (default: through the eaves of
             an end gable; give about d_eave for a gable standing in a long wall);
    z_eave:  height of the eave's top edge; the eave has a ``fascia`` below it, so the walls
             end (and the roof sits) at z_eave - fascia;
    inner_cs: the walls' inner outline (for hollowing), or None for a solid body.
    Returns dict(body, tex, skins, skin_tex, walls=[dict(facade, cs, shoulder, apex, L, slope)])
    where cs is the gable wall's outline in its facade frame, v up from z_eave (it starts at
    v = -fascia, the wall top), ``clr`` under the skin and clear of the roof body."""
    tk = tex_kw or {}
    zlo = z_eave - fascia
    solid, tex = R.hip_roof(pieces, z_eave, pieces[0][2], d_eave, texture=texture, tex_kw=tk, zlo=zlo)
    low, _ = R.hip_roof(pieces, z_eave - skin, pieces[0][2], d_eave, texture=None, zlo=zlo - 10.0)
    cuts, zones, walls = [], [], []
    for g in gables:
        f = Facade(g["p0"], g["p1"], z_eave)
        L, s = f.L, g["slope"]
        e = g.get("e") or (d_eave + rake + 1.0)
        cuts.append(f.place(box([-e, -60.0, -t - clr], [L + e, 600.0, 60.0])))
        zones.append(f.place(box([-e, -60.0, -t - clr - 0.01], [L + e, 600.0, rake])))
        sh = s * d_eave - skin - clr
        apex = s * (L / 2 + d_eave) - skin - clr
        cs = poly([(0.0, -fascia), (L, -fascia), (L, sh), (L / 2, apex), (0.0, sh)])
        walls.append(dict(facade=f, cs=cs, shoulder=sh, apex=apex, L=L, slope=s))
    cut = union(cuts)
    zone = union(zones)
    skins = ((solid - low) ^ zone)
    skin_tex = tex ^ zone
    body = solid - cut
    body_tex = tex - cut
    if inner_cs is not None and hollow:
        s0 = pieces[0][2]
        dz = hollow * math.sqrt(1 + s0 * s0)
        inner, _ = R.hip_roof(pieces, z_eave - dz, s0, d_eave, texture=None, zlo=zlo - 10.0)
        body = body - (inner ^ slab(inner_cs, zlo - 1.0, z_eave + 400.0))
    return dict(body=body, tex=body_tex, skins=skins, skin_tex=skin_tex, walls=walls, zlo=zlo)


MIN_BAR = 1.0        # no bar, stem or tie of a gable ornament narrower than this (in its plane)


def _tie(cs, w=MIN_BAR):
    """Thicken the bars, stems and ties of an ornament's outline narrower than ``w`` (rather
    than cutting them away), so no accent hangs by a single nozzle line; drop crumbs."""
    from .lace import sturdy
    cs = sturdy(cs, w * 0.95, grow=0.35)
    return cs_union([pc for pc in cs.decompose() if pc.area() > 2.0])


def _text(cs, w0, w1):
    """ext() for the gable ornaments: a piece that starts on the back (w0 = 0) is tied first."""
    return ext(_tie(cs) if w0 <= 0.01 else cs, w0, w1)


def bargeboard(L, slope, d_eave, skin=1.8, width=2.6, d=TRIM_D, finial=5.0, drop=3.0, pierce="trefoil"):
    """Pierced bargeboard for a gable of wall length L, in the wall's facade frame (v up from
    the eave, u from the wall's left end). It hangs on the rake's outer end: its top edge runs
    with the roof's top surface from eave to apex (covering the skin's end), its lower edge is
    scalloped, trefoils are pierced along it, a turned drop hangs under the apex and a spike
    finial stands above it. Place it at w = rake; it is flat and prints face-up."""
    s = slope
    c = math.hypot(1.0, s)
    a_l = np.array([-d_eave, 0.0])
    tip = np.array([L / 2, s * (L / 2 + d_eave)])
    a_r = np.array([L + d_eave, 0.0])
    depth = skin + width                              # the skin's end face plus the hanging band
    band = []
    for a in (a_l, a_r):
        n = np.array([s, -1.0]) / c if a[0] < L / 2 else np.array([-s, -1.0]) / c
        band.append(poly([tuple(a), tuple(tip), tuple(tip + n * depth), tuple(a + n * depth)]))
    board = cs_union(band) ^ rect(-d_eave - 5, -0.01, L + d_eave + 5, tip[1] + 5)
    holes, scal = [], []
    run = float(np.linalg.norm(tip - a_l))
    n_s = max(3, int(run / 3.2))
    for a in (a_l, a_r):
        n = np.array([s, -1.0]) / c if a[0] < L / 2 else np.array([-s, -1.0]) / c
        dirv = (tip - a) / np.linalg.norm(tip - a)
        for k in range(1, n_s):
            p = a + dirv * (run * k / n_s)
            sc = circle(tuple(p + n * (depth + 0.35)), 1.05, 20)
            if (sc ^ board).area() < 0.8 * sc.area():     # near the apex the other half's scallops fall inside the board
                scal.append(sc)
            if pierce == "trefoil" and k % 2 == 1 and k < n_s - 2:
                cc = p + n * (skin + width * 0.5)
                r = 0.42
                holes.append(cs_union([circle((cc[0] + r * math.cos(t_), cc[1] + r * math.sin(t_)), 0.36, 16)
                                       for t_ in (math.pi / 2, math.pi / 2 + 2.094, math.pi / 2 + 4.189)]))
    board = board - cs_union(scal)
    if holes:
        board = board - cs_union(holes)
    # a king post at the apex ties the two halves (and the drop and finial) together
    board = board + rect(L / 2 - 1.1, tip[1] - depth * c - 0.6, L / 2 + 1.1, tip[1])
    board = cs_union([pc for pc in board.decompose() if pc.area() > 2.0])
    parts = [_text(board, 0.0, d)]
    ay = tip[1] - depth * c - 0.4
    if drop:
        dcs = cs_union([rect(L / 2 - 0.45, ay - drop, L / 2 + 0.45, ay + 0.3),
                        circle((L / 2, ay - drop + 0.6), 0.75, 20),
                        poly([(L / 2 - 0.5, ay - drop + 0.2), (L / 2 + 0.5, ay - drop + 0.2), (L / 2, ay - drop - 1.0)])])
        parts.append(_text(dcs, 0.0, d + 0.2))
    if finial:
        fcs = cs_union([rect(L / 2 - 0.5, tip[1] - 0.6, L / 2 + 0.5, tip[1] + finial - 1.2),
                        circle((L / 2, tip[1] + finial * 0.45), 0.8, 20),
                        poly([(L / 2 - 0.5, tip[1] + finial - 1.2), (L / 2 + 0.5, tip[1] + finial - 1.2), (L / 2, tip[1] + finial)])])
        parts.append(_text(fcs, 0.0, d + 0.2))
    return union(parts)


def ridge_cap(p0, p1, z, s, z_grid, half=1.5, up=0.9):
    """A ridge cap (roll) along the ridge p0 -> p1 at height z over slopes s: it covers the
    joint of the two slate faces, standing ``up`` over the ridge and 0.5 over the slates at
    its edges, with a flat top two nozzle widths across on the layer grid counted from
    ``z_grid`` (where the roof starts printing)."""
    p0, p1 = np.array(p0, float), np.array(p1, float)
    d = (p1 - p0) / np.linalg.norm(p1 - p0)
    n = np.array([-d[1], d[0]])
    up = round((z + up - z_grid) / 0.2) * 0.2 + z_grid - z
    pts = []
    for p in (p0, p1):
        for sg in (-1, 1):
            q = p + sg * n * half
            pts += [(q[0], q[1], z - s * half - 0.6), (q[0], q[1], z - s * half + 0.5)]
            q = p + sg * n * 0.4
            pts.append((q[0], q[1], z + up))
    return M.hull_points(pts)


def chimney_seat(roof_solid, x, y, half, z_top):
    """Fill a hollow roof under a ridge chimney with a downward 45-degree pyramid (so it
    prints upright), leaving the chimney a blind pocket."""
    h = half + 2.0
    pts = [(x + sx * h, y + sy * h, z_top) for sx in (-1, 1) for sy in (-1, 1)]
    pts.append((x, y, z_top - h - 1.0))
    return M.hull_points(pts) ^ roof_solid


def hip_cap(a, b, half=1.0, up=0.7, drop=1.6):
    """A cap (roll) along a sloping hip line from 3D point a up to b: it covers the joint of
    the two slate faces meeting there, ``up`` proud of the hip and sunk ``drop`` at its edges."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = b[:2] - a[:2]
    n = np.array([-d[1], d[0]]) / max(np.linalg.norm(d), 1e-9)
    pts = []
    for p in (a, b):
        for sg in (-1, 1):
            pts.append((p[0] + sg * n[0] * half, p[1] + sg * n[1] * half, p[2] - drop))
            pts.append((p[0] + sg * n[0] * 0.35, p[1] + sg * n[1] * 0.35, p[2] + up))
    return M.hull_points(pts)


def gable_truss(L, slope, d_eave, skin=1.8, width=1.6, d=TRIM_D, collar=0.42, finial=5.0, drop=3.4, fan=True):
    """Stick-style gable truss hung on the rake like a bargeboard (same frame and placement):
    plain rafters over the skin's end, a collar tie across the gable at ``collar`` of its
    height, a king post from the apex through the collar ending in a drop, struts from the
    collar up to the rafters, a fan of sticks radiating over the collar, a spike finial."""
    s = slope
    c = math.hypot(1.0, s)
    tip = np.array([L / 2, s * (L / 2 + d_eave)])
    depth = skin + width
    band = []
    for a in (np.array([-d_eave, 0.0]), np.array([L + d_eave, 0.0])):
        n = np.array([s, -1.0]) / c if a[0] < L / 2 else np.array([-s, -1.0]) / c
        band.append(poly([tuple(a), tuple(tip), tuple(tip + n * depth), tuple(a + n * depth)]))
    rafters = cs_union(band) ^ rect(-d_eave - 5, -0.01, L + d_eave + 5, tip[1] + 5)
    H = tip[1]
    vc = H * collar                                      # collar tie height
    u_c = vc / s - d_eave                                # where the collar meets the rafters' tops
    sticks = [rect(u_c - 0.5, vc - 1.2, L - u_c + 0.5, vc)]
    kp_bot = vc - 2.2
    sticks.append(rect(L / 2 - 0.6, kp_bot, L / 2 + 0.6, H - 0.5))
    # struts from the collar (a third of the way in) up to the rafters' undersides
    for sg in (-1, 1):
        ua = L / 2 + sg * (L / 2 - u_c) * 0.45
        vb = vc + (H - vc) * 0.55
        ub = L / 2 + sg * ((H - vb) / s)
        sticks.append(stroke([(ua, vc - 0.3), (ub - sg * 1.5, vb - 0.8)], 0.8))
    if fan:
        for k in range(1, 6):
            a = math.pi * k / 6
            p1 = (L / 2 + 30 * math.cos(a), vc + 30 * math.sin(a))
            sticks.append(stroke([(L / 2, vc - 0.2), p1], 0.55))
    frame_cs = (cs_union(sticks) ^ poly([(-d_eave, 0.0), (L + d_eave, 0.0), tuple(tip)])) + rafters
    frame_cs = cs_union([pc for pc in frame_cs.decompose() if pc.area() > 2.0])
    parts = [_text(frame_cs, 0.0, d)]
    parts.append(_text(rect(u_c - 0.3, vc - 1.5, L - u_c + 0.3, vc - 0.9), 0.0, d + 0.4))      # a bead on the collar
    if drop:
        dcs = cs_union([rect(L / 2 - 0.45, kp_bot - drop, L / 2 + 0.45, kp_bot + 0.3),
                        circle((L / 2, kp_bot - drop + 0.6), 0.75, 20),
                        poly([(L / 2 - 0.5, kp_bot - drop + 0.2), (L / 2 + 0.5, kp_bot - drop + 0.2), (L / 2, kp_bot - drop - 1.0)])])
        parts.append(_text(dcs, 0.0, d + 0.2))
    if finial:
        fcs = cs_union([rect(L / 2 - 0.5, H - 0.6, L / 2 + 0.5, H + finial - 1.2),
                        circle((L / 2, H + finial * 0.45), 0.8, 20),
                        poly([(L / 2 - 0.5, H + finial - 1.2), (L / 2 + 0.5, H + finial - 1.2), (L / 2, H + finial)])])
        parts.append(_text(fcs, 0.0, d + 0.2))
    return union(parts)


def gable_sunburst(L, slope, d_eave, skin=1.8, width=1.4, d=TRIM_D, collar=0.36, finial=4.4):
    """Folk Victorian gable ornament hung on the rake like a bargeboard: narrow rafters with a
    scalloped lower edge, a collar across the gable over a frieze of short spindles, and a
    sunburst (a half-round hub and rays) standing on the collar, with a spike finial."""
    s = slope
    c = math.hypot(1.0, s)
    tip = np.array([L / 2, s * (L / 2 + d_eave)])
    depth = skin + width
    band = []
    for a in (np.array([-d_eave, 0.0]), np.array([L + d_eave, 0.0])):
        n = np.array([s, -1.0]) / c if a[0] < L / 2 else np.array([-s, -1.0]) / c
        band.append(poly([tuple(a), tuple(tip), tuple(tip + n * depth), tuple(a + n * depth)]))
    rafters = cs_union(band) ^ rect(-d_eave - 5, -0.01, L + d_eave + 5, tip[1] + 5)
    H = tip[1]
    vc = H * collar
    u_c = vc / s - d_eave
    tri = poly([(-d_eave, 0.0), (L + d_eave, 0.0), tuple(tip)])
    parts = [rect(u_c - 0.5, vc, L - u_c + 0.5, vc + 1.1)]                       # collar
    parts.append(rect(u_c + 0.5, vc - 3.0, L - u_c - 0.5, vc - 2.3))             # rail under the spindles
    n = max(3, int((L - 2 * u_c) / 1.4))
    for k in range(n):
        u = u_c + 1.0 + (L - 2 * u_c - 2.0) * (k + 0.5) / n
        parts.append(rect(u - 0.28, vc - 2.35, u + 0.28, vc + 0.05))
    r_hub = min(3.0, (H - vc) * 0.22)
    hub = (circle((L / 2, vc + 1.1), r_hub, 32) - circle((L / 2, vc + 1.1), r_hub - 0.7, 32)) ^ rect(-5, vc + 1.0, L + 5, H)
    parts.append(hub)
    for k in range(1, 10):
        a = math.pi * k / 10
        p0 = (L / 2 + (r_hub - 0.3) * math.cos(a), vc + 1.1 + (r_hub - 0.3) * math.sin(a))
        p1 = (L / 2 + 40 * math.cos(a), vc + 1.1 + 40 * math.sin(a))
        parts.append(stroke([p0, p1], 0.55 if k % 2 else 0.7))
    frame_cs = (cs_union(parts) ^ tri) + rafters
    # scallops along the rafters' lower edge
    run = float(np.linalg.norm(tip - np.array([-d_eave, 0.0])))
    scal = []
    for a in (np.array([-d_eave, 0.0]), np.array([L + d_eave, 0.0])):
        nrm = np.array([s, -1.0]) / c if a[0] < L / 2 else np.array([-s, -1.0]) / c
        dirv = (tip - a) / np.linalg.norm(tip - a)
        m = max(3, int(run / 2.4))
        for k in range(1, m):
            p = a + dirv * (run * k / m)
            sc = circle(tuple(p + nrm * (depth + 0.3)), 0.8, 16)
            if (sc ^ cs_union(parts)).area() < 0.01:
                scal.append(sc)
    if scal:
        frame_cs = frame_cs - cs_union(scal)
    frame_cs = cs_union([pc for pc in frame_cs.decompose() if pc.area() > 2.0])
    out = [_text(frame_cs, 0.0, d), _text(hub.offset(-0.15), 0.0, d + 0.4)]
    if finial:
        fcs = cs_union([rect(L / 2 - 0.5, H - 0.6, L / 2 + 0.5, H + finial - 1.2),
                        circle((L / 2, H + finial * 0.45), 0.8, 20),
                        poly([(L / 2 - 0.5, H + finial - 1.2), (L / 2 + 0.5, H + finial - 1.2), (L / 2, H + finial)])])
        out.append(_text(fcs, 0.0, d + 0.2))
    return union(out)


def gable_tudor(L, slope, d_eave, skin=1.8, width=1.4, d=TRIM_D, finial=4.0):
    """Queen Anne / Tudor gable truss hung on the rake: plain rafters, a collar, a king post
    and two curved braces rising from the collar ends to the king post (an arch-braced
    truss), with a turned drop under the king post and a finial."""
    s = slope
    c = math.hypot(1.0, s)
    tip = np.array([L / 2, s * (L / 2 + d_eave)])
    depth = skin + width
    band = []
    for a in (np.array([-d_eave, 0.0]), np.array([L + d_eave, 0.0])):
        n = np.array([s, -1.0]) / c if a[0] < L / 2 else np.array([-s, -1.0]) / c
        band.append(poly([tuple(a), tuple(tip), tuple(tip + n * depth), tuple(a + n * depth)]))
    rafters = cs_union(band) ^ rect(-d_eave - 5, -0.01, L + d_eave + 5, tip[1] + 5)
    H = tip[1]
    vc = H * 0.3
    u_c = vc / s - d_eave
    tri = poly([(-d_eave, 0.0), (L + d_eave, 0.0), tuple(tip)])
    parts = [rect(u_c - 0.5, vc, L - u_c + 0.5, vc + 1.2), rect(L / 2 - 0.6, vc - 2.0, L / 2 + 0.6, H - 0.5)]
    # arch braces: circular arcs from the collar ends up to the king post, springing tangent to the collar
    for sg in (-1, 1):
        ua = L / 2 + sg * (L / 2 - u_c - 0.5)
        vb = vc + (H - vc) * 0.55
        pts = []
        for t in np.linspace(0, 1, 24):
            x = ua + (L / 2 - ua) * math.sin(t * math.pi / 2)
            y = vc + 1.2 + (vb - vc - 1.2) * (1 - math.cos(t * math.pi / 2))
            pts.append((x, y))
        parts.append(stroke(pts, 0.8))
        # a pair of short vertical studs between collar and rafters
        us = L / 2 + sg * (L / 2 - u_c) * 0.7
        parts.append(rect(us - 0.35, vc + 1.0, us + 0.35, s * (min(us, L - us) + d_eave) - 0.2))
    frame_cs = (cs_union(parts) ^ tri) + rafters
    frame_cs = cs_union([pc for pc in frame_cs.decompose() if pc.area() > 2.0])
    out = [_text(frame_cs, 0.0, d)]
    kb = vc - 2.0
    out.append(_text(cs_union([rect(L / 2 - 0.45, kb - 2.4, L / 2 + 0.45, kb + 0.3), circle((L / 2, kb - 2.6), 0.7, 20)]),
                   0.0, d + 0.2))
    if finial:
        out.append(_text(cs_union([rect(L / 2 - 0.5, H - 0.6, L / 2 + 0.5, H + finial - 1.0),
                                 circle((L / 2, H + finial - 1.0), 0.75, 20)]), 0.0, d + 0.2))
    return union(out)


def gable_gingerbread(L, slope, d_eave, skin=1.8, width=1.6, d=TRIM_D, finial=4.0):
    """Folk Victorian gingerbread: a narrow rafter board edged with a row of sawn drops, and
    a spindle screen (a rail with short spindles and balls) hung across the peak from a
    king post that ends in a turned drop."""
    s = slope
    c = math.hypot(1.0, s)
    tip = np.array([L / 2, s * (L / 2 + d_eave)])
    depth = skin + width
    band, drops = [], []
    for a in (np.array([-d_eave, 0.0]), np.array([L + d_eave, 0.0])):
        n = np.array([s, -1.0]) / c if a[0] < L / 2 else np.array([-s, -1.0]) / c
        band.append(poly([tuple(a), tuple(tip), tuple(tip + n * depth), tuple(a + n * depth)]))
        dirv = (tip - a) / np.linalg.norm(tip - a)
        run = float(np.linalg.norm(tip - a))
        m = max(3, int(run / 2.0))
        for k in range(1, m - 1):
            p = a + dirv * (run * k / m) + n * (depth - 0.2)
            drops.append(cs_union([rect(p[0] - 0.3, p[1] - 1.2, p[0] + 0.3, p[1] + 0.3), circle((p[0], p[1] - 1.4), 0.45, 14)]))
    rafters = cs_union(band + drops) ^ rect(-d_eave - 5, -0.01, L + d_eave + 5, tip[1] + 5)
    H = tip[1]
    vr = H * 0.52
    u_r = vr / s - d_eave + depth * c * 0.5
    tri = poly([(-d_eave, 0.0), (L + d_eave, 0.0), tuple(tip)])
    parts = [rect(u_r, vr - 0.7, L - u_r, vr), rect(L / 2 - 0.55, vr - 2.4, L / 2 + 0.55, H - 0.5)]
    n = max(3, int((L - 2 * u_r) / 2.4))            # spindles 1 mm thick, 1.4 mm apart: each stands clear
    for k in range(n):
        x = u_r + (L - 2 * u_r) * (k + 0.5) / n
        ytop = s * (min(x, L - x) + d_eave) - depth * c + 0.3
        if ytop - vr < 1.0:
            continue
        parts += [rect(x - 0.5, vr - 0.1, x + 0.5, ytop), circle((x, vr + 0.8), 0.62, 16)]
    frame_cs = (cs_union(parts) ^ tri) + rafters
    frame_cs = cs_union([pc for pc in frame_cs.decompose() if pc.area() > 2.0])
    out = [_text(frame_cs, 0.0, d)]
    kb = vr - 2.4
    out.append(_text(cs_union([rect(L / 2 - 0.4, kb - 1.8, L / 2 + 0.4, kb + 0.3), circle((L / 2, kb - 2.0), 0.6, 18),
                             poly([(L / 2 - 0.45, kb - 2.4), (L / 2 + 0.45, kb - 2.4), (L / 2, kb - 3.3)])]), 0.0, d + 0.2))
    if finial:
        out.append(_text(cs_union([rect(L / 2 - 0.5, H - 0.6, L / 2 + 0.5, H + finial - 1.2),
                                 poly([(L / 2 - 0.7, H + finial - 1.2), (L / 2 + 0.7, H + finial - 1.2), (L / 2, H + finial)])]),
                       0.0, d + 0.2))
    return union(out)


def gable_eastlake(L, slope, d_eave, skin=1.8, width=1.6, d=TRIM_D, tie=0.3, finial=6.0):
    """Eastlake gable ornament hung on the rake like a bargeboard: narrow rafters with a drop
    at each foot; a tie beam across the gable ``tie`` of the way up, faced with a row of
    square rosette panels; a half-round fan standing on the tie beam, its rays raised; a king
    post from the fan's hub to the apex; and a pinnacle-topped spike at the apex. Flat, prints
    face-up; place at w = rake."""
    s = slope
    c = math.hypot(1.0, s)
    tip = np.array([L / 2, s * (L / 2 + d_eave)])
    depth = skin + width
    band = []
    for a in (np.array([-d_eave, 0.0]), np.array([L + d_eave, 0.0])):
        n = np.array([s, -1.0]) / c if a[0] < L / 2 else np.array([-s, -1.0]) / c
        band.append(poly([tuple(a), tuple(tip), tuple(tip + n * depth), tuple(a + n * depth)]))
    rafters = cs_union(band) ^ rect(-d_eave - 5, -0.01, L + d_eave + 5, tip[1] + 5)
    H = tip[1]
    vt = round(H * tie / 0.2) * 0.2
    u_t = vt / s - d_eave
    tri = poly([(-d_eave, 0.0), (L + d_eave, 0.0), tuple(tip)])
    beam = rect(u_t - 0.6, vt - 1.6, L - u_t + 0.6, vt + 0.2)
    r_fan = min(4.2, (H - vt) * 0.32)
    fan = (circle((L / 2, vt + 0.2), r_fan, 40) - circle((L / 2, vt + 0.2), r_fan - 0.6, 40)) ^ rect(-5, vt + 0.1, L + 5, H)
    hub = circle((L / 2, vt + 0.2), 1.2, 24) ^ rect(-5, vt + 0.1, L + 5, H)
    rays = cs_union([stroke([(L / 2 + 1.0 * math.cos(a), vt + 0.2 + 1.0 * math.sin(a)),
                             (L / 2 + (r_fan - 0.3) * math.cos(a), vt + 0.2 + (r_fan - 0.3) * math.sin(a))], 0.55)
                     for a in np.linspace(math.pi / 8, 7 * math.pi / 8, 7)])
    king = rect(L / 2 - 0.5, vt + 0.2, L / 2 + 0.5, H)
    frame = ((beam + fan + hub + rays + king) ^ tri) + rafters
    drops = []
    for a, sg in ((np.array([-d_eave, 0.0]), 1), (np.array([L + d_eave, 0.0]), -1)):
        n = np.array([s, -1.0]) / c if a[0] < L / 2 else np.array([-s, -1.0]) / c
        foot = a + n * depth
        x = float((a[0] + foot[0]) / 2)
        drops.append(cs_union([rect(x - 0.45, -2.2, x + 0.45, 0.2), circle((x, -2.2), 0.7, 16),
                               poly([(x - 0.45, -2.6), (x + 0.45, -2.6), (x, -3.4)])]))
    frame = frame + cs_union(drops)
    parts = [_text(frame, 0.0, d)]
    n = max(3, int((L - 2 * u_t) / 2.8))
    for k in range(n):
        u = u_t + 0.6 + (L - 2 * u_t - 1.2) * (k + 0.5) / n
        parts.append(_text(rect(u - 0.9, vt - 1.4, u + 0.9, vt), d - 0.01, d + 0.4))
        parts.append(_text(circle((u, vt - 0.7), 0.4, 12), d + 0.39, d + 0.8))
    fcs = cs_union([rect(L / 2 - 0.5, H - 0.6, L / 2 + 0.5, H + finial - 2.2), circle((L / 2, H + finial - 1.6), 0.8, 20),
                    poly([(L / 2 - 0.4, H + finial - 1.0), (L / 2 + 0.4, H + finial - 1.0), (L / 2, H + finial)])])
    parts.append(_text(fcs, 0.0, d + 0.2))
    return union(parts)


def gable_wheel(L, slope, d_eave, skin=1.8, width=1.6, d=TRIM_D, collar=0.34, finial=4.0):
    """Stick-style gable ornament hung on the rake: narrow rafters with a drop at each foot, a
    collar across the gable with a row of pendant drops under it, and a spoked wheel (a rim,
    eight spokes and a hub) standing on the collar and touching the rafters; a spike over the
    apex. Flat, prints face-up; place at w = rake."""
    s = slope
    c = math.hypot(1.0, s)
    tip = np.array([L / 2, s * (L / 2 + d_eave)])
    depth = skin + width
    band = []
    for a in (np.array([-d_eave, 0.0]), np.array([L + d_eave, 0.0])):
        n = np.array([s, -1.0]) / c if a[0] < L / 2 else np.array([-s, -1.0]) / c
        band.append(poly([tuple(a), tuple(tip), tuple(tip + n * depth), tuple(a + n * depth)]))
    rafters = cs_union(band) ^ rect(-d_eave - 5, -0.01, L + d_eave + 5, tip[1] + 5)
    H = tip[1]
    vc = round(H * collar / 0.2) * 0.2
    u_c = vc / s - d_eave
    tri = poly([(-d_eave, 0.0), (L + d_eave, 0.0), tuple(tip)])
    parts = [rect(u_c - 0.5, vc, L - u_c + 0.5, vc + 1.2)]
    n = max(3, int((L - 2 * u_c) / 1.8))
    for k in range(n):
        u = u_c + 0.6 + (L - 2 * u_c - 1.2) * (k + 0.5) / n
        parts.append(cs_union([rect(u - 0.3, vc - 1.0, u + 0.3, vc + 0.05), circle((u, vc - 1.2), 0.45, 12)]))
    # the wheel: as big as fits between the collar and the rafters
    inner = (tri - rafters.offset(0.0)) ^ rect(-5, vc + 1.2, L + 5, H)
    from .lace import _fit
    fit = _fit(inner.offset(0.3), (L / 2, vc + (H - vc) * 0.35), rmin=1.5, rmax=6.0)
    if fit is not None:
        (cx, cy), r = fit
        cx = L / 2
        wheel = [circle((cx, cy), r, 48) - circle((cx, cy), r - 0.7, 48), circle((cx, cy), 0.9, 20)]
        wheel += [stroke([(cx, cy), (cx + (r - 0.3) * math.cos(a), cy + (r - 0.3) * math.sin(a))], 0.55)
                  for a in np.linspace(0, 2 * math.pi, 8, endpoint=False)]
        wheel.append(rect(cx - 0.5, vc + 1.1, cx + 0.5, cy - r + 0.35))
        parts += wheel
    frame = (cs_union(parts) ^ tri) + rafters
    drops = []
    for a in (np.array([-d_eave, 0.0]), np.array([L + d_eave, 0.0])):
        nrm = np.array([s, -1.0]) / c if a[0] < L / 2 else np.array([-s, -1.0]) / c
        foot = a + nrm * depth
        x = float((a[0] + foot[0]) / 2)
        drops.append(cs_union([rect(x - 0.45, -2.0, x + 0.45, 0.2), circle((x, -2.0), 0.65, 16)]))
    frame = frame + cs_union(drops)
    fcs = cs_union([rect(L / 2 - 0.45, H - 0.6, L / 2 + 0.45, H + finial - 1.0),
                    poly([(L / 2 - 0.45, H + finial - 1.0), (L / 2 + 0.45, H + finial - 1.0), (L / 2, H + finial)])])
    return _text(frame, 0.0, d) + _text(fcs, 0.0, d + 0.2)


def gable_pediment(L, slope, d_eave, skin=1.8, width=1.6, d=TRIM_D, finial=4.0, fan_v=None, clear=None, fan_r=None):
    """Free Classic gable ornament hung on the rake: raking boards, a cornice board across the
    gable's foot closing it into a pediment, and in the tympanum a half-round fan (a moulded
    rim, rays and a hub) standing on the cornice; a spike over the apex (the Larkspur). Flat,
    prints face-up; place at w = rake. ``fan_v``: raise the fan's centre (a sunburst over an
    attic window), ``clear``: a cross-section (the window and its frame) the fan keeps off,
    ``fan_r``: the fan's radius."""
    s = slope
    c = math.hypot(1.0, s)
    tip = np.array([L / 2, s * (L / 2 + d_eave)])
    depth = skin + width
    band = []
    for a in (np.array([-d_eave, 0.0]), np.array([L + d_eave, 0.0])):
        n = np.array([s, -1.0]) / c if a[0] < L / 2 else np.array([-s, -1.0]) / c
        band.append(poly([tuple(a), tuple(tip), tuple(tip + n * depth), tuple(a + n * depth)]))
    rafters = cs_union(band) ^ rect(-d_eave - 5, -0.01, L + d_eave + 5, tip[1] + 5)
    H = tip[1]
    tri = poly([(-d_eave, 0.0), (L + d_eave, 0.0), tuple(tip)])
    vb = 1.8
    parts = [rect(-d_eave, 0.0, L + d_eave, vb)]                                   # the cornice across the foot
    fv = vb if fan_v is None else fan_v
    R = fan_r or min(L * 0.24, (H - vb) * 0.62)
    cx = L / 2
    half = circle((cx, fv), R, 48) ^ rect(-5, fv - 0.01, L + 5, H)
    rim = half - circle((cx, fv), R - 0.8, 48)
    rays = cs_union([stroke([(cx, fv), (cx + R * math.cos(a), fv + R * math.sin(a))], 0.55)
                     for a in np.linspace(math.pi / 8, 7 * math.pi / 8, 7)]) ^ half
    hub = circle((cx, fv), min(1.4, R * 0.3), 24) ^ rect(-5, fv - 0.01, L + 5, H)
    if clear is not None:
        rim, rays, hub = rim - clear, rays - clear, hub - clear
    parts += [rim, rays, hub]
    frame = (cs_union(parts) ^ tri) + rafters
    out = [_text(frame, 0.0, d), _text(rim.offset(-0.15) + hub.offset(-0.15), 0.0, d + 0.4),
           _text(rect(-d_eave, vb - 0.6, L + d_eave, vb) ^ tri, 0.0, d + 0.4)]
    if finial:
        fcs = cs_union([rect(L / 2 - 0.45, H - 0.6, L / 2 + 0.45, H + finial - 1.0),
                        poly([(L / 2 - 0.45, H + finial - 1.0), (L / 2 + 0.45, H + finial - 1.0), (L / 2, H + finial)])])
        out.append(_text(fcs, 0.0, d + 0.2))
    return union(out)


def gable_pendant(L, slope, d_eave, skin=1.8, width=1.6, d=TRIM_D, finial=4.0):
    """Queen Anne gable ornament hung on the rake: raking boards, a pair of curved braces
    springing from the rafters to a turned king pendant that hangs below them from the apex,
    and a spike over the apex (the Juniper). Flat, prints face-up; place at w = rake."""
    s = slope
    c = math.hypot(1.0, s)
    tip = np.array([L / 2, s * (L / 2 + d_eave)])
    depth = skin + width
    band = []
    for a in (np.array([-d_eave, 0.0]), np.array([L + d_eave, 0.0])):
        n = np.array([s, -1.0]) / c if a[0] < L / 2 else np.array([-s, -1.0]) / c
        band.append(poly([tuple(a), tuple(tip), tuple(tip + n * depth), tuple(a + n * depth)]))
    rafters = cs_union(band) ^ rect(-d_eave - 5, -0.01, L + d_eave + 5, tip[1] + 5)
    H = tip[1]
    tri = poly([(-d_eave, 0.0), (L + d_eave, 0.0), tuple(tip)])
    cx = L / 2
    # the king pendant: a post from the apex down to about a third of the gable's height,
    # swelling to a turned drop at its foot
    pv = H * 0.36
    post = rect(cx - 0.6, pv, cx + 0.6, H)
    drop = cs_union([circle((cx, pv), 1.0, 24), poly([(cx - 0.7, pv - 0.4), (cx + 0.7, pv - 0.4), (cx, pv - 2.6)])])
    # curved braces: quarter arcs from each rafter to the pendant, their undersides round
    braces = []
    R = min(L * 0.22, (H - pv) * 0.7)
    for sg in (-1, 1):
        cc = (cx + sg * R, pv + R * 0.2)
        ring = circle(cc, R + 0.35, 48) - circle(cc, R - 0.35, 48)
        quad = rect(min(cx, cx + sg * R), pv, max(cx, cx + sg * R), H)
        braces.append(ring ^ quad)
    frame = (cs_union([post] + braces) ^ tri) + rafters + drop
    out = [_text(frame, 0.0, d), _text(post.offset(-0.2) ^ tri, 0.0, d + 0.4)]
    if finial:
        fcs = cs_union([rect(cx - 0.45, H - 0.6, cx + 0.45, H + finial - 1.0),
                        poly([(cx - 0.45, H + finial - 1.0), (cx + 0.45, H + finial - 1.0), (cx, H + finial)])])
        out.append(_text(fcs, 0.0, d + 0.2))
    return union(out)


def gable_keyhole(L, slope, d_eave, skin=1.8, width=3.0, d=TRIM_D, finial=5.0, collar=0.42):
    """Deep gingerbread bargeboards (the Camellia): each rafter board's foot cut into a row of
    cusps with a ball at every point and pierced with keyholes, a collar tie across the gable
    with a diamond-lattice panel above it up to the apex, a teardrop pendant under the collar
    and a spike over the apex. ``collar``: the collar tie's height as a fraction of the gable's
    (raise it to keep the pendant clear of an attic window). Flat, prints face-up; place at
    w = rake."""
    s = slope
    c = math.hypot(1.0, s)
    tip = np.array([L / 2, s * (L / 2 + d_eave)])
    H = tip[1]
    depth = skin + width
    ends = (np.array([-d_eave, 0.0]), np.array([L + d_eave, 0.0]))
    band, cuts, balls, holes = [], [], [], []
    for a in ends:
        n = np.array([s, -1.0]) / c if a[0] < L / 2 else np.array([-s, -1.0]) / c
        band.append(poly([tuple(a), tuple(tip), tuple(tip + n * depth), tuple(a + n * depth)]))
        run = float(np.linalg.norm(tip - a))
        dirv = (tip - a) / run
        n_c = max(3, int(run / 2.6))
        for k in range(n_c + 1):
            p = a + dirv * (run * k / n_c)
            if k < n_c - 1:                               # a scallop cut between two cusp points (none at the apex)
                q = a + dirv * (run * (k + 0.5) / n_c)
                side = rect(-d_eave - 5, -5, L / 2 - 0.8, H + 5) if a[0] < L / 2 else rect(L / 2 + 0.8, -5, L + d_eave + 5, H + 5)
                cuts.append(circle(tuple(q + n * (depth + 0.55)), run / n_c * 0.62, 28) ^ side)
            if 0 < k < n_c - 1:                           # a ball hung at each cusp point
                balls.append(circle(tuple(p + n * (depth - 0.1)), 0.62, 16))     # a ball well into the cusp
            if 0 < k < n_c - 2 and k % 2 == 1:            # a keyhole in the board over every other scallop
                q = a + dirv * (run * (k + 0.5) / n_c) + n * (skin + width * 0.28)
                holes.append(cs_union([circle(tuple(q), 0.5, 16),
                                       poly([tuple(q + np.array([-0.3, 0.0])), tuple(q + np.array([0.3, 0.0])),
                                             tuple(q + np.array([0.4, -0.9])), tuple(q + np.array([-0.4, -0.9]))])]))
    tri = poly([(-d_eave, 0.0), (L + d_eave, 0.0), tuple(tip)])
    rafters = cs_union(band) ^ tri                     # (each board's square end stays under the other's line)
    rafters = rafters - cs_union(cuts)
    rafters = rafters + (rect(L / 2 - 1.0, H - depth * c - 1.0, L / 2 + 1.0, H) ^ tri)   # a king post ties the halves
    rafters = cs_union([pc for pc in rafters.decompose() if pc.area() > 1.0])
    rafters = rafters + (cs_union(balls) ^ rect(-d_eave - 5, 0.2, L + d_eave + 5, H))
    if holes:
        rafters = rafters - cs_union(holes)
    # collar tie, lattice above it, pendant below it
    inner = tri.offset(-depth * c * 0.62, JoinType.Miter, 4.0)
    vc = H * collar
    collar = rect(-d_eave, vc - 0.6, L + d_eave, vc + 0.6) ^ tri
    panel = inner ^ rect(-d_eave, vc + 0.5, L + d_eave, H)
    parts = [rafters, collar]
    if not panel.is_empty():
        bars = []
        pb = panel.bounds()
        span_ = (pb[2] - pb[0]) + (pb[3] - pb[1])
        k = -int(span_ / 1.8) - 2
        while k * 1.8 < span_ + 2:
            x = pb[0] + k * 1.8
            bars.append(stroke([(x, pb[1] - 1), (x + (pb[3] - pb[1]) + 2, pb[3] + 1)], 0.55, caps=False))
            bars.append(stroke([(x, pb[3] + 1), (x + (pb[3] - pb[1]) + 2, pb[1] - 1)], 0.55, caps=False))
            k += 1
        rim = panel - panel.offset(-0.55, JoinType.Miter, 4.0)
        parts.append((cs_union(bars) ^ panel) + rim)
    cx = L / 2
    parts.append(cs_union([rect(cx - 0.45, vc - 2.2, cx + 0.45, vc - 0.5), circle((cx, vc - 2.4), 0.85, 24),
                           poly([(cx - 0.6, vc - 2.9), (cx + 0.6, vc - 2.9), (cx, vc - 4.4)])]))
    frame = cs_union(parts)
    frame = cs_union([pc for pc in frame.decompose() if pc.area() > 2.0])
    out = [_text(frame, 0.0, d)]
    if finial:
        fcs = cs_union([rect(cx - 0.45, H - 0.6, cx + 0.45, H + finial - 1.2), circle((cx, H + finial * 0.4), 0.7, 20),
                        poly([(cx - 0.45, H + finial - 1.2), (cx + 0.45, H + finial - 1.2), (cx, H + finial)])])
        out.append(_text(fcs, 0.0, d + 0.2))
    return union(out)


def gable_crescent(L, slope, d_eave, skin=1.8, width=1.8, d=TRIM_D, finial=4.4):
    """A crescent gable (the Wisteria): raking boards, a crescent arch hung between them from
    about a third of the way up (thick at its crown, thinning to its springings), a turned drop
    at each springing, a pierced diamond in the apex panel above the arch, and a spike over
    the apex. Flat, prints face-up; place at w = rake."""
    s = slope
    c = math.hypot(1.0, s)
    tip = np.array([L / 2, s * (L / 2 + d_eave)])
    H = tip[1]
    depth = skin + width
    tri = poly([(-d_eave, 0.0), (L + d_eave, 0.0), tuple(tip)])
    band = []
    for a in (np.array([-d_eave, 0.0]), np.array([L + d_eave, 0.0])):
        n = np.array([s, -1.0]) / c if a[0] < L / 2 else np.array([-s, -1.0]) / c
        band.append(poly([tuple(a), tuple(tip), tuple(tip + n * depth), tuple(a + n * depth)]))
    rafters = cs_union(band) ^ tri
    inner = tri.offset(-depth * c * 0.5, JoinType.Miter, 4.0)
    ib = inner.bounds()
    vs = H * 0.32                                       # the arch springs from the rafters here
    h_i = (H - depth * c) - vs                          # the rafters' inner edges meet this far above the springing
    half = h_i / s + 0.4                                # the arch springs from the rafters' inner edges
    rise = h_i * 0.42                                   # low enough to stand clear of the steep rafters
    cx = L / 2
    ell = lambda a_, b_: poly([(cx + a_ * math.cos(t), vs + b_ * math.sin(t)) for t in np.linspace(0, math.pi, 40)] +
                              [(cx - a_, vs - 0.01), (cx + a_, vs - 0.01)])
    outer = ell(half + 0.3, rise + 0.9)
    inside = ell(half - 0.6, rise)
    arch = (outer - inside) ^ tri
    parts = [rafters, arch]
    th = math.radians(42.0)                             # a drop hangs where the arch comes clear of the rafters
    for sg in (-1, 1):
        x = cx + sg * (half - 0.45) * math.cos(th)
        y = vs + rise * math.sin(th)
        parts.append(cs_union([rect(x - 0.4, y - 1.6, x + 0.4, y + 0.2), circle((x, y - 1.9), 0.62, 20),
                               poly([(x - 0.45, y - 2.3), (x + 0.45, y - 2.3), (x, y - 3.3)])]))
    apex_panel = (inner ^ rect(-50, vs + rise + 0.8, 50, H)) - rect(-50, -50, 50, vs + rise + 0.8)
    if not apex_panel.is_empty():
        pb = apex_panel.bounds()
        my = (pb[1] + pb[3]) / 2
        dh = min(1.6, (pb[3] - pb[1]) * 0.3)
        dia = poly([(cx, my - dh), (cx + dh * 0.7, my), (cx, my + dh), (cx - dh * 0.7, my)])
        parts.append(apex_panel - dia)
    frame = cs_union(parts)
    frame = cs_union([pc for pc in frame.decompose() if pc.area() > 2.0])
    out = [_text(frame, 0.0, d)]
    if finial:
        fcs = cs_union([rect(cx - 0.45, H - 0.6, cx + 0.45, H + finial - 1.0),
                        poly([(cx - 0.45, H + finial - 1.0), (cx + 0.45, H + finial - 1.0), (cx, H + finial)])])
        out.append(_text(fcs, 0.0, d + 0.2))
    return union(out)


def gable_star(L, slope, d_eave, skin=1.8, width=1.6, d=TRIM_D, finial=4.4):
    """A star gable (the Hawthorn): raking boards, a collar tie across the gable, a king post
    from the apex down through a disc pierced with an eight-pointed star to the collar, a
    turned drop under the collar and a spike over the apex. Flat, prints face-up; place at
    w = rake."""
    s = slope
    c = math.hypot(1.0, s)
    tip = np.array([L / 2, s * (L / 2 + d_eave)])
    H = tip[1]
    depth = skin + width
    tri = poly([(-d_eave, 0.0), (L + d_eave, 0.0), tuple(tip)])
    band = []
    for a in (np.array([-d_eave, 0.0]), np.array([L + d_eave, 0.0])):
        n = np.array([s, -1.0]) / c if a[0] < L / 2 else np.array([-s, -1.0]) / c
        band.append(poly([tuple(a), tuple(tip), tuple(tip + n * depth), tuple(a + n * depth)]))
    rafters = cs_union(band) ^ tri
    cx = L / 2
    vc = H * 0.38
    collar = rect(-d_eave, vc - 0.6, L + d_eave, vc + 0.6) ^ tri
    top_in = H - depth * c
    R = min((top_in - vc) * 0.36, (L / 2) * 0.3)
    cy = vc + 0.6 + R + 0.4
    disc = circle((cx, cy), R, 40)
    star = poly([(cx + (R - 0.7 if k % 2 == 0 else (R - 0.7) * 0.45) * math.cos(math.pi / 2 + k * math.pi / 8),
                  cy + (R - 0.7 if k % 2 == 0 else (R - 0.7) * 0.45) * math.sin(math.pi / 2 + k * math.pi / 8)) for k in range(16)])
    post = rect(cx - 0.55, vc, cx + 0.55, H) ^ tri
    drop = cs_union([rect(cx - 0.45, vc - 1.8, cx + 0.45, vc), circle((cx, vc - 2.1), 0.7, 20),
                     poly([(cx - 0.5, vc - 2.6), (cx + 0.5, vc - 2.6), (cx, vc - 3.6)])])
    frame = cs_union([rafters, collar, post, disc, drop]) - (star - circle((cx, cy), 0.55, 16))
    frame = cs_union([pc for pc in frame.decompose() if pc.area() > 2.0])
    out = [_text(frame, 0.0, d)]
    if finial:
        fcs = cs_union([rect(cx - 0.45, H - 0.6, cx + 0.45, H + finial - 1.0),
                        poly([(cx - 0.45, H + finial - 1.0), (cx + 0.45, H + finial - 1.0), (cx, H + finial)])])
        out.append(_text(fcs, 0.0, d + 0.2))
    return union(out)


def gable_arcade(L, slope, d_eave, skin=1.8, width=1.6, d=TRIM_D, finial=4.4, band_at=0.34):
    """An arcaded gable (the Magnolia): raking boards and, across the gable, a band pierced
    with a row of little round-headed arches, a drop hung under each pier between them, a
    king post from the band to the apex carrying a ring, and a spike over the apex.
    ``band_at``: the band's height as a fraction of the gable's (raise it clear of an attic
    window). Flat, prints face-up; place at w = rake."""
    s = slope
    c = math.hypot(1.0, s)
    tip = np.array([L / 2, s * (L / 2 + d_eave)])
    H = tip[1]
    depth = skin + width
    tri = poly([(-d_eave, 0.0), (L + d_eave, 0.0), tuple(tip)])
    band = []
    for a in (np.array([-d_eave, 0.0]), np.array([L + d_eave, 0.0])):
        n = np.array([s, -1.0]) / c if a[0] < L / 2 else np.array([-s, -1.0]) / c
        band.append(poly([tuple(a), tuple(tip), tuple(tip + n * depth), tuple(a + n * depth)]))
    rafters = cs_union(band) ^ tri
    cx = L / 2
    vb = H * band_at
    bh = 3.2
    inner = tri.offset(-depth * c * 0.5, JoinType.Miter, 4.0)
    arc_band = (rect(-d_eave, vb, L + d_eave, vb + bh) ^ tri)
    ib = (inner ^ rect(-50, vb + bh - 0.2, 50, vb + bh)).bounds()     # the band's width at its top
    span_ = ib[2] - ib[0]
    n = max(3, int(span_ / 2.6))
    p_ = span_ / n
    holes, drops = [], []
    for k in range(n):
        u = ib[0] + p_ * (k + 0.5)
        ow = min(0.8, p_ / 2 - 0.35)
        holes.append(cs_union([rect(u - ow, vb + 0.6, u + ow, vb + bh - 0.6 - ow), circle((u, vb + bh - 0.6 - ow), ow, 16)]))
    for k in range(1, n):
        u = ib[0] + p_ * k
        drops.append(cs_union([rect(u - 0.35, vb - 1.2, u + 0.35, vb + 0.01), circle((u, vb - 1.5), 0.55, 16),
                               poly([(u - 0.4, vb - 1.9), (u + 0.4, vb - 1.9), (u, vb - 2.8)])]))
    post = rect(cx - 0.5, vb + bh - 0.01, cx + 0.5, H) ^ tri               # a king post up to the apex
    vr = (vb + bh + H - depth * c) / 2
    ring = circle((cx, vr), 1.4, 28) - circle((cx, vr), 0.7, 20)          # carrying a ring half way up
    parts = [rafters, arc_band - cs_union(holes), post, ring] + drops
    frame = cs_union(parts)
    frame = cs_union([pc for pc in frame.decompose() if pc.area() > 2.0])
    out = [_text(frame, 0.0, d)]
    if finial:
        fcs = cs_union([rect(cx - 0.45, H - 0.6, cx + 0.45, H + finial - 1.0),
                        poly([(cx - 0.45, H + finial - 1.0), (cx + 0.45, H + finial - 1.0), (cx, H + finial)])])
        out.append(_text(fcs, 0.0, d + 0.2))
    return union(out)

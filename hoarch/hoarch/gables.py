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


def bargeboard(L, slope, d_eave, skin=1.8, width=2.6, d=0.8, finial=5.0, drop=3.0, pierce="trefoil"):
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
    board = board.offset(-0.26, JoinType.Round).offset(0.26, JoinType.Round)
    board = cs_union([pc for pc in board.decompose() if pc.area() > 2.0])
    parts = [ext(board, 0.0, d)]
    ay = tip[1] - depth * c - 0.4
    if drop:
        dcs = cs_union([rect(L / 2 - 0.45, ay - drop, L / 2 + 0.45, ay + 0.3),
                        circle((L / 2, ay - drop + 0.6), 0.75, 20),
                        poly([(L / 2 - 0.5, ay - drop + 0.2), (L / 2 + 0.5, ay - drop + 0.2), (L / 2, ay - drop - 1.0)])])
        parts.append(ext(dcs, 0.0, d + 0.2))
    if finial:
        fcs = cs_union([rect(L / 2 - 0.5, tip[1] - 0.6, L / 2 + 0.5, tip[1] + finial - 1.2),
                        circle((L / 2, tip[1] + finial * 0.45), 0.8, 20),
                        poly([(L / 2 - 0.5, tip[1] + finial - 1.2), (L / 2 + 0.5, tip[1] + finial - 1.2), (L / 2, tip[1] + finial)])])
        parts.append(ext(fcs, 0.0, d + 0.2))
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


def gable_truss(L, slope, d_eave, skin=1.8, width=1.6, d=0.8, collar=0.42, finial=5.0, drop=3.4, fan=True):
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
    frame_cs = frame_cs.offset(-0.26, JoinType.Round).offset(0.26, JoinType.Round)
    frame_cs = cs_union([pc for pc in frame_cs.decompose() if pc.area() > 2.0])
    parts = [ext(frame_cs, 0.0, d)]
    parts.append(ext(rect(u_c - 0.3, vc - 1.5, L - u_c + 0.3, vc - 0.9), 0.0, d + 0.4))      # a bead on the collar
    if drop:
        dcs = cs_union([rect(L / 2 - 0.45, kp_bot - drop, L / 2 + 0.45, kp_bot + 0.3),
                        circle((L / 2, kp_bot - drop + 0.6), 0.75, 20),
                        poly([(L / 2 - 0.5, kp_bot - drop + 0.2), (L / 2 + 0.5, kp_bot - drop + 0.2), (L / 2, kp_bot - drop - 1.0)])])
        parts.append(ext(dcs, 0.0, d + 0.2))
    if finial:
        fcs = cs_union([rect(L / 2 - 0.5, H - 0.6, L / 2 + 0.5, H + finial - 1.2),
                        circle((L / 2, H + finial * 0.45), 0.8, 20),
                        poly([(L / 2 - 0.5, H + finial - 1.2), (L / 2 + 0.5, H + finial - 1.2), (L / 2, H + finial)])])
        parts.append(ext(fcs, 0.0, d + 0.2))
    return union(parts)

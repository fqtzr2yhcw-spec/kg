"""Dormers, towers, chimneys, porches and steps.

Local frames follow the insert convention where it applies: u along the wall,
v up, w out of the wall. Each builder returns manifolds in its local frame;
the building script places them with a 3x4 frame matrix.
"""
import math

import numpy as np
from manifold3d import JoinType, Manifold as M

from .core import (RIB, SLOT, Facade, box, brick, ccw, circle, cs_union, lattice, miters, offset, poly, rect, slab,
                   sweep_run, union)
from .ornament import chamfer_box, chimney_pot, dentils, ext, keystone, spandrel, stroke
from . import openings as O


# ------------------------------------------------------------------ dormer
def dormer(W=17.2, H=13.5, D=10.5, win_w=7.4, win_h=16.0, wall=2.0, hood_t=0.85):
    """Round-topped dormer. Local frame: u across, v up from the dormer sill line
    (mansard base), w out of the front face (front face at w = 0, body back at -D).

    Returns dict(body, hood, window, keep) where keep is a solid used to notch the
    mansard slices."""
    R = W / 2
    face = cs_union([rect(-R, 0, R, H), circle((0, H), R, 48) ^ rect(-R, H, R, H + R + 1)])
    body = ext(face, -D, 0.0)
    # hollow: flat-ceilinged cavity (bridges cleanly when printed upright)
    cav = rect(-R + wall, 0.0, R - wall, H)
    body = body - ext(cav, -D - 1, -wall)
    win = O.window_insert(win_w, win_h, rise=win_w / 2, lites=(2, 2), bare=True)
    v_sill = 1.4
    body = body - ext(win["cut"].translate((0, v_sill)), -wall - 1, 1)
    # front dressing: pilasters, arch band, keystone, casing, sill
    dress = []
    for s in (-1, 1):
        pu = s * (R - 0.8)
        dress.append(ext(rect(pu - 0.8, 0.0, pu + 0.8, H - 0.6), 0.0, 0.5))
        dress.append(ext(rect(pu - 1.0, H - 1.4, pu + 1.0, H - 0.2), 0.0, 0.75))          # capital
        dress.append(ext(rect(pu - 1.0, 0.0, pu + 1.0, 0.8), 0.0, 0.7))                   # plinth
    arch_band = (circle((0, H), R, 48) - circle((0, H), R - 1.2, 48)) ^ rect(-R, H - 0.3, R, H + R + 1)
    dress.append(ext(arch_band, 0.0, 0.5))
    dress.append(keystone(0.0, H + R - 2.2, 2.2, 1.0, 1.5, 0.0, 0.9))
    cas = (win["cut"].offset(0.8, JoinType.Round) - win["cut"]).translate((0, v_sill))
    dress.append(ext(cas ^ rect(-R, v_sill, R, H + R), 0.0, 0.45))
    dress.append(ext(rect(-win_w / 2 - 1.3, v_sill - 0.8, win_w / 2 + 1.3, v_sill), 0.0, 0.9))
    body = body + union(dress)
    # hood: barrel vault shell over the arched top, with a front lip
    ro, ri = R + hood_t, R + 0.02
    shell = (circle((0, H), ro, 64) - circle((0, H), ri, 64)) ^ rect(-ro - 1, H, ro + 1, H + ro + 1)
    hood = ext(shell, -D, 0.9)
    lip = (circle((0, H), ro + 0.35, 64) - circle((0, H), ri, 64)) ^ rect(-ro - 1, H, ro + 1, H + ro + 2)
    hood = hood + ext(lip, 0.3, 0.9)
    window = win["insert"].translate([0, v_sill, -wall + O.PLUG])
    keep = ext(face.offset(0.15, JoinType.Miter), -D - 0.15, 3.0) + ext(shell.offset(0.15, JoinType.Round), -D - 0.15, 3.0)
    return dict(body=body, hood=hood, window=window, keep=keep, top=H + ro)


# ------------------------------------------------------------------ tower
def tower_cap(path, z0, h=16.0, d_flare=0.4, d_top=-7.0, bands=4, top_th=1.2):
    """Concave (bell-cast) mansard cap for a small tower, as a solid with a flat top.
    Profile (d, z) approximated with ``bands`` straight segments."""
    pts = []
    for k in range(bands + 1):
        s = k / bands
        # concave: fast inward move low down, slower near the top
        d = d_flare + (d_top - d_flare) * (1 - (1 - s) ** 1.8)
        pts.append((d, z0 + h * s))
    return pts


def tower_cap_solid(path, z0, h=16.0, d_flare=0.4, d_top=-7.0, bands=4):
    from .roof import slope_texture
    pts = tower_cap(path, z0, h, d_flare, d_top, bands)
    P = np.asarray(ccw(path), float)
    Mi = miters(P)
    # build as a stack of frusta (hulls) between successive offsets: robust for convex paths
    layers = []
    for (d0, z0_), (d1, z1_) in zip(pts[:-1], pts[1:]):
        a = np.c_[P + d0 * Mi, np.full(len(P), z0_)]
        b = np.c_[P + d1 * Mi, np.full(len(P), z1_)]
        layers.append(M.hull_points(np.vstack([a, b]).tolist()))
    solid = union(layers)
    tex = union([slope_texture(path, z0_, z1_, d0, d1, pitch=1.35, wtab=1.55, d=0.3)
                 for (d0, z0_), (d1, z1_) in zip(pts[:-1], pts[1:])])
    return solid, tex, pts


# ------------------------------------------------------------------ chimney
def chimney(w=10.5, dpt=10.5, h=20.5, cap=1.6, pots=2, peg=(5.8, 5.8, 2.0), panel=(1.4, 6.0)):
    """Brick chimney standing on a flat deck (z = 0 at the deck), with a corbelled
    cap, pots and a locating peg below. ``panel`` = (gap under the cap, height) of a sunk
    panel on every face, its top edge bevelled 45 degrees so it prints upright."""
    core = box([-w / 2, -dpt / 2, 0], [w / 2, dpt / 2, h - 3 * cap])
    parts = [core]
    prev = 0.0                                    # the core (the top brick course may be a joint)
    for k, grow in enumerate((0.5, 1.0, 0.6)):
        z = h - 3 * cap + k * cap
        parts.append(box([-w / 2 - grow, -dpt / 2 - grow, z], [w / 2 + grow, dpt / 2 + grow, z + cap]))
        # corbel out at most 0.25 per 0.2 mm layer so no course hangs in the air
        g, zz = prev, z
        while grow - g > 0.3:
            g += 0.25
            zz -= 0.2
        g2, z2 = prev, zz
        while g2 < grow - 0.3 + 1e-9 and z2 < z:
            g2 += 0.25
            parts.append(box([-w / 2 - g2, -dpt / 2 - g2, z2], [w / 2 + g2, dpt / 2 + g2, z2 + 0.2]))
            z2 += 0.2
        prev = grow
    # brick texture on the 4 shaft faces
    shaft_h = h - 3 * cap
    fac = [Facade((-w / 2, -dpt / 2), (w / 2, -dpt / 2)), Facade((w / 2, -dpt / 2), (w / 2, dpt / 2)),
           Facade((w / 2, dpt / 2), (-w / 2, dpt / 2)), Facade((-w / 2, dpt / 2), (-w / 2, -dpt / 2))]
    for i, f in enumerate(fac):
        parts.append(f.place(brick(rect(0.1, 0.0, f.L - 0.1, shaft_h), d=0.25,
                                   uoff=0.5 * (i % 2))))
    for k in range(pots):
        x = (k - (pots - 1) / 2) * (w * 0.45)
        parts.append(chimney_pot(1.5, 3.2).translate([x, 0, h]))
    if peg:
        parts.append(box([-peg[0] / 2, -peg[1] / 2, -peg[2]], [peg[0] / 2, peg[1] / 2, 0.01]))
    out = union(parts)
    if panel:
        dep, ins = 0.5, 1.6
        v1 = shaft_h - panel[0]
        v0 = max(0.5, v1 - panel[1])
        pockets = []
        for f in fac:
            u0, u1 = ins, f.L - ins
            pts = [(u, v, ww) for u in (u0, u1) for (v, ww) in ((v0, -dep), (v1 - dep, -dep), (v0, 1.0), (v1, 0.0), (v1, 1.0))]
            pockets.append(f.place(M.hull_points(pts)))
        out = out - union(pockets)
    return out


# ------------------------------------------------------------------ porch
def baluster_cs(u, v0, v1, wmax=1.0, wmin=0.6):
    """Turned baluster silhouette (u centred, v0..v1): base and top blocks, a belly and
    two necks. Never narrower than ``wmin`` so it prints as a shape, not a hairline."""
    prof = [(0.0, 1.0), (0.12, 1.0), (0.14, 0.72), (0.22, 0.66), (0.34, 0.9), (0.46, 1.04), (0.58, 0.92),
            (0.72, 0.64), (0.78, 0.6), (0.82, 0.8), (0.86, 0.62), (0.88, 1.0), (1.0, 1.0)]
    h = v1 - v0
    right = [(u + max(wmin, f * wmax) / 2, v0 + t * h) for t, f in prof]
    left = [(2 * u - x, v) for x, v in reversed(right)]
    return poly(right + left)


def porch_posts(L, H, posts_u, pw=2.6, beam=2.2, drop=5.2, t=2.6, cap=True, style="arcade", rail=None):
    """Flat post panel (prints front-face down, t thick).

    style "arcade": quarter-round spandrels meet at mid-span (Second Empire arcade);
    style "bracket": a pierced scroll bracket each side of every post (Italianate).
    Posts stand on panelled pedestals and carry capital blocks with a sunk rosette
    (cut into the front face, which is the bed face when printed).
    ``rail`` = dict(h, skip=[(u0, u1), ...]): a turned-baluster railing between posts,
    left out of the skipped spans (the steps).
    Local frame: u along the porch edge (0..L), v up from the porch floor, w out
    (panel from w = -t/2 to t/2). posts_u = post centre positions."""
    parts = [ext(rect(0, H - beam, L, H), -t / 2, t / 2)]                     # beam
    cuts = []
    ped_h, cap_h = 3.4, 2.4
    for pu in posts_u:
        shaft = rect(pu - pw / 2 + 0.25, 0.0, pu + pw / 2 - 0.25, H - beam)
        parts.append(ext(shaft, -t / 2 + 0.25, t / 2))
        # pedestal, mid collar and capital block, full width
        for (v0, v1) in ((0.0, ped_h), (H * 0.4, H * 0.4 + 0.8), (H - beam - cap_h, H - beam)):
            parts.append(ext(rect(pu - pw / 2, v0, pu + pw / 2, v1), -t / 2, t / 2))
        parts.append(ext(rect(pu - pw / 2 - 0.3, ped_h - 0.4, pu + pw / 2 + 0.3, ped_h), -t / 2, t / 2))
        parts.append(ext(rect(pu - pw / 2 - 0.35, H - beam - 0.8, pu + pw / 2 + 0.35, H - beam), -t / 2, t / 2))
        # sunk panel in the pedestal, sunk rosette (ring and boss) in the capital
        cuts.append(ext(rect(pu - pw / 2 + 0.5, 0.6, pu + pw / 2 - 0.5, ped_h - 0.9), t / 2 - 0.4, t / 2 + 1))
        cc = (pu, H - beam - cap_h / 2 - 0.2)
        cuts.append(ext(circle(cc, 0.85, 20) - circle(cc, 0.35, 16), t / 2 - 0.4, t / 2 + 1))
    # arcade spandrels between posts
    for a, b in zip(posts_u[:-1], posts_u[1:]):
        span = b - a - pw
        half = span / 2 if style == "arcade" else min(span / 2 - 0.5, 4.6)
        drop_ = drop if style == "arcade" else min(drop, 4.4)
        vt = H - beam
        for s in (-1, 1):
            u_post = a + pw / 2 - 0.25 if s < 0 else b - pw / 2 + 0.25
            sp = spandrel(0.0, half, 0.0, drop_, 0.0, 1.0, bar=0.55)
            # spandrel() draws the corner at u=0: mirror for the right-hand post
            if s < 0:
                sp = sp.translate([u_post, vt, 0])
            else:
                sp = sp.mirror([1, 0, 0]).translate([u_post, vt, 0])
            parts.append(sp.translate([0, 0, t / 2 - 1.0]))
    if style == "arcade":   # pendant drops at the arch crowns
        for a, b in zip(posts_u[:-1], posts_u[1:]):
            um = (a + b) / 2
            parts.append(ext(rect(um - 0.5, H - beam - 1.5, um + 0.5, H - beam), t / 2 - 1.2, t / 2))
    else:                   # a frieze board with a row of drops under the beam
        parts.append(ext(rect(0, H - beam - 0.6, L, H - beam), t / 2 - 0.8, t / 2))
        for a, b in zip(posts_u[:-1], posts_u[1:]):
            for um in np.arange(a + pw / 2 + 6.0, b - pw / 2 - 5.9, 2.4):
                parts.append(ext(rect(um - 0.3, H - beam - 1.2, um + 0.3, H - beam - 0.6), t / 2 - 0.8, t / 2))
    if rail:
        rh = rail.get("h", 8.6)
        skip = rail.get("skip", [])
        for a, b in zip(posts_u[:-1], posts_u[1:]):
            if any(not (b <= s0 or a >= s1) for s0, s1 in skip):
                continue
            u0, u1 = a + pw / 2 - 0.1, b - pw / 2 + 0.1
            parts.append(ext(rect(u0, 0.8, u1, 1.6), t / 2 - 1.2, t / 2))                  # bottom rail
            parts.append(ext(rect(u0, rh - 0.9, u1, rh), t / 2 - 1.4, t / 2))               # hand rail
            parts.append(ext(rect(u0, rh - 0.5, u1, rh), t / 2 - 1.6, t / 2))               # its cap
            n = int((u1 - u0 - 0.9) / 1.8)
            if n >= 1:
                pitch = (u1 - u0) / (n + 1)
                bal = cs_union([baluster_cs(u0 + pitch * (j + 1), 1.55, rh - 0.85) for j in range(n)])
                parts.append(ext(bal, t / 2 - 1.0, t / 2))
    out = union(parts)
    return out - union(cuts) if cuts else out


def porch_deck(poly_pts, outer_edges, H=14.0, floor_t=1.6, piers_u=None, pier=3.4, skirt=1.4, floor=True,
               ledger_off=0.0, infill="lattice", pier_tex="brick", planks=None):
    """Porch deck: brick piers, lattice skirt and fascia along the outer edges, a ledger on
    the house side, and (``floor=True``) the floor slab. With floor=False the floor is left
    to porch_floor() as its own part (its own colour, boards on its bed face).

    Prints upside down (top on the bed). outer_edges: list of edge indices of
    the CCW polygon that face the yard; piers_u: {edge: [u, ...]}."""
    pts = ccw(poly_pts)
    base = poly(pts)
    parts = [slab(base, H - floor_t, H)] if floor else []
    ztop = H - floor_t + (0.01 if floor else -0.02)      # a separate floor rests on this
    if planks is not None:
        # planks printed with the deck (upside down, on the bed): the frame reaches 0.2 up
        # into them so every plank is one solid with it, and joists cross under the planks
        floor_t = planks.get("t", 1.2)
        ztop = H - floor_t + 0.2
        along = np.asarray(planks["along"], float)
        ang = np.degrees(np.arctan2(along[1], along[0])) + (45.0 if planks.get("diagonal") else 0.0)
        b = base.bounds()
        R = np.hypot(b[2] - b[0], b[3] - b[1]) + 10
        cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
        sp = planks.get("joist", 6.0)
        js = cs_union([rect(k - 0.5, -R, k + 0.5, R) for k in np.arange(-R, R, sp)]).rotate(ang).translate((cx, cy))    # across the planks
        parts.append(slab(js ^ offset(base, -0.3), H - floor_t - skirt, ztop))
    for i in range(len(pts)):
        f = Facade(pts[i], pts[(i + 1) % len(pts)], 0.0)
        L = f.L
        if i not in outer_edges:   # ledger along the house: the floor rests on it
            parts.append(f.place(box([0, H - floor_t - skirt, -1.6 - ledger_off], [L, ztop, -ledger_off])))
            continue
        # skirt fascia board under the floor edge, deep enough to carry the lattice, its
        # backing web and the piers when the deck prints upside down without its floor
        parts.append(f.place(box([0, H - floor_t - skirt, -0.9 if floor else -(pier - 0.2)], [L, ztop, 0.0])))
        if floor:  # nosing lip
            parts.append(f.place(box([-0.3, H - 0.6, -0.2], [L + 0.3, H, 0.35])))
        pu = (piers_u or {}).get(i, [])
        # lattice between piers, recessed
        lat_reg = rect(0.2, 0.0, L - 0.2, H - floor_t - skirt)
        for u in pu:
            lat_reg = lat_reg - rect(u - pier / 2, -1, u + pier / 2, H)
        from . import porchwork as PW
        lat = PW.skirt_fill(infill, lat_reg, d=1.2)                # two 0.6 layers: no fused slot
        parts.append(f.place(lat.translate([0, 0, -1.9])))
        parts.append(f.place(box([0.0, 0.0, -2.5], [L, H - floor_t - skirt, -1.8])))      # backing web
        for u in pu:
            pr = box([u - pier / 2, 0.0, -pier + 0.2], [u + pier / 2, H - floor_t - skirt + 0.01, 0.0])
            preg = rect(u - pier / 2 + 0.05, 0.0, u + pier / 2 - 0.05, H - floor_t - skirt)
            if pier_tex == "plain":
                tex = chamfer_box(u - pier / 2 + 0.3, 0.3, u + pier / 2 - 0.3, H - floor_t - skirt - 0.3, 0.0, 0.3, c=0.2)
            else:
                tex = _pier_skin(pier_tex, preg, int(u * 13) % 97)
            tex = tex.translate([0, 0, -0.01])
            parts.append(f.place(pr + tex))
    return union(parts)


def porch_planks(poly_pts, outer_edges, H=14.0, t=1.2, pitch=1.8, crack=0.25, border=1.6, along=None, nose=0.35,
                 diagonal=False, joist=6.0):
    """The porch floor as separate planks with hairline cracks between them, for a deck that
    prints upside down with them: the planks are its first layers on the bed (print them in a
    wood colour and change filament once, at ``t``). The cracks run right through the planks,
    finer than the nozzle, so the boards print as separate strips with a dark line between.
    Border boards frame the yard edges (``border`` = 0 for none) behind a rounded nosing that
    overhangs the skirt. Planks run ``along`` (default: away from the house, perpendicular to
    the longest yard edge); ``diagonal`` turns them 45 degrees."""
    pts = ccw(poly_pts)
    base = poly(pts)
    edges = [Facade(pts[i], pts[(i + 1) % len(pts)], 0.0) for i in outer_edges]
    if along is None:
        along = -max(edges, key=lambda f: f.L).n
    along = np.asarray(along, float) / np.linalg.norm(along)
    ang = np.degrees(np.arctan2(along[1], along[0])) + (45.0 if diagonal else 0.0)
    b = base.bounds()
    R = np.hypot(b[2] - b[0], b[3] - b[1]) + 10
    cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
    cracks = cs_union([rect(k - crack / 2, -R, k + crack / 2, R) for k in np.arange(-R, R, pitch)])
    cracks = cracks.rotate(ang - 90).translate((cx, cy))
    field = base
    if border > 0:
        for f in edges:
            strip = poly([tuple(f.p0 + f.u * -50 + f.n * 0.01), tuple(f.p1 + f.u * 50 + f.n * 0.01),
                          tuple(f.p1 + f.u * 50 - f.n * border), tuple(f.p0 + f.u * -50 - f.n * border)])
            field = field - strip
    boards = field - cracks
    if border > 0:
        boards = boards + (base - offset(field, crack))
    out = slab(boards, H - t, H)
    for f in edges:            # rounded nosing: the border board's edge, proud of the skirt
        out = out + f.place(box([-0.3, H - 0.6, -0.2], [f.L + 0.3, H, nose]))
    return out


def plank_zones(deck, H, planks_col, deck_col, t=1.2):
    """Render zones of a planked deck: the planks (its first ``t`` of print, the wood colour)
    and the frame above them."""
    top = box([-1e4, -1e4, H - t], [1e4, 1e4, H + 5])
    return [(planks_col, deck ^ top), (deck_col, deck - top)]


def _pier_skin(style, reg, seed):
    """Facing for a porch pier, a small-scale match for each building's foundation:
    brick (default), stone, fieldstone, limestone, granite, rubble, parged, block, coursed."""
    from .core import ashlar
    from . import skins as SK
    if style in ("stone", "fieldstone"):
        return ashlar(reg, course=(1.8, 2.6), length=(1.6, 3.4), d=0.3, seed=seed)
    if style == "limestone":
        return SK.brick_bond(reg, "running", bl=3.2, bh=1.6, mortar=0.5, bed=0.4, d=0.3)
    if style == "granite":
        return ashlar(reg, course=(2.4, 3.0), length=(2.4, 3.4), d=0.35, seed=seed, rough=0.15)
    if style == "rubble":
        return ashlar(reg, course=(1.2, 1.8), length=(1.2, 2.4), d=0.3, seed=seed, rough=0.12)
    if style == "parged":
        return SK.scored_stucco(reg, course=2.0, block=3.4, d=0.25)
    if style == "block":
        return ashlar(reg, course=(1.6, 1.6), length=(3.2, 3.2), d=0.3, seed=seed, rough=0.1)
    if style == "coursed":
        return ashlar(reg, course=(1.2, 1.4), length=(2.0, 3.4), d=0.3, seed=seed, rough=0.08)
    if style == "banded":                # smooth courses of two heights in turn, joints on the layer grid
        b = reg.bounds()
        cells, v, j = [], b[1], 0
        while v < b[3]:
            ch = 2.0 if j % 2 == 0 else 1.2
            cells.append(rect(b[0] - 1, v + 0.2, b[2] + 1, v + ch - 0.2))
            v += ch
            j += 1
        return M.extrude(cs_union(cells) ^ reg, 0.35)
    if style in ("coquina", "pebble", "drafted", "tuckpoint", "diamond", "riverstone", "ledgestone"):
        from .trimwork import foundation_skin
        return foundation_skin(style, reg, seed=seed)
    return brick(reg, bl=2.0, d=0.2)


def porch_floor(poly_pts, outer_edges, H=14.0, floor_t=1.6, pitch=1.8, slot=SLOT, depth=0.4, border=1.6,
                along=None):
    """Tongue-and-groove porch floor as its own part: boards run ``along`` (a unit plan
    vector; default perpendicular to the longest yard edge, as porch boards run away from
    the house), a border board frames the yard edges, and a rounded nosing overhangs them.
    Boards are slots on the top face, which prints on the bed (upside down)."""
    pts = ccw(poly_pts)
    base = poly(pts)
    floor = slab(base, H - floor_t, H)
    edges = [(i, Facade(pts[i], pts[(i + 1) % len(pts)], 0.0)) for i in outer_edges]
    if along is None:
        f_long = max(edges, key=lambda e: e[1].L)[1]
        along = -f_long.n
    along = np.asarray(along, float) / np.linalg.norm(along)
    ang = np.degrees(np.arctan2(along[1], along[0]))
    # field of boards inside the border, grooves every pitch across ``along``
    b = base.bounds()
    R = np.hypot(b[2] - b[0], b[3] - b[1]) + 10
    cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
    grooves = cs_union([rect(k - slot / 2, -R, k + slot / 2, R) for k in np.arange(-R, R, pitch)])
    grooves = grooves.rotate(ang - 90).translate((cx, cy))
    inner = base
    for i, f in edges:
        strip = poly([tuple(f.p0 + f.u * -50 + f.n * 0.01), tuple(f.p1 + f.u * 50 + f.n * 0.01),
                      tuple(f.p1 + f.u * 50 - f.n * border), tuple(f.p0 + f.u * -50 - f.n * border)])
        inner = inner - strip
    cut = (grooves ^ inner)
    # the joint between the border boards and the field
    for i, f in edges:
        seam = poly([tuple(f.p0 + f.u * -50 - f.n * (border - slot)), tuple(f.p1 + f.u * 50 - f.n * (border - slot)),
                     tuple(f.p1 + f.u * 50 - f.n * border), tuple(f.p0 + f.u * -50 - f.n * border)])
        cut = cut + (seam ^ offset(base, -0.3))
    floor = floor - slab(cut, H - depth, H + 1)
    for i, f in edges:   # nosing
        floor = floor + f.place(box([-0.3, H - 0.6, -0.2], [f.L + 0.3, H, 0.35]))
    return floor


ROOF_EDGES = ("dentil", "modillion", "fillet", "cove", "drop", "sticks", "button", "reeded", "plain", "scallop",
              "beadreel", "notched", "lozenge", "billet", "cable", "arcading", "sawtooth")


def porch_roof(poly_pts, outer_path, z0, th=2.4, fascia=3.2, over=1.4, dent=True, roof_cs=None, edge="dentil"):
    """Flat porch roof: deck slab plus a moulded fascia along the yard edges.

    outer_path = open polyline along the yard edges (CCW order, yard on the right).
    Prints upside down, so every ornament on the fascia hangs from the crown (stands on it
    in print) or is a groove, and every flat face is a multiple of 0.2 from z0. ``edge``, one
    per building: dentil, modillion (blocks with bevelled feet), fillet (two raised bands),
    cove (a concave crown, no ornament), drop (Gothic points), sticks (Stick battens),
    button (round bosses), reeded (grooves cut along the fascia), scallop (a valance of
    half-round scallops), beadreel, notched (V notches cut up the fascia), lozenge (a band of
    raised lozenges), billet (square billets, alternate ones longer), plain."""
    if not dent:
        edge = "plain"
    top = z0 + fascia + th - 0.4
    deck = slab(roof_cs if roof_cs is not None else poly(ccw(poly_pts)), top - th, top)
    seat = -(over + 4.0)   # inner edge: wide enough to sit on the post beams
    zc = z0 + fascia                       # the crown's foot
    face = [(0.0, z0)]
    if edge == "fillet":                   # raised bands, their tops bevelled 45 degrees (undersides in print)
        for zb in (z0 + 0.6, z0 + 1.6):
            face += [(0.0, zb), (0.4, zb), (0.4, zb + 0.2), (0.0, zb + 0.6)]
    elif edge == "reeded":                 # grooves 0.3 deep, two layers tall
        for zb in (z0 + 0.6, z0 + 1.2, z0 + 1.8):
            face += [(0.0, zb), (-0.3, zb), (-0.3, zb + 0.4), (0.0, zb + 0.4)]
    if edge == "cove":
        face += [(0.0, zc - 1.2)] + [(1.1 - 1.1 * math.cos(t), zc - 1.2 + 1.2 * math.sin(t))
                                     for t in np.linspace(0.15, math.pi / 2, 7)]
    else:
        face += [(0.0, zc - 0.6), (0.35, zc - 0.4), (over - 0.3, zc)]
    prof = [(seat, z0)] + face + [(over, zc + 0.3), (over, top), (seat, top)]
    parts = [deck, sweep_run(outer_path, prof)]
    P = np.asarray(outer_path, float)
    cuts = []
    for a, b in zip(P[:-1], P[1:]):
        f = Facade(a, b, 0.0)
        L = f.L
        if edge == "dentil":
            # dentils run up into the crown moulding so, upside down, they stand on it
            parts.append(f.place(dentils(0.6, L - 0.6, zc - 1.2, 1.0, 0.0, 0.7)))
        elif edge == "modillion":
            n = max(1, int((L - 1.6) / 3.0))
            for k in range(n + 1):
                u = 0.8 + (L - 1.6) * k / max(n, 1)
                parts.append(f.place(M.hull_points([(u + du, z, d) for du in (-0.5, 0.5) for z, d in
                                                    ((z0 + 1.2, 0.0), (z0 + 1.2, 0.5), (z0 + 1.6, 0.9), (zc, 0.9), (zc, 0.0))])))
        elif edge == "drop":
            n = max(1, int((L - 1.2) / 2.0))
            cs = cs_union([poly([(u - 0.55, zc - 0.2), (u + 0.55, zc - 0.2), (u + 0.55, zc - 0.7), (u, zc - 1.7),
                                 (u - 0.55, zc - 0.7)]) for u in (0.6 + (L - 1.2) * (k + 0.5) / n for k in range(n))])
            parts.append(f.place(ext(cs, 0.0, 0.7)))
        elif edge == "sticks":
            n = max(1, int((L - 1.2) / 2.2))
            cs = cs_union([rect(u - 0.3, z0 + 0.4, u + 0.3, zc - 0.2) for u in (0.6 + (L - 1.2) * (k + 0.5) / n
                                                                              for k in range(n))])
            parts.append(f.place(ext(cs, 0.0, 0.5)))
        elif edge == "beadreel":           # a bead-and-reel moulding along the fascia
            n = max(1, int((L - 1.2) / 1.2))
            cs = []
            for k in range(n):
                u = 0.6 + (L - 1.2) * (k + 0.5) / n
                cs.append(circle((u, zc - 1.0), 0.42, 16) if k % 2 == 0 else rect(u - 0.45, zc - 1.2, u + 0.45, zc - 0.8))
            parts.append(f.place(ext(cs_union(cs) + rect(0.3, zc - 1.2, L - 0.3, zc - 0.8), 0.0, 0.5)))
        elif edge == "scallop":            # a valance of half-round scallops hung under the crown
            n = max(1, int((L - 1.2) / 1.5))
            cs = cs_union([circle((u, zc - 0.2), 0.72, 20) for u in (0.6 + (L - 1.2) * (k + 0.5) / n for k in range(n))])
            cs = (cs + rect(0.3, zc - 0.6, L - 0.3, zc)) ^ rect(0.0, zc - 1.2, L, zc)
            parts.append(f.place(ext(cs, 0.0, 0.6)))
        elif edge == "billet":             # short square billets in a row under the crown, alternate ones set lower
            n = max(1, int((L - 1.2) / 1.2))
            cs = cs_union([rect(u - 0.4, zc - (1.2 if k % 2 else 0.8), u + 0.4, zc)
                           for k, u in enumerate(0.6 + (L - 1.2) * (k + 0.5) / n for k in range(n))])
            parts.append(f.place(ext(cs, 0.0, 0.5)))
        elif edge == "sawtooth":           # a row of sawn triangular teeth hung under the crown
            n = max(1, int((L - 1.2) / 1.2))
            cs = cs_union([poly([(u - 0.6, zc - 0.4), (u + 0.6, zc - 0.4), (u, zc - 1.4)])
                           for u in (0.6 + (L - 1.2) * (k + 0.5) / n for k in range(n))]) + rect(0.3, zc - 0.6, L - 0.3, zc)
            parts.append(f.place(ext(cs, 0.0, 0.5)))
        elif edge == "arcading":           # a row of little round arches on colonnettes along the fascia
            n = max(1, int((L - 1.6) / 1.6))
            p_ = (L - 1.6) / n
            cs = []
            for k in range(n + 1):
                u = 0.8 + p_ * k
                cs.append(rect(u - 0.3, zc - 1.6, u + 0.3, zc - 0.2))
            for k in range(n):
                u = 0.8 + p_ * (k + 0.5)
                r_ = p_ / 2
                cs.append((circle((u, zc - 1.0), r_ + 0.3, 20) - circle((u, zc - 1.0), max(0.2, r_ - 0.3), 20))
                          ^ rect(u - p_, zc - 1.0, u + p_, zc - 0.2))
            parts.append(f.place(ext(cs_union(cs) + rect(0.3, zc - 0.6, L - 0.3, zc - 0.2), 0.0, 0.5)))
        elif edge == "cable":              # a cable (rope) moulding: slanted strands in a row along the fascia
            n = max(1, int((L - 1.6) / 1.1))
            cs = cs_union([poly([(u - 0.5, zc - 1.2), (u + 0.1, zc - 1.2), (u + 0.5, zc - 0.4), (u - 0.1, zc - 0.4)])
                           for u in (0.8 + (L - 1.6) * (k + 0.5) / n for k in range(n))])
            parts.append(f.place(ext(cs, 0.0, 0.5) + ext(rect(0.3, zc - 1.2, L - 0.3, zc - 0.4), 0.0, 0.2)))
        elif edge == "lozenge":            # a band of raised lozenges along the fascia, hung from the crown
            n = max(1, int((L - 1.2) / 2.4))
            cs = cs_union([poly([(u - 1.0, zc - 1.0), (u, zc - 1.6), (u + 1.0, zc - 1.0), (u, zc - 0.4)])
                           for u in (0.6 + (L - 1.2) * (k + 0.5) / n for k in range(n))]) + rect(0.3, zc - 0.6, L - 0.3, zc)
            parts.append(f.place(ext(cs, 0.0, 0.5)))
        elif edge == "notched":            # Stick style: V notches cut up the fascia every 2 mm
            n = max(1, int((L - 1.2) / 2.0))
            for k in range(n):
                u = 0.6 + (L - 1.2) * (k + 0.5) / n
                cuts.append(f.place(M.hull_points([(u + du, z, d) for z in (z0 - 0.1, zc - 0.8)
                                                   for du, d in ((-0.45, 0.01), (0.45, 0.01), (0.0, -0.4))])))
        elif edge == "button":
            n = max(1, int((L - 1.2) / 1.6))
            cs = cs_union([circle((u, zc - 0.65), 0.45, 16) for u in (0.6 + (L - 1.2) * (k + 0.5) / n for k in range(n))])
            parts.append(f.place(ext(cs, 0.0, 0.6)))
    return union(parts) - union(cuts) if cuts else union(parts)


def steps(width, rise_total, n, tread=2.6, cheek=1.8):
    """Stair block: n risers up to rise_total, cheek walls each side. Local: u across,
    w out from the porch edge (stairs descend toward +w), v up."""
    r = rise_total / n
    parts = []
    for k in range(n):
        top = round((rise_total - k * r) / 0.2) * 0.2          # tread tops on the 0.2 mm layer grid
        parts.append(box([-width / 2, 0, 0], [width / 2, top, (k + 1) * tread]))
    for s in (-1, 1):
        u0 = s * width / 2
        parts.append(box([min(u0, u0 + s * cheek), 0, 0], [max(u0, u0 + s * cheek), rise_total + 0.8, n * tread + 0.4]))
        parts.append(box([min(u0, u0 + s * cheek) - 0.2, rise_total + 0.4, -0.0],
                         [max(u0, u0 + s * cheek) + 0.2, rise_total + 1.2, n * tread + 0.6]))
    return union(parts)


# ------------------------------------------------------------------ porch assembly
def porch(poly_pts, runs, H_floor=14.0, post_h=35.5, over=1.4, footprint_keep=None, steps_at=(),
          pier=3.4, pw=2.6, t=2.6, style="arcade", rail=None, boards=None):
    """A complete porch from its plan polygon (CCW) and its yard-facing *runs*.

    runs: list of dict(a=(x,y), b=(x,y), posts=[u,...]) in CCW order, u measured from a.
    steps_at: list of (run_index, u, width).
    rail: dict(h=...) for a baluster railing between the posts (left open at the steps).
    boards: dict for porch_floor() to make the floor its own part (slotted boards), or None.
    Returns dict(deck, floor, panels=[(name, solid_local, A)], roof, steps=[(solid_local, A)])."""
    pts = ccw(poly_pts)
    # deck: outer edges are the polygon edges that coincide with runs
    edges = []
    for i in range(len(pts)):
        a, b = np.array(pts[i]), np.array(pts[(i + 1) % len(pts)])
        for r in runs:
            if np.allclose(a, r["a"], atol=0.05) and np.allclose(b, r["b"], atol=0.05):
                edges.append((i, r))
    piers = {}
    for i, r in edges:
        piers[i] = list(r["posts"])
    outer = [i for i, _ in edges]
    deck = porch_deck(pts, outer, H=H_floor, piers_u=piers, pier=pier, floor=boards is None)
    floor = porch_floor(pts, outer, H=H_floor, **boards) if boards is not None else None
    panels = []
    for k, r in enumerate(runs):
        f = Facade(r["a"], r["b"], H_floor)
        A = f.A.copy()
        A[:, 3] = f.world(0.0, 0.0, -t / 2 - 0.3)
        # a run that starts where the previous one ended leaves the corner to that panel
        s0 = t + 0.45 if k > 0 and np.allclose(runs[k - 1]["b"], r["a"], atol=0.05) else 0.0
        posts = [u - s0 for u in r["posts"] if u - s0 >= pw / 2 - 1e-6]
        rl = None
        if rail:
            rl = dict(rail)
            rl["skip"] = [(u - wd / 2 - s0, u + wd / 2 - s0) for (ri, u, wd) in steps_at if ri == k]
        panel = porch_posts(f.L - s0, post_h, posts, pw=pw, t=t, style=style, rail=rl).translate([s0, 0, 0])
        panels.append((f"run{k}", panel, A))
    roof = _porch_roof(pts, runs, H_floor + post_h, over)
    st = _porch_steps(runs, steps_at, H_floor)
    return dict(deck=deck, floor=floor, panels=panels, roof=roof, steps=st)


def _porch_roof(pts, runs, z0, over, edge="dentil"):
    """Roof over the porch polygon grown by ``over``, with its fascia along the runs."""
    base = poly(pts)
    roof_cs = offset(base, over)
    chain = []
    for k, r in enumerate(runs):
        f = Facade(r["a"], r["b"], 0.0)
        chain.append((np.array(r["a"]) + f.n * over, np.array(r["b"]) + f.n * over))
    # merge consecutive runs into one open polyline (corners meet at the grown offset)
    path = []
    for k, (a, b) in enumerate(chain):
        if k == 0:
            path.append(a)
        else:
            # intersection of previous and current offset lines
            pa, pb = chain[k - 1]
            d1, d2 = pb - pa, b - a
            den = d1[0] * d2[1] - d1[1] * d2[0]
            if abs(den) > 1e-9:
                tpar = ((a[0] - pa[0]) * d2[1] - (a[1] - pa[1]) * d2[0]) / den
                path.append(pa + d1 * tpar)
        if k == len(chain) - 1:
            path.append(b)
    # extend the chain ends a little so they die into the wall cut
    if len(path) >= 2:
        e0 = path[0] - path[1]
        path[0] = path[0] + e0 / np.linalg.norm(e0) * over
        e1 = path[-1] - path[-2]
        path[-1] = path[-1] + e1 / np.linalg.norm(e1) * over
    return porch_roof(None, [tuple(p) for p in path], z0, over=over, roof_cs=roof_cs, edge=edge)


def _porch_steps(runs, steps_at, H_floor):
    st = []
    for (ri, u, wdt) in steps_at:
        r = runs[ri]
        f = Facade(r["a"], r["b"], 0.0)
        A = f.A.copy()
        A[:, 3] = f.world(u, 0.0, 0.45)
        st.append((steps(wdt, H_floor, 4), A))
    return st


# ------------------------------------------------------------------ shutters
def shutter(w, h, t=0.8, stile=0.6, louver=1.0, mid=True):
    """Louvered shutter panel. Local frame: u across (0..w), v up (0..h), back at w = 0.

    Prints face-up (back on the bed). Each louver is a slat one nozzle wide (RIB) standing
    two layers proud of a 0.4 mm back web, with a SLOT between slats, so the slats print as
    separate lines instead of a textured smear. Stiles and rails are full thickness."""
    web = 0.4
    frame_cs = rect(0, 0, w, h) - rect(stile, stile, w - stile, h - stile)
    parts = [ext(frame_cs, 0.0, t)]
    rails = [(h / 2 - stile / 2, h / 2 + stile / 2)] if mid else []
    for v0, v1 in rails:
        parts.append(ext(rect(stile, v0, w - stile, v1), 0.0, t))
    inner = rect(stile, stile, w - stile, h - stile)
    for v0, v1 in rails:
        inner = inner - rect(0, v0, w, v1)
    parts.append(ext(inner, 0.0, web))
    # slats: fit a whole number into each open field, a slot at both ends
    slats = []
    for fld in inner.decompose():
        b = fld.bounds()
        n = max(1, int((b[3] - b[1] - SLOT) / louver))
        pitch = (b[3] - b[1] - SLOT) / n
        for k in range(n):
            v = b[1] + SLOT + k * pitch
            slats.append(rect(b[0] - 0.1, v, b[2] + 0.1, v + min(RIB + 0.05, pitch - SLOT)))
    if slats:
        parts.append(ext(cs_union(slats) ^ inner.offset(0.05), web, t - 0.2))
    return union(parts)


def shutter_panel(w, h, t=0.8, stile=0.6):
    """Raised-panel shutter (Italianate): two panels, each a bevelled field inside the frame."""
    # prints on its back: the field at 0.4 and the panels' bevelled tops at t keep every flat
    # face on the layer grid (0.5 would sit on a slicing plane)
    parts = [ext(rect(0, 0, w, h), 0.0, t - 0.4)]
    mid = h * 0.42
    for v0, v1 in ((stile, mid - stile / 2), (mid + stile / 2, h - stile)):
        if v1 - v0 > 1.5 and w - 2 * stile > 1.2:
            parts.append(chamfer_box(stile + 0.5, v0 + 0.5, w - stile - 0.5, v1 - 0.5, t - 0.41, 0.41, c=0.15))
    frame_cs = rect(0, 0, w, h) - rect(stile, stile, w - stile, h - stile) + rect(0, mid - stile / 2, w, mid + stile / 2)
    parts.append(ext(frame_cs, 0.0, t))
    return union(parts)


def shutter_board(w, h, t=0.8):
    """Farmhouse board shutter: vertical boards with grooves, a Z brace of battens and a
    diamond cut-out near the top."""
    parts = [ext(rect(0, 0, w, h), 0.0, t - 0.2)]            # flat faces on the layer grid
    n = max(2, int(w / 1.2))
    g = cs_union([rect(w * k / n - 0.25, 0.3, w * k / n + 0.25, h - 0.3) for k in range(1, n)])
    parts[0] = parts[0] - ext(g, 0.2, t)
    bat = cs_union([rect(0.2, 1.0, w - 0.2, 1.9), rect(0.2, h - 1.9, w - 0.2, h - 1.0),
                    stroke([(0.6, 1.8), (w - 0.6, h - 1.8)], 0.8)])
    parts.append(ext(bat, t - 0.21, t + 0.2))
    c = (w / 2, h - 3.2)
    dia = poly([(c[0], c[1] + 0.8), (c[0] + 0.55, c[1]), (c[0], c[1] - 0.8), (c[0] - 0.55, c[1])])
    return union(parts) - ext(dia, -1, t + 1)


def shutters_for(opening_w, opening_h, casing=1.1, gap=0.6, t=0.8, h=None, style="louver"):
    """A pair of shutters (left, right) framing an opening, in insert-local coordinates
    (u centred on the opening, v from the opening bottom, mounted at w = stand_off).
    The default gap clears the casing's ears (0.5 past the casing at the head)."""
    sw = opening_w / 2
    hh = opening_h if h is None else h
    mk = {"louver": shutter, "panel": shutter_panel, "board": shutter_board}[style]
    left = mk(sw, hh, t=t).translate([-(opening_w / 2 + casing + gap + sw), 0, 0])
    right = mk(sw, hh, t=t).translate([opening_w / 2 + casing + gap, 0, 0])
    return left, right


# ------------------------------------------------------------------ turned porch
# Posts and railings print standing up, so they are round all the way round with one finish;
# the arcade (beam, sawn-work spandrels, drops) prints on its top edge, so front and back
# match too. Nothing here is a flat panel with a glossy bed face on one side.

def _clamp_45(prof):
    """Make a revolved (r, z) profile printable upright: wherever r grows going up, it may
    grow no faster than z (45 degrees); the z of such points is pushed up as needed. The
    first segment (out from the axis) is the flat bottom, which stands on its support."""
    out = [prof[0], prof[1]]
    for r, z in prof[2:]:
        r0, z0 = out[-1]
        if r > r0 and r - r0 > z - z0:
            z = z0 + (r - r0)
        out.append((r, max(z, z0)))
    return out


COLLAR_PAD = 0.2       # the collar band runs past the hand rail (edges level with its faces upset PrusaSlicer)


def turned_post(h, plinth=3.2, abacus=3.0, seg=36, slot=(1.2, 1.0), collar=None):
    """Victorian turned porch post, printed upright, floor at z=0, top of the abacus at h.

    Square plinth, torus base, tapered lower shaft, a ringed collar, a vase with a belly,
    a necked ring, the upper shaft, and a bell capital flaring at 45 degrees into a square
    abacus. Never thinner than 1.9 mm. A slot across the abacus takes the arcade's tab.
    ``collar``: height of a railing's hand rail top above the post's foot; the ringed collar
    is then placed so the hand rail runs into it (a solid joint when post and railing print
    as one piece) instead of meeting the thin shaft."""
    ph, ah = 1.2, 1.0
    z0, z1 = ph, h - ah - 1.4                 # turned zone (the capital bell sits above z1)
    L = z1 - z0

    def Z(t):
        return z0 + t * L
    if collar is None:
        c0, c1, c2 = Z(0.20), Z(0.23), Z(0.30)
    else:                                   # the ring's straight band spans the hand rail
        c0, c1 = collar - 1.3 - COLLAR_PAD, collar + COLLAR_PAD
        c2 = max(Z(0.30), c1 + 0.55)
    prof = [(0.0, z0 - 0.01), (1.5, z0 - 0.01), (1.5, z0 + 0.35), (1.25, z0 + 0.7), (1.15, Z(0.04)),
            (1.05, c0), (1.35, c0 + 0.3), (1.35, c1), (1.0, c1 + 0.35),
            (1.0, c2), (1.25, Z(0.36)), (1.42, Z(0.45)), (1.25, Z(0.56)), (0.95, Z(0.64)),
            (1.3, Z(0.64) + 0.35), (1.3, Z(0.67)), (0.95, Z(0.67) + 0.35), (1.05, Z(0.76)), (1.0, z1),
            (1.1, z1 + 0.1), (1.45, z1 + 0.45), (1.45, z1 + 0.8), (0.0, z1 + 0.8)]
    prof = _clamp_45(prof[:-1]) + [(0.0, prof[-2][1])]
    body = M.revolve(poly([(r, z) for r, z in prof]), seg)
    body = body + box([-plinth / 2, -plinth / 2, 0.0], [plinth / 2, plinth / 2, ph])
    # bell -> square abacus at 45 degrees (hull of the bell's top ring and the abacus)
    zb = z1 + 0.8
    ring = [(1.45 * math.cos(a), 1.45 * math.sin(a), zb - 0.01) for a in np.linspace(0, 2 * math.pi, 24, endpoint=False)]
    sq = abacus / 2
    rise = max(0.2, (sq * math.sqrt(2) - 1.45))
    corners = [(x, y, zb + rise) for x in (-sq, sq) for y in (-sq, sq)]
    body = body + M.hull_points(ring + corners)
    body = body + box([-sq, -sq, zb + rise - 0.01], [sq, sq, h])
    if slot:
        body = body - box([-slot[0] / 2, -sq - 1, h - slot[1]], [slot[0] / 2, sq + 1, h + 1])
    return body


def baluster(h, rmax=0.55, rmin=0.36, seg=20):
    """Turned baluster (revolved), printed upright; z = 0..h."""
    t = [(0.0, 0.5), (0.1, 0.5), (0.14, 0.38), (0.22, 0.4), (0.36, 0.52), (0.46, 0.55), (0.58, 0.46),
         (0.72, 0.36), (0.78, 0.36), (0.82, 0.46), (0.86, 0.38), (0.9, 0.5), (1.0, 0.5)]
    prof = [(max(rmin, min(rmax, r)), f * h) for f, r in t]
    prof = _clamp_45([(0.0, 0.0)] + prof)
    prof.append((0.0, prof[-1][1]))
    return M.revolve(poly(prof), seg)


def railing_section(L, h=8.6, pitch=1.8, rail_w=1.4, foot=0.8, sink=0.0, foot_pitch=8.0, foot_margin=0.5,
                    stiles=True, style="turned"):
    """Baluster railing between two posts, printed upright. Local frame: u along 0..L, v up
    from the porch floor (= print z), w across, centred. Feet carry the bottom rail
    ``foot`` above the floor; turned balusters; a hand rail with a rounded top.
    ``sink``: the feet run that far below the floor (into sockets), level with the posts'
    plinths when the railing is printed in one piece with its posts. There the posts are the
    stiles (``stiles=False``) and ``foot_margin`` keeps the end feet clear of the plinths: a
    foot half over a plinth leaves a sliver PrusaSlicer fails on ("negative spacing")."""
    parts = []
    nf = max(2, int((L - 2 * foot_margin + 1.0) / foot_pitch) + 1)
    for j in range(nf):
        u = foot_margin + (L - 2 * foot_margin) * j / (nf - 1)
        parts.append(box([u - 0.5, -0.6, -sink], [u + 0.5, 0.6, foot + 0.01]))
    parts.append(box([0.0, -0.6, foot], [L, 0.6, foot + 0.8]))                        # bottom rail
    vb, vt = foot + 0.8, h - 1.0                   # every flat face on the 0.2 mm layer grid
    for u in ((0.0, L - 0.7) if stiles else ()):                                     # end stiles
        parts.append(box([u, -0.5, foot], [u + 0.7, 0.5, vt + 0.01]))
    from . import porchwork as PW
    if style in ("chippendale", "x", "pierced", "sawn", "lace", "ladder", "hearts", "paddle"):
        parts.append(PW.fill_flat(style, L, vb - 0.01, vt + 0.01))
    else:
        mk, pt = {"turned": (baluster, pitch), "vase": (PW.baluster_vase, 2.4), "urn": (PW.baluster_urn, 2.4),
                  "spindle": (PW.spindle, 1.25), "bead": (PW.baluster_bead, 1.9), "twist": (PW.baluster_twist, 1.7),
                  "ringed": (PW.baluster_ringed, 1.6), "hourglass": (PW.baluster_hourglass, 1.7)}[style]
        n = max(1, int(round((L - 1.4) / pt)))
        for j in range(n):
            u = 0.7 + (L - 1.4) * (j + 0.5) / n
            parts.append(mk(vt - vb + 0.02).translate([u, 0.0, vb - 0.01]))
    # hand rail: square under-rail, rounded cap (in (w, v), extruded along u)
    cap = poly([(-rail_w / 2, vt), (rail_w / 2, vt), (rail_w / 2, h - 0.4), (rail_w / 2 - 0.2, h - 0.2),
                (rail_w / 2 - 0.4, h), (-rail_w / 2 + 0.4, h), (-rail_w / 2 + 0.2, h - 0.2), (-rail_w / 2, h - 0.4)])
    rail = M.extrude(cap, L).transform(np.array([[0, 0, 1.0, 0], [1.0, 0, 0, 0], [0, 1.0, 0, 0]]))
    parts.append(rail)
    return union(parts)


def _largest_hole(region, near, min_r=0.45, max_r=1.6):
    """Biggest circle that fits inside ``region`` (already shrunk by the wood to keep),
    centred as close as possible to ``near``. Returns (centre, r) or None."""
    best = None
    r = max_r
    while r >= min_r - 1e-9:
        core = region.offset(-r, JoinType.Round)
        if not core.is_empty():
            pts = [p for poly_ in core.to_polygons() for p in poly_]
            c = min(pts, key=lambda p: (p[0] - near[0]) ** 2 + (p[1] - near[1]) ** 2)
            best = ((float(c[0]), float(c[1])), r)
            break
        r -= 0.1
    return best


def _spandrel_cs(u0, u1, v_bot, v_top, band=0.8, wood=0.7):
    """Sawn-work spandrel between two posts (u0..u1) under a beam at v_top, springing at
    v_bot: an elliptical arch with a band, then in each half the biggest roundel that fits
    by the post and a curved piercing following the arch toward the crown, with a turned
    drop hanging from the crown. Every bar of wood is at least ``wood`` wide. (u, v)."""
    mid, half = (u0 + u1) / 2, (u1 - u0) / 2
    rise = (v_top - v_bot) - 0.8          # crown 1.6 under the beam: on the layer grid when printed

    def ell(a, b, seg=72):
        return poly([(mid + a * math.cos(t), v_bot + b * math.sin(t)) for t in np.linspace(0, math.pi, seg)] +
                    [(mid - a, v_bot - 5), (mid + a, v_bot - 5)])
    region = rect(u0, v_bot, u1, v_top + 0.05)
    solid = region - ell(half - band, rise - band)
    free = (rect(u0, v_bot, u1, v_top) - ell(half, rise)).offset(-wood, JoinType.Round)
    holes = []
    for s in (-1, 1):
        side = free ^ (rect(mid, v_bot - 1, u1 + 1, v_top + 1) if s > 0 else rect(u0 - 1, v_bot - 1, mid, v_top + 1))
        if side.is_empty():
            continue
        hole = _largest_hole(side, (mid + s * half, v_top))
        if hole is None:
            continue
        c = circle(hole[0], hole[1], 28)
        holes.append(c)
        # the rest of this half, clear of the roundel: a curved piercing along the arch,
        # kept only where it is at least a nozzle-and-a-half wide
        rest = side - c.offset(wood, JoinType.Round)
        rest = rest ^ (rect(mid + 0.8, v_bot - 1, hole[0][0], v_top + 1) if s > 0 else
                       rect(hole[0][0], v_bot - 1, mid - 0.8, v_top + 1))
        rest = rest.offset(-0.3, JoinType.Round).offset(0.3, JoinType.Round)
        for piece in rest.decompose():
            if piece.area() > 0.8:
                holes.append(piece)
    if holes:
        solid = solid - cs_union(holes)
    # turned drop under the crown
    cvb = v_bot + rise - band
    drop = cs_union([rect(mid - 0.35, cvb - 1.0, mid + 0.35, cvb + 0.1), circle((mid, cvb - 1.4), 0.6, 20),
                     poly([(mid - 0.4, cvb - 1.8), (mid + 0.4, cvb - 1.8), (mid, cvb - 2.6)])])
    return solid + drop


def _gothic_spandrel_cs(u0, u1, v_bot, v_top, band=0.8, wood=0.7):
    """Gothic bay between two posts: a pointed (two-centred) arch with a band, a trefoil
    pierced in each spandrel where it fits, and a small pendant at the apex. (u, v)."""
    mid, half = (u0 + u1) / 2, (u1 - u0) / 2
    rise = (v_top - v_bot) - 0.8

    def pointed(hw, r_scale=1.25, seg=36):
        # two arcs of radius R springing at v_bot from mid +- hw, meeting at the apex
        R = hw * 2 * r_scale
        cL, cR = mid + hw - R, mid - hw + R
        top = v_bot + math.sqrt(max(R * R - (R - hw) ** 2, 0.0))
        k = min(1.0, rise / max(top - v_bot, 1e-6))
        pts = [(mid - hw, v_bot - 5)]
        for t in np.linspace(0, 1, seg):
            x = mid - hw + t * hw
            y = v_bot + k * math.sqrt(max(R * R - (x - cR) ** 2, 0.0))
            pts.append((x, y))
        for t in np.linspace(1, 0, seg):
            x = mid + hw - t * hw
            y = v_bot + k * math.sqrt(max(R * R - (x - cL) ** 2, 0.0))
            pts.append((x, y))
        pts.append((mid + hw, v_bot - 5))
        return poly(pts)
    region = rect(u0, v_bot, u1, v_top + 0.05)
    solid = region - pointed(half - band)
    free = (rect(u0, v_bot, u1, v_top) - pointed(half)).offset(-wood, JoinType.Round)
    holes = []
    for sgn in (-1, 1):
        side = free ^ (rect(mid, v_bot - 1, u1 + 1, v_top + 1) if sgn > 0 else rect(u0 - 1, v_bot - 1, mid, v_top + 1))
        if side.is_empty():
            continue
        hole = _largest_hole(side, (mid + sgn * half, v_top), min_r=0.9, max_r=2.2)
        if hole is None:
            continue
        (cx, cy), r = hole
        rr = r * 0.5
        tre = cs_union([circle((cx + rr * math.cos(a), cy + rr * math.sin(a)), r * 0.52, 20)
                        for a in (math.pi / 2, math.pi / 2 + 2.094, math.pi / 2 + 4.189)])
        tre = tre ^ circle((cx, cy), r, 32)
        tre = tre.offset(-0.26, JoinType.Round).offset(0.26, JoinType.Round)
        if not tre.is_empty():
            holes.append(tre)
    if holes:
        solid = solid - cs_union(holes)
    apex = v_bot + rise                                   # the opening's point: hang the drop from it
    drop = cs_union([rect(mid - 0.35, apex - 1.0, mid + 0.35, apex + 0.3),
                     poly([(mid - 0.5, apex - 1.0), (mid + 0.5, apex - 1.0), (mid, apex - 2.2)])])
    return solid + drop


def _braced_spandrel_cs(u0, u1, v_bot, v_top, wood=0.8):
    """Stick-style bay between two posts: a frieze of short sticks between the beam and a
    rail below it, and a straight diagonal knee brace from each post up to the rail. (u, v)"""
    rail0, rail1 = v_top - 2.0, v_top - 1.2          # printed upside down from the beam: faces on the grid
    parts = [rect(u0, rail0, u1, rail1)]
    n = max(2, int((u1 - u0) / 1.4))
    for k in range(n):
        u = u0 + (u1 - u0) * (k + 0.5) / n
        parts.append(rect(u - 0.28, rail1 - 0.05, u + 0.28, v_top + 0.05))
    L = min(4.2, (u1 - u0) * 0.3)
    for sg, ue in ((1, u0), (-1, u1)):
        parts.append(stroke([(ue + sg * 0.35, rail0 - L * 0.8), (ue + sg * L, rail0 + 0.3)], wood))
        foot = v_top - round((v_top - (rail0 - L * 0.8 - 0.4)) / 0.2) * 0.2
        parts.append(rect(min(ue, ue + sg * 0.9), foot, max(ue, ue + sg * 0.9), rail1))
    return cs_union(parts) ^ rect(u0, v_bot, u1, v_top + 0.05)


def porch_arcade(u_start, u_end, posts_u, H, beam=2.2, tb=2.2, ts=1.0, drop=5.0, cap=3.0, style="sawn"):
    """Upper porch work for one run: beam with moulded edges, a square block with a rosette
    over every post, a tab into each post's slot, and a sawn-work spandrel (arch, roundels,
    teardrops, crown drop) in every bay. Local: u along, v up from the floor, w out (front at
    +tb/2). Prints on its top edge, upside down, so both faces print alike."""
    vb = H - beam
    parts = [box([u_start, vb, -tb / 2], [u_end, H, tb / 2])]
    parts.append(box([u_start, vb, tb / 2 - 0.01], [u_end, vb + 0.4, tb / 2 + 0.3]))        # bead
    parts.append(box([u_start, H - 0.4, tb / 2 - 0.01], [u_end, H, tb / 2 + 0.3]))          # fillet
    for u in [u for u in posts_u if u_start + 1.0 <= u <= u_end - 1.0]:
        parts.append(box([u - 0.5, vb - 0.8, -0.5], [u + 0.5, vb + 0.01, 0.5]))              # tab
        blk = chamfer_box(u - 1.2, vb + 0.55, u + 1.2, H - 0.55, tb / 2 - 0.01, 0.45, c=0.25)
        ros = ext(circle((u, (vb + H) / 2), 0.42, 16), tb / 2 + 0.4, tb / 2 + 0.7)
        parts.append(blk + ros)
    for a, b in zip(posts_u[:-1], posts_u[1:]):
        u0, u1 = a + cap / 2 + 0.1, b - cap / 2 - 0.1
        if u1 - u0 < 6.0:
            continue
        from . import porchwork as PW
        from . import lace as LC
        fn = {"gothic": _gothic_spandrel_cs, "braced": _braced_spandrel_cs, "sawn": _spandrel_cs,
              "lace": LC.lace_spandrel_cs}.get(style) or PW.FRIEZES[style]
        sp = fn(u0, u1, vb - drop, vb)
        body = ext(sp, tb / 2 - ts, tb / 2)
        rim = ext(sp.offset(-0.55, JoinType.Round).offset(0.05, JoinType.Round), tb / 2 - 0.3, tb / 2 + 1)
        parts.append(body - rim)
    return union(parts)


# (x, y, z) z-up part -> facade local (u, v, w) = (x, z, -y)
Z_UP_TO_FACADE = np.array([[1.0, 0, 0, 0], [0, 0, 1.0, 0], [0, -1.0, 0, 0]])
# print transform for arcades: local (u, v, w) -> (u, w, -v): upside down on the beam's top edge
ARCADE_PRINT = np.array([[1.0, 0, 0, 0], [0, 0, 1.0, 0], [0, -1.0, 0, 0]])


def porch_turned(poly_pts, runs, H_floor, post_h, steps_at=(), over=1.4, inset=1.6, rail_h=8.6,
                 boards=None, beam=2.2, pier=3.4, joined=False, ledger_off=0.0, arcade="sawn", post="turned",
                 rail="turned", skirt="lattice", pier_tex="brick", roof_edge="dentil", planks=None, drop=5.0):
    """Porch with turned posts, upright railings and edge-printed arcades.
    ``planks`` = dict for porch_planks(): the floor is planks printed with the deck (one part,
    upside down, one filament change at the planks' thickness) instead of a separate floor.
    ``arcade``: "sawn" (elliptical arches with roundels), "gothic" (pointed arches, trefoils),
    "lace" (elliptical arches in pierced lace with scrolls, see lace.py), or a frieze name;
    ``drop``: how far the spandrels hang below the beam.

    runs: list of dict(a, b, posts=[u, ...]) in CCW order (u from a along the yard edge);
    posts stand ``inset`` inside the yard edge, and a post at a corner is shared by the two
    runs (give it at u = L - inset on one run and u = inset on the next). The longer run's
    arcade covers a shared corner post; the shorter one stops against it. At an inside
    (reflex) corner the shared post stands past the ends, at u = L + c and u = -c; a run may
    then give ``piers=[u, ...]`` to keep its skirt piers on the yard edge.
    Returns dict(deck, floor, posts=[world solid], rails=[world solid], arcades=[(world solid,
    A)], roof, steps=[(local, A)], sockets=[(x, y)]).
    ``joined``: the posts and railings of each connected chain of runs are one piece
    (``frames``), printed upright on the plinths and the railing feet, which drop into
    sockets in the floor; ``posts`` and ``rails`` are then empty."""
    pts = ccw(poly_pts)
    edges = []
    for i in range(len(pts)):
        a, b = np.array(pts[i]), np.array(pts[(i + 1) % len(pts)])
        for r in runs:
            if np.allclose(a, r["a"], atol=0.05) and np.allclose(b, r["b"], atol=0.05):
                edges.append((i, r))
    outer = [i for i, _ in edges]
    piers = {i: list(r.get("piers", r["posts"])) for i, r in edges}
    if planks is not None:
        planks = dict(planks)
        if planks.get("along") is None:
            fl = max((Facade(pts[i], pts[(i + 1) % len(pts)], 0.0) for i in outer), key=lambda f: f.L)
            planks["along"] = -fl.n
        deck = porch_deck(pts, outer, H=H_floor, piers_u=piers, pier=pier, floor=False, ledger_off=ledger_off,
                          infill=skirt, pier_tex=pier_tex, planks=planks)
        deck = deck + porch_planks(pts, outer, H=H_floor, **planks)
        boards = None
    else:
        deck = porch_deck(pts, outer, H=H_floor, piers_u=piers, pier=pier, floor=boards is None,
                          ledger_off=ledger_off, infill=skirt, pier_tex=pier_tex)
    # post positions (deduplicated at shared corners)
    where = []
    for r in runs:
        f = Facade(r["a"], r["b"], 0.0)
        for u in r["posts"]:
            p = f.p0 + f.u * u - f.n * inset
            if not any(np.allclose(p, q, atol=0.05) for q in where):
                where.append(p)
    ph = post_h - beam + 0.4                    # plinth sits 0.4 down in a floor socket
    from . import porchwork as PW
    post_style = post
    post = PW.POSTS[post_style](ph, collar=(rail_h + 0.4) if joined else None)
    posts = [post.translate([p[0], p[1], H_floor - 0.4]) for p in where]
    floor = None
    if boards is not None:
        floor = porch_floor(pts, outer, H=H_floor, **boards)
        if not joined:
            socks = union([box([p[0] - 1.68, p[1] - 1.68, H_floor - 0.4], [p[0] + 1.68, p[1] + 1.68, H_floor + 1])
                           for p in where])
            floor = floor - socks
    # railings and arcades per run
    rails, arcades, stops = [], [], []
    run_rails = {}
    lens = [Facade(r["a"], r["b"]).L for r in runs]
    for k, r in enumerate(runs):
        f = Facade(r["a"], r["b"], 0.0)
        us = sorted(r["posts"])
        A = f.A.copy()
        A[:, 3] = np.r_[f.p0 - f.n * inset, H_floor]
        skip = [(u - w / 2, u + w / 2) for (ri, u, w) in steps_at if ri == k]
        # the square plinths stay square to the plan: on a slanted run they reach further;
        # a joined railing runs into the round shafts instead
        clr = 0.8 if joined else max(1.75, 1.6 * (abs(f.u[0]) + abs(f.u[1])) + 0.15)
        for a_, b_ in zip(us[:-1], us[1:]):
            if any(not (b_ <= s0 or a_ >= s1) for s0, s1 in skip):
                continue
            L = (b_ - a_) - 2 * clr
            if L < 3.0:
                continue
            # railing_section is built z-up; facade frames are (u, v up, w out)
            if joined:        # end feet clear of the square plinths (they reach further on a slant)
                ext_ = 1.6 * (abs(f.u[0]) + abs(f.u[1]))
                rs = railing_section(L, rail_h, sink=0.4, foot_margin=ext_ + 0.8 - clr, stiles=False, style=rail)
            else:
                rs = railing_section(L, rail_h, style=rail)
            rails.append(rs.translate([a_ + clr, 0, 0]).transform(Z_UP_TO_FACADE).transform(A))
            run_rails.setdefault(k, []).append(rails[-1])
        if len(us) < 2:                         # a lone corner post: its longer neighbour's arcade covers it
            arcades.append((None, A))
            continue
        # arcade ends: stop against a corner post covered by a longer neighbour's arcade
        u0, u1 = us[0] - 1.5, us[-1] + 1.5
        prev, nxt = runs[k - 1] if k > 0 else None, runs[k + 1] if k + 1 < len(runs) else None
        if prev is not None and np.allclose(prev["b"], r["a"], atol=0.05) and lens[k - 1] > lens[k] - 1e-6:
            # (on a tie, e.g. the equal facets of a curved run, the later run stops)
            u0 = us[0] + beam / 2 + 0.1
            stops.append((k, k - 1, us[0]))
        if nxt is not None and np.allclose(nxt["a"], r["b"], atol=0.05) and lens[k + 1] > lens[k]:
            u1 = us[-1] - beam / 2 - 0.1
            stops.append((k, k + 1, us[-1]))
        arc = porch_arcade(u0, u1, us, post_h, beam=beam, style=arcade, drop=drop)
        arcades.append((arc.transform(A), A))
    # a stopped end meets the covering beam square only at a right angle: clear it of that
    # beam (on any angle) and of the corner post's square capital below the beam
    for k, j, u in stops:
        arc, A = arcades[k]
        Aj, Lj = arcades[j][1], lens[j]
        beam_j = box([-5.0, -1.0, -1.1 - 0.15], [Lj + 5.0, post_h + 1.0, 1.1 + 0.8]).transform(Aj)
        f = Facade(runs[k]["a"], runs[k]["b"], 0.0)
        p = f.p0 + f.u * u - f.n * inset
        cap = box([p[0] - 1.75, p[1] - 1.75, H_floor - 1.0], [p[0] + 1.75, p[1] + 1.75, H_floor + post_h - beam])
        arcades[k] = (arc - beam_j - cap, A)
    arcades = [(a, A) for a, A in arcades if a is not None]
    roof = _porch_roof(pts, runs, H_floor + post_h, over, edge=roof_edge)
    st = _porch_steps(runs, steps_at, H_floor)
    frames = []
    if joined:
        # chains of runs that meet end to end; each chain's posts and railings are one piece
        chains, cur = [], [0]
        for k in range(1, len(runs)):
            if np.allclose(runs[k - 1]["b"], runs[k]["a"], atol=0.05):
                cur.append(k)
            else:
                chains.append(cur)
                cur = [k]
        chains.append(cur)
        for ch in chains:
            mine = []
            for k in ch:
                f = Facade(runs[k]["a"], runs[k]["b"], 0.0)
                for u in runs[k]["posts"]:
                    p = f.p0 + f.u * u - f.n * inset
                    if not any(np.allclose(p, q, atol=0.05) for q in mine):
                        mine.append(p)
            pieces = [post.translate([p[0], p[1], H_floor - 0.4]) for p in mine]
            pieces += [r for k in ch for r in run_rails.get(k, [])]
            frames += union(pieces).decompose()           # a post with no railing stays its own piece
        if floor is not None or planks is not None:       # sockets for the plinths and the railing feet
            # (sliced at the floor's top too: a post whose base block has a chamfered foot is widest there)
            foot = cs_union([fr.slice(z) for fr in frames for z in (H_floor - 0.2, H_floor - 0.01)])
            sock = slab(foot.offset(0.15, JoinType.Miter, 4.0), H_floor - 0.41, H_floor + 1)
            if floor is not None:
                floor = floor - sock
            else:
                deck = deck - sock
                deck = union([c for c in deck.decompose() if c.volume() > 0.5])
        posts, rails = [], []
    return dict(deck=deck, floor=floor, posts=posts, rails=rails, arcades=arcades, roof=roof, steps=st,
                sockets=[tuple(p) for p in where], frames=frames)


def entry_pediment(w, depth, rise, t=1.0, fan=True):
    """A small gabled pediment for a porch entry, standing on the porch roof over the steps:
    a triangular gable face ``w`` wide with a raised rim and a half-round fan on its base, and
    a gabled roof block ``depth`` deep behind it. Local: u across (centred), v up from the
    porch roof top, w out from the house (the face at w = depth). Prints upright on its base:
    the roof slopes are its top faces."""
    face = poly([(-w / 2, 0.0), (w / 2, 0.0), (0.0, rise)])
    body = M.extrude(face, depth).transform(np.array([[1.0, 0, 0, 0], [0, 1.0, 0, 0], [0, 0, 1.0, 0]]))
    parts = [body]
    rim = face - face.offset(-0.8, JoinType.Miter, 4.0)
    parts.append(ext(rim, depth - 0.01, depth + t))
    if fan:
        r = min(w * 0.28, rise * 0.55)
        half = circle((0.0, 0.8), r, 40) ^ rect(-r - 1, 0.8, r + 1, r + 1)
        rays = cs_union([stroke([(0.0, 0.8), ((r - 0.2) * math.cos(a), 0.8 + (r - 0.2) * math.sin(a))], 0.5)
                         for a in np.linspace(math.pi / 7, 6 * math.pi / 7, 6)])
        ring = half - circle((0.0, 0.8), r - 0.6, 40)
        parts.append(ext((rays ^ half) + ring + rect(-w / 2 + 0.8, 0.0, w / 2 - 0.8, 0.8), depth - 0.01, depth + t * 0.6))
    return union(parts).transform(np.array([[1.0, 0, 0, 0], [0, 0, 1.0, 0], [0, 1.0, 0, 0]]))

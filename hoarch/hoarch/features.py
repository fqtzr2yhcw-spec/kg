"""Dormers, towers, chimneys, porches and steps.

Local frames follow the insert convention where it applies: u along the wall,
v up, w out of the wall. Each builder returns manifolds in its local frame;
the building script places them with a 3x4 frame matrix.
"""
import numpy as np
from manifold3d import JoinType, Manifold as M

from .core import (Facade, box, brick, ccw, circle, cs_union, lattice, miters, offset, poly, rect, slab,
                   sweep_run, union)
from .ornament import chimney_pot, dentils, ext, keystone, spandrel
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
        dress.append(ext(rect(pu - 1.0, H - 1.4, pu + 1.0, H - 0.3), 0.0, 0.75))          # capital
        dress.append(ext(rect(pu - 1.0, 0.0, pu + 1.0, 0.9), 0.0, 0.7))                   # plinth
    arch_band = (circle((0, H), R, 48) - circle((0, H), R - 1.2, 48)) ^ rect(-R, H - 0.3, R, H + R + 1)
    dress.append(ext(arch_band, 0.0, 0.5))
    dress.append(keystone(0.0, H + R - 2.1, 2.05, 1.0, 1.5, 0.0, 0.9))
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
def chimney(w=10.5, dpt=10.5, h=20.5, cap=1.6, pots=2, peg=(5.8, 5.8, 2.0)):
    """Brick chimney standing on a flat deck (z = 0 at the deck), with a corbelled
    cap, pots and a locating peg below."""
    core = box([-w / 2, -dpt / 2, 0], [w / 2, dpt / 2, h - 3 * cap])
    parts = [core]
    for k, grow in enumerate((0.5, 1.0, 0.6)):
        z = h - 3 * cap + k * cap
        parts.append(box([-w / 2 - grow, -dpt / 2 - grow, z], [w / 2 + grow, dpt / 2 + grow, z + cap]))
    # brick texture on the 4 shaft faces
    shaft_h = h - 3 * cap
    fac = [Facade((-w / 2, -dpt / 2), (w / 2, -dpt / 2)), Facade((w / 2, -dpt / 2), (w / 2, dpt / 2)),
           Facade((w / 2, dpt / 2), (-w / 2, dpt / 2)), Facade((-w / 2, dpt / 2), (-w / 2, -dpt / 2))]
    for i, f in enumerate(fac):
        parts.append(f.place(brick(rect(0.1, 0.0, f.L - 0.1, shaft_h), bl=2.1, bh=0.78, mortar=0.16, d=0.2,
                                   uoff=0.5 * (i % 2))))
    for k in range(pots):
        x = (k - (pots - 1) / 2) * (w * 0.45)
        parts.append(chimney_pot(1.5, 3.2).translate([x, 0, h]))
    parts.append(box([-peg[0] / 2, -peg[1] / 2, -peg[2]], [peg[0] / 2, peg[1] / 2, 0.01]))
    return union(parts)


# ------------------------------------------------------------------ porch
def porch_posts(L, H, posts_u, pw=2.6, beam=2.2, drop=5.2, t=2.6, cap=True):
    """Flat post-and-arcade panel (prints lying on its back, t thick).

    Local frame: u along the porch edge (0..L), v up from the porch floor, w out
    (panel from w = -t/2 to t/2). posts_u = post centre positions."""
    parts = [ext(rect(0, H - beam, L, H), -t / 2, t / 2)]                     # beam
    for pu in posts_u:
        shaft = rect(pu - pw / 2 + 0.25, 0.0, pu + pw / 2 - 0.25, H - beam)
        parts.append(ext(shaft, -t / 2 + 0.25, t / 2))
        # chamfer-look: full-width blocks at base, mid-collar and capital
        for (v0, v1) in ((0.0, 2.6), (H * 0.36, H * 0.36 + 0.7), (H - beam - 1.6, H - beam)):
            parts.append(ext(rect(pu - pw / 2, v0, pu + pw / 2, v1), -t / 2, t / 2))
        parts.append(ext(rect(pu - pw / 2 - 0.35, H - beam - 0.8, pu + pw / 2 + 0.35, H - beam), -t / 2, t / 2))
    # arcade spandrels between posts
    for a, b in zip(posts_u[:-1], posts_u[1:]):
        span = b - a - pw
        half = span / 2
        vt = H - beam
        for s in (-1, 1):
            u_post = a + pw / 2 if s < 0 else b - pw / 2
            u_mid = (a + b) / 2
            u0, u1 = (u_post, u_mid) if s < 0 else (u_mid, u_post)
            sp = spandrel(0.0, half, 0.0, drop, 0.0, 1.0, bar=0.55)
            # spandrel() draws the corner at u=0: mirror for the right-hand post
            if s < 0:
                sp = sp.translate([u_post, vt, 0])
            else:
                sp = sp.mirror([1, 0, 0]).translate([u_post, vt, 0])
            parts.append(sp.translate([0, 0, t / 2 - 1.0]))
    # pendant drops at the arch crowns
    for a, b in zip(posts_u[:-1], posts_u[1:]):
        um = (a + b) / 2
        parts.append(ext(rect(um - 0.5, H - beam - 1.5, um + 0.5, H - beam), t / 2 - 1.2, t / 2))
    return union(parts)


def porch_deck(poly_pts, outer_edges, H=14.0, floor_t=1.6, piers_u=None, pier=3.4, skirt=1.4):
    """Porch deck: floor slab + brick piers + lattice skirt along outer edges.

    Prints upside down (floor on the bed). outer_edges: list of edge indices of
    the CCW polygon that face the yard; piers_u: {edge: [u, ...]}."""
    pts = ccw(poly_pts)
    base = poly(pts)
    parts = [slab(base, H - floor_t, H)]
    # floor board grooves on top: shallow cuts along the depth direction are hard on a
    # bed face, so boards are drawn as tiny ridges on the edges only (nosing)
    for i in outer_edges:
        f = Facade(pts[i], pts[(i + 1) % len(pts)], 0.0)
        L = f.L
        # skirt fascia board under the floor edge
        parts.append(f.place(box([0, H - floor_t - skirt, -0.9], [L, H - floor_t + 0.01, 0.0])))
        # nosing lip
        parts.append(f.place(box([-0.3, H - 0.6, -0.2], [L + 0.3, H, 0.35])))
        pu = (piers_u or {}).get(i, [])
        # lattice between piers, recessed
        lat_reg = rect(0.2, 0.0, L - 0.2, H - floor_t - skirt)
        for u in pu:
            lat_reg = lat_reg - rect(u - pier / 2, -1, u + pier / 2, H)
        lat = lattice(lat_reg, pitch=1.7, bar=0.5, d=0.9)
        parts.append(f.place(lat.translate([0, 0, -1.6])))
        parts.append(f.place(box([0.0, 0.0, -2.2], [L, H - floor_t - skirt, -1.5])))      # backing web
        for u in pu:
            pr = box([u - pier / 2, 0.0, -pier + 0.2], [u + pier / 2, H - floor_t - skirt + 0.01, 0.2])
            tex = brick(rect(u - pier / 2 + 0.05, 0.0, u + pier / 2 - 0.05, H - floor_t - skirt), bl=2.0, bh=0.75,
                        mortar=0.15, d=0.15).translate([0, 0, 0.2])
            parts.append(f.place(pr + tex))
    return union(parts)


def porch_roof(poly_pts, outer_path, z0, th=2.4, fascia=3.2, over=1.4, dent=True, roof_cs=None):
    """Flat porch roof: deck slab plus a moulded fascia along the yard edges.

    outer_path = open polyline along the yard edges (CCW order, yard on the right).
    Prints upside down."""
    top = z0 + fascia + th - 0.4
    deck = slab(roof_cs if roof_cs is not None else poly(ccw(poly_pts)), top - th, top)
    seat = -(over + 4.0)   # inner edge: wide enough to sit on the post beams
    prof = [(seat, z0), (0.0, z0), (0.0, z0 + fascia - 0.6), (0.35, z0 + fascia - 0.4), (over - 0.3, z0 + fascia),
            (over, z0 + fascia + 0.3), (over, top), (seat, top)]
    edge = sweep_run(outer_path, prof)
    parts = [deck, edge]
    if dent:
        P = np.asarray(outer_path, float)
        for a, b in zip(P[:-1], P[1:]):
            f = Facade(a, b, 0.0)
            den = dentils(0.6, f.L - 0.6, z0 + fascia - 1.3, 0.8, 0.0, 0.7, tooth=0.42, gap=0.38)
            parts.append(f.place(den))
    return union(parts)


def steps(width, rise_total, n, tread=2.6, cheek=1.8):
    """Stair block: n risers up to rise_total, cheek walls each side. Local: u across,
    w out from the porch edge (stairs descend toward +w), v up."""
    r = rise_total / n
    parts = []
    for k in range(n):
        parts.append(box([-width / 2, 0, 0], [width / 2, rise_total - k * r, (k + 1) * tread]))
    for s in (-1, 1):
        u0 = s * width / 2
        parts.append(box([min(u0, u0 + s * cheek), 0, 0], [max(u0, u0 + s * cheek), rise_total + 0.8, n * tread + 0.4]))
        parts.append(box([min(u0, u0 + s * cheek) - 0.2, rise_total + 0.3, -0.0],
                         [max(u0, u0 + s * cheek) + 0.2, rise_total + 1.1, n * tread + 0.6]))
    return union(parts)


# ------------------------------------------------------------------ porch assembly
def porch(poly_pts, runs, H_floor=14.0, post_h=35.5, over=1.4, footprint_keep=None, steps_at=(),
          pier=3.4, pw=2.6, t=2.6):
    """A complete porch from its plan polygon (CCW) and its yard-facing *runs*.

    runs: list of dict(a=(x,y), b=(x,y), posts=[u,...]) in CCW order, u measured from a.
    steps_at: list of (run_index, u, width).
    Returns dict(deck, panels=[(name, solid_local, A)], roof, steps=[(solid_local, A)])."""
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
    deck = porch_deck(pts, [i for i, _ in edges], H=H_floor, piers_u=piers, pier=pier)
    panels = []
    for k, r in enumerate(runs):
        f = Facade(r["a"], r["b"], H_floor)
        A = f.A.copy()
        A[:, 3] = f.world(0.0, 0.0, -t / 2 - 0.3)
        # a run that starts where the previous one ended leaves the corner to that panel
        s0 = t + 0.45 if k > 0 and np.allclose(runs[k - 1]["b"], r["a"], atol=0.05) else 0.0
        posts = [u - s0 for u in r["posts"] if u - s0 >= pw / 2 - 1e-6]
        panel = porch_posts(f.L - s0, post_h, posts, pw=pw, t=t).translate([s0, 0, 0])
        panels.append((f"run{k}", panel, A))
    # roof: polygon grown outward, cut back from the building later by the caller
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
    roof = porch_roof(None, [tuple(p) for p in path], H_floor + post_h, over=over, roof_cs=roof_cs)
    st = []
    for (ri, u, wdt) in steps_at:
        r = runs[ri]
        f = Facade(r["a"], r["b"], 0.0)
        A = f.A.copy()
        A[:, 3] = f.world(u, 0.0, 0.45)
        st.append((steps(wdt, H_floor, 4), A))
    return dict(deck=deck, panels=panels, roof=roof, steps=st)

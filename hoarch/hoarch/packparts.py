"""More detail-pack pieces: industrial clutter, board-formed concrete walls, trench works,
track-crew stock, modern-era EV chargers and solar, a Halloween cemetery, a Christmas tree lot
and telephone poles. As in hoarch.details, each prints in its colours with at most one filament
change at a height its plate shares, and needs no supports. Local z is up from the bed; HO sizes."""
import math

import numpy as np
from manifold3d import Manifold as M

from .core import box, cs_union, ft, inch, poly, rect, union
from .details import _rbox, _tie
from .ornament import ext
from .porchwork import _revolve

# change heights (the colour above starts here)
REEL_FLANGE = 0.8         # cable reel: wooden flange, then the cable
EV_PAD = 1.0              # EV island: concrete curb, then the chargers and bollards
SOLAR_FRAME = 0.6         # solar array: aluminium racking, then the modules
AC_PAD = 0.6              # condenser: concrete pad, then the unit
FENCE_CURB = 2.6          # cemetery fence: stone curb, then iron
TREE_STAND = 0.8          # Christmas tree: wooden stand, then the tree
SHACK_EAVE = 11.0         # tree-lot shack: red walls, then the snowy roof
ARM_TOP = 1.4             # telephone crossarm: the arm, then the glass insulators
RACK_TOP = 5.4            # rail rack: timbers, then the rails


def _capsule(a, b, r, seg=12):
    return M.hull(M.sphere(r, seg).translate(list(a)) + M.sphere(r, seg).translate(list(b)))


def _chain(pts, r0, r1=None, seg=12):
    r1 = r0 if r1 is None else r1
    n = len(pts) - 1
    return union([M.hull(M.sphere(r0 + (r1 - r0) * k / n, seg).translate(list(pts[k])) +
                         M.sphere(r0 + (r1 - r0) * (k + 1) / n, seg).translate(list(pts[k + 1]))) for k in range(n)])


# ================================================================== industrial clutter
def crate(l=ft(4.0), w=ft(3.0), h=ft(3.0)):
    """A wooden shipping crate: plank joints on every face, proud corner battens, and a diagonal
    brace across each long side."""
    b = box([0, 0, 0], [l, w, h])
    pitch = inch(6.0)
    cuts = []
    for k in range(1, int(h / pitch) + 1):
        z = k * pitch
        if z < h - 0.3:
            cuts.append(box([-1, -1, z - 0.07], [l + 1, w + 1, z + 0.07]) - box([0.15, 0.15, z - 1], [l - 0.15, w - 0.15, z + 1]))
    for k in range(1, int(w / pitch) + 1):                     # lid planks
        y = k * pitch
        if y < w - 0.3:
            cuts.append(box([-1, y - 0.07, h - 0.15], [l + 1, y + 0.07, h + 1]))
    b = b - union(cuts)
    bat = 0.5
    battens = []
    for x in (0.0, l - bat):
        for y in (-0.15, w - bat + 0.15):
            battens.append(box([x - 0.15 * (x == 0), y, 0.0], [x + bat + 0.15 * (x > 0), y + bat, h]))
    for y0, y1 in ((-0.15, 0.01), (w - 0.01, w + 0.15)):        # diagonal braces on the long sides
        for (x0, z0, x1, z1) in ((bat, 0.3, l - bat, h - 0.3),):
            d = math.hypot(x1 - x0, z1 - z0)
            a = math.degrees(math.atan2(z1 - z0, x1 - x0))
            br = box([0, y0, -0.25], [d, y1, 0.25]).rotate([0, -a, 0]).translate([x0, 0, z0])
            battens.append(br ^ box([bat, y0 - 1, 0.0], [l - bat, y1 + 1, h]))
        battens.append(box([0, y0, 0.0], [l, y1, 0.45]))
        battens.append(box([0, y0, h - 0.45], [l, y1, h]))
    return b + union(battens)


def barrel(h=ft(35 / 12), r_end=inch(10.5), r_mid=inch(12.5)):
    """A wooden barrel: bulged staves (a groove between each), four iron hoops, and a head set
    down inside the chime."""
    prof = [(0.0, 0.0)] + [(r_end + (r_mid - r_end) * math.sin(math.pi * t), h * t) for t in np.linspace(0, 1, 13)] + [(0.0, h)]
    body = _revolve(prof[:-1] + [(0.0, h)], 40)
    grooves = union([box([r_end - 0.4, -0.05, 0.3], [r_mid + 0.5, 0.05, h - 0.3]).rotate([0, 0, 360.0 * k / 22]) for k in range(22)])
    body = body - grooves
    hoops = []
    for t in (0.1, 0.3, 0.7, 0.9):
        z = h * t
        r = r_end + (r_mid - r_end) * math.sin(math.pi * t)
        hoops.append(M.cylinder(0.32, r + 0.1, r + 0.1, 40).translate([0, 0, z - 0.16]))
    head = M.cylinder(0.4, r_end - 0.35, r_end - 0.35, 40).translate([0, 0, h - 0.35])
    return body + union(hoops) - head


def tire_stack(n=5, seed=41):
    """Worn car tyres stacked flat, a little off true, with tread blocks round the crown."""
    rng = np.random.default_rng(seed)
    R, w, ri = inch(13.0), inch(8.0), inch(7.5)
    prof = [(ri, 0.15), (ri + 0.3, 0.0), (R - 0.5, 0.0), (R, 0.45), (R, w - 0.45), (R - 0.5, w), (ri + 0.3, w), (ri, w - 0.15)]
    t = M.revolve(poly([(r, z) for r, z in prof]), 40)
    tread = union([box([R - 0.25, -0.12, 0.6], [R + 0.1, 0.12, w - 0.6]).rotate([0, 0, 360.0 * k / 36]) for k in range(36)])
    tire = t - tread
    return union([tire.translate([rng.uniform(-0.3, 0.3), rng.uniform(-0.3, 0.3), k * (w - 0.05)]) for k in range(n)])


def pipe_stack(L=35.0, r=inch(6.4), bore=0.72, rows=(4, 3, 2), seed=43):
    """Steel pipe stacked in a pyramid, the bottom row flattened where it meets the ground (no
    overhang past 45 degrees), with wedge chocks at the outer pipes. Prints as one piece."""
    out = []
    z0 = r * 0.7                                  # bottom row's centre: 0.3 r cut off below
    for k, n in enumerate(rows):
        zc = z0 + k * r * math.sqrt(3) * 0.995
        for i in range(n):
            y = (i - (n - 1) / 2) * 2 * r * 0.995
            p = M.cylinder(L, r, r, 36).rotate([0, 90, 0]).translate([0, y, zc])
            hole = M.cylinder(L + 2, r * bore, r * bore, 28).rotate([0, 90, 0]).translate([-1, y, zc])
            out.append((p, hole))
    pipes = union([p for p, _ in out]) - union([h for _, h in out])
    pipes = pipes ^ box([-1, -50, 0.0], [L + 1, 50, 50])
    n0 = rows[0]
    yo = (n0 - 1) / 2 * 2 * r * 0.995 + r
    chocks = union([M.hull_points([(x, s * yo, 0.0) for x in (xc - 0.8, xc + 0.8)] + [(x, s * (yo + 1.6), 0.0) for x in (xc - 0.8, xc + 0.8)] +
                                  [(x, s * (yo - 0.3), r * 1.1) for x in (xc - 0.8, xc + 0.8)])
                    for xc in (4.0, L - 4.0) for s in (-1, 1)])
    return pipes + chocks


def cable_reel(R=ft(2.5), W=ft(3.6), core=0.82):
    """A cable reel standing on one flange: the wooden flange (planks and bolt heads) to
    REEL_FLANGE, the wound cable above it in its own colour, ridged turn by turn. The top
    flange is reel_flange(), glued on: it covers the whole cable end."""
    fl = M.cylinder(REEL_FLANGE, R, R, 64)
    planks = union([box([-R - 1, y - 0.06, REEL_FLANGE - 0.12], [R + 1, y + 0.06, REEL_FLANGE + 0.01]) for y in np.arange(-R, R, inch(8.0))])
    fl = fl - planks
    bolts = union([M.cylinder(0.25, 0.35, 0.35, 10).translate([0.62 * R * math.cos(a), 0.62 * R * math.sin(a), -0.0])
                   for a in np.linspace(0, 2 * math.pi, 8, endpoint=False)])
    rc = R * core
    cable = M.cylinder(W, rc, rc, 64).translate([0, 0, REEL_FLANGE - 0.01])
    ridges = union([M.cylinder(0.2, rc + 0.12, rc + 0.12, 64).translate([0, 0, REEL_FLANGE + z]) for z in np.arange(0.3, W - 0.3, 0.55)])
    return fl - bolts + cable + ridges


def reel_flange(R=ft(2.5)):
    """The reel's top flange, printed flat: planks across it, a steel hub plate with bolt heads."""
    fl = M.cylinder(REEL_FLANGE, R, R, 64)
    planks = union([box([-R - 1, y - 0.06, REEL_FLANGE - 0.12], [R + 1, y + 0.06, REEL_FLANGE + 0.01]) for y in np.arange(-R, R, inch(8.0))])
    hub = M.cylinder(0.3, R * 0.25, R * 0.25, 32).translate([0, 0, REEL_FLANGE - 0.01]) - \
        M.cylinder(1.0, R * 0.09, R * 0.09, 24).translate([0, 0, REEL_FLANGE - 0.3])
    bolts = union([M.cylinder(0.25, 0.3, 0.3, 10).translate([R * 0.19 * math.cos(a), R * 0.19 * math.sin(a), REEL_FLANGE + 0.28])
                   for a in np.linspace(0, 2 * math.pi, 6, endpoint=False)])
    return fl - planks + hub + bolts


def concrete_wall(L=50.0, H=20.0, seed=51):
    """A board-formed concrete retaining wall panel printed face-up: the lines of the form boards,
    form-tie dimples in a grid, and a coping along the top edge, on lapped ends like tie_wall
    (installed, y is up)."""
    lap = 1.5
    back = box([-lap, 0.0, 0.0], [L, H, 1.0])
    face = box([0.0, 0.0, 0.99], [L, H - 1.4, 1.8])
    rng = np.random.default_rng(seed)
    lines = [box([-1, y - 0.06, 1.66], [L + 1, y + 0.06, 1.9]) for y in np.arange(inch(6.0), H - 1.5, inch(6.0))]
    # the form boards' ends, staggered course by course
    ends = []
    for k, y in enumerate(np.arange(0.0, H - 1.5, inch(6.0))):
        for x in np.arange(rng.uniform(2, 14), L - 1, ft(8.0)):
            ends.append(box([x - 0.06, y, 1.66], [x + 0.06, min(y + inch(6.0), H - 1.4), 1.9]))
    ties = [M.sphere(0.22, 10).translate([x, y, 1.8]) for x in np.arange(3.5, L - 1, 7.0) for y in np.arange(3.0, H - 2.5, 7.0)]
    coping = _rbox(0.0, H - 1.4, 0.99, L, H, 2.2, 0.25)
    from .details import scarf
    return scarf(back + (face - union(lines + ends + ties)) + coping, L, lap, H)


# ================================================================== trench works
def jerrycan(cx=0.0, cy=0.0, z0=0.0):
    """A 20 litre jerrycan standing: the X pressed in each side, three handles across the top."""
    l, w, h = 5.4 * 0.86, 1.9, 3.9 * 0.86
    c = _rbox(-l / 2, -w / 2, 0.0, l / 2, w / 2, h, 0.2)
    xs = []
    for s in (-1, 1):
        for a in (1, -1):
            xs.append(box([-1.9, -0.11, -0.13], [1.9, 0.11, 0.13]).rotate([0, a * 32, 0]).translate([0, s * (w / 2 + 0.02), h * 0.47]))
    c = c + (union(xs) ^ box([-l / 2 + 0.3, -w, 0.4], [l / 2 - 0.3, w, h - 0.5]))
    for x in (-0.9, 0.0, 0.9):                      # handles: tiny bridges
        c = c + (box([x - 0.18, -0.35, h - 0.01], [x + 0.18, 0.35, h + 0.45]) - box([x - 1, -0.15, h - 0.1], [x + 1, 0.15, h + 0.25]))
    c = c + M.cylinder(0.35, 0.35, 0.35, 12).translate([l / 2 - 0.65, 0.0, h - 0.01])
    return c.translate([cx, cy, z0])


def jerrycan_stack(cols=4, rows=3):
    """Jerrycans standing shoulder to shoulder in ranks, as dumped at a fuel point."""
    l, w = 5.4 * 0.86, 1.9
    return union([jerrycan(i * (l - 0.05), j * (w - 0.05), 0.0) for i in range(cols) for j in range(rows)])


def revetment(L=40.0, H=20.0, kind="planks", seed=61):
    """A trench revetment panel printed face-up (installed, y is up): pointed stakes every
    ~1 m with horizontal planks behind them, or (``kind`` = "wattle") brushwood woven in and
    out of the stakes."""
    rng = np.random.default_rng(seed)
    back = box([0.0, 0.0, 0.0], [L, H, 0.8])
    stakes_x = np.arange(2.0, L - 1.0, 9.0)
    parts = [back]
    if kind == "planks":
        for y in np.arange(0.0, H - 0.5, inch(8.0)):
            for x0 in np.arange(-rng.uniform(0, 12), L, ft(10.0)):
                a, b = max(x0, 0.0), min(x0 + ft(10.0) - 0.2, L)
                if b - a > 1.0:
                    parts.append(_rbox(a, y + 0.05, 0.79, b, y + inch(8.0) - 0.08, 1.35 + rng.uniform(-0.08, 0.08), 0.1))
    else:
        for k, y in enumerate(np.arange(0.4, H - 0.4, 0.75)):
            ph = (k % 2) * math.pi
            pts = [(x, y, 1.15 + 0.32 * math.sin(math.pi * (x - stakes_x[0]) / 9.0 + ph)) for x in np.linspace(0.3, L - 0.3, 41)]
            parts.append(_chain(pts, 0.36) ^ box([0, 0, 0.75], [L, H, 3]))
    for x in stakes_x:
        r = 0.55
        parts.append(_chain([(x, -1.2, 1.4), (x, H + 1.0, 1.4)], r))
        parts.append(M.hull_points([(x + dx, H + 1.0, 1.4 + dz) for dx in (-r, r) for dz in (-r, r)] + [(x, H + 2.4, 1.4)]))
    return union(parts) ^ box([-1, -1.3, 0.0], [L + 1, H + 3, 5])


def duckboard(L=40.0, W=ft(2.2)):
    """A trench duckboard: two runners and cross slats, a gap between each slat."""
    runners = [box([0.0, y, 0.0], [L, y + 0.8, 0.8]) for y in (0.5, W - 1.3)]
    slats = [box([x, 0.0, 0.79], [x + 1.0, W, 1.25]) for x in np.arange(0.2, L - 0.9, 1.7)]
    return union(runners + slats)


# ================================================================== track crew
def tie_heap(seed=72):
    """Old ties pulled from the track and dumped: two loose layers at odd angles."""
    rng = np.random.default_rng(seed)
    tl, tw, td = ft(8.5), inch(9.0), inch(7.0)
    ties = []
    for k in range(8):
        a = rng.uniform(-12, 12)
        t = _tie(-tl / 2, -tw / 2, 0.0, tl, rng, w=tw, d=td).rotate([0, 0, a]).translate([rng.uniform(-2.5, 2.5), k * 2.35 - 8.2, 0])
        ties.append(t)
    for k in range(4):
        a = 90 + rng.uniform(-30, 30)
        t = _tie(-tl / 2, -tw / 2, 0.0, tl, rng, w=tw, d=td).rotate([0, 0, a]).translate([rng.uniform(-5, 5), rng.uniform(-3, 3), td - 0.08])
        ties.append(t)
    return union(ties)


def _rail(L):
    """A code 83 rail lying in its upright section along x: base, web and head."""
    s = poly([(-0.9, 0.0), (0.9, 0.0), (0.9, 0.25), (0.25, 0.45), (0.2, 1.45), (0.5, 1.6), (0.5, 2.1), (-0.5, 2.1), (-0.5, 1.6),
              (-0.2, 1.45), (-0.25, 0.45), (-0.9, 0.25)])
    return ext(s, 0.0, L).rotate([0, 90, 0]).rotate([90, 0, 0])


def rail_rack(L=40.0, n=5):
    """A rack of relay rail: two cross timbers on short posts carrying ``n`` rails. Timbers to
    RACK_TOP, the rails above in steel colour (the bridges between timbers print unsupported)."""
    span = n * 2.6 + 1.0
    posts, timbers = [], []
    for x in (6.0, L - 6.0):
        for y in (-span / 2, span / 2 - 1.6):
            posts.append(box([x - 0.8, y, 0.0], [x + 0.8, y + 1.6, RACK_TOP - 1.4]))
        timbers.append(_rbox(x - 0.9, -span / 2 - 0.4, RACK_TOP - 1.41, x + 0.9, span / 2 + 0.4, RACK_TOP, 0.12))
    rails = []
    for k in range(n):
        y = -span / 2 + 1.3 + k * 2.6
        r = _rail(L)
        b = r.bounding_box()
        rails.append(r.translate([-b[0], y - (b[1] + b[4]) / 2, RACK_TOP - 0.02 - b[2]]))
    return union(posts + timbers + rails)


def keg(h=inch(18.0), r=inch(6.5)):
    prof = [(0.0, 0.0)] + [(r * (0.9 + 0.1 * math.sin(math.pi * t)), h * t) for t in np.linspace(0, 1, 9)] + [(0.0, h)]
    k = _revolve(prof[:-1] + [(0.0, h)], 28)
    hoops = union([M.cylinder(0.22, r * 0.97, r * 0.97, 28).translate([0, 0, h * t - 0.11]) for t in (0.15, 0.85)])
    return k + hoops


def keg_cluster(n=6, seed=73):
    """Spike and tie-plate kegs grouped on a low plank skid, one keg lying on top."""
    rng = np.random.default_rng(seed)
    skid = box([-0.5, -0.5, 0.0], [3 * 4.2 + 0.5, 2 * 4.2 + 0.5, 0.6])
    out = [skid]
    for i in range(3):
        for j in range(2):
            out.append(keg().translate([2.1 + i * 4.2 + rng.uniform(-0.2, 0.2), 2.1 + j * 4.2 + rng.uniform(-0.2, 0.2), 0.59]))
    return union(out)


# ================================================================== modern era
def ev_charger(x=0.0, y=0.0, z0=EV_PAD - 0.01):
    """A pedestal EV charger: a rounded column with an inset screen panel, a holster with the
    connector, and the cable running down the side to a loop at the foot (all attached)."""
    w, d, h = 2.8, 1.5, 15.0
    body = _rbox(-w / 2, -d / 2, 0.0, w / 2, d / 2, h - 0.6, 0.35) + \
        M.hull_points([(xx, yy, h - 0.61) for xx in (-w / 2 + 0.35, w / 2 - 0.35) for yy in (-d / 2 + 0.35, d / 2 - 0.35)] +
                      [(xx, yy, h) for xx in (-w / 2 + 0.6, w / 2 - 0.6) for yy in (-d / 2 + 0.5, d / 2 - 0.5)])
    screen = box([-w / 2 + 0.45, -d / 2 - 0.1, h * 0.62], [w / 2 - 0.45, -d / 2 + 0.15, h * 0.85])
    body = body - screen
    holster = _rbox(w / 2 - 0.02, -0.5, h * 0.45, w / 2 + 0.7, 0.5, h * 0.58, 0.15)
    cable = _chain([(w / 2 + 0.35, 0.0, h * 0.45), (w / 2 + 0.3, 0.1, h * 0.25), (w / 2 + 0.25, 0.25, 2.0),
                    (w / 2 + 0.2, 0.55, 0.6), (w / 2 - 0.4, 0.75, 0.5)], 0.3)
    base = _rbox(-w / 2 - 0.3, -d / 2 - 0.3, 0.0, w / 2 + 0.3, d / 2 + 0.3, 0.8, 0.15)
    return (body + holster + cable + base).translate([x, y, z0])


def ev_island(n=2):
    """A curbed concrete island with ``n`` chargers and a bollard at each end. Curb to EV_PAD,
    chargers and bollards above in their own colour."""
    L = 6.5 * n + 7.0
    pad = _rbox(0.0, 0.0, 0.0, L, 6.0, EV_PAD, 0.3)
    up = [ev_charger(3.5 + 1.7 + k * 6.5, 3.0) for k in range(n)]
    for x in (1.6, L - 1.6):
        up.append(M.cylinder(8.0, 0.75, 0.75, 24).translate([x, 3.0, EV_PAD - 0.01]) +
                  M.sphere(0.75, 16).translate([x, 3.0, EV_PAD + 7.99]) +
                  (M.cylinder(0.8, 0.82, 0.82, 24).translate([x, 3.0, EV_PAD + 5.5])))
    return pad + union(up)


def solar_array(nx=3, ny=2):
    """A flush rooftop solar array: aluminium rails and module frames to SOLAR_FRAME, the dark
    modules raised inside them above it (60-cell modules, 19.0 x 11.4 mm), with the cell grid
    pressed in. Glue it to a roof."""
    mw, mh, g = 11.4, 19.0, 0.35
    L, W = nx * (mw + g) + g, ny * (mh + g) + g
    frame = box([0.0, 0.0, 0.0], [L, W, SOLAR_FRAME])
    rails = [box([-0.6, y - 0.5, 0.0], [L + 0.6, y + 0.5, SOLAR_FRAME]) for y in (W * 0.25, W * 0.75)]
    mods = []
    for i in range(nx):
        for j in range(ny):
            x0, y0 = g + i * (mw + g), g + j * (mh + g)
            m = box([x0 + 0.2, y0 + 0.2, SOLAR_FRAME - 0.01], [x0 + mw - 0.2, y0 + mh - 0.2, SOLAR_FRAME + 0.4])
            grid = [box([x0 + mw * k / 6 - 0.04, y0, SOLAR_FRAME + 0.3], [x0 + mw * k / 6 + 0.04, y0 + mh, SOLAR_FRAME + 0.5]) for k in range(1, 6)]
            grid += [box([x0, y0 + mh * k / 10 - 0.04, SOLAR_FRAME + 0.3], [x0 + mw, y0 + mh * k / 10 + 0.04, SOLAR_FRAME + 0.5]) for k in range(1, 10)]
            mods.append(m - union(grid))
    return union([frame] + rails) + union(mods)


def ac_condenser():
    """A house's air-conditioning condenser on its concrete pad: louvred sides, a fan guard of
    rings and spokes on top. Pad to AC_PAD, the unit above."""
    s, h = 8.6, 7.4
    pad = _rbox(-s / 2 - 1.0, -s / 2 - 1.0, 0.0, s / 2 + 1.0, s / 2 + 1.0, AC_PAD, 0.2)
    unit = _rbox(-s / 2, -s / 2, AC_PAD - 0.01, s / 2, s / 2, AC_PAD + h, 0.25)
    louv = union([box([-s, -s, AC_PAD + z - 0.08], [s, s, AC_PAD + z + 0.08]) - box([-s / 2 + 0.15, -s / 2 + 0.15, 0], [s / 2 - 0.15, s / 2 - 0.15, 20])
                  for z in np.arange(1.2, h - 1.2, 0.5)])
    unit = unit - louv
    fan = M.cylinder(0.5, s * 0.42, s * 0.42, 48).translate([0, 0, AC_PAD + h - 0.49])
    guard = union([M.cylinder(0.5, r + 0.08, r + 0.08, 48) - M.cylinder(0.6, r - 0.08, r - 0.08, 48) for r in np.arange(0.8, s * 0.42, 0.6)] +
                  [box([-s * 0.42, -0.1, 0], [s * 0.42, 0.1, 0.5]).rotate([0, 0, a]) for a in (0, 60, 120)])
    unit = unit - fan + guard.translate([0, 0, AC_PAD + h - 0.49])
    return pad + unit


def rooftop_unit(l=26.0, w=12.0, h=9.0):
    """A commercial rooftop package unit: louvred end panels, access doors with handles and two
    fan shrouds on top. One colour; glue it to a flat roof."""
    u = _rbox(0.0, 0.0, 0.0, l, w, h, 0.3)
    louv = union([box([-1, -1, z - 0.08], [l * 0.3, w + 1, z + 0.08]) for z in np.arange(1.0, h - 1.0, 0.45)])
    inner = box([0.15, 0.15, 0.0], [l - 0.15, w - 0.15, h + 1])
    u = u - (louv - inner)
    doors = union([box([x, -0.12, 0.8], [x + 4.5, 0.01, h - 0.8]) - box([x + 0.15, -1, 0.95], [x + 4.35, 1, h - 0.95])
                   for x in (l * 0.36, l * 0.36 + 5.2)])
    handles = union([box([x + 3.6, -0.3, h * 0.5 - 0.5], [x + 3.9, 0.01, h * 0.5 + 0.5]) for x in (l * 0.36, l * 0.36 + 5.2)])
    fans = union([(M.cylinder(1.2, 3.6, 3.6, 40) - M.cylinder(1.3, 3.2, 3.2, 40).translate([0, 0, 0.5])).translate([x, w / 2, h - 0.01])
                  for x in (l * 0.55, l * 0.82)])
    grilles = union([box([x - 3.3, w / 2 - 0.1, h + 0.6], [x + 3.3, w / 2 + 0.1, h + 1.0]) for x in (l * 0.55, l * 0.82)] +
                    [box([x - 0.1, w / 2 - 3.3, h + 0.6], [x + 0.1, w / 2 + 3.3, h + 1.0]) for x in (l * 0.55, l * 0.82)])
    grilles = grilles ^ union([M.cylinder(2, 3.3, 3.3, 40).translate([x, w / 2, h]) for x in (l * 0.55, l * 0.82)])
    return u + doors + handles + fans + grilles


# ================================================================== cemetery
def _stone_outline(kind, w, h):
    if kind == "round":
        pts = [(-w / 2, 0.0), (w / 2, 0.0), (w / 2, h - w / 2)] + \
              [(w / 2 * math.cos(t), h - w / 2 + w / 2 * math.sin(t)) for t in np.linspace(0, math.pi, 20)[1:-1]] + [(-w / 2, h - w / 2)]
    elif kind == "gothic":
        rise = w * 0.8
        spring = h - rise
        R = (rise ** 2 + (w / 2) ** 2) / w           # each side an arc centred on the far springing line
        right = [(w / 2 - R + R * math.cos(t), spring + R * math.sin(t)) for t in np.linspace(0, math.asin(rise / R), 10)]
        pts = [(-w / 2, 0.0), (w / 2, 0.0)] + right[:-1] + [(0.0, h)] + [(-x, z) for x, z in right[:-1][::-1]]
    elif kind == "shoulder":
        pts = [(-w / 2, 0.0), (w / 2, 0.0), (w / 2, h - 1.2), (w / 2 - 0.8, h - 1.2), (w / 2 - 0.8, h - 0.4), (w / 6, h - 0.4),
               (0.0, h), (-w / 6, h - 0.4), (-w / 2 + 0.8, h - 0.4), (-w / 2 + 0.8, h - 1.2), (-w / 2, h - 1.2)]
    elif kind == "cross":
        a = w * 0.32
        pts = [(-a / 2, 0.0), (a / 2, 0.0), (a / 2, h * 0.62), (w / 2, h * 0.62), (w / 2, h * 0.62 + a), (a / 2, h * 0.62 + a),
               (a / 2, h), (-a / 2, h), (-a / 2, h * 0.62 + a), (-w / 2, h * 0.62 + a), (-w / 2, h * 0.62), (-a / 2, h * 0.62)]
    else:                                                       # flat tablet with a sloped top
        pts = [(-w / 2, 0.0), (w / 2, 0.0), (w / 2, h - 0.6), (0.0, h), (-w / 2, h - 0.6)]
    return poly(pts)


def headstone(kind="round", w=5.0, h=8.0, t=1.6, lean=0.0):
    """A headstone printed upright on its base: the stone (``kind`` round, gothic, shoulder,
    cross or tablet) with a sunk inscription panel on the face, on a stepped base."""
    base = _rbox(-w / 2 - 0.7, -t / 2 - 0.7, 0.0, w / 2 + 0.7, t / 2 + 0.7, 1.0, 0.25)
    s = ext(_stone_outline(kind, w, h), -t / 2, t / 2).rotate([90, 0, 0]).translate([0, 0, 0.99])
    if kind != "cross":
        panel = box([-w / 2 + 0.8, -t / 2 - 0.2, 0.99 + h * 0.2], [w / 2 - 0.8, -t / 2 + 0.15, 0.99 + h * 0.62])
        s = s - panel
    if lean:
        s = s.rotate([lean, 0, 0])
        s = s ^ box([-20, -20, 0.6], [20, 20, 40])
    return base + s


def obelisk(h=16.0):
    """A granite obelisk on a two-step plinth with a die block."""
    p1 = _rbox(-3.0, -3.0, 0.0, 3.0, 3.0, 1.2, 0.25)
    p2 = _rbox(-2.3, -2.3, 1.19, 2.3, 2.3, 2.2, 0.2)
    die = _rbox(-1.8, -1.8, 2.19, 1.8, 1.8, 5.2, 0.15)
    shaft = M.hull_points([(x, y, 5.19) for x in (-1.2, 1.2) for y in (-1.2, 1.2)] + [(x, y, h - 1.4) for x in (-0.75, 0.75) for y in (-0.75, 0.75)])
    tip = M.hull_points([(x, y, h - 1.41) for x in (-0.75, 0.75) for y in (-0.75, 0.75)] + [(0.0, 0.0, h)])
    return p1 + p2 + die + shaft + tip


def mausoleum():
    """A small Greek-revival family tomb: three steps, a cella with a panelled bronze-style door,
    two round columns in antis, an entablature and a pediment with a wreath."""
    W, D = 18.0, 20.0
    steps = union([_rbox(-W / 2 - 2.4 + k * 0.8, -1.5 - 2.4 + k * 0.8, k * 0.8, W / 2 + 2.4 - k * 0.8, D + 0.6 - k * 0.8, (k + 1) * 0.8, 0.12)
                   for k in range(3)])
    z0 = 2.4
    cella = box([-W / 2 + 0.6, 3.0, z0 - 0.01], [W / 2 - 0.6, D - 0.6, z0 + 14.0])
    door = box([-3.2, 2.9, z0 - 0.01], [3.2, 3.6, z0 + 9.5])
    door_panels = union([box([x - 1.3, 3.25, z0 + zz], [x + 1.3, 3.61, z0 + zz + 3.6]) for x in (-1.6, 1.6) for zz in (1.0, 5.2)])
    antae = union([box([s * (W / 2 - 0.6) - 1.0, 0.0, z0 - 0.01], [s * (W / 2 - 0.6) + 1.0, 3.2, z0 + 14.0]) for s in (-1, 1)])
    cols = union([_revolve([(0.0, z0 - 0.01), (1.25, z0 - 0.01), (1.25, z0 + 0.5), (1.0, z0 + 0.8), (0.85, z0 + 13.0), (1.2, z0 + 13.4),
                            (1.4, z0 + 14.0), (0.0, z0 + 14.0)], 28).translate([x, 1.4, 0]) for x in (-3.6, 3.6)])
    ent = M.hull_points([(x, y, z) for x in (-W / 2, W / 2) for y in (-0.4, D - 0.3) for z in (z0 + 13.99, z0 + 15.6)] +
                        [(x, y, z0 + 16.3) for x in (-W / 2 - 0.6, W / 2 + 0.6) for y in (-1.0, D + 0.3)])
    zp = z0 + 16.3
    ped = M.hull_points([(x, y, zp - 0.01) for x in (-W / 2 - 0.6, W / 2 + 0.6) for y in (-1.0, D + 0.3)] +
                        [(0.0, y, zp + 4.5) for y in (-1.0, D + 0.3)])
    wreath = (M.cylinder(0.4, 1.6, 1.6, 32) - M.cylinder(0.6, 1.0, 1.0, 32).translate([0, 0, -0.1])).rotate([90, 0, 0]).translate([0, -1.0, zp + 1.7])
    return steps + (cella - door) + door_panels.translate([0, 0.0, 0]) + antae + cols + ent + ped + wreath


def cemetery_fence(L=40.0, pitch=2.2):
    """A cemetery railing on a granite curb printed upright: lancet-headed pickets, a quatrefoil
    band under the top rail, two rails. Curb to FENCE_CURB, iron above."""
    w = 2.0
    curb = M.hull_points([(x, y, z) for x in (0.0, L) for y in (-w / 2, w / 2) for z in (0.0, FENCE_CURB - 0.35)] +
                         [(x, y, FENCE_CURB) for x in (0.0, L) for y in (-w / 2 + 0.35, w / 2 - 0.35)])
    n = int((L - 1.0) / pitch)
    x0 = (L - n * pitch) / 2
    xs = [x0 + k * pitch for k in range(n + 1)]
    iron = []
    for x in xs:
        s = poly([(x - 0.35, FENCE_CURB - 0.01), (x + 0.35, FENCE_CURB - 0.01), (x + 0.35, 10.8), (x + 0.6, 11.2), (x + 0.3, 11.9),
                  (x, 12.6), (x - 0.3, 11.9), (x - 0.6, 11.2), (x - 0.35, 10.8)])
        iron.append(ext(s, -0.35, 0.35).rotate([90, 0, 0]))
    iron += [box([-0.3, -0.4, 4.0], [L + 0.3, 0.4, 4.6]), box([-0.3, -0.4, 9.6], [L + 0.3, 0.4, 10.2])]
    for a, b in zip(xs[:-1], xs[1:]):
        c = (a + b) / 2
        r = (b - a) / 2 - 0.35
        q = cs_union([poly([(c + r * 0.55 * math.cos(t) + dx, 8.4 + r * 0.55 * math.sin(t) + dz) for t in np.linspace(0, 2 * math.pi, 14, endpoint=False)])
                      for dx, dz in ((r * 0.55, 0), (-r * 0.55, 0), (0, r * 0.45), (0, -r * 0.45))])
        hole = poly([(c + r * 0.3 * math.cos(t), 8.4 + r * 0.3 * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 12, endpoint=False)])
        iron.append(ext(q - hole, -0.3, 0.3).rotate([90, 0, 0]))
    return curb + union(iron)


def cemetery_post():
    """A cemetery fence post: a granite block to FENCE_CURB, an iron post with a cross finial."""
    blk = M.hull_points([(x, y, z) for x in (-1.5, 1.5) for y in (-1.5, 1.5) for z in (0.0, FENCE_CURB - 0.35)] +
                        [(x, y, FENCE_CURB) for x in (-1.15, 1.15) for y in (-1.15, 1.15)])
    post = box([-0.85, -0.85, FENCE_CURB - 0.01], [0.85, 0.85, 12.0])
    cap = M.hull_points([(x, y, 11.99) for x in (-0.85, 0.85) for y in (-0.85, 0.85)] +
                        [(x, y, z) for x in (-1.2, 1.2) for y in (-1.2, 1.2) for z in (12.35, 12.6)])
    cross = box([-0.25, -0.25, 12.59], [0.25, 0.25, 15.4]) + box([-1.0, -0.25, 14.0], [1.0, 0.25, 14.5])
    return blk + post + cap + cross


def dead_tree(h=26.0, seed=81):
    """A bare, crooked tree for the cemetery: a tapering trunk on a root flare and branches that
    climb at 45 degrees or steeper (so it prints without support)."""
    rng = np.random.default_rng(seed)
    trunk_pts = [(0.0, 0.0, 0.0)]
    x = y = 0.0
    for k in range(1, 7):
        x += rng.uniform(-0.7, 0.7)
        y += rng.uniform(-0.7, 0.7)
        trunk_pts.append((x, y, h * 0.62 * k / 6))
    parts = [_chain(trunk_pts, 1.6, 0.8), M.cylinder(0.8, 3.2, 1.6, 24)]
    for k in range(5):
        z0 = h * (0.3 + 0.07 * k)
        a = rng.uniform(0, 2 * math.pi)
        p0 = np.array(trunk_pts[min(int(z0 / (h * 0.62) * 6), 6)])
        p0[2] = z0
        pts = [tuple(p0)]
        for s in range(3):
            step = rng.uniform(2.2, 3.5)
            p = np.array(pts[-1]) + np.array([math.cos(a) * step * 0.7, math.sin(a) * step * 0.7, step])
            a += rng.uniform(-0.5, 0.5)
            pts.append(tuple(p))
        parts.append(_chain(pts, 0.65, 0.43))          # no twig under 0.85 mm: the nozzle draws 0.4
    return union(parts) ^ box([-50, -50, 0.0], [50, 50, 100])


# ================================================================== Christmas tree lot
def xmas_tree(h=21.0, seed=91):
    """A cut fir in a wooden cross stand: the stand to TREE_STAND, then the tree in tiers that
    flare out at 45 degrees and slope back up, each hem notched into boughs."""
    rng = np.random.default_rng(seed)
    stand = box([-2.4, -0.45, 0.0], [2.4, 0.45, TREE_STAND]) + box([-0.45, -2.4, 0.0], [0.45, 2.4, TREE_STAND])
    trunk = M.cylinder(2.0, 0.55, 0.5, 16).translate([0, 0, TREE_STAND - 0.01])
    tiers = []
    z = TREE_STAND + 1.2
    n = 5
    R0 = h * 0.24
    for k in range(n):
        R = R0 * (1 - k / (n + 0.6))
        th = (h - (z - TREE_STAND)) / (n - k) * 1.35
        prof = [(0.0, z), (0.55, z), (R, z + R - 0.55), (R * 0.25, z + max(th, R - 0.3)), (0.0, z + max(th, R - 0.3))]
        tier = M.revolve(poly([(r, zz) for r, zz in prof]), 24)
        notch = union([box([R * 0.55, -0.22, z - 1], [R + 1, 0.22, z + R * 0.62]).rotate([0, 0, 360 * j / 9 + rng.uniform(-8, 8)]) for j in range(9)])
        tiers.append(tier - notch)
        z += th * 0.62
    tip = M.cylinder(1.6, 0.4, 0.05, 12).translate([0, 0, z])
    return stand + trunk + union(tiers) + tip


def lot_shack():
    """The tree lot's sales shack: board-and-batten walls with a serving hatch and door to
    SHACK_EAVE (red), then the gable roof with deep eaves (white: snow)."""
    L, W = 14.0, 10.0
    walls = box([0.0, 0.0, 0.0], [L, W, SHACK_EAVE])
    battens = union([box([x - 0.12, -0.12, 0.0], [x + 0.12, W + 0.12, SHACK_EAVE]) for x in np.arange(1.0, L, 1.4)] +
                    [box([-0.12, y - 0.12, 0.0], [L + 0.12, y + 0.12, SHACK_EAVE]) for y in np.arange(1.0, W, 1.4)])
    hatch = box([3.0, -0.2, 4.6], [10.5, 0.4, 8.6])
    shelf = M.hull_points([(x, y, z) for x in (2.6, 10.9) for y in (-1.2, 0.0) for z in (4.2, 4.6)] + [(x, 0.0, 3.0) for x in (2.6, 10.9)])
    door = box([L - 0.2, 3.0, 0.0], [L + 0.2, 7.0, 8.4])
    gable = M.hull_points([(x, y, SHACK_EAVE - 0.01) for x in (0.0, L) for y in (0.0, W)] + [(x, W / 2, SHACK_EAVE + 4.0) for x in (0.0, L)])
    roof = M.hull_points([(x, y, z) for x in (-1.2, L + 1.2) for (y, z) in ((-1.4, SHACK_EAVE - 0.01), (-1.4, SHACK_EAVE + 0.5),
                                                                           (W + 1.4, SHACK_EAVE - 0.01), (W + 1.4, SHACK_EAVE + 0.5))] +
                         [(x, W / 2, SHACK_EAVE + 4.8) for x in (-1.2, L + 1.2)])
    # a coved soffit under the eaves, flaring from the walls at 45 degrees, so the roof's
    # overhang prints without support; it stays below the colour change (red)
    cove = M.hull_points([(x, y, SHACK_EAVE - 1.45) for x in (0.0, L) for y in (0.0, W)] +
                         [(x, y, SHACK_EAVE) for x in (-1.2, L + 1.2) for y in (-1.4, W + 1.4)])
    return (walls + battens - hatch - door) + shelf + cove + gable + roof


def lot_fence(L=36.0):
    """Split-rail lot fence: posts every 9 mm with two rails mortised through them."""
    posts = [box([x - 0.6, -0.6, 0.0], [x + 0.6, 0.6, 9.0]) for x in np.arange(0.6, L, 9.0)]
    rails = [box([0.0, -0.4, z], [L + 1.2, 0.4, z + 0.9]) for z in (3.4, 7.0)]
    return union(posts + rails)


# ================================================================== telephone poles
def telephone_pole(h=ft(30.0), r0=inch(5.2), r1=inch(4.0), steps=True):
    """A creosoted pole printed upright on a small bed disc: tapering, with a spigot on top that
    the crossarm's socket drops over, and pole steps up the sides from 8 ft."""
    pole = M.cylinder(h, r0, r1, 28)
    foot = M.cylinder(0.6, r0 + 1.6, r0 + 0.4, 28)
    spig = M.cylinder(1.4, 0.45, 0.45, 16).translate([0, 0, h - 0.01])
    parts = [pole, foot, spig]
    if steps:
        for k, z in enumerate(np.arange(ft(8.0), h - ft(3.0), ft(1.5))):
            a = 0 if k % 2 else 180
            rr = r0 + (r1 - r0) * z / h
            # a wedge step: its underside rises at 45 degrees from the pole, so it prints unsupported
            parts.append(M.hull_points([(rr - 0.25, y, z - 0.6) for y in (-0.22, 0.22)] + [(rr + 0.6, y, z) for y in (-0.22, 0.22)] +
                                       [(x, y, z + 0.25) for x in (rr - 0.25, rr + 0.6) for y in (-0.22, 0.22)]).rotate([0, 0, a]))
    return union(parts)


def crossarm(n=4, L=ft(8.0)):
    """A crossarm printed on its underside: the arm to ARM_TOP with a socket for the pole's spigot,
    then pins and glass insulators above it in the insulator colour."""
    w = inch(4.0)
    arm = _rbox(-L / 2, -w / 2, 0.0, L / 2, w / 2, ARM_TOP, 0.12) + _rbox(-1.2, -1.15, 0.0, 1.2, 1.15, ARM_TOP, 0.12)
    arm = arm - M.cylinder(3.0, 0.55, 0.55, 16).translate([0, 0, -1.0])
    xs = [(-L / 2 + 0.9) + (L - 1.8) * k / (n - 1) for k in range(n)]
    xs = [x for x in xs if abs(x) > 1.4] if n % 2 == 0 else xs
    ins = []
    for x in xs:
        ins.append(M.cylinder(0.5, 0.32, 0.32, 12).translate([x, 0, ARM_TOP - 0.01]))
        ins.append(_revolve([(0.0, ARM_TOP + 0.45), (0.55, ARM_TOP + 0.45), (0.7, ARM_TOP + 0.75), (0.6, ARM_TOP + 1.2),
                             (0.45, ARM_TOP + 1.6), (0.0, ARM_TOP + 1.7)], 16).translate([x, 0, 0]))
    return arm + union(ins)


def transformer():
    """A pole-top transformer can, printed upright: the tank with cooling ribs, a lid, two
    bushings, and a saddle at the back shaped to the pole for a full glue face."""
    r, h = 2.3, 6.4
    tank = M.cylinder(h, r, r, 32)
    ribs = union([box([r - 0.2, -0.12, 0.6], [r + 0.3, 0.12, h - 0.8]).rotate([0, 0, a]) for a in range(20, 170, 25)])
    lid = M.cylinder(0.5, r + 0.2, r + 0.2, 32).translate([0, 0, h - 0.01]) + M.cylinder(0.4, r * 0.7, 0.4, 24).translate([0, 0, h + 0.49])
    bush = union([M.cylinder(1.0, 0.3, 0.25, 12).translate([x, 0.4, h + 0.4]) for x in (-0.9, 0.9)])
    pr = inch(4.6)
    saddle = box([-1.4, -r - 1.6, 1.0], [1.4, -r + 0.3, h - 1.0]) - M.cylinder(h + 2, pr, pr, 28).translate([0, -r - 1.6 - pr + 0.5, 0])
    return tank + ribs + lid + bush + saddle

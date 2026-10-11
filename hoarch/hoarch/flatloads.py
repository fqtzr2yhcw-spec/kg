"""Flatcar loads: freight that rides on HO flatcars. As with the detail packs, each piece prints
in its colours, with at most one filament change at a height its plate shares, and needs no
supports. Local z is up from the bed; HO sizes.

The stand-in cars at the bottom are for the renders only (the cars are not sold): plain
flatcars at the usual HO sizes, so a buyer sees how a load sits on the car they have."""
import math

import numpy as np
from manifold3d import CrossSection as CS, Manifold as M

from manifold3d import JoinType

from .core import box, circle, cs_union, ft, offset, poly, union
from .ornament import ext

# change heights (the colour above starts here)
XF_BLOCK = 2.0            # transformer: timber cribbing, then the tank
TARP_BLOCK = 2.0          # tarped loads: timber blocking, then the tarp
PIPE_DUN = 1.4            # line pipe: dunnage strips, then the pipe


BED_SHEET = 0.6          # every load's footprint is filled at the bed, three layers thick


def _sheeted(fn):
    """Fill the gaps between a load's feet (timbers, dunnage, skid beams, frame members) with a
    sheet BED_SHEET thick, in its base colour, kept 0.3 mm inside the feet's outline. Loads
    standing on their blocking alone touched the plate with 6 to 29 % of their footprint, and
    the nacelle's ends lifted off a cool plate as the housing above shrank."""
    import functools

    @functools.wraps(fn)
    def wrapped(*a, **k):
        m = fn(*a, **k)
        feet = m.slice(0.05)
        if feet.is_empty():
            return m
        filled = feet.offset(15.0, JoinType.Round).offset(-15.0, JoinType.Round)    # closes gaps under 30 mm
        sheet = ext(filled.offset(-0.3, JoinType.Miter) + feet, 0.0, BED_SHEET)
        m = m + sheet
        voids = [c.hull() for c in m.decompose() if c.volume() < 0]          # pockets sealed under the load: fill them
        return union([m] + voids) if voids else m
    return wrapped


def _seg(a, b, w):
    """A 2D member of width w from a to b, with round ends."""
    return cs_union([circle(a, w / 2, 16), circle(b, w / 2, 16)]).hull()


# ================================================================== wind tower section
TOWER_L = 245.0                       # about 70 ft of tower: stands within a 256 mm build height
TOWER_R0 = ft(13.1) / 2               # 4.0 m at the big end
TOWER_R1 = ft(11.8) / 2               # 3.6 m at the small end
TOWER_T = 1.2
TOWER_FLANGE = 3.0                    # the bolting flange inside each end
TOWER_GAP = ft(1.0)                   # the tower's underside clears the deck by a foot


def tower_section(L=TOWER_L, r0=TOWER_R0, r1=TOWER_R1, t=TOWER_T):
    """A tapered steel wind tower section, printed upright on its big end: a 1.2 mm shell rolled
    in cans 3 m long, each can with its longitudinal seam (staggered), raised girth welds between
    the cans, and an L-flange inside each end for the bolts (the top flange has a 45 degree
    underside). The transport frames glue onto the end faces."""
    seg = 144
    r = lambda z: r0 + (r1 - r0) * z / L
    shell = M.cylinder(L, r0, r1, seg) - M.cylinder(L + 2.0, r0 - t, r1 - t, seg).translate([0, 0, -1.0])
    fw, fh = TOWER_FLANGE, 1.6
    ri0, ri1 = r0 - t, r1 - t
    bot = M.revolve(poly([(ri0 - fw, 0.0), (ri0 + 0.3, 0.0), (ri0 + 0.3, fh + 0.4), (ri0, fh + 0.4), (ri0 - fw, fh)]), seg)
    top = M.revolve(poly([(ri1 - fw, L), (ri1 + 0.3, L), (ri1 + 0.3, L - fh - fw), (ri1, L - fh - fw), (ri1 - fw, L - fh)]), seg)
    parts = [shell, bot, top]
    can = ft(9.84)
    n = int(round(L / can))
    can = L / n
    for k in range(n):
        z0, z1 = k * can, (k + 1) * can
        if k:                                                   # girth weld, 45 degrees underneath
            rz = r(z0)
            parts.append(M.revolve(poly([(rz - 0.2, z0 - 0.45), (rz + 0.14, z0 - 0.25), (rz + 0.14, z0 + 0.25), (rz - 0.2, z0 + 0.25)]), seg))
        a = math.radians(35 + 150 * (k % 2) + 40 * (k % 3))    # long seams staggered round the shell
        c, s = math.cos(a), math.sin(a)
        pts = []
        for z in (z0 + 0.3, z1 - 0.3):
            for dr in (-0.3, 0.1):
                for dt in (-0.25, 0.25):
                    rr = r(z) + dr
                    pts.append((rr * c - dt * s, rr * s + dt * c, z))
        parts.append(M.hull_points(pts))
    return union(parts)


def tower_frame(r_end, r_big=TOWER_R0, W=ft(9.8), gap=TOWER_GAP):
    """A transport frame for one end of the tower, printed flat. In print coordinates u runs
    across the car, v up from the tower's axis and w out from the tower's end face (print z).
    A bolting ring (its flat side glues to the tower end), a base beam whose foot plate stands
    on the deck, two raking legs and a centre post. Every member has flanged edges like rolled
    sections, and a ring of bolt heads."""
    ro, rin = r_end + 0.6, r_end - TOWER_T - TOWER_FLANGE + 0.6
    vb = -(r_big + gap)                 # the deck, below the tower's axis
    bh = 3.0
    ring = circle((0, 0), ro, 96) - circle((0, 0), rin, 96)
    beam = CS.square((W, bh)).translate((-W / 2, vb))
    members = [ring, beam]
    for side in (-1, 1):
        a = math.radians(270 + side * 52)
        p = (r_end * math.cos(a), r_end * math.sin(a))
        members.append(_seg(p, (side * (W / 2 - 1.4), vb + bh - 0.6), 2.4))
    members.append(_seg((0, -r_end + 1.0), (0, vb + bh - 0.6), 2.2))
    cs = cs_union(members)
    plate = ext(cs, 0.0, 1.2)
    rims = ext(cs - offset(cs, -0.5), 1.19, 2.0)
    bolts = [M.cylinder(0.4, 0.38, 0.3, 10).translate([(r_end - 1.5) * math.cos(a), (r_end - 1.5) * math.sin(a), 1.19])
             for a in np.linspace(0, 2 * math.pi, 24, endpoint=False)]
    foot = box([-W / 2, vb, 0.0], [W / 2, vb + 0.8, 4.6])
    gussets = [M.hull_points([(u + du, vb + 0.79, 1.19), (u + du, vb + bh, 1.19), (u + du, vb + 0.79, 4.2)])
               for u in (-W / 2 + 0.6, -W / 4, W / 4, W / 2 - 0.6) for du in (-0.35, 0.35)]
    return union([plate, rims, foot] + bolts + gussets)


# ================================================================== power transformer
def _crect(x0, y0, x1, y1, c, z):
    return [(x0 + c, y0, z), (x1 - c, y0, z), (x1, y0 + c, z), (x1, y1 - c, z),
            (x1 - c, y1, z), (x0 + c, y1, z), (x0, y1 - c, z), (x0, y0 + c, z)]


def _belt(x0, y0, x1, y1, c, z, d, h):
    """A band round a chamfered tank, d proud and h tall above z, with a 45 degree underside."""
    return M.hull_points(_crect(x0, y0, x1, y1, c, z - d - 0.2) +
                         _crect(x0 - d, y0 - d, x1 + d, y1 + d, c + d * 0.4, z) +
                         _crect(x0 - d, y0 - d, x1 + d, y1 + d, c + d * 0.4, z + h))


@_sheeted
def transformer(L=ft(22.0), W=ft(8.5)):
    """A large power transformer as it travels: the main tank only, with the radiators,
    conservator and bushings taken off and their openings blanked. On timber cribbing (to
    XF_BLOCK), a heavy base skid with jacking pads and pulling eyes, a stiffened tank with a
    bolted cover flange, blanked high- and low-voltage turrets, manholes, lifting lugs, the
    blanked radiator flanges down both sides, an impact recorder, and a dry-nitrogen bottle on
    a bracket at one end that keeps the tank under pressure on the road."""
    c = 1.2
    z0 = XF_BLOCK + 1.4                          # skid top: the tank starts here
    zt = z0 + ft(9.6)                            # cover top
    parts = []
    # cribbing (brown) and the skid
    for x in np.linspace(-1.4 + 1.75, L + 1.4 - 1.75, 4):           # the end timbers carry the skid's ends
        parts.append(box([x - 1.75, -2.2, 0.0], [x + 1.75, W + 2.2, XF_BLOCK]))
    parts.append(box([-1.0, -0.6, XF_BLOCK - 0.01], [L + 1.0, W + 0.6, z0]))
    for x0, sgn in ((-1.0, -1), (L + 1.0, 1)):            # pulling eyes, 45 degrees under
        for y in (W * 0.25, W * 0.75):
            eye = M.hull_points([(x0, y + dy, z) for dy in (-1.3, 1.3) for z in (XF_BLOCK + 0.01, z0)] +
                                [(x0 + sgn * 1.4, y + dy, z0) for dy in (-1.3, 1.3)])
            parts.append(eye - M.cylinder(0.5, 0.45, 0.45, 12).translate([x0 + sgn * 0.75, y, z0 - 0.3]))
    # tank, cover flange and a mid-height stiffening belt
    parts.append(M.hull_points(_crect(0, 0, L, W, c, z0 - 0.01) + _crect(0, 0, L, W, c, zt)))
    parts.append(_belt(0, 0, L, W, c, zt - 2.0, 0.6, 0.8))
    parts.append(_belt(0, 0, L, W, c, z0 + ft(5.0), 0.35, 0.6))
    # jacking pads at the corners, standing on the skid
    for xa, xb in ((-0.9, 0.01), (L - 0.01, L + 0.9)):
        for ya, yb in ((0.2, 2.4), (W - 2.4, W - 0.2)):
            parts.append(box([xa, ya, z0 - 0.01], [xb, yb, z0 + 2.0]))
    # vertical stiffeners (channels) up the sides and ends, stopping under the cover flange
    zs1 = zt - 2.6
    xs = np.linspace(L * 0.08, L * 0.92, 7)
    for x in xs:
        for y0, y1 in ((-0.6, 0.01), (W - 0.01, W + 0.6)):
            parts.append(box([x - 0.6, y0, z0], [x + 0.6, y1, zs1]))
    for y in (W * 0.3, W * 0.7):
        for x0, x1 in ((-0.6, 0.01), (L - 0.01, L + 0.6)):
            parts.append(box([x0, y - 0.6, z0], [x1, y + 0.6, zs1]))
    # blanked radiator flanges between the stiffeners, top and bottom, on both sides
    def disc_y(x, y, z, r, d, sgn):
        """A round boss d proud of the side wall at y (sgn: which way is out)."""
        cyl = M.cylinder(d + 0.3, r, r, 16).rotate([-90, 0, 0])
        return cyl.translate([x, y - 0.3, z]) if sgn > 0 else cyl.translate([x, y - d, z])
    for x in (xs[:-1] + xs[1:]) / 2:
        for z in (z0 + ft(1.8), zt - ft(2.6)):
            for y, sgn in ((0.0, -1), (W, 1)):
                parts.append(disc_y(x, y, z, 1.3, 0.5, sgn))
                parts.append(disc_y(x, y, z, 0.9, 0.85, sgn))
    # on the cover: three blanked HV turrets, four LV turrets, two manholes, four lifting lugs
    for x in (L * 0.28, L * 0.5, L * 0.72):
        parts.append(M.cylinder(2.4, 2.3, 2.3, 32).translate([x, W * 0.32, zt - 0.01]))
        parts.append(M.cylinder(0.6, 2.85, 2.85, 32).translate([x, W * 0.32, zt + 2.3]))
        parts.append(M.cylinder(0.55, 2.3, 2.85, 32).translate([x, W * 0.32, zt + 1.75]))   # 45 degrees under the flange
    for x in np.linspace(L * 0.2, L * 0.8, 4):
        parts.append(M.cylinder(1.4, 1.2, 1.2, 24).translate([x, W * 0.76, zt - 0.01]))
        parts.append(M.cylinder(0.4, 1.5, 1.5, 24).translate([x, W * 0.76, zt + 1.3]))
        parts.append(M.cylinder(0.3, 1.2, 1.5, 24).translate([x, W * 0.76, zt + 1.0]))
    for x in (L * 0.12, L * 0.88):
        parts.append(M.cylinder(0.45, 2.0, 2.0, 32).translate([x, W * 0.5, zt - 0.01]))
    for x in (1.6, L - 1.6):
        for y in (1.2, W - 1.2):
            lug = M.hull(box([x - 1.4, y - 0.45, zt - 0.01], [x + 1.4, y + 0.45, zt + 1.6]) +
                         M.cylinder(0.9, 1.4, 1.4, 20).rotate([90, 0, 0]).translate([x, y + 0.45, zt + 1.6]))
            hole = M.cylinder(2.0, 0.6, 0.6, 12).rotate([90, 0, 0]).translate([x, y + 1.0, zt + 1.6])
            parts.append(lug - hole)
    # impact recorder and drain valve on the front, nameplate on the far end
    parts.append(M.hull_points([(x, y, z) for x in (L * 0.62, L * 0.62 + 4.0) for (y, z) in
                                ((0.01, z0 + 3.0), (-1.1, z0 + 4.1), (-1.1, z0 + 6.4), (0.01, z0 + 6.4))]))
    parts.append(M.cylinder(1.0, 0.7, 0.7, 14).rotate([90, 0, 0]).translate([L * 0.9, 0.3, z0 + 1.6]))
    parts.append(box([-0.15, W * 0.35, z0 + ft(6.0)], [0.01, W * 0.65, z0 + ft(7.2)]))
    # dry-nitrogen bottle on its bracket at the x = L end
    by, bz = W * 0.68, z0 + 3.2
    bx = L + 2.2
    parts.append(M.hull_points([(L - 0.01, by + dy, z) for dy in (-1.8, 1.8) for z in (z0 - 0.01, bz)] +
                               [(L + 1.0, by + dy, z0 - 0.01) for dy in (-1.8, 1.8)] +
                               [(L + 3.8, by + dy, z) for dy in (-1.8, 1.8) for z in (z0 + 2.8, bz)]))
    h = ft(4.4)
    parts.append(M.cylinder(h, 1.45, 1.45, 28).translate([bx, by, bz - 0.01]))
    parts.append(M.sphere(1.45, 28).translate([bx, by, bz + h]) - box([bx - 3, by - 3, bz + h - 3], [bx + 3, by + 3, bz + h - 0.05]))
    parts.append(M.cylinder(1.0, 0.45, 0.45, 12).translate([bx, by, bz + h + 1.2]))
    for z in (bz + 3.0, bz + h - 2.5):
        parts.append(M.cylinder(0.6, 1.65, 1.65, 28).translate([bx, by, z]))
        parts.append(box([L - 0.01, by - 0.4, z], [bx, by + 0.4, z + 0.6]))
    parts.append(M.hull_points([(L - 0.01, y, z) for y in (by - 3.2, by - 1.9) for z in (bz + h - 2.2, bz + h + 1.0)] +
                               [(L + 1.2, y, z) for y in (by - 3.2, by - 1.9) for z in (bz + h - 1.0, bz + h + 1.0)]))   # regulator
    return union(parts)


# ================================================================== tarped loads
def _tbox(x0, y0, z0, x1, y1, z1, r, flare=0.0):
    """A tarp-covered block: flat bottom at z0 (flared out by ``flare``), rounded top edges."""
    pts = [(x, y, z0) for x in (x0 - flare, x1 + flare) for y in (y0 - flare, y1 + flare)]
    sph = [M.sphere(r, 16).translate([x, y, z1 - r]) for x in (x0 + r, x1 - r) for y in (y0 + r, y1 - r)]
    return M.hull_points(pts + [tuple(v) for s in sph for v in s.to_mesh().vert_properties[:, :3]])


TARPS = {
    # hulls of rounded blocks (x0, y0, x1, y1, height); each list is hulled, the hulls unioned
    "machine": [[(0, 0, 54, 24, 12.5)], [(30, 3, 54, 21, 21.0), (24, 3, 30, 21, 12.5)],
                [(5, 6, 18, 18, 16.5)]],
    "long": [[(0, 0, 128, 22, 9.5)], [(14, 3, 40, 19, 11.5)], [(84, 3, 112, 19, 11.0)]],
    "tall": [[(0, 0, 30, 24, 22.0), (8, 6, 22, 18, 27.0)]],
}


def _tarp_body(kind, grow=0.0):
    z0 = TARP_BLOCK
    hulls = []
    for g, grp in enumerate(TARPS[kind]):
        bodies = [_tbox(x0 - grow, y0 - grow, z0, x1 + grow, y1 + grow, z0 + h + grow, 1.6 + grow, 0.7 if g == b == 0 else 0.0)
                  for b, (x0, y0, x1, y1, h) in enumerate(grp)]
        hulls.append(union(bodies).hull())
    return union(hulls)


@_sheeted
def tarp_load(kind, seed=3):
    """A load under a lashed tarpaulin on timber blocking (to TARP_BLOCK). The cloth hangs to
    the blocking with a flare and a stitched hem, folds run down its sides and gather at the
    corners, and ropes cross it at intervals. ``kind``: machine, long or tall."""
    rng = np.random.default_rng(seed)
    z0 = TARP_BLOCK
    body = _tarp_body(kind)
    x0, y0, _, x1, y1, _ = body.bounding_box()
    base = TARPS[kind][0][0]
    bx0, by0, bx1, by1, bh = base
    parts = [body]
    # folds: ridges standing out most at the hem, fading up the side
    for (ya, out) in ((by0, -1), (by1, 1)):
        x = bx0 + rng.uniform(2.0, 4.0)
        while x < bx1 - 2.0:
            top = z0 + bh * rng.uniform(0.45, 0.9)
            d, w = rng.uniform(0.35, 0.6), rng.uniform(1.2, 2.0)
            yf = ya + out * 0.7                           # the flared hem line
            parts.append(M.hull_points([(x - w / 2, yf - out * 0.6, z0), (x + w / 2, yf - out * 0.6, z0), (x, yf + out * d, z0),
                                        (x, ya + out * 0.02, top), (x - 0.05, ya - out * 0.3, top)]))
            x += rng.uniform(4.0, 9.0)
    for (xa, out) in ((bx0, -1), (bx1, 1)):
        y = by0 + rng.uniform(3.0, 5.0)
        while y < by1 - 3.0:
            top = z0 + bh * rng.uniform(0.45, 0.85)
            d, w = rng.uniform(0.35, 0.55), rng.uniform(1.2, 1.8)
            xf = xa + out * 0.7
            parts.append(M.hull_points([(xf - out * 0.6, y - w / 2, z0), (xf - out * 0.6, y + w / 2, z0), (xf + out * d, y, z0),
                                        (xa + out * 0.02, y, top), (xa - out * 0.3, y - 0.05, top)]))
            y += rng.uniform(5.0, 8.0)
    # gathered corners: a diagonal fold from each top corner to the hem
    for cx, sx in ((bx0, -1), (bx1, 1)):
        for cy, sy in ((by0, -1), (by1, 1)):
            parts.append(M.hull_points([(cx - sx * 1.6, cy - sy * 1.6, z0 + bh - 0.8), (cx - sx * 1.0, cy - sy * 1.0, z0 + bh - 2.0),
                                        (cx + sx * 1.3, cy + sy * 1.3, z0), (cx + sx * 0.7 - sx * 3.0, cy + sy * 0.7, z0),
                                        (cx + sx * 0.7, cy + sy * 0.7 - sy * 3.0, z0)]))
    body = union(parts)
    # hem: a stitched band round the bottom
    hem = _tarp_body(kind, 0.15) ^ box([x0 - 3, y0 - 3, z0], [x1 + 3, y1 + 3, z0 + 0.6])
    # ropes across the load; between them the cloth bulges out, pinched in at each rope
    n = max(2, int((bx1 - bx0) / 22.0) + 1)
    xr = [bx0 + (bx1 - bx0) * (k + 0.5) / n + rng.uniform(-2.0, 2.0) for k in range(n)]
    bulge = []
    for xa, xb in zip(xr[:-1], xr[1:]):
        steps = 7
        for i in range(steps):
            g = 0.4 * math.sin(math.pi * (i + 0.5) / steps)
            bulge.append(_tarp_body(kind, g) ^ box([xa + (xb - xa) * i / steps, y0 - 3, z0], [xa + (xb - xa) * (i + 1) / steps + 0.01, y1 + 3, z0 + 40]))
    grown = _tarp_body(kind, 0.42)
    ropes = [grown ^ box([x - 0.35, y0 - 3, z0], [x + 0.35, y1 + 3, z0 + 40]) for x in xr]
    if kind == "tall":                                    # and round it, near the top
        ropes.append(grown ^ box([x0 - 3, y0 - 3, z0 + bh - 6.0], [x1 + 3, y1 + 3, z0 + bh - 5.3]))
    ropes += bulge
    lashing = union([hem] + ropes)
    # blocking under it, standing out either side
    blocks = [box([x - 1.75, by0 - 2.6, 0.0], [x + 1.75, by1 + 2.6, z0])      # the end ones carry the gathered corners
              for x in np.linspace(bx0 - 1.5 + 1.75, bx1 + 1.5 - 1.75, max(2, int((bx1 - bx0) / 26.0) + 2))]
    return union([body, lashing] + blocks)


# ================================================================== line pipe
@_sheeted
def pipe_load(r=ft(1.5), L=ft(40.0), rows=(3, 2)):
    """Coated line pipe, 40 ft joints, stacked three and two on dunnage (to PIPE_DUN) and banded.
    The ends wear bevel protectors. Printed lying: each bottom pipe sits on a 45 degree keel
    and each upper pipe on a web down into its valley, both hidden in the stack and stopping
    short of the ends, so the round ends show and nothing hangs past 45 degrees."""
    s2 = math.sqrt(0.5)
    zl = PIPE_DUN + r
    centres = [(r + 2 * r * k, zl) for k in range(rows[0])]
    zu = zl + r * math.sqrt(3)
    centres += [(2 * r + 2 * r * k, zu) for k in range(rows[1])]
    keel = []
    for (y, z) in centres[:rows[0]]:
        dz = z - s2 * r - PIPE_DUN
        keel.append(poly([(y - s2 * r, z - s2 * r), (y + s2 * r, z - s2 * r), (y + s2 * r - dz, PIPE_DUN - 0.01),
                          (y - s2 * r + dz, PIPE_DUN - 0.01)]))
    for (y, z) in centres[rows[0]:]:
        keel.append(poly([(y - s2 * r, z - s2 * r), (y + s2 * r, z - s2 * r), (y, zl)]))
    pipes_cs = cs_union([circle(c, r, 64) for c in centres])
    end = 0.4

    def along_x(cs, xa, xb):
        """Extrude a (y, z) section between x = xa and xb."""
        return M.extrude(cs, xb - xa).transform(np.array([[0, 0, 1, xa], [1, 0, 0, 0], [0, 1, 0, 0]], float))

    pipes = along_x(pipes_cs, 0.0, L) + along_x(cs_union(keel), end, L - end)
    # bevel protectors: a lipped cap on each end, dished in the middle
    caps = []
    for (y, z) in centres:
        lip = (circle((y, z), r + 0.2, 64) - circle((y, z), r - 0.01, 64)) ^ CS.square((4 * r, 4 * r)).translate((y - 2 * r, z - 0.3 * r))
        for xa, xb, xd in ((-0.5, 0.0, -0.51), (L, L + 0.5, L + 0.31)):
            cap = along_x(circle((y, z), r, 64) + lip, xa - 0.01 * (xa > 0), xb + 0.01 * (xa < 0))
            dish = along_x(circle((y, z), r - 1.1, 48), xd, xd + 0.2)
            caps.append(cap - dish)
    # steel banding round the stack over each dunnage strip
    hull = cs_union([pipes_cs] + keel).hull()
    band_cs = offset(hull, 0.4) - offset(hull, -0.05)
    xs = [1.2, L * 0.21, L * 0.4, L * 0.6, L * 0.79, L - 1.2]     # end strips carry the pipe ends; spans under 30 mm
    bands = [along_x(band_cs, x - 0.3, x + 0.3) - box([x - 1, -5, -5], [x + 1, 6 * r + 5, PIPE_DUN]) for x in xs[::5] + xs[2:4]]
    dun = [box([x - 0.7, -1.4, 0.0], [x + 0.7, 2 * r * rows[0] + 1.4, PIPE_DUN]) for x in xs]
    return union([pipes] + caps + bands + dun)


# ================================================================== wind turbine nacelle and hub
NAC_FRAME = 3.0           # nacelle and hub: yellow transport frame or stand, then the white casting


@_sheeted
def nacelle(L=105.0, W=36.0, H=40.0):
    """A wind turbine nacelle on its transport frame (yellow, to NAC_FRAME): a GRP housing with
    rounded roof edges, tapering to the nose, with panel seams, a roof hatch, louvred intakes
    at the rear, lifting points, and the main-shaft flange the hub bolts to on a cast bearing
    housing (45 degrees underneath). The frame is flush with the housing so nothing overhangs."""
    z0 = NAC_FRAME
    rr = 6.0
    parts = []
    # frame: perimeter beams, cross beams, corner feet and tie-down lugs
    fb = 2.2
    for (x0, y0, x1, y1) in ((0, 0, L, fb), (0, W - fb, L, W), (0, 0, fb, W), (L - fb, 0, L, W),
                             (L * 0.33 - fb / 2, 0, L * 0.33 + fb / 2, W), (L * 0.66 - fb / 2, 0, L * 0.66 + fb / 2, W),
                             (0, W / 2 - fb / 2, L, W / 2 + fb / 2)):
        parts.append(box([x0, y0, 0.0], [x1, y1, z0 + 0.01]))
    for x in (6.0, L - 6.0):
        for y, sgn in ((0.0, -1), (W, 1)):
            parts.append(M.hull_points([(x + dx, y, z) for dx in (-1.6, 1.6) for z in (0.0, z0)] +
                                       [(x + dx, y + sgn * 1.4, z) for dx in (-1.6, 1.6) for z in (0.0, 1.4)]))
    # housing: cross-section with rounded roof edges, swept nose
    def section(x, w, h):
        pts = [(x, 0.0 + (W - w) / 2, z0), (x, W - (W - w) / 2, z0)]
        for k in range(9):
            a = math.pi / 2 * k / 8
            pts.append((x, W - (W - w) / 2 - rr + rr * math.cos(a), z0 + h - rr + rr * math.sin(a)))
            pts.append((x, (W - w) / 2 + rr - rr * math.cos(a), z0 + h - rr + rr * math.sin(a)))
        return pts
    body = M.hull_points(section(0.0, W, H) + section(L - 14.0, W, H))
    nose = M.hull_points(section(L - 14.01, W, H) + section(L, W - 6.0, H - 7.0))
    housing = body + nose
    # panel seams and a belt seam, sunk 0.2
    seams = []
    for ya, yb in ((-1.0, 0.2), (W - 0.2, W + 1.0)):
        seams += [box([x - 0.2, ya, z0 + 1.0], [x + 0.2, yb, z0 + H - rr]) for x in np.arange(15.0, L - 14.0, 15.0)]
        seams.append(box([0.6, ya, z0 + H * 0.45 - 0.2], [L - 14.6, yb, z0 + H * 0.45 + 0.2]))
    housing = housing - union(seams)
    parts.append(housing)
    # roof hatch and lifting points
    parts.append(box([L * 0.35, W * 0.3, z0 + H - 0.01], [L * 0.35 + 12.0, W * 0.7, z0 + H + 0.5]))
    for x in (L * 0.15, L * 0.75):
        for y in (W * 0.3, W * 0.7):
            lug = M.hull(box([x - 1.2, y - 0.4, z0 + H - 0.01], [x + 1.2, y + 0.4, z0 + H + 1.4]) +
                         M.cylinder(0.8, 1.2, 1.2, 18).rotate([90, 0, 0]).translate([x, y + 0.4, z0 + H + 1.4]))
            parts.append(lug - M.cylinder(2.0, 0.5, 0.5, 12).rotate([90, 0, 0]).translate([x, y + 1.0, z0 + H + 1.4]))
    # louvred intakes: slats with 45 degree undersides on the rear end and both sides near it
    def slats(x0, x1, y0, y1, zlo, zhi, out):
        s = []
        for z in np.arange(zlo, zhi, 1.2):
            if out == "x":
                s.append(M.hull_points([(x0, y, z) for y in (y0, y1)] + [(x0 - 0.5, y, z + 0.5) for y in (y0, y1)] +
                                       [(x0, y, z + 0.8) for y in (y0, y1)] + [(x0 - 0.5, y, z + 0.8) for y in (y0, y1)]))
            else:
                sg = -1 if out == "-y" else 1
                s.append(M.hull_points([(x, y0, z) for x in (x0, x1)] + [(x, y0 + sg * 0.5, z + 0.5) for x in (x0, x1)] +
                                       [(x, y0, z + 0.8) for x in (x0, x1)] + [(x, y0 + sg * 0.5, z + 0.8) for x in (x0, x1)]))
        return s
    parts += slats(0.01, 0, W * 0.2, W * 0.8, z0 + 8.0, z0 + H - 10.0, "x")
    parts += slats(4.0, 16.0, 0.01, 0, z0 + 10.0, z0 + 22.0, "-y")
    parts += slats(4.0, 16.0, W - 0.01, 0, z0 + 10.0, z0 + 22.0, "+y")
    # main bearing housing and shaft flange at the nose, 45 degrees under
    zc = z0 + H * 0.55
    rf = 9.0
    disc = M.cylinder(4.0, rf, rf, 48).rotate([0, 90, 0]).translate([L - 0.01, W / 2, zc])
    flange = M.cylinder(1.0, rf + 0.8, rf + 0.8, 48).rotate([0, 90, 0]).translate([L + 3.99, W / 2, zc])
    keel = M.hull(disc + flange + box([L - 0.01, W / 2 - rf, zc - rf - 6.0], [L, W / 2 + rf, zc]))
    face = M.cylinder(0.6, rf - 3.0, rf - 3.0, 40).rotate([0, 90, 0]).translate([L + 4.6, W / 2, zc])
    studs = [M.cylinder(0.5, 0.35, 0.35, 8).rotate([0, 90, 0]).translate([L + 4.95, W / 2 + (rf - 1.2) * math.cos(a), zc + (rf - 1.2) * math.sin(a)])
             for a in np.linspace(0, 2 * math.pi, 20, endpoint=False)]
    parts += [keel - face] + studs
    return union(parts)


def hub(R=21.0):
    """A cast rotor hub on its transport stand (yellow, to NAC_FRAME), main-shaft flange down: a
    45 degree waist rising from the flange into the spherical body, three flat-faced blade
    flanges with bolting rings, studs and bores, and the spinner flange on top."""
    z0 = NAC_FRAME
    zf = z0 + 1.6                                  # top of the main-shaft flange
    zc = zf + R * 0.75
    stand = [box([-15, -15, 0.0], [15, 15, 1.0]),
             M.cylinder(z0 - 0.99, 13.0, 13.0, 48).translate([0, 0, 0.99])]
    for a in range(45, 360, 90):
        stand.append(M.hull_points([(13.0, -0.5, 1.0), (13.0, 0.5, 1.0), (13.0, -0.5, z0 - 0.2), (13.0, 0.5, z0 - 0.2),
                                    (15.0, -0.5, 1.0), (15.0, 0.5, 1.0)]).rotate([0, 0, a]))
    flange = M.cylinder(1.6, 12.0, 12.0, 64).translate([0, 0, z0 - 0.01])
    h = 2 * R
    waist = M.cylinder(h, 11.4, 11.4 + h, 72).translate([0, 0, zf - 0.01])      # 45 degrees out from the flange
    body = M.sphere(R, 72).translate([0, 0, zc]) ^ waist
    body = body - box([-40, -40, zc + R - 4.0], [40, 40, zc + R + 5])
    d = R - 4.0
    rings, bores = [], []
    for k in range(3):
        a = 90 + 120 * k
        body = body - box([d, -R - 5, zc - R - 5], [d + 30, R + 5, zc + R + 5]).rotate([0, 0, a])
        ring = (M.cylinder(0.7, 11.0, 11.0, 48) - M.cylinder(2.0, 8.5, 8.5, 48).translate([0, 0, -1])).rotate([0, 90, 0]).translate([d - 0.01, 0, zc])
        studs = [M.cylinder(0.4, 0.3, 0.3, 8).rotate([0, 90, 0]).translate([d + 0.68, 9.8 * math.cos(t), zc + 9.8 * math.sin(t)])
                 for t in np.linspace(0, 2 * math.pi, 18, endpoint=False)]
        rings.append((ring + union(studs)).rotate([0, 0, a]))
        bores.append(M.cylinder(2.0, 6.5, 6.5, 40).rotate([0, 90, 0]).translate([d - 1.6, 0, zc]).rotate([0, 0, a]))
    spinner = M.cylinder(0.8, 10.0, 10.0, 48).translate([0, 0, zc + R - 4.01]) - M.cylinder(1.0, 8.0, 8.0, 48).translate([0, 0, zc + R - 3.6])
    reach = M.cylinder(h, 12.1, 12.1 + h, 72).translate([0, 0, zf - 0.01])        # rings stand at most 0.7 off the waist
    return union(stand + [flange, body - union(bores), spinner] + [rg ^ reach for rg in rings])


# ================================================================== steel mill loads
STEEL_DUN = 1.4           # steel loads: wood skids and dunnage, then the steel


def _skid(L, W, runners=3, gap=0.3, plank=2.4):
    """A timber skid to STEEL_DUN: runners under, planks across on top."""
    ph = 0.6
    parts = [box([0, y - 1.1, 0.0], [L, y + 1.1, STEEL_DUN - ph + 0.01]) for y in np.linspace(1.1, W - 1.1, runners)]
    x = 0.0
    while x < L - 0.5:
        parts.append(box([x, 0, STEEL_DUN - ph], [min(x + plank, L), W, STEEL_DUN]))
        x += plank + gap
    return union(parts)


@_sheeted
def coil(od=ft(6.0), idia=ft(2.0), w=ft(5.0)):
    """A steel coil eye-to-sky on a timber skid: laps marked on its face, the outer wrap's end,
    an edge chamfer, four radial bands through the eye and two round it."""
    ro, ri = od / 2, idia / 2
    sk = ro * 2 + 2.0
    z0 = STEEL_DUN
    c = M.cylinder(w, ro, ro, 72) - M.cylinder(w + 2, ri, ri, 40).translate([0, 0, -1])
    c = c - (M.cylinder(0.4, ro + 1, ro + 1, 72).translate([0, 0, w - 0.4]) - M.cylinder(0.41, ro + 0.01, ro - 0.4, 72).translate([0, 0, w - 0.4]))
    laps = [M.cylinder(0.4, r + 0.15, r + 0.15, 72).translate([0, 0, w - 0.2]) - M.cylinder(0.6, r - 0.15, r - 0.15, 72).translate([0, 0, w - 0.3])
            for r in np.arange(ri + 1.0, ro - 0.8, 0.9)]
    c = c - union(laps)
    parts = [c.translate([0, 0, z0])]
    parts.append(M.hull_points([(ro - 0.05, -0.15, z0), (ro + 0.15, 0.0, z0), (ro - 0.05, 0.15, z0),
                                (ro - 0.05, -0.15, z0 + w), (ro + 0.15, 0.0, z0 + w), (ro - 0.05, 0.15, z0 + w)]).rotate([0, 0, 20]))
    for a in (45, 135, 225, 315):
        b = [box([ri - 0.2, -0.3, z0 + w - 0.01], [ro + 0.01, 0.3, z0 + w + 0.2]),
             box([ro - 0.01, -0.3, z0], [ro + 0.2, 0.3, z0 + w + 0.2]),
             box([ri - 0.2, -0.3, z0], [ri + 0.01, 0.3, z0 + w + 0.2])]
        parts.append(union(b).rotate([0, 0, a]))
    for z in (z0 + w * 0.3, z0 + w * 0.7):
        parts.append(M.cylinder(0.6, ro + 0.2, ro + 0.2, 72).translate([0, 0, z]) - M.cylinder(1.0, ro - 0.5, ro - 0.5, 72).translate([0, 0, z - 0.2]))
        parts.append(M.cylinder(0.2, ro, ro + 0.2, 72).translate([0, 0, z - 0.2]) - M.cylinder(1.0, ro - 0.5, ro - 0.5, 72).translate([0, 0, z - 0.5]))
    return union(parts + [_skid(sk, sk).translate([-sk / 2, -sk / 2, 0])])


@_sheeted
def plate_bundle(L=ft(20.0), W=ft(8.0), n=8, t=0.6):
    """A bundle of steel plate on dunnage: each plate's edge shows, the stack a little ragged,
    banded three times."""
    rng = np.random.default_rng(11)
    z = STEEL_DUN
    plates = []
    for k in range(n):
        dx, dy = rng.uniform(-0.25, 0.25, 2)
        plates.append(box([dx, dy, z], [L + dx, W + dy, z + t - 0.06]))
        plates.append(box([dx + 0.15, dy + 0.15, z + t - 0.07], [L + dx - 0.15, W + dy - 0.15, z + t + 0.01]))
        z += t
    stack = union(plates)
    bands = []
    for x in (L * 0.2, L * 0.5, L * 0.8):                       # bands stand on dunnage strips
        outer = box([x - 0.3, -0.45, STEEL_DUN], [x + 0.3, W + 0.45, z + 0.25])
        inner = box([x - 1, 0.3, STEEL_DUN - 1], [x + 1, W - 0.3, z])
        bands.append(outer - inner)
    dun = [box([x - 0.7, -1.2, 0.0], [x + 0.7, W + 1.2, STEEL_DUN]) for x in (1.2, L * 0.2, L * 0.5, L * 0.8, L - 1.2)]
    return union([stack] + bands + dun)


@_sheeted
def beam_bundle(L=ft(40.0), n=5, tiers=2, d=6.0, bf=3.0, tf=0.6, tw=0.45):
    """A bundle of wide-flange beams standing on their bottom flanges on dunnage, two tiers,
    banded. Inner flanges meet their neighbours' (the gap under them is a bridge); the outer
    flange tips reach 0.9 mm, a ledge."""
    parts = []
    z = STEEL_DUN
    for t in range(tiers):
        for k in range(n):
            y0 = k * bf
            yc = y0 + bf / 2
            lo, hi = (0.9 if k == 0 else bf / 2), (0.9 if k == n - 1 else bf / 2)
            parts.append(box([0, y0 + (bf / 2 - lo if k == 0 else 0.0), z], [L, y0 + bf - (bf / 2 - hi if k == n - 1 else 0.0), z + tf]))
            parts.append(box([0, yc - tw / 2, z + tf - 0.01], [L, yc + tw / 2, z + d - tf + 0.01]))
            parts.append(box([0, yc - lo, z + d - tf], [L, yc + hi, z + d]))
        z += d
    W = n * bf
    bands = []
    e = bf / 2 - 0.9                                            # where the outer flange tips are
    for x in (L / 6, L / 2, 5 * L / 6):                         # bands stand on dunnage strips
        outer = box([x - 0.3, e - 0.4, STEEL_DUN], [x + 0.3, W - e + 0.4, z + 0.3])
        inner = box([x - 1, e + 0.05, STEEL_DUN - 1], [x + 1, W - e - 0.05, z])
        bands.append(outer - inner)
    dun = [box([x - 0.7, -1.2, 0.0], [x + 0.7, W + 1.2, STEEL_DUN]) for x in (1.2, L / 6, L / 3, L / 2, 2 * L / 3, 5 * L / 6, L - 1.2)]
    return union(parts + bands + dun)


# ================================================================== pressure vessel
VESSEL_SKID = 2.0         # pressure vessel: skid beams' top
VESSEL_R = 13.1           # 7.5 ft shell
VESSEL_ZC = VESSEL_SKID + VESSEL_R * math.sqrt(2) + 6.2      # shell axis: a tall cradle under it
VESSEL_CHANGE = math.floor((VESSEL_ZC - VESSEL_R - 0.5) / 0.2) * 0.2   # black skid and cradle, then the white vessel


@_sheeted
def pressure_vessel(Lt=ft(34.0)):
    """A horizontal pressure vessel shipped on a skid: shell with girth seams, 2:1 ellipsoidal
    heads, two saddles with wear plates, a cradle web between them pierced with 45 degree
    topped openings, nozzles with blind flanges, a manway, lifting lugs and a nameplate. The
    web under the shell carries it at 45 degrees, so nothing overhangs. Skid and cradle print
    black to VESSEL_CHANGE, half a millimetre under the shell; the vessel prints white."""
    r = VESSEL_R
    hd = r / 2
    z0 = VESSEL_SKID
    zc = VESSEL_ZC
    x0, x1 = hd, hd + Lt
    L = Lt + 2 * hd
    shell = M.cylinder(Lt, r, r, 96).rotate([0, 90, 0]).translate([x0, 0, zc])
    head = M.sphere(1.0, 64).scale([hd, r, r])
    heads = [(head - box([0, -r - 1, -r - 1], [hd + 1, r + 1, r + 1])).translate([x0 + 0.01, 0, zc]),
             (head - box([-hd - 1, -r - 1, -r - 1], [0, r + 1, r + 1])).translate([x1 - 0.01, 0, zc])]
    vessel = union([shell] + heads)
    yw = 8.0
    web = M.hull(vessel + box([x0, -yw, z0 - 0.01], [x1, yw, z0]))
    # openings through the web between the saddles, gable-topped at 45 degrees
    xs1, xs2 = x0 + Lt * 0.18, x1 - Lt * 0.18
    holes = []
    span = xs2 - xs1 - 6.0
    wmax = 2 * ((zc - r - z0) - 2.6)               # the gable's apex stays a mm under the shell
    n = 3
    w = min(wmax, (span - (n - 1) * 4.0) / n)
    start = xs1 + 3.0 + (span - (n * w + (n - 1) * 4.0)) / 2
    for k in range(n):
        a = start + k * (w + 4.0)
        top = z0 + 1.6
        holes.append(M.hull_points([(x, y, z) for y in (-20, 20) for (x, z) in
                                    ((a, z0 - 0.5), (a + w, z0 - 0.5), (a, top), (a + w, top), (a + w / 2, top + w / 2))]))
    web = web - union(holes)
    # saddles (on the skid's cross beams) with wear plates
    sad = []
    for xs in (xs1, xs2):
        yy = r * math.sin(math.radians(60)) + 0.8
        plate = box([xs - 0.8, -yy, z0 - 0.01], [xs + 0.8, yy, zc - r * math.cos(math.radians(60))])
        sad.append(plate - M.cylinder(4.0, r + 0.01, r + 0.01, 96).rotate([0, 90, 0]).translate([xs - 2, 0, zc]))
        wear = M.cylinder(5.0, r + 0.25, r + 0.25, 96).rotate([0, 90, 0]).translate([xs - 2.5, 0, zc])
        sad.append(wear ^ box([xs - 2.5, -yy, z0], [xs + 2.5, yy, zc - r * 0.45]))
        for y in (-yy + 0.8, 0.0, yy - 0.8):
            sad.append(box([xs - 3.0, y - 0.4, z0 - 0.01], [xs + 3.0, y + 0.4, z0 + 2.4]))
    # girth seams with 45 degree undersides, kept to the upper half (the web hides the rest)
    seams = []
    for x in np.linspace(x0 + Lt / 3, x1 - Lt / 3, 2):
        ring = M.cylinder(0.5, r + 0.15, r + 0.15, 96).rotate([0, 90, 0]).translate([x - 0.25, 0, zc])
        seams.append(ring ^ box([x - 1, -r - 1, zc - r * 0.7], [x + 1, r + 1, zc + r + 1]))
    for x in (x0, x1):
        ring = M.cylinder(0.5, r + 0.15, r + 0.15, 96).rotate([0, 90, 0]).translate([x - 0.25, 0, zc])
        seams.append(ring ^ box([x - 1, -r - 1, zc - r * 0.7], [x + 1, r + 1, zc + r + 1]))
    # nozzles, manway, lugs on top
    tops = []
    for x, rn, hn in ((x0 + Lt * 0.15, 1.6, 4.0), (x0 + Lt * 0.5, 4.0, 3.0), (x0 + Lt * 0.72, 2.0, 4.5), (x0 + Lt * 0.88, 1.3, 3.5)):
        zt = zc + r - 0.6
        tops.append(M.cylinder(hn + 0.6, rn, rn, 40).translate([x, 0, zt]))
        tops.append(M.cylinder(0.6, rn + 0.9, rn + 0.9, 40).translate([x, 0, zt + hn + 0.6]))
        tops.append(M.cylinder(0.9, rn, rn + 0.9, 40).translate([x, 0, zt + hn - 0.3]))
    for x in (x0 + Lt * 0.3, x0 + Lt * 0.62):
        lug = M.hull(box([x - 1.6, -0.5, zc + r - 1.0], [x + 1.6, 0.5, zc + r + 1.6]) +
                     M.cylinder(1.0, 1.6, 1.6, 20).rotate([90, 0, 0]).translate([x, 0.5, zc + r + 1.6]))
        tops.append(lug - M.cylinder(2.2, 0.6, 0.6, 12).rotate([90, 0, 0]).translate([x, 1.1, zc + r + 1.6]))
    name = M.hull_points([(x0 + Lt * 0.42 + dx, -r - 0.15, zc + dz) for dx in (0, 5.0) for dz in (-1.2, 1.6)] +
                         [(x0 + Lt * 0.42 + dx, -r + 1.0, zc + dz) for dx in (0, 5.0) for dz in (-1.6, 1.6)])
    # skid: two longitudinal beams, cross beams under the saddles and at the ends
    skid = [box([x0 - 2.0, y - 1.0, 0.0], [x1 + 2.0, y + 1.0, z0]) for y in (-yw + 1.0, yw - 1.0)]
    yy = r * math.sin(math.radians(60)) + 0.8
    for x, hw in ((x0 - 1.0, 1.2), (xs1, 3.2), (xs2, 3.2), (x1 + 1.0, 1.2)):      # the saddles' gussets stand on these
        skid.append(box([x - hw, -yy, 0.0], [x + hw, yy, z0]))
    for x in (x0 - 1.0, x1 + 1.0):
        for y in (-yy, yy):
            skid.append(M.hull_points([(x + dx, y, z) for dx in (-1.2, 1.2) for z in (0.0, z0)] +
                                      [(x + dx, y + math.copysign(1.2, y), z) for dx in (-1.2, 1.2) for z in (0.0, 1.0)]))
    out = union([vessel, web, name] + sad + seams + tops + skid)
    return out.translate([0, yy + 1.2, 0])


# ================================================================== ship propeller
PROP_SKID = 1.6           # propeller: timber platform, then the bronze


@_sheeted
def propeller(R=18.5, blades=4, rh=4.6, hh=9.5):
    """A cast bronze ship's propeller lying face down on a timber platform: a tapered boss with
    its bore and keyway, and skewed blades whose backs rise in an airfoil from thin edges, from
    a thick root to a thin tip. Everything stands on the platform."""
    z0 = PROP_SKID
    parts = []
    stations = np.linspace(rh - 1.0, R, 10)
    for b in range(blades):
        ang = 2 * math.pi * b / blades
        secs = []
        for i, r in enumerate(stations):
            f = (r - stations[0]) / (R - stations[0])
            chord = (9.0 + 12.0 * math.sin(math.pi * min(f, 0.7) / 1.4)) * math.sqrt(max(1.0 - f ** 2.4, 0.04))
            skew = 9.0 * f ** 1.8                       # the blade sweeps back toward the tip
            tmax = 3.0 * (1 - f) ** 1.3 + 0.55
            pts = []
            for s in np.linspace(0, 1, 9):
                h = 0.4 + (tmax - 0.4) * math.sin(math.pi * s ** 0.8) ** 0.9
                u = (s - 0.4) * chord - skew
                pts.append((r, u, z0 + h))
                pts.append((r, u, z0 - 0.01))
            # to world: radial along ang, chord along the tangent
            ca, sa = math.cos(ang), math.sin(ang)
            secs.append([(rr * ca - u * sa, rr * sa + u * ca, z) for (rr, u, z) in pts])
        for a, b2 in zip(secs[:-1], secs[1:]):
            parts.append(M.hull_points(a + b2))
    boss = M.cylinder(hh, rh + 0.6, rh - 0.4, 64).translate([0, 0, z0 - 0.01])
    boss = boss + M.cylinder(0.8, rh - 0.4, rh - 1.2, 64).translate([0, 0, z0 + hh - 0.02])
    bore = M.cylinder(hh + 2, 2.4, 2.0, 40).translate([0, 0, z0 + 2.0])
    key = box([1.8, -0.5, z0 + 2.0], [2.9, 0.5, z0 + hh + 2])
    parts.append(boss - bore - key)
    parts.append(M.cylinder(0.25, rh + 0.65, rh + 0.42, 64).translate([0, 0, z0 + hh * 0.35 - 0.25]))
    # platform: runners, planks across, a little larger than the propeller
    S = 2 * R + 3.0
    plat = _skid(S, S, runners=4, plank=2.8)
    plat = plat.scale([1, 1, PROP_SKID / STEEL_DUN]).translate([-S / 2, -S / 2, 0])
    out = union(parts + [plat])
    return union([c for c in out.decompose() if c.volume() > 1.0])     # drop slivers where blade segments meet


# ================================================================== stand-in cars (renders only)
RAIL_TOP = 2.9                    # code 83 rail on 0.8 mm ties
DECK_H = ft(3.7)                  # deck top above the rail head


def track(x0, x1):
    ties = [box([x - 1.2, -ft(4.25), 0.0], [x + 1.2, ft(4.25), 0.8]) for x in np.arange(x0, x1, ft(1.75))]
    g = 16.5 / 2
    rails = [box([x0, y - 0.45, 0.79], [x1, y + 0.45, RAIL_TOP]) for y in (-g - 0.45, g + 0.45)]
    return {"tie": [union(ties)], "rail": [union(rails)]}


def _truck(x):
    zr = RAIL_TOP
    wr = ft(33 / 24.0)
    g = 16.5 / 2 + 0.45
    wheels = [M.cylinder(1.2, wr, wr, 24).rotate([90, 0, 0]).translate([x + dx, y + 0.6, zr + wr])
              for dx in (-ft(2.9), ft(2.9)) for y in (-g, g + 1.2 - 1.2)]
    frames = [box([x - ft(4.6), y - 0.8, zr + 1.2], [x + ft(4.6), y + 0.8, zr + 2 * wr + 0.6]) for y in (-g - 1.6, g + 1.6)]
    bolster = box([x - 1.6, -g - 2.0, zr + wr], [x + 1.6, g + 2.0, zr + 2 * wr + 1.4])
    return wheels, union(frames + [bolster])


def stand_in_flat(L, W=ft(9.6), kind="flat", well=None, bulkhead=None):
    """A plain flatcar at HO size on a length of track, for the renders: deck, side sills with
    stake pockets, two trucks, couplers. ``kind``: flat, fishbelly (deep centre sills, as an 89 ft
    car) or depressed (a well of length ``well`` between raised ends). ``bulkhead``: height of end
    bulkheads. Returns {material: [solids]} with the car's x from 0 to L, deck top at deck()."""
    zd = RAIL_TOP + DECK_H
    out = {"car": [], "deck": [], "wheel": []}
    trucks = (ft(8.0), L - ft(8.0)) if kind != "fishbelly" else (ft(12.5), L - ft(12.5))
    if kind == "depressed":
        e = (L - well) / 2
        zw = zd - ft(1.9)
        out["deck"].append(box([0, -W / 2, zd - 0.8], [e, W / 2, zd]))
        out["deck"].append(box([L - e, -W / 2, zd - 0.8], [L, W / 2, zd]))
        out["deck"].append(box([e - 0.01, -W / 2 + 1.0, zw - 0.8], [L - e + 0.01, W / 2 - 1.0, zw]))
        girder = M.hull_points([(x, y, z) for y in (0, 1.0) for (x, z) in
                                ((e - 6, zd), (L - e + 6, zd), (L - e, zw - 3.5), (e, zw - 3.5), (e - 6, zd - 3.0), (L - e + 6, zd - 3.0))])
        for y in (-W / 2, W / 2 - 1.0):
            out["car"].append(girder.translate([0, y, 0]))
        out["car"].append(box([0, -W / 2, zd - 3.0], [e, W / 2, zd - 0.79]))
        out["car"].append(box([L - e, -W / 2, zd - 3.0], [L, W / 2, zd - 0.79]))
    else:
        out["deck"].append(box([0, -W / 2, zd - 0.8], [L, W / 2, zd]))
        for y in (-W / 2, W / 2 - 0.8):
            if kind == "fishbelly":
                sill = M.hull_points([(x, y + dy, z) for dy in (0, 0.8) for (x, z) in
                                      ((0, zd - 0.01), (L, zd - 0.01), (0, zd - 2.6), (L, zd - 2.6),
                                       (L * 0.3, zd - 6.0), (L * 0.7, zd - 6.0))])
            else:
                sill = box([0, y, zd - 2.8], [L, y + 0.8, zd - 0.01])
            out["car"].append(sill)
        out["car"].append(box([0, -2.0, zd - 4.5], [L, 2.0, zd - 0.79]))
        for x in np.arange(ft(2.0), L - ft(1.0), ft(4.0)):
            for y in (-W / 2 - 0.5, W / 2):
                out["car"].append(box([x - 0.5, y, zd - 2.2], [x + 0.5, y + 0.5, zd - 0.6]))
    for x in trucks:
        w, f = _truck(x)
        out["wheel"] += w
        out["car"].append(f)
    for x0, x1 in ((-2.6, 0.01), (L - 0.01, L + 2.6)):
        out["car"].append(box([x0, -1.0, zd - 4.2], [x1, 1.0, zd - 2.6]))
    if bulkhead:
        for x0 in (0.0, L - 1.6):
            bh = box([x0, -W / 2, zd - 0.01], [x0 + 1.6, W / 2, zd + bulkhead])
            ribs = [box([x0 - 0.4 if x0 > 0 else x0 + 1.59, y - 0.6, zd], [x0 + 0.01 if x0 > 0 else x0 + 2.0, y + 0.6, zd + bulkhead])
                    for y in np.linspace(-W / 2 + 1.0, W / 2 - 1.0, 5)]
            out["car"].append(union([bh] + ribs))
    return out


def deck(kind="flat"):
    return RAIL_TOP + DECK_H - (ft(1.9) if kind == "depressed" else 0.0)


def ballast(x0, x1):
    return M.hull_points([(x, y, 0.0) for x in (x0, x1) for y in (-21.0, 21.0)] +
                         [(x, y, 0.55) for x in (x0, x1) for y in (-16.5, 16.5)])


# ================================================================== pack render scenes
CAR_COLOURS = {"ttx_yellow": ["#E3AE12", 0.6, 0.0], "car_black": ["#262626", 0.7, 0.0], "car_oxide": ["#6A2C1E", 0.75, 0.0],
               "car_mineral": ["#5B3A2A", 0.75, 0.0], "deck": ["#76664F", 0.85, 0.0], "wheel": ["#2C2B2A", 0.5, 0.5],
               "tie": ["#4A3D31", 0.9, 0.0], "rail": ["#857E76", 0.4, 0.6], "ballast": ["#8E8A84", 0.95, 0.0]}


def _car(L, body, **kw):
    mats = {"ballast": [ballast(-12.0, L + 12.0)]}
    for k, v in track(-12.0, L + 12.0).items():
        mats.setdefault(k, []).extend(v)
    for k, v in stand_in_flat(L, **kw).items():
        mats.setdefault(body if k == "car" else k, []).extend(v)
    return mats


def _put(mats, colour, m):
    mats.setdefault(colour.replace(" ", "_").lower(), []).append(m)


def _place(mats, m, colour, x, z, change=None, y=None, centre=False):
    """Set a piece (print pose) on the deck: its low x at ``x`` (or centred on x), centred
    across the car, its base at ``z``; split at its colour change. Returns its far x."""
    b = m.bounding_box()
    dx = (x - (b[0] + b[3]) / 2) if centre else (x - b[0])
    move = [dx, -(b[1] + b[4]) / 2 if y is None else y, z]
    if change:
        hi, lo = m.split_by_plane((0.0, 0.0, 1.0), change[0] + 1e-3)
        _put(mats, colour, lo.translate(move))
        _put(mats, change[1], hi.translate(move))
    else:
        _put(mats, colour, m.translate(move))
    return b[3] + dx


def pack_scene(key):
    """{material: [solids]}: a flatcar-load pack on its stand-in car, on track, for the renders."""
    zd = deck()
    if key == "windtower":
        L = ft(89.3)
        s = _car(L, "ttx_yellow", kind="fishbelly", W=ft(9.8))
        x0 = (L - TOWER_L) / 2
        zc = zd + TOWER_R0 + TOWER_GAP
        _put(s, "Light Gray", tower_section().transform(np.array([[0, 0, 1, x0], [0, 1, 0, 0], [-1, 0, 0, zc]], float)))
        _put(s, "Cobalt Blue", tower_frame(TOWER_R0).transform(np.array([[0, 0, -1, x0], [-1, 0, 0, 0], [0, 1, 0, zc]], float)))
        _put(s, "Cobalt Blue", tower_frame(TOWER_R1).transform(np.array([[0, 0, 1, x0 + TOWER_L], [1, 0, 0, 0], [0, 1, 0, zc]], float)))
        return s
    if key == "nacelle":
        L = ft(89.3)
        s = _car(L, "car_black", kind="fishbelly", W=ft(9.8))
        x = _place(s, nacelle(), "Sunflower Yellow", 30.0, zd, (NAC_FRAME, "White"))
        _place(s, hub(), "Sunflower Yellow", x + 50.0, zd, (NAC_FRAME, "White"), centre=True)
        return s
    if key == "transformer":
        L = ft(52.0)
        s = _car(L, "car_black", kind="depressed", well=ft(30.0), W=ft(10.0))
        _place(s, transformer(), "Cocoa Brown", L / 2, deck("depressed"), (XF_BLOCK, "Gray"), centre=True)
        return s
    if key == "linepipe":
        L = ft(53.5)
        s = _car(L, "car_mineral", bulkhead=ft(9.0))
        _place(s, pipe_load(), "Cocoa Brown", L / 2, zd, (PIPE_DUN, "Green"), centre=True)
        return s
    if key == "tarps":
        L = ft(89.3)
        s = _car(L, "car_oxide", kind="fishbelly", W=ft(9.8))
        x = 14.0
        for kind, colour in (("machine", "Desert Tan"), ("tall", "Marine Blue"), ("long", "Black")):
            x = _place(s, tarp_load(kind), "Cocoa Brown", x, zd, (TARP_BLOCK, colour)) + 18.0
        return s
    if key == "steel":
        L = ft(89.3)
        s = _car(L, "car_black", kind="fishbelly", W=ft(9.8))
        x = 6.0
        for _ in range(3):
            x = _place(s, coil(), "Cocoa Brown", x, zd, (STEEL_DUN, "Silver")) + 3.0
        x = _place(s, plate_bundle(), "Cocoa Brown", x + 3.0, zd, (STEEL_DUN, "Iron Gray Metallic")) + 6.0
        _place(s, beam_bundle(), "Cocoa Brown", x, zd, (STEEL_DUN, "Copper Brown Metallic"))
        return s
    if key == "vessel":
        L = ft(60.0)
        s = _car(L, "car_oxide")
        _place(s, pressure_vessel(), "Black", L / 2, zd, (VESSEL_CHANGE, "White"), centre=True)
        return s
    if key == "propeller":
        L = ft(42.0)
        s = _car(L, "car_mineral")
        _place(s, propeller(), "Cocoa Brown", L / 2, zd, (PROP_SKID, "Iridium Gold Metallic"), centre=True)
        return s
    raise KeyError(key)

"""Detail packs: the small, sought-after pieces modellers buy by the bag. Loaded pallets, sandbag
works and tank obstacles for HO military dioramas, modular retaining walls, and railroad tie
piles. Like hoarch.scenery, each piece prints in its colours with at most one filament change,
at a height shared by its plate, so it ships with no painting.

- Pallets: wood to PALLET_TOP, the load above it.
- Crib walls: earth fill to CRIB_FILL, concrete above it.
- Everything else prints in one colour.

Local z is up from the bed. Sizes are HO (1:87.1)."""
import math

import numpy as np
from manifold3d import Manifold as M

from .core import box, ft, inch, union

PALLET_TOP = 1.6          # a 48 x 40 in pallet stands 5.5 in tall
CRIB_FILL = 1.0           # crib wall: earth fill up to here, concrete members above


def _rbox(x0, y0, z0, x1, y1, z1, c=0.15):
    """A box with its four vertical edges and top edges chamfered by ``c``, standing on z0."""
    return M.hull_points([(x, y, z) for x in (x0 + c, x1 - c) for y in (y0, y1) for z in (z0, z1 - c)] +
                         [(x, y, z) for x in (x0, x1) for y in (y0 + c, y1 - c) for z in (z0, z1 - c)] +
                         [(x, y, z1) for x in (x0 + c, x1 - c) for y in (y0 + c, y1 - c)])


# ================================================================== pallets
def pallet():
    """A 48 x 40 in stringer pallet, printed upright: five bottom boards, three notched stringers,
    seven top boards. 14.0 x 11.7 x 1.6 mm."""
    L, W = ft(4.0), ft(40 / 12.0)
    parts = []
    for k in range(5):                                       # bottom deck
        x = (L - 1.0) * k / 4
        parts.append(box([x, 0.0, 0.0], [x + 1.0, W, 0.4]))
    for y in (0.0, (W - 0.9) / 2, W - 0.9):                  # stringers with fork notches
        s = box([0.0, y, 0.39], [L, y + 0.9, 1.21])
        for xn in (L * 0.22, L * 0.78):
            s = s - box([xn - 1.6, y - 1, 0.38], [xn + 1.6, y + 2, 0.75])
        parts.append(s)
    for k in range(7):                                       # top deck
        x = (L - 1.05) * k / 6
        parts.append(box([x, 0.0, 1.2], [x + 1.05, W, PALLET_TOP]))
    return union(parts)


def _carton(x0, y0, z0, dx, dy, dz):
    c = _rbox(x0, y0, z0, x0 + dx, y0 + dy, z0 + dz, 0.12)
    tape = box([x0 + dx / 2 - 0.25, y0 - 0.05, z0 + dz - 0.01], [x0 + dx / 2 + 0.25, y0 + dy + 0.05, z0 + dz + 0.08])
    return c + tape


def load_cartons(seed=1):
    """Pallet + cartons: three tiers of shipping cartons in mixed sizes, the top tier short one."""
    rng = np.random.default_rng(seed)
    L, W = ft(4.0), ft(40 / 12.0)
    g = 0.15
    tiers = []
    z = PALLET_TOP
    for t in range(3):
        h = 3.2
        cells = [(0, 0), (1, 0), (0, 1), (1, 1)] if t < 2 else [(0, 0), (1, 0), (0, 1)]
        for i, j in cells:
            dx, dy = (L - g) / 2 - g, (W - g) / 2 - g
            if t == 1:                                         # the middle tier turned across
                dx, dy = dy * L / W, dx * W / L
            x0, y0 = g + i * (L - g) / 2, g + j * (W - g) / 2
            jit = rng.uniform(-0.12, 0.12, 2)
            tiers.append(_carton(x0 + jit[0], y0 + jit[1], z, min(dx, L - x0 - g), min(dy, W - y0 - g), h + rng.uniform(-0.2, 0.0)))
        z += h
    return pallet() + union(tiers)


def _sack(cx, cy, z0, l=6.4, w=3.9, h=1.15, ang=0.0):
    """A filled paper sack: a pillow, full at mid-height, pulled in at its ends."""
    pts = []
    for zz, ins in ((z0, 0.45), (z0 + h * 0.5, 0.0), (z0 + h, 0.5)):
        for sx in (-1, 1):
            for sy in (-1, 1):
                pts.append((sx * (l / 2 - ins - 0.3), sy * (w / 2 - ins), zz))
                pts.append((sx * (l / 2 - ins), sy * (w / 2 - ins - 0.4), zz))
    return M.hull_points(pts).rotate([0, 0, ang]).translate([cx, cy, 0])


def load_sacks(seed=2):
    """Pallet + sacks: five layers of cement or feed sacks, the courses turned alternately."""
    rng = np.random.default_rng(seed)
    L, W = ft(4.0), ft(40 / 12.0)
    sacks = []
    z = PALLET_TOP
    for layer in range(5):
        if layer % 2 == 0:                     # three sacks along, side by side across ... 2 x 3 pattern
            spots = [(L * (2 * i + 1) / 6, W * (2 * j + 1) / 4, 90.0) for i in range(3) for j in range(2)]
        else:
            spots = [(L * (2 * i + 1) / 4, W * (2 * j + 1) / 6, 0.0) for i in range(2) for j in range(3)]
        for cx, cy, a in spots:
            l, w = (W / 2 - 0.15, L / 3 - 0.15) if a == 90.0 else (L / 2 - 0.15, W / 3 - 0.15)
            sacks.append(_sack(cx + rng.uniform(-0.1, 0.1), cy + rng.uniform(-0.1, 0.1), z, l, w, 1.15,
                               a + rng.uniform(-3, 3)))
        z += 1.05
    return pallet() + union(sacks)


def _drum(cx, cy, z0, r=2.88, h=ft(34.5 / 12)):
    """A 55 gallon drum: rolled chimes at both ends, two rolling hoops, and the bungs on top."""
    body = M.cylinder(h, r - 0.08, r - 0.08, 40)
    chime = M.cylinder(0.3, r, r, 40)
    hoop = M.cylinder(0.25, r, r, 40)
    d = body + chime + chime.translate([0, 0, h - 0.3]) + hoop.translate([0, 0, h / 3]) + hoop.translate([0, 0, 2 * h / 3])
    d = d - M.cylinder(0.2, r - 0.35, r - 0.35, 40).translate([0, 0, h - 0.19])
    bungs = M.cylinder(0.35, 0.45, 0.45, 16).translate([r * 0.55, 0, h - 0.2]) + \
        M.cylinder(0.3, 0.3, 0.3, 12).translate([-r * 0.6, 0.6, h - 0.2])
    return (d + bungs).translate([cx, cy, z0])


def load_drums():
    """Pallet + four 55 gallon drums."""
    L, W = ft(4.0), ft(40 / 12.0)
    r = 2.88
    drums = [_drum(L / 2 + sx * (r + 0.05), W / 2 + sy * (r + 0.02 - 0.03), PALLET_TOP) for sx in (-1, 1) for sy in (-1, 1)]
    return pallet() + union(drums)


def _block(x0, y0, z0, cores=True):
    """An 8 x 8 x 16 in concrete block, its two cores open at the top."""
    l, w, h = inch(15.6), inch(7.6), inch(7.6)
    b = box([x0, y0, z0], [x0 + l, y0 + w, z0 + h])
    if cores:
        for k in (0.27, 0.73):
            b = b - box([x0 + l * k - 0.62, y0 + 0.45, z0 + h - 0.6], [x0 + l * k + 0.62, y0 + w - 0.45, z0 + h + 0.1])
    return b


def load_blocks():
    """Pallet + concrete blocks: four courses of 3 x 4 blocks, cores showing on the top course."""
    L, W = ft(4.0), ft(40 / 12.0)
    l, w, h = inch(15.6), inch(7.6), inch(7.6)
    gap = 0.1
    nx = int(L // (l + gap))
    ny = int(W // (w + gap))
    blocks = []
    for c in range(4):
        for i in range(nx):
            for j in range(ny):
                x0 = (L - nx * (l + gap)) / 2 + i * (l + gap)
                y0 = (W - ny * (w + gap)) / 2 + j * (w + gap)
                blocks.append(_block(x0, y0, PALLET_TOP + c * (h + 0.05), cores=c == 3))
    return pallet() + union(blocks)


def pallet_stack(n=6):
    """Empty pallets stacked ``n`` high, a little askew, as found behind any warehouse."""
    rng = np.random.default_rng(7)
    p = pallet()
    out = []
    for k in range(n):
        a = rng.uniform(-3.0, 3.0)
        out.append(p.translate([-7.0, -5.85, 0]).rotate([0, 0, a]).translate([7.0 + rng.uniform(-0.25, 0.25),
                                                                               5.85 + rng.uniform(-0.25, 0.25), k * PALLET_TOP]))
    return union(out)


# ================================================================== military
def _bag(cx, cy, z0, ang, l=6.6, w=3.5, h=1.55):
    """A filled sandbag: a pillow with one end tied and pinched narrower."""
    pts = []
    for zz, ins in ((z0, 0.35), (z0 + h * 0.45, 0.0), (z0 + h, 0.4)):
        for sx, pinch in ((-1, 0.0), (1, 0.35)):
            for sy in (-1, 1):
                pts.append((sx * (l / 2 - ins - 0.35), sy * (w / 2 - ins - pinch * 0.6), zz))
                pts.append((sx * (l / 2 - ins), sy * (w / 2 - ins - 0.45 - pinch), zz))
    tie = M.cylinder(0.5, 0.45, 0.3, 10).rotate([0, 90, 0]).translate([l / 2 - 0.05, 0, z0 + h * 0.45])
    return (M.hull_points(pts) + tie).rotate([0, 0, ang]).translate([cx, cy, 0])


def _wall_path(path, courses=6, seed=3, closed=False):
    """Sandbags laid along a polyline ``path`` [(x, y)...], two bags thick: stretcher courses
    (two rows along the line) alternating with header courses (bags across it), each course
    set back slightly so the wall batters."""
    rng = np.random.default_rng(seed)
    pts = np.asarray(path, float)
    seg = np.diff(pts, axis=0)
    seglen = np.hypot(seg[:, 0], seg[:, 1])
    total = seglen.sum()

    def at(s):
        k = min(int(np.searchsorted(np.cumsum(seglen), s, side="right")), len(seglen) - 1)
        s0 = np.cumsum(seglen)[k] - seglen[k]
        t = (s - s0) / seglen[k]
        p = pts[k] + seg[k] * t
        d = seg[k] / seglen[k]
        return p, d

    bags = []
    for c in range(courses):
        z0 = c * 1.38
        bat = c * 0.18                                    # each course set back a little
        if c % 2 == 0:                                   # stretchers: two rows along
            pitch = 6.5
            n = max(1, int(total / pitch))
            for row in (-1, 1):
                for i in range(n):
                    s = (i + 0.5 + (0.5 if (c // 2) % 2 else 0.0)) * total / n
                    s = min(s, total - 0.01)
                    p, d = at(s)
                    nrm = np.array([-d[1], d[0]])
                    q = p + nrm * row * (1.8 - bat * (row > 0))
                    a = math.degrees(math.atan2(d[1], d[0])) + rng.uniform(-5, 5) + (180 if row > 0 else 0)
                    bags.append(_bag(q[0] + rng.uniform(-0.1, 0.1), q[1] + rng.uniform(-0.1, 0.1), z0, a))
        else:                                            # headers: across the line
            pitch = 3.6
            n = max(1, int(total / pitch))
            for i in range(n):
                s = (i + 0.5) * total / n
                p, d = at(s)
                nrm = np.array([-d[1], d[0]])
                q = p - nrm * bat / 2
                a = math.degrees(math.atan2(nrm[1], nrm[0])) + rng.uniform(-6, 6) + (180 if i % 2 else 0)
                bags.append(_bag(q[0], q[1], z0, a))
    return union(bags)


def sandbag_wall(L=40.0, courses=6):
    """A straight sandbag breastwork ``L`` long, two bags thick, about 0.75 m (8.5 mm) high."""
    return _wall_path([(0.0, 0.0), (L, 0.0)], courses, seed=3)


def sandbag_corner(a=24.0, courses=6):
    """An L-shaped sandbag wall, each leg ``a`` long."""
    return _wall_path([(0.0, a), (0.0, 0.0), (a, 0.0)], courses, seed=4)


def sandbag_pit(r=16.0, opening=70.0, courses=6):
    """A round gun pit of sandbags, ``r`` to the wall's centre line, open ``opening`` degrees at
    the rear for the crew."""
    a0 = math.radians(-90 + opening / 2)
    a1 = math.radians(270 - opening / 2)
    path = [(r * math.cos(t), r * math.sin(t)) for t in np.linspace(a0, a1, 28)]
    return _wall_path(path, courses, seed=5)


def dragons_tooth(h=ft(3.4)):
    """A concrete 'dragon's tooth' tank obstacle: a truncated pyramid on a square plinth."""
    b = h * 0.9
    plinth = box([-b / 2 - 0.4, -b / 2 - 0.4, 0.0], [b / 2 + 0.4, b / 2 + 0.4, 0.6])
    tooth = M.hull_points([(x, y, 0.59) for x in (-b / 2, b / 2) for y in (-b / 2, b / 2)] +
                          [(x, y, h) for x in (-b / 6, b / 6) for y in (-b / 6, b / 6)])
    return plinth + tooth


def teeth_row(n=4, pitch=None):
    """A staggered double row of dragon's teeth on one footing, ready to set in a field."""
    h = ft(3.4)
    pitch = pitch or h * 1.25
    teeth = [dragons_tooth(h * (1.0 if k % 2 else 0.85)).translate([k * pitch / 2, (pitch / 2.2) * (k % 2), 0])
             for k in range(2 * n)]
    footing = box([-pitch / 2, -pitch / 2, 0.0], [(2 * n - 1) * pitch / 2 + pitch / 2, pitch / 2.2 + pitch / 2, 0.6])
    return footing + union(teeth)


def ammo_stack(cols=3, rows=2, tiers=3):
    """Wooden ammunition boxes stacked in tiers, each box with rope handles and lid battens."""
    l, w, h = ft(2.5), ft(1.0), ft(0.9)
    boxes = []
    for t in range(tiers):
        for i in range(cols):
            for j in range(rows):
                x0, y0, z0 = i * (l + 0.12), j * (w + 0.12), t * (h + 0.02)
                b = _rbox(x0, y0, z0, x0 + l, y0 + w, z0 + h, 0.1)
                for xb in (0.6, l - 1.2):
                    b = b + box([x0 + xb, y0 - 0.08, z0 + h - 0.35], [x0 + xb + 0.6, y0 + w + 0.08, z0 + h - 0.05])
                b = b + box([x0 - 0.12, y0 + w / 2 - 0.35, z0 + h * 0.45], [x0 + 0.01, y0 + w / 2 + 0.35, z0 + h * 0.65])
                b = b + box([x0 + l - 0.01, y0 + w / 2 - 0.35, z0 + h * 0.45], [x0 + l + 0.12, y0 + w / 2 + 0.35, z0 + h * 0.65])
                boxes.append(b)
    return union(boxes)


# ================================================================== retaining walls
def _tie(x0, y0, z0, l, rng, w=None, d=None):
    """One weathered crosstie seen on its side: ``l`` long, checked with two grain lines."""
    w = w or inch(8.0)
    d = d or inch(7.0)
    t = _rbox(x0, y0, z0, x0 + l, y0 + w, z0 + d, 0.12)
    for k in (0.33, 0.68):
        yy = y0 + w * k + rng.uniform(-0.1, 0.1)
        t = t - box([x0 + rng.uniform(0.5, 3.0), yy - 0.06, z0 + d - 0.12], [x0 + l - rng.uniform(0.5, 3.0), yy + 0.06, z0 + d + 0.1])
    return t


def tie_wall(L=50.0, H=20.0, seed=11):
    """A crosstie retaining wall panel, printed face-up: ties laid on edge with broken joints, held by
    steel H-pile posts every 8 ft, on a 1 mm backing. Panels lap at their ends (the face runs
    1.5 mm past the backing at x = L, the backing 1.5 mm past the face at x = 0), so a run of
    panels hides its joints. Installed, the panel's y is up and its z points out of the bank."""
    rng = np.random.default_rng(seed)
    lap = 1.5
    tl = ft(8.5)
    tw = inch(8.0) + 0.06
    back = box([-lap, 0.0, 0.0], [L, H, 1.0])
    ties = []
    for c in range(int(H // tw)):
        y0 = c * tw
        x = -rng.uniform(0.0, tl) if c else 0.0
        while x < L:
            x0 = max(x, 0.0)
            x1 = min(x + tl, L)
            if x1 - x0 > 1.5:
                ties.append(_tie(x0 + 0.04, y0 + 0.03, 0.99, x1 - x0 - 0.08, rng, w=tw - 0.06,
                                 d=inch(7.0) * 0.55 + rng.uniform(-0.12, 0.12)))
            x += tl
    posts = []
    for xp in np.arange(ft(4.0), L - 1.0, ft(8.0)):
        # an H-pile: flanges and web, standing proud of the ties
        z0 = 0.99 + inch(7.0) * 0.55
        posts.append(box([xp - 0.9, -0.0, z0 - 0.3], [xp + 0.9, H + 0.6, z0 + 0.25]) +
                     box([xp - 0.12, -0.0, z0 + 0.2], [xp + 0.12, H + 0.6, z0 + 1.2]) +
                     box([xp - 0.9, -0.0, z0 + 1.15], [xp + 0.9, H + 0.6, z0 + 1.5]))
    return scarf(back + union(ties) + union(posts), L, lap, H)


def scarf(panel, L, lap, H):
    """Cut a face-up wall panel's lapped ends on a 45 degree plane so both print clean: the right
    end keeps what lies above the plane (its face lip rests on a 45 degree underside), the left end
    keeps what lies below it (the backing's lap, its top sloping), and two panels set L apart meet
    on the same plane."""
    big = 50.0
    right = M.hull_points([(L - lap, y, 0.0) for y in (-5, H + 5)] + [(L - lap + big, y, big) for y in (-5, H + 5)] +
                          [(L - lap + big, y, -1.0) for y in (-5, H + 5)] + [(L - lap, y, -1.0) for y in (-5, H + 5)])
    left = M.hull_points([(-lap, y, 0.0) for y in (-5, H + 5)] + [(-lap + big, y, big) for y in (-5, H + 5)] +
                         [(-lap - 1.0, y, big) for y in (-5, H + 5)] + [(-lap - 1.0, y, 0.0) for y in (-5, H + 5)])
    left = left ^ box([-lap - 2, -10, -1], [0.0, H + 10, big])
    return panel - right - left


def crib_wall(L=50.0, H=24.0):
    """A precast concrete crib wall panel, printed face-up: stretchers (long beams across the face)
    and the square ends of the headers between them, with the earth fill showing in each cell. Two
    colours: the fill up to CRIB_FILL, the concrete above it. Installed, y is up."""
    sl, sh = ft(9.0), ft(1.0)            # stretcher length and height on the face
    hw = ft(1.0)                         # header end, square
    back = box([0.0, 0.0, 0.0], [L, H, CRIB_FILL])
    # rough the fill surface a little: shallow pebble dimples
    rng = np.random.default_rng(21)
    peb = union([M.sphere(rng.uniform(0.3, 0.5), 8).translate([rng.uniform(0, L), rng.uniform(0, H), CRIB_FILL - 0.45])
                 for _ in range(int(L * H / 6))])
    members = []
    ycourse = sh + hw                    # a stretcher course, then a course of header ends
    n = int(H // ycourse) + 1
    for c in range(n):
        y0 = c * ycourse
        off = (sl / 2) * (c % 2)
        x = -off
        while x < L:
            x0, x1 = max(x, 0.0), min(x + sl - 0.25, L)
            if x1 - x0 > 1.0 and y0 < H:
                members.append(_rbox(x0, y0, CRIB_FILL - 0.01, x1, min(y0 + sh, H), CRIB_FILL + 1.6, 0.18))
            for xh in (x, x + sl - 0.25 - hw):
                if 0.0 <= xh and xh + hw <= L and y0 + sh + hw <= H + 0.01:
                    members.append(_rbox(xh, y0 + sh, CRIB_FILL - 0.01, xh + hw, y0 + sh + hw, CRIB_FILL + 1.6, 0.18))
            x += sl
    # the pebbles stay below the colour change, so the fill prints all in its earth colour
    return back + (peb ^ box([0, 0, 0], [L, H, CRIB_FILL])) + union(members)


def culvert_headwall(W=30.0, H=14.0, d=ft(3.0)):
    """A concrete culvert headwall printed upright: the wall with a coped top, a pipe opening of
    diameter ``d`` with a projecting collar, splayed wingwalls sloping down to the ground, and a
    corrugated pipe running back 10 mm. Set it in a bank where a stream or ditch passes under."""
    t = 2.2
    wall = box([-W / 2, 0.0, 0.0], [W / 2, t, H])
    cope = M.hull_points([(x, y, z) for x in (-W / 2 - 0.4, W / 2 + 0.4) for y in (-0.4, t + 0.4) for z in (H - 0.01, H + 0.35)] +
                         [(x, y, H + 0.9) for x in (-W / 2 - 0.1, W / 2 + 0.1) for y in (-0.1, t + 0.1)])
    r = d / 2
    zc = r + 0.8
    collar = M.cylinder(0.8, r + 0.9, r + 0.9, 48).rotate([90, 0, 0]).translate([0, 0.0, zc])
    # the bore: round where it shows at the face, pointed (45 degree roof) behind it, so its top
    # needs no bridge
    roof = M.hull_points([(x, y, zc) for x in (-r * 0.7071, r * 0.7071) for y in (0.6, t + 22)] +
                         [(0.0, y, zc + r * 1.414) for y in (0.6, t + 22)])
    hole = M.cylinder(t + 22, r, r, 48).rotate([90, 0, 0]).translate([0, t + 11, zc]) + roof
    pipe = union([M.cylinder(0.5, r + 0.35, r + 0.35, 48).rotate([90, 0, 0]).translate([0, t + 0.5 + k * 0.9, zc])
                  for k in range(11)]) + M.cylinder(10.0, r + 0.2, r + 0.2, 48).rotate([90, 0, 0]).translate([0, t + 10.0, zc])
    cradle = box([-r - 0.9, t - 0.01, 0.0], [r + 0.9, t + 10.0, zc])      # the pipe beds in a concrete cradle
    pipe = (pipe + cradle) ^ box([-W, t - 0.01, 0.0], [W, t + 10.0, H])
    wings = []
    for s in (-1, 1):
        wl = 12.0
        a = math.radians(30)
        p0 = np.array([s * W / 2, 0.0])
        p1 = p0 + np.array([s * wl * math.sin(a), -wl * math.cos(a)])
        n = np.array([p1[1] - p0[1], -(p1[0] - p0[0])])
        n = n / np.linalg.norm(n) * (t / 2)
        quad = [p0 - n, p0 + n, p1 + n, p1 - n]
        wings.append(M.hull_points([(q[0], q[1], 0.0) for q in quad] +
                                   [(q[0], q[1], H) for q in quad[:2]] + [(q[0], q[1], 2.0) for q in quad[2:]]))
    out = wall + cope + collar + union(wings) + pipe
    return out - hole + (M.cylinder(0.4, r + 0.2, r + 0.2, 48).rotate([90, 0, 0]).translate([0, t + 10.0, zc]) - hole)


# ================================================================== railroad
def tie_pile(layers=6, n=9, seed=31):
    """A pile of new crossties, stacked in alternate directions as the section gang leaves them."""
    rng = np.random.default_rng(seed)
    tl, tw, td = ft(8.5), inch(9.0), inch(7.0)
    span = n * (tw + 0.35)
    ties = []
    for layer in range(layers):
        z0 = layer * (td - 0.02)
        for k in range(n):
            o = (span - tl) / 2
            jit = rng.uniform(-0.25, 0.25)
            if layer % 2 == 0:
                t = _tie(o + jit, k * (tw + 0.35), z0, tl, rng, w=tw, d=td)
            else:
                t = _tie(0.0, 0.0, 0.0, tl, rng, w=tw, d=td).rotate([0, 0, 90]).translate([k * (tw + 0.35) + tw, o + jit, z0])
            ties.append(t)
    return union(ties)


def review_scene():
    """The pilot detail pieces set out for review renders. Returns {material: [solids]}."""
    mats = {k: [] for k in ("palletwood", "carton", "sack", "drum", "block", "sandbag", "concrete", "olive",
                            "creosote", "steel", "earth", "cribconcrete")}

    def two(m, z, below, above):
        hi, lo = m.split_by_plane((0.0, 0.0, 1.0), z + 1e-3)
        mats[below].append(lo)
        mats[above].append(hi)

    # --- a loading dock apron: loaded pallets and an empty stack
    x = 0.0
    for f, mat in ((load_cartons, "carton"), (load_sacks, "sack"), (load_drums, "drum"), (load_blocks, "block")):
        two(f().translate([x, 0.0, 0.0]), PALLET_TOP, "palletwood", mat)
        x += 17.0
    mats["palletwood"].append(pallet_stack(6).translate([x, 0.0, 0.0]))
    # --- a sandbag position with tank obstacles
    mats["sandbag"].append(sandbag_pit().translate([20.0, 48.0, 0.0]))
    mats["sandbag"].append(sandbag_wall(40.0).translate([45.0, 34.0, 0.0]))
    mats["sandbag"].append(sandbag_corner(22.0).translate([95.0, 30.0, 0.0]))
    mats["concrete"].append(teeth_row(4).translate([48.0, 58.0, 0.0]))
    mats["olive"].append(ammo_stack().translate([12.0, 40.0, 0.0]))
    # --- retaining walls stood in a bank, and the railroad's tie pile
    stand = lambda m: m.rotate([90, 0, 0])          # face-up print -> wall face to -y
    mats["creosote"].append(stand(tie_wall(50.0, 20.0)).translate([125.0, 10.0, 0.0]))
    hi, lo = crib_wall(50.0, 24.0).split_by_plane((0.0, 0.0, 1.0), CRIB_FILL + 1e-3)
    mats["earth"].append(stand(lo).translate([180.0, 10.0, 0.0]))
    mats["cribconcrete"].append(stand(hi).translate([180.0, 10.0, 0.0]))
    mats["concrete"].append(culvert_headwall().translate([150.0, 45.0, 0.0]))
    mats["creosote"].append(tie_pile().translate([195.0, 35.0, 0.0]))
    return mats


def write_review_npz(path):
    from .core import mesh_arrays
    data = {}
    for mat, ms in review_scene().items():
        ms = [m for m in ms if not m.is_empty()]
        if not ms:
            continue
        vs, fs, o = [], [], 0
        for m in ms:
            v, f = mesh_arrays(m)
            vs.append(v)
            fs.append(f + o)
            o += len(v)
        data[mat + "__v"] = np.concatenate(vs).astype(np.float32)
        data[mat + "__f"] = np.concatenate(fs).astype(np.int32)
    np.savez_compressed(path, **data)

"""Flatcar loads, second series. Same rules as hoarch.flatloads (NOTES.md, "Flatcar loads"): each
piece prints in its colours with at most one filament change at a height its plate shares, needs no
supports, and stands on its own blocking, cribbing or frame. Local z is up from the bed; HO sizes.

Each load's scene (its stand-in car with the load on it, for the renders) is in SCENES at the
bottom; the pack entries (pieces, colours, listing copy) are in hoarch.loads2."""
import math

import numpy as np
from manifold3d import CrossSection as CS, Manifold as M

from .core import box, circle, cs_union, ft, inch, offset, poly, revolve, union
from . import flatloads as F

S2 = math.sqrt(0.5)


# ================================================================== shared helpers
def along_x(cs, xa, xb):
    """Extrude a (y, z) section between x = xa and xb."""
    return M.extrude(cs, xb - xa).transform(np.array([[0, 0, 1, xa], [1, 0, 0, 0], [0, 1, 0, 0]], float))


def along_y(cs, ya, yb):
    """Extrude an (x, z) section between y = ya and yb."""
    return M.extrude(cs, yb - ya).transform(np.array([[1, 0, 0, 0], [0, 0, -1, yb], [0, 1, 0, 0]], float))


def solid(fn):
    """Drop the zero-volume slivers coplanar faces leave, so a piece is one solid."""
    import functools

    @functools.wraps(fn)
    def wrapped(*a, **k):
        m = fn(*a, **k)
        parts = [c for c in m.decompose() if abs(c.volume()) > 0.05]
        return union(parts) if len(parts) != len(m.decompose()) else m
    return wrapped


def flip(m):
    """Display pose to print pose for a load printed upside down: turned over about x, bottom at 0."""
    m = m.rotate([180, 0, 0])
    return m.translate([0, 0, -m.bounding_box()[2]])


def keel(y, z, r, base):
    """The 45 degree keel under a round thing of radius r centred at (y, z), down to ``base``:
    its sides are the circle's tangents at 45 degrees, so nothing past 45 degrees overhangs."""
    dz = z - S2 * r - base
    return poly([(y - S2 * r, z - S2 * r), (y + S2 * r, z - S2 * r), (y + S2 * r - dz, base - 0.01), (y - S2 * r + dz, base - 0.01)])


def tangent_on(c1, r1, c2, r2, r, ov=0.05):
    """Centre of a circle of radius r resting on circles (c1, r1) and (c2, r2): the upper solution."""
    (y1, z1), (y2, z2) = c1, c2
    a, b = r1 + r - ov, r2 + r - ov
    d = math.hypot(y2 - y1, z2 - z1)
    t = (a * a - b * b + d * d) / (2 * d)
    h = math.sqrt(max(a * a - t * t, 0.0))
    ex, ez = (y2 - y1) / d, (z2 - z1) / d
    px, pz = y1 + t * ex, z1 + t * ez
    cands = [(px - h * ez, pz + h * ex), (px + h * ez, pz - h * ex)]
    return max(cands, key=lambda p: p[1])


# ================================================================== 1. precast concrete bridge girders
GIRDER_L = ft(70.0)
GIRDER_SKEW = 12.0          # degrees: the ends are cut for a skewed bridge
GIRDER_Y = inch(13) + 2.6   # the two girders' centres either side of the car's centre line
BOLSTER_T = inch(12)


def _aashto4():
    """AASHTO Type IV section (y across, z up), from the standard's inches: 54 in deep, 20 in top
    flange, 26 in bottom flange, 8 in web, and the flanges' tapers at 45 degrees."""
    pts = [(-13, 0), (13, 0), (13, 8), (4, 17), (4, 40), (10, 46), (10, 54), (-10, 54), (-10, 46), (-4, 40),
           (-4, 17), (-13, 8)]
    return poly([(inch(y), inch(z)) for y, z in pts])


@solid
def girder(L=GIRDER_L, skew=GIRDER_SKEW):
    """A 70 ft AASHTO Type IV prestressed concrete bridge girder, printed upright as it rides: the
    tapers are 45 degrees, so nothing overhangs. Stirrups stand out of the top flange every 2 ft,
    two strand lifting loops near each end, diaphragm inserts in the web; the ends skewed."""
    H = inch(54)
    s = math.tan(math.radians(skew))
    body = along_x(_aashto4(), -3.0, L + 3.0)
    plan = poly([(-8 * s, -8.0), (L - 8 * s, -8.0), (L + 8 * s, 8.0), (8 * s, 8.0)])
    body = body ^ M.extrude(plan, H + 6.0).translate([0, 0, -1.0])
    lifts = (ft(5.0), L - ft(5.0))
    bits = []
    for x in np.arange(ft(1.0), L - ft(1.0) + 0.01, ft(2.0)):
        if min(abs(x - xl) for xl in lifts) < 2.6:
            continue
        for y in (-1.0, 1.0):
            bits.append(box([x - 0.3, y - 0.3, H - 0.01], [x + 0.3, y + 0.3, H + 1.4]))
        bits.append(box([x - 0.3, -1.3, H + 0.8], [x + 0.3, 1.3, H + 1.4]))
    for xl in lifts:
        for y in (-1.25, 1.25):
            bits += [box([xl - 1.5, y - 0.3, H - 0.01], [xl - 0.9, y + 0.3, H + 2.6]),
                     box([xl + 0.9, y - 0.3, H - 0.01], [xl + 1.5, y + 0.3, H + 2.6]),
                     box([xl - 1.5, y - 0.3, H + 2.0], [xl + 1.5, y + 0.3, H + 2.6])]
    holes = []
    for x in (L * 0.25, L * 0.5, L * 0.75):
        for sgn in (-1, 1):
            holes.append(M.cylinder(0.7, 0.45, 0.45, 16).rotate([90, 0, 0]).translate([x, sgn * inch(4) + 0.35, inch(28.5)]))
    return union([body] + bits) - union(holes)


@solid
def girder_bolster():
    """The timber bolster both girders ride on, one near each end: a 12 x 12 across the car, an oak
    pad under each girder and a chock either side of its bottom flange (they locate the girder and
    give the glue a corner to fill)."""
    T = BOLSTER_T
    Lb = ft(9.0)
    bw = inch(26)
    zp = T + 0.8
    parts = [box([-T / 2, -Lb / 2, 0.0], [T / 2, Lb / 2, T])]
    for yc in (-GIRDER_Y, GIRDER_Y):
        parts.append(box([-T / 2 + 0.2, yc - bw / 2 - 2.4, T - 0.01], [T / 2 - 0.2, yc + bw / 2 + 2.4, zp]))
        for sgn in (-1, 1):
            y0 = yc + sgn * (bw / 2 + 0.05)
            cs = poly([(y0, zp - 0.01), (y0, zp + 1.2), (y0 + sgn * 0.5, zp + 1.2), (y0 + sgn * 1.9, zp - 0.01)])
            parts.append(along_x(cs, -T / 2 + 0.4, T / 2 - 0.4))
    # bolt heads through the pads into the bolster
    for yc in (-GIRDER_Y, GIRDER_Y):
        for sgn in (-1, 1):
            for dx in (-1.1, 1.1):
                parts.append(M.cylinder(0.25, 0.35, 0.35, 12).translate([dx, yc + sgn * (bw / 2 + 2.05), zp - 0.01]))
    return union(parts)


# ================================================================== 2-3. lumber
LUMBER_L = ft(16.0)
BUNDLE_H = 8.8            # 20 courses of 2 in nominal; printed upside down, the stickers start here
STICKER = 1.2
BOARDS = {"2x4": (3.5, 13), "2x6": (5.5, 8), "2x10": (9.25, 5), "2x12": (11.25, 4)}


def _stickers(W, n=4, w=1.2, over=0.5):
    xs = np.linspace(w / 2 + 0.3, LUMBER_L - w / 2 - 0.3, n)
    return [box([x - w / 2, -W / 2 - over, 0.0], [x + w / 2, W / 2 + over, STICKER + 0.01]) for x in xs]


@solid
def lumber_bundle(size="2x10", seed=1):
    """A bundle of fresh-sawn dimensional lumber, 16 ft, 20 courses, on four 4 x 4 stickers. One end
    trimmed even, the other ragged, every board's end its own; the outside boards' edges uneven;
    three steel bands with their crimp seals. Printed upside down (its top on the plate), so the
    lumber is the base colour and the stickers print above BUNDLE_H."""
    bw, cols = BOARDS[size]
    rng = np.random.default_rng(seed)
    t = BUNDLE_H / 20
    W = cols * inch(bw)
    L = LUMBER_L
    z0 = STICKER
    parts = []
    for r in range(20):
        for c in range(cols):
            y0 = -W / 2 + c * inch(bw)
            y1 = y0 + inch(bw)
            if c == 0:
                y0 -= rng.uniform(-0.08, 0.14)
            if c == cols - 1:
                y1 += rng.uniform(-0.08, 0.14)
            parts.append(box([-rng.uniform(0.0, 0.12), y0, z0 + r * t], [L + rng.uniform(0.0, 0.7), y1, z0 + (r + 1) * t]))
    for i, x in enumerate((4.0, L / 2, L - 4.0)):
        for sgn in (-1, 1):
            parts.append(box([x - 0.25, sgn * (W / 2 - 0.2), z0], [x + 0.25, sgn * (W / 2 + 0.36), z0 + BUNDLE_H]))
        parts.append(box([x - 0.45, W / 2 - 0.2, z0 + BUNDLE_H * (0.3 + 0.15 * i)], [x + 0.45, W / 2 + 0.5, z0 + BUNDLE_H * (0.3 + 0.15 * i) + 0.8]))
    return flip(union(parts + _stickers(W)))


@solid
def wrapped_bundle(seed=1):
    """A bundle of lumber in its mill wrap, 16 ft on four stickers: the wrap's ends folded in, the top
    flap over the side ears; three bands with plastic corner guards at the top. Printed upside down
    (the wrapped top on the plate), wrap colour below BUNDLE_H, stickers above."""
    W = inch(45.5)
    L = LUMBER_L
    z0 = STICKER
    H = BUNDLE_H
    c = 0.3
    zt = z0 + H - c                     # where the top's chamfer starts
    wrap = (box([0, -W / 2, z0], [L, W / 2, zt]) + box([c, -W / 2 + c, z0], [L - c, W / 2 - c, z0 + H])).hull()
    parts = [wrap]
    ear = lambda sgn: poly([(sgn * (W / 2 - 0.1), zt - 0.05), (sgn * (W / 2 - 0.1), z0 + 0.25), (sgn * (W / 2 - 0.1 - 0.36 * W), zt - 0.05)])
    flap = poly([(-W / 2 + 0.15, z0 + 0.62 * H), (W / 2 - 0.15, z0 + 0.62 * H), (W / 2 - 0.15, zt - 0.05), (-W / 2 + 0.15, zt - 0.05)])
    for xa, xb, fa, fb in ((-0.15, 0.01, -0.28, 0.01), (L - 0.01, L + 0.15, L - 0.01, L + 0.28)):
        parts += [along_x(ear(-1), xa, xb), along_x(ear(1), xa, xb), along_x(flap, fa, fb)]
    for x in (4.5, L / 2, L - 4.5):
        for sgn in (-1, 1):
            parts.append(box([x - 0.25, sgn * (W / 2 - 0.1), z0], [x + 0.25, sgn * (W / 2 + 0.22), zt]))
            parts.append(box([x - 0.55, sgn * (W / 2 - 0.1), zt - 1.8], [x + 0.55, sgn * (W / 2 + 0.32), zt]))
    return flip(union(parts + _stickers(W)))


# ================================================================== 4. mining truck tires
TIRE_FRAME = 3.0          # yellow steel frame, then the black tire on its saddle
TIRE_R = inch(140) / 2    # a 40.00R57 haul-truck tire: 11 ft 8 in across
TIRE_ZC = TIRE_FRAME + 1.6 + TIRE_R


def _arc_text(text, r, cap, top=True, a0=5.7, a1=6.45, font="sans"):
    """Raised letters round the tire's axis (z), on the +z sidewall: along the top of the circle
    reading outward, or along the bottom reading upright."""
    from .storefront import text_cs
    glyphs = [(ch, text_cs(ch, cap=cap, font=font, grow=0.05)) for ch in text]
    widths = [(g.bounds()[2] - g.bounds()[0]) if not g.is_empty() else cap * 0.45 for _, g in glyphs]
    adv = [w + 0.32 for w in widths]
    rm = r + cap / 2
    total = sum(adv)
    out = []
    s = -total / 2
    for (ch, g), a in zip(glyphs, adv):
        mid = s + a / 2
        s += a
        if g.is_empty():
            continue
        ang = math.degrees(mid / rm)
        if top:
            cs = g.translate((0.0, r)).rotate(-ang)
        else:
            cs = g.translate((0.0, -r - cap)).rotate(ang)
        out.append(M.extrude(cs, a1 - a0).translate([0, 0, a0]))
    return union(out)


@solid
def otr_tire():
    """A 40.00R57 haul-truck tire standing in its steel cradle, the way they ride: a deep rock lug
    tread with open shoulders, a bulged sidewall lettered with its size, the bead's bore. A black
    saddle under it carries the tread at 45 degrees with cheeks either side, on a yellow frame.
    The bore is round at both faces and 45 degree pointed behind them, so its top needs no support."""
    R = TIRE_R
    P = [(8.3, 4.3), (9.0, 4.55), (9.8, 4.8), (11.0, 5.3), (12.5, 5.85), (14.2, 6.12), (15.8, 6.13), (17.2, 6.0),
         (18.4, 5.82), (19.2, 5.55), (19.8, 5.1), (20.2, 4.5), (R - 0.04, 3.6), (R, 1.8), (R, 0.0)]
    prof = P + [(r, -a) for (r, a) in reversed(P[:-1])]
    tire = revolve(prof, 144)
    cuts = []
    N = 26
    for k in range(N):
        for side in (1, -1):
            g = box([19.45, -0.7, 1.1], [R + 1.0, 0.7, 4.7]) + box([19.0, -0.7, 4.4], [R + 1.0, 0.7, 7.5])
            g = g.rotate([14.0, 0, 0])
            if side < 0:
                g = g.mirror([0, 0, 1])
            cuts.append(g.rotate([0, 0, 360.0 * (k + (0.5 if side < 0 else 0.0)) / N]))
    tire = tire - union(cuts)
    letters = union([_arc_text("40.00R57", 12.9, 2.4, top=True), _arc_text("RADIAL  E-4", 12.9, 2.4, top=False)])
    tire = union([tire, letters, letters.rotate([0, 180, 0])])
    zc = TIRE_ZC
    tire = tire.rotate([90, 0, 0]).translate([0, 0, zc])
    rb = 8.3
    tear = poly([(-rb * S2, zc + rb * S2 - 0.3), (rb * S2, zc + rb * S2 - 0.3), (rb * S2, zc + rb * S2), (0, zc + rb * math.sqrt(2)),
                 (-rb * S2, zc + rb * S2)])
    tire = tire - along_y(tear, -3.7, 3.7)
    z0 = TIRE_FRAME
    xt = R * S2
    zt = zc - R * S2
    saddle = along_y(poly([(-xt, zt), (xt, zt), (xt - (zt - z0), z0 - 0.01), (-xt + (zt - z0), z0 - 0.01)]), -5.35, 5.35)
    arc = [(x, zc - math.sqrt((R + 0.15) ** 2 - x * x)) for x in np.linspace(xt, -xt, 41)]
    cheek_cs = poly([(-xt, z0 - 0.01), (xt, z0 - 0.01)] + arc)
    cheeks = []
    for ya, yb in ((6.6, 7.4), (-7.4, -6.6)):
        cheeks.append(along_y(cheek_cs, ya, yb))
        o = 7.4 if ya > 0 else -7.4
        for x in (-8.0, 8.0):                    # stiffeners on the cheeks' outer faces
            ztop = zc - math.sqrt((R + 0.15) ** 2 - x * x)
            cheeks.append(box([x - 0.3, min(o, o + math.copysign(0.4, o)), z0 - 0.01], [x + 0.3, max(o, o + math.copysign(0.4, o)), ztop - 0.3]))
    # yellow frame: two beams with a channel down their outer faces, cross members, a deck plate
    fx = R + 1.2
    frame = []
    for sgn in (-1, 1):
        beam = box([-fx, sgn * 4.6, 0.0], [fx, sgn * 6.8, z0])
        frame.append(beam - box([-fx - 1, sgn * 6.3, 0.7], [fx + 1, sgn * 7.5, z0 - 0.7]))
    for x in (-fx + 0.8, -9.0, 9.0, fx - 0.8):
        frame.append(box([x - 0.8, -6.8, 0.0], [x + 0.8, 6.8, z0 - 0.6]))
    frame.append(box([-xt - 1.2, -7.6, z0 - 0.6], [xt + 1.2, 7.6, z0]))
    for x in (-fx, fx):                          # lifting eyes at the frame's ends, on the beams
        for sgn in (-1, 1):
            frame.append(box([x - (0.01 if x > 0 else -0.01), sgn * 4.9, 0.0], [x + (0.9 if x > 0 else -0.9), sgn * 6.5, 1.6]))
    return F._sheeted(lambda: union([tire, saddle] + cheeks + frame))()


# ================================================================== 5. sawlogs
LOG_BUNK = 2.0            # bunks, then the logs
LOG_L = ft(16.0)
LOG_BUNKS = (1.8, LOG_L / 2, LOG_L - 1.8)


def _log(x0, x1, y, z, r, butt_left, rng, upper=True):
    """A log: a little tapered and out of round, its bark fissured, rings and a heart check on each
    cut end, sometimes a knot. Returns (solid, smallest radius)."""
    ra, rb = (r * 1.03, r * 0.97) if butt_left else (r * 0.97, r * 1.03)
    ell = rng.uniform(1.0, 1.04)

    def ring(x, rr):
        return [(x, y + rr * ell * math.cos(t), z + rr * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 48, endpoint=False)]
    body = M.hull_points(ring(x0, ra) + ring(x1, rb))
    cuts = []
    for _ in range(14):
        th = math.radians(rng.uniform(-25.0, 205.0))
        xa = rng.uniform(x0 - 1.0, x0 + (x1 - x0) * 0.5)
        xb = rng.uniform(xa + (x1 - x0) * 0.3, x1 + 1.0)
        g = CS.square((1.4, rng.uniform(0.22, 0.34)), True).translate((r + 0.45, 0.0)).rotate(math.degrees(th))
        cuts.append(along_x(g.translate((y, z)), xa, xb))
    for xe, re, sgn in ((x0, ra, -1), (x1, rb, 1)):
        rings = [circle((y, z), re * f + 0.11, 40) - circle((y, z), re * f - 0.11, 40) for f in (0.28, 0.5, 0.68, 0.84)]
        a = rng.uniform(0, 360)
        check = CS.square((re * 0.62, 0.22)).rotate(a).translate((y, z))
        cs = cs_union(rings + [check])
        cuts.append(along_x(cs, xe - 0.3, xe + 0.25) if sgn < 0 else along_x(cs, xe - 0.25, xe + 0.3))
    knots = []
    if upper:
        for _ in range(int(rng.integers(0, 3))):
            th = rng.uniform(55.0, 125.0)
            xk = rng.uniform(x0 + 5, x1 - 5)
            k = M.cylinder(1.0, 0.6, 0.3, 12).rotate([th - 90.0, 0, 0])
            knots.append(k.translate([xk, y + (r - 0.3) * math.cos(math.radians(th)), z + (r - 0.3) * math.sin(math.radians(th))]))
    return union([body - union(cuts)] + knots), min(ra, rb)


@solid
def log_stack(seed=3):
    """Sixteen-foot sawlogs piled three, two and one on three log bunks with stakes, a wire-rope
    wrapper over each bunk. The bottom logs sit on 45 degree keels and the upper ones on webs in
    their valleys, all hidden in the pile and short of the ends; the bunks print in their colour to
    LOG_BUNK and the logs above."""
    rng = np.random.default_rng(seed)
    b = LOG_BUNK
    rs = [5.1, 5.6, 5.2]
    w = 2 * sum(rs)
    logs = []
    yy = -w / 2
    for r in rs:
        logs.append(((yy + r, b + r), r))
        yy += 2 * r
    c2 = [(tangent_on(*logs[0], *logs[1], 5.3), 5.3), (tangent_on(*logs[1], *logs[2], 4.9), 4.9)]
    c3 = [(tangent_on(*c2[0], *c2[1], 4.5), 4.5)]
    parts, keels, hull_cs = [], [], []
    for i, ((y, z), r) in enumerate(logs + c2 + c3):
        x0 = rng.uniform(-0.9, 0.3)
        x1 = LOG_L + rng.uniform(-0.3, 0.9)
        solid, rmin = _log(x0, x1, y, z, r, i % 2 == 0, rng, upper=i >= 2)
        parts.append(solid)
        hull_cs.append(circle((y, z), r * 1.07, 48))
        rk = rmin * 0.99
        if i < 3:
            cs = keel(y, z, rk, b)
        else:
            under = [p for p in logs + c2 if math.hypot(p[0][0] - y, p[0][1] - z) < p[1] + r + 0.2]
            zl = min(p[0][1] for p in under)
            cs = poly([(y - S2 * rk, z - S2 * rk), (y + S2 * rk, z - S2 * rk), (y, zl)])
        keels.append(along_x(cs, x0 + 0.4, x1 - 0.4))
    ext = max(abs(y) + r * 1.04 for (y, z), r in logs)
    hull = cs_union(hull_cs).hull()
    wrap_cs = (offset(hull, 0.35) - offset(hull, -0.05)) ^ CS.square((60.0, 60.0)).translate((-30.0, b - 0.01))
    bunks, stakes, wraps = [], [], []
    for xb in LOG_BUNKS:
        bunks.append(box([xb - 1.5, -ext - 2.4, 0.0], [xb + 1.5, ext + 2.4, b]))
        for sgn in (-1, 1):
            y0 = sgn * (ext - 0.12)
            stake = box([xb - 0.2, min(y0, y0 + sgn * 1.6), b - 0.01], [xb + 1.4, max(y0, y0 + sgn * 1.6), b + 13.5])
            top = M.hull_points([(xb + dx, y0 + sgn * dy, b + 13.49) for dx in (-0.2, 1.4) for dy in (0.0, 1.6)] +
                                [(xb + dx, y0 + sgn * dy, b + 14.0) for dx in (0.1, 1.1) for dy in (0.3, 1.3)])
            stakes += [stake, top]
        wraps.append(along_x(wrap_cs, xb - 1.4, xb - 0.8))
    return F._sheeted(lambda: union(parts + keels + bunks + stakes + wraps))()


# ================================================================== 6. track panels
PANEL_TIE = 2.0           # wood ties, then the rail and tie plates
PANEL_L = ft(39.0)
RAIL_H = inch(7.125)      # 132 lb rail


def _rail_cs(yc, z0):
    pts = [(-0.875, 0.0), (0.875, 0.0), (0.875, 0.22), (0.25, 0.62), (0.25, 1.34), (0.45, 1.54), (0.45, RAIL_H),
           (-0.45, RAIL_H), (-0.45, 1.54), (-0.25, 1.34), (-0.25, 0.62), (-0.875, 0.22)]
    return poly([(yc + y, z0 + z) for y, z in pts])


@solid
def track_panel(seed=1):
    """A 39 ft panel of new track as a rail gang lays it: 24 wood ties at 19 1/2 in, a little out of
    line as they come off the machine, some with end splits; tie plates; 132 lb rail on
    standard gauge. Stacked panels rest tie on rail head. Ties print brown, rail and plates grey."""
    rng = np.random.default_rng(seed)
    L = PANEL_L
    tw, tl, sp = inch(9), ft(8.5), inch(19.5)
    zt = PANEL_TIE
    yr = 16.5 / 2 + 0.45
    ties, plates, splits = [], [], []
    for x in np.arange(sp / 2, L - sp / 2 + 0.01, sp):
        x += rng.uniform(-0.12, 0.12)
        dy = rng.uniform(-0.35, 0.35)
        tie = box([-tw / 2, -tl / 2 + rng.uniform(-0.2, 0.2), 0.0], [tw / 2, tl / 2 + rng.uniform(-0.2, 0.2), zt])
        tie = tie.rotate([0, 0, rng.uniform(-1.2, 1.2)]).translate([x, dy, 0])
        if rng.uniform() < 0.3:
            ye = dy + (tl / 2 - 1.6) * (1 if rng.uniform() < 0.5 else -1)
            splits.append(box([x - 0.11, ye - 1.6, zt - 0.4], [x + 0.11, ye + 1.6, zt + 0.1]))
        ties.append(tie)
        for y in (-yr, yr):
            plates.append(box([x - inch(7.75) / 2, y - inch(14) / 2, zt - 0.01], [x + inch(7.75) / 2, y + inch(14) / 2, zt + 0.2]))
    rails = [along_x(_rail_cs(y, zt + 0.19), 0.0, L) for y in (-yr, yr)]
    return union([union(ties) - union(splits)] + plates + rails)


# ================================================================== 7. concrete ties
CTIE_SEAT = 2.6           # concrete ties to their rail seats, then the iron shoulders and the dunnage
CTIE_PITCH = 3.6


def _concrete_tie(x):
    """One prestressed concrete tie at x, across y: 8 ft 6 in, 11 in base, 9 in deep at the rail
    seats and 7 1/2 in in the middle, the sides battered."""
    L = ft(8.5)
    hb, ht = inch(11) / 2, inch(8.5) / 2
    zs, zm = CTIE_SEAT, CTIE_SEAT - 0.45
    prof = [(-L / 2, zs), (-6.5, zs), (-4.5, zm), (4.5, zm), (6.5, zs), (L / 2, zs)]     # full depth under the seats
    outline = poly([(-L / 2, 0.0), (L / 2, 0.0)] + prof[::-1])            # (y, z): the tie's elevation
    side = poly([(x - hb, -0.01), (x + hb, -0.01), (x + ht, zs + 0.3), (x - ht, zs + 0.3)])   # (x, z): battered sides
    return along_x(outline, x - hb, x + hb) ^ along_y(side, -L / 2 - 1, L / 2 + 1)


@solid
def concrete_tie_layer(n=15):
    """A layer of n concrete crossties side by side with the dunnage for the next layer on top, at
    the rail seats between the cast-in shoulders. Ties print in concrete grey to CTIE_SEAT; the
    shoulders (rusty iron) and the dunnage print above in one dark brown."""
    parts = []
    for k in range(n):
        x = CTIE_PITCH / 2 + k * CTIE_PITCH
        parts.append(_concrete_tie(x))
        for yr in (-8.7, 8.7):
            for sgn in (-1, 1):
                yc = yr + sgn * 1.125
                parts.append(box([x - 0.55, yc - 0.3, CTIE_SEAT - 0.01], [x + 0.55, yc + 0.3, CTIE_SEAT + 1.0]))
    Lx = n * CTIE_PITCH
    for yr in (-8.7, 8.7):
        parts.append(box([0.3, yr - 0.55, CTIE_SEAT - 0.01], [Lx - 0.3, yr + 0.55, CTIE_SEAT + 1.2]))
    return union(parts)


@solid
def tie_dunnage(n=15):
    """A 4 x 4 the bottom layer of concrete ties stands on, at a rail seat."""
    return box([0.3, -0.55, 0.0], [n * CTIE_PITCH - 0.3, 0.55, 1.2])


# ================================================================== 8. wood tie bundles
WTIE_DUN = 1.2            # new-lumber dunnage strips, then the creosoted ties


@solid
def wood_tie_row(seed=2, bundles=4):
    """Four bundles of new creosoted crossties, 25 to a bundle (five by five, 7 x 9 in by 8 ft 6 in),
    banded twice, on two dunnage strips near the tie ends. Each tie's length a little different;
    anti-split plates and checks on the ends."""
    rng = np.random.default_rng(seed)
    tw, th, tl = inch(9), inch(7), ft(8.5)
    z0 = WTIE_DUN
    Wb = 5 * tw
    parts, cuts = [], []
    for b in range(bundles):
        x0 = b * (Wb + 1.0)
        for i in range(5):
            for j in range(5):
                xa, za = x0 + i * tw, z0 + j * th
                ya, yb = -tl / 2 + rng.uniform(-0.35, 0.2), tl / 2 + rng.uniform(-0.2, 0.35)
                parts.append(box([xa, ya, za], [xa + tw, yb, za + th]))
                for ye, sgn in ((ya, -1), (yb, 1)):
                    if rng.uniform() < 0.55:                  # an S-iron or gang plate on the end
                        parts.append(box([xa + 0.5, ye - (0.15 if sgn < 0 else 0.05), za + 0.5],
                                         [xa + tw - 0.5, ye + (0.15 if sgn > 0 else 0.05), za + th - 0.5]))
                    elif rng.uniform() < 0.5:                 # a check
                        cuts.append(box([xa + rng.uniform(0.4, tw - 0.6), ye - 0.4, za + 0.3], [xa + rng.uniform(0.4, tw - 0.6) + 0.2, ye + 0.4, za + th - 0.3]))
        for yb_ in (-tl / 2 + 3.5, tl / 2 - 3.5):
            parts.append(box([x0 - 0.2, yb_ - 0.25, z0], [x0 + Wb + 0.2, yb_ + 0.25, z0 + 5 * th + 0.2]) -
                         box([x0 + 0.01, yb_ - 1, z0 - 1], [x0 + Wb - 0.01, yb_ + 1, z0 + 5 * th - 0.01]))
    Lx = bundles * (Wb + 1.0) - 1.0
    dun = [box([-0.4, y - 0.7, 0.0], [Lx + 0.4, y + 0.7, z0 + 0.01]) for y in (-tl / 2 + 2.0, tl / 2 - 2.0)]
    return union(parts + dun) - union(cuts)


# ================================================================== 9. granite blocks
STONE_BLOCK = 1.8         # timbers, then the stone
GRANITE_COLOURS = ["Light Gray", "Gray", "Light Gray", "Gray"]     # two shades, as two quarries' stone
BLOCKS = [((10.0, 5.0, 5.0), "B-17"), ((9.0, 5.0, 4.5), "B-21"), ((8.0, 5.5, 5.0), "C-4"), ((11.0, 4.5, 5.0), "A-30")]


@solid
def granite_block(i=0, seed=4):
    """A quarry block of building granite on three timbers: the corners and edges chipped, the plug
    and feather drill holes down one split face, the quarry's number painted on an end (raised)."""
    from .storefront import text_cs
    (lf, wf, hf), num = BLOCKS[i]
    rng = np.random.default_rng(seed + i)
    L, W, H = ft(lf), ft(wf), ft(hf)
    z0 = STONE_BLOCK
    pts = []
    for sx in (0, 1):
        for sy in (0, 1):
            for sz in (0, 1):
                cx, cy, cz = sx * L, sy * W - W / 2, z0 + sz * H
                ch = rng.uniform(0.2, 1.0, 3) if sz else np.array([rng.uniform(0.1, 0.4)] * 3)
                ix, iy, iz = (1 - 2 * sx), (1 - 2 * sy), (1 - 2 * sz)
                pts += [(cx + ix * ch[0], cy, cz), (cx, cy + iy * ch[1], cz), (cx, cy, cz + iz * ch[2] * (1 if sz else 0.0))]
    blk = M.hull_points([(x + rng.uniform(-0.15, 0.15) * (z > z0 + 0.1), y + rng.uniform(-0.15, 0.15) * (z > z0 + 0.1), z) for x, y, z in pts])
    cuts = []
    # split faces (the long sides and the top) broken into facets: big slabs tilted a few degrees,
    # each biting up to 0.7 mm into part of a face, leave ridges where they meet
    for fn, (cx, cy, cz) in (((0, -1, 0), (L / 2, -W / 2, z0 + H / 2)), ((0, 1, 0), (L / 2, W / 2, z0 + H / 2)),
                             ((0, 0, 1), (L / 2, 0.0, z0 + H))):
        for _ in range(5):
            slab = box([-40, -40, 0.0], [40, 40, 20.0])
            n = np.array(fn, float)
            # orient the slab's bottom face to the face's normal, tilted, then push it in
            if fn == (0, 0, 1):
                rot = [rng.uniform(-2.5, 2.5), rng.uniform(-2.5, 2.5), 0]
            elif fn == (0, -1, 0):
                rot = [90 + rng.uniform(-2.5, 2.5), 0, rng.uniform(-2.5, 2.5)]
            else:
                rot = [-90 + rng.uniform(-2.5, 2.5), 0, rng.uniform(-2.5, 2.5)]
            off = np.array([cx + rng.uniform(-L / 3, L / 3), cy, cz]) - n * rng.uniform(0.1, 0.4)
            if fn == (0, 0, 1):
                off[1] += rng.uniform(-W / 3, W / 3)
            else:
                off[2] += rng.uniform(-H / 3, H / 3)
            cuts.append(slab.rotate(rot).translate(list(off)))
    face = -W / 2 if i % 2 == 0 else W / 2
    for x in np.arange(1.2, L - 1.0, 1.7):
        cuts.append(M.cylinder(H + 2, 0.4, 0.4, 12).translate([x, face, z0 - 1]))
    blk = blk - union(cuts)
    lab = text_cs(num, cap=2.4, font="sans", grow=0.05)
    tag = M.extrude(lab, 0.35).rotate([90, 0, 90]).translate([L - 0.05, 0.0, z0 + H * 0.45])
    timbers = [box([x - 1.0, -W / 2 - 1.0, 0.0], [x + 1.0, W / 2 + 1.0, z0 + 0.01]) for x in (1.2, L / 2, L - 1.2)]
    wedges = []
    for x in (1.2, L - 1.2):
        for sgn in (-1, 1):
            y0 = sgn * (W / 2 + 0.05)
            wedges.append(along_x(poly([(y0, z0 - 0.01), (y0, z0 + 0.9), (y0 + sgn * 0.4, z0 + 0.9), (y0 + sgn * 0.95, z0 - 0.01)]), x - 0.9, x + 0.9))
    return F._sheeted(lambda: union([blk, tag] + timbers + wedges))()


# ================================================================== 10. brick cubes
@solid
def brick_cube(seed=1):
    """A cube of packaged face brick as it leaves the plant: 16 courses stacked tight, stretchers
    and headers by turns, two fork voids through the bottom, banded both ways."""
    rng = np.random.default_rng(seed)
    Lx, Wy, c = ft(4.0), ft(3.33), 0.6
    n = 16
    H = n * c
    cube = box([0, 0, 0], [Lx, Wy, H])
    cuts = []
    for k in range(1, n):
        z = k * c
        cuts.append(box([-1, -1, z - 0.1], [Lx + 1, 0.12, z + 0.1]))
        cuts.append(box([-1, Wy - 0.12, z - 0.1], [Lx + 1, Wy + 1, z + 0.1]))
        cuts.append(box([-1, -1, z - 0.1], [0.12, Wy + 1, z + 0.1]))
        cuts.append(box([Lx - 0.12, -1, z - 0.1], [Lx + 1, Wy + 1, z + 0.1]))
    bl, bw = inch(7.625) + 0.05, inch(3.625) + 0.03
    for k in range(n):
        z0, z1 = k * c + 0.1, (k + 1) * c - 0.1
        step = bl if k % 2 == 0 else bw
        off = rng.uniform(0, step)
        for x in np.arange(off, Lx, step):                   # the long faces
            for y0, y1 in ((-1, 0.12), (Wy - 0.12, Wy + 1)):
                cuts.append(box([x - 0.12, y0, z0], [x + 0.12, y1, z1]))
        step2 = bw if k % 2 == 0 else bl
        for y in np.arange(rng.uniform(0, step2), Wy, step2):  # the short faces
            for x0, x1 in ((-1, 0.12), (Lx - 0.12, Lx + 1)):
                cuts.append(box([x0, y - 0.12, z0], [x1, y + 0.12, z1]))
    for y in np.arange(bw, Wy - 0.1, bw):                     # top course joints, a layer deep
        cuts.append(box([0.3, y - 0.12, H - 0.2], [Lx - 0.3, y + 0.12, H + 1]))
    for x in (Lx * 0.27, Lx * 0.73):                          # fork voids, two courses tall
        cuts.append(box([x - 0.7, -1, -1], [x + 0.7, Wy + 1, 2 * c]))
    cube = cube - union(cuts)
    bands = []
    for x in (Lx * 0.27, Lx * 0.73):
        bands.append(box([x - 0.2, -0.15, 2 * c], [x + 0.2, Wy + 0.15, H + 0.2]) - box([x - 1, 0.0, -1], [x + 1, Wy, H]))
    for y in (Wy * 0.3, Wy * 0.7):
        bands.append(box([-0.15, y - 0.2, 0.0], [Lx + 0.15, y + 0.2, H + 0.2]) - box([0.0, y - 1, -1], [Lx, y + 1, H]))
    return union([cube] + bands)


# ================================================================== 11. ingot molds
MOLD_STOOL = 1.6          # the cast-iron stool, then the mold


@solid
def ingot_mold():
    """A big-end-down slab ingot mold on its stool: a tapered cast-iron tube 8 ft tall, fluted down
    its broad faces, a thickened top rim on a 45 degree underside, a lifting lug on each end."""
    z0 = MOLD_STOOL
    H = ft(8.0)
    bx, by, tx, ty = 8.6, 15.6, 7.6, 14.6               # outside, bottom and top
    wall = 1.8
    r = 1.0

    def rr(x, y, z):
        return [(sx * (x / 2 - r) + r * math.cos(t) * sx, sy * (y / 2 - r) + r * math.sin(t) * sy, z)
                for sx in (-1, 1) for sy in (-1, 1) for t in np.linspace(0, math.pi / 2, 5)]
    outer = M.hull_points(rr(bx, by, z0) + rr(tx, ty, z0 + H))
    inner = M.hull_points(rr(bx - 2 * wall, by - 2 * wall, z0 - 0.5) + rr(tx - 2 * wall, ty - 2 * wall, z0 + H + 0.5))
    mold = outer - inner
    flutes = []
    for y in np.linspace(-by / 2 + 2.2, by / 2 - 2.2, 7):
        for sgn in (-1, 1):
            flutes.append(M.hull_points([(sgn * (bx / 2 + 0.3), y + dy, z0 + 1.2) for dy in (-0.35, 0.35)] +
                                        [(sgn * (bx / 2 - 0.3), y + dy, z0 + 1.2) for dy in (-0.35, 0.35)] +
                                        [(sgn * (tx / 2 + 0.3), y + dy, z0 + H - 2.4) for dy in (-0.35, 0.35)] +
                                        [(sgn * (tx / 2 - 0.3), y + dy, z0 + H - 2.4) for dy in (-0.35, 0.35)]))
    mold = mold - union(flutes)
    rim = M.hull_points(rr(tx, ty, z0 + H - 1.9) + rr(tx + 0.9, ty + 0.9, z0 + H - 1.45) + rr(tx + 0.9, ty + 0.9, z0 + H)) - inner
    lugs = []
    for sgn in (-1, 1):
        y0 = sgn * (ty / 2 - 0.1)
        lug = M.hull_points([(x, y0, z) for x in (-1.6, 1.6) for z in (z0 + H - 7.0, z0 + H - 2.0)] +
                            [(x, y0 + sgn * 2.0, z) for x in (-1.6, 1.6) for z in (z0 + H - 5.0, z0 + H - 2.6)])
        hole = M.cylinder(4.0, 0.55, 0.55, 16).rotate([0, 90, 0]).translate([-2.0, y0 + sgn * 1.2, z0 + H - 3.7])
        lugs.append(lug - hole)
    stool = M.hull_points(rr(bx + 2.4, by + 2.4, 0.0) + rr(bx + 2.4, by + 2.4, z0 - 0.5) + rr(bx + 1.4, by + 1.4, z0 + 0.01))
    return union([mold, rim, stool] + lugs)


# ================================================================== 12. HV cable reels
REEL_R = ft(11.5) / 2     # steel drum flanges 11 ft 6 in across
REEL_W = ft(7.6)          # between the flanges' outer faces
REEL_FL = 1.4             # flange plate
REEL_CORE = ft(5.0) / 2


@solid
def reel_flange():
    """A steel cable drum's flange, printed flat on its inner face: twelve radial ribs and a ring
    stiffener on the outer face, the arbor plate with its bolt circle, the arbor hole and two
    driving-pin holes, a lifting hole near the rim."""
    R = REEL_R
    plate = M.cylinder(REEL_FL, R, R, 120)
    rim = M.cylinder(REEL_FL + 0.6, R, R, 120) - M.cylinder(REEL_FL + 2, R - 0.7, R - 0.7, 120).translate([0, 0, -1])
    ribs = [box([REEL_CORE * 0.55, -0.35, REEL_FL - 0.01], [R - 0.7, 0.35, REEL_FL + 0.7]).rotate([0, 0, 30 * k]) for k in range(12)]
    ring = M.cylinder(0.7, REEL_CORE + 0.5, REEL_CORE + 0.5, 96).translate([0, 0, REEL_FL - 0.01]) - M.cylinder(4, REEL_CORE - 0.2, REEL_CORE - 0.2, 96).translate([0, 0, -1])
    arbor = M.cylinder(REEL_FL + 1.0, 5.0, 5.0, 64)
    bolts = [M.cylinder(0.35, 0.4, 0.4, 10).translate([4.0 * math.cos(math.radians(a)), 4.0 * math.sin(math.radians(a)), REEL_FL + 0.99]) for a in range(0, 360, 30)]
    holes = [M.cylinder(6, 2.2, 2.2, 40).translate([0, 0, -1])] + \
            [M.cylinder(6, 0.75, 0.75, 20).translate([x, 0, -1]) for x in (-3.5, 3.5)] + \
            [M.cylinder(6, 1.0, 1.0, 20).translate([0, R - 2.4, -1])]
    return union([plate, rim, ring, arbor] + ribs + bolts) - union(holes)


@solid
def reel_barrel(lagged=False):
    """The drum's barrel between the flanges, printed standing on end: the last layer of HV cable
    wound on it, turn by turn, its tail clamped; or (``lagged``) the wood lagging battens that
    protect the cable, banded twice."""
    w = REEL_W - 2 * REEL_FL
    ro = REEL_R - 2.2
    if not lagged:
        body = M.cylinder(w, ro, ro, 120)
        d = inch(4.2)
        turns = [M.cylinder(d * 0.42, ro + 0.1, ro + 0.1, 120).translate([0, 0, z]) - M.cylinder(d * 0.42 + 0.2, ro - 0.2, ro - 0.2, 120).translate([0, 0, z - 0.1])
                 for z in np.arange(0.1, w - d * 0.4, d)]
        grooves = M.cylinder(w, ro + 1, ro + 1, 120) - M.cylinder(w + 2, ro - 0.16, ro - 0.16, 120).translate([0, 0, -1])
        body = body - grooves + union(turns)
        tail = M.cylinder(w * 0.6, 0.55, 0.55, 16).translate([ro - 0.1, 0.0, w * 0.2])
        clamp = box([ro - 0.6, -0.9, w * 0.45], [ro + 0.85, 0.9, w * 0.55])
        out = union([body, tail, clamp])
    else:
        n = 44
        out = M.cylinder(w, ro - 0.6, ro - 0.6, 120)
        for k in range(n):
            a = 360.0 * k / n
            out = out + box([ro - 0.75, -0.95 * math.pi * ro / n, 0.0], [ro, 0.95 * math.pi * ro / n, w]).rotate([0, 0, a])
        for z in (w * 0.22, w * 0.78):
            out = out + (M.cylinder(0.5, ro + 0.2, ro + 0.2, 120).translate([0, 0, z]) - M.cylinder(1.0, ro - 0.3, ro - 0.3, 120).translate([0, 0, z - 0.2]))
    core = M.cylinder(w, 2.2, 2.2, 40).translate([0, 0, -0.01])
    return out - core.scale([1, 1, 1.01])


REEL_CHOCK_D = 7.5        # chocks' centres from the drum's centre


@solid
def reel_chock():
    """A timber chock under a drum's flange rim, its top cut to the rim's curve on the drum's side
    (the drum's centre is at x = -REEL_CHOCK_D)."""
    R = REEL_R
    blk = box([-3.6, -1.6, 0.0], [3.6, 1.6, 3.4])
    rim = M.cylinder(4, R, R, 200).rotate([90, 0, 0]).translate([-REEL_CHOCK_D, 2, R])
    return blk - rim


# ================================================================== crawler tracks (batch 3)
def track_unit(xa, xb, rr, rf, h, yi, yo, n_road, rw, z0=0.0, band=0.55, recess=0.4, rollers=0, pitch=0.75):
    """One crawler track from x = xa (rear, sprocket radius rr) to xb (front, idler radius rf), its top
    run at z0 + h, across yi..yo with the outer face at yo (yo > yi; mirror for the other side).
    The run rises from the ground at 45 degrees into the sprocket and idler, so nothing overhangs.
    The loop's inside is recessed on the outer face with the road wheels, return rollers, idler and
    toothed sprocket standing in it; shoe joints cut across the top run and down the band's face."""
    zt = z0 + h
    cf, cr = (xb - rf, zt - rf), (xa + rr, zt - rr)
    xf = cf[0] + rf * S2 - (cf[1] - rf * S2 - z0)
    xr = cr[0] - rr * S2 + (cr[1] - rr * S2 - z0)
    prof = cs_union([circle(cf, rf, 40), circle(cr, rr, 40), poly([(xr, z0), (xf, z0), (cf[0], cf[1]), (cr[0], cr[1])])]).hull()
    unit = along_y(prof, yi, yo)
    inner = offset(prof, -band)
    unit = unit - along_y(inner, yo - recess, yo + 1.0)
    wheels = []
    wz = z0 + band + rw - 0.05
    xs = np.linspace(xr + rw * 0.6, xf - rw * 0.6, n_road)
    for x in xs:
        wheels.append(M.cylinder(recess + 0.02, rw, rw, 28).rotate([-90, 0, 0]).translate([x, yo - recess - 0.01, wz]))
        wheels.append(M.cylinder(0.25, rw * 0.45, rw * 0.38, 20).rotate([-90, 0, 0]).translate([x, yo - 0.02, wz]))
    for x in np.linspace(cr[0] + rr, cf[0] - rf, rollers + 2)[1:-1] if rollers else []:
        rret = 0.9
        wheels.append(M.cylinder(recess + 0.02, rret, rret, 20).rotate([-90, 0, 0]).translate([x, yo - recess - 0.01, zt - band - rret + 0.05]))
    wheels.append(M.cylinder(recess + 0.02, rf - band - 0.1, rf - band - 0.1, 32).rotate([-90, 0, 0]).translate([cf[0], yo - recess - 0.01, cf[1]]))
    wheels.append(M.cylinder(0.3, (rf - band) * 0.4, (rf - band) * 0.35, 20).rotate([-90, 0, 0]).translate([cf[0], yo - 0.02, cf[1]]))
    teeth = cs_union([circle((0, 0), rr - band - 0.55, 32)] +
                     [CS.square((0.7, 1.1), True).translate((rr - band - 0.55, 0.0)).rotate(360.0 * k / 11) for k in range(11)])
    wheels.append(along_y(teeth.translate(cr), yo - recess - 0.01, yo - 0.02))
    wheels.append(M.cylinder(0.3, (rr - band) * 0.45, (rr - band) * 0.4, 20).rotate([-90, 0, 0]).translate([cr[0], yo - 0.02, cr[1]]))
    unit = union([unit] + wheels)
    cuts = []
    for x in np.arange(cr[0], cf[0], pitch):                      # shoe joints across the top run
        cuts.append(box([x - 0.1, yi - 1, zt - 0.22], [x + 0.1, yo + 1, zt + 1]))
    for x in np.arange(xr, xf, pitch):                            # and down the band's face on the bottom run
        cuts.append(box([x - 0.1, yo - 0.18, z0 - 1], [x + 0.1, yo + 1, z0 + band]))
    return unit - union(cuts)


def tracks(xa, xb, rr, rf, h, yc, tw, n_road, rw, **kw):
    """Both tracks, centred at y = +-yc, tw wide."""
    right = track_unit(xa, xb, rr, rf, h, yc - tw / 2, yc + tw / 2, n_road, rw, **kw)
    return right + right.mirror([0, 1, 0])


def _side(pts, ya, yb):
    """A side profile [(x, z), ...] extruded across ya..yb."""
    return along_y(poly(pts), ya, yb)


def _grille(x0, x1, y0, y1, z, n, d=0.22, along="x"):
    """Grooves in a top face at z: n slots across x0..x1 (``along`` x: slots run across y)."""
    out = []
    if along == "x":
        for x in np.linspace(x0, x1, n):
            out.append(box([x - 0.12, y0, z - d], [x + 0.12, y1, z + 1]))
    else:
        for y in np.linspace(y0, y1, n):
            out.append(box([x0, y - 0.12, z - d], [x1, y + 0.12, z + 1]))
    return out


# ================================================================== 13. main battle tank
TANK_TRACK = 9.6          # steel-grey tracks and running gear to the top run, then the olive hull
TANK_GUN_Z = TANK_TRACK + 5.4 + 5.0


@solid
def tank():
    """A main battle tank as it rides on a flatcar: turret turned to the rear, the gun on its travel
    lock over the engine deck (the barrel is a separate piece that plugs into the mantlet). Seven
    road wheels a side behind side skirts, a long shallow glacis, a low wedge turret with its
    bustle, cupola, hatches, sights and smoke dischargers, grilles on the engine deck. Generic,
    not any one army's tank."""
    zt = TANK_TRACK
    zd = zt + 5.4
    trk = tracks(0.0, 74.0, 4.2, 3.6, zt, 16.1, 7.4, 7, 3.9, rollers=2)
    upper = _side([(4.2, zt - 0.01), (70.4, zt - 0.01), (75.0, zt + 4.6), (68.0, zd), (2.0, zd), (-0.6, zd - 0.6), (-0.6, zt + 4.8)], -20.6, 20.6)
    belly = _side([(8.0, 4.0), (68.0, 4.0), (68.0 + zt - 4.0, zt + 0.01), (8.0 - zt + 4.0, zt + 0.01)], -12.3, 12.3)
    skirts = []
    for sgn in (-1, 1):
        sk = _side([(5.0, 5.4), (70.0, 5.4), (73.0, zt + 0.3), (3.0, zt + 0.3)], 19.8 if sgn > 0 else -20.6, 20.6 if sgn > 0 else -19.8)
        for x in np.arange(14.0, 70.0, 10.5):
            sk = sk - box([x - 0.12, sgn * 20.4 - 1, 5.0], [x + 0.12, sgn * 20.4 + 1, zt + 0.5])
        skirts.append(sk)
    hull = union([trk, upper, belly] + skirts)
    det = []
    for sgn in (-1, 1):                                          # fender boxes, headlights with guards, tow eyes
        det.append(box([46.0, sgn * 14.5, zd - 0.01], [60.0, sgn * 20.2, zd + 2.2]))
        det.append(box([70.0, sgn * 16.5 - 1.2, zt + 4.2], [72.6, sgn * 16.5 + 1.2, zt + 5.6]))
        det.append(box([73.4, sgn * 9.0 - 1.0, zt + 1.0], [75.4, sgn * 9.0 + 1.0, zt + 3.6]))
    cuts = _grille(3.5, 21.0, -12.0, 12.0, zd, 14) + _grille(46.5, 59.5, 15.0, 19.7, zd + 2.2, 0)
    # turret, turned to the rear (its gun along -x)
    xt = 44.0
    base = [(20, -6), (20, 6), (12, 17), (-20, 17), (-26, 14), (-26, -14), (-20, -17), (12, -17)]
    roof = [(14, -5), (14, 5), (8, 15), (-19, 15.5), (-24, 12.5), (-24, -12.5), (-19, -15.5), (8, -15)]
    tz = zd + 9.0
    turret = M.hull_points([(xt - u, v, zd - 0.01) for u, v in base] + [(xt - u, v, tz) for u, v in roof])
    tdet = [box([xt - 21.5, -4.2, zd + 1.6], [xt - 17.0, 4.2, zd + 8.0]),                 # mantlet
            M.cylinder(1.5, 3.0, 3.0, 28).translate([xt + 6, 7.0, tz - 0.01]),           # commander's cupola
            M.cylinder(0.5, 2.6, 2.4, 28).translate([xt + 6, 7.0, tz + 1.49]),
            M.cylinder(0.45, 2.4, 2.2, 28).translate([xt + 6, -7.0, tz - 0.01]),         # loader's hatch
            box([xt - 2.0, -10.2, tz - 0.01], [xt + 3.4, -9.6, tz + 0.6]),               # loader's MG, stowed flat
            box([xt - 13.0, 8.5, tz - 0.01], [xt - 9.0, 12.0, tz + 2.4]),                # gunner's sight
            box([xt + 14.0, -11.0, zd - 0.01], [xt + 26.0, 11.0, zd + 3.6]),             # stowage on the deck at the bustle
            M.cylinder(1.4, 0.35, 0.3, 10).translate([xt + 22.0, 11.5, tz - 0.01]),       # antenna bases
            M.cylinder(1.4, 0.35, 0.3, 10).translate([xt + 22.0, -11.5, tz - 0.01])]
    for sgn in (-1, 1):                                          # smoke dischargers on the cheeks
        for k in range(3):
            tdet.append(box([xt - 2.0 - 1.0 * k, sgn * 15.7 - 0.7, zd + 6.0], [xt - 1.2 - 1.0 * k, sgn * 15.7 + 0.7, zd + 7.4]))
    gun = M.cylinder(4.0, 0.68, 0.68, 20).rotate([0, -90, 0]).translate([xt - 18.0, 0.0, TANK_GUN_Z])
    # travel lock on the rear deck: an A-frame with a saddle under the barrel
    zg = TANK_GUN_Z
    lock = [box([2.0, -2.4, zd - 0.01], [4.2, 2.4, zd + 0.8])]
    for sgn in (-1, 1):
        lock.append(_side([(2.4, zd), (3.8, zd), (3.5, zg - 1.9), (2.7, zg - 1.9)], sgn * 1.6 - 0.4, sgn * 1.6 + 0.4))
    sad = box([2.2, -2.0, zg - 2.1], [4.0, 2.0, zg - 1.0]) - M.cylinder(3, 1.3, 1.3, 24).rotate([0, 90, 0]).translate([1.5, 0, zg])
    lock.append(sad)
    return union([hull, turret] + det + tdet + lock) - union(cuts + [gun])


@solid
def tank_barrel():
    """The tank's gun, printed lying with its underside cut flat (it rests on the travel lock with
    the flat down): thermal sleeve with its clamp bands, the bore evacuator, the muzzle; a peg that
    plugs into the mantlet."""
    segs = [(0.0, 3.0, 0.62), (3.0, 4.0, 1.7), (4.0, 26.0, 1.35), (26.0, 27.5, 1.5), (27.5, 35.0, 1.8), (35.0, 36.5, 1.5),
            (36.5, 64.5, 1.2), (64.5, 67.0, 1.3)]
    parts = [M.cylinder(b - a, r, r, 32).rotate([0, 90, 0]).translate([a, 0, 0]) for a, b, r in segs]
    for x in (10.0, 18.0, 46.0, 56.0):
        r = 1.35 if x < 26 else 1.2
        parts.append(M.cylinder(0.6, r + 0.15, r + 0.15, 32).rotate([0, 90, 0]).translate([x, 0, 0]))
    b = union(parts)
    b = b - M.cylinder(1.0, 0.55, 0.55, 20).rotate([0, 90, 0]).translate([66.5, 0, 0])
    zc = 0.84                                                      # cut 0.36 under the thin tube's axis (0.3 r)
    b = b.translate([0, 0, zc])
    return b ^ box([-1, -3, 0.0], [70, 3, 6])


# ================================================================== 14. armoured personnel carriers
APC_TRACK = 7.2


@solid
def apc():
    """A tracked armoured personnel carrier: a plain aluminium box on five road wheels a side, the
    glacis with its trim vane folded down, headlights in guards, the driver's hatch and the
    commander's cupola with its MG stowed, the big cargo hatch, the rear ramp with its door and
    hinges, an exhaust on the right front. Generic."""
    zt = APC_TRACK
    zr = zt + 13.8
    trk = tracks(0.0, 50.0, 3.0, 3.0, zt, 12.2, 6.0, 5, 3.0)
    upper = _side([(2.8, zt - 0.01), (47.2, zt - 0.01), (52.6, zt + 5.4), (40.0, zr), (0.0, zr), (0.0, zt + 2.8)], -15.4, 15.4)
    belly = _side([(6.0, 3.6), (44.0, 3.6), (44.0 + zt - 3.6, zt + 0.01), (6.0 - zt + 3.6, zt + 0.01)], -9.1, 9.1)
    body = union([trk, upper, belly])
    # trim vane folded on the glacis: a raised panel in the glacis' plane
    g0, g1 = (52.6, zt + 5.4), (40.0, zr)
    n = np.array([g1[1] - g0[1], -(g1[0] - g0[0])])
    n = n / np.linalg.norm(n) * 0.45
    vane = _side([(g0[0] - 1.2, g0[1] + 0.9), (g1[0] + 1.6, g1[1] - 1.2), (g1[0] + 1.6 + n[0] * -1, g1[1] - 1.2 - n[1] * -1),
                  (g0[0] - 1.2 + n[0] * -1, g0[1] + 0.9 - n[1] * -1)], -12.5, 12.5)
    det = [vane]
    for sgn in (-1, 1):
        det.append(box([49.0, sgn * 13.0 - 1.1, zt + 4.4], [51.4, sgn * 13.0 + 1.1, zt + 6.2]))
    det += [M.cylinder(0.5, 2.6, 2.4, 24).translate([34.0, -8.0, zr - 0.01]),                  # driver's hatch
            M.cylinder(1.6, 3.0, 3.0, 28).translate([28.0, 7.5, zr - 0.01]),                   # cupola
            M.cylinder(0.5, 2.7, 2.5, 28).translate([28.0, 7.5, zr + 1.59]),
            box([22.0, 9.6, zr + 2.0], [32.0, 10.2, zr + 2.6]),                                 # its MG, stowed along the roof
            box([22.0, 9.4, zr + 1.5], [23.0, 10.4, zr + 2.1]),
            box([4.0, -7.0, zr - 0.01], [21.0, 7.0, zr + 0.35]),                                # cargo hatch
            M.cylinder(1.0, 0.8, 0.8, 16).translate([15.0, 10.5, zr - 0.01]),                  # vent
            M.cylinder(0.5, 0.8, 1.3, 16).translate([15.0, 10.5, zr + 0.99]),
            box([42.0, 15.39, zt + 3.0], [46.0, 16.2, zt + 9.0]),                               # exhaust guard on the right side
            M.cylinder(3.0, 0.6, 0.6, 14).translate([44.0, 15.8, zt + 8.99])]
    det += [box([-0.4, y - 1.2, zt + 3.0], [0.01, y + 1.2, zt + 4.2]) for y in (-9.0, 9.0)]   # ramp hinges
    det += [box([-0.4, sgn * 12.5 - 0.8, zt + 9.0], [0.01, sgn * 12.5 + 0.8, zt + 10.5]) for sgn in (-1, 1)]  # tail lights
    cuts = [box([-1, -10.5, zt + 2.8], [0.12, -10.26, zr - 1.0]), box([-1, 10.26, zt + 2.8], [0.12, 10.5, zr - 1.0]),
            box([-1, -10.5, zr - 1.24], [0.12, 10.5, zr - 1.0]),                                 # ramp outline
            box([-1, 1.5, zt + 3.6], [0.12, 1.74, zr - 2.4]), box([-1, 6.76, zt + 3.6], [0.12, 7.0, zr - 2.4]),
            box([-1, 1.5, zr - 2.64], [0.12, 7.0, zr - 2.4])]                                    # door in the ramp
    cuts += [box([4.2, y - 0.12, zr + 0.13], [20.8, y + 0.12, zr + 1]) for y in (0.0,)]
    return union([body] + det) - union(cuts)


# ================================================================== 15. crawler excavator
EXC_TRACK = 10.4          # tracks, carbody and swing ring, then the yellow upper
EXC_SWING = 28.0          # swing centre's x


@solid
def excavator():
    """A 20 tonne class crawler excavator without its front (boom, arm and bucket are separate
    pieces): long-frame tracks with rollers and carriers, the carbody and swing ring, the upper with
    its cab on the left, engine hood and grilles, exhaust, fuel and tool boxes on the right, the
    rounded counterweight, handrails, and the boom-foot bracket the boom slides into."""
    zc = EXC_TRACK
    trk = tracks(0.0, 51.0, 4.0, 3.7, 10.2, 13.7, 6.9, 7, 1.4, rollers=2)
    carbody = _side([(14.0, 3.2), (38.0, 3.2), (42.0, 7.2), (42.0, 10.21), (10.0, 10.21), (10.0, 7.2)], -10.3, 10.3)
    ring = M.cylinder(zc - 9.6, 9.0, 9.0, 48).translate([EXC_SWING, 0, 9.6])
    xs = EXC_SWING
    R = 30.0
    zb = zc
    plan = [(xs + 14.0, -15.8), (xs + 14.0, 15.8), (xs - 18.0, 15.8)] + \
           [(xs + R * math.cos(t), R * math.sin(t)) for t in np.linspace(math.radians(148), math.radians(212), 9)] + [(xs - 18.0, -15.8)]
    deck_top = zb + 6.0
    house = M.hull_points([(x, y, zb) for x, y in plan if x >= 4.0] + [(x, y, deck_top) for x, y in plan])
    # counterweight: taller at the back, its underside rising at 45 degrees behind the tracks
    cw = M.hull_points([(x, y, z) for x, y in plan if x < xs - 12.0 for z in (deck_top - 0.01, zb + 17.0)] +
                       [(xs - 12.0, y, zb + 8.0) for y in (-15.8, 15.8)])
    cut45 = M.hull_points([(4.0, y, zb - 0.01) for y in (-20, 20)] + [(-10.0, y, zb - 0.01) for y in (-20, 20)] +
                          [(-10.0, y, zb + 14.0) for y in (-20, 20)])
    upper = union([house, cw]) - cut45
    # cab on the left front
    cab = M.hull_points([(x, y, z) for x in (xs + 1.0, xs + 13.6) for y in (-15.6, -5.0) for z in (deck_top - 0.01,)] +
                        [(x, y, zb + 24.0) for x in (xs + 1.0, xs + 12.4) for y in (-15.6, -5.0)])
    roof = M.hull_points([(x, y, zb + 24.0) for x in (xs + 0.6, xs + 12.8) for y in (-15.9, -4.7)] +
                         [(x, y, zb + 24.6) for x in (xs + 0.9, xs + 12.5) for y in (-15.7, -4.9)])
    panes = []
    for (x0, x1, y0, y1) in ((xs + 2.0, xs + 12.0, -15.7, -15.3), (xs + 2.0, xs + 12.0, -5.3, -4.9)):
        panes.append(box([x0, y0 - 0.2, deck_top + 2.5], [x1, y1 + 0.2, zb + 23.0]) - box([x0 - 1, -14.9, deck_top], [x1 + 1, -5.7, zb + 25]))
    front = M.hull_points([(xs + 13.7, y, z) for y in (-14.8, -5.8) for z in (deck_top + 1.5,)] + [(xs + 12.5, y, zb + 23.2) for y in (-14.8, -5.8)] +
                          [(xs + 13.0, y, deck_top + 1.5) for y in (-14.8, -5.8)] + [(xs + 11.8, y, zb + 23.2) for y in (-14.8, -5.8)])
    # engine hood, exhaust, right-hand boxes, handrails, boom-foot bracket
    hood = box([xs - 18.0, -15.0, deck_top - 0.01], [xs - 1.0, 15.0, zb + 13.0])
    rbox = box([xs + 1.0, 5.0, deck_top - 0.01], [xs + 13.8, 15.6, zb + 11.0])
    det = [cab, roof, hood, rbox,
           M.cylinder(5.0, 0.7, 0.7, 14).translate([xs - 6.0, 9.0, zb + 12.99]),
           box([xs - 15.0, -13.0, zb + 12.99], [xs - 8.0, -6.0, zb + 15.5])]
    for y in (14.2, 4.6):
        det.append(box([xs - 16.0, y - 0.25, zb + 12.99], [xs - 2.0, y + 0.25, zb + 15.0]))
    for x in (xs - 15.5, xs - 9.0, xs - 2.5):
        for y in (14.2,):
            det.append(box([x - 0.25, y - 0.25, zb + 12.99], [x + 0.25, y + 0.25, zb + 15.0]))
    for sgn in (-1, 1):
        det.append(box([xs + 13.5, sgn * 3.6 - 0.4, deck_top - 0.01], [xs + 19.0, sgn * 3.6 + 0.4, zb + 10.5]))
    cuts = _grille(xs - 10.5, xs - 2.0, -14.0, -8.0, zb + 13.0, 7) + _grille(xs - 10.5, xs - 2.0, 7.0, 13.0, zb + 13.0, 7)
    return union([trk, carbody, ring, upper] + det + panes + [front]) - union(cuts)


EXC_FOOT = (EXC_SWING + 16.5, EXC_TRACK + 6.0 + 2.0)     # the boom foot pin (x, z), between the bracket's plates


def _band(pts, half):
    """A beam along a polyline [(x, z), ...] with half-depths ``half`` at its points, as a 2D outline."""
    outs = []
    for (a, ha), (b, hb) in zip(zip(pts[:-1], half[:-1]), zip(pts[1:], half[1:])):
        d = np.array(b) - np.array(a)
        n = np.array([-d[1], d[0]]) / np.linalg.norm(d)
        outs.append(poly([tuple(np.array(a) + n * ha), tuple(np.array(b) + n * hb), tuple(np.array(b) - n * hb), tuple(np.array(a) - n * ha)]))
        outs += [circle(a, ha, 24), circle(b, hb, 24)]
    return cs_union(outs)


def _excavator_front(side=1):
    """One half (``side`` +1 or -1) of the excavator's front, split down its centre plane so each
    half prints on its cut face: the box-section boom folded down, the arm tucked back under it,
    the bucket curled and resting on its timber, the boom, arm and bucket cylinders down the middle,
    pin bosses on the outside. Glue the halves face to face."""
    F_ = EXC_FOOT
    K, T, A = (75.0, 27.0), (104.0, 22.0), (79.0, 14.0)
    boom = _band([F_, K, T], [2.6, 4.6, 2.6])
    arm = _band([T, A], [3.2, 2.0])
    bucket = poly([(A[0] + 2.0, A[1] + 1.0), (A[0] - 3.0, A[1] + 1.5), (A[0] - 7.5, A[1] - 2.0), (A[0] - 8.5, 6.0), (A[0] - 6.5, 2.0),
                   (A[0] + 5.0, 2.0), (A[0] + 6.5, 4.0), (A[0] + 5.5, A[1] - 3.0)])
    cyl_boom = _band([(EXC_FOOT[0] + 1.0, EXC_FOOT[1] - 3.5), (62.0, 20.0)], [0.9, 0.9])
    cyl_arm = _band([(62.0, 31.0), (100.0, 27.0)], [0.8, 0.8])
    cyl_bkt = _band([(102.0, 18.5), (86.0, 15.0)], [0.75, 0.75])
    w_boom, w_arm, w_bkt, w_cyl = 3.0, 2.6, 5.8, 0.9
    parts = [along_y(boom, 0.0, w_boom), along_y(arm, 0.0, w_arm), along_y(bucket, 0.0, w_bkt),
             along_y(cyl_boom, 0.0, w_cyl), along_y(cyl_arm, 0.0, w_cyl), along_y(cyl_bkt, 0.0, w_cyl)]
    for (x, z), r, w in ((F_, 1.6, w_boom), (K, 1.8, w_boom), (T, 1.6, w_boom), (A, 1.3, w_bkt)):
        parts.append(M.cylinder(0.5, r, r, 24).rotate([-90, 0, 0]).translate([x, w - 0.01, z]))
    for k in range(3):                                               # teeth on the bucket's lip, the middle one on the centre line
        y0 = [0.0, 2.0, 4.0][k]
        parts.append(box([A[0] + 5.8, y0, 3.0], [A[0] + 7.6, y0 + 1.0, 4.4]))
    m = union(parts)
    return m if side > 0 else m.mirror([0, 1, 0])


@solid
def excavator_front(side=1):
    """An excavator front half in its print pose: on its cut face."""
    return _excavator_front(side).rotate([90 * side, 0, 0])


@solid
def excavator_block():
    """The timber the bucket rests on."""
    return box([-8.0, -4.5, 0.0], [8.0, 4.5, 1.2]) + box([-6.5, -6.0, 1.19], [6.5, 6.0, 2.0])


# ================================================================== 16. crawler dozer and its blade
DOZER_TRACK = 8.6
BLADE_SKID = 1.2


@solid
def dozer():
    """A mid-size crawler dozer shipped with its blade off (the blade rides beside it): oval tracks
    on six rollers a side, the mainframe between them with the push-arm trunnions, the long engine
    hood with its radiator guard, side louvres, exhaust stack and precleaner, the ROPS cab with its
    glass and overhung roof on a 45 degree soffit, fenders, the fuel tank and a single-shank ripper
    lowered onto a steel block. Generic."""
    zt = DOZER_TRACK
    trk = tracks(0.0, 48.0, 3.6, 3.6, zt, 11.4, 6.4, 6, 1.6, rollers=1)
    frame = _side([(6.0, 2.6), (42.0, 2.6), (46.0, 6.6), (46.0, zt + 0.01), (2.0, zt + 0.01), (2.0, 6.6)], -8.25, 8.25)
    fenders = box([0.0, -14.8, zt - 0.01], [26.0, 14.8, zt + 0.5])
    hood = M.hull_points([(x, y, zt + 0.49) for x in (24.0, 50.0) for y in (-8.8, 8.8)] + [(x, y, zt + 12.4) for x in (24.0, 49.0) for y in (-8.0, 8.0)])
    grille = box([49.0, -7.6, zt + 1.0], [50.6, 7.6, zt + 11.6])
    cab = M.hull_points([(x, y, zt + 0.49) for x in (8.0, 24.5) for y in (-9.5, 9.5)] + [(x, y, zt + 24.0) for x in (8.6, 23.6) for y in (-8.9, 8.9)])
    roof = M.hull_points([(x, y, zt + 23.4) for x in (8.4, 23.8) for y in (-9.1, 9.1)] + [(x, y, zt + 24.4) for x in (7.6, 24.6) for y in (-9.9, 9.9)] +
                         [(x, y, zt + 25.2) for x in (7.6, 24.6) for y in (-9.9, 9.9)])
    tank_ = box([0.6, -8.0, zt + 0.49], [8.2, 8.0, zt + 8.0])
    det = [M.cylinder(6.0, 0.75, 0.75, 16).translate([40.0, 4.5, zt + 12.39]),
           M.cylinder(3.5, 1.1, 1.1, 20).translate([33.0, -4.5, zt + 12.39]),
           M.cylinder(0.9, 1.1, 1.8, 20).translate([33.0, -4.5, zt + 15.88]),
           M.cylinder(0.5, 1.8, 1.8, 20).translate([33.0, -4.5, zt + 16.77])]
    for sgn in (-1, 1):                                          # push-arm trunnions on the track frames
        det.append(M.cylinder(1.8, 1.5, 1.5, 20).rotate([-90 * sgn, 0, 0]).translate([24.0, sgn * 14.0, 4.6]))
        det.append(box([46.0, sgn * 7.0 - 1.0, zt + 4.0], [49.0, sgn * 7.0 + 1.0, zt + 7.5]))     # lift cylinder brackets
    panes = []
    for x0, x1 in ((9.5, 15.6), (16.6, 22.6)):
        for sgn in (-1, 1):
            panes.append(box([x0, sgn * 9.0 - 0.6, zt + 6.0], [x1, sgn * 9.0 + 0.6, zt + 22.0]))
    for sgn in (-1, 1):
        panes.append(box([8.0 - 0.6 if sgn < 0 else 23.4, -7.6, zt + 6.0], [8.6 if sgn < 0 else 24.6, 7.6, zt + 22.0]))
    cuts = []
    for z in np.arange(zt + 2.0, zt + 11.0, 1.1):                 # radiator guard bars
        cuts.append(box([50.2, -7.0, z], [51.0, 7.0, z + 0.45]))
    for x in np.arange(27.0, 46.0, 1.2):                          # hood side louvres
        for sgn in (-1, 1):
            cuts.append(box([x, sgn * 8.6 - 0.3, zt + 3.0], [x + 0.4, sgn * 8.6 + 0.3, zt + 9.0]))
    # ripper: a beam on two 45 degree links, the shank down onto a steel block
    rip = [_side([(0.5, 2.4), (1.8, 2.4), (-4.2, 8.4), (-5.5, 8.4)], -6.0, -4.6), _side([(0.5, 2.4), (1.8, 2.4), (-4.2, 8.4), (-5.5, 8.4)], 4.6, 6.0),
           box([-7.0, -6.5, 8.2], [-4.0, 6.5, 12.0]),
           _side([(-6.2, 0.99), (-4.8, 0.99), (-4.8, 8.3), (-6.4, 8.3), (-7.4, 3.0)], -0.8, 0.8),
           box([-8.4, -2.0, 0.0], [-3.6, 2.0, 1.0]),
           _side([(0.0, zt + 2.0), (0.6, zt + 2.0), (-5.0, 11.8), (-5.6, 11.8)], -3.2, -2.2), _side([(0.0, zt + 2.0), (0.6, zt + 2.0), (-5.0, 11.8), (-5.6, 11.8)], 2.2, 3.2)]
    return union([trk, frame, fenders, hood, grille, cab, roof, tank_] + det + rip) - union(cuts + panes)


@solid
def dozer_blade():
    """The dozer's semi-U blade standing on its cutting edge on timber skids, as it ships: the
    moldboard's concave face curling forward at the top no more than 45 degrees, end bits, ribs and
    the push-arm and tilt brackets on the back, bolts along the cutting edge."""
    L = ft(11.2)
    z0 = BLADE_SKID
    sec = [(0.4, 0), (0, 0.6), (-1.6, 3), (-2.6, 6), (-3.0, 9), (-2.8, 12), (-2.0, 14), (-1.0, 15), (-4.4, 15), (-4.4, 3.2), (-1.2, 0)]
    blade = along_x(poly([(y + 2.2, z + z0) for y, z in sec]), 0.0, L)
    parts = [blade]
    for x0 in (-0.6, L):                                          # end bits, swept forward a little
        parts.append(along_x(poly([(2.8, z0), (1.6, z0 + 3.0), (-0.4, z0 + 14.6), (-2.2, z0 + 15.0), (-2.2, z0 + 3.2), (1.0, z0)]), x0, x0 + 0.6))
    for x in np.linspace(3.0, L - 3.0, 6):                        # ribs on the back
        parts.append(_side_y(x, -2.2, -3.2, z0 + 3.2, z0 + 14.6))
    for x in (L * 0.28, L * 0.72):                                # push-arm brackets and pins
        parts.append(box([x - 1.6, -4.4, z0 + 2.4], [x + 1.6, -2.19, z0 + 6.4]))
        parts.append(M.cylinder(4.0, 0.7, 0.7, 16).rotate([0, 90, 0]).translate([x - 2.0, -3.4, z0 + 4.8]))
    parts.append(box([L / 2 - 1.2, -4.0, z0 + 11.0], [L / 2 + 1.2, -2.19, z0 + 14.0]))
    for x in np.linspace(1.5, L - 1.5, 12):
        parts.append(M.cylinder(0.25, 0.3, 0.3, 10).rotate([-90, 0, 0]).translate([x, 1.45, z0 + 1.6]))
    skids = [box([x - 1.2, -3.8, 0.0], [x + 1.2, 4.2, z0 + 0.01]) for x in (2.0, L / 2, L - 2.0)]
    return F._sheeted(lambda: union(parts + skids))()


def _side_y(x, y0, y1, z0, z1, t=0.6):
    """A rib in the (y, z) plane at x: from y0 at the plate out to y1, z0 to z1, its outer edge sloped
    in at both ends."""
    return along_x(poly([(y0, z0), (y1, z0 + 1.2), (y1, z1 - 1.2), (y0, z1)]), x - t / 2, x + t / 2)


# ================================================================== 17. vintage crawler tractors
CRAWLER_TRACK = 6.6


@solid
def crawler_tractor():
    """A 1940s crawler tractor: oval tracks on five rollers, the radiator with its cast top tank and
    vertical grille, a narrow hood with the exhaust and air-cleaner stacks, the fuel tank, the open
    operator's seat with its back and steering levers, fenders over the tracks and the drawbar
    plate at the rear. Generic."""
    zt = CRAWLER_TRACK
    trk = tracks(0.0, 36.0, 2.8, 2.8, zt, 9.0, 5.8, 5, 1.8, rollers=1)
    frame = _side([(5.0, 2.4), (32.0, 2.4), (35.0, 5.4), (35.0, zt + 0.01), (1.0, zt + 0.01), (1.0, 5.4)], -6.1, 6.1)
    fenders = box([0.0, -11.9, zt - 0.01], [14.0, 11.9, zt + 0.4])
    hood = box([14.0, -4.4, zt - 0.01], [33.0, 4.4, zt + 8.5])
    rad = M.hull_points([(x, y, z) for x in (33.0, 37.4) for y in (-5.6, 5.6) for z in (zt - 0.01, zt + 9.4)] +
                        [(x, y, zt + 10.6) for x in (33.4, 37.0) for y in (-5.0, 5.0)])
    tank_ = box([9.0, -6.0, zt + 0.39], [14.5, 6.0, zt + 7.5])
    seat = [box([3.0, -4.5, zt + 0.39], [8.0, 4.5, zt + 3.4]), box([2.0, -4.5, zt + 0.39], [3.2, 4.5, zt + 8.0])]
    levers = [box([9.6, y - 0.3, zt + 3.4], [10.2, y + 0.3, zt + 10.5]) for y in (-1.8, 1.8)]
    stacks = [M.cylinder(5.5, 0.55, 0.55, 14).translate([28.0, 2.4, zt + 8.49]), M.cylinder(4.5, 1.0, 1.0, 18).translate([22.0, -2.2, zt + 8.49]),
              M.cylinder(0.6, 1.0, 1.4, 18).translate([22.0, -2.2, zt + 12.98]), M.cylinder(0.4, 1.4, 1.4, 18).translate([22.0, -2.2, zt + 13.57])]
    det = [box([-0.4, -2.0, 2.0], [1.01, 2.0, 6.0])]
    cuts = [box([37.0, y - 0.18, zt + 1.2], [38.0, y + 0.18, zt + 8.8]) for y in np.arange(-4.6, 4.7, 0.8)]
    cuts += [box([x, sgn * 4.4 - 0.3, zt + 2.0], [x + 0.35, sgn * 4.4 + 0.3, zt + 6.5]) for x in np.arange(16.0, 31.5, 1.1) for sgn in (-1, 1)]
    return union([trk, frame, fenders, hood, rad, tank_] + seat + levers + stacks + det) - union(cuts)


# ================================================================== wheels (batch 4)
def _tire(x, zc, r, ya, yb, lugs=24, hub=True, outer=1):
    """A tire on its wheel, axis along y between ya and yb, centre (x, zc): tread lugs cut across
    the crown, the wheel's disc recessed in the outer face (``outer`` +1 at yb, -1 at ya) with its
    hub and nuts."""
    t = M.cylinder(yb - ya, r, r, 48).rotate([-90, 0, 0]).translate([x, ya, zc])
    cuts = []
    for k in range(lugs):
        a = 360.0 * k / lugs
        for half in (0, 1):
            gg = box([-0.2, ya + 0.5, r - 0.35], [0.2, (ya + yb) / 2 - 0.15, r + 1]) if half == 0 else \
                 box([-0.2, (ya + yb) / 2 + 0.15, r - 0.35], [0.2, yb - 0.5, r + 1])
            gg = gg.rotate([0, a + (180.0 / lugs if half else 0.0), 0]).translate([x, 0, zc])
            cuts.append(gg)
    yo = yb if outer > 0 else ya
    rim = M.cylinder(0.5, r * 0.62, r * 0.62, 32).rotate([-90, 0, 0]).translate([x, yo - 0.4 if outer > 0 else yo - 0.1, zc])
    cuts.append(rim)
    t = t - union(cuts)
    if hub:
        add = [M.cylinder(0.6, r * 0.28, r * 0.24, 20).rotate([-90 * outer, 0, 0]).translate([x, yo - 0.45 * outer, zc])]
        for k in range(8):
            a = math.radians(45 * k)
            add.append(M.cylinder(0.25, 0.22, 0.22, 8).rotate([-90 * outer, 0, 0]).translate([x + r * 0.4 * math.cos(a), yo - 0.42 * outer, zc + r * 0.4 * math.sin(a)]))
        t = union([t] + add)
    return t


def _wheel_keel(x, zc, r, ya, yb, zplane):
    """The fill between the top of a tire and the plane above it (zplane), with its sides on the
    tire's 45 degree tangents: what a tire hangs on when its part prints upside down."""
    z45 = zc + r * S2
    d = zplane - z45
    return along_y(poly([(x - r * S2, z45), (x + r * S2, z45), (x + r * S2 - d, zplane + 0.01), (x - r * S2 + d, zplane + 0.01)]), ya + 0.4, yb - 0.4)


# ================================================================== 19. TOFC trailers
TRL_FLOOR = 13.6          # the van's floor above the ground (display)
TRL_ROOF = ft(13.5)
TRL_CHANGE = round((TRL_ROOF - TRL_FLOOR) / 0.2) * 0.2      # printed upside down: the body, then the black running gear


@solid
def trailer(seed=1):
    """A 40 ft piggyback van trailer of the 1960s, printed upside down (roof on the plate): exterior
    posts every two feet, top and bottom rails, the rear doors with hinges, lock rods and handles,
    the ICC bar, rounded front corners; the tandem with dual wheels on a slider, mud flaps, the
    landing gear down on sand shoes. Blank, ready for a road's decals."""
    L, W = ft(40.0), ft(8.0)
    zb, zr = TRL_FLOOR, TRL_ROOF
    rc = 1.5
    body = (box([0, -W / 2, zb], [L - rc, W / 2, zr]) +
            M.cylinder(zr - zb, rc, rc, 20).translate([L - rc, W / 2 - rc, zb]) + M.cylinder(zr - zb, rc, rc, 20).translate([L - rc, -W / 2 + rc, zb]) +
            box([L - rc - 0.01, -W / 2 + rc, zb], [L, W / 2 - rc, zr]))
    det = []
    for sgn in (-1, 1):
        yo = sgn * W / 2
        for x in np.arange(ft(2.0), L - 2.0, ft(2.0)):
            det.append(box([x - 0.3, yo - sgn * 0.01, zb + 1.0], [x + 0.3, yo + sgn * 0.3, zr - 1.4]))
        det.append(box([0.0, yo - sgn * 0.01, zr - 1.4], [L - rc, yo + sgn * 0.45, zr]))
        det.append(box([0.0, yo - sgn * 0.01, zb], [L - rc, yo + sgn * 0.45, zb + 1.0]))
    for sgn in (-1, 1):                                         # rear doors: hinges, lock rods, handles
        y_edge = sgn * (W / 2 - 0.8)
        for z in np.linspace(zb + 3.0, zr - 3.0, 4):
            det.append(box([-0.4, y_edge - 0.5, z - 0.6], [0.01, y_edge + 0.5, z + 0.6]))
        for yy in (sgn * 3.5, sgn * 9.0):
            det.append(box([-0.45, yy - 0.18, zb + 1.4], [0.01, yy + 0.18, zr - 1.8]))      # lock rod
            ya, yb = sorted((yy, yy + sgn * 1.6))                                         # its handle, toward the door's edge
            det.append(box([-0.7, ya - 0.2, zb + 8.0], [0.01, yb + 0.2, zb + 8.5]))
    for sgn in (-1, 1):                                         # ICC bar on two struts
        det.append(box([0.6, sgn * 9.0 - 0.5, 6.0], [1.6, sgn * 9.0 + 0.5, zb + 0.01]))
    det.append(box([0.4, -12.0, 5.0], [1.8, 12.0, 6.4]))
    cuts = [box([-1, -0.12, zb + 1.2], [0.12, 0.12, zr - 1.2])]
    # running gear: slider, springs, axles, duals, mud flaps
    rt = 5.8
    for x in (ft(4.6), ft(8.2)):
        for sgn in (-1, 1):
            ya, yb = (W / 2 - 6.4, W / 2) if sgn > 0 else (-W / 2, -W / 2 + 6.4)
            det.append(_tire(x, rt, rt, ya, yb, lugs=22, outer=sgn))
            det.append(_wheel_keel(x, rt, rt, ya, yb, zb))
        det.append(box([x - 0.6, -W / 2 + 6.0, rt - 0.6], [x + 0.6, W / 2 - 6.0, rt + 0.6]))
        for sgn in (-1, 1):
            det.append(box([x - 3.0, sgn * 7.5 - 0.6, rt + 0.5], [x + 3.0, sgn * 7.5 + 0.6, zb + 0.01]))
    for sgn in (-1, 1):
        det.append(box([ft(2.0) - 0.3, sgn * (W / 2 - 6.0), 2.0], [ft(2.0) + 0.1, sgn * W / 2 - sgn * 0.2, zb + 0.01]))
    lg = L - ft(7.0)
    for sgn in (-1, 1):                                         # landing gear on sand shoes, braced
        det.append(box([lg - 0.6, sgn * 11.0 - 0.6, 0.6], [lg + 0.6, sgn * 11.0 + 0.6, zb + 0.01]))
        det.append(box([lg - 1.4, sgn * 11.0 - 1.4, 0.0], [lg + 1.4, sgn * 11.0 + 1.4, 0.61]))
        det.append(along_x(poly([(sgn * 10.6, 7.0), (sgn * 11.2, 7.0), (sgn * 3.6, zb + 0.01), (sgn * 3.0, zb + 0.01)]), lg - 0.3, lg + 0.3))
    det.append(box([lg - 0.4, -11.0, 6.5], [lg + 0.4, 11.0, 7.3]))
    det.append(box([lg + 0.6, 11.0, 7.6], [lg + 1.6, 12.6, 8.4]))           # crank
    return flip(union([body] + det) - union(cuts))


# ================================================================== 20. ISO containers
@solid
def iso_container(L=ft(20.0)):
    """A 20 ft ISO container: corrugated sides and front recessed between the corner posts and the
    top and bottom rails, eight corner castings with their apertures, the doors with four lock rods,
    cam keepers and handles, hinges, the fork pockets, a corrugated roof."""
    W, H = ft(8.0), ft(8.5)
    env = box([0, 0, 0], [L, W, H])
    rec = 0.5
    cuts = [box([1.0, -1, 1.6], [L - 1.0, rec, H - 1.1]), box([1.0, W - rec, 1.6], [L - 1.0, W + 1, H - 1.1]),
            box([L - rec, 1.0, 1.6], [L + 1, W - 1.0, H - 1.1]), box([-1, 1.0, 1.2], [0.3, W - 1.0, H - 1.0])]
    m = env - union(cuts)
    ribs = []
    pitch = 3.2
    for x in np.arange(1.0 + pitch / 2, L - 1.0, pitch):
        for y0, y1 in ((rec, 0.08), (W - rec, W - 0.08)):
            ribs.append(M.hull_points([(x + dx, y0, z) for dx in (-0.95, 0.95) for z in (1.59, H - 1.09)] +
                                      [(x + dx, y1, z) for dx in (-0.65, 0.65) for z in (1.59, H - 1.09)]))
    for y in np.arange(1.0 + pitch / 2, W - 1.0, pitch):
        ribs.append(M.hull_points([(L - rec, y + dy, z) for dy in (-0.95, 0.95) for z in (1.59, H - 1.09)] +
                                  [(L - 0.08, y + dy, z) for dy in (-0.65, 0.65) for z in (1.59, H - 1.09)]))
    for y in np.arange(2.2, W - 1.5, 2.0):                       # door panels' vertical corrugation
        ribs.append(box([0.0, y - 0.45, 1.6], [0.32, y + 0.45, H - 1.4]))
    det = []
    for y in (W * 0.16, W * 0.36, W * 0.64, W * 0.84):           # lock rods with keepers and handles
        ya, yb = sorted((y, y + (1.4 if y < W / 2 else -1.4)))                      # handle, toward the door's middle
        det += [box([-0.5, y - 0.18, 1.0], [0.01, y + 0.18, H - 0.9]),
                box([-0.6, y - 0.45, 1.0], [0.01, y + 0.45, 1.8]), box([-0.6, y - 0.45, H - 1.7], [0.01, y + 0.45, H - 0.9]),
                box([-0.75, ya - 0.2, H * 0.45], [0.01, yb + 0.2, H * 0.45 + 0.5])]
    for y_edge in (0.6, W - 0.6):
        for z in np.linspace(3.0, H - 3.0, 4):
            det.append(box([-0.35, y_edge - 0.45, z - 0.5], [0.01, y_edge + 0.45, z + 0.5]))
    det.append(box([-0.25, W * 0.66, H * 0.62], [0.01, W * 0.8, H * 0.72]))          # CSC plate
    cast = []
    for x in (0.0, L - 1.6):
        for y in (0.0, W - 1.6):
            for z in (0.0, H - 1.3):
                c = box([x - 0.12 * (x == 0), y - 0.12 * (y == 0), z], [x + 1.6 + 0.12 * (x > 0), y + 1.6 + 0.12 * (y > 0), z + 1.3])
                ap = []
                xs_ = x + 0.8
                for yy in (y - 0.5, y + 2.1):
                    ap.append(box([xs_ - 0.35, yy - 0.3, z + 0.35], [xs_ + 0.35, yy + 0.3, z + 0.95]))
                cast.append(c - union(ap))
    roofc = [box([x - 0.15, 1.2, H - 0.2], [x + 0.15, W - 1.2, H + 1]) for x in np.arange(2.0, L - 1.5, 2.5)]
    forks = [box([L / 2 + dx - 2.0, -1, 0.35], [L / 2 + dx + 2.0, 0.45, 1.35]) for dx in (-10.0, 10.0)] + \
            [box([L / 2 + dx - 2.0, W - 0.45, 0.35], [L / 2 + dx + 2.0, W + 1, 1.35]) for dx in (-10.0, 10.0)]
    return union([m] + ribs + det + cast) - union(roofc + forks)


# ================================================================== 21. machinery crates
CRATES = [((12.0, 6.0, 6.0), "MACHINERY"), ((8.0, 5.0, 7.0), "THIS SIDE UP"), ((10.0, 4.5, 4.0), ""), ((6.0, 4.0, 5.0), ""),
          ((5.0, 5.0, 4.0), ""), ((14.0, 6.0, 5.0), "FRAGILE")]


@solid
def crate(i=0):
    """A wooden machinery crate on two skids: planked sides and top, a frame of battens round every
    face with a diagonal brace, stencilled lettering raised on the big ones."""
    from .storefront import text_cs
    (lf, wf, hf), word = CRATES[i]
    L, W, H = ft(lf), ft(wf), ft(hf)
    zs = 1.2
    body = box([0, -W / 2, zs], [L, W / 2, zs + H])
    cuts = []
    for z in np.arange(zs + 2.0, zs + H - 1.2 - 0.4, 2.0):      # plank joints round the sides, clear of the top batten
        cuts.append(box([-1, -W / 2 - 1, z - 0.1], [L + 1, -W / 2 + 0.15, z + 0.1]))
        cuts.append(box([-1, W / 2 - 0.15, z - 0.1], [L + 1, W / 2 + 1, z + 0.1]))
        cuts.append(box([-1, -W / 2 - 1, z - 0.1], [0.15, W / 2 + 1, z + 0.1]))
        cuts.append(box([L - 0.15, -W / 2 - 1, z - 0.1], [L + 1, W / 2 + 1, z + 0.1]))
    for x in np.arange(2.0, L - 0.5, 2.0):                      # top boards, a layer deep (none under a top batten)
        if min(abs(x - c) for c in (0.6, L / 2, L - 0.6)) < 1.0:
            continue
        cuts.append(box([x - 0.12, -W / 2 + 1.2, zs + H - 0.2], [x + 0.12, W / 2 - 1.2, zs + H + 1]))
    body = body - union(cuts)
    bat = []
    t, b = 0.3, 1.2
    for sgn in (-1, 1):                                         # side faces: frame, and a brace or a mid batten
        yo = sgn * W / 2
        ya, yb = sorted((yo - sgn * 0.01, yo + sgn * t))
        bat += [box([0, ya, zs], [b, yb, zs + H]), box([L - b, ya, zs], [L, yb, zs + H]),
                box([0, ya, zs], [L, yb, zs + b]), box([0, ya, zs + H - b], [L, yb, zs + H])]
        if word and sgn < 0:                                    # the stencilled face: a mid batten, the word above it
            bat.append(box([0, ya, zs + H * 0.42 - b / 2], [L, yb, zs + H * 0.42 + b / 2]))
            continue
        n = max(1, int(round(L / H)))
        seg = L / n
        for k in range(n):
            x0 = k * seg
            bat.append(along_y(poly([(x0 + b * 0.7, zs + b), (x0 + b * 1.7, zs + b), (x0 + seg - b * 0.7, zs + H - b), (x0 + seg - b * 1.7, zs + H - b)]), ya, yb))
    for xo, sgn in ((0.0, -1), (L, 1)):                         # end faces: frame and a brace
        xa, xb = sorted((xo - sgn * 0.01, xo + sgn * t))
        bat += [box([xa, -W / 2, zs], [xb, -W / 2 + b, zs + H]), box([xa, W / 2 - b, zs], [xb, W / 2, zs + H]),
                box([xa, -W / 2, zs], [xb, W / 2, zs + b]), box([xa, -W / 2, zs + H - b], [xb, W / 2, zs + H])]
        bat.append(along_x(poly([(-W / 2 + b * 0.7, zs + b), (-W / 2 + b * 1.7, zs + b), (W / 2 - b * 0.7, zs + H - b), (W / 2 - b * 1.7, zs + H - b)]), xa, xb))
    for x in (b / 2, L / 2, L - b / 2):                         # top battens
        bat.append(box([x - b / 2, -W / 2, zs + H - 0.01], [x + b / 2, W / 2, zs + H + t]))
    skids = [box([0, y - 0.9, 0.0], [L, y + 0.9, zs + 0.01]) for y in (-W / 2 + 1.4, W / 2 - 1.4)]
    out = union([body] + bat + skids)
    if word:
        cs = text_cs(word, cap=2.4, font="sans", grow=0.05)
        if cs.bounds()[2] - cs.bounds()[0] < L - 2 * b - 1.0:
            zl = zs + H * 0.42 + b / 2 + (H * 0.58 - 1.5 * b - 2.4) / 2       # centred in the panel above the mid batten
            out = out + M.extrude(cs, 0.35).rotate([90, 0, 0]).translate([L / 2, -W / 2 + 0.05, zl])
    return out


# ================================================================== 22. air-cooled chillers
CHILL_BASE = 1.6          # base rails, then the unit


@solid
def chiller():
    """A 30 ft air-cooled chiller on its base rails: the control panel end with two doors and its
    nameplate, the compressor bay behind louvres, the condenser coils down both sides between their
    frames, and twelve fans on top, each in its shroud behind a guard of rings and spokes."""
    L, W = ft(30.0), ft(7.5)
    zb = CHILL_BASE
    H = ft(8.0)
    zt = zb + H
    body = box([0, -W / 2, zb], [L, W / 2, zt])
    cuts = []
    for sgn in (-1, 1):
        yo = sgn * W / 2
        # control end doors
        cuts += [box([0.8, yo - 0.12 if sgn > 0 else yo - 1, zb + 1.0], [1.04, yo + 1 if sgn > 0 else yo + 0.12, zt - 1.0])]
        # louvres on the compressor bay
        for z in np.arange(zb + 1.5, zt - 1.2, 0.7):
            cuts.append(box([15.0, yo - 0.25 if sgn > 0 else yo - 1, z], [27.0, yo + 1 if sgn > 0 else yo + 0.25, z + 0.25]))
        # coil panels: recessed with fine vertical fins, in bays between the frame posts
        for x0 in np.arange(29.0, L - 1.0, 12.5):
            x1 = min(x0 + 11.5, L - 1.0)
            cuts.append(box([x0, yo - 0.5 if sgn > 0 else yo - 1, zb + 1.0], [x1, yo + 1 if sgn > 0 else yo + 0.5, zt - 1.6]))
    body = body - union(cuts)
    fins = []
    for sgn in (-1, 1):
        yo = sgn * W / 2
        for x0 in np.arange(29.0, L - 1.0, 12.5):
            x1 = min(x0 + 11.5, L - 1.0)
            for x in np.arange(x0 + 0.4, x1 - 0.2, 0.55):
                fins.append(box([x - 0.12, yo - 0.52 * sgn if sgn > 0 else yo + 0.1, zb + 1.0], [x + 0.12, yo - 0.1 if sgn > 0 else yo + 0.52, zt - 1.6])
                            if sgn > 0 else box([x - 0.12, yo, zb + 1.0], [x + 0.12, yo + 0.4, zt - 1.6]))
    det = []
    for x in (2.5, 7.5):                                          # door handles on the control end's face
        det.append(box([x - 0.3, -W / 2 - 0.4, zb + H * 0.5], [x + 0.3, -W / 2 + 0.01, zb + H * 0.5 + 1.4]))
    det.append(box([-0.3, -3.0, zb + H * 0.55], [0.01, 3.0, zb + H * 0.75]))         # nameplate on the end
    for k, x in enumerate(np.linspace(35.0, L - 7.0, 6)):           # fans: shroud, guard rings and spokes
        for y in (-W / 4 - 0.2, W / 4 + 0.2):
            rf = 5.6
            sh = M.cylinder(1.0, rf + 0.5, rf + 0.5, 48).translate([x, y, zt - 0.01]) - M.cylinder(3, rf, rf, 48).translate([x, y, zt - 1])
            det.append(sh)
            det.append(M.cylinder(0.6, rf, rf, 48).translate([x, y, zt - 0.01]) - M.cylinder(3, rf - 0.01, rf - 0.01, 48).translate([x, y, zt + 0.2]))
            for rr in (1.6, 3.2, 4.6):
                det.append(M.cylinder(0.4, rr + 0.2, rr + 0.2, 40).translate([x, y, zt + 0.59]) - M.cylinder(1, rr - 0.2, rr - 0.2, 40).translate([x, y, zt]))
            for a in range(0, 180, 45):
                det.append(box([-rf, -0.18, 0.0], [rf, 0.18, 0.4]).rotate([0, 0, a]).translate([x, y, zt + 0.59]))
            det.append(M.cylinder(0.6, 0.9, 0.9, 16).translate([x, y, zt + 0.59]))
    rails = [box([-0.4, y - 1.0, 0.0], [L + 0.4, y + 1.0, zb + 0.01]) for y in (-W / 2 + 1.0, W / 2 - 1.0)]
    rails += [box([x - 0.8, -W / 2 + 0.5, 0.0], [x + 0.8, W / 2 - 0.5, zb + 0.01]) for x in np.linspace(0.8, L - 0.8, 5)]
    for x in (1.0, L - 1.0):                                       # lifting lugs on the rails' ends
        for y in (-W / 2 + 1.0, W / 2 - 1.0):
            rails.append(box([x - 0.8, y - 1.2 if y < 0 else y + 0.99, 0.0], [x + 0.8, y - 0.99 if y < 0 else y + 1.2, zb + 0.01]))
    return F._sheeted(lambda: union([body] + fins + det + rails))()


# ================================================================== 23. propane tanks
PROP_DUN = 1.2            # dunnage, then the white tanks


@solid
def propane_pair():
    """Two new 1,000 gallon propane tanks side by side on dunnage: 2:1 heads, saddle legs, the valve
    dome on top with its hinged lid, a lifting lug and a nameplate. Each tank stands on a cradle web
    under its shell, pierced with gable-topped openings, so the shell needs no support."""
    r = inch(41) / 2
    Lt = ft(16.0) - r
    hd = r / 2
    z0 = PROP_DUN
    zc = z0 + 1.6 + r
    parts = []
    for yc in (-(r + 1.0), r + 1.0):
        shell = M.cylinder(Lt, r, r, 64).rotate([0, 90, 0]).translate([hd, yc, zc])
        head = M.sphere(1.0, 48).scale([hd, r, r])
        heads = [(head - box([0, -r - 1, -r - 1], [hd + 1, r + 1, r + 1])).translate([hd + 0.01, yc, zc]),
                 (head - box([-hd - 1, -r - 1, -r - 1], [0, r + 1, r + 1])).translate([hd + Lt - 0.01, yc, zc])]
        tank_ = union([shell] + heads)
        web = M.hull((tank_ ^ box([hd, yc - r, zc - r], [hd + Lt, yc + r, zc - r * S2 + 0.01])) + box([hd + 2.0, yc - 1.6, z0 - 0.01], [hd + Lt - 2.0, yc + 1.6, z0]))
        xs1, xs2 = hd + Lt * 0.2, hd + Lt * 0.8
        holes = []
        w = 6.0
        for a in np.linspace(xs1 + 3.0, xs2 - 3.0 - w, 3):
            top = z0 + 0.4
            holes.append(M.hull_points([(x, y, z) for y in (yc - r, yc + r) for (x, z) in
                                        ((a, z0 - 0.5), (a + w, z0 - 0.5), (a, top), (a + w, top), (a + w / 2, top + min(w / 2, zc - r - top - 0.9)))]))
        parts += [tank_, web - union(holes)]
        for xs in (xs1, xs2):                                    # saddle legs
            leg = box([xs - 0.6, yc - r * 0.8, z0 - 0.01], [xs + 0.6, yc + r * 0.8, zc - r * 0.5])
            parts.append(leg - M.cylinder(4, r - 0.05, r - 0.05, 64).rotate([0, 90, 0]).translate([xs - 2, yc, zc]))
            parts.append(box([xs - 1.4, yc - r * 0.8, z0 - 0.01], [xs + 1.4, yc + r * 0.8, z0 + 0.4]))
        xm = hd + Lt / 2
        parts += [M.cylinder(1.4, 2.6, 2.6, 32).translate([xm, yc, zc + r - 0.5]),
                  M.cylinder(0.5, 2.6, 2.2, 32).translate([xm, yc, zc + r + 0.89]),
                  box([xm + 2.4, yc - 0.5, zc + r + 0.7], [xm + 2.9, yc + 0.5, zc + r + 1.3])]
        lug = M.hull(box([xm - 9.0 - 1.2, yc - 0.3, zc + r - 0.6], [xm - 9.0 + 1.2, yc + 0.3, zc + r + 0.3]) +
                     M.cylinder(0.6, 0.9, 0.9, 16).rotate([90, 0, 0]).translate([xm - 9.0, yc + 0.3, zc + r + 1.0]))
        parts.append(lug - M.cylinder(2, 0.4, 0.4, 12).rotate([90, 0, 0]).translate([xm - 9.0, yc + 1.0, zc + r + 1.0]))
        out_ = 1.0 if yc > 0 else -1.0                                           # nameplate on the outboard side
        parts.append(M.hull_points([(xm + dx, yc + out_ * (r + 0.12), zc + dz) for dx in (4.0, 8.0) for dz in (-0.8, 1.2)] +
                                   [(xm + dx, yc + out_ * (r - 0.8), zc + dz) for dx in (4.0, 8.0) for dz in (-1.2, 1.2)]))
    L = Lt + 2 * hd
    dun = [box([x - 1.2, -2 * r - 2.6, 0.0], [x + 1.2, 2 * r + 2.6, z0 + 0.01]) for x in (hd + Lt * 0.2, hd + Lt * 0.5, hd + Lt * 0.8)]
    return F._sheeted(lambda: union(parts + dun))()


# ================================================================== 24. military 6x6 cargo trucks
MT_PLANE = 13.0           # chassis frame top = body bottom (display)
MT_TR = 6.3               # tire radius


def _mt_chassis_display():
    """The truck's chassis as it stands: frame rails, bumper with shackles, springs, axles with their
    differentials, six tires, the fuel tank, battery box and transfer case. Everything reaches up to
    MT_PLANE, so the part prints upside down on its frame rails."""
    zp, r = MT_PLANE, MT_TR
    parts = [box([6.0, s * 3.8 - (1.0 if s > 0 else 0.0), zp - 2.4], [79.0, s * 3.8 + (0.0 if s > 0 else 1.0), zp]) for s in (-1, 1)]
    parts.append(box([76.0, -10.5, zp - 2.6], [79.6, 10.5, zp]))                # bumper at frame height
    for sgn in (-1, 1):
        parts.append(box([79.5, sgn * 6.0 - 0.6, zp - 2.3], [80.6, sgn * 6.0 + 0.6, zp]))       # shackles
    parts.append(box([77.0, -3.5, zp - 4.6], [79.0, 3.5, zp]))                   # winch
    parts.append(box([1.0, -1.8, zp - 3.0], [6.2, 1.8, zp]))                     # pintle
    parts.append(box([1.0, -9.0, zp - 2.0], [6.5, 9.0, zp]))                     # rear crossmember, across the rails
    for x in (68.0, 28.0, 14.0):
        for sgn in (-1, 1):
            ya, yb = (sgn * 9.6, sgn * 13.6) if sgn > 0 else (-13.6, -9.6)
            parts.append(_tire(x, r, r, min(ya, yb), max(ya, yb), lugs=20, outer=sgn))
            parts.append(_wheel_keel(x, r, r, min(ya, yb), max(ya, yb), zp))
        parts.append(box([x - 0.7, -9.7, r - 0.7], [x + 0.7, 9.7, r + 0.7]))                 # axle
        parts.append(M.hull_points([(x + dx, y, z) for dx in (-1.8, 1.8) for y in (-1.6, 1.6) for z in (r - 0.4, r + 1.6)] +
                                   [(x + dx, y, r - 1.6) for dx in (-0.8, 0.8) for y in (-0.8, 0.8)]))    # differential
        for sgn in (-1, 1):                                                      # leaf springs up to the rails
            parts.append(box([x - 4.5, sgn * 3.8 - 0.5, r + 0.6], [x + 4.5, sgn * 3.8 + 0.5, zp - 2.39]))
    for sgn, (x0, x1) in ((1, (38.0, 46.0)), (-1, (36.0, 42.0))):                # fuel tank, battery box
        ya, yb = sorted((sgn * 3.6, sgn * 7.0))                                  # hung on the rail's outer face
        parts.append(box([x0, ya, zp - 6.0], [x1, yb, zp]))
    parts.append(box([44.0, -3.0, zp - 6.5], [52.0, 3.0, zp]))                   # transfer case, between the rails
    parts.append(box([20.0, -0.5, zp - 4.0], [66.0, 0.5, zp]))                   # drive line
    return union(parts)


@solid
def mt_chassis():
    """The truck's chassis in its print pose: upside down on its frame rails."""
    return flip(_mt_chassis_display())


@solid
def mt_body():
    """The truck's body, printed standing on its flat underside (it sits on the chassis' rails): the
    hood with its grille, headlights and brush guard, flat fenders, the hard cab with its windshield,
    doors and windows, the cargo bed with troop-seat sides and a canvas cover over its bows, the
    exhaust stack, tail lights."""
    parts = [box([62.0, -7.5, 0.0], [77.0, 7.5, 9.0]),                                   # hood
             box([76.6, -7.0, 0.8], [78.0, 7.0, 8.4]),                                    # grille
             box([60.0, -13.8, 0.0], [77.4, 13.8, 0.8])]                                   # fenders
    for sgn in (-1, 1):
        parts.append(box([75.4, sgn * 10.6 - 1.3, 0.79], [77.4, sgn * 10.6 + 1.3, 2.6]))   # headlights
        parts.append(box([77.6, sgn * 5.0 - 0.3, 0.79], [78.4, sgn * 5.0 + 0.3, 8.0]))     # brush guard bars
    parts.append(box([77.6, -5.3, 7.4], [78.4, 5.3, 8.0]))
    cab = M.hull_points([(x, y, 0.0) for x in (49.0, 62.0) for y in (-12.0, 12.0)] + [(x, y, 15.4) for x in (49.0, 61.0) for y in (-12.0, 12.0)])
    roof = M.hull_points([(x, y, 15.3) for x in (49.0, 61.0) for y in (-12.0, 12.0)] + [(x, y, 15.8) for x in (48.6, 61.6) for y in (-12.4, 12.4)] +
                         [(x, y, 16.4) for x in (48.6, 61.6) for y in (-12.4, 12.4)])
    parts += [cab, roof]
    bed = box([0.0, -13.8, 0.0], [48.0, 13.8, 6.5]) + box([47.9, -8.0, 0.0], [49.1, 8.0, 1.0])      # with the spacer to the cab
    canvas_cs = cs_union([poly([(-13.6, 6.4), (13.6, 6.4), (13.6, 16.0), (-13.6, 16.0)]),
                          CS.circle(1.0, 48).scale((13.6, 3.0)).translate((0.0, 16.0))]) ^ CS.square((40, 30)).translate((-20.0, 6.4))
    canvas = along_x(canvas_cs, 0.3, 47.6)
    parts += [bed, canvas]
    for x in np.arange(4.0, 46.0, 8.5):                                                    # bows
        parts.append(along_x(offset(canvas_cs, 0.25) - offset(canvas_cs, -0.05), x - 0.3, x + 0.3))
    for x in np.arange(2.0, 47.0, 3.0):                                                    # rope tie-downs
        for sgn in (-1, 1):
            parts.append(box([x - 0.25, sgn * 13.8 - 0.3, 6.6], [x + 0.25, sgn * 13.8 + 0.3, 7.4]))
    parts.append(M.cylinder(11.0, 0.55, 0.55, 14).translate([60.5, 12.6, 0.0]))            # exhaust stack
    for sgn in (-1, 1):
        parts.append(box([-0.4, sgn * 11.5 - 0.8, 2.0], [0.01, sgn * 11.5 + 0.8, 3.4]))     # tail lights
    cuts = []
    for sgn in (-1, 1):                                                                    # windshield, door outline, door window
        cuts.append(box([60.4, sgn * 6.0 - 5.0, 9.4], [62.5, sgn * 6.0 + 5.0, 14.6]))
        yo = sgn * 12.0
        cuts.append(box([50.5, yo - 0.12 - (1 if sgn < 0 else 0), 1.0], [50.74, yo + 0.12 + (1 if sgn > 0 else 0), 14.8]))
        cuts.append(box([50.9, yo - 0.4 - (1 if sgn < 0 else 0), 9.0], [58.6, yo + 0.4 + (1 if sgn > 0 else 0), 14.4]))
    for z in np.arange(1.4, 8.0, 0.9):                                                    # grille bars
        cuts.append(box([77.6, -6.5, z], [78.1, 6.5, z + 0.4]))
    cuts += [box([-1, -12.5, 7.8], [0.25, 12.5, 15.0])]                                     # the rear flap's edge
    return union(parts) - union(cuts)


# ================================================================== 25. precast box culverts
CULV_DUN = 1.2


@solid
def box_culvert():
    """An 8 x 6 ft precast box culvert section, 6 ft long, on two timbers: 8 in walls with 45 degree
    haunches in the corners (they also keep the roof's span short), the tongue at one end and the
    groove's lip at the other, four lifting inserts on top, its size stencilled on a side."""
    from .storefront import text_cs
    t = inch(8)
    Wi, Hi = ft(8.0), ft(6.0)
    W, H = Wi + 2 * t, Hi + 2 * t
    L = ft(6.0)
    z0 = CULV_DUN
    h = t
    inner = poly([(-Wi / 2 + h, z0 + t), (Wi / 2 - h, z0 + t), (Wi / 2, z0 + t + h), (Wi / 2, z0 + t + Hi - h), (Wi / 2 - h, z0 + t + Hi),
                  (-Wi / 2 + h, z0 + t + Hi), (-Wi / 2, z0 + t + Hi - h), (-Wi / 2, z0 + t + h)])
    outer = poly([(-W / 2, z0), (W / 2, z0), (W / 2, z0 + H), (-W / 2, z0 + H)])
    body = along_x(outer - inner, 0.0, L)
    tongue = along_x(offset(inner, t / 2) - inner, L - 0.01, L + 1.0)
    lip = along_x(outer - offset(inner, t / 2), -1.0, 0.01)
    cuts = [M.cylinder(1.0, 0.45, 0.45, 12).translate([x, y, z0 + H - 0.5]) for x in (L * 0.25, L * 0.75) for y in (-W / 4, W / 4)]
    lab = M.extrude(text_cs("8X6", cap=2.6, font="sans", grow=0.05), 0.35).rotate([90, 0, 0]).translate([L / 2, -W / 2 + 0.05, z0 + H * 0.55])
    dun = [box([x - 1.0, -W / 2 - 0.8, 0.0], [x + 1.0, W / 2 + 0.8, z0 + 0.01]) for x in (2.6, L - 2.6)]
    return F._sheeted(lambda: union([body, tongue, lip, lab] + dun) - union(cuts))()


# ================================================================== 26. reinforced concrete pipe
RCP_DUN = 1.2


@solid
def rcp_row(n=3):
    """Three 48 in reinforced concrete pipes, 8 ft lengths, lying side by side across the car with
    their bells at alternate ends, on two dunnage strips under the ends. Each bore is round at both
    faces and 45 degree pointed behind them; keels hidden under the barrels and bells carry them."""
    ro, ri, rb = inch(29), inch(24), inch(34)
    L, Lb = ft(8.0), inch(6.5)
    z0 = RCP_DUN
    zc = z0 + 0.3 + rb
    parts, cuts = [], []
    pitch = 2 * rb + 0.8
    for k in range(n):
        x = k * pitch
        sgn = 1 if k % 2 == 0 else -1                          # which end the bell is at
        y0, y1 = -L / 2, L / 2
        barrel = M.cylinder(L, ro, ro, 64).rotate([-90, 0, 0]).translate([x, y0, zc])
        yb0 = y1 - Lb if sgn > 0 else y0
        bell = M.cylinder(Lb, rb, rb, 64).rotate([-90, 0, 0]).translate([x, yb0, zc])
        taper = M.cylinder(1.4, ro, rb, 64).rotate([-90, 0, 0]).translate([x, yb0 - 1.4, zc]) if sgn > 0 else \
                M.cylinder(1.4, rb, ro, 64).rotate([-90, 0, 0]).translate([x, y0 + Lb, zc])
        parts += [barrel, bell, taper]
        ya, yb = (y0 + 0.4, yb0 - 1.4 - 0.4) if sgn > 0 else (y0 + Lb + 1.4 + 0.4, y1 - 0.4)
        parts.append(along_y(keel(x, zc, ro, z0), ya, yb))
        yba, ybb = (yb0 + 0.4, y1 - 0.4) if sgn > 0 else (y0 + 0.4, y0 + Lb - 0.4)
        parts.append(along_y(keel(x, zc, rb, z0), yba, ybb))
        cuts.append(M.cylinder(L + 2, ri, ri, 64).rotate([-90, 0, 0]).translate([x, y0 - 1, zc]))
        tear = poly([(x - ri * S2, zc + ri * S2 - 0.3), (x + ri * S2, zc + ri * S2 - 0.3), (x + ri * S2, zc + ri * S2), (x, zc + ri * math.sqrt(2)),
                     (x - ri * S2, zc + ri * S2)])
        cuts.append(along_y(tear, y0 + 0.6, y1 - 0.6))
        for yy in (-L / 4, L / 4):                               # lifting holes
            cuts.append(M.cylinder(3.0, 0.5, 0.5, 12).translate([x, yy, zc + ri - 0.5]))
    Lx = (n - 1) * pitch
    dun = [box([-rb - 0.6, y - 1.0, 0.0], [Lx + rb + 0.6, y + 1.0, z0 + 0.01]) for y in (-L / 2 + 1.6, L / 2 - 1.6)]
    return F._sheeted(lambda: union(parts + dun) - union(cuts))()


# ================================================================== 27. jersey barriers
@solid
def jersey_barrier():
    """A 12 ft New Jersey concrete median barrier to the standard profile (3 in upright, 55 degree
    face to 13 in, 84 degree face to the 6 in top, 32 in tall), with its pin-and-loop connectors at
    both ends, two scuppers through the base and a lifting hole through the top."""
    pts = [(12, 0), (12, 3), (5, 13), (3, 32), (-3, 32), (-5, 13), (-12, 3), (-12, 0)]
    L = ft(12.0)
    body = along_x(poly([(inch(y), inch(z)) for y, z in pts]), 0.0, L)
    det = []
    for x0, x1 in ((-0.6, 0.01), (L - 0.01, L + 0.6)):
        for z in (inch(6), inch(22)):
            det.append(box([x0, -0.6, z], [x1, 0.6, z + 1.0]))
    cuts = [box([x - 1.6, -5, -1], [x + 1.6, 5, 1.0]) for x in (L * 0.3, L * 0.7)]
    cuts.append(M.cylinder(4, 0.55, 0.55, 12).rotate([90, 0, 0]).translate([L / 2, 2, inch(26)]))
    return union([body] + det) - union(cuts)


# ================================================================== 28. precast manhole sections
MH_PAL = 1.2              # the pallet, then the concrete
MH_RI, MH_RO = inch(24), inch(29)


def _pallet(r):
    """A square pallet under a round section: three stringers and top boards, to MH_PAL."""
    s = r + 1.2
    parts = [box([-s, y - 0.7, 0.0], [s, y + 0.7, MH_PAL - 0.39]) for y in (-s + 0.7, 0.0, s - 0.7)]
    for x in np.linspace(-s + 0.9, s - 0.9, 7):
        parts.append(box([x - 0.9, -s, MH_PAL - 0.4], [x + 0.9, s, MH_PAL + 0.01]))
    return union(parts)


@solid
def manhole(kind="riser", h_ft=3.0):
    """A precast manhole section on its pallet: ``kind`` riser (a ring with its joint's tongue on
    top), base (closed floor, two pipe knockouts) or cone (eccentric, 4 ft, to a 24 in opening),
    with lifting holes and the steps' stubs inside."""
    z0 = MH_PAL
    ri, ro = MH_RI, MH_RO
    if kind == "cone":
        H = ft(4.0)
        top_ro, top_ri = inch(17), inch(12)
        off = ro - top_ro
        outer = M.hull(M.cylinder(0.01, ro, ro, 64).translate([0, 0, z0]) + M.cylinder(0.01, top_ro, top_ro, 48).translate([off, 0, z0 + H - 0.01]))
        inner = M.hull(M.cylinder(0.01, ri, ri, 64).translate([0, 0, z0 - 0.5]) + M.cylinder(0.01, top_ri, top_ri, 48).translate([off, 0, z0 + H + 0.5]))
        body = outer - inner
        body = body + (M.cylinder(0.6, top_ro - 1.0, top_ro - 1.0, 48) - M.cylinder(2, top_ri, top_ri, 48).translate([0, 0, -0.5])).translate([off, 0, z0 + H - 0.01])
    else:
        H = ft(h_ft)
        body = M.cylinder(H, ro, ro, 64).translate([0, 0, z0]) - M.cylinder(H + 2, ri, ri, 64).translate([0, 0, z0 - 1])
        body = body + (M.cylinder(0.6, ro - 1.0, ro - 1.0, 64) - M.cylinder(2, ri, ri, 64).translate([0, 0, -0.5])).translate([0, 0, z0 + H - 0.01])
        if kind == "base":
            body = body + M.cylinder(ft(0.67), ri + 0.01, ri + 0.01, 64).translate([0, 0, z0])
            for a in (0, 150):
                kn = M.cylinder(0.4, 3.2, 3.2, 32).rotate([0, 90, 0]).translate([ro - 0.39, 0, z0 + H * 0.45]).rotate([0, 0, a])
                body = body - kn
    for a in (90, 270):                                           # lifting holes through the wall
        body = body - M.cylinder(4, 0.5, 0.5, 12).rotate([0, 90, 0]).translate([ri - 1, 0, z0 + H * 0.7]).rotate([0, 0, a])
    stubs = [box([ri - 0.5, y - 0.25, z0 + z], [ri + 0.05, y + 0.25, z0 + z + 0.5])         # on the vertical side (the cone's too)
             for z in np.arange(2.5, H - 1.5, 3.5) for y in (-1.15, 1.15)]
    return F._sheeted(lambda: union([body, _pallet(ro)] + stubs))()


# ================================================================== 29. precast double tees
DT_DEPTH = 7.6            # printed upside down: the tee to its stems' feet, then the dunnage


@solid
def double_tee():
    """A 40 ft precast prestressed double tee for a parking deck, printed flange down: an 8 ft
    flange with weld plates along its edges, two tapered stems with bearing plates at their ends,
    and the dunnage under the stems (printed on top, in its colour)."""
    W, L = ft(8.0), ft(40.0)
    tf = 1.2
    D = DT_DEPTH
    flange = box([0, -W / 2, D - tf], [L, W / 2, D])
    stems = []
    for yc in (-ft(2.0), ft(2.0)):
        bw, tw = inch(5.75) / 2, inch(7.75) / 2
        stems.append(along_x(poly([(yc - bw, 0.0), (yc + bw, 0.0), (yc + tw, D - tf + 0.01), (yc - tw, D - tf + 0.01)]), 0.0, L))
        for x0 in (0.0, L - 1.6):
            stems.append(box([x0, yc - bw - 0.15, 0.0], [x0 + 1.6, yc + bw + 0.15, 0.25]))      # bearing plates
    cuts = []
    for x in np.arange(ft(5.0), L - 2.0, ft(5.0)):                                          # weld plates in the edges
        for sgn in (-1, 1):
            cuts.append(box([x - 0.8, sgn * W / 2 - 0.2, D - tf + 0.3], [x + 0.8, sgn * W / 2 + 0.2, D - 0.3]))
    dun = [box([x - 1.2, -W / 2 + 1.5, -1.2], [x + 1.2, W / 2 - 1.5, 0.01]) for x in (3.0, L / 2, L - 3.0)]
    return flip(union([flange] + stems + dun) - union(cuts))


# ================================================================== 30. rebar bundles
REBAR_DUN = 1.2


@solid
def rebar_lift(n=7, seed=5):
    """A lift of rebar for a flatcar: seven 40 ft bundles side by side on dunnage, each a rounded
    stack of bars with every bar's line showing down its length, the ends ragged with bars of a
    little different length, wire ties every 8 ft."""
    rng = np.random.default_rng(seed)
    L = ft(40.0)
    z0 = REBAR_DUN
    bw, bh = 4.2, 3.0
    parts, cuts = [], []
    for k in range(n):
        yc = (k - (n - 1) / 2) * (bw + 0.15)
        sec = cs_union([CS.square((bw, bh * 0.55)).translate((yc - bw / 2, z0)),
                        CS.circle(1.0, 32).scale((bw / 2, bh * 0.45)).translate((yc, z0 + bh * 0.55))]) ^ CS.square((bw, bh + 1)).translate((yc - bw / 2, z0))
        x0, x1 = rng.uniform(-0.4, 0.4), L + rng.uniform(-0.4, 0.4)
        parts.append(along_x(sec, x0, x1))
        for j in range(5):                                       # bars sticking out of the ragged ends, inside the bundle's section
            yy = yc + rng.uniform(-bw / 2 + 0.6, bw / 2 - 0.6)
            ztop = z0 + bh * 0.55 + bh * 0.45 * math.sqrt(max(0.0, 1 - ((yy - yc) / (bw / 2)) ** 2)) - 0.35
            zz = z0 + rng.uniform(0.4, ztop - z0)
            for xe, sgn in ((x0, -1), (x1, 1)):
                e = rng.uniform(0.2, 1.0)
                parts.append(box([min(xe - sgn * 0.3, xe + sgn * e), yy - 0.2, zz - 0.2], [max(xe - sgn * 0.3, xe + sgn * e), yy + 0.2, zz + 0.2]))
        for yy in np.arange(yc - bw / 2 + 0.5, yc + bw / 2 - 0.3, 0.55):     # bar lines along the top
            top = z0 + bh * 0.55 + bh * 0.45 * math.sqrt(max(0.0, 1 - ((yy - yc) / (bw / 2)) ** 2))
            cuts.append(box([x0 + 0.5, yy - 0.08, top - 0.2], [x1 - 0.5, yy + 0.08, top + 1]))
        for x in np.arange(ft(4.0), L - 2.0, ft(8.0)):                        # wire ties
            ring = (offset(sec, 0.2) - offset(sec, -0.05)) ^ CS.square((bw + 2, bh + 2)).translate((yc - bw / 2 - 1, z0 + 0.3))
            parts.append(along_x(ring, x - 0.25, x + 0.25))
    W = n * (bw + 0.15)
    dun = [box([x - 1.0, -W / 2 - 0.8, 0.0], [x + 1.0, W / 2 + 0.8, z0 + 0.01]) for x in np.linspace(2.0, L - 2.0, 6)]
    return F._sheeted(lambda: union(parts + dun) - union(cuts))()


# ================================================================== 31. steel sheet piling
SP_DUN = 1.2


@solid
def sheet_pile_tier(n=3, layers=8, seed=2):
    """Three bundles of 40 ft steel Z-pile, nested eight deep, side by side on dunnage: the trapezoid
    wave of each bundle (52 degree webs; the flanges' undersides bridge between them), every pile's
    end a little proud or short of its neighbours so the nesting shows, two bands round each."""
    rng = np.random.default_rng(seed)
    L = ft(40.0)
    z0 = SP_DUN
    P, fl, run, dep, t = 10.5, 2.5, 2.75, 3.5, 0.5
    parts = []
    for b in range(n):
        y0 = (b - (n - 1) / 2) * (P + 0.8) - P / 2
        wave = [(y0, 0.0), (y0 + fl, 0.0), (y0 + fl + run, dep), (y0 + 2 * fl + run, dep), (y0 + P, 0.0)]
        for k in range(layers):
            zk = z0 + k * t
            top = [(y, z + zk + t) for y, z in wave]
            bot = [(y, z + zk) for y, z in wave][::-1]
            sec = poly(top + bot)
            parts.append(along_x(sec, rng.uniform(-0.3, 0.1), L + rng.uniform(-0.1, 0.3)))
        zt = z0 + layers * t
        for x in (L * 0.2, L * 0.8):                                      # bands over the top flanges and down the sides
            parts.append(box([x - 0.3, y0 - 0.25, z0], [x + 0.3, y0 + 0.01, zt + 0.25]))
            parts.append(box([x - 0.3, y0 + P - 0.01, z0], [x + 0.3, y0 + P + 0.25, zt + 0.25]))
            parts.append(box([x - 0.3, y0 - 0.25, zt + dep - 0.01], [x + 0.3, y0 + P + 0.25, zt + dep + 0.25]))
            parts.append(box([x - 0.3, y0 - 0.25, zt - 0.01], [x + 0.3, y0 + fl, zt + dep + 0.25]))
            parts.append(box([x - 0.3, y0 + P - fl, zt - 0.01], [x + 0.3, y0 + P + 0.25, zt + dep + 0.25]))
    W = n * (P + 0.8)
    dun = [box([x - 1.0, -W / 2 - 0.6, 0.0], [x + 1.0, W / 2 + 0.6, z0 + 0.01]) for x in np.linspace(2.0, L - 2.0, 6)]
    return F._sheeted(lambda: union(parts + dun))()


# ================================================================== 32. utility poles
POLE_BUNK = 1.6


@solid
def pole_pile(seed=4):
    """Treated wood utility poles, 45 ft, piled eight, seven, six and five on six bunks with stakes,
    their butts at alternate ends: each pole tapered from a 12 in butt to a 7 in top, the top cut
    to a roof, a brand plate near the butt, a wire-rope wrapper over the end bunks. Keels and valley
    webs hidden in the pile carry the round poles."""
    rng = np.random.default_rng(seed)
    L = ft(45.0)
    b = POLE_BUNK
    rm = inch(9.5) / 2
    rows = [8, 7, 6, 5]
    parts, keels, hull_cs = [], [], []
    centres = []
    for j, n in enumerate(rows):
        for i in range(n):
            y = (i - (n - 1) / 2) * 2 * rm
            z = b + rm + j * rm * math.sqrt(3)
            centres.append((y, z, j))
    for k, (y, z, j) in enumerate(centres):
        butt_left = (k % 2 == 0)
        rb, rt = inch(12) / 2, inch(7) / 2
        ra, rz = (rb, rt) if butt_left else (rt, rb)
        x0, x1 = rng.uniform(-0.8, 0.2), L + rng.uniform(-0.2, 0.8)
        pole = M.hull_points([(x0, y + ra * math.cos(t), z + ra * math.sin(t) - (rm - ra) * 0) for t in np.linspace(0, 2 * math.pi, 24, endpoint=False)] +
                             [(x1, y + rz * math.cos(t), z + rz * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 24, endpoint=False)])
        xt = x1 if butt_left else x0                                       # roof cut on the top end
        sgn = 1 if butt_left else -1
        roof = box([-3, -3, 0], [3, 3, 6]).rotate([0, -30 * sgn, 0]).translate([xt + sgn * 0.2, y, z + 0.4])
        pole = pole - roof
        xb = x0 + 6.0 if butt_left else x1 - 6.0
        plate = box([xb - 0.5, y - 0.4, z + ra * 0.9 - 0.2 if butt_left else z + rz * 0.9 - 0.2], [xb + 0.5, y + 0.4, z + (ra if butt_left else rz) + 0.15])
        parts += [pole, plate]
        hull_cs.append(circle((y, z), rm, 24))
        rk = min(ra, rz) * 0.97
        if j == 0:
            keels.append(along_x(keel(y, z, rk, b), x0 + 0.4, x1 - 0.4))
        else:
            keels.append(along_x(poly([(y - S2 * rk, z - S2 * rk), (y + S2 * rk, z - S2 * rk), (y, z - rm * math.sqrt(3))]), x0 + 0.4, x1 - 0.4))
    ext = rows[0] * rm + 0.1
    hull = cs_union(hull_cs).hull()
    wrap_cs = (offset(hull, 0.75) - offset(hull, -0.1)) ^ CS.square((60.0, 60.0)).translate((-30.0, b - 0.01))
    bunks, stakes, wraps = [], [], []
    for xb in np.linspace(1.6, L - 1.6, 6):
        bunks.append(box([xb - 1.4, -ext - 2.4, 0.0], [xb + 1.4, ext + 2.4, b]))
        for sgn in (-1, 1):
            y0 = sgn * (ext - 0.15)
            stakes.append(box([xb - 0.2, min(y0, y0 + sgn * 1.4), b - 0.01], [xb + 1.2, max(y0, y0 + sgn * 1.4), b + 9.5]))
        if xb < 3 or xb > L - 3:
            wraps.append(along_x(wrap_cs, xb - 1.3, xb - 0.7))
    return F._sheeted(lambda: union(parts + keels + bunks + stakes + wraps))()


# ================================================================== 33. crushed car scrap
CAR_SLAB = ft(1.5)
CRUSH_CHANGE = 3 * 1.6    # three crushed cars in the bottom colour, the rest in the top colour


@solid
def crushed_stack(seed=1, n=6):
    """A stack of six cars flattened at the scrapyard, as they ride to the shredder: each body
    crumpled into a slab, its roof pillars folded down with the window openings still showing,
    wheel wells, bumpers, hood and trunk seams, each car a little askew on the one below."""
    rng = np.random.default_rng(seed)
    parts = []
    z = 0.0
    h = 1.6
    for k in range(n):
        L, W = ft(rng.uniform(14.0, 16.5)), ft(rng.uniform(5.6, 6.2))
        dx, dy, a = rng.uniform(-0.6, 0.6), rng.uniform(-0.5, 0.5), rng.uniform(-2.5, 2.5)
        pts = []
        for sx in (-1, 1):
            for sy in (-1, 1):
                pts += [(sx * L / 2 + rng.uniform(-0.6, 0.0) * sx, sy * W / 2 + rng.uniform(-0.4, 0.0) * sy, z),
                        (sx * (L / 2 - rng.uniform(0.6, 1.6)), sy * (W / 2 - rng.uniform(0.2, 0.6)), z + h)]
        slab = M.hull_points(pts)
        cuts = []
        for sx in (-1, 1):                                                 # wheel wells, gable-topped
            for sy in (-1, 1):
                xw = sx * L * 0.3
                cuts.append(M.hull_points([(xw + ddx, sy * W / 2 + ddy, zz) for ddx in (-2.0, 2.0) for ddy in (-1.0, 1.0) for zz in (z - 0.1, z + 0.5)] +
                                          [(xw, sy * W / 2 + ddy, z + 1.1) for ddy in (-1.0, 1.0)]))
        for sy in (-1, 1):                                                 # window openings of the folded greenhouse
            for xc in (-L * 0.08, L * 0.1):
                cuts.append(box([xc - 1.6, sy * W / 2 - 1.2, z + 0.6], [xc + 1.6, sy * W / 2 + 1.2, z + 1.15]))
        for xs in (-L * 0.28, L * 0.25) if k == n - 1 else ():            # hood and trunk seams (the top car's; the rest are covered)
            cuts.append(box([xs - 0.1, -W / 2 + 1.5, z + h - 0.2], [xs + 0.1, W / 2 - 1.5, z + h + 1]))
        for _ in range(3 if k == n - 1 else 0):                            # dents
            cuts.append(box([-6, -6, 0], [6, 6, 3]).rotate([rng.uniform(-6, 6), rng.uniform(-6, 6), 0]).translate(
                [rng.uniform(-L / 3, L / 3), rng.uniform(-W / 3, W / 3), z + h - rng.uniform(0.1, 0.35)]))
        slab = slab - union(cuts)
        bumpers = [box([L / 2 - 2.0, -W / 2 + 0.6, z + 0.3], [L / 2 + 0.3, W / 2 - 0.6, z + 0.9]),          # front, 0.3 proud
                   box([-L / 2 - 0.3, -W / 2 + 0.6, z + 0.3], [-L / 2 + 2.0, W / 2 - 0.6, z + 0.9])]       # rear
        parts.append(union([slab] + bumpers).rotate([0, 0, a]).translate([dx, dy, 0]))
        z += h
    return union(parts)


# ================================================================== 34. giant old-growth log
GLOG_SILL = 4.8           # sills and the bed between them, then the log


@solid
def giant_log():
    """One log of an old-growth fir, 9 ft through and 32 ft long, the way they were photographed on
    a single flatcar: deep bark furrows, two springboard notches near the butt, the saw cut on both
    ends with its rings and checks, two binder chains over it, riding on two timber sills with a
    chock at each end. The log's underside is buried in the bed between the sills, out of sight."""
    rng = np.random.default_rng(9)
    L = ft(32.0)
    r0, r1 = ft(9.0) / 2, ft(8.2) / 2
    zc = 0.6 + r0
    log = M.hull_points([(0.0, r0 * math.cos(t), zc + r0 * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 96, endpoint=False)] +
                        [(L, r1 * math.cos(t), zc - (r0 - r1) + r1 * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 96, endpoint=False)])
    cuts = []
    for _ in range(46):                                                    # bark furrows
        th = math.radians(rng.uniform(-30.0, 210.0))
        xa = rng.uniform(-1.0, L * 0.4)
        xb = rng.uniform(xa + L * 0.35, L + 1.0)
        g = CS.square((2.2, rng.uniform(0.5, 0.8)), True).translate((r0 + 0.45, 0.0)).rotate(math.degrees(th))
        cuts.append(along_x(g.translate((0.0, zc)), xa, xb))
    for xe, re in ((0.0, r0), (L, r1)):                                    # rings and checks on the cut ends
        zce = zc if xe == 0.0 else zc - (r0 - r1)
        rings = [circle((0.0, zce), re * f + 0.12, 64) - circle((0.0, zce), re * f - 0.12, 64) for f in np.linspace(0.12, 0.9, 11)]
        checks = [CS.square((re * 0.7, 0.3)).rotate(a).translate((0.0, zce)) for a in (25, 160, 250)]
        cs = cs_union(rings + checks)
        cuts.append(along_x(cs, -0.4, 0.3) if xe == 0.0 else along_x(cs, L - 0.3, L + 0.4))
    for sgn in (-1, 1):                                                    # springboard notches, their tops at 45 degrees
        xn = 9.0 + (3.0 if sgn > 0 else 0.0)
        yo = sgn * (r0 + 1.0)
        cuts.append(along_x(poly([(yo, zc + 1.0), (sgn * (r0 - 2.2), zc + 1.0), (sgn * (r0 - 2.2), zc + 2.0), (yo, zc + 2.0 + abs(yo - sgn * (r0 - 2.2)))]), xn, xn + 3.0))
    log = log - union(cuts)
    ys = r0 * 0.68
    sills = [box([-1.0, sgn * ys - 1.5, 0.0], [L + 1.0, sgn * ys + 1.5, GLOG_SILL / 2]) for sgn in (-1, 1)]          # two timbers each
    sills += [box([-0.6, sgn * ys - 1.5, GLOG_SILL / 2 - 0.01], [L + 0.6, sgn * ys + 1.5, GLOG_SILL]) for sgn in (-1, 1)]
    bed = box([0.6, -ys + 1.5, 0.0], [L - 0.6, ys - 1.5, GLOG_SILL])
    chocks = [along_y(poly([(xe, 0.0), (xe + sgn * 3.2, 0.0), (xe, GLOG_SILL)]), -ys + 1.5, ys - 1.5) for xe, sgn in ((0.6, -1), (L - 0.6, 1))]
    chains = []
    for x in (L * 0.22, L * 0.78):                                         # each over the log's section where it lies
        f = x / L
        hull = circle((0.0, zc - (r0 - r1) * f), r0 - (r0 - r1) * f, 96)
        band = (offset(hull, 0.45) - offset(hull, -0.8)) ^ CS.square((80, 80)).translate((-40.0, GLOG_SILL - 0.01))
        band = band ^ CS.square((2 * ys + 3.0, 80)).translate((-ys - 1.5, 0.0))
        chains.append(along_x(band, x - 0.35, x + 0.35))
    return F._sheeted(lambda: union([log] + sills + [bed] + chocks + chains))()


# ================================================================== 35. pulpwood
PULP_H_CHANGE = round((ft(9.0) - 2.4) / 0.2) * 0.2     # the cut ends below, the top course's bark above


@solid
def pulpwood_rack(seed=3):
    """A section of 8 ft pulpwood sticks piled crosswise between the racks of a pulpwood car, 9 ft
    high: both sides a mosaic of cut ends, each its own size and standing a little proud or short,
    with its bark ring; the top course in bark. Cut ends below PULP_H_CHANGE, bark above."""
    rng = np.random.default_rng(seed)
    L, W, H = 40.0, ft(8.0), ft(9.0)
    zc = PULP_H_CHANGE
    core = box([0, -W / 2 + 0.6, 0.0], [L, W / 2 - 0.6, zc])
    ends = []
    pts = []
    tries = 0
    while tries < 4000:                                                    # random packing of end circles on the side face
        tries += 1
        r = rng.uniform(0.85, 1.7)
        x, z = rng.uniform(r, L - r), rng.uniform(r, zc - r * 0.3)
        if all(math.hypot(x - px, z - pz) > r + pr + 0.05 for px, pz, pr in pts):
            pts.append((x, z, r))
    for x, z, r in pts:
        for sgn in (-1, 1):
            e = rng.uniform(0.0, 0.7)
            y0 = sgn * (W / 2 - 0.6)
            ya, yb = sorted((y0 - sgn * 0.3, y0 + sgn * (0.6 + e)))
            stick = M.cylinder(yb - ya, r, r, 20).rotate([-90, 0, 0]).translate([x, ya, z])
            ye = yb if sgn > 0 else ya                                       # the cut end: a groove just inside the bark
            groove = M.cylinder(0.4, r - 0.2, r - 0.2, 20) - M.cylinder(1, r - 0.45, r - 0.45, 20).translate([0, 0, -0.3])
            groove = groove.rotate([-90, 0, 0]).translate([x, ye - 0.2, z])
            if z - r < 0.0:
                stick = stick ^ box([-100, -100, 0.0], [100, 100, 100])
            ends.append(stick - groove)
    top = []
    x = 1.2
    while x < L - 1.0:                                                     # the top course, in bark
        r = rng.uniform(1.0, 1.6)
        top.append(M.cylinder(W, r, r, 20).rotate([-90, 0, 0]).translate([x, -W / 2 + rng.uniform(-0.3, 0.3), zc - 0.3]) ^ box([-100, -100, zc - 0.01], [100, 100, 100]))
        x += 2 * r - 0.2
    face = []
    for xs in (0.0, L):                                                    # the sticks' sides on the section's faces
        for zz in np.arange(1.0, zc - 0.5, 1.9):
            sg = -1 if xs == 0.0 else 1
            face.append(along_y(poly([(xs, zz - 0.8), (xs + sg * 0.5, zz), (xs, zz + 0.8)]), -W / 2 + 0.6, W / 2 - 0.6))
    return union([core] + ends + top + face)


# ================================================================== 36. pony truss bridge steel
TRUSS_L = ft(50.0)
TRUSS_H = ft(8.0)


@solid
def truss_side():
    """One side of a 50 ft riveted Warren pony truss, printed flat: top chord laced on its face,
    bottom chord, inclined end posts, diagonals and verticals, gusset plates with rivet rows at every
    joint, the bearing shoes. It stands on edge on the car (and on your bridge piers)."""
    L, H = TRUSS_L, TRUSS_H
    n = 5
    pw = L / n
    t = 1.6
    m = []

    def bar(a, b, w):
        return along_z_cs(F._seg(a, b, w), 0.0, t)
    m.append(bar((pw * 0.5, H - 1.0), (L - pw * 0.5, H - 1.0), 2.0))           # top chord
    m.append(bar((0.0, 0.9), (L, 0.9), 1.8))                                   # bottom chord
    m.append(bar((0.0, 0.9), (pw * 0.5, H - 1.0), 2.0))                        # end posts
    m.append(bar((L, 0.9), (L - pw * 0.5, H - 1.0), 2.0))
    for k in range(n):                                                      # Warren diagonals and a vertical in each panel
        x0, xm = k * pw, k * pw + pw * 0.5
        m.append(bar((xm, H - 1.0), (x0 + pw, 0.9), 1.2))
        if k > 0:                                                           # (the first panel's is the end post)
            m.append(bar((xm, H - 1.0), (x0, 0.9), 1.2))
        m.append(bar((xm, H - 1.0), (xm, 0.9), 0.9))
    gus = []
    for k in range(n + 1):
        gus.append(box([k * pw - 1.8, 0.0, t - 0.01], [k * pw + 1.8, 3.0, t + 0.25]))
    for k in range(n):
        gus.append(box([k * pw + pw * 0.5 - 1.8, H - 3.2, t - 0.01], [k * pw + pw * 0.5 + 1.8, H, t + 0.25]))
    lace = []
    for x in np.arange(pw * 0.5 + 1.0, L - pw * 0.5 - 1.0, 1.6):
        lace.append(along_z_cs(F._seg((x, H - 1.8), (x + 1.4, H - 0.2), 0.45), t - 0.01, t + 0.2))
    shoes = [box([x - 2.0, 0.0, 0.0], [x + 2.0, 0.5, t + 0.6]) for x in (1.0, L - 1.0)]
    return union(m + gus + lace + shoes)


def along_z_cs(cs, z0, z1):
    return M.extrude(cs, z1 - z0).translate([0, 0, z0])


@solid
def floor_beam_bundle(n=6):
    """The span's floor beams, six 16 ft I-beams with their end connection angles, two layers of
    three on dunnage (brown to 1.2 mm, the steel above)."""
    Lb = ft(16.0)
    d, bf, tf, tw = inch(30), inch(10), 0.6, 0.6
    parts = []
    for j in range(2):                                                      # the top layer sits on the bottom one's flanges
        for i in range(n // 2):
            y = (i - (n // 2 - 1) / 2) * (bf + 0.6)
            z0 = 1.2 + j * (d - 0.01)
            parts += [box([0, y - bf / 2, z0], [Lb, y + bf / 2, z0 + tf]),
                      box([0, y - tw / 2, z0 + tf - 0.01], [Lb, y + tw / 2, z0 + d - tf + 0.01]),
                      box([0, y - bf / 2, z0 + d - tf], [Lb, y + bf / 2, z0 + d])]
            for xe in (0.6, Lb - 0.6):
                parts.append(box([xe - 0.6, y - 1.6, z0 + tf], [xe + 0.6, y + 1.6, z0 + d - tf]))
    W = (n // 2) * (bf + 0.6)
    for x in (2.0, Lb / 2, Lb - 2.0):                                       # dunnage under the bottom layer
        parts.append(box([x - 1.0, -W / 2, 0.0], [x + 1.0, W / 2, 1.21]))
    return F._sheeted(lambda: union(parts))()


@solid
def truss_blocking():
    """A timber the two truss sides stand on, notched for their bottom chords, with a spacer block
    between them."""
    Lb = ft(9.0)
    blk = box([-1.6, -Lb / 2, 0.0], [1.6, Lb / 2, 2.4])
    for y in (-8.0, 8.0):
        blk = blk - box([-2, y - 1.0, 1.6], [2, y + 1.0, 3])
    return blk


# ================================================================== round loads on a cradle web (batch 7)
def _cradle(body, x0, x1, zc, r, z0, yw, holes=3):
    """The vessel-style cradle under a lying round body (axis along x at height zc, radius r): the
    hull of the body's underside down to a strip on the skid at z0, pierced with gable-topped
    openings whose apexes stay a mm under the body. Carries the body at 45 degrees."""
    under = body ^ box([x0, -r - 2, zc - r - 1], [x1, r + 2, zc - r * S2 + 0.01])
    web = M.hull(under + box([x0 + 1.0, -yw, z0 - 0.01], [x1 - 1.0, yw, z0]))
    span = x1 - x0 - 8.0
    wmax = 2 * ((zc - r - z0) - 1.6)
    if wmax < 1.5 or holes == 0:
        return web
    w = min(wmax, (span - (holes - 1) * 4.0) / holes)
    start = x0 + 4.0 + (span - (holes * w + (holes - 1) * 4.0)) / 2
    cut = []
    for k in range(holes):
        a = start + k * (w + 4.0)
        top = z0 + 0.6
        cut.append(M.hull_points([(x, y, z) for y in (-r - 5, r + 5) for (x, z) in
                                  ((a, z0 - 0.5), (a + w, z0 - 0.5), (a, top), (a + w, top), (a + w / 2, top + w / 2))]))
    return web - union(cut)


def _skid_frame(x0, x1, yw, z0):
    """A steel skid under a cradle: two beams, cross members."""
    parts = [box([x0, y - 1.0, 0.0], [x1, y + 1.0, z0]) for y in (-yw + 1.0, yw - 1.0)]
    parts += [box([x - 1.2, -yw, 0.0], [x + 1.2, yw, z0]) for x in np.linspace(x0 + 1.2, x1 - 1.2, 4)]
    return union(parts)


# ================================================================== 37. generator rotor
ROTOR_SKID = 2.0
ROTOR_R = ft(4.0) / 2
ROTOR_ZC = ROTOR_SKID + 4.0 + ft(4.4) / 2
ROTOR_CHANGE = math.floor((ROTOR_ZC - ft(4.4) / 2 - 0.5) / 0.2) * 0.2


@solid
def generator_rotor():
    """A turbine-generator's rotor on its shipping skid: the forged body with its winding slots
    and two unslotted pole faces, a retaining ring and fan at each end, the journals, the coupling
    flange with its bolt circle and the collector rings; the cradle under the body and saddles
    under the journals."""
    r, rr = ROTOR_R, ft(4.4) / 2
    zc, z0 = ROTOR_ZC, ROTOR_SKID
    Lb = ft(20.0)
    x0 = 14.0
    ax = lambda m: m.rotate([0, 90, 0])
    parts = [ax(M.cylinder(Lb, r, r, 72)).translate([x0, 0, zc])]
    slots = []
    for k in range(28):
        a = 360.0 * k / 28
        if min(abs((a % 180) - 0), abs((a % 180) - 180)) < 20:            # the pole faces
            continue
        slots.append(box([x0 + 0.6, -0.28, r - 0.45], [x0 + Lb - 0.6, 0.28, r + 1]).rotate([a, 0, 0]).translate([0, 0, zc]))
    parts[0] = parts[0] - union(slots)
    for xe, sgn in ((x0, -1), (x0 + Lb, 1)):
        xa = xe if sgn > 0 else xe - 5.5
        parts.append(ax(M.cylinder(5.5, rr, rr, 72)).translate([xa, 0, zc]))                  # retaining ring
        xf = xe + 5.5 if sgn > 0 else xe - 7.5
        fan = ax(M.cylinder(2.0, r - 0.6, r - 0.6, 60)).translate([xf, 0, zc])
        fan = fan - union([box([xf - 1, -0.15, r - 1.6], [xf + 3, 0.15, r]).rotate([10.0 * k, 0, 0]).translate([0, 0, zc]) for k in range(36)])
        parts.append(fan)
    rj = 2.8
    parts += [ax(M.cylinder(14.0, rj, rj, 40)).translate([x0 - 14.0, 0, zc]), ax(M.cylinder(14.0, rj, rj, 40)).translate([x0 + Lb, 0, zc])]
    fl = ax(M.cylinder(1.4, 4.6, 4.6, 48)).translate([x0 - 14.0, 0, zc])
    fl = fl - union([ax(M.cylinder(3, 0.35, 0.35, 10)).translate([x0 - 15.0, 3.6 * math.cos(math.radians(a)), zc + 3.6 * math.sin(math.radians(a))]) for a in range(0, 360, 30)])
    parts.append(fl)
    for xr in (x0 + Lb + 6.0, x0 + Lb + 8.5):                                                # collector rings
        parts.append(ax(M.cylinder(1.4, rj + 0.7, rj + 0.7, 40)).translate([xr, 0, zc]))
    body = union(parts)
    web = _cradle(body, x0 - 5.5, x0 + Lb + 5.5, zc, rr, z0, 9.0)
    sad = []
    for xs in (x0 - 9.0, x0 + Lb + 11.5):                                                    # journal saddles
        sad.append(along_x(keel(0.0, zc, rj, z0), xs - 1.2, xs + 1.2))
    skid = _skid_frame(x0 - 13.0, x0 + Lb + 13.0, 9.5, z0)
    return F._sheeted(lambda: union([body, web, skid] + sad))()


# ================================================================== 38. generator stator
STATOR_SKID = 2.0
STATOR_R = ft(12.0) / 2
STATOR_ZC = STATOR_SKID + 3.6 + STATOR_R
STATOR_CHANGE = math.floor((STATOR_ZC - STATOR_R - 0.5) / 0.2) * 0.2


@solid
def generator_stator():
    """A generator stator, 12 ft through and 28 ft long, the kind that rides a depressed-centre car
    as a dimensional load: the welded frame with its ring stiffeners and longitudinal bars, bolted
    end covers, the terminal box on top with six bushings, four lifting trunnions, the nameplate,
    on its cradle and skid."""
    r = STATOR_R
    zc, z0 = STATOR_ZC, STATOR_SKID
    L = ft(28.0)
    ax = lambda m: m.rotate([0, 90, 0])
    shell = ax(M.cylinder(L, r, r, 96)).translate([0, 0, zc])
    parts = [shell]
    for x in np.linspace(3.0, L - 3.0, 7):
        parts.append(ax(M.cylinder(1.0, r + 0.6, r + 0.6, 96)).translate([x - 0.5, 0, zc]))
    for a in range(0, 360, 30):
        parts.append(box([3.0, -0.4, r - 0.2], [L - 3.0, 0.4, r + 0.45]).rotate([a, 0, 0]).translate([0, 0, zc]))
    for xe, sgn in ((0.0, -1), (L, 1)):                                                      # end covers and bolt circles
        cov = ax(M.cylinder(1.2, r - 1.2, r - 1.2, 96)).translate([xe if sgn > 0 else xe - 1.2, 0, zc])
        bolts = [ax(M.cylinder(0.4, 0.35, 0.35, 10)).translate([(xe + 1.19) if sgn > 0 else xe - 1.59, (r - 2.2) * math.cos(math.radians(a)), zc + (r - 2.2) * math.sin(math.radians(a))])
                 for a in range(0, 360, 12)]
        parts += [cov] + bolts
    tb = box([L * 0.35, -6.0, zc + r - 1.0], [L * 0.65, 6.0, zc + r + 4.0])
    parts.append(tb)
    for i in range(6):
        xb = L * 0.38 + i * L * 0.048
        parts += [M.cylinder(3.5, 0.9, 0.7, 16).translate([xb, 0.0, zc + r + 3.99]),
                  M.cylinder(0.5, 1.2, 1.2, 16).translate([xb, 0.0, zc + r + 3.99])]
    for x in (L * 0.18, L * 0.82):                                                           # trunnions
        for sgn in (-1, 1):
            yb = sgn * (r * math.cos(math.radians(30)))
            boss = M.hull_points([(x + dx, yb, zc + r * 0.5 + dz) for dx in (-2.0, 2.0) for dz in (-2.0, 2.0)] +
                                 [(x + dx, yb + sgn * 2.0, zc + r * 0.5 + dz) for dx in (-1.4, 1.4) for dz in (0.0, 1.6)])
            parts.append(boss)
    parts.append(M.hull_points([(L * 0.55 + dx, -r - 0.2, zc + dz) for dx in (0, 6.0) for dz in (-1.5, 2.0)] +
                               [(L * 0.55 + dx, -r + 1.0, zc + dz) for dx in (0, 6.0) for dz in (-2.0, 2.0)]))
    body = union(parts)
    web = _cradle(body, 2.0, L - 2.0, zc, r + 0.6, z0, 14.0)
    skid = _skid_frame(0.0, L, 14.5, z0)
    return F._sheeted(lambda: union([body, web, skid]))()


# ================================================================== 39. heat exchanger tube bundle
TB_SKID = 1.6
TB_R = ft(4.0) / 2
TB_ZC = TB_SKID + 3.4 + TB_R + 1.0
TB_CHANGE = math.floor((TB_ZC - TB_R - 1.0 - 0.5) / 0.2) * 0.2


@solid
def tube_bundle():
    """A shell-and-tube heat exchanger's tube bundle, out of its shell: the stationary tubesheet with
    its bolt ring, tube-end pattern and lifting lugs, every tube's line along the bundle, segmental
    baffles every 2 ft with their cuts alternating, the floating head with its domed cover, on a
    cradle and skid."""
    r = TB_R
    zc, z0 = TB_ZC, TB_SKID
    L = ft(20.0)
    ax = lambda m: m.rotate([0, 90, 0])
    tubes = ax(M.cylinder(L, r, r, 72)).translate([0, 0, zc])
    tubes = tubes - union([box([0.5, -0.12, r - 0.3], [L - 0.5, 0.12, r + 1]).rotate([6.0 * k, 0, 0]).translate([0, 0, zc]) for k in range(60)])
    parts = [tubes]
    for i, x in enumerate(np.arange(ft(2.0), L - 2.0, ft(2.0))):                           # baffles, cut top and bottom by turns
        bf = ax(M.cylinder(0.5, r + 1.0, r + 1.0, 72)).translate([x - 0.25, 0, zc])
        cut = box([x - 1, -r - 2, zc + r * 0.55], [x + 1, r + 2, zc + r + 2]) if i % 2 == 0 else box([x - 1, -r - 2, zc - r - 2], [x + 1, r + 2, zc - r * 0.55])
        parts.append(bf - cut)
    ts = ax(M.cylinder(1.6, r + 1.8, r + 1.8, 72)).translate([-1.6, 0, zc])
    holes = [ax(M.cylinder(0.5, 0.4, 0.4, 10)).translate([-1.7, (r + 1.2) * math.cos(math.radians(a)), zc + (r + 1.2) * math.sin(math.radians(a))]) for a in range(0, 360, 15)]
    dimples = [ax(M.cylinder(0.4, 0.28, 0.28, 8)).translate([-1.7, y, zc + z]) for y in np.arange(-r + 0.8, r - 0.6, 1.0)
               for z in np.arange(-r + 0.8, r - 0.6, 1.0) if math.hypot(y, z) < r - 0.7]
    parts.append(ts - union(holes + dimples))
    for sgn in (-1, 1):
        lug = M.hull(box([-1.6, sgn * 2.5 - 0.3, zc + r + 1.0], [-0.0, sgn * 2.5 + 0.3, zc + r + 1.8]) +
                     M.cylinder(0.6, 0.9, 0.9, 16).rotate([90, 0, 0]).translate([-0.8, sgn * 2.5 + 0.3, zc + r + 2.6]))
        parts.append(lug - M.cylinder(2, 0.4, 0.4, 12).rotate([90, 0, 0]).translate([-0.8, sgn * 2.5 + 1.0, zc + r + 2.6]))
    fh = ax(M.cylinder(1.2, r + 0.6, r + 0.6, 72)).translate([L, 0, zc])
    dome = (M.sphere(1.0, 48).scale([r * 0.45, r + 0.2, r + 0.2]) ^ box([0, -r - 1, -r - 1], [r, r + 1, r + 1])).translate([L + 1.19, 0, zc])
    parts += [fh, dome]
    body = union(parts)
    web = _cradle(body, 2.0, L - 2.0, zc, r + 1.0, z0, 8.0)
    skid = _skid_frame(-2.0, L + 3.0, 8.5, z0)
    return F._sheeted(lambda: union([body, web, skid]))()


# ================================================================== 40. distillation column
COL_SKID = 1.6
COL_R = ft(8.0) / 2
COL_ZC = COL_SKID + 3.6 + COL_R
COL_CHANGE = math.floor((COL_ZC - COL_R - 0.5) / 0.2) * 0.2


@solid
def column():
    """A refinery distillation column, 56 ft, shipped lying: the shell with its girth seams, a 2:1
    top head, the skirt with its access opening and base ring, nozzles and manways along it, the
    ladder clipped along the top and rings of platform brackets, on three cradles."""
    r = COL_R
    zc, z0 = COL_ZC, COL_SKID
    Ls = 175.0
    xk = 22.0                                                               # the skirt's length
    ax = lambda m: m.rotate([0, 90, 0])
    hd = r / 2
    shell = ax(M.cylinder(Ls, r, r, 96)).translate([xk, 0, zc])
    head = (M.sphere(1.0, 64).scale([hd, r, r]) - box([-hd - 1, -r - 1, -r - 1], [0, r + 1, r + 1])).translate([xk + Ls - 0.01, 0, zc])
    skirt = ax(M.cylinder(xk + 0.01, r, r, 96)).translate([0, 0, zc]) - ax(M.cylinder(xk + 1, r - 0.6, r - 0.6, 96)).translate([-1, 0, zc])
    skirt = skirt - box([4.0, -3.0, zc + r - 3.0], [12.0, 3.0, zc + r + 1])                 # access opening (on top)
    base_ring = ax(M.cylinder(1.2, r + 1.2, r + 1.2, 96)).translate([0, 0, zc])
    parts = [shell, head, skirt, base_ring]
    for x in np.linspace(xk + 25.0, xk + Ls - 20.0, 5):                                       # girth seams on the upper half
        ring = ax(M.cylinder(0.5, r + 0.15, r + 0.15, 96)).translate([x - 0.25, 0, zc])
        parts.append(ring ^ box([x - 1, -r - 1, zc - r * 0.6], [x + 1, r + 1, zc + r + 1]))
    for x, rn, hn, a in ((xk + 20.0, 1.6, 3.0, 0), (xk + 60.0, 3.4, 2.6, 40), (xk + 95.0, 1.4, 3.0, -35), (xk + 130.0, 3.4, 2.6, 40),
                         (xk + 160.0, 1.8, 3.0, 0)):
        nz = union([M.cylinder(hn + 0.6, rn, rn, 32), M.cylinder(0.6, rn + 0.9, rn + 0.9, 32).translate([0, 0, hn + 0.6])]).translate([0, 0, r - 0.6])
        parts.append(nz.rotate([a, 0, 0]).translate([x, 0, zc]))
    rails = []
    for sgn in (-1, 1):                                                                       # the ladder along the top
        y = sgn * 1.4
        rails.append(box([xk + 4.0, y - 0.25, zc + r + 0.8], [xk + Ls - 6.0, y + 0.25, zc + r + 1.3]))
    for x in np.arange(xk + 8.0, xk + Ls - 8.0, 12.0):
        rails.append(box([x - 0.3, -1.65, zc + r - 0.3], [x + 0.3, 1.65, zc + r + 0.81]))      # clips
    for x in np.arange(xk + 5.0, xk + Ls - 6.0, 1.0):
        rails.append(box([x - 0.12, -1.4, zc + r + 0.85], [x + 0.12, 1.4, zc + r + 1.2]))      # rungs
    for x in (xk + 45.0, xk + 110.0):                                                         # platform bracket rings
        for a in (-60, -30, 30, 60):
            g = along_y(poly([(x - 0.4, r - 0.2), (x + 0.4, r - 0.2), (x + 0.4, r + 2.4), (x - 0.4, r + 2.4)]), -0.3, 0.3)
            parts.append(g.rotate([a, 0, 0]).translate([0, 0, zc]))
    body = union(parts + rails)
    webs = [_cradle(body, xa, xa + 22.0, zc, r, z0, 12.0, holes=1) for xa in (6.0, 85.0, 160.0)]
    skid = [_skid_frame(xa - 2.0, xa + 24.0, 12.5, z0) for xa in (6.0, 85.0, 160.0)]
    return F._sheeted(lambda: union([body] + webs + skid))()


# ================================================================== 41. girth gear
GEAR_SKID = 1.2


@solid
def girth_gear_half(teeth=70):
    """Half of a 20 ft girth gear for a kiln or a grinding mill, lying face down on two timbers: the
    toothed rim, the web with radial ribs, the inner flange that bolts to the shell, and the split
    flanges at its ends with their bolt heads."""
    Ro, Ri = ft(20.0) / 2, ft(20.0) / 2 - 4.0
    z0 = GEAR_SKID
    H = 9.0
    rf_o, rf_i = 26.0, 23.5
    keep = box([-Ro - 2, 0.0, -1], [Ro + 2, Ro + 2, H + 2])                 # the half on the +y side
    rim = M.cylinder(H, Ri + 3.0, Ri + 3.0, 180) - M.cylinder(H + 2, Ri, Ri, 180).translate([0, 0, -1])
    web = M.cylinder(2.0, Ri + 0.01, Ri + 0.01, 180).translate([0, 0, H * 0.4]) - M.cylinder(4, rf_o - 0.01, rf_o - 0.01, 180).translate([0, 0, -1])
    flange = M.cylinder(H, rf_o, rf_o, 180) - M.cylinder(H + 2, rf_i, rf_i, 180).translate([0, 0, -1])
    tooth = M.hull_points([(Ri + 2.9, y, z) for y in (-0.5, 0.5) for z in (0.0, H)] + [(Ro, y, z) for y in (-0.25, 0.25) for z in (0.0, H)])
    teeth_ = [tooth.rotate([0, 0, 180.0 * (k + 0.5) / teeth]) for k in range(teeth)]
    ribs = [box([rf_o - 0.1, -0.4, 0.0], [Ri + 0.1, 0.4, H]).rotate([0, 0, a]) for a in np.linspace(9, 171, 10)]
    ends = []
    for sgn in (-1, 1):                                                     # split flanges and their bolt heads
        xa, xb = sorted((sgn * rf_i, sgn * (Ri + 3.0)))
        ends.append(box([xa, 0.0, 0.0], [xb, 2.2, H]))
        for xbolt in np.linspace(rf_i + 1.0, Ri + 2.0, 5):
            for zb in (H * 0.25, H * 0.75):
                ends.append(M.cylinder(0.4, 0.5, 0.5, 10).rotate([90, 0, 0]).translate([sgn * xbolt, 0.01, zb]))
    gear = (union([rim, web, flange] + teeth_ + ribs + ends) ^ keep).translate([0, 0, z0])
    timbers = [box([-Ro + 4.0, y - 1.2, 0.0], [Ro - 4.0, y + 1.2, z0 + 0.01]) for y in (3.0, Ri - 2.0)]
    return F._sheeted(lambda: union([gear] + timbers))()


# ================================================================== 42. enclosed genset
GENSET_BASE = 1.6


@solid
def genset():
    """A 40 ft enclosed diesel generator set: the sound-attenuated housing with four pairs of doors a
    side (handles, louvres in their lower panels), the radiator end's louvre wall, two vertical
    silencers with rain caps and the radiator's discharge hood on the roof, corner castings, on its
    fuel-tank base."""
    L, W, H = ft(40.0), ft(8.0), ft(9.5)
    zb = GENSET_BASE
    zt = zb + H
    body = box([0, -W / 2, zb], [L, W / 2, zt])
    cuts = []
    for sgn in (-1, 1):
        yo = sgn * W / 2
        for k in range(4):
            x0 = 20.0 + k * 26.0
            for xd in (x0, x0 + 12.0):                                      # door outlines
                cuts += [box([xd - 0.12, yo - 0.15 if sgn > 0 else yo - 1, zb + 1.0], [xd + 0.12, yo + 1 if sgn > 0 else yo + 0.15, zt - 1.2])]
            cuts += [box([x0, yo - 0.15 if sgn > 0 else yo - 1, zt - 1.32], [x0 + 24.0, yo + 1 if sgn > 0 else yo + 0.15, zt - 1.08])]
            for z in np.arange(zb + 1.6, zb + 9.0, 0.7):                    # louvres in the lower panels
                cuts.append(box([x0 + 2.0, yo - 0.25 if sgn > 0 else yo - 1, z], [x0 + 22.0, yo + 1 if sgn > 0 else yo + 0.25, z + 0.25]))
    for z in np.arange(zb + 1.5, zt - 1.5, 0.8):                           # radiator louvre wall at x = L
        cuts.append(box([L - 0.3, -W / 2 + 1.5, z], [L + 1, W / 2 - 1.5, z + 0.3]))
    body = body - union(cuts)
    det = []
    for sgn in (-1, 1):
        yo = sgn * W / 2
        for k in range(4):
            for xh in (20.0 + k * 26.0 + 11.0, 20.0 + k * 26.0 + 13.0):
                ya, yb = sorted((yo - sgn * 0.01, yo + sgn * 0.35))
                det.append(box([xh - 0.25, ya, zb + 13.0], [xh + 0.25, yb, zb + 15.0]))
    for x in (30.0, 48.0):                                                  # silencers with rain caps
        det += [M.cylinder(6.0, 2.2, 2.2, 32).translate([x, 0.0, zt - 0.01]),
                M.cylinder(1.4, 2.2, 3.2, 32).translate([x, 0.0, zt + 5.99]),
                M.cylinder(0.6, 3.2, 3.2, 32).translate([x, 0.0, zt + 7.38])]
    det.append(M.hull_points([(x, y, zt - 0.01) for x in (L - 30.0, L - 2.0) for y in (-W / 2 + 1.5, W / 2 - 1.5)] +
                             [(x, y, zt + 4.0) for x in (L - 28.0, L - 6.0) for y in (-W / 2 + 2.5, W / 2 - 2.5)]))
    for x in (0.0, L - 1.6):
        for y in (-W / 2, W / 2 - 1.6):
            det.append(box([x, y, zt - 1.3], [x + 1.6, y + 1.6, zt + 0.01]))
            det.append(box([x, y, zb], [x + 1.6, y + 1.6, zb + 1.3]))
    base = [box([-0.4, -W / 2 - 0.2, 0.0], [L + 0.4, W / 2 + 0.2, zb + 0.01])]
    return union([body] + det + base)


# ================================================================== scenes (renders only)
def _place(s, m, base, change, x, z, y=0.0, upside=False, rz=0.0):
    """Set a piece (in its print pose) on the car: split at its colour change, turned over if it
    prints upside down, turned ``rz`` degrees, centred on (x, y), its bottom at z."""
    if change:
        hi, lo = m.split_by_plane((0.0, 0.0, 1.0), change[0] + 1e-3)
        bits = [(base, lo), (change[1], hi)]
    else:
        bits = [(base, m)]
    if upside:
        bits = [(c, p.rotate([180, 0, 0])) for c, p in bits]
    if rz:
        bits = [(c, p.rotate([0, 0, rz])) for c, p in bits]
    bb = np.array([p.bounding_box() for _, p in bits if not p.is_empty()])
    lo, hi = bb[:, :3].min(0), bb[:, 3:].max(0)
    move = [x - (lo[0] + hi[0]) / 2, y - (lo[1] + hi[1]) / 2, z - lo[2]]
    for c, p in bits:
        F._put(s, c, p.translate(move))
    return hi[2] - lo[2]


def scene_girders():
    L = ft(89.3)
    s = F._car(L, "car_oxide", kind="fishbelly", W=ft(9.8))
    zd = F.deck()
    g = girder()
    x0 = (L - GIRDER_L) / 2
    hb = girder_bolster().bounding_box()[5]
    for xb in (x0 + ft(3.0), x0 + GIRDER_L - ft(3.0)):
        _place(s, girder_bolster(), "Cocoa Brown", None, xb, zd)
    for y in (-GIRDER_Y, GIRDER_Y):
        F._put(s, "Light Gray", g.translate([x0, y, zd + BOLSTER_T + 0.8]))
    return s


def _lumber_scene(kind):
    L = ft(53.5)
    s = F._car(L, "car_mineral" if kind == "lumber" else "car_black", bulkhead=ft(9.0))
    zd = F.deck()
    rng = np.random.default_rng(5)
    sizes = list(BOARDS)
    tier = BUNDLE_H + STICKER
    for i, xc in enumerate(np.linspace(1.6 + LUMBER_L / 2 + 2.0, L - 1.6 - LUMBER_L / 2 - 2.0, 3)):
        for t in range(3):
            for j, y in enumerate((-7.6, 7.6)):
                if kind == "lumber":
                    m = lumber_bundle(sizes[int(rng.integers(0, 4))], seed=int(rng.integers(1 << 20)))
                    col = "Desert Tan"
                else:
                    m = wrapped_bundle()
                    col = "White"
                _place(s, m, col, (BUNDLE_H, "Cocoa Brown"), xc + rng.uniform(-0.6, 0.6), zd + t * tier, y, upside=True,
                       rz=180.0 * int(rng.integers(0, 2)))
    return s


def scene_tires():
    L = ft(53.5)
    s = F._car(L, "car_oxide")
    zd = F.deck()
    m = otr_tire()
    for x in np.linspace(L / 2 - 50.0, L / 2 + 50.0, 3):
        for y in (-8.1, 8.1):
            _place(s, m, "Sunflower Yellow", (TIRE_FRAME, "Black"), x, zd, y)
    return s


def scene_logs():
    L = ft(40.0)
    s = F._car(L, "car_black")
    zd = F.deck()
    for x, seed in ((L / 2 - LOG_L / 2 - 3.0, 3), (L / 2 + LOG_L / 2 + 3.0, 8)):
        _place(s, log_stack(seed), "Black Walnut", (LOG_BUNK, "Dark Brown"), x, zd, rz=180.0 if seed == 8 else 0.0)
    return s


def scene_panels():
    L = ft(89.3)
    s = F._car(L, "ttx_yellow", kind="fishbelly", W=ft(9.8))
    zd = F.deck()
    step = PANEL_TIE + 0.2 + RAIL_H
    for k, x in enumerate((L / 2 - PANEL_L / 2 - 3.0, L / 2 + PANEL_L / 2 + 3.0)):
        for t in range(3):
            _place(s, track_panel(seed=10 * k + t), "Black Walnut", (PANEL_TIE, "Iron Gray Metallic"), x, zd + t * step)
    return s


def scene_concties():
    L = ft(53.5)
    s = F._car(L, "car_black", bulkhead=ft(9.0))
    zd = F.deck()
    n = 15
    for x in np.linspace(1.6 + n * CTIE_PITCH / 2 + 2.0, L - 1.6 - n * CTIE_PITCH / 2 - 2.0, 3):
        for y in (-8.7, 8.7):
            _place(s, tie_dunnage(), "Black Walnut", None, x, zd, y)
        for t in range(5):
            _place(s, concrete_tie_layer(), "Light Gray", (CTIE_SEAT, "Black Walnut"), x, zd + 1.2 + t * (CTIE_SEAT + 1.2))
    return s


def scene_woodties():
    L = ft(53.5)
    s = F._car(L, "car_mineral", bulkhead=ft(9.0))
    zd = F.deck()
    h = WTIE_DUN + 5 * inch(7) + 0.2
    for k, x in enumerate(np.linspace(1.6 + 30.0, L - 1.6 - 30.0, 3)):
        for t in range(2):
            _place(s, wood_tie_row(seed=7 * k + t), "Caramel", (WTIE_DUN, "Black Walnut"), x, zd + t * (h - 0.2))
    return s


def scene_granite():
    L = ft(50.0)
    s = F._car(L, "car_oxide")
    zd = F.deck()
    xs = np.linspace(26.0, L - 26.0, 4)
    for i, x in enumerate(xs):
        _place(s, granite_block(i), "Cocoa Brown", (STONE_BLOCK, GRANITE_COLOURS[i]), x, zd, rz=90.0)
    return s


def scene_bricks():
    L = ft(40.0)
    s = F._car(L, "car_mineral")
    zd = F.deck()
    cols = ["Red", "Caramel", "Cocoa Brown"]
    k = 0
    for x in np.linspace(9.0, L - 9.0, 9):
        for y in (-7.4, 7.4):
            for t in range(2):
                _place(s, brick_cube(seed=k), cols[(k // 2) % 3], None, x, zd + t * (16 * 0.6 + 0.2), y, rz=90.0)
                k += 1
    return s


def scene_ingotmolds():
    L = ft(40.0)
    s = F._car(L, "car_black")
    zd = F.deck()
    for x in np.linspace(22.0, L - 22.0, 4):
        _place(s, ingot_mold(), "Iron Gray Metallic", (MOLD_STOOL, "Copper Brown Metallic"), x, zd, rz=90.0)
    return s


def scene_cablereels():
    L = ft(53.5)
    s = F._car(L, "car_oxide")
    zd = F.deck()
    R = REEL_R
    fl, bar, ch = reel_flange(), reel_barrel(), reel_chock()
    lag = reel_barrel(lagged=True)
    for i, x in enumerate(np.linspace(L / 2 - 2 * R - 6.0, L / 2 + 2 * R + 6.0, 3)):
        zc = zd + R
        w = REEL_W - 2 * REEL_FL
        b = lag if i == 1 else bar
        F._put(s, "Caramel" if i == 1 else "Black", b.translate([0, 0, -w / 2]).rotate([90, 0, 0]).translate([x, 0, zc]))
        for sgn in (-1, 1):
            F._put(s, "Cobalt Blue", fl.translate([0, 0, 0]).rotate([90 * -sgn, 0, 0]).translate([x, sgn * w / 2, zc]))
            for d in (-1, 1):
                c = ch if d > 0 else ch.rotate([0, 0, 180])
                F._put(s, "Cocoa Brown", c.translate([x + d * REEL_CHOCK_D, sgn * (w / 2 + 1.0), zd]))
    return s


def scene_tank():
    L = ft(53.5)
    s = F._car(L, "car_black")
    zd = F.deck()
    t = tank()
    x0 = L / 2 - 30.0
    _place(s, t, "Iron Gray Metallic", (TANK_TRACK, "Bronze"), x0 + 37.6, zd)
    b = tank_barrel()
    bb = t.bounding_box()
    xm = x0 + 37.6 - (bb[0] + bb[3]) / 2 + 44.0 - 18.0             # the mantlet's face, where the peg goes in
    F._put(s, "Bronze", b.translate([0, 0, -0.84]).rotate([0, 0, 180]).translate([xm + 3.0, 0, zd + TANK_GUN_Z]))
    return s


def scene_apc():
    L = ft(53.5)
    s = F._car(L, "car_oxide")
    zd = F.deck()
    for x in (L / 2 - 32.0, L / 2 + 32.0):
        _place(s, apc(), "Iron Gray Metallic", (APC_TRACK, "Bronze"), x, zd)
    return s


def scene_excavator():
    L = ft(53.5)
    s = F._car(L, "car_black")
    zd = F.deck()
    x0 = 30.0
    m = excavator()
    hi, lo = m.split_by_plane((0, 0, 1), EXC_TRACK + 1e-3)
    F._put(s, "Iron Gray Metallic", lo.translate([x0, 0, zd]))
    F._put(s, "Sunflower Yellow", hi.translate([x0, 0, zd]))
    for side in (1, -1):
        F._put(s, "Sunflower Yellow", _excavator_front(side).translate([x0, 0, zd]))
    F._put(s, "Cocoa Brown", excavator_block().translate([x0 + 79.0, 0, zd]))
    return s


def scene_dozer():
    L = ft(53.5)
    s = F._car(L, "car_mineral")
    zd = F.deck()
    _place(s, dozer(), "Iron Gray Metallic", (DOZER_TRACK, "Sunflower Yellow"), 60.0, zd)
    _place(s, dozer_blade(), "Cocoa Brown", (BLADE_SKID, "Sunflower Yellow"), 140.0, zd)
    return s


def scene_crawler():
    L = ft(40.0)
    s = F._car(L, "car_oxide")
    zd = F.deck()
    for x in (L / 2 - 26.0, L / 2 + 26.0):
        _place(s, crawler_tractor(), "Iron Gray Metallic", (CRAWLER_TRACK, "Sunflower Yellow"), x, zd)
    return s


def scene_trailers():
    L = ft(89.3)
    s = F._car(L, "ttx_yellow", kind="fishbelly", W=ft(9.8))
    zd = F.deck()
    for x, col, seed in ((L / 2 - ft(21.0), "Silver", 1), (L / 2 + ft(21.0), "White", 2)):
        _place(s, trailer(seed), col, (TRL_CHANGE, "Black"), x, zd, upside=True)
    return s


def scene_containers():
    L = ft(89.3)
    s = F._car(L, "car_mineral", kind="fishbelly", W=ft(9.8))
    zd = F.deck()
    for x, col in zip(np.linspace(L / 2 - 108.0, L / 2 + 108.0, 4), ("Red", "Marine Blue", "Mistletoe Green", "Light Gray")):
        _place(s, iso_container(), col, None, x, zd)
    return s


def scene_crates():
    L = ft(40.0)
    s = F._car(L, "car_oxide")
    zd = F.deck()
    spots = [(28.0, -6.5, 0), (24.0, 8.5, 2), (62.0, -7.0, 1), (66.0, 9.0, 3), (100.0, 8.0, 4), (104.0, -6.0, 5)]
    cols = ["Caramel", "Latte Brown", "Caramel", "Desert Tan", "Latte Brown", "Caramel"]
    for (x, y, i), c in zip(spots, cols):
        _place(s, crate(i), c, None, x, zd, y, rz=0.0 if i in (0, 5) else 90.0)
    return s


def scene_chillers():
    L = ft(89.3)
    s = F._car(L, "car_black", kind="fishbelly", W=ft(9.8))
    zd = F.deck()
    for x in (L / 2 - 56.0, L / 2 + 56.0):
        _place(s, chiller(), "Iron Gray Metallic", (CHILL_BASE, "Light Gray"), x, zd)
    return s


def scene_propane():
    L = ft(53.5)
    s = F._car(L, "car_mineral", bulkhead=ft(9.0))
    zd = F.deck()
    for x in np.linspace(1.6 + 30.0, L - 1.6 - 30.0, 3):
        _place(s, propane_pair(), "Cocoa Brown", (PROP_DUN, "White"), x, zd)
    return s


def scene_miltrucks():
    L = ft(53.5)
    s = F._car(L, "car_black")
    zd = F.deck()
    for x0 in (8.0, 98.0):
        F._put(s, "Black", _mt_chassis_display().translate([x0, 0, zd]))
        F._put(s, "Bronze", mt_body().translate([x0, 0, zd + MT_PLANE]))
    return s


def scene_culverts():
    L = ft(40.0)
    s = F._car(L, "car_black")
    zd = F.deck()
    for x in np.linspace(16.0, L - 16.0, 4):
        _place(s, box_culvert(), "Cocoa Brown", (CULV_DUN, "Light Gray"), x, zd)
    return s


def scene_conpipe():
    L = ft(40.0)
    s = F._car(L, "car_mineral")
    zd = F.deck()
    for x in np.linspace(L / 2 - 44.0, L / 2 + 44.0, 3):
        _place(s, rcp_row(), "Cocoa Brown", (RCP_DUN, "Light Gray"), x, zd)
    return s


def scene_barriers():
    L = ft(53.5)
    s = F._car(L, "car_oxide")
    zd = F.deck()
    for x in np.linspace(26.0, L - 26.0, 4):
        for y in (-10.6, 0.0, 10.6):
            _place(s, jersey_barrier(), "Light Gray", None, x, zd, y)
    return s


def scene_manholes():
    L = ft(40.0)
    s = F._car(L, "car_black")
    zd = F.deck()
    kinds = [("base", 4.0), ("riser", 4.0), ("riser", 3.0), ("cone", 4.0), ("base", 4.0), ("riser", 2.0), ("cone", 4.0), ("riser", 3.0)]
    for i, (k, h) in enumerate(kinds):
        x = 14.0 + (i // 2) * 37.0
        y = -9.4 if i % 2 == 0 else 9.4
        _place(s, manhole(k, h), "Cocoa Brown", (MH_PAL, "Light Gray"), x, zd, y, rz=180.0 * (i % 2))
    return s


def scene_doubletees():
    L = ft(53.5)
    s = F._car(L, "car_mineral")
    zd = F.deck()
    for t in range(3):
        _place(s, double_tee(), "Light Gray", (DT_DEPTH, "Cocoa Brown"), L / 2, zd + t * (DT_DEPTH + 1.2), upside=True)
    return s


def scene_rebar():
    L = ft(53.5)
    s = F._car(L, "car_oxide")
    zd = F.deck()
    for t in range(2):
        _place(s, rebar_lift(seed=5 + t), "Cocoa Brown", (REBAR_DUN, "Copper Brown Metallic"), L / 2 + (t - 0.5) * 4.0, zd + t * (REBAR_DUN + 3.0))
    return s


def scene_sheetpile():
    L = ft(42.0)
    s = F._car(L, "car_oxide")
    zd = F.deck()
    for t in range(2):
        _place(s, sheet_pile_tier(seed=2 + t), "Cocoa Brown", (SP_DUN, "Iron Gray Metallic"), L / 2, zd + t * (SP_DUN + 8 * 0.5 + 3.5))
    return s


def scene_poles():
    L = ft(50.0)
    s = F._car(L, "car_black")
    zd = F.deck()
    _place(s, pole_pile(), "Caramel", (POLE_BUNK, "Black Walnut"), L / 2, zd)
    return s


def scene_crushed():
    L = ft(53.5)
    s = F._car(L, "car_oxide")
    zd = F.deck()
    pairs = [("Red", "Light Gray"), ("Cobalt Blue", "Copper Brown Metallic"), ("Mistletoe Green", "Black")]
    for i, x in enumerate(np.linspace(L / 2 - 58.0, L / 2 + 58.0, 3)):
        _place(s, crushed_stack(seed=i + 1), pairs[i][0], (CRUSH_CHANGE, pairs[i][1]), x, zd)
    return s


def scene_giantlog():
    L = ft(40.0)
    s = F._car(L, "car_black")
    zd = F.deck()
    _place(s, giant_log(), "Cocoa Brown", (GLOG_SILL, "Dark Brown"), L / 2, zd)
    return s


def scene_pulpwood():
    L = ft(40.0)
    s = F._car(L, "car_oxide", bulkhead=ft(10.0))
    zd = F.deck()
    for k, x in enumerate(np.linspace(1.6 + 22.0, L - 1.6 - 22.0, 3)):
        _place(s, pulpwood_rack(seed=3 + k), "Latte Brown", (PULP_H_CHANGE, "Dark Brown"), x, zd)
    return s


def scene_truss():
    L = ft(53.5)
    s = F._car(L, "car_mineral")
    zd = F.deck()
    side = truss_side()
    x0 = (L - TRUSS_L) / 2
    for xb in (x0 + 12.0, L / 2, x0 + TRUSS_L - 12.0):
        F._put(s, "Cocoa Brown", truss_blocking().translate([xb, 0, zd]))
    for y in (-8.0, 8.0):
        F._put(s, "Black", side.rotate([90, 0, 0]).translate([x0, y + 0.8, zd + 1.6]))
    return s


def scene_rotor():
    L = ft(53.5)
    s = F._car(L, "car_black")
    zd = F.deck()
    _place(s, generator_rotor(), "Black", (ROTOR_CHANGE, "Silver"), L / 2, zd)
    return s


def scene_stator():
    L = ft(52.0)
    s = F._car(L, "car_black", kind="depressed", well=ft(30.0), W=ft(10.0))
    _place(s, generator_stator(), "Black", (STATOR_CHANGE, "Gray"), L / 2, F.deck("depressed"))
    return s


def scene_tubebundle():
    L = ft(42.0)
    s = F._car(L, "car_mineral")
    zd = F.deck()
    _place(s, tube_bundle(), "Black", (TB_CHANGE, "Copper Brown Metallic"), L / 2, zd)
    return s


def scene_column():
    L = ft(60.0)
    s = F._car(L, "car_oxide")
    zd = F.deck()
    _place(s, column(), "Black", (COL_CHANGE, "Light Gray"), L / 2, zd)
    return s


def scene_gear():
    L = ft(40.0)
    s = F._car(L, "car_black")
    zd = F.deck()
    g = girth_gear_half()
    for x, rz in ((L / 2 - 36.0, 90.0), (L / 2 + 36.0, -90.0)):
        _place(s, g, "Cocoa Brown", (GEAR_SKID, "Gray"), x, zd, rz=rz)
    return s


def scene_genset():
    L = ft(53.5)
    s = F._car(L, "car_oxide")
    zd = F.deck()
    _place(s, genset(), "Black", (GENSET_BASE, "Bone White"), L / 2, zd)
    return s


SCENES = {"rotor": scene_rotor, "stator": scene_stator, "tubebundle": scene_tubebundle, "column": scene_column, "gear": scene_gear,
          "genset": scene_genset,
"sheetpile": scene_sheetpile, "poles": scene_poles, "crushed": scene_crushed, "giantlog": scene_giantlog,
          "pulpwood": scene_pulpwood, "truss": scene_truss,
"culverts": scene_culverts, "conpipe": scene_conpipe, "barriers": scene_barriers, "manholes": scene_manholes,
          "doubletees": scene_doubletees, "rebar": scene_rebar,
"trailers": scene_trailers, "containers": scene_containers, "crates": scene_crates, "chillers": scene_chillers,
          "propane": scene_propane, "miltrucks": scene_miltrucks,
"tank": scene_tank, "apc": scene_apc, "excavator": scene_excavator, "dozer": scene_dozer, "crawler": scene_crawler,
"concties": scene_concties, "woodties": scene_woodties, "granite": scene_granite, "bricks": scene_bricks,
          "ingotmolds": scene_ingotmolds, "cablereels": scene_cablereels,
"girders": scene_girders, "lumber": lambda: _lumber_scene("lumber"), "wrapped": lambda: _lumber_scene("wrapped"),
          "tires": scene_tires, "logs": scene_logs, "panels": scene_panels}

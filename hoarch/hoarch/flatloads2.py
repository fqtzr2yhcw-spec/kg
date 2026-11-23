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
    wrap_cs = (offset(hull, 0.35) - offset(hull, -0.05)) ^ CS.square((60.0, 60.0)).translate((-30.0, b))
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
    face = -W / 2 if i % 2 == 0 else W / 2
    for x in np.arange(1.2, L - 1.0, 1.9):
        cuts.append(M.cylinder(H + 2, 0.32, 0.32, 12).translate([x, face, z0 - 1]))
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
        _place(s, granite_block(i), "Cocoa Brown", (STONE_BLOCK, "Light Gray"), x, zd, rz=90.0)
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


SCENES = {"concties": scene_concties, "woodties": scene_woodties, "granite": scene_granite, "bricks": scene_bricks,
          "ingotmolds": scene_ingotmolds, "cablereels": scene_cablereels,
"girders": scene_girders, "lumber": lambda: _lumber_scene("lumber"), "wrapped": lambda: _lumber_scene("wrapped"),
          "tires": scene_tires, "logs": scene_logs, "panels": scene_panels}

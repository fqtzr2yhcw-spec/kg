"""Scenery packs: street lamps, iron fencing and trackside signs, sold in packs beside the
buildings. Every piece prints in its colours straight off the plate, with one filament change at
a height shared by the whole pack, so a plate is a batch of packs with no painting.

- Lamps: cast iron to ``ZG``, the globes above it.
- Fence: a stone curb to ``ZC``, wrought iron above it.
- Signs: printed lying face-up, the board to ``ZS`` and raised letters above it.

Local z is up from the ground (or from the bed, for the signs)."""
import math

import numpy as np
from manifold3d import Manifold as M

from .core import box, cs_union, poly, rect, union
from .ornament import ext
from .porchwork import _revolve
from .storefront import text_cs

ZG = 36.0                 # lamps: iron below, globe above
ZC = 3.0                  # fence: stone curb below, iron above
ZS = 1.2                  # signs: board below, letters above
LETTER = 0.4              # raised letters, 2 layers


def _capsule(a, b, r, seg=16):
    return M.hull(M.sphere(r, seg).translate(list(a)) + M.sphere(r, seg).translate(list(b)))


def _chain(pts, r, seg=16):
    return union([_capsule(a, b, r, seg) for a, b in zip(pts[:-1], pts[1:])])


def _ribs(prof, n, w=0.36, proud=0.22, z0=None, z1=None):
    """``n`` raised ribs following a revolved profile [(r, z)...] between z0 and z1."""
    zs = [z for _, z in prof]
    z0 = zs[0] if z0 is None else z0
    z1 = zs[-1] if z1 is None else z1
    seg = []
    for (ra, za), (rb, zb) in zip(prof[:-1], prof[1:]):
        if zb <= z0 or za >= z1 or zb <= za:
            continue
        seg.append(M.hull_points([(0.4, y, z) for y in (-w / 2, w / 2) for z in (max(za, z0), min(zb, z1))] +
                                 [(r + proud, y, z) for y in (-w / 2, w / 2)
                                  for r, z in ((ra + (rb - ra) * (max(za, z0) - za) / (zb - za), max(za, z0)),
                                               (ra + (rb - ra) * (min(zb, z1) - za) / (zb - za), min(zb, z1)))]))
    rib = union(seg)
    return union([rib.rotate([0, 0, 360.0 * k / n]) for k in range(n)])


def _globe_ball(c, r, neck):
    """A round globe on a short neck, wholly above ZG: the neck from ZG, the ball tangent to the
    neck at 45 degrees so it prints without support."""
    zc = ZG + 0.35 + math.sqrt(max(r * r - neck * neck, 0.0))
    return (M.cylinder(0.36, neck, neck, 24).translate([c[0], c[1], ZG]) +
            M.sphere(r, 36).translate([c[0], c[1], zc]))


# ================================================================== lamps
def lamp_acorn():
    """A park lamp with an acorn globe: an octagonal plinth, a bell base with eight raised ribs
    and a bead, a slim round shaft with two collars, a flared cup, and the acorn globe (with a
    knob) above ZG. About 42 mm tall."""
    plinth = M.cylinder(0.8, 2.6, 2.6, 8).rotate([0, 0, 22.5])
    bell = [(0.0, 0.79), (2.05, 0.79), (2.05, 1.2), (1.8, 1.5), (1.45, 2.4), (1.2, 3.6), (1.05, 4.8), (1.05, 5.1),
            (1.35, 5.4), (1.35, 5.8), (0.95, 6.2)]
    base = _revolve(bell, 40) + _ribs(bell, 8, z0=1.5, z1=4.8)
    shaft = _revolve([(0.0, 6.1), (0.86, 6.1), (0.74, 31.0), (0.74, 33.4), (1.0, 34.6), (1.25, 35.6),
                      (1.25, ZG), ], 28)
    collars = union([M.cylinder(0.25, 0.86, 1.12, 24).translate([0, 0, z]) + M.cylinder(0.3, 1.12, 1.12, 24).translate([0, 0, z + 0.24]) +
                     M.cylinder(0.25, 1.12, 0.8, 24).translate([0, 0, z + 0.53]) for z in (14.0, 27.0)])
    globe = _revolve([(0.0, ZG), (1.05, ZG), (1.6, ZG + 0.9), (1.85, ZG + 2.0), (1.8, ZG + 2.8), (1.5, ZG + 3.8),
                      (1.0, ZG + 4.6), (0.45, ZG + 5.1), (0.3, ZG + 5.3), (0.42, ZG + 5.45), (0.42, ZG + 5.7),
                      (0.0, ZG + 5.95)], 40)
    return union([plinth, base, shaft, collars, globe])


def lamp_boulevard():
    """A boulevard lamp with two ball globes: a round stepped base, a shaft with a crown of
    beads, two arms rising at 50 degrees to cups, and an iron spire between them that stops
    below ZG. About 40 mm tall."""
    base = _revolve([(0.0, 0.0), (2.5, 0.0), (2.5, 0.7), (2.1, 0.7), (2.1, 1.3), (1.75, 1.3), (1.75, 2.0), (1.3, 2.4),
                     (1.1, 3.4), (1.1, 3.8), (0.92, 4.1)], 40)
    zc = 29.6                                     # the collar the arms spring from
    shaft = _revolve([(0.0, 4.0), (0.92, 4.0), (0.78, zc), (1.25, zc + 0.4), (1.25, zc + 1.0), (0.6, zc + 1.6),
                      (0.45, ZG - 1.4), (0.0, ZG - 0.25)], 28)
    beads = union([M.sphere(0.32, 12).translate([1.2 * math.cos(a), 1.2 * math.sin(a), zc + 0.7])
                   for a in np.linspace(0, 2 * math.pi, 10, endpoint=False)])
    arms, cups, globes = [], [], []
    for s in (-1, 1):
        x1 = 4.3
        a = (s * 0.7, 0.0, zc + 0.5)
        b = (s * x1, 0.0, zc + 0.5 + (x1 - 0.7) * math.tan(math.radians(50)))
        arms.append(_capsule(a, b, 0.5))
        cups.append(_revolve([(0.0, b[2] - 0.2), (0.5, b[2] - 0.2), (1.12, ZG - 0.02), (1.12, ZG), (0.0, ZG)], 24)
                    .translate([s * x1, 0.0, 0.0]))
        globes.append(_globe_ball((s * x1, 0.0), 1.55, 1.1))
    # the arms must end below the cups' feet: clip anything above ZG
    iron = union([base, shaft, beads] + arms + cups)
    iron = iron ^ box([-20, -20, -1], [20, 20, ZG])
    return iron + union(globes)


def lamp_platform():
    """A square platform lamp: a chamfered plinth, a tapering square post with a sunk panel on
    each face, a moulded cap, a square-to-round holder and a large ball globe. About 41 mm."""
    plinth = M.hull_points([(x, y, z) for x in (-2.3, 2.3) for y in (-2.3, 2.3) for z in (0.0, 0.7)] +
                           [(x, y, 1.15) for x in (-1.85, 1.85) for y in (-1.85, 1.85)])
    post = M.hull_points([(x, y, 1.1) for x in (-1.15, 1.15) for y in (-1.15, 1.15)] +
                         [(x, y, 30.0) for x in (-0.82, 0.82) for y in (-0.82, 0.82)])
    panels = []
    for k in range(4):
        p = M.hull_points([(x, -1.4, z) for x in (-0.55, 0.55) for z in (3.0, 3.6)] +
                          [(x, -1.4, z) for x in (-0.42, 0.42) for z in (19.0, 19.6)] +
                          [(x, -0.9, z) for x in (-0.55, 0.55) for z in (3.0, 3.6)] +
                          [(x, -0.75, z) for x in (-0.42, 0.42) for z in (19.0, 19.6)])
        panels.append(p.rotate([0, 0, 90 * k]))
    # sink the panels 0.15 into the faces: cut the panel boxes with the post grown inward
    sunk = union(panels) - M.hull_points([(x, y, 1.1) for x in (-1.0, 1.0) for y in (-1.0, 1.0)] +
                                         [(x, y, 30.0) for x in (-0.67, 0.67) for y in (-0.67, 0.67)])
    post = post - sunk
    cap = (M.hull_points([(x, y, 29.95) for x in (-0.82, 0.82) for y in (-0.82, 0.82)] +
                         [(x, y, z) for x in (-1.35, 1.35) for y in (-1.35, 1.35) for z in (30.5, 31.1)]) +
           M.hull_points([(x, y, z) for x in (-1.1, 1.1) for y in (-1.1, 1.1) for z in (31.05, 31.5)]))
    holder = _revolve([(0.0, 31.45), (1.0, 31.45), (0.8, 33.2), (1.0, 34.0), (1.5, 35.4), (1.5, ZG), (0.0, ZG)], 32)
    return union([plinth, post, cap, holder, _globe_ball((0.0, 0.0), 2.05, 1.5)])


# ================================================================== fence
def _curb(x0, x1, w=2.2, joint=8.4):
    """A dressed stone curb from x0 to x1, ``w`` thick, up to ZC: a 0.4 chamfer on its top
    edges and a sunk joint every ``joint`` on both faces."""
    h = w / 2
    c = M.hull_points([(x, y, z) for x in (x0, x1) for y in (-h, h) for z in (0.0, ZC - 0.4)] +
                      [(x, y, ZC) for x in (x0, x1) for y in (-h + 0.4, h - 0.4)])
    n = max(1, int(round((x1 - x0) / joint)))
    cuts = [box([x0 + (x1 - x0) * k / n - 0.13, -h - 1, 0.35], [x0 + (x1 - x0) * k / n + 0.13, -h + 0.2, ZC + 1])
            for k in range(1, n)]
    cuts += [m.mirror([0, 1, 0]) for m in cuts]
    return c - union(cuts)


def _spear(x, z0, z1, b=0.8, d=0.8, tip=1.5):
    """A square bar ``b`` from z0 to z1 ending in a spear head ``tip`` tall: a 45 degree flare
    to 1.5 b, then the point. ``d`` thick across the fence."""
    s = poly([(x - b / 2, z0), (x + b / 2, z0), (x + b / 2, z1), (x + 0.75 * b, z1 + 0.25 * b),
              (x + 0.45 * b, z1 + 0.25 * b + 0.2), (x, z1 + tip), (x - 0.45 * b, z1 + 0.25 * b + 0.2),
              (x - 0.75 * b, z1 + 0.25 * b), (x - b / 2, z1)])
    return ext(s, -d / 2, d / 2).rotate([90, 0, 0])


def _xz(cs, d):
    """Extrude an (x, z) cross-section ``d`` thick, centred on y = 0."""
    return ext(cs, -d / 2, d / 2).rotate([90, 0, 0])


def fence_section(L=48.0, pitch=2.6):
    """A straight run of wrought-iron fence on a stone curb, ``L`` long, printed upright: spear
    bars every ``pitch`` to 12.6 mm, short dog bars between them at the foot, two rails, and an
    arcade band under the top rail. Butts against a fence_post at each end; the rails run 0.3
    past the curb to meet the post's iron."""
    curb = _curb(0.0, L)
    n = int((L - 1.2) / pitch)
    x0 = (L - n * pitch) / 2
    xs = [x0 + pitch * k for k in range(n + 1)]
    bars = [_spear(x, ZC - 0.01, 12.6) for x in xs]
    dogs = [_spear((a + b) / 2, ZC - 0.01, 6.2, b=0.7, d=0.7, tip=1.1) for a, b in zip(xs[:-1], xs[1:])]
    rails = [box([-0.3, -0.45, 4.1], [L + 0.3, 0.45, 4.8]), box([-0.3, -0.45, 10.6], [L + 0.3, 0.45, 11.4])]
    band = rect(xs[0], 9.0, xs[-1], 10.61)
    holes = []
    for a, b in zip(xs[:-1], xs[1:]):
        r = (b - a - 0.8) / 2
        holes.append(cs_union([rect(a + 0.4, 8.9, b - 0.4, 9.6), _arch(a + 0.4, b - 0.4, 9.6, r)]))
    arcade = _xz(band - cs_union(holes), 0.6)
    return union([curb] + bars + dogs + rails + [arcade])


def _arch(u0, u1, spring, r, seg=16):
    """A semicircular arch head of radius ``r`` on the span u0..u1, springing at ``spring``."""
    c = (u0 + u1) / 2
    return poly([(c + r * math.cos(t), spring + r * math.sin(t)) for t in np.linspace(0, math.pi, seg)])


def fence_post(tall=False):
    """A fence (or gate) post: a stone block up to ZC, then a square iron post with a sunk
    panel line, a cap, a pyramid and a ball finial. Gate posts (``tall``) are larger."""
    s = 1.1 if tall else 0.9                     # half the iron post's width
    h = 15.0 if tall else 12.6
    blk = s + 0.3                                # the stone block, the curb's ends butt against it
    stone = M.hull_points([(x, y, z) for x in (-blk, blk) for y in (-blk, blk) for z in (0.0, ZC - 0.4)] +
                          [(x, y, ZC) for x in (-blk + 0.4, blk - 0.4) for y in (-blk + 0.4, blk - 0.4)])
    post = box([-s, -s, ZC - 0.01], [s, s, h])
    groove = union([box([-s - 1, -0.12, ZC + 1.2], [s + 1, 0.12, h - 1.4]).rotate([0, 0, a]) for a in (0, 90)])
    post = post - (groove - box([-s + 0.2, -s + 0.2, 0], [s - 0.2, s - 0.2, h + 1]))
    collar = M.hull_points([(x, y, h - 0.01) for x in (-s, s) for y in (-s, s)] +
                           [(x, y, z) for x in (-s - 0.35, s + 0.35) for y in (-s - 0.35, s + 0.35) for z in (h + 0.35, h + 0.7)])
    pyr = M.hull_points([(x, y, h + 0.69) for x in (-s - 0.35, s + 0.35) for y in (-s - 0.35, s + 0.35)] +
                        [(x, y, h + 0.7 + s) for x in (-0.35, 0.35) for y in (-0.35, 0.35)])
    ball = M.cylinder(0.5, 0.3, 0.3, 12).translate([0, 0, h + 0.65 + s]) + M.sphere(0.6 if tall else 0.5, 16).translate([0, 0, h + 1.5 + s])
    return union([stone, post, collar, pyr, ball])


def fence_gate(W=22.0, pitch=2.4):
    """A double gate ``W`` wide between two tall posts (fence_post(tall=True)): a stone sill, two
    leaves whose top rail rises in an arc to the middle, spear bars, a lozenge medallion at the
    meeting stiles and a kick plate band at the foot."""
    sill = _curb(0.0, W, w=2.4, joint=W)
    sill = sill ^ box([-1, -2, -1], [W + 1, 2, ZC])
    rise = 2.0
    top = lambda x: 11.0 + rise * math.sin(math.pi * min(max(x / W, 0.0), 1.0))
    n = int((W - 1.6) / pitch)
    x0 = (W - n * pitch) / 2
    xs = [x0 + pitch * k for k in range(n + 1)]
    bars = [_spear(x, ZC - 0.01, top(x) + 1.0) for x in xs if abs(x - W / 2) > 1.0]
    stiles = [box([-0.3, -0.5, ZC - 0.01], [0.7, 0.5, top(0.5) + 0.8]), box([W - 0.7, -0.5, ZC - 0.01], [W + 0.3, 0.5, top(W - 0.5) + 0.8]),
              box([W / 2 - 0.9, -0.5, ZC - 0.01], [W / 2 + 0.9, 0.5, top(W / 2) + 1.0])]
    arc = [(x, top(x)) for x in np.linspace(0.0, W, 25)]
    toprail = _xz(poly(arc + [(x, z + 0.8) for x, z in arc[::-1]]), 0.9)
    rails = [box([0.0, -0.45, 4.0], [W, 0.45, 4.8]), box([0.0, -0.45, 6.4], [W, 0.45, 7.0])]
    kick = box([0.0, -0.3, ZC - 0.01], [W, 0.3, 4.05])
    cx, cz, R = W / 2, 9.0, 2.2
    lozenge = poly([(cx, cz - R), (cx + R, cz), (cx, cz + R), (cx - R, cz)])
    inner = poly([(cx, cz - R + 0.9), (cx + R - 0.9, cz), (cx, cz + R - 0.9), (cx - R + 0.9, cz)])
    medal = _xz(lozenge - inner, 0.8) + _xz(poly([(cx, cz - 0.5), (cx + 0.5, cz), (cx, cz + 0.5), (cx - 0.5, cz)]), 0.9)
    return union([sill] + bars + stiles + [toprail] + rails + [kick, medal])


# ================================================================== signs
def _sign(outline, words):
    """A sign printed face-up: ``outline`` (an (x, y) cross-section) to ZS, then the letters
    [(text, cap, x, y)] raised LETTER above it."""
    body = ext(outline, 0.0, ZS)
    letters = []
    for text, cap, x, y in words:
        letters.append(text_cs(text, cap, "sans", grow=0.1).translate((x, y)))
    return body + ext(cs_union(letters), ZS - 0.01, ZS + LETTER)


def _spike(w, y0, depth=2.6):
    """A planting spike below y0: the post narrowing to a point ``depth`` below."""
    return poly([(-w / 2, y0 + 0.01), (w / 2, y0 + 0.01), (0.25, y0 - depth), (-0.25, y0 - depth)])


def whistle_post():
    """A whistle post: a square-headed board with a big 'W' on a post, with a spike to plant."""
    post = rect(-0.8, 0.0, 0.8, 12.0)
    board = rect(-2.4, 11.0, 2.4, 16.6)
    outline = cs_union([post, board, _spike(1.6, 0.0)])
    return _sign(outline, [("W", 3.6, 0.0, 12.0)])


def milepost(n=37):
    """A concrete milepost with a rounded head and its number stacked down the face."""
    digits = str(n)
    h = 5.0 + 3.1 * len(digits)
    body = cs_union([rect(-1.5, 0.0, 1.5, h - 1.5), _round_head(1.5, h - 1.5), _spike(3.0, 0.0)])
    words = [(d, 2.4, 0.0, h - 3.6 - 3.1 * k) for k, d in enumerate(digits)]
    return _sign(body, words)


def _round_head(r, y0, seg=20):
    return poly([(r * math.cos(t), y0 + r * math.sin(t)) for t in np.linspace(0, math.pi, seg)])


def speed_board(n=25):
    """A speed-limit board: a square board with the number on a post."""
    post = rect(-0.75, 0.0, 0.75, 12.5)
    board = rect(-3.0, 11.5, 3.0, 17.5)
    rim = board - rect(-2.55, 11.95, 2.55, 17.05)
    s = _sign(cs_union([post, board, _spike(1.5, 0.0)]), [(str(n), 3.4, 0.0, 12.9)])
    return s + ext(rim, ZS - 0.01, ZS + LETTER)


def station_sign(name="FAIRVIEW", cap=2.8):
    """A station name board on two posts, with a raised border and the name centred."""
    w = max(20.0, 0.78 * cap * len(name) + 5.0)
    board = rect(-w / 2, 14.0, w / 2, 14.0 + cap + 2.4)
    rim = board - rect(-w / 2 + 0.5, 14.5, w / 2 - 0.5, 13.5 + cap + 2.4)
    posts = [rect(x - 0.8, 0.0, x + 0.8, 14.5) for x in (-w / 2 + 2.5, w / 2 - 2.5)]
    spikes = [_spike(1.6, 0.0).translate((x, 0.0)) for x in (-w / 2 + 2.5, w / 2 - 2.5)]
    s = _sign(cs_union([board] + posts + spikes), [(name, cap, 0.0, 15.2)])
    return s + ext(rim, ZS - 0.01, ZS + LETTER)


# ================================================================== packs
LAMPS = {"Acorn": lamp_acorn, "Boulevard": lamp_boulevard, "Platform": lamp_platform}


def review_scene():
    """The pilot pieces set out as a street corner for the review renders: a fence run with a
    gate across a front yard, the three lamps along the walk, and the signs planted beside it.
    Returns {material: [solids]}."""
    from .core import rot_z
    mats = {"iron": [], "globe": [], "stone": [], "signboard": [], "letters": []}

    def split(m, z, below, above):
        hi, lo = m.split_by_plane((0.0, 0.0, 1.0), z + 1e-3)
        mats[below].append(lo)
        mats[above].append(hi)

    x = 0.0
    run = [("post", None), ("section", 48.0), ("post", None), ("section", 48.0), ("gatepost", None), ("gate", 22.0),
           ("gatepost", None), ("section", 48.0), ("post", None)]
    for kind, L in run:
        if kind in ("post", "gatepost"):
            tall = kind == "gatepost"
            half = (1.1 if tall else 0.9) + 0.3
            split(fence_post(tall).translate([x + half, 0, 0]), ZC, "stone", "iron")
            x += 2 * half
        elif kind == "section":
            split(fence_section(L).translate([x, 0, 0]), ZC, "stone", "iron")
            x += L
        else:
            split(fence_gate(L).translate([x, 0, 0]), ZC, "stone", "iron")
            x += L
    for k, (f, lx) in enumerate([(lamp_acorn, 22.0), (lamp_boulevard, 70.0), (lamp_platform, 118.0),
                                 (lamp_acorn, 166.0)]):
        split(f().translate([lx, -16.0, 0]), ZG, "iron", "globe")
    signs = [(whistle_post(), 190.0), (milepost(37), 197.0), (speed_board(25), 205.0), (station_sign("FAIRVIEW"), 226.0)]
    for m, sx in signs:                          # stood up, face to the front, spike in the ground
        hi, lo = m.split_by_plane((0.0, 0.0, 1.0), ZS + 1e-3)
        mats["signboard"].append(lo.rotate([90, 0, 0]).translate([sx, -6.0, -2.4]))
        mats["letters"].append(hi.rotate([90, 0, 0]).translate([sx, -6.0, -2.4]))
    return mats


def write_review_npz(path):
    from .core import mesh_arrays
    data = {}
    for mat, ms in review_scene().items():
        vs, fs, o = [], [], 0
        for m in ms:
            if m.is_empty():
                continue
            v, f = mesh_arrays(m)
            vs.append(v)
            fs.append(f + o)
            o += len(v)
        data[mat + "__v"] = np.concatenate(vs).astype(np.float32)
        data[mat + "__f"] = np.concatenate(fs).astype(np.int32)
    np.savez_compressed(path, **data)

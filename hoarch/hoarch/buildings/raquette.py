"""The Raquette: an original HO-scale (1:87.1) Adirondack great camp lodge; house 110, of the
new-layouts batch (hoarch.novel2), after the main lodge at Sagamore, Raquette Lake, New York
(1897, William West Durant).

A Swiss-chalet lodge of logs three storeys high under one steep gable that faces the lake.
The roof runs twenty feet out over the gable front on purlins and two great log brackets and
shelters the stacked balconies there: a porch on rustic cedar posts across the whole front,
a balcony over it on more posts, and a small balcony tucked under the peak. A boulder
chimney climbs the lodge's west side. Behind, at right angles, the dining cabin (its own
porch, its own boulder chimney at the east gable), reached from the lodge by a covered walk.

- Walls: half-round logs laid up with a chink between, the logs at each corner running out
  past it as round log ends (every other course, the crossing wall's logs taking the others);
  the gables sided in cedar bark slabs. One part each storey; the upper one's gable in the
  bark colour above its one change.
- Cornices: the storey joint, the floor logs' cut ends with their growth rings between rails,
  a course of crossed twigs, a bevelled crown; the eave, Adirondack twig mosaic (nested
  diamonds) over log rafter ends under an ovolo; the cabin's own (crossed twigs, a cavetto).
- Windows and doors: casements in casings of half logs, the head log running past the jambs;
  the upper floors' under little bark hoods on twig brackets. The front door: two leaves of
  chevron boards with iron straps; glazed balcony doors over boarded panels.
- Porches: bark-on cedar posts with branch stubs, log beams and knee braces, railings of
  crooked branches crossed in Xs; planked decks on boulder piers. Each frame is one piece
  (posts, beams, railings, the deck over it) printed upside down; posts peg into the deck.
- Roof: hand-split slab shakes with zigzag butts, a ridge roll; purlins under the overhang
  and a twig-work bargeboard with a pendant across its front.

usage: python3 -m hoarch.buildings.raquette [check] [export]
"""
import json
import math
import os
import sys
import time

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import box, inv34, offset, poly, rect, slab, union
from hoarch import cornice as CO, gables as G, novel2 as N, openings as O
from hoarch.kit import Kit, print_flip
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, stacked_shells, wall_shell

NAME = "The Raquette"
COLORS = {"Logs": "#6B4B33", "Bark": "#4A3B2F", "Planks": "#B08A5E", "Green": "#3D5A41", "Red": "#8C3226",
          "Stone": "#8A857B", "Shakes": "#5A524B", "Windows_Doors": "#3D5A41"}
RENDER_MAT = {"Logs": "logs", "Bark": "bark", "Planks": "planks", "Green": "green", "Red": "red", "Stone": "stone",
              "Shakes": "roof", "Windows_Doors": "frame", "Sash": "sash", "Door": "door", "Glass": "glass"}
PALETTE = {"logs": ["#6B4B33", 0.85, 0.0], "bark": ["#4A3B2F", 0.95, 0.0], "planks": ["#B08A5E", 0.75, 0.0],
           "green": ["#3D5A41", 0.6, 0.0], "red": ["#8C3226", 0.6, 0.0], "stone": ["#8A857B", 0.9, 0.0],
           "roof": ["#5A524B", 0.85, 0.0], "frame": ["#3D5A41", 0.6, 0.0], "sash": ["#8C3226", 0.5, 0.0],
           "door": ["#7A4A2E", 0.6, 0.0]}
VIEWS = {"hero": [-30, 16, 70, 0.9, [0, 0, -12]], "hero_right": [32, 16, 70, 0.9, [0, 0, -12]],
         "front": [0, 6, 85, 0.92, [0, 0, 0]], "rear": [160, 20, 70, 0.92, [0, 0, -10]],
         "balconies": [-14, 8, 85, None, [88, 60, 80], 190], "cabin": [24, 14, 85, None, [196, 100, 30], 170],
         "peak": [-12, 14, 85, None, [88, 62, 112], 150]}

LEDGE = 1.4
JOINT = dict(pitch=10.0, margin=3.0, layers=[
    dict(kind="frieze", h=4.0, b=1.2, orn="rqlogends", role="Planks"),
    dict(kind="course", h=1.6, b=1.2, orn="rqtwig", role="Bark"),
    dict(kind="crown", h=1.6, b=1.2, P=2.8, orn="bevel", role="Green")])
EAVE = dict(pitch=9.0, margin=3.0, layers=[
    dict(kind="frieze", h=3.8, b=1.2, orn="rqmosaic", role="Red"),
    dict(kind="bed", h=2.2, b=1.4, P=4.0, role="Bark", brackets=dict(style="rqrafter", t=1.6, h=2.4)),
    dict(kind="crown", h=1.8, b=1.4, P=4.6, orn="ovolo", role="Green")])
CEAVE = dict(pitch=9.0, margin=3.0, layers=[
    dict(kind="course", h=2.0, b=1.2, orn="rqtwig", role="Bark"),
    dict(kind="crown", h=1.6, b=1.2, P=3.0, orn="cavetto", role="Green")])
RJ = round((LEDGE + 0.4 + CO.band_height(JOINT)) / 0.2) * 0.2
HE = CO.band_height(EAVE)
HEC = CO.band_height(CEAVE)

# ------------------------------------------------------------------ the lodge
T = 3.0
ZF = 10.0
X0, X1, Y0, Y1 = 40.0, 136.0, 76.0, 156.0          # 96 x 80, the gable front to -y
XC = (X0 + X1) / 2
S1 = ZF + 34.0
ZU = S1 + RJ
ZE = ZU + 26.0
ZW = round((ZE + HE) / 0.2) * 0.2
FASCIA = 1.4
Z_EAVE = ZW + FASCIA
SL, D_EAVE, SKIN = 1.05, 3.6, 1.6
RAKE_F, RAKE_B = 20.0, 3.4                         # the roof's run past the front gable, and the back
LODGE = Block("lodge", [(X0, Y0), (X1, Y0), (X1, Y1), (X0, Y1)], ZF, ZW)
YPF = Y0 - 15.5                                    # the balconies' front posts
PXS = [float(x) for x in np.linspace(X0 + 1.5, X1 - 1.5, 6)]
YB = Y0 - 1.3                                      # the upper decks' back edge (clear of the logs)
YD = Y0 - 17.5                                     # the balconies' front edge
CY = (Y0 + Y1) / 2 + 8.0                           # the boulder chimney on the west side
CH = np.array([[0.0, -1.0, 0.0, X0], [1.0, 0.0, 0.0, CY], [0.0, 0.0, 1.0, 0.0]])
# the dining cabin, its gables east and west, and the covered walk to it
DX0, DX1, DY0, DY1 = 158.0, 230.0, 100.0, 156.0
ZEC = ZF + 32.0
ZWC = round((ZEC + HEC) / 0.2) * 0.2
ZC_EAVE = ZWC + 1.2
SLC, DC_EAVE, RAKE_C = 0.85, 3.0, 3.0
CABIN = Block("cabin", [(DX0, DY0), (DX1, DY0), (DX1, DY1), (DX0, DY1)], ZF, ZWC)
CYC = 128.0
CHC = np.array([[0.0, 1.0, 0.0, DX1], [-1.0, 0.0, 0.0, CYC], [0.0, 0.0, 1.0, 0.0]])
WY0, WY1 = 116.0, 136.0
ZWP = ZF + 22.0                                    # the walk's plates
V1 = 7.0


def _z_us(x):
    """The lodge roof's under side over x (under the skin, out on the overhang)."""
    return Z_EAVE - SKIN + SL * min(x - (X0 - D_EAVE), (X1 + D_EAVE) - x)


def _openings():
    L1, L2, LC = [], [], []
    fams = {}

    def add(L, blk, x, y, v0, sp, name, kind="window"):
        e, u = blk.locate(x, y)
        L.append(Opening(blk, e, u, v0, sp, name, kind))
        L[-1].fam = fams.setdefault(id(sp), name)

    lo, up, bal = N.window_rqlower(), N.window_rqupper(), N.door_rqbalcony()
    VB = ZU + 1.4 - ZF                             # the balcony's floor (its deck on the joint's crown)
    V2 = ZU + 5.0 - ZF
    VT = ZW + 1.4 - ZF                             # the top balcony's floor
    # the gable front: the front door between two windows, the balcony door between two more,
    # the door onto the top balcony under the peak
    add(L1, LODGE, XC, Y0, 0.0, N.door_rqfront(), "front-door", "door")
    add(L2, LODGE, XC, Y0, VB, bal, "balcony-door", "door")
    for x in (XC - 30.0, XC + 30.0):
        add(L1, LODGE, x, Y0, V1, lo, f"S{x:.0f}-1")
        add(L2, LODGE, x, Y0, V2, up, f"S{x:.0f}-2")
    add(L2, LODGE, XC, Y0, VT, N.door_rqbalcony(w=8.0, h=18.0), "top-door", "door")
    # the back: two windows and a door, two windows over, one in the gable
    for x in (X0 + 18.0, XC):
        add(L1, LODGE, x, Y1, V1, lo, f"N{x:.0f}-1")
    add(L1, LODGE, X1 - 18.0, Y1, 0.0, bal, "back-door", "door")
    for x in (X0 + 24.0, X1 - 24.0):
        add(L2, LODGE, x, Y1, V2, up, f"N{x:.0f}-2")
    add(L2, LODGE, XC, Y1, ZW + 8.0 - ZF, up, "N-gable")
    # the west side beside the chimney; the east, the door onto the walk between windows
    add(L1, LODGE, X0, 92.0, V1, lo, "W92-1")
    add(L2, LODGE, X0, 92.0, V2, up, "W92-2")
    for y in (92.0, 146.0):
        add(L1, LODGE, X1, y, V1, lo, f"E{y:.0f}-1")
    add(L1, LODGE, X1, (WY0 + WY1) / 2, 0.0, bal, "walk-door", "door")
    for y in (96.0, 140.0):
        add(L2, LODGE, X1, y, V2, up, f"E{y:.0f}-2")
    # the cabin: its door onto the porch between windows, two at the back, one in the east
    # gable beside the chimney, the door from the walk in the west
    add(LC, CABIN, 194.0, DY0, 0.0, N.door_rqfront(w=11.0, h=22.0), "cabin-door", "door")
    for x in (172.0, 216.0):
        add(LC, CABIN, x, DY0, V1, lo, f"C-S{x:.0f}")
    for x in (176.0, 212.0):
        add(LC, CABIN, x, DY1, V1, lo, f"C-N{x:.0f}")
    add(LC, CABIN, DX1, 108.0, V1, lo, "C-E108")
    add(LC, CABIN, DX0, (WY0 + WY1) / 2, 0.0, bal, "cabin-walk-door", "door")
    return L1, L2, LC


OPEN1, OPEN2, OPEN_C = _openings()
OPENINGS = OPEN1 + OPEN2 + OPEN_C
BLOCKS = [LODGE, CABIN]


def _skin(f, b, reg):
    """Half logs up to the eave cornice's band (and clear of the joint's), cedar bark in the
    gables over it."""
    ze, zw = (ZE, ZW) if b is LODGE else (ZEC, ZWC)
    reg = reg - rect(-1, ze - LEDGE - 0.6 - b.z0, f.L + 1, zw - b.z0 + 0.2)
    if b is LODGE:
        reg = reg - rect(-1, S1 - b.z0, f.L + 1, ZU - b.z0)
    if reg.is_empty():
        return M()
    cut = rect(-50.0, -50.0, f.L + 50.0, zw - b.z0)
    lo, hi = reg ^ cut, reg - cut
    out = []
    if not lo.is_empty():
        out.append(N.halflog_raquette(lo, datum=0.0, L=f.L if f.L > 8.0 else None, shift=0.0 if abs(f.u[0]) > 0.5 else 0.5))
    if not hi.is_empty():
        out.append(N.bark_raquette(hi, datum=zw - b.z0 + 0.2, seed=int(f.L) % 17))
    return union(out)


def _place_inserts(kit, ops, keep, group="inserts"):
    for o in ops:
        A = o.local_frame()
        sp = o.spec
        b = sp["cut"].bounds()
        key = "DOOR" if o.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, "Windows_Doors", "Door" if o.kind == "door" else "Sash", "Glass")
        part = kit.add(f"{key}-{o.name}", "Windows_Doors", world, P=P, key=f"{key}-{o.fam}-{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}",
                       group=group, render=zones)
        keep.append(part.solid)


def _env(c, step=2.0, grow=0.4):
    """A chimney's room: the hulls of its slices, each a little grown."""
    b = c.bounding_box()
    out = []
    for z in np.arange(b[2], b[5], step):
        sl = c ^ box([b[0] - 1, b[1] - 1, z - 0.01], [b[3] + 1, b[4] + 1, z + step + 0.01])
        if not sl.is_empty():
            h = M.hull(sl)
            hb = h.bounding_box()
            cx, cy = (hb[0] + hb[3]) / 2, (hb[1] + hb[4]) / 2
            sx = (hb[3] - hb[0] + grow) / max(1e-6, hb[3] - hb[0])
            sy = (hb[4] - hb[1] + grow) / max(1e-6, hb[4] - hb[1])
            out.append(h.translate([-cx, -cy, 0]).scale([sx, sy, 1.0]).translate([cx, cy, 0]))
    return union(out)


def _zones(solid, z, below, above):
    lo = box([-1e4, -1e4, -10.0], [1e4, 1e4, z + 0.05])
    return [(below, solid ^ lo), (above, solid - lo)]


def _m44(A):
    return np.vstack([A, [0, 0, 0, 1.0]])


def _gable_cs(wl, fascia):
    return wl["cs"] + rect(0.0, -fascia - 0.4, wl["L"], -fascia + 0.01)


# ------------------------------------------------------------------ rustic carpentry
def _rail(a, b, z0, h=7.0, t=1.0):
    """A branch railing from a to b (plan points) standing on z0."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy)
    c, s = dx / L, dy / L
    return N.rail_raquette(L, h=h, t=t).transform(np.array([[c, 0.0, s, a[0]], [s, 0.0, -c, a[1]], [0.0, 1.0, 0.0, z0]]))


def _capsule(p, q, r=0.6):
    return M.hull(M.sphere(r, 12).translate(p) + M.sphere(r, 12).translate(q))


def _beam(p0, p1, zb, zt, half):
    """A squared log beam from p0 to p1 (plan), its under edges chamfered."""
    p0, p1 = np.array(p0, float), np.array(p1, float)
    d = (p1 - p0) / np.linalg.norm(p1 - p0)
    n = np.array([-d[1], d[0]])
    pts = []
    for p in (p0, p1):
        for sg in (-1, 1):
            pts += [tuple(p + sg * n * half) + (zt,), tuple(p + sg * n * half) + (zb + 0.6,), tuple(p + sg * n * (half - 0.6)) + (zb,)]
    return M.hull_points(pts)


def _pier(x, y, z1, r=2.0, seed=0):
    """A pier of boulders laid dry, each course chamfered top and bottom (45 degrees), from
    z = 0 to z1."""
    rng = np.random.default_rng(seed)
    parts, z = [], 0.0
    while z < z1 - 0.3:
        h = min(rng.uniform(2.2, 3.0), z1 - z)
        rr = r * rng.uniform(0.88, 1.05)
        jit = rng.uniform(0.9, 1.08, 9)
        ring = [(x + rr * j * math.cos(a), y + rr * j * math.sin(a)) for j, a in zip(jit, np.linspace(0, 2 * math.pi, 9, endpoint=False))]
        c = min(0.3, h / 4)
        pts = [(px, py, z + dz) for px, py in ring for dz in (c, h - c)]
        pts += [(x + (px - x) * (1 - c / rr), y + (py - y) * (1 - c / rr), z + dz) for px, py in ring for dz in (0.0, h)]
        parts.append(M.hull_points(pts))
        z += h - 0.05
    return union(parts)


def _frame(xs, ybk, z_foot, z_top, beam_h, r, seed0, skip=(), y_wall=Y0 - 2.6, rail_gap=1.0):
    """A balcony frame: cedar posts at (x, YPF) and back posts at the ends' (x, ybk) from z_foot
    (pegs under them) to the beams, the beams along the front and back along the sides to the
    back posts (top z_top), knee braces, branch railings between the front posts (not the
    ``skip`` bays) and down the sides to the wall."""
    zb = z_top - beam_h
    parts = [_beam((xs[0] - r, YPF), (xs[-1] + r, YPF), zb, z_top, 1.3)]
    for x in (xs[0], xs[-1]):
        parts.append(_beam((x, YPF), (x, ybk - 1.6), zb, z_top, 1.3))
    posts = [(x, YPF) for x in xs] + [(xs[0], ybk), (xs[-1], ybk)]
    for k, (x, y) in enumerate(posts):
        parts.append(N.post_raquette(zb - z_foot + 0.3, r=r, seed=seed0 + k).translate([x, y, z_foot]))
        parts.append(box([x - 0.8, y - 0.8, z_foot - 1.2], [x + 0.8, y + 0.8, z_foot + 0.3]))
    zk = zb - 5.0
    for x in xs:                                   # knee braces along the front
        for sg in (-1, 1):
            if xs[0] - 0.1 <= x + sg * 5.0 <= xs[-1] + 0.1:
                parts.append(_capsule((x + sg * (r - 0.2), YPF, zk), (x + sg * 5.0, YPF, zb + 0.3)))
    for x in (xs[0], xs[-1]):                      # and back along the sides
        parts.append(_capsule((x, YPF + r - 0.2, zk), (x, YPF + 5.0, zb + 0.3)))
        parts.append(_capsule((x, ybk - r + 0.2, zk), (x, ybk - 5.0, zb + 0.3)))
    for xa, xb in zip(xs[:-1], xs[1:]):
        if any(u0 <= (xa + xb) / 2 <= u1 for u0, u1 in skip):
            continue
        parts.append(_rail((xa + r - 0.4, YPF), (xb - r + 0.4, YPF), z_foot + rail_gap))
    for x in (xs[0], xs[-1]):
        parts.append(_rail((x, YPF + r - 0.4), (x, ybk - r + 0.4), z_foot + rail_gap))
        parts.append(_rail((x, ybk + r - 0.4), (x, y_wall), z_foot + rail_gap))
    return union(parts), posts


def _deck(x0, x1, y0, y1, z, posts, th=1.4, rim=2.6, sock=1.0, along="y"):
    """A planked deck (top z) with a rim board round its edge and sockets for posts."""
    d = box([x0, y0, z - th], [x1, y1, z])
    d = d + box([x0, y0, z - rim], [x1, y0 + 1.0, z - th + 0.1]) + box([x0, y0, z - rim], [x0 + 1.0, y1, z - th + 0.1]) + \
        box([x1 - 1.0, y0, z - rim], [x1, y1, z - th + 0.1])
    if along == "y":
        gaps = [box([x - 0.15, y0 - 1, z - 0.3], [x + 0.15, y1 + 1, z + 1]) for x in np.arange(x0 + 1.6, x1 - 0.4, 1.6)]
    else:
        gaps = [box([x0 - 1, y - 0.15, z - 0.3], [x1 + 1, y + 0.15, z + 1]) for y in np.arange(y0 + 1.6, y1 - 0.4, 1.6)]
    socks = [box([x - 0.95, y - 0.95, z - th - sock], [x + 0.95, y + 0.95, z + 1]) for x, y in posts]
    return d - union(gaps) - union(socks)




def _purlin(x, vc, r, y0, y1):
    """A log purlin along y (from y1 to y0) under the overhang, its axis at height vc, its
    under side cut to a 45 degree ridge (it prints with the roof, nothing hanging)."""
    pts = [(r * math.cos(a), vc + r * math.sin(a)) for a in np.linspace(-math.pi / 4, 5 * math.pi / 4, 12)]
    pts.append((0.0, vc - r * math.sqrt(2)))
    return M.extrude(poly(pts), y0 - y1).transform(np.array([[-1.0, 0, 0, x], [0, 0, 1.0, y1], [0, 1.0, 0, 0]]))


def _sheared(x0, x1, y0, y1, ztop, below, above):
    """A slab under (and over) a plane sloping along y."""
    return M.hull_points([(x, y, ztop(y) + dz) for x in (x0, x1) for y in (y0, y1) for dz in (-below, above)])


def _steps(xa, xb, y0, dy, n=3, rise=2.5, run=2.8):
    """Split stone steps from a deck's edge at y0 out along dy, standing on z = 0."""
    out = []
    for j in range(n):
        z = ZF - rise * (j + 1)
        ya, yb = sorted((y0 + dy * run * j, y0 + dy * run * (j + 1)))
        out.append(M.hull_points([(x, y, 0.0) for x in (xa, xb) for y in (ya, yb)] +
                                 [(x, y, z - 0.4) for x in (xa, xb) for y in (ya, yb)] +
                                 [(x, y, z) for x in (xa + 0.35, xb - 0.35) for y in (ya + 0.35, yb - 0.35)]))
    return union(out)


def _deck_piece(kit, name, deck, piers, sockets, P, zf=ZF):
    """A deck on its boulder piers, printed upside down: the planks, then the stone."""
    d = (deck + piers) - sockets
    kit.add(name, "Planks", d, P=P, group="porch", change=(2.6, "Stone"), render=_zones(d, zf - 2.6, "Stone", "Planks"))


def _shed_porch(kit, name, A, L, D, posts, steps, z_hi, s=0.32, OS=1.6, OV=2.4, PT=1.4, seed=0):
    """A porch against a wall, in its own frame (x 0..L along the wall, the wall at y = 0, the
    porch out to y = -D) placed by A. The top is one piece: a shake roof sloping ``s`` from
    z_hi, its courses and joints grooved into its face, pole rafters, a ledger, a log beam on
    rustic posts (pegs under them) with knee braces, branch railings (not across ``steps``).
    It prints tilted onto its roof face: the shakes are the first 0.6 mm, then one change.
    The deck: planks out from the wall, a rim, boulder piers; printed upside down."""
    zt = lambda y: z_hi + s * y
    y_out = -(D + OV)
    rng = np.random.default_rng(seed + 3)
    parts = [_sheared(-OS, L + OS, y_out, 0.0, zt, PT, 0.0)]
    grooves = []
    for y in np.arange(-1.6, y_out, -2.6):
        grooves.append(_sheared(-OS - 1, L + OS + 1, y - 0.15, y + 0.15, zt, 0.3, 1.0))
        x = -OS + rng.uniform(0.5, 2.5)
        while x < L + OS - 0.5:
            grooves.append(_sheared(x - 0.13, x + 0.13, max(y - 2.6, y_out - 1.0), y, zt, 0.3, 1.0))
            x += rng.uniform(2.2, 3.6)
    parts.append(box([0.0, -1.2, z_hi - PT - 2.2], [L, 0.0, z_hi - PT + 0.3]))
    for x in np.arange(1.2, L - 0.6, 4.4):
        parts.append(_sheared(x - 0.5, x + 0.5, y_out + 0.3, -1.2, zt, PT + 1.0, -PT + 0.2))
    zb = round((zt(-D) - PT - 2.6) / 0.2) * 0.2
    yp = -D + 1.4
    parts.append(_beam((-0.4, yp), (L + 0.4, yp), zb, zt(-D + 2.8) - PT + 0.2, 1.4))
    for k, u in enumerate(posts):
        parts.append(N.post_raquette(zb - ZF + 0.3, r=1.4, seed=seed + 40 + k).translate([u, yp, ZF]))
        parts.append(box([u - 0.8, yp - 0.8, ZF - 1.2], [u + 0.8, yp + 0.8, ZF + 0.3]))
        for sg in (-1, 1):
            if 0.4 < u + sg * 4.6 < L - 0.4:
                parts.append(_capsule((u + sg * 1.2, yp, zb - 4.6), (u + sg * 4.6, yp, zb + 0.3)))
    for ua, ub in zip(posts[:-1], posts[1:]):
        if any(u0 <= (ua + ub) / 2 <= u1 for u0, u1 in steps):
            continue
        parts.append(_rail((ua + 1.0, yp), (ub - 1.0, yp), ZF + 1.0))
    for u in (posts[0], posts[-1]):
        parts.append(_rail((u, yp + 1.0), (u, -2.6), ZF + 1.0))
    top = union(parts) - union(grooves)
    face = _sheared(-OS - 1, L + OS + 1, y_out - 1, 1.0, zt, 0.6, 2.0)
    ph_ = math.pi - math.atan(s)
    R = np.array([[1.0, 0, 0, 0], [0, math.cos(ph_), -math.sin(ph_), 0], [0, math.sin(ph_), math.cos(ph_), 0]])
    P = (_m44(R) @ np.linalg.inv(_m44(A)))[:3]
    topw, facew = top.transform(A), face.transform(A)
    kit.add(f"{name}-top", "Shakes", topw, P=P, group="porch", change=(0.6, "Bark"),
            render=[("Shakes", topw ^ facew), ("Bark", topw - facew)])
    pp = [(u, yp) for u in posts]
    deck = _deck(0.0, L, -D, -1.8, ZF, pp)
    piers = union([_pier(min(max(u, 1.8), L - 1.8), y, ZF - 1.3, seed=seed + k * 3 + j)
                   for k, u in enumerate(posts) for j, y in enumerate((yp, -4.0))])
    socks = union([box([u - 0.95, yp - 0.95, ZF - 2.4], [u + 0.95, yp + 0.95, ZF + 1]) for u in posts])
    _deck_piece(kit, f"{name}-deck", deck.transform(A), piers.transform(A), socks.transform(A),
                (_m44(print_flip()) @ np.linalg.inv(_m44(A)))[:3])
    return topw


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    keep = []

    # --- the chimneys first: everything else keeps clear of them
    chl = N.chimney_raquette(h=round((ZW + 32.0) / 0.2) * 0.2, seed=2).transform(CH)
    zrc = ZC_EAVE + SLC * ((DY1 - DY0) / 2 + DC_EAVE)
    chc = N.chimney_raquette(h=round((zrc + 7.0) / 0.2) * 0.2, w0=22.0, d0=12.0, w1=13.0, d1=9.0, seed=5,
                             boulders=False).transform(CHC)
    ch_env, chc_env = _env(chl), _env(chc)

    # --- the lodge: its roof and gable walls, two storey shells, the cornices
    yf, yb_ = Y0 - (RAKE_F - D_EAVE), Y1 + (RAKE_B - D_EAVE)
    rpts = [(X0, yf), (X1, yf), (X1, yb_), (X0, yb_)]
    rf = G.gabled_roof([(rpts, [1, 3], SL)], Z_EAVE, D_EAVE,
                       [dict(p0=(X0, Y0), p1=(X1, Y0), slope=SL), dict(p0=(X1, Y1), p1=(X0, Y1), slope=SL)],
                       texture="rqslab", tex_kw=dict(pitch=2.8, d=0.35), skin=SKIN, rake=RAKE_F,
                       inner_cs=offset(LODGE.cs, -3.0), fascia=FASCIA, hollow=2.6)
    gables = [(LODGE, 0, _gable_cs(rf["walls"][0], FASCIA).translate((0.0, Z_EAVE - ZF))),
              (LODGE, 2, _gable_cs(rf["walls"][1], FASCIA).translate((0.0, Z_EAVE - ZF)))]
    BX = (XC - 16.0, XC + 16.0)                    # the great brackets (the bark kept off the gable behind them)
    br_env = union([box([x - 1.7, Y0 - 1.0, ZW - 0.5], [x + 1.7, Y0 + 0.1, _z_us(x) + 2.0]) for x in BX])
    walk_env = box([X1 - 0.2, WY0 - 3.0, ZWP - 0.6], [DX0 + 0.2, WY1 + 3.0, ZWP + 12.0])
    band = slab(offset(LODGE.cs, 10.0), ZE - LEDGE - 0.6, ZW + 0.01)
    st = stacked_shells([LODGE], OPEN1 + OPEN2, [S1], t=T, corners="none", siding=_skin, clear=[lip_keep(LODGE.cs, T, ZF, 1.2)],
                        prof=CO.joint_profile(RJ, LEDGE), belt_blocks=None, water_table=False,
                        undress=[band, ch_env, br_env, walk_env], gables=gables)
    kit.add("WALLS-1", "Logs", st["shells"][0].trim_by_plane([0, 0, 1.0], ZF), group="walls")
    kit.add("BELT", "Logs", st["rings"][0] - ch_env, group="walls")
    lip = _corbel(LODGE.cs, T, ZW) + lip_ring(LODGE.cs, T, ZW)
    w2 = st["shells"][1] + lip + (CO.ledge(LODGE.pts, ZE, LEDGE, t=T) - ch_env)
    kit.add("WALLS-2", "Logs", w2, group="walls", change=(round(ZW - ZU, 1), "Bark"), render=_zones(w2, ZW, "Logs", "Bark"))
    jr, _ = CO.level(st["outlines"][0], S1 + LEDGE + 0.4, JOINT, cut=ch_env)
    CO.add_level(kit, jr, "CORNICE-J", "cornice")
    er, _ = CO.level(LODGE.pts, ZE, EAVE, t=T, cut=ch_env)
    CO.add_level(kit, er, "CORNICE-E", "cornice")
    j_env = union([r["solid"] for r in jr])
    jtop = max(r["solid"].bounding_box()[5] for r in jr)
    yproj = min(r["solid"].bounding_box()[1] for r in er)
    ybk = min(Y0 - 7.5, yproj - 2.0)               # the balconies' back posts, clear of the cornices
    print("joint top", round(jtop, 2), "ZU", ZU, "eave out to", round(Y0 - yproj, 2), "ZW", ZW)
    _place_inserts(kit, OPEN1 + OPEN2, keep)
    house_keep = union(keep)
    print("lodge walls", round(time.time() - t0, 1))

    # --- the roof: slab shakes, a ridge roll, purlins and eave plates under the overhang
    roof = rf["body"] + rf["tex"] + rf["skins"] + rf["skin_tex"]
    zr = Z_EAVE + SL * ((X1 - X0) / 2 + D_EAVE)
    walls_env = union([wl["facade"].place(M.extrude(wl["cs"].offset(0.15), RAKE_B + 4.2).translate([0, 0, -3.15])) for wl in rf["walls"]])
    roof = roof + (G.ridge_cap((XC, Y0 - RAKE_F), (XC, Y1 + RAKE_B), zr, SL, ZW, half=1.2, up=0.6) - walls_env)
    y_bg = Y0 - RAKE_F + 1.2                       # the bargeboard's back
    purl = [_purlin(x, _z_us(x) - 0.8, 1.6, Y0 - 0.6, y_bg) for x in (XC - 32.0, XC + 32.0)]
    purl.append(_purlin(XC, _z_us(XC) - 1.4, 1.8, Y0 - 0.6, y_bg))
    for xa, xb in ((X0 + 0.3, X0 + 2.7), (X1 - 2.7, X1 - 0.3)):
        purl.append(M.hull_points([(x, y, z) for x in (xa, xb) for y in (y_bg, yproj - 0.4) for z in (ZW, _z_us(x) + 0.6)]))
    roof = roof + union(purl)
    roof = roof - lip_keep(LODGE.cs, T, ZW) - ch_env
    roof = max(roof.decompose(), key=lambda m_: m_.volume())
    kit.add("ROOF", "Shakes", roof, group="roof")
    rb = roof.bounding_box()
    print("roof y", round(rb[1], 2), round(rb[4], 2), "x", round(rb[0], 2), round(rb[3], 2))
    Lb = (X1 - X0) + 2 * D_EAVE
    A_bg = np.array([[1.0, 0, 0, X0 - D_EAVE], [0, 0, -1.0, y_bg], [0, 1.0, 0, Z_EAVE - SKIN]])
    bg = N.barge_raquette(Lb, SL).transform(A_bg) - roof
    kit.add("BARGE", "Bark", max(bg.decompose(), key=lambda m_: m_.volume()), P=inv34(A_bg), group="roof")
    Rb = np.array([[0, 1.0, 0, 0], [0, 0, 1.0, 0], [1.0, 0, 0, 0]])
    brackets = []
    for k, x in enumerate(BX):
        ztop = _z_us(x) + 1.0
        Ab = np.array([[-1.0, 0, 0, x], [0, -1.0, 0, Y0 - 0.05], [0, 0, 1.0, ztop]])
        bk = N.bracket_raquette(H=ztop - ZW, D=Y0 - 0.05 - y_bg, r=1.5).transform(Ab) - roof
        bk = max(bk.decompose(), key=lambda m_: m_.volume())
        brackets.append(bk)
        kit.add(f"BRACKET-{k}", "Bark", bk, P=(_m44(Rb) @ np.linalg.inv(_m44(Ab)))[:3], group="roof")
    print("roof", round(time.time() - t0, 1))

    # --- the stacked balconies. The top one under the peak: its deck on the eave cornice and
    # the frame below, branch railings on short posts, printed upside down
    txs = [float(x) for x in np.linspace(X0 + 9.5, X1 - 9.5, 4)]
    tdeck = box([X0 + 8.0, YD, ZW], [X1 - 8.0, YB, ZW + 1.4])
    tdeck = tdeck - union([box([x - 0.15, YD - 1, ZW + 1.1], [x + 0.15, YB + 1, ZW + 3]) for x in np.arange(X0 + 9.6, X1 - 8.4, 1.6)])
    tparts = [tdeck]
    for k, x in enumerate(txs):
        tparts.append(N.post_raquette(8.4, r=1.2, seed=60 + k).translate([x, YD + 1.2, ZW + 1.39]))
        tparts.append(M.cylinder(0.8, 1.5, 1.5, 18).translate([x, YD + 1.2, ZW + 9.7]))
    for xa, xb in zip(txs[:-1], txs[1:]):
        tparts.append(_rail((xa + 0.9, YD + 1.2), (xb - 0.9, YD + 1.2), ZW + 2.2))
    for x in (txs[0], txs[-1]):
        tparts.append(_rail((x, YD + 2.1), (x, Y0 - 0.6), ZW + 2.2))
    top = union(tparts) - house_keep - union([box([x - 1.75, Y0 - 3.3, ZW - 1], [x + 1.75, Y0 + 1, ZW + 12]) for x in BX])
    kit.add("TOP-BALCONY", "Planks", top, P=print_flip(), group="porch", change=(1.4, "Bark"),
            render=_zones(top, ZW + 1.4, "Planks", "Bark"))
    # the balcony frame: posts from the balcony's floor to the plates under the top balcony
    corner = union([box([x - 2.0, Y0 - 2.7, 0.0], [x + 2.0, Y0 + 1.0, 200.0]) for x in (X0 + 0.5, X1 - 0.5)])
    uf, uposts = _frame(PXS, ybk, ZU + 1.4, ZW, 2.4, 1.5, 20)
    kit.add("BALCONY-top", "Bark", uf, P=print_flip(), group="porch")
    # the porch frame and the balcony deck on it (one piece, printed upside down on the deck)
    lf, lposts = _frame(PXS, ybk, ZF, ZU, 2.6, 1.8, 1, skip=[(XC - 5.0, XC + 5.0)])
    bdeck = _deck(X0 - 0.3, X1 + 0.3, YD, YB, ZU + 1.4, uposts, rim=2.6) - j_env - corner - house_keep
    ptop = lf + bdeck
    kit.add("PORCH-top", "Planks", ptop, P=print_flip(), group="porch", change=(1.4, "Bark"),
            render=_zones(ptop, ZU, "Bark", "Planks"))
    # the porch deck on its boulder piers
    pdeck = _deck(X0 - 0.5, X1 + 0.5, Y0 - 18.0, Y0 - 1.8, ZF, lposts) - corner
    piers = union([_pier(x, y, ZF - 1.3, seed=k) for k, (x, y) in enumerate(lposts)] +
                  [_pier(x, Y0 - 4.6, ZF - 1.3, seed=30 + k) for k, x in enumerate((XC - 24.0, XC + 24.0))])
    socks = union([box([x - 0.95, y - 0.95, ZF - 2.4], [x + 0.95, y + 0.95, ZF + 1]) for x, y in lposts])
    _deck_piece(kit, "PORCH-deck", pdeck, piers, socks, print_flip())
    kit.add("STEPS", "Stone", _steps(XC - 6.4, XC + 6.4, Y0 - 18.0, -1.0), group="stoop")
    print("balconies", round(time.time() - t0, 1))

    # --- the covered walk: deck on piers, a frame of posts, plates and ties (upside down), a
    # little gabled roof between the walls
    wxs, wys = [X1 + 4.5, DX0 - 4.5], [WY0 + 1.6, WY1 - 1.6]
    wposts = [(x, y) for x in wxs for y in wys]
    wpts = [(X1 + 0.1, WY0), (DX0 - 0.1, WY0), (DX0 - 0.1, WY1), (X1 + 0.1, WY1)]
    rw = G.gabled_roof([(wpts, [0, 2], 0.7)], ZWP + 1.0, 1.4, [], texture="rqslab", tex_kw=dict(pitch=2.4, d=0.3), skin=1.2,
                       inner_cs=offset(poly(wpts), -1.6), fascia=1.0, hollow=1.6)
    walls_both = LODGE.solid(grow=0.1, dz0=-10, dz1=300) + CABIN.solid(grow=0.1, dz0=-10, dz1=300)
    wroof = rw["body"] + rw["tex"] - walls_both
    wroof = max(wroof.decompose(), key=lambda m_: m_.volume())
    kit.add("WALK-ROOF", "Shakes", wroof, group="roof")
    fr = []
    for k, (x, y) in enumerate(wposts):
        fr.append(N.post_raquette(ZWP - 1.4 - ZF + 0.3, r=1.2, seed=70 + k).translate([x, y, ZF]))
        fr.append(box([x - 0.7, y - 0.7, ZF - 1.0], [x + 0.7, y + 0.7, ZF + 0.3]))
        for sg in (-1, 1):
            xe = x + sg * 3.6
            if X1 + 1.6 < xe < DX0 - 1.6:
                fr.append(_capsule((x + sg * 1.0, y, ZWP - 5.0), (xe, y, ZWP - 1.2), 0.5))
        sg = 1 if y < (WY0 + WY1) / 2 else -1
        fr.append(_capsule((x, y + sg * 1.0, ZWP - 5.0), (x, y + sg * 3.6, ZWP - 1.2), 0.5))
    for y in wys:
        fr.append(_beam((X1 + 1.6, y), (DX0 - 1.6, y), ZWP - 1.4, ZWP, 0.8))
    for x in wxs:
        fr.append(_beam((x, WY0 + 0.8), (x, WY1 - 0.8), ZWP - 1.4, ZWP, 0.7))
    kit.add("WALK-frame", "Bark", union(fr), P=print_flip(), group="porch")
    wdeck = _deck(X1 + 1.8, DX0 - 1.8, WY0, WY1, ZF, wposts)
    wpiers = union([_pier(x, y, ZF - 1.3, r=1.8, seed=80 + k) for k, (x, y) in enumerate(wposts)])
    wsocks = union([box([x - 0.85, y - 0.85, ZF - 2.4], [x + 0.85, y + 0.85, ZF + 1]) for x, y in wposts])
    _deck_piece(kit, "WALK-deck", wdeck, wpiers, wsocks, print_flip())
    wr_env = M.hull(wroof)
    print("walk", round(time.time() - t0, 1))

    # --- the dining cabin
    rc = G.gabled_roof([(CABIN.pts, [0, 2], SLC)], ZC_EAVE, DC_EAVE,
                       [dict(p0=(DX1, DY0), p1=(DX1, DY1), slope=SLC), dict(p0=(DX0, DY1), p1=(DX0, DY0), slope=SLC)],
                       texture="rqslab", tex_kw=dict(pitch=2.6, d=0.35), skin=1.6, rake=RAKE_C,
                       inner_cs=offset(CABIN.cs, -3.0), fascia=1.2, hollow=2.4)
    cg = [(CABIN, 1, _gable_cs(rc["walls"][0], 1.2).translate((0.0, ZC_EAVE - ZF))),
          (CABIN, 3, _gable_cs(rc["walls"][1], 1.2).translate((0.0, ZC_EAVE - ZF)))]
    z_hi = ZEC - LEDGE - 1.0
    cpl = box([DX0 - 3.0, DY0 - 2.6, z_hi - 4.2], [DX1 + 3.0, DY0 + 0.1, z_hi + 0.6])
    cband = slab(offset(CABIN.cs, 8.0), ZEC - LEDGE - 0.6, ZWC + 0.01)
    csh = wall_shell([CABIN], OPEN_C, t=T, belt=None, corners="none", water_table=False, siding=_skin, gables=cg,
                     undress=[cband, chc_env, walk_env, cpl])
    cw = csh.trim_by_plane([0, 0, 1.0], ZF) - lip_keep(CABIN.cs, T, ZF, 1.2)
    cw = cw + _corbel(CABIN.cs, T, ZWC) + lip_ring(CABIN.cs, T, ZWC) + (CO.ledge(CABIN.pts, ZEC, LEDGE, t=T) - chc_env - wr_env)
    kit.add("CABIN-WALLS", "Logs", cw, group="walls", change=(round(ZWC - ZF, 1), "Bark"), render=_zones(cw, ZWC, "Logs", "Bark"))
    cr, _ = CO.level(CABIN.pts, ZEC, CEAVE, t=T, cut=chc_env + wr_env)
    CO.add_level(kit, cr, "CORNICE-C", "cornice")
    _place_inserts(kit, OPEN_C, keep)
    croof = rc["body"] + rc["tex"] + rc["skins"] + rc["skin_tex"]
    cwenv = union([wl["facade"].place(M.extrude(wl["cs"].offset(0.15), RAKE_C + 4.2).translate([0, 0, -3.15])) for wl in rc["walls"]])
    croof = croof + (G.ridge_cap((DX0 - RAKE_C, (DY0 + DY1) / 2), (DX1 + RAKE_C, (DY0 + DY1) / 2), zrc, SLC, ZWC, half=1.1, up=0.5) - cwenv)
    croof = croof - lip_keep(CABIN.cs, T, ZWC) - chc_env
    kit.add("CABIN-ROOF", "Shakes", max(croof.decompose(), key=lambda m_: m_.volume()), group="roof")
    cposts = [1.6, 24.5, 47.5, DX1 - DX0 - 1.6]
    _shed_porch(kit, "CABIN-PORCH", np.array([[1.0, 0, 0, DX0], [0, 1.0, 0, DY0], [0, 0, 1.0, 0]]), DX1 - DX0, 14.0, cposts,
                [(24.5, 47.5)], z_hi, seed=4)
    kit.add("CABIN-STEPS", "Stone", _steps(DX0 + 29.5, DX0 + 42.5, DY0 - 14.0, -1.0), group="stoop")
    print("cabin", round(time.time() - t0, 1))

    # --- the footings and the chimneys
    doors = union(keep)                            # (the door casings run a little under the sills)
    kit.add("BASE", "Stone", foundation([LODGE], 0.0, ZF, style="rqboulder") - ch_env - doors, group="foundation")
    kit.add("CABIN-BASE", "Stone", foundation([CABIN], 0.0, ZF, style="rqboulder", seed=9) - chc_env - doors, group="foundation")
    kit.add("CHIMNEY", "Stone", chl, P=inv34(CH), group="chimney")
    kit.add("CABIN-CHIMNEY", "Stone", chc, P=inv34(CHC), group="chimney")
    print("specks dropped:", kit.drop_specks())
    print("done", round(time.time() - t0, 1))
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "raquette")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    json.dump({"materials": PALETTE, "views": VIEWS}, open(os.path.join(OUT, "palette.json"), "w"), indent=1)
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:80]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "raquette.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))

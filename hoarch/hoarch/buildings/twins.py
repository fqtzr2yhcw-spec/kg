"""Laurel & Myrtle -- an original HO-scale (1:87.1) pair of San Francisco Italianate row houses,
after the user's photo of a cream house and a sage house side by side. Rev B: the house-size
plan (two houses 96 x 136 mm, storeys of 46 and 42 mm), framed windows, and built-up cornices at
every level.

Two houses built as one model, mirror images in plan with their doors side by side in the
middle, each on a panelled wooden raised basement and each with its own trim:

- The Laurel (cream and gold): narrow bevel siding, banded corner pilasters, a tablet
  belt, a two-storey slanted bay with Corinthian colonnettes, round-arched windows in
  square architraves under caps on scroll consoles (two lights over four), a portico of
  Corinthian columns with a segmental pediment and a sunburst over a pair of roundel doors
  with a gridded transom, a cornice on paired acanthus consoles with dentils, a pediment
  with an oculus over the bay, and a stuccoed chimney with roundels.
- The Myrtle (sage and forest green): flush beaded boards, cabled corner pilasters, a
  belt of paired blocks, a slanted bay with fluted colonnettes, segmental windows under
  hoods with oval cartouches (a plain lower sash under an upper sash of three rows), a portico of fluted square piers carrying a
  pierced balustrade over a pair of bolection doors with a quatrefoil transom, a cornice on
  twin consoles under a fleur-de-lis iron cresting, and a brick chimney with a chequer band.

Each house climbs a tall stoop with panelled cheek walls and newel posts, and an iron area
railing of spear-headed bars fences the ground in front of each bay. The flat roofs are the
cornice rings' decks (a filament change gives them a dark top). Built-up cornices, each house
its own: between the storeys the Laurel's gold panelled frieze, cream egg-and-dart course and
gold crown, the Myrtle's forest key-block frieze, sage cable course and forest crown; under
each main cornice a frieze and a course of its own (the Laurel's gold medallions over cream
dentils, the Myrtle's forest tulips over sage pellets).

usage: python3 -m hoarch.buildings.twins [check] [export]
"""
import math
import os
import sys
import time

import numpy as np
from manifold3d import JoinType, Manifold as M

from hoarch.core import arch_cs, box, circle, compose, cs_union, inv34, offset, poly, rect, slab, union
from hoarch import cornice as CO, extras as EX, features as FT, openings as O, roof as R, skins as SK, storefront as SF, \
    trimwork as TW
from hoarch.kit import Kit, print_flip
from hoarch.ornament import chamfer_box, ext, stroke
from hoarch.porchwork import _clamp45
from hoarch.shell import Block, Opening, foundation, stacked_shells

NAME = "Laurel & Myrtle San Francisco Pair"
COLORS = {"Cream": "#EDE2C4", "Gold": "#C9A24A", "Sage": "#9DB49E", "Forest": "#3F5E4C", "Stone": "#D8CDB4",
          "Brick": "#8C4A36", "Slate": "#4A4E52", "Iron": "#23262A", "Windows_Doors": "#F1ECDF"}
RENDER_MAT = {"Cream": "siding", "Gold": "gold", "Sage": "sage", "Forest": "forest", "Stone": "stone",
              "Brick": "brick", "Slate": "roof", "Iron": "iron", "Windows_Doors": "trim", "Sash": "sash",
              "Door": "door", "Glass": "glass"}

# ------------------------------------------------------------------ cornices (each house its own)
LEDGE = 1.4
JOINTS = {"L": dict(pitch=11.0, margin=3.6, layers=[
              dict(kind="frieze", h=4.4, b=1.2, orn="panels", role="Gold"),
              dict(kind="course", h=1.6, b=1.4, orn="eggdart", role="Cream"),
              dict(kind="crown", h=2.2, b=1.4, P=3.6, orn="ogee_fillet", role="Gold")]),
          "M": dict(pitch=11.0, margin=3.6, layers=[
              dict(kind="frieze", h=4.4, b=1.2, orn="keys", role="Forest"),
              dict(kind="course", h=1.6, b=1.4, orn="cable", role="Sage"),
              dict(kind="crown", h=2.2, b=1.4, P=3.6, orn="stepped", role="Forest")])}
FRIEZES = {"L": dict(pitch=11.0, margin=3.6, layers=[        # under each house's bracketed cornice
               dict(kind="frieze", h=5.2, b=1.2, orn="medallions", role="Gold"),
               dict(kind="course", h=1.6, b=1.4, orn="dentil", role="Cream", tooth=1.0, gap=0.6)]),
           "M": dict(pitch=11.0, margin=3.6, layers=[
               dict(kind="frieze", h=5.2, b=1.2, orn="tulips", role="Forest"),
               dict(kind="course", h=1.6, b=1.4, orn="pellets", role="Sage")])}
RJ = round((LEDGE + 0.4 + CO.band_height(JOINTS["L"])) / 0.2) * 0.2
HF = CO.band_height(FRIEZES["L"])

# ------------------------------------------------------------------ levels (on the 0.2 mm grid)
ZF = 22.0                       # the raised basement
S1 = ZF + 46.0
RH = RJ
ZE = S1 + RJ + 42.0             # the frieze ledge's top
ZC = ZE + HF                    # the wall top: the bracketed cornice ring sits here
V1 = 8.0
V2 = S1 + RJ + 5.0 - ZF

# ------------------------------------------------------------------ plan: two halves 96 wide, 136 deep
HW, D = 96.0, 136.0
BD = 12.8                       # the bays' depth; their cants are at 45 degrees
PH = 33.0                       # portico: column height above the floor
PD = 10.0                       # portico depth (front of its cornice)
DOOR_W, DOOR_H = 14.0, 32.0
NST, TREAD = 10, 2.4            # stoop risers and tread
LAND = 10.0                     # stoop landing depth
SW = 12.0                       # stoop half-width inside the cheek walls
UC = 10.0                       # portico columns either side of the door (2 inside the cheeks)
CHEEK = 1.8


def _half(tag):
    """Plan and style of one house. The Myrtle is the Laurel's plan mirrored about x = 60."""
    m = tag == "M"
    X = (lambda x: 2 * HW - x) if m else (lambda x: x)
    x0, x1 = sorted((X(0.0), X(HW)))
    b0, b1 = sorted((X(6.0), X(56.0)))
    main = Block(f"main{tag}", [(x0, 0), (x1, 0), (x1, D), (x0, D)], ZF, ZC)
    bay = Block(f"bay{tag}", [(b0, 3.0), (b0, 0.0), (b0 + BD, -BD), (b1 - BD, -BD), (b1, 0.0), (b1, 3.0)], ZF, ZC)
    H = dict(tag=tag, X=X, x0=x0, x1=x1, main=main, bay=bay, door_x=X(76.0), chim=(X(14.0), 90.0),
             party=HW)
    if not m:
        H.update(name="Laurel", wall="Cream", trim="Gold", siding=SK.narrow_lap, corners="banded", belt="tablet",
                 head="ancon", rise=lambda w: w / 2, lites=(2, 2), rows=(2, 1), leaf="roundel", tstyle="grid",
                 chimney="roundel", keep=box([HW, -100, -1], [400, 300, 400]))
    else:
        H.update(name="Myrtle", wall="Sage", trim="Forest", siding=SK.flush_bead, corners="cabled", belt="twinblock",
                 head="cartouche", rise=lambda w: round(w * 0.24 / 0.2) * 0.2, lites=(1, 1), rows=(1, 3),
                 leaf="bolection", tstyle="quatrefoil", chimney="chequer", keep=box([-400, -100, -1], [HW, 300, 400]))
    return H


HALVES = [_half("L"), _half("M")]


def _openings(H):
    L = []
    X = H["X"]

    def win(w, h):
        return SF.window_commercial(w, h, rise=H["rise"](w), lites=H["lites"], rows=H["rows"], sill=1.2, head=H["head"],
                                    casing=1.3, band=True)

    def add(blk, x, y, v0, sp, name, kind="window"):
        e, u = blk.locate(x, y)
        L.append(Opening(blk, e, u, v0, sp, f"{H['tag']}-{name}", kind))

    bay, main = H["bay"], H["main"]
    Q = [np.array(p) for p in bay.pts]
    for k, (w1, tag) in ((1, (7.2, "c0")), (2, (10.4, "f")), (3, (7.2, "c1"))):
        mm = (Q[k] + Q[k + 1]) / 2
        add(bay, mm[0], mm[1], V1, win(w1, 28.0), f"bay{tag}-1")
        add(bay, mm[0], mm[1], V2, win(w1, 26.0), f"bay{tag}-2")
    door = SF.door_commercial(DOOR_W, DOOR_H, transom=5.6, leaf=H["leaf"], tstyle=H["tstyle"], head=None, leaves=2)
    add(main, H["door_x"], 0.0, 0.0, door, "door", "door")
    add(main, H["door_x"], 0.0, V2, win(8.4, 26.0), "over-door-2")
    xs = X(0.0)                                        # the outer side wall
    for y in (36.0, 80.0, 118.0):
        add(main, xs, y, V1, win(8.4, 26.0), f"side{y:.0f}-1")
        add(main, xs, y, V2, win(8.4, 24.0), f"side{y:.0f}-2")
    add(main, X(72.0), D, 0.0, SF.door_commercial(10.0, 30.0, transom=4.4, leaf=H["leaf"], tstyle=H["tstyle"], head=None),
        "back-door", "door")
    for x in (22.0, 48.0):
        add(main, X(x), D, V1, win(8.4, 26.0), f"back{x:.0f}-1")
    for x in (22.0, 48.0, 74.0):
        add(main, X(x), D, V2, win(8.4, 24.0), f"back{x:.0f}-2")
    return L


for _H in HALVES:
    _H["openings"] = _openings(_H)


# ------------------------------------------------------------------ turned and square supports
def _revolve(prof, seg=32):
    p = _clamp45(prof)
    return M.revolve(poly(p + [(0.0, p[-1][1])]), seg)


def corinthian(h, r, plinth=True):
    """A Corinthian column (or colonnette) of height h, shaft radius r at its foot: a square
    plinth, a torus base, a tapering shaft, an astragal, a bell capital flaring at 45 degrees
    cut into eight leaves, and a square abacus. Prints upright."""
    zq = lambda z: round(z / 0.2) * 0.2
    pl = zq(max(0.8, r * 0.8)) if plinth else 0.0
    cap = zq(r * 1.9)
    prof = [(0, pl), (r + 0.3, pl), (r + 0.3, pl + 0.4), (r + 0.1, pl + 0.6), (r, pl + 0.8), (r * 0.86, h - cap - 0.4),
            (r * 0.86 + 0.2, h - cap - 0.2), (r * 0.86, h - cap), (r * 0.86 + cap * 0.55, h - cap * 0.45), (r * 0.86 + cap * 0.55, h - 0.8)]
    body = _revolve(prof)
    for k in range(8):                                  # the bell cut into eight leaves
        slot = box([r * 0.86 + 0.3, -0.25, zq(h - cap + 0.4)], [r * 3.0, 0.25, h - 0.8])
        body = body - slot.rotate([0, 0, 22.5 + 45.0 * k])
    ab = r * 0.86 + cap * 0.55 + 0.2
    body = body + box([-ab, -ab, h - 0.8], [ab, ab, h])
    if plinth:
        body = body + box([-r - 0.5, -r - 0.5, 0.0], [r + 0.5, r + 0.5, pl + 0.01])
    return body


def fluted(h, r, square=False):
    """A fluted support: a round colonnette (six flutes, a torus-and-block cushion cap) or,
    ``square``, a square pier with two flutes on each face, a plinth and a capital flaring
    at 45 degrees under a square abacus. Prints upright."""
    zq = lambda z: round(z / 0.2) * 0.2
    if not square:
        prof = [(0, 0), (r + 0.5, 0), (r + 0.5, 0.8), (r + 0.2, 1.0), (r, 1.2), (r, h - 2.0), (r + 0.3, h - 1.7),
                (r + 0.3, h - 1.4), (r + 0.7, h - 1.0), (r + 0.7, h - 0.8)]
        body = _revolve(prof)
        for k in range(6):
            a = 2 * math.pi * k / 6
            body = body - box([r - 0.25, -0.25, 1.6], [r + 1.0, 0.25, h - 2.4]).rotate([0, 0, math.degrees(a)])
        return body + box([-r - 0.8, -r - 0.8, h - 0.8], [r + 0.8, r + 0.8, h])
    s = r
    body = box([-s, -s, 0.0], [s, s, h])
    for k in range(4):
        for du in (-0.6, 0.6):
            cut = box([du - 0.25, s - 0.3, 2.4], [du + 0.25, s + 1.0, h - 2.8])
            body = body - cut.rotate([0, 0, 90.0 * k])
    base = box([-s - 0.5, -s - 0.5, 0.0], [s + 0.5, s + 0.5, 1.2])
    capf = M.hull_points([(x, y, h - 2.2) for x in (-s, s) for y in (-s, s)] +
                         [(x, y, h - 1.6) for x in (-s - 0.6, s + 0.6) for y in (-s - 0.6, s + 0.6)])
    cap = box([-s - 0.6, -s - 0.6, h - 1.61], [s + 0.6, s + 0.6, h - 0.8]) + box([-s - 0.9, -s - 0.9, h - 0.81], [s + 0.9, s + 0.9, h])
    return body + base + capf + cap


# ------------------------------------------------------------------ the portico and the stoop (door frame: u across, v up
# from the floor at ZF, w out from the wall face)
def portico_canopy(H):
    """The portico's roof, printed on its back (w = 0 on the bed): wall pilasters answering
    the columns, an entablature, and over it the Laurel's segmental pediment with a sunburst
    or the Myrtle's flat top (its balustrade is a part of its own). Returns (solid, landing)."""
    uc = UC
    ew = uc + 2.4
    parts = []
    for sg in (-1, 1):                                 # responds
        parts.append(box([sg * uc - 1.2, 0.0, 0.0], [sg * uc + 1.2, PH, 0.8]))
        parts.append(box([sg * uc - 1.6, 0.0, 0.0], [sg * uc + 1.6, 1.2, 1.0]))
        parts.append(box([sg * uc - 1.6, PH - 1.4, 0.0], [sg * uc + 1.6, PH, 1.0]))
    parts.append(box([-ew, PH, 0.0], [ew, PH + 1.4, PD - 0.6]))                                   # architrave
    parts.append(box([-ew, PH + 1.39, 0.0], [ew, PH + 3.2, PD - 0.8]))                           # frieze
    parts.append(chamfer_box(-ew - 0.6, PH + 3.2, ew + 0.6, PH + 4.4, 0.0, PD, c=0.4, square=("v1",)))   # cornice
    top = PH + 4.4
    if H["tag"] == "L":
        for u in np.linspace(-ew + 1.0, ew - 1.0, 12):                                         # dentils on the frieze face
            parts.append(box([u - 0.35, PH + 2.0, PD - 0.81], [u + 0.35, PH + 3.21, PD - 0.4]))
        seg = arch_cs(-ew - 0.6, ew + 0.6, top - 0.01, top - 0.01, rise=5.0, seg=40)
        parts.append(ext(seg, 0.0, PD - 0.4))
        parts.append(ext(seg - seg.offset(-0.9), PD - 0.41, PD + 0.2))
        inner = seg.offset(-0.9)
        rays = cs_union([stroke([(0.0, top), (9 * math.cos(a), top + 9 * math.sin(a))], 0.55)
                         for a in np.linspace(0.3, math.pi - 0.3, 7)] + [circle((0.0, top), 1.4, 24)])
        parts.append(ext(rays ^ inner, PD - 0.41, PD))
        parts.append(ext(poly([(-0.8, top + 3.2), (0.8, top + 3.2), (1.0, top + 5.6), (-1.0, top + 5.6)]), PD - 0.41, PD + 0.4))
        outline = cs_union([rect(-ew - 0.6, 0.0, ew + 0.6, top), seg])
    else:
        parts.append(box([-ew - 0.6, top - 0.01, 0.0], [ew + 0.6, top + 0.6, PD]))             # the balcony floor edge
        outline = rect(-ew - 0.6, 0.0, ew + 0.6, top + 0.6)
    land = ext(outline.offset(0.2) ^ rect(-50, 0.0, 50, 200), -0.01, 0.8)
    return union(parts), land


def portico_rail(H):
    """The Myrtle's balustrade round the portico top: corner posts with ball caps, a top rail
    and panels pierced with a row of round holes. Prints upright. Frame as portico_canopy,
    v from the portico top."""
    ew = UC + 2.4 + 0.6 - 0.9
    h, t = 4.4, 0.8
    wb = 2.2                                           # clear of the siding and the belt
    runs = [((-ew, PD - 0.9), (ew, PD - 0.9)), ((-ew, wb), (-ew, PD - 0.9)), ((ew, PD - 0.9), (ew, wb))]
    out = []
    for (a, b) in runs:
        a, b = np.array(a), np.array(b)
        L_ = float(np.linalg.norm(b - a))
        tt = (b - a) / L_
        n = np.array([tt[1], -tt[0]])
        panel = rect(0.0, 0.0, L_, h) - cs_union([circle((L_ * (k + 0.5) / max(1, int(L_ / 2.2)), h * 0.5), 0.7, 16)
                                                   for k in range(max(1, int(L_ / 2.2)))])
        A = np.array([[tt[0], 0.0, n[0], a[0]], [0.0, 1.0, 0.0, 0.0], [tt[1], 0.0, n[1], a[1]]])
        body = ext(panel, 0.0, t) + box([0.0, h - 0.8, -0.2], [L_, h, t + 0.2]) + box([0.0, 0.0, -0.2], [L_, 0.8, t + 0.2])
        out.append(body.translate([0, 0, -t / 2]).transform(A))
    for (x, y) in ((-ew, PD - 0.9), (ew, PD - 0.9), (-ew, wb), (ew, wb)):
        post = box([x - 0.9, 0.0, y - 0.9], [x + 0.9, h + 0.4, y + 0.9]) + M.sphere(0.7, 16).translate([x, h + 0.9, y])
        out.append(post)
    return union(out)


def stoop(H):
    """A tall stoop: a landing at the floor, a straight flight of NST risers, panelled cheek
    walls following the flight with a coping, and a newel post at the foot of each with its
    cap (the Laurel's a ball, the Myrtle's a pyramid). Local door frame, v = world z."""
    r = ZF / NST
    parts = [box([-SW, 0.0, 0.0], [SW, ZF, LAND])]
    for k in range(NST - 1):
        top = round((ZF - (k + 1) * r) / 0.2) * 0.2
        parts.append(box([-SW, 0.0, LAND + k * TREAD - 0.01], [SW, top, LAND + (k + 1) * TREAD]))
    run = LAND + (NST - 1) * TREAD
    for sg in (-1, 1):
        a, b = sorted((sg * SW, sg * (SW + CHEEK)))
        pts = [(u, 0.0, 0.0) for u in (a, b)] + [(u, ZF + 6.0, 0.0) for u in (a, b)] + \
              [(u, ZF + 6.0, LAND) for u in (a, b)] + [(u, 6.0, run) for u in (a, b)] + [(u, 0.0, run) for u in (a, b)]
        wall = M.hull_points(pts)
        # a sunk panel on the outer face, following the flight
        o = b if sg > 0 else a
        d = 0.3 * sg
        pp = [(o - d * 1.5, v, w) for v, w in ((2.0, LAND + 1.0), (ZF + 2.4, LAND + 1.0), (4.6, run - 2.4), (2.0, run - 2.4))]
        pp += [(o + d * 2, v, w) for _, v, w in pp]
        wall = wall - M.hull_points(pp)
        uu = (a - 0.3, b + 0.3)
        cop = box([uu[0], ZF + 5.99, 0.0], [uu[1], ZF + 6.8, LAND]) + \
            M.hull_points([(u, v, w) for u in uu for v, w in ((ZF + 5.99, LAND), (ZF + 6.8, LAND), (5.99, run), (6.8, run))])
        parts += [wall, cop]
        nc = (a + b) / 2
        newel = box([nc - 1.6, 0.0, run - 0.01], [nc + 1.6, 9.0, run + 3.2])
        newel = newel + box([nc - 1.9, 9.0, run - 0.3], [nc + 1.9, 9.8, run + 3.5])
        if H["tag"] == "L":
            newel = newel + M.sphere(1.3, 24).translate([nc, 11.0, run + 1.6]) + \
                M.cylinder(0.6, 0.8, 0.8, 16).translate([nc, run + 1.6, 9.79]).transform(
                    np.array([[1.0, 0, 0, 0], [0, 0, 1.0, 0], [0, 1.0, 0, 0]]))
        else:
            newel = newel + M.hull_points([(x, 9.79, w) for x in (nc - 1.9, nc + 1.9) for w in (run - 0.3, run + 3.5)] +
                                          [(nc, 12.0, run + 1.6)])
        parts.append(newel)
    return union(parts)


def pediment(H):
    """The Laurel's pediment over its bay: a triangle with a raking cornice and a round
    oculus, standing on the cornice. Built lying on its back (prints face-up); returns
    (solid in (u, v, w), half-width)."""
    hw, rise = 18.0, 10.4
    tri = poly([(-hw, 0.0), (hw, 0.0), (0.0, rise)])
    body = ext(tri, -2.4, 0.0)
    rim = tri - tri.offset(-1.0)
    body = body + ext(rim, -0.01, 0.6) + ext(rect(-hw, 0.0, hw, 1.0), -0.01, 0.6)
    c = (0.0, rise * 0.4)
    body = body + ext(circle(c, 2.6, 32) - circle(c, 1.8, 32), -0.01, 0.6) - ext(circle(c, 1.8, 32), -0.6, 1.0)
    return body, hw


# ------------------------------------------------------------------ cornice profiles (heights from the top: rings print upside down)
EAVE_L = [(-4.4, 0), (1.0, 0), (1.0, 4.6), (1.4, 4.8), (1.4, 5.2), (6.2, 5.2), (6.2, 6.4), (6.6, 6.6), (6.8, 7.0),
          (6.8, 7.8), (-4.4, 7.8)]
EAVE_M = [(-4.4, 0), (0.8, 0), (0.8, 5.8), (1.2, 6.0), (5.4, 6.0), (5.4, 7.2), (5.8, 7.6), (5.8, 8.4), (-4.4, 8.4)]


def _door_frame(H, w=0.0, z=0.0):
    main = H["main"]
    e, u = main.locate(H["door_x"], 0.0)
    f = main.facades()[e]
    A = f.A.copy()
    A[:, 3] = f.world(u, z - ZF, w)
    return A


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    blocks_all = [b for H in HALVES for b in (H["main"], H["bay"])]
    fnd = foundation(blocks_all, 0.0, ZF, style="panelled")
    kit.add("FOUNDATION", "Stone", fnd, group="foundation")
    for H in HALVES:
        tg, keep = H["tag"], H["keep"]
        blocks = [H["main"], H["bay"]]
        party = H["party"]

        def siding(f, b, reg, H=H):
            if abs(f.p0[0] - party) < 0.05 and abs(f.p1[0] - party) < 0.05:
                return M()
            reg = reg - rect(-1, ZE - b.z0, f.L + 1, ZC - b.z0)          # nothing behind the frieze band
            return H["siding"](reg, datum=0.0)
        hcs = cs_union([b.cs for b in blocks])
        undress = [slab(offset(hcs, 8.0), ZE - LEDGE - 0.6, ZC + 0.01)]
        st = stacked_shells(blocks, H["openings"], [S1], t=3.0, corners=H["corners"], siding=siding,
                            prof=CO.joint_profile(RJ, LEDGE), belt_blocks=None, water_table=False, hide_extra=keep,
                            undress=undress)
        # colonnettes on the bay's two outer corners, a storey each
        cols1, cols2 = [], []
        for k in (2, 3):
            p = np.array(H["bay"].pts[k])
            sup = (lambda hh: corinthian(hh, 0.9)) if tg == "L" else (lambda hh: fluted(hh, 0.9))
            cols1.append(sup(S1 - ZF).translate([p[0], p[1], ZF]))
            cols2.append(sup(ZE - LEDGE - 0.6 - S1 - RH).translate([p[0], p[1], S1 + RH]))
        canopy, land = portico_canopy(H)
        Ad = _door_frame(H, z=ZF)
        walls1 = st["shells"][0] + union(cols1) - land.transform(Ad)
        kit.add(f"{tg}-WALLS-1", H["wall"], walls1, group=f"walls-{tg}")
        kit.add(f"{tg}-JOINT", H["wall"], st["rings"][0] - keep, group=f"walls-{tg}")
        H["outline"] = st["outlines"][0]
        H["walls1"] = walls1
        H["walls2"] = st["shells"][1] + union(cols2) + (CO.ledge(H["outline"], ZE, LEDGE) - keep)
        kgrow = keep.translate([-0.1 if tg == "L" else 0.1, 0, 0])      # rings stop at the party wall
        for lvl, z0, spec in (("J", S1 + LEDGE + 0.4, JOINTS[tg]), ("F", ZE, FRIEZES[tg])):
            rings, _ = CO.level(H["outline"], z0, spec, cut=kgrow)
            for r_ in rings:
                kit.add(f"{tg}-CORNICE-{lvl}-{r_['name']}", r_["role"], r_["solid"], P=print_flip() if r_["flip"] else None,
                        group=f"cornice-{tg}")
        for o in H["openings"]:
            A = o.local_frame()
            sp = o.spec
            b = sp["cut"].bounds()
            key = "DOOR" if o.kind == "door" else "WIN"
            world, P, zones = O.place(sp, A, "Windows_Doors", "Door" if o.kind == "door" else "Windows_Doors", "Glass")
            kit.add(f"{key}-{o.name}", "Windows_Doors", world, P=P, key=f"{key}-{tg}-{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}",
                    group=f"inserts-{tg}", render=zones)
    print("walls + inserts", round(time.time() - t0, 1))

    for H in HALVES:
        tg, keep, X = H["tag"], H["keep"], H["X"]
        outline = [tuple(p) for p in H["outline"]]
        party = H["party"]
        skip = lambda p: abs(p[0] - party) < 3.0
        if tg == "L":
            eave = R.bracketed_cornice(outline, ZC, EAVE_L,
                                       brackets=dict(z_top=5.2, h=5.2, d0=1.0, d=4.8, t=1.0, pitch=7.0, pair=2.2, margin=3.0,
                                                     style="acanthus", skip=skip),
                                       dents=dict(z=4.4, h=0.8, d0=1.0, d=0.6), deck=(6.6, 7.8))
            ztop = ZC + EAVE_L[-1][1]
        else:
            eave = R.bracketed_cornice(outline, ZC, EAVE_M,
                                       brackets=dict(z_top=6.0, h=6.0, d0=0.8, d=4.4, t=1.8, pitch=8.0, margin=3.0,
                                                     style="twin", skip=skip),
                                       deck=(7.2, 8.4))
            ztop = ZC + EAVE_M[-1][1]
        cx, cy = H["chim"]
        pocket = box([cx - 7.0, cy - 5.6, ztop - 0.6], [cx + 7.0, cy + 5.6, ztop + 1])
        eave = eave - keep - pocket - H["walls2"]
        # printed upside down, the first 0.8 mm are the roof deck and the fascia's top fillet:
        # a filament change there gives a dark roof over a trim-coloured cornice
        deck = eave ^ slab(poly(outline).offset(20.0), ztop - 0.8, ztop + 1)
        kit.add(f"{tg}-EAVE-roof", H["trim"], eave, P=print_flip(), group=f"roof-{tg}",
                render=[("Slate", deck), (H["trim"], eave - deck)])
        ch = TW.chimney(H["chimney"], w=13.2, d=10.4, h=22.0).translate([cx, cy, ztop - 0.6])
        kit.add(f"{tg}-CHIMNEY", "Brick" if tg == "M" else "Stone", ch, group=f"roof-{tg}")
        # the pediment (Laurel) or the cresting (Myrtle) over the front
        Q = [np.array(p) for p in H["bay"].pts]
        if tg == "L":
            ped, hw = pediment(H)
            dep = EAVE_L[-3][0]                                         # the cornice's projection
            mc = (Q[2] + Q[3]) / 2
            Ap = np.array([[1.0, 0, 0, mc[0]], [0, 0, -1.0, mc[1] - dep + 2.4], [0, 1.0, 0, ztop]])
            kit.add("L-PEDIMENT", "Gold", ped.transform(Ap), P=inv34(Ap), group="roof-L")
        else:
            # fleur-de-lis cresting strips standing just inside the fascia along the front
            ring = poly(outline).offset(EAVE_M[-3][0] - 0.8, JoinType.Miter, 4.0)
            P_ = [np.array(p) for p in max(ring.to_polygons(), key=len)]
            if poly([tuple(p) for p in P_]).area() < 0:
                P_ = P_[::-1]
            for k in range(len(P_)):
                a, b = P_[k], P_[(k + 1) % len(P_)]
                if (a[1] + b[1]) / 2 > 0.0:
                    continue
                a = a.copy()
                b = b.copy()
                for q in (a, b):
                    q[0] = max(q[0], party + 0.6)
                tt = (b - a) / max(np.linalg.norm(b - a), 1e-9)
                L_ = float(np.linalg.norm(b - a)) - 1.2
                if L_ < 8.0:
                    continue
                n = np.array([tt[1], -tt[0]])
                o = a + tt * 0.6
                fence = R.crest_fence(L_, 3.6, 1.8, bar=0.6, t=0.8, style="fleur")
                A = np.array([[tt[0], 0.0, n[0], o[0]], [tt[1], 0.0, n[1], o[1]], [0.0, 1.0, 0.0, ztop]])
                kit.add(f"M-CRESTING-{k}", "Iron", fence.transform(A), P=inv34(A), group="roof-M")
        kit.add(f"{tg}-WALLS-2", H["wall"], H["walls2"], group=f"walls-{tg}")
    print("roof", round(time.time() - t0, 1))

    for H in HALVES:
        tg = H["tag"]
        Ad = _door_frame(H, z=ZF)
        canopy, _ = portico_canopy(H)
        kit.add(f"{tg}-PORTICO", H["trim"], canopy.transform(Ad), P=inv34(Ad), group=f"portico-{tg}")
        for sg in (-1, 1):
            if tg == "L":
                col = corinthian(PH, 1.1)
            else:
                col = fluted(PH, 1.4, square=True)
            Ac = Ad.copy()
            Ac[:, 3] = Ad[:, 3] + Ad[:, 0] * sg * UC + Ad[:, 2] * 6.0
            Acol = np.array([[1.0, 0, 0, Ac[0, 3]], [0, 1.0, 0, Ac[1, 3]], [0, 0, 1.0, Ac[2, 3]]])
            kit.add(f"{tg}-COLUMN-{'ab'[sg > 0]}", H["trim"], col.transform(Acol), key=f"{tg}-COLUMN", group=f"portico-{tg}")
        if tg == "M":
            Ar = Ad.copy()
            Ar[:, 3] = Ad[:, 3] + Ad[:, 1] * (PH + 5.0)
            kit.add("M-PORTICO-rail", "Forest", portico_rail(H).transform(Ar), group="portico-M")
        sw = stoop(H).transform(_door_frame(H, z=0.0))
        door = next(p.solid for p in kit.parts if p.name == f"DOOR-{tg}-door")
        kit.add(f"{tg}-STOOP", "Stone", sw - fnd - H["walls1"] - door, group=f"stoop-{tg}")
        # a plain flight down from the back door
        e, u = H["main"].locate(H["X"](44.0), D)
        f = H["main"].facades()[e]
        A = f.A.copy()
        A[:, 3] = f.world(u, -ZF, 0.0)
        kit.add(f"{tg}-STOOP-back", "Stone", FT.steps(10.0, ZF - 0.2, 8, tread=2.2, cheek=1.2).transform(A) - fnd - H["walls1"],
                group=f"stoop-{tg}")
    # iron area railings in front of the bays: a front run to the stoop and a return to the house
    FY = -26.0
    for H in HALVES:
        tg = H["tag"]
        if tg == "L":
            runs = [((0.0, FY), (1.0, 0.0), H["door_x"] - SW - CHEEK - 0.4), ((0.0, FY), (0.0, 1.0), -1.8 - FY)]
        else:
            x_in = H["door_x"] + SW + CHEEK + 0.4
            runs = [((x_in, FY), (1.0, 0.0), 2 * HW - x_in), ((2 * HW, -1.8), (0.0, -1.0), -1.8 - FY)]
        for k, ((x, y), (ux, uy), L_) in enumerate(runs):
            A = np.array([[ux, 0.0, uy, x], [uy, 0.0, -ux, y], [0.0, 1.0, 0.0, 0.0]])
            kit.add(f"{tg}-RAILING-{k}", "Iron", EX.iron_fence(L_).transform(A), P=inv34(A), group=f"extras-{tg}")
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "twins")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:40]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "twins.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))

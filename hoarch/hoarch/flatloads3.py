"""Flatcar loads, third series: made for the 0.2 mm nozzle at 0.10 mm layers (LOADS_BATCH3.md, and
NOTES.md "Fine-nozzle loads"). Same rules as the first two series: pieces in their colours with at
most one change, no supports, no weak connections, nothing floating; every glue joint a peg, a
socket or a flat face. Detail goes down to 0.4 mm. Local z is up from the bed; HO sizes.

Each load's scene (its stand-in car with the load on it, for the renders) is in SCENES at the
bottom; the pack entries are in hoarch.loads3."""
import math

import numpy as np
from manifold3d import CrossSection as CS, JoinType, Manifold as M

from .core import box, circle, cs_union, ft, inch, poly, union
from . import flatloads as F
from .flatloads2 import along_x, along_y, keel, solid, _place
from .locoengine import bolt_x, bolt_y, bolt_z, cyl_x, ext_z, rrect, tear

S2 = math.sqrt(2.0)


def ring(r0, r1, z0, z1, seg=96):
    return M.cylinder(z1 - z0, r1, r1, seg).translate([0, 0, z0]) - M.cylinder(z1 - z0 + 0.02, r0, r0, seg).translate([0, 0, z0 - 0.01])


def sector(r0, r1, a0, a1, n=24):
    """An annular sector in the xy plane between angles a0 and a1 (radians)."""
    ts = np.linspace(a0, a1, n)
    pts = [(r1 * math.cos(t), r1 * math.sin(t)) for t in ts] + [(r0 * math.cos(t), r0 * math.sin(t)) for t in ts[::-1]]
    return poly(pts)


def hexnut(x, y, z, r, h):
    return M.cylinder(h, r, r, 6).translate([x, y, z])


# ================================================================== 1. steam locomotive drivers
DR_R = inch(31.5)            # 63 in drivers (a heavy Mikado): 9.17 mm over the tread
DR_TIRE = 0.95               # tire, radially
DR_W = 1.8                   # tread width: the tire's outer face stands this high off the bed
DR_CHANGE = 1.6              # black wheel centre; tire face, hub face and crank pin silver above this
DR_CRANK = inch(15)          # 30 in stroke
DR_B2B = inch(53.375)        # back to back of the wheels
DR_SOCK_R, DR_SOCK_D = 1.55, 1.6
DR_SEAT_R, DR_SEAT_L = 1.45, 1.5
DR_AX_UP = 1.0               # the axle's flat is this far under its centre line
DR_ZC = 10.4                 # axle centre above the deck on the cradles
DR_PITCH = 22.5              # driver sets along the car
DR_YJ = DR_B2B / 2 - 1.92    # journal centre lines
ROD_PALLET = 1.8             # rod pallet's deck top: brown below, the rods silver above


def driver_wheel(main=False):
    """One driver, printed flat on its inner face: tire and flange, sixteen spokes rounded on their
    outer faces, the crescent counterweight with its lead plugs, hub, crank boss and crank pin (the
    main drivers' bigger, with the return crank). The axle seat is a socket in the inner face."""
    R = DR_R
    rin = R - DR_TIRE
    parts = [ring(rin, R, 0.0, DR_W, 160),                                          # tire
             ring(rin, R + 0.35, 0.0, 0.25, 160),                                    # flange
             M.cylinder(0.35, R + 0.35, R, 160).translate([0, 0, 0.249]) - M.cylinder(0.4, rin, rin, 160).translate([0, 0, 0.2]),
             ring(R - 1.45, rin + 0.01, 0.0, 1.5, 160)]                              # wheel centre's rim
    r0, r1 = 2.3, R - 1.4
    for k in range(16):                                                             # spokes
        t = 2 * math.pi * (k + 0.5) / 16
        c, s = math.cos(t), math.sin(t)

        def quad(w0, w1):
            return poly([(r0 * c - w0 * s, r0 * s + w0 * c), (r1 * c - w1 * s, r1 * s + w1 * c),
                         (r1 * c + w1 * s, r1 * s - w1 * c), (r0 * c + w0 * s, r0 * s - w0 * c)])
        parts.append(M.hull(union([ext_z(quad(0.42, 0.29), 0.0, 0.55), ext_z(quad(0.25, 0.17), 0.99, 1.0)])))
    tc = math.pi                                                                    # counterweight, opposite the crank
    half = math.radians(64 if main else 56)
    cw = sector(2.4, R - 1.42, tc - half, tc + half, 40)
    parts.append(ext_z(cw, 0.0, 1.2))
    parts.append(ext_z(cw.offset(-0.25, JoinType.Round), 1.19, 1.45))
    rp = (2.4 + R - 1.42) / 2
    for dt in (-0.42, 0.0, 0.42):
        parts.append(M.cylinder(0.14, 0.38, 0.38, 20).translate([rp * math.cos(tc + dt), rp * math.sin(tc + dt), 1.44]))
    parts += [M.cylinder(2.1, 2.5, 2.5, 64), M.cylinder(0.3, 2.5, 2.2, 64).translate([0, 0, 2.099])]   # hub
    boss = cs_union([circle((0, 0), 2.3, 48), circle((DR_CRANK, 0), 1.75, 48)]).hull()
    parts.append(ext_z(boss, 0.0, 1.5))
    rp_ = 1.25 if main else 1.05
    top = 3.9 if main else 3.5
    parts += [M.cylinder(0.31, rp_ + 0.3, rp_ + 0.3, 40).translate([DR_CRANK, 0, 1.49]),       # crank pin collar
              M.cylinder(top - 1.79, rp_, rp_, 40).translate([DR_CRANK, 0, 1.79])]
    if main:                                                                        # return crank, its underside at 45
        a = math.radians(100)
        ex, ey = DR_CRANK + 1.9 * math.cos(a), 1.9 * math.sin(a)
        arm = M.hull(union([M.cylinder(1.75, 1.25, 1.25, 32).translate([DR_CRANK, 0, top - 1.75]),
                            M.cylinder(0.5, 0.62, 0.62, 24).translate([ex, ey, top - 0.5])]))
        parts += [arm, M.cylinder(0.8, 0.45, 0.45, 20).translate([ex, ey, top - 0.01])]
    else:
        parts.append(hexnut(DR_CRANK, 0, top - 0.01, 0.85, 0.35))
    m = union(parts)
    return m - M.cylinder(DR_SOCK_D + 0.01, DR_SOCK_R, DR_SOCK_R, 48).translate([0, 0, -0.01])


@solid
def driver():
    return driver_wheel(False)


@solid
def main_driver():
    return driver_wheel(True)


@solid
def driver_axle():
    """A driving axle lying along x on its flat (cut DR_AX_UP under its centre): wheel seats at both
    ends into the drivers' sockets, journals with their collars, the body between."""
    zc = DR_AX_UP
    L = DR_B2B + 2 * DR_SEAT_L
    a, b = DR_SEAT_L, DR_SEAT_L + DR_B2B
    parts = [cyl_x(0.0, a + 0.01, 0, zc, DR_SEAT_R, 48), cyl_x(b - 0.01, L, 0, zc, DR_SEAT_R, 48),
             cyl_x(a, b, 0, zc, 1.35, 48)]
    for x0, x1, r in ((a, a + 0.35, 1.95), (a + 0.25, a + 3.6, 1.65), (a + 3.6, a + 3.95, 1.95)):
        parts.append(cyl_x(x0, x1, 0, zc, r, 56))
        parts.append(cyl_x(L - x1, L - x0, 0, zc, r, 56))
    m = union(parts)
    return m ^ box([-1, -5, 0.0], [L + 1, 5, 5])


@solid
def driver_cradle(n=4):
    """Cribbing for n driver sets, one piece: two runners under the journals, spacers between them,
    and at each set a two-timber block either side with wedges, its top where the journal's flat sits."""
    zt = DR_ZC - DR_AX_UP
    x0, x1 = -DR_PITCH / 2, (n - 0.5) * DR_PITCH
    parts = []
    for y in (-DR_YJ, DR_YJ):
        parts.append(box([x0, y - 1.3, 0.0], [x1, y + 1.3, 2.8]))
    for k in range(n + 1):
        x = x0 + k * DR_PITCH
        x = min(max(x, x0 + 1.2), x1 - 1.2)
        parts.append(box([x - 1.2, -DR_YJ + 1.29, 0.0], [x + 1.2, DR_YJ - 1.29, 2.4]))
    for i in range(n):
        xc = i * DR_PITCH
        for y in (-DR_YJ, DR_YJ):
            parts.append(box([xc - 2.5, y - 1.3, 2.79], [xc + 2.5, y + 1.3, 6.1]))
            parts.append(box([xc - 2.4, y - 1.2, 6.09], [xc + 2.4, y + 1.2, zt]))
            for d in (-1, 1):                                                       # wedges against the journal
                xa, xb = xc + d * 1.75, xc + d * 2.35
                parts.append(along_y(poly([(xa, zt - 0.01), (xb, zt - 0.01), (xb, zt + 0.8)]), y - 1.0, y + 1.0))
    m = union(parts)
    grooves = []
    for i in range(n):                                                              # the joint between the two timbers
        xc = i * DR_PITCH
        for y in (-DR_YJ, DR_YJ):
            for d in (-1, 1):
                grooves.append(box([xc + d * 2.5 - 0.1, y - 1.4, 4.4], [xc + d * 2.5 + 0.1, y + 1.4, 4.55]))
    return m - union(grooves)


def _rod(x0, x1, w0, w1, t, z0, flute=True):
    """A rod body from x0 to x1, tapering from w0 to w1 wide, t thick, fluted on top."""
    body = ext_z(poly([(x0, -w0 / 2), (x1, -w1 / 2), (x1, w1 / 2), (x0, w0 / 2)]), z0, z0 + t)
    if not flute:
        return body
    f = ext_z(poly([(x0 + 1.2, -w0 / 2 + 0.42), (x1 - 1.2, -w1 / 2 + 0.38), (x1 - 1.2, w1 / 2 - 0.38),
                    (x0 + 1.2, w0 / 2 - 0.42)]), z0 + t - 0.3, z0 + t + 0.1)
    return body - f


def _eye(x, r, rb, z0, t):
    return ext_z(circle((x, 0), r, 48), z0, z0 + t) - ext_z(circle((x, 0), rb, 32), z0 - 0.1, z0 + t + 0.1) \
        + ext_z(circle((x, 0), rb + 0.3, 32) - circle((x, 0), rb, 32), z0 + t - 0.01, z0 + t + 0.15)


def main_rod(z0):
    L = 41.0
    big = ext_z(rrect(-2.4, -2.1, 2.4, 2.1, 0.6), z0, z0 + 1.3)
    big = big - ext_z(circle((0, 0), 1.3, 40), z0 - 0.1, z0 + 1.4)
    big = big + ext_z(circle((0, 0), 1.6, 40) - circle((0, 0), 1.3, 40), z0 + 1.29, z0 + 1.45)   # brass
    parts = [big, _rod(2.2, L - 1.2, 2.3, 1.5, 1.1, z0), _eye(L, 1.45, 0.65, z0, 1.1)]
    for y in (-1.45, 1.45):
        parts.append(hexnut(-1.7, y, z0 + 1.29, 0.32, 0.25))
    return union(parts)


def side_rod(span, n_eyes, z0):
    parts = []
    xs = [k * span for k in range(n_eyes)]
    for x in xs:
        parts.append(_eye(x, 1.55, 0.75, z0, 1.0))
    for a, b in zip(xs[:-1], xs[1:]):
        parts.append(_rod(a + 1.2, b - 1.2, 1.45, 1.45, 1.0, z0))
    return union(parts)


@solid
def rod_pallet():
    """Both sides' rods banded to a pallet: the main rods and the side rods (a short and a long
    section each side), every eye bushed in brass and every rod fluted. Pallet brown, rods silver."""
    z0 = ROD_PALLET
    S = 19.3                                                                         # driver spacing, 5 ft 6 in
    parts = []
    xL = -3.0
    for y in (-11.0, -5.5, 0.0, 5.5, 11.0):                                          # stringers
        parts.append(box([xL, y - 0.9, 0.0], [44.0, y + 0.9, 1.21]))
    for x in np.arange(xL + 1.0, 44.0, 2.6):                                         # deck boards
        parts.append(box([x - 1.0, -13.4, 1.2], [x + 1.0, 13.4, z0]))
    rods = [main_rod(z0).translate([0.0, -10.4, 0]), main_rod(z0).translate([0.0, 10.4, 0]),
            side_rod(S, 2, z0).translate([1.5, -5.6, 0]), side_rod(S, 2, z0).translate([1.5, 5.6, 0]),
            side_rod(S, 3, z0).translate([1.5, -1.6, 0]), side_rod(S, 3, z0).translate([1.5, 1.6, 0])]
    parts += rods
    for x in (6.0, 30.0):                                                            # steel bands over the rods
        parts.append(box([x - 0.3, -13.4, z0 - 0.01], [x + 0.3, 13.4, z0 + 0.15]))
    return union(parts)


def scene_drivers():
    L = ft(50.0)
    s = F._car(L, "car_oxide")
    zd = F.deck()
    n = 4
    xs0 = 18.0
    cr = driver_cradle(n)
    F._put(s, "Cocoa Brown", cr.translate([xs0, 0, zd]))
    w, wm = driver(), main_driver()
    ax = driver_axle()
    zc = zd + DR_ZC
    for i in range(n):
        x = xs0 + i * DR_PITCH
        wheel = wm if i == 2 else w
        for side, phi in ((1, 0.0), (-1, 90.0)):                                     # right leads left by 90 degrees
            wv = wheel.rotate([0, 0, phi + 35.0 * i])
            hi, lo = wv.split_by_plane((0.0, 0.0, 1.0), DR_CHANGE + 1e-3)
            for col, part in (("Black", lo), ("Silver", hi)):
                p = part.rotate([-90, 0, 0]) if side > 0 else part.rotate([90, 0, 0])
                F._put(s, col, p.translate([x, side * DR_B2B / 2, zc]))
        a = ax.translate([-(DR_B2B / 2 + DR_SEAT_L), 0, -DR_AX_UP]).rotate([0, 0, 90])
        F._put(s, "Iron Gray Metallic", a.translate([x, 0, zc]))
    rp = rod_pallet()
    hi, lo = rp.split_by_plane((0.0, 0.0, 1.0), ROD_PALLET + 1e-3)
    xr = xs0 + (n - 0.5) * DR_PITCH + 6.0
    F._put(s, "Cocoa Brown", lo.translate([xr + 3.0, 0, zd]))
    F._put(s, "Silver", hi.translate([xr + 3.0, 0, zd]))
    return s


# ================================================================== 2. truck side frames and bolsters
SF_T, SF_WEB = 1.6, 0.7      # side frame: rim depth (its thickness lying flat) and web
SF_DUN = 1.2                 # dunnage top: brown below, black castings above
BOL_T = 3.4                  # bolster width (its thickness lying on its side)


def _side_frame_profile():
    """A 70-ton cast side frame's outline and openings (u along it, v up), HO mm: the top member,
    pedestal jaws open at the bottom for the bearing adapters, the tension member sloping down to the
    spring seat, the bolster window and two lightening openings each side."""
    half = [(0.0, 10.4), (4.0, 10.4), (12.6, 9.75), (13.3, 9.4), (13.3, 6.9), (12.9, 6.5), (11.6, 6.5), (11.6, 9.25),
            (8.3, 9.25), (8.3, 6.5), (6.9, 6.5), (4.6, 4.0), (0.0, 4.0)]
    pts = half + [(-u, v) for (u, v) in reversed(half[1:-1])]
    outline = poly(pts)
    window = rrect(-3.6, 5.3, 3.6, 9.1, 0.5)
    holes = [window]
    for sgn in (-1, 1):
        tri = poly([(sgn * 5.15, 8.85), (sgn * 6.65, 8.85), (sgn * 5.15, 7.25)])
        holes.append(tri.offset(0.15, JoinType.Round).offset(-0.15, JoinType.Round))
    return outline, cs_union(holes)


def side_frame(covered=False):
    """One side frame lying flat on its inner face: a 0.7 mm web with a 1.6 mm rim round the outline
    and every opening, friction-wedge column guides, brake hanger lugs, wear plates in the jaws,
    and the foundry's pattern plate. ``covered``: another frame lies on it, so its web is filled to
    the rims (the pocket would be sealed into a void)."""
    outline, holes = _side_frame_profile()
    web = ext_z(outline - holes, 0.0, SF_T if covered else SF_WEB)
    rim_cs = (outline - outline.offset(-0.5, JoinType.Miter)) + (holes.offset(0.45, JoinType.Round) - holes)
    rim = ext_z(rim_cs - holes, 0.0, SF_T)
    parts = [web, rim]
    for sgn in (-1, 1):
        parts.append(ext_z(poly([(sgn * 3.6, 5.6), (sgn * 4.4, 5.6), (sgn * 4.4, 8.8), (sgn * 3.6, 8.8)]), SF_WEB - 0.01, SF_T - 0.2))
        parts.append(ext_z(circle((sgn * 4.6, 9.6), 0.38, 20), SF_WEB - 0.01, SF_T + 0.15))   # brake hanger lugs
        for u0, u1 in ((8.3, 8.65), (11.25, 11.6)):                                       # jaw wear plates
            a, b = sorted((sgn * u0, sgn * u1))
            parts.append(ext_z(poly([(a, 6.5), (b, 6.5), (b, 9.25), (a, 9.25)]), 0.0, SF_T))
    parts.append(ext_z(rrect(-1.6, 4.45, 1.6, 4.95, 0.15), SF_WEB - 0.01, SF_WEB + 0.25))      # pattern plate
    return union(parts)


@solid
def side_frame_stacks(n=4):
    """Two stacks of n side frames on three dunnage strips, one piece: each frame on the rims of the
    one under it, the stacks a little out of line, as a foundry loads them."""
    parts = []
    for u in (-9.8, 0.0, 9.8):
        parts.append(box([u - 1.2, -8.4, 0.0], [u + 1.2, 8.4, SF_DUN]))
    sf, sfc = side_frame(), side_frame(covered=True)
    for j, yc in enumerate((-3.6, 3.6)):                                             # frame v runs 4.0 to 10.4
        for k in range(n):
            f0 = sfc if k < n - 1 else sf
            f = f0.mirror([1, 0, 0]) if (k + j) % 2 else f0
            du = (0.25, -0.2, 0.3, -0.1)[k % 4]
            parts.append(f.translate([du, yc - 7.2, SF_DUN - 0.01 + k * (SF_T - 0.01)]))
    return union(parts)


def bolster(pockets=True):
    """A truck bolster lying on its side: fish belly, centre plate with its bowl, side bearings,
    the gibs at the ends, spring-seat lugs under the ends, and two lightening pockets on the face."""
    half = [(0.0, 0.0), (4.5, 0.0), (9.9, 1.25), (14.3, 1.25), (14.3, 2.65), (0.0, 2.65)]
    outline = poly(half + [(-u, v) for (u, v) in reversed(half[1:-1])])
    parts = [ext_z(outline, 0.0, BOL_T)]
    parts.append(ext_z(poly([(-2.0, 2.64), (2.0, 2.64), (2.0, 2.95), (-2.0, 2.95)]), 0.0, BOL_T))   # centre plate rim
    for sgn in (-1, 1):
        parts.append(ext_z(poly([(sgn * 5.5, 2.64), (sgn * 6.7, 2.64), (sgn * 6.7, 3.25), (sgn * 5.5, 3.25)]), 0.0, BOL_T))
        for u0 in (9.95, 11.5):                                                          # gibs
            a, b = sorted((sgn * u0, sgn * (u0 + 0.45)))
            parts.append(ext_z(poly([(a, 2.64), (b, 2.64), (b, 3.0), (a, 3.0)]), 0.0, BOL_T))
        a, b = sorted((sgn * 12.0, sgn * 13.6))                                           # spring seat lugs
        parts.append(ext_z(poly([(a, 0.95), (b, 0.95), (b, 1.26), (a, 1.26)]), 0.0, BOL_T))
    m = union(parts)
    cuts = [ext_z(poly([(-1.0, 2.66), (1.0, 2.66), (1.0, 3.0), (-1.0, 3.0)]), 0.6, BOL_T - 0.6)]   # bowl
    for sgn in (-1, 1) if pockets else ():                                               # pockets on the upper face
        pocket = poly([(sgn * u, v) for (u, v) in ((1.6, 0.55), (4.5, 0.55), (8.3, 1.45), (8.3, 2.1), (1.6, 2.1))])
        cuts.append(ext_z(pocket, BOL_T - 0.35, BOL_T + 0.1))
    return m - union(cuts)


@solid
def bolster_bundle(n=4):
    """Two layers of n bolsters lying on their sides on three dunnage strips."""
    parts = []
    w = 3.45
    for u in (-10.5, 0.0, 10.5):
        parts.append(box([u - 1.2, -n * w / 2 - 0.6, 0.0], [u + 1.2, n * w / 2 + 0.6, SF_DUN]))
    for layer in range(2):
        b = bolster(pockets=layer == 1)                                                  # the bottom layer's would be sealed
        for k in range(n):
            v = -n * w / 2 + k * w
            bb = b.mirror([1, 0, 0]) if (k + layer) % 2 else b
            parts.append(bb.translate([0.15 * ((k + layer) % 3 - 1), v, SF_DUN - 0.01 + layer * (BOL_T - 0.01)]))
    return union(parts)


def scene_castings():
    L = ft(40.0)
    s = F._car(L, "car_mineral")
    zd = F.deck()
    sf, bb = side_frame_stacks(), bolster_bundle()
    for (x, y) in ((24.0, -8.6), (24.0, 8.6), (56.0, -8.6), (56.0, 8.6)):
        _place(s, sf, "Cocoa Brown", (SF_DUN, "Black"), x, zd, y)
    for (x, y) in ((92.0, -8.0), (92.0, 8.0)):
        _place(s, bb, "Cocoa Brown", (SF_DUN, "Black"), x, zd, y)
    return s


# ================================================================== 3. blowout preventer stack
BOP_FR, BOP_FT = 5.1, 2.0    # 13-5/8 in flange: radius, thickness
BOP_BC, BOP_N = 4.45, 20     # bolt circle, studs
BOP_SKID = 1.4               # skid timbers' top: brown below, black steel above


def studded_flange(z0, nuts=True, studs_up=0.5):
    """An API flange at z0: its disc, twenty studs and their heavy hex nuts on top."""
    parts = [M.cylinder(BOP_FT, BOP_FR, BOP_FR, 96).translate([0, 0, z0])]
    for k in range(BOP_N):
        t = 2 * math.pi * (k + 0.5) / BOP_N
        x, y = BOP_BC * math.cos(t), BOP_BC * math.sin(t)
        if nuts:
            parts.append(hexnut(x, y, z0 + BOP_FT - 0.01, 0.5, 0.55))
        parts.append(M.cylinder(0.55 + studs_up + 0.02, 0.27, 0.27, 12).translate([x, y, z0 + BOP_FT - 0.01]))
    return union(parts)


def stud_ring(z0, h=1.2):
    """Studs standing up from a studded top (no nuts: they come with the next flange)."""
    out = []
    for k in range(BOP_N):
        t = 2 * math.pi * (k + 0.5) / BOP_N
        out.append(M.cylinder(h + 0.01, 0.27, 0.27, 12).translate([BOP_BC * math.cos(t), BOP_BC * math.sin(t), z0 - 0.01]))
    return out


def dished_handwheel(x, y, z, r=1.6, n=4):
    """A gate valve's handwheel on its stem, dished: spokes rise at 45 degrees from the hub to the rim,
    so it prints standing on its stem."""
    parts = [M.cylinder(0.5, 0.45, 0.45, 20).translate([x, y, z])]
    h = r - 0.4
    for k in range(n):
        t = 2 * math.pi * k / n + math.pi / 4
        parts.append(M.hull(union([M.cylinder(0.3, 0.2, 0.2, 10).translate([x, y, z + 0.2]),
                                   M.cylinder(0.3, 0.2, 0.2, 10).translate([x + (r - 0.25) * math.cos(t), y + (r - 0.25) * math.sin(t), z + 0.2 + h])])))
    parts.append(ring(r - 0.38, r, z + 0.2 + h - 0.05, z + 0.2 + h + 0.33, 48).translate([x, y, 0]))
    return union(parts)


def gate_valve(y0, y1, zc, hcr=False):
    """A flanged gate valve along y from y0 to y1 at height zc, its bonnet up, handwheel or
    hydraulic operator on top, standing on its support."""
    ya, yb = sorted((y0, y1))
    parts = [box([-1.5, ya + 0.5, zc - 1.5], [1.5, yb - 0.5, zc + 1.5])]
    for yf in (ya, yb - 0.5):
        parts.append(M.cylinder(0.5, 1.9, 1.9, 40).rotate([-90, 0, 0]).translate([0, yf, zc]))
    ym = (ya + yb) / 2
    parts.append(M.cylinder(2.0, 1.1, 1.1, 32).translate([0, ym, zc + 1.49]))       # bonnet
    parts.append(M.cylinder(0.3, 1.4, 1.4, 32).translate([0, ym, zc + 3.4]))
    if hcr:
        parts.append(M.cylinder(3.0, 1.35, 1.35, 32).translate([0, ym, zc + 3.69]))
        parts.append(M.cylinder(0.4, 0.9, 0.9, 24).translate([0, ym, zc + 6.68]))
    else:
        parts.append(M.cylinder(1.0, 0.3, 0.3, 12).translate([0, ym, zc + 3.69]))   # stem
        parts.append(dished_handwheel(0, ym, zc + 4.6))
    parts.append(box([-1.2, ya, 0.0], [1.2, yb, zc - 1.49]))                           # support, under the flanges too
    return union(parts)


def _ram_level(zc, z_bottom_support=None):
    """One ram's two bonnets and operators either side (along y), centred at height zc."""
    parts = []
    for sgn in (-1, 1):
        y0, y1 = sorted((sgn * 5.0, sgn * 8.6))
        parts.append(box([-4.6, y0, zc - 2.3], [4.6, y1, zc + 2.3]))                 # bonnet
        f0, f1 = sorted((sgn * 4.95, sgn * 5.5))
        parts.append(box([-5.0, f0, zc - 2.6], [5.0, f1, zc + 2.6]))                 # bonnet flange
        for x in (-4.4, -1.5, 1.5, 4.4):
            for z in (zc - 2.3, zc + 2.3):
                parts.append(bolt_y(x, sgn * 5.5, z, sgn, 0.24))
        c0, c1 = sorted((sgn * 8.59, sgn * 13.0))
        parts.append(M.cylinder(c1 - c0, 2.0, 2.0, 48).rotate([-90, 0, 0]).translate([0, c0, zc]))   # operator
        e0, e1 = sorted((sgn * 12.9, sgn * 13.5))
        parts.append(M.cylinder(e1 - e0, 2.25, 2.25, 48).rotate([-90, 0, 0]).translate([0, e0, zc]))  # head
        l0, l1 = sorted((sgn * 13.49, sgn * 15.0))
        parts.append(M.cylinder(l1 - l0, 0.9, 0.9, 24).rotate([-90, 0, 0]).translate([0, l0, zc]))    # lock housing
        n0, n1 = sorted((sgn * 14.99, sgn * 15.4))
        parts.append(M.cylinder(n1 - n0, 0.75, 0.75, 6).rotate([-90, 0, 0]).translate([0, n0, zc]))   # lock nut
        if z_bottom_support is not None:                                             # stands under the bottom level
            parts.append(box([-4.4, y0 + 0.5, z_bottom_support], [4.4, y1 - 0.3, zc - 2.29]))
            k0, k1 = sorted((sgn * 9.6, sgn * 13.5))
            parts.append(along_y(keel(0.0, zc, 2.25, z_bottom_support), k0, k1))   # plate under the operator
    return parts


def ram_bop(levels=2):
    """A ram preventer (double or single), upright on its bottom flange: body with chamfered corners,
    the studded top, each ram's bonnets and operators either side (stacked on a double), and stands
    under the bottom operators."""
    body_h = 6.0 if levels == 1 else 11.0
    zb = BOP_FT
    sec = poly([(-5.6, -4.4), (-5.0, -5.0), (5.0, -5.0), (5.6, -4.4), (5.6, 4.4), (5.0, 5.0), (-5.0, 5.0), (-5.6, 4.4)])
    parts = [studded_flange(0.0), ext_z(sec, zb + 2.3, zb + body_h),
             M.hull(union([M.cylinder(0.01, BOP_FR, BOP_FR, 96).translate([0, 0, zb - 0.01]), ext_z(sec, zb + 2.3, zb + 2.31)]))]
    parts += stud_ring(zb + body_h)
    zcs = [zb + 3.0] if levels == 1 else [zb + 2.8, zb + 7.4]
    for i, zc in enumerate(zcs):
        parts += _ram_level(zc, 0.0 if i == 0 else None)
    if levels == 2:                                                                  # web between the stacked operators
        for sgn in (-1, 1):
            c0, c1 = sorted((sgn * 9.0, sgn * 13.5))
            parts.append(along_y(keel(0.0, zcs[1], 2.0, zcs[0] + 1.9), c0, c1))
    for sgn in (-1, 1) if levels == 2 else ():                                       # side outlets' blind flanges
        x0_, x1_ = sorted((sgn * 5.5, sgn * 6.0))
        zo = zb + body_h / 2
        parts.append(along_x(rrect(-1.3, zo - 1.3, 1.3, zo + 1.3, 0.3), x0_, x1_))      # outlet cover plate
        for dy in (-0.85, 0.85):
            for dz in (-0.85, 0.85):
                parts.append(bolt_x(sgn * 6.0, dy, zo + dz, sgn, 0.2))
    return union(parts)


def annular_bop():
    """An annular preventer upright on its bottom flange: body flaring at 45 degrees from the flange,
    the head bolted on with a ring of cap screws, domed up to the studded top; hydraulic ports and
    lifting eyes."""
    parts = [studded_flange(0.0)]
    plate = ext_z(rrect(-8.0, -8.0, 8.0, 8.0, 1.2), -0.8, 0.01)                     # shipping adapter plate
    parts.append(plate)
    for x in (-6.8, 6.8):
        for y in (-6.8, 6.8):
            parts.append(hexnut(x, y, 0.0, 0.42, 0.35))
    parts.append(M.cylinder(2.5, BOP_FR, 7.6, 96).translate([0, 0, BOP_FT - 0.01]))    # 45 degree flare
    parts.append(M.cylinder(4.4, 7.6, 7.6, 120).translate([0, 0, BOP_FT + 2.48]))
    parts.append(M.cylinder(0.6, 7.9, 7.9, 120).translate([0, 0, BOP_FT + 6.87]))       # head joint
    for k in range(24):
        t = 2 * math.pi * k / 24
        parts.append(hexnut(7.55 * math.cos(t), 7.55 * math.sin(t), BOP_FT + 7.46, 0.32, 0.3))
    parts.append(M.cylinder(2.6, 7.5, 5.4, 120).translate([0, 0, BOP_FT + 7.46]))      # dome
    zt = BOP_FT + 10.05
    parts.append(M.cylinder(1.0, 5.4, 5.4, 96).translate([0, 0, zt]))
    parts += stud_ring(zt + 1.0)
    for t in (0.6, 0.6 + math.pi * 0.5):                                             # hydraulic ports
        parts.append(along_x(tear((0.0, BOP_FT + 5.0), 0.55, 16), 7.3, 8.4).rotate([0, 0, math.degrees(t)]))
    for t in (math.pi / 4, math.pi * 1.25):                                          # lifting eyes on the dome
        x, y = 6.2 * math.cos(t), 6.2 * math.sin(t)
        eye = union([box([-0.5, -1.1, 0.0], [0.5, 1.1, 1.2]), cyl_x(-0.5, 0.5, 0, 1.2, 1.1, 24)])
        eye = eye - cyl_x(-0.6, -0.25, 0, 1.2, 0.45, 16) - cyl_x(0.25, 0.6, 0, 1.2, 0.45, 16)
        parts.append(eye.rotate([0, 0, math.degrees(t) + 90]).translate([x, y, BOP_FT + 8.2]))
    return union(parts).translate([0, 0, 0.8])


def drilling_spool():
    """The drilling spool between the rams, flanged both ends, its choke and kill outlets each with a
    manual gate valve and a hydraulic one, all on supports."""
    parts = [studded_flange(0.0), M.cylinder(6.0, 3.9, 3.9, 80).translate([0, 0, BOP_FT - 0.01]),
             M.cylinder(1.2, 3.9, BOP_FR, 80).translate([0, 0, BOP_FT + 4.79]),                 # shoulder at 45
             M.cylinder(BOP_FT, BOP_FR, BOP_FR, 96).translate([0, 0, BOP_FT + 5.98])]
    parts += stud_ring(2 * BOP_FT + 5.98)
    zc = BOP_FT + 3.0
    for sgn in (-1, 1):
        y0, y1 = sorted((sgn * 3.5, sgn * 5.6))
        parts.append(M.cylinder(y1 - y0, 1.2, 1.2, 32).rotate([-90, 0, 0]).translate([0, y0, zc]))
        f0, f1 = sorted((sgn * 5.5, sgn * 6.1))
        parts.append(M.cylinder(f1 - f0, 1.9, 1.9, 40).rotate([-90, 0, 0]).translate([0, f0, zc]))
        parts.append(gate_valve(sgn * 6.05, sgn * 10.6, zc, hcr=False))
        parts.append(gate_valve(sgn * 10.55, sgn * 15.1, zc, hcr=True))
        parts.append(box([-1.2, min(sgn * 3.8, sgn * 6.1), 0.0], [1.2, max(sgn * 3.8, sgn * 6.1), zc - 1.19]))   # under the outlet
    return union(parts)


@solid
def bop_double():
    return ram_bop(2)


@solid
def bop_single():
    return ram_bop(1)


@solid
def bop_annular():
    return annular_bop()


@solid
def bop_spool():
    return drilling_spool()


BOP_SKID_L, BOP_SKID_W = 124.0, 26.0


@solid
def bop_skid():
    """An oilfield skid: a solid steel deck with channel edges, padeyes at the corners and bolt rows,
    on three timber runners. Timbers brown, steel black."""
    L, W = BOP_SKID_L, BOP_SKID_W
    zt = BOP_SKID
    parts = [box([0.0, y - 1.3, 0.0], [L, y + 1.3, zt]) for y in (-11.0, -5.5, 0.0, 5.5, 11.0)]   # runners
    parts.append(box([0.0, -W / 2, zt - 0.01], [L, W / 2, zt + 2.0]))                  # deck
    for x in (2.5, L - 2.5):                                                           # padeyes
        for y in (-W / 2 + 2.0, W / 2 - 2.0):
            pe = union([box([x - 0.5, y - 1.1, zt + 1.99], [x + 0.5, y + 1.1, zt + 3.0]), cyl_x(x - 0.5, x + 0.5, y, zt + 3.0, 1.1, 24)])
            pe = pe - cyl_x(x - 0.6, x - 0.25, y, zt + 3.0, 0.45, 16) - cyl_x(x + 0.25, x + 0.6, y, zt + 3.0, 0.45, 16)
            parts.append(pe)
    for x in np.arange(4.0, L - 3.0, 4.0):
        for y in (-W / 2 + 0.5, W / 2 - 0.5):
            parts.append(bolt_z(x, y, zt + 2.0, 0.22, 0.2))
    m = union(parts)
    grooves = [box([-0.1, -W / 2 - 0.1, zt + 0.45], [L + 0.1, -W / 2 + 0.3, zt + 1.55]),   # channel webs along the sides
               box([-0.1, W / 2 - 0.3, zt + 0.45], [L + 0.1, W / 2 + 0.1, zt + 1.55]),
               box([-0.1, -W / 2 + 0.8, zt + 0.45], [0.3, W / 2 - 0.8, zt + 1.55]),
               box([L - 0.3, -W / 2 + 0.8, zt + 0.45], [L + 0.1, W / 2 - 0.8, zt + 1.55])]
    return m - union(grooves)


def scene_bop():
    L = ft(40.0)
    s = F._car(L, "car_black")
    zd = F.deck()
    sk = bop_skid()
    x0 = (L - BOP_SKID_L) / 2
    _place(s, sk, "Cocoa Brown", (BOP_SKID, "Black"), L / 2, zd)
    zs = zd + BOP_SKID + 2.0
    xs = [x0 + 10.0, x0 + 36.0, x0 + 70.0, x0 + 104.0]
    for (fn, x) in ((bop_annular, xs[0]), (bop_double, xs[1]), (bop_spool, xs[2]), (bop_single, xs[3])):
        m = fn().rotate([0, 0, 90])                                                  # rams along the car
        b = m.bounding_box()
        F._put(s, "Red", m.translate([x - (b[0] + b[3]) / 2, -(b[1] + b[4]) / 2, zs - b[2]]))
    return s


SCENES = {"drivers": scene_drivers, "castings": scene_castings, "bop": scene_bop}

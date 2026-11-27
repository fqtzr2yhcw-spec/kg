"""Locomotive engine and main generator load, after the 16-cylinder two-stroke engines of the SD40-2
era (generic: no maker's name or plates). Made for a 0.2 mm nozzle at 0.10 mm layers, so the detail
goes down to 0.4 mm: the owner asked for the most realistic load we can print.

Four pieces, each in its own colour with at most one change, glued with pegs and a spigot:

  Skid        timber blocking (Cocoa Brown) under a steel shipping skid (Black), changing at the
              timbers' top. Two wide-flange beams with web stiffeners, cross channels, end
              channels, corner lifting lugs and the engine's locating pegs.
  Engine      (Gray) printed upright on its mounting flange: oil pan with stiffeners, crankcase
              with sixteen inspection doors and their dog handles, the air box with sixteen
              handhole covers, water inlet and discharge manifolds with a collar at every
              cylinder, two banks of eight top-deck covers (hinges, pull, raised panel), the
              exhaust manifold down the V in flanged sections with sixteen exhaust elbows, lifting
              brackets, the accessory end (gear housing with its bolt ring, two water pumps and
              their risers, the lube oil pump, governor, oil strainer) under the turbo support,
              the two aftercoolers, and the flywheel housing with its bolt ring and spigot.
  Turbo       (Iron Gray Metallic) the turbocharger on its pedestal: covered compressor inlet,
              compressor and turbine housings with their keels, discharge stubs to the
              aftercoolers, the turbine inlet against the exhaust manifold, the exhaust stack
              adapter with its covered flange, oil lines.
  Generator   (Black) printed standing on its engine flange: frame bands, mounting rails, the
              covered air inlet on top, lifting lugs, terminal box, screened vents, end bell with
              its bolts, and the companion alternator with cooling ribs and its own terminal box.

Coordinates (HO mm): x along the engine from the block's accessory-end face, y across, z up from
the engine's base (the skid beams' top). Every overhang is 45 degrees or less, or a bridge, or
under 0.5 mm; horizontal pipes are teardrops."""
import math

import numpy as np
from manifold3d import CrossSection as CS, JoinType, Manifold as M

from .core import box, circle, cs_union, ft, poly, union
from . import flatloads as F
from .flatloads2 import along_x, along_y, keel, solid

S2 = math.sqrt(2.0)
T22 = math.tan(math.radians(22.5))

P = 6.42                    # cylinder pitch (22 in)
NC = 8                      # cylinders a bank
END = 1.6                   # block end walls
LB = NC * P + 2 * END       # block length
W2 = 8.9                    # block half width (5 ft 1 in)
ZC = 8.4                    # crankshaft centre above the base
Z_CASE = 4.75               # crankcase from here (the pan flange below)
Z_LEDGE = 10.6              # ledge between the crankcase and the air box
Z_DECK = 15.6               # top deck, outer edge
Y_MAN = 2.7                 # exhaust manifold half width
Z_DECKIN = Z_DECK + (W2 - Y_MAN) * T22
Z_MAN = 21.2                # exhaust manifold top
XA = 3.6                    # accessory gear housing depth
XW = 8.0                    # turbo support front (45 degrees up from the housing)
Z_PLAT = Z_LEDGE + (XW - XA)   # turbo platform
YH = 8.6                    # accessory housing half width
XF = 2.6                    # flywheel housing depth
GEN_X = LB + XF             # generator flange face
ZT = 20.4                   # turbocharger axis
Z_AC = 19.2                 # aftercooler top
X_AC = -6.6                 # aftercooler front
CYL = [END + P * (k + 0.5) for k in range(NC)]

SKID_T = 4.2                # timber top (14 in blocking): the skid's colour change, on the 0.2 and 0.1 grids
SKID_H = 3.0                # skid beams
SKID_Y = 8.0                # beam centre lines
SKID_X0, SKID_X1 = -10.6, GEN_X + 24.6
PEG_R, PEG_H, SOCK_R, SOCK_D = 0.6, 0.9, 0.75, 1.1


# ================================================================== helpers
def tear(c, r, seg=28):
    """A circle with a 45 degree point at the bottom: a horizontal pipe's section that prints."""
    return cs_union([circle(c, r, seg), poly([(c[0] - r / S2, c[1] - r / S2), (c[0] + r / S2, c[1] - r / S2),
                                              (c[0], c[1] - r * S2)])]).hull()


def rrect(u0, v0, u1, v1, r):
    r = min(r, (u1 - u0) / 2 - 0.01, (v1 - v0) / 2 - 0.01)
    return CS.square((u1 - u0 - 2 * r, v1 - v0 - 2 * r)).translate((u0 + r, v0 + r)).offset(r, JoinType.Round, circular_segments=16)


def ext_z(cs, z0, z1):
    return M.extrude(cs, z1 - z0).translate([0, 0, z0])


def cyl_x(x0, x1, y, z, r, seg=40):
    return M.cylinder(x1 - x0, r, r, seg).rotate([0, 90, 0]).translate([x0, y, z])


def bolt_x(x, y, z, d, r=0.28):
    """A hex bolt head on a face looking along x (d = +1 or -1), 0.3 mm proud."""
    h = 0.3
    m = M.cylinder(h + 0.02, r, r, 6).rotate([0, 90, 0])
    return m.translate([x - 0.02 if d > 0 else x - h, y, z])


def bolt_y(x, y, z, d, r=0.28):
    h = 0.3
    m = M.cylinder(h + 0.02, r, r, 6).rotate([-90, 0, 0])
    return m.translate([x, y - 0.02 if d > 0 else y - h, z])


def bolt_z(x, y, z, r=0.3, h=0.3):
    return M.cylinder(h + 0.02, r, r, 6).translate([x, y, z - 0.02])


def zdeck(y):
    """Top deck height at |y| (it falls 22.5 degrees from the manifold to the block's side)."""
    return Z_DECKIN - (abs(y) - Y_MAN) * T22


def mirror_y(ms):
    return [m.mirror([0, 1, 0]) for m in ms]


# ================================================================== engine
def _side(sgn):
    """One side of the block (sgn = +1 or -1): doors, covers, manifolds, ledge details."""
    out = []
    yo = sgn * W2
    for x in CYL:                                                            # crankcase inspection doors
        z0, z1 = 5.6, 9.6
        door = along_y(rrect(x - 2.2, z0, x + 2.2, z1, 0.8), *sorted((yo - sgn * 0.01, yo + sgn * 0.35)))
        out.append(door)
        rim = along_y(rrect(x - 1.8, z0 + 0.4, x + 1.8, z1 - 0.4, 0.6), *sorted((yo + sgn * 0.34, yo + sgn * 0.5)))
        out.append(rim)
        bar = along_x(poly([(yo + sgn * 0.49, 7.25), (yo + sgn * 0.95, 7.71), (yo + sgn * 0.95, 8.05), (yo + sgn * 0.49, 8.05)]),
                      x - 1.5, x + 1.5)                                       # the dog bar, underside sloped
        out.append(bar)
        out.append(along_y(tear((x, 7.75), 0.62, 16), *sorted((yo + sgn * 0.49, yo + sgn * 1.2))))   # its centre boss
        for dx, dz in ((-1.6, z0 + 0.45), (1.6, z0 + 0.45), (-1.6, z1 - 0.45), (1.6, z1 - 0.45)):
            out.append(bolt_y(x + dx, yo + sgn * 0.34, dz, sgn, 0.22))
        za0, za1 = 12.6, 15.25                                               # air box handhole covers
        out.append(along_y(rrect(x - 1.9, za0, x + 1.9, za1, 0.7), *sorted((yo - sgn * 0.01, yo + sgn * 0.3))))
        for dx in (-1.1, 1.1):                                               # clamp handles
            out.append(along_x(poly([(yo + sgn * 0.29, 13.3), (yo + sgn * 0.7, 13.7), (yo + sgn * 0.7, 14.65),
                                     (yo + sgn * 0.29, 14.65)]), x + dx - 0.25, x + dx + 0.25))
        out.append(bolt_y(x, yo + sgn * 0.29, za1 - 0.45, sgn, 0.2))
    for k in range(NC + 1):                                                  # oil pan stiffeners
        x = END + k * P
        out.append(box([x - 0.25, sgn * 8.55, 0.85], [x + 0.25, sgn * 9.0, 3.8]))
    out.append(along_x(poly([(sgn * 8.6, 3.75), (sgn * 9.25, 4.4), (sgn * 9.25, Z_CASE), (sgn * 8.5, Z_CASE), (sgn * 8.5, 3.75)]),
                       0.2, LB - 0.2))                                      # pan to crankcase flange
    for x in np.arange(1.2, LB - 0.6, 1.6):
        out.append(bolt_y(x, sgn * 9.25, 4.6, sgn, 0.2))
    out.append(along_x(poly([(sgn * 8.8, Z_LEDGE - 0.6), (sgn * 9.4, Z_LEDGE), (sgn * 9.4, Z_LEDGE + 0.4),
                             (sgn * 8.8, Z_LEDGE + 0.4)]), 0.0, LB))         # ledge
    yw, zw = sgn * 9.25, 11.8                                                 # water inlet manifold
    out.append(along_x(tear((yw, zw), 0.7), 0.6, LB - 1.0))
    out.append(box([0.6, sgn * 8.85, Z_LEDGE + 0.39], [LB - 1.0, yw, zw]))      # filled to the wall: no pocket under it
    for x in CYL:
        out.append(along_x(tear((yw, zw), 0.92), x - 0.25, x + 0.25))
        out.append(box([x - 0.35, sgn * 8.95, zw + 0.3], [x + 0.35, sgn * 9.4, 12.75]))                # jumper up to the air box
    yd, zd = sgn * 8.55, Z_DECK + 0.55                                       # water discharge manifold
    out.append(along_x(tear((yd, zd), 0.75), 1.4, LB - 0.3))
    for x in CYL:
        out.append(along_x(tear((yd, zd), 0.98), x - 0.25, x + 0.25))
    for x in np.arange(1.0, LB - 0.4, 3.21):                                 # base flange bolts
        out.append(bolt_z(x, sgn * 9.45, 0.9, 0.3))
    return out


def _bank(sgn):
    """One bank's top deck: eight covers with raised panels, hinges and pulls; eight exhaust elbows."""
    out = []
    yi, yo = Y_MAN + 0.25, W2 - 1.65

    def slab(ya, yb, t, xa, xb, lift=0.0):
        pts = [(ya, zdeck(ya) - 0.01 + lift), (yb, zdeck(yb) - 0.01 + lift), (yb, zdeck(yb) + t + lift), (ya, zdeck(ya) + t + lift)]
        m = along_x(poly(pts), xa, xb)
        return m if sgn > 0 else m.mirror([0, 1, 0])

    for x in CYL:
        out.append(slab(yi, yo, 0.7, x - 2.75, x + 2.75))                    # the cover
        out.append(slab(yi + 0.7, yo - 0.7, 0.25, x - 2.05, x + 2.05, 0.69))  # raised panel
        pull = slab(yo - 1.25, yo - 0.45, 0.5, x - 0.8, x + 0.8, 0.69)
        out.append(pull)
        for dx in (-1.6, 1.6):                                               # hinge knuckles at the manifold side
            k = cyl_x(x + dx - 0.55, x + dx + 0.55, yi + 0.4, zdeck(yi + 0.4) + 0.7, 0.33, 16)
            out.append(k if sgn > 0 else k.mirror([0, 1, 0]))
        y0, y1 = Y_MAN + 0.6, Y_MAN + 1.9                                    # exhaust elbow into the manifold
        e = M.hull(union([box([x - 0.95, y0, zdeck(y1) + 0.6], [x + 0.95, y1, zdeck(y1) + 1.45]),
                          box([x - 1.05, Y_MAN - 0.05, Z_DECKIN + 0.7], [x + 1.05, Y_MAN + 0.15, Z_DECKIN + 2.7])]))
        f = box([x - 1.35, Y_MAN - 0.05, Z_DECKIN + 0.55], [x + 1.35, Y_MAN + 0.35, Z_DECKIN + 2.95])
        out += [e, f] if sgn > 0 else mirror_y([e, f])
    return out


def _manifold():
    sec = poly([(-Y_MAN, Z_DECK - 0.01), (Y_MAN, Z_DECK - 0.01), (Y_MAN, Z_MAN - 0.6), (Y_MAN - 0.6, Z_MAN),
                (-Y_MAN + 0.6, Z_MAN), (-Y_MAN, Z_MAN - 0.6)])
    out = [along_x(sec, 1.2, LB - 1.0)]
    band = poly([(-Y_MAN - 0.3, Z_DECK), (Y_MAN + 0.3, Z_DECK), (Y_MAN + 0.3, Z_MAN - 0.45), (Y_MAN - 0.45, Z_MAN + 0.3),
                 (-Y_MAN + 0.45, Z_MAN + 0.3), (-Y_MAN - 0.3, Z_MAN - 0.45)])
    xs = [END + k * P for k in range(1, NC)] + [1.5, LB - 1.3]
    for x in xs:
        out.append(along_x(band, x - 0.3, x + 0.3))
    edges = sorted(xs)
    for a, b in zip(edges[:-1], edges[1:]):                                  # heat shield plates on top
        out.append(box([a + 0.55, -Y_MAN + 0.95, Z_MAN - 0.01], [b - 0.55, Y_MAN - 0.95, Z_MAN + 0.2]))
        for x in (a + 0.95, b - 0.95):
            for y in (-Y_MAN + 1.3, Y_MAN - 1.3):
                out.append(bolt_z(x, y, Z_MAN + 0.2, 0.2, 0.2))
    return out


def _accessory_end():
    out = [box([-XA, -YH, 0.0], [0.01, YH, Z_LEDGE + 0.01])]
    out.append(along_y(poly([(-XA, Z_LEDGE), (0.01, Z_LEDGE), (0.01, Z_PLAT), (-XW, Z_PLAT)]), -YH, YH))   # turbo support
    for y in np.arange(-7.6, 7.7, 1.9):                                      # gear housing bolt ring
        for z in (0.7, Z_LEDGE - 0.5):
            out.append(bolt_x(-XA, y, z, -1, 0.22))
    for z in np.arange(2.6, Z_LEDGE - 1.0, 1.9):
        for y in (-7.9, 7.9):
            out.append(bolt_x(-XA, y, z, -1, 0.22))
    for sgn in (-1, 1):                                                      # water pumps and their risers
        yp, zp = sgn * 5.0, 5.6
        out.append(along_x(tear((yp, zp), 2.5), -XA - 2.0, -XA + 0.01))
        out.append(along_x(tear((yp, zp), 1.1, 20), -XA - 2.8, -XA - 1.99))
        for a in range(6):
            t = math.radians(30 + 60 * a)
            out.append(bolt_x(-XA - 2.0, yp + 1.85 * math.cos(t), zp + 1.85 * math.sin(t), -1, 0.2))
        xr, yr = -XA - 1.0, sgn * 6.3
        out.append(M.cylinder(Z_LEDGE + 2.6 - zp, 0.85, 0.85, 24).translate([xr, yr, zp]))
        out.append(M.cylinder(0.45, 1.1, 1.1, 24).translate([xr, yr, 9.4]))
    out.append(along_x(tear((0.0, 2.9), 1.9), -XA - 1.8, -XA + 0.01))         # lube oil pump
    out.append(along_x(tear((0.0, 2.9), 0.8, 16), -XA - 2.4, -XA - 1.79))
    out.append(M.cylinder(Z_LEDGE + 1.2 - 3.6, 0.7, 0.7, 20).translate([-XA - 0.8, -1.7, 3.6]))
    gov = along_y(poly([(-XA + 0.01, 6.9), (-XA - 1.8, 8.7), (-XA - 1.8, 11.0), (-XA + 0.01, 11.0)]), 0.3, 2.3)   # governor
    out += [gov, M.cylinder(1.2, 0.95, 0.95, 24).translate([-XA - 0.9, 1.3, 10.99]),
            M.cylinder(0.5, 0.45, 0.45, 12).translate([-XA - 0.9, 1.3, 12.18])]
    out.append(along_x(tear((-3.6, 9.3), 0.75, 16), -XA - 1.0, -XA + 0.01))   # overspeed trip
    ys, rs = -(YH + 0.95), 1.6                                               # oil strainer, standing on the bed
    out += [M.cylinder(7.0, rs, rs, 32).translate([-1.8, ys, 0.0]),
            M.cylinder(0.5, rs + 0.3, rs + 0.3, 32).translate([-1.8, ys, 7.0]),
            M.cylinder(0.45, 0.6, 0.6, 12).translate([-1.8, ys, 7.49])]
    for a in range(8):
        t = math.radians(22.5 + 45 * a)
        out.append(bolt_z(-1.8 + 1.55 * math.cos(t), ys + 1.55 * math.sin(t), 7.5, 0.2, 0.2))
    for sgn in (-1, 1):                                                      # aftercoolers either side of the turbo
        y0, y1 = sgn * 4.9, sgn * YH
        ya, yb = sorted((y0, y1))
        out.append(box([X_AC, ya, Z_PLAT - 0.01], [1.4, yb, Z_AC]))
        yc0, yc1 = sorted((y1 - sgn * 0.01, y1 + sgn * 0.4))
        out.append(along_y(rrect(X_AC + 0.6, Z_PLAT + 0.7, 0.8, Z_AC - 0.6, 0.6), yc0, yc1))
        for x in np.linspace(X_AC + 1.0, 0.4, 5):
            for z in (Z_PLAT + 1.05, Z_AC - 0.95):
                out.append(bolt_y(x, y1 + sgn * 0.4, z, sgn, 0.2))
        out.append(along_x(rrect(min(y0, y1) + 0.6, Z_PLAT + 0.7, max(y0, y1) - 0.6, Z_AC - 0.6, 0.5), X_AC - 0.4, X_AC + 0.01))
        for x in (-5.2, -0.6):                                               # water connections on top
            yy = sgn * 6.75
            out += [M.cylinder(1.3, 0.6, 0.6, 20).translate([x, yy, Z_AC - 0.01]), M.cylinder(0.35, 0.85, 0.85, 20).translate([x, yy, Z_AC + 0.9])]
        yy = sgn * 6.75                                                      # lifting eye
        eye = union([box([-3.4, yy - 1.1, Z_AC - 0.01], [-2.4, yy + 1.1, Z_AC + 1.2]), cyl_x(-3.4, -2.4, yy, Z_AC + 1.2, 1.1, 24)])
        for dx in (-0.5, 0.5):
            eye = eye - cyl_x(-2.9 + dx - 0.25, -2.9 + dx + 0.25, yy, Z_AC + 1.2, 0.45, 16)
        out.append(eye)
    seat = union([cyl_x(-9.5, -4.0, 0.0, ZT, 4.62, 64), along_x(keel(0.0, ZT, 4.62, Z_PLAT - 0.5), -9.5, -4.0)])
    for sgn in (-1, 1):                                                      # aftercooler inlets, saddled on the compressor
        ya, yb = sorted((sgn * 3.0, sgn * YH))
        duct = M.hull(union([box([-XW, ya, Z_PLAT - 0.01], [X_AC + 0.01, yb, Z_PLAT + 2.0]),
                             box([-XW + 0.4, ya, Z_PLAT + 2.0], [X_AC + 0.01, yb, Z_AC - 0.4])]))
        out.append(duct - seat)
    for x in (-6.0, -1.6):                                                   # the turbo's locating pegs
        out.append(M.cylinder(PEG_H + 0.01, PEG_R, PEG_R, 20).translate([x, 0.0, Z_PLAT - 0.01]))
    return out


def _flywheel_end():
    def tomb(r):
        return cs_union([circle((0.0, ZC), r, 64), CS.square((2 * r, ZC)).translate((-r, 0.0))]) ^ \
            CS.square((40.0, 40.0)).translate((-20.0, 0.0))
    out = [along_x(tomb(8.2), LB - 0.01, LB + XF), along_x(tomb(8.4), LB + XF - 0.6, LB + XF)]
    for a in range(0, 360, 18):
        t = math.radians(a)
        y, z = 8.15 * math.cos(t), ZC + 8.15 * math.sin(t)
        if z > 0.4:
            out.append(bolt_x(LB + XF - 0.6, y, z, -1, 0.2))
    out.append(along_x(tear((0.0, ZC), 2.4, 32), LB + XF - 0.01, LB + XF + 1.0))   # spigot into the generator
    return out


def _lifting_brackets():
    out = []
    for x in (LB - 0.8,):
        for y in (-5.6, 5.6):
            zb = zdeck(abs(y) + 1.3) - 0.5
            plate = union([box([x - 0.6, y - 1.3, zb], [x + 0.6, y + 1.3, zdeck(abs(y) - 1.3) + 1.6]),
                           cyl_x(x - 0.6, x + 0.6, y, zdeck(abs(y) - 1.3) + 1.6, 1.3, 32)])
            for dx in (-0.6, 0.6):
                eye = cyl_x(x + dx - 0.3, x + dx + 0.3, y, zdeck(abs(y) - 1.3) + 1.6, 0.55, 20)
                plate = plate - eye
            out.append(plate)
    return out


@solid
def engine():
    """The engine in its print pose (upright on its mounting flange, base at z = 0)."""
    parts = [box([0.2, -9.9, 0.0], [LB - 0.2, 9.9, 0.9]),                      # mounting flange
             box([0.4, -8.6, 0.85], [LB - 0.4, 8.6, Z_CASE]),                 # oil pan
             box([0.0, -W2, Z_CASE - 0.01], [LB, W2, Z_DECK]),                 # crankcase and air box
             along_x(poly([(Y_MAN - 0.01, Z_DECK - 0.01), (W2, Z_DECK - 0.01), (W2, Z_DECK), (Y_MAN - 0.01, Z_DECKIN)]), 0.0, LB),
             along_x(poly([(-Y_MAN + 0.01, Z_DECK - 0.01), (-W2, Z_DECK - 0.01), (-W2, Z_DECK), (-Y_MAN + 0.01, Z_DECKIN)]), 0.0, LB)]
    for sgn in (-1, 1):
        parts += _side(sgn) + _bank(sgn)
    parts += _manifold() + _accessory_end() + _flywheel_end() + _lifting_brackets()
    m = union(parts)
    socks = [M.cylinder(SOCK_D, SOCK_R, SOCK_R, 20).translate([x, y, -0.01]) for x in (6.0, LB - 6.0) for y in (-SKID_Y, SKID_Y)]
    return m - union(socks)


# ================================================================== turbocharger
def _turbo_assembled():
    z0 = Z_PLAT
    parts = [box([-7.6, -2.9, z0], [-6.55, 2.9, z0 + 1.2]),                    # pedestal, wide where it can be
             box([-6.55, -4.4, z0], [-0.1, 4.4, z0 + 1.2])]
    for x in (-7.0, -4.6, -2.2, -0.7):
        for y in (-2.65, 2.65):
            parts.append(bolt_z(x, y, z0 + 1.2, 0.22, 0.22))

    def housing(xa, xb, r):
        return union([cyl_x(xa, xb, 0.0, ZT, r, 56), along_x(keel(0.0, ZT, r, z0), xa, xb)])

    parts += [housing(-8.6, -5.0, 4.6),                                       # compressor
              housing(-9.0, -8.59, 3.6),                                      # inlet flange
              housing(-5.01, -3.79, 3.0),                                     # bearing housing
              housing(-3.8, 0.0, 4.2),                                        # turbine
              housing(-4.0, -3.6, 4.5), housing(-0.4, 0.0, 4.5)]              # turbine flanges
    parts.append(cyl_x(-9.4, -8.99, 0.0, ZT, 3.4, 48))                       # shipping cover on the inlet
    for a in range(0, 360, 36):
        t = math.radians(a)
        parts.append(bolt_x(-9.4, 2.9 * math.cos(t), ZT + 2.9 * math.sin(t), -1, 0.22))
    parts.append(cyl_x(-9.7, -9.39, 0.0, ZT, 0.9, 20))                      # cover handle boss
    for a in range(0, 360, 30):                                               # compressor front cover bolts
        t = math.radians(a + 15)
        y, z = 4.15 * math.cos(t), ZT + 4.15 * math.sin(t)
        if z > ZT - 2.9:
            parts.append(bolt_x(-8.6, y, z, -1, 0.22))
    parts.append(M.hull(union([box([-0.2, -2.6, z0 + 1.2], [-0.1, 2.6, Z_MAN]),        # turbine inlet, against the manifold
                               box([1.18, -2.6, z0 + 2.5], [1.19, 2.6, Z_MAN])])))    # end; underside at 45 degrees
    parts.append(M.hull(union([box([0.85, -2.95, z0 + 2.15], [0.86, 2.95, Z_MAN + 0.3]),
                               box([1.18, -2.95, z0 + 2.5], [1.19, 2.95, Z_MAN + 0.3])])))
    stack = rrect(-3.4, -2.0, -0.6, 2.0, 0.8)                                 # exhaust stack adapter
    parts.append(ext_z(stack, ZT + 3.0, 26.6))
    parts.append(M.hull(union([ext_z(rrect(-3.4, -2.0, -0.6, 2.0, 0.8), 25.6, 25.61),
                               ext_z(rrect(-3.8, -2.4, -0.2, 2.4, 1.0), 26.0, 26.6)])))
    parts.append(ext_z(rrect(-3.7, -2.3, -0.3, 2.3, 0.9), 26.59, 26.9))       # shipping cover
    for x, y in ((-3.3, -1.8), (-3.3, 1.8), (-0.7, -1.8), (-0.7, 1.8), (-2.0, -2.0), (-2.0, 2.0)):
        parts.append(bolt_z(x, y, 26.9, 0.2, 0.2))
    for sgn in (-1, 1):                                                       # oil supply and drain
        parts.append(M.cylinder(ZT - 1.6 - z0 - 1.19, 0.42, 0.42, 16).translate([-4.4, sgn * 2.2, z0 + 1.19]))
    parts.append(box([-7.4, -0.5, ZT + 4.4], [-6.0, 0.5, ZT + 5.8]))          # lifting eye on the compressor
    return union(parts)


@solid
def turbo():
    m = _turbo_assembled()
    socks = [M.cylinder(SOCK_D, SOCK_R, SOCK_R, 20).translate([x, 0.0, Z_PLAT - 0.01]) for x in (-6.0, -1.6)]
    m = m - union(socks)
    return m.translate([0, 0, -Z_PLAT])


# ================================================================== main generator
GR = 8.0                    # frame radius
GL = 23.2                   # flange face to companion alternator hub
VENTS = (0.0, 25.0, 155.0, 180.0)   # vent angles from +y round the axis


def _gen_assembled():
    """Generator in assembly pose: axis along x at z = ZC, flange face at x = 0, base (skid top) z = 0."""
    parts = [cyl_x(0.0, 1.0, 0.0, ZC, 8.4, 96),                                # engine flange
             cyl_x(0.99, 15.0, 0.0, ZC, GR, 96)]                               # frame
    for x0 in (2.2, 7.6, 14.2):                                                # frame bands
        parts.append(cyl_x(x0, x0 + 0.8, 0.0, ZC, GR + 0.25, 96))
    for a in range(0, 360, 20):                                                # flange bolts
        t = math.radians(a + 10)
        y, z = 8.15 * math.cos(t), ZC + 8.15 * math.sin(t)
        if z > 0.5:
            parts.append(bolt_x(1.0, y, z, 1, 0.2))
    for sgn in (-1, 1):                                                        # mounting rails
        ya, yb = sorted((sgn * 6.7, sgn * 9.3))
        parts.append(box([0.0, ya, 0.0], [15.0, yb, 6.2]))
        for x in (2.4, 7.5, 12.6):
            parts.append(bolt_z(x, sgn * 8.5, 6.2, 0.36, 0.3))
    top = ZC + GR                                                              # air inlet on top, engine side at 45
    parts.append(M.hull(union([box([3.4, -3.4, top - 1.0], [12.6, 3.4, top - 0.99]),
                               box([5.6, -3.0, top + 1.2], [10.4, 3.0, top + 1.21])])))
    parts.append(box([5.8, -2.8, top + 1.2], [10.2, 2.8, top + 1.5]))
    for x in np.linspace(6.2, 9.8, 4):
        for y in (-2.45, 2.45):
            parts.append(bolt_z(x, y, top + 1.5, 0.2, 0.2))
    for sgn in (-1, 1):                                                        # lifting lugs on the shoulders
        y = sgn * 5.5
        zs = ZC + math.sqrt(GR * GR - y * y) - 0.6
        for x0 in (1.2, 10.8):                                                 # engine side at 45 degrees
            lug = along_y(poly([(x0, zs), (x0 + 4.2, zs), (x0 + 4.2, zs + 1.8), (x0 + 3.6, zs + 2.4), (x0 + 2.4, zs + 2.4)]),
                          y - 0.5, y + 0.5)
            ex, ez = x0 + 3.0, zs + 1.5
            for ya, yb in ((y + 0.5 - 0.32, y + 0.51), (y - 0.51, y - 0.5 + 0.32)):
                lug = lug - M.cylinder(yb - ya, 0.5, 0.5, 20).rotate([-90, 0, 0]).translate([ex, ya, ez])
            parts.append(lug)
    parts.append(M.hull(union([box([4.0, 6.9, 5.0], [11.0, 7.0, 11.0]),        # terminal box, engine side at 45
                               box([6.4, 9.3, 5.4], [11.0, 9.4, 10.6])])))
    for x, z in ((7.0, 6.0), (10.4, 6.0), (7.0, 10.0), (10.4, 10.0)):
        parts.append(bolt_y(x, 9.4, z, 1, 0.2))
    parts.append(cyl_x(15.0, 16.4, 0.0, ZC, 7.6, 96))                          # end bell
    for a in range(0, 360, 24):
        t = math.radians(a)
        parts.append(bolt_x(16.4, 6.6 * math.cos(t), ZC + 6.6 * math.sin(t), 1, 0.22))
    parts.append(cyl_x(16.39, 21.8, 0.0, ZC, 4.6, 64))                         # companion alternator
    for a in range(0, 360, 30):
        rib = box([16.6, -0.25, 4.4], [21.4, 0.25, 5.0]).rotate([a + 15, 0, 0]).translate([0, 0, ZC])
        parts.append(rib)
    parts.append(cyl_x(21.79, 22.6, 0.0, ZC, 4.2, 64))
    parts.append(cyl_x(22.59, GL, 0.0, ZC, 1.6, 32))
    parts.append(M.hull(union([box([16.8, -1.4, ZC + 4.0], [21.0, 1.4, ZC + 4.01]),
                               box([18.4, -1.2, ZC + 5.6], [21.0, 1.2, ZC + 5.61])])))
    m = union(parts)
    cuts = []
    for a in VENTS:                                                            # screened vents round the frame
        w = box([11.4, -1.5, GR - 0.45], [14.0, 1.5, GR + 1.0]).rotate([a - 90.0, 0, 0]).translate([0, 0, ZC])
        cuts.append(w)
    for sgn in (-1, 1):                                                        # recessed panel in each rail
        ya, yb = sorted((sgn * 9.0, sgn * 9.4))
        cuts.append(box([3.6, ya, 1.2], [11.4, yb, 5.0]))
    m = m - union(cuts)
    bars = []
    for a in VENTS:
        for dy in (-0.75, 0.0, 0.75):
            b = box([11.4, dy - 0.15, GR - 0.5], [14.0, dy + 0.15, GR - 0.1]).rotate([a - 90.0, 0, 0]).translate([0, 0, ZC])
            bars.append(b)
    m = union([m] + bars)
    sock = along_x(tear((0.0, ZC), 2.55, 32), -0.01, 1.15)
    return m - sock


@solid
def generator():
    """Print pose: standing on its engine flange (axis up)."""
    m = _gen_assembled().rotate([0, -90, 0])
    b = m.bounding_box()
    return m.translate([0, 0, -b[2]])


# ================================================================== skid
def _ibeam(x0, x1, yc, z0):
    sec = poly([(yc - 1.0, z0), (yc + 1.0, z0), (yc + 1.0, z0 + 0.5), (yc + 0.3, z0 + 0.5), (yc + 0.3, z0 + SKID_H - 1.2),
                (yc + 1.0, z0 + SKID_H - 0.5), (yc + 1.0, z0 + SKID_H), (yc - 1.0, z0 + SKID_H), (yc - 1.0, z0 + SKID_H - 0.5),
                (yc - 0.3, z0 + SKID_H - 1.2), (yc - 0.3, z0 + 0.5), (yc - 1.0, z0 + 0.5)])
    return along_x(sec, x0, x1)


@solid
def skid():
    """Print pose: flat. Timbers to SKID_T (Cocoa Brown), the steel skid above (Black)."""
    zt = SKID_T
    parts = []
    xs = np.linspace(SKID_X0 + 3.0, SKID_X1 - 3.0, 7)
    for x in xs:                                                               # timber blocking across the car
        parts.append(box([x - 1.75, -15.0, 0.0], [x + 1.75, 15.0, zt]))
    zb = zt - 0.01
    for yc in (-SKID_Y, SKID_Y):
        parts.append(_ibeam(SKID_X0, SKID_X1, yc, zb))
        for x in np.arange(SKID_X0 + 5.0, SKID_X1 - 2.0, 9.2):                 # web stiffeners
            for d in (-1, 1):
                ya, yb = sorted((yc + d * 0.29, yc + d * 0.99))
                parts.append(box([x - 0.25, ya, zb + 0.49], [x + 0.25, yb, zb + SKID_H - 0.51]))
    for x in xs:                                                               # cross channels on the timbers
        parts.append(box([x - 0.8, -SKID_Y + 0.29, zb], [x + 0.8, SKID_Y - 0.29, zb + SKID_H - 0.6]))
    for x0 in (SKID_X0, SKID_X1 - 1.2):                                        # end channels
        parts.append(box([x0, -SKID_Y - 1.0, zb], [x0 + 1.2, SKID_Y + 1.0, zb + SKID_H]))
    for x in (SKID_X0 + 0.6, SKID_X1 - 0.6):                                   # corner lifting lugs
        for y in (-SKID_Y, SKID_Y):
            lug = union([box([x - 0.5, y - 1.2, zb + SKID_H - 0.01], [x + 0.5, y + 1.2, zb + SKID_H + 1.6]),
                         cyl_x(x - 0.5, x + 0.5, y, zb + SKID_H + 1.6, 1.2, 28)])
            for dx in (-0.5, 0.5):
                lug = lug - cyl_x(x + dx - 0.25, x + dx + 0.25, y, zb + SKID_H + 1.6, 0.5, 16)
            parts.append(lug)
    zs = zb + SKID_H
    for x in (6.0, LB - 6.0):                                                  # the engine's locating pegs
        for y in (-SKID_Y, SKID_Y):
            parts.append(M.cylinder(PEG_H + 0.01, PEG_R, PEG_R, 20).translate([x, y, zs - 0.01]))
    for x in np.arange(SKID_X0 + 2.0, SKID_X1 - 1.0, 4.6):                     # bolts along the top flanges
        for y in (-SKID_Y - 0.65, -SKID_Y + 0.65, SKID_Y - 0.65, SKID_Y + 0.65):
            if all(abs(x - p) > 1.2 for p in (6.0, LB - 6.0)):
                parts.append(bolt_z(x, y, zs, 0.2, 0.18))
    m = union(parts)
    grooves = []
    rng = np.random.default_rng(87)
    for x in xs:                                                               # timber checks and grain
        for sgn in (-1, 1):                                                   # out past the beams, so none is roofed over
            for k in range(2):
                dx = rng.uniform(-1.2, 1.2)
                ya = rng.uniform(9.4, 11.5)
                yb = min(14.7, ya + rng.uniform(2.5, 5.0))
                grooves.append(box([x + dx - 0.1, sgn * ya, zt - 0.2], [x + dx + 0.1, sgn * yb, zt + 0.1]))
    m = m - union(grooves)
    runners = [box([SKID_X0 + 1.25, y - 1.5, 0.0], [SKID_X1 - 1.25, y + 1.5, 0.6]) for y in (-SKID_Y, SKID_Y)]
    return union([m] + runners)


# ================================================================== scene (renders)
def scene():
    L = ft(40.0)
    s = F._car(L, "car_black")
    zd = F.deck()
    xc = L / 2 - (SKID_X0 + SKID_X1) / 2                                      # engine x = 0 on the car
    sk = skid()
    hi, lo = sk.split_by_plane((0.0, 0.0, 1.0), SKID_T + 1e-3)
    F._put(s, "Cocoa Brown", lo.translate([xc, 0, zd]))
    F._put(s, "Black", hi.translate([xc, 0, zd]))
    zs = zd + SKID_T - 0.01 + SKID_H
    F._put(s, "Gray", engine().translate([xc, 0, zs]))
    F._put(s, "Iron Gray Metallic", turbo().translate([xc, 0, zs + Z_PLAT]))
    F._put(s, "Black", _gen_assembled().translate([xc + GEN_X, 0, zs]))
    return s

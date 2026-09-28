"""Parts for the railroad and town batch (buildings 61-70). Each building's skins, cornice
ornament, windows, doors, porch pieces and chimneys are its own; nothing here is shared between
buildings, or with the houses and shops before them."""
import math

import numpy as np
from manifold3d import JoinType, Manifold as M

from .core import RIB, box, circle, cs_union, poly, rect, union
from .ornament import chamfer_box, ext, stroke
from . import cornice as CO, features as FT, openings as O, porchwork as PW, skins as SK, trimwork as TW
from .colonial import _st
from .colonial4 import _glazed

MJ = JoinType.Miter


# ================================================================== 61 the Millbrook depot
def depot_wainscot(region, pitch=1.2):
    """Car siding: narrow tongue-and-groove boards standing on end, a groove between each pair
    (the Millbrook's wainscot)."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    grooves = cs_union([rect(u - 0.22, v0 - 1, u + 0.22, v1 + 1) for u in np.arange(u0 + pitch / 2, u1, pitch)])
    return M.extrude(region, 0.4) - ext(grooves ^ region, 0.2, 1.0)


def depot_droplap(region, datum=0.0, pitch=1.5, sticks=()):
    """Drop siding in panels: flat courses, each with a sharp groove at its foot and a soft bead
    over it, framed by flat stick boards standing proud at ``sticks`` (u positions)
    (the Millbrook's upper walls)."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    k0 = math.floor((v0 - datum) / pitch) - 1
    ks = range(k0, k0 + int((v1 - v0) / pitch) + 4)
    grooves = cs_union([rect(u0 - 1, datum + k * pitch - 0.18, u1 + 1, datum + k * pitch + 0.18) for k in ks])
    beads = cs_union([rect(u0 - 1, datum + k * pitch + 0.18, u1 + 1, datum + k * pitch + 0.62) for k in ks])
    out = M.extrude(region, 0.35) - ext(grooves ^ region, 0.12, 1.0) + ext(beads ^ region, 0.3, 0.5)
    if sticks:
        st = cs_union([rect(u - 0.7, v0 - 1, u + 0.7, v1 + 1) for u in sticks]) ^ region
        out = out + ext(st, 0.0, 0.8)
    return out


def foundation_drafted(reg, seed=0):
    """Coursed ashlar with drafted margins: each block rock-pitched in the middle and dressed
    smooth in a narrow band round its edges (the Millbrook)."""
    b = reg.bounds()
    rng = np.random.default_rng(seed + 613)
    ch = 2.6
    joints, bosses, knobs = [], [], []
    for v in np.arange(b[1], b[3], ch):
        joints.append(rect(b[0] - 1, v - 0.15, b[2] + 1, v + 0.15))
        u = b[0] - rng.uniform(0.0, 4.0)
        while u < b[2]:
            L = rng.uniform(4.6, 7.4)
            joints.append(rect(u - 0.15, v, u + 0.15, v + ch))
            if v + ch - 0.6 - (v + 0.6) >= 1.2:
                bosses.append(rect(u + 0.65, v + 0.6, u + L - 0.65, v + ch - 0.6))
                for _ in range(2):
                    x = rng.uniform(u + 1.2, u + L - 1.2)
                    knobs.append(circle((x, v + ch / 2 + rng.uniform(-0.3, 0.3)), 0.5, 10))
            u += L
    out = M.extrude(reg, 0.3) - ext(cs_union(joints) ^ reg, 0.15, 1.0)
    out = out + ext(cs_union(bosses) ^ reg, 0.29, 0.6)
    if knobs:
        out = out + ext(cs_union(knobs) ^ cs_union(bosses) ^ reg, 0.59, 0.75)
    return out


def frieze_driverwheels(L, h, b, pitch, margin, pair, half):
    """Locomotive drivers: at every station a spoked wheel with a counterweight, the wheels
    coupled hub to hub by side rods standing proud of them (the Millbrook)."""
    v0, v1 = 0.6, h - 0.6
    vc = (v0 + v1) / 2
    r = min(2.0, (v1 - v0) / 2)
    us = CO._us(L, pitch, margin, 0.0)
    out = []
    for u in us:
        rim = circle((u, vc), r, 32) - circle((u, vc), r - 0.55, 32)
        spokes = [stroke([(u + 0.5 * math.cos(a), vc + 0.5 * math.sin(a)), (u + (r - 0.4) * math.cos(a), vc + (r - 0.4) * math.sin(a))], 0.45, caps=False)
                  for a in np.linspace(0.0, 2 * math.pi, 9)[:-1]]
        cw = (circle((u, vc), r - 0.45, 32) ^ rect(u - r, vc - r, u + r, vc - r * 0.35))          # the counterweight
        out.append(_st(cs_union([rim, cw, circle((u, vc), 0.75, 16)] + spokes), b, 0.45))
    for a, c in zip(us[:-1], us[1:]):
        rod = cs_union([rect(a, vc + 0.35, c, vc + 1.0), circle((a, vc + 0.68), 0.6, 14), circle((c, vc + 0.68), 0.6, 14)])
        out.append(_st(rod, b + 0.44, 0.35))
    return out, []


def course_railties(L, h, b, pitch, margin, p):
    """A rail on its ties: a continuous rail head along the top over a row of square tie ends,
    each with a spike head (the Millbrook)."""
    rail = rect(0.3, h - 0.55, L - 0.3, h - 0.1)
    ties = cs_union([rect(u - 0.55, 0.1, u + 0.55, h - 0.55) for u in np.arange(1.0, L - 0.6, 1.9)])
    spikes = cs_union([rect(u - 0.22, h - 1.0, u + 0.22, h - 0.55) for u in np.arange(1.0, L - 0.6, 1.9)])
    return [ext(ties, b - 0.05, b + 0.35), ext(rail, b - 0.05, b + 0.45), ext(spikes, b + 0.3, b + 0.45)]


def bracket_depotknee(h, d, t):
    """A big station eave knee: a solid sweep from a plumb post on the wall out along the soffit,
    its foot a stepped drop (side profile, top at v = 0)."""
    hb = max(3.0, h)
    pts = [(0.0, 0.0), (d, 0.0), (d, -0.9)] + \
          [(d - (d - 1.2) * math.sin(a), -0.9 - (hb - 2.1) * (1 - math.cos(a))) for a in np.linspace(0.1, math.pi / 2, 10)] + \
          [(1.2, -hb + 0.6), (0.9, -hb + 0.6), (0.9, -hb), (0.0, -hb)]
    return poly(pts)


CO.FRIEZE_EXTRA.update(driverwheels=frieze_driverwheels)
CO.COURSE_EXTRA.update(railties=course_railties)
TW.BRACKET_EXTRA.update(depotknee=bracket_depotknee)
TW.FOUNDATION_EXTRA.update(drafted=foundation_drafted)


def _ray_pediment(hw, zb, rise, rays=7, proud=1.1):
    """A low gabled head: a tympanum with a fan of rays from the middle of its foot, under
    raking mouldings that stand proud (the depot's window and door heads)."""
    tri = poly([(-hw, zb), (hw, zb), (0.0, zb + rise)])
    inner = tri.offset(-0.8, MJ, 4.0)
    rk = [stroke([(0.0, zb + 0.2), ((rise - 0.9) * math.cos(a) * hw / rise, zb + 0.2 + (rise - 1.1) * math.sin(a))], 0.42, caps=False)
          for a in np.linspace(math.pi * 0.14, math.pi * 0.86, rays)]
    return [ext(tri, 0.0, 0.5), ext(tri - inner, 0.0, proud), ext(cs_union(rk) ^ inner, 0.0, 0.85),
            ext(circle((0.0, zb + 0.2), 0.9, 16) ^ tri, 0.0, 0.95)]


def window_depot(w, h, A=1.4):
    """The Millbrook's window: tall two-over-two sash under a frieze board and a low gabled head
    with a fan of rays in it, the sill lugged on two corbel blocks."""
    op = O.opening_cs(w, h, 0)
    plug_cs = op.offset(-O.CLR, MJ, 4.0)
    pl = O.PLUG
    u0, v0, u1, v1 = plug_cs.offset(-0.5, MJ, 4.0).bounds()
    vm, um = v0 + (v1 - v0) * 0.5, (u0 + u1) / 2
    bars = cs_union([rect(u0 - 1, vm - 0.35, u1 + 1, vm + 0.35), rect(um - 0.22, v0 - 1, um + 0.22, v1 + 1)])
    sash = _glazed([ext(plug_cs, -pl, -0.6)], rect(u0, v0, u1, v1), pl, bars, plug_cs)
    hw = w / 2 + A
    parts = [ext(op - op.offset(-RIB, MJ, 4.0), 0.0, 0.7),
             ext((op.offset(A, MJ, 4.0) - op) ^ rect(-w, 0.0, w, h + A), 0.0, 0.6),
             ext(rect(-hw, h + A - 0.01, hw, h + A + 1.6), 0.0, 0.75)]
    zb = h + A + 1.59
    rise = round((hw + 1.2) * 0.42 / 0.2) * 0.2
    parts += _ray_pediment(hw + 1.2, zb, rise)
    parts.append(chamfer_box(-hw - 1.0, -1.2, hw + 1.0, 0.2, 0.0, 1.4, c=0.4, bottom=0.8))
    for sg in (-1, 1):
        parts.append(chamfer_box(sg * hw - 1.0, -2.8, sg * hw + 1.0, -1.19, 0.0, 1.0, c=0.3, bottom=1.0))
    return O._one_piece(sash, parts, op, plug_cs, pl, zb + rise, -2.8)


def door_depot(w=16.0, h=27.0, A=1.6):
    """The waiting room doors: a pair of leaves, each a tall light over a cross-braced panel,
    a three-light transom over them, in a casing under the depot's rayed gable head."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, MJ, 4.0)
    pl = O.PLUG
    ht = h - 5.0                                  # the transom bar
    body = [ext(plug_cs, -pl, -1.0)]
    glass = []
    lw = (w - 2 * O.CLR - 1.0) / 2
    for sg in (-1, 1):
        a, e = sorted((sg * 0.5, sg * (0.5 + lw)))
        leaf = rect(a, 0.3, e, ht - 0.3)
        lite = rect(a + 0.9, ht * 0.45, e - 0.9, ht - 1.2)
        body.append(ext(leaf - lite, -1.0, -0.6))
        glass.append(lite)
        pan = rect(a + 0.9, 1.2, e - 0.9, ht * 0.45 - 1.0)
        pb = pan.bounds()
        body.append(ext(pan - pan.offset(-0.5, MJ, 4.0), -0.6, -0.25))
        body.append(ext(cs_union([stroke([(pb[0] + 0.4, pb[1] + 0.4), (pb[2] - 0.4, pb[3] - 0.4)], 0.5),
                                  stroke([(pb[0] + 0.4, pb[3] - 0.4), (pb[2] - 0.4, pb[1] + 0.4)], 0.5)]) ^ pan, -0.6, -0.2))
    tw = (w - 2 * O.CLR - 2.4) / 3
    for k in range(3):
        a = -w / 2 + O.CLR + 0.6 + k * (tw + 0.6)
        glass.append(rect(a, ht + 0.6, a + tw, h - O.CLR - 0.6))
    body.append(ext(rect(-w / 2, ht - 0.4, w / 2, ht + 0.6) ^ plug_cs, -pl, -0.6))
    sash = _glazed(body, cs_union(glass), pl, None, plug_cs)
    hw = w / 2 + A
    parts = [ext(op - op.offset(-RIB, MJ, 4.0), 0.0, 0.7),
             ext((op.offset(A, MJ, 4.0) - op) ^ rect(-w, 0.0, w, h + A), 0.0, 0.7),
             ext(rect(-hw, h + A - 0.01, hw, h + A + 2.0), 0.0, 0.8)]
    for sg in (-1, 1):                            # plinth blocks at the casing's feet
        parts.append(chamfer_box(sg * (w / 2 + A / 2) - A / 2 - 0.3, 0.0, sg * (w / 2 + A / 2) + A / 2 + 0.3, 3.0, 0.0, 1.0, c=0.3))
    zb = h + A + 1.99
    rise = round((hw + 1.6) * 0.4 / 0.2) * 0.2
    parts += _ray_pediment(hw + 1.6, zb, rise, rays=9, proud=1.2)
    return O._one_piece(sash, parts, op, plug_cs, pl, zb + rise, 0.0)


def door_freight(w=18.0, h=26.0):
    """The freight room's sliding door: a leaf of vertical boards with a Z brace, hung by two
    strap hangers from a track bar that runs on past the opening to one side."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, MJ, 4.0)
    pl = O.PLUG
    leaf = rect(-w / 2 - 0.8, 0.2, w / 2 + 0.8, h + 0.6)
    lb = leaf.bounds()
    grooves = cs_union([rect(u - 0.18, lb[1], u + 0.18, lb[3]) for u in np.arange(lb[0] + 1.6, lb[2] - 0.4, 1.6)])
    body = [ext(plug_cs, -pl, 0.0), ext(leaf, 0.0, 0.8) - ext(grooves, 0.55, 1.0)]
    zs = [lb[1] + 1.6, (lb[1] + lb[3]) / 2, lb[3] - 1.6]
    rails = cs_union([rect(lb[0] + 0.6, z - 0.8, lb[2] - 0.6, z + 0.8) for z in zs])
    diag = cs_union([stroke([(lb[0] + 1.4, zs[0]), (lb[2] - 1.4, zs[1])], 1.4, caps=False),
                     stroke([(lb[0] + 1.4, zs[1]), (lb[2] - 1.4, zs[2])], 1.4, caps=False)])
    body.append(ext(rails + diag, 0.79, 1.3))
    tr0, tr1 = -w / 2 - 1.4, w / 2 + w * 0.8
    body.append(chamfer_box(tr0, h + 1.4, tr1, h + 2.6, 0.0, 1.6, c=0.35, bottom=1.4))       # the track
    for u in (-w / 4, w / 4):
        body.append(ext(rect(u - 0.8, h - 1.0, u + 0.8, h + 2.0), 0.79, 1.4))                 # hanger straps
        body.append(ext(circle((u, h + 2.0), 1.0, 16), 1.39, 1.9))                           # rollers
    body.append(chamfer_box(tr1 - 1.4, h - 3.0, tr1, h + 1.41, 0.0, 1.2, c=0.3))              # the stop
    return O._one_piece(body, [ext(op - op.offset(-RIB, MJ, 4.0), 0.0, 0.5)], op, plug_cs, pl, h + 2.6, 0.0)


def post_depot(h, collar=None, abacus=4.4, slot=None):
    """A platform column: an octagonal base block with a bevelled top, a round shaft with a
    swell, a double ring at the neck and a flared cap under the square abacus (the Millbrook)."""
    base_h = 5.4
    zt = h - 2.4
    body = PW._plinth(4.4, 1.2) + M.cylinder(base_h - 2.0, 2.35, 2.35, 8).translate([0, 0, 1.19])
    body = body + M.cylinder(0.82, 2.35, 1.5, 8).translate([0, 0, base_h - 0.82])
    zn = zt - 2.2
    body = body + PW._revolve([(0.0, base_h - 0.01), (1.35, base_h - 0.01), (1.4, (base_h + zn) * 0.45), (1.1, zn),
                               (1.45, zn + 0.4), (1.45, zn + 0.8), (1.1, zn + 1.0), (1.45, zn + 1.4), (1.45, zn + 1.8),
                               (1.1, zn + 2.0), (1.1, zt), (0.0, zt)], 28)
    return body + PW._top(h, abacus / 2, zt - 0.01, 1.1, slot)


def frieze_depotbeam(u0, u1, v_bot, v_top):
    """The platform beam: a deep plate with a bead along its foot and, at both ends, a big
    solid cove bracket (the Millbrook)."""
    L = u1 - u0
    v0 = v_top - 2.8
    parts = [rect(u0, v0, u1, v_top + 0.05), rect(u0, v0 - 0.6, u1, v0 + 0.01)]
    R = min(5.0, L * 0.18)
    for sg, ue in ((1, u0), (-1, u1)):
        q = [(ue, v0), (ue, v0 - R)] + [(ue + sg * (R - R * math.cos(a)), v0 - R + R * math.sin(a)) for a in np.linspace(0.12, math.pi / 2, 8)]
        parts.append(poly(q if sg > 0 else q[::-1]))
    return cs_union(parts)


def edge_beadrosette(L, z0, zc):
    """Platform fascia: a flat band with a half-round bead along its foot and a small square
    rosette block every 12 mm."""
    band = rect(0.3, zc - 1.6, L - 0.3, zc)
    bead = rect(0.3, zc - 2.0, L - 0.3, zc - 1.55)
    ros = cs_union([rect(u - 0.8, zc - 1.4, u + 0.8, zc - 0.2) for u in np.arange(6.0, L - 3.0, 12.0)])
    return band + bead + ros, 0.7


def skirt_platform(reg, d=1.2):
    """The platform's face: two heavy timber stringers, bolted, over a plain toe board."""
    if reg.is_empty():
        return M()
    u0, v0, u1, v1 = reg.bounds()
    body = M.extrude(reg, d * 0.55)
    joints = cs_union([rect(u0 - 1, v - 0.12, u1 + 1, v + 0.12) for v in np.arange(v1 - 2.4, v0, -2.4)])
    bolts = cs_union([rect(u - 0.3, v - 0.3, u + 0.3, v + 0.3) for v in np.arange(v1 - 1.2, v0 + 0.8, -2.4)
                      for u in np.arange(u0 + 2.0, u1 - 1.0, 5.0)])
    return body - ext(joints ^ reg, d * 0.4, d) + ext(bolts ^ reg.offset(-0.4, MJ, 4.0), d * 0.5, d * 0.8)


PW.POSTS.update(depot=post_depot)
PW.FRIEZES.update(depotbeam=frieze_depotbeam)
PW.SKIRTS.update(platform=skirt_platform)
FT.EDGE_EXTRA.update(beadrosette=edge_beadrosette)


def chimney_depot(w=7.0, d=7.0, h=18.0):
    """A station stove flue: a slim brick stack in running bond, two corbelled courses, a
    stone cap and a sheet-iron stovepipe with a conical rain hat."""
    h = round(h / 0.2) * 0.2
    zt = h - 6.4
    body = box([-w / 2, -d / 2, 0.0], [w / 2, d / 2, zt])
    body = body + TW._skin(w, d, 0.0, zt - 0.2, lambda reg, i: SK.brick_bond(reg, "running", bl=2.2, bh=0.75, d=0.25, uoff=i * 0.7))
    z = zt
    for k in range(2):
        g = 0.4 * (k + 1)
        body = body + box([-w / 2 - g, -d / 2 - g, z - 0.01], [w / 2 + g, d / 2 + g, z + 0.75])
        z += 0.75
    body = body + M.hull_points([(x * (w / 2 + 0.8), y * (d / 2 + 0.8), z - 0.01) for x in (-1, 1) for y in (-1, 1)] +
                                [(x * (w / 2 - 0.2), y * (d / 2 - 0.2), z + 0.8) for x in (-1, 1) for y in (-1, 1)])
    z += 0.79
    pipe = M.cylinder(h - z - 1.6, 1.3, 1.3, 24).translate([0, 0, z])
    hat = M.cylinder(0.6, 1.3, 1.3, 24).translate([0, 0, h - 1.61]) + M.cylinder(1.0, 2.3, 0.3, 24).translate([0, 0, h - 1.01])
    return body + pipe + hat


def sign_board(text, L, H=7.0, t=1.2, cap=3.6):
    """A station name board: a flat board with a moulded border and raised capitals, lying in
    its facade frame (u along the wall, v up, w out), centred on u = 0 with its foot at v = 0."""
    from .storefront import text_cs
    b = rect(-L / 2, 0.0, L / 2, H)
    parts = [ext(b, 0.0, t), ext(b - b.offset(-0.8, MJ, 4.0), t - 0.01, t + 0.5)]
    letters = text_cs(text, cap=cap, font="serif", track=0.35)
    lb = letters.bounds()
    sc = min(1.0, (L - 3.2) / max(1e-6, lb[2] - lb[0]))
    letters = letters.scale((sc, 1.0)).translate(((-(lb[0] + lb[2]) / 2) * sc, (H - cap) / 2 - lb[1]))
    parts.append(ext(letters, t - 0.01, t + 0.5))
    return union(parts)


# ================================================================== 62 St. Brendan's church
RND = JoinType.Round


def pointed_cs(w, h, r_frac=1.0):
    """An opening with a pointed (two-centred) head, ``w`` wide and ``h`` to the apex, its arcs
    of radius ``r_frac`` * w (1.0 = equilateral). Returns (outline, springing height)."""
    r = r_frac * w
    rise = math.sqrt(r * r - (r - w / 2) ** 2)
    s = h - rise
    head = circle((w / 2 - r, s), r, 96) ^ circle((r - w / 2, s), r, 96) ^ rect(-w / 2, s - 0.01, w / 2, h + 1.0)
    return cs_union([rect(-w / 2, 0.0, w / 2, s + 0.01), head]), s


def _voussoirs(op, s, A, n=11):
    """Every other voussoir of a pointed arch's surround (the ones set proud, for polychromy)."""
    band = (op.offset(A, RND) - op) ^ rect(-100, s, 100, 999)
    R = 60.0
    wedges = [poly([(0.0, s), (R * math.cos(math.pi * k / n), s + R * math.sin(math.pi * k / n)),
                    (R * math.cos(math.pi * (k + 1) / n), s + R * math.sin(math.pi * (k + 1) / n))]) for k in range(0, n, 2)]
    return band ^ cs_union(wedges)


def _hood(op, s, A, w, stops=True):
    """A hood mould following the arch outside the surround, ending in square label stops."""
    hood = (op.offset(A + 1.4, RND) - op.offset(A + 0.3, RND)) ^ rect(-100, s, 100, 999)
    out = [ext(hood, 0.0, 1.4)]
    if stops:
        x = w / 2 + A + 0.85
        out += [chamfer_box(sg * x - 1.0, s - 1.8, sg * x + 1.0, s + 0.1, 0.0, 1.4, c=0.3) for sg in (-1, 1)]
    return out


def window_lancet(w, h, A=1.4, r_frac=1.25, lattice=2.1):
    """St. Brendan's lancet: a tall pointed light of diamond quarries in a stone surround whose
    arch is laid in alternate raised voussoirs, under a hood mould with square label stops, on a
    weathered sill."""
    op, s = pointed_cs(w, h, r_frac)
    plug_cs = op.offset(-O.CLR, RND)
    pl = O.PLUG
    g = plug_cs.offset(-0.5, RND)
    b = g.bounds()
    run = (b[2] - b[0] + 4.0) * 1.7
    lat = []
    for k in np.arange(-run, b[3] - b[1] + run, lattice):
        lat.append(stroke([(b[0] - 2, b[1] + k), (b[2] + 2, b[1] + k + run)], 0.4, caps=False))
        lat.append(stroke([(b[0] - 2, b[1] + k + run), (b[2] + 2, b[1] + k)], 0.4, caps=False))
    sash = _glazed([ext(plug_cs, -pl, -0.6)], g, pl, cs_union(lat), plug_cs)
    parts = [ext(op - op.offset(-RIB, RND), 0.0, 0.7),
             ext((op.offset(A, RND) - op) ^ rect(-w, 0.0, w, 999), 0.0, 0.8),
             ext(_voussoirs(op, s, A), 0.79, 1.1)] + _hood(op, s, A, w)
    parts.append(chamfer_box(-w / 2 - A - 0.8, -1.4, w / 2 + A + 0.8, 0.2, 0.0, 1.6, c=0.5, bottom=1.0))
    return O._one_piece(sash, parts, op, plug_cs, pl, h + A + 1.4, -1.4)


def window_rose(D=24.0, A=1.6):
    """The west rose: eight cusped petals round a quatrefoil, spokes between them, in a moulded
    ring of two orders set with eight square bosses."""
    r = D / 2
    c = (0.0, r)
    op = circle(c, r, 96)
    plug_cs = op.offset(-O.CLR, RND)
    pl = O.PLUG
    g = plug_cs.offset(-0.5, RND)
    rr = r - O.CLR - 0.5
    ring = lambda cc, ro, t=0.45: circle(cc, ro, 40) - circle(cc, ro - t, 40)
    bars = [ring(c, rr * 0.4)]
    for k in range(8):
        a = math.pi * k / 4
        bars.append(stroke([(c[0] + rr * 0.4 * math.cos(a), c[1] + rr * 0.4 * math.sin(a)), (c[0] + rr * math.cos(a), c[1] + rr * math.sin(a))], 0.45, caps=False))
        a2 = a + math.pi / 8
        bars.append(ring((c[0] + rr * 0.72 * math.cos(a2), c[1] + rr * 0.72 * math.sin(a2)), rr * 0.19))
    for k in range(4):
        a = math.pi * k / 2
        bars.append(ring((c[0] + rr * 0.15 * math.cos(a), c[1] + rr * 0.15 * math.sin(a)), rr * 0.15, 0.4))
    sash = _glazed([ext(plug_cs, -pl, -0.6)], g, pl, cs_union(bars), plug_cs)
    parts = [ext(op - op.offset(-RIB, RND), 0.0, 0.7), ext(op.offset(A, RND) - op, 0.0, 0.9),
             ext(op.offset(A + 1.6, RND) - op.offset(A - 0.3, RND), 0.0, 1.4)]
    bosses = cs_union([rect(-0.8, -0.8, 0.8, 0.8).rotate(k * 45.0 + 22.5).translate((c[0] + (r + A + 1.0) * math.cos(math.radians(k * 45.0 + 22.5)),
                                                                                    c[1] + (r + A + 1.0) * math.sin(math.radians(k * 45.0 + 22.5)))) for k in range(8)])
    parts.append(ext(bosses, 0.0, 1.9))
    return O._one_piece(sash, parts, op, plug_cs, pl, D + A + 1.6, -A - 1.6)


def window_belfry(w, h, A=1.4):
    """A belfry opening: a pointed arch of two receding orders filled with louvres standing out of
    the dark, under a hood mould."""
    op, s = pointed_cs(w, h, 1.0)
    plug_cs = op.offset(-O.CLR, RND)
    pl = O.PLUG
    g = plug_cs.offset(-0.5, RND)
    sash = _glazed([ext(plug_cs, -pl, -0.6)], g, pl, None, plug_cs)
    slats = cs_union([rect(-w, v, w, v + 0.8) for v in np.arange(1.0, h, 1.7)]) ^ g
    sash.append(ext(slats, -pl + O.GLASS - 0.01, -0.3))
    o1 = (op.offset(A, RND) - op) ^ rect(-w * 2, 0.0, w * 2, 999)
    o2 = (op.offset(2 * A, RND) - op.offset(A - 0.01, RND)) ^ rect(-w * 2, 0.0, w * 2, 999)
    parts = [ext(op - op.offset(-RIB, RND), 0.0, 0.7), ext(o1, 0.0, 0.8), ext(o2, 0.0, 1.3)] + _hood(op, s, 2 * A, w)
    parts.append(chamfer_box(-w / 2 - 2 * A - 0.8, -1.4, w / 2 + 2 * A + 0.8, 0.2, 0.0, 1.8, c=0.5, bottom=1.2))
    return O._one_piece(sash, parts, op, plug_cs, pl, h + 2 * A + 1.4, -1.4)


def _straps(w, vs, leaf, scroll=True):
    """Wrought strap hinges across a plank leaf, each ending in a scroll (or a split C)."""
    out = []
    for v in vs:
        for sg in (-1, 1):
            x0, x1 = sg * 0.7, sg * (w / 2 - 1.2)
            out.append(stroke([(x0, v), (x1, v)], 0.7, caps=True))
            if scroll:
                pts = [(x0 + sg * 0.2 + sg * 0.9 * math.sin(a), v + 0.9 * (1 - math.cos(a))) for a in np.linspace(0.0, math.pi * 1.4, 10)]
            else:
                pts = [(x1 - sg * 0.9 * math.sin(a), v + 1.0 * math.cos(a) - 1.0 + 1.0) for a in np.linspace(-math.pi * 0.6, math.pi * 0.6, 10)]
            out.append(stroke(pts, 0.5, caps=True))
    return cs_union(out) ^ leaf


def door_west(w=14.0, h=30.0):
    """The west door: two plank leaves under a pointed arch on scrolled strap hinges, in three
    receding moulded orders on plinths, under a gablet with a trefoil in its field."""
    op, s = pointed_cs(w, h, 1.0)
    plug_cs = op.offset(-O.CLR, RND)
    pl = O.PLUG
    leaf = plug_cs.offset(-0.3, RND)
    grooves = cs_union([rect(u - 0.15, -1.0, u + 0.15, h + 5.0) for u in np.arange(-w / 2 + 1.3, w / 2, 1.3)]) ^ leaf
    body = [ext(plug_cs, -pl, -1.0), ext(leaf, -1.0, -0.6) - ext(grooves, -0.8, -0.5) - ext(rect(-0.3, 0.0, 0.3, h), -0.9, -0.5)]
    body.append(ext(_straps(w, (h * 0.16, h * 0.5), leaf), -0.61, -0.25))
    body.append(ext(plug_cs - plug_cs.offset(-0.5, RND), -pl, 0.0))                  # the rebate rim
    parts = [ext(op - op.offset(-RIB, RND), 0.0, 0.7)]
    for k, dep in enumerate((0.8, 1.3, 1.8)):
        a = 1.2 * (k + 1)
        ring = (op.offset(a, RND) - op.offset(a - 1.21, RND)) ^ rect(-w * 2, 0.0, w * 2, 999)
        parts.append(ext(ring, 0.0, dep))
    for sg in (-1, 1):
        parts.append(chamfer_box(sg * (w / 2 + 1.8) - 2.2, 0.0, sg * (w / 2 + 1.8) + 2.2, 3.6, 0.0, 2.2, c=0.5))
    xo = w / 2 + 3.6 + 1.2
    apex = h + 3.6 + 7.0
    tri = poly([(-xo, s), (xo, s), (0.0, apex)])
    field = tri - op.offset(3.6, RND)
    parts.append(ext(tri - tri.offset(-1.1, MJ, 4.0) - op.offset(3.6, RND), 0.0, 1.6))
    parts.append(ext(field, 0.0, 0.5))
    tc = (0.0, (h + 3.6 + apex) / 2 + 0.6)
    tre = cs_union([circle((tc[0] + 1.0 * math.cos(a), tc[1] + 1.0 * math.sin(a)), 1.0, 20) - circle((tc[0] + 1.0 * math.cos(a), tc[1] + 1.0 * math.sin(a)), 0.55, 20)
                    for a in (math.pi / 2, math.pi / 2 + 2.09, math.pi / 2 + 4.19)])
    parts.append(ext(tre ^ tri.offset(-1.2, MJ, 4.0), 0.0, 1.0))
    parts.append(chamfer_box(-1.0, apex - 1.4, 1.0, apex + 1.6, 0.0, 1.8, c=0.4))
    return O._one_piece(body, parts, op, plug_cs, pl, apex + 1.6, 0.0)


def door_tower(w=10.0, h=26.0):
    """The tower door: one plank leaf under a pointed arch on split-C strap hinges, in two
    receding orders under a hood mould with label stops."""
    op, s = pointed_cs(w, h, 1.1)
    plug_cs = op.offset(-O.CLR, RND)
    pl = O.PLUG
    leaf = plug_cs.offset(-0.3, RND)
    grooves = cs_union([rect(u - 0.15, -1.0, u + 0.15, h + 5.0) for u in np.arange(-w / 2 + 1.25, w / 2, 1.25)]) ^ leaf
    body = [ext(plug_cs, -pl, -1.0), ext(leaf, -1.0, -0.6) - ext(grooves, -0.8, -0.5)]
    body.append(ext(_straps(w, (h * 0.18, h * 0.46, h * 0.72), leaf, scroll=False), -0.61, -0.25))
    body.append(ext(plug_cs - plug_cs.offset(-0.5, RND), -pl, 0.0))                  # the rebate rim
    o1 = (op.offset(1.2, RND) - op) ^ rect(-w * 2, 0.0, w * 2, 999)
    o2 = (op.offset(2.4, RND) - op.offset(1.19, RND)) ^ rect(-w * 2, 0.0, w * 2, 999)
    parts = [ext(op - op.offset(-RIB, RND), 0.0, 0.7), ext(o1, 0.0, 0.8), ext(o2, 0.0, 1.3)] + _hood(op, s, 2.4, w)
    return O._one_piece(body, parts, op, plug_cs, pl, h + 2.4 + 1.4, 0.0)


def brick_polychrome(region, datum=0.0, every=14, n=2, bh=0.8):
    """Red brick in running bond, every ``every`` courses a band of ``n`` courses of headers set a
    hair proud for the buff (High Victorian polychromy) (St. Brendan's)."""
    if region.is_empty():
        return M()
    b = region.bounds()
    out = SK.brick_bond(region, "running", bl=2.4, bh=bh, d=0.25, datum=datum)
    rows = [k for k in range(int(math.floor((b[1] - datum) / bh)) - 1, int(math.ceil((b[3] - datum) / bh)) + 1) if k % every < n]
    if not rows:
        return out
    band = cs_union([rect(b[0] - 1, datum + k * bh, b[2] + 1, datum + (k + 1) * bh) for k in rows]) ^ region
    joints = cs_union([rect(b[0] - 1, datum + k * bh - 0.1, b[2] + 1, datum + k * bh + 0.1) for k in rows] +
                      [rect(u - 0.1, datum + k * bh, u + 0.1, datum + (k + 1) * bh) for k in rows
                       for u in np.arange(b[0] + (k % 2) * 0.6, b[2], 1.2)])
    return out - ext(band, 0.05, 1.0) + (ext(band, 0.0, 0.4) - ext(joints ^ band, 0.22, 1.0))


def band_rows(z0, z1, datum, every=14, n=2, bh=0.8):
    """World z ranges of the polychrome bands (for the render's buff)."""
    out = []
    for k in range(int(math.floor((z0 - datum) / bh)), int(math.ceil((z1 - datum) / bh)) + 1):
        if k % every == 0:
            out.append((datum + k * bh, datum + (k + n) * bh))
    return out


def foundation_snecked(reg, seed=0):
    """Snecked rubble: squared stones of mixed heights brought to rough courses, small snecks
    filling the steps between them (St. Brendan's)."""
    b = reg.bounds()
    rng = np.random.default_rng(seed + 877)
    stones = []
    v = b[1]
    while v < b[3]:
        ch = rng.uniform(2.2, 3.2)
        u = b[0] - rng.uniform(0.0, 3.0)
        while u < b[2]:
            L = rng.uniform(2.8, 5.6)
            if rng.random() < 0.3 and ch > 2.6:                   # two stones stacked, or a stone and a sneck
                split = rng.uniform(0.45, 0.6) * ch
                stones.append(rect(u + 0.15, v + 0.15, u + L - 0.15, v + split - 0.15))
                sw = rng.uniform(1.2, L * 0.6)
                stones.append(rect(u + 0.15, v + split + 0.15, u + sw - 0.15, v + ch - 0.15))
                stones.append(rect(u + sw + 0.15, v + split + 0.15, u + L - 0.15, v + ch - 0.15))
            else:
                stones.append(rect(u + 0.15, v + 0.15, u + L - 0.15, v + ch - 0.15))
            u += L
        v += ch
    st = cs_union(stones) ^ reg
    st = st.offset(-0.2, MJ, 4.0).offset(0.2, MJ, 4.0)
    return M.extrude(reg, 0.3) + ext(st, 0.29, 0.62)


def frieze_tracery(L, h, b, pitch, margin, pair, half):
    """Blind tracery: at every station a two-light panel (twin pointed lights under a round eye,
    all in outline) standing proud (St. Brendan's)."""
    v0, v1 = 0.6, h - 0.6
    hh = v1 - v0
    out = []
    pw = min(pitch * 0.8, hh * 0.95)
    for u in CO._us(L, pitch, margin, 0.0):
        outer, _ = pointed_cs(pw, hh, 1.0)
        outer = outer.translate((u, v0))
        lw = pw * 0.38
        lights = []
        for sg in (-1, 1):
            li, _ = pointed_cs(lw, hh * 0.58, 1.0)
            li = li.translate((u + sg * pw * 0.22, v0 + 0.4))
            lights.append(li - li.offset(-0.4, RND))
        eye = circle((u, v0 + hh * 0.74), pw * 0.15, 24)
        parts = [outer - outer.offset(-0.45, RND), eye - eye.offset(-0.4, RND), rect(u - 0.2, v0, u + 0.2, v0 + hh * 0.5)] + lights
        out.append(_st(cs_union(parts) ^ outer, b, 0.45))
    return out, []


def frieze_crockets(L, h, b, pitch, margin, pair, half):
    """A fillet along the foot with a leafy crocket at every station, its stalk curling up and
    over into a knob of leaves (St. Brendan's tower)."""
    v0, v1 = 0.6, h - 0.6
    hh = v1 - v0
    out = [_st(rect(0.3, v0, L - 0.3, v0 + 0.7), b, 0.35)]
    for u in CO._us(L, pitch, margin, 0.0):
        r = min(0.95, hh * 0.22)
        leaf = cs_union([stroke([(u, v0 + 0.5), (u + 0.2, v0 + hh * 0.45), (u + 0.8, v0 + hh * 0.7)], 0.5),
                         circle((u + 0.9, v1 - r), r, 18), circle((u + 0.9 - r * 1.1, v1 - r * 1.4), r * 0.7, 14)])
        out.append(_st(leaf ^ rect(0.0, v0, L, v1), b, 0.45))
    return out, []


def course_fourleaf(L, h, b, pitch, margin, p):
    """A row of four-leaf flowers (four round petals and a boss) between two fillets."""
    vc = h / 2
    rp = min(0.34, h * 0.2)
    flowers = []
    for u in np.arange(1.2, L - 0.8, 2.2):
        flowers += [circle((u + 0.4 * math.cos(a), vc + 0.4 * math.sin(a)), rp, 12) for a in (0.0, math.pi / 2, math.pi, 1.5 * math.pi)]
    fil = cs_union([rect(0.3, 0.05, L - 0.3, 0.35), rect(0.3, h - 0.35, L - 0.3, h - 0.05)])
    return [ext(fil, b - 0.05, b + 0.3), ext(cs_union(flowers), b - 0.05, b + 0.4)]


CO.FRIEZE_EXTRA.update(tracery=frieze_tracery, crockets=frieze_crockets)
CO.COURSE_EXTRA.update(fourleaf=course_fourleaf)
TW.FOUNDATION_EXTRA.update(snecked=foundation_snecked)


def buttress(h, d0=5.0, w=5.0, set1=0.45):
    """A stepped buttress in the facade frame (u across, v up, w out): full depth to ``set1`` of
    its height, a 45 degree weathering back to 3/5, and a second weathering into the wall."""
    from .ornament import side_profile
    v1 = round(h * set1 / 0.2) * 0.2
    d1 = d0 * 0.6
    prof = [(0.0, 0.0), (d0, 0.0), (d0, v1), (d1, v1 + (d0 - d1)), (d1, h - d1), (0.0, h)]
    return side_profile(prof, -w / 2, w / 2)


def spire(half, r_in, h_sp, plate_t=1.6, pin=4.4, pin_h=8.0, tex_kw=None):
    """The steeple's crown, one piece: a square deck plate over the tower top, an octagonal spire
    of pointed-band slates, and a gabled pinnacle at each corner. Local: centred on the tower,
    z = 0 at the plate's foot."""
    from . import roof as R_
    plate = box([-half, -half, 0.0], [half, half, plate_t])
    rc = r_in / math.cos(math.pi / 8)
    octo = [(rc * math.cos(math.pi / 8 + k * math.pi / 4), rc * math.sin(math.pi / 8 + k * math.pi / 4)) for k in range(8)]
    S = h_sp / r_in
    sp, tex = R_.hip_roof([(octo, list(range(8)))], plate_t, S, 0.0, texture="zigband",
                          tex_kw=tex_kw or dict(pitch=1.5, wtab=2.0, d=0.35), zlo=plate_t - 0.01)
    body = plate + sp + tex
    body = body + M.cylinder(1.2, 1.6, 1.0, 20).translate([0, 0, plate_t + h_sp - 1.8])       # the spire's knop
    q = half - pin / 2 - 0.4
    for x in (-q, q):
        for y in (-q, q):
            shaft = box([x - pin / 2, y - pin / 2, plate_t - 0.01], [x + pin / 2, y + pin / 2, plate_t + pin_h])
            cap = M.hull_points([(x + a * pin / 2, y + c * pin / 2, plate_t + pin_h - 0.01) for a in (-1, 1) for c in (-1, 1)] +
                                [(x, y, plate_t + pin_h + pin * 1.6)])
            body = body + shaft + cap + M.sphere(0.75, 16).translate([x, y, plate_t + pin_h + pin * 1.6 + 0.3])
    return body


def cross_finial(h=11.0, arm=5.4, t=1.4):
    """A stone cross for the spire's tip, its arms carried on 45 degree brackets (prints
    upright). Local: centred, foot at z = 0."""
    a = arm / 2
    p = t / 2
    za = h * 0.62
    prof = poly([(-p, 0.0), (p, 0.0), (p, za - (a - p)), (a, za), (a, za + t), (p, za + t), (p, h), (-p, h), (-p, za + t),
                 (-a, za + t), (-a, za), (-p, za - (a - p))])
    return M.extrude(prof, t).translate([0, 0, -p]).transform(np.array([[1.0, 0, 0, 0], [0, 0, 1.0, 0], [0, 1.0, 0, 0]]))


# ------------------------------------------------------------------ the Millbrook's dormer (added after review)
def dormer_depot(w=24.0, dep=16.0, hwall=11.0, sg=0.9):
    """The Millbrook's dormer over the agent's bay: a gabled front of drop siding with a
    two-light window under a rayed head, a king-post truss in the peak, corner and raking boards.
    Local as the other dormers (u across, v up from its foot, w out from the face); returns
    (body, core, face)."""
    rise = w / 2 * sg
    face = poly([(-w / 2, 0.0), (w / 2, 0.0), (w / 2, hwall), (0.0, hwall + rise), (-w / 2, hwall)])
    inner = face.offset(-1.2, MJ, 4.0) ^ rect(-50, 1.2, 50, 999)
    body = ext(face, -dep, 0.0) - ext(inner, -dep - 1, -1.2)
    win = rect(-4.6, 2.4, 4.6, 8.4)
    trim = cs_union([rect(-w / 2, 0.0, -w / 2 + 1.1, hwall), rect(w / 2 - 1.1, 0.0, w / 2, hwall),
                     (face - face.offset(-1.1, MJ, 4.0)) ^ rect(-50, hwall - 0.01, 50, 999), rect(-w / 2, hwall - 0.9, w / 2, hwall + 0.2)])
    sid_reg = (face ^ rect(-50, 0.0, 50, hwall - 0.9)) - trim - win.offset(1.0, MJ, 4.0) - rect(-5.8, 0.9, 5.8, 2.4)
    body = body + depot_droplap(sid_reg, datum=0.0, pitch=1.5)
    body = body + ext(trim, -0.01, 0.8)
    body = body - ext(win, -1.3, 1.0)
    body = body + ext(win.offset(0.9, MJ, 4.0) - win, -0.01, 0.7)
    body = body + ext(cs_union([rect(-0.4, 2.4, 0.4, 8.4), rect(-4.6, 5.2, 4.6, 5.7)]) ^ win, -1.2, -0.4)
    body = body + chamfer_box(-5.8, 1.2, 5.8, 2.4, -0.01, 1.1, c=0.3, bottom=1.0)
    body = body + union(_ray_pediment(5.6, 9.29, 2.2, rays=5, proud=0.9))
    # the king-post truss in the peak, every member tied into the raking boards
    vc = hwall + 1.4
    xc = (hwall + rise - vc) / sg
    truss = cs_union([rect(-xc, vc - 0.45, xc, vc + 0.45), rect(-0.45, vc, 0.45, hwall + rise - 0.8),
                      stroke([(-xc * 0.55, vc + 0.3), (0.0, hwall + rise - 2.2)], 0.8, caps=False),
                      stroke([(xc * 0.55, vc + 0.3), (0.0, hwall + rise - 2.2)], 0.8, caps=False)]) ^ face.offset(-0.2, MJ, 4.0)
    body = body + ext(truss, -0.01, 0.7)
    core = ext(inner ^ rect(-50, 1.2, 50, hwall - 1.0), -dep + 1.2, -1.2)
    return body, core, face


def dormer_depot_roof(w, dep, hwall, sg=0.9, over=1.8, t=1.3, back=18.0, pitch=1.7):
    """The dormer's gable roof: a chevron slab over the face's rakes running back into the main
    roof, shingle courses grooved along it (local as dormer_depot)."""
    rise = w / 2 * sg
    a = w / 2 + over
    base_v = hwall - over * sg
    lift = t * math.sqrt(1 + sg * sg)
    outer = poly([(-a, base_v), (a, base_v), (0.0, hwall + rise + lift)])
    inner = poly([(-a - 5.0, base_v - 5.0 * sg), (a + 5.0, base_v - 5.0 * sg), (0.0, hwall + rise)])
    slab_ = outer - inner
    notches = []
    L = math.hypot(a, rise + over * sg)
    for k in np.arange(pitch, L - 0.4, pitch):
        f = k / L
        for sg_ in (-1, 1):
            notches.append(circle((sg_ * a * (1 - f), base_v + (hwall + rise + lift - base_v) * f), 0.22, 8))
    cs = slab_ - cs_union(notches)
    return max(ext(cs, -dep - back, over).decompose(), key=lambda m_: m_.volume())       # drop the notched-off tips


def clock_face(D=16.0, t=1.0):
    """A tower clock: a stone ring round a dial with twelve hour marks and the hands at ten past
    ten, a boss at the centre. Facade frame, centred on u = v = 0. Returns (whole, dial, marks)."""
    r = D / 2
    dial = ext(circle((0.0, 0.0), r + 1.8, 64), 0.0, t)
    ring = ext(circle((0.0, 0.0), r + 1.8, 64) - circle((0.0, 0.0), r + 0.2, 64), t - 0.01, t + 0.9)
    marks = []
    for k in range(12):
        a = math.pi / 2 - k * math.pi / 6
        ln = 1.8 if k % 3 == 0 else 1.1
        marks.append(stroke([((r - 0.8) * math.cos(a), (r - 0.8) * math.sin(a)), ((r - 0.8 - ln) * math.cos(a), (r - 0.8 - ln) * math.sin(a))], 0.55, caps=False))
    ah = math.pi / 2 - (10 + 10 / 60) * math.pi / 6
    am = math.pi / 2 - 10 * math.pi / 30
    marks.append(stroke([(0.0, 0.0), (r * 0.5 * math.cos(ah), r * 0.5 * math.sin(ah))], 0.8, caps=True))
    marks.append(stroke([(0.0, 0.0), (r * 0.78 * math.cos(am), r * 0.78 * math.sin(am))], 0.55, caps=True))
    marks.append(circle((0.0, 0.0), 0.9, 16))
    mk = ext(cs_union(marks), t - 0.01, t + 0.45)
    return dial + ring + mk, dial, mk

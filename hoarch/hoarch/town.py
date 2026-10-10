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
    lat = O.lozenges(g, pitch=max(lattice, 2.4))       # quarries fitted to the light, 0.9 mm leads
    sash = _glazed([ext(plug_cs, -pl, -0.6)], g, pl, lat, plug_cs)
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
    box_ = rect(-w / 2, 0.0, w / 2, hwall)
    inner = box_.offset(-1.2, MJ, 4.0) ^ rect(-50, 1.2, 50, hwall + 1.0)
    # an open-topped box with the gable only as a plate on its face: the roof is a solid cap on it
    body = ext(box_, -dep, 0.0) - ext(inner, -dep - 1, -1.2) + ext(face ^ rect(-50, hwall - 0.01, 50, 999), -1.2, 0.0)
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
    """The dormer's gable roof: a solid cap with a flat foot on the dormer box's top, running back
    into the main roof, open under the rakes in front of the gable plate, shingle courses grooved
    along it (local as dormer_depot). Prints upright on its foot."""
    rise = w / 2 * sg
    lift = t * math.sqrt(1 + sg * sg)
    a = (rise + lift) / sg                                   # the cap's half width at its flat foot (on the box's top)
    outer = poly([(-a, hwall), (a, hwall), (0.0, hwall + rise + lift)])
    face = poly([(-w / 2, hwall - 0.01), (w / 2, hwall - 0.01), (0.0, hwall + rise)]).offset(0.05, MJ, 4.0)
    notches = []
    L = math.hypot(a, rise + lift)
    for k in np.arange(pitch, L - 0.6, pitch):
        f = k / L
        for sg_ in (-1, 1):
            notches.append(circle((sg_ * a * (1 - f), hwall + (rise + lift) * f), 0.22, 8))
    cap = ext(outer - cs_union(notches), -dep - back, over) - ext(face, -1.21, over + 1.0)
    return max(cap.decompose(), key=lambda m_: m_.volume())


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


# ================================================================== 63 Harmon Town Hall
def brick_civic(region, datum=0.0, bands=()):
    """Red pressed brick in English cross bond (stretcher courses shifting half a brick in turn,
    a header course between), with smooth stone bands ``bands`` = [(v0, v1)] standing proud
    (Harmon Town Hall)."""
    if region.is_empty():
        return M()
    b = region.bounds()
    bh = 0.8
    out = M.extrude(region, 0.12)
    bricks = []
    for k in range(int(math.floor((b[1] - datum) / bh)) - 1, int(math.ceil((b[3] - datum) / bh)) + 1):
        v = datum + k * bh
        if k % 2:                                           # headers
            step, off = 1.2, 0.3
        else:                                               # stretchers, shifting half a brick every other time
            step, off = 2.4, (0.0 if (k // 2) % 2 == 0 else 1.2)
        for u in np.arange(b[0] - 2.4 + off, b[2] + 2.4, step):
            bricks.append(rect(u + 0.1, v + 0.1, u + step - 0.1, v + bh - 0.1))
    br = cs_union(bricks) ^ region
    stone = cs_union([rect(b[0] - 1, v0, b[2] + 1, v1) for v0, v1 in bands]) ^ region if bands else None
    if stone is not None:
        br = br - stone
    out = out + ext(br, 0.11, 0.35)
    if stone is not None and not stone.is_empty():
        out = out + ext(stone, 0.0, 0.6)
    return out


def foundation_cushion(reg, seed=0):
    """Cushion rustication: long limestone blocks whose faces swell like pillows, deep V joints
    between (Harmon Town Hall)."""
    b = reg.bounds()
    rng = np.random.default_rng(seed + 919)
    ch = 3.0
    out = [M.extrude(reg, 0.2)]
    for k, v in enumerate(np.arange(b[1], b[3] - 0.5, ch)):
        u = b[0] - (k % 2) * 3.0
        while u < b[2]:
            L = rng.uniform(5.6, 7.6)
            blk = rect(u + 0.25, v + 0.25, u + L - 0.25, min(v + ch, b[3]) - 0.25) ^ reg
            if not blk.is_empty():
                bb = blk.bounds()
                if bb[2] - bb[0] > 1.6 and bb[3] - bb[1] > 1.2:
                    out.append(chamfer_box(bb[0], bb[1], bb[2], bb[3], 0.19, 0.6, c=0.45))
            u += L
    return union(out)


def frieze_lambrequin(L, h, b, pitch, margin, pair, half):
    """A lambrequin: a band along the top from which pointed drapery tabs hang, each ending in a
    small bead, three to a bay (Harmon Town Hall)."""
    v0, v1 = 0.6, h - 0.6
    hh = v1 - v0
    parts = [rect(0.3, v1 - 0.9, L - 0.3, v1)]
    tw = max(1.8, min(pitch / 3.0, 3.2))
    n = int((L - 0.6) / tw)
    u0 = (L - n * tw) / 2
    for k in range(n):
        a = u0 + k * tw
        parts.append(poly([(a + 0.1, v1 - 0.85), (a + tw - 0.1, v1 - 0.85), (a + tw / 2, v0 + 0.9)]))
        parts.append(circle((a + tw / 2, v0 + 0.55), 0.5, 12))
    return [_st(cs_union(parts), b, 0.45)], []


def frieze_roundelpanel(L, h, b, pitch, margin, pair, half):
    """Between the brackets, a long sunk panel with a raised roundel at its middle; a plain face
    behind every bracket (Harmon Town Hall)."""
    v0, v1 = 0.6, h - 0.6
    out = []
    for uc, wd in CO._between(L, pitch, margin, pair, half + 0.6):
        if wd < 3.0:
            continue
        pan = rect(uc - wd / 2, v0, uc + wd / 2, v1)
        rim = pan - pan.offset(-0.5, MJ, 4.0)
        rnd = circle((uc, (v0 + v1) / 2), min(1.3, (v1 - v0) * 0.32), 20)
        out.append(_st(rim + rnd, b, 0.4))
    return out, []


def course_beadbar(L, h, b, pitch, margin, p):
    """Bead and bar: long bars and round beads in turn along a fillet."""
    vc = h / 2
    items = []
    u = 0.8
    while u < L - 1.4:
        items.append(rect(u, vc - 0.3, u + 1.3, vc + 0.3))
        items.append(circle((u + 1.9, vc), min(0.42, h * 0.3), 12))
        u += 2.5
    return [ext(rect(0.3, 0.05, L - 0.3, 0.3), b - 0.05, b + 0.25), ext(cs_union(items), b - 0.05, b + 0.4)]


def bracket_civicconsole(h, d, t):
    """A civic console: a stepped block head over an S-curved front that rolls into a scroll at
    the foot, an acorn drop hanging under it (side profile, top at v = 0)."""
    hb = max(3.0, h)
    head = [(0.0, 0.0), (d, 0.0), (d, -0.8), (d - 0.4, -0.8), (d - 0.4, -1.3)]
    s = [(d - 0.4 - (d - 1.6) * (3 * q * q - 2 * q ** 3), -1.3 - (hb - 2.5) * q) for q in np.linspace(0.05, 1.0, 10)]
    prof = poly(head + s + [(0.9, -hb + 1.0), (0.0, -hb + 1.0)])
    return cs_union([prof, circle((1.2, -hb + 1.2), 0.9, 16), circle((0.7, -hb + 0.5), 0.55, 12)])


CO.FRIEZE_EXTRA.update(lambrequin=frieze_lambrequin, roundelpanel=frieze_roundelpanel)
CO.COURSE_EXTRA.update(beadbar=course_beadbar)
TW.BRACKET_EXTRA.update(civicconsole=bracket_civicconsole)
TW.FOUNDATION_EXTRA.update(cushion=foundation_cushion)


def _sash(plug_cs, pl, rows=2, cols=2, arch_v=None):
    """Glazed sash in a plug: ``rows`` x ``cols`` lights (a meeting rail between the rows)."""
    g = plug_cs.offset(-0.5, RND)
    u0, v0, u1, v1 = g.bounds()
    bars = [rect(u0 - 1, v0 + (v1 - v0) * k / rows - 0.3, u1 + 1, v0 + (v1 - v0) * k / rows + 0.3) for k in range(1, rows)]
    bars += [rect(u0 + (u1 - u0) * k / cols - 0.22, v0 - 1, u0 + (u1 - u0) * k / cols + 0.22, v1 + 1) for k in range(1, cols)]
    return _glazed([ext(plug_cs, -pl, -0.6)], g, pl, cs_union(bars) if bars else None, plug_cs)


def window_civic_lower(w, h, A=1.4):
    """Harmon's ground-floor window: two-over-two sash under a segmental head, in a stone lintel
    of five raised voussoirs and a tall keystone, on a lugged sill."""
    rise = w * 0.18
    op = O.opening_cs(w, h, rise)
    plug_cs = op.offset(-O.CLR, RND)
    pl = O.PLUG
    sash = _sash(plug_cs, pl)
    s = h - rise
    lint = (op.offset(A + 1.6, RND) - op) ^ rect(-w, s - 0.6, w, 999)
    parts = [ext(op - op.offset(-RIB, RND), 0.0, 0.7), ext((op.offset(A, RND) - op) ^ rect(-w, 0.0, w, s), 0.0, 0.6),
             ext(lint, 0.0, 0.8)]
    vs = []
    R = 50.0
    cy = s - (w * w / 4 - rise * rise) / (2 * rise)
    for k in range(5):
        a0 = math.atan2(s + rise - cy, 0.0) - 0.6 + k * 0.24
        vs.append(poly([(0.0, cy), (R * math.cos(a0), cy + R * math.sin(a0)), (R * math.cos(a0 + 0.2), cy + R * math.sin(a0 + 0.2))]))
    parts.append(ext(lint ^ cs_union(vs), 0.79, 1.1))
    parts.append(chamfer_box(-1.0, h - 0.4, 1.0, h + A + 2.2, 0.0, 1.4, c=0.3))
    hw = w / 2 + A
    parts.append(chamfer_box(-hw - 1.0, -1.2, hw + 1.0, 0.2, 0.0, 1.4, c=0.4, bottom=0.8))
    return O._one_piece(sash, parts, op, plug_cs, pl, h + A + 2.2, -1.2)


def window_civic_upper(w, h, A=1.3):
    """Harmon's council-chamber window: a tall round-headed sash with radiating bars in its arch,
    under a moulded hood on two scrolled consoles with a keystone, on a sill with a panel apron."""
    op = O.opening_cs(w, h)
    plug_cs = op.offset(-O.CLR, RND)
    pl = O.PLUG
    g = plug_cs.offset(-0.5, RND)
    u0, v0, u1, v1 = g.bounds()
    s = h - w / 2
    bars = [rect(u0 - 1, s - 0.3, u1 + 1, s + 0.3), rect(u0 - 1, v0 + (s - v0) * 0.5 - 0.3, u1 + 1, v0 + (s - v0) * 0.5 + 0.3),
            rect(-0.22, v0 - 1, 0.22, s)]
    bars += [stroke([(0.0, s), (w * math.cos(a), s + w * math.sin(a))], 0.4, caps=False) for a in (math.pi / 4, 3 * math.pi / 4)]
    sash = _glazed([ext(plug_cs, -pl, -0.6)], g, pl, cs_union(bars), plug_cs)
    hood = (op.offset(A + 1.6, RND) - op.offset(A + 0.2, RND)) ^ rect(-w * 2, s, w * 2, 999)
    parts = [ext(op - op.offset(-RIB, RND), 0.0, 0.7), ext((op.offset(A, RND) - op) ^ rect(-w, 0.0, w, 999), 0.0, 0.6),
             ext(hood, 0.0, 1.3), chamfer_box(-1.0, h + 0.2, 1.0, h + A + 2.6, 0.0, 1.5, c=0.3)]
    x = w / 2 + A + 0.9
    for sg in (-1, 1):
        parts.append(ext(cs_union([rect(sg * x - 0.8, s - 3.0, sg * x + 0.8, s + 0.1), circle((sg * x, s - 3.0), 0.8, 14)]), 0.0, 1.3))
    hw = w / 2 + A
    parts.append(chamfer_box(-hw - 1.0, -1.2, hw + 1.0, 0.2, 0.0, 1.4, c=0.4, bottom=0.8))
    apron = rect(-hw + 0.6, -3.6, hw - 0.6, -1.19)
    parts.append(ext(apron, 0.0, 0.5))
    parts.append(ext(apron.offset(-0.6, MJ, 4.0) - apron.offset(-1.1, MJ, 4.0), 0.49, 0.8))
    return O._one_piece(sash, parts, op, plug_cs, pl, h + A + 2.6, -3.6)


def window_civicbelfry(w, h, A=1.4):
    """Harmon's belfry opening: a round arch on impost blocks filled with louvres, a keystone
    over it and a pilaster strip each side."""
    op = O.opening_cs(w, h)
    plug_cs = op.offset(-O.CLR, RND)
    pl = O.PLUG
    g = plug_cs.offset(-0.5, RND)
    sash = _glazed([ext(plug_cs, -pl, -0.6)], g, pl, None, plug_cs)
    sash.append(ext(cs_union([rect(-w, v, w, v + 0.8) for v in np.arange(1.0, h, 1.6)]) ^ g, -pl + O.GLASS - 0.01, -0.3))
    s = h - w / 2
    parts = [ext(op - op.offset(-RIB, RND), 0.0, 0.7), ext((op.offset(A, RND) - op) ^ rect(-w, s, w, 999), 0.0, 0.9),
             chamfer_box(-1.0, h - 0.2, 1.0, h + A + 1.2, 0.0, 1.3, c=0.3)]
    for sg in (-1, 1):
        x = sg * (w / 2 + A / 2)
        parts.append(chamfer_box(x - A / 2 - 0.4, s - 1.0, x + A / 2 + 0.4, s + 0.2, 0.0, 1.2, c=0.3))
        parts.append(ext(rect(x - A / 2, 0.0, x + A / 2, s - 0.99), 0.0, 0.8))
    parts.append(chamfer_box(-w / 2 - A - 0.8, -1.2, w / 2 + A + 0.8, 0.2, 0.0, 1.4, c=0.4, bottom=0.8))
    return O._one_piece(sash, parts, op, plug_cs, pl, h + A + 1.2, -1.2)


def door_civic(w=15.0, h=30.0):
    """Harmon's entrance: a pair of raised-panel leaves under a fanlight of radiating bars, in a
    rusticated arch of alternate long and short blocks with a keystone, between pilasters on
    plinths carrying an entablature."""
    op = O.opening_cs(w, h)
    plug_cs = op.offset(-O.CLR, RND)
    pl = O.PLUG
    s = h - w / 2
    fan = (plug_cs.offset(-0.5, RND) ^ rect(-w, s + 0.4, w, 999))
    body = [ext(plug_cs, -pl, -1.0)]
    leaves = plug_cs.offset(-0.3, RND) ^ rect(-w, 0.0, w, s - 0.3)
    body.append(ext(leaves, -1.0, -0.6))
    lb = leaves.bounds()
    for sg in (-1, 1):
        a, e = sorted((sg * 0.5, sg * (lb[2] - 0.2)))
        for (p0, p1) in ((1.0, (s - 0.3) * 0.42), ((s - 0.3) * 0.48, s - 1.2)):
            body.append(chamfer_box(a + 0.6, p0, e - 0.6, p1, -0.6, 0.35, c=0.2))
    body.append(ext(rect(-w, s - 0.3, w, s + 0.4) ^ plug_cs, -pl, -0.6))
    bars = cs_union([stroke([(0.0, s + 0.4), (w * math.cos(a), s + 0.4 + w * math.sin(a))], 0.45, caps=False)
                     for a in np.linspace(math.pi / 6, 5 * math.pi / 6, 5)] + [circle((0.0, s + 0.4), 1.4, 20) ^ rect(-3, s + 0.4, 3, s + 3)])
    sash = _glazed(body, fan, pl, bars, plug_cs)
    A = 2.2
    arch = (op.offset(A, RND) - op) ^ rect(-w * 2, s, w * 2, 999)
    parts = [ext(op - op.offset(-RIB, RND), 0.0, 0.7), ext((op.offset(A, RND) - op) ^ rect(-w * 2, 0.0, w * 2, s), 0.0, 0.8),
             ext(arch, 0.0, 0.8)]
    R = 60.0
    blocks = []
    n = 9
    for k in range(0, n, 2):
        a0, a1 = math.pi * k / n, math.pi * (k + 1) / n
        blocks.append(poly([(0.0, s), (R * math.cos(a0), s + R * math.sin(a0)), (R * math.cos(a1), s + R * math.sin(a1))]))
    parts.append(ext((op.offset(A + 1.0, RND) - op) ^ rect(-w * 2, s, w * 2, 999) ^ cs_union(blocks), 0.0, 1.2))
    parts.append(chamfer_box(-1.3, h - 0.3, 1.3, h + A + 2.2, 0.0, 1.6, c=0.35))
    xp = w / 2 + A + 2.2
    ztop = h + A + 2.2
    for sg in (-1, 1):
        parts.append(chamfer_box(sg * xp - 1.6, 0.0, sg * xp + 1.6, 3.2, 0.0, 1.8, c=0.4))
        parts.append(ext(rect(sg * xp - 1.3, 3.19, sg * xp + 1.3, ztop), 0.0, 1.3))
        parts.append(ext(cs_union([rect(sg * xp + d_ - 0.2, 4.2, sg * xp + d_ + 0.2, ztop - 1.2) for d_ in (-0.6, 0.0, 0.6)]), 1.29, 1.5))
    parts.append(ext(rect(-xp - 1.6, ztop - 0.01, xp + 1.6, ztop + 2.4), 0.0, 1.6))
    parts.append(chamfer_box(-xp - 2.2, ztop + 2.39, xp + 2.2, ztop + 3.4, 0.0, 2.2, c=0.5, bottom=1.2))
    return O._one_piece(sash, parts, op, plug_cs, pl, ztop + 3.4, 0.0)


def name_tablet(text, L, H=6.0, t=1.2, cap=3.0):
    """A carved stone tablet: a moulded border under a low pediment, raised capitals (facade
    frame, centred on u = 0, foot at v = 0). Returns (tablet, letters)."""
    from .storefront import text_cs
    b = rect(-L / 2, 0.0, L / 2, H)
    ped = poly([(-L / 2 - 0.8, H - 0.01), (L / 2 + 0.8, H - 0.01), (0.0, H + L * 0.12)])
    body = ext(b, 0.0, t) + ext(b - b.offset(-0.7, MJ, 4.0), t - 0.01, t + 0.5) + ext(ped, 0.0, t + 0.3)
    letters = text_cs(text, cap=cap, font="serif", track=0.3)
    lb = letters.bounds()
    sc = min(1.0, (L - 2.4) / max(1e-6, lb[2] - lb[0]))
    letters = letters.scale((sc, 1.0)).translate(((-(lb[0] + lb[2]) / 2) * sc, (H - cap) / 2 - lb[1]))
    lt = ext(letters, t - 0.01, t + 0.45)
    return body + lt, lt


def clock_civic(D=13.0, t=1.0):
    """Harmon's tower clock: a round dial with Roman-style bar numerals in a square stone frame
    with carved spandrels, a small pediment over it. Facade frame, centred on the dial.
    Returns (whole, dial, marks)."""
    r = D / 2
    sq = r + 2.0
    frame = ext(rect(-sq, -sq, sq, sq), 0.0, t) + ext(rect(-sq, -sq, sq, sq) - circle((0, 0), r + 0.3, 64), t - 0.01, t + 0.8)
    frame = frame + ext(poly([(-sq - 0.6, sq - 0.01), (sq + 0.6, sq - 0.01), (0.0, sq + 3.0)]), 0.0, t + 0.9)
    for x in (-1, 1):
        for y in (-1, 1):
            frame = frame + ext(circle((x * (sq - 1.2), y * (sq - 1.2)), 0.7, 12), t + 0.79, t + 1.1)
    dial = ext(circle((0, 0), r + 0.31, 64), 0.0, t)
    marks = []
    for k in range(12):
        a = math.pi / 2 - k * math.pi / 6
        n = 1 if k % 3 else 2
        for j in range(n):
            off = (j - (n - 1) / 2) * 0.55
            ca, sa = math.cos(a), math.sin(a)
            marks.append(stroke([((r - 0.7) * ca - off * sa, (r - 0.7) * sa + off * ca), ((r - 2.0) * ca - off * sa, (r - 2.0) * sa + off * ca)], 0.42, caps=False))
    ah = math.pi / 2 - (3 + 40 / 60) * math.pi / 6
    am = math.pi / 2 - 40 * math.pi / 30
    marks.append(stroke([(0.0, 0.0), (r * 0.5 * math.cos(ah), r * 0.5 * math.sin(ah))], 0.75, caps=True))
    marks.append(stroke([(0.0, 0.0), (r * 0.8 * math.cos(am), r * 0.8 * math.sin(am))], 0.5, caps=True))
    marks.append(circle((0, 0), 0.8, 14))
    mk = ext(cs_union(marks), t - 0.01, t + 0.4)
    return frame + dial + mk, dial, mk


def flagstaff(h=16.0, r=0.7):
    """A flagstaff for a tower roof: a pole with a gilt ball and a pennant whose foot rises at 45
    degrees from the pole (prints upright). Local: foot at z = 0."""
    pole = M.cylinder(h, r, r * 0.8, 16)
    ball = M.sphere(1.0, 16).translate([0, 0, h + 0.4])
    zp = h - 7.0
    pen = poly([(0.0, zp), (4.6, zp + 4.6), (4.6, zp + 5.4), (0.0, zp + 6.2)])
    pen = M.extrude(pen, 0.8).translate([0, 0, -0.4]).transform(np.array([[1.0, 0, 0, 0], [0, 0, 1.0, 0], [0, 1.0, 0, 0]]))
    return pole + ball + pen


# ================================================================== 64 Engine Company No. 3
def brick_firehouse(region, datum=0.0, soldiers=()):
    """Buff brick in American common bond (a course of headers every sixth), with soldier
    courses (bricks set on end, standing proud for the red) at ``soldiers`` = [v] (Engine No. 3)."""
    if region.is_empty():
        return M()
    b = region.bounds()
    bh = 0.8
    rows = []
    for k in range(int(math.floor((b[1] - datum) / bh)) - 1, int(math.ceil((b[3] - datum) / bh)) + 1):
        v = datum + k * bh
        step = 1.2 if k % 6 == 0 else 2.4
        off = 0.0 if k % 2 == 0 else step / 2
        rows += [rect(u + 0.1, v + 0.1, u + step - 0.1, v + bh - 0.1) for u in np.arange(b[0] - 2.4 + off, b[2] + 2.4, step)]
    sold = cs_union([rect(b[0] - 1, v, b[2] + 1, v + 2.0) for v in soldiers]) ^ region if soldiers else None
    br = cs_union(rows) ^ region
    if sold is not None:
        br = br - sold
    out = M.extrude(region, 0.12) + ext(br, 0.11, 0.35)
    if sold is not None and not sold.is_empty():
        sb = sold.bounds()
        ends = cs_union([rect(u - 0.1, sb[1] - 1, u + 0.1, sb[3] + 1) for u in np.arange(sb[0], sb[2], 0.8)])
        out = out + ext(sold, 0.0, 0.5) - ext(ends ^ sold, 0.3, 1.0)
    return out


def foundation_bevelgranite(reg, seed=0):
    """A granite water table: long smooth blocks in two courses, the upper one bevelled back at
    45 degrees along its top (Engine No. 3)."""
    b = reg.bounds()
    rng = np.random.default_rng(seed + 431)
    out = [M.extrude(reg, 0.25)]
    vm = b[1] + (b[3] - b[1]) * 0.5
    for (v0, v1, bev) in ((b[1], vm, False), (vm, b[3], True)):
        u = b[0] - rng.uniform(0.0, 5.0)
        while u < b[2]:
            L = rng.uniform(9.0, 14.0)
            blk = rect(u + 0.15, v0 + 0.15, u + L - 0.15, v1 - 0.15) ^ reg
            if not blk.is_empty():
                bb = blk.bounds()
                if bev:
                    out.append(chamfer_box(bb[0], bb[1], bb[2], bb[3], 0.24, 0.55, c=0.5, square=("v0", "u0", "u1")))
                else:
                    out.append(ext(blk, 0.24, 0.55))
            u += L
    return union(out)


def _maltese(c, r):
    """A Maltese cross: four arms widening outward, each notched at its end."""
    arms = []
    for k in range(4):
        a = k * math.pi / 2
        ca, sa = math.cos(a), math.sin(a)
        pts = [(0.18, 0.12), (1.0, 0.55), (0.8, 0.0), (1.0, -0.55), (0.18, -0.12)]
        arms.append(poly([(c[0] + r * (x * ca - y * sa), c[1] + r * (x * sa + y * ca)) for x, y in pts]))
    return cs_union(arms + [circle(c, r * 0.28, 12)])


def frieze_maltese(L, h, b, pitch, margin, pair, half):
    """A Maltese cross at every station, a twisted hose-rope line running between them
    (Engine No. 3)."""
    v0, v1 = 0.6, h - 0.6
    vc = (v0 + v1) / 2
    out = []
    for u in CO._us(L, pitch, margin, 0.0):
        out.append(_st(_maltese((u, vc), min(1.9, (v1 - v0) * 0.46)), b, 0.45))
    for uc, wd in CO._between(L, pitch, margin, pair, half + 2.4):
        if wd < 2.0:
            continue
        rope = [stroke([(x, vc - 0.45), (x + 0.9, vc + 0.45)], 0.45, caps=False) for x in np.arange(uc - wd / 2, uc + wd / 2 - 0.9, 0.7)]
        out.append(_st(cs_union(rope) ^ rect(uc - wd / 2, vc - 0.8, uc + wd / 2, vc + 0.8), b, 0.35))
    return out, []


def frieze_flames(L, h, b, pitch, margin, pair, half):
    """A row of flame tongues rising from a fillet, tall and short in turn (Engine No. 3)."""
    v0, v1 = 0.6, h - 0.6
    hh = v1 - v0
    parts = [rect(0.3, v0, L - 0.3, v0 + 0.7)]
    k = 0
    for u in np.arange(1.2, L - 1.0, 1.9):
        top = v0 + hh * (0.95 if k % 2 == 0 else 0.62)
        parts.append(poly([(u - 0.75, v0 + 0.6), (u + 0.75, v0 + 0.6), (u + 0.5, v0 + (top - v0) * 0.55), (u + 0.1, top),
                           (u - 0.25, v0 + (top - v0) * 0.6)]))
        k += 1
    return [_st(cs_union(parts), b, 0.45)], []


def course_rungs(L, h, b, pitch, margin, p):
    """A ladder laid along the course: two rails and a rung every 1.6 mm."""
    rails = cs_union([rect(0.3, 0.1, L - 0.3, 0.45), rect(0.3, h - 0.45, L - 0.3, h - 0.1)])
    rungs = cs_union([rect(u - 0.25, 0.3, u + 0.25, h - 0.3) for u in np.arange(0.9, L - 0.6, 1.6)])
    return [ext(rails, b - 0.05, b + 0.4), ext(rungs, b - 0.05, b + 0.3)]


def bracket_hook(h, d, t):
    """A pike-pole bracket: a square head along the soffit, a straight drop, and a hook curling
    out and up at the foot, the hook's bow filled solid (side profile, top at v = 0)."""
    hb = max(3.0, h)
    r = min(1.2, d * 0.35)
    pts = [(0.0, 0.0), (d, 0.0), (d, -0.9), (1.1, -0.9), (1.1, -hb + 2 * r)]
    pts += [(1.1 + r - r * math.cos(a), -hb + 2 * r - r * math.sin(a) - 0.0) for a in np.linspace(0.0, math.pi, 10)]
    pts += [(1.1 + 2 * r, -hb + 2 * r + 0.6), (0.0, -hb + 2 * r + 0.6)]
    return cs_union([poly(pts), rect(0.0, -hb + 2 * r - 0.01, 1.1 + 2 * r, -hb + 2 * r + 0.61), circle((1.1 + r, -hb + r), r, 16)])


CO.FRIEZE_EXTRA.update(maltese=frieze_maltese, flames=frieze_flames)
CO.COURSE_EXTRA.update(rungs=course_rungs)
TW.BRACKET_EXTRA.update(hook=bracket_hook)
TW.FOUNDATION_EXTRA.update(bevelgranite=foundation_bevelgranite)


def _rowlock(op, s, A, rows=2):
    """A rowlock arch of ``rows`` rings of bricks on end round a round or segmental head."""
    out = []
    for k in range(rows):
        ring = (op.offset(A + 1.2 * (k + 1), RND) - op.offset(A + 1.2 * k, RND)) ^ rect(-100, s, 100, 999)
        R = 60.0
        n = 26 + 6 * k
        joints = cs_union([stroke([(0.0, s), (R * math.cos(math.pi * j / n), s + R * math.sin(math.pi * j / n))], 0.18, caps=False)
                           for j in range(1, n)])
        out.append(ext(ring, 0.0, 0.7 + 0.25 * k) - ext(joints ^ ring, 0.45 + 0.25 * k, 2.0))
    return out


def door_apparatus(w=26.0, h=36.0):
    """An engine-house door: a pair of tall leaves, each with six lights over X-braced panels,
    under a fanlight of radiating bars, in a round arch of two rowlock rings with a stone
    keystone and impost blocks."""
    op = O.opening_cs(w, h)
    plug_cs = op.offset(-O.CLR, RND)
    pl = O.PLUG
    s = h - w / 2
    body = [ext(plug_cs, -pl, -1.0), ext(plug_cs - plug_cs.offset(-0.5, RND), -pl, 0.0)]
    glass = []
    lw = (w - 2 * O.CLR - 1.0) / 2
    for sg in (-1, 1):
        a, e = sorted((sg * 0.5, sg * (0.5 + lw)))
        leaf = rect(a, 0.3, e, s - 0.3)
        body.append(ext(leaf, -1.0, -0.6))
        gl = rect(a + 1.0, s * 0.5, e - 1.0, s - 1.3)
        gb = gl.bounds()
        for i in range(2):
            for j in range(3):
                glass.append(rect(gb[0] + (gb[2] - gb[0]) * i / 2 + 0.25, gb[1] + (gb[3] - gb[1]) * j / 3 + 0.25,
                                  gb[0] + (gb[2] - gb[0]) * (i + 1) / 2 - 0.25, gb[1] + (gb[3] - gb[1]) * (j + 1) / 3 - 0.25))
        pan = rect(a + 1.0, 1.4, e - 1.0, s * 0.5 - 1.2)
        pb = pan.bounds()
        body.append(ext(pan - pan.offset(-0.55, MJ, 4.0), -0.6, -0.25))
        body.append(ext(cs_union([stroke([(pb[0] + 0.4, pb[1] + 0.4), (pb[2] - 0.4, pb[3] - 0.4)], 0.55),
                                  stroke([(pb[0] + 0.4, pb[3] - 0.4), (pb[2] - 0.4, pb[1] + 0.4)], 0.55)]) ^ pan, -0.6, -0.2))
    fan = plug_cs.offset(-0.5, RND) ^ rect(-w, s + 0.4, w, 999)
    glass.append(fan)
    body.append(ext(rect(-w, s - 0.3, w, s + 0.4) ^ plug_cs, -pl, -0.6))
    bars = cs_union([stroke([(0.0, s + 0.4), (w * math.cos(a), s + 0.4 + w * math.sin(a))], 0.5, caps=False)
                     for a in np.linspace(math.pi / 8, 7 * math.pi / 8, 7)])
    sash = _glazed(body, cs_union(glass), pl, bars, plug_cs)
    parts = [ext(op - op.offset(-RIB, RND), 0.0, 0.7), ext((op.offset(1.4, RND) - op) ^ rect(-w, 0.0, w, s), 0.0, 0.7)]
    parts += _rowlock(op, s, 0.0, rows=2)
    parts.append(chamfer_box(-1.6, h + 0.6, 1.6, h + 3.4, 0.0, 1.6, c=0.35))
    for sg in (-1, 1):
        parts.append(chamfer_box(sg * (w / 2 + 1.3) - 1.8, s - 1.4, sg * (w / 2 + 1.3) + 1.8, s + 0.2, 0.0, 1.4, c=0.3))
    return O._one_piece(sash, parts, op, plug_cs, pl, h + 3.4, 0.0)


def window_fire_upper(w, h):
    """The engine house's upper window: a tall one-over-one sash under a segmental head of two
    rowlock rings, a stone keystone, a stone sill on brick corbels."""
    rise = w * 0.2
    op = O.opening_cs(w, h, rise)
    plug_cs = op.offset(-O.CLR, RND)
    pl = O.PLUG
    sash = _sash(plug_cs, pl, rows=2, cols=1)
    s = h - rise
    parts = [ext(op - op.offset(-RIB, RND), 0.0, 0.7), ext((op.offset(1.2, RND) - op) ^ rect(-w, 0.0, w, s), 0.0, 0.6)]
    parts += _rowlock(op, s, 0.0, rows=2)
    parts.append(chamfer_box(-1.1, h + 0.4, 1.1, h + 2.9, 0.0, 1.4, c=0.3))
    hw = w / 2 + 1.2
    parts.append(chamfer_box(-hw - 0.8, -1.2, hw + 0.8, 0.2, 0.0, 1.4, c=0.4, bottom=0.8))
    for sg in (-1, 1):
        parts.append(chamfer_box(sg * (hw - 0.4) - 0.9, -2.6, sg * (hw - 0.4) + 0.9, -1.19, 0.0, 0.9, c=0.25, bottom=0.9))
    return O._one_piece(sash, parts, op, plug_cs, pl, h + 2.9, -2.6)


def window_fire_lower(w, h):
    """The engine house's ground-floor window: two-over-two sash under a flat stone lintel with
    a raised centre block and eared ends, on a plain stone sill."""
    op = O.opening_cs(w, h, 0)
    plug_cs = op.offset(-O.CLR, MJ, 4.0)
    pl = O.PLUG
    sash = _sash(plug_cs, pl, rows=2, cols=2)
    hw = w / 2 + 1.2
    parts = [ext(op - op.offset(-RIB, MJ, 4.0), 0.0, 0.7), ext((op.offset(1.2, MJ, 4.0) - op) ^ rect(-w, 0.0, w, h), 0.0, 0.6),
             chamfer_box(-hw - 1.2, h - 0.01, hw + 1.2, h + 2.6, 0.0, 1.2, c=0.3, bottom=0.8),
             chamfer_box(-2.0, h + 0.4, 2.0, h + 2.9, 0.0, 1.6, c=0.35),
             chamfer_box(-hw - 0.8, -1.2, hw + 0.8, 0.2, 0.0, 1.3, c=0.4, bottom=0.8)]
    return O._one_piece(sash, parts, op, plug_cs, pl, h + 2.9, -1.2)


def window_hoseslit(w, h):
    """A slit light in the hose tower: tall and narrow under a round head, a stone sill."""
    op = O.opening_cs(w, h)
    plug_cs = op.offset(-O.CLR, RND)
    pl = O.PLUG
    sash = _sash(plug_cs, pl, rows=1, cols=1)
    s = h - w / 2
    parts = [ext(op - op.offset(-RIB, RND), 0.0, 0.7), ext((op.offset(1.0, RND) - op) ^ rect(-w, 0.0, w, 999), 0.0, 0.6)]
    parts += _rowlock(op, s, 1.0, rows=1)
    parts.append(chamfer_box(-w / 2 - 1.4, -1.0, w / 2 + 1.4, 0.2, 0.0, 1.2, c=0.35, bottom=0.8))
    return O._one_piece(sash, parts, op, plug_cs, pl, h + 2.2, -1.0)


def window_hoselouvre(w, h):
    """The hose tower's drying vents: a louvred round-headed opening under a rowlock ring."""
    op = O.opening_cs(w, h)
    plug_cs = op.offset(-O.CLR, RND)
    pl = O.PLUG
    g = plug_cs.offset(-0.5, RND)
    sash = _glazed([ext(plug_cs, -pl, -0.6)], g, pl, None, plug_cs)
    sash.append(ext(cs_union([rect(-w, v, w, v + 0.8) for v in np.arange(1.0, h, 1.5)]) ^ g, -pl + O.GLASS - 0.01, -0.3))
    s = h - w / 2
    parts = [ext(op - op.offset(-RIB, RND), 0.0, 0.7), ext((op.offset(1.0, RND) - op) ^ rect(-w, 0.0, w, 999), 0.0, 0.6)]
    parts += _rowlock(op, s, 1.0, rows=1)
    parts.append(chamfer_box(-w / 2 - 1.4, -1.0, w / 2 + 1.4, 0.2, 0.0, 1.2, c=0.35, bottom=0.8))
    return O._one_piece(sash, parts, op, plug_cs, pl, h + 2.2, -1.0)


def door_fire_rear(w=11.0, h=25.0):
    """The engine house's back door: a four-panel leaf with a transom light, under a segmental
    rowlock head."""
    rise = w * 0.18
    op = O.opening_cs(w, h, rise)
    plug_cs = op.offset(-O.CLR, RND)
    pl = O.PLUG
    s = h - rise
    ht = s - 4.0
    body = [ext(plug_cs, -pl, -1.0), ext(plug_cs - plug_cs.offset(-0.5, RND), -pl, 0.0),
            ext(rect(-w / 2, 0.3, w / 2, ht) ^ plug_cs, -1.0, -0.6), ext(rect(-w / 2, ht, w / 2, ht + 0.7) ^ plug_cs, -pl, -0.6)]
    for (a, e) in ((-w / 2 + 1.0, -0.5), (0.5, w / 2 - 1.0)):
        for (p0, p1) in ((1.2, ht * 0.45), (ht * 0.52, ht - 1.0)):
            body.append(chamfer_box(a, p0, e, p1, -0.6, 0.35, c=0.2))
    tr = plug_cs.offset(-0.5, RND) ^ rect(-w, ht + 0.7, w, 999)
    sash = _glazed(body, tr, pl, None, plug_cs)
    parts = [ext(op - op.offset(-RIB, RND), 0.0, 0.7), ext((op.offset(1.2, RND) - op) ^ rect(-w, 0.0, w, s), 0.0, 0.6)]
    parts += _rowlock(op, s, 0.0, rows=2)
    return O._one_piece(sash, parts, op, plug_cs, pl, h + 2.4, 0.0)


def tablet_fire(text, L, H=6.0, t=1.2, cap=3.0):
    """The engine house's name stone: a tablet with a round-arched top and a raised rim, raised
    capitals (facade frame, centred on u = 0, foot at v = 0). Returns (tablet, letters)."""
    from .storefront import text_cs
    b = cs_union([rect(-L / 2, 0.0, L / 2, H), circle((0.0, H), L / 2, 64) ^ rect(-L / 2, H, L / 2, H + L / 2)])
    Ht = H + L * 0.22
    b = b ^ rect(-L / 2, 0.0, L / 2, Ht)
    body = ext(b, 0.0, t) + ext(b - b.offset(-0.7, RND), t - 0.01, t + 0.5)
    letters = text_cs(text, cap=cap, font="serif", track=0.3)
    lb = letters.bounds()
    sc = min(1.0, (L - 4.4) / max(1e-6, lb[2] - lb[0]))
    letters = letters.scale((sc, 1.0)).translate(((-(lb[0] + lb[2]) / 2) * sc, (Ht - cap) / 2 - lb[1]))
    lt = ext(letters, t - 0.01, t + 0.45)
    return body + lt, lt


def chimney_firehouse(w=9.0, d=7.0, h=20.0):
    """The engine house's stack: buff brick with a red soldier band, three corbelled courses and
    a stone cap with a low hood."""
    h = round(h / 0.2) * 0.2
    zt = h - 3.6
    body = box([-w / 2, -d / 2, 0.0], [w / 2, d / 2, zt])
    body = body + TW._skin(w, d, 0.0, zt - 0.2, lambda reg, i: brick_firehouse(reg, soldiers=(zt - 4.0,)))
    z = zt
    for k in range(3):
        g = 0.3 * (k + 1)
        body = body + box([-w / 2 - g, -d / 2 - g, z - 0.01], [w / 2 + g, d / 2 + g, z + 0.6])
        z += 0.6
    body = body + box([-w / 2 - 1.1, -d / 2 - 1.1, z - 0.01], [w / 2 + 1.1, d / 2 + 1.1, z + 0.6])
    body = body + M.hull_points([(x * (w / 2 + 1.1), y * (d / 2 + 1.1), z + 0.59) for x in (-1, 1) for y in (-1, 1)] +
                                [(x * (w / 2 - 1.5), y * (d / 2 - 1.5), h) for x in (-1, 1) for y in (-1, 1)])
    return body


def finial_blockball(h=9.0):
    """The hose tower's finial: a square block on a neck, a ball and a short spike (prints
    upright). Local: foot at z = 0."""
    return (box([-1.4, -1.4, 0.0], [1.4, 1.4, 2.2]) + M.cylinder(2.0, 0.8, 0.6, 16).translate([0, 0, 2.19]) +
            M.sphere(1.3, 20).translate([0, 0, 5.2]) + M.cylinder(h - 6.2, 0.45, 0.2, 12).translate([0, 0, 6.2]))


def apron_setts(w, depth, rise):
    """A granite-sett apron sloping from the ground up to the engine-house floor: ``w`` wide,
    ``depth`` out from the wall, ``rise`` high at the wall. Local: u across (centred), v up,
    w out from the wall (its back face at w = 0)."""
    from .ornament import side_profile
    body = side_profile([(0.0, 0.0), (depth, 0.0), (depth, 0.4), (0.0, rise)], -w / 2, w / 2)
    slope = (rise - 0.4) / depth
    grooves = [box([-w / 2 - 1, -2.0, x - 0.1], [w / 2 + 1, rise + 2.0, x + 0.1]) for x in np.arange(1.8, depth, 1.4)]
    top = M.hull_points([(-w / 2 - 1, rise + 1.0, 0.0), (w / 2 + 1, rise + 1.0, 0.0), (-w / 2 - 1, rise + 1.0, depth + 1), (w / 2 + 1, rise + 1.0, depth + 1)] +
                        [(-w / 2 - 1, rise - 0.15, 0.0), (w / 2 + 1, rise - 0.15, 0.0), (-w / 2 - 1, 0.4 - 0.15 - slope, depth + 1), (w / 2 + 1, 0.4 - 0.15 - slope, depth + 1)])
    band = union([g for g in grooves]) ^ top
    cols = union([box([u - 0.1, -2.0, -1.0], [u + 0.1, rise + 2, depth + 1]) for u in np.arange(-w / 2 + 1.8, w / 2, 1.8)]) ^ top
    return body - band - cols


# ================================================================== 65 Lakeshore Freight House
def shiplap_alternating(region, datum=0.0, wide=2.2, narrow=1.2):
    """Shiplap in alternating wide and narrow courses, each with a square rebate shadow at its
    foot (the Lakeshore Freight House)."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    lines = []
    v = datum - 4 * (wide + narrow)
    k = 0
    while v < v1 + wide:
        lines.append(rect(u0 - 1, v - 0.2, u1 + 1, v + 0.2))
        v += wide if k % 2 == 0 else narrow
        k += 1
    return M.extrude(region, 0.4) - ext(cs_union(lines) ^ region, 0.15, 1.0)


def foundation_crib(reg, seed=0):
    """A timber crib: squared timbers laid in courses, their ends showing where the courses
    cross at intervals (the Lakeshore Freight House)."""
    b = reg.bounds()
    th = 1.6
    out = [M.extrude(reg, 0.2)]
    for k, v in enumerate(np.arange(b[1], b[3] - 0.4, th)):
        out.append(ext(rect(b[0] - 1, v + 0.12, b[2] + 1, v + th - 0.12) ^ reg, 0.19, 0.55))
        for u in np.arange(b[0] + (4.0 if k % 2 else 10.0), b[2] - 1.0, 12.0):
            end = rect(u, v + 0.12, u + th - 0.24, v + th - 0.12) ^ reg
            if not end.is_empty():
                out.append(ext(end, 0.54, 0.85))
    return union(out)


def frieze_rivetplates(L, h, b, pitch, margin, pair, half):
    """Riveted iron plates at every station, a flat bar with rivets between them (the Lakeshore
    Freight House)."""
    v0, v1 = 0.6, h - 0.6
    out = []
    pw = min(pitch * 0.55, 6.0)
    for u in CO._us(L, pitch, margin, 0.0):
        pl_ = rect(u - pw / 2, v0, u + pw / 2, v1)
        riv = cs_union([circle((x, y), 0.32, 10) for x in (u - pw / 2 + 0.7, u + pw / 2 - 0.7)
                        for y in np.linspace(v0 + 0.7, v1 - 0.7, max(2, int((v1 - v0) / 1.3)))])
        out.append(_st(pl_ - pl_.offset(-0.2, MJ, 4.0), b, 0.3))
        out.append(_st(pl_.offset(-0.2, MJ, 4.0), b, 0.25))
        out.append(_st(riv ^ pl_, b, 0.45))
    for uc, wd in CO._between(L, pitch, margin, pair, half + pw / 2 + 0.4):
        if wd < 2.0:
            continue
        vc = (v0 + v1) / 2
        bar = rect(uc - wd / 2, vc - 0.5, uc + wd / 2, vc + 0.5)
        riv = cs_union([circle((x, vc), 0.3, 10) for x in np.arange(uc - wd / 2 + 0.8, uc + wd / 2 - 0.5, 1.6)])
        out.append(_st(bar, b, 0.3))
        out.append(_st(riv ^ bar, b, 0.45))
    return out, []


def course_boltheads(L, h, b, pitch, margin, p):
    """Square bolt heads on round washers along a plain fillet."""
    vc = h / 2
    wash = cs_union([circle((u, vc), min(0.55, h * 0.36), 12) for u in np.arange(1.0, L - 0.6, 2.0)])
    heads = cs_union([rect(u - 0.3, vc - 0.3, u + 0.3, vc + 0.3) for u in np.arange(1.0, L - 0.6, 2.0)])
    return [ext(rect(0.3, 0.1, L - 0.3, h - 0.1), b - 0.05, b + 0.2), ext(wash, b - 0.05, b + 0.35), ext(heads, b + 0.3, b + 0.5)]


def bracket_dockbrace(h, d, t):
    """A dock-shed brace: a plumb post on the wall, a long diagonal strut out to the soffit's edge,
    the triangle between them filled solid with a bolt plate at the joint (side profile, top at
    v = 0)."""
    hb = max(4.0, h)
    return cs_union([poly([(0.0, 0.0), (d, 0.0), (d, -0.9), (1.0, -hb + 0.8), (1.0, -hb), (0.0, -hb)]),
                     rect(0.0, -hb * 0.55, 1.6, -hb * 0.55 + 1.8)])


CO.FRIEZE_EXTRA.update(rivetplates=frieze_rivetplates)
CO.COURSE_EXTRA.update(boltheads=course_boltheads)
TW.BRACKET_EXTRA.update(dockbrace=bracket_dockbrace)
TW.FOUNDATION_EXTRA.update(crib=foundation_crib)


def door_freightx(w=20.0, h=28.0):
    """A freight house door: a sliding leaf framed round a cross-buck, the fields between filled
    with diagonal boards, hung from a track under a sheet-iron hood that runs on past the opening."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, MJ, 4.0)
    pl = O.PLUG
    leaf = rect(-w / 2 - 0.8, 0.2, w / 2 + 0.8, h + 0.6)
    lb = leaf.bounds()
    inner = leaf.offset(-1.4, MJ, 4.0)
    ib = inner.bounds()
    diag = cs_union([stroke([(x, ib[1] - 1), (x + (ib[3] - ib[1]) + 2, ib[3] + 1)], 0.2, caps=False)
                     for x in np.arange(ib[0] - (ib[3] - ib[1]) - 2, ib[2] + 2, 1.3)]) ^ inner
    body = [ext(plug_cs, -pl, 0.0), ext(leaf, 0.0, 0.8) - ext(diag, 0.55, 1.0)]
    frame = (leaf - inner) + cs_union([stroke([(ib[0], ib[1]), (ib[2], ib[3])], 1.3, caps=False),
                                       stroke([(ib[0], ib[3]), (ib[2], ib[1])], 1.3, caps=False),
                                       rect(ib[0], (ib[1] + ib[3]) / 2 - 0.6, ib[2], (ib[1] + ib[3]) / 2 + 0.6)]) ^ leaf
    body.append(ext(frame, 0.79, 1.3))
    tr0, tr1 = -w / 2 - 1.6, w / 2 + w * 0.85
    body.append(ext(rect(tr0, h + 1.0, tr1, h + 2.0), 0.0, 1.5))
    hood = poly([(tr0 - 0.4, h + 1.9), (tr1 + 0.4, h + 1.9), (tr1 + 0.4, h + 3.6), (tr0 - 0.4, h + 3.6)])
    body.append(chamfer_box(tr0 - 0.4, h + 1.99, tr1 + 0.4, h + 3.6, 0.0, 2.2, c=0.8, square=("v1", "u0", "u1")))
    for u in (-w / 4, w / 4):
        body.append(ext(rect(u - 0.8, h - 1.2, u + 0.8, h + 1.4), 0.79, 1.4))
    return O._one_piece(body, [ext(op - op.offset(-RIB, MJ, 4.0), 0.0, 0.5)], op, plug_cs, pl, h + 3.6, 0.0)


def window_freight(w=8.0, h=8.0):
    """A freight house light: a fixed sash of four panes in a flat casing under a drip cap."""
    op = O.opening_cs(w, h, 0)
    plug_cs = op.offset(-O.CLR, MJ, 4.0)
    pl = O.PLUG
    sash = _sash(plug_cs, pl, rows=2, cols=2)
    parts = [ext(op - op.offset(-RIB, MJ, 4.0), 0.0, 0.7), ext(op.offset(1.2, MJ, 4.0) - op, 0.0, 0.6),
             chamfer_box(-w / 2 - 1.8, h + 1.19, w / 2 + 1.8, h + 2.0, 0.0, 1.2, c=0.3, bottom=1.0),
             chamfer_box(-w / 2 - 1.4, -1.2, w / 2 + 1.4, 0.2, 0.0, 1.2, c=0.35, bottom=0.8)]
    return O._one_piece(sash, parts, op, plug_cs, pl, h + 2.0, -1.2)


def door_office(w=10.0, h=24.0):
    """The freight agent's door: four lights over two tall panels, a transom over, in a flat
    casing under a drip cap."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, MJ, 4.0)
    pl = O.PLUG
    ht = h - 4.0
    body = [ext(plug_cs, -pl, -1.0), ext(plug_cs - plug_cs.offset(-0.5, MJ, 4.0), -pl, 0.0),
            ext(rect(-w / 2, 0.3, w / 2, ht) ^ plug_cs, -1.0, -0.6), ext(rect(-w / 2, ht, w / 2, ht + 0.7) ^ plug_cs, -pl, -0.6)]
    gl = rect(-w / 2 + 1.1, ht * 0.52, w / 2 - 1.1, ht - 1.0)
    for a, e in ((-w / 2 + 1.1, -0.4), (0.4, w / 2 - 1.1)):
        body.append(chamfer_box(a, 1.2, e, ht * 0.52 - 1.0, -0.6, 0.35, c=0.2))
    gb = gl.bounds()
    bars = cs_union([rect((gb[0] + gb[2]) / 2 - 0.22, gb[1] - 1, (gb[0] + gb[2]) / 2 + 0.22, gb[3] + 1),
                     rect(gb[0] - 1, (gb[1] + gb[3]) / 2 - 0.22, gb[2] + 1, (gb[1] + gb[3]) / 2 + 0.22)])
    tr = plug_cs.offset(-0.5, MJ, 4.0) ^ rect(-w, ht + 0.7, w, 999)
    sash = _glazed(body, gl + tr, pl, bars, plug_cs)
    parts = [ext(op - op.offset(-RIB, MJ, 4.0), 0.0, 0.7), ext((op.offset(1.3, MJ, 4.0) - op) ^ rect(-w, 0.0, w, h + 1.3), 0.0, 0.6),
             chamfer_box(-w / 2 - 2.0, h + 1.29, w / 2 + 2.0, h + 2.2, 0.0, 1.3, c=0.3, bottom=1.0)]
    return O._one_piece(sash, parts, op, plug_cs, pl, h + 2.2, 0.0)


def skirt_dockcrib(reg, d=1.2):
    """The dock's face: a heavy timber fascia over cribbed timbers with their ends showing."""
    if reg.is_empty():
        return M()
    u0, v0, u1, v1 = reg.bounds()
    body = M.extrude(reg, d * 0.5)
    fas = rect(u0 - 1, v1 - 2.2, u1 + 1, v1) ^ reg
    lines = cs_union([rect(u0 - 1, v - 0.12, u1 + 1, v + 0.12) for v in np.arange(v1 - 2.2, v0, -1.6)]) ^ reg
    ends = cs_union([rect(u, v - 1.4, u + 1.4, v) for v in np.arange(v1 - 2.4, v0 + 1.4, -3.2)
                     for u in np.arange(u0 + 3.0, u1 - 2.0, 9.0)]) ^ reg.offset(-0.3, MJ, 4.0)
    return body - ext(lines, d * 0.35, d) + ext(fas, 0.0, d * 0.7) + ext(ends, d * 0.49, d * 0.8)


PW.SKIRTS.update(dockcrib=skirt_dockcrib)


def sign_freight(text, L, H=5.0, t=1.0, cap=3.0):
    """A long painted sign board with a raised rim and raised capitals (facade frame, centred on
    u = 0, foot at v = 0). Returns (board, letters)."""
    from .storefront import text_cs
    b = rect(-L / 2, 0.0, L / 2, H)
    board = ext(b, 0.0, t) + ext(b - b.offset(-0.6, MJ, 4.0), t - 0.01, t + 0.4)
    letters = text_cs(text, cap=cap, font="sans" if False else "serif", track=0.6)
    lb = letters.bounds()
    sc = min(1.0, (L - 2.0) / max(1e-6, lb[2] - lb[0]))
    letters = letters.scale((sc, 1.0)).translate(((-(lb[0] + lb[2]) / 2) * sc, (H - cap) / 2 - lb[1]))
    lt = ext(letters, t - 0.01, t + 0.4)
    return board + lt, lt


# ================================================================== 66 Pleasant Valley School
def lap_german(region, datum=0.0, pitch=1.6, corners=()):
    """German (cove) siding: each course a flat board whose top is cut in a hollow under the
    board above, a crisp line at its foot; flat corner boards at ``corners`` (u positions)
    (Pleasant Valley School)."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    k0 = math.floor((v0 - datum) / pitch) - 1
    ks = range(k0, k0 + int((v1 - v0) / pitch) + 4)
    lines = cs_union([rect(u0 - 1, datum + k * pitch - 0.15, u1 + 1, datum + k * pitch + 0.15) for k in ks])
    coves = cs_union([rect(u0 - 1, datum + k * pitch + 0.15, u1 + 1, datum + k * pitch + 0.75) for k in ks])
    out = M.extrude(region, 0.4) - ext(lines ^ region, 0.1, 1.0) - ext(coves ^ region, 0.28, 1.0)
    if corners:
        out = out + ext(cs_union([rect(u - 0.9, v0 - 1, u + 0.9, v1 + 1) for u in corners]) ^ region, 0.0, 0.85)
    return out


def foundation_pierlattice(reg, seed=0):
    """Brick piers at intervals with diagonal lattice between them (Pleasant Valley School)."""
    b = reg.bounds()
    out = [M.extrude(reg, 0.15)]
    piers = []
    for u in np.arange(b[0] + 0.5, b[2], 16.0):
        pr = rect(u, b[1], u + 4.0, b[3]) ^ reg
        if not pr.is_empty():
            piers.append(pr)
    pc = cs_union(piers) if piers else None
    lat = []
    H = b[3] - b[1]
    for x in np.arange(b[0] - H, b[2] + H, 1.8):
        lat.append(stroke([(x, b[1]), (x + H, b[3])], 0.45, caps=False))
        lat.append(stroke([(x + H, b[1]), (x, b[3])], 0.45, caps=False))
    field = reg.offset(-0.6, MJ, 4.0)
    if pc is not None:
        field = field - pc.offset(0.3, MJ, 4.0)
        bricks = SK.brick_bond(pc, "running", bl=2.0, bh=0.7, d=0.25)
        out.append(ext(pc, 0.14, 0.5) + bricks.translate([0, 0, 0.49]))
    out.append(ext(cs_union(lat) ^ field, 0.14, 0.5))
    out.append(ext((reg - reg.offset(-0.6, MJ, 4.0)) ^ rect(b[0] - 1, b[3] - 0.9, b[2] + 1, b[3] + 1), 0.14, 0.7))
    return union(out)


def frieze_bellflowers(L, h, b, pitch, margin, pair, half):
    """Between the brackets, a stem with three small hanging bells (Pleasant Valley School)."""
    v0, v1 = 0.6, h - 0.6
    out = []
    for uc, wd in CO._between(L, pitch, margin, pair, half + 0.8):
        if wd < 3.5:
            continue
        parts = [rect(uc - wd / 2 + 0.3, v1 - 0.6, uc + wd / 2 - 0.3, v1)]
        for k, dx in enumerate((-wd * 0.28, 0.0, wd * 0.28)):
            x = uc + dx
            ln = (v1 - v0) * (0.55 if k == 1 else 0.38)
            parts.append(rect(x - 0.22, v1 - ln, x + 0.22, v1 - 0.5))
            bell = poly([(x - 0.35, v1 - ln + 0.05), (x + 0.35, v1 - ln + 0.05), (x + 0.75, v1 - ln - 1.2), (x - 0.75, v1 - ln - 1.2)])
            parts.append(bell)
        out.append(_st(cs_union(parts) ^ rect(0.0, v0, L, v1), b, 0.45))
    return out, []


def course_abacus(L, h, b, pitch, margin, p):
    """A counting frame: a thin rod along the course with beads strung in groups of five."""
    vc = h / 2
    rod = rect(0.3, vc - 0.18, L - 0.3, vc + 0.18)
    beads = []
    u = 1.0
    while u < L - 4.5:
        for k in range(5):
            beads.append(circle((u + k * 0.75, vc), min(0.36, h * 0.25), 10))
        u += 5.4
    return [ext(rod, b - 0.05, b + 0.25), ext(cs_union(beads), b - 0.05, b + 0.45)]


def bracket_schoolscroll(h, d, t):
    """A sawn scroll bracket: a C-scroll under the soffit, its tail running down the wall into a
    teardrop (side profile, top at v = 0)."""
    hb = max(3.0, h)
    r = min(d * 0.42, hb * 0.3)
    pts = [(0.0, 0.0), (d, 0.0)] + [(d - r + r * math.cos(a), -r + r * math.sin(a)) for a in np.linspace(0.0, -math.pi * 0.8, 10)]
    pts += [(0.8, -hb + 1.0), (0.0, -hb + 1.0)]
    return cs_union([poly(pts), circle((0.5, -hb + 0.9), 0.6, 14)])


CO.FRIEZE_EXTRA.update(bellflowers=frieze_bellflowers)
CO.COURSE_EXTRA.update(abacus=course_abacus)
TW.BRACKET_EXTRA.update(schoolscroll=bracket_schoolscroll)
TW.FOUNDATION_EXTRA.update(pierlattice=foundation_pierlattice)


def window_school(w, h):
    """The schoolroom window: tall six-over-six sash in flat casings under a head cap on two
    small blocks, on a sill."""
    op = O.opening_cs(w, h, 0)
    plug_cs = op.offset(-O.CLR, MJ, 4.0)
    pl = O.PLUG
    g = plug_cs.offset(-0.5, MJ, 4.0)
    u0, v0, u1, v1 = g.bounds()
    vm = (v0 + v1) / 2
    bars = [rect(u0 - 1, vm - 0.35, u1 + 1, vm + 0.35)]
    for vv in (v0 + (vm - v0) / 2, vm + (v1 - vm) / 2):
        bars.append(rect(u0 - 1, vv - 0.2, u1 + 1, vv + 0.2))
    for uu in (u0 + (u1 - u0) / 3, u0 + 2 * (u1 - u0) / 3):
        bars.append(rect(uu - 0.2, v0 - 1, uu + 0.2, v1 + 1))
    sash = _glazed([ext(plug_cs, -pl, -0.6)], g, pl, cs_union(bars), plug_cs)
    hw = w / 2 + 1.4
    parts = [ext(op - op.offset(-RIB, MJ, 4.0), 0.0, 0.7), ext((op.offset(1.4, MJ, 4.0) - op) ^ rect(-w, 0.0, w, h + 1.4), 0.0, 0.6),
             ext(rect(-hw, h + 1.39, hw, h + 3.0), 0.0, 0.7),
             chamfer_box(-hw - 1.4, h + 2.99, hw + 1.4, h + 4.0, 0.0, 1.5, c=0.4, bottom=1.1)]
    for sg in (-1, 1):
        parts.append(chamfer_box(sg * hw - 0.7, h + 1.4, sg * hw + 0.7, h + 3.0, 0.0, 1.1, c=0.25))
    parts.append(chamfer_box(-hw - 0.8, -1.2, hw + 0.8, 0.2, 0.0, 1.3, c=0.4, bottom=0.8))
    return O._one_piece(sash, parts, op, plug_cs, pl, h + 4.0, -1.2)


def door_school(w=16.0, h=28.0):
    """The school's doors: a pair of four-panel leaves under a three-light transom, sheltered by a
    gabled hood on two scroll brackets."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, MJ, 4.0)
    pl = O.PLUG
    ht = h - 5.0
    body = [ext(plug_cs, -pl, -1.0), ext(plug_cs - plug_cs.offset(-0.5, MJ, 4.0), -pl, 0.0),
            ext(rect(-w / 2, 0.3, w / 2, ht) ^ plug_cs, -1.0, -0.6), ext(rect(-w / 2, ht, w / 2, ht + 0.7) ^ plug_cs, -pl, -0.6),
            ext(rect(-0.25, 0.3, 0.25, ht), -1.0, -0.4)]
    for sg in (-1, 1):
        a, e = sorted((sg * 0.7, sg * (w / 2 - 0.9)))
        for (p0, p1) in ((1.0, ht * 0.3), (ht * 0.36, ht - 0.9)):
            for (q0, q1) in ((a, (a + e) / 2 - 0.3), ((a + e) / 2 + 0.3, e)):
                body.append(chamfer_box(q0, p0, q1, p1, -0.6, 0.35, c=0.2))
    tw = (w - 2 * O.CLR - 2.4) / 3
    tr = cs_union([rect(-w / 2 + O.CLR + 0.6 + k * (tw + 0.6), ht + 1.3, -w / 2 + O.CLR + 0.6 + k * (tw + 0.6) + tw, h - O.CLR - 0.6)
                   for k in range(3)])
    sash = _glazed(body, tr, pl, None, plug_cs)
    hw = w / 2 + 1.5
    parts = [ext(op - op.offset(-RIB, MJ, 4.0), 0.0, 0.7), ext((op.offset(1.5, MJ, 4.0) - op) ^ rect(-w, 0.0, w, h + 1.5), 0.0, 0.7)]
    # the hood: a gabled canopy on two scroll brackets, its underside 45 degrees back to the wall
    hd = 4.0
    zh = h + 1.5
    rise = (hw + 2.0) * 0.55
    from .ornament import side_profile
    for sg in (-1, 1):
        br = side_profile([(0.0, zh), (hd, zh), (hd - 0.6, zh - 1.2), (0.9, zh - 5.5), (0.0, zh - 5.5)], sg * hw - 0.6, sg * hw + 0.6)
        parts.append(br.transform(np.array([[1.0, 0, 0, 0], [0, 1.0, 0, 0], [0, 0, 1.0, 0]])))
    tri = poly([(-hw - 2.0, zh), (hw + 2.0, zh), (0.0, zh + rise)])
    hood = M.extrude(tri, hd).transform(np.array([[1.0, 0, 0, 0], [0, 1.0, 0, 0], [0, 0, 1.0, 0]]))
    parts.append(hood)
    parts.append(ext(tri - tri.offset(-0.9, MJ, 4.0), hd - 0.01, hd + 0.6))
    return O._one_piece(sash, parts, op, plug_cs, pl, zh + rise, 0.0)


def belfry_school(w=16.0, h0=10.0, hl=11.0, s=1.5):
    """The school's belfry, one piece printed upright: a square base (its foot sits on a flat seat
    in the ridge), a louvred stage with corner posts, a flared cornice, a steep pyramid with
    45-degree eaves and a ball finial. Local: centred, z = 0 at the foot."""
    base = box([-w / 2, -w / 2, 0.0], [w / 2, w / 2, h0])
    wi = w - 2.0
    stage = box([-wi / 2, -wi / 2, h0 - 0.01], [wi / 2, wi / 2, h0 + hl])
    slats = []
    for k, (ax, sg) in enumerate(((0, 1), (0, -1), (1, 1), (1, -1))):
        for z in np.arange(h0 + 1.2, h0 + hl - 1.2, 1.3):
            y0, y1 = sorted((sg * (wi / 2 - 0.9), sg * (wi / 2 + 0.3)))
            if ax == 0:
                slats.append(box([-wi / 2 + 1.5, y0, z], [wi / 2 - 1.5, y1, z + 0.6]))
            else:
                slats.append(box([y0, -wi / 2 + 1.5, z], [y1, wi / 2 - 1.5, z + 0.6]))
    recess = union([box([-wi / 2 + 1.6, -wi / 2 - 1, h0 + 0.8], [wi / 2 - 1.6, wi / 2 + 1, h0 + hl - 0.8]),
                    box([-wi / 2 - 1, -wi / 2 + 1.6, h0 + 0.8], [wi / 2 + 1, wi / 2 - 1.6, h0 + hl - 0.8])])
    stage = stage - (recess - box([-wi / 2 + 0.8, -wi / 2 + 0.8, 0], [wi / 2 - 0.8, wi / 2 - 0.8, 100])) + union(slats)
    zc = h0 + hl
    corn = M.hull_points([(x * wi / 2, y * wi / 2, zc - 0.01) for x in (-1, 1) for y in (-1, 1)] +
                         [(x * (w / 2 + 0.6), y * (w / 2 + 0.6), zc + 1.4) for x in (-1, 1) for y in (-1, 1)])
    corn = corn + box([-(w / 2 + 0.6), -(w / 2 + 0.6), zc + 1.39], [w / 2 + 0.6, w / 2 + 0.6, zc + 2.0])
    a = w / 2 + 1.6
    zr = zc + 2.0
    pyr = M.hull_points([(x * (w / 2 + 0.6), y * (w / 2 + 0.6), zr - 0.01) for x in (-1, 1) for y in (-1, 1)] +
                        [(x * a, y * a, zr + 1.0) for x in (-1, 1) for y in (-1, 1)] + [(0.0, 0.0, zr + 1.0 + s * a)])
    ball = M.sphere(1.2, 18).translate([0, 0, zr + 1.0 + s * a + 0.8]) + M.cylinder(1.0, 0.7, 0.7, 12).translate([0, 0, zr + 1.0 + s * a - 0.6])
    return base + stage + corn + pyr + ball


def chimney_school(w=8.0, d=8.0, h=16.0):
    """The stove flue at the back gable: a plain brick stack with a projecting band and a
    stepped cap."""
    h = round(h / 0.2) * 0.2
    zt = h - 2.4
    body = box([-w / 2, -d / 2, 0.0], [w / 2, d / 2, zt])
    body = body + TW._skin(w, d, 0.0, zt - 0.2, lambda reg, i: SK.brick_bond(reg, "english", bl=2.2, bh=0.75, d=0.25))
    body = body + box([-w / 2 - 0.5, -d / 2 - 0.5, zt - 3.0], [w / 2 + 0.5, d / 2 + 0.5, zt - 2.2])
    body = body + box([-w / 2 - 0.6, -d / 2 - 0.6, zt - 0.01], [w / 2 + 0.6, d / 2 + 0.6, zt + 1.2])
    body = body + box([-w / 2 + 0.6, -d / 2 + 0.6, zt + 1.19], [w / 2 - 0.6, d / 2 - 0.6, h])
    return body - box([-w / 2 + 1.8, -d / 2 + 1.8, h - 1.4], [w / 2 - 1.8, d / 2 - 1.8, h + 1])


def board_school(text, L, H=5.0, t=1.0, cap=2.6):
    """The school's name board: a long board with round ends and a raised rim, raised capitals
    (facade frame, centred on u = 0, foot at v = 0). Returns (board, letters)."""
    from .storefront import text_cs
    b = cs_union([rect(-L / 2 + H / 2, 0.0, L / 2 - H / 2, H), circle((-L / 2 + H / 2, H / 2), H / 2, 24),
                  circle((L / 2 - H / 2, H / 2), H / 2, 24)])
    board = ext(b, 0.0, t) + ext(b - b.offset(-0.6, RND), t - 0.01, t + 0.4)
    letters = text_cs(text, cap=cap, font="serif", track=0.35)
    lb = letters.bounds()
    sc = min(1.0, (L - H - 1.0) / max(1e-6, lb[2] - lb[0]))
    letters = letters.scale((sc, 1.0)).translate(((-(lb[0] + lb[2]) / 2) * sc, (H - cap) / 2 - lb[1]))
    lt = ext(letters, t - 0.01, t + 0.4)
    return board + lt, lt


# ================================================================== 67 Thorne Livery
def boards_butted(region, datum=0.0, pitch=1.8, seed=0):
    """Rough horizontal boards, each course broken by butt joints at random along it (the Thorne
    Livery)."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    rng = np.random.default_rng(seed + 71)
    cuts = []
    k0 = math.floor((v0 - datum) / pitch) - 1
    for k in range(k0, k0 + int((v1 - v0) / pitch) + 4):
        v = datum + k * pitch
        cuts.append(rect(u0 - 1, v - 0.18, u1 + 1, v + 0.18))
        u = u0 + rng.uniform(4.0, 40.0)
        while u < u1:
            cuts.append(rect(u - 0.15, v, u + 0.15, v + pitch))
            u += rng.uniform(26.0, 48.0)
    return M.extrude(region, 0.4) - ext(cs_union(cuts) ^ region, 0.15, 1.0)


def foundation_cobble(reg, seed=0):
    """River cobbles set in mortar, packed in rough rows (the Thorne Livery)."""
    b = reg.bounds()
    rng = np.random.default_rng(seed + 523)
    stones = []
    for k, v in enumerate(np.arange(b[1] + 0.9, b[3], 1.9)):
        u = b[0] + rng.uniform(0.0, 1.2)
        while u < b[2]:
            r = rng.uniform(0.7, 1.05)
            stones.append(circle((u + r, v + rng.uniform(-0.2, 0.2)), r, 14))
            u += 2 * r + rng.uniform(0.15, 0.4)
    st = cs_union(stones) ^ reg.offset(-0.2, MJ, 4.0)
    return M.extrude(reg, 0.25) + ext(st, 0.24, 0.6) + ext(st.offset(-0.35, RND), 0.59, 0.75)


def frieze_horseshoes(L, h, b, pitch, margin, pair, half):
    """A horseshoe at every station, points up for luck, with its nail holes, a thin rail
    between (the Thorne Livery)."""
    v0, v1 = 0.6, h - 0.6
    vc = (v0 + v1) / 2
    out = []
    for u in CO._us(L, pitch, margin, 0.0):
        r = min(1.9, (v1 - v0) * 0.45)
        shoe = (circle((u, vc), r, 32) - circle((u, vc), r - 0.75, 32)) - rect(u - r * 0.55, vc + r * 0.35, u + r * 0.55, vc + r + 1)
        out.append(_st(shoe, b, 0.45))
    for uc, wd in CO._between(L, pitch, margin, pair, half + 2.4):
        if wd < 2.0:
            continue
        out.append(_st(rect(uc - wd / 2, vc - 0.3, uc + wd / 2, vc + 0.3), b, 0.3))
    return out, []


def course_snaffles(L, h, b, pitch, margin, p):
    """Snaffle bits in a row: two rings joined by a jointed bar."""
    vc = h / 2
    r = min(0.55, h * 0.34)
    parts = []
    for u in np.arange(1.2, L - 3.0, 3.6):
        parts += [circle((u, vc), r, 14) - circle((u, vc), r - 0.28, 12), circle((u + 2.4, vc), r, 14) - circle((u + 2.4, vc), r - 0.28, 12),
                  rect(u + r - 0.1, vc - 0.2, u + 2.4 - r + 0.1, vc + 0.2)]
    return [ext(cs_union(parts), b - 0.05, b + 0.4)]


def bracket_ogeebrace(h, d, t):
    """An ogee brace: a solid sweep from the wall to the soffit whose outer edge is an S curve,
    a round peg at the joint (side profile, top at v = 0)."""
    hb = max(3.0, h)
    pts = [(0.0, 0.0), (d, 0.0)] + [(d - (d - 0.8) * s_, -hb * s_ - 0.5 * math.sin(2 * math.pi * s_)) for s_ in np.linspace(0.05, 1.0, 12)]
    pts += [(0.0, -hb)]
    return cs_union([poly(pts), circle((0.6, -hb + 0.6), 0.5, 12)])


CO.FRIEZE_EXTRA.update(horseshoes=frieze_horseshoes)
CO.COURSE_EXTRA.update(snaffles=course_snaffles)
TW.BRACKET_EXTRA.update(ogeebrace=bracket_ogeebrace)
TW.FOUNDATION_EXTRA.update(cobble=foundation_cobble)


def door_stable(w=30.0, h=34.0):
    """The livery's big doors: a pair of hinged leaves in heavy frames, each field boarded in a
    chevron, long strap hinges with round ends, under a plain head casing and drip cap."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, MJ, 4.0)
    pl = O.PLUG
    body = [ext(plug_cs, -pl, -1.0), ext(plug_cs - plug_cs.offset(-0.5, MJ, 4.0), -pl, 0.0)]
    for sg in (-1, 1):
        a, e = sorted((sg * 0.3, sg * (w / 2 - O.CLR)))
        leaf = rect(a, 0.3, e, h - O.CLR)
        body.append(ext(leaf, -1.0, -0.6))
        fld = leaf.offset(-1.4, MJ, 4.0)
        fb = fld.bounds()
        mid = (fb[1] + fb[3]) / 2
        for (q0, q1) in ((fb[1], mid - 0.6), (mid + 0.6, fb[3])):
            f_ = rect(fb[0], q0, fb[2], q1)
            xc = (fb[0] + fb[2]) / 2
            grooves = cs_union([stroke([(xc, y), (xc - 20, y - 20)], 0.2, caps=False) for y in np.arange(q0 - 20, q1 + 20, 1.3)] +
                               [stroke([(xc, y), (xc + 20, y - 20)], 0.2, caps=False) for y in np.arange(q0 - 20, q1 + 20, 1.3)] +
                               [rect(xc - 0.15, q0, xc + 0.15, q1)]) ^ f_
            body.append(ext(f_, -0.6, -0.45) - ext(grooves, -0.55, 0.0))
        for v in (h * 0.2, h * 0.75):
            st_ = cs_union([rect(min(sg * 0.8, sg * (w / 2 - 3.0)), v - 0.4, max(sg * 0.8, sg * (w / 2 - 3.0)), v + 0.4),
                            circle((sg * (w / 2 - 3.0), v), 0.8, 12)])
            body.append(ext(st_ ^ leaf, -0.61, -0.3))
    parts = [ext(op - op.offset(-RIB, MJ, 4.0), 0.0, 0.7), ext((op.offset(1.6, MJ, 4.0) - op) ^ rect(-w, 0.0, w, h + 1.6), 0.0, 0.8),
             chamfer_box(-w / 2 - 2.4, h + 1.59, w / 2 + 2.4, h + 2.6, 0.0, 1.4, c=0.35, bottom=1.0)]
    return O._one_piece(body, parts, op, plug_cs, pl, h + 2.6, 0.0)


def door_hay(w=14.0, h=14.0):
    """The hay-loft door: a pair of small board leaves with a Z brace each, in a plain frame."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, MJ, 4.0)
    pl = O.PLUG
    body = [ext(plug_cs, -pl, -1.0), ext(plug_cs - plug_cs.offset(-0.5, MJ, 4.0), -pl, 0.0), ext(plug_cs.offset(-0.3, MJ, 4.0), -1.0, -0.6)]
    grooves = cs_union([rect(u - 0.15, -1, u + 0.15, h + 1) for u in np.arange(-w / 2 + 1.2, w / 2, 1.2)]) ^ plug_cs
    body[2] = body[2] - ext(grooves, -0.8, -0.5)
    for sg in (-1, 1):
        a, e = sorted((sg * 0.6, sg * (w / 2 - 0.9)))
        z = cs_union([rect(a, 1.2, e, 2.4), rect(a, h - 2.6, e, h - 1.4), stroke([(a + 0.5, 2.0), (e - 0.5, h - 2.0)], 1.0, caps=False)])
        body.append(ext(z, -0.61, -0.25))
    parts = [ext(op - op.offset(-RIB, MJ, 4.0), 0.0, 0.7), ext((op.offset(1.2, MJ, 4.0) - op), 0.0, 0.7)]
    return O._one_piece(body, parts, op, plug_cs, pl, h + 1.2, -1.2)


def window_stall(w=7.0, h=7.0):
    """A stall window: a four-light sash in a plain frame with a board sill."""
    op = O.opening_cs(w, h, 0)
    plug_cs = op.offset(-O.CLR, MJ, 4.0)
    pl = O.PLUG
    sash = _sash(plug_cs, pl, rows=2, cols=2)
    parts = [ext(op - op.offset(-RIB, MJ, 4.0), 0.0, 0.7), ext(op.offset(1.1, MJ, 4.0) - op, 0.0, 0.6),
             chamfer_box(-w / 2 - 1.6, -1.1, w / 2 + 1.6, 0.2, 0.0, 1.2, c=0.35, bottom=0.8)]
    return O._one_piece(sash, parts, op, plug_cs, pl, h + 1.1, -1.1)


def door_dutch(w=10.0, h=22.0):
    """A stall's Dutch door: the leaf split across the middle, each half boarded with a cross
    brace, a ledge on the lower half, strap hinges."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, MJ, 4.0)
    pl = O.PLUG
    leaf = plug_cs.offset(-0.3, MJ, 4.0)
    grooves = cs_union([rect(u - 0.15, -1, u + 0.15, h + 1) for u in np.arange(-w / 2 + 1.2, w / 2, 1.2)] +
                       [rect(-w, h * 0.52 - 0.2, w, h * 0.52 + 0.2)]) ^ leaf
    body = [ext(plug_cs, -pl, -1.0), ext(plug_cs - plug_cs.offset(-0.5, MJ, 4.0), -pl, 0.0), ext(leaf, -1.0, -0.6) - ext(grooves, -0.85, -0.5)]
    lb = leaf.bounds()
    for (q0, q1) in ((lb[1] + 0.6, h * 0.52 - 0.6), (h * 0.52 + 0.6, lb[3] - 0.6)):
        body.append(ext(cs_union([stroke([(lb[0] + 0.8, q0 + 0.4), (lb[2] - 0.8, q1 - 0.4)], 0.9, caps=False),
                                  rect(lb[0] + 0.5, q0, lb[2] - 0.5, q0 + 0.9), rect(lb[0] + 0.5, q1 - 0.9, lb[2] - 0.5, q1)]), -0.61, -0.25))
    body.append(chamfer_box(lb[0], h * 0.52 - 0.2, lb[2], h * 0.52 + 0.8, -0.61, 1.2, c=0.3, bottom=0.9))
    parts = [ext(op - op.offset(-RIB, MJ, 4.0), 0.0, 0.7), ext((op.offset(1.2, MJ, 4.0) - op) ^ rect(-w, 0.0, w, h + 1.2), 0.0, 0.6)]
    return O._one_piece(body, parts, op, plug_cs, pl, h + 1.2, 0.0)


def hay_hood(w=22.0, rise=10.0, depth=10.0, t=1.4):
    """The hay hood: a small gabled canopy standing out from the gable over the loft door, a
    square hoist beam under its ridge. Facade frame (u across, v up from the hood's foot, w out);
    prints on its back face (the flat that glues to the gable)."""
    outer = poly([(-w / 2, 0.0), (w / 2, 0.0), (0.0, rise)])
    inner = poly([(-w / 2 + t * 1.6, -0.01), (w / 2 - t * 1.6, -0.01), (0.0, rise - t * 1.9)])
    shell = ext(outer, 0.0, depth) - ext(inner, 1.2, depth + 1.0)
    rake = ext(outer - outer.offset(-0.9, MJ, 4.0), depth - 0.01, depth + 0.6)
    beam = ext(rect(-0.9, rise - t * 1.9 - 2.4, 0.9, rise - t * 1.9 + 0.2), 0.0, depth + 1.6)
    hook = ext(rect(-0.3, rise - t * 1.9 - 4.2, 0.3, rise - t * 1.9 - 2.3), depth + 0.4, depth + 1.0)
    return shell + rake + beam + hook


def _horse():
    """A trotting horse in silhouette for the weathervane, about 6 mm long, facing +u."""
    pts = [(0.0, 1.4), (0.4, 1.9), (1.2, 2.3), (3.6, 2.3), (4.3, 2.9), (4.9, 3.8), (5.6, 3.9), (6.0, 3.4), (5.3, 3.1), (4.9, 2.4),
           (4.8, 1.6), (5.4, 0.6), (5.2, 0.4), (4.4, 1.3), (4.0, 1.4), (3.6, 0.2), (3.2, 0.2), (3.4, 1.4), (1.6, 1.4), (1.1, 0.2),
           (0.7, 0.2), (0.9, 1.5), (0.4, 1.6)]
    return poly(pts)


def cupola_livery(w=18.0, h0=9.0, hl=10.0, s=1.1):
    """The livery's ventilator cupola, one piece printed upright: a base that sits on a seat in
    the ridge, louvred sides between corner boards, a flared eave, a steep hip and a weathervane
    (a trotting horse over the points of the compass). Local: centred, z = 0 at its foot."""
    base = box([-w / 2, -w / 2, 0.0], [w / 2, w / 2, h0])
    wi = w - 1.6
    stage = box([-wi / 2, -wi / 2, h0 - 0.01], [wi / 2, wi / 2, h0 + hl])
    cut = union([box([-wi / 2 + 1.4, -wi / 2 - 1, h0 + 0.8], [wi / 2 - 1.4, wi / 2 + 1, h0 + hl - 0.8]),
                 box([-wi / 2 - 1, -wi / 2 + 1.4, h0 + 0.8], [wi / 2 + 1, wi / 2 - 1.4, h0 + hl - 0.8])])
    core = box([-wi / 2 + 0.8, -wi / 2 + 0.8, 0.0], [wi / 2 - 0.8, wi / 2 - 0.8, 100.0])
    stage = stage - (cut - core)
    slats = []
    for z in np.arange(h0 + 1.3, h0 + hl - 1.2, 1.2):
        for sg in (-1, 1):
            y0, y1 = sorted((sg * (wi / 2 - 0.9), sg * (wi / 2 + 0.1)))
            slats.append(M.hull_points([(x, y, z + dz) for x in (-wi / 2 + 1.2, wi / 2 - 1.2) for (y, dz) in ((y0, 0.0), (y1, 0.0), (y0, 0.7), (y1, 0.3))]))
            slats.append(M.hull_points([(y, x, z + dz) for x in (-wi / 2 + 1.2, wi / 2 - 1.2) for (y, dz) in ((y0, 0.0), (y1, 0.0), (y0, 0.7), (y1, 0.3))]))
    zc = h0 + hl
    a = w / 2 + 1.4
    eave = M.hull_points([(x * wi / 2, y * wi / 2, zc - 0.01) for x in (-1, 1) for y in (-1, 1)] +
                         [(x * a, y * a, zc + 1.4) for x in (-1, 1) for y in (-1, 1)])
    hipr = M.hull_points([(x * a, y * a, zc + 1.39) for x in (-1, 1) for y in (-1, 1)] + [(0.0, 0.0, zc + 1.4 + s * a)])
    zt = zc + 1.4 + s * a
    rod = M.cylinder(9.0, 0.45, 0.45, 12).translate([0, 0, zt - 1.0])
    arms = union([box([-2.4, -0.3, zt + 2.6], [2.4, 0.3, zt + 3.2]), box([-0.3, -2.4, zt + 2.6], [0.3, 2.4, zt + 3.2])])
    horse = M.extrude(_horse().translate((-3.0, 0.0)), 0.8).translate([0, 0, -0.4]).transform(
        np.array([[1.0, 0, 0, 0], [0, 0, 1.0, 0], [0, 1.0, 0, 0]])).translate([0, 0, zt + 5.0])
    ball = M.sphere(0.9, 14).translate([0, 0, zt + 0.6])
    return base + stage + union(slats) + eave + hipr + rod + arms + horse + ball


def board_livery(text, L, H=6.0, t=1.0, cap=3.2):
    """The livery's sign: a board with swallowtail ends and a raised rim, raised capitals (facade
    frame, centred on u = 0, foot at v = 0). Returns (board, letters)."""
    from .storefront import text_cs
    n = 2.2
    b = poly([(-L / 2, 0.0), (L / 2, 0.0), (L / 2 - n, H / 2), (L / 2, H), (-L / 2, H), (-L / 2 + n, H / 2)])
    board = ext(b, 0.0, t) + ext(b - b.offset(-0.6, MJ, 4.0), t - 0.01, t + 0.4)
    letters = text_cs(text, cap=cap, font="serif", track=0.35)
    lb = letters.bounds()
    sc = min(1.0, (L - 2 * n - 1.6) / max(1e-6, lb[2] - lb[0]))
    letters = letters.scale((sc, 1.0)).translate(((-(lb[0] + lb[2]) / 2) * sc, (H - cap) / 2 - lb[1]))
    lt = ext(letters, t - 0.01, t + 0.4)
    return board + lt, lt


# ================================================================== 68 MX Tower (interlocking tower)
def brick_raked(region, datum=0.0, every=5):
    """Red brick in stretcher bond with every ``every``-th course raked back, reading as
    horizontal shadow bands (MX Tower's lower storey)."""
    if region.is_empty():
        return M()
    b = region.bounds()
    bh = 0.8
    bricks = []
    for k in range(int(math.floor((b[1] - datum) / bh)) - 1, int(math.ceil((b[3] - datum) / bh)) + 1):
        if k % every == every - 1:
            continue
        v = datum + k * bh
        off = 0.0 if k % 2 == 0 else 1.2
        bricks += [rect(u + 0.1, v + 0.1, u + 2.3, v + bh - 0.1) for u in np.arange(b[0] - 2.4 + off, b[2] + 2.4, 2.4)]
    return M.extrude(region, 0.1) + ext(cs_union(bricks) ^ region, 0.09, 0.35)


def boards_panelled(region, datum=0.0, rails=(), pitch=1.1):
    """Narrow vertical beaded boards framed into panels by flat horizontal rails at ``rails``
    (v positions) (MX Tower's operating floor)."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    grooves = cs_union([rect(u - 0.16, v0 - 1, u + 0.16, v1 + 1) for u in np.arange(u0 + pitch / 2, u1, pitch)])
    out = M.extrude(region, 0.35) - ext(grooves ^ region, 0.15, 1.0)
    if rails:
        out = out + ext(cs_union([rect(u0 - 1, v - 0.8, u1 + 1, v + 0.8) for v in rails]) ^ region, 0.0, 0.75)
    return out


def foundation_scoredconcrete(reg, seed=0):
    """A poured concrete plinth scored into long panels, a chamfered wash along its top (MX
    Tower)."""
    b = reg.bounds()
    out = M.extrude(reg, 0.45)
    lines = cs_union([rect(u - 0.12, b[1] - 1, u + 0.12, b[3] - 0.9) for u in np.arange(b[0] + 9.0, b[2], 9.0)])
    out = out - ext(lines ^ reg, 0.3, 1.0)
    wash = rect(b[0] - 1, b[3] - 0.9, b[2] + 1, b[3] + 1) ^ reg
    return out + ext(wash, 0.44, 0.7)


def frieze_levers(L, h, b, pitch, margin, pair, half):
    """A lever frame: interlocking levers standing in a row, each a bar with a round handle and a
    latch plate, a quadrant along their feet (MX Tower)."""
    v0, v1 = 0.6, h - 0.6
    parts = [rect(0.3, v0, L - 0.3, v0 + 0.8)]
    for u in np.arange(1.4, L - 1.0, 1.9):
        parts.append(rect(u - 0.25, v0 + 0.7, u + 0.25, v1 - 0.8))
        parts.append(circle((u, v1 - 0.75), 0.55, 12))
        parts.append(rect(u - 0.5, v0 + (v1 - v0) * 0.45, u + 0.5, v0 + (v1 - v0) * 0.45 + 0.7))
    return [_st(cs_union(parts), b, 0.45)], []


def frieze_semaphores(L, h, b, pitch, margin, pair, half):
    """Semaphore signals at every station: a mast with its blade raised at 45 degrees and a
    spectacle plate of two round lenses (MX Tower)."""
    v0, v1 = 0.6, h - 0.6
    out = []
    for u in CO._us(L, pitch, margin, 0.0):
        hh = v1 - v0
        parts = [rect(u - 0.3, v0, u + 0.3, v1 - 0.4), circle((u, v1 - 0.5), 0.5, 12),
                 stroke([(u + 0.2, v0 + hh * 0.62), (u + hh * 0.42, v0 + hh * 0.62 + hh * 0.3)], 0.6, caps=False),
                 circle((u - 0.9, v0 + hh * 0.55), 0.45, 12), circle((u - 0.9, v0 + hh * 0.3), 0.45, 12),
                 rect(u - 0.9, v0 + hh * 0.3, u - 0.2, v0 + hh * 0.55)]
        out.append(_st(cs_union(parts) ^ rect(0.0, v0, L, v1), b, 0.45))
    return out, []


def course_pulleys(L, h, b, pitch, margin, p):
    """Signal wires on their pulley wheels: two thin lines, a wheel every 3 mm."""
    wires = cs_union([rect(0.3, h * 0.3 - 0.12, L - 0.3, h * 0.3 + 0.12), rect(0.3, h * 0.7 - 0.12, L - 0.3, h * 0.7 + 0.12)])
    wheels = cs_union([circle((u, h / 2), min(0.55, h * 0.35), 14) for u in np.arange(1.5, L - 1.0, 3.0)])
    return [ext(wires, b - 0.05, b + 0.25), ext(wheels, b - 0.05, b + 0.4)]


def bracket_towerknee(h, d, t):
    """A tower eave knee: a plumb post and a diagonal brace meeting the soffit, the triangle
    solid, the brace's foot notched (side profile, top at v = 0)."""
    hb = max(3.0, h)
    return poly([(0.0, 0.0), (d, 0.0), (d, -0.8), (1.6, -hb + 1.2), (1.2, -hb + 0.6), (0.9, -hb + 0.8), (0.9, -hb), (0.0, -hb)])


CO.FRIEZE_EXTRA.update(levers=frieze_levers, semaphores=frieze_semaphores)
CO.COURSE_EXTRA.update(pulleys=course_pulleys)
TW.BRACKET_EXTRA.update(towerknee=bracket_towerknee)
TW.FOUNDATION_EXTRA.update(scoredconcrete=foundation_scoredconcrete)


def window_operator(w=14.0, h=16.0):
    """The operator's window: a pair of sliding sashes of six lights each (two across, three up)
    in a flat casing with a sill and a drip cap."""
    op = O.opening_cs(w, h, 0)
    plug_cs = op.offset(-O.CLR, MJ, 4.0)
    pl = O.PLUG
    g = plug_cs.offset(-0.5, MJ, 4.0)
    u0, v0, u1, v1 = g.bounds()
    um = (u0 + u1) / 2
    bars = [rect(um - 0.45, v0 - 1, um + 0.45, v1 + 1)]
    for a, e in ((u0, um), (um, u1)):
        bars.append(rect((a + e) / 2 - 0.2, v0 - 1, (a + e) / 2 + 0.2, v1 + 1))
    for k in (1, 2):
        bars.append(rect(u0 - 1, v0 + (v1 - v0) * k / 3 - 0.2, u1 + 1, v0 + (v1 - v0) * k / 3 + 0.2))
    sash = _glazed([ext(plug_cs, -pl, -0.6)], g, pl, cs_union(bars), plug_cs)
    parts = [ext(op - op.offset(-RIB, MJ, 4.0), 0.0, 0.7), ext((op.offset(1.3, MJ, 4.0) - op) ^ rect(-w, 0.0, w, h + 1.3), 0.0, 0.6),
             chamfer_box(-w / 2 - 2.0, h + 1.29, w / 2 + 2.0, h + 2.2, 0.0, 1.3, c=0.3, bottom=1.0),
             chamfer_box(-w / 2 - 1.8, -1.2, w / 2 + 1.8, 0.2, 0.0, 1.3, c=0.4, bottom=0.8)]
    return O._one_piece(sash, parts, op, plug_cs, pl, h + 2.2, -1.2)


def door_tower_upper(w=9.0, h=22.0):
    """The operator's door at the stair head: four lights over a cross-braced panel."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, MJ, 4.0)
    pl = O.PLUG
    leaf = plug_cs.offset(-0.3, MJ, 4.0)
    lb = leaf.bounds()
    gl = rect(lb[0] + 0.9, h * 0.5, lb[2] - 0.9, lb[3] - 0.9)
    body = [ext(plug_cs, -pl, -1.0), ext(plug_cs - plug_cs.offset(-0.5, MJ, 4.0), -pl, 0.0), ext(leaf - gl, -1.0, -0.6)]
    pan = rect(lb[0] + 0.9, lb[1] + 0.9, lb[2] - 0.9, h * 0.5 - 0.9)
    pb = pan.bounds()
    body.append(ext(cs_union([stroke([(pb[0], pb[1]), (pb[2], pb[3])], 0.6), stroke([(pb[0], pb[3]), (pb[2], pb[1])], 0.6)]) ^ pan, -0.6, -0.25))
    gb = gl.bounds()
    bars = cs_union([rect((gb[0] + gb[2]) / 2 - 0.2, gb[1] - 1, (gb[0] + gb[2]) / 2 + 0.2, gb[3] + 1),
                     rect(gb[0] - 1, (gb[1] + gb[3]) / 2 - 0.2, gb[2] + 1, (gb[1] + gb[3]) / 2 + 0.2)])
    sash = _glazed(body, gl, pl, bars, plug_cs)
    parts = [ext(op - op.offset(-RIB, MJ, 4.0), 0.0, 0.7), ext((op.offset(1.2, MJ, 4.0) - op) ^ rect(-w, 0.0, w, h + 1.2), 0.0, 0.6),
             chamfer_box(-w / 2 - 1.8, h + 1.19, w / 2 + 1.8, h + 2.0, 0.0, 1.2, c=0.3, bottom=1.0)]
    return O._one_piece(sash, parts, op, plug_cs, pl, h + 2.0, 0.0)


def stair_tower(rise, run, w=7.0, landing=10.0, n=None, t=1.2, rail=6.0):
    """An outside stair up to the operator's door, one piece: a closed flight between boarded
    stringers that rise into solid balustrades, a landing at the head on a boarded under-frame.
    Local: u across the flight (its wall side at u = 0, the flight to +u... w), v up, w along the
    wall (the foot at w = 0, the landing at the head). Prints lying on its outer stringer."""
    n = n or max(4, int(round(rise / 2.4)))
    r = rise / n
    tr = run / n
    from .ornament import side_profile
    # the flight's profile along w (horizontal) and v: treads stepping up
    prof = [(0.0, 0.0)]
    for k in range(n):
        prof += [(k * tr, (k + 1) * r), ((k + 1) * tr, (k + 1) * r)]
    prof += [(run + landing, rise), (run + landing, 0.0)]
    body = side_profile([(v_w, v_v) for v_w, v_v in prof], 0.0, w).transform(np.array([[1.0, 0, 0, 0], [0, 1.0, 0, 0], [0, 0, 1.0, 0]]))
    # stringers with balustrades (solid, boarded), the outer one full length
    sprof = [(0.0, 0.0), (0.0, r + rail), (run, rise + rail), (run + landing, rise + rail), (run + landing, 0.0)]
    outer = side_profile(sprof, w, w + t)
    front = box([0.0, 0.0, run + landing - t], [w + t, rise + rail, run + landing])
    grooves = union([box([w + t - 0.2, -1.0, z - 0.12], [w + t + 1.0, rise + rail + 1, z + 0.12]) for z in np.arange(1.2, run + landing, 1.2)])
    return (body + outer + front) - grooves


def sign_tower(text, L, H=6.0, t=1.0, cap=4.0):
    """The tower's call-letter board: chamfered corners, a raised rim, big raised letters
    (facade frame, centred on u = 0, foot at v = 0). Returns (board, letters)."""
    from .storefront import text_cs
    c = 1.2
    b = poly([(-L / 2 + c, 0.0), (L / 2 - c, 0.0), (L / 2, c), (L / 2, H - c), (L / 2 - c, H), (-L / 2 + c, H), (-L / 2, H - c), (-L / 2, c)])
    board = ext(b, 0.0, t) + ext(b - b.offset(-0.6, MJ, 4.0), t - 0.01, t + 0.4)
    letters = text_cs(text, cap=cap, font="serif", track=0.6)
    lb = letters.bounds()
    sc = min(1.0, (L - 2.0) / max(1e-6, lb[2] - lb[0]))
    letters = letters.scale((sc, 1.0)).translate(((-(lb[0] + lb[2]) / 2) * sc, (H - cap) / 2 - lb[1]))
    lt = ext(letters, t - 0.01, t + 0.45)
    return board + lt, lt


def window_relay(w=8.0, h=13.0):
    """The relay room's window: two-over-two sash under a flat arch of splayed bricks with a
    keystone, on a stone sill."""
    op = O.opening_cs(w, h, 0)
    plug_cs = op.offset(-O.CLR, MJ, 4.0)
    pl = O.PLUG
    sash = _sash(plug_cs, pl, rows=2, cols=2)
    hw = w / 2 + 1.1
    arch = poly([(-hw, h), (hw, h), (hw + 1.4, h + 2.6), (-hw - 1.4, h + 2.6)])
    joints = cs_union([stroke([(x, h - 0.1), (x * 1.35, h + 2.7)], 0.18, caps=False) for x in np.linspace(-hw + 0.9, hw - 0.9, 7)])
    parts = [ext(op - op.offset(-RIB, MJ, 4.0), 0.0, 0.7), ext((op.offset(1.1, MJ, 4.0) - op) ^ rect(-w, 0.0, w, h), 0.0, 0.5),
             ext(arch, 0.0, 0.7) - ext(joints ^ arch, 0.45, 1.0), chamfer_box(-0.8, h - 0.2, 0.8, h + 2.9, 0.0, 1.0, c=0.25),
             chamfer_box(-hw - 0.8, -1.1, hw + 0.8, 0.2, 0.0, 1.2, c=0.35, bottom=0.8)]
    return O._one_piece(sash, parts, op, plug_cs, pl, h + 2.9, -1.1)


# ================================================================== 69 Water Tank No. 12
def tank_body(r=34.0, h=40.0, hoops=4, spout_at=0.0):
    """A wooden water tank of vertical staves, one piece: a stave-grooved drum with a projecting
    chime at its foot, iron hoops with lugs, a rim at the top, and the hinged spout on its pivot
    box, raised at 45 degrees. Local: centred, z = 0 at the drum's foot; the spout faces -y."""
    n = max(48, int(2 * math.pi * r / 1.5))
    drum = M.cylinder(h, r, r, n)
    grooves = union([box([r - 0.35, -0.13, 1.2], [r + 1.0, 0.13, h - 0.6]).rotate([0, 0, 360.0 * k / n]) for k in range(n)])
    drum = drum - grooves
    chime = M.cylinder(1.4, r + 0.6, r + 0.6, n)
    rim = M.cylinder(1.2, r + 0.5, r + 0.5, n).translate([0, 0, h - 1.2])
    hoops_ = []
    for k in range(hoops):
        z = 4.0 + k * (h - 9.0) / max(1, hoops - 1)
        hoops_.append(M.cylinder(0.9, r + 0.45, r + 0.45, n).translate([0, 0, z]))
        a = 40.0 + 70.0 * k
        hoops_.append(box([r - 0.2, -0.8, z - 0.3], [r + 1.4, 0.8, z + 1.2]).rotate([0, 0, a]))
    body = drum + chime + rim + union(hoops_)
    # the spout: a pivot box on the drum, the trough rising from it at 45 degrees
    zp = h * 0.3
    piv = box([-2.4, -r - 3.2, zp - 2.4], [2.4, -r + 0.6, zp + 2.4])
    L = 16.0
    trough = box([-1.6, -1.6, 0.0], [1.6, 1.6, L]) - box([-1.0, 0.2, 1.0], [1.0, 2.0, L + 1.0])
    trough = trough.rotate([45.0, 0, 0]).translate([0, -r - 2.0, zp])
    return body + piv + trough


def tank_roof(r, rise=16.0, over=2.4):
    """The tank's conical roof, printed upright: boards running up the cone, a ball vent at the
    tip. Local: centred, z = 0 at its eave."""
    from . import roof as R_
    ap = r + over
    sol, tex, _, zt = R_.bell_roof((0.0, 0.0), ap, 0.0, [(round(rise / 0.2) * 0.2, rise / ap)], n=24, texture="upboards",
                                   tex_kw=dict(pitch=1.6, wtab=1.6, d=0.35))
    vent = M.cylinder(2.4, 1.6, 1.4, 20).translate([0, 0, zt - 0.8]) + M.sphere(1.8, 20).translate([0, 0, zt + 2.2])
    return sol + tex + vent


def trestle(r, h, post=2.4, deck_t=2.0, peg=1.2):
    """The tank's timber trestle, one piece printed upside down on its deck: a 3 x 3 grid of posts
    under a planked deck on joists, girts at mid-height and at the foot, X braces in every outer
    bay, a square peg under every post. Local: z = 0 at the posts' feet, the deck's top at h."""
    q = r * 0.72
    xs = (-q, 0.0, q)
    out = []
    for x in xs:
        for y in xs:
            out.append(box([x - post / 2, y - post / 2, 0.0], [x + post / 2, y + post / 2, h - deck_t]))
            out.append(box([x - peg / 2, y - peg / 2, -1.6], [x + peg / 2, y + peg / 2, 0.01]))
    for z in (h * 0.5, 2.0):
        for c in xs:
            out.append(box([-q - post / 2, c - 0.8, z - 0.8], [q + post / 2, c + 0.8, z + 0.8]))
            out.append(box([c - 0.8, -q - post / 2, z - 0.8], [c + 0.8, q + post / 2, z + 0.8]))
    for (z0, z1) in ((2.0, h * 0.5), (h * 0.5, h - deck_t)):
        for a, b in ((-q, 0.0), (0.0, q)):
            for side in (-q, q):
                out.append(M.hull_points([(a, side - 0.6, z0), (a, side + 0.6, z0), (b, side - 0.6, z1), (b, side + 0.6, z1),
                                          (a + 1.4, side - 0.6, z0), (a + 1.4, side + 0.6, z0), (b - 1.4, side - 0.6, z1), (b - 1.4, side + 0.6, z1)]))
                out.append(M.hull_points([(b, side - 0.6, z0), (b, side + 0.6, z0), (a, side - 0.6, z1), (a, side + 0.6, z1),
                                          (b - 1.4, side - 0.6, z0), (b - 1.4, side + 0.6, z0), (a + 1.4, side - 0.6, z1), (a + 1.4, side + 0.6, z1)]))
                out.append(M.hull_points([(side - 0.6, a, z0), (side + 0.6, a, z0), (side - 0.6, b, z1), (side + 0.6, b, z1),
                                          (side - 0.6, a + 1.4, z0), (side + 0.6, a + 1.4, z0), (side - 0.6, b - 1.4, z1), (side + 0.6, b - 1.4, z1)]))
                out.append(M.hull_points([(side - 0.6, b, z0), (side + 0.6, b, z0), (side - 0.6, a, z1), (side + 0.6, a, z1),
                                          (side - 0.6, b - 1.4, z0), (side + 0.6, b - 1.4, z0), (side - 0.6, a + 1.4, z1), (side + 0.6, a + 1.4, z1)]))
    dw = r + 1.6
    deck = box([-dw, -dw, h - deck_t], [dw, dw, h])
    planks = union([box([x - 0.12, -dw - 1, h - 0.3], [x + 0.12, dw + 1, h + 1]) for x in np.arange(-dw + 1.6, dw, 1.6)])
    joists = union([box([-dw, y - 0.8, h - deck_t - 1.6], [dw, y + 0.8, h - deck_t + 0.01]) for y in (-q, 0.0, q)])
    return union(out) + (deck - planks) + joists


def footings(r, post=2.4, peg=1.2, pad=1.8):
    """A concrete pad with a footing block under every trestle post, each socketed for its peg.
    Local: z = 0 at the ground, the blocks' tops at 4.0."""
    q = r * 0.72
    xs = (-q, 0.0, q)
    slab_ = box([-q - 6.0, -q - 6.0, 0.0], [q + 6.0, q + 6.0, pad])
    out = [slab_]
    socks = []
    for x in xs:
        for y in xs:
            out.append(M.hull_points([(x + a * (post / 2 + 1.4), y + c * (post / 2 + 1.4), pad - 0.01) for a in (-1, 1) for c in (-1, 1)] +
                                     [(x + a * (post / 2 + 0.5), y + c * (post / 2 + 0.5), 4.0) for a in (-1, 1) for c in (-1, 1)]))
            socks.append(box([x - peg / 2 - 0.12, y - peg / 2 - 0.12, 4.0 - 1.8], [x + peg / 2 + 0.12, y + peg / 2 + 0.12, 4.1]))
    return union(out) - union(socks)


# ================================================================== 70 the Greenfield Bandstand
def post_bandstand(h, collar=None, abacus=4.0, slot=None):
    """A bandstand column: a square plinth, a vase-turned base, a slim shaft with a ring at mid
    height, a bell capital under the abacus (the Greenfield)."""
    zt = h - 2.2
    body = PW._plinth(3.8, 1.2)
    prof = [(0.0, 1.19), (1.7, 1.19), (1.7, 1.8), (1.2, 2.4), (1.55, 3.6), (1.55, 5.0), (1.0, 6.4), (0.95, zt * 0.5 - 0.5),
            (1.35, zt * 0.5), (1.35, zt * 0.5 + 0.5), (0.95, zt * 0.5 + 1.0), (0.9, zt - 1.8), (1.3, zt - 0.8), (1.0, zt), (0.0, zt)]
    return body + PW._revolve(prof, 28) + PW._top(h, abacus / 2, zt - 0.01, 1.0, slot)


def fill_bandstand(L, vb, vt):
    """The bandstand railing: top and bottom rails with sawn balusters whose waists are cut in a
    lyre's outline, set close."""
    parts = [rect(0.0, vb, L, vb + 1.0), rect(0.0, vt - 1.2, L, vt)]
    n = max(2, int(L / 2.2))
    for k in range(n):
        c = L * (k + 0.5) / n
        hh = vt - vb
        parts.append(poly([(c - 0.55, vb + 0.9), (c + 0.55, vb + 0.9), (c + 0.8, vb + hh * 0.3), (c + 0.35, vb + hh * 0.5),
                           (c + 0.8, vb + hh * 0.72), (c + 0.55, vt - 1.1), (c - 0.55, vt - 1.1), (c - 0.8, vb + hh * 0.72),
                           (c - 0.35, vb + hh * 0.5), (c - 0.8, vb + hh * 0.3)]))
    return parts


def frieze_bandarch(u0, u1, v_bot, v_top):
    """A shallow elliptical arch between the columns, a solid sunburst of rays in each spandrel,
    the beam over it."""
    L = u1 - u0
    v0 = v_top - 2.4
    beam = rect(u0, v0, u1, v_top + 0.05)
    depth = min(4.5, L * 0.2)
    span = rect(u0, v0 - depth, u1, v0 + 0.01)
    uc = (u0 + u1) / 2
    ell = [(uc + (L / 2) * math.cos(a), v0 - depth + depth * 0.9 * math.sin(a)) for a in np.linspace(0.0, math.pi, 24)]
    opening = poly([(u1, v0 - depth - 1)] + ell + [(u0, v0 - depth - 1)])
    spandrel = span - opening
    rays = []
    for ue, sg in ((u0, 1), (u1, -1)):
        for a in np.linspace(0.15, 1.35, 4):
            rays.append(stroke([(ue, v0), (ue + sg * depth * 1.1 * math.cos(a), v0 - depth * 1.1 * math.sin(a))], 0.45, caps=False))
    return beam + spandrel + (cs_union(rays) ^ span.offset(0.5, MJ, 4.0))


def edge_bellvalance(L, z0, zc):
    """A valance of small bells along the fascia's foot, a flat band over them."""
    band = rect(0.3, zc - 1.3, L - 0.3, zc)
    bells = []
    for u in np.arange(1.4, L - 1.0, 2.4):
        bells.append(poly([(u - 0.4, zc - 1.29), (u + 0.4, zc - 1.29), (u + 0.85, zc - 2.5), (u - 0.85, zc - 2.5)]))
        bells.append(circle((u, zc - 2.75), 0.35, 10))
    return band + cs_union(bells), 0.7


def skirt_gridlattice(reg, d=1.2):
    """A square-grid lattice skirt: upright and level slats crossing, behind a flat rim."""
    if reg.is_empty():
        return M()
    u0, v0, u1, v1 = reg.bounds()
    body = M.extrude(reg, d * 0.3)
    grid = cs_union([rect(u - 0.3, v0 - 1, u + 0.3, v1 + 1) for u in np.arange(u0 + 1.0, u1, 2.0)] +
                    [rect(u0 - 1, v - 0.3, u1 + 1, v + 0.3) for v in np.arange(v0 + 1.0, v1, 2.0)])
    rim = reg - reg.offset(-0.8, MJ, 4.0)
    return body + ext((grid ^ reg) + rim, d * 0.29, d * 0.8)


PW.POSTS.update(bandstand=post_bandstand)
PW.FILLS.update(bandstand=fill_bandstand)
PW.FRIEZES.update(bandarch=frieze_bandarch)
PW.SKIRTS.update(gridlattice=skirt_gridlattice)
FT.EDGE_EXTRA.update(bellvalance=edge_bellvalance)


def finial_bandstand(h=10.0):
    """The bandstand's finial: a turned knop, an urn and a spike (prints upright). Local: foot at
    z = 0."""
    prof = [(0.0, 0.0), (1.8, 0.0), (1.8, 0.6), (1.0, 1.4), (1.4, 2.2), (1.4, 2.8), (0.8, 3.4), (1.2, 4.4), (1.2, 5.0), (0.5, 5.8),
            (0.35, h), (0.0, h)]
    return PW._revolve(prof, 24)

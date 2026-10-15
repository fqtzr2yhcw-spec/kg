"""The Laurel: an original HO-scale (1:87.1) water-powered gristmill with the miller's cabin;
house 113, of the new-layouts batch (hoarch.novel2), after Mabry Mill on the Blue Ridge
Parkway (Virginia, about 1910) and the mountain mills like it.

Water and machinery: the creek runs across the front of the base, cut below its banks; the
mill stands at the front corner with its front wall over a dry-laid stone wall at the water,
the overshot wheel turning in the creek against it (its axle in the wall and on a stone pier)
fed over the top by a plank flume carried on trestles from upstream; a loading shed with a
platform on the mill's west end; a plank footbridge crosses to the miller's cabin, which sits
back on the bank with its porch and fieldstone chimney.

- The site is one part (banks, the creek bed strewn with stones, paths), the water another
  (clear, it lies in the creek round the wheel, the trestles and the bridge legs).
- Walls: rough-sawn weatherboards of uneven widths, plain corner boards, on dry-laid stone.
- Cornices: the mill's girt with its peg heads at the floor, a frieze board over sawn rafter
  tails at the eave; the cabin's own.
- The wheel prints as two flat halves glued at the buckets; its axle is a rod through the hub.

usage: python3 -m hoarch.buildings.laurel [check] [export]
"""
import json
import math
import os
import sys
import time

import numpy as np
from manifold3d import JoinType, Manifold as M

from hoarch.core import Facade, box, cs_union, inv34, offset, poly, rect, slab, union
from hoarch import cornice as CO, gables as G, novel2 as N, openings as O
from hoarch.kit import Kit, print_flip
from hoarch.ornament import ext, stroke
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, stacked_shells, wall_shell

NAME = "The Laurel"
COLORS = {"Boards": "#86705C", "Trim": "#D8D0BE", "Tin": "#8E949A", "Shakes": "#675C52", "Stone": "#8C877D",
          "Earth": "#7A6A52", "Water": "#6E8FA0", "Timber": "#6E5A46", "Brick": "#8E4A38", "Windows_Doors": "#D8D0BE"}
RENDER_MAT = {"Boards": "boards", "Trim": "trim", "Tin": "tin", "Shakes": "roof", "Stone": "stone", "Earth": "earth",
              "Water": "water", "Timber": "timber", "Brick": "brick", "Windows_Doors": "trim", "Sash": "sash", "Door": "door",
              "Glass": "glass"}
PALETTE = {"boards": ["#86705C", 0.9, 0.0], "trim": ["#D8D0BE", 0.65, 0.0], "tin": ["#8E949A", 0.45, 0.35],
           "roof": ["#675C52", 0.85, 0.0], "stone": ["#8C877D", 0.9, 0.0], "earth": ["#7A6A52", 0.95, 0.0],
           "water": ["#6E8FA0", 0.15, 0.0], "timber": ["#6E5A46", 0.85, 0.0], "brick": ["#8E4A38", 0.85, 0.0],
           "sash": ["#D8D0BE", 0.5, 0.0], "door": ["#6E5A46", 0.6, 0.0]}
VIEWS = {"hero": [-30, 18, 70, 0.92, [0, 0, -12]], "hero_right": [32, 18, 70, 0.92, [0, 0, -12]],
         "front": [0, 8, 85, 0.95, [0, 0, 0]], "rear": [160, 22, 70, 0.92, [0, 0, -10]],
         "wheel": [-14, 6, 85, None, [180, 30, 32], 150], "cabin": [-20, 14, 85, None, [58, 110, 30], 150]}

LEDGE = 1.4
JOINT_M = dict(pitch=9.0, margin=3.0, layers=[
    dict(kind="course", h=2.2, b=1.2, orn="lrgirt", role="Boards"),
    dict(kind="crown", h=1.4, b=1.2, P=2.0, orn="bevel", role="Trim")])
EAVE_M = dict(pitch=6.0, margin=2.0, layers=[
    dict(kind="course", h=2.6, b=1.2, orn="lrboard", role="Trim"),
    dict(kind="bed", h=2.2, b=1.4, P=3.6, role="Boards", brackets=dict(style="lrrafter", t=1.6, h=2.2)),
    dict(kind="crown", h=1.6, b=1.4, P=4.0, orn="bevel", role="Trim")])
EAVE_H = dict(pitch=9.0, margin=3.0, layers=[
    dict(kind="course", h=2.0, b=1.2, orn="lrgirt", role="Trim"),
    dict(kind="crown", h=1.6, b=1.2, P=2.4, orn="cavetto", role="Boards")])
RJ = round((LEDGE + 0.4 + CO.band_height(JOINT_M)) / 0.2) * 0.2

T = 3.0
# the site: the bank behind the creek, the creek bed, the low far bank
SX, SY = 240.0, 200.0
ZB, ZWT, ZBED, ZFAR = 16.0, 7.0, 3.0, 10.0
CY0, CY1 = 12.0, 52.0
# the mill at the front corner, its front over the water, gable ends east and west
MX0, MX1, MY0, MY1 = 146.0, 218.0, CY1 + 1.0, 117.0
ZMF = ZB + 4.0
ZF = ZMF                                           # (the floors, mill and cabin alike, for the audit)
S1 = ZMF + 26.0
ZU = S1 + RJ
ZE = ZU + 22.0
ZW = round((ZE + CO.band_height(EAVE_M)) / 0.2) * 0.2
Z_EAVE = ZW + 1.4
SLM, DM, RAKEM = 0.75, 3.4, 4.0
MILL = Block("mill", [(MX0, MY0), (MX1, MY0), (MX1, MY1), (MX0, MY1)], ZMF, ZW)
# the wheel, its axle, the flume
WR, WW = 26.0, 12.0
WX = 190.0
WY1 = CY1 - 3.4                                    # its inner face (toward the mill)
WY0 = WY1 - WW
WYM = (WY0 + WY1) / 2
WZ = ZBED + WR                                     # its rim on the creek bed
FZ = WZ + WR + 2.0                                 # the flume's floor
# the loading shed on the mill's west end
LDY0, LDY1 = MY0 + 18.0, MY0 + 46.0
# the miller's cabin on the bank
HX0, HX1, HY0, HY1 = 26.0, 90.0, 120.0, 168.0
ZHF = ZB + 4.0
ZHE = ZHF + 31.0
ZHW = round((ZHE + CO.band_height(EAVE_H)) / 0.2) * 0.2
ZH_EAVE = ZHW + 1.2
SLH, DH = 0.9, 3.0
CABIN = Block("cabin", [(HX0, HY0), (HX1, HY0), (HX1, HY1), (HX0, HY1)], ZHF, ZHW)
CHY = (HY0 + HY1) / 2
CH = np.array([[0.0, -1.0, 0.0, HX0], [1.0, 0.0, 0.0, CHY], [0.0, 0.0, 1.0, ZB]])
# the footbridge
BX0, BX1 = 56.0, 70.0
BYA, BYB = 3.0, CY1 + 6.0
BLOCKS = [MILL, CABIN]
V1 = 7.0


def _openings():
    LM1, LM2, LH = [], [], []
    fams = {}

    def add(L, blk, x, y, v0, sp, name, kind="window"):
        e, u = blk.locate(x, y)
        L.append(Opening(blk, e, u, v0, sp, name, kind))
        L[-1].fam = fams.setdefault(id(sp), name)

    wm, loft = N.window_lrmill(), N.window_lrloft()
    V2 = ZU - ZMF + 6.0
    # the mill: lights at the creek either side of the wheel, at the back, at the ends; the
    # door under the loading shed in the west end, a man door in the east end
    add(LM1, MILL, MX0 + 9.0, MY0, V1, wm, "S-1")
    for x in (MX0 + 9.0, MX1 - 9.0):
        add(LM2, MILL, x, MY0, V2, wm, f"S{x:.0f}-2")
    for x in (MX0 + 18.0, MX1 - 18.0):
        add(LM1, MILL, x, MY1, V1, wm, f"N{x:.0f}-1")
    add(LM2, MILL, (MX0 + MX1) / 2, MY1, V2, wm, "N-2")
    add(LM1, MILL, MX0, (LDY0 + LDY1) / 2, 0.0, N.door_lrmill(w=12.0, h=18.0), "mill-door", "door")
    add(LM2, MILL, MX0, (LDY0 + LDY1) / 2, V2, wm, "W-2")
    add(LM1, MILL, MX1, MY0 + 16.0, 0.0, N.door_lrcabin(w=7.0, h=18.0), "east-door", "door")
    add(LM1, MILL, MX1, MY1 - 16.0, V1, wm, "E-1")
    add(LM2, MILL, MX1, (MY0 + MY1) / 2, V2, wm, "E-2")
    for x, tag in ((MX0, "W"), (MX1, "E")):
        add(LM2, MILL, x, (MY0 + MY1) / 2, ZW + 7.0 - ZMF, loft, f"{tag}-loft")
    # the cabin: its door between two windows onto the porch, two at the back, a light in
    # the east end and its gable, two little lights beside the chimney in the west gable
    wc = N.window_lrcabin()
    add(LH, CABIN, (HX0 + HX1) / 2, HY0, 0.0, N.door_lrcabin(), "cabin-door", "door")
    for x in (HX0 + 14.0, HX1 - 14.0):
        add(LH, CABIN, x, HY0, V1, wc, f"C-S{x:.0f}")
    for x in (HX0 + 20.0, HX1 - 20.0):
        add(LH, CABIN, x, HY1, V1, wc, f"C-N{x:.0f}")
    add(LH, CABIN, HX1, CHY, V1, wc, "C-E")
    add(LH, CABIN, HX1, CHY, ZHW + 4.0 - ZHF, loft, "C-E-loft")
    for y in (CHY - 12.0, CHY + 12.0):
        add(LH, CABIN, HX0, y, ZHW + 2.0 - ZHF, loft, f"C-W{y:.0f}-loft")
    return LM1, LM2, LH


OPEN_M1, OPEN_M2, OPEN_H = _openings()
OPENINGS = OPEN_M1 + OPEN_M2 + OPEN_H


def _skin(f, b, reg):
    """Weatherboards, kept clear of the cornices' bands (corner boards below the eaves)."""
    ze, zw = (ZE, ZW) if b is MILL else (ZHE, ZHW)
    reg = reg - rect(-1, ze - LEDGE - 0.6 - b.z0, f.L + 1, zw - b.z0 + 0.2)
    if b is MILL:
        reg = reg - rect(-1, S1 - b.z0, f.L + 1, ZU - b.z0)
    if reg.is_empty():
        return M()
    cut = rect(-50.0, -50.0, f.L + 50.0, zw - b.z0)
    lo, hi = reg ^ cut, reg - cut
    out = []
    if not lo.is_empty():
        out.append(N.weather_laurel(lo, datum=0.0, L=f.L, seed=int(f.L * 3) % 29))
    if not hi.is_empty():
        out.append(N.weather_laurel(hi, datum=0.0, seed=int(f.L * 7) % 31))
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


def _m44(A):
    return np.vstack([A, [0, 0, 0, 1.0]])


def _zones(solid, z, below, above):
    lo = box([-1e4, -1e4, -10.0], [1e4, 1e4, z + 0.05])
    return [(below, solid ^ lo), (above, solid - lo)]


def _gable_cs(wl, fascia):
    return wl["cs"] + rect(0.0, -fascia - 0.4, wl["L"], -fascia + 0.01)


def _sheared(x0, x1, y0, y1, ztop, below, above):
    return M.hull_points([(x, y, ztop(y) + dz) for x in (x0, x1) for y in (y0, y1) for dz in (-below, above)])


def _env(c, step=2.0, grow=0.4):
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


def _shed_porch(kit, name, A, L, D, posts, steps, z_hi, zf, s=0.3, OS=1.4, OV=2.2, PT=1.4, rails=True, seed=0):
    """A porch against a wall in its own frame (x 0..L along the wall, the wall at y = 0, out to
    y = -D; z as the world), placed by A, its floor at zf. The top is one piece: a shake roof
    sloping ``s`` from z_hi (its courses and joints grooved into the face it prints on), pole
    rafters, a ledger, a beam on turned posts with pegs, railings (not across ``steps``); it
    prints tilted onto its roof face, the shakes its first 0.6 mm. The deck: planks out from
    the wall, a rim, stone piers to the ground (ZB); printed upside down."""
    zt = lambda y: z_hi + s * y
    y_out = -(D + OV)
    rng = np.random.default_rng(seed + 7)
    parts = [_sheared(-OS, L + OS, y_out, 0.0, zt, PT, 0.0)]
    grooves = []
    for y in np.arange(-1.5, y_out, -2.2):
        grooves.append(_sheared(-OS - 1, L + OS + 1, y - 0.15, y + 0.15, zt, 0.3, 1.0))
        x = -OS + rng.uniform(0.3, 1.8)
        while x < L + OS - 0.4:
            grooves.append(_sheared(x - 0.12, x + 0.12, max(y - 2.2, y_out - 1.0), y, zt, 0.3, 1.0))
            x += rng.uniform(1.5, 2.6)
    parts.append(box([0.0, -1.2, z_hi - PT - 2.2], [L, 0.0, z_hi - PT + 0.3]))
    for x in np.arange(1.2, L - 0.6, 4.0):
        parts.append(_sheared(x - 0.45, x + 0.45, y_out + 0.3, -1.2, zt, PT + 0.9, -PT + 0.2))
    zb = round((zt(-D) - PT - 2.2) / 0.2) * 0.2
    yp = -D + 1.4
    parts.append(box([-0.4, yp - 1.2, zb], [L + 0.4, yp + 1.2, zt(-D + 2.6) - PT + 0.2]))
    for u in posts:
        parts.append(N.post_laurel(zb - zf + 0.3).translate([u, yp, zf]))
        parts.append(box([u - 0.8, yp - 0.8, zf - 1.2], [u + 0.8, yp + 0.8, zf + 0.3]))
    if rails:
        for ua, ub in zip(posts[:-1], posts[1:]):
            if any(u0 <= (ua + ub) / 2 <= u1 for u0, u1 in steps):
                continue
            Ar = np.array([[1.0, 0, 0, ua + 1.0], [0, 0, -1.0, yp], [0, 1.0, 0, zf + 0.8]])
            parts.append(N.rail_laurel(ub - ua - 2.0).transform(Ar))
        for u in (posts[0], posts[-1]):
            Ar = np.array([[0, 0, 1.0, u], [1.0, 0, 0, yp + 1.0], [0, 1.0, 0, zf + 0.8]])
            parts.append(N.rail_laurel(-yp - 1.0 - 2.6).transform(Ar))
    top = union(parts) - union(grooves)
    face = _sheared(-OS - 1, L + OS + 1, y_out - 1, 1.0, zt, 0.6, 2.0)
    ph_ = math.pi - math.atan(s)
    R = np.array([[1.0, 0, 0, 0], [0, math.cos(ph_), -math.sin(ph_), 0], [0, math.sin(ph_), math.cos(ph_), 0]])
    P = (_m44(R) @ np.linalg.inv(_m44(A)))[:3]
    topw, facew = top.transform(A), face.transform(A)
    kit.add(f"{name}-top", "Shakes", topw, P=P, group="porch", change=(0.6, "Timber"),
            render=[("Shakes", topw ^ facew), ("Timber", topw - facew)])
    deck = box([0.0, -D, zf - 1.4], [L, -1.8, zf]) + box([0.0, -D, zf - 2.6], [L, -D + 1.0, zf - 1.3]) + \
        box([0.0, -D, zf - 2.6], [1.0, -1.8, zf - 1.3]) + box([L - 1.0, -D, zf - 2.6], [L, -1.8, zf - 1.3])
    gaps = [box([x - 0.15, -D - 1, zf - 0.3], [x + 0.15, 0.0, zf + 1]) for x in np.arange(1.5, L - 0.4, 1.5)]
    piers = []
    for k, u in enumerate(posts):
        uu = min(max(u, 1.8), L - 1.8)
        for y in (yp, -4.2):
            piers.append(M.hull_points([(uu + dx, y + dy, z) for dx in (-1.7, 1.7) for dy in (-1.6, 1.6) for z in (ZB - 0.6, zf - 2.4)] +
                                       [(uu + dx, y + dy, zf - 1.3) for dx in (-1.3, 1.3) for dy in (-1.2, 1.2)]))
    socks = [box([u - 0.95, yp - 0.95, zf - 2.4], [u + 0.95, yp + 0.95, zf + 1]) for u in posts]
    d_ = (deck - union(gaps) + union(piers)) - union(socks)
    dw = d_.transform(A)
    kit.add(f"{name}-deck", "Timber", dw, P=(_m44(print_flip()) @ np.linalg.inv(_m44(A)))[:3], group="porch",
            change=(2.6, "Stone"), render=_zones(dw, zf - 2.6, "Stone", "Timber"))
    return topw, dw


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    keep = []

    # --- the cabin's chimney first (its gable, cornice and roof keep clear of it)
    chim, zch = N.chimney_laurel(w0=14.0, d0=9.0, zs=24.0, w1=8.0, d1=6.0, top=72.0, seed=3)
    chw = chim.transform(CH)
    ch_env = _env(chw)

    # --- the mill: its roof and gables, two storey shells, the girt and the eave
    rm = G.gabled_roof([([(MX0 - (RAKEM - DM), MY0), (MX1 + (RAKEM - DM), MY0), (MX1 + (RAKEM - DM), MY1), (MX0 - (RAKEM - DM), MY1)], [0, 2], SLM)],
                       Z_EAVE, DM, [dict(p0=(MX1, MY0), p1=(MX1, MY1), slope=SLM), dict(p0=(MX0, MY1), p1=(MX0, MY0), slope=SLM)],
                       texture="lrtin", tex_kw=dict(pitch=2.2, d=0.4), skin=1.4, rake=RAKEM, inner_cs=offset(MILL.cs, -3.0),
                       fascia=1.4, hollow=2.2)
    gm = [(MILL, 1, _gable_cs(rm["walls"][0], 1.4).translate((0.0, Z_EAVE - ZMF))),
          (MILL, 3, _gable_cs(rm["walls"][1], 1.4).translate((0.0, Z_EAVE - ZMF)))]
    z_ld = S1 - 1.2                                                     # the loading shed's roof at the wall
    ld_und = box([MX0 - 2.0, LDY0 - 2.0, z_ld - 4.4], [MX0 + 0.1, LDY1 + 2.0, z_ld + 0.6])
    brg = box([WX - 2.6, MY0 - 2.0, WZ - 2.6], [WX + 2.6, MY0, WZ + 2.6])
    band = slab(offset(MILL.cs, 10.0), ZE - LEDGE - 0.6, ZW + 0.01)
    st = stacked_shells([MILL], OPEN_M1 + OPEN_M2, [S1], t=T, corners="none", siding=_skin, clear=[lip_keep(MILL.cs, T, ZMF, 1.2)],
                        prof=CO.joint_profile(RJ, LEDGE), belt_blocks=None, water_table=False,
                        undress=[band, ld_und, brg.translate([0, -0.5, 0]) + brg], gables=gm)
    axle_hole = M.cylinder(4.0, 1.75, 1.75, 24).rotate([-90, 0, 0]).translate([WX, MY0 - 1.0, WZ])
    kit.add("WALLS-1", "Boards", st["shells"][0] - axle_hole, group="walls")
    kit.add("BELT", "Boards", st["rings"][0], group="walls")
    lip = _corbel(MILL.cs, T, ZW) + lip_ring(MILL.cs, T, ZW)
    kit.add("WALLS-2", "Boards", st["shells"][1] + lip + CO.ledge(MILL.pts, ZE, LEDGE, t=T), group="walls")
    jr, _ = CO.level(st["outlines"][0], S1 + LEDGE + 0.4, JOINT_M)
    CO.add_level(kit, jr, "CORNICE-J", "cornice")
    er, _ = CO.level(MILL.pts, ZE, EAVE_M, t=T)
    CO.add_level(kit, er, "CORNICE-E", "cornice")
    _place_inserts(kit, OPEN_M1 + OPEN_M2, keep)
    roof = rm["body"] + rm["tex"] + rm["skins"] + rm["skin_tex"]
    zr = Z_EAVE + SLM * ((MY1 - MY0) / 2 + DM)
    wenv = union([wl["facade"].place(M.extrude(wl["cs"].offset(0.15), RAKEM + 4.2).translate([0, 0, -3.15])) for wl in rm["walls"]])
    roof = roof + (G.ridge_cap((MX0 - RAKEM, (MY0 + MY1) / 2), (MX1 + RAKEM, (MY0 + MY1) / 2), zr, SLM, ZW, half=1.1, up=0.5) - wenv)
    roof = roof - lip_keep(MILL.cs, T, ZW)
    kit.add("ROOF", "Tin", max(roof.decompose(), key=lambda m_: m_.volume()), group="roof")
    kit.add("BASE", "Stone", foundation([MILL], ZB, ZMF, style="lrstone") - union(keep), group="foundation")
    print("mill", round(time.time() - t0, 1))

    # --- the water works: the wheel in two halves, its axle on a pier and in a bearing on the
    # wall, the flume on its trestles, the stone wall at the water
    half = N.wheel_laurel_half(R=WR, W=WW) - M.cylinder(40.0, 1.75, 1.75, 24).translate([0, 0, -20.0])
    TA = np.array([[1.0, 0, 0, WX], [0, 0, 1.0, WY0], [0, -1.0, 0, WZ]])
    ha = half.transform(TA)
    hb = ha.translate([0, -WYM, 0]).mirror([0, 1.0, 0]).translate([0, WYM, 0])
    kit.add("WHEEL-a", "Timber", ha, P=inv34(TA), group="wheel")
    kit.add("WHEEL-b", "Timber", hb, P=np.array([[1.0, 0, 0, -WX], [0, 0, 1.0, -WZ], [0, -1.0, 0, WY1]]), group="wheel")
    axle = M.cylinder(MY0 + 2.2 - (WY0 - 6.0), 1.6, 1.6, 24).rotate([-90, 0, 0]).translate([WX, WY0 - 6.0, WZ])
    kit.add("AXLE", "Timber", axle, P=np.array([[1.0, 0, 0, -WX], [0, 0, -1.0, WZ], [0, 1.0, 0, -(WY0 - 6.0)]]), group="wheel")
    kit.add("BEARING", "Timber", brg - axle.translate([0, 0, 0]) - M.cylinder(6.0, 1.75, 1.75, 24).rotate([-90, 0, 0]).translate([WX, MY0 - 3.0, WZ]),
            group="wheel")
    pier = box([WX - 3.0, WY0 - 6.5, ZBED - 0.4], [WX + 3.0, WY0 - 1.0, WZ - 1.0])
    pier = pier - M.cylinder(8.0, 1.65, 1.65, 24).rotate([-90, 0, 0]).translate([WX, WY0 - 7.0, WZ])
    pier = pier - union([box([WX - 4, WY0 - 8, z - 0.12], [WX + 4, WY0, z + 0.12]) - box([WX - 2.8, WY0 - 6.3, z - 1], [WX + 2.8, WY0 - 1.2, z + 1])
                         for z in np.arange(ZBED + 2.2, WZ - 2.0, 2.2)])
    kit.add("PIER", "Stone", pier, group="wheel")
    flume = N.flume_laurel(WX + 2.0, W=14.0, H=6.0).translate([0.0, WYM, FZ])
    kit.add("FLUME", "Timber", flume, group="wheel")
    bents = []
    for k, x in enumerate((12.0, 36.0, 84.0, 108.0, 132.0, 156.0)):
        Ab = np.array([[0, 0, 1.0, x - 0.7], [1.0, 0, 0, WYM], [0, 1.0, 0, ZBED - 0.4]])
        b_ = N.bent_laurel(FZ - (ZBED - 0.4), 9.6).transform(Ab)
        bents.append(b_)
        kit.add(f"TRESTLE-{k}", "Timber", b_, P=inv34(Ab), key="TRESTLE-laurel", group="wheel")
    # the dry-laid wall at the water under the mill's front
    f = Facade((MX0 - 4.0, CY1 - 2.4), (MX1 + 4.0, CY1 - 2.4), ZBED - 0.4)
    wall = box([MX0 - 4.0, CY1 - 2.4, ZBED - 0.4], [MX1 + 4.0, CY1, ZB])
    wall = wall + f.place(N.foundation_lrstone(rect(0.0, 0.5, f.L, ZB - ZBED + 0.4 - 0.2), seed=4).translate([0, 0, -0.05]))
    kit.add("STONEWALL", "Stone", wall, P=inv34(f.A), group="wheel")
    print("wheel", round(time.time() - t0, 1))

    # --- the footbridge: a sloping plank deck on two stringers from bank to bank, a rail each
    # side, a bent at mid-creek; printed upside down on its deck
    zl = lambda y: (ZFAR - 0.4) + (ZB - ZFAR) * (y - BYA) / (BYB - BYA)
    deck = M.hull_points([(x, y, zl(y) + dz) for x in (BX0, BX1) for y in (BYA, BYB) for dz in (0.0, 1.2)])
    deck = deck - union([M.hull_points([(x, y + dy, zl(y) + dz) for x in (BX0 - 1, BX1 + 1) for dy in (-0.12, 0.12) for dz in (0.9, 3.0)])
                         for y in np.arange(BYA + 1.6, BYB - 0.4, 1.6)])
    parts = [deck]
    for x in (BX0 + 1.6, BX1 - 1.6):
        parts.append(M.hull_points([(x + dx, y, zl(y) + dz) for dx in (-0.7, 0.7) for y in (BYA + 0.6, BYB - 0.6) for dz in (-1.6, 0.1)]))
    for x in (BX0 + 0.6, BX1 - 0.6):
        for y in np.linspace(BYA + 1.0, BYB - 1.0, 6):
            parts.append(box([x - 0.5, y - 0.5, zl(y) + 1.1], [x + 0.5, y + 0.5, zl(y) + 8.0]))
        parts.append(M.hull_points([(x + dx, y, zl(y) + dz) for dx in (-0.5, 0.5) for y in (BYA + 0.5, BYB - 0.5) for dz in (7.0, 8.0)]))
        parts.append(M.hull_points([(x + dx, y, zl(y) + dz) for dx in (-0.4, 0.4) for y in (BYA + 0.5, BYB - 0.5) for dz in (4.0, 4.8)]))
    ym = (CY0 + CY1) / 2
    for x in (BX0 + 1.6, BX1 - 1.6):
        parts.append(box([x - 0.8, ym - 0.8, ZBED - 0.4], [x + 0.8, ym + 0.8, zl(ym) - 1.0]))
    parts.append(box([BX0 + 0.6, ym - 0.9, zl(ym) - 2.6], [BX1 - 0.6, ym + 0.9, zl(ym) - 1.4]))
    parts.append(M.hull_points([(x, ym + dy, z) for (x, z) in ((BX0 + 2.2, ZBED + 1.0), (BX1 - 2.2, zl(ym) - 3.0)) for dy in (-0.4, 0.4)] +
                               [(x + dx, ym + dy, z) for (x, z) in ((BX0 + 2.2, ZBED + 1.0), (BX1 - 2.2, zl(ym) - 3.0)) for dy in (-0.4, 0.4) for dx in (-0.5, 0.5)]))
    bridge = union(parts)
    th = math.atan((ZB - ZFAR) / (BYB - BYA))
    ph = math.pi - th
    Pb = np.array([[1.0, 0, 0, 0], [0, math.cos(ph), -math.sin(ph), 0], [0, math.sin(ph), math.cos(ph), 0]])
    kit.add("BRIDGE", "Timber", bridge, P=Pb, group="porch")
    print("bridge", round(time.time() - t0, 1))

    # --- the loading shed on the mill's west end: a platform at the floor on stone piers
    A_ld = np.array([[0, 1.0, 0, MX0], [-1.0, 0, 0, LDY1], [0, 0, 1.0, 0]])
    _, ld_deck = _shed_porch(kit, "LOADING", A_ld, LDY1 - LDY0, 12.0, [1.4, 14.0, 26.6], [], z_ld, ZMF, rails=False, seed=1)

    # --- the miller's cabin
    rc = G.gabled_roof([(CABIN.pts, [0, 2], SLH)], ZH_EAVE, DH,
                       [dict(p0=(HX1, HY0), p1=(HX1, HY1), slope=SLH), dict(p0=(HX0, HY1), p1=(HX0, HY0), slope=SLH)],
                       texture="lrshake", tex_kw=dict(pitch=2.0, d=0.38), skin=1.6, rake=3.0, inner_cs=offset(CABIN.cs, -3.0),
                       fascia=1.2, hollow=2.4)
    gc = [(CABIN, 1, _gable_cs(rc["walls"][0], 1.2).translate((0.0, ZH_EAVE - ZHF))),
          (CABIN, 3, _gable_cs(rc["walls"][1], 1.2).translate((0.0, ZH_EAVE - ZHF)))]
    z_hp = ZHE - LEDGE - 1.0
    hp_und = box([HX0 - 3.0, HY0 - 2.0, z_hp - 4.4], [HX1 + 3.0, HY0 + 0.1, z_hp + 0.6])
    hband = slab(offset(CABIN.cs, 8.0), ZHE - LEDGE - 0.6, ZHW + 0.01)
    hsh = wall_shell([CABIN], OPEN_H, t=T, belt=None, corners="none", water_table=False, siding=_skin, gables=gc,
                     undress=[hband, hp_und, ch_env])
    hw = (hsh - lip_keep(CABIN.cs, T, ZHF, 1.2)) + _corbel(CABIN.cs, T, ZHW) + lip_ring(CABIN.cs, T, ZHW) + \
        (CO.ledge(CABIN.pts, ZHE, LEDGE, t=T) - ch_env)
    kit.add("CABIN-WALLS", "Boards", hw, group="walls")
    hr, _ = CO.level(CABIN.pts, ZHE, EAVE_H, t=T, cut=ch_env)
    CO.add_level(kit, hr, "CORNICE-H", "cornice")
    _place_inserts(kit, OPEN_H, keep)
    croof = rc["body"] + rc["tex"] + rc["skins"] + rc["skin_tex"]
    zrc = ZH_EAVE + SLH * ((HY1 - HY0) / 2 + DH)
    cwenv = union([wl["facade"].place(M.extrude(wl["cs"].offset(0.15), 3.0 + 4.2).translate([0, 0, -3.15])) for wl in rc["walls"]])
    croof = croof + (G.ridge_cap((HX0 - 3.0, CHY), (HX1 + 3.0, CHY), zrc, SLH, ZHW, half=1.0, up=0.5) - cwenv)
    croof = croof - lip_keep(CABIN.cs, T, ZHW) - ch_env
    kit.add("CABIN-ROOF", "Shakes", max(croof.decompose(), key=lambda m_: m_.volume()), group="roof")
    kit.add("CHIMNEY", "Stone", chw, P=inv34(CH), group="chimney", change=(zch, "Brick"), render=_zones(chw, ZB + zch, "Stone", "Brick"))
    kit.add("CABIN-BASE", "Stone", foundation([CABIN], ZB, ZHF, style="lrstone", seed=6) - union(keep) - ch_env, group="foundation")
    _, h_deck = _shed_porch(kit, "PORCH", np.array([[1.0, 0, 0, HX0], [0, 1.0, 0, HY0], [0, 0, 1.0, 0]]), HX1 - HX0, 14.0,
                [1.4, 22.0, 42.0, HX1 - HX0 - 1.4], [(22.0, 42.0)], z_hp, ZHF, seed=2)
    steps = []
    for j in range(2):
        z = ZHF - 2.0 * (j + 1)
        ya, yb = HY0 - 14.0 - 2.8 * (j + 1), HY0 - 14.0 - 2.8 * j
        steps.append(M.hull_points([(x, y, ZB - 0.4) for x in (HX0 + 25.0, HX0 + 39.0) for y in (ya, yb)] +
                                   [(x, y, z - 0.3) for x in (HX0 + 25.0, HX0 + 39.0) for y in (ya, yb)] +
                                   [(x, y, z) for x in (HX0 + 25.3, HX0 + 38.7) for y in (ya + 0.3, yb - 0.3)]))
    steps.append(box([HX0 + 25.0, HY0 - 14.0, ZB - 0.4], [HX0 + 39.0, HY0 - 13.0, ZHF - 2.6]))
    steps.append(box([HX0 + 25.0, HY0 - 13.0, ZB - 0.4], [HX0 + 39.0, HY0 - 12.2, ZHF - 1.4]))
    steps = union(steps)
    kit.add("STEPS", "Stone", steps, group="stoop")
    mst = N.millstone_laurel().translate([122.0, 64.0, ZB - 0.4])
    kit.add("MILLSTONE", "Stone", mst, group="stoop")
    print("cabin", round(time.time() - t0, 1))

    # --- the site: the bank, the far bank, the creek bed strewn with stones, paths; seats for
    # everything standing on it; the water
    rng = np.random.default_rng(17)
    g = box([0.0, CY1, 0.0], [SX, SY, ZB]) + box([0.0, 0.0, 0.0], [SX, CY0, ZFAR]) + box([0.0, CY0, 0.0], [SX, CY1, ZBED])
    for xa, xb in ((0.0, MX0 - 4.0), (MX1 + 4.0, SX)):
        g = g + M.hull_points([(x, y, z) for x in (xa, xb) for (y, z) in ((CY1, ZB), (CY1 - 6.5, ZBED), (CY1, ZBED))])
    g = g + M.hull_points([(x, y, z) for x in (0.0, SX) for (y, z) in ((CY0, ZFAR), (CY0 + 3.5, ZBED), (CY0, ZBED))])
    peb = []
    for _ in range(170):
        x, y = rng.uniform(2.0, SX - 2.0), rng.uniform(CY0 + 4.0, CY1 - 7.0)
        r = rng.uniform(0.7, 1.5)
        peb.append(M.sphere(1.0, 10).scale([r * rng.uniform(0.8, 1.3), r, r * 0.45]).translate([x, y, ZBED]))
    def boulder(x, y, z, r):
        """A field boulder: an angular hull of points on a squat ellipsoid, sunk a third."""
        pts = []
        for _ in range(16):
            th, ph = rng.uniform(0.0, 2 * math.pi), rng.uniform(-0.35, 1.2)
            k = rng.uniform(0.8, 1.1)
            pts.append((x + k * r * 1.2 * math.cos(th) * math.cos(ph), y + k * r * math.sin(th) * math.cos(ph), z + k * r * 0.75 * math.sin(ph)))
        pts += [(x + r * math.cos(t_), y + r * math.sin(t_), z - r * 0.4) for t_ in np.linspace(0, 2 * math.pi, 7)[:-1]]
        return M.hull_points(pts)
    for (x, y, r) in ((30.0, 22.0, 4.0), (100.0, 40.0, 3.4), (226.0, 26.0, 4.6), (122.0, 18.0, 3.0)):
        peb.append(boulder(x, y, ZBED, r))
    for (x, y, r) in ((8.0, 190.0, 6.0), (140.0, 182.0, 5.0), (232.0, 150.0, 6.0), (110.0, 140.0, 3.6), (14.0, 4.0, 3.0)):
        peb.append(boulder(x, y, ZB if y > CY1 else ZFAR, r))
    g = g + (union(peb) ^ box([0.0, 0.0, -1.0], [SX, SY, 60.0]))
    paths = [stroke([(63.0, BYB - 1.0), (60.0, 80.0), (58.0, HY0 - 22.0)], 4.6),
             stroke([(64.0, 72.0), (100.0, 74.0), (MX0 - 13.0, (LDY0 + LDY1) / 2)], 4.0)]
    pcs = cs_union(paths)
    g = g - slab(pcs, ZB - 0.3, ZB + 1.0)
    gr = []
    for _ in range(260):
        x, y = rng.uniform(0, SX), rng.uniform(CY1, SY)
        gr.append(M.sphere(0.35, 8).scale([1.0, 1.0, 0.6]).translate([x, y, ZB - 0.3]))
    g = g + (union(gr) ^ slab(pcs.offset(-0.4, JoinType.Round), ZB - 0.4, ZB + 1.0))
    stand = union([ha, hb, pier, wall, bridge, ld_deck, h_deck, steps, mst] + bents)
    g = g - stand
    kit.add("GROUND", "Earth", g, group="foundation")
    water = box([0.0, CY0 - 1.0, ZBED - 1.0], [SX, CY1 + 1.0, ZWT]) - g
    water = water - union([M.hull(b_) for b_ in bents]) - M.hull(pier) - wall - M.hull(ha + hb) - \
        union([box([x - 1.1, ym - 1.1, ZBED - 2], [x + 1.1, ym + 1.1, ZWT + 1]) for x in (BX0 + 1.6, BX1 - 1.6)]) - \
        M.hull_points([(x, ym, z) for x in (BX0 + 1.0, BX1 - 1.0) for z in (ZBED - 2, ZWT + 1)] + [(x, ym + dy, z) for x in (BX0 + 1.0, BX1 - 1.0) for dy in (-0.7, 0.7) for z in (ZBED - 2, ZWT + 1)])
    water = max(water.decompose(), key=lambda m_: m_.volume())
    kit.add("WATER", "Water", water, P=print_flip(), group="foundation")
    print("site", round(time.time() - t0, 1))
    print("specks dropped:", kit.drop_specks())
    print("done", round(time.time() - t0, 1))
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "laurel")
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
    kit.render_npz(os.path.join(OUT, "laurel.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))

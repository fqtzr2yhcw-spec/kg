"""The Prow: an original HO-scale (1:87.1) flatiron block; house 112, of the new-layouts batch
(hoarch.novel2), after the Gooderham Building, Toronto (1892, David Roberts Jr.).

A wedge of a building for the odd corner where two streets fork: two long fronts meeting at a
sharp angle, the point taken by an octagonal turret that rises a stage above the main
cornice under a copper spire. Cast-iron shopfronts along the ground floor of both fronts,
the entrance at the point; three storeys of red brick over them, each with its own windows
(segmental heads under hood moulds, then carved lintels, then round arches of gauged brick);
a corbelled-arcade cornice; a steep slate roof with stepped stone dormers rising to a flat
top railed in iron cresting; a blank party wall at the back with a sign panel for paint.
The point faces -y; it stands on its own sidewalk.

- Walls: running bond with a header course every sixth, on a granite plinth. One part per
  storey (four), the turret with them; its top stage with the top storey.
- Cornices: billet moulding and an ovolo over the shops; a chequer band at each upper floor
  (not on the party wall); the main cornice a corbelled brick arcade over stepped corbels
  under a sheet-metal cyma, wrapped round the turret; the turret's own under the spire.

usage: python3 -m hoarch.buildings.prow [check] [export]
"""
import json
import math
import os
import sys
import time

import numpy as np
from manifold3d import JoinType, Manifold as M

from hoarch.core import box, cs_union, inv34, offset, poly, rect, slab, union
from hoarch import cornice as CO, gables as G, novel2 as N, openings as O, roof as R
from hoarch.kit import Kit
from hoarch.ornament import ext
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, stacked_shells

NAME = "The Prow"
COLORS = {"Brick": "#8E3B2C", "Stone": "#C9B48E", "Iron": "#2B3A34", "Slate": "#4A4F57", "Copper": "#5E9C88",
          "Granite": "#8F8D88", "Concrete": "#B9B6AE", "Windows_Doors": "#C9B48E"}
RENDER_MAT = {"Brick": "brick", "Stone": "stone", "Iron": "iron", "Slate": "roof", "Copper": "copper", "Granite": "granite",
              "Concrete": "concrete", "Windows_Doors": "stone", "Sash": "sash", "Door": "door", "Glass": "glass"}
PALETTE = {"brick": ["#8E3B2C", 0.85, 0.0], "stone": ["#C9B48E", 0.75, 0.0], "iron": ["#2B3A34", 0.45, 0.2],
           "roof": ["#4A4F57", 0.75, 0.0], "copper": ["#5E9C88", 0.55, 0.15], "granite": ["#8F8D88", 0.85, 0.0],
           "concrete": ["#B9B6AE", 0.9, 0.0], "sash": ["#2B3A34", 0.5, 0.0], "door": ["#5A3524", 0.5, 0.0]}
VIEWS = {"hero": [-28, 14, 70, 0.95, [0, 0, -14]], "hero_right": [28, 14, 70, 0.95, [0, 0, -14]],
         "front": [0, 6, 85, 0.98, [0, 0, 0]], "rear": [160, 18, 70, 0.95, [0, 0, -12]],
         "point": [-6, 6, 85, None, [128, 30, 40], 170], "roof": [-30, 30, 85, None, [128, 90, 190], 190]}

LEDGE = 1.4
J1 = dict(pitch=9.0, margin=3.0, layers=[
    dict(kind="course", h=2.2, b=1.2, orn="prbillet", role="Brick"),
    dict(kind="crown", h=1.8, b=1.2, P=3.0, orn="ovolo", role="Stone")])
J2 = dict(pitch=9.0, margin=3.0, layers=[
    dict(kind="course", h=2.2, b=1.2, orn="prchequer", role="Brick"),
    dict(kind="crown", h=1.8, b=1.2, P=2.4, orn="bevel", role="Stone")])
EAVE = dict(pitch=9.0, margin=3.0, layers=[
    dict(kind="frieze", h=4.8, b=1.2, orn="prarcade", role="Brick"),
    dict(kind="bed", h=2.4, b=1.4, P=4.0, role="Stone", brackets=dict(style="prcorbel", t=1.6, h=2.4)),
    dict(kind="crown", h=2.0, b=1.4, P=5.0, orn="cyma", role="Iron")])
TEAVE = dict(pitch=6.0, margin=2.0, layers=[
    dict(kind="course", h=2.0, b=1.2, orn="prbillet", role="Stone"),
    dict(kind="crown", h=1.8, b=1.2, P=3.0, orn="cyma", role="Iron")])
RJ1 = round((LEDGE + 0.4 + CO.band_height(J1)) / 0.2) * 0.2
RJ2 = round((LEDGE + 0.4 + CO.band_height(J2)) / 0.2) * 0.2

T = 3.0
ZF = 4.0                                           # the plinth's top (the shop floors)
Z1 = ZF + 36.0
ZU1 = Z1 + RJ1
S2 = ZU1 + 26.0
ZU2 = S2 + RJ2
S3 = ZU2 + 26.0
ZU3 = S3 + RJ2
ZE = ZU3 + 26.0
ZW = round((ZE + CO.band_height(EAVE)) / 0.2) * 0.2
FASCIA = 1.4
Z_EAVE = ZW + FASCIA
SL, D_EAVE = 1.6, 2.4
ZTOP = round((Z_EAVE + 30.0) / 0.2) * 0.2          # the roof's flat top
# the plan: the point (an octagonal turret) at C, the two fronts at HALF to the axis
XC, YN, YB, HALF, RN = 128.0, 48.0, 226.0, 17.0, 15.0
RT = 17.0                                          # the turret's circumradius (inradius 15.7)
ZT = ZW + 32.0                                     # the turret's top stage (it rises past the roof's flat top)
ZTW = round((ZT + CO.band_height(TEAVE)) / 0.2) * 0.2
_h = math.radians(HALF)
T_R = (XC + RN * math.cos(-_h), YN + RN * math.sin(-_h))
T_L = (XC - RN * math.cos(-_h), YN + RN * math.sin(-_h))
_t = (YB - T_R[1]) / math.cos(_h)
B_R = (T_R[0] + math.sin(_h) * _t, YB)
B_L = (T_L[0] - math.sin(_h) * _t, YB)
WEDGE = Block("wedge", [T_R, B_R, B_L, T_L], ZF, ZW)
TURRET = Block("turret", [(XC + RT * math.cos(math.radians(22.5 + 45 * k)), YN + RT * math.sin(math.radians(22.5 + 45 * k))) for k in range(8)],
               ZF, ZTW)
BLOCKS = [WEDGE, TURRET]
FRONT_L = math.hypot(B_R[0] - T_R[0], B_R[1] - T_R[1])


def _front(side, s):
    """The world point s along a front from its tangent point toward the back (side +1 the
    right front, -1 the left)."""
    t0 = np.array(T_R if side > 0 else T_L)
    t1 = np.array(B_R if side > 0 else B_L)
    return tuple(t0 + (t1 - t0) * s / FRONT_L)


def _tfacet(k):
    """The midpoint of the turret's facet facing -90 + 45 k degrees."""
    a = math.radians(-90.0 + 45.0 * k)
    ri = RT * math.cos(math.radians(22.5))
    return (XC + ri * math.cos(a), YN + ri * math.sin(a))


def _openings():
    L1, L2, L3, L4, LT = [], [], [], [], []
    fams = {}

    def add(L, blk, pt, v0, sp, name, kind="window"):
        e, u = blk.locate(*pt)
        L.append(Opening(blk, e, u, v0, sp, name, kind))
        L[-1].fam = fams.setdefault(id(sp), name)

    shop = N.shop_prow()
    w2, w3, w4 = N.window_prow2(), N.window_prow3(), N.window_prow4()
    wt = N.window_prowturret()
    stair = N.door_prowmain(w=7.0, h=16.0)
    V2, V3, V4 = ZU1 - ZF + 5.0, ZU2 - ZF + 5.0, ZU3 - ZF + 5.0
    for side, tag in ((1, "R"), (-1, "L")):
        for j, s in enumerate((34.0, 74.0, 114.0, 154.0)):
            add(L1, WEDGE, _front(side, s), 0.0, shop, f"shop-{tag}{j}", "door")
        add(L1, WEDGE, _front(side, 181.0), 0.0, stair, f"stair-{tag}", "door")
        for j, s in enumerate(np.linspace(24.0, 174.0, 6)):
            add(L2, WEDGE, _front(side, s), V2, w2, f"{tag}{j}-2")
            add(L3, WEDGE, _front(side, s), V3, w3, f"{tag}{j}-3")
            add(L4, WEDGE, _front(side, s), V4, w4, f"{tag}{j}-4")
    # the turret: the entrance at the point, tall lights either side; a light in each of
    # its three street facets on every storey and in its top stage
    add(L1, TURRET, _tfacet(0), 0.0, N.door_prowmain(), "entrance", "door")
    tall = N.window_prowturret(w=6.0, h=22.0)
    for k in (-1, 1):
        add(L1, TURRET, _tfacet(k), 6.0, tall, f"T{k}-1")
    for k in (-1, 0, 1):
        add(L2, TURRET, _tfacet(k), V2, w2, f"T{k}-2")
        add(L3, TURRET, _tfacet(k), V3, w3, f"T{k}-3")
        add(L4, TURRET, _tfacet(k), V4, w4, f"T{k}-4")
        add(LT, TURRET, _tfacet(k), ZW + 5.0 - ZF, wt, f"T{k}-top")
    return L1, L2, L3, L4, LT


OPEN1, OPEN2, OPEN3, OPEN4, OPEN_T = _openings()
OPENINGS = OPEN1 + OPEN2 + OPEN3 + OPEN4 + OPEN_T


def _is_back(f):
    return f.u[0] < -0.9


def _skin(f, b, reg):
    """Brick, kept clear of the cornices' bands; on the party wall a sign panel in the top
    storey."""
    if b is WEDGE:
        reg = reg - rect(-1, ZE - LEDGE - 0.6 - b.z0, f.L + 1, ZW - b.z0 + 0.2)
    else:
        reg = reg - rect(-1, ZE - LEDGE - 0.6 - b.z0, f.L + 1, ZW - b.z0 + 0.2) - rect(-1, ZT - LEDGE - 0.6 - b.z0, f.L + 1, ZTW - b.z0 + 0.2)
    for z0, z1 in ((Z1, ZU1), (S2, ZU2), (S3, ZU3)):
        reg = reg - rect(-1, z0 - b.z0, f.L + 1, z1 - b.z0)
    if reg.is_empty():
        return M()
    sign = None
    if b is WEDGE and _is_back(f):
        sign = rect(f.L * 0.16, ZU3 - b.z0 + 3.0, f.L * 0.84, ZE - LEDGE - b.z0 - 4.0)
    return N.brick_prow(reg, datum=0.0, L=f.L, sign=sign)


def _place_inserts(kit, ops, keep, group="inserts"):
    for o in ops:
        A = o.local_frame()
        sp = o.spec
        b = sp["cut"].bounds()
        key = "DOOR" if o.kind == "door" else "WIN"
        frame = "Iron" if o.name.startswith("shop") else "Windows_Doors"
        world, P, zones = O.place(sp, A, frame, "Door" if o.kind == "door" else "Sash", "Glass")
        part = kit.add(f"{key}-{o.name}", frame, world, P=P, key=f"{key}-{o.fam}-{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}",
                       group=group, render=zones)
        keep.append(part.solid)


def _m44(A):
    return np.vstack([A, [0, 0, 0, 1.0]])


def _outline():
    cs = cs_union([b.cs for b in BLOCKS])
    return max(cs.to_polygons(), key=lambda L: abs(poly(L).area())), cs


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    keep = []
    opts, ocs = _outline()
    tur_env = TURRET.solid(grow=0.6, dz0=-10, dz1=80)
    foot = slab(ocs, -1.0, 400.0)                                            # (the rings stay outside the walls' plane)
    back_cut = box([0.0, YB - 0.6, -1.0], [400.0, YB + 40.0, 400.0])            # (no string courses on the party wall)
    assert abs(RJ1 - RJ2) < 1e-6

    # --- the walls: four storey shells, the turret with them; the joints' rings and cornices
    st = stacked_shells(BLOCKS, OPENINGS, [Z1, S2, S3], t=T, corners="none", siding=_skin, clear=[lip_keep(ocs, T, ZF, 1.2)],
                        prof=CO.joint_profile(RJ1, LEDGE), belt_blocks=None, water_table=False,
                        undress=[slab(offset(ocs, 10.0), ZE - LEDGE - 0.6, ZW + 0.01), slab(offset(TURRET.cs, 10.0), ZT - LEDGE - 0.6, ZTW + 0.01)])
    for i in range(3):
        kit.add(f"WALLS-{i + 1}", "Brick", st["shells"][i], group="walls")
        kit.add(f"BELT-{i + 1}", "Brick", st["rings"][i], group="walls")
        rr, _ = CO.level(st["outlines"][i], (Z1, S2, S3)[i] + LEDGE + 0.4, (J1, J2, J2)[i], cut=back_cut + foot)
        CO.add_level(kit, rr, f"CORNICE-J{i + 1}", "cornice")
    lip = (_corbel(WEDGE.cs, T, ZW) + lip_ring(WEDGE.cs, T, ZW)) - TURRET.solid(grow=0.1, dz0=-5, dz1=100)
    tlip = _corbel(TURRET.cs, T, ZTW) + lip_ring(TURRET.cs, T, ZTW)
    w4 = st["shells"][3] + lip + tlip + CO.ledge(opts, ZE, LEDGE, t=T) + CO.ledge(TURRET.pts, ZT, LEDGE, t=T)
    kit.add("WALLS-4", "Brick", w4, group="walls")
    er, _ = CO.level(opts, ZE, EAVE, t=T, cut=foot)
    CO.add_level(kit, er, "CORNICE-E", "cornice")
    tr, _ = CO.level(TURRET.pts, ZT, TEAVE, t=T, cut=slab(TURRET.cs, -1.0, 400.0))
    CO.add_level(kit, tr, "CORNICE-T", "cornice")
    _place_inserts(kit, OPENINGS, keep)
    print("walls", round(time.time() - t0, 1))

    # --- the roof: banded slate, steep to a flat top railed in iron; the dormers; the spire
    rf = G.gabled_roof([(list(WEDGE.pts), [0, 1, 2, 3], SL)], Z_EAVE, D_EAVE, [], texture="prslate", tex_kw=dict(pitch=1.4, d=0.3),
                       skin=1.6, inner_cs=offset(WEDGE.cs, -3.0), fascia=FASCIA, hollow=2.6)
    solid_env, _ = R.hip_roof([(list(WEDGE.pts), [0, 1, 2, 3], SL)], Z_EAVE, SL, D_EAVE, texture=None, zlo=ZW)
    inset = (ZTOP - Z_EAVE) / SL - D_EAVE
    deck_cs = offset(WEDGE.cs, -inset)
    roof = (rf["body"] + rf["tex"]) ^ box([-1e3, -1e3, -1.0], [1e3, 1e3, ZTOP])
    roof = roof + slab(deck_cs, ZTOP - 1.6, ZTOP + 0.6)
    roof = roof - lip_keep(WEDGE.cs, T, ZW)
    DW, DDEP, DHW = 12.0, 12.0, 9.0
    dbody, dcore, dface = N.dormer_prow(DW, DDEP, DHW)
    dAs = []
    for side in (1, -1):
        n = np.array([math.cos(-_h), math.sin(-_h)]) * np.array([side, 1.0])
        u = np.array([-n[1], n[0]])
        di = 2.0
        for s in (54.0, 84.0, 114.0, 144.0):
            p = np.array(_front(side, s)) - n * di
            zdf = round((Z_EAVE + SL * (di + D_EAVE) - 1.2) / 0.2) * 0.2
            dAs.append(np.array([[u[0], 0, n[0], p[0]], [u[1], 0, n[1], p[1]], [0, 1.0, 0, zdf]]))
    for Ad in dAs:
        zdf = Ad[2, 3]
        dkeep = ext(dface.offset(0.3, JoinType.Miter, 4.0), -DDEP - 0.3, 1.4).transform(Ad)
        dpocket = dkeep ^ box([-500, -500, zdf], [500, 500, 999])
        seat = ext(rect(-DW / 2 - 1.3, ZW - zdf, DW / 2 + 1.3, 0.0), -DDEP - 1.3, 1.6).transform(Ad) ^ solid_env
        roof = roof - dpocket + (seat - dpocket - lip_keep(WEDGE.cs, T, ZW))
    roof = roof - tur_env - slab(offset(TURRET.cs, 1.8), ZT - 2.0, ZT + 40.0)
    roof = max(roof.decompose(), key=lambda m_: m_.volume())
    kit.add("ROOF", "Slate", roof, group="roof")
    rise = DW / 2 * 0.9
    droof_cs = (dface.offset(1.0, JoinType.Miter, 4.0) - dface) ^ rect(-50.0, DHW - 0.6, 50.0, 99.0)   # slates over the gable
    for k, Ad in enumerate(dAs):
        kit.add(f"DORMER-{k}", "Stone", dbody.transform(Ad), key="DORMER-prow", group="roof")
        kit.add(f"DORMER-core-{k}", "Slate", dcore.transform(Ad), key="DORMER-core-prow", group="roof")
        droof = ext(droof_cs, -DDEP - 12.0, -0.95).transform(Ad) - solid_env - dbody.transform(Ad) - roof
        if not droof.is_empty():
            kit.add(f"DORMER-roof-{k}", "Slate", max(droof.decompose(), key=lambda m_: m_.volume()), group="roof")
    # the cresting round the flat top (not across the point, where the turret rises)
    dpts = max(deck_cs.to_polygons(), key=lambda L: abs(poly(L).area()))
    tb = tur_env.bounding_box()
    for k in range(len(dpts)):
        p, q = np.array(dpts[k]), np.array(dpts[(k + 1) % len(dpts)])
        if max(p[1], q[1]) < tb[4] + 2.0:
            continue
        if min(p[1], q[1]) < tb[4] + 2.0:                       # a long edge: start it clear of the turret
            lo_, hi_ = (p, q) if p[1] < q[1] else (q, p)
            f = (tb[4] + 2.0 - lo_[1]) / (hi_[1] - lo_[1])
            lo_ = lo_ + (hi_ - lo_) * f
            p, q = (lo_, hi_) if p[1] < q[1] else (hi_, lo_)
        d = (q - p) / np.linalg.norm(q - p)
        nn = np.array([d[1], -d[0]])
        L = float(np.linalg.norm(q - p)) - 5.0
        o = p + d * 2.5 - nn * 1.6
        Ac = np.array([[d[0], 0, nn[0], o[0]], [d[1], 0, nn[1], o[1]], [0, 1.0, 0, ZTOP + 0.6]])
        kit.add(f"CRESTING-{k}", "Iron", N.cresting_prow(L).transform(Ac), P=inv34(Ac), group="roof")
    for k, sg in enumerate((-1, 1)):
        kit.add(f"CHIMNEY-{k}", "Brick", N.chimney_prow(h=16.0).translate([XC + sg * 26.0, YB - 22.0, ZTOP + 0.6]), key="CHIMNEY-prow", group="roof")
    sp = N.spire_prow(R=RT + 1.6, h=36.0).translate([XC, YN, ZTW]) - lip_keep(TURRET.cs, T, ZTW)
    kit.add("SPIRE", "Copper", sp, group="roof")
    print("roof", round(time.time() - t0, 1))

    # --- the plinth and the sidewalk round it
    house_keep = union(keep)
    kit.add("BASE", "Granite", foundation(BLOCKS, 0.0, ZF, style="prplinth") - house_keep, group="foundation")
    walk = slab(ocs.offset(8.0, JoinType.Miter, 4.0) - ocs.offset(1.65, JoinType.Miter, 4.0), 0.0, 1.2)
    b_ = walk.bounding_box()
    gr = [box([x - 0.12, b_[1] - 1, 0.95], [x + 0.12, b_[4] + 1, 2.0]) for x in np.arange(b_[0] + 7.0, b_[3], 7.0)]
    gr += [box([b_[0] - 1, y - 0.12, 0.95], [b_[3] + 1, y + 0.12, 2.0]) for y in np.arange(b_[1] + 7.0, b_[4], 7.0)]
    walk = walk - union(gr) - house_keep
    kit.add("SIDEWALK", "Concrete", walk, group="foundation")
    print("specks dropped:", kit.drop_specks())
    print("done", round(time.time() - t0, 1))
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "prow")
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
    kit.render_npz(os.path.join(OUT, "prow.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors", "Iron"))

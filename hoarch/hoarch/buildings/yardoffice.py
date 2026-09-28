"""The Blackwater Yard Office: an original HO-scale (1:87.1) railroad yard office, building 75 (the
engine terminal batch).

A two-storey yardmaster's office of about 1898 in railroad ochre with cream trim and dark green
accents, on dressed sandstone. The first storey is channel rustic siding with a canted bay window
toward the tracks under its own low hip; the second storey narrow V-grooved boards with a band at
the sills. Lower windows two over two under entablature caps with dentils, upper windows one over
one under shouldered heads, a panelled door with a transom up two plank steps, YARD OFFICE on a
round-ended board. A hip roof of shingles with a bead at every butt carries the yardmaster's
lookout: one wide four-light window each way under a flared pyramid; a panelled brick stove
chimney on the back slope. Cornices: train-order hoops over a telegraph crossarm (the joint),
hand lanterns over the crossarm on stick brackets (the eave), the crossarm under the bay's roof.

usage: python3 -m hoarch.buildings.yardoffice [check] [export]
"""
import os
import sys
import time

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import box, offset, poly, rect, slab, union
from hoarch import cornice as CO, gables as G, openings as O, roof as R, yard as YD
from hoarch.kit import Kit
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, stacked_shells

NAME = "The Blackwater Yard Office"
COLORS = {"Ochre": "#C39A45", "Cream": "#EDE2C2", "Green": "#2F4A36", "Shingle": "#5A4E44", "Sandstone": "#B59B78",
          "Brick": "#8A3C2C", "Timber": "#6B563F", "Windows_Doors": "#EDE2C2"}
RENDER_MAT = {"Ochre": "siding", "Cream": "trim", "Green": "green", "Shingle": "roof", "Sandstone": "stone", "Brick": "brick",
              "Timber": "timber", "Windows_Doors": "trim", "Door": "door", "Glass": "glass", "Letters": "green"}
PALETTE = {"siding": ("#C39A45", 0.8, 0.0), "trim": ("#EDE2C2", 0.55, 0.0), "green": ("#2F4A36", 0.6, 0.0),
           "roof": ("#5A4E44", 0.85, 0.0), "stone": ("#B59B78", 0.9, 0.0), "brick": ("#8A3C2C", 0.9, 0.0),
           "timber": ("#6B563F", 0.9, 0.0), "door": ("#2F4A36", 0.6, 0.0)}
VIEWS = {"hero": [-34, 14, 60, 0.95, [0, 0, 0]], "front": [0, 6, 70, 0.92, [0, 0, 0]], "rear": [150, 16, 60, 0.95, [0, 0, 0]]}

# ------------------------------------------------------------------ cornices (unique to the yard office)
LEDGE = 1.4
JOINT = dict(pitch=9.0, margin=3.0, layers=[
    dict(kind="frieze", h=4.4, b=1.2, orn="orderhoops", role="Cream"),
    dict(kind="course", h=1.6, b=1.4, orn="insulators", role="Green"),
    dict(kind="crown", h=2.0, b=1.4, P=3.4, orn="ovolo", role="Cream")])
EAVE = dict(pitch=9.0, margin=3.5, layers=[
    dict(kind="frieze", h=5.0, b=1.2, orn="lanterns", role="Cream"),
    dict(kind="course", h=1.6, b=1.4, orn="insulators", role="Green"),
    dict(kind="bed", h=2.4, b=1.4, P=7.0, role="Cream", brackets=dict(style="officestick", t=1.6, reach=0.5)),
    dict(kind="crown", h=2.0, b=1.4, P=7.4, orn="cavetto", role="Green")])
BAY_C = dict(pitch=6.0, margin=2.0, layers=[
    dict(kind="course", h=1.6, b=1.2, orn="insulators", role="Green"),
    dict(kind="crown", h=1.8, b=1.4, P=3.0, orn="ovolo", role="Cream")])
RJ = round((LEDGE + 0.4 + CO.band_height(JOINT)) / 0.2) * 0.2
HE = CO.band_height(EAVE)

# ------------------------------------------------------------------ levels and plan
ZF = 4.0
S1 = ZF + 30.0
ZE = S1 + RJ + 26.0
ZW = round((ZE + HE) / 0.2) * 0.2
FASCIA = 1.4
Z_EAVE = ZW + FASCIA
D_EAVE = 6.0
S_MAIN = 0.55
W, D = 56.0, 38.0
XC, YC = W / 2, D / 2
MAIN = Block("main", [(0, 0), (W, 0), (W, D), (0, D)], ZF, ZW)
BAY_LEDGE = ZF + 23.0
BAY_TOP = round((BAY_LEDGE + CO.band_height(BAY_C)) / 0.2) * 0.2
BAY = Block("bay", [(14.0, 0.0), (18.0, -8.0), (34.0, -8.0), (38.0, 0.0), (38.0, 3.0), (14.0, 3.0)], ZF, BAY_TOP)
BLOCKS = [MAIN, BAY]
ZR = Z_EAVE + S_MAIN * (D / 2 + D_EAVE)
V2 = S1 + RJ + 5.0 - ZF
SIGN_X, SIGN_L, SIGN_H = 28.0, 24.0, 5.0
DOOR_X = 47.0
CHIM = (46.0, 28.0)
LK = 16.0


def _openings():
    L = []

    def add(blk, x, y, v0, sp, name, kind="window"):
        e, u = blk.locate(x, y)
        L.append(Opening(blk, e, u, v0, sp, name, kind))

    lo = YD.window_office_lower(8.0, 14.0)
    up = YD.window_office_upper(8.0, 13.0)
    add(BAY, 26.0, -8.0, 4.0, YD.window_office_lower(8.0, 12.0), "bay-front")
    add(BAY, 16.0, -4.0, 4.0, YD.window_office_lower(4.6, 12.0), "bay-west")
    add(BAY, 36.0, -4.0, 4.0, YD.window_office_lower(4.6, 12.0), "bay-east")
    add(MAIN, 7.0, 0.0, 6.0, lo, "S7")
    add(MAIN, DOOR_X, 0.0, 4.4, YD.door_yardoffice(10.0, 21.0), "door", "door")
    for x in (8.0, 48.0):
        add(MAIN, x, 0.0, V2, up, f"S{x:.0f}-2")
    for y in (11.0, 27.0):
        add(MAIN, W, y, 6.0, lo, f"E{y:.0f}")
        add(MAIN, W, y, V2, up, f"E{y:.0f}-2")
    add(MAIN, 0.0, YC, 6.0, lo, "W")
    add(MAIN, 0.0, YC, V2, up, "W-2")
    for x in (14.0, 42.0):
        add(MAIN, x, D, 6.0, lo, f"N{x:.0f}")
        add(MAIN, x, D, V2, up, f"N{x:.0f}-2")
    return L


OPENINGS = _openings()


def _skin(f, b, reg):
    top = (BAY_LEDGE if b is BAY else ZE) - b.z0
    reg = reg - rect(-1, top - LEDGE - 0.6, f.L + 1, ZW - b.z0 + 0.2)
    if b is MAIN and np.allclose(MAIN.facades()[0].n, f.n):
        reg = reg - rect(SIGN_X - SIGN_L / 2 - 0.3, V2 + 12.5 - 0.3, SIGN_X + SIGN_L / 2 + 0.3, V2 + 12.5 + SIGN_H + 0.3)
    lo = reg ^ rect(-1, -100, f.L + 1, S1 - b.z0)
    hi = reg ^ rect(-1, S1 + RJ - b.z0, f.L + 1, 999)
    out = YD.rustic_channel(lo, datum=0.0)
    if not hi.is_empty():
        out = out + YD.boards_vgroove(hi, datum=0.0, band=V2 - 1.6)
    return out


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    base = MAIN.cs
    allcs = MAIN.cs + BAY.cs
    undress = [slab(offset(base, 10.0), ZE - LEDGE - 0.6, ZW + 0.01),
               slab(offset(BAY.cs, 8.0) ^ rect(0.0, -200.0, 400.0, -0.6), BAY_LEDGE - LEDGE - 0.6, BAY_TOP + 0.01)]
    st = stacked_shells(BLOCKS, OPENINGS, [S1], t=3.0, corners="none", siding=_skin,
                        prof=CO.joint_profile(RJ, LEDGE), belt_blocks=None, water_table=False, undress=undress)
    ledge_b = CO.ledge(BAY.pts, BAY_LEDGE, LEDGE) - MAIN.solid(grow=0.2, dz0=-1, dz1=1)
    kit.add("WALLS-1", "Ochre", st["shells"][0] - lip_keep(allcs, 3.0, ZF, 1.2) + ledge_b, group="walls")
    kit.add("JOINT", "Ochre", st["rings"][0], group="walls")
    w2 = st["shells"][1] + _corbel(base, 3.0, ZW) + lip_ring(base, 3.0, ZW) + CO.ledge(MAIN.pts, ZE, LEDGE)
    kit.add("WALLS-2", "Ochre", w2, group="walls")
    rings, _ = CO.level(st["outlines"][0], S1 + LEDGE + 0.4, JOINT)
    CO.add_level(kit, rings, "CORNICE-J", "cornice")
    rings, _ = CO.level(MAIN.pts, ZE, EAVE)
    CO.add_level(kit, rings, "CORNICE-E", "cornice")
    rings, _ = CO.level(BAY.pts, BAY_LEDGE, BAY_C, cut=MAIN.solid(grow=0.7, dz0=-2, dz1=2))
    CO.add_level(kit, rings, "CORNICE-B", "bay")
    fnd = foundation(BLOCKS, 0.0, ZF, style="sandstone")
    kit.add("FOUNDATION", "Sandstone", fnd, group="foundation")
    ins = []
    for op in OPENINGS:
        A = op.local_frame()
        sp = op.spec
        bb = sp["cut"].bounds()
        key = "DOOR" if op.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, "Windows_Doors", "Door" if op.kind == "door" else "Windows_Doors", "Glass")
        p_ = kit.add(f"{key}-{op.name}", "Windows_Doors", world, P=P, key=f"{key}-{bb[2] - bb[0]:.1f}x{bb[3] - bb[1]:.1f}",
                     group="inserts", render=zones)
        ins.append(p_.solid)
    f = MAIN.facades()[0]
    A = f.A.copy()
    A[:, 3] = f.world(SIGN_X, V2 + 12.5, 0.0)
    sb, letters = YD.sign_yard("YARD OFFICE", SIGN_L, SIGN_H, cap=3.0)
    kit.add("SIGN", "Cream", sb.transform(A), P=np.column_stack([np.vstack([A[:, 0], A[:, 1], A[:, 2]]), np.zeros(3)]),
            group="walls", render=[("Cream", (sb - letters).transform(A)), ("Letters", letters.transform(A))])
    e, u = MAIN.locate(DOOR_X, 0.0)
    Ad = f.A.copy()
    Ad[:, 3] = f.world(u, -ZF, 0.5)
    stoop = YD.stoop_yard(13.0, ZF + 4.2, 2).transform(Ad) - fnd - union(ins)
    kit.add("STOOP", "Timber", stoop, group="porch")
    print("walls + cornices + inserts", round(time.time() - t0, 1))

    # --- the hip roof of bead-butt shingles, the lookout on a flat seat, the chimney
    pieces = [(MAIN.pts, [0, 1, 2, 3], S_MAIN)]
    rf = G.gabled_roof(pieces, Z_EAVE, D_EAVE, [], texture="beadbutt", tex_kw=dict(pitch=1.7, wtab=2.2, d=0.35),
                       inner_cs=offset(base, -3.0), fascia=FASCIA, hollow=2.6)
    roof = rf["body"] + rf["tex"]
    corners = [(-D_EAVE, -D_EAVE), (W + D_EAVE, -D_EAVE), (W + D_EAVE, D + D_EAVE), (-D_EAVE, D + D_EAVE)]
    ends = [(D / 2, YC), (W - D / 2, YC), (W - D / 2, YC), (D / 2, YC)]
    roof = roof + G.ridge_cap((D / 2, YC), (W - D / 2, YC), ZR, S_MAIN, ZW, half=1.1, up=0.6)
    roof = roof + union([G.hip_cap((c[0], c[1], Z_EAVE), (e_[0], e_[1], ZR), half=1.1, up=0.6, drop=1.6) for c, e_ in zip(corners, ends)])
    roof = (roof - lip_keep(base, 3.0, ZW)).trim_by_plane([0, 0, 1.0], ZW)
    solid_env, _ = R.hip_roof(pieces, Z_EAVE, S_MAIN, D_EAVE, texture=None, zlo=ZW)
    z_lk = round((ZR - S_MAIN * (LK / 2 + 1.5) - 0.4) / 0.2) * 0.2
    roof = roof + (box([XC - LK / 2 - 1.4, YC - LK / 2 - 1.4, ZW + 0.01], [XC + LK / 2 + 1.4, YC + LK / 2 + 1.4, z_lk + 0.01]) ^ solid_env)
    roof = roof - box([XC - LK / 2 - 0.8, YC - LK / 2 - 0.8, z_lk], [XC + LK / 2 + 0.8, YC + LK / 2 + 0.8, ZR + 60])
    cx, cy = CHIM
    CW = 6.4
    zc = Z_EAVE + S_MAIN * (D + D_EAVE - cy - CW / 2 - 0.4)
    z0 = round((zc - 4.0) / 0.2) * 0.2
    roof = roof + (box([cx - CW / 2 - 1.6, cy - CW / 2 - 1.6, ZW + 0.01], [cx + CW / 2 + 1.6, cy + CW / 2 + 1.6, z0 + 0.01]) ^ solid_env)
    roof = roof - box([cx - CW / 2 - 0.5, cy - CW / 2 - 0.5, z0], [cx + CW / 2 + 0.5, cy + CW / 2 + 0.5, ZR + 60])
    kit.add("ROOF", "Shingle", roof, group="roof")
    lk, lglass = YD.lookout_yard(LK, h0=3.0, hw=9.0)
    lk, lglass = lk.translate([XC, YC, z_lk]), lglass.translate([XC, YC, z_lk])
    zch = round((3.0 + 9.0 + 0.01) / 0.2) * 0.2
    kit.add("LOOKOUT", "Ochre", lk, group="roof", change=(zch, "Shingle"),
            render=[("Ochre", lk - lglass - box([-999, -999, z_lk + zch], [999, 999, 999])),
                    ("Shingle", lk ^ box([-999, -999, z_lk + zch], [999, 999, 999])), ("Glass", lk ^ lglass)])
    kit.add("CHIMNEY", "Brick", YD.chimney_yard(CW, CW, ZR + 8.0 - z0).translate([cx, cy, z0]), group="roof")
    # --- the bay's low hip under the joint
    bay_keep = MAIN.solid(grow=0.45, dz0=-1, dz1=300)
    broof, btex = R.hip_roof([(BAY.pts, [0, 1, 2])], BAY_TOP, 0.9, BAY_C["layers"][-1]["P"] + 0.2, texture="beadbutt",
                             flat_top=S1 - 0.4, tex_kw=dict(pitch=1.5, wtab=2.0, d=0.3), zlo=BAY_TOP)
    kit.add("BAY-ROOF", "Shingle", (broof + btex) - bay_keep, group="bay")
    print("roof", round(time.time() - t0, 1))
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "yardoffice")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:80]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "yardoffice.npz"))
    import json
    json.dump({"materials": {k: list(v) for k, v in PALETTE.items()}, "views": VIEWS},
              open(os.path.join(OUT, "palette.json"), "w"), indent=1)
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))

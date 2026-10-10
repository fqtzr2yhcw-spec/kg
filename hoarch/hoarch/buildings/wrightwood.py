"""The Wrightwood: an original HO-scale (1:87.1) Prairie School house, house 53 of the fifth batch
(the Craftsman era, 1900-1930).

Long and low: a two-storey centre block between one-storey wings, all under low hipped roofs of
ribbed clay tile with very broad eaves. Up to the sill line the walls are long tawny Roman
brick with deep-raked bed joints and flush head joints; above, smooth stucco crossed by
flat wood bands. The windows run in ribbons of casements leaded in art-glass geometry (two
verticals, a high transom line, little squares) over long projecting sills; the door is a tall
art-glass leaf between art-glass sidelights, set back under a broad slab lintel. On a plinth of
long limestone blocks. Between the storeys a frieze of art-glass geometry over two raised
lines; at the eaves Prairie trees of life. Across the front an open terrace with brick parapet
walls, limestone copings and a shallow planter on each corner pier. A broad low chimney with an
overhanging slab cap straddles the ridge.

usage: python3 -m hoarch.buildings.wrightwood [check] [export]
"""
import os
import sys
import time

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import box, offset, poly, rect, slab, union
from hoarch import craftsman as CR, cornice as CO, features as FT, gables as G, openings as O, roof as R
from hoarch.kit import Kit
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, stacked_shells

NAME = "The Wrightwood"
COLORS = {"Tawny": "#A9764B", "Stucco": "#E6DCC3", "Walnut": "#4E3524", "Terracotta": "#8A4632", "Limestone": "#CFC6B0",
          "Moss": "#5E6B4E", "Windows_Doors": "#4E3524"}
RENDER_MAT = {"Tawny": "brick", "Stucco": "siding", "Walnut": "wood", "Terracotta": "roof", "Limestone": "stone",
              "Moss": "accent", "Windows_Doors": "wood", "Door": "door", "Glass": "glass"}

# ------------------------------------------------------------------ cornices (unique to the Wrightwood)
LEDGE = 1.4
JOINT = dict(pitch=14.0, margin=4.0, layers=[
    dict(kind="frieze", h=4.2, b=1.2, orn="artglass", role="Walnut"),
    dict(kind="course", h=1.4, b=1.4, orn="doubleline", role="Stucco"),
    dict(kind="crown", h=2.0, b=1.4, P=3.4, orn="stepped", role="Walnut")])
EAVE = dict(pitch=16.0, margin=4.0, layers=[
    dict(kind="frieze", h=4.6, b=1.2, orn="treeoflife", role="Walnut"),
    dict(kind="course", h=1.4, b=1.4, orn="doubleline", role="Stucco"),
    dict(kind="crown", h=2.2, b=1.4, P=4.0, orn="bevel", role="Walnut")])
WING_C = dict(pitch=14.0, margin=3.0, layers=[
    dict(kind="frieze", h=4.0, b=1.2, orn="treeoflife", role="Walnut"),
    dict(kind="course", h=1.2, b=1.2, orn="doubleline", role="Stucco"),
    dict(kind="crown", h=2.0, b=1.2, P=3.6, orn="bevel", role="Walnut")])
RJ = round((LEDGE + 0.4 + CO.band_height(JOINT)) / 0.2) * 0.2
HE = CO.band_height(EAVE)

# ------------------------------------------------------------------ levels and plan
ZF = 8.0
S1 = ZF + 36.0
ZU = S1 + RJ
ZE = ZU + 30.0
ZW = round((ZE + HE) / 0.2) * 0.2
FASCIA = 1.6
Z_EAVE = ZW + FASCIA
D_EAVE = 12.0
S_MAIN = 0.33
MX0, MX1, MD = 44.0, 150.0, 100.0               # the centre block
W = 194.0
XC, YC = (MX0 + MX1) / 2, MD / 2
WY0, WY1 = 14.0, 86.0                           # the wings
WING_ZE = ZF + 30.0
WING_ZW = round((WING_ZE + CO.band_height(WING_C)) / 0.2) * 0.2
WING_EAVE = WING_ZW + 1.4
D_EAVE_W = 10.0
MAIN = Block("main", [(MX0, 0), (MX1, 0), (MX1, MD), (MX0, MD)], ZF, ZW)
WINGW = Block("wingw", [(0.0, WY0), (MX0 + 3.0, WY0), (MX0 + 3.0, WY1), (0.0, WY1)], ZF, WING_ZW)
WINGE = Block("winge", [(MX1 - 3.0, WY0), (W, WY0), (W, WY1), (MX1 - 3.0, WY1)], ZF, WING_ZW)
BLOCKS = [MAIN, WINGW, WINGE]
V1 = 8.0
V2 = ZU - ZF + 4.0
SILL = V1 - 2.4                                 # brick below, stucco above (from ZF)
TD = 24.0                                       # the terrace's depth


def _skin(f, b, reg):
    top = (WING_ZE if b is not MAIN else ZE) - LEDGE - 0.6 - b.z0
    reg = reg - rect(-1, top, f.L + 1, 999)
    lo = reg ^ rect(-1, -50, f.L + 1, SILL)
    hi = reg - rect(-1, -50, f.L + 1, SILL)
    out = CR.brick_prairie(lo) if not lo.is_empty() else M()
    if not hi.is_empty():
        bands = [SILL, V1 + 18.0 + 2.2] + ([V2 + 16.0 + 2.2] if b is MAIN else [])
        out = out + CR.stucco_banded(hi, bands=bands, seed=int(f.p0[0] + f.p0[1]))
    return out


def _openings():
    L = []

    def add(blk, x, y, v0, sp, name, kind="window"):
        e, u = blk.locate(x, y)
        L.append(Opening(blk, e, u, v0, sp, name, kind))

    r3 = CR.window_artglass(28.0, 18.0, n=3)
    r4 = CR.window_artglass(34.0, 18.0, n=4)
    u5 = CR.window_artglass(48.0, 16.0, n=5)
    w3 = CR.window_artglass(28.0, 16.0, n=3)
    w4 = CR.window_artglass(34.0, 16.0, n=4)
    add(MAIN, XC, 0.0, 0.4, CR.door_prairie(10.0, 22.0), "front-door", "door")
    add(MAIN, 67.0, 0.0, V1, r3, "S67")
    add(MAIN, 127.0, 0.0, V1, r3, "S127")
    add(MAIN, XC, 0.0, V2, u5, "S-2")
    add(MAIN, 70.0, MD, V1, r3, "N70")
    add(MAIN, 124.0, MD, 0.4, CR.door_prairie(8.0, 21.0, side=2.4), "back-door", "door")
    add(MAIN, XC, MD, V2, u5, "N-2")
    for blk, xa, xb, tag in ((WINGW, 0.0, MX0, "W"), (WINGE, MX1, W, "E")):
        xm = (xa + xb) / 2
        add(blk, xm, WY0, V1, w4, f"{tag}-S")
        add(blk, xm, WY1, V1, w3, f"{tag}-N")
        add(blk, xa if tag == "W" else xb, (WY0 + WY1) / 2, V1, w3, f"{tag}-end")
    return L


OPENINGS = _openings()


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    base = MAIN.cs
    wings = [WINGW, WINGE]
    undress = [slab(offset(base, 12.0), ZE - LEDGE - 0.6, ZW + 0.01)] + \
        [slab(offset(wb.cs, 10.0) - offset(base, 0.5), WING_ZE - LEDGE - 0.6, WING_ZW + 0.01) for wb in wings]
    clear = [lip_keep(base, 3.0, ZF, 1.2)] + [lip_keep(wb.cs, 3.0, ZF, 1.2) for wb in wings]
    st = stacked_shells(BLOCKS, OPENINGS, [S1], t=3.0, corners="none", siding=_skin, gables=[], clear=clear,
                        prof=CO.joint_profile(RJ, LEDGE), belt_blocks=None, water_table=False, undress=undress,
                        partitions=[((XC, 3.0), (XC, MD - 3.0), 2.0, ZF, ZW)])
    extra = M()
    for wb in wings:
        extra = extra + ((_corbel(wb.cs, 3.0, WING_ZW) + lip_ring(wb.cs, 3.0, WING_ZW)) - MAIN.solid(grow=0.3, dz0=-5, dz1=5))
        extra = extra + (CO.ledge(wb.pts, WING_ZE, LEDGE) - MAIN.solid(grow=0.2, dz0=-1, dz1=1))
    jring = st["rings"][0]
    w1 = st["shells"][0] + (extra - jring)
    below = box([-50, -50, -1], [W + 50, MD + 50, ZF + SILL])
    hc = round(SILL / 0.2) * 0.2
    kit.add("WALLS-1", "Tawny", w1, group="walls", change=(hc, "Stucco"), render=[("Tawny", w1 ^ below), ("Stucco", w1 - below)])
    kit.add("JOINT", "Stucco", st["rings"][0], group="walls")
    lip = _corbel(base, 3.0, ZW) + lip_ring(base, 3.0, ZW)
    kit.add("WALLS-2", "Stucco", st["shells"][1] + lip + CO.ledge(MAIN.pts, ZE, LEDGE), group="walls")
    wenvs = []
    for wb, ex in ((WINGW, [0, 2, 3]), (WINGE, [0, 1, 2])):
        env, _ = R.hip_roof([(wb.pts, ex, S_MAIN)], WING_EAVE + 0.6, S_MAIN, D_EAVE_W + 0.6, texture=None, zlo=WING_ZW - 1.0)
        wenvs.append(env)
    rings, _ = CO.level(st["outlines"][0], S1 + LEDGE + 0.4, JOINT, cut=union(wenvs))
    CO.add_level(kit, rings, "CORNICE-J", "cornice")
    rings, _ = CO.level(MAIN.pts, ZE, EAVE)
    CO.add_level(kit, rings, "CORNICE-E", "cornice")
    for wb, tag in ((WINGW, "W"), (WINGE, "E")):
        rings, _ = CO.level(wb.pts, WING_ZE, WING_C, cut=MAIN.solid(grow=0.7, dz0=-2, dz1=2) + jring)
        CO.add_level(kit, rings, f"CORNICE-WING{tag}", "cornice")
    fnd = foundation(BLOCKS, 0.0, ZF, style="prairieplinth")
    kit.add("FOUNDATION", "Limestone", fnd, group="foundation")
    ins_keep = []
    for op in OPENINGS:
        A = op.local_frame()
        sp = op.spec
        b = sp["cut"].bounds()
        key = "DOOR" if op.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, "Windows_Doors", "Door" if op.kind == "door" else "Windows_Doors", "Glass")
        part = kit.add(f"{key}-{op.name}", "Windows_Doors", world, P=P,
                       key=f"{key}-{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}-{op.v0 > 20}", group="inserts", render=zones)
        ins_keep.append(part.solid)
    print("walls + cornices + inserts", round(time.time() - t0, 1))

    # --- the roofs: low hips of ribbed tile, very broad eaves, the broad stack on the ridge
    pieces = [(MAIN.pts, [0, 1, 2, 3], S_MAIN)]
    rf = G.gabled_roof(pieces, Z_EAVE, D_EAVE, [], texture="ribtile", tex_kw=dict(pitch=2.2, seam_pitch=3.0, d=0.35),
                       inner_cs=offset(base, -3.0), fascia=FASCIA, hollow=2.4)
    roof = rf["body"] + rf["tex"]
    Wm = MX1 - MX0
    zr = Z_EAVE + S_MAIN * (MD / 2 + D_EAVE)
    corners = [(MX0 - D_EAVE, -D_EAVE), (MX1 + D_EAVE, -D_EAVE), (MX1 + D_EAVE, MD + D_EAVE), (MX0 - D_EAVE, MD + D_EAVE)]
    ends = [(MX0 + MD / 2, YC), (MX1 - MD / 2, YC), (MX1 - MD / 2, YC), (MX0 + MD / 2, YC)]
    roof = roof + G.ridge_cap((MX0 + MD / 2, YC), (MX1 - MD / 2, YC), zr, S_MAIN, ZW, half=1.3, up=0.7)
    roof = roof + union([G.hip_cap((c[0], c[1], Z_EAVE), (e[0], e[1], zr), half=1.3, up=0.7, drop=1.6) for c, e in zip(corners, ends)])
    roof = roof - lip_keep(base, 3.0, ZW)
    roof = roof.trim_by_plane([0, 0, 1.0], Z_EAVE - FASCIA)
    solid_env, _ = R.hip_roof(pieces, Z_EAVE, S_MAIN, D_EAVE, texture=None, zlo=ZW)
    CW, CD = 26.0, 8.0
    z0 = round((zr - 6.0) / 0.2) * 0.2
    roof = roof + (box([XC - CW / 2 - 1.8, YC - CD / 2 - 1.8, ZW + 0.01], [XC + CW / 2 + 1.8, YC + CD / 2 + 1.8, z0 + 0.01]) ^ solid_env)
    roof = roof - box([XC - CW / 2 - 0.5, YC - CD / 2 - 0.5, z0], [XC + CW / 2 + 0.5, YC + CD / 2 + 0.5, zr + 60])
    kit.add("ROOF", "Terracotta", roof, group="roof")
    kit.add("CHIMNEY", "Tawny", CR.chimney_prairie(CW, CD, zr + 9.0 - z0).translate([XC, YC, z0]), group="roof")
    main_keep = union([p.solid for p in kit.parts if p.name in ("WALLS-1", "JOINT", "WALLS-2") or p.name.startswith("CORNICE")])
    for wb, ex, tag in ((WINGW, [0, 2, 3], "W"), (WINGE, [0, 1, 2], "E")):
        wrf = G.gabled_roof([(wb.pts, ex, S_MAIN)], WING_EAVE, D_EAVE_W, [], texture="ribtile",
                            tex_kw=dict(pitch=2.2, seam_pitch=3.0, d=0.35), inner_cs=offset(wb.cs, -3.0), fascia=1.4, hollow=2.4)
        wr = (wrf["body"] + wrf["tex"]) - MAIN.solid(grow=0.35, dz0=-5, dz1=300) - main_keep - union(ins_keep) - lip_keep(wb.cs, 3.0, WING_ZW)
        wr = wr.trim_by_plane([0, 0, 1.0], WING_ZW)
        kit.add(f"WING-roof-{tag}", "Terracotta", max(wr.decompose(), key=lambda m_: m_.volume()), group="roof")
    print("roofs", round(time.time() - t0, 1))

    # --- the terrace across the front: a floor, brick parapet walls and corner piers (one
    # piece), limestone copings with a planter on each pier (one piece), steps at the door
    TX0, TX1 = MX0 + 4.0, MX1 - 4.0
    H_t = ZF - 1.4
    t = 2.6
    hp = H_t + 8.0
    gap = 16.0
    walls_t = [box([TX0, -TD, H_t - 0.01], [TX1, -TD + t, hp]), box([TX0, -TD, H_t - 0.01], [TX0 + t, -0.2, hp]),
               box([TX1 - t, -TD, H_t - 0.01], [TX1, -0.2, hp])]
    piers = [box([x - 3.4, -TD - 0.8, 0.0], [x + 3.4, -TD + 5.8, hp + 1.6]) for x in (TX0 + 2.6, TX1 - 2.6)]
    floor_ = box([TX0, -TD, 0.0], [TX1, -0.2, H_t])
    terr = floor_ + union(walls_t) + union(piers) - box([XC - gap / 2, -TD - 5, H_t], [XC + gap / 2, -TD + t + 0.5, hp + 5])
    face = (CR.brick_prairie(rect(0.0, 0.0, TX1 - TX0, hp)).transform(np.array([[1.0, 0, 0, TX0], [0, 0, -1.0, -TD], [0, 1.0, 0, 0]])))
    face = face - box([XC - gap / 2, -TD - 5, H_t], [XC + gap / 2, -TD + t + 0.5, hp + 5]) - union(piers)
    terr = terr + face
    fkeep = slab(offset(base, 0.8 + 0.55 + 0.15), -1, ZF + 1.3)
    terr = terr - fkeep - fnd - w1 - union(ins_keep)
    kit.add("TERRACE", "Tawny", terr, group="terrace")
    cop = [box([TX0 - 0.8, -TD - 0.8, hp - 0.01], [XC - gap / 2, -TD + t + 0.8, hp + 1.0]),
           box([XC + gap / 2, -TD - 0.8, hp - 0.01], [TX1 + 0.8, -TD + t + 0.8, hp + 1.0]),
           box([TX0 - 0.8, -TD - 0.8, hp - 0.01], [TX0 + t + 0.8, -3.0, hp + 1.0]),
           box([TX1 - t - 0.8, -TD - 0.8, hp - 0.01], [TX1 + 0.8, -3.0, hp + 1.0])]
    # each pier cap is a sleeve over its pier's top, down to the copings (one piece with them)
    pcaps = [box([x - 4.2, -TD - 1.6, hp - 0.01], [x + 4.2, -TD + 6.6, hp + 2.6]) for x in (TX0 + 2.6, TX1 - 2.6)]
    urns = [CR.planter_urn(3.2, 3.6, 3.8).translate([x, -TD + 2.5, hp + 2.59]) for x in (TX0 + 2.6, TX1 - 2.6)]
    coping = union(cop) + union(pcaps) + union(urns) - union(piers)
    coping = coping - fkeep - terr - union(ins_keep) - w1
    for tag, xa, xb in (("W", -50.0, XC), ("E", XC, W + 50.0)):
        kit.add(f"TERRACE-coping-{tag}", "Limestone", coping ^ box([xa, -60.0, -1.0], [xb, 60.0, 200.0]), group="terrace")
    fr = MAIN.facades()[0]
    A = fr.A.copy()
    A[:, 3] = fr.world(XC - MX0, -ZF, TD)
    kit.add("TERRACE-steps", "Limestone", FT.steps(gap - 0.4, H_t - 0.6, 3).transform(A) - terr, group="terrace")
    e, u = MAIN.locate(124.0, MD)
    fb = MAIN.facades()[e]
    A = fb.A.copy()
    A[:, 3] = fb.world(u, -ZF, 1.4)
    kit.add("STOOP-back", "Limestone", FT.steps(14.0, ZF - 0.6, 3).transform(A) - fnd, group="terrace")
    FT.key_into(kit, "TERRACE-steps", ["TERRACE"], (0, 1, 0), depth=0.8, conform=True)
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "wrightwood")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:80]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "wrightwood.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))

"""The Ridgely: an original HO-scale (1:87.1) Baltimore Federal row of three houses, house 50
of the fourth batch (all Colonial).

Three brick houses built as one row, two storeys and an attic over a raised basement of
boasted brownstone, in Flemish stretcher bond. Each house has its doorway at the end of the
row or beside the carriage passage: a six-panel door under a half-round fanlight leaded in
rays hung with swags, in a round arch of marble voussoirs on panelled pilasters, up a flight
of white marble steps. Through the middle house runs an arched carriage passage, a barrel
vault with a ring of marble voussoirs at each mouth. Tall six-over-nine parlour windows under
splayed marble flat arches with keystones; six-over-six chamber windows under marble lintels
with a bead and bull's-eye end blocks. Between the storeys a frieze of Federal shields and
crossed olive sprigs over a hit-and-miss course; at the eave cords looped in festoons with
tassels from rosettes, dentils, corbelled modillions and an ovolo. A gabled roof of
batten-seam tin with three twin-arched dormers front and back, broad party-wall stacks with
four clay pots each, and a stack inside each gable end.

usage: python3 -m hoarch.buildings.ridgely [check] [export]
"""
import os
import sys
import time

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import box, circle, offset, rect, slab, union
from hoarch import colonial4 as C4, cornice as CO, features as FT, gables as G, openings as O, roof as R
from hoarch.kit import Kit
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, stacked_shells

NAME = "The Ridgely"
COLORS = {"Brick": "#9A4432", "Marble": "#ECEAE4", "Cream": "#F1EADB", "Green": "#2D4A3A", "Tin": "#4B4F55",
          "Brownstone": "#6B4A3C", "Windows_Doors": "#ECEAE4"}
RENDER_MAT = {"Brick": "brick", "Marble": "marble", "Cream": "trim", "Green": "accent", "Tin": "roof",
              "Brownstone": "stone", "Windows_Doors": "marble", "Door": "door", "Glass": "glass"}

# ------------------------------------------------------------------ cornices (unique to the Ridgely)
LEDGE = 1.4
JOINT = dict(pitch=16.0, margin=4.0, layers=[
    dict(kind="frieze", h=4.4, b=1.2, orn="shields", role="Cream"),
    dict(kind="course", h=1.4, b=1.4, orn="hitmiss", role="Green"),
    dict(kind="crown", h=2.2, b=1.4, P=3.4, orn="ogee_fillet", role="Cream")])
EAVE = dict(pitch=15.0, margin=4.0, layers=[
    dict(kind="frieze", h=5.2, b=1.2, orn="tassels", role="Cream"),
    dict(kind="course", h=1.6, b=1.4, orn="dentil", role="Green", tooth=0.7, gap=0.6),
    dict(kind="bed", h=2.2, b=1.4, P=5.6, role="Cream", brackets=dict(style="corbelstep", t=1.4, reach=0.3)),
    dict(kind="crown", h=2.8, b=1.4, P=6.4, orn="ovolo", role="Cream")])
RJ = round((LEDGE + 0.4 + CO.band_height(JOINT)) / 0.2) * 0.2
HE = CO.band_height(EAVE)

# ------------------------------------------------------------------ levels and plan
ZF = 14.0                                       # a raised basement
S1 = ZF + 38.0
ZU = S1 + RJ
ZE = ZU + 34.0
ZW = round((ZE + HE) / 0.2) * 0.2
FASCIA = 1.4
Z_EAVE = ZW + FASCIA
D_EAVE, RAKE, SKIN = 5.0, 5.0, 1.8
S_MAIN = 0.8
W, D = 186.0, 96.0                              # three houses of 62
XC, YC = W / 2, D / 2
MAIN = Block("main", [(0, 0), (W, 0), (W, D), (0, D)], ZF, ZW)
BLOCKS = [MAIN]
V1 = 6.0
V2 = ZU - ZF + 5.0
PW, PSPRING, PT = 13.0, 24.0, 2.0              # the carriage passage: width, springing, wall
UPPER = (13.0, 31.0, 49.0, 71.0, 93.0, 115.0, 137.0, 155.0, 173.0)


def _arch_zone():
    """The passage's arch trim on a front or back wall, in facade (u, v from the block's
    foot): the skin is left off there so the trim sits on the wall's face."""
    r = PW / 2 + PT + 0.15 + 2.6 + 0.3
    vs = PSPRING - ZF
    return (circle((XC, vs), r, 64) ^ rect(XC - r - 1, vs, XC + r + 1, vs + r + 1)) + rect(XC - r - 0.3, vs - 2.0, XC + r + 0.3, vs + 0.01) \
        + rect(XC - 1.8, vs + r - 1.0, XC + 1.8, vs + r + 1.2)


def _skin(f, b, reg):
    reg = reg - rect(-1, ZE - LEDGE - 0.6 - b.z0, f.L + 1, ZW - b.z0 + 0.2)
    if abs(f.n[1]) > 0.5:
        reg = reg - _arch_zone()
    return C4.brick_flemishstretcher(reg, datum=0.0)


def _openings():
    L = []

    def add(x, y, v0, sp, name, kind="window"):
        e, u = MAIN.locate(x, y)
        L.append(Opening(MAIN, e, u, v0, sp, name, kind))

    lo = C4.window_jackkey(10.0, 22.0)
    up = C4.window_beadlintel(10.0, 19.0)
    door = C4.door_swagfan(11.0, 22.0)
    for x in (31.0, 49.0, 71.0, 137.0, 155.0):
        add(x, 0.0, V1, lo, f"S{x:.0f}-1")
    for x in (13.0, 115.0, 173.0):
        add(x, 0.0, 0.4, door, f"S{x:.0f}-door", "door")
    for x in (13.0, 31.0, 115.0, 155.0, 173.0):
        add(x, D, V1, lo, f"N{x:.0f}-1")
    for x in (49.0, 71.0, 137.0):
        add(x, D, 0.4, door, f"N{x:.0f}-door", "door")
    for x in UPPER:
        add(x, 0.0, V2, up, f"S{x:.0f}-2")
        add(x, D, V2, up, f"N{x:.0f}-2")
    for x_, tag in ((0.0, "W"), (W, "E")):
        for y in (30.0, D - 30.0):
            add(x_, y, V1, lo, f"{tag}{y:.0f}-1")
            add(x_, y, V2, up, f"{tag}{y:.0f}-2")
    return L


OPENINGS = _openings()


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    base = MAIN.cs
    pieces = [(MAIN.pts, [0, 2], S_MAIN)]
    gdefs = [dict(p0=(W, 0.0), p1=(W, D), slope=S_MAIN, e=0.3), dict(p0=(0.0, D), p1=(0.0, 0.0), slope=S_MAIN, e=0.3)]
    rf = G.gabled_roof(pieces, Z_EAVE, D_EAVE, gdefs, texture="batten", tex_kw=dict(seam_pitch=3.2, d=0.45),
                       skin=SKIN, rake=RAKE, inner_cs=offset(base, -3.0), fascia=FASCIA, hollow=2.8)
    we, ww = rf["walls"]
    gables = [(MAIN, 1, we["cs"].translate((0.0, Z_EAVE - ZF))), (MAIN, 3, ww["cs"].translate((0.0, Z_EAVE - ZF)))]
    undress = [slab(offset(base, 8.0), ZE - LEDGE - 0.6, ZW + 0.01)]
    clear = [lip_keep(base, 3.0, ZF, 1.2)]
    st = stacked_shells(BLOCKS, OPENINGS, [S1], t=3.0, corners="none", siding=_skin, gables=gables, clear=clear,
                        prof=CO.joint_profile(RJ, LEDGE), belt_blocks=None, water_table=False, undress=undress,
                        partitions=[((62.0, 3.0), (62.0, D - 3.0), 2.0, ZF, ZW), ((124.0, 3.0), (124.0, D - 3.0), 2.0, ZF, ZW)])
    # the carriage passage runs through the middle house under a barrel vault (its own part)
    vault, vout = C4.passage_vault(PW, PSPRING, D, PT)
    vault = vault.translate([XC, 0.0, 0.0])
    tunnel = M.extrude(vout.offset(0.15, C4.JoinType.Miter, 4.0), D + 10.0).transform(
        np.array([[1.0, 0, 0, XC], [0, 0, 1.0, -5.0], [0, 1.0, 0, 0]]))
    kit.add("WALLS-1", "Brick", st["shells"][0] - tunnel, group="walls")
    kit.add("JOINT", "Brick", st["rings"][0], group="walls")
    no_lip = union([box([W - 5.0, -1, ZW - 1], [W + 1, D + 1, ZW + 5]), box([-1, -1, ZW - 1], [5.0, D + 1, ZW + 5])])
    lip = (_corbel(base, 3.0, ZW) + lip_ring(base, 3.0, ZW)) - no_lip
    kit.add("WALLS-2", "Brick", st["shells"][1] + lip + CO.ledge(MAIN.pts, ZE, LEDGE), group="walls")
    rings, _ = CO.level(st["outlines"][0], S1 + LEDGE + 0.4, JOINT)
    CO.add_level(kit, rings, "CORNICE-J", "cornice")
    rings, _ = CO.level(MAIN.pts, ZE, EAVE)
    CO.add_level(kit, rings, "CORNICE-E", "cornice")
    fnd = foundation(BLOCKS, 0.0, ZF, style="boasted") - tunnel
    kit.add("FOUNDATION", "Brownstone", fnd, group="foundation")
    ins_keep = []
    for o in OPENINGS:
        A = o.local_frame()
        sp = o.spec
        b = sp["cut"].bounds()
        key = "DOOR" if o.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, "Windows_Doors", "Door" if o.kind == "door" else "Windows_Doors", "Glass")
        part = kit.add(f"{key}-{o.name}", "Windows_Doors", world, P=P,
                       key=f"{key}-{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}-{o.v0 > 20}", group="inserts", render=zones)
        ins_keep.append(part.solid)
    kit.add("PASSAGE-vault", "Brick", vault, P=np.array([[1.0, 0, 0, 0], [0, 0, -1.0, 0], [0, 1.0, 0, 0]]), group="passage")
    arch, _ = C4.passage_arch(PW, PSPRING, PT)
    for tag, A in (("S", np.array([[1.0, 0, 0, XC], [0, 0, -1.0, 0.0], [0, 1.0, 0, 0]])),
                   ("N", np.array([[-1.0, 0, 0, XC], [0, 0, 1.0, D], [0, 1.0, 0, 0]]))):
        kit.add(f"PASSAGE-arch-{tag}", "Marble", arch.transform(A), P=np.array([[1.0, 0, 0, 0], [0, 0, 1.0, 0], [0, -1.0, 0, 0]])
                if tag == "S" else np.array([[1.0, 0, 0, 0], [0, 0, -1.0, 0], [0, 1.0, 0, 0]]), key="PASSAGE-arch", group="passage")
    print("walls + cornices + inserts + passage", round(time.time() - t0, 1))

    # --- the roof: batten-seam tin, a ridge cap, twin-arched dormers, party-wall and end stacks
    roof = rf["body"] + rf["tex"] + rf["skins"] + rf["skin_tex"]
    zr = Z_EAVE + S_MAIN * (D / 2 + D_EAVE)
    walls_env = union([wl["facade"].place(M.extrude(wl["cs"].offset(0.15), RAKE + 4.2).translate([0, 0, -3.15])) for wl in rf["walls"]])
    roof = roof + (G.ridge_cap((-RAKE, YC), (W + RAKE, YC), zr, S_MAIN, ZW) - walls_env)
    roof = roof - lip_keep(base, 3.0, ZW)
    solid_env, _ = R.hip_roof(pieces, Z_EAVE, S_MAIN, D_EAVE, texture=None, zlo=ZW)
    CW, CD = 8.0, 16.0
    pockets, stacks = [], []
    for cx in (12.0, 62.0, 124.0, W - 12.0):
        z0 = round((zr - 8.0) / 0.2) * 0.2
        roof = roof + (box([cx - CW / 2 - 1.2, YC - CD / 2 - 1.2, ZW + 0.01], [cx + CW / 2 + 1.2, YC + CD / 2 + 1.2, z0 + 0.01]) ^ solid_env)
        pockets.append(box([cx - CW / 2 - 0.4, YC - CD / 2 - 0.4, z0], [cx + CW / 2 + 0.4, YC + CD / 2 + 0.4, zr + 40]))
        stacks.append(C4.chimney_partywall(CW, CD, zr + 13.0 - z0).translate([cx, YC, z0]))
    roof = roof - union(pockets)
    DW, DDEP, DHW = 15.0, 16.0, 12.0
    dyf = 12.0
    zdf = round((Z_EAVE + S_MAIN * (dyf + D_EAVE) - 1.0) / 0.2) * 0.2
    dbody, dcore, dface = C4.dormer_twinarch(DW, DDEP, DHW)
    droof = C4.dormer_twinarch_roof(DW, DDEP, DHW)
    dparts = []
    for dxc in (31.0, XC, W - 31.0):
        for side in (0, 1):
            if side == 0:
                Ad = np.array([[1.0, 0, 0, dxc], [0, 0, -1.0, dyf], [0, 1.0, 0, zdf]])
            else:
                Ad = np.array([[-1.0, 0, 0, dxc], [0, 0, 1.0, D - dyf], [0, 1.0, 0, zdf]])
            dkeep = C4.ext(dface.offset(0.3, C4.JoinType.Miter, 4.0), -DDEP - 0.3, 0.3).transform(Ad)
            dpocket = dkeep ^ box([-500, -500, zdf], [500, 500, 999])
            yb0, yb1 = (dyf - 1.6, dyf + DDEP + 1.3) if side == 0 else (D - dyf - DDEP - 1.3, D - dyf + 1.6)
            dseat = box([dxc - DW / 2 - 1.3, yb0, ZW], [dxc + DW / 2 + 1.3, yb1, zdf]) ^ solid_env
            roof = roof - dpocket
            roof = roof + (dseat - dpocket - lip_keep(base, 3.0, ZW))
            dparts.append(Ad)
    kit.add("ROOF", "Tin", roof, group="roof")
    for k, s_ in enumerate(stacks):
        kit.add(f"CHIMNEY-{k}", "Brick", s_, key="CHIMNEY", group="roof")
    for k, Ad in enumerate(dparts):
        kit.add(f"DORMER-{k}", "Cream", dbody.transform(Ad), key="DORMER", group="roof")
        kit.add(f"DORMER-core-{k}", "Tin", dcore.transform(Ad), key="DORMER-core", group="roof")
        dr = droof.transform(Ad) - solid_env - dbody.transform(Ad) - roof
        kit.add(f"DORMER-roof-{k}", "Tin", max(dr.decompose(), key=lambda m_: m_.volume()), key="DORMER-roof", group="roof")
    print("roof", round(time.time() - t0, 1))

    # --- white marble steps at every door
    for o in OPENINGS:
        if o.kind != "door":
            continue
        f = MAIN.facades()[o.edge]
        A = f.A.copy()
        A[:, 3] = f.world(o.u, -ZF, 1.4)
        kit.add(f"STOOP-{o.name}", "Marble", FT.steps(13.0, ZF - 0.6, 5).transform(A) - fnd, key="STOOP", group="steps")
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "ridgely")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:80]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "ridgely.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))

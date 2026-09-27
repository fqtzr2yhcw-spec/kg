"""The Hollister: an original HO-scale (1:87.1) American Foursquare, house 52 of the fifth batch
(the Craftsman era, 1900-1930).

A square two-storey house under a hipped roof of three-tab asphalt strips with deep eaves and a
hipped dormer on every face, on a base of rock-faced concrete block. The ground storey is
butter-yellow narrow clapboard run round mitred corners, its bottom course flared over the
block; the upper storey is olive shingles laid to two exposures in turn. Between the storeys a
frieze of dragonflies over waterline reeds and a course of rings; at the eave irises between
crossed blades, dentils, rafter tails cut in a cove and a cavetto. A porch runs the width of the
front on round columns banded under their capitals, with Prairie railings of slats in threes, a
banded beam and a fascia of keys, under a low hip. On the east side a box bay of two windows
under its own little hip. Ground-floor windows have a margin of narrow lights round a big
centre light in the upper sash; upstairs three tall lights over one under head shelves on
corbels. The door has a big oval of bevelled glass. A block chimney rises through the back
slope.

usage: python3 -m hoarch.buildings.hollister [check] [export]
"""
import os
import sys
import time

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import box, offset, poly, rect, slab, union
from hoarch import craftsman as CR, cornice as CO, features as FT, gables as G, openings as O, roof as R
from hoarch.kit import Kit, print_flip
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, stacked_shells

NAME = "The Hollister"
COLORS = {"Butter": "#D8C27C", "Olive": "#5F5B3B", "White": "#F1EEE4", "Oxblood": "#6E2A22", "Charcoal": "#4A4B4C",
          "Block": "#B3AC9F", "PorchDeck": "#8A7358", "Windows_Doors": "#F1EEE4"}
RENDER_MAT = {"Butter": "siding", "Olive": "shingle", "White": "trim", "Oxblood": "accent", "Charcoal": "roof",
              "Block": "stone", "PorchDeck": "planks", "Planks": "planks", "Windows_Doors": "trim", "Door": "door",
              "Glass": "glass"}

# ------------------------------------------------------------------ cornices (unique to the Hollister)
LEDGE = 1.4
JOINT = dict(pitch=16.0, margin=4.0, layers=[
    dict(kind="frieze", h=4.4, b=1.2, orn="dragonflies", role="Oxblood"),
    dict(kind="course", h=1.4, b=1.4, orn="rings", role="White"),
    dict(kind="crown", h=2.2, b=1.4, P=3.4, orn="reverse", role="White")])
EAVE = dict(pitch=7.5, margin=3.0, layers=[
    dict(kind="frieze", h=4.8, b=1.2, orn="irises", role="Oxblood"),
    dict(kind="course", h=1.4, b=1.4, orn="dentil", role="White", tooth=0.6, gap=0.6),
    dict(kind="bed", h=2.4, b=1.4, P=7.0, role="White", brackets=dict(style="covetail", t=1.2, reach=0.3)),
    dict(kind="crown", h=1.8, b=1.4, P=7.4, orn="cavetto", role="White")])
BAY_C = dict(pitch=10.0, margin=3.0, layers=[
    dict(kind="frieze", h=3.6, b=1.2, orn="dragonflies", role="Oxblood"),
    dict(kind="course", h=1.2, b=1.2, orn="rings", role="White"),
    dict(kind="crown", h=2.0, b=1.2, P=3.6, orn="reverse", role="White")])
RJ = round((LEDGE + 0.4 + CO.band_height(JOINT)) / 0.2) * 0.2
HE = CO.band_height(EAVE)

# ------------------------------------------------------------------ levels and plan
ZF = 12.0
S1 = ZF + 40.0
ZU = S1 + RJ
ZE = ZU + 36.0
ZW = round((ZE + HE) / 0.2) * 0.2
FASCIA = 1.6
Z_EAVE = ZW + FASCIA
D_EAVE = 8.0
S_MAIN = 0.55
W, D = 164.0, 150.0
XC, YC = W / 2, D / 2
BY0, BY1, BX = 58.0, 96.0, 11.0                 # the box bay on the east side
BAY_ZE = ZF + 30.4
BAY_ZW = round((BAY_ZE + CO.band_height(BAY_C)) / 0.2) * 0.2
BAY_EAVE = BAY_ZW + 1.4
S_BAY, D_EAVE_B = 0.4, 3.4
MAIN = Block("main", [(0, 0), (W, 0), (W, D), (0, D)], ZF, ZW)
BAY = Block("bay", [(W - 3.0, BY0), (W + BX, BY0), (W + BX, BY1), (W - 3.0, BY1)], ZF, BAY_ZW)
BLOCKS = [MAIN, BAY]
V1 = 6.0
V2 = ZU - ZF + 5.0
PD = 30.0                                       # the porch's depth


def _skin(f, b, reg):
    if b is BAY:
        reg = reg - rect(-1, BAY_ZE - LEDGE - 0.6 - b.z0, f.L + 1, 999)
        return CR.clapboard_flared(reg, datum=0.0)
    reg = reg - rect(-1, ZE - LEDGE - 0.6 - b.z0, f.L + 1, 999)
    lo = reg ^ rect(-1, -50, f.L + 1, S1 - b.z0)
    hi = reg ^ rect(-1, ZU - b.z0, f.L + 1, 999)
    out = CR.clapboard_flared(lo, datum=0.0) if not lo.is_empty() else M()
    if not hi.is_empty():
        out = out + CR.shingles_alternate(hi, datum=ZU - b.z0, seed=int(abs(f.n[0]) * 3 + abs(f.n[1]) * 7))
    return out


def _openings():
    L = []

    def add(blk, x, y, v0, sp, name, kind="window"):
        e, u = blk.locate(x, y)
        L.append(Opening(blk, e, u, v0, sp, name, kind))

    lo1 = CR.window_prairieborder(10.0, 19.0)
    lo2 = CR.window_prairieborder(19.0, 19.0, n=2)
    up = CR.window_shelfhead(10.0, 20.0)
    add(MAIN, 36.0, 0.0, 0.4, CR.door_oval(10.0, 21.0), "front-door", "door")
    add(MAIN, 82.0, 0.0, V1, lo1, "S82")
    add(MAIN, 126.0, 0.0, V1, lo2, "S126")
    add(MAIN, 128.0, D, 0.4, CR.door_oval(9.0, 20.0), "back-door", "door")
    for x in (40.0, 84.0):
        add(MAIN, x, D, V1, lo1, f"N{x:.0f}")
    for x in (36.0, 82.0, 128.0):
        add(MAIN, x, 0.0, V2, up, f"S{x:.0f}-2")
        add(MAIN, x, D, V2, up, f"N{x:.0f}-2")
    add(MAIN, 0.0, 40.0, V1, lo2, "W40")
    add(MAIN, 0.0, 110.0, V1, lo1, "W110")
    for y in (30.0, 124.0):
        add(MAIN, W, y, V1, lo1, f"E{y:.0f}")
    for y in (40.0, 110.0):
        add(MAIN, 0.0, y, V2, up, f"W{y:.0f}-2")
    for y in (40.0, (BY0 + BY1) / 2, 110.0):
        add(MAIN, W, y, V2, up, f"E{y:.0f}-2")
    add(BAY, W + BX, (BY0 + BY1) / 2, V1, lo2, "bay")
    return L


OPENINGS = _openings()


def _frame(u, v, w, o):
    return np.column_stack([u, v, w, o]).astype(float)


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    base = MAIN.cs
    undress = [slab(offset(base, 9.0), ZE - LEDGE - 0.6, ZW + 0.01),
               slab(offset(BAY.cs, 8.0) - offset(base, 0.5), BAY_ZE - LEDGE - 0.6, BAY_ZW + 0.01)]
    clear = [lip_keep(base, 3.0, ZF, 1.2)]
    st = stacked_shells(BLOCKS, OPENINGS, [S1], t=3.0, corners="none", siding=_skin, gables=[], clear=clear,
                        prof=CO.joint_profile(RJ, LEDGE), belt_blocks=None, water_table=False, undress=undress,
                        partitions=[((XC, 3.0), (XC, D - 3.0), 2.0, ZF, ZW)])
    bay_lip = (_corbel(BAY.cs, 3.0, BAY_ZW) + lip_ring(BAY.cs, 3.0, BAY_ZW)) - MAIN.solid(grow=0.3, dz0=-5, dz1=5)
    bay_ledge = CO.ledge(BAY.pts, BAY_ZE, LEDGE) - MAIN.solid(grow=0.2, dz0=-1, dz1=1)
    kit.add("WALLS-1", "Butter", st["shells"][0] + bay_lip + bay_ledge, group="walls")
    kit.add("JOINT", "Butter", st["rings"][0], group="walls")
    lip = _corbel(base, 3.0, ZW) + lip_ring(base, 3.0, ZW)
    kit.add("WALLS-2", "Olive", st["shells"][1] + lip + CO.ledge(MAIN.pts, ZE, LEDGE), group="walls")
    bay_env, _ = R.hip_roof([(BAY.pts, [0, 1, 2], S_BAY)], BAY_EAVE + 0.6, S_BAY, D_EAVE_B + 0.6, texture=None, zlo=BAY_ZW - 1.0)
    rings, _ = CO.level(st["outlines"][0], S1 + LEDGE + 0.4, JOINT, cut=bay_env)
    CO.add_level(kit, rings, "CORNICE-J", "cornice")
    rings, _ = CO.level(MAIN.pts, ZE, EAVE)
    CO.add_level(kit, rings, "CORNICE-E", "cornice")
    rings, _ = CO.level(BAY.pts, BAY_ZE, BAY_C, cut=MAIN.solid(grow=0.7, dz0=-2, dz1=2))
    CO.add_level(kit, rings, "CORNICE-BAY", "cornice")
    fnd = foundation(BLOCKS, 0.0, ZF, style="rockblock")
    kit.add("FOUNDATION", "Block", fnd, group="foundation")
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

    # --- the main roof: a hip of three-tab strips, caps, a dormer on every face, a block stack
    pieces = [(MAIN.pts, [0, 1, 2, 3], S_MAIN)]
    rf = G.gabled_roof(pieces, Z_EAVE, D_EAVE, [], texture="keyslot", tex_kw=dict(pitch=1.7, wtab=3.0, d=0.35),
                       inner_cs=offset(base, -3.0), fascia=FASCIA, hollow=2.8)
    roof = rf["body"] + rf["tex"]
    zr = Z_EAVE + S_MAIN * (D / 2 + D_EAVE)
    corners = [(-D_EAVE, -D_EAVE), (W + D_EAVE, -D_EAVE), (W + D_EAVE, D + D_EAVE), (-D_EAVE, D + D_EAVE)]
    ends = [(D / 2, YC), (W - D / 2, YC), (W - D / 2, YC), (D / 2, YC)]
    roof = roof + G.ridge_cap((D / 2, YC), (W - D / 2, YC), zr, S_MAIN, ZW, half=1.3, up=0.7)
    roof = roof + union([G.hip_cap((c[0], c[1], Z_EAVE), (e[0], e[1], zr), half=1.3, up=0.7, drop=1.8) for c, e in zip(corners, ends)])
    roof = roof - lip_keep(base, 3.0, ZW)
    roof = roof.trim_by_plane([0, 0, 1.0], Z_EAVE - FASCIA)
    solid_env, _ = R.hip_roof(pieces, Z_EAVE, S_MAIN, D_EAVE, texture=None, zlo=ZW)
    CW = 10.0
    cx, cy = 48.0, 104.0
    zc = Z_EAVE + S_MAIN * (D + D_EAVE - cy - CW / 2 - 0.4)
    z0 = round((zc - 7.0) / 0.2) * 0.2
    roof = roof + (box([cx - CW / 2 - 1.8, cy - CW / 2 - 1.8, ZW + 0.01], [cx + CW / 2 + 1.8, cy + CW / 2 + 1.8, z0 + 0.01]) ^ solid_env)
    roof = roof - box([cx - CW / 2 - 1.0, cy - CW / 2 - 1.0, z0], [cx + CW / 2 + 1.0, cy + CW / 2 + 1.0, zr + 60])   # the block's rock faces stand 0.7 proud
    stack = CR.chimney_rockblock(CW, CW, zr + 8.0 - z0).translate([cx, cy, z0])
    DW, DDEP, DHW = 23.0, 14.0, 11.4
    dyf = 12.0
    zdf = round((Z_EAVE + S_MAIN * (dyf + D_EAVE) - 1.0) / 0.2) * 0.2
    dbody, dcore, dface = CR.dormer_hipband(DW, DDEP, DHW)
    droof = CR.dormer_hipband_roof(DW, DDEP, DHW)
    up_ = (0.0, 0.0, 1.0)
    dA = [_frame((1, 0, 0), up_, (0, -1, 0), (XC, dyf, zdf)), _frame((-1, 0, 0), up_, (0, 1, 0), (XC, D - dyf, zdf)),
          _frame((0, 1, 0), up_, (1, 0, 0), (W - dyf, YC, zdf)), _frame((0, -1, 0), up_, (-1, 0, 0), (dyf, YC, zdf))]
    for Ad in dA:
        dkeep = CR.ext(dface.offset(0.3, CR.JoinType.Miter, 4.0), -DDEP - 0.3, 0.3).transform(Ad)
        dpocket = dkeep ^ box([-500, -500, zdf], [500, 500, 999])
        seat = box([-DW / 2 - 1.3, ZW - zdf, -DDEP - 1.3], [DW / 2 + 1.3, 0.0, 1.6]).transform(Ad) ^ solid_env
        roof = roof - dpocket + (seat - dpocket - lip_keep(base, 3.0, ZW))
    kit.add("ROOF", "Charcoal", roof, group="roof")
    kit.add("CHIMNEY", "Block", stack, group="roof")
    for k, Ad in enumerate(dA):
        kit.add(f"DORMER-{k}", "Olive", dbody.transform(Ad), key="DORMER", group="roof")
        kit.add(f"DORMER-core-{k}", "Charcoal", dcore.transform(Ad), key="DORMER-core", group="roof")
        dr = droof.transform(Ad) - solid_env - dbody.transform(Ad) - roof
        kit.add(f"DORMER-roof-{k}", "Charcoal", max(dr.decompose(), key=lambda m_: m_.volume()), key="DORMER-roof", group="roof")
    # the bay's own little hip
    brf = G.gabled_roof([(BAY.pts, [0, 1, 2], S_BAY)], BAY_EAVE, D_EAVE_B, [], texture="keyslot",
                        tex_kw=dict(pitch=1.6, wtab=2.8, d=0.35), inner_cs=offset(BAY.cs, -3.0), fascia=1.4, hollow=2.2)
    main_keep = union([p.solid for p in kit.parts if p.name in ("WALLS-1", "JOINT", "WALLS-2") or p.name.startswith("CORNICE")])
    broof = (brf["body"] + brf["tex"]) - MAIN.solid(grow=0.35, dz0=-5, dz1=300) - main_keep - union(ins_keep) - lip_keep(BAY.cs, 3.0, BAY_ZW)
    broof = broof.trim_by_plane([0, 0, 1.0], BAY_ZW)
    kit.add("BAY-roof", "Charcoal", max(broof.decompose(), key=lambda m_: m_.volume()), group="roof")
    print("roofs", round(time.time() - t0, 1))

    # --- the porch across the front, under a low hip
    INSET = 2.2
    ppts = [(0.0, 0.0), (0.0, -PD), (W, -PD), (W, 0.0)]
    runs = [dict(a=(0.0, 0.0), b=(0.0, -PD), posts=[3.4, PD - INSET]),
            dict(a=(0.0, -PD), b=(W, -PD), posts=[INSET, 54.0, 110.0, W - INSET]),
            dict(a=(W, -PD), b=(W, 0.0), posts=[INSET, PD - 3.4])]
    H_floor = ZF - 1.4
    ptop = ZF + 31.0
    o = 2.4
    PP = FT.porch_turned(ppts, runs, H_floor, ptop - 5.2 - H_floor, steps_at=[(1, 36.0, 14.0)], over=o, inset=INSET,
                         rail_h=8.4, planks=dict(pitch=1.8, border=1.2), post="hollister", rail="triplets", arcade="banded",
                         skirt="blockvent", pier_tex="rockblock", roof_edge="keys", top=True)
    fkeep = slab(offset(base, 0.8 + 0.55 + 0.15), -1, ZF + 1.3)
    deck = PP["deck"] - fkeep
    kit.add("PORCH-deck", "PorchDeck", deck, P=print_flip(), group="porch", render=FT.plank_zones(deck, H_floor, "Planks", "PorchDeck"))
    keep = main_keep + union(ins_keep) + fnd
    res = FT.add_porch_top(kit, "PORCH", PP, keep, "White", "White", tin="custom", group="porch")
    zs = res["ptop"] - 0.8
    outer = [(-o, -PD - o), (W + o, -PD - o), (W + o, 3.0), (-o, 3.0)]
    pr, pr_tex = R.hip_roof([(outer, [0, 1, 3])], zs, 0.28, 0.0, texture="keyslot", tex_kw=dict(pitch=1.6, wtab=2.8, d=0.35), zlo=zs)
    proof = ((pr + pr_tex) ^ slab(poly(outer), zs, zs + 14.0)) - main_keep - union(ins_keep)
    kit.add("PORCH-roof", "Charcoal", max(proof.decompose(), key=lambda m_: m_.volume()), group="porch")
    for k, (sm, A) in enumerate(PP["steps"]):
        kit.add(f"PORCH-steps-{k}", "Block", sm.transform(A) - fkeep - deck, group="porch")
    e, u = MAIN.locate(128.0, D)
    fb = MAIN.facades()[e]
    A = fb.A.copy()
    A[:, 3] = fb.world(u, -ZF, 1.4)
    kit.add("STOOP-back", "Block", FT.steps(14.0, ZF - 0.6, 4).transform(A) - fnd, group="porch")
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "hollister")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:80]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "hollister.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))

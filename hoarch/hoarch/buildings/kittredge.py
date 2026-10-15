"""The Kittredge: an original HO-scale (1:87.1) airplane bungalow, house 56 of the fifth batch
(the Craftsman era, 1900-1930).

A broad one-storey bungalow under a low side-gabled roof of Dutch-lap shingles with deep eaves
on notched rafter tails, and rising through the middle of the roof the "cockpit": a small upper
room with ribbons of casements on every side under its own low gable. The walls are
channel-rustic siding on a tapestry-brick foundation; the gable fields are board-and-batten
with louvered vents, the rakes carried on outrigger purlins. Across the front a porch with a
low gable of its own, its roof carried on twin columns on brick piers with paired-stick
railings and a joisted beam, a lattice in its gable. Double-hung windows with a band of small
diamonds across each upper sash under dentilled caps; the door has three stepped lights over
a dentil shelf between sidelights. Winged roundels and rivets at the eaves, rising suns round
the cockpit's foot.

usage: python3 -m hoarch.buildings.kittredge [check] [export]
"""
import os
import sys
import time

import numpy as np
from manifold3d import JoinType, Manifold as M

from hoarch.core import Facade, box, cs_union, offset, poly, rect, slab, union
from hoarch import craftsman2 as CR2, cornice as CO, features as FT, gables as G, openings as O, roof as R
from hoarch.kit import Kit, print_flip
from hoarch.ornament import ext
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, stacked_shells, wall_shell

NAME = "The Kittredge"
COLORS = {"Slate": "#6F8390", "Cream": "#EDE3CC", "Rust": "#9A4A28", "Brick": "#7A3B2A", "Shingle": "#6B6259",
          "Planks": "#7A6450", "PorchDeck": "#7A6450", "Windows_Doors": "#EDE3CC"}
RENDER_MAT = {"Slate": "siding", "Cream": "trim", "Rust": "accent", "Brick": "brick", "Shingle": "roof",
              "Planks": "planks", "PorchDeck": "planks", "Windows_Doors": "trim", "Door": "door", "Glass": "glass"}

# ------------------------------------------------------------------ cornices (unique to the Kittredge)
LEDGE = 1.4
EAVE = dict(pitch=15.0, margin=4.0, layers=[
    dict(kind="frieze", h=4.4, b=1.2, orn="wingchevrons", role="Rust"),
    dict(kind="course", h=1.4, b=1.4, orn="rivets", role="Cream"),
    dict(kind="bed", h=2.4, b=1.4, P=8.0, role="Cream", brackets=dict(style="notchtail", t=1.2, reach=0.35)),
    dict(kind="crown", h=2.0, b=1.4, P=8.4, orn="bevel", role="Cream")])
BELT = dict(pitch=14.0, margin=3.6, layers=[
    dict(kind="frieze", h=4.0, b=1.2, orn="risingsun", role="Rust"),
    dict(kind="course", h=1.4, b=1.4, orn="rivets", role="Cream"),
    dict(kind="crown", h=2.0, b=1.4, P=3.4, orn="ovolo", role="Cream")])
CEAVE = dict(pitch=13.0, margin=3.4, layers=[
    dict(kind="frieze", h=3.8, b=1.2, orn="wingchevrons", role="Rust"),
    dict(kind="course", h=1.2, b=1.2, orn="rivets", role="Cream"),
    dict(kind="bed", h=2.2, b=1.2, P=6.0, role="Cream", brackets=dict(style="notchtail", t=1.1, reach=0.35)),
    dict(kind="crown", h=1.8, b=1.2, P=6.4, orn="bevel", role="Cream")])
HE = CO.band_height(EAVE)
RB = round((LEDGE + 0.4 + CO.band_height(BELT)) / 0.2) * 0.2
HCE = CO.band_height(CEAVE)

# ------------------------------------------------------------------ levels and plan
ZF = 9.0
ZE = ZF + 38.0
ZW = round((ZE + HE) / 0.2) * 0.2
FASCIA = 1.6
Z_EAVE = ZW + FASCIA
D_EAVE, RAKE, SKIN = 10.0, 10.4, 1.8
S = 0.5
W, D = 160.0, 110.0
XC, YC = W / 2, D / 2
ZR = Z_EAVE + S * (D / 2 + D_EAVE)
CX0, CX1, CY0, CY1 = 50.0, 110.0, 36.0, 76.0         # the cockpit
Z_BELT = round((ZR + 1.2) / 0.2) * 0.2
ZCU = Z_BELT + RB
ZCE = ZCU + 20.0
ZCW = round((ZCE + HCE) / 0.2) * 0.2
Z_CEAVE = ZCW + 1.6
D_EAVE_C, RAKE_C, S_C = 7.0, 7.4, 0.5
MAIN = Block("main", [(0, 0), (W, 0), (W, D), (0, D)], ZF, ZW)
COCKPIT = Block("cockpit", [(CX0, CY0), (CX1, CY0), (CX1, CY1), (CX0, CY1)], ZW, ZCW)
PX0, PX1, PD = 36.0, 124.0, 26.0                     # the porch
V1 = 8.0
VC = ZCU - ZW + 3.0


def _skin(f, b, reg):
    top = (ZE if b is MAIN else ZCE) - LEDGE - 0.6 - b.z0
    wall_top = (ZW if b is MAIN else ZCW) - b.z0
    lo = reg ^ rect(-1, -50, f.L + 1, top)
    hi = reg ^ rect(-1, wall_top + 0.2, f.L + 1, 999)
    out = CR2.siding_channel(lo) if not lo.is_empty() else M()
    if not hi.is_empty():
        out = out + CR2.boardbatten(hi)
        ap = hi.bounds()[3]
        if ap - wall_top > 14.0:
            lw, lh = (12.0, 6.0) if b is MAIN else (8.0, 4.4)
            out = out + CR2.gable_louver(lw, lh).translate([f.L / 2, ap - lh - (7.0 if b is MAIN else 5.0), 0.0])
    return out


def _openings():
    main, cock = [], []

    def add(L, blk, x, y, v0, sp, name, kind="window"):
        e, u = blk.locate(x, y)
        L.append(Opening(blk, e, u, v0, sp, name, kind))

    w2 = CR2.window_diamondtop(24.0, 22.0, n=2)
    w1 = CR2.window_diamondtop(14.0, 22.0, n=1)
    add(main, MAIN, XC, 0.0, 0.4, CR2.door_steplight(11.0, 24.0), "front-door", "door")
    for x, sp in ((18.0, w2), (58.0, w1), (102.0, w1), (142.0, w2)):
        add(main, MAIN, x, 0.0, V1, sp, f"S{x:.0f}")
    add(main, MAIN, 0.0, 30.0, V1, w2, "W30")
    add(main, MAIN, 0.0, 80.0, V1, w1, "W80")
    add(main, MAIN, W, 30.0, V1, w1, "E30")
    add(main, MAIN, W, 80.0, V1, w2, "E80")
    for x, sp in ((28.0, w2), (66.0, w1), (138.0, w1)):
        add(main, MAIN, x, D, V1, sp, f"N{x:.0f}")
    add(main, MAIN, 104.0, D, 0.4, CR2.door_halflight(9.0, 21.0), "back-door", "door")
    r3 = CR2.window_cockpit(20.0, 12.0, n=3)
    r2 = CR2.window_cockpit(14.0, 12.0, n=2)
    for x in (66.0, 94.0):
        add(cock, COCKPIT, x, CY0, VC, r3, f"C-S{x:.0f}")
        add(cock, COCKPIT, x, CY1, VC, r3, f"C-N{x:.0f}")
    add(cock, COCKPIT, CX0, (CY0 + CY1) / 2, VC, r2, "C-W")
    add(cock, COCKPIT, CX1, (CY0 + CY1) / 2, VC, r2, "C-E")
    return main, cock


OPEN_MAIN, OPEN_COCK = _openings()
OPENINGS = OPEN_MAIN + OPEN_COCK


def _purlins(rf, s, rake, n_u):
    out = []
    for wl in rf["walls"]:
        f, Lg = wl["facade"], wl["L"]
        for u in n_u(Lg):
            vtop = wl["shoulder"] + s * min(u, Lg - u) - 0.25
            out.append(f.place(CR2.purlin_end(rake - 1.4, 1.4).translate([u, vtop, 0.0])))
    return union(out)


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    base, cbase = MAIN.cs, COCKPIT.cs
    r = RAKE - D_EAVE
    pieces = [([(-r, 0.0), (W + r, 0.0), (W + r, D), (-r, D)], [0, 2], S)]
    gdefs = [dict(p0=(0.0, D), p1=(0.0, 0.0), slope=S), dict(p0=(W, 0.0), p1=(W, D), slope=S)]
    rf = G.gabled_roof(pieces, Z_EAVE, D_EAVE, gdefs, texture="dutchlap", tex_kw=dict(pitch=1.9, wtab=2.8, d=0.4),
                       skin=SKIN, rake=RAKE, inner_cs=offset(base, -3.0), fascia=FASCIA, hollow=2.8)
    gables = [(MAIN, 3, rf["walls"][0]["cs"].translate((0.0, Z_EAVE - ZF))), (MAIN, 1, rf["walls"][1]["cs"].translate((0.0, Z_EAVE - ZF)))]
    undress = [slab(offset(base, 10.0), ZE - LEDGE - 0.6, ZW + 0.01)]
    parts_ = [((CX0, CY0 + 1.5), (CX1, CY0 + 1.5), 3.0, ZF, ZW), ((CX0, CY1 - 1.5), (CX1, CY1 - 1.5), 3.0, ZF, ZW),
              ((CX0 + 1.5, CY0), (CX0 + 1.5, CY1), 3.0, ZF, ZW), ((CX1 - 1.5, CY0), (CX1 - 1.5, CY1), 3.0, ZF, ZW)]
    walls = wall_shell([MAIN], OPEN_MAIN, t=3.0, belt=None, corners="none", water_table=False, siding=_skin,
                       gables=gables, undress=undress, partitions=parts_)
    walls = walls - lip_keep(base, 3.0, ZF, 1.2)
    no_lip = union([box([-1, -1, ZW - 1], [5.0, D + 1, ZW + 5]), box([W - 5.0, -1, ZW - 1], [W + 1, D + 1, ZW + 5])])
    lip = (_corbel(base, 3.0, ZW) + lip_ring(base, 3.0, ZW)) - no_lip
    clip = _corbel(cbase, 3.0, ZW) + lip_ring(cbase, 3.0, ZW)             # the cockpit stands on its walls' lip
    walls = walls + lip + clip + CO.ledge(MAIN.pts, ZE, LEDGE) + _purlins(rf, S, RAKE, lambda L: (16.0, 34.0, L - 34.0, L - 16.0))
    kit.add("WALLS", "Slate", walls, group="walls")

    # --- the cockpit: its foot (through the roof), the belt, its storey and gables
    crc = RAKE_C - D_EAVE_C
    cpieces = [([(CX0 - crc, CY0), (CX1 + crc, CY0), (CX1 + crc, CY1), (CX0 - crc, CY1)], [0, 2], S_C)]
    cdefs = [dict(p0=(CX0, CY1), p1=(CX0, CY0), slope=S_C), dict(p0=(CX1, CY0), p1=(CX1, CY1), slope=S_C)]
    crf = G.gabled_roof(cpieces, Z_CEAVE, D_EAVE_C, cdefs, texture="dutchlap", tex_kw=dict(pitch=1.7, wtab=2.5, d=0.38),
                        skin=SKIN, rake=RAKE_C, inner_cs=offset(cbase, -3.0), fascia=1.6, hollow=2.4)
    cgables = [(COCKPIT, 3, crf["walls"][0]["cs"].translate((0.0, Z_CEAVE - ZW))), (COCKPIT, 1, crf["walls"][1]["cs"].translate((0.0, Z_CEAVE - ZW)))]
    st = stacked_shells([COCKPIT], OPEN_COCK, [Z_BELT], t=3.0, corners="none", siding=_skin, gables=cgables,
                        clear=[lip_keep(cbase, 3.0, ZW, 1.2)], prof=CO.joint_profile(RB, LEDGE), belt_blocks=None,
                        water_table=False, undress=[slab(offset(cbase, 8.0), ZCE - LEDGE - 0.6, ZCW + 0.01)])
    kit.add("COCKPIT-foot", "Slate", st["shells"][0] - lip_keep(cbase, 3.0, ZW, 1.2), group="cockpit")
    kit.add("COCKPIT-joint", "Slate", st["rings"][0], group="cockpit")
    cno_lip = union([box([CX0 - 1, CY0 - 1, ZCW - 1], [CX0 + 5.0, CY1 + 1, ZCW + 5]), box([CX1 - 5.0, CY0 - 1, ZCW - 1], [CX1 + 1, CY1 + 1, ZCW + 5])])
    clip2 = (_corbel(cbase, 3.0, ZCW) + lip_ring(cbase, 3.0, ZCW)) - cno_lip
    kit.add("COCKPIT", "Slate", st["shells"][1] + clip2 + CO.ledge(COCKPIT.pts, ZCE, LEDGE) +
            _purlins(crf, S_C, RAKE_C, lambda L: (10.0, L - 10.0)), group="cockpit")

    # --- the porch's gable roof envelope (the eave cornice stops round it)
    ptop = ZF + 30.0
    o = 2.6
    S_P = 0.42
    zs = ptop - 0.8
    outer = [(PX0 - o, -PD - o), (PX1 + o, -PD - o), (PX1 + o, 3.0), (PX0 - o, 3.0)]
    proof_env, _ = R.hip_roof([(outer, [1, 3])], zs, S_P, 0.0, texture=None, zlo=zs)
    rings, _ = CO.level(MAIN.pts, ZE, EAVE, cut=proof_env)
    CO.add_level(kit, rings, "CORNICE-E", "cornice")
    rings, _ = CO.level(st["outlines"][0], Z_BELT + LEDGE + 0.4, BELT)
    CO.add_level(kit, rings, "CORNICE-B", "cockpit")
    rings, _ = CO.level(COCKPIT.pts, ZCE, CEAVE)
    CO.add_level(kit, rings, "CORNICE-C", "cockpit")
    fnd = foundation([MAIN], 0.0, ZF, style="tapestry")
    kit.add("FOUNDATION", "Brick", fnd, group="foundation")
    ins_keep = []
    for op in OPENINGS:
        A = op.local_frame()
        sp = op.spec
        b = sp["cut"].bounds()
        key = "DOOR" if op.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, "Windows_Doors", "Door" if op.kind == "door" else "Windows_Doors", "Glass")
        part = kit.add(f"{key}-{op.name}", "Windows_Doors", world, P=P, key=f"{key}-{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}-{op.block is COCKPIT}",
                       group="inserts", render=zones)
        ins_keep.append(part.solid)
    print("walls + cornices + inserts", round(time.time() - t0, 1))

    # --- the roofs
    roof = rf["body"] + rf["tex"] + rf["skins"] + rf["skin_tex"]
    walls_env = union([wl["facade"].place(M.extrude(wl["cs"].offset(0.15), RAKE + 4.2).translate([0, 0, -3.15])) for wl in rf["walls"]])
    roof = roof + (G.ridge_cap((-RAKE, YC), (W + RAKE, YC), ZR, S, ZW) - walls_env)
    roof = roof - lip_keep(base, 3.0, ZW) - COCKPIT.solid(grow=0.9, dz0=-5.0, dz1=300.0)
    solid_env, _ = R.hip_roof(pieces, Z_EAVE, S, D_EAVE, texture=None, zlo=ZW)
    CW, CD = 11.0, 9.0
    cx, cy = 136.0, YC
    z0 = round((ZR - 6.0) / 0.2) * 0.2
    roof = roof + (box([cx - CW / 2 - 1.6, cy - CD / 2 - 1.6, ZW + 0.01], [cx + CW / 2 + 1.6, cy + CD / 2 + 1.6, z0 + 0.01]) ^ solid_env)
    roof = roof - box([cx - CW / 2 - 0.9, cy - CD / 2 - 0.9, z0], [cx + CW / 2 + 0.9, cy + CD / 2 + 0.9, ZR + 60])
    kit.add("ROOF", "Shingle", max(roof.decompose(), key=lambda m_: m_.volume()), group="roof")
    kit.add("CHIMNEY", "Brick", CR2.chimney_tapestry(CW, CD, round((ZR + 12.0 - z0) / 0.2) * 0.2).translate([cx, cy, z0]), group="roof")
    croof = crf["body"] + crf["tex"] + crf["skins"] + crf["skin_tex"]
    zrc = Z_CEAVE + S_C * ((CY1 - CY0) / 2 + D_EAVE_C)
    cwalls_env = union([wl["facade"].place(M.extrude(wl["cs"].offset(0.15), RAKE_C + 4.2).translate([0, 0, -3.15])) for wl in crf["walls"]])
    croof = croof + (G.ridge_cap((CX0 - RAKE_C, (CY0 + CY1) / 2), (CX1 + RAKE_C, (CY0 + CY1) / 2), zrc, S_C, ZCW) - cwalls_env)
    kit.add("COCKPIT-roof", "Shingle", croof - lip_keep(cbase, 3.0, ZCW), group="cockpit")
    print("roofs", round(time.time() - t0, 1))

    # --- the porch: twin columns on brick piers, its own low gable with a lattice in it
    INSET = 2.6
    ppts = [(PX0, 0.0), (PX0, -PD), (PX1, -PD), (PX1, 0.0)]
    Lp = PX1 - PX0
    H_floor = ZF - 1.4
    runs = [dict(a=(PX0, 0.0), b=(PX0, -PD), posts=[3.4, PD - INSET]),
            dict(a=(PX0, -PD), b=(PX1, -PD), posts=[INSET, Lp / 2 - 11.0, Lp / 2 + 11.0, Lp - INSET]),
            dict(a=(PX1, -PD), b=(PX1, 0.0), posts=[INSET, PD - 3.4])]
    PP = FT.porch_turned(ppts, runs, H_floor, ptop - 5.2 - H_floor, steps_at=[(1, Lp / 2, 16.0)], over=o, inset=INSET,
                         rail_h=8.6, planks=dict(pitch=1.8, border=1.2), post="kittredge", rail="pairsticks", arcade="joistbeam",
                         skirt="soldierbrick", pier_tex="tapestry", roof_edge="notchfascia", top=True)
    fkeep = slab(offset(base, 0.8 + 0.55 + 0.15), -1, ZF + 1.3)
    deck = PP["deck"] - fkeep
    kit.add("PORCH-deck", "PorchDeck", deck, P=print_flip(), group="porch", render=FT.plank_zones(deck, H_floor, "Planks", "PorchDeck"))
    bld_keep = union([p.solid for p in kit.parts if p.name == "WALLS" or p.name.startswith("CORNICE-E")])
    keep = bld_keep + union(ins_keep) + fnd
    res = FT.add_porch_top(kit, "PORCH", PP, keep, "Cream", "Cream", tin="custom", group="porch")
    zs = res["ptop"] - 0.8
    pr, pr_tex = R.hip_roof([(outer, [1, 3])], zs, S_P, 0.0, texture="dutchlap", tex_kw=dict(pitch=1.7, wtab=2.5, d=0.38), zlo=zs)
    xm = (PX0 + PX1) / 2
    zpr = zs + S_P * (Lp / 2 + o)
    proof = pr + pr_tex + G.ridge_cap((xm, -PD - o), (xm, 3.0), zpr, S_P, zs, half=1.2, up=0.7)
    fg = Facade((PX0 - o, -PD - o), (PX1 + o, -PD - o), 0.0)
    Lg = PX1 - PX0 + 2 * o
    tri = poly([(0.0, zs), (Lg, zs), (Lg / 2, zpr)])
    barge = tri - tri.offset(-2.0, JoinType.Miter, 4.0)
    inner = tri.offset(-2.0, JoinType.Miter, 4.0)
    lat = cs_union([CR2._stripes(inner, np.radians(45), 2.2, 0.55), CR2._stripes(inner, np.radians(135), 2.2, 0.55)]) ^ inner
    gface = fg.place(ext(barge, -0.01, 0.9) + ext(lat, -0.01, 0.5))
    proof = proof + gface
    proof = ((proof ^ slab(poly(outer).offset(2.0, JoinType.Miter, 4.0), zs, zpr + 5.0)) - bld_keep - union(ins_keep) - roof)
    proof = max(proof.decompose(), key=lambda m_: m_.volume())
    kit.add("PORCH-roof", "Shingle", proof, group="porch", render=[("Shingle", proof - gface), ("Cream", proof ^ gface)])
    for k, (sm, A) in enumerate(PP["steps"]):
        kit.add(f"PORCH-steps-{k}", "Brick", sm.transform(A) - fkeep - deck, group="porch")
    e, u = MAIN.locate(104.0, D)
    fb = MAIN.facades()[e]
    A = fb.A.copy()
    A[:, 3] = fb.world(u, -ZF, 1.4)
    kit.add("STOOP-back", "Brick", FT.steps(14.0, ZF - 0.6, 3).transform(A) - fnd, group="porch")
    FT.key_into(kit, "PORCH-steps-0", ["PORCH-deck"], (0, 1, 0), depth=0.8, conform=True)
    FT.key_into(kit, "STOOP-back", ["FOUNDATION"], (0, -1, 0), depth=0.8, conform=True)
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "kittredge")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:80]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "kittredge.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))

"""The Arroyo: an original HO-scale (1:87.1) California Craftsman bungalow, house 51 and the first
of the fifth batch (the Craftsman era, 1900-1930).

A storey under a low front-facing gable with deep eaves, on a clinker-brick base. Sage bungalow
siding runs up to a belt at the window heads; above it, and all over the gables, cedar shingles
in random widths, every fourth course doubled. The eaves are open: rafter tails cut with two
cloud lifts under a frieze of ginkgo leaves and a band of paired pegs, and under each rake knee
braces with pegged arms. Across the front, offset to the left, a porch under its own gable:
round battered columns on clinker-brick pedestals, a solid lap-sided porch wall, a beam with
cloud-lift corbels and rafter ends at its eave, a river-stone skirt. The door is a slab of three
tall panels under a row of four lights, between sidelights, under a cloud-lift head. Windows of
four over one, singly and in pairs, under eared head casings; louvred vents high in the gables.
On the east wall an outside chimney of river stone, battered at its foot, with a clinker-brick
top and a clay pot.

usage: python3 -m hoarch.buildings.arroyo [check] [export]
"""
import os
import sys
import time

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import Facade, box, offset, poly, rect, slab, union
from hoarch import craftsman as CR, cornice as CO, features as FT, gables as G, openings as O, roof as R
from hoarch.kit import Kit, print_flip
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, wall_shell

NAME = "The Arroyo"
COLORS = {"Sage": "#8C9A6E", "Shingle": "#6A4E36", "Cream": "#E8DFC4", "Green": "#3F5A3C", "Moss": "#56644A",
          "Clinker": "#6B3A2C", "Stone": "#A39C8E", "PorchDeck": "#7A6A55", "Windows_Doors": "#E8DFC4"}
RENDER_MAT = {"Sage": "siding", "Shingle": "shingle", "Cream": "trim", "Green": "accent", "Moss": "roof",
              "Clinker": "brick", "Stone": "stone", "PorchDeck": "planks", "Planks": "planks", "Windows_Doors": "trim",
              "Door": "door", "Glass": "glass"}

# ------------------------------------------------------------------ the eave cornice (unique to the Arroyo)
LEDGE = 1.4
EAVE = dict(pitch=7.0, margin=3.0, layers=[
    dict(kind="frieze", h=4.6, b=1.2, orn="ginkgo", role="Green"),
    dict(kind="course", h=1.4, b=1.4, orn="pegs", role="Cream"),
    dict(kind="bed", h=2.4, b=1.4, P=7.2, role="Shingle", brackets=dict(style="cloudlift", t=1.2, reach=0.3)),
    dict(kind="crown", h=1.6, b=1.4, P=7.6, orn="bevel", role="Shingle")])
HE = CO.band_height(EAVE)

# ------------------------------------------------------------------ levels and plan
ZF = 9.0
ZE = ZF + 40.0
ZW = round((ZE + HE) / 0.2) * 0.2
FASCIA = 1.4
Z_EAVE = ZW + FASCIA
D_EAVE, RAKE, SKIN = 8.0, 7.6, 1.8
S_MAIN = 0.5
W, D = 156.0, 150.0
XC, YC = W / 2, D / 2
MAIN = Block("main", [(0, 0), (W, 0), (W, D), (0, D)], ZF, ZW)
BLOCKS = [MAIN]
V1 = 7.0
BELT = 31.0                                     # the belt board, over the window heads (from ZF)
PX0, PX1, PD = 10.0, 110.0, 30.0                # the front porch
CHY = 70.0                                      # the outside chimney, on the east wall


def _chimney_zone():
    return rect(CHY - 8.6, -ZF - 1, CHY + 8.6, 999)          # east facade: u = y


def _skin(f, b, reg):
    reg = reg - rect(-1, ZE - LEDGE - 0.6 - b.z0, f.L + 1, ZW - b.z0 + 0.2)
    if f.n[0] > 0.5:
        reg = reg - _chimney_zone()
    return CR.lap_bungalow(reg, datum=0.0, belt=BELT)


def _openings():
    L = []

    def add(x, y, v0, sp, name, kind="window"):
        e, u = MAIN.locate(x, y)
        L.append(Opening(MAIN, e, u, v0, sp, name, kind))

    one = CR.window_eared41(10.0, 20.0)
    two = CR.window_eared41(19.0, 20.0, n=2)
    vent = CR.attic_vent(12.0, 7.0)
    add(60.0, 0.0, 0.4, CR.door_arroyo(10.0, 22.0), "front-door", "door")
    for x in (30.0, 90.0, 133.0):
        add(x, 0.0, V1, two, f"S{x:.0f}")
    add(40.0, D, 0.4, CR.door_arroyo(8.0, 21.0, side=2.0), "back-door", "door")
    for x, sp in ((82.0, two), (126.0, one)):
        add(x, D, V1, sp, f"N{x:.0f}")
    for y in (28.0, 112.0):
        add(W, y, V1, one, f"E{y:.0f}")
    for y, sp in ((26.0, one), (66.0, two), (112.0, one)):
        add(0.0, y, V1, sp, f"W{y:.0f}")
    vv = Z_EAVE + 12.0 - ZF
    add(XC, 0.0, vv, vent, "S-vent")
    add(XC, D, vv, vent, "N-vent")
    return L


OPENINGS = _openings()


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    base = MAIN.cs
    pieces = [(MAIN.pts, [1, 3], S_MAIN)]
    gdefs = [dict(p0=(0.0, 0.0), p1=(W, 0.0), slope=S_MAIN, e=0.3), dict(p0=(W, D), p1=(0.0, D), slope=S_MAIN, e=0.3)]
    rf = G.gabled_roof(pieces, Z_EAVE, D_EAVE, gdefs, texture="doubled", tex_kw=dict(pitch=1.8, wtab=2.4, d=0.4),
                       skin=SKIN, rake=RAKE, inner_cs=offset(base, -3.0), fascia=FASCIA, hollow=2.8)
    ws, wn = rf["walls"]
    gables = [(MAIN, 0, ws["cs"].translate((0.0, Z_EAVE - ZF))), (MAIN, 2, wn["cs"].translate((0.0, Z_EAVE - ZF)))]
    undress = [slab(offset(base, 9.0), ZE - LEDGE - 0.6, ZW + 0.01)]
    walls = wall_shell(BLOCKS, OPENINGS, t=3.0, belt=None, corners="none", water_table=False, siding=_skin,
                       gables=gables, undress=undress, partitions=[((XC, 3.0), (XC, D - 3.0), 2.0, ZF, ZW)])
    walls = walls - lip_keep(base, 3.0, ZF, 1.2)
    no_lip = union([box([-1, -1, ZW - 1], [W + 1, 5.0, ZW + 5]), box([-1, D - 5.0, ZW - 1], [W + 1, D + 1, ZW + 5])])
    lip = (_corbel(base, 3.0, ZW) + lip_ring(base, 3.0, ZW)) - no_lip
    # knee braces under both rakes, pegged, each topped just under the rake's skin
    braces = []
    for wl in rf["walls"]:
        f, Lg = wl["facade"], wl["L"]
        for u in (12.0, 42.0, Lg - 42.0, Lg - 12.0):
            vtop = wl["shoulder"] + S_MAIN * min(u, Lg - u) - 0.25
            bL = RAKE - 1.6
            br = CR.knee_brace(bL, t=1.1).translate([u, vtop - bL, 0.0])
            braces.append(f.place(br))
    walls = walls + lip + CO.ledge(MAIN.pts, ZE, LEDGE) + union(braces)
    # the outside chimney against the east wall
    chim = CR.chimney_arroyo(16.0, 8.0, Z_EAVE + 26.0, ZF + 12.0, Z_EAVE - 2.0)
    Ac = np.array([[0, 1.0, 0, W], [-1.0, 0, 0, CHY], [0, 0, 1.0, 0]])
    chim = chim.transform(Ac)
    chim_keep = box([W - 0.2, CHY - 11.2, -1.0], [W + 11.6, CHY + 11.2, 400.0])
    below = box([-50, -50, -1], [W + 50, D + 50, ZF + BELT + 1.6])
    walls = walls - box([W, CHY - 11.2, -1.0], [W + 12.0, CHY + 11.2, 400.0])
    kit.add("WALLS", "Sage", walls, group="walls", change=(round((BELT + 1.6) / 0.2) * 0.2, "Shingle"),
            render=[("Sage", walls ^ below), ("Shingle", walls - below)])
    # the porch's gable roof (for cutting the eave cornice round it)
    INSET = 2.2
    ppts = [(PX0, 0.0), (PX0, -PD), (PX1, -PD), (PX1, 0.0)]
    Lp = PX1 - PX0
    H_floor = ZF - 1.4
    ptop = ZF + 30.0
    o = 2.6
    zs = ptop - 0.8
    S_P = 0.5
    outer = [(PX0 - o, -PD - o), (PX1 + o, -PD - o), (PX1 + o, 3.0), (PX0 - o, 3.0)]
    proof_env, _ = R.hip_roof([(outer, [1, 3])], zs, S_P, 0.0, texture=None, zlo=zs)
    rings, _ = CO.level(MAIN.pts, ZE, EAVE, cut=chim_keep + proof_env.translate([0, 0, 0.0]))
    CO.add_level(kit, rings, "CORNICE-E", "cornice")
    fnd = foundation(BLOCKS, 0.0, ZF, style="clinker") - chim_keep
    kit.add("FOUNDATION", "Clinker", fnd, group="foundation")
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
    print("walls + cornice + inserts", round(time.time() - t0, 1))

    # --- the roof: random-width shingles, a ridge cap, notched round the chimney
    roof = rf["body"] + rf["tex"] + rf["skins"] + rf["skin_tex"]
    zr = Z_EAVE + S_MAIN * (W / 2 + D_EAVE)
    walls_env = union([wl["facade"].place(M.extrude(wl["cs"].offset(0.15), RAKE + 4.2).translate([0, 0, -3.15])) for wl in rf["walls"]])
    roof = roof + (G.ridge_cap((XC, -RAKE), (XC, D + RAKE), zr, S_MAIN, ZW) - walls_env)
    roof = roof - lip_keep(base, 3.0, ZW) - chim_keep
    kit.add("ROOF", "Moss", roof, group="roof")
    zb_ = round((Z_EAVE - 2.0) / 0.2) * 0.2                          # river stone below, clinker brick above
    kit.add("CHIMNEY", "Stone", chim, group="roof", change=(zb_, "Clinker"),
            render=[("Stone", chim ^ box([-1e3, -1e3, -1], [1e3, 1e3, zb_])), ("Clinker", chim - box([-1e3, -1e3, -1], [1e3, 1e3, zb_]))])
    print("roof", round(time.time() - t0, 1))

    # --- the porch: battered columns on pedestals, a lap-sided wall, its own gable roof
    runs = [dict(a=(PX0, 0.0), b=(PX0, -PD), posts=[3.2, PD - INSET]),
            dict(a=(PX0, -PD), b=(PX1, -PD), posts=[INSET, Lp / 2 - 9.5, Lp / 2 + 9.5, Lp - INSET]),
            dict(a=(PX1, -PD), b=(PX1, 0.0), posts=[INSET, PD - 3.2])]
    PP = FT.porch_turned(ppts, runs, H_floor, ptop - 5.2 - H_floor, steps_at=[(1, Lp / 2, 15.0)], over=o, inset=INSET,
                         rail_h=9.0, planks=dict(pitch=1.8, border=1.2), post="arroyo", rail="lapwall", arcade="cloudbeam",
                         skirt="riverstone", pier_tex="clinker", roof_edge="rafters", top=True)
    fkeep = slab(offset(base, 0.8 + 0.55 + 0.15), -1, ZF + 1.3)
    deck = PP["deck"] - fkeep
    kit.add("PORCH-deck", "PorchDeck", deck, P=print_flip(), group="porch", render=FT.plank_zones(deck, H_floor, "Planks", "PorchDeck"))
    bld_keep = union([p.solid for p in kit.parts if p.name == "WALLS" or p.name.startswith("CORNICE")])
    keep = bld_keep + union(ins_keep) + fnd
    res = FT.add_porch_top(kit, "PORCH", PP, keep, "Shingle", "Cream", tin="custom", group="porch")
    zs = res["ptop"] - 0.8
    pr, pr_tex = R.hip_roof([(outer, [1, 3])], zs, S_P, 0.0, texture="doubled", tex_kw=dict(pitch=1.7, wtab=2.3, d=0.4), zlo=zs)
    xm = (PX0 + PX1) / 2
    zpr = zs + S_P * (Lp / 2 + o)
    proof = pr + pr_tex + G.ridge_cap((xm, -PD - o), (xm, 3.0), zpr, S_P, zs, half=1.2, up=0.7)
    # the porch gable's face: bargeboards along the rakes and battens between
    fg = Facade((PX0 - o, -PD - o), (PX1 + o, -PD - o), 0.0)
    Lg = PX1 - PX0 + 2 * o
    tri = poly([(0.0, zs), (Lg, zs), (Lg / 2, zpr)])
    barge = tri - tri.offset(-1.8, CR.JoinType.Miter, 4.0)
    battens = CR.cs_union([rect(u - 0.3, zs, u + 0.3, zpr) for u in np.arange(Lg / 2 % 3.2 + 1.6, Lg, 3.2)]) ^ tri.offset(-2.0, CR.JoinType.Miter, 4.0)
    proof = proof + fg.place(CR.ext(barge, -0.01, 0.8) + CR.ext(battens, -0.01, 0.45))
    proof = ((proof ^ slab(poly(outer).offset(2.0, CR.JoinType.Miter, 4.0), zs, zpr + 5.0)) - bld_keep - union(ins_keep))
    kit.add("PORCH-roof", "Moss", max(proof.decompose(), key=lambda m_: m_.volume()), group="porch")
    for k, (sm, A) in enumerate(PP["steps"]):
        kit.add(f"PORCH-steps-{k}", "Clinker", sm.transform(A) - fkeep - deck, group="porch")
    e, u = MAIN.locate(40.0, D)
    fb = MAIN.facades()[e]
    A = fb.A.copy()
    A[:, 3] = fb.world(u, -ZF, 1.4)
    kit.add("STOOP-back", "Clinker", FT.steps(14.0, ZF - 0.6, 3).transform(A) - fnd, group="porch")
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "arroyo")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:80]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "arroyo.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))

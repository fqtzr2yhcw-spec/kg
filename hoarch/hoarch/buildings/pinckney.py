"""The Pinckney: an original HO-scale (1:87.1) Charleston single house, house 43 of the fourth
batch (all Colonial).

One room wide and long, its gable end to the street: a ground storey of Flemish-bond brick
tuckpointed with raised lime fillets, over it a storey of butter-yellow weatherboard beaded
at every butt between wooden quoins, on a brick foundation pierced with iron-grilled vents.
Down the west side runs the double piazza: a lower tier of Tuscan columns on Attic bases with
turned balusters, and an upper tier of slender colonnettes with palmetto capitals and a
cracked-ice railing, both under friezes sawn with crescent moons, the upper under a shed roof
of clipped slates. At the street end the lower piazza is closed by the screen wall with the
piazza door: four panels under a fanlight, Tuscan pilasters and a pediment with a palmetto.
Inside it, halfway along, the house door: a pair of three-panel leaves under an elliptical
fan, fluted pilasters and a reeded frieze. Ground-floor windows in eared (crossette)
architraves under cornices, the upper storey's in Gibbs surrounds (rusticated blocks and a
keyed flat arch), jib doors onto the upper piazza; Charleston-green louvred shutters. Between
the storeys a Charleston-green frieze of palmettos and crescent moons over a bead-and-reel
course and a torus; at the eave a frieze of paired cornucopias, dentils, a soffit on scrolled
modillions and a cyma, carried across the street gable as a pediment with a louvred
demilune. Two panelled stacks on the ridge.

usage: python3 -m hoarch.buildings.pinckney [check] [export]
"""
import os
import sys
import time

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import box, offset, poly, rect, slab, union
from hoarch import colonial4 as C4, cornice as CO, features as FT, gables as G, openings as O, roof as R
from hoarch.colonial import shutters_pair
from hoarch.kit import Kit, inv34, print_flip
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, stacked_shells

NAME = "The Pinckney"
COLORS = {"Brick": "#8E5440", "Butter": "#E8CF83", "White": "#F2F0E8", "Green": "#2A4436", "Slate": "#56606A",
          "Stone": "#A8A092", "Planks": "#6E5238", "PorchDeck": "#6E5238", "Windows_Doors": "#F2F0E8"}
RENDER_MAT = {"Brick": "brick", "Butter": "siding", "White": "trim", "Green": "accent", "Slate": "roof", "Stone": "stone",
              "Planks": "planks", "PorchDeck": "planks", "Windows_Doors": "trim", "Door": "door", "Glass": "glass"}

# ------------------------------------------------------------------ cornices (unique to the Pinckney)
LEDGE = 1.4
JOINT = dict(pitch=14.0, margin=4.0, layers=[
    dict(kind="frieze", h=4.4, b=1.2, orn="palmettos", role="Green"),
    dict(kind="course", h=1.4, b=1.4, orn="beadreel", role="White"),
    dict(kind="crown", h=2.2, b=1.4, P=3.4, orn="torus", role="White")])
EAVE = dict(pitch=13.0, margin=4.0, layers=[
    dict(kind="frieze", h=5.6, b=1.2, orn="cornucopias", role="Green"),
    dict(kind="course", h=1.6, b=1.4, orn="dentil", role="White", tooth=0.8, gap=0.6),
    dict(kind="bed", h=2.0, b=1.4, P=5.4, role="White", brackets=dict(style="scrollmod", t=1.4, reach=0.3)),
    dict(kind="crown", h=2.8, b=1.4, P=6.4, orn="cyma", role="White")])
RJ = round((LEDGE + 0.4 + CO.band_height(JOINT)) / 0.2) * 0.2
HE = CO.band_height(EAVE)

# ------------------------------------------------------------------ levels (on the 0.2 mm grid)
ZF = 8.0
S1 = ZF + 42.0
ZU = S1 + RJ                                    # the upper floor = the upper piazza's floor
ZE = ZU + 40.0
ZW = round((ZE + HE) / 0.2) * 0.2
FASCIA = 1.6
Z_EAVE = ZW + FASCIA
D_EAVE, RAKE, SKIN = 6.4, 6.6, 1.8
S_MAIN = 0.85
S_PIAZ = 0.25
V1 = 7.0
V2 = ZU - ZF + 5.0
VJ = ZU - ZF + 0.8                              # the jib doors' sills bear on the joint cornice

# ------------------------------------------------------------------ plan (x east, y north; the street is to the south)
W, D = 78.0, 172.0
XC = W / 2
PD, YP = 22.0, 146.0                            # the piazza: its depth (west of the house) and length
INSET = 1.6
TOP_DZ = 5.2                                    # a porch top's flat stands this far above its posts' height
MAIN = Block("main", [(0, 0), (W, 0), (W, D), (0, D)], ZF, ZW)
BLOCKS = [MAIN]
Y_BAYS = (24.0, 56.0, 88.0, 120.0, 152.0)


def _skin(f, b, reg):
    """Tuckpointed brick below the joint, quoined weatherboard above; nothing in the eave band."""
    reg = reg - rect(-1, ZE - LEDGE - 0.6 - b.z0, f.L + 1, ZW - b.z0 + 0.2)
    lo = reg ^ rect(-1, -10, f.L + 1, S1 - b.z0)
    hi = reg ^ rect(-1, S1 - b.z0, f.L + 1, 999)
    out = []
    if not lo.is_empty():
        out.append(C4.brick_tuckpointed(lo))
    if not hi.is_empty():
        out.append(C4.weatherboard_quoined(hi, f.L, datum=S1 - b.z0, qtop=ZE - LEDGE - 0.6 - b.z0))
    return union(out) if out else M()


def _openings():
    L, SH = [], []

    def add(x, y, v0, sp, name, kind="window", shut=False):
        e, u = MAIN.locate(x, y)
        L.append(Opening(MAIN, e, u, v0, sp, name, kind))
        if shut:
            SH.append(name)

    lo = C4.window_crossette(10.0, 24.0)
    up = C4.window_gibbs(10.0, 22.0)
    jib = C4.window_gibbs(10.0, 23.0, jib=True)
    fan = C4.window_louvrefan(14.0)
    for x in (21.0, W - 21.0):                                          # the street front
        add(x, 0.0, V1, lo, f"S{x:.0f}-1", shut=True)
        add(x, 0.0, V2, up, f"S{x:.0f}-2", shut=True)
    add(XC, 0.0, ZW - ZF + 4.0, fan, "S-gable")
    for y in Y_BAYS:                                                    # the east side
        add(W, y, V1, lo, f"E{y:.0f}-1", shut=True)
        add(W, y, V2, up, f"E{y:.0f}-2", shut=True)
    for y in Y_BAYS:                                                    # the piazza side
        if y > YP:                                                      # past the piazza, clear of its roof
            add(0.0, y + 6.0, V1, lo, f"W{y + 6.0:.0f}-1")
            add(0.0, y + 6.0, V2, up, f"W{y + 6.0:.0f}-2")
            continue
        if y == 88.0:
            add(0.0, y, 0.4, C4.door_charleston(11.0, 24.0), "house-door", "door")
        else:
            add(0.0, y, V1, lo, f"W{y:.0f}-1")
        add(0.0, y, VJ, jib, f"W{y:.0f}-jib", "door")
    add(20.0, D, V1, lo, f"N20-1", shut=True)                           # the back
    add(W - 22.0, D, 0.4, C4.door_charleston(10.0, 22.0, back=True), "back-door", "door")
    for x in (20.0, W - 20.0):
        add(x, D, V2, up, f"N{x:.0f}-2", shut=True)
    add(XC, D, ZW - ZF + 4.0, fan, "N-gable")
    return L, SH


OPENINGS, SHUTTERED = _openings()


def _piazza_runs():
    pts = [(0.0, YP), (-PD, YP), (-PD, 0.0), (0.0, 0.0)]
    side = [INSET + (YP - 2 * INSET) * k / 5 for k in range(6)]
    runs = [dict(a=(0.0, YP), b=(-PD, YP), posts=[3.0, PD - INSET]),
            dict(a=(-PD, YP), b=(-PD, 0.0), posts=side),
            dict(a=(-PD, 0.0), b=(0.0, 0.0), posts=[INSET])]           # the screen wall closes the street end below
    runs2 = [dict(r) for r in runs[:2]] + [dict(a=(-PD, 0.0), b=(0.0, 0.0), posts=[INSET, PD - 3.0])]
    return pts, runs, runs2


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    base = MAIN.cs
    pieces = [(MAIN.pts, [1, 3], S_MAIN)]
    gdefs = [dict(p0=(0.0, 0.0), p1=(W, 0.0), slope=S_MAIN, e=0.3), dict(p0=(W, D), p1=(0.0, D), slope=S_MAIN, e=0.3)]
    rf = G.gabled_roof(pieces, Z_EAVE, D_EAVE, gdefs, texture=["clipped", "square"], tex_kw=dict(pitch=1.6, wtab=2.2, d=0.4),
                       skin=SKIN, rake=RAKE, inner_cs=offset(base, -3.0), fascia=FASCIA, hollow=2.8)
    ws, wn = rf["walls"]
    gables = [(MAIN, 0, ws["cs"].translate((0.0, Z_EAVE - ZF))), (MAIN, 2, wn["cs"].translate((0.0, Z_EAVE - ZF)))]
    undress = [slab(offset(base, 8.0), ZE - LEDGE - 0.6, ZW + 0.01)]
    clear = [lip_keep(base, 3.0, ZF, 1.2)]
    st = stacked_shells(BLOCKS, OPENINGS, [S1], t=3.0, corners="none", siding=_skin, gables=gables, clear=clear,
                        prof=CO.joint_profile(RJ, LEDGE), belt_blocks=None, water_table=False, undress=undress,
                        partitions=[((3.0, 70.0), (W - 3.0, 70.0), 2.0, ZF, ZW)])
    kit.add("WALLS-1", "Brick", st["shells"][0], group="walls")
    kit.add("JOINT", "Brick", st["rings"][0], group="walls")
    no_lip = union([box([-1, -1, ZW - 1], [W + 1, 5.0, ZW + 5]), box([-1, D - 5.0, ZW - 1], [W + 1, D + 1, ZW + 5])])
    lip = (_corbel(base, 3.0, ZW) + lip_ring(base, 3.0, ZW)) - no_lip
    walls2 = kit.add("WALLS-2", "Butter", st["shells"][1] + lip + CO.ledge(MAIN.pts, ZE, LEDGE), group="walls")
    rings, _ = CO.level(st["outlines"][0], S1 + LEDGE + 0.4, JOINT)
    CO.add_level(kit, rings, "CORNICE-J", "cornice")
    rings, _ = CO.level(MAIN.pts, ZE, EAVE)
    CO.add_level(kit, rings, "CORNICE-E", "cornice")
    fnd = foundation(BLOCKS, 0.0, ZF, style="ventgrille")
    kit.add("FOUNDATION", "Brick", fnd, group="foundation")

    # windows, doors and shutters
    ins_keep, shut = [], []
    for o in OPENINGS:
        A = o.local_frame()
        sp = o.spec
        b = sp["cut"].bounds()
        key = "DOOR" if o.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, "Windows_Doors", "Door" if o.kind == "door" else "Windows_Doors", "Glass")
        part = kit.add(f"{key}-{o.name}", "Windows_Doors", world, P=P,
                       key=f"{key}-{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}-{o.v0 > 20}", group="inserts", render=zones)
        ins_keep.append(part.solid)
        if o.name in SHUTTERED:
            w_op, h_op = b[2] - b[0], b[3] - b[1]
            cas = 2.9 if o.v0 > 20 else 2.2                         # clear of the Gibbs blocks / the crossettes
            left, right = shutters_pair(w_op, h_op, casing=cas, gap=0.4, make=C4.shutter_charleston)
            for s_, m in (("L", left), ("R", right)):
                sp_ = kit.add(f"SHUTTER-{o.name}-{s_}", "Green", m.translate([0, 0, 0.5]).transform(A),
                              P=inv34(A), key=f"SHUTTER-{h_op:.1f}", group="shutters")
                shut.append(sp_.solid)
    print("walls + cornices + inserts", round(time.time() - t0, 1))

    # --- the double piazza
    pts, runs, runs2 = _piazza_runs()
    bld_keep = union([p.solid for p in kit.parts if p.name in ("WALLS-1", "JOINT", "WALLS-2") or p.name.startswith("CORNICE")])
    keep = bld_keep + union(ins_keep) + fnd
    H1 = ZF - 1.4
    ud = (INSET + PD) / 2
    P1 = FT.porch_turned(pts, runs, H1, ZU - TOP_DZ - H1, steps_at=[(2, ud, 12.0)], over=2.4, inset=INSET, rail_h=8.6,
                         post="attic", rail="charleston", arcade="crescent", skirt="diamondgrille", pier_tex="tuckflemish",
                         roof_edge="reeded", planks=dict(pitch=1.8, border=1.4), top=True)
    fkeep = slab(offset(base, 0.8 + 0.55 + 0.15), -1, ZF + 1.3)
    deck = P1["deck"] - fkeep
    kit.add("PIAZZA-deck", "PorchDeck", deck, P=print_flip(), group="piazza",
            render=FT.plank_zones(deck, H1, "Planks", "PorchDeck"))
    where = []
    for r in runs2:
        f = FT.Facade(r["a"], r["b"], 0.0)
        for u in r["posts"]:
            p = f.p0 + f.u * u - f.n * INSET
            if not any(np.allclose(p, q, atol=0.05) for q in where):
                where.append(p)
    # the lower tier's top is the upper tier's floor: its flat is laid with planks (the part's
    # first colour, printed upside down) and socketed for the upper colonnettes' pegs
    top1 = P1["top"] - keep
    ptop1 = top1.bounding_box()[5]
    planks = FT.porch_planks(pts, [0, 1, 2], H=ptop1, t=1.2, pitch=1.8, crack=0.25, border=1.4, along=(1.0, 0.0))
    planks = planks + slab(poly(pts), ptop1 - 1.2, ptop1 - 0.6)           # the cracks stop in the plank colour
    top1 = (top1 - slab(poly(pts), ptop1 - 1.2, ptop1 + 1.0)) + (planks - keep)
    socks = union([box([p[0] - 1.0, p[1] - 1.0, ptop1 - 2.0], [p[0] + 1.0, p[1] + 1.0, ptop1 + 1.0]) for p in where])
    top1 = top1 - socks
    sheet = top1 ^ box([-1e3, -1e3, ptop1 - 1.2], [1e3, 1e3, 1e3])
    kit.add("PIAZZA-top-1", "Planks", top1, P=print_flip(), change=(1.2, "White"), group="piazza",
            render=[("Planks", sheet), ("White", top1 - sheet)])
    for k, (sm, A) in enumerate(P1["steps"]):
        kit.add(f"PIAZZA-steps-{k}", "Stone", sm.transform(A) - fkeep - deck, group="piazza")
    # the upper tier, under a shed roof that meets the wall under the eave cornice
    o = 2.4
    zs = ZE - 0.6 - S_PIAZ * (PD + o)
    P2 = FT.porch_turned(pts, runs2, ptop1, zs + 0.8 - TOP_DZ - ptop1, over=2.4, inset=INSET, rail_h=8.6, post="palmetto",
                         rail="ice", arcade="crescent", skirt="diamondgrille", pier_tex="tuckflemish", roof_edge="reeded",
                         top=True)
    res = FT.add_porch_top(kit, "PIAZZA-2", P2, keep, "White", "White", tin="custom", group="piazza")
    zs = res["ptop"] - 0.8
    outer = [(-PD - o, -o), (3.0, -o), (3.0, YP + o), (-PD - o, YP + o)]
    sk, sk_tex = R.hip_roof([(outer, [0, 2, 3])], zs, S_PIAZ, 0.0, texture=["clipped", "square"],
                            tex_kw=dict(pitch=1.5, wtab=2.0, d=0.38), zlo=zs)
    skirt = ((sk + sk_tex) ^ slab(poly(outer), zs, zs + S_PIAZ * (PD + o + 3.0) + 0.6)) - bld_keep - union(ins_keep)
    kit.add("PIAZZA-roof", "Slate", max(skirt.decompose(), key=lambda m_: m_.volume()), group="piazza")
    # the screen wall across the street end of the lower piazza, with the piazza door
    xa, xb = -PD + INSET + 1.7, 0.6
    y0, y1 = 1.8, 3.4                               # set back so the pilaster bases clear the steps
    scr = box([xa, y0, H1], [xb, y1, ptop1])
    sp = C4.door_screen(9.0, 20.0)
    xd = (xa + 0.0) / 2
    A = np.array([[1.0, 0, 0, xd], [0, 0, -1.0, y0], [0, 1.0, 0, H1]])
    grooves = union([box([xa - 1, y0 - 0.1, z - 0.2], [xb + 1, y0 + 0.3, z + 0.2]) for z in np.arange(H1 + 3.6, ptop1, 2.0)])
    land = M.extrude(sp["landing"], 3.0).translate([0, 0, -0.5]).transform(A)
    scr = scr - (grooves - land) + (box([xa, y0 - 0.5, H1], [xb, y1 + 0.5, H1 + 1.6]) - land)
    scr = scr - M.extrude(sp["cut"], 8.0).translate([0, 0, -4.0]).transform(A)
    scr = scr - bld_keep - fnd
    for pt_ in kit.parts:
        if pt_.name in ("PIAZZA-top-1", "PIAZZA-deck"):
            scr = scr - pt_.solid
    kit.add("PIAZZA-screen", "Butter", max(scr.decompose(), key=lambda m_: m_.volume()), group="piazza")
    world, P, zones = O.place(sp, A, "Windows_Doors", "Door", "Glass")
    kit.add("DOOR-piazza", "Windows_Doors", world, P=P, group="inserts", render=zones)
    print("piazza", round(time.time() - t0, 1))

    # --- the roof: clipped and square slates, a ridge cap, two panelled stacks on the ridge
    roof = rf["body"] + rf["tex"] + rf["skins"] + rf["skin_tex"]
    zr = Z_EAVE + S_MAIN * (W / 2 + D_EAVE)
    walls_env = union([wl["facade"].place(M.extrude(wl["cs"].offset(0.15), RAKE + 4.2).translate([0, 0, -3.15])) for wl in rf["walls"]])
    roof = roof + (G.ridge_cap((XC, -RAKE), (XC, D + RAKE), zr, S_MAIN, ZW) - walls_env)
    roof = roof - lip_keep(base, 3.0, ZW)
    solid_env, _ = R.hip_roof(pieces, Z_EAVE, S_MAIN, D_EAVE, texture=None, zlo=ZW)
    CW, CD = 8.0, 12.0
    pockets, stacks = [], []
    for cy in (58.0, 122.0):
        z0 = round((zr - 8.0) / 0.2) * 0.2
        roof = roof + (box([XC - CW / 2 - 1.2, cy - CD / 2 - 1.2, ZW + 0.01], [XC + CW / 2 + 1.2, cy + CD / 2 + 1.2, z0 + 0.01]) ^ solid_env)
        pockets.append(box([XC - CW / 2 - 0.4, cy - CD / 2 - 0.4, z0], [XC + CW / 2 + 0.4, cy + CD / 2 + 0.4, zr + 40]))
        stacks.append(C4.chimney_panelled(CW, CD, zr + 14.0 - z0).translate([XC, cy, z0]))
    roof = roof - union(pockets)
    kit.add("ROOF", "Slate", roof, group="roof")
    for k, s_ in enumerate(stacks):
        kit.add(f"CHIMNEY-{k}", "Stone", s_, key="CHIMNEY", group="roof")
    print("roof", round(time.time() - t0, 1))

    # --- the back stoop
    e, u = MAIN.locate(W - 22.0, D)
    fb = MAIN.facades()[e]
    A = fb.A.copy()
    A[:, 3] = fb.world(u, -ZF, 1.4)
    kit.add("STOOP-back", "Stone", FT.steps(16.0, ZF - 0.6, 3).transform(A) - fnd, group="steps")
    # glue joints: the piazza steps fitted to the deck's edge (see NOTES.md)
    FT.key_into(kit, "PIAZZA-steps-0", ["PIAZZA-deck"], (0, 1, 0), depth=0.8, conform=True)
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "pinckney")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:80]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "pinckney.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))

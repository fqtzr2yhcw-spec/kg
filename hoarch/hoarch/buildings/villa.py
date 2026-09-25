"""The Ashby — an original HO-scale (1:87.1) Italianate villa, first building of the lineup.
Rev C: the house-size plan (180 x 156 mm, storeys of 42 and 38 mm), framed windows spaced along
the walls, and built-up cornices at every level.

Two-storey square block of cream common-bond brick with stone quoins and a canted bay. Between
the storeys a three-part cornice: a green frieze of sunk-margin coffers with diamond bosses, a
white egg-and-dart course and a white torus crown. At the eave a four-part cornice: a green
frieze carrying a running vine (rinceau), a white dentil course, a white soffit on paired
Italianate scroll brackets and a green cyma crown. A low hipped standing-seam roof with a flat
top carries a V-groove cupola with twin arched lights under its own cornice (a white frieze of
round eyes under keystones, a green soffit on paired scrolls, a white ovolo crown) and an acorn
finial. A full-width porch (chamfered posts, vase balusters, scroll frieze, panelled skirt, a
planked floor and a standing-seam roof), a one-storey kitchen ell behind with its own cornice
(a green frieze of pearls, a white billet course, a white cavetto crown) and a low hip, panel
shutters, stucco chimneys and a smooth limestone foundation.

usage: python3 -m hoarch.buildings.villa [check] [export] [views]
"""
import os
import sys
import time

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import box, compose, inv34, offset, poly, rect, slab, union
from hoarch import cornice as CO, features as FT, openings as O, roof as R, skins as SK, trimwork as TW
from hoarch.kit import Kit, print_flip
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, stacked_shells, wall_shell

NAME = "Ashby Italianate Villa"
COLORS = {"PorchDeck": "#F2F0EB", "Planks": "#6F5034",       # the planked porch deck: two colours, one change
          "Sand": "#D8C49A", "White": "#F2F0EB", "Charcoal": "#3E4247", "Stone": "#8C8A85",
          "Forest": "#2F4A3A", "Brick": "#8A3B2B", "Windows_Doors": "#F2F0EB"}
# windows and doors are one part each (plug with glass and sash, and the surround), all on
# their own plate: it is the one plate printed with supports (under the surrounds)
RENDER_MAT = {"PorchDeck": "trim", "Planks": "planks",
              "Sand": "siding", "White": "trim", "Charcoal": "roof", "Stone": "stone", "Forest": "accent",
              "Brick": "brick", "Windows_Doors": "trim", "Door": "door", "Glass": "glass"}
PALETTE = {"siding": ["#D8C49A", 0.6, 0.0], "trim": ["#EEECE7", 0.55, 0.0], "roof": ["#3E4247", 0.5, 0.0],
           "stone": ["#8C8A85", 0.85, 0.0], "accent": ["#2F4A3A", 0.5, 0.0], "brick": ["#8A3B2B", 0.85, 0.0]}

# ------------------------------------------------------------------ cornices (unique to the Ashby)
LEDGE = 1.4
JOINT = dict(pitch=13.0, margin=4.4, layers=[
    dict(kind="frieze", h=4.6, b=1.2, orn="coffers", role="Forest"),
    dict(kind="course", h=1.6, b=1.4, orn="eggdart", role="White"),
    dict(kind="crown", h=2.2, b=1.4, P=3.6, orn="torus", role="White")])
EAVE = dict(pitch=13.0, margin=4.4, pair=2.2, layers=[
    dict(kind="frieze", h=6.0, b=1.2, orn="rinceau", role="Forest"),
    dict(kind="course", h=1.6, b=1.4, orn="dentil", role="White", tooth=0.9, gap=0.6),
    dict(kind="bed", h=2.2, b=1.4, P=6.6, role="White", brackets=dict(style="scroll", t=0.9, reach=0.6)),
    dict(kind="crown", h=3.0, b=1.4, P=7.4, orn="cyma", role="Forest")])
ELL_C = dict(pitch=11.0, margin=3.6, layers=[
    dict(kind="frieze", h=4.2, b=1.2, orn="pearls", role="Forest"),
    dict(kind="course", h=1.4, b=1.4, orn="billet", role="White"),
    dict(kind="crown", h=2.0, b=1.4, P=4.0, orn="cavetto", role="White")])
CUPOLA_C = dict(pitch=9.0, margin=3.0, pair=1.6, layers=[
    dict(kind="frieze", h=4.2, b=1.2, orn="oculi", role="White"),
    dict(kind="bed", h=1.8, b=1.4, P=4.8, role="Forest", brackets=dict(style="scroll", t=0.8, reach=0.7)),
    dict(kind="crown", h=2.2, b=1.4, P=5.6, orn="ovolo", role="White")])
RJ = round((LEDGE + 0.4 + CO.band_height(JOINT)) / 0.2) * 0.2      # the joint (belt ring) height
HE = CO.band_height(EAVE)

# ------------------------------------------------------------------ levels (on the 0.2 mm grid)
ZF = 14.0                         # foundation / first floor
S1 = ZF + 42.0                    # first-storey shell top = the joint ring's foot
ZE = S1 + RJ + 38.0               # the eave ledge's top
ZW = ZE + HE                      # the wall top behind the eave cornice; the roof sits here
FASCIA = 1.8
Z_EAVE = ZW + FASCIA
ROOF_SLOPE = 0.5
D_EAVE = 7.8                      # covers the crown (7.4)
V1 = 8.0
V2 = S1 + RJ + 5.0 - ZF
ELL_ZE = ZF + 32.0                # the ell's ledge
ELL_ZW = ELL_ZE + CO.band_height(ELL_C)

# ------------------------------------------------------------------ massing (mm, plan x east / y north, front = south)
W, D = 180.0, 156.0
BAY_Y = (48.0, 108.0)             # the canted bay on the east, 14 deep
MAIN = Block("main", [(0, 0), (W, 0), (W, BAY_Y[0]), (W + 14, BAY_Y[0] + 14), (W + 14, BAY_Y[1] - 14), (W, BAY_Y[1]),
                      (W, D), (0, D)], ZF, ZW)
ELL = Block("ell", [(104, D), (168, D), (168, D + 50), (104, D + 50)], ZF, ELL_ZW)
BLOCKS = [MAIN, ELL]
CUP_SIZE, CUP_H = 44.0, 28.0
CUP_C = (90.0, 78.0)
DOOR_X = 90.0


# ------------------------------------------------------------------ openings
def _openings():
    L = []
    s22 = dict(lites=(2, 2), rows=(2, 2), casing=1.3)       # four-over-four sash
    lo = O.window_insert(9.6, 24.0, rise=0, style="flat", apron=True, **s22)
    up = O.window_insert(9.6, 21.0, rise=None, style="key", **s22)
    bay_lo = O.window_insert(9.0, 24.0, rise=0, style="flat", ends=0.2, sill_ext=0.3, clip=True, apron=True,
                             lites=(2, 2), rows=(2, 2), casing=0.9)
    bay_up = O.window_insert(9.0, 21.0, rise=None, style="key", ends=0.2, sill_ext=0.3, clip=True,
                             lites=(2, 2), rows=(2, 2), casing=0.9)
    ell_w = O.window_insert(8.4, 19.0, rise=0, style="flat", apron=True, **s22)
    twin = O.twin_arch_window(16.0, 22.0, balcony=0)
    front = O.door_insert(17.0, 32.0, leaves=2, transom=5.4)
    back = O.door_insert(11.0, 24.6, leaves=1, glass_top=True)

    def add(block, x, y, v0, sp, name, kind="window", shutters=False):
        e, u = block.locate(x, y)
        L.append((Opening(block, e, u, v0, sp, name, kind), shutters))

    # front (south)
    for x in (26.0, 58.0, 122.0, 154.0):
        add(MAIN, x, 0, V1, lo, f"S{x:.0f}-1", shutters=True)
        add(MAIN, x, 0, V2, up, f"S{x:.0f}-2", shutters=True)
    add(MAIN, DOOR_X, 0, 0.4, front, "front-door", "door")
    add(MAIN, DOOR_X, 0, V2, twin, "S90-2")
    # east, with the canted bay
    for y in (22.0, 134.0):
        add(MAIN, W, y, V1, lo, f"E{y:.0f}-1", shutters=True)
        add(MAIN, W, y, V2, up, f"E{y:.0f}-2", shutters=True)
    ym = (BAY_Y[0] + BAY_Y[1]) / 2
    for (x, y, nm) in ((W + 14, ym, "front"), (W + 7, BAY_Y[0] + 7, "c1"), (W + 7, BAY_Y[1] - 7, "c2")):
        add(MAIN, x, y, V1, bay_lo, f"bay-{nm}-1")
        add(MAIN, x, y, V2, bay_up, f"bay-{nm}-2")
    # west
    for y in (36.0, 78.0, 120.0):
        add(MAIN, 0, y, V1, lo, f"W{y:.0f}-1", shutters=True)
        add(MAIN, 0, y, V2, up, f"W{y:.0f}-2", shutters=True)
    # rear (north) of the main block, clear of the ell and its roof
    for x in (26.0, 58.0):
        add(MAIN, x, D, V1, lo, f"N{x:.0f}-1", shutters=True)
        add(MAIN, x, D, V2, up, f"N{x:.0f}-2", shutters=True)
    # kitchen ell
    add(ELL, 168, 181.0, 7.0, ell_w, "ellE181", shutters=True)
    add(ELL, 104, 186.0, 7.0, ell_w, "ellW186", shutters=True)
    add(ELL, 122.0, D + 50, 7.0, ell_w, "ellN122", shutters=True)
    add(ELL, 150.0, D + 50, 0.4, back, "back-door", "door")
    return L


OPENINGS_S = _openings()
OPENINGS = [o for o, _ in OPENINGS_S]


def _brick(f, b, reg):
    """Cream common-bond brick: five stretcher courses to every header course. Nothing in the
    cornice bands (the joint's is the belt ring; the eave's and the ell's are cut out here)."""
    top = (ELL_ZE if b is ELL else ZE) - b.z0
    return SK.brick_bond(reg - rect(-1, top, f.L + 1, 999), "common", datum=1.8)


# ------------------------------------------------------------------ build
def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    # one shell per storey; the joint ring carries the storey cornice's band
    clear = [lip_keep(poly(MAIN.pts) + poly(ELL.pts), 3.0, ZF, 1.2),                 # foundation lip
             lip_keep(poly(MAIN.pts), 3.0, ZW - 1.6, 1.6, inner=0.15, reach=1.2)]    # eave lip
    undress = [slab(offset(MAIN.cs, 8.0), ZE - LEDGE - 0.6, ZW + 0.01),
               slab(offset(ELL.cs, 8.0) - offset(MAIN.cs, 2.0), ELL_ZE - LEDGE - 0.6, ELL_ZW + 0.01)]
    st = stacked_shells(BLOCKS, OPENINGS, [S1], t=3.0, corners="quoin", clear=clear, siding=_brick,
                        prof=CO.joint_profile(RJ, LEDGE), belt_blocks=None, water_table=False, undress=undress,
                        partitions=[((DOOR_X, 3.0), (DOOR_X, D - 3.0), 2.0, ZF, ZW)])
    main_keep = MAIN.solid(grow=0.8, dz0=-2, dz1=400)
    ell_ledge = CO.ledge(ELL.pts, ELL_ZE, LEDGE) - main_keep
    ell_lip = (_corbel(ELL.cs, 3.0, ELL_ZW) + lip_ring(ELL.cs, 3.0, ELL_ZW)) - MAIN.solid(grow=0.2, dz0=-2, dz1=400)
    kit.add("WALLS-1", "Sand", st["shells"][0] + ell_ledge + ell_lip, group="walls")
    kit.add("JOINT", "Sand", st["rings"][0], group="walls")
    lip = _corbel(MAIN.cs, 3.0, ZW) + lip_ring(MAIN.cs, 3.0, ZW)
    kit.add("WALLS-2", "Sand", st["shells"][1] + lip + CO.ledge(MAIN.pts, ZE, LEDGE), group="walls")
    kit.add("FOUNDATION", "Stone", foundation(BLOCKS, 0.0, ZF, style="limestone"), group="foundation")

    # the kitchen ell's low hip (under the joint cornice, which is cut back to it)
    ell_d = ELL_C["layers"][-1]["P"] + 0.6
    ell_ze = ELL_ZW + 1.4
    eroof, etex = R.hip_roof([(ELL.pts, [1, 2, 3])], ell_ze, ROOF_SLOPE, ell_d, texture="seam", zlo=ELL_ZW)
    ell_env, _ = R.hip_roof([(ELL.pts, [1, 2, 3])], ell_ze + 0.5, ROOF_SLOPE, ell_d + 0.5, texture=None,
                            zlo=ELL_ZW - 1.0)
    joint_keep = slab(offset(MAIN.cs, 2.0), S1 - 2.2, S1 + RJ + 0.2)        # the joint band and its ledge
    kit.add("ROOF-ell", "Charcoal", (eroof + etex) - MAIN.solid(grow=0.8, dz0=-2, dz1=400) - joint_keep
            - lip_keep(ELL.cs, 3.0, ELL_ZW), group="roof")

    # the cornices: at the joint (cut back to the ell's roof), at the eave, round the ell
    rings, _ = CO.level(st["outlines"][0], S1 + LEDGE + 0.4, JOINT, cut=ell_env)
    CO.add_level(kit, rings, "CORNICE-J", "cornice")
    rings, _ = CO.level(MAIN.pts, ZE, EAVE)
    CO.add_level(kit, rings, "CORNICE-E", "cornice")
    rings, _ = CO.level(ELL.pts, ELL_ZE, ELL_C, cut=main_keep)
    CO.add_level(kit, rings, "CORNICE-ELL", "cornice")

    # inserts and shutters
    inserts = []
    for o, sh in OPENINGS_S:
        A = o.local_frame()
        sp = o.spec
        tag = f"{sp['cut'].bounds()[2] - sp['cut'].bounds()[0]:.1f}x{sp['cut'].bounds()[3] - sp['cut'].bounds()[1]:.1f}"
        key = "DOOR" if o.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, "Windows_Doors", "Door" if o.kind == "door" else "Windows_Doors", "Glass")
        inserts.append(kit.add(f"{key}-{o.name}", "Windows_Doors", world, P=P,
                               key=f"{key}-{tag}-{o.v0 > 20}", group="inserts", render=zones))
        if sh:
            w_op = sp["cut"].bounds()[2] - sp["cut"].bounds()[0]
            h_op = sp["cut"].bounds()[3] - sp["cut"].bounds()[1]
            arched = abs(sp["top"] - h_op) > 3.0 and o.v0 > 20
            hh = (h_op - w_op / 2 - 1.8) if arched else h_op
            left, right = FT.shutters_for(w_op, h_op, casing=1.3, h=hh, style="panel")
            for side, m in (("L", left), ("R", right)):
                ms = m.translate([0, 0, 0.32]).transform(A)
                kit.add(f"SHUTTER-{o.name}-{side}", "Forest", ms, P=inv34(A), key=f"SHUTTER-{hh:.1f}",
                        group="shutters")
    print("walls + cornices + inserts", round(time.time() - t0, 1))

    # --- the main roof: a low standing-seam hip with a flat top for the cupola
    rect_p = [(0, 0), (W, 0), (W, D), (0, D)]
    bay_p = [(W - 14, BAY_Y[0]), (W, BAY_Y[0]), (W + 14, BAY_Y[0] + 14), (W + 14, BAY_Y[1] - 14), (W, BAY_Y[1]),
             (W - 14, BAY_Y[1])]
    i_top = 56.4                          # the flat deck 28.2 over the eave: a layer line
    flat = Z_EAVE + ROOF_SLOPE * i_top
    roof, tex = R.hip_roof([(rect_p, [0, 1, 2, 3]), (bay_p, [1, 2, 3])], Z_EAVE, ROOF_SLOPE, D_EAVE,
                           texture="seam", flat_top=flat, zlo=ZW)
    CW = 12.0
    chims = [(30.0, 78.0), (150.0, 78.0)]

    def chim_z0(x, y):   # 3 mm below the lowest roof point under the chimney
        i = min(x + D_EAVE, W + D_EAVE - x, y + D_EAVE, D + D_EAVE - y) - CW / 2
        return round((Z_EAVE + ROOF_SLOPE * i - 3.0) / 0.2) * 0.2

    pockets = union([box([x - CW / 2 - 0.4, y - CW / 2 - 0.4, chim_z0(x, y)], [x + CW / 2 + 0.4, y + CW / 2 + 0.4, flat + 20])
                     for x, y in chims])
    kit.add("ROOF-main", "Charcoal", (roof + tex) - pockets - lip_keep(MAIN.cs, 3.0, ZW), group="roof")
    for k, (x, y) in enumerate(chims):
        z0 = chim_z0(x, y)
        ch = TW.chimney("stucco", w=CW, d=CW, h=round((flat + 16.0 - z0) / 0.2) * 0.2).translate([x, y, z0])
        kit.add(f"CHIMNEY-{k}", "White", ch, key="CHIMNEY", group="roof")

    # --- the cupola: V-groove walls, twin arched lights, its own cornice and a low hip
    cx, cy = CUP_C
    hs = CUP_SIZE / 2
    cze = flat + CUP_H                    # the cupola's ledge
    czw = cze + CO.band_height(CUPOLA_C)
    cup = Block("cupola", [(cx - hs, cy - hs), (cx + hs, cy - hs), (cx + hs, cy + hs), (cx - hs, cy + hs)], flat, czw)
    twin = O.twin_arch_window(12.0, 17.0, casing=1.0, balcony=0)
    cup_ops = []
    for (x, y, nm) in ((cx, cy - hs, "S"), (cx + hs, cy, "E"), (cx, cy + hs, "N"), (cx - hs, cy, "W")):
        e, u = cup.locate(x, y)
        cup_ops.append(Opening(cup, e, u, 4.4, twin, f"cupola-{nm}"))
    cup_und = [slab(offset(cup.cs, 8.0), cze - LEDGE - 0.6, czw + 0.01)]
    cwalls = wall_shell([cup], cup_ops, t=2.4, belt=None, corners="panel", water_table=False,
                        siding=lambda f, b, reg: SK.vgroove(reg, datum=0.6), undress=cup_und)
    clip = _corbel(cup.cs, 2.4, czw) + lip_ring(cup.cs, 2.4, czw)
    kit.add("CUPOLA-walls", "White", cwalls + CO.ledge(cup.pts, cze, LEDGE, t=2.4) + clip, group="cupola")
    for o in cup_ops:
        A = o.local_frame()
        world, P, zones = O.place(o.spec, A, "Windows_Doors", "Windows_Doors", "Glass")
        kit.add(f"WIN-{o.name}", "Windows_Doors", world, P=P, key="WIN-cupola", group="cupola", render=zones)
    rings, _ = CO.level(cup.pts, cze, CUPOLA_C, t=2.4)
    CO.add_level(kit, rings, "CORNICE-CUP", "cupola")
    cd = CUPOLA_C["layers"][-1]["P"] + 0.6
    croof, ctex = R.hip_roof([(cup.pts, [0, 1, 2, 3])], czw + 1.4, 0.62, cd, texture="seam", tex_kw=dict(seam_pitch=3.6),
                             zlo=czw)
    ztip = czw + 1.4 + 0.62 * (hs + cd)
    zseat = round((ztip - 0.8) / 0.2) * 0.2          # the roof's tip is cut flat with a shallow seat for the finial
    seat = M.cylinder(1.0, 1.5, 1.5, 32).translate([cx, cy, zseat - 0.4])
    kit.add("CUPOLA-roof", "Charcoal", (croof + ctex).trim_by_plane([0, 0, -1.0], -zseat) - seat
            - lip_keep(cup.cs, 2.4, czw), group="cupola")
    kit.add("CUPOLA-finial", "Charcoal", TW.finial("acorn", 1.4, 9.0).translate([cx, cy, zseat - 0.4]), group="cupola")
    print("roof + cupola", round(time.time() - t0, 1))

    # --- front porch: full width, chamfered posts, vase railings, scroll arcades, steps at the door
    H_floor = ZF - 1.4
    post_h = S1 - 2.0 - 5.6 - H_floor                         # the roof tucks under the joint's ledge
    y0, y1 = -1.4, -30.0
    runs = [dict(a=(0.0, y0), b=(0.0, y1), posts=[1.7, 27.0]),
            dict(a=(0.0, y1), b=(W, y1), posts=[1.6, 27.0, 52.0, 75.0, 105.0, 128.0, 153.0, W - 1.6]),
            dict(a=(W, y1), b=(W, y0), posts=[1.6, 26.9])]
    P = FT.porch_turned([(0.0, y0), (0.0, y1), (W, y1), (W, y0)], runs, H_floor, post_h,
                        steps_at=[(1, DOOR_X, 18.0)], planks=dict(pitch=2.2, border=1.6), joined=True,
                        post="chamfered", rail="vase", arcade="scroll", skirt="panels", pier_tex="limestone",
                        roof_edge="modillion")
    fkeep = slab(offset(poly(MAIN.pts), 0.8 + 0.55 + 0.15), -1, ZF + 1.3)
    ins_keep = union([box(np.array(p.solid.bounding_box()[:3]) - 0.2, np.array(p.solid.bounding_box()[3:]) + 0.2)
                      for p in inserts if p is not None])
    deck = P["deck"] - fkeep           # planks and frame in one part: wood planks, one filament change
    kit.add("PORCH-deck", "PorchDeck", deck, P=print_flip(), group="porch",
            render=FT.plank_zones(deck, H_floor, "Planks", "PorchDeck"))
    # posts and railings: one upright piece each side of the steps (round all the way round)
    for k, fr in enumerate(sorted(P["frames"], key=lambda m: m.bounding_box()[0])):
        kit.add(f"PORCH-frame-{k}", "White", fr, group="porch")
    for k, (arc, A) in enumerate(P["arcades"]):
        kit.add(f"PORCH-arcade-{k}", "White", arc, P=compose(FT.ARCADE_PRINT, inv34(A)), group="porch")
    bld_keep = MAIN.solid(grow=1.45, dz0=-20, dz1=0)
    proof = P["roof"] - bld_keep - ins_keep
    ptop = proof.bounding_box()[5]
    cap = proof.trim_by_plane([0, 0, 1.0], ptop - 0.8)          # standing-seam tin cap, its own colour
    bx = proof.bounding_box()
    cap_cs = cap.slice(ptop - 0.4)
    ribs = union([box([x - 0.25, -1000, ptop - 0.01], [x + 0.25, 1000, ptop + 0.4])
                  for x in np.arange(bx[0] + 2.6, bx[3] - 1.0, 5.2)]) ^ M.extrude(cap_cs.offset(-0.5), 5).translate([0, 0, ptop - 1])
    below = proof.trim_by_plane([0, 0, -1.0], -(ptop - 0.8))
    kit.add("PORCH-roof", "White", below, P=print_flip(), group="porch")
    kit.add("PORCH-roof-tin", "Charcoal", cap + ribs, group="porch")
    for k, (sm, A) in enumerate(P["steps"]):
        kit.add(f"PORCH-steps-{k}", "Stone", sm.transform(A) - fkeep, group="porch")
    # back stoop
    e, u = ELL.locate(150.0, D + 50)
    f = ELL.facades()[e]
    A = f.A.copy()
    A[:, 3] = f.world(u, -ZF, 1.4)
    kit.add("STOOP-back", "Stone", FT.steps(15.0, ZF - 0.6, 4).transform(A), group="porch")
    print("specks dropped:", kit.drop_specks())
    print("ell + porch", round(time.time() - t0, 1))
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "villa")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:40]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "villa.npz"))
    if "views" in sys.argv:
        small = ("WIN-", "DOOR-", "SHUTTER-")
        kit.flatlay_npz(os.path.join(OUT, "villa_flat_big.npz"), only=lambda p: not p.name.startswith(small),
                        width=470.0, gap=8.0)
        seen = set()

        def one_each(p):     # one of each window / door / shutter design
            if not p.name.startswith(small) or p.key in seen:
                return False
            seen.add(p.key)
            return True
        kit.flatlay_npz(os.path.join(OUT, "villa_flat_small.npz"), only=one_each, width=150.0, gap=4.0)
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors", "Test"))

"""The Ashby — an original HO-scale (1:87.1) Italianate villa, first building of the lineup.

Two-storey square block of cream common-bond brick with stone quoins and a dentil belt,
a canted bay, low hipped standing-seam roof on deep bracketed eaves, a V-groove cupola
with an acorn finial, full-width porch (chamfered posts, vase balusters, scroll frieze,
panelled skirt), one-storey kitchen ell, panel shutters, stucco chimneys and a smooth
limestone foundation.

usage: python3 -m hoarch.buildings.villa [check] [export] [views]
"""
import os
import sys
import time

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import box, compose, inv34, offset, poly, slab, union
from hoarch import features as FT, openings as O, roof as R, skins as SK, trimwork as TW
from hoarch.kit import Kit, print_flip
from hoarch.shell import Block, Opening, foundation, lip_keep, storey_shells, wall_shell

NAME = "Ashby Italianate Villa"
COLORS = {"PorchDeck": "#F2F0EB", "Planks": "#6F5034",       # the planked porch deck: two colours, one change
          "Sand": "#D8C49A", "White": "#F2F0EB", "Charcoal": "#3E4247", "Stone": "#8C8A85",
          "Forest": "#2F4A3A", "Brick": "#8A3B2B", "Windows_Doors": "#F2F0EB"}
# windows and doors are one part each (plug with glass and sash, and the surround), all on
# their own plate: it is the one plate printed with supports (under the surrounds)
RENDER_MAT = {"PorchDeck": "trim", "Planks": "planks",
              "Sand": "siding", "White": "trim", "Charcoal": "roof", "Stone": "stone", "Forest": "accent",
              "Brick": "brick", "Windows_Doors": "trim", "Glass": "glass"}
PALETTE = {"siding": ["#D8C49A", 0.6, 0.0], "trim": ["#EEECE7", 0.55, 0.0], "roof": ["#3E4247", 0.5, 0.0],
           "stone": ["#8C8A85", 0.85, 0.0], "accent": ["#2F4A3A", 0.5, 0.0], "brick": ["#8A3B2B", 0.85, 0.0]}

# ------------------------------------------------------------------ massing (mm, plan x east / y north, front = south)
ZF = 12.0                         # foundation / first floor
H2 = 78.0                         # two-storey wall height
ZW = ZF + H2                      # wall top
BELT = (41.0, 45.4)              # first-floor shell top / belt ring top, above ZF
MAIN = Block("main", [(0, 0), (134, 0), (134, 34), (146, 46), (146, 72), (134, 84), (134, 118), (0, 118)], ZF, ZW)
ELL = Block("ell", [(74, 118), (128, 118), (128, 170), (74, 170)], ZF, ZF + BELT[0])
BLOCKS = [MAIN, ELL]
V1, V2 = 5.0, 48.6               # sill heights above the wall base

EAVE = R.EAVE_DEEP
Z_EAVE_TOP = ZW + EAVE[-1][1]
ROOF_SLOPE = 0.5
D_EAVE = 7.0
CUP_SIZE, CUP_H = 34.0, 22.0
CUP_C = (67.0, 59.0)


# ------------------------------------------------------------------ openings
def _openings():
    L = []
    s22 = dict(lites=(2, 2), rows=(2, 2))       # four-over-four sash
    lo = O.window_insert(10.0, 24.0, rise=0, style="flat", apron=True, **s22)
    up = O.window_insert(10.0, 21.0, rise=None, style="key", **s22)
    bay_lo = O.window_insert(9.0, 24.0, rise=0, style="flat", casing=0.8, ends=0.2, sill_ext=0.3, clip=True,
                             apron=True, **s22)
    bay_up = O.window_insert(9.0, 21.0, rise=None, style="key", casing=0.8, ends=0.2, sill_ext=0.3, clip=True, **s22)
    ell_w = O.window_insert(9.0, 21.0, rise=0, style="flat", apron=True, **s22)
    twin = O.twin_arch_window(14.0, 21.0, balcony=0)
    front = O.door_insert(16.0, 30.0, leaves=2, transom=5.0)
    back = O.door_insert(11.0, 26.0, leaves=1, glass_top=True)

    def add(block, x, y, v0, sp, name, kind="window", shutters=False):
        e, u = block.locate(x, y)
        L.append((Opening(block, e, u, v0, sp, name, kind), shutters))

    # front (south)
    for x in (27.0, 107.0):
        add(MAIN, x, 0, V1, lo, f"S{x:.0f}-1", shutters=True)
        add(MAIN, x, 0, V2, up, f"S{x:.0f}-2", shutters=True)
    add(MAIN, 67.0, 0, 0.4, front, "front-door", "door")
    add(MAIN, 67.0, 0, V2, twin, "S67-2")
    # east, with the canted bay
    for y in (17.0, 101.0):
        add(MAIN, 134, y, V1, lo, f"E{y:.0f}-1", shutters=True)
        add(MAIN, 134, y, V2, up, f"E{y:.0f}-2", shutters=True)
    for (x, y, nm) in ((146, 59, "front"), (140, 40, "c1"), (140, 78, "c2")):
        add(MAIN, x, y, V1, bay_lo, f"bay-{nm}-1")
        add(MAIN, x, y, V2, bay_up, f"bay-{nm}-2")
    # west
    for y in (30.0, 88.0):
        add(MAIN, 0, y, V1, lo, f"W{y:.0f}-1", shutters=True)
        add(MAIN, 0, y, V2, up, f"W{y:.0f}-2", shutters=True)
    # rear (north) of the main block, clear of the ell
    for x in (25.5, 51.5):
        add(MAIN, x, 118, V1, lo, f"N{x:.0f}-1", shutters=True)
        add(MAIN, x, 118, V2, up, f"N{x:.0f}-2", shutters=True)
    # kitchen ell
    for y in (131.6, 155.5):
        add(ELL, 128, y, V1 + 1, ell_w, f"ellE{y:.0f}", shutters=True)
    add(ELL, 74, 150.0, V1 + 1, ell_w, "ellW150", shutters=True)
    add(ELL, 89.0, 170, V1 + 1, ell_w, "ellN89", shutters=True)
    add(ELL, 114.0, 170, 0.4, back, "back-door", "door")
    return L


OPENINGS_S = _openings()
OPENINGS = [o for o, _ in OPENINGS_S]


def _brick(f, b, reg):
    """Cream common-bond brick: five stretcher courses to every header course."""
    return SK.brick_bond(reg, "common", datum=1.8)


# ------------------------------------------------------------------ build
def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    # one shell per storey with a White belt ring between (the ring is the joint)
    clear = [lip_keep(poly(MAIN.pts) + poly(ELL.pts), 3.0, ZF, 1.2),                 # foundation lip
             lip_keep(poly(MAIN.pts), 3.0, ZW - 1.6, 1.6, inner=0.15, reach=1.2)]    # eave lip
    bprof, bblocks = TW.BELTS["dentil"]
    S = storey_shells(BLOCKS, OPENINGS, ZF + BELT[0], t=3.0, corners="quoin", clear=clear, prof=bprof,
                      belt_blocks=bblocks, siding=_brick, partitions=[((67.0, 3.0), (67.0, 115.0), 2.0, ZF, ZW)])
    kit.add("WALLS-1", "Sand", S["lower"], group="walls")
    kit.add("BELT", "White", S["ring"], group="walls")
    kit.add("WALLS-2", "Sand", S["upper"], group="walls")
    kit.add("FOUNDATION", "Stone", foundation(BLOCKS, 0.0, ZF, style="limestone"), group="foundation")
    # inserts and shutters
    inserts = []
    for o, sh in OPENINGS_S:
        A = o.local_frame()
        sp = o.spec
        tag = f"{sp['cut'].bounds()[2] - sp['cut'].bounds()[0]:.1f}x{sp['cut'].bounds()[3] - sp['cut'].bounds()[1]:.1f}"
        key = "DOOR" if o.kind == "door" else "WIN"
        col = "Forest" if o.kind == "door" else "White"
        world, P, zones = O.place(sp, A, "White", col, "Glass")          # one part: glass, sash and frame
        inserts.append(kit.add(f"{key}-{o.name}", "Windows_Doors", world, P=P,
                               key=f"{key}-{tag}-{o.v0 > 20}", group="inserts", render=zones))
        if sh:
            w_op = sp["cut"].bounds()[2] - sp["cut"].bounds()[0]
            h_op = sp["cut"].bounds()[3] - sp["cut"].bounds()[1]
            arched = abs(sp["top"] - h_op) > 3.0 and o.v0 > 20
            hh = (h_op - w_op / 2 - 1.8) if arched else h_op
            left, right = FT.shutters_for(w_op, h_op, casing=1.1, h=hh, style="panel")
            for side, m in (("L", left), ("R", right)):
                ms = m.translate([0, 0, 0.32]).transform(A)
                kit.add(f"SHUTTER-{o.name}-{side}", "Forest", ms, P=inv34(A), key=f"SHUTTER-{hh:.1f}",
                        group="shutters")
    print("walls + inserts", round(time.time() - t0, 1))
    # main eave + roof
    eave = R.bracketed_cornice(MAIN.pts, ZW, EAVE,
                               brackets=dict(z_top=5.2, h=5.0, d0=0.9, d=5.6, t=0.8, pitch=12.0, pair=1.9, margin=4.5),
                               dents=dict(z=4.4, h=0.8, d0=0.9, d=0.7), panels=dict(z=0.6, h=3.0, d=0.4))
    kit.add("EAVE-main", "White", eave, P=print_flip(), group="roof")
    rect_p = [(0, 0), (134, 0), (134, 118), (0, 118)]
    bay_p = [(120, 34), (134, 34), (146, 46), (146, 72), (134, 84), (120, 84)]
    z_eave = Z_EAVE_TOP
    i_top = 43.2                          # flat deck at +21.6: a layer line
    flat = z_eave + ROOF_SLOPE * i_top
    roof, tex = R.hip_roof([(rect_p, [0, 1, 2, 3]), (bay_p, [1, 2, 3])], z_eave, ROOF_SLOPE, D_EAVE,
                           texture="seam", flat_top=flat)
    # chimney pockets
    chims = [(22.0, 59.0), (112.0, 59.0)]
    def chim_z0(x):   # 3 mm below the lowest roof point under the chimney
        return z_eave + ROOF_SLOPE * (min(x + D_EAVE, 134 + D_EAVE - x) - 5.25) - 3.0

    pockets = union([box([x - 5.65, y - 5.65, chim_z0(x)], [x + 5.65, y + 5.65, flat + 20]) for x, y in chims])
    kit.add("ROOF-main", "Charcoal", (roof + tex) - pockets, group="roof")
    for k, (x, y) in enumerate(chims):
        z0 = chim_z0(x)
        ztop = flat + 14.0
        ch = TW.chimney("stucco", w=10.5, d=10.5, h=ztop - z0).translate([x, y, z0])
        kit.add(f"CHIMNEY-{k}", "White", ch, key="CHIMNEY", group="roof")
    # cupola
    cx, cy = CUP_C
    hs = CUP_SIZE / 2
    cup = Block("cupola", [(cx - hs, cy - hs), (cx + hs, cy - hs), (cx + hs, cy + hs), (cx - hs, cy + hs)],
                flat, flat + CUP_H)
    twin = O.twin_arch_window(10.0, 14.0, casing=0.9, balcony=0)
    cup_ops = []
    for (x, y, nm) in ((cx, cy - hs, "S"), (cx + hs, cy, "E"), (cx, cy + hs, "N"), (cx - hs, cy, "W")):
        e, u = cup.locate(x, y)
        cup_ops.append(Opening(cup, e, u, 4.0, twin, f"cupola-{nm}"))
    kit.add("CUPOLA-walls", "White", wall_shell([cup], cup_ops, t=2.4, belt=None, corners="panel", water_table=False,
                                                siding=lambda f, b, reg: SK.vgroove(reg, datum=0.6)),
            group="cupola")
    for o in cup_ops:
        A = o.local_frame()
        world, P, zones = O.place(o.spec, A, "White", "White", "Glass")
        kit.add(f"WIN-{o.name}", "Windows_Doors", world, P=P, key="WIN-cupola", group="cupola", render=zones)
    cz = flat + CUP_H
    cup_eave = R.bracketed_cornice(cup.pts, cz, R.CORNICE_SMALL,
                                   brackets=dict(z_top=4.6, h=4.2, d0=0.8, d=2.4, t=0.7, pitch=7.0, pair=1.5, margin=3.0),
                                   dents=dict(z=3.8, h=0.8, d0=0.8, d=0.7), lip_t=2.4, deck=(6.0, 8.0),
                                   panels=dict(z=0.6, h=2.4, d=0.4))
    kit.add("CUPOLA-eave", "White", cup_eave, P=print_flip(), group="cupola")
    croof, ctex = R.hip_roof([(cup.pts, [0, 1, 2, 3])], cz + 8.0, 0.62, 4.5, texture="seam",
                             tex_kw=dict(seam_pitch=3.6))
    ztip = cz + 8.0 + 0.62 * (hs + 4.5)
    zseat = ztip - 0.8                   # the roof's tip is cut flat with a shallow seat for the finial
    seat = M.cylinder(1.0, 1.35, 1.35, 32).translate([cx, cy, zseat - 0.4])
    kit.add("CUPOLA-roof", "Charcoal", (croof + ctex).trim_by_plane([0, 0, -1.0], -zseat) - seat, group="cupola")
    kit.add("CUPOLA-finial", "Charcoal", TW.finial("acorn", 1.2, 7.4).translate([cx, cy, zseat - 0.4]), group="cupola")
    print("roof + cupola", round(time.time() - t0, 1))
    # kitchen ell: eave + low hip roof against the main wall
    main_keep = MAIN.solid(grow=2.0, dz0=-1, dz1=200)         # clear of the belt ring (1.8 proud)
    ell_eave = R.bracketed_cornice(ELL.pts, ELL.z1, R.CORNICE_SMALL,
                                   brackets=dict(z_top=4.6, h=4.2, d0=0.8, d=2.4, t=0.7, pitch=8.0, margin=2.4),
                                   dents=dict(z=3.8, h=0.8, d0=0.8, d=0.7),
                                   panels=dict(z=0.6, h=2.4, d=0.4)) - main_keep
    kit.add("EAVE-ell", "White", ell_eave, P=print_flip(), group="roof")
    eroof, etex = R.hip_roof([(ELL.pts, [1, 2, 3])], ELL.z1 + 8.0, ROOF_SLOPE, 4.5, texture="seam")
    kit.add("ROOF-ell", "Charcoal", (eroof + etex) - main_keep, group="roof")
    # front porch: full width, turned posts, upright railings, sawn-work arcades, steps at the door
    H_floor = ZF - 1.0
    post_h = (ZF + BELT[0] - 0.2) - (H_floor + 5.2)          # roof tucks under the belt ring
    y0, y1 = -1.4, -27.0
    runs = [dict(a=(0.0, y0), b=(0.0, y1), posts=[1.7, 24.0]),
            dict(a=(0.0, y1), b=(134.0, y1), posts=[1.6, 28.0, 54.5, 79.5, 106.0, 132.4]),
            dict(a=(134.0, y1), b=(134.0, y0), posts=[1.6, 23.9])]
    P = FT.porch_turned([(0.0, y0), (0.0, y1), (134.0, y1), (134.0, y0)], runs, H_floor, post_h,
                        steps_at=[(1, 67.0, 16.0)], planks=dict(pitch=2.2, border=1.6), joined=True,
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
    bld_keep = union([b.solid(grow=1.45, dz0=-20, dz1=0) for b in BLOCKS])
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
    e, u = ELL.locate(114.0, 170)
    f = ELL.facades()[e]
    A = f.A.copy()
    A[:, 3] = f.world(u, -ZF, 1.4)
    kit.add("STOOP-back", "Stone", FT.steps(14.0, ZF - 0.6, 3).transform(A), group="porch")
    print("ell + porch", round(time.time() - t0, 1))
    return kit


def exploded_offsets(kit):
    """Per-part (dx, dy, dz) that pull the kit apart along its assembly directions:
    foundation, first-floor shell, belt ring and second-floor shell apart, inserts out
    of their openings, roof and cupola up, porch forward."""
    normal = {}
    for o, _ in OPENINGS_S:
        normal[o.name] = o.facade.n
    for nm, n in (("S", (0, -1)), ("E", (1, 0)), ("N", (0, 1)), ("W", (-1, 0))):
        normal[f"cupola-{nm}"] = np.array(n, float)
    UP = 30.0                                    # second storey lift
    lift = {"FOUNDATION": -24, "WALLS-1": 0, "BELT": UP / 2, "WALLS-2": UP, "EAVE-main": UP + 26,
            "ROOF-main": UP + 50, "CHIMNEY": UP + 84, "CUPOLA": UP + 84, "CUPOLA-eave": UP + 104,
            "CUPOLA-roof": UP + 120, "CUPOLA-finial": UP + 136, "EAVE-ell": 20, "ROOF-ell": 38}
    out = {}
    for p in kit.parts:
        nm = p.name
        d = np.zeros(3)
        if nm.startswith(("WIN-", "DOOR-", "SHUTTER-")):
            oname = nm.split("-", 1)[1].rsplit("-", 1)[0]
            n = normal.get(oname, np.zeros(2))
            d[:2] = n * (9.0 if nm.startswith("SHUTTER-") else 17.0)
            if "cupola" in oname:
                d[2] = lift["CUPOLA"]
            elif oname.endswith("-2"):
                d[2] = UP
            if oname.startswith(("S", "front")) and not oname.endswith("-2"):
                d[:2] += n * 36          # clear of the porch
        elif nm.startswith("PORCH-"):
            d[1] = -46
            d[2] = {"PORCH-roof": 26, "PORCH-roof-tin": 36}.get(nm, 0)
            if nm.startswith("PORCH-steps"):
                d[1] -= 12
        elif nm == "STOOP-back":
            d[1] = 18
        else:
            key = nm if nm in lift else nm.split("-")[0]
            d[2] = lift.get(key, 0)
        out[nm] = tuple(d)
    return out


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
        kit.render_npz(os.path.join(OUT, "villa_exploded.npz"), offsets=exploded_offsets(kit))
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

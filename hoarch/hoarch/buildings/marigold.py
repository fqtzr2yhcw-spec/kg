"""The Marigold -- an original HO-scale (1:87.1) gingerbread cottage, after the user's photo of a
turquoise cottage with gold lace trim. Rev B: the house-size plan (124 x 172 mm, a 46 mm storey),
framed windows spaced along the walls, and a built-up cornice under the roof.

A tall one-storey front-gabled cottage with a side cross gable, in turquoise ogee-lap siding on a coquina-stone base, with
reeded corner boards. The steep front gable is the show piece: a deep gold lace bargeboard
with a cusped edge, scrolls curling at its feet, a pendant and a fleur finial; a lace band
across the gable's foot with pierced corners rising up the rakes; a round medallion under the
apex; and a round-headed window under a gold fan hood with a sunburst and scroll ears. Across
the whole front, a porch on orange boxed posts with gold lace arches (scrolls, eyelets and
pendants), gold lace railings, a scalloped fascia and a planked floor; orange round-headed
windows under halo mouldings; a door with a lace-grilled light under a fan hood. Cove-cut
shingles on the roof, a fluted chimney. Under the eaves a four-part cornice: a gold frieze of
linked rings, an orange bead-and-reel course, a gold soffit on jigsawn brackets and an orange
ogee crown; it runs across the gable feet under the lace. Add-ons: a blue rocking chair and
flower boxes.

Colour comes from the part split: turquoise walls, gold lace, orange posts, windows and doors,
grey roofs. The porch deck prints planks first (one filament change); the flower boxes change
to pink for the flowers.

usage: python3 -m hoarch.buildings.marigold [check] [export]
"""
import math
import os
import sys
import time

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import box, compose, inv34, offset, poly, rect, slab, union
from hoarch import cornice as CO, extras as EX, features as FT, gables as G, lace as LC, openings as O, roof as R, \
    skins as SK, storefront as SF, trimwork as TW
from hoarch.kit import Kit, print_flip
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, wall_shell

NAME = "The Marigold Cottage"
COLORS = {"Turquoise": "#3FB5AE", "Gold": "#E7B52B", "Orange": "#E2772C", "Roof": "#4C5056", "Stone": "#CDBFA3",
          "PorchDeck": "#E2772C", "Planks": "#7A5A3A", "Brick": "#9A4A36", "Blue": "#3E6FB5",
          "FlowerBox": "#3FB5AE", "Windows_Doors": "#E2772C"}
RENDER_MAT = {"Turquoise": "siding", "Gold": "gold", "Orange": "orange", "Roof": "roof", "Stone": "stone",
              "PorchDeck": "orange", "Planks": "planks", "Brick": "brick", "Blue": "blue",
              "Pink": "pink", "FlowerBox": "siding", "Blooms": "pink", "Windows_Doors": "orange", "Sash": "sash",
              "Door": "door", "Glass": "glass"}

# ------------------------------------------------------------------ the cornice (unique to the Marigold)
LEDGE = 1.4
EAVE = dict(pitch=11.0, margin=3.6, layers=[
    dict(kind="frieze", h=5.0, b=1.2, orn="circles", role="Gold"),
    dict(kind="course", h=1.6, b=1.4, orn="beadreel", role="Orange"),
    dict(kind="bed", h=1.8, b=1.4, P=5.6, role="Gold", brackets=dict(style="sawn", t=0.8, reach=0.55)),
    dict(kind="crown", h=2.4, b=1.4, P=6.4, orn="ogee_fillet", role="Orange")])
HE = CO.band_height(EAVE)

# ------------------------------------------------------------------ levels (on the 0.2 mm grid)
ZF = 10.0
ZE = ZF + 46.0                  # the eave ledge's top: the wall face ends here
ZW = ZE + HE                    # the wall top behind the cornice: the roof sits here
FASCIA = 1.6
Z_EAVE = ZW + FASCIA
D_EAVE, RAKE, SKIN = 6.8, 7.0, 1.8
S = 1.3                         # a steep front gable, as in the photo
S2 = 1.3                        # the side cross gable

# ------------------------------------------------------------------ plan
W, D = 124.0, 172.0
Y0, Y1 = 100.0, 148.0           # the cross gable on the east side
MAIN = Block("main", [(0, 0), (W, 0), (W, D), (0, D)], ZF, ZW)
V_GW = ZW - ZF + 7.0            # the gable window's foot (block-relative), clear of the lace band
GW_W, GW_H = 9.6, 26.0
PD = 32.0                       # porch depth


def _siding(f, b, reg):
    reg = reg - rect(-1, ZE - ZF, f.L + 1, ZW - ZF)      # nothing behind the cornice
    return SK.ogee_lap(reg, datum=0.0)


def _gable_specs():
    return [dict(p0=(0.0, 0.0), p1=(W, 0.0), slope=S, edge=0, u0=0.0),
            dict(p0=(W, D), p1=(0.0, D), slope=S, edge=2, u0=0.0),
            dict(p0=(W, Y0), p1=(W, Y1), slope=S2, edge=1, u0=Y0, e=0.3)]


def _roof_pieces():
    r = RAKE - D_EAVE
    return [([(0.0, -r), (W, -r), (W, D + r), (0.0, D + r)], [1, 3], S),
            ([(W / 2 + 2.0, Y0), (W + r, Y0), (W + r, Y1), (W / 2 + 2.0, Y1)], [0, 2], S2)]


def _openings():
    L = []

    def add(x, y, v0, sp, name, kind="window"):
        e, u = MAIN.locate(x, y)
        L.append(Opening(MAIN, e, u, v0, sp, name, kind))

    win = SF.window_commercial(8.4, 26.0, rise=4.2, lites=(2, 2), rows=(1, 2), sill=1.2, head="halo", casing=1.3,
                               band=True)
    add(W / 2, 0.0, 0.0, SF.door_commercial(10.0, 30.0, transom=0.0, leaf="lace", tstyle="plain", head="fanhood"),
        "front-door", "door")
    for x in WIN_X:
        add(x, 0.0, 9.0, win, f"F{x:.0f}")
    gw = SF.window_commercial(GW_W, GW_H, rise=GW_W / 2, lites=(1, 1), rows=(1, 1), sill=1.0, head=None, casing=1.3,
                              band=True)
    add(W / 2, 0.0, V_GW, gw, "gable")
    add(W / 2, D, V_GW, gw, "back-gable")
    add(W, (Y0 + Y1) / 2, ZW - ZF + 5.0, SF.window_commercial(7.2, 16.0, rise=3.6, lites=(1, 1), rows=(1, 1), sill=1.0,
                                                               head=None, casing=1.3, band=True), "east-gable")
    for y in (28.0, 64.0, 100.0, 136.0):
        add(0.0, y, 9.0, win, f"W{y:.0f}")
    for y in (28.0, 64.0, (Y0 + Y1) / 2):
        add(W, y, 9.0, win, f"E{y:.0f}")
    add(W - 30.0, D, 0.0, SF.door_commercial(10.0, 30.0, transom=0.0, leaf="lace", tstyle="plain", head=None),
        "back-door", "door")
    for x in (28.0, 60.0):
        add(x, D, 9.0, win, f"B{x:.0f}")
    return L


WIN_X = (28.0, W - 28.0)
OPENINGS = _openings()


def _gable_trim():
    """The front gable's applied gold trim, in the front facade frame (u from x = 0, v up
    from the block base): the lace band across the gable's foot with its corners (kept inside
    the gable wall), and the gable window's fan hood."""
    v0 = ZW - ZF + 0.2
    screen = LC.gable_screen(W, S, v0=v0, band=2.4, corner=12.0)
    wall = poly([(0.0, 0.0), (W, 0.0), (W, v0 + 0.1), (W / 2, v0 + 0.1 + S * W / 2), (0.0, v0 + 0.1)]).offset(-0.5)
    screen = screen ^ M.extrude(wall, 5.0).translate([0, 0, -1.0])
    hood = LC.fan_hood(GW_W + 1.6, GW_H - GW_W / 2, band=1.6, ear=3.4, fan=4.2).translate([W / 2, V_GW, 0.0])
    return screen, hood


SCREEN, HOOD = _gable_trim()
FLOWER_V = 3.0                   # flower boxes hang under the front windows' sills


def _applied():
    out = []
    for name, m in (("SCREEN", SCREEN), ("HOOD", HOOD)):
        land = m.project().offset(0.15)
        out.append(Opening(MAIN, 0, 0.0, 0.0, SF.applied(land), name, "trim"))
    for x in WIN_X:
        out.append(Opening(MAIN, 0, 0.0, 0.0, SF.applied(rect(x - 5.9, FLOWER_V - 0.2, x + 5.9, FLOWER_V + 2.4)),
                           f"BOX{x:.0f}", "trim"))
    return out


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    specs = _gable_specs()
    rf = G.gabled_roof(_roof_pieces(), Z_EAVE, D_EAVE, specs, texture="cove", skin=SKIN, rake=RAKE,
                       inner_cs=offset(MAIN.cs, -3.0), fascia=FASCIA, tex_kw=dict(pitch=1.6, wtab=2.2))
    gables = [(MAIN, g["edge"], wl["cs"].translate((g["u0"], Z_EAVE - ZF))) for g, wl in zip(specs, rf["walls"])]
    undress = [slab(offset(MAIN.cs, 8.0), ZE - LEDGE - 0.6, ZW + 0.01)]
    walls = wall_shell([MAIN], OPENINGS + _applied(), t=3.0, belt=None, corners="reeded", water_table=False,
                       siding=_siding, gables=gables, undress=undress)
    no_lip = union([box([-1, -1, ZW - 1], [W + 1, 5.0, ZW + 5]), box([-1, D - 5.0, ZW - 1], [W + 1, D + 1, ZW + 5]),
                    box([W - 5.0, Y0 - 1.5, ZW - 1], [W + 1, Y1 + 1.5, ZW + 5])])
    lip = (_corbel(MAIN.cs, 3.0, ZW) + lip_ring(MAIN.cs, 3.0, ZW)) - no_lip
    kit.add("WALLS", "Turquoise", walls + lip + CO.ledge(MAIN.pts, ZE, LEDGE), group="walls")
    rings, _ = CO.level(MAIN.pts, ZE, EAVE)
    CO.add_level(kit, rings, "CORNICE-E", "cornice")
    fnd = foundation([MAIN], 0.0, ZF, style="coquina")
    kit.add("FOUNDATION", "Stone", fnd, group="foundation")
    inserts = []
    for o in OPENINGS:
        A = o.local_frame()
        sp = o.spec
        b = sp["cut"].bounds()
        key = "DOOR" if o.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, "Windows_Doors", "Door" if o.kind == "door" else "Windows_Doors", "Glass")
        inserts.append(kit.add(f"{key}-{o.name}", "Windows_Doors", world, P=P,
                               key=f"{key}-{o.name.split('-')[0][:1]}-{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}",
                               group="inserts", render=zones))
    f = MAIN.facades()[0]
    Af = f.A.copy()
    Af[:, 3] = f.world(0.0, 0.0, 0.0)
    for name, m in (("GABLE-screen", SCREEN), ("GABLE-hood", HOOD)):
        kit.add(name, "Gold", m.transform(Af), P=inv34(Af), group="gable")
    print("walls + inserts", round(time.time() - t0, 1))

    # --- the roof: one hollow body with its rake skins, a fluted chimney near the back
    walls_env = union([wl["facade"].place(M.extrude(wl["cs"].offset(0.15), 3.8).translate([0, 0, -3.15]))   # + siding
                       for wl in rf["walls"]])
    zr = Z_EAVE + S * (W / 2 + D_EAVE)
    zc = Z_EAVE + S2 * ((Y1 - Y0) / 2 + D_EAVE)
    x_meet = W - ((zc - Z_EAVE) / S - D_EAVE) + 1.0          # where the cross ridge dies into the main slope
    ridge = G.ridge_cap((W / 2, -RAKE), (W / 2, D + RAKE), zr, S, ZW) + \
        G.ridge_cap((x_meet, (Y0 + Y1) / 2), (W + RAKE, (Y0 + Y1) / 2), zc, S2, ZW)
    roof = rf["body"] + rf["tex"] + rf["skins"] + rf["skin_tex"] + (ridge - walls_env)
    roof = roof - lip_keep(MAIN.cs, 3.0, ZW)
    CH = 9.2
    cx, cy = W / 2, D - 34.0
    z_low = zr - S * (CH / 2) - 0.2
    z0 = round((z_low - 2.4) / 0.2) * 0.2
    solid_env, _ = R.hip_roof(_roof_pieces(), Z_EAVE, S, D_EAVE, texture=None, zlo=ZW)
    roof = roof + G.chimney_seat(solid_env, cx, cy, CH / 2, zr + 1.0)
    pocket = box([cx - CH / 2 - 0.4, cy - CH / 2 - 0.4, z0], [cx + CH / 2 + 0.4, cy + CH / 2 + 0.4, zr + 40])
    kit.add("ROOF", "Roof", roof - pocket, group="roof")
    ch = TW.chimney("fluted", w=CH, d=CH, h=round((zr + 14.0 - z0) / 0.2) * 0.2).translate([cx, cy, z0])
    kit.add("CHIMNEY", "Brick", ch, group="roof")
    for k, (g, wl) in enumerate(zip(specs, rf["walls"])):
        big = wl["L"] > 40.0
        bb = LC.lace_bargeboard(wl["L"], wl["slope"], D_EAVE, skin=SKIN, width=5.0 if big else 3.6,
                                medal=6.0 if big else 3.4, curl=3.0)
        fw = wl["facade"]
        A = fw.A.copy()
        A[:, 3] = fw.world(0.0, 0.0, RAKE)
        bw = bb.transform(A) - (roof - pocket)                 # the cross gable's feet stop on the main roof
        bw = max(bw.decompose(), key=lambda m_: m_.volume())
        kit.add(f"BARGE-{k}", "Gold", bw, P=inv34(A), key=f"BARGE-{wl['L']:.0f}", group="gable")
    print("roof", round(time.time() - t0, 1))

    # --- the porch across the front: boxed posts, lace arches and railings, planked floor
    PX0, PX1 = -1.0, W + 1.0
    ppoly = [(PX0, -PD), (PX1, -PD), (PX1, 0.0), (PX0, 0.0)]
    Lf = PX1 - PX0
    m = Lf / 2
    runs = [dict(a=(PX0, 0.0), b=(PX0, -PD), posts=[3.2, PD - 1.6]),
            dict(a=(PX0, -PD), b=(PX1, -PD), posts=[1.6, 30.0, m - 11.0, m + 11.0, Lf - 30.0, Lf - 1.6]),
            dict(a=(PX1, -PD), b=(PX1, 0.0), posts=[1.6, PD - 3.2])]
    H_floor = ZF - 1.0
    post_h = 36.0                   # the porch roof stays under the eave cornice
    P = FT.porch_turned(ppoly, runs, H_floor, post_h, steps_at=[(1, m, 16.0)],
                        planks=dict(pitch=1.8, border=1.2), joined=False, ledger_off=1.5, arcade="lace", post="boxed",
                        rail="lace", skirt="rings", pier_tex="coquina", roof_edge="scallop", drop=9.6)
    fkeep = slab(offset(MAIN.cs, 0.8 + 0.55 + 0.15), -1, ZF + 1.3)
    ins_keep = union([box(np.array(p.solid.bounding_box()[:3]) - 0.2, np.array(p.solid.bounding_box()[3:]) + 0.2)
                      for p in inserts if p is not None])
    socks = union([box([x - 1.75, y - 1.75, H_floor - 0.4], [x + 1.75, y + 1.75, H_floor + 1]) for x, y in P["sockets"]])
    deck = P["deck"] - fkeep - socks
    deck = union([c for c in deck.decompose() if c.volume() > 0.5])
    kit.add("PORCH-deck", "PorchDeck", deck, P=print_flip(), group="porch",
            render=FT.plank_zones(deck, H_floor, "Planks", "PorchDeck"))
    tabs = union([arc for arc, _ in P["arcades"]])
    for k, po in enumerate(P["posts"]):
        kit.add(f"PORCH-post-{k}", "Orange", po - tabs, key="PORCH-post", group="porch")
    for k, rl in enumerate(P["rails"]):
        L_ = rl.bounding_box()
        kit.add(f"PORCH-rail-{k}", "Gold", rl, key=f"PORCH-rail-{max(L_[3] - L_[0], L_[4] - L_[1]):.1f}", group="porch")
    for k, (arc, A) in enumerate(P["arcades"]):
        kit.add(f"PORCH-arcade-{k}", "Gold", arc, P=compose(FT.ARCADE_PRINT, inv34(A)), group="porch")
    bld_keep = MAIN.solid(grow=1.45, dz0=-20, dz1=0)
    proof = P["roof"] - bld_keep - ins_keep
    ptop = proof.bounding_box()[5]
    kit.add("PORCH-roof", "Gold", proof.trim_by_plane([0, 0, -1.0], -(ptop - 0.8)), P=print_flip(), group="porch")
    kit.add("PORCH-roof-top", "Roof", proof.trim_by_plane([0, 0, 1.0], ptop - 0.8), group="porch")
    for k, (sm, A) in enumerate(P["steps"]):
        kit.add(f"PORCH-steps-{k}", "Stone", sm.transform(A) - fkeep, group="porch")
    e, u = MAIN.locate(W - 16.0, D)
    fb = MAIN.facades()[e]
    A = fb.A.copy()
    A[:, 3] = fb.world(u, -ZF, 1.4)
    kit.add("STOOP-back", "Stone", FT.steps(14.0, ZF - 0.6, 4).transform(A), group="porch")
    print("porch", round(time.time() - t0, 1))

    # --- add-ons: a rocking chair and flower boxes
    a = math.radians(200.0)
    Rz = np.array([[math.cos(a), -math.sin(a), 0.0, 14.0], [math.sin(a), math.cos(a), 0.0, -PD + 10.0], [0, 0, 1.0, H_floor + 0.3]])
    Ark = compose(Rz, np.array([[1.0, 0, 0, 0], [0, 0, 1.0, 0], [0, 1.0, 0, 0]]))       # (x fwd, y up, z across) -> world
    kit.add("ROCKER", "Blue", EX.rocking_chair().transform(Ark), P=inv34(Ark), group="extras")
    for k, x in enumerate(WIN_X):
        e, u = MAIN.locate(x, 0.0)
        fw = MAIN.facades()[e]
        A = fw.A.copy()
        A[:, 3] = fw.world(u - 5.4, FLOWER_V, 0.0)
        bx = EX.flower_box(10.8)
        kit.add(f"FLOWERBOX-{k}", "FlowerBox", bx.transform(A), P=compose(np.array([[1.0, 0, 0, 0], [0, 0, -1.0, 0], [0, 1.0, 0, 0]]),
                                                                           inv34(A)), key="FLOWERBOX", group="extras",
                render=[("FlowerBox", (bx ^ box([-5, -5, -5], [20, 2.2, 5])).transform(A)),
                        ("Blooms", (bx - box([-5, -5, -5], [20, 2.2, 5])).transform(A))])
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "marigold")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:40]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "marigold.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))

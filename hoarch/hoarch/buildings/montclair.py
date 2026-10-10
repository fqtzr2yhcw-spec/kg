"""The Montclair -- an original HO-scale (1:87.1) Second Empire house: the first of the mansard
batch (houses 81 to 90), built on the batch's roof system (hoarch.secondempire).

A square, symmetrical villa of cream-city brick in Flemish stretcher bond with V-jointed
brownstone quoins, on a reticulated brownstone foundation. The last storey is a straight-sided
mansard of square slate banded with lozenges of diamond-cut slate with twelve window add-ins (round-headed lights between fluted
pilasters under keyed archivolts; a twin light with an oculus over the door), a crest on its
flat top and scrolled iron cresting. Two panelled stacks with octagonal pots. A veranda across
the whole front on Gibbs columns, pear balusters and a frieze of paired brackets.

- Ground-floor windows in tabernacle frames (colonnettes, a frieze with a rosette, a pediment,
  a swagged apron), upper windows under hood moulds on drop pendants with a fleuron; an arched
  doorway with voussoirs, a carved keystone, banded pilasters and a balustered entablature.
- Storey joint: a brownstone blind balustrade, a gilt leaf-and-dart course and a torus crown.
- Eave: a brownstone architrave of two fasciae, a gilt frieze of Napoleonic bees, a brownstone
  leaf-and-dart course, a soffit on paired fluted consoles and a gilt cyma crown.
- Crest (the mansard's top): gilt olive beads under a brownstone ovolo crown on block
  modillions, a slate deck with a roof hatch.

usage: python3 -m hoarch.buildings.montclair [check] [export]
"""
import math
import os
import sys
import time

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import box, compose, cs_union, inv34, offset, poly, rect, slab, union
from hoarch import cornice as CO, features as FT, openings as O, roof as R, secondempire as SE
from hoarch.kit import Kit, print_flip
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, stacked_shells

NAME = "Montclair"
COLORS = {"PorchDeck": "#5E3D2E", "Planks": "#6F5034",       # the planked veranda floor: two colours, one change
          "Brick": "#CDAA70", "Brownstone": "#5E3D2E", "Gold": "#B8913E", "Slate": "#3E4852", "Iron": "#232528",
          "Windows_Doors": "#5E3D2E", "Addins": "#3E4852"}      # add-ins: slate plug, one change to the frame colour
RENDER_MAT = {"PorchDeck": "trim", "Planks": "planks", "Brick": "brick", "Brownstone": "trim", "Gold": "accent",
              "Slate": "roof", "Iron": "iron", "Windows_Doors": "trim", "Addins": "roof", "Sash": "sash", "Door": "door", "Glass": "glass"}
PALETTE = {"brick": ["#CDAA70", 0.85, 0.0], "trim": ["#5E3D2E", 0.6, 0.0], "accent": ["#B8913E", 0.4, 0.35],
           "roof": ["#3E4852", 0.75, 0.0], "iron": ["#232528", 0.45, 0.3], "planks": ["#6F5034", 0.75, 0.0],
           "sash": ["#2A2420", 0.45, 0.0], "door": ["#3A2418", 0.45, 0.0]}

# ------------------------------------------------------------------ cornices (unique to the Montclair)
LEDGE = 1.4
JOINT = dict(pitch=13.0, margin=5.0, layers=[
    dict(kind="frieze", h=4.8, b=1.2, orn="balustrade", role="Brownstone"),
    dict(kind="course", h=1.8, b=1.4, orn="leafdart", role="Gold"),
    dict(kind="crown", h=2.2, b=1.4, P=3.6, orn="torus", role="Brownstone")])
EAVE = dict(pitch=13.0, margin=5.0, pair=2.8, layers=[
    dict(kind="course", h=2.0, b=1.0, orn="fasciae", role="Brownstone"),
    dict(kind="frieze", h=6.0, b=1.2, orn="bees", role="Gold"),
    dict(kind="course", h=1.6, b=1.4, orn="leafdart", role="Brownstone"),
    dict(kind="bed", h=2.2, b=1.4, P=6.8, role="Brownstone", brackets=dict(style="flutedconsole", t=1.6, reach=0.55)),
    dict(kind="crown", h=2.8, b=1.4, P=7.6, orn="cyma", role="Gold")])
CREST_COURSE = dict(h=2.0, b=0.6, orn=SE.olives, role="Gold")
CREST_CROWN = dict(h=2.6, P=3.6, kind="ovolo", role="Brownstone", blocks=(0.9, 5.2))
RJ = round((LEDGE + 0.4 + CO.band_height(JOINT)) / 0.2) * 0.2
HE = CO.band_height(EAVE)

# ------------------------------------------------------------------ levels (all on the 0.2 mm grid)
ZF = 12.0                 # foundation top / first floor
S1 = ZF + 42.0            # first-storey shell top = the joint ring's foot
ZE = S1 + RJ + 38.0       # the eave ledge's top
ZW = ZE + HE              # the wall top: the mansard's foot stands on the eave's crown
MZ0 = ZW
MH = 30.0                 # mansard height to the crest
MZ1 = MZ0 + MH
DK = EAVE["layers"][-1]["P"] + 0.2
D_TOP = -1.6
MANSARD = [(DK, MZ0), (DK - 1.4, MZ0 + 1.4), (D_TOP, MZ1)]     # a short kick, then straight at about 74 degrees
SLATE = SE.slate_lozenges
V1, V2 = 6.4, S1 + RJ + 5.0 - ZF        # sill heights above ZF
Z_ADD = MZ0 + 3.2                       # the add-ins' sill line

# ------------------------------------------------------------------ plan (mm; x east, y north, front = south)
X1, Y1 = 196.0, 148.0
MAIN = Block("main", [(0, 0), (X1, 0), (X1, Y1), (0, Y1)], ZF, ZW)
BLOCKS = [MAIN]
BAYS_X = (34.0, 98.0, 162.0)
BAYS_Y = (30.0, 74.0, 118.0)


def _brick(f, b, reg):
    """Flemish stretcher bond; nothing in the cornice bands."""
    reg = reg - rect(-1, ZE - b.z0, f.L + 1, ZW - b.z0)
    return SE.brick_flemishstretcher(reg, datum=1.8)


# ------------------------------------------------------------------ openings
def _openings():
    L = []
    lo = SE.window_montclair_lower()
    up = SE.window_montclair_upper()
    front = SE.door_montclair()
    back = SE.door_montclair_back()

    def add(x, y, v0, sp, name, kind="window"):
        e, u = MAIN.locate(x, y)
        L.append(Opening(MAIN, e, u, v0, sp, name, kind))

    for x in BAYS_X:
        if x != 98.0:
            add(x, 0, V1, lo, f"S{x:.0f}-1")
            add(x, Y1, V1, lo, f"N{x:.0f}-1")
        add(x, 0, V2, up, f"S{x:.0f}-2")
        add(x, Y1, V2, up, f"N{x:.0f}-2")
    add(98.0, 0, 0.4, front, "front-door", "door")
    add(98.0, Y1, 0.4, back, "back-door", "door")
    for y in BAYS_Y:
        for x in (0, X1):
            side = "W" if x == 0 else "E"
            add(x, y, V1, lo, f"{side}{y:.0f}-1")
            add(x, y, V2, up, f"{side}{y:.0f}-2")
    return L


OPENINGS = _openings()
# add-ins: (x, y) on the wall line, twin over the front door
ADDINS = [(x, 0.0) for x in BAYS_X] + [(X1, y) for y in BAYS_Y] + [(x, Y1) for x in BAYS_X] + [(0.0, y) for y in BAYS_Y]


def _addin_frame(x, y, w0):
    e, u = MAIN.locate(x, y)
    f = MAIN.facades()[e]
    A = f.A.copy()
    A[:, 3] = f.world(u, Z_ADD - ZF, w0)
    return A


# ------------------------------------------------------------------ build
def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    undress = [slab(offset(MAIN.cs, 8.0), ZE - LEDGE - 0.6, ZW + 0.01)]
    clear = [lip_keep(MAIN.cs, 3.0, ZF, 1.2)]
    st = stacked_shells(BLOCKS, OPENINGS, [S1], t=3.0, corners="quoin_vee", clear=clear, siding=_brick,
                        prof=CO.joint_profile(RJ, LEDGE), belt_blocks=None, water_table=False, undress=undress)
    kit.add("WALLS-1", "Brick", st["shells"][0], group="walls")
    kit.add("JOINT", "Brick", st["rings"][0], group="walls")
    kit.add("WALLS-2", "Brick", st["shells"][1] + CO.ledge(MAIN.pts, ZE, LEDGE), group="walls")
    rings, _ = CO.level(st["outlines"][0], S1 + LEDGE + 0.4, JOINT)
    CO.add_level(kit, rings, "CORNICE-J", "cornice")
    rings, _ = CO.level(MAIN.pts, ZE, EAVE)
    CO.add_level(kit, rings, "CORNICE-E", "cornice")
    kit.add("FOUNDATION", "Brownstone", foundation(BLOCKS, 0.0, ZF, style="reticulated"), group="foundation")
    inserts = []
    for o in OPENINGS:
        A = o.local_frame()
        sp = o.spec
        b = sp["cut"].bounds()
        tag = f"{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}"
        key = "DOOR" if o.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, "Brownstone", "Door" if o.kind == "door" else "Sash", "Glass")
        inserts.append(kit.add(f"{key}-{o.name}", "Windows_Doors", world, P=P,
                               key=f"{key}-{tag}-{o.v0 > 20}", group="inserts", render=zones))
    print("walls + cornices + inserts", round(time.time() - t0, 1))

    # --- the mansard (upside down) on the eave's crown, a pocket in every bay for its add-in
    mans, mtex, inner = R.mansard(MAIN.pts, MANSARD, t=2.6, tex=dict(pitch=1.8, wtab=2.4, d=0.4, shape=SLATE))
    single, twin = SE.addin_montclair(), SE.addin_montclair_twin()
    specs = [twin if (x, y) == (98.0, 0.0) else single for x, y in ADDINS]
    places = [SE.addin_place(sp, MANSARD, Z_ADD) for sp in specs]
    depth = max(d for _, d in places)              # one plug length: every add-in changes colour at one height
    keeps, flashes = [], []
    for k, ((x, y), sp, (w0, _)) in enumerate(zip(ADDINS, specs, places)):
        A = _addin_frame(x, y, w0)
        a = SE.addin(sp, depth)
        keeps.append(a["keep"].transform(A))
        flashes.append(a["flash"].transform(A))
        zones = [("Glass", a["glass"].transform(A)), ("Slate", (a["plug"] - a["glass"]).transform(A)),
                 ("Brownstone", a["frame"].transform(A))]
        kit.add(f"ADDIN-{k}", "Addins", a["solid"].transform(A), P=inv34(A), change=(round(depth, 1), "Brownstone"),
                key="ADDIN-twin" if sp is twin else "ADDIN", group="addins", render=zones)
    C = SE.crest_ring(MAIN.pts, D_TOP, MZ1, D_TOP - inner(MZ1), CREST_COURSE, CREST_CROWN)
    kit.add("MANSARD", "Slate", mans + (mtex - union(flashes)) - union(keeps) - C["groove"], P=print_flip(), group="roof")
    print("mansard + add-ins", round(time.time() - t0, 1), "plug", depth)

    # --- crest on the band's flat top (its key in the band's groove), the deck, cresting, chimneys
    kit.add("CREST", "Brownstone", C["solid"], P=print_flip(), change=C["change"], group="roof", render=C["zones"])
    zdeck = C["z_top"]
    deck = C["deck"]
    dpath = R.offset_path(C["path"], -1.6)
    cs = poly(dpath)
    x0, y0, x1, y1 = cs.bounds()
    seams = cs_union([rect(x - 0.25, y0, x + 0.25, y1) for x in np.arange(x0 + 2.6, x1, 5.2)]) ^ cs
    hatch = box([110.0, 92.0, zdeck - 0.01], [124.0, 104.0, zdeck + 1.6]) + \
        M.hull_points([(x, y, zdeck + 1.59) for x in (110.0, 124.0) for y in (92.0, 104.0)] +
                      [(x, y, zdeck + 2.2) for x in (109.4, 124.6) for y in (91.4, 104.6)])      # the lid flares at 45 degrees
    chims = [(14.0, 74.0), (182.0, 74.0)]
    pads = union([box([x - 6.4, y - 7.9, zdeck - 0.6], [x + 6.4, y + 7.9, zdeck + 1]) for x, y in chims])
    deck = deck + slab(seams - cs_union([rect(108.8, 90.8, 125.2, 105.2)]), zdeck - 0.01, zdeck + 0.4) + hatch
    kit.add("ROOF-deck", "Slate", deck - pads, group="roof")
    for i, seg, A, L in SE.cresting_strips(C["path"], zdeck, C["P"] - 1.4, SE.printable(SE.fence_montclair), 6.4):
        kit.add(f"CREST-iron-{i}", "Iron", seg, P=inv34(A), key=f"CREST-iron-{round(L, 1)}", group="roof")
    for k, (x, y) in enumerate(chims):
        ch = SE.chimney_montclair(w=10.4, d=13.4, h=24.0).translate([x, y, zdeck - 0.6])
        zc = zdeck - 0.6 + 20.0                    # the corbelled cap, coping and pots in brownstone: one change
        cap = ch ^ box([-1e3, -1e3, zc], [1e3, 1e3, 1e3])
        kit.add(f"CHIMNEY-{k}", "Brick", ch, key="CHIMNEY", group="roof", change=(20.0, "Brownstone"),
                render=[("Brick", ch - cap), ("Brownstone", cap)])
    print("roof", round(time.time() - t0, 1))

    # --- veranda across the front: Gibbs columns, pear balusters, a frieze of paired brackets
    H_floor = ZF - 1.4
    post_h = S1 - 2.0 - 5.6 - H_floor              # the roof tucks under the joint's ledge
    y0, y1 = -1.4, -27.0
    px0, px1 = -3.0, X1 + 3.0
    Lf = px1 - px0
    mid = 98.0 - px0
    runs = [dict(a=(px0, y0), b=(px0, y1), posts=[1.7, (y0 - y1) - 1.6]),
            dict(a=(px0, y1), b=(px1, y1), posts=[1.6, 50.0, mid - 12.0, mid + 12.0, Lf - 50.0, Lf - 1.6]),
            dict(a=(px1, y1), b=(px1, y0), posts=[1.6, (y0 - y1) - 1.7])]
    P = FT.porch_turned([(px0, y0), (px0, y1), (px1, y1), (px1, y0)], runs, H_floor, post_h,
                        steps_at=[(1, mid, 18.0)], planks=dict(pitch=1.4, border=1.6), joined=True,
                        post="gibbs", rail="pear", arcade="pairbrackets", skirt="crossvent", pier_tex="limestone",
                        roof_edge="pairconsoles", top=True)
    fkeep = slab(offset(MAIN.cs, 0.8 + 0.55 + 0.15), -1, ZF + 1.3)
    ins_keep = union([box([b[0] - 0.2, b[1] - 0.2, math.floor((b[2] - 0.2) / 0.2) * 0.2],
                          [b[3] + 0.2, b[4] + 0.2, math.ceil((b[5] + 0.2) / 0.2) * 0.2])
                      for b in (p.solid.bounding_box() for p in inserts if p is not None)])
    deck_ = P["deck"] - fkeep
    kit.add("PORCH-deck", "PorchDeck", deck_, P=print_flip(), group="porch",
            render=FT.plank_zones(deck_, H_floor, "Planks", "PorchDeck"))
    bld_keep = MAIN.solid(grow=1.45, dz0=-20, dz1=300)
    FT.add_porch_top(kit, "PORCH", P, bld_keep + ins_keep, "Brownstone", "Brownstone", tin_col="Slate", tin="flat")
    for k, (sm, A) in enumerate(P["steps"]):
        kit.add(f"PORCH-steps-{k}", "Brownstone", sm.transform(A) - fkeep, group="porch")
    e, u = MAIN.locate(98.0, Y1)
    f = MAIN.facades()[e]
    A = f.A.copy()
    A[:, 3] = f.world(u, -ZF, 1.6)
    kit.add("STOOP-back", "Brownstone", FT.steps(16.0, ZF - 0.6, 5).transform(A), group="porch")
    print("porch", round(time.time() - t0, 1))
    for p_ in [p_ for p_ in kit.parts if p_.name.startswith("CREST-iron")]:
        FT.key_into(kit, p_.name, ["CREST"], (0, 0, -1), depth=0.6)
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "montclair")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:40]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "montclair.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors", "Addins"))

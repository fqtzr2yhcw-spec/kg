"""The Primrose -- an original HO-scale (1:87.1) Eastlake Queen Anne, after the user's photo of a
butter-yellow house with a round-cornered porch. Rev B: the house-size plan (176 x 148 mm,
storeys of 42 and 38 mm), framed windows spaced along the walls, and built-up cornices at every
level.

Two storeys of butter double-course lap siding on a pebble-dash base, rope-moulded corner
boards. Between the floors a three-part cornice (an olive frieze of spindles, a burgundy rope
course and an olive cavetto crown); at the eave a four-part one (a burgundy guilloche frieze,
an olive dogtooth course, an olive soffit on beaded brackets and a burgundy ovolo crown),
running across the wing's gable foot. A hipped main block
with a flat top ringed by a widow's-walk railing, and a front-gabled wing: its gable faced in
sawtooth shingles and hung with an Eastlake ornament (a tie beam of rosette panels, a
half-round fan, a king post and a pinnacle).
Windows with a transom of small square lights over each sash, under head boards with
rosette blocks; a wide picture window in the wing. Across the front and round the corner in
a wide sweep, a porch on bobbin posts with beaded balusters, an Eastlake frieze of rosette
panels, a shingled skirt, a bead-and-reel fascia, and a pedimented gable with a fan over the
steps. Notched shingles on the roofs, a crowned brick chimney.

Colour comes from the part split: butter walls, olive trim, burgundy sash and doors, brown
roofs. The porch deck prints planks first (one filament change).

usage: python3 -m hoarch.buildings.primrose [check] [export]
"""
import math
import os
import sys
import time

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import box, compose, inv34, offset, rect, scallop_rows, slab, union
from hoarch import cornice as CO, features as FT, gables as G, openings as O, roof as R, skins as SK, \
    storefront as SF, trimwork as TW
from hoarch.kit import Kit, print_flip
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, stacked_shells

NAME = "The Primrose"
COLORS = {"Butter": "#F0D27C", "Olive": "#6F7447", "Burgundy": "#7A2E36", "Roof": "#6A4B36", "Pebble": "#B9B2A6",
          "PorchDeck": "#6F7447", "Planks": "#7A5A3A", "Brick": "#8E4632", "Windows_Doors": "#7A2E36"}
RENDER_MAT = {"Butter": "siding", "Olive": "olive", "Burgundy": "burgundy", "Roof": "roof", "Pebble": "stone",
              "PorchDeck": "olive", "Planks": "planks", "Brick": "brick", "Windows_Doors": "burgundy", "Sash": "sash",
              "Door": "door", "Glass": "glass"}

# ------------------------------------------------------------------ cornices (unique to the Primrose)
LEDGE = 1.4
JOINT = dict(pitch=11.0, margin=3.6, layers=[
    dict(kind="frieze", h=4.2, b=1.2, orn="spindles", role="Olive"),
    dict(kind="course", h=1.6, b=1.4, orn="rope", role="Burgundy"),
    dict(kind="crown", h=2.2, b=1.4, P=3.6, orn="cavetto", role="Olive")])
EAVE = dict(pitch=11.0, margin=3.6, layers=[
    dict(kind="frieze", h=5.2, b=1.2, orn="guilloche", role="Burgundy"),
    dict(kind="course", h=1.6, b=1.4, orn="dogtooth", role="Olive"),
    dict(kind="bed", h=1.8, b=1.4, P=5.8, role="Olive", brackets=dict(style="beaded", t=0.9, reach=0.55)),
    dict(kind="crown", h=2.6, b=1.4, P=6.6, orn="ovolo", role="Burgundy")])
RJ = round((LEDGE + 0.4 + CO.band_height(JOINT)) / 0.2) * 0.2
HE = CO.band_height(EAVE)

# ------------------------------------------------------------------ levels (on the 0.2 mm grid)
ZF = 12.0
S1 = ZF + 42.0                  # first-storey shell top = the joint ring's foot
RH = RJ
ZE = S1 + RJ + 38.0             # the eave ledge's top
ZW = ZE + HE                    # the wall top behind the eave cornice; the roof sits here
FASCIA = 1.8
Z_EAVE = ZW + FASCIA
D_EAVE, RAKE, SKIN = 7.0, 7.2, 1.8
S_MAIN, S_WING = 1.0, 1.15
Z_FLAT = Z_EAVE + 50.0          # the hip's flat top (over the wing's ridge)
V1 = 8.0
V2 = S1 + RJ + 5.0 - ZF

# ------------------------------------------------------------------ plan: an L of main block and front wing
W, D = 176.0, 148.0
WX0, WX1, WY = 86.0, 150.0, -38.0
PLAN = [(0, 0), (WX0, 0), (WX0, WY), (WX1, WY), (WX1, 0), (W, 0), (W, D), (0, D)]
MAIN = Block("main", PLAN, ZF, ZW)
BLOCKS = [MAIN]
TR_H = 4.2                      # the square-light transom over every window
DOOR_X = 44.0


def _siding(f, b, reg):
    """Double-course lap on both storeys; sawtooth shingles in the wing's gable; nothing behind
    the eave cornice."""
    lo = reg ^ rect(-1, -100, f.L + 1, ZE - ZF)
    hi = reg ^ rect(-1, ZW - ZF, f.L + 1, 400)
    out = SK.double_lap(lo, datum=0.0)
    if not hi.is_empty():
        out = out + scallop_rows(hi, 1.5, 1.9, d=0.42, shape="saw", datum=ZW - ZF, taper=0.6)
    return out


def _openings():
    L = []

    def add(x, y, v0, sp, name, kind="window"):
        e, u = MAIN.locate(x, y)
        L.append(Opening(MAIN, e, u, v0, sp, name, kind))

    def win(x, y, v0, w, h, name):
        add(x, y, v0, SF.window_commercial(w, h, rise=0, lites=(1, 1), rows=(1, 1), sill=1.2, head=None, casing=1.3,
                                           band=True), name)
        tr = SF.window_commercial(w, TR_H, rise=0, lites=(max(3, int(w / 1.8)), max(3, int(w / 1.8))), rows=(1, 1),
                                  sill=None, head="rosettes", casing=1.3)
        add(x, y, v0 + h + 1.6, tr, name + "-t")

    add(DOOR_X, 0.0, 0.0, SF.door_commercial(11.0, 30.0, transom=4.6, leaf="sunray", tstyle="beads", head=None),
        "front-door", "door")
    wx = (WX0 + WX1) / 2
    win(wx, WY, V1, 16.0, 19.0, "wing-1")
    win(wx, WY, V2, 13.0, 17.0, "wing-2")
    for x in (wx - 6.0, wx + 6.0):
        add(x, WY, ZW - ZF + 5.0, SF.window_commercial(6.4, 14.0, rise=0, lites=(1, 1), rows=(1, 2), sill=1.0, head=None,
                                                        casing=1.3, band=True), f"wing-gable-{x:.0f}")
    win(16.0, 0.0, V1, 8.4, 19.0, "F16")
    win(70.0, 0.0, V1, 8.4, 19.0, "F70")
    for x in (20.0, DOOR_X, 68.0):
        win(x, 0.0, V2, 8.4, 17.0, f"F{x:.0f}-2")
    win(WX0, WY / 2, V1, 7.2, 19.0, "WW")
    win(WX1, WY / 2, V2, 7.2, 17.0, "WE-2")
    for y in (30.0, 74.0, 118.0):
        win(0.0, y, V1, 8.4, 19.0, f"W{y:.0f}")
        win(W, y, V1, 8.4, 19.0, f"E{y:.0f}")
        win(0.0, y, V2, 8.4, 17.0, f"W{y:.0f}-2")
        win(W, y, V2, 8.4, 17.0, f"E{y:.0f}-2")
    add(140.0, D, 0.0, SF.door_commercial(10.0, 29.0, transom=4.4, leaf="sunray", tstyle="beads", head=None),
        "back-door", "door")
    for x in (30.0, 70.0, 108.0):
        win(x, D, V1, 8.4, 19.0, f"B{x:.0f}")
    for x in (30.0, 70.0, 108.0, 146.0):
        win(x, D, V2, 8.4, 17.0, f"B{x:.0f}-2")
    return L


OPENINGS = _openings()


def _roof_pieces():
    r = RAKE - D_EAVE
    return [([(0.0, 0.0), (W, 0.0), (W, D), (0.0, D)], [0, 1, 2, 3], S_MAIN),
            ([(WX0, WY - r), (WX1, WY - r), (WX1, 48.0), (WX0, 48.0)], [1, 3], S_WING)]


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    pieces = _roof_pieces()
    specs = [dict(p0=(WX0, WY), p1=(WX1, WY), slope=S_WING)]
    rf = G.gabled_roof(pieces, Z_EAVE, D_EAVE, specs, texture="notch", tex_kw=dict(pitch=1.5, wtab=2.2, d=0.42),
                       skin=SKIN, rake=RAKE, inner_cs=offset(MAIN.cs, -3.0), fascia=FASCIA, hollow=2.6)
    wl = rf["walls"][0]
    gables = [(MAIN, 2, wl["cs"].translate((0.0, Z_EAVE - ZF)))]
    undress = [slab(offset(MAIN.cs, 8.0), ZE - LEDGE - 0.6, ZW + 0.01)]
    st = stacked_shells(BLOCKS, OPENINGS, [S1], t=3.0, corners="rope", siding=_siding, gables=gables,
                        prof=CO.joint_profile(RJ, LEDGE), belt_blocks=None, water_table=False, undress=undress)
    no_lip = box([WX0 - 1.5, WY - 1, ZW - 1], [WX1 + 1.5, WY + 5.0, ZW + 5])
    lip = (_corbel(MAIN.cs, 3.0, ZW) + lip_ring(MAIN.cs, 3.0, ZW)) - no_lip
    kit.add("WALLS-1", "Butter", st["shells"][0], group="walls")
    kit.add("JOINT", "Butter", st["rings"][0], group="walls")
    kit.add("WALLS-2", "Butter", st["shells"][1] + lip + CO.ledge(PLAN, ZE, LEDGE), group="walls")
    for tag, path, z0, spec in (("J", st["outlines"][0], S1 + LEDGE + 0.4, JOINT), ("E", PLAN, ZE, EAVE)):
        rings, _ = CO.level(path, z0, spec)
        CO.add_level(kit, rings, f"CORNICE-{tag}", "cornice")
    fnd = foundation(BLOCKS, 0.0, ZF, style="pebble")
    kit.add("FOUNDATION", "Pebble", fnd, group="foundation")
    inserts = []
    for o in OPENINGS:
        A = o.local_frame()
        sp = o.spec
        b = sp["cut"].bounds()
        key = "DOOR" if o.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, "Windows_Doors", "Door" if o.kind == "door" else "Windows_Doors", "Glass")
        inserts.append(kit.add(f"{key}-{o.name}", "Windows_Doors", world, P=P,
                               key=f"{key}-{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}", group="inserts", render=zones))
    print("walls + inserts", round(time.time() - t0, 1))

    # --- the roof: a hollow notched-shingle hip, cut flat on top, with the wing's gable
    roof = rf["body"] + rf["tex"] + rf["skins"] + rf["skin_tex"]
    solid_env, _ = R.hip_roof(pieces, Z_EAVE, S_MAIN, D_EAVE, texture=None, zlo=ZW)
    flat_cs = solid_env.slice(Z_FLAT)
    # the flat top's deck, carried on a 45 degree inverted hip filling the hollow under it
    # (so the deck is no bridge when the roof prints upright)
    fb0 = flat_cs.bounds()
    inset = min(fb0[2] - fb0[0], fb0[3] - fb0[1]) / 2          # down to a ridge line: no flat underside
    under = M.hull_points([(x, y, Z_FLAT) for x in (fb0[0], fb0[2]) for y in (fb0[1], fb0[3])] +
                          [(x, y, Z_FLAT - inset) for x in (fb0[0] + inset, fb0[2] - inset) for y in (fb0[1] + inset, fb0[3] - inset)])
    roof = roof.trim_by_plane([0, 0, -1.0], -Z_FLAT) + slab(flat_cs, Z_FLAT - 1.6, Z_FLAT) + (under ^ solid_env)
    zc = Z_EAVE + S_WING * ((WX1 - WX0) / 2 + D_EAVE)
    xm = (WX0 + WX1) / 2
    y_meet = (zc - Z_EAVE) / S_MAIN - D_EAVE + 1.0
    walls_env = wl["facade"].place(M.extrude(wl["cs"].offset(0.15), RAKE + 4.2).translate([0, 0, -3.15]))
    cap = G.ridge_cap((xm, WY - RAKE), (xm, y_meet), zc, S_WING, ZW) - walls_env
    fb = flat_cs.bounds()
    corners = [(-D_EAVE, -D_EAVE), (W + D_EAVE, -D_EAVE), (W + D_EAVE, D + D_EAVE), (-D_EAVE, D + D_EAVE)]
    ends = [(fb[0], fb[1]), (fb[2], fb[1]), (fb[2], fb[3]), (fb[0], fb[3])]
    hips = union([G.hip_cap((c[0], c[1], Z_EAVE), (e[0], e[1], Z_FLAT), half=1.6, up=0.9, drop=2.2)
                  for c, e in zip(corners, ends)])
    roof = roof + cap + hips.trim_by_plane([0, 0, -1.0], -Z_FLAT)
    roof = roof - lip_keep(MAIN.cs, 3.0, ZW)
    CH = 12.0
    cx, cy = W - 26.0, 96.0
    z_roof = Z_EAVE + S_MAIN * (W + D_EAVE - (cx + CH / 2))
    z0 = round((z_roof - 3.0) / 0.2) * 0.2
    pocket = box([cx - CH / 2 - 0.4, cy - CH / 2 - 0.4, z0], [cx + CH / 2 + 0.4, cy + CH / 2 + 0.4, Z_FLAT + 60])
    roof = roof + G.chimney_seat(solid_env, cx, cy, CH / 2, Z_FLAT) - pocket
    roof = roof.trim_by_plane([0, 0, 1.0], ZW)          # the hip caps' drops end at the base: a flat first layer
    kit.add("ROOF", "Roof", roof, group="roof")
    ch = TW.chimney("crowned", w=CH, d=CH * 0.75, h=round((Z_FLAT + 16.0 - z0) / 0.2) * 0.2).translate([cx, cy, z0])
    kit.add("CHIMNEY", "Brick", ch, group="roof")
    # the widow's walk round the flat top: four strips standing on the deck's edge
    for k in range(4):
        a, b = (fb[0], fb[1]), (fb[2], fb[1])
        if k == 1:
            a, b = (fb[2], fb[1]), (fb[2], fb[3])
        elif k == 2:
            a, b = (fb[2], fb[3]), (fb[0], fb[3])
        elif k == 3:
            a, b = (fb[0], fb[3]), (fb[0], fb[1])
        a, b = np.array(a), np.array(b)
        L_ = float(np.linalg.norm(b - a))
        dvec = (b - a) / L_
        n = np.array([dvec[1], -dvec[0]])
        o = a + n * (-0.6) - dvec * 0.0
        Aw = np.array([[dvec[0], 0.0, n[0], o[0]], [dvec[1], 0.0, n[1], o[1]], [0.0, 1.0, 0.0, Z_FLAT]])
        rail = R.walk_rail(L_ - 1.4 if k % 2 else L_, h=4.4).translate([0.7 if k % 2 else 0.0, 0, 0])
        kit.add(f"WALK-{k}", "Olive", rail.transform(Aw), P=inv34(Aw), key=f"WALK-{k % 2}", group="roof")
    # the Eastlake gable ornament on the wing, ladder brackets under its eave returns
    bb = G.gable_eastlake(wl["L"], wl["slope"], D_EAVE, skin=SKIN)
    f = wl["facade"]
    A = f.A.copy()
    A[:, 3] = f.world(0.0, 0.0, RAKE)
    ow = bb.transform(A) - roof                                # the ornament's feet stop on the main roof
    kit.add("GABLE-ornament", "Olive", max(ow.decompose(), key=lambda m_: m_.volume()), P=inv34(A), group="roof")
    print("roof", round(time.time() - t0, 1))

    # --- the porch: across the front, round the corner in three facets, down the west side
    C, RC = np.array([12.0, 8.0]), 46.0
    PW = C[0] - RC                                  # the porch's west edge
    arc = [tuple(C + RC * np.array([math.cos(a), math.sin(a)])) for a in np.radians([180, 210, 240, 270])]
    ppoly = [(PW, 60.0)] + arc + [(WX0, WY), (WX0, 0.0), (0.0, 0.0), (0.0, 60.0)]
    c30 = 1.6 * math.tan(math.radians(15))
    Lseg = 2 * RC * math.sin(math.radians(15))
    Lw = 60.0 - arc[0][1]
    Lf = WX0 - arc[3][0]
    ud = DOOR_X - arc[3][0]
    runs = [dict(a=(0.0, 60.0), b=(PW, 60.0), posts=[3.2, -PW - 1.6]),
            dict(a=(PW, 60.0), b=arc[0], posts=[1.6, Lw / 2, Lw - c30]),
            dict(a=arc[0], b=arc[1], posts=[c30, Lseg - c30]),
            dict(a=arc[1], b=arc[2], posts=[c30, Lseg - c30]),
            dict(a=arc[2], b=arc[3], posts=[c30, Lseg - c30]),
            dict(a=arc[3], b=(WX0, WY), posts=[c30, ud - 11.0, ud + 11.0, Lf - 3.4])]
    H_floor = ZF - 1.4
    post_h = S1 - 2.0 - 5.6 - H_floor          # the porch roof tucks under the flared skirt
    P = FT.porch_turned(ppoly, runs, H_floor, post_h, steps_at=[(5, ud, 16.0)],
                        planks=dict(pitch=1.6, border=1.4), joined=True, ledger_off=1.5, post="bobbin", rail="bead",
                        arcade="rosette", skirt="shingles", pier_tex="pebble", roof_edge="beadreel", top=True)
    fkeep = slab(offset(MAIN.cs, 0.8 + 0.55 + 0.15), -1, ZF + 1.3)
    ins_keep = union([box(np.array(p.solid.bounding_box()[:3]) - 0.2, np.array(p.solid.bounding_box()[3:]) + 0.2)
                      for p in inserts if p is not None])
    deck = P["deck"] - fkeep
    kit.add("PORCH-deck", "PorchDeck", deck, P=print_flip(), group="porch",
            render=FT.plank_zones(deck, H_floor, "Planks", "PorchDeck"))
    bld_keep = MAIN.solid(grow=1.8, dz0=-20, dz1=0)
    ptop = FT.add_porch_top(kit, "PORCH", P, bld_keep + ins_keep + fnd,
                            "Olive", "Olive", tin_col="Roof")["ptop"]
    for k, (sm, A) in enumerate(P["steps"]):
        kit.add(f"PORCH-steps-{k}", "Pebble", sm.transform(A) - fkeep, group="porch")
    ped = FT.entry_pediment(18.0, 3.4, 8.8)
    Ap = np.array([[-1.0, 0, 0, DOOR_X], [0, -1.0, 0, WY - 1.4 + 3.0], [0, 0, 1.0, ptop]])
    kit.add("PORCH-pediment", "Olive", ped.transform(Ap), P=inv34(Ap), group="porch")
    e, u = MAIN.locate(140.0, D)
    fbk = MAIN.facades()[e]
    A = fbk.A.copy()
    A[:, 3] = fbk.world(u, -ZF, 1.4)
    kit.add("STOOP-back", "Pebble", FT.steps(14.0, ZF - 0.6, 5).transform(A), group="porch")
    print("porch", round(time.time() - t0, 1))
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "primrose")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:40]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "primrose.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))

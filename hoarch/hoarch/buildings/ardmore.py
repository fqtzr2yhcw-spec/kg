"""The Ardmore -- an original HO-scale (1:87.1) Richardsonian Romanesque house for the lineup. Rev B:
the house-size plan (176 x 116 mm, storeys of 42 and 38 mm) and built-up cornices at every level.

Two and a half storeys of rock-faced brownstone on a base of tall boulder courses. A round
(twelve-sided) tower at the front corner rises a storey above the eaves to an arcaded
belvedere and a steep conical clay-tile roof with a stacked finial. The entrance is a stone
loggia with a great round arch; inside it a round-arched doorway of receding orders with
iron-studded doors. Round-arched windows (three-over-one sash) ring their heads with long
voussoirs on squat colonnettes with cushion capitals: singles, an arcaded triple, and paired
square-headed lights under a heavy lintel. A steep hipped clay-tile roof with a front gable and
rock-faced stone chimneys under gabled copings.

- Between the storeys a three-part cornice: a buff frieze of interlaced round arches, a
  terracotta billet course and a buff bevel crown.
- At the eave (round the house and the tower): the arched corbel table as a buff frieze of
  little round arches hung on corbels, a terracotta dog-tooth course and a stepped buff crown.
- Round the tower's top: a terracotta frieze of nailheads, a buff bead-and-reel course and a
  buff ovolo crown under the cone.

usage: python3 -m hoarch.buildings.ardmore [check] [export]
"""
import math
import os
import sys
import time

from manifold3d import Manifold as M

from hoarch.core import ashlar, box, cs_union, inv34, ngon, offset, poly, rect, slab, union
from hoarch import cornice as CO, features as FT, gables as G, openings as O, roof as R, trimwork as TW
from hoarch.kit import Kit, print_flip
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, stacked_shells

NAME = "Ardmore Richardsonian Romanesque"
COLORS = {"Sandstone": "#9A6248", "Buff": "#D8C8A4", "Tile": "#44584B", "Granite": "#7E7C78", "Brick": "#8A3B2B",
          "Terracotta": "#B0603A", "Windows_Doors": "#EDE3C8"}
RENDER_MAT = {"Sandstone": "stone_wall", "Buff": "trim", "Tile": "roof", "Granite": "stone", "Brick": "brick",
              "Terracotta": "accent", "Windows_Doors": "trim", "Sash": "sash", "Door": "door", "Glass": "glass"}
PALETTE = {"stone_wall": ["#9A6248", 0.85, 0.0], "trim": ["#D8C8A4", 0.7, 0.0], "roof": ["#44584B", 0.6, 0.0],
           "stone": ["#7E7C78", 0.9, 0.0], "brick": ["#8A3B2B", 0.85, 0.0], "sash": ["#2F3A2E", 0.45, 0.0],
           "door": ["#4A2616", 0.45, 0.0], "accent": ["#B0603A", 0.7, 0.0]}

# ------------------------------------------------------------------ cornices (unique to the Ardmore)
LEDGE = 1.4
JOINT = dict(pitch=12.0, margin=4.0, layers=[
    dict(kind="frieze", h=4.8, b=1.2, orn="interlace", role="Buff"),
    dict(kind="course", h=1.6, b=1.4, orn="billet", role="Terracotta"),
    dict(kind="crown", h=2.0, b=1.4, P=3.6, orn="bevel", role="Buff")])
EAVE = dict(pitch=12.0, margin=4.0, layers=[
    dict(kind="frieze", h=5.8, b=1.2, orn="corbel_arches", role="Buff"),
    dict(kind="course", h=1.6, b=1.4, orn="dogtooth", role="Terracotta"),
    dict(kind="crown", h=2.6, b=1.4, P=4.6, orn="stepped", role="Buff")])
TOWER_C = dict(pitch=9.0, margin=2.6, layers=[
    dict(kind="frieze", h=4.4, b=1.2, orn="nailhead", role="Terracotta"),
    dict(kind="course", h=1.4, b=1.4, orn="beadreel", role="Buff"),
    dict(kind="crown", h=2.2, b=1.4, P=4.4, orn="ovolo", role="Buff")])
RJ = round((LEDGE + 0.4 + CO.band_height(JOINT)) / 0.2) * 0.2
HE = CO.band_height(EAVE)

# ------------------------------------------------------------------ levels (on the 0.2 mm grid)
ZF = 14.0
S1 = ZF + 42.0
ZE = S1 + RJ + 38.0
ZW = ZE + HE                     # the wall top behind the eave cornice; the roof sits here
ZT = ZW + 40.0                   # the tower's ledge: its cornice and cone clear the main roof
ZTW = ZT + CO.band_height(TOWER_C)
FASCIA = 2.4
Z_EAVE = ZW + FASCIA
D_EAVE, RAKE, SKIN = 5.0, 5.6, 1.8
S_MAIN, S_CROSS = 1.1, 1.5
PZ = ZF + 33.0                   # entrance loggia top
V1 = 8.0
V2 = S1 + RJ + 5.0 - ZF

# ------------------------------------------------------------------ plan
W, D = 176.0, 116.0
GX0, GX1 = 128.0, 170.0          # front gable
TC, TAPO = (26.0, 4.0), 26.0     # the round tower
MAIN = Block("main", [(0, 0), (W, 0), (W, D), (0, D)], ZF, ZW)
TOWER = Block("tower", ngon(TC, TAPO, n=12), ZF, ZTW)
PX0, PX1, PD = 64.0, 122.0, 22.0
PORCH = Block("porch", [(PX0, -PD), (PX1, -PD), (PX1, 3.0), (PX0, 3.0)], ZF, PZ)
BLOCKS = [MAIN, TOWER, PORCH]


def _roof_z(x, y):
    """Height of the main hip roof's top at plan (x, y) (None outside its eave)."""
    d = min(x + D_EAVE, W + D_EAVE - x, y + D_EAVE, D + D_EAVE - y)
    return None if d < 0 else Z_EAVE + S_MAIN * d


def _siding(f, b, reg):
    """Rock-faced brownstone; nothing in the cornice bands (the corbel table is the eave
    cornice's frieze now)."""
    seed = sum(map(ord, b.name)) + int(f.p0[0] * 7 + f.p0[1] * 3) % 1000
    if b is not PORCH:
        reg = reg - rect(-1, ZE - b.z0, f.L + 1, ZW - b.z0)
        if b is TOWER:
            reg = reg - rect(-1, ZT - b.z0, f.L + 1, 999)
    return ashlar(reg, course=(2.6, 4.2), length=(4.0, 9.0), d=0.55, seed=seed)


def _outside(p, blk, margin):
    return (blk.cs ^ rect(p[0] - margin, p[1] - margin, p[0] + margin, p[1] + margin)).is_empty()


def _openings():
    L = []
    s31 = dict(lites=(1, 3))                    # three-over-one sash
    lo = O.window_romanesque(9.6, 25.0, **s31)
    up = O.window_romanesque(9.2, 22.0, **s31)
    tri = O.window_romanesque(7.2, 21.0, n=3)
    pair = O.window_romanesque(8.4, 21.0, n=2, flat=True, **s31)
    gab = O.window_romanesque(6.8, 16.0, col=1.0, L=2.0)
    tw = O.window_romanesque(6.0, 20.0, col=0.9, L=1.8, hood=False, sill_ext=0.4)
    bel = O.window_romanesque(6.0, 14.0, col=0.9, L=1.6, hood=False, sill_ext=0.4)
    portal = O.door_romanesque(22.0, 29.0, plug=False, orders=1)
    door = O.door_romanesque(13.0, 28.0, orders=1)
    back_door = O.door_romanesque(11.0, 26.0, orders=1, leaves=1, L=2.4)

    def add(blk, x, y, v0, sp, name, kind="window"):
        e, u = blk.locate(x, y)
        L.append(Opening(blk, e, u, v0, sp, name, kind))

    add(PORCH, (PX0 + PX1) / 2, -PD, 0.0, portal, "portal", "portal")
    add(MAIN, (PX0 + PX1) / 2, 0.0, 0.4, door, "front-door", "door")
    xm = (GX0 + GX1) / 2
    add(MAIN, xm, 0.0, V1, tri, "front-tri")
    add(MAIN, xm, 0.0, V2, pair, "front-pair")
    add(MAIN, xm, 0.0, ZW - ZF + 3.0, gab, "gable")
    add(MAIN, (PX0 + PX1) / 2, 0.0, V2, up, "front-up")
    for y in (58.0, 92.0):
        add(MAIN, 0.0, y, V1, lo, f"west-{int(y)}-1")
        add(MAIN, 0.0, y, V2, up, f"west-{int(y)}-2")
    for y in (28.0, 86.0):
        add(MAIN, W, y, V1, lo, f"east-{int(y)}-1")
        add(MAIN, W, y, V2, up, f"east-{int(y)}-2")
    add(MAIN, 128.0, D, 0.4, back_door, "back-door", "door")
    for x in (36.0, 82.0, W - 20.0):
        add(MAIN, x, D, V1, lo, f"back-{int(x)}-1")
    for x in (36.0, 82.0, 128.0, W - 20.0):
        add(MAIN, x, D, V2, up, f"back-{int(x)}-2")
    # the tower: windows on its outside faces, an arcaded belvedere above the roof
    for k, f in enumerate(TOWER.facades()):         # lights on every other face only
        if k % 2:
            continue
        m = (f.p0 + f.p1) / 2
        mo = m + f.n * 3.0
        if _outside(mo, MAIN, 3.5) and _outside(mo, PORCH, 3.5):
            add(TOWER, m[0], m[1], V1 + 2.0, tw, f"tower-{k}-1")
            add(TOWER, m[0], m[1], V2 + 1.0, tw, f"tower-{k}-2")
        zr = _roof_z(*(m + f.n * 2.0))
        if zr is None or zr < ZT - 22.0 - 2.0:
            add(TOWER, m[0], m[1], ZT - ZF - 22.0, bel, f"tower-{k}-3")
    return L


OPENINGS = _openings()


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    pieces = [(MAIN.pts, [0, 1, 2, 3], S_MAIN),
              ([(GX0, -(RAKE - D_EAVE)), (GX1, -(RAKE - D_EAVE)), (GX1, 30.0), (GX0, 30.0)], [1, 3], S_CROSS)]
    specs = [dict(p0=(GX0, 0.0), p1=(GX1, 0.0), slope=S_CROSS, e=0.3)]
    rf = G.gabled_roof(pieces, Z_EAVE, D_EAVE, specs, texture="tile", tex_kw=dict(pitch=2.2, seam_pitch=2.6, d=0.45),
                       skin=SKIN, rake=RAKE, inner_cs=offset(MAIN.cs, -3.0), fascia=FASCIA, hollow=2.6)
    wl = rf["walls"][0]
    gables = [(MAIN, 0, wl["cs"].translate((GX0, Z_EAVE - ZF)))]
    wall_ops = [o for o in OPENINGS if o.kind != "portal"] + [o for o in OPENINGS if o.kind == "portal"]
    # one joint only: above it the upper walls, the front gable and the whole tower are one
    # upright piece (the gable wall stays joined to the storey below it)
    eave_cs = cs_union([MAIN.cs, TOWER.cs])
    eave_path = max(eave_cs.to_polygons(), key=lambda L_: abs(poly(L_).area()))
    undress = [slab(offset(eave_cs, 8.0), ZE - LEDGE - 0.6, ZW + 0.01),
               slab(offset(TOWER.cs, 8.0), ZT - LEDGE - 0.6, ZTW + 0.01)]
    st = stacked_shells(BLOCKS, wall_ops, [S1], t=3.0, corners="none", siding=_siding, gables=gables,
                        water_table=True, prof=CO.joint_profile(RJ, LEDGE), belt_blocks=None, undress=undress)
    kit.add("WALLS-1", "Sandstone", st["shells"][0], group="walls")
    kit.add("JOINT", "Sandstone", st["rings"][0], group="walls")
    tower_keep = TOWER.solid(grow=0.2, dz0=-1, dz1=1)
    no_lip = union([box([GX0 - D_EAVE - 0.6, -1, ZW - 1], [GX1 + D_EAVE + 0.6, 5.0, ZW + 5]), tower_keep,
                    slab(offset(TOWER.cs, 1.0), ZW - 1, ZW + 5)])
    lip = (_corbel(MAIN.cs, 3.0, ZW) + lip_ring(MAIN.cs, 3.0, ZW)) - no_lip
    # carry the tower's wall down through the main house's upper storey, so its top storey
    # stands on wall rather than hanging over the rooms
    base = cs_union([MAIN.cs, TOWER.cs])
    tring = slab((offset(TOWER.cs, -0.05) - offset(TOWER.cs, -3.0)) ^ offset(MAIN.cs, -3.05), S1 + RJ, ZW + 1.2)
    tring = tring - lip_keep(base, 3.0, S1 + RJ)
    ledges = CO.ledge(eave_path, ZE, LEDGE) + CO.ledge(TOWER.pts, ZT, LEDGE)
    tlip = _corbel(TOWER.cs, 3.0, ZTW) + lip_ring(TOWER.cs, 3.0, ZTW)
    kit.add("WALLS-2", "Sandstone", st["shells"][1] + lip + tring + ledges + tlip, group="walls")
    rings, _ = CO.level(st["outlines"][0], S1 + LEDGE + 0.4, JOINT)
    CO.add_level(kit, rings, "CORNICE-J", "cornice")
    # the eave's rings wrap the tower: parted where they meet it and halved round it (to fit)
    cut = CO.blades(CO.tower_cuts(eave_path, TC, TAPO + 8.0, wall=TAPO, away=(-1.0, -1.0), tower=TOWER.pts,
                                   house=MAIN.pts), ZE, ZW)
    rings, _ = CO.level(eave_path, ZE, EAVE, cut=cut)
    CO.add_level(kit, rings, "CORNICE-E", "cornice")
    kit.add("FOUNDATION", "Granite", foundation(BLOCKS, 0.0, ZF, style="boulder"), group="foundation")
    inserts = []
    for o in OPENINGS:
        A = o.local_frame()
        sp = o.spec
        b = sp["cut"].bounds()
        tag = f"{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}"
        if o.kind == "portal":
            B = A.copy()
            kit.add("PORTAL", "Buff", sp["insert"].transform(B), P=inv34(B), group="porch")
            continue
        key = "DOOR" if o.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, "Buff", "Door" if o.kind == "door" else "Sash", "Glass")
        inserts.append(kit.add(f"{key}-{o.name}", "Windows_Doors", world, P=P, key=f"{key}-{tag}",
                               group="inserts", render=zones))
    print("walls + inserts", round(time.time() - t0, 1))

    # --- main roof: hollow hip with the front gable, cut round the tower and its belt
    roof = rf["body"] + rf["tex"] + rf["skins"] + rf["skin_tex"]
    zr = Z_EAVE + S_MAIN * (D / 2 + D_EAVE)
    zc = Z_EAVE + S_CROSS * ((GX1 - GX0) / 2 + D_EAVE)
    xm = (GX0 + GX1) / 2
    y_meet = (zc - Z_EAVE) / S_MAIN - D_EAVE + 1.0
    caps = union([G.ridge_cap((D / 2, D / 2), (W - D / 2, D / 2), zr, S_MAIN, ZW),
                  G.ridge_cap((xm, -RAKE), (xm, y_meet), zc, S_CROSS, ZW)])
    walls_env = wl["facade"].place(M.extrude(wl["cs"].offset(0.15), 4.2).translate([0, 0, -3.15]))   # and its stonework
    # hip caps from the eave corners up to the ridge ends
    corners = [(-D_EAVE, -D_EAVE), (W + D_EAVE, -D_EAVE), (W + D_EAVE, D + D_EAVE), (-D_EAVE, D + D_EAVE)]
    ends = [(D / 2, D / 2), (W - D / 2, D / 2), (W - D / 2, D / 2), (D / 2, D / 2)]
    hips = union([G.hip_cap((c[0], c[1], Z_EAVE), (e[0], e[1], zr), half=1.3, up=0.7, drop=1.8)
                  for c, e in zip(corners, ends)])
    roof = roof + ((caps + hips) - walls_env)
    roof = roof.trim_by_plane([0, 0, 1.0], ZW) - lip_keep(MAIN.cs, 3.0, ZW)
    CH = 11.0
    chims = [(76.0, D / 2), (104.0, D / 2)]
    z_low = zr - S_MAIN * (CH / 2) - 0.2
    z0 = round((z_low - 2.4) / 0.2) * 0.2
    solid_env, _ = R.hip_roof(pieces, Z_EAVE, S_MAIN, D_EAVE, texture=None, zlo=ZW)
    for (x, y) in chims:
        roof = roof + G.chimney_seat(solid_env, x, y, CH / 2, zr + 1.0)
    g = CH / 2 + 0.9                         # clear of the chimney's rock-faced stones
    pockets = union([box([x - g, y - g, z0], [x + g, y + g, zr + 40]) for x, y in chims])
    roof = roof - pockets - slab(offset(TOWER.cs, 1.4), ZW - 1, ZTW + 90)
    kit.add("ROOF", "Tile", roof, group="roof")
    for k, (x, y) in enumerate(chims):
        ch = TW.chimney("stone", w=CH, d=CH, h=round((zr + 18.0 - z0) / 0.2) * 0.2).translate([x, y, z0])
        kit.add(f"CHIMNEY-{k}", "Sandstone", ch, key="CHIMNEY", group="roof")
    print("roof", round(time.time() - t0, 1))

    # --- the tower's cornice (cut back where the main roof climbs past it) and conical roof
    t_env, _ = R.hip_roof(pieces, Z_EAVE + 1.4, S_MAIN, D_EAVE + 1.4, texture=None, zlo=ZW)
    rings, _ = CO.level(TOWER.pts, ZT, TOWER_C, cut=t_env)
    CO.add_level(kit, rings, "CORNICE-T", "tower")
    tpts = TOWER.pts
    dt = TOWER_C["layers"][-1]["P"] + 0.6
    zc0 = ZTW + 1.4
    cone, ctex = R.hip_roof([(tpts, list(range(12)))], zc0, 2.4, dt, texture="tile",
                            tex_kw=dict(pitch=2.2, seam_pitch=2.6, d=0.5), zlo=ZTW)     # steep: deeper relief reads
    inner, _ = R.hip_roof([(tpts, list(range(12)))], zc0 - 2.4 * math.sqrt(1 + 2.4 ** 2), 2.4, dt, texture=None)
    cone = (cone + ctex) - (inner ^ slab(offset(TOWER.cs, -3.2), ZTW - 1, zc0 + 300)) - lip_keep(TOWER.cs, 3.0, ZTW)
    rr = TAPO + dt
    zseat = round((zc0 + 2.4 * rr - 2.0) / 0.2) * 0.2
    seat = M.cylinder(1.2, 1.35, 1.35, 32).translate([TC[0], TC[1], zseat - 0.4])
    re = (TAPO + dt) / math.cos(math.pi / 12)
    zap = zc0 + 2.4 * (TAPO + dt)
    tips = [(TC[0] + re * math.cos(-math.pi / 2 + math.pi / 12 + 2 * math.pi * k / 12),
             TC[1] + re * math.sin(-math.pi / 2 + math.pi / 12 + 2 * math.pi * k / 12)) for k in range(12)]
    hipc = union([G.hip_cap((x, y, zc0), (TC[0], TC[1], zap), half=0.9, up=0.5, drop=1.4) for x, y in tips])
    cone = cone + hipc.trim_by_plane([0, 0, 1.0], zc0 + 0.2)
    cone = cone.trim_by_plane([0, 0, -1.0], -zseat) - seat
    kit.add("TOWER-roof", "Tile", cone, group="tower")
    kit.add("TOWER-finial", "Tile", TW.finial("stack", 1.6, 13.0).translate([TC[0], TC[1], zseat - 0.4]), group="tower")
    print("tower", round(time.time() - t0, 1))

    # --- the entrance loggia: a paved floor, a stone deck with a parapet, steps
    inner_p = offset(PORCH.cs, -3.0) - offset(MAIN.cs, 0.0)
    fnd = foundation(BLOCKS, 0.0, ZF, style="boulder")
    kit.add("PORCH-floor", "Granite", slab(inner_p.offset(-0.15), 0.0, ZF) - fnd, group="porch")
    deck_cs = PORCH.cs.offset(0.8) - MAIN.cs
    deck = slab(deck_cs, PZ, PZ + 1.6) + slab(offset(PORCH.cs, -3.15) - offset(MAIN.cs, 0.15), PZ - 1.2, PZ + 0.01)
    walls_lo = st["shells"][0] + st["rings"][0] + st["shells"][1] + union([p.solid for p in kit.parts
                                                                             if p.name.startswith("CORNICE-J")])
    # the portal's arch and the front door's head rise into the deck and parapet: clear them
    arches = union([p.solid for p in kit.parts if p.name in ("PORTAL", "DOOR-front-door")])
    walls_lo = walls_lo + union([arches.translate(v) for v in
                                 ((0.2, 0, 0), (-0.2, 0, 0), (0, 0.2, 0), (0, -0.2, 0), (0, 0, 0.2), (0, 0, -0.2))])
    kit.add("PORCH-deck", "Buff", deck - walls_lo, P=print_flip(), group="porch")
    par_out = PORCH.cs.offset(0.4) - MAIN.cs.offset(0.15)
    par = slab(par_out - PORCH.cs.offset(-1.4), PZ + 1.6, PZ + 6.0)
    cope = slab(par_out.offset(0.4) - PORCH.cs.offset(-1.8) - MAIN.cs.offset(0.15), PZ + 6.0, PZ + 7.0)
    piers = union([box([x - 2.0, y - 2.0, PZ + 1.6], [x + 2.0, y + 2.0, PZ + 8.2])
                   for x, y in ((PX0 + 1.6, -PD + 1.6), (PX1 - 1.6, -PD + 1.6))])
    kit.add("PORCH-parapet", "Buff", (par + cope + piers) - walls_lo, group="porch")
    e, u = PORCH.locate((PX0 + PX1) / 2, -PD)
    f = PORCH.facades()[e]
    A = f.A.copy()
    A[:, 3] = f.world(u, -ZF, 2.0)                     # clear of the boulder courses
    kit.add("STEPS-front", "Granite", FT.steps(26.0, ZF - 0.6, 5, cheek=2.0).transform(A), group="porch")
    e, u = MAIN.locate(128.0, D)
    f = MAIN.facades()[e]
    A = f.A.copy()
    A[:, 3] = f.world(u, -ZF, 2.0)                     # clear of the boulder courses
    kit.add("STEPS-back", "Granite", FT.steps(15.0, ZF - 0.6, 5).transform(A), group="porch")
    print("porch", round(time.time() - t0, 1))
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "ardmore")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:40]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "ardmore.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))

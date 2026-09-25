"""The Wisteria -- an original HO-scale (1:87.1) storey-and-a-half cottage, combining the
user's gingerbread-cottage photo with the round-cornered porch of the butter-yellow house.

Wisteria-lavender wide-and-narrow lap siding with blocked corner boards on a base of rounded
river stones; a steep side-gabled roof of clipped-corner shingles in moss green, a front
cross-gabled wing on the east, two hipped dormers on the front slope and a brick chimney
that flares to a tulip crown. Each gable carries split shingles in its field and a crescent
gable ornament: raking boards, a crescent arch with turned drops, a pierced diamond in the
apex and a spike. A porch runs across the front and round the west corner in a true curve,
on octagonal posts with heart-pierced railings, plum wisteria clusters hanging from the
frieze, an arcaded fascia and a skirt of X-braced panels on river-stone piers. Windows with Y
tracery in the upper sash under little boarded gablets; doors with a tall hexagonal light
under a lozenge transom.

usage: python3 -m hoarch.buildings.wisteria [check] [export]
"""
import math
import os
import sys
import time

import numpy as np
from manifold3d import JoinType, Manifold as M

from hoarch.core import box, compose, cs_union, inv34, offset, poly, rect, scallop_rows, slab, union
from hoarch import features as FT, gables as G, openings as O, roof as R, skins as SK, storefront as SF, trimwork as TW
from hoarch.kit import Kit, print_flip
from hoarch.ornament import ext
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, wall_shell

NAME = "The Wisteria"
COLORS = {"Wisteria": "#A596CF", "Cream": "#F2EBDA", "Plum": "#5C2C4E", "Moss": "#5F6B52", "River": "#8D8A83",
          "Brick": "#8E3F31", "PorchDeck": "#8D8A83", "Windows_Doors": "#F2EBDA"}
RENDER_MAT = {"Wisteria": "siding", "Cream": "trim", "Plum": "plum", "Moss": "roof", "River": "stone",
              "Brick": "brick", "PorchDeck": "stone", "Planks": "planks", "Windows_Doors": "trim", "Sash": "sash",
              "Door": "door", "Glass": "glass"}

# ------------------------------------------------------------------ levels (on the 0.2 mm grid)
ZF = 8.0
ZE = ZF + 34.0                  # wall top: the roof sits here
FASCIA = 1.8
Z_EAVE = ZE + FASCIA
D_EAVE, RAKE, SKIN = 3.0, 3.2, 1.8
S_MAIN, S_WING = 1.3, 1.45
V1 = 6.0

# ------------------------------------------------------------------ plan
W, D = 100.0, 56.0
WX0, WX1, WY = 58.0, 94.0, -14.0          # the front cross-gabled wing
MAIN = Block("main", [(0, 0), (W, 0), (W, D), (0, D)], ZF, ZE)
WING = Block("wing", [(WX0, WY), (WX1, WY), (WX1, 3.0), (WX0, 3.0)], ZF, ZE)
BLOCKS = [MAIN, WING]
DOOR_X = 30.0
DORMERS = (16.0, 40.0)                    # the hipped dormers' centres on the front slope
DW, DDEP, DHW = 11.0, 14.0, 7.0


def _siding(f, b, reg):
    """Wide-and-narrow lap siding on the walls; split shingles in the gable fields."""
    cut = ZE - b.z0
    out = []
    lo = reg ^ rect(-1, -100, f.L + 1, cut)
    hi = reg ^ rect(-1, cut, f.L + 1, 999)
    if not lo.is_empty():
        out.append(SK.alternating_lap(lo, datum=0.0))
    if not hi.is_empty():
        out.append(scallop_rows(hi, 1.6, 2.2, d=0.42, datum=cut + 0.4, shape="slot", lap=2.0))
    return union(out) if out else M()


def _openings():
    L = []

    def win(w, h, rise=0, head="gablet"):
        return SF.window_commercial(w, h, rise=rise, lites=(1, 1), rows=(1, 1), sill=1.0, head=head, upper="ytracery")

    def add(blk, x, y, v0, sp, name, kind="window"):
        e, u = blk.locate(x, y)
        L.append(Opening(blk, e, u, v0, sp, name, kind))

    door = lambda w, h: SF.door_commercial(w, h, transom=4.2, leaf="hexlight", tstyle="lozenge", head=None, leaves=1)
    add(MAIN, DOOR_X, 0.0, 0.0, door(9.0, 25.0), "door", "door")
    for x in (13.0, 47.0):
        add(MAIN, x, 0.0, V1, win(7.2, 19.0), f"F{x:.0f}")
    wm = (WX0 + WX1) / 2
    add(WING, wm, WY, V1, win(10.0, 19.0), "wing")
    add(WING, wm, WY, ZE - ZF + 3.0, win(6.0, 11.0, head=None), "wing-gable")
    add(WING, WX1, WY / 2, V1, win(5.6, 17.0), "wing-east")
    add(WING, WX0, WY / 2, V1, win(5.6, 17.0), "wing-west")
    for y in (14.0, 44.0):
        add(MAIN, 0.0, y, V1, win(7.2, 19.0), f"W{y:.0f}")
        add(MAIN, W, y, V1, win(7.2, 19.0), f"E{y:.0f}")
    add(MAIN, W, 28.0, V1, win(7.2, 19.0), "E28")
    for x0 in (0.0, W):
        add(MAIN, x0, D / 2, ZE - ZF + 6.0, win(6.4, 13.0, head=None), f"gable{x0:.0f}")
    add(MAIN, 70.0, D, 0.0, door(8.0, 24.0), "back-door", "door")
    for x in (14.0, 34.0, 52.0, 86.0):
        add(MAIN, x, D, V1, win(7.2, 19.0), f"B{x:.0f}")
    return L


OPENINGS = _openings()


def dormer_hipped(w=DW, dep=DDEP, hwall=DHW):
    """A hipped dormer's body: a box with a flat bottom (it drops into a pocket in the roof and
    sits on a seat), its front wall 1.2 thick carrying a pair of round-headed lights over a
    dark core, a sill board and corner boards. Local: u across (centred), v up from its foot,
    w out (the face at w = 0). Returns (body, core)."""
    body = box([-w / 2, 0.0, -dep], [w / 2, hwall, 0.0]) - box([-w / 2 + 1.2, 1.2, -dep - 1], [w / 2 - 1.2, hwall + 1, -1.2])
    from hoarch.core import arch_cs
    lights = cs_union([arch_cs(u - 1.6, u + 1.6, 1.8, hwall - 2.8, seg=20) for u in (-2.2, 2.2)])
    body = body - ext(lights, -1.3, 1.0)
    body = body + ext(rect(-w / 2 + 0.6, 1.0, w / 2 - 0.6, 1.6), -0.01, 0.8)                  # sill
    for sg in (-1, 1):
        body = body + ext(rect(sg * w / 2 - 0.7, 0.0, sg * w / 2 + 0.7, hwall), -0.01, 0.4) ^ box([-w / 2 - 0.05, -1, -1], [w / 2 + 0.05, 99, 1])
    core = box([-w / 2 + 1.2, 1.2, -dep + 1.2], [w / 2 - 1.2, hwall - 0.4, -1.2])
    return body, core


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    r = RAKE - D_EAVE
    zcw = Z_EAVE + S_WING * ((WX1 - WX0) / 2 + D_EAVE)
    gy = (zcw - Z_EAVE) / S_MAIN - D_EAVE + 4.0
    pieces = [(MAIN.pts, [0, 2], S_MAIN),
              ([(WX0, WY - r), (WX1, WY - r), (WX1, gy), (WX0, gy)], [1, 3], S_WING)]
    specs = [dict(p0=(W, 0.0), p1=(W, D), slope=S_MAIN, e=0.3),
             dict(p0=(0.0, D), p1=(0.0, 0.0), slope=S_MAIN, e=0.3),
             dict(p0=(WX0, WY), p1=(WX1, WY), slope=S_WING, e=0.3)]
    rf = G.gabled_roof(pieces, Z_EAVE, D_EAVE, specs, texture="bevel", tex_kw=dict(pitch=1.5, wtab=2.2, d=0.42),
                       skin=SKIN, rake=RAKE, inner_cs=offset(cs_union([MAIN.cs, WING.cs]), -3.0), fascia=FASCIA,
                       hollow=2.6)
    we, ww, wg = rf["walls"]
    gables = [(MAIN, 1, we["cs"].translate((0.0, Z_EAVE - ZF))), (MAIN, 3, ww["cs"].translate((0.0, Z_EAVE - ZF))),
              (WING, 0, wg["cs"].translate((0.0, Z_EAVE - ZF)))]
    walls = wall_shell(BLOCKS, OPENINGS, t=3.0, belt=None, corners="blocked", water_table=False, siding=_siding,
                       gables=gables)
    base = cs_union([MAIN.cs, WING.cs])
    no_lip = union([box([W - 5.0, -1, ZE - 1], [W + 1, D + 1, ZE + 5]), box([-1, -1, ZE - 1], [5.0, D + 1, ZE + 5]),
                    box([WX0 - D_EAVE - 0.6, WY - 1, ZE - 1], [WX1 + D_EAVE + 0.6, WY + 5.0, ZE + 5])])
    lip = (_corbel(base, 3.0, ZE) + lip_ring(base, 3.0, ZE)) - no_lip
    kit.add("WALLS", "Wisteria", walls + lip, group="walls")
    fnd = foundation(BLOCKS, 0.0, ZF, style="riverstone")
    kit.add("FOUNDATION", "River", fnd, group="foundation")
    inserts = []
    for o in OPENINGS:
        A = o.local_frame()
        sp = o.spec
        b = sp["cut"].bounds()
        key = "DOOR" if o.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, "Windows_Doors", "Door" if o.kind == "door" else "Sash", "Glass")
        inserts.append(kit.add(f"{key}-{o.name}", "Windows_Doors", world, P=P,
                               key=f"{key}-{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}", group="inserts", render=zones))
    print("walls + inserts", round(time.time() - t0, 1))

    # --- the roof: a hollow side-gabled roof with the wing's cross gable, the dormers in pockets
    roof = rf["body"] + rf["tex"] + rf["skins"] + rf["skin_tex"]
    zr = Z_EAVE + S_MAIN * (D / 2 + D_EAVE)
    caps = [G.ridge_cap((-RAKE, D / 2), (W + RAKE, D / 2), zr, S_MAIN, ZE)]
    walls_env = union([wl["facade"].place(M.extrude(wl["cs"].offset(0.15), RAKE + 4.2).translate([0, 0, -3.15]))
                       for wl in rf["walls"]])
    wx = (WX0 + WX1) / 2
    caps.append(G.ridge_cap((wx, WY - RAKE), (wx, (zcw - Z_EAVE) / S_MAIN - D_EAVE + 1.0), zcw, S_WING, ZE))
    roof = roof + (union(caps) - walls_env)
    roof = roof - lip_keep(base, 3.0, ZE)
    solid_env, _ = R.hip_roof(pieces, Z_EAVE, S_MAIN, D_EAVE, texture=None, zlo=ZE)
    CW, CD = 7.0, 7.0
    cx, cy = 30.0, D / 2
    z0 = round((zr - 4.0) / 0.2) * 0.2
    roof = roof + G.chimney_seat(solid_env, cx, cy, CW / 2, zr + 1.0)
    pocket = box([cx - CW / 2 - 0.4, cy - CD / 2 - 0.4, z0], [cx + CW / 2 + 0.4, cy + CD / 2 + 0.4, zr + 40])
    roof = roof - pocket
    # the hipped dormers: each a flat-bottomed box dropped into a pocket shaped to it, on a seat
    # block standing on the bed inside the hollow roof, under its own little hip roof
    dyf = 8.0
    zdf = ZE + round((Z_EAVE - ZE + S_MAIN * (dyf + D_EAVE) - 1.0) / 0.2) * 0.2
    dbody, dcore = dormer_hipped()
    dparts = []
    for k, dxc in enumerate(DORMERS):
        Ad = np.array([[1.0, 0, 0, dxc], [0, 0, -1.0, dyf], [0, 1.0, 0, zdf]])
        dkeep = box([-DW / 2 - 0.3, -0.3, -DDEP - 0.3], [DW / 2 + 0.3, DHW, 0.9]).transform(Ad)
        dpocket = dkeep ^ box([-500, -500, zdf], [500, 500, 999])
        dseat = box([dxc - DW / 2 - 1.3, dyf - 1.6, ZE], [dxc + DW / 2 + 1.3, dyf + DDEP + 1.3, zdf]) ^ solid_env
        roof = roof - dpocket + (dseat - dpocket)
        dparts.append((k, dxc, Ad))
    kit.add("ROOF", "Moss", roof, group="roof")
    for k, dxc, Ad in dparts:
        kit.add(f"DORMER-{k}", "Wisteria", dbody.transform(Ad), group="roof")
        kit.add(f"DORMER-core-{k}", "Plum", dcore.transform(Ad), group="roof")
        zeave = zdf + DHW
        path = [(dxc - DW / 2, dyf - DDEP - 6.0), (dxc + DW / 2, dyf - DDEP - 6.0), (dxc + DW / 2, dyf), (dxc - DW / 2, dyf)]
        # (a hip over the dormer's front and sides; it runs back into the main roof)
        dpath = [(dxc - DW / 2, dyf), (dxc + DW / 2, dyf), (dxc + DW / 2, dyf + DDEP + 6.0), (dxc - DW / 2, dyf + DDEP + 6.0)]
        dsol, dtex = R.hip_roof([(dpath, [0, 1, 3])], zeave, 1.1, 1.2, texture="bevel", tex_kw=dict(pitch=1.4, wtab=2.0, d=0.4),
                                zlo=zeave)
        droof = (dsol + dtex) - solid_env - dbody.transform(Ad)
        droof = droof - roof
        kit.add(f"DORMER-roof-{k}", "Moss", droof, group="roof")
    ch = TW.chimney("tulip", w=CW, d=CD, h=round((zr + 9.0 - z0) / 0.2) * 0.2).translate([cx, cy, z0])
    kit.add("CHIMNEY", "Brick", ch, group="roof")
    for k, wl in enumerate(rf["walls"]):
        orn = G.gable_crescent(wl["L"], wl["slope"], D_EAVE, skin=SKIN)
        f = wl["facade"]
        A = f.A.copy()
        A[:, 3] = f.world(0.0, 0.0, RAKE)
        kit.add(f"GABLE-{k}", "Cream", orn.transform(A), P=inv34(A), group="roof")
    print("roof", round(time.time() - t0, 1))

    # --- the porch: across the front and round the west corner in a true curve
    RP = 16.0
    FY = -RP
    YN = 34.0
    XE = WX0
    nf = 5
    arc = [(RP * math.cos(math.pi + (math.pi / 2) * k / nf), RP * math.sin(math.pi + (math.pi / 2) * k / nf))
           for k in range(nf + 1)]
    ppts = [(0.0, YN), (-RP, YN)] + arc + [(XE, FY), (XE, 0.0), (0.0, 0.0)]
    turn = (math.pi / 2) / nf
    ca = 1.6 * math.tan(turn / 2)                 # at the joints between facets
    cj = 1.6 * math.tan(turn / 4)                 # where the curve meets a straight run
    Ls = float(np.linalg.norm(np.array(arc[1]) - np.array(arc[0])))
    runs = [dict(a=(0.0, YN), b=(-RP, YN), posts=[3.0, RP - 1.6]),
            dict(a=(-RP, YN), b=arc[0], posts=[1.6, YN / 2, YN - cj])]
    for k in range(nf):
        runs.append(dict(a=arc[k], b=arc[k + 1], posts=[cj if k == 0 else ca, Ls - (cj if k == nf - 1 else ca)]))
    Lf = XE - arc[-1][0]
    ud = DOOR_X - arc[-1][0]
    runs.append(dict(a=arc[-1], b=(XE, FY), posts=[cj, ud - 8.2, ud + 8.2, Lf - 2.6]))
    steps_run = len(runs) - 1
    H_floor = ZF - 1.4
    post_h = ZE - 3.0 - 5.6 - H_floor
    PP = FT.porch_turned(ppts, runs, H_floor, post_h, steps_at=[(steps_run, ud, 14.0)],
                         planks=dict(pitch=1.5, border=1.4), joined=True, ledger_off=1.5, post="octagon",
                         rail="hearts", arcade="clusters", skirt="saltire", pier_tex="riverstone", roof_edge="arcading")
    fkeep = slab(offset(base, 0.8 + 0.55 + 0.15), -1, ZF + 1.3)
    ins_keep = union([box(np.array(p.solid.bounding_box()[:3]) - 0.2, np.array(p.solid.bounding_box()[3:]) + 0.2)
                      for p in inserts if p is not None])
    deck = PP["deck"] - fkeep
    kit.add("PORCH-deck", "PorchDeck", deck, P=print_flip(), group="porch",
            render=FT.plank_zones(deck, H_floor, "Planks", "PorchDeck"))
    tabs = union([arc_ for arc_, _ in PP["arcades"]])
    for k, fr in enumerate(sorted(PP["frames"], key=lambda m_: -m_.volume())):
        kit.add(f"PORCH-frame-{k}", "Cream", fr - tabs - fnd, group="porch")
    for k, (arc_, A) in enumerate(PP["arcades"]):
        kit.add(f"PORCH-frieze-{k}", "Plum", arc_, P=compose(FT.ARCADE_PRINT, inv34(A)), group="porch")
    bld_keep = union([b.solid(grow=1.8, dz0=-20, dz1=0) for b in BLOCKS])
    proof = PP["roof"] - bld_keep - ins_keep
    ptop = proof.bounding_box()[5]
    kit.add("PORCH-roof", "Cream", proof.trim_by_plane([0, 0, -1.0], -(ptop - 0.8)), P=print_flip(), group="porch")
    kit.add("PORCH-roof-top", "Moss", proof.trim_by_plane([0, 0, 1.0], ptop - 0.8), group="porch")
    for k, (sm, A) in enumerate(PP["steps"]):
        kit.add(f"PORCH-steps-{k}", "River", sm.transform(A) - fkeep - deck, group="porch")
    e, u = MAIN.locate(70.0, D)
    fb = MAIN.facades()[e]
    A = fb.A.copy()
    A[:, 3] = fb.world(u, -ZF, 1.4)
    kit.add("STOOP-back", "River", FT.steps(10.0, ZF - 0.6, 3).transform(A) - fnd, group="porch")
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "wisteria")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:40]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "wisteria.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))

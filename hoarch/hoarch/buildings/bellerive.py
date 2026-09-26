"""The Bellerive: an original HO-scale (1:87.1) French Colonial (Louisiana Creole) house, house
42 and the second pilot of the fourth batch.

A raised Creole house. The ground storey is rose lime stucco over soft brick, fallen away in
ragged patches to show the brick, with arched openings closed by batten doors; the main floor
stands above it on the gallery, its walls of briquette-entre-poteaux (a timber frame with brick
laid between the posts), limewashed, every opening a pair of French doors under a fanlit
transom between Creole-green batten shutters. A gallery runs across the front and down both
ends on stuccoed Tuscan columns, slender turned colonnettes above them carrying a pierced
frieze board and a railing of diamond-set balusters, its floor of planks; its roof, a gentle
skirt of crenel-cut cypress shingles, sweeps out from under the main eave. A grand stair with
sloped stucco cheeks climbs to the gallery. Between the storeys an oxblood frieze of fleurs-de-lis
with lozenges over a white chevron course; at the eave an oxblood grapevine frieze, white
dentils, exposed rafter tails and a cavetto crown. A steep hip roof of the same shingles with
two gabled dormers and two stuccoed stacks with arcaded caps.

usage: python3 -m hoarch.buildings.bellerive [check] [export]
"""
import os
import sys
import time

import numpy as np
from manifold3d import JoinType, Manifold as M

from hoarch.core import box, inv34, offset, poly, rect, slab, union
from hoarch import colonial as C, cornice as CO, features as FT, federal as F, gables as G, openings as O, roof as R
from hoarch.kit import Kit, print_flip
from hoarch.ornament import ext
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, stacked_shells

NAME = "The Bellerive"
COLORS = {"Rose": "#D39B86", "Limewash": "#E9E2CE", "White": "#F2EFE6", "Oxblood": "#7A2E2A", "Cypress": "#6E6254",
          "Green": "#3E5E3A", "Planks": "#6F5034", "PorchDeck": "#6F5034", "Brick": "#8A4632", "Windows_Doors": "#F2EFE6"}
RENDER_MAT = {"Rose": "stone", "Limewash": "siding", "White": "trim", "Oxblood": "accent", "Cypress": "roof",
              "Green": "shutter", "Planks": "planks", "PorchDeck": "planks", "Brick": "brick", "Windows_Doors": "trim", "Door": "door",
              "Glass": "glass"}

# ------------------------------------------------------------------ cornices (unique to the Bellerive)
LEDGE = 1.4
JOINT = dict(pitch=15.0, margin=4.0, layers=[
    dict(kind="frieze", h=4.2, b=1.2, orn="fleurs", role="Oxblood"),
    dict(kind="course", h=1.4, b=1.4, orn="chevron", role="White"),
    dict(kind="crown", h=2.0, b=1.4, P=3.4, orn="ovolo", role="White")])
EAVE = dict(pitch=12.0, margin=4.0, layers=[
    dict(kind="frieze", h=5.2, b=1.2, orn="grapes", role="Oxblood"),
    dict(kind="course", h=1.4, b=1.4, orn="dentil", role="White", tooth=0.8, gap=0.6),
    dict(kind="bed", h=1.8, b=1.4, P=5.0, role="White", brackets=dict(style="rafter", t=1.2, reach=0.3)),
    dict(kind="crown", h=2.4, b=1.4, P=5.8, orn="cavetto", role="White")])
RJ = round((LEDGE + 0.4 + CO.band_height(JOINT)) / 0.2) * 0.2
HE = CO.band_height(EAVE)

# ------------------------------------------------------------------ levels (on the 0.2 mm grid)
ZF = 4.0
S1 = ZF + 26.0                  # the raised ground storey
H_FLOOR = S1 + RJ               # the main floor = the gallery floor
POST_H = 34.0
ZE = H_FLOOR + 48.0
ZW = ZE + HE
FASCIA = 1.4
Z_EAVE = ZW + FASCIA
D_EAVE = 6.4
S_MAIN = 1.0
S_GAL = 0.42                    # the gallery's skirt roof

# ------------------------------------------------------------------ plan (x east, y north; the front faces south)
W, D = 152.0, 92.0
XC = W / 2
GD = 16.0                        # gallery depth
EJ = 3.7                        # the joint cornice's reach: the gallery floor starts there
MAIN = Block("main", [(0, 0), (W, 0), (W, D), (0, D)], ZF, ZW)
BLOCKS = [MAIN]
INSET = 1.6
FRONT_X = (20.0, 48.0, XC, 104.0, 132.0)


def _skin(f, b, reg):
    """Stucco over brick below the joint, colombage above it; nothing in the eave band."""
    reg = reg - rect(-1, ZE - b.z0, f.L + 1, 999)
    lo = reg ^ rect(-1, -10, f.L + 1, S1 - b.z0)
    hi = reg ^ rect(-1, S1 - b.z0, f.L + 1, 999)
    seed = int(abs(f.n[0]) * 3 + abs(f.n[1]) * 7 + f.p0[0])
    out = []
    if not lo.is_empty():
        out.append(F.stucco_spalled(lo, seed=seed))
    if not hi.is_empty():
        out.append(F.colombage(hi, datum=S1 - b.z0))
    return union(out) if out else M()


def _openings():
    L, SH = [], []

    def add(x, y, v0, sp, name, kind="window", shutters=False):
        e, u = MAIN.locate(x, y)
        L.append(Opening(MAIN, e, u, v0, sp, name, kind))
        if shutters:
            SH.append(name)

    gdoor = F.door_batten_arched(11.0, 19.0, rise=2.6)
    gwin = F.door_batten_arched(8.0, 12.6, rise=2.0)
    fdoor = F.door_creole(10.0, 31.0)
    fwin = F.door_creole(9.0, 22.0, transom=4.0)
    v_main = H_FLOOR - ZF + 0.4
    for x in FRONT_X:
        if x == XC:
            add(x, 0.0, 0.4, gdoor, "S-ground-door", "door")
        else:
            add(x, 0.0, 6.2, gwin, f"S{x:.0f}-g")
        add(x, 0.0, v_main, fdoor, f"S{x:.0f}-m", "door", shutters=True)
    for x_ in (0.0, W):
        tag = "W" if x_ == 0 else "E"
        for y in (24.0, 68.0):
            add(x_, y, 6.2, gwin, f"{tag}{y:.0f}-g")
        for y in (22.0, 46.0, 70.0):
            add(x_, y, v_main, fdoor, f"{tag}{y:.0f}-m", "door", shutters=True)
    for x in FRONT_X:
        if x == XC:
            add(x, D, 0.4, gdoor, "N-ground-door", "door")
        else:
            add(x, D, 6.2, gwin, f"N{x:.0f}-g")
        add(x, D, v_main + 8.0, fwin, f"N{x:.0f}-m", shutters=True)
    return L, SH


OPENINGS, SHUTTERED = _openings()


def _gallery():
    """The U-shaped gallery across the front and down both ends: its outline, runs and posts."""
    pts = [(-GD, D), (-GD, -GD), (W + GD, -GD), (W + GD, D), (W + EJ, D), (W + EJ, -EJ), (-EJ, -EJ), (-EJ, D)]
    Le = GD - EJ
    side = [INSET + (D + GD - 2 * INSET) * k / 6 for k in range(7)]
    front = [INSET + (W + 2 * GD - 2 * INSET) * k / 9 for k in range(10)]
    runs = [dict(a=(-EJ, D), b=(-GD, D), posts=[INSET, Le - INSET]),
            dict(a=(-GD, D), b=(-GD, -GD), posts=side),
            dict(a=(-GD, -GD), b=(W + GD, -GD), posts=front),
            dict(a=(W + GD, -GD), b=(W + GD, D), posts=side),
            dict(a=(W + GD, D), b=(W + EJ, D), posts=[INSET, Le - INSET])]
    return pts, runs


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    base = MAIN.cs
    pieces = [(MAIN.pts, [0, 1, 2, 3], S_MAIN)]
    undress = [slab(offset(base, 8.0), ZE - LEDGE - 0.6, ZW + 0.01)]
    clear = [lip_keep(base, 3.0, ZF, 1.2)]
    st = stacked_shells(BLOCKS, OPENINGS, [S1], t=3.0, corners="none", siding=_skin, gables=[], clear=clear,
                        prof=CO.joint_profile(RJ, LEDGE), belt_blocks=None, water_table=False, undress=undress,
                        partitions=[((XC - 18.0, 3.0), (XC - 18.0, D - 3.0), 2.0, ZF, ZW)])
    kit.add("WALLS-1", "Rose", st["shells"][0], group="walls")
    kit.add("JOINT", "Rose", st["rings"][0], group="walls")
    lip = _corbel(base, 3.0, ZW) + lip_ring(base, 3.0, ZW)
    kit.add("WALLS-2", "Limewash", st["shells"][1] + lip + CO.ledge(MAIN.pts, ZE, LEDGE), group="walls")
    rings, _ = CO.level(st["outlines"][0], S1 + LEDGE + 0.4, JOINT)
    CO.add_level(kit, rings, "CORNICE-J", "cornice")
    rings, _ = CO.level(MAIN.pts, ZE, EAVE)
    CO.add_level(kit, rings, "CORNICE-E", "cornice")
    fnd = foundation(BLOCKS, 0.0, ZF, style="bricksill")
    kit.add("FOUNDATION", "Brick", fnd, group="foundation")

    # windows, doors and shutters
    ins_keep = []
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
            left, right = C.shutters_pair(w_op, h_op - 2.0, casing=1.1, gap=0.6, make=F.shutter_batten)
            for s_, m in (("L", left), ("R", right)):
                kit.add(f"SHUTTER-{o.name}-{s_}", "Green", m.translate([0, 0, 0.32]).transform(A),
                        P=inv34(A), key=f"SHUTTER-{h_op:.1f}", group="shutters")
    print("walls + cornices + inserts", round(time.time() - t0, 1))

    # --- the gallery: planks on stuccoed columns (one part, upside down), the pink-house top
    pts, runs = _gallery()
    P = FT.porch_turned(pts, runs, H_FLOOR, POST_H, steps_at=[(2, (W + 2 * GD) / 2, 22.0)], over=2.4, inset=INSET,
                        rail_h=8.6, post="creole", rail="diamond", arcade="cutwork", roof_edge="ovals", skirt="lattice",
                        pier_tex="brick", planks=dict(pitch=1.6, crack=0.25, border=1.4, along=(0.0, 1.0)), top=True)
    bld_keep = union([st["shells"][0], st["shells"][1], st["rings"][0]] +
                     [p.solid for p in kit.parts if p.name.startswith("CORNICE")])
    keep = bld_keep + union(ins_keep)
    where = []
    for r in runs:
        f = FT.Facade(r["a"], r["b"], 0.0)
        for u in r["posts"]:
            p = f.p0 + f.u * u - f.n * INSET
            if not any(np.allclose(p, q, atol=0.05) for q in where):
                where.append(p)
    gcs = poly(pts)
    planks = FT.porch_planks(pts, [7, 0, 1, 2, 3], H=H_FLOOR, pitch=1.6, crack=0.25, border=1.4, along=(0.0, 1.0))
    ring = gcs - offset(gcs, -2.4)
    frame = slab(ring, H_FLOOR - 4.4, H_FLOOR - 1.0)
    b_ = gcs.bounds()
    joists = union([box([x - 0.5, b_[1], H_FLOOR - 3.0], [x + 0.5, b_[3], H_FLOOR - 1.0]) for x in np.arange(b_[0] + 3, b_[2], 6.0)]) \
        ^ slab(gcs, -10, 999)
    cols = []
    from hoarch.porchwork import _revolve
    hc = H_FLOOR - 4.4 + 0.3
    prof = [(0.0, 0.0), (2.8, 0.0), (2.8, 1.0), (2.4, 1.4), (2.2, 1.8), (2.1, hc * 0.35), (1.9, hc - 2.4), (2.4, hc - 1.9),
            (2.6, hc - 1.4), (2.9, hc - 1.0), (2.9, hc), (0.0, hc)]
    col = _revolve(prof, 36)
    for p in where:
        cols.append(col.translate([p[0], p[1], 0.0]))
    deck = planks + frame + joists + union(cols)
    socks = union([box([p[0] - 1.0, p[1] - 1.0, H_FLOOR - 2.0], [p[0] + 1.0, p[1] + 1.0, H_FLOOR + 1.0]) for p in where])
    deck = (deck - socks) - bld_keep
    kit.add("GALLERY-deck", "PorchDeck", deck, P=print_flip(), group="gallery",
            render=FT.plank_zones(deck, H_FLOOR, "Planks", "Rose"))
    res = FT.add_porch_top(kit, "GALLERY", P, keep, "White", "White", tin="custom", group="gallery")
    zs = res["ptop"] - 0.8                                        # the flat top the skirt roof sits on
    # the skirt roof: a gentle hip of cypress shingles from the gallery's edge up to the wall
    o = 2.4
    outer = [(-GD - o, -GD - o), (W + GD + o, -GD - o), (W + GD + o, D + o), (-GD - o, D + o)]
    sk, sk_tex = R.hip_roof([(outer, [0, 1, 3])], zs, S_GAL, 0.0, texture=["crenel"], tex_kw=dict(pitch=1.5, wtab=2.0, d=0.38), zlo=zs)
    reg = poly(outer) - rect(0.0, -0.01, W, D + o + 1)
    skirt = (sk + sk_tex) ^ slab(reg, zs, zs + S_GAL * (GD + o) + 0.6)
    skirt = skirt - bld_keep
    kit.add("GALLERY-roof", "Cypress", skirt, group="gallery")
    # the grand stair up to the gallery
    fr = FT.Facade((-GD, -GD), (W + GD, -GD), 0.0)
    A = fr.A.copy()
    A[:, 3] = fr.world((W + 2 * GD) / 2, 0.0, 0.0)
    kit.add("STAIR", "Rose", F.stair_creole(18.0, H_FLOOR, 12, cheek=2.0).transform(A), group="gallery")
    print("gallery", round(time.time() - t0, 1))

    # --- the main roof: a steep hip of crenel-cut shingles, two dormers, two stacks
    rf = G.gabled_roof(pieces, Z_EAVE, D_EAVE, [], texture=["crenel"], tex_kw=dict(pitch=1.6, wtab=2.2, d=0.4),
                       inner_cs=offset(base, -3.0), fascia=FASCIA, hollow=2.8)
    roof = rf["body"] + rf["tex"]
    zr = Z_EAVE + S_MAIN * (D / 2 + D_EAVE)
    caps = [G.ridge_cap((D / 2, D / 2), (W - D / 2, D / 2), zr, S_MAIN, ZW, half=1.2, up=0.6)]
    corners = [(-D_EAVE, -D_EAVE), (W + D_EAVE, -D_EAVE), (W + D_EAVE, D + D_EAVE), (-D_EAVE, D + D_EAVE)]
    ends = [(D / 2, D / 2), (W - D / 2, D / 2), (W - D / 2, D / 2), (D / 2, D / 2)]
    hips = union([G.hip_cap((c[0], c[1], Z_EAVE), (e[0], e[1], zr), half=1.2, up=0.6, drop=1.8) for c, e in zip(corners, ends)])
    roof = roof + union(caps) + hips
    roof = roof - lip_keep(base, 3.0, ZW)
    roof = roof.trim_by_plane([0, 0, 1.0], Z_EAVE - FASCIA)
    solid_env, _ = R.hip_roof(pieces, Z_EAVE, S_MAIN, D_EAVE, texture=None, zlo=ZW)
    CW, CD = 9.0, 9.0
    pockets, stacks = [], []
    for cx in (XC - 34.0, XC + 34.0):
        cy = D / 2
        z0 = round((zr - 8.0) / 0.2) * 0.2
        roof = roof + G.chimney_seat(solid_env, cx, cy, CW / 2, zr + 1.0)
        pockets.append(box([cx - CW / 2 - 0.4, cy - CD / 2 - 0.4, z0], [cx + CW / 2 + 0.4, cy + CD / 2 + 0.4, zr + 40]))
        stacks.append(F.chimney_arcade(CW, CD, zr + 12.0 - z0).translate([cx, cy, z0]))
    roof = roof - union(pockets)
    DW, DDEP, DHW = 13.0, 18.0, 12.0
    dyf = 14.0
    zdf = round((Z_EAVE + S_MAIN * (dyf + D_EAVE) - 1.0) / 0.2) * 0.2
    dbody, dcore, dface = F.dormer_creole(DW, DDEP, DHW)
    dparts = []
    for dxc in (48.0, W - 48.0):
        Ad = np.array([[1.0, 0, 0, dxc], [0, 0, -1.0, dyf], [0, 1.0, 0, zdf]])
        dkeep = ext(dface.offset(0.3, JoinType.Miter, 4.0), -DDEP - 0.3, 0.3).transform(Ad)
        dpocket = dkeep ^ box([-500, -500, zdf], [500, 500, 999])
        dseat = box([dxc - DW / 2 - 1.3, dyf - 1.6, ZW], [dxc + DW / 2 + 1.3, dyf + DDEP + 1.3, zdf]) ^ solid_env
        roof = roof - dpocket
        roof = roof + (dseat - dpocket - lip_keep(base, 3.0, ZW))
        dparts.append(Ad)
    kit.add("ROOF", "Cypress", roof, group="roof")
    for k, s_ in enumerate(stacks):
        kit.add(f"CHIMNEY-{k}", "Rose", s_, key="CHIMNEY", group="roof")
    ez = DHW - 1.6
    droof_cs = poly([(-DW / 2 - 1.6, ez), (-DW / 2, ez), (-DW / 2, DHW), (0.0, DHW + DW / 2 + 0.2), (DW / 2, DHW),
                     (DW / 2, ez), (DW / 2 + 1.6, ez), (DW / 2 + 1.6, ez + 1.6), (0.0, DHW + DW / 2 + 2.2),
                     (-DW / 2 - 1.6, ez + 1.6)])
    for k, Ad in enumerate(dparts):
        kit.add(f"DORMER-{k}", "White", dbody.transform(Ad), key="DORMER", group="roof")
        kit.add(f"DORMER-core-{k}", "Cypress", dcore.transform(Ad), key="DORMER-core", group="roof")
        droof = ext(droof_cs, -DDEP - 6.0, 1.2).transform(Ad) - solid_env - dbody.transform(Ad) - roof
        kit.add(f"DORMER-roof-{k}", "Cypress", max(droof.decompose(), key=lambda m_: m_.volume()), key="DORMER-roof", group="roof")
    print("roof", round(time.time() - t0, 1))
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "bellerive")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:40]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "bellerive.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))

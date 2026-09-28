"""The Millbrook Depot: an original HO-scale (1:87.1) passenger and freight station, building 61
(the railroad and town batch).

A long one-storey railroad Stick depot of about 1885 under a steep hipped roof of sawn shingles
(every other course with octagon butts) on deep eaves carried by big solid knee brackets. Car
siding (vertical tongue-and-groove) to a chair rail, drop siding in stick-framed panels above,
on drafted-margin ashlar. The eave cornice is a frieze of locomotive drivers coupled by side
rods, a rail on its ties, the bracketed soffit and an ogee crown. A platform runs the length of
the track side under a low canopy on round columns (octagonal bases, ringed necks), with cove
brackets at every column and a beaded fascia with rosettes; steps at the west end. The agent's
canted bay stands out onto the platform under the canopy. Two-over-two windows and the waiting
room doors wear low gabled heads with fans of rays; the freight room has sliding doors on
track bars. A gabled dormer over the agent's bay (drop siding, a rayed window head, a king-post
truss in its peak). Name boards on both ends; two brick stove flues with iron stovepipes.

usage: python3 -m hoarch.buildings.millbrook [check] [export]
"""
import os
import sys
import time

import numpy as np

from hoarch.core import box, offset, poly, rect, slab, union
from hoarch import cornice as CO, features as FT, gables as G, openings as O, roof as R, town as TN
from hoarch.kit import Kit, print_flip
from hoarch.ornament import chamfer_box
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, wall_shell

NAME = "The Millbrook Depot"
COLORS = {"Gold": "#D3A447", "Chocolate": "#5A3A2A", "Cream": "#EDE3C8", "Green": "#435A4C", "Stone": "#9E978A",
          "Brick": "#7B3B2D", "PorchDeck": "#7C6853", "Windows_Doors": "#EDE3C8"}
RENDER_MAT = {"Gold": "siding", "Chocolate": "choc", "Cream": "trim", "Green": "roof", "Stone": "stone", "Brick": "brick",
              "PorchDeck": "deck", "Planks": "planks", "Windows_Doors": "trim", "Door": "door", "Glass": "glass",
              "Letters": "choc"}
PALETTE = {"siding": ("#D3A447", 0.8), "choc": ("#5A3A2A", 0.6), "trim": ("#EDE3C8", 0.5), "roof": ("#435A4C", 0.85),
           "stone": ("#9E978A", 0.9), "brick": ("#7B3B2D", 0.9), "deck": ("#6E5B48", 0.85), "planks": ("#8C7456", 0.85),
           "door": ("#5A3A2A", 0.6)}
VIEWS = {"hero": [-34, 16, 70, 0.95, [0, 0, 0]], "front": [0, 6, 80, 0.92, [0, 0, 0]], "rear": [150, 18, 70, 0.95, [0, 0, 0]],
         "right": [60, 12, 70, 0.95, [0, 0, 0]], "platform": [-26, 8, 85, None, [45, -22, 26], 170]}

# ------------------------------------------------------------------ the eave cornice (unique to the Millbrook)
LEDGE = 1.4
EAVE = dict(pitch=13.0, margin=4.5, layers=[
    dict(kind="frieze", h=5.2, b=1.2, orn="driverwheels", role="Chocolate"),
    dict(kind="course", h=1.6, b=1.4, orn="railties", role="Cream"),
    dict(kind="bed", h=2.6, b=1.4, P=9.2, role="Cream", brackets=dict(style="depotknee", t=1.6, reach=0.4)),
    dict(kind="crown", h=2.0, b=1.4, P=9.6, orn="ogee_fillet", role="Chocolate")])
HE = CO.band_height(EAVE)

# ------------------------------------------------------------------ levels and plan
ZF = 8.0
ZE = ZF + 48.0
ZW = round((ZE + HE) / 0.2) * 0.2
FASCIA = 1.6
Z_EAVE = ZW + FASCIA
D_EAVE = 10.2
S_MAIN = 0.62
W, D = 196.0, 64.0
XC, YC = W / 2, D / 2
CHAIR = 14.0                                    # the chair rail's top, above ZF
PD = 34.0                                       # the platform's depth
PTOP = ZF + 39.0                                # the canopy's flat top
S_CAN = 0.16
CX, BW0, BW1, BD = 100.0, 15.0, 9.0, 9.0        # the agent's bay: centre, half widths at the wall and front, depth
MAIN = Block("main", [(0, 0), (W, 0), (W, D), (0, D)], ZF, ZW)
BAY = Block("bay", [(CX - BW0, 3.0), (CX - BW0, 0.0), (CX - BW1, -BD), (CX + BW1, -BD), (CX + BW0, 0.0), (CX + BW0, 3.0)],
            ZF, PTOP - 0.8)
BLOCKS = [MAIN, BAY]
V1 = 7.0
SIGN_V, SIGN_L, SIGN_H = 38.0, 40.0, 7.0        # the name boards on the end walls (v from ZF)
FLUES = [(62.0, YC + 5.0), (148.0, YC + 5.0)]


def _openings():
    L = []

    def add(blk, x, y, v0, sp, name, kind="window"):
        e, u = blk.locate(x, y)
        L.append(Opening(blk, e, u, v0, sp, name, kind))

    win = TN.window_depot(11.0, 22.0)
    narrow = TN.window_depot(6.0, 22.0, A=1.2)
    for x in (22.0, 48.0):
        add(MAIN, x, 0.0, V1, win, f"S{x:.0f}")
    add(MAIN, 70.0, 0.0, 0.4, TN.door_depot(16.0, 26.0), "front-door", "door")
    add(MAIN, 128.0, 0.0, 0.4, TN.door_depot(14.0, 26.0), "baggage-door", "door")
    add(MAIN, 166.0, 0.0, 0.4, TN.door_freight(18.0, 26.0), "freight-S", "door")
    add(BAY, CX, -BD, V1, win, "bay")
    add(BAY, CX - (BW0 + BW1) / 2, -BD / 2, V1, narrow, "bay-W")
    add(BAY, CX + (BW0 + BW1) / 2, -BD / 2, V1, narrow, "bay-E")
    for x in (24.0, 52.0, 80.0, 108.0):
        add(MAIN, x, D, V1, win, f"N{x:.0f}")
    add(MAIN, 134.0, D, 0.4, TN.door_depot(13.0, 26.0), "back-door", "door")
    add(MAIN, 170.0, D, 0.4, TN.door_freight(18.0, 26.0), "freight-N", "door")
    for y in (18.0, 46.0):
        add(MAIN, 0.0, y, V1, win, f"W{y:.0f}")
    add(MAIN, W, YC, 0.4, TN.door_freight(18.0, 26.0), "freight-E", "door")
    return L


OPENINGS = _openings()


def _sticks(f, b):
    """Stick boards at the corners and midway between the openings of a facade."""
    if b is not MAIN:
        return ()
    us = sorted(op.u for op in OPENINGS if op.block is MAIN and np.allclose(MAIN.facades()[op.edge].n, f.n))
    return [0.7, f.L - 0.7] + [(a + c) / 2 for a, c in zip(us[:-1], us[1:])]


def _fields(f, b):
    """Plain fields left in the siding: the name board's on the end walls, and the sliding
    freight doors' (leaf, track and hangers stand on the wall's flat face)."""
    out = []
    if b is not MAIN:
        return out
    if abs(f.n[0]) > 0.5:
        out.append(rect(f.L / 2 - SIGN_L / 2 - 0.2, SIGN_V - 0.2, f.L / 2 + SIGN_L / 2 + 0.2, SIGN_V + SIGN_H + 0.2))
    for op in OPENINGS:
        if op.block is MAIN and op.name.startswith("freight") and np.allclose(MAIN.facades()[op.edge].n, f.n):
            w_ = op.spec["cut"].bounds()[2] - op.spec["cut"].bounds()[0] - 0.4
            out.append(rect(op.u - w_ / 2 - 1.8, op.v0 - 0.2, op.u + w_ / 2 + w_ * 0.8 + 0.4, op.v0 + 26.0 + 3.4))
    return out


def _skin(f, b, reg):
    reg = reg - rect(-1, ZE - LEDGE - 0.6 - b.z0, f.L + 1, 999)
    fields = _fields(f, b)
    for fl in fields:
        reg = reg - fl
    lo = reg ^ rect(-1, -50, f.L + 1, CHAIR - 1.8)
    hi = reg ^ rect(-1, CHAIR, f.L + 1, 999)
    out = TN.depot_wainscot(lo) + TN.depot_droplap(hi, datum=CHAIR, sticks=_sticks(f, b))
    rail = chamfer_box(-1.0, CHAIR - 1.8, f.L + 1.0, CHAIR, 0.0, 0.9, c=0.3, bottom=0.9)
    rail = rail ^ TN.ext(reg.offset(2.0, TN.MJ, 4.0) ^ rect(0.0, -50, f.L, 999), -1.0, 3.0)
    if fields:
        rail = rail - TN.ext(TN.cs_union(fields), -1.0, 3.0)
    return out + rail


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    base = MAIN.cs
    undress = [slab(offset(base, 11.0), ZE - LEDGE - 0.6, ZW + 0.01)]
    walls = wall_shell(BLOCKS, OPENINGS, t=3.0, belt=None, corners="none", water_table=False, siding=_skin,
                       undress=undress, partitions=[((140.0, 3.0), (140.0, D - 3.0), 2.0, ZF, ZW)])
    walls = walls - lip_keep(base, 3.0, ZF, 1.2) - lip_keep(BAY.cs, 3.0, ZF, 1.2)
    lip = _corbel(base, 3.0, ZW) + lip_ring(base, 3.0, ZW)
    walls = walls + lip + CO.ledge(MAIN.pts, ZE, LEDGE)
    walls = walls - union([O.place(op.spec, op.local_frame(), "Windows_Doors", "Door", "Glass")[0]
                           for op in OPENINGS if op.name.startswith("freight")])      # the sliding doors' hardware
    below = box([-50, -50, -1], [W + 50, D + 50, ZF + CHAIR])
    kit.add("WALLS", "Chocolate", walls, group="walls", change=(CHAIR, "Gold"),
            render=[("Chocolate", walls ^ below), ("Gold", walls - below)])
    rings, _ = CO.level(MAIN.pts, ZE, EAVE)
    CO.add_level(kit, rings, "CORNICE-E", "cornice")
    fnd = foundation(BLOCKS, 0.0, ZF, style="drafted")
    kit.add("FOUNDATION", "Stone", fnd, group="foundation")
    ins_keep = []
    for op in OPENINGS:
        A = op.local_frame()
        sp = op.spec
        b = sp["cut"].bounds()
        key = "DOOR" if op.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, "Windows_Doors", "Door" if op.kind == "door" else "Windows_Doors", "Glass")
        part = kit.add(f"{key}-{op.name}", "Windows_Doors", world, P=P,
                       key=f"{key}-{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}-{op.name[:4]}", group="inserts", render=zones)
        ins_keep.append(part.solid)
    # the name boards, each glued by its whole back into the plain field left in the siding
    for e in (1, 3):
        f = MAIN.facades()[e]
        A = f.A.copy()
        A[:, 3] = f.world(f.L / 2, SIGN_V, 0.0)
        sb = TN.sign_board("MILLBROOK", SIGN_L, SIGN_H)
        Pp = np.column_stack([np.vstack([A[:, 0], A[:, 1], A[:, 2]]), np.zeros(3)])
        board = sb.transform(A)
        flat = box([-SIGN_L / 2 - 1, -1.0, -1.0], [SIGN_L / 2 + 1, SIGN_H + 1, 1.205]).transform(A)
        kit.add(f"SIGN-{'E' if e == 1 else 'W'}", "Cream", board, P=Pp, key="SIGN", group="signs",
                render=[("Cream", board ^ flat), ("Letters", board - flat)])
    print("walls + cornice + inserts", round(time.time() - t0, 1))

    # --- the roof: a steep hip of octagon-butt shingles, ridge and hip caps, two stove flues
    pieces = [(MAIN.pts, [0, 1, 2, 3], S_MAIN)]
    rf = G.gabled_roof(pieces, Z_EAVE, D_EAVE, [], texture="octabutt", tex_kw=dict(pitch=1.8, wtab=2.6, d=0.4),
                       inner_cs=offset(base, -3.0), fascia=FASCIA, hollow=2.8)
    roof = rf["body"] + rf["tex"]
    zr = Z_EAVE + S_MAIN * (D / 2 + D_EAVE)
    corners = [(-D_EAVE, -D_EAVE), (W + D_EAVE, -D_EAVE), (W + D_EAVE, D + D_EAVE), (-D_EAVE, D + D_EAVE)]
    ends = [(D / 2, YC), (W - D / 2, YC), (W - D / 2, YC), (D / 2, YC)]
    roof = roof + G.ridge_cap((D / 2, YC), (W - D / 2, YC), zr, S_MAIN, ZW, half=1.4, up=0.8)
    roof = roof + union([G.hip_cap((c[0], c[1], Z_EAVE), (e[0], e[1], zr), half=1.4, up=0.8, drop=2.0) for c, e in zip(corners, ends)])
    roof = roof - lip_keep(base, 3.0, ZW)
    roof = roof.trim_by_plane([0, 0, 1.0], Z_EAVE - FASCIA)
    solid_env, _ = R.hip_roof(pieces, Z_EAVE, S_MAIN, D_EAVE, texture=None, zlo=ZW)
    flues = []
    for cx, cy in FLUES:
        CW = 7.0
        zc = Z_EAVE + S_MAIN * (D + D_EAVE - cy - CW / 2 - 0.4)
        z0 = round((zc - 6.0) / 0.2) * 0.2
        roof = roof + (box([cx - CW / 2 - 1.8, cy - CW / 2 - 1.8, ZW + 0.01], [cx + CW / 2 + 1.8, cy + CW / 2 + 1.8, z0 + 0.01]) ^ solid_env)
        roof = roof - box([cx - CW / 2 - 0.6, cy - CW / 2 - 0.6, z0], [cx + CW / 2 + 0.6, cy + CW / 2 + 0.6, zr + 60])
        flues.append(TN.chimney_depot(CW, CW, zr + 12.0 - z0).translate([cx, cy, z0]))
    # the dormer over the agent's bay, its face on the front slope
    DW, DDEP, DHW = 24.0, 16.0, 11.0
    dyf = 8.0
    zdf = round((Z_EAVE + S_MAIN * (dyf + D_EAVE) - 1.0) / 0.2) * 0.2
    dbody, dcore, dface = TN.dormer_depot(DW, DDEP, DHW)
    droof = TN.dormer_depot_roof(DW, DDEP, DHW)
    Ad = np.column_stack([(1.0, 0, 0), (0, 0, 1.0), (0, -1.0, 0), (CX, dyf, zdf)]).astype(float)
    dkeep = TN.ext(dface.offset(0.3, TN.MJ, 4.0), -DDEP - 0.3, 0.3).transform(Ad)
    dpocket = dkeep ^ box([-500, -500, zdf], [500, 500, 999])
    seat = box([-DW / 2 - 1.3, ZW - zdf, -DDEP - 1.3], [DW / 2 + 1.3, 0.0, 1.6]).transform(Ad) ^ solid_env
    roof = roof - dpocket + (seat - dpocket - lip_keep(base, 3.0, ZW)) - dbody.transform(Ad)
    kit.add("ROOF", "Green", roof, group="roof")
    kit.add("DORMER", "Gold", dbody.transform(Ad), group="roof")
    kit.add("DORMER-core", "Green", dcore.transform(Ad), group="roof", render=[("Glass", dcore.transform(Ad))])
    dr = droof.transform(Ad) - solid_env - dbody.transform(Ad) - roof
    kit.add("DORMER-roof", "Green", max(dr.decompose(), key=lambda m_: m_.volume()), group="roof")
    for k, fl in enumerate(flues):
        kit.add(f"FLUE-{k}", "Brick", fl, key="FLUE", group="roof")
    print("roof", round(time.time() - t0, 1))

    # --- the platform: planks on timber stringers, columns one piece with the canopy
    INSET = 2.2
    ppts = [(0.0, 0.0), (0.0, -PD), (W, -PD), (W, 0.0)]
    posts = list(np.linspace(INSET, W - INSET, 7))
    runs = [dict(a=(0.0, 0.0), b=(0.0, -PD), posts=[3.4, PD - INSET]),
            dict(a=(0.0, -PD), b=(W, -PD), posts=posts),
            dict(a=(W, -PD), b=(W, 0.0), posts=[INSET, PD - 3.4])]
    H_floor = ZF - 1.4
    o = 2.6
    PP = FT.porch_turned(ppts, runs, H_floor, PTOP - 5.2 - H_floor, steps_at=[(0, PD / 2, 16.0)], over=o, inset=INSET,
                         rail=None, planks=dict(pitch=1.8, border=1.2), post="depot", arcade="depotbeam", skirt="platform",
                         pier_tex="plain", roof_edge="beadrosette", top=True)
    fkeep = slab(offset(base, 0.8 + 0.55 + 0.15) + offset(BAY.cs, 0.8 + 0.55 + 0.15), -1, ZF + 1.3)
    deck = PP["deck"] - fkeep
    kit.add("PLATFORM-deck", "PorchDeck", deck, P=print_flip(), group="porch", render=FT.plank_zones(deck, H_floor, "Planks", "PorchDeck"))
    main_keep = union([p.solid for p in kit.parts if p.name == "WALLS" or p.name.startswith("CORNICE")])
    keep = main_keep + union(ins_keep) + fnd
    res = FT.add_porch_top(kit, "PLATFORM", PP, keep, "Cream", "Cream", tin="custom", group="porch")
    zs = res["ptop"] - 0.8
    outer = [(-o, -PD - o), (W + o, -PD - o), (W + o, 3.0), (-o, 3.0)]
    pr, pr_tex = R.hip_roof([(outer, [0, 1, 3])], zs, S_CAN, 0.0, texture="octabutt", tex_kw=dict(pitch=1.7, wtab=2.4, d=0.35), zlo=zs)
    proof = ((pr + pr_tex) ^ slab(poly(outer), zs, zs + 12.0)) - main_keep - union(ins_keep)
    kit.add("PLATFORM-roof", "Green", max(proof.decompose(), key=lambda m_: m_.volume()), group="porch")
    for k, (sm, A) in enumerate(PP["steps"]):
        kit.add(f"PLATFORM-steps-{k}", "Stone", sm.transform(A) - fkeep - deck, group="porch")
    FT.key_into(kit, "PLATFORM-steps-0", ["PLATFORM-deck"], (1, 0, 0), depth=0.8, conform=True)
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "millbrook")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:80]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "millbrook.npz"))
    import json
    json.dump({"materials": {k: [h, r, 0.0] for k, (h, r) in PALETTE.items()}, "views": VIEWS},
              open(os.path.join(OUT, "palette.json"), "w"), indent=1)
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))

"""MX Tower: an original HO-scale (1:87.1) interlocking (signal) tower, building 68 (the railroad
and town batch).

A two-storey interlocking tower of about 1896: the relay room below in red brick whose every
fifth course is raked back, on a scored concrete plinth; the operating floor above in narrow
beaded boards framed by rails, cream with brown trim, with three wide windows of sliding
six-light sashes watching the tracks and another on the east end, MX on a call-letter board on
the west; a boxed outside stair climbs the back to a landing at the operator's door. A hip of
tapered slates on deep eaves. Cornices of a lever frame over signal wires on pulleys (the floor
joint) and of semaphores over the same wires, on knee braces (the eave).

usage: python3 -m hoarch.buildings.mxtower [check] [export]
"""
import os
import sys
import time

import numpy as np

from hoarch.core import box, offset, slab, union
from hoarch import cornice as CO, gables as G, openings as O, roof as R, town as TN
from hoarch.kit import Kit
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, stacked_shells

NAME = "MX Tower"
COLORS = {"Brick": "#8E3A2C", "Cream": "#E8DDC0", "Brown": "#5A3A28", "Slate": "#505860", "Concrete": "#A9A59C",
          "Windows_Doors": "#E8DDC0"}
RENDER_MAT = {"Brick": "brick", "Cream": "siding", "Brown": "brown", "Slate": "roof", "Concrete": "stone",
              "Windows_Doors": "trim", "Door": "door", "Glass": "glass", "Letters": "brown"}
PALETTE = {"brick": ("#8E3A2C", 0.9), "siding": ("#E8DDC0", 0.6), "brown": ("#5A3A28", 0.6), "roof": ("#505860", 0.8),
           "stone": ("#A9A59C", 0.9), "trim": ("#EFE7D2", 0.5), "door": ("#5A3A28", 0.6)}
VIEWS = {"hero": [-34, 14, 60, 0.95, [0, 0, 0]], "front": [0, 6, 70, 0.92, [0, 0, 0]], "rear": [150, 16, 60, 0.95, [0, 0, 0]],
         "right": [60, 12, 60, 0.95, [0, 0, 0]]}

# ------------------------------------------------------------------ cornices (unique to MX Tower)
LEDGE = 1.4
JOINT = dict(pitch=10.0, margin=3.0, layers=[
    dict(kind="frieze", h=4.2, b=1.2, orn="levers", role="Brown"),
    dict(kind="course", h=1.6, b=1.4, orn="pulleys", role="Cream"),
    dict(kind="crown", h=2.0, b=1.4, P=3.4, orn="ogee_fillet", role="Brown")])
EAVE = dict(pitch=10.0, margin=3.5, layers=[
    dict(kind="frieze", h=4.8, b=1.2, orn="semaphores", role="Brown"),
    dict(kind="course", h=1.6, b=1.4, orn="pulleys", role="Cream"),
    dict(kind="bed", h=2.4, b=1.4, P=8.0, role="Cream", brackets=dict(style="towerknee", t=1.6, reach=0.5)),
    dict(kind="crown", h=2.0, b=1.4, P=8.4, orn="cavetto", role="Brown")])
RJ = round((LEDGE + 0.4 + CO.band_height(JOINT)) / 0.2) * 0.2
HE = CO.band_height(EAVE)

# ------------------------------------------------------------------ levels and plan
ZF = 4.0
S1 = ZF + 32.0
ZE = S1 + RJ + 28.0
ZW = round((ZE + HE) / 0.2) * 0.2
FASCIA = 1.4
Z_EAVE = ZW + FASCIA
D_EAVE = 9.0
S_MAIN = 0.6
W, D = 64.0, 40.0
XC, YC = W / 2, D / 2
MAIN = Block("main", [(0, 0), (W, 0), (W, D), (0, D)], ZF, ZW)
BLOCKS = [MAIN]
V1 = 9.0
V2 = S1 + RJ + 4.0 - ZF
FLOOR2 = S1 + RJ + 0.4                             # the operating floor (the door's sill)
ST_X0, ST_RUN, ST_LAND, ST_W = 3.0, 34.0, 10.0, 7.0
SIGN_V, SIGN_L, SIGN_H = V2 + 4.0, 18.0, 8.0


def _openings():
    L = []

    def add(x, y, v0, sp, name, kind="window"):
        e, u = MAIN.locate(x, y)
        L.append(Opening(MAIN, e, u, v0, sp, name, kind))

    rel = TN.window_relay(8.0, 13.0)
    opw = TN.window_operator(14.0, 16.0)
    for x in (13.0, 51.0):
        add(x, 0.0, V1, rel, f"S{x:.0f}")
    add(XC, 0.0, 0.4, TN.door_tower_upper(9.0, 20.0), "relay-door", "door")
    for x in (13.0, XC, 51.0):
        add(x, 0.0, V2, opw, f"S{x:.0f}-2")
    add(W, YC, V1, rel, "E")
    add(W, YC, V2, opw, "E-2")
    add(0.0, YC, V1, rel, "W")
    add(ST_X0 + ST_RUN + ST_LAND / 2, D, FLOOR2 - ZF, TN.door_tower_upper(9.0, 20.0), "operator-door", "door")
    add(56.0, D, V1, rel, "N56")
    return L


OPENINGS = _openings()


def _skin(f, b, reg):
    reg = reg - TN.rect(-1, ZE - LEDGE - 0.6 - b.z0, f.L + 1, 999)
    if np.allclose(MAIN.facades()[3].n, f.n):
        reg = reg - TN.rect(f.L / 2 - SIGN_L / 2 - 0.3, SIGN_V - 0.3, f.L / 2 + SIGN_L / 2 + 0.3, SIGN_V + SIGN_H + 0.3)
    lo = reg ^ TN.rect(-1, -50, f.L + 1, S1 - b.z0)
    hi = reg ^ TN.rect(-1, S1 + RJ - b.z0, f.L + 1, 999)
    out = TN.brick_raked(lo, datum=0.0)
    if not hi.is_empty():
        out = out + TN.boards_panelled(hi, datum=0.0, rails=(V2 - 1.6, V2 + 19.4))
    return out


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    base = MAIN.cs
    undress = [slab(offset(base, 10.0), ZE - LEDGE - 0.6, ZW + 0.01)]
    st = stacked_shells(BLOCKS, OPENINGS, [S1], t=3.0, corners="none", siding=_skin,
                        prof=CO.joint_profile(RJ, LEDGE), belt_blocks=None, water_table=False, undress=undress)
    kit.add("WALLS-1", "Brick", st["shells"][0] - lip_keep(base, 3.0, ZF, 1.2), group="walls")
    kit.add("JOINT", "Brown", st["rings"][0], group="walls")
    w2 = st["shells"][1] + _corbel(base, 3.0, ZW) + lip_ring(base, 3.0, ZW) + CO.ledge(MAIN.pts, ZE, LEDGE)
    kit.add("WALLS-2", "Cream", w2, group="walls")
    rings, _ = CO.level(st["outlines"][0], S1 + LEDGE + 0.4, JOINT)
    CO.add_level(kit, rings, "CORNICE-J", "cornice")
    rings, _ = CO.level(MAIN.pts, ZE, EAVE)
    CO.add_level(kit, rings, "CORNICE-E", "cornice")
    fnd = foundation(BLOCKS, 0.0, ZF, style="scoredconcrete")
    kit.add("FOUNDATION", "Concrete", fnd, group="foundation")
    ins_keep = []
    for op in OPENINGS:
        A = op.local_frame()
        sp = op.spec
        b = sp["cut"].bounds()
        key = "DOOR" if op.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, "Windows_Doors", "Door" if op.kind == "door" else "Windows_Doors", "Glass")
        part = kit.add(f"{key}-{op.name}", "Windows_Doors", world, P=P,
                       key=f"{key}-{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}", group="inserts", render=zones)
        ins_keep.append(part.solid)
    f = MAIN.facades()[3]
    A = f.A.copy()
    A[:, 3] = f.world(f.L / 2, SIGN_V, 0.0)
    sb, letters = TN.sign_tower("MX", SIGN_L, SIGN_H, cap=5.0)
    kit.add("SIGN", "Cream", sb.transform(A), P=np.column_stack([np.vstack([A[:, 0], A[:, 1], A[:, 2]]), np.zeros(3)]),
            group="walls", render=[("Cream", (sb - letters).transform(A)), ("Letters", letters.transform(A))])
    print("walls + cornices + inserts", round(time.time() - t0, 1))

    # --- the hip roof of tapered slates
    pieces = [(MAIN.pts, [0, 1, 2, 3], S_MAIN)]
    rf = G.gabled_roof(pieces, Z_EAVE, D_EAVE, [], texture="tapered", tex_kw=dict(pitch=1.6, wtab=2.2, d=0.4),
                       inner_cs=offset(base, -3.0), fascia=FASCIA, hollow=2.6)
    roof = rf["body"] + rf["tex"]
    zr = Z_EAVE + S_MAIN * (D / 2 + D_EAVE)
    corners = [(-D_EAVE, -D_EAVE), (W + D_EAVE, -D_EAVE), (W + D_EAVE, D + D_EAVE), (-D_EAVE, D + D_EAVE)]
    ends = [(D / 2, YC), (W - D / 2, YC), (W - D / 2, YC), (D / 2, YC)]
    roof = roof + G.ridge_cap((D / 2, YC), (W - D / 2, YC), zr, S_MAIN, ZW, half=1.2, up=0.7)
    roof = roof + union([G.hip_cap((c[0], c[1], Z_EAVE), (e[0], e[1], zr), half=1.2, up=0.7, drop=1.6) for c, e in zip(corners, ends)])
    roof = (roof - lip_keep(base, 3.0, ZW)).trim_by_plane([0, 0, 1.0], Z_EAVE - FASCIA)
    kit.add("ROOF", "Slate", roof, group="roof")
    # --- the outside stair up the back to the operator's door, printed lying on its outer stringer
    rise = FLOOR2 - 0.2
    stair = TN.stair_tower(rise, ST_RUN, ST_W, ST_LAND)
    A = np.column_stack([(0.0, 1.0, 0.0), (0.0, 0.0, 1.0), (1.0, 0.0, 0.0), (ST_X0, D + 0.9, 0.0)]).astype(float)
    belt = union([p.solid for p in kit.parts if p.name == "JOINT" or p.name.startswith("CORNICE-J")])
    world = stair.transform(A) - fnd - union(ins_keep) - belt          # notched round the storey cornice
    Rp = np.vstack([[0.0, 0.0, 1.0], [0.0, 1.0, 0.0], [-1.0, 0.0, 0.0]])
    kit.add("STAIR", "Brown", world, P=np.column_stack([Rp @ A[:, :3].T, np.zeros(3)]), group="stair")
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "mxtower")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:80]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "mxtower.npz"))
    import json
    json.dump({"materials": {k: [h, r, 0.0] for k, (h, r) in PALETTE.items()}, "views": VIEWS},
              open(os.path.join(OUT, "palette.json"), "w"), indent=1)
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))

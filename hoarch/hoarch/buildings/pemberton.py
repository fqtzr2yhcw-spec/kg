"""The Pemberton Block -- an original HO-scale (1:87.1) three-storey brick commercial block, 1868.

A Main Street dry-goods store: a cast-iron storefront (fluted columns, panelled bulkheads,
display windows under a band of prism-glass transom lights) with a recessed entry, a side
door with its street number in the transom for the stairs to the upper floors, a sign band
with raised lettering under a small cornice, and a stone sill course. The upper front is in
English bond with rowlock arches over the second-storey windows, a soldier course, stone
lintels over the third storey and brick piers at the ends, and a corbel table under a
two-layer top cornice: a panelled frieze with bracket tails, and a pressed-metal cap on
brackets with dentils. The name-and-date tablet stands on the parapet. The sides are party
walls in running bond; the flat roof drops inside the walls onto a ledge, with a roof hatch
and a party-wall chimney.

Colour comes from the part split (see storefront.py): the storefront and caps in iron, the
sign printed black with a filament change for gilt letters, a cream frieze, the brick,
granite and roof. Everything on the front is applied trim printed face-up.

usage: python3 -m hoarch.buildings.pemberton [check] [export]
"""
import os
import sys
import time

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import arch_cs, box, cs_union, inv34, offset, rect, slab, union
from hoarch import openings as O, skins as SK, storefront as SF, trimwork as TW
from hoarch.kit import Kit
from hoarch.ornament import ext
from hoarch.shell import Block, Opening, _corbel, foundation, stacked_shells

NAME = "Pemberton Block"
COLORS = {"Brick": "#9A4A32", "Granite": "#8C8A84", "Iron": "#2F4A3A", "Sign": "#1E1E1E", "Cream": "#E6D9BC",
          "Roof": "#3A3A3C", "Windows_Doors": "#E6D9BC"}
RENDER_MAT = {"Brick": "brick", "Granite": "stone", "Iron": "iron", "Sign": "sign", "Gilt": "gilt", "Cream": "trim",
              "Roof": "roof", "Windows_Doors": "trim", "Sash": "sash", "Door": "door", "Glass": "glass"}

# ------------------------------------------------------------------ levels (v from the block base)
ZF = 4.4                  # granite plinth
SF_H = 46.0               # storefront opening
SIGN_V, SIGN_H = SF_H, 6.4
CAP1_V = SIGN_V + SIGN_H  # the store cornice
CAP1_PROF = [(0.0, 0.0), (1.4, 0.0), (1.4, 0.6), (1.6, 0.6), (1.6, 1.8), (3.0, 1.8), (3.0, 2.4), (3.2, 2.6),
             (3.4, 3.0), (3.4, 3.4), (0.0, 3.4)]
S1 = ZF + CAP1_V + 3.4    # storey joint: the sill course sits right on the store cornice
RH = 4.4
V2 = S1 - ZF + RH + 5.0   # second-storey windows
W2, H2 = 10.0, 24.0
VS = V2 + H2 + 5.8        # soldier course
W3, H3 = 10.0, 21.0
V3 = VS + 2.4 + 3.0       # third-storey windows
VC = V3 + H3 + 2.8 + 2.0  # corbel table
VF = VC + 3.2             # frieze band
FR_H = 6.4
VK = VF + FR_H            # cornice cap
CAP2_PROF = [(0.0, 0.0), (1.6, 0.0), (1.6, 0.8), (1.8, 0.8), (1.8, 2.8), (4.0, 2.8), (4.0, 3.6), (4.2, 3.7),
             (4.5, 4.0), (4.6, 4.4), (4.8, 4.8), (4.8, 5.2), (0.0, 5.2)]
ZP = ZF + VK + 5.2        # parapet top
ZR = ZF + VC - 1.2        # roof ledge (the deck sits on it, behind the corbel table)
T = 3.0

# ------------------------------------------------------------------ plan
X1, Y1 = 128.0, 150.0
MAIN = Block("main", [(0, 0), (X1, 0), (X1, Y1), (0, Y1)], ZF, ZP)
BLOCKS = [MAIN]
SF_W = 52.0              # storefront width
SHOPS = ((30.0, "DRY GOODS", ""), (98.0, "BOOTS & SHOES", "-2"))    # storefront centre, sign, part suffix
DOOR_U = X1 / 2           # the street door to the upper floors, between the two shops
WIN_U = (16.0, 40.0, 64.0, 88.0, 112.0)
PIER = 3.0                # end piers on the upper front


def _front_skin(reg):
    """English bond with rowlock arches over the second storey, a soldier course, end piers
    standing proud and a corbel table under the frieze."""
    L = X1
    parts, keep = [], []
    for u in WIN_U:
        band, rel = SK.brick_arch(u, V2, W2, H2, 2.0, casing=0.6)
        keep.append(band)
        parts.append(rel)
    keep.append(rect(-1, VS, L + 1, VS + 2.4))
    parts.append(SK.soldier_band(reg, VS, bw=1.0))
    out, rel = SK.corbel_courses(PIER, L - PIER, VC)
    keep.append(out)
    parts.append(rel)
    v_up = S1 - ZF + RH
    for u0, u1 in ((0.0, PIER), (L - PIER, L)):
        pier = rect(u0, v_up, u1, VF) ^ reg
        keep.append(pier)
        parts.append(M.extrude(pier, 0.6))
        parts.append(SK.brick_bond(pier, "running", bl=1.5, bh=0.8, d=0.25, datum=1.8,
                                   uoff=0.75 if u0 else 0.0).translate([0, 0, 0.58]))
    parts.append(SK.brick_bond(reg - cs_union(keep), "english", datum=1.8))
    return union(parts) ^ ext(reg, -1.0, 5.0)


def _siding(f, b, reg):
    if f.n[1] < -0.3:
        return _front_skin(reg)
    tex = SK.brick_bond(reg, "running", bl=2.4, bh=0.8, d=0.25, datum=1.8)
    if f.n[1] > 0.3:                                  # the rear: one-ring arches over the windows
        arches = []
        for o in OPENINGS:
            if o.facade.n[1] > 0.3 and o.kind == "window":
                sp = o.spec
                w = sp["cut"].bounds()[2] - sp["cut"].bounds()[0]
                h = sp["cut"].bounds()[3]
                band, rel = SK.brick_arch(o.u, o.v0, w, h, 1.6, casing=0.6, rings=1)
                arches.append((band, rel))
        if arches:
            tex = SK.brick_bond(reg - cs_union([a for a, _ in arches]), "running", bl=2.4, bh=0.8, d=0.25, datum=1.8)
            tex = tex + (union([r for _, r in arches]) ^ ext(reg, -1.0, 5.0))
    return tex


def _openings():
    L = []

    def add(x, y, v0, sp, name, kind="window"):
        e, u = MAIN.locate(x, y)
        L.append(Opening(MAIN, e, u, v0, sp, name, kind))

    sf = SF.storefront(SF_W, SF_H, entry=14.0, col=2.4, style="fluted", bulk=7.2, transom=6.4, lite=2.4)
    for u, _, sfx in SHOPS:
        add(u, 0, 0.0, sf, "storefront" + sfx, "door")
    add(DOOR_U, 0, 0.0, SF.door_commercial(10.0, 34.0, transom=5.0, leaf="four_panel", tstyle="number:112"),
        "street-door", "door")
    w2 = SF.window_commercial(W2, H2, rise=2.0, lites=(2, 2), sill=1.2)
    w3 = SF.window_commercial(W3, H3, rise=0, lites=(1, 1), sill=1.0, head="lintel")
    for u in WIN_U:
        add(u, 0, V2, w2, f"F{u:.0f}-2")
        add(u, 0, V3, w3, f"F{u:.0f}-3")
    # rear: two windows and the back door below, three windows on each floor above
    wr1 = SF.window_commercial(9.0, 22.0, rise=1.6, lites=(1, 1), rows=(1, 2), sill=1.0)
    wr2 = SF.window_commercial(9.0, 21.0, rise=1.6, lites=(1, 1), rows=(1, 1), sill=1.0)
    add(100.0, Y1, 0.0, SF.door_commercial(9.0, 30.0, transom=4.0, leaf="four_panel", tstyle="number:112", head=None),
        "back-door", "door")
    for x in (20.0, 44.0, 68.0):
        add(x, Y1, 12.0, wr1, f"R{x:.0f}-1")
    for x in (16.0, 40.0, 64.0, 88.0, 112.0):
        add(x, Y1, V2, wr2, f"R{x:.0f}-2")
        add(x, Y1, V3 + 1.0, wr2, f"R{x:.0f}-3")
    return L


OPENINGS = _openings()

# applied trim on the front (face-up parts): landings where the brick stops
APPLIED = [("SIGN" + sfx, u - SF_W / 2, SIGN_V, SF_W, SIGN_H) for u, _, sfx in SHOPS] + \
          [("CORNICE-store", 0.0, CAP1_V, X1, 3.4),
           ("FRIEZE", 0.0, VF, X1, FR_H),
           ("CORNICE-top", 0.0, VK, X1, 5.2)]


def _applied_openings():
    out = []
    for name, u0, v0, L, h in APPLIED:
        out.append(Opening(MAIN, 0, 0.0, 0.0, SF.applied(rect(u0, v0, u0 + L, v0 + h)), name, "trim"))
    return out


def _gilt(solid, A, level):
    """Render zones of a face-up part printed with one filament change at local w = ``level``:
    black below, gilt above."""
    hi = solid ^ box([-1e3, -1e3, level], [1e3, 1e3, 1e3])
    return [("Sign", (solid - hi).transform(A)), ("Gilt", hi.transform(A))]


def _upright(A):
    """Print transform for a part built in facade frame A that prints standing on its v = 0
    face (local v -> print z, local w -> print -y)."""
    R = np.array([[1.0, 0, 0], [0, 0, -1.0], [0, 1.0, 0]])
    return R @ inv34(A)


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    base = MAIN.cs
    trim_ops = _applied_openings()
    bprof, _ = TW.BELTS["sill"]
    st = stacked_shells(BLOCKS, OPENINGS + trim_ops, [S1], t=T, corners="none", siding=_siding, prof=bprof,
                        belt_blocks=None, water_table=False)
    walls_top = st["shells"][1] + _corbel(base, T, ZR)
    sfos = [o for o in OPENINGS if o.name.startswith("storefront")]
    posts = union([o.spec["posts"].transform(o.local_frame()) for o in sfos])   # brick posts behind the inner columns
    kit.add("WALLS-1", "Brick", st["shells"][0] + posts, group="walls")
    kit.add("SILL-COURSE", "Granite", st["rings"][0], group="walls")
    kit.add("WALLS-2", "Brick", walls_top, group="walls")

    # --- the storefront, its recessed entry and the street door
    entries = []
    for sfo in sfos:
        sfx = sfo.name[len("storefront"):]
        sp = sfo.spec
        world, P, zones = O.place(sp, sfo.local_frame(), "Iron", "Iron", "Glass")
        kit.add("STOREFRONT" + sfx, "Iron", world, P=P, key="STOREFRONT", group="storefront", render=zones)
        eu, ew, eh = sp["entry"]
        A = sfo.local_frame()
        Av = A.copy()
        Av[:, 3] = A[:, 3] + A[:, 0] * eu
        vest = SF.vestibule(ew, 7.0, eh, bulk=7.2, front=-T)         # behind the brick posts; granite threshold
        kit.add("VESTIBULE" + sfx, "Iron", vest.transform(Av), P=_upright(Av), key="VESTIBULE", group="storefront")
        entries.append((Av, np.array(vest.bounding_box())))
    for o in OPENINGS:
        if o.name.startswith("storefront"):
            continue
        s = o.spec
        b = s["cut"].bounds()
        key = "DOOR" if o.kind == "door" else "WIN"
        tag = f"{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}"
        world, P, zones = O.place(s, o.local_frame(), "Windows_Doors", "Door" if o.kind == "door" else "Sash", "Glass")
        kit.add(f"{key}-{o.name}", "Windows_Doors", world, P=P, key=f"{key}-{tag}-{o.v0:.0f}", group="inserts",
                render=zones)
    print("walls + storefront", round(time.time() - t0, 1))

    # --- granite plinth; a pad under the vestibule floor, the lip cut where the entry is
    fnd = foundation(BLOCKS, 0.0, ZF, style="plinth")
    for Av, vb in entries:
        pad = box([vb[0] + 0.2, -ZF, vb[2] + 0.2], [vb[3] - 0.2, 0.0, -T]).transform(Av)
        fnd = fnd + pad - box([vb[0] - 0.2, 0.0, vb[2] - 0.2], [vb[3] + 0.2, 2.0, -0.01]).transform(Av)
    kit.add("FOUNDATION", "Granite", fnd, group="foundation")

    # --- applied front trim: sign band + store cornice (the lower double eave), and the
    # frieze + cornice cap at the top (the upper double eave), each printed face-up
    f = MAIN.facades()[0]
    Af = f.A.copy()
    Af[:, 3] = f.world(0.0, 0.0, 0.0)

    def put(name, color, local, u0, v0, render=None, **kw):
        A_ = Af.copy()
        A_[:, 3] = f.world(u0, v0, 0.0)
        return kit.add(name, color, local.transform(A_), P=inv34(A_), group="front",
                       render=render(local, A_) if render else None, **kw)

    for u, text, sfx in SHOPS:
        sign = SF.sign_band(SF_W, SIGN_H, text, cap=3.4, board=1.0, frame=0.8, relief=0.4)
        put("SIGN" + sfx, "Sign", sign, u - SF_W / 2, SIGN_V, render=lambda m, A_: _gilt(m, A_, 1.0))
    cap1 = SF.cornice_cap(X1, CAP1_PROF, dentils=dict(v=0.6, h=1.0, d=2.2, tooth=0.6, gap=0.6))
    put("CORNICE-store", "Iron", cap1, 0.0, CAP1_V)
    bus = [1.5 + (X1 - 3.0) * k / 5 for k in range(6)]
    frieze = SF.frieze_band(X1, FR_H, board=1.2, panels=[(a + 2.5, b - 2.5) for a, b in zip(bus, bus[1:])],
                            tails=dict(us=bus, w=1.6, d=1.8, style="metal"))
    put("FRIEZE", "Cream", frieze, 0.0, VF)
    cap2 = SF.cornice_cap(X1, CAP2_PROF, dentils=dict(v=0.8, h=1.4, d=2.4, tooth=0.6, gap=0.6)) + \
        SF.bracket_row(X1, bus, 2.0, 3.8, 1.6, 2.8, style="metal")
    put("CORNICE-top", "Iron", cap2 ^ box([0.0, -1.0, 0.0], [X1, 6.0, 6.0]), 0.0, VK)
    print("front trim", round(time.time() - t0, 1))

    # --- coping on the walls, the name tablet on the parapet
    cop = slab(offset(base, 0.6) - offset(base, -T - 0.4), ZP, ZP + 0.8) + \
        slab(offset(base, 0.2) - offset(base, -T), ZP + 0.79, ZP + 1.2)
    kit.add("COPING", "Granite", cop, group="roof")
    tw, th = 40.0, 14.0
    rise = th * 0.35
    outline = arch_cs(-tw / 2, tw / 2, 0.0, th - rise, rise=rise, seg=48)
    tab = SF.name_tablet(tw, th, "PEMBERTON", "1868", cap=3.4, board=1.2, relief=0.4) + \
        ext(outline + rect(-tw / 2 - 2.4, 0.0, tw / 2 + 2.4, 2.4), -2.4, 0.01)        # a block behind it all
    At = Af.copy()
    At[:, 3] = f.world(X1 / 2, ZP + 1.2 - ZF, -1.0)
    kit.add("TABLET", "Cream", tab.transform(At), P=inv34(At), group="roof")

    # --- the roof: a deck on the ledge inside the walls, seams, a hatch; the chimney
    inner = offset(base, -T - 0.15)
    deck = slab(inner, ZR, ZR + 1.2)
    b = inner.bounds()
    seams = union([box([b[0] + 0.4, y - 0.3, ZR + 1.19], [b[2] - 0.4, y + 0.3, ZR + 1.4])
                   for y in np.arange(b[1] + 7.2, b[3] - 2.0, 7.2)])
    hx, hy = 84.0, 100.0
    hatch = union([box([hx - 4.5 - g, hy - 5.5 - g, z0], [hx + 4.5 + g, hy + 5.5 + g, z1])       # lid flares at 45 deg
                   for g, z0, z1 in ((0.0, ZR + 1.19, ZR + 2.8), (0.2, ZR + 2.79, ZR + 3.0), (0.4, ZR + 2.99, ZR + 3.4))])
    cw, cd = 20.0, 7.0
    cx, cy = T + 0.6 + cd / 2, 70.0
    pocket = box([cx - cd / 2 - 0.4, cy - cw / 2 - 0.4, ZR + 0.6], [cx + cd / 2 + 0.4, cy + cw / 2 + 0.4, ZR + 2.0])
    kit.add("ROOF", "Roof", deck + seams - pocket + hatch, group="roof")
    zc = ZR + 0.6
    ch = TW.chimney("party", w=cw, d=cd, h=round((ZP + 13.0 - zc) / 0.2) * 0.2).rotate([0, 0, 90]).translate([cx, cy, zc])
    kit.add("CHIMNEY", "Brick", ch, group="roof")
    print("roof", round(time.time() - t0, 1))
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "pemberton")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:40]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "pemberton.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))

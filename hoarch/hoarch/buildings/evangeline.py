"""The Evangeline -- an original HO-scale (1:87.1) Steamboat Gothic plantation house, 1858: the second
of the grand batch (houses 91 to 100, hoarch.grand), on the mansard batch's roof system
(hoarch.secondempire).

A sugar planter's house raised on a stuccoed ground storey ruled as ashlar in tall and short
courses, its main storey of twin-beaded lap, ivory trim and deep teal accents, wrapped on all
four sides by a gallery that reads like a riverboat's decks: a lower arcade of stuccoed arches on
square piers carrying a planked main gallery of slender Gothic colonnettes with crocket capitals,
lancet-arcade friezes with turned drops, onion balusters and a valance of lancets, its flat tin
roof a promenade deck behind a railing of lancets between pointed newels. Above the eave a
straight slated hip, banded with swallow-tailed slates and set with Gothic wall dormers (steep
gablets with notched bargeboards and fleur finials), stops at a flat crested deck behind star
cresting, and on the deck stands the pilot house: a glazed belvedere of lancet windows under its
own bracketed cornice and a concave tent roof with a crest, cresting and an onion finial. A
double horseshoe stair climbs to the front door; two domed cypress cisterns on octagonal brick
bases stand by the back corners; two stucco stacks end in feathered steamboat crowns.

- Main storey: floor-length lancet French windows with bar tracery (two sub-lancets and an
  oculus), crocketed hood moulds on carved stops with trefoil finials; the front door's lancet
  of tracery between clustered colonnettes under a crocketed ogee hood.
- Ground storey: six-over-six segmental sashes and fanlit doors under stucco voussoirs.
- Storey joint: an ivory row of stars, a teal frieze of crossed sugar canes, an ivory cyma.
- Eave: an ivory trefoil course, a teal frieze of cotton bolls, trefoil knee brackets and a
  teal reverse crown. The belvedere's eave: a blind lancet arcade with quatrefoils.
- Crests: an ivory quatrefoil chain under a teal stepped crown.

usage: python3 -m hoarch.buildings.evangeline [check] [export]
"""
import math
import os
import sys
import time

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import Facade, box, cs_union, inv34, offset, poly, rect, slab, union
from hoarch import cornice as CO, features as FT, grand as G, openings as O, roof as R, secondempire as SE
from hoarch.kit import Kit, print_flip
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, stacked_shells, wall_shell

NAME = "The Evangeline"
COLORS = {"Stucco": "#D9A77E", "Siding": "#A8C3B1", "Ivory": "#EFE7D3", "Teal": "#2F6467", "Roof": "#5B6670",
          "Iron": "#232528", "Brick": "#9A4B36", "Cypress": "#7A5A3E", "Planks": "#6F5034",
          "Windows_Doors": "#EFE7D3", "Addins": "#5B6670"}
RENDER_MAT = {"Stucco": "stucco", "Siding": "siding", "Ivory": "trim", "Teal": "accent", "Roof": "roof", "Iron": "iron",
              "Brick": "brick", "Cypress": "cypress", "Planks": "planks", "Windows_Doors": "trim", "Addins": "roof",
              "Sash": "sash", "Door": "door", "Glass": "glass"}
PALETTE = {"stucco": ["#D9A77E", 0.9, 0.0], "siding": ["#A8C3B1", 0.75, 0.0], "trim": ["#EFE7D3", 0.6, 0.0],
           "accent": ["#2F6467", 0.5, 0.0], "roof": ["#5B6670", 0.75, 0.0], "iron": ["#232528", 0.45, 0.3],
           "brick": ["#9A4B36", 0.85, 0.0], "cypress": ["#7A5A3E", 0.8, 0.0], "planks": ["#6F5034", 0.75, 0.0],
           "sash": ["#2B2A26", 0.45, 0.0], "door": ["#2F4F4A", 0.45, 0.0]}

# ------------------------------------------------------------------ cornices (unique to the Evangeline)
LEDGE = 1.4
JOINT = dict(pitch=14.0, margin=4.0, layers=[
    dict(kind="course", h=1.8, b=1.0, orn="starrow", role="Ivory"),
    dict(kind="frieze", h=5.2, b=1.2, orn="sugarcane", role="Teal"),
    dict(kind="crown", h=2.0, b=1.4, P=3.4, orn="cyma", role="Ivory")])
EAVE = dict(pitch=10.0, margin=4.0, layers=[
    dict(kind="course", h=1.6, b=1.0, orn="trefoilrow", role="Ivory"),
    dict(kind="frieze", h=6.0, b=1.2, orn="cottonbolls", role="Teal"),
    dict(kind="bed", h=2.6, b=1.4, P=6.8, role="Ivory", brackets=dict(style="trefoilknee", t=1.6, reach=0.6)),
    dict(kind="crown", h=2.6, b=1.4, P=7.6, orn="reverse", role="Teal")])
BELV_C = dict(pitch=9.0, margin=3.5, layers=[
    dict(kind="frieze", h=4.6, b=1.2, orn="lancetfoils", role="Teal"),
    dict(kind="bed", h=2.0, b=1.4, P=5.2, role="Ivory", brackets=dict(style="trefoilknee", t=1.4, reach=0.5)),
    dict(kind="crown", h=2.2, b=1.4, P=6.0, orn="ovolo", role="Ivory")])
CREST_COURSE = dict(h=2.6, b=0.6, orn=G.quatrefoilchain, role="Ivory")
CREST_CROWN = dict(h=2.4, P=3.4, kind="stepped", role="Teal", blocks=None)
RJ = round((LEDGE + 0.4 + CO.band_height(JOINT)) / 0.2) * 0.2
HE = CO.band_height(EAVE)
HB = CO.band_height(BELV_C)

# ------------------------------------------------------------------ levels (on the 0.2 mm grid)
ZF = 3.0
S1 = ZF + 28.0                  # the raised ground storey
H_FLOOR = S1 + RJ               # the main floor = the gallery floor
POST_H = 40.0
ZE = H_FLOOR + 50.0
ZW = ZE + HE
DK = EAVE["layers"][-1]["P"] + 0.2
RH = 24.0                       # the slated hip's rise to the deck
ZR1 = ZW + RH
D_TOP = round(DK - 1.6 - (RH - 1.2) / math.tan(math.radians(56.0)), 1)
ROOF = [(DK, ZW), (DK - 1.6, ZW + 1.2), (D_TOP, ZR1)]
SLATE = dict(pitch=1.8, wtab=2.2, d=0.4, shape=G.slate_swallowbands)
Z_ADD = ZW + 3.0
BELV_H = 24.0                   # the belvedere's walls, deck to eave

# ------------------------------------------------------------------ plan (mm; x east, y north, front = south)
W, D = 150.0, 104.0
XC, YC = W / 2, D / 2
MAIN = Block("main", [(0, 0), (W, 0), (W, D), (0, D)], ZF, ZW)
BLOCKS = [MAIN]
GD = 16.0                       # the gallery's depth, all round
INSET = 1.6
YM = YC                         # the front and back galleries meet halfway down each side
BX0, BX1, BY0, BY1 = XC - 23.0, XC + 23.0, YC - 16.0, YC + 16.0
CHIMS = [(22.0, YC), (W - 22.0, YC)]
CISTERNS = [(-GD - 13.0, D - 12.0), (W + GD + 13.0, D - 12.0)]


def _walls(f, b, reg):
    """Tabled stucco below the joint, twin-bead lap above; nothing in the eave band."""
    reg = reg - rect(-1, ZE - b.z0, f.L + 1, 999)
    lo = reg ^ rect(-1, -100, f.L + 1, S1 - b.z0)
    hi = reg ^ rect(-1, S1 + RJ - b.z0, f.L + 1, 999)
    out = []
    if not lo.is_empty():
        out.append(G.stucco_tabled(lo, datum=0.0))
    if not hi.is_empty():
        out.append(G.lap_twinbead(hi, datum=S1 + RJ - b.z0 + 0.4))
    return union(out) if out else M()


def _openings():
    L = []

    def add(x, y, v0, sp, name, kind="window"):
        e, u = MAIN.locate(x, y)
        L.append(Opening(MAIN, e, u, v0, sp, name, kind))

    gw, gd = G.window_evangeline_ground(), G.door_evangeline_ground()
    mw, fd, bd = G.window_evangeline_main(), G.door_evangeline(), G.door_evangeline_back()
    VG = 6.0
    VM = H_FLOOR - ZF + 0.8                       # the main storey's sills bear on the joint's crown
    for y_, tag in ((0.0, "S"), (D, "N")):
        for x in (20.0, 46.0, 104.0, 130.0):
            add(x, y_, VG, gw, f"{tag}{x:.0f}-g")
            add(x, y_, VM, mw, f"{tag}{x:.0f}-m")
        add(XC, y_, 0.8, gd, f"{tag}-ground-door", "door")
    add(XC, 0.0, VM, fd, "front-door", "door")
    add(XC, D, VM, bd, "back-door", "door")
    for x_, tag in ((0.0, "W"), (W, "E")):
        for y in (30.0, 74.0):
            add(x_, y, VG, gw, f"{tag}{y:.0f}-g")
        for y in (18.0, YC, 86.0):
            add(x_, y, VM, mw, f"{tag}{y:.0f}-m")
    return L


OPENINGS = _openings()
ADDINS = [(40.0, 0.0), (XC, 0.0), (110.0, 0.0), (40.0, D), (XC, D), (110.0, D), (0.0, YC), (W, YC)]


def _frame_on(block, x, y, z, w0):
    e, u = block.locate(x, y)
    f = block.facades()[e]
    A = f.A.copy()
    A[:, 3] = f.world(u, z - block.z0, w0)
    return A


def _addins(kit, block, places, prof, z_sill, sp, tag):
    pl = [SE.addin_place(sp, prof, z_sill) for _ in places]
    depth = max(d for _, d in pl)
    keeps, flashes = [], []
    for k, ((x, y), (w0, _)) in enumerate(zip(places, pl)):
        A = _frame_on(block, x, y, z_sill, w0)
        a = SE.addin(sp, depth)
        keeps.append(a["keep"].transform(A))
        flashes.append(a["flash"].transform(A))
        zones = [("Glass", a["glass"].transform(A)), ("Roof", (a["plug"] - a["glass"]).transform(A)),
                 ("Ivory", a["frame"].transform(A))]
        kit.add(f"{tag}-{k}", "Addins", a["solid"].transform(A), P=inv34(A), change=(round(depth, 1), "Ivory"),
                key=tag, group="addins", render=zones)
    print(tag, "plug", depth)
    return union(keeps), union(flashes)


def _deck_plate(C, z):
    dcs = poly(R.offset_path(C["path"], -1.6))
    x0, y0, x1, y1 = dcs.bounds()
    seams = cs_union([rect(x - 0.25, y0, x + 0.25, y1) for x in np.arange(x0 + 2.6, x1, 5.2)]) ^ dcs
    return C["deck"] + slab(seams, z - 0.01, z + 0.4)


def _inset_chain(pts, d):
    """An open chain of points moved ``d`` to its left (inward for a CCW yard edge)."""
    P = [np.asarray(p, float) for p in pts]
    n = len(P)
    nrm = []
    for i in range(n - 1):
        t = (P[i + 1] - P[i]) / np.linalg.norm(P[i + 1] - P[i])
        nrm.append(np.array([-t[1], t[0]]))
    out = [P[0] + d * nrm[0]]
    for i in range(1, n - 1):
        a0, a1 = P[i - 1] + d * nrm[i - 1], P[i] + d * nrm[i - 1]
        b0, b1 = P[i] + d * nrm[i], P[i + 1] + d * nrm[i]
        da, db = a1 - a0, b1 - b0
        den = da[0] * db[1] - da[1] * db[0]
        s = ((b0[0] - a0[0]) * db[1] - (b0[1] - a0[1]) * db[0]) / den
        out.append(a0 + da * s)
    out.append(P[-1] + d * nrm[-1])
    return [tuple(p) for p in out]


def _gallery(front):
    """One half of the four-sided gallery (a U): across the front (or back) and halfway down
    each side, where it meets the other half. Returns (pts, runs, outer chain)."""
    if front:
        pts = [(-GD, YM), (-GD, -GD), (W + GD, -GD), (W + GD, YM), (W, YM), (W, 0.0), (0.0, 0.0), (0.0, YM)]
    else:
        pts = [(W + GD, YM), (W + GD, D + GD), (-GD, D + GD), (-GD, YM), (0.0, YM), (0.0, D), (W, D), (W, YM)]
    a, b, c, d = pts[:4]
    Ls, Lf = YM + GD, W + 2 * GD
    side_a = [2.6, Ls * 0.36, Ls * 0.68, Ls - INSET]
    side_b = [Ls - u for u in reversed(side_a)]
    across = [INSET + (Lf - 2 * INSET) * k / 9 for k in range(10)]
    runs = [dict(a=a, b=b, posts=side_a), dict(a=b, b=c, posts=across), dict(a=c, b=d, posts=side_b)]
    return pts, runs, [a, b, c, d]


def _gallery_deck(pts, runs, keep):
    """The gallery floor in one piece, printed upside down: planks (the first layers, one
    filament change), an edge frame and joists, and under its outer edges the lower arcade of
    stuccoed arches, a pier under every post. Sockets take the posts' pegs."""
    gcs = poly(pts)
    planks = FT.porch_planks(pts, [0, 1, 2], H=H_FLOOR, pitch=1.6, crack=0.25, border=1.4, along=(0.0, 1.0))
    ring = gcs - offset(gcs, -2.4)
    frame = slab(ring, H_FLOOR - 4.4, H_FLOOR - 1.0)
    b_ = gcs.bounds()
    joists = union([box([x - 0.5, b_[1], H_FLOOR - 3.0], [x + 0.5, b_[3], H_FLOOR - 1.0])
                    for x in np.arange(b_[0] + 3, b_[2], 6.0)]) ^ slab(gcs, -10, 999)
    arc, where = [], []
    for r in runs:
        f = Facade(r["a"], r["b"], 0.0)
        arc.append(f.place(G.arcade_evangeline(f.L, r["posts"], H_FLOOR - 4.39, t=3.2)))
        for u in r["posts"]:
            p = f.p0 + f.u * u - f.n * INSET
            if not any(np.allclose(p, q, atol=0.05) for q in where):
                where.append(p)
    socks = union([box([p[0] - 1.0, p[1] - 1.0, H_FLOOR - 2.0], [p[0] + 1.0, p[1] + 1.0, H_FLOOR + 1.0]) for p in where])
    return (planks + frame + joists + union(arc)) - socks - keep


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    allcs = MAIN.cs
    undress = [slab(offset(allcs, 8.0), ZE - LEDGE - 0.6, ZW + 0.01)]
    st = stacked_shells(BLOCKS, OPENINGS, [S1], t=3.0, corners="evangeline", clear=[lip_keep(allcs, 3.0, ZF, 1.2)],
                        siding=_walls, prof=CO.joint_profile(RJ, LEDGE), belt_blocks=None, water_table=False,
                        undress=undress)
    kit.add("WALLS-1", "Stucco", st["shells"][0], group="walls")
    kit.add("JOINT", "Siding", st["rings"][0], group="walls")
    walls2 = st["shells"][1] + CO.ledge(MAIN.pts, ZE, LEDGE)
    kit.add("WALLS-2", "Siding", walls2, group="walls")
    rings, _ = CO.level(st["outlines"][0], S1 + LEDGE + 0.4, JOINT)
    CO.add_level(kit, rings, "CORNICE-J", "cornice")
    rings, _ = CO.level(MAIN.pts, ZE, EAVE)
    CO.add_level(kit, rings, "CORNICE-E", "cornice")
    kit.add("FOUNDATION", "Stucco", foundation(BLOCKS, 0.0, ZF, style="plinthtorus"), group="foundation")
    inserts = []
    for o in OPENINGS:
        A = o.local_frame()
        sp = o.spec
        b = sp["cut"].bounds()
        tag = f"{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}"
        key = "DOOR" if o.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, "Ivory", "Door" if o.kind == "door" else "Sash", "Glass")
        inserts.append(kit.add(f"{key}-{o.name}", "Windows_Doors", world, P=P,
                               key=f"{key}-{tag}-{o.v0 > 20}", group="inserts", render=zones))
    print("walls + cornices + inserts", round(time.time() - t0, 1))

    # --- the slated hip (upside down) with its dormers, the crest, the deck, stacks, cresting
    mans, mtex, inner = R.mansard(MAIN.pts, ROOF, t=2.6, tex=SLATE)
    mk, mf = _addins(kit, MAIN, ADDINS, ROOF, Z_ADD, G.addin_evangeline(), "ADDIN")
    C = SE.crest_ring(MAIN.pts, D_TOP, ZR1, D_TOP - inner(ZR1), CREST_COURSE, CREST_CROWN)
    kit.add("ROOF", "Roof", (mans + (mtex - mf)) - mk - C["groove"], P=print_flip(), group="roof")
    kit.add("CREST", "Teal", C["solid"], P=print_flip(), change=C["change"], group="roof", render=C["zones"])
    zdeck = C["z_top"]
    zdeck_g = math.floor(zdeck / 0.2 + 1e-6) * 0.2
    ZBE = zdeck_g + BELV_H
    ZBW = ZBE + HB
    BELV = Block("belvedere", [(BX0, BY0), (BX1, BY0), (BX1, BY1), (BX0, BY1)], zdeck, ZBW)
    pads = union([box([x - 5.4, y - 5.0, zdeck - 0.6], [x + 5.4, y + 5.0, zdeck + 1]) for x, y in CHIMS])
    kit.add("ROOF-deck", "Roof", _deck_plate(C, zdeck) - pads - BELV.solid(grow=0.3, dz0=-0.02), group="roof")
    for k, (x, y) in enumerate(CHIMS):
        kit.add(f"CHIMNEY-{k}", "Stucco", G.chimney_evangeline(9.0, 8.0, 26.0).translate([x, y, zdeck - 0.6]),
                key="CHIMNEY", group="roof")
    for i, seg, A, L in SE.cresting_strips(C["path"], zdeck, C["rail"], SE.printable(G.fence_evangeline), 7.2):
        for j, piece in enumerate(seg.decompose()):
            if piece.volume() > 3.0:
                kit.add(f"CREST-iron-{i}{chr(97 + j)}", "Iron", piece, P=inv34(A), key=f"CREST-iron-{round(L, 1)}", group="roof")
    print("roof", round(time.time() - t0, 1))

    # --- the belvedere (the pilot house): walls, lancet windows, cornice, a concave tent, crest
    bopen = []
    bw = G.window_evangeline_belv()
    for x in (XC - 11.0, XC + 11.0):
        for y in (BY0, BY1):
            e, u = BELV.locate(x, y)
            bopen.append(Opening(BELV, e, u, 3.0, bw, f"B{x:.0f}-{y:.0f}"))
    for x in (BX0, BX1):
        e, u = BELV.locate(x, YC)
        bopen.append(Opening(BELV, e, u, 3.0, bw, f"B{x:.0f}-{YC:.0f}"))

    def _bskin(f, b, reg):
        reg = reg - rect(-1, ZBE - b.z0 - LEDGE - 0.6, f.L + 1, 999)
        return G.lap_twinbead(reg, datum=1.0) if not reg.is_empty() else M()
    bshell = wall_shell([BELV], bopen, t=2.4, belt=None, belt_trim=False, corners="evangeline", siding=_bskin,
                        water_table=False, undress=[slab(offset(BELV.cs, 6.0), ZBE - LEDGE - 0.6, ZBW + 0.01)])
    blip = _corbel(BELV.cs, 2.4, ZBW) + lip_ring(BELV.cs, 2.4, ZBW)
    kit.add("BELV-walls", "Siding", bshell + CO.ledge(BELV.pts, ZBE, LEDGE, t=2.4) + blip, group="belvedere")
    for o in bopen:
        A = o.local_frame()
        world, P, zones = O.place(o.spec, A, "Ivory", "Sash", "Glass")
        inserts.append(kit.add(f"WIN-{o.name}", "Windows_Doors", world, P=P, key="WIN-belv", group="belvedere", render=zones))
    rings, _ = CO.level(BELV.pts, ZBE, BELV_C)
    CO.add_level(kit, rings, "CORNICE-B", "belvedere")
    DB = BELV_C["layers"][-1]["P"] + 0.2
    tent, z_, d_ = [(DB, ZBW)], ZBW, DB
    for dd, dz in ((2.0, 0.8), (1.8, 1.0), (1.6, 1.2), (1.4, 1.4), (1.2, 1.6), (1.0, 1.8), (0.8, 2.2)):
        d_, z_ = d_ - dd, z_ + dz
        tent.append((round(d_, 2), round(z_, 2)))
    tb, ttx, tin = R.mansard(BELV.pts, tent, t=2.6, tex=dict(pitch=1.6, wtab=2.0, d=0.35, shape="square"))
    BC = SE.crest_ring(BELV.pts, tent[-1][0], tent[-1][1], tent[-1][0] - tin(tent[-1][1]), CREST_COURSE, CREST_CROWN)
    kit.add("BELV-roof", "Roof", (tb + ttx) - lip_keep(BELV.cs, 2.4, ZBW) - BC["groove"], group="belvedere")
    kit.add("BELV-CREST", "Teal", BC["solid"], P=print_flip(), change=BC["change"], group="belvedere", render=BC["zones"])
    bz = BC["z_top"]
    kit.add("BELV-deck", "Roof", _deck_plate(BC, bz), group="belvedere")
    for i, seg, A, L in SE.cresting_strips(BC["path"], bz, BC["rail"], SE.printable(G.fence_evangeline), 6.4):
        kit.add(f"BELV-iron-{i}", "Iron", seg, P=inv34(A), key=f"BELV-iron-{round(L, 1)}", group="belvedere")
    kit.add("BELV-finial", "Iron", G.finial_evangeline(14.0).translate([XC, YC, bz + 0.39]), group="belvedere")
    print("belvedere", round(time.time() - t0, 1))

    # --- the gallery: two U halves (front, back), each a planked deck on its lower arcade
    # (upside down) and a one-piece top of colonnettes, lace, railings and the promenade deck
    parts = {p_.name: p_ for p_ in kit.parts}
    bld_keep = union([parts[n].solid for n in ("WALLS-1", "JOINT", "WALLS-2", "FOUNDATION")] +
                     [p_.solid for p_ in kit.parts if p_.name.startswith("CORNICE-J") or p_.name.startswith("CORNICE-E")])
    ins_keep = union([box([b[0] - 0.2, b[1] - 0.2, math.floor((b[2] - 0.2) / 0.2) * 0.2],
                          [b[3] + 0.2, b[4] + 0.2, math.ceil((b[5] + 0.2) / 0.2) * 0.2])
                      for b in (p.solid.bounding_box() for p in inserts if p is not None and p.group == "inserts")])
    keep = bld_keep + ins_keep
    Lf = W + 2 * GD
    decks = {}
    for front, tag in ((True, "F"), (False, "B")):
        pts, runs, chain = _gallery(front)
        P = FT.porch_turned(pts, runs, H_FLOOR, POST_H, steps_at=[(1, Lf / 2, 16.0)], inset=INSET, rail_h=8.6,
                            post="crocketcap", rail="onionbulb", arcade="lancetarcade", roof_edge="lancetfringe",
                            skirt="lattice", pier_tex="brick", top=True)
        # each half stops square at the side's midpoint, where the other takes over
        half = box([-1e3, YM, -1e3], [1e3, 1e3, 1e3]) if front else box([-1e3, -1e3, -1e3], [1e3, YM, 1e3])
        deck = _gallery_deck(pts, runs, bld_keep + half)
        decks[tag] = deck
        kit.add(f"GALLERY-{tag}-deck", "Stucco", deck, P=print_flip(), group="gallery",
                render=FT.plank_zones(deck, H_FLOOR, "Planks", "Stucco"))
        ptop = FT.add_porch_top(kit, f"GALLERY-{tag}", P, keep + half, "Ivory", "Ivory", tin_col="Roof", tin="flat",
                                group="gallery")["ptop"]
        ch = _inset_chain(chain, 2.2)
        for i in range(3):
            f = Facade(np.array(ch[i]), np.array(ch[i + 1]), 0.0)
            cs = G.fence_evangeline_promenade(f.L - 0.8, 6.0).translate([0.4, 0.0])
            strip = M.extrude(cs, 0.9).translate([0, 0, -0.45])
            A = f.A.copy()
            A[:, 3] = f.world(0, 0, 0) + np.array([0, 0, ptop - 0.01])
            seg = strip.transform(A) - bld_keep - half
            for j, piece in enumerate(seg.decompose()):
                if piece.volume() > 3.0:
                    kit.add(f"GALLERY-{tag}-rail-{i}{chr(97 + j)}", "Ivory", piece, P=inv34(A), group="gallery")
        if not front:
            for k, (sm, A) in enumerate(P["steps"]):
                kit.add(f"STEPS-back-{k}", "Stucco", sm.transform(A) - deck, group="gallery")
    # the horseshoe stair up to the front door
    As = np.array([[1.0, 0, 0, XC], [0, 0, -1.0, -GD], [0, 1.0, 0, 0]])
    kit.add("STAIR", "Stucco", G.stair_horseshoe(H_FLOOR, n=14, land=(16.0, 9.0)).transform(As) - decks["F"], group="gallery")
    print("gallery", round(time.time() - t0, 1))

    # --- the cisterns by the back corners
    for k, (x, y) in enumerate(CISTERNS):
        base, tank, dome = G.cistern_evangeline()
        kit.add(f"CISTERN-base-{k}", "Brick", base.translate([x, y, 0.0]), key="CISTERN-base", group="cisterns")
        tb_ = tank.bounding_box()
        hc = round(math.ceil((dome.bounding_box()[2] - tb_[2]) / 0.2 - 1e-6) * 0.2, 1)
        kit.add(f"CISTERN-tank-{k}", "Cypress", (tank + dome).translate([x, y, 12.0]), key="CISTERN-tank", group="cisterns",
                change=(hc, "Teal"), render=[("Cypress", tank.translate([x, y, 12.0])), ("Teal", dome.translate([x, y, 12.0]))])

    for p_ in [p_ for p_ in kit.parts if p_.name.startswith("CREST-iron")]:
        FT.key_into(kit, p_.name, ["CREST"], (0, 0, -1), depth=0.6)
    for p_ in [p_ for p_ in kit.parts if p_.name.startswith("BELV-iron")]:
        FT.key_into(kit, p_.name, ["BELV-CREST"], (0, 0, -1), depth=0.6)
    for tag in ("F", "B"):
        for p_ in [p_ for p_ in kit.parts if p_.name.startswith(f"GALLERY-{tag}-rail")]:
            FT.key_into(kit, p_.name, [f"GALLERY-{tag}-top"], (0, 0, -1), depth=0.6)
    FT.crown(kit, "BELV-finial", "BELV-deck")
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "evangeline")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:60]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "evangeline.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors", "Addins"))

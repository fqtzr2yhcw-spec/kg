"""The Zenobia -- an original HO-scale (1:87.1) Oriental Revival octagon villa, 1861: the sixth of the
grand batch (houses 91 to 100, hoarch.grand), on the mansard batch's roof system
(hoarch.secondempire).

An octagon villa of the kind the Natchez cotton planters dreamed of. Walls of ablaq below
(courses of smooth and of scored stone in turn) and of rose lap with a rope bead every fourth
board above, wrapped on every face by a two-tier gallery: slender Moorish colonnettes with
cushion capitals under tall imposts, horseshoe arches cusped into lobes with stars in their
spandrels, mashrabiya railings of turned beads and a fringe of stars, the lower tier on a skirt
of girih. Over a cornice of muqarnas on lotus consoles a steep octagonal roof slated in bands of
arrowheads rises to a crested deck with merlon cresting, and from it a twelve-sided drum of
horseshoe lights under a band of merlons carries a gilt onion dome with a tulip finial. Two
stacks are little domed turrets.

- Ground storey: horseshoe-arched windows with lobed heads in alfiz frames, star aprons. Upper
  storey: paired ajimez lights on a central colonnette under an alfiz.
- Door: studded leaves under a horseshoe fanlight, a lobed frame, an alfiz with a band of stars.
- Storey joint: an ivory row of eight-pointed stars, a turquoise arabesque of knotted stars, an
  ivory torus. Eave: the stars, a turquoise muqarnas, lotus consoles, an ivory cyma.
- Crest: an ivory Kufic fret under a turquoise cavetto.

usage: python3 -m hoarch.buildings.zenobia [check] [export]
"""
import math
import os
import sys
import time

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import Facade, box, cs_union, inv34, ngon, offset, poly, rect, slab, union
from hoarch import cornice as CO, features as FT, grand as G, openings as O, roof as R, secondempire as SE
from hoarch.kit import Kit, print_flip
from hoarch.shell import Block, Opening, foundation, lip_keep, lip_ring, _corbel, stacked_shells, wall_shell

NAME = "The Zenobia"
COLORS = {"Sand": "#D9C6A2", "Rose": "#C98B7A", "Ivory": "#EFE6D2", "Turquoise": "#2E8C8A", "Oxblood": "#6E2A26",
          "Gilt": "#C9A64E", "Iron": "#232528", "Planks": "#6F5034", "PorchDeck": "#EFE6D2", "Windows_Doors": "#EFE6D2"}
RENDER_MAT = {"Sand": "stone", "Rose": "siding", "Ivory": "trim", "Turquoise": "accent", "Oxblood": "roof", "Gilt": "gilt",
              "Iron": "iron", "Planks": "planks", "PorchDeck": "trim", "Windows_Doors": "trim", "Sash": "sash", "Door": "door",
              "Glass": "glass"}
PALETTE = {"stone": ["#D9C6A2", 0.85, 0.0], "siding": ["#C98B7A", 0.75, 0.0], "trim": ["#EFE6D2", 0.6, 0.0],
           "accent": ["#2E8C8A", 0.5, 0.0], "roof": ["#6E2A26", 0.75, 0.0], "gilt": ["#C9A64E", 0.35, 0.6],
           "iron": ["#232528", 0.45, 0.3], "planks": ["#6F5034", 0.75, 0.0], "sash": ["#2B2A26", 0.45, 0.0],
           "door": ["#4A2A1C", 0.45, 0.0]}

# ------------------------------------------------------------------ cornices (unique to the Zenobia)
LEDGE = 1.4
JOINT = dict(pitch=12.0, margin=3.0, layers=[
    dict(kind="course", h=1.6, b=1.0, orn="octostars", role="Ivory"),
    dict(kind="frieze", h=5.2, b=1.2, orn="arabesque", role="Turquoise"),
    dict(kind="crown", h=2.0, b=1.4, P=3.4, orn="torus", role="Ivory")])
EAVE = dict(pitch=7.0, margin=2.5, layers=[
    dict(kind="course", h=1.6, b=1.0, orn="octostars", role="Ivory"),
    dict(kind="frieze", h=6.6, b=1.2, orn="muqarnas", role="Turquoise"),
    dict(kind="bed", h=3.0, b=1.4, P=7.4, role="Ivory", brackets=dict(style="lotusconsole", t=1.6, reach=0.6)),
    dict(kind="crown", h=2.8, b=1.4, P=8.2, orn="cyma", role="Ivory")])
DRUM_C = dict(pitch=8.0, margin=2.0, layers=[
    dict(kind="frieze", h=4.6, b=1.2, orn="merlons", role="Turquoise"),
    dict(kind="crown", h=2.2, b=1.4, P=3.6, orn="ogee_fillet", role="Ivory")])
CREST_COURSE = dict(h=2.6, b=0.6, orn=G.kufic, role="Ivory")
CREST_CROWN = dict(h=2.4, P=3.4, kind="cavetto", role="Turquoise", blocks=None)
RJ = round((LEDGE + 0.4 + CO.band_height(JOINT)) / 0.2) * 0.2
HE = CO.band_height(EAVE)
HD = CO.band_height(DRUM_C)

# ------------------------------------------------------------------ levels (on the 0.2 mm grid)
ZF = 6.0
S1 = ZF + 32.0
ZE = S1 + RJ + 32.0
ZW = ZE + HE
DK = EAVE["layers"][-1]["P"] + 0.2
RH = 24.0
ZR1 = ZW + RH
D_TOP = round(DK - 1.2 - (RH - 1.2) / math.tan(math.radians(60.0)), 1)
ROOF = [(DK, ZW), (DK - 1.2, ZW + 1.2), (D_TOP, ZR1)]
SLATE = dict(pitch=1.7, wtab=2.0, d=0.4, shape=G.slate_zenobia)
DRUM_H = 20.0
V1, V2 = 5.0, S1 + RJ - ZF + 3.0

# ------------------------------------------------------------------ plan (mm; the octagon about the origin, front = south)
A = 54.0
OCT = Block("octagon", ngon((0.0, 0.0), A, n=8), ZF, ZW)
BLOCKS = [OCT]
GD = 14.0
INSET = 1.6
CA = INSET * math.tan(math.radians(22.5))
DA = 16.0                                        # the drum's apothem
CHIMS = [(-32.0, 0.0), (32.0, 0.0)]


def _walls(f, b, reg):
    """Ablaq below the joint, rope-beaded lap above; nothing in the eave band."""
    reg = reg - rect(-1, ZE - b.z0, f.L + 1, 999)
    lo = reg ^ rect(-1, -100, f.L + 1, S1 - b.z0)
    hi = reg ^ rect(-1, S1 + RJ - b.z0, f.L + 1, 999)
    out = []
    if not lo.is_empty():
        out.append(G.ablaq(lo, datum=0.0))
    if not hi.is_empty():
        out.append(G.lap_ropebead(hi, datum=S1 + RJ - b.z0 + 0.4))
    return union(out) if out else M()


def _openings():
    L = []
    gw, uw = G.window_zenobia_ground(), G.window_zenobia_upper(h=16.0)
    for e in range(8):
        f = OCT.facades()[e]
        u = f.L / 2
        if e in (0, 4):
            L.append(Opening(OCT, e, u, 1.2, G.door_zenobia() if e == 0 else G.door_zenobia_back(), f"F{e}-door", "door"))
        else:
            L.append(Opening(OCT, e, u, V1, gw, f"F{e}-1"))
        L.append(Opening(OCT, e, u, V2, uw, f"F{e}-2"))
    return L


OPENINGS = _openings()


def _deck_plate(C, z, hole=None):
    dcs = poly(R.offset_path(C["path"], -1.6))
    x0, y0, x1, y1 = dcs.bounds()
    seams = cs_union([rect(x - 0.25, y0, x + 0.25, y1) for x in np.arange(x0 + 2.6, x1, 5.2)]) ^ dcs
    if hole is not None:
        seams = seams - hole
    return C["deck"] + slab(seams, z - 0.01, z + 0.4)


def _gallery(front):
    """One half of the octagonal gallery: its polygon (outer facets CCW, then back along the
    walls) and its runs (half a facet, three facets, half a facet)."""
    Q = [np.array(q) for q in ngon((0.0, 0.0), A + GD, n=8)]
    Pw = [np.array(p) for p in ngon((0.0, 0.0), A, n=8)]

    def mid(a, b):
        return tuple((a + b) / 2)
    if front:
        outer = [mid(Q[6], Q[7]), tuple(Q[7]), tuple(Q[0]), tuple(Q[1]), tuple(Q[2]), mid(Q[2], Q[3])]
        inner = [mid(Pw[2], Pw[3]), tuple(Pw[2]), tuple(Pw[1]), tuple(Pw[0]), tuple(Pw[7]), mid(Pw[6], Pw[7])]
    else:
        outer = [mid(Q[2], Q[3]), tuple(Q[3]), tuple(Q[4]), tuple(Q[5]), tuple(Q[6]), mid(Q[6], Q[7])]
        inner = [mid(Pw[6], Pw[7]), tuple(Pw[6]), tuple(Pw[5]), tuple(Pw[4]), tuple(Pw[3]), mid(Pw[2], Pw[3])]
    Lo = float(np.linalg.norm(Q[1] - Q[0]))
    Lh = Lo / 2
    runs = [dict(a=outer[0], b=outer[1], posts=[2.6, Lh * 0.55, Lh - CA])]
    for k in (1, 2, 3):
        runs.append(dict(a=outer[k], b=outer[k + 1], posts=[CA, Lo / 3, 2 * Lo / 3, Lo - CA]))
    runs.append(dict(a=outer[4], b=outer[5], posts=[CA, Lh * 0.45, Lh - 2.6]))
    return outer + inner, runs, outer, Lo


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    allcs = OCT.cs
    undress = [slab(offset(allcs, 10.0), ZE - LEDGE - 0.6, ZW + 0.01)]
    st = stacked_shells(BLOCKS, OPENINGS, [S1], t=3.0, corners="zenobia", clear=[lip_keep(allcs, 3.0, ZF, 1.2)],
                        siding=_walls, prof=CO.joint_profile(RJ, LEDGE), belt_blocks=None, water_table=False,
                        undress=undress)
    kit.add("WALLS-1", "Sand", st["shells"][0], group="walls")
    kit.add("JOINT", "Rose", st["rings"][0], group="walls")
    walls2 = st["shells"][1] + CO.ledge(OCT.pts, ZE, LEDGE)
    kit.add("WALLS-2", "Rose", walls2, group="walls")
    rings, _ = CO.level(st["outlines"][0], S1 + LEDGE + 0.4, JOINT)
    CO.add_level(kit, rings, "CORNICE-J", "cornice")
    rings, _ = CO.level(OCT.pts, ZE, EAVE)
    CO.add_level(kit, rings, "CORNICE-E", "cornice")
    kit.add("FOUNDATION", "Sand", foundation(BLOCKS, 0.0, ZF, style="starplinth"), group="foundation")
    inserts = []
    for o in OPENINGS:
        Af = o.local_frame()
        sp = o.spec
        b = sp["cut"].bounds()
        tag = f"{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}"
        key = "DOOR" if o.kind == "door" else "WIN"
        world, P, zones = O.place(sp, Af, "Ivory", "Door" if o.kind == "door" else "Sash", "Glass")
        inserts.append(kit.add(f"{key}-{o.name}", "Windows_Doors", world, P=P,
                               key=f"{key}-{tag}-{o.v0 > 20}", group="inserts", render=zones))
    print("walls + cornices + inserts", round(time.time() - t0, 1))

    # --- the octagonal roof (upside down), crest, deck, stacks, cresting
    mans, mtex, inner = R.mansard(OCT.pts, ROOF, t=2.6, tex=SLATE)
    C = SE.crest_ring(OCT.pts, D_TOP, ZR1, D_TOP - inner(ZR1), CREST_COURSE, CREST_CROWN)
    kit.add("ROOF", "Oxblood", (mans + mtex) - C["groove"], P=print_flip(), group="roof")
    kit.add("CREST", "Turquoise", C["solid"], P=print_flip(), change=C["change"], group="roof", render=C["zones"])
    zdeck = C["z_top"]
    DRUM = Block("drum", ngon((0.0, 0.0), DA, n=12), zdeck, zdeck + DRUM_H + HD)
    pads = union([M.cylinder(1.6, 5.4, 5.4, 16).translate([x, y, zdeck - 0.6]) for x, y in CHIMS])
    kit.add("ROOF-deck", "Oxblood", _deck_plate(C, zdeck, hole=offset(DRUM.cs, 0.3)) - pads, group="roof")
    for k, (x, y) in enumerate(CHIMS):
        kit.add(f"CHIMNEY-{k}", "Sand", G.chimney_zenobia(4.6, 22.0).translate([x, y, zdeck - 0.6]), key="CHIMNEY", group="roof")
    for i, seg, Af, L in SE.cresting_strips(C["path"], zdeck, C["rail"], SE.printable(G.fence_zenobia), 7.0):
        kit.add(f"CREST-iron-{i}", "Iron", seg, P=inv34(Af), key=f"CREST-iron-{round(L, 1)}", group="roof")
    print("roof", round(time.time() - t0, 1))

    # --- the drum: twelve sides of ablaq, four horseshoe lights, a band of merlons; the onion
    dw = G.window_zenobia_drum()
    dopen = [Opening(DRUM, e, DRUM.facades()[e].L / 2, 3.4, dw, f"D{e}") for e in (0, 3, 6, 9)]
    ZDE = zdeck + DRUM_H

    def _dskin(f, b, reg):
        reg = reg - rect(-1, DRUM_H - LEDGE - 0.6, f.L + 1, 999)
        return G.ablaq(reg, datum=0.4) if not reg.is_empty() else M()
    dshell = wall_shell([DRUM], dopen, t=2.4, belt=None, belt_trim=False, corners="zenobia", siding=_dskin,
                        water_table=False, undress=[slab(offset(DRUM.cs, 6.0), ZDE - LEDGE - 0.6, ZDE + HD + 0.01)])
    kit.add("DRUM-walls", "Sand", dshell + CO.ledge(DRUM.pts, ZDE, LEDGE, t=2.4), group="drum")
    for o in dopen:
        Af = o.local_frame()
        world, P, zones = O.place(o.spec, Af, "Ivory", "Sash", "Glass")
        inserts.append(kit.add(f"WIN-{o.name}", "Windows_Doors", world, P=P, key="WIN-drum", group="drum", render=zones))
    rings, _ = CO.level(DRUM.pts, ZDE, DRUM_C)
    CO.add_level(kit, rings, "CORNICE-D", "drum")
    zon = ZDE + HD
    kit.add("ONION", "Gilt", G.onion_zenobia(DA + 0.2, 34.0).translate([0.0, 0.0, zon]), group="drum")
    kit.add("ONION-finial", "Gilt", G.finial_tulip(14.0).translate([0.0, 0.0, zon + 33.6]), group="drum")
    FT.crown(kit, "ONION-finial", "ONION")
    print("drum", round(time.time() - t0, 1))

    # --- the two-tier gallery, in a front and a back half, each a deck (upside down), a lower
    # top whose roof is the upper floor, and an upper top under the eave
    parts = {p_.name: p_ for p_ in kit.parts}
    bld_keep = union([parts[n].solid for n in ("WALLS-1", "JOINT", "WALLS-2", "FOUNDATION")] +
                     [p_.solid for p_ in kit.parts if p_.name.startswith("CORNICE-J") or p_.name.startswith("CORNICE-E")])
    ins_keep = union([box([b[0] - 0.2, b[1] - 0.2, math.floor((b[2] - 0.2) / 0.2) * 0.2],
                          [b[3] + 0.2, b[4] + 0.2, math.ceil((b[5] + 0.2) / 0.2) * 0.2])
                      for b in (p.solid.bounding_box() for p in inserts if p is not None and p.group == "inserts")])
    keep = bld_keep + ins_keep
    H1 = ZF - 1.0
    ph1 = S1 + RJ - 0.4 - 5.2 - H1
    H2 = H1 + ph1 + 5.2
    ph2 = ZE - 2.6 - 5.2 - H2
    fkeep = slab(offset(allcs, 1.7), -1, ZF + 1.3)
    for front, tag in ((True, "F"), (False, "B")):
        pts, runs, outer, Lo = _gallery(front)
        half = box([-1e3, 0.0, -1e3], [1e3, 1e3, 1e3]) if front else box([-1e3, -1e3, -1e3], [1e3, 0.0, 1e3])
        P1 = FT.porch_turned(pts, runs, H1, ph1, steps_at=[(2, Lo / 2, 14.0)], planks=dict(pitch=1.5, border=1.4),
                             post="moorish", rail="mashrabiya", arcade="horseshoearcade", skirt="girih", pier_tex="stone",
                             roof_edge="starfringe", top=True)
        P2 = FT.porch_turned(pts, runs, H2, ph2, post="moorish", rail="mashrabiya", arcade="horseshoearcade",
                             skirt="girih", pier_tex="stone", roof_edge="starfringe", top=True)
        for P_, hf, ph in ((P1, H1, ph1), (P2, H2, ph2)):
            where = []
            for r in runs:
                f = Facade(r["a"], r["b"], 0.0)
                for u in r["posts"]:
                    p = f.p0 + f.u * u - f.n * INSET
                    if not any(np.allclose(p, q, atol=0.05) for q in where):
                        where.append(p)
            z0r = hf + ph
            P_["top"] = P_["top"] + union([box([p[0] - 0.5, p[1] - 0.5, z0r - 0.6], [p[0] + 0.5, p[1] + 0.5, z0r + 0.6]) for p in where])
        deck_ = P1["deck"] - fkeep - half
        kit.add(f"GALLERY-{tag}-deck", "PorchDeck", deck_, P=print_flip(), group="gallery",
                render=FT.plank_zones(deck_, H1, "Planks", "PorchDeck"))
        socks = union([box([p[0] - 1.0, p[1] - 1.0, H2 - 2.0], [p[0] + 1.0, p[1] + 1.0, H2 + 1.0]) for p in where])
        FT.add_porch_top(kit, f"GALLERY-{tag}-1", P1, keep + half + socks, "Ivory", "Ivory", tin_col="Oxblood", tin="flat", group="gallery")
        FT.add_porch_top(kit, f"GALLERY-{tag}-2", P2, keep + half, "Ivory", "Ivory", tin_col="Oxblood", tin="flat", group="gallery")
        for k, (sm, Af) in enumerate(P1["steps"]):
            kit.add(f"GALLERY-{tag}-steps-{k}", "Sand", sm.transform(Af) - fkeep, group="gallery")
    print("gallery", round(time.time() - t0, 1))

    for p_ in [p_ for p_ in kit.parts if p_.name.startswith("CREST-iron")]:
        FT.key_into(kit, p_.name, ["CREST"], (0, 0, -1), depth=0.6)
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "zenobia")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:60]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "zenobia.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))

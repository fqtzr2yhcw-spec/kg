"""The Randolph: an original HO-scale (1:87.1) Tidewater Virginia Colonial, house 44 of the
fourth batch (all Colonial).

A long two-storey house of red brick in Flemish bond with glazed headers standing proud of
the stretchers, on a footing of English bond under a rubbed-brick torus water table. The
roof is a steep jerkinhead: side gables whose apexes are clipped back in short hips, covered
in shakes cut with two lobes at the butt, with three jerkinhead dormers front and back. At
each end a Stratford cluster: four stacks joined near the top by arches on every side under
one corbelled cap. Ground-floor windows (nine over nine) under segmental pediments on
consoles; upper windows (nine over six) in lugged architraves under caps carved with a
rosette. The door is a Doric frontispiece (pilasters, a triglyph frieze with guttae, a
pediment with an oval patera) inside a portico of Roman Doric columns with double-vase
balusters, a triglyph entablature and a low hipped roof. Between the storeys an ochre frieze
of crossed tobacco leaves and tobacco blossoms over a billet course and an ovolo; at the eave
an ochre dogwood branch in bloom, dentils, a soffit on cavetto modillions and an ogee crown.

usage: python3 -m hoarch.buildings.randolph [check] [export]
"""
import os
import sys
import time

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import box, offset, poly, rect, slab, union
from hoarch import colonial4 as C4, cornice as CO, features as FT, gables as G, openings as O, roof as R
from hoarch.kit import Kit, print_flip
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, stacked_shells

NAME = "The Randolph"
COLORS = {"Brick": "#8A3B2B", "Ivory": "#EFE9DA", "Ochre": "#C4953F", "Shake": "#6A5E52", "Clinker": "#5E2A20",
          "Sandstone": "#B9A48A", "Planks": "#6E5238", "PorchDeck": "#6E5238", "Windows_Doors": "#EFE9DA"}
RENDER_MAT = {"Brick": "brick", "Ivory": "trim", "Ochre": "accent", "Shake": "roof", "Clinker": "brick2",
              "Sandstone": "stone", "Planks": "planks", "PorchDeck": "planks", "Windows_Doors": "trim", "Door": "door",
              "Glass": "glass"}

# ------------------------------------------------------------------ cornices (unique to the Randolph)
LEDGE = 1.4
JOINT = dict(pitch=14.0, margin=4.0, layers=[
    dict(kind="frieze", h=4.4, b=1.2, orn="tobacco", role="Ochre"),
    dict(kind="course", h=1.4, b=1.4, orn="billet", role="Ivory"),
    dict(kind="crown", h=2.2, b=1.4, P=3.2, orn="ovolo", role="Ivory")])
EAVE = dict(pitch=13.0, margin=4.0, layers=[
    dict(kind="frieze", h=5.2, b=1.2, orn="dogwood", role="Ochre"),
    dict(kind="course", h=1.6, b=1.4, orn="dentil", role="Ivory", tooth=0.8, gap=0.6),
    dict(kind="bed", h=2.0, b=1.4, P=5.6, role="Ivory", brackets=dict(style="cavettomod", t=1.4, reach=0.3)),
    dict(kind="crown", h=2.8, b=1.4, P=6.4, orn="ogee_fillet", role="Ivory")])
RJ = round((LEDGE + 0.4 + CO.band_height(JOINT)) / 0.2) * 0.2
HE = CO.band_height(EAVE)

# ------------------------------------------------------------------ levels (on the 0.2 mm grid)
ZF = 10.0
S1 = ZF + 42.0
ZU = S1 + RJ
ZE = ZU + 38.0
ZW = round((ZE + HE) / 0.2) * 0.2
FASCIA = 1.6
Z_EAVE = ZW + FASCIA
D_EAVE, RAKE, SKIN = 6.4, 6.6, 1.8
S_MAIN = 1.0
S_END = 1.8                                     # the jerkinhead hips
TK = 2.8                                        # the clipped faces' thickness
V1 = 7.0
V2 = ZU - ZF + 5.0

# ------------------------------------------------------------------ plan (x east, y north; the front faces south)
W, D = 208.0, 100.0
XC = W / 2
MAIN = Block("main", [(0, 0), (W, 0), (W, D), (0, D)], ZF, ZW)
BLOCKS = [MAIN]
BAYS = (26.0, 62.0, W - 62.0, W - 26.0)
Z_RIDGE = Z_EAVE + S_MAIN * (D / 2 + D_EAVE)
Z_CLIP = round((Z_EAVE + 0.6 * (Z_RIDGE - Z_EAVE)) / 0.2) * 0.2
PLANES = C4.jerkin_planes(W, D, Z_EAVE, S_MAIN, D_EAVE, Z_CLIP, S_END, RAKE)


def _skin(f, b, reg):
    """Glazed-header Flemish bond all round; nothing in the eave band."""
    reg = reg - rect(-1, ZE - LEDGE - 0.6 - b.z0, f.L + 1, ZW - b.z0 + 0.2)
    return C4.brick_glazedheader(reg, datum=0.0)


def _openings():
    L = []

    def add(x, y, v0, sp, name, kind="window"):
        e, u = MAIN.locate(x, y)
        L.append(Opening(MAIN, e, u, v0, sp, name, kind))

    lo = C4.window_segped(10.0, 26.0)
    up = C4.window_rosettecap(10.0, 22.0)
    att = C4.window_rosettecap(7.0, 12.0)
    for x in BAYS:
        add(x, 0.0, V1, lo, f"S{x:.0f}-1")
        add(x, D, V1, lo, f"N{x:.0f}-1")
    for x in BAYS + (XC,):
        add(x, 0.0, V2, up, f"S{x:.0f}-2")
        add(x, D, V2, up, f"N{x:.0f}-2")
    add(XC, 0.0, 0.4, C4.door_doric(10.0, 22.0, transom=3.2), "front-door", "door")
    add(XC, D, 0.4, C4.door_doric(10.0, 22.0, transom=3.2, back=True), "back-door", "door")
    for x_, tag in ((0.0, "W"), (W, "E")):
        for y in (28.0, D - 28.0):
            add(x_, y, V1, lo, f"{tag}{y:.0f}-1")
            add(x_, y, V2, up, f"{tag}{y:.0f}-2")
        for y in (D / 2 - 15.0, D / 2 + 15.0):
            add(x_, y, Z_EAVE + 3.0 - ZF, att, f"{tag}{y:.0f}-attic")
    return L


OPENINGS = _openings()


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    base = MAIN.cs
    Ls, Ln, Ew, Ee = PLANES
    pieces = [(MAIN.pts, [0, 2], S_MAIN)]
    gdefs = [dict(p0=(W, 0.0), p1=(W, D), slope=S_MAIN, e=0.3), dict(p0=(0.0, D), p1=(0.0, 0.0), slope=S_MAIN, e=0.3)]
    rf = G.gabled_roof(pieces, Z_EAVE, D_EAVE, gdefs, texture="lobed", tex_kw=dict(pitch=1.6, wtab=2.4, d=0.4),
                       skin=SKIN, rake=RAKE, inner_cs=offset(base, -3.0), fascia=FASCIA, hollow=2.8)
    we, ww = rf["walls"]
    gables = [(MAIN, 1, we["cs"].translate((0.0, Z_EAVE - ZF))), (MAIN, 3, ww["cs"].translate((0.0, Z_EAVE - ZF)))]
    undress = [slab(offset(base, 8.0), ZE - LEDGE - 0.6, ZW + 0.01)]
    clear = [lip_keep(base, 3.0, ZF, 1.2)]
    st = stacked_shells(BLOCKS, OPENINGS, [S1], t=3.0, corners="none", siding=_skin, gables=gables, clear=clear,
                        prof=CO.joint_profile(RJ, LEDGE), belt_blocks=None, water_table=False, undress=undress,
                        partitions=[((XC - 20.0, 3.0), (XC - 20.0, D - 3.0), 2.0, ZF, ZW),
                                    ((XC + 20.0, 3.0), (XC + 20.0, D - 3.0), 2.0, ZF, ZW)])
    kit.add("WALLS-1", "Brick", st["shells"][0], group="walls")
    kit.add("JOINT", "Brick", st["rings"][0], group="walls")
    no_lip = union([box([W - 5.0, -1, ZW - 1], [W + 1, D + 1, ZW + 5]), box([-1, -1, ZW - 1], [5.0, D + 1, ZW + 5])])
    lip = (_corbel(base, 3.0, ZW) + lip_ring(base, 3.0, ZW)) - no_lip
    w2 = st["shells"][1] + lip + CO.ledge(MAIN.pts, ZE, LEDGE)
    # the gable walls stop under the clipped faces, their tops sloping with them
    drop = TK * np.sqrt(1 + S_END * S_END) + 0.3
    for E in (Ew, Ee):
        w2 = R.below(w2, R.Plane(E.q, E.t, E.z0 - drop, E.s))
    kit.add("WALLS-2", "Brick", w2, group="walls")
    rings, _ = CO.level(st["outlines"][0], S1 + LEDGE + 0.4, JOINT)
    CO.add_level(kit, rings, "CORNICE-J", "cornice")
    rings, _ = CO.level(MAIN.pts, ZE, EAVE)
    CO.add_level(kit, rings, "CORNICE-E", "cornice")
    fnd = foundation(BLOCKS, 0.0, ZF, style="englishtorus")
    kit.add("FOUNDATION", "Clinker", fnd, group="foundation")
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
    print("walls + cornices + inserts", round(time.time() - t0, 1))

    # --- the jerkinhead roof: the gabled roof clipped at both ends, the clipped faces closed
    clip = lambda m_: R.below(R.below(m_, Ew), Ee)
    roof = clip(rf["body"] + rf["tex"] + rf["skins"] + rf["skin_tex"])
    solid_env, _ = R.hip_roof(pieces, Z_EAVE, S_MAIN, D_EAVE, texture=None, zlo=ZW)
    fp = poly([(-RAKE, -D_EAVE), (W + RAKE, -D_EAVE), (W + RAKE, D + D_EAVE), (-RAKE, D + D_EAVE)])
    faces, ftex = C4.jerkin_faces(solid_env, PLANES, fp, tk=TK, texture="lobed", tex_kw=dict(pitch=1.6, wtab=2.4, d=0.4))
    roof = roof + faces + ftex
    xr = (Z_RIDGE - Z_CLIP) / S_END - RAKE                  # where each clipped face meets the ridge
    yc = (Z_CLIP - Z_EAVE) / S_MAIN - D_EAVE                 # and where it meets the long slopes
    walls_env = union([wl["facade"].place(M.extrude(wl["cs"].offset(0.15), RAKE + 4.2).translate([0, 0, -3.15])) for wl in rf["walls"]])
    caps = G.ridge_cap((xr, D / 2), (W - xr, D / 2), Z_RIDGE, S_MAIN, ZW)
    for x0, x1 in ((-RAKE, xr), (W + RAKE, W - xr)):
        for y0 in (yc, D - yc):
            caps = caps + G.hip_cap((x0, y0, Z_CLIP), (x1, D / 2, Z_RIDGE), half=1.2, up=0.6, drop=1.4)
    roof = roof + (caps - walls_env)
    roof = roof - lip_keep(base, 3.0, ZW)
    roof = roof.trim_by_plane([0, 0, 1.0], ZW)
    # the Stratford clusters on the ridge, one near each end
    S_CL = 17.0
    pockets, stacks = [], []
    for cx in (30.0, W - 30.0):
        z0 = round((Z_RIDGE - 8.0) / 0.2) * 0.2
        roof = roof + G.pocket_seat(solid_env, cx, D / 2, S_CL / 2 + 0.4, S_CL / 2 + 0.4, z0)
        pockets.append(box([cx - S_CL / 2 - 0.4, D / 2 - S_CL / 2 - 0.4, z0], [cx + S_CL / 2 + 0.4, D / 2 + S_CL / 2 + 0.4, Z_RIDGE + 40]))
        stacks.append(C4.chimney_cluster(S_CL, 5.4, Z_RIDGE + 17.0 - z0).translate([cx, D / 2, z0]))
    roof = roof - union(pockets)
    # jerkinhead dormers, three a side
    DW, DDEP, DHW = 13.0, 20.0, 12.0
    dyf = 16.0
    zdf = round((Z_EAVE + S_MAIN * (dyf + D_EAVE) - 1.0) / 0.2) * 0.2
    dbody, dcore, dface = C4.dormer_jerkin(DW, DDEP, DHW)
    droof = C4.dormer_jerkin_roof(DW, DDEP, DHW)
    dparts = []
    for dxc in (66.0, XC, W - 66.0):
        for side in (0, 1):
            if side == 0:
                Ad = np.array([[1.0, 0, 0, dxc], [0, 0, -1.0, dyf], [0, 1.0, 0, zdf]])
            else:
                Ad = np.array([[-1.0, 0, 0, dxc], [0, 0, 1.0, D - dyf], [0, 1.0, 0, zdf]])
            dkeep = C4.ext(dface.offset(0.3, C4.JoinType.Miter, 4.0), -DDEP - 0.3, 0.3).transform(Ad)
            dpocket = dkeep ^ box([-500, -500, zdf], [500, 500, 999])
            yb0, yb1 = (dyf - 1.6, dyf + DDEP + 1.3) if side == 0 else (D - dyf - DDEP - 1.3, D - dyf + 1.6)
            dseat = box([dxc - DW / 2 - 1.3, yb0, ZW], [dxc + DW / 2 + 1.3, yb1, zdf]) ^ solid_env
            roof = roof - dpocket
            roof = roof + (dseat - dpocket - lip_keep(base, 3.0, ZW))
            dparts.append(Ad)
    kit.add("ROOF", "Shake", roof, group="roof")
    for k, s_ in enumerate(stacks):
        kit.add(f"CHIMNEY-{k}", "Brick", s_, key="CHIMNEY", group="roof")
    for k, Ad in enumerate(dparts):
        kit.add(f"DORMER-{k}", "Ivory", dbody.transform(Ad), key="DORMER", group="roof")
        kit.add(f"DORMER-core-{k}", "Shake", dcore.transform(Ad), key="DORMER-core", group="roof")
        dr = droof.transform(Ad) - solid_env - dbody.transform(Ad) - roof
        kit.add(f"DORMER-roof-{k}", "Shake", max(dr.decompose(), key=lambda m_: m_.volume()), key="DORMER-roof", group="roof")
    print("roof", round(time.time() - t0, 1))

    # --- the portico
    PX0, PX1, PY = XC - 17.0, XC + 17.0, -16.0
    INSET = 1.6
    ppts = [(PX0, 0.0), (PX0, PY), (PX1, PY), (PX1, 0.0)]
    Lf = PX1 - PX0
    runs = [dict(a=(PX0, 0.0), b=(PX0, PY), posts=[3.0, -PY - INSET]),
            dict(a=(PX0, PY), b=(PX1, PY), posts=[INSET, Lf / 2 - 5.8, Lf / 2 + 5.8, Lf - INSET]),
            dict(a=(PX1, PY), b=(PX1, 0.0), posts=[INSET, -PY - 3.0])]
    H_floor = ZF - 1.4
    ptop = S1 - 0.6
    PP = FT.porch_turned(ppts, runs, H_floor, ptop - 5.2 - H_floor, steps_at=[(1, Lf / 2, 10.0)], over=2.4, inset=INSET,
                         planks=dict(pitch=1.8, border=1.2), post="virginian", rail="doublevase", arcade="doricfrieze",
                         skirt="lozenges", pier_tex="englishtorus", roof_edge="mutules", top=True)
    fkeep = slab(offset(base, 0.8 + 0.55 + 0.15), -1, ZF + 1.3)
    deck = PP["deck"] - fkeep
    kit.add("PORTICO-deck", "PorchDeck", deck, P=print_flip(), group="portico",
            render=FT.plank_zones(deck, H_floor, "Planks", "PorchDeck"))
    bld_keep = union([p.solid for p in kit.parts if p.name in ("WALLS-1", "JOINT", "WALLS-2") or p.name.startswith("CORNICE")])
    keep = bld_keep + union(ins_keep) + fnd
    res = FT.add_porch_top(kit, "PORTICO", PP, keep, "Ivory", "Ivory", tin="custom", group="portico")
    zs = res["ptop"] - 0.8
    o = 2.4
    outer = [(PX0 - o, PY - o), (PX1 + o, PY - o), (PX1 + o, 3.0), (PX0 - o, 3.0)]
    pr, pr_tex = R.hip_roof([(outer, [0, 1, 3])], zs, 0.42, 0.0, texture="lobed", tex_kw=dict(pitch=1.5, wtab=2.2, d=0.38), zlo=zs)
    proof = ((pr + pr_tex) ^ slab(poly(outer), zs, zs + 12.0)) - bld_keep - union(ins_keep)
    kit.add("PORTICO-roof", "Shake", max(proof.decompose(), key=lambda m_: m_.volume()), group="portico")
    for k, (sm, A) in enumerate(PP["steps"]):
        kit.add(f"PORTICO-steps-{k}", "Sandstone", sm.transform(A) - fkeep - deck, group="portico")
    e, u = MAIN.locate(XC, D)
    fb = MAIN.facades()[e]
    A = fb.A.copy()
    A[:, 3] = fb.world(u, -ZF, 1.4)
    kit.add("STOOP-back", "Sandstone", FT.steps(16.0, ZF - 0.6, 4).transform(A) - fnd, group="portico")
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "randolph")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:80]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "randolph.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))

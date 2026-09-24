"""The Harcourt -- an original HO-scale (1:87.1) Second Empire house for the lineup.

A symmetrical red-brick block with a centre tower over the entrance and cream stone trim:
stone-arch window heads with long-and-short voussoirs, a straight bell-cast slate mansard
with round-topped dormers, iron cresting on its flat top, and a tall concave mansard cap
on the tower. A one-storey canted bay on the east side, a turned entrance portico, and a
coursed granite foundation.

usage: python3 -m hoarch.buildings.harcourt [check] [export]
"""
import os
import sys
import time

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import box, brick, compose, cs_union, inv34, offset, poly, slab, union
from hoarch import features as FT, openings as O, roof as R
from hoarch.kit import Kit, print_flip
from hoarch.ornament import finial
from hoarch.shell import Block, Opening, foundation, lip_keep, stacked_shells

NAME = "Harcourt Second Empire"
COLORS = {"Brick": "#8E3B2C", "Limestone": "#D9CFB6", "Slate": "#4A5159", "Iron": "#27292C",
          "Granite": "#7E7C78", "PorchGray": "#6B706F", "Windows_Doors": "#D9CFB6"}
# windows and doors print in one colour and are painted; Sash/Door/Glass are render-only zones
RENDER_MAT = {"Brick": "brick", "Limestone": "trim", "Slate": "roof", "Iron": "iron", "Granite": "stone",
              "PorchGray": "porchfloor", "Windows_Doors": "trim", "Sash": "sash", "Door": "door", "Glass": "glass"}
PALETTE = {"brick": ["#8E3B2C", 0.85, 0.0], "trim": ["#D9CFB6", 0.6, 0.0], "roof": ["#4A5159", 0.75, 0.0],
           "iron": ["#27292C", 0.45, 0.3], "stone": ["#7E7C78", 0.9, 0.0], "porchfloor": ["#6B706F", 0.7, 0.0],
           "sash": ["#2E3B33", 0.45, 0.0], "door": ["#4A2616", 0.45, 0.0]}

# ------------------------------------------------------------------ levels (all on the 0.2 mm grid)
ZF = 12.0                 # foundation top / first floor
S1 = ZF + 40.0            # first-floor shell top = belt ring bottom
RH = 4.4                  # belt ring height
ZE = S1 + RH + 36.0       # main eave (second-floor shell top)
EAVE = R.EAVE_DEEP
MZ0 = ZE + EAVE[-1][1]    # mansard foot (top of the eave ring)
MH = 28.0                 # mansard height
MZ1 = MZ0 + MH
MANSARD = [(6.2, MZ0), (4.6, MZ0 + 1.6), (-2.4, MZ1)]       # bell-cast kick, then about 75 degrees
TT = ZE + RH + 44.0       # tower wall top
TCAP_H = 20.0
V1, V2 = 7.0, S1 + RH + 3.0 - ZF       # sill heights above ZF
V3 = ZE + RH + 5.0 - ZF                 # tower third storey

# ------------------------------------------------------------------ plan (mm; x east, y north, front = south)
X1, Y1 = 128.0, 112.0
MAIN = Block("main", [(0, 0), (X1, 0), (X1, Y1), (0, Y1)], ZF, ZE)
TX0, TX1, TY0, TY1 = 46.0, 82.0, -12.0, 20.0
TOWER = Block("tower", [(TX0, TY0), (TX1, TY0), (TX1, TY1), (TX0, TY1)], ZF, TT)
BAY = Block("bay", [(X1 - 3.0, 42.0), (X1, 42.0), (X1 + 9.0, 48.0), (X1 + 9.0, 64.0), (X1, 70.0),
                    (X1 - 3.0, 70.0)], ZF, ZF + 31.6)
BLOCKS = [MAIN, TOWER, BAY]
SLATE = ("fish", "fish", "square", "square", "diamond", "square", "square")    # banded courses
TOWER_SLATE = ("fish", "fish", "diamond")


def _brick(f, b, reg):
    return brick(reg, datum=1.8)


# ------------------------------------------------------------------ openings
def _openings():
    L = []
    lo = O.window_insert(10.4, 26.0, rise=2.6, style="voussoir", apron=True)
    up = O.window_insert(9.6, 22.0, rise=2.4, style="voussoir")
    tk = dict(casing=0.8, ends=0.2, sill_ext=0.3, clip=True)
    bay_f = O.window_insert(9.6, 20.0, rise=2.4, style="voussoir", apron=True, **tk)
    bay_s = O.window_insert(6.8, 20.0, rise=1.8, style="voussoir", apron=True, **tk)
    tw2 = O.window_insert(11.2, 24.0, rise=None, style="voussoir")         # round-headed
    tw3 = O.twin_arch_window(14.0, 20.0, balcony=0)
    front = O.door_ornate(15.4, 26.0, leaves=2, transom=4.2, head="pediment")
    back = O.door_insert(11.0, 26.0, leaves=1, transom=3.0)

    def add(block, x, y, v0, sp, name, kind="window"):
        e, u = block.locate(x, y)
        L.append(Opening(block, e, u, v0, sp, name, kind))

    for x in (14.5, 31.5, 96.5, 113.5):                                   # front, either side of the tower
        add(MAIN, x, 0, V1, lo, f"S{x:.0f}-1")
        add(MAIN, x, 0, V2, up, f"S{x:.0f}-2")
    mx = (TX0 + TX1) / 2
    add(TOWER, mx, TY0, 0.4, front, "front-door", "door")                 # tower front
    add(TOWER, mx, TY0, V2, tw2, "T-2")
    add(TOWER, mx, TY0, V3, tw3, "T-3")
    for y in (20.0, 56.0, 92.0):                                          # west
        add(MAIN, 0, y, V1, lo, f"W{y:.0f}-1")
        add(MAIN, 0, y, V2, up, f"W{y:.0f}-2")
    for y in (20.0, 92.0):                                                # east, with the bay between
        add(MAIN, X1, y, V1, lo, f"E{y:.0f}-1")
        add(MAIN, X1, y, V2, up, f"E{y:.0f}-2")
    add(MAIN, X1, 56.0, V2, up, "E56-2")
    Q = BAY.pts
    for i in range(len(Q)):                                               # the bay's three faces
        a, b = np.array(Q[i]), np.array(Q[(i + 1) % len(Q)])
        if min(a[0], b[0]) < X1 - 0.1 or np.linalg.norm(b - a) < 5:
            continue
        m = (a + b) / 2
        add(BAY, m[0], m[1], V1 - 0.4, bay_f if abs(a[0] - b[0]) < 0.1 else bay_s, f"bay{i}-1")
    for x in (25.0, 103.0):                                               # rear
        add(MAIN, x, Y1, V1, lo, f"N{x:.0f}-1")
        add(MAIN, x, Y1, V2, up, f"N{x:.0f}-2")
    add(MAIN, 64.0, Y1, 0.4, back, "back-door", "door")
    add(MAIN, 64.0, Y1, V2, up, "N64-2")
    return L


OPENINGS = _openings()
# dormers: centre points on the wall line
DORMERS = [(23.0, 0), (105.0, 0), (X1, 20.0), (X1, 92.0), (0, 20.0), (0, 92.0), (25.0, Y1), (64.0, Y1), (103.0, Y1)]
D_FACE = 6.0              # dormer face, outward from the wall face (on the mansard's kick)


def _dormer_frame(x, y):
    """Facade frame of the dormer centred on the wall-line point (x, y), at the mansard foot."""
    e, u = MAIN.locate(x, y)
    f = MAIN.facades()[e]
    A = f.A.copy()
    A[:, 3] = f.world(u, MZ0 - ZF, D_FACE)
    return A


# ------------------------------------------------------------------ build
def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    clear = [lip_keep(cs_union([b.cs for b in BLOCKS]), 3.0, ZF, 1.2)]
    st = stacked_shells(BLOCKS, OPENINGS, [S1, ZE], t=3.0, corners="quoin", clear=clear, siding=_brick)
    kit.add("WALLS-1", "Brick", st["shells"][0], group="walls")
    kit.add("BELT-1", "Limestone", st["rings"][0], group="walls")
    # the tower's walls inside the house rise from the second floor, so its belt ring bears all round
    tw_in = slab((TOWER.cs - offset(TOWER.cs, -3.0)) ^ offset(MAIN.cs, -1.0), S1 + RH, ZE)
    tw_in = tw_in - lip_keep(cs_union([MAIN.cs, TOWER.cs]), 3.0, S1 + RH)
    kit.add("WALLS-2", "Brick", st["shells"][1] + tw_in, group="walls")
    kit.add("TOWER-BELT", "Limestone", st["rings"][1], group="tower")
    kit.add("TOWER-3", "Brick", st["shells"][2], group="tower")
    kit.add("FOUNDATION", "Granite", foundation(BLOCKS, 0.0, ZF), group="foundation")
    inserts = []
    for o in OPENINGS:
        A = o.local_frame()
        sp = o.spec
        b = sp["cut"].bounds()
        tag = f"{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}"
        key = "DOOR" if o.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, "Limestone", "Door" if o.kind == "door" else "Sash", "Glass")
        inserts.append(kit.add(f"{key}-{o.name}", "Windows_Doors", world, P=P,
                               key=f"{key}-{tag}-{o.v0 > 20}", group="inserts", render=zones))
    print("walls + inserts", round(time.time() - t0, 1))

    tower_keep = TOWER.solid(grow=2.1, dz0=-1, dz1=200)
    tower_hug = TOWER.solid(grow=0.5, dz0=-1, dz1=200)          # the mansard notch hugs the tower (brick 0.25 proud)
    # --- main eave: single large brackets over frieze panels (upside down)
    eave = R.bracketed_cornice(MAIN.pts, ZE, EAVE,
                               brackets=dict(z_top=5.2, h=5.0, d0=0.9, d=5.6, t=0.9, pitch=9.6, margin=4.0,
                                             skip=lambda p: TX0 - 3.2 < p[0] < TX1 + 3.2 and p[1] < TY1 + 3.2),
                               dents=dict(z=4.4, h=0.8, d0=0.9, d=0.7), panels=dict(z=0.6, h=3.0, d=0.4))
    kit.add("EAVE-main", "Limestone", eave - tower_keep, P=print_flip(), group="roof")
    # --- mansard band (upright) with dormer notches; it drops round the tower, which locates it
    mans, mtex, inner = R.mansard(MAIN.pts, MANSARD, t=2.6, tex=dict(pitch=1.6, wtab=1.9, d=0.4, shape=SLATE))
    dorm = []
    for k, (x, y) in enumerate(DORMERS):
        A = _dormer_frame(x, y)
        dm = FT.dormer(W=15.2, H=12.0, D=10.1, win_w=6.6, win_h=14.0)    # faces and notch top on the grid
        dorm.append((A, dm))
    notches = union([dm["keep"].transform(A) for A, dm in dorm])
    kit.add("MANSARD", "Slate", (mans + mtex) - tower_hug - notches, group="roof")
    for k, (A, dm) in enumerate(dorm):
        kit.add(f"DORMER-{k}", "Limestone", dm["body"].transform(A), key="DORMER", group="dormers")
        kit.add(f"DORMER-hood-{k}", "Slate", dm["hood"].transform(A), P=compose(print_flip(), inv34(A)),
                key="DORMER-hood", group="dormers")
        win = dm["window"]
        wb = win.bounding_box()
        glass = win ^ box([-50, -50, wb[2] - 0.1], [50, 50, wb[2] + O.GLASS])
        zones = [("Glass", glass.transform(A)), ("Sash", (win - glass).transform(A))]
        kit.add(f"WIN-dormer-{k}", "Windows_Doors", win.transform(A), P=inv34(A), key="WIN-dormer",
                group="inserts", render=zones)
    # --- top curb (upside down) and standing-seam deck, iron cresting strips, chimneys on the deck
    t_top = MANSARD[-1][0] - inner(MZ1)
    T = R.mansard_top(MAIN.pts, MANSARD[-1][0], MZ1, t_top)
    zdeck = T["z_top"]
    chims = [(14.0, 56.0), (114.0, 56.0)]
    # each chimney stands in a 0.6 mm pocket in the deck, which locates it (no peg to overhang)
    pads = union([box([x - 5.7, y - 5.7, zdeck - 0.6], [x + 5.7, y + 5.7, zdeck + 1]) for x, y in chims])
    kit.add("ROOF-curb", "Limestone", T["ring"] - tower_hug, P=print_flip(), group="roof")
    kit.add("ROOF-deck", "Slate", T["deck"] - tower_hug - pads, group="roof")
    top_path = T["path"]
    crest = R.cresting(top_path, zdeck, h=2.4, pitch=1.6, d_off=-1.0)
    for i, seg, A, L in R.cresting_strips(crest, top_path, zdeck, -1.0):
        for j, piece in enumerate((seg - tower_keep).decompose()):
            if piece.volume() > 1.0:
                kit.add(f"CREST-{i}{'ab'[j] if j < 2 else j}", "Iron", piece, P=inv34(A), group="roof")
    for k, (x, y) in enumerate(chims):
        ch = FT.chimney(w=10.5, dpt=10.5, h=16.6, peg=None).translate([x, y, zdeck - 0.6])
        kit.add(f"CHIMNEY-{k}", "Brick", ch, key="CHIMNEY", group="roof")
    print("roof", round(time.time() - t0, 1))

    # --- tower: eave ring, concave slate cap, curb and deck, cresting and finial
    teave = R.bracketed_cornice(TOWER.pts, TT, R.CORNICE_SMALL,
                                brackets=dict(z_top=4.6, h=4.2, d0=0.8, d=2.4, t=0.8, pitch=6.6, margin=2.6),
                                dents=dict(z=3.8, h=0.8, d0=0.8, d=0.7), panels=dict(z=0.6, h=2.4, d=0.35))
    kit.add("TOWER-EAVE", "Limestone", teave, P=print_flip(), group="tower")
    cz0 = TT + R.CORNICE_SMALL[-1][1]
    cprof = FT.tower_cap(None, cz0, TCAP_H, d_flare=3.6, d_top=-4.6, bands=5)
    cap, ctex, cin = R.mansard(TOWER.pts, cprof, t=2.4, tex=dict(pitch=1.4, wtab=1.6, d=0.35, shape=TOWER_SLATE))
    kit.add("TOWER-CAP", "Slate", cap + ctex, group="tower")
    TT_ = R.mansard_top(TOWER.pts, cprof[-1][0], cz0 + TCAP_H, cprof[-1][0] - cin(cz0 + TCAP_H), seams=3.6)
    ttop_path, tdeck = TT_["path"], TT_["z_top"]
    tc = ((TX0 + TX1) / 2, (TY0 + TY1) / 2)
    fpad = box([tc[0] - 1.8, tc[1] - 1.8, tdeck - 0.01], [tc[0] + 1.8, tc[1] + 1.8, tdeck + 1])
    kit.add("TOWER-curb", "Limestone", TT_["ring"], P=print_flip(), group="tower")
    kit.add("TOWER-deck", "Slate", TT_["deck"] - fpad, group="tower")
    tcrest = R.cresting(ttop_path, tdeck, h=2.8, pitch=1.6, d_off=-1.0)
    for i, seg, A, L in R.cresting_strips(tcrest, ttop_path, tdeck, -1.0):
        kit.add(f"TOWER-crest-{i}", "Iron", seg, P=inv34(A), key=f"TOWER-crest-{round(L, 1)}", group="tower")
    kit.add("TOWER-finial", "Iron", finial(1.4, 9.0).translate([tc[0], tc[1], tdeck]), group="tower")
    print("tower", round(time.time() - t0, 1))

    # --- east bay: flat roof with its cornice (upside down) and cresting
    main_keep = MAIN.solid(grow=0.45, dz0=-1, dz1=300)
    broof = max(R.flat_roof(BAY, keep=main_keep).decompose(), key=lambda m: m.volume())   # drop the offcut by the wall
    kit.add("BAY-roof", "Limestone", broof, P=print_flip(), group="bay")
    bz = BAY.z1 + R.CORNICE_SMALL[-1][1]
    bcrest = R.cresting(BAY.pts, bz, h=2.4, pitch=1.6, d_off=3.0) - MAIN.solid(grow=1.0, dz0=-1, dz1=300)
    for i, seg, A, L in R.cresting_strips(bcrest, BAY.pts, bz, 3.0):
        if not seg.is_empty() and seg.volume() > 1.0:
            kit.add(f"BAY-crest-{i}", "Iron", seg, P=inv34(A), group="bay")

    # --- entrance portico: turned posts and railings in one piece, arcades, tin roof
    H_floor = ZF - 1.0
    post_h = (S1 - 0.2) - (H_floor + 5.2)             # the roof tucks under the belt ring
    y0, y1 = TY0 - 1.4, TY0 - 22.0
    px0, px1 = TX0 - 6.0, TX1 + 6.0
    runs = [dict(a=(px0, y0), b=(px0, y1), posts=[1.7, (y0 - y1) - 1.6]),
            dict(a=(px0, y1), b=(px1, y1), posts=[1.6, 12.0, (px1 - px0) - 12.0, (px1 - px0) - 1.6]),
            dict(a=(px1, y1), b=(px1, y0), posts=[1.6, (y0 - y1) - 1.7])]
    P = FT.porch_turned([(px0, y0), (px0, y1), (px1, y1), (px1, y0)], runs, H_floor, post_h,
                        steps_at=[(1, (px1 - px0) / 2, 14.0)], boards=dict(pitch=1.8), joined=True)
    fkeep = slab(offset(cs_union([b.cs for b in BLOCKS]), 0.8 + 0.55 + 0.15), -1, ZF + 1.3)
    ins_keep = union([box(np.array(p.solid.bounding_box()[:3]) - 0.2, np.array(p.solid.bounding_box()[3:]) + 0.2)
                      for p in inserts if p is not None])
    kit.add("PORCH-deck", "Limestone", P["deck"] - fkeep, P=print_flip(), group="porch")
    kit.add("PORCH-floor", "PorchGray", P["floor"] - fkeep, P=print_flip(), group="porch")
    for k, fr in enumerate(sorted(P["frames"], key=lambda m: m.bounding_box()[0])):
        kit.add(f"PORCH-frame-{k}", "Limestone", fr, group="porch")
    for k, (arc, A) in enumerate(P["arcades"]):
        kit.add(f"PORCH-arcade-{k}", "Limestone", arc, P=compose(FT.ARCADE_PRINT, inv34(A)), group="porch")
    bld_keep = union([b.solid(grow=1.45, dz0=-20, dz1=0) for b in BLOCKS]) + TOWER.solid(grow=1.45, dz0=-20, dz1=300)
    proof = P["roof"] - bld_keep - ins_keep
    ptop = proof.bounding_box()[5]
    below = proof.trim_by_plane([0, 0, -1.0], -(ptop - 0.8))
    cap_ = proof.trim_by_plane([0, 0, 1.0], ptop - 0.8)
    inner_cs = M.extrude(cap_.slice(ptop - 0.4).offset(-0.5), 5).translate([0, 0, ptop - 1])
    ribs = union([box([x - 0.25, y1 - 10, ptop - 0.01], [x + 0.25, y0, ptop + 0.4])
                  for x in np.arange(px0 + 1.0, px1, 5.2)]) ^ inner_cs
    kit.add("PORCH-roof", "Limestone", below, P=print_flip(), group="porch")
    kit.add("PORCH-roof-tin", "Slate", cap_ + ribs, group="porch")
    for k, (sm, A) in enumerate(P["steps"]):
        kit.add(f"PORCH-steps-{k}", "Granite", sm.transform(A) - fkeep, group="porch")
    # back stoop
    e, u = MAIN.locate(64.0, Y1)
    f = MAIN.facades()[e]
    A = f.A.copy()
    A[:, 3] = f.world(u, -ZF, 1.4)
    kit.add("STOOP-back", "Granite", FT.steps(14.0, ZF - 0.6, 3).transform(A), group="porch")
    print("porch", round(time.time() - t0, 1))
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "harcourt")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:40]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "harcourt.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))

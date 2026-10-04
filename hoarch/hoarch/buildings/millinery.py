"""Madame Dufresne's Millinery -- an original HO-scale (1:87.1) two-storey milliner's shop, 1880.

A narrow shop with a pressed-metal front on brick side walls in Flemish garden-wall bond. On
the ground floor a canted display bay with a hipped roof stands out on a stone base beside a
door with a lozenge-glazed leaf, a transom of three little arches and a crested cap, up two
stone steps. Over them hangs a sign board lettered "Millinery" in italic capitals and lower
case. An ovolo belt course divides the floors. Upstairs, two 6-over-1 windows under crested
caps sit in the grid of raised pressed-metal panels between plain stiles, and a gilt hat hangs
from an iron arm on the corner stile. Above: a lettered frieze on beaded brackets, a moulded
cap, and a false mansard of octagon-cut slates with a pedimented dormer carrying the date.
Behind it a flat tin roof with a glazed monitor over the workroom and a twin-flue chimney.

The front wall is its own part, printed face-up, so the pressed metal prints as a relief on
top and takes its own colour; the side walls print upright as one U-shaped shell per storey.
Colour comes from the part split (see storefront.py): the sign and frieze take one filament
change for their letters, the hat sign one for its gilt face.

usage: python3 -m hoarch.buildings.millinery [check] [export]
"""
import math
import os
import sys
import time

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import arch_cs, box, cs_union, inv34, offset, poly, rect, slab, union
from hoarch import features as FT, openings as O, skins as SK, storefront as SF, trimwork as TW
from hoarch.kit import Kit
from hoarch.ornament import chamfer_box, ext
from hoarch.shell import Block, Opening, _corbel, foundation, stacked_shells

NAME = "Madame Dufresne's Millinery"
COLORS = {"Metal": "#9E92B4", "Brick": "#A0543C", "Trim": "#EDE4D3", "Plum": "#5A2748", "Sign": "#5A2748",
          "Slate": "#4B5260", "Roof": "#8A3A2C", "Base": "#A69F92", "Blade": "#1E1E1E", "Windows_Doors": "#EDE4D3"}
RENDER_MAT = {"Metal": "metal", "Brick": "brick", "Trim": "trim", "Plum": "plum", "Sign": "plum", "Gilt": "gilt",
              "Slate": "slate", "Roof": "roof", "Base": "base", "Blade": "iron", "Windows_Doors": "trim",
              "Sash": "sash", "Door": "door", "Glass": "glass"}

# ------------------------------------------------------------------ levels (v from the block base)
ZF = 5.0                   # moulded stone base
H1 = 44.0                  # storey joint
S1 = ZF + H1
RH = 4.4                   # the ovolo belt
V2 = H1 + RH               # upper floor
VF, FR_H = V2 + 38.0, 6.4  # frieze over a 38 mm upper storey
VK = VF + FR_H             # cornice cap
CAP_K = 1.3
CAP_PROF = [(CAP_K * a, CAP_K * b) for a, b in
            [(0.0, 0.0), (1.2, 0.0), (1.2, 0.6), (1.6, 1.0), (1.6, 1.6), (2.2, 1.8), (2.6, 2.2), (2.8, 2.8),
             (2.8, 3.2), (0.0, 3.2)]]
CAP_H = CAP_K * 3.2
VTOP = VK + CAP_H          # top of the front wall; the false mansard stands on it
HB = VK                    # side and rear walls
T = 3.0
W, D = 70.0, 110.0
MAIN = Block("main", [(0, 0), (W, 0), (W, D), (0, D)], ZF, ZF + HB)
ZR = ZF + HB - 3.2         # roof ledge (the deck sits on it, 2 mm below the wall tops)

# ------------------------------------------------------------------ the front
STILE = 2.5                # plain stiles at the corners; pressed-metal panels between
PW, PH = 6.5, 38.0 / 8     # panel grid (upper front: 10 x 8 panels, the windows fill 2 columns each)
BAY_U, BAY_W, BAY_P = STILE + 3 * PW, 36.0, 4.4       # the bay fills panel columns 0-5
BAY_BULK, BAY_GLASS, BAY_HEAD = 7.0, 22.0, 2.4
BAY_TOP = BAY_BULK + BAY_GLASS + BAY_HEAD
DOOR_U = STILE + 8 * PW     # its landing fills panel columns 7-8
PIERS = (6, 9)              # the panelled piers downstairs
SIGN_V, SIGN_H = H1 - 7.6, 7.2
WIN_U = (STILE + 2 * PW, STILE + 5 * PW, STILE + 8 * PW)
WIN_V = V2 + 5.0
BLADE_X = W - 0.2
MH, HIP = 14.0, 4.0        # false mansard: height, hip run at each end
DORMER = (W / 2 - 6.0, W / 2 + 6.0, 11.0)    # x0, x1, height to the pediment's foot


def _bay_spec():
    """The display bay as an opening: it plugs into a plain rectangular cut and stands on
    the wall face (the siding stops round it)."""
    solid, glass = SF.display_bay(BAY_W, BAY_P, bulk=BAY_BULK, glass_h=BAY_GLASS, head=BAY_HEAD,
                                  transom=BAY_BULK + BAY_GLASS - 5.0)
    hw = BAY_W / 2
    outside = solid ^ box([-100, -100, 0.0], [100, 100, 100])
    land = outside.project().offset(0.15)
    return dict(insert=solid, glass=glass, sash=M(), frame=solid - glass, surround=solid, back=0.0,
                cut=rect(-hw - O.CLR, 0.0, hw + O.CLR, BAY_TOP + O.CLR), landing=land,
                top=BAY_TOP + BAY_P + 0.4, bottom=0.0)


def _openings():
    L = []

    def add(x, y, v0, sp, name, kind="window"):
        e, u = MAIN.locate(x, y)
        L.append(Opening(MAIN, e, u, v0, sp, name, kind))

    add(BAY_U, 0, 0.0, _bay_spec(), "bay", "door")
    add(DOOR_U, 0, 0.0, SF.door_commercial(10.0, 26.0, transom=4.4, leaf="lozenge", tstyle="scallop", head="crested"),
        "shop-door", "door")
    up = SF.window_commercial(8.4, 21.0, rise=0, lites=(1, 3), rows=(1, 2), sill=1.0, head="crested")
    for u in WIN_U:
        add(u, 0, WIN_V, up, f"F{u:.0f}-2")
    plain = SF.window_commercial(8.4, 21.0, rise=1.6, lites=(1, 3), rows=(1, 2), sill=1.0)
    for y in (30.0, 60.0, 90.0):             # the east side looks over an alley; the west is a party wall
        add(W, y, V2 + 5.0, plain, f"E{y:.0f}-2")
    for y in (60.0, 90.0):
        add(W, y, 10.0, plain, f"E{y:.0f}-1")
    add(W - 14.0, D, 0.0, SF.door_commercial(10.0, 30.0, transom=4.0, leaf="lozenge", tstyle="scallop", head=None),
        "back-door", "door")
    add(W - 40.0, D, 10.0, plain, "N40-1")
    for x in (16.0, 38.0, 58.0):
        add(W - x, D, V2 + 5.0, plain, f"N{x:.0f}-2")
    return L


OPENINGS = _openings()
APPLIED = [("SIGN", STILE + 0.4, SIGN_V, W - 2 * STILE - 0.8, SIGN_H), ("FRIEZE", 0.0, VF, W, FR_H),
           ("CAP", 0.0, VK, W, CAP_H)]


def _applied_openings():
    return [Opening(MAIN, 0, 0.0, 0.0, SF.applied(rect(u0, v0, u0 + L, v0 + h)), name, "trim")
            for name, u0, v0, L, h in APPLIED]


def _siding(f, b, reg):
    if f.n[1] < -0.3:
        # the street front: pressed-metal panels between plain stiles, in whole panels only;
        # upstairs each window takes two panel columns, full height (plain metal round it);
        # downstairs the pier between the bay and the door is panelled
        up = reg ^ rect(STILE, V2 - 0.01, W - STILE, VF)
        for u in WIN_U:
            up = up - rect(u - PW, V2 - 1.0, u + PW, VF + 1.0)
        pier = reg ^ cs_union([rect(STILE + k * PW, -100.0, STILE + (k + 1) * PW, SIGN_V) for k in PIERS])
        stiles = reg ^ (rect(-1.0, -100.0, STILE, VF) + rect(W - STILE, -100.0, W + 1.0, VF))
        return SK.pressed_metal(up, pw=PW, ph=PH, d=0.4, datum=V2, uoff=STILE) + \
            SK.pressed_metal(pier, pw=PW, ph=SIGN_V / 7, d=0.4, datum=0.0, uoff=STILE) + ext(stiles, -0.02, 0.4)
    # brick sides and rear, stopping where the front wall's ends are (y < T)
    ud = f.A[:2, 0]
    if abs(ud[1]) > 0.5:
        ucut = (T - f.p0[1]) / ud[1]
        keep = rect(ucut, -100.0, 1e3, 1e3) if ud[1] > 0 else rect(-1e3, -100.0, ucut, 1e3)
        reg = reg ^ keep
    return SK.brick_bond(reg, "garden", datum=0.0)


def _gilt(solid, A, level, lo):
    top = solid ^ box([-1e3, -1e3, level], [1e3, 1e3, 1e3])
    return [(lo, (solid - top).transform(A)), ("Gilt", top.transform(A))]


def _upright(A):
    """Print transform for a part built in facade frame A that prints standing on its v = 0
    face (local v -> print z, local w -> print -y)."""
    R = np.array([[1.0, 0, 0], [0, 0, -1.0], [0, 1.0, 0]])
    return R @ inv34(A)


def _on_back(y_back, z0):
    """Print transform for a part on the front that lies on its flat back (the plane
    y = y_back) with its front face up."""
    return np.array([[1.0, 0, 0, 0], [0, 0, 1.0, -z0], [0, -1.0, 0, y_back]])


def _mansard():
    """The false mansard (a hipped wedge of octagon-cut slates standing on the front wall and
    the cap) with a notch for the dormer, and the dormer: a pedimented front with pilasters
    and the date in an arched panel. Both print on their backs."""
    zb = ZF + VTOP
    y0, y1 = -1.8, T
    body = M.hull_points([(x, y, zb) for x in (0.0, W) for y in (y0, y1)] +
                         [(x, y, zb + MH) for x in (HIP, W - HIP) for y in (y1 - 1.0, y1)])
    # slates on the sloping front: frame u = x, v up the slope, w out of it
    run = y1 - 1.0 - y0
    L = math.hypot(run, MH)
    vdir = np.array([0.0, run / L, MH / L])
    wdir = np.array([0.0, -MH / L, run / L])
    A = np.column_stack([[1.0, 0, 0], vdir, wdir, [0.0, y0, zb]])
    hip_u = HIP * 1.0
    face = poly([(0.3, 0.0), (W - 0.3, 0.0), (W - hip_u - 0.3, L - 0.3), (hip_u + 0.3, L - 0.3)])
    slates = SK.octagon_slates(face, pitch=1.6, width=2.0, d=0.35).translate([0, 0, -0.02]).transform(A)
    x0, x1, dh = DORMER
    notch = box([x0 - 0.15, y0 - 2.0, zb - 1.0], [x1 + 0.15, y1 - 1.0, zb + MH + 1.0])
    mansard = body + slates - notch
    # the dormer: body to the pediment, then everything added proud of its front (y < yf)
    yf, yb = -2.0, y1 - 1.15
    ped = 3.8
    outline = rect(x0, zb, x1, zb + dh) + poly([(x0, zb + dh - 0.01), (x1, zb + dh - 0.01), ((x0 + x1) / 2, zb + dh + ped)])
    Ad = np.array([[1.0, 0, 0, 0], [0, 0, -1.0, yb], [0, 1.0, 0, 0]])        # (x, z, depth) -> (x, y, z)

    def front(cs, d0, d1):                   # a relief d0..d1 in front of the plane y = yf
        return ext(cs, d0, d1).transform(np.array([[1.0, 0, 0, 0], [0, 0, -1.0, yf], [0, 1.0, 0, 0]]))
    dormer = ext(outline, 0.0, yb - yf).transform(Ad)
    for a in (x0, x1 - 1.4):
        dormer = dormer + front(rect(a, zb, a + 1.4, zb + dh - 1.6), -0.01, 0.4)        # pilasters
    dormer = dormer + front(rect(x0, zb + dh - 1.6, x1, zb + dh), -0.01, 0.6)          # entablature
    tri = poly([(x0, zb + dh), (x1, zb + dh), ((x0 + x1) / 2, zb + dh + ped)])
    dormer = dormer + front(tri - tri.offset(-0.9), -0.01, 0.6)                         # raking cornice
    xa, xb = x0 + 2.0, x1 - 2.0
    panel = arch_cs(xa, xb, zb + 1.6, zb + dh - 1.6 - (xb - xa) / 2 - 0.6, rise=(xb - xa) / 2, seg=32)
    dormer = dormer - front(panel, -0.4, 0.01)
    digits = SF.text_cs("1880", 2.4, "roman", grow=0.1)
    dormer = dormer + front(digits.translate(((x0 + x1) / 2, zb + 3.2)) ^ panel, -0.41, 0.0)
    return mansard, dormer, zb, y1, yb


def _monitor(zd):
    """A glazed roof monitor over the workroom: low walls with four lights a side, a gable
    roof at 40 degrees with 45 degree undercut eaves. Prints upright on the deck."""
    x0, x1, y0, y1 = W / 2 - 8.0, W / 2 + 8.0, 36.0, 64.0
    hwall = 5.0
    body = box([x0, y0, zd], [x1, y1, zd + hwall])
    n = 5
    p = (y1 - y0) / n
    for k in range(n):
        a, b = y0 + k * p + 0.6, y0 + (k + 1) * p - 0.6
        for x in (x0, x1):
            body = body - box([x - 0.3, a, zd + 1.0], [x + 0.3, b, zd + 3.8])
    zt = zd + hwall
    xc, half = (x0 + x1) / 2, (x1 - x0) / 2 + 0.6
    rise = half * math.tan(math.radians(40))
    sec = poly([(x0, zt - 0.6), (x1, zt - 0.6), (x1 + 0.6, zt), (x1 + 0.6, zt + 0.4), (xc, zt + 0.4 + rise),
                (x0 - 0.6, zt + 0.4), (x0 - 0.6, zt)])
    roof = M.extrude(sec, y1 - y0 + 0.8).rotate([90, 0, 0]).translate([0, y1 + 0.4, 0])
    return body + roof


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    base = MAIN.cs
    bprof, _ = TW.BELTS["ovolo"]
    front = rect(0.0, HB - 0.01, W, VTOP)
    st = stacked_shells([MAIN], OPENINGS + _applied_openings(), [S1], t=T, corners="none", siding=_siding, prof=bprof,
                        belt_blocks=None, water_table=False, gables=[(MAIN, 0, front)])
    fcut = box([-5.0, -5.0, -1.0], [W + 5.0, T, 400.0])
    # the side walls lose the corbels and lips along the front (they would bridge the gap)
    inner = box([T + 0.01, -5.0, -1.0], [W - T - 0.01, T + 3.0, 400.0])
    ledge = _corbel(base, T, ZR) - fcut - inner
    f = MAIN.facades()[0]
    Af = f.A.copy()
    Af[:, 3] = f.world(0.0, 0.0, 0.0)
    kit.add("FRONT-1", "Metal", st["shells"][0] ^ fcut, P=inv34(Af), group="walls")
    kit.add("FRONT-2", "Metal", st["shells"][1] ^ fcut, P=inv34(Af), group="walls")
    kit.add("WALLS-1", "Brick", st["shells"][0] - fcut - inner, group="walls")
    kit.add("BELT", "Trim", st["rings"][0], group="walls")
    kit.add("WALLS-2", "Brick", st["shells"][1] - fcut - inner + ledge, group="walls")
    print("walls", round(time.time() - t0, 1))

    ops = {o.name: o for o in OPENINGS}
    bo = ops["bay"]
    Ab = bo.local_frame()
    sp = bo.spec
    kit.add("BAY", "Plum", sp["insert"].transform(Ab), P=_upright(Ab), group="front",
            render=[("Plum", sp["frame"].transform(Ab)), ("Glass", sp["glass"].transform(Ab))])
    for o in OPENINGS:
        if o.name == "bay":
            continue
        s = o.spec
        b = s["cut"].bounds()
        key = "DOOR" if o.kind == "door" else "WIN"
        world, P, zones = O.place(s, o.local_frame(), "Windows_Doors", "Door" if o.kind == "door" else "Sash", "Glass")
        kit.add(f"{key}-{o.name}", "Windows_Doors", world, P=P, key=f"{key}-{o.name.split('-')[0]}-{b[2] - b[0]:.1f}",
                group="inserts", render=zones)

    # --- the base: moulded stone, a plinth under the bay, two steps up to the door
    hw = BAY_W / 2
    plinth = M.extrude(poly([(BAY_U - hw - 0.3, 0.5), (BAY_U - hw + BAY_P - 0.1, -BAY_P - 0.3),
                             (BAY_U + hw - BAY_P + 0.1, -BAY_P - 0.3), (BAY_U + hw + 0.3, 0.5)]), ZF)
    steps = box([DOOR_U - 6.0, -2.4, 0.0], [DOOR_U + 6.0, 0.5, ZF]) + box([DOOR_U - 6.0, -4.8, 0.0], [DOOR_U + 6.0, -2.39, ZF / 2])
    kit.add("FOUNDATION", "Base", foundation([MAIN], 0.0, ZF, style="moulded", lip=1.2) + plinth + steps, group="foundation")

    # --- the front: sign, frieze, cap, hat sign
    def frame_at(u0, v0, w0=0.0):
        A_ = f.A.copy()
        A_[:, 3] = f.world(u0, v0, w0)
        return A_

    sl = W - 2 * STILE - 0.8
    sign = SF.sign_band(sl, SIGN_H, "Millinery", cap=4.6, font="italic", board=1.0, frame=1.0, relief=0.4)
    As = frame_at(STILE + 0.4, SIGN_V)
    kit.add("SIGN", "Sign", sign.transform(As), P=inv34(As), group="front", render=_gilt(sign, As, 1.0, "Sign"))
    ends = [1.0, W - 1.0]
    fr = SF.frieze_band(W, FR_H, board=1.0, tails=dict(us=ends, w=2.0, d=2.4, style="beaded"), text="MME. DUFRESNE",
                        cap=3.6, font="roman")
    Afr = frame_at(0.0, VF)
    kit.add("FRIEZE", "Sign", fr.transform(Afr), P=inv34(Afr), group="front", render=_gilt(fr, Afr, 1.0, "Sign"))
    cap = SF.cornice_cap(W, CAP_PROF) + SF.bracket_row(W, ends + [W / 2 - 16.0, W / 2 + 16.0], 2.0, 3.0, 1.6,
                                                        CAP_K * 1.8, style="beaded")
    Ac = frame_at(0.0, VK)
    kit.add("CAP", "Trim", (cap ^ box([0.0, -1.0, 0.0], [W, 5.2, 5.2])).transform(Ac), P=inv34(Ac), group="front")
    bs = SF.blade_sign(SF.hat_cs(9.0, 6.4), None, t=1.2, arm=12.0, drop=4.0, hang=(-1.0, 0.9))
    Abl = np.array([[0.0, 0.0, -1.0, BLADE_X], [-1.0, 0.0, 0.0, -0.4], [0.0, 1.0, 0.0, ZF + V2 + 16.0]])
    kit.add("BLADE", "Blade", bs.transform(Abl), P=inv34(Abl), group="front", render=_gilt(bs, Abl, 0.8, "Blade"))
    print("front", round(time.time() - t0, 1))

    # --- the false mansard and its dormer
    mansard, dormer, zb, yb_m, yb_d = _mansard()
    kit.add("MANSARD", "Slate", mansard, P=_on_back(yb_m, zb), group="roof")
    kit.add("DORMER", "Trim", dormer, P=_on_back(yb_d, zb), group="roof")

    # --- the flat tin roof (flat-lock sheets in staggered courses), the monitor, the chimney
    inner_cs = offset(base, -T - 0.15)
    deck = slab(inner_cs, ZR, ZR + 1.2)
    bx = inner_cs.bounds()
    grooves = []
    sy, sx = 7.0, 5.0
    for j, y in enumerate(np.arange(bx[1] + sy, bx[3] - 0.5, sy)):
        grooves.append(box([bx[0] - 1, y - 0.25, ZR + 1.0], [bx[2] + 1, y + 0.25, ZR + 2.0]))
    ys = [bx[1]] + list(np.arange(bx[1] + sy, bx[3] - 0.5, sy)) + [bx[3]]
    for j in range(len(ys) - 1):
        off = (j % 2) * sx / 2
        for x in np.arange(bx[0] + sx - off, bx[2] - 0.5, sx):
            grooves.append(box([x - 0.25, ys[j], ZR + 1.0], [x + 0.25, ys[j + 1], ZR + 2.0]))
    zd = ZR + 1.2
    cw, cd = 9.0, 4.5
    cx, cy = W / 2, D - T - 1.2 - cd / 2
    pocket = box([cx - cw / 2 - 0.4, cy - cd / 2 - 0.4, ZR + 0.6], [cx + cw / 2 + 0.4, cy + cd / 2 + 0.4, ZR + 2.0])
    kit.add("ROOF", "Roof", deck - union(grooves) - pocket, group="roof")
    kit.add("MONITOR", "Trim", _monitor(zd), group="roof")
    zc = ZR + 0.6
    ch = TW.chimney("twin", w=cw, d=cd, h=round((ZF + HB + 14.0 - zc) / 0.2) * 0.2).translate([cx, cy, zc])
    kit.add("CHIMNEY", "Brick", ch, group="roof")
    # coping on the side and rear walls
    cop = slab(offset(base, 0.4) - offset(base, -T - 0.3), ZF + HB, ZF + HB + 0.8) - box([-5, -5, 0], [W + 5, T, 400]) - \
        box([T + 0.1, -5, 0], [W - T - 0.1, T + 1.0, 400])        # none across the front: the front wall rises there
    kit.add("COPING", "Base", cop, group="roof")
    print("roof", round(time.time() - t0, 1))
    # glue joints: nothing small is left butted on a dab of glue (see NOTES.md)
    FT.key_into(kit, "BLADE", ["FRONT-2"], (0, 1, 0), depth=2.0)
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "millinery")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:40]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "millinery.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))

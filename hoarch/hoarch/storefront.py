"""Main Street parts: cast-iron storefronts, recessed entries, sign bands, applied cornices
(a frieze course and a bracketed cap: the "double eave"), name-and-date tablets, commercial
windows and doors, and raised lettering.

Almost everything here is applied trim in a facade's (u, v, w) frame (u along the wall, v up,
w = 0 on the wall face and out of it) and prints face-up: its back on the bed, so every
(u, v) column of a part is solid from the bed to its surface and nothing overhangs. Flat
faces sit at w = multiples of 0.2 measured from the part's back, so none lands on a slicing
plane. The one exception is the vestibule (a recessed entry), which prints upright on its
floor.

Each part is one colour. A building's colour scheme comes from the part split (walls,
storefront, sign, cornice layers, windows) rather than from painting, and the cornices come
in two layers so the frieze and the cap can be two colours.
"""
import math

import numpy as np
from manifold3d import CrossSection as CS, FillRule, JoinType, Manifold as M

from .core import arch_cs, box, circle, cs_union, poly, rect, slab, union
from .ornament import chamfer_box, ext, stroke

PLUG = 1.6      # depth into the wall opening (as the windows)
GLASS = 0.4

FONTS = {"serif": "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
         "sans": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
         "grotesque": "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
         "roman": "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
         "mono": "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
         "italic": "/usr/share/fonts/truetype/liberation/LiberationSerif-BoldItalic.ttf"}


def zq(v):
    return round(v / 0.2) * 0.2


# ------------------------------------------------------------------ lettering
def text_cs(text, cap=3.0, font="serif", grow=0.08, track=0.0):
    """Raised-letter outline for ``text``: capitals ``cap`` tall, baseline at v = 0, centred
    on u = 0. ``grow`` thickens every stroke (hairlines of a bold serif at HO size are finer
    than the nozzle); ``track`` adds space between letters."""
    from matplotlib.font_manager import FontProperties
    from matplotlib.textpath import TextPath, TextToPath
    fp = FontProperties(fname=FONTS.get(font, font))
    hv = TextPath((0, 0), "H", size=10.0, prop=fp).vertices
    size = cap / (hv[:, 1].max() / 10.0)
    ttp = TextToPath()
    polys = []
    for i, ch in enumerate(text):
        if ch == " ":
            continue
        x = ttp.get_text_width_height_descent(text[:i], fp, ismath=False)[0] * size / fp.get_size_in_points() \
            if i else 0.0
        tp = TextPath((x + i * track, 0.0), ch, size=size, prop=fp)
        polys += [np.array(p[:-1], float) for p in tp.to_polygons(closed_only=True) if len(p) > 3]
    if not polys:
        return CS()
    cs = CS(polys, FillRule.EvenOdd)
    if grow:
        cs = cs.offset(grow, JoinType.Round)
    b = cs.bounds()
    return cs.translate(((-(b[0] + b[2]) / 2), 0.0))


# ------------------------------------------------------------------ profiles swept along u
def run_profile(L, prof, u0=0.0):
    """A straight moulding: profile [(w, v), ...] (w out of the wall, v up; a closed polygon
    with its back on w = 0) extruded along u from u0 to u0 + L."""
    cs = poly([(v, w) for w, v in prof])            # plane (v, w)
    m = M.extrude(cs, L)                            # along +z
    A = np.array([[0.0, 0.0, 1.0, u0],              # (v, w, z) -> (u = z, v, w)
                  [1.0, 0.0, 0.0, 0.0],
                  [0.0, 1.0, 0.0, 0.0]])
    return m.transform(A)


# ------------------------------------------------------------------ the storefront
def _column(style, u0, u1, v0, v1, cap_h=2.4, base_h=3.0):
    """A cast-iron pilaster between u0..u1 and v0..v1 (face-up, back at w = 0)."""
    parts = [chamfer_box(u0 - 0.2, v0, u1 + 0.2, v0 + base_h, 0.0, 1.2, c=0.3, bottom=0.0)]
    parts.append(box([u0, v0 + base_h - 0.01, 0.0], [u1, v1 - cap_h + 0.01, 0.8]))
    um = (u0 + u1) / 2
    s0, s1 = v0 + base_h + 1.0, v1 - cap_h - 1.0
    cut = None
    if style == "fluted" and s1 - s0 > 3:
        cut = union([box([x - 0.25, s0, 0.4], [x + 0.25, s1, 1.0]) for x in (um - 0.5, um + 0.5)])
    elif style == "panel" and s1 - s0 > 3:
        cut = box([u0 + 0.5, s0, 0.6], [u1 - 0.5, s1, 1.0])
    if cut is not None:
        parts[-1] = parts[-1] - cut
    if style == "rosette" and s1 - s0 > 3:       # a column of round bosses up the shaft
        n = max(2, int((s1 - s0) / 3.2))
        for k in range(n):
            vv = s0 + (s1 - s0) * (k + 0.5) / n
            parts.append(ext(circle((um, vv), min(0.6, (u1 - u0) / 2 - 0.35), 16), 0.79, 1.2))
    if style == "chamfered" and s1 - s0 > 3:     # a wooden pilaster: a raised chamfered shaft with stops
        parts.append(chamfer_box(u0 + 0.3, s0 - 0.6, u1 - 0.3, s1 + 0.6, 0.79, 0.41, c=0.21))     # faces on the grid
    if style == "panel":
        parts.append(ext(circle((um, (s0 + s1) / 2), 0.55, 16), 0.59, 1.0))      # a boss in the panel
    # capital: necking, a bell flaring out, the abacus
    c0 = v1 - cap_h
    parts.append(box([u0 - 0.1, c0, 0.0], [u1 + 0.1, c0 + 0.6, 1.0]))
    parts.append(chamfer_box(u0 - 0.35, c0 + 0.6, u1 + 0.35, v1, 0.0, 1.2, c=0.3, bottom=0.0))
    return union(parts)


def storefront(W, H, entry=14.0, entry_at=0.0, col=2.4, style="fluted", bulk=7.2, transom=6.4, beam=2.0,
               lite=2.4, bulk_style="panel", mullion=True, posts=True, t=3.0, grid=None, bays=1):
    """Cast-iron storefront filling a W x H opening (u centred, v from 0), one part printed
    face-up (plug back on the bed, no supports): pilasters at both ends and either side of a
    recessed entry ``entry`` wide at ``entry_at``, panelled bulkheads under the display
    windows, a sill, the display glass, a transom bar and a band of prism-glass transom
    lights ``lite`` wide, and a beam under the sign band. The entry is an opening through the
    part: the vestibule (its own part) stands behind it.

    ``posts``: a brick post (returned as ``posts``, local frame, for the wall part of a wall
    ``t`` thick) stands behind every inner column, so the wall over the storefront bridges
    only from post to post instead of across the whole front. The posts' fronts come to a
    steep point and the plug has a matching V notch: the wall still prints upright and the
    storefront face-up without supports.

    Returns the insert dict of openings.py (insert, glass / sash / frame zones, cut, landing,
    top, bottom, back) plus ``entry`` = (u centre, width, height) for the vestibule."""
    op = rect(-W / 2, 0.0, W / 2, H)
    vt = zq(H - beam - transom)                  # transom lights' bottom
    ve = vt - 0.8                                # the entry opening's top = the transom bar's bottom
    cols = [(-W / 2, -W / 2 + col), (W / 2 - col, W / 2)]
    if entry <= 0 and bays > 1:                  # no entry: ``bays`` display bays between columns
        for k in range(1, bays):
            c = -W / 2 + W * k / bays
            cols.append((c - col / 2, c + col / 2))
    ent = None
    if entry > 0:
        e0, e1 = entry_at - entry / 2, entry_at + entry / 2
        cols += [(e0 - col, e0), (e1, e1 + col)]
        ent = rect(e0, 0.0, e1, ve)
    cols.sort()
    plug_cs = op - ent if ent is not None else op
    post_m = notch = M()
    if posts:
        A = np.array([[1.0, 0, 0, 0], [0, 0, 1.0, 0], [0, 1.0, 0, 0]])       # (u, w, v) -> (u, v, w)
        pm, nm = [], []
        for a, b in cols:
            if a < -W / 2 + 0.01 or b > W / 2 - 0.01:
                continue                        # the jambs carry the ends
            c = (a + b) / 2
            hw = 1.2                            # the V's sides rise 1.6 in 1.2: 37 degrees off vertical
            sec = poly([(c - hw, -t), (c + hw, -t), (c + hw, -PLUG), (c, 0.0), (c - hw, -PLUG)])
            pm.append(M.extrude(sec, H + 0.2).transform(A))
            nm.append(M.extrude(sec.offset(0.15, JoinType.Miter, 4.0), H + 2.0).translate([0, 0, -1.0]).transform(A))
        post_m, notch = union(pm), union(nm)
    # display bays: between neighbouring columns, except the entry
    bays = []
    for (a0, a1), (b0, b1) in zip(cols[:-1], cols[1:]):
        if ent is not None and a1 <= entry_at <= b0:
            continue
        bays.append((a1, b0))
    glass = []
    for a, b in bays:
        g = rect(a + 0.8, bulk + 0.8, b - 0.8, vt - 0.8 - 0.6)
        glass.append(g)
    # transom lights between the columns (above the entry too), each run divided into
    # prism-glass lights of equal width
    tls, bars = [], []
    for (a0, a1), (b0, b1) in zip(cols[:-1], cols[1:]):
        a, b = a1 + 0.4, b0 - 0.4
        tls.append(rect(a, vt + 0.4, b, H - beam - 0.4))
        nl = max(1, int(round((b - a) / lite)))
        bars += [rect(a + (b - a) * k / nl - 0.25, vt, a + (b - a) * k / nl + 0.25, H) for k in range(1, nl)]
    glass_cs = cs_union(glass + tls)
    sash = [ext(glass_cs, -PLUG, -PLUG + GLASS) - notch, ext(plug_cs - glass_cs, -PLUG, 0.0) - notch]
    # a centre mullion in wide display windows
    if mullion:
        for a, b in bays:
            if b - a > 18.0:
                m_ = (a + b) / 2
                bars.append(rect(m_ - 0.35, bulk, m_ + 0.35, vt))
    if grid:                                         # small-paned display windows: muntins
        gc, gr = grid
        for a, b in bays:
            g0, g1 = a + 0.8, b - 0.8
            h0, h1 = bulk + 0.8, vt - 0.8 - 0.6
            bars += [rect(g0 + (g1 - g0) * k / gc - 0.25, h0, g0 + (g1 - g0) * k / gc + 0.25, h1) for k in range(1, gc)]
            bars += [rect(g0, h0 + (h1 - h0) * k / gr - 0.25, g1, h0 + (h1 - h0) * k / gr + 0.25) for k in range(1, gr)]
    sash.append(ext(cs_union(bars) ^ glass_cs, -PLUG + GLASS - 0.01, -0.4))
    parts = []
    for a, b in bays:
        # bulkhead: a raised panel (or a lozenge) on the frame
        if bulk_style == "panel":
            parts.append(chamfer_box(a + 0.8, 1.2, b - 0.8, bulk - 0.6, -0.01, 0.4, c=0.2))
        elif bulk_style == "tile":                 # a grid of small raised square tiles
            parts.append(box([a + 0.8, 1.2, -0.01], [b - 0.8, bulk - 0.6, 0.2]))
            nu = max(2, int((b - a - 1.6) / 1.4))
            nv = max(2, int((bulk - 1.8) / 1.4))
            tw = (b - a - 1.6) / nu
            th = (bulk - 1.8) / nv
            for i in range(nu):
                for j in range(nv):
                    parts.append(box([a + 0.8 + i * tw + 0.25, 1.2 + j * th + 0.25, 0.19],
                                     [a + 0.8 + (i + 1) * tw - 0.25, 1.2 + (j + 1) * th - 0.25, 0.6]))
        elif bulk_style == "boards":               # vertical beaded boards
            parts.append(box([a + 0.8, 1.2, -0.01], [b - 0.8, bulk - 0.6, 0.4]) -
                         union([box([x - 0.25, 1.6, 0.2], [x + 0.25, bulk - 1.0, 1.0])
                                for x in np.arange(a + 2.0, b - 1.2, 1.2)]))
        elif bulk_style == "lozenge":
            parts.append(box([a + 0.8, 1.2, -0.01], [b - 0.8, bulk - 0.6, 0.2]))
            cu, cv = (a + b) / 2, bulk / 2 + 0.3
            hw, hh = (b - a) / 2 - 2.0, (bulk - 1.8) / 2 - 0.3
            parts.append(ext(poly([(cu - hw, cv), (cu, cv + hh), (cu + hw, cv), (cu, cv - hh)]), 0.19, 0.6))
        # the sill, and a bead round the display glass
        parts.append(box([a, bulk, 0.0], [b, bulk + 0.8, 0.6]))
        g = rect(a + 0.8, bulk + 0.8, b - 0.8, vt - 0.8 - 0.6)
        parts.append(ext(rect(a, bulk + 0.8, b, vt - 0.8) - g, -0.01, 0.2))      # the glazing stop, wall to wall
    parts.append(box([-W / 2, vt - 0.8, 0.0], [W / 2, vt, 0.4]))              # transom bar
    parts.append(box([-W / 2, H - beam, 0.0], [W / 2, H, 0.4]))               # beam
    parts.append(box([-W / 2, H - beam, 0.0], [W / 2, H - beam + 0.6, 0.6]))  # its bed moulding
    for a, b in cols:
        parts.append(_column(style, a, b, 0.0, H - beam))
    frame = (union(parts) ^ ext(plug_cs, -PLUG - 1, 5.0)) - notch     # nothing past the plug: no support needed
    sash_m = union(sash)
    ins = sash_m + frame
    n = len(ins.decompose())
    if n > 1:
        print("  WARNING: storefront falls into", n, "pieces")
    gl = sash_m ^ ext(glass_cs.offset(0.01), -PLUG - 1.0, -PLUG + GLASS)
    return dict(insert=ins, glass=gl, sash=sash_m - gl, frame=frame, surround=frame, back=0.0,
                cut=op, landing=op.offset(0.15, JoinType.Miter, 4.0), top=H, bottom=0.0, posts=post_m,
                entry=(entry_at, entry, ve) if ent is not None else None, cols=cols)


def vestibule(entry, depth, v_top, bulk=7.2, side=0.8, door_h=None, transom=True, front=-PLUG, doors="pair"):
    """The recessed entry behind a storefront, as its own part: a floor (a step up from the
    sidewalk), side walls whose inner faces carry a panelled base and a display-glass panel,
    a back wall with a pair of half-glazed doors (and a transom light), and a ceiling.
    Local frame as the storefront (u centred on the entry, v up, w out; it stands behind the
    storefront, w <= ``front``: -PLUG, or the wall's inner face when the storefront leaves
    posts in the wall). ``doors``: "pair" of half-glazed leaves, or one "single" leaf with a
    big light. Prints upright on its floor; the ceiling bridges the entry."""
    wl = entry / 2
    wo = wl + side
    w0 = front
    wb = front - depth                         # the door plane
    parts = [box([-wo, 0.0, wb - 0.8], [wo, 0.8, w0]),                   # floor
             box([-wo, v_top, wb - 0.8], [wo, v_top + 0.8, w0]),         # ceiling
             box([-wo, 0.8, wb - 0.8], [wo, v_top, wb])]                  # back wall
    for sg in (-1, 1):
        u0, u1 = sorted((sg * wl, sg * wo))
        parts.append(box([u0, 0.8, wb - 0.8], [u1, v_top, w0]))
    body = union(parts)
    cuts, adds = [], []
    for sg in (-1, 1):
        # inner faces: a display-glass panel (recessed) over a raised panel
        ui = sg * wl
        g0, g1 = sorted((ui, ui + sg * 0.3))
        cuts.append(box([g0, bulk + 0.8, wb + 0.8], [g1, v_top - 0.8, w0 - 0.4]))
        r0, r1 = sorted((ui, ui - sg * 0.3))
        adds.append(box([r0, 1.6, wb + 1.0], [r1, bulk - 0.4, w0 - 1.0]))
    dh = zq(door_h if door_h is not None else v_top - (3.2 if transom else 1.2))
    dw = wl - 0.6
    # doors: the frame stands 0.4 proud; each leaf has glass over a raised panel
    adds.append(box([-dw - 0.6, 0.8, wb], [dw + 0.6, dh + 0.6, wb + 0.4]) -
                box([-dw, 0.8, wb - 1], [dw, dh, wb + 1]))
    if doors == "glass_pair":                 # two fully glazed leaves with a grid of lights
        for sg in (-1, 1):
            a0, a1 = sorted((sg * 0.25, sg * dw))
            adds.append(box([a0 + 0.5, 1.4, wb - 0.01], [a1 - 0.5, zq(dh * 0.18), wb + 0.3]))
            g0, g1, h0, h1 = a0 + 0.6, a1 - 0.6, zq(dh * 0.24), zq(dh - 0.8)
            cuts.append(box([g0, h0, wb - 0.3], [g1, h1, wb + 0.01]))
            for k in (1, 2):
                vv = zq(h0 + (h1 - h0) * k / 3)
                adds.append(box([g0 - 0.1, vv - 0.2, wb - 0.3], [g1 + 0.1, vv + 0.2, wb + 0.01]))
            um = (g0 + g1) / 2
            adds.append(box([um - 0.2, h0 - 0.1, wb - 0.3], [um + 0.2, h1 + 0.1, wb + 0.01]))
        cuts.append(box([-0.25, 0.8, wb - 0.3], [0.25, dh, wb + 0.01]))
    elif doors == "single":
        adds.append(box([-dw + 0.9, 1.4, wb - 0.01], [dw - 0.9, zq(dh * 0.3), wb + 0.3]))   # low panel
        adds.append(box([-dw + 0.9, 0.8, wb - 0.01], [dw - 0.9, 1.2, wb + 0.3]))            # kick plate
        cuts.append(box([-dw + 1.0, zq(dh * 0.36), wb - 0.3], [dw - 1.0, zq(dh - 0.8), wb + 0.01]))
        vb = zq(dh * 0.52)
        adds.append(box([-dw + 0.7, vb - 0.2, wb - 0.3], [dw - 0.7, vb + 0.4, wb + 0.3]))     # push bar
        adds.append(M.cylinder(0.5, 0.3, 0.3, 12).translate([dw - 1.6, zq(dh * 0.33), wb - 0.1]))        # knob
    else:
        for sg in (-1, 1):
            a0, a1 = sorted((sg * 0.25, sg * dw))
            adds.append(box([a0 + 0.5, 1.6, wb - 0.01], [a1 - 0.5, dh * 0.38, wb + 0.3]))
            cuts.append(box([a0 + 0.6, dh * 0.45, wb - 0.3], [a1 - 0.6, dh - 0.8, wb + 0.01]))
            kx = sg * 0.9
            adds.append(M.cylinder(0.5, 0.3, 0.3, 12).rotate([-90, 0, 0]).translate([kx, dh * 0.42, wb]))
        cuts.append(box([-0.25, 0.8, wb - 0.3], [0.25, dh, wb + 0.01]))       # the meeting stiles
    if transom and v_top - dh > 2.0:
        cuts.append(box([-dw, dh + 0.6, wb - 0.3], [dw, v_top - 0.6, wb + 0.01]))
    return (body - union(cuts)) + union(adds)


# ------------------------------------------------------------------ applied bands (face-up)
def console(h, d, t, u, v_top, style="scroll"):
    """A small end console under a sign band or cornice (face-up: back at w = 0)."""
    from .trimwork import bracket
    b = bracket(style, h, d, t, u=u, v_top=v_top, w0=0.0)
    return b ^ box([u - t, v_top - h - 5, 0.0], [u + t, v_top + 5, d + 5])      # its back on the wall plane


def sign_band(L, h=6.0, text=None, cap=3.0, font="serif", board=1.0, frame=0.8, relief=0.4, track=0.0,
              ends=None, end_w=2.0):
    """The storefront's sign band (the lower layer of its double cornice): a board ``h`` tall
    with a moulded frame and raised lettering, and optional end blocks (``ends`` = a console
    style hung under each end). Local u 0..L, v 0..h, w out; prints face-up."""
    parts = [box([0, 0, 0], [L, h, board])]
    ring = rect(0, 0, L, h) - rect(frame, frame, L - frame, h - frame)
    parts.append(ext(ring, board - 0.01, board + relief))
    if text:
        t = text_cs(text, cap, font, track=track)
        tb = t.bounds()
        room = L - 2 * frame - 2 * (end_w if ends else 0) - 1.0
        if tb[2] - tb[0] > room:
            print(f"  WARNING: sign text {text!r} is {tb[2] - tb[0]:.1f} wide for {room:.1f}")
        parts.append(ext(t.translate((L / 2, (h - cap) / 2)), board - 0.01, board + relief))
    if ends:
        for u0 in (0.0, L - end_w):
            parts.append(chamfer_box(u0, 0.0, u0 + end_w, h, 0.0, board + relief + 0.2, c=0.3))
            parts.append(console(3.2, 1.8, end_w - 0.4, u0 + end_w / 2, 0.01, style=ends))
    return union(parts)


def cornice_cap(L, prof, dentils=None, ends=True):
    """The upper layer of a double cornice: a moulding ``prof`` [(w, v), ...] run along u
    from 0 to L, with an optional dentil course (dict(v, h, d, tooth=0.6, gap=0.6)) under its
    soffit. The ends are closed square. Prints face-up."""
    m = run_profile(L, prof)
    if dentils:
        v0, h, d = dentils["v"], dentils["h"], dentils["d"]
        tooth, gap = dentils.get("tooth", 0.6), dentils.get("gap", 0.6)
        n = int((L - 1.0) / (tooth + gap))
        off = (L - n * (tooth + gap) + gap) / 2
        m = m + union([box([off + k * (tooth + gap), v0, 0.0], [off + k * (tooth + gap) + tooth, v0 + h, d])
                       for k in range(n)])
    return m


def frieze_band(L, h, board=1.2, panels=None, tails=None, text=None, cap=2.4, font="serif", relief=0.4):
    """The lower layer of a double top cornice: a frieze board with raised panels (``panels``
    = [(u0, u1), ...]), bracket tails (``tails`` = dict(us=[u...], w=, d=, style=)) hanging
    under the cornice's brackets, and optional raised lettering centred. Prints face-up."""
    parts = [box([0, 0, 0], [L, h, board])]
    for u0, u1 in (panels or []):
        parts.append(chamfer_box(u0, 0.8, u1, h - 0.8, board - 0.01, relief, c=0.2))
    if tails:
        for u in tails["us"]:
            parts.append(console(h, tails.get("d", 1.6), tails.get("w", 1.0), u, h, style=tails.get("style", "pendant")))
    if text:
        t = text_cs(text, cap, font)
        parts.append(ext(t.translate((L / 2, (h - cap) / 2)), board - 0.01, board + relief))
    return union(parts)


def bracket_row(L, us, h, d, t, v_top, style="scroll"):
    """Brackets at the u positions ``us`` under a cornice cap (top at v_top). Face-up."""
    return union([console(h, d, t, u, v_top, style=style) for u in us])


def name_tablet(W, h, text=None, date=None, cap=2.8, font="serif", head="segment", board=1.2, relief=0.4):
    """A raised name-and-date tablet for the top of a front: a board with a segmental or
    triangular head, a moulded rim, the name and the date in raised letters, and scroll
    shoulders. Local u centred, v from 0 (on the cornice), w out. Prints face-up."""
    rise = h * 0.35
    if head == "segment":
        outline = arch_cs(-W / 2, W / 2, 0.0, h - rise, rise=rise, seg=48)
    else:
        outline = poly([(-W / 2, 0), (W / 2, 0), (W / 2, h - rise), (0, h), (-W / 2, h - rise)])
    parts = [ext(outline, 0.0, board)]
    parts.append(ext(outline - outline.offset(-0.8, JoinType.Miter, 4.0), board - 0.01, board + relief))
    y = 1.2
    if date:
        d = text_cs(date, max(2.4, cap * 0.85), font, grow=0.1)
        parts.append(ext(d.translate((0.0, y)), board - 0.01, board + relief))
        y += max(2.4, cap * 0.85) + 1.0
    if text:
        t = text_cs(text, cap, font, grow=0.1)
        parts.append(ext(t.translate((0.0, y)), board - 0.01, board + relief))
    # scroll shoulders at the foot
    for sg in (-1, 1):
        c = (sg * (W / 2 + 1.2), 1.2)
        sc = circle(c, 1.2, 24) - circle(c, 0.55, 16) + rect(min(sg * W / 2, c[0]), 0.0, max(sg * W / 2, c[0]), 1.2)
        parts.append(ext(sc, 0.0, board))
    return union(parts)


def applied(landing, top=None, bottom=None):
    """An 'opening' spec for trim applied to a facade: no cut, only a landing where the
    siding stops so the trim sits flat on the wall."""
    b = landing.bounds()
    return dict(cut=CS(), landing=landing, top=b[3] if top is None else top, bottom=b[1] if bottom is None else bottom,
                insert=M(), glass=M(), sash=M(), frame=M(), surround=M(), back=0.0)


# ------------------------------------------------------------------ commercial windows and doors
def window_commercial(w, h, rise=2.0, lites=(1, 1), rows=(1, 1), sill=1.2, casing=0.6, head=None, hood_w=1.2):
    """A plain commercial window for a brick front: a narrow brickmould casing round a
    segmental (``rise``) or flat head, sash with ``lites``/``rows``, a stone sill with lugs
    (``sill`` = its projection), and optionally a head: "hood" (a cast-iron segmental hood
    with ears), "lintel" (a stone lintel with a keystone), "archivolt" (a stepped arch band
    with a keystone and imposts), "pediment" (frieze, cornice and a triangular pediment),
    "shouldered" (a flat lintel with shouldered ends and a rosette), "drip" (a bevelled drip
    cap), "crested" (a cap with a cresting of little arches), "triple" (a lintel with a
    stepped triple keystone), "halo" (a round moulding over a round head, with a drop
    keystone), "rosettes" (a head board with three rosette blocks under a cap), "ancon" (a
    square architrave round an arched head, a frieze and a cap on scroll consoles) or
    "cartouche" (a moulded hood with ears and an oval cartouche at the crown). The brick arch of a brick
    building belongs to the wall's skin (skins.brick_arches). Prints face-up."""
    from .openings import CLR, _one_piece, opening_cs, window_insert
    op = opening_cs(w, h, rise if rise else 0)
    plug_cs = op.offset(-CLR, JoinType.Miter, 4.0)
    sash = window_insert(w, h, rise if rise else 0, lites=lites, rows=rows, bare=True)["insert"]
    parts = [ext(op - op.offset(-0.5, JoinType.Miter, 4.0), 0.0, 0.6)]
    parts.append(ext((op.offset(casing, JoinType.Miter, 4.0) - op) ^ rect(-w, 0.0, w, h + casing + 1), 0.0, 0.4))
    top = h + casing
    if head == "hood":
        spring = h - (rise or 0)
        hood = (op.offset(casing + hood_w, JoinType.Round) - op.offset(casing, JoinType.Round)) ^ \
            rect(-w, spring - 0.01, w, h + 10)
        parts.append(ext(hood, 0.0, 1.0))
        for sg in (-1, 1):
            u = sg * (w / 2 + casing + hood_w / 2)
            parts.append(chamfer_box(u - hood_w / 2 - 0.2, spring - 1.6, u + hood_w / 2 + 0.2, spring + 0.2, 0.0, 1.2, c=0.3))
        top = h + casing + hood_w
    elif head == "archivolt":
        # a moulded arch band round the head in two steps, a keystone and impost blocks
        spring = h - (rise or 0)
        clip = rect(-w, spring - 0.01, w, h + 20)
        outer = op.offset(casing + hood_w, JoinType.Round)
        parts.append(ext((outer - op.offset(casing, JoinType.Round)) ^ clip, 0.0, 0.6))
        parts.append(ext((outer - op.offset(casing + hood_w * 0.5, JoinType.Round)) ^ clip, 0.0, 1.0))
        kt = h + casing + hood_w + 0.8
        parts.append(ext(poly([(-0.7, h + casing - 0.4), (0.7, h + casing - 0.4), (1.0, kt), (-1.0, kt)]), 0.0, 1.4))
        for sg in (-1, 1):
            u = sg * (w / 2 + casing + hood_w / 2)
            parts.append(chamfer_box(u - hood_w / 2 - 0.3, spring - 1.2, u + hood_w / 2 + 0.3, spring + 0.01, 0.0, 1.2,
                                     c=0.3))
        top = kt
    elif head == "pediment":
        # a frieze, a cornice and a triangular pediment over the casing
        pw = w / 2 + casing + 1.0
        v0 = h + casing
        parts.append(box([-pw + 0.4, v0 - 0.01, 0.0], [pw - 0.4, v0 + 1.2, 0.6]))
        parts.append(chamfer_box(-pw, v0 + 1.2, pw, v0 + 1.8, 0.0, 1.0, c=0.3))
        v1 = v0 + 1.8
        tri = poly([(-pw, v1 - 0.01), (pw, v1 - 0.01), (0.0, v1 + pw * 0.42)])
        parts.append(ext(tri, 0.0, 0.4))
        parts.append(ext(tri - tri.offset(-0.7, JoinType.Miter, 4.0), 0.0, 1.0))
        top = v1 + pw * 0.42
    elif head == "crested":
        hp, top = _crested(w / 2 + casing + 0.8, h + casing)
        parts += hp
    elif head == "peak":
        # Stick style: a frieze board with a small raised disc under a steep peaked gablet
        lw = w / 2 + casing + 0.8
        v0 = h + casing
        parts.append(box([-lw + 0.4, v0 - 0.01, 0.0], [lw - 0.4, v0 + 1.4, 0.6]))
        tri = poly([(-lw, v0 + 1.39), (lw, v0 + 1.39), (0.0, v0 + 1.39 + lw * 0.9)])
        parts.append(ext(tri, 0.0, 0.6))
        parts.append(ext(tri - tri.offset(-0.6, JoinType.Miter, 4.0), 0.59, 1.0))
        parts.append(ext(circle((0.0, v0 + 1.39 + lw * 0.3), min(0.9, lw * 0.2), 16), 0.59, 1.0))
        top = v0 + 1.39 + lw * 0.9
    elif head == "rosettes":
        # Eastlake: a flat head board with three raised square rosette blocks under a cap
        lw = w / 2 + casing + 0.6
        v0 = h + casing
        parts.append(box([-lw, v0 - 0.01, 0.0], [lw, v0 + 1.8, 0.6]))
        for u in (-lw * 0.62, 0.0, lw * 0.62):
            parts.append(chamfer_box(u - 0.7, v0 + 0.2, u + 0.7, v0 + 1.6, 0.59, 0.4, c=0.15))
            parts.append(ext(circle((u, v0 + 0.9), 0.35, 12), 0.98, 1.2))
        parts.append(chamfer_box(-lw - 0.3, v0 + 1.8, lw + 0.3, v0 + 2.4, 0.0, 1.0, c=0.2, bottom=0.6))
        top = v0 + 2.4
    elif head == "halo":
        # a round moulding following the casing round the head, with a small drop keystone
        spring = h - (rise or 0)
        clip = rect(-w, spring - 0.01, w, h + 20)
        ring = (op.offset(casing + 1.0, JoinType.Round) - op.offset(casing - 0.01, JoinType.Round)) ^ clip
        parts.append(ext(ring, 0.0, 0.8))
        kt = h + casing + 1.4
        parts.append(ext(poly([(-0.6, h + casing - 0.3), (0.6, h + casing - 0.3), (0.8, kt), (-0.8, kt)]), 0.0, 1.2))
        top = kt
    elif head == "triple":
        # a flat stone lintel with a stepped triple keystone
        lw = w / 2 + casing + 1.0
        v0 = h + casing
        parts.append(chamfer_box(-lw, v0 - 0.01, lw, v0 + 1.8, 0.0, 0.8, c=0.2))
        parts.append(chamfer_box(-0.8, v0 - 0.6, 0.8, v0 + 2.6, 0.0, 1.2, c=0.3))
        for sg in (-1, 1):
            parts.append(chamfer_box(sg * 1.3 - 0.5, v0 - 0.3, sg * 1.3 + 0.5, v0 + 2.2, 0.0, 1.0, c=0.25))
        top = v0 + 2.6
    elif head == "drip":
        # a plain drip cap: a board with a bevelled top
        dw = w / 2 + casing + 0.6
        parts.append(box([-dw, h + casing - 0.01, 0.0], [dw, h + casing + 1.0, 0.8]))
        parts.append(chamfer_box(-dw - 0.3, h + casing + 1.0, dw + 0.3, h + casing + 1.8, 0.0, 1.2, c=0.4, bottom=0.8))
        top = h + casing + 1.8
    elif head == "shouldered":
        # a flat lintel whose ends step up into shoulders, with a raised rosette at the centre
        lw = w / 2 + casing + 1.2
        parts.append(chamfer_box(-lw, h + casing - 0.01, lw, h + casing + 1.6, 0.0, 0.8, c=0.2))
        for sg in (-1, 1):
            a, b = sorted((sg * lw, sg * (lw - 1.8)))
            parts.append(chamfer_box(a, h + casing + 1.59, b, h + casing + 2.6, 0.0, 0.8, c=0.2))
        parts.append(ext(circle((0.0, h + casing + 0.8), 0.6, 16), 0.79, 1.2))
        top = h + casing + 2.6
    elif head == "ancon":
        # Italianate: the arch set in a square architrave (its spandrels filled), a frieze and
        # a cornice cap carried on a scroll console (an ancon) at each side (the Laurel)
        lw = w / 2 + casing
        v0 = h + casing
        spring = h - (rise or 0)
        parts.append(ext(rect(-lw, spring, lw, v0) - op.offset(casing - 0.02, JoinType.Round), 0.0, 0.4))
        parts.append(box([-lw, v0 - 0.01, 0.0], [lw, v0 + 1.4, 0.6]))
        parts.append(chamfer_box(-lw - 1.4, v0 + 1.4, lw + 1.4, v0 + 2.2, 0.0, 1.2, c=0.3, bottom=0.8))
        for sg in (-1, 1):
            u = sg * (lw + 0.6)
            parts.append(chamfer_box(u - 0.6, v0 - 2.4, u + 0.6, v0 + 1.41, 0.0, 1.0, c=0.3, bottom=1.0))
            parts.append(ext(circle((u, v0 - 2.6), 0.5, 16), 0.0, 0.8))
        top = v0 + 2.2
    elif head == "cartouche":
        # a moulded hood following the head, with ears at the springing and a raised oval
        # cartouche with scrolled sides at the crown (the Myrtle)
        spring = h - (rise or 0)
        clip = rect(-w, spring - 0.01, w, h + 20)
        band = (op.offset(casing + 1.0, JoinType.Round) - op.offset(casing - 0.01, JoinType.Round)) ^ clip
        parts.append(ext(band, 0.0, 0.8))
        for sg in (-1, 1):
            u = sg * (w / 2 + casing + 0.5)
            parts.append(chamfer_box(u - 0.9, spring - 0.8, u + 0.9, spring + 0.01, 0.0, 1.0, c=0.3, bottom=1.0))
        cy = h + casing + 1.0
        ov = poly([(1.0 * math.cos(a), cy + 1.4 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 32, endpoint=False)])
        parts.append(ext(ov, 0.0, 1.0))
        parts.append(ext(ov - ov.offset(-0.5), 0.99, 1.2))
        for sg in (-1, 1):
            parts.append(ext(circle((sg * 1.35, cy - 0.5), 0.5, 16), 0.0, 0.8))
        top = cy + 1.4
    elif head == "lintel":
        lw = w / 2 + casing + 1.0
        parts.append(chamfer_box(-lw, h, lw, h + 2.4, 0.0, 0.8, c=0.2))
        parts.append(chamfer_box(-0.8, h - 0.4, 0.8, h + 2.8, 0.0, 1.2, c=0.3))
        top = h + 2.8
    bottom = 0.0
    if sill:
        sw = w / 2 + casing + 1.0
        parts.append(chamfer_box(-sw, -1.4, sw, 0.2, 0.0, sill, c=0.3))
        bottom = -1.4
    return _one_piece([sash], parts, op, plug_cs, PLUG, top, bottom)


def _crested(dw, v0):
    """A crested head from v0 up, 2 dw wide: a frieze board, a flat cap and a cresting of
    little arches standing on it. Returns (parts, top)."""
    parts = [box([-dw + 0.4, v0 - 0.01, 0.0], [dw - 0.4, v0 + 1.6, 0.6]),
             chamfer_box(-dw, v0 + 1.2, dw, v0 + 2.0, 0.0, 1.0, c=0.3, bottom=0.6)]
    v1 = v0 + 2.0
    n = max(3, int(round(2 * dw / 1.4)))
    r = dw / n - 0.1
    arcs = [circle((-dw + 2 * dw * (k + 0.5) / n, v1 - 0.01), r, 16) -
            circle((-dw + 2 * dw * (k + 0.5) / n, v1 - 0.01), max(0.2, r - 0.5), 12) for k in range(n)]
    parts.append(ext(cs_union(arcs) ^ rect(-dw, v1 - 0.01, dw, v1 + 3), 0.0, 0.6))
    return parts, v1 + dw / n


def door_commercial(w, h, transom=4.0, leaf="four_panel", tstyle="number:12", casing=0.8, head="cornice", leaves=1,
                    text=None):
    """A commercial street door (the upstairs entrance beside a storefront): leaves and a
    transom (see openings._ornate_door_sash), a flat casing with corner blocks and a head:
    "cornice" (a moulded cap on two small consoles), "temple" (pilasters, an entablature
    lettered with ``text``, a segmental pediment), "crested" (a cap with a cresting of little
    arches), "fanhood" (a half-round fan hood with ribs and a hub) or None. Prints face-up."""
    from .openings import _ornate_door_sash, _one_piece
    op, plug_cs, sash_parts = _ornate_door_sash(w, h, leaves, transom, leaf, tstyle)
    parts = [ext(op - op.offset(-0.5, JoinType.Miter, 4.0), 0.0, 0.6)]
    parts.append(ext((op.offset(casing, JoinType.Miter, 4.0) - op) ^ rect(-w, 0.0, w, h + casing + 1), 0.0, 0.6))
    for sg in (-1, 1):                       # corner blocks at the head
        u = sg * (w / 2 + casing / 2)
        parts.append(chamfer_box(u - casing / 2 - 0.1, h - 0.1, u + casing / 2 + 0.1, h + casing + 0.1, 0.0, 1.0, c=0.25))
    top = h + casing + 0.1
    if head == "cornice":
        hw = w / 2 + casing + 0.6
        parts.append(box([-hw, top - 0.01, 0.0], [hw, top + 1.4, 0.8]))
        parts.append(chamfer_box(-hw - 0.4, top + 1.4, hw + 0.4, top + 2.2, 0.0, 1.4, c=0.3, bottom=0.8))
        for sg in (-1, 1):
            parts.append(console(1.8, 1.0, 0.8, sg * (hw - 0.4), top + 1.41, style="scroll"))
        top += 2.2
    elif head == "crested":
        hp, top = _crested(w / 2 + casing + 0.8, top)
        parts += hp
    elif head == "fanhood":
        # a half-round fan hood over the casing: a rim, radial ribs and a hub
        R = w / 2 + casing + 0.6
        v0 = top - 0.01
        half = circle((0.0, v0), R, 48) ^ rect(-R - 1, v0, R + 1, v0 + R + 1)
        parts.append(ext(half, 0.0, 0.6))
        ribs = cs_union([stroke([(0.0, v0), (R * math.cos(a), v0 + R * math.sin(a))], 0.55)
                         for a in np.linspace(math.pi / 6, 5 * math.pi / 6, 5)])
        rim = half - circle((0.0, v0), R - 0.6, 48)
        parts.append(ext((ribs ^ half) + rim + (circle((0.0, v0), 1.2, 24) ^ half), 0.59, 1.0))
        top = v0 + R
    elif head == "temple":
        # pilasters on plinths, an entablature with ``text`` in raised letters on its frieze,
        # and a segmental pediment
        pu = w / 2 + casing + 0.9
        for sg in (-1, 1):
            a, b = sorted((sg * (pu - 0.9), sg * (pu + 0.9)))
            parts.append(chamfer_box(a - 0.2, 0.0, b + 0.2, 2.4, 0.0, 1.2, c=0.3))
            parts.append(box([a, 2.39, 0.0], [b, top + 0.01, 0.8]) - box([(a + b) / 2 - 0.25, 3.4, 0.6], [(a + b) / 2 + 0.25, top - 1.6, 1.0]))
            parts.append(chamfer_box(a - 0.3, top - 1.2, b + 0.3, top, 0.0, 1.2, c=0.3))
        ew = pu + 1.2
        parts.append(box([-ew, top - 0.01, 0.0], [ew, top + 0.8, 0.8]))                        # architrave
        parts.append(box([-ew, top + 0.79, 0.0], [ew, top + 3.41, 0.6]))                       # frieze
        if text:
            cap = 1.8
            parts.append(ext(text_cs(text, cap, "serif", grow=0.08).translate((0.0, top + 0.8 + (2.6 - cap) / 2)), 0.59, 1.0))
        parts.append(chamfer_box(-ew - 0.6, top + 3.4, ew + 0.6, top + 4.4, 0.0, 1.4, c=0.3, bottom=0.8))   # cornice
        v1 = top + 4.4
        seg = arch_cs(-ew - 0.6, ew + 0.6, v1 - 0.01, v1 - 0.01, rise=2.8, seg=40)
        parts.append(ext(seg, 0.0, 0.4))
        parts.append(ext(seg - seg.offset(-0.8, JoinType.Miter, 4.0), 0.0, 1.2))
        top = v1 + 2.8
    return _one_piece(sash_parts, parts, op, plug_cs, PLUG, top, 0.0)


# ------------------------------------------------------------------ awnings, poles, boardwalks
def awning(L, depth=10.0, drop=5.0, valance=2.6, t=0.8, rail=2.0, point=2.4):
    """A shop awning ``L`` wide: a mounting rail on the wall, the canvas sloping ``depth`` out
    and ``drop`` down, and a valance cut into points along its hem (45 degree edges). Local
    frame: u 0..L along the wall, v = 0 at the rail top, w out. Prints on its side (u up), so
    stripes across it are colour bands by height: change filament every stripe (see
    ``awning_stripes``) or print it in one colour. Every layer is the same thin profile: no
    overhangs, no supports."""
    th = t / math.cos(math.atan2(drop, depth))
    sec = cs_union([rect(0.0, -rail, t, 0.0),                                             # rail on the wall
                    poly([(0.0, 0.0), (depth, -drop), (depth, -drop - th), (0.0, -th)]),      # canvas
                    rect(depth - t, -drop - valance, depth, -drop)])                           # valance
    A = np.array([[0.0, 0.0, 1.0, 0.0], [0.0, 1.0, 0.0, 0.0], [1.0, 0.0, 0.0, 0.0]])         # (w, v, u) -> (u, v, w)
    return M.extrude(sec, L).transform(A) - awning_hem(L, depth, drop, valance, t, point)


def awning_hem(L, depth, drop, valance, t=0.8, point=2.4):
    """The points cut out of an awning's valance hem (see awning): triangles pointing up
    between the points, 45 degree edges."""
    n = max(1, int(round(L / point)))
    p = L / n
    tri = cs_union([poly([(k * p, -drop - valance - 0.01), ((k + 1) * p, -drop - valance - 0.01),
                          ((k + 0.5) * p, -drop - valance + p / 2)]) for k in range(n)])
    return ext(tri, depth - t - 0.5, depth + 0.5)


def awning_stripes(L, stripe=2.4):
    """u positions where an awning's stripes change colour (the filament-change heights when
    it prints on its side)."""
    n = max(1, int(round(L / stripe)))
    return [round(L * k / n, 2) for k in range(1, n)]


def barber_pole(h=16.0, r=1.0, turns=1.5, starts=3):
    """A barber pole: a turned base, a shaft with ``starts`` helical ridges (the stripes:
    raised so they take a paint-on colour cleanly), a band and a ball top. Prints upright."""
    ridge = cs_union([circle((0.0, 0.0), r, 32)] +
                     [circle((r * math.cos(2 * math.pi * k / starts), r * math.sin(2 * math.pi * k / starts)), 0.35, 12)
                      for k in range(starts)])
    shaft_h = h - 5.4
    parts = [M.cylinder(1.0, r + 0.8, r + 0.8, 32),
             M.cylinder(0.6, r + 0.8, r + 0.3, 32).translate([0, 0, 0.99]),
             M.cylinder(0.6, r + 0.3, r + 0.3, 32).translate([0, 0, 1.58]),
             M.extrude(ridge, shaft_h, int(shaft_h / 0.2), 360.0 * turns).translate([0, 0, 2.17]),
             M.cylinder(0.8, r + 0.3, r + 0.3, 32).translate([0, 0, 2.18 + shaft_h - 0.02]),
             M.cylinder(0.4, r + 0.3, 0.6, 32).translate([0, 0, 2.18 + shaft_h + 0.77]),
             M.sphere(1.3, 32).translate([0, 0, h - 1.3])]
    return union(parts)


def boardwalk(L, depth, H, pitch=2.2, crack=0.25, t=1.2, stringers=3, fascia=1.0, nose=0.35, base=None):
    """A plank sidewalk in front of a shop: planks running from the building out to the
    street with hairline cracks between them, on stringers along the street, a fascia on the
    street edge and the ends, and a rounded nosing. Local frame: u 0..L along the street,
    v 0..depth out from the building, z up from the street, the walk's top at H. Prints
    upside down with the planks on the bed: print them in a wood colour and change filament
    once, at ``t`` (as the planked porch decks)."""
    cracks = cs_union([rect(u - crack / 2, -1.0, u + crack / 2, depth + 1.0) for u in np.arange(pitch, L - 0.5, pitch)])
    planks = slab(rect(0, 0, L, depth) - cracks, H - t, H)
    top = H - t + 0.2                                    # the frame reaches into the planks
    z0 = 0.0 if base is None else H - t - base          # ``base``: a shallow frame (a balcony deck)
    parts = [planks]
    for v in np.linspace(1.2, depth - 1.2, stringers):
        parts.append(box([0.0, v - 0.5, z0], [L, v + 0.5, top]))
    parts.append(box([0.0, depth - fascia, z0], [L, depth, top]))                     # street fascia
    for u0 in (0.0, L - fascia):
        parts.append(box([u0, 0.0, z0], [u0 + fascia, depth, top]))                   # end fascias
    parts.append(box([-0.3, depth - 0.2, H - 0.6], [L + 0.3, depth + nose, H]))      # nosing
    return union(parts)


def baluster_bottle(h, seg=24):
    """A bottle baluster: a low round belly, a long neck and a ring under the cap."""
    from .porchwork import _revolve
    t = [(0.0, 0.55), (0.1, 0.55), (0.14, 0.62), (0.34, 0.78), (0.52, 0.55), (0.72, 0.38), (0.84, 0.4),
         (0.88, 0.55), (1.0, 0.55)]
    return _revolve([(0.0, 0.0)] + [(r, f * h) for f, r in t], seg)


def balustrade(L, h=5.6, t=2.6, pitch=1.9, pedestals=(), ped_w=2.6, end=True):
    """A stone balustrade ``L`` long for the top of a parapet: a plinth rail, bottle
    balusters, a moulded top rail and solid pedestals (at the ends and at ``pedestals`` =
    u positions). Local frame: u 0..L, v up from its foot, w into the wall (0..t); prints
    upright on its foot. The top rail overhangs 0.2 mm (one layer) each side."""
    parts = [box([0.0, 0.0, 0.0], [L, 1.2, t]),
             box([-0.2, h - 1.0, -0.2], [L + 0.2, h, t + 0.2]) + box([0.0, h - 1.21, 0.0], [L, h - 0.99, t])]
    peds = sorted(set(([ped_w / 2, L - ped_w / 2] if end else []) + list(pedestals)))
    for u in peds:
        parts.append(box([u - ped_w / 2, 0.0, 0.0], [u + ped_w / 2, h - 0.99, t]))
    bh = h - 1.2 - 1.2
    free = []
    edges = [0.0] + [x for u in peds for x in (u - ped_w / 2, u + ped_w / 2)] + [L]
    for a, b in zip(edges[::2], edges[1::2]):
        n = int((b - a - 0.4) / pitch)
        if n < 1:
            continue
        off = a + (b - a - (n - 1) * pitch) / 2
        free += [off + k * pitch for k in range(n)]
    bal = baluster_bottle(bh)
    for u in free:
        parts.append(bal.translate([u, t / 2, 0.0]).transform(np.array([[1.0, 0, 0, 0], [0, 0, 1.0, 1.2], [0, 1.0, 0, 0]])))
    return union(parts)


def skylight(W, D, h=4.0, curb=1.6, bars=2.4):
    """A hipped glass skylight on a curb, for a flat roof (D >= W): glazing bars standing
    0.3 proud of the glass on its sloping faces (45 degrees at most), a ridge and a curb.
    Local frame: x 0..W, y 0..D, z up from the roof deck. Prints upright.
    Returns (solid, glass zone for renders)."""
    rise = min(W / 2, h)
    hip = M.hull_points([(x, y, curb) for x in (0.0, W) for y in (0.0, D)] +
                        [(W / 2, y, curb + rise) for y in (W / 2, D - W / 2)])
    body = box([0.0, 0.0, 0.0], [W, D, curb + 0.01]) + hip
    ribs = [box([x - 0.25, -1, curb - 0.01], [x + 0.25, D + 1, curb + h + 1]) for x in np.arange(bars, W - 0.5, bars)]
    ribs += [box([-1, y - 0.25, curb - 0.01], [W + 1, y + 0.25, curb + h + 1]) for y in np.arange(bars, D - 0.5, bars)]
    over = M.hull_points([(x, y, curb) for x in (-0.3, W + 0.3) for y in (-0.3, D + 0.3)] +
                         [(W / 2, y, curb + rise + 0.3) for y in (W / 2 - 0.3, D - W / 2 + 0.3)])
    frame = union(ribs) ^ over
    solid = body + frame
    return solid, hip - frame


def flag_sidewalk(L, depth, H, course=4.2, joint=0.5, d=0.4, seed=7):
    """A sidewalk of big flagstones: a slab ``H`` thick, u 0..L, v 0..depth, its top cut
    into courses of stones of random length with ``joint`` wide joints ``d`` deep. Prints
    flat on its bottom (the joints are open to the top)."""
    rng = np.random.default_rng(seed)
    cuts = []
    v = course
    while v < depth - 0.5:
        cuts.append(rect(-1.0, v - joint / 2, L + 1.0, v + joint / 2))
        v += course
    v = 0.0
    while v < depth - 0.5:
        u = -rng.uniform(0.0, 4.0)
        while u < L:
            u += rng.uniform(5.0, 9.0)
            if 0.8 < u < L - 0.8:
                cuts.append(rect(u - joint / 2, v, u + joint / 2, min(depth, v + course)))
        v += course
    return box([0.0, 0.0, 0.0], [L, depth, H]) - M.extrude(cs_union(cuts), d + 1.0).translate([0, 0, H - d])


def gallery_frame(xs, H, beam=1.6, post=2.0, gusset=2.4, rail=None, depth_t=2.0):
    """One level of a two-storey gallery, in the plane of its posts: square posts at ``xs``
    (u positions) from v = 0 to H, a beam along their tops, pierced 45 degree gussets at
    every post head, and optionally a railing (``rail`` = dict(h=, pitch=, picket=)): a sill
    on the floor, square pickets and a hand rail. Local frame: u along, v up, w across (the
    posts' depth, centred). Prints upright; the beam and hand rail bridge post to post."""
    x0, x1 = min(xs) - post / 2, max(xs) + post / 2
    hw = depth_t / 2
    parts = [box([x0, H - beam, -hw], [x1, H, hw])]
    for x in xs:
        parts.append(box([x - post / 2, 0.0, -post / 2], [x + post / 2, H - beam + 0.01, post / 2]))
        for sg in (-1, 1):
            a = x + sg * post / 2
            tri = poly([(a, H - beam + 0.01), (a + sg * gusset, H - beam + 0.01), (a, H - beam - gusset)])
            hole = circle((a + sg * gusset * 0.3, H - beam - gusset * 0.3), 0.35, 12)
            if (x0 <= a + sg * gusset <= x1):
                parts.append(ext(tri - hole, -0.4, 0.4).transform(np.array([[1.0, 0, 0, 0], [0, 1.0, 0, 0], [0, 0, 1.0, 0]])))
    if rail:
        rh, pitch, pk = rail.get("h", 8.0), rail.get("pitch", 1.8), rail.get("picket", 0.8)
        parts.append(box([x0, 0.0, -hw * 0.6], [x1, 0.8, hw * 0.6]))                  # sill
        parts.append(box([x0, rh - 1.0, -hw * 0.7], [x1, rh, hw * 0.7]))              # hand rail
        for a, b in zip(sorted(xs)[:-1], sorted(xs)[1:]):
            a, b = a + post / 2, b - post / 2
            n = max(1, int(round((b - a) / pitch)) - 1)
            for k in range(1, n + 1):
                u = a + (b - a) * k / (n + 1)
                parts.append(box([u - pk / 2, 0.79, -pk / 2], [u + pk / 2, rh - 0.99, pk / 2]))
    return union(parts)


def corrugated_panel(L, W, t=1.0, pitch=1.6, h=0.4, chord=1.3):
    """A roof panel of corrugated iron, ``L`` along the eave by ``W`` up the slope: a sheet
    ``t`` thick with low round ribs (``h`` high, ``chord`` wide at the foot, so even their top
    layer is wider than the nozzle) running up the slope every ``pitch``. Own frame (u along
    the eave, v up the slope, w out); prints flat on its back."""
    r = (chord * chord / 4 + h * h) / (2 * h)
    ribs = [M.cylinder(W, r, r, 48).rotate([-90, 0, 0]).translate([u, 0.0, t + h - r])
            for u in np.arange(pitch / 2, L, pitch)]
    return box([0, 0, 0], [L, W, t]) + (union(ribs) ^ box([0, 0, t - 0.01], [L, W, t + h]))


def blade_sign(shape_cs, text=None, cap=1.8, t=1.2, arm=9.0, drop=2.4, relief=0.4, font="serif", hang=None,
               face=None):
    """A hanging blade sign standing out from a wall: a flat board of outline ``shape_cs``
    (in its own (x, y) plane, top at y = 0, hanging below) with raised ``text`` on its face,
    hung from a scrolled iron arm ``arm`` long with a wall plate. Local frame: x out from the
    wall (0 at the wall), y up, z across. Prints lying on its back (z = 0 on the bed): board,
    arm and plate all start on the bed; the letters stand on the board. ``hang``: the two
    hangers' x offsets from the board's centre (default 1 mm in from its ends); each reaches
    down to the outline below it. ``face``: a CrossSection in the outline's own coordinates
    raised ``relief`` on the board (a watch's bezel and hands, say)."""
    b = shape_cs.bounds()
    parts = [ext(shape_cs.translate((arm / 2 - (b[0] + b[2]) / 2, -drop)), 0.0, t)]
    if face is not None:
        parts.append(ext((face ^ shape_cs).translate((arm / 2 - (b[0] + b[2]) / 2, -drop)), t - 0.01, t + relief))
    if text:
        tc = text_cs(text, cap, font, grow=0.08)
        cy = -drop + (b[1] + b[3]) / 2 - cap / 2
        parts.append(ext(tc.translate((arm / 2, cy)), t - 0.01, t + relief))
    # arm: a bar along the top with a scroll under it, a wall plate, and two hangers
    parts.append(box([0.0, -0.5, 0.0], [arm, 0.5, 0.8]))
    parts.append(ext(circle((2.4, -1.8), 1.3, 24) - circle((2.4, -1.8), 0.7, 20) + rect(0.0, -1.8, 2.4, -0.4) -
                     rect(0.5, -3.2, 2.4, -1.8), 0.0, 0.8))
    parts.append(box([0.0, -3.0, 0.0], [0.8, 1.0, 1.6]))                                  # wall plate
    board = shape_cs.translate((arm / 2 - (b[0] + b[2]) / 2, -drop))
    xs = (arm / 2 + (b[0] - (b[0] + b[2]) / 2) + 1.0, arm / 2 + (b[2] - (b[0] + b[2]) / 2) - 1.0) if hang is None \
        else tuple(arm / 2 + dx for dx in hang)
    for x in xs:
        y = -drop + b[3] - 0.2
        col = board ^ rect(x - 0.3, -1e3, x + 0.3, 1e3)
        if not col.is_empty() and col.bounds()[3] < -drop + b[3] - 0.05:     # the outline is lower here
            y = col.bounds()[3] - 0.3
        parts.append(box([x - 0.3, y, 0.0], [x + 0.3, 0.0, 0.6]))
    return union(parts)


def mortar_pestle_cs(w=7.0, h=6.0):
    """Outline of a mortar and pestle (a bowl on a foot with a pestle leaning out of it),
    top of the pestle at y = 0."""
    bowl = poly([(-w / 2, -h * 0.45), (w / 2, -h * 0.45), (w * 0.38, -h * 0.8), (w * 0.2, -h * 0.92),
                 (-w * 0.2, -h * 0.92), (-w * 0.38, -h * 0.8)])
    foot = rect(-w * 0.28, -h, w * 0.28, -h * 0.9)
    lip = rect(-w / 2 - 0.3, -h * 0.47, w / 2 + 0.3, -h * 0.38)
    pestle = stroke([(w * 0.05, -h * 0.5), (w * 0.34, -0.5)], 0.9) + circle((w * 0.34, -0.6), 0.75, 16)
    return cs_union([bowl, foot, lip, pestle])


def gravel_deck(cs, z0, t=1.2, stone=0.5, pitch=0.9, seed=11):
    """A flat roof deck of tar and gravel: a slab of outline ``cs`` from z0, its top
    scattered with little stones (square pyramids, so every one prints). Prints flat."""
    rng = np.random.default_rng(seed)
    deck = M.extrude(cs, t).translate([0, 0, z0])
    b = cs.bounds()
    inner = cs.offset(-0.6, JoinType.Miter, 4.0)
    stones = []
    for x in np.arange(b[0] + 0.6, b[2] - 0.6, pitch):
        for y in np.arange(b[1] + 0.6, b[3] - 0.6, pitch):
            px, py = x + rng.uniform(-0.25, 0.25), y + rng.uniform(-0.25, 0.25)
            if rng.random() < 0.55:
                continue
            s = stone * rng.uniform(0.8, 1.2)
            stones.append(M.hull_points([(px - s / 2, py - s / 2, 0), (px + s / 2, py - s / 2, 0), (px - s / 2, py + s / 2, 0),
                                         (px + s / 2, py + s / 2, 0), (px, py, 0.3)]).translate([0, 0, z0 + t - 0.01]))
    return deck + (union(stones) ^ M.extrude(inner, t + 2).translate([0, 0, z0]))


def door_batwing(w, h, casing=0.8, bw=None, text=None):
    """A saloon doorway: an open doorway (a dark panel at the back of the plug for the room
    beyond) with a pair of louvered batwing doors across its middle, a casing and a lettered
    head board. Local frame as the windows; prints face-up."""
    from .openings import CLR, _one_piece
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-CLR, JoinType.Miter, 4.0)
    sash = [ext(plug_cs, -PLUG, -PLUG + GLASS), ext(plug_cs - plug_cs.offset(-0.5, JoinType.Miter, 4.0), -PLUG, 0.0)]
    v0, v1 = zq(h * 0.22), zq(h * 0.62)
    lw = (w - 2 * CLR - 1.2) / 2
    for sg in (-1, 1):
        a0, a1 = sorted((sg * 0.2, sg * (0.2 + lw)))
        # the leaf: stiles and rails with louvers between, its top scalloped down to the middle
        leaf = rect(a0, v0, a1, v1 - 1.0) + poly([(a0, v1 - 1.01), (a1, v1 - 1.01), (a1, v1 if sg < 0 else v1 - 1.0),
                                                     (a0, v1 - 1.0 if sg < 0 else v1)])
        louv = cs_union([rect(a0 + 0.5, vv, a1 - 0.5, vv + 0.5) for vv in np.arange(v0 + 1.0, v1 - 2.0, 1.1)])
        frame_ = leaf - rect(a0 + 0.5, v0 + 0.6, a1 - 0.5, v1 - 1.6)
        sash.append(ext(frame_, -PLUG + GLASS - 0.01, -0.6))
        sash.append(ext(louv, -PLUG + GLASS - 0.01, -0.8))
        hx = a1 if sg < 0 else a0
        sash.append(ext(rect(min(hx, sg * (w / 2 - CLR)) - 0.01, v0 + 1.0, max(hx, sg * (w / 2 - CLR)) + 0.01, v0 + 2.0) ^ plug_cs,
                        -PLUG + GLASS - 0.01, -0.8))               # hinge strap to the jamb
        sash.append(ext(rect(min(hx, sg * (w / 2 - CLR)) - 0.01, v1 - 3.0, max(hx, sg * (w / 2 - CLR)) + 0.01, v1 - 2.0) ^ plug_cs,
                        -PLUG + GLASS - 0.01, -0.8))
    parts = [ext(op - op.offset(-0.5, JoinType.Miter, 4.0), 0.0, 0.6)]
    parts.append(ext((op.offset(casing, JoinType.Miter, 4.0) - op) ^ rect(-w, 0.0, w, h + casing + 1), 0.0, 0.6))
    top = h + casing
    hb = w / 2 + casing + 0.8
    parts.append(box([-hb, top - 0.01, 0.0], [hb, top + 3.2, 0.8]))
    if text:
        parts.append(ext(text_cs(text, 2.0, "roman", grow=0.08).translate((0.0, top + 0.6)), 0.79, 1.2))
    parts.append(chamfer_box(-hb - 0.3, top + 3.2, hb + 0.3, top + 4.0, 0.0, 1.2, c=0.4, bottom=0.8))
    return _one_piece(sash, parts, op, plug_cs, PLUG, top + 4.0, 0.0)


def iron_railing(L, h=7.6, t=0.8, rail=0.8, pitch=2.6):
    """A flat wrought-iron balcony railing ``L`` long: a bottom and a top rail, upright bars,
    and a ring between each pair of bars. Local (u along, v up, w its thickness 0..t); prints
    flat on its back and stands on the balcony edge."""
    parts = [box([0, 0, 0], [L, rail, t]), box([0, h - rail, 0], [L, h, t])]
    n = max(2, int(round(L / pitch)))
    us = [L * k / n for k in range(n + 1)]
    for u in us:
        a, b = max(0.0, u - 0.3), min(L, u + 0.3)
        parts.append(box([a, rail - 0.01, 0], [b, h - rail + 0.01, t]))
    r = min((L / n) / 2 - 0.5, (h - 2 * rail) / 2 - 0.3)
    for a, b in zip(us[:-1], us[1:]):
        c = ((a + b) / 2, h / 2)
        ring = circle(c, r, 24) - circle(c, r - 0.5, 20)
        parts.append(ext(ring + rect(c[0] - 0.25, rail - 0.01, c[0] + 0.25, c[1] - r + 0.2) +
                         rect(c[0] - 0.25, c[1] + r - 0.2, c[0] + 0.25, h - rail + 0.01), 0.0, t))
    return union(parts)


def vertical_sign(text, cap=3.0, board=1.0, margin=1.0, relief=0.4, font="roman", arm=2.4):
    """A tall projecting sign with its letters stacked one above the other (H O T E L), with
    two iron arms to the wall. Local: x out from the wall (the arms from x = 0), y up (the
    sign's foot at y = 0), z its thickness; prints flat on its back."""
    letters = [c for c in text if c != " "]
    gap = cap * 0.45
    H = len(letters) * cap + (len(letters) - 1) * gap + 2 * margin + 1.0
    Wd = cap * 1.1 + 2 * margin
    x0 = arm
    parts = [box([x0, 0, 0], [x0 + Wd, H, board])]
    ring = rect(x0, 0, x0 + Wd, H) - rect(x0 + 0.7, 0.7, x0 + Wd - 0.7, H - 0.7)
    parts.append(ext(ring, board - 0.01, board + relief))
    for k, ch in enumerate(letters):
        y = H - margin - 0.5 - (k + 1) * cap - k * gap
        parts.append(ext(text_cs(ch, cap, font, grow=0.1).translate((x0 + Wd / 2, y)), board - 0.01, board + relief))
    for y in (H * 0.15, H * 0.85):
        parts.append(box([0.0, y - 0.4, 0.0], [x0 + 0.01, y + 0.4, 0.8]))
        parts.append(box([0.0, y - 1.4, 0.0], [0.8, y + 1.4, 1.6]))                       # wall plates
    return union(parts), H


def batten_panel(L, W, t=1.2, pitch=3.0, bw=0.8, bh=0.4):
    """A board-and-batten roof panel, ``L`` along the eave by ``W`` up the slope: a sheet
    ``t`` thick with battens ``bw`` wide running up the slope every ``pitch``. Own frame (u
    along the eave, v up the slope, w out); prints flat on its back."""
    parts = [box([0, 0, 0], [L, W, t])]
    for u in np.arange(pitch / 2, L - 0.3, pitch):
        parts.append(chamfer_box(u - bw / 2, 0.0, u + bw / 2, W, t - 0.01, bh, c=0.15))
    return union(parts)


def pretzel_cs(w=7.0, h=6.0, bar=1.0):
    """Outline of a baker's pretzel, top at y = 0: a loop of dough crossed in the middle."""
    pts = []
    for t in np.linspace(0, 2 * math.pi, 90):
        x = math.sin(t) * (1 + 0.35 * math.cos(t))
        y = math.cos(t) * math.sin(t) * 1.1 - 0.3 * math.cos(t)
        pts.append((x * w / 2.7, y * h / 1.6 - h * 0.55))
    body = stroke(pts, bar, caps=True)
    return body + stroke([(0.0, -0.2), (0.0, -h * 0.25)], bar * 0.8)


def pantile_panel(L, W, t=1.2, pitch=2.4, course=4.0, h=0.5):
    """A roof panel of pantiles, ``L`` along the eave by ``W`` up the slope: S-waved tiles in
    rows running up the slope every ``pitch``, laid in courses ``course`` long, each course's
    butt standing proud of the one above. Own frame (u along the eave, v up, w out); prints
    flat on its back."""
    parts = [box([0, 0, 0], [L, W, t])]
    prof = []
    for x in np.linspace(0, pitch, 13):
        s = x / pitch
        z = h * (0.5 + 0.5 * math.sin(2 * math.pi * s - math.pi / 2)) * (1.0 if s < 0.6 else 0.9)
        prof.append((x, z))
    v = 0.0
    while v < W - 0.01:
        v1 = min(W, v + course)
        for u in np.arange(0.0, L, pitch):
            pts = [(u + x, t - 0.01 + z) for x, z in prof]
            sec = poly([(u, t - 0.01)] + pts + [(u + pitch, t - 0.01)])
            m = M.extrude(sec, v1 - v)                                   # along +z = up the slope
            m = m.transform(np.array([[1.0, 0, 0, 0], [0, 0, 1.0, v], [0, 1.0, 0, 0]]))
            # a butt: each course thickest at its lower end
            parts.append(m.warp_batch(lambda P, v0=v, v1=v1: _taper(P, v0, v1, t)))
        v = v1
    return union(parts) ^ box([0, 0, 0], [L, W, t + h + 0.4])


def _taper(P, v0, v1, t):
    """Thin each pantile course toward its upper end and thicken its butt; the tiles' feet
    stay on the sheet (only points above it move)."""
    P = np.array(P)
    s = np.clip((P[:, 1] - v0) / max(v1 - v0, 1e-6), 0, 1)
    base = t - 0.01
    up = (P[:, 2] - base) > 0.005
    P[:, 2] = np.where(up, base + (P[:, 2] - base) * (1.0 - 0.45 * s) + 0.25 * (1 - s), P[:, 2])
    return P


def iron_shutter(w, h, t=0.8, straps=2):
    """One leaf of an iron fire shutter, hooked open beside a window: a plate with a raised
    rim, ``straps`` horizontal straps with rivet heads, and a hinge pin. Local (u 0..w, v
    0..h, w 0..t+); prints flat on its back."""
    parts = [box([0, 0, 0], [w, h, t])]
    parts.append(ext(rect(0, 0, w, h) - rect(0.5, 0.5, w - 0.5, h - 0.5), t - 0.01, t + 0.4))
    for k in range(straps):
        v = h * (k + 1) / (straps + 1)
        parts.append(box([0.0, v - 0.4, t - 0.01], [w, v + 0.4, t + 0.4]))
        parts.append(ext(cs_union([circle((x, v), 0.25, 10) for x in (0.8, w / 2, w - 0.8)]), t + 0.39, t + 0.6))
    return union(parts)


def hoist_cs(beam=8.0, drop=7.0):
    """Side view of a hoist over a loading door, for a flat part standing out from the wall:
    a beam (x out from the wall, y up from the beam's foot), a pulley wheel at its end, the
    rope down to a block and a hook, and a wall plate. Top of the beam at y = 1.6."""
    beam_cs = rect(0.0, 0.0, beam, 1.6) + rect(0.0, -0.8, 0.9, 2.4)
    wheel = circle((beam - 1.4, -0.8), 1.3, 28) - circle((beam - 1.4, -0.8), 0.45, 12)
    hanger = rect(beam - 1.7, -0.9, beam - 1.1, 0.01)
    rope = rect(beam - 2.95, -drop, beam - 2.45, -0.8) + rect(beam - 0.35, -drop + 1.2, beam + 0.15, -0.8)
    block = rect(beam - 3.3, -drop - 1.6, beam + 0.5, -drop + 1.2)
    hook = stroke([(beam - 1.4, -drop - 1.6), (beam - 1.4, -drop - 2.6), (beam - 0.8, -drop - 3.2), (beam - 0.2, -drop - 2.8)],
                  0.6, caps=True)
    return cs_union([beam_cs, wheel, hanger, rope, block, hook])


def shingle_panel(L, W, t=1.2, pitch=1.8, width=2.0):
    """A roof panel of wood shingles in straight courses, ``L`` along the eave by ``W`` up the
    slope. Own frame (u along the eave, v up the slope, w out); prints flat on its back."""
    from .skins import coursed_shingles
    return box([0, 0, 0], [L, W, t]) + coursed_shingles(rect(0, 0, L, W), pitch=pitch, width=width, d=0.45,
                                                           datum=0.0).translate([0, 0, t - 0.02])


def display_bay(w, proj, bulk=6.0, glass_h=18.0, head=2.0, t=0.6, post=0.8, transom=None):
    """A canted display bay for a shop front, standing out ``proj`` from the wall: a solid
    bulkhead, three thin glass walls (``t`` thick) with posts at the corners and an optional
    transom bar, a head slab, and a hipped roof falling back to the wall at 45 degrees. The
    part also fills the wall opening behind it to PLUG deep (the opening is ``w`` wide and
    ``bulk + glass_h + head`` tall); the roof's back is on the wall face. Local frame as the
    storefront (u centred, v up, w out); prints upright on its floor. Returns (solid, glass zone)."""
    hw = w / 2
    plan = poly([(-hw, -PLUG), (hw, -PLUG), (hw, 0.0), (hw - proj, proj), (-hw + proj, proj), (-hw, 0.0)])
    A = np.array([[1.0, 0, 0, 0], [0, 0, 1.0, 0], [0, 1.0, 0, 0]])        # (u, w, v) -> (u, v, w)

    def prism(cs, v0, v1):
        return M.extrude(cs, v1 - v0).translate([0, 0, v0]).transform(A)
    v_g1 = bulk + glass_h
    parts = [prism(plan, 0.0, bulk)]
    shell = plan - plan.offset(-t, JoinType.Miter, 4.0) - rect(-hw - 1, -PLUG - 1, hw + 1, -0.5)
    glass = prism(shell, bulk - 0.01, v_g1 + 0.01)
    corners = cs_union([rect(x - post / 2, y - post / 2, x + post / 2, y + post / 2)
                        for x, y in ((hw - proj, proj - post / 2), (-hw + proj, proj - post / 2))]) + \
        rect(-hw, -PLUG, -hw + post, 0.0) + rect(hw - post, -PLUG, hw, 0.0)
    parts.append(prism(corners ^ plan, bulk - 0.01, v_g1 + 0.01))
    if transom:
        parts.append(prism(shell.offset(0.1, JoinType.Miter, 4.0) ^ plan, transom - 0.4, transom + 0.4))
    parts.append(prism(plan, v_g1, v_g1 + head))
    parts.append(prism(plan.offset(0.4, JoinType.Miter, 4.0) ^ rect(-hw - 1, 0.0, hw + 1, proj + 1),
                       v_g1 + head - 0.6, v_g1 + head))
    top = v_g1 + head
    # the roof falls back to the wall face at 45 degrees (its back on the wall plane)
    roof = M.hull_points([(x, top - 0.01, z) for x, z in ((-hw - 0.4, 0.0), (hw + 0.4, 0.0),
                                                         (hw - proj + 0.2, proj + 0.4), (-hw + proj - 0.2, proj + 0.4))] +
                         [(x, top + proj + 0.4, 0.0) for x in (-hw + proj, hw - proj)])
    parts.append(roof.transform(np.array([[1.0, 0, 0, 0], [0, 1.0, 0, 0], [0, 0, 1.0, 0]])))
    solid = union(parts) + glass
    return solid, glass


def hat_cs(w=7.0, h=5.0):
    """Outline of a lady's hat for a milliner's sign: a brim curling up at its tips, a crown
    with a rounded top, a band standing proud of the crown's foot, and an ostrich plume
    arching over the crown from the band; top of the plume at y = 0."""
    brim = poly([(-w / 2, -h + 0.9), (-w / 2 + 0.6, -h + 0.3), (-w / 4, -h), (w / 4, -h), (w / 2 - 0.6, -h + 0.3),
                 (w / 2, -h + 0.9), (w / 4, -h + 0.6), (-w / 4, -h + 0.6)])
    cw = w * 0.24
    crown = rect(-cw + 0.8, -h + 0.5, cw - 0.8, -h + 2.4).offset(0.8, JoinType.Round) ^ rect(-w, -h + 0.5, w, 0.0)
    band = rect(-cw - 0.25, -h + 0.6, cw + 0.25, -h + 1.3)
    s = h / 5.0
    plume = stroke([(cw - 0.1, -h + 1.3), (cw + 0.8, -h + 2.6 * s), (cw + 0.2, -h + 3.7 * s), (0.4, -h + 4.3 * s),
                    (-1.0, -h + 4.0 * s)], 0.8, caps=True)
    return cs_union([brim, crown, band, plume])


def watch_cs(d=6.0):
    """Outline of a pocket watch for a jeweller's sign: the round case, the winding crown and
    the bow (a ring) above it; top of the bow at y = 0. Returns (outline, face) where face is
    the raised bezel ring, hour marks and hands (at ten past ten) for ``blade_sign(face=)``."""
    r = d / 2
    cy = -2.2 - r
    case = circle((0.0, cy), r, 40)
    crown = rect(-0.6, cy + r - 0.2, 0.6, -1.5)
    bow = circle((0.0, -0.9), 0.9, 20) - circle((0.0, -0.9), 0.4, 16)
    face = (circle((0.0, cy), r, 40) - circle((0.0, cy), r - 0.6, 40))
    for k in range(0, 12, 3):
        a = math.pi / 2 - k * math.pi / 6
        face = face + circle((0.0 + (r - 1.1) * math.cos(a), cy + (r - 1.1) * math.sin(a)), 0.3, 10)
    for a, L, wd in ((math.radians(150), r * 0.45, 0.6), (math.radians(30), r * 0.7, 0.5)):
        face = face + stroke([(0.0, cy), (L * math.cos(a), cy + L * math.sin(a))], wd)
    face = face + circle((0.0, cy), 0.45, 12)
    return cs_union([case, crown, bow]), face


def egg_dart(L, h=2.2, pitch=2.8):
    """An egg-and-dart moulding along u 0..L, v 0..h, as two relief levels (darts, eggs): a
    row of raised ovals with a slim dart pointing down between each pair (a shell round each
    egg would be finer than the nozzle at HO scale)."""
    n = max(1, int(L / pitch))
    off = (L - n * pitch) / 2 + pitch / 2
    from .ornament import oval
    darts, eggs = [], []
    cy = h / 2
    for k in range(n):
        x = off + k * pitch
        eggs.append(oval((x, cy), 0.6, min(0.85, h * 0.4), 20))
        if k:
            xd = x - pitch / 2
            darts.append(poly([(xd - 0.25, h - 0.15), (xd + 0.25, h - 0.15), (xd + 0.25, h - 0.6), (xd, 0.25),
                               (xd - 0.25, h - 0.6)]))
    band = rect(0, 0, L, h)
    return cs_union(darts) ^ band, cs_union(eggs) ^ band


def arched_shopfront(w, spring, door_w=6.4, leaf="twin_arch", bulk=5.0, text=None, cap=1.6, fan=7, font="roman",
                     casing=0.6):
    """A shop front filling a round-arched opening ``w`` wide (a semicircular head springing at
    ``spring``): a display window on the left over a panelled bulkhead, with ``text`` in raised
    gilt letters on the glass, a door on the right (``leaf``, see openings._leaf) up to a
    transom bar at the springing, and a fanlight of ``fan`` radial bars round a half hub in
    the arch. One piece with a slim casing round the opening (the wall's arch band belongs to
    its skin, see skins.moulded_arch); prints face-up. Local frame: u centred, v from 0, w out."""
    from .openings import CLR, GLASS as G, _glass_bars, _leaf, _one_piece
    r = w / 2
    op = arch_cs(-r, r, 0.0, spring, seg=48)
    plug_cs = arch_cs(-r + CLR, r - CLR, 0.0, spring, seg=48)
    pl = PLUG
    du1 = r - CLR - 0.5
    du0 = du1 - door_w
    dh = spring - 0.4
    parts = [ext(plug_cs, -pl, -1.0)]
    lp, dlight = _leaf(leaf, du0, door_w, dh, hinge_left=False)
    parts += lp
    wu0, wu1 = -r + CLR + 0.5, du0 - 1.2
    dg = rect(wu0, bulk + 0.6, wu1, dh - 0.5)
    parts.append(ext(rect(wu0, 0.5, wu1, bulk), -1.0, -0.8))                           # bulkhead
    parts.append(ext(rect(wu0, 0.5, wu1, bulk).offset(-0.8, JoinType.Miter, 4.0), -0.81, -0.4))
    parts.append(ext(dg.offset(0.5, JoinType.Miter, 4.0) - dg, -1.0, -0.6))            # display frame
    fcs = arch_cs(-r + CLR + 0.5, r - CLR - 0.5, spring + 0.4, spring + 0.4, seg=48)
    fcs = fcs ^ rect(-r, spring + 0.4, r, spring + r + 1)
    lights = [g for g in (dlight, dg, fcs) if g is not None]
    glass = cs_union(lights)
    cut = ext(glass, -pl - 1, 0.0)
    parts = [p - cut for p in parts] + _glass_bars()
    parts.append(ext(glass, -pl, -pl + G))
    parts.append(ext(plug_cs - plug_cs.offset(-0.5, JoinType.Miter, 4.0), -pl, 0.0))
    parts.append(ext(rect(du0 - 1.2, 0.0, du0, spring) ^ plug_cs, -pl, -0.4))             # mullion
    parts.append(ext(rect(-r, spring - 0.4, r, spring + 0.4) ^ plug_cs, -pl, -0.4))       # transom bar
    spokes = [stroke([(0.0, spring), (r * 1.2 * math.cos(math.pi * k / (fan + 1)), spring + r * 1.2 * math.sin(math.pi * k / (fan + 1)))],
                     0.5, caps=False) for k in range(1, fan + 1)]
    hub = circle((0.0, spring), 1.9, 32) - circle((0.0, spring), 1.3, 32)
    parts.append(ext((cs_union(spokes) - circle((0.0, spring), 1.4, 24) + hub) ^ fcs.offset(0.1), -pl + G - 0.01, -0.6))
    if text:
        t = text_cs(text, cap, font, grow=0.1)
        tb = t.bounds()
        room = wu1 - wu0 - 1.0
        if tb[2] - tb[0] > room:
            print(f"  WARNING: glass text {text!r} is {tb[2] - tb[0]:.1f} wide for {room:.1f}")
        parts.append(ext(t.translate(((wu0 + wu1) / 2, bulk + 0.6 + (dh - 0.5 - bulk - 0.6) * 0.62)) ^ dg,
                         -pl + G - 0.01, -0.8))
    sur = [ext(op - op.offset(-0.5, JoinType.Miter, 4.0), 0.0, 0.6),
           ext((op.offset(casing, JoinType.Round) - op) ^ rect(-r - 5, 0.0, r + 5, spring + r + 5), 0.0, 0.4)]
    return _one_piece(parts, sur, op, plug_cs, pl, spring + r + casing, 0.0)


def oriel(w, proj, h, head=2.0, lights=(1, 2, 1), base=None):
    """A canted oriel window on a corbel for an upper storey: three faces (a front ``w`` - 2
    ``proj`` wide and two sides at 45 degrees), each with recessed sashes (``lights`` panes
    across per face) with a meeting rail, a sill course, a frieze and a cornice; below, a
    corbel narrowing at 45 degrees to the wall. Local frame: u centred, v from 0 at the
    corbel's foot, w out. A flat back plug of the whole silhouette goes PLUG deep into a cut
    of the same outline, so the part prints on its back with everything growing up from it.
    Returns dict(solid, glass, cut, landing, top, roof) - roof a separate hipped roof part
    whose back sits on the wall face above the oriel."""
    hw = w / 2
    base = proj + 1.0 if base is None else base
    A = np.array([[1.0, 0, 0, 0], [0, 0, 1.0, 0], [0, 1.0, 0, 0]])        # (u, w, v) -> (u, v, w)
    plan_pts = [(-hw, 0.0), (hw, 0.0), (hw - proj, proj), (-hw + proj, proj)]
    plan = poly(plan_pts)
    wpos = rect(-hw - 2, 0.0, hw + 2, proj + 2)

    def prism(cs, v0, v1):
        return M.extrude(cs, v1 - v0).translate([0, 0, v0]).transform(A)
    foot = hw - proj - 0.6
    corbel = M.hull_points([(u, base, ww) for u, ww in plan_pts] + [(u, 0.0, ww) for u in (-foot, foot) for ww in (0.0, 0.4)])
    parts = [corbel, prism(plan.offset(0.4, JoinType.Miter, 4.0) ^ wpos, base - 0.6, base + 0.01)]      # a bead on the corbel
    top = base + h + head
    parts.append(prism(plan, base, top))
    parts.append(prism(plan.offset(0.4, JoinType.Miter, 4.0) ^ wpos, base + 0.6, base + 1.2))           # sill course
    parts.append(prism(plan.offset(0.6, JoinType.Miter, 4.0) ^ wpos, top - 0.8, top))                    # cornice
    parts.append(prism(plan.offset(0.4, JoinType.Miter, 4.0) ^ wpos, top - 1.4, top - 0.79))
    body = union(parts)
    cuts, bars, glass = [], [], []
    v0, v1 = base + 1.6, base + h - 0.8
    vm = (v0 + v1) / 2
    faces = [((-hw, 0.0), (-hw + proj, proj)), ((-hw + proj, proj), (hw - proj, proj)), ((hw - proj, proj), (hw, 0.0))]
    for (p0, p1), nl in zip(faces, lights):
        du, dw_ = p1[0] - p0[0], p1[1] - p0[1]
        L = math.hypot(du, dw_)
        t_ = (du / L, dw_ / L)
        n_ = (-t_[1], t_[0])
        F = np.array([[t_[0], 0.0, n_[0], p0[0]], [0.0, 1.0, 0.0, 0.0], [t_[1], 0.0, n_[1], p0[1]]])
        m0, m1 = 0.7, L - 0.7
        pw = (m1 - m0 - 0.6 * (nl - 1)) / nl
        for k in range(nl):
            a = m0 + k * (pw + 0.6)
            pane = rect(a, v0, a + pw, v1)
            cuts.append(ext(pane, -0.4, 1.0).transform(F))
            glass.append(ext(pane, -0.42, -0.38).transform(F))
            bars.append(ext(rect(a, vm - 0.3, a + pw, vm + 0.3), -0.41, 0.0).transform(F))
            bars.append(ext(pane.offset(0.01) - pane.offset(-0.5, JoinType.Miter, 4.0), -0.41, -0.2).transform(F))
    outside = body - union(cuts) + union(bars)
    sil = outside.project()
    solid = outside + ext(sil, -PLUG, 0.01)
    gz = union(glass) ^ solid
    roof_pts = [(-hw - 0.6, 0.0), (hw + 0.6, 0.0), (hw - proj + 0.25, proj + 0.6), (-hw + proj - 0.25, proj + 0.6)]
    rise = proj + 0.6
    roof = M.hull_points([(u, top, ww) for u, ww in roof_pts] +
                         [(u, top + rise, 0.0) for u in (-hw + proj, hw - proj)])
    return dict(solid=solid, glass=gz, cut=sil.offset(0.15, JoinType.Miter, 4.0), landing=sil.offset(0.15, JoinType.Miter, 4.0),
                top=top, roof=roof)


def street_clock(h=40.0, head=6.0, r=1.2):
    """A four-faced sidewalk clock about ``h`` tall: a stepped plinth, a round column with a
    collar, a 45 degree skirt flaring to a square head with a round dial seat (0.4 deep, for
    a separate ``clock_dial``) inside a bezel ring on each face, a cornice, a pyramid cap and
    a ball finial. Stands on z = 0, prints upright. Returns (solid, [(centre, normal)] of the
    four dial seats)."""
    hw = head / 2
    parts = [box([-2.2, -2.2, 0.0], [2.2, 2.2, 1.2]),
             M.hull_points([(x, y, 1.19) for x in (-2.2, 2.2) for y in (-2.2, 2.2)] +
                           [(x, y, 1.8) for x in (-1.6, 1.6) for y in (-1.6, 1.6)]),
             box([-1.6, -1.6, 1.79], [1.6, 1.6, 3.6]),
             M.hull_points([(x, y, 3.59) for x in (-1.6, 1.6) for y in (-1.6, 1.6)] +
                           [(r * math.cos(a), r * math.sin(a), 4.0) for a in np.linspace(0, 2 * math.pi, 24, endpoint=False)])]
    zc = h - head - 3.0 - 4.2
    parts.append(M.cylinder(zc - 3.99, r, r, 24).translate([0, 0, 3.99]))
    zm = 3.6 + (zc - 3.6) * 0.45
    parts.append(M.cylinder(0.3, r, r + 0.3, 24).translate([0, 0, zm]) + M.cylinder(0.6, r + 0.3, r + 0.3, 24).translate([0, 0, zm + 0.29]))
    parts.append(M.hull_points([(r * math.cos(a), r * math.sin(a), zc - 0.01) for a in np.linspace(0, 2 * math.pi, 24, endpoint=False)] +
                               [(x, y, zc + 3.0) for x in (-hw, hw) for y in (-hw, hw)]))
    zh = zc + 3.0
    parts.append(box([-hw, -hw, zh - 0.01], [hw, hw, zh + head]))
    zt = zh + head
    parts.append(M.hull_points([(x, y, zt - 0.01) for x in (-hw, hw) for y in (-hw, hw)] +
                               [(x, y, z) for x in (-hw - 0.3, hw + 0.3) for y in (-hw - 0.3, hw + 0.3) for z in (zt + 0.3, zt + 0.6)]))
    parts.append(M.hull_points([(x, y, zt + 0.59) for x in (-hw - 0.3, hw + 0.3) for y in (-hw - 0.3, hw + 0.3)] +
                               [(x, y, zt + 0.6 + hw - 0.2) for x in (-0.5, 0.5) for y in (-0.5, 0.5)]))
    zf = zt + 0.6 + hw - 0.2
    parts.append(M.cylinder(0.8, 0.35, 0.35, 12).translate([0, 0, zf - 0.01]))
    parts.append(M.sphere(0.7, 16).translate([0, 0, zf + 1.2]))
    solid = union(parts)
    seats = []
    rd = hw - 0.7
    zd = zh + head / 2
    for ang in range(4):
        a = math.pi / 2 * ang
        n = np.array([math.cos(a), math.sin(a), 0.0])
        c = n * hw + np.array([0, 0, zd])
        R = np.array([[-math.sin(a), 0.0, math.cos(a)], [math.cos(a), 0.0, math.sin(a)], [0.0, 1.0, 0.0]])
        Tm = np.column_stack([R, c])                       # local (x across, y up, z out) -> world
        bez = ext(circle((0.0, 0.0), rd + 0.5, 40) - circle((0.0, 0.0), rd, 40), -0.01, 0.3).transform(Tm)
        seat = ext(circle((0.0, 0.0), rd, 40), -0.4, 0.5).transform(Tm)
        solid = solid + bez - seat
        seats.append((c - n * 0.4, n))
    return solid, seats


def clock_dial(r, t=0.6, hands=(10, 10)):
    """A clock dial for a ``street_clock`` seat: a disc ``t`` thick with raised quarter marks,
    hands at ``hands`` (hour, minute) and a centre boss 0.4 above it - print white, change to
    black at ``t``. Local: disc centred at the origin, face up."""
    parts = [M.cylinder(t, r, r, 40)]
    for k in range(4):                       # quarter marks (twelve would run together at this size)
        a = math.pi / 2 - k * math.pi / 2
        parts.append(ext(stroke([((r - 0.95) * math.cos(a), (r - 0.95) * math.sin(a)),
                                 ((r - 0.25) * math.cos(a), (r - 0.25) * math.sin(a))], 0.55, caps=False), t - 0.01, t + 0.4))
    hh, mm = hands
    for ang, L, wd in ((math.pi / 2 - (hh % 12 + mm / 60) * math.pi / 6, r * 0.5, 0.6),
                       (math.pi / 2 - mm * math.pi / 30, r * 0.78, 0.5)):
        parts.append(ext(stroke([(0.0, 0.0), (L * math.cos(ang), L * math.sin(ang))], wd), t - 0.01, t + 0.4))
    parts.append(ext(circle((0.0, 0.0), 0.45, 12), t - 0.01, t + 0.4))
    return union(parts)


def hex_paving(L, depth, t=1.2, a=1.2, curb=1.6, groove=0.5):
    """A sidewalk of hexagonal paving tiles (circumradius ``a``, joints ``groove`` wide and
    0.2 deep) with a plain stone curb ``curb`` wide along its far edge (y = depth). Local: u 0..L
    along the front, y 0..depth out from the building, top at z = t. Prints flat."""
    slab_ = M.extrude(rect(0, 0, L, depth), t - 0.2)
    tiles = []
    s3 = math.sqrt(3)
    i = -1
    while 1.5 * a * i < L + 2 * a:
        j = -1
        while s3 * a * j < depth + 2 * a:
            cx, cy = 1.5 * a * i, s3 * a * (j + 0.5 * (i % 2))
            tiles.append(poly([(cx + (a - groove / 2 / s3 * 2) * math.cos(k * math.pi / 3),
                                cy + (a - groove / 2 / s3 * 2) * math.sin(k * math.pi / 3)) for k in range(6)]))
            j += 1
        i += 1
    field = rect(0, 0, L, depth - curb - 0.25)
    top = M.extrude(cs_union(tiles) ^ field, 0.21).translate([0, 0, t - 0.21])
    kerb = M.extrude(rect(0, depth - curb, L, depth), 0.21).translate([0, 0, t - 0.21])
    return slab_ + top + kerb

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

from .core import arch_cs, box, circle, cs_union, poly, rect, union
from .ornament import chamfer_box, ext, stroke

PLUG = 1.6      # depth into the wall opening (as the windows)
GLASS = 0.4

FONTS = {"serif": "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
         "sans": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
         "condensed": "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf",
         "mono": "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"}


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
    if style == "panel":
        parts.append(ext(circle((um, (s0 + s1) / 2), 0.55, 16), 0.59, 1.0))      # a boss in the panel
    # capital: necking, a bell flaring out, the abacus
    c0 = v1 - cap_h
    parts.append(box([u0 - 0.1, c0, 0.0], [u1 + 0.1, c0 + 0.6, 1.0]))
    parts.append(chamfer_box(u0 - 0.35, c0 + 0.6, u1 + 0.35, v1, 0.0, 1.2, c=0.3, bottom=0.0))
    return union(parts)


def storefront(W, H, entry=14.0, entry_at=0.0, col=2.4, style="fluted", bulk=7.2, transom=6.4, beam=2.0,
               lite=2.4, bulk_style="panel", mullion=True):
    """Cast-iron storefront filling a W x H opening (u centred, v from 0), one part printed
    face-up (plug back on the bed, no supports): pilasters at both ends and either side of a
    recessed entry ``entry`` wide at ``entry_at``, panelled bulkheads under the display
    windows, a sill, the display glass, a transom bar and a band of prism-glass transom
    lights ``lite`` wide, and a beam under the sign band. The entry is an opening through the
    part: the vestibule (its own part) stands behind it.

    Returns the insert dict of openings.py (insert, glass / sash / frame zones, cut, landing,
    top, bottom, back) plus ``entry`` = (u centre, width, height) for the vestibule."""
    op = rect(-W / 2, 0.0, W / 2, H)
    vt = zq(H - beam - transom)                  # transom lights' bottom
    ve = vt - 0.8                                # the entry opening's top = the transom bar's bottom
    cols = [(-W / 2, -W / 2 + col), (W / 2 - col, W / 2)]
    ent = None
    if entry > 0:
        e0, e1 = entry_at - entry / 2, entry_at + entry / 2
        cols += [(e0 - col, e0), (e1, e1 + col)]
        ent = rect(e0, 0.0, e1, ve)
    cols.sort()
    plug_cs = op - ent if ent is not None else op
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
    # transom lights across the whole width (above the entry too)
    tl = rect(-W / 2 + col, vt + 0.4, W / 2 - col, H - beam - 0.4)
    glass_cs = cs_union(glass + [tl])
    sash = [ext(glass_cs, -PLUG, -PLUG + GLASS), ext(plug_cs - glass_cs, -PLUG, 0.0)]
    # prism-glass muntins in the transom band, and a centre mullion in wide display windows
    bars = [rect(x - 0.25, vt, x + 0.25, H) for x in np.arange(-W / 2 + col + lite, W / 2 - col - 0.5, lite)]
    if mullion:
        for a, b in bays:
            if b - a > 18.0:
                m_ = (a + b) / 2
                bars.append(rect(m_ - 0.35, bulk, m_ + 0.35, vt))
    sash.append(ext(cs_union(bars) ^ glass_cs, -PLUG + GLASS - 0.01, -0.4))
    parts = []
    for a, b in bays:
        # bulkhead: a raised panel (or a lozenge) on the frame
        if bulk_style == "panel":
            parts.append(chamfer_box(a + 0.8, 1.2, b - 0.8, bulk - 0.6, -0.01, 0.4, c=0.2))
        elif bulk_style == "lozenge":
            parts.append(chamfer_box(a + 0.8, 1.2, b - 0.8, bulk - 0.6, -0.01, 0.2, c=0.1))
            cu, cv = (a + b) / 2, bulk / 2 + 0.3
            hw, hh = (b - a) / 2 - 2.0, (bulk - 1.8) / 2 - 0.3
            parts.append(ext(poly([(cu - hw, cv), (cu, cv + hh), (cu + hw, cv), (cu, cv - hh)]), 0.19, 0.6))
        # the sill, and a bead round the display glass
        parts.append(box([a, bulk, 0.0], [b, bulk + 0.8, 0.6]))
        g = rect(a + 0.8, bulk + 0.8, b - 0.8, vt - 0.8 - 0.6)
        parts.append(ext(g.offset(0.5, JoinType.Miter, 4.0) - g, -0.01, 0.2))
    parts.append(box([-W / 2, vt - 0.8, 0.0], [W / 2, vt, 0.4]))              # transom bar
    parts.append(box([-W / 2, H - beam, 0.0], [W / 2, H, 0.4]))               # beam
    parts.append(box([-W / 2, H - beam, 0.0], [W / 2, H - beam + 0.6, 0.6]))  # its bed moulding
    for a, b in cols:
        parts.append(_column(style, a, b, 0.0, H - beam))
    frame = union(parts)
    sash_m = union(sash)
    ins = sash_m + frame
    n = len(ins.decompose())
    if n > 1:
        print("  WARNING: storefront falls into", n, "pieces")
    gl = sash_m ^ ext(glass_cs.offset(0.01), -PLUG - 1.0, -PLUG + GLASS)
    return dict(insert=ins, glass=gl, sash=sash_m - gl, frame=frame, surround=frame, back=0.0,
                cut=op, landing=op.offset(0.15, JoinType.Miter, 4.0), top=H, bottom=0.0,
                entry=(entry_at, entry, ve) if ent is not None else None, cols=cols)


def vestibule(entry, depth, v_top, bulk=7.2, side=0.8, door_h=None, transom=True):
    """The recessed entry behind a storefront, as its own part: a floor (a step up from the
    sidewalk), side walls whose inner faces carry a panelled base and a display-glass panel,
    a back wall with a pair of half-glazed doors (and a transom light), and a ceiling.
    Local frame as the storefront (u centred on the entry, v up, w out; it stands behind the
    storefront, w <= -PLUG). Prints upright on its floor; the ceiling bridges the entry."""
    wl = entry / 2
    wo = wl + side
    w0 = -PLUG
    wb = -(PLUG + depth)                       # the door plane
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
    for sg in (-1, 1):
        a0, a1 = sorted((sg * 0.25, sg * dw))
        adds.append(box([a0 + 0.5, 1.6, wb - 0.01], [a1 - 0.5, dh * 0.38, wb + 0.3]))
        cuts.append(box([a0 + 0.6, dh * 0.45, wb - 0.3], [a1 - 0.6, dh - 0.8, wb + 0.01]))
        kx = sg * 0.9
        adds.append(M.cylinder(0.5, 0.3, 0.3, 12).rotate([-90, 0, 0]).translate([kx, dh * 0.42, wb]))
    cuts.append(box([-0.25, 0.8, wb - 0.3], [0.25, dh, wb + 0.01]))           # the meeting stiles
    if transom and v_top - dh > 2.0:
        cuts.append(box([-dw, dh + 0.6, wb - 0.3], [dw, v_top - 0.6, wb + 0.01]))
    return (body - union(cuts)) + union(adds)


# ------------------------------------------------------------------ applied bands (face-up)
def console(h, d, t, u, v_top, style="scroll"):
    """A small end console under a sign band or cornice (face-up: back at w = 0)."""
    from .trimwork import bracket
    return bracket(style, h, d, t, u=u, v_top=v_top, w0=0.0)


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


def name_tablet(W, h, text=None, date=None, cap=2.6, font="serif", head="segment", board=1.2, relief=0.4):
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
        d = text_cs(date, cap * 0.8, font)
        parts.append(ext(d.translate((0.0, y)), board - 0.01, board + relief))
        y += cap * 0.8 + 1.0
    if text:
        t = text_cs(text, cap, font)
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
    with ears) or "lintel" (a stone lintel with a keystone). The brick arch of a brick
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

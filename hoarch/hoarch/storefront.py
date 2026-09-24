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
               lite=2.4, bulk_style="panel", mullion=True, posts=True, t=3.0):
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
    sash.append(ext(cs_union(bars) ^ glass_cs, -PLUG + GLASS - 0.01, -0.4))
    parts = []
    for a, b in bays:
        # bulkhead: a raised panel (or a lozenge) on the frame
        if bulk_style == "panel":
            parts.append(chamfer_box(a + 0.8, 1.2, b - 0.8, bulk - 0.6, -0.01, 0.4, c=0.2))
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
    if doors == "single":
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


def door_commercial(w, h, transom=4.0, leaf="four_panel", tstyle="number:12", casing=0.8, head="cornice", leaves=1):
    """A commercial street door (the upstairs entrance beside a storefront): leaves and a
    transom (see openings._ornate_door_sash), a flat casing with corner blocks, a stone step
    and a head: "cornice" (a moulded cap on two small consoles) or None. Prints face-up."""
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


def boardwalk(L, depth, H, pitch=2.2, crack=0.25, t=1.2, stringers=3, fascia=1.0, nose=0.35):
    """A plank sidewalk in front of a shop: planks running from the building out to the
    street with hairline cracks between them, on stringers along the street, a fascia on the
    street edge and the ends, and a rounded nosing. Local frame: u 0..L along the street,
    v 0..depth out from the building, z up from the street, the walk's top at H. Prints
    upside down with the planks on the bed: print them in a wood colour and change filament
    once, at ``t`` (as the planked porch decks)."""
    cracks = cs_union([rect(u - crack / 2, -1.0, u + crack / 2, depth + 1.0) for u in np.arange(pitch, L - 0.5, pitch)])
    planks = slab(rect(0, 0, L, depth) - cracks, H - t, H)
    top = H - t + 0.2                                    # the frame reaches into the planks
    parts = [planks]
    for v in np.linspace(1.2, depth - 1.2, stringers):
        parts.append(box([0.0, v - 0.5, 0.0], [L, v + 0.5, top]))
    parts.append(box([0.0, depth - fascia, 0.0], [L, depth, top]))                    # street fascia
    for u0 in (0.0, L - fascia):
        parts.append(box([u0, 0.0, 0.0], [u0 + fascia, depth, top]))                  # end fascias
    parts.append(box([-0.3, depth - 0.2, H - 0.6], [L + 0.3, depth + nose, H]))      # nosing
    return union(parts)

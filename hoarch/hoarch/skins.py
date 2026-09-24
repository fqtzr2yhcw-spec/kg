"""Wall skins: every building in the collection gets its own (see COLLECTION.md).

All in a facade's (u, v, w) frame: u along the wall, v up, w out of the wall face; relief
from w = 0 to at most ~0.6 mm, clipped to ``region`` (the siding region, windows' landings
already cut out). Walls print upright, so a skin is made of
  * horizontal features whose ledges step out no more than ~0.3 mm per layer (a lap
    siding's bottom edge, a brick's bed joint), their heights on the 0.2 mm grid, or
  * vertical or diagonal grooves and ribs at least a nozzle wide (0.5 mm).
No fish-scale ("U") shingles: those are left out of the collection on purpose.
"""
import math

import numpy as np
from manifold3d import JoinType, Manifold as M

from .core import SLOT, circle, cs_union, frame, poly, rect, union
from .ornament import stroke


# ------------------------------------------------------------------ lap sidings
def _lap(region, pitch, course, datum=0.0):
    """Horizontal siding repeated every ``pitch`` from a per-course profile ``course`` =
    [(dv, w), ...] measured from the course's bottom edge (dv from 0 to pitch)."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    k0 = math.floor((v0 - datum) / pitch) - 1
    k1 = math.ceil((v1 - datum) / pitch) + 1
    pts = [(datum + k0 * pitch, 0.0)]
    for k in range(k0, k1):
        vk = datum + k * pitch
        pts += [(vk + dv, w) for dv, w in course]
    pts.append((datum + k1 * pitch, 0.0))
    d = max(w for _, w in course)
    strip = M.extrude(poly(pts), (u1 - u0) + 2).transform(frame([u0 - 1, 0, 0], [0, 1, 0], [0, 0, 1], [1, 0, 0]))
    return strip ^ M.extrude(region, d + 0.2).translate([0, 0, -0.1])


def beaded_lap(region, datum=0.0):
    """Beaded lap siding: a bevel board whose bottom edge is a rounded bead with a small
    quirk above it (1.4 mm courses = 7 layers)."""
    return _lap(region, 1.4, [(0.0, 0.18), (0.2, 0.42), (0.4, 0.42), (0.6, 0.34), (1.4, 0.08)], datum)


def dutch_lap(region, datum=0.0):
    """Dutch lap: each 2.0 mm course is a bevel face under a deep cove, so every course
    reads as a double line (a shadow under the butt, a soft one under the cove)."""
    return _lap(region, 2.0, [(0.0, 0.46), (1.0, 0.36), (1.2, 0.30), (1.4, 0.21), (1.6, 0.14), (1.8, 0.10), (2.0, 0.08)],
                datum)


def drop_siding(region, datum=0.0):
    """Drop (novelty) siding: flat boards with a quarter-round cove cut at the top of each."""
    return _lap(region, 1.8, [(0.0, 0.40), (1.2, 0.40), (1.3, 0.30), (1.4, 0.22), (1.5, 0.17), (1.6, 0.15),
                              (1.8, 0.15)], datum)


def shiplap(region, datum=0.0):
    """Channel (shiplap) siding: flat boards with a square shadow channel under each."""
    return _lap(region, 2.2, [(0.0, 0.10), (0.6, 0.10), (0.6, 0.40), (2.2, 0.40)], datum)


def rustic_lap(region, datum=0.0):
    """Rustic (log-cabin) siding: 2.4 mm courses, each board's face rounded like a
    half-log, so every course casts a soft shadow under a round belly."""
    return _lap(region, 2.4, [(0.0, 0.12), (0.3, 0.30), (0.7, 0.42), (1.2, 0.46), (1.8, 0.40), (2.2, 0.24),
                              (2.4, 0.12)], datum)


def banded_rustication(region, course=2.4, groove=0.6, d=0.4, datum=0.0):
    """Banded rustication: smooth stone courses parted by V channels only (no upright
    joints), as on the ground floor of a bank. The channels' sides are 45 degrees."""
    g = groove / 2
    return _lap(region, course, [(0.0, d - g), (g, d), (course - g, d), (course, d - g)], datum)


def vgroove(region, datum=0.0):
    """Tongue-and-groove boards with a V joint at every course."""
    return _lap(region, 1.4, [(0.0, 0.40), (1.0, 0.40), (1.2, 0.15), (1.4, 0.40)], datum)


# ------------------------------------------------------------------ vertical and diagonal boards
def vertical_lap(region, pitch=2.0, d=0.45, d0=0.1, datum=0.0):
    """Vertical lapped boards: each board's edge laps over the next, so across the wall the
    boards make a sawtooth (a shadow line at every lap). All faces upright."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    k0 = math.floor((u0 - datum) / pitch) - 1
    k1 = math.ceil((u1 - datum) / pitch) + 1
    pts = [(datum + k0 * pitch, 0.0)]
    for k in range(k0, k1):
        uk = datum + k * pitch
        pts += [(uk, d), (uk + pitch, d0)]
    pts.append((datum + k1 * pitch, 0.0))
    H = v1 - v0 + 2.0
    strip = M.extrude(poly(pts), H).rotate([90, 0, 0]).translate([0, v1 + 1.0, 0])
    return strip ^ M.extrude(region, d + 0.2).translate([0, 0, -0.1])


def _grooved(region, grooves, d):
    if region.is_empty():
        return M()
    field = M.extrude(region, d)
    if grooves:
        g = cs_union(grooves) ^ region
        field = field - M.extrude(g, d + 0.2).translate([0, 0, 0.1])     # 0.1 left under each groove
    return field


def beadboard(region, pitch=1.6, groove=0.5, d=0.4, datum=0.0):
    """Vertical beadboard: narrow boards with a groove every ``pitch``."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    gs = []
    k = math.floor((u0 - datum) / pitch) - 1
    while datum + k * pitch < u1 + pitch:
        u = datum + k * pitch
        gs.append(rect(u - groove / 2, v0 - 1, u + groove / 2, v1 + 1))
        k += 1
    return _grooved(region, gs, d)


def diagonal_boards(region, pitch=1.8, groove=0.5, d=0.4, centre=None, angle=45.0):
    """Diagonal boarding; with ``centre`` (a u) the boards meet in a chevron pointing up
    along that line, as in a gable."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    t = math.tan(math.radians(angle))

    def fam(sign, ua, ub):
        hw = groove / 2 / math.sin(math.radians(angle))
        step = pitch / math.sin(math.radians(angle))        # horizontal spacing for a perpendicular pitch
        base = centre if centre is not None else u0
        kmax = int(((u1 - u0) + (v1 - v0) / t) / step) + 3
        out = []
        for k in range(-kmax, kmax + 1):
            c = base + k * step
            ya, yb = v0 - 1, v1 + 1
            xa, xb = c + sign * (ya - v0) / t, c + sign * (yb - v0) / t
            out.append(poly([(xa - hw, ya), (xa + hw, ya), (xb + hw, yb), (xb - hw, yb)]) ^ rect(ua, v0 - 1, ub, v1 + 1))
        return out
    if centre is None:
        gs = fam(1, u0 - 1, u1 + 1)
    else:          # boards rise toward the centre line from both sides
        gs = fam(1, u0 - 1, centre) + fam(-1, centre, u1 + 1)
        gs.append(rect(centre - groove / 2, v0 - 1, centre + groove / 2, v1 + 1))
    gs = [g for g in gs if not g.is_empty()]
    return _grooved(region, gs, d)


# ------------------------------------------------------------------ shingles (square butts, no scallops)
def pressed_metal(region, pw=5.0, ph=4.0, d=0.4, datum=0.0, uoff=0.0):
    """A pressed-metal front: a grid of raised panels (bevelled all round, so they also
    print upright) each with a round boss standing 2 d proud, between flat stiles and
    rails. Panel tops sit on the layer grid when ``datum`` and ``ph`` do."""
    if region.is_empty():
        return M()
    from .ornament import chamfer_box
    u0, v0, u1, v1 = region.bounds()
    cells, bosses = [], []
    for j in range(math.floor((v0 - datum) / ph) - 1, math.ceil((v1 - datum) / ph) + 1):
        vb = datum + j * ph
        for i in range(math.floor((u0 - uoff) / pw) - 1, math.ceil((u1 - uoff) / pw) + 1):
            ub = uoff + i * pw
            cells.append(chamfer_box(ub + 0.4, vb + 0.4, ub + pw - 0.4, vb + ph - 0.4, 0.0, d, c=0.2, bottom=d))
            bosses.append(circle((ub + pw / 2, vb + ph / 2), 0.6, 16))
    out = union(cells) + M.extrude(cs_union(bosses), 2 * d)
    return out ^ M.extrude(region, d + 1.0).translate([0, 0, -0.1])


def octagon_slates(region, pitch=1.6, width=2.0, d=0.35, clip=0.5, gap=SLOT, datum=0.0):
    """Octagon-cut slates: square slates in courses, their two bottom corners clipped, the
    joints broken by half a slate each course; each course thickens toward its butt."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    rows = []
    for k in range(math.floor((v0 - datum) / pitch) - 1, math.ceil((v1 - datum) / pitch) + 1):
        vk = datum + k * pitch
        top = vk + pitch * 2
        off = (k % 2) * width / 2
        tabs = []
        u = u0 - width - off
        while u < u1 + width:
            a, b = u + gap / 2, u + width - gap / 2
            tabs.append(poly([(a + clip, vk), (b - clip, vk), (b, vk + clip), (b, top), (a, top), (a, vk + clip)]))
            u += width
        row = cs_union(tabs) ^ region ^ rect(u0 - 1, vk, u1 + 1, top)
        if row.is_empty():
            continue

        def f(P, vb=vk, span=top - vk):
            P = np.array(P)
            tt = np.clip((P[:, 1] - vb) / span, 0, 1)
            P[:, 2] *= (1 - 0.6 * tt)
            return P
        rows.append(M.extrude(row, d).warp_batch(f))
    return union(rows)


def coursed_shingles(region, pitch=1.8, width=2.0, d=0.42, gap=SLOT, datum=0.0):
    """Square-butt shingles in regular courses: equal widths, straight butts, the joints
    broken by half a shingle each course, each course thickening toward its butt (upright
    wall). The orderly cousin of stagger_shingles."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    rows = []
    k0 = math.floor((v0 - datum) / pitch) - 1
    k1 = math.ceil((v1 - datum) / pitch) + 1
    for k in range(k0, k1):
        vk = datum + k * pitch
        top = vk + pitch * 2           # two courses: every edge that shows through a joint is on the grid
        off = (k % 2) * width / 2
        tabs = []
        u = u0 - width - off
        while u < u1 + width:
            tabs.append(rect(u + gap / 2, vk, u + width - gap / 2, top))
            u += width
        row = cs_union(tabs) ^ region ^ rect(u0 - 1, vk, u1 + 1, top)
        if row.is_empty():
            continue
        m = M.extrude(row, d)

        def f(P, vb=vk, span=top - vk):
            P = np.array(P)
            tt = np.clip((P[:, 1] - vb) / span, 0, 1)
            P[:, 2] *= (1 - 0.6 * tt)
            return P
        rows.append(m.warp_batch(f))
    return union(rows)


def stagger_shingles(region, pitch=1.6, d=0.42, gap=SLOT, datum=0.0, seed=3, drop=0.4):
    """Staggered-butt square shingles: random widths, every other one hanging ``drop``
    lower, each course thickening toward its butt (upright wall)."""
    if region.is_empty():
        return M()
    rng = np.random.default_rng(seed)
    u0, v0, u1, v1 = region.bounds()
    rows = []
    k0 = math.floor((v0 - datum) / pitch) - 1
    k1 = math.ceil((v1 - datum) / pitch) + 1
    for k in range(k0, k1):
        vk = datum + k * pitch
        top = vk + pitch * 1.5
        tabs = []
        u = u0 - rng.uniform(0.5, 2.0)
        j = 0
        while u < u1 + 1:
            wdt = rng.uniform(1.2, 2.3)
            low = drop if (j + k) % 2 else 0.0
            tabs.append(rect(u + gap / 2, vk - low, u + wdt - gap / 2, top))
            u += wdt
            j += 1
        row = cs_union(tabs) ^ region ^ rect(u0 - 1, vk - drop, u1 + 1, top)
        if row.is_empty():
            continue
        m = M.extrude(row, d)
        span = top - (vk - drop)

        def f(P, vb=vk - drop, span=span):
            P = np.array(P)
            tt = np.clip((P[:, 1] - vb) / span, 0, 1)
            P[:, 2] *= (1 - 0.6 * tt)
            return P
        rows.append(m.warp_batch(f))
    return union(rows)


# ------------------------------------------------------------------ brick bonds
def brick_bond(region, bond="flemish", bl=2.4, bh=0.8, mortar=SLOT, bed=0.2, d=0.25, datum=0.0, uoff=0.0,
               diaper=0.0, header_every=6):
    """Brick in a named bond (bricks d proud of the mortar):
    "running"  stretchers, half-bond;
    "flemish"  stretcher and header in turn along each course, headers centred on the
               stretchers of the course below;
    "english"  a course of stretchers, then a course of headers;
    "common"   (American) running bond with a course of headers every ``header_every``;
    "roman"    long, thin Roman brick (pass bl ~ 3.8, bh ~ 0.6) in running bond;
    "stack"    bricks straight above each other (panels, chimneys);
    "monk"     two stretchers and a header in turn, the pattern stepping a third each course;
    "garden"   Flemish garden wall: three stretchers and a header along each course.
    ``diaper``: in Flemish bond, headers on a diamond lattice stand this much prouder."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    hl = bl / 2
    cells, proud = [], []
    k = math.floor((v0 - datum) / bh) - 1
    while datum + k * bh < v1:
        v = datum + k * bh
        top = v + bh - bed
        if bond == "flemish":
            unit = bl + hl
            u = u0 - 2 * unit + (k % 2) * unit / 2 + uoff
            j = 0
            while u < u1 + unit:
                cells.append(rect(u + mortar / 2, v, u + bl - mortar / 2, top))
                hc = rect(u + bl + mortar / 2, v, u + unit - mortar / 2, top)
                idx = int(round((u - u0) / unit))
                if diaper and ((idx + k) % 6 in (0,) or (idx - k) % 6 in (0,)):
                    proud.append(hc)
                else:
                    cells.append(hc)
                u += unit
                j += 1
        elif bond == "english" or (bond == "common" and k % header_every == 0):
            if bond == "english" and k % 2 == 0:
                u = u0 - bl + uoff
                while u < u1 + bl:
                    cells.append(rect(u + mortar / 2, v, u + bl - mortar / 2, top))
                    u += bl
            else:
                u = u0 - bl + uoff + hl / 2
                while u < u1 + bl:
                    cells.append(rect(u + mortar / 2, v, u + hl - mortar / 2, top))
                    u += hl
        elif bond == "monk":             # two stretchers and a header in turn, stepping each course
            unit = 2 * bl + hl
            u = u0 - 2 * unit + (k % 3) * unit / 3 + uoff
            while u < u1 + unit:
                cells.append(rect(u + mortar / 2, v, u + bl - mortar / 2, top))
                cells.append(rect(u + bl + mortar / 2, v, u + 2 * bl - mortar / 2, top))
                cells.append(rect(u + 2 * bl + mortar / 2, v, u + unit - mortar / 2, top))
                u += unit
        elif bond == "garden":           # Flemish garden wall: three stretchers and a header, the
            unit = 3 * bl + hl            # header centred over the middle stretcher of the course below
            u = u0 - 2 * unit + (k % 2) * unit / 2 + uoff
            while u < u1 + unit:
                for j in range(3):
                    cells.append(rect(u + j * bl + mortar / 2, v, u + (j + 1) * bl - mortar / 2, top))
                cells.append(rect(u + 3 * bl + mortar / 2, v, u + unit - mortar / 2, top))
                u += unit
        elif bond == "stack":
            u = u0 - bl + uoff
            while u < u1 + bl:
                cells.append(rect(u + mortar / 2, v, u + bl - mortar / 2, top))
                u += bl
        else:   # running, roman, common's stretcher courses
            u = u0 - bl + (k % 2) * bl / 2 + uoff
            while u < u1 + bl:
                cells.append(rect(u + mortar / 2, v, u + bl - mortar / 2, top))
                u += bl
        k += 1
    out = M.extrude(cs_union(cells) ^ region, d)
    if proud:
        out = out + M.extrude(cs_union(proud) ^ region, d + diaper)
    return out


def banded_brick(region, every=5, bl=2.4, bh=0.8, datum=0.0, d=0.25, **kw):
    """Running-bond brick with every ``every``-th course left out: a deep horizontal channel
    at regular heights (banded brickwork, as on a commercial front)."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    k0 = math.floor((v0 - datum) / (bh * every)) - 1
    k1 = math.ceil((v1 - datum) / (bh * every)) + 1
    chan = cs_union([rect(u0 - 1, datum + k * every * bh, u1 + 1, datum + k * every * bh + bh) for k in range(k0, k1)])
    return brick_bond(region - chan, "running", bl=bl, bh=bh, d=d, datum=datum, **kw)


def soldier_band(region, v0, h=2.4, bw=0.8, mortar=SLOT, d=0.3):
    """A band of soldier bricks (standing on end) from v0 to v0 + h."""
    band = region ^ rect(-1e3, v0, 1e3, v0 + h)
    if band.is_empty():
        return M()
    b = band.bounds()
    cells = []
    u = b[0]
    while u < b[2]:
        cells.append(rect(u + mortar / 2, v0, u + bw - mortar / 2, v0 + h - 0.2))
        u += bw
    return M.extrude(cs_union(cells) ^ band, d)


# ------------------------------------------------------------------ stucco and half-timber
def scored_stucco(region, course=3.2, block=6.4, groove=0.5, d=0.3, datum=0.0):
    """Stucco scored to look like ashlar ("gravel wall"): a flat skin with horizontal joints
    every ``course`` and staggered vertical joints every ``block``."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    gs = []
    k = math.floor((v0 - datum) / course) - 1
    while datum + k * course < v1 + course:
        v = datum + k * course
        gs.append(rect(u0 - 1, v - 0.2, u1 + 1, v + 0.2))          # two layers: both edges on the grid
        u = u0 - block + (k % 2) * block / 2
        while u < u1 + block:
            gs.append(rect(u - groove / 2, v, u + groove / 2, v + course))
            u += block
        k += 1
    return _grooved(region, gs, d)


def half_timber(region, rails=(), post_pitch=4.8, tw=0.9, d=0.6, field_d=0.2, braces=True, datum=0.0):
    """Half-timbering: a plain stucco field with timbers standing proud of it: posts every
    ``post_pitch``, rails at the heights in ``rails``, and a diagonal brace in every other
    bay between the rails. Timbers stop at the region's edges (window trim included)."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    field = M.extrude(region, field_d)
    parts = []
    n = max(1, int(round((u1 - u0) / post_pitch)))
    us = [u0 + (u1 - u0) * i / n for i in range(n + 1)]
    for u in us:
        parts.append(rect(u - tw / 2, v0 - 1, u + tw / 2, v1 + 1))
    vs = sorted(set([v0 + 0.2] + list(rails) + [v1 - 0.2]))
    for v in vs:
        parts.append(rect(u0 - 1, v - tw / 2, u1 + 1, v + tw / 2))
    if braces:
        for i, (a, b) in enumerate(zip(us[:-1], us[1:])):
            if i % 2:
                continue
            for lo, hi in zip(vs[:-1], vs[1:]):
                if hi - lo < 3.0:
                    continue
                parts.append(stroke([(a + 0.3, lo + 0.3), (b - 0.3, hi - 0.3)], tw))
    t = cs_union(parts) ^ region
    t = t.offset(-0.3, JoinType.Miter, 4.0).offset(0.3, JoinType.Miter, 4.0)
    return field + M.extrude(t, d)


SKINS = {
    "beaded_lap": beaded_lap, "dutch_lap": dutch_lap, "drop_siding": drop_siding, "shiplap": shiplap,
    "vgroove": vgroove, "beadboard": beadboard, "diagonal_boards": diagonal_boards,
    "stagger_shingles": stagger_shingles, "scored_stucco": scored_stucco,
}


# ------------------------------------------------------------------ brick details for commercial fronts
def brick_arch(u, v0, w, h, rise, casing=0.6, rings=2, course=1.0, gap=0.4, joint=0.5, d=0.4, brick=1.0):
    """Rowlock arch over a segmental (or round) opening centred at u, bottom v0, w wide and
    h tall with a head of ``rise``: ``rings`` rings of bricks on edge round the casing,
    ``joint`` wide radial joints between the bricks and a ``gap`` of mortar between the rings,
    standing ``d`` proud. Facade (u, v). Returns (outline for the keep-out, relief).
    The ring edges' crowns (flat facets on a wall that prints upright) land on the 0.2 mm
    layer grid when v0 + h does: keep ``course`` and ``gap`` multiples of 0.2."""
    from .openings import _arc_band
    spring = v0 + h - rise
    thick = rings * course + (rings - 1) * gap
    band, cy, r0 = _arc_band(w, spring - v0, rise, round((casing + 0.1) / 0.2) * 0.2, thick)
    band = band.translate((u, v0))
    cy += v0
    cuts = []
    for k in range(1, rings):                          # mortar between the rings
        ri = r0 + k * course + (k - 1) * gap
        cuts.append(circle((u, cy), ri + gap, 96) - circle((u, cy), ri, 96))
    rmid = r0 + thick / 2
    n = max(3, int(round(math.pi * rmid / (brick + joint))))
    for k in range(-n, n + 1):                          # radial joints
        a = k * (brick + joint) / rmid
        ca, sa = math.sin(a), math.cos(a)
        cuts.append(stroke([(u + ca * (r0 - 0.5), cy + sa * (r0 - 0.5)), (u + ca * (r0 + thick + 0.5),
                                                                       cy + sa * (r0 + thick + 0.5))], joint))
    relief = band - cs_union(cuts) if cuts else band
    # a mortar bed under the bricks keeps the arch one body
    return band, union([M.extrude(band, d / 2), M.extrude(relief, d)])


def dentil_arch(u, v0, w, h, rise, casing=0.6, course=1.4, joint=0.5, d=0.35, brick=0.9, stone=True):
    """A single brick ring round an arched opening with every other brick standing proud
    (a dog-tooth arch), springing from stone imposts and keyed with a stone at the crown.
    Returns (outline for the keep-out, relief)."""
    from .openings import _arc_band
    spring = v0 + h - rise
    band, cy, r0 = _arc_band(w, spring - v0, rise, round((casing + 0.1) / 0.2) * 0.2, course)
    band = band.translate((u, v0))
    cy += v0
    rmid = r0 + course / 2
    n = max(3, int(round(math.pi * rmid / (brick + joint))))
    cuts, proud = [], []
    for k in range(-n, n + 1):
        a = k * (brick + joint) / rmid
        ca, sa = math.sin(a), math.cos(a)
        cuts.append(stroke([(u + ca * (r0 - 0.5), cy + sa * (r0 - 0.5)), (u + ca * (r0 + course + 0.5),
                                                                       cy + sa * (r0 + course + 0.5))], joint))
        if k % 2 == 0:
            a2 = (k + 0.5) * (brick + joint) / rmid
            proud.append(poly([(u + math.sin(a + 0.01) * r0, cy + math.cos(a + 0.01) * r0),
                               (u + math.sin(a + 0.01) * (r0 + course), cy + math.cos(a + 0.01) * (r0 + course)),
                               (u + math.sin(a2) * (r0 + course), cy + math.cos(a2) * (r0 + course)),
                               (u + math.sin(a2) * r0, cy + math.cos(a2) * r0)]))
    relief = union([M.extrude(band, d / 2), M.extrude(band - cs_union(cuts), d)])
    pr = (cs_union(proud) ^ band) - cs_union(cuts)
    if not pr.is_empty():
        relief = relief + M.extrude(pr, d + 0.3)
    out = band
    if stone:
        top = v0 + h + round((casing + 0.1) / 0.2) * 0.2
        key = poly([(u - 0.7, top - 0.2), (u + 0.7, top - 0.2), (u + 1.0, top + course + 0.4), (u - 1.0, top + course + 0.4)])
        relief = relief + M.extrude(key, d + 0.5)
        out = out + key
    return out, relief


def stone_arch(u, v0, w, h, rise, casing=0.6, ring=2.4, joint=0.5, d=0.45, block=1.8):
    """A ring of stone voussoirs round an arched opening, long and short in turn at the
    extrados, with a raised keystone. Returns (outline for the keep-out, relief)."""
    from .openings import _arc_band
    spring = v0 + h - rise
    band, cy, r0 = _arc_band(w, spring - v0, rise, round((casing + 0.1) / 0.2) * 0.2, ring)
    band = band.translate((u, v0))
    cy += v0
    rmid = r0 + ring / 2
    n = max(2, int(round(math.pi * rmid / 2 / (block + joint))))
    cuts, notch = [], []
    for k in range(-n, n + 1):
        a = (k + 0.5) * (block + joint) / rmid
        ca, sa = math.sin(a), math.cos(a)
        cuts.append(stroke([(u + ca * (r0 - 0.5), cy + sa * (r0 - 0.5)), (u + ca * (r0 + ring + 0.5),
                                                                       cy + sa * (r0 + ring + 0.5))], joint))
        if k % 2:                                 # every other voussoir stops short at the extrados
            notch.append(circle((u, cy), r0 + ring + 0.1, 64) - circle((u, cy), r0 + ring - 0.6, 64))
    stones = band - cs_union(cuts)
    relief = union([M.extrude(band, d / 2), M.extrude(stones, d)])
    top = v0 + h + round((casing + 0.1) / 0.2) * 0.2
    kt = round((top + ring + 0.3) / 0.2) * 0.2
    key = poly([(u - 0.8, top - 0.2), (u + 0.8, top - 0.2), (u + 1.1, kt), (u - 1.1, kt)])
    relief = relief + M.extrude(key, d + 0.4)
    return band + key, relief


def jack_arch(u, v_top, w, h=2.4, splay=1.2, joint=0.5, d=0.45, n=7):
    """A flat (jack) arch of splayed stone voussoirs over a square-headed opening ``w`` wide
    whose head is at ``v_top``, with a taller keystone. Returns (outline, relief)."""
    top = v_top + h
    outline = poly([(u - w / 2 - 0.2, v_top), (u + w / 2 + 0.2, v_top), (u + w / 2 + 0.2 + splay, top),
                    (u - w / 2 - 0.2 - splay, top)])
    cuts = []
    for k in range(1, n):
        s = k / n
        xb = u - w / 2 - 0.2 + (w + 0.4) * s
        xt = u - w / 2 - 0.2 - splay + (w + 0.4 + 2 * splay) * s
        cuts.append(stroke([(xb, v_top - 0.5), (xt, top + 0.5)], joint, caps=False))
    relief = union([M.extrude(outline, d / 2), M.extrude(outline - cs_union(cuts), d)])
    key = poly([(u - 0.6, v_top), (u + 0.6, v_top), (u + 0.9, top + 0.6), (u - 0.9, top + 0.6)])
    return outline + key, relief + M.extrude(key, d + 0.3)


def corbel_courses(u0, u1, v0, courses=3, bh=0.8, bed=0.2, step=0.25, d0=0.25, bl=2.4, mortar=0.5, dentils=True):
    """A corbelled brick frieze: ``courses`` courses of stretchers each stepping ``step``
    further out than the one below (45 degrees or less, so the wall still prints upright), and
    a course of dentils (every other header standing out) on top. Facade (u, v); returns
    (outline for the keep-out, relief)."""
    parts = []
    for k in range(courses):
        v = v0 + k * bh
        cells = []
        u = u0 - bl + (k % 2) * bl / 2
        while u < u1:
            cells.append(rect(max(u0, u + mortar / 2), v, min(u1, u + bl - mortar / 2), v + bh - bed))
            u += bl
        # the course's body, then its brick faces
        parts.append(M.extrude(rect(u0, v - 0.01, u1, v + bh), d0 + step * k))
        parts.append(M.extrude(cs_union(cells), d0 + step * (k + 1)))
    top = v0 + courses * bh
    dmax = d0 + step * courses
    if dentils:
        parts.append(M.extrude(rect(u0, top - 0.01, u1, top + bh), dmax - 0.1))
        cells = []
        u = u0 + 0.4
        while u + 1.1 < u1:
            cells.append(rect(u, top, u + 1.1, top + bh - bed))
            u += 2.2
        parts.append(M.extrude(cs_union(cells), dmax + 0.1))
        top += bh
    return rect(u0, v0, u1, top), union(parts)

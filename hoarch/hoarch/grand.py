"""The grand batch (houses 91 to 100): Gilded Age mansions that blend the collection's three
families: Victorian massing and ornament (towers, bays, wraparound porches, brackets), Colonial
order (porticoes, Palladian windows, fanlit entrances, symmetry) and the mansard batch's layered
roof storeys (deep eaves, add-ins, crests, cresting). They build on the mansard batch's roof
system (``hoarch.secondempire``: ``addin``, ``crest_ring``, ``cresting_strips``, ``bell_profile``,
``bell_cap``) and register their own cornice ornaments, brackets, corners, foundations and porch
parts on import; nothing in one house's section is shared with another building.
"""
import math

import numpy as np
from manifold3d import JoinType, Manifold as M

from .core import RIB, arch_cs, box, circle, cs_union, frame, poly, rect, union
from .ornament import chamfer_box, ext, keystone, oval, stroke, swag, urn_cs
from . import cornice as CO, features as FT, moulding as MD, openings as O, porchwork as PW
from . import shell as SH, trimwork as TW
from .colonial import _lens, _st
from .colonial4 import _glazed, _panel

MIT = JoinType.Miter
RND = JoinType.Round


def _clip_v(cs, v0, v1):
    return cs ^ rect(-1e4, v0, 1e4, v1)


def _ball(r, zc, neck=0.4, seg=24):
    """A ball turned on a stem (axis z, centre zc), its underside drawn in to 45 degrees down to
    the stem, so it prints upright with nothing hanging (a plain sphere's lower half did)."""
    z0 = zc - r - (r - neck)
    prof = [(0.0, z0), (neck, z0)] + [(r * math.sin(t), zc - r * math.cos(t)) for t in np.linspace(0.25, math.pi - 0.05, 16)]
    return PW._revolve(prof + [(0.0, zc + r)], seg)


def _chrys(c, r, n=12, half=False, disc=0.55, petal_w=0.55):
    """A chrysanthemum seen face on, as CrossSections: (petals, centre). ``n`` pointed petals
    radiating from a disc to radius ``r`` (``half``: n petals over the upper half only, for a
    tympanum or a transom)."""
    if half:
        angs = [math.pi * (i + 0.5) / n for i in range(n)]
    else:
        angs = [2 * math.pi * i / n for i in range(n)]
    pet = cs_union([_lens((c[0] + r * 0.55 * math.cos(a), c[1] + r * 0.55 * math.sin(a)), r * 0.9, petal_w, a)
                    for a in angs])
    centre = circle(c, disc, 16)
    if half:
        keep = rect(c[0] - r - 1, c[1], c[0] + r + 1, c[1] + r + 1)
        pet, centre = pet ^ keep, centre ^ keep
    return pet, centre


# ================================================================== the Wyndham (house 91)
# The batch's flagship, 1889: a Gilded Age mansion of pressed brick in Sussex bond below and
# beaded narrow-and-wide lap above, brownstone dressings, cream trim and gold accents. Queen Anne
# massing (a great octagonal tower on the front-east corner rising a storey over the eave to a
# tall bell cap, a two-storey bow on the west), a Second Empire roof (a straight mansard slated in
# a trellis of diamond slates, a taller pavilion mansard over the front pavilion, crests and
# sunflower cresting) and a Colonial Revival heart (the pavilion's tripartite window and Palladian
# add-in, a fanlit entrance between fluted pilasters, a porch of Scamozzi Ionic columns round the
# tower with a balustrade on its roof). The ornament is the Aesthetic Movement's: chrysanthemums,
# peacock feathers, lilies, bamboo and pagoda hoods.

WY_LEVELS = dict(lo=42.0, hi=52.6)      # the building sets them: the brick storey's top and the lap storey's foot,
                                        # in a block's own heights (from its foot)


def slate_trellis(k, j, P=7):
    """The Wyndham's slating: square slates crossed by two families of diagonals of diamond-cut
    slates, a trellis seven slates to the mesh."""
    u = j + 0.5 * (k % 2)
    a, b = int(round(u - 0.5 * k)), int(round(u + 0.5 * k))
    return "diamond" if a % P == 0 or b % P == 0 else "square"


# ------------------------------------------------------------------ wall skins, corners, foundation
def brick_sussex(region, datum=0.0, bl=2.4, bh=0.8, mortar=0.5, bed=0.2, d=0.25):
    """Sussex bond: three stretchers and a header in every course, each course's header over
    the middle stretcher of the course below (the Wyndham's brick storey)."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    unit = 3 * bl + bl / 2
    cells = []
    k = math.floor((v0 - datum) / bh) - 1
    while datum + k * bh < v1:
        v = datum + k * bh
        top = v + bh - bed
        u = u0 - 2 * unit + (k % 2) * unit / 2
        while u < u1 + unit:
            for a, b in ((0.0, bl), (bl, 2 * bl), (2 * bl, 3 * bl), (3 * bl, unit)):
                cells.append(rect(u + a + mortar / 2, v, u + b - mortar / 2, top))
            u += unit
        k += 1
    return M.extrude(cs_union(cells) ^ region, d)


def lap_beadnarrow(region, datum=0.0, wide=1.6, narrow=1.0, d=0.34):
    """Narrow-and-wide lap: a wide bevel board, then a narrow board with a bead at its butt,
    in turn (the Wyndham's upper storey). Every butt is a short square step (it prints clean
    upright) and the bead swells at 31 degrees."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    p = wide + narrow
    k0 = math.floor((v0 - datum) / p) - 1
    k1 = math.ceil((v1 - datum) / p) + 1
    pts = [(datum + k0 * p, 0.0)]
    for k in range(k0, k1):
        vk = datum + k * p
        vn = vk + wide
        pts += [(vk, d), (vn, 0.06), (vn, d - 0.06), (vn + 0.2, d + 0.06), (vn + 0.4, d - 0.06), (vn + 0.5, 0.22),
                (vn + narrow, 0.06)]
    pts.append((datum + k1 * p, 0.0))
    strip = M.extrude(poly(pts), (u1 - u0) + 2).transform(frame([u0 - 1, 0, 0], [0, 1, 0], [0, 0, 1], [1, 0, 0]))
    return strip ^ M.extrude(region, d + 0.3).translate([0, 0, -0.1])


def corner_wyndham(L, at_start, qa, qb, w=2.4, t=0.65):
    """The Wyndham's corners: moulded-brick quoins on the brick storey (long and short, each
    block chamfered, a raised field on its face, a 45 degree bevel underneath), and on
    the lap storey a pilaster board (a flute between a plinth and a capital block with a
    45 degree bed)."""
    def span(a, b):
        return (a, b) if at_start else (L - b, L - a)
    lo, hi = WY_LEVELS["lo"], WY_LEVELS["hi"]
    parts = []
    v = max(qa, 1.8)
    k = 0
    while v < min(qb, lo) - 1.8:
        leg = 4.6 if k % 2 == 0 else 2.8
        top = min(v + 2.0, lo - 0.2)
        a, b = span(-t - 0.3, leg)
        parts.append(chamfer_box(a, v, b, top, 0.0, t + 0.45, c=0.25, bottom=0.45, square=("u0",) if at_start else ("u1",)))
        fa, fb = span(0.5, leg - 0.5)
        if fb - fa > 0.9:
            parts.append(ext(rect(min(fa, fb), v + 0.6, max(fa, fb), top - 0.5), t + 0.44, t + 0.62))
        v += 2.4
        k += 1
    z0 = max(qa, hi)
    if qb - z0 > 6.0:
        a, b = span(0.0, w)
        fa, fb = span(w / 2 - 0.3, w / 2 + 0.3)
        flute = ext(rect(fa, z0 + 2.4, fb, qb - 2.6), t - 0.25, t + 0.5)
        parts.append(box([a, z0, 0.0], [b, qb, t]) - flute)
        pa, pb = span(-0.2, w + 0.2)
        parts.append(chamfer_box(pa, z0, pb, z0 + 1.6, 0.0, t + 0.3, c=0.2, bottom=t + 0.3))
        parts.append(chamfer_box(pa, qb - 1.8, pb, qb, 0.0, t + 0.45, c=0.2, bottom=t + 0.45))
    return union(parts) if parts else M()


def foundation_panelplinth(reg, seed=0):
    """A brownstone plinth of raised panels between pilaster strips, under a bevelled cap with a
    roll (the Wyndham)."""
    b = reg.bounds()
    out = [M.extrude(reg, 0.25)]
    u = b[0] + 1.2
    while u < b[2] - 1.0:
        out.append(ext(rect(u, b[1] + 0.4, u + 1.6, b[3] - 2.2) ^ reg, 0.24, 0.75))
        if u + 14.0 < b[2] - 1.0:
            pan = rect(u + 2.4, b[1] + 1.4, u + 13.2, b[3] - 3.2) ^ reg
            if not pan.is_empty():
                pb = pan.bounds()
                if pb[2] - pb[0] > 2.0 and pb[3] - pb[1] > 2.0:
                    out.append(chamfer_box(pb[0], pb[1], pb[2], pb[3], 0.24, 0.42, c=0.3, bottom=0.42))
        u += 14.0
    cap = rect(b[0] - 1, b[3] - 2.0, b[2] + 1, b[3]) ^ reg
    if not cap.is_empty():
        cb = cap.bounds()
        out.append(M.hull_points([(x, cb[1], 0.24) for x in (cb[0], cb[2])] + [(x, cb[1] + 0.6, 0.85) for x in (cb[0], cb[2])] +
                                 [(x, cb[3], 0.85) for x in (cb[0], cb[2])] + [(x, cb[3], 0.24) for x in (cb[0], cb[2])]))
        out.append(ext(rect(cb[0], cb[1] + 0.9, cb[2], cb[1] + 1.5), 0.84, 1.05))
    return union(out)


# ------------------------------------------------------------------ cornice ornaments
def course_bamboo(L, h, b, pitch, margin, p):
    """A bamboo stalk along the course, ringed at every node, a leaf sprouting from every
    fourth node (the Wyndham's storey joint)."""
    out = [_st(rect(0.2, 0.35, L - 0.2, h - 0.35), b, 0.3)]
    us = list(np.arange(1.3, L - 1.0, 2.6))
    out.append(_st(cs_union([rect(u - 0.3, 0.1, u + 0.3, h - 0.1) for u in us]), b, 0.45))
    leaves = [_lens((u + 0.95, h * 0.55), 1.5, 0.55, 0.3) for u in us[1::4] if u + 2.0 < L - 0.4]
    if leaves:
        out.append(_st(cs_union(leaves) ^ rect(0.2, 0.05, L - 0.2, h - 0.05), b + 0.3, 0.25))
    return out


def course_pearlribbon(L, h, b, pitch, margin, p):
    """A ribbon wound slantwise round a rod, a pearl in every turn (the Wyndham's eave)."""
    pu = 2.4
    n = max(1, int((L - 0.6) / pu))
    u0 = (L - n * pu) / 2
    rod = rect(0.2, 0.3, L - 0.2, h - 0.3)
    bands = cs_union([poly([(u0 + pu * k, 0.3), (u0 + pu * k + 0.6, 0.3), (u0 + pu * (k + 0.5) + 0.6, h - 0.3),
                            (u0 + pu * (k + 0.5), h - 0.3)]) for k in range(n)]) ^ rod
    pearls = cs_union([circle((u0 + pu * (k + 0.75) + 0.3, h / 2), 0.32, 12) for k in range(n)]) ^ rod
    return [_st(rod, b, 0.25), _st(bands, b + 0.25, 0.2), _st(pearls, b + 0.25, 0.3)]


def frieze_chrysanthemums(L, h, b, pitch, margin, pair, half):
    """Chrysanthemum roundels, a ringed disc in a ring of pointed petals, one in every bay; at
    every station between them a bamboo cane with a pointed leaf either side (the Wyndham's
    storey joint)."""
    v0, v1 = 0.8, h - 0.8
    hh = v1 - v0
    vm = (v0 + v1) / 2
    out = []
    for uc, wd in CO._between(L, pitch, margin, pair, half):
        r = min(hh * 0.48, wd * 0.38, 2.4)
        if r < 1.2:
            continue
        pet, centre = _chrys((uc, vm), r, n=11, petal_w=0.6)
        out.append(_st(_clip_v(pet, v0, v1), b, 0.35))
        out.append(_st(centre, b, 0.6))
    for u in CO._us(L, pitch, margin, 0.0):
        if 0.8 < u < L - 0.8:
            cane = rect(u - 0.3, v0 + 0.1, u + 0.3, v1 - 0.1)
            leaves = cs_union([_lens((u + sg * 0.7, vm + 0.4), 1.6, 0.5, sg * 0.9) for sg in (-1, 1)])
            out.append(_st(_clip_v(cane + leaves, v0, v1) ^ rect(0.2, -1, L - 0.2, h + 1), b, 0.4))
    return out, []


def frieze_peacocks(L, h, b, pitch, margin, pair, half):
    """Peacock feathers: in every bay between the bracket pairs three feathers fanning up from a
    knot, each a stem ending in an eye (an outer ring round a raised heart) (the Wyndham's
    eave)."""
    v0, v1 = 0.8, h - 0.8
    hh = v1 - v0
    out = []
    for uc, wd in CO._between(L, pitch, margin, pair, half):
        if wd < 3.0:
            continue
        angs = (-0.5, 0.0, 0.5) if wd >= 5.6 else (0.0,)
        base = (uc, v0 + 0.3)
        Lf = hh - 1.5
        stems, rings, hearts = [], [], []
        for a in angs:
            ca, sa = math.sin(a), math.cos(a)
            tip = (base[0] + Lf * ca * (0.8 if a else 1.0), base[1] + Lf * sa * (0.8 if a else 1.0))
            stems.append(stroke([base, ((base[0] + tip[0]) / 2 + 0.2 * a, (base[1] + tip[1]) / 2), tip], 0.5))
            rings.append(oval(tip, 0.62, 0.85, 20))
            hearts.append(oval((tip[0], tip[1] + 0.05), 0.3, 0.42, 14))
        out.append(_st(_clip_v(cs_union(stems), v0, v1), b, 0.3))
        out.append(_st(_clip_v(cs_union(rings), v0, v1), b, 0.45))
        out.append(_st(_clip_v(cs_union(hearts), v0, v1), b + 0.45, 0.2))
        out.append(_st(circle(base, 0.5, 12), b, 0.5))
    return out, []


def frieze_lilies(L, h, b, pitch, margin, pair, half):
    """Lilies: in every bay a stem rising in a gentle S from a pair of long leaves to a
    trumpet flower of three pointed petals (the Wyndham's tower)."""
    v0, v1 = 0.8, h - 0.8
    hh = v1 - v0
    out = []
    for uc, wd in CO._between(L, pitch, margin, pair, half):
        if wd < 3.0:
            continue
        top = (uc, v0 + hh * 0.66)
        stem = stroke([(uc, v0 + 0.2), (uc + 0.35, v0 + hh * 0.3), (uc - 0.25, v0 + hh * 0.5), top], 0.5)
        leaves = cs_union([_lens((uc + sg * 0.75, v0 + hh * 0.28), hh * 0.5, 0.55, math.pi / 2 - sg * 0.55) for sg in (-1, 1)])
        petals = cs_union([_lens((top[0] + 0.75 * math.sin(a), top[1] + 0.75 * math.cos(a)), 1.7, 0.6, math.pi / 2 - a)
                           for a in (-0.65, 0.0, 0.65)])
        out.append(_st(_clip_v(stem + leaves, v0, v1), b, 0.35))
        out.append(_st(_clip_v(petals, v0, v1), b, 0.5))
    return out, []


def bracket_fiddlehead(h, d, t):
    """A fiddlehead console: a body tapering from the wall up and out to a fern head curled
    under the soffit's front edge, three leaflets along its underside and a sunk eye in the
    curl (side profile, top at v = 0; the Wyndham)."""
    r = min(0.3 * h, 0.42 * d, 1.25)
    c = (d - r, -r)
    pts = [(0.0, 0.0), (d - r, 0.0)]
    for t_ in np.linspace(0.0, 1.0, 12):
        a = math.pi / 2 - t_ * math.pi * 1.25
        pts.append((c[0] + r * math.cos(a), c[1] + r * math.sin(a)))
    pts += [(d * 0.5, -h * 0.5), (0.8, -h + 0.5), (0.0, -h + 0.5)]
    body = poly(pts)
    leaf = []
    for k, s in enumerate((0.3, 0.52, 0.74)):
        x = d - r * 1.2 - (d - r * 1.2 - 0.9) * s
        y = -r * 1.6 - (h - r * 1.6 - 0.6) * s
        leaf.append(circle((x - 0.1, y - 0.25), 0.36, 10))
    prof = cs_union([body, circle(c, r, 20)] + leaf)
    return prof - circle(c, min(0.5, r * 0.42), 12)


def japanfret(L, h):
    """A Japanese key fret as CrossSections: one line running along in square hooks, each
    hook turned in once, on a fillet (the Wyndham's crests)."""
    lw = 0.44
    pu = 3.0
    n = max(1, int((L - 0.6) / pu))
    u0 = (L - n * pu) / 2
    lo, hi = 0.35, h - 0.35
    mid = (lo + hi) / 2
    pts = []
    for k in range(n):
        u = u0 + pu * k
        pts += [(u, lo), (u, hi), (u + 1.9, hi), (u + 1.9, mid), (u + 0.95, mid), (u + 0.95, lo)]
    pts.append((u0 + pu * n, lo))
    line = stroke(pts, lw, caps=False)
    base = rect(0.2, 0.05, L - 0.2, 0.3)
    return [cs_union([line, base]) ^ rect(0.2, 0.05, L - 0.2, h - 0.05)]


# ------------------------------------------------------------------ the mansard's add-ins
def _pagoda(half, v0, rise=2.4, tip=0.9, t=0.9):
    """A pagoda hood's outline over a head ``half`` wide at v0: a low gable whose ends turn up
    in little horns (the Wyndham's upper windows and add-ins)."""
    pts = [(-half - 1.0, v0 - 0.01), (-half - 1.4, v0 + tip), (-half - 0.4, v0 + 0.55), (0.0, v0 + rise),
           (half + 0.4, v0 + 0.55), (half + 1.4, v0 + tip), (half + 1.0, v0 - 0.01)]
    out = poly(pts)
    return out, out.offset(-t * 0.6, MIT, 4.0) ^ rect(-50, v0 + 0.3, 50, 50)


def addin_wyndham(w=5.0, h=8.6, A=0.9):
    """A Wyndham add-in: a round-headed light in a moulded architrave, a pagoda hood over it on
    two small blocks, a sill (its plug's roof a gable)."""
    r = w / 2
    op = O.opening_cs(w, h, r)
    bars = cs_union([rect(-RIB / 2, -1.0, RIB / 2, h + 1.0), rect(-w, h - r - RIB / 2, w, h - r + RIB / 2)])
    half = w / 2 + A + 0.4
    vt = h + A + 0.4
    body = cs_union([rect(-half, -0.2, half, vt), circle((0.0, h - r), r + A + 0.2, 32)])
    hood, inner = _pagoda(half, vt - 0.01, rise=2.4)
    parts = [ext(body - op, 0.0, 0.6),
             MD.band(op.offset(A, RND), A, MD.ARCHITRAVE, clip=rect(-20, 0.0, 20, 40) - op),
             ext(hood, 0.0, 1.0), ext(inner, 0.99, 1.3)]
    for sg in (-1, 1):
        parts.append(chamfer_box(sg * half - 0.6, vt - 1.6, sg * half + 0.6, vt, 0.0, 1.1, c=0.25))
    sw = half + 0.2
    parts.append(MD.run(-sw, sw, 0.0, MD.SILL, 1.0, up=False))
    parts = [p - ext(op, -1.0, 5.0) for p in parts]
    outline = cs_union([body, hood]).offset(-0.4, RND) ^ rect(-50, 0.2, 50, 100)
    return dict(light=op, bars=bars, frame=parts, outline=outline, top=vt + 2.4, bottom=-1.0)


def addin_wyndham_palladian(wc=5.4, hc=10.4, ws=2.4, hs=6.6, mul=1.0, A=0.9):
    """The pavilion's Palladian add-in: a round-headed centre light between two flat-headed side
    lights, mullions with capital blocks under an entablature that runs across the side lights, an archivolt
    with a keystone over the centre, a balustered apron under the sill."""
    r = wc / 2
    xs = r + mul + ws / 2
    centre = O.opening_cs(wc, hc, r)
    sides = [rect(sg * xs - ws / 2, 0.0, sg * xs + ws / 2, hs) for sg in (-1, 1)]
    light = cs_union([centre] + sides)
    bars = cs_union([rect(-RIB / 2, -1.0, RIB / 2, hc + 1.0), rect(-wc, hc - r - RIB / 2, wc, hc - r + RIB / 2)] +
                    [rect(sg * xs - ws, hs * 0.5 - RIB / 2, sg * xs + ws, hs * 0.5 + RIB / 2) for sg in (-1, 1)])
    half = xs + ws / 2 + mul
    ve = hs + 1.4
    body = cs_union([rect(-half, -0.2, half, ve), circle((0.0, hc - r), r + A + 0.5, 40)])
    parts = [ext(body - light, 0.0, 0.6)]
    parts.append(MD.band(centre.offset(A, RND), A, MD.ARCHITRAVE, clip=rect(-20, hs + 0.6, 20, 40) - centre))
    parts.append(keystone(0.0, hc - 0.3, A + 1.2, 1.1, 1.6, 0.0, 1.3))
    for sg in (-1, 1):
        for x in (sg * (r + mul / 2), sg * (half - mul / 2)):
            parts.append(ext(rect(x - mul / 2, 0.0, x + mul / 2, hs), 0.0, 0.9))
            parts.append(chamfer_box(x - mul / 2 - 0.2, hs - 0.01, x + mul / 2 + 0.2, hs + 0.6, 0.0, 1.1, c=0.2))
        ea, eb = sorted((sg * (r + mul + 0.1), sg * (half + 0.3)))
        parts.append(ext(rect(ea, hs + 0.59, eb, hs + 1.4), 0.0, 0.8))
        parts.append(MD.run(ea - 0.1, eb + 0.1, hs + 1.4 + 0.8, MD.CROWN, 0.8, up=False))
    sw = half + 0.3
    parts.append(MD.run(-sw, sw, 0.0, MD.SILL, 1.0, up=False))
    ap = [rect(-half + 0.4, -2.8, half - 0.4, -2.3), rect(-half + 0.4, -1.3, half - 0.4, -0.79)]
    for x in np.linspace(-half + 1.2, half - 1.2, 7):
        ap.append(cs_union([rect(x - 0.25, -2.4, x + 0.25, -1.2), oval((x, -1.85), 0.42, 0.42, 12)]))
    parts.append(ext(cs_union(ap), 0.0, 0.7))
    parts = [p - ext(light, -1.0, 5.0) for p in parts]
    outline = body.offset(-0.4, RND) ^ rect(-50, 0.2, 50, 100)
    top = hc + A + 0.5 + 0.4
    return dict(light=light, bars=bars, frame=parts, outline=outline, top=top, bottom=-2.8)


def addin_wyndham_tower(rx=1.9, ry=2.8, A=0.8):
    """The tower cap's add-in: an upright oval light in a moulded frame under a little pagoda
    hood, on a sill."""
    c = (0.0, ry + 0.6)
    light = oval(c, rx, ry, 32)
    bars = cs_union([rect(-RIB / 2, -1.0, RIB / 2, 2 * ry + 2), rect(-rx - 1, c[1] - RIB / 2, rx + 1, c[1] + RIB / 2)])
    body = cs_union([oval(c, rx + A + 0.4, ry + A + 0.4, 36), rect(-rx - A - 0.4, -0.2, rx + A + 0.4, c[1])])
    vt = c[1] + ry + A + 0.2
    hood, inner = _pagoda(rx + A, vt - 0.6, rise=1.8, tip=0.8)
    parts = [ext(body - light, 0.0, 0.6), MD.band(light.offset(A, RND), A, MD.CASING, clip=rect(-20, -1, 20, 40) - light),
             ext(hood, 0.0, 0.9)]
    sw = rx + A + 0.6
    parts.append(MD.run(-sw, sw, 0.0, MD.SILL, 0.9, up=False))
    parts = [p - ext(light, -1.0, 5.0) for p in parts]
    outline = cs_union([body, hood]).offset(-0.4, RND) ^ rect(-50, 0.2, 50, 100)
    return dict(light=light, bars=bars, frame=parts, outline=outline, top=vt + 1.8, bottom=-1.0)


# ------------------------------------------------------------------ chimney, cresting, finial
def chimney_wyndham(w=11.0, d=9.0, h=26.0):
    """A Queen Anne stack: a plinth, a shaft with corner pilaster strips framing a sunk panel on
    every face that holds a raised sunflower roundel, a cap corbelled out in three steps over a
    band of blind arches, a slab, and two octagonal pots."""
    h = round(h / 0.2) * 0.2
    sh = h - 6.0
    body = box([-w / 2 - 0.5, -d / 2 - 0.5, 0.0], [w / 2 + 0.5, d / 2 + 0.5, 2.0])
    body = body + M.hull_points([(x, y, 1.99) for x in (-w / 2 - 0.5, w / 2 + 0.5) for y in (-d / 2 - 0.5, d / 2 + 0.5)] +
                                [(x, y, 2.5) for x in (-w / 2, w / 2) for y in (-d / 2, d / 2)])
    body = body + box([-w / 2, -d / 2, 0.0], [w / 2, d / 2, sh])
    for (L, D, rot) in ((w, d, 0), (d, w, 90), (w, d, 180), (d, w, 270)):
        pan = box([-L / 2 + 1.5, D / 2 - 0.5, 3.6], [L / 2 - 1.5, D / 2 + 0.1, sh - 1.6])
        body = body - pan.rotate([0, 0, rot])
        zc = (3.6 + sh - 1.6) / 2
        rr = min(L / 2 - 2.2, 2.2)
        pet, cen = _chrys((0.0, zc), rr, n=10, petal_w=0.6)
        disc = (M.extrude(pet, 0.35) + M.extrude(cen, 0.55)).transform(np.array([[1.0, 0, 0, 0], [0, 0, 1.0, D / 2 - 0.51],
                                                                                 [0, 1.0, 0, 0]]))
        body = body + disc.rotate([0, 0, rot])
    # the cap: a frieze band (bevelled out from the shaft) sunk with a row of blind arches, a
    # corbel stepped out three times at 45 degrees, then the slab
    fb = 0.6

    def ring(e0, e1, z0, z1):
        return M.hull_points([(x, y, z0) for x in (-w / 2 - e0, w / 2 + e0) for y in (-d / 2 - e0, d / 2 + e0)] +
                             [(x, y, z1) for x in (-w / 2 - e1, w / 2 + e1) for y in (-d / 2 - e1, d / 2 + e1)])
    body = body + ring(0.0, fb, sh - fb - 0.01, sh) + ring(fb, fb, sh - 0.01, sh + 2.4)
    for (L, D, rot) in ((w + 2 * fb, d + 2 * fb, 0), (d + 2 * fb, w + 2 * fb, 90),
                        (w + 2 * fb, d + 2 * fb, 180), (d + 2 * fb, w + 2 * fb, 270)):
        n = max(2, int(L / 2.2))
        arches = cs_union([arch_cs(-L / 2 + L * (i + 0.2) / n, -L / 2 + L * (i + 0.8) / n, 0.0, 0.6) for i in range(n)])
        band = M.extrude(arches, 0.3).transform(np.array([[1.0, 0, 0, 0], [0, 0, 1.0, D / 2 - 0.29], [0, 1.0, 0, sh + 0.45]]))
        body = body - band.rotate([0, 0, rot])
    for k in range(3):
        e, z = fb + 0.4 * k, sh + 2.4 + 0.8 * k
        body = body + ring(e, e + 0.4, z - 0.01, z + 0.4) + ring(e + 0.4, e + 0.4, z + 0.39, z + 0.8)
    zt = sh + 4.8
    body = body + ring(fb + 1.2, fb + 1.2, zt - 0.01, zt + 1.2)
    zp = zt + 1.19
    for sx in (-1, 1):
        x = sx * w * 0.24
        pot = (M.cylinder(3.2, 1.7, 1.35, 8).translate([x, 0.0, zp]) + M.cylinder(0.41, 1.35, 1.7, 8).translate([x, 0, zp + 3.19])
               + M.cylinder(0.4, 1.7, 1.7, 8).translate([x, 0, zp + 3.59]))
        pot = pot - M.cylinder(4.8, 0.85, 0.85, 8).translate([x, 0, zp + 0.4])
        body = body + pot
    return body          # (solid: a sealed flue would print as a hidden cavity)


def fence_wyndham(L, h):
    """Wyndham cresting (drawn at half size for SE.printable): spears with arrow heads, and
    between every two a sunflower on a stem, a ring of six petals round a ringed disc."""
    pitch = 3.2
    n = max(1, int(round(L / pitch)))
    p = L / n
    rail = h * 0.28
    cells = [rect(0.0, 0.0, L, 0.6), rect(0.0, rail, L, rail + 0.45)]
    for j in range(n + 1):
        u = p * j
        cells.append(rect(u - 0.25, 0.0, u + 0.25, h - 0.6))
        cells.append(poly([(u - 0.6, h - 0.75), (u + 0.6, h - 0.75), (u, h + 0.2)]))
        if j < n:
            m = u + p / 2
            vc = rail + 0.45 + (h - rail - 0.45) * 0.55
            rr = min(0.85, p / 2 - 0.55)
            # the stem runs up to the disc, so the disc hangs on it inside its ring
            cells.append(rect(m - 0.26, rail + 0.4, m + 0.26, vc))
            cells.append(circle((m, vc), rr, 18) - circle((m, vc), rr - 0.36, 14))
            cells.append(circle((m, vc), 0.24, 10))
            for a in np.linspace(0, 2 * math.pi, 6, endpoint=False) + math.pi / 6:
                tipx, tipy = m + (rr + 0.55) * math.cos(a), vc + (rr + 0.55) * math.sin(a)
                bx, by = m + (rr - 0.1) * math.cos(a), vc + (rr - 0.1) * math.sin(a)
                nx, ny = -math.sin(a) * 0.23, math.cos(a) * 0.23
                cells.append(poly([(bx + nx, by + ny), (tipx, tipy), (bx - nx, by - ny)]))
    return cs_union(cells) ^ rect(0.0, 0.0, L, h + 1.0)


def fence_wyndham_balustrade(L, h):
    """A wooden balustrade seen face on (printed flat): a plinth, a moulded hand rail, square
    newels with ball caps every 14 mm or so, and between them bottle balusters (full size)."""
    nseg = max(1, int(round(L / 14.0)))
    seg = L / nseg
    cells = [rect(0.0, 0.0, L, 0.9), rect(0.0, h - 1.1, L, h - 0.35), rect(0.25, h - 0.36, L - 0.25, h)]
    for j in range(nseg + 1):
        u = min(max(seg * j, 0.85), L - 0.85)
        cells.append(rect(u - 0.85, 0.0, u + 0.85, h + 0.2))
        cells.append(circle((u, h + 0.75), 0.62, 16))
        if j < nseg:
            a, b = u + 0.85, min(max(seg * (j + 1), 0.85), L - 0.85) - 0.85
            nb = max(1, int((b - a) / 1.75))
            for k in range(nb):
                x = a + (b - a) * (k + 0.5) / nb
                cells.append(cs_union([rect(x - 0.3, 0.85, x + 0.3, h - 1.05), oval((x, 0.85 + (h - 1.9) * 0.33), 0.48, 0.8, 14),
                                       rect(x - 0.45, h - 1.5, x + 0.45, h - 1.05)]))
    return cs_union(cells) ^ rect(0.0, 0.0, L, h + 1.5)


def finial_wyndham(h=16.0):
    """The tower's finial: a turned base, an urn with a lid, then a slender spire threaded with
    three orbs that diminish upward, ending in a point no thinner than 0.8 mm."""
    prof = [(0.0, 0.0), (1.7, 0.0), (1.7, 0.6), (1.2, 1.1), (0.75, 1.6), (0.75, 2.2), (1.35, 3.0), (1.55, 3.9), (1.3, 4.8),
            (0.8, 5.2), (1.05, 5.5), (0.55, 5.9), (0.0, 5.9)]
    body = PW._revolve(prof, 28)
    body = body + M.cylinder(h - 5.8, 0.55, 0.4, 14).translate([0, 0, 5.85])
    for z, r in ((7.6, 1.0), (10.0, 0.8), (12.2, 0.62)):
        body = body + _ball(r, z, neck=0.45)
    return body


# ------------------------------------------------------------------ windows and doors
PULVIN = [(0.0, 0.5), (0.25, 0.9), (0.5, 1.0), (0.75, 0.9), (1.0, 0.5)]


def window_wyndham_lower(w=9.0, h=23.0, A=1.0, qa=True):
    """Wyndham ground floor: a Queen Anne sash (the upper sash a big light ringed by small
    border lights) in an architrave eared at its head, a pulvinated frieze, a cornice and a
    segmental pediment holding a half chrysanthemum; a sill over a panelled apron with a boss."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    sash = O.window_insert(w, h, 0, lites=(1, 1), qa=qa, bare=True)["insert"]
    half = w / 2 + A + 0.7
    outer = cs_union([op.offset(A, MIT, 4.0), rect(-half, h - 1.6, half, h + A)])
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             MD.band(outer, A + 0.7, MD.ARCHITRAVE, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op)]
    vf = h + A
    parts.append(MD.run(-half, half, vf - 0.01, PULVIN, 1.6, up=True))
    vc = vf + 1.6 + 0.96                                 # the cornice overlaps the frieze
    parts.append(MD.run(-half - 0.6, half + 0.6, vc, MD.CROWN, 1.0, up=False))
    rise = 2.6
    seg = arch_cs(-half - 0.6, half + 0.6, vc - 0.01, vc - 0.01, rise=rise, seg=40)
    rim = seg - seg.offset(-0.8, MIT, 4.0)
    parts.append(ext(rim ^ rect(-50, vc - 0.01, 50, 50), 0.0, 1.1))
    parts.append(ext(seg.offset(-0.8, MIT, 4.0) ^ rect(-50, vc, 50, 50), 0.0, 0.5))
    pet, cen = _chrys((0.0, vc + 0.1), rise - 0.95, n=9, half=True, disc=0.6, petal_w=0.55)
    parts.append(ext(pet ^ seg.offset(-0.85, MIT, 4.0), 0.49, 0.9))
    parts.append(ext(cen ^ seg.offset(-0.85, MIT, 4.0), 0.49, 1.1))
    sw = w / 2 + A + 0.4
    parts.append(MD.run(-sw, sw, 0.0, MD.SILL, 1.0, up=False))
    ap = rect(-w / 2 - 0.2, -3.6, w / 2 + 0.2, -0.79)
    parts.append(ext(ap, 0.0, 0.5))
    parts.append(chamfer_box(-w / 2 + 0.6, -3.0, w / 2 - 0.6, -1.4, 0.49, 0.35, c=0.2))
    parts.append(ext(oval((0.0, -2.2), 1.0, 0.55, 20), 0.83, 1.15))
    return O._one_piece([sash], parts, op, plug_cs, O.PLUG, vc + rise + 0.2, -3.6)


def window_wyndham_upper(w=8.6, h=20.0, A=0.9):
    """Wyndham upper floor: a one-over-one sash in a plain architrave, a bamboo bar across its
    head, and a pagoda hood (a low gable turned up at its ends) on two consoles; a sill on two
    blocks."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    sash = O.window_insert(w, h, 0, lites=(1, 1), bare=True)["insert"]
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             MD.band(op.offset(A, MIT, 4.0), A, MD.ARCHITRAVE, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op)]
    half = w / 2 + A
    vb = h + A
    parts.append(ext(rect(-half, vb - 0.01, half, vb + 1.0), 0.0, 0.6))
    nodes = cs_union([rect(u - 0.3, vb - 0.01, u + 0.3, vb + 1.0) for u in np.linspace(-half + 0.8, half - 0.8, 4)])
    parts.append(ext(nodes, 0.0, 0.9))
    vh = vb + 1.0
    hood, inner = _pagoda(half + 0.4, vh, rise=2.6, tip=1.0)
    parts.append(ext(hood, 0.0, 1.2))
    parts.append(ext(inner, 1.19, 1.5))
    for sg in (-1, 1):
        x = sg * (half + 0.2)
        parts.append(ext(cs_union([rect(x - 0.55, vb - 2.6, x + 0.55, vh), circle((x, vb - 2.6), 0.55, 12)]), 0.0, 1.0))
    sw = half + 0.2
    parts.append(MD.run(-sw, sw, 0.0, MD.SILL, 1.0, up=False))
    for sg in (-1, 1):
        parts.append(chamfer_box(sg * (w / 2) - 0.7, -1.8, sg * (w / 2) + 0.7, -0.8, 0.0, 0.9, c=0.25))
    return O._one_piece([sash], parts, op, plug_cs, O.PLUG, vh + 2.7, -1.8)


def window_wyndham_tripartite(wc=8.4, ws=3.4, h=23.0, mul=1.6, A=1.0):
    """The pavilion's Colonial Revival tripartite window: a two-over-two sash between narrow
    one-over-one side lights, fluted mullion pilasters on plinths, a full entablature (an
    architrave, a frieze of three swags, a cornice) and a balustered apron."""
    W = wc + 2 * ws + 2 * mul
    op = rect(-W / 2, 0.0, W / 2, h)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    inner = plug_cs.offset(-0.6, MIT, 4.0)
    u0, v0, u1, v1 = inner.bounds()
    vm = (v0 + v1) / 2
    meet = 0.6
    lights = []
    for a, b in ((u0, -wc / 2 - mul + 0.3), (-wc / 2 + 0.3, wc / 2 - 0.3), (wc / 2 + mul - 0.3, u1)):
        lights.append(rect(a, v0, b, vm - meet / 2))
        lights.append(rect(a, vm + meet / 2, b, v1))
    g = cs_union(lights)
    bars = cs_union([rect(-RIB / 2, v0 - 1, RIB / 2, v1 + 1)])
    body = [ext(plug_cs, -pl, -0.6)]
    sash = _glazed(body, g, pl, bars, plug_cs) + [ext(rect(u0, vm - meet / 2 - 0.01, u1, vm + meet / 2 + 0.01), -pl, -0.3)]
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             MD.band(op.offset(A, MIT, 4.0), A, MD.ARCHITRAVE, clip=rect(-W - 10, 0.0, W + 10, h + 40) - op)]
    for sg in (-1, 1):
        x = sg * (wc / 2 + mul / 2)
        pil = rect(x - mul / 2, 0.0, x + mul / 2, h)
        parts.append(ext(pil, 0.0, 1.0) - ext(rect(x - 0.25, 2.0, x + 0.25, h - 2.0), 0.7, 1.1))
        parts.append(chamfer_box(x - mul / 2 - 0.2, 0.0, x + mul / 2 + 0.2, 1.6, 0.0, 1.2, c=0.2))
        parts.append(chamfer_box(x - mul / 2 - 0.2, h - 1.2, x + mul / 2 + 0.2, h, 0.0, 1.2, c=0.2))
    half = W / 2 + A + 0.3
    va = h + A
    parts.append(ext(rect(-half, va - 0.01, half, va + 0.8), 0.0, 0.9))
    vf = va + 0.8
    parts.append(ext(rect(-half, vf - 0.01, half, vf + 2.2), 0.0, 0.5))
    sw_ = cs_union([swag(-half + 0.8 + k * (2 * half - 1.6) / 3, -half + 0.8 + (k + 1) * (2 * half - 1.6) / 3, vf + 1.9, 1.0,
                         width=0.6) for k in range(3)])
    parts.append(ext(_clip_v(sw_, vf + 0.2, vf + 2.1), 0.49, 0.95))
    vc = vf + 2.2 + 1.2
    parts.append(MD.run(-half - 0.7, half + 0.7, vc, MD.CROWN, 1.2, up=False))
    sw = half + 0.2
    parts.append(MD.run(-sw, sw, 0.0, MD.SILL, 1.0, up=False))
    apr = [rect(-W / 2, -3.2, W / 2, -2.7), rect(-W / 2, -1.3, W / 2, -0.79)]
    for x in np.linspace(-W / 2 + 0.9, W / 2 - 0.9, 9):
        apr.append(cs_union([rect(x - 0.25, -2.8, x + 0.25, -1.2), oval((x, -2.0), 0.45, 0.45, 12)]))
    parts.append(ext(cs_union(apr), 0.0, 0.7))
    return O._one_piece(sash, parts, op, plug_cs, pl, vc + 0.2, -3.2)


def window_wyndham_tower(w=8.2, h=20.0, A=0.9):
    """The tower's top storey: a round-headed one-over-one sash with a fan of three panes,
    under an archivolt with a keystone between ringed colonnettes on blocks; a sill."""
    r = w / 2
    spring = h - r
    op = O.opening_cs(w, h, r)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    sash = O.window_insert(w, h, r, lites=(1, 1), bare=True)["insert"]
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             MD.band(op.offset(A, RND), A, MD.ARCHITRAVE, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op),
             MD.band(op.offset(A + 0.9, RND), 0.9, MD.CROWN, clip=rect(-w - 10, spring - 0.4, w + 10, h + 40))]
    parts.append(keystone(0.0, h - 0.3, A + 1.6, 1.2, 1.8, 0.0, 1.5))
    rc = 0.75
    xc = r + A + 0.9 + rc
    vt = spring - 0.2
    for sg in (-1, 1):
        x = sg * xc
        parts.append(ext(rect(x - rc - 0.2, 0.0, x + rc + 0.2, vt), 0.0, 0.5))
        parts.append(chamfer_box(x - rc - 0.35, -0.2, x + rc + 0.35, 2.0, 0.0, 1.3, c=0.25))
        parts.append(chamfer_box(x - rc - 0.35, vt - 0.01, x + rc + 0.35, vt + 1.2, 0.0, 1.3, c=0.25))
        prof = [(0.0, 0.0), (rc, 0.0)]
        z = 0.4
        while z < vt - 2.0 - 0.9:
            prof += [(rc, z), (rc + 0.18, z + 0.2), (rc + 0.18, z + 0.4), (rc, z + 0.6)]
            z += 2.2
        prof += [(rc, vt - 2.0), (0.0, vt - 2.0)]
        col = PW._revolve(prof, 20).rotate([-90, 0, 0]).translate([x, 1.99, 0.0]) ^ box([x - 3, 0.0, 0.0], [x + 3, vt, 5.0])
        parts.append(col)
    sw = xc + rc + 0.5
    parts.append(MD.run(-sw, sw, 0.0, MD.SILL, 1.0, up=False))
    return O._one_piece([sash], parts, op, plug_cs, O.PLUG, h + A + 1.8, -0.2)


def door_wyndham(w=15.2, h=27.0, A=1.2, sl=2.4, rise=3.6):
    """The Wyndham's entrance (Colonial Revival): a pair of leaves, each an upright oval light
    over a raised panel, between leaded side lights, all under one elliptical fanlight of
    radiating bars; fluted pilasters with capital blocks, an entablature with a frieze of swags
    round a chrysanthemum medallion, and a cornice."""
    op = O.opening_cs(w, h, rise)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    spring = h - rise
    mid = 0.5
    u0, u1 = -w / 2 + O.CLR + 0.5, w / 2 - O.CLR - 0.5
    dw = w - 2 * O.CLR - 1.0 - 2 * (sl + 0.7)
    dh = spring - 0.5
    lw = (dw - mid) / 2
    body, lights = [ext(plug_cs, -pl, -1.0)], []
    ul = -dw / 2
    for i in range(2):
        body.append(ext(rect(ul, 0.5, ul + lw, dh), -pl, -0.8))
        cy = dh * 0.62
        lights.append(oval((ul + lw / 2, cy), lw / 2 - 0.8, dh * 0.22, 28))
        body.append(_panel(rect(ul + 0.8, 1.2, ul + lw - 0.8, cy - dh * 0.22 - 1.0)))
        ul += lw + mid
    for sg in (-1, 1):
        a, b = sorted((sg * (dw / 2 + 0.7), sg * (dw / 2 + 0.7 + sl)))
        lights.append(rect(a, 1.2, b, dh))
        body.append(ext(rect(a, 0.5, b, 1.2), -pl, -0.8))
    fan = plug_cs.offset(-0.5, MIT, 4.0) ^ rect(-w, spring + 0.2, w, h + 2)
    rays = []
    fc = (0.0, spring + 0.2)
    for a in np.linspace(0.45, math.pi - 0.45, 4):
        rays.append(stroke([fc, (fc[0] + w * math.cos(a), fc[1] + w * math.sin(a))], RIB))
    tracery = cs_union(rays + [rect(-w, spring + 0.2, w, spring + 0.7), circle(fc, 1.6, 20) - circle(fc, 1.6 - RIB, 20)])
    side_bars = cs_union([rect(sg * (dw / 2 + 0.7 + sl / 2) - RIB / 2, 1.0, sg * (dw / 2 + 0.7 + sl / 2) + RIB / 2, dh)
                          for sg in (-1, 1)] if sl > 4.0 else [rect(-w, dh * 0.5 - RIB / 2, -dw / 2, dh * 0.5 + RIB / 2),
                                                               rect(dw / 2, dh * 0.5 - RIB / 2, w, dh * 0.5 + RIB / 2)])
    sash = _glazed(body, cs_union(lights) + fan, pl, tracery + side_bars, plug_cs)
    sash.append(ext(rect(-w, dh - 0.01, w, spring + 0.2) ^ plug_cs, -pl, -0.5))
    for sg in (-1, 1):
        x = sg * (dw / 2 + 0.35)
        sash.append(ext(rect(x - 0.35, 0.4, x + 0.35, spring + 0.2), -pl, -0.6))
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             MD.band(op.offset(A, MIT, 4.0), A, MD.ARCHITRAVE, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op)]
    pw = 1.8
    xs = w / 2 + A + 0.2 + pw / 2
    vcap = h + A + 0.4
    for sg in (-1, 1):
        x = sg * xs
        parts.append(ext(rect(x - pw / 2, 0.0, x + pw / 2, vcap), 0.0, 1.1) - ext(rect(x - 0.3, 3.0, x + 0.3, vcap - 2.4), 0.8, 1.2))
        parts.append(chamfer_box(x - pw / 2 - 0.3, 0.0, x + pw / 2 + 0.3, 2.6, 0.0, 1.5, c=0.25))
        parts.append(chamfer_box(x - pw / 2 - 0.3, vcap - 1.8, x + pw / 2 + 0.3, vcap, 0.0, 1.5, c=0.25))
        parts.append(ext(circle((x - 0.55, vcap - 0.9), 0.42, 12) + circle((x + 0.55, vcap - 0.9), 0.42, 12), 1.49, 1.8))
    half = xs + pw / 2 + 0.3
    parts.append(ext(rect(-half, vcap - 0.01, half, vcap + 0.8), 0.0, 1.0))
    vf = vcap + 0.8
    parts.append(ext(rect(-half, vf - 0.01, half, vf + 2.6), 0.0, 0.6))
    sws = cs_union([swag(-half + 0.8 + k * (half - 3.2) / 2, -half + 0.8 + (k + 1) * (half - 3.2) / 2, vf + 2.3, 1.0, width=0.6)
                    for k in range(2)] +
                   [swag(2.4 + k * (half - 3.2) / 2, 2.4 + (k + 1) * (half - 3.2) / 2, vf + 2.3, 1.0, width=0.6) for k in range(2)])
    parts.append(ext(_clip_v(sws, vf + 0.2, vf + 2.5), 0.59, 1.0))
    pet, cen = _chrys((0.0, vf + 1.3), 1.25, n=10, petal_w=0.5)
    parts.append(ext(_clip_v(pet, vf + 0.1, vf + 2.5), 0.59, 1.0))
    parts.append(ext(cen, 0.59, 1.3))
    vk = vf + 2.6 + 1.3
    parts.append(MD.run(-half - 0.8, half + 0.8, vk, MD.CROWN, 1.3, up=False))
    return O._one_piece(sash, parts, op, plug_cs, pl, vk + 0.2, 0.0)


def door_wyndham_back(w=10.0, h=25.0, A=1.0):
    """The back door: one leaf with a light over two raised panels, a transom with a half
    chrysanthemum, an architrave and a pagoda hood on two consoles."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    dh = h - 5.0
    u0, u1 = -w / 2 + O.CLR + 0.5, w / 2 - O.CLR - 0.5
    gv0 = dh * 0.5
    gp = (gv0 - 0.8 - 1.2) / 2
    body = [ext(plug_cs, -pl, -1.0), ext(rect(u0, 0.5, u1, dh), -pl, -0.8),
            _panel(rect(u0 + 0.8, 1.2, u1 - 0.8, 1.2 + gp - 0.2)), _panel(rect(u0 + 0.8, 1.2 + gp + 0.2, u1 - 0.8, gv0 - 0.8))]
    light = rect(u0 + 0.9, gv0, u1 - 0.9, dh - 0.8)
    tran = rect(u0, dh + 0.6, u1, h - O.CLR - 0.5)
    pet, cen = _chrys((0.0, dh + 0.6), min(3.4, h - dh - 1.2), n=7, half=True, disc=0.7, petal_w=0.6)
    bars = cs_union([rect(-w, dh + 0.6, w, dh + 1.0), pet, cen])
    sash = _glazed(body, light + tran, pl, bars + rect(-RIB / 2, gv0, RIB / 2, dh), plug_cs)
    sash.append(ext(rect(-w, dh - 0.01, w, dh + 0.62) ^ plug_cs, -pl, -0.5))
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             MD.band(op.offset(A, MIT, 4.0), A, MD.ARCHITRAVE, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op)]
    half = w / 2 + A
    vh = h + A
    hood, inner = _pagoda(half + 0.4, vh, rise=2.6, tip=1.0)
    parts += [ext(hood, 0.0, 1.2), ext(inner, 1.19, 1.5)]
    for sg in (-1, 1):
        x = sg * (half + 0.2)
        parts.append(ext(cs_union([rect(x - 0.55, vh - 2.6, x + 0.55, vh), circle((x, vh - 2.6), 0.55, 12)]), 0.0, 1.0))
    return O._one_piece(sash, parts, op, plug_cs, pl, vh + 2.7, 0.0)


# ------------------------------------------------------------------ porch
def post_scamozzi(h, collar=None, abacus=3.4, slot=(1.2, 1.0)):
    """A Scamozzi Ionic column: an Attic base, a plain shaft with entasis, an astragal, an
    echinus, and a square abacus with a volute under each corner (a half disc hanging flat side
    up, so it stands on the abacus when the porch top prints upside down) (the Wyndham)."""
    z1 = h - 3.0
    r = 1.0
    prof = [(0.0, 1.19), (1.5, 1.19), (1.5, 1.4), (1.3, 1.6), (1.18, 1.8), (1.3, 2.0), (1.12, 2.3), (r, 2.6),
            (r * 1.05, (2.6 + z1) * 0.4), (r * 0.9, z1 - 0.3), (1.08, z1 - 0.1), (1.08, z1 + 0.15), (r * 0.9, z1 + 0.35),
            (1.2, z1 + 0.75), (1.4, z1 + 1.05)]
    body = PW._revolve(prof, 32) + PW._plinth(3.0)
    body = body + PW._top(h, abacus / 2, z1 + 1.05, 1.4, slot, seg=32)
    zt = z1 + 1.05 + max(0.2, abacus / 2 * math.sqrt(2) - 1.4)
    sq = abacus / 2
    for sx in (-1, 1):
        for sy in (-1, 1):
            d = np.array([sx, sy]) / math.sqrt(2)
            c = np.array([sx, sy]) * (sq - 0.25)
            disc = (circle((0.0, 0.0), 0.75, 20) ^ rect(-1, -1, 1, 0.0))
            plate = M.extrude(disc, 0.5).translate([0, 0, -0.25])
            A = np.array([[-d[1], 0.0, d[0], c[0]], [d[0], 0.0, d[1], c[1]], [0.0, 1.0, 0.0, zt]])
            body = body + plate.transform(A)
    return body


def baluster_bottleblock(h, seg=18):
    """A bottle baluster: a swelling body on a ring, a square block at its waist, a slender
    neck and a top block (the Wyndham)."""
    prof = [(0.0, 0.8), (0.32, 0.8), (0.32, 1.0), (0.5, h * 0.2), (0.52, h * 0.3), (0.3, h * 0.42), (0.26, h * 0.5),
            (0.26, h * 0.58), (0.3, h * 0.66), (0.3, h - 0.8)]
    body = PW._revolve(prof, seg) + box([-0.55, -0.55, 0.0], [0.55, 0.55, 0.81]) + box([-0.55, -0.55, h - 0.81], [0.55, 0.55, h])
    return body + box([-0.48, -0.48, h * 0.5 - 0.3], [0.48, 0.48, h * 0.5 + 0.3])


def frieze_ballspindle(u0, u1, v_bot, v_top):
    """A porch frieze: a beam over a row of spindles each threaded with a ball, on a bottom rail,
    and a quarter sunburst pierced with three rays at each post (the Wyndham)."""
    vb = v_top - 3.8
    cells = [rect(u0, v_top - 1.0, u1, v_top + 0.05), rect(u0, vb, u1, vb + 0.6)]
    L = u1 - u0
    n = max(1, int((L - 6.0) / 1.7))
    for k in range(n):
        x = u0 + 3.0 + (L - 6.0) * (k + 0.5) / n
        cells.append(rect(x - 0.27, vb + 0.5, x + 0.27, v_top - 0.9))
        cells.append(circle((x, (vb + v_top) / 2 - 0.2), 0.45, 12))
    for x0, sg in ((u0, 1), (u1, -1)):
        q = circle((x0, v_top - 1.0), 3.2, 32) ^ rect(min(x0, x0 + sg * 3.3), v_top - 4.4, max(x0, x0 + sg * 3.3), v_top - 1.0)
        rays = cs_union([stroke([(x0 + sg * 0.9 * math.cos(a), v_top - 1.0 - 0.9 * math.sin(a)),
                                 (x0 + sg * 2.6 * math.cos(a), v_top - 1.0 - 2.6 * math.sin(a))], 0.55) for a in (0.35, 0.8, 1.25)])
        cells.append(q - rays)
    return cs_union(cells)


def skirt_sunpanels(reg, d=1.2):
    """A porch skirt of framed panels, each holding a raised half sunburst rising from its foot
    (the Wyndham)."""
    u0, v0, u1, v1 = reg.bounds()
    out = [M.extrude(reg, d * 0.4)]
    pw = 7.0
    n = max(1, int((u1 - u0) / pw))
    p = (u1 - u0) / n
    for k in range(n):
        a, b = u0 + p * k, u0 + p * (k + 1)
        out.append(ext(rect(a, v0, a + 0.7, v1), d * 0.4 - 0.01, d * 0.7))
        c = ((a + b) / 2, v0 + 0.6)
        R_ = min((b - a) / 2 - 1.0, v1 - v0 - 1.6)
        if R_ > 1.2:
            fan = circle(c, R_, 28) ^ rect(-1e3, c[1], 1e3, 1e3)
            rays = cs_union([stroke([c, (c[0] + R_ * 1.2 * math.cos(t), c[1] + R_ * 1.2 * math.sin(t))], 0.5)
                             for t in np.linspace(0.35, math.pi - 0.35, 4)])
            out.append(ext((fan - rays) - circle(c, 0.7, 16), d * 0.4 - 0.01, d * 0.62))
            out.append(ext(circle(c, 0.6, 16) ^ rect(-1e3, c[1], 1e3, 1e3), d * 0.4 - 0.01, d * 0.7))
    out.append(ext(rect(u0 - 1, v1 - 0.8, u1 + 1, v1 + 1), d * 0.4 - 0.01, d * 0.7))
    return union(out) ^ M.extrude(reg, d + 0.5)


def edge_ballfringe(L, z0, zc):
    """Porch fascia (the Wyndham): a fillet under the crown hung with balls on stems, long and
    short in turn."""
    out = [rect(0.3, zc - 0.45, L - 0.3, zc)]
    for i, x in enumerate(np.arange(1.0, L - 0.8, 1.3)):
        ln = 1.3 if i % 2 == 0 else 0.7
        out.append(rect(x - 0.25, zc - 0.45 - ln + 0.3, x + 0.25, zc - 0.4))
        out.append(circle((x, zc - 0.45 - ln), 0.4, 12))
    return cs_union(out), 0.6


def entry_wyndham(w, depth, rise, t=1.0):
    """The Wyndham's porch entry: a triangular pediment standing on the porch roof over the
    steps, a raised rim round its face and a half chrysanthemum in the tympanum on a ringed
    disc; its back a lean-to. Local as features.entry_pediment (u across, v up from the porch
    roof top, w out from the house, the face at w = depth); prints upright on its base."""
    face = poly([(-w / 2, 0.0), (0.0, rise), (w / 2, 0.0)])
    parts = [M.extrude(face, depth)]
    parts.append(ext(face - face.offset(-0.8, MIT, 4.0), depth - 0.01, depth + t))
    parts.append(ext(rect(-w / 2 + 0.8, 0.0, w / 2 - 0.8, 0.8), depth - 0.01, depth + t * 0.6))
    pet, cen = _chrys((0.0, 0.8), rise * 0.62, n=11, half=True, disc=0.9, petal_w=0.6)
    tym = face.offset(-1.0, MIT, 4.0)
    parts.append(ext(pet ^ tym, depth - 0.01, depth + t * 0.5))
    parts.append(ext(cen ^ tym, depth - 0.01, depth + t * 0.8))
    return union(parts).transform(np.array([[1.0, 0, 0, 0], [0, 0, 1.0, 0], [0, 1.0, 0, 0]]))


CO.FRIEZE_EXTRA.update(chrysanthemums=frieze_chrysanthemums, peacocks=frieze_peacocks, lilies=frieze_lilies)
CO.COURSE_EXTRA.update(bamboo=course_bamboo, pearlribbon=course_pearlribbon)
TW.BRACKET_EXTRA.update(fiddlehead=bracket_fiddlehead)
TW.PIERCED = TW.PIERCED + ("fiddlehead",)
TW.FOUNDATION_EXTRA.update(panelplinth=foundation_panelplinth)
SH.CORNER_EXTRA.update(wyndham=corner_wyndham)
PW.POSTS.update(scamozzi=post_scamozzi)
PW.BALUSTERS.update(bottleblock=(baluster_bottleblock, 1.6))
PW.FRIEZES.update(ballspindle=frieze_ballspindle)
PW.SKIRTS.update(sunpanels=skirt_sunpanels)
FT.EDGE_EXTRA.update(ballfringe=edge_ballfringe)


# ================================================================== the Evangeline (house 92)
# Steamboat Gothic, 1858: a sugar planter's house raised on a stuccoed ground storey, wrapped on
# all four sides by a gallery whose paired decks read like a riverboat's: a lower arcade of
# stuccoed arches carrying a planked main gallery of slender Gothic colonnettes, lancet lace and
# onion balusters, its flat roof a promenade deck behind a Gothic railing. Above, a straight
# slated hip with Gothic wall dormers stops at a flat crested deck, and on the deck stands the
# pilot house: a glazed belvedere of lancet windows under its own bracketed cornice and a
# concave tent roof with a star finial. A double horseshoe stair climbs to the front door; two
# domed cypress cisterns on brick bases stand by the back corners. Peach stucco, celadon lap,
# ivory trim, deep teal accents and a pewter roof; the ornament is the Delta's (sugar cane,
# cotton bolls, stars) set in Gothic lancets, trefoils and quatrefoils.

def _lancet(u0, u1, vs, v0=0.0, r=None, seg=10):
    """A pointed (lancet) outline: straight jambs from v0 up to the springing vs, then two arcs
    of radius r (default the span: an equilateral arch) struck from the opposite springings,
    meeting in a point."""
    s = u1 - u0
    r = s if r is None else max(r, s / 2 + 1e-3)
    cx = u0 + r
    th = math.acos(max(-1.0, min(1.0, (s / 2 - r) / r)))
    left = [(cx + r * math.cos(t), vs + r * math.sin(t)) for t in np.linspace(math.pi, th, seg + 1)]
    right = [(u0 + u1 - x, y) for x, y in reversed(left[:-1])]
    return poly([(u0, v0)] + left + right + [(u1, v0)])


def _apex(s, r=None):
    """Height of a lancet's point over its springing, span s, radius r (default s)."""
    r = s if r is None else r
    return math.sqrt(max(0.0, r * r - (s / 2) ** 2))


def _star(c, ro, ri=None, n=5, rot=math.pi / 2):
    ri = ro * 0.45 if ri is None else ri
    pts = []
    for k in range(2 * n):
        r = ro if k % 2 == 0 else ri
        a = rot + math.pi * k / n
        pts.append((c[0] + r * math.cos(a), c[1] + r * math.sin(a)))
    return poly(pts)


def _trefoil(c, r, seg=14):
    d = r * 0.9
    return cs_union([circle((c[0] + d * math.cos(a), c[1] + d * math.sin(a)), r, seg)
                     for a in (math.pi / 2, math.pi / 2 + 2.094, math.pi / 2 - 2.094)] + [circle(c, r * 0.8, seg)])


def _quatrefoil(c, r, seg=14):
    d = r * 0.85
    return cs_union([circle((c[0] + dx * d, c[1] + dy * d), r, seg) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
                    + [circle(c, r, seg)])


def slate_swallowbands(k, j):
    """The Evangeline's slating: square slates, every seventh and eighth course swallow-tailed
    (a band of V-cut butts round the roof), the band's slates in the second course shifted."""
    return "swallow" if k % 8 in (5, 6) else "square"


# ------------------------------------------------------------------ wall skins, corners, foundation
def stucco_tabled(region, datum=0.0, tall=3.0, short=1.2, block=7.2, joint=0.5, d=0.32):
    """Stucco ruled as ashlar in tall and short courses in turn: the tall courses' blocks
    bevelled round every edge (V joints), the short courses plain bands between grooves (the
    Evangeline's raised ground storey). Every bevel is 45 degrees (it prints upright)."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    p = tall + short
    out = []
    k = math.floor((v0 - datum) / p) - 1
    while datum + k * p < v1 + p:
        v = datum + k * p
        a, b = v + joint / 2, v + tall - joint / 2
        if b > v0 - 1 and a < v1 + 1:
            u = u0 - block + (k % 2) * block / 2
            while u < u1 + block:
                out.append(chamfer_box(u + joint / 2, a, u + block - joint / 2, b, 0.0, d, c=0.28, bottom=d))
                u += block
            out.append(ext(rect(u0 - 1, v + tall + joint / 2, u1 + 1, v + p - joint / 2), 0.0, d * 0.55))
        k += 1
    return union(out) ^ M.extrude(region, d + 0.1)


def lap_twinbead(region, datum=0.0, pitch=2.0, d=0.34):
    """Lap boards 2 mm to the weather, each butt a short square step under a pair of small
    beads run along the board just above it (the Evangeline's main storey)."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    k0 = math.floor((v0 - datum) / pitch) - 1
    k1 = math.ceil((v1 - datum) / pitch) + 1
    pts = [(datum + k0 * pitch, 0.0)]
    for k in range(k0, k1):
        vk = datum + k * pitch
        pts += [(vk, d), (vk + 0.12, d + 0.1), (vk + 0.3, d - 0.02), (vk + 0.48, d + 0.06), (vk + 0.62, d - 0.06),
                (vk + pitch, 0.06)]
    pts.append((datum + k1 * pitch, 0.0))
    strip = M.extrude(poly(pts), (u1 - u0) + 2).transform(frame([u0 - 1, 0, 0], [0, 1, 0], [0, 0, 1], [1, 0, 0]))
    return strip ^ M.extrude(region, d + 0.3).translate([0, 0, -0.1])


def corner_evangeline(L, at_start, qa, qb, w=2.4, t=0.65):
    """The Evangeline's corner boards: a board on a plinth block, sunk with a long lancet-headed
    panel, a raised trefoil over the panel's point, and a gabled cap block (its gablet a 45
    degree prism, so it prints upright)."""
    def span(a, b):
        return (a, b) if at_start else (L - b, L - a)
    if qb - qa < 8.0:
        return M()
    a, b = span(0.0, w)
    parts = [box([a, qa, 0.0], [b, qb, t])]
    pa, pb = span(-0.2, w + 0.2)
    parts.append(chamfer_box(pa, qa, pb, qa + 2.0, 0.0, t + 0.3, c=0.2, bottom=t + 0.3))
    um = (a + b) / 2
    top = qb - 3.6
    pan = _lancet(um - 0.5, um + 0.5, top - 0.9, v0=qa + 2.8, r=1.0)
    out = union(parts) - ext(pan, t - 0.25, t + 1.0)
    out = out + ext(_trefoil((um, top + 0.6), 0.32), t - 0.01, t + 0.25)
    out = out + chamfer_box(pa, qb - 2.0, pb, qb, 0.0, t + 0.45, c=0.2, bottom=t + 0.45)
    return out


def foundation_plinthtorus(reg, seed=0):
    """A low stucco plinth: a chamfered base course, a sunk band, and a torus under a fillet
    at its head (the Evangeline)."""
    b = reg.bounds()
    h = b[3] - b[1]
    out = [M.extrude(reg, 0.25)]
    base = rect(b[0] - 1, b[1], b[2] + 1, b[1] + h * 0.45) ^ reg
    if not base.is_empty():
        bb = base.bounds()
        out.append(M.hull_points([(x, bb[1], 0.24) for x in (bb[0], bb[2])] + [(x, bb[1], 0.7) for x in (bb[0], bb[2])] +
                                 [(x, bb[3], 0.7) for x in (bb[0], bb[2])] + [(x, bb[3] + 0.45, 0.24) for x in (bb[0], bb[2])]))
    tor = rect(b[0] - 1, b[3] - 1.0, b[2] + 1, b[3]) ^ reg
    if not tor.is_empty():
        tb = tor.bounds()
        out.append(M.hull_points([(x, tb[1] - 0.35, 0.24) for x in (tb[0], tb[2])] + [(x, tb[1] + 0.15, 0.62) for x in (tb[0], tb[2])] +
                                 [(x, tb[3] - 0.2, 0.62) for x in (tb[0], tb[2])] + [(x, tb[3], 0.4) for x in (tb[0], tb[2])]))
    return union(out)


# ------------------------------------------------------------------ cornice ornaments
def course_starrow(L, h, b, pitch, margin, p):
    """A row of five-pointed steamboat stars on a fillet (the Evangeline's storey joint)."""
    pu = 2.4
    n = max(1, int((L - 0.6) / pu))
    u0 = (L - n * pu) / 2
    rod = rect(0.2, 0.25, L - 0.2, h - 0.25)
    ro = min(h * 0.5 - 0.05, 0.95)
    stars = cs_union([_star((u0 + pu * (k + 0.5), h / 2 - 0.05), ro) for k in range(n)]) ^ rect(0.2, 0.0, L - 0.2, h)
    return [_st(rod, b, 0.2), _st(stars, b + 0.2, 0.3)]


def course_trefoilrow(L, h, b, pitch, margin, p):
    """A row of raised trefoils, each on a short stalk, between beads (the Evangeline's eave)."""
    pu = 2.2
    n = max(1, int((L - 0.6) / pu))
    u0 = (L - n * pu) / 2
    rod = rect(0.2, 0.2, L - 0.2, h - 0.2)
    r = min(0.42, h * 0.2)
    tre = cs_union([_trefoil((u0 + pu * (k + 0.5), h * 0.56), r) for k in range(n)])
    beads = cs_union([circle((u0 + pu * k, h / 2), 0.32, 10) for k in range(n + 1)])
    return [_st(rod, b, 0.22), _st(tre ^ rod, b + 0.22, 0.3), _st(beads ^ rod, b + 0.22, 0.22)]


def frieze_sugarcane(L, h, b, pitch, margin, pair, half):
    """Sugar cane: in every bay two jointed canes crossed saltire-wise, a long leaf springing
    each way from their crossing; a rosette at every station between bays (the Evangeline's
    storey joint)."""
    v0, v1 = 0.8, h - 0.8
    vm = (v0 + v1) / 2
    out = []
    for uc, wd in CO._between(L, pitch, margin, pair, half):
        if wd < 3.6:
            continue
        hw = min(wd * 0.36, 3.6)
        a0, a1 = (uc - hw, v0 + 0.3), (uc + hw, v1 - 0.3)
        b0, b1 = (uc + hw, v0 + 0.3), (uc - hw, v1 - 0.3)
        canes = cs_union([stroke([a0, a1], 0.6), stroke([b0, b1], 0.6)])
        nodes = []
        for (p0, p1) in ((a0, a1), (b0, b1)):
            for t_ in (0.2, 0.8):
                nodes.append(circle((p0[0] + (p1[0] - p0[0]) * t_, p0[1] + (p1[1] - p0[1]) * t_), 0.42, 12))
        leaves = cs_union([_lens((uc + sg * hw * 0.55, vm + 0.35), min(2.8, hw * 1.1), 0.6, sg * 0.42) for sg in (-1, 1)])
        out.append(_st(_clip_v(canes, v0, v1), b, 0.32))
        out.append(_st(_clip_v(cs_union(nodes), v0, v1), b, 0.5))
        out.append(_st(_clip_v(leaves, v0, v1), b, 0.38))
    for u in CO._us(L, pitch, margin, 0.0):
        if 1.2 < u < L - 1.2:
            out.append(_st(_quatrefoil((u, vm), min(0.55, (v1 - v0) * 0.18)), b, 0.35))
            out.append(_st(circle((u, vm), 0.4, 12), b + 0.35, 0.2))
    return out, []


def frieze_cottonbolls(L, h, b, pitch, margin, pair, half):
    """Cotton: in every bay between the brackets an open boll, four locks round a heart on a
    calyx of three pointed bracts, on a stem with a leaf either side (the Evangeline's eave)."""
    v0, v1 = 0.8, h - 0.8
    hh = v1 - v0
    out = []
    for uc, wd in CO._between(L, pitch, margin, pair, half):
        if wd < 3.0:
            continue
        r = min(0.62, wd * 0.12, hh * 0.13)
        c = (uc, v0 + hh * 0.62)
        locks = cs_union([circle((c[0] + dx * r * 1.05, c[1] + dy * r * 1.05), r, 14) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))])
        bracts = cs_union([_lens((c[0] + 1.3 * r * math.sin(a), c[1] - 1.3 * r * math.cos(a)), 2.4 * r, 0.55, -math.pi / 2 + a)
                           for a in (-0.9, 0.0, 0.9)])
        stem = stroke([(uc, v0 + 0.2), (uc + 0.25, v0 + hh * 0.3), (uc, c[1] - 1.6 * r)], 0.5)
        leaves = cs_union([_lens((uc + sg * 0.85, v0 + hh * 0.28), min(2.0, wd * 0.3), 0.6, sg * 0.5) for sg in (-1, 1)])
        out.append(_st(_clip_v(stem + leaves, v0, v1), b, 0.32))
        out.append(_st(_clip_v(bracts, v0, v1), b, 0.38))
        out.append(_st(_clip_v(locks, v0, v1), b, 0.55))
        out.append(_st(circle(c, r * 0.55, 12), b + 0.55, 0.2))
    return out, []


def frieze_lancetfoils(L, h, b, pitch, margin, pair, half):
    """A blind Gothic arcade: in every bay a lancet outlined by a raised rim, a quatrefoil boss
    in its head (the Evangeline's belvedere)."""
    v0, v1 = 0.7, h - 0.7
    out = []
    for uc, wd in CO._between(L, pitch, margin, pair, half):
        s = min(wd * 0.7, 3.6)
        if s < 2.2:
            continue
        ap = _apex(s)
        vs = v1 - ap
        if vs < v0 + 1.0:
            continue
        outer = _lancet(uc - s / 2, uc + s / 2, vs, v0=v0)
        rim = outer - outer.offset(-0.5, MIT, 4.0)
        out.append(_st(rim, b, 0.35))
        qr = min(0.42, s * 0.14)
        out.append(_st(_quatrefoil((uc, vs + ap * 0.3), qr), b, 0.4))
    return out, []


def bracket_trefoilknee(h, d, t):
    """A Gothic knee bracket: a leg on the wall, an arm under the soffit, a hollow-curved brace
    between them and a sunk trefoil in the spandrel (side profile, top at v = 0)."""
    leg, arm = 0.9, 0.9
    pts = [(0.0, 0.0), (d, 0.0), (d, -arm)]
    cx, cy = d, -h
    rr = min(d - leg, h - arm)
    for t_ in np.linspace(0.0, 1.0, 10):
        a = math.pi / 2 + t_ * math.pi / 2
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a) + (h - arm - rr)))
    pts += [(leg, -h), (0.0, -h)]
    prof = poly(pts)
    prof = prof + circle((d - 0.35, -arm - 0.15), 0.42, 12)
    tc = (leg + (d - leg) * 0.32, -arm - (h - arm) * 0.32)
    return prof - _trefoil(tc, min(0.34, (d - leg) * 0.12))


def quatrefoilchain(L, h):
    """A crest course: a chain of quatrefoils linked by a bar, on a fillet (the Evangeline's
    roof deck and belvedere)."""
    pu = 2.6
    n = max(1, int((L - 0.6) / pu))
    u0 = (L - n * pu) / 2
    vm = h / 2 + 0.1
    r = min(0.48, h * 0.18)
    quat = cs_union([_quatrefoil((u0 + pu * (k + 0.5), vm), r) for k in range(n)])
    bar = rect(0.2, vm - 0.25, L - 0.2, vm + 0.25)
    base = rect(0.2, 0.05, L - 0.2, 0.35)
    return [cs_union([quat, bar, base]) ^ rect(0.2, 0.05, L - 0.2, h - 0.05)]


def fence_evangeline(L, h):
    """Evangeline cresting (drawn at half size for SE.printable): a bottom rail, uprights
    rising to five-pointed stars, between every two a lancet arch springing from a middle rail,
    and under the rail a lozenge."""
    pitch = 3.4
    n = max(1, int(round(L / pitch)))
    p = L / n
    rail = h * 0.32
    cells = [rect(0.0, 0.0, L, 0.6), rect(0.0, rail, L, rail + 0.45)]
    ro = min(0.95, p * 0.28)
    for j in range(n + 1):
        u = min(max(p * j, 0.25), L - 0.25)
        cells.append(rect(u - 0.25, 0.0, u + 0.25, h - ro))
        cells.append(_star((u, h - ro + 0.1), ro, ro * 0.5))
        if j < n:
            m = p * j + p / 2
            s = p - 0.5
            ap = min(_apex(s, s * 0.8), h - ro * 2 - rail - 0.6)
            arc = _lancet(m - s / 2, m + s / 2, rail + 0.45, v0=rail, r=s * 0.8, seg=12)
            cells.append(arc - arc.offset(-0.45, MIT, 4.0) ^ rect(-1e3, rail, 1e3, rail + 0.45 + ap + 0.5))
            lz = poly([(m, 0.55), (m + 0.6, (rail + 0.6) / 2), (m, rail + 0.05), (m - 0.6, (rail + 0.6) / 2)])
            cells.append(lz)
    return cs_union(cells) ^ rect(0.0, 0.0, L, h + 1.0)


def fence_evangeline_promenade(L, h):
    """The promenade deck's railing seen face on (printed flat, full size): a plinth rail, a
    hand rail, square newels with pointed caps every 14 mm or so, and between them an arcade of
    lancets on slender bars."""
    nseg = max(1, int(round(L / 14.0)))
    seg = L / nseg
    cells = [rect(0.0, 0.0, L, 0.9), rect(0.0, h - 1.0, L, h)]
    for j in range(nseg + 1):
        u = min(max(seg * j, 0.85), L - 0.85)
        cells.append(rect(u - 0.85, 0.0, u + 0.85, h + 0.3))
        cells.append(poly([(u - 0.85, h + 0.29), (u + 0.85, h + 0.29), (u, h + 1.4)]))
        if j < nseg:
            a, b = u + 0.85, min(max(seg * (j + 1), 0.85), L - 0.85) - 0.85
            field = rect(a, 0.85, b, h - 0.95)
            nb = max(1, int(round((b - a) / 2.2)))
            pw = (b - a) / nb
            holes = []
            for k in range(nb):
                x0, x1 = a + pw * k + 0.32, a + pw * (k + 1) - 0.32
                if x1 - x0 < 1.2:
                    continue
                ap = _apex(x1 - x0)
                holes.append(_lancet(x0, x1, h - 1.25 - ap, v0=0.9))
            cells.append(field - cs_union(holes) if holes else field)
    return cs_union(cells) ^ rect(0.0, 0.0, L, h + 1.6)


def finial_evangeline(h=14.0):
    """The belvedere's finial: a turned base, an onion bulb with a ring under it, and a spike
    carrying a ball (a riverboat's flagstaff knob)."""
    prof = [(0.0, 0.0), (1.6, 0.0), (1.6, 0.6), (1.1, 1.1), (0.7, 1.5), (0.7, 2.1), (1.05, 2.4), (1.05, 2.7), (0.8, 2.9),
            (1.25, 3.4), (1.5, 4.0), (1.35, 4.7), (0.9, 5.3), (0.55, 5.8), (0.45, 6.2), (0.0, 6.2)]
    body = PW._revolve(prof, 28)
    body = body + M.cylinder(h - 6.1, 0.5, 0.4, 14).translate([0, 0, 6.1])
    body = body + _ball(0.85, 6.1 + (h - 6.1) * 0.55, neck=0.45)
    return body


# ------------------------------------------------------------------ windows and doors
def _vous(w, h, rise, A, n=7, long_=2.2, short=1.6, gap=0.3):
    """Stucco voussoirs round a segmental head, long and short in turn, as one CrossSection
    (and the keystone's outline)."""
    half = w / 2
    spring = h - rise
    R0 = (half * half + rise * rise) / (2 * rise)
    cy = spring + rise - R0
    a_lim = math.asin(min(1.0, half / R0)) + 0.06
    blocks = []
    for k in range(n):
        a0 = -a_lim + 2 * a_lim * k / n + (gap / 2) / (R0 + A)
        a1 = -a_lim + 2 * a_lim * (k + 1) / n - (gap / 2) / (R0 + A)
        L = long_ if k % 2 == 0 else short
        r0, r1 = R0 + A - 0.05, R0 + A + L
        pts = [(r0 * math.sin(a), cy + r0 * math.cos(a)) for a in np.linspace(a0, a1, 5)]
        pts += [(r1 * math.sin(a), cy + r1 * math.cos(a)) for a in np.linspace(a1, a0, 5)]
        if k != n // 2:
            blocks.append(poly(pts))
    kw = 2 * a_lim / n * (R0 + A)
    key = poly([(-kw / 2, cy + R0 + A - 0.05), (kw / 2, cy + R0 + A - 0.05), (kw / 2 + 0.4, cy + R0 + A + long_ + 0.6),
                (-kw / 2 - 0.4, cy + R0 + A + long_ + 0.6)])
    return cs_union(blocks), key, cy + R0 + A + long_ + 0.6


def window_evangeline_ground(w=8.0, h=14.0, A=0.8, rise=1.6):
    """The ground storey's window: a six-over-six sash under a segmental head, an architrave,
    stucco voussoirs long and short in turn round a projecting keystone, and a sill on two
    blocks."""
    op = O.opening_cs(w, h, rise)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    sash = O.window_insert(w, h, rise, lites=(3, 3), rows=(2, 2), bare=True)["insert"]
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             MD.band(op.offset(A, RND), A, MD.CASING, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op)]
    vs, key, vt = _vous(w, h, rise, A)
    parts.append(ext(vs, 0.0, 0.7))
    parts.append(ext(key, 0.0, 1.1))
    sw = w / 2 + A + 0.5
    parts.append(MD.run(-sw, sw, 0.0, MD.SILL, 1.0, up=False))
    for sg in (-1, 1):
        parts.append(chamfer_box(sg * (w / 2) - 0.7, -1.8, sg * (w / 2) + 0.7, -0.8, 0.0, 0.9, c=0.25))
    return O._one_piece([sash], parts, op, plug_cs, O.PLUG, vt + 0.2, -1.8)


def _hood_lancet(op, A, vs, w, stops=True, crockets=0, finial=True):
    """A hood mould round a lancet (outline ``op`` widened by A): a moulded label stopping at
    the springing on carved stops, with ``crockets`` knobs up each side and a trefoil finial."""
    out = [MD.band(op.offset(A + 1.0, MIT, 4.0), 1.0, MD.CROWN, clip=rect(-50, vs - 0.01, 50, 100))]
    hu = w / 2 + A + 0.5
    if stops:
        for sg in (-1, 1):
            out.append(chamfer_box(sg * hu - 0.7, vs - 1.6, sg * hu + 0.7, vs, 0.0, 1.0, c=0.2))
            out.append(ext(circle((sg * hu, vs - 0.8), 0.45, 12), 0.99, 1.35))
    top = op.offset(A + 1.0, MIT, 4.0).bounds()[3]
    if crockets:
        outer = op.offset(A + 1.3, MIT, 4.0)
        ob = outer.bounds()
        for k in range(crockets):
            t_ = (k + 1) / (crockets + 1)
            v = vs + (ob[3] - vs) * t_ * 0.92
            row = outer ^ rect(-50, v - 0.05, 50, v + 0.05)
            if row.is_empty():
                continue
            rb = row.bounds()
            for x in (rb[0], rb[2]):
                out.append(ext(circle((x, v), 0.45, 12), 0.0, 1.1))
    if finial:
        out.append(ext(cs_union([rect(-0.3, top - 0.6, 0.3, top + 0.8), _trefoil((0.0, top + 1.1), 0.42)]), 0.0, 1.1))
        top += 1.6
    return out, top


def window_evangeline_main(w=9.6, h=30.0, A=1.0):
    """The main storey's French window, floor to near ceiling (it opens onto the gallery): two
    casement leaves of three lights over a raised panel, under a lancet head filled with bar
    tracery (two sub-lancets and an oculus); a moulded architrave, a crocketed hood mould on
    carved stops with a trefoil finial; a threshold."""
    ap = _apex(w, w * 0.9)
    vs = h - ap
    op = _lancet(-w / 2, w / 2, vs, r=w * 0.9, seg=14)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    inner = plug_cs.offset(-0.6, MIT, 4.0)
    ib = inner.bounds()
    pan_top = 5.0
    body = [ext(plug_cs, -pl, -0.6), _panel(rect(ib[0] + 0.5, 1.0, -0.9, pan_top - 0.8)),
            _panel(rect(0.9, 1.0, ib[2] - 0.5, pan_top - 0.8))]
    g = inner ^ rect(-w, pan_top, w, h + 5)
    bars = [rect(-0.4, pan_top - 1, 0.4, vs + 0.2)]
    for v in np.linspace(pan_top, vs, 4)[1:-1]:
        bars.append(rect(-w, v - RIB / 2, w, v + RIB / 2))
    bars.append(rect(-w, vs - 0.3, w, vs + 0.3))
    sub = w / 2 - 0.6
    for sg in (-1, 1):
        x0, x1 = sorted((sg * 0.0, sg * (w / 2 - 0.6)))
        sl = _lancet(x0, x1, vs, v0=vs - 1.0, r=sub * 0.9, seg=10)
        bars.append(sl - sl.offset(-RIB, MIT, 4.0))
    oc = (0.0, vs + _apex(sub, sub * 0.9) + (ap - _apex(sub, sub * 0.9)) * 0.45)
    ro = min(1.2, (ap - _apex(sub, sub * 0.9)) * 0.42)
    if ro > 0.7:
        bars.append(circle(oc, ro, 24) - circle(oc, ro - RIB, 24))
    sash = _glazed(body, g, pl, cs_union(bars), plug_cs)
    sash.append(ext(rect(-w, pan_top - 0.8, w, pan_top + 0.01) ^ plug_cs, -pl, -0.6))
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             MD.band(op.offset(A, MIT, 4.0), A, MD.ARCHITRAVE, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op)]
    hood, top = _hood_lancet(op, A, vs, w, crockets=3)
    parts += hood
    parts.append(ext(rect(-w / 2 - A - 0.4, -0.6, w / 2 + A + 0.4, 0.01), 0.0, 1.0))
    return O._one_piece(sash, parts, op, plug_cs, pl, top + 0.2, -0.6)


def window_evangeline_belv(w=6.6, h=15.0, A=0.8):
    """The belvedere's window: a lancet of two lights divided by a mullion that forks into Y
    tracery in the head, an architrave, a hood mould on stops and a sill."""
    ap = _apex(w)
    vs = h - ap
    op = _lancet(-w / 2, w / 2, vs, seg=14)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    inner = plug_cs.offset(-0.6, MIT, 4.0)
    body = [ext(plug_cs, -pl, -0.6)]
    mid = vs * 0.5
    bars = [rect(-RIB / 2, -1.0, RIB / 2, vs + 0.4), rect(-w, mid - 0.35, w, mid + 0.35)]
    ycs = cs_union([stroke([(0.0, vs + 0.2), (sg * w * 0.18, vs + ap * 0.45), (sg * w * 0.22, vs + ap * 0.9)], RIB)
                    for sg in (-1, 1)])
    bars.append(ycs)
    sash = _glazed(body, inner, pl, cs_union(bars) ^ inner.offset(0.4, MIT, 4.0), plug_cs)
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             MD.band(op.offset(A, MIT, 4.0), A, MD.CASING, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op)]
    hood, top = _hood_lancet(op, A, vs, w, crockets=0, finial=False)
    parts += hood
    sw = w / 2 + A + 0.5
    parts.append(MD.run(-sw, sw, 0.0, MD.SILL, 1.0, up=False))
    return O._one_piece(sash, parts, op, plug_cs, pl, top + 0.2, -1.0)


def _ogee(x0, v0, H, n=16):
    """The centre line of an ogee arch from (+-x0, v0) to its point at (0, v0 + H): a convex
    swell at the haunches reversing into a concave rise to the point."""
    P0, P1, P2, P3 = np.array([x0, v0]), np.array([x0, v0 + 0.62 * H]), np.array([0.0, v0 + 0.42 * H]), np.array([0.0, v0 + H])
    pts = []
    for t in np.linspace(0.0, 1.0, n + 1):
        p = (1 - t) ** 3 * P0 + 3 * (1 - t) ** 2 * t * P1 + 3 * (1 - t) * t * t * P2 + t ** 3 * P3
        pts.append((float(p[0]), float(p[1])))
    return pts


def door_evangeline(w=15.0, h=28.0, A=1.2, hx=4.0):
    """The Evangeline's entrance: a pair of leaves, each a raised panel under a glazed lancet
    light, under a lancet head of bar tracery (two sub-lancets and a quatrefoil); an architrave
    between clustered colonnettes on blocks, and over all an ogee hood rising in a crocketed
    swell to a tall trefoil finial, a quatrefoil boss in its tympanum; a threshold."""
    ap = _apex(w, w * 0.75)
    vs = h - ap
    op = _lancet(-w / 2, w / 2, vs, r=w * 0.75, seg=16)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    inner = plug_cs.offset(-0.5, MIT, 4.0)
    ib = inner.bounds()
    mid = 0.7
    dh = vs - 0.4
    lw = (ib[2] - ib[0] - mid) / 2
    body, lights = [ext(plug_cs, -pl, -1.0)], []
    ul = ib[0]
    for i in range(2):
        body.append(ext(rect(ul, 0.5, ul + lw, dh), -pl, -0.8))
        body.append(_panel(rect(ul + 0.8, 1.2, ul + lw - 0.8, dh * 0.42)))
        s = lw - 1.8
        la = _apex(s)
        lights.append(_lancet(ul + 0.9, ul + lw - 0.9, dh - 0.9 - la, v0=dh * 0.42 + 1.0))
        ul += lw + mid
    head = inner ^ rect(-w, vs + 0.4, w, h + 5)
    bars = [rect(-w, vs - 0.1, w, vs + 0.5)]
    sub = w / 2 - 0.8
    for sg in (-1, 1):
        x0, x1 = sorted((0.0, sg * (w / 2 - 0.8)))
        sl = _lancet(x0, x1, vs + 0.4, v0=vs, r=sub * 0.8, seg=10)
        bars.append(sl - sl.offset(-RIB, MIT, 4.0))
    sap = _apex(sub, sub * 0.8)
    qc = (0.0, vs + 0.4 + sap + (ap - 0.4 - sap) * 0.42)
    qr = min(0.9, (ap - sap) * 0.2)
    if qr > 0.5:
        q = _quatrefoil(qc, qr, 18)
        bars.append(q - q.offset(-RIB, RND))
    sash = _glazed(body, cs_union(lights) + head, pl, cs_union(bars), plug_cs)
    sash.append(ext(rect(-w, dh - 0.01, w, vs + 0.5) ^ plug_cs, -pl, -0.5))
    sash.append(ext(rect(-mid / 2, 0.4, mid / 2, vs) ^ plug_cs, -pl, -0.6))
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             MD.band(op.offset(A, MIT, 4.0), A, MD.ARCHITRAVE, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op)]
    # clustered colonnettes: three half-round shafts on a block, ringed capitals
    xc = w / 2 + A + 1.2
    vt = vs + 0.6
    for sg in (-1, 1):
        x = sg * xc
        parts.append(chamfer_box(x - 1.4, -0.2, x + 1.4, 2.2, 0.0, 1.5, c=0.25))
        parts.append(chamfer_box(x - 1.5, vt - 0.01, x + 1.5, vt + 1.4, 0.0, 1.6, c=0.25))
        for dx, rc in ((-0.75, 0.55), (0.0, 0.7), (0.75, 0.55)):
            prof = [(0.0, 0.0), (rc, 0.0)]
            z = 3.6
            prof += [(rc, z), (rc + 0.18, z + 0.2), (rc + 0.18, z + 0.4), (rc, z + 0.6)]
            z = (vt - 2.2) * 0.55
            prof += [(rc, z), (rc + 0.18, z + 0.2), (rc + 0.18, z + 0.4), (rc, z + 0.6)]
            prof += [(rc, vt - 2.2), (0.0, vt - 2.2)]
            col = PW._revolve(prof, 18).rotate([-90, 0, 0]).translate([x + dx, 2.19, 0.0]) ^ box([x - 3, 0.0, 0.0], [x + 3, vt, 5.0])
            parts.append(col)
    # the ogee hood: a band along an ogee from over the capitals to a point, crockets, finial
    H = ap + hx
    cl = _ogee(xc, vt + 1.4, H)
    band = cs_union([stroke(cl, 1.2), stroke([(-x, v) for x, v in cl], 1.2)])
    parts.append(ext(band, 0.0, 1.3))
    for k in range(3, len(cl) - 2, 3):
        x, v = cl[k]
        for sg in (-1, 1):
            parts.append(ext(circle((sg * (x + 0.75), v + 0.35), 0.45, 12), 0.0, 1.2))
    vtop = vt + 1.4 + H
    parts.append(ext(cs_union([rect(-0.35, vtop - 0.8, 0.35, vtop + 1.2), _trefoil((0.0, vtop + 1.6), 0.5)]), 0.0, 1.3))
    tym = poly(cl + [(-x, v) for x, v in reversed(cl)]) - op.offset(A + 0.2, MIT, 4.0)
    tb = tym.bounds() if not tym.is_empty() else None
    if tb is not None:
        qc2 = (0.0, (op.bounds()[3] + A + vtop) / 2 - 0.4)
        parts.append(ext(_quatrefoil(qc2, 0.62, 16) ^ tym, 0.0, 0.9))
        parts.append(ext(tym, 0.0, 0.3))
    parts.append(ext(rect(-xc - 1.5, -0.6, xc + 1.5, 0.01), 0.0, 1.2))
    return O._one_piece(sash, parts, op, plug_cs, pl, vtop + 2.3, -0.6)


def door_evangeline_back(w=10.0, h=29.0, A=1.0):
    """The back door to the gallery: one leaf of two raised panels under a glazed lancet
    light, a lancet transom with a Y bar, an architrave, and a hood mould on stops with a
    trefoil finial; a threshold."""
    ap = _apex(w, w * 0.85)
    vs = h - ap
    op = _lancet(-w / 2, w / 2, vs, r=w * 0.85, seg=14)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    inner = plug_cs.offset(-0.5, MIT, 4.0)
    ib = inner.bounds()
    dh = vs - 0.4
    u0, u1 = ib[0], ib[2]
    gp = (dh * 0.5 - 2.0) / 2
    body = [ext(plug_cs, -pl, -1.0), ext(rect(u0, 0.5, u1, dh), -pl, -0.8),
            _panel(rect(u0 + 0.8, 1.2, u1 - 0.8, 1.2 + gp - 0.2)), _panel(rect(u0 + 0.8, 1.2 + gp + 0.2, u1 - 0.8, dh * 0.5 - 0.8))]
    s = (u1 - u0) - 1.8
    light = _lancet(u0 + 0.9, u1 - 0.9, dh - 0.9 - _apex(s), v0=dh * 0.5)
    head = inner ^ rect(-w, vs + 0.4, w, h + 5)
    ycs = cs_union([stroke([(0.0, vs + 0.3), (sg * w * 0.16, vs + ap * 0.45), (sg * w * 0.2, vs + ap)], RIB) for sg in (-1, 1)]
                   + [rect(-RIB / 2, vs, RIB / 2, vs + 0.6)])
    sash = _glazed(body, light + head, pl, ycs ^ head.offset(0.2, MIT, 4.0), plug_cs)
    sash.append(ext(rect(-w, dh - 0.01, w, vs + 0.42) ^ plug_cs, -pl, -0.5))
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             MD.band(op.offset(A, MIT, 4.0), A, MD.ARCHITRAVE, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op)]
    hood, top = _hood_lancet(op, A, vs, w, crockets=0)
    parts += hood
    parts.append(ext(rect(-w / 2 - A - 0.4, -0.6, w / 2 + A + 0.4, 0.01), 0.0, 1.0))
    return O._one_piece(sash, parts, op, plug_cs, pl, top + 0.2, -0.6)


def door_evangeline_ground(w=9.0, h=18.0, A=0.8, rise=2.0):
    """The ground storey's door under the gallery: a pair of batten-and-panel leaves under a
    segmental fanlight of radiating bars, a casing, voussoirs and a keystone."""
    op = O.opening_cs(w, h, rise)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    spring = h - rise
    inner = plug_cs.offset(-0.5, MIT, 4.0)
    ib = inner.bounds()
    dh = spring - 1.6
    body = [ext(plug_cs, -pl, -1.0), ext(rect(ib[0], 0.5, ib[2], dh), -pl, -0.8)]
    for x0, x1 in ((ib[0] + 0.7, -0.6), (0.6, ib[2] - 0.7)):
        body.append(_panel(rect(x0, 1.2, x1, dh * 0.45)))
        body.append(_panel(rect(x0, dh * 0.45 + 0.8, x1, dh - 0.8)))
    fan = inner ^ rect(-w, dh + 0.5, w, h + 2)
    fc = (0.0, dh + 0.5)
    rays = cs_union([stroke([fc, (fc[0] + w * math.cos(a), fc[1] + w * math.sin(a))], RIB) for a in np.linspace(0.6, math.pi - 0.6, 3)])
    sash = _glazed(body, fan, pl, rays, plug_cs)
    sash.append(ext(rect(-w, dh - 0.01, w, dh + 0.52) ^ plug_cs, -pl, -0.5))
    sash.append(ext(rect(-0.3, 0.4, 0.3, dh) ^ plug_cs, -pl, -0.6))
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             MD.band(op.offset(A, RND), A, MD.CASING, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op)]
    vs, key, vt = _vous(w, h, rise, A, n=9)
    parts.append(ext(vs, 0.0, 0.7))
    parts.append(ext(key, 0.0, 1.1))
    parts.append(ext(rect(-w / 2 - A - 0.3, -0.6, w / 2 + A + 0.3, 0.01), 0.0, 1.0))
    return O._one_piece(sash, parts, op, plug_cs, pl, vt + 0.2, -0.6)


def addin_evangeline(w=5.2, h=9.0, A=0.8):
    """A Gothic wall dormer for the hip (an add-in): a lancet light of two panes, its frame a
    steep gablet whose bargeboard is cut in a row of trefoil-headed notches, tied solid to a
    pendant and a fleur finial at the peak; a sill. The plug's roof is the gablet."""
    ap = _apex(w)
    vs = h - ap
    op = _lancet(-w / 2, w / 2, vs, seg=12)
    bars = cs_union([rect(-RIB / 2, -1.0, RIB / 2, vs + 0.3), rect(-w, vs * 0.5 - RIB / 2, w, vs * 0.5 + RIB / 2)])
    half = w / 2 + A + 0.6
    pk = vs + half * 1.25 + 0.6                     # the gablet's peak: a steep 51 degree gable
    gab = poly([(-half - 0.6, vs - 0.6), (-half, vs - 0.6), (-half, -0.2), (half, -0.2), (half, vs - 0.6),
                (half + 0.6, vs - 0.6), (0.0, pk + 0.6)])
    face = gab.offset(-0.01, MIT, 4.0)
    barge = gab - gab.offset(-1.1, MIT, 4.0) ^ rect(-50, vs - 0.6, 50, 100)
    notch = []
    for t_ in (0.3, 0.55, 0.8):
        for sg in (-1, 1):
            x = sg * (half + 0.6) * (1 - t_)
            v = vs - 0.6 + (pk + 0.6 - vs + 0.6) * t_ - 0.9
            notch.append(circle((x, v), 0.3, 10))
    barge = barge - cs_union(notch)
    parts = [ext(face - op, 0.0, 0.6),
             MD.band(op.offset(A, MIT, 4.0), A, MD.CASING, clip=rect(-20, 0.0, 20, 40) - op),
             ext(barge, 0.0, 1.1)]
    parts.append(ext(cs_union([rect(-0.35, pk - 2.0, 0.35, pk + 1.4), _trefoil((0.0, pk + 1.7), 0.45)]), 0.0, 1.1))
    sw = half - 0.2
    parts.append(MD.run(-sw, sw, 0.0, MD.SILL, 1.0, up=False))
    parts = [p - ext(op, -1.0, 5.0) for p in parts]
    outline = gab.offset(-0.4, MIT, 4.0) ^ rect(-50, 0.2, 50, 100)
    return dict(light=op, bars=bars, frame=parts, outline=outline, top=pk + 2.3, bottom=-1.0)


# ------------------------------------------------------------------ gallery parts
def post_crocketcap(h, collar=None, abacus=3.2, slot=(1.2, 1.0)):
    """A Gothic colonnette: an octagonal plinth, a moulded base, a slender shaft girdled by two
    shaft rings, a bell capital with a crocket leaf curling out under each corner of the
    abacus (a flat-topped plate, so it stands on the abacus when the gallery top prints upside
    down) (the Evangeline)."""
    z1 = h - 3.2
    r = 0.82
    za, zb = z1 * 0.36, z1 * 0.68
    prof = [(0.0, 1.19), (1.3, 1.19), (1.3, 1.45), (1.05, 1.75), (1.18, 1.95), (0.95, 2.25), (r, 2.5),
            (r, za), (1.02, za + 0.2), (1.02, za + 0.6), (r, za + 0.8), (r, zb), (1.02, zb + 0.2), (1.02, zb + 0.6), (r, zb + 0.8),
            (r, z1), (1.0, z1 + 0.2), (1.0, z1 + 0.45), (0.9, z1 + 0.6), (1.35, z1 + 1.05)]
    body = PW._revolve(prof, 28)
    body = body + M.extrude(circle((0.0, 0.0), 1.62, 8).rotate(22.5), 1.2)
    body = body + PW._top(h, abacus / 2, z1 + 1.05, 1.35, slot, seg=28)
    zt = z1 + 1.05 + max(0.2, abacus / 2 * math.sqrt(2) - 1.35)
    sq = abacus / 2
    leaf = poly([(-1.0, 0.0), (0.0, 0.0), (0.62, -0.62), (0.66, -1.0), (0.4, -1.2), (0.05, -1.0), (-1.0, -1.7)])
    for sx in (-1, 1):
        for sy in (-1, 1):
            d = np.array([sx, sy]) / math.sqrt(2)
            c = d * sq * math.sqrt(2) * 0.92
            plate = M.extrude(leaf, 0.5).translate([0, 0, -0.25])
            A = np.array([[d[0], 0.0, -d[1], c[0]], [d[1], 0.0, d[0], c[1]], [0.0, 1.0, 0.0, zt]])
            body = body + plate.transform(A)
    return body


def baluster_onionbulb(h, seg=18):
    """An onion baluster: a ring on a square foot, a slender stem swelling into an onion bulb
    that draws to a point, a long neck, and a square top block (the Evangeline)."""
    prof = [(0.0, 0.8), (0.32, 0.8), (0.32, 1.0), (0.42, 1.2), (0.26, 1.45), (0.24, h * 0.28), (0.46, h * 0.38),
            (0.52, h * 0.45), (0.38, h * 0.55), (0.22, h * 0.64), (0.22, h - 1.3), (0.34, h - 1.1), (0.34, h - 0.8)]
    body = PW._revolve(prof, seg)
    return body + box([-0.55, -0.55, 0.0], [0.55, 0.55, 0.81]) + box([-0.55, -0.55, h - 0.81], [0.55, 0.55, h])


def frieze_lancetarcade(u0, u1, v_bot, v_top):
    """A gallery frieze: a beam over a run of lancet arches on slender piers, a turned drop
    under every pier, and a solid spandrel with a pierced trefoil at each post (the
    Evangeline)."""
    vb = v_top - 4.6
    L = u1 - u0
    cells = [rect(u0, v_top - 0.9, u1, v_top + 0.05)]
    a, b = u0 + 3.0, u1 - 3.0
    n = max(1, int(round((b - a) / 2.4)))
    pw = (b - a) / n
    field = rect(a - 0.3, vb, b + 0.3, v_top - 0.85)
    holes = []
    for k in range(n):
        x0, x1 = a + pw * k + 0.3, a + pw * (k + 1) - 0.3
        holes.append(_lancet(x0, x1, v_top - 1.2 - _apex(x1 - x0), v0=vb - 1.0))
    cells.append(field - cs_union(holes))
    for k in range(n + 1):
        x = a + pw * k
        cells.append(rect(x - 0.3, vb - 0.6, x + 0.3, vb + 0.1))
        cells.append(circle((x, vb - 0.85), 0.42, 12))
    for x0, sg in ((u0, 1), (u1, -1)):
        q = poly([(x0, v_top - 0.85), (x0 + sg * 3.4, v_top - 0.85), (x0, v_top - 4.6)])
        cells.append(q - _trefoil((x0 + sg * 1.1, v_top - 2.0), 0.34))
    return cs_union(cells)


def edge_lancetfringe(L, z0, zc):
    """Gallery fascia (the Evangeline): a valance cut along its foot in a row of small
    lancets, a bead hanging under every point between them."""
    band = rect(0.3, zc - 1.8, L - 0.3, zc)
    pu = 1.9
    n = max(1, int((L - 1.0) / pu))
    u0 = (L - n * pu) / 2
    holes = cs_union([_lancet(u0 + pu * k + 0.35, u0 + pu * (k + 1) - 0.35, zc - 1.0 - _apex(1.2), v0=zc - 2.2, seg=6)
                      for k in range(n)])
    beads = cs_union([circle((u0 + pu * k, zc - 2.05), 0.36, 10) for k in range(n + 1)]) ^ rect(0.3, -1e3, L - 0.3, 1e3)
    return cs_union([band - holes, beads]), 0.6


def arcade_evangeline(L, piers, H, t=3.0, pw=4.2, rise=3.0, pier_side=None):
    """The lower gallery's arcade along one side, in a run's frame (u along it, v up from the
    ground, w out: the face at w = 0, the back at w = -t): square stucco piers at ``piers``,
    segmental arches between them with an archivolt and keystone, impost bands, plinths. It
    is part of the gallery deck, printed upside down, so every relief is stepped from the top."""
    from .secondempire import _st_down
    wall = rect(0.0, 0.0, L, H)
    us = sorted(piers)
    holes, rel = [], []
    spring = H - 3.4 - rise
    for a, b in zip(us[:-1], us[1:]):
        x0, x1 = a + pw / 2, b - pw / 2
        if x1 - x0 < 3.0:
            continue
        holes.append(arch_cs(x0, x1, -1.0, spring, rise=min(rise, (x1 - x0) / 2), seg=24))
    if not holes:
        return ext(wall, -t, 0.0)
    out = [ext(wall - cs_union(holes), -t, 0.0)]
    for hcs in holes:
        rel.append(hcs.offset(0.9, MIT, 4.0) - hcs.offset(0.0, MIT, 4.0) ^ rect(-1e3, spring - 0.6, 1e3, 1e3))
        hb = hcs.bounds()
        xm = (hb[0] + hb[2]) / 2
        rel.append(poly([(xm - 0.7, hb[3] - 0.1), (xm + 0.7, hb[3] - 0.1), (xm + 1.0, hb[3] + 1.6), (xm - 1.0, hb[3] + 1.6)]))
    for u in us:
        rel.append(rect(u - pw / 2 - 0.4, spring - 1.2, u + pw / 2 + 0.4, spring) ^ wall)
        rel.append(rect(u - pw / 2 - 0.3, 0.0, u + pw / 2 + 0.3, 1.6) ^ wall)
    rel.append(rect(0.0, H - 2.2, L, H - 0.8))
    relief = cs_union(rel) ^ wall
    out.append(_st_down(relief, H, 0.0, 0.4))
    return union(out)


def stair_horseshoe(H, n=13, fw=7.0, tread=2.6, land=(16.0, 8.0), cheek=1.6, wall_t=2.0):
    """A double horseshoe stair: a landing at the gallery floor (``land`` = width, depth) with
    two flights falling away from it to left and right, parallel to the house, each between
    stucco cheek walls with a sloping coping, a pier with a ball at each foot. Local frame: u
    along the house (0 at the landing's middle), v up from the ground, the landing's back at
    w = 0 and the stair coming forward to w = depth. One part, printed upright: every step and
    the coping stand on the solid below."""
    LW, LD = land
    rise = H / n
    run = (n - 1) * tread
    depth = max(LD, fw + cheek)
    parts = [box([-LW / 2, 0.0, 0.0], [LW / 2, H, LD])]
    # the landing's parapet across the front with an opening for the house door behind it
    parts.append(box([-LW / 2, H - 0.01, LD - cheek], [LW / 2, H + 5.2, LD]))
    for sg in (-1, 1):
        for k in range(n - 1):
            x0 = sg * (LW / 2 + k * tread)
            x1 = sg * (LW / 2 + (k + 1) * tread)
            top = H - rise * (k + 1)
            parts.append(box([min(x0, x1) - (0.01 if sg < 0 else 0), 0.0, LD - fw - cheek],
                             [max(x0, x1) + (0.01 if sg > 0 else 0), top, LD - cheek + 0.01]))
        # the outer cheek wall (front), its coping sloping with the flight, a pier at its foot
        xa, xb = sg * LW / 2, sg * (LW / 2 + run)
        pts = [(xa, 0.0), (xb, 0.0), (xb, 4.2), (xa, H + 5.2)]
        cw = M.extrude(poly(pts), cheek).translate([0, 0, LD - cheek])
        parts.append(cw)
        xp = xb + sg * 1.4
        parts.append(box([min(xp - 1.8, xp + 1.8), 0.0, LD - cheek - 0.6], [max(xp - 1.8, xp + 1.8), 6.4, LD + 0.6]))
        parts.append(M.hull_points([(xp + dx, 6.39, LD - cheek / 2 + dz) for dx in (-1.8, 1.8) for dz in (-1.4, 1.4)] +
                                   [(xp + dx, 7.4, LD - cheek / 2 + dz) for dx in (-1.3, 1.3) for dz in (-0.9, 0.9)]))
        parts.append(_ball(1.3, 9.0, neck=0.8).rotate([-90, 0, 0]).translate([xp, 0.0, LD - cheek / 2]))
        # the back cheek (against the gallery) as a low wall
        parts.append(box([min(xa, xb) - 0.01, 0.0, 0.0], [max(xa, xb) + 0.01, 3.0, LD - fw - cheek + 0.01]))
    body = union(parts)
    # the parapet's door opening, a blind lancet arch under the landing
    body = body - box([-LW / 2 + cheek, H - 0.5, LD - cheek - 1], [LW / 2 - cheek, H + 6, LD + 1])
    nich = _lancet(-3.0, 3.0, H - 9.0 - _apex(6.0), v0=2.0)
    body = body - M.extrude(nich, 0.8).translate([0, 0, LD - 0.79])
    return body


def cistern_evangeline(r=9.0, hb=12.0, ht=30.0):
    """A domed cypress cistern on an octagonal brick base, as two parts: the base (a battered
    octagon with a chamfered cap) and the tank (staves with three iron hoops, a cornice ring and
    an ogee dome with a ball finial; one filament change at the dome). Both print upright; the
    tank's foot drops into a shallow socket in the base."""
    oc = circle((0.0, 0.0), r + 2.4, 8).rotate(22.5)
    base = M.extrude(oc, hb - 1.2)
    base = base + M.hull_points([(p[0] * 1.0, p[1] * 1.0, hb - 1.21) for p in oc.offset(0.0, MIT, 4.0).to_polygons()[0]] +
                                [(p[0], p[1], hb) for p in oc.offset(0.6, MIT, 4.0).to_polygons()[0]])
    for k in range(8):
        a = math.pi / 4 * k
        arch = _lancet(-2.0, 2.0, 5.0, v0=1.4, r=4.0, seg=8)
        A = np.array([[-math.sin(a), 0, math.cos(a), (r + 2.4) * math.cos(math.pi / 8) * math.cos(a)],
                      [math.cos(a), 0, math.sin(a), (r + 2.4) * math.cos(math.pi / 8) * math.sin(a)],
                      [0, 1.0, 0, 0]])
        base = base - ext(arch, -0.5, 1.0).transform(A)
    sock = M.cylinder(1.0, r + 0.15, r + 0.15, 48).translate([0, 0, hb - 0.8])
    base = base - sock
    # the tank: staves (shallow grooves), hoops, a cornice, the dome
    tank = M.cylinder(ht + 0.8, r, r, 48).translate([0, 0, -0.8])
    grooves = union([box([r - 0.25, -0.2, 0.6], [r + 1.0, 0.2, ht - 2.6]).rotate([0, 0, 360.0 * k / 40]) for k in range(40)])
    tank = tank - grooves
    for z in (ht * 0.12, ht * 0.45, ht * 0.78):
        tank = tank + M.cylinder(0.8, r + 0.3, r + 0.3, 48).translate([0, 0, z]) + \
            M.cylinder(0.3, r, r + 0.3, 48).translate([0, 0, z - 0.3])
    tank = tank + M.cylinder(0.6, r, r + 0.6, 48).translate([0, 0, ht - 2.0]) + M.cylinder(1.4, r + 0.6, r + 0.6, 48).translate([0, 0, ht - 1.41])
    zc = ht
    prof = [(0.0, 0.0), (r + 0.2, 0.0), (r - 0.2, 1.0), (r - 1.2, 2.6), (r - 3.0, 4.6), (r * 0.42, 6.4), (r * 0.26, 8.0),
            (r * 0.2, 9.0), (0.9, 9.6), (0.6, 10.2), (0.0, 10.2)]
    dome = PW._revolve(prof, 48).translate([0, 0, zc - 0.01])
    dome = dome + _ball(1.2, zc + 11.2, neck=0.6)
    return base, tank, dome


def chimney_evangeline(w=9.0, d=8.0, h=30.0):
    """A riverboat stack pair: a stucco base with a sunk lancet panel on each face under a
    moulded band, from which rise two round flues each crowned with a flared feathered crown
    (points round a ring) like a steamboat's smokestacks; a tie bar between them below the
    crowns. Prints upright."""
    h = round(h / 0.2) * 0.2
    hb = h * 0.42
    body = box([-w / 2, -d / 2, 0.0], [w / 2, d / 2, hb])
    for (L, D, rot) in ((w, d, 0), (d, w, 90), (w, d, 180), (d, w, 270)):
        pan = _lancet(-L / 2 + 1.4, L / 2 - 1.4, hb - 3.0 - _apex(L - 2.8), v0=2.4)
        sunk = M.extrude(pan, 0.5).transform(np.array([[1.0, 0, 0, 0], [0, 0, 1.0, D / 2 - 0.49], [0, 1.0, 0, 0]]))
        body = body - sunk.rotate([0, 0, rot])
    body = body + M.hull_points([(x, y, hb - 0.01) for x in (-w / 2, w / 2) for y in (-d / 2, d / 2)] +
                                [(x, y, hb + 0.6) for x in (-w / 2 - 0.6, w / 2 + 0.6) for y in (-d / 2 - 0.6, d / 2 + 0.6)])
    body = body + box([-w / 2 - 0.6, -d / 2 - 0.6, hb + 0.59], [w / 2 + 0.6, d / 2 + 0.6, hb + 1.6])
    body = body + M.hull_points([(x, y, hb + 1.59) for x in (-w / 2 - 0.6, w / 2 + 0.6) for y in (-d / 2 - 0.6, d / 2 + 0.6)] +
                                [(x, y, hb + 2.4) for x in (-w / 2, w / 2) for y in (-d / 2, d / 2)])
    rf = min(w / 4 - 0.2, d / 2 - 0.8)
    zf = hb + 2.39
    hf = h - zf - 3.2
    for sx in (-1, 1):
        x = sx * w / 4
        flue = M.cylinder(hf, rf, rf * 0.92, 32).translate([x, 0.0, zf])
        flue = flue + M.cylinder(1.2, rf * 0.92, rf * 0.92 + 1.1, 32).translate([x, 0.0, zf + hf - 0.01])
        ring = M.cylinder(0.8, rf * 0.92 + 1.1, rf * 0.92 + 1.1, 32).translate([x, 0.0, zf + hf + 1.18])
        flue = flue + ring
        for k in range(8):
            a = 2 * math.pi * k / 8
            cx, cy = x + (rf * 0.92 + 0.65) * math.cos(a), (rf * 0.92 + 0.65) * math.sin(a)
            flue = flue + M.hull_points([(cx + 0.45 * math.cos(a + s * math.pi / 2), cy + 0.45 * math.sin(a + s * math.pi / 2), zf + hf + 1.97)
                                         for s in (-1, 1)] + [(cx + 0.3 * math.cos(a), cy + 0.3 * math.sin(a), zf + hf + 1.97),
                                                              (cx - 0.3 * math.cos(a), cy - 0.3 * math.sin(a), zf + hf + 1.97),
                                                              (cx, cy, zf + hf + 3.2)])
        flue = flue - M.cylinder(4.0, rf * 0.92 - 0.6, rf * 0.92 - 0.6, 24).translate([x, 0.0, zf + hf - 1.0])
        body = body + flue
    body = body + box([-w / 4, -0.45, zf + hf * 0.7], [w / 4, 0.45, zf + hf * 0.7 + 0.9])
    return body


CO.FRIEZE_EXTRA.update(sugarcane=frieze_sugarcane, cottonbolls=frieze_cottonbolls, lancetfoils=frieze_lancetfoils)
CO.COURSE_EXTRA.update(starrow=course_starrow, trefoilrow=course_trefoilrow)
TW.BRACKET_EXTRA.update(trefoilknee=bracket_trefoilknee)
TW.PIERCED = TW.PIERCED + ("trefoilknee",)
TW.FOUNDATION_EXTRA.update(plinthtorus=foundation_plinthtorus)
SH.CORNER_EXTRA.update(evangeline=corner_evangeline)
PW.POSTS.update(crocketcap=post_crocketcap)
PW.BALUSTERS.update(onionbulb=(baluster_onionbulb, 1.6))
PW.FRIEZES.update(lancetarcade=frieze_lancetarcade)
FT.EDGE_EXTRA.update(lancetfringe=edge_lancetfringe)

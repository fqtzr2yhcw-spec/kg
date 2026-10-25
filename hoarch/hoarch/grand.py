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
    # each flight rides on a raking soffit 7 mm under its nosings (49 degrees: it prints
    # upright with nothing hanging), open beneath so the arcade shows through; a lancet
    # passage runs under the landing
    for sg in (-1, 1):
        x0, x1 = sg * (LW / 2 + 1.0), sg * (LW / 2 + run * (1 - 7.0 / H) - 3.6)
        vt = H * (1 - (abs(x0) - LW / 2) / run) - 7.0
        vb = H * (1 - (abs(x1) - LW / 2) / run) - 7.0
        hole = poly([(x0, -1.0), (x1, -1.0), (x1, max(vb, 0.0) + 0.0), (x0, vt)]).offset(-0.6, RND).offset(0.6, RND)
        body = body - ext(hole ^ rect(-1e3, -1.0, 1e3, 1e3), -1.0, LD + 1.0)
    pas = _lancet(-LW / 2 + 2.4, LW / 2 - 2.4, H - 9.0 - _apex(LW - 4.8), v0=-1.0)
    body = body - ext(pas, -1.0, LD + 1.0)
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


# ================================================================== the Bellosguardo (house 93)
# An Italian villa, 1866, of the kind the pattern books called "Tuscan": a brownstone ground
# storey of drafted ashlar and an upper storey of orange Siena brick in monk bond with a diaper of
# raised headers, pillowed quoins, cream stone dressings and olive accents; a flat roof behind a
# stone balustrade with urns over a deep cornice of coffers and paired pendant scrolls. In the
# angle of the L a campanile rises two stages over the roof: a stage of bifora windows, then an
# open belvedere loggia of paired arches, under a bracketed cornice and a pyramid of clay tiles
# crowned by a pine cone. A loggia of Corinthian columns and archivolted arches wraps the front
# and the west side, its flat roof a terrace behind another balustrade; the wing's upper storey
# holds a Serliana over a balconet; the door stands in a Gibbs surround of rusticated blocks.

BS_LEVELS = dict(hi=40.0)      # the building sets it: the brick storey's foot over the block's base


def stone_drafted(region, datum=0.0, course=3.0, block=6.4, joint=0.45, d=0.42):
    """Drafted ashlar: every block a raised field inside a flat margin band, both bevelled at
    45 degrees all round, in courses of long blocks broken half a block (the Bellosguardo's
    ground storey)."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    out = []
    k = math.floor((v0 - datum) / course) - 1
    while datum + k * course < v1 + course:
        a, b = datum + k * course + joint / 2, datum + (k + 1) * course - joint / 2
        if b > v0 - 1 and a < v1 + 1:
            u = u0 - block + (k % 2) * block / 2
            while u < u1 + block:
                x0, x1 = u + joint / 2, u + block - joint / 2
                out.append(chamfer_box(x0, a, x1, b, 0.0, d * 0.55, c=0.2, bottom=d * 0.55))
                out.append(chamfer_box(x0 + 0.5, a + 0.45, x1 - 0.5, b - 0.45, d * 0.55 - 0.01, d * 0.45, c=0.18,
                                       bottom=d * 0.45))
                u += block
        k += 1
    return union(out) ^ M.extrude(region, d + 0.2)


def brick_monk(region, datum=0.0, bl=2.4, bh=0.8, mortar=0.5, bed=0.2, d=0.25, lift=0.14):
    """Monk bond (two stretchers and a header in every course, each course shifted half a unit),
    its headers on a diagonal lattice raised a little proud as a diaper of glazed headers (the
    Bellosguardo's upper storey)."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    unit = 2 * bl + bl / 2
    cells, diaper = [], []
    k = math.floor((v0 - datum) / bh) - 1
    while datum + k * bh < v1:
        v = datum + k * bh
        top = v + bh - bed
        j0 = math.floor((u0 - 2 * unit) / unit)
        u = j0 * unit + (k % 2) * unit / 2
        j = j0
        while u < u1 + unit:
            cells.append(rect(u + mortar / 2, v, u + bl - mortar / 2, top))
            cells.append(rect(u + bl + mortar / 2, v, u + 2 * bl - mortar / 2, top))
            hd = rect(u + 2 * bl + mortar / 2, v, u + unit - mortar / 2, top)
            if (j + k // 2) % 4 == 0 or (j - k // 2) % 4 == 0:
                diaper.append(hd)
            else:
                cells.append(hd)
            u += unit
            j += 1
        k += 1
    out = [M.extrude(cs_union(cells) ^ region, d)]
    if diaper:
        out.append(M.extrude(cs_union(diaper) ^ region, d + lift))
    return union(out)


def corner_bellosguardo(L, at_start, qa, qb, w=2.4, t=0.65):
    """The Bellosguardo's corners: on the ashlar storey long and short drafted blocks in its
    courses; on the brick storey pillowed quoins (each face swelling in a 45 degree pillow from
    a flat margin), long and short in turn."""
    def span(a, b):
        return (a, b) if at_start else (L - b, L - a)
    hi = BS_LEVELS["hi"]
    parts = []
    v, k = qa, 0
    while v < min(qb, hi) - 1.6:
        leg = 4.6 if k % 2 == 0 else 2.8
        top = min(v + 2.6, min(qb, hi) - 0.2)
        a, b = span(-0.6, leg)
        parts.append(chamfer_box(a, v + 0.2, b, top, 0.0, t, c=0.25, bottom=t, square=("u0",) if at_start else ("u1",)))
        v += 3.0
        k += 1
    v, k = max(qa, hi), 0
    while v < qb - 2.0:
        leg = 4.4 if k % 2 == 0 else 2.6
        top = min(v + 2.2, qb - 0.2)
        a, b = span(-t - 0.3, leg)
        parts.append(chamfer_box(a, v, b, top, 0.0, 0.35, c=0.15, bottom=0.35, square=("u0",) if at_start else ("u1",)))
        fa, fb = span(0.4, leg - 0.4)
        parts.append(M.hull_points([(x, y, 0.34) for x in (min(fa, fb), max(fa, fb)) for y in (v + 0.4, top - 0.4)] +
                                   [(x, y, t + 0.3) for x in (min(fa, fb) + 0.5, max(fa, fb) - 0.5) for y in (v + 0.9, top - 0.9)]))
        v += 2.6
        k += 1
    return union(parts) if parts else M()


def foundation_talusvent(reg, seed=0):
    """A battered brownstone talus under a cyma water table, pierced every 20 mm or so by a
    square vent with two bars (the Bellosguardo)."""
    b = reg.bounds()
    out = [M.hull_points([(x, b[1], 0.0) for x in (b[0], b[2])] + [(x, b[1], 0.9) for x in (b[0], b[2])] +
                         [(x, b[3] - 1.6, 0.4) for x in (b[0], b[2])] + [(x, b[3] - 1.6, 0.0) for x in (b[0], b[2])])]
    wt = rect(b[0] - 1, b[3] - 1.6, b[2] + 1, b[3]) ^ reg
    if not wt.is_empty():
        wb = wt.bounds()
        out.append(M.hull_points([(x, wb[1] - 0.3, 0.0) for x in (wb[0], wb[2])] + [(x, wb[1] + 0.4, 0.9) for x in (wb[0], wb[2])] +
                                 [(x, wb[3] - 0.3, 0.9) for x in (wb[0], wb[2])] + [(x, wb[3], 0.4) for x in (wb[0], wb[2])] +
                                 [(x, wb[3], 0.0) for x in (wb[0], wb[2])]))
    body = union(out) ^ M.extrude(reg, 2.0)
    u = b[0] + 10.0
    vents = []
    while u < b[2] - 6.0:
        vc = (b[1] + b[3] - 1.6) / 2
        if b[3] - b[1] > 5.0:
            vents.append(ext(rect(u - 1.6, vc - 1.0, u + 1.6, vc + 1.0), 0.3, 2.0) -
                         ext(cs_union([rect(u - 0.8 - 0.25, vc - 1.2, u - 0.8 + 0.25, vc + 1.2),
                                       rect(u + 0.8 - 0.25, vc - 1.2, u + 0.8 + 0.25, vc + 1.2)]), 0.3, 2.0))
        u += 20.0
    if vents:
        body = body - union(vents)
    return body


# ------------------------------------------------------------------ cornice ornaments
def course_guilloche(L, h, b, pitch, margin, p):
    """A guilloche: a chain of interlaced rings, a bead in every eye (the Bellosguardo's storey
    joint)."""
    ro = h * 0.45
    pu = ro * 1.7
    n = max(1, int((L - 0.6) / pu))
    u0 = (L - n * pu) / 2
    rings = cs_union([circle((u0 + pu * (k + 0.5), h / 2), ro, 24) - circle((u0 + pu * (k + 0.5), h / 2), ro - 0.42, 20)
                      for k in range(n)]) ^ rect(0.2, 0.0, L - 0.2, h)
    beads = cs_union([circle((u0 + pu * (k + 0.5), h / 2), max(0.3, ro - 0.75), 12) for k in range(n)])
    return [_st(rect(0.2, 0.15, L - 0.2, h - 0.15), b, 0.18), _st(rings, b + 0.18, 0.3), _st(beads, b + 0.18, 0.3)]


def course_eggdart(L, h, b, pitch, margin, p):
    """Egg and dart: eggs in open shells, a dart between every two (the Bellosguardo's eave)."""
    pu = 2.0
    n = max(1, int((L - 0.6) / pu))
    u0 = (L - n * pu) / 2
    eggs, shells, darts = [], [], []
    for k in range(n):
        c = (u0 + pu * (k + 0.5), h * 0.48)
        ry = h * 0.36
        eggs.append(oval(c, 0.5, ry, 16))
        sh = oval(c, 0.82, ry + 0.3, 18) - oval(c, 0.58, ry + 0.08, 16)
        shells.append(sh ^ rect(-1e3, -1e3, 1e3, c[1] + ry * 0.6))
        x = u0 + pu * k
        darts.append(poly([(x - 0.26, h * 0.82), (x + 0.26, h * 0.82), (x, h * 0.12)]))
    darts.append(poly([(u0 + pu * n - 0.26, h * 0.82), (u0 + pu * n + 0.26, h * 0.82), (u0 + pu * n, h * 0.12)]))
    clip = rect(0.2, 0.0, L - 0.2, h)
    return [_st(rect(0.2, 0.15, L - 0.2, h - 0.15), b, 0.15), _st(cs_union(shells) ^ clip, b + 0.15, 0.25),
            _st(cs_union(eggs) ^ clip, b + 0.15, 0.4), _st(cs_union(darts) ^ clip, b + 0.15, 0.3)]


def frieze_olivebranch(L, h, b, pitch, margin, pair, half):
    """An olive branch running the length of the frieze in a gentle wave, pointed leaves in
    pairs along it and clusters of olives; a rosette at every station (the Bellosguardo's storey
    joint)."""
    v0, v1 = 0.8, h - 0.8
    vm = (v0 + v1) / 2
    amp = (v1 - v0) * 0.18
    pts = [(u, vm + amp * math.sin(u / 5.0 * math.pi)) for u in np.arange(0.4, L - 0.3, 0.5)]
    out = []
    if len(pts) > 1:
        out.append(_st(stroke(pts, 0.5), b, 0.3))
    leaves, olives = [], []
    for k, u in enumerate(np.arange(1.6, L - 1.4, 1.8)):
        v = vm + amp * math.sin(u / 5.0 * math.pi)
        sg = 1 if k % 2 == 0 else -1
        leaves.append(_lens((u + 0.35, v + sg * 0.75), 1.9, 0.55, sg * 1.1))
        if k % 3 == 1:
            olives.append(oval((u - 0.4, v - sg * 0.85), 0.4, 0.55, 12))
    clip = rect(0.2, v0, L - 0.2, v1)
    if leaves:
        out.append(_st(cs_union(leaves) ^ clip, b, 0.38))
    if olives:
        out.append(_st(cs_union(olives) ^ clip, b, 0.5))
    return out, []


def frieze_rosettecoffers(L, h, b, pitch, margin, pair, half):
    """Coffers: in every bay between the paired brackets a square coffer with a moulded rim and
    a raised eight-petal rosette (the Bellosguardo's eave)."""
    v0, v1 = 0.7, h - 0.7
    out = []
    for uc, wd in CO._between(L, pitch, margin, pair, half):
        s = min(wd - 0.8, v1 - v0)
        if s < 3.0:
            continue
        sq = rect(uc - s / 2, (v0 + v1) / 2 - s / 2, uc + s / 2, (v0 + v1) / 2 + s / 2)
        out.append(_st(sq - sq.offset(-0.55, MIT, 4.0), b, 0.4))
        c = (uc, (v0 + v1) / 2)
        r = min(1.3, s * 0.3)
        pet = cs_union([circle((c[0] + r * 0.62 * math.cos(a), c[1] + r * 0.62 * math.sin(a)), r * 0.38, 12)
                        for a in np.linspace(0, 2 * math.pi, 8, endpoint=False)])
        out.append(_st(pet, b, 0.35))
        out.append(_st(circle(c, r * 0.36, 12), b, 0.55))
    return out, []


def frieze_wreathribbons(L, h, b, pitch, margin, pair, half):
    """Laurel wreaths tied with ribbons whose ends flutter down either side, one in every bay
    (the Bellosguardo's campanile)."""
    v0, v1 = 0.7, h - 0.7
    out = []
    for uc, wd in CO._between(L, pitch, margin, pair, half):
        R_ = min((v1 - v0) * 0.36, wd * 0.28, 1.9)
        if R_ < 1.1:
            continue
        c = (uc, (v0 + v1) / 2 + 0.3)
        leaves = []
        for a in np.linspace(math.pi * 0.62, math.pi * 2.38, 12):
            leaves.append(_lens((c[0] + R_ * math.cos(a), c[1] + R_ * math.sin(a)), 1.1, 0.5, a + math.pi / 2 + 0.45))
        bow = circle((c[0], c[1] - R_), 0.45, 12)
        ribbons = cs_union([stroke([(c[0], c[1] - R_), (c[0] + sg * 0.8, c[1] - R_ - 0.7), (c[0] + sg * 1.2, v0 + 0.15)], 0.5)
                            for sg in (-1, 1)])
        out.append(_st(_clip_v(cs_union(leaves), v0, v1), b, 0.38))
        out.append(_st(_clip_v(ribbons + bow, v0, v1), b, 0.3))
    return out, []


def bracket_pendantscroll(h, d, t):
    """An Italianate console: an S of a big scroll against the wall and a small one under the
    soffit's front, a bead down its front edge and a turned drop hanging under the big scroll
    (side profile, top at v = 0; the Bellosguardo, in pairs)."""
    rb = min(1.1, h * 0.26, d * 0.3)
    rs = min(0.6, h * 0.14, d * 0.18)
    cb = (rb + 0.25, -h + rb + 0.5)
    cs_ = (d - rs, -rs)
    body = poly([(0.0, 0.0), (d, 0.0), (d, -rs * 2 + 0.1), (cb[0] + rb * 0.6, cb[1] + rb * 0.9), (cb[0], cb[1] - rb),
                 (0.0, cb[1] - rb)])
    prof = cs_union([body, circle(cb, rb, 20), circle(cs_, rs, 14), circle((cb[0], cb[1] - rb - 0.25), 0.42, 12)])
    return prof - circle(cb, rb * 0.4, 12)


def fence_bello_parapet(L, h):
    """The roofs' stone balustrade seen face on (printed flat, full size): a plinth, a capped
    rail, square pedestals every 16 mm or so carrying urns, and between them Renaissance
    balusters swelling twice (vase over vase)."""
    nseg = max(1, int(round(L / 16.0)))
    seg = L / nseg
    cells = [rect(0.0, 0.0, L, 1.0), rect(0.0, h - 1.1, L, h - 0.4), rect(0.0, h - 0.41, L, h)]
    for j in range(nseg + 1):
        u = min(max(seg * j, 1.1), L - 1.1)
        cells.append(rect(u - 1.1, 0.0, u + 1.1, h + 0.4))
        cells.append(urn_cs(u, h + 0.39, 3.2, 1.8))
        if j < nseg:
            a, b = u + 1.1, min(max(seg * (j + 1), 1.1), L - 1.1) - 1.1
            nb = max(1, int((b - a) / 1.7))
            for k in range(nb):
                x = a + (b - a) * (k + 0.5) / nb
                lo, hi = 0.95, h - 1.05
                cells.append(cs_union([rect(x - 0.28, lo, x + 0.28, hi), oval((x, lo + (hi - lo) * 0.28), 0.5, (hi - lo) * 0.17, 14),
                                       oval((x, lo + (hi - lo) * 0.7), 0.42, (hi - lo) * 0.13, 14)]))
    return cs_union(cells) ^ rect(0.0, 0.0, L, h + 4.0)


def finial_pigna(h=8.0):
    """A pine cone (pigna) finial: a moulded base, a cone of scales (rings stepping in), a
    pointed tip (the Bellosguardo's campanile)."""
    prof = [(0.0, 0.0), (1.5, 0.0), (1.5, 0.5), (1.0, 1.0), (0.7, 1.3), (1.1, 1.7)]
    z = 1.7
    r = 1.25
    k = 0
    while r > 0.6 and z < h - 1.6:
        prof += [(r, z), (r - 0.15, z + 0.35), (r - 0.05, z + 0.45)]
        z += 0.6
        r = 1.25 * (1 - (z - 1.7) / (h - 1.7)) + 0.1 * (k % 2)
        k += 1
    prof += [(0.5, z), (0.45, h - 0.9), (0.0, h - 0.9)]       # (the tip ends in a ball: a bare spike is
    return PW._revolve(prof, 24) + _ball(0.58, h - 0.58, neck=0.0)   # too thin to print)


# ------------------------------------------------------------------ windows and doors
def _florentine(w, h, A, n=9, gap=0.3, crown=2.6, foot=1.5):
    """Florentine voussoirs round a round head (opening w wide, spring at h - w/2): radial
    stones whose extrados rises from ``foot`` long at the springing to ``crown`` at the key, so
    the arch's outer edge comes to a slight point. Returns (cs, top v)."""
    r0 = w / 2 + A
    cy = h - w / 2
    blocks = []
    for k in range(n):
        a0 = math.pi * k / n + gap / 2 / r0
        a1 = math.pi * (k + 1) / n - gap / 2 / r0
        am = (a0 + a1) / 2
        Lk = foot + (crown - foot) * math.sin(am)
        pts = [(r0 * math.cos(a), cy + r0 * math.sin(a)) for a in np.linspace(a0, a1, 5)]
        pts += [((r0 + Lk) * math.cos(a), cy + (r0 + Lk) * math.sin(a)) for a in np.linspace(a1, a0, 5)]
        blocks.append(poly(pts))
    return cs_union(blocks), cy + r0 + crown


def window_bello_ground(w=8.4, h=20.0, A=0.8):
    """The ashlar storey's window: a round-headed two-over-two sash in a casing, Florentine
    voussoirs round its head over an impost band, a sill on two blocks and a panelled apron."""
    op = O.opening_cs(w, h, w / 2)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    sash = O.window_insert(w, h, w / 2, lites=(2, 2), bare=True)["insert"]
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             MD.band(op.offset(A, RND), A, MD.CASING, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op)]
    vs, vt = _florentine(w, h, A)
    parts.append(ext(vs, 0.0, 0.8))
    spring = h - w / 2
    hw = w / 2 + A + 1.8
    parts.append(chamfer_box(-hw, spring - 1.0, -w / 2 - A + 0.01, spring, 0.0, 0.9, c=0.2, bottom=0.9))
    parts.append(chamfer_box(w / 2 + A - 0.01, spring - 1.0, hw, spring, 0.0, 0.9, c=0.2, bottom=0.9))
    sw = w / 2 + A + 0.6
    parts.append(MD.run(-sw, sw, 0.0, MD.SILL, 1.0, up=False))
    parts.append(ext(rect(-w / 2, -3.4, w / 2, -0.79), 0.0, 0.4))
    parts.append(chamfer_box(-w / 2 + 0.7, -2.8, w / 2 - 0.7, -1.4, 0.39, 0.3, c=0.15))
    return O._one_piece([sash], parts, op, plug_cs, O.PLUG, vt + 0.2, -3.4)


def window_bello_upper(w=8.0, h=19.0, A=0.9, rise=1.2):
    """The brick storey's window (a tabernacle): a segmental one-over-one sash in an eared
    architrave, a frieze hung with a festoon, a cornice hood on two scroll consoles, a sill on
    blocks."""
    op = O.opening_cs(w, h, rise)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    sash = O.window_insert(w, h, rise, lites=(1, 1), bare=True)["insert"]
    half = w / 2 + A
    outer = cs_union([rect(-half, 0.0, half, h + A), rect(-half - 0.7, h - 1.8, half + 0.7, h + A)])
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             MD.band(outer, A + 0.7, MD.ARCHITRAVE, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op)]
    vf = h + A
    parts.append(ext(rect(-half, vf - 0.01, half, vf + 2.4), 0.0, 0.5))
    fest = swag(-half + 1.0, half - 1.0, vf + 2.0, 1.1, width=0.6)
    tails = cs_union([stroke([(sg * (half - 1.0), vf + 2.0), (sg * (half - 0.8), vf + 0.6)], 0.5) for sg in (-1, 1)])
    parts.append(ext(_clip_v(fest + tails, vf + 0.15, vf + 2.3), 0.49, 0.9))
    vc = vf + 2.4 + 1.1
    parts.append(MD.run(-half - 1.2, half + 1.2, vc, MD.CROWN, 1.1, up=False))
    for sg in (-1, 1):
        x = sg * (half + 0.55)
        con = cs_union([rect(x - 0.5, vf - 2.2, x + 0.5, vc - 1.05), circle((x, vf - 2.2), 0.5, 12)])
        parts.append(ext(con, 0.0, 1.0))
        parts.append(ext(circle((x, vc - 1.6), 0.4, 12), 0.99, 1.3))
    sw = half + 0.4
    parts.append(MD.run(-sw, sw, 0.0, MD.SILL, 1.0, up=False))
    for sg in (-1, 1):
        parts.append(chamfer_box(sg * (w / 2) - 0.7, -1.8, sg * (w / 2) + 0.7, -0.8, 0.0, 0.9, c=0.25))
    return O._one_piece([sash], parts, op, plug_cs, O.PLUG, vc + 0.2, -1.8)


def window_bello_serliana(wc=7.2, hc=20.0, ws=3.2, hs=14.0, mul=1.6, A=0.9):
    """A Serliana for the wing's upper storey: a round-headed centre light springing from the
    entablature over two narrow flat-headed side lights, engaged colonnettes at the mullions, an
    archivolt with a keystone; a balconet of turned balusters below."""
    W_ = wc + 2 * ws + 2 * mul
    rc = wc / 2
    spring = hc - rc
    op = cs_union([O.opening_cs(wc + 2 * mul, hc, rc + mul), rect(-W_ / 2, 0.0, W_ / 2, hs)])
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    inner = plug_cs.offset(-0.6, MIT, 4.0)
    body = [ext(plug_cs, -pl, -0.6)]
    mids = cs_union([rect(sg * (wc / 2 + mul / 2) - mul / 2, -1, sg * (wc / 2 + mul / 2) + mul / 2, hs + 0.8) for sg in (-1, 1)]
                    + [rect(-W_, hs - 0.1, W_, hs + 0.8) - rect(-wc / 2, -1, wc / 2, 100)])
    g = inner - mids
    bars = cs_union([rect(-W_, hs * 0.5 - 0.35, W_, hs * 0.5 + 0.35), rect(-RIB / 2, spring, RIB / 2, hc)])
    sash = _glazed(body, g, pl, bars, plug_cs) + [ext(mids ^ plug_cs, -pl, -0.6)]
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             MD.band(op.offset(A, MIT, 4.0), A, MD.CASING, clip=rect(-W_ - 10, 0.0, W_ + 10, hc + 40) - op)]
    for sg in (-1, 1):
        x = sg * (wc / 2 + mul / 2)
        prof = [(0.0, 0.0), (0.55, 0.0), (0.55, hs - 1.4), (0.75, hs - 1.0), (0.75, hs - 0.6), (0.0, hs - 0.6)]
        parts.append(PW._revolve(prof, 18).rotate([-90, 0, 0]).translate([x, 0.0, 0.0]) ^ box([x - 2, 0.0, 0.0], [x + 2, hs, 3.0]))
    ent = rect(-W_ / 2 - A, hs - 0.01, W_ / 2 + A, hs + 1.2) - O.opening_cs(wc, hc + 5, rc)
    parts.append(ext(ent, 0.0, 1.0))
    arc = O.opening_cs(wc + 2 * (mul + 1.0), hc + 1.0, rc + mul + 1.0) - O.opening_cs(wc + 2 * mul, hc, rc + mul)
    parts.append(ext(arc ^ rect(-W_, spring, W_, hc + 5), 0.0, 1.1))
    parts.append(keystone(0.0, hc - 0.4, 2.6, 1.2, 1.8, 0.0, 1.5))
    sw = W_ / 2 + A + 0.6
    parts.append(MD.run(-sw, sw, 0.0, MD.SILL, 1.0, up=False))
    bal = [rect(-sw + 0.4, -4.2, sw - 0.4, -3.6), rect(-sw + 0.4, -1.4, sw - 0.4, -0.79)]
    for x in np.arange(-sw + 1.2, sw - 1.0, 1.5):
        bal.append(cs_union([rect(x - 0.25, -3.7, x + 0.25, -1.3), oval((x, -2.6), 0.45, 0.6, 12)]))
    parts.append(ext(cs_union(bal), 0.0, 0.8))
    return O._one_piece(sash, parts, op, plug_cs, pl, hc + 2.4, -4.2)


def window_bello_bifora(w=11.0, h=17.0, A=0.9):
    """The campanile's bifora: two round-headed lights parted by a colonnette under one round
    arch, an oculus in the tympanum between them, an archivolt with a keystone; a sill."""
    r = w / 2
    op = O.opening_cs(w, h, r)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    inner = plug_cs.offset(-0.6, MIT, 4.0)
    sw_ = (w - 1.2 - 1.2) / 2
    rs = sw_ / 2
    vs = h - r - 0.6
    lights = [O.opening_cs(sw_, vs, rs).translate((sg * (sw_ / 2 + 0.6), 0.0)) ^ inner for sg in (-1, 1)]
    oc = (0.0, vs + (h - vs) * 0.45)
    ro = min(1.4, (h - vs) * 0.3)
    lights.append(circle(oc, ro, 24))
    body = [ext(plug_cs, -pl, -0.6)]
    bars = cs_union([rect(-w, (vs - rs) * 0.5 - 0.3, w, (vs - rs) * 0.5 + 0.3)])
    sash = _glazed(body, cs_union(lights), pl, bars, plug_cs)
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             MD.band(op.offset(A, RND), A, MD.ARCHITRAVE, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op)]
    prof = [(0.0, 0.0), (0.5, 0.0), (0.5, vs - rs - 1.0), (0.72, vs - rs - 0.6), (0.72, vs - rs - 0.2), (0.0, vs - rs - 0.2)]
    parts.append(PW._revolve(prof, 16).rotate([-90, 0, 0]) ^ box([-2, 0.0, 0.0], [2, h, 3.0]))
    parts.append(keystone(0.0, h - 0.3, A + 1.6, 1.2, 1.8, 0.0, 1.4))
    sw = r + A + 0.5
    parts.append(MD.run(-sw, sw, 0.0, MD.SILL, 1.0, up=False))
    return O._one_piece(sash, parts, op, plug_cs, pl, h + A + 1.6, -1.0)


def door_bello(w=13.0, h=25.0, A=1.0):
    """The Bellosguardo's entrance: a pair of leaves of two raised panels each under a round
    fanlight of radiating bars and a ring; a Gibbs surround (a casing broken by rusticated
    blocks long and short up the jambs and round the head as voussoirs, a big keystone); a
    cornice over all."""
    r = w / 2
    op = O.opening_cs(w, h, r)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    spring = h - r
    inner = plug_cs.offset(-0.5, MIT, 4.0)
    ib = inner.bounds()
    dh = spring - 0.4
    mid = 0.6
    lw = (ib[2] - ib[0] - mid) / 2
    body = [ext(plug_cs, -pl, -1.0)]
    ul = ib[0]
    for i in range(2):
        body.append(ext(rect(ul, 0.5, ul + lw, dh), -pl, -0.8))
        body.append(_panel(rect(ul + 0.7, 1.2, ul + lw - 0.7, dh * 0.42)))
        body.append(_panel(rect(ul + 0.7, dh * 0.42 + 0.8, ul + lw - 0.7, dh - 0.8)))
        ul += lw + mid
    fan = inner ^ rect(-w, spring + 0.4, w, h + 2)
    fc = (0.0, spring + 0.4)
    rays = [stroke([fc, (fc[0] + w * math.cos(a), fc[1] + w * math.sin(a))], RIB) for a in np.linspace(0.42, math.pi - 0.42, 5)]
    ring = circle(fc, r * 0.55, 32) - circle(fc, r * 0.55 - RIB, 32)
    sash = _glazed(body, fan, pl, cs_union(rays + [ring, circle(fc, 1.0, 16)]), plug_cs)
    sash.append(ext(rect(-w, dh - 0.01, w, spring + 0.42) ^ plug_cs, -pl, -0.5))
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             MD.band(op.offset(A, RND), A, MD.ARCHITRAVE, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op)]
    # the Gibbs blocks up the jambs
    v = 0.0
    k = 0
    while v < spring - 2.0:
        leg = 2.8 if k % 2 == 0 else 1.8
        for sg in (-1, 1):
            a, b = sorted((sg * (w / 2 + A - 0.2), sg * (w / 2 + A + leg)))
            parts.append(chamfer_box(a, v, b, min(v + 2.4, spring), 0.0, 1.0, c=0.25, bottom=1.0))
        v += 2.8
        k += 1
    vs, vt = _florentine(w, h, A, n=7, crown=3.0, foot=2.4)
    parts.append(ext(vs, 0.0, 1.0))
    parts.append(keystone(0.0, h + A - 0.4, 3.6, 1.8, 2.6, 0.0, 1.6))
    half = w / 2 + A + 3.2
    parts.append(MD.run(-half, half, vt + 0.6, MD.CROWN, 1.2, up=False))
    parts.append(ext(rect(-half + 0.4, vt - 0.61, half - 0.4, vt + 0.61 - 1.2 + 0.01), 0.0, 0.6))
    parts.append(ext(rect(-w / 2 - A - 0.6, -0.6, w / 2 + A + 0.6, 0.01), 0.0, 1.2))
    return O._one_piece(sash, parts, op, plug_cs, pl, vt + 0.8, -0.6)


def door_bello_back(w=10.0, h=24.0, A=0.9, rise=1.4):
    """The garden door: one leaf, two raised panels under a light of four panes, a segmental
    transom, a plain architrave under a frieze and cornice."""
    op = O.opening_cs(w, h, rise)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    inner = plug_cs.offset(-0.5, MIT, 4.0)
    ib = inner.bounds()
    dh = h - rise - 3.6
    gv0 = dh * 0.48
    body = [ext(plug_cs, -pl, -1.0), ext(rect(ib[0], 0.5, ib[2], dh), -pl, -0.8),
            _panel(rect(ib[0] + 0.8, 1.2, ib[2] - 0.8, gv0 * 0.5 - 0.2)), _panel(rect(ib[0] + 0.8, gv0 * 0.5 + 0.2, ib[2] - 0.8, gv0 - 0.8))]
    light = rect(ib[0] + 0.9, gv0, ib[2] - 0.9, dh - 0.8)
    tran = inner ^ rect(-w, dh + 0.5, w, h + 2)
    bars = cs_union([rect(-RIB / 2, gv0, RIB / 2, dh), rect(-w, (gv0 + dh - 0.8) / 2 - RIB / 2, w, (gv0 + dh - 0.8) / 2 + RIB / 2)])
    sash = _glazed(body, light + tran, pl, bars, plug_cs)
    sash.append(ext(rect(-w, dh - 0.01, w, dh + 0.52) ^ plug_cs, -pl, -0.5))
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             MD.band(op.offset(A, MIT, 4.0), A, MD.ARCHITRAVE, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op)]
    half = w / 2 + A + 0.4
    vf = h + A
    parts.append(ext(rect(-half, vf - 0.01, half, vf + 1.8), 0.0, 0.5))
    vc = vf + 1.8 + 1.1
    parts.append(MD.run(-half - 0.8, half + 0.8, vc, MD.CROWN, 1.1, up=False))
    parts.append(ext(rect(-w / 2 - A - 0.4, -0.6, w / 2 + A + 0.4, 0.01), 0.0, 1.0))
    return O._one_piece(sash, parts, op, plug_cs, pl, vc + 0.2, -0.6)


# ------------------------------------------------------------------ loggia parts
def post_corinthian(h, collar=None, abacus=3.4, slot=(1.2, 1.0)):
    """A Corinthian column: an Attic base, a plain shaft with entasis, a bell capital wrapped in
    two rows of eight acanthus leaves (thin ribs standing off the bell) under four corner
    volutes (flat-topped plates) and a concave abacus (the Bellosguardo's loggia)."""
    zc = h - 3.6
    r = 1.0
    prof = [(0.0, 1.19), (1.45, 1.19), (1.45, 1.4), (1.25, 1.6), (1.12, 1.8), (1.26, 2.0), (1.08, 2.3), (r, 2.6),
            (r * 1.05, (2.6 + zc) * 0.4), (r * 0.9, zc - 0.3), (1.05, zc - 0.1), (1.05, zc + 0.1), (0.95, zc + 0.3),
            (1.1, zc + 1.4), (1.3, zc + 2.0)]
    body = PW._revolve(prof, 32) + PW._plinth(3.0)
    body = body + PW._top(h, abacus / 2, zc + 2.0, 1.3, slot, seg=32)
    for row, (z0, z1, rr, off) in enumerate(((zc + 0.3, zc + 1.2, 1.08, 0.0), (zc + 0.9, zc + 1.9, 1.24, math.pi / 8))):
        for k in range(8):
            a = 2 * math.pi * k / 8 + off
            c, s = math.cos(a), math.sin(a)
            leaf = M.hull_points([(c * (rr - 0.1) - s * 0.25, s * (rr - 0.1) + c * 0.25, z0), (c * (rr - 0.1) + s * 0.25, s * (rr - 0.1) - c * 0.25, z0),
                                  (c * (rr + 0.25) - s * 0.25, s * (rr + 0.25) + c * 0.25, z1 - 0.25),
                                  (c * (rr + 0.25) + s * 0.25, s * (rr + 0.25) - c * 0.25, z1 - 0.25),
                                  (c * (rr - 0.1), s * (rr - 0.1), z1)])
            body = body + leaf
    zt = zc + 2.0 + max(0.2, abacus / 2 * math.sqrt(2) - 1.3)
    sq = abacus / 2
    for sx in (-1, 1):
        for sy in (-1, 1):
            d = np.array([sx, sy]) / math.sqrt(2)
            cc = np.array([sx, sy]) * (sq - 0.3)
            disc = circle((0.0, 0.0), 0.7, 20) ^ rect(-1, -1, 1, 0.0)
            plate = M.extrude(disc, 0.5).translate([0, 0, -0.25])
            A = np.array([[-d[1], 0.0, d[0], cc[0]], [d[0], 0.0, d[1], cc[1]], [0.0, 1.0, 0.0, zt]])
            body = body + plate.transform(A)
    return body


def baluster_squarebellied(h, seg=4):
    """A Renaissance baluster square in plan: a square foot, a square belly swelling out and
    in at 45 degrees, a square neck and a square top block, each stage a chamfered block (the
    Bellosguardo)."""
    def lay(z0, z1, a0, a1):
        return M.hull_points([(x * a0, y * a0, z0) for x in (-1, 1) for y in (-1, 1)] + [(x * a1, y * a1, z1) for x in (-1, 1) for y in (-1, 1)])
    hb = h * 0.42
    parts = [box([-0.55, -0.55, 0.0], [0.55, 0.55, 0.8]), lay(0.79, 1.0, 0.36, 0.36), lay(0.99, hb, 0.36, 0.52),
             lay(hb - 0.01, hb + (0.52 - 0.28), 0.52, 0.28), lay(hb + 0.23, h - 1.2, 0.28, 0.28), lay(h - 1.21, h - 0.81, 0.28, 0.42),
             box([-0.55, -0.55, h - 0.82], [0.55, 0.55, h])]
    return union(parts)


def frieze_archivoltarcade(u0, u1, v_bot, v_top):
    """A loggia arcade: an elliptical arch filling the bay from post to post, an archivolt
    band round it, a pierced roundel in each spandrel and a keystone at the crown (the
    Bellosguardo)."""
    L = u1 - u0
    hh = v_top - v_bot
    rise = min(L / 2, hh - 1.6)
    solid = rect(u0, v_bot, u1, v_top + 0.05)
    hole = arch_cs(u0 + 0.3, u1 - 0.3, v_bot - 1.0, v_bot, rise=rise, seg=32)
    out = solid - hole
    rnd = []
    for x in (u0 + L * 0.13, u1 - L * 0.13):
        rr = min(0.9, hh * 0.12)
        if rr > 0.55:
            rnd.append(circle((x, v_top - rr - 0.9), rr, 16))
    if rnd:
        out = out - cs_union(rnd)
    key = poly([(0.0 + (u0 + u1) / 2 - 0.7, v_bot + rise - 0.6), ((u0 + u1) / 2 + 0.7, v_bot + rise - 0.6),
                ((u0 + u1) / 2 + 1.0, v_top), ((u0 + u1) / 2 - 1.0, v_top)])
    return out + (key ^ solid)


def edge_eggedge(L, z0, zc):
    """Loggia fascia (the Bellosguardo): a fillet over a row of hanging eggs between darts."""
    out = [rect(0.3, zc - 0.5, L - 0.3, zc)]
    pu = 1.6
    n = max(1, int((L - 1.0) / pu))
    u0 = (L - n * pu) / 2
    for k in range(n):
        x = u0 + pu * (k + 0.5)
        out.append(oval((x, zc - 1.05), 0.5, 0.65, 14))
        out.append(poly([(u0 + pu * k - 0.25, zc - 0.45), (u0 + pu * k + 0.25, zc - 0.45), (u0 + pu * k, zc - 1.4)]))
    return cs_union(out) ^ rect(0.3, -1e3, L - 0.3, 1e3), 0.6


def skirt_medallion(reg, d=1.2):
    """A loggia skirt of sunk panels, each holding a raised oval medallion between small
    pilaster strips (the Bellosguardo)."""
    u0, v0, u1, v1 = reg.bounds()
    out = [M.extrude(reg, d * 0.4)]
    pw = 8.0
    n = max(1, int((u1 - u0) / pw))
    p = (u1 - u0) / n
    for k in range(n):
        a, b = u0 + p * k, u0 + p * (k + 1)
        out.append(ext(rect(a, v0, a + 0.8, v1), d * 0.4 - 0.01, d * 0.75))
        c = ((a + b) / 2 + 0.4, (v0 + v1) / 2)
        rx, ry = min(2.2, (b - a) * 0.28), min(1.4, (v1 - v0) * 0.3)
        if rx > 0.9 and ry > 0.7:
            out.append(ext(oval(c, rx, ry, 24) - oval(c, rx - 0.5, ry - 0.5, 20), d * 0.4 - 0.01, d * 0.72))
            out.append(ext(oval(c, rx - 0.85, ry - 0.85, 16), d * 0.4 - 0.01, d * 0.62) if rx > 1.5 and ry > 1.2 else M())
    out.append(ext(rect(u0 - 1, v1 - 0.9, u1 + 1, v1 + 1), d * 0.4 - 0.01, d * 0.75))
    return union(out) ^ M.extrude(reg, d + 0.5)


def chimney_bellosguardo(w=10.0, d=8.0, h=26.0):
    """An Italian stack (comignolo): a plinth, a brick shaft with a sunk round-headed panel on
    each face, a corbelled cap, and on it a little house over the flues: four piers carrying a
    hipped tile roof with a ball at its peak. Prints upright."""
    h = round(h / 0.2) * 0.2
    sh = h - 9.0
    body = box([-w / 2 - 0.5, -d / 2 - 0.5, 0.0], [w / 2 + 0.5, d / 2 + 0.5, 1.6])
    body = body + M.hull_points([(x, y, 1.59) for x in (-w / 2 - 0.5, w / 2 + 0.5) for y in (-d / 2 - 0.5, d / 2 + 0.5)] +
                                [(x, y, 2.1) for x in (-w / 2, w / 2) for y in (-d / 2, d / 2)])
    body = body + box([-w / 2, -d / 2, 0.0], [w / 2, d / 2, sh])
    for (L, D, rot) in ((w, d, 0), (d, w, 90), (w, d, 180), (d, w, 270)):
        pan = O.opening_cs(L - 3.0, sh - 5.0, (L - 3.0) / 2).translate((0.0, 3.0))
        body = body - M.extrude(pan, 0.45).transform(np.array([[1.0, 0, 0, 0], [0, 0, 1.0, D / 2 - 0.44], [0, 1.0, 0, 0]])).rotate([0, 0, rot])
    for k, e in enumerate((0.4, 0.8)):
        z = sh + 0.8 * k
        body = body + M.hull_points([(x, y, z - 0.01) for x in (-w / 2 - e + 0.4, w / 2 + e - 0.4) for y in (-d / 2 - e + 0.4, d / 2 + e - 0.4)] +
                                    [(x, y, z + 0.4) for x in (-w / 2 - e, w / 2 + e) for y in (-d / 2 - e, d / 2 + e)]) + \
            box([-w / 2 - e, -d / 2 - e, z + 0.39], [w / 2 + e, d / 2 + e, z + 0.8])
    zp = sh + 1.6
    body = body + box([-w / 2 - 0.4, -d / 2 - 0.4, zp - 0.01], [w / 2 + 0.4, d / 2 + 0.4, zp + 0.8])
    zq = zp + 0.79
    hp = 3.6
    for sx in (-1, 1):
        for sy in (-1, 1):
            body = body + box([sx * (w / 2 - 0.2) - 0.8, sy * (d / 2 - 0.2) - 0.8, zq], [sx * (w / 2 - 0.2) + 0.8, sy * (d / 2 - 0.2) + 0.8, zq + hp])
    zr = zq + hp - 0.01
    rh = 3.0
    body = body + M.hull_points([(x, y, zr) for x in (-w / 2 - 0.9, w / 2 + 0.9) for y in (-d / 2 - 0.9, d / 2 + 0.9)] +
                                [(x, y, zr + 0.5) for x in (-w / 2 - 0.9, w / 2 + 0.9) for y in (-d / 2 - 0.9, d / 2 + 0.9)] +
                                [(x, 0.0, zr + rh) for x in (-w / 2 + d / 2, w / 2 - d / 2)])
    body = body + _ball(0.8, zr + rh + 0.6, neck=0.5)
    return body


CO.FRIEZE_EXTRA.update(olivebranch=frieze_olivebranch, rosettecoffers=frieze_rosettecoffers, wreathribbons=frieze_wreathribbons)
CO.COURSE_EXTRA.update(guillocheroses=course_guilloche, eggdartfine=course_eggdart)
TW.BRACKET_EXTRA.update(pendantscroll=bracket_pendantscroll)
TW.PIERCED = TW.PIERCED + ("pendantscroll",)
TW.FOUNDATION_EXTRA.update(talusvent=foundation_talusvent)
SH.CORNER_EXTRA.update(bellosguardo=corner_bellosguardo)
PW.POSTS.update(corinthian=post_corinthian)
PW.BALUSTERS.update(squarebellied=(baluster_squarebellied, 1.6))
PW.FRIEZES.update(archivoltarcade=frieze_archivoltarcade)
PW.SKIRTS.update(medallion=skirt_medallion)
FT.EDGE_EXTRA.update(eggedge=edge_eggedge)


# ================================================================== the Chantilly (house 94)
# Châteauesque, 1892: a Loire château brought to an American lawn. A ground storey of fine
# limestone ashlar on a plinth of diamond-point blocks, an upper storey of red brick in header
# bond with tabled stone quoins; a cornice of ermine spots on machicolation corbels; a steep
# slated roof with tall stone wall dormers (lucarnes) stopping at a flat crested top with lead
# fleuron cresting. Two round towers stand on the front corners under candle-snuffer cones with
# lead finials (épis); a basket-arched door between candelabra pilasters; stone cross windows
# below, demi-croisées under shell pediments above; a balustraded terrace across the front.
# The ornament is François I's and Anne de Bretagne's: salamanders, ermines, the knotted cord.

CH_LEVELS = dict(hi=40.0)      # the building sets it: the brick storey's foot over the block's base


def slate_hexbands(k, j):
    """The Chantilly's slating: square slates with every fourth and fifth course hexagonal
    (clipped corners), a double band of honeycomb round the roof."""
    return "hex" if k % 6 in (3, 4) else "square"


def stone_fine(region, datum=0.0, course=2.6, block=7.2, joint=0.32, d=0.3):
    """Fine limestone ashlar (pierre de taille): long blocks broken a third in each course, every
    joint a shallow V (each block bevelled at 45 degrees all round) (the Chantilly)."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    out = []
    k = math.floor((v0 - datum) / course) - 1
    while datum + k * course < v1 + course:
        a, b = datum + k * course + joint / 2, datum + (k + 1) * course - joint / 2
        if b > v0 - 1 and a < v1 + 1:
            u = u0 - block + (k % 3) * block / 3
            while u < u1 + block:
                out.append(chamfer_box(u + joint / 2, a, u + block - joint / 2, b, 0.0, d, c=0.24, bottom=d))
                u += block
        k += 1
    return union(out) ^ M.extrude(region, d + 0.1)


def brick_header(region, datum=0.0, bh=0.8, hw=1.15, mortar=0.45, bed=0.2, d=0.25):
    """Header bond: every brick laid end on, each course broken half a header (the Chantilly's
    upper storey)."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    cells = []
    k = math.floor((v0 - datum) / bh) - 1
    while datum + k * bh < v1:
        v = datum + k * bh
        u = u0 - 2 * hw + (k % 2) * hw / 2
        while u < u1 + hw:
            cells.append(rect(u + mortar / 2, v, u + hw - mortar / 2 + 0.25, v + bh - bed))
            u += hw + 0.25
        k += 1
    return M.extrude(cs_union(cells) ^ region, d)


def corner_chantilly(L, at_start, qa, qb, w=2.4, t=0.65):
    """The Chantilly's corners: on the ashlar storey long and short blocks in its courses; on the
    brick storey tabled stone quoins (a sunk table in every face), long and short in turn."""
    def span(a, b):
        return (a, b) if at_start else (L - b, L - a)
    hi = CH_LEVELS["hi"]
    parts = []
    v, k = qa, 0
    while v < min(qb, hi) - 1.6:
        leg = 4.4 if k % 2 == 0 else 2.6
        top = min(v + 2.4, min(qb, hi) - 0.2)
        a, b = span(-0.5, leg)
        parts.append(chamfer_box(a, v + 0.15, b, top, 0.0, t * 0.7, c=0.24, bottom=t * 0.7, square=("u0",) if at_start else ("u1",)))
        v += 2.6
        k += 1
    v, k = max(qa, hi), 0
    while v < qb - 2.0:
        leg = 4.8 if k % 2 == 0 else 3.0
        top = min(v + 2.6, qb - 0.2)
        a, b = span(-t - 0.3, leg)
        blk = chamfer_box(a, v, b, top, 0.0, t + 0.2, c=0.2, bottom=t + 0.2, square=("u0",) if at_start else ("u1",))
        fa, fb = span(0.6, leg - 0.6)
        if fb - fa > 0.9 and top - v > 1.6:
            blk = blk - ext(rect(min(fa, fb), v + 0.6, max(fa, fb), top - 0.6), t - 0.05, t + 1.0)
        parts.append(blk)
        v += 3.0
        k += 1
    return union(parts) if parts else M()


def foundation_diamondpoint(reg, seed=0):
    """A plinth of diamond-point blocks (each face a low pyramid drawn to a ridge) under a
    bevelled cap (the Chantilly)."""
    b = reg.bounds()
    out = [M.extrude(reg, 0.25)]
    hc = 1.2
    u = b[0] + 0.3
    while u < b[2] - 0.6:
        u1 = min(u + 5.6, b[2] - 0.3)
        v0, v1 = b[1] + 0.3, b[3] - hc - 0.3
        if u1 - u > 1.6 and v1 - v0 > 1.2:
            vm = (v0 + v1) / 2
            r = min((v1 - v0) / 2, 0.8)
            out.append(M.hull_points([(x, y, 0.24) for x in (u, u1) for y in (v0, v1)] +
                                     [(x, vm, 0.24 + r) for x in (u + r, u1 - r)]))
        u = u1 + 0.3
    cap = rect(b[0] - 1, b[3] - hc, b[2] + 1, b[3]) ^ reg
    if not cap.is_empty():
        cb = cap.bounds()
        out.append(M.hull_points([(x, cb[1], 0.24) for x in (cb[0], cb[2])] + [(x, cb[1] + 0.5, 0.75) for x in (cb[0], cb[2])] +
                                 [(x, cb[3], 0.75) for x in (cb[0], cb[2])] + [(x, cb[3], 0.24) for x in (cb[0], cb[2])]))
    return union(out)


# ------------------------------------------------------------------ cornice ornaments
def course_cordelette(L, h, b, pitch, margin, p):
    """The knotted cord (cordelière): a twisted cord of slanting strands, tied every 6 mm in a
    figure-of-eight knot (the Chantilly's storey joint)."""
    cord = rect(0.2, h * 0.32, L - 0.2, h * 0.68)
    pu = 0.8
    strands = cs_union([poly([(u, h * 0.32), (u + 0.35, h * 0.32), (u + 0.75, h * 0.68), (u + 0.4, h * 0.68)])
                        for u in np.arange(0.4, L - 1.0, pu)]) ^ cord
    knots = []
    for u in np.arange(3.0, L - 2.0, 6.0):
        r = h * 0.24
        for dx in (-r * 0.8, r * 0.8):
            knots.append(circle((u + dx, h / 2), r, 16) - circle((u + dx, h / 2), max(0.15, r - 0.42), 12))
    out = [_st(cord, b, 0.2), _st(strands, b + 0.2, 0.18)]
    if knots:
        out.append(_st(cs_union(knots) ^ rect(0.2, 0.05, L - 0.2, h - 0.05), b, 0.45))
    return out


def frieze_salamanders(L, h, b, pitch, margin, pair, half):
    """François I's salamander: in every bay a crowned salamander, its body in an S over a bed
    of flames, its tail curled (the Chantilly's storey joint)."""
    v0, v1 = 0.7, h - 0.7
    hh = v1 - v0
    out = []
    for uc, wd in CO._between(L, pitch, margin, pair, half):
        s = min(wd * 0.42, 5.2)
        if s < 2.4:
            continue
        vb = v0 + hh * 0.42
        body = [(uc - s, vb + 0.2), (uc - s * 0.55, vb + hh * 0.18), (uc - s * 0.1, vb - 0.1), (uc + s * 0.35, vb + hh * 0.16),
                (uc + s * 0.7, vb + hh * 0.3)]
        tail = [(uc - s, vb + 0.2), (uc - s * 1.05, vb + hh * 0.3), (uc - s * 0.85, vb + hh * 0.38)]
        head = oval((uc + s * 0.82, vb + hh * 0.34), 0.55, 0.42, 14)
        crown = cs_union([poly([(uc + s * 0.82 + dx - 0.18, vb + hh * 0.34 + 0.35), (uc + s * 0.82 + dx + 0.18, vb + hh * 0.34 + 0.35),
                                (uc + s * 0.82 + dx, vb + hh * 0.34 + 0.95)]) for dx in (-0.32, 0.0, 0.32)])
        legs = cs_union([stroke([(uc + x, vb + hh * 0.08 + 0.1 * k), (uc + x + 0.3, vb - hh * 0.12)], 0.45) for k, x in
                         enumerate((-s * 0.55, -s * 0.2, s * 0.2, s * 0.5))])
        flames = cs_union([_lens((uc + x, v0 + hh * 0.18), hh * 0.36, 0.6, math.pi / 2 + 0.25 * math.sin(x)) for x in
                           np.linspace(-s * 0.8, s * 0.8, 5)])
        out.append(_st(_clip_v(flames, v0, v1), b, 0.3))
        out.append(_st(_clip_v(stroke(body, 0.75) + stroke(tail, 0.5) + legs, v0, v1), b, 0.42))
        out.append(_st(_clip_v(head + crown, v0, v1), b, 0.5))
    return out, []


def frieze_ermines(L, h, b, pitch, margin, pair, half):
    """Ermine spots strewn in a lozenge net over the frieze, each three dots over a flared
    tail (Anne de Bretagne's ermine; the Chantilly's eave)."""
    v0, v1 = 0.7, h - 0.7
    hh = v1 - v0
    spots = []
    pu, pv = 2.8, max(2.2, hh / 2)
    rows = max(1, int(round(hh / pv)))
    for r in range(rows):
        vc = v0 + hh * (r + 0.5) / rows
        off = (r % 2) * pu / 2
        for u in np.arange(1.2 + off, L - 1.0, pu):
            sp = cs_union([circle((u + dx, vc + 0.55), 0.26, 10) for dx in (-0.42, 0.0, 0.42)] +
                          [poly([(u - 0.25, vc + 0.25), (u + 0.25, vc + 0.25), (u + 0.55, vc - 0.75), (u, vc - 0.45), (u - 0.55, vc - 0.75)])])
            spots.append(sp)
    return [_st(_clip_v(cs_union(spots), v0, v1) ^ rect(0.2, -1, L - 0.2, h + 1), b, 0.4)], []


def frieze_machiarches(L, h, b, pitch, margin, pair, half):
    """A blind arcade of small round arches with a drop under every springing, under a band
    (the Chantilly's towers)."""
    v0, v1 = 0.6, h - 0.6
    pu = 2.6
    n = max(1, int((L - 1.0) / pu))
    u0 = (L - n * pu) / 2
    band = rect(0.2, v1 - 0.8, L - 0.2, v1)
    arches = cs_union([O.opening_cs(pu - 0.6, v1 - 0.8 - v0 - 0.4, (pu - 0.6) / 2).translate((u0 + pu * (k + 0.5), v0 + 0.4))
                       for k in range(n)])
    field = rect(0.2, v0, L - 0.2, v1 - 0.79) - arches
    drops = cs_union([circle((u0 + pu * k, v0 + 0.5), 0.36, 10) for k in range(n + 1)])
    return [_st(band, b, 0.4), _st(field ^ rect(0.2, v0, L - 0.2, v1), b, 0.3), _st(drops ^ rect(0.2, 0, L - 0.2, h), b, 0.4)], []


def bracket_machicolation(h, d, t):
    """A machicolation corbel: three quarter-rounds stepped out one over another (side profile,
    top at v = 0; the Chantilly's eave)."""
    pts = [(0.0, 0.0), (d, 0.0)]
    steps = 3
    for k in range(steps):
        x_out = d * (steps - k) / steps
        x_in = d * (steps - k - 1) / steps
        v_top = -h * k / steps
        v_bot = -h * (k + 1) / steps
        r = min(x_out - x_in, v_top - v_bot)
        for a in np.linspace(0.0, -math.pi / 2, 7):
            pts.append((x_in + r * math.cos(a) + (x_out - x_in - r), v_top + r * math.sin(a) - 0.0))
        pts.append((x_in, v_bot))
    pts.append((0.0, -h))
    return poly(pts)


def lozengechain(L, h):
    """A crest course: a chain of open lozenges on a fillet (the Chantilly's roof and towers)."""
    pu = 2.4
    n = max(1, int((L - 0.6) / pu))
    u0 = (L - n * pu) / 2
    vm = h / 2 + 0.1
    lz = []
    for k in range(n):
        u = u0 + pu * (k + 0.5)
        outer = poly([(u - 1.15, vm), (u, vm + h * 0.42), (u + 1.15, vm), (u, vm - h * 0.42)])
        lz.append(outer - outer.offset(-0.45, MIT, 4.0))
    base = rect(0.2, 0.05, L - 0.2, 0.35)
    return [cs_union(lz + [base]) ^ rect(0.2, 0.05, L - 0.2, h - 0.05)]


def fence_chantilly(L, h):
    """Chantilly cresting (drawn at half size for SE.printable): lead fleurons, each a
    three-lobed bloom on a stem between two scrolls, and between them small trefoils on stalks,
    all on a rail."""
    pitch = 3.4
    n = max(1, int(round(L / pitch)))
    p = L / n
    cells = [rect(0.0, 0.0, L, 0.6), rect(0.0, h * 0.3, L, h * 0.3 + 0.4)]
    for j in range(n + 1):
        u = min(max(p * j, 0.4), L - 0.4)
        cells.append(rect(u - 0.25, 0.0, u + 0.25, h - 1.4))
        cells.append(_lens((u, h - 0.85), 1.6, 0.75, math.pi / 2))
        cells.append(_lens((u - 0.45, h - 1.25), 1.1, 0.5, math.pi / 2 + 0.7))
        cells.append(_lens((u + 0.45, h - 1.25), 1.1, 0.5, math.pi / 2 - 0.7))
        if j < n:
            m = p * j + p / 2
            cells.append(rect(m - 0.25, h * 0.3, m + 0.25, h * 0.62))
            cells.append(_trefoil((m, h * 0.62 + 0.35), 0.32))
            for sg in (-1, 1):
                cells.append(stroke([(m + sg * 0.3, 0.55), (m + sg * 0.95, h * 0.18), (m + sg * 0.55, h * 0.3)], 0.42))
    return cs_union(cells) ^ rect(0.0, 0.0, L, h + 1.0)


def fence_chantilly_terrace(L, h):
    """The terrace's stone parapet seen face on (printed flat, full size): a plinth and a capped
    rail, square dies every 15 mm or so, and between them squares each pierced with a
    quatrefoil, Gothic fashion."""
    nseg = max(1, int(round(L / 15.0)))
    seg = L / nseg
    cells = [rect(0.0, 0.0, L, 1.0), rect(0.0, h - 1.2, L, h - 0.4), rect(0.0, h - 0.41, L, h)]
    for j in range(nseg + 1):
        u = min(max(seg * j, 1.1), L - 1.1)
        cells.append(rect(u - 1.1, 0.0, u + 1.1, h + 0.5))
        cells.append(poly([(u - 1.1, h + 0.49), (u + 1.1, h + 0.49), (u, h + 1.6)]))
        if j < nseg:
            a, b = u + 1.1, min(max(seg * (j + 1), 1.1), L - 1.1) - 1.1
            field = rect(a, 0.95, b, h - 1.15)
            s = h - 2.15
            nq = max(1, int(round((b - a) / (s + 0.2))))
            qw = (b - a) / nq
            holes = []
            for k in range(nq):
                c = (a + qw * (k + 0.5), (0.95 + h - 1.15) / 2)
                r = min(qw, s) * 0.2
                if r > 0.5:
                    holes.append(_quatrefoil(c, r, 14))
            cells.append(field - cs_union(holes) if holes else field)
    return cs_union(cells) ^ rect(0.0, 0.0, L, h + 1.7)


def finial_epi(h=12.0):
    """A lead épi: a moulded base, a gadrooned bulb, a collar, a vase and a spike carrying a
    ball (the Chantilly's towers and lucarnes)."""
    prof = [(0.0, 0.0), (1.5, 0.0), (1.5, 0.5), (1.0, 1.0), (0.7, 1.4), (1.3, 2.0), (1.45, 2.8), (1.2, 3.6), (0.6, 4.2), (0.9, 4.5),
            (0.9, 4.8), (0.5, 5.1), (0.85, 5.8), (0.95, 6.6), (0.6, 7.3), (0.4, 7.6), (0.0, 7.6)]
    body = PW._revolve(prof, 24)
    body = body + M.cylinder(h - 7.5, 0.45, 0.35, 12).translate([0, 0, 7.5])
    return body + _ball(0.7, 7.5 + (h - 7.5) * 0.6, neck=0.4)


# ------------------------------------------------------------------ windows and doors
def _larmier(half, v, A=1.0, drop=2.4):
    """A dripstone over a head: a moulded label across it that turns down at each end into a
    short return ending on a carved boss."""
    out = [MD.run(-half - 0.6, half + 0.6, v + 1.1, MD.CROWN, 1.1, up=False)]
    for sg in (-1, 1):
        x = sg * (half + 0.1)
        out.append(ext(rect(x - 0.5, v - drop, x + 0.5, v + 0.02), 0.0, 1.0))
        out.append(ext(circle((x, v - drop), 0.6, 14), 0.0, 1.25))
    return out


def window_chantilly_croisee(w=9.6, h=20.0, A=1.0):
    """The ashlar storey's stone cross window (croisée): a mullion and a transom crossing in the
    light, the lower lights barred in three, the upper in diamond leading; a moulded frame, a
    dripstone with carved bosses, an allège panel with a lozenge under the sill."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    inner = plug_cs.offset(-0.6, MIT, 4.0)
    ib = inner.bounds()
    vt = h * 0.64
    body = [ext(plug_cs, -pl, -0.6)]
    cross = cs_union([rect(-0.55, -1, 0.55, h + 1), rect(-w, vt - 0.55, w, vt + 0.55)])
    lights = inner - cross
    bars = [rect(-w, ib[1] + (vt - ib[1]) * k / 3 - RIB / 2, w, ib[1] + (vt - ib[1]) * k / 3 + RIB / 2) for k in (1, 2)]
    top = rect(-w, vt + 0.55, w, ib[3])
    for s in np.arange(-w, w, 2.2):
        bars.append(stroke([(s, vt), (s + 6.0, vt + 6.0)], RIB) ^ top)
        bars.append(stroke([(s + 6.0, vt), (s, vt + 6.0)], RIB) ^ top)
    sash = _glazed(body, lights, pl, cs_union(bars), plug_cs) + [ext(cross ^ plug_cs, -pl, 0.0)]
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             MD.band(op.offset(A, MIT, 4.0), A, MD.ARCHITRAVE, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op)]
    parts += _larmier(w / 2 + A, h + A)
    sw = w / 2 + A + 0.5
    parts.append(MD.run(-sw, sw, 0.0, MD.SILL, 1.0, up=False))
    ap = rect(-w / 2 - 0.2, -3.6, w / 2 + 0.2, -0.79)
    parts.append(ext(ap, 0.0, 0.45))
    lz = poly([(0.0, -3.3), (w * 0.3, -2.2), (0.0, -1.1), (-w * 0.3, -2.2)])
    parts.append(ext(lz - lz.offset(-0.5, MIT, 4.0), 0.44, 0.8))
    return O._one_piece(sash, parts, op, plug_cs, pl, h + A + 2.4, -3.6)


def window_chantilly_upper(w=8.6, h=18.0, A=0.9):
    """The brick storey's demi-croisée: a light parted by a transom, framed by candelabra
    pilasters (a vase of rising leaves sunk up each shaft), under an entablature and a
    triangular pediment holding a scallop shell; a sill on blocks."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    inner = plug_cs.offset(-0.6, MIT, 4.0)
    vt = h * 0.68
    body = [ext(plug_cs, -pl, -0.6)]
    tr = rect(-w, vt - 0.5, w, vt + 0.5)
    sash = _glazed(body, inner - tr, pl, cs_union([rect(-RIB / 2, -1, RIB / 2, vt), rect(-RIB / 2, vt, RIB / 2, h + 1)]), plug_cs) + \
        [ext(tr ^ plug_cs, -pl, -0.2)]
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             MD.band(op.offset(A, MIT, 4.0), A, MD.CASING, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op)]
    pw = 1.8
    xs = w / 2 + A + pw / 2
    for sg in (-1, 1):
        x = sg * xs
        parts.append(ext(rect(x - pw / 2, 0.0, x + pw / 2, h + A), 0.0, 1.0))
        cand = cs_union([oval((x, 2.6), 0.5, 0.7, 12), rect(x - 0.22, 3.2, x + 0.22, h + A - 1.4)] +
                        [_lens((x + sg2 * 0.35, v), 1.0, 0.36, math.pi / 2 - sg2 * 0.5) for v in np.arange(4.4, h + A - 2.0, 2.4) for sg2 in (-1, 1)])
        parts[-1] = parts[-1] - ext(cand ^ rect(x - pw / 2 + 0.3, 1.0, x + pw / 2 - 0.3, h + A - 0.8), 0.75, 1.2)
        parts.append(chamfer_box(x - pw / 2 - 0.3, -0.2, x + pw / 2 + 0.3, 1.4, 0.0, 1.3, c=0.25))
    half = xs + pw / 2 + 0.2
    ve = h + A
    parts.append(ext(rect(-half, ve - 0.01, half, ve + 1.6), 0.0, 1.0))
    vc = ve + 1.6 + 0.9
    parts.append(MD.run(-half - 0.6, half + 0.6, vc, MD.CROWN, 0.9, up=False))
    rise = half * 0.42
    ped = poly([(-half - 0.3, vc - 0.01), (half + 0.3, vc - 0.01), (0.0, vc + rise)])
    parts.append(ext(ped - ped.offset(-0.8, MIT, 4.0), 0.0, 1.0))
    parts.append(ext(ped.offset(-0.8, MIT, 4.0), 0.0, 0.4))
    sc = (0.0, vc + 0.3)
    shell = circle(sc, rise * 0.62, 24) ^ rect(-50, vc + 0.3, 50, 100)
    ribs = cs_union([stroke([sc, (sc[0] + 4 * math.cos(a), sc[1] + 4 * math.sin(a))], 0.32) for a in np.linspace(0.35, math.pi - 0.35, 5)])
    parts.append(ext((shell - ribs) ^ ped.offset(-0.85, MIT, 4.0), 0.39, 0.85))
    sw = half
    parts.append(MD.run(-sw, sw, 0.0, MD.SILL, 1.0, up=False))
    return O._one_piece(sash, parts, op, plug_cs, pl, vc + rise + 0.2, -1.4)


def window_chantilly_tower(w=6.4, h=15.0, A=0.8):
    """A tower light: one light parted by a transom in a chamfered stone frame, under a
    dripstone on bosses; a sill."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    inner = plug_cs.offset(-0.6, MIT, 4.0)
    vt = h * 0.66
    tr = rect(-w, vt - 0.45, w, vt + 0.45)
    sash = _glazed([ext(plug_cs, -pl, -0.6)], inner - tr, pl, None, plug_cs) + [ext(tr ^ plug_cs, -pl, -0.2)]
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             MD.band(op.offset(A, MIT, 4.0), A, MD.CASING, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op)]
    parts += _larmier(w / 2 + A, h + A, drop=2.0)
    parts.append(MD.run(-w / 2 - A - 0.4, w / 2 + A + 0.4, 0.0, MD.SILL, 1.0, up=False))
    return O._one_piece(sash, parts, op, plug_cs, pl, h + A + 2.4, -1.0)


def _basket(w, spring, rise, seg=28):
    """A basket (three-centred) arch head as a semi-ellipse of half-span w/2 and ``rise``,
    over straight jambs from 0 to the springing."""
    pts = [(-w / 2, 0.0)] + [(w / 2 * math.cos(t), spring + rise * math.sin(t)) for t in np.linspace(math.pi, 0.0, seg)] + [(w / 2, 0.0)]
    return poly(pts)


def door_chantilly(w=14.0, h=24.0, A=1.1):
    """The Chantilly's entrance: two leaves of linenfold panels under glazed lights, a basket
    arch over them glazed as a fan; a moulded arch frame between candelabra pilasters, an
    entablature, and over it a little pediment flanked by pinnacles, a shell at its heart."""
    rise = w * 0.28
    spring = h - rise
    op = _basket(w, spring, rise)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    inner = plug_cs.offset(-0.5, MIT, 4.0)
    ib = inner.bounds()
    dh = spring - 0.4
    mid = 0.6
    lw = (ib[2] - ib[0] - mid) / 2
    body, lights = [ext(plug_cs, -pl, -1.0)], []
    ul = ib[0]
    for i in range(2):
        body.append(ext(rect(ul, 0.5, ul + lw, dh), -pl, -0.8))
        pan = rect(ul + 0.7, 1.2, ul + lw - 0.7, dh * 0.5)
        body.append(_panel(pan))
        pb = pan.bounds()
        for x in np.linspace(pb[0] + 0.7, pb[2] - 0.7, 3):
            body.append(ext(rect(x - 0.22, pb[1] + 0.6, x + 0.22, pb[3] - 0.6), -0.5, -0.15))
        lights.append(rect(ul + 0.8, dh * 0.5 + 0.8, ul + lw - 0.8, dh - 0.8))
        ul += lw + mid
    fan = inner ^ rect(-w, dh + 0.5, w, h + 2)
    fc = (0.0, dh + 0.5)
    rays = cs_union([stroke([fc, (fc[0] + w * math.cos(a), fc[1] + w * math.sin(a))], RIB) for a in np.linspace(0.5, math.pi - 0.5, 4)])
    sash = _glazed(body, cs_union(lights) + fan, pl, rays, plug_cs)
    sash.append(ext(rect(-w, dh - 0.01, w, dh + 0.52) ^ plug_cs, -pl, -0.5))
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             MD.band(op.offset(A, MIT, 4.0), A, MD.ARCHITRAVE, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op)]
    pw = 2.0
    xs = w / 2 + A + pw / 2 + 0.2
    vtop = h + A + 0.6
    for sg in (-1, 1):
        x = sg * xs
        shaft = ext(rect(x - pw / 2, 0.0, x + pw / 2, vtop), 0.0, 1.1)
        cand = cs_union([oval((x, 3.0), 0.55, 0.8, 12), rect(x - 0.24, 3.6, x + 0.24, vtop - 1.6)] +
                        [_lens((x + s2 * 0.38, v), 1.1, 0.4, math.pi / 2 - s2 * 0.5) for v in np.arange(5.0, vtop - 2.2, 2.6) for s2 in (-1, 1)])
        parts.append(shaft - ext(cand ^ rect(x - pw / 2 + 0.3, 1.0, x + pw / 2 - 0.3, vtop - 1.0), 0.85, 1.3))
        parts.append(chamfer_box(x - pw / 2 - 0.3, -0.2, x + pw / 2 + 0.3, 2.0, 0.0, 1.5, c=0.25))
    half = xs + pw / 2 + 0.3
    parts.append(ext(rect(-half, vtop - 0.01, half, vtop + 2.0), 0.0, 1.1))
    vc = vtop + 2.0 + 1.0
    parts.append(MD.run(-half - 0.6, half + 0.6, vc, MD.CROWN, 1.0, up=False))
    for sg in (-1, 1):
        x = sg * xs
        parts.append(ext(cs_union([rect(x - 0.7, vc - 0.01, x + 0.7, vc + 1.2), poly([(x - 0.7, vc + 1.19), (x + 0.7, vc + 1.19), (x, vc + 4.2)])]), 0.0, 1.0))
    pr = 3.6
    ped = poly([(-xs + 1.2, vc - 0.01), (xs - 1.2, vc - 0.01), (0.0, vc + pr)])
    parts.append(ext(ped - ped.offset(-0.8, MIT, 4.0), 0.0, 1.0))
    sc = (0.0, vc + 0.3)
    shell = circle(sc, pr * 0.6, 24) ^ rect(-50, vc + 0.3, 50, 100)
    ribs = cs_union([stroke([sc, (sc[0] + 5 * math.cos(a), sc[1] + 5 * math.sin(a))], 0.34) for a in np.linspace(0.35, math.pi - 0.35, 5)])
    parts.append(ext(ped.offset(-0.79, MIT, 4.0), 0.0, 0.4))
    parts.append(ext((shell - ribs) ^ ped.offset(-0.85, MIT, 4.0), 0.39, 0.8))
    parts.append(ext(rect(-xs - 1.4, -0.6, xs + 1.4, 0.01), 0.0, 1.2))
    return O._one_piece(sash, parts, op, plug_cs, pl, vc + 4.4, -0.6)


def door_chantilly_back(w=10.0, h=23.0, A=0.9):
    """The garden door: a single leaf of linenfold panels under a light, a basket-arched fanlight,
    a moulded frame and a dripstone on bosses."""
    rise = w * 0.26
    spring = h - rise
    op = _basket(w, spring, rise)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    inner = plug_cs.offset(-0.5, MIT, 4.0)
    ib = inner.bounds()
    dh = spring - 0.4
    body = [ext(plug_cs, -pl, -1.0), ext(rect(ib[0], 0.5, ib[2], dh), -pl, -0.8)]
    pan = rect(ib[0] + 0.8, 1.2, ib[2] - 0.8, dh * 0.5)
    body.append(_panel(pan))
    pb = pan.bounds()
    for x in np.linspace(pb[0] + 0.8, pb[2] - 0.8, 4):
        body.append(ext(rect(x - 0.22, pb[1] + 0.6, x + 0.22, pb[3] - 0.6), -0.5, -0.15))
    light = rect(ib[0] + 0.9, dh * 0.5 + 0.8, ib[2] - 0.9, dh - 0.8)
    fan = inner ^ rect(-w, dh + 0.5, w, h + 2)
    sash = _glazed(body, light + fan, pl, cs_union([rect(-RIB / 2, dh * 0.5, RIB / 2, h + 2)]), plug_cs)
    sash.append(ext(rect(-w, dh - 0.01, w, dh + 0.52) ^ plug_cs, -pl, -0.5))
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             MD.band(op.offset(A, MIT, 4.0), A, MD.ARCHITRAVE, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op)]
    parts += _larmier(w / 2 + A, h + A, drop=3.0)
    parts.append(ext(rect(-w / 2 - A - 0.4, -0.6, w / 2 + A + 0.4, 0.01), 0.0, 1.0))
    return O._one_piece(sash, parts, op, plug_cs, pl, h + A + 2.4, -0.6)


def addin_chantilly(w=6.0, h=11.0, A=0.8, grand=False):
    """A lucarne for the steep roof (an add-in): a light parted by a cross, a stone frame
    between pilasters with pinnacles, an entablature, and a tall gable with a finial and an
    oculus, scrolls (ailerons) at its foot either side. ``grand``: the frontispiece's, wider,
    with two lights."""
    if grand:
        w, h = w * 1.8, h * 1.15
    op = rect(-w / 2, 0.0, w / 2, h)
    vt = h * 0.64
    bars = cs_union([rect(-w, vt - 0.5, w, vt + 0.5), rect(-0.5, -1.0, 0.5, h + 1.0)])
    pw = 1.4
    xs = w / 2 + A + pw / 2
    ve = h + A
    half = xs + pw / 2 + 0.2
    gh = half * (1.3 if grand else 1.15)
    gable = poly([(-half, ve + 1.39), (half, ve + 1.39), (0.0, ve + 1.4 + gh)])
    body = cs_union([rect(-half, -0.2, half, ve + 1.4), gable])
    parts = [ext(body - op, 0.0, 0.6),
             MD.band(op.offset(A, MIT, 4.0), A, MD.CASING, clip=rect(-30, 0.0, 30, 60) - op)]
    for sg in (-1, 1):
        x = sg * xs
        parts.append(ext(rect(x - pw / 2, -0.2, x + pw / 2, ve + 1.4), 0.0, 1.1))
        parts.append(ext(cs_union([rect(x - 0.45, ve + 1.39, x + 0.45, ve + 2.6), poly([(x - 0.45, ve + 2.59), (x + 0.45, ve + 2.59), (x, ve + 4.6)])]), 0.0, 1.0))
        sc = cs_union([stroke([(sg * (half + 0.2), -0.2), (sg * (half + 1.6), ve * 0.35), (sg * (half + 0.7), ve * 0.6), (sg * (half - 0.1), ve * 0.62)], 0.6),
                       circle((sg * (half + 1.6), ve * 0.35), 0.55, 12)])
        parts.append(ext(sc, 0.0, 0.8))
    parts.append(ext(rect(-half, ve - 0.01, half, ve + 1.4), 0.0, 1.0))
    parts.append(ext(gable - gable.offset(-0.75, MIT, 4.0), 0.0, 1.0))
    oc = (0.0, ve + 1.4 + gh * 0.36)
    ro = min(1.2, gh * 0.2)
    parts.append(ext(circle(oc, ro + 0.5, 20) - circle(oc, ro, 18), 0.0, 1.0))
    parts.append(ext(cs_union([rect(-0.4, ve + 1.4 + gh - 1.2, 0.4, ve + 1.4 + gh + 0.8), _trefoil((0.0, ve + 1.4 + gh + 1.2), 0.45)]), 0.0, 1.0))
    sw = half
    parts.append(MD.run(-sw, sw, 0.0, MD.SILL, 1.0, up=False))
    parts = [p - ext(op, -1.0, 5.0) for p in parts]
    outline = body.offset(-0.4, MIT, 4.0) ^ rect(-50, 0.2, 50, 100)
    return dict(light=op, bars=bars, frame=parts, outline=outline, top=ve + 1.4 + gh + 1.8, bottom=-1.0)


def chimney_chantilly(w=11.0, d=8.0, h=30.0):
    """A château stack: a stone shaft with a sunk panel holding a raised lozenge on each face, a
    moulded cornice, an attic band arcaded with little round arches, and a capping slab."""
    h = round(h / 0.2) * 0.2
    sh = h - 6.0
    body = box([-w / 2, -d / 2, 0.0], [w / 2, d / 2, sh])
    for (L, D, rot) in ((w, d, 0), (d, w, 90), (w, d, 180), (d, w, 270)):
        T = np.array([[1.0, 0, 0, 0], [0, 0, 1.0, D / 2], [0, 1.0, 0, 0]])
        pan = rect(-L / 2 + 1.3, 3.0, L / 2 - 1.3, sh - 2.0)
        body = body - (M.extrude(pan, 0.5).translate([0, 0, -0.49]).transform(T)).rotate([0, 0, rot])
        lzw = (L - 2.6) * 0.42
        lc = (sh + 1.0) / 2
        lz = poly([(0.0, lc - lzw * 1.6), (lzw, lc), (0.0, lc + lzw * 1.6), (-lzw, lc)])
        body = body + (M.extrude(lz ^ pan.offset(-0.4, MIT, 4.0), 0.4).translate([0, 0, -0.5]).transform(T)).rotate([0, 0, rot])
    def ring(e0, e1, z0, z1):
        return M.hull_points([(x, y, z0) for x in (-w / 2 - e0, w / 2 + e0) for y in (-d / 2 - e0, d / 2 + e0)] +
                             [(x, y, z1) for x in (-w / 2 - e1, w / 2 + e1) for y in (-d / 2 - e1, d / 2 + e1)])
    body = body + ring(0.0, 0.8, sh - 0.01, sh + 0.8) + ring(0.8, 0.8, sh + 0.79, sh + 1.4)
    za = sh + 1.39
    att = box([-w / 2 - 0.3, -d / 2 - 0.3, za], [w / 2 + 0.3, d / 2 + 0.3, za + 3.2])
    for (L, D, rot) in ((w + 0.6, d + 0.6, 0), (d + 0.6, w + 0.6, 90), (w + 0.6, d + 0.6, 180), (d + 0.6, w + 0.6, 270)):
        n = max(2, int(L / 2.4))
        arches = cs_union([O.opening_cs(L / n - 0.8, 2.2, (L / n - 0.8) / 2).translate((-L / 2 + L * (k + 0.5) / n, 0.5)) for k in range(n)])
        T = np.array([[1.0, 0, 0, 0], [0, 0, 1.0, D / 2], [0, 1.0, 0, za]])
        att = att - (M.extrude(arches, 0.4).translate([0, 0, -0.39]).transform(T)).rotate([0, 0, rot])
    body = body + att + ring(0.3, 1.0, za + 3.19, za + 3.9) + ring(1.0, 1.0, za + 3.89, za + 4.6)
    return body


CO.FRIEZE_EXTRA.update(salamanders=frieze_salamanders, ermines=frieze_ermines, machiarches=frieze_machiarches)
CO.COURSE_EXTRA.update(cordelette=course_cordelette)
TW.BRACKET_EXTRA.update(machicolation=bracket_machicolation)
TW.FOUNDATION_EXTRA.update(diamondpoint=foundation_diamondpoint)
SH.CORNER_EXTRA.update(chantilly=corner_chantilly)


# ================================================================== the Vanderlyn (house 95)
# Beaux-Arts, 1902: a white palace for a Gilded Age fortune. A podium, a ground storey of
# deep V-jointed rustication pierced by round-arched French windows under scrolled keys, an upper
# storey of buff brick in English cross bond between colossal pilasters, its windows balconied
# under segmental pediments; a cornice of bucrania and garlands on garland consoles, carrying a
# balustrade of bottle balusters between pedestals with balls, and behind it a copper mansard
# with oeils-de-boeuf, a crested deck with bronze anthemion cresting and, at the centre, a ribbed
# dome on a drum of oculi under a lantern. A colossal portico of four fluted Composite columns
# rises through both storeys to a triglyph entablature and a pediment with a cartouche and
# garlands, urns and a palmette at its corners.

VL_LEVELS = dict(hi=40.0)      # the building sets it: the brick storey's foot over the block's base


def slate_copper(k, j):
    """The Vanderlyn's copper: square copper shingles, every seventh course clipped into a
    band of hexagons."""
    return "hex" if k % 7 == 3 else "square"


def rusticated_vjoint(region, datum=0.0, course=2.8, block=8.4, joint=0.8, d=0.45):
    """Rustication with deep V joints both ways: every block a flat face bevelled back 45
    degrees to the joint, long blocks broken half (the Vanderlyn's ground storey)."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    out = []
    k = math.floor((v0 - datum) / course) - 1
    while datum + k * course < v1 + course:
        a, b = datum + k * course + 0.05, datum + (k + 1) * course - 0.05
        if b > v0 - 1 and a < v1 + 1:
            u = u0 - block + (k % 2) * block / 2
            while u < u1 + block:
                out.append(chamfer_box(u + 0.05, a, u + block - 0.05, b, 0.0, d, c=joint / 2, bottom=d))
                u += block
        k += 1
    return union(out) ^ M.extrude(region, d + 0.1)


def brick_englishcross(region, datum=0.0, bl=2.4, bh=0.8, mortar=0.45, bed=0.2, d=0.25):
    """English cross bond: courses of stretchers and of headers in turn, every other stretcher
    course broken half a brick, so the joints form crosses (the Vanderlyn's buff brick)."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    cells = []
    k = math.floor((v0 - datum) / bh) - 1
    while datum + k * bh < v1:
        v = datum + k * bh
        top = v + bh - bed
        if k % 2 == 0:
            step, off = bl, (bl / 2 if (k // 2) % 2 else 0.0)
        else:
            step, off = bl / 2, bl / 4
        u = u0 - 2 * bl + off
        while u < u1 + bl:
            cells.append(rect(u + mortar / 2, v, u + step - mortar / 2, top))
            u += step
        k += 1
    return M.extrude(cs_union(cells) ^ region, d)


def corner_vanderlyn(L, at_start, qa, qb, w=2.4, t=0.65):
    """The Vanderlyn's corners: on the rusticated storey the V-jointed blocks turning the
    corner; on the brick storey a colossal pilaster (three sunk flutes, a base, a capital block
    with two volute bosses)."""
    def span(a, b):
        return (a, b) if at_start else (L - b, L - a)
    hi = VL_LEVELS["hi"]
    parts = []
    v = qa
    while v < min(qb, hi) - 1.4:
        a, b = span(-0.45, 4.2)
        top = min(v + 2.7, min(qb, hi) - 0.1)
        parts.append(chamfer_box(a, v + 0.05, b, top, 0.0, 0.45, c=0.4, bottom=0.45, square=("u0",) if at_start else ("u1",)))
        v += 2.8
    z0 = max(qa, hi)
    if qb - z0 > 8.0:
        pw = 3.2
        a, b = span(0.0, pw)
        shaft = box([a, z0, 0.0], [b, qb, t + 0.15])
        for f in (0.25, 0.5, 0.75):
            fa, fb = span(pw * f - 0.22, pw * f + 0.22)
            shaft = shaft - box([fa, z0 + 3.0, t - 0.1], [fb, qb - 3.4, t + 0.5])
        parts.append(shaft)
        pa, pb = span(-0.3, pw + 0.3)
        parts.append(chamfer_box(pa, z0, pb, z0 + 2.0, 0.0, t + 0.5, c=0.2, bottom=t + 0.5))
        parts.append(chamfer_box(pa, qb - 2.6, pb, qb, 0.0, t + 0.6, c=0.25, bottom=t + 0.6))
        for f in (0.2, 0.8):
            x = span(pw * f, pw * f)[0]
            parts.append(ext(circle((x, qb - 1.5), 0.45, 12), t + 0.59, t + 0.9))
    return union(parts) if parts else M()


def foundation_dadopodium(reg, seed=0):
    """A podium: a moulded base (a torus over a plinth), a dado sunk in long panels, a cyma
    cap (the Vanderlyn)."""
    b = reg.bounds()
    hgt = b[3] - b[1]
    out = [M.extrude(reg, 0.3)]
    base = rect(b[0] - 1, b[1], b[2] + 1, b[1] + 1.6) ^ reg
    if not base.is_empty():
        bb = base.bounds()
        out.append(M.hull_points([(x, bb[1], 0.0) for x in (bb[0], bb[2])] + [(x, bb[1], 0.9) for x in (bb[0], bb[2])] +
                                 [(x, bb[3] - 0.4, 0.9) for x in (bb[0], bb[2])] + [(x, bb[3] + 0.3, 0.29) for x in (bb[0], bb[2])]))
    cap = rect(b[0] - 1, b[3] - 1.4, b[2] + 1, b[3]) ^ reg
    if not cap.is_empty():
        cb = cap.bounds()
        out.append(M.hull_points([(x, cb[1] - 0.5, 0.29) for x in (cb[0], cb[2])] + [(x, cb[1] + 0.4, 0.95) for x in (cb[0], cb[2])] +
                                 [(x, cb[3], 0.95) for x in (cb[0], cb[2])] + [(x, cb[3], 0.29) for x in (cb[0], cb[2])]))
    body = union(out)
    if hgt > 5.0:
        u = b[0] + 1.6
        while u < b[2] - 4.0:
            u1 = min(u + 12.0, b[2] - 1.6)
            pan = rect(u, b[1] + 2.4, u1, b[3] - 2.4) ^ reg
            if not pan.is_empty() and pan.area() > 4.0:
                body = body - ext(pan, 0.12, 1.0)
            u = u1 + 1.6
    return body


# ------------------------------------------------------------------ cornice ornaments
def course_rosettebeads(L, h, b, pitch, margin, p):
    """Small rosettes between pairs of beads (the Vanderlyn's storey joint and eave)."""
    pu = 2.8
    n = max(1, int((L - 0.6) / pu))
    u0 = (L - n * pu) / 2
    ros, beads = [], []
    for k in range(n):
        c = (u0 + pu * (k + 0.5), h / 2)
        r = min(0.62, h * 0.32)
        ros.append(cs_union([circle((c[0] + r * 0.55 * math.cos(a), c[1] + r * 0.55 * math.sin(a)), r * 0.45, 10)
                             for a in np.linspace(0, 2 * math.pi, 6, endpoint=False)]))
        for dx in (-0.95, 0.95):
            beads.append(oval((c[0] + dx, h / 2), 0.26, 0.38, 10))
    clip = rect(0.2, 0.05, L - 0.2, h - 0.05)
    return [_st(rect(0.2, 0.2, L - 0.2, h - 0.2), b, 0.18), _st(cs_union(ros) ^ clip, b + 0.18, 0.32),
            _st(cs_union(beads) ^ clip, b + 0.18, 0.25)]


def frieze_anthemion(L, h, b, pitch, margin, pair, half):
    """The anthemion: palmettes (fans of pointed leaves) and inverted lotus in turn, linked by
    S-scrolls (the Vanderlyn's storey joint)."""
    v0, v1 = 0.7, h - 0.7
    hh = v1 - v0
    pu = max(4.0, hh * 1.2)
    n = max(1, int((L - 1.0) / pu))
    u0 = (L - n * pu) / 2
    pal, lot, scr = [], [], []
    for k in range(n):
        u = u0 + pu * (k + 0.5)
        if k % 2 == 0:
            base = (u, v0 + 0.3)
            for a in np.linspace(-0.9, 0.9, 5):
                Lf = hh * (0.62 if abs(a) > 0.5 else 0.78)
                pal.append(_lens((base[0] + Lf * 0.5 * math.sin(a), base[1] + Lf * 0.5 * math.cos(a)), Lf, 0.55, math.pi / 2 - a))
            pal.append(circle(base, 0.5, 12))
        else:
            top = (u, v1 - 0.3)
            for a in (-0.55, 0.0, 0.55):
                Lf = hh * 0.6
                lot.append(_lens((top[0] + Lf * 0.5 * math.sin(a), top[1] - Lf * 0.5 * math.cos(a)), Lf, 0.6, -math.pi / 2 + a))
        if k < n - 1:
            x0, x1 = u + pu * 0.18, u + pu * 0.82
            scr.append(stroke([(x0, v0 + hh * 0.3), ((x0 + x1) / 2, v0 + hh * 0.15), ((x0 + x1) / 2, v0 + hh * 0.85), (x1, v0 + hh * 0.7)], 0.45))
    clip = rect(0.2, v0, L - 0.2, v1)
    out = []
    if scr:
        out.append(_st(cs_union(scr) ^ clip, b, 0.3))
    if pal:
        out.append(_st(cs_union(pal) ^ clip, b, 0.42))
    if lot:
        out.append(_st(cs_union(lot) ^ clip, b, 0.42))
    return out, []


def frieze_bucrania(L, h, b, pitch, margin, pair, half):
    """Bucrania and garlands: at every station an ox skull with curling horns, between them a
    garland of husks hung from ribbons (the Vanderlyn's eave)."""
    v0, v1 = 0.7, h - 0.7
    hh = v1 - v0
    out = []
    for u in CO._us(L, pitch, margin, 0.0):
        if not 1.6 < u < L - 1.6:
            continue
        sk = poly([(u - 0.75, v1 - 1.0), (u + 0.75, v1 - 1.0), (u + 0.45, v0 + hh * 0.3), (u, v0 + hh * 0.18), (u - 0.45, v0 + hh * 0.3)])
        horns = cs_union([stroke([(u + sg * 0.6, v1 - 1.0), (u + sg * 1.4, v1 - 0.6), (u + sg * 1.5, v1 - 1.5), (u + sg * 1.15, v1 - 1.7)], 0.42)
                          for sg in (-1, 1)])
        eyes = cs_union([circle((u + sg * 0.32, v1 - 1.6), 0.2, 8) for sg in (-1, 1)])
        out.append(_st(_clip_v(horns, v0, v1), b, 0.35))
        out.append(_st(_clip_v(sk, v0, v1) - eyes, b, 0.55))
    for uc, wd in CO._between(L, pitch, margin, pair, half):
        if wd < 4.0:
            continue
        a, c = uc - wd / 2 + 1.6, uc + wd / 2 - 1.6
        g = swag(a, c, v1 - 1.0, hh * 0.45, width=0.9)
        husks = cs_union([circle((a + (c - a) * t_, v1 - 1.0 - hh * 0.45 * (1 - (2 * t_ - 1) ** 2)), 0.42, 10) for t_ in np.linspace(0.15, 0.85, 6)])
        drop = cs_union([circle((uc, v1 - 1.0 - hh * 0.45 - 0.5 - 0.6 * k), 0.38 - 0.06 * k, 10) for k in range(2)])
        out.append(_st(_clip_v(g, v0, v1), b, 0.3))
        out.append(_st(_clip_v(husks + drop, v0, v1), b + 0.3, 0.2))
    return out, []


def bracket_garlandconsole(h, d, t):
    """A console with a garland: an S of a big scroll at the wall and a small one at the soffit,
    and a drop of three husks hanging from the big scroll (side profile, top at v = 0; the
    Vanderlyn)."""
    rb = min(1.0, h * 0.24, d * 0.3)
    rs = min(0.55, h * 0.13)
    cb = (rb + 0.2, -h + rb + 1.5)
    body = poly([(0.0, 0.0), (d, 0.0), (d, -rs * 2), (cb[0] + rb * 0.7, cb[1] + rb * 0.8), (cb[0], cb[1] - rb), (0.0, cb[1] - rb)])
    husks = cs_union([circle((cb[0] - 0.2, cb[1] - rb - 0.25 - 0.55 * k), 0.38 - 0.04 * k, 10) for k in range(3)] +
                     [rect(cb[0] - 0.42, cb[1] - rb - 1.4, cb[0] + 0.02, cb[1] - rb + 0.01)])
    prof = cs_union([body, circle(cb, rb, 18), circle((d - rs, -rs), rs, 12), husks])
    return prof - circle(cb, rb * 0.42, 12)


def anthemionlets(L, h):
    """A crest course: little palmettes on a fillet, one every 2.6 mm (the Vanderlyn's deck
    and drum)."""
    pu = 2.6
    n = max(1, int((L - 0.6) / pu))
    u0 = (L - n * pu) / 2
    cells = [rect(0.2, 0.05, L - 0.2, 0.45)]
    for k in range(n):
        u = u0 + pu * (k + 0.5)
        for a in (-0.65, 0.0, 0.65):
            Lf = h * 0.62
            cells.append(_lens((u + Lf * 0.45 * math.sin(a), 0.4 + Lf * 0.45 * math.cos(a)), Lf, 0.5, math.pi / 2 - a))
    return [cs_union(cells) ^ rect(0.2, 0.05, L - 0.2, h - 0.05)]


def fence_vanderlyn(L, h):
    """Vanderlyn cresting (drawn at half size for SE.printable): bronze anthemion: tall palmette
    fans on stems and small lotus buds in turn, linked low by S-scrolls, on a rail."""
    pitch = 3.4
    n = max(1, int(round(L / pitch)))
    p = L / n
    cells = [rect(0.0, 0.0, L, 0.6)]
    for j in range(n + 1):
        u = min(max(p * j, 0.4), L - 0.4)
        cells.append(rect(u - 0.25, 0.0, u + 0.25, h * 0.5))
        for a in (-0.7, -0.35, 0.0, 0.35, 0.7):
            Lf = h * 0.48
            cells.append(_lens((u + Lf * 0.45 * math.sin(a), h * 0.48 + Lf * 0.45 * math.cos(a)), Lf, 0.5, math.pi / 2 - a))
        if j < n:
            m = p * j + p / 2
            cells.append(rect(m - 0.25, 0.0, m + 0.25, h * 0.45))
            cells.append(_lens((m, h * 0.5), h * 0.28, 0.6, math.pi / 2))
            for sg in (-1, 1):
                cells.append(stroke([(m + sg * 0.25, h * 0.2), (m + sg * 0.9, h * 0.32), (m + sg * 1.2, h * 0.16)], 0.42))
    return cs_union(cells) ^ rect(0.0, 0.0, L, h + 1.0)


def fence_vanderlyn_balustrade(L, h):
    """The eave balustrade seen face on (printed flat, full size): a plinth, a capped rail,
    pedestals every 18 mm or so with sunk panels and balls on plinths, bottle balusters."""
    nseg = max(1, int(round(L / 18.0)))
    seg = L / nseg
    cells = [rect(0.0, 0.0, L, 1.0), rect(0.0, h - 1.1, L, h - 0.4), rect(0.0, h - 0.41, L, h)]
    for j in range(nseg + 1):
        u = min(max(seg * j, 1.2), L - 1.2)
        ped = rect(u - 1.2, 0.0, u + 1.2, h + 0.5)
        cells.append(ped - rect(u - 0.55, 1.6, u + 0.55, h - 1.6))
        cells.append(rect(u - 0.8, h + 0.49, u + 0.8, h + 1.0))
        cells.append(circle((u, h + 1.75), 0.8, 16))
        if j < nseg:
            a, b = u + 1.2, min(max(seg * (j + 1), 1.2), L - 1.2) - 1.2
            nb = max(1, int((b - a) / 1.6))
            for k in range(nb):
                x = a + (b - a) * (k + 0.5) / nb
                lo, hi = 0.95, h - 1.05
                cells.append(cs_union([rect(x - 0.27, lo, x + 0.27, hi), oval((x, lo + (hi - lo) * 0.3), 0.52, (hi - lo) * 0.24, 14),
                                       rect(x - 0.45, hi - 0.5, x + 0.45, hi)]))
    return cs_union(cells) ^ rect(0.0, 0.0, L, h + 2.6)


def dome_vanderlyn(r=13.0, hd=12.0, hdrum=11.0, ribs=12):
    """The central dome as one part, printed upright: a drum (pilaster strips between oculi
    sunk in its wall, a cornice), a ribbed dome, and a lantern of arched lights under a little
    dome; the finial is added by the building. Local: centred on the axis, foot at z = 0."""
    drum = M.cylinder(hdrum, r, r, 64)
    for k in range(ribs):
        a = 2 * math.pi * (k + 0.5) / ribs
        oc = M.cylinder(2.0, 1.5, 1.5, 20).rotate([0, 90, 0]).translate([r - 0.6, 0, hdrum * 0.55]).rotate([0, 0, math.degrees(a)])
        drum = drum - oc + (M.cylinder(1.2, 1.0, 1.0, 16).rotate([0, 90, 0]).translate([r - 1.3, 0, hdrum * 0.55]).rotate([0, 0, math.degrees(a)])
                            - M.cylinder(3.0, 0.55, 0.55, 12).rotate([0, 90, 0]).translate([r - 2.0, 0, hdrum * 0.55]).rotate([0, 0, math.degrees(a)]))
        pil = box([r - 0.2, -0.7, 0.0], [r + 0.4, 0.7, hdrum]).rotate([0, 0, math.degrees(2 * math.pi * k / ribs)])
        drum = drum + pil
    drum = drum + PW._revolve([(0.0, hdrum - 1.4), (r + 0.4, hdrum - 1.4), (r + 1.0, hdrum - 0.8), (r + 1.0, hdrum), (0.0, hdrum)], 64)
    prof = [(0.0, hdrum - 0.01), (r + 0.4, hdrum - 0.01)]
    for t in np.linspace(0.0, math.pi / 2, 12)[1:]:
        prof.append(((r + 0.4) * math.cos(t), hdrum + hd * math.sin(t)))
    dome = PW._revolve(prof, 64)
    rib_body = PW._revolve([(0.0, hdrum)] + [((r + 0.75) * math.cos(t), hdrum + (hd + 0.35) * math.sin(t)) for t in np.linspace(0.0, math.pi / 2, 12)], 64)
    for k in range(ribs):
        sl = box([0.0, -0.4, hdrum], [r + 2.0, 0.4, hdrum + hd + 2.0]).rotate([0, 0, math.degrees(2 * math.pi * k / ribs)])
        dome = dome + (rib_body ^ sl)
    zl = hdrum + hd - 0.6
    rl = 3.4
    lan = M.cylinder(5.0, rl, rl, 32).translate([0, 0, zl])
    for k in range(6):
        a = math.degrees(2 * math.pi * k / 6)
        win = (O.opening_cs(1.6, 3.2, 0.8))
        lan = lan - M.extrude(win, 1.4).translate([0, 0, -0.7]).transform(np.array([[1.0, 0, 0, 0], [0, 0, 1.0, rl], [0, 1.0, 0, zl + 0.8]])).rotate([0, 0, a + 90])
    lan = lan + PW._revolve([(0.0, zl + 4.99), (rl + 0.6, zl + 4.99), (rl + 0.6, zl + 5.6), (rl * 0.8, zl + 6.6), (rl * 0.45, zl + 7.4), (0.0, zl + 7.6)], 32)
    return drum + dome + lan, zl + 7.6


# ------------------------------------------------------------------ windows and doors
def _scrollkey(v0, h=3.2, w0=1.0, w1=1.8, d=1.4):
    """A scrolled keystone: a console standing on the arch's crown, its face rolled into a scroll
    at the top and dressed with a leaf."""
    body = poly([(-w0 / 2, v0), (w0 / 2, v0), (w1 / 2, v0 + h), (-w1 / 2, v0 + h)])
    out = [ext(body, 0.0, d)]
    out.append(ext(circle((0.0, v0 + h - 0.5), 0.5, 14), d - 0.01, d + 0.35))
    out.append(ext(_lens((0.0, v0 + h * 0.4), h * 0.5, 0.6, math.pi / 2), d - 0.01, d + 0.25))
    return out


def window_vanderlyn_ground(w=9.2, h=22.0, A=0.9):
    """The rusticated storey's French window: two casements under a round head of radiating
    bars, an archivolt and a scrolled keystone, a balconette of balusters across its foot."""
    r = w / 2
    spring = h - r
    op = O.opening_cs(w, h, r)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    inner = plug_cs.offset(-0.6, MIT, 4.0)
    body = [ext(plug_cs, -pl, -0.6)]
    fc = (0.0, spring)
    bars = [rect(-0.4, -1.0, 0.4, spring + 0.3), rect(-w, spring - 0.35, w, spring + 0.35)]
    for v in np.linspace(0.0, spring, 4)[1:-1]:
        bars.append(rect(-w, v - RIB / 2, w, v + RIB / 2))
    for a in np.linspace(0.6, math.pi - 0.6, 3):
        bars.append(stroke([fc, (fc[0] + w * math.cos(a), fc[1] + w * math.sin(a))], RIB))
    sash = _glazed(body, inner, pl, cs_union(bars), plug_cs)
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             MD.band(op.offset(A, RND), A, MD.ARCHITRAVE, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op)]
    parts += _scrollkey(h + A - 0.6)
    bal = [rect(-r - A, -0.6, r + A, 0.01), rect(-r - 0.4, 3.4, r + 0.4, 4.0)]
    for x in np.linspace(-r + 0.2, r - 0.2, 6):
        bal.append(cs_union([rect(x - 0.25, -0.1, x + 0.25, 3.5), oval((x, 1.1), 0.45, 0.65, 12)]))
    parts.append(ext(cs_union(bal), 0.0, 0.9))
    return O._one_piece(sash, parts, op, plug_cs, pl, h + A + 2.8, -0.6)


def window_vanderlyn_upper(w=8.8, h=20.0, A=0.9):
    """The brick storey's window: a one-over-one sash in an eared architrave, a frieze with a
    cartouche, a segmental pediment on two consoles; a stone balcony on two big scrolls
    below."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    sash = O.window_insert(w, h, 0, lites=(1, 1), bare=True)["insert"]
    half = w / 2 + A
    outer = cs_union([op.offset(A, MIT, 4.0), rect(-half - 0.7, h - 1.8, half + 0.7, h + A)])
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             MD.band(outer, A + 0.7, MD.ARCHITRAVE, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op)]
    vf = h + A
    parts.append(ext(rect(-half, vf - 0.01, half, vf + 2.4), 0.0, 0.5))
    car = oval((0.0, vf + 1.2), 1.4, 0.9, 20)
    parts.append(ext(car - oval((0.0, vf + 1.2), 0.9, 0.45, 16), 0.49, 0.95))
    parts.append(ext(cs_union([stroke([(sg * 1.3, vf + 1.2), (sg * 2.8, vf + 1.9), (sg * 4.0, vf + 1.0)], 0.45) for sg in (-1, 1)]) ^ rect(-half, vf, half, vf + 2.4), 0.49, 0.85))
    vc = vf + 2.4 + 0.96
    parts.append(MD.run(-half - 1.0, half + 1.0, vc, MD.CROWN, 1.0, up=False))
    seg = arch_cs(-half - 1.0, half + 1.0, vc - 0.01, vc - 0.01, rise=2.2, seg=40)
    parts.append(ext((seg - seg.offset(-0.8, MIT, 4.0)) ^ rect(-50, vc - 0.01, 50, 50), 0.0, 1.1))
    for sg in (-1, 1):
        x = sg * (half + 0.5)
        parts.append(ext(cs_union([rect(x - 0.5, vf - 2.4, x + 0.5, vc - 1.0), circle((x, vf - 2.4), 0.5, 12)]), 0.0, 1.0))
    sw = half + 0.6
    parts.append(MD.run(-sw, sw, 0.0, MD.SILL, 1.2, up=False))
    for sg in (-1, 1):
        x = sg * (half - 0.4)
        parts.append(ext(cs_union([rect(x - 0.6, -3.4, x + 0.6, -1.19), circle((x, -3.4), 0.6, 14)]), 0.0, 1.4))
    bal = [rect(-sw + 0.4, -1.2, sw - 0.4, -0.79)]
    parts.append(ext(cs_union(bal), 0.0, 1.0))
    return O._one_piece([sash], parts, op, plug_cs, O.PLUG, vc + 2.4, -4.0)


def addin_vanderlyn(rx=2.4, ry=3.2, A=0.9):
    """An oeil-de-boeuf for the copper mansard (an add-in): an oval light with a cross of bars
    in a moulded oval frame, a garland hung across its head from two rosettes, a scrolled
    cartouche crest and a sill on a console."""
    c = (0.0, ry + 1.0)
    op = oval(c, rx, ry, 40)
    bars = cs_union([rect(-RIB / 2, -1.0, RIB / 2, 20.0), rect(-10.0, c[1] - RIB / 2, 10.0, c[1] + RIB / 2)])
    rim = oval(c, rx + A + 0.4, ry + A + 0.4, 40) - op
    parts = [ext(rim, 0.0, 0.9)]
    g = swag(-rx - 0.8, rx + 0.8, c[1] + ry * 0.55, 1.1, width=0.7)
    parts.append(ext(g + circle((-rx - 0.8, c[1] + ry * 0.55), 0.55, 12) + circle((rx + 0.8, c[1] + ry * 0.55), 0.55, 12), 0.6, 1.25))
    top = c[1] + ry + A + 0.4
    crest = cs_union([poly([(-1.4, top - 0.5), (1.4, top - 0.5), (0.8, top + 1.6), (-0.8, top + 1.6)]),
                      circle((-1.2, top + 1.3), 0.5, 12), circle((1.2, top + 1.3), 0.5, 12)])
    parts.append(ext(crest, 0.0, 1.0))
    parts.append(MD.run(-rx - 0.8, rx + 0.8, 0.6, MD.SILL, 0.9, up=False))
    parts.append(ext(cs_union([rect(-0.6, -0.9, 0.6, 0.0), circle((0.0, -0.9), 0.6, 12)]), 0.0, 1.0))
    parts = [p - ext(op, -1.0, 5.0) for p in parts]
    outline = (oval(c, rx + A + 0.4, ry + A + 0.4, 40) + rect(-rx - A - 0.4, 0.2, rx + A + 0.4, c[1])).offset(-0.3, RND) ^ rect(-50, 0.2, 50, 100)
    return dict(light=op, bars=bars, frame=parts, outline=outline, top=top + 1.8, bottom=-1.6)


def door_vanderlyn(w=14.0, h=27.0, A=1.2):
    """The Vanderlyn's entrance under the portico: a pair of leaves, each a glazed upper panel
    over a raised one, under a round fanlight of radiating bars; a heavy architrave, and over
    it a broken segmental pediment on consoles with a cartouche in the break."""
    r = w / 2
    op = O.opening_cs(w, h, r)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    spring = h - r
    inner = plug_cs.offset(-0.5, MIT, 4.0)
    ib = inner.bounds()
    dh = spring - 0.4
    mid = 0.6
    lw = (ib[2] - ib[0] - mid) / 2
    body, lights = [ext(plug_cs, -pl, -1.0)], []
    ul = ib[0]
    for i in range(2):
        body.append(ext(rect(ul, 0.5, ul + lw, dh), -pl, -0.8))
        body.append(_panel(rect(ul + 0.7, 1.2, ul + lw - 0.7, dh * 0.38)))
        lights.append(rect(ul + 0.8, dh * 0.38 + 0.8, ul + lw - 0.8, dh - 0.8))
        ul += lw + mid
    fan = inner ^ rect(-w, dh + 0.5, w, h + 2)
    fc = (0.0, dh + 0.5)
    rays = [stroke([fc, (fc[0] + w * math.cos(a), fc[1] + w * math.sin(a))], RIB) for a in np.linspace(0.4, math.pi - 0.4, 6)]
    bars = cs_union(rays + [circle(fc, 1.2, 16) - circle(fc, 1.2 - RIB, 16)] +
                    [rect(ul_ - 0.0, (dh * 0.38 + dh) / 2 - RIB / 2, ul_ + lw, (dh * 0.38 + dh) / 2 + RIB / 2) for ul_ in (ib[0], ib[0] + lw + mid)])
    sash = _glazed(body, cs_union(lights) + fan, pl, bars, plug_cs)
    sash.append(ext(rect(-w, dh - 0.01, w, dh + 0.52) ^ plug_cs, -pl, -0.5))
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             MD.band(op.offset(A, RND), A, MD.ARCHITRAVE, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op)]
    parts += _scrollkey(h + A - 0.6, h=3.4, w0=1.2, w1=2.0)
    half = r + A + 2.4
    for sg in (-1, 1):
        x = sg * (r + A + 1.2)
        parts.append(ext(rect(x - 1.1, 0.0, x + 1.1, spring + 2.0), 0.0, 1.0))
        parts.append(ext(cs_union([rect(x - 0.65, spring + 2.0, x + 0.65, h + 2.0), circle((x, spring + 2.0), 0.65, 12)]), 0.0, 1.3))
    vc = h + A + 3.6
    parts.append(MD.run(-half, half, vc, MD.CROWN, 1.2, up=False))
    seg = arch_cs(-half, half, vc - 0.01, vc - 0.01, rise=3.4, seg=40)
    band = (seg - seg.offset(-1.0, MIT, 4.0)) ^ rect(-50, vc - 0.01, 50, 50)
    parts.append(ext(band - rect(-2.6, vc - 1, 2.6, 50), 0.0, 1.2))
    car = oval((0.0, vc + 2.0), 1.8, 2.2, 24)
    parts.append(ext(car, 0.0, 0.8))
    parts.append(ext(car - car.offset(-0.5, RND), 0.79, 1.3))
    parts.append(ext(rect(-half, -0.6, half, 0.01), 0.0, 1.2))
    return O._one_piece(sash, parts, op, plug_cs, pl, vc + 4.4, -0.6)


def door_vanderlyn_back(w=10.0, h=24.0, A=1.0, rise=1.6):
    """The garden door: one leaf, a glazed upper panel over two raised ones, a segmental
    transom, an architrave under a frieze and cornice on consoles."""
    op = O.opening_cs(w, h, rise)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    inner = plug_cs.offset(-0.5, MIT, 4.0)
    ib = inner.bounds()
    dh = h - rise - 3.4
    gv0 = dh * 0.5
    body = [ext(plug_cs, -pl, -1.0), ext(rect(ib[0], 0.5, ib[2], dh), -pl, -0.8),
            _panel(rect(ib[0] + 0.8, 1.2, ib[2] - 0.8, gv0 * 0.5 - 0.2)), _panel(rect(ib[0] + 0.8, gv0 * 0.5 + 0.2, ib[2] - 0.8, gv0 - 0.8))]
    light = rect(ib[0] + 0.9, gv0, ib[2] - 0.9, dh - 0.8)
    tran = inner ^ rect(-w, dh + 0.5, w, h + 2)
    sash = _glazed(body, light + tran, pl, cs_union([rect(-RIB / 2, gv0, RIB / 2, h + 2)]), plug_cs)
    sash.append(ext(rect(-w, dh - 0.01, w, dh + 0.52) ^ plug_cs, -pl, -0.5))
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             MD.band(op.offset(A, MIT, 4.0), A, MD.ARCHITRAVE, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op)]
    half = w / 2 + A + 0.5
    vf = h + A
    parts.append(ext(rect(-half, vf - 0.01, half, vf + 1.8), 0.0, 0.5))
    vc = vf + 1.8 + 1.1
    parts.append(MD.run(-half - 0.9, half + 0.9, vc, MD.CROWN, 1.1, up=False))
    for sg in (-1, 1):
        x = sg * (half + 0.4)
        parts.append(ext(cs_union([rect(x - 0.5, vf - 2.2, x + 0.5, vc - 1.1), circle((x, vf - 2.2), 0.5, 12)]), 0.0, 1.0))
    parts.append(ext(rect(-half, -0.6, half, 0.01), 0.0, 1.0))
    return O._one_piece(sash, parts, op, plug_cs, pl, vc + 0.2, -0.6)


# ------------------------------------------------------------------ the portico
def post_composite(h, collar=None, abacus=7.4, slot=(1.2, 1.0), r=2.9):
    """A colossal Composite column: an Attic base on a plinth, a shaft with entasis cut in
    sixteen flutes, an astragal, a bell wrapped in two rows of acanthus (ribs standing off it),
    an egg band, big Ionic volutes under the corners of a concave abacus (flat-topped plates,
    for the upside-down top) (the Vanderlyn's portico)."""
    zc = h - 7.0
    prof = [(0.0, 1.79), (r + 0.9, 1.79), (r + 0.9, 2.3), (r + 0.5, 2.7), (r + 0.35, 3.1), (r + 0.6, 3.5), (r + 0.25, 3.9), (r, 4.3),
            (r * 1.04, (4.3 + zc) * 0.38), (r * 0.88, zc - 0.4), (r + 0.1, zc - 0.2), (r + 0.1, zc + 0.15), (r * 0.9, zc + 0.4),
            (r + 0.1, zc + 2.6), (r + 0.55, zc + 3.6), (r + 0.85, zc + 4.2)]
    body = PW._revolve(prof, 48) + box([-(r + 1.2), -(r + 1.2), 0.0], [r + 1.2, r + 1.2, 1.8])
    for k in range(16):
        a = 360.0 * (k + 0.5) / 16
        fl = box([r * 0.88 - 0.35, -0.3, 5.0], [r + 0.6, 0.3, zc - 1.6]).rotate([0, 0, a])
        body = body - fl
    body = body + PW._top(h, abacus / 2, zc + 4.2, r + 0.85, slot, seg=48)
    for z0, z1, rr, off in ((zc + 0.4, zc + 2.0, r + 0.15, 0.0), (zc + 1.4, zc + 3.4, r + 0.5, math.pi / 8)):
        for k in range(8):
            a = 2 * math.pi * k / 8 + off
            c, s = math.cos(a), math.sin(a)
            body = body + M.hull_points([(c * (rr - 0.15) - s * 0.4, s * (rr - 0.15) + c * 0.4, z0), (c * (rr - 0.15) + s * 0.4, s * (rr - 0.15) - c * 0.4, z0),
                                         (c * (rr + 0.35) - s * 0.4, s * (rr + 0.35) + c * 0.4, z1 - 0.4),
                                         (c * (rr + 0.35) + s * 0.4, s * (rr + 0.35) - c * 0.4, z1 - 0.4), (c * (rr - 0.15), s * (rr - 0.15), z1)])
    zt = zc + 4.2 + max(0.2, abacus / 2 * math.sqrt(2) - (r + 0.85))
    sq = abacus / 2
    for sx in (-1, 1):
        for sy in (-1, 1):
            d = np.array([sx, sy]) / math.sqrt(2)
            cc = np.array([sx, sy]) * (sq - 0.5)
            disc = circle((0.0, 0.0), 1.3, 24) ^ rect(-2, -2, 2, 0.0)
            plate = M.extrude(disc, 0.6).translate([0, 0, -0.3])
            A = np.array([[-d[1], 0.0, d[0], cc[0]], [d[0], 0.0, d[1], cc[1]], [0.0, 1.0, 0.0, zt]])
            body = body + plate.transform(A)
    return max(body.decompose(), key=lambda c: c.volume())          # (the flutes' ends leave specks)


def baluster_invertedvase(h, seg=18):
    """An inverted vase baluster: a slender stem rising from a ring on a square foot to a
    swelling body high up under a neck and a square top (the Vanderlyn)."""
    prof = [(0.0, 0.8), (0.34, 0.8), (0.34, 1.0), (0.24, 1.3), (0.24, h * 0.4), (0.4, h * 0.52), (0.52, h * 0.62), (0.46, h * 0.72),
            (0.28, h * 0.8), (0.28, h - 1.0), (0.36, h - 0.8)]
    body = PW._revolve(prof, seg)
    return body + box([-0.55, -0.55, 0.0], [0.55, 0.55, 0.81]) + box([-0.55, -0.55, h - 0.81], [0.55, 0.55, h])


def frieze_regulae(u0, u1, v_bot, v_top):
    """A portico's architrave: a fascia under the beam with a regula and six guttae under every
    triglyph above (the Vanderlyn)."""
    cells = [rect(u0, v_top - 1.6, u1, v_top + 0.05)]
    L = u1 - u0
    n = max(1, int(L / 5.0))
    for k in range(n):
        x = u0 + L * (k + 0.5) / n
        cells.append(rect(x - 1.2, v_top - 2.0, x + 1.2, v_top - 1.59))
        cells += [circle((x + dx, v_top - 2.15), 0.28, 8) for dx in np.linspace(-0.95, 0.95, 4)]
    return cs_union(cells)


def edge_triglyphs(L, z0, zc):
    """Portico fascia (the Vanderlyn): a Doric frieze of triglyphs (three bars) and metopes
    each with a rosette, under the crown."""
    out = [rect(0.3, zc - 0.5, L - 0.3, zc)]
    pu = 4.4
    n = max(1, int((L - 1.0) / pu))
    u0 = (L - n * pu) / 2
    for k in range(n + 1):
        x = u0 + pu * k
        out += [rect(x - 1.0 + 0.7 * j, z0 + 0.4, x - 0.6 + 0.7 * j, zc - 0.45) for j in range(3)]
        if k < n:
            c = (x + pu / 2, zc - 0.5 - 0.7)
            out.append(cs_union([circle((c[0] + 0.5 * math.cos(a), c[1] + 0.5 * math.sin(a)), 0.32, 10) for a in np.linspace(0, 2 * math.pi, 6, endpoint=False)]))
    return cs_union(out) ^ rect(0.3, -1e3, L - 0.3, 1e3), 0.6


def skirt_dadopanels(reg, d=1.2):
    """A stylobate skirt: long sunk dado panels between die blocks, a moulded cap (the
    Vanderlyn)."""
    u0, v0, u1, v1 = reg.bounds()
    out = [M.extrude(reg, d * 0.75)]
    pw = 12.0
    n = max(1, int((u1 - u0) / pw))
    p = (u1 - u0) / n
    for k in range(n):
        a, b = u0 + p * k + 1.2, u0 + p * (k + 1) - 1.2
        if b - a > 2.0 and v1 - v0 > 4.0:
            out[0] = out[0] - ext(rect(a, v0 + 1.4, b, v1 - 1.8), d * 0.45, d)
    out.append(ext(rect(u0 - 1, v1 - 1.0, u1 + 1, v1 + 1), d * 0.74, d))
    return union(out) ^ M.extrude(reg, d + 0.5)


def pediment_vanderlyn(w, depth, rise, t=1.2):
    """The portico's pediment, standing on its roof: a raking cornice and a horizontal one with
    dentils, a tympanum holding a cartouche between garlands, acroteria (a palmette at the apex,
    urns at the feet). Local as features.entry_pediment (u across, v up from the porch roof's
    top, w out from the house, the face at w = depth); prints upright on its base."""
    face = poly([(-w / 2, 0.0), (0.0, rise), (w / 2, 0.0)])
    parts = [M.extrude(face, depth)]
    parts.append(ext(face - face.offset(-1.2, MIT, 4.0), depth - 0.01, depth + t))
    parts.append(ext(rect(-w / 2 + 1.0, 0.0, w / 2 - 1.0, 1.4), depth - 0.01, depth + t))
    parts.append(ext(cs_union([rect(x - 0.3, 1.4, x + 0.3, 2.0) for x in np.arange(-w / 2 + 3.0, w / 2 - 2.8, 1.2)]) ^ face.offset(-1.2, MIT, 4.0),
                     depth - 0.01, depth + t * 0.7))
    tym = face.offset(-1.2, MIT, 4.0) ^ rect(-50, 2.0, 50, 50)
    c = (0.0, 2.0 + (rise - 3.2) * 0.42)
    car = oval(c, min(3.2, w * 0.08), min(2.4, (rise - 3.2) * 0.32), 28)
    parts.append(ext(car ^ tym, depth - 0.01, depth + t * 0.6))
    parts.append(ext((car - car.offset(-0.6, RND)) ^ tym, depth + t * 0.59, depth + t))
    for sg in (-1, 1):
        g = swag(sg * 3.6, sg * w * 0.32, c[1] + 0.8, 1.6, width=0.8)
        parts.append(ext(g ^ tym, depth - 0.01, depth + t * 0.65))
    out = union(parts)
    pal = cs_union([_lens((0.0 + 1.6 * math.sin(a), rise + 1.6 * math.cos(a) - 1.0), 2.4, 0.7, math.pi / 2 - a) for a in (-0.6, 0.0, 0.6)] +
                   [rect(-1.0, rise - 1.2, 1.0, rise)])
    out = out + ext(pal, depth - 2.0, depth)
    for sg in (-1, 1):
        out = out + ext(urn_cs(sg * (w / 2 - 1.4), 0.0, 4.6, 2.4), depth - 2.0, depth)
    return out.transform(np.array([[1.0, 0, 0, 0], [0, 0, 1.0, 0], [0, 1.0, 0, 0]]))


def chimney_vanderlyn(w=11.0, d=9.0, h=24.0):
    """A Beaux-Arts stack: a stone shaft with a sunk panel on each face, a cornice, and a cap
    with a small pediment on each face over a capping slab. Prints upright."""
    h = round(h / 0.2) * 0.2
    sh = h - 6.4
    body = box([-w / 2, -d / 2, 0.0], [w / 2, d / 2, sh])
    for (L, D, rot) in ((w, d, 0), (d, w, 90), (w, d, 180), (d, w, 270)):
        T = np.array([[1.0, 0, 0, 0], [0, 0, 1.0, D / 2], [0, 1.0, 0, 0]])
        body = body - (M.extrude(rect(-L / 2 + 1.4, 2.4, L / 2 - 1.4, sh - 1.8), 0.45).translate([0, 0, -0.44]).transform(T)).rotate([0, 0, rot])
    def ring(e0, e1, z0, z1):
        return M.hull_points([(x, y, z0) for x in (-w / 2 - e0, w / 2 + e0) for y in (-d / 2 - e0, d / 2 + e0)] +
                             [(x, y, z1) for x in (-w / 2 - e1, w / 2 + e1) for y in (-d / 2 - e1, d / 2 + e1)])
    body = body + ring(0.0, 0.8, sh - 0.01, sh + 0.8) + ring(0.8, 0.8, sh + 0.79, sh + 1.6)
    zc = sh + 1.59
    body = body + box([-w / 2 + 0.2, -d / 2 + 0.2, zc], [w / 2 - 0.2, d / 2 - 0.2, zc + 2.4])
    for (L, D, rot) in ((w - 0.4, d - 0.4, 0), (d - 0.4, w - 0.4, 90), (w - 0.4, d - 0.4, 180), (d - 0.4, w - 0.4, 270)):
        T = np.array([[1.0, 0, 0, 0], [0, 0, 1.0, D / 2 - 0.01], [0, 1.0, 0, zc + 2.39]])
        ped = poly([(-L / 2, 0.0), (L / 2, 0.0), (0.0, 1.8)])
        body = body + (M.extrude(ped, 0.6).transform(T)).rotate([0, 0, rot])
    body = body + ring(0.0, 0.6, zc + 2.39, zc + 3.2) + ring(0.6, 0.6, zc + 3.19, zc + 4.8)
    return body


CO.FRIEZE_EXTRA.update(anthemionlotus=frieze_anthemion, bucrania=frieze_bucrania)
CO.COURSE_EXTRA.update(rosettebeads=course_rosettebeads)
TW.BRACKET_EXTRA.update(garlandconsole=bracket_garlandconsole)
TW.PIERCED = TW.PIERCED + ("garlandconsole",)
TW.FOUNDATION_EXTRA.update(dadopodium=foundation_dadopodium)
SH.CORNER_EXTRA.update(vanderlyn=corner_vanderlyn)
PW.POSTS.update(composite=post_composite)
PW.BALUSTERS.update(invertedvase=(baluster_invertedvase, 1.6))
PW.FRIEZES.update(regulae=frieze_regulae)
PW.SKIRTS.update(dadopanels=skirt_dadopanels)
FT.EDGE_EXTRA.update(triglyphs=edge_triglyphs)


# ================================================================== the Zenobia (house 96)
# Oriental Revival, 1861: an octagon villa of the kind the Natchez cotton planters dreamed of,
# its walls of ablaq (courses of smooth and of scored stone in turn) below and rope-beaded lap
# above, wrapped on every face by a two-tier gallery of slender Moorish colonnettes, horseshoe
# arches cusped into lobes, mashrabiya railings and a fringe of stars. Over a muqarnas cornice a
# steep octagonal roof rises to a crested deck, and from it a twelve-sided drum of horseshoe
# lights under merlons carries a gilt onion dome with a tulip finial. Windows are horseshoe arches
# in alfiz frames below and paired ajimez lights above; the stacks are little domed turrets.

ZN_LEVELS = dict(hi=40.0)      # the building sets it: the lap storey's foot over the block's base


def _horseshoe(a, vs_jamb, kick=1.18, seg=28):
    """A horseshoe-arch opening: straight jambs 2a apart from v = 0 up to vs_jamb, then a circle of
    radius kick*a whose centre stands over the jambs, so the arch swells past them before it
    closes. Returns (outline, centre v, radius)."""
    R_ = a * kick
    vc = vs_jamb + math.sqrt(R_ * R_ - a * a)
    th0 = math.atan2(vs_jamb - vc, a)
    pts = [(-a, 0.0), (a, 0.0)]
    for t in np.linspace(th0, math.pi - th0, seg):
        pts.append((R_ * math.cos(t), vc + R_ * math.sin(t)))
    return poly(pts), vc, R_


def _lobes(outline, vc, R_, n=7, r=None):
    """Cusp a horseshoe arch's head into lobes: small circles taken out of the arch's ring just
    inside it (for a frame's inner edge)."""
    r = R_ * 0.22 if r is None else r
    return cs_union([circle((R_ * 0.98 * math.cos(t), vc + R_ * 0.98 * math.sin(t)), r, 12) for t in np.linspace(0.15, math.pi - 0.15, n)])


def _octostar(c, ro, ri=None):
    return _star(c, ro, ro * 0.62 if ri is None else ri, n=8, rot=0.0)


def slate_zenobia(k, j):
    """The Zenobia's roof: square slates, every fifth course swallow-tailed and the next pointed
    (chisel), a band of arrowheads round the octagon."""
    m = k % 5
    return "swallow" if m == 2 else ("chisel" if m == 3 else "square")


def ablaq(region, datum=0.0, course=2.4, joint=0.4, d=0.32):
    """Ablaq: courses of smooth ashlar and courses scored with fine vertical lines in turn, the
    smooth ones standing a little prouder, every course bevelled top and bottom (the Zenobia's
    ground storey)."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    out = []
    k = math.floor((v0 - datum) / course) - 1
    while datum + k * course < v1 + course:
        a, b = datum + k * course + joint / 2, datum + (k + 1) * course - joint / 2
        if b > v0 - 1 and a < v1 + 1:
            dd = d if k % 2 == 0 else d * 0.6
            out.append(M.hull_points([(x, a, 0.0) for x in (u0 - 1, u1 + 1)] + [(x, a + dd, dd) for x in (u0 - 1, u1 + 1)] +
                                     [(x, b - dd * 0.4, dd) for x in (u0 - 1, u1 + 1)] + [(x, b, 0.0) for x in (u0 - 1, u1 + 1)]))
            if k % 2 == 1:
                sc = cs_union([rect(u, a + 0.3, u + 0.25, b - 0.3) for u in np.arange(u0 - 1, u1 + 1, 0.9)])
                out[-1] = out[-1] - ext(sc, dd - 0.15, dd + 0.5)
        k += 1
    return union(out) ^ M.extrude(region, d + 0.1)


def lap_ropebead(region, datum=0.0, pitch=1.8, d=0.34, every=4):
    """Lap boards 1.8 mm to the weather, every fourth butt dressed with a twisted rope bead
    (the Zenobia's upper storey)."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    k0 = math.floor((v0 - datum) / pitch) - 1
    k1 = math.ceil((v1 - datum) / pitch) + 1
    pts = [(datum + k0 * pitch, 0.0)]
    for k in range(k0, k1):
        vk = datum + k * pitch
        pts += [(vk, d), (vk + pitch, 0.06)]
    pts.append((datum + k1 * pitch, 0.0))
    strip = M.extrude(poly(pts), (u1 - u0) + 2).transform(frame([u0 - 1, 0, 0], [0, 1, 0], [0, 0, 1], [1, 0, 0]))
    ropes = []
    for k in range(k0, k1):
        if k % every:
            continue
        vk = datum + k * pitch
        cells = cs_union([poly([(u, vk + 0.05), (u + 0.3, vk + 0.05), (u + 0.62, vk + 0.5), (u + 0.32, vk + 0.5)])
                          for u in np.arange(u0 - 1, u1 + 1, 0.55)])
        ropes.append(ext(cells, d - 0.06, d + 0.2))
    out = strip + (union(ropes) if ropes else M())
    return out ^ M.extrude(region, d + 0.4).translate([0, 0, -0.1])


def corner_zenobia(L, at_start, qa, qb, w=2.4, t=0.65):
    """The Zenobia's octagon corners (where the turn is sharp enough for dressing): an engaged
    colonnette on a block, ringed thrice, under a cushion capital."""
    def span(a, b):
        return (a, b) if at_start else (L - b, L - a)
    if qb - qa < 8.0:
        return M()
    x = span(0.0, 0.0)[0]
    rc = 0.7
    prof = [(0.0, 0.0), (rc, 0.0)]
    for f in (0.3, 0.55, 0.8):
        z = (qb - qa - 3.4) * f
        prof += [(rc, z), (rc + 0.2, z + 0.2), (rc + 0.2, z + 0.4), (rc, z + 0.6)]
    prof += [(rc, qb - qa - 3.2), (0.0, qb - qa - 3.2)]
    col = PW._revolve(prof, 18).rotate([-90, 0, 0]).translate([x, qa + 1.79, 0.0]) ^ box([x - 3, qa, 0.0], [x + 3, qb, 3.0])
    a, b = span(-0.6, 1.6)
    out = col + chamfer_box(a, qa, b, qa + 1.8, 0.0, 1.0, c=0.2, bottom=1.0) + chamfer_box(a, qb - 1.6, b, qb, 0.0, 1.1, c=0.3, bottom=1.1)
    return out


def foundation_starplinth(reg, seed=0):
    """A plinth faced in tiles, each with a raised eight-pointed star, under a bevelled cap (the
    Zenobia)."""
    b = reg.bounds()
    out = [M.extrude(reg, 0.3)]
    s = 3.0
    v0, v1 = b[1] + 0.3, b[3] - 1.4
    if v1 - v0 > 2.0:
        stars = []
        for v in np.arange(v0 + s / 2, v1 - s / 2 + 0.01, s):
            for u in np.arange(b[0] + s / 2, b[2] - s / 2 + 0.01, s):
                stars.append(_octostar((u, v), s * 0.36))
        if stars:
            out.append(ext(cs_union(stars) ^ reg, 0.29, 0.6))
    cap = rect(b[0] - 1, b[3] - 1.4, b[2] + 1, b[3]) ^ reg
    if not cap.is_empty():
        cb = cap.bounds()
        out.append(M.hull_points([(x, cb[1], 0.29) for x in (cb[0], cb[2])] + [(x, cb[1] + 0.5, 0.8) for x in (cb[0], cb[2])] +
                                 [(x, cb[3], 0.8) for x in (cb[0], cb[2])] + [(x, cb[3], 0.29) for x in (cb[0], cb[2])]))
    return union(out)


# ------------------------------------------------------------------ cornice ornaments
def course_octostars(L, h, b, pitch, margin, p):
    """A row of eight-pointed stars on a fillet, a bead between every two (the Zenobia)."""
    pu = 2.4
    n = max(1, int((L - 0.6) / pu))
    u0 = (L - n * pu) / 2
    stars = cs_union([_octostar((u0 + pu * (k + 0.5), h / 2), min(0.85, h * 0.46)) for k in range(n)])
    beads = cs_union([circle((u0 + pu * k, h / 2), 0.3, 10) for k in range(n + 1)])
    clip = rect(0.2, 0.0, L - 0.2, h)
    return [_st(rect(0.2, 0.2, L - 0.2, h - 0.2), b, 0.18), _st(stars ^ clip, b + 0.18, 0.32), _st(beads ^ clip, b + 0.18, 0.22)]


def frieze_arabesque(L, h, b, pitch, margin, pair, half):
    """Strapwork: a band of interlaced straps knotting into eight-pointed stars, one star in
    every 5 mm, a boss at each heart (the Zenobia's storey joint)."""
    v0, v1 = 0.7, h - 0.7
    hh = v1 - v0
    vm = (v0 + v1) / 2
    pu = max(4.2, hh * 1.05)
    n = max(1, int((L - 1.0) / pu))
    u0 = (L - n * pu) / 2
    straps, bosses = [], []
    for k in range(n):
        c = (u0 + pu * (k + 0.5), vm)
        ro = hh * 0.44
        st_ = _octostar(c, ro, ro * 0.66)
        straps.append(st_ - st_.offset(-0.45, MIT, 4.0))
        bosses.append(circle(c, 0.5, 12))
        if k < n - 1:
            x0, x1 = c[0] + ro * 0.75, c[0] + pu - ro * 0.75
            straps.append(stroke([(x0, vm + hh * 0.22), (x1, vm - hh * 0.22)], 0.45))
            straps.append(stroke([(x0, vm - hh * 0.22), (x1, vm + hh * 0.22)], 0.45))
    clip = rect(0.2, v0, L - 0.2, v1)
    return [_st(cs_union(straps) ^ clip, b, 0.38), _st(cs_union(bosses) ^ clip, b, 0.55)], []


def frieze_muqarnas(L, h, b, pitch, margin, pair, half):
    """Muqarnas: stalactite vaulting seen face on, three tiers of little pointed niches each
    stepped out over the one below, a pendant under every second (the Zenobia's eave)."""
    v0, v1 = 0.5, h - 0.5
    hh = v1 - v0
    tiers = 3
    th = hh / tiers
    out = []
    for t in range(tiers):
        vb, vt = v0 + th * t, v0 + th * (t + 1)
        pu = 2.0
        n = max(1, int((L - 0.6) / pu))
        u0 = (L - n * pu) / 2 + (t % 2) * pu / 2
        band = rect(0.2, vb, L - 0.2, vt)
        niches = cs_union([_lancet(u0 + pu * k + 0.25, u0 + pu * (k + 1) - 0.25, vt - 0.5 - _apex(pu - 0.5, (pu - 0.5) * 0.7), v0=vb - 0.5,
                                   r=(pu - 0.5) * 0.7, seg=6) for k in range(-1, n + 1)])
        out.append(_st((band - niches) ^ rect(0.2, v0, L - 0.2, v1), b + 0.3 * t, 0.3))
        out.append(_st(band ^ rect(0.2, v0, L - 0.2, v1), b + 0.3 * t - 0.01, 0.06))
    for k, u in enumerate(np.arange(1.2, L - 1.0, 4.0)):
        out.append(_st(circle((u, v0 + 0.35), 0.35, 10) ^ rect(0.2, v0, L - 0.2, v1), b + 0.3, 0.3))
    return out, []


def frieze_merlons(L, h, b, pitch, margin, pair, half):
    """A band of stepped Moorish merlons in relief, each pierced (sunk) with a small star (the
    Zenobia's drum)."""
    v0, v1 = 0.6, h - 0.6
    hh = v1 - v0
    pu = max(3.0, hh * 0.9)
    n = max(1, int((L - 1.0) / pu))
    u0 = (L - n * pu) / 2
    cells, stars = [rect(0.2, v0, L - 0.2, v0 + hh * 0.25)], []
    for k in range(n):
        u = u0 + pu * (k + 0.5)
        hw = pu * 0.36
        cells.append(poly([(u - hw, v0), (u + hw, v0), (u + hw, v0 + hh * 0.55), (u + hw * 0.55, v0 + hh * 0.55),
                           (u + hw * 0.55, v0 + hh * 0.8), (u, v1), (u - hw * 0.55, v0 + hh * 0.8), (u - hw * 0.55, v0 + hh * 0.55),
                           (u - hw, v0 + hh * 0.55)]))
        stars.append(_octostar((u, v0 + hh * 0.42), min(0.6, hw * 0.55)))
    mer = cs_union(cells) ^ rect(0.2, v0, L - 0.2, v1)
    return [_st(mer, b, 0.45)], [ext(cs_union(stars), b + 0.2, b + 1.0)]


def bracket_lotusconsole(h, d, t):
    """A console ending in a hanging lotus bud: a body sweeping out from the wall to the soffit's
    front, and from its toe a bud of three petals (side profile, top at v = 0; the Zenobia)."""
    body = poly([(0.0, 0.0), (d, 0.0), (d, -0.9), (d * 0.45, -h * 0.55), (0.9, -h + 0.6), (0.0, -h + 0.6)])
    bud = cs_union([_lens((d - 0.45, -1.4), 1.6, 0.8, math.pi / 2), _lens((d - 0.85, -1.2), 1.2, 0.5, math.pi / 2 + 0.5)])
    return cs_union([body, bud])


def kufic(L, h):
    """A crest course: a Kufic-like square fret, a band folding up into battlement steps at
    every 3 mm (the Zenobia's deck)."""
    pu = 3.0
    n = max(1, int((L - 0.6) / pu))
    u0 = (L - n * pu) / 2
    lo, hi = 0.35, h - 0.35
    pts = []
    for k in range(n):
        u = u0 + pu * k
        pts += [(u, lo), (u + 0.9, lo), (u + 0.9, hi), (u + 2.1, hi), (u + 2.1, lo)]
    pts.append((u0 + pu * n, lo))
    return [cs_union([stroke(pts, 0.46, caps=False), rect(0.2, 0.05, L - 0.2, 0.3)]) ^ rect(0.2, 0.05, L - 0.2, h - 0.05)]


def fence_zenobia(L, h):
    """Zenobia cresting (drawn at half size for SE.printable): stepped merlons pierced with
    stars, and between them slender spires each tipped with a little crescent of leaf, on a
    rail."""
    pitch = 3.6
    n = max(1, int(round(L / pitch)))
    p = L / n
    cells = [rect(0.0, 0.0, L, 0.6)]
    holes = []
    for j in range(n):
        m = p * j + p / 2
        hw = p * 0.32
        cells.append(poly([(m - hw, 0.0), (m + hw, 0.0), (m + hw, h * 0.5), (m + hw * 0.55, h * 0.5), (m + hw * 0.55, h * 0.72),
                           (m, h * 0.92), (m - hw * 0.55, h * 0.72), (m - hw * 0.55, h * 0.5), (m - hw, h * 0.5)]))
        holes.append(_octostar((m, h * 0.36), min(0.55, hw * 0.5)))
    for j in range(n + 1):
        u = min(max(p * j, 0.3), L - 0.3)
        cells.append(rect(u - 0.25, 0.0, u + 0.25, h * 0.8))
        cells.append(_lens((u, h * 0.82), 0.9, 0.6, math.pi / 2))
    return (cs_union(cells) - cs_union(holes)) ^ rect(0.0, 0.0, L, h + 1.0)


def finial_tulip(h=14.0):
    """The onion's finial: a turned collar, a slender spire carrying a tulip bud (its swell
    drawn in at 45 degrees below), then a point."""
    prof = [(0.0, 0.0), (1.4, 0.0), (1.4, 0.5), (0.9, 1.0), (0.6, 1.3), (0.9, 1.7), (0.5, 2.1), (0.45, 6.0), (0.95, 7.0),
            (1.05, 7.8), (0.8, 8.6), (0.45, 9.2), (0.4, 9.6), (0.0, 9.6)]
    body = PW._revolve(prof, 24)
    return body + M.cylinder(h - 9.5, 0.4, 0.3, 12).translate([0, 0, 9.5])


def onion_zenobia(r0=15.0, h=34.0):
    """The gilt onion dome, solid, printed upright: from the drum's rim it swells out at 45
    degrees (no more, so nothing hangs), turns, and draws in on an ogee to its point. Local: foot
    at z = 0 on the axis."""
    prof = [(0.0, 0.0), (r0, 0.0), (r0 + 0.6, 0.6), (r0 * 1.22, r0 * 0.22 + 0.6), (r0 * 1.24, h * 0.3), (r0 * 1.18, h * 0.42),
            (r0 * 0.98, h * 0.55), (r0 * 0.66, h * 0.68), (r0 * 0.36, h * 0.8), (r0 * 0.16, h * 0.9), (0.5, h * 0.97), (0.3, h), (0.0, h)]
    body = PW._revolve(prof, 64)
    ribs = PW._revolve([(0.0, 0.0)] + [(rr + 0.35, z) for rr, z in prof[2:-1]] + [(0.0, h)], 64)
    for k in range(16):
        sl = box([0.0, -0.3, 0.6], [r0 * 1.5, 0.3, h]).rotate([0, 0, 360.0 * k / 16])
        body = body + (ribs ^ sl)
    return body


# ------------------------------------------------------------------ windows and doors
def _alfiz(half, top, v0, t=0.9):
    """An alfiz: a rectangular moulded frame enclosing a horseshoe arch's head, from the
    springing up past the crown."""
    o = rect(-half, v0, half, top)
    return ext(o - o.offset(-t, MIT, 4.0), 0.0, 0.9)


def window_zenobia_ground(w=8.6, h=21.0, A=0.9):
    """The ground storey's window: a horseshoe-arched light (two lights below a transom, the head
    glazed in a fan) in a frame whose head is cusped into lobes, set in an alfiz with a star in
    each spandrel; a sill on a panelled apron."""
    a = w / 2
    op, vc, R_ = _horseshoe(a, h - a * 1.18 - a * 0.6)
    ob = op.bounds()
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    inner = plug_cs.offset(-0.6, MIT, 4.0)
    body = [ext(plug_cs, -pl, -0.6)]
    vt = vc - R_ * 0.3
    bars = cs_union([rect(-RIB / 2, -1.0, RIB / 2, vt), rect(-w, vt - 0.35, w, vt + 0.35)] +
                    [stroke([(0.0, vt), (R_ * 1.5 * math.cos(t_), vt + R_ * 1.5 * math.sin(t_))], RIB) for t_ in np.linspace(0.5, math.pi - 0.5, 3)])
    sash = _glazed(body, inner, pl, bars, plug_cs)
    ring = op.offset(A, RND) - op
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS), ext(ring, 0.0, 0.8),
             ext(_lobes(op, vc, R_ + A * 0.5, n=9, r=0.42) ^ (op.offset(A, RND) - op.offset(-0.01, RND)), 0.0, 1.05)]
    half = R_ + A + 1.0
    top = ob[3] + A + 1.2
    parts.append(_alfiz(half, top, vc - R_ * 0.35))
    for sg in (-1, 1):
        parts.append(ext(_octostar((sg * (half - 1.4), top - 1.6), 0.7), 0.0, 1.0))
    parts.append(ext(rect(-half, vc - R_ * 0.35 - 0.01, half, vc - R_ * 0.35 + 0.9) - op.offset(A, RND), 0.0, 0.9))
    sw = half
    parts.append(MD.run(-sw, sw, 0.0, MD.SILL, 1.0, up=False))
    parts.append(ext(rect(-a, -3.2, a, -0.79), 0.0, 0.45))
    parts.append(ext(_octostar((0.0, -2.0), 1.0), 0.44, 0.8))
    return O._one_piece(sash, parts, op, plug_cs, pl, top + 0.2, -3.2)


def window_zenobia_upper(w=11.0, h=18.0, A=0.8):
    """The upper storey's ajimez: two horseshoe-arched lights sharing a slender central
    colonnette, under one alfiz with a lozenge between the heads; a sill."""
    sw_ = (w - 1.2) / 2
    a = sw_ / 2
    lights, cents = [], []
    for sg in (-1, 1):
        o, vc, R_ = _horseshoe(a, h - a * 1.18 - a * 0.6)
        lights.append(o.translate((sg * (a + 0.6), 0.0)))
        cents.append((sg * (a + 0.6), vc, R_))
    op = cs_union(lights)                         # two lights: the wall between them stands solid to the sill
    ob = op.bounds()
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    inner = cs_union([l.offset(-O.CLR - 0.5, MIT, 4.0) for l in lights])
    body = [ext(plug_cs, -pl, -0.6)]
    bars = cs_union([rect(-w, h * 0.45 - 0.3, w, h * 0.45 + 0.3)])
    sash = _glazed(body, inner, pl, bars, plug_cs)
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             ext(cs_union([l.offset(A, RND) - l for l in lights]) - op, 0.0, 0.8)]
    prof = [(0.0, 0.0), (0.55, 0.0), (0.55, cents[0][1] - 1.4), (0.8, cents[0][1] - 0.9), (0.8, cents[0][1] - 0.3), (0.0, cents[0][1] - 0.3)]
    parts.append(PW._revolve(prof, 16).rotate([-90, 0, 0]) ^ box([-2, 0.0, 0.0], [2, h, 3.0]))
    half = w / 2 + A + 0.9
    top = ob[3] + A + 1.0
    parts.append(_alfiz(half, top, cents[0][1] - cents[0][2] * 0.3))
    lz = poly([(0.0, top - 0.9 - 2.0), (1.0, top - 0.9 - 1.0), (0.0, top - 0.9), (-1.0, top - 0.9 - 1.0)])
    parts.append(ext(lz, 0.0, 1.0))
    parts.append(MD.run(-half, half, 0.0, MD.SILL, 1.0, up=False))
    return O._one_piece(sash, parts, op, plug_cs, pl, top + 0.2, -1.0)


def window_zenobia_drum(w=6.0, h=13.0, A=0.7):
    """A drum light: a horseshoe arch in a plain ring with a keystone star; a sill."""
    a = w / 2
    op, vc, R_ = _horseshoe(a, h - a * 1.18 - a * 0.6)
    ob = op.bounds()
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    inner = plug_cs.offset(-0.6, MIT, 4.0)
    sash = _glazed([ext(plug_cs, -pl, -0.6)], inner, pl, cs_union([rect(-RIB / 2, -1, RIB / 2, h + 2)]), plug_cs)
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS), ext(op.offset(A, RND) - op, 0.0, 0.8),
             ext(_octostar((0.0, ob[3] + A * 0.5), 0.75), 0.0, 1.1)]
    parts.append(MD.run(-a - A - 0.4, a + A + 0.4, 0.0, MD.SILL, 0.9, up=False))
    return O._one_piece(sash, parts, op, plug_cs, pl, ob[3] + A + 1.0, -0.9)


def door_zenobia(w=12.0, h=25.0, A=1.1):
    """The Zenobia's portal: a pair of studded leaves (raised panels set with rows of nail
    heads) under a horseshoe fanlight of radiating bars, a frame cusped into lobes, an alfiz with
    stars in the spandrels and a band of stars across its head."""
    a = w / 2
    op, vc, R_ = _horseshoe(a, h - a * 1.18 - a * 0.6)
    ob = op.bounds()
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    inner = plug_cs.offset(-0.5, MIT, 4.0)
    ib = inner.bounds()
    dh = vc - R_ * 0.55
    mid = 0.6
    lw = (2 * a - 2 * O.CLR - 1.0 - mid) / 2
    body = [ext(plug_cs, -pl, -1.0)]
    ul = -a + O.CLR + 0.5
    for i in range(2):
        body.append(ext(rect(ul, 0.5, ul + lw, dh), -pl, -0.8))
        pan = rect(ul + 0.7, 1.2, ul + lw - 0.7, dh - 0.8)
        body.append(_panel(pan))
        pb = pan.bounds()
        for v in np.arange(pb[1] + 1.2, pb[3] - 0.8, 2.4):
            for x in np.linspace(pb[0] + 0.8, pb[2] - 0.8, 3):
                body.append(ext(circle((x, v), 0.3, 8), -0.45, -0.1))
        ul += lw + mid
    fan = inner ^ rect(-w, dh + 0.5, w, h + 5)
    fc = (0.0, dh + 0.5)
    rays = cs_union([stroke([fc, (fc[0] + w * math.cos(t_), fc[1] + w * math.sin(t_))], RIB) for t_ in np.linspace(0.45, math.pi - 0.45, 5)])
    sash = _glazed(body, fan, pl, rays, plug_cs)
    sash.append(ext(rect(-w, dh - 0.01, w, dh + 0.52) ^ plug_cs, -pl, -0.5))
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS), ext(op.offset(A, RND) - op, 0.0, 0.9),
             ext(_lobes(op, vc, R_ + A * 0.5, n=11, r=0.45) ^ (op.offset(A, RND) - op.offset(-0.01, RND)), 0.0, 1.15)]
    half = R_ + A + 1.6
    top = ob[3] + A + 1.6
    parts.append(_alfiz(half, top, vc - R_ * 0.4, t=1.1))
    for sg in (-1, 1):
        parts.append(ext(_octostar((sg * (half - 1.7), top - 2.0), 0.9), 0.0, 1.1))
    parts.append(ext(rect(-half, top - 0.01, half, top + 1.8), 0.0, 0.8))
    parts.append(ext(cs_union([_octostar((x, top + 0.9), 0.6) for x in np.arange(-half + 1.2, half - 0.9, 2.0)]), 0.79, 1.2))
    parts.append(ext(rect(-half, -0.6, half, 0.01), 0.0, 1.1))
    return O._one_piece(sash, parts, op, plug_cs, pl, top + 2.0, -0.6)


def door_zenobia_back(w=9.0, h=22.0, A=0.9):
    """The garden door: one leaf of studded panels under a horseshoe fanlight, a plain ring and
    an alfiz."""
    a = w / 2
    op, vc, R_ = _horseshoe(a, h - a * 1.18 - a * 0.6)
    ob = op.bounds()
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    inner = plug_cs.offset(-0.5, MIT, 4.0)
    ja = a - O.CLR - 0.5                         # the leaf between the jambs (not the arch's swell)
    dh = vc - R_ * 0.55
    body = [ext(plug_cs, -pl, -1.0), ext(rect(-ja, 0.5, ja, dh), -pl, -0.8)]
    pan = rect(-ja + 0.8, 1.2, ja - 0.8, dh - 0.8)
    body.append(_panel(pan))
    pb = pan.bounds()
    for v in np.arange(pb[1] + 1.2, pb[3] - 0.8, 2.4):
        for x in np.linspace(pb[0] + 0.8, pb[2] - 0.8, 3):
            body.append(ext(circle((x, v), 0.3, 8), -0.45, -0.1))
    fan = inner ^ rect(-w, dh + 0.5, w, h + 5)
    sash = _glazed(body, fan, pl, cs_union([rect(-RIB / 2, dh, RIB / 2, h + 5)]), plug_cs)
    sash.append(ext(rect(-w, dh - 0.01, w, dh + 0.52) ^ plug_cs, -pl, -0.5))
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS), ext(op.offset(A, RND) - op, 0.0, 0.9)]
    half = R_ + A + 1.0
    top = ob[3] + A + 1.2
    parts.append(_alfiz(half, top, vc - R_ * 0.4))
    parts.append(ext(rect(-half, -0.6, half, 0.01), 0.0, 1.0))
    return O._one_piece(sash, parts, op, plug_cs, pl, top + 0.2, -0.6)


# ------------------------------------------------------------------ gallery parts
def post_moorish(h, collar=None, abacus=3.0, slot=(1.2, 1.0)):
    """A Moorish colonnette: a square base, a slender shaft ringed at its foot and below its
    capital, a cushion capital (a cube rounded underneath) and a tall impost block (cimacio)
    over it (the Zenobia's galleries)."""
    zc = h - 4.4
    r = 0.78
    prof = [(0.0, 1.19), (1.0, 1.19), (1.0, 1.4), (r, 1.7), (r, zc - 0.8), (1.0, zc - 0.6), (1.0, zc - 0.3), (r, zc - 0.1), (r, zc), (1.4, zc + 0.6),
            (1.45, zc + 1.2)]
    body = PW._revolve(prof, 24) + PW._plinth(2.6)
    body = body + PW._top(h, abacus / 2, zc + 1.2, 1.45, slot, seg=24, shape="square")
    return body


def baluster_mashrabiya(h, seg=14):
    """A mashrabiya spindle: a stack of turned balls and rings on a slender core, on a square
    foot under a square top (the Zenobia)."""
    prof = [(0.0, 0.8), (0.26, 0.8)]
    z = 0.9
    k = 0
    while z < h - 1.6:
        prof += [(0.26, z), (0.46 if k % 2 == 0 else 0.36, z + 0.4), (0.26, z + 0.8)]
        z += 0.9
        k += 1
    prof += [(0.26, h - 0.8)]
    body = PW._revolve(prof, seg)
    return body + box([-0.55, -0.55, 0.0], [0.55, 0.55, 0.81]) + box([-0.55, -0.55, h - 0.81], [0.55, 0.55, h])


def frieze_horseshoearcade(u0, u1, v_bot, v_top):
    """A gallery frieze: one horseshoe arch filling the bay from post to post, its head cusped
    into lobes, a star in each spandrel (the Zenobia)."""
    L = u1 - u0
    hh = v_top - v_bot
    um = (u0 + u1) / 2
    a = L / 2 - 0.4
    R_ = a * 1.12
    vc = v_top - 1.2 - R_
    pts = []
    th0 = math.asin(max(-1.0, min(1.0, (v_bot - 1.0 - vc) / R_)))
    for t in np.linspace(th0, math.pi - th0, 32):
        pts.append((um + R_ * math.cos(t), vc + R_ * math.sin(t)))
    hole = poly(pts) - cs_union([circle((um + R_ * math.cos(t), vc + R_ * math.sin(t)), 0.5, 10) for t in np.linspace(0.3, math.pi - 0.3, 7)])
    solid = rect(u0, v_bot, u1, v_top + 0.05) - hole
    stars = cs_union([_octostar((x, v_top - 1.6), 0.55) for x in (u0 + 1.5, u1 - 1.5)])
    return solid - stars


def edge_starfringe(L, z0, zc):
    """Gallery fascia (the Zenobia): a fillet under the crown hung with a row of small
    eight-pointed stars."""
    out = [rect(0.3, zc - 0.5, L - 0.3, zc)]
    pu = 1.8
    n = max(1, int((L - 1.0) / pu))
    u0 = (L - n * pu) / 2
    out += [_octostar((u0 + pu * (k + 0.5), zc - 1.05), 0.68) for k in range(n)]
    return cs_union(out) ^ rect(0.3, -1e3, L - 0.3, 1e3), 0.6


def skirt_girih(reg, d=1.2):
    """A gallery skirt of girih: a lattice of interlaced octagons and stars in relief (the
    Zenobia)."""
    u0, v0, u1, v1 = reg.bounds()
    out = [M.extrude(reg, d * 0.4)]
    s = 3.4
    cells = []
    for v in np.arange(v0 + s / 2, v1, s):
        for u in np.arange(u0 + s / 2, u1, s):
            st_ = _octostar((u, v), s * 0.42)
            cells.append(st_ - st_.offset(-0.45, MIT, 4.0))
    if cells:
        out.append(ext(cs_union(cells) ^ reg, d * 0.4 - 0.01, d * 0.75))
    out.append(ext(rect(u0 - 1, v1 - 0.9, u1 + 1, v1 + 1), d * 0.4 - 0.01, d * 0.75))
    return union(out) ^ M.extrude(reg, d + 0.5)


def chimney_zenobia(r=4.6, h=24.0):
    """A stack as a little turret: an octagonal shaft with a horseshoe niche in every other face,
    a ring of merlon-cut corbelling, and a little onion cap with a point. Prints upright."""
    h = round(h / 0.2) * 0.2
    sh = h - 8.0
    oc = circle((0.0, 0.0), r, 8).rotate(22.5)
    body = M.extrude(oc, sh)
    ap = r * math.cos(math.pi / 8)
    for k in range(0, 8, 2):
        a = 2 * math.pi * k / 8
        nich, _, _ = _horseshoe(1.0, sh * 0.5)
        T = np.array([[-math.sin(a), 0, math.cos(a), ap * math.cos(a)], [math.cos(a), 0, math.sin(a), ap * math.sin(a)], [0, 1.0, 0, sh * 0.2]])
        body = body - ext(nich, -0.5, 1.0).transform(T)
    body = body + M.extrude(circle((0.0, 0.0), r + 0.6, 8).rotate(22.5), 0.6).translate([0, 0, sh - 0.01])
    body = body + M.hull_points([(p[0], p[1], sh - 0.61) for p in oc.to_polygons()[0]] +
                                [(p[0], p[1], sh) for p in circle((0.0, 0.0), r + 0.6, 8).rotate(22.5).to_polygons()[0]])
    cap = onion_zenobia(r * 0.95, 7.4).translate([0, 0, sh + 0.59])
    return body + cap


CO.FRIEZE_EXTRA.update(arabesque=frieze_arabesque, muqarnas=frieze_muqarnas, merlons=frieze_merlons)
CO.COURSE_EXTRA.update(octostars=course_octostars)
TW.BRACKET_EXTRA.update(lotusconsole=bracket_lotusconsole)
TW.FOUNDATION_EXTRA.update(starplinth=foundation_starplinth)
SH.CORNER_EXTRA.update(zenobia=corner_zenobia)
PW.POSTS.update(moorish=post_moorish)
PW.BALUSTERS.update(mashrabiya=(baluster_mashrabiya, 1.6))
PW.FRIEZES.update(horseshoearcade=frieze_horseshoearcade)
PW.SKIRTS.update(girih=skirt_girih)
FT.EDGE_EXTRA.update(starfringe=edge_starfringe)


# ================================================================== the Thornbury (house 97)
# Richardsonian Romanesque, 1887: a ground storey of rock-faced red sandstone in random courses
# on a chamfered plinth, an upper storey of long thin Roman brick, rock-faced quoins; deep
# round-arched windows of long voussoirs below, ribbon windows of three lights on colonnettes
# above, a cornice of deeply cut Byzantine leaves on roll corbels between nailhead courses, an
# interlace band at the storey joint. A round tower on the front corner rises a stage over the
# eave to a steep cone; the steep slate roof carries eyebrow dormers and stops at a crested top
# with foliate cresting; the entrance porch is a low Syrian arch on squat columns with cushion
# capitals carved in interlace, its portal recessed in orders.

TB_LEVELS = dict(hi=40.0)      # the building sets it: the brick storey's foot over the block's base


def slate_keybands(k, j):
    """The Thornbury's slating: square slates with a band of key-butted slates every sixth
    course and a course of saw-cut ones under it."""
    m = k % 6
    return "key" if m == 3 else ("saw" if m == 4 else "square")


def _rough(u0, v0, u1, v1, d, seed, jit=0.18):
    """A rock-faced block: a hull of its bevelled margin and a few jittered points on its face,
    so each stone bulges unevenly (pitched face). The margin is 45 degrees."""
    rng = np.random.default_rng(seed)
    pts = [(x, y, 0.0) for x in (u0, u1) for y in (v0, v1)]
    m = min(d * 0.7, (v1 - v0) * 0.3, (u1 - u0) * 0.2)
    pts += [(x, y, d * 0.55) for x in (u0 + m, u1 - m) for y in (v0 + m, v1 - m)]
    for _ in range(5):
        x = rng.uniform(u0 + m * 1.6, u1 - m * 1.6) if u1 - u0 > 4 * m else (u0 + u1) / 2
        y = rng.uniform(v0 + m * 1.6, v1 - m * 1.6) if v1 - v0 > 4 * m else (v0 + v1) / 2
        pts.append((x, y, d * (0.75 + rng.uniform(0.0, jit) / d * 0.5)))
    return M.hull_points(pts)


def rockfaced(region, datum=0.0, d=0.55, joint=0.35, seed=7):
    """Rock-faced ashlar in random courses: courses of two heights in an irregular rhythm, stones
    of random length, every face pitched to an uneven bulge (the Thornbury's ground storey)."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    rng = np.random.default_rng(seed)
    out = []
    v = datum + math.floor((v0 - datum) / 5.4) * 5.4 - 5.4
    k = 0
    while v < v1:
        hc = (2.2, 3.2, 2.2, 2.2, 3.2)[k % 5]
        a, b = v + joint / 2, v + hc - joint / 2
        if b > v0 - 1:
            u = u0 - rng.uniform(0.0, 4.0)
            while u < u1 + 1:
                Ls = rng.uniform(3.2, 7.4)
                out.append(_rough(u + joint / 2, a, u + Ls - joint / 2, b, d, int(rng.integers(1e9))))
                u += Ls
        v += hc
        k += 1
    return union(out) ^ M.extrude(region, d + 0.3)


def brick_roman(region, datum=0.0, bl=3.8, bh=0.6, mortar=0.4, bed=0.2, d=0.22):
    """Roman brick: long thin bricks in running bond, broken a third, with deep horizontal beds
    (the Thornbury's upper storey)."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    cells = []
    k = math.floor((v0 - datum) / bh) - 1
    while datum + k * bh < v1:
        v = datum + k * bh
        u = u0 - 2 * bl + (k % 3) * bl / 3
        while u < u1 + bl:
            cells.append(rect(u + mortar / 2, v, u + bl - mortar / 2, v + bh - bed))
            u += bl
        k += 1
    return M.extrude(cs_union(cells) ^ region, d)


def corner_thornbury(L, at_start, qa, qb, w=2.4, t=0.65):
    """The Thornbury's corners: rock-faced quoins long and short, up both storeys."""
    def span(a, b):
        return (a, b) if at_start else (L - b, L - a)
    parts = []
    v, k = max(qa, 0.3), 0
    while v < qb - 1.8:
        leg = 5.0 if k % 2 == 0 else 3.2
        top = min(v + 3.0, qb - 0.2)
        a, b = span(-t - 0.3, leg)
        parts.append(_rough(min(a, b), v, max(a, b), top, t + 0.25, 1000 + k * 7 + (0 if at_start else 3)))
        v += 3.3
        k += 1
    return union(parts) if parts else M()


def foundation_chamfercourse(reg, seed=0):
    """A plinth of two great chamfered courses, the upper set back over the lower (the
    Thornbury)."""
    b = reg.bounds()
    hgt = b[3] - b[1]
    out = [M.extrude(reg, 0.3)]
    mid = b[1] + hgt * 0.55
    lo = rect(b[0] - 1, b[1], b[2] + 1, mid) ^ reg
    hi = rect(b[0] - 1, mid, b[2] + 1, b[3]) ^ reg
    for r_, d in ((lo, 1.1), (hi, 0.75)):
        if not r_.is_empty():
            bb = r_.bounds()
            out.append(M.hull_points([(x, bb[1], 0.0) for x in (bb[0], bb[2])] + [(x, bb[1], d) for x in (bb[0], bb[2])] +
                                     [(x, bb[3] - d + 0.3, d) for x in (bb[0], bb[2])] + [(x, bb[3], 0.29) for x in (bb[0], bb[2])]))
    return union(out)


# ------------------------------------------------------------------ cornice ornaments
def course_nailhead(L, h, b, pitch, margin, p):
    """Nailhead: a row of little pyramids, each a square studded up to a point (the
    Thornbury)."""
    pu = 1.5
    n = max(1, int((L - 0.6) / pu))
    u0 = (L - n * pu) / 2
    out = [_st(rect(0.2, 0.15, L - 0.2, h - 0.15), b, 0.15)]
    s = min(0.6, h * 0.36)
    for k in range(n):
        u = u0 + pu * (k + 0.5)
        out.append(M.hull_points([(u + dx, h / 2 + dy, 0.0) for dx in (-s, s) for dy in (-s, s)] + [(u, h / 2, 0.5)]).translate([0, 0, b + 0.14]))
    return out


def frieze_interlace(L, h, b, pitch, margin, pair, half):
    """Byzantine interlace: two bands weaving over and under in a running knot of circles and
    figure-eights, a pellet in every eye (the Thornbury's storey joint)."""
    v0, v1 = 0.7, h - 0.7
    hh = v1 - v0
    vm = (v0 + v1) / 2
    r = hh * 0.36
    pu = r * 1.7
    n = max(1, int((L - 1.0) / pu))
    u0 = (L - n * pu) / 2
    bands, pel = [], []
    a1 = [(u, vm + r * 0.8 * math.sin((u - u0) / pu * math.pi)) for u in np.arange(u0, u0 + pu * n + 0.01, 0.4)]
    a2 = [(u, vm - r * 0.8 * math.sin((u - u0) / pu * math.pi)) for u in np.arange(u0, u0 + pu * n + 0.01, 0.4)]
    if len(a1) > 1:
        bands.append(stroke(a1, 0.5))
        bands.append(stroke(a2, 0.5))
    for k in range(n):
        pel.append(circle((u0 + pu * (k + 0.5), vm), 0.4, 10))
    clip = rect(0.2, v0, L - 0.2, v1)
    frame_ = rect(0.2, v0, L - 0.2, v0 + 0.45) + rect(0.2, v1 - 0.45, L - 0.2, v1)
    return [_st(frame_, b, 0.25), _st(cs_union(bands) ^ clip, b, 0.4), _st(cs_union(pel) ^ clip, b, 0.5)], []


def frieze_byzantineleaf(L, h, b, pitch, margin, pair, half):
    """Richardson's Byzantine leaf: a running band of deeply cut acanthus, each leaf a spray of
    pointed lobes curling from a central stem, the sprays alternating up and down (the
    Thornbury's eave)."""
    v0, v1 = 0.6, h - 0.6
    hh = v1 - v0
    vm = (v0 + v1) / 2
    pu = max(3.6, hh * 0.9)
    n = max(1, int((L - 1.0) / pu))
    u0 = (L - n * pu) / 2
    stems, lobes = [], []
    pts = [(u, vm + hh * 0.12 * math.sin((u - u0) / pu * 2 * math.pi)) for u in np.arange(u0, u0 + pu * n + 0.01, 0.4)]
    if len(pts) > 1:
        stems.append(stroke(pts, 0.5))
    for k in range(n):
        u = u0 + pu * (k + 0.5)
        sg = 1 if k % 2 == 0 else -1
        base = (u, vm)
        for j, a in enumerate((-0.9, -0.35, 0.25, 0.8)):
            Lf = hh * (0.42 - 0.04 * abs(j - 1.5))
            ang = math.pi / 2 * sg + a * sg
            lobes.append(_lens((base[0] + Lf * 0.5 * math.cos(ang), base[1] + Lf * 0.5 * math.sin(ang)), Lf, 0.55, ang))
    clip = rect(0.2, v0, L - 0.2, v1)
    return [_st(cs_union(stems) ^ clip, b, 0.3), _st(cs_union(lobes) ^ clip, b, 0.5)], []


def bracket_rollcorbel(h, d, t):
    """A Romanesque corbel: a block whose underside rolls round in a big half-round, a smaller
    roll beneath it (side profile, top at v = 0; the Thornbury)."""
    r1 = min(h * 0.45, d * 0.5)
    pts = [(0.0, 0.0), (d, 0.0)]
    for a in np.linspace(0.0, -math.pi / 2, 9):
        pts.append((d - r1 + r1 * math.cos(a), -r1 + r1 * math.sin(a) + 0.0))
    r2 = min(h * 0.25, d * 0.3)
    for a in np.linspace(0.0, -math.pi / 2, 7):
        pts.append((d - r1 - 0.2 + r2 * math.cos(a) - r2 * 0.2, -2 * r1 + r2 * math.sin(a) + 0.0))
    pts += [(0.0, -2 * r1 - r2)]
    return poly(pts)


def pelletchain(L, h):
    """A crest course: pellets threaded on a rod, between beads (the Thornbury's roof)."""
    pu = 1.6
    n = max(1, int((L - 0.6) / pu))
    u0 = (L - n * pu) / 2
    cells = [rect(0.2, 0.05, L - 0.2, h / 2 - 0.5), rect(0.2, h / 2 - 0.22, L - 0.2, h / 2 + 0.22)]
    cells += [circle((u0 + pu * (k + 0.5), h / 2), min(0.62, h * 0.24), 12) for k in range(n)]
    return [cs_union(cells) ^ rect(0.2, 0.05, L - 0.2, h - 0.05)]


def fence_thornbury(L, h):
    """Thornbury cresting (drawn at half size for SE.printable): terracotta crockets, each a
    curling leaf on a stem, rising from a moulded ridge band."""
    pitch = 2.8
    n = max(1, int(round(L / pitch)))
    p = L / n
    cells = [rect(0.0, 0.0, L, 0.9)]
    for j in range(n):
        m = p * j + p / 2
        cells.append(rect(m - 0.3, 0.0, m + 0.3, h * 0.55))
        cells.append(stroke([(m, h * 0.5), (m - 0.4, h * 0.75), (m + 0.3, h * 0.95), (m + 0.75, h * 0.72)], 0.5))
        cells.append(_lens((m - 0.55, h * 0.45), 1.1, 0.55, math.pi / 2 + 0.6))
    return cs_union(cells) ^ rect(0.0, 0.0, L, h + 1.0)


def fence_thornbury_parapet(L, h):
    """A parapet as a dwarf gallery: a row of little round arches on stubby piers between a
    plain base and a coping (the Thornbury's apse). Printed flat."""
    pu = 3.0
    n = max(1, int((L - 1.6) / pu))
    u0 = (L - n * pu) / 2
    holes = cs_union([O.opening_cs(pu - 1.1, h - 3.0, (pu - 1.1) / 2).translate((u0 + pu * (k + 0.5), 1.5)) for k in range(n)])
    return rect(0.2, 0.0, L - 0.2, h) - holes


def finial_thornbury(h=11.0):
    """The tower's finial: a turned knop over a collar, a tall spike with a ring."""
    prof = [(0.0, 0.0), (1.3, 0.0), (1.3, 0.6), (0.8, 1.0), (1.2, 1.5), (1.3, 2.2), (0.9, 2.8), (0.45, 3.2), (0.45, 3.6), (0.0, 3.6)]
    body = PW._revolve(prof, 24) + M.cylinder(h - 3.5, 0.45, 0.32, 12).translate([0, 0, 3.5])
    return body + _ball(0.6, 3.5 + (h - 3.5) * 0.45, neck=0.4)


# ------------------------------------------------------------------ windows and doors
def _longvous(w, h, A, n=9, crown=3.4, foot=2.6, gap=0.3):
    """Long Richardsonian voussoirs round a round head: radial stones of nearly even length,
    deepest at the key."""
    r0 = w / 2 + A
    cy = h - w / 2
    blocks = []
    for k in range(n):
        a0 = math.pi * k / n + gap / 2 / r0
        a1 = math.pi * (k + 1) / n - gap / 2 / r0
        am = (a0 + a1) / 2
        Lk = foot + (crown - foot) * math.sin(am)
        pts = [(r0 * math.cos(a), cy + r0 * math.sin(a)) for a in np.linspace(a0, a1, 5)]
        pts += [((r0 + Lk) * math.cos(a), cy + (r0 + Lk) * math.sin(a)) for a in np.linspace(a1, a0, 5)]
        blocks.append(poly(pts))
    return cs_union(blocks), cy + r0 + crown


def window_thornbury_ground(w=8.6, h=20.0, A=0.6):
    """The ground storey's window: a deep round-headed one-over-one sash under a ring of long
    rock-faced voussoirs; a plain sill on two corbels."""
    op = O.opening_cs(w, h, w / 2)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    sash = O.window_insert(w, h, w / 2, lites=(1, 1), bare=True)["insert"]
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS), MD.band(op.offset(A, RND), A, MD.CASING, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op)]
    vs, vt = _longvous(w, h, A)
    parts.append(ext(vs, 0.0, 1.0))
    sw = w / 2 + A + 1.0
    parts.append(chamfer_box(-sw, -1.4, sw, 0.01, 0.0, 1.3, c=0.3, bottom=1.3))
    for sg in (-1, 1):
        parts.append(chamfer_box(sg * (w / 2) - 0.8, -2.8, sg * (w / 2) + 0.8, -1.39, 0.0, 1.0, c=0.3, bottom=1.0))
    return O._one_piece([sash], parts, op, plug_cs, O.PLUG, vt + 0.2, -2.8)


def window_thornbury_ribbon(wl=5.2, h=16.0, n=3, col=1.4, A=0.8):
    """The brick storey's ribbon window: three lights in a row parted by short colonnettes with
    carved cushion capitals, under one stone lintel carved with Byzantine leaves; a sill course."""
    W = n * wl + (n - 1) * col
    op = rect(-W / 2, 0.0, W / 2, h)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    inner = plug_cs.offset(-0.5, MIT, 4.0)
    mids = cs_union([rect(-W / 2 + wl * (k + 1) + col * k, -1, -W / 2 + wl * (k + 1) + col * (k + 1), h + 1) for k in range(n - 1)])
    g = inner - mids
    bars = cs_union([rect(-W, h * 0.5 - 0.3, W, h * 0.5 + 0.3)])
    sash = _glazed([ext(plug_cs, -pl, -0.6)], g, pl, bars, plug_cs) + [ext(mids ^ plug_cs, -pl, -0.2)]
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS), MD.band(op.offset(A, MIT, 4.0), A, MD.CASING, clip=rect(-W - 10, 0.0, W + 10, h + 40) - op)]
    for k in range(n - 1):
        x = -W / 2 + wl * (k + 1) + col * k + col / 2
        prof = [(0.0, 0.0), (0.6, 0.0), (0.6, h - 2.2), (0.95, h - 1.6), (0.95, h - 0.6), (0.0, h - 0.6)]
        parts.append(PW._revolve(prof, 16).rotate([-90, 0, 0]).translate([x, 0.0, 0.0]) ^ box([x - 2, 0.0, 0.0], [x + 2, h, 3.0]))
    half = W / 2 + A + 0.6
    lin = rect(-half, h + A - 0.01, half, h + A + 3.0)
    parts.append(ext(lin, 0.0, 0.8))
    lv = []
    for k, x in enumerate(np.arange(-half + 1.4, half - 1.0, 2.0)):
        sg = 1 if k % 2 == 0 else -1
        lv.append(_lens((x, h + A + 1.5), 2.2, 0.6, math.pi / 2 + 0.6 * sg))
    parts.append(ext(cs_union(lv) ^ lin.offset(-0.3, MIT, 4.0), 0.79, 1.2))
    parts.append(chamfer_box(-half, -1.2, half, 0.01, 0.0, 1.1, c=0.3, bottom=1.1))
    return O._one_piece(sash, parts, op, plug_cs, pl, h + A + 3.2, -1.2)


def window_thornbury_tower(w=6.0, h=14.0, A=0.6):
    """A tower light: round-headed, in a ring of long voussoirs."""
    op = O.opening_cs(w, h, w / 2)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    sash = O.window_insert(w, h, w / 2, lites=(1, 1), bare=True)["insert"]
    vs, vt = _longvous(w, h, A, n=7, crown=2.4, foot=1.8)
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS), ext(op.offset(A + 0.06, RND) - op, 0.0, 0.6), ext(vs, 0.0, 0.9)]
    parts.append(chamfer_box(-w / 2 - A - 0.6, -1.2, w / 2 + A + 0.6, 0.01, 0.0, 1.0, c=0.3, bottom=1.0))
    return O._one_piece([sash], parts, op, plug_cs, O.PLUG, vt + 0.2, -1.2)


def door_thornbury(w=11.0, h=22.0, orders=3):
    """The Thornbury's portal: a pair of heavy plank leaves strapped with iron hinges under a
    round fanlight, set deep in a round arch of three orders, each ring stepping in over a nook
    shaft with a cushion capital."""
    r = w / 2
    op = O.opening_cs(w, h, r)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    spring = h - r
    inner = plug_cs.offset(-0.5, MIT, 4.0)
    dh = spring - 0.4
    ja = r - O.CLR - 0.5
    body = [ext(plug_cs, -pl, -1.0), ext(rect(-ja, 0.5, ja, dh), -pl, -0.8)]
    for x in np.arange(-ja + 0.9, ja - 0.5, 1.4):
        body.append(ext(rect(x - 0.15, 0.6, x + 0.15, dh - 0.1), -0.81, -0.6))
    for v in (dh * 0.25, dh * 0.75):
        for sg in (-1, 1):
            body.append(ext(rect(min(sg * ja, sg * 0.4), v - 0.35, max(sg * ja, sg * 0.4), v + 0.35), -0.81, -0.45))
    fan = inner ^ rect(-w, dh + 0.5, w, h + 2)
    fc = (0.0, dh + 0.5)
    rays = cs_union([stroke([fc, (fc[0] + w * math.cos(t_), fc[1] + w * math.sin(t_))], RIB) for t_ in np.linspace(0.6, math.pi - 0.6, 3)])
    sash = _glazed(body, fan, pl, rays, plug_cs)
    sash.append(ext(rect(-w, dh - 0.01, w, dh + 0.52) ^ plug_cs, -pl, -0.5))
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS)]
    for k in range(orders):
        e0, e1 = 0.4 + k * 1.6, 0.4 + (k + 1) * 1.6
        ring = O.opening_cs(w + 2 * e1, h + e1, r + e1) - O.opening_cs(w + 2 * e0, h + e0, r + e0)
        parts.append(ext(ring ^ rect(-50, spring, 50, 60), 0.0, 1.2 + 0.4 * (orders - k - 1)))
        for sg in (-1, 1):
            x = sg * (r + (e0 + e1) / 2)
            prof = [(0.0, 0.0), (0.6, 0.0), (0.6, spring - 1.6), (0.95, spring - 1.1), (0.95, spring), (0.0, spring)]
            parts.append(PW._revolve(prof, 16).rotate([-90, 0, 0]).translate([x, 0.0, 0.0]) ^ box([x - 2, 0.0, 0.0], [x + 2, spring, 3.0]))
    half = r + 0.4 + orders * 1.6 + 0.6
    parts.append(ext(rect(-half, -0.6, half, 0.01), 0.0, 1.4))
    return O._one_piece(sash, parts, op, plug_cs, pl, h + 0.4 + orders * 1.6 + 0.2, -0.6)


def addin_eyebrow(w=9.0, h=4.6, A=0.7):
    """An eyebrow dormer for the steep roof (an add-in): a low wide light under a segmental
    head, its frame and the plug's roof one smooth wave that dies into the slope at each end."""
    op = arch_cs(-w / 2, w / 2, 0.0, h - 1.4, rise=1.4, seg=24)
    bars = cs_union([rect(-RIB / 2 + x, -1.0, RIB / 2 + x, h + 1.0) for x in (-w / 6, w / 6)])
    wave = [(-w / 2 - 4.0, -0.2)] + [(x, h + 1.0 - (x / (w / 2 + 4.0)) ** 2 * (h + 1.2)) for x in np.linspace(-w / 2 - 3.6, w / 2 + 3.6, 21)] + [(w / 2 + 4.0, -0.2)]
    body = poly(wave)
    parts = [ext(body - op, 0.0, 0.5), MD.band(op.offset(A, RND), A, MD.CASING, clip=rect(-30, 0.0, 30, 30) - op)]
    parts.append(MD.run(-w / 2 - A - 0.4, w / 2 + A + 0.4, 0.0, MD.SILL, 0.9, up=False))
    parts = [p - ext(op, -1.0, 5.0) for p in parts]
    outline = body.offset(-0.3, RND) ^ rect(-50, 0.2, 50, 100)
    return dict(light=op, bars=bars, frame=parts, outline=outline, top=h + 1.6, bottom=-0.9)


# ------------------------------------------------------------------ the porch
def post_cushion(h, collar=None, abacus=4.4, slot=(1.2, 1.0)):
    """A squat Romanesque column: a broad base with spurs at its corners, a stout shaft, a cushion
    capital (round below, square above) carved with an interlace ring, a thick abacus (the
    Thornbury's porch)."""
    zc = h - 4.6
    r = 1.6
    prof = [(0.0, 1.39), (2.05, 1.39), (2.05, 1.7), (1.8, 2.0), (1.9, 2.3), (r, 2.7), (r * 1.04, zc * 0.5), (r * 0.96, zc - 0.3),
            (1.85, zc), (1.85, zc + 0.3), (r, zc + 0.5)]
    body = PW._revolve(prof, 28) + PW._plinth(4.2, ph=1.4)
    body = body + PW._top(h, abacus / 2, zc + 0.5, r, slot, seg=28, shape="round")
    return body


def baluster_spindleknop(h, seg=16):
    """A short stout spindle with a knop at its middle, between square blocks (the
    Thornbury)."""
    prof = [(0.0, 0.8), (0.36, 0.8), (0.36, 1.1), (0.28, 1.5), (0.28, h * 0.42), (0.5, h * 0.5), (0.28, h * 0.58), (0.28, h - 1.2), (0.36, h - 0.8)]
    return PW._revolve(prof, seg) + box([-0.55, -0.55, 0.0], [0.55, 0.55, 0.81]) + box([-0.55, -0.55, h - 0.81], [0.55, 0.55, h])


def frieze_syrianarch(u0, u1, v_bot, v_top):
    """A porch's Syrian arch: one broad round arch springing low between the posts, a ring of
    long voussoirs round it (the Thornbury)."""
    L = u1 - u0
    um = (u0 + u1) / 2
    rise = min(L / 2, v_top - v_bot - 1.0)
    solid = rect(u0, v_bot, u1, v_top + 0.05)
    hole = arch_cs(u0 + 0.3, u1 - 0.3, v_bot - 1.0, v_top - 1.0 - rise, rise=rise, seg=40)
    out = solid - hole
    n = max(5, int(L / 2.2)) | 1
    cy = v_top - 1.0 - rise
    r0 = L / 2 - 0.3
    joints = cs_union([stroke([(um + (r0 - 0.1) * math.cos(t), cy + (rise - 0.1) * math.sin(t)),
                               (um + (r0 + 2.4) * math.cos(t), cy + (rise + 2.4) * math.sin(t))], 0.4)
                       for t in np.linspace(0.0, math.pi, n + 1)[1:-1]])
    return out - (joints ^ rect(u0 + 0.7, v_bot - 2.0, u1 - 0.7, v_top - 0.7))


def edge_corbeltable(L, z0, zc):
    """Porch fascia (the Thornbury): a corbel table, little round arches hung between corbel
    knobs under the crown."""
    out = [rect(0.3, zc - 0.6, L - 0.3, zc)]
    pu = 2.4
    n = max(1, int((L - 1.0) / pu))
    u0 = (L - n * pu) / 2
    band = rect(0.3, zc - 1.6, L - 0.3, zc - 0.55)
    holes = cs_union([O.opening_cs(pu - 0.7, 1.4, (pu - 0.7) / 2).translate((u0 + pu * (k + 0.5), zc - 2.0)) for k in range(n)])
    out.append(band - holes)
    out += [circle((u0 + pu * k, zc - 1.7), 0.38, 10) for k in range(n + 1)]
    return cs_union(out) ^ rect(0.3, -1e3, L - 0.3, 1e3), 0.6


def skirt_rockwall(reg, d=1.2):
    """The porch's base between the piers: a solid wall of rock-faced stone under a chamfered
    sill, with a little round-arched vent at the middle (the Thornbury)."""
    u0, v0, u1, v1 = reg.bounds()
    out = [M.extrude(reg, d * 0.4)]
    body = rect(u0 - 1, v0 - 1, u1 + 1, v1 - 1.0) ^ reg
    out.append(rockfaced(body, datum=v0, d=0.5, seed=int(abs(u0) * 7 + abs(v0) * 3) % 97 + 5).translate([0, 0, d * 0.4 - 0.05]))
    out.append(ext(rect(u0 - 1, v1 - 1.0, u1 + 1, v1 + 1) ^ reg, d * 0.4 - 0.01, d * 0.85))
    vw = min(2.4, (u1 - u0) * 0.3)
    if v1 - v0 > 4.0 and vw > 1.2:
        um = (u0 + u1) / 2
        vent = O.opening_cs(vw, 2.6, vw / 2).translate((um, v0 + 0.8))
        out = [o - ext(vent, -1.0, 5.0) for o in out]
    return union(out) ^ M.extrude(reg, d + 0.5)


def entry_thornbury(w, depth, rise, t=1.0):
    """The Thornbury's porch entry: a steep gable of rock-faced stone standing on the porch roof
    over the steps, a moulded coping on its rakes stopping on kneelers, and in its tympanum a
    roundel of Byzantine leaves round a boss over a nailhead string. Local as entry_wyndham
    (u across, v up from the porch roof top, w out from the house, the face at w = depth);
    prints upright on its base."""
    face = poly([(-w / 2, 0.0), (0.0, rise), (w / 2, 0.0)])
    parts = [M.extrude(face, depth)]
    cop = (face - face.offset(-1.1, MIT, 4.0)) ^ rect(-w, 1.6, w, rise + 1)
    parts.append(ext(cop, depth - 0.01, depth + t))
    parts.append(ext(cop.offset(-0.35, MIT, 4.0) ^ face.offset(-0.2, MIT, 4.0), depth + t - 0.01, depth + t + 0.3))
    for sg in (-1, 1):
        kn = rect(min(sg * w / 2, sg * (w / 2 - 2.6)), 0.0, max(sg * w / 2, sg * (w / 2 - 2.6)), 2.4) ^ face.offset(0.3, MIT, 4.0)
        parts.append(ext(kn, depth - 0.01, depth + t + 0.2))
    tym = face.offset(-1.4, MIT, 4.0) ^ rect(-w, 1.2, w, rise)
    lo = tym ^ rect(-w, 1.2, w, rise * 0.24)
    parts.append(rockfaced(lo, datum=1.2, d=0.45, seed=53).translate([0, 0, depth - 0.05]))
    s = rect(-w, rise * 0.24, w, rise * 0.24 + 1.0) ^ tym
    parts.append(ext(s, depth - 0.01, depth + 0.5))
    for x in np.arange(-w / 2 + 2.0, w / 2 - 1.9, 1.3):
        if (rect(x - 0.45, rise * 0.24 + 0.05, x + 0.45, rise * 0.24 + 0.95) - tym).is_empty():
            parts.append(M.hull_points([(x + dx, rise * 0.24 + 0.5 + dy, 0.0) for dx in (-0.4, 0.4) for dy in (-0.4, 0.4)] +
                                       [(x, rise * 0.24 + 0.5, 0.4)]).translate([0, 0, depth + 0.49]))
    c = (0.0, rise * 0.24 + 1.0 + (rise * 0.76 - 2.6) * 0.42)
    R_ = min((rise * 0.76 - 2.6) * 0.42, w * 0.2)
    ring = circle(c, R_, 40) - circle(c, R_ - 0.7, 40)
    parts.append(ext(ring, depth - 0.01, depth + 0.7))
    lv = []
    for k in range(8):
        a = math.pi / 8 + k * math.pi / 4
        lv.append(_lens((c[0] + (R_ - 0.7) * 0.55 * math.cos(a), c[1] + (R_ - 0.7) * 0.55 * math.sin(a)), (R_ - 0.7) * 0.9, 0.55, a))
    parts.append(ext(cs_union(lv) ^ circle(c, R_ - 0.75, 40), depth - 0.01, depth + 0.45))
    parts.append(ext(circle(c, R_ * 0.22, 20), depth - 0.01, depth + 0.8))
    return union(parts).transform(np.array([[1.0, 0, 0, 0], [0, 0, 1.0, 0], [0, 1.0, 0, 0]]))


def chimney_thornbury(w=12.0, d=9.0, h=26.0):
    """A massive stack: rock-faced to the cap, a corbel table of little arches, a projecting cap,
    two flues each with a round pot. Prints upright."""
    h = round(h / 0.2) * 0.2
    sh = h - 7.0
    body = box([-w / 2, -d / 2, 0.0], [w / 2, d / 2, sh])
    stones = []
    for (L, D, rot) in ((w, d, 0), (d, w, 90), (w, d, 180), (d, w, 270)):
        T = np.array([[1.0, 0, 0, 0], [0, 0, 1.0, D / 2 - 0.05], [0, 1.0, 0, 0]])
        reg = rect(-L / 2, 0.0, L / 2, sh - 2.0)
        stones.append((rockfaced(reg, d=0.45, seed=31 + rot).transform(T)).rotate([0, 0, rot]))
    body = body + union(stones)

    def ring(e0, e1, z0, z1):
        return M.hull_points([(x, y, z0) for x in (-w / 2 - e0, w / 2 + e0) for y in (-d / 2 - e0, d / 2 + e0)] +
                             [(x, y, z1) for x in (-w / 2 - e1, w / 2 + e1) for y in (-d / 2 - e1, d / 2 + e1)])
    body = body + ring(0.0, 1.0, sh - 2.01, sh - 1.0) + ring(1.0, 1.0, sh - 1.01, sh + 1.0)
    for (L, D, rot) in ((w + 2.0, d + 2.0, 0), (d + 2.0, w + 2.0, 90), (w + 2.0, d + 2.0, 180), (d + 2.0, w + 2.0, 270)):
        n = max(2, int(L / 2.2))
        arches = cs_union([O.opening_cs(L / n - 0.7, 1.4, (L / n - 0.7) / 2).translate((-L / 2 + L * (k + 0.5) / n, 0.0)) for k in range(n)])
        T = np.array([[1.0, 0, 0, 0], [0, 0, 1.0, D / 2], [0, 1.0, 0, sh - 0.9]])
        body = body - (M.extrude(arches, 0.4).translate([0, 0, -0.39]).transform(T)).rotate([0, 0, rot])
    body = body + ring(1.0, 1.4, sh + 0.99, sh + 1.4) + ring(1.4, 1.4, sh + 1.39, sh + 2.4)
    for sx in (-1, 1):
        x = sx * w * 0.25
        pot = M.cylinder(3.6, 1.6, 1.3, 24).translate([x, 0.0, sh + 2.39]) + M.cylinder(0.4, 1.3, 1.7, 24).translate([x, 0, sh + 5.98]) + \
            M.cylinder(0.6, 1.7, 1.7, 24).translate([x, 0, sh + 6.37])
        body = body + pot - M.cylinder(5.0, 0.8, 0.8, 16).translate([x, 0, sh + 2.8])
    return body


CO.FRIEZE_EXTRA.update(byzantineknot=frieze_interlace, byzantineleaf=frieze_byzantineleaf)
CO.COURSE_EXTRA.update(nailheadstud=course_nailhead)
TW.BRACKET_EXTRA.update(rollcorbel=bracket_rollcorbel)
TW.FOUNDATION_EXTRA.update(chamfercourse=foundation_chamfercourse)
SH.CORNER_EXTRA.update(thornbury=corner_thornbury)
PW.POSTS.update(cushion=post_cushion)
PW.BALUSTERS.update(spindleknop=(baluster_spindleknop, 1.6))
PW.FRIEZES.update(syrianarch=frieze_syrianarch)
PW.SKIRTS.update(rockwall=skirt_rockwall)
FT.EDGE_EXTRA.update(corbeltable=edge_corbeltable)


# ================================================================== the Foscari (house 98)
# Venetian Gothic Revival, 1876: a palazzo after the Ca' d'Oro and the Fondaco dei Turchi for a
# shipping fortune. A ground storey of white Istrian ashlar in tall and short courses, a piano
# nobile of rose stucco patterned in the Doge's Palace lozenge diaper, twisted rope colonnettes at
# every corner. Between two corner towers (torreselle) that rise a stage over the roof, an open
# loggia of ogee arches on slender columns carries a balcony, and over it the piano nobile's
# polifora: five cusped ogee lights under a band of quatrefoil tracery. Every window is an ogee
# in a rectangular frame bordered with saw-tooth dentils, roundels (patere) in its spandrels. The
# flat roofs are edged with Venetian merlons; on the main roof stand a timber altana and funnel
# chimneys. Istrian white, rose, Verona red, a gilt frieze (the Ca' d'Oro was gilded).

FS_LEVELS = dict(hi=40.0)      # the building sets it: the upper storey's foot over the block's base


def _ogee_op(w, vs, H, n=14):
    """An ogee-headed outline: jambs from v = 0 to the springing vs, an ogee head rising H to
    its point."""
    right = _ogee(w / 2, vs, H, n)
    left = [(-x, y) for x, y in reversed(right[:-1])]
    return poly([(w / 2, 0.0)] + right + left + [(-w / 2, 0.0)])


def _ogee_cusped(w, vs, H, n=14):
    """The light of a Venetian 'fifth order' arch: the ogee with trefoil cusping in its head
    (three lobes whose meeting points are the cusps)."""
    op = _ogee_op(w, vs, H, n)
    r2 = w * 0.3
    lobes = cs_union([circle((0.0, vs + H * 0.42), w * 0.24, 20), circle((-w * 0.2, vs + H * 0.06), r2, 20),
                      circle((w * 0.2, vs + H * 0.06), r2, 20), rect(-w, -1.0, w, vs + H * 0.06)])
    return op ^ lobes


def _dentil_rect(x0, y0, x1, y1, bw=1.1, d0=0.45, d1=0.85, pu=0.9):
    """A rectangular frame band carved all round as a row of saw teeth (dentello)."""
    band = rect(x0, y0, x1, y1) - rect(x0 + bw, y0 + bw, x1 - bw, y1 - bw)
    teeth = []
    for u in np.arange(x0 + bw, x1 - bw - pu * 0.6, pu):
        teeth.append(poly([(u, y1 - bw), (u + pu, y1 - bw), (u + pu / 2, y1 - 0.12)]))
        teeth.append(poly([(u + pu / 2, y0 + 0.12), (u + pu, y0 + bw), (u, y0 + bw)]))
    for v in np.arange(y0 + bw, y1 - bw - pu * 0.6, pu):
        teeth.append(poly([(x0 + bw, v + pu), (x0 + 0.12, v + pu / 2), (x0 + bw, v)]))
        teeth.append(poly([(x1 - bw, v), (x1 - 0.12, v + pu / 2), (x1 - bw, v + pu)]))
    return [ext(band, 0.0, d0), ext(cs_union(teeth) ^ band, d0 - 0.01, d1)]


def _patera(c, r, w0=0.0, d=0.45):
    """A Byzantine roundel (patera): a moulded ring round an eight-petalled rosette and a boss."""
    out = [ext(circle(c, r, 32) - circle(c, r - 0.45, 32), w0, w0 + d + 0.15), ext(circle(c, r - 0.2, 32), w0, w0 + 0.12)]
    pet = [_lens((c[0] + (r - 0.45) * 0.5 * math.cos(a), c[1] + (r - 0.45) * 0.5 * math.sin(a)), (r - 0.45) * 0.95, 0.5, a)
           for a in np.arange(0, 2 * math.pi, math.pi / 4)]
    out.append(ext(cs_union(pet) ^ circle(c, r - 0.46, 32), w0, w0 + d))
    out.append(ext(circle(c, max(0.35, r * 0.2), 14), w0, w0 + d + 0.2))
    return out


# ------------------------------------------------------------------ wall skins, corners, foundation
def stone_istrian(region, datum=0.0, tall=2.8, short=1.4, joint=0.25, d=0.3):
    """Istrian stone ashlar in tall and short courses in turn (pseudo-isodomic), the blocks of
    each course of random length, every edge chamfered (the Foscari's ground storey)."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    rng = np.random.default_rng(17)
    out = []
    v = datum + math.floor((v0 - datum) / (tall + short)) * (tall + short) - (tall + short)
    k = 0
    while v < v1:
        hc = tall if k % 2 == 0 else short
        if v + hc > v0 - 1:
            u = u0 - rng.uniform(0.0, 5.0)
            while u < u1 + 1:
                Ls = rng.uniform(5.0, 8.6) if hc == tall else rng.uniform(7.0, 11.0)
                out.append(chamfer_box(u + joint / 2, v + joint / 2, u + Ls - joint / 2, v + hc - joint / 2, 0.0, d, c=0.18))
                u += Ls
        v += hc
        k += 1
    return union(out) ^ M.extrude(region, d + 0.2)


def stucco_diaper(region, datum=0.0, pw=6.0, ph=4.4, bar=0.5, d=0.26):
    """Rose stucco patterned in the Doge's Palace lozenge diaper: a net of raised bands crossing
    on the diagonal, a little cross in every lozenge (the Foscari's piano nobile)."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    lines, crosses = [], []
    span = (v1 - v0) + (u1 - u0) * ph / pw + 2 * ph
    k0 = math.floor((u0 - (v1 - datum) * pw / ph) / pw) - 2
    k1 = math.ceil((u1 + (v1 - datum) * pw / ph) / pw) + 2
    for k in range(k0, k1):
        x = k * pw
        lines.append(stroke([(x, datum), (x + span * pw / ph, datum + span)], bar, caps=False))
        lines.append(stroke([(x, datum), (x - span * pw / ph, datum + span)], bar, caps=False))
        lines.append(stroke([(x, datum), (x + span * pw / ph, datum - span)], bar, caps=False))
        lines.append(stroke([(x, datum), (x - span * pw / ph, datum - span)], bar, caps=False))
    jv0 = math.floor((v0 - datum) / ph) - 1
    for j in range(jv0, int((v1 - datum) / ph) + 2):
        vc = datum + j * ph + ph / 2
        for k in range(k0, k1):
            uc = k * pw + (pw / 2 if j % 2 == 0 else 0.0)
            if u0 - 2 < uc < u1 + 2:
                crosses.append(rect(uc - 0.7, vc - 0.18, uc + 0.7, vc + 0.18) + rect(uc - 0.18, vc - 0.7, uc + 0.18, vc + 0.7))
    net = cs_union(lines) ^ region
    out = [M.extrude(net, d)]
    if crosses:
        out.append(M.extrude(cs_union(crosses) ^ region, d * 0.8))
    return union(out)


def corner_foscari(L, at_start, qa, qb, w=2.4, t=0.65):
    """The Foscari's corners: a twisted rope colonnette standing on the corner itself (drawn at
    each facade's start only, so every corner has one), on a little base under a cap."""
    if not at_start:
        return M()
    H = qb - qa - 2.0
    if H < 4.0:
        return M()
    r, rs = 0.95, 0.5
    cs = cs_union([circle((rs * math.cos(a), rs * math.sin(a)), 0.55, 16) for a in (0.0, 2.094, 4.189)])
    rope = M.extrude(cs, H, int(H / 0.4), 360.0 * H / 3.2)
    base = M.cylinder(1.0, r + 0.25, r, 24)
    cap = M.cylinder(1.0, r, r + 0.25, 24)
    col = base + rope.translate([0, 0, 0.99]) + cap.translate([0, 0, H + 0.98])
    return col.rotate([-90, 0, 0]).translate([0.0, qa, 0.0])


def foundation_foscari(reg, seed=0):
    """A plinth of Istrian stone: a plain face under a bevelled water table carried on a band of
    saw teeth (the Foscari)."""
    b = reg.bounds()
    hgt = b[3] - b[1]
    out = [M.extrude(reg, 0.35)]
    top = rect(b[0] - 1, b[3] - 1.4, b[2] + 1, b[3]) ^ reg
    if not top.is_empty():
        tb = top.bounds()
        out.append(M.hull_points([(x, tb[1], 0.0) for x in (tb[0], tb[2])] + [(x, tb[1] + 0.3, 1.0) for x in (tb[0], tb[2])] +
                                 [(x, tb[3] - 0.3, 1.0) for x in (tb[0], tb[2])] + [(x, tb[3], 0.34) for x in (tb[0], tb[2])]))
    teeth = []
    for u in np.arange(b[0] + 0.3, b[2] - 0.9, 1.0):
        teeth.append(poly([(u, b[3] - 1.4), (u + 0.5, b[3] - 2.4), (u + 1.0, b[3] - 1.4)]))
    if teeth and hgt > 3.0:
        out.append(M.extrude(cs_union(teeth) ^ reg, 0.75))
    return union(out)


# ------------------------------------------------------------------ cornice ornaments
def course_dentello(L, h, b, pitch, margin, p):
    """Dentello: the Venetian saw-tooth course, a row of triangular teeth on a fillet (the
    Foscari)."""
    pu = 1.0
    n = max(1, int((L - 0.6) / pu))
    u0 = (L - n * pu) / 2
    teeth = cs_union([poly([(u0 + pu * k, 0.25), (u0 + pu * (k + 1), 0.25), (u0 + pu * (k + 0.5), h - 0.25)]) for k in range(n)])
    clip = rect(0.2, 0.0, L - 0.2, h)
    return [_st(rect(0.2, 0.15, L - 0.2, h - 0.15), b, 0.15), _st(teeth ^ clip, b + 0.14, 0.4)]


def frieze_paterae(L, h, b, pitch, margin, pair, half):
    """Patere and formelle: Byzantine roundels in turn with upright panels carved with a cross
    between two leaves, on a ground framed in fillets (the Foscari's storey joint)."""
    v0, v1 = 0.6, h - 0.6
    hh = v1 - v0
    vm = (v0 + v1) / 2
    pu = max(4.0, hh * 1.25)
    n = max(1, int((L - 1.0) / pu))
    u0 = (L - n * pu) / 2
    rings, pets, bosses, panels, crosses = [], [], [], [], []
    for k in range(n):
        c = (u0 + pu * (k + 0.5), vm)
        if k % 2 == 0:
            r = hh * 0.44
            rings.append(circle(c, r, 32) - circle(c, r - 0.42, 32))
            pets += [_lens((c[0] + (r - 0.42) * 0.5 * math.cos(a), c[1] + (r - 0.42) * 0.5 * math.sin(a)), (r - 0.42) * 0.95, 0.5, a)
                     for a in np.arange(0, 2 * math.pi, math.pi / 4)]
            bosses.append(circle(c, 0.4, 12))
        else:
            pw_, ph_ = hh * 0.62, hh * 0.86
            pan = rect(c[0] - pw_ / 2, c[1] - ph_ / 2, c[0] + pw_ / 2, c[1] + ph_ / 2)
            panels.append(pan - pan.offset(-0.4, MIT, 4.0))
            crosses.append(rect(c[0] - 0.22, c[1] - ph_ * 0.32, c[0] + 0.22, c[1] + ph_ * 0.34) +
                           rect(c[0] - pw_ * 0.28, c[1] + ph_ * 0.1 - 0.22, c[0] + pw_ * 0.28, c[1] + ph_ * 0.1 + 0.22))
            for sg in (-1, 1):
                crosses.append(_lens((c[0] + sg * pw_ * 0.18, c[1] - ph_ * 0.2), ph_ * 0.32, 0.4, math.pi / 2 - sg * 0.5))
    clip = rect(0.2, v0, L - 0.2, v1)
    frame_ = rect(0.2, v0, L - 0.2, v0 + 0.4) + rect(0.2, v1 - 0.4, L - 0.2, v1)
    return [_st(frame_, b, 0.3), _st(cs_union(rings + panels) ^ clip, b, 0.45), _st(cs_union(pets + crosses) ^ clip, b, 0.35),
            _st(cs_union(bosses) ^ clip, b, 0.6)], []


def frieze_archetti(L, h, b, pitch, margin, pair, half):
    """Archetti pensili: a corbel table of little hanging trefoil-cusped arches, a knob at every
    springing, under a fillet (the Foscari's eave, gilt)."""
    v0, v1 = 0.5, h - 0.5
    hh = v1 - v0
    pu = max(2.6, hh * 0.62)
    n = max(1, int((L - 1.0) / pu))
    u0 = (L - n * pu) / 2
    top = rect(0.2, v1 - 0.6, L - 0.2, v1)
    arcs, knobs = [], []
    for k in range(n):
        uc = u0 + pu * (k + 0.5)
        o = _ogee_cusped(pu - 0.5, hh * 0.18, hh * 0.42).translate((uc, v0 + hh * 0.18))
        oo = _ogee_op(pu + 0.3, hh * 0.18, hh * 0.46).translate((uc, v0 + hh * 0.14))
        arcs.append((oo - o) ^ rect(-1e3, v0 + hh * 0.3, 1e3, 1e3))
    for k in range(n + 1):
        u = u0 + pu * k
        knobs.append(circle((u, v0 + hh * 0.3), 0.42, 12))
    clip = rect(0.2, v0, L - 0.2, v1)
    return [_st(top, b, 0.35), _st(cs_union(arcs) ^ clip, b, 0.42), _st(cs_union(knobs) ^ clip, b, 0.55)], []


def bracket_mensola(h, d, t):
    """A Venetian mensola: a corbel built of three stepped quarter rounds, each course projecting
    over the one below (side profile, top at v = 0; the Foscari)."""
    pts = [(0.0, 0.0), (d, 0.0)]
    steps = 3
    sh = h / steps
    for k in range(steps):
        dk = d * (1.0 - k / steps)
        dn = d * (1.0 - (k + 1) / steps)
        for a in np.linspace(0.0, -math.pi / 2, 6):
            pts.append((dn + (dk - dn) * math.cos(a), -k * sh + sh * math.sin(a) * 0.999))
    pts.append((0.0, -h))
    return poly(pts)


def fence_foscari_merli(L, h):
    """Venetian merlons (drawn at full size, printed flat): a row of stepped merlons each rising
    to a pointed tip between two little horns, on a base course (the Foscari's roofs)."""
    pu = 3.6
    n = max(1, int((L - 0.8) / pu))
    u0 = (L - n * pu) / 2
    out = [rect(0.2, 0.0, L - 0.2, 1.4)]
    for k in range(n):
        uc = u0 + pu * (k + 0.5)
        w1, w2 = 1.2, 0.75
        h1, h2 = h * 0.5, h * 0.72
        out.append(poly([(uc - w1, 1.0), (uc + w1, 1.0), (uc + w1, h1), (uc + w2, h1 + 0.4), (uc + w2 + 0.35, h2),
                         (uc + 0.35, h2 - 0.2), (uc, h), (uc - 0.35, h2 - 0.2), (uc - w2 - 0.35, h2), (uc - w2, h1 + 0.4),
                         (uc - w1, h1)]))
    body = cs_union(out)
    eyes = cs_union([_quatrefoil((u0 + pu * (k + 0.5), h * 0.32), 0.3) for k in range(n)])
    return body - eyes


def fence_foscari_balcony(L, h):
    """The loggia roof's balcony front (printed flat): little columns carrying cusped ogee
    arches under a rail, on a base course."""
    pu = 2.8
    n = max(1, int((L - 1.0) / pu))
    u0 = (L - n * pu) / 2
    solid = rect(0.2, 0.0, L - 0.2, h)
    holes = cs_union([_ogee_cusped(pu - 0.9, h * 0.32, h * 0.3).translate((u0 + pu * (k + 0.5), 1.1)) for k in range(n)])
    return solid - (holes ^ rect(-1e3, 1.1, 1e3, h - 1.0))


def fence_foscari_altana(L, h):
    """The altana's timber railing (printed flat): posts, a top and a middle rail, and a St
    Andrew's cross in every bay below."""
    pu = 4.4
    n = max(1, int((L - 1.0) / pu))
    u0 = (L - n * pu) / 2
    out = [rect(0.2, h - 0.8, L - 0.2, h), rect(0.2, 0.0, L - 0.2, 0.7), rect(0.2, h * 0.55 - 0.3, L - 0.2, h * 0.55 + 0.3)]
    for k in range(n + 1):
        x = u0 + pu * k
        out.append(rect(x - 0.4, 0.0, x + 0.4, h))
    for k in range(n):
        a, b_ = u0 + pu * k, u0 + pu * (k + 1)
        out.append(stroke([(a, 0.5), (b_, h * 0.55)], 0.5))
        out.append(stroke([(a, h * 0.55), (b_, 0.5)], 0.5))
    return cs_union(out) ^ rect(0.2, 0.0, L - 0.2, h)


def finial_foscari(h=9.0):
    """A corner pinnacle for the towers: a square pedestal, an octagonal spirelet with a ring and
    a ball at its tip. Stands on its pedestal."""
    ped = box([-1.2, -1.2, 0.0], [1.2, 1.2, 2.4]) + M.hull_points([(x, y, 2.39) for x in (-1.2, 1.2) for y in (-1.2, 1.2)] +
                                                                 [(x, y, 2.9) for x in (-0.9, 0.9) for y in (-0.9, 0.9)])
    oc = circle((0.0, 0.0), 0.85, 8)
    spire = M.extrude(oc, h - 4.2, 0, 0.0, (0.25, 0.25)).translate([0, 0, 2.89])
    ring = M.cylinder(0.4, 0.9, 0.9, 16).translate([0, 0, 2.89 + (h - 4.2) * 0.35])
    return ped + spire + ring + _ball(0.55, h - 0.6, neck=0.3)


# ------------------------------------------------------------------ windows and doors
def window_foscari_upper(w=7.4, vs=16.0, H=6.4, A=0.7):
    """The piano nobile's window: a cusped ogee light (two casements, a trefoil in the head) in an
    Istrian frame, set in a rectangle of saw-tooth dentils with patere in the spandrels and a
    fleuron on the ogee's point; a balconette on two corbels, its front carved with little
    cusped arches."""
    op = _ogee_op(w, vs, H)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    inner = plug_cs.offset(-0.5, MIT, 4.0)
    tre = _ogee_cusped(w - 1.0, vs, H - 0.8).translate((0.0, 0.0))
    bars = [rect(-RIB / 2, -1.0, RIB / 2, vs + 0.2), rect(-w, vs - 0.3, w, vs + 0.3), rect(-w, vs * 0.5 - RIB / 2, w, vs * 0.5 + RIB / 2)]
    bars.append((inner - tre) ^ rect(-w, vs, w, vs + H + 2))
    sash = _glazed([ext(plug_cs, -pl, -0.6)], inner, pl, cs_union(bars), plug_cs)
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             MD.band(op.offset(A, MIT, 4.0), A, MD.ARCHITRAVE, clip=rect(-w - 10, 0.0, w + 10, vs + H + 20) - op)]
    X = w / 2 + A + 2.0
    top = vs + H + A + 2.8
    parts += _dentil_rect(-X, -0.4, X, top)
    spand = (rect(-X + 1.0, vs, X - 1.0, top - 1.0) - op.offset(A, MIT, 4.0))
    parts.append(ext(spand, 0.0, 0.2))
    for sg in (-1, 1):
        parts += _patera((sg * (X - 2.1), top - 2.6), 1.15, 0.19, 0.35)
    fl = _trefoil((0.0, vs + H + A + 0.9), 0.55) + rect(-0.25, vs + H + A - 0.3, 0.25, vs + H + A + 0.6)
    parts.append(ext(fl ^ rect(-X, -1, X, top - 1.0), 0.0, 0.9))
    bw = X - 0.2
    parts.append(chamfer_box(-bw, -3.2, bw, 0.01, 0.0, 2.6, c=0.3))
    arc = cs_union([_ogee_cusped(1.3, 0.9, 0.6).translate((u, -2.7)) for u in np.arange(-bw + 1.2, bw - 1.0, 1.9)])
    parts.append(ext(rect(-bw + 0.5, -2.8, bw - 0.5, -0.5) - arc, 2.59, 2.9))
    for sg in (-1, 1):
        parts.append(chamfer_box(sg * (bw - 1.6) - 0.8, -5.6, sg * (bw - 1.6) + 0.8, -3.19, 0.0, 2.2, c=0.3, bottom=2.2))
    return O._one_piece(sash, parts, op, plug_cs, pl, top + 0.2, -5.6)


def window_foscari_ground(w=6.0, h=16.0, A=0.6):
    """The ground storey's window: a pointed light behind an iron grille, in a plain Istrian frame
    under a hood of saw teeth, a patera over its point, a sill on two little corbels."""
    ap = _apex(w, w * 0.8)
    vs = h - ap
    op = _lancet(-w / 2, w / 2, vs, r=w * 0.8, seg=14)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    inner = plug_cs.offset(-0.5, MIT, 4.0)
    bars = [rect(x - RIB / 2, -1.0, x + RIB / 2, h + 1) for x in (-w / 6, w / 6)]
    bars += [rect(-w, v - RIB / 2, w, v + RIB / 2) for v in np.arange(3.0, vs + 0.1, 3.2)]
    sash = _glazed([ext(plug_cs, -pl, -0.6)], inner, pl, cs_union(bars), plug_cs)
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             MD.band(op.offset(A, MIT, 4.0), A, MD.CASING, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op)]
    hood = (op.offset(A + 1.2, MIT, 4.0) - op.offset(A - 0.05, MIT, 4.0)) ^ rect(-50, vs, 50, 100)
    parts.append(ext(hood, 0.0, 0.55))
    hb = hood.bounds()
    nt = []
    for x in np.arange(hb[0] + 0.4, hb[2] - 0.4, 0.9):
        nt.append(poly([(x, vs + 0.3), (x + 0.45, vs - 0.9), (x + 0.9, vs + 0.3)]))
    parts.append(ext(cs_union(nt) ^ (rect(-w / 2 - A - 1.2, vs - 1.0, -w / 2 - A + 0.1, vs + 0.3) +
                                     rect(w / 2 + A - 0.1, vs - 1.0, w / 2 + A + 1.2, vs + 0.3)), 0.0, 0.55))
    parts += _patera((0.0, hb[3] + 1.5), 1.2, 0.0, 0.4)
    parts.append(ext(rect(-0.35, hb[3] - 0.2, 0.35, hb[3] + 0.4), 0.0, 0.4))
    sw = w / 2 + A + 0.8
    parts.append(chamfer_box(-sw, -1.2, sw, 0.01, 0.0, 1.2, c=0.3, bottom=1.2))
    for sg in (-1, 1):
        parts.append(chamfer_box(sg * (w / 2 - 0.4) - 0.7, -2.6, sg * (w / 2 - 0.4) + 0.7, -1.19, 0.0, 1.0, c=0.3, bottom=1.0))
    return O._one_piece(sash, parts, op, plug_cs, pl, hb[3] + 2.9, -2.6)


def window_foscari_polifora(n=5, wl=4.4, col=1.4, vs=15.0, H=5.0, T=5.6, A=0.6):
    """The piano nobile's polifora over the loggia (after the Ca' d'Oro): five cusped ogee lights
    on slim columns, over them a band of quatrefoils in rings, all in one rectangle of saw-tooth
    dentils, a fleuron on every point; a sill course on corbels."""
    W = n * wl + (n - 1) * col
    hb = vs + H + 0.6 + T
    op = rect(-W / 2, 0.0, W / 2, hb)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    inner = plug_cs.offset(-0.4, MIT, 4.0)
    xs = [-W / 2 + wl / 2 + k * (wl + col) for k in range(n)]
    lights = cs_union([_ogee_cusped(wl, vs, H).translate((x, 0.0)) for x in xs])
    qv = vs + H + 0.6 + T / 2
    rq = T * 0.42
    rings = cs_union([circle((x + (wl + col) / 2, qv), rq, 32) for x in xs[:-1]] + [circle((x, qv), rq, 32) for x in (xs[0] - (wl + col) / 2, xs[-1] + (wl + col) / 2)])
    quats = cs_union([_quatrefoil((x + (wl + col) / 2, qv), rq * 0.42) for x in xs[:-1]])
    glass_ = lights + (quats ^ inner)
    bars = (inner - glass_)
    sash = _glazed([ext(plug_cs, -pl, -0.6)], inner, pl, bars, plug_cs)
    sash.append(ext(cs_union([rect(x - RIB / 2, 0.0, x + RIB / 2, vs) for x in xs]) ^ inner, -pl + O.GLASS - 0.01, -0.5))
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS)]
    ring_band = (rings - rings.offset(-0.45, MIT, 4.0)) ^ rect(-W / 2, vs + H + 0.6, W / 2, hb)
    parts.append(ext(ring_band, -0.6, 0.35))
    for x in [xs[0] - (wl + col) / 2] + [x + (wl + col) / 2 for x in xs]:
        xc = max(-W / 2 + 0.6, min(W / 2 - 0.6, x))
        prof = [(0.0, 0.0), (0.55, 0.0), (0.55, 0.4), (0.4, 0.7), (0.42, vs - 1.6), (0.75, vs - 0.6), (0.75, vs), (0.0, vs)]
        parts.append(PW._revolve(prof, 16).rotate([-90, 0, 0]).translate([xc, 0.0, 0.0]) ^ box([xc - 2, 0.0, 0.0], [xc + 2, vs, 2.0]))
    fl = cs_union([_trefoil((x, vs + H + 0.25), 0.4) for x in xs])
    parts.append(ext(fl ^ op, -0.6, 0.6))
    X = W / 2 + A + 1.2
    parts += _dentil_rect(-X, -0.6, X, hb + A + 1.2, bw=1.2)
    parts.append(ext(rect(-X + 1.1, -0.5, X - 1.1, hb + A + 0.1) - op, 0.0, 0.25))
    parts.append(chamfer_box(-X - 0.6, -1.8, X + 0.6, -0.59, 0.0, 1.4, c=0.3, bottom=1.4))
    for x in [xs[0] - (wl + col) / 2 + 0.5, xs[-1] + (wl + col) / 2 - 0.5] + [x + (wl + col) / 2 for x in xs[:-1]]:
        parts.append(chamfer_box(x - 0.7, -3.4, x + 0.7, -1.79, 0.0, 1.2, c=0.3, bottom=1.2))
    return O._one_piece(sash, parts, op, plug_cs, pl, hb + A + 1.4, -3.4)


def window_foscari_bifora(wl=4.0, col=1.2, vs=10.0, H=4.2, A=0.5):
    """A tower's bifora: two cusped ogee lights parted by a column, a quatrefoil oculus over
    them, in a dentil rectangle."""
    W = 2 * wl + col
    hb = vs + H + 4.2
    op = rect(-W / 2, 0.0, W / 2, hb)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    inner = plug_cs.offset(-0.4, MIT, 4.0)
    xs = (-(wl + col) / 2, (wl + col) / 2)
    lights = cs_union([_ogee_cusped(wl, vs, H).translate((x, 0.0)) for x in xs])
    oc = (0.0, vs + H + 1.6)
    quat = _quatrefoil(oc, 0.75)
    glass_ = lights + quat
    sash = _glazed([ext(plug_cs, -pl, -0.6)], inner, pl, inner - glass_, plug_cs)
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS)]
    parts.append(ext(circle(oc, 1.9, 28) - circle(oc, 1.45, 28), -0.6, 0.35))
    prof = [(0.0, 0.0), (0.5, 0.0), (0.5, 0.4), (0.38, 0.7), (0.4, vs - 1.4), (0.68, vs - 0.5), (0.68, vs), (0.0, vs)]
    parts.append(PW._revolve(prof, 16).rotate([-90, 0, 0]) ^ box([-2, 0.0, 0.0], [2, vs, 2.0]))
    X = W / 2 + A + 1.1
    parts += _dentil_rect(-X, -0.5, X, hb + A + 1.1, bw=1.1)
    parts.append(ext(rect(-X + 1.0, -0.4, X - 1.0, hb + A) - op, 0.0, 0.22))
    parts.append(chamfer_box(-X - 0.4, -1.6, X + 0.4, -0.49, 0.0, 1.2, c=0.3, bottom=1.2))
    return O._one_piece(sash, parts, op, plug_cs, pl, hb + A + 1.3, -1.6)


def door_foscari(w=11.0, h=24.0, A=1.0, back=False):
    """The Foscari's portal: a pair of leaves of studded panels under a tympanum carved with a
    shield bearing a lily, in a cusped ogee arch of Istrian stone with a carved leaf band, all in
    a rectangle of saw-tooth dentils; an ogee hood with crockets rises to a fleuron. The back
    door (``back``) drops the hood and the crockets."""
    H = w * 0.62
    vs = h - H
    op = _ogee_op(w, vs, H, n=18)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    inner = plug_cs.offset(-0.5, MIT, 4.0)
    ja = w / 2 - O.CLR - 0.5
    dh = vs - 0.3
    body = [ext(plug_cs, -pl, -1.0), ext(rect(-ja, 0.5, ja, dh), -pl, -0.8)]
    for sg in (-1, 1):
        x0, x1 = sorted((sg * 0.35, sg * (ja - 0.4)))
        for v0_, v1_ in ((1.2, dh * 0.45), (dh * 0.5, dh - 0.6)):
            body.append(ext(rect(x0 + 0.3, v0_, x1 - 0.3, v1_) - rect(x0 + 0.8, v0_ + 0.5, x1 - 0.8, v1_ - 0.5), -0.81, -0.5))
            for x in np.linspace(x0 + 0.9, x1 - 0.9, 3):
                for v in np.linspace(v0_ + 1.0, v1_ - 1.0, max(2, int((v1_ - v0_) / 2.6))):
                    body.append(ext(circle((x, v), 0.32, 8), -0.81, -0.45))
    tym = inner ^ rect(-w, dh + 0.5, w, h + 2)
    shield = poly([(-1.6, vs + H * 0.55), (1.6, vs + H * 0.55), (1.6, vs + H * 0.2), (0.0, vs - 0.6 + H * 0.05), (-1.6, vs + H * 0.2)])
    lily = _trefoil((0.0, vs + H * 0.33), 0.5) + rect(-0.2, vs + H * 0.12, 0.2, vs + H * 0.36)
    rays = cs_union([stroke([(0.0, dh + 0.5), (w * math.cos(t_), dh + 0.5 + w * math.sin(t_))], RIB) for t_ in (0.45, math.pi - 0.45)])
    sash = _glazed(body, tym, pl, (shield + rays) ^ tym, plug_cs)
    sash.append(ext(lily ^ tym, -0.51, -0.2))
    sash.append(ext(rect(-w, dh - 0.01, w, dh + 0.52) ^ plug_cs, -pl, -0.5))
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             MD.band(op.offset(A, MIT, 4.0), A, MD.ARCHITRAVE, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op)]
    lb = (op.offset(A + 1.5, MIT, 4.0) - op.offset(A - 0.05, MIT, 4.0)) ^ rect(-50, 0.0, 50, 100)
    parts.append(ext(lb, 0.0, 0.5))
    leaves = []
    for v in np.arange(0.8, vs, 1.6):
        for sg in (-1, 1):
            leaves.append(_lens((sg * (w / 2 + A + 0.75), v + 0.8), 1.3, 0.45, math.pi / 2 + sg * 0.5))
    parts.append(ext(cs_union(leaves) ^ lb, 0.49, 0.8))
    X = w / 2 + A + 3.0
    top = h + A + (2.4 if back else 4.6)
    parts += _dentil_rect(-X, -0.6, X, top, bw=1.2)
    parts.append(ext(rect(-X + 1.1, -0.5, X - 1.1, top - 1.1) - op.offset(A + 1.5, MIT, 4.0), 0.0, 0.25))
    if not back:
        for sg in (-1, 1):
            parts += _patera((sg * (X - 2.4), top - 3.0), 1.2, 0.24, 0.4)
        right = _ogee(w / 2 + A + 1.5, vs, H + A + 1.5, 18)
        for t_ in (0.3, 0.55, 0.78):
            p = right[int(t_ * (len(right) - 1))]
            for sg in (-1, 1):
                parts.append(ext(_lens((sg * p[0] + sg * 0.5, p[1] + 0.3), 1.3, 0.55, math.pi / 2 - sg * 0.7) ^ rect(-X + 1.1, 0, X - 1.1, top - 1.1), 0.49, 0.9))
        parts.append(ext(_trefoil((0.0, h + A + 2.6), 0.75) + rect(-0.3, h + A + 1.0, 0.3, h + A + 2.2), 0.0, 0.9))
    parts.append(ext(rect(-X, -0.6, X, 0.01), 0.0, 1.4))
    return O._one_piece(sash, parts, op, plug_cs, pl, top + 0.2, -0.6)


# ------------------------------------------------------------------ the loggia
def post_foscari(h, collar=None, abacus=3.2, slot=(1.2, 1.0)):
    """A Venetian Gothic column: an Attic base on a square plinth, a slender shaft, a basket
    capital whose bell carries four leaves curling out under the corners of a square impost
    (the Foscari's loggia)."""
    zc = h - 4.2
    r = 0.95
    prof = [(0.0, 1.19), (1.35, 1.19), (1.35, 1.45), (1.1, 1.7), (1.2, 1.95), (r, 2.25), (r, zc - 0.4), (1.15, zc - 0.25), (1.15, zc), (r, zc + 0.15)]
    body = PW._revolve(prof, 24) + PW._plinth(3.0)
    body = body + PW._top(h, abacus / 2, zc + 0.15, r, slot, seg=24, shape="round")
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        c, s_ = math.cos(a), math.sin(a)
        leaf = M.hull_points([(r * 0.9 * c, r * 0.9 * s_, zc + 0.4), ((r + 0.8) * c, (r + 0.8) * s_, zc + 1.6),
                              ((r + 0.4) * c - 0.4 * s_, (r + 0.4) * s_ + 0.4 * c, zc + 1.0), ((r + 0.4) * c + 0.4 * s_, (r + 0.4) * s_ - 0.4 * c, zc + 1.0),
                              (r * 0.9 * c, r * 0.9 * s_, zc + 1.9)])
        body = body + leaf
    return body


def baluster_foscaritwist(h, seg=16):
    """A twisted colonnette for the loggia railing: a spiral-fluted shaft between a square foot
    and a square cap."""
    H = h - 1.6
    cs = cs_union([circle((0.18 * math.cos(a), 0.18 * math.sin(a)), 0.27, 12) for a in (0.0, 2.094, 4.189)])
    tw = M.extrude(cs, H, int(H / 0.4), 360.0 * H / 2.4).translate([0, 0, 0.79])
    return tw + box([-0.55, -0.55, 0.0], [0.55, 0.55, 0.81]) + box([-0.55, -0.55, h - 0.81], [0.55, 0.55, h])


def frieze_ogeearcade(u0, u1, v_bot, v_top):
    """The loggia's arcade: a cusped ogee arch between every two columns, a patera pierced as a
    quatrefoil in each spandrel where there is room (the Foscari)."""
    L = u1 - u0
    um = (u0 + u1) / 2
    hh = v_top - v_bot
    H = min(hh - 1.4, (L - 0.6) * 0.62)
    vs = v_top - 1.0 - H
    solid = rect(u0, v_bot, u1, v_top + 0.05)
    hole = _ogee_cusped(L - 0.6, vs - (v_bot - 1.0), H).translate((um, v_bot - 1.0))
    out = solid - hole
    rq = min(0.9, (v_top - 1.0 - (vs + H * 0.55)) * 0.3)
    if rq > 0.45 and L > 8.0:
        for sg in (-1, 1):
            out = out - _quatrefoil((um + sg * (L / 2 - 1.8), vs + H * 0.75), rq * 0.6)
    return out


def edge_dentello(L, z0, zc):
    """Loggia fascia (the Foscari): a fillet under the crown hung with a row of saw teeth."""
    out = [rect(0.3, zc - 0.6, L - 0.3, zc)]
    pu = 1.2
    n = max(1, int((L - 1.0) / pu))
    u0 = (L - n * pu) / 2
    out += [poly([(u0 + pu * k, zc - 0.55), (u0 + pu * (k + 0.5), zc - 1.6), (u0 + pu * (k + 1), zc - 0.55)]) for k in range(n)]
    return cs_union(out) ^ rect(0.3, -1e3, L - 0.3, 1e3), 0.6


def skirt_foscari(reg, d=1.2):
    """The loggia's base between the piers: Istrian panels each set with a Verona roundel."""
    u0, v0, u1, v1 = reg.bounds()
    out = [M.extrude(reg, d * 0.4)]
    n = max(1, int((u1 - u0) / 8.0))
    pw_ = (u1 - u0) / n
    for k in range(n):
        a = u0 + pw_ * k
        pan = rect(a + 0.6, v0 + 0.6, a + pw_ - 0.6, v1 - 0.6)
        out.append(ext(pan - pan.offset(-0.5, MIT, 4.0), d * 0.4 - 0.01, d * 0.8))
        c = (a + pw_ / 2, (v0 + v1) / 2)
        r = min((v1 - v0) * 0.3, pw_ * 0.25)
        if r > 0.9:
            out += _patera(c, r, d * 0.4, 0.35)
    return union(out) ^ M.extrude(reg, d + 0.5)


# ------------------------------------------------------------------ the roof
def chimney_foscari(s=6.0, h=28.0):
    """A Venetian funnel chimney (fumaiolo): a square stuccoed shaft on a moulded base, a collar,
    and an inverted cone flaring at 30 degrees to a rim of little merlons round a domed cap.
    Prints upright."""
    h = round(h / 0.2) * 0.2
    sh = h - 9.0
    body = box([-s / 2, -s / 2, 0.0], [s / 2, s / 2, sh])
    body = body + M.hull_points([(x, y, 0.0) for x in (-s / 2 - 0.8, s / 2 + 0.8) for y in (-s / 2 - 0.8, s / 2 + 0.8)] +
                                [(x, y, 1.2) for x in (-s / 2 - 0.8, s / 2 + 0.8) for y in (-s / 2 - 0.8, s / 2 + 0.8)] +
                                [(x, y, 2.0) for x in (-s / 2, s / 2) for y in (-s / 2, s / 2)])
    body = body + M.hull_points([(x, y, sh - 0.01) for x in (-s / 2, s / 2) for y in (-s / 2, s / 2)] +
                                [(x, y, sh + 0.8) for x in (-s / 2 - 0.8, s / 2 + 0.8) for y in (-s / 2 - 0.8, s / 2 + 0.8)] +
                                [(x, y, sh + 1.6) for x in (-s / 2 - 0.8, s / 2 + 0.8) for y in (-s / 2 - 0.8, s / 2 + 0.8)])
    r0 = s * 0.42
    r1 = r0 + 5.0 * math.tan(math.radians(30.0))
    neck = M.cylinder(1.0, r0, r0, 32).translate([0, 0, sh + 1.59])
    funnel = M.cylinder(5.0, r0, r1, 32).translate([0, 0, sh + 2.58])
    rim = M.cylinder(0.8, r1, r1, 32).translate([0, 0, sh + 7.57])
    body = body + neck + funnel + rim
    for k in range(10):
        a = 2 * math.pi * k / 10
        body = body + box([-0.45, -0.45, 0.0], [0.45, 0.45, 1.0]).rotate([0, 0, math.degrees(a)]).translate(
            [(r1 - 0.45) * math.cos(a), (r1 - 0.45) * math.sin(a), sh + 8.36])
    cap = M.cylinder(0.6, r1 - 0.9, r1 - 1.3, 32).translate([0, 0, sh + 8.36]) + _ball(r1 * 0.35, sh + 8.9, neck=0.0)
    return body + cap


def altana_foscari(w, d, h, post=1.4):
    """The altana: a timber roof terrace, a planked platform on six posts with knee braces at 45
    degrees, a peg under every post. Local: the posts' feet at z = 0 (on the roof deck), the
    platform's planked top at z = h + 1.2. One part, printed upside down on its planks."""
    out = []
    xs = (-w / 2 + post, 0.0, w / 2 - post)
    ys = (-d / 2 + post, d / 2 - post)
    plat = box([-w / 2, -d / 2, h], [w / 2, d / 2, h + 1.2])
    slots = union([box([-w / 2 + 1.0, y - 0.15, h + 0.9], [w / 2 - 1.0, y + 0.15, h + 1.3]) for y in np.arange(-d / 2 + 1.6, d / 2 - 1.0, 1.6)])
    out.append(plat - slots)
    out.append(box([-w / 2, -d / 2, h - 1.0], [w / 2, -d / 2 + 1.0, h + 0.01]))
    out.append(box([-w / 2, d / 2 - 1.0, h - 1.0], [w / 2, d / 2, h + 0.01]))
    for x in xs:
        for y in ys:
            out.append(box([x - post / 2, y - post / 2, 0.0], [x + post / 2, y + post / 2, h + 0.01]))
            out.append(box([x - 0.5, y - 0.5, -0.8], [x + 0.5, y + 0.5, 0.01]))
            sg = 1 if y < 0 else -1
            for dx in ((-1, 1) if x == 0.0 else ((1,) if x < 0 else (-1,))):
                k = 2.6
                out.append(M.hull_points([(x + dx * post / 2, y + a, z) for a in (-0.35, 0.35) for z in (h - 1.0 - k, h - 1.0 - k + 0.7)] +
                                         [(x + dx * (post / 2 + k), y + a, z) for a in (-0.35, 0.35) for z in (h - 1.0, h - 0.99)]))
    return union(out)


CO.FRIEZE_EXTRA.update(pateraeformelle=frieze_paterae, archetti=frieze_archetti)
CO.COURSE_EXTRA.update(dentello=course_dentello)
TW.BRACKET_EXTRA.update(mensola=bracket_mensola)
TW.FOUNDATION_EXTRA.update(foscari=foundation_foscari)
SH.CORNER_EXTRA.update(foscari=corner_foscari)
PW.POSTS.update(foscari=post_foscari)
PW.BALUSTERS.update(foscaritwist=(baluster_foscaritwist, 1.4))
PW.FRIEZES.update(venetianogee=frieze_ogeearcade)
PW.SKIRTS.update(foscari=skirt_foscari)
FT.EDGE_EXTRA.update(dentello=edge_dentello)


# ================================================================== the Carrington (house 99)
# Southern Colonial Revival, 1906: a cotton factor's mansion. Two storeys of butter-yellow
# bevelled clapboard on a red brick base with arched iron-grilled vents, panelled corner
# pilasters, every window a six-over-six sash between louvered plantation shutters. At the
# middle of the front a bowed bay, and round it a colossal portico of six Ionic columns on a
# curved plan carrying a full entablature and a balustrade; inside it, at the second floor, a
# curved cast-iron balcony on consoles. The front door has a leaded elliptical fanlight and
# sidelights between fluted pilasters; over it a Palladian window. A hipped slate roof with
# pedimented dormers rises to a widow's walk; tall panelled brick chimneys stand at each end.
# Cornices of ribbon-bound reeds, swags hung from bow-knots, Prince-of-Wales plumes and volute
# modillions.

CR_LEVELS = dict(hi=40.0)


def lap_carrington(region, datum=0.0, ch=1.6, d=0.36, joint_every=34.0, seed=5):
    """Bevelled clapboard: every course a wedge, thick at its butt and feathered at its top, so
    the shadow line falls under each butt; the boards butt-jointed at random, staggered course to
    course (the Carrington's walls)."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    rng = np.random.default_rng(seed)
    out = []
    k = math.floor((v0 - datum) / ch) - 1
    while datum + k * ch < v1 + ch:
        v = datum + k * ch
        out.append(M.hull_points([(x, v, z) for x in (u0 - 1, u1 + 1) for z in (0.0,)] + [(x, v, d) for x in (u0 - 1, u1 + 1)] +
                                 [(x, v + ch, 0.0) for x in (u0 - 1, u1 + 1)] + [(x, v + ch - 0.01, 0.1) for x in (u0 - 1, u1 + 1)]))
        k += 1
    body = union(out)
    cuts = []
    k = math.floor((v0 - datum) / ch) - 1
    while datum + k * ch < v1 + ch:
        v = datum + k * ch
        u = u0 - rng.uniform(0.0, joint_every)
        while u < u1 + 1:
            cuts.append(box([u - 0.1, v + 0.05, 0.12], [u + 0.1, v + ch - 0.05, 1.0]))
            u += rng.uniform(joint_every * 0.6, joint_every * 1.4)
        k += 1
    if cuts:
        body = body - union(cuts)
    return body ^ M.extrude(region, d + 0.1)


def corner_carrington(L, at_start, qa, qb, w=2.4, t=0.65):
    """The Carrington's corners: a panelled pilaster on each face, a sunk panel between a base
    block and a moulded capital, one per storey's height (it stops under the cornices)."""
    def span(a, b):
        return (a, b) if at_start else (L - b, L - a)
    pw = 2.8
    u0, u1 = span(-0.65, pw)
    if qb - qa < 6.0:
        return M()
    parts = [box([u0, qa, 0.0], [u1, qb, 0.65])]
    p0, p1 = span(0.55, pw - 0.6)
    parts = [parts[0] - box([p0, qa + 2.6, 0.45], [p1, qb - 2.6, 1.0])]
    b0, b1 = span(-0.85, pw + 0.2)
    parts.append(chamfer_box(b0, qa, b1, qa + 1.8, 0.0, 0.85, c=0.2))
    parts.append(chamfer_box(b0, qb - 1.4, b1, qb, 0.0, 0.85, c=0.2, bottom=0.85))
    parts.append(chamfer_box(min(span(-0.65, pw)), qb - 2.0, max(span(-0.65, pw)), qb - 1.39, 0.0, 0.75, c=0.15, bottom=0.75))
    return union(parts)


def foundation_carrington(reg, seed=0):
    """A red brick base in stretcher bond under a moulded water table, an arched vent with an
    iron grille every 22 mm (the Carrington)."""
    b = reg.bounds()
    out = [M.extrude(reg, 0.3)]
    cells = []
    for k, v in enumerate(np.arange(b[1], b[3] - 1.2, 0.8)):
        off = 0.0 if k % 2 == 0 else 1.0
        for u in np.arange(b[0] - 2.0 + off, b[2] + 1.0, 2.0):
            cells.append(rect(u + 0.1, v + 0.1, u + 1.9, v + 0.7))
    if cells:
        out.append(M.extrude(cs_union(cells) ^ reg, 0.5))
    top = rect(b[0] - 1, b[3] - 1.2, b[2] + 1, b[3]) ^ reg
    if not top.is_empty():
        tb = top.bounds()
        out.append(M.hull_points([(x, tb[1], 0.0) for x in (tb[0], tb[2])] + [(x, tb[1] + 0.3, 0.9) for x in (tb[0], tb[2])] +
                                 [(x, tb[3], 0.9) for x in (tb[0], tb[2])] + [(x, tb[3], 0.3) for x in (tb[0], tb[2])]))
    body = union(out)
    hgt = b[3] - b[1]
    if hgt > 4.0:
        for u in np.arange(b[0] + 11.0, b[2] - 6.0, 22.0):
            vent = O.opening_cs(3.0, min(3.2, hgt - 2.4), 1.5).translate((u, b[1] + 0.8))
            body = body - M.extrude(vent, 2.0).translate([0, 0, 0.0])
            bars = cs_union([rect(x - 0.22, b[1] + 0.6, x + 0.22, b[3]) for x in (u - 0.75, u, u + 0.75)]) ^ vent
            body = body + M.extrude(vent, 0.15) + M.extrude(bars, 0.25)
    return body


# ------------------------------------------------------------------ cornice ornaments
def course_ribbonreed(L, h, b, pitch, margin, p):
    """Ribbon and reed: a bundle of three reeds bound by a ribbon crossing them on the diagonal
    every 3 mm (the Carrington)."""
    reeds = [rect(0.2, h * f - 0.18, L - 0.2, h * f + 0.18) for f in (0.25, 0.5, 0.75)]
    pu = 3.0
    n = max(1, int((L - 0.6) / pu))
    u0 = (L - n * pu) / 2
    rib = cs_union([poly([(u0 + pu * k - 0.25, 0.1), (u0 + pu * k + 0.35, 0.1), (u0 + pu * k + 0.95, h - 0.1), (u0 + pu * k + 0.35, h - 0.1)])
                    for k in range(n + 1)])
    clip = rect(0.2, 0.0, L - 0.2, h)
    return [_st(rect(0.2, 0.1, L - 0.2, h - 0.1), b, 0.12), _st(cs_union(reeds) ^ clip, b + 0.11, 0.3), _st(rib ^ clip, b + 0.11, 0.45)]


def frieze_bowknotswags(L, h, b, pitch, margin, pair, half):
    """Swags and bow-knots: drapery swags, each of two folds, hung between ribbon bow-knots with
    tails falling below them (the Carrington's storey joint)."""
    v0, v1 = 0.5, h - 0.5
    hh = v1 - v0
    pu = max(5.0, hh * 1.4)
    n = max(1, int((L - 1.0) / pu))
    u0 = (L - n * pu) / 2
    sw, knots = [], []
    vt = v1 - hh * 0.22
    for k in range(n):
        a, c = u0 + pu * k, u0 + pu * (k + 1)
        sw.append(swag(a + 0.4, c - 0.4, vt, hh * 0.42, width=0.6))
        sw.append(swag(a + 0.8, c - 0.8, vt - 0.2, hh * 0.24, width=0.45))
    for k in range(n + 1):
        u = u0 + pu * k
        knots.append(cs_union([_lens((u - 0.5, vt + 0.25), 1.2, 0.6, 0.35), _lens((u + 0.5, vt + 0.25), 1.2, 0.6, -0.35),
                               circle((u, vt), 0.35, 10), stroke([(u - 0.15, vt), (u - 0.45, vt - hh * 0.55)], 0.35),
                               stroke([(u + 0.15, vt), (u + 0.45, vt - hh * 0.5)], 0.35)]))
    clip = rect(0.2, v0, L - 0.2, v1)
    return [_st(cs_union(sw) ^ clip, b, 0.42), _st(cs_union(knots) ^ clip, b, 0.55)], []


def frieze_plumes(L, h, b, pitch, margin, pair, half):
    """Prince of Wales plumes: three ostrich feathers bound in a little coronet, the outer two
    curling out, between small hanging festoons (the Carrington's eave)."""
    v0, v1 = 0.5, h - 0.5
    hh = v1 - v0
    pu = max(5.0, hh * 0.95)
    n = max(1, int((L - 1.0) / pu))
    u0 = (L - n * pu) / 2
    feathers, crowns, fest = [], [], []
    for k in range(n):
        u = u0 + pu * (k + 0.5)
        base = v0 + hh * 0.18
        feathers.append(_lens((u, base + hh * 0.42), hh * 0.72, 1.0, math.pi / 2))
        for sg in (-1, 1):
            pts = [(u + sg * (0.3 + 1.6 * t_ ** 1.2) * (hh / 5.0), base + hh * 0.62 * math.sin(t_ * math.pi * 0.62) + 0.2)
                   for t_ in np.linspace(0.0, 1.0, 9)]
            feathers.append(stroke(pts, 0.75))
        crowns.append(rect(u - 0.8, base - 0.5, u + 0.8, base + 0.25))
        if k < n - 1:
            fest.append(swag(u + 1.6, u + pu - 1.6, v1 - 0.4, hh * 0.3, width=0.5))
    clip = rect(0.2, v0, L - 0.2, v1)
    return [_st(cs_union(feathers) ^ clip, b, 0.45), _st(cs_union(crowns) ^ clip, b, 0.6), _st(cs_union(fest) ^ clip, b, 0.35)], []


def bracket_volutemod(h, d, t):
    """A volute modillion: a long block ending in a front volute, its underside curling back in a
    smaller reverse scroll (side profile, top at v = 0; the Carrington)."""
    r1 = min(h * 0.48, d * 0.3)
    pts = [(0.0, 0.0), (d - r1, 0.0)]
    cx, cy = d - r1, -r1
    for a in np.linspace(math.pi / 2, -math.pi, 14):
        pts.append((cx + r1 * math.cos(a), cy + r1 * math.sin(a)))
    pts += [(d - 2 * r1, -h * 0.62)]
    r2 = h * 0.2
    for a in np.linspace(0.0, -math.pi / 2, 6):
        pts.append((d * 0.3 + r2 * math.cos(a) * 1.4, -h + r2 + r2 * math.sin(a)))
    pts += [(0.0, -h)]
    return poly(pts)


def festoonchain(L, h):
    """A crest course: little festoons hung between beads on a fillet (the Carrington's
    roof)."""
    pu = 2.4
    n = max(1, int((L - 0.6) / pu))
    u0 = (L - n * pu) / 2
    cells = [rect(0.2, 0.05, L - 0.2, 0.45), rect(0.2, h - 0.65, L - 0.2, h - 0.05)]
    cells += [swag(u0 + pu * k + 0.35, u0 + pu * (k + 1) - 0.35, h - 0.6, h * 0.42, width=0.5) for k in range(n)]
    cells += [circle((u0 + pu * k, h - 0.9), 0.42, 10) for k in range(n + 1)]
    cells += [rect(u0 + pu * k - 0.22, 0.3, u0 + pu * k + 0.22, h - 0.6) for k in range(n + 1)]
    return [cs_union(cells) ^ rect(0.2, 0.05, L - 0.2, h - 0.05)]


def fence_carrington_balustrade(L, h):
    """The Carrington's balustrade (printed flat): turned balusters in silhouette between a rail
    and a plinth, a panelled pedestal every 14 mm with a ball on it."""
    pr = 0.7
    out = [rect(0.2, 0.0, L - 0.2, pr), rect(0.2, h - 1.6, L - 0.2, h - 0.8)]
    npd = max(1, int((L - 1.0) / 14.0))
    peds = [0.9 + (L - 1.8) * k / npd for k in range(npd + 1)]
    for x in peds:
        out.append(rect(x - 0.9, 0.0, x + 0.9, h - 0.6))
        out.append(rect(x - 1.1, h - 0.8, x + 1.1, h - 0.3))
        out.append(circle((x, h + 0.4), 0.75, 16))
        out.append(rect(x - 0.3, h - 0.4, x + 0.3, h + 0.0))
    for a, c in zip(peds[:-1], peds[1:]):
        m = max(1, int((c - a - 1.8) / 1.8))
        for x in np.linspace(a + 0.9 + (c - a - 1.8) / (2 * m), c - 0.9 - (c - a - 1.8) / (2 * m), m):
            out.append(rect(x - 0.46, pr - 0.05, x + 0.46, h - 1.55))
            out.append(oval((x, pr + (h - pr - 1.6) * 0.32), 0.68, (h - pr - 1.6) * 0.22, 16))
    return cs_union(out)


def fence_carrington_iron(L, h):
    """The balcony's cast-iron railing (drawn at half size for SE.printable, so every bar comes
    out 0.9 mm or more): a Greek-key band over a row of anthemion panels between a top rail and
    a bottom bar."""
    bw = 0.46
    out = [rect(0.1, 0.0, L - 0.1, bw), rect(0.1, h - bw, L - 0.1, h), rect(0.1, h * 0.68 - bw / 2, L - 0.1, h * 0.68 + bw / 2)]
    pu = 2.4
    n = max(1, int((L - 0.4) / pu))
    u0 = (L - n * pu) / 2
    for k in range(n + 1):
        x = u0 + pu * k
        out.append(rect(x - bw / 2, 0.0, x + bw / 2, h))
    for k in range(n):
        x = u0 + pu * (k + 0.5)
        out.append(_lens((x, h * 0.36), h * 0.62, 0.5, math.pi / 2))
        for sg in (-1, 1):
            out.append(stroke([(x, bw), (x + sg * 0.42, h * 0.2), (x + sg * 0.62, h * 0.42)], bw))
        y0, y1 = h * 0.68, h - bw / 2
        if y1 - y0 > 1.4:
            out.append(stroke([(x - 0.75, y0), (x - 0.75, y1 - 0.2), (x + 0.45, y1 - 0.2), (x + 0.45, (y0 + y1) / 2), (x - 0.15, (y0 + y1) / 2)], bw))
    return cs_union(out) ^ rect(0.1, 0.0, L - 0.1, h)


# ------------------------------------------------------------------ windows, doors, dormers
def shutter_plantation(w, h, t=0.8):
    """A plantation shutter: two louvered fields parted by a centre rail, its top rail cut in a
    shallow arch (the Carrington). Local as features.shutter (back at w = 0; face up)."""
    st = 0.6
    web = 0.4
    out = [ext(rect(0, 0, w, h) - rect(st, st, w - st, h - st), 0.0, t)]
    rv = round(h * 0.45 / 0.2) * 0.2
    out.append(ext(rect(st, rv - 0.35, w - st, rv + 0.35), 0.0, t))
    top = rect(st, h - st - 0.9, w - st, h - st) - oval((w / 2, h - st - 0.9), (w - 2 * st) / 2 - 0.1, 0.6, 24)
    out.append(ext(top, 0.0, t))
    for v0_, v1_ in ((st, rv - 0.35), (rv + 0.35, h - st - 0.9)):
        field = rect(st, v0_, w - st, v1_)
        out.append(ext(field, 0.0, web))
        n = max(1, int((v1_ - v0_ - 0.3) / 0.9))
        pitch = (v1_ - v0_ - 0.3) / n
        slats = [rect(st - 0.05, v0_ + 0.3 + k * pitch, w - st + 0.05, v0_ + 0.3 + k * pitch + min(RIB + 0.05, pitch - 0.3)) for k in range(n)]
        out.append(ext(cs_union(slats) ^ field.offset(0.05), web - 0.01, t - 0.2))
    return union(out)


def _shutters(w, h, sw, gap=-0.05):
    """A pair of plantation shutters beside an opening ``w`` wide, ``h`` tall."""
    return [shutter_plantation(sw, h).translate([-(w / 2 + gap + sw), 0, 0]), shutter_plantation(sw, h).translate([w / 2 + gap, 0, 0])]


def _sixsix(w, h, pl, plug_cs):
    """A six-over-six sash in the plug: muntins over the glass, a meeting rail."""
    inner = plug_cs.offset(-0.55, MIT, 4.0)
    ib = inner.bounds()
    bars = [rect(-w, (ib[1] + ib[3]) / 2 - 0.35, w, (ib[1] + ib[3]) / 2 + 0.35)]
    for x in (ib[0] + (ib[2] - ib[0]) / 3, ib[0] + 2 * (ib[2] - ib[0]) / 3):
        bars.append(rect(x - RIB / 2, -1.0, x + RIB / 2, h + 1))
    for f_ in (0.25, 0.75):
        v = ib[1] + (ib[3] - ib[1]) * f_
        bars.append(rect(-w, v - RIB / 2, w, v + RIB / 2))
    return _glazed([ext(plug_cs, -pl, -0.6)], inner, pl, cs_union(bars), plug_cs)


def window_carrington_lower(w=7.6, h=17.0, A=0.8):
    """The ground storey's window: a six-over-six sash in a moulded architrave between plantation
    shutters, under a cornice cap with a frieze tablet carved with a small festoon; a sill."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    sash = _sixsix(w, h, pl, plug_cs)
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             MD.band(op.offset(A, MIT, 4.0), A, MD.ARCHITRAVE, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op)]
    X = w / 2 + A
    parts.append(ext(rect(-X, h + A - 0.01, X, h + A + 2.2), 0.0, 0.6))
    parts.append(ext(swag(-X + 1.2, X - 1.2, h + A + 1.9, 1.0, width=0.5) + circle((-X + 1.2, h + A + 1.9), 0.4, 10) + circle((X - 1.2, h + A + 1.9), 0.4, 10),
                     0.59, 0.95))
    parts.append(chamfer_box(-X - 0.8, h + A + 2.19, X + 0.8, h + A + 3.0, 0.0, 1.1, c=0.3, bottom=1.1))
    parts.append(chamfer_box(-X - 1.2, h + A + 2.99, X + 1.2, h + A + 3.6, 0.0, 1.4, c=0.3, bottom=0.5))
    parts += _shutters(w + 2 * A, h, 3.6)
    parts.append(chamfer_box(-X - 0.6, -1.0, X + 0.6, 0.01, 0.0, 1.2, c=0.3, bottom=1.2))
    return O._one_piece(sash, parts, op, plug_cs, pl, h + A + 3.8, -1.0)


def window_carrington_upper(w=7.6, h=15.6, A=0.8):
    """The upper storey's window: a six-over-six sash between plantation shutters under a flat
    arch of splayed voussoirs with a raised keystone; a sill."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    sash = _sixsix(w, h, pl, plug_cs)
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             MD.band(op.offset(A, MIT, 4.0), A, MD.CASING, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op)]
    X = w / 2 + A
    ha = 2.6
    arch = poly([(-X, h + A - 0.01), (X, h + A - 0.01), (X + 1.2, h + A + ha), (-X - 1.2, h + A + ha)])
    joints = cs_union([stroke([(x, h + A), (x * 1.25, h + A + ha + 0.2)], 0.22) for x in np.linspace(-X + 1.0, X - 1.0, 6) if abs(x) > 1.0])
    parts.append(ext(arch, 0.0, 0.7) - ext(joints, 0.5, 1.0))
    parts.append(chamfer_box(-0.9, h + A - 0.4, 0.9, h + A + ha + 0.6, 0.0, 1.2, c=0.25))
    parts += _shutters(w + 2 * A, h, 3.6)
    parts.append(chamfer_box(-X - 0.6, -1.0, X + 0.6, 0.01, 0.0, 1.2, c=0.3, bottom=1.2))
    return O._one_piece(sash, parts, op, plug_cs, pl, h + A + ha + 0.8, -1.0)


def window_carrington_palladian(wc=6.4, ws=3.2, h=16.0, A=0.7):
    """The Palladian window over the front door: a round-headed six-light centre between two
    narrow side lights under an entablature, fluted pilasters between, a keystone."""
    W = wc + 2 * ws + 2 * 1.4
    hs = h - wc / 2 - 0.8
    op = cs_union([O.opening_cs(wc, h, wc / 2), rect(-W / 2, 0.0, W / 2, hs)])
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    inner = plug_cs.offset(-0.5, MIT, 4.0)
    mull = cs_union([rect(sg * (wc / 2 + 0.7) - 0.7, -1.0, sg * (wc / 2 + 0.7) + 0.7, hs + 0.1) for sg in (-1, 1)])
    bars = [mull, rect(-W, hs * 0.5 - RIB / 2, W, hs * 0.5 + RIB / 2), rect(-RIB / 2, -1.0, RIB / 2, h + 1),
            rect(-W, hs - 0.35, W, hs + 0.35)]
    spring = h - wc / 2
    for t_ in (0.6, math.pi / 2, math.pi - 0.6):
        bars.append(stroke([(0.0, spring), (wc * math.cos(t_), spring + wc * math.sin(t_))], RIB))
    sash = _glazed([ext(plug_cs, -pl, -0.6)], inner, pl, cs_union(bars), plug_cs)
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             MD.band(op.offset(A, MIT, 4.0), A, MD.CASING, clip=rect(-W - 10, 0.0, W + 10, h + 40) - op)]
    for sg in (-1, 1):
        x = sg * (wc / 2 + 0.7)
        parts.append(ext(rect(x - 0.65, 0.0, x + 0.65, hs), 0.0, 0.8) - ext(cs_union([rect(x - 0.35 + k * 0.35 - 0.08, 0.8, x - 0.35 + k * 0.35 + 0.08, hs - 0.8) for k in range(3)]), 0.6, 1.0))
    parts.append(chamfer_box(-0.8, h + A - 0.6, 0.8, h + A + 1.6, 0.0, 1.2, c=0.25))
    parts.append(chamfer_box(-W / 2 - A - 0.6, -1.0, W / 2 + A + 0.6, 0.01, 0.0, 1.2, c=0.3, bottom=1.2))
    return O._one_piece(sash, parts, op, plug_cs, pl, h + A + 1.8, -1.0)


def door_carrington(w=9.0, h=21.0, side=2.6, A=1.0, back=False):
    """The Carrington's entrance: a six-panel door between leaded sidelights under an elliptical
    fanlight of radiating leading, fluted pilasters on plinths each side, and over all an
    entablature with a pulvinated frieze and a dentilled cornice. The back door (``back``) has
    no sidelights and a plain transom."""
    sd = 0.0 if back else side + 0.8
    W = w + 2 * sd
    rise = 0.0 if back else 3.6
    hd = h - rise
    op = rect(-W / 2, 0.0, W / 2, hd) + (oval((0.0, hd), W / 2, rise, 48) ^ rect(-W, hd - 0.01, W, h + 1) if rise else rect(0, 0, 0, 0))
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    inner = plug_cs.offset(-0.5, MIT, 4.0)
    dh = hd - (0.6 if rise else 3.0)
    ja = w / 2 - 0.5
    body = [ext(plug_cs, -pl, -1.0), ext(rect(-ja, 0.5, ja, dh), -pl, -0.8)]
    for cx in (-ja / 2, ja / 2):
        for v0_, v1_ in ((1.2, dh * 0.32), (dh * 0.36, dh * 0.62), (dh * 0.66, dh - 0.7)):
            pan = rect(cx - ja / 2 + 0.6, v0_, cx + ja / 2 - 0.6, v1_)
            body.append(ext(pan - pan.offset(-0.4, MIT, 4.0), -0.81, -0.5))
    g = inner - rect(-ja - 0.3, -1.0, ja + 0.3, dh + 0.3)
    bars = []
    if not back:
        for sg in (-1, 1):
            x = sg * (w / 2 + sd / 2)
            for v in np.arange(2.0, dh, 2.4):
                bars.append(stroke([(x - sd / 2, v), (x, v + 1.2), (x + sd / 2, v)], RIB))
        c0 = (0.0, hd)
        for t_ in np.linspace(0.25, math.pi - 0.25, 7):
            bars.append(stroke([c0, (c0[0] + W * math.cos(t_), c0[1] + W * math.sin(t_))], RIB))
        bars.append(oval(c0, W * 0.22, rise * 0.4, 24) - oval(c0, W * 0.22 - RIB, rise * 0.4 - RIB, 24))
    else:
        bars.append(rect(-RIB / 2, dh, RIB / 2, h + 1))
    sash = _glazed(body, g, pl, cs_union(bars) if bars else None, plug_cs)
    sash.append(ext(rect(-w / 2, dh - 0.01, w / 2, dh + 0.5) ^ plug_cs, -pl, -0.5))
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             MD.band(op.offset(A, MIT, 4.0), A, MD.ARCHITRAVE, clip=rect(-W - 10, 0.0, W + 10, h + 40) - op)]
    X = W / 2 + A
    for sg in (-1, 1):
        x0, x1 = sorted((sg * X, sg * (X + 2.0)))
        parts.append(chamfer_box(x0, 0.0, x1, 2.0, 0.0, 1.3, c=0.25))
        parts.append(ext(rect(x0 + 0.2, 1.99, x1 - 0.2, h + 0.2), 0.0, 1.0) -
                     ext(cs_union([rect(x0 + 0.6 + k * 0.4 - 0.1, 3.0, x0 + 0.6 + k * 0.4 + 0.1, h - 1.0) for k in range(3)]), 0.8, 1.2))
    et = h + A
    parts.append(ext(rect(-X - 2.3, et - 0.01, X + 2.3, et + 1.2), 0.0, 1.0))
    parts.append(M.hull_points([(x, et + 1.19, 0.0) for x in (-X - 2.3, X + 2.3)] + [(x, et + 2.4, 0.0) for x in (-X - 2.3, X + 2.3)] +
                               [(x, et + 1.8, 1.4) for x in (-X - 2.3, X + 2.3)]))
    parts.append(chamfer_box(-X - 2.8, et + 2.39, X + 2.8, et + 3.2, 0.0, 1.8, c=0.3, bottom=1.0))
    dent = cs_union([rect(x - 0.3, et + 2.4, x + 0.3, et + 2.95) for x in np.arange(-X - 2.2, X + 2.3, 1.0)])
    parts.append(ext(dent, 1.79, 2.2))
    parts.append(ext(rect(-X - 2.3, -0.6, X + 2.3, 0.01), 0.0, 1.4))
    return O._one_piece(sash, parts, op, plug_cs, pl, et + 3.4, -0.6)


def addin_carrington(w=5.6, h=8.4, A=0.8):
    """A pedimented dormer for the hipped roof (an add-in): a six-light sash between pilasters
    under a triangular pediment with a raking cornice; a sill."""
    op = rect(-w / 2, 0.0, w / 2, h)
    bars = cs_union([rect(-RIB / 2, -1.0, RIB / 2, h + 1.0), rect(-10, h / 3 - RIB / 2, 10, h / 3 + RIB / 2), rect(-10, 2 * h / 3 - RIB / 2, 10, 2 * h / 3 + RIB / 2)])
    X = w / 2 + A + 0.9
    parts = [ext(rect(-X, 0.0, X, h + A) - op, 0.0, 0.8)]
    for sg in (-1, 1):
        x0, x1 = sorted((sg * (w / 2 + 0.1), sg * X))
        parts.append(ext(rect(x0 + 0.2, 0.4, x1 - 0.2, h + A - 0.4), 0.79, 1.1))
    ped = poly([(-X - 0.7, h + A - 0.01), (X + 0.7, h + A - 0.01), (0.0, h + A + 3.4)])
    parts.append(ext(ped, 0.0, 0.9))
    rake = ped - ped.offset(-0.7, MIT, 4.0)
    parts.append(ext(rake, 0.89, 1.3))
    parts.append(MD.run(-X - 0.4, X + 0.4, 0.0, MD.SILL, 0.9, up=False))
    parts = [p - ext(op, -1.0, 5.0) for p in parts]
    outline = (rect(-X - 0.7, 0.2, X + 0.7, h + A) + ped).offset(-0.3, RND) ^ rect(-50, 0.2, 50, 100)
    return dict(light=op, bars=bars, frame=parts, outline=outline, top=h + A + 3.6, bottom=-0.9)


# ------------------------------------------------------------------ the portico
def post_carringtonionic(h, collar=None, abacus=6.2, slot=(1.2, 1.0), r=2.5):
    """A colossal Ionic column: an Attic base on a square plinth, a plain shaft with entasis, an
    astragal, an egg-and-dart echinus, and on each face a pair of volutes joined across the sides
    by the cushion (pulvinus), under a thin abacus (the Carrington's portico)."""
    zc = h - 4.6
    prof = [(0.0, 1.59), (r + 0.8, 1.59), (r + 0.8, 2.0), (r + 0.45, 2.4), (r + 0.3, 2.7), (r + 0.55, 3.1), (r + 0.2, 3.5), (r, 3.9),
            (r * 1.05, (3.9 + zc) * 0.35), (r * 0.86, zc - 0.5), (r + 0.05, zc - 0.3), (r + 0.05, zc), (r * 0.88, zc + 0.2),
            (r * 0.95, zc + 0.6), (r + 0.4, zc + 1.4)]
    body = PW._revolve(prof, 48) + box([-(r + 1.1), -(r + 1.1), 0.0], [r + 1.1, r + 1.1, 1.6])
    body = body + PW._top(h, abacus / 2, zc + 1.4, r + 0.4, slot, seg=48)
    zv = zc + 1.0
    rv = 1.15
    for sy in (-1, 1):
        for sx in (-1, 1):
            c = (sx * (abacus / 2 - 0.5), zv)
            disc = circle((0.0, 0.0), rv, 28) - circle((0.0, 0.0), rv * 0.42, 16) + circle((0.0, 0.0), 0.3, 10)
            spiral = stroke([(rv * (0.95 - 0.55 * t_) * math.cos(6.0 * t_), rv * (0.95 - 0.55 * t_) * math.sin(6.0 * t_)) for t_ in np.linspace(0.0, 1.0, 20)], 0.22)
            plate = M.extrude(disc, 0.7) + M.extrude(spiral ^ circle((0, 0), rv, 28), 0.95)
            A = np.array([[1.0, 0.0, 0.0, c[0]], [0.0, 0.0, -sy, sy * (abacus / 2 - 0.6)], [0.0, 1.0, 0.0, c[1]]])
            if sy < 0:
                A = np.array([[1.0, 0.0, 0.0, c[0]], [0.0, 0.0, -1.0, -(abacus / 2 - 0.6)], [0.0, 1.0, 0.0, c[1]]])
            else:
                A = np.array([[1.0, 0.0, 0.0, c[0]], [0.0, 0.0, 1.0, abacus / 2 - 0.6], [0.0, 1.0, 0.0, c[1]]])
            body = body + plate.transform(A)
        cush = M.cylinder(abacus - 1.4, rv * 0.95, rv * 0.95, 24).rotate([90, 0, 0]).translate([sy * (abacus / 2 - 0.5), (abacus - 1.4) / 2, zv])
        body = body + cush
    return max(body.decompose(), key=lambda c: c.volume())


def frieze_festoonarchitrave(u0, u1, v_bot, v_top):
    """The portico's architrave between the columns: a solid beam, its soffit stepped up 0.6 mm
    a little in from each column so the two fasciae read from below (the Carrington)."""
    out = rect(u0, v_bot, u1, v_top + 0.05)
    if u1 - u0 > 6.0 and v_top - v_bot > 1.6:
        out = out - rect(u0 + 1.2, v_bot - 1.0, u1 - 1.2, v_bot + 0.6)
    return out


def edge_dentilegg(L, z0, zc):
    """Portico fascia (the Carrington): a row of dentils under an egg-and-dart band below the
    crown."""
    out = [rect(0.3, zc - 0.6, L - 0.3, zc), rect(0.3, zc - 2.0, L - 0.3, zc - 1.5)]
    pu = 1.2
    n = max(1, int((L - 1.0) / pu))
    u0 = (L - n * pu) / 2
    out += [rect(u0 + pu * k + 0.15, zc - 1.51, u0 + pu * k + 0.85, zc - 0.59) for k in range(n)]
    out += [oval((u0 + pu * (k + 0.5), zc - 2.4), 0.4, 0.55, 12) for k in range(n)]
    return cs_union(out) ^ rect(0.3, -1e3, L - 0.3, 1e3), 0.6


def skirt_carrington(reg, d=1.2):
    """The portico's base between the column plinths: brick with an arched iron-grilled vent in
    the middle of each bay, under a moulded cap."""
    u0, v0, u1, v1 = reg.bounds()
    cells = []
    for k, v in enumerate(np.arange(v0, v1 - 0.8, 0.8)):
        off = 0.0 if k % 2 == 0 else 1.0
        for u in np.arange(u0 - 2.0 + off, u1 + 1.0, 2.0):
            cells.append(rect(u + 0.1, v + 0.1, u + 1.9, v + 0.7))
    out = [M.extrude(reg, d * 0.4)]
    if cells:
        out.append(ext(cs_union(cells) ^ reg, d * 0.4 - 0.01, d * 0.7))
    out.append(ext(rect(u0 - 1, v1 - 0.8, u1 + 1, v1 + 1) ^ reg, d * 0.4 - 0.01, d * 0.9))
    body = union(out)
    if v1 - v0 > 4.0 and u1 - u0 > 5.0:
        um = (u0 + u1) / 2
        vent = O.opening_cs(2.6, min(3.0, v1 - v0 - 2.0), 1.3).translate((um, v0 + 0.6))
        body = body - ext(vent, d * 0.15, 5.0)
        body = body + ext(cs_union([rect(x - 0.2, v0, x + 0.2, v1) for x in (um - 0.65, um, um + 0.65)]) ^ vent, d * 0.15 - 0.01, d * 0.4)
    return body ^ M.extrude(reg, d + 0.5)


def balcony_carrington(region, z, t=1.2, consoles=()):
    """The curved balcony's floor inside the portico: a slab over ``region`` (its back on the
    storey cornice's crown) and under its free edge a scrolled console at each of ``consoles`` =
    [(x, y, angle)], the console's deep end toward the house. World coords; printed upside down."""
    body = M.extrude(region, t).translate([0, 0, z - t])
    for x, y, a in consoles:
        prof = poly([(0.0, 0.0), (3.0, 0.0), (3.0, -0.6), (2.2, -1.2), (1.2, -2.6), (0.4, -3.4), (0.0, -3.4)])
        con = M.extrude(prof, 1.4).translate([0, 0, -0.7]).transform(np.array([[1.0, 0, 0, 0], [0, 0, 1.0, 0], [0, 1.0, 0, 0]]))
        con = con.rotate([0, 0, math.degrees(a)]).translate([x, y, z - t + 0.01])
        body = body + con
    return body


def chimney_carrington(w=12.0, d=7.0, h=30.0):
    """A tall Colonial end stack: running-bond brick with a sunk panel on each broad face, a
    four-course corbelled cap under a stone coping, two round clay pots. Prints upright."""
    h = round(h / 0.2) * 0.2
    sh = h - 5.0
    body = box([-w / 2, -d / 2, 0.0], [w / 2, d / 2, sh])
    for sy in (-1, 1):
        body = body - box([-w / 2 + 1.6, sy * d / 2 - 0.4, 3.0], [w / 2 - 1.6, sy * d / 2 + 0.4, sh - 3.6])
    courses = []
    for k, z in enumerate(np.arange(0.0, sh - 0.4, 0.8)):
        for sy in (-1, 1):
            for x in np.arange(-w / 2 - (0.0 if k % 2 == 0 else 1.0), w / 2, 2.0):
                courses.append(box([max(x + 0.1, -w / 2), sy * d / 2 - 0.01 if sy > 0 else -d / 2 - 0.2, z + 0.1],
                                   [min(x + 1.9, w / 2), d / 2 + 0.2 if sy > 0 else -d / 2 + 0.01, z + 0.7]))
    body = body + union(courses) - union([box([-w / 2 + 1.6, sy * d / 2 - 0.4 if sy > 0 else -d / 2 - 1.0, 3.0],
                                              [w / 2 - 1.6, d / 2 + 1.0 if sy > 0 else -d / 2 + 0.4, sh - 3.6]) for sy in (-1, 1)])
    z = sh
    for k in range(4):
        g = 0.25 * (k + 1)
        body = body + box([-w / 2 - g, -d / 2 - g, z - 0.01], [w / 2 + g, d / 2 + g, z + 0.6])
        z += 0.6
    body = body + box([-w / 2 - 1.3, -d / 2 - 1.3, z - 0.01], [w / 2 + 1.3, d / 2 + 1.3, z + 0.8])
    for sx in (-1, 1):
        body = body + M.cylinder(2.4, 1.2, 1.0, 20).translate([sx * w / 4, 0, z + 0.79]) + M.cylinder(0.4, 1.3, 1.3, 20).translate([sx * w / 4, 0, z + 3.18])
        body = body - M.cylinder(4.0, 0.6, 0.6, 12).translate([sx * w / 4, 0, z + 1.2])
    return body


CO.FRIEZE_EXTRA.update(bowknotswags=frieze_bowknotswags, plumes=frieze_plumes)
CO.COURSE_EXTRA.update(ribbonreed=course_ribbonreed)
TW.BRACKET_EXTRA.update(volutemod=bracket_volutemod)
TW.FOUNDATION_EXTRA.update(carrington=foundation_carrington)
SH.CORNER_EXTRA.update(carrington=corner_carrington)
PW.POSTS.update(carringtonionic=post_carringtonionic)
PW.FRIEZES.update(festoonarchitrave=frieze_festoonarchitrave)
PW.SKIRTS.update(carrington=skirt_carrington)
FT.EDGE_EXTRA.update(dentilegg=edge_dentilegg)


# ================================================================== the Ravenhurst (house 100)
# Castellated Gothic Revival, 1868: a Hudson River castle-villa in the manner of A. J. Davis. A
# ground storey of grey squared rubble brought to course with little snecks, an upper storey of
# knapped flint chequered with limestone squares (East Anglian flushwork), stepped angle
# buttresses at every corner. Every roof is flat behind battlements pierced with cross loops; a
# square tower on the front corner rises two stages over the roof to its own battlements, a
# pepperpot turret with a slate spire at each of its corners. Tudor-arched windows of two cusped
# lights under square label moulds below, single traceried lights above, a great three-light
# window of panel tracery in the tower; the oak door is set in a four-centred arch. A vaulted
# porch of clustered piers and Tudor arches carries a battlemented roof; tall clustered chimneys
# of twisted brick rise from the roof. Cornices of dogtooth, blind quatrefoil panels, grotesque
# corbel heads.

RV_LEVELS = dict(hi=40.0)


def _tudor(w, vs, rise, seg=10):
    """A four-centred (Tudor) arch outline: jambs from 0 to the springing vs, then two short arcs
    of small radius turning into two long flat arcs meeting in a low point ``rise`` over vs."""
    r1 = w * 0.2
    pts = [(w / 2, 0.0), (w / 2, vs)]
    for a in np.linspace(0.0, math.radians(55.0), seg):
        pts.append((w / 2 - r1 + r1 * math.cos(a), vs + r1 * math.sin(a)))
    x1, y1 = pts[-1]
    pts.append((x1 * 0.45, y1 + (rise - (y1 - vs)) * 0.8))
    pts.append((0.0, vs + rise))
    right = pts
    left = [(-x, y) for x, y in reversed(right[1:-1])]
    return poly(right + left + [(-w / 2, 0.0)])


def _label(x0, x1, v_top, drop, d=1.0):
    """A square label (hood) mould over an opening: a moulded bar along v_top returned down
    ``drop`` at each end onto a square stop. A list of solids in the (u, v, w) frame."""
    out = [chamfer_box(x0 - 0.9, v_top - 0.01, x1 + 0.9, v_top + 1.0, 0.0, d, c=0.3, bottom=d)]
    for x in (x0 - 0.9, x1 + 0.1):
        out.append(chamfer_box(x, v_top - drop, x + 0.8, v_top + 0.01, 0.0, d, c=0.25, bottom=d))
        out.append(chamfer_box(x - 0.2, v_top - drop - 1.0, x + 1.0, v_top - drop + 0.01, 0.0, d + 0.2, c=0.25, bottom=d + 0.2))
    return out


# ------------------------------------------------------------------ wall skins, corners, foundation
def rubble_coursed(region, datum=0.0, course=5.6, joint=0.35, d=0.4, seed=23):
    """Squared rubble brought to course every 5.6 mm: within each course stones of the full height,
    or two stacked, or a big one with a little square sneck beside it; every stone's face
    chamfered (the Ravenhurst's ground storey)."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    rng = np.random.default_rng(seed)
    out = []
    v = datum + math.floor((v0 - datum) / course) * course - course
    while v < v1:
        if v + course > v0 - 1:
            u = u0 - rng.uniform(0.0, 4.0)
            while u < u1 + 1:
                kind = rng.integers(0, 3)
                Ls = rng.uniform(3.6, 7.6)
                if kind == 0:
                    out.append(chamfer_box(u + joint / 2, v + joint / 2, u + Ls - joint / 2, v + course - joint / 2, 0.0, d, c=0.2))
                elif kind == 1:
                    hs = rng.uniform(2.0, course - 2.0)
                    out.append(chamfer_box(u + joint / 2, v + joint / 2, u + Ls - joint / 2, v + hs - joint / 2, 0.0, d, c=0.2))
                    L2 = rng.uniform(2.6, Ls)
                    out.append(chamfer_box(u + joint / 2, v + hs + joint / 2, u + L2 - joint / 2, v + course - joint / 2, 0.0, d, c=0.2))
                    if L2 < Ls - 1.4:
                        out.append(chamfer_box(u + L2 + joint / 2, v + hs + joint / 2, u + Ls - joint / 2, v + course - joint / 2, 0.0, d, c=0.2))
                else:
                    sn = 1.6
                    out.append(chamfer_box(u + joint / 2, v + joint / 2, u + Ls - joint / 2, v + course - sn - joint / 2, 0.0, d, c=0.2))
                    out.append(chamfer_box(u + joint / 2, v + course - sn + joint / 2, u + sn * 1.4 - joint / 2, v + course - joint / 2, 0.0, d, c=0.2))
                    out.append(chamfer_box(u + sn * 1.4 + joint / 2, v + course - sn + joint / 2, u + Ls - joint / 2, v + course - joint / 2, 0.0, d, c=0.2))
                u += Ls
        v += course
    return union(out) ^ M.extrude(region, d + 0.2)


def flint_chequer(region, datum=0.0, s=3.2, d=0.3, seed=29):
    """Flushwork: a chequer of smooth limestone squares and squares of knapped flint, each flint
    square a cluster of little rounded nodules (the Ravenhurst's upper storey)."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    rng = np.random.default_rng(seed)
    stones, nods = [], []
    j0 = math.floor((v0 - datum) / s) - 1
    for j in range(j0, int((v1 - datum) / s) + 2):
        v = datum + j * s
        k0 = math.floor(u0 / s) - 1
        for k in range(k0, int(u1 / s) + 2):
            u = k * s
            if (j + k) % 2 == 0:
                stones.append(rect(u + 0.12, v + 0.12, u + s - 0.12, v + s - 0.12))
            else:
                for a in range(3):
                    for b in range(3):
                        cx = u + s * (a + 0.5) / 3 + rng.uniform(-0.15, 0.15)
                        cy = v + s * (b + 0.5) / 3 + rng.uniform(-0.15, 0.15)
                        nods.append(circle((cx, cy), s / 6 - 0.05, 8))
    out = []
    if stones:
        out.append(M.extrude(cs_union(stones) ^ region, d))
    if nods:
        out.append(M.extrude(cs_union(nods) ^ region, d * 0.6))
    return union(out) if out else M()


def corner_ravenhurst(L, at_start, qa, qb, w=2.4, t=0.65):
    """The Ravenhurst's corners: an angle buttress on each face, 2.4 mm wide, standing 2.2 out at
    its foot and stepping back to 1.2 at a 45 degree set-off halfway up, its head weathered back
    to the wall at 45 degrees under the cornice."""
    if qb - qa < 8.0:
        return M()
    bw = 2.6
    u0, u1 = (0.3, 0.3 + bw) if at_start else (L - 0.3 - bw, L - 0.3)
    zm = qa + (qb - qa) * 0.5
    lo = M.hull_points([(u, qa, w_) for u in (u0, u1) for w_ in (-0.02, 2.2)] + [(u, zm, w_) for u in (u0, u1) for w_ in (-0.02, 2.2)] +
                       [(u, zm + 1.0, w_) for u in (u0, u1) for w_ in (-0.02, 1.2)])
    hi = M.hull_points([(u, zm + 0.99, w_) for u in (u0, u1) for w_ in (-0.02, 1.2)] + [(u, qb - 1.2, w_) for u in (u0, u1) for w_ in (-0.02, 1.2)] +
                       [(u, qb, -0.02) for u in (u0, u1)])
    return lo + hi


def foundation_quatrefoilplinth(reg, seed=0):
    """A plinth of plain ashlar carrying a band of blind quatrefoils in square panels under a
    chamfered bench table (the Ravenhurst)."""
    b = reg.bounds()
    hgt = b[3] - b[1]
    out = [M.extrude(reg, 0.4)]
    top = rect(b[0] - 1, b[3] - 1.2, b[2] + 1, b[3]) ^ reg
    if not top.is_empty():
        tb = top.bounds()
        out.append(M.hull_points([(x, tb[1], 0.0) for x in (tb[0], tb[2])] + [(x, tb[1] + 0.4, 1.0) for x in (tb[0], tb[2])] +
                                 [(x, tb[3], 1.0) for x in (tb[0], tb[2])] + [(x, tb[3], 0.39) for x in (tb[0], tb[2])]))
    if hgt > 5.0:
        s = min(3.6, hgt - 2.6)
        vm = b[1] + 0.8 + s / 2
        cells, qf = [], []
        for u in np.arange(b[0] + 1.0, b[2] - s, s + 0.6):
            sq = rect(u, vm - s / 2, u + s, vm + s / 2)
            cells.append(sq - sq.offset(-0.4, MIT, 4.0))
            q = _quatrefoil((u + s / 2, vm), s * 0.16)
            qf.append(q - q.offset(-0.35, MIT, 4.0))
        if cells:
            out.append(M.extrude(cs_union(cells + qf) ^ reg, 0.75))
    return union(out)


# ------------------------------------------------------------------ cornice ornaments
def course_dogtooth(L, h, b, pitch, margin, p):
    """Dogtooth: a row of four-leaved pyramids, each a square set on its point with its leaves
    rising to a sharp middle (Early English; the Ravenhurst)."""
    pu = 1.6
    n = max(1, int((L - 0.6) / pu))
    u0 = (L - n * pu) / 2
    out = [_st(rect(0.2, 0.15, L - 0.2, h - 0.15), b, 0.12)]
    s = min(0.72, h * 0.42)
    for k in range(n):
        u = u0 + pu * (k + 0.5)
        out.append(M.hull_points([(u + s, h / 2, 0.0), (u - s, h / 2, 0.0), (u, h / 2 + s, 0.0), (u, h / 2 - s, 0.0), (u, h / 2, 0.55)])
                   .translate([0, 0, b + 0.11]))
    return out


def frieze_panelquatrefoils(L, h, b, pitch, margin, pair, half):
    """Blind panelling: a row of square panels, each framing a quatrefoil with a flower at its
    heart (Perpendicular; the Ravenhurst's storey joint)."""
    v0, v1 = 0.5, h - 0.5
    hh = v1 - v0
    vm = (v0 + v1) / 2
    s = hh * 0.92
    pu = s + 0.6
    n = max(1, int((L - 1.0) / pu))
    u0 = (L - n * pu) / 2
    frames, qf, fl = [], [], []
    for k in range(n):
        uc = u0 + pu * (k + 0.5)
        sq = rect(uc - s / 2, vm - s / 2, uc + s / 2, vm + s / 2)
        frames.append(sq - sq.offset(-0.4, MIT, 4.0))
        q = _quatrefoil((uc, vm), s * 0.17)
        qf.append(q - q.offset(-0.38, MIT, 4.0))
        fl.append(circle((uc, vm), 0.45, 12))
    clip = rect(0.2, v0, L - 0.2, v1)
    return [_st(cs_union(frames) ^ clip, b, 0.35), _st(cs_union(qf) ^ clip, b, 0.45), _st(cs_union(fl) ^ clip, b, 0.6)], []


def frieze_grotesques(L, h, b, pitch, margin, pair, half):
    """A corbel table of grotesque heads: little cusped arches springing from carved heads (a
    brow, two hollow eyes, a grinning mouth), a fillet over all (the Ravenhurst's eave)."""
    v0, v1 = 0.5, h - 0.5
    hh = v1 - v0
    pu = max(3.4, hh * 0.8)
    n = max(1, int((L - 1.0) / pu))
    u0 = (L - n * pu) / 2
    top = rect(0.2, v1 - 0.6, L - 0.2, v1)
    arcs, heads, eyes = [], [], []
    for k in range(n):
        uc = u0 + pu * (k + 0.5)
        o = arch_cs(uc - pu / 2 + 0.75, uc + pu / 2 - 0.75, v0 + hh * 0.42, v1 - 1.4, rise=(pu - 1.5) / 2, seg=16)
        oo = arch_cs(uc - pu / 2 + 0.3, uc + pu / 2 - 0.3, v0 + hh * 0.42, v1 - 0.9, rise=(pu - 0.6) / 2, seg=16)
        arcs.append((oo - o) ^ rect(-1e3, v0 + hh * 0.42, 1e3, 1e3))
    for k in range(n + 1):
        u = u0 + pu * k
        c = (u, v0 + hh * 0.3)
        heads.append(oval(c, 0.75, hh * 0.28, 16))
        eyes.append(circle((u - 0.28, c[1] + hh * 0.06), 0.16, 8) + circle((u + 0.28, c[1] + hh * 0.06), 0.16, 8) +
                    rect(u - 0.35, c[1] - hh * 0.14, u + 0.35, c[1] - hh * 0.1))
    clip = rect(0.2, v0, L - 0.2, v1)
    hd = cs_union(heads) ^ clip
    return [_st(top, b, 0.35), _st(cs_union(arcs) ^ clip, b, 0.42), _st(hd - cs_union(eyes), b, 0.65)], []


def bracket_corbelhead(h, d, t):
    """A Gothic corbel: a moulded block over a rounded head, stepped back under it (side
    profile, top at v = 0; the Ravenhurst)."""
    pts = [(0.0, 0.0), (d, 0.0), (d, -h * 0.22), (d - 0.3, -h * 0.3)]
    r = min(h * 0.32, d * 0.4)
    cx, cy = d - 0.3 - r, -h * 0.3 - r
    for a in np.linspace(0.0, -math.pi * 0.75, 9):
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    pts += [(d * 0.25, -h), (0.0, -h)]
    return poly(pts)


def fence_ravenhurst_battlements(L, h):
    """Battlements (drawn at full size, printed flat): merlons with a cross loop in each and a
    moulded coping, embrasures between them, on a solid parapet."""
    mw, ew = 3.6, 2.6
    pu = mw + ew
    n = max(1, int((L - 0.4 + ew) / pu))
    u0 = (L - (n * pu - ew)) / 2
    base = h * 0.52
    out = [rect(0.2, 0.0, L - 0.2, base)]
    loops = []
    for k in range(n):
        x = u0 + pu * k
        out.append(rect(x, base - 0.1, x + mw, h - 0.5))
        out.append(rect(x - 0.3, h - 0.6, x + mw + 0.3, h))
        cx = x + mw / 2
        loops.append(rect(cx - 0.32, base - 1.6, cx + 0.32, h - 1.4) + rect(cx - 1.0, h * 0.72 - 0.3, cx + 1.0, h * 0.72 + 0.3))
    if u0 > 0.8:
        out.append(rect(0.2, base - 0.1, u0 - 0.6, h - 0.5))
    if L - (u0 + n * pu - ew) > 0.8:
        out.append(rect(u0 + n * pu - ew + 0.6, base - 0.1, L - 0.2, h - 0.5))
    out.append(rect(0.2, base - 0.6, L - 0.2, base))
    return (cs_union(out) - cs_union(loops)) ^ rect(0.2, 0.0, L - 0.2, h)


def bartizan_ravenhurst(r=4.2, h=10.0, spire=9.0):
    """A pepperpot turret for a corner of the tower's top: an octagonal turret on a two-step
    moulded base, a cross loop in each face, a moulded string, and a slate spire with a finial
    ball. Local: its axis at the origin, its flat base at z = 0 (it stands on the tower's deck
    and prints upright on that base); one filament change at the spire's foot. Returns (solid,
    the spire's foot height)."""
    oc = circle((0.0, 0.0), r, 8).rotate(22.5)
    body = M.extrude(oc.offset(0.5, MIT, 4.0), 0.6) + M.extrude(oc.offset(0.25, MIT, 4.0), 0.6).translate([0, 0, 0.59])
    body = body + M.extrude(oc, h).translate([0, 0, 1.18])
    zt = round((1.18 + h) / 0.2) * 0.2
    body = body + M.extrude(oc.offset(0.4, MIT, 4.0), 0.8).translate([0, 0, zt - 0.8])
    ap = r * math.cos(math.pi / 8)
    for k in range(8):
        a = math.pi / 8 + k * math.pi / 4 + math.pi / 8
        cx, cy = ap * math.cos(a), ap * math.sin(a)
        loop = (box([-0.3, -0.6, -1.8], [0.3, 0.6, 1.8]) + box([-1.0, -0.6, -0.3], [1.0, 0.6, 0.3])).rotate([0, 0, math.degrees(a) + 90])
        body = body - loop.translate([cx, cy, 1.2 + h * 0.5])
    sp = M.extrude(oc.offset(0.4, MIT, 4.0), spire, 0, 0.0, (0.08, 0.08)).translate([0, 0, zt - 0.01])
    body = body + sp + _ball(0.55, zt + spire + 0.3, neck=0.25)
    return body, zt


# ------------------------------------------------------------------ windows and doors
def window_ravenhurst_ground(wl=3.8, h=15.0, mull=1.0, A=0.7):
    """The ground storey's window: two lights, each under a cusped Tudor arch, parted by a stone
    mullion, a transom across, in a chamfered frame under a square label on stops."""
    W = 2 * wl + mull
    op = rect(-W / 2, 0.0, W / 2, h)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    inner = plug_cs.offset(-0.4, MIT, 4.0)
    xs = (-(wl + mull) / 2, (wl + mull) / 2)
    vs = h - wl * 0.42
    lights = cs_union([_tudor(wl, vs, wl * 0.36).translate((x, 0.0)) for x in xs])
    bars = (inner - lights) + rect(-W, h * 0.48 - RIB / 2, W, h * 0.48 + RIB / 2)
    sash = _glazed([ext(plug_cs, -pl, -0.6)], inner, pl, bars, plug_cs)
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS),
             ext(op.offset(A, MIT, 4.0) - op, 0.0, 0.7)]
    spand = cs_union([rect(x - wl / 2, vs, x + wl / 2, h) for x in xs]) - lights
    parts.append(ext(spand ^ op, -0.6, 0.35))
    parts += _label(-W / 2 - A, W / 2 + A, h + A, 3.0)
    parts.append(chamfer_box(-W / 2 - A - 0.4, -1.2, W / 2 + A + 0.4, 0.01, 0.0, 1.1, c=0.3, bottom=1.1))
    return O._one_piece(sash, parts, op, plug_cs, pl, h + A + 1.2, -1.2)


def window_ravenhurst_upper(w=5.6, h=15.0, A=0.7):
    """The upper storey's window: one Tudor-arched light filled with tracery (two cusped sub-
    lights and a quatrefoil), in a chamfered frame under a label mould that follows the arch."""
    rise = w * 0.32
    vs = h - rise
    op = _tudor(w, vs, rise)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    inner = plug_cs.offset(-0.4, MIT, 4.0)
    subs = cs_union([_tudor(w / 2 - 0.7, vs - 1.4, (w / 2 - 0.7) * 0.4).translate((sg * (w / 4), 0.0)) for sg in (-1, 1)])
    quat = _quatrefoil((0.0, vs + rise * 0.15), 0.55)
    glass_ = (subs + quat) ^ inner
    bars = (inner - glass_) + rect(-w, h * 0.45 - RIB / 2, w, h * 0.45 + RIB / 2)
    sash = _glazed([ext(plug_cs, -pl, -0.6)], inner, pl, bars, plug_cs)
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS), ext(op.offset(A, MIT, 4.0) - op, 0.0, 0.7)]
    hood = (op.offset(A + 1.0, MIT, 4.0) - op.offset(A - 0.05, MIT, 4.0)) ^ rect(-50, vs - 0.3, 50, 100)
    parts.append(ext(hood, 0.0, 1.0))
    for sg in (-1, 1):
        x = sg * (w / 2 + A + 0.5)
        parts.append(chamfer_box(x - 0.6, vs - 1.6, x + 0.6, vs - 0.29, 0.0, 1.1, c=0.25, bottom=1.1))
    parts.append(chamfer_box(-w / 2 - A - 0.4, -1.2, w / 2 + A + 0.4, 0.01, 0.0, 1.1, c=0.3, bottom=1.1))
    return O._one_piece(sash, parts, op, plug_cs, pl, h + A + 1.2, -1.2)


def window_ravenhurst_great(n=3, wl=3.2, mull=0.9, h=22.0, A=0.8):
    """The tower's great window: a tall pointed arch of three lights with a transom, the head
    filled with panel tracery (mullions running up into it, a row of cusped panels and a
    quatrefoil at the point), a hood mould on carved stops."""
    W = n * wl + (n - 1) * mull
    ap = _apex(W, W * 0.75)
    vs = h - ap
    op = _lancet(-W / 2, W / 2, vs, r=W * 0.75, seg=16)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    inner = plug_cs.offset(-0.4, MIT, 4.0)
    xs = [-W / 2 + wl / 2 + k * (wl + mull) for k in range(n)]
    lights = cs_union([_tudor(wl, vs - 0.6, wl * 0.35).translate((x, 0.0)) for x in xs])
    panels = cs_union([_lancet(x - wl / 2 + 0.2, x + wl / 2 - 0.2, vs + ap * 0.15, v0=vs + 0.5, r=wl * 0.5) for x in xs])
    quat = _quatrefoil((0.0, vs + ap * 0.68), min(0.8, ap * 0.12))
    glass_ = (lights + panels + quat) ^ inner
    bars = (inner - glass_) + rect(-W, vs * 0.5 - RIB / 2, W, vs * 0.5 + RIB / 2)
    sash = _glazed([ext(plug_cs, -pl, -0.6)], inner, pl, bars, plug_cs)
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS), ext(op.offset(A, MIT, 4.0) - op, 0.0, 0.8)]
    hood, top = _hood_lancet(op, A, vs, W, crockets=2)
    parts += hood
    parts.append(chamfer_box(-W / 2 - A - 0.5, -1.4, W / 2 + A + 0.5, 0.01, 0.0, 1.2, c=0.3, bottom=1.2))
    return O._one_piece(sash, parts, op, plug_cs, pl, top + 0.2, -1.4)


def door_ravenhurst(w=10.0, h=21.0, A=1.0, back=False):
    """The Ravenhurst's portal: a pair of boarded oak leaves on long strap hinges with a wicket
    grille, in a four-centred arch of two chamfered orders, shields carved in the spandrels under
    a square label on stops. The back door (``back``) has one order and no shields."""
    rise = w * 0.3
    vs = h - rise
    op = _tudor(w, vs, rise, seg=12)
    plug_cs = op.offset(-O.CLR, MIT, 4.0)
    pl = O.PLUG
    ja = w / 2 - O.CLR - 0.5
    dh = vs + rise * 0.4
    body = [ext(plug_cs, -pl, -1.0), ext(op.offset(-O.CLR - 0.5, MIT, 4.0), -pl, -0.8)]
    grooves = cs_union([rect(x - 0.15, 0.6, x + 0.15, h) for x in np.arange(-ja + 1.0, ja, 1.3)]) ^ op.offset(-O.CLR - 0.6, MIT, 4.0)
    body = [b_ - ext(grooves, -0.81, 0.0) if k == 1 else b_ for k, b_ in enumerate(body)]
    for v in (dh * 0.22, dh * 0.62):
        for sg in (-1, 1):
            x0, x1 = sorted((sg * 0.5, sg * (ja - 0.1)))
            body.append(ext(rect(x0, v - 0.3, x1, v + 0.3), -0.81, -0.45))
            body.append(ext(circle((sg * (ja - 0.4), v), 0.45, 10), -0.81, -0.4))
    grille = rect(-1.4, dh * 0.72, 1.4, dh * 0.72 + 2.4)
    gb = cs_union([rect(x - 0.2, dh * 0.72, x + 0.2, dh * 0.72 + 2.4) for x in (-0.7, 0.0, 0.7)])
    body.append(ext(grille - grille.offset(-0.35, MIT, 4.0) + gb, -0.81, -0.4))
    body.append(ext(rect(-0.25, 0.5, 0.25, dh), -0.81, -0.5))
    sash = body + [ext(plug_cs - plug_cs.offset(-0.5, MIT, 4.0), -pl, 0.0)]
    orders = 1 if back else 2
    parts = [ext(op - op.offset(-RIB, MIT, 4.0), 0.0, O.CAS)]
    for k in range(orders):
        e0, e1 = A * 0.2 + k * 1.3, A * 0.2 + (k + 1) * 1.3
        ring = (op.offset(e1, MIT, 4.0) - op.offset(e0, MIT, 4.0)) ^ rect(-50, -0.6, 50, 100)
        parts.append(ext(ring, 0.0, 0.9 + 0.4 * (orders - k - 1)))
    X = w / 2 + A * 0.2 + orders * 1.3
    top = h + A * 0.2 + orders * 1.3 + 0.8
    if not back:
        sp = rect(-X, vs, X, top) - op.offset(X - w / 2, MIT, 4.0)
        parts.append(ext(sp, 0.0, 0.5))
        for sg in (-1, 1):
            c = (sg * (X - 1.6), top - 1.9)
            sh = poly([(c[0] - 0.9, c[1] + 0.9), (c[0] + 0.9, c[1] + 0.9), (c[0] + 0.9, c[1] - 0.1), (c[0], c[1] - 1.0), (c[0] - 0.9, c[1] - 0.1)])
            parts.append(ext(sh, 0.49, 0.95))
    parts += _label(-X, X, top, 4.0, d=1.3)
    parts.append(ext(rect(-X - 1.0, -0.6, X + 1.0, 0.01), 0.0, 1.4))
    return O._one_piece(sash, parts, op, plug_cs, pl, top + 1.2, -0.6)


# ------------------------------------------------------------------ the porch
def post_clusterpier(h, collar=None, abacus=4.0, slot=(1.2, 1.0)):
    """A clustered Gothic pier: four round shafts round a core, each with a moulded base and a
    bell capital, under a shared octagonal abacus (the Ravenhurst's porch)."""
    zc = h - 3.2
    body = PW._plinth(3.6, ph=1.4) + M.cylinder(zc - 1.39, 1.05, 1.05, 24).translate([0, 0, 1.39])
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        x, y = 0.95 * math.cos(a), 0.95 * math.sin(a)
        prof = [(0.0, 1.39), (0.75, 1.39), (0.75, 1.6), (0.6, 1.9), (0.55, 2.1), (0.55, zc - 0.5), (0.7, zc - 0.3), (0.7, zc), (0.55, zc + 0.1)]
        body = body + PW._revolve(prof, 16).translate([x, y, 0.0])
    body = body + PW._top(h, abacus / 2, zc, 1.75, slot, seg=24, shape="round")
    return body


def frieze_tudorarch(u0, u1, v_bot, v_top):
    """The porch's arcade: a four-centred Tudor arch between every two piers, a pierced
    quatrefoil in each spandrel where there is room (the Ravenhurst)."""
    L = u1 - u0
    um = (u0 + u1) / 2
    hh = v_top - v_bot
    rise = min(hh - 1.4, (L - 0.6) * 0.3)
    vs = v_top - 1.0 - rise
    solid = rect(u0, v_bot, u1, v_top + 0.05)
    hole = _tudor(L - 0.6, vs - (v_bot - 1.0), rise).translate((um, v_bot - 1.0))
    out = solid - hole
    rq = min(0.9, (v_top - 1.0 - (vs + rise * 0.5)) * 0.35)
    if rq > 0.45 and L > 8.0:
        for sg in (-1, 1):
            out = out - _quatrefoil((um + sg * (L / 2 - 1.9), v_top - 1.0 - rise * 0.35), rq * 0.6)
    return out


def edge_crenelfascia(L, z0, zc):
    """Porch fascia (the Ravenhurst): a fillet under the crown with a row of little square
    crenellations hanging below it."""
    out = [rect(0.3, zc - 0.7, L - 0.3, zc)]
    pu = 1.6
    n = max(1, int((L - 1.0) / pu))
    u0 = (L - n * pu) / 2
    out += [rect(u0 + pu * k + 0.2, zc - 1.5, u0 + pu * k + 1.0, zc - 0.65) for k in range(n)]
    return cs_union(out) ^ rect(0.3, -1e3, L - 0.3, 1e3), 0.6


def skirt_ravenhurst(reg, d=1.2):
    """The porch's base between the piers: ashlar with a band of blind quatrefoils in squares."""
    u0, v0, u1, v1 = reg.bounds()
    out = [M.extrude(reg, d * 0.45)]
    s = min(3.4, v1 - v0 - 1.4)
    if s > 1.6:
        vm = (v0 + v1) / 2
        cells = []
        for u in np.arange(u0 + 0.6, u1 - s, s + 0.5):
            sq = rect(u, vm - s / 2, u + s, vm + s / 2)
            cells.append(sq - sq.offset(-0.35, MIT, 4.0))
            q = _quatrefoil((u + s / 2, vm), s * 0.16)
            cells.append(q - q.offset(-0.33, MIT, 4.0))
        if cells:
            out.append(ext(cs_union(cells) ^ reg, d * 0.45 - 0.01, d * 0.85))
    out.append(ext(rect(u0 - 1, v1 - 0.8, u1 + 1, v1 + 1) ^ reg, d * 0.45 - 0.01, d * 0.9))
    return union(out) ^ M.extrude(reg, d + 0.5)


def chimney_ravenhurst(w=11.0, d=6.0, h=30.0, n=3):
    """A clustered Tudor chimney: a plain base with a moulded set-off, ``n`` tall octagonal shafts
    of brick twisting one turn in their height, joined at their heads by a corbelled cap of three
    oversailing courses. Prints upright."""
    h = round(h / 0.2) * 0.2
    zb = round(h * 0.34 / 0.2) * 0.2
    body = box([-w / 2, -d / 2, 0.0], [w / 2, d / 2, zb])
    body = body + M.hull_points([(x, y, zb - 0.01) for x in (-w / 2, w / 2) for y in (-d / 2, d / 2)] +
                                [(x, y, zb + 0.6) for x in (-w / 2 + 0.6, w / 2 - 0.6) for y in (-d / 2 + 0.6, d / 2 - 0.6)])
    zc = h - 2.4
    rs = min(d / 2 - 0.4, w / (2 * n) - 0.2)
    oc = cs_union([circle((rs * 0.25 * math.cos(a), rs * 0.25 * math.sin(a)), rs * 0.8, 8) for a in (0.0, 2.094, 4.189)])
    oc = circle((0.0, 0.0), rs, 8).rotate(22.5) ^ oc.offset(0.15, MIT, 4.0) + circle((0.0, 0.0), rs * 0.82, 16)
    for k in range(n):
        x = -w / 2 + w * (k + 0.5) / n
        shaft = M.extrude(oc, zc - zb - 0.4, int((zc - zb) / 0.4), 360.0).translate([x, 0, zb + 0.4])
        body = body + shaft + M.cylinder(0.6, rs + 0.3, rs + 0.3, 16).translate([x, 0, zb + 0.4])
    z = zc - 0.01
    for k in range(3):
        g = 0.3 * (k + 1)
        body = body + box([-w / 2 - g + 0.4, -d / 2 - g + 0.4, z], [w / 2 + g - 0.4, d / 2 + g - 0.4, z + 0.8])
        z += 0.8
    for k in range(n):
        x = -w / 2 + w * (k + 0.5) / n
        body = body - M.cylinder(3.0, rs * 0.5, rs * 0.5, 12).translate([x, 0, h - 1.6])
    return body


CO.FRIEZE_EXTRA.update(panelquatrefoils=frieze_panelquatrefoils, grotesques=frieze_grotesques)
CO.COURSE_EXTRA.update(dogtoothleaf=course_dogtooth)
TW.BRACKET_EXTRA.update(corbelhead=bracket_corbelhead)
TW.FOUNDATION_EXTRA.update(quatrefoilplinth=foundation_quatrefoilplinth)
SH.CORNER_EXTRA.update(ravenhurst=corner_ravenhurst)
PW.POSTS.update(clusterpier=post_clusterpier)
PW.FRIEZES.update(tudorarch=frieze_tudorarch)
PW.SKIRTS.update(ravenhurst=skirt_ravenhurst)
FT.EDGE_EXTRA.update(crenelfascia=edge_crenelfascia)

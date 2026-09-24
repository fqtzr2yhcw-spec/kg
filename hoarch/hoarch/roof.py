"""Stacked-slice roofs: cornice rings, mansard slices, decks and small hipped roofs.

The technique (learned from the reference kit): instead of one big roof, the roof
is cut into horizontal *slices*, each a flat-bottomed ring that prints without
supports (cornices upside down so brackets and dentils face up). Stacked, the
slices build a complex moulded profile: cornice -> curb -> mansard (2 slices) ->
top cornice + deck.

Profiles are closed polygons in (d, z): d = outward offset from the plan path
(the wall's outer face), z absolute.
"""
import math

import numpy as np
from manifold3d import CrossSection as CS, JoinType, Manifold as M

from .core import (Facade, box, ccw, cs_union, frame, miters, offset, poly, rect, scallop_rows, slab,
                   sweep_ring, union)
from .ornament import chamfer_box, console, dentils, lozenge, side_profile


def _edges(path):
    P = np.asarray(ccw(path), float)
    return P, miters(P)


def edge_brackets(path, z_top, h, d0, d, t, pitch, margin=2.5, pair=0.0, corner=True, skip=None, style="scroll"):
    """Consoles under a soffit along every edge. d0 = frieze face offset; brackets
    project to d0 + d. ``pair`` > 0 places twin brackets that far apart."""
    P, Mi = _edges(path)
    out = []
    n = len(P)
    for i in range(n):
        a, b = P[i], P[(i + 1) % n]
        f = Facade(a, b, 0.0)
        L = f.L
        if L < 2 * margin + t:
            continue
        k = max(1, int(round((L - 2 * margin) / pitch)))
        us = [margin + (L - 2 * margin) * j / k for j in range(k + 1)] if k > 0 else [L / 2]
        for u in us:
            for du in ((-pair / 2, pair / 2) if pair > 0 else (0.0,)):
                uu = u + du
                if skip is not None and skip(f.world(uu, 0, d0)):
                    continue
                from .trimwork import bracket
                c = bracket(style, h, d, t, u=uu, v_top=0.0, w0=0.0)
                A = f.A.copy()
                A[:, 3] = f.world(0.0, 0.0, d0) + np.array([0, 0, z_top])
                out.append(c.transform(A))
    return union(out)


def edge_panels(path, z0, h, d0, d, pitch, margin=2.5, pair=0.0, t=0.8, clear=0.6, boss=True):
    """Raised frieze panels between the bracket positions of edge_brackets (same pitch,
    margin and pair), each with a diamond boss. z0 = panel bottom; d0 = frieze face."""
    P, Mi = _edges(path)
    out = []
    for i in range(len(P)):
        a, b = P[i], P[(i + 1) % len(P)]
        f = Facade(a, b, 0.0)
        L = f.L
        if L < 2 * margin + t:
            continue
        k = max(1, int(round((L - 2 * margin) / pitch)))
        us = [margin + (L - 2 * margin) * j / k for j in range(k + 1)]
        half = (pair / 2 if pair > 0 else 0.0) + t / 2 + clear
        loc = []
        for ua, ub in zip(us[:-1], us[1:]):
            u0, u1 = ua + half, ub - half
            if u1 - u0 < 2.0:
                continue
            loc.append(chamfer_box(u0, 0.0, u1, h, d0 - 0.05, d + 0.05, c=min(0.3, d)))
            if boss and u1 - u0 > 3.0 and h > 2.0:
                loc.append(lozenge((u0 + u1) / 2, h / 2, min(1.6, (u1 - u0) * 0.3), min(1.8, h - 1.0), d0 + d, 0.3))
        if loc:
            A = f.A.copy()
            A[:, 3] = f.world(0.0, 0.0, 0.0) + np.array([0, 0, z0])
            out.append(union(loc).transform(A))
    return union(out)


def edge_dentils(path, z0, h, d0, d, tooth=0.6, gap=0.5, margin=0.8, skip=None):
    P, Mi = _edges(path)
    out = []
    n = len(P)
    for i in range(n):
        a, b = P[i], P[(i + 1) % n]
        f = Facade(a, b, 0.0)
        if f.L < 2 * margin + tooth:
            continue
        den = dentils(margin, f.L - margin, 0.0, h, 0.0, d, tooth, gap)
        A = f.A.copy()
        A[:, 3] = f.world(0.0, 0.0, d0) + np.array([0, 0, z0])
        out.append(den.transform(A))
    return union(out)


def slope_texture(path, z0, z1, d_bot, d_top, pitch=1.55, wtab=1.8, d=0.33, shape="fish", seed=0):
    """Scallop slate rows on each planar face of a swept slope (d_bot at z0 -> d_top at z1)."""
    P, Mi = _edges(path)
    out = []
    n = len(P)
    for i in range(n):
        j = (i + 1) % n
        B0 = np.r_[P[i] + d_bot * Mi[i], z0]
        B1 = np.r_[P[j] + d_bot * Mi[j], z0]
        T0 = np.r_[P[i] + d_top * Mi[i], z1]
        T1 = np.r_[P[j] + d_top * Mi[j], z1]
        u = B1 - B0
        L = np.linalg.norm(u)
        if L < 1.0:
            continue
        u /= L
        vv = T0 - B0
        vv = vv - u * (vv @ u)
        vv /= np.linalg.norm(vv)
        w = np.cross(u, vv)
        region = poly([(0, 0), (L, 0), ((T1 - B0) @ u, (T1 - B0) @ vv), ((T0 - B0) @ u, (T0 - B0) @ vv)])
        tex = scallop_rows(region, pitch, wtab, d=d, shape=shape, datum=0.0)
        out.append(tex.transform(frame(B0, u, vv, w)))
    return union(out)


def ring_profile(path, profile):
    return sweep_ring(path, profile)


def filled(path, z0, z1, grow=0.0):
    cs = poly(ccw(path))
    return slab(cs if grow == 0 else offset(cs, grow), z0, z1)


# ------------------------------------------------------------------ hipped roofs by planes
class Plane:
    """Roof plane z = z0 + s * t.(p - q), t = unit up-slope direction in plan."""

    def __init__(self, q, t, z0, s):
        self.q = np.asarray(q, float)
        t = np.asarray(t, float)
        self.t = t / np.linalg.norm(t)
        self.z0, self.s = z0, s

    def z(self, x, y):
        return self.z0 + self.s * ((x - self.q[0]) * self.t[0] + (y - self.q[1]) * self.t[1])

    def normal(self):
        n = np.array([-self.s * self.t[0], -self.s * self.t[1], 1.0])
        return n / np.linalg.norm(n)


def below(solid, pl):
    n = pl.normal()
    p = np.array([pl.q[0], pl.q[1], pl.z0])
    return solid.trim_by_plane(list(-n), float(-n @ p))


def hip_solid(path, z_eave, slope, zlo, zhi=500.0, d_eave=0.0, exposed=None):
    """Solid under a hipped roof whose planes pass through the path edges
    (offset d_eave) at z_eave and rise inward at ``slope`` (dz/dplan).
    ``exposed`` limits the sloped planes to those edge indices (others stay vertical)."""
    P, Mi = _edges(path)
    n = len(P)
    s = slab(poly([tuple(p + d_eave * m) for p, m in zip(P, Mi)]), zlo, zhi)
    planes = []
    for i in (range(n) if exposed is None else exposed):
        a, b = P[i], P[(i + 1) % n]
        e = (b - a) / np.linalg.norm(b - a)
        nout = np.array([e[1], -e[0]])
        q = a + nout * d_eave
        pl = Plane(q, -nout, z_eave, slope)
        planes.append(pl)
        s = below(s, pl)
    return s, planes


def hip_texture(path, planes, z_eave, d_eave=0.0, pitch=1.55, wtab=1.8, d=0.33, shape="fish", zmax=None,
                seam_pitch=5.2, seam_w=0.5):
    """Texture on each hip face (region = the face's plan triangle/trapezoid):
    shape "fish"/"square"/"diamond" slate rows, or "seam" for a standing-seam metal roof."""
    P, Mi = _edges(path)
    fp = poly([tuple(p + d_eave * m) for p, m in zip(P, Mi)])
    out = []
    for i, pi in enumerate(planes):
        reg = fp
        for j, pj in enumerate(planes):
            if i == j:
                continue
            ax = pi.s * pi.t[0] - pj.s * pj.t[0]
            ay = pi.s * pi.t[1] - pj.s * pj.t[1]
            c = (pi.z0 - pi.s * (pi.q @ pi.t)) - (pj.z0 - pj.s * (pj.q @ pj.t))
            reg = reg ^ _halfplane(ax, ay, c)
        if reg.is_empty():
            continue
        # plan -> plane-local (u along eave, v up-slope)
        s = pi.s
        cth = 1 / math.sqrt(1 + s * s)
        t = pi.t
        e = np.array([t[1], -t[0]])
        q = pi.q
        A2 = np.array([[e[0], e[1], -(e @ q)], [t[0] / cth, t[1] / cth, -(t @ q) / cth]])
        loc = reg.transform(A2)
        if shape in ("tile", "crimp"):
            b = loc.bounds()
            n0 = int(np.floor(b[0] / seam_pitch))
            ribs = []
            for k in range(n0, int(np.ceil(b[2] / seam_pitch)) + 1):
                u = k * seam_pitch
                if shape == "tile":       # barrel tiles: a wide rib per row, broken at every course
                    for j in range(int(np.floor(b[1] / pitch)) - 1, int(np.ceil(b[3] / pitch)) + 1):
                        ribs.append(rect(u - seam_pitch * 0.32, j * pitch + 0.25, u + seam_pitch * 0.32, (j + 1) * pitch))
                else:                     # 5V crimp: a pair of narrow ribs per panel
                    ribs += [rect(u - 0.85, b[1] - 1, u - 0.35, b[3] + 1), rect(u + 0.35, b[1] - 1, u + 0.85, b[3] + 1)]
            tex = M.extrude(cs_union(ribs) ^ loc.offset(-0.3, JoinType.Miter, 4.0), d)
        elif shape == "seam":
            b = loc.bounds()
            n0 = int(np.floor(b[0] / seam_pitch))
            ribs = [rect(k * seam_pitch - seam_w / 2, b[1] - 1, k * seam_pitch + seam_w / 2, b[3] + 1)
                    for k in range(n0, int(np.ceil(b[2] / seam_pitch)) + 1)]
            tex = M.extrude(cs_union(ribs) ^ loc.offset(-0.3, JoinType.Miter, 4.0), d)
        else:
            tex = scallop_rows(loc, pitch, wtab, d=d, shape=shape, datum=loc.bounds()[1])
        vdir = np.array([t[0] * cth, t[1] * cth, s * cth])
        ndir = np.array([-t[0] * s * cth, -t[1] * s * cth, cth])
        # sunk a hair into the roof plane: texture that only touches it comes out as loose pieces
        out.append(tex.translate([0, 0, -0.03]).transform(frame([q[0], q[1], pi.z0], [e[0], e[1], 0.0], vdir, ndir)))
    tex = union(out).trim_by_plane([0, 0, 1.0], z_eave)      # the sunk texture stays clear of the eave ring
    if zmax is not None:
        tex = tex.trim_by_plane([0, 0, -1.0], -zmax)
    return tex


def _halfplane(a, b, c, big=3000.0):
    nv = np.array([a, b], float)
    ln = np.linalg.norm(nv)
    if ln < 1e-12:
        return rect(-big, -big, big, big) if c <= 0 else CS()
    nv /= ln
    c /= ln
    p0 = -c * nv
    tv = np.array([-nv[1], nv[0]])
    return poly([p0 + tv * big, p0 - tv * big, p0 - tv * big - nv * big, p0 + tv * big - nv * big])


def crest_fence(L, h=2.4, pitch=1.6, bar=0.5, t=0.6):
    """One straight run of cresting in its own frame: u = 0..L along, v up, centred across.

    A bottom rail, spikes of two heights, and a middle rail carried on little pointed
    arches that spring from the spikes at 45 degrees, so the fence prints upright with no
    bridge anchored on a spike (PrusaSlicer flags those as loose extrusions)."""
    k = max(1, int(L / pitch))

    def zq(v):                          # printed upright: every rail and tip on the 0.2 mm grid
        return round(v / 0.2) * 0.2
    vm = zq(h * 0.55)
    cells = [rect(0, 0, L, 0.6), rect(0, vm, L, vm + 0.4)]
    for j in range(k + 1):
        u = L * j / k
        cells.append(rect(u - bar / 2, 0, u + bar / 2, zq(h * (1.0 if j % 2 == 0 else 0.75))))
        if j < k:
            uL, uR = u + bar / 2, u + L / k - bar / 2
            g = min((uR - uL) / 2, vm - 0.6)
            cells.append(poly([(uL, vm - g), ((uL + uR) / 2, vm), (uR, vm - g), (uR, vm + 0.01), (uL, vm + 0.01)]))
    return M.extrude(cs_union(cells) ^ rect(0, 0, L, h + 1), t).translate([0, 0, -t / 2])


def cresting(path, z0, h=2.4, pitch=1.6, bar=0.5, t=0.6, d_off=0.0, finials=True):
    """Iron roof cresting (a pierced fence of loops and spikes) along a closed path."""
    P, Mi = _edges(path)
    out = []
    n = len(P)
    for i in range(n):
        a, b = P[i] + d_off * Mi[i], P[(i + 1) % n] + d_off * Mi[(i + 1) % n]
        f = Facade(a, b, 0.0)
        fence = crest_fence(f.L, h, pitch, bar, t)
        A = f.A.copy()
        A[:, 3] = f.world(0, 0, 0) + np.array([0, 0, z0])
        out.append(fence.transform(A))
    return union(out)


def shift_profile(prof, z0):
    return [(d, z + z0) for d, z in prof]


# Italianate deep eave: frieze board, bed moulding, wide soffit, fascia and crown fillet.
# Heights sit on the 0.2 mm grid measured from the top (the ring prints upside down).
# The ring reaches 4.4 inside the wall face so the locating lip (to 4.2) stands on it upside down.
EAVE_DEEP = [(-4.4, 0), (0.9, 0), (0.9, 5.0), (1.4, 5.2), (6.8, 5.2), (6.8, 6.6), (7.3, 6.8), (7.3, 7.6), (-4.4, 7.6)]
# Compact bracketed cornice (one-storey wings, towers, cupolas).
CORNICE_SMALL = [(-4.4, 0), (0.8, 0), (0.8, 4.0), (1.2, 4.2), (1.3, 4.6), (3.2, 4.6), (3.2, 5.6), (3.6, 6.0),
                 (4.2, 6.8), (4.7, 7.4), (4.8, 8.0), (-4.4, 8.0)]


def bracketed_cornice(path, z0, prof, brackets=None, dents=None, lip_t=3.0, lip_h=1.6, deck=None, panels=None):
    """A cornice ring swept along ``path`` with brackets and dentils (prints upside down).

    brackets = dict(z_top, h, d0, d, t, pitch, pair=0, margin=2.5, skip=None) (z_top relative to z0;
               skip(p) -> True drops the bracket at world point p, e.g. where a tower cuts the ring)
    dents    = dict(z, h, d0, d, tooth=0.6, gap=0.5) (z relative to z0). Put their top at the
               soffit (z + h = soffit height): the ring prints upside down, and dentils that stop
               short of the soffit hang over a gap and get support.
    panels   = dict(z, h, d) raised frieze panels with a boss between the bracket pairs
    lip_t    = wall thickness: a locating lip drops just inside the wall's inner face
    deck     = (z_bottom, z_top) relative to z0 for a solid roof deck filling the ring, or None."""
    parts = [sweep_ring(path, shift_profile(prof, z0))]
    if brackets:
        b = dict(pair=0.0, margin=2.5)
        b.update(brackets)
        parts.append(edge_brackets(path, z0 + b["z_top"], b["h"], b["d0"], b["d"], b["t"], b["pitch"],
                                   margin=b["margin"], pair=b["pair"], skip=b.get("skip"), style=b.get("style", "scroll")))
    if brackets and panels:
        b = dict(pair=0.0, margin=2.5)
        b.update(brackets)
        parts.append(edge_panels(path, z0 + panels["z"], panels["h"], b["d0"], panels["d"], b["pitch"],
                                 margin=b["margin"], pair=b["pair"], t=b["t"]))
    if dents:
        dn = dict(tooth=0.6, gap=0.5)
        dn.update(dents)
        parts.append(edge_dentils(path, z0 + dn["z"], dn["h"], dn["d0"], dn["d"], tooth=dn["tooth"], gap=dn["gap"]))
    base = poly(ccw(path))
    if lip_t:
        lip = offset(base, -lip_t - 0.15) - offset(base, -lip_t - 1.2)
        parts.append(slab(lip, z0 - lip_h, z0 + 0.01))
    if deck:
        parts.append(slab(offset(base, -lip_t - 0.15), z0 + deck[0], z0 + deck[1]))
    return union(parts)


def flat_roof(block, keep=None, prof=CORNICE_SMALL, pitch=8.0):
    """Cornice ring + flat deck for a one-storey block (prints upside down)."""
    h = prof[-1][1]
    m = bracketed_cornice(block.pts, block.z1, prof,
                          brackets=dict(z_top=4.6, h=4.2, d0=0.8, d=2.4, t=0.7, pitch=pitch, margin=2.4),
                          dents=dict(z=3.8, h=0.8, d0=0.8, d=0.7), lip_h=1.2,
                          deck=(h - 2.0, h))
    return m - keep if keep is not None else m


def hip_roof(pieces, z_eave, slope, d_eave, texture="seam", flat_top=None, tex_kw=None, zlo=None):
    """Hipped roof over the union of convex ``pieces`` = [(path, exposed_edges), ...].

    Each piece's planes rise from its exposed edges (offset d_eave) at z_eave. Concave
    outlines (bays, ells) are roofed as several convex pieces whose planes meet in
    valleys. flat_top = z to truncate at (deck for a cupola), or None. A piece may carry its
    own slope as a third item. ``zlo`` extends the solid down (a flat underside to print on).
    Returns (solid, texture)."""
    solids, planes = [], []
    for pc in pieces:                       # (path, exposed) or (path, exposed, own slope)
        path, exposed = pc[0], pc[1]
        s, pl = hip_solid(path, z_eave, pc[2] if len(pc) > 2 else slope, zlo if zlo is not None else z_eave,
                          d_eave=d_eave, exposed=exposed)
        solids.append(s)
        planes.append(pl)
    texs = []
    for k, pc in enumerate(pieces):
        path = pc[0]
        if texture is None:
            break
        t = hip_texture(path, planes[k], z_eave, d_eave=d_eave, shape=texture, **(tex_kw or {}))
        others = [solids[j] for j in range(len(pieces)) if j != k]
        if others:
            t = t - union(others)
        texs.append(t)
    solid = union(solids)
    tex = union(texs)
    if flat_top is not None:
        solid = solid.trim_by_plane([0, 0, -1.0], -flat_top)
        tex = tex.trim_by_plane([0, 0, -1.0], -(flat_top - 0.2))
    return solid, tex


def cresting_strips(crest, path, z, d_off, t=0.6):
    """Split a cresting loop (from ``cresting``) into one flat-printable strip per edge.
    Each strip stops short of the corners and takes only its own fence (``t`` thick), so
    no sliver of the crossing fence rides along. Returns [(edge_index, solid, frame 3x4,
    length)] -- print each with inv34(frame)."""
    P, Mi = _edges(path)
    out = []
    n = len(P)
    for i in range(n):
        a, b = P[i] + d_off * Mi[i], P[(i + 1) % n] + d_off * Mi[(i + 1) % n]
        f = Facade(a, b, z)
        e = t / 2 + 0.05
        clip = f.place(box([e, -1, -t / 2 - 0.01], [f.L - e, 5, t / 2 + 0.01]))
        seg = crest ^ clip
        if not seg.is_empty():
            out.append((i, seg, f.A.copy(), f.L))
    return out


# ------------------------------------------------------------------ mansards
def offset_path(path, d):
    """The convex plan ``path`` offset outward by d (mitred corners), CCW."""
    P, Mi = _edges(path)
    return [tuple(p + d * m) for p, m in zip(P, Mi)]


def mansard(path, prof, t=2.6, tex=None):
    """A mansard band on a convex plan ``path``: hollow, open at the top, printed upright.

    ``prof`` = the outer profile [(d, z), ...] from the bottom up, d = outward offset from
    the wall face. It must only move in (or straight up) as z rises, so no outer face
    overhangs: a straight slope with a bell-cast kick at its foot, or a concave tower cap.
    The inner face is one straight line parallel to the chord from the bottom point to the
    top one, set in so the band is at least ``t`` thick everywhere. It leans in at about
    the roof's own pitch (15-20 degrees off vertical), which prints fine.
    ``tex`` = dict(pitch, wtab, d, shape) puts slate rows on every segment taller than a row
    (a short bell-cast kick stays smooth, like flashing), or None. The band prints upright,
    or upside down when dormer notches or other openings have arched tops: then every
    opening widens as the print rises, and the slate rows' ledges face up.
    Returns (solid, texture, inner) where inner(z) is the inner face offset at height z."""
    P, Mi = _edges(path)

    def ring_at(d, z):
        return np.c_[P + d * Mi, np.full(len(P), z)]
    outer = union([M.hull_points(np.vstack([ring_at(d0, z0), ring_at(d1, z1)]).tolist())
                   for (d0, z0), (d1, z1) in zip(prof[:-1], prof[1:])])
    (da, za), (db, zb) = prof[0], prof[-1]
    k = (db - da) / (zb - za)
    s = t + max(da + k * (z - za) - d for d, z in prof)

    def inner(z):
        return da + k * (z - za) - s
    cav = M.hull_points(np.vstack([ring_at(inner(za - 1.0), za - 1.0), ring_at(inner(zb + 1.0), zb + 1.0)]).tolist())
    solid = outer - cav
    texture = M()
    if tex:
        tk = dict(pitch=1.6, wtab=1.9, d=0.4, shape="fish")
        tk.update(tex)
        texture = union([slope_texture(path, z0, z1, d0, d1, **tk)
                         for (d0, z0), (d1, z1) in zip(prof[:-1], prof[1:]) if z1 - z0 > tk["pitch"] + 0.01])
        texture = texture.trim_by_plane([0, 0, -1.0], -zb)      # rows stand square to the slope: none above the top
    return solid, texture, inner


def mansard_top(path, d_top, z, t, h=2.6, deck_th=1.2, seams=5.2, clr=0.15):
    """Top curb and flat deck of a mansard whose band's top outer edge is at offset
    ``d_top`` and is ``t`` thick (horizontally) at height z. Two parts:

    * ``ring``: a moulded curb on the band top, printed upside down. A lip in the same
      profile drops just inside the band's inner edge to locate it, and its inner face has a
      45 degree seat for the deck;
    * ``deck``: a flat standing-seam deck plate, printed flat, its edge chamfered 45 degrees
      to sit on the seat, flush with the curb top.

    Every face either stands on the one below or overhangs 45 degrees in print. Returns
    dict(ring, deck, path=top outline, z_top=deck top)."""
    top_path = offset_path(path, d_top)
    prof = [(-t - 1.2, -1.2), (-t - clr, -1.2), (-t - clr, 0.0), (0.2, 0.0), (0.2, 0.6), (0.6, 1.0), (0.6, 1.6),
            (1.0, 2.0), (1.0, h), (-t, h), (-t - deck_th, h - deck_th)]
    ring = sweep_ring(top_path, shift_profile(prof, z))
    P, Mi = _edges(top_path)
    a = np.c_[P + (-t - clr) * Mi, np.full(len(P), z + h)]
    b = np.c_[P + (-t - clr - deck_th) * Mi, np.full(len(P), z + h - deck_th)]
    deck = M.hull_points(np.vstack([a, b]).tolist())
    if seams:
        cs = poly([tuple(p) for p in P + (-t - clr - 0.8) * Mi])
        x0, y0, x1, y1 = cs.bounds()
        ribs = cs_union([rect(x - 0.25, y0, x + 0.25, y1) for x in np.arange(x0 + seams / 2, x1, seams)]) ^ cs
        deck = deck + slab(ribs, z + h - 0.01, z + h + 0.4)
    return dict(ring=ring, deck=deck, path=top_path, z_top=z + h)


# ------------------------------------------------------------------ two-layer eaves
def _bracket_us(L, pitch, margin, pair):
    k = max(1, int(round((L - 2 * margin) / pitch)))
    us = [margin + (L - 2 * margin) * j / k for j in range(k + 1)]
    return [u + du for u in us for du in ((-pair / 2, pair / 2) if pair > 0 else (0.0,))]


def frieze_ring(path, z0, h=5.6, t=3.0, face=0.9, brackets=None, tail=1.6, panels=True, skip=None):
    """Upright frieze course under a bracketed cornice ring: the lower layer of a two-layer
    eave. The full wall thickness plus a frieze board ``face`` proud, a projecting plinth
    moulding at its foot (on the print bed, so it needs no support), raised panels with a
    diamond boss between the bracket positions, and a tapering scroll tail with a drop under
    every bracket of the cornice above, so each bracket continues down the frieze.

    ``brackets`` = the cornice's bracket dict (pitch, margin, pair, t, d0): the tails line up
    with it and meet the cornice brackets' feet (``tail`` = their projection there).
    It stands on the wall's top lip; the cornice ring's own lip drops inside it."""
    prof = [(-t, 0.0), (face + 0.5, 0.0), (face + 0.5, 0.6), (face, 1.1), (face, h), (-t, h)]
    parts = [sweep_ring(path, shift_profile(prof, z0))]
    P, Mi = _edges(path)
    b = dict(pair=0.0, margin=2.5, t=0.8, pitch=10.0)
    b.update(brackets or {})
    for i in range(len(P)):
        a_, b_ = P[i], P[(i + 1) % len(P)]
        f = Facade(a_, b_, 0.0)
        if f.L < 2 * b["margin"] + b["t"]:
            continue
        us = _bracket_us(f.L, b["pitch"], b["margin"], b["pair"])
        loc = []
        for u in us:
            if skip is not None and skip(f.world(u, 0, face)):
                continue
            L = h - 1.6
            side = [(0.0, h), (tail, h), (tail * 0.6, h - L * 0.55), (0.6, h - L), (0.6, 1.6), (0.0, 1.6)]
            loc.append(side_profile(side, u - b["t"] / 2, u + b["t"] / 2).translate([0, 0, face - 0.02]))
            drop = [(0.0, 1.6), (0.6, 1.6), (0.0, 1.0)]
            loc.append(side_profile(drop, u - b["t"] / 2, u + b["t"] / 2).translate([0, 0, face - 0.02]))
        if panels:
            half = (b["pair"] / 2 if b["pair"] > 0 else 0.0) + b["t"] / 2 + 0.6
            centres = _bracket_us(f.L, b["pitch"], b["margin"], 0.0)
            for ua, ub in zip(centres[:-1], centres[1:]):
                u0, u1 = ua + half, ub - half
                if u1 - u0 < 2.4:
                    continue
                if skip is not None and (skip(f.world(u0, 0, face)) or skip(f.world(u1, 0, face))):
                    continue
                loc.append(chamfer_box(u0, 1.8, u1, h - 0.8, face - 0.05, 0.45, c=0.3))
                loc.append(lozenge((u0 + u1) / 2, (h + 1.0) / 2, min(1.6, (u1 - u0) * 0.3), min(2.2, h - 3.0),
                                   face + 0.4, 0.3))
        if loc:
            A = f.A.copy()
            A[:, 3] = f.world(0.0, 0.0, 0.0) + np.array([0, 0, z0])
            parts.append(union(loc).transform(A))
    return union(parts)

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
from manifold3d import CrossSection as CS, Manifold as M

from .core import (Facade, ccw, cs_union, frame, miters, offset, poly, rect, scallop_rows, slab,
                   sweep_ring, union)
from .ornament import console, dentils


def _edges(path):
    P = np.asarray(ccw(path), float)
    return P, miters(P)


def edge_brackets(path, z_top, h, d0, d, t, pitch, margin=2.5, pair=0.0, corner=True, skip=None):
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
                c = console(h, d, t, u=uu, v_top=0.0, w0=0.0)
                A = f.A.copy()
                A[:, 3] = f.world(0.0, 0.0, d0) + np.array([0, 0, z_top])
                out.append(c.transform(A))
    return union(out)


def edge_dentils(path, z0, h, d0, d, tooth=0.45, gap=0.4, margin=0.8, skip=None):
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


def hip_texture(path, planes, z_eave, d_eave=0.0, pitch=1.55, wtab=1.8, d=0.33, shape="fish", zmax=None):
    """Scallops on each hip face (region = the face's plan triangle/trapezoid)."""
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
        tex = scallop_rows(loc, pitch, wtab, d=d, shape=shape, datum=loc.bounds()[1])
        vdir = np.array([t[0] * cth, t[1] * cth, s * cth])
        ndir = np.array([-t[0] * s * cth, -t[1] * s * cth, cth])
        out.append(tex.transform(frame([q[0], q[1], pi.z0], [e[0], e[1], 0.0], vdir, ndir)))
    tex = union(out)
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


def cresting(path, z0, h=2.2, pitch=1.4, bar=0.3, t=0.45, d_off=0.0, finials=True):
    """Iron roof cresting (a pierced fence of loops and spikes) along a closed path."""
    P, Mi = _edges(path)
    out = []
    n = len(P)
    for i in range(n):
        a, b = P[i] + d_off * Mi[i], P[(i + 1) % n] + d_off * Mi[(i + 1) % n]
        f = Facade(a, b, 0.0)
        L = f.L
        k = max(1, int(L / pitch))
        cells = [rect(0, 0, L, bar), rect(0, h * 0.55, L, h * 0.55 + bar * 0.8)]
        for j in range(k + 1):
            u = L * j / k
            cells.append(rect(u - bar / 2, 0, u + bar / 2, h * (1.0 if j % 2 == 0 else 0.75)))
            if j < k:
                cx = u + L / k / 2
                r = min(L / k, h * 0.5) * 0.36
                ring = CS.circle(r, 12).translate((cx, h * 0.3)) - CS.circle(r - bar * 0.7, 12).translate((cx, h * 0.3))
                cells.append(ring)
        fence = M.extrude(cs_union(cells) ^ rect(0, 0, L, h + 1), t).translate([0, 0, -t / 2])
        A = f.A.copy()
        A[:, 3] = f.world(0, 0, 0) + np.array([0, 0, z0])
        out.append(fence.transform(A))
    return union(out)

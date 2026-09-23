"""Core geometry for HO-scale (1:87.1) printable architecture.

Units are millimetres at model scale. ``ft()`` / ``inch()`` convert prototype
dimensions. Plan coordinates: x east, y north, z up.

Facade-local coordinates (see ``Facade``): u runs along the facade (left to
right when seen from outside), v is up from the facade base, w points out of
the building (w = 0 is the outer face of the wall core).
"""
import math

import numpy as np
from manifold3d import CrossSection as CS, FillRule, JoinType, Manifold as M, Mesh, OpType

SCALE = 87.1


def ft(x):
    return x * 304.8 / SCALE


def inch(x):
    return ft(x / 12.0)


# ------------------------------------------------------------------ primitives
def box(p0, p1):
    p0 = np.asarray(p0, float)
    p1 = np.asarray(p1, float)
    lo, hi = np.minimum(p0, p1), np.maximum(p0, p1)
    return M.cube(list(hi - lo)).translate(list(lo))


def union(ms):
    ms = [m for m in ms if m is not None and not m.is_empty()]
    if not ms:
        return M()
    return ms[0] if len(ms) == 1 else M.batch_boolean(ms, OpType.Add)


def cs_union(cs):
    cs = [c for c in cs if c is not None and not c.is_empty()]
    if not cs:
        return CS()
    return cs[0] if len(cs) == 1 else CS.batch_boolean(cs, OpType.Add)


def rect(u0, v0, u1, v1):
    return CS.square((u1 - u0, v1 - v0)).translate((u0, v0))


def poly(pts):
    return CS([np.asarray(pts, float)], FillRule.EvenOdd)


def circle(c, r, seg=32):
    return CS.circle(r, seg).translate(tuple(c))


def arch_cs(u0, u1, v0, spring, rise=None, seg=24):
    """Opening outline: rectangle u0..u1 from v0 up to ``spring`` capped by an arch.

    rise=None gives a semicircle; a smaller rise gives a segmental arch."""
    w = u1 - u0
    half = w / 2
    rise = half if rise is None else rise
    if rise >= half - 1e-6:
        r = half
        cy = spring
    else:
        r = (half * half + rise * rise) / (2 * rise)
        cy = spring + rise - r
    a0 = math.asin(min(1.0, half / r))
    pts = [(u0, v0), (u1, v0), (u1, spring)]
    for k in range(1, seg):
        a = -a0 + 2 * a0 * k / seg
        pts.append((u0 + half + r * math.sin(-a), cy + r * math.cos(a)))
    pts.append((u0, spring))
    # the loop above runs right-to-left; make sure it is ordered correctly
    return poly(pts)


def offset(cs, d, join=JoinType.Miter):
    return cs.offset(d, join, 4.0)


def slab(cs, z0, z1):
    return M.extrude(cs, z1 - z0).translate([0, 0, z0])


def cyl(p, r, h, seg=24, r2=None):
    return M.cylinder(h, r, r if r2 is None else r2, seg).translate(list(p))


def revolve(profile, seg=32):
    """profile: list of (r, z); revolved about the z axis."""
    return M.revolve(poly(profile), seg)


def frame(origin, xdir, ydir, zdir):
    A = np.zeros((3, 4))
    A[:, 0], A[:, 1], A[:, 2], A[:, 3] = xdir, ydir, zdir, origin
    return A


def m4(A):
    B = np.eye(4)
    B[:3, :] = A
    return B


def compose(B, A):
    """Apply A then B (both 3x4)."""
    return (m4(B) @ m4(A))[:3, :]


def inv34(A):
    R, t = A[:, :3], A[:, 3]
    out = np.zeros((3, 4))
    out[:, :3] = R.T
    out[:, 3] = -R.T @ t
    return out


I34 = np.hstack([np.eye(3), np.zeros((3, 1))])


def rot_z(deg, about=(0, 0)):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    A = np.array([[c, -s, 0, 0], [s, c, 0, 0], [0, 0, 1.0, 0]])
    ax, ay = about
    A[0, 3] = ax - (c * ax - s * ay)
    A[1, 3] = ay - (s * ax + c * ay)
    return A


def extrude_profile_x(profile, x0, x1):
    """Extrude a (y, z) profile polygon along +x from x0 to x1."""
    m = M.extrude(poly(profile), x1 - x0)          # profile in (x,y) plane, along z
    return m.transform(frame([x0, 0, 0], [0, 0, 1], [1, 0, 0], [0, 1, 0]))


# ------------------------------------------------------------------ polygons
def ccw(pts):
    pts = [tuple(map(float, p)) for p in pts]
    a = 0.0
    for i in range(len(pts)):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % len(pts)]
        a += x0 * y1 - x1 * y0
    return pts if a > 0 else pts[::-1]


def miters(pts):
    """Outward miter vectors of a CCW polygon (offset by d = P + d*m)."""
    P = np.asarray(pts, float)
    n = len(P)
    out = np.zeros_like(P)
    for i in range(n):
        a, b, c = P[i - 1], P[i], P[(i + 1) % n]
        d0 = (b - a) / np.linalg.norm(b - a)
        d1 = (c - b) / np.linalg.norm(c - b)
        n0 = np.array([d0[1], -d0[0]])
        n1 = np.array([d1[1], -d1[0]])
        out[i] = (n0 + n1) / (1 + n0 @ n1)
    return out


def sweep_ring(path, profile):
    """Sweep a closed (d, z) profile around a closed plan path with mitred corners.

    d is the outward offset from the path. The profile must be a simple polygon
    and offsets must stay small relative to the path's edge lengths."""
    P = np.asarray(ccw(path), float)
    Mi = miters(P)
    prof = np.asarray(profile, float)
    # profile orientation: make it CCW in (d, z)
    a = np.sum(prof[:, 0] * np.roll(prof[:, 1], -1) - np.roll(prof[:, 0], -1) * prof[:, 1])
    if a < 0:
        prof = prof[::-1]
    N, K = len(P), len(prof)
    V = np.zeros((K * N, 3))
    for k, (d, z) in enumerate(prof):
        V[k * N:(k + 1) * N, :2] = P + d * Mi
        V[k * N:(k + 1) * N, 2] = z
    tris = []
    for k in range(K):
        k1 = (k + 1) % K
        for i in range(N):
            i1 = (i + 1) % N
            a0, a1 = k * N + i, k * N + i1
            b0, b1 = k1 * N + i, k1 * N + i1
            tris.append((a0, b0, b1))
            tris.append((a0, b1, a1))
    T = np.array(tris, np.uint32)
    m = M(Mesh(V.astype(np.float32), T))
    if m.is_empty() or m.volume() <= 0:
        m = M(Mesh(V.astype(np.float32), T[:, ::-1].copy()))
    return m


def sweep_run(path, profile, end0=None, end1=None, closed=False):
    """Sweep a (d, z) profile along an open plan polyline (d = left->right offset).

    Straight segments are extruded and trimmed by the bisector planes at every
    joint, so any profile works. ``end0``/``end1`` optionally give plan vectors
    for the end cut planes (default: square cuts)."""
    P = np.asarray(path, float)
    segs = []
    n = len(P) - 1
    for i in range(n):
        a, b = P[i], P[i + 1]
        dvec = (b - a) / np.linalg.norm(b - a)
        L = np.linalg.norm(b - a)
        # profile d axis = right of travel direction
        right = np.array([dvec[1], -dvec[0]])
        m = M.extrude(poly(profile), L + 40).translate([0, 0, -20])
        A = frame([a[0], a[1], 0], [right[0], right[1], 0], [0, 0, 1], [dvec[0], dvec[1], 0])
        m = m.transform(A)
        # trim at start
        if i > 0:
            pd = (a - P[i - 1]) / np.linalg.norm(a - P[i - 1])
            nrm = pd + dvec
        else:
            nrm = dvec if end0 is None else np.asarray(end0, float)
        nrm = nrm / np.linalg.norm(nrm)
        m = m.trim_by_plane([nrm[0], nrm[1], 0.0], float(nrm @ a))
        if i < n - 1:
            nd = (P[i + 2] - b) / np.linalg.norm(P[i + 2] - b)
            nrm = -(dvec + nd)
        else:
            nrm = -dvec if end1 is None else -np.asarray(end1, float)
        nrm = nrm / np.linalg.norm(nrm)
        m = m.trim_by_plane([nrm[0], nrm[1], 0.0], float(nrm @ b))
        segs.append(m)
    return union(segs)


def ring_cs(path, d_out, d_in):
    """Plan ring between outward offsets d_in < d_out of a closed path."""
    base = poly(ccw(path))
    return offset(base, d_out) - offset(base, d_in)


# ------------------------------------------------------------------ facades
class Facade:
    """Planar facade from plan point p0 to p1 (building interior on the left)."""

    def __init__(self, p0, p1, zb=0.0):
        p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
        d = p1 - p0
        self.L = float(np.linalg.norm(d))
        self.u = d / self.L
        self.n = np.array([self.u[1], -self.u[0]])          # outward for CCW plans
        self.p0, self.p1, self.zb = p0, p1, zb
        self.A = frame([p0[0], p0[1], zb], [self.u[0], self.u[1], 0], [0, 0, 1], [self.n[0], self.n[1], 0])

    def place(self, m):
        return m.transform(self.A)

    def world(self, u, v, w=0.0):
        p = self.p0 + self.u * u + self.n * w
        return np.array([p[0], p[1], self.zb + v])

    def to_local(self):
        return inv34(self.A)


def facades_of(path, zb=0.0):
    P = ccw(path)
    return [Facade(P[i], P[(i + 1) % len(P)], zb) for i in range(len(P))]


# ------------------------------------------------------------------ textures
def clapboard(region, pitch=inch(4.0) * 1.0, d=0.3, dmin=0.05, datum=0.0):
    """Bevel-lap siding in facade (u, v): each course thickens toward its bottom edge.

    The bottom edge is a short horizontal step, so it prints cleanly upright."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    k0 = math.floor((v0 - datum) / pitch) - 1
    k1 = math.ceil((v1 - datum) / pitch) + 1
    pts = [(datum + k0 * pitch, 0.0)]
    for k in range(k0, k1):
        vk = datum + k * pitch
        pts += [(vk, d), (vk + pitch, dmin)]
    pts.append((datum + k1 * pitch, 0.0))
    strip = M.extrude(poly(pts), (u1 - u0) + 2).transform(frame([u0 - 1, 0, 0], [0, 1, 0], [0, 0, 1], [1, 0, 0]))
    return strip ^ M.extrude(region, d + 0.2).translate([0, 0, -0.1])


def scallop_rows(region, pitch, wtab, d=0.35, gap=0.14, datum=0.0, lap=1.5, seg=12, shape="fish", taper=0.75):
    """Fish-scale (or square) slate rows over a flat (u, v) region; v = up-slope."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    rows = []
    k0 = math.floor((v0 - datum) / pitch) - 1
    k1 = math.ceil((v1 - datum) / pitch) + 1
    for k in range(k0, k1):
        vk = datum + k * pitch
        top = vk + pitch * lap
        band = region ^ rect(u0 - 1, vk, u1 + 1, top)
        if band.is_empty():
            continue
        tabs = []
        u = u0 - wtab * 1.5 + (k % 2) * wtab * 0.5
        while u < u1 + wtab:
            r = (wtab - gap) / 2
            if shape == "fish":
                tabs.append(circle((u + wtab / 2, vk + r), r, seg))
                tabs.append(rect(u + gap / 2, vk + r, u + wtab - gap / 2, top))
            elif shape == "diamond":
                c = u + wtab / 2
                tabs.append(poly([(c, vk), (c + r, vk + r), (c + r, top), (c - r, top), (c - r, vk + r)]))
            else:
                tabs.append(rect(u + gap / 2, vk, u + wtab - gap / 2, top))
            u += wtab
        row = cs_union(tabs) ^ band
        if row.is_empty():
            continue
        m = M.extrude(row, d)
        span = top - vk

        def f(Pv, vk=vk, span=span):
            Pv = np.array(Pv)
            t = np.clip((Pv[:, 1] - vk) / span, 0, 1)
            Pv[:, 2] *= (1 - taper * t)
            return Pv

        rows.append(m.warp_batch(f))
    return union(rows)


def ashlar(region, course=(ft(1.0), ft(1.6)), length=(ft(1.2), ft(3.2)), d=0.5, gap=0.3,
           seed=1, datum=0.0, rough=0.12, bevel=0.2):
    """Coursed rubble / ashlar stone: random course heights and stone lengths,
    each stone a bevelled block with a slightly irregular face depth."""
    if region.is_empty():
        return M()
    rng = np.random.default_rng(seed)
    u0, v0, u1, v1 = region.bounds()
    stones = []
    v = datum + math.floor((v0 - datum) / course[1]) * course[1]
    while v < v1:
        h = rng.uniform(*course)
        u = u0 - rng.uniform(0, length[1])
        while u < u1:
            L = rng.uniform(*length)
            s = rect(u + gap / 2, v + gap / 2, u + L - gap / 2, v + h - gap / 2) ^ region
            if not s.is_empty() and s.area() > 0.3:
                dd = d * rng.uniform(0.75, 1.15)
                core = M.extrude(s, dd * 0.6)
                top = s.offset(-bevel, JoinType.Round)
                if not top.is_empty():
                    face = M.extrude(top, dd * 0.4).translate([0, 0, dd * 0.6])
                    # pillow the face a little so it doesn't read as a flat tile
                    c = np.array(top.bounds())
                    cx, cy = (c[0] + c[2]) / 2, (c[1] + c[3]) / 2
                    sx, sy = max(1e-3, (c[2] - c[0]) / 2), max(1e-3, (c[3] - c[1]) / 2)

                    def fp(Pv, cx=cx, cy=cy, sx=sx, sy=sy, dd=dd):
                        Pv = np.array(Pv)
                        top_ = Pv[:, 2] > dd * 0.61
                        r2 = ((Pv[:, 0] - cx) / sx) ** 2 + ((Pv[:, 1] - cy) / sy) ** 2
                        Pv[top_, 2] -= rough * np.clip(r2[top_], 0, 1)
                        return Pv

                    core = core + face.refine(3).warp_batch(fp)
                stones.append(core)
            u += L
        v += h
    return union(stones)


def brick(region, bl=inch(8), bh=inch(2.67), mortar=0.14, d=0.18, datum=0.0, uoff=0.0):
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    cells = []
    k = math.floor((v0 - datum) / bh) - 1
    while datum + k * bh < v1:
        v = datum + k * bh
        u = u0 - bl + (k % 2) * bl / 2 + uoff
        while u < u1:
            cells.append(rect(u + mortar / 2, v + mortar / 2, u + bl - mortar / 2, v + bh - mortar / 2))
            u += bl
        k += 1
    return M.extrude(cs_union(cells) ^ region, d)


def lattice(region, pitch=1.6, bar=0.45, d=0.5, angle=45):
    """Diagonal lattice (two layers of slats) filling a (u, v) region."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    diag = math.hypot(u1 - u0, v1 - v0) + 4
    cx, cy = (u0 + u1) / 2, (v0 + v1) / 2
    out = []
    for sgn, z0 in ((1, 0.0), (-1, d / 2)):
        bars = []
        k = -diag
        while k < diag:
            bars.append(rect(k - bar / 2, -diag, k + bar / 2, diag))
            k += pitch
        cs = cs_union(bars).rotate(sgn * angle).translate((cx, cy)) ^ region
        out.append(M.extrude(cs, d / 2).translate([0, 0, z0]))
    return union(out)


# ------------------------------------------------------------------ mesh io
def mesh_arrays(m):
    mesh = m.to_mesh()
    return np.asarray(mesh.vert_properties)[:, :3].astype(np.float64), np.asarray(mesh.tri_verts).astype(np.int64)

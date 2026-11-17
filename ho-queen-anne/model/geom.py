"""Geometry helpers for the HO-scale Queen Anne house.

All units are millimetres at HO scale (1:87.1). Use ``ft()`` to convert
prototype feet to model millimetres.

Coordinate system (world): x = left->right when viewed from the front,
y = front->back, z = up. The front of the house faces -y.

Wall-local coordinates: u runs along the wall, v is up, w points out of the
wall (w = 0 is the sheathing plane; texture sits at w >= 0, the wall core at
w < 0).
"""
import math
import numpy as np
from manifold3d import Manifold as M, CrossSection as CS, OpType, JoinType, FillRule

SCALE = 87.1


def ft(x):
    return x * 304.8 / SCALE


def inch(x):
    return ft(x / 12.0)


# ---------------------------------------------------------------- basics
def box(p0, p1):
    p0 = np.asarray(p0, float)
    p1 = np.asarray(p1, float)
    lo = np.minimum(p0, p1)
    hi = np.maximum(p0, p1)
    return M.cube(list(hi - lo)).translate(list(lo))


def union(ms):
    ms = [m for m in ms if m is not None and not m.is_empty()]
    if not ms:
        return M()
    if len(ms) == 1:
        return ms[0]
    return M.batch_boolean(ms, OpType.Add)


def cs_union(cs):
    cs = [c for c in cs if c is not None and not c.is_empty()]
    if not cs:
        return CS()
    if len(cs) == 1:
        return cs[0]
    return CS.batch_boolean(cs, OpType.Add)


def rect(u0, v0, u1, v1):
    return CS.square((u1 - u0, v1 - v0)).translate((u0, v0))


def poly(pts):
    return CS([np.asarray(pts, float)], FillRule.EvenOdd)


def prism(pts, z0, z1):
    return M.extrude(poly(pts), z1 - z0).translate([0, 0, z0])


def cyl(p, r, h, seg=24, r2=None):
    return M.cylinder(h, r, r if r2 is None else r2, seg).translate(list(p))


def revolve(profile, seg=24):
    """profile: list of (r, z) points; revolved about the z axis."""
    return M.revolve(poly(profile), seg)


def frame_matrix(origin, xdir, ydir, zdir):
    A = np.zeros((3, 4))
    A[:, 0] = xdir
    A[:, 1] = ydir
    A[:, 2] = zdir
    A[:, 3] = origin
    return A


# ---------------------------------------------------------------- walls
class Wall:
    """A planar wall from plan point p0 to p1 with base height zb."""

    def __init__(self, p0, p1, zb):
        p0 = np.asarray(p0, float)
        p1 = np.asarray(p1, float)
        d = p1 - p0
        self.L = float(np.linalg.norm(d))
        u = d / self.L
        self.u = u
        self.n = np.array([u[1], -u[0]])
        self.p0 = p0
        self.zb = zb
        self.A = frame_matrix([p0[0], p0[1], zb], [u[0], u[1], 0], [0, 0, 1],
                              [self.n[0], self.n[1], 0])

    def place(self, m):
        return m.transform(self.A)

    def world(self, u, v, w=0.0):
        p = self.p0 + self.u * u + self.n * w
        return np.array([p[0], p[1], self.zb + v])


def clapboard(region, e=inch(4.5), d=0.34, dmin=0.06, datum=0.0):
    """Lap siding texture over a (u,v) region. Courses aligned to ``datum``."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    k0 = math.floor((v0 - datum) / e) - 1
    k1 = math.ceil((v1 - datum) / e) + 1
    pts = [(datum + k0 * e, 0.0)]
    for k in range(k0, k1):
        vk = datum + k * e
        pts.append((vk, d))
        pts.append((vk + e, dmin))
    pts.append((datum + k1 * e, 0.0))
    prof = poly(pts)
    L = (u1 - u0) + 2
    strip = M.extrude(prof, L).transform(
        frame_matrix([u0 - 1, 0, 0], [0, 1, 0], [0, 0, 1], [1, 0, 0]))
    clip = M.extrude(region, d + 0.2).translate([0, 0, -0.1])
    return strip ^ clip


def shingle_rows(region, e, wtab, d=0.38, shape="fish", gap=0.16,
                 datum=0.0, seed=0, taper=0.8, lap=1.6, seg=14):
    """Overlapping rows of shingles (fish-scale, square or random-width)."""
    if region.is_empty():
        return M()
    rng = np.random.default_rng(seed)
    u0, v0, u1, v1 = region.bounds()
    k0 = math.floor((v0 - datum) / e) - 1
    k1 = math.ceil((v1 - datum) / e) + 1
    rows = []
    for k in range(k0, k1):
        vk = datum + k * e
        top = vk + e * lap
        band = region ^ rect(u0 - 1, vk, u1 + 1, top)
        if band.is_empty():
            continue
        tabs = []
        off = (k % 2) * wtab * 0.5
        u = u0 - wtab * 1.5 + off
        while u < u1 + wtab:
            w = wtab
            if shape == "random":
                w = wtab * rng.uniform(0.65, 1.45)
            if shape == "fish":
                r = (w - gap) / 2
                tabs.append(CS.circle(r, seg).translate((u + w / 2, vk + r)))
                tabs.append(rect(u + gap / 2, vk + r, u + w - gap / 2, top))
            elif shape == "hex":
                c = u + w / 2
                h = (w - gap) / 2
                tabs.append(poly([(c, vk), (c + h, vk + h * 0.8), (c + h, top),
                                  (c - h, top), (c - h, vk + h * 0.8)]))
            else:
                drop = rng.uniform(0, 0.12) if shape == "random" else 0
                tabs.append(rect(u + gap / 2, vk + drop, u + w - gap / 2, top))
            u += w
        row = cs_union(tabs) ^ band
        if row.is_empty():
            continue
        m = M.extrude(row, d)
        span = top - vk

        def f(P, vk=vk, span=span):
            P = np.array(P)
            t = np.clip((P[:, 1] - vk) / span, 0, 1)
            P[:, 2] = P[:, 2] * (1 - taper * t)
            return P

        rows.append(m.warp_batch(f))
    return union(rows)


def stonework(region, course=ft(1.1), d=0.45, gap=0.28, seed=1, datum=0.0):
    """Rough coursed stone (random-length blocks with bevelled faces)."""
    if region.is_empty():
        return M()
    rng = np.random.default_rng(seed)
    u0, v0, u1, v1 = region.bounds()
    stones = []
    v = datum + math.floor((v0 - datum) / course) * course
    while v < v1:
        h = course
        u = u0 - rng.uniform(0, ft(1.5))
        while u < u1:
            L = ft(rng.uniform(1.2, 2.6))
            s = rect(u + gap / 2, v + gap / 2, u + L - gap / 2, v + h - gap / 2)
            s = s ^ region
            if not s.is_empty():
                dd = d * rng.uniform(0.7, 1.15)
                top = s.offset(-0.18, JoinType.Miter)
                st = M.extrude(s, dd * 0.55)
                if not top.is_empty():
                    st = st + M.extrude(top, dd)
                stones.append(st)
            u += L
        v += h
    return union(stones)


def brickwork(region, bl=inch(8) * 1.0, bh=inch(2.67) * 1.0, mortar=0.16,
              d=0.2, datum=0.0):
    """Running-bond bricks as raised blocks."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    cells = []
    k = math.floor((v0 - datum) / bh) - 1
    while datum + k * bh < v1:
        v = datum + k * bh
        off = (k % 2) * bl / 2
        u = u0 - bl + off
        while u < u1:
            cells.append(rect(u + mortar / 2, v + mortar / 2, u + bl - mortar / 2,
                              v + bh - mortar / 2))
            u += bl
        k += 1
    cs = cs_union(cells) ^ region
    return M.extrude(cs, d)


# ---------------------------------------------------------------- roofs
class Plane:
    """Roof plane z = z0 + s * t.(p - q) with t the unit up-slope direction."""

    def __init__(self, q, t, z0, s):
        self.q = np.asarray(q, float)
        t = np.asarray(t, float)
        self.t = t / np.linalg.norm(t)
        self.z0 = z0
        self.s = s

    def z(self, x, y):
        return self.z0 + self.s * ((x - self.q[0]) * self.t[0] + (y - self.q[1]) * self.t[1])

    def shifted(self, dz):
        return Plane(self.q, self.t, self.z0 + dz, self.s)

    def normal(self):
        n = np.array([-self.s * self.t[0], -self.s * self.t[1], 1.0])
        return n / np.linalg.norm(n)


def halfspace_below(solid, pl):
    n = pl.normal()
    p = np.array([pl.q[0], pl.q[1], pl.z0])
    # keep the side where -n points (below the plane)
    return solid.trim_by_plane(list(-n), float(np.dot(-n, p)))


def roof_solid(footprint, planes, zlo, zhi=400.0):
    s = M.extrude(poly(footprint), zhi - zlo).translate([0, 0, zlo])
    for pl in planes:
        s = halfspace_below(s, pl)
    return s


def roof_slab(footprint, planes, thick, zlo):
    outer = roof_solid(footprint, planes, zlo)
    inner = roof_solid(footprint, [p.shifted(-thick) for p in planes], zlo - 50)
    return outer - inner


def halfplane_cs(a, b, c, big=2000.0):
    """2D region a*x + b*y + c <= 0 as a CrossSection."""
    n = np.array([a, b], float)
    ln = np.linalg.norm(n)
    if ln < 1e-12:
        return rect(-big, -big, big, big) if c <= 0 else CS()
    n /= ln
    c /= ln
    p0 = -c * n  # point on the line
    tvec = np.array([-n[1], n[0]])
    pts = [p0 + tvec * big, p0 - tvec * big, p0 - tvec * big - n * big,
           p0 + tvec * big - n * big]
    return poly(pts)


def plane_faces(footprint, planes):
    """Plan-view region on which each plane is the (lowest) roof surface."""
    fp = poly(footprint)
    faces = []
    for i, pi in enumerate(planes):
        reg = fp
        for j, pj in enumerate(planes):
            if i == j:
                continue
            # z_i - z_j <= 0 : linear in x,y
            ax = pi.s * pi.t[0] - pj.s * pj.t[0]
            ay = pi.s * pi.t[1] - pj.s * pj.t[1]
            c = (pi.z0 - pi.s * (pi.q @ pi.t)) - (pj.z0 - pj.s * (pj.q @ pj.t))
            reg = reg ^ halfplane_cs(ax, ay, c)
        faces.append(reg)
    return faces


def plane_frame(pl):
    """Matrix mapping plane-local (u, v_slope, w) to world."""
    s = pl.s
    c = 1 / math.sqrt(1 + s * s)
    sn = s * c
    t = pl.t
    e = np.array([t[1], -t[0], 0.0])
    vdir = np.array([t[0] * c, t[1] * c, sn])
    ndir = np.array([-t[0] * sn, -t[1] * sn, c])
    origin = np.array([pl.q[0], pl.q[1], pl.z0])
    return frame_matrix(origin, e, vdir, ndir), c


def plan_to_plane_cs(region, pl):
    _, c = plane_frame(pl)
    t = pl.t
    e = np.array([t[1], -t[0]])
    q = pl.q
    # u = e.(p - q) ; v = t.(p - q) / c
    A = np.array([[e[0], e[1], -(e @ q)],
                  [t[0] / c, t[1] / c, -(t @ q) / c]])
    return region.transform(A)


def roof_texture(footprint, planes, kind="random", e=inch(6), wtab=inch(9),
                 d=0.36, seed=3, faces=None):
    out = []
    faces = faces or plane_faces(footprint, planes)
    for i, (pl, reg) in enumerate(zip(planes, faces)):
        if reg.is_empty():
            continue
        loc = plan_to_plane_cs(reg, pl)
        tex = shingle_rows(loc, e, wtab, d=d, shape=kind, seed=seed + i,
                           datum=loc.bounds()[1])
        A, _ = plane_frame(pl)
        out.append(tex.transform(A))
    return union(out)


def segment_bar(p0, p1, width, height, up=(0, 0, 1)):
    """Box of given cross-section running along the 3D segment p0->p1."""
    p0 = np.asarray(p0, float)
    p1 = np.asarray(p1, float)
    x = p1 - p0
    L = np.linalg.norm(x)
    x /= L
    upv = np.asarray(up, float)
    z = upv - x * (upv @ x)
    z /= np.linalg.norm(z)
    y = np.cross(z, x)
    b = M.cube([L, width, height]).translate([0, -width / 2, -height / 2])
    return b.transform(frame_matrix(p0, x, y, z))


def roof_caps(footprint, planes, width=1.2, height=0.9, lift=0.3, faces=None):
    """Caps along every hip/ridge (edges shared by two plane faces)."""
    faces = faces or plane_faces(footprint, planes)
    fp = poly(footprint)
    caps = []
    seen = set()
    for i, reg in enumerate(faces):
        for loop in reg.to_polygons():
            n = len(loop)
            for k in range(n):
                a = loop[k]
                b = loop[(k + 1) % n]
                if np.linalg.norm(b - a) < 0.5:
                    continue
                mid = (a + b) / 2
                # interior edge if midpoint is strictly inside footprint
                probe = rect(mid[0] - 0.05, mid[1] - 0.05, mid[0] + 0.05, mid[1] + 0.05)
                if (fp ^ probe).area() < 0.0099:
                    continue
                key = tuple(np.round(np.concatenate([np.minimum(a, b), np.maximum(a, b)]), 1))
                if key in seen:
                    continue
                seen.add(key)
                za = planes[i].z(*a)
                zb = planes[i].z(*b)
                caps.append(segment_bar([a[0], a[1], za + lift], [b[0], b[1], zb + lift],
                                        width, height))
    return union(caps)

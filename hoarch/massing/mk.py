"""Plain massing models (no ornament) for layout review: volumes, roofs, openings."""
import json
import math

import numpy as np
from manifold3d import Manifold as M, CrossSection as CS

from hoarch.core import poly, slab, union

GREYS = {
    "wall": ["#cfccc6", 0.85, 0.0],
    "upper": ["#c2bfb9", 0.85, 0.0],
    "roof": ["#86898e", 0.8, 0.0],
    "base": ["#a39e95", 0.9, 0.0],
    "trim": ["#ebe9e4", 0.8, 0.0],
    "chimney": ["#ada59c", 0.9, 0.0],
    "deck": ["#b9b4ab", 0.9, 0.0],
    "glass": ["#1d2329", 0.15, 0.0],
    "shadow": ["#2a2a2a", 1.0, 0.0],
}


class Model:
    def __init__(self):
        self.parts = {}

    def add(self, mat, m):
        if m is not None and not m.is_empty():
            self.parts.setdefault(mat, []).append(m)

    def solid(self, mat):
        return union(self.parts.get(mat, []))

    def save(self, npz, palette):
        out = {}
        for mat, ms in self.parts.items():
            mesh = union(ms).to_mesh()
            out[mat + "__v"] = np.asarray(mesh.vert_properties)[:, :3].astype(np.float32)
            out[mat + "__f"] = np.asarray(mesh.tri_verts).astype(np.int32)
        np.savez_compressed(npz, **out)
        json.dump({"materials": {k: v for k, v in GREYS.items() if k in self.parts},
                   "views": {"plan": [0, 89.5, 50, 1.0, [0, 0, 0]], "left": [-62, 14, 70, 0.95, [0, 0, 0]]}},
                  open(palette, "w"), indent=1)
        lo = np.min([out[k].min(0) for k in out if k.endswith("__v")], axis=0)
        hi = np.max([out[k].max(0) for k in out if k.endswith("__v")], axis=0)
        return lo, hi


def bx(x0, y0, z0, x1, y1, z1):
    return M.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])


def below(solid, q, t, z0, s):
    """Keep the part of ``solid`` under the plane z = z0 + s * t.(p - q) (t: unit up-slope
    direction in plan)."""
    t = np.asarray(t, float)
    t = t / np.linalg.norm(t)
    n = np.array([-s * t[0], -s * t[1], 1.0])
    n /= np.linalg.norm(n)
    p = np.array([q[0], q[1], z0], float)
    return solid.trim_by_plane(list(-n), float(-n @ p))


def roof(footprint, zlo, planes, zhi=400.0):
    """Volume over a plan polygon up to a roof made of plane groups. Each group is a list of
    planes (q, t, z0, s) cut in turn; the groups are unioned (so a group's flatter 'kick'
    plane gives a flared eave)."""
    base = slab(poly(footprint), zlo, zhi)
    out = []
    for grp in planes:
        s = base
        for q, t, z0, sl in grp:
            s = below(s, q, t, z0, sl)
        out.append(s)
    return union(out)


def cone(c, r, z0, h, seg=64, r_top=0.0):
    return M.cylinder(h, r, r_top, seg).translate([c[0], c[1], z0])


def bellcone(c, r_eave, z0, h, flare=0.22, seg=64):
    """A conical roof that flares out at the eave (concave, bell-cast)."""
    prof = [(0.0, z0 - 1.2)]
    for i in range(0, 21):
        k = i / 20
        r = r_eave * (1 - k) ** (1 + flare * 3)
        prof.append((r if i < 20 else 0.0, z0 + h * k))
    prof = [(0.0, z0 - 1.2), (r_eave, z0 - 1.2)] + prof[1:]
    return M.revolve(CS([prof]), seg).translate([c[0], c[1], 0])


def ring(c, r, z0, z1, seg=64):
    return M.cylinder(z1 - z0, r, r, seg).translate([c[0], c[1], z0])


def pointed(x0, x1, z0, spring, k=1.0, seg=16):
    """Pointed (two-centred) arch outline in (x, z), base at z0, springing at ``spring``."""
    w = x1 - x0
    R = w * k
    pts = [(x0, z0), (x1, z0), (x1, spring)]
    c1 = x1 - R
    a1 = math.acos(min(1.0, (w / 2 + (R - w)) / R)) if R > w / 2 else 0
    ang_end = math.acos((x0 + w / 2 - c1) / R)
    for i in range(1, seg + 1):
        a = ang_end * i / seg
        pts.append((c1 + R * math.cos(a), spring + R * math.sin(a)))
    c0 = x0 + R
    for i in range(seg - 1, -1, -1):
        a = ang_end * i / seg
        pts.append((c0 - R * math.cos(a), spring + R * math.sin(a)))
    return pts


def round_head(x0, x1, z0, spring, seg=20):
    w = x1 - x0
    r = w / 2
    pts = [(x0, z0), (x1, z0)]
    for i in range(seg + 1):
        a = math.pi * i / seg
        pts.append((x0 + r + r * math.cos(a), spring + r * math.sin(a)))
    return pts


def xz_panel(outline, y0, y1):
    """Extrude an (x, z) outline across y0..y1."""
    m = M.extrude(CS([outline]), y1 - y0)                 # outline in (x, y'), along z'
    # map (x, y', z') -> (x, y0 + z', y')
    A = [[1, 0, 0, 0], [0, 0, 1, y0], [0, 1, 0, 0]]
    return m.transform(A)


def yz_panel(outline, x0, x1):
    """Extrude a (y, z) outline across x0..x1."""
    m = M.extrude(CS([outline]), x1 - x0)
    A = [[0, 0, 1, x0], [1, 0, 0, 0], [0, 1, 0, 0]]
    return m.transform(A)


def win_xz(x0, x1, z0, z1, y, out=-1, d=0.4, head=None):
    """A dark window pane on a wall face at y (the face looks toward -y if out=-1)."""
    if head == "round":
        ol = round_head(x0, x1, z0, z1 - (x1 - x0) / 2)
    elif head == "pointed":
        ol = pointed(x0, x1, z0, z1 - (x1 - x0) * 0.8)
    else:
        ol = [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]
    ya, yb = (y - d, y + 0.3) if out < 0 else (y - 0.3, y + d)
    return xz_panel(ol, ya, yb)


def win_yz(y0, y1, z0, z1, x, out=1, d=0.4, head=None):
    if head == "round":
        ol = round_head(y0, y1, z0, z1 - (y1 - y0) / 2)
    elif head == "pointed":
        ol = pointed(y0, y1, z0, z1 - (y1 - y0) * 0.8)
    else:
        ol = [(y0, z0), (y1, z0), (y1, z1), (y0, z1)]
    xa, xb = (x - 0.3, x + d) if out > 0 else (x - d, x + 0.3)
    return yz_panel(ol, xa, xb)


def win_round(c, r, a_deg, w, z0, z1, d=0.4):
    """A window on a round tower of radius r at azimuth a (deg, 0 = +x, -90 = front)."""
    a = math.radians(a_deg)
    half = w / 2 / r
    ring_ = M.cylinder(z1 - z0, r + d, r + d, 96).translate([c[0], c[1], z0]) - \
        M.cylinder(z1 - z0 + 2, r - 0.3, r - 0.3, 96).translate([c[0], c[1], z0 - 1])
    wedge = poly([(c[0], c[1]), (c[0] + 3 * r * math.cos(a - half), c[1] + 3 * r * math.sin(a - half)),
                  (c[0] + 3 * r * math.cos(a + half), c[1] + 3 * r * math.sin(a + half))])
    return ring_ ^ slab(wedge, z0 - 1, z1 + 1)


def skin_roof(fp, groups, th=2.6, zlo=0.0):
    """A roof skin ``th`` thick over a plan polygon (see roof()); the inner volume runs past
    the outline so the gable ends stay open (the walls close them)."""
    P = np.asarray(fp, float)
    c = P.mean(0)
    big = [tuple(p + np.sign(p - c) * 3.0) for p in P]

    def low(pl):
        q, t, z0, s = pl
        return q, t, z0 - th * math.sqrt(1 + s * s), s
    return roof(fp, zlo, groups) - roof(big, zlo - 5.0, [[low(p) for p in g] for g in groups])


def plane_z(pl, p):
    q, t, z0, s = pl
    t = np.asarray(t, float) / np.linalg.norm(t)
    return z0 + s * ((p[..., 0] - q[0]) * t[0] + (p[..., 1] - q[1]) * t[1])


def eyebrow(pl, c, e, W, H, L, glass=True):
    """An eyebrow dormer rolling out of roof plane ``pl``: front centre ``c`` (plan), ``e`` the
    unit eave direction, up-slope along the plane's t. Returns (hump, window)."""
    q, t, z0, s = pl
    t = np.asarray(t, float) / np.linalg.norm(t)
    e = np.asarray(e, float) / np.linalg.norm(e)
    c = np.asarray(c, float)

    def wave(u):
        k = np.clip(u / W, -1, 1)
        return np.cos(k * math.pi / 2) ** 2

    def warp(v):
        u, w, zl = v[:, 0], v[:, 1], v[:, 2]
        p = c[None, :] + u[:, None] * e[None, :] + w[:, None] * t[None, :]
        tw = np.clip((w / L - 0.25) / 0.75, 0, 1)
        h = H * wave(u) * np.cos(tw * math.pi / 2) ** 2
        z = plane_z(pl, p) - 3.0 + (3.0 + h) * zl
        return np.c_[p, z]
    hump = bx(-W, 0.0, 0.0, W, L, 1.0).refine(30).warp_batch(warp)

    def wwarp(v):
        u, w, zl = v[:, 0], v[:, 1], v[:, 2]
        p = c[None, :] + u[:, None] * e[None, :] + w[:, None] * t[None, :]
        zb = plane_z(pl, c[None, :])[0] + 1.0
        top = np.maximum(H * wave(u) - 2.4, 0.4)
        return np.c_[p, zb + top * zl]
    win = bx(-0.72 * W, -0.4, 0.0, 0.72 * W, 0.3, 1.0).refine(24).warp_batch(wwarp) if glass else None
    return hump, win


def boulder(c, r, squash=0.55, seed=0):
    rng = np.random.default_rng(seed)
    b = M.sphere(r, 20).scale([1.0 + 0.2 * rng.random(), 0.8 + 0.3 * rng.random(), squash])
    return b.translate([c[0], c[1], 0.0])

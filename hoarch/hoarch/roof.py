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

from .core import (Facade, box, ccw, circle, cs_union, frame, miters, offset, poly, rect, scallop_rows, slab,
                   sweep_ring, union)
from .ornament import chamfer_box, console, dentils, lozenge, side_profile, stroke


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
        if shape == "tile":
            # barrel tiles: a wide rib per row; each course is thickest at its lower end and
            # thins up the slope, so the next course's butt laps over it (no gap to fuse)
            b = loc.bounds()
            clip = loc.offset(-0.3, JoinType.Miter, 4.0)
            cols = range(int(np.floor(b[0] / seam_pitch)), int(np.ceil(b[2] / seam_pitch)) + 1)
            courses = []
            for j in range(int(np.floor(b[1] / pitch)) - 1, int(np.ceil(b[3] / pitch)) + 1):
                cs = cs_union([rect(k * seam_pitch - seam_pitch * 0.32, j * pitch, k * seam_pitch + seam_pitch * 0.32,
                                    (j + 1) * pitch + 0.01) for k in cols]) ^ clip
                if cs.is_empty():
                    continue

                def taper(P, v0=j * pitch):
                    P = np.array(P)
                    P[:, 2] *= 1 - 0.55 * np.clip((P[:, 1] - v0) / pitch, 0, 1)
                    return P
                courses.append(M.extrude(cs, d).warp_batch(taper))
            tex = union(courses)
        elif shape == "barrel":           # Spanish barrel tiles: half-round rows up the slope, a lap at every course (the Alvarado)
            b = loc.bounds()
            clip = loc.offset(-0.3, JoinType.Miter, 4.0)
            r = seam_pitch * 0.36
            L_ = b[3] - b[1] + 4.0
            rows = [M.cylinder(L_, r, r, 20).rotate([-90, 0, 0]).translate([k * seam_pitch, b[1] - 2.0, 0.0])
                    for k in range(int(np.floor(b[0] / seam_pitch)) - 1, int(np.ceil(b[2] / seam_pitch)) + 2)]
            laps = [M.cube([b[2] - b[0] + 20, 0.3, 2 * r + 2]).translate([b[0] - 10, j * pitch, 0.35 * r])
                    for j in range(int(np.floor(b[1] / pitch)) - 1, int(np.ceil(b[3] / pitch)) + 2)]
            tex = (union(rows) - union(laps)) ^ M.extrude(clip, r + 1.0)
        elif shape == "flatseam":         # flat-seam tin: small plates in staggered courses, their folded seams raised (the Brenton)
            b = loc.bounds()
            seams = []
            for j in range(int(np.floor(b[1] / pitch)) - 1, int(np.ceil(b[3] / pitch)) + 1):
                v = j * pitch
                seams.append(rect(b[0] - 1, v - seam_w / 2, b[2] + 1, v + seam_w / 2))
                off = (j % 2) * seam_pitch / 2
                for k in range(int(np.floor(b[0] / seam_pitch)) - 1, int(np.ceil(b[2] / seam_pitch)) + 2):
                    u = k * seam_pitch + off
                    seams.append(rect(u - seam_w / 2, v, u + seam_w / 2, v + pitch))
            tex = M.extrude(cs_union(seams) ^ loc.offset(-0.3, JoinType.Miter, 4.0), d)
        elif shape == "ribtile":          # flat interlocking clay tiles, each with a raised rib along one edge (the Wrightwood)
            b = loc.bounds()
            clip = loc.offset(-0.3, JoinType.Miter, 4.0)
            tiles, ribs = [], []
            for j in range(int(np.floor(b[1] / pitch)) - 1, int(np.ceil(b[3] / pitch)) + 1):
                off = (j % 2) * seam_pitch / 2
                for k in range(int(np.floor(b[0] / seam_pitch)) - 1, int(np.ceil(b[2] / seam_pitch)) + 2):
                    u = k * seam_pitch + off
                    tiles.append(rect(u + 0.25, j * pitch, u + seam_pitch - 0.25, (j + 1) * pitch - 0.25))
                    ribs.append(rect(u + 0.25, j * pitch, u + 0.85, (j + 1) * pitch - 0.25))
            tex = M.extrude(cs_union(tiles) ^ clip, d) + M.extrude(cs_union(ribs) ^ clip, d + 0.25)
        elif shape == "batten":           # batten-seam tin: square battens under wider capped strips (the Ridgely)
            b = loc.bounds()
            clip = loc.offset(-0.3, JoinType.Miter, 4.0)
            ks = range(int(np.floor(b[0] / seam_pitch)), int(np.ceil(b[2] / seam_pitch)) + 1)
            base_ = cs_union([rect(k * seam_pitch - 0.45, b[1] - 1, k * seam_pitch + 0.45, b[3] + 1) for k in ks])
            cap_ = cs_union([rect(k * seam_pitch - 0.25, b[1] - 1, k * seam_pitch + 0.25, b[3] + 1) for k in ks])
            tex = M.extrude(base_ ^ clip, d * 0.6) + M.extrude(cap_ ^ clip, d)
        elif shape == "crimp":            # 5V crimp: a pair of narrow ribs per panel
            b = loc.bounds()
            ribs = []
            for k in range(int(np.floor(b[0] / seam_pitch)), int(np.ceil(b[2] / seam_pitch)) + 1):
                u = k * seam_pitch
                ribs += [rect(u - 0.85, b[1] - 1, u - 0.35, b[3] + 1), rect(u + 0.35, b[1] - 1, u + 0.85, b[3] + 1)]
            tex = M.extrude(cs_union(ribs) ^ loc.offset(-0.3, JoinType.Miter, 4.0), d)
        elif shape == "seam":
            b = loc.bounds()
            n0 = int(np.floor(b[0] / seam_pitch))
            ribs = [rect(k * seam_pitch - seam_w / 2, b[1] - 1, k * seam_pitch + seam_w / 2, b[3] + 1)
                    for k in range(n0, int(np.ceil(b[2] / seam_pitch)) + 1)]
            tex = M.extrude(cs_union(ribs) ^ loc.offset(-0.3, JoinType.Miter, 4.0), d)
        elif shape == "graduated":        # Georgian graduated slate: square butts, the courses shortening up the roof
            b = loc.bounds()
            bands, v = [], b[1]
            span = max(1e-6, b[3] - b[1])
            while v < b[3]:
                f_ = min(1.0, (v - b[1]) / span)          # 0 at the eave, 1 at the top of the face
                p_ = round(pitch * (1.0 - 0.35 * f_) / 0.05) * 0.05
                band = loc ^ rect(b[0] - 1, v, b[2] + 1, v + 3 * p_)
                if not band.is_empty():
                    bands.append(scallop_rows(band, p_, wtab * (1.0 - 0.25 * f_), d=d, shape="square", datum=v))
                v += 3 * p_
            tex = union(bands) if bands else M()
        elif shape == "stoneslate":       # Cotswold stone slates: random widths, courses diminishing up the roof,
            b = loc.bounds()              # rough butts, each slate one of three thicknesses (the Ashcombe)
            span = max(1e-6, b[3] - b[1])
            rng = np.random.default_rng(int(abs(b[0]) * 7 + abs(b[2]) * 3 + i * 13) % 997)
            layers = {}
            v = b[1]
            while v < b[3]:
                f_ = min(1.0, (v - b[1]) / span)
                p_ = round(pitch * (1.0 - 0.4 * f_) / 0.05) * 0.05
                u = b[0] - rng.uniform(0.0, 3.0)
                while u < b[2]:
                    wd = rng.uniform(1.8, 3.6) * (1.0 - 0.3 * f_)
                    tl = rng.uniform(-0.16, 0.16)
                    layers.setdefault(int(rng.integers(0, 3)), []).append(
                        poly([(u + 0.12, v + 0.2 + tl), (u + wd - 0.12, v + 0.2 - tl), (u + wd - 0.12, v + p_), (u + 0.12, v + p_)]))
                    u += wd
                v += p_
            clip = loc.offset(-0.3, JoinType.Miter, 4.0)
            tex = union([M.extrude(cs_union(cs_) ^ clip, d + 0.07 * k) for k, cs_ in layers.items()])
        elif shape == "pancover":         # mission pan-and-cover tile: flat pans between round covers, each cover
            b = loc.bounds()              # course lapped with a thick nose, laid by hand a little out of line (the Capistrano)
            clip = loc.offset(-0.3, JoinType.Miter, 4.0)
            rng = np.random.default_rng(int(abs(b[0]) * 5 + abs(b[2]) * 11 + i * 7) % 997)
            pans, covers, crowns, noses = [], [], [], []
            for k in range(int(np.floor(b[0] / seam_pitch)) - 1, int(np.ceil(b[2] / seam_pitch)) + 2):
                u = k * seam_pitch
                jit = rng.uniform(-0.12, 0.12)
                pans.append(rect(u + 0.75, b[1] - 1, u + seam_pitch - 0.75, b[3] + 1))
                covers.append(rect(u - 0.6 + jit, b[1] - 1, u + 0.6 + jit, b[3] + 1))
                crowns.append(rect(u - 0.3 + jit, b[1] - 1, u + 0.3 + jit, b[3] + 1))
                for j in range(int(np.floor(b[1] / pitch)) - 1, int(np.ceil(b[3] / pitch)) + 1):
                    v = j * pitch + rng.uniform(-0.25, 0.25)
                    noses.append(rect(u - 0.75 + jit, v, u + 0.75 + jit, v + 0.7))
                    pans.append(rect(u + 0.75, v - 0.12, u + seam_pitch - 0.75, v + 0.12))
            pan = cs_union(pans[0::1]) ^ clip
            tex = (M.extrude(pan, d * 0.45) + M.extrude(cs_union(covers) ^ clip, d) + M.extrude(cs_union(crowns) ^ clip, d + 0.15)
                   + M.extrude(cs_union(noses) ^ clip, d + 0.25))
        elif shape == "dutchlap":         # Dutch-lap shingles: each laid slanting so its corner laps the next,
            b = loc.bounds()              # the courses reading as diagonal zigzags, a thick butt on each (the Kittredge)
            clip = loc.offset(-0.3, JoinType.Miter, 4.0)
            sh, butts = [], []
            for j in range(int(np.floor(b[1] / pitch)) - 1, int(np.ceil(b[3] / pitch)) + 1):
                v = j * pitch
                off = (j % 2) * wtab / 2
                for k in range(int(np.floor((b[0] - off) / wtab)) - 2, int(np.ceil((b[2] - off) / wtab)) + 2):
                    u = off + k * wtab
                    sl = pitch * 0.35
                    sh.append(poly([(u + 0.12, v), (u + wtab - 0.12, v), (u + wtab - 0.12 + sl, v + pitch - 0.14), (u + 0.12 + sl, v + pitch - 0.14)]))
                    butts.append(poly([(u + 0.12, v), (u + wtab - 0.12, v), (u + wtab - 0.12 + 0.2, v + 0.55), (u + 0.12 + 0.2, v + 0.55)]))
            tex = M.extrude(cs_union(sh) ^ clip, d) + M.extrude(cs_union(butts) ^ clip, d + 0.15)
        elif shape == "tlock":            # T-lock asphalt shingles: each a T, its stem hanging between the bars of
            b = loc.bounds()              # the course below, so the courses lock together (the Pullman)
            clip = loc.offset(-0.3, JoinType.Miter, 4.0)
            ts = []
            for j in range(int(np.floor(b[1] / pitch)) - 1, int(np.ceil(b[3] / pitch)) + 1):
                v = j * pitch
                off = (j % 2) * wtab / 2
                for k in range(int(np.floor((b[0] - off) / wtab)) - 2, int(np.ceil((b[2] - off) / wtab)) + 2):
                    u = off + k * wtab
                    ts.append(rect(u + 0.12, v + pitch * 0.5, u + wtab - 0.12, v + pitch - 0.12))
                    ts.append(rect(u + wtab * 0.3, v, u + wtab * 0.7, v + pitch * 0.5 + 0.01))
            tex = M.extrude(cs_union(ts) ^ clip, d)
        elif shape == "schindel":         # Swiss split shingles (Schindeln): narrow riven shingles of random width in
            b = loc.bounds()              # many close courses, each butt thickened (the Lindenwald)
            clip = loc.offset(-0.3, JoinType.Miter, 4.0)
            rng = np.random.default_rng(int(abs(b[0]) * 3 + abs(b[2]) * 7 + i * 11) % 997)
            sh, butts = [], []
            for j in range(int(np.floor(b[1] / pitch)) - 1, int(np.ceil(b[3] / pitch)) + 1):
                v = j * pitch + rng.uniform(-0.06, 0.06)
                u = b[0] - rng.uniform(0.0, 1.8)
                while u < b[2] + 1.0:
                    wd = rng.uniform(0.9, 1.8)
                    sh.append(rect(u + 0.08, v, u + wd - 0.08, v + pitch - 0.1))
                    butts.append(rect(u + 0.08, v, u + wd - 0.08, v + 0.4))
                    u += wd
            tex = M.extrude(cs_union(sh) ^ clip, d) + M.extrude(cs_union(butts) ^ clip, d + 0.12)
        elif shape == "hexslate":         # hexagonal slates laid point-down, each course's points between those of
            b = loc.bounds()              # the course below, reading as a honeycomb (the Stickley)
            clip = loc.offset(-0.3, JoinType.Miter, 4.0)
            hx = []
            for j in range(int(np.floor(b[1] / pitch)) - 1, int(np.ceil(b[3] / pitch)) + 1):
                v = j * pitch
                off = (j % 2) * wtab / 2
                for k in range(int(np.floor((b[0] - off) / wtab)) - 2, int(np.ceil((b[2] - off) / wtab)) + 2):
                    u = off + k * wtab
                    c = u + wtab / 2
                    hx.append(poly([(c, v), (u + wtab - 0.15, v + pitch * 0.4), (u + wtab - 0.15, v + pitch * 1.1),
                                    (u + 0.15, v + pitch * 1.1), (u + 0.15, v + pitch * 0.4)]))
            lay = {0: [], 1: []}
            for n_, h_ in enumerate(hx):
                lay[n_ % 2].append(h_)
            tex = M.extrude(cs_union(hx) ^ clip, d)
        elif shape == "upboards":         # boards running up the slope, a groove between each pair, the butts cut
            b = loc.bounds()              # square along the eave (the water tank's cone)
            clip = loc.offset(-0.2, JoinType.Miter, 4.0)
            gr = cs_union([rect(u - 0.12, b[1] - 1, u + 0.12, b[3] + 1) for u in np.arange(b[0] + wtab / 2, b[2], wtab)])
            tex = M.extrude(clip - gr, d)
        elif shape == "longshort":        # slates long and short in turn along each course, so the butts step
            b = loc.bounds()              # down and up like a battlement (the Greenfield Bandstand)
            clip = loc.offset(-0.3, JoinType.Miter, 4.0)
            sh = []
            for j in range(int(np.floor(b[1] / pitch)) - 1, int(np.ceil(b[3] / pitch)) + 1):
                v = j * pitch
                for k, u in enumerate(np.arange(b[0] - wtab + (j % 2) * wtab / 2, b[2] + wtab, wtab)):
                    dv = 0.0 if k % 2 else pitch * 0.35
                    sh.append(rect(u + 0.08, v - pitch * 0.35 + dv, u + wtab - 0.08, v + pitch - 0.1))
            tex = M.extrude(cs_union(sh) ^ clip, d)
        elif shape == "tapered":          # slates narrower at the butt than at the head, so a V of shadow opens
            b = loc.bounds()              # between each pair (MX Tower)
            clip = loc.offset(-0.3, JoinType.Miter, 4.0)
            sh = []
            tp = min(0.35, wtab * 0.15)
            for j in range(int(np.floor(b[1] / pitch)) - 1, int(np.ceil(b[3] / pitch)) + 1):
                v = j * pitch
                for u in np.arange(b[0] - wtab + (j % 2) * wtab / 2, b[2] + wtab, wtab):
                    s0, s1 = u + 0.08, u + wtab - 0.08
                    sh.append(poly([(s0 + tp, v), (s1 - tp, v), (s1, v + pitch - 0.1), (s0, v + pitch - 0.1)]))
            tex = M.extrude(cs_union(sh) ^ clip, d)
        elif shape == "roundcorner":      # sawn shingles with their two lower corners rounded off (not a scallop: the
            b = loc.bounds()              # butt stays straight between them), broken joints (the Thorne Livery)
            clip = loc.offset(-0.3, JoinType.Miter, 4.0)
            sh = []
            rr = min(0.45, wtab * 0.2, pitch * 0.3)
            for j in range(int(np.floor(b[1] / pitch)) - 1, int(np.ceil(b[3] / pitch)) + 1):
                v = j * pitch
                for u in np.arange(b[0] - wtab + (j % 2) * wtab / 2, b[2] + wtab, wtab):
                    s0, s1 = u + 0.08, u + wtab - 0.08
                    sh.append(cs_union([rect(s0, v + rr, s1, v + pitch - 0.1), rect(s0 + rr, v, s1 - rr, v + rr + 0.01),
                                        circle((s0 + rr, v + rr), rr, 10), circle((s1 - rr, v + rr), rr, 10)]))
            tex = M.extrude(cs_union(sh) ^ clip, d)
        elif shape == "bevelbutt":        # sawn shingles of random width whose butts are bevelled back, a sharp
            b = loc.bounds()              # shadow line under each course (Pleasant Valley School)
            clip = loc.offset(-0.3, JoinType.Miter, 4.0)
            rng = np.random.default_rng(int(abs(b[0]) * 5 + abs(b[2]) * 3 + i * 13) % 991)
            sh, butt = [], []
            for j in range(int(np.floor(b[1] / pitch)) - 1, int(np.ceil(b[3] / pitch)) + 1):
                v = j * pitch
                u = b[0] - rng.uniform(0.0, wtab)
                while u < b[2] + 1.0:
                    wd = rng.uniform(wtab * 0.6, wtab * 1.4)
                    sh.append(rect(u + 0.08, v + 0.35, u + wd - 0.08, v + pitch - 0.1))
                    butt.append(rect(u + 0.08, v, u + wd - 0.08, v + 0.36))
                    u += wd
            tex = M.extrude(cs_union(sh) ^ clip, d) + M.extrude(cs_union(butt) ^ clip, d * 0.55)
        elif shape == "rolllap":          # rolled roofing: wide strips lapped up the slope, a row of nail heads along
            b = loc.bounds()              # each lap (the Lakeshore Freight House)
            clip = loc.offset(-0.3, JoinType.Miter, 4.0)
            laps, nails = [], []
            for j in range(int(np.floor(b[1] / pitch)) - 1, int(np.ceil(b[3] / pitch)) + 1):
                v = j * pitch
                laps.append(rect(b[0] - 1, v, b[2] + 1, v + pitch - 0.15))
                nails += [circle((u, v + 0.35), 0.18, 8) for u in np.arange(b[0] + (j % 2) * 0.9, b[2], 1.8)]
            tex = M.extrude(cs_union(laps) ^ clip, d) + M.extrude(cs_union(nails) ^ clip, d + 0.12)
        elif shape == "embossed":         # pressed-tin shingles: square plates in broken courses, each with a raised
            b = loc.bounds()              # boss at its middle (Engine No. 3)
            clip = loc.offset(-0.3, JoinType.Miter, 4.0)
            sh, boss = [], []
            for j in range(int(np.floor(b[1] / pitch)) - 1, int(np.ceil(b[3] / pitch)) + 1):
                v = j * pitch
                for u in np.arange(b[0] - wtab + (j % 2) * wtab / 2, b[2] + wtab, wtab):
                    sh.append(rect(u + 0.1, v, u + wtab - 0.1, v + pitch - 0.12))
                    boss.append(circle((u + wtab / 2, v + pitch * 0.45), min(0.45, pitch * 0.22), 10))
            tex = M.extrude(cs_union(sh) ^ clip, d) + M.extrude(cs_union(boss) ^ clip.offset(-0.3, JoinType.Miter, 4.0), d + 0.15)
        elif shape == "clipcorner":       # slates each with one lower corner clipped, left and right in turn along
            b = loc.bounds()              # the course, so the butts read as a sawtooth (Harmon Town Hall)
            clip = loc.offset(-0.3, JoinType.Miter, 4.0)
            sh = []
            c = min(0.6, pitch * 0.4)
            for j in range(int(np.floor(b[1] / pitch)) - 1, int(np.ceil(b[3] / pitch)) + 1):
                v = j * pitch
                for k, u in enumerate(np.arange(b[0] - wtab + (j % 2) * wtab / 2, b[2] + wtab, wtab)):
                    s0, s1 = u + 0.08, u + wtab - 0.08
                    if k % 2:
                        sh.append(poly([(s0, v), (s1 - c, v), (s1, v + c), (s1, v + pitch - 0.1), (s0, v + pitch - 0.1)]))
                    else:
                        sh.append(poly([(s0, v + c), (s0 + c, v), (s1, v), (s1, v + pitch - 0.1), (s0, v + pitch - 0.1)]))
            tex = M.extrude(cs_union(sh) ^ clip, d)
        elif shape == "zigband":          # plain slates in broken-joint courses, every fifth course pointed at its
            b = loc.bounds()              # butt so the band reads as a zigzag (St. Brendan's)
            clip = loc.offset(-0.3, JoinType.Miter, 4.0)
            sh = []
            c = min(0.7, pitch * 0.45)
            for j in range(int(np.floor(b[1] / pitch)) - 1, int(np.ceil(b[3] / pitch)) + 1):
                v = j * pitch
                for u in np.arange(b[0] - wtab + (j % 2) * wtab / 2, b[2] + wtab, wtab):
                    s0, s1 = u + 0.08, u + wtab - 0.08
                    if j % 5 == 0:
                        sh.append(poly([(s0, v + c), ((s0 + s1) / 2, v), (s1, v + c), (s1, v + pitch - 0.1), (s0, v + pitch - 0.1)]))
                    else:
                        sh.append(rect(s0, v, s1, v + pitch - 0.1))
            tex = M.extrude(cs_union(sh) ^ clip, d)
        elif shape == "corrugated":       # corrugated iron: round-topped ribs down the slope every 1.2 mm, a
            b = loc.bounds()              # heavier side lap every ``wtab`` and an end lap every ``pitch``
            clip = loc.offset(-0.3, JoinType.Miter, 4.0)      # up the roof (the Blackwater Coaling Tower)
            ribs, side, laps = [], [], []
            for k, u in enumerate(np.arange(b[0] + 0.6, b[2], 1.2)):
                (side if k % max(1, int(round(wtab / 1.2))) == 0 else ribs).append(rect(u - 0.27, b[1] - 1, u + 0.27, b[3] + 1))
            for j in range(int(np.floor(b[1] / pitch)), int(np.ceil(b[3] / pitch)) + 1):
                laps.append(rect(b[0] - 1, j * pitch - 0.25, b[2] + 1, j * pitch + 0.25))
            tex = (M.extrude(cs_union(ribs) ^ clip, d) + M.extrude(cs_union(side) ^ clip, d + 0.12) +
                   M.extrude(cs_union(laps) ^ clip, d * 0.45))
        elif shape == "diamondtin":       # pressed-tin diamonds: square shingles set point-down in courses,
            b = loc.bounds()              # each with a raised rib down its middle (the Crossing Shanty)
            clip = loc.offset(-0.3, JoinType.Miter, 4.0)
            sh, rib = [], []
            for j in range(int(np.floor(b[1] / pitch)) - 1, int(np.ceil(b[3] / pitch)) + 2):
                v = j * pitch
                for u in np.arange(b[0] - wtab + (j % 2) * wtab / 2, b[2] + wtab, wtab):
                    uc = u + wtab / 2
                    sh.append(poly([(uc, v - 0.05), (uc + wtab / 2 - 0.12, v + pitch * 0.9), (uc, v + pitch * 1.8), (uc - wtab / 2 + 0.12, v + pitch * 0.9)]))
                    rib.append(rect(uc - 0.2, v + 0.3, uc + 0.2, v + pitch * 1.5))
            tex = M.extrude(cs_union(sh) ^ clip, d) + M.extrude(cs_union(rib) ^ clip, d + 0.15)
        elif shape == "cleatseam":        # tin in long pans between standing ribs, their cross seams cleated
            b = loc.bounds()              # and staggered pan to pan (the Oil House)
            clip = loc.offset(-0.3, JoinType.Miter, 4.0)
            ribs, seams = [], []
            for k, u in enumerate(np.arange(b[0], b[2] + wtab, wtab)):
                ribs.append(rect(u - 0.3, b[1] - 1, u + 0.3, b[3] + 1))
                for v in np.arange(b[1] + (k % 2) * pitch / 2, b[3], pitch):
                    seams.append(rect(u + 0.3, v - 0.2, u + wtab - 0.3, v + 0.2))
            tex = M.extrude(cs_union(ribs) ^ clip, d + 0.15) + M.extrude(cs_union(seams) ^ clip, d * 0.5)
        elif shape == "doublecourse":     # double-coursed shingles: every course laid over an under-course
            b = loc.bounds()              # whose butt shows a hair below it (Section House No. 4)
            clip = loc.offset(-0.3, JoinType.Miter, 4.0)
            sh, under = [], []
            for j in range(int(np.floor(b[1] / pitch)) - 1, int(np.ceil(b[3] / pitch)) + 1):
                v = j * pitch
                for u in np.arange(b[0] - wtab + (j % 2) * wtab / 2, b[2] + wtab, wtab):
                    sh.append(rect(u + 0.08, v + 0.45, u + wtab - 0.08, v + pitch - 0.1))
                under.append(rect(b[0] - 1, v, b[2] + 1, v + 0.5))
            tex = M.extrude(cs_union(sh) ^ clip, d) + M.extrude(cs_union(under) ^ clip, d * 0.55)
        elif shape == "beadbutt":         # sawn shingles in broken joint, a half-round bead nailed along every
            b = loc.bounds()              # butt line (the Blackwater Yard Office)
            clip = loc.offset(-0.3, JoinType.Miter, 4.0)
            sh, bead = [], []
            for j in range(int(np.floor(b[1] / pitch)) - 1, int(np.ceil(b[3] / pitch)) + 1):
                v = j * pitch
                for u in np.arange(b[0] - wtab + (j % 2) * wtab / 2, b[2] + wtab, wtab):
                    sh.append(rect(u + 0.08, v, u + wtab - 0.08, v + pitch - 0.1))
                bead.append(rect(b[0] - 1, v + 0.05, b[2] + 1, v + 0.5))
            tex = M.extrude(cs_union(sh) ^ clip, d) + M.extrude(cs_union(bead) ^ clip, d + 0.18)
        elif shape == "randomslate":      # rough slates of random width, each butt set a little higher or lower
            b = loc.bounds()              # than its neighbours (the Blackwater Engine House)
            clip = loc.offset(-0.3, JoinType.Miter, 4.0)
            rng = np.random.default_rng(7)
            sh = []
            for j in range(int(np.floor(b[1] / pitch)) - 1, int(np.ceil(b[3] / pitch)) + 1):
                v = j * pitch
                u = b[0] - wtab * rng.uniform(0.2, 1.0)
                while u < b[2] + wtab:
                    wd = wtab * rng.uniform(0.65, 1.35)
                    dv = rng.uniform(-0.3, 0.3)
                    sh.append(rect(u + 0.1, v + dv, u + wd - 0.1, v + pitch - 0.12))
                    u += wd
            tex = M.extrude(cs_union(sh) ^ clip, d)
        elif shape == "tarbatten":        # tar paper in wide strips lapped up the roof, held by wood battens
            b = loc.bounds()              # running down the slope every ``wtab`` (the Blackwater Sand House)
            clip = loc.offset(-0.3, JoinType.Miter, 4.0)
            laps = [rect(b[0] - 1, j * pitch, b[2] + 1, j * pitch + pitch - 0.3)
                    for j in range(int(np.floor(b[1] / pitch)) - 1, int(np.ceil(b[3] / pitch)) + 1)]
            bat = [rect(u - 0.35, b[1] - 1, u + 0.35, b[3] + 1) for u in np.arange(b[0] + wtab / 2, b[2], wtab)]
            tex = M.extrude(cs_union(laps) ^ clip, d * 0.5) + M.extrude(cs_union(bat) ^ clip, d + 0.2)
        elif shape == "octabutt":         # sawn wood shingles in broken-joint courses, every other course's butts
            b = loc.bounds()              # clipped at both corners (octagon butts) (the Millbrook)
            clip = loc.offset(-0.3, JoinType.Miter, 4.0)
            sh = []
            c = min(0.45, pitch * 0.3)
            for j in range(int(np.floor(b[1] / pitch)) - 1, int(np.ceil(b[3] / pitch)) + 1):
                v = j * pitch
                for u in np.arange(b[0] - wtab + (j % 2) * wtab / 2, b[2] + wtab, wtab):
                    s0, s1 = u + 0.08, u + wtab - 0.08
                    if j % 2:
                        sh.append(poly([(s0, v + c), (s0 + c, v), (s1 - c, v), (s1, v + c), (s1, v + pitch - 0.1), (s0, v + pitch - 0.1)]))
                    else:
                        sh.append(rect(s0, v, s1, v + pitch - 0.1))
            tex = M.extrude(cs_union(sh) ^ clip, d)
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


def crest_fence(L, h=2.4, pitch=1.6, bar=0.5, t=0.6, style="arch"):
    """One straight run of cresting in its own frame: u = 0..L along, v up, centred across.

    A bottom rail, spikes of two heights, and a middle rail carried on little pointed
    arches that spring from the spikes at 45 degrees, so the fence prints upright with no
    bridge anchored on a spike (PrusaSlicer flags those as loose extrusions)."""
    if callable(style):                 # a building's own fence: style(L, h) -> its (u, v) outline
        return M.extrude(style(L, h), t).translate([0, 0, -t / 2])
    k = max(1, int(L / pitch))

    def zq(v):                          # printed upright: every rail and tip on the 0.2 mm grid
        return round(v / 0.2) * 0.2
    vm = zq(h * 0.55)
    cells = [rect(0, 0, L, 0.6), rect(0, vm, L, vm + 0.4)]
    if style == "fleur":
        # bars with fleur-de-lis heads and a ring between each pair under the rail (prints flat)
        top = zq(h)
        for j in range(k + 1):
            u = L * j / k
            cells.append(rect(u - bar / 2, 0, u + bar / 2, top - 1.4))
            cells.append(poly([(u - 0.35, top - 1.5), (u + 0.35, top - 1.5), (u + 0.35, top - 0.6), (u, top), (u - 0.35, top - 0.6)]))
            for sg in (-1, 1):
                cells.append(stroke([(u, top - 1.6), (u + sg * 0.75, top - 1.2), (u + sg * 0.8, top - 0.6)], 0.45))
            if j < k:
                rc = (u + L / k / 2, (0.6 + vm) / 2)
                rr = (vm - 0.6) / 2 + 0.05
                cells.append(circle(rc, rr, 20) - circle(rc, max(rr - 0.45, 0.2), 16))
        return M.extrude(cs_union(cells) ^ rect(0, 0, L, h + 1), t).translate([0, 0, -t / 2])
    if style == "spear":
        # spear-headed bars of two heights and a ball on the rail between them (prints flat)
        for j in range(k + 1):
            u = L * j / k
            top = zq(h * (1.0 if j % 2 == 0 else 0.8))
            cells.append(rect(u - bar / 2, 0, u + bar / 2, top - 0.6))
            cells.append(poly([(u, top - 1.2), (u + 0.5, top - 0.6), (u, top), (u - 0.5, top - 0.6)]))
            if j < k:
                cells.append(circle((u + L / k / 2, vm + 0.6), 0.4, 16))
        return M.extrude(cs_union(cells) ^ rect(0, 0, L, h + 1), t).translate([0, 0, -t / 2])
    for j in range(k + 1):
        u = L * j / k
        cells.append(rect(u - bar / 2, 0, u + bar / 2, zq(h * (1.0 if j % 2 == 0 else 0.75))))
        if j < k:
            uL, uR = u + bar / 2, u + L / k - bar / 2
            g = min((uR - uL) / 2, vm - 0.6)
            cells.append(poly([(uL, vm - g), ((uL + uR) / 2, vm), (uR, vm - g), (uR, vm + 0.01), (uL, vm + 0.01)]))
    return M.extrude(cs_union(cells) ^ rect(0, 0, L, h + 1), t).translate([0, 0, -t / 2])


def cresting(path, z0, h=2.4, pitch=1.6, bar=0.5, t=0.6, d_off=0.0, finials=True, style="arch"):
    """Iron roof cresting along a closed path: "arch" (spikes carrying a rail on pointed
    arches, prints upright), "spear" (spear-headed bars with balls on the rail, for strips
    that print flat) or "fleur" (fleur-de-lis bars with rings under the rail, flat strips),
    or a building's own fence(L, h) -> (u, v) outline, extruded ``t`` thick."""
    P, Mi = _edges(path)
    out = []
    n = len(P)
    for i in range(n):
        a, b = P[i] + d_off * Mi[i], P[(i + 1) % n] + d_off * Mi[(i + 1) % n]
        f = Facade(a, b, 0.0)
        fence = crest_fence(f.L, h, pitch, bar, t, style=style)
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


def bell_roof(c, r0, z0, bands, n=16, texture="square", tex_kw=None):
    """A bell (ogee) roof on a round tower: a stack of conical bands on an n-gon, each with
    its own slope, [(rise, slope), ...] from the eave up, so the profile can flare out at its
    foot, bulge and then draw in to a point (the Camellia). Each band carries its own
    courses. Every band narrows upward, so it prints upright on its flat foot. Keep z0 and
    each rise on the 0.2 grid; ``r0`` is the foot's apothem (the planes rise from the edges).
    Returns (solid, texture, apothem at the top, z_top)."""
    from .core import ngon
    ap = r0
    z = z0
    solids, texs = [], []
    for dz, s in bands:
        path = ngon(c, ap, n=n)
        sol, tex = hip_roof([(path, list(range(n)))], z, s, 0.0, texture=texture, tex_kw=tex_kw,
                            zlo=z - (0.2 if solids else 0.0))
        top = z + dz
        solids.append(sol.trim_by_plane([0, 0, -1.0], -top))
        if texture is not None:
            texs.append(tex.trim_by_plane([0, 0, -1.0], -top))
        ap -= dz / s
        z = top
    return union(solids), union(texs), ap, z


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
        clip = f.place(box([e, -1, -t / 2 - 0.01], [f.L - e, 50, t / 2 + 0.01]))
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


def roll_panel(L, W, t=1.2, course=6.0, butt=0.4, lap=0.1):
    """A flat roof panel of rolled roofing, ``L`` along the eave by ``W`` up the slope and
    ``t`` thick, in its own frame (u along the eave, v up the slope, w out of the roof).
    Prints flat on its back. Each course stands ``butt`` proud at its lower edge and thins to
    ``lap`` where the next course laps over it: wide shallow strips, no seams."""
    parts = [box([0, 0, 0], [L, W, t])]
    v = 0.0
    while v < W - 0.01:
        v1 = min(W, v + course)
        parts.append(M.hull_points([(u, vv, t - 0.01) for u in (0.0, L) for vv in (v, v1)] +
                                   [(u, v, t + butt) for u in (0.0, L)] + [(u, v1, t + lap) for u in (0.0, L)]))
        v = v1
    return union(parts)


def walk_rail(L, h=3.2, pitch=1.2, t=0.8, post=1.0):
    """A widow's-walk railing ``L`` long as a flat strip that prints face-up: a bottom rail,
    a hand rail, flat balusters with a waist, and square posts with ball tops at the ends.
    Local: u along, v up, w across (0..t); stand it on its v = 0 edge round a flat roof."""
    cells = [rect(0.0, 0.0, L, 0.6), rect(0.0, h - 0.7, L, h)]
    n = max(1, int((L - 2 * post) / pitch))
    for k in range(n):
        u = post + (L - 2 * post) * (k + 0.5) / n
        cells.append(poly([(u - 0.3, 0.55), (u + 0.3, 0.55), (u + 0.18, h / 2), (u + 0.3, h - 0.65), (u - 0.3, h - 0.65),
                           (u - 0.18, h / 2)]))
    for u in (0.0, L - post):
        cells.append(rect(u, 0.0, u + post, h + 0.6))
        cells.append(circle((u + post / 2, h + 1.1), 0.6, 16))
    return M.extrude(cs_union(cells), t)

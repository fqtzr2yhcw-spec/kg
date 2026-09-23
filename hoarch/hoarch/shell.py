"""One-piece wall shells (printed upright) and stone foundations.

A building is a set of *blocks*: plan polygons (outer wall face) with a base and
top height. The shell is the union of the blocks' walls; siding, corner quoins,
the belt course and the water table are added per exposed facade.
"""
import numpy as np
from manifold3d import JoinType, Manifold as M

from .core import (Facade, ashlar, box, ccw, clapboard, cs_union, offset, poly, rect, slab, sweep_ring, union)


class Block:
    def __init__(self, name, pts, z0, z1):
        self.name, self.pts, self.z0, self.z1 = name, ccw(pts), z0, z1
        self.cs = poly(self.pts)

    def solid(self, grow=0.0, dz0=0.0, dz1=0.0):
        cs = self.cs if grow == 0 else offset(self.cs, grow)
        return slab(cs, self.z0 + dz0, self.z1 + dz1)

    def facades(self):
        P = self.pts
        return [Facade(P[i], P[(i + 1) % len(P)], self.z0) for i in range(len(P))]

    def locate(self, x, y):
        """(edge index, u) of the plan point (x, y) on this block's outline."""
        best = None
        for i, f in enumerate(self.facades()):
            d = np.array([x, y], float) - f.p0
            u = float(d @ f.u)
            off = abs(float(d @ f.n))
            if -0.5 <= u <= f.L + 0.5 and (best is None or off < best[2]):
                best = (i, u, off)
        return best[0], best[1]

    def convex_corners(self, min_turn=0.0):
        """Convex corners whose turning angle (deg) is at least min_turn."""
        P = np.asarray(self.pts)
        out = []
        for i in range(len(P)):
            a, b, c = P[i - 1], P[i], P[(i + 1) % len(P)]
            d0, d1 = b - a, c - b
            cr = d0[0] * d1[1] - d0[1] * d1[0]
            ang = np.degrees(np.arctan2(cr, d0 @ d1))
            out.append(cr > 1e-9 and ang >= min_turn)
        return out


class Opening:
    """An opening on block facade ``edge`` (index into block.pts), centred at
    ``u`` along it, bottom at ``v0`` above the block base; ``spec`` is the insert
    dict from openings.py (cut / landing / insert in local coords)."""

    def __init__(self, block, edge, u, v0, spec, name, kind="window"):
        self.block, self.edge, self.u, self.v0, self.spec = block, edge, u, v0, spec
        self.name, self.kind = name, kind

    @property
    def facade(self):
        return self.block.facades()[self.edge]

    def local_frame(self):
        """3x4 matrix: insert-local (u, v, w) -> world."""
        f = self.facade
        A = f.A.copy()
        A[:, 3] = f.world(self.u, self.v0, 0.0)
        return A

    def cs_on_facade(self, cs):
        return cs.translate((self.u, self.v0))


def _quoin_cs(L_long, L_short, h, gap, v0, v1, leg_u, flip):
    """Alternating quoin blocks on one leg of a corner, (u, v) with the corner at u = 0
    and the leg extending in +u (or -u if flip)."""
    cells = []
    v = v0
    k = 0
    while v < v1 - 0.3:
        L = L_long if k % 2 == 0 else L_short
        top = min(v + h - gap, v1)
        cells.append(rect(0.0, v, L, top))
        v += h
        k += 1
    cs = cs_union(cells)
    if flip:
        cs = cs.mirror((1, 0))
    return cs


def wall_shell(blocks, openings, t=3.0, pitch=1.2, sid_d=0.3, belt=None, quoins=True,
               water_table=True, partitions=(), extra_cut=None, hide_extra=None, corners=None,
               belt_trim=True):
    """Build the one-piece shell with its siding and trim.

    ``belt`` = (v_bottom, v_top) of the belt course above each block's base (None for none).
    ``corners`` = "quoin" (alternating blocks), "board" (plain corner boards) or "none";
    default follows the legacy ``quoins`` flag. ``belt_trim=False`` leaves the belt zone
    bare (storey_shells puts a separate belt ring there)."""
    corners = corners or ("quoin" if quoins else "none")
    quoins = corners == "quoin"
    boards = corners == "board"
    CBW, CBT = 2.4, 0.65
    solids = [b.solid() for b in blocks]
    outer_all = union(solids)
    voids = union([slab(offset(b.cs, -t), b.z0 - 1, b.z1 + 1) for b in blocks])
    shell = outer_all - voids
    for (p0, p1, th, z0, z1) in partitions:
        f = Facade(p0, p1, z0)
        shell = shell + f.place(box([0, 0, -th / 2], [f.L, z1 - z0, th / 2]))
    # openings
    cuts = []
    for o in openings:
        f = o.facade
        cs = o.cs_on_facade(o.spec["cut"])
        cuts.append(f.place(M.extrude(cs, t + 2.0).translate([0, 0, -t - 1.0])))
    if extra_cut is not None:
        cuts.append(extra_cut)
    shell = shell - union(cuts)
    # dressing per facade
    dress = []
    QL, QS, QH, QG, QT = 3.4, 2.3, 2.306, 0.28, 0.75
    for b in blocks:
        facs = b.facades()
        conv = b.convex_corners(min_turn=70.0)
        bead = [c and not q for c, q in zip(b.convex_corners(), conv)]
        H = b.z1 - b.z0
        for i, f in enumerate(facs):
            region = rect(0.0, 0.0, f.L, H)
            # keep-outs: openings' landings, quoin legs, belt, water table
            keep = []
            for o in openings:
                if o.block is b and o.edge == i:
                    keep.append(o.cs_on_facade(o.spec["landing"]))
            cstart, cend = conv[i], conv[(i + 1) % len(facs)]
            qw = (QL if quoins else CBW) + 0.05
            if quoins or boards:
                if cstart:
                    keep.append(rect(-1, -1, qw, H + 1))
                if cend:
                    keep.append(rect(f.L - qw, -1, f.L + 1, H + 1))
            bs, be = bead[i], bead[(i + 1) % len(facs)]
            if bs:
                keep.append(rect(-1, -1, 1.0, H + 1))
                dress.append(f.place(box([0, 1.8, 0], [1.0, H, 0.55])))
            if be:
                keep.append(rect(f.L - 1.0, -1, f.L + 1, H + 1))
                dress.append(f.place(box([f.L - 1.0, 1.8, 0], [f.L, H, 0.55])))
            if belt is not None and H > belt[1]:
                keep.append(rect(-1, belt[0], f.L + 1, belt[1]))
            if water_table:
                keep.append(rect(-1, -1, f.L + 1, 1.8))
            reg = region - cs_union(keep)
            # drop slivers narrower than ~0.9 mm (they print as hairlines and render as cracks)
            reg = reg.offset(-0.45, JoinType.Miter, 4.0).offset(0.45, JoinType.Miter, 4.0) ^ region
            if not reg.is_empty():
                dress.append(f.place(clapboard(reg, pitch=pitch, d=sid_d, dmin=0.05, datum=1.8)))
            # quoins
            if quoins:
                for at_start, on in ((True, cstart), (False, cend)):
                    if not on:
                        continue
                    zones = [(0.0, H)] if belt is None or H <= belt[1] else [(0.0, belt[0]), (belt[1], H)]
                    for (qa, qb) in zones:
                        qa2 = max(qa, 1.8) if water_table and qa == 0 else qa
                        qcs = _quoin_cs(QL, QS, QH, QG, qa2, qb, QL, flip=not at_start)
                        if not at_start:
                            qcs = qcs.translate((f.L, 0))
                        # bevelled blocks: two layers
                        q = M.extrude(qcs, QT * 0.6) + M.extrude(qcs.offset(-0.18, JoinType.Miter), QT * 0.4).translate([0, 0, QT * 0.6])
                        dress.append(f.place(q))
            # plain corner boards (Italianate / Gothic houses), with a small cap under the belt/eave
            if boards:
                zones = [(1.8, H)] if belt is None or H <= belt[1] else [(1.8, belt[0]), (belt[1], H)]
                for at_start, on in ((True, cstart), (False, cend)):
                    if not on:
                        continue
                    u0, u1 = (0.0, CBW) if at_start else (f.L - CBW, f.L)
                    for (qa, qb) in zones:
                        dress.append(f.place(box([u0, qa, 0], [u1, qb, CBT])))
                        dress.append(f.place(box([u0 - (0.2 if not at_start else 0), qb - 0.9, 0],
                                                 [u1 + (0.2 if at_start else 0), qb, CBT + 0.3])))
            # belt course: frieze band + drip cap
            if belt_trim and belt is not None and H > belt[1]:
                e0 = -1.0 if cstart else 0.0
                e1 = f.L + 1.0 if cend else f.L
                band = box([e0, belt[0], 0], [e1, belt[1] - 0.8, 0.9])
                cap = box([e0 - 0.3, belt[1] - 0.8, 0], [e1 + 0.3, belt[1], 1.4])
                dress.append(f.place(band + cap))
            if water_table:
                e0 = -1.2 if cstart else 0.0
                e1 = f.L + 1.2 if cend else f.L
                wt = box([e0, 0, 0], [e1, 1.3, 1.0]) + box([e0 - 0.2, 1.3, 0], [e1 + 0.2, 1.8, 1.2])
                dress.append(f.place(wt))
    dress = union(dress)
    # hide dressing that falls inside another block or into an opening
    hide = union([b.solid(grow=-0.02, dz0=-0.5, dz1=0.5) for b in blocks])
    open_clear = union([o.facade.place(M.extrude(o.cs_on_facade(o.spec["cut"]).offset(0.05, JoinType.Miter),
                                                 6.0).translate([0, 0, -3.0])) for o in openings])
    lands = union([o.facade.place(M.extrude(o.cs_on_facade(o.spec["landing"]), 4.0).translate([0, 0, -0.05]))
                   for o in openings])
    dress = dress - hide - open_clear - lands
    if hide_extra is not None:
        dress = dress - hide_extra
    # dress must not overhang past a shorter block's roof line where it meets a taller one: fine as is
    return shell + dress


def foundation(blocks, z0, z1, t=3.0, proud=0.8, stone_d=0.55, seed=4, openings=(), lip=1.2):
    """Stone foundation ring under all blocks, ``proud`` outside the wall face.

    A locating lip rises ``lip`` above z1 just inside the wall's inner face so the
    shell drops onto it squarely."""
    base = cs_union([b.cs for b in blocks])
    outer = offset(base, proud)
    ring = slab(outer, z0, z1) - slab(offset(base, -t - 1.3), z0 - 1, z1 + 1)
    lip_cs = offset(base, -t - 0.12) - offset(base, -t - 1.3)
    walls = union([slab(offset(b.cs, 0.15) - offset(b.cs, -t - 0.15), z1 - 1, z1 + lip + 1) for b in blocks])
    ring = ring + (slab(lip_cs, z1 - 0.01, z1 + lip) - walls)
    # ashlar on every outer edge
    tex = []
    loops = outer.to_polygons()
    loop = max(loops, key=lambda L: abs(poly(L).area()))
    pts = ccw(loop)
    for i in range(len(pts)):
        f = Facade(pts[i], pts[(i + 1) % len(pts)], z0)
        if f.L < 0.8:
            continue
        reg = rect(0.0, 0.3, f.L, z1 - z0 - 0.3)
        s = ashlar(reg, course=(2.6, 3.9), length=(3.5, 8.5), d=stone_d, seed=seed + i)
        tex.append(f.place(s))
    ring = ring + union(tex)
    # clip stone at corners so neighbours don't stack up outside the miter
    clip = slab(offset(outer, stone_d + 0.2), z0 - 1, z1 + 1)
    ring = ring ^ clip
    cuts = []
    for (f, u, v0, w, h) in openings:
        cuts.append(f.place(box([u - w / 2, v0, -t - 2], [u + w / 2, v0 + h, 3])))
    return ring - union(cuts)


# ------------------------------------------------------------------ storeys
# Italianate string course, printed upright: every outward step has a 45 degree underside,
# heights on the 0.2 mm grid. (d outward from the wall face, z up from the ring bottom.)
BELT_PROF = [(0.0, 0.0), (0.4, 0.4), (0.4, 0.8), (0.8, 1.2), (0.8, 2.8), (1.4, 3.4), (1.4, 3.6),
             (1.8, 4.0), (1.8, 4.4)]
LIP_H, LIP_IN, LIP_W = 1.2, 0.12, 1.3     # locating lip: height, clearance to the wall, reach


def _corbel(base, t, z_top, reach=LIP_W, step=0.2):
    """Inward shelf under a lip: grows 45 degrees from nothing to ``reach`` at z_top."""
    n = int(round(reach / step))
    out = []
    for k in range(n):
        e = min(reach, (k + 1) * step)
        out.append(slab(offset(base, -t + 0.05) - offset(base, -t - e), z_top - reach + k * step,
                        z_top - reach + (k + 1) * step))
    return union(out)


def lip_ring(base, t, z0, h=LIP_H):
    """Locating lip just inside the wall's inner face, standing on z0."""
    return slab(offset(base, -t - LIP_IN) - offset(base, -t - LIP_W), z0 - 0.01, z0 + h)


def lip_keep(base, t, z0, h=LIP_H, inner=LIP_IN, reach=LIP_W, clr=0.15):
    """Keep-out around a locating lip, limited to the building's interior, for cutting the
    partitions of the parts the lip reaches into."""
    cs = (offset(base, -t - inner + clr) - offset(base, -t - reach - clr)) ^ offset(base, -t + 0.02)
    return slab(cs, z0 - clr, z0 + h + clr)


def belt_ring(outline_pts, z0, t=3.0, prof=BELT_PROF, lip=True):
    """Belt course between two storey shells, the full wall thickness plus a moulded band.

    It sits on the lower shell (located by that shell's lip) and carries the lip for the
    upper shell on an inside corbel that starts above the lower lip. Prints upright."""
    h = prof[-1][1]
    ring = sweep_ring(outline_pts, [(-t, z0)] + [(d, z0 + z) for d, z in prof] + [(-t, z0 + h)])
    base = poly(ccw(outline_pts))
    if lip:
        assert h - LIP_W >= LIP_H + 0.2, "belt ring too short for its corbel"
        ring = ring + _corbel(base, t, z0 + h) + lip_ring(base, t, z0 + h)
    return ring


def storey_shells(blocks, openings, z_split, t=3.0, prof=BELT_PROF, clear=(), **kw):
    """One-piece shells per storey with a belt ring between, like the reference's stacks.

    Builds the full shell (siding, trim, openings) with the belt zone bare, then cuts it
    at ``z_split`` and at the top of the belt ring. Blocks that end at or below z_split (a
    one-storey wing) stay whole in the lower shell. The lower shell gets a corbelled
    locating lip for the ring, the ring one for the upper shell. ``clear`` = keep-out
    solids for interior partitions (other parts' lips, see lip_keep).

    Returns dict(lower, ring, upper, ring_h, outline)."""
    h = prof[-1][1]
    zb = min(b.z0 for b in blocks)
    belt = (z_split - zb, z_split - zb + h)
    shell = wall_shell(blocks, openings, t=t, belt=belt, belt_trim=False, **kw)
    upper_blocks = [b for b in blocks if b.z1 > z_split + h + 1.0]
    base = cs_union([b.cs for b in upper_blocks])
    outline = max(base.to_polygons(), key=lambda L: abs(poly(L).area()))
    lower = shell.trim_by_plane([0, 0, -1.0], -z_split)
    lower = lower + _corbel(base, t, z_split) + lip_ring(base, t, z_split)
    upper = shell.trim_by_plane([0, 0, 1.0], z_split + h)
    ring = belt_ring(outline, z_split, t=t, prof=prof)
    upper = upper - lip_keep(base, t, z_split + h)
    for kp in clear:
        upper = upper - kp
        lower = lower - kp
    return dict(lower=lower, ring=ring, upper=upper, ring_h=h, outline=outline)

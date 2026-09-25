"""One-piece wall shells (printed upright) and stone foundations.

A building is a set of *blocks*: plan polygons (outer wall face) with a base and
top height. The shell is the union of the blocks' walls; siding, corner quoins,
the belt course and the water table are added per exposed facade.
"""
import math

import numpy as np
from manifold3d import JoinType, Manifold as M

from .core import (Facade, ashlar, box, ccw, circle, clapboard, cs_union, offset, poly, rect, slab, sweep_ring, union)
from .ornament import chamfer_box, ext


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


def _zones(H, belts, start):
    """Height intervals of a facade of height H between the belt zones (for quoins/boards)."""
    zs, v = [], start
    for b0, b1 in sorted(belts):
        if H <= b1:
            continue
        if b0 > v:
            zs.append((v, b0))
        v = max(v, b1)
    if H > v:
        zs.append((v, H))
    return zs


def wall_shell(blocks, openings, t=3.0, pitch=1.2, sid_d=0.3, belt=None, quoins=True,
               water_table=True, partitions=(), extra_cut=None, hide_extra=None, corners=None,
               belt_trim=True, siding=None, gables=()):
    """Build the one-piece shell with its siding and trim.

    ``belt`` = (v_bottom, v_top) of the belt course above each block's base, a list of such
    zones, or None.
    ``corners`` = "quoin" (long and short blocks), "quoin_even" (equal blocks, tighter
    courses), a corner-board style (see CORNER_BOARDS: board, pilaster, chamfer, stepped,
    capital, panel) or "none"; default follows the legacy ``quoins`` flag. ``belt_trim=False`` leaves the belt zone
    bare (storey_shells puts a separate belt ring there).
    ``siding(f, block, region)`` -> texture in the facade's (u, v) frame (v up from the
    block's base) replaces the default clapboard, e.g. shingles on an upper storey.
    ``gables`` = [(block, edge index, cs)]: a gable wall standing on that facade, cs in the
    facade's (u, v) frame (v up from the block's base). It is part of the shell, takes the
    facade's siding and openings, and is ``t`` thick."""
    corners = corners or ("quoin" if quoins else "none")
    belts = [] if belt is None else ([belt] if isinstance(belt[0], (int, float)) else list(belt))
    quoins = corners in ("quoin", "quoin_even")
    boards = corners in CORNER_BOARDS
    CBW, CBT = 2.4, 0.65
    solids = [b.solid() for b in blocks]
    outer_all = union(solids)
    voids = union([slab(offset(b.cs, -t), b.z0 - 1, b.z1 + 1) for b in blocks])
    shell = outer_all - voids
    gable_cs = {}
    for (gb, gi, gcs) in gables:
        f = gb.facades()[gi]
        shell = shell + f.place(M.extrude(gcs, t).translate([0, 0, -t]))
        gable_cs[(gb.name, gi)] = gcs
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
    QL, QS, QH, QG, QT, QC = 3.6, 2.4, 2.4, 0.4, 0.7, 0.4    # long, short, course, joint, depth, chamfer
    if corners == "quoin_even":                               # equal blocks in tighter courses
        QL, QS, QH, QC = 2.6, 2.6, 2.0, 0.3
    for b in blocks:
        facs = b.facades()
        conv = b.convex_corners(min_turn=70.0)
        # a corner where this block meets another (a wing against the main house) is an
        # inside corner of the whole building: no quoins or corner boards there
        others = [offset(o.cs, 0.2) for o in blocks if o is not b]
        touch = [any(not (o ^ rect(p[0] - 0.01, p[1] - 0.01, p[0] + 0.01, p[1] + 0.01)).is_empty() for o in others)
                 for p in b.pts]
        conv = [c and not tc for c, tc in zip(conv, touch)]
        bead = [c and not q and not tc for c, q, tc in zip(b.convex_corners(), conv, touch)]
        H = b.z1 - b.z0
        for i, f in enumerate(facs):
            region = rect(0.0, 0.0, f.L, H)
            if (b.name, i) in gable_cs:
                region = region + gable_cs[(b.name, i)]
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
            for bl in belts:
                if H > bl[1]:
                    keep.append(rect(-1, bl[0], f.L + 1, bl[1]))
            if water_table:
                keep.append(rect(-1, -1, f.L + 1, 1.8))
            reg = region - cs_union(keep)
            # drop slivers narrower than ~0.9 mm (they print as hairlines and render as cracks)
            reg = reg.offset(-0.45, JoinType.Miter, 4.0).offset(0.45, JoinType.Miter, 4.0) ^ region
            if not reg.is_empty():
                tex = siding(f, b, reg) if siding else clapboard(reg, pitch=pitch, d=sid_d, dmin=0.05, datum=1.8)
                dress.append(f.place(tex.translate([0, 0, -0.02])))     # sunk a hair: one solid with the wall
            # quoins: chamfered blocks, long and short legs alternating, wrapping the corner
            # (each leg runs QT past the corner so the two faces' blocks meet solid)
            if quoins:
                for at_start, on in ((True, cstart), (False, cend)):
                    if not on:
                        continue
                    zones = _zones(H, belts, 0.0)
                    for (qa, qb) in zones:
                        v = max(qa, 1.8) if water_table and qa == 0 else qa
                        k = 0 if at_start else 1
                        while v < qb - 1.6:            # no stub blocks (they can't take the bevel)
                            top = min(v + QH - QG, qb)
                            leg = QL if k % 2 == 0 else QS
                            if at_start:
                                blk = chamfer_box(-QT, v, leg, top, 0.0, QT, QC, square=("u0",), bottom=QT)
                            else:
                                blk = chamfer_box(f.L - leg, v, f.L + QT, top, 0.0, QT, QC, square=("u1",),
                                                  bottom=QT)
                            dress.append(f.place(blk))
                            v += QH
                            k += 1
            # corner boards, one style per building, each zone between belts on its own
            if boards:
                zones = _zones(H, belts, 1.8)
                for at_start, on in ((True, cstart), (False, cend)):
                    if not on:
                        continue
                    for (qa, qb) in zones:
                        dress.append(f.place(_corner_board(corners, f.L, at_start, qa, qb, CBW, CBT)))
            # belt course: frieze band + drip cap
            for belt in (belts if belt_trim else []):
                if H <= belt[1]:
                    continue
                e0 = -1.0 if cstart else 0.0
                e1 = f.L + 1.0 if cend else f.L
                band = box([e0, belt[0], 0], [e1, belt[1] - 0.8, 0.9])
                cap = box([e0 - 0.3, belt[1] - 0.8, 0], [e1 + 0.3, belt[1], 1.4])
                dress.append(f.place(band + cap))
            if water_table:
                e0 = -1.2 if cstart else 0.0
                e1 = f.L + 1.2 if cend else f.L
                wt = box([e0, 0, 0], [e1, 1.2, 1.0]) + box([e0 - 0.2, 1.2, 0], [e1 + 0.2, 1.8, 1.2])
                dress.append(f.place(wt))
    dress = union(dress)
    # hide dressing that falls inside another block or into an opening
    hide = union([b.solid(grow=-0.02, dz0=-0.4, dz1=0.4) for b in blocks])     # 0.4: on the layer grid
    open_clear = union([o.facade.place(M.extrude(o.cs_on_facade(o.spec["cut"]).offset(0.05, JoinType.Miter),
                                                 6.0).translate([0, 0, -3.0])) for o in openings])
    lands = union([o.facade.place(M.extrude(o.cs_on_facade(o.spec["landing"]), 4.0).translate([0, 0, -0.05]))
                   for o in openings])
    dress = dress - hide - open_clear - lands
    if hide_extra is not None:
        dress = dress - hide_extra
    # dress must not overhang past a shorter block's roof line where it meets a taller one: fine as is
    return shell + dress


CORNER_BOARDS = ("board", "pilaster", "chamfer", "stepped", "capital", "panel", "beaded", "reeded", "rope",
                 "notched", "banded", "cabled", "reveal", "rosette", "lozenge", "blocked")


def _corner_board(style, L, at_start, qa, qb, w=2.4, t=0.65):
    """One corner board between heights qa and qb in a facade's (u, v, w) frame, at the
    corner u = 0 (at_start) or u = L. Every flat face is at qa or qb or a multiple of 0.2
    from them, and every projection's underside is square to the wall (it prints upright)
    or bevelled 45 degrees:
      board     plain, with a cap under the belt or eave (Beaumont)
      pilaster  a flute down the middle, a base block and the cap (Delancey)
      chamfer   the two boards mitred into a square post with its outer corner chamfered (Whitby)
      stepped   a narrow second board on the corner side, no cap (Merritt)
      capital   a base plinth and a capital flaring out at 45 degrees (Hollis)
      panel     a long sunk panel (Ashby's cupola)
      beaded    a bead down the middle between a plinth and a cap (the barber shop)
      reeded    three round reeds down the board between a plinth and a cap (the cottage)
      rope      a twisted three-strand cable down the board (the Primrose)
      notched   cut across with V notches every 6 mm (the Rosecroft)
      banded    a pilaster banded by raised blocks every 3.6 mm (the Laurel)
      cabled    two flutes, their lower third filled with round cables (the Myrtle)
      reveal    two narrow boards with a sunk reveal between them, on a plinth, under a cap
                (the Larkspur)
      rosette   a plain board with square Eastlake blocks carrying round rosettes at its
                foot and head (the Juniper)
      lozenge   a plain board on a plinth carrying raised lozenges every 5.6 mm (the Camellia)
      blocked   a board with small raised blocks at alternate edges every 2.4 mm (the Wisteria)"""
    def span(a, b):                      # u from the corner: a..b (a < b), mirrored at the end
        return (a, b) if at_start else (L - b, L - a)
    u0, u1 = span(0.0, w)
    far0, far1 = span(0.0, w + 0.2)      # reaching 0.2 past the board on the side away from the corner
    parts = []
    if style == "chamfer":
        c = 0.5
        prof = [(0.0, 0.0), (w, 0.0), (w, t), (-t + c, t), (-(t - c / 2), t - c / 2)]
        pts = [((uu if at_start else L - uu), v, ww) for uu, ww in prof for v in (qa, qb)]
        return M.hull_points(pts)
    parts.append(box([u0, qa, 0], [u1, qb, t]))
    if style in ("board", "pilaster"):
        parts.append(box([far0, qb - 0.8, 0], [far1, qb, t + 0.3]))
    if style == "pilaster":
        parts.append(box([far0, qa, 0], [far1, qa + 1.2, t + 0.3]))
        um = (u0 + u1) / 2
        if qb - qa > 5.0:
            return union(parts) - box([um - 0.25, qa + 1.6, t - 0.25], [um + 0.25, qb - 1.6, t + 0.5])
    if style == "stepped":
        n0, n1 = span(0.0, 1.4)
        parts.append(box([n0, qa, t - 0.01], [n1, qb, t + 0.4]))
    if style == "capital":
        parts.append(box([far0, qa, 0], [far1, qa + 1.4, t + 0.3]))
        e0, e1 = span(0.0, w + 0.4)
        if qb - qa > 5.0:
            parts.append(M.hull_points([(uu, qb - 2.0, ww) for uu in (u0, u1) for ww in (0.0, t)] +
                                       [(uu, qb - 1.6, ww) for uu in (e0, e1) for ww in (0.0, t + 0.4)]))
            parts.append(box([e0, qb - 1.6, 0], [e1, qb, t + 0.4]))
    if style == "beaded":
        parts.append(box([far0, qa, 0], [far1, qa + 1.6, t + 0.3]))
        parts.append(box([far0, qb - 1.0, 0], [far1, qb, t + 0.3]))
        um = (u0 + u1) / 2
        if qb - qa > 5.0:
            parts.append(chamfer_box(um - 0.5, qa + 1.6, um + 0.5, qb - 1.0, t - 0.01, 0.31, c=0.25))
    if style == "notched":              # Stick style: the board cut across with V notches every 6 mm
        if qb - qa > 5.0:
            cuts = []
            for v in np.arange(qa + 3.0, qb - 2.0, 6.0):
                v = round(v / 0.2) * 0.2
                cuts.append(M.hull_points([(uu, vv, ww) for uu in (u0 - 0.1, u1 + 0.1)
                                           for vv, ww in ((v - 0.4, t + 0.1), (v + 0.4, t + 0.1), (v, t - 0.35))]))
            return union(parts) - union(cuts)
    if style == "rope":                 # a twisted cable moulding down the middle of the board
        parts.append(box([far0, qa, 0], [far1, qa + 1.4, t + 0.3]))
        parts.append(box([far0, qb - 1.0, 0], [far1, qb, t + 0.3]))
        if qb - qa > 5.0:
            um = (u0 + u1) / 2
            L_ = qb - qa - 2.4
            strand = cs_union([circle((0.42 * math.cos(2 * math.pi * k / 3), 0.42 * math.sin(2 * math.pi * k / 3)), 0.32, 12)
                               for k in range(3)])
            rope = M.extrude(strand, L_, int(L_ / 0.2), 360.0 * L_ / 2.4)
            parts.append(rope.transform(np.array([[1.0, 0, 0, um], [0, 0, 1.0, qa + 1.4], [0, 1.0, 0, t + 0.2]])))
    if style == "reeded":               # three reeds down the board between a plinth and a cap
        parts.append(box([far0, qa, 0], [far1, qa + 1.4, t + 0.3]))
        parts.append(box([far0, qb - 1.0, 0], [far1, qb, t + 0.3]))
        if qb - qa > 5.0:
            for k in range(3):
                uc = u0 + (u1 - u0) * (k + 0.5) / 3
                parts.append(M.cylinder(qb - qa - 2.4, 0.3, 0.3, 12).translate([uc, t - 0.05, 0.0])
                             .transform(np.array([[1.0, 0, 0, 0], [0, 0, 1.0, qa + 1.4], [0, 1.0, 0, 0]])))
    if style == "banded":               # a pilaster banded by raised, chamfered blocks
        parts.append(box([far0, qa, 0], [far1, qa + 1.6, t + 0.3]))
        parts.append(box([far0, qb - 1.0, 0], [far1, qb, t + 0.3]))
        if qb - qa > 6.0:
            for v in np.arange(qa + 3.2, qb - 2.6, 3.6):
                v = round(v / 0.2) * 0.2
                parts.append(chamfer_box(far0, v, far1, v + 1.6, t - 0.01, 0.31, c=0.2))
    if style == "cabled":               # two flutes, their lower third filled with round cables
        u0, u1 = span(0.0, w + 0.6)                     # a wider board to carry two flutes
        far0, far1 = span(0.0, w + 0.8)
        parts = [box([u0, qa, 0], [u1, qb, t])]
        parts.append(box([far0, qa, 0], [far1, qa + 1.4, t + 0.3]))
        parts.append(box([far0, qb - 1.2, 0], [far1, qb, t + 0.3]))
        if qb - qa > 7.0:
            um = (u0 + u1) / 2
            f0, f1 = qa + 2.0, qb - 1.8
            vc = round((f0 + (f1 - f0) / 3) / 0.2) * 0.2
            body = union(parts)
            for du in (-0.6, 0.6):
                body = body - box([um + du - 0.25, f0, t - 0.3], [um + du + 0.25, f1, t + 0.5])
                body = body + M.cylinder(vc - f0, 0.25, 0.25, 12).transform(
                    np.array([[1.0, 0, 0, um + du], [0, 0, 1.0, f0], [0, 1.0, 0, t - 0.3]]))
            return body
    if style == "rosette":              # Eastlake corner blocks with rosettes at the foot and head
        for va, vb in ((qa, qa + 2.4), (qb - 2.4, qb)):
            if vb - va > 1.0:
                parts.append(chamfer_box(far0, va, far1, vb, t - 0.01, 0.35, c=0.15))
                um = (far0 + far1) / 2
                parts.append(M.cylinder(0.3, 0.7, 0.55, 20).translate([um, (va + vb) / 2, t + 0.33]))
    if style == "blocked":              # a board with small raised blocks at alternate edges every 2.4 mm, like wooden quoins (the Wisteria)
        v = qa + 1.2
        k = 0
        while v + 1.6 < qb - 0.4:
            a0, a1 = span(0.0, w * 0.62) if k % 2 == 0 else span(w * 0.38, w + 0.2)
            parts.append(chamfer_box(a0, v, a1, v + 1.6, t - 0.01, 0.3, c=0.15))
            v += 2.4
            k += 1
    if style == "lozenge":              # a plain board with a plinth, carrying raised lozenges every 5.6 mm (the Camellia)
        parts.append(box([far0, qa, 0], [far1, qa + 1.2, t + 0.3]))
        um = (u0 + u1) / 2
        v = qa + 3.6
        while v + 1.2 < qb - 0.8:
            dia = poly([(um, v - 1.2), (um + 0.8, v), (um, v + 1.2), (um - 0.8, v)])
            parts.append(ext(dia, t - 0.01, t + 0.3))
            v += 5.6
    if style == "reveal":               # two narrow boards parted by a sunk reveal
        parts.append(box([far0, qa, 0], [far1, qa + 1.4, t + 0.3]))
        parts.append(box([far0, qb - 1.2, 0], [far1, qb, t + 0.3]))
        if qb - qa > 4.0:
            um = (u0 + u1) / 2
            return union(parts) - box([um - 0.3, qa + 1.4, t - 0.3], [um + 0.3, qb - 1.2, t + 0.5])
    if style == "panel" and qb - qa > 3.0:
        return union(parts) - box([u0 + 0.5, qa + 1.0, t - 0.2], [u1 - 0.5, qb - 1.0, t + 0.5])
    return union(parts)


def foundation(blocks, z0, z1, t=3.0, proud=0.8, stone_d=0.55, seed=4, openings=(), lip=1.2, style="fieldstone"):
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
        reg = rect(0.0, 0.4, f.L, z1 - z0 - 0.4)
        from .trimwork import foundation_skin
        s = foundation_skin(style, reg, seed=seed + i)
        tex.append(f.place(s.translate([0, 0, -0.03])))      # sunk a hair: one solid with the ring
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
    """Inward shelf under a lip: grows 45 degrees from nothing to ``reach`` at z_top.
    Steps are one layer tall and end exactly at z_top at the full reach."""
    n = int(math.ceil(reach / step - 1e-9))
    out = []
    for k in range(n):
        e = min(reach, (k + 1) * step)
        out.append(slab(offset(base, -t + 0.05) - offset(base, -t - e), z_top - (n - k) * step,
                        z_top - (n - k - 1) * step))
    return union(out)


def lip_ring(base, t, z0, h=LIP_H):
    """Locating lip just inside the wall's inner face, standing on z0."""
    return slab(offset(base, -t - LIP_IN) - offset(base, -t - LIP_W), z0 - 0.01, z0 + h)


def lip_keep(base, t, z0, h=LIP_H, inner=LIP_IN, reach=LIP_W, clr=0.15):
    """Keep-out around a locating lip, limited to the building's interior, for cutting the
    partitions of the parts the lip reaches into."""
    cs = (offset(base, -t - inner + clr) - offset(base, -t - reach - clr)) ^ offset(base, -t + 0.02)
    return slab(cs, z0 - clr, z0 + h + clr)


BELT_BLOCKS = dict(w=0.9, z=1.4, h=1.2, d0=0.8, d=0.5, c=0.35, pitch=3.0, margin=1.8)


def _stepped(cs, w0, d):
    """A relief of outline ``cs`` (u, v) standing ``d`` proud of w0, printable on an upright
    wall: the first 0.2 at full size, each further 0.2 with its foot pulled up 0.2, so its
    underside steps back at 45 degrees instead of hanging flat."""
    out, k = [], 0
    while k * 0.2 < d - 1e-6:
        layer = cs
        for j in range(1, k + 1):
            layer = layer ^ cs.translate((0.0, 0.2 * j))
        if not layer.is_empty():
            out.append(ext(layer, w0 + 0.2 * k - (0.05 if k == 0 else 0.0), w0 + min(d, 0.2 * (k + 1))))
        k += 1
    return union(out)


def _swag_row(outline_pts, z0, sw):
    """Festoons (swags) hung between rosettes along a belt's fascia, on every face (the
    Camellia): each swag a crescent that thickens to its lowest point, each rosette a
    round boss; both step back underneath so the ring prints upright."""
    pts = ccw(outline_pts)
    w0, zr, sag, pitch, margin = sw["w0"], sw["zr"], sw["sag"], sw["pitch"], sw["margin"]
    row = []
    for i in range(len(pts)):
        f = Facade(pts[i], pts[(i + 1) % len(pts)], z0)
        span = f.L - 2 * margin
        if span < 2.4:
            continue
        n = max(1, int(round(span / pitch)))
        us = [margin + span * j / n for j in range(n + 1)]
        for a, b in zip(us[:-1], us[1:]):
            ts = np.linspace(0.0, 1.0, 17)
            lo = [(a + 0.4 + (b - a - 0.8) * t_, zr - 0.2 - sag * math.sin(math.pi * t_)) for t_ in ts]
            hi = [(x, z + 0.5 + 0.35 * math.sin(math.pi * t_)) for (x, z), t_ in zip(lo, ts)]
            row.append(f.place(_stepped(poly(lo + hi[::-1]), w0, 0.4)))
        for u in us:
            row.append(f.place(_stepped(circle((u, zr), 0.6, 20), w0, 0.45)))
    return union(row)


def belt_ring(outline_pts, z0, t=3.0, prof=BELT_PROF, lip=True, blocks=BELT_BLOCKS):
    """Belt course between two storey shells, the full wall thickness plus a moulded band.

    It sits on the lower shell (located by that shell's lip) and carries the lip for the
    upper shell on an inside corbel that starts above the lower lip. Prints upright.
    ``blocks``: a row of small chamfered blocks on the fascia band (modillion blocks)."""
    h = prof[-1][1]
    ring = sweep_ring(outline_pts, [(-t, z0)] + [(d, z0 + z) for d, z in prof] + [(-t, z0 + h)])
    if blocks and blocks.get("kind") == "swag":
        ring = ring + _swag_row(outline_pts, z0, blocks)
    elif blocks:
        bk = dict(BELT_BLOCKS)
        bk.update(blocks)
        pts = ccw(outline_pts)
        row = []
        for i in range(len(pts)):
            f = Facade(pts[i], pts[(i + 1) % len(pts)], z0)
            span = f.L - 2 * bk["margin"]
            if span < bk["w"]:
                continue
            n = max(1, int(round(span / bk["pitch"])))
            for j in range(n + 1):
                for du in ((-bk["pair"] / 2, bk["pair"] / 2) if bk.get("pair") else (0.0,)):
                    u = bk["margin"] + span * j / n + du
                    row.append(f.place(chamfer_box(u - bk["w"] / 2, bk["z"], u + bk["w"] / 2, bk["z"] + bk["h"],
                                                   bk["d0"] - 0.05, bk["d"] + 0.05, bk["c"])))
        ring = ring + union(row)
    base = poly(ccw(outline_pts))
    if lip:
        assert h - LIP_W >= LIP_H + 0.2, "belt ring too short for its corbel"
        ring = ring + _corbel(base, t, z0 + h) + lip_ring(base, t, z0 + h)
    return ring


def storey_shells(blocks, openings, z_split, t=3.0, prof=BELT_PROF, clear=(), belt_blocks="default", **kw):
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
    ring = belt_ring(outline, z_split, t=t, prof=prof, **({} if belt_blocks == "default" else dict(blocks=belt_blocks)))
    upper = upper - lip_keep(base, t, z_split + h)
    for kp in clear:
        upper = upper - kp
        lower = lower - kp
    return dict(lower=lower, ring=ring, upper=upper, ring_h=h, outline=outline)


def stacked_shells(blocks, openings, splits, t=3.0, prof=BELT_PROF, clear=(), belt_blocks="default", **kw):
    """Walls as a stack of one-piece storey shells with a belt ring at every split.

    ``splits`` = absolute z of each storey joint, low to high. At each one the shell is cut,
    a belt ring (the outline of the blocks that continue above it) takes the joint, the
    piece below gets a corbelled locating lip for the ring and the ring one for the piece
    above. A block that ends below a split (a wing, or the main house under a taller
    tower) simply stops in the piece below. ``clear`` = keep-outs for interior partitions.

    Returns dict(shells=[bottom .. top], rings=[...], outlines=[...], ring_h)."""
    h = prof[-1][1]
    zb = min(b.z0 for b in blocks)
    belts = [(z - zb, z - zb + h) for z in splits]
    shell = wall_shell(blocks, openings, t=t, belt=belts, belt_trim=False, **kw)
    shells, rings, outlines = [], [], []
    lo = prev_base = None
    for z in splits:
        above = [b for b in blocks if b.z1 > z + h + 1.0]
        base = cs_union([b.cs for b in above])
        outline = max(base.to_polygons(), key=lambda L: abs(poly(L).area()))
        piece = shell.trim_by_plane([0, 0, -1.0], -z)
        if lo is not None:
            piece = piece.trim_by_plane([0, 0, 1.0], lo)
        piece = piece + _corbel(base, t, z) + lip_ring(base, t, z)
        if lo is not None:
            piece = piece - lip_keep(prev_base, t, lo)
        shells.append(piece)
        rings.append(belt_ring(outline, z, t=t, prof=prof,
                               **({} if belt_blocks == "default" else dict(blocks=belt_blocks))))
        outlines.append(outline)
        lo, prev_base = z + h, base
    top = shell.trim_by_plane([0, 0, 1.0], lo) - lip_keep(prev_base, t, lo)
    shells.append(top)
    out = []
    for piece in shells:
        for kp in clear:
            piece = piece - kp
        out.append(piece)
    return dict(shells=out, rings=rings, outlines=outlines, ring_h=h)

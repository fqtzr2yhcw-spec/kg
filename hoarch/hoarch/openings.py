"""Windows and doors, each ONE part like the reference kit's: a plug and its surround.

Construction (the house standard):
  * the wall has a plain opening; the part's *plug* slides into it with CLR clearance
    per side and PLUG depth, and its surround (casing, sill, hood...) sits on the wall
    face in the landing cut in the siding;
  * the glazing is the plug's back face: GLASS thick (two 0.2 mm layers), so it glows
    when lit, and the sash is built on it, recessed inside the wall;
  * it prints face-up (local w becomes print z + PLUG). The surround is wider than the
    plug, so it starts PLUG above the bed: print these parts WITH supports (tree, on
    the build plate only). The supports touch only the back of the surround, which lies
    against the wall.

All geometry is in a local (u, v, w) frame: u = 0 at the opening centre,
v = 0 at the opening bottom, w = 0 at the wall face.
"""
import math
import numpy as np

from manifold3d import CrossSection as CS, JoinType, Manifold as M

from .core import RIB, SLOT, arch_cs, circle, cs_union, poly, rect, union
from .ornament import (bezier, bullseye, chamfer_box, console, dentils, ext, fan_crest, keystone, oval, quatrefoil,
                       rosette_block, scroll_bracket, stepped, stroke, sunburst, swag, urn_cs, volute)

CLR = 0.15      # plug clearance per side
PLUG = 1.6      # plug depth into a 3.0 mm wall (8 x 0.2 mm layers)
GLASS = 0.4     # glazing thickness (2 x 0.2 mm layers)
SASH_REC = 0.4  # sash face sits this far behind the wall face
# face-up relief heights above the wall face sit on the 0.2 mm layer grid:
CAS = 0.6       # flat casing band
BEAD = 1.0      # raised back-band / bead on the casing


def place(sp, A, frame_col, sash_col, glass_col=None):
    """World solid, print transform and render zones of a one-piece window/door ``sp`` in
    the facade frame ``A`` (local w = 0 on the wall face; the plug goes into the opening)."""
    from .core import inv34
    B = A.copy()
    B[:, 3] = A[:, 3] + A[:, 2] * sp["back"]          # shift out by the back depth
    zones = [(glass_col or sash_col, sp["glass"]), (sash_col, sp["sash"]), (frame_col, sp["frame"])]
    return sp["insert"].transform(B), inv34(B), [(c, m.transform(B)) for c, m in zones]


def footprint(surround, op, grow=0.15):
    """Where the siding must stop for an insert: the surround's own outline seen from the
    front (plus a hair), so the clapboards run right up to the trim with no bare patches."""
    return cs_union([surround.project().offset(grow, JoinType.Miter, 4.0), op.offset(grow, JoinType.Miter, 4.0)])


def _one_piece(sash_parts, sur_parts, op, plug_cs, pl, top, bottom, land_extra=None):
    """Join the plug (glass and sash) and the surround into one part (see the module notes).
    Returns the insert dict; ``glass``/``sash``/``frame`` are its colour zones for renders."""
    sur = union(sur_parts)
    sash = union(sash_parts)
    loose = [round(c.volume(), 2) for c in (sur + sash).decompose()]
    if len(loose) > 1:
        print("  WARNING: one-piece insert falls into", len(loose), "pieces", sorted(loose)[:6])
    glass = sash ^ ext(op.offset(1.0), -pl - 1.0, -pl + GLASS)
    land = footprint(sur, op)
    if land_extra is not None:
        land = land + land_extra
    return dict(insert=sash + sur, sash=sash - glass, glass=glass, frame=sur, surround=sur, back=0.0,
                cut=op, landing=land, top=top, bottom=bottom)


def opening_cs(w, h, rise=None, arch=True):
    """Opening outline in local coords (u centred, v from 0)."""
    if not arch or rise == 0:
        return rect(-w / 2, 0, w / 2, h)
    r = w / 2 if rise is None else rise
    return arch_cs(-w / 2, w / 2, 0, h - r, rise=r)


def _arc_band(w_in, spring, rise, r_in_extra, thick, u_ext=0.0, seg=32):
    """Band following a (segmental) arch: inner edge offset r_in_extra outside the
    opening arch, radial thickness ``thick``. Returns (cs, centre_v, radius_in)."""
    half = w_in / 2
    if rise >= half - 1e-6:
        r = half
        cy = spring
    else:
        r = (half * half + rise * rise) / (2 * rise)
        cy = spring + rise - r
    r0, r1 = r + r_in_extra, r + r_in_extra + thick
    # angular extent: to where the band meets v = spring (at its inner radius)
    a_lim = math.acos(max(-1.0, min(1.0, (spring - cy) / r1)))
    pts_o, pts_i = [], []
    for k in range(seg + 1):
        a = -a_lim + 2 * a_lim * k / seg
        pts_o.append((r1 * math.sin(a), cy + r1 * math.cos(a)))
    a_in = math.acos(max(-1.0, min(1.0, (spring - cy) / r0)))
    for k in range(seg + 1):
        a = a_in - 2 * a_in * k / seg
        pts_i.append((r0 * math.sin(a), cy + r0 * math.cos(a)))
    band = poly(pts_o + pts_i)
    return band, cy, r0


def window_insert(w, h, rise=None, style="crest", lites=(1, 1), casing=1.1, bare=False, ends=0.9, sill_ext=0.6,
                  clip=False, apron=False, consoles=None, qa=False, rows=(1, 1), upper=None):
    """Italianate window: segmental- or round-arched head, eared casing,
    bracketed sill, moulded hood with keystone; ``style`` in {"crest", "key", "flat"}, or
    "voussoir" (a brick-house head: stone voussoirs long and short in turn, and a keystone).
    Queen Anne styles (see _window_qa): "pediment" (segmental pediment with a sunburst on
    bullseye corner blocks, a shaped apron with a drop), "blocks" (the same without the
    pediment, for a head with no headroom) and "scroll" (an eyebrow hood whose ends roll
    into volutes, keystone and fan crest, a sill on scroll brackets).
    ``apron``: a panelled apron under the sill instead of the two sill brackets.
    ``consoles``: scroll consoles carrying a flat cap (default on for "flat").
    ``qa``: Queen Anne upper sash, a big centre light ringed by small border lights.

    Returns dict(insert=Manifold, cut=CrossSection, landing=CrossSection, top=v, bottom=v)."""
    rise = w / 2 if rise is None else rise
    spring = h - rise
    op = opening_cs(w, h, rise)
    plug_cs = op.offset(-CLR, JoinType.Miter, 4.0)
    pl, rec = PLUG, SASH_REC
    parts = []
    # --- glass + sash ring + bars ---------------------------------------------------
    frame_w = 0.55
    glass = ext(plug_cs, -pl, -pl + GLASS)
    ring = ext(plug_cs - plug_cs.offset(-frame_w, JoinType.Miter, 4.0), -pl, 0.0)
    parts += [glass, ring]
    inner = plug_cs.offset(-frame_w, JoinType.Miter, 4.0)
    bars = []
    lo, up = lites
    mr = h * 0.46                              # meeting rail height
    bars.append(rect(-w, mr - 0.3, w, mr + 0.3))
    for n, v0, v1 in ((lo, 0, mr), (up, mr, h)):
        for i in range(1, n):
            u = -w / 2 + w * i / n
            bars.append(rect(u - RIB / 2, v0, u + RIB / 2, v1))
    # ``rows``: horizontal muntins in each sash (6-over-6 is lites=(3, 3), rows=(2, 2))
    for nr, v0, v1 in ((rows[0], 0.0, mr), (rows[1], mr, spring if rise > 0 else h)):
        for j in range(1, nr):
            v = v0 + (v1 - v0) * j / nr
            bars.append(rect(-w, v - RIB / 2, w, v + RIB / 2))
    if upper == "diamond":           # leaded diamond panes in the upper sash
        for sgn in (-1, 1):
            for k in range(-14, 15):
                x0 = k * 1.6
                bars.append(stroke([(x0 - sgn * 12, mr - 12 * 1.6), (x0 + sgn * 12, mr + 12 * 1.6)], RIB, caps=False)
                            ^ rect(-w, mr, w, h + 5))
    if qa:   # border lights: an inner frame line and short bars across the border
        top = inner ^ rect(-w, mr + 0.3, w, h + 5)
        b = 1.2 if w >= 8 else 1.0
        core = top.offset(-b, JoinType.Miter, 4.0)
        if not core.is_empty():   # borders on the top and sides only; the core sits on the meeting rail
            c0 = core.bounds()
            core = (core + rect(c0[0], mr, c0[2], c0[1] + 0.1)) ^ top
            bars.append(core.offset(RIB / 2, JoinType.Miter, 4.0) - core.offset(-RIB / 2, JoinType.Miter, 4.0))
            ring = top - core
            cb = core.bounds()
            n_top = max(1, int(round((cb[2] - cb[0]) / 1.9)))
            for i in range(1, n_top):
                u = cb[0] + (cb[2] - cb[0]) * i / n_top
                bars.append(rect(u - RIB / 2, cb[3] - 0.2, u + RIB / 2, h + 5) ^ ring)
            n_side = max(1, int(round((cb[3] - cb[1]) / 1.9)))
            for i in range(1, n_side):
                v = cb[1] + (cb[3] - cb[1]) * i / n_side
                bars.append(rect(-w, v - RIB / 2, w, v + RIB / 2) ^ ring)
            for u in (cb[0], cb[2]):   # corner bars out to the frame
                bars.append(rect(u - RIB / 2, cb[3] - RIB / 2, u + RIB / 2, h + 5) ^ ring)
    sash = cs_union(bars) ^ inner
    parts.append(ext(sash, -pl + GLASS, -rec))
    # upper sash frame (a second frame line just inside the ring reads as the sash stile)
    parts.append(ext(inner - inner.offset(-RIB, JoinType.Miter, 4.0), -pl + GLASS, -rec))
    if bare:
        ins = union(parts)
        return dict(insert=ins, sash=ins, surround=None, cut=op, landing=op.offset(0.2, JoinType.Miter, 4.0),
                    top=h, bottom=0.0)
    sash_parts, parts = parts, []
    # --- casing (flat band around sides and arch) with a raised inner bead ------------
    cas_out = op.offset(casing, JoinType.Round)
    cas = cas_out - op.offset(0.0, JoinType.Miter, 4.0)
    cas = cas ^ rect(-w, 0.0, w, h + casing + 1)         # no casing under the sill
    parts.append(ext(cas, 0.0, CAS))
    bead = (op.offset(RIB, JoinType.Round) - op) ^ rect(-w, 0.0, w, h + 1)
    parts.append(ext(bead, CAS, BEAD))
    if style in ("pediment", "scroll", "blocks"):
        return _window_qa(w, h, rise, spring, op, cas_out, casing, style, apron, clip, parts, sash_parts, plug_cs)
    # ears: small outward steps at the spring line (a flat cap on consoles has none)
    consoles = (style == "flat") if consoles is None else consoles
    ear_h = 1.1
    for s in (() if ((style == "flat" and consoles) or style == "voussoir") else (-1, 1)):
        u0 = s * (w / 2 + casing)
        parts.append(ext(rect(min(u0, u0 + s * 0.5), spring - ear_h, max(u0, u0 + s * 0.5), spring + 0.2), 0.0, CAS))
    # --- sill with two small brackets -------------------------------------------------
    sw = w / 2 + casing + sill_ext
    sill = rect(-sw, -0.9, sw, 0.0)
    parts.append(ext(sill, 0.0, 1.2))
    parts.append(ext(rect(-sw - 0.2, -SLOT, sw + 0.2, 0.0), 1.2, 1.4))      # drip nose
    bottom = -2.25
    if apron:
        # panelled apron: a raised field with a sunken-bevel inner panel and a bead at its foot
        aw = w / 2 + casing - 0.1
        parts.append(ext(rect(-aw, -2.9, aw, -0.9), 0.0, 0.4))
        parts.append(chamfer_box(-aw + 0.7, -2.5, aw - 0.7, -1.3, 0.4, 0.4, c=0.25))
        parts.append(ext(rect(-aw - 0.2, -3.1, aw + 0.2, -2.7), 0.0, 0.6))
        bottom = -3.1
    else:
        for s in (-1, 1):
            parts.append(ext(rect(s * (w / 2 + 0.2) - 0.45, -1.9, s * (w / 2 + 0.2) + 0.45, -0.9), 0.0, 0.8))
            parts.append(ext(rect(s * (w / 2 + 0.2) - 0.35, -2.25, s * (w / 2 + 0.2) + 0.35, -1.9), 0.0, 0.6))
    top = h + casing
    # --- hood --------------------------------------------------------------------------
    if style in ("crest", "key"):
        band, cy, r0 = _arc_band(w, spring, rise, casing - 0.15, 1.5)
        hood_face = band ^ rect(-w, spring - 0.2, w, h + 20)
        # hood ends: horizontal returns beyond the casing, dropping over little corbels
        endw = w / 2 + casing + ends
        ends_cs = cs_union([rect(-endw, spring - 0.4, -w / 2 - casing + 0.3, spring + 0.9),
                            rect(w / 2 + casing - 0.3, spring - 0.4, endw, spring + 0.9)])
        hood = cs_union([hood_face, ends_cs])
        if clip:   # keep the hood within the casing + ends width (narrow piers, bays)
            hood = hood ^ rect(-endw, -1, endw, h + 20)
        # stepped crown: three stacked layers, each smaller, for a moulded section
        parts.append(stepped(hood, [(0.0, 0.0, 1.0), (0.25, 1.0, 1.4), (0.5, 1.4, 1.8)]))
        # a bead line on the inner edge of the crown
        rim = (band.offset(0.0, JoinType.Round) - band.offset(-RIB, JoinType.Round)) ^ rect(-w, spring, w, h + 20) ^ hood
        parts.append(ext(rim, 1.0, 1.2))
        # corbel blocks under the hood ends
        for s in (-1, 1):
            if ends >= 0.6:
                parts.append(rosette_block(s * (endw - 0.55), spring - 1.0, 1.0, 0.0, 1.2))
        # keystone
        ktop = cy + r0 + 1.5 + 0.6
        parts.append(keystone(0.0, h - 0.2, ktop - h + 0.2, 1.2, 1.7, 0.0, 2.0))
        top = ktop
        if style == "crest":
            parts.append(fan_crest(0.0, ktop - 0.05, 1.6, 0.0, 1.6))
            top = ktop + 1.6
        # tympanum fan (radiating flutes between the opening arch and the hood)
        if rise > 1.2 and casing >= 1.0:          # on slim casings the flutes print as loose specks
            fl = []
            for k in range(5):
                a = -0.9 + 1.8 * k / 4
                fl.append(poly([(0, spring - 0.1), ((r0 + 0.2) * math.sin(a) - 0.3 * math.cos(a), cy + (r0 + 0.2) * math.cos(a) + 0.3 * math.sin(a)),
                                ((r0 + 0.2) * math.sin(a) + 0.3 * math.cos(a), cy + (r0 + 0.2) * math.cos(a) - 0.3 * math.sin(a))]))
            fan = (cs_union(fl) ^ (cas_out - op) ^ rect(-w, spring + 0.3, w, h + 20)).offset(-0.2).offset(0.2)
            parts.append(ext(fan, CAS, BEAD))
    elif style == "voussoir":
        # brick-house head: an arch of stone voussoirs, long and short in turn (Gibbs
        # fashion), with a projecting keystone. The joints are nozzle-wide slots.
        thick = 1.6
        band, cy, r0 = _arc_band(w, spring, rise, casing - 0.15, thick)
        r1 = r0 + thick
        a_lim = math.acos(max(-1.0, min(1.0, (spring - 0.2 - cy) / (r1 + 0.8))))
        n = max(5, int(round(2 * a_lim * (r0 + thick / 2) / 1.8)))
        n += 1 - n % 2                                  # odd: a stone (the keystone) at the crown
        stones = []
        for k in range(n):
            if k == n // 2:
                continue
            a0, a1 = -a_lim + 2 * a_lim * k / n, -a_lim + 2 * a_lim * (k + 1) / n
            ro = r1 + (0.8 if (k - n // 2) % 2 == 0 else 0.0)
            g = math.asin(0.3 / r0)                     # 0.6 joints: clear of a nozzle width
            arc = [a0 + g + (a1 - a0 - 2 * g) * j / 6 for j in range(7)]
            pts = [(ro * math.sin(a), cy + ro * math.cos(a)) for a in arc]
            pts += [(r0 * math.sin(a), cy + r0 * math.cos(a)) for a in reversed(arc)]
            stones.append(poly(pts))
        ktop = round((cy + r1 + 1.2) / 0.2) * 0.2
        kv0 = cy + r0 - 0.2
        kcs = poly([(-0.65, kv0), (0.65, kv0), (0.95, ktop), (-0.95, ktop)])
        face = (cs_union(stones) ^ rect(-w, spring - 0.2, w, h + 20)) - kcs.offset(0.6, JoinType.Miter, 4.0)
        if clip:
            face = face ^ rect(-w / 2 - casing - ends, -1, w / 2 + casing + ends, h + 20)
        face = face.offset(-0.25, JoinType.Miter, 4.0).offset(0.25, JoinType.Miter, 4.0)   # no specks
        parts.append(stepped(face, [(0.0, 0.0, 0.8), (0.2, 0.8, 1.0)]))
        parts.append(keystone(0.0, kv0, ktop - kv0, 1.3, 1.9, 0.0, 1.6))
        top = ktop
    else:  # flat cornice cap
        cw = w / 2 + casing + 0.8
        parts.append(ext(rect(-cw, h + casing - 0.2, cw, h + casing + 0.9), 0.0, 1.2))
        parts.append(ext(rect(-cw - 0.3, h + casing + 0.9, cw + 0.3, h + casing + 1.5), 0.0, 1.6))
        parts.append(dentils(-cw + 0.2, cw - 0.2, h + casing - 0.9, 0.7, 0.0, 0.8))
        if consoles:   # scroll consoles on the casing carry the cap
            for s in (-1, 1):
                parts.append(console(2.6, 1.2, 0.8, u=s * (w / 2 + casing / 2), v_top=h + casing - 0.9, w0=CAS))
        top = h + casing + 1.5
    parts.append(ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, CAS))      # lip over the sash frame
    return _one_piece(sash_parts, parts, op, plug_cs, PLUG, top, bottom)


def door_insert(w, h, leaves=2, transom=0.0, casing=1.2, crown=True, glass_top=True):
    """Panelled door(s) with an Italianate crown (cornice cap on two consoles).

    transom > 0 adds a glazed transom of that height at the top of the opening."""
    op = rect(-w / 2, 0, w / 2, h)
    plug_cs = op.offset(-CLR, JoinType.Miter, 4.0)
    pl = PLUG
    parts = [ext(plug_cs, -pl, -1.0)]                               # door slab back
    ring = plug_cs - plug_cs.offset(-0.5, JoinType.Miter, 4.0)
    parts.append(ext(ring, -pl, 0.0))
    dh = h - transom
    mid = SLOT if leaves > 1 else 0.0              # the meeting gap between leaves
    lw = (w - 2 * CLR - 1.0 - mid * (leaves - 1)) / leaves
    u = -w / 2 + CLR + 0.5
    for i in range(leaves):
        leaf = rect(u, 0.5, u + lw, dh - 0.3)
        parts.append(ext(leaf, -1.0, -0.8))
        # panels: a tall upper and a short lower, raised with a bevel
        pu0, pu1 = u + 0.6, u + lw - 0.6
        pv = [(0.5 + 0.6, 0.5 + dh * 0.28), (0.5 + dh * 0.28 + 0.6, dh - 0.9)]
        for k, (v0, v1) in enumerate(pv):
            pc = rect(pu0, v0, pu1, v1)
            if k == 1 and glass_top:
                parts[-1] = parts[-1] - ext(pc.offset(-0.25, JoinType.Miter), -pl + GLASS, 0.5)
                parts.append(ext(pc.offset(-0.25, JoinType.Miter), -pl, -pl + GLASS))
                continue
            parts.append(stepped(pc, [(0.0, -0.8, -0.6), (0.3, -0.6, -0.4)]))
        u += lw + mid
    if transom > 0:
        tcs = rect(-w / 2 + CLR + 0.5, dh + 0.2, w / 2 - CLR - 0.5, h - 0.5)
        parts = [p - ext(tcs, -pl - 1, -1.0 + 0.01) for p in parts]
        parts.append(ext(tcs, -pl, -pl + GLASS))
        parts.append(ext(rect(-w / 2, dh - 0.3, w / 2, dh + 0.3), -pl, -0.4))
    sash_parts, parts = parts, []
    cas_out = op.offset(casing, JoinType.Miter, 4.0) ^ rect(-w, 0.0, w, h + casing + 1)
    parts.append(ext(cas_out - op, 0.0, CAS))
    parts.append(ext((op - op.offset(-RIB, JoinType.Miter, 4.0)) ^ rect(-w, 0.3, w, h + 1), 0.0, CAS))
    parts.append(ext((op.offset(RIB, JoinType.Miter, 4.0) - op) ^ rect(-w, 0, w, h + 1), CAS, BEAD))
    # plinth blocks at the casing foot
    for s in (-1, 1):
        parts.append(ext(rect(s * (w / 2) - (casing + 0.15) * (s < 0), 0.0, s * (w / 2) + (casing + 0.15) * (s > 0), 2.2), 0.0, 1.0))
    top = h + casing
    if crown:
        cw = w / 2 + casing + 1.1
        v0 = h + casing
        parts.append(ext(rect(-cw + 0.5, v0 - 0.2, cw - 0.5, v0 + 1.6), 0.0, 0.8))          # frieze
        parts.append(dentils(-cw + 0.8, cw - 0.8, v0 + 1.6, 0.6, 0.0, 1.2))
        parts.append(ext(rect(-cw, v0 + 2.2, cw, v0 + 2.8), 0.0, 2.0))                      # cap
        parts.append(ext(rect(-cw - 0.3, v0 + 2.8, cw + 0.3, v0 + 3.3), 0.0, 2.2))
        for s in (-1, 1):
            parts.append(console(3.2, 1.6, 0.8, u=s * (cw - 0.6), v_top=v0 + 2.2, w0=0.0))
        top = v0 + 3.3
    return _one_piece(sash_parts, parts, op, plug_cs, PLUG, top, 0.0)


def twin_arch_window(w, h, balcony=5.0, casing=1.0):
    """Paired round-arched lights under one hood with a bracketed balcony below
    (tower window). The balcony is part of the insert and prints standing on the
    wall face (w up), so its brackets need no support."""
    op = opening_cs(w, h, None)
    plug_cs = op.offset(-CLR, JoinType.Miter, 4.0)
    pl = PLUG
    parts = [ext(plug_cs, -pl, -pl + GLASS),
             ext(plug_cs - plug_cs.offset(-0.5, JoinType.Miter, 4.0), -pl, 0.0)]
    # centre colonnette + two arched lights
    lw = (w - 2 * CLR - 1.0 - 0.8) / 2
    spring = h - w / 2
    col = rect(-0.4, 0, 0.4, spring + 0.5)
    lights = []
    for s in (-1, 1):
        c = s * (0.4 + lw / 2)
        lights.append(arch_cs(c - lw / 2, c + lw / 2, 0.4, spring + (w / 2 - lw / 2) * 0.35))
    frame_cs = plug_cs.offset(-0.5, JoinType.Miter, 4.0) - cs_union(lights)
    parts.append(ext(frame_cs + col, -pl + GLASS, -SASH_REC))
    parts.append(ext(rect(-0.55, spring - 0.2, 0.55, spring + 0.25), -pl + GLASS, 0.0))   # capital
    sash_parts, parts = parts, []
    cas_out = op.offset(casing, JoinType.Round)
    parts.append(ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, CAS))
    parts.append(ext((cas_out - op) ^ rect(-w, 0, w, h + 5), 0.0, 0.8))
    band, cy, r0 = _arc_band(w, spring, w / 2, casing - 0.1, 1.3)
    parts.append(stepped(band ^ rect(-w, spring - 0.1, w, h + 10), [(0.0, 0.0, 1.0), (0.25, 1.0, 1.4)]))
    parts.append(keystone(0.0, h - 0.2, 2.6, 1.1, 1.6, 0.0, 1.8))
    bw = w / 2 + casing + 2.0
    if not balcony:   # its own bracketed sill (with a balcony, the balcony floor is the sill)
        sw = w / 2 + casing + 0.6
        parts.append(ext(rect(-sw, -0.9, sw, 0.0), 0.0, 1.2))
        parts.append(ext(rect(-sw - 0.2, -SLOT, sw + 0.2, 0.0), 1.2, 1.4))
        for s_ in (-1, 0, 1):
            parts.append(ext(rect(s_ * (w / 2 - 0.6) - 0.45, -1.9, s_ * (w / 2 - 0.6) + 0.45, -0.9), 0.0, 0.8))
    # with a balcony, keep the wall bare where the balcony's floor and brackets land
    extra = rect(-bw - 0.3, -4.2, bw + 0.3, 0.2) if balcony else None
    return _one_piece(sash_parts, parts, op, plug_cs, pl, cy + r0 + 1.3, -0.9 if balcony else -1.9, extra)


def balcony(width, depth, rail_h=3.4, drop=3.0):
    """Bracketed balcony (floor, turned-look railing, three consoles) as its own part.

    Local frame as the inserts: floor top at v = 0, wall face at w = 0.
    Print it railing-down: print z = depth - w (use ``BALCONY_PRINT``)."""
    bw = width / 2
    parts = [ext(rect(-bw, -0.9, bw, 0.0), 0.0, depth)]                           # floor
    parts.append(ext(rect(-bw, -0.9, bw, rail_h), depth - 0.5, depth))            # railing panel back
    n = 9
    n = max(3, min(n, int((2 * bw - 0.7) / (RIB + SLOT)) + 1))
    posts = [rect(-bw + 0.35 + i * (2 * bw - 0.7) / (n - 1) - RIB / 2, 0.0,
                  -bw + 0.35 + i * (2 * bw - 0.7) / (n - 1) + RIB / 2, rail_h) for i in range(n)]
    parts[-1] = ext(cs_union(posts + [rect(-bw, rail_h - 0.55, bw, rail_h), rect(-bw, 0.0, bw, 0.5)]),
                    depth - 0.5, depth)
    for s in (-1, 1):                                                             # side rails
        parts.append(ext(rect(s * bw - RIB * (s > 0), 0.0, s * bw + RIB * (s < 0), rail_h), 0.3, depth))
    for s in (-1, 0, 1):
        parts.append(console(drop, depth - 0.4, 0.7, u=s * (bw - 0.8), v_top=-0.9, w0=0.0))
    return union(parts)


# print transform for balcony(): local (u, v, w) -> print (u, -v, depth - w) is a mirror,
# so use (u, v, w) -> (u, -v, depth - w) composed with a flip of v: (-u, v, depth - w)... kept
# explicit in the builder where depth is known.


# ------------------------------------------------------------------ Queen Anne surrounds
# Flowing sawn and carved work drawn as outlines and built up in flat terraces, so the
# surround still prints face-up: every level sits inside the one below, curves come out
# as clean perimeters, relief heights are on the 0.2 mm grid.

def _pediment_head(half, v_base, rise_in=2.4, band=0.9, sun=True):
    """Segmental pediment: a shelf, a curved cornice band and a sunburst in the tympanum.
    half = half-span of the shelf's body; v_base = shelf bottom. Returns (parts, top)."""
    parts = []
    shelf = rect(-half - 0.3, v_base, half + 0.3, v_base + 0.6)
    parts.append(ext(shelf, 0.0, 1.4))
    parts.append(ext(rect(-half, v_base - 0.2, half, v_base + 0.1), 0.0, 1.0))
    vs = v_base + 0.6
    arc, cy, r0 = _arc_band(2 * (half - band), vs, rise_in, 0.0, band)
    arc = arc ^ rect(-half - 1, vs - 0.01, half + 1, vs + rise_in + band + 1)
    parts.append(stepped(arc, [(0.0, 0.0, 1.2), (0.2, 1.2, 1.6)]))
    parts.append(ext(arc.hull(), 0.0, CAS))                   # tympanum: the whole segment under the band
    parts.append(ext(rect(-(half - band), vs - 0.2, half - band, vs + 0.2), 0.0, CAS))   # seats it into the shelf
    tymp = arch_cs(-(half - band), half - band, vs - 0.01, vs, rise=rise_in, seg=40)
    if sun and rise_in >= 2.0:
        # a carved fan: a half-round boss with five ribs radiating from a round bead
        R = rise_in - 0.35
        hub, rays = sunburst((0.0, vs), 0.0, 0.5, R - 0.1, n=5, a0=0.2, a1=math.pi - 0.2, ray0=0.45, ray1=0.7)
        half_disc = arch_cs(-R, R, vs - 0.01, vs, rise=R, seg=40) ^ tymp.offset(-0.3, JoinType.Round)
        parts.append(ext(half_disc, CAS - 0.01, 1.0))
        parts.append(ext(rays ^ half_disc, 1.0 - 0.01, 1.2))
        parts.append(ext(circle((0.0, vs), max(0.55, R * 0.3), 20) ^ half_disc, 1.0 - 0.01, 1.4))
    return parts, vs + rise_in + band


def _drop_apron(w, casing):
    """Shaped apron under the sill: its lower edge sweeps down in two curves to a centre
    drop, with a quatrefoil boss and two small discs on the field."""
    aw = w / 2 + casing - 0.1
    top, side = -0.9, -2.3
    tip = side - 1.2
    right = bezier((aw, side), (aw * 0.5, side), (aw * 0.2, tip), (0.0, tip), 12)
    pts = [(-aw, top), (aw, top)] + [tuple(p) for p in right] + [(-p[0], p[1]) for p in right[::-1][1:]]
    field = poly(pts)
    parts = [ext(field, 0.0, 0.4),
             ext(rect(-aw - 0.2, top - 0.4, aw + 0.2, top), 0.0, 0.8),                    # bead under the sill
             ext(circle((0.0, tip - 0.3), 0.55, 20), 0.0, 0.8),                             # drop
             ext(quatrefoil((0.0, (top + side) / 2 - 0.2), 0.42), 0.4 - 0.01, 0.8)]
    for sg in (-1, 1):
        parts.append(ext(circle((sg * aw * 0.6, (top + side) / 2 - 0.1), 0.35, 16), 0.4 - 0.01, 0.6))
    return parts, tip - 0.85


def _scroll_hood(w, h, rise, spring, casing):
    """Eyebrow hood: a curved band over the head whose ends roll down into volutes, a
    keystone and a small fan crest. Works over flat (rise 0) and arched heads."""
    parts = []
    if rise == 0:
        half = w / 2 + casing + 0.5
        vs = h + 0.6
        arc, cy, r0 = _arc_band(2 * half, vs, 1.9, 0.0, 0.9)
        crown = vs + 1.9 + 0.9
        field = arch_cs(-half, half, h + casing - 0.2, vs, rise=1.9, seg=40)
        parts.append(ext(field, 0.0, CAS))
    else:
        arc, cy, r0 = _arc_band(w, spring, rise, casing - 0.15, 0.9)
        half = r0 + 0.45
        vs = spring
        crown = cy + r0 + 0.9
    arc = arc ^ rect(-half - 2, vs - 0.01, half + 2, crown + 1)
    parts.append(stepped(arc, [(0.0, 0.0, 1.2), (0.2, 1.2, 1.6)]))
    ends = []
    for sg in (-1, 1):
        xe = sg * (half + 0.45 - 0.45)           # centre line of the band at its foot
        c = (xe + sg * 0.35, vs - 0.75)
        ends.append(volute(c, 0.95, turns=0.9, band=0.55, gap=SLOT, a0=math.pi / 2 if sg > 0 else math.pi / 2,
                           sense=-1 if sg > 0 else 1))
        ends.append(stroke([(xe, vs + 0.05), (xe, vs - 0.3)], 0.9))
    parts.append(ext(cs_union(ends), 0.0, 1.2))
    ktop = crown + 0.5
    parts.append(keystone(0.0, h - 0.2 if rise == 0 else h - 0.2, ktop - h + 0.2, 1.1, 1.6, 0.0, 1.8))
    parts.append(fan_crest(0.0, ktop - 0.05, 1.3, 0.0, 1.4))
    return parts, ktop + 1.3


def _window_qa(w, h, rise, spring, op, cas_out, casing, style, apron, clip, parts, sash_parts, plug_cs):
    """The Queen Anne window surrounds (see window_insert)."""
    # sill
    sw = w / 2 + casing + 0.4
    parts.append(ext(rect(-sw, -0.9, sw, 0.0), 0.0, 1.2))
    parts.append(ext(rect(-sw - 0.2, -SLOT, sw + 0.2, 0.0), 1.2, 1.4))
    if style in ("pediment", "blocks"):
        # bullseye corner blocks, segmental pediment with a sunburst (or, where there is no
        # headroom, "blocks": just a moulded shelf), shaped apron with a drop
        s_ = casing + 0.6
        cu = w / 2 + casing / 2
        for sg in (-1, 1):
            parts.append(bullseye(sg * cu, h + casing / 2, s_, 0.0, 1.2))
        half = w / 2 + casing + (0.3 if not clip else 0.0)
        if style == "pediment":
            head, top = _pediment_head(half, h + casing + 0.2, rise_in=2.4 if not clip else 2.0)
            parts += head
        else:
            parts.append(ext(rect(-half - 0.3, h + casing + 0.2, half + 0.3, h + casing + 0.8), 0.0, 1.4))
            parts.append(ext(rect(-half, h + casing, half, h + casing + 0.3), 0.0, 1.0))
            top = h + casing + 0.8
        if apron:
            ap, bottom = _drop_apron(w, casing)
            parts += ap
        else:
            bottom = -0.9
    else:
        # rounded ears, scroll hood, sill on two scroll brackets with a pendant between
        for sg in (-1, 1):
            u0 = sg * (w / 2 + casing)
            v_ear = spring if rise else h
            ear = cs_union([rect(min(u0, u0 + sg * 0.55), v_ear - 1.3, max(u0, u0 + sg * 0.55), v_ear + casing),
                            circle((u0, v_ear - 1.3), 0.55, 16)])
            parts.append(ext(ear, 0.0, CAS))
        head, top = _scroll_hood(w, h, rise, spring, casing)
        parts += head
        br = []
        for sg in (-1, 1):
            br.append(scroll_bracket(sg * (w / 2 + casing / 2 - 0.1), -0.9, 2.0, 1.3, band=0.6, sense=sg))
        parts.append(ext(cs_union(br), 0.0, 0.8))
        parts.append(ext(cs_union([stroke([(0.0, -0.9), (0.0, -1.5)], 0.5), circle((0.0, -1.75), 0.45, 16)]), 0.0, 0.6))
        bottom = -2.9
    parts.append(ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, CAS))      # lip over the sash frame
    return _one_piece(sash_parts, parts, op, plug_cs, PLUG, top, bottom)


def _ornate_leaf(u, lw, dh, hinge_left):
    """One ornate door leaf (face at w -0.8): a round-headed glazed light with a bead and
    spandrel rosettes, a beaded lock rail, a raised lower panel with a quatrefoil boss,
    and a knob. Returns (solids, glass_cs)."""
    st = min(1.0, lw * 0.16)
    parts = [ext(rect(u, 0.5, u + lw, dh - 0.3), -1.0, -0.8)]
    pu0, pu1 = u + st, u + lw - st
    g0 = 0.5 + dh * 0.42
    gtop = dh - 0.3 - 1.0
    r = (pu1 - pu0) / 2
    light = arch_cs(pu0, pu1, g0, gtop - r)
    parts.append(ext(light.offset(0.5, JoinType.Round) - light, -0.8, -0.6))
    for sg in (-1, 1):                                    # rosettes in the arch's spandrels
        cx = (pu0 + pu1) / 2 + sg * (r + 0.05)
        parts.append(ext(circle((cx - sg * 0.1, gtop - 0.05), 0.35, 12), -0.8, -0.6))
    parts.append(ext(rect(u + 0.4, g0 - 1.0, u + lw - 0.4, g0 - 0.45), -0.8, -0.6))           # lock rail bead
    pnl = rect(pu0, 1.4, pu1, g0 - 1.6)
    parts.append(stepped(pnl, [(0.0, -0.8, -0.6), (0.3, -0.6, -0.4)]))
    pb = pnl.bounds()
    qr = min(0.55, (pb[2] - pb[0]) * 0.11)
    parts.append(ext(quatrefoil(((pb[0] + pb[2]) / 2, (pb[1] + pb[3]) / 2), qr), -0.4 - 0.01, -0.2))
    kx = u + lw - 0.55 if hinge_left else u + 0.55
    parts.append(ext(circle((kx, g0 - 2.4), 0.35, 12), -0.8, -0.4))
    return parts, light


_GLASS_BARS = []           # bars a leaf lays over its glass: added back after the glass is cut


def _glass_bars():
    out = list(_GLASS_BARS)
    _GLASS_BARS.clear()
    return out


def zq(v):
    return round(v / 0.2) * 0.2


def _leaf(style, u, lw, dh, hinge_left):
    """One door leaf of the given style (face at w -0.8, details up to -0.2), from v 0.5 to
    dh - 0.3. Returns (solids, glass CrossSection or None). One style per building:
    arched (round-headed light over a quatrefoil panel), arch_panels (two raised panels with
    arched heads, no glass), studded (boards with rows of iron studs and a ring), crossbuck
    (a glazed light with muntins over an X-braced panel), half_glass (a light with a muntin
    cross over two small panels), two_panel (two tall raised panels), glazed_tall (glass
    nearly full height under a segmental head), oval (an oval light over a panel with a
    raised lozenge), four_panel (four raised panels, two over two), store (one big light
    with a push bar over a low panel and a kick plate), grille (a light behind a diagonal
    iron grille over a raised panel), six_light (six lights over two short panels), margin,
    french, dutch, boards_glass, lozenge, ledged, twin_arch (two round-headed lights over a
    raised panel), keyhole, sunray, lace, roundel (a round light in a square panel over a
    tall raised panel) and bolection (a light over a panel ringed by a bolection moulding)."""
    if style == "arched":
        return _ornate_leaf(u, lw, dh, hinge_left)
    st = min(1.0, lw * 0.16)
    top = dh - 0.3
    parts = [ext(rect(u, 0.5, u + lw, top), -1.0, -0.8)]
    pu0, pu1 = u + st, u + lw - st
    kx = u + lw - 0.55 if hinge_left else u + 0.55
    knob_v = dh * 0.46
    glass = None

    def panel(cs, lvl=0):
        parts.append(stepped(cs, [(0.0, -0.8, -0.6), (0.3, -0.6, -0.4)]))
    if style == "arch_panels":
        r = (pu1 - pu0) / 2
        lo = rect(pu0, 1.4, pu1, dh * 0.3)
        hi = arch_cs(pu0, pu1, dh * 0.3 + 1.0, top - 1.0 - r)
        panel(lo)
        panel(hi)
        parts.append(ext(circle(((pu0 + pu1) / 2, (dh * 0.3 + 1.0 + top - 1.0 - r) / 2), min(0.55, r * 0.4), 16), -0.41, -0.2))
    elif style == "studded":
        g = []
        n = max(2, int(lw / 1.3))
        for k in range(1, n):
            x = u + lw * k / n
            g.append(rect(x - 0.25, 0.9, x + 0.25, top - 0.4))
        parts[0] = parts[0] - ext(cs_union(g), -1.0, 0.0)          # joint floors on the layer grid
        studs = []
        for v in (1.6, dh * 0.35, dh * 0.65, top - 1.0):
            for k in range(n):
                studs.append(circle((u + lw * (k + 0.5) / n, v), 0.3, 10))
        parts.append(ext(cs_union(studs), -0.81, -0.4))
        parts.append(ext(circle((kx, knob_v), 0.7, 20) - circle((kx, knob_v), 0.25, 12), -0.81, -0.4))
    elif style == "crossbuck":
        gl = rect(pu0, dh * 0.5, pu1, top - st)
        glass = gl
        parts.append(ext(gl.offset(0.45, JoinType.Miter, 4.0) - gl, -0.8, -0.6))
        lo = rect(pu0, 1.2, pu1, dh * 0.5 - 1.0)
        parts.append(ext(lo.offset(0.45, JoinType.Miter, 4.0) - lo, -0.8, -0.4))        # faces on the layer grid
        b = lo.bounds()
        x = cs_union([stroke([(b[0], b[1]), (b[2], b[3])], 0.6), stroke([(b[0], b[3]), (b[2], b[1])], 0.6)]) ^ lo
        parts.append(ext(x, -0.81, -0.4))
    elif style == "half_glass":
        gl = rect(pu0, dh * 0.52, pu1, top - st)
        glass = gl
        parts.append(ext(gl.offset(0.45, JoinType.Miter, 4.0) - gl, -0.8, -0.6))
        c = gl.bounds()
        _GLASS_BARS.append(ext((rect((c[0] + c[2]) / 2 - 0.25, c[1], (c[0] + c[2]) / 2 + 0.25, c[3]) +
                                rect(c[0], (c[1] + c[3]) / 2 - 0.25, c[2], (c[1] + c[3]) / 2 + 0.25)) ^ gl.offset(0.2),
                               -1.21, -0.6))
        m = (pu0 + pu1) / 2
        panel(rect(pu0, 1.3, m - 0.35, dh * 0.52 - 1.0))
        panel(rect(m + 0.35, 1.3, pu1, dh * 0.52 - 1.0))
    elif style == "two_panel":
        panel(rect(pu0, 1.3, pu1, dh * 0.38))
        panel(rect(pu0, dh * 0.38 + 0.9, pu1, top - st))
    elif style == "glazed_tall":
        gl = arch_cs(pu0, pu1, dh * 0.24, top - st - 1.0, rise=1.0)
        glass = gl
        parts.append(ext(gl.offset(0.5, JoinType.Round) - gl, -0.8, -0.55))
        pl_ = rect(pu0, 1.2, pu1, dh * 0.24 - 0.9)
        panel(pl_)
        pb = pl_.bounds()
        parts.append(ext(circle(((pb[0] + pb[2]) / 2, (pb[1] + pb[3]) / 2), min(0.5, (pb[3] - pb[1]) * 0.3), 16), -0.41, -0.2))
    elif style == "four_panel":
        m = (pu0 + pu1) / 2
        vm = dh * 0.5
        for a, b in ((pu0, m - 0.35), (m + 0.35, pu1)):
            panel(rect(a, 1.3, b, vm - 0.45))
            panel(rect(a, vm + 0.45, b, top - st))
    elif style == "store":
        gl = rect(pu0, dh * 0.36, pu1, top - st)
        glass = gl
        parts.append(ext(gl.offset(0.45, JoinType.Miter, 4.0) - gl, -0.8, -0.6))
        parts.append(ext(rect(pu0, dh * 0.5 - 0.3, pu1, dh * 0.5 + 0.3) ^ gl.offset(0.2), -1.2, -0.6))     # push bar
        panel(rect(pu0, 2.4, pu1, dh * 0.36 - 1.0))
        parts.append(ext(rect(pu0, 0.8, pu1, 1.8), -0.81, -0.6))                                          # kick plate
    elif style == "grille":
        gl = rect(pu0, dh * 0.42, pu1, top - st)
        glass = gl
        parts.append(ext(gl.offset(0.45, JoinType.Miter, 4.0) - gl, -0.8, -0.6))
        b = gl.bounds()
        bars = []
        for sgn in (-1, 1):
            for k in range(-10, 11):
                x0 = (b[0] + b[2]) / 2 + k * 1.6
                bars.append(stroke([(x0 - sgn * 12, b[1] - 12), (x0 + sgn * 12, b[1] + 12)], 0.5, caps=False))
        _GLASS_BARS.append(ext(cs_union(bars) ^ gl.offset(0.2), -1.21, -0.6))              # iron grille
        panel(rect(pu0, 1.3, pu1, dh * 0.42 - 1.0))
    elif style == "six_light":            # six lights (two by three) over two short raised panels
        gl = rect(pu0, dh * 0.45, pu1, top - st)
        glass = gl
        parts.append(ext(gl.offset(0.45, JoinType.Miter, 4.0) - gl, -0.8, -0.6))
        b = gl.bounds()
        m = (b[0] + b[2]) / 2
        bars = [rect(m - 0.25, b[1], m + 0.25, b[3])]
        bars += [rect(b[0], b[1] + (b[3] - b[1]) * k / 3 - 0.25, b[2], b[1] + (b[3] - b[1]) * k / 3 + 0.25) for k in (1, 2)]
        _GLASS_BARS.append(ext(cs_union(bars) ^ gl.offset(0.2), -1.21, -0.6))
        panel(rect(pu0, 1.3, m - 0.35, dh * 0.45 - 1.0))
        panel(rect(m + 0.35, 1.3, pu1, dh * 0.45 - 1.0))
    elif style == "margin":               # one big light ringed by narrow margin lights
        gl = rect(pu0, dh * 0.40, pu1, top - st)
        glass = gl
        parts.append(ext(gl.offset(0.45, JoinType.Miter, 4.0) - gl, -0.8, -0.6))
        inner = gl.offset(-0.9, JoinType.Miter, 4.0)
        ring = inner.offset(0.25, JoinType.Miter, 4.0) - inner.offset(-0.25, JoinType.Miter, 4.0)
        b = gl.bounds()
        ib = inner.bounds()
        ticks = [rect(ib[0] - 0.25, ib[1] - 0.25 - 2, ib[0] + 0.25, ib[1] + 0.25) , rect(ib[2] - 0.25, ib[1] - 2, ib[2] + 0.25, ib[1] + 0.25),
                 rect(ib[0] - 0.25, ib[3] - 0.25, ib[0] + 0.25, ib[3] + 2), rect(ib[2] - 0.25, ib[3] - 0.25, ib[2] + 0.25, ib[3] + 2)]
        _GLASS_BARS.append(ext((ring + cs_union(ticks)) ^ gl.offset(0.2), -1.21, -0.6))
        panel(rect(pu0, 1.3, pu1, dh * 0.40 - 1.0))
    elif style == "french":               # glazed nearly full height with a grid of lights (2 x 4)
        gl = rect(pu0, 2.2, pu1, top - st)
        glass = gl
        parts.append(ext(gl.offset(0.45, JoinType.Miter, 4.0) - gl, -0.8, -0.6))
        b = gl.bounds()
        m = (b[0] + b[2]) / 2
        bars = [rect(m - 0.25, b[1], m + 0.25, b[3])]
        bars += [rect(b[0], b[1] + (b[3] - b[1]) * k / 4 - 0.25, b[2], b[1] + (b[3] - b[1]) * k / 4 + 0.25) for k in (1, 2, 3)]
        _GLASS_BARS.append(ext(cs_union(bars) ^ gl.offset(0.2), -1.21, -0.6))
    elif style == "dutch":                # a Dutch door: two halves, the top one glazed with four lights
        mid = zq(dh * 0.48)
        parts.append(ext(rect(u, mid - 0.25, u + lw, mid + 0.25), -1.2, -0.4))           # the split, a ledge
        gl = rect(pu0, mid + 1.0, pu1, top - st)
        glass = gl
        parts.append(ext(gl.offset(0.45, JoinType.Miter, 4.0) - gl, -0.8, -0.6))
        b = gl.bounds()
        m, vm = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
        _GLASS_BARS.append(ext((rect(m - 0.25, b[1], m + 0.25, b[3]) + rect(b[0], vm - 0.25, b[2], vm + 0.25)) ^ gl.offset(0.2),
                               -1.21, -0.6))
        lo = rect(pu0, 1.3, pu1, mid - 1.0)
        panel(lo)
        lb = lo.bounds()
        parts.append(ext(stroke([(lb[0] + 0.6, lb[1] + 0.6), (lb[2] - 0.6, lb[3] - 0.6)], 0.6, caps=False) ^ lo, -0.41, -0.2))
    elif style == "boards_glass":         # a tall light with a centre bar over a panel of upright boards
        gl = rect(pu0, dh * 0.34, pu1, top - st)
        glass = gl
        parts.append(ext(gl.offset(0.45, JoinType.Miter, 4.0) - gl, -0.8, -0.6))
        c = gl.bounds()
        _GLASS_BARS.append(ext(rect((c[0] + c[2]) / 2 - 0.25, c[1], (c[0] + c[2]) / 2 + 0.25, c[3]) ^ gl.offset(0.2), -1.21, -0.6))
        lo = rect(pu0, 1.3, pu1, dh * 0.34 - 1.0)
        parts.append(ext(lo, -0.81, -0.6))
        lb = lo.bounds()
        parts.append(ext(cs_union([rect(x - 0.25, lb[1] + 0.4, x + 0.25, lb[3] - 0.4)
                                   for x in np.arange(lb[0] + 1.0, lb[2] - 0.5, 1.0)]), -0.61, -0.4))
    elif style == "lozenge":              # a tall light with a lozenge of bars in it, over a panel
        gl = rect(pu0, dh * 0.36, pu1, top - st)
        glass = gl
        parts.append(ext(gl.offset(0.45, JoinType.Miter, 4.0) - gl, -0.8, -0.6))
        c = gl.bounds()
        cx, cy = (c[0] + c[2]) / 2, (c[1] + c[3]) / 2
        hx, hy = (c[2] - c[0]) / 2 - 0.3, (c[3] - c[1]) / 2 - 0.3
        loz = poly([(cx, cy + hy), (cx + hx, cy), (cx, cy - hy), (cx - hx, cy)])
        _GLASS_BARS.append(ext((loz - loz.offset(-0.5, JoinType.Miter, 4.0)) ^ gl.offset(0.2), -1.21, -0.6))
        panel(rect(pu0, 1.3, pu1, dh * 0.36 - 1.0))
    elif style == "keyhole":              # a keyhole-shaped light (a round head on a narrow shaft) over a panel
        cx = (pu0 + pu1) / 2
        rr = min((pu1 - pu0) / 2 - 0.3, 1.6)
        vc = top - st - rr - 0.3
        gl = circle((cx, vc), rr, 28) + rect(cx - rr * 0.55, dh * 0.45, cx + rr * 0.55, vc)
        glass = gl
        parts.append(ext(gl.offset(0.45, JoinType.Round) - gl, -0.8, -0.6))
        panel(rect(pu0, 1.3, pu1, dh * 0.45 - 1.0))
    elif style == "sunray":               # a square-headed light over a panel carved with a sunburst
        gl = rect(pu0, dh * 0.5, pu1, top - st)
        glass = gl
        parts.append(ext(gl.offset(0.45, JoinType.Miter, 4.0) - gl, -0.8, -0.6))
        pc = rect(pu0, 1.3, pu1, dh * 0.5 - 1.0)
        panel(pc)
        b = pc.bounds()
        cx, cy = (b[0] + b[2]) / 2, b[1] + 0.4
        rays = cs_union([stroke([(cx, cy), (cx + 9 * math.cos(a), cy + 9 * math.sin(a))], 0.5)
                         for a in np.linspace(0.35, math.pi - 0.35, 5)]) ^ pc.offset(-0.5, JoinType.Miter, 4.0)
        parts.append(ext(rays, -0.41, -0.2))
    elif style == "lace":                 # a tall round-headed light behind a lace grille, over a panel
        gw = pu1 - pu0
        gl = arch_cs(pu0, pu1, dh * 0.4, top - st - gw / 2, seg=24)
        glass = gl
        parts.append(ext(gl.offset(0.45, JoinType.Round) - gl, -0.8, -0.6))
        c = gl.bounds()
        cx = (c[0] + c[2]) / 2
        bars = [gl.offset(-0.9, JoinType.Round) - gl.offset(-1.45, JoinType.Round), rect(cx - 0.25, c[1], cx + 0.25, c[3])]
        for v in np.linspace(c[1] + 2.0, c[3] - 2.5, 3):
            bars.append(circle((cx, v), 0.75, 16) - circle((cx, v), 0.25, 10))
        _GLASS_BARS.append(ext(cs_union(bars) ^ gl.offset(0.2), -1.21, -0.6))
        panel(rect(pu0, 1.3, pu1, dh * 0.4 - 1.0))
    elif style == "twin_arch":            # two round-headed lights side by side over a raised panel
        gw = (pu1 - pu0 - 0.6) / 2
        gl = cs_union([arch_cs(a, a + gw, dh * 0.42, top - st - gw / 2, seg=16) for a in (pu0, pu0 + gw + 0.6)])
        glass = gl
        parts.append(ext(gl.offset(0.45, JoinType.Round) - gl, -0.8, -0.6))
        panel(rect(pu0, 1.3, pu1, dh * 0.42 - 1.0))
    elif style == "ledged":               # vertical planks on three ledges with Z braces between them
        g = []
        nb = max(2, int(lw / 1.2))
        for k in range(1, nb):
            x = u + lw * k / nb
            g.append(rect(x - 0.25, 0.9, x + 0.25, top - 0.4))
        parts[0] = parts[0] - ext(cs_union(g), -1.0, 0.0)
        ledges = [1.6, dh * 0.5, top - 1.6]
        for vv in ledges:
            parts.append(ext(rect(u + 0.4, vv - 0.5, u + lw - 0.4, vv + 0.5), -0.81, -0.4))
        for va, vb in zip(ledges[:-1], ledges[1:]):
            a0, a1 = (u + 0.6, va + 0.5), (u + lw - 0.6, vb - 0.5)
            if not hinge_left:
                a0, a1 = (u + lw - 0.6, va + 0.5), (u + 0.6, vb - 0.5)
            parts.append(ext(stroke([a0, a1], 0.8, caps=False) ^ rect(u, va, u + lw, vb), -0.81, -0.4))
    elif style == "roundel":              # a tall raised panel under a round light set in a square panel
        cx = (pu0 + pu1) / 2
        rr = min((pu1 - pu0) / 2 - 0.5, 1.6)
        sq = rect(pu0, top - st - (pu1 - pu0), pu1, top - st)
        vc = (sq.bounds()[1] + sq.bounds()[3]) / 2
        gl = circle((cx, vc), rr, 32)
        glass = gl
        parts.append(ext(sq - sq.offset(-0.45, JoinType.Miter, 4.0), -0.8, -0.6))
        parts.append(ext(gl.offset(0.45, JoinType.Round) - gl, -0.8, -0.6))
        panel(rect(pu0, 1.3, pu1, sq.bounds()[1] - 0.9))
    elif style == "bolection":            # a light over a panel ringed by a bolection moulding, a raised rosette in it
        gl = rect(pu0, dh * 0.52, pu1, top - st)
        glass = gl
        parts.append(ext(gl.offset(0.45, JoinType.Miter, 4.0) - gl, -0.8, -0.6))
        lo = rect(pu0 + 0.3, 1.5, pu1 - 0.3, dh * 0.52 - 1.2)
        parts.append(ext(lo.offset(0.5, JoinType.Miter, 4.0) - lo, -0.81, -0.4))
        lb = lo.bounds()
        parts.append(ext(circle(((lb[0] + lb[2]) / 2, (lb[1] + lb[3]) / 2), min(0.7, (lb[2] - lb[0]) * 0.3), 16), -0.81, -0.4))
    elif style == "oval":
        cx, cy = (pu0 + pu1) / 2, dh * 0.7
        rx, ry = (pu1 - pu0) / 2 - 0.2, min(dh * 0.18, top - st - cy)
        gl = poly([(cx + rx * math.cos(2 * math.pi * k / 40), cy + ry * math.sin(2 * math.pi * k / 40)) for k in range(40)])
        glass = gl
        parts.append(ext(gl.offset(0.5, JoinType.Round) - gl, -0.8, -0.55))
        lo = rect(pu0, 1.3, pu1, dh * 0.42)
        panel(lo)
        b = lo.bounds()
        mx, my = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
        parts.append(ext(poly([(mx, b[1] + 0.8), (b[2] - 0.7, my), (mx, b[3] - 0.8), (b[0] + 0.7, my)]), -0.41, -0.2))
    else:
        raise ValueError(style)
    if style != "studded":
        parts.append(ext(circle((kx, knob_v), 0.35, 12), -0.8, -0.4))
    return parts, glass


def door_ornate(w, h, leaves=2, transom=4.2, head="swan", pil=1.6, leaf="arched", tstyle="sunburst"):
    """Queen Anne entrance: ornate leaves (round-headed lights, quatrefoil panels), a
    sunburst transom, panelled pilasters on plinths with bullseye capitals, and either
    ``head="swan"``: a frieze with a cartouche and swags, a cornice and a broken swan-neck
    pediment with an urn, or ``head="pediment"``: a segmental pediment with a sunburst.
    Local frame as the windows (u centred, v from the sill, w out of the wall)."""
    op, plug_cs, sash_parts = _ornate_door_sash(w, h, leaves, transom, leaf, tstyle)
    parts = []
    return _door_ornate_surround(w, h, op, plug_cs, sash_parts, head, pil)


def _ornate_door_sash(w, h, leaves, transom, leaf="arched", tstyle="sunburst"):
    """The leaves and transom of a door (the plug part): leaf style (see _leaf) and a
    transom of style sunburst, plain (with an oval boss), stick (a row of narrow lights),
    diamond (a diamond grid), leaded (a border of small squares), ring (a ring on a cross of
    bars), twin (one bar), cross (a cross of bars), heart, scallop (three little arches),
    chevron, beads, grid (two rows of four lights), quatrefoil (four linked rings) or
    "number:<digits>" (the street number in
    raised gilt figures on the glass). One transom style per building."""
    op = rect(-w / 2, 0, w / 2, h)
    plug_cs = op.offset(-CLR, JoinType.Miter, 4.0)
    pl = PLUG
    dh = h - transom
    mid = SLOT if leaves > 1 else 0.0
    lw = (w - 2 * CLR - 1.0 - mid * (leaves - 1)) / leaves
    u = -w / 2 + CLR + 0.5
    parts, lights = [], []
    for i in range(leaves):
        lp, light = _leaf(leaf, u, lw, dh, hinge_left=(i == 0))
        parts += lp
        if light is not None:
            lights.append(light)
        u += lw + mid
    glass = cs_union(lights) if lights else CS()
    cut = ext(glass, -pl - 1, 0.0)
    parts = [p - cut for p in [ext(plug_cs, -pl, -1.0)] + parts] + _glass_bars()
    parts.append(ext(glass, -pl, -pl + GLASS))
    ring = plug_cs - plug_cs.offset(-0.5, JoinType.Miter, 4.0)
    parts.append(ext(ring, -pl, 0.0))
    if transom > 0:
        tcs = rect(-w / 2 + CLR + 0.5, dh + 0.2, w / 2 - CLR - 0.5, h - CLR - 0.5)
        parts = [p - ext(tcs, -pl - 1, -0.99) for p in parts]
        parts.append(ext(tcs, -pl, -pl + GLASS))
        parts.append(ext(rect(-w / 2, dh - 0.3, w / 2, dh + 0.3), -pl, -0.4))             # transom bar
        tb = tcs.bounds()
        if tstyle == "sunburst":
            hub, rays = sunburst((0.0, tb[1]), 1.0, 1.6, max(tb[2], tb[3] - tb[1]) + 2.0, n=7, a0=0.2, a1=math.pi - 0.2,
                                 ray0=RIB, ray1=RIB + 0.1)
            pat = hub + rays
        elif tstyle == "plain":
            cy = (tb[1] + tb[3]) / 2
            pat = oval((0.0, cy), min(2.2, (tb[2] - tb[0]) * 0.2), min(1.1, (tb[3] - tb[1]) * 0.36))
        elif tstyle == "stick":
            n = max(3, int((tb[2] - tb[0]) / 1.5))
            pat = cs_union([rect(tb[0] + (tb[2] - tb[0]) * k / n - 0.25, tb[1] - 1, tb[0] + (tb[2] - tb[0]) * k / n + 0.25,
                                 tb[3] + 1) for k in range(1, n)])
        elif tstyle == "diamond":
            bars = []
            for sgn in (-1, 1):
                for k in range(-12, 13):
                    x0 = k * 1.8
                    bars.append(stroke([(x0 - sgn * 8, tb[1] - 8), (x0 + sgn * 8, tb[1] + 8)], RIB, caps=False))
            pat = cs_union(bars)
        elif tstyle.startswith("number") or tstyle.startswith("text"):
            from .storefront import text_cs
            digits = tstyle.split(":", 1)[1] if ":" in tstyle else "12"
            cap = min(2.6, (tb[3] - tb[1]) - 0.6)
            pat = text_cs(digits, cap, "serif", grow=0.1).translate((0.0, (tb[1] + tb[3]) / 2 - cap / 2))
        elif tstyle == "ring":
            cy = (tb[1] + tb[3]) / 2
            r = min((tb[3] - tb[1]) / 2 - 0.2, (tb[2] - tb[0]) / 2 - 0.4)
            pat = (circle((0.0, cy), r + RIB / 2, 32) - circle((0.0, cy), r - RIB / 2, 32)) + \
                rect(tb[0] - 1, cy - RIB / 2, tb[2] + 1, cy + RIB / 2) + rect(-RIB / 2, tb[1] - 1, RIB / 2, tb[3] + 1)
        elif tstyle == "arch":                   # a round arch bar springing from the transom's foot
            cx, r = 0.0, min((tb[2] - tb[0]) / 2 - 0.5, (tb[3] - tb[1]) - 0.5)
            pat = (circle((cx, tb[1]), r + RIB / 2, 40) - circle((cx, tb[1]), r - RIB / 2, 40))
        elif tstyle == "heart":                  # a raised heart in the middle of the light
            cy = (tb[1] + tb[3]) / 2
            r = min((tb[3] - tb[1]) * 0.28, 0.9)
            pat = cs_union([circle((-r * 0.75, cy + r * 0.35), r, 20), circle((r * 0.75, cy + r * 0.35), r, 20),
                            poly([(-r * 1.6, cy + 0.1), (r * 1.6, cy + 0.1), (0.0, cy - r * 1.9)])])
        elif tstyle == "twin":                   # one upright bar: two lights
            pat = rect(-RIB / 2, tb[1] - 1, RIB / 2, tb[3] + 1)
        elif tstyle == "cross":                  # a cross of bars: four lights
            cy = (tb[1] + tb[3]) / 2
            pat = rect(-RIB / 2, tb[1] - 1, RIB / 2, tb[3] + 1) + rect(tb[0] - 1, cy - RIB / 2, tb[2] + 1, cy + RIB / 2)
        elif tstyle == "chevron":                # a zigzag bar across the light
            n = max(2, int((tb[2] - tb[0]) / 2.2))
            pts = [(tb[0] - 0.5 + (tb[2] - tb[0] + 1.0) * k / (2 * n), tb[1] + 0.3 if k % 2 == 0 else tb[3] - 0.3)
                   for k in range(2 * n + 1)]
            pat = stroke(pts, RIB, caps=False)
        elif tstyle == "beads":                  # a row of round beads on a bar across the light
            cy = (tb[1] + tb[3]) / 2
            n = max(3, int((tb[2] - tb[0]) / 1.4))
            pat = rect(tb[0] - 1, cy - RIB / 2, tb[2] + 1, cy + RIB / 2) + \
                cs_union([circle((tb[0] + (tb[2] - tb[0]) * (k + 0.5) / n, cy), 0.45, 16) for k in range(n)])
        elif tstyle == "scallop":                # a row of three small round arch bars on the transom's foot
            p = (tb[2] - tb[0]) / 3
            r = min(p / 2 - 0.1, (tb[3] - tb[1]) - 0.5)
            pat = cs_union([circle((tb[0] + p * (k + 0.5), tb[1]), r + RIB / 2, 28) -
                            circle((tb[0] + p * (k + 0.5), tb[1]), r - RIB / 2, 28) for k in range(3)])
        elif tstyle == "grid":                   # two rows of four small lights
            cy = (tb[1] + tb[3]) / 2
            pat = rect(tb[0] - 1, cy - RIB / 2, tb[2] + 1, cy + RIB / 2) + \
                cs_union([rect(tb[0] + (tb[2] - tb[0]) * k / 4 - RIB / 2, tb[1] - 1, tb[0] + (tb[2] - tb[0]) * k / 4 + RIB / 2,
                               tb[3] + 1) for k in (1, 2, 3)])
        elif tstyle == "quatrefoil":             # four linked rings in the middle of the light, on a bar
            cy = (tb[1] + tb[3]) / 2
            r = min((tb[3] - tb[1]) * 0.25, 0.9)
            rings = [circle((dx, cy + dy), r + RIB / 2, 20) - circle((dx, cy + dy), r - RIB / 2, 20)
                     for dx, dy in ((-r, 0.0), (r, 0.0), (0.0, -r), (0.0, r))]
            pat = cs_union(rings) + rect(tb[0] - 1, cy - RIB / 2, -2 * r, cy + RIB / 2) + rect(2 * r, cy - RIB / 2, tb[2] + 1, cy + RIB / 2)
        elif tstyle == "leaded":
            inner = tcs.offset(-1.1, JoinType.Miter, 4.0)
            bars = [inner.offset(RIB / 2, JoinType.Miter, 4.0) - inner.offset(-RIB / 2, JoinType.Miter, 4.0)]
            n = max(2, int((tb[2] - tb[0]) / 1.2))
            for k in range(1, n):
                x = tb[0] + (tb[2] - tb[0]) * k / n
                bars.append(rect(x - RIB / 2, tb[1] - 1, x + RIB / 2, tb[3] + 1) - inner.offset(-RIB / 2, JoinType.Miter, 4.0))
            pat = cs_union(bars)
        else:
            raise ValueError(tstyle)
        parts.append(ext(pat ^ tcs, -pl + GLASS - 0.01, -0.6))
    return op, plug_cs, parts


def _door_ornate_surround(w, h, op, plug_cs, sash_parts, head, pil):
    parts = []
    # opening lip and inner bead
    parts.append(ext((op - op.offset(-RIB, JoinType.Miter, 4.0)) ^ rect(-w, 0.5, w, h + 1), 0.0, CAS))
    parts.append(ext((op.offset(RIB, JoinType.Miter, 4.0) - op) ^ rect(-w, 0, w, h + 1), CAS, BEAD))
    # pilasters with a sunk, round-ended flute; plinths; bullseye capitals
    for sg in (-1, 1):
        u0, u1 = sorted((sg * w / 2, sg * (w / 2 + pil)))
        um = (u0 + u1) / 2
        body = ext(rect(u0, 2.2, u1, h + 0.2), 0.0, 0.8)
        flute = ext(stroke([(um, 3.4), (um, h - 1.2)], 0.6), 0.4, 1.0)
        parts.append(body - flute)
        parts.append(chamfer_box(u0 - 0.15, 0.0, u1 + 0.15, 2.2, 0.0, 1.0, c=0.4))
        parts.append(bullseye(um, h + 2.2 - (pil + 0.4) / 2, pil + 0.4, 0.0, 1.2))
    cw = w / 2 + pil + 0.5
    if head == "swan":
        # frieze: cartouche and swags between rosettes
        parts.append(ext(rect(-w / 2, h, w / 2, h + 2.4), 0.0, CAS))        # into the cornice: one piece
        parts.append(ext(oval((0.0, h + 1.1), 1.4, 0.85), CAS - 0.01, 1.0))
        parts.append(ext(oval((0.0, h + 1.1), 0.75, 0.42), 1.0 - 0.01, 1.2))
        sw_ = []
        for sg in (-1, 1):
            a, b = sg * 1.25, sg * (w / 2 - 0.5)
            sw_.append(swag(min(a, b), max(a, b), h + 1.75, 0.9, 0.6))
            parts.append(ext(circle((b, h + 1.75), 0.42, 16), CAS - 0.01, 1.2))
        parts.append(ext(cs_union(sw_), CAS - 0.01, 1.0))
        # cornice
        parts.append(ext(rect(-cw, h + 2.2, cw, h + 2.8), 0.0, 1.4))
        parts.append(ext(rect(-cw - 0.3, h + 2.8, cw + 0.3, h + 3.2), 0.0, 1.8))
        vc = h + 3.2
        necks, fields, ros = [], [], []
        for sg in (-1, 1):
            p0 = (sg * (cw - 0.45), vc + 0.4)
            p3 = (sg * 2.1, vc + 3.1)
            pts = bezier(p0, (sg * cw * 0.55, vc + 0.4), (sg * cw * 0.5, vc + 3.1), p3, 28)
            necks.append(stroke(pts, 0.8))
            fields.append(poly([tuple(p) for p in pts] + [(p3[0], vc - 0.2), (p0[0], vc - 0.2)]))     # into the cornice
            necks.append(volute((p3[0], p3[1] - 0.6), 0.95, turns=0.85, band=0.55, a0=math.pi / 2,
                                sense=1 if sg > 0 else -1))
            ros.append(circle((sg * (cw * 0.62), vc + 1.0), 0.45, 16))
        parts.append(ext(cs_union(fields), 0.0, CAS))
        parts.append(ext(cs_union(necks), 0.0, 1.2))
        parts.append(ext(cs_union([stroke(bezier((sg * (cw - 0.45), vc + 0.4), (sg * cw * 0.55, vc + 0.4),
                                                 (sg * cw * 0.5, vc + 3.1), (sg * 2.1, vc + 3.1), 28), 0.5)
                                   for sg in (-1, 1)]), 1.2 - 0.01, 1.6))
        parts.append(ext(cs_union(ros), CAS - 0.01, 1.0))
        parts.append(ext(urn_cs(0.0, vc, 3.4, 1.9) + rect(-0.6, vc - 0.2, 0.6, vc + 0.3), 0.0, 1.2))
        parts.append(ext(circle((0.0, vc + 3.4 * 3.35 / 4), 0.38, 16), 1.2 - 0.01, 1.4))
        top = vc + 3.6
    else:
        parts.append(ext(rect(-w / 2, h, w / 2, h + 2.4), 0.0, CAS))        # into the pediment: one piece
        parts.append(ext(cs_union([swag(-w / 2 + 0.6, -0.4, h + 1.6, 0.7, 0.6), swag(0.4, w / 2 - 0.6, h + 1.6, 0.7, 0.6),
                                   circle((0.0, h + 1.5), 0.5, 16)]), CAS - 0.01, 1.0))
        head_, top = _pediment_head(cw - 0.3, h + 2.2, rise_in=3.0)
        parts += head_
        parts.append(ext(cs_union([stroke([(0.0, top - 0.2), (0.0, top + 0.5)], 0.6), circle((0.0, top + 0.85), 0.5, 16)]),
                         0.0, 1.2))
        top += 1.35
    return _one_piece(sash_parts, parts, op, plug_cs, PLUG, top, 0.0)


# ------------------------------------------------------------------ Second Empire surrounds
# Sculpted mouldings (hoarch.moulding): every casing, hood and shelf has a real profile built
# as a height field on the 0.2 mm grid, so it prints face-up as clean nested perimeters.

def window_se(w, h, rise=None, head="hood", lites=(1, 1), arch_w=2.0, apron=True, sill_consoles=True, hood_w=1.4):
    """Second Empire window: an eared, moulded architrave and a sculpted head.

    head "pediment": frieze, scroll consoles, a moulded shelf and a segmental pediment with a
                     cartouche in the tympanum (first floor);
    head "hood":     a crowned drip hood following the arch, returned at the spring line over
                     drop pendants, with a scroll keystone rising into a palmette crest;
    head "cap":      a moulded cornice cap on consoles, no pediment (where headroom is short).
    Sill: a moulded nose on two small consoles, and (apron) a panelled apron with a drop."""
    from . import moulding as MD
    rise = w / 2 if rise is None else rise
    spring = h - rise
    op = opening_cs(w, h, rise)
    plug_cs = op.offset(-CLR, JoinType.Miter, 4.0)
    sash = window_insert(w, h, rise, lites=lites, bare=True)["insert"]
    A = arch_w
    parts = []
    # --- eared architrave (crossettes at the head), no casing under the sill
    v_ear = spring if rise > 0 else h
    outer = op.offset(A, JoinType.Miter, 4.0)
    ears = cs_union([rect(-w / 2 - A - 0.6, v_ear - 1.8, -w / 2, v_ear + (A if rise == 0 else 0.6)),
                     rect(w / 2, v_ear - 1.8, w / 2 + A + 0.6, v_ear + (A if rise == 0 else 0.6))])
    outer = cs_union([outer, ears])
    above_sill = rect(-w - 10, 0.0, w + 10, h + 40)
    parts.append(MD.band(outer, A + 0.6, MD.ARCHITRAVE, clip=above_sill - op))
    parts.append(ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, CAS))      # lip over the sash frame
    half = w / 2 + A + 0.6                       # outer half-width at the ears
    top = h + A
    if head in ("pediment", "cap"):
        v0 = (h if rise == 0 else h) + A          # top of the architrave (flat head)
        if rise > 0:
            v0 = spring + rise + A
        # frieze with rosettes over the consoles
        parts.append(ext(rect(-half, v0 - 0.2, half, v0 + 1.8), 0.0, CAS))
        for sg in (-1, 1):
            parts.append(MD.rosette(sg * (half - 0.7), v0 + 0.8, 0.62, CAS - 0.01, 0.6))
            parts.append(console(3.6, 1.8, 1.2, u=sg * (half - 0.7), v_top=v0 - 0.2, w0=0.0))
        # moulded shelf, returned past the consoles
        vs = v0 + 1.8
        parts.append(MD.run(-half - 0.6, half + 0.6, vs + 1.2, MD.CROWN, 1.2, up=False))
        top = vs + 1.2
        if head == "pediment":
            rise_p = 2.6
            seg = arch_cs(-half - 0.3, half + 0.3, vs + 1.2 - 0.01, vs + 1.2, rise=rise_p, seg=48)
            parts.append(MD.band(seg, 1.1, MD.CROWN, clip=rect(-half - 2, vs + 1.2, half + 2, vs + 10)))
            tymp = seg.offset(-1.0, JoinType.Round) ^ rect(-half, vs + 1.2, half, vs + 10)
            parts.append(ext(tymp, 0.0, CAS))
            parts.append(cartouche_or_fan(vs + 1.2, rise_p, half))
            top = vs + 1.2 + rise_p
    else:  # "hood": crowned drip hood following the head, stopped at the spring line on corbels
        HB = hood_w
        hood_out = op.offset(A + HB, JoinType.Miter, 4.0)
        vcut = v_ear if rise > 0 else h + A
        parts.append(MD.band(hood_out, HB, MD.CROWN, clip=rect(-w - 10, vcut, w + 10, h + 40)))
        if rise > 0:
            for sg in (-1, 1):
                u0, u1 = sorted((sg * (w / 2 + A - 0.2), sg * (w / 2 + A + HB + 0.8)))
                parts.append(MD.run(u0, u1, vcut, MD.CROWN, 1.2, up=False))          # label stop
                parts.append(console(2.4, 1.6, 1.2, u=sg * (w / 2 + A + HB * 0.5 + 0.2), v_top=vcut - 1.0, w0=0.0))
        crown_v = (h + A + HB) if rise == 0 else (spring + rise + A + HB)
        kv0 = h - 0.2
        parts.append(MD.scroll_keystone(0.0, kv0, crown_v + 1.0 - kv0, 1.6, 2.4, 0.0, 2.0))
        parts.append(MD.anthemion((0.0, crown_v + 0.8), 4.0, 3.0, 0.0, 1.2))
        top = crown_v + 0.8 + 3.0
    # --- sill: moulded nose on two small consoles, panelled apron with a drop
    sw = half + 0.3
    parts.append(MD.run(-sw, sw, 0.0, MD.SILL, 1.0, up=False))
    bottom = -1.0
    if sill_consoles:
        for sg in (-1, 1):
            parts.append(console(1.8, 1.0, 0.8, u=sg * (w / 2 + A / 2), v_top=-0.8, w0=0.0))
        bottom = -2.8
    if apron:
        aw = w / 2 + A * 0.5
        field = rect(-aw + 1.0, -3.2, aw - 1.0, -1.0)
        parts.append(ext(field, 0.0, CAS))
        parts.append(chamfer_box(-aw + 1.6, -2.7, aw - 1.6, -1.5, CAS, 0.4, c=0.25))
        parts.append(MD.pendant(0.0, -3.0, 2.0, 0.0, 0.8))
        bottom = min(bottom, -5.0)
    return _one_piece([sash], parts, op, plug_cs, PLUG, top, bottom)


def cartouche_or_fan(v_base, rise_p, half):
    """Tympanum ornament of a segmental pediment: a cartouche if it fits, else a fan."""
    from . import moulding as MD
    hc = rise_p - 0.6
    if hc >= 1.8 and half >= 4.0:
        return MD.cartouche((0.0, v_base + 0.2 + hc / 2), min(3.2, half * 0.55), hc, CAS - 0.01, 0.8)
    hub, rays = sunburst((0.0, v_base), 0.0, 0.5, rise_p - 0.4, n=5, a0=0.2, a1=math.pi - 0.2, ray0=0.45, ray1=0.7)
    return ext(rays, CAS - 0.01, 1.0)


def door_se(w, h, leaves=2, transom=4.4, pil=2.0, arch_w=1.8, head="pediment", leaf="arched", tstyle="sunburst"):
    """Second Empire entrance: the ornate leaves and fanlight of door_ornate in a moulded
    architrave, fluted pilasters on plinths with moulded capitals, an entablature (frieze
    with a cartouche between rosettes, dentils, a crowned cornice returned over the
    pilasters) and a segmental pediment with a fan and a palmette on the apex."""
    from . import moulding as MD
    op, plug_cs, sash_parts = _ornate_door_sash(w, h, leaves, transom, leaf, tstyle)
    A = arch_w
    parts = []
    outer = op.offset(A, JoinType.Miter, 4.0)
    parts.append(MD.band(outer, A, MD.ARCHITRAVE, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op))
    parts.append(ext((op - op.offset(-RIB, JoinType.Miter, 4.0)) ^ rect(-w, 0.5, w, h + 1), 0.0, CAS))
    # fluted pilasters on plinths with moulded capitals
    ui, uo = w / 2 + A, w / 2 + A + pil
    vcap = h + A
    for sg in (-1, 1):
        u0, u1 = sorted((sg * ui, sg * uo))
        um = (u0 + u1) / 2
        body = ext(rect(u0, 2.6, u1, vcap), 0.0, 1.0)
        flute = ext(stroke([(um, 3.6), (um, vcap - 1.0)], 0.6), 0.6, 1.2)
        parts.append(body - flute)
        parts.append(chamfer_box(u0 - 0.2, 0.0, u1 + 0.2, 2.6, 0.0, 1.2, c=0.4))
        parts.append(MD.run(u0 - 0.3, u1 + 0.3, vcap, MD.CROWN, 1.0, up=False))
    # entablature: frieze with a cartouche between rosettes, dentils, crowned cornice
    half = uo + 0.3
    parts.append(ext(rect(-half, vcap, half, vcap + 2.8), 0.0, CAS))
    parts.append(MD.cartouche((0.0, vcap + 1.4), 4.2, 2.4, CAS - 0.01, 0.8))
    for sg in (-1, 1):
        parts.append(MD.rosette(sg * (ui + pil / 2), vcap + 1.4, 0.8, CAS - 0.01, 0.6))
    parts.append(dentils(-half + 0.3, half - 0.3, vcap + 2.6, 1.1, 0.0, 1.2))     # into the frieze and cornice
    vs = vcap + 3.5
    parts.append(MD.run(-half - 0.7, half + 0.7, vs + 1.4, MD.CROWN, 1.4, up=False))
    vb = vs + 1.4
    if head == "entablature":
        # an Italianate door hood: the cornice carried on two big scroll consoles over the
        # pilaster capitals, a low blocking course with a palmette in the middle
        for sg in (-1, 1):
            parts.append(console(4.2, 2.2, 1.4, u=sg * (ui + pil / 2), v_top=vs + 0.2, w0=0.0))
        parts.append(ext(rect(-half + 0.8, vb, half - 0.8, vb + 0.8), 0.0, 1.0))
        parts.append(MD.anthemion((0.0, vb + 0.6), 4.4, 2.8, 0.0, 1.2))
        top = vb + 0.6 + 2.8
        return _one_piece(sash_parts, parts, op, plug_cs, PLUG, top, 0.0)
    # segmental pediment with a fan in the tympanum and a palmette on the apex
    rise_p = 3.4
    seg = arch_cs(-half - 0.4, half + 0.4, vb - 0.01, vb, rise=rise_p, seg=60)
    parts.append(MD.band(seg, 1.2, MD.CROWN, clip=rect(-half - 2, vb, half + 2, vb + 10)))
    tymp = seg.offset(-1.1, JoinType.Round) ^ rect(-half, vb, half, vb + 10)
    parts.append(ext(tymp, 0.0, CAS))
    hub, rays = sunburst((0.0, vb), 0.0, 1.0, rise_p - 0.6, n=7, a0=0.25, a1=math.pi - 0.25, ray0=0.5, ray1=0.8)
    parts.append(ext((rays ^ tymp.offset(-0.3, JoinType.Round)), CAS - 0.01, 1.0))
    parts.append(ext(arch_cs(-1.2, 1.2, vb - 0.01, vb, rise=1.2, seg=24), CAS - 0.01, 1.2))
    parts.append(MD.anthemion((0.0, vb + rise_p - 0.2), 4.0, 3.0, 0.0, 1.2))
    top = vb + rise_p - 0.2 + 3.0
    return _one_piece(sash_parts, parts, op, plug_cs, PLUG, top, 0.0)


# ------------------------------------------------------------------ Gothic Revival surrounds
# Pointed (two-centred) openings with bar tracery in the sash, a moulded casing, and a drip
# label (hood mould) that stops on carved label stops at the spring line. The label can carry
# crockets (curled leaves climbing its back) and a fleur finial, or a crocketed gablet.

def _outline_top(cs, v_min):
    """The boundary of ``cs`` above v_min, left spring -> apex -> right spring, as an array."""
    import numpy as np
    pts = max(cs.to_polygons(), key=lambda L: abs(poly(L).area()))
    pts = np.asarray(pts, float)
    if poly(pts.tolist()).area() < 0:
        pts = pts[::-1]
    n = len(pts)
    start = int(np.argmin(pts[:, 1]))                  # rotate so the run above v_min is contiguous
    pts = np.roll(pts, -start, axis=0)
    keep = pts[:, 1] > v_min
    idx = np.nonzero(keep)[0]
    run = pts[idx[0]:idx[-1] + 1]
    return run[::-1]                                   # CCW runs right side first: flip to left first


def _resample(run, pitch, skip0, skip1):
    """Points every ``pitch`` along a polyline, skipping ``skip0``/``skip1`` at its two ends,
    with the unit tangent (along the run) at each. Returns [(p, t)]."""
    import numpy as np
    seg = np.diff(run, axis=0)
    ln = np.hypot(seg[:, 0], seg[:, 1])
    cum = np.concatenate([[0.0], np.cumsum(ln)])
    total = cum[-1]
    out = []
    s = skip0
    while s <= total - skip1 + 1e-9:
        i = min(int(np.searchsorted(cum, s, side="right")) - 1, len(seg) - 1)
        f = (s - cum[i]) / max(ln[i], 1e-9)
        out.append((run[i] + f * seg[i], seg[i] / max(ln[i], 1e-9)))
        s += pitch
    return out


def crockets(outline, v_min, apex_clear=1.6, pitch=2.5, w1=2.0, size=0.65):
    """Crockets climbing the outer edge of a hood or gablet ``outline`` above v_min: small
    curled leaves, each a boss with a tip hooked up toward the apex, rooted 0.3 into the
    hood. Printed face-up to w1. The two sides mirror each other about the apex."""
    import numpy as np
    run = _outline_top(outline, v_min)
    k = int(np.argmax(run[:, 1]))
    leaves = []
    for side, part in ((0, run[:k + 1]), (1, run[k:][::-1])):
        for p, t in _resample(part, pitch, 1.2, apex_clear):
            nrm = np.array([t[1], -t[0]]) if side == 0 else np.array([-t[1], t[0]])   # outward
            c = p + nrm * (size - 0.3)
            tip = p + nrm * (size + 0.55) + t * 0.9
            leaf = cs_union([circle(tuple(c), size, 16),
                             poly([tuple(c - t * size * 0.8), tuple(c + nrm * size * 0.9), tuple(tip),
                                   tuple(c + t * size * 0.2)])])
            leaves.append(leaf)
    if not leaves:
        return None
    cs = cs_union(leaves).offset(-0.25, JoinType.Round).offset(0.25, JoinType.Round)
    return stepped(cs, [(0.0, 0.0, w1 - 0.4), (0.2, w1 - 0.4, w1)])


def fleur(u, v0, w0=0.0, d=1.6, s=1.0):
    """Fleur finial standing on (u, v0): a collar, a tall middle petal and two side petals."""
    cs = cs_union([rect(u - 0.4 * s, v0 - 0.5, u + 0.4 * s, v0 + 1.6 * s),
                   rect(u - 1.0 * s, v0 + 0.3 * s, u + 1.0 * s, v0 + 1.05 * s),
                   circle((u, v0 + 1.8 * s), 0.6 * s, 20),
                   poly([(u - 0.5 * s, v0 + 1.9 * s), (u + 0.5 * s, v0 + 1.9 * s), (u, v0 + 3.1 * s)]),
                   circle((u - 1.05 * s, v0 + 1.35 * s), 0.5 * s, 16), circle((u + 1.05 * s, v0 + 1.35 * s), 0.5 * s, 16)])
    return stepped(cs, [(0.0, w0, w0 + d - 0.4), (0.2, w0 + d - 0.4, w0 + d)])


def _gothic_bars(inner, w, h, spring, k, lights, mr):
    """Tracery bars (CrossSection, before clipping to ``inner``) for a pointed light.
    lights: "twin" (a mullion under two sub-lancets with an oculus in the head),
            "diamond" (leaded quarries), "cross" (mullion and transom), "plain" (one bar)."""
    from .core import pointed_cs, pointed_rise
    from .features import _largest_hole
    b = 0.55
    bars = []
    if lights == "twin":
        subs = [pointed_cs(-w / 2, 0.0, -2.0, spring, k), pointed_cs(0.0, w / 2, -2.0, spring, k)]
        for sb in subs:
            bars.append(sb.offset(b / 2, JoinType.Miter, 4.0) - sb.offset(-b / 2, JoinType.Miter, 4.0))
        bars.append(rect(-w, mr - b / 2, w, mr + b / 2))
        spand = inner.offset(-0.5, JoinType.Miter, 4.0) - cs_union(subs).offset(b / 2 + 0.5, JoinType.Miter, 4.0)
        spand = spand ^ rect(-w, spring, w, h + 5)
        hole = _largest_hole(spand, (0.0, h), min_r=0.5, max_r=3.0) if not spand.is_empty() else None
        if hole is not None:
            (cx, cy), r = hole
            bars.append(circle((cx, cy), r + 0.45, 32) - circle((cx, cy), max(r - 0.1, 0.3), 32))
            if r >= 1.3:                                        # cusp it into a quatrefoil
                q = quatrefoil((cx, cy), r * 0.42, 20)
                bars.append(circle((cx, cy), r + 0.1, 32) - q.offset(0.0))
    elif lights == "diamond":
        ang = math.radians(58.0)
        pitch = 1.9
        L = h + w + 10
        for sgn in (-1, 1):
            du, dv = math.cos(ang) * sgn, math.sin(ang)
            for i in range(-int(L / pitch) - 2, int(L / pitch) + 3):
                u0 = i * pitch
                a = (u0 - du * L, -dv * L)
                c = (u0 + du * L, dv * L)
                nx, ny = -dv * (b / 2) / 1.0, du * (b / 2)
                bars.append(poly([(a[0] + nx, a[1] + ny), (c[0] + nx, c[1] + ny), (c[0] - nx, c[1] - ny),
                                  (a[0] - nx, a[1] - ny)]) if sgn > 0 else
                            poly([(a[0] - nx, a[1] - ny), (c[0] - nx, c[1] - ny), (c[0] + nx, c[1] + ny),
                                  (a[0] + nx, a[1] + ny)]))
        bars.append(rect(-w, mr - b / 2, w, mr + b / 2))
    elif lights == "cross":
        bars += [rect(-b / 2, -1, b / 2, h + 5), rect(-w, mr - b / 2, w, mr + b / 2)]
    else:
        bars.append(rect(-w, mr - b / 2, w, mr + b / 2))
    return cs_union(bars)


def window_gothic(w, h, k=1.0, lights="twin", head="label", arch_w=1.4, hood_w=1.2, crocket=True, finial=True,
                  stops=True, apron=False, flat=False):
    """Gothic Revival window: a pointed opening (k: see core.pointed_cs) with tracery,
    a moulded casing, a sill on two corbels and a sculpted head:

    head "label":  a drip label following the arch, returned at the spring line onto carved
                   label stops (a block with a rosette over a small drop), crockets climbing
                   its back and a fleur finial at the apex (``crocket``/``finial``);
    head "gablet": a steep crocketed gablet over the label, with a quatrefoil in the
                   tympanum and a fleur on top;
    head "tudor":  (with ``flat=True``: a square-headed opening) a square drip label whose
                   ends drop down the sides onto the stops.
    """
    from . import moulding as MD
    from .core import pointed_cs, pointed_rise
    rise = 0.0 if flat else pointed_rise(w, k)
    spring = h - rise
    op = rect(-w / 2, 0.0, w / 2, h) if flat else pointed_cs(-w / 2, w / 2, 0.0, spring, k)
    plug_cs = op.offset(-CLR, JoinType.Miter, 4.0)
    pl = PLUG
    frame_w = 0.55
    inner = plug_cs.offset(-frame_w, JoinType.Miter, 4.0)
    mr = spring * 0.5 if not flat else h * 0.46
    sash_parts = [ext(plug_cs, -pl, -pl + GLASS),
                  ext(plug_cs - inner, -pl, 0.0)]
    bars = _gothic_bars(inner, w, h, spring if not flat else h, k, lights, mr) ^ inner
    sash_parts.append(ext(bars, -pl + GLASS, -SASH_REC))
    A, HB = arch_w, hood_w
    parts = []
    above_sill = rect(-w - 20, 0.0, w + 20, h + 60)
    parts.append(MD.band(op.offset(A, JoinType.Miter, 4.0), A, MD.CASING, clip=above_sill - op))
    parts.append(ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, CAS))      # lip over the sash frame
    hood_out = op.offset(A + HB, JoinType.Miter, 4.0)
    ob = hood_out.bounds()
    v_stop = spring if not flat else h - min(h * 0.28, 6.0)        # where the label turns out onto its stops
    parts.append(MD.band(hood_out, HB, MD.CROWN, clip=rect(-w - 20, v_stop, w + 20, h + 60)))
    top = ob[3]
    if stops:
        for sg in (-1, 1):
            u0, u1 = sorted((sg * (w / 2 + A - 0.2), sg * (w / 2 + A + HB + 0.9)))
            parts.append(MD.run(u0, u1, v_stop, MD.CROWN, 1.2, up=False))
            uc = sg * (w / 2 + A + HB * 0.5 + 0.35)
            parts.append(chamfer_box(uc - 0.85, v_stop - 3.0, uc + 0.85, v_stop - 0.9, 0.0, 1.0, c=0.35))
            parts.append(MD.rosette(uc, v_stop - 1.95, 0.62, 0.8, 0.8))
            parts.append(MD.pendant(uc, v_stop - 2.8, 1.8, 0.0, 0.8))
    if head == "gablet" and not flat:
        gw = w / 2 + A + HB + 0.6
        gb = spring + 0.2
        gt = top + 3.2
        tri = poly([(-gw, gb), (gw, gb), (0.0, gt)])
        parts.append(MD.band(tri, 1.1, MD.CROWN, clip=rect(-w - 20, gb + 1.1, w + 20, h + 60) - hood_out.offset(-0.2)))
        tymp = (tri.offset(-1.0, JoinType.Miter, 4.0) - hood_out.offset(0.2, JoinType.Miter, 4.0)) ^ rect(-gw, gb + 1.1, gw, gt)
        tymp = tymp.offset(-0.3, JoinType.Round).offset(0.3, JoinType.Round)
        parts.append(ext(tymp, 0.0, CAS))
        tb = tymp.bounds() if not tymp.is_empty() else None
        if tb is not None and (tb[3] - tb[1]) > 2.4:
            qv = tb[3] - 1.5
            parts.append(ext(quatrefoil((0.0, qv), 0.5, 16), CAS - 0.01, CAS + 0.6))
        if crocket:
            cr = crockets(tri, gb + 2.0, apex_clear=1.4, pitch=2.2)
            if cr is not None:
                parts.append(cr - ext(hood_out, -1.0, 5.0))
        if finial:
            parts.append(fleur(0.0, gt - 0.6, 0.0, 1.6, 0.9))
            top = gt - 0.6 + 3.1 * 0.9
        else:
            top = gt
    else:
        if crocket and not flat:
            cr = crockets(hood_out, spring + 1.4)
            if cr is not None:
                parts.append(cr)
        if finial and not flat:
            parts.append(fleur(0.0, top - 0.4, 0.0, 1.6, 0.9))
            top = top - 0.4 + 3.1 * 0.9
        elif flat:
            # a carved boss in the middle of a square label
            parts.append(MD.rosette(0.0, h + A + HB * 0.5, 0.7, 1.0, 1.2))
    # sill: a moulded nose on two small corbels, or a panelled apron
    sw = w / 2 + A + 0.4
    parts.append(MD.run(-sw, sw, 0.0, MD.SILL, 1.0, up=False))
    bottom = -1.0
    if apron:
        aw = w / 2 + A * 0.5
        parts.append(ext(rect(-aw + 0.6, -3.0, aw - 0.6, -0.8), 0.0, CAS))
        parts.append(ext(quatrefoil((0.0, -1.9), 0.45, 16), CAS - 0.01, CAS + 0.6))
        bottom = -3.0
    else:
        for sg in (-1, 1):
            parts.append(chamfer_box(sg * (w / 2 + A * 0.5) - 0.6, -2.4, sg * (w / 2 + A * 0.5) + 0.6, -0.8,
                                     0.0, 0.8, c=0.3, bottom=0.6))
        bottom = -2.4
    return _one_piece(sash_parts, parts, op, plug_cs, PLUG, top, bottom)


def door_gothic(w, h, k=1.0, shaft=1.6, arch_w=1.6, hood_w=1.3, leaves=2):
    """Gothic Revival entrance: a pointed doorway with a traceried fanlight (twin sub-arches
    and a cusped oculus) over boarded leaves carrying long strap hinges with spear ends and a
    ring boss; the arch is moulded and carried on engaged shafts (colonnettes with bell
    capitals and moulded bases); a crocketed drip label on carved stops and a fleur finial."""
    from . import moulding as MD
    from .core import pointed_cs, pointed_rise
    rise = pointed_rise(w, k)
    spring = h - rise
    op = pointed_cs(-w / 2, w / 2, 0.0, spring, k)
    plug_cs = op.offset(-CLR, JoinType.Miter, 4.0)
    pl = PLUG
    # --- plug: boarded leaves below the spring line, glazed tracery in the head
    head_cs = plug_cs ^ rect(-w, spring + 0.3, w, h + 5)
    leaf_cs = plug_cs ^ rect(-w, 0.5, w, spring - 0.3)
    sash = [ext(plug_cs, -pl, -1.0)]
    boards = ext(leaf_cs, -1.0, -0.6)
    pitch = 1.6
    grooves = []
    n = int(w / pitch) + 2
    for i in range(-n, n + 1):
        u = i * pitch
        if abs(u) < 0.3:
            continue
        grooves.append(rect(u - 0.25, 0.9, u + 0.25, spring - 0.8))
    boards = boards - ext(cs_union(grooves), -0.8, 0.0)
    sash.append(boards)
    if leaves == 2:
        sash.append(ext(rect(-0.3, 0.5, 0.3, spring - 0.3), -1.0, -0.4))           # meeting stile bead
    # strap hinges: long straps across the boards ending in spears, a ring boss at the handle
    hl = w / 2 - CLR - 0.6
    straps = []
    for v in (2.4, spring - 3.2):
        for sg in ((-1, 1) if leaves == 2 else (-1,)):
            u_h = sg * hl
            u_t = sg * 0.9 if leaves == 2 else hl * 0.55
            straps.append(stroke([(u_h, v), (u_t, v)], 0.6, caps=False))
            straps.append(poly([(u_t, v - 0.55), (u_t, v + 0.55), (u_t - sg * 1.1, v)]))
            straps.append(circle((u_h - sg * 0.2, v), 0.5, 16))
    sash.append(ext(cs_union(straps) ^ leaf_cs.offset(-0.2), -0.6 - 0.01, -0.2))
    for sg in ((-1, 1) if leaves == 2 else (1,)):
        sash.append(ext(circle((sg * 1.1 if leaves == 2 else hl - 1.0, spring * 0.48), 0.45, 16), -0.6 - 0.01, -0.2))
    # fanlight in the head
    sash.append(ext(head_cs, -pl, -pl + GLASS))
    sash = [s_ - ext(head_cs, -pl + GLASS - 0.001, 0.5) if i == 0 else s_ for i, s_ in enumerate(sash)]
    ring_ = plug_cs - plug_cs.offset(-0.55, JoinType.Miter, 4.0)
    sash.append(ext(ring_, -pl, 0.0))
    sash.append(ext(rect(-w, spring - 0.3, w, spring + 0.3) ^ plug_cs, -pl, -0.4))          # transom
    inner = head_cs.offset(-0.3, JoinType.Miter, 4.0)
    tr = _gothic_bars(plug_cs.offset(-0.55, JoinType.Miter, 4.0), w - 2 * CLR - 1.1, h - CLR - 0.55, spring, k,
                      "twin", spring - 5.0) ^ head_cs
    sash.append(ext(tr, -pl + GLASS - 0.01, -SASH_REC))
    # --- surround
    A, HB, S = arch_w, hood_w, shaft
    parts = []
    parts.append(ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, CAS))
    # moulded arch (architrave) from the capitals up
    arch_clip = rect(-w - 20, spring - 0.2, w + 20, h + 60) - op
    parts.append(MD.band(op.offset(A, JoinType.Miter, 4.0), A, MD.ARCHITRAVE, clip=arch_clip))
    # engaged shafts: a rounded face, bell capital, moulded base
    SHAFT = [(0.0, 0.6), (0.2, 0.8), (0.45, 1.0), (0.7, 1.2), (1.0, 1.2)]
    ui = w / 2
    for sg in (-1, 1):
        u0, u1 = sorted((sg * ui, sg * (ui + A)))
        parts.append(MD.band(rect(u0, 2.2, u1, spring - 1.6), A / 2, SHAFT))
        parts.append(chamfer_box(u0 - 0.3, 0.0, u1 + 0.3, 2.2, 0.0, 1.4, c=0.4, bottom=0.0))
        parts.append(chamfer_box(u0 - 0.35, spring - 1.8, u1 + 0.35, spring - 0.2, 0.0, 1.4, c=0.5, bottom=0.6))
        parts.append(ext(rect(u0 - 0.1, spring - 2.2, u1 + 0.1, spring - 1.6), 0.0, 1.2))      # necking
        # outer jamb: a plain chamfered pier outside the shaft
        v0, v1 = sorted((sg * (ui + A), sg * (ui + A + S)))
        parts.append(chamfer_box(v0, 0.0, v1, spring - 0.2, 0.0, 0.8, c=0.3, square=("v0",)))
    # drip label, crockets, stops and fleur
    hood_out = op.offset(A + HB, JoinType.Miter, 4.0)
    parts.append(MD.band(hood_out, HB, MD.CROWN, clip=rect(-w - 20, spring - 0.2, w + 20, h + 60)))
    for sg in (-1, 1):
        u0, u1 = sorted((sg * (w / 2 + A - 0.2), sg * (w / 2 + A + S + 0.9)))
        parts.append(MD.run(u0, u1, spring - 0.2, MD.CROWN, 1.2, up=False))
        uc = sg * (w / 2 + A + S * 0.5)
        parts.append(MD.rosette(uc, spring - 2.6, 0.7, 0.6, 0.8))
    cr = crockets(hood_out, spring + 1.6, pitch=2.4)
    if cr is not None:
        parts.append(cr)
    top = hood_out.bounds()[3]
    parts.append(fleur(0.0, top - 0.4, 0.0, 1.6, 1.0))
    top = top - 0.4 + 3.1
    return _one_piece(sash, parts, op, plug_cs, PLUG, top, 0.0)


# ------------------------------------------------------------------ Richardsonian Romanesque
# Round arches of long, equal voussoirs (0.6 mm joints) springing from squat colonnettes with
# cushion capitals; arcaded bands of lights sharing their colonnettes; heavy rock-faced
# lintels and sills; a great arched entrance of receding orders.

ROLL = [(0.0, 0.8), (0.25, 1.1), (0.5, 1.2), (0.75, 1.1), (1.0, 0.8)]
SHAFT = [(0.0, 0.6), (0.2, 0.8), (0.45, 1.0), (0.7, 1.2), (1.0, 1.2)]


def _voussoirs(cx, spring, r0, L, stone=1.9, joint=0.6, clip=None, d=(0.8, 1.0)):
    """A semicircular ring of equal voussoirs round (cx, spring) from radius r0 out L, face-up
    relief stepped d[0] then d[1] with a chamfer; an odd count so a stone sits at the crown."""
    n = max(5, int(round(math.pi * (r0 + L / 2) / stone)))
    n += 1 - n % 2
    stones = []
    g = math.asin(min(0.9, joint / 2 / r0))
    for k in range(n):
        a0, a1 = math.pi * k / n, math.pi * (k + 1) / n
        arc = [a0 + g + (a1 - a0 - 2 * g) * j / 6 for j in range(7)]
        if k == 0:
            arc[0] = -0.12                                   # the springers sit down on the impost
        if k == n - 1:
            arc[-1] = math.pi + 0.12
        pts = [(cx + (r0 + L) * math.cos(a), spring + (r0 + L) * math.sin(a)) for a in arc]
        pts += [(cx + r0 * math.cos(a), spring + r0 * math.sin(a)) for a in reversed(arc)]
        stones.append(poly(pts))
    above = rect(cx - r0 - L - 1, spring, cx + r0 + L + 1, spring + r0 + L + 1)
    face = cs_union(stones) ^ above
    back = (circle((cx, spring), r0 + L, 96) - circle((cx, spring), r0, 96)) ^ above
    if clip is not None:
        face = face ^ clip
        back = back ^ clip
    face = face.offset(-0.25, JoinType.Miter, 4.0).offset(0.25, JoinType.Miter, 4.0)
    # a continuous backing ring under the stones: the joints are grooves, not through-slots,
    # so the ring prints (and stays) as one piece
    return ext(back, 0.0, 0.4) + stepped(face, [(0.0, 0.2, d[0]), (0.2, d[0], d[1])])


def _cushion(u, v_top, wd, ht, w0=0.0, d=1.4):
    """Cushion capital (a block whose lower corners round off into the shaft), top at v_top."""
    blk = cs_union([rect(u - wd / 2, v_top - ht * 0.45, u + wd / 2, v_top),
                    circle((u - wd / 2 + ht * 0.55, v_top - ht * 0.45), ht * 0.55, 20),
                    circle((u + wd / 2 - ht * 0.55, v_top - ht * 0.45), ht * 0.55, 20)])
    blk = blk ^ rect(u - wd / 2, v_top - ht, u + wd / 2, v_top)
    return stepped(blk, [(0.0, w0, w0 + d - 0.4), (0.2, w0 + d - 0.4, w0 + d)])


def window_romanesque(w, h, n=1, gap=2.6, lites=(1, 1), flat=False, col=1.2, L=2.2, hood=True, sill_ext=1.2):
    """Romanesque window of ``n`` lights (w wide, h tall to the crown) side by side, ``gap``
    apart. Arched (default): each light a semicircle ringed by long voussoirs springing from
    squat colonnettes with cushion capitals (shared between lights), a roll hood over the
    whole group, and a long stone sill. ``flat``: square-headed lights under one heavy
    rock-faced lintel, with colonnette mullions."""
    from . import moulding as MD
    pitch = w + gap
    cs_ = [(-(n - 1) / 2 + i) * pitch for i in range(n)]
    rise = 0.0 if flat else w / 2
    spring = h - rise
    ops = [opening_cs(w, h, 0 if flat else None).translate((c, 0.0)) for c in cs_]
    op = cs_union(ops)
    plug_cs = op.offset(-CLR, JoinType.Miter, 4.0)
    sash = [window_insert(w, h, 0 if flat else None, lites=lites, bare=True)["insert"].translate([c, 0, 0]) for c in cs_]
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, CAS)]
    half = cs_[-1] + w / 2 + col + 0.3                   # outer edge of the end colonnettes
    # colonnettes: one at each end and one on every pier between lights
    posts = [cs_[0] - w / 2 - col / 2 - 0.15] + [(a + b) / 2 for a, b in zip(cs_[:-1], cs_[1:])] + \
            [cs_[-1] + w / 2 + col / 2 + 0.15]
    for i, u in enumerate(posts):
        cw = col if i in (0, len(posts) - 1) else min(col + 0.4, gap - 0.2)
        parts.append(MD.band(rect(u - cw / 2, 1.0, u + cw / 2, spring - 1.6), cw / 2, SHAFT))
        parts.append(chamfer_box(u - cw / 2 - 0.25, 0.0, u + cw / 2 + 0.25, 1.2, 0.0, 1.4, c=0.4, bottom=0.0))
        parts.append(_cushion(u, spring, cw + 0.8, 1.8))
    if flat:
        # one heavy lintel over the group, rock-faced (a pillowed stepped block)
        lt = rect(-half - 0.8, h - 0.1, half + 0.8, h + 3.2)
        parts.append(stepped(lt, [(0.0, 0.0, 1.0), (0.3, 1.0, 1.4)]))
        top = h + 3.2
    else:
        clip = None
        vs = []
        for c in cs_:
            cl = rect(c - pitch / 2, -1, c + pitch / 2, h + 20) if n > 1 else None
            vs.append(_voussoirs(c, spring, w / 2 + 0.1, L, clip=cl))
        parts += vs
        if n > 1:   # fill the spandrels between neighbouring rings with plain ashlar
            ring_out = cs_union([circle((c, spring), w / 2 + L + 0.1, 48) for c in cs_])
            sp = (rect(cs_[0], spring, cs_[-1], spring + w / 2 + L) - ring_out)
            sp = sp.offset(-0.3, JoinType.Round).offset(0.3, JoinType.Round)
            parts.append(ext(sp, 0.0, 0.6))
        top = spring + w / 2 + L + 0.1
        if hood:
            outer = cs_union([circle((c, spring), w / 2 + L + 1.2, 64) for c in cs_]) + \
                rect(cs_[0] - w / 2 - L - 1.2, spring - 0.01, cs_[-1] + w / 2 + L + 1.2, spring + 0.6)
            parts.append(MD.band(outer, 1.1, ROLL, clip=rect(-half - 20, spring, half + 20, h + 40)))
            for sg in (-1, 1):                          # the hood's ends run out as a short impost band
                u0, u1 = sorted((sg * (half - 0.4), sg * (half + 2.2)))
                parts.append(MD.run(u0, u1, spring, MD.CROWN, 1.0, up=False))
            top = spring + w / 2 + L + 1.2
    sw = half + sill_ext
    parts.append(chamfer_box(-sw, -1.8, sw, 0.2, 0.0, 1.4, c=0.4, bottom=0.6))
    return _one_piece(sash, parts, op, plug_cs, PLUG, top, -1.8)


def door_romanesque(w, h, orders=2, col=1.3, L=3.0, plug=True, leaves=2, leaf="studded"):
    """Great round-arched Romanesque entrance: the arch springs low (w/2 under the crown)
    from ``orders`` receding pairs of colonnettes with cushion capitals on a moulded impost
    band; a ring of long voussoirs and a roll hood over it. With ``plug`` the doorway holds
    ornate leaves under a fanlight of radiating bars; without, it is an open porch arch (the
    surround alone, printed flat on its back)."""
    from . import moulding as MD
    rise = w / 2
    spring = h - rise
    op = opening_cs(w, h, None)
    plug_cs = op.offset(-CLR, JoinType.Miter, 4.0)
    pl = PLUG
    sash = []
    if plug:
        dh = spring - 0.4
        mid = SLOT if leaves > 1 else 0.0
        lw = (w - 2 * CLR - 1.0 - mid * (leaves - 1)) / leaves
        u = -w / 2 + CLR + 0.5
        body = [ext(plug_cs, -pl, -1.0)]
        lights = []
        for i in range(leaves):
            lp, light = _leaf(leaf, u, lw, dh, hinge_left=(i == 0))
            body += lp
            if light is not None:
                lights.append(light)
            u += lw + mid
        fan = plug_cs.offset(-0.5, JoinType.Miter, 4.0) ^ rect(-w, spring + 0.3, w, h + 5)
        glass = (cs_union(lights) + fan) if lights else fan
        cut = ext(glass, -pl - 1, 0.0)
        sash = [p - cut for p in body] + _glass_bars()
        sash.append(ext(glass, -pl, -pl + GLASS))
        sash.append(ext(plug_cs - plug_cs.offset(-0.5, JoinType.Miter, 4.0), -pl, 0.0))
        sash.append(ext(rect(-w, spring - 0.3, w, spring + 0.3) ^ plug_cs, -pl, -0.4))
        hub, rays = sunburst((0.0, spring + 0.3), 1.4, 2.2, rise + 2.0, n=9, a0=0.15, a1=math.pi - 0.15,
                             ray0=RIB, ray1=RIB + 0.1)
        sash.append(ext((hub + rays) ^ fan, -pl + GLASS - 0.01, -0.6))
    parts = []
    if plug:
        parts.append(ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, CAS))
    # receding orders: colonnettes and an arched roll per order
    u_edge = w / 2
    for k in range(orders):
        uc = u_edge + col / 2 + 0.1
        for sg in (-1, 1):
            u = sg * uc
            parts.append(MD.band(rect(u - col / 2, 1.4, u + col / 2, spring - 2.0), col / 2, SHAFT))
            parts.append(chamfer_box(u - col / 2 - 0.3, 0.0, u + col / 2 + 0.3, 1.6, 0.0, 1.4, c=0.4, bottom=0.0))
            parts.append(_cushion(u, spring - 0.4, col + 0.9, 1.8))
        r_in = u_edge + 0.1
        parts.append(MD.band(circle((0.0, spring), r_in + col + 0.2, 72), col + 0.2, ROLL,
                             clip=rect(-w - 20, spring, w + 20, h + 40)))
        u_edge = uc + col / 2 + 0.1
    # impost band across the capitals and out past the jambs
    parts.append(MD.run(-u_edge - 1.2, u_edge + 1.2, spring - 0.4, MD.CROWN, 1.0, up=True))
    # the voussoir ring and the hood
    parts.append(_voussoirs(0.0, spring + 0.6, u_edge + 0.1, L, stone=2.2, d=(1.0, 1.4)))
    ro = u_edge + 0.1 + L
    outer = circle((0.0, spring + 0.6), ro + 1.3, 96)
    parts.append(MD.band(outer, 1.2, ROLL, clip=rect(-w - 20, spring + 0.6, w + 20, h + 40)))
    for sg in (-1, 1):
        u0, u1 = sorted((sg * (ro - 0.3), sg * (ro + 3.0)))
        parts.append(MD.run(u0, u1, spring + 0.6, MD.CROWN, 1.0, up=False))
    top = spring + 0.6 + ro + 1.3
    if not plug:
        sur = union(parts) - ext(op, -5, 5)
        return dict(insert=sur, sash=M(), glass=M(), frame=sur, surround=sur, back=0.0, cut=op,
                    landing=footprint(sur, op), top=top, bottom=0.0)
    return _one_piece(sash, parts, op, plug_cs, PLUG, top, 0.0)


# ------------------------------------------------------------------ Stick style
# Flat board trim whose members cross at the corners like framing sticks, a pent hood on
# diagonal knee braces over a frieze of short sticks, an X-braced apron, border-light sashes.

def _stick_frame(w, h, A, parts, ext_=0.9, d=CAS):
    """Head and side boards that run past each other at the corners (crossed sticks)."""
    parts.append(ext(rect(-w / 2 - A - ext_, h, w / 2 + A + ext_, h + A), 0.0, d))               # head
    for sg in (-1, 1):
        u0, u1 = sorted((sg * w / 2, sg * (w / 2 + A)))
        parts.append(ext(rect(u0, -ext_ - 1.0, u1, h + A + ext_), 0.0, d + 0.2))                  # sides


def _stick_head(w, h, A, parts, hood_w=1.4, frieze=2.2, brace=True):
    """A frieze of short sticks over the head board, a pent hood (a crowned shelf) over it,
    and two diagonal knee braces from the side boards up to the hood's ends. Returns top."""
    from . import moulding as MD
    v0 = h + A
    half = w / 2 + A
    parts.append(ext(rect(-half, v0 - 0.01, half, v0 + frieze), 0.0, 0.4))                   # frieze field
    n = max(2, int((2 * half - 0.8) / 1.3))
    sticks = [rect(-half + 0.4 + (2 * half - 0.8) * (k + 0.5) / n - 0.3, v0, -half + 0.4 + (2 * half - 0.8) * (k + 0.5) / n + 0.3,
                   v0 + frieze) for k in range(n)]
    parts.append(ext(cs_union(sticks), 0.39, 0.8))
    hv = v0 + frieze
    hh = half + hood_w
    parts.append(MD.run(-hh, hh, hv + 1.4, MD.CROWN, 1.4, up=False))
    parts.append(ext(rect(-hh + 0.2, hv + 1.39, hh - 0.2, hv + 2.0), 0.0, 1.0))                # the hood's roof edge
    if brace:
        for sg in (-1, 1):
            a = (sg * (w / 2 + A * 0.5), h - 2.6)
            b = (sg * (hh - 0.5), hv + 0.2)
            parts.append(ext(stroke([a, b], 0.7), 0.0, 1.2))
    return hv + 2.0


def window_stick(w, h, lites=(1, 1), qa=True, A=1.2, apron=True, brace=True, rows=(1, 1)):
    """Stick-style window: border-light sash (``qa``), crossed-stick casing, a pent hood on
    knee braces over a frieze of sticks, a sill on two blocks and an X-braced apron."""
    from . import moulding as MD
    op = opening_cs(w, h, 0)
    plug_cs = op.offset(-CLR, JoinType.Miter, 4.0)
    sash = window_insert(w, h, 0, lites=lites, bare=True, qa=qa, rows=rows)["insert"]
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, CAS)]
    _stick_frame(w, h, A, parts)
    top = _stick_head(w, h, A, parts, brace=brace)
    sw = w / 2 + A + 0.6
    parts.append(MD.run(-sw, sw, 0.0, MD.SILL, 1.0, up=False))
    bottom = -1.9
    if apron:
        aw = w / 2
        parts.append(ext(rect(-aw, -3.6, aw, -0.9), 0.0, 0.4))
        x = cs_union([stroke([(-aw + 0.5, -3.3), (aw - 0.5, -1.2)], 0.55), stroke([(-aw + 0.5, -1.2), (aw - 0.5, -3.3)], 0.55)])
        parts.append(ext(x ^ rect(-aw, -3.6, aw, -0.9), 0.39, 0.8))
        parts.append(ext(rect(-aw - 0.3, -4.0, aw + 0.3, -3.5), 0.0, 0.8))
        bottom = -4.0
    return _one_piece([sash], parts, op, plug_cs, PLUG, top, bottom)


def door_stick(w, h, leaves=2, transom=4.0, A=1.4, leaf="crossbuck", tstyle="stick"):
    """Stick-style entrance: the ornate leaves and transom of door_ornate in a crossed-stick
    casing, a stick frieze and a deep pent hood on big knee braces."""
    op, plug_cs, sash_parts = _ornate_door_sash(w, h, leaves, transom, leaf, tstyle)
    parts = [ext((op - op.offset(-RIB, JoinType.Miter, 4.0)) ^ rect(-w, 0.5, w, h + 1), 0.0, CAS)]
    parts.append(ext(rect(-w / 2 - A - 0.9, h, w / 2 + A + 0.9, h + A), 0.0, CAS))
    for sg in (-1, 1):
        u0, u1 = sorted((sg * w / 2, sg * (w / 2 + A)))
        parts.append(ext(rect(u0, 0.0, u1, h + A + 0.9), 0.0, CAS + 0.2))
        parts.append(chamfer_box(u0 - 0.2, 0.0, u1 + 0.2, 2.4, 0.0, 1.2, c=0.3, bottom=0.0))       # plinths
    top = _stick_head(w, h, A, parts, hood_w=2.0, frieze=2.6)
    return _one_piece(sash_parts, parts, op, plug_cs, PLUG, top, 0.0)


# ------------------------------------------------------------------ Folk Victorian
# Crossetted flat casings, a raised frieze panel and a crown: a low pediment with a fan of
# rays over a dentil course (head "pediment") or a moulded cap on dentils (head "cap").

def _folk_crown(half, v0, head, parts):
    from . import moulding as MD
    parts.append(ext(rect(-half, v0 - 0.01, half, v0 + 2.2), 0.0, CAS))                     # frieze
    parts.append(chamfer_box(-half + 1.0, v0 + 0.5, half - 1.0, v0 + 1.7, CAS - 0.01, 0.4, c=0.2))
    parts.append(dentils(-half + 0.2, half - 0.2, v0 + 2.0, 1.2, 0.0, 1.0))            # into frieze and crown
    vs = v0 + 3.0
    parts.append(MD.run(-half - 0.8, half + 0.8, vs + 1.2, MD.CROWN, 1.2, up=False))
    top = vs + 1.2
    if head == "pediment":
        rise = (half + 0.8) * 0.42
        tri = poly([(-half - 0.8, top - 0.01), (half + 0.8, top - 0.01), (0.0, top + rise)])
        parts.append(MD.band(tri, 1.0, MD.CROWN, clip=rect(-half - 5, top + 0.4, half + 5, top + 20)))
        tymp = tri.offset(-0.9, JoinType.Miter, 4.0) + \
            (rect(-half + 0.9, top - 0.4, half - 0.9, top + 1.2) ^ tri.offset(-0.5, JoinType.Miter, 4.0).translate((0.0, -0.6)))
        parts.append(ext(tymp, 0.0, CAS))
        hub, rays = sunburst((0.0, top), 0.0, 0.6, rise, n=5, a0=0.35, a1=math.pi - 0.35, ray0=0.5, ray1=0.7)
        parts.append(ext((rays + hub) ^ tymp.offset(-0.2, JoinType.Miter, 4.0), CAS - 0.01, 1.0))
        top += rise
    return top


def window_folk(w, h, lites=(1, 1), head="pediment", A=1.2):
    """Folk Victorian window: 2-over-2 sash, crossetted flat casing with a bead, a frieze
    with a raised panel, dentils and a crown (a low pediment with a fan, or a moulded cap),
    and a sill on two small brackets."""
    from . import moulding as MD
    op = opening_cs(w, h, 0)
    plug_cs = op.offset(-CLR, JoinType.Miter, 4.0)
    sash = window_insert(w, h, 0, lites=lites, bare=True)["insert"]
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, CAS)]
    cas = (op.offset(A, JoinType.Miter, 4.0) - op) ^ rect(-w, 0.0, w, h + A)
    parts.append(ext(cas, 0.0, CAS))
    parts.append(ext((op.offset(RIB, JoinType.Miter, 4.0) - op) ^ rect(-w, 0.0, w, h + 1), CAS - 0.01, BEAD))
    for sg in (-1, 1):                                  # crossettes (ears) at the head
        u0, u1 = sorted((sg * (w / 2 + A), sg * (w / 2 + A + 0.6)))
        parts.append(ext(rect(u0, h - 1.2, u1, h + A), 0.0, CAS))
    top = _folk_crown(w / 2 + A + 0.6, h + A, head, parts)
    sw = w / 2 + A + 0.5
    parts.append(MD.run(-sw, sw, 0.0, MD.SILL, 1.0, up=False))
    for sg in (-1, 1):
        parts.append(ext(rect(sg * (w / 2 + 0.2) - 0.45, -1.9, sg * (w / 2 + 0.2) + 0.45, -0.9), 0.0, 0.8))
    return _one_piece([sash], parts, op, plug_cs, PLUG, top, -1.9)


def door_folk(w, h, leaves=1, transom=3.6, A=1.4, head="pediment", leaf="half_glass", tstyle="diamond"):
    """Folk Victorian entrance: the ornate leaf and transom of door_ornate in a crossetted
    casing on plinths, with the frieze, dentils and pediment crown of window_folk."""
    op, plug_cs, sash_parts = _ornate_door_sash(w, h, leaves, transom, leaf, tstyle)
    parts = [ext((op - op.offset(-RIB, JoinType.Miter, 4.0)) ^ rect(-w, 0.5, w, h + 1), 0.0, CAS)]
    parts.append(ext((op.offset(A, JoinType.Miter, 4.0) - op) ^ rect(-w, 0.0, w, h + A), 0.0, CAS))
    for sg in (-1, 1):
        u0, u1 = sorted((sg * w / 2, sg * (w / 2 + A)))
        parts.append(chamfer_box(u0 - 0.2, 0.0, u1 + 0.2, 2.4, 0.0, 1.2, c=0.3, bottom=0.0))
        e0, e1 = sorted((sg * (w / 2 + A), sg * (w / 2 + A + 0.6)))
        parts.append(ext(rect(e0, h - 1.4, e1, h + A), 0.0, CAS))
    top = _folk_crown(w / 2 + A + 0.6, h + A, head, parts)
    return _one_piece(sash_parts, parts, op, plug_cs, PLUG, top, 0.0)


# ------------------------------------------------------------------ Greek Revival (the Fowler)
def window_greek(w, h, lites=(3, 3), rows=(2, 2), A=1.2):
    """Greek Revival window: six-over-six sash, a flat casing with a bead, a lintel board
    under a low peaked cap with acroteria blocks at its ends and apex, and a slab sill."""
    from . import moulding as MD
    op = opening_cs(w, h, 0)
    plug_cs = op.offset(-CLR, JoinType.Miter, 4.0)
    sash = window_insert(w, h, 0, lites=lites, rows=rows, bare=True)["insert"]
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, CAS)]
    parts.append(ext((op.offset(A, JoinType.Miter, 4.0) - op) ^ rect(-w, 0.0, w, h + A), 0.0, CAS))
    parts.append(ext((op.offset(RIB, JoinType.Miter, 4.0) - op) ^ rect(-w, 0.0, w, h + 1), CAS - 0.01, BEAD))
    half = w / 2 + A + 0.6
    v0 = h + A - 0.2
    parts.append(ext(rect(-half, v0, half, v0 + 1.8), 0.0, 1.0))                    # lintel board
    parts.append(MD.run(-half - 0.4, half + 0.4, v0 + 1.8 + 0.8, MD.CROWN, 0.8, up=False))
    vt = v0 + 2.6
    rise = 0.32 * (half + 0.4)
    tri = poly([(-half - 0.4, vt - 0.3), (half + 0.4, vt - 0.3), (0.0, vt + rise)])             # seated in the cap
    parts.append(MD.band(tri, 0.9, MD.CROWN, clip=rect(-half - 2, vt + 0.3, half + 2, vt + 10)))
    parts.append(ext(tri.offset(-0.8, JoinType.Miter, 4.0) + (rect(-half + 0.6, vt - 0.3, half - 0.6, vt + 0.9) ^ tri), 0.0, CAS))
    for u in (-half - 0.1, half + 0.1):
        parts.append(chamfer_box(u - 0.6, vt - 0.2, u + 0.6, vt + 1.0, 0.0, 1.2, c=0.3))
    parts.append(chamfer_box(-0.6, vt + rise - 0.6, 0.6, vt + rise + 0.8, 0.0, 1.2, c=0.3))
    top = vt + rise + 0.8
    sw = w / 2 + A + 0.5
    parts.append(chamfer_box(-sw, -1.4, sw, 0.2, 0.0, 1.4, c=0.4, bottom=0.8))
    return _one_piece([sash], parts, op, plug_cs, PLUG, top, -1.4)


def door_greek(w, h, side=2.4, transom=3.6, A=1.6):
    """Greek Revival entrance: a two-panel door between glazed sidelights under a transom of
    rectangular lights, framed by panelled pilasters and a plain entablature."""
    from . import moulding as MD
    W = w + 2 * side
    op = rect(-W / 2, 0, W / 2, h)
    plug_cs = op.offset(-CLR, JoinType.Miter, 4.0)
    pl = PLUG
    dh = h - transom
    body = [ext(plug_cs, -pl, -1.0)]
    lp, _ = _leaf("two_panel", -w / 2 + 0.2, w - 0.4, dh, True)
    body += lp
    glass = []
    for sg in (-1, 1):
        u0, u1 = sorted((sg * (w / 2 + 0.3), sg * (W / 2 - CLR - 0.5)))
        glass.append(rect(u0, dh * 0.35, u1, dh - 0.5))
        body.append(chamfer_box(u0, 1.0, u1, dh * 0.35 - 0.5, -1.0, 0.4, c=0.2))
    tcs = rect(-W / 2 + CLR + 0.5, dh + 0.3, W / 2 - CLR - 0.5, h - CLR - 0.5)
    glass.append(tcs)
    g = cs_union(glass)
    body = [p - ext(g, -pl + GLASS, 0.5) for p in body]
    sash = body + [ext(g, -pl, -pl + GLASS), ext(plug_cs - plug_cs.offset(-0.5, JoinType.Miter, 4.0), -pl, 0.0)]
    bars = [rect(-w / 2 - 0.2, 0.3, -w / 2 + 0.3, h), rect(w / 2 - 0.3, 0.3, w / 2 + 0.2, h), rect(-W, dh - 0.3, W, dh + 0.3)]
    for sg in (-1, 1):
        for j in (1, 2):
            v = dh * 0.35 + (dh * 0.65 - 0.5) * j / 3
            bars.append(rect(sg * (w / 2) - (side if sg < 0 else 0), v - RIB / 2, sg * (w / 2) + (side if sg > 0 else 0), v + RIB / 2))
    for k in range(1, 6):
        x = -W / 2 + W * k / 6
        bars.append(rect(x - RIB / 2, dh, x + RIB / 2, h))
    sash.append(ext(cs_union(bars) ^ plug_cs, -pl + GLASS - 0.01, -0.4))
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, CAS)]
    for sg in (-1, 1):
        u0, u1 = sorted((sg * W / 2, sg * (W / 2 + A)))
        parts.append(ext(rect(u0, 0.0, u1, h + 0.2), 0.0, 0.8))
        parts.append(chamfer_box(u0 + 0.35, 2.6, u1 - 0.35, h - 1.4, 0.8 - 0.01, 0.4, c=0.2))
        parts.append(chamfer_box(u0 - 0.2, 0.0, u1 + 0.2, 2.0, 0.0, 1.2, c=0.3, bottom=0.0))
    half = W / 2 + A + 0.4
    parts.append(ext(rect(-half, h - 0.1, half, h + 1.0), 0.0, 1.0))                # architrave
    parts.append(ext(rect(-half, h + 0.9, half, h + 3.0), 0.0, CAS))                # frieze
    parts.append(MD.run(-half - 0.6, half + 0.6, h + 4.2, MD.CROWN, 1.3, up=False))
    return _one_piece(sash, parts, op, plug_cs, PLUG, h + 4.2, 0.0)


# ------------------------------------------------------------------ San Francisco Italianate (the Delancey)
def window_sf(w, h, rise=2.2, A=1.4, col=1.2, lites=(1, 2)):
    """San Francisco Italianate window: a segmental head, engaged colonnettes with leafy
    capitals carrying an arched architrave, a raised keystone block with a rosette, and a
    moulded sill on paired corbels."""
    from . import moulding as MD
    spring = h - rise
    op = opening_cs(w, h, rise)
    plug_cs = op.offset(-CLR, JoinType.Miter, 4.0)
    sash = window_insert(w, h, rise, lites=lites, bare=True)["insert"]      # default two-over-one
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, CAS)]
    for sg in (-1, 1):
        u = sg * (w / 2 + col / 2 + 0.1)
        parts.append(MD.band(rect(u - col / 2, 1.2, u + col / 2, spring - 1.4), col / 2, [(0.0, 0.6), (0.5, 1.0), (1.0, 1.2)]))
        parts.append(chamfer_box(u - col / 2 - 0.25, 0.0, u + col / 2 + 0.25, 1.4, 0.0, 1.2, c=0.3, bottom=0.0))
        cap = chamfer_box(u - col / 2 - 0.3, spring - 1.6, u + col / 2 + 0.3, spring, 0.0, 1.4, c=0.4, bottom=0.8)
        parts.append(cap)
        parts.append(ext(cs_union([circle((u + dx, spring - 0.8), 0.3, 12) for dx in (-0.45, 0.0, 0.45)]), 1.39, 1.8))
    ar = op.offset(A + col * 0.5, JoinType.Miter, 4.0)
    parts.append(MD.band(ar, A, MD.ARCHITRAVE, clip=rect(-w - 10, spring - 0.01, w + 10, h + 20) - op))
    ktop = h + A + col * 0.5 + 0.8
    parts.append(chamfer_box(-0.8, h - 0.4, 0.8, ktop, 0.0, 1.8, c=0.4))
    parts.append(MD.rosette(0.0, (h + ktop) / 2 + 0.2, 0.5, 1.6, 0.6))
    sw = w / 2 + col + 0.6
    parts.append(MD.run(-sw, sw, 0.0, MD.SILL, 1.0, up=False))
    for sg in (-1, 1):
        for du in (-0.6, 0.6):
            parts.append(console(1.6, 0.9, 0.5, u=sg * (w / 2 - 0.2) + du, v_top=-0.8, w0=0.0))
    return _one_piece([sash], parts, op, plug_cs, PLUG, ktop, -2.4)


def door_sf(w, h, rise=2.6, pil=1.8, A=1.4):
    """San Francisco entrance: tall glazed double doors under an arched transom of radiating
    bars, fluted pilasters with capitals, a frieze with three rosettes and a segmental
    arched cornice with a ball on top."""
    from . import moulding as MD
    spring = h - rise
    op = opening_cs(w, h, rise)
    plug_cs = op.offset(-CLR, JoinType.Miter, 4.0)
    pl = PLUG
    dh = spring - 0.4
    mid = SLOT
    lw = (w - 2 * CLR - 1.0 - mid) / 2
    u = -w / 2 + CLR + 0.5
    body, lights = [ext(plug_cs, -pl, -1.0)], []
    for i in range(2):
        lp, light = _leaf("glazed_tall", u, lw, dh, i == 0)
        body += lp
        if light is not None:
            lights.append(light)
        u += lw + mid
    fan = plug_cs.offset(-0.5, JoinType.Miter, 4.0) ^ rect(-w, spring + 0.3, w, h + 5)
    g = cs_union(lights) + fan
    sash = [p - ext(g, -pl - 1, 0.0) for p in body]
    sash += [ext(g, -pl, -pl + GLASS), ext(plug_cs - plug_cs.offset(-0.5, JoinType.Miter, 4.0), -pl, 0.0),
             ext(rect(-w, spring - 0.3, w, spring + 0.3) ^ plug_cs, -pl, -0.4)]
    rays = cs_union([stroke([(0.0, spring), (8 * math.cos(a), spring + 8 * math.sin(a))], RIB) for a in
                     (0.5, 1.0, math.pi / 2, math.pi - 1.0, math.pi - 0.5)])
    sash.append(ext(rays ^ fan, -pl + GLASS - 0.01, -0.6))
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, CAS)]
    parts.append(MD.band(op.offset(A, JoinType.Miter, 4.0), A, MD.CASING, clip=rect(-w - 10, 0.0, w + 10, h + 20) - op))
    ui, uo = w / 2 + A, w / 2 + A + pil
    vcap = h + A
    for sg in (-1, 1):
        u0, u1 = sorted((sg * ui, sg * uo))
        um = (u0 + u1) / 2
        parts.append(ext(rect(u0, 2.4, u1, vcap), 0.0, 1.0) -
                     union([ext(stroke([(um + dx, 3.4), (um + dx, vcap - 1.2)], 0.5), 0.6, 1.2) for dx in (-0.45, 0.45)]))
        parts.append(chamfer_box(u0 - 0.2, 0.0, u1 + 0.2, 2.4, 0.0, 1.2, c=0.4, bottom=0.0))
        parts.append(chamfer_box(u0 - 0.3, vcap - 0.2, u1 + 0.3, vcap + 1.4, 0.0, 1.4, c=0.4, bottom=0.8))
    half = uo + 0.3
    parts.append(ext(rect(-half, vcap + 1.2, half, vcap + 3.6), 0.0, CAS))          # into the cornice: one piece
    for uu in (-half * 0.55, 0.0, half * 0.55):
        parts.append(MD.rosette(uu, vcap + 2.3, 0.65, CAS - 0.01, 0.8))
    vb = vcap + 3.4
    parts.append(MD.run(-half - 0.5, half + 0.5, vb + 1.2, MD.CROWN, 1.2, up=False))
    seg = arch_cs(-half - 0.2, half + 0.2, vb + 0.8, vb + 1.2, rise=2.4, seg=48)                  # seated in the cornice
    parts.append(MD.band(seg, 1.1, MD.CROWN, clip=rect(-half - 2, vb + 1.2, half + 2, vb + 10)))
    parts.append(ext((seg.offset(-1.0, JoinType.Round) + (rect(-half + 0.5, vb + 0.9, half - 0.5, vb + 2.2) ^ seg))
                     ^ rect(-half, vb + 0.9, half, vb + 10), 0.0, CAS))
    top = vb + 1.2 + 2.4
    parts.append(ext(circle((0.0, top + 0.5), 0.75, 20) + rect(-0.35, top - 0.4, 0.35, top + 0.2), 0.0, 1.4))
    return _one_piece(sash, parts, op, plug_cs, PLUG, top + 1.25, 0.0)


# ------------------------------------------------------------------ Queen Anne Free Classic (the Carrow)
def window_fc(w, h, A=1.3, pediment=True):
    """Queen Anne Free Classic window: diamond-paned upper sash over a plain lower one,
    fluted pilaster jambs on plinths with capitals, dentils under a triangular pediment
    with an oculus in its tympanum, and a moulded sill."""
    from . import moulding as MD
    op = opening_cs(w, h, 0)
    plug_cs = op.offset(-CLR, JoinType.Miter, 4.0)
    sash = window_insert(w, h, 0, lites=(1, 1), bare=True, upper="diamond")["insert"]
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, CAS)]
    for sg in (-1, 1):
        u0, u1 = sorted((sg * w / 2, sg * (w / 2 + A)))
        um = (u0 + u1) / 2
        parts.append(ext(rect(u0, 1.2, u1, h + 0.2), 0.0, 0.8) - ext(stroke([(um, 2.2), (um, h - 1.2)], 0.5), 0.4, 1.0))
        parts.append(chamfer_box(u0 - 0.2, -0.2, u1 + 0.2, 1.4, 0.0, 1.0, c=0.3, bottom=0.0))
        parts.append(chamfer_box(u0 - 0.25, h - 0.2, u1 + 0.25, h + 1.2, 0.0, 1.2, c=0.35, bottom=0.7))
    half = w / 2 + A + 0.25
    parts.append(ext(rect(-half, h + 1.0, half, h + 2.2), 0.0, CAS))
    parts.append(dentils(-half + 0.2, half - 0.2, h + 1.8, 0.9, 0.0, 1.0))
    vb = h + 2.6
    parts.append(MD.run(-half - 0.5, half + 0.5, vb + 0.8, MD.CROWN, 1.0, up=False))
    top = vb + 0.8
    if pediment:
        rise = 0.5 * (half + 0.5)
        tri = poly([(-half - 0.5, top - 0.01), (half + 0.5, top - 0.01), (0.0, top + rise)])
        parts.append(MD.band(tri, 1.0, MD.CROWN, clip=rect(-half - 2, top + 0.3, half + 2, top + 20)))
        parts.append(ext(tri.offset(-0.9, JoinType.Miter, 4.0) + (rect(-half + 0.6, top - 0.3, half - 0.6, top + 0.3) ^ tri),
                         0.0, CAS))
        oc = (0.0, top + rise * 0.36)
        rr = min(0.95, rise * 0.24)
        parts.append(ext(circle(oc, rr + 0.5, 24) - circle(oc, rr, 24), CAS - 0.01, 1.2))
        top += rise
    sw = w / 2 + A + 0.4
    parts.append(MD.run(-sw, sw, 0.0, MD.SILL, 1.0, up=False))
    return _one_piece([sash], parts, op, plug_cs, PLUG, top, -1.2)


def window_palladian(wc, h, ws=2.6, gap=1.2, A=1.1):
    """Palladian (Venetian) window: a round-headed centre light between two narrow
    square-headed side lights, on pilaster mullions, the side lights' entablature running
    into the arch's springing, a keystone at the crown and a sill across all three."""
    from . import moulding as MD
    spring = h - wc / 2
    hs = spring
    xs = wc / 2 + gap + ws / 2
    ops = [opening_cs(wc, h, None), rect(-xs - ws / 2, 0.0, -xs + ws / 2, hs), rect(xs - ws / 2, 0.0, xs + ws / 2, hs)]
    op = cs_union(ops)
    plug_cs = op.offset(-CLR, JoinType.Miter, 4.0)
    sash = [window_insert(wc, h, None, lites=(2, 2), bare=True, upper="diamond")["insert"]]
    for sg in (-1, 1):
        sash.append(window_insert(ws, hs, 0, lites=(1, 1), bare=True)["insert"].translate([sg * xs, 0, 0]))
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, CAS)]
    for u in (-xs - ws / 2 - A / 2 - 0.1, -wc / 2 - gap / 2, wc / 2 + gap / 2, xs + ws / 2 + A / 2 + 0.1):
        cw = min(A, gap) if abs(abs(u) - (wc / 2 + gap / 2)) < 0.01 else A
        parts.append(ext(rect(u - cw / 2 - 0.05, 0.0, u + cw / 2 + 0.05, hs), 0.0, 0.8))
    half = xs + ws / 2 + A + 0.2
    parts.append(ext(rect(-half, hs - 0.1, -wc / 2, hs + 1.2), 0.0, 1.0))
    parts.append(ext(rect(wc / 2, hs - 0.1, half, hs + 1.2), 0.0, 1.0))
    band = op.offset(A, JoinType.Round) ^ rect(-wc, spring, wc, h + 10)
    parts.append(MD.band(band, A, MD.CASING, clip=rect(-wc, spring, wc, h + 20) - ops[0]))
    kt = h + A + 0.8
    parts.append(chamfer_box(-0.6, h - 0.3, 0.6, kt, 0.0, 1.6, c=0.35))
    sw = half + 0.3
    parts.append(MD.run(-sw, sw, 0.0, MD.SILL, 1.0, up=False))
    return _one_piece(sash, parts, op, plug_cs, PLUG, kt, -1.2)


def door_fc(w, h, side=2.2, transom=3.4, A=1.4):
    """Queen Anne Free Classic entrance: an oval-light door between leaded sidelights under
    a leaded transom, fluted pilasters, dentils and a triangular pediment with an oculus."""
    from . import moulding as MD
    W = w + 2 * side
    op = rect(-W / 2, 0, W / 2, h)
    plug_cs = op.offset(-CLR, JoinType.Miter, 4.0)
    pl = PLUG
    dh = h - transom
    body = [ext(plug_cs, -pl, -1.0)]
    lp, light = _leaf("oval", -w / 2 + 0.2, w - 0.4, dh, True)
    body += lp
    glass = [light]
    for sg in (-1, 1):
        u0, u1 = sorted((sg * (w / 2 + 0.3), sg * (W / 2 - CLR - 0.5)))
        glass.append(rect(u0, 1.4, u1, dh - 0.5))
    tcs = rect(-W / 2 + CLR + 0.5, dh + 0.3, W / 2 - CLR - 0.5, h - CLR - 0.5)
    glass.append(tcs)
    g = cs_union(glass)
    body = [p - ext(g, -pl + GLASS, 0.5) for p in body]
    sash = body + [ext(g, -pl, -pl + GLASS), ext(plug_cs - plug_cs.offset(-0.5, JoinType.Miter, 4.0), -pl, 0.0)]
    bars = [rect(-w / 2 - 0.2, 0.3, -w / 2 + 0.3, h), rect(w / 2 - 0.3, 0.3, w / 2 + 0.2, h), rect(-W, dh - 0.3, W, dh + 0.3)]
    for sg in (-1, 1):
        u0, u1 = sorted((sg * (w / 2 + 0.3), sg * (W / 2 - CLR - 0.5)))
        side_cs = rect(u0, 1.4, u1, dh - 0.5)
        inner = side_cs.offset(-0.6, JoinType.Miter, 4.0)
        bars.append(side_cs - inner.offset(-RIB, JoinType.Miter, 4.0) if not inner.is_empty() else side_cs)
    inner_t = tcs.offset(-0.8, JoinType.Miter, 4.0)
    bars.append(tcs - inner_t)
    bars.append(inner_t.offset(RIB / 2) - inner_t.offset(-RIB / 2))
    sash.append(ext(cs_union(bars) ^ plug_cs, -pl + GLASS - 0.01, -0.4))
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, CAS)]
    for sg in (-1, 1):
        u0, u1 = sorted((sg * W / 2, sg * (W / 2 + A)))
        um = (u0 + u1) / 2
        parts.append(ext(rect(u0, 2.2, u1, h + 0.2), 0.0, 1.0) - ext(stroke([(um, 3.2), (um, h - 1.2)], 0.5), 0.6, 1.2))
        parts.append(chamfer_box(u0 - 0.2, 0.0, u1 + 0.2, 2.2, 0.0, 1.2, c=0.3, bottom=0.0))
        parts.append(chamfer_box(u0 - 0.3, h - 0.2, u1 + 0.3, h + 1.3, 0.0, 1.4, c=0.4, bottom=0.8))
    half = W / 2 + A + 0.3
    parts.append(ext(rect(-half, h + 1.1, half, h + 2.6), 0.0, CAS))
    parts.append(dentils(-half + 0.2, half - 0.2, h + 2.2, 1.0, 0.0, 1.0))
    vb = h + 3.0
    parts.append(MD.run(-half - 0.5, half + 0.5, vb + 1.0, MD.CROWN, 1.2, up=False))
    top = vb + 1.0
    rise = 0.42 * (half + 0.5)
    tri = poly([(-half - 0.5, top - 0.01), (half + 0.5, top - 0.01), (0.0, top + rise)])
    parts.append(MD.band(tri, 1.1, MD.CROWN, clip=rect(-half - 2, top + 0.3, half + 2, top + 20)))
    parts.append(ext(tri.offset(-1.0, JoinType.Miter, 4.0) + (rect(-half + 0.6, top - 0.3, half - 0.6, top + 0.3) ^ tri), 0.0, CAS))
    oc = (0.0, top + rise * 0.36)
    rr = min(1.2, rise * 0.24)
    parts.append(ext(circle(oc, rr + 0.55, 28) - circle(oc, rr, 28), CAS - 0.01, 1.2))
    return _one_piece(sash, parts, op, plug_cs, PLUG, top + rise, 0.0)

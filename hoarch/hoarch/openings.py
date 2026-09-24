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

from manifold3d import JoinType, Manifold as M

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
                  clip=False, apron=False, consoles=None, qa=False):
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


def door_ornate(w, h, leaves=2, transom=4.2, head="swan", pil=1.6):
    """Queen Anne entrance: ornate leaves (round-headed lights, quatrefoil panels), a
    sunburst transom, panelled pilasters on plinths with bullseye capitals, and either
    ``head="swan"``: a frieze with a cartouche and swags, a cornice and a broken swan-neck
    pediment with an urn, or ``head="pediment"``: a segmental pediment with a sunburst.
    Local frame as the windows (u centred, v from the sill, w out of the wall)."""
    op, plug_cs, sash_parts = _ornate_door_sash(w, h, leaves, transom)
    parts = []
    return _door_ornate_surround(w, h, op, plug_cs, sash_parts, head, pil)


def _ornate_door_sash(w, h, leaves, transom):
    """The ornate leaves and sunburst transom of door_ornate / door_se (the plug part)."""
    op = rect(-w / 2, 0, w / 2, h)
    plug_cs = op.offset(-CLR, JoinType.Miter, 4.0)
    pl = PLUG
    dh = h - transom
    mid = SLOT if leaves > 1 else 0.0
    lw = (w - 2 * CLR - 1.0 - mid * (leaves - 1)) / leaves
    u = -w / 2 + CLR + 0.5
    parts, lights = [], []
    for i in range(leaves):
        lp, light = _ornate_leaf(u, lw, dh, hinge_left=(i == 0))
        parts += lp
        lights.append(light)
        u += lw + mid
    glass = cs_union(lights)
    cut = ext(glass, -pl - 1, 0.0)
    parts = [p - cut for p in [ext(plug_cs, -pl, -1.0)] + parts]
    parts.append(ext(glass, -pl, -pl + GLASS))
    ring = plug_cs - plug_cs.offset(-0.5, JoinType.Miter, 4.0)
    parts.append(ext(ring, -pl, 0.0))
    if transom > 0:
        tcs = rect(-w / 2 + CLR + 0.5, dh + 0.2, w / 2 - CLR - 0.5, h - CLR - 0.5)
        parts = [p - ext(tcs, -pl - 1, -0.99) for p in parts]
        parts.append(ext(tcs, -pl, -pl + GLASS))
        parts.append(ext(rect(-w / 2, dh - 0.3, w / 2, dh + 0.3), -pl, -0.4))             # transom bar
        tb = tcs.bounds()
        hub, rays = sunburst((0.0, tb[1]), 1.0, 1.6, max(tb[2], tb[3] - tb[1]) + 2.0, n=7, a0=0.2, a1=math.pi - 0.2,
                             ray0=RIB, ray1=RIB + 0.1)
        parts.append(ext((hub + rays) ^ tcs, -pl + GLASS - 0.01, -0.6))
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
        parts.append(ext(rect(-w / 2, h, w / 2, h + 2.2), 0.0, CAS))
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
            fields.append(poly([tuple(p) for p in pts] + [(p3[0], vc), (p0[0], vc)]))
            necks.append(volute((p3[0], p3[1] - 0.6), 0.95, turns=0.85, band=0.55, a0=math.pi / 2,
                                sense=1 if sg > 0 else -1))
            ros.append(circle((sg * (cw * 0.62), vc + 1.0), 0.45, 16))
        parts.append(ext(cs_union(fields), 0.0, CAS))
        parts.append(ext(cs_union(necks), 0.0, 1.2))
        parts.append(ext(cs_union([stroke(bezier((sg * (cw - 0.45), vc + 0.4), (sg * cw * 0.55, vc + 0.4),
                                                 (sg * cw * 0.5, vc + 3.1), (sg * 2.1, vc + 3.1), 28), 0.5)
                                   for sg in (-1, 1)]), 1.2 - 0.01, 1.6))
        parts.append(ext(cs_union(ros), CAS - 0.01, 1.0))
        parts.append(ext(urn_cs(0.0, vc, 3.4, 1.9), 0.0, 1.2))
        parts.append(ext(circle((0.0, vc + 3.4 * 3.35 / 4), 0.38, 16), 1.2 - 0.01, 1.4))
        top = vc + 3.6
    else:
        parts.append(ext(rect(-w / 2, h, w / 2, h + 2.2), 0.0, CAS))
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


def door_se(w, h, leaves=2, transom=4.4, pil=2.0, arch_w=1.8, head="pediment"):
    """Second Empire entrance: the ornate leaves and fanlight of door_ornate in a moulded
    architrave, fluted pilasters on plinths with moulded capitals, an entablature (frieze
    with a cartouche between rosettes, dentils, a crowned cornice returned over the
    pilasters) and a segmental pediment with a fan and a palmette on the apex."""
    from . import moulding as MD
    op, plug_cs, sash_parts = _ornate_door_sash(w, h, leaves, transom)
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


def door_romanesque(w, h, orders=2, col=1.3, L=3.0, plug=True, leaves=2):
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
            lp, light = _ornate_leaf(u, lw, dh, hinge_left=(i == 0))
            body += lp
            lights.append(light)
            u += lw + mid
        fan = plug_cs.offset(-0.5, JoinType.Miter, 4.0) ^ rect(-w, spring + 0.3, w, h + 5)
        glass = cs_union(lights) + fan
        cut = ext(glass, -pl - 1, 0.0)
        sash = [p - cut for p in body]
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

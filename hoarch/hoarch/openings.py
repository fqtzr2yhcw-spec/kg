"""Window and door inserts that plug into wall openings from outside.

Construction (learned from the reference kit and kept as the house standard):
  * the wall has a plain opening; the insert has a *plug* that slides into it
    with CLR clearance per side and PLUG depth;
  * the glazing is the plug's back face: GLASS thick (two 0.2 mm layers), so it
    glows when lit and the sash reads as recessed;
  * the casing, sill and hood sit on the wall face (w >= 0);
  * inserts print face-up: local w becomes print z (+PLUG), no supports.

All geometry is in a local (u, v, w) frame: u = 0 at the opening centre,
v = 0 at the opening bottom, w = 0 at the wall face.
"""
import math

from manifold3d import JoinType

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


def footprint(surround, op, grow=0.15):
    """Where the siding must stop for an insert: the surround's own outline seen from the
    front (plus a hair), so the clapboards run right up to the trim with no bare patches."""
    return cs_union([surround.project().offset(grow, JoinType.Miter, 4.0), op.offset(grow, JoinType.Miter, 4.0)])


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
    bracketed sill, moulded hood with keystone; ``style`` in {"crest", "key", "flat"}.
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
    parts = []
    # --- plug ring + glass + sash --------------------------------------------------
    frame_w = 0.55
    glass = ext(plug_cs, -PLUG, -PLUG + GLASS)
    ring = ext(plug_cs - plug_cs.offset(-frame_w, JoinType.Miter, 4.0), -PLUG, 0.0)
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
    parts.append(ext(sash, -PLUG + GLASS, -SASH_REC))
    # upper sash frame (a second frame line just inside the ring reads as the sash stile)
    parts.append(ext(inner - inner.offset(-RIB, JoinType.Miter, 4.0), -PLUG + GLASS, -SASH_REC))
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
        return _window_qa(w, h, rise, spring, op, cas_out, casing, style, apron, clip, parts, sash_parts)
    # ears: small outward steps at the spring line (a flat cap on consoles has none)
    consoles = (style == "flat") if consoles is None else consoles
    ear_h = 1.1
    for s in (() if (style == "flat" and consoles) else (-1, 1)):
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
    sur = union(parts)
    sash = union(sash_parts)
    land = footprint(sur, op)
    return dict(insert=sash + sur, sash=sash, surround=sur, cut=op, landing=land, top=top, bottom=bottom)


def door_insert(w, h, leaves=2, transom=0.0, casing=1.2, crown=True, glass_top=True):
    """Panelled door(s) with an Italianate crown (cornice cap on two consoles).

    transom > 0 adds a glazed transom of that height at the top of the opening."""
    op = rect(-w / 2, 0, w / 2, h)
    plug_cs = op.offset(-CLR, JoinType.Miter, 4.0)
    parts = [ext(plug_cs, -PLUG, -1.0)]                             # door slab back
    ring = plug_cs - plug_cs.offset(-0.5, JoinType.Miter, 4.0)
    parts.append(ext(ring, -PLUG, 0.0))
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
                parts[-1] = parts[-1] - ext(pc.offset(-0.25, JoinType.Miter), -PLUG + 0.4, 0.5)
                parts.append(ext(pc.offset(-0.25, JoinType.Miter), -PLUG, -PLUG + GLASS))
                continue
            parts.append(stepped(pc, [(0.0, -0.8, -0.6), (0.3, -0.6, -0.4)]))
        u += lw + mid
    if transom > 0:
        tcs = rect(-w / 2 + CLR + 0.5, dh + 0.2, w / 2 - CLR - 0.5, h - 0.5)
        parts.append(ext(tcs, -PLUG, -PLUG + GLASS))
        parts.append(ext(rect(-w / 2, dh - 0.3, w / 2, dh + 0.3), -PLUG, -0.4))
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
    sur = union(parts)
    sash = union(sash_parts)
    land = footprint(sur, op)
    return dict(insert=sash + sur, sash=sash, surround=sur, cut=op, landing=land, top=top, bottom=0.0)


def twin_arch_window(w, h, balcony=5.0, casing=1.0):
    """Paired round-arched lights under one hood with a bracketed balcony below
    (tower window). The balcony is part of the insert and prints standing on the
    wall face (w up), so its brackets need no support."""
    op = opening_cs(w, h, None)
    plug_cs = op.offset(-CLR, JoinType.Miter, 4.0)
    parts = [ext(plug_cs, -PLUG, -PLUG + GLASS),
             ext(plug_cs - plug_cs.offset(-0.5, JoinType.Miter, 4.0), -PLUG, 0.0)]
    # centre colonnette + two arched lights
    lw = (w - 2 * CLR - 1.0 - 0.8) / 2
    spring = h - w / 2
    col = rect(-0.4, 0, 0.4, spring + 0.5)
    lights = []
    for s in (-1, 1):
        c = s * (0.4 + lw / 2)
        lights.append(arch_cs(c - lw / 2, c + lw / 2, 0.4, spring + (w / 2 - lw / 2) * 0.35))
    frame_cs = plug_cs.offset(-0.5, JoinType.Miter, 4.0) - cs_union(lights)
    parts.append(ext(frame_cs + col, -PLUG + GLASS, -SASH_REC))
    parts.append(ext(rect(-0.55, spring - 0.2, 0.55, spring + 0.25), -PLUG + GLASS, 0.0))   # capital
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
    sur = union(parts)
    sash = union(sash_parts)
    land = footprint(sur, op)
    if balcony:       # keep the wall bare where the balcony's floor and brackets land
        land = land + rect(-bw - 0.3, -4.2, bw + 0.3, 0.2)
    return dict(insert=sash + sur, sash=sash, surround=sur, cut=op, landing=land, top=cy + r0 + 1.3,
                bottom=-0.9 if balcony else -1.9)


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


def _window_qa(w, h, rise, spring, op, cas_out, casing, style, apron, clip, parts, sash_parts):
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
    sur = union(parts)
    sash = union(sash_parts)
    land = footprint(sur, op)
    return dict(insert=sash + sur, sash=sash, surround=sur, cut=op, landing=land, top=top, bottom=bottom)


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
    op = rect(-w / 2, 0, w / 2, h)
    plug_cs = op.offset(-CLR, JoinType.Miter, 4.0)
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
    cut = ext(glass, -PLUG - 1, 0.0)
    parts = [p - cut for p in [ext(plug_cs, -PLUG, -1.0)] + parts]
    parts.append(ext(glass, -PLUG, -PLUG + GLASS))
    ring = plug_cs - plug_cs.offset(-0.5, JoinType.Miter, 4.0)
    parts.append(ext(ring, -PLUG, 0.0))
    if transom > 0:
        tcs = rect(-w / 2 + CLR + 0.5, dh + 0.2, w / 2 - CLR - 0.5, h - CLR - 0.5)
        parts = [p - ext(tcs, -PLUG - 1, -0.99) for p in parts]
        parts.append(ext(tcs, -PLUG, -PLUG + GLASS))
        parts.append(ext(rect(-w / 2, dh - 0.3, w / 2, dh + 0.3), -PLUG, -0.4))           # transom bar
        tb = tcs.bounds()
        hub, rays = sunburst((0.0, tb[1]), 1.0, 1.6, max(tb[2], tb[3] - tb[1]) + 2.0, n=7, a0=0.2, a1=math.pi - 0.2,
                             ray0=RIB, ray1=RIB + 0.1)
        parts.append(ext((hub + rays) ^ tcs, -PLUG + GLASS - 0.01, -0.6))
    sash_parts, parts = parts, []
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
    sur = union(parts)
    sash = union(sash_parts)
    land = footprint(sur, op)
    return dict(insert=sash + sur, sash=sash, surround=sur, cut=op, landing=land, top=top, bottom=0.0)

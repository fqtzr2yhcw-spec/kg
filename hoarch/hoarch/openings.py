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

from .core import RIB, SLOT, arch_cs, cs_union, poly, rect, union
from .ornament import chamfer_box, console, dentils, ext, fan_crest, keystone, rosette_block, stepped

CLR = 0.15      # plug clearance per side
PLUG = 1.6      # plug depth into a 3.0 mm wall (8 x 0.2 mm layers)
GLASS = 0.4     # glazing thickness (2 x 0.2 mm layers)
SASH_REC = 0.4  # sash face sits this far behind the wall face
# face-up relief heights above the wall face sit on the 0.2 mm layer grid:
CAS = 0.6       # flat casing band
BEAD = 1.0      # raised back-band / bead on the casing


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
                  clip=False, apron=False, consoles=None):
    """Italianate window: segmental- or round-arched head, eared casing,
    bracketed sill, moulded hood with keystone; ``style`` in {"crest", "key", "flat"}.
    ``apron``: a panelled apron under the sill instead of the two sill brackets.
    ``consoles``: scroll consoles carrying a flat cap (default on for "flat").

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
        rim = (band.offset(0.0, JoinType.Round) - band.offset(-RIB, JoinType.Round)) ^ rect(-w, spring, w, h + 20)
        parts.append(ext(rim, 1.0, 1.2))
        # corbel blocks under the hood ends
        for s in (-1, 1):
            if ends >= 0.6:
                parts.append(rosette_block(s * (endw - 0.55), spring - 1.0, 1.0, 0.0, 1.1))
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
    lw = w / 2 + casing + ends + 0.6
    if style not in ("crest", "key"):
        lw = max(lw, w / 2 + casing + 0.8 + 0.3 + 0.2)          # the flat cap's drip reaches past the ends
    land = cs_union([cas_out, rect(-sw - 0.3, bottom - 0.15, sw + 0.3, 0.1), rect(-lw, spring - 1.6, lw, top)])
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
        parts.append(ext(rect(-cw, v0 + 2.2, cw, v0 + 2.8), 0.0, 1.9))                      # cap
        parts.append(ext(rect(-cw - 0.3, v0 + 2.8, cw + 0.3, v0 + 3.3), 0.0, 2.2))
        for s in (-1, 1):
            parts.append(console(3.2, 1.6, 0.8, u=s * (cw - 0.6), v_top=v0 + 2.2, w0=0.0))
        top = v0 + 3.3
    sur = union(parts)
    sash = union(sash_parts)
    land = cs_union([cas_out, rect(-(w / 2 + casing + 1.5), h, w / 2 + casing + 1.5, top),
                     rect(-(w / 2 + casing + 0.4), 0.0, w / 2 + casing + 0.4, 2.4)])
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
    # no sill: the separate balcony floor is the sill; keep the wall bare behind it
    bw = w / 2 + casing + 2.0
    sur = union(parts)
    sash = union(sash_parts)
    land = cs_union([cas_out, rect(-bw - 0.3, -4.2, bw + 0.3, 0.2),
                     rect(-(w / 2 + casing + 1.6), 0.0, w / 2 + casing + 1.6, cy + r0 + 1.6 + 2.6)])
    return dict(insert=sash + sur, sash=sash, surround=sur, cut=op, landing=land, top=cy + r0 + 1.3, bottom=-0.9)


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

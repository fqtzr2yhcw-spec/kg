"""Colonial and Colonial Revival parts for the third batch (houses 31 to 40): window and door
families, shutters, porticoes, railings, dormers and chimneys, and the batch's own cornice
ornament (friezes, courses, brackets) and foundation facings, which register themselves with
``cornice`` and ``trimwork`` on import. As everywhere in the collection, each house takes its
own family and patterns.

Frames follow ``openings``: local (u, v, w) with u = 0 at the opening centre, v = 0 at its
bottom, w = 0 on the wall face; a one-piece insert is a plug with the glass and sash plus the
surround, printed face-up with supports under the surround."""
import math

import numpy as np
from manifold3d import JoinType, Manifold as M

from .core import RIB, SLOT, box, circle, cs_union, poly, rect, union
from .ornament import chamfer_box, ext, oval, stroke
from . import cornice as CO, moulding as MD, openings as O, trimwork as TW


def _st(cs, b, d):
    """Relief on an upright face: each 0.2 layer pulled up 0.2 underneath (no overhang)."""
    return CO._stepped(cs, b, d)


def _lens(c, length, width, ang, seg=10):
    """A pointed leaf (two arcs meeting at the tips), ``length`` long, centred on c."""
    ca, sa = math.cos(ang), math.sin(ang)
    pts = []
    for s in np.linspace(-1, 1, seg + 1):
        pts.append((s * length / 2, width / 2 * (1 - s * s)))
    for s in np.linspace(1, -1, seg + 1)[1:-1]:
        pts.append((s * length / 2, -width / 2 * (1 - s * s)))
    return poly([(c[0] + x * ca - y * sa, c[1] + x * sa + y * ca) for x, y in pts])


def _husk(c, length, width, ang):
    """A bell-flower husk: a round head and a point, ``ang`` the direction of the point."""
    ca, sa = math.cos(ang), math.sin(ang)
    r = width / 2
    tip = (c[0] + (length - r) * ca, c[1] + (length - r) * sa)
    side = (-sa * r, ca * r)
    return cs_union([circle(c, r, 14), poly([(c[0] + side[0], c[1] + side[1]), tip, (c[0] - side[0], c[1] - side[1])])])


# ------------------------------------------------------------------ friezes (the Whitmore)
def frieze_husks(L, h, b, pitch, margin, pair, half):
    """Adam husks: at every station a patera with a drop of three husks under it, and between
    the stations a swag of husks hanging from the head."""
    v0, v1 = 0.8, h - 0.8
    hh = v1 - v0
    out = []
    r = min(0.85, hh / 2 - 0.35)
    for u in CO._us(L, pitch, margin, 0.0):
        vc = v1 - r - 0.1
        out.append(_st(circle((u, vc), r, 20) - circle((u, vc), max(0.3, r - 0.5), 20), b, 0.4))
        out.append(_st(circle((u, vc), 0.3, 10), b, 0.6))
        v = vc - r - 0.25
        for k, s in enumerate((0.95, 0.8, 0.65)):
            if v - s < v0 - 0.05:
                break
            out.append(_st(_husk((u, v - 0.3), s, 0.62 - 0.06 * k, -math.pi / 2), b, 0.4))
            v -= s + 0.05
    for uc, wd in CO._between(L, pitch, margin, pair, half):
        a, e = uc - wd / 2 + 0.5, uc + wd / 2 - 0.5
        sag = min(hh - 1.0, 1.9)
        n = max(3, int((e - a) / 1.0))
        for k in range(n):
            t = (k + 0.5) / n
            x = a + (e - a) * t
            y = v1 - 0.45 - sag * 4 * t * (1 - t)
            slope = -sag * 4 * (1 - 2 * t) / (e - a)
            ang = math.atan(slope) + (math.pi if t > 0.5 else 0.0)
            out.append(_st(_husk((x, y), 0.9, 0.6, ang - (0.0 if t > 0.5 else 0.0)), b, 0.4))
    return out, []


def frieze_laurel(L, h, b, pitch, margin, pair, half):
    """A bay-leaf garland: pairs of pointed leaves along a stem, each half of a bay pointing
    in to a berry at its middle, a crossed ribbon tie at every station."""
    v0, v1 = 0.8, h - 0.8
    vm = (v0 + v1) / 2
    hh = v1 - v0
    out = [_st(rect(margin * 0.5, vm - 0.25, L - margin * 0.5, vm + 0.25), b, 0.3)]
    lf = min(1.5, hh * 0.55)
    for uc, wd in CO._between(L, pitch, margin, pair, 0.9):
        n = max(1, int((wd / 2 - 0.6) / 1.05))
        for side in (-1, 1):
            for k in range(n):
                x = uc - side * (wd / 2 - 0.5 - k * 1.05)
                ang_up = math.radians(35) if side < 0 else math.pi - math.radians(35)
                ang_dn = -math.radians(35) if side < 0 else math.pi + math.radians(35)
                for ang, dv in ((ang_up, 0.35), (ang_dn, -0.35)):
                    c = (x + math.cos(ang) * lf * 0.45, vm + dv + math.sin(ang) * lf * 0.3)
                    out.append(_st(_lens(c, lf, 0.62, ang), b, 0.4))
        out.append(_st(circle((uc, vm), 0.5, 12), b, 0.6))
    for u in CO._us(L, pitch, margin, 0.0):
        tie = stroke([(u - 0.7, vm - hh * 0.35), (u + 0.7, vm + hh * 0.35)], 0.5) + \
            stroke([(u - 0.7, vm + hh * 0.35), (u + 0.7, vm - hh * 0.35)], 0.5)
        out.append(_st(tie ^ rect(u - 1.0, v0, u + 1.0, v1), b, 0.5))
    return out, []


def frieze_tablets(L, h, b, pitch, margin, pair, half):
    """Federal tablets: a raised tablet with three reeds at every station, an oval patera in
    every bay between them."""
    v0, v1 = 0.8, h - 0.8
    vm = (v0 + v1) / 2
    hh = v1 - v0
    out = []
    tw = 1.1
    for u in CO._us(L, pitch, margin, 0.0):
        out.append(_st(rect(u - tw, v0 + 0.1, u + tw, v1 - 0.1), b, 0.4))
        for dx in (-0.6, 0.0, 0.6):
            out.append(_st(rect(u + dx - 0.2, v0 + 0.4, u + dx + 0.2, v1 - 0.4), b + 0.4, 0.2))
    for uc, wd in CO._between(L, pitch, margin, pair, tw):
        rx, ry = min(wd / 2 - 0.6, 2.2), min(hh / 2 - 0.1, 1.3)
        if rx < 0.8:
            continue
        out.append(_st(oval((uc, vm), rx, ry) - oval((uc, vm), rx - 0.5, ry - 0.5), b, 0.4))
        out.append(_st(oval((uc, vm), max(0.35, rx - 1.3), max(0.3, ry - 0.9)), b, 0.5))
    return out, []


# ------------------------------------------------------------------ courses (the Whitmore)
def course_troy(L, h, b, pitch, margin, p):
    """A crenellated (Wall of Troy) dentil course: tall and short teeth in turn, all standing
    on the course's foot."""
    tooth, gap = p.get("tooth", 0.9), p.get("gap", 0.6)
    n = int((L - 1.2) / (tooth + gap))
    u0 = (L - (n * (tooth + gap) - gap)) / 2
    out = []
    for k in range(n):
        u = u0 + k * (tooth + gap)
        top = h if k % 2 == 0 else round(h * 0.55 / 0.2) * 0.2
        out.append(ext(rect(u, 0.0, u + tooth, top), b - 0.05, b + p.get("d", 0.7)))
    return out


# ------------------------------------------------------------------ brackets (the Whitmore)
def bracket_mutule(h, d, t):
    """A Georgian block modillion: a long block with a square front and an ogee underside
    sweeping back to the wall, a bead under its nose (side profile, top at v = 0)."""
    hb = min(h, max(1.6, 0.42 * d))
    pts = [(0.0, 0.0), (d, 0.0), (d, -hb * 0.55)]
    pts += [(d - (d * 0.62) * (s - math.sin(2 * math.pi * s) / (2 * math.pi)), -hb * 0.55 - hb * 0.45 * s)
            for s in np.linspace(0.1, 1.0, 10)]
    pts += [(0.0, -hb)]
    return cs_union([poly(pts), circle((d - 0.35, -hb * 0.55), 0.35, 12)])


# ------------------------------------------------------------------ foundations (the Whitmore)
def foundation_watertable(reg, seed=0):
    """English-bond brick under a moulded water table: a course of bricks set out and bevelled
    at the top of the foundation (the Whitmore)."""
    from . import skins as S
    b = reg.bounds()
    body = S.brick_bond(reg ^ rect(b[0] - 1, b[1] - 1, b[2] + 1, b[3] - 1.6), "english", d=0.25)
    wt = chamfer_box(b[0], b[3] - 1.6, b[2], b[3], 0.0, 0.8, c=0.2, square=("u0", "u1"), bottom=0.8)
    return body + wt


CO.FRIEZE_EXTRA.update(husks=frieze_husks, laurel=frieze_laurel, tablets=frieze_tablets)
CO.COURSE_EXTRA.update(troy=course_troy)
TW.BRACKET_EXTRA.update(mutule=bracket_mutule)
TW.FOUNDATION_EXTRA.update(watertable=foundation_watertable)


# ------------------------------------------------------------------ Georgian windows and doors (the Whitmore)
def window_georgian(w, h, lintel="keyed", lites=(3, 3), rows=(2, 2), A=1.0, apron=False):
    """Georgian window: six-over-six sash in a narrow brickmould casing with a back-band, a
    splayed stone jack arch over it (its joints radiating from a point below), a stone sill;
    ``lintel`` "keyed" adds a tall raised keystone, "plain" a flush one; ``apron`` a sunk panel
    under the sill (the lower windows)."""
    op = O.opening_cs(w, h, 0)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    sash = O.window_insert(w, h, 0, lites=lites, rows=rows, bare=True)["insert"]
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS)]
    frame = (op.offset(A, JoinType.Miter, 4.0) - op) ^ rect(-w, 0.0, w, h + A)
    parts.append(ext(frame, 0.0, O.CAS))
    bead = (op.offset(A, JoinType.Miter, 4.0) - op.offset(A - 0.5, JoinType.Miter, 4.0)) ^ rect(-w, 0.0, w, h + A)
    parts.append(ext(bead, O.CAS - 0.01, O.BEAD))
    ha = 3.2
    vb = h + A - 0.1
    wb = w / 2 + A + 0.5
    wt = wb + ha * 0.4
    lint = poly([(-wb, vb), (wb, vb), (wt, vb + ha), (-wt, vb + ha)])
    parts.append(ext(lint, 0.0, 1.0))
    focus = (0.0, vb - 6.0)                          # the joints radiate from here
    joints = []
    for k in range(-3, 4):
        if k == 0:
            continue
        x = k * wb / 3.5
        dx, dy = x - focus[0], vb - focus[1]
        s_ = ha / dy
        joints.append(stroke([(x, vb - 0.1), (x + dx * s_ * 1.05, vb + ha + 0.1)], 0.3, caps=False))
    parts[-1] = parts[-1] - ext(cs_union(joints) ^ lint, 0.8, 1.2)
    top = vb + ha
    if lintel == "keyed":
        kb, kt = 1.5, 2.2
        parts.append(chamfer_box(-kb / 2, vb - 0.4, kb / 2, vb + ha + 1.0, 0.0, 1.6, c=0.3))
        parts[-1] = parts[-1] + ext(poly([(-kb / 2, vb - 0.4), (kb / 2, vb - 0.4), (kt / 2, vb + ha + 1.0),
                                          (-kt / 2, vb + ha + 1.0)]), 0.0, 1.3)
        top = vb + ha + 1.0
    else:
        parts.append(ext(poly([(-0.7, vb), (0.7, vb), (0.95, vb + ha), (-0.95, vb + ha)]), 0.99, 1.3))
    sw = w / 2 + A + 0.8
    parts.append(MD.run(-sw, sw, 0.0, MD.SILL, 1.2, up=False))
    bottom = -1.2
    if apron:                                        # a board under the sill, framed, a raised panel on it
        ap = rect(-w / 2 - 0.2, -4.4, w / 2 + 0.2, -1.0)
        parts.append(ext(ap, 0.0, 0.4))
        parts.append(ext(ap - ap.offset(-0.55, JoinType.Miter, 4.0), 0.39, 0.8))
        parts.append(chamfer_box(-w / 2 + 0.7, -3.6, w / 2 - 0.7, -1.9, 0.39, 0.4, c=0.2))
        bottom = -4.4
    return O._one_piece([sash], parts, op, plug_cs, O.PLUG, top, bottom)


def window_oculus(d, A=1.1):
    """A round window (oculus) with a cross of bars, a moulded ring and four keystones."""
    r = d / 2
    c = (0.0, r)
    op = circle(c, r, 48)
    plug_cs = circle(c, r - O.CLR, 48)
    pl = O.PLUG
    g = circle(c, r - O.CLR - 0.6, 48)
    sash = [ext(plug_cs - g, -pl, 0.0), ext(g, -pl, -pl + O.GLASS)]
    bars = (rect(-r, r - RIB / 2, r, r + RIB / 2) + rect(-RIB / 2, 0.0, RIB / 2, d)) ^ plug_cs
    sash.append(ext(bars, -pl + O.GLASS - 0.01, -0.6))
    parts = [ext(op - circle(c, r - RIB, 48), 0.0, O.CAS)]
    ring = circle(c, r + A, 48) - op
    parts.append(ext(ring, 0.0, 0.8))
    parts.append(ext(circle(c, r + A, 48) - circle(c, r + A - 0.5, 48), 0.79, 1.2))
    for a in (0.0, math.pi / 2, math.pi, 3 * math.pi / 2):
        ca, sa = math.cos(a), math.sin(a)
        k = poly([(c[0] + ca * (r - 0.2) - sa * 0.7, c[1] + sa * (r - 0.2) + ca * 0.7),
                  (c[0] + ca * (r - 0.2) + sa * 0.7, c[1] + sa * (r - 0.2) - ca * 0.7),
                  (c[0] + ca * (r + A + 0.9) + sa * 0.95, c[1] + sa * (r + A + 0.9) - ca * 0.95),
                  (c[0] + ca * (r + A + 0.9) - sa * 0.95, c[1] + sa * (r + A + 0.9) + ca * 0.95)])
        parts.append(ext(k, 0.0, 1.4))
    return O._one_piece(sash, parts, op, plug_cs, pl, d + A + 0.9, -A - 0.9)


def door_georgian(w, h, transom=4.6, A=1.4):
    """Georgian entrance: a six-panel door under a five-light transom, reeded casings on
    plinth blocks, rosette corner blocks and a reeded head."""
    op = rect(-w / 2, 0, w / 2, h)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    dh = h - transom
    body = [ext(plug_cs, -pl, -1.0)]
    lp, _ = O._leaf("six_panel", -w / 2 + 0.2, w - 0.4, dh, True)
    body += lp
    tcs = rect(-w / 2 + O.CLR + 0.5, dh + 0.3, w / 2 - O.CLR - 0.5, h - O.CLR - 0.5)
    body = [p - ext(tcs, -pl + O.GLASS, 0.5) for p in body]
    sash = body + [ext(tcs, -pl, -pl + O.GLASS), ext(plug_cs - plug_cs.offset(-0.5, JoinType.Miter, 4.0), -pl, 0.0)]
    bars = [rect(-w, dh - 0.3, w, dh + 0.3)]
    for k in range(1, 5):
        x = -w / 2 + w * k / 5
        bars.append(rect(x - RIB / 2, dh, x + RIB / 2, h))
    sash.append(ext(cs_union(bars) ^ plug_cs, -pl + O.GLASS - 0.01, -0.4))
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS)]
    for sg in (-1, 1):
        u0, u1 = sorted((sg * w / 2, sg * (w / 2 + A)))
        um = (u0 + u1) / 2
        jamb = ext(rect(u0, 2.4, u1, h), 0.0, 1.0)
        for dx in (-0.4, 0.4):
            jamb = jamb - ext(rect(um + dx - 0.15, 3.0, um + dx + 0.15, h - 0.6), 0.8, 1.2)
        parts.append(jamb)
        parts.append(chamfer_box(u0 - 0.2, 0.0, u1 + 0.2, 2.4, 0.0, 1.2, c=0.3, bottom=0.0))
        parts.append(chamfer_box(u0 - 0.1, h - 0.1, u1 + 0.1, h + A + 0.1, 0.0, 1.2, c=0.3))
        parts.append(MD.rosette(um, h + A / 2, 0.55, 1.19, 0.6))
    head = ext(rect(-w / 2, h, w / 2, h + A), 0.0, 1.0)
    for dv in (-0.4, 0.0, 0.4):
        head = head - ext(rect(-w / 2 + 0.3, h + A / 2 + dv - 0.12, w / 2 - 0.3, h + A / 2 + dv + 0.12), 0.8, 1.2)
    parts.append(head)
    return O._one_piece(sash, parts, op, plug_cs, pl, h + A + 0.1, 0.0)


def door_venetian(w, h, A=1.2, pil=1.4):
    """A round-headed French window onto a balcony: two glazed leaves under a fanlight of
    radiating bars round a hub, fluted pilasters with impost blocks, an archivolt with a
    keystone."""
    spring = h - w / 2
    op = O.opening_cs(w, h, None)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    dh = spring - 0.4
    lw = (w - 2 * O.CLR - 1.0 - SLOT) / 2
    u = -w / 2 + O.CLR + 0.5
    body, lights = [ext(plug_cs, -pl, -1.0)], []
    for i in range(2):
        lp, light = O._leaf("french", u, lw, dh, i == 0)
        body += lp
        if light is not None:
            lights.append(light)
        u += lw + SLOT
    fan = plug_cs.offset(-0.5, JoinType.Miter, 4.0) ^ rect(-w, spring + 0.3, w, h + 5)
    g = cs_union(lights) + fan
    sash = [p - ext(g, -pl - 1, 0.0) for p in body]
    sash += [ext(g, -pl, -pl + O.GLASS), ext(plug_cs - plug_cs.offset(-0.5, JoinType.Miter, 4.0), -pl, 0.0),
             ext(rect(-w, spring - 0.3, w, spring + 0.3) ^ plug_cs, -pl, -0.4)]
    hub = circle((0.0, spring), 1.3, 24) ^ rect(-2, spring, 2, spring + 2)
    rays = cs_union([stroke([(1.3 * math.cos(a), spring + 1.3 * math.sin(a)), (9 * math.cos(a), spring + 9 * math.sin(a))], RIB)
                     for a in np.linspace(math.pi / 6, 5 * math.pi / 6, 5)])
    sash.append(ext((rays + hub) ^ fan, -pl + O.GLASS - 0.01, -0.6))
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS)]
    for sg in (-1, 1):
        u0, u1 = sorted((sg * w / 2, sg * (w / 2 + pil)))
        um = (u0 + u1) / 2
        p_ = ext(rect(u0, 1.6, u1, spring - 1.2), 0.0, 1.0) - ext(stroke([(um, 2.4), (um, spring - 2.0)], 0.45), 0.6, 1.2)
        parts.append(p_)
        parts.append(chamfer_box(u0 - 0.2, 0.0, u1 + 0.2, 1.6, 0.0, 1.2, c=0.3, bottom=0.0))
        parts.append(chamfer_box(u0 - 0.3, spring - 1.3, u1 + 0.3, spring + 0.2, 0.0, 1.4, c=0.35))
    band = op.offset(A, JoinType.Round) ^ rect(-w, spring, w, h + 10)
    parts.append(MD.band(band, A, MD.CASING, clip=rect(-w, spring, w, h + 20) - op))
    kt = h + A + 1.0
    parts.append(chamfer_box(-0.7, h - 0.4, 0.7, kt, 0.0, 1.7, c=0.35))
    return O._one_piece(sash, parts, op, plug_cs, pl, kt, 0.0)


# ------------------------------------------------------------------ shutters (the Whitmore)
def shutter_louver_panel(w, h, t=0.8, stile=0.6):
    """A Colonial shutter: louvers over a lock rail, a raised panel below it. Local frame as
    features.shutter (u 0..w, v 0..h, back at w = 0; prints face-up)."""
    web = 0.4
    rv = round(h * 0.33 / 0.2) * 0.2
    parts = [ext(rect(0, 0, w, h) - rect(stile, stile, w - stile, h - stile), 0.0, t),
             ext(rect(stile, rv - stile / 2, w - stile, rv + stile / 2), 0.0, t)]
    field = rect(stile, rv + stile / 2, w - stile, h - stile)
    parts.append(ext(field, 0.0, web))
    b = field.bounds()
    n = max(1, int((b[3] - b[1] - SLOT) / 1.0))
    pitch = (b[3] - b[1] - SLOT) / n
    slats = [rect(b[0] - 0.1, b[1] + SLOT + k * pitch, b[2] + 0.1, b[1] + SLOT + k * pitch + min(RIB + 0.05, pitch - SLOT))
             for k in range(n)]
    parts.append(ext(cs_union(slats) ^ field.offset(0.05), web, t - 0.2))
    pan = rect(stile, stile, w - stile, rv - stile / 2)
    parts.append(ext(pan, 0.0, web))
    parts.append(chamfer_box(stile + 0.35, stile + 0.35, w - stile - 0.35, rv - stile / 2 - 0.35, web - 0.01, t - web,
                             c=0.2))
    return union(parts)


def shutters_pair(opening_w, opening_h, casing=1.0, gap=0.7, t=0.8, h=None, make=shutter_louver_panel):
    """A pair of shutters (left, right) beside an opening, as features.shutters_for."""
    sw = opening_w / 2
    hh = opening_h if h is None else h
    left = make(sw, hh, t=t).translate([-(opening_w / 2 + casing + gap + sw), 0, 0])
    right = make(sw, hh, t=t).translate([opening_w / 2 + casing + gap, 0, 0])
    return left, right


# ------------------------------------------------------------------ chimney (the Whitmore)
def chimney_georgian(w=14.0, d=8.0, h=30.0):
    """A Georgian end stack: English-bond brick, a stone band two thirds up, a four-course
    corbelled cap under a stone coping, three square flue pots in a row. Stands on z = 0."""
    h = round(h / 0.2) * 0.2
    sh = round((h - 4.0) / 0.2) * 0.2
    body = box([-w / 2, -d / 2, 0], [w / 2, d / 2, sh]) + TW._skin(w, d, 0.0, sh, TW._brick("english"))
    zb = round(sh * 0.66 / 0.2) * 0.2
    body = body + TW._corbel_out(w, d, zb, 0.4) + box([-w / 2 - 0.4, -d / 2 - 0.4, zb - 0.01], [w / 2 + 0.4, d / 2 + 0.4, zb + 1.0])
    z = sh
    for k in range(4):
        g = 0.2 * (k + 1)
        body = body + box([-w / 2 - g, -d / 2 - g, z - 0.01], [w / 2 + g, d / 2 + g, z + 0.6])
        z += 0.6
    body = body + TW._corbel_out(w + 1.6, d + 1.6, z + 0.4, 0.4) + \
        box([-w / 2 - 1.2, -d / 2 - 1.2, z + 0.39], [w / 2 + 1.2, d / 2 + 1.2, z + 1.0])
    for k in (-1, 0, 1):
        body = body + TW._pot(1.2, 2.8, "square").translate([k * (w / 3.2), 0, z + 0.99])
    return body


# ------------------------------------------------------------------ Chippendale railing
def chippendale_panel(L, h, t=1.2, post=1.6, rail=0.9, n=None):
    """A Chinese Chippendale railing run, ``L`` long and ``h`` tall: square end posts, a
    bottom and a top rail, and between them panels of crossed diagonals inside a rectangle
    (a lattice of X's). Local frame u 0..L, v up, w 0..t; prints on its back (w = 0 on the bed)."""
    parts = [ext(rect(0.0, 0.0, post, h), 0.0, t), ext(rect(L - post, 0.0, L, h), 0.0, t),
             ext(rect(0.0, 0.0, L, rail), 0.0, t), ext(rect(0.0, h - rail, L, h), 0.0, t)]
    inner = rect(post, rail, L - post, h - rail)
    ib = inner.bounds()
    hh = ib[3] - ib[1]
    n = n or max(1, int(round((ib[2] - ib[0]) / (hh * 1.4))))
    pw = (ib[2] - ib[0]) / n
    bars = []
    for k in range(n):
        a, e = ib[0] + pw * k, ib[0] + pw * (k + 1)
        if k:
            bars.append(rect(a - 0.3, ib[1], a + 0.3, ib[3]))
        box_ = rect(a + 0.9, ib[1] + 0.8, e - 0.9, ib[3] - 0.8)
        bb = box_.bounds()
        bars.append(box_ - box_.offset(-0.5, JoinType.Miter, 4.0))
        bars.append(stroke([(a, ib[1]), (bb[0], bb[1])], 0.5) + stroke([(e, ib[1]), (bb[2], bb[1])], 0.5) +
                    stroke([(a, ib[3]), (bb[0], bb[3])], 0.5) + stroke([(e, ib[3]), (bb[2], bb[3])], 0.5))
        bars.append(stroke([(bb[0], bb[1]), (bb[2], bb[3])], 0.5) + stroke([(bb[0], bb[3]), (bb[2], bb[1])], 0.5))
    parts.append(ext(cs_union(bars) ^ inner, 0.0, t * 0.7))
    return union(parts)


# ------------------------------------------------------------------ the Whitmore's dormer
def dormer_pedimented(w=15.0, dep=16.0, hwall=13.0, rise=None):
    """A Georgian dormer: a flat front with pilaster strips, a round-headed six-light window
    (its lights open onto a dark core), a triangular pediment with a raking and a level
    cornice. Local: u across (centred), v up from its foot, w out (face at w = 0, the body back
    to w = -dep). Returns (body, core, face outline for the roof pocket and the dormer roof)."""
    rise = rise if rise is not None else w / 2 * 0.62
    face = poly([(-w / 2, 0.0), (w / 2, 0.0), (w / 2, hwall), (0.0, hwall + rise), (-w / 2, hwall)])
    body = ext(face, -dep, 0.0) - ext(face.offset(-1.2, JoinType.Miter, 4.0) ^ rect(-50, 1.2, 50, 99), -dep - 1, -1.2)
    lw = w * 0.42
    spring = hwall - 1.4 - lw / 2
    light = cs_union([rect(-lw / 2, 2.2, lw / 2, spring), circle((0.0, spring), lw / 2, 32) ^ rect(-lw, spring, lw, spring + lw)])
    body = body - ext(light, -1.3, 1.0)
    bars = cs_union([rect(-lw / 2, (2.2 + spring) / 2 - 0.25, lw / 2, (2.2 + spring) / 2 + 0.25),
                     rect(-0.25, 2.2, 0.25, spring + lw / 2)] +
                    [stroke([(0.0, spring), (lw / 2 * math.cos(a), spring + lw / 2 * math.sin(a))], 0.45)
                     for a in (math.pi / 4, 3 * math.pi / 4)]) ^ light
    body = body + ext(bars, -1.2, -0.5)
    body = body + ext((light.offset(0.8, JoinType.Round) - light) ^ rect(-w, 1.6, w, hwall + rise), -0.01, 0.6)
    body = body + chamfer_box(-lw / 2 - 1.0, 1.2, lw / 2 + 1.0, 2.2, -0.01, 0.9, c=0.3, bottom=0.9)       # sill
    for sg in (-1, 1):
        body = body + ext(rect(sg * (w / 2) - (1.2 if sg > 0 else 0.0), 1.2, sg * (w / 2) + (0.0 if sg > 0 else 1.2), hwall - 0.8),
                          -0.01, 0.5)
    lvl = rect(-w / 2 - 0.4, hwall - 0.8, w / 2 + 0.4, hwall + 0.2)                                       # level cornice
    body = body + ext(lvl, -0.01, 0.8)
    rake = face - face.offset(-0.9, JoinType.Miter, 4.0)
    body = body + ext(rake ^ rect(-50, hwall, 50, 99), -0.01, 0.8)
    core = ext(face.offset(-1.2, JoinType.Miter, 4.0) ^ rect(-50, 1.2, 50, hwall), -dep + 1.2, -1.2)
    return body, core, face


# ================================================================== the Westbrook (house 38)
# ------------------------------------------------------------------ friezes
def frieze_ribbon(L, h, b, pitch, margin, pair, half):
    """Ribbon and stick: a ribbon wound round a rod, the diagonal turns in relief, a bead
    between each pair of turns."""
    v0, v1 = 0.8, h - 0.8
    vm = (v0 + v1) / 2
    hh = v1 - v0
    out = [_st(rect(margin * 0.4, vm - 0.3, L - margin * 0.4, vm + 0.3), b, 0.2)]
    pu = max(1.6, hh * 0.75)
    n = int((L - margin) / pu)
    u0 = (L - n * pu) / 2
    for k in range(n):
        u = u0 + pu * k
        out.append(_st(poly([(u, v0 + 0.1), (u + 0.7, v0 + 0.1), (u + pu * 0.9, v1 - 0.1), (u + pu * 0.9 - 0.7, v1 - 0.1)]),
                       b + 0.2, 0.4))
    return out, []


def frieze_gougework(L, h, b, pitch, margin, pair, half):
    """Federal gouge-work: groups of sunk vertical flutes between drilled sunbursts, a sunk
    oval at every station."""
    v0, v1 = 0.8, h - 0.8
    vm = (v0 + v1) / 2
    hh = v1 - v0
    cuts, out = [], []
    for u in CO._us(L, pitch, margin, 0.0):
        rx, ry = min(1.4, pitch / 5), min(hh / 2 - 0.2, 1.1)
        cuts.append(ext(oval((u, vm), rx, ry) - oval((u, vm), max(0.45, rx - 0.7), max(0.4, ry - 0.6)), b - 0.3, b + 0.1))
    for uc, wd in CO._between(L, pitch, margin, pair, 1.6):
        n = max(2, int((wd - 1.0) / 0.9))
        for k in range(n):
            u = uc - (n - 1) * 0.45 + 0.9 * k
            cuts.append(ext(rect(u - 0.22, v0 + 0.3, u + 0.22, v1 - 0.3), b - 0.3, b + 0.1))
    return out, cuts


def frieze_urns(L, h, b, pitch, margin, pair, half):
    """Adam urns at the stations with a bead drapery looping between them."""
    from .ornament import urn_cs
    v0, v1 = 0.8, h - 0.8
    hh = v1 - v0
    out = []
    for u in CO._us(L, pitch, margin, 0.0):
        out.append(_st(urn_cs(u, v0 + 0.1, hh - 0.2, min(2.2, pitch / 3)), b, 0.4))
    for uc, wd in CO._between(L, pitch, margin, pair, 1.3):
        a, e = uc - wd / 2 + 0.2, uc + wd / 2 - 0.2
        n = max(3, int((e - a) / 0.9))
        for k in range(n + 1):
            t = k / n
            out.append(_st(circle((a + (e - a) * t, v1 - 0.5 - min(hh - 1.2, 1.6) * 4 * t * (1 - t)), 0.34, 10), b, 0.4))
    return out, []


def bracket_leafy(h, d, t):
    """A Colonial Revival modillion: a block rolled under at its nose, a leaf lying along its
    underside, its tip curling at the wall end (side profile, top at v = 0)."""
    hb = min(h, max(1.8, 0.45 * d))
    r = min(0.5 * hb, 0.28 * d)
    body = poly([(0.0, 0.0), (d, 0.0), (d, -hb * 0.45), (0.0, -hb * 0.7)])
    leaf = [(d - r * 1.2 - (d - r * 1.2 - 0.3) * s, -hb * 0.45 - 0.25 * hb * math.sin(math.pi * s) - 0.25 * hb * s)
            for s in np.linspace(0.0, 1.0, 12)]
    leaf_cs = poly([(d - r, -hb * 0.45)] + leaf + [(0.3, -hb * 0.7 + 0.2)])
    return cs_union([body, leaf_cs, circle((d - r, -hb * 0.45 - r * 0.6), r, 16), circle((0.4, -hb * 0.75), 0.4, 12)])


def foundation_capstone(reg, seed=0):
    """Rubble stone under a dressed cap course of long stones with chamfered faces (the
    Westbrook)."""
    from .trimwork import ashlar
    b = reg.bounds()
    rub = ashlar(reg ^ rect(b[0] - 1, b[1] - 1, b[2] + 1, b[3] - 1.8), course=(0.9, 1.6), length=(1.4, 3.4), d=0.4,
                 seed=seed + 5, rough=0.2)
    cap = []
    u = b[0] + (seed % 3) * 1.7
    while u < b[2]:
        u1 = min(u + 7.6, b[2])
        cap.append(chamfer_box(max(u, b[0]) + 0.05, b[3] - 1.8, u1 - 0.05, b[3], 0.0, 0.5, c=0.25, bottom=0.5))
        u = u1
    return rub + union(cap)


CO.FRIEZE_EXTRA.update(ribbon=frieze_ribbon, gougework=frieze_gougework, urns=frieze_urns)
TW.BRACKET_EXTRA.update(leafy=bracket_leafy)
TW.FOUNDATION_EXTRA.update(capstone=foundation_capstone)


# ------------------------------------------------------------------ Colonial clapboard with butt joints
def clapboard_butt(region, datum=0.0, pitch=1.5, seed=3):
    """Colonial clapboard: bevelled 1.5 mm courses of short boards, their butt joints (0.4
    wide) staggered from course to course, as hand-split clapboards were laid."""
    from .skins import _lap
    if region.is_empty():
        return M()
    lap = _lap(region, pitch, [(0.0, 0.42), (0.2, 0.40), (pitch, 0.08)], datum)
    u0, v0, u1, v1 = region.bounds()
    rng = np.random.default_rng(seed)
    slots = []
    k0 = math.floor((v0 - datum) / pitch) - 1
    k1 = math.ceil((v1 - datum) / pitch) + 1
    for k in range(k0, k1):
        vk = datum + k * pitch
        u = u0 - rng.uniform(0.0, 12.0)
        while u < u1:
            u += rng.uniform(9.0, 15.0)
            slots.append(rect(u - 0.2, vk + 0.05, u + 0.2, vk + pitch - 0.05))
    if not slots:
        return lap
    return lap - ext(cs_union(slots), 0.14, 1.0)


# ------------------------------------------------------------------ Westbrook windows and doors
def window_capped(w, h, cap="cornice", lites=(3, 3), rows=(2, 2), A=1.1):
    """Colonial Revival window: six-over-six sash in a flat casing with a back-band, a sill
    on a small bed moulding, and over it a head: "cornice" (a frieze board under a moulded cap
    with a row of dentils; the lower windows) or "cap" (a plain drip cap over a narrow board;
    the upper windows)."""
    op = O.opening_cs(w, h, 0)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    sash = O.window_insert(w, h, 0, lites=lites, rows=rows, bare=True)["insert"]
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS)]
    parts.append(ext((op.offset(A, JoinType.Miter, 4.0) - op) ^ rect(-w, 0.0, w, h + A), 0.0, O.CAS))
    parts.append(ext((op.offset(A, JoinType.Miter, 4.0) - op.offset(A - 0.45, JoinType.Miter, 4.0)) ^ rect(-w, 0.0, w, h + A),
                     O.CAS - 0.01, O.BEAD))
    half = w / 2 + A + 0.3
    if cap == "cornice":
        parts.append(ext(rect(-half, h + A - 0.1, half, h + A + 2.2), 0.0, 0.8))                 # frieze board
        parts.append(MD.run(-half - 0.2, half + 0.2, h + A + 2.2 + 0.6, MD.BED, 0.6, up=False))
        from .ornament import dentils
        parts.append(dentils(-half + 0.3, half - 0.3, h + A + 1.2, 0.8, 0.79, 0.5))
        parts.append(MD.run(-half - 0.6, half + 0.6, h + A + 2.8 + 1.0, MD.CROWN, 1.0, up=False))
        top = h + A + 3.8
    else:
        parts.append(ext(rect(-half, h + A - 0.1, half, h + A + 1.2), 0.0, 0.8))
        parts.append(MD.run(-half - 0.4, half + 0.4, h + A + 1.2 + 0.8, MD.CROWN, 0.8, up=False))
        top = h + A + 2.0
    sw = w / 2 + A + 0.5
    parts.append(MD.run(-sw, sw, 0.0, MD.SILL, 1.0, up=False))
    parts.append(ext(rect(-w / 2 - 0.3, -1.8, w / 2 + 0.3, -0.9), 0.0, 0.6))                       # bed under the sill
    return O._one_piece([sash], parts, op, plug_cs, O.PLUG, top, -1.8)


def door_fanlight(w, h, side=2.4, fan=4.4, A=1.4):
    """Colonial Revival entrance: a six-panel door between glazed sidelights, under an
    elliptical fanlight with radiating leads spanning door and sidelights, in a moulded
    elliptical architrave with a keystone; plain pilasters on plinths."""
    W = w + 2 * side
    spring = h - fan
    op = cs_union([rect(-W / 2, 0.0, W / 2, spring), oval((0.0, spring), W / 2, fan, 48) ^ rect(-W / 2, spring - 0.01, W / 2, h + 1)])
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    dh = spring - 0.4
    body = [ext(plug_cs, -pl, -1.0)]
    lp, _ = O._leaf("six_panel", -w / 2 + 0.2, w - 0.4, dh, True)
    body += lp
    glass = []
    for sg in (-1, 1):
        u0, u1 = sorted((sg * (w / 2 + 0.3), sg * (W / 2 - O.CLR - 0.5)))
        glass.append(rect(u0, dh * 0.3, u1, dh - 0.5))
        body.append(chamfer_box(u0, 1.0, u1, dh * 0.3 - 0.5, -1.0, 0.4, c=0.2))
    fan_cs = plug_cs.offset(-0.5, JoinType.Miter, 4.0) ^ rect(-W, spring + 0.3, W, h + 5)
    glass.append(fan_cs)
    g = cs_union(glass)
    body = [p - ext(g, -pl + O.GLASS, 0.5) for p in body]
    sash = body + [ext(g, -pl, -pl + O.GLASS), ext(plug_cs - plug_cs.offset(-0.5, JoinType.Miter, 4.0), -pl, 0.0),
                   ext(rect(-W, spring - 0.3, W, spring + 0.3) ^ plug_cs, -pl, -0.4)]
    bars = [rect(-w / 2 - 0.2, 0.3, -w / 2 + 0.3, spring), rect(w / 2 - 0.3, 0.3, w / 2 + 0.2, spring)]
    for a in np.linspace(math.pi / 8, 7 * math.pi / 8, 5):
        bars.append(stroke([(0.0, spring), (W * math.cos(a), spring + W * math.sin(a) * fan / (W / 2))], RIB))
    bars.append(oval((0.0, spring), 1.6, 1.0) ^ rect(-3, spring, 3, spring + 2))
    sash.append(ext(cs_union(bars) ^ plug_cs, -pl + O.GLASS - 0.01, -0.5))
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS)]
    for sg in (-1, 1):
        u0, u1 = sorted((sg * W / 2, sg * (W / 2 + A)))
        parts.append(ext(rect(u0, 1.8, u1, spring), 0.0, 0.9))
        parts.append(chamfer_box(u0 - 0.2, 0.0, u1 + 0.2, 1.8, 0.0, 1.2, c=0.3, bottom=0.0))
        parts.append(chamfer_box(u0 - 0.2, spring - 1.2, u1 + 0.2, spring, 0.0, 1.2, c=0.3))
    arch = (oval((0.0, spring), W / 2 + A, fan + A, 48) - oval((0.0, spring), W / 2, fan, 48)) ^ rect(-W, spring, W, h + 10)
    parts.append(ext(arch, 0.0, 0.9))
    parts.append(ext((oval((0.0, spring), W / 2 + A, fan + A, 48) - oval((0.0, spring), W / 2 + A - 0.5, fan + A - 0.5, 48))
                     ^ rect(-W, spring, W, h + 10), 0.89, 1.3))
    parts.append(chamfer_box(-0.8, h - 0.4, 0.8, h + A + 0.9, 0.0, 1.7, c=0.35))
    return O._one_piece(sash, parts, op, plug_cs, pl, h + A + 0.9, 0.0)


def door_french(w, h, transom=4.0, A=1.1):
    """A pair of glazed French doors (each of three lights over two, over a low panel) under
    a transom of three lights, in the capped casing of the Westbrook's windows."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    dh = h - transom
    lw = (w - 2 * O.CLR - 1.0 - SLOT) / 2
    u = -w / 2 + O.CLR + 0.5
    body, lights = [ext(plug_cs, -pl, -1.0)], []
    for i in range(2):
        lp, light = O._leaf("french", u, lw, dh, i == 0)
        body += lp
        if light is not None:
            lights.append(light)
        u += lw + SLOT
    tcs = rect(-w / 2 + O.CLR + 0.5, dh + 0.3, w / 2 - O.CLR - 0.5, h - O.CLR - 0.5)
    g = cs_union(lights) + tcs
    sash = [p - ext(g, -pl - 1, 0.0) for p in body]
    sash += [ext(g, -pl, -pl + O.GLASS), ext(plug_cs - plug_cs.offset(-0.5, JoinType.Miter, 4.0), -pl, 0.0),
             ext(rect(-w, dh - 0.3, w, dh + 0.3) ^ plug_cs, -pl, -0.4)]
    bars = [rect(x - RIB / 2, dh, x + RIB / 2, h) for x in (-w / 6, w / 6)]
    sash.append(ext(cs_union(bars) ^ tcs.offset(0.3, JoinType.Miter, 4.0), -pl + O.GLASS - 0.01, -0.4))
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS)]
    parts.append(ext((op.offset(A, JoinType.Miter, 4.0) - op) ^ rect(-w, 0.0, w, h + A), 0.0, O.CAS))
    parts.append(ext((op.offset(A, JoinType.Miter, 4.0) - op.offset(A - 0.45, JoinType.Miter, 4.0)) ^ rect(-w, 0.0, w, h + A),
                     O.CAS - 0.01, O.BEAD))
    half = w / 2 + A + 0.3
    parts.append(ext(rect(-half, h + A - 0.1, half, h + A + 1.2), 0.0, 0.8))
    parts.append(MD.run(-half - 0.4, half + 0.4, h + A + 1.2 + 0.8, MD.CROWN, 0.8, up=False))
    return O._one_piece(sash, parts, op, plug_cs, pl, h + A + 2.0, 0.0)


def shutter_rod(w, h, t=0.8, stile=0.6):
    """A louvered shutter with a tilt rod: two louver fields either side of a mid rail, a
    slim rod standing proud down the middle of each field (the Westbrook)."""
    web = 0.4
    mv = round(h * 0.5 / 0.2) * 0.2
    parts = [ext(rect(0, 0, w, h) - rect(stile, stile, w - stile, h - stile), 0.0, t),
             ext(rect(stile, mv - stile / 2, w - stile, mv + stile / 2), 0.0, t)]
    for f0, f1 in ((stile, mv - stile / 2), (mv + stile / 2, h - stile)):
        field = rect(stile, f0, w - stile, f1)
        parts.append(ext(field, 0.0, web))
        n = max(1, int((f1 - f0 - SLOT) / 1.0))
        pitch = (f1 - f0 - SLOT) / n
        slats = [rect(stile - 0.1, f0 + SLOT + k * pitch, w - stile + 0.1, f0 + SLOT + k * pitch + min(RIB + 0.05, pitch - SLOT))
                 for k in range(n)]
        parts.append(ext(cs_union(slats) ^ field.offset(0.05), web, t - 0.2))
        parts.append(ext(rect(w / 2 - 0.25, f0 + 0.6, w / 2 + 0.25, f1 - 0.6), web, t))           # the tilt rod
    return union(parts)


# ------------------------------------------------------------------ Westbrook dormer, chimney, column, baluster
def dormer_returns(w=16.0, dep=18.0, hwall=13.0, pitch=1.0):
    """A gabled dormer with cornice returns: a round-headed window with a fan and a keystone,
    a raking fascia and a level cornice that returns a little way across the gable foot.
    Local as dormer_pedimented. Returns (body, core, face)."""
    rise = w / 2 * pitch
    face = poly([(-w / 2, 0.0), (w / 2, 0.0), (w / 2, hwall), (0.0, hwall + rise), (-w / 2, hwall)])
    body = ext(face, -dep, 0.0) - ext(face.offset(-1.2, JoinType.Miter, 4.0) ^ rect(-50, 1.2, 50, 99), -dep - 1, -1.2)
    lw = w * 0.46
    spring = hwall - 1.0 - lw / 2
    light = cs_union([rect(-lw / 2, 2.0, lw / 2, spring), circle((0.0, spring), lw / 2, 32) ^ rect(-lw, spring, lw, spring + lw)])
    body = body - ext(light, -1.3, 1.0)
    fan = cs_union([stroke([(0.0, spring), (lw / 2 * math.cos(a), spring + lw / 2 * math.sin(a))], 0.45)
                    for a in np.linspace(math.pi / 6, 5 * math.pi / 6, 4)] + [circle((0.0, spring), 0.9, 16)]) ^ light
    bars = cs_union([rect(-lw / 2, spring - 0.25, lw / 2, spring + 0.25), rect(-0.25, 2.0, 0.25, spring),
                     rect(-lw / 2, (2.0 + spring) / 2 - 0.25, lw / 2, (2.0 + spring) / 2 + 0.25)]) ^ light
    body = body + ext(fan + bars, -1.2, -0.5)
    body = body + ext((light.offset(0.8, JoinType.Round) - light) ^ rect(-w, 1.6, w, hwall + rise), -0.01, 0.6)
    body = body + ext(rect(-0.6, spring + lw / 2 - 0.2, 0.6, spring + lw / 2 + 1.4), -0.01, 1.0)           # keystone
    body = body + chamfer_box(-lw / 2 - 1.0, 1.0, lw / 2 + 1.0, 2.0, -0.01, 0.9, c=0.3, bottom=0.9)
    rake = (face - face.offset(-0.9, JoinType.Miter, 4.0)) ^ rect(-50, hwall, 50, 99)
    body = body + ext(rake, -0.01, 0.8)
    for sg in (-1, 1):                                  # the cornice returns: 3 mm in from each corner, 0.4 past it
        a_, e_ = sorted((sg * (w / 2 + 0.4), sg * (w / 2 - 3.0)))
        body = body + ext(rect(a_, hwall - 0.9, e_, hwall + 0.1), -0.01, 0.9)
    core = ext(face.offset(-1.2, JoinType.Miter, 4.0) ^ rect(-50, 1.2, 50, hwall), -dep + 1.2, -1.2)
    return body, core, face


def chimney_bridged(w=22.0, d=8.0, h=30.0):
    """A bridged chimney: two brick flues rising from one base, joined at the top by a
    round brick arch under a shared corbelled cap (the Westbrook). Stands on z = 0."""
    h = round(h / 0.2) * 0.2
    fw = w * 0.32
    zs = round((h - 17.0) / 0.2) * 0.2                  # where the flues part
    body = box([-w / 2, -d / 2, 0.0], [w / 2, d / 2, zs]) + TW._skin(w, d, 0.0, zs, TW._brick("running"))
    zc = round((h - 2.4) / 0.2) * 0.2
    for sg in (-1, 1):
        x0, x1 = sorted((sg * w / 2, sg * (w / 2 - fw)))
        body = body + box([x0, -d / 2, zs - 0.01], [x1, d / 2, zc])
        body = body + TW._skin(fw, d, 0.0, zc - zs, TW._brick("running")).translate([(x0 + x1) / 2, 0, zs])
    gap = w - 2 * fw
    r = gap / 2
    za = zc - 3.0
    arch = box([-gap / 2 - 0.01, -d / 2, za - r], [gap / 2 + 0.01, d / 2, zc]) - \
        M.cylinder(d + 2, r, r, 32).rotate([90, 0, 0]).translate([0, d / 2 + 1, za - r])
    body = body + arch.trim_by_plane([0, 0, 1.0], zs + 1.0)
    body = body + TW._corbel_out(w, d, zc + 0.6, 0.6) + box([-w / 2 - 0.6, -d / 2 - 0.6, zc + 0.59], [w / 2 + 0.6, d / 2 + 0.6, zc + 1.4])
    body = body + box([-w / 2 - 0.9, -d / 2 - 0.9, zc + 1.39], [w / 2 + 0.9, d / 2 + 0.9, h])
    for sg in (-1, 1):                                  # a clay pot over each flue
        body = body + TW._pot(1.3, 3.4, "tall").translate([sg * (w / 2 - fw / 2), 0, h - 0.01])
    return body


def column_ionic(h, r=1.6):
    """A slender Ionic column, printed upright: a plinth, an Attic base, a straight shaft, an
    egg band and a capital whose volutes stand as two rolled pads front and back under a
    square abacus."""
    from .porchwork import _revolve
    z1 = h - 2.6
    prof = [(0.0, 0.0), (r + 0.6, 0.0), (r + 0.6, 0.8), (r + 0.4, 1.0), (r + 0.4, 1.3), (r + 0.1, 1.5), (r + 0.25, 1.7),
            (r, 1.9), (r, z1), (r + 0.2, z1 + 0.2), (r + 0.2, z1 + 0.6), (r, z1 + 0.8)]
    body = _revolve(prof, 36)
    ab = r + 0.7
    cap = box([-ab, -ab, h - 0.8], [ab, ab, h]) + M.hull_points(
        [(r * math.cos(a), r * math.sin(a), z1 + 0.79) for a in np.linspace(0, 2 * math.pi, 24, endpoint=False)] +
        [(x, y, h - 0.8) for x in (-ab, ab) for y in (-ab * 0.8, ab * 0.8)])
    vol = union([M.cylinder(2 * ab * 0.92, 0.75, 0.75, 20).rotate([0, 90, 0]).translate([-ab * 0.92, sg * (ab * 0.8 - 0.3), h - 1.3])
                 for sg in (-1, 1)])
    return body + cap + (vol ^ box([-ab, -ab, z1 + 0.8], [ab, ab, h]))


def baluster_colonial(h, seg=20):
    """A Colonial Revival baluster (printed upright): a square-ish foot, a vase low down, a
    long slim neck and a ring under the rail."""
    from .porchwork import _revolve
    prof = [(0.0, 0.0), (0.6, 0.0), (0.6, 0.5), (0.45, 0.7), (0.62, 1.2), (0.66, 1.6), (0.52, 2.2), (0.32, 2.7),
            (0.32, h - 1.0), (0.45, h - 0.8), (0.45, h - 0.5), (0.36, h - 0.3), (0.36, h)]
    return _revolve(prof, seg)


# ------------------------------------------------------------------ the bowed portico
def bowed_portico(c, R, a0, a1, H_floor, z_col_top, ent_h=5.0, n_cols=6, col_r=1.6, rail_h=7.0, depth_in=4.0, col_trim=0.12,
                  wall_y=None):
    """A bowed (segmental) portico round the centre ``c`` of radius ``R`` between plan angles
    a0..a1 (radians; the wall chord at the ends): ``n_cols`` Ionic columns on the arc, a
    curved entablature with a frieze of roundels and a dentilled cornice under a flat deck,
    and a curved balustrade of turned balusters on the deck's edge. Returns dict of world
    solids: cols [solid], ent (prints upside down), rail (prints upright)."""
    angs = np.linspace(a0 + col_trim, a1 - col_trim, n_cols)   # the end columns clear of the wall's cornices
    Rc = R - 2.6                                              # the columns' circle
    cols = []
    zc0 = H_floor
    hcol = z_col_top - zc0
    colm = column_ionic(hcol, col_r)
    for a in angs:
        cols.append(colm.translate([c[0] + Rc * math.cos(a), c[1] + Rc * math.sin(a), zc0]))

    def sector(r0, r1, z0, z1, seg=64):
        pts = [(c[0] + r1 * math.cos(a), c[1] + r1 * math.sin(a)) for a in np.linspace(a0, a1, seg)] + \
              [(c[0] + r0 * math.cos(a), c[1] + r0 * math.sin(a)) for a in np.linspace(a1, a0, seg)]
        return M.extrude(poly(pts), z1 - z0).translate([0, 0, z0])

    zt = z_col_top
    r_in = Rc - col_r - 0.8 - depth_in
    ent = sector(r_in, Rc + col_r + 0.3, zt, zt + 1.6) + sector(r_in, Rc + col_r + 0.6, zt + 1.6, zt + 3.4)
    for k in range(3):                                         # a 45 degree stepped cornice
        ent = ent + sector(r_in, Rc + col_r + 0.6 + 0.4 * (k + 1), zt + 3.4 + 0.4 * k, zt + 3.8 + 0.4 * k)
    ent = ent + sector(r_in, Rc + col_r + 2.0, zt + ent_h - 0.4, zt + ent_h)
    # roundels on the frieze, dentils under the cornice
    rf = Rc + col_r + 0.6
    orn = []
    for a in np.linspace(a0, a1, n_cols * 2 - 1):
        p = (c[0] + rf * math.cos(a), c[1] + rf * math.sin(a))
        orn.append(M.cylinder(0.4, 0.55, 0.55, 16).rotate([0, 90, 0]).rotate([0, 0, math.degrees(a)])
                   .translate([p[0], p[1], zt + 2.5]))
    n_d = int((a1 - a0) * rf / 1.4)
    for a in np.linspace(a0, a1, n_d):
        p = (c[0] + (rf + 0.3) * math.cos(a), c[1] + (rf + 0.3) * math.sin(a))
        orn.append(box([-0.3, -0.35, zt + 3.0], [0.3, 0.35, zt + 3.6]).rotate([0, 0, math.degrees(a)]).translate([p[0], p[1], 0]))
    ent = ent + union(orn)
    # the balustrade on the deck's edge: base and top rails on the arc, turned balusters, posts over the columns
    ztop = zt + ent_h
    rr = Rc + col_r + 0.4
    b0, b1 = (angs[0], angs[-1]) if wall_y is not None else (a0, a1)     # the curved run: post to post
    a0s, a1s = a0, a1
    a0, a1 = b0, b1
    rail = sector(rr - 1.2, rr + 0.2, ztop, ztop + 1.0) + sector(rr - 1.4, rr + 0.4, ztop + rail_h - 1.0, ztop + rail_h)
    a0, a1 = a0s, a1s
    bal = baluster_colonial(rail_h - 2.0 + 0.02)
    n_b = int((b1 - b0) * (rr - 0.5) / 1.5)
    bs = []
    post_a = list(angs)
    if wall_y is not None:                     # straight returns from the end posts back to the wall
        for a in (b0, b1):
            p = np.array([c[0] + (rr - 0.5) * math.cos(a), c[1] + (rr - 0.5) * math.sin(a)])
            Lr = wall_y - 0.02 - p[1]
            bs.append(box([p[0] - 0.7, p[1], ztop], [p[0] + 0.7, wall_y - 0.02, ztop + 1.0]) +
                      box([p[0] - 0.9, p[1], ztop + rail_h - 1.0], [p[0] + 0.9, wall_y - 0.02, ztop + rail_h]))
            nr = int(Lr / 1.5)
            for k in range(1, nr):
                bs.append(bal.translate([p[0], p[1] + Lr * k / nr, ztop + 0.99]))
    for a in np.linspace(b0, b1, n_b):
        if min(abs(a - pa) for pa in post_a) * (rr - 0.5) < 1.5:
            continue
        bs.append(bal.translate([c[0] + (rr - 0.5) * math.cos(a), c[1] + (rr - 0.5) * math.sin(a), ztop + 0.99]))
    for a in post_a:
        p = (c[0] + (rr - 0.5) * math.cos(a), c[1] + (rr - 0.5) * math.sin(a))
        bs.append(box([-1.1, -1.1, ztop], [1.1, 1.1, ztop + rail_h + 0.4]).rotate([0, 0, math.degrees(a)]).translate([p[0], p[1], 0]))
    rail = rail + union(bs)
    return dict(cols=cols, ent=ent, rail=rail, angs=angs, Rc=Rc)


# ================================================================== the Pennock (house 32)
# ------------------------------------------------------------------ fieldstone, quoins, rubble arches
def _knocked(a, lo, e, hi, cut):
    """A stone's face: the rectangle (a, lo)-(e, hi) with its four corners knocked off by
    cut[0..3] (bottom-left, bottom-right, top-right, top-left)."""
    c0, c1, c2, c3 = cut
    pts = [(a + c0, lo), (e - c1, lo), (e, lo + c1), (e, hi - c2), (e - c2, hi), (a + c3, hi), (a, hi - c3), (a, lo + c0)]
    out = []
    for p in pts:
        if not out or abs(p[0] - out[-1][0]) + abs(p[1] - out[-1][1]) > 1e-6:
            out.append(p)
    if abs(out[0][0] - out[-1][0]) + abs(out[0][1] - out[-1][1]) < 1e-6:
        out.pop()
    return poly(out)


def fieldstone(region, datum=0.0, seed=0, joint=0.5, bed=0.4, d=(0.3, 0.42)):
    """Pennsylvania fieldstone: roughly coursed rubble. Courses of random height (1.6 to 3.2
    mm) of stones of random length, each stone's corners knocked off at random and its top or
    bottom stepped a layer out of line, so the courses wander as laid rubble does; 0.5 mm
    joints, the stones standing 0.3 or 0.42 proud with every layer pulled back underneath."""
    from .shell import _stepped
    if region.is_empty():
        return M()
    rng = np.random.default_rng(seed)
    u0, v0, u1, v1 = region.bounds()
    by_d = {d[0]: [], d[1]: []}
    v = datum + math.floor((v0 - datum) / 0.2) * 0.2 - 3.2
    while v < v1 + 0.1:
        hc = float(rng.choice([1.6, 2.0, 2.4, 2.8, 3.2], p=[0.14, 0.26, 0.26, 0.2, 0.14]))
        u = u0 - rng.uniform(0.0, 5.0)
        while u < u1 + 0.5:
            L = rng.uniform(2.2, 6.2) if hc < 2.5 else rng.uniform(3.0, 7.6)
            a, e = u + joint / 2, u + L - joint / 2
            lo = v + bed / 2 + 0.2 * int(rng.integers(0, 2))
            hi = v + hc - bed / 2 - 0.2 * int(rng.integers(0, 2))
            if hi - lo >= 0.8 and e - a >= 1.2:
                lim = min(e - a, hi - lo) / 2 - 0.15
                cut = [min(lim, float(rng.choice([0.0, 0.25, 0.45, 0.6]))) for _ in range(4)]
                by_d[d[0] if rng.random() < 0.35 else d[1]].append(_knocked(a, lo, e, hi, cut))
            u += L
        v += hc
    out = []
    for dd, stones in by_d.items():
        if stones:
            cs = cs_union(stones) ^ region
            if not cs.is_empty():
                out.append(_stepped(cs, 0.0, dd))
    return union(out) if out else M()


def quoins_drafted(L, v_top, ends=(True, True), datum=0.0, long=7.4, short=4.4, course=3.6, joint=0.4, d=0.6):
    """Dressed quoins with a drafted margin (a sunk line chiselled round each face) at the
    ends of a wall face of length L, long and short in turn, and the other way round at the
    face's far end so the two faces of a corner interlock. Returns (relief, zone)."""
    from .shell import _stepped
    blocks, grooves = [], []
    k = 0
    v = datum
    while v + course <= v_top + 0.01:
        lo, hi = v + joint / 2, v + course - joint / 2
        for end, (on, first_long) in enumerate(zip(ends, (k % 2 == 0, k % 2 == 1))):
            if not on:
                continue
            ln = long if first_long else short
            a, e = (0.0, ln) if end == 0 else (L - ln, L)
            r = rect(a, lo, e, hi)
            blocks.append(r)
            grooves.append(r.offset(-0.5, JoinType.Miter, 4.0) - r.offset(-0.9, JoinType.Miter, 4.0))
        v += course
        k += 1
    if not blocks:
        return M(), rect(0, 0, 0, 0)
    cs = cs_union(blocks)
    relief = _stepped(cs, 0.0, d) - ext(cs_union(grooves), d - 0.2, d + 0.2)
    return relief, cs.offset(joint / 2, JoinType.Miter, 4.0)


def rubble_arch(u, v_base, span, rise=1.8, foot=1.6, seed=0, joint=0.45, d=0.5):
    """A flat-bottomed segmental arch of thin stones set on edge over an opening: its soffit
    runs level on the frame's head, its back rises in a segment (``foot`` tall at the ends,
    ``foot + rise`` at the crown), the stones radiate from a point below and their tails are
    left ragged. Returns (relief, zone) in the facade's (u, v) frame."""
    from .shell import _stepped
    rng = np.random.default_rng(seed)
    n = max(5, int(round(span / 1.25)) | 1)
    Rf = span * 0.9
    half = span / 2

    def back(x):                               # the extrados, a parabolic segment
        t = (x - u) / half
        return v_base + foot + rise * (1 - t * t)
    stones = []
    for i in range(n):
        xa = u - half + span * i / n + joint / 2
        xb = u - half + span * (i + 1) / n - joint / 2
        xm = (xa + xb) / 2
        top = back(xm) - v_base + (0.5 if i == n // 2 else rng.uniform(-0.15, 0.35))
        pa = (xa + (xa - u) * top / Rf, v_base + top)
        pb = (xb + (xb - u) * top / Rf, v_base + top)
        stones.append(poly([(xa, v_base), (xb, v_base), pb, pa]))
    cs = cs_union(stones)
    zone = cs_union([cs.offset(0.3, JoinType.Miter, 4.0), rect(u - half - 0.3, v_base - 0.3, u + half + 0.3, v_base + foot)])
    return _stepped(cs, 0.0, d), zone


# ------------------------------------------------------------------ friezes and a course
def frieze_compass(L, h, b, pitch, margin, pair, half):
    """Pennsylvania compass stars: in every bay a ring with a six-petalled rosette inside (the
    petals laid out with a compass, as on a barn star), a lozenge at every station."""
    v0, v1 = 0.8, h - 0.8
    vm = (v0 + v1) / 2
    hh = v1 - v0
    out = []
    for uc, wd in CO._between(L, pitch, margin, pair, 0.8):
        r = min(hh / 2 - 0.05, wd / 2 - 0.4)
        if r < 1.0:
            continue
        out.append(_st(circle((uc, vm), r, 36) - circle((uc, vm), r - 0.45, 36), b, 0.4))
        ri = r - 0.45
        for k in range(6):
            a = math.pi / 2 + k * math.pi / 3
            c = (uc + math.cos(a) * ri / 2, vm + math.sin(a) * ri / 2)
            out.append(_st(_lens(c, ri * 0.96, min(0.62, ri * 0.55), a), b, 0.45))
    for u in CO._us(L, pitch, margin, 0.0):
        out.append(_st(poly([(u, v0 + 0.1), (u + 0.55, vm), (u, v1 - 0.1), (u - 0.55, vm)]), b, 0.4))
    return out, []


def frieze_gadroons(L, h, b, pitch, margin, pair, half):
    """Gadrooning: a run of slanting convex lobes along the band, each a pill in two steps
    (so it reads round), broken at every station by a square boss."""
    v0, v1 = 0.7, h - 0.7
    out = []
    stations = CO._us(L, pitch, margin, 0.0)
    for u in np.arange(margin * 0.5, L - margin * 0.5, 1.4):
        if any(abs(u - s) < 1.3 for s in stations):
            continue
        a, e = (u - 0.45, v0 + 0.4), (u + 0.45, v1 - 0.4)
        out.append(_st(stroke([a, e], 0.9), b, 0.25))
        out.append(_st(stroke([a, e], 0.5), b + 0.25, 0.25))
    for s in stations:
        out.append(_st(rect(s - 0.8, v0 + 0.2, s + 0.8, v1 - 0.2), b, 0.3))
        out.append(_st(circle((s, (v0 + v1) / 2), 0.4, 12), b + 0.3, 0.3))
    return out, []


def frieze_whirls(L, h, b, pitch, margin, pair, half):
    """Whirling rosettes (the hex-sign whirl): in every bay four curved blades swept round a
    boss, and a little bead either side of every station."""
    v0, v1 = 0.8, h - 0.8
    vm = (v0 + v1) / 2
    hh = v1 - v0
    out = []
    for uc, wd in CO._between(L, pitch, margin, pair, 0.6):
        r = min(hh / 2, wd / 2 - 0.3)
        if r < 1.0:
            continue
        for k in range(4):
            a0 = k * math.pi / 2
            pts = [(uc + (0.45 + (r - 0.45) * t) * math.cos(a0 + 1.3 * t), vm + (0.45 + (r - 0.45) * t) * math.sin(a0 + 1.3 * t))
                   for t in np.linspace(0.0, 1.0, 8)]
            out.append(_st(stroke(pts, 0.5), b, 0.4))
        out.append(_st(circle((uc, vm), 0.55, 14), b, 0.55))
    for u in CO._us(L, pitch, margin, 0.0):
        for dv in (-0.7, 0.7):
            out.append(_st(circle((u, vm + dv), 0.35, 10), b, 0.35))
    return out, []


def course_wedges(L, h, b, pitch, margin, p):
    """Wolf's teeth: wedges standing on the course's foot and hanging from its head in turn,
    each pair parted by a slot a nozzle wide."""
    wd, g = p.get("tooth", 1.8), p.get("gap", 0.6)
    step = wd / 2 + g
    n = int((L - wd - 0.6) / step)
    u0 = (L - (n * step + wd)) / 2
    out = []
    for k in range(n + 1):
        u = u0 + k * step
        if k % 2 == 0:
            cs = poly([(u, 0.0), (u + wd, 0.0), (u + wd / 2, h)])
        else:
            cs = poly([(u, h), (u + wd, h), (u + wd / 2, 0.0)])
        out.append(ext(cs, b - 0.05, b + p.get("d", 0.6)))
    return out


# ------------------------------------------------------------------ foundation
def foundation_ledgestone(reg, seed=0):
    """Dry-laid ledgestone: thin courses (0.8 and 1.2 mm) of long flat stones with a bond
    stone standing a course taller every so often, deeper than the rest."""
    from .shell import _stepped
    rng = np.random.default_rng(seed + 11)
    b = reg.bounds()
    thin, deep = [], []
    v = b[1]
    while v < b[3]:
        hc = float(rng.choice([0.8, 1.2]))
        u = b[0] - rng.uniform(0.0, 6.0)
        while u < b[2]:
            L = rng.uniform(4.0, 11.0)
            lo, hi = v + 0.2, v + hc - 0.2
            if rng.random() < 0.12 and v + hc + 1.2 <= b[3]:
                deep.append(rect(u + 0.25, lo, u + min(L, 5.0) - 0.25, hi + 1.2))
                u += min(L, 5.0)
                continue
            if hi - lo >= 0.4:
                thin.append(rect(u + 0.25, lo, u + L - 0.25, hi))
            u += L
        v += hc
    thin_cs = cs_union(thin) - cs_union(deep).offset(0.25, JoinType.Miter, 4.0) if deep else cs_union(thin)
    out = [_stepped(thin_cs ^ reg, 0.0, 0.3)]
    if deep:
        out.append(_stepped(cs_union(deep) ^ reg, 0.0, 0.5))
    return union(out)


CO.FRIEZE_EXTRA.update(compass=frieze_compass, gadroons=frieze_gadroons, whirls=frieze_whirls)
CO.COURSE_EXTRA.update(wedges=course_wedges)
TW.FOUNDATION_EXTRA.update(ledgestone=foundation_ledgestone)


# ------------------------------------------------------------------ windows and the door
def window_pennsylvania(w, h, lites=(3, 3), rows=(3, 2), A=1.4, head="drip"):
    """A Pennsylvania window: a wide plank frame with a quirked bead round the sash and a
    lugged sill (its ends run past the frame). ``head`` "drip": a drip cap over the head (the
    lower storey, nine-over-six); "ears": the frame's head corners stepped out as crossettes
    (the upper storey, six-over-six)."""
    op = O.opening_cs(w, h, 0)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    sash = O.window_insert(w, h, 0, lites=lites, rows=rows, bare=True)["insert"]
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS)]
    frame = (op.offset(A, JoinType.Miter, 4.0) - op) ^ rect(-w, 0.0, w, h + A)
    parts.append(ext(frame, 0.0, 1.0))
    quirk = (op.offset(0.75, JoinType.Miter, 4.0) - op.offset(0.4, JoinType.Miter, 4.0)) ^ rect(-w, 0.3, w, h + 0.75)
    parts[-1] = parts[-1] - ext(quirk, 0.8, 1.2)
    top = h + A
    if head == "drip":
        parts.append(chamfer_box(-w / 2 - A - 0.6, h + A - 0.01, w / 2 + A + 0.6, h + A + 0.8, 0.0, 1.6, c=0.4))
        parts.append(ext(rect(-w / 2 - A - 0.3, h + A - 0.5, w / 2 + A + 0.3, h + A), 0.0, 1.3))
        top = h + A + 0.8
    else:
        for sg in (-1, 1):
            u0, u1 = sorted((sg * (w / 2 + A - 0.01), sg * (w / 2 + A + 0.8)))
            parts.append(ext(rect(u0, h - 1.4, u1, h + A), 0.0, 1.0))
        parts.append(ext(rect(-w / 2 - A - 0.8, h + A - 0.01, w / 2 + A + 0.8, h + A + 0.6), 0.0, 1.2))
        top = h + A + 0.6
    parts.append(chamfer_box(-w / 2 - A - 1.2, -1.6, w / 2 + A + 1.2, 0.01, 0.0, 1.8, c=0.45, bottom=0.6))
    return O._one_piece([sash], parts, op, plug_cs, O.PLUG, top, -1.6)


def window_attic(w, h, A=1.0):
    """A small four-light attic window in the gable: a plain frame and a thin sill."""
    op = O.opening_cs(w, h, 0)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    sash = O.window_insert(w, h, 0, lites=(2, 2), rows=(1, 1), bare=True)["insert"]
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS),
             ext((op.offset(A, JoinType.Miter, 4.0) - op) ^ rect(-w, 0.0, w, h + A), 0.0, 0.9),
             chamfer_box(-w / 2 - A - 0.5, -1.0, w / 2 + A + 0.5, 0.01, 0.0, 1.3, c=0.35, bottom=0.5)]
    return O._one_piece([sash], parts, op, plug_cs, O.PLUG, h + A, -1.0)


def _strap(u0, u1, v, flip=False):
    """An iron strap hinge's outline: a strap from the hinge edge u0 tapering to a spear
    point with a round eye short of it."""
    s = 1.0 if u1 > u0 else -1.0
    tip = u1
    body = poly([(u0, v - 0.3), (tip - s * 1.0, v - 0.22), (tip - s * 1.0, v + 0.22), (u0, v + 0.3)])
    spear = poly([(tip - s * 1.2, v - 0.45), (tip, v), (tip - s * 1.2, v + 0.45)])
    return cs_union([body, spear, circle((u0 + s * 0.6, v), 0.45, 12)])


def door_hooded(w, h, transom=4.2, A=1.3, hood=True):
    """A Pennsylvania entrance: a pair of leaves, each with two raised panels and a pair of
    iron strap hinges, under a four-light transom, in a beaded plank frame; over it a hood
    on two scrolled consoles: a moulded shelf and a pediment with a compass star in its
    tympanum. All one piece, printed face-up; the hood stands 4.6 proud. ``hood=False``: the
    door and frame alone (the back doors)."""
    op = rect(-w / 2, 0, w / 2, h)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    dh = h - transom
    body = [ext(plug_cs, -pl, -1.0)]
    lw = (w - 2 * O.CLR - SLOT) / 2
    for i, ua in enumerate((-w / 2 + O.CLR, SLOT / 2)):
        ub = ua + lw
        body.append(ext(rect(ua, 0.4, ub, dh - 0.3), -1.01, -0.8))
        mid = round((dh * 0.42) / 0.2) * 0.2
        for pv0, pv1 in ((1.4, mid - 0.5), (mid + 0.5, dh - 1.3)):
            body.append(chamfer_box(ua + 0.8, pv0, ub - 0.8, pv1, -0.81, 0.4, c=0.25))
        hinge_u, free_u = (ua + 0.2, ub - 1.6) if i == 0 else (ub - 0.2, ua + 1.6)
        for v in (2.4, dh - 2.6):
            body.append(ext(_strap(hinge_u, free_u, v), -0.81, -0.3))
    tcs = rect(-w / 2 + O.CLR + 0.5, dh + 0.3, w / 2 - O.CLR - 0.5, h - O.CLR - 0.5)
    body = [p - ext(tcs, -pl + O.GLASS, 0.5) for p in body]
    sash = body + [ext(tcs, -pl, -pl + O.GLASS), ext(plug_cs - plug_cs.offset(-0.5, JoinType.Miter, 4.0), -pl, 0.0)]
    bars = [rect(-w, dh - 0.3, w, dh + 0.3)] + [rect(x - 0.3, dh, x + 0.3, h) for x in (-w / 4, 0.0, w / 4)]
    sash.append(ext(cs_union(bars) ^ plug_cs, -pl + O.GLASS - 0.01, -0.4))
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS)]
    frame = (op.offset(A, JoinType.Miter, 4.0) - op) ^ rect(-w, 0.0, w, h + A)
    parts.append(ext(frame, 0.0, 1.0) - ext((op.offset(0.75, JoinType.Miter, 4.0) - op.offset(0.4, JoinType.Miter, 4.0))
                                             ^ rect(-w, 0.3, w, h + 0.75), 0.8, 1.2))
    if not hood:
        parts.append(chamfer_box(-w / 2 - A - 0.4, h + A - 0.01, w / 2 + A + 0.4, h + A + 0.8, 0.0, 1.4, c=0.35))
        return O._one_piece(sash, parts, op, plug_cs, pl, h + A + 0.8, 0.0)
    # the hood: consoles either side, a shelf, a pediment
    uc = w / 2 + A + 0.79
    vb, vt = h - 7.0, h + A
    for sg in (-1, 1):
        u0, u1 = sg * uc - 0.8, sg * uc + 0.8
        v = vb
        while v < vt - 0.01:
            t = (v - vb) / (vt - vb)
            parts.append(ext(rect(u0, v, u1, min(vt, v + 0.4) + 0.01), 0.0, 1.2 + 3.0 * t ** 1.6))
            v += 0.4
        parts.append(ext(circle((sg * uc, vb + 0.9), 0.9, 20), 0.0, 1.9))
        parts.append(ext(circle((sg * uc, vb + 0.9), 0.35, 12), 1.89, 2.2))
    S = uc + 1.5
    parts.append(ext(rect(-S + 0.4, vt - 0.01, S - 0.4, vt + 0.6), 0.0, 4.2))
    parts.append(ext(rect(-S, vt + 0.6, S, vt + 1.8), 0.0, 4.6))
    rise = round(S * 0.48 / 0.2) * 0.2
    base = vt + 1.8
    tri = poly([(-S - 0.3, base - 0.01), (S + 0.3, base - 0.01), (0.0, base + rise)])
    inner = poly([(-S + 1.7, base + 0.4), (S - 1.7, base + 0.4), (0.0, base + rise - 1.0)])
    parts.append(ext(tri - inner, 0.0, 4.6))
    parts.append(ext(inner.offset(0.05, JoinType.Miter, 4.0), 0.0, 3.6))
    rc = min(rise - 1.9, S - 3.0) * 0.56
    cc = (0.0, base + 0.4 + rc + 0.25)
    if rc > 0.7:
        parts.append(ext(circle(cc, rc, 28) - circle(cc, rc - 0.4, 28), 3.59, 4.0))
        for k in range(6):
            a = math.pi / 2 + k * math.pi / 3
            parts.append(ext(_lens((cc[0] + math.cos(a) * (rc - 0.4) / 2, cc[1] + math.sin(a) * (rc - 0.4) / 2),
                                   (rc - 0.4) * 0.96, 0.5, a), 3.59, 4.0))
    return O._one_piece(sash, parts, op, plug_cs, pl, base + rise + 0.1, 0.0)


# ------------------------------------------------------------------ shutters, bench
def shutter_strap(w, h, t=0.8, stile=0.6, hinge_left=True):
    """A Pennsylvania shutter: two raised panels in a frame, and a pair of iron strap hinges
    on its face from the hinge side (local frame as features.shutter, prints face-up)."""
    mid = round(h * 0.5 / 0.2) * 0.2
    parts = [ext(rect(0, 0, w, h), 0.0, 0.45),
             ext(rect(0, 0, w, h) - rect(stile, stile, w - stile, h - stile), 0.0, t),
             ext(rect(stile, mid - stile / 2, w - stile, mid + stile / 2), 0.0, t)]
    for p0, p1 in ((stile, mid - stile / 2), (mid + stile / 2, h - stile)):
        parts.append(chamfer_box(stile + 0.3, p0 + 0.3, w - stile - 0.3, p1 - 0.3, 0.44, t - 0.44, c=0.2))
    a, e = (0.1, w * 0.78) if hinge_left else (w - 0.1, w * 0.22)
    for v in (h * 0.14, h * 0.86):
        parts.append(ext(_strap(a, e, v), t - 0.01, t + 0.25))
    return union(parts)


def settle_bench(L=9.0, depth=4.2, seat=5.2, back=9.6, t=0.8):
    """A stoop bench (a settle): two shaped end boards, a seat, a back board and an apron.
    Local: u along it (0..L), y out from the wall (0 at the back), z up; prints upright."""
    ends = []
    for x in (0.0, L - t):
        prof = poly([(0.0, 0.0), (depth, 0.0), (depth, seat - 1.2), (depth - 0.8, seat), (1.0, seat),
                     (t + 0.2, back - 1.0), (t + 0.2, back), (0.0, back)])
        ends.append(M.extrude(prof, t).transform(np.array([[0, 0, 1.0, x], [1.0, 0, 0, 0], [0, 1.0, 0, 0]])))
    seat_b = box([t - 0.01, 0.6, seat - 0.8], [L - t + 0.01, depth - 0.2, seat])
    back_b = box([t - 0.01, 0.0, seat - 0.01], [L - t + 0.01, t, back - 0.4])
    apron = box([t - 0.01, depth - 0.9, seat - 2.2], [L - t + 0.01, depth - 0.2, seat - 0.79])
    return union(ends + [seat_b, back_b, apron])


# ------------------------------------------------------------------ chimney
def chimney_stonehood(w=8.0, d=15.0, h=30.0, seed=5):
    """A fieldstone stack with a two-slab drip course and a stone hood: two gabled end
    stones carrying a pitched stone roof over the flue, open at the sides (the smoke leaves
    under the hood). The long side runs along y. Stands on z = 0."""
    h = round(h / 0.2) * 0.2
    sh = round((h - 6.4) / 0.2) * 0.2
    body = box([-w / 2, -d / 2, 0], [w / 2, d / 2, sh])
    body = body + TW._skin(w, d, 0.0, sh - 0.4, lambda reg, i: fieldstone(reg, datum=0.0, seed=seed + i, d=(0.26, 0.36)))
    z = sh
    for g in (0.5, 0.9):
        body = body + TW._corbel_out(w, d, z + g, g) + box([-w / 2 - g, -d / 2 - g, z + g - 0.01], [w / 2 + g, d / 2 + g, z + g + 0.6])
        z += g + 0.6
    body = body + box([-w / 2 + 0.4, -d / 2 + 0.4, z - 0.01], [w / 2 - 0.4, d / 2 - 0.4, z + 0.8])
    z += 0.8
    body = body - box([-w / 2 + 1.6, -d / 2 + 2.6, z - 2.0], [w / 2 - 1.6, d / 2 - 2.6, z + 10])
    hw = w / 2 + 0.6
    ze = z + 2.6
    rise = hw
    for sg in (-1, 1):
        y0, y1 = sorted((sg * (d / 2 - 0.4), sg * (d / 2 - 1.8)))
        e_ = w / 2 - 0.4
        end = poly([(-e_, z - 0.01), (e_, z - 0.01), (e_, ze - 0.35 + (hw - e_)), (0.0, ze + rise - 0.35), (-e_, ze - 0.35 + (hw - e_))])
        body = body + M.extrude(end, y1 - y0).transform(np.array([[1.0, 0, 0, 0], [0, 0, 1.0, y0], [0, 1.0, 0, 0]]))
    roof = poly([(-hw, ze - 0.4), (0.0, ze + rise - 0.4), (hw, ze - 0.4), (hw, ze + 0.5), (0.0, ze + rise + 0.5), (-hw, ze + 0.5)])
    body = body + M.extrude(roof, d + 0.4).transform(np.array([[1.0, 0, 0, 0], [0, 0, 1.0, -d / 2 - 0.2], [0, 1.0, 0, 0]]))
    return body


# ------------------------------------------------------------------ the arched dormer
def dormer_arched(w=15.0, dep=18.0, hwall=11.0, rise=3.6):
    """A dormer with a segmental (arched) roof: a flat front with pilaster strips, a six-light
    window whose head follows the arch, a keystone at the crown. Local as dormer_pedimented.
    Returns (body, core, face, arc(t) points for the roof)."""
    R = (w * w / 4 + rise * rise) / (2 * rise)
    cy = hwall + rise - R

    def arc(r, n=40):
        a0 = math.asin((w / 2) / R)
        return [(r * math.sin(a), cy + r * math.cos(a)) for a in np.linspace(-a0, a0, n)]
    face = poly([(-w / 2, 0.0), (w / 2, 0.0)] + list(reversed(arc(R))))
    body = ext(face, -dep, 0.0) - ext(face.offset(-1.2, JoinType.Miter, 4.0) ^ rect(-50, 1.2, 50, 99), -dep - 1, -1.2)
    lw = w * 0.46
    light = face.translate((0.0, -2.4)) ^ rect(-lw / 2, 2.2, lw / 2, 99)
    body = body - ext(light, -1.3, 1.0)
    lb = light.bounds()
    bars = cs_union([rect(-lw / 2, 2.2 + (lb[3] - 2.2) * k / 3 - 0.22, lw / 2, 2.2 + (lb[3] - 2.2) * k / 3 + 0.22) for k in (1, 2)] +
                    [rect(-0.25, 2.2, 0.25, lb[3])]) ^ light
    body = body + ext(bars, -1.2, -0.5)
    body = body + ext((light.offset(0.8, JoinType.Miter, 4.0) - light) ^ rect(-w, 1.6, w, 99), -0.01, 0.6)
    body = body + chamfer_box(-lw / 2 - 1.0, 1.2, lw / 2 + 1.0, 2.2, -0.01, 0.9, c=0.3, bottom=0.9)
    for sg in (-1, 1):
        body = body + ext(rect(sg * (w / 2) - (1.2 if sg > 0 else 0.0), 1.2, sg * (w / 2) + (0.0 if sg > 0 else 1.2), hwall - 0.4),
                          -0.01, 0.5)
    body = body + ext(poly([(-0.6, lb[3] - 0.3), (0.6, lb[3] - 0.3), (0.8, lb[3] + 1.4), (-0.8, lb[3] + 1.4)]), -0.01, 0.9)
    core = ext(face.offset(-1.2, JoinType.Miter, 4.0) ^ rect(-50, 1.2, 50, hwall), -dep + 1.2, -1.2)
    return body, core, face, (R, cy)


def arched_roof_cs(w, R, cy, t=1.0, eave=1.2, seam_pitch=2.2):
    """Cross-section (u, v) of the dormer's arched tin roof: a band over the arc of radius R
    (centre (0, cy)), ``t`` thick, running ``eave`` past the face's sides, with standing
    seams (little ribs) every ``seam_pitch`` along it; extruded along the dormer's depth."""
    a0 = math.asin(min(0.999, (w / 2 + eave) / (R + t)))
    n = 48
    outer = [((R + t) * math.sin(a), cy + (R + t) * math.cos(a)) for a in np.linspace(-a0, a0, n)]
    inner = [(R * math.sin(a), cy + R * math.cos(a)) for a in np.linspace(a0, -a0, n)]
    band = poly(outer + inner)
    seams = []
    arc_len = 2 * a0 * (R + t)
    k = int(arc_len / seam_pitch)
    for j in range(1, k):
        a = -a0 + 2 * a0 * j / k
        c, s = math.cos(a), math.sin(a)
        p = ((R + t - 0.05) * s, cy + (R + t - 0.05) * c)
        seams.append(poly([(p[0] - 0.25 * c, p[1] + 0.25 * s), (p[0] + 0.25 * c, p[1] - 0.25 * s),
                           (p[0] + 0.25 * c + 0.4 * s, p[1] - 0.25 * s + 0.4 * c), (p[0] - 0.25 * c + 0.4 * s, p[1] + 0.25 * s + 0.4 * c)]))
    return cs_union([band] + seams)

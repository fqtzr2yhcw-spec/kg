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
from manifold3d import JoinType

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

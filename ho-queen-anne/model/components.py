"""Detail components built in wall-local (u, v, w) coordinates.

Each builder returns ``(opening, parts)`` where ``opening`` is a CrossSection
to cut from the wall and ``parts`` maps a material name to a Manifold.
"""
import math
import numpy as np
from manifold3d import Manifold as M, CrossSection as CS
from geom import box, union, rect, poly, cs_union, revolve, frame_matrix, ft, inch


def _add(parts, key, m):
    if m is None or m.is_empty():
        return
    parts.setdefault(key, []).append(m)


def finish(parts):
    return {k: union(v) for k, v in parts.items()}


def sash_frame(u0, v0, u1, v1, w0, w1, stile=0.42, top=0.42, bot=0.42):
    outer = rect(u0, v0, u1, v1)
    inner = rect(u0 + stile, v0 + bot, u1 - stile, v1 - top)
    return M.extrude(outer - inner, w1 - w0).translate([0, 0, w0])


def window(uc, vb, w, h, lites="2/2", head="cornice", tex=0.4, T=2.4,
           cw=inch(5), sill=True, arched=False):
    """Double-hung window with casing, head and sill."""
    parts = {}
    u0, u1 = uc - w / 2, uc + w / 2
    v1 = vb + h
    opening = rect(u0, vb, u1, v1)
    face = tex + 0.3  # casing face height above sheathing

    # jamb liner
    _add(parts, "trim", M.extrude(opening - rect(u0 + 0.3, vb + 0.3, u1 - 0.3, v1 - 0.3),
                                   T - 0.2).translate([0, 0, -T]))
    # glass
    _add(parts, "glass", box([u0, vb, -1.45], [u1, v1, -1.3]))
    # sashes
    fr = 0.3
    vm = vb + fr + (h - 2 * fr) * 0.5
    su0, su1 = u0 + fr, u1 - fr
    _add(parts, "sash", sash_frame(su0, vm - 0.2, su1, v1 - fr, -1.3, -0.9,
                                   stile=0.42, top=0.42, bot=0.4))
    _add(parts, "sash", sash_frame(su0, vb + fr, su1, vm + 0.2, -0.9, -0.5,
                                   stile=0.42, top=0.4, bot=0.62))
    if lites == "2/2":
        _add(parts, "sash", box([uc - 0.14, vm, -1.3], [uc + 0.14, v1 - fr, -1.0]))
        _add(parts, "sash", box([uc - 0.14, vb + fr, -0.9], [uc + 0.14, vm, -0.6]))
    elif lites == "qa":
        # Queen Anne upper sash: border of small lites around a large pane
        bi = 0.42 + 0.95
        ib0, ib1 = su0 + bi, su1 - bi
        jb0, jb1 = vm - 0.2 + 0.4 + 0.95, v1 - fr - bi
        for uu in (ib0, ib1):
            _add(parts, "sash", box([uu - 0.12, vm, -1.3], [uu + 0.12, v1 - fr, -1.05]))
        for vv in (jb0, jb1):
            _add(parts, "sash", box([su0, vv - 0.12, -1.3], [su1, vv + 0.12, -1.05]))
        # small panes along border
        n = max(2, int(round((ib1 - ib0) / 1.2)))
        for k in range(1, n):
            uu = ib0 + (ib1 - ib0) * k / n
            _add(parts, "sash", box([uu - 0.1, jb1, -1.3], [uu + 0.1, v1 - fr, -1.05]))
        m = max(2, int(round((jb1 - jb0) / 1.2)))
        for k in range(1, m):
            vv = jb0 + (jb1 - jb0) * k / m
            for (a, b) in ((su0, ib0), (ib1, su1)):
                _add(parts, "sash", box([a, vv - 0.1, -1.3], [b, vv + 0.1, -1.05]))
        # coloured glass border
        border = rect(su0, vm, su1, v1 - fr) - rect(ib0, jb0, ib1, jb1)
        _add(parts, "stained", M.extrude(border, 0.1).translate([0, 0, -1.29]))
    # casing
    _add(parts, "trim", M.extrude(rect(u0 - cw, vb, u1 + cw, v1 + cw) - opening,
                                   face + 0.3).translate([0, 0, -0.3]))
    # corner blocks / plinths effect: thin backband
    bb = rect(u0 - cw - 0.25, vb, u1 + cw + 0.25, v1 + cw + 0.25) - rect(u0 - cw, vb - 1, u1 + cw, v1 + cw)
    _add(parts, "trim", M.extrude(bb, face + 0.15).translate([0, 0, -0.3]))
    top = v1 + cw
    if head in ("cornice", "pediment", "hood"):
        a0, a1 = u0 - cw - 0.35, u1 + cw + 0.35
        _add(parts, "trim", box([a0, top, -0.3], [a1, top + ft(1.0), face + 0.2]))
        _add(parts, "accent", box([a0 + 0.35, top + 0.35, face + 0.2], [a1 - 0.35, top + ft(1.0) - 0.35, face + 0.32]))
        _add(parts, "trim", box([a0 - 0.45, top + ft(1.0), -0.3], [a1 + 0.45, top + ft(1.0) + 0.45, face + 0.85]))
        _add(parts, "trim", box([a0 - 0.2, top + ft(1.0) - 0.25, -0.3], [a1 + 0.2, top + ft(1.0), face + 0.55]))
        ctop = top + ft(1.0) + 0.45
        if head == "pediment":
            half = (a1 - a0) / 2 + 0.45
            tri = poly([(uc - half, ctop), (uc + half, ctop), (uc, ctop + half * 0.42)])
            _add(parts, "trim", M.extrude(tri, face + 0.7).translate([0, 0, -0.3]))
        # small brackets under cornice ends
        for uu in (a0 + 0.1, a1 - 0.6):
            _add(parts, "trim", box([uu, top - 1.2, face], [uu + 0.5, top, face + 0.45]))
    if sill:
        _add(parts, "trim", box([u0 - cw - 0.5, vb - 0.55, -0.6], [u1 + cw + 0.5, vb, face + 0.95]))
        _add(parts, "trim", box([u0 - 0.1, vb - 1.6, -0.3], [u1 + 0.1, vb - 0.55, face + 0.25]))
    return opening, finish(parts)


def double_door(uc, vb, w, h, transom=ft(1.6), tex=0.4, T=2.4, cw=inch(6)):
    parts = {}
    u0, u1 = uc - w / 2, uc + w / 2
    v1 = vb + h + transom
    opening = rect(u0, vb, u1, v1)
    face = tex + 0.3
    _add(parts, "trim", M.extrude(opening - rect(u0 + 0.35, vb, u1 - 0.35, v1 - 0.35),
                                   T - 0.2).translate([0, 0, -T]))
    dv1 = vb + h
    # transom bar + glass
    _add(parts, "trim", box([u0, dv1, -1.6], [u1, dv1 + 0.5, -0.5]))
    _add(parts, "glass", box([u0, dv1, -1.5], [u1, v1, -1.35]))
    _add(parts, "sash", sash_frame(u0 + 0.35, dv1 + 0.5, u1 - 0.35, v1 - 0.35, -1.35, -0.9,
                                   stile=0.4, top=0.4, bot=0.4))
    nb = 3
    for k in range(1, nb):
        uu = u0 + 0.35 + (w - 0.7) * k / nb
        _add(parts, "sash", box([uu - 0.12, dv1 + 0.5, -1.35], [uu + 0.12, v1 - 0.35, -1.1]))
    # leaves
    lw = (w - 0.7) / 2
    for i in range(2):
        a = u0 + 0.35 + i * lw
        b = a + lw
        leaf = rect(a + 0.05, vb, b - 0.05, dv1)
        glass = rect(a + 0.55, vb + h * 0.48, b - 0.55, dv1 - 0.6)
        _add(parts, "door", M.extrude(leaf - glass, 0.5).translate([0, 0, -1.2]))
        _add(parts, "glass", M.extrude(glass, 0.12).translate([0, 0, -1.1]))
        # raised panels
        for (pv0, pv1) in ((vb + 0.8, vb + h * 0.2), (vb + h * 0.24, vb + h * 0.44)):
            _add(parts, "door", box([a + 0.6, pv0, -0.7], [b - 0.6, pv1, -0.52]))
            _add(parts, "door", box([a + 0.85, pv0 + 0.25, -0.52], [b - 0.85, pv1 - 0.25, -0.42]))
        # knob
        kx = b - 0.5 if i == 0 else a + 0.5
        _add(parts, "brass", box([kx - 0.18, vb + h * 0.45 - 0.18, -0.7], [kx + 0.18, vb + h * 0.45 + 0.18, -0.35]))
    # casing + pedimented head
    _add(parts, "trim", M.extrude(rect(u0 - cw, vb, u1 + cw, v1 + cw) - opening,
                                   face + 0.35).translate([0, 0, -0.3]))
    for uu in (u0 - cw, u1):
        # fluted pilasters
        _add(parts, "trim", box([uu + 0.15, vb, face], [uu + cw - 0.15, v1, face + 0.25]))
        _add(parts, "trim", box([uu - 0.15, vb, -0.3], [uu + cw + 0.15, vb + 1.4, face + 0.5]))
    top = v1 + cw
    a0, a1 = u0 - cw - 0.5, u1 + cw + 0.5
    _add(parts, "trim", box([a0, top, -0.3], [a1, top + ft(1.2), face + 0.3]))
    _add(parts, "trim", box([a0 - 0.5, top + ft(1.2), -0.3], [a1 + 0.5, top + ft(1.2) + 0.5, face + 0.95]))
    half = (a1 - a0) / 2 + 0.5
    ctop = top + ft(1.2) + 0.5
    tri = poly([(uc - half, ctop), (uc + half, ctop), (uc, ctop + half * 0.45)])
    inner = poly([(uc - half + 1.0, ctop + 0.35), (uc + half - 1.0, ctop + 0.35),
                  (uc, ctop + half * 0.45 - 0.55)])
    _add(parts, "trim", M.extrude(tri - inner, face + 0.8).translate([0, 0, -0.3]))
    _add(parts, "accent", M.extrude(inner, face + 0.35).translate([0, 0, -0.3]))
    return opening, finish(parts)


# ---------------------------------------------------------------- porch bits
def turned_post(h, sq=inch(6.5)):
    """Turned porch post standing on z = 0, height h."""
    s = sq / 2
    base = box([-s, -s, 0], [s, s, h * 0.2])
    cap = box([-s, -s, h * 0.86], [s, s, h])
    r = s * 0.8
    prof = [(0, h * 0.2 - 0.01), (r * 0.95, h * 0.2 - 0.01), (r * 1.05, h * 0.23),
            (r * 0.7, h * 0.26), (r * 0.62, h * 0.30), (r * 0.9, h * 0.34), (r * 0.62, h * 0.38),
            (r * 0.55, h * 0.55), (r * 0.62, h * 0.70), (r * 0.9, h * 0.74), (r * 0.62, h * 0.78),
            (r * 0.7, h * 0.82), (r * 1.05, h * 0.845), (r * 0.95, h * 0.861), (0, h * 0.861)]
    shaft = revolve(prof, 16)
    return union([base, cap, shaft])


def spindle(h, r=0.34):
    prof = [(0, 0), (r * 0.8, 0), (r * 0.8, h * 0.12), (r * 1.2, h * 0.2), (r * 0.6, h * 0.3),
            (r * 0.55, h * 0.5), (r * 0.6, h * 0.7), (r * 1.2, h * 0.8), (r * 0.8, h * 0.88),
            (r * 0.8, h), (0, h)]
    return revolve(prof, 8)


def scroll_bracket(a, b, thick=0.55, seg=10):
    """Flat gingerbread bracket in the (x, z) plane: a = horizontal reach, b = drop.

    Occupies x in [0, a], z in [-b, 0], y in [-thick/2, thick/2]. Corner at origin.
    """
    pts = [(0, 0), (a, 0), (a, -0.6)]
    # concave sweep from (a,-0.6) down to (0.6,-b)
    for k in range(seg + 1):
        t = k / seg
        ang = t * math.pi / 2
        x = 0.6 + (a - 0.6) * (1 - math.sin(ang))
        z = -0.6 - (b - 0.6) * (1 - math.cos(ang))
        pts.append((x, z))
    pts += [(0, -b)]
    outer = poly(pts)
    # pierced circle
    hole = CS.circle(min(a, b) * 0.16, 10).translate((a * 0.28, -b * 0.28))
    cs = outer - hole
    m = M.extrude(cs, thick).translate([0, 0, -thick / 2])
    # map (x, y_cs, z_ext) -> (x, z, y)
    return m.transform(frame_matrix([0, 0, 0], [1, 0, 0], [0, 0, 1], [0, -1, 0]))


def eave_bracket(reach, drop, thick=0.9):
    """Stout cornice bracket: body in (x=reach outward, z=down)."""
    pts = [(0, 0), (reach, 0), (reach, -0.5)]
    seg = 8
    for k in range(seg + 1):
        t = k / seg
        x = reach - (reach - 0.7) * t
        z = -0.5 - (drop - 0.5) * (t ** 1.8)
        pts.append((x, z))
    pts += [(0, -drop)]
    m = M.extrude(poly(pts), thick).translate([0, 0, -thick / 2])
    return m.transform(frame_matrix([0, 0, 0], [1, 0, 0], [0, 0, 1], [0, -1, 0]))

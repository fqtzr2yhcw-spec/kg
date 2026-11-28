"""Printable window and door parts for the kit, in wall-local (u, v, w) coordinates.

Wall convention: sheathing plane at w = 0, core w in [-T, 0], texture w >= 0.

Every window is two single-colour parts:
  * casing (Cream): casing, head, sill and apron. Its flat back sits in a
    PK-deep pocket cut into the wall face, so it drops into place. Printed
    back-down.
  * sash (Oxblood): printed interior-side down. Its first 0.2 mm layer is the
    glass, the second layer forms a flange that sits on the inside face of
    the wall, and a plug ring keys it into the opening. Sash frames and
    muntins stand up from the glass.
Doors follow the same pattern with a Walnut door insert.
"""
from manifold3d import Manifold as M
from geom import box, union, rect, poly, cs_union, ft, inch

PK = 0.4        # pocket depth for trim
CLR = 0.1       # fit clearance per side
TEX = 0.42      # tallest wall texture above sheathing
FACE = TEX + 0.3  # casing face height above sheathing
LAYER = 0.2     # glazing thickness (one layer)


def _ring(outer, inner):
    return outer - inner


def casing(uc, vb, w, h, head="cornice", cw=inch(5), head_h=ft(0.9), sill=True):
    """Returns (opening CS, pocket CS, casing Manifold)."""
    u0, u1 = uc - w / 2, uc + w / 2
    v1 = vb + h
    opening = rect(u0, vb, u1, v1)
    wb = -PK
    parts = []
    backs = []
    frame = rect(u0 - cw, vb, u1 + cw, v1 + cw) - opening
    parts.append(M.extrude(frame, FACE - wb).translate([0, 0, wb]))
    backs.append(rect(u0 - cw, vb, u1 + cw, v1 + cw))
    bb = rect(u0 - cw - 0.25, vb, u1 + cw + 0.25, v1 + cw + 0.25) - rect(u0 - cw, vb - 1, u1 + cw, v1 + cw)
    parts.append(M.extrude(bb, FACE - 0.15 - wb).translate([0, 0, wb]))
    backs.append(rect(u0 - cw - 0.25, vb, u1 + cw + 0.25, v1 + cw + 0.25))
    top = v1 + cw + 0.25
    if head in ("cornice", "pediment"):
        a0, a1 = u0 - cw - 0.35, u1 + cw + 0.35
        fr = box([a0, top, wb], [a1, top + head_h, FACE + 0.2])
        # recessed panel where the render had an oxblood accent
        fr = fr - box([a0 + 0.4, top + 0.4, FACE + 0.08], [a1 - 0.4, top + head_h - 0.4, FACE + 0.3])
        parts.append(fr)
        parts.append(box([a0 - 0.45, top + head_h, wb], [a1 + 0.45, top + head_h + 0.45, FACE + 0.85]))
        parts.append(box([a0 - 0.2, top + head_h - 0.25, wb], [a1 + 0.2, top + head_h, FACE + 0.55]))
        backs.append(rect(a0 - 0.45, top, a1 + 0.45, top + head_h + 0.45))
        ctop = top + head_h + 0.45
        if head == "pediment":
            half = (a1 - a0) / 2 + 0.45
            tri = poly([(uc - half, ctop), (uc + half, ctop), (uc, ctop + half * 0.42)])
            parts.append(M.extrude(tri, FACE + 0.7 - wb).translate([0, 0, wb]))
            backs.append(tri)
        for uu in (a0 + 0.1, a1 - 0.6):
            parts.append(box([uu, top - 1.2, FACE - 0.05], [uu + 0.5, top, FACE + 0.45]))
    if sill:
        parts.append(box([u0 - cw - 0.5, vb - 0.55, wb], [u1 + cw + 0.5, vb, FACE + 0.95]))
        parts.append(box([u0 - 0.1, vb - 1.6, wb], [u1 + 0.1, vb - 0.55, FACE + 0.25]))
        backs.append(rect(u0 - cw - 0.5, vb - 0.55, u1 + cw + 0.5, vb))
        backs.append(rect(u0 - 0.1, vb - 1.6, u1 + 0.1, vb - 0.55))
    pocket = cs_union(backs).offset(CLR, _miter())
    return opening, pocket, union(parts)


def _miter():
    from manifold3d import JoinType
    return JoinType.Miter


def sash_frame(u0, v0, u1, v1, w0, w1, stile=0.5, top=0.5, bot=0.5):
    outer = rect(u0, v0, u1, v1)
    inner = rect(u0 + stile, v0 + bot, u1 - stile, v1 - top)
    return M.extrude(outer - inner, w1 - w0).translate([0, 0, w0])


def sash(uc, vb, w, h, T, lites="2/2", flange=0.8, bottom_flange=True):
    """Sash + glazing insert. Returns Manifold (wall-local)."""
    u0, u1 = uc - w / 2, uc + w / 2
    v1 = vb + h
    g0 = -T - 2 * LAYER           # glass layer (first printed layer)
    g1 = -T - LAYER
    fvb = vb - flange if bottom_flange else vb
    parts = []
    outer = rect(u0 - flange, fvb, u1 + flange, v1 + flange)
    parts.append(M.extrude(outer, LAYER).translate([0, 0, g0]))
    parts.append(M.extrude(outer - rect(u0, vb, u1, v1), LAYER).translate([0, 0, g1]))
    # plug ring keyed into the opening
    p0, p1 = u0 + CLR, u1 - CLR
    q0, q1 = vb + CLR, v1 - CLR
    plug = rect(p0, q0, p1, q1) - rect(p0 + 0.45, q0 + 0.45, p1 - 0.45, q1 - 0.45)
    parts.append(M.extrude(plug, 1.0 + LAYER).translate([0, 0, g1]))
    # sashes
    su0, su1 = p0 + 0.45, p1 - 0.45
    sv0, sv1 = q0 + 0.45, q1 - 0.45
    vm = (sv0 + sv1) / 2
    parts.append(sash_frame(su0, vm - 0.2, su1, sv1, g1, g1 + 0.6, stile=0.45, top=0.45, bot=0.45))
    parts.append(sash_frame(su0, sv0, su1, vm + 0.2, g1, g1 + 1.0, stile=0.45, top=0.45, bot=0.65))
    if lites == "2/2":
        parts.append(box([uc - 0.2, vm, g1], [uc + 0.2, sv1, g1 + 0.45]))
        parts.append(box([uc - 0.2, sv0, g1], [uc + 0.2, vm, g1 + 0.45]))
    elif lites == "qa":
        bi = 0.45 + 0.9
        ib0, ib1 = su0 + bi, su1 - bi
        jb0, jb1 = vm + 0.25 + 0.9, sv1 - bi
        for uu in (ib0, ib1):
            parts.append(box([uu - 0.18, vm, g1], [uu + 0.18, sv1, g1 + 0.45]))
        for vv in (jb0, jb1):
            parts.append(box([su0, vv - 0.18, g1], [su1, vv + 0.18, g1 + 0.45]))
        n = max(2, int(round((ib1 - ib0) / 1.3)))
        for k in range(1, n):
            uu = ib0 + (ib1 - ib0) * k / n
            parts.append(box([uu - 0.17, jb1, g1], [uu + 0.17, sv1, g1 + 0.45]))
        m = max(2, int(round((jb1 - jb0) / 1.3)))
        for k in range(1, m):
            vv = jb0 + (jb1 - jb0) * k / m
            for (a, b) in ((su0, ib0), (ib1, su1)):
                parts.append(box([a, vv - 0.17, g1], [b, vv + 0.17, g1 + 0.45]))
    return union(parts)


def door_casing(uc, vb, w, h, cw=inch(6), pediment=True, head_h=ft(1.1), ped_slope=0.45):
    """Front-door casing with fluted pilasters and an open pediment."""
    u0, u1 = uc - w / 2, uc + w / 2
    v1 = vb + h
    opening = rect(u0, vb, u1, v1)
    wb = -PK
    parts, backs = [], []
    frame = rect(u0 - cw, vb, u1 + cw, v1 + cw) - opening
    parts.append(M.extrude(frame, FACE + 0.35 - wb).translate([0, 0, wb]))
    backs.append(rect(u0 - cw, vb, u1 + cw, v1 + cw))
    for uu in (u0 - cw, u1):
        # flutes: raised strip + plinth block
        parts.append(box([uu + 0.3, vb + 1.6, FACE + 0.35], [uu + cw - 0.3, v1 - 0.2, FACE + 0.6]))
        parts.append(box([uu - 0.15, vb, wb], [uu + cw + 0.15, vb + 1.6, FACE + 0.6]))
        backs.append(rect(uu - 0.15, vb, uu + cw + 0.15, vb + 1.6))
    top = v1 + cw
    a0, a1 = u0 - cw - 0.5, u1 + cw + 0.5
    if head_h > 0:
        parts.append(box([a0, top, wb], [a1, top + head_h, FACE + 0.3]))
    parts.append(box([a0 - 0.5, top + head_h, wb], [a1 + 0.5, top + head_h + 0.5, FACE + 0.95]))
    backs.append(rect(a0 - 0.5, top, a1 + 0.5, top + head_h + 0.5))
    if pediment:
        half = (a1 - a0) / 2 + 0.5
        ctop = top + head_h + 0.5
        tri = poly([(uc - half, ctop), (uc + half, ctop), (uc, ctop + half * ped_slope)])
        inner = poly([(uc - half + 1.1, ctop + 0.4), (uc + half - 1.1, ctop + 0.4),
                      (uc, ctop + half * ped_slope - 0.6)])
        parts.append(M.extrude(tri - inner, FACE + 0.8 - wb).translate([0, 0, wb]))
        parts.append(M.extrude(inner, FACE + 0.2 - wb).translate([0, 0, wb]))
        backs.append(tri)
    pocket = cs_union(backs).offset(CLR, _miter())
    return opening, pocket, union(parts)


def door_insert(uc, vb, w, h, T, transom=ft(1.6), leaves=2, flange=0.8):
    """Door leaves + transom, printed interior-side down (first layer = glass)."""
    u0, u1 = uc - w / 2, uc + w / 2
    v1 = vb + h + transom
    g0 = -T - 2 * LAYER
    g1 = -T - LAYER
    parts = []
    outer = rect(u0 - flange, vb, u1 + flange, v1 + flange)
    # glass layer only where there is glass; solid door elsewhere
    dv1 = vb + h
    parts.append(M.extrude(outer, LAYER).translate([0, 0, g0]))
    parts.append(M.extrude(outer - rect(u0, vb, u1, v1), LAYER).translate([0, 0, g1]))
    p0, p1 = u0 + CLR, u1 - CLR
    plug = rect(p0, vb, p1, v1 - CLR) - rect(p0 + 0.45, vb, p1 - 0.45, v1 - CLR - 0.45)
    parts.append(M.extrude(plug, 1.0 + LAYER).translate([0, 0, g1]))
    # transom bar + sash bars
    parts.append(box([p0, dv1, g1], [p1, dv1 + 0.55, g1 + 1.2]))
    nb = 3
    for k in range(1, nb):
        uu = p0 + (p1 - p0) * k / nb
        parts.append(box([uu - 0.17, dv1 + 0.55, g1], [uu + 0.17, v1 - CLR - 0.45, g1 + 0.5]))
    lw = (p1 - p0 - 0.9) / leaves
    for i in range(leaves):
        a = p0 + 0.45 + i * lw
        b = a + lw
        leaf = rect(a + 0.05, vb, b - 0.05, dv1)
        glass = rect(a + 0.6, vb + h * 0.5, b - 0.6, dv1 - 0.6)
        parts.append(M.extrude(leaf - glass, 0.9).translate([0, 0, g1]))
        for (pv0, pv1) in ((vb + 0.8, vb + h * 0.22), (vb + h * 0.26, vb + h * 0.46)):
            parts.append(box([a + 0.65, pv0, g1 + 0.9], [b - 0.65, pv1, g1 + 1.1]))
            parts.append(box([a + 0.95, pv0 + 0.3, g1 + 1.1], [b - 0.95, pv1 - 0.3, g1 + 1.25]))
        kx = b - 0.55 if (leaves == 2 and i == 0) else a + 0.55
        if leaves == 1:
            kx = b - 0.6
        parts.append(box([kx - 0.2, vb + h * 0.46 - 0.2, g1 + 0.9], [kx + 0.2, vb + h * 0.46 + 0.2, g1 + 1.35]))
    return union(parts)

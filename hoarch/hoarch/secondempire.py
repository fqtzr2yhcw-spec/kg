"""Second Empire mansard batch (houses 81 to 90): the batch's roof system, and each house's
own parts. Like ``colonial4`` and ``craftsman2`` the module registers its cornice ornaments,
brackets, corner boards, foundations and porch parts on import; nothing in one house's section
is shared with another building.

The roof system (studied from the owner's tan reference kit; the designs are our own):

* the eave is a deep stack of rings (``hoarch.cornice``): an architrave course, the frieze, a
  second course, the bracket bed and the crown, so the eave alone is three parts in several
  colours;
* the mansard band (``roof.mansard``) is the last storey: hollow, slated, printed upside down,
  with a pocket in every bay for a window add-in;
* an add-in (``addin``) is one part: a slate-coloured plug that goes into the pocket (its sides
  are a dormer's cheeks, its top the dormer's little roof, its front the glass) and the frame in
  front of it (casing, hood, keystone, sill, glazing bars), one filament change between them.
  Its face stands upright while the roof leans back, so its head stands proud like a dormer's.
  It prints on its back, with supports under the frame only;
* the crest (``crest_ring``) on the band's flat top: a course and a crown, printed upside down as
  one part with one change, carrying the flat deck on a seat inside; iron cresting strips are
  keyed into the crown's top.
"""
import math

import numpy as np
from manifold3d import JoinType, Manifold as M

from .core import RIB, Facade, arch_cs, box, ccw, circle, cs_union, poly, rect, sweep_ring, union
from .ornament import chamfer_box, console, ext, fan_crest, oval, stroke, swag
from . import cornice as CO, features as FT, moulding as MD, openings as O, porchwork as PW, roof as R
from . import shell as SH, trimwork as TW
from .colonial import _lens, _st
from .colonial4 import _glazed, _muntins, _panel

ENTER = 0.8         # how far an add-in's plug runs into the band at its head
FCLR = 0.15         # clearance: add-in frame to the roof face, plug to its pocket


# ================================================================== the roof system
def face_at(prof, z):
    """The outer face's offset of a mansard profile [(d, z), ...] at height z."""
    if z <= prof[0][1]:
        return prof[0][0]
    for (d0, z0), (d1, z1) in zip(prof[:-1], prof[1:]):
        if z0 - 1e-9 <= z <= z1 + 1e-9 and z1 > z0:
            return d0 + (d1 - d0) * (z - z0) / (z1 - z0)
    return prof[-1][0]


def bell_profile(d0, z0, d1, z1, kick=(1.4, 1.4), n=6, power=1.8):
    """A bell-cast (concave) mansard face: a short kick at the foot, then a curve leaning back
    fast low down and slower toward the top, from (d0, z0) to (d1, z1)."""
    pts = [(d0, z0), (d0 - kick[0], z0 + kick[1])]
    da, za = pts[-1]
    for k in range(1, n + 1):
        s = k / n
        pts.append((da + (d1 - da) * (1 - (1 - s) ** power), za + (z1 - za) * s))
    return pts


def addin_place(sp, prof, z_sill):
    """Where an add-in ``sp`` stands on a mansard of outer profile ``prof``, its sill line at
    world z_sill: (w0, depth). w0 is the glass plane's offset from the wall plane (the frame's
    back, just clear of the roof face at its lowest point); depth is the plug's length behind
    it, so that it runs ENTER into the band at its head (on the 0.2 grid: the colour change)."""
    v_lo, vt = sp["bottom"], sp["outline"].bounds()[3]
    w0 = max(face_at(prof, z_sill + v) for v in np.linspace(v_lo, vt, 25)) + FCLR
    wb = face_at(prof, z_sill + vt) - ENTER
    return w0, math.ceil((w0 - wb) / 0.2 - 1e-6) * 0.2


def addin(sp, depth):
    """One add-in part in its local frame (u across, v up from the sill line, w out; the glass
    at w = 0): the plug (outline ``sp['outline']``, ``depth`` long behind the glass) and the frame
    (``sp['frame']`` solids in front). Returns dict(solid, plug, frame, glass, keep, flash):
    ``keep`` cuts its pocket in the band, ``flash`` clears the slates round its frame."""
    plug = ext(sp["outline"], -depth, 0.0)
    frame = union(sp["frame"])
    if sp.get("bars") is not None:
        frame = frame + ext(sp["bars"] ^ sp["light"].offset(0.1, JoinType.Miter, 4.0), -0.01, 0.8)
    glass = plug ^ ext(sp["light"], -0.4, 0.01)
    keep = ext(sp["outline"].offset(FCLR, JoinType.Round), -depth - FCLR, 0.3)
    flash = ext(frame.project().offset(0.25, JoinType.Round) + sp["outline"].offset(0.45, JoinType.Round),
                -depth - 3.0, 14.0)
    return dict(solid=plug + frame, plug=plug, frame=frame, glass=glass, keep=keep, flash=flash)


def _st_down(cs, h, b, d):
    """Relief on an upright face, for a ring printed upside down: stepped from the top."""
    m = _st(cs.mirror([0, 1]).translate([0, h]), b, d)
    return m.mirror([0, 1, 0]).translate([0, h, 0])


def crest_ring(path, d_s, z_s, t_s, course, crown, deck_th=1.2, s_out=-0.6, lip=1.0):
    """The crest on a mansard band's flat top (its outer edge ``d_s`` off the wall plane ``path``,
    ``t_s`` thick, at z_s): one part, printed upside down: a course ring sitting on the band top
    (a lip drops inside the band to locate it), dict(h, b, orn (a cs generator), role), and a
    crown over it, dict(h, P, kind, role, blocks=(w, pitch) or None), widening to P with a 45
    degree seat inside for the deck. Returns dict(solid, zones, change, z_top, deck, path)."""
    top = R.offset_path(path, d_s)
    hA, hB = course["h"], crown["h"]
    H = hA + hB
    b, P = course["b"], crown["P"]
    di = -t_s - FCLR
    cpro = CO.crown_profile(crown["kind"], b, P, hB)
    prof = [(di - lip, -1.2), (di, -1.2), (di, 0.0), (b, 0.0), (b, hA)] + [(d, hA + z) for d, z in cpro[1:]] + \
           [(P, H), (s_out, H), (s_out - deck_th, H - deck_th), (di - lip, H - deck_th)]
    ring = sweep_ring(top, [(d, z_s + z) for d, z in prof])
    orn = []
    for f in CO._edges(top):
        if f.L < 4.0:
            continue
        sol = [_st_down(cs, hA, b - 0.05, course.get("d", 0.4)) for cs in course["orn"](f.L, hA)]
        if crown.get("blocks"):
            bw, bp = crown["blocks"]
            for u in CO._us(f.L, bp, 2.0):
                sol.append(box([u - bw / 2, hA - 0.01, b - 0.05], [u + bw / 2, hA + hB * 0.55, b + (P - b) * 0.7]))
        orn += [CO._place(f, z_s, m) for m in sol]
    solid = ring + union(orn)
    zc = z_s + hA
    zones = [(course["role"], solid ^ box([-1e4, -1e4, z_s - 5], [1e4, 1e4, zc])),
             (crown["role"], solid ^ box([-1e4, -1e4, zc], [1e4, 1e4, z_s + H + 5]))]
    P_, Mi = R._edges(top)
    a = np.c_[P_ + (s_out - FCLR) * Mi, np.full(len(P_), z_s + H)]
    bb = np.c_[P_ + (s_out - FCLR - deck_th) * Mi, np.full(len(P_), z_s + H - deck_th)]
    deck = M.hull_points(np.vstack([a, bb]).tolist())
    change = (round(hB / 0.2) * 0.2, course["role"]) if course["role"] != crown["role"] else None
    return dict(solid=solid, zones=zones, change=change, z_top=z_s + H, deck=deck, path=top, P=P)


def cresting_strips(path, z0, d_off, fence, h, e=0.4):
    """Flat-printing cresting strips along each edge of ``path`` (offset ``d_off``), standing
    on z0, each stopping ``e`` short of the corners: [(edge index, world solid, frame, length)].
    ``fence(L, h)`` -> a CrossSection in (u, v); strips are 0.8 thick."""
    P_, Mi = R._edges(path)
    out = []
    n = len(P_)
    for i in range(n):
        a, b_ = P_[i] + d_off * Mi[i], P_[(i + 1) % n] + d_off * Mi[(i + 1) % n]
        f = Facade(a, b_, 0.0)
        L = f.L - 2 * e
        if L < 4.0:
            continue
        cs = fence(L, h).translate([e, 0.0])
        strip = M.extrude(cs, 0.8).translate([0, 0, -0.4])
        A = f.A.copy()
        A[:, 3] = f.world(0, 0, 0) + np.array([0, 0, z0])
        out.append((i, strip.transform(A), A, L))
    return out


# ================================================================== the Montclair (house 81)
# A Second Empire cube of cream-city brick: brownstone trim, gilt accents, a straight mansard
# of square slate banded with lozenges of diamond-cut slate, twelve add-ins, a full-width veranda.

def slate_lozenges(k, j):
    """The Montclair's slating: square slates, with a band of lozenges laid in diamond-cut
    slates (each lozenge seven courses tall and four slates across) round the middle of the
    roof, a lozenge every eight slates."""
    r = k % 16 - 4
    if 0 <= r <= 6:
        m = (j + 0.5 * (k % 2)) % 8 - 4.0
        if abs(m) <= (3 - abs(r - 3)) * 0.5 + 0.01:
            return "diamond"
    return "square"


# ------------------------------------------------------------------ cornice ornaments
def _baluster_cs(x, v0, H, w=1.1):
    t = [(0.55, 0.0), (0.55, 0.12), (0.3, 0.2), (0.55, 0.42), (0.5, 0.55), (0.25, 0.72), (0.25, 0.82),
         (0.45, 0.88), (0.45, 1.0)]
    return poly([(x + w * fx, v0 + H * fy) for fx, fy in t] + [(x - w * fx, v0 + H * fy) for fx, fy in reversed(t)])


def frieze_balustrade(L, h, b, pitch, margin, pair, half):
    """A blind balustrade: little vase balusters between pedestal blocks at the stations, under
    a rail and over a plinth (the Montclair's storey joint)."""
    v0, v1 = 0.8, h - 0.8
    out = [_st(rect(0.4, v1 - 0.6, L - 0.4, v1 - 0.05), b, 0.45), _st(rect(0.4, v0, L - 0.4, v0 + 0.5), b, 0.45)]
    for u in CO._us(L, pitch, margin, 0.0):
        out.append(_st(rect(u - 0.9, v0, u + 0.9, v1 - 0.05), b, 0.6))
        out.append(_st(rect(u - 0.45, v0 + 1.0, u + 0.45, v1 - 1.1), b + 0.6, 0.2))
    for uc, wd in CO._between(L, pitch, margin, 0.0, 1.0):
        n = max(1, int(wd / 1.7))
        for k in range(n):
            out.append(_st(_baluster_cs(uc - wd / 2 + wd * (k + 0.5) / n, v0 + 0.5, v1 - v0 - 1.1), b, 0.45))
    return out, []


def _bee(x, y, s):
    """A Napoleonic bee seen from above, head up: wings, a striped abdomen, thorax and head."""
    wings = cs_union([_lens((x + sg * 0.62 * s, y + 0.62 * s), 1.25 * s, 0.62 * s, sg * 0.55) for sg in (-1, 1)] +
                     [_lens((x + sg * 0.55 * s, y + 0.05 * s), 0.95 * s, 0.48 * s, -sg * 0.35) for sg in (-1, 1)])
    body = cs_union([oval((x, y - 0.35 * s), 0.42 * s, 0.85 * s, 20), circle((x, y + 0.5 * s), 0.36 * s, 14),
                     circle((x, y + 1.0 * s), 0.27 * s, 12)])
    stripes = cs_union([rect(x - s, y - 0.35 * s + dy * s - 0.11, x + s, y - 0.35 * s + dy * s + 0.11) for dy in (-0.35, 0.05)])
    return wings, body, stripes


def frieze_bees(L, h, b, pitch, margin, pair, half):
    """Napoleon's bees: a gilt bee in every bay, a lozenge either side of it (the Montclair's
    eave)."""
    v0, v1 = 0.8, h - 0.8
    vm = (v0 + v1) / 2
    s = min(1.5, (v1 - v0) / 2.9)
    out = []
    for uc, wd in CO._between(L, pitch, margin, pair, half):
        if wd < 3.4:
            continue
        wings, body, stripes = _bee(uc, vm - 0.1 * s, s)
        out.append(_st(wings, b, 0.35))
        out.append(_st(body, b, 0.6) - ext(stripes, b + 0.4, b + 1.0))
        for sg in (-1, 1):
            x = uc + sg * min(wd / 2 - 0.9, 2.6 * s)
            if abs(x - uc) > 1.6 * s:
                out.append(_st(poly([(x - 0.55, vm), (x, vm + 0.9), (x + 0.55, vm), (x, vm - 0.9)]), b, 0.4))
    return out, []


def course_fasciae(L, h, b, pitch, margin, p):
    """An architrave: two fasciae, the upper one prouder, a bead between them (the Montclair)."""
    v1 = round(h * 0.5 / 0.2) * 0.2
    return [ext(rect(0.2, 0.0, L - 0.2, v1), b - 0.05, b + 0.25), _st(rect(0.2, v1, L - 0.2, h - 0.2), b, 0.55),
            _st(rect(0.2, v1 - 0.4, L - 0.2, v1 + 0.05), b, 0.75)]


def course_leafdart(L, h, b, pitch, margin, p):
    """Leaf and dart: heart-shaped leaves hanging from the head, a dart between each pair (the
    Montclair)."""
    pu = p.get("pu", 2.0)
    n = max(1, int((L - 0.8) / pu))
    u0 = (L - n * pu) / 2
    r = pu * 0.24
    out = []
    for k in range(n):
        uc = u0 + pu * (k + 0.5)
        vt = h - 0.2 - r
        leaf = cs_union([circle((uc - r * 0.75, vt), r, 14), circle((uc + r * 0.75, vt), r, 14),
                         poly([(uc - r * 1.7, vt), (uc + r * 1.7, vt), (uc, 0.25)])])
        out.append(_st(leaf, b, 0.45))
        if k < n - 1:
            ud = uc + pu / 2
            out.append(_st(poly([(ud - 0.28, h - 0.2), (ud + 0.28, h - 0.2), (ud, h * 0.3)]), b, 0.35))
    return out


def olives(L, h):
    """The crest course: olive beads (long ovals) between pairs of discs, as CrossSections (the
    Montclair)."""
    pu = 2.4
    n = max(1, int((L - 1.0) / pu))
    u0 = (L - n * pu) / 2
    vm = h / 2
    out = []
    for k in range(n):
        uc = u0 + pu * (k + 0.5)
        out.append(oval((uc, vm), 0.8, min(0.6, h / 2 - 0.25), 20))
        for sg in (-1, 1):
            out.append(rect(uc + sg * 1.2 - 0.15, vm - min(0.75, h / 2 - 0.1), uc + sg * 1.2 + 0.15, vm + min(0.75, h / 2 - 0.1)))
    return [cs_union(out)]


def bracket_flutedconsole(h, d, t):
    """An Italianate console for pairs: a block head, the front swelling into a scroll and
    sweeping down in an S to a small curl at the foot, a round drop under the curl, and a flute
    following the S sunk into each face (side profile, top at v = 0; the Montclair)."""
    hd = 0.8
    r1 = min(0.3 * h, 0.42 * d)
    r2 = min(0.16 * h, 0.22 * d, 0.6)
    c1 = (d - r1, -hd - r1 * 0.9)
    c2 = (0.3 * d + r2, -h + r2 + 0.9)
    front = [(d, -hd)] + [(c1[0] + r1 * math.cos(a), c1[1] + r1 * math.sin(a)) for a in np.linspace(0.0, -math.pi * 0.55, 8)]
    s_pts = [front[-1]]
    for s in np.linspace(0.1, 1.0, 9):
        s_pts.append((front[-1][0] + (c2[0] + r2 - front[-1][0]) * (3 * s * s - 2 * s ** 3),
                      front[-1][1] + (c2[1] - front[-1][1]) * s))
    body = poly([(0.0, 0.0), (d, 0.0)] + front + s_pts[1:] + [(c2[0], c2[1] - r2), (0.0, -h + 0.9)])
    prof = cs_union([body, circle(c1, r1, 20), circle(c2, r2, 14), rect(0.0, -h + 0.9, 0.6, 0.0),
                     circle((0.35, -h + 0.5), 0.45, 14)])
    flute = stroke([(c1[0] - r1 * 0.2, c1[1] + r1 * 0.1)] + [(p[0] - 0.75, p[1]) for p in s_pts[2:-2]], 0.5)
    return prof - (flute ^ prof.offset(-0.55))


# ------------------------------------------------------------------ the mansard's window add-ins
def _arched_frame(R_in, spring, A=0.9, P=1.3, key=True):
    """The Montclair add-in surround for a round-headed opening of radius R_in springing at
    ``spring``: a moulded architrave, fluted pilasters on the sill, impost blocks, a round
    archivolt with a bead, a scrolled keystone carrying a shell, and the sill on two consoles.
    Returns (frame solids, outer outline, top v, bottom v)."""
    big = cs_union([rect(-R_in, 0.0, R_in, spring), circle((0.0, spring), R_in, 64) ^ rect(-R_in, spring, R_in, spring + R_in + 1)])
    Ro = R_in + A + P
    outer = cs_union([rect(-Ro, 0.0, Ro, spring), circle((0.0, spring), Ro, 72) ^ rect(-Ro, spring - 0.01, Ro, spring + Ro + 1)])
    up = rect(-Ro - 5, spring - 0.01, Ro + 5, spring + Ro + 5)
    parts = [ext(outer - big, 0.0, 0.6),
             MD.band(big.offset(A, JoinType.Round), A, MD.ARCHITRAVE, clip=rect(-Ro - 5, 0.0, Ro + 5, spring + Ro + 5) - big)]
    for sg in (-1, 1):
        u0, u1 = sorted((sg * (R_in + A), sg * Ro))
        um = (u0 + u1) / 2
        parts.append(ext(rect(u0, 0.0, u1, spring - 0.8), 0.0, 1.0) - ext(stroke([(um, 1.2), (um, spring - 1.8)], 0.45), 0.7, 1.3))
        parts.append(chamfer_box(u0 - 0.25, spring - 0.8, u1 + 0.25, spring + 0.2, 0.0, 1.3, c=0.3))
    ring = (circle((0.0, spring), Ro, 72) - circle((0.0, spring), R_in + A, 72)) ^ up
    parts.append(ext(ring, 0.0, 1.0))
    parts.append(ext((circle((0.0, spring), Ro, 72) - circle((0.0, spring), Ro - 0.5, 72)) ^ up, 0.0, 1.4))
    top = spring + Ro
    if key:
        kv0 = spring + R_in - 0.4
        parts.append(MD.scroll_keystone(0.0, kv0, Ro - R_in + 1.6, 1.4, 2.0, 0.0, 1.8))
        parts.append(fan_crest(0.0, spring + Ro + 1.1, 1.6, 0.0, 1.0, rays=3))
        top = spring + Ro + 1.1 + 1.6
    sw = Ro + 0.4
    parts.append(MD.run(-sw, sw, 0.0, MD.SILL, 1.0, up=False))
    for sg in (-1, 1):
        parts.append(console(1.6, 1.0, 0.8, u=sg * (R_in + A + P / 2), v_top=-0.8, w0=0.0))
    return parts, outer, top, -2.4


def addin_montclair(w=5.6, h=11.0):
    """A Montclair add-in: a round-headed two-over-two light in the arched surround."""
    r = w / 2
    spring = h - r
    light = O.opening_cs(w, h, r)
    bars = cs_union([rect(-RIB / 2, -1.0, RIB / 2, h + 1.0), rect(-w, spring * 0.55 - 0.3, w, spring * 0.55 + 0.3)])
    parts, outer, top, bottom = _arched_frame(r, spring)
    parts = [p - ext(light, -1.0, 5.0) for p in parts]
    outline = outer.offset(-0.4, JoinType.Round) ^ rect(-50, 0.2, 50, 100)
    return dict(light=light, bars=bars, frame=parts, outline=outline, top=top, bottom=bottom)


def addin_montclair_twin(w=4.0, h=10.4, gap=1.4):
    """The Montclair's centre add-in: two round-headed lights on a colonnette under one round
    arch, an oculus in its tympanum, in the same surround."""
    r = w / 2
    spring = h - r
    uc = w / 2 + gap / 2
    R_in = uc + r
    lights = cs_union([O.opening_cs(w, h, r).translate([sg * uc, 0.0]) for sg in (-1, 1)])
    ocu = circle((0.0, spring + R_in * 0.62), min(1.2, R_in - r - 0.9), 24)
    light = lights + ocu
    bars = cs_union([rect(-w * 3, spring * 0.55 - 0.3, w * 3, spring * 0.55 + 0.3)] +
                    [rect(sg * uc - RIB / 2, -1.0, sg * uc + RIB / 2, h + 1.0) for sg in (-1, 1)]) ^ lights.offset(0.1)
    parts, outer, top, bottom = _arched_frame(R_in, spring)
    big = cs_union([rect(-R_in, 0.0, R_in, spring), circle((0.0, spring), R_in, 64) ^ rect(-R_in, spring, R_in, spring + R_in + 1)])
    parts.append(ext(big - light, 0.0, 0.6))                                       # the tympanum and the colonnette
    parts.append(ext(rect(-gap / 2 + 0.05, 0.0, gap / 2 - 0.05, spring - 0.4), 0.0, 1.0))
    parts.append(chamfer_box(-gap / 2 - 0.2, spring - 0.6, gap / 2 + 0.2, spring, 0.0, 1.2, c=0.3))
    parts.append(ext(circle((0.0, spring + R_in * 0.62), min(1.2, R_in - r - 0.9) + 0.6, 28) - ocu, 0.0, 1.0))
    parts = [p - ext(light, -1.0, 5.0) for p in parts]
    outline = outer.offset(-0.4, JoinType.Round) ^ rect(-50, 0.2, 50, 100)
    return dict(light=light, bars=bars, frame=parts, outline=outline, top=top, bottom=bottom)


# ------------------------------------------------------------------ walls, corners, foundation
def brick_flemishstretcher(region, datum=0.0, bl=2.4, bh=0.8, mortar=0.5, bed=0.2, d=0.25):
    """Flemish stretcher bond: a course of headers and stretchers in turn, then three courses
    of stretchers, each half a brick on from the last (the Montclair's cream-city brick)."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    hl = bl / 2
    cells = []
    k = math.floor((v0 - datum) / bh) - 1
    while datum + k * bh < v1:
        v = datum + k * bh
        top = v + bh - bed
        if k % 4 == 0:
            unit = bl + hl
            u = u0 - 2 * unit + ((k // 4) % 2) * unit / 2
            while u < u1 + unit:
                cells.append(rect(u + mortar / 2, v, u + bl - mortar / 2, top))
                cells.append(rect(u + bl + mortar / 2, v, u + unit - mortar / 2, top))
                u += unit
        else:
            u = u0 - 2 * bl + (k % 2) * hl
            while u < u1 + bl:
                cells.append(rect(u + mortar / 2, v, u + bl - mortar / 2, top))
                u += bl
        k += 1
    return M.extrude(cs_union(cells) ^ region, d)


def foundation_reticulated(reg, seed=0):
    """Reticulated brownstone: big blocks in two-course rows, each face sunk in a net of
    irregular cells between raised ribs, inside a smooth margin (the Montclair)."""
    b = reg.bounds()
    rng = np.random.default_rng(seed + 81)
    out = [M.extrude(reg, 0.2)]
    v = b[1] + 0.2
    j = 0
    while v < b[3] - 1.0:
        hh = min(3.6 if j % 2 == 0 else 2.6, b[3] - v - 0.2)
        u = b[0] - (j % 2) * 3.0
        while u < b[2]:
            ww = 6.0
            blk = rect(u + 0.25, v + 0.25, u + ww - 0.25, v + hh - 0.25) ^ reg
            if not blk.is_empty():
                out.append(ext(blk, 0.15, 0.55))
                cells = []
                fld = blk.offset(-0.5, JoinType.Miter, 4.0)
                if not fld.is_empty():
                    fb = fld.bounds()
                    cx = np.arange(fb[0] + 0.6, fb[2], 1.25)
                    cy = np.arange(fb[1] + 0.55, fb[3], 1.1)
                    for iy, y_ in enumerate(cy):
                        for x_ in cx:
                            xx = x_ + (0.6 if iy % 2 else 0.0) + rng.uniform(-0.15, 0.15)
                            cells.append(circle((xx, y_ + rng.uniform(-0.1, 0.1)), rng.uniform(0.32, 0.42), 7))
                    out[-1] = out[-1] - ext(cs_union(cells) ^ fld, 0.35, 0.8)
            u += ww
        v += hh
        j += 1
    return union(out)


def chimney_montclair(w=10.0, d=13.0, h=24.0):
    """The Montclair's stacks: cream brick on a brownstone plinth, a sunk panel with a raised
    diamond on each face, a corbelled cap of three courses under a stone coping, two
    octagonal pots."""
    h = round(h / 0.2) * 0.2
    sh = h - 4.0
    body = box([-w / 2 - 0.6, -d / 2 - 0.6, 0.0], [w / 2 + 0.6, d / 2 + 0.6, 2.4]) + \
        M.hull_points([(x, y, 2.4 - 0.01) for x in (-w / 2 - 0.6, w / 2 + 0.6) for y in (-d / 2 - 0.6, d / 2 + 0.6)] +
                      [(x, y, 3.0) for x in (-w / 2, w / 2) for y in (-d / 2, d / 2)])
    body = body + box([-w / 2, -d / 2, 0.0], [w / 2, d / 2, sh])
    for k in range(3):
        g = 0.3 * (k + 1)
        body = body + box([-w / 2 - g, -d / 2 - g, sh + 0.6 * k - 0.01], [w / 2 + g, d / 2 + g, sh + 0.6 * (k + 1)])
    zc = sh + 1.8
    body = body + box([-w / 2 - 1.3, -d / 2 - 1.3, zc - 0.01], [w / 2 + 1.3, d / 2 + 1.3, zc + 0.8])
    pots = []
    for sy in (-1, 1):
        pot = M.cylinder(2.6, 1.2, 1.0, 8).translate([0, sy * d / 4, zc + 0.79])
        pots.append(pot + M.cylinder(0.5, 1.35, 1.35, 8).translate([0, sy * d / 4, zc + 0.79 + 2.6 - 0.5]))
    body = body + union(pots) - union([M.cylinder(8.0, 0.6, 0.6, 12).translate([0, sy * d / 4, zc - 3.0]) for sy in (-1, 1)])
    pan_z0, pan_z1 = 4.4, sh - 1.4
    cuts, adds = [], []
    for axis, L_, D_ in ((0, w, d), (1, d, w)):
        pw_ = L_ - 3.0
        panel = rect(-pw_ / 2, pan_z0, pw_ / 2, pan_z1)
        dia = poly([(0.0, (pan_z0 + pan_z1) / 2 - min(3.4, (pan_z1 - pan_z0) / 2 - 1.0)), (pw_ / 2 - 1.0, (pan_z0 + pan_z1) / 2),
                    (0.0, (pan_z0 + pan_z1) / 2 + min(3.4, (pan_z1 - pan_z0) / 2 - 1.0)), (-pw_ / 2 + 1.0, (pan_z0 + pan_z1) / 2)])
        for sg in (-1, 1):
            T = np.array([[1.0, 0, 0, 0], [0, 0, sg * 1.0, sg * D_ / 2], [0, 1.0, 0, 0]]) if axis == 0 else \
                np.array([[0, 0, sg * 1.0, sg * D_ / 2], [1.0, 0, 0, 0], [0, 1.0, 0, 0]])
            cuts.append(ext(panel, -0.5, 1.0).transform(T) if sg > 0 else ext(panel, -1.0, 0.5).transform(T))
            adds.append(ext(dia, -0.5, 0.0).transform(T) if sg > 0 else ext(dia, 0.0, 0.5).transform(T))
    return body - union(cuts) + union(adds)


# ------------------------------------------------------------------ cresting
def fence_montclair(L, h):
    """Montclair cresting: pairs of C-scrolls back to back, a spear rising between each pair,
    a ball on the rail between the pairs, on a bottom rail."""
    pitch = 3.2
    n = max(1, int(round(L / pitch)))
    p = L / n
    cells = [rect(0.0, 0.0, L, 0.6), rect(0.0, h * 0.42, L, h * 0.42 + 0.45)]
    for j in range(n + 1):
        u = p * j
        cells.append(rect(u - 0.3, 0.0, u + 0.3, h - 0.9))
        cells.append(poly([(u - 0.55, h - 1.0), (u + 0.55, h - 1.0), (u, h)]))
        if j < n:
            m = u + p / 2
            rr = min(0.8, p / 4 - 0.15)
            for sg in (-1, 1):                     # a C-scroll each side, open away from the middle
                c = (m + sg * (rr - 0.1), h * 0.42 + 0.45 + rr - 0.3)
                gap = rect(min(c[0], c[0] + sg * 5), c[1] - rr * 0.45, max(c[0], c[0] + sg * 5), c[1] + rr * 0.45)
                cells.append((circle(c, rr, 20) - circle(c, max(rr - 0.5, 0.15), 16)) - gap)
            cells.append(circle((m, h * 0.42 - 0.35), 0.45, 14))
            cells.append(rect(m - 0.25, 0.5, m + 0.25, h * 0.42))
    return cs_union(cells) ^ rect(0.0, 0.0, L, h + 1.0)


# ------------------------------------------------------------------ windows and doors
def window_montclair_lower(w=10.0, h=22.0, A=1.2):
    """Montclair ground floor: a round-headed two-over-two sash in a tabernacle frame: half-round
    colonnettes on plinths either side, a frieze with a rosette over carved spandrels, a
    cornice and a triangular pediment; a sill over an apron carved with a swag."""
    r = w / 2
    spring = h - r
    op = O.opening_cs(w, h, r)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    sash = O.window_insert(w, h, r, lites=(2, 2), bare=True)["insert"]
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS),
             MD.band(op.offset(A, JoinType.Round), A, MD.ARCHITRAVE, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op)]
    cr = 1.0
    ucs = r + A + cr + 0.1
    v_ent = h + A + 0.4
    for sg in (-1, 1):
        u = sg * ucs
        shaft = M.cylinder(v_ent - 2.6, cr, cr * 0.9, 28).rotate([-90, 0, 0]).translate([u, 1.8, 0.0])
        parts.append(shaft ^ box([u - 2, 0.0, 0.0], [u + 2, v_ent, 3.0]))
        parts.append(chamfer_box(u - cr - 0.35, 0.0, u + cr + 0.35, 1.8, 0.0, 1.5, c=0.4))
        parts.append(chamfer_box(u - cr - 0.3, v_ent - 0.81, u + cr + 0.3, v_ent, 0.0, 1.5, c=0.35))
    half = ucs + cr + 0.4
    span = (rect(-half + 0.2, spring, half - 0.2, v_ent) - op.offset(A, JoinType.Round))
    parts.append(ext(span, 0.0, 0.6))
    for sg in (-1, 1):
        parts.append(ext(circle((sg * (r + A * 0.4), v_ent - 1.0), 0.75, 16), 0.59, 1.0))
    parts.append(ext(rect(-half, v_ent - 0.01, half, v_ent + 2.2), 0.0, 0.7))
    parts.append(MD.rosette(0.0, v_ent + 1.1, 0.8, 0.69, 0.6))
    for sg in (-1, 1):
        parts.append(ext(_lens((sg * 2.6, v_ent + 1.1), 2.6, 0.9, 0.0), 0.69, 1.0))
    vc = v_ent + 2.0 + 1.2
    parts.append(MD.run(-half - 0.6, half + 0.6, vc, MD.CROWN, 1.2, up=False))
    hp = (half + 0.6) * 0.32
    tri = poly([(-half - 0.6, vc - 0.4), (half + 0.6, vc - 0.4), (0.0, vc + hp)])
    inner = tri.offset(-1.1, JoinType.Miter, 4.0)
    parts.append(ext(tri - inner, 0.0, 1.2))
    parts.append(ext(inner, 0.0, 0.5))
    parts.append(ext(oval((0.0, vc + hp * 0.32), 1.2, 0.75, 24), 0.49, 0.95))
    sw = half + 0.2
    parts.append(MD.run(-sw, sw, 0.0, MD.SILL, 1.0, up=False))
    aw = r + A
    parts.append(ext(rect(-aw, -3.6, aw, -0.99), 0.0, 0.55))
    parts.append(ext(swag(-aw + 1.2, aw - 1.2, -1.4, 1.4, width=0.6), 0.54, 0.95))
    for sg in (-1, 1):
        parts.append(ext(circle((sg * (aw - 1.0), -1.6), 0.45, 12), 0.54, 1.0))
    return O._one_piece([sash], parts, op, plug_cs, O.PLUG, vc + hp, -3.6)


def window_montclair_upper(w=9.6, h=21.0, rise=1.8, A=1.0):
    """Montclair upper floor: a segmental-headed two-over-two sash in an eared architrave, a
    hood mould following the head stopped on drop pendants, a fleuron on its crown, and a sill
    on two small consoles."""
    op = O.opening_cs(w, h, rise)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    sash = O.window_insert(w, h, rise, lites=(2, 2), bare=True)["insert"]
    spring = h - rise
    outer = op.offset(A, JoinType.Miter, 4.0)
    ears = cs_union([rect(-w / 2 - A - 0.7, spring - 2.0, -w / 2, spring + 0.6), rect(w / 2, spring - 2.0, w / 2 + A + 0.7, spring + 0.6)])
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS),
             MD.band(cs_union([outer, ears]), A + 0.7, MD.ARCHITRAVE, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op)]
    HB = 1.2
    hood_out = op.offset(A + HB + 0.2, JoinType.Miter, 4.0)
    parts.append(MD.band(hood_out, HB, MD.CROWN, clip=rect(-w - 10, spring + 0.6, w + 10, h + 40)))
    for sg in (-1, 1):
        u = sg * (w / 2 + A + 0.2 + HB / 2)
        parts.append(chamfer_box(u - 0.8, spring - 0.2, u + 0.8, spring + 0.6, 0.0, 1.4, c=0.3))
        parts.append(MD.pendant(u, spring - 0.2, 2.4, 0.0, 0.9))
    vt = h + A + HB + 0.2
    leaf = cs_union([_lens((0.0, vt + 1.2), 2.4, 1.0, math.pi / 2)] + [_lens((sg * 0.9, vt + 0.7), 1.8, 0.7, math.pi / 2 - sg * 0.7) for sg in (-1, 1)])
    parts.append(ext(leaf + rect(-1.2, vt - 0.3, 1.2, vt + 0.3), 0.0, 1.1))
    sw = w / 2 + A + 0.8
    parts.append(MD.run(-sw, sw, 0.0, MD.SILL, 1.0, up=False))
    for sg in (-1, 1):
        parts.append(console(1.8, 1.0, 0.8, u=sg * (w / 2 + A / 2), v_top=-0.8, w0=0.0))
    return O._one_piece([sash], parts, op, plug_cs, O.PLUG, vt + 2.4, -2.8)


def _leaf_montclair(u0, lw, dh, pl):
    """A Montclair door leaf: a tall round-headed light with an oval etched centre over a
    raised panel with a round boss, in its plug frame."""
    body = [ext(rect(u0, 0.5, u0 + lw, dh), -pl, -0.8)]
    gw = lw - 1.6
    gv0 = dh * 0.42
    light = cs_union([rect(u0 + 0.8, gv0, u0 + 0.8 + gw, dh - 0.8 - gw / 2), circle((u0 + lw / 2, dh - 0.8 - gw / 2), gw / 2, 24)])
    body.append(_panel(rect(u0 + 0.8, 1.2, u0 + lw - 0.8, gv0 - 0.8)))
    body.append(ext(circle((u0 + lw / 2, (1.2 + gv0 - 0.8) / 2), 0.7, 16), -0.4, 0.0))
    bars = (oval((u0 + lw / 2, (gv0 + dh - 0.8) / 2), gw / 2 - 0.2, gw * 0.6, 24) - oval((u0 + lw / 2, (gv0 + dh - 0.8) / 2), gw / 2 - 0.7, gw * 0.6 - 0.5, 24))
    return body, light, bars


def door_montclair(w=14.0, h=27.0, A=1.2):
    """The Montclair's entrance: a pair of leaves (round-headed lights, raised panels) under a
    fanlight of radiating bars and one ring (a spider-web), in a round-arched doorway with
    voussoirs and a big carved keystone, between banded pilasters carrying an entablature on
    two consoles, a cartouche on its cornice."""
    r = w / 2
    spring = h - r
    op = O.opening_cs(w, h, r)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    mid = 0.5
    lw = (w - 2 * O.CLR - 1.0 - mid) / 2
    dh = spring - 0.4
    body, lights, bars = [ext(plug_cs, -pl, -1.0)], [], []
    u = -w / 2 + O.CLR + 0.5
    for i in range(2):
        b_, lt, br = _leaf_montclair(u, lw, dh, pl)
        body += b_
        lights.append(lt)
        bars.append(br)
        u += lw + mid
    fan = plug_cs.offset(-0.5, JoinType.Miter, 4.0) ^ rect(-w, spring + 0.2, w, h + 2)
    rays = cs_union([stroke([(0.0, spring + 0.2), (r * 1.2 * math.cos(a), spring + 0.2 + r * 1.2 * math.sin(a))], 0.5)
                     for a in np.linspace(0.35, math.pi - 0.35, 5)] +
                    [circle((0.0, spring + 0.2), r * 0.55, 40) - circle((0.0, spring + 0.2), r * 0.55 - 0.5, 40),
                     circle((0.0, spring + 0.2), 1.2, 20)])
    g = cs_union(lights) + fan
    sash = _glazed(body, g, pl, cs_union(bars) + rays, plug_cs)
    sash.append(ext(rect(-w, dh - 0.01, w, spring + 0.2) ^ plug_cs, -pl, -0.5))
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS),
             MD.band(op.offset(A, JoinType.Round), A, MD.ARCHITRAVE, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op)]
    # voussoirs round the arch, a carved keystone
    Rv0, Rv1 = r + A - 0.1, r + A + 1.9
    for a in np.linspace(math.radians(12), math.radians(168), 9):
        if abs(a - math.pi / 2) < 0.15:
            continue
        da = math.radians(7.5)
        pts = [(Rv0 * math.cos(a - da), spring + Rv0 * math.sin(a - da)), (Rv1 * math.cos(a - da), spring + Rv1 * math.sin(a - da)),
               (Rv1 * math.cos(a + da), spring + Rv1 * math.sin(a + da)), (Rv0 * math.cos(a + da), spring + Rv0 * math.sin(a + da))]
        parts.append(ext(poly(pts), 0.0, 0.9))
    parts.append(MD.scroll_keystone(0.0, h - 0.2, Rv1 - r + 1.4, 2.0, 2.6, 0.0, 2.0))
    # banded pilasters, an entablature on consoles, a cartouche on the cornice
    pw = 2.4
    ui = Rv1 + 0.3
    vcap = spring + Rv1 + 0.4
    for sg in (-1, 1):
        u0, u1 = sorted((sg * ui, sg * (ui + pw)))
        parts.append(chamfer_box(u0 - 0.3, 0.0, u1 + 0.3, 2.8, 0.0, 1.5, c=0.4))
        parts.append(ext(rect(u0, 2.7, u1, vcap - 0.9), 0.0, 0.7))
        for vb in np.arange(2.8, vcap - 1.0, 2.4):
            parts.append(chamfer_box(u0, vb + 0.15, u1, min(vb + 2.25, vcap - 1.0), 0.0, 1.1, c=0.3))
        parts.append(MD.run(u0 - 0.3, u1 + 0.3, vcap, MD.CROWN, 1.0, up=False))
    half = ui + pw + 0.3
    parts.append(ext(rect(-half, spring, half, vcap) - op.offset(A, JoinType.Round), 0.0, 0.6))
    parts.append(ext(rect(-half, vcap - 0.01, half, vcap + 2.2), 0.0, 0.7))
    for sg in (-1, 1):
        parts.append(console(3.4, 1.8, 1.4, u=sg * (ui + pw / 2), v_top=vcap + 2.2, w0=0.0))
        parts.append(MD.rosette(sg * (r * 0.62), vcap + 1.1, 0.7, 0.69, 0.6))
    vs = vcap + 2.0 + 1.4
    parts.append(MD.run(-half - 0.8, half + 0.8, vs, MD.CROWN, 1.4, up=False))
    parts.append(ext(rect(-3.0, vs - 0.01, 3.0, vs + 0.6), 0.0, 1.2))
    parts.append(ext(oval((0.0, vs + 1.6), 2.9, 1.5, 32), 0.0, 0.5))           # the scrolls' backing
    parts.append(MD.cartouche((0.0, vs + 1.7), 3.2, 2.4, 0.0, 1.2))
    return O._one_piece(sash, parts, op, plug_cs, pl, vs + 3.1, 0.0)


def door_montclair_back(w=10.4, h=26.0, A=1.0):
    """The Montclair's back door: one leaf of four raised panels under a three-light transom,
    an eared architrave and a cornice hood on two consoles."""
    transom = 4.0
    H = h
    op = rect(-w / 2, 0.0, w / 2, H)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    dh = H - transom
    u0, u1 = -w / 2 + O.CLR + 0.3, w / 2 - O.CLR - 0.3
    body = [ext(plug_cs, -pl, -1.0), ext(rect(u0, 0.5, u1, dh - 0.3), -1.0, -0.8)]
    cw = (u1 - u0 - 1.8) / 2
    for c in range(2):
        pa = u0 + 0.6 + c * (cw + 0.6)
        for vb, vt in ((1.0, dh * 0.45), (dh * 0.45 + 0.8, dh - 1.1)):
            body.append(_panel(rect(pa, vb, pa + cw, vt)))
    g = plug_cs.offset(-0.5, JoinType.Miter, 4.0) ^ rect(-w, dh + 0.3, w, H + 2)
    sash = _glazed(body, g, pl, _muntins(g, 3, 1), plug_cs)
    sash.append(ext(rect(-w, dh - 0.3, w, dh + 0.3) ^ plug_cs, -pl, -0.4))
    outer = op.offset(A, JoinType.Miter, 4.0)
    ears = cs_union([rect(-w / 2 - A - 0.7, H - 2.0, -w / 2, H + A), rect(w / 2, H - 2.0, w / 2 + A + 0.7, H + A)])
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS),
             MD.band(cs_union([outer, ears]), A + 0.7, MD.ARCHITRAVE, clip=rect(-w - 10, 0.0, w + 10, H + 40) - op)]
    half = w / 2 + A + 0.7
    vf = H + A
    parts.append(ext(rect(-half, vf - 0.01, half, vf + 1.8), 0.0, 0.6))
    for sg in (-1, 1):
        parts.append(console(2.8, 1.4, 1.1, u=sg * (half - 0.6), v_top=vf + 1.8, w0=0.0))
    parts.append(MD.run(-half - 0.6, half + 0.6, vf + 1.8 + 1.2, MD.CROWN, 1.2, up=False))
    return O._one_piece(sash, parts, op, plug_cs, pl, vf + 3.0, 0.0)


# ------------------------------------------------------------------ porch
def post_gibbs(h, collar=None, abacus=3.0, slot=(1.2, 1.0)):
    """A Gibbs column: a round shaft broken by three square blocks with chamfered edges, on a
    plinth and a torus, under a moulded capital (the Montclair's veranda)."""
    z1 = h - 2.6
    r = 1.05
    prof = [(0.0, 1.19), (1.55, 1.19), (1.55, 1.45), (1.3, 1.7), (r, 1.95), (r, z1), (1.25, z1 + 0.2), (1.25, z1 + 0.45),
            (r * 0.95, z1 + 0.65)]
    body = PW._revolve(prof, 32) + PW._plinth(3.1)
    for f in (0.28, 0.5, 0.72):
        zc = round((1.95 + (z1 - 1.95) * f) / 0.2) * 0.2
        s = 1.2
        blk = M.hull_points([(x, y, zc - 0.7) for x in (-s + 0.3, s - 0.3) for y in (-s + 0.3, s - 0.3)] +
                            [(x, y, zc - 0.4) for x in (-s, s) for y in (-s, s)] + [(x, y, zc + 0.4) for x in (-s, s) for y in (-s, s)] +
                            [(x, y, zc + 0.7) for x in (-s + 0.3, s - 0.3) for y in (-s + 0.3, s - 0.3)])
        body = body + blk
    return body + PW._top(h, abacus / 2, z1 + 0.65, r * 0.95, slot, seg=32)


def baluster_pear(h, seg=20):
    """A pear baluster: a long body swelling low and drawing up to a ringed neck, square ends
    (the Montclair)."""
    prof = [(0.0, 0.8), (0.32, 0.8), (0.5, 1.4), (0.58, h * 0.32), (0.44, h * 0.55), (0.28, h - 2.0), (0.28, h - 1.6),
            (0.45, h - 1.4), (0.45, h - 1.15), (0.3, h - 1.0), (0.3, h - 0.8)]
    return PW._revolve(prof, seg) + box([-0.55, -0.55, 0.0], [0.55, 0.55, 0.81]) + box([-0.55, -0.55, h - 0.81], [0.55, 0.55, h])


def frieze_pairbrackets(u0, u1, v_bot, v_top):
    """A porch frieze: a board with pairs of small scroll brackets under the cornice, a sunk
    panel between each pair (the Montclair)."""
    v0 = v_top - 2.8
    board = rect(u0, v0, u1, v_top + 0.05)
    n = max(2, int((u1 - u0) / 5.0))
    out = [board]
    sunk = []
    for j in range(n + 1):
        x = u0 + 0.9 + (u1 - u0 - 1.8) * j / n
        for sg in (-1, 1):
            xx = x + sg * 0.55
            out.append(poly([(xx - 0.3, v0 + 0.01), (xx + 0.3, v0 + 0.01), (xx + 0.3, v0 - 0.6), (xx, v0 - 1.4), (xx - 0.3, v0 - 0.6)]))
        if j < n:
            xm = x + (u1 - u0 - 1.8) / n / 2
            hw = (u1 - u0 - 1.8) / n / 2 - 1.6
            if hw > 0.6:
                sunk.append(rect(xm - hw, v0 + 0.7, xm + hw, v_top - 0.7))
    cs = cs_union(out)
    return cs - cs_union(sunk) if sunk else cs


def skirt_crossvent(reg, d=1.2):
    """A porch skirt of plain panels, each with a sunk cross-shaped vent and a bead round the
    panel (the Montclair)."""
    u0, v0, u1, v1 = reg.bounds()
    out = M.extrude(reg, d * 0.5)
    if v1 - v0 < 2.4:
        return out
    n = max(1, int((u1 - u0) / 5.0))
    frames, vents = [], []
    for j in range(n):
        a, b_ = u0 + (u1 - u0) * j / n, u0 + (u1 - u0) * (j + 1) / n
        pn = rect(a + 0.5, v0 + 0.4, b_ - 0.5, v1 - 0.4)
        frames.append(pn - pn.offset(-0.5, JoinType.Miter, 4.0))
        xm, vm = (a + b_) / 2, (v0 + v1) / 2
        hv = min(1.2, (v1 - v0) / 2 - 0.9)
        vents.append(cs_union([rect(xm - 0.3, vm - hv, xm + 0.3, vm + hv), rect(xm - hv, vm - 0.3, xm + hv, vm + 0.3)]))
    return out + M.extrude(cs_union(frames) ^ reg, d) - M.extrude(cs_union(vents), d * 0.5 + 1).translate([0, 0, 0.25])


def edge_pairconsoles(L, z0, zc):
    """Porch fascia (the Montclair): pairs of little consoles hung under the crown."""
    out = [rect(0.3, zc - 0.45, L - 0.3, zc)]
    n = max(1, int((L - 2.0) / 4.0))
    for k in range(n + 1):
        x = 1.0 + (L - 2.0) * k / n
        for sg in (-1, 1):
            xx = x + sg * 0.5
            out.append(poly([(xx - 0.3, zc - 0.4), (xx + 0.3, zc - 0.4), (xx + 0.3, zc - 1.0), (xx, zc - 1.5), (xx - 0.3, zc - 1.0)]))
    return cs_union(out), 0.6


CO.FRIEZE_EXTRA.update(balustrade=frieze_balustrade, bees=frieze_bees)
CO.COURSE_EXTRA.update(fasciae=course_fasciae, leafdart=course_leafdart)
TW.BRACKET_EXTRA.update(flutedconsole=bracket_flutedconsole)
TW.PIERCED = TW.PIERCED + ("flutedconsole",)
TW.FOUNDATION_EXTRA.update(reticulated=foundation_reticulated)
PW.POSTS.update(gibbs=post_gibbs)
PW.BALUSTERS.update(pear=(baluster_pear, 1.7))
PW.FRIEZES.update(pairbrackets=frieze_pairbrackets)
PW.SKIRTS.update(crossvent=skirt_crossvent)
FT.EDGE_EXTRA.update(pairconsoles=edge_pairconsoles)

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
from .ornament import bezier, chamfer_box, console, ext, fan_crest, keystone, oval, quatrefoil, stroke, swag, urn_cs
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


def bell_profile(d0, z0, d1, z1, kick=(1.2, 1.2), power=1.6, step=8.0, convex=False):
    """A bell-cast (concave) mansard face: a short kick at the foot, then a curve leaning back
    fast low down and slower toward the top (``convex``: the other way, a swelling face that
    stands steep low down and leans back more toward its top), from (d0, z0) to (d1, z1), as
    straight facets
    ``step`` long up the slope (a whole even number of slate courses, so the courses run on
    unbroken from facet to facet); the last facet takes what is left."""
    da, za = d0 - kick[0], z0 + kick[1]
    s = np.linspace(0.0, 1.0, 801)
    d = da + (d1 - da) * (s ** power if convex else 1 - (1 - s) ** power)     # convex: steep low, leaning back high up
    z = za + (z1 - za) * s
    run = np.r_[0.0, np.cumsum(np.hypot(np.diff(d), np.diff(z)))]
    pts = [(d0, z0), (da, za)]
    target = step
    for i in range(1, len(s)):
        if run[i] >= target and run[-1] - run[i] > step * 0.5:
            pts.append((float(d[i]), float(z[i])))
            target += step
    pts.append((d1, z1))
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


def crest_ring(path, d_s, z_s, t_s, course, crown, deck_th=1.2, s_out=-0.6, key=(1.2, 2.0, 1.0)):
    """The crest on a mansard band's flat top (its outer edge ``d_s`` off the wall plane ``path``,
    ``t_s`` thick, at z_s): one part, printed upside down: a course ring sitting on the band top,
    dict(h, b, orn (a cs generator), role), and a crown over it, dict(h, P, kind, role,
    blocks=(w, pitch) or None), widening to P with a 45 degree seat inside for the deck. Under
    it a key (``key`` = from, to inside the band's outer edge, depth) drops into a groove in
    the band top to locate it, whatever the band's thickness (``groove``: cut it from the band).
    Its inside steps in at 45 degrees from the seat to its foot, so nothing in print is a
    ledge over air. Returns dict(solid, zones, change, z_top, deck, path, P, groove, rail):
    ``rail`` is where cresting strips stand (their offset), clear of a concave crown's lip."""
    top = R.offset_path(path, d_s)
    hA, hB = course["h"], crown["h"]
    H = hA + hB
    b, P = course["b"], crown["P"]
    k0, k1, kd = key
    assert t_s >= k1 + 0.4, ("band too thin for the crest's key", t_s)
    d_foot = s_out - deck_th - (H - deck_th)            # where the 45 degree inside meets the band top
    cpro = CO.crown_profile(crown["kind"], b, P, hB)
    prof = [(-k1, -kd), (-k0, -kd), (-k0, 0.0), (b, 0.0), (b, hA)] + [(d, hA + z) for d, z in cpro[1:]] + \
           [(P, H), (s_out, H), (s_out - deck_th, H - deck_th), (min(d_foot, -k1), 0.0), (-k1, 0.0)]
    ring = sweep_ring(top, [(d, z_s + z) for d, z in prof])
    groove = sweep_ring(top, [(d, z_s + z) for d, z in [(-k1 - FCLR, -kd - 0.2), (-k0 + FCLR, -kd - 0.2), (-k0 + FCLR, 0.5),
                                                         (-k1 - FCLR, 0.5)]])
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
    # where cresting may stand: its 0.6 key slot must lie over solid crown, or under a concave
    # crown (a cove, a torus) it cuts the crown's top lip free
    zq = hB - 0.8
    dq = max(d0 + (d1 - d0) * (zq - z0) / (z1 - z0) for (d0, z0), (d1, z1) in zip(cpro[:-1], cpro[1:])
             if min(z0, z1) <= zq <= max(z0, z1) and z1 != z0)
    rail = min(P - 1.4, dq - 0.95)
    return dict(solid=solid, zones=zones, change=change, z_top=z_s + H, deck=deck, path=top, P=P, groove=groove, rail=rail)


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


def printable(fence, s=2.0):
    """A cresting fence drawn at 1/s and enlarged s times, so its bars, rails and ornaments
    come out at least 0.9 mm wide (two lines of a 0.4 mm nozzle) and its openings stay open:
    drawn at full size they were 0.4-0.6 mm wide and did not print. Call it with the finished
    height (s times the old one)."""
    def f(L, h):
        return fence(L / s, h / s).scale((s, s))
    return f


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
            cuts.append(ext(panel, -0.5, 1.0).transform(T))       # w < 0 is inside the stack on every face
            adds.append(ext(dia, -0.6, 0.0).transform(T))         # the diamond runs into the panel's floor
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


# ================================================================== the Lafayette (house 82)
# A Second Empire house of sage clapboard with ivory trim and plum accents: a corner pavilion
# whose taller bell-cast mansard rises through the main roof, trefoil-cut purple slate, oval and
# segmental add-ins, a veranda round the front and the east side.

# ------------------------------------------------------------------ cornice ornaments
def frieze_cockades(L, h, b, pitch, margin, pair, half):
    """Cockades: in every bay a pleated round rosette (a ring of radial pleats round a boss)
    with two ribbon tails hanging from it, a small bow knot at each station (the Lafayette's
    storey joint)."""
    v0, v1 = 0.8, h - 0.8
    hh = v1 - v0
    out = []
    for uc, wd in CO._between(L, pitch, margin, pair, half):
        if wd < 3.6:
            continue
        r = min(hh * 0.36, wd / 2 - 0.6, 1.7)
        vc = v1 - r - 0.1
        out.append(_st(circle((uc, vc), r, 32), b, 0.35))
        pleats = cs_union([stroke([(uc + (r * 0.4) * math.cos(a), vc + (r * 0.4) * math.sin(a)),
                                   (uc + (r - 0.15) * math.cos(a), vc + (r - 0.15) * math.sin(a))], 0.42)
                           for a in np.linspace(0, 2 * math.pi, 12, endpoint=False)])
        out.append(_st(pleats, b + 0.35, 0.25))
        out.append(_st(circle((uc, vc), r * 0.36, 16), b + 0.35, 0.4))
        for sg in (-1, 1):
            tail = poly([(uc + sg * 0.15, vc - r * 0.6), (uc + sg * 0.75, vc - r * 0.5), (uc + sg * 1.3, v0 + 0.1),
                         (uc + sg * 0.85, v0 + 0.55), (uc + sg * 0.6, v0 + 0.1)])
            out.append(_st(tail, b, 0.35))
    for u in CO._us(L, pitch, margin, 0.0):
        vm = (v0 + v1) / 2
        bow = cs_union([_lens((u - 0.65, vm), 1.3, 0.75, 0.25), _lens((u + 0.65, vm), 1.3, 0.75, -0.25), circle((u, vm), 0.38, 12)])
        out.append(_st(bow, b, 0.4))
    return out, []


def frieze_candelabra(L, h, b, pitch, margin, pair, half):
    """Candelabra: in every bay a Renaissance candelabrum standing on the foot (a footed base,
    a vase, a stem with two scrolled branches and a flame), sunk panels either side (the
    Lafayette's eave)."""
    v0, v1 = 0.8, h - 0.8
    hh = v1 - v0
    out, cuts = [], []
    for uc, wd in CO._between(L, pitch, margin, pair, half):
        if wd < 4.0:
            continue
        s = hh / 5.0
        c = [rect(uc - 0.8 * s, v0, uc + 0.8 * s, v0 + 0.35 * s),
             poly([(uc - 0.3 * s, v0 + 0.35 * s), (uc + 0.3 * s, v0 + 0.35 * s), (uc + 0.75 * s, v0 + 1.4 * s), (uc + 0.45 * s, v0 + 1.9 * s),
                   (uc - 0.45 * s, v0 + 1.9 * s), (uc - 0.75 * s, v0 + 1.4 * s)]),
             rect(uc - 0.22, v0 + 1.9 * s, uc + 0.22, v0 + 3.9 * s),
             oval((uc, v0 + 2.6 * s), 0.38 * s, 0.22 * s, 14),
             _lens((uc, v0 + 4.45 * s), 1.1 * s, 0.55 * s, math.pi / 2)]
        for sg in (-1, 1):
            arc = [(uc + sg * 1.05 * s * math.sin(t), v0 + 2.9 * s + 0.9 * s * (1 - math.cos(t))) for t in np.linspace(0.0, math.pi * 0.8, 10)]
            c.append(stroke([(uc, v0 + 2.9 * s)] + arc[1:], 0.4))
            c.append(circle(arc[-1], 0.32, 10))
        out.append(_st(cs_union(c), b, 0.45))
        pw = wd / 2 - 1.6 * s - 0.8
        if pw > 1.0:
            for sg in (-1, 1):
                x0 = uc + sg * (1.6 * s + 0.4)
                pan = rect(min(x0, x0 + sg * pw), v0 + 0.5, max(x0, x0 + sg * pw), v1 - 0.5)
                cuts.append(ext(pan.offset(-0.35, JoinType.Miter, 4.0), b - 0.25, b + 1.0))
                out.append(_st(pan - pan.offset(-0.35, JoinType.Miter, 4.0), b, 0.3))
    return out, cuts


def course_ribbonstick(L, h, b, pitch, margin, p):
    """Ribbon and stick: a round rod with a ribbon wound round it in slanting bands (the
    Lafayette)."""
    out = [_st(rect(0.2, h * 0.2, L - 0.2, h * 0.8), b, 0.35)]
    sp = max(1.4, h * 1.1)
    n = max(1, int((L - 0.8) / sp))
    u0 = (L - n * sp) / 2
    bands = [poly([(u0 + k * sp, 0.15), (u0 + k * sp + 0.6, 0.15), (u0 + k * sp + 0.6 + h * 0.55, h - 0.15),
                   (u0 + k * sp + h * 0.55, h - 0.15)]) for k in range(n)]
    out.append(_st(cs_union(bands) ^ rect(0.2, 0.0, L - 0.2, h), b + 0.3, 0.3))
    return out


def course_beaddentil(L, h, b, pitch, margin, p):
    """Dentils hanging from a fillet, a round bead dropped in every gap (the Lafayette)."""
    tooth, gap = 0.9, 0.7
    n = int((L - 1.2) / (tooth + gap))
    u0 = (L - (n * (tooth + gap) - gap)) / 2
    out = [ext(rect(0.2, h - 0.5, L - 0.2, h), b - 0.05, b + 0.45)]
    for k in range(n):
        u = u0 + k * (tooth + gap)
        out.append(ext(rect(u, 0.5, u + tooth, h - 0.45), b - 0.05, b + 0.75))
        if k < n - 1:
            out.append(_st(circle((u + tooth + gap / 2, 0.75), 0.42, 12), b, 0.45))
    return out


def course_lambstongue(L, h, b, pitch, margin, p):
    """Lamb's tongues: round-ended tongues hanging from a fillet, close set (the Lafayette's
    storey joint)."""
    pu = 1.3
    n = max(1, int((L - 0.8) / pu))
    u0 = (L - n * pu) / 2
    tongues = [rect(0.2, h - 0.45, L - 0.2, h)]
    for k in range(n):
        uc = u0 + pu * (k + 0.5)
        tongues += [rect(uc - 0.4, 0.6, uc + 0.4, h - 0.3), circle((uc, 0.6), 0.4, 12)]
    return [_st(cs_union(tongues), b, 0.45)]


def ribbonbands(L, h):
    """The Lafayette's crest course as CrossSections: slanting ribbon bands over a rod."""
    sp = max(1.6, h * 1.0)
    n = max(1, int((L - 0.8) / sp))
    u0 = (L - n * sp) / 2
    rod = rect(0.2, h * 0.22, L - 0.2, h * 0.78)
    bands = [poly([(u0 + k * sp, 0.1), (u0 + k * sp + 0.6, 0.1), (u0 + k * sp + 0.6 + h * 0.5, h - 0.1),
                   (u0 + k * sp + h * 0.5, h - 0.1)]) for k in range(n)]
    return [rod + (cs_union(bands) ^ rect(0.2, 0.0, L - 0.2, h))]


def bracket_leafmod(h, d, t):
    """A modillion with a leaf under it: a long horizontal block, its front end rolled into a
    scroll and its back into a smaller one, the underside between them cut in the lobes of an
    acanthus leaf (side profile, top at v = 0; the Lafayette)."""
    r1 = min(0.45 * h, 0.22 * d)
    r2 = min(0.32 * h, 0.15 * d)
    body = rect(0.0, -h * 0.55, d, 0.0)
    lobes = cs_union([circle((d * f, -h * 0.55), h * 0.2, 12) for f in np.linspace(0.3, 0.72, 4)])
    prof = cs_union([body, lobes, circle((d - r1, -h + r1), r1, 18), circle((0.15 + r2, -h + r2 + 0.2), r2, 14),
                     rect(d - 2 * r1, -h + r1, d, 0.0), rect(0.0, -h + r2 + 0.2, 0.3 + 2 * r2, 0.0)])
    return prof - circle((d - r1, -h + r1), r1 * 0.4, 12)


# ------------------------------------------------------------------ the mansard's window add-ins
def addin_lafayette_oval(rx=2.6, ry=3.4):
    """A Lafayette add-in: an oval light (oeil-de-boeuf) with a cross of bars in an oval frame
    keyed at its four points, a scrolled crest with a fan over it, and a corbel under it."""
    vc = ry + 2.2
    light = oval((0.0, vc), rx, ry, 40)
    bars = cs_union([rect(-RIB / 2, vc - ry - 1, RIB / 2, vc + ry + 1), rect(-rx - 1, vc - 0.25, rx + 1, vc + 0.25)])
    A = 1.3
    outer = oval((0.0, vc), rx + A, ry + A, 48)
    parts = [ext(outer.offset(0.6, JoinType.Round) - light, 0.0, 0.6),
             MD.band(light.offset(A, JoinType.Round), A, MD.ARCHITRAVE, clip=rect(-20, -20, 20, 40) - light)]
    for ang in (0.0, math.pi / 2, math.pi, 3 * math.pi / 2):
        cx, cy = (rx + A * 0.5) * math.cos(ang), vc + (ry + A * 0.5) * math.sin(ang)
        key = rect(-0.55, -(A * 0.5 + 0.5), 0.55, A * 0.5 + 0.5)
        if abs(math.cos(ang)) > 0.5:
            key = rect(-(A * 0.5 + 0.5), -0.55, A * 0.5 + 0.5, 0.55)
        parts.append(ext(key.translate([cx, cy]), 0.0, 1.5))
    vt = vc + ry + A + 0.2
    crest = [rect(-2.6, vt - 0.6, 2.6, vt + 0.3)]
    for sg in (-1, 1):
        crest.append(stroke([(sg * 0.6, vt), (sg * 1.8, vt + 0.9), (sg * 2.6, vt + 0.4), (sg * 2.4, vt - 0.2)], 0.5))
    parts.append(ext(cs_union(crest), 0.0, 1.0))
    parts.append(fan_crest(0.0, vt + 0.2, 1.7, 0.0, 1.1, rays=3))
    parts.append(chamfer_box(-2.2, 0.0, 2.2, vc - ry - A + 0.4, 0.0, 1.2, c=0.3))
    parts.append(MD.pendant(0.0, 0.2, 1.8, 0.0, 0.8))
    parts = [p - ext(light, -1.0, 5.0) for p in parts]
    outline = (oval((0.0, vc), rx + A + 0.2, ry + A + 0.2, 48) + rect(-2.0, 0.6, 2.0, vc)) ^ rect(-50, 0.6, 50, 100)
    return dict(light=light, bars=bars, frame=parts, outline=outline, top=vt + 2.1, bottom=-1.6)


def addin_lafayette_seg(w=5.6, h=10.4, rise=1.4, A=1.0):
    """A Lafayette add-in: a segmental-headed two-over-two light in an eared architrave, a
    segmental pediment over it with a shell in the tympanum, a sill on a corbel block."""
    op = O.opening_cs(w, h, rise)
    spring = h - rise
    bars = cs_union([rect(-RIB / 2, -1.0, RIB / 2, h + 1.0), rect(-w, spring * 0.5 - 0.3, w, spring * 0.5 + 0.3)])
    half = w / 2 + A + 0.7
    outer = cs_union([op.offset(A, JoinType.Miter, 4.0), rect(-half, spring - 2.0, half, spring + 0.6)])
    parts = [ext(outer.offset(0.3) - op, 0.0, 0.6),
             MD.band(outer, A + 0.7, MD.ARCHITRAVE, clip=rect(-20, 0.0, 20, 40) - op)]
    vp = h + A + 0.2
    parts.append(ext(rect(-half, vp - 0.6, half, vp + 0.2), 0.0, 1.0))
    rp = 2.2
    seg = arch_cs(-half - 0.4, half + 0.4, vp - 0.01, vp, rise=rp, seg=48)
    parts.append(MD.band(seg, 1.0, MD.CROWN, clip=rect(-half - 2, vp, half + 2, vp + 10)))
    tymp = seg.offset(-0.9, JoinType.Round) ^ rect(-half, vp, half, vp + 10)
    parts.append(ext(tymp, 0.0, 0.6))
    parts.append(fan_crest(0.0, vp + 0.1, min(1.6, rp - 0.5), 0.59, 0.5, rays=3))
    sw = half + 0.3
    parts.append(MD.run(-sw, sw, 0.0, MD.SILL, 1.0, up=False))
    parts.append(chamfer_box(-1.4, -2.0, 1.4, -0.8, 0.0, 1.0, c=0.3))
    parts = [p - ext(op, -1.0, 5.0) for p in parts]
    outline = (cs_union([rect(-half - 0.1, 0.4, half + 0.1, vp)]) + (seg.offset(-0.6, JoinType.Round) ^ rect(-20, vp - 1, 20, 40)))
    outline = outline.offset(-0.4, JoinType.Round) ^ rect(-50, 0.4, 50, 100)
    return dict(light=op, bars=bars, frame=parts, outline=outline, top=vp + rp, bottom=-2.0)


# ------------------------------------------------------------------ walls, corners, foundation
def jointed_clapboard(region, datum=0.0, pitch=1.2, d=0.32, seed=82):
    """Bevel clapboard laid in board lengths: every course broken by butt joints, staggered
    from course to course (the Lafayette)."""
    from .core import clapboard
    if region.is_empty():
        return M()
    lap = clapboard(region, pitch=pitch, d=d, dmin=0.05, datum=datum)
    u0, v0, u1, v1 = region.bounds()
    rng = np.random.default_rng(seed + int(u1 * 10) % 97)
    cuts = []
    k = math.floor((v0 - datum) / pitch) - 1
    while datum + k * pitch < v1:
        v = datum + k * pitch
        u = u0 + rng.uniform(1.0, 9.0)
        while u < u1 - 1.0:
            cuts.append(rect(u - 0.2, v + 0.05, u + 0.2, v + pitch - 0.05))
            u += rng.uniform(9.0, 15.0)
        k += 1
    return lap - ext(cs_union(cuts), 0.12, d + 0.5) if cuts else lap


def corner_woodquoin(L, at_start, qa, qb, w=2.4, t=0.65):
    """Wooden quoins: a corner board carrying chamfered blocks, long and short in turn, so the
    corner reads as dressed stone (the Lafayette)."""
    def span(a, b):
        return (a, b) if at_start else (L - b, L - a)
    u0, u1 = span(-t, w)
    parts = [box([u0, qa, 0.0], [u1, qb, t])]
    v = qa + 0.4
    k = 0
    while v < qb - 2.0:
        leg = 3.6 if k % 2 == 0 else 2.4
        a, b = span(-t - 0.4, leg)
        top = min(v + 2.4, qb - 0.4)
        parts.append(chamfer_box(a, v, b, top, 0.0, t + 0.45, c=0.3, bottom=0.45, square=("u0",) if at_start else ("u1",)))
        v += 2.8
        k += 1
    return union(parts)


def foundation_chequerstone(reg, seed=0):
    """Stone laid in a chequer: smooth ashlar blocks and rock-faced ones in turn, in even
    courses (the Lafayette)."""
    b = reg.bounds()
    rng = np.random.default_rng(seed + 82)
    out = [M.extrude(reg, 0.2)]
    v = b[1] + 0.2
    j = 0
    while v < b[3] - 1.0:
        hh = min(3.0, b[3] - v - 0.2)
        u = b[0] - (j % 2) * 2.5
        i = 0
        while u < b[2]:
            blk = rect(u + 0.25, v + 0.25, u + 5.0 - 0.25, v + hh - 0.25) ^ reg
            if not blk.is_empty():
                if (i + j) % 2 == 0:
                    out.append(ext(blk, 0.15, 0.5))
                else:
                    pts = blk.offset(-0.4, JoinType.Miter, 4.0)
                    out.append(ext(blk, 0.15, 0.4))
                    if not pts.is_empty():
                        bb = pts.bounds()
                        bumps = cs_union([circle((rng.uniform(bb[0], bb[2]), rng.uniform(bb[1], bb[3])), rng.uniform(0.5, 0.9), 8)
                                          for _ in range(5)]) ^ pts
                        out.append(ext(pts, 0.35, 0.6) + ext(bumps, 0.55, 0.85))
            u += 5.0
            i += 1
        v += hh
        j += 1
    return union(out)


def chimney_lafayette(w=10.0, d=10.0, h=24.0):
    """The Lafayette's stacks: stucco scored as V-jointed rusticated blocks, a moulded stone
    cornice under a coping, and two tall round pots with flared rims."""
    h = round(h / 0.2) * 0.2
    sh = h - 3.6
    body = box([-w / 2, -d / 2, 0.0], [w / 2, d / 2, sh])
    for z in np.arange(2.4, sh - 1.0, 2.4):                       # the rusticated courses' joints
        ring = box([-w / 2 - 1, -d / 2 - 1, z], [w / 2 + 1, d / 2 + 1, z + 0.4]) - box([-w / 2 + 0.3, -d / 2 + 0.3, z - 1], [w / 2 - 0.3, d / 2 - 0.3, z + 1])
        body = body - ring
    for k, g in enumerate((0.3, 0.6, 0.9)):
        body = body + M.hull_points([(x, y, sh + 0.6 * k - 0.01) for x in (-w / 2 - g + 0.3, w / 2 + g - 0.3) for y in (-d / 2 - g + 0.3, d / 2 + g - 0.3)] +
                                    [(x, y, sh + 0.6 * (k + 1)) for x in (-w / 2 - g, w / 2 + g) for y in (-d / 2 - g, d / 2 + g)])
    zc = sh + 1.8
    body = body + box([-w / 2 - 1.1, -d / 2 - 1.1, zc - 0.01], [w / 2 + 1.1, d / 2 + 1.1, zc + 0.8])
    pots = []
    for sx in (-1, 1):
        x = sx * w / 4
        prof = [(0.0, 0.0), (1.1, 0.0), (0.95, 0.8), (0.8, 2.6), (1.15, 3.0), (1.15, 3.4), (0.0, 3.4)]
        pots.append(M.revolve(poly(prof), 20).translate([x, 0, zc + 0.79]))
    body = body + union(pots)
    return body - union([M.cylinder(8.0, 0.55, 0.55, 12).translate([sx * w / 4, 0, zc - 3.0]) for sx in (-1, 1)])


# ------------------------------------------------------------------ cresting and finial
def fence_lafayette(L, h):
    """Lafayette cresting: palmettes (a fan of five petals on a base) between spear-headed
    bars, a ring on the rail under each palmette."""
    pitch = 3.6
    n = max(1, int(round(L / pitch)))
    p = L / n
    rail = h * 0.38
    cells = [rect(0.0, 0.0, L, 0.6), rect(0.0, rail, L, rail + 0.45)]
    for j in range(n + 1):
        u = p * j
        cells.append(rect(u - 0.3, 0.0, u + 0.3, h - 1.0))
        cells.append(poly([(u - 0.5, h - 1.1), (u + 0.5, h - 1.1), (u, h - 0.1)]))
        if j < n:
            m = u + p / 2
            base = rail + 0.4
            for a in np.linspace(math.pi * 0.2, math.pi * 0.8, 5):
                ln = (h - base - 0.3) * (1.0 if abs(a - math.pi / 2) < 0.1 else 0.8)
                cells.append(_lens((m + ln / 2 * math.cos(a), base + ln / 2 * math.sin(a)), ln, 0.55, a))
            cells.append(circle((m, base), 0.55, 14))
            rr = min(0.75, rail / 2 - 0.1)
            cells.append(circle((m, rail / 2 + 0.3), rr, 18) - circle((m, rail / 2 + 0.3), max(rr - 0.45, 0.15), 14))
            cells.append(rect(m - 0.22, rail / 2 + 0.3 + rr - 0.1, m + 0.22, rail + 0.05))
            cells.append(rect(m - 0.22, 0.55, m + 0.22, rail / 2 + 0.3 - rr + 0.1))
    return cs_union(cells) ^ rect(0.0, 0.0, L, h + 1.0)


def finial_torch(h=9.0):
    """An iron torch finial: a square plinth, a turned stem with two rings, a cup and a flame
    (the Lafayette's pavilion)."""
    prof = [(0.0, 0.0), (1.4, 0.0), (1.4, 0.8), (0.9, 1.2), (0.6, 1.6), (0.6, h * 0.35), (0.95, h * 0.38), (0.95, h * 0.43),
            (0.6, h * 0.46), (0.55, h * 0.6), (0.9, h * 0.63), (0.9, h * 0.67), (0.55, h * 0.7), (1.1, h * 0.78),
            (0.9, h * 0.82), (0.0, h * 0.82)]
    body = PW._revolve(prof, 28)
    flame = M.revolve(poly([(0.0, 0.0), (0.7, 0.0), (0.75, 0.5), (0.45, 1.0), (0.0, h * 0.18 + 0.2)]), 20).translate([0, 0, h * 0.82 - 0.01])
    return body + flame


# ------------------------------------------------------------------ windows and doors
def window_lafayette_lower(w=9.6, h=21.0, rise=1.6, A=1.0):
    """Lafayette ground floor: a segmental-headed two-over-two sash in a moulded architrave, a
    frieze carved with a garland between rosettes, a cornice hood on two long scroll consoles
    with a sawn crest of C-scrolls round a fan, and a panelled apron under a moulded sill."""
    op = O.opening_cs(w, h, rise)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    sash = O.window_insert(w, h, rise, lites=(2, 2), bare=True)["insert"]
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS),
             MD.band(op.offset(A, JoinType.Miter, 4.0), A, MD.ARCHITRAVE, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op)]
    half = w / 2 + A + 1.8
    vf = h + A - 0.2
    parts.append(ext(rect(-half + 1.2, vf - 0.01, half - 1.2, vf + 2.4), 0.0, 0.6))
    parts.append(ext(swag(-half + 2.6, half - 2.6, vf + 2.0, 1.3, width=0.6) + rect(-half + 2.4, vf + 1.8, half - 2.4, vf + 2.1), 0.59, 1.0))
    for sg in (-1, 1):
        parts.append(MD.rosette(sg * (half - 2.0), vf + 1.2, 0.6, 0.59, 0.5))
        parts.append(console(5.0, 1.8, 1.2, u=sg * (half - 0.6), v_top=vf + 2.4, w0=0.0))
    vc = vf + 2.4 + 1.2
    parts.append(MD.run(-half - 0.6, half + 0.6, vc, MD.CROWN, 1.4, up=False))
    crest = [rect(-half + 0.4, vc - 0.01, half - 0.4, vc + 0.5)]
    for sg in (-1, 1):
        crest.append(stroke([(sg * 1.4, vc + 0.4), (sg * 2.6, vc + 1.6), (sg * 3.8, vc + 1.2), (sg * 3.6, vc + 0.5)], 0.5))
        crest.append(circle((sg * 3.7, vc + 0.75), 0.4, 12))
    parts.append(ext(cs_union(crest), 0.0, 0.9))
    parts.append(fan_crest(0.0, vc + 0.4, 1.8, 0.0, 1.0, rays=3))
    sw = w / 2 + A + 0.6
    parts.append(MD.run(-sw, sw, 0.0, MD.SILL, 1.0, up=False))
    aw = w / 2 + A * 0.5
    parts.append(ext(rect(-aw, -3.2, aw, -0.99), 0.0, 0.55))
    parts.append(chamfer_box(-aw + 0.8, -2.7, aw - 0.8, -1.4, 0.54, 0.35, c=0.2))
    return O._one_piece([sash], parts, op, plug_cs, O.PLUG, vc + 2.3, -3.2)


def window_lafayette_upper(w=8.4, h=20.0, A=0.9):
    """Lafayette upper floor: a round-headed one-over-one sash in an architrave, a hood mould
    following the arch whose ends curl into volutes at the spring line, a keystone carrying a
    small shell, a sill on a corbel."""
    r = w / 2
    spring = h - r
    op = O.opening_cs(w, h, r)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    sash = O.window_insert(w, h, r, lites=(1, 1), bare=True)["insert"]
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS),
             MD.band(op.offset(A, JoinType.Round), A, MD.ARCHITRAVE, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op)]
    HB = 1.2
    R0, R1 = r + A + 0.1, r + A + 0.1 + HB
    up = rect(-R1 - 3, spring - 0.01, R1 + 3, spring + R1 + 2)
    parts.append(ext((circle((0.0, spring), R1, 64) - circle((0.0, spring), R0, 64)) ^ up, 0.0, 1.2))
    for sg in (-1, 1):
        c = (sg * (R0 + HB / 2), spring - 0.9)
        vol = cs_union([circle(c, 1.0, 20) - circle(c, 0.45, 14), rect(c[0] - HB / 2, spring - 0.9, c[0] + HB / 2, spring + 0.01)])
        parts.append(ext(vol, 0.0, 1.2))
        parts.append(ext(circle(c, 0.5, 12), 0.0, 1.0))
    parts.append(MD.scroll_keystone(0.0, h - 0.3, R1 - r + 0.9, 1.3, 1.8, 0.0, 1.6))
    parts.append(fan_crest(0.0, spring + R1 + 0.5, 1.4, 0.0, 1.0, rays=3))
    sw = r + A + 0.6
    parts.append(MD.run(-sw, sw, 0.0, MD.SILL, 1.0, up=False))
    parts.append(chamfer_box(-1.6, -2.2, 1.6, -0.8, 0.0, 1.0, c=0.3))
    return O._one_piece([sash], parts, op, plug_cs, O.PLUG, spring + R1 + 0.5 + 1.4, -2.2)


def _leaf_lafayette(u0, lw, dh, pl):
    """A Lafayette door leaf: a long light with an octagonal head over two raised panels, the
    upper one round-headed."""
    body = [ext(rect(u0, 0.5, u0 + lw, dh), -pl, -0.8)]
    gw = lw - 1.6
    gv0 = dh * 0.46
    gv1 = dh - 0.8
    c = 0.8
    light = poly([(u0 + 0.8, gv0), (u0 + 0.8 + gw, gv0), (u0 + 0.8 + gw, gv1 - c), (u0 + 0.8 + gw - c, gv1), (u0 + 0.8 + c, gv1),
                  (u0 + 0.8, gv1 - c)])
    body.append(_panel(rect(u0 + 0.8, 1.2, u0 + lw - 0.8, gv0 * 0.45)))
    pv0, pv1 = gv0 * 0.45 + 0.7, gv0 - 0.8
    body.append(_panel(cs_union([rect(u0 + 0.8, pv0, u0 + lw - 0.8, pv1 - gw / 2), circle((u0 + lw / 2, pv1 - gw / 2), gw / 2, 24)])))
    return body, light


def door_lafayette(w=13.6, h=28.0, A=1.2):
    """The Lafayette's entrance: a pair of leaves (octagon-headed lights over a square and a
    round-headed panel) under a segmental transom with a star of bars, an architrave with
    crossettes, a frieze with a cartouche, and a big segmental hood on two long consoles."""
    transom = 5.0
    rise = 1.6
    op = O.opening_cs(w, h, rise)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    mid = 0.5
    lw = (w - 2 * O.CLR - 1.0 - mid) / 2
    dh = h - transom - rise
    body, lights = [ext(plug_cs, -pl, -1.0)], []
    u = -w / 2 + O.CLR + 0.5
    for i in range(2):
        b_, lt = _leaf_lafayette(u, lw, dh, pl)
        body += b_
        lights.append(lt)
        u += lw + mid
    tr = plug_cs.offset(-0.5, JoinType.Miter, 4.0) ^ rect(-w, dh + 0.5, w, h + 2)
    tc = ((0.0), (dh + 0.5 + h) / 2)
    star = cs_union([stroke([(tc[0] - 3.2 * math.cos(a), tc[1] - 3.2 * math.sin(a)), (tc[0] + 3.2 * math.cos(a), tc[1] + 3.2 * math.sin(a))], 0.5)
                     for a in (0.0, math.pi / 3, 2 * math.pi / 3)] + [circle(tc, 0.9, 16)])
    g = cs_union(lights) + tr
    sash = _glazed(body, g, pl, star, plug_cs)
    sash.append(ext(rect(-w, dh - 0.01, w, dh + 0.5) ^ plug_cs, -pl, -0.5))
    outer = op.offset(A, JoinType.Miter, 4.0)
    spring = h - rise
    ears = cs_union([rect(-w / 2 - A - 0.8, spring - 2.4, -w / 2, spring + 0.8), rect(w / 2, spring - 2.4, w / 2 + A + 0.8, spring + 0.8)])
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS),
             MD.band(cs_union([outer, ears]), A + 0.8, MD.ARCHITRAVE, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op)]
    for sg in (-1, 1):
        parts.append(chamfer_box(sg * (w / 2 + A / 2) - 1.1, 0.0, sg * (w / 2 + A / 2) + 1.1, 2.4, 0.0, 1.4, c=0.35))
    half = w / 2 + A + 2.4
    vf = h + A
    parts.append(ext(rect(-half + 0.6, vf - 0.2, half - 0.6, vf + 2.6), 0.0, 0.6))
    parts.append(ext(oval((0.0, vf + 1.2), 2.4, 1.0, 28), 0.0, 0.5))
    parts.append(MD.cartouche((0.0, vf + 1.2), 3.6, 2.0, 0.59, 0.6))
    for sg in (-1, 1):
        parts.append(console(6.4, 2.4, 1.4, u=sg * (half - 1.0), v_top=vf + 2.6, w0=0.0))
    vc = vf + 2.6 + 1.4
    parts.append(MD.run(-half - 0.8, half + 0.8, vc, MD.CROWN, 1.6, up=False))
    rp = 2.6
    seg = arch_cs(-half - 0.6, half + 0.6, vc - 0.01, vc, rise=rp, seg=64)
    parts.append(MD.band(seg, 1.2, MD.CROWN, clip=rect(-half - 2, vc, half + 2, vc + 10)))
    tymp = seg.offset(-1.1, JoinType.Round) ^ rect(-half, vc, half, vc + 10)
    parts.append(ext(tymp, 0.0, 0.6))
    parts.append(fan_crest(0.0, vc + 0.1, rp - 0.5, 0.59, 0.5, rays=5))
    return O._one_piece(sash, parts, op, plug_cs, pl, vc + rp, 0.0)


def door_lafayette_back(w=10.0, h=25.0, A=1.0):
    """The Lafayette's back door: one leaf with an octagon-headed light over panels, a
    two-light transom, an architrave and a cornice hood on two consoles."""
    transom = 3.6
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    dh = h - transom
    lw = w - 2 * O.CLR - 1.0
    body, light = _leaf_lafayette(-w / 2 + O.CLR + 0.5, lw, dh, pl)
    body = [ext(plug_cs, -pl, -1.0)] + body
    g = plug_cs.offset(-0.5, JoinType.Miter, 4.0) ^ rect(-w, dh + 0.3, w, h + 2)
    sash = _glazed(body, light + g, pl, _muntins(g, 2, 1), plug_cs)
    sash.append(ext(rect(-w, dh - 0.3, w, dh + 0.3) ^ plug_cs, -pl, -0.4))
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS),
             MD.band(op.offset(A, JoinType.Miter, 4.0), A, MD.ARCHITRAVE, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op)]
    half = w / 2 + A + 0.6
    vf = h + A
    parts.append(ext(rect(-half, vf - 0.01, half, vf + 1.8), 0.0, 0.6))
    for sg in (-1, 1):
        parts.append(console(3.0, 1.4, 1.1, u=sg * (half - 0.6), v_top=vf + 1.8, w0=0.0))
    parts.append(MD.run(-half - 0.6, half + 0.6, vf + 1.8 + 1.2, MD.CROWN, 1.2, up=False))
    return O._one_piece(sash, parts, op, plug_cs, pl, vf + 3.0, 0.0)


# ------------------------------------------------------------------ porch
def post_reededvase(h, collar=None, abacus=3.0, slot=(1.2, 1.0)):
    """A turned post with a vase-shaped foot and a reeded shaft (eight round reeds), a ring
    under a bell capital (the Lafayette's veranda)."""
    z1 = h - 2.8
    zv = round(min(6.0, h * 0.22) / 0.2) * 0.2
    prof = [(0.0, 1.19), (1.5, 1.19), (1.5, 1.4), (1.1, 1.7), (1.35, zv * 0.55), (0.95, zv), (1.2, zv + 0.2), (1.2, zv + 0.45),
            (0.85, zv + 0.65), (0.85, z1), (1.15, z1 + 0.2), (1.15, z1 + 0.4), (0.9, z1 + 0.6), (1.2, z1 + 1.0)]
    body = PW._revolve(prof, 32) + PW._plinth(3.0)
    reeds = union([M.cylinder(z1 - zv - 1.6, 0.25, 0.25, 10).translate([0.85 * math.cos(a), 0.85 * math.sin(a), zv + 1.0])
                   for a in np.linspace(0, 2 * math.pi, 8, endpoint=False)])
    return body + reeds + PW._top(h, abacus / 2, z1 + 1.0, 1.2, slot, seg=32)


def fill_fleursplats(L, vb, vt):
    """A railing of sawn splats, each cut as a fleur-de-lis between plain stiles (the
    Lafayette)."""
    H = vt - vb
    n = max(1, int(round(L / 2.6)))
    parts = []
    for i in range(n + 1):
        x = L * i / n
        parts.append(rect(x - 0.3, vb, x + 0.3, vt))
        if i < n:
            m = x + L / n / 2
            vm = vb + H * 0.5
            fl = cs_union([_lens((m, vm + H * 0.12), H * 0.5, 0.75, math.pi / 2),
                           _lens((m - 0.55, vm + H * 0.02), H * 0.35, 0.55, math.pi / 2 + 0.6),
                           _lens((m + 0.55, vm + H * 0.02), H * 0.35, 0.55, math.pi / 2 - 0.6),
                           rect(m - 0.85, vm - H * 0.12, m + 0.85, vm - H * 0.04),
                           rect(m - 0.28, vb, m + 0.28, vt)])
            parts.append(fl ^ rect(x + 0.2, vb, x + L / n - 0.2, vt))
    return parts


def frieze_festoons(u0, u1, v_bot, v_top):
    """A porch frieze: a board with a rope festoon hung in shallow loops along its foot, a
    tassel at every point (the Lafayette)."""
    v0 = v_top - 2.6
    board = rect(u0, v0, u1, v_top + 0.05)
    n = max(2, int((u1 - u0) / 4.0))
    pts = []
    for j in range(n * 12 + 1):
        t = j / (n * 12)
        x = u0 + (u1 - u0) * t
        pts.append((x, v0 - 0.9 * abs(math.sin(math.pi * n * t))))
    rope = stroke(pts, 0.55)
    tassels = [poly([(u0 + (u1 - u0) * k / n - 0.35, v0 + 0.01), (u0 + (u1 - u0) * k / n + 0.35, v0 + 0.01), (u0 + (u1 - u0) * k / n, v0 - 1.6)])
               for k in range(1, n)]
    return cs_union([board, rope] + tassels) ^ rect(u0, v0 - 2.0, u1, v_top + 0.05)


def skirt_scallopboards(reg, d=1.2):
    """A porch skirt of upright boards, their feet cut in rounded scallops (the Lafayette)."""
    u0, v0, u1, v1 = reg.bounds()
    boards = []
    for u in np.arange(u0 + 0.2, u1, 1.6):
        boards.append(cs_union([rect(u, v0 + 0.7, u + 1.2, v1 + 1), circle((u + 0.6, v0 + 0.7), 0.6, 14)]))
    return M.extrude(reg, d * 0.4) + M.extrude(cs_union(boards) ^ reg, d)


def edge_pendants(L, z0, zc):
    """Porch fascia (the Lafayette): little turned pendants hung under the crown."""
    out = [rect(0.3, zc - 0.45, L - 0.3, zc)]
    for x in np.arange(1.2, L - 0.8, 2.6):
        out += [rect(x - 0.25, zc - 1.0, x + 0.25, zc - 0.4), circle((x, zc - 1.2), 0.4, 12)]
    return cs_union(out), 0.6


CO.FRIEZE_EXTRA.update(cockades=frieze_cockades, candelabra=frieze_candelabra)
CO.COURSE_EXTRA.update(ribbonstick=course_ribbonstick, beaddentil=course_beaddentil, lambstongue=course_lambstongue)
TW.BRACKET_EXTRA.update(leafmod=bracket_leafmod)
TW.PIERCED = TW.PIERCED + ("leafmod",)
SH.CORNER_EXTRA.update(woodquoin=corner_woodquoin)
TW.FOUNDATION_EXTRA.update(chequerstone=foundation_chequerstone)
PW.POSTS.update(reededvase=post_reededvase)
PW.FILLS.update(fleursplats=fill_fleursplats)
PW.FRIEZES.update(festoons=frieze_festoons)
PW.SKIRTS.update(scallopboards=skirt_scallopboards)
FT.EDGE_EXTRA.update(pendants=edge_pendants)


# ================================================================== the Delacroix (house 83)
# Deep red brick in rat-trap bond with buff sandstone dressings and bottle-green accents; a
# tall square corner tower under a concave cap; a straight mansard of square slate with a
# diaper of hexagon-cut slates; pedimented add-ins; a veranda along the front to the tower.

def slate_diaper(k, j):
    """The Delacroix's slating: square slates with a diaper of hexagon-cut ones, diagonal
    lines of them crossing every eight slates."""
    x = j + 0.5 * (k % 2)
    a, b = (x + 0.5 * k) % 8, (x - 0.5 * k) % 8
    return "hex" if min(a, 8 - a) < 0.3 or min(b, 8 - b) < 0.3 else "square"


# ------------------------------------------------------------------ cornice ornaments
def frieze_thistles(L, h, b, pitch, margin, pair, half):
    """Thistles: in every bay a thistle head (a bulb under a fan of spikes) on a stem between
    two spiny leaves; a boss at each station (the Delacroix's storey joint)."""
    v0, v1 = 0.8, h - 0.8
    hh = v1 - v0
    s = hh / 4.0
    out = []
    for uc, wd in CO._between(L, pitch, margin, pair, half):
        if wd < 3.8:
            continue
        stem = rect(uc - 0.22, v0, uc + 0.22, v0 + 2.2 * s)
        leaves = [_lens((uc + sg * 0.85 * s, v0 + 1.1 * s), 1.9 * s, 0.6 * s, sg * 0.55) for sg in (-1, 1)]
        out.append(_st(cs_union([stem] + leaves), b, 0.35))
        head = oval((uc, v0 + 2.55 * s), 0.7 * s, 0.6 * s, 18)
        spikes = [poly([(uc + dx - 0.2, v0 + 2.9 * s), (uc + dx + 0.2, v0 + 2.9 * s), (uc + dx * 1.6, v0 + 3.95 * s)])
                  for dx in (-0.5 * s, -0.17 * s, 0.17 * s, 0.5 * s)]
        out.append(_st(cs_union([head] + spikes), b, 0.55))
        out.append(_st(rect(uc - 0.75 * s, v0 + 2.3 * s, uc + 0.75 * s, v0 + 2.45 * s) ^ head.offset(-0.1), b + 0.55, 0.2))
    for u in CO._us(L, pitch, margin, 0.0):
        out.append(_st(circle((u, (v0 + v1) / 2), 0.6, 14), b, 0.45))
    return out, []


def frieze_ferns(L, h, b, pitch, margin, pair, half):
    """Ferns: in every bay two fronds arching out from a tuft, each a curved rib with leaflets
    along it, shrinking to the tip (the Delacroix's eave)."""
    v0, v1 = 0.8, h - 0.8
    hh = v1 - v0
    out = []
    for uc, wd in CO._between(L, pitch, margin, pair, half):
        if wd < 4.4:
            continue
        W, H = wd / 2 - 0.6, hh * 0.72
        parts = [circle((uc, v0 + 0.45), 0.55, 14)]
        for sg in (-1, 1):
            ts = np.linspace(0.0, 1.0, 14)
            pts = [(uc + sg * W * t, v0 + 0.4 + H * math.sin(math.pi * 0.9 * t)) for t in ts]
            parts.append(stroke(pts, 0.4))
            for t in np.linspace(0.15, 0.85, 6):
                i = int(t * 13)
                p0, p1 = np.array(pts[i]), np.array(pts[min(i + 1, 13)])
                tg = (p1 - p0) / max(np.linalg.norm(p1 - p0), 1e-6)
                ang = math.atan2(tg[1], tg[0])
                ln = 1.2 * (1 - 0.55 * t)
                for side in (1, -1):
                    a = ang + side * 1.0
                    c = p0 + np.array([math.cos(a), math.sin(a)]) * ln * 0.5
                    parts.append(_lens((c[0], c[1]), ln, 0.45, a))
        out.append(_st(cs_union(parts) ^ rect(uc - wd / 2 + 0.2, v0, uc + wd / 2 - 0.2, v1), b, 0.4))
    return out, []


def course_knurl(L, h, b, pitch, margin, p):
    """Knurling: close-set upright ribs, like a milled edge, between two fillets (the
    Delacroix)."""
    out = [ext(rect(0.2, 0.0, L - 0.2, 0.4), b - 0.05, b + 0.5), ext(rect(0.2, h - 0.4, L - 0.2, h), b - 0.05, b + 0.5)]
    out += [_st(rect(u - 0.25, 0.35, u + 0.25, h - 0.35), b, 0.4) for u in np.arange(0.7, L - 0.5, 0.95)]
    return out


def plait(L, h):
    """A plait as CrossSections: two strands crossing in a run of overlapping tilted ovals."""
    pu = max(1.4, h * 0.9)
    n = max(1, int((L - 1.0) / pu))
    u0 = (L - n * pu) / 2
    return [cs_union([_lens((u0 + pu * (k + 0.5), h / 2), pu * 1.35, min(h * 0.5, 0.8), 0.45 if k % 2 else -0.45)
                      for k in range(n)]) ^ rect(0.2, 0.1, L - 0.2, h - 0.1)]


def course_plait(L, h, b, pitch, margin, p):
    """A plait: two strands crossing in a run of overlapping tilted ovals (the Delacroix)."""
    return [_st(cs, b, 0.45) for cs in plait(L, h)]


def bracket_swanneck(h, d, t):
    """A swan-neck bracket: a broad tail on the wall sweeping out in an S that curls into a
    round head under the soffit's front edge, a sunk eye in the neck (side profile, top at
    v = 0; the Delacroix)."""
    r = min(0.24 * h, 0.3 * d, 0.85)
    pts = [(0.0, 0.0), (d, 0.0), (d, -r)]
    for s in np.linspace(0.0, 1.0, 12):
        pts.append((d - r - (d - r - 0.7) * (3 * s * s - 2 * s ** 3), -r - (h - r - 0.3) * s))
    pts += [(0.0, -h + 0.3)]
    prof = cs_union([poly(pts), circle((d - r, -r), r, 16), circle((0.35, -h + 0.4), 0.4, 12)])
    return prof - circle((d - 2.3 * r, -1.9 * r), min(0.55, r * 0.6), 14)


# ------------------------------------------------------------------ the mansard's window add-ins
def addin_delacroix(w=5.4, h=10.4, A=0.9):
    """A Delacroix add-in: a flat-headed two-over-two light in an architrave with crossettes, a
    frieze with a rosette, a triangular pediment with acroteria, a sill on two blocks."""
    op = rect(-w / 2, 0.0, w / 2, h)
    bars = cs_union([rect(-RIB / 2, -1.0, RIB / 2, h + 1.0), rect(-w, h * 0.5 - 0.3, w, h * 0.5 + 0.3)])
    half = w / 2 + A + 0.6
    ears = cs_union([rect(-half, h - 1.8, half, h + A)])
    outer = cs_union([op.offset(A, JoinType.Miter, 4.0), ears])
    vf = h + A
    vp = vf + 1.8 + 1.0
    hp = 2.6
    tri = poly([(-half - 0.4, vp - 0.4), (half + 0.4, vp - 0.4), (0.0, vp + hp)])
    body = cs_union([rect(-half, -0.2, half, vp), tri])
    parts = [ext(body - op, 0.0, 0.6), MD.band(outer, A + 0.6, MD.ARCHITRAVE, clip=rect(-20, 0.0, 20, 40) - op),
             ext(rect(-half, vf - 0.01, half, vf + 1.8), 0.0, 0.7), MD.rosette(0.0, vf + 0.9, 0.6, 0.69, 0.5),
             MD.run(-half - 0.4, half + 0.4, vp, MD.CROWN, 1.0, up=False)]
    inner = tri.offset(-0.9, JoinType.Miter, 4.0)
    parts.append(ext(tri - inner, 0.0, 1.1))
    for x, v in ((-half - 0.1, vp - 0.4), (half + 0.1, vp - 0.4), (0.0, vp + hp - 0.6)):
        parts.append(chamfer_box(x - 0.55, v - 0.1, x + 0.55, v + 0.9, 0.0, 1.2, c=0.3))
    sw = half + 0.3
    parts.append(MD.run(-sw, sw, 0.0, MD.SILL, 1.0, up=False))
    for sg in (-1, 1):
        parts.append(chamfer_box(sg * (w / 2) - 0.6, -1.8, sg * (w / 2) + 0.6, -0.8, 0.0, 0.9, c=0.25))
    parts = [p - ext(op, -1.0, 5.0) for p in parts]
    outline = body.offset(-0.4, JoinType.Miter, 4.0) ^ rect(-50, 0.2, 50, 100)
    return dict(light=op, bars=bars, frame=parts, outline=outline, top=vp + hp + 0.4, bottom=-1.8)


# ------------------------------------------------------------------ walls, foundation, chimney
def brick_rattrap(region, datum=0.0, bl=2.4, bh=1.2, mortar=0.5, bed=0.25, d=0.25):
    """Rat-trap bond: every brick laid on edge, shiners (stretchers on edge) and rowlocks
    (headers on edge) in turn along each course, so the courses are tall and the wall reads
    as a lattice (the Delacroix)."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    hl = bl / 2
    unit = bl + hl
    cells, proud = [], []
    k = math.floor((v0 - datum) / bh) - 1
    while datum + k * bh < v1:
        v = datum + k * bh
        top = v + bh - bed
        u = u0 - 2 * unit + (k % 2) * unit / 2
        while u < u1 + unit:
            cells.append(rect(u + mortar / 2, v, u + bl - mortar / 2, top))
            proud.append(rect(u + bl + mortar / 2, v, u + unit - mortar / 2, top))
            u += unit
        k += 1
    return M.extrude(cs_union(cells) ^ region, d) + M.extrude(cs_union(proud) ^ region, d + 0.1)


def foundation_pickdressed(reg, seed=0):
    """Pick-dressed sandstone: long blocks in two course heights, each face covered in rows of
    little pyramids left by the pick, inside a smooth chiselled margin (the Delacroix)."""
    b = reg.bounds()
    out = [M.extrude(reg, 0.2)]
    v = b[1] + 0.2
    j = 0
    while v < b[3] - 1.0:
        hh = min(3.2 if j % 2 == 0 else 2.2, b[3] - v - 0.2)
        u = b[0] - (j % 2) * 3.5
        while u < b[2]:
            blk = rect(u + 0.25, v + 0.25, u + 7.0 - 0.25, v + hh - 0.25) ^ reg
            if not blk.is_empty():
                out.append(ext(blk, 0.15, 0.45))
                fld = blk.offset(-0.5, JoinType.Miter, 4.0)
                if not fld.is_empty():
                    fb = fld.bounds()
                    pts = []
                    for y_ in np.arange(fb[1] + 0.4, fb[3] - 0.2, 0.8):
                        for x_ in np.arange(fb[0] + 0.4, fb[2] - 0.2, 0.8):
                            pts += [(x_, y_, 0.44), ]
                    if pts:
                        pyr = union([M.hull_points([(x_ - 0.35, y_ - 0.35, z), (x_ + 0.35, y_ - 0.35, z), (x_ + 0.35, y_ + 0.35, z),
                                                    (x_ - 0.35, y_ + 0.35, z), (x_, y_, z + 0.3)]) for x_, y_, z in pts])
                        out.append(pyr)
            u += 7.0
        v += hh
        j += 1
    return union(out)


def chimney_delacroix(w=10.0, d=10.0, h=26.0):
    """The Delacroix's stacks: red brick with a sandstone band, the top an open stone cap on
    four corner piers under a little gabled coping (the smoke leaves under the gables)."""
    h = round(h / 0.2) * 0.2
    sh = h - 6.0
    body = box([-w / 2, -d / 2, 0.0], [w / 2, d / 2, sh])
    zb = sh - 6.0
    body = body + box([-w / 2 - 0.5, -d / 2 - 0.5, zb], [w / 2 + 0.5, d / 2 + 0.5, zb + 1.2])
    body = body + M.hull_points([(x, y, sh - 0.01) for x in (-w / 2, w / 2) for y in (-d / 2, d / 2)] +
                                [(x, y, sh + 0.6) for x in (-w / 2 - 0.6, w / 2 + 0.6) for y in (-d / 2 - 0.6, d / 2 + 0.6)])
    body = body + box([-w / 2 - 0.6, -d / 2 - 0.6, sh + 0.59], [w / 2 + 0.6, d / 2 + 0.6, sh + 1.2])
    for sx in (-1, 1):
        for sy in (-1, 1):
            body = body + box([sx * (w / 2 - 1.0) - 1.0, sy * (d / 2 - 1.0) - 1.0, sh + 1.19], [sx * (w / 2 - 1.0) + 1.0, sy * (d / 2 - 1.0) + 1.0, sh + 3.4])
    zc = sh + 3.39
    body = body + box([-w / 2 - 0.4, -d / 2 - 0.4, zc], [w / 2 + 0.4, d / 2 + 0.4, zc + 0.6])
    gable = M.hull_points([(x, y, zc + 0.59) for x in (-w / 2 - 0.4, w / 2 + 0.4) for y in (-d / 2 - 0.4, d / 2 + 0.4)] +
                          [(x, 0.0, zc + 0.6 + d / 2 * 0.45) for x in (-w / 2 - 0.4, w / 2 + 0.4)])
    flue = box([-w / 2 + 2.0, -d / 2 + 2.0, sh - 4.0], [w / 2 - 2.0, d / 2 - 2.0, sh + 3.4])
    return body + gable - flue


def fence_delacroix(L, h):
    """Delacroix cresting: bars with trefoil heads, a row of quatrefoil rings between the
    rails."""
    pitch = 2.8
    n = max(1, int(round(L / pitch)))
    p = L / n
    r0, r1 = h * 0.18, h * 0.58
    cells = [rect(0.0, 0.0, L, 0.6), rect(0.0, r0, L, r0 + 0.45), rect(0.0, r1, L, r1 + 0.45)]
    for j in range(n + 1):
        u = p * j
        cells.append(rect(u - 0.28, 0.0, u + 0.28, h - 0.9))
        cells += [circle((u, h - 0.55), 0.42, 12), circle((u - 0.45, h - 0.95), 0.36, 12), circle((u + 0.45, h - 0.95), 0.36, 12)]
        if j < n:
            m = u + p / 2
            vc = (r0 + 0.45 + r1) / 2
            rr = min((r1 - r0 - 0.45) / 2 + 0.05, p / 2 - 0.35)
            cells.append(circle((m, vc), rr, 20))               # a boss (a ring this small printed shut)
            cells.append(rect(m - 0.23, vc + rr - 0.15, m + 0.23, r1 + 0.05))
            cells.append(rect(m - 0.23, r0 + 0.4, m + 0.23, vc - rr + 0.15))
    return cs_union(cells) ^ rect(0.0, 0.0, L, h + 1.0)


def finial_crownball(h=9.0):
    """A finial of a ball on a turned stem carrying a little crown of four points (the
    Delacroix's tower)."""
    prof = [(0.0, 0.0), (1.4, 0.0), (1.4, 0.8), (0.8, 1.3), (0.55, 2.0), (0.55, h * 0.4), (0.9, h * 0.44), (0.55, h * 0.48),
            (0.0, h * 0.48)]
    body = PW._revolve(prof, 28) + M.sphere(1.3, 28).translate([0, 0, h * 0.48 + 1.1])
    zc = h * 0.48 + 2.2
    crown = M.cylinder(0.6, 0.9, 0.9, 20).translate([0, 0, zc - 0.2])
    for a in np.linspace(0, 2 * math.pi, 4, endpoint=False):
        crown = crown + M.hull_points([(0.7 * math.cos(a) + dx, 0.7 * math.sin(a) + dy, zc + 0.3) for dx in (-0.25, 0.25) for dy in (-0.25, 0.25)] +
                                      [(0.85 * math.cos(a), 0.85 * math.sin(a), zc + 1.5)])
    return body + crown + M.cylinder(h - zc - 0.2, 0.3, 0.12, 12).translate([0, 0, zc + 0.2])


# ------------------------------------------------------------------ windows and doors
def window_delacroix_lower(w=9.6, h=22.0, A=1.0):
    """Delacroix ground floor: a round-headed two-over-two sash in a beaded architrave, under a
    segmental pediment on two consoles that is broken at its apex by a scrolled keystone rising
    from the arch; a panelled apron with a lozenge under the sill."""
    r = w / 2
    spring = h - r
    op = O.opening_cs(w, h, r)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    sash = O.window_insert(w, h, r, lites=(2, 2), bare=True)["insert"]
    band = op.offset(A, JoinType.Round)
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS),
             MD.band(band, A, MD.ARCHITRAVE, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op)]
    beads = []
    for t in np.linspace(0.04, 0.96, 23):
        if t < 0.33:
            x, v = -r - A * 0.5, spring * t / 0.33
        elif t > 0.67:
            x, v = r + A * 0.5, spring * (1 - t) / 0.33
        else:
            a = math.pi * (1 - (t - 0.33) / 0.34)
            x, v = (r + A * 0.5) * math.cos(a), spring + (r + A * 0.5) * math.sin(a)
        beads.append(circle((x, v), 0.32, 10))
    parts.append(ext(cs_union(beads) ^ rect(-w, 0.3, w, h + 5), 0.6, 1.3))
    half = r + A + 1.6
    vc = spring + r + A + 1.0
    for sg in (-1, 1):
        parts.append(console(4.0, 1.6, 1.2, u=sg * (half - 0.8), v_top=vc - 1.0, w0=0.0))
    parts.append(ext(rect(-half, spring + 0.5, half, vc - 1.0) - band, 0.0, 0.6))
    parts.append(MD.run(-half - 0.5, half + 0.5, vc, MD.CROWN, 1.2, up=False))
    rp = 2.4
    seg = arch_cs(-half - 0.4, half + 0.4, vc - 0.01, vc, rise=rp, seg=48)
    ped = MD.band(seg, 1.0, MD.CROWN, clip=rect(-half - 2, vc, half + 2, vc + 10) - rect(-1.4, vc - 1, 1.4, vc + 10))
    parts.append(ped)
    parts.append(ext(seg.offset(-0.9, JoinType.Round) ^ rect(-half, vc, half, vc + 10), 0.0, 0.6))
    parts.append(MD.scroll_keystone(0.0, h - 0.3, vc + rp - h + 0.6, 1.4, 2.2, 0.0, 1.8))
    sw = r + A + 0.6
    parts.append(MD.run(-sw, sw, 0.0, MD.SILL, 1.0, up=False))
    aw = r + A * 0.5
    parts.append(ext(rect(-aw, -3.2, aw, -0.99), 0.0, 0.55))
    parts.append(ext(poly([(-aw + 1.2, -2.1), (0.0, -2.9), (aw - 1.2, -2.1), (0.0, -1.3)]), 0.54, 0.95))
    return O._one_piece([sash], parts, op, plug_cs, O.PLUG, vc + rp + 0.6, -3.2)


def window_delacroix_upper(w=9.0, h=20.0, A=0.9):
    """Delacroix upper floor: a flat-headed two-over-two sash in an eared architrave, a
    pulvinated (cushioned) frieze, a cornice cap and a blocking course with a raised tablet;
    a sill on two blocks."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    sash = O.window_insert(w, h, 0, lites=(2, 2), bare=True)["insert"]
    half = w / 2 + A + 0.7
    outer = cs_union([op.offset(A, JoinType.Miter, 4.0), rect(-half, h - 2.0, half, h + A)])
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS),
             MD.band(outer, A + 0.7, MD.ARCHITRAVE, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op)]
    vf = h + A
    parts.append(ext(rect(-half, vf - 0.01, half, vf + 2.0), 0.0, 0.5))
    cushion = M.cylinder(2 * half, 1.0, 1.0, 24).rotate([0, 90, 0]).translate([-half, vf + 1.0, 0.0]) ^ box([-half, vf, 0.0], [half, vf + 2.0, 1.0])
    parts.append(cushion)
    vc = vf + 2.0 + 1.0
    parts.append(MD.run(-half - 0.6, half + 0.6, vc, MD.CROWN, 1.2, up=False))
    parts.append(ext(rect(-half + 0.4, vc - 0.01, half - 0.4, vc + 1.4), 0.0, 0.8))
    parts.append(ext(rect(-2.2, vc + 0.3, 2.2, vc + 1.1), 0.79, 1.1))
    sw = half + 0.2
    parts.append(MD.run(-sw, sw, 0.0, MD.SILL, 1.0, up=False))
    for sg in (-1, 1):
        parts.append(chamfer_box(sg * (w / 2) - 0.7, -2.0, sg * (w / 2) + 0.7, -0.8, 0.0, 0.9, c=0.25))
    return O._one_piece([sash], parts, op, plug_cs, O.PLUG, vc + 1.4, -2.0)


def door_delacroix(w=13.0, h=27.0, A=1.2):
    """The Delacroix's entrance: a pair of leaves, each with a long oval light over a raised
    panel, under a round fanlight with a sunk shell of bars, in a sandstone architrave with a
    keystone, between rusticated pilasters under a cornice on two consoles."""
    r = w / 2
    spring = h - r
    op = O.opening_cs(w, h, r)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    mid = 0.5
    lw = (w - 2 * O.CLR - 1.0 - mid) / 2
    dh = spring - 0.4
    body, lights = [ext(plug_cs, -pl, -1.0)], []
    u = -w / 2 + O.CLR + 0.5
    for i in range(2):
        body.append(ext(rect(u, 0.5, u + lw, dh), -pl, -0.8))
        gv0 = dh * 0.42
        lights.append(oval((u + lw / 2, (gv0 + dh - 0.8) / 2), lw / 2 - 0.8, (dh - 0.8 - gv0) / 2, 28))
        body.append(_panel(rect(u + 0.8, 1.2, u + lw - 0.8, gv0 - 0.8)))
        u += lw + mid
    fan = plug_cs.offset(-0.5, JoinType.Miter, 4.0) ^ rect(-w, spring + 0.2, w, h + 2)
    shell = cs_union([stroke([(0.0, spring + 0.2), (r * 1.2 * math.cos(a), spring + 0.2 + r * 1.2 * math.sin(a))], 0.45)
                      for a in np.linspace(0.2, math.pi - 0.2, 9)] + [circle((0.0, spring + 0.2), 1.6, 20)])
    g = cs_union(lights) + fan
    sash = _glazed(body, g, pl, shell, plug_cs)
    sash.append(ext(rect(-w, dh - 0.01, w, spring + 0.2) ^ plug_cs, -pl, -0.5))
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS),
             MD.band(op.offset(A, JoinType.Round), A, MD.ARCHITRAVE, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op)]
    pw = 2.4
    ui = r + A + 0.2
    vcap = h + A + 0.6
    for sg in (-1, 1):
        u0, u1 = sorted((sg * ui, sg * (ui + pw)))
        parts.append(ext(rect(u0, 0.0, u1, vcap), 0.0, 0.7))
        for vb in np.arange(0.0, vcap - 1.0, 2.0):
            parts.append(chamfer_box(u0 - 0.1, vb + 0.2, u1 + 0.1, min(vb + 1.8, vcap - 0.2), 0.0, 1.1, c=0.35))
    half = ui + pw + 0.3
    parts.append(ext(rect(-half, spring, half, vcap) - op.offset(A, JoinType.Round), 0.0, 0.6))
    parts.append(MD.scroll_keystone(0.0, h - 0.2, vcap - h + 1.0, 1.8, 2.6, 0.0, 2.0))
    parts.append(ext(rect(-half, vcap - 0.01, half, vcap + 2.0), 0.0, 0.7))
    for sg in (-1, 1):
        parts.append(console(3.2, 1.8, 1.4, u=sg * (ui + pw / 2), v_top=vcap + 2.0, w0=0.0))
    vs = vcap + 1.8 + 1.4
    parts.append(MD.run(-half - 0.8, half + 0.8, vs, MD.CROWN, 1.4, up=False))
    return O._one_piece(sash, parts, op, plug_cs, pl, vs, 0.0)


def door_delacroix_back(w=10.0, h=25.0, A=1.0):
    """The Delacroix's back door: one leaf of a long oval light over a panel, a flat transom,
    an architrave and a cornice cap."""
    transom = 3.4
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    dh = h - transom
    lw = w - 2 * O.CLR - 1.0
    u = -w / 2 + O.CLR + 0.5
    gv0 = dh * 0.42
    body = [ext(plug_cs, -pl, -1.0), ext(rect(u, 0.5, u + lw, dh), -pl, -0.8), _panel(rect(u + 0.8, 1.2, u + lw - 0.8, gv0 - 0.8))]
    light = oval((0.0, (gv0 + dh - 0.8) / 2), lw / 2 - 0.9, (dh - 0.8 - gv0) / 2, 28)
    g = plug_cs.offset(-0.5, JoinType.Miter, 4.0) ^ rect(-w, dh + 0.3, w, h + 2)
    sash = _glazed(body, light + g, pl, None, plug_cs)
    sash.append(ext(rect(-w, dh - 0.3, w, dh + 0.3) ^ plug_cs, -pl, -0.4))
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS),
             MD.band(op.offset(A, JoinType.Miter, 4.0), A, MD.ARCHITRAVE, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op)]
    half = w / 2 + A + 0.4
    vf = h + A
    parts.append(ext(rect(-half, vf - 0.01, half, vf + 1.6), 0.0, 0.6))
    parts.append(MD.run(-half - 0.6, half + 0.6, vf + 1.6 + 1.0, MD.CROWN, 1.2, up=False))
    return O._one_piece(sash, parts, op, plug_cs, pl, vf + 2.6, 0.0)


# ------------------------------------------------------------------ porch
def post_beadcollar(h, collar=None, abacus=3.0, slot=(1.2, 1.0)):
    """A round tapering post with a necking of beads under its capital and a bead-and-reel
    collar at a third of its height (the Delacroix's veranda)."""
    z1 = h - 2.6
    r0, r1 = 1.15, 0.92
    zc = round(z1 * 0.33 / 0.2) * 0.2
    prof = [(0.0, 1.19), (1.55, 1.19), (1.55, 1.45), (1.3, 1.7), (r0, 2.0), (r0 - (r0 - r1) * 0.3, zc - 0.6), (1.25, zc - 0.4),
            (1.25, zc + 0.4), (r0 - (r0 - r1) * 0.3, zc + 0.6), (r1, z1), (1.2, z1 + 0.25), (1.2, z1 + 0.5), (r1, z1 + 0.7)]
    body = PW._revolve(prof, 32) + PW._plinth(3.0)
    beads = union([M.sphere(0.32, 10).translate([1.1 * math.cos(a), 1.1 * math.sin(a), z1 - 0.5]) for a in np.linspace(0, 2 * math.pi, 10, endpoint=False)])
    return body + beads + PW._top(h, abacus / 2, z1 + 0.7, r1, slot, seg=32)


def baluster_beadstack(h, seg=18):
    """A bobbin-turned baluster: a stack of beads and reels between square ends (the
    Delacroix)."""
    prof = [(0.0, 0.8), (0.32, 0.8)]
    n = 5
    span = h - 1.6
    for k in range(n):
        z = 0.8 + span * k / n
        prof += [(0.32, z + 0.05), (0.52, z + span / n * 0.5), (0.32, z + span / n - 0.05)]
    prof += [(0.32, h - 0.8)]
    return PW._revolve(prof, seg) + box([-0.55, -0.55, 0.0], [0.55, 0.55, 0.81]) + box([-0.55, -0.55, h - 0.81], [0.55, 0.55, h])


def frieze_ogeearcade(u0, u1, v_bot, v_top):
    """A porch frieze: a board cut below into a row of small ogee arches, a drop at every
    meeting (the Delacroix)."""
    v0 = v_top - 2.8
    n = max(2, int((u1 - u0) / 3.2))
    p = (u1 - u0) / n
    board = rect(u0, v0, u1, v_top + 0.05)
    cuts, drops = [], []
    for k in range(n):
        a = u0 + p * k + 0.3
        e = u0 + p * (k + 1) - 0.3
        m = (a + e) / 2
        ts = np.linspace(0.0, 1.0, 9)
        left = [(a + (m - a) * t, v0 + 1.6 * (0.5 - 0.5 * math.cos(math.pi * t))) for t in ts]
        right = [(m + (e - m) * t, v0 + 1.6 * (0.5 + 0.5 * math.cos(math.pi * t))) for t in ts[1:]]
        cuts.append(poly([(a, v0 - 1.0)] + left + right + [(e, v0 - 1.0)]))
        if k:
            x = u0 + p * k
            drops.append(cs_union([rect(x - 0.3, v0 - 0.6, x + 0.3, v0 + 0.2), circle((x, v0 - 0.8), 0.4, 12)]))
    return (board - cs_union(cuts)) + cs_union(drops) + rect(u0, v0 + 1.7, u1, v_top + 0.05)


def skirt_archslats(reg, d=1.2):
    """A porch skirt of upright slats whose tops are cut in round arches under a rail (the
    Delacroix)."""
    u0, v0, u1, v1 = reg.bounds()
    slats = []
    for u in np.arange(u0 + 0.3, u1, 1.6):
        top = v1 - 1.2
        slats.append(cs_union([rect(u, v0 - 1, u + 1.0, top - 0.5), circle((u + 0.5, top - 0.5), 0.5, 12)]))
    return M.extrude(reg, d * 0.4) + M.extrude((cs_union(slats) + rect(u0, v1 - 0.8, u1, v1 + 1)) ^ reg, d)


def edge_acorndrops(L, z0, zc):
    """Porch fascia (the Delacroix): acorns hung under the crown."""
    out = [rect(0.3, zc - 0.45, L - 0.3, zc)]
    for x in np.arange(1.4, L - 1.0, 3.0):
        out += [rect(x - 0.4, zc - 0.85, x + 0.4, zc - 0.4), oval((x, zc - 1.35), 0.42, 0.55, 14)]
    return cs_union(out), 0.6


CO.FRIEZE_EXTRA.update(thistles=frieze_thistles, ferns=frieze_ferns)
CO.COURSE_EXTRA.update(knurl=course_knurl, plait=course_plait)
TW.BRACKET_EXTRA.update(swanneck=bracket_swanneck)
TW.PIERCED = TW.PIERCED + ("swanneck",)
TW.FOUNDATION_EXTRA.update(pickdressed=foundation_pickdressed)
PW.POSTS.update(beadcollar=post_beadcollar)
PW.BALUSTERS.update(beadstack=(baluster_beadstack, 1.6))
PW.FRIEZES.update(ogeearcade=frieze_ogeearcade)
PW.SKIRTS.update(archslats=skirt_archslats)
FT.EDGE_EXTRA.update(acorndrops=edge_acorndrops)


# ================================================================== the Belcourt (house 84)
# The batch's Italianate flat-roof house: ochre ashlar laid in tall and short courses, cream
# trim, oxblood accents; the last storey is an attic band of frieze windows between tall paired
# brackets, under a bracketed eave and a flat roof with a balustrade and a belvedere.

# ------------------------------------------------------------------ cornice ornaments
def frieze_squarelinks(L, h, b, pitch, margin, pair, half):
    """Square links: a chain of interlaced squares set on the diagonal, each over the next, a
    boss in every link (the Belcourt's storey joint)."""
    v0, v1 = 0.8, h - 0.8
    hh = v1 - v0
    vm = (v0 + v1) / 2
    s = hh * 0.62
    n = max(1, int((L - 1.0) / (s * 1.1)))
    u0 = (L - n * s * 1.1) / 2
    out = []
    for k in range(n):
        uc = u0 + s * 1.1 * (k + 0.5)
        sq = poly([(uc - s * 0.72, vm), (uc, vm + s * 0.72), (uc + s * 0.72, vm), (uc, vm - s * 0.72)])
        ring = sq - sq.offset(-0.5, JoinType.Miter, 4.0)
        out.append(_st(ring, b + (0.25 if k % 2 else 0.0), 0.35))
        out.append(_st(circle((uc, vm), 0.45, 12), b, 0.5))
    return out, []


def course_flutes(L, h, b, pitch, margin, p):
    """A fluted band: short round-ended flutes sunk in a plain band between fillets (the
    Belcourt)."""
    out = [ext(rect(0.2, 0.0, L - 0.2, h), b - 0.05, b + 0.5)]
    cuts = cs_union([cs_union([rect(u - 0.25, 0.65, u + 0.25, h - 0.65), circle((u, 0.65), 0.25, 10), circle((u, h - 0.65), 0.25, 10)])
                     for u in np.arange(0.9, L - 0.6, 1.1)])
    return [out[0] - ext(cuts, b + 0.2, b + 1.0)]


def frieze_sixfoils(L, h, b, pitch, margin, pair, half):
    """Sixfoils: in every bay a round panel holding a six-lobed rosette, a bead between (the
    Belcourt's belvedere)."""
    v0, v1 = 0.8, h - 0.8
    vm = (v0 + v1) / 2
    out = []
    for uc, wd in CO._between(L, pitch, margin, pair, half):
        r = min((v1 - v0) / 2 - 0.1, wd / 2 - 0.4, 1.8)
        if r < 0.9:
            continue
        out.append(_st(circle((uc, vm), r, 28) - circle((uc, vm), r - 0.45, 28), b, 0.4))
        lobes = cs_union([circle((uc + r * 0.4 * math.cos(a), vm + r * 0.4 * math.sin(a)), r * 0.32, 12)
                          for a in np.linspace(0, 2 * math.pi, 6, endpoint=False)])
        out.append(_st(lobes, b, 0.35))
        out.append(_st(circle((uc, vm), r * 0.22, 10), b + 0.35, 0.2))
    return out, []


def bracket_longconsole(h, d, t):
    """A long Italianate console for the attic: a block head under the soffit, a straight
    tapering shank down the wall, and a big scroll at the foot curling outward over a drop
    (side profile, top at v = 0; the Belcourt)."""
    r = min(0.42 * d, 0.16 * h, 1.4)
    hd = min(1.2, 0.12 * h)
    c = (r + 0.3, -h + r + 0.8)
    shank = poly([(0.0, 0.0), (d, 0.0), (d, -hd), (d * 0.55, -hd - 0.6), (c[0] + r * 0.7, c[1] + r * 0.6), (0.0, c[1] + r * 0.3)])
    prof = cs_union([shank, circle(c, r, 22), rect(0.0, c[1], 0.6, 0.0), circle((0.35, -h + 0.4), 0.4, 12)])
    return prof - circle(c, r * 0.38, 14)


# ------------------------------------------------------------------ walls, foundation, chimney
def ashlar_pseudoisodomic(region, datum=0.0, tall=3.6, short=1.8, length=7.6, joint=0.5, d=0.3, v=0.2):
    """Ashlar in tall and short courses in turn (pseudo-isodomic), every joint a shallow V,
    the blocks broken half a block course to course (the Belcourt)."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    cells = []
    z = datum - 2 * (tall + short)
    k = 0
    while z < v1:
        hh = tall if k % 2 == 0 else short
        u = u0 - length * 2 + (k % 2) * length / 2
        while u < u1 + length:
            cells.append(rect(u + joint / 2, z + joint / 2, u + length - joint / 2, z + hh - joint / 2))
            u += length
        z += hh
        k += 1
    cs = cs_union(cells) ^ region
    return ext(cs, 0.0, d - v) + ext(cs.offset(-v, JoinType.Miter, 4.0), d - v - 0.01, d)


def foundation_frostwork(reg, seed=0):
    """Frost-work rustication: big blocks whose faces carry rows of hanging, icicle-like
    ridges inside a smooth margin (the Belcourt's raised basement)."""
    b = reg.bounds()
    rng = np.random.default_rng(seed + 84)
    out = [M.extrude(reg, 0.2)]
    v = b[1] + 0.2
    j = 0
    while v < b[3] - 1.0:
        hh = min(3.4, b[3] - v - 0.2)
        u = b[0] - (j % 2) * 3.0
        while u < b[2]:
            blk = rect(u + 0.3, v + 0.3, u + 6.0 - 0.3, v + hh - 0.3) ^ reg
            if not blk.is_empty():
                out.append(ext(blk, 0.15, 0.45))
                fld = blk.offset(-0.5, JoinType.Miter, 4.0)
                if not fld.is_empty():
                    fb = fld.bounds()
                    ic = []
                    for x_ in np.arange(fb[0] + 0.35, fb[2] - 0.2, 0.75):
                        ln = rng.uniform(0.45, 0.95) * (fb[3] - fb[1])
                        ic.append(poly([(x_ - 0.3, fb[3]), (x_ + 0.3, fb[3]), (x_ + 0.05, fb[3] - ln), (x_ - 0.05, fb[3] - ln)]))
                    out.append(ext(cs_union(ic) ^ fld, 0.44, 0.75))
            u += 6.0
        v += hh
        j += 1
    return union(out)


def chimney_belcourt(w=10.0, d=11.0, h=22.0):
    """The Belcourt's stacks: stucco, a round-headed blind niche on each broad face, a frieze
    band and a broad cap on a row of little corbels, two squat round pots."""
    h = round(h / 0.2) * 0.2
    sh = h - 4.4
    body = box([-w / 2, -d / 2, 0.0], [w / 2, d / 2, sh])
    for sy in (-1, 1):
        nw = w - 4.0
        niche = cs_union([rect(-nw / 2, 3.0, nw / 2, sh - 3.0 - nw / 2), circle((0.0, sh - 3.0 - nw / 2), nw / 2, 24)])
        T = np.array([[1.0, 0, 0, 0], [0, 0, sy * 1.0, sy * d / 2], [0, 1.0, 0, 0]])
        body = body - (ext(niche, -0.6, 1.0) if sy > 0 else ext(niche, -1.0, 0.6)).transform(T)
    body = body + box([-w / 2 - 0.3, -d / 2 - 0.3, sh - 1.6], [w / 2 + 0.3, d / 2 + 0.3, sh])
    for x in np.arange(-w / 2 + 0.9, w / 2 - 0.5, 1.6):
        for sy in (-1, 1):
            body = body + M.hull_points([(x - 0.4, sy * (d / 2 + 0.3), sh - 0.01), (x + 0.4, sy * (d / 2 + 0.3), sh - 0.01),
                                         (x - 0.4, sy * (d / 2 + 1.1), sh + 0.8), (x + 0.4, sy * (d / 2 + 1.1), sh + 0.8),
                                         (x - 0.4, sy * (d / 2), sh - 0.01), (x + 0.4, sy * (d / 2), sh - 0.01)])
    # under the cap on the narrow faces (no corbels there) a 45 degree cove, so nothing prints over air
    body = body + M.hull_points([(x, y, sh - 0.01) for x in (-w / 2 - 0.3, w / 2 + 0.3) for y in (-d / 2 - 0.3, d / 2 + 0.3)] +
                                [(x, y, sh + 0.8) for x in (-w / 2 - 1.2, w / 2 + 1.2) for y in (-d / 2 - 0.3, d / 2 + 0.3)])
    body = body + box([-w / 2 - 1.2, -d / 2 - 1.2, sh + 0.79], [w / 2 + 1.2, d / 2 + 1.2, sh + 1.6])
    for sx in (-1, 1):
        body = body + M.revolve(poly([(0.0, 0.0), (1.4, 0.0), (1.2, 1.2), (1.4, 1.6), (1.4, 2.0), (0.0, 2.0)]), 20).translate([sx * w / 4, 0, sh + 1.59])
    return body - union([M.cylinder(8.0, 0.6, 0.6, 12).translate([sx * w / 4, 0, sh - 4.0]) for sx in (-1, 1)])


# ------------------------------------------------------------------ the roof balustrade and the belvedere's finial
def fence_belcourt(L, h):
    """The Belcourt's roof balustrade, as flat strips: a plinth and a coping rail with little
    vase balusters between them and a pedestal every few balusters."""
    n_ped = max(1, int(round(L / 22.0)))
    cells = [rect(0.0, 0.0, L, 0.8), rect(0.0, h - 0.8, L, h)]
    for j in range(n_ped + 1):
        x = L * j / n_ped
        cells.append(rect(max(0.0, x - 1.0), 0.0, min(L, x + 1.0), h))
        if j < n_ped:
            a, e = x + 1.0, L * (j + 1) / n_ped - 1.0
            m = max(1, int((e - a) / 1.7))
            for k in range(m):
                cells.append(_baluster_cs(a + (e - a) * (k + 0.5) / m, 0.79, h - 1.58, 1.15))
    return cs_union(cells)


def finial_ballspire(h=8.0):
    """The belvedere's finial: a turned base, a ball and a short spire (the Belcourt)."""
    prof = [(0.0, 0.0), (1.3, 0.0), (1.3, 0.7), (0.7, 1.2), (0.55, 2.4), (0.9, 2.7), (0.55, 3.0), (0.0, 3.0)]
    return PW._revolve(prof, 24) + M.sphere(1.1, 24).translate([0, 0, 3.9]) + \
        M.cylinder(h - 4.6, 0.45, 0.1, 12).translate([0, 0, 4.6])


# ------------------------------------------------------------------ windows and doors
def window_belcourt_lower(w=9.6, h=22.0, A=1.0):
    """Belcourt ground floor: a round-headed two-over-two sash in an architrave on imposts, a
    moulded archivolt with a keystone, rosettes in the spandrels, under a cornice cap."""
    r = w / 2
    spring = h - r
    op = O.opening_cs(w, h, r)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    sash = O.window_insert(w, h, r, lites=(2, 2), bare=True)["insert"]
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS),
             MD.band(op.offset(A, JoinType.Round), A, MD.ARCHITRAVE, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op)]
    for sg in (-1, 1):
        parts.append(chamfer_box(sg * (r + A / 2) - 1.0, spring - 0.8, sg * (r + A / 2) + 1.0, spring + 0.1, 0.0, 1.3, c=0.3))
    Ro = r + A + 1.2
    arc = (circle((0.0, spring), Ro, 64) - circle((0.0, spring), r + A, 64)) ^ rect(-Ro - 1, spring + 0.09, Ro + 1, spring + Ro + 1)
    parts.append(ext(arc, 0.0, 1.0))
    half = Ro + 0.4
    vc = spring + Ro + 1.2
    parts.append(ext(rect(-half, spring + 0.1, half, vc - 1.0) - circle((0.0, spring), Ro, 64), 0.0, 0.6))
    for sg in (-1, 1):
        parts.append(MD.rosette(sg * (Ro - 0.6), vc - 2.2, 0.55, 0.59, 0.5))
    parts.append(MD.scroll_keystone(0.0, h - 0.3, vc - h - 0.2, 1.4, 2.0, 0.0, 1.8))
    parts.append(MD.run(-half - 0.5, half + 0.5, vc, MD.CROWN, 1.2, up=False))
    sw = r + A + 0.6
    parts.append(MD.run(-sw, sw, 0.0, MD.SILL, 1.0, up=False))
    for sg in (-1, 1):
        parts.append(console(1.8, 1.0, 0.8, u=sg * (r + A / 2), v_top=-0.8, w0=0.0))
    return O._one_piece([sash], parts, op, plug_cs, O.PLUG, vc, -2.8)


def window_belcourt_upper(w=9.0, h=19.0, A=0.9):
    """Belcourt upper floor: a flat-headed two-over-two sash in an architrave with crossettes,
    a segmental cap on two little brackets, a plain sill."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    sash = O.window_insert(w, h, 0, lites=(2, 2), bare=True)["insert"]
    half = w / 2 + A + 0.7
    outer = cs_union([op.offset(A, JoinType.Miter, 4.0), rect(-half, h - 1.8, half, h + A)])
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS),
             MD.band(outer, A + 0.7, MD.ARCHITRAVE, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op)]
    vf = h + A
    for sg in (-1, 1):
        parts.append(console(2.2, 1.2, 1.0, u=sg * (half - 0.6), v_top=vf + 1.8, w0=0.0))
    parts.append(ext(rect(-half + 1.2, vf - 0.01, half - 1.2, vf + 1.8), 0.0, 0.5))
    rp = 1.8
    seg = arch_cs(-half - 0.5, half + 0.5, vf + 1.8 - 0.01, vf + 1.8, rise=rp, seg=48)
    parts.append(MD.band(seg, 1.2, MD.CROWN, clip=rect(-half - 2, vf + 1.79, half + 2, vf + 10)))
    parts.append(ext(seg.offset(-1.0, JoinType.Round) ^ rect(-half, vf + 1.8, half, vf + 10), 0.0, 0.6))
    sw = half + 0.2
    parts.append(MD.run(-sw, sw, 0.0, MD.SILL, 1.0, up=False))
    return O._one_piece([sash], parts, op, plug_cs, O.PLUG, vf + 1.8 + rp, -1.0)


def window_belcourt_attic(w=10.0, h=4.6, A=0.8):
    """The Belcourt's frieze windows: oblong lights in a moulded frame, glazed behind a cast
    grille of three rings joined by a bar."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    g = plug_cs.offset(-0.5, JoinType.Miter, 4.0)
    rr = min(h / 2 - 0.6, 1.3)
    rings = cs_union([circle((x, h / 2), rr, 20) - circle((x, h / 2), rr - 0.45, 16) for x in (-w / 4, 0.0, w / 4)] +
                     [rect(-w, h / 2 - 0.22, w, h / 2 + 0.22)])
    sash = _glazed([ext(plug_cs, -pl, -0.6)], g, pl, rings, plug_cs)
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS),
             MD.band(op.offset(A, JoinType.Miter, 4.0), A, MD.ARCHITRAVE, clip=rect(-w - 10, -5, w + 10, h + 10) - op)]
    return O._one_piece(sash, parts, op, plug_cs, pl, h + A, -A)


def window_belcourt_belvedere(w=6.4, h=13.0, A=0.8):
    """The belvedere's windows: a round-headed one-over-one sash in an architrave with a
    keystone."""
    r = w / 2
    op = O.opening_cs(w, h, r)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    sash = O.window_insert(w, h, r, lites=(1, 1), bare=True)["insert"]
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS),
             MD.band(op.offset(A, JoinType.Round), A, MD.ARCHITRAVE, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op),
             MD.scroll_keystone(0.0, h - 0.3, A + 1.2, 1.1, 1.6, 0.0, 1.4)]
    sw = r + A + 0.4
    parts.append(MD.run(-sw, sw, 0.0, MD.SILL, 0.8, up=False))
    return O._one_piece([sash], parts, op, plug_cs, O.PLUG, h + A + 0.9, -0.8)


def door_belcourt(w=13.0, h=27.0, A=1.2):
    """The Belcourt's entrance: a pair of leaves with arched panels under a round fanlight of
    radiating bars, in a moulded architrave with a big keystone, imposts and spandrels under a
    cornice."""
    r = w / 2
    spring = h - r
    op = O.opening_cs(w, h, r)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    mid = 0.5
    lw = (w - 2 * O.CLR - 1.0 - mid) / 2
    dh = spring - 0.4
    body = [ext(plug_cs, -pl, -1.0)]
    u = -w / 2 + O.CLR + 0.5
    for i in range(2):
        body.append(ext(rect(u, 0.5, u + lw, dh), -pl, -0.8))
        pw_ = lw - 1.6
        for vb, vt in ((1.2, dh * 0.38), (dh * 0.38 + 0.8, dh - 0.8)):
            body.append(_panel(cs_union([rect(u + 0.8, vb, u + 0.8 + pw_, vt - pw_ / 2), circle((u + lw / 2, vt - pw_ / 2), pw_ / 2, 24)])))
        u += lw + mid
    fan = plug_cs.offset(-0.5, JoinType.Miter, 4.0) ^ rect(-w, spring + 0.2, w, h + 2)
    rays = cs_union([stroke([(0.0, spring + 0.2), (r * 1.2 * math.cos(a), spring + 0.2 + r * 1.2 * math.sin(a))], 0.45)
                     for a in np.linspace(0.3, math.pi - 0.3, 7)] + [circle((0.0, spring + 0.2), 1.4, 20)])
    sash = _glazed(body, fan, pl, rays, plug_cs)
    sash.append(ext(rect(-w, dh - 0.01, w, spring + 0.2) ^ plug_cs, -pl, -0.5))
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS),
             MD.band(op.offset(A, JoinType.Round), A, MD.ARCHITRAVE, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op)]
    for sg in (-1, 1):
        parts.append(chamfer_box(sg * (r + A / 2) - 1.1, spring - 1.0, sg * (r + A / 2) + 1.1, spring + 0.1, 0.0, 1.4, c=0.3))
    Ro = r + A + 1.4
    half = Ro + 0.6
    vc = spring + Ro + 1.4
    parts.append(ext(rect(-half, spring + 0.1, half, vc - 1.2) - op.offset(A, JoinType.Round), 0.0, 0.6))
    for sg in (-1, 1):
        parts.append(MD.rosette(sg * (Ro - 0.4), vc - 2.4, 0.7, 0.59, 0.6))
    parts.append(MD.scroll_keystone(0.0, h - 0.3, vc - h - 0.2, 1.8, 2.6, 0.0, 2.0))
    parts.append(MD.run(-half - 0.6, half + 0.6, vc, MD.CROWN, 1.4, up=False))
    return O._one_piece(sash, parts, op, plug_cs, pl, vc, 0.0)


def door_belcourt_back(w=10.0, h=24.0, A=1.0):
    """The Belcourt's back door: one leaf with an arched upper panel and a two-light transom, an
    architrave and a cornice cap."""
    transom = 3.4
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    dh = h - transom
    u0, u1 = -w / 2 + O.CLR + 0.5, w / 2 - O.CLR - 0.5
    pw_ = u1 - u0 - 1.6
    body = [ext(plug_cs, -pl, -1.0), ext(rect(u0, 0.5, u1, dh - 0.3), -1.0, -0.8),
            _panel(rect(u0 + 0.8, 1.2, u1 - 0.8, dh * 0.4)),
            _panel(cs_union([rect(u0 + 0.8, dh * 0.4 + 0.8, u1 - 0.8, dh - 1.0 - pw_ / 2), circle((0.0, dh - 1.0 - pw_ / 2), pw_ / 2, 24)]))]
    g = plug_cs.offset(-0.5, JoinType.Miter, 4.0) ^ rect(-w, dh + 0.3, w, h + 2)
    sash = _glazed(body, g, pl, _muntins(g, 2, 1), plug_cs)
    sash.append(ext(rect(-w, dh - 0.3, w, dh + 0.3) ^ plug_cs, -pl, -0.4))
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS),
             MD.band(op.offset(A, JoinType.Miter, 4.0), A, MD.ARCHITRAVE, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op)]
    half = w / 2 + A + 0.4
    vf = h + A
    parts.append(ext(rect(-half, vf - 0.01, half, vf + 1.6), 0.0, 0.6))
    parts.append(MD.run(-half - 0.6, half + 0.6, vf + 1.6 + 1.0, MD.CROWN, 1.2, up=False))
    return O._one_piece(sash, parts, op, plug_cs, pl, vf + 2.6, 0.0)


# ------------------------------------------------------------------ porch
def post_halffluted(h, collar=None, abacus=3.2, slot=(1.2, 1.0)):
    """A column fluted on its lower third only, plain above a ring, under a moulded capital
    (the Belcourt's portico)."""
    z1 = h - 2.8
    r = 1.15
    zf = round((2.2 + (z1 - 2.2) * 0.34) / 0.2) * 0.2
    prof = [(0.0, 1.19), (1.6, 1.19), (1.6, 1.45), (1.4, 1.75), (r, 2.2), (r, zf), (1.32, zf + 0.2), (1.32, zf + 0.5), (r * 0.97, zf + 0.7),
            (r * 0.9, z1), (1.25, z1 + 0.25), (1.25, z1 + 0.55), (r * 0.9, z1 + 0.75)]
    body = PW._revolve(prof, 36) + PW._plinth(3.3)
    fl = union([M.cylinder(zf - 3.0, 0.26, 0.26, 10).translate([r * math.cos(a), r * math.sin(a), 2.6])
                for a in np.linspace(0, 2 * math.pi, 10, endpoint=False)])
    return body - fl + PW._top(h, abacus / 2, z1 + 0.75, r * 0.9, slot, seg=36)


def baluster_doubleball(h, seg=18):
    """A slim baluster with two balls on it, square ends (the Belcourt)."""
    prof = [(0.0, 0.8), (0.3, 0.8), (0.3, h * 0.3), (0.52, h * 0.36), (0.3, h * 0.42), (0.3, h * 0.6), (0.52, h * 0.66),
            (0.3, h * 0.72), (0.3, h - 0.8)]
    return PW._revolve(prof, seg) + box([-0.55, -0.55, 0.0], [0.55, 0.55, 0.81]) + box([-0.55, -0.55, h - 0.81], [0.55, 0.55, h])


def frieze_paterae(u0, u1, v_bot, v_top):
    """A porch frieze: an architrave band with a row of round paterae on the frieze over it
    (the Belcourt)."""
    v0 = v_top - 3.0
    board = rect(u0, v0, u1, v_top + 0.05)
    n = max(2, int((u1 - u0) / 3.0))
    holes = [circle((u0 + (u1 - u0) * (k + 0.5) / n, v0 + 1.9), 0.75, 16) - circle((u0 + (u1 - u0) * (k + 0.5) / n, v0 + 1.9), 0.3, 10)
             for k in range(n)]
    return (board - cs_union(holes)) + rect(u0, v0 - 0.6, u1, v0 + 0.8)


def skirt_louvres(reg, d=1.2):
    """A porch skirt of horizontal louvres between plain stiles (the Belcourt)."""
    u0, v0, u1, v1 = reg.bounds()
    out = M.extrude(reg, d * 0.35)
    slats = cs_union([rect(u0 - 1, v, u1 + 1, v + 0.6) for v in np.arange(v0 + 0.5, v1 - 0.4, 1.1)])
    stiles = cs_union([rect(u, v0 - 1, u + 0.9, v1 + 1) for u in np.arange(u0, u1, 6.0)])
    return out + M.extrude(slats ^ reg, d * 0.75) + M.extrude(stiles ^ reg, d)


def edge_pelletdentil(L, z0, zc):
    """Porch fascia (the Belcourt): dentils with a pellet between each pair."""
    out = [rect(0.3, zc - 0.45, L - 0.3, zc)]
    for x in np.arange(1.0, L - 0.8, 1.6):
        out.append(rect(x - 0.4, zc - 1.2, x + 0.4, zc - 0.4))
        out.append(circle((x + 0.8, zc - 0.85), 0.3, 10))
    return cs_union(out) ^ rect(0.3, zc - 2, L - 0.3, zc + 1), 0.6


CO.FRIEZE_EXTRA.update(squarelinks=frieze_squarelinks, sixfoils=frieze_sixfoils)
CO.COURSE_EXTRA.update(flutecourse=course_flutes)
TW.BRACKET_EXTRA.update(longconsole=bracket_longconsole)
TW.PIERCED = TW.PIERCED + ("longconsole",)
TW.FOUNDATION_EXTRA.update(frostwork=foundation_frostwork)
PW.POSTS.update(halffluted=post_halffluted)
PW.BALUSTERS.update(doubleball=(baluster_doubleball, 1.6))
PW.FRIEZES.update(paterae=frieze_paterae)
PW.SKIRTS.update(louvres=skirt_louvres)
FT.EDGE_EXTRA.update(pelletdentil=edge_pelletdentil)


# ================================================================== the Valcour (house 85)
# Dove-grey rusticated boarding with white trim and navy accents; a convex (swelling) mansard
# of striped slate, a centre pavilion under a taller convex roof, oculus add-ins, a veranda
# down the east side and a stoop under a hooded doorway.

def slate_stripes(k, j):
    """The Valcour's slating: square slates with every fourth column cut to a diamond point,
    so the roof is striped from eave to crest."""
    x = j + 0.5 * (k % 2)
    return "diamond" if abs(x % 4 - 1.0) < 0.3 else "square"


# ------------------------------------------------------------------ cornice ornaments
def frieze_crossedpalms(L, h, b, pitch, margin, pair, half):
    """Crossed palms: in every bay two palm fronds crossed at their stems and tied with a
    knot; a disc at each station (the Valcour's storey joint)."""
    v0, v1 = 0.8, h - 0.8
    hh = v1 - v0
    out = []
    for uc, wd in CO._between(L, pitch, margin, pair, half):
        if wd < 4.0:
            continue
        W = min(wd / 2 - 0.5, hh * 1.2)
        parts = [circle((uc, v0 + 0.6), 0.5, 12)]
        for sg in (-1, 1):
            ts = np.linspace(0.0, 1.0, 12)
            pts = [(uc - sg * 0.6 + sg * W * t, v0 + 0.4 + hh * 0.85 * math.sin(math.pi * 0.5 * t)) for t in ts]
            parts.append(stroke(pts, 0.4))
            for t in np.linspace(0.25, 0.95, 5):
                i = int(t * 11)
                p0 = np.array(pts[i])
                for side in (1, -1):
                    a = (math.pi / 2 if sg > 0 else math.pi / 2) + side * 0.9 - sg * 0.5
                    ln = 1.0 * (1.1 - 0.5 * t)
                    c = p0 + np.array([math.cos(a), math.sin(a)]) * ln * 0.45
                    parts.append(_lens((c[0], c[1]), ln, 0.4, a))
        out.append(_st(cs_union(parts) ^ rect(uc - wd / 2 + 0.2, v0, uc + wd / 2 - 0.2, v1), b, 0.4))
    for u in CO._us(L, pitch, margin, 0.0):
        out.append(_st(circle((u, (v0 + v1) / 2), 0.7, 16) - circle((u, (v0 + v1) / 2), 0.3, 10), b, 0.4))
    return out, []


def frieze_caducei(L, h, b, pitch, margin, pair, half):
    """Caducei: in every bay a staff with two serpents twined round it and a pair of wings at
    its head, a sunk panel either side (the Valcour's eave)."""
    v0, v1 = 0.8, h - 0.8
    hh = v1 - v0
    out, cuts = [], []
    for uc, wd in CO._between(L, pitch, margin, pair, half):
        if wd < 4.4:
            continue
        top = v1 - 0.3
        staff = cs_union([rect(uc - 0.22, v0 + 0.1, uc + 0.22, top - 0.6), circle((uc, top - 0.45), 0.45, 12)])
        snakes = []
        for sg in (-1, 1):
            ts = np.linspace(0.0, 1.0, 16)
            snakes.append(stroke([(uc + sg * 0.6 * math.sin(2.5 * math.pi * t), v0 + 0.4 + (hh * 0.68) * t) for t in ts], 0.36))
        wings = [_lens((uc + sg * 1.0, top - 1.0), 1.9, 0.6, sg * 0.35) for sg in (-1, 1)]
        out.append(_st(cs_union([staff] + snakes + wings), b, 0.45))
        pw = wd / 2 - 2.0
        if pw > 1.0:
            for sg in (-1, 1):
                x0 = uc + sg * 1.9
                pan = rect(min(x0, x0 + sg * pw), v0 + 0.5, max(x0, x0 + sg * pw), v1 - 0.5)
                cuts.append(ext(pan.offset(-0.35, JoinType.Miter, 4.0), b - 0.25, b + 1.0))
    return out, cuts


def course_cusps(L, h, b, pitch, margin, p):
    """A cusped course: a band cut below into a run of small round arches with pointed cusps
    where they meet (the Valcour)."""
    pu = 1.6
    n = max(1, int((L - 0.6) / pu))
    u0 = (L - n * pu) / 2
    band = rect(0.2, 0.0, L - 0.2, h)
    arches = cs_union([circle((u0 + pu * (k + 0.5), 0.0), pu * 0.42, 16) for k in range(n)])
    return [_st(band - arches, b, 0.45)]


def course_tribead(L, h, b, pitch, margin, p):
    """Triple beads: clusters of three beads (two over one) along a fillet (the Valcour)."""
    out = [ext(rect(0.2, 0.0, L - 0.2, 0.4), b - 0.05, b + 0.4)]
    pu = 2.0
    n = max(1, int((L - 0.6) / pu))
    u0 = (L - n * pu) / 2
    r = min(0.4, h * 0.22)
    beads = []
    for k in range(n):
        uc = u0 + pu * (k + 0.5)
        beads += [circle((uc - r * 1.05, h - r - 0.15), r, 10), circle((uc + r * 1.05, h - r - 0.15), r, 10),
                  circle((uc, h - 3 * r - 0.1), r, 10)]
    out.append(_st(cs_union(beads), b, 0.45))
    return out


def tribeads(L, h):
    """The Valcour's crest course as CrossSections: clusters of three beads on a fillet."""
    pu = 2.0
    n = max(1, int((L - 0.6) / pu))
    u0 = (L - n * pu) / 2
    r = min(0.42, h * 0.22)
    beads = [rect(0.2, 0.0, L - 0.2, 0.45)]
    for k in range(n):
        uc = u0 + pu * (k + 0.5)
        beads += [circle((uc - r * 1.05, h - r - 0.15), r, 10), circle((uc + r * 1.05, h - r - 0.15), r, 10),
                  circle((uc, h - 3 * r - 0.1), r, 10), rect(uc - 0.2, 0.3, uc + 0.2, h - 3 * r)]
    return [cs_union(beads)]


def bracket_trefoilconsole(h, d, t):
    """A console whose front is cut in three round lobes, a scroll at its head and a drop at
    its foot (side profile, top at v = 0; the Valcour)."""
    r = min(0.24 * h, 0.3 * d)
    body = poly([(0.0, 0.0), (d, 0.0), (d, -r), (0.6, -h + 0.5), (0.0, -h + 0.5)])
    lobes = [circle((d - r - (d - r - 0.9) * f, -r - (h - r - 1.0) * f), r * 0.8, 14) for f in (0.15, 0.5, 0.85)]
    prof = cs_union([body, circle((d - r, -r), r, 16), circle((0.35, -h + 0.4), 0.4, 12)] + lobes)
    return prof - circle((d - r, -r), r * 0.4, 12)


# ------------------------------------------------------------------ the mansards' window add-ins
def addin_valcour_oculus(r=3.0, A=1.1):
    """A Valcour add-in: a round oculus with a cross of bars in a wreathed frame (a ring of
    leaves), a hood on two scrolls over it and a corbel under it."""
    vc = r + A + 1.6
    light = circle((0.0, vc), r, 40)
    bars = cs_union([rect(-RIB / 2, vc - r - 1, RIB / 2, vc + r + 1), rect(-r - 1, vc - RIB / 2, r + 1, vc + RIB / 2)])
    ring = circle((0.0, vc), r + A, 48)
    parts = [ext(ring.offset(0.5, JoinType.Round) - light, 0.0, 0.6),
             MD.band(light.offset(A, JoinType.Round), A, MD.ARCHITRAVE, clip=rect(-20, -20, 20, 40) - light)]
    leaves = cs_union([_lens(((r + A * 0.5) * math.cos(a), vc + (r + A * 0.5) * math.sin(a)), 1.2, 0.5, a + math.pi / 2)
                       for a in np.linspace(math.pi * 0.05, math.pi * 0.95, 7)])
    parts.append(ext(leaves - light.offset(0.2), 0.59, 1.1))
    vh = vc + r + A + 0.2
    hood = arch_cs(-r - A - 1.0, r + A + 1.0, vh - 0.6, vh, rise=1.4, seg=40)
    parts.append(MD.band(hood, 0.9, MD.CROWN, clip=rect(-20, vh - 0.6, 20, 40)))
    parts.append(ext(hood.offset(-0.7, JoinType.Round) ^ rect(-20, vh - 0.6, 20, 40), 0.0, 0.6))
    for sg in (-1, 1):
        c = (sg * (r + A + 0.5), vh - 0.9)
        parts.append(ext(cs_union([circle(c, 0.75, 16) - circle(c, 0.3, 10), rect(c[0] - 0.4, c[1], c[0] + 0.4, vh - 0.5)]), 0.0, 1.0))
    parts.append(chamfer_box(-1.6, 0.0, 1.6, vc - r - A + 0.4, 0.0, 1.2, c=0.3))
    parts.append(MD.pendant(0.0, 0.2, 1.8, 0.0, 0.8))
    parts = [p - ext(light, -1.0, 5.0) for p in parts]
    outline = (circle((0.0, vc), r + A + 0.3, 48) + rect(-1.6, 0.6, 1.6, vc)) ^ rect(-50, 0.6, 50, 100)
    return dict(light=light, bars=bars, frame=parts, outline=outline, top=vh + 1.4, bottom=-1.6)


def addin_valcour_big(w=7.0, h=13.0, A=1.0):
    """The Valcour pavilion's add-in: a round-headed two-over-two light between little scrolled
    pilasters, under a broken scroll pediment with a ball in the break."""
    r = w / 2
    spring = h - r
    op = O.opening_cs(w, h, r)
    bars = cs_union([rect(-RIB / 2, -1.0, RIB / 2, h + 1.0), rect(-w, spring * 0.55 - 0.3, w, spring * 0.55 + 0.3)])
    half = r + A + 1.2
    vt = spring + r + A
    body = cs_union([rect(-half, -0.2, half, vt + 1.0)])
    parts = [ext(body - op, 0.0, 0.6), MD.band(op.offset(A, JoinType.Round), A, MD.ARCHITRAVE, clip=rect(-20, 0.0, 20, 40) - op)]
    for sg in (-1, 1):
        u0, u1 = sorted((sg * (r + A), sg * half))
        parts.append(ext(rect(u0, 0.0, u1, spring), 0.0, 1.0))
        c = ((u0 + u1) / 2, spring + 0.6)
        parts.append(ext(circle(c, 0.8, 16) - circle(c, 0.3, 10), 0.0, 1.2))
    parts.append(MD.run(-half - 0.4, half + 0.4, vt + 1.0, MD.CROWN, 1.0, up=False))
    for sg in (-1, 1):
        pts = [(sg * (half + 0.3), vt + 1.0), (sg * (half - 0.4), vt + 2.6), (sg * 1.4, vt + 3.4)]
        parts.append(ext(stroke(pts, 0.8), 0.0, 1.1))
        parts.append(ext(circle((sg * 1.3, vt + 3.0), 0.6, 14) - circle((sg * 1.3, vt + 3.0), 0.2, 8), 0.0, 1.2))
    parts.append(ext(circle((0.0, vt + 2.6), 0.9, 18), 0.0, 1.2))
    parts.append(ext(rect(-0.6, vt + 0.99, 0.6, vt + 2.0), 0.0, 1.0))
    sw = half + 0.3
    parts.append(MD.run(-sw, sw, 0.0, MD.SILL, 1.0, up=False))
    parts.append(chamfer_box(-1.6, -2.0, 1.6, -0.8, 0.0, 1.0, c=0.3))
    parts = [p - ext(op, -1.0, 5.0) for p in parts]
    outline = body.offset(-0.4, JoinType.Miter, 4.0) ^ rect(-50, 0.4, 50, 100)
    return dict(light=op, bars=bars, frame=parts, outline=outline, top=vt + 3.6, bottom=-2.0)


# ------------------------------------------------------------------ walls, corners, foundation, chimney
def rusticboard(region, datum=0.0, course=2.6, block=6.4, groove=0.45, d=0.32):
    """Rusticated boarding: wide boards cut to look like stone, every course and every block
    joint a bevelled V-groove, the blocks broken half a block course to course (the Valcour)."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    cells = []
    k = math.floor((v0 - datum) / course) - 1
    while datum + k * course < v1:
        v = datum + k * course
        u = u0 - block * 2 + (k % 2) * block / 2
        while u < u1 + block:
            cells.append(rect(u + groove / 2, v + groove / 2, u + block - groove / 2, v + course - groove / 2))
            u += block
        k += 1
    cs = cs_union(cells) ^ region
    return ext(cs, 0.0, d - 0.15) + ext(cs.offset(-0.15, JoinType.Miter, 4.0), d - 0.16, d)


def corner_rusticpier(L, at_start, qa, qb, w=2.4, t=0.65):
    """Corner piers of rusticated boarding: a board 2.8 wide standing 0.7 proud, cut into
    blocks by deep V-grooves, a plinth at its foot (the Valcour)."""
    def span(a, b):
        return (a, b) if at_start else (L - b, L - a)
    u0, u1 = span(-t - 0.1, 2.8)
    parts = [box([u0, qa, 0.0], [u1, qb, t + 0.1])]
    for v in np.arange(qa + 2.6, qb - 0.5, 2.6):
        a, b = span(-t - 0.6, 3.4)
        parts_cut = M.hull_points([(x, v - 0.3, t + 0.2) for x in (a, b)] + [(x, v + 0.3, t + 0.2) for x in (a, b)] +
                                  [(x, v, t - 0.25) for x in (a, b)])
        parts[0] = parts[0] - parts_cut
    p0, p1 = span(-t - 0.4, 3.2)
    parts.append(chamfer_box(p0, qa, p1, qa + 1.6, 0.0, t + 0.4, c=0.3, square=("u0",) if at_start else ("u1",)))
    return union(parts)


def foundation_brickpanel(reg, seed=0):
    """A brick foundation laid in sunk panels between plain piers, a stone cap course along its
    top (the Valcour)."""
    from . import skins as SK
    b = reg.bounds()
    out = [M.extrude(reg, 0.45)]
    cap = rect(b[0] - 1, b[3] - 1.6, b[2] + 1, b[3] + 1) ^ reg
    out.append(ext(cap, 0.44, 0.75))
    for u in np.arange(b[0] + 1.0, b[2] - 6.0, 14.0):
        pan = rect(u + 2.4, b[1] + 1.2, u + 12.6, b[3] - 2.4) ^ reg
        if not pan.is_empty():
            out[0] = out[0] - ext(pan, 0.25, 1.0)
            out.append(SK.brick_bond(pan, "running", bl=2.0, bh=0.8, d=0.2).translate([0, 0, 0.2]))
    return union(out)


def chimney_valcour(w=9.6, d=12.0, h=24.0):
    """The Valcour's stacks: brick with a recessed panel down each broad face, a stone band,
    an oversailing cap of four courses and three square pots in a row."""
    h = round(h / 0.2) * 0.2
    sh = h - 4.2
    body = box([-w / 2, -d / 2, 0.0], [w / 2, d / 2, sh])
    for sx in (-1, 1):
        T = np.array([[0, 0, sx * 1.0, sx * w / 2], [1.0, 0, 0, 0], [0, 1.0, 0, 0]])
        pan = rect(-d / 2 + 1.6, 3.0, d / 2 - 1.6, sh - 4.0)
        body = body - (ext(pan, -0.5, 1.0) if sx > 0 else ext(pan, -1.0, 0.5)).transform(T)
    body = body + box([-w / 2 - 0.4, -d / 2 - 0.4, sh - 3.2], [w / 2 + 0.4, d / 2 + 0.4, sh - 2.2])
    for k in range(4):
        g = 0.25 * (k + 1)
        body = body + box([-w / 2 - g, -d / 2 - g, sh + 0.5 * k - 0.01], [w / 2 + g, d / 2 + g, sh + 0.5 * (k + 1)])
    zc = sh + 2.0
    for y in (-d / 3, 0.0, d / 3):
        body = body + box([-1.2, y - 1.2, zc - 0.01], [1.2, y + 1.2, zc + 2.0]) + box([-1.4, y - 1.4, zc + 1.6], [1.4, y + 1.4, zc + 2.2])
    return body - union([box([-0.6, y - 0.6, sh - 3.0], [0.6, y + 0.6, zc + 3.0]) for y in (-d / 3, 0.0, d / 3)])


def fence_valcour(L, h):
    """Valcour cresting: lozenges standing on their points between spiked bars, a ball on each
    lozenge."""
    pitch = 3.0
    n = max(1, int(round(L / pitch)))
    p = L / n
    cells = [rect(0.0, 0.0, L, 0.6)]
    for j in range(n + 1):
        u = p * j
        cells.append(rect(u - 0.28, 0.0, u + 0.28, h - 0.8))
        cells.append(poly([(u - 0.45, h - 0.9), (u + 0.45, h - 0.9), (u, h)]))
        if j < n:
            m = u + p / 2
            hz = h * 0.42
            loz = poly([(m, 0.55), (m + p / 2 - 0.35, hz), (m, 2 * hz - 0.55), (m - p / 2 + 0.35, hz)])
            cells.append(loz - loz.offset(-0.45, JoinType.Miter, 4.0))
            cells.append(circle((m, 2 * hz - 0.2), 0.42, 12))
    return cs_union(cells) ^ rect(0.0, 0.0, L, h + 1.0)


def finial_urnspike(h=9.0):
    """An iron finial: a little urn on a turned stem with a long spike (the Valcour's
    pavilion)."""
    prof = [(0.0, 0.0), (1.3, 0.0), (1.3, 0.7), (0.6, 1.2), (0.55, 2.4), (1.0, 2.8), (1.2, 3.6), (1.0, 4.4), (0.6, 4.8),
            (0.8, 5.0), (0.0, 5.0)]
    return PW._revolve(prof, 24) + M.cylinder(h - 4.8, 0.4, 0.1, 12).translate([0, 0, 4.8])


# ------------------------------------------------------------------ windows and doors
def window_valcour_lower(w=9.6, h=22.0, rise=2.0, A=1.0):
    """Valcour ground floor: a segmental-headed two-over-two sash in an architrave with a
    keyed segmental head, a frieze of triglyph blocks, a cornice cap with a little crest of a
    ball between scrolls, a sill on two blocks."""
    op = O.opening_cs(w, h, rise)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    sash = O.window_insert(w, h, rise, lites=(2, 2), bare=True)["insert"]
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS),
             MD.band(op.offset(A, JoinType.Miter, 4.0), A, MD.ARCHITRAVE, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op),
             MD.scroll_keystone(0.0, h - 0.3, A + 1.4, 1.3, 1.9, 0.0, 1.7)]
    half = w / 2 + A + 0.8
    vf = h + A + 0.2
    parts.append(ext(rect(-half, h - rise, half, vf) - op.offset(A, JoinType.Miter, 4.0), 0.0, 0.6))
    parts.append(ext(rect(-half, vf - 0.01, half, vf + 1.8), 0.0, 0.6))
    for x in np.linspace(-half + 1.0, half - 1.0, 5):
        if abs(x) < 1.2:
            continue
        parts.append(ext(rect(x - 0.45, vf + 0.2, x + 0.45, vf + 1.6), 0.59, 1.0))
    vc = vf + 1.8 + 1.0
    parts.append(MD.run(-half - 0.6, half + 0.6, vc, MD.CROWN, 1.2, up=False))
    crest = [rect(-2.4, vc - 0.01, 2.4, vc + 0.4), circle((0.0, vc + 0.95), 0.7, 16)]
    for sg in (-1, 1):
        crest.append(stroke([(sg * 0.5, vc + 0.3), (sg * 1.6, vc + 1.0), (sg * 2.3, vc + 0.5)], 0.45))
    parts.append(ext(cs_union(crest), 0.0, 0.9))
    sw = w / 2 + A + 0.4
    parts.append(MD.run(-sw, sw, 0.0, MD.SILL, 1.0, up=False))
    for sg in (-1, 1):
        parts.append(chamfer_box(sg * (w / 2) - 0.7, -2.0, sg * (w / 2) + 0.7, -0.8, 0.0, 0.9, c=0.25))
    return O._one_piece([sash], parts, op, plug_cs, O.PLUG, vc + 1.8, -2.0)


def window_valcour_upper(w=9.0, h=20.0, A=0.9):
    """Valcour upper floor: a round-headed two-over-two sash in an architrave whose head
    rises into an ogee point with a knob, label stops at the spring line."""
    r = w / 2
    spring = h - r
    op = O.opening_cs(w, h, r)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    sash = O.window_insert(w, h, r, lites=(2, 2), bare=True)["insert"]
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS),
             MD.band(op.offset(A, JoinType.Round), A, MD.ARCHITRAVE, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op)]
    R0 = r + A + 0.1
    ts = np.linspace(0.0, 1.0, 14)
    left = [(-R0 * math.cos(t * math.pi / 2), spring + R0 * math.sin(t * math.pi / 2) + 1.6 * t ** 3) for t in ts]
    right = [(-x, y) for x, y in reversed(left)]
    curve = left + [(0.0, spring + R0 + 2.4)] + right
    parts.append(ext(stroke(curve, 1.0), 0.0, 1.2))
    parts.append(ext(circle((0.0, spring + R0 + 2.6), 0.6, 14), 0.0, 1.3))
    for sg in (-1, 1):
        parts.append(chamfer_box(sg * R0 - 0.7, spring - 1.2, sg * R0 + 0.7, spring + 0.2, 0.0, 1.3, c=0.3))
    sw = r + A + 0.5
    parts.append(MD.run(-sw, sw, 0.0, MD.SILL, 1.0, up=False))
    return O._one_piece([sash], parts, op, plug_cs, O.PLUG, spring + R0 + 3.2, -1.0)


def door_valcour(w=12.4, h=27.0, A=1.2):
    """The Valcour's entrance: a pair of leaves with long arched lights over square panels,
    a transom with a ring of bars, in an architrave under a deep hood on two long scroll
    brackets."""
    transom = 4.4
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    mid = 0.5
    lw = (w - 2 * O.CLR - 1.0 - mid) / 2
    dh = h - transom
    body, lights = [ext(plug_cs, -pl, -1.0)], []
    u = -w / 2 + O.CLR + 0.5
    for i in range(2):
        body.append(ext(rect(u, 0.5, u + lw, dh), -pl, -0.8))
        gw = lw - 1.6
        gv0 = dh * 0.4
        lights.append(cs_union([rect(u + 0.8, gv0, u + 0.8 + gw, dh - 0.8 - gw / 2), circle((u + lw / 2, dh - 0.8 - gw / 2), gw / 2, 24)]))
        body.append(_panel(rect(u + 0.8, 1.2, u + lw - 0.8, gv0 - 0.8)))
        u += lw + mid
    tr = plug_cs.offset(-0.5, JoinType.Miter, 4.0) ^ rect(-w, dh + 0.4, w, h + 2)
    tc = (0.0, (dh + 0.4 + h - 0.6) / 2)
    ringbars = cs_union([circle(tc, 1.4, 20) - circle(tc, 0.95, 16), rect(-w, tc[1] - 0.22, w, tc[1] + 0.22)])
    sash = _glazed(body, cs_union(lights) + tr, pl, ringbars, plug_cs)
    sash.append(ext(rect(-w, dh - 0.01, w, dh + 0.4) ^ plug_cs, -pl, -0.5))
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS),
             MD.band(op.offset(A, JoinType.Miter, 4.0), A, MD.ARCHITRAVE, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op)]
    half = w / 2 + A + 2.2
    vf = h + A
    for sg in (-1, 1):
        parts.append(console(8.0, 3.0, 1.4, u=sg * (w / 2 + A + 1.0), v_top=vf + 1.6, w0=0.0))
    parts.append(ext(rect(-half + 0.6, vf - 0.01, half - 0.6, vf + 1.6), 0.0, 0.6))
    parts.append(MD.rosette(0.0, vf + 0.8, 0.6, 0.59, 0.5))
    vc = vf + 1.6 + 1.6
    parts.append(MD.run(-half - 1.0, half + 1.0, vc, MD.CROWN, 1.8, up=False))
    parts.append(ext(rect(-half + 0.4, vc - 0.01, half - 0.4, vc + 0.8), 0.0, 1.2))
    return O._one_piece(sash, parts, op, plug_cs, pl, vc + 0.8, 0.0)


def door_valcour_side(w=10.0, h=24.0, A=1.0):
    """The Valcour's side and back doors: one leaf with an arched light over a panel, a plain
    transom, an architrave and a cornice cap."""
    transom = 3.4
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    dh = h - transom
    u0, u1 = -w / 2 + O.CLR + 0.5, w / 2 - O.CLR - 0.5
    gw = u1 - u0 - 1.6
    gv0 = dh * 0.42
    body = [ext(plug_cs, -pl, -1.0), ext(rect(u0, 0.5, u1, dh), -pl, -0.8), _panel(rect(u0 + 0.8, 1.2, u1 - 0.8, gv0 - 0.8))]
    light = cs_union([rect(u0 + 0.8, gv0, u1 - 0.8, dh - 0.8 - gw / 2), circle((0.0, dh - 0.8 - gw / 2), gw / 2, 24)])
    g = plug_cs.offset(-0.5, JoinType.Miter, 4.0) ^ rect(-w, dh + 0.3, w, h + 2)
    sash = _glazed(body, light + g, pl, None, plug_cs)
    sash.append(ext(rect(-w, dh - 0.3, w, dh + 0.3) ^ plug_cs, -pl, -0.4))
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS),
             MD.band(op.offset(A, JoinType.Miter, 4.0), A, MD.ARCHITRAVE, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op)]
    half = w / 2 + A + 0.4
    vf = h + A
    parts.append(ext(rect(-half, vf - 0.01, half, vf + 1.6), 0.0, 0.6))
    parts.append(MD.run(-half - 0.6, half + 0.6, vf + 1.6 + 1.0, MD.CROWN, 1.2, up=False))
    return O._one_piece(sash, parts, op, plug_cs, pl, vf + 2.6, 0.0)


# ------------------------------------------------------------------ porch
def post_spiralflute(h, collar=None, abacus=3.0, slot=(1.2, 1.0)):
    """A round post with spiral flutes on its middle third between plain lengths and rings,
    on a plinth, under a moulded capital (the Valcour's veranda)."""
    z1 = h - 2.6
    r = 1.05
    za = round((2.0 + (z1 - 2.0) * 0.33) / 0.2) * 0.2
    zb = round((2.0 + (z1 - 2.0) * 0.67) / 0.2) * 0.2
    prof = [(0.0, 1.19), (1.55, 1.19), (1.55, 1.45), (1.3, 1.7), (r, 2.0), (r, za - 0.4), (1.25, za - 0.2), (1.25, za),
            (r, za + 0.2), (r, zb - 0.2), (1.25, zb), (1.25, zb + 0.2), (r, zb + 0.4), (r * 0.94, z1), (1.2, z1 + 0.25),
            (1.2, z1 + 0.5), (r * 0.94, z1 + 0.7)]
    body = PW._revolve(prof, 32) + PW._plinth(3.0)
    groove = M.extrude(circle((r, 0.0), 0.24, 10), zb - za - 0.6, int((zb - za) / 0.2), 180.0).translate([0, 0, za + 0.3])
    grooves = union([groove.rotate([0, 0, a]) for a in np.linspace(0, 360, 6, endpoint=False)])
    return body - grooves + PW._top(h, abacus / 2, z1 + 0.7, r * 0.94, slot, seg=32)


def fill_lozengesplats(L, vb, vt):
    """A railing of sawn splats: a lozenge ring between stiles in every bay (the Valcour)."""
    H = vt - vb
    n = max(1, int(round(L / 2.8)))
    parts = []
    for i in range(n + 1):
        x = L * i / n
        parts.append(rect(x - 0.3, vb, x + 0.3, vt))
        if i < n:
            m = x + L / n / 2
            hw = L / n / 2 - 0.2              # its points run into the stiles and the rails, its ring 0.7 wide:
            loz = poly([(m, vb - 0.3), (m + hw, vb + H / 2), (m, vt + 0.3), (m - hw, vb + H / 2)])    # whole in a one-piece top
            parts.append(loz - loz.offset(-0.7, JoinType.Miter, 4.0))
    return [cs_union(parts) ^ rect(0.0, vb, L, vt)]


def frieze_scallopvalance(u0, u1, v_bot, v_top):
    """A porch frieze: a valance board cut below in scallops, each pierced with a round hole
    (the Valcour)."""
    v0 = v_top - 2.8
    n = max(2, int((u1 - u0) / 2.6))
    p = (u1 - u0) / n
    board = rect(u0, v0 + 0.6, u1, v_top + 0.05)
    scal = cs_union([circle((u0 + p * (k + 0.5), v0 + 0.8), p * 0.48, 18) for k in range(n)]) ^ rect(u0, v0 - 1.0, u1, v0 + 0.8)
    holes = cs_union([circle((u0 + p * (k + 0.5), v0 + 1.4), 0.35, 10) for k in range(n)])
    return (board + scal) - holes


def skirt_crossbuck(reg, d=1.2):
    """A porch skirt of crossbuck panels: an X of boards in every panel between plain stiles
    (the Valcour)."""
    u0, v0, u1, v1 = reg.bounds()
    out = M.extrude(reg, d * 0.4)
    n = max(1, int((u1 - u0) / 5.0))
    xs = []
    for j in range(n):
        a, b_ = u0 + (u1 - u0) * j / n, u0 + (u1 - u0) * (j + 1) / n
        xs += [rect(a, v0 - 1, a + 0.8, v1 + 1), stroke([(a + 0.6, v0 + 0.4), (b_ - 0.6, v1 - 0.4)], 0.6),
               stroke([(a + 0.6, v1 - 0.4), (b_ - 0.6, v0 + 0.4)], 0.6)]
    return out + M.extrude(cs_union(xs) ^ reg, d)


def edge_bellcourse(L, z0, zc):
    """Porch fascia (the Valcour): little bells hung under the crown."""
    out = [rect(0.3, zc - 0.45, L - 0.3, zc)]
    for x in np.arange(1.2, L - 0.8, 2.4):
        out.append(poly([(x - 0.25, zc - 0.4), (x + 0.25, zc - 0.4), (x + 0.55, zc - 1.3), (x - 0.55, zc - 1.3)]))
        out.append(circle((x, zc - 1.45), 0.25, 8))
    return cs_union(out), 0.6


CO.FRIEZE_EXTRA.update(crossedpalms=frieze_crossedpalms, caducei=frieze_caducei)
CO.COURSE_EXTRA.update(cusps=course_cusps, tribead=course_tribead)
TW.BRACKET_EXTRA.update(trefoilconsole=bracket_trefoilconsole)
TW.PIERCED = TW.PIERCED + ("trefoilconsole",)
SH.CORNER_EXTRA.update(rusticpier=corner_rusticpier)
TW.FOUNDATION_EXTRA.update(brickpanel=foundation_brickpanel)
PW.POSTS.update(spiralflute=post_spiralflute)
PW.FILLS.update(lozengesplats=fill_lozengesplats)
PW.FRIEZES.update(scallopvalance=frieze_scallopvalance)
PW.SKIRTS.update(crossbuck=skirt_crossbuck)
FT.EDGE_EXTRA.update(bellcourse=edge_bellcourse)


# ================================================================== the Chevalier (house 86)
# Fawn cove-lap siding over a vertical-board wainscot at the foot of each storey, chocolate trim
# and teal accents; a straight mansard of red slate with a chevron band; ogee-capped add-ins;
# two-storey canted bays under crested decks; a porch round the front-east corner.

def slate_chevron(k, j):
    """The Chevalier's slating: square slates with a chevron band of diamond-cut ones zigzagging
    across the middle of the roof."""
    r = k % 18 - 6
    if 0 <= r <= 4:
        x = (j + 0.5 * (k % 2)) % 8
        if abs(min(x, 8 - x) - r * 0.5 - 0.5) < 0.3 or abs(min(x, 8 - x) - r * 0.5 - 1.5) < 0.3:
            return "diamond"
    return "square"


# ------------------------------------------------------------------ cornice ornaments
def frieze_swallows(L, h, b, pitch, margin, pair, half):
    """Swallows: in every bay two swallows in flight, swept wings and forked tails, a dot
    between them (the Chevalier's storey joint)."""
    v0, v1 = 0.8, h - 0.8
    hh = v1 - v0
    out = []
    for uc, wd in CO._between(L, pitch, margin, pair, half):
        if wd < 4.4:
            continue
        for sg, dv in ((-1, 0.2), (1, -0.2)):
            x, y = uc + sg * wd * 0.22, v0 + hh / 2 + dv * hh
            s = min(1.0, hh / 3.2)
            body = _lens((x, y), 1.8 * s, 0.6 * s, 0.15 * sg)
            wings = [_lens((x - 0.2 * s, y + 0.55 * s), 2.0 * s, 0.45 * s, 0.9), _lens((x + 0.2 * s, y + 0.5 * s), 2.0 * s, 0.45 * s, 2.25)]
            tail = [_lens((x - sg * 0.95 * s, y - 0.25 * s), 1.0 * s, 0.3 * s, math.pi + sg * 0.5),
                    _lens((x - sg * 0.95 * s, y + 0.1 * s), 1.0 * s, 0.3 * s, math.pi - sg * 0.2)]
            out.append(_st(cs_union([body] + wings + tail), b, 0.4))
        out.append(_st(circle((uc, v0 + hh / 2), 0.4, 10), b, 0.4))
    return out, []


def frieze_peltae(L, h, b, pitch, margin, pair, half):
    """Peltae: a running band of crescent shields (each a crescent with a knob in its hollow)
    joined horn to horn (the Chevalier's eave)."""
    v0, v1 = 0.8, h - 0.8
    hh = v1 - v0
    vm = (v0 + v1) / 2
    R_ = min(hh * 0.42, 2.4)
    pu = R_ * 2.4
    n = max(1, int((L - 1.0) / pu))
    u0 = (L - n * pu) / 2
    out = []
    for k in range(n):
        uc = u0 + pu * (k + 0.5)
        cres = circle((uc, vm), R_, 32) - circle((uc, vm + R_ * 0.55), R_ * 0.85, 32)
        out.append(_st(cres, b, 0.45))
        out.append(_st(circle((uc, vm + R_ * 0.25), R_ * 0.28, 12), b, 0.55))
    out.append(_st(rect(u0, vm - 0.2, u0 + n * pu, vm + 0.2), b, 0.3))
    return out, []


def course_hexchain(L, h, b, pitch, margin, p):
    """A chain of hexagon links along the course (the Chevalier)."""
    pu = max(1.8, h * 1.15)
    n = max(1, int((L - 0.6) / pu))
    u0 = (L - n * pu) / 2
    r = min(h / 2 - 0.05, pu * 0.55)
    links = []
    for k in range(n):
        uc = u0 + pu * (k + 0.5)
        hx = poly([(uc + r * math.cos(a), h / 2 + r * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 6, endpoint=False)])
        links.append(hx - hx.offset(-0.45, JoinType.Miter, 4.0))
    return [_st(cs_union(links), b, 0.45)]


def hexlinks(L, h):
    """The Chevalier's crest course as CrossSections: a chain of hexagon links on a fillet."""
    pu = max(1.8, h * 1.15)
    n = max(1, int((L - 0.6) / pu))
    u0 = (L - n * pu) / 2
    r = min(h / 2 - 0.05, pu * 0.55)
    links = [rect(0.2, h / 2 - 0.25, L - 0.2, h / 2 + 0.25)]
    for k in range(n):
        uc = u0 + pu * (k + 0.5)
        hx = poly([(uc + r * math.cos(a), h / 2 + r * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 6, endpoint=False)])
        links.append(hx - hx.offset(-0.45, JoinType.Miter, 4.0))
    return [cs_union(links)]


def bracket_fantail(h, d, t):
    """A fan-tail bracket: a sawn console whose foot spreads in three round fingers, a sunk eye
    in its head (side profile, top at v = 0; the Chevalier)."""
    body = poly([(0.0, 0.0), (d, 0.0), (d, -0.8), (d * 0.45, -h * 0.55), (0.6, -h + 1.4), (0.0, -h + 1.4)])
    fingers = [circle((0.5 + 0.55 * k, -h + 1.0 - 0.15 * k), 0.5, 12) for k in range(3)]
    prof = cs_union([body] + fingers)
    return prof - circle((d * 0.62, -h * 0.22), min(0.55, d * 0.15), 12)


# ------------------------------------------------------------------ the mansard's window add-ins
def addin_chevalier(w=5.4, h=10.6, A=0.9):
    """A Chevalier add-in: a round-headed two-over-two light in an architrave under an ogee
    (onion) hood rising to a knob, its plug's roof the same ogee, a sill on a corbel."""
    r = w / 2
    spring = h - r
    op = O.opening_cs(w, h, r)
    bars = cs_union([rect(-RIB / 2, -1.0, RIB / 2, h + 1.0), rect(-w, spring * 0.55 - 0.3, w, spring * 0.55 + 0.3)])
    half = r + A + 0.9
    ts = np.linspace(0.0, 1.0, 16)
    ogee = [(-half + (half) * t, spring + (h - spring + A + 2.6) * (3 * t * t - 2 * t ** 3) + 0.6 * math.sin(math.pi * t)) for t in ts]
    shape = poly([(-half, -0.2)] + ogee + [(-x, y) for x, y in reversed(ogee[:-1])] + [(half, -0.2)])
    parts = [ext(shape - op, 0.0, 0.6), MD.band(op.offset(A, JoinType.Round), A, MD.ARCHITRAVE, clip=rect(-20, 0.0, 20, 40) - op)]
    rim = shape - shape.offset(-0.7, JoinType.Round)
    parts.append(ext(rim ^ rect(-20, spring - 0.5, 20, 40), 0.0, 1.1))
    vt = ogee[-1][1]
    parts.append(ext(circle((0.0, vt + 0.5), 0.6, 14), 0.0, 1.2))
    for sg in (-1, 1):
        parts.append(chamfer_box(sg * half - 0.55, spring - 1.2, sg * half + 0.55, spring, 0.0, 1.2, c=0.3))
    sw = half + 0.3
    parts.append(MD.run(-sw, sw, 0.0, MD.SILL, 1.0, up=False))
    parts.append(chamfer_box(-1.4, -2.0, 1.4, -0.8, 0.0, 1.0, c=0.3))
    parts = [p - ext(op, -1.0, 5.0) for p in parts]
    outline = shape.offset(-0.4, JoinType.Round) ^ rect(-50, 0.4, 50, 100)
    return dict(light=op, bars=bars, frame=parts, outline=outline, top=vt + 1.1, bottom=-2.0)


# ------------------------------------------------------------------ walls, foundation, chimney
def wainscotlap(region, datum=0.0, rail=11.0, pitch=1.3, d=0.32, bv=1.6):
    """Siding of two kinds in every storey: a wainscot of vertical V-jointed boards up to a
    capped rail ``rail`` above the storey's foot, rebated lap above it (each board a flat band
    at its butt, then a bevel) (the Chevalier). ``datum`` is the storey's foot."""
    from . import skins as SK
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    low = region ^ rect(u0 - 1, datum - 1, u1 + 1, datum + rail)
    up = region ^ rect(u0 - 1, datum + rail + 0.8, u1 + 1, v1 + 1)
    out = []
    if not low.is_empty():
        boards = cs_union([rect(u + 0.22, datum - 1, u + bv - 0.22, datum + rail) for u in np.arange(u0 - 1, u1 + 1, bv)])
        out.append(ext(low, 0.0, 0.15) + ext(boards ^ low, 0.14, d))
    capr = region ^ rect(u0 - 1, datum + rail - 0.01, u1 + 1, datum + rail + 0.8)
    if not capr.is_empty():
        out.append(ext(capr, 0.0, d + 0.3))
    if not up.is_empty():
        # rebated lap: each board a flat band at its butt, then a long bevel up to the next
        out.append(SK._lap(up, pitch, [(0.0, d), (0.3, d), (0.42, d - 0.12), (pitch - 0.05, 0.06), (pitch, 0.06)],
                           datum=datum + rail + 0.8))
    return union(out)


def foundation_herringstone(reg, seed=0):
    """Thin stones laid in herringbone courses between plain bands, a dressed cap course (the
    Chevalier)."""
    b = reg.bounds()
    out = [M.extrude(reg, 0.3)]
    cap = rect(b[0] - 1, b[3] - 1.4, b[2] + 1, b[3] + 1) ^ reg
    out.append(ext(cap, 0.29, 0.7))
    v = b[1] + 0.4
    k = 0
    while v < b[3] - 3.0:
        hh = min(3.2, b[3] - 1.6 - v)
        band = rect(b[0] - 1, v, b[2] + 1, v + hh) ^ reg
        st = []
        for u in np.arange(b[0] - 4, b[2] + 4, 1.4):
            ang = 0.785 if k % 2 == 0 else -0.785
            c = (u, v + hh / 2)
            st.append(stroke([(c[0] - 1.4 * math.cos(ang), c[1] - 1.4 * math.sin(ang)), (c[0] + 1.4 * math.cos(ang), c[1] + 1.4 * math.sin(ang))], 0.6))
        out.append(ext(cs_union(st) ^ band.offset(-0.3, JoinType.Miter, 4.0), 0.29, 0.6))
        v += hh + 0.6
        k += 1
    return union(out)


def chimney_chevalier(w=12.0, d=8.0, h=24.0):
    """The Chevalier's stacks: two square brick shafts on a common base, joined at the top by a
    round arch under a shared corbelled cap."""
    h = round(h / 0.2) * 0.2
    sh = h - 3.0
    s = 4.0
    body = box([-w / 2, -d / 2, 0.0], [w / 2, d / 2, 6.0])
    for sx in (-1, 1):
        body = body + box([sx * (w / 2 - s / 2) - s / 2, -s / 2, 5.99], [sx * (w / 2 - s / 2) + s / 2, s / 2, sh])
    arch = (rect(-w / 2, sh - 4.0, w / 2, sh) - circle((0.0, sh - 4.0), w / 2 - s, 24))
    body = body + ext(arch, -s / 2, s / 2).transform(np.array([[1.0, 0, 0, 0], [0, 0, 1.0, 0], [0, 1.0, 0, 0]]))
    for k, g in enumerate((0.3, 0.6)):
        body = body + box([-w / 2 - g, -s / 2 - g, sh + 0.6 * k - 0.01], [w / 2 + g, s / 2 + g, sh + 0.6 * (k + 1)])
    body = body + box([-w / 2 - 0.9, -s / 2 - 0.9, sh + 1.19], [w / 2 + 0.9, s / 2 + 0.9, sh + 1.8])
    return body - union([M.cylinder(h, 0.7, 0.7, 12).translate([sx * (w / 2 - s / 2), 0, 2.0]) for sx in (-1, 1)])


def fence_chevalier(L, h):
    """Chevalier cresting: inverted hearts on the rail between spear-headed bars."""
    pitch = 2.8
    n = max(1, int(round(L / pitch)))
    p = L / n
    rail = h * 0.3
    cells = [rect(0.0, 0.0, L, 0.6), rect(0.0, rail, L, rail + 0.45)]
    for j in range(n + 1):
        u = p * j
        cells.append(rect(u - 0.28, 0.0, u + 0.28, h - 0.8))
        cells.append(poly([(u - 0.45, h - 0.9), (u + 0.45, h - 0.9), (u, h)]))
        if j < n:
            m = u + p / 2
            rr = min(0.5, p / 4 - 0.1)
            vt = h - 1.0
            heart = cs_union([circle((m - rr * 0.8, vt - rr), rr, 12), circle((m + rr * 0.8, vt - rr), rr, 12),
                              poly([(m - rr * 1.7, vt - rr), (m + rr * 1.7, vt - rr), (m, rail + 0.4)])])
            cells.append(heart - heart.offset(-0.46))
            cells.append(rect(m - 0.23, rail + 0.3, m + 0.23, rail + 0.9))
    return cs_union(cells) ^ rect(0.0, 0.0, L, h + 1.0)


# ------------------------------------------------------------------ windows and doors
def window_chevalier_lower(w=9.4, h=21.0, A=1.1):
    """Chevalier ground floor: a flat-headed two-over-two sash in a casing with corner blocks
    carrying roundels, a cornice cap on two little brackets with a sawn crest of lozenges."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    sash = O.window_insert(w, h, 0, lites=(2, 2), bare=True)["insert"]
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS),
             MD.band(op.offset(A, JoinType.Miter, 4.0), A, MD.CASING, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op)]
    for sg in (-1, 1):
        c = (sg * (w / 2 + A / 2), h + A / 2)
        parts.append(chamfer_box(c[0] - A / 2 - 0.2, c[1] - A / 2 - 0.2, c[0] + A / 2 + 0.2, c[1] + A / 2 + 0.2, 0.0, 1.1, c=0.2))
        parts.append(ext(circle(c, 0.5, 14) - circle(c, 0.2, 8), 1.09, 1.4))
    half = w / 2 + A + 0.6
    vf = h + A + 0.2
    for sg in (-1, 1):
        parts.append(console(2.0, 1.0, 0.9, u=sg * (half - 0.5), v_top=vf + 1.6, w0=0.0))
    parts.append(ext(rect(-half + 0.9, vf - 0.01, half - 0.9, vf + 1.6), 0.0, 0.5))
    vc = vf + 1.6 + 1.0
    parts.append(MD.run(-half - 0.5, half + 0.5, vc, MD.CROWN, 1.2, up=False))
    crest = rect(-half + 0.6, vc - 0.01, half - 0.6, vc + 1.6)
    loz = cs_union([poly([(x - 0.6, vc + 0.8), (x, vc + 1.3), (x + 0.6, vc + 0.8), (x, vc + 0.3)]) for x in np.linspace(-half + 1.8, half - 1.8, 4)])
    parts.append(ext(crest - loz, 0.0, 0.7))
    sw = w / 2 + A + 0.4
    parts.append(MD.run(-sw, sw, 0.0, MD.SILL, 1.0, up=False))
    return O._one_piece([sash], parts, op, plug_cs, O.PLUG, vc + 1.6, -1.0)


def window_chevalier_upper(w=8.6, h=19.0, rise=1.8, A=0.9):
    """Chevalier upper floor: a segmental-headed one-over-one sash in an architrave, a hood
    following the head and ending in teardrops, an apron cut in a scallop."""
    op = O.opening_cs(w, h, rise)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    sash = O.window_insert(w, h, rise, lites=(1, 1), bare=True)["insert"]
    spring = h - rise
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS),
             MD.band(op.offset(A, JoinType.Miter, 4.0), A, MD.ARCHITRAVE, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op)]
    HB = 1.1
    parts.append(MD.band(op.offset(A + HB - 0.1, JoinType.Miter, 4.0), HB, MD.CROWN, clip=rect(-w - 10, spring, w + 10, h + 40)))
    for sg in (-1, 1):
        x = sg * (w / 2 + A - 0.1 + HB / 2)
        parts.append(ext(cs_union([rect(x - 0.4, spring - 1.0, x + 0.4, spring + 0.2), circle((x, spring - 1.3), 0.55, 14)]), 0.0, 1.1))
    sw = w / 2 + A + 0.4
    parts.append(MD.run(-sw, sw, 0.0, MD.SILL, 1.0, up=False))
    aw = w / 2 + 0.2
    ap = rect(-aw, -2.6, aw, -0.99) - cs_union([circle((x, -2.6), 0.6, 12) for x in np.linspace(-aw + 0.9, aw - 0.9, 4)])
    parts.append(ext(ap, 0.0, 0.6))
    return O._one_piece([sash], parts, op, plug_cs, O.PLUG, h + A + HB + 0.2, -2.6)


def door_chevalier(w=12.4, h=27.0, A=1.2):
    """The Chevalier's entrance: a pair of leaves with oval lights over raised panels, a
    transom with a scrolled bar, an architrave, and a hood on two big sawn brackets."""
    transom = 4.2
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    mid = 0.5
    lw = (w - 2 * O.CLR - 1.0 - mid) / 2
    dh = h - transom
    body, lights = [ext(plug_cs, -pl, -1.0)], []
    u = -w / 2 + O.CLR + 0.5
    for i in range(2):
        body.append(ext(rect(u, 0.5, u + lw, dh), -pl, -0.8))
        gv0 = dh * 0.45
        lights.append(oval((u + lw / 2, (gv0 + dh - 0.8) / 2), lw / 2 - 0.8, (dh - 0.8 - gv0) / 2, 28))
        body.append(_panel(rect(u + 0.8, 1.2, u + lw - 0.8, gv0 - 0.8)))
        u += lw + mid
    tr = plug_cs.offset(-0.5, JoinType.Miter, 4.0) ^ rect(-w, dh + 0.4, w, h + 2)
    tv = (dh + 0.4 + h - 0.6) / 2
    scroll = stroke([(-w / 2, tv), (-w * 0.25, tv + 0.9), (0.0, tv), (w * 0.25, tv - 0.9), (w / 2, tv)], 0.45)
    sash = _glazed(body, cs_union(lights) + tr, pl, scroll, plug_cs)
    sash.append(ext(rect(-w, dh - 0.01, w, dh + 0.4) ^ plug_cs, -pl, -0.5))
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS),
             MD.band(op.offset(A, JoinType.Miter, 4.0), A, MD.ARCHITRAVE, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op)]
    half = w / 2 + A + 2.6
    vf = h + A
    for sg in (-1, 1):
        x0 = sg * (w / 2 + A + 0.2)
        br = poly([(x0, vf + 1.6), (x0 + sg * 3.2, vf + 1.6), (x0 + sg * 3.2, vf + 0.8), (x0 + sg * 0.8, vf - 4.0), (x0, vf - 4.0)])
        br = br - circle((x0 + sg * 1.4, vf - 0.3), 0.6, 14)
        parts.append(ext(br, 0.0, 1.4))
    parts.append(ext(rect(-half + 0.6, vf - 0.01, half - 0.6, vf + 1.6), 0.0, 0.6))
    vc = vf + 1.6 + 1.4
    parts.append(MD.run(-half - 0.8, half + 0.8, vc, MD.CROWN, 1.6, up=False))
    return O._one_piece(sash, parts, op, plug_cs, pl, vc, 0.0)


def door_chevalier_back(w=10.0, h=24.0, A=1.0):
    """The Chevalier's back door: one leaf with an oval light over a panel, a plain transom,
    a casing and a cornice cap."""
    transom = 3.4
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    dh = h - transom
    u0, u1 = -w / 2 + O.CLR + 0.5, w / 2 - O.CLR - 0.5
    gv0 = dh * 0.45
    body = [ext(plug_cs, -pl, -1.0), ext(rect(u0, 0.5, u1, dh), -pl, -0.8), _panel(rect(u0 + 0.8, 1.2, u1 - 0.8, gv0 - 0.8))]
    light = oval((0.0, (gv0 + dh - 0.8) / 2), (u1 - u0) / 2 - 0.8, (dh - 0.8 - gv0) / 2, 28)
    g = plug_cs.offset(-0.5, JoinType.Miter, 4.0) ^ rect(-w, dh + 0.3, w, h + 2)
    sash = _glazed(body, light + g, pl, None, plug_cs)
    sash.append(ext(rect(-w, dh - 0.3, w, dh + 0.3) ^ plug_cs, -pl, -0.4))
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS),
             MD.band(op.offset(A, JoinType.Miter, 4.0), A, MD.CASING, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op)]
    half = w / 2 + A + 0.4
    vf = h + A
    parts.append(ext(rect(-half, vf - 0.01, half, vf + 1.6), 0.0, 0.6))
    parts.append(MD.run(-half - 0.6, half + 0.6, vf + 1.6 + 1.0, MD.CROWN, 1.2, up=False))
    return O._one_piece(sash, parts, op, plug_cs, pl, vf + 2.6, 0.0)


# ------------------------------------------------------------------ porch
def post_bulbring(h, collar=None, abacus=3.0, slot=(1.2, 1.0)):
    """A turned post: a bulb low on the shaft between rings, a long plain shaft, a ring and a
    bell under the capital (the Chevalier's porch)."""
    z1 = h - 2.6
    r = 0.95
    zb = round(min(5.6, h * 0.2) / 0.2) * 0.2
    prof = [(0.0, 1.19), (1.5, 1.19), (1.5, 1.45), (1.15, 1.7), (1.15, 2.0), (r, 2.2), (1.4, 2.2 + zb * 0.45), (r, 2.2 + zb),
            (1.2, 2.4 + zb), (1.2, 2.7 + zb), (r, 2.9 + zb), (r, z1 - 0.8), (1.15, z1 - 0.6), (1.15, z1 - 0.3), (r, z1),
            (1.25, z1 + 0.7)]
    body = PW._revolve(prof, 32) + PW._plinth(3.0)
    return body + PW._top(h, abacus / 2, z1 + 0.7, 1.25, slot, seg=32)


def fill_tulipsplats(L, vb, vt):
    """A railing of sawn splats, each cut as a tulip (a cup of three petals on a stem) between
    stiles (the Chevalier)."""
    H = vt - vb
    n = max(1, int(round(L / 2.6)))
    parts = []
    for i in range(n + 1):
        x = L * i / n
        parts.append(rect(x - 0.3, vb, x + 0.3, vt))
        if i < n:
            m = x + L / n / 2
            hw = L / n / 2 - 0.35
            cup = cs_union([_lens((m, vb + H * 0.62), H * 0.5, min(0.9, hw * 0.9), math.pi / 2),
                            _lens((m - hw * 0.45, vb + H * 0.58), H * 0.4, 0.6, math.pi / 2 + 0.4),
                            _lens((m + hw * 0.45, vb + H * 0.58), H * 0.4, 0.6, math.pi / 2 - 0.4),
                            rect(m - 0.35, vb, m + 0.35, vt)])
            parts.append(cup ^ rect(x + 0.2, vb, x + L / n - 0.2, vt))
    return parts


def frieze_keyholearcade(u0, u1, v_bot, v_top):
    """A porch frieze: a board cut below into a row of keyhole arches (a round head over a
    narrow slot) (the Chevalier)."""
    v0 = v_top - 2.8
    n = max(2, int((u1 - u0) / 3.0))
    p = (u1 - u0) / n
    board = rect(u0, v0 - 1.4, u1, v_top + 0.05)
    cuts = cs_union([cs_union([circle((u0 + p * (k + 0.5), v0 - 0.1), p * 0.32, 18),
                               rect(u0 + p * (k + 0.5) - p * 0.16, v0 - 2.0, u0 + p * (k + 0.5) + p * 0.16, v0 - 0.1)])
                     for k in range(n)])
    return board - cuts


def skirt_diamondboards(reg, d=1.2):
    """A porch skirt of upright boards with a diamond cut out of every other one (the
    Chevalier)."""
    u0, v0, u1, v1 = reg.bounds()
    boards, holes = [], []
    for k, u in enumerate(np.arange(u0 + 0.2, u1, 1.8)):
        boards.append(rect(u, v0 - 1, u + 1.5, v1 + 1))
        if k % 2 == 0 and v1 - v0 > 2.4:
            vm = (v0 + v1) / 2
            holes.append(poly([(u + 0.75, vm - 0.9), (u + 1.35, vm), (u + 0.75, vm + 0.9), (u + 0.15, vm)]))
    out = M.extrude(reg, d * 0.4) + M.extrude(cs_union(boards) ^ reg, d)
    return out - M.extrude(cs_union(holes), d + 1).translate([0, 0, d * 0.4 + 0.01]) if holes else out


def edge_teardrops(L, z0, zc):
    """Porch fascia (the Chevalier): teardrops hung under the crown."""
    out = [rect(0.3, zc - 0.45, L - 0.3, zc)]
    for x in np.arange(1.0, L - 0.8, 1.8):
        out += [poly([(x - 0.2, zc - 0.4), (x + 0.2, zc - 0.4), (x + 0.35, zc - 1.0), (x - 0.35, zc - 1.0)]), circle((x, zc - 1.15), 0.42, 12)]
    return cs_union(out), 0.6


CO.FRIEZE_EXTRA.update(swallows=frieze_swallows, peltae=frieze_peltae)
CO.COURSE_EXTRA.update(hexchain=course_hexchain)
TW.BRACKET_EXTRA.update(fantail=bracket_fantail)
TW.PIERCED = TW.PIERCED + ("fantail",)
TW.FOUNDATION_EXTRA.update(herringstone=foundation_herringstone)
PW.POSTS.update(bulbring=post_bulbring)
PW.FILLS.update(tulipsplats=fill_tulipsplats)
PW.FRIEZES.update(keyholearcade=frieze_keyholearcade)
PW.SKIRTS.update(diamondboards=skirt_diamondboards)
FT.EDGE_EXTRA.update(teardrops=edge_teardrops)


# ================================================================== the Marchand (house 87)
# Rose-red brick stepped a third each course, chequered bands of headers, cream limestone
# dressings and indigo accents; an octagonal turret engaged at the front-west corner rises a
# storey over the eave to a bell cap of arrow-pointed slates; a veranda turns round the turret.

def slate_arrowbands(k, j):
    """The Marchand's slating: square slates with a band of two courses of arrow-pointed slates
    (square shoulders, a narrow V point dropping from the middle) every nine courses."""
    return "arrow" if k % 9 in (3, 4) else "square"


def bell_cap(z0, h, d0, d1, a=0.6, bands=8):
    """A bell (ogee) cap profile [(d, z), ...] for a turret: flaring out at its foot (concave),
    standing steepest half way up, then rounding in like a dome to its neck (convex): the lean
    is (1 + a cos 2 pi s) times the mean, so it leans most at the two ends; keep
    (1 + a) (d0 - d1) / h under 1 for it to print upside down. ``bands`` straight facets."""
    out = []
    for k in range(bands + 1):
        s = k / bands
        out.append((d0 + (d1 - d0) * (s + a * math.sin(2 * math.pi * s) / (2 * math.pi)), z0 + h * s))
    assert (1 + a) * (d0 - d1) / h < 1.0, "bell cap leans more than 45 degrees"
    return out


# ------------------------------------------------------------------ cornice ornaments
def frieze_rinceau(L, h, b, pitch, margin, pair, half):
    """A rinceau: a vine stem running in waves along the frieze, a scroll curling off it into
    every hollow and a leaf on every swell (the Marchand's storey joint)."""
    v0, v1 = 0.8, h - 0.8
    hh = v1 - v0
    vm = (v0 + v1) / 2
    lam = max(6.0, hh * 1.9)
    n = max(1, int((L - 1.0) / lam))
    u0 = (L - n * lam) / 2
    amp = hh * 0.2
    us = np.linspace(u0, u0 + n * lam, n * 24 + 1)
    cs = [stroke([(u, vm + amp * math.sin(2 * math.pi * (u - u0) / lam)) for u in us], 0.5)]
    rc = min(hh * 0.3, 1.1)
    for k in range(2 * n):
        sg = 1 if k % 2 == 0 else -1
        up = u0 + lam * (k + 0.5) / 2
        cx, cy = up + lam * 0.2, vm - sg * (amp * 0.35)
        pts = []
        for t in np.linspace(0.0, 1.0, 20):
            a = sg * math.pi / 2 - sg * t * 1.7 * math.pi
            r = rc * (1 - 0.55 * t)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        cs.append(stroke(pts, 0.42))
        cs.append(circle(pts[-1], 0.32, 10))
        cs.append(_lens((up - lam * 0.17, vm + sg * amp * 0.75), 1.7, 0.6, sg * 0.55))
    return [_st(cs_union(cs) ^ rect(0.2, v0 - 0.3, L - 0.2, v1 + 0.3), b, 0.45)], []


def frieze_cartouches(L, h, b, pitch, margin, pair, half):
    """Cartouches: in every bay between the bracket pairs an oval shield in a rim with a boss,
    curls at its sides and a little shell on top, hung with a garland to each side (the
    Marchand's eave)."""
    v0, v1 = 0.8, h - 0.8
    hh = v1 - v0
    vm = v0 + hh * 0.46
    out = []
    for uc, wd in CO._between(L, pitch, margin, pair, half):
        if wd < 5.0:
            continue
        rx, ry = min(wd * 0.16, 1.5), hh * 0.34
        ov = oval((uc, vm), rx, ry, 28)
        out.append(_st(ov - oval((uc, vm), rx - 0.45, ry - 0.45, 24), b, 0.5))
        out.append(_st(oval((uc, vm), max(0.4, rx - 0.85), max(0.5, ry - 0.85), 20), b, 0.35))
        out.append(_st(ov ^ rect(-1e3, -1e3, 1e3, 1e3), b, 0.15))
        for sg in (-1, 1):
            cc = (uc + sg * (rx + 0.35), vm - ry * 0.25)
            curl = circle(cc, 0.55, 14) - circle(cc, 0.15, 8)
            out.append(_st(curl, b, 0.4))
            u_end = uc + sg * (wd / 2 - 0.3)
            out.append(_st(swag(min(uc + sg * (rx + 0.6), u_end), max(uc + sg * (rx + 0.6), u_end), vm + ry * 0.55,
                                hh * 0.32, width=0.5), b, 0.4))
        fan = poly([(uc, vm + ry - 0.2)] + [(uc + 1.0 * math.cos(a), vm + ry - 0.2 + 1.0 * math.sin(a))
                                            for a in np.linspace(0.35, math.pi - 0.35, 9)])
        out.append(_st(fan ^ rect(-1e3, v0, 1e3, v1), b, 0.45))
    return out, []


def guilloche(L, h):
    """A guilloche as CrossSections: two strands waving across each other, a round boss in
    every eye between them."""
    pu = max(2.2, h * 1.35)
    n = max(1, int((L - 0.6) / pu))
    u0 = (L - n * pu) / 2
    amp = h / 2 - 0.35
    us = np.linspace(u0, u0 + n * pu, n * 16 + 1)
    out = [stroke([(u, h / 2 + sg * amp * math.sin(math.pi * (u - u0) / pu)) for u in us], 0.42) for sg in (-1, 1)]
    out += [circle((u0 + pu * (k + 0.5), h / 2), max(0.25, min(0.4, amp - 0.45)), 12) for k in range(n)]
    return [cs_union(out) ^ rect(0.2, 0.05, L - 0.2, h - 0.05)]


def course_guilloche(L, h, b, pitch, margin, p):
    """A guilloche: two strands waving across each other with a boss in every eye (the
    Marchand)."""
    return [_st(cs, b, 0.45) for cs in guilloche(L, h)]


def course_eggdart(L, h, b, pitch, margin, p):
    """Egg and dart: eggs sitting in open shells, a dart between every two, under a fillet
    (the Marchand's eave)."""
    pu = max(1.9, h * 1.15)
    n = max(1, int((L - 0.6) / pu))
    u0 = (L - n * pu) / 2
    vc = (h - 0.4) * 0.48
    eggs, shells, darts = [], [], []
    for k in range(n):
        uc = u0 + pu * (k + 0.5)
        rx, ry = pu * 0.26, (h - 0.4) * 0.34
        eggs.append(oval((uc, vc), rx, ry, 18))
        shells.append((oval((uc, vc), rx + 0.42, ry + 0.4, 18) - oval((uc, vc), rx + 0.05, ry + 0.05, 18))
                      ^ rect(uc - pu, -1.0, uc + pu, vc + ry * 0.4))
        x = u0 + pu * k
        if k:
            darts.append(cs_union([rect(x - 0.2, vc - ry * 0.2, x + 0.2, h - 0.4),
                                   poly([(x - 0.38, vc), (x + 0.38, vc), (x, max(0.15, vc - ry - 0.2))])]))
    out = [ext(rect(0.2, h - 0.42, L - 0.2, h), b - 0.05, b + 0.45)]
    out.append(_st(cs_union(eggs) ^ rect(0.2, 0.05, L - 0.2, h), b, 0.5))
    out.append(_st(cs_union(shells) ^ rect(0.2, 0.05, L - 0.2, h), b, 0.35))
    if darts:
        out.append(_st(cs_union(darts) ^ rect(0.2, 0.05, L - 0.2, h), b, 0.35))
    return out


def bracket_dropconsole(h, d, t):
    """A console with a big round head under the soffit, its neck sweeping back to a curled foot
    on the wall and a pendant drop hung below the foot; a sunk eye in the head (side profile,
    top at v = 0; the Marchand)."""
    r = min(0.3 * h, 0.35 * d, 1.0)
    pts = [(0.0, 0.0), (d, 0.0), (d, -r)]
    hb = h - 1.7
    for s in np.linspace(0.0, 1.0, 12):
        pts.append((d - r - (d - r - 0.9) * (1 - (1 - s) ** 2), -r - (hb - r - 0.6) * s))
    pts += [(0.0, -hb + 0.6)]
    prof = cs_union([poly(pts), circle((d - r, -r), r, 18), circle((0.65, -hb + 0.55), 0.65, 14),
                     poly([(0.0, -hb + 0.3), (0.95, -hb + 0.3), (0.55, -h + 0.55), (0.0, -h + 0.55)]),
                     circle((0.4, -h + 0.45), 0.4, 12)])
    return prof - circle((d - r, -r), min(0.55, r * 0.55), 14)


# ------------------------------------------------------------------ the mansard's window add-ins
def addin_marchand(w=5.2, h=10.4, A=0.9):
    """A Marchand add-in: a round-headed two-light window in an architrave with a keystone and
    imposts, under a swan-neck pediment (two S-scrolls rising to curls, a ball between them),
    its plug's roof a segment; a sill on a corbel."""
    r = w / 2
    spring = h - r
    op = O.opening_cs(w, h, r)
    bars = cs_union([rect(-RIB / 2, -1.0, RIB / 2, h + 1.0), rect(-w, spring * 0.55 - 0.3, w, spring * 0.55 + 0.3)])
    half = r + A + 0.7
    vt = h + A
    rise = 3.0
    seg = arch_cs(-half, half, vt - 1.6, vt - 1.6, rise=rise + 1.6, seg=40)
    body = cs_union([rect(-half, -0.2, half, vt - 1.6), seg])
    parts = [ext(body - op, 0.0, 0.6),
             MD.band(op.offset(A, JoinType.Round), A, MD.ARCHITRAVE, clip=rect(-20, 0.0, 20, 40) - op)]
    for sg in (-1, 1):
        parts.append(chamfer_box(sg * (r + A / 2) - A / 2 - 0.25, spring - 0.5, sg * (r + A / 2) + A / 2 + 0.25, spring + 0.3,
                                 0.0, 1.1, c=0.2))
        neck = bezier((sg * (half - 0.2), vt - 1.0), (sg * (half - 0.4), vt + 1.4), (sg * 1.6, vt + 0.6), (sg * 1.1, vt + 2.0), 16)
        parts.append(ext(stroke(neck, 0.8), 0.0, 1.1))
        cc = (sg * 1.45, vt + 2.0)
        parts.append(ext(circle(cc, 0.62, 16) - circle(cc, 0.18, 8), 0.0, 1.2))
    parts.append(keystone(0.0, h - 0.3, A + 0.9, 1.1, 1.6, 0.0, 1.3))
    parts.append(ext(cs_union([rect(-0.4, vt + 0.4, 0.4, vt + 1.2), circle((0.0, vt + 1.7), 0.6, 14)]), 0.0, 1.1))
    sw = half + 0.3
    parts.append(MD.run(-sw, sw, 0.0, MD.SILL, 1.0, up=False))
    parts.append(ext(poly([(-1.6, -0.8), (1.6, -0.8), (0.0, -2.0)]), 0.0, 0.9))
    parts = [p - ext(op, -1.0, 5.0) for p in parts]
    outline = body.offset(-0.4, JoinType.Round) ^ rect(-50, 0.2, 50, 100)
    return dict(light=op, bars=bars, frame=parts, outline=outline, top=vt + 2.7, bottom=-2.0)


# ------------------------------------------------------------------ walls, foundation, chimney
def brick_thirdcheck(region, datum=0.0, bl=2.4, bh=0.8, mortar=0.5, bed=0.2, d=0.25, every=12):
    """Stretcher bond stepped a third of a brick each course (raking third bond), and every
    ``every`` courses a chequered band: two courses of headers, alternately proud and sunk (the
    Marchand)."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    hl = bl / 2
    cells, proud = [], []
    k = math.floor((v0 - datum) / bh) - 1
    while datum + k * bh < v1:
        v = datum + k * bh
        top = v + bh - bed
        r = k % every
        if r in (0, 1):
            u = u0 - 2 * bl
            j = 0
            while u < u1 + bl:
                (proud if (j + r) % 2 == 0 else cells).append(rect(u + mortar / 2, v, u + hl - mortar / 2, top))
                u += hl
                j += 1
        else:
            u = u0 - 2 * bl + (k % 3) * bl / 3
            while u < u1 + bl:
                cells.append(rect(u + mortar / 2, v, u + bl - mortar / 2, top))
                u += bl
        k += 1
    out = M.extrude(cs_union(cells) ^ region, d)
    if proud:
        out = out + M.extrude(cs_union(proud) ^ region, d + 0.2)
    return out


def foundation_chamferrustic(reg, seed=0):
    """Chamfered rustication: long blocks in courses, every edge bevelled so the joints are deep
    V's, over a plain plinth course and under a dressed cap (the Marchand)."""
    b = reg.bounds()
    out = [M.extrude(reg, 0.2)]
    out.append(ext(rect(b[0] - 1, b[3] - 1.2, b[2] + 1, b[3] + 1) ^ reg, 0.19, 0.75))
    out.append(ext(rect(b[0] - 1, b[1] - 1, b[2] + 1, b[1] + 1.6) ^ reg, 0.19, 0.7))
    keep = ext(reg, 0.0, 2.0)
    v = b[1] + 1.6
    j = 0
    while v < b[3] - 2.2:
        hh = min(2.6, b[3] - 1.2 - v)
        u = b[0] - (j % 2) * 3.2
        while u < b[2]:
            blk = rect(u + 0.1, v + 0.1, u + 6.3, v + hh - 0.1) ^ reg
            if not blk.is_empty():
                bb = blk.bounds()
                if bb[2] - bb[0] > 1.0 and bb[3] - bb[1] > 1.0:
                    out.append(chamfer_box(bb[0], bb[1], bb[2], bb[3], 0.19, 0.5, c=0.4) ^ keep)
            u += 6.4
        v += hh
        j += 1
    return union(out)


def chimney_marchand(w=10.4, d=8.8, h=25.0):
    """The Marchand's stacks: red brick on a stone plinth, a sunk round-headed panel on every
    face, a band of dogtooth (bricks set corner-out) under a corbelled stone cap, two round pots."""
    h = round(h / 0.2) * 0.2
    sh = h - 5.0
    body = box([-w / 2, -d / 2, 0.0], [w / 2, d / 2, sh])
    body = body + box([-w / 2 - 0.4, -d / 2 - 0.4, 0.0], [w / 2 + 0.4, d / 2 + 0.4, 1.6])
    for (L, D, rot) in ((w, d, 0), (d, w, 90), (w, d, 180), (d, w, 270)):
        pan = ext(O.opening_cs(L - 3.2, sh - 7.0, (L - 3.2) / 2), -0.5, 0.01).translate([0, 3.0, 0])
        A = np.array([[1.0, 0, 0, 0], [0, 0, 1.0, 0], [0, 1.0, 0, 0]])
        body = body - pan.transform(A).translate([0, D / 2, 0]).rotate([0, 0, rot])
    zd = sh - 2.0
    teeth = []
    for (L, D, rot) in ((w, d, 0), (d, w, 90), (w, d, 180), (d, w, 270)):
        for x in np.arange(-L / 2 + 0.6, L / 2 - 0.4, 1.0):
            teeth.append(M.hull_points([(x - 0.4, D / 2 - 0.05, zd), (x + 0.4, D / 2 - 0.05, zd), (x, D / 2 + 0.4, zd),
                                        (x - 0.4, D / 2 - 0.05, zd + 1.2), (x + 0.4, D / 2 - 0.05, zd + 1.2),
                                        (x, D / 2 + 0.4, zd + 1.2)]).rotate([0, 0, rot]))
    body = body + union(teeth)
    body = body + M.hull_points([(x, y, sh - 0.01) for x in (-w / 2, w / 2) for y in (-d / 2, d / 2)] +
                                [(x, y, sh + 0.7) for x in (-w / 2 - 0.7, w / 2 + 0.7) for y in (-d / 2 - 0.7, d / 2 + 0.7)])
    body = body + box([-w / 2 - 0.7, -d / 2 - 0.7, sh + 0.69], [w / 2 + 0.7, d / 2 + 0.7, sh + 1.6])
    body = body + box([-w / 2 - 0.3, -d / 2 - 0.3, sh + 1.59], [w / 2 + 0.3, d / 2 + 0.3, sh + 2.2])
    for sx in (-1, 1):
        prof = [(0.0, 0.0), (1.3, 0.0), (1.3, 0.5), (1.0, 0.9), (0.9, 2.0), (1.15, 2.4), (1.15, h - sh - 2.2), (0.0, h - sh - 2.2)]
        body = body + PW._revolve(prof, 24).translate([sx * w / 4, 0.0, sh + 2.19])
    flues = union([M.cylinder(h, 0.55, 0.55, 12).translate([sx * w / 4, 0.0, sh - 4.0]) for sx in (-1, 1)])
    return body - flues


def fence_marchand(L, h):
    """Marchand cresting: spear-headed bars, and between every two an anthemion (a fan of five
    petals) rising out of a pair of C-scrolls on the rail."""
    pitch = 3.2
    n = max(1, int(round(L / pitch)))
    p = L / n
    rail = h * 0.3
    cells = [rect(0.0, 0.0, L, 0.6), rect(0.0, rail, L, rail + 0.45)]
    for j in range(n + 1):
        u = p * j
        cells.append(rect(u - 0.28, 0.0, u + 0.28, h - 1.0))
        cells.append(poly([(u - 0.5, h - 1.1), (u + 0.5, h - 1.1), (u, h)]))
        if j < n:
            m = u + p / 2
            vb = rail + 0.4
            for sg in (-1, 1):
                cc = (m + sg * 0.6, vb + 0.4)
                cells.append(circle(cc, 0.5, 12) - circle(cc, 0.1, 6))
            for a in np.linspace(-0.62, 0.62, 5):
                ln = (h - vb - 1.2) * (1.0 - 0.3 * abs(a) / 0.62)
                cells.append(_lens((m + math.sin(a) * ln / 2, vb + 0.6 + math.cos(a) * ln / 2), ln, 0.5, math.pi / 2 - a))
    return cs_union(cells) ^ rect(0.0, 0.0, L, h + 1.0)


def finial_artichoke(h=10.0):
    """A finial of an artichoke (stacked cups of leaves, each widening up to its rim) on a
    turned stem, a needle above (the Marchand's turret)."""
    z0, z1 = h * 0.36, h * 0.74
    prof = [(0.0, 0.0), (1.5, 0.0), (1.5, 0.8), (0.95, 1.4), (0.55, 2.0), (0.55, z0 - 0.6), (0.85, z0 - 0.3), (0.6, z0)]
    nsc = 5
    for k in range(nsc):
        za = z0 + (z1 - z0) * k / nsc
        zb = z0 + (z1 - z0) * (k + 1) / nsc
        s = (k + 0.5) / nsc
        rmax = 0.75 + 0.6 * math.sin(math.pi * min(1.0, s * 1.15))
        prof += [(rmax * 0.7, za + 0.01), (rmax, zb - 0.05)]
    prof += [(0.45, z1 + 0.3), (0.0, z1 + 0.3)]
    body = PW._revolve(prof, 28)
    return body + M.cylinder(h - z1 - 0.1, 0.35, 0.12, 12).translate([0, 0, z1 + 0.1])


# ------------------------------------------------------------------ windows and doors
def window_marchand_lower(w=9.6, h=22.0, A=1.0):
    """Marchand ground floor: a round-headed two-over-two sash in an architrave on imposts, a
    hood moulding round the arch ending in curled stops, a shell keystone; a sill on two
    consoles over a shaped apron with a drop."""
    r = w / 2
    spring = h - r
    op = O.opening_cs(w, h, r)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    sash = O.window_insert(w, h, r, lites=(2, 2), bare=True)["insert"]
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS),
             MD.band(op.offset(A, JoinType.Round), A, MD.ARCHITRAVE, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op)]
    for sg in (-1, 1):
        x = sg * (r + A / 2)
        parts.append(chamfer_box(x - A / 2 - 0.3, spring - 0.7, x + A / 2 + 0.3, spring + 0.3, 0.0, 1.3, c=0.25))
    HB = 1.0
    parts.append(MD.band(op.offset(A + HB - 0.1, JoinType.Round), HB, MD.CROWN, clip=rect(-w - 10, spring, w + 10, h + 40)))
    for sg in (-1, 1):
        cc = (sg * (r + A - 0.1 + HB / 2), spring - 0.4)
        parts.append(ext(circle(cc, 0.8, 16) - circle(cc, 0.25, 8), 0.0, 1.2))
        parts.append(ext(circle(cc, 0.3, 8), 0.0, 0.8))
    vs = h - 0.5
    shell = poly([(0.0, vs)] + [(2.0 * math.cos(a), vs + 2.0 * math.sin(a)) for a in np.linspace(0.3, math.pi - 0.3, 13)])
    ribs = cs_union([stroke([(0.0, vs + 0.3), (1.85 * math.cos(a), vs + 1.85 * math.sin(a))], 0.42)
                     for a in np.linspace(0.45, math.pi - 0.45, 5)])
    parts.append(ext(shell, 0.0, 1.3) + ext(ribs ^ shell, 1.29, 1.6))
    sw = r + A + 0.6
    parts.append(MD.run(-sw, sw, 0.0, MD.SILL, 1.0, up=False))
    for sg in (-1, 1):
        parts.append(console(2.2, 1.0, 0.9, u=sg * (r - 0.2), v_top=-0.99, w0=0.0))
    aw = r - 0.9
    xs = np.linspace(aw, -aw, 13)
    apron = poly([(-aw, -0.99), (aw, -0.99)] + [(x, -1.9 - 0.7 * (1 - (x / aw) ** 2)) for x in xs])
    parts.append(ext(apron, 0.0, 0.55))
    parts.append(ext(cs_union([rect(-0.25, -3.0, 0.25, -2.4), circle((0.0, -3.0), 0.45, 12)]), 0.0, 0.8))
    return O._one_piece([sash], parts, op, plug_cs, O.PLUG, h + A + HB + 0.2, -3.45)


def window_marchand_upper(w=9.0, h=19.6, A=0.9):
    """Marchand upper floor: a flat-headed one-over-one sash in a casing, a frieze hung with a
    garland between two rosettes, a cornice cap crested with an anthemion between two
    reclining scrolls; a sill on blocks."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    sash = O.window_insert(w, h, 0, lites=(1, 1), bare=True)["insert"]
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS),
             MD.band(op.offset(A, JoinType.Miter, 4.0), A, MD.CASING, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op)]
    half = w / 2 + A + 0.4
    vf = h + A
    parts.append(ext(rect(-half, vf - 0.01, half, vf + 2.4), 0.0, 0.5))
    parts.append(ext(swag(-half + 1.4, half - 1.4, vf + 2.0, 1.2, width=0.5), 0.49, 0.9))
    for sg in (-1, 1):
        parts.append(MD.rosette(sg * (half - 0.9), vf + 1.4, 0.7, 0.49, 0.6))
    vc = vf + 2.4 + 1.0
    parts.append(MD.run(-half - 0.5, half + 0.5, vc, MD.CROWN, 1.2, up=False))
    parts.append(MD.anthemion((0.0, vc - 0.01), 3.0, 2.6, 0.0, 1.0))
    for sg in (-1, 1):
        pts = bezier((sg * 1.2, vc + 0.5), (sg * 2.4, vc + 1.2), (sg * (half - 1.0), vc + 0.2), (sg * (half - 0.2), vc + 0.9), 14)
        parts.append(ext(stroke(pts, 0.6) ^ rect(-half - 2, vc - 0.01, half + 2, vc + 3), 0.0, 0.8))
        parts.append(ext(circle((sg * (half - 0.4), vc + 0.8), 0.45, 12), 0.0, 0.9))
    sw = half + 0.2
    parts.append(MD.run(-sw, sw, 0.0, MD.SILL, 1.0, up=False))
    for sg in (-1, 1):
        parts.append(chamfer_box(sg * (w / 2) - 0.7, -2.0, sg * (w / 2) + 0.7, -0.8, 0.0, 0.9, c=0.25))
    return O._one_piece([sash], parts, op, plug_cs, O.PLUG, vc + 2.6, -2.0)


def door_marchand(w=13.0, h=27.0, A=1.2):
    """The Marchand's entrance: a pair of leaves, each a round-headed light over a raised panel,
    under a round fanlight barred like a spider's web; an architrave with a keystone between
    engaged round columns on pedestals, an entablature with a cartouche in its frieze, a cornice
    and a crest of two scrolls round a ball."""
    r = w / 2
    spring = h - r
    op = O.opening_cs(w, h, r)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    mid = 0.5
    lw = (w - 2 * O.CLR - 1.0 - mid) / 2
    dh = spring - 0.4
    body, lights = [ext(plug_cs, -pl, -1.0)], []
    u = -w / 2 + O.CLR + 0.5
    for i in range(2):
        body.append(ext(rect(u, 0.5, u + lw, dh), -pl, -0.8))
        gv0 = dh * 0.45
        lr = lw / 2 - 0.8
        lights.append(O.opening_cs(2 * lr, dh - 0.8 - gv0, lr).translate([u + lw / 2, gv0]))
        body.append(_panel(rect(u + 0.8, 1.2, u + lw - 0.8, gv0 - 0.8)))
        u += lw + mid
    fan = plug_cs.offset(-0.5, JoinType.Miter, 4.0) ^ rect(-w, spring + 0.2, w, h + 2)
    c0 = (0.0, spring + 0.2)
    web = cs_union([circle(c0, r * 0.5, 32) - circle(c0, r * 0.5 - 0.45, 32)] +
                   [stroke([(r * 0.48 * math.cos(a), spring + 0.2 + r * 0.48 * math.sin(a)),
                            (r * 1.2 * math.cos(a), spring + 0.2 + r * 1.2 * math.sin(a))], 0.45)
                    for a in np.linspace(0.0, math.pi, 7)[1:-1]] + [circle(c0, 1.0, 16)])
    sash = _glazed(body, cs_union(lights) + fan, pl, web, plug_cs)
    sash.append(ext(rect(-w, dh - 0.01, w, spring + 0.2) ^ plug_cs, -pl, -0.5))
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS),
             MD.band(op.offset(A, JoinType.Round), A, MD.ARCHITRAVE, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op)]
    rc = 1.15
    xc = r + A + 0.4 + rc
    vcap = h + A + 0.8
    half = xc + rc + 0.6
    for sg in (-1, 1):
        x = sg * xc
        parts.append(ext(rect(x - rc - 0.3, 0.0, x + rc + 0.3, vcap), 0.0, 0.6))
        parts.append(chamfer_box(x - rc - 0.5, 0.0, x + rc + 0.5, 4.2, 0.0, 1.8, c=0.3))
        prof = [(0.0, 0.0), (rc + 0.25, 0.0), (rc + 0.25, 0.4), (rc, 0.8), (rc * 0.88, vcap - 4.2 - 1.6), (rc + 0.2, vcap - 4.2 - 1.2),
                (rc + 0.2, vcap - 4.2 - 0.9), (rc * 0.88, vcap - 4.2 - 0.7), (rc + 0.5, vcap - 4.2), (0.0, vcap - 4.2)]
        col = PW._revolve(prof, 28).rotate([-90, 0, 0]).translate([x, 4.19, 0.0]) ^ box([x - 3, 0.0, 0.0], [x + 3, vcap + 1, 5.0])
        parts.append(col)
        parts.append(chamfer_box(x - rc - 0.6, vcap - 0.8, x + rc + 0.6, vcap + 0.01, 0.0, 1.8, c=0.2))
    parts.append(ext(rect(-xc, spring, xc, vcap) - op.offset(A, JoinType.Round), 0.0, 0.6))
    parts.append(keystone(0.0, h - 0.3, vcap - h + 0.3, 1.6, 2.4, 0.0, 1.6))
    parts.append(ext(rect(-half, vcap - 0.01, half, vcap + 0.8), 0.0, 1.0))
    parts.append(ext(rect(-half + 0.3, vcap + 0.79, half - 0.3, vcap + 3.4), 0.0, 0.7))
    parts.append(MD.cartouche((0.0, vcap + 2.1), 3.0, 2.2, 0.69, 0.8))
    vk = vcap + 3.4 + 1.4
    parts.append(MD.run(-half - 0.8, half + 0.8, vk, MD.CROWN, 1.4, up=False))
    for sg in (-1, 1):
        pts = bezier((sg * (half - 0.4), vk + 0.4), (sg * (half - 1.4), vk + 2.4), (sg * 2.6, vk + 0.4), (sg * 1.5, vk + 1.6), 14)
        parts.append(ext(stroke(pts, 0.8) ^ rect(-half - 2, vk - 0.01, half + 2, vk + 4), 0.0, 1.0))
        cc = (sg * 1.75, vk + 1.75)
        parts.append(ext(circle(cc, 0.6, 14) - circle(cc, 0.18, 8), 0.0, 1.1))
    parts.append(ext(cs_union([rect(-0.5, vk - 0.01, 0.5, vk + 1.4), circle((0.0, vk + 2.0), 0.85, 16)]), 0.0, 1.2))
    return O._one_piece(sash, parts, op, plug_cs, pl, vk + 2.85, 0.0)


def door_marchand_back(w=10.0, h=24.0, A=1.0, rise=1.6):
    """The Marchand's back door: one leaf with a round-headed light over a panel under a
    segmental transom, in an architrave with a keystone and a segmental hood."""
    op = O.opening_cs(w, h, rise)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    spring = h - rise
    dh = spring - 3.0
    u0, u1 = -w / 2 + O.CLR + 0.5, w / 2 - O.CLR - 0.5
    gv0 = dh * 0.45
    body = [ext(plug_cs, -pl, -1.0), ext(rect(u0, 0.5, u1, dh), -pl, -0.8), _panel(rect(u0 + 0.8, 1.2, u1 - 0.8, gv0 - 0.8))]
    lr = (u1 - u0) / 2 - 0.9
    light = O.opening_cs(2 * lr, dh - 0.8 - gv0, lr).translate([0.0, gv0])
    g = plug_cs.offset(-0.5, JoinType.Miter, 4.0) ^ rect(-w, dh + 0.3, w, h + 2)
    sash = _glazed(body, light + g, pl, None, plug_cs)
    sash.append(ext(rect(-w, dh - 0.3, w, dh + 0.3) ^ plug_cs, -pl, -0.4))
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS),
             MD.band(op.offset(A, JoinType.Miter, 4.0), A, MD.ARCHITRAVE, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op)]
    HB = 1.0
    parts.append(MD.band(op.offset(A + HB - 0.1, JoinType.Miter, 4.0), HB, MD.CROWN, clip=rect(-w - 10, spring, w + 10, h + 40)))
    parts.append(keystone(0.0, h - 0.3, A + HB + 0.4, 1.3, 1.9, 0.0, 1.5))
    return O._one_piece(sash, parts, op, plug_cs, pl, h + A + HB + 0.2, 0.0)


# ------------------------------------------------------------------ porch
def post_cushionwaist(h, collar=None, abacus=3.0, slot=(1.2, 1.0)):
    """A turned post: a plain round shaft with a cushion collar between fillets at half its
    height, a necking ring and an echinus under the capital (the Marchand's veranda)."""
    z1 = h - 2.6
    r = 0.95
    zm = round(z1 * 0.5 / 0.2) * 0.2
    prof = [(0.0, 1.19), (1.55, 1.19), (1.55, 1.4), (1.35, 1.6), (1.35, 1.9), (r, 2.3),
            (r, zm - 1.2), (1.2, zm - 0.9), (1.2, zm - 0.7), (1.42, zm - 0.45), (1.42, zm + 0.45), (1.2, zm + 0.7),
            (1.2, zm + 0.9), (r, zm + 1.2), (r, z1 - 0.6), (1.12, z1 - 0.4), (1.12, z1 - 0.1), (r * 0.95, z1 + 0.1),
            (1.3, z1 + 0.7)]
    body = PW._revolve(prof, 32) + PW._plinth(3.0)
    return body + PW._top(h, abacus / 2, z1 + 0.7, 1.3, slot, seg=32)


def baluster_urnneck(h, seg=18):
    """A baluster: a squat urn at its foot, a long neck and a collar under the top block (the
    Marchand)."""
    prof = [(0.0, 0.8), (0.32, 0.8), (0.5, h * 0.2), (0.56, h * 0.3), (0.42, h * 0.4), (0.28, h * 0.48), (0.28, h * 0.76),
            (0.45, h * 0.84), (0.3, h * 0.9), (0.3, h - 0.8)]
    return PW._revolve(prof, seg) + box([-0.55, -0.55, 0.0], [0.55, 0.55, 0.81]) + box([-0.55, -0.55, h - 0.81], [0.55, 0.55, h])


def frieze_basketarch(u0, u1, v_bot, v_top):
    """A porch frieze: a board cut below into flat basket-handle arches, a pierced quatrefoil
    in the spandrel over every pier (the Marchand)."""
    v0 = v_top - 3.4
    n = max(1, int((u1 - u0) / 9.0))
    p = (u1 - u0) / n
    board = rect(u0, v0 - 1.6, u1, v_top + 0.05)
    cuts, holes = [], []
    for k in range(n):
        a, e = u0 + p * k + 0.5, u0 + p * (k + 1) - 0.5
        m, hw = (a + e) / 2, (e - a) / 2
        arch = [(m - hw * math.cos(t), v0 - 1.6 + 1.4 * math.sin(t) ** 0.55) for t in np.linspace(0.0, math.pi, 25)]
        cuts.append(poly([(a, v0 - 3.0)] + arch + [(e, v0 - 3.0)]))
    for k in range(1, n):
        holes.append(quatrefoil((u0 + p * k, v0 + 0.3), 0.42, 12))
    return board - cs_union(cuts) - (cs_union(holes) if holes else rect(0, 0, 0, 0))


def skirt_herringboards(reg, d=1.2):
    """A porch skirt of boards laid diagonally, alternate panels sloping opposite ways so the
    run reads as herringbone, between upright stiles under a rail (the Marchand)."""
    u0, v0, u1, v1 = reg.bounds()
    pw_ = 4.0
    out = [M.extrude(reg, d * 0.35)]
    boards, stiles = [], []
    for k, uc in enumerate(np.arange(u0, u1, pw_)):
        pan = rect(uc + 0.4, v0 - 1, uc + pw_ - 0.4, v1 - 0.8)
        sg = 1 if k % 2 == 0 else -1
        st = [stroke([(x, v0 - 2), (x + sg * (v1 - v0 + 4), v1 + 2)], 0.7, caps=False)
              for x in np.arange(uc - (v1 - v0) - 4, uc + pw_ + (v1 - v0) + 4, 1.2)]
        boards.append(cs_union(st) ^ pan)
        stiles.append(rect(uc - 0.4, v0 - 1, uc + 0.4, v1 + 1))
    out.append(M.extrude(cs_union(boards) ^ reg, d * 0.75))
    out.append(M.extrude((cs_union(stiles) + rect(u0 - 1, v1 - 0.8, u1 + 1, v1 + 1)) ^ reg, d))
    return union(out)


def edge_dartbeads(L, z0, zc):
    """Porch fascia (the Marchand): darts and beads hung under the crown in turn."""
    out = [rect(0.3, zc - 0.45, L - 0.3, zc)]
    for i, x in enumerate(np.arange(1.0, L - 0.8, 1.3)):
        if i % 2 == 0:
            out.append(poly([(x - 0.42, zc - 0.4), (x + 0.42, zc - 0.4), (x, zc - 1.5)]))
        else:
            out.append(circle((x, zc - 0.8), 0.42, 12))
    return cs_union(out), 0.6


CO.FRIEZE_EXTRA.update(vinescroll=frieze_rinceau, garlandcartouche=frieze_cartouches)
CO.COURSE_EXTRA.update(twinstrand=course_guilloche, eggcup=course_eggdart)
TW.BRACKET_EXTRA.update(dropconsole=bracket_dropconsole)
TW.PIERCED = TW.PIERCED + ("dropconsole",)
TW.FOUNDATION_EXTRA.update(chamferrustic=foundation_chamferrustic)
PW.POSTS.update(cushionwaist=post_cushionwaist)
PW.BALUSTERS.update(urnneck=(baluster_urnneck, 1.6))
PW.FRIEZES.update(basketarch=frieze_basketarch)
PW.SKIRTS.update(herringboards=skirt_herringboards)
FT.EDGE_EXTRA.update(dartbeads=edge_dartbeads)


# ================================================================== the Rochambeau (house 88)
# Sage stucco scored as ashlar with chamfered quoins, ivory dressings and burgundy accents, on a
# bluestone base with a blind arcade; a straight mansard of purple slate laid with crosses; two
# two-storey side bays under mansard hoods that run into the main roof; a portico on banded
# columns with an iron balustrade on its roof; a veranda down the east side.

def slate_crosses(k, j):
    """The Rochambeau's slating: square slates with Greek crosses of diamond-cut ones laid in a
    quincunx (a cross every ten slates across, every fourteen courses up, alternate rows of
    crosses half a step on)."""
    x = j + 0.5 * (k % 2)
    kk = k % 14 - 6
    if -3 <= kk <= 3:
        m = (x + 5 * ((k // 14) % 2)) % 10 - 5.0
        if (kk == 0 and abs(m) <= 2.01) or (kk != 0 and abs(m) <= 0.51):
            return "diamond"
    return "square"


# ------------------------------------------------------------------ cornice ornaments
def frieze_medallions(L, h, b, pitch, margin, pair, half):
    """Medallions: a row of round medallions (a ring round a six-petalled rosette) linked by
    ribbons tied in bows between them (the Rochambeau's storey joint)."""
    v0, v1 = 0.8, h - 0.8
    hh = v1 - v0
    vm = (v0 + v1) / 2
    R_ = min(hh * 0.45, 1.8)
    pu = max(R_ * 2 + 4.6, 7.0)
    n = max(1, int((L - 1.0) / pu))
    u0 = (L - n * pu) / 2
    out = []
    for k in range(n):
        uc = u0 + pu * (k + 0.5)
        out.append(_st(circle((uc, vm), R_, 28) - circle((uc, vm), R_ - 0.45, 24), b, 0.5))
        pet = cs_union([circle((uc + R_ * 0.45 * math.cos(a), vm + R_ * 0.45 * math.sin(a)), max(0.3, R_ * 0.24), 10)
                        for a in np.linspace(0, 2 * math.pi, 6, endpoint=False)])
        out.append(_st(pet + circle((uc, vm), 0.4, 10), b, 0.35))
    for k in range(n + 1):
        x = u0 + pu * k
        xa, xb = max(0.4, x - pu / 2 + R_ - 0.1), min(L - 0.4, x + pu / 2 - R_ + 0.1)
        if xb - xa < 1.5:
            continue
        rib = stroke([(xa, vm), ((xa + x) / 2, vm - hh * 0.18), (x, vm), ((x + xb) / 2, vm - hh * 0.18), (xb, vm)], 0.42)
        bow = cs_union([_lens((x - 0.55, vm + 0.15), 1.2, 0.55, 0.35), _lens((x + 0.55, vm + 0.15), 1.2, 0.55, -0.35),
                        circle((x, vm), 0.32, 10)])
        tails = cs_union([stroke([(x, vm), (x - 0.5, vm - hh * 0.38)], 0.4), stroke([(x, vm), (x + 0.5, vm - hh * 0.38)], 0.4)])
        out.append(_st((rib + bow + tails) ^ rect(0.3, v0, L - 0.3, v1), b, 0.4))
    return out, []


def frieze_acanthus(L, h, b, pitch, margin, pair, half):
    """Acanthus: in every bay between the bracket pairs a fan of acanthus leaves rising from a
    bud, two scrolls rolling out from its foot along the frieze (the Rochambeau's eave)."""
    v0, v1 = 0.8, h - 0.8
    hh = v1 - v0
    out = []
    for uc, wd in CO._between(L, pitch, margin, pair, half):
        if wd < 4.6:
            continue
        vb = v0 + 0.4
        fan = cs_union([_lens((uc + math.sin(a) * hh * 0.33, vb + math.cos(a) * hh * 0.33), hh * 0.7, 0.6, math.pi / 2 - a)
                        for a in (-0.6, -0.3, 0.0, 0.3, 0.6)])
        out.append(_st(fan ^ rect(-1e3, v0, 1e3, v1), b, 0.45))
        out.append(_st(circle((uc, vb + 0.2), 0.5, 12), b, 0.55))
        for sg in (-1, 1):
            reach = min(wd / 2 - 0.4, 3.6)
            pts = []
            for t in np.linspace(0.0, 1.0, 18):
                a = math.pi * (1.0 + 1.5 * t) if sg < 0 else -math.pi * 1.5 * t
                r = 0.95 * (1 - 0.5 * t)
                cx = uc + sg * (reach - 0.95)
                pts.append((cx + r * math.cos(a) * (1 if sg > 0 else 1), vb + 0.95 + r * math.sin(a)))
            out.append(_st((stroke([(uc + sg * 0.4, vb + 0.1), (uc + sg * (reach - 0.95), vb)], 0.45) + stroke(pts, 0.42))
                           ^ rect(-1e3, v0, 1e3, v1), b, 0.4))
    return out, []


def runningdog(L, h):
    """A running dog (Vitruvian scroll) as CrossSections: a wave curling over into a scroll at
    every crest, on a fillet."""
    pu = max(2.4, h * 1.4)
    n = max(1, int((L - 0.6) / pu))
    u0 = (L - n * pu) / 2
    out = [rect(0.2, 0.05, L - 0.2, 0.45)]
    r = min(h * 0.28, 0.65)
    for k in range(n):
        x = u0 + pu * k
        cx, cy = x + pu * 0.62, h * 0.52
        pts = [(x, 0.3), (x + pu * 0.3, 0.35)]
        for t in np.linspace(0.0, 1.0, 14):
            a = -math.pi / 2 - t * 1.6 * math.pi
            rr = r * (1 + 0.6 * (1 - t))
            pts.append((cx - rr * math.cos(a + math.pi), cy + rr * math.sin(a)))
        out.append(stroke(pts, 0.42))
    return [cs_union(out) ^ rect(0.2, 0.05, L - 0.2, h - 0.05)]


def course_runningdog(L, h, b, pitch, margin, p):
    """A running dog (Vitruvian scroll) along the course (the Rochambeau)."""
    return [_st(cs, b, 0.45) for cs in runningdog(L, h)]


def course_tripledentil(L, h, b, pitch, margin, p):
    """Dentils in groups of three, a gap between the groups, under a fillet (the
    Rochambeau)."""
    out = [ext(rect(0.2, h - 0.45, L - 0.2, h), b - 0.05, b + 0.55)]
    teeth = []
    u = 0.8
    while u + 3 * 0.9 < L - 0.6:
        for k in range(3):
            teeth.append(rect(u + 0.9 * k, 0.2, u + 0.9 * k + 0.6, h - 0.4))
        u += 3 * 0.9 + 1.1
    if teeth:
        out.append(_st(cs_union(teeth), b, 0.45))
    return out


def bracket_cushionconsole(h, d, t):
    """A cushion console: a block under the soffit, a swelling face curving down and back to a
    small scroll at its foot on the wall, a sunk eye in the scroll (side profile, top at v = 0;
    the Rochambeau)."""
    rf = min(0.7, h * 0.12)
    pts = [(0.0, 0.0), (d, 0.0), (d, -0.9)]
    for s in np.linspace(0.0, 1.0, 14):
        pts.append((d - (d - 2 * rf) * s ** 1.6, -0.9 - (h - 0.9 - 2 * rf) * s))
    pts += [(0.0, -h + 2 * rf)]
    prof = cs_union([poly(pts), circle((rf + 0.15, -h + rf + 0.1), rf + 0.15, 16)])
    return prof - circle((rf + 0.15, -h + rf + 0.1), min(0.45, rf * 0.6), 12)


# ------------------------------------------------------------------ the mansard's window add-ins
def addin_rochambeau(w=5.0, h=10.0, A=0.9):
    """A Rochambeau add-in: a flat-headed two-light window in an architrave, cheeked by two big
    S-scrolls climbing from the sill to a cornice cap, a raised tablet with a shell over the cap;
    its plug's roof a hip."""
    op = rect(-w / 2, 0.0, w / 2, h)
    bars = cs_union([rect(-RIB / 2, -1.0, RIB / 2, h + 1.0), rect(-w, h * 0.55 - 0.3, w, h * 0.55 + 0.3)])
    half = w / 2 + A + 1.6
    vc = h + A + 1.0
    body = cs_union([rect(-half, -0.2, half, vc), poly([(-half + 0.6, vc - 0.1), (half - 0.6, vc - 0.1), (0.0, vc + 2.6)])])
    parts = [ext(body - op, 0.0, 0.6),
             MD.band(op.offset(A, JoinType.Miter, 4.0), A, MD.ARCHITRAVE, clip=rect(-20, 0.0, 20, 40) - op)]
    for sg in (-1, 1):
        x0 = sg * (w / 2 + A + 0.2)
        pts = bezier((x0 + sg * 0.6, 0.6), (x0 + sg * 2.0, h * 0.35), (x0 - sg * 0.2, h * 0.6), (x0 + sg * 0.7, vc - 1.2), 18)
        parts.append(ext(stroke(pts, 0.9), 0.0, 1.0))
        for cc, rr in (((x0 + sg * 1.0, 1.0), 0.75), ((x0 + sg * 1.0, vc - 1.3), 0.6)):
            parts.append(ext(circle(cc, rr, 16) - circle(cc, 0.2, 8), 0.0, 1.15))
    parts.append(MD.run(-half - 0.3, half + 0.3, vc, MD.CROWN, 1.0, up=False))
    tab = rect(-1.6, vc - 0.01, 1.6, vc + 1.8)
    parts.append(ext(tab, 0.0, 0.8))
    parts.append(ext(poly([(0.0, vc + 0.2)] + [(1.3 * math.cos(a), vc + 0.2 + 1.3 * math.sin(a)) for a in np.linspace(0.35, math.pi - 0.35, 9)]),
                     0.79, 1.15))
    sw = half - 0.6
    parts.append(MD.run(-sw, sw, 0.0, MD.SILL, 1.0, up=False))
    parts.append(ext(swag(-1.8, 1.8, -0.8, 0.9, width=0.5) + rect(-2.0, -1.2, 2.0, -0.79), 0.0, 0.7))
    parts = [p - ext(op, -1.0, 5.0) for p in parts]
    outline = body.offset(-0.4, JoinType.Miter, 4.0) ^ rect(-50, 0.2, 50, 100)
    return dict(light=op, bars=bars, frame=parts, outline=outline, top=vc + 2.4, bottom=-1.8)


# ------------------------------------------------------------------ walls, corners, foundation, chimney
def scoredstucco(region, datum=0.0, course=3.0, block=6.0, joint=0.45, d=0.4, g=0.2):
    """Smooth stucco scored as ashlar: a flat coat with fine V-ish joints (a groove ``g`` deep)
    in courses ``course`` high and blocks ``block`` long, broken joint (the Rochambeau)."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    cuts = []
    k = math.floor((v0 - datum) / course) - 1
    while datum + k * course < v1:
        v = datum + k * course
        cuts.append(rect(u0 - 1, v - joint / 2, u1 + 1, v + joint / 2))
        u = u0 - block + (k % 2) * block / 2
        while u < u1 + block:
            cuts.append(rect(u - joint / 2, v, u + joint / 2, v + course))
            u += block
        k += 1
    return M.extrude(region, d) - ext(cs_union(cuts), d - g, d + 0.5)


def corner_chamferquoin(L, at_start, qa, qb, w=2.4, t=0.65):
    """Stucco quoins: blocks long and short in turn, every edge chamfered, standing proud of the
    scored coat at an outside corner, their courses matching the scoring (the Rochambeau)."""
    def span(a, b):
        return (a, b) if at_start else (L - b, L - a)
    parts = []
    v = qa + 0.2
    k = 0
    while v < qb - 2.0:
        leg = 4.6 if k % 2 == 0 else 3.0
        a, b = span(-t - 0.3, leg)
        top = min(v + 2.6, qb - 0.2)
        parts.append(chamfer_box(a, v, b, top, 0.0, t + 0.6, c=0.35, bottom=0.45, square=("u0",) if at_start else ("u1",)))
        v += 3.0
        k += 1
    return union(parts) if parts else M()


def foundation_blindarcade(reg, seed=0):
    """A bluestone base with a blind arcade: a row of sunk round-headed panels between pilaster
    strips, over a plinth and under a cap (the Rochambeau)."""
    b = reg.bounds()
    out = [M.extrude(reg, 0.45)]
    out.append(ext(rect(b[0] - 1, b[3] - 1.2, b[2] + 1, b[3] + 1) ^ reg, 0.44, 0.75))
    out.append(ext(rect(b[0] - 1, b[1] - 1, b[2] + 1, b[1] + 1.4) ^ reg, 0.44, 0.75))
    va, vb = b[1] + 2.2, b[3] - 2.0
    if vb - va > 3.0:
        pw_ = 5.2
        n = max(1, int((b[2] - b[0]) / pw_))
        p = (b[2] - b[0]) / n
        arches = []
        for k in range(n):
            x0, x1 = b[0] + p * k + 0.8, b[0] + p * (k + 1) - 0.8
            if x1 - x0 < 1.6:
                continue
            arches.append(O.opening_cs(x1 - x0, vb - va, (x1 - x0) / 2).translate([(x0 + x1) / 2, va]))
        if arches:
            out = [union(out) - ext(cs_union(arches) ^ reg, 0.2, 2.0)]
    return union(out)


def chimney_rochambeau(w=10.4, d=10.4, h=25.0):
    """The Rochambeau's stacks: stuccoed, with chamfered quoins at the corners, a cornice cap
    and four little piers carrying a low pyramid lid (the smoke leaves between the piers)."""
    h = round(h / 0.2) * 0.2
    sh = h - 6.0
    body = box([-w / 2, -d / 2, 0.0], [w / 2, d / 2, sh])
    for sx in (-1, 1):
        for sy in (-1, 1):
            for k, z in enumerate(np.arange(1.0, sh - 3.0, 2.4)):
                lx, ly = (2.6, 1.6) if k % 2 == 0 else (1.6, 2.6)
                cx, cy = sx * (w / 2 - lx / 2 + 0.3), sy * (d / 2 - ly / 2 + 0.3)
                body = body + box([cx - lx / 2, cy - ly / 2, z], [cx + lx / 2, cy + ly / 2, z + 2.0])
    body = body + M.hull_points([(x, y, sh - 0.01) for x in (-w / 2, w / 2) for y in (-d / 2, d / 2)] +
                                [(x, y, sh + 0.7) for x in (-w / 2 - 0.7, w / 2 + 0.7) for y in (-d / 2 - 0.7, d / 2 + 0.7)])
    body = body + box([-w / 2 - 0.7, -d / 2 - 0.7, sh + 0.69], [w / 2 + 0.7, d / 2 + 0.7, sh + 1.4])
    for sx in (-1, 1):
        for sy in (-1, 1):
            body = body + box([sx * (w / 2 - 1.2) - 1.2, sy * (d / 2 - 1.2) - 1.2, sh + 1.39],
                              [sx * (w / 2 - 1.2) + 1.2, sy * (d / 2 - 1.2) + 1.2, sh + 3.6])
    zc = sh + 3.59
    body = body + box([-w / 2 - 0.3, -d / 2 - 0.3, zc], [w / 2 + 0.3, d / 2 + 0.3, zc + 0.6])
    body = body + M.hull_points([(x, y, zc + 0.59) for x in (-w / 2 - 0.3, w / 2 + 0.3) for y in (-d / 2 - 0.3, d / 2 + 0.3)] +
                                [(0.0, 0.0, h)])
    flue = box([-w / 2 + 2.4, -d / 2 + 2.4, sh - 4.0], [w / 2 - 2.4, d / 2 - 2.4, sh + 3.6])
    return body - flue


def fence_rochambeau(L, h):
    """Rochambeau cresting: ball-topped bars, and between every two a lyre of two C-scrolls back
    to back on the rail with a bead between their heads."""
    pitch = 3.2
    n = max(1, int(round(L / pitch)))
    p = L / n
    rail = h * 0.28
    cells = [rect(0.0, 0.0, L, 0.6), rect(0.0, rail, L, rail + 0.45)]
    for j in range(n + 1):
        u = p * j
        cells.append(rect(u - 0.28, 0.0, u + 0.28, h - 0.8))
        cells.append(circle((u, h - 0.5), 0.5, 12))
        if j < n:
            m = u + p / 2
            vt = h - 1.0
            for sg in (-1, 1):
                pts = bezier((m + sg * 0.25, rail + 0.4), (m + sg * 1.1, rail + 0.9), (m + sg * 1.1, vt - 0.6), (m + sg * 0.3, vt - 0.3), 12)
                cells.append(stroke(pts, 0.42))
            cells.append(circle((m, vt - 0.1), 0.38, 10))
    return cs_union(cells) ^ rect(0.0, 0.0, L, h + 1.0)


def fence_rochambeau_balcony(L, h):
    """The portico roof's iron balustrade: a top rail on square bars, a band of rings between a
    lower rail and a middle one, a scroll at every bar's foot."""
    pitch = 2.6
    n = max(1, int(round(L / pitch)))
    p = L / n
    r1, r2 = h * 0.18, h * 0.42
    cells = [rect(0.0, 0.0, L, 0.6), rect(0.0, r1, L, r1 + 0.45), rect(0.0, r2, L, r2 + 0.45), rect(0.0, h - 0.7, L, h)]
    for j in range(n + 1):
        u = p * j
        cells.append(rect(u - 0.28, 0.0, u + 0.28, h - 0.3))
        if j < n:
            m = u + p / 2
            vc = (r1 + 0.45 + r2) / 2
            rr = min((r2 - r1 - 0.45) / 2 + 0.05, p / 2 - 0.3)
            cells.append(circle((m, vc), rr, 18) - circle((m, vc), max(rr - 0.42, 0.15), 14))
            cells.append(rect(m - 0.22, r2 + 0.4, m + 0.22, h - 0.6))
    return cs_union(cells) ^ rect(0.0, 0.0, L, h)


# ------------------------------------------------------------------ windows and doors
def _gibbs(op, w, h, spring, A, blocks=5, deep=1.4):
    """A Gibbs surround: blocks long and short in turn up each jamb, standing proud of the
    architrave, and a keystone; returns solids."""
    parts = []
    vstep = spring / blocks
    for sg in (-1, 1):
        for k in range(blocks):
            leg = A + 1.4 if k % 2 == 0 else A + 0.6
            u0, u1 = sorted((sg * (w / 2 - 0.1), sg * (w / 2 + leg)))
            parts.append(chamfer_box(u0, k * vstep + 0.2, u1, (k + 1) * vstep - 0.2, 0.0, deep, c=0.3))
    return parts


def _baluster_row(u0, u1, v0, v1, n):
    """Little balusters in silhouette between two rails (for aprons and balconettes)."""
    out = [rect(u0, v0, u1, v0 + 0.5), rect(u0, v1 - 0.5, u1, v1)]
    H = v1 - v0 - 1.0
    for x in np.linspace(u0 + (u1 - u0) / (2 * n), u1 - (u1 - u0) / (2 * n), n):
        out.append(cs_union([rect(x - 0.25, v0 + 0.4, x + 0.25, v1 - 0.4), oval((x, v0 + 0.5 + H * 0.35), 0.45, H * 0.28, 14)]))
    return cs_union(out)


def window_rochambeau_lower(w=9.6, h=22.0, rise=2.0, A=1.0):
    """Rochambeau ground floor: a segmental-headed two-over-two sash in a Gibbs surround (blocks
    long and short up the jambs, voussoirs round the head, a tall keystone), a sill on a band."""
    op = O.opening_cs(w, h, rise)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    sash = O.window_insert(w, h, rise, lites=(2, 2), bare=True)["insert"]
    spring = h - rise
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS),
             MD.band(op.offset(A, JoinType.Miter, 4.0), A, MD.ARCHITRAVE, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op)]
    parts += _gibbs(op, w, h, spring, A)
    ring = (op.offset(A + 1.6, JoinType.Round) - op.offset(A - 0.5, JoinType.Round)) ^ rect(-w, spring - 0.4, w, h + 10)
    vous = []
    for a in np.linspace(0.1, 0.9, 5):
        x = (a - 0.5) * (w + 2 * A + 2.0)
        vous.append(rect(x - 0.22, spring - 1, x + 0.22, h + 10))
    parts.append(ext(ring - cs_union(vous) - rect(-1.0, spring, 1.0, h + 10), 0.0, 1.2))
    parts.append(keystone(0.0, h - 0.6, A + 2.6, 1.6, 2.4, 0.0, 1.6))
    sw = w / 2 + A + 1.0
    parts.append(MD.run(-sw, sw, 0.0, MD.SILL, 1.1, up=False))
    parts.append(ext(rect(-w / 2 - 0.2, -1.8, w / 2 + 0.2, -0.99), 0.0, 0.6))
    return O._one_piece([sash], parts, op, plug_cs, O.PLUG, h + A + 2.6 + 0.2, -1.8)


def window_rochambeau_upper(w=9.0, h=20.0, A=0.9):
    """Rochambeau upper floor: a round-headed one-over-one sash in a moulded architrave with a
    keystone, an archivolt hood on two little consoles at the springing, and a balconette of
    balusters under the sill."""
    r = w / 2
    spring = h - r
    op = O.opening_cs(w, h, r)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    sash = O.window_insert(w, h, r, lites=(1, 1), bare=True)["insert"]
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS),
             MD.band(op.offset(A, JoinType.Round), A, MD.ARCHITRAVE, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op)]
    HB = 1.0
    parts.append(MD.band(op.offset(A + HB - 0.1, JoinType.Round), HB, MD.CROWN, clip=rect(-w - 10, spring, w + 10, h + 40)))
    for sg in (-1, 1):
        parts.append(console(2.4, 1.2, 1.0, u=sg * (r + A + HB / 2 - 0.1), v_top=spring + 0.01, w0=0.0))
    parts.append(keystone(0.0, h - 0.3, A + HB + 0.6, 1.3, 1.9, 0.0, 1.5))
    sw = r + A + 1.2
    parts.append(MD.run(-sw, sw, 0.0, MD.SILL, 1.0, up=False))
    parts.append(ext(_baluster_row(-sw + 0.4, sw - 0.4, -3.4, -0.99, 5), 0.0, 0.8))
    for sg in (-1, 1):
        parts.append(chamfer_box(sg * (sw - 0.4) - 0.5, -3.8, sg * (sw - 0.4) + 0.5, -0.99, 0.0, 1.1, c=0.25))
    return O._one_piece([sash], parts, op, plug_cs, O.PLUG, h + A + HB + 0.8, -3.8)


def door_rochambeau(w=13.0, h=27.0, rise=2.4, A=1.2):
    """The Rochambeau's entrance: a pair of leaves with tall lights and a crossbar over sunk
    panels, under a segmental transom with radiating bars, in a Gibbs surround with voussoirs
    and a scrolled keystone, a cornice over it on two consoles."""
    op = O.opening_cs(w, h, rise)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    spring = h - rise
    dh = spring - 3.6
    mid = 0.5
    lw = (w - 2 * O.CLR - 1.0 - mid) / 2
    body, lights = [ext(plug_cs, -pl, -1.0)], []
    u = -w / 2 + O.CLR + 0.5
    for i in range(2):
        body.append(ext(rect(u, 0.5, u + lw, dh), -pl, -0.8))
        gv0 = dh * 0.4
        lights.append(rect(u + 0.8, gv0, u + lw - 0.8, dh - 0.8))
        body.append(_panel(rect(u + 0.8, 1.2, u + lw - 0.8, gv0 - 0.8)))
        u += lw + mid
    tr = plug_cs.offset(-0.5, JoinType.Miter, 4.0) ^ rect(-w, dh + 0.4, w, h + 2)
    c0 = (0.0, dh + 0.4)
    bars = cs_union([stroke([c0, (w * math.cos(a), dh + 0.4 + w * math.sin(a))], 0.45) for a in np.linspace(0.35, math.pi - 0.35, 5)] +
                    [rect(-w, (dh * 0.4 + dh - 0.8) / 2 - 0.25, w, (dh * 0.4 + dh - 0.8) / 2 + 0.25) ^ cs_union(lights)])
    sash = _glazed(body, cs_union(lights) + tr, pl, bars, plug_cs)
    sash.append(ext(rect(-w, dh - 0.01, w, dh + 0.4) ^ plug_cs, -pl, -0.5))
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS),
             MD.band(op.offset(A, JoinType.Miter, 4.0), A, MD.ARCHITRAVE, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op)]
    parts += _gibbs(op, w, h, spring, A, blocks=7, deep=1.6)
    ring = (op.offset(A + 1.8, JoinType.Round) - op.offset(A - 0.5, JoinType.Round)) ^ rect(-w, spring - 0.4, w, h + 10)
    vous = [rect((a - 0.5) * (w + 2 * A + 2.4) - 0.22, spring - 1, (a - 0.5) * (w + 2 * A + 2.4) + 0.22, h + 10)
            for a in np.linspace(0.1, 0.9, 6)]
    parts.append(ext(ring - cs_union(vous) - rect(-1.2, spring, 1.2, h + 10), 0.0, 1.4))
    vk = h + A + 2.2
    parts.append(MD.scroll_keystone(0.0, h - 0.4, vk - h + 0.4, 1.8, 2.6, 0.0, 1.9))
    half = w / 2 + A + 2.0
    for sg in (-1, 1):
        parts.append(console(3.0, 1.6, 1.3, u=sg * (half - 0.9), v_top=vk + 0.01, w0=0.0))
    parts.append(ext(rect(-half, vk - 1.0, half, vk + 0.6) - rect(-1.4, vk - 2, 1.4, vk + 0.6), 0.0, 0.6))
    vc = vk + 0.6 + 1.4
    parts.append(MD.run(-half - 0.8, half + 0.8, vc, MD.CROWN, 1.4, up=False))
    return O._one_piece(sash, parts, op, plug_cs, pl, vc, 0.0)


def door_rochambeau_back(w=10.0, h=24.0, A=1.0):
    """The Rochambeau's back and side doors: one leaf with a tall light over a sunk panel, a
    flat transom, an architrave with a keystone block and a cornice cap."""
    transom = 3.2
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    dh = h - transom
    u0, u1 = -w / 2 + O.CLR + 0.5, w / 2 - O.CLR - 0.5
    gv0 = dh * 0.42
    body = [ext(plug_cs, -pl, -1.0), ext(rect(u0, 0.5, u1, dh), -pl, -0.8), _panel(rect(u0 + 0.8, 1.2, u1 - 0.8, gv0 - 0.8))]
    light = rect(u0 + 0.9, gv0, u1 - 0.9, dh - 0.8)
    g = plug_cs.offset(-0.5, JoinType.Miter, 4.0) ^ rect(-w, dh + 0.3, w, h + 2)
    sash = _glazed(body, light + g, pl, None, plug_cs)
    sash.append(ext(rect(-w, dh - 0.3, w, dh + 0.3) ^ plug_cs, -pl, -0.4))
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS),
             MD.band(op.offset(A, JoinType.Miter, 4.0), A, MD.ARCHITRAVE, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op)]
    parts.append(chamfer_box(-1.2, h - 0.2, 1.2, h + A + 0.6, 0.0, 1.4, c=0.25))
    half = w / 2 + A + 0.4
    vf = h + A
    parts.append(ext(rect(-half, vf - 0.01, half, vf + 1.4), 0.0, 0.6))
    parts.append(MD.run(-half - 0.6, half + 0.6, vf + 1.4 + 1.0, MD.CROWN, 1.2, up=False))
    return O._one_piece(sash, parts, op, plug_cs, pl, vf + 2.4, 0.0)


# ------------------------------------------------------------------ porch
def post_bandedcolumn(h, collar=None, abacus=3.2, slot=(1.2, 1.0)):
    """A banded column: a round shaft ringed by drums of rustication (broad bands) every third
    of its height up to a plain upper shaft, an astragal, an echinus and a square abacus (the
    Rochambeau's portico)."""
    z1 = h - 2.8
    r, rb = 1.0, 1.32
    prof = [(0.0, 1.19), (1.5, 1.19), (1.5, 1.45), (1.32, 1.7), (1.32, 2.0), (r, 2.4)]
    span = (z1 - 2.4) * 0.62
    nb = 4
    for k in range(nb):
        za = 2.4 + span * (k + 0.25) / nb
        prof += [(r, za), (rb, za + 0.35), (rb, za + 0.35 + 1.0), (r, za + 0.35 + 1.0 + 0.35)]
    prof += [(r * 0.94, z1 - 0.6), (1.12, z1 - 0.4), (1.12, z1 - 0.1), (r * 0.94, z1 + 0.1), (1.32, z1 + 0.75)]
    body = PW._revolve(prof, 32) + PW._plinth(3.0)
    return body + PW._top(h, abacus / 2, z1 + 0.75, 1.32, slot, seg=32)


def baluster_bellbase(h, seg=18):
    """A baluster: a bell-shaped foot, a slender shaft and a ring under the top block (the
    Rochambeau)."""
    prof = [(0.0, 0.8), (0.55, 0.8), (0.52, h * 0.16), (0.36, h * 0.3), (0.28, h * 0.4), (0.26, h * 0.78), (0.42, h * 0.84),
            (0.28, h * 0.9), (0.3, h - 0.8)]
    return PW._revolve(prof, seg) + box([-0.55, -0.55, 0.0], [0.55, 0.55, 0.81]) + box([-0.55, -0.55, h - 0.81], [0.55, 0.55, h])


def frieze_wreathpierced(u0, u1, v_bot, v_top):
    """A porch frieze: an entablature board pierced with a row of laurel wreaths (open rings of
    little leaves) over a moulded fascia (the Rochambeau)."""
    v0 = v_top - 3.2
    board = rect(u0, v0 - 0.8, u1, v_top + 0.05)
    n = max(1, int((u1 - u0) / 4.2))
    holes = []
    for k in range(n):
        c = (u0 + (u1 - u0) * (k + 0.5) / n, v0 + 1.3)
        for a in np.linspace(-0.9, 4.04, 5):          # open at the foot, wide webs: nothing inside comes loose
            holes.append(_lens((c[0] + 0.95 * math.cos(a), c[1] + 0.95 * math.sin(a)), 0.7, 0.42, a + math.pi / 2, seg=6))
    return board - cs_union(holes) if holes else board


def skirt_roundels(reg, d=1.2):
    """A porch skirt of panels, each with a round vent, between plain stiles under a rail (the
    Rochambeau)."""
    u0, v0, u1, v1 = reg.bounds()
    out = M.extrude(reg, d * 0.7)
    stiles = cs_union([rect(u, v0 - 1, u + 0.9, v1 + 1) for u in np.arange(u0, u1, 4.4)] + [rect(u0 - 1, v1 - 0.8, u1 + 1, v1 + 1)])
    out = out + M.extrude(stiles ^ reg, d)
    vm = (v0 + v1 - 0.8) / 2
    rr = min(1.0, (v1 - v0 - 0.8) / 2 - 0.5)
    if rr > 0.4:
        holes = cs_union([circle((u + 2.65, vm), rr, 16) for u in np.arange(u0, u1 - 3.0, 4.4)])
        out = out - M.extrude(holes, d + 1).translate([0, 0, d * 0.35])
    return out


def edge_crescents(L, z0, zc):
    """Porch fascia (the Rochambeau): crescents hung horns-up under the crown, a bead between."""
    out = [rect(0.3, zc - 0.45, L - 0.3, zc)]
    for i, x in enumerate(np.arange(1.2, L - 1.0, 1.6)):
        if i % 2 == 0:
            out.append(circle((x, zc - 0.95), 0.6, 14) - circle((x, zc - 0.6), 0.5, 14))
            out.append(rect(x - 0.2, zc - 0.5, x + 0.2, zc - 0.4))
        else:
            out.append(circle((x, zc - 0.75), 0.35, 10))
    return cs_union(out), 0.6


CO.FRIEZE_EXTRA.update(ribbonmedallions=frieze_medallions, acanthusfan=frieze_acanthus)
CO.COURSE_EXTRA.update(runningdog=course_runningdog, tripledentil=course_tripledentil)
TW.BRACKET_EXTRA.update(cushionconsole=bracket_cushionconsole)
TW.PIERCED = TW.PIERCED + ("cushionconsole",)
TW.FOUNDATION_EXTRA.update(blindarcade=foundation_blindarcade)
SH.CORNER_EXTRA.update(chamferquoin=corner_chamferquoin)
PW.POSTS.update(bandedcolumn=post_bandedcolumn)
PW.BALUSTERS.update(bellbase=(baluster_bellbase, 1.6))
PW.FRIEZES.update(wreathpierced=frieze_wreathpierced)
PW.SKIRTS.update(roundels=skirt_roundels)
FT.EDGE_EXTRA.update(crescents=edge_crescents)


# ================================================================== the Beauvais (house 89)
# A cottage of one storey and a half: peach channel-and-bead siding, cream trim and forest
# accents on a pebble-dashed base; the tall bell-cast mansard is the bedroom storey, chequered
# in square and diamond-pointed slates, with big dormer add-ins and a twin one over the door; a veranda
# wraps the front and both sides.

def slate_chequer(k, j):
    """The Beauvais's slating: a chequer of square slates and diamond-pointed ones, in blocks
    four slates across and three courses up."""
    x = j + 0.5 * (k % 2)
    return "diamond" if (int(math.floor(x / 4.0)) + k // 3) % 2 else "square"


# ------------------------------------------------------------------ cornice ornaments
def frieze_sunflowers(L, h, b, pitch, margin, pair, half):
    """Sunflowers: in every bay between the bracket pairs a sunflower (a ring of petals round a
    seeded disc) on a stem between two broad leaves (the Beauvais's eave)."""
    v0, v1 = 0.8, h - 0.8
    hh = v1 - v0
    out = []
    for uc, wd in CO._between(L, pitch, margin, pair, half):
        if wd < 4.4:
            continue
        R_ = min(hh * 0.3, wd * 0.22, 1.5)
        c = (uc, v1 - R_ - 0.2)
        pet = cs_union([_lens((c[0] + R_ * 0.75 * math.cos(a), c[1] + R_ * 0.75 * math.sin(a)), R_ * 0.75, 0.42, a, seg=6)
                        for a in np.linspace(0, 2 * math.pi, 10, endpoint=False)])
        out.append(_st(pet ^ rect(-1e3, v0, 1e3, v1), b, 0.35))
        out.append(_st(circle(c, R_ * 0.48, 16), b, 0.5))
        stem = stroke([(uc, v0 + 0.1), (uc, c[1] - R_ * 0.5)], 0.42)
        leaves = cs_union([_lens((uc - 0.75, v0 + hh * 0.3), 1.6, 0.6, 0.6), _lens((uc + 0.75, v0 + hh * 0.22), 1.6, 0.6, -0.6)])
        out.append(_st((stem + leaves) ^ rect(-1e3, v0, 1e3, v1), b, 0.4))
    return out, []


def course_interlace(L, h, b, pitch, margin, p):
    """Interlaced arcading: a row of little round arches on stilts, each springing from the
    middle of the last, so they cross into pointed ones (the Beauvais)."""
    pu = max(1.4, h * 0.85)
    n = max(2, int((L - 1.0) / pu))
    u0 = (L - n * pu) / 2
    r = pu
    arcs = []
    for k in range(n - 1):
        c = (u0 + pu * (k + 1), h * 0.25)
        ring = circle(c, r, 24) - circle(c, r - 0.42, 24)
        arcs.append(ring ^ rect(c[0] - r - 1, c[1], c[0] + r + 1, h))
        arcs.append(rect(c[0] - r, 0.15, c[0] - r + 0.42, c[1] + 0.05))
        arcs.append(rect(c[0] + r - 0.42, 0.15, c[0] + r, c[1] + 0.05))
    out = [ext(rect(0.2, 0.0, L - 0.2, 0.3), b - 0.05, b + 0.45)]
    out.append(_st(cs_union(arcs) ^ rect(0.2, 0.0, L - 0.2, h - 0.1), b, 0.4))
    return out


def ovalbar(L, h):
    """Ovals and bars as CrossSections: upright ovals with a short bar between each two, on a
    fillet."""
    pu = max(1.6, h * 1.0)
    n = max(1, int((L - 0.6) / pu))
    u0 = (L - n * pu) / 2
    out = [rect(0.2, 0.05, L - 0.2, 0.4)]
    for k in range(n):
        uc = u0 + pu * (k + 0.5)
        out.append(oval((uc, h * 0.55), pu * 0.27, h * 0.36, 16))
        if k:
            x = u0 + pu * k
            out.append(rect(x - 0.2, 0.3, x + 0.2, h - 0.3))
    return [cs_union(out) ^ rect(0.2, 0.05, L - 0.2, h - 0.05)]


def course_ovalbar(L, h, b, pitch, margin, p):
    """Ovals and bars along the course (the Beauvais)."""
    return [_st(cs, b, 0.45) for cs in ovalbar(L, h)]


def bracket_lyreconsole(h, d, t):
    """A lyre console: its front edge swelling out twice, like the arms of a lyre, from a block
    under the soffit to a ball foot on the wall, a sunk eye between the swells (side profile,
    top at v = 0; the Beauvais)."""
    pts = [(0.0, 0.0), (d, 0.0), (d, -0.8)]
    for s in np.linspace(0.0, 1.0, 20):
        base = d - (d - 1.0) * s
        bulge = 0.45 * math.sin(2 * math.pi * s) ** 2
        pts.append((min(d, base + bulge), -0.8 - (h - 1.8) * s))
    pts += [(0.0, -h + 1.0)]
    prof = cs_union([poly(pts), circle((0.55, -h + 0.75), 0.55, 14)])
    return prof - circle((d * 0.5, -h * 0.5), min(0.5, d * 0.14), 12)


# ------------------------------------------------------------------ the mansard's window add-ins
def addin_beauvais(w=6.4, h=13.0, rise=1.6, A=1.0, twin=False):
    """A Beauvais add-in, big enough to light the bedroom storey: a segmental-headed two-over-two
    light (``twin``: two of them, a mullion between) in a casing, a sunburst in a tympanum under a
    segmental pediment on two brackets; a sill on brackets; its plug's roof a segment."""
    gap = 1.6
    lights = [O.opening_cs(w, h, rise).translate([(-(w + gap) / 2 if twin else 0.0) + k * (w + gap), 0.0])
              for k in range(2 if twin else 1)]
    op = cs_union(lights)
    bars = cs_union([rect(x - RIB / 2, -1.0, x + RIB / 2, h + 1.0) for x in ((-(w + gap) / 2, (w + gap) / 2) if twin else (0.0,))]
                    + [rect(-2 * w, h * 0.48 - 0.3, 2 * w, h * 0.48 + 0.3)])
    half = (w + gap / 2 if twin else w / 2) + A + 1.0
    vt = h + A + 0.4
    rise_p = 2.4 if twin else 1.8
    seg = arch_cs(-half - 0.3, half + 0.3, vt + 2.2, vt + 2.2, rise=rise_p, seg=40)
    body = cs_union([rect(-half, -0.2, half, vt + 2.2), seg])
    parts = [ext(body - op, 0.0, 0.6)]
    for L_ in lights:
        parts.append(MD.band(L_.offset(A, JoinType.Miter, 4.0), A, MD.CASING, clip=rect(-30, 0.0, 30, 40) - op))
    tym = rect(-half + 0.8, vt - 0.2, half - 0.8, vt + 2.2)
    rays = cs_union([stroke([(0.0, vt), (3.0 * math.cos(a), vt + 3.0 * math.sin(a))], 0.42) for a in np.linspace(0.25, math.pi - 0.25, 7)]
                    + [circle((0.0, vt), 0.8, 16)]) ^ tym
    parts.append(ext(tym, 0.0, 0.7) + ext(rays, 0.69, 1.0))
    parts.append(MD.band(seg.offset(0.0, JoinType.Round), 1.0, MD.CROWN, clip=rect(-30, vt + 2.15, 30, 40)))
    parts.append(MD.run(-half - 0.4, half + 0.4, vt + 2.2, MD.CROWN, 0.9, up=False))
    for sg in (-1, 1):
        parts.append(console(2.6, 1.1, 1.0, u=sg * (half - 0.4), v_top=vt + 1.4, w0=0.0))
    sw = half + 0.2
    parts.append(MD.run(-sw, sw, 0.0, MD.SILL, 1.0, up=False))
    for sg in (-1, 1):
        parts.append(console(1.8, 0.9, 0.8, u=sg * (half - 1.2), v_top=-0.99, w0=0.0))
    parts = [p - ext(op, -1.0, 5.0) for p in parts]
    outline = body.offset(-0.4, JoinType.Round) ^ rect(-50, 0.2, 50, 100)
    return dict(light=op, bars=bars, frame=parts, outline=outline, top=vt + 2.2 + rise_p + 1.0, bottom=-2.9)


# ------------------------------------------------------------------ walls, corners, foundation, chimney
def channelbead(region, datum=0.0, pitch=2.0, d=0.36):
    """Channel-and-bead siding: wide flush boards, a deep channel at the foot of each and a
    small bead run along its head (the Beauvais)."""
    from . import skins as SK
    course = [(0.0, 0.08), (0.35, 0.08), (0.45, d), (pitch - 0.55, d), (pitch - 0.45, d - 0.16), (pitch - 0.3, d - 0.02),
              (pitch - 0.15, d - 0.16), (pitch - 0.05, 0.08), (pitch, 0.08)]
    return SK._lap(region, pitch, course, datum=datum)


def corner_bobbin(L, at_start, qa, qb, w=2.4, t=0.65):
    """A corner board with a run of bobbins (raised blocks, long and short in turn) up its
    middle (the Beauvais)."""
    def span(a, b):
        return (a, b) if at_start else (L - b, L - a)
    u0, u1 = span(-t, w)
    parts = [box([u0, qa, 0.0], [u1, qb, t])]
    uc = (u0 + u1) / 2
    v = qa + 0.6
    k = 0
    while v < qb - 1.6:
        ln = 1.6 if k % 2 == 0 else 0.8
        top = min(v + ln, qb - 0.6)
        parts.append(ext(rect(uc - 0.5, v, uc + 0.5, top), t - 0.01, t + 0.35))
        v = top + 0.3
        k += 1
    return union(parts)


def foundation_pebbledash(reg, seed=0):
    """A pebble-dashed base: panels of rough-cast (a scatter of little pebbles) inside smooth
    margins, a plinth and a cap (the Beauvais)."""
    b = reg.bounds()
    out = [M.extrude(reg, 0.3)]
    out.append(ext(rect(b[0] - 1, b[3] - 1.2, b[2] + 1, b[3] + 1) ^ reg, 0.29, 0.75))
    out.append(ext(rect(b[0] - 1, b[1] - 1, b[2] + 1, b[1] + 1.2) ^ reg, 0.29, 0.7))
    rng = np.random.default_rng(seed + 89)
    pan_w = 9.0
    n = max(1, int((b[2] - b[0]) / pan_w))
    p = (b[2] - b[0]) / n
    for k in range(n):
        x0, x1 = b[0] + p * k + 0.8, b[0] + p * (k + 1) - 0.8
        y0, y1 = b[1] + 1.8, b[3] - 1.8
        if x1 - x0 < 2.0 or y1 - y0 < 1.2:
            continue
        pan = rect(x0, y0, x1, y1) ^ reg
        if pan.is_empty():
            continue
        pts = [(x, y) for x in np.arange(x0 + 0.4, x1 - 0.3, 0.75) for y in np.arange(y0 + 0.4, y1 - 0.3, 0.75)]
        peb = cs_union([circle((x + rng.uniform(-0.15, 0.15), y + rng.uniform(-0.15, 0.15)), 0.3, 6) for x, y in pts]) ^ pan
        out.append(ext(peb, 0.29, 0.6))
    return union(out)


def chimney_beauvais(w=10.0, d=8.4, h=24.0):
    """The Beauvais's stacks: brick with a sunk diamond on every face, a corbelled necking, and an
    arched hood over the flue (a vault on two end walls)."""
    h = round(h / 0.2) * 0.2
    sh = h - 5.4
    body = box([-w / 2, -d / 2, 0.0], [w / 2, d / 2, sh])
    for (L, D, rot) in ((w, d, 0), (d, w, 90), (w, d, 180), (d, w, 270)):
        dm = min(L * 0.32, 3.0)
        cs = poly([(0.0, sh * 0.5 - dm * 1.4), (dm, sh * 0.5), (0.0, sh * 0.5 + dm * 1.4), (-dm, sh * 0.5)])
        cut = ext(cs, -0.4, 0.01).transform(np.array([[1.0, 0, 0, 0], [0, 0, 1.0, 0], [0, 1.0, 0, 0]])).translate([0, D / 2, 0])
        body = body - cut.rotate([0, 0, rot])
    for k, g in enumerate((0.3, 0.6, 0.9)):
        body = body + box([-w / 2 - g, -d / 2 - g, sh - 1.8 + 0.6 * k], [w / 2 + g, d / 2 + g, sh - 1.2 + 0.6 * k + 0.01])
    body = body + box([-w / 2 - 0.6, -d / 2 - 0.6, sh - 0.01], [w / 2 + 0.6, d / 2 + 0.6, sh + 0.6])
    ends = [box([sx * (w / 2 - 0.6) - 0.6, -d / 2 + 0.6, sh + 0.59], [sx * (w / 2 - 0.6) + 0.6, d / 2 - 0.6, h - 2.0]) for sx in (-1, 1)]
    vault = ext(rect(-d / 2 + 0.6, h - 4.0, d / 2 - 0.6, h - 0.01) - circle((0.0, h - 4.0), d / 2 - 1.6, 24) +
                (circle((0.0, h - 4.0), d / 2 - 0.6, 32) - circle((0.0, h - 4.0), d / 2 - 1.6, 32)), -w / 2, w / 2)
    vault = vault.transform(np.array([[0, 0, 1.0, 0], [1.0, 0, 0, 0], [0, 1.0, 0, 0]])) ^ box([-w, -d, h - 4.0], [w, d, h])
    body = body + union(ends) + vault
    return body - box([-w / 2 + 1.8, -d / 2 + 1.8, sh - 4.0], [w / 2 - 1.8, d / 2 - 1.8, sh + 0.61])


def fence_beauvais(L, h):
    """Beauvais cresting: bars ending in shepherd's crooks, turned alternately, and a daisy (a
    ring of six round petals) between every two on the rail."""
    pitch = 3.0
    n = max(1, int(round(L / pitch)))
    p = L / n
    rail = h * 0.3
    cells = [rect(0.0, 0.0, L, 0.6), rect(0.0, rail, L, rail + 0.45)]
    for j in range(n + 1):
        u = p * j
        sg = 1 if j % 2 == 0 else -1
        cells.append(rect(u - 0.28, 0.0, u + 0.28, h - 1.0))
        hook = [(u + sg * 0.6 * (1 - math.cos(a)), h - 1.0 + 0.6 * math.sin(a)) for a in np.linspace(0.0, math.pi * 1.25, 10)]
        cells.append(stroke([(u, h - 1.05)] + hook, 0.42))
        if j < n:
            m = u + p / 2
            vc = (rail + 0.45 + h - 0.9) / 2
            cells += [circle((m + 0.55 * math.cos(a), vc + 0.55 * math.sin(a)), 0.32, 10) for a in np.linspace(0, 2 * math.pi, 6, endpoint=False)]
            cells.append(circle((m, vc), 0.32, 10))
            cells.append(rect(m - 0.2, rail + 0.4, m + 0.2, vc - 0.5))
    return cs_union(cells) ^ rect(0.0, 0.0, L, h + 1.0)


# ------------------------------------------------------------------ windows and doors
def window_beauvais(w=9.6, h=26.0, A=1.1):
    """Beauvais ground floor: a tall flat-headed two-over-two sash in a casing with corner
    blocks, a frieze with a sunflower, and a shed hood on two sawn brackets; a sill on brackets."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    sash = O.window_insert(w, h, 0, lites=(2, 2), bare=True)["insert"]
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS),
             MD.band(op.offset(A, JoinType.Miter, 4.0), A, MD.CASING, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op)]
    half = w / 2 + A + 0.6
    vf = h + A
    parts.append(ext(rect(-half + 0.3, vf - 0.01, half - 0.3, vf + 2.6), 0.0, 0.55))
    c = (0.0, vf + 1.3)
    parts.append(ext(cs_union([_lens((c[0] + 0.7 * math.cos(a), c[1] + 0.7 * math.sin(a)), 0.7, 0.42, a, seg=6)
                               for a in np.linspace(0, 2 * math.pi, 10, endpoint=False)]), 0.54, 0.85))
    parts.append(ext(circle(c, 0.55, 14), 0.54, 1.05))
    for sg in (-1, 1):
        x0 = sg * (half - 0.3)
        br = poly([(x0, vf + 2.6), (x0 + sg * 1.6, vf + 2.6), (x0 + sg * 1.6, vf + 2.0), (x0 + sg * 0.5, vf - 1.6), (x0, vf - 1.6)])
        parts.append(ext(br - circle((x0 + sg * 0.75, vf + 1.2), 0.35, 10), 0.0, 1.2))
    vh = vf + 2.6
    parts.append(ext(rect(-half - 1.8, vh - 0.05, half + 1.8, vh + 0.7), 0.0, 1.6))
    parts.append(ext(rect(-half - 1.8, vh + 0.69, half + 1.8, vh + 1.3), 0.0, 1.0))
    sw = w / 2 + A + 0.4
    parts.append(MD.run(-sw, sw, 0.0, MD.SILL, 1.0, up=False))
    for sg in (-1, 1):
        parts.append(console(2.0, 0.9, 0.8, u=sg * (w / 2 - 0.3), v_top=-0.99, w0=0.0))
    return O._one_piece([sash], parts, op, plug_cs, O.PLUG, vh + 1.3, -3.0)


def door_beauvais(w=19.0, h=27.0, A=1.1):
    """The Beauvais's entrance: one leaf with a big segmental-headed light over two panels,
    sidelights over panels either side, a transom across the whole of it barred in diamonds; a
    casing, a frieze with a sunburst and a cornice with a sawn crest of sunflowers."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    transom = 4.0
    dh = h - transom
    lw = 8.6
    sl = (w - 2 * O.CLR - lw - 2 * 0.7) / 2
    body = [ext(plug_cs, -pl, -1.0)]
    u0 = -lw / 2
    body.append(ext(rect(u0, 0.5, u0 + lw, dh), -pl, -0.8))
    gv0 = dh * 0.42
    lights = [O.opening_cs(lw - 1.6, dh - 0.8 - gv0, 1.2).translate([0.0, gv0])]
    for k in range(2):
        body.append(_panel(rect(u0 + 0.8 + k * (lw - 1.6) / 2 + (0.2 if k else 0.0), 1.2, u0 + 0.8 + (k + 1) * (lw - 1.6) / 2 - (0.0 if k else 0.2), gv0 - 0.8)))
    for sg in (-1, 1):
        x0, x1 = sorted((sg * (lw / 2 + 0.7), sg * (lw / 2 + 0.7 + sl)))
        lights.append(rect(x0 + 0.4, gv0, x1 - 0.4, dh - 0.8))
        body.append(_panel(rect(x0 + 0.4, 1.2, x1 - 0.4, gv0 - 0.8)))
    tr = plug_cs.offset(-0.5, JoinType.Miter, 4.0) ^ rect(-w, dh + 0.4, w, h + 2)
    tv0, tv1 = dh + 0.4, h - O.CLR - 0.5
    dia = []
    for x in np.arange(-w / 2 + 1.6, w / 2 - 1.0, 2.4):
        dia.append(stroke([(x - 1.2, tv0), (x, tv1), (x + 1.2, tv0)], 0.42, caps=False))
    bars = cs_union(dia) ^ tr
    sash = _glazed(body, cs_union(lights) + tr, pl, bars, plug_cs)
    sash.append(ext(rect(-w, dh - 0.01, w, dh + 0.4) ^ plug_cs, -pl, -0.5))
    sash.append(ext(cs_union([rect(sg * (lw / 2 + 0.35) - 0.35, 0.0, sg * (lw / 2 + 0.35) + 0.35, dh) for sg in (-1, 1)]) ^ plug_cs, -pl, -0.5))
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS),
             MD.band(op.offset(A, JoinType.Miter, 4.0), A, MD.CASING, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op)]
    half = w / 2 + A + 0.4
    vf = h + A
    parts.append(ext(rect(-half, vf - 0.01, half, vf + 2.4), 0.0, 0.6))
    rays = cs_union([stroke([(0.0, vf + 0.2), (2.6 * math.cos(a), vf + 0.2 + 2.6 * math.sin(a))], 0.42) for a in np.linspace(0.3, math.pi - 0.3, 7)])
    parts.append(ext(rays ^ rect(-half, vf, half, vf + 2.3), 0.59, 0.9))
    parts.append(ext(circle((0.0, vf + 0.2), 0.9, 16) ^ rect(-2, vf, 2, vf + 2), 0.59, 1.0))
    vc = vf + 2.4 + 1.2
    parts.append(MD.run(-half - 0.8, half + 0.8, vc, MD.CROWN, 1.2, up=False))
    crest = rect(-half + 0.4, vc - 0.01, half - 0.4, vc + 0.6)
    for x in np.linspace(-half + 2.0, half - 2.0, 5):
        c = (x, vc + 1.5)
        crest = crest + cs_union([circle((c[0] + 0.6 * math.cos(a), c[1] + 0.6 * math.sin(a)), 0.36, 10) for a in np.linspace(0, 2 * math.pi, 7, endpoint=False)]
                                 + [circle(c, 0.4, 10), rect(x - 0.22, vc + 0.5, x + 0.22, vc + 1.1)])
    parts.append(ext(crest, 0.0, 0.8))
    return O._one_piece(sash, parts, op, plug_cs, pl, vc + 2.3, 0.0)


def door_beauvais_back(w=10.0, h=25.0, A=1.0):
    """The Beauvais's back door: one leaf with a segmental-headed light over two panels, a flat
    transom, a casing and a shed hood on brackets."""
    transom = 3.2
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    dh = h - transom
    u0, u1 = -w / 2 + O.CLR + 0.5, w / 2 - O.CLR - 0.5
    gv0 = dh * 0.45
    mid = (u0 + u1) / 2
    body = [ext(plug_cs, -pl, -1.0), ext(rect(u0, 0.5, u1, dh), -pl, -0.8),
            _panel(rect(u0 + 0.8, 1.2, mid - 0.3, gv0 - 0.8)), _panel(rect(mid + 0.3, 1.2, u1 - 0.8, gv0 - 0.8))]
    light = O.opening_cs(u1 - u0 - 1.8, dh - 0.8 - gv0, 1.0).translate([mid, gv0])
    g = plug_cs.offset(-0.5, JoinType.Miter, 4.0) ^ rect(-w, dh + 0.3, w, h + 2)
    sash = _glazed(body, light + g, pl, None, plug_cs)
    sash.append(ext(rect(-w, dh - 0.3, w, dh + 0.3) ^ plug_cs, -pl, -0.4))
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS),
             MD.band(op.offset(A, JoinType.Miter, 4.0), A, MD.CASING, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op)]
    half = w / 2 + A + 0.4
    vf = h + A
    for sg in (-1, 1):
        x0 = sg * (half - 0.2)
        parts.append(ext(poly([(x0, vf + 1.2), (x0 + sg * 1.4, vf + 1.2), (x0 + sg * 1.4, vf + 0.6), (x0 + sg * 0.4, vf - 1.6), (x0, vf - 1.6)]), 0.0, 1.1))
    parts.append(ext(rect(-half, vf - 0.01, half, vf + 1.2), 0.0, 0.6))
    parts.append(ext(rect(-half - 1.6, vf + 1.19, half + 1.6, vf + 1.9), 0.0, 1.5))
    return O._one_piece(sash, parts, op, plug_cs, pl, vf + 1.9, 0.0)


# ------------------------------------------------------------------ porch
def post_twinvase(h, collar=None, abacus=3.0, slot=(1.2, 1.0)):
    """A post turned as two vases end to end: one swelling up from the plinth, one down from the
    capital, their necks meeting at a ring half way up (the Beauvais's veranda)."""
    z1 = h - 2.6
    zm = round(z1 * 0.5 / 0.2) * 0.2
    prof = [(0.0, 1.19), (1.5, 1.19), (1.5, 1.45), (1.2, 1.7), (1.0, 2.0),
            (1.3, 2.0 + (zm - 2.0) * 0.3), (1.2, 2.0 + (zm - 2.0) * 0.55), (0.75, zm - 0.6), (1.15, zm - 0.3), (1.15, zm + 0.3),
            (0.75, zm + 0.6), (1.2, zm + (z1 - zm) * 0.45), (1.3, zm + (z1 - zm) * 0.7), (1.0, z1 - 0.2), (1.3, z1 + 0.7)]
    body = PW._revolve(prof, 32) + PW._plinth(3.0)
    return body + PW._top(h, abacus / 2, z1 + 0.7, 1.3, slot, seg=32)


def fill_ringstack(L, vb, vt):
    """A railing of stacked rings: in every panel between stiles two rings one over the other,
    touching the rails and each other, tied to the stiles by a bar through each; every member
    0.7 wide, so it stands in a one-piece porch top (the Beauvais)."""
    H = vt - vb
    R_ = H / 4 + 0.1
    n = max(1, int(round(L / max(2 * R_ + 1.6, 3.0))))
    parts = []
    for i in range(n + 1):
        x = L * i / n
        parts.append(rect(x - 0.35, vb, x + 0.35, vt))
        if i < n:
            m = x + L / n / 2
            for vc in (vb + H / 4, vt - H / 4):
                hole = circle((m, vc), max(R_ - 0.7, 0.3), 20)
                parts.append(circle((m, vc), R_, 24) - hole)
                parts.append(rect(x, vc - 0.35, x + L / n, vc + 0.35) - hole)
    return [cs_union(parts) ^ rect(0.0, vb, L, vt)]


def frieze_scrollarch(u0, u1, v_bot, v_top):
    """A porch frieze: a valance board, and under it in every bay a shallow arch made of two
    C-scrolls meeting at a drop (the Beauvais)."""
    v0 = v_top - 2.0
    out = [rect(u0, v0, u1, v_top + 0.05)]
    n = max(1, int((u1 - u0) / 8.0))
    p = (u1 - u0) / n
    for k in range(n):
        a, e = u0 + p * k + 0.4, u0 + p * (k + 1) - 0.4
        m = (a + e) / 2
        for sg, x0 in ((1, a), (-1, e)):
            pts = bezier((x0, v0 + 0.1), (x0 + sg * p * 0.12, v0 - 2.4), (m - sg * p * 0.18, v0 - 1.4), (m, v0 - 0.9), 14)
            out.append(stroke(pts, 0.5))
        out.append(cs_union([rect(m - 0.25, v0 - 1.2, m + 0.25, v0 + 0.05), circle((m, v0 - 1.4), 0.42, 12)]))
    return cs_union(out)


def skirt_basketweave(reg, d=1.2):
    """A porch skirt of slats in basket weave: little squares of three slats, laid alternately
    across and up (the Beauvais)."""
    u0, v0, u1, v1 = reg.bounds()
    out = [M.extrude(reg, d * 0.35)]
    s = 2.4
    sl = []
    for i, u in enumerate(np.arange(u0, u1, s)):
        for j, v in enumerate(np.arange(v0, v1, s)):
            if (i + j) % 2 == 0:
                sl += [rect(u + 0.2, v + 0.2 + k * 0.7, u + s - 0.2, v + 0.2 + k * 0.7 + 0.5) for k in range(3)]
            else:
                sl += [rect(u + 0.2 + k * 0.7, v + 0.2, u + 0.2 + k * 0.7 + 0.5, v + s - 0.2) for k in range(3)]
    out.append(M.extrude(cs_union(sl) ^ reg, d))
    return union(out)


def edge_icicles(L, z0, zc):
    """Porch fascia (the Beauvais): icicle drops of three lengths in turn hung under the crown."""
    out = [rect(0.3, zc - 0.45, L - 0.3, zc)]
    for i, x in enumerate(np.arange(0.9, L - 0.6, 0.9)):
        ln = (0.9, 1.5, 1.2)[i % 3]
        out.append(poly([(x - 0.3, zc - 0.4), (x + 0.3, zc - 0.4), (x, zc - 0.4 - ln)]))
    return cs_union(out), 0.6


CO.FRIEZE_EXTRA.update(sunflowers=frieze_sunflowers)
CO.COURSE_EXTRA.update(interarcade=course_interlace, ovalbar=course_ovalbar)
TW.BRACKET_EXTRA.update(lyreconsole=bracket_lyreconsole)
TW.PIERCED = TW.PIERCED + ("lyreconsole",)
TW.FOUNDATION_EXTRA.update(pebbledash=foundation_pebbledash)
SH.CORNER_EXTRA.update(bobbinboard=corner_bobbin)
PW.POSTS.update(twinvase=post_twinvase)
PW.FILLS.update(ringstack=fill_ringstack)
PW.FRIEZES.update(scrollarch=frieze_scrollarch)
PW.SKIRTS.update(basketweave=skirt_basketweave)
FT.EDGE_EXTRA.update(icicles=edge_icicles)


# ================================================================== the Fontaine (house 90)
# The batch's grand house, an H in plan: grey granite, the ground storey in banded rustication,
# the upper one in fine ashlar, vermiculated quoins, marble dressings and verdigris accents. A
# centre range with a straight mansard between two end pavilions that break forward and back
# under taller mansards of their own; a square tower in the middle of the front rising over the
# eave to a swelling dome with a bannerette vane; a veranda filling the recess between the
# pavilions round the foot of the tower.

def slate_pyramids(k, j):
    """The Fontaine's slating: square slates, with a band of pyramids (filled triangles of
    diamond-cut slates, seven slates wide at the foot, four courses tall) low on the roof, a
    pyramid every ten slates."""
    r = k % 22 - 2
    if 0 <= r <= 3:
        m = (j + 0.5 * (k % 2)) % 10 - 5.0
        if abs(m) <= 3.0 - r + 0.01:
            return "diamond"
    return "square"


# ------------------------------------------------------------------ cornice ornaments
def frieze_lozengerosettes(L, h, b, pitch, margin, pair, half):
    """Lozenges and rosettes: a run of lozenge frames, each round a rosette, with a disc between
    every two (the Fontaine's storey joint)."""
    v0, v1 = 0.8, h - 0.8
    hh = v1 - v0
    vm = (v0 + v1) / 2
    pu = max(hh * 1.5, 5.0)
    n = max(1, int((L - 1.0) / pu))
    u0 = (L - n * pu) / 2
    out = []
    for k in range(n):
        uc = u0 + pu * (k + 0.5)
        hw = pu * 0.38
        loz = poly([(uc - hw, vm), (uc, v1), (uc + hw, vm), (uc, v0)])
        out.append(_st(loz - loz.offset(-0.5, JoinType.Miter, 4.0), b, 0.45))
        pet = cs_union([circle((uc + hh * 0.17 * math.cos(a), vm + hh * 0.17 * math.sin(a)), max(0.3, hh * 0.1), 10)
                        for a in np.linspace(0, 2 * math.pi, 6, endpoint=False)] + [circle((uc, vm), 0.35, 10)])
        out.append(_st(pet, b, 0.4))
        if k:
            out.append(_st(circle((u0 + pu * k, vm), min(0.7, hh * 0.18), 14), b, 0.5))
    return out, []


def frieze_coronets(L, h, b, pitch, margin, pair, half):
    """Coronets: in every bay between the bracket pairs a little crown (a band, five points
    tipped with pearls, a jewelled rim) over crossed palm sprigs (the Fontaine's eave)."""
    v0, v1 = 0.8, h - 0.8
    hh = v1 - v0
    out = []
    for uc, wd in CO._between(L, pitch, margin, pair, half):
        if wd < 4.4:
            continue
        cw = min(wd * 0.36, 2.6)
        vb = v0 + hh * 0.35
        band = rect(uc - cw, vb, uc + cw, vb + 0.6)
        pts = []
        for i in range(5):
            x = uc - cw + 2 * cw * i / 4
            pts.append(poly([(x - 0.35, vb + 0.55), (x + 0.35, vb + 0.55), (x, vb + 0.55 + hh * 0.32)]))
        pearls = [circle((uc - cw + 2 * cw * i / 4, vb + 0.55 + hh * 0.32 + 0.2), 0.3, 10) for i in range(5)]
        out.append(_st(cs_union([band] + pts) ^ rect(-1e3, v0, 1e3, v1), b, 0.45))
        out.append(_st(cs_union(pearls) ^ rect(-1e3, v0, 1e3, v1), b, 0.55))
        for sg in (-1, 1):
            out.append(_st(_lens((uc + sg * cw * 0.5, v0 + hh * 0.18), cw * 1.3, 0.55, sg * 0.35) ^ rect(-1e3, v0, 1e3, v1), b, 0.35))
    return out, []


def loopknot(L, h):
    """A loop knot as CrossSections: one strand running along in a row of open loops, each
    crossing itself, on a fillet."""
    pu = max(2.2, h * 1.3)
    n = max(1, int((L - 0.6) / pu))
    u0 = (L - n * pu) / 2
    r = min(h * 0.3, 0.7)
    pts = []
    for t in np.linspace(0.0, n, n * 24 + 1):
        a = 2 * math.pi * t
        pts.append((u0 + pu * t + r * 1.1 * math.sin(a), h * 0.5 - r * math.cos(a)))
    return [cs_union([stroke(pts, 0.42), rect(0.2, 0.05, L - 0.2, 0.4)]) ^ rect(0.2, 0.05, L - 0.2, h - 0.05)]


def course_loopknot(L, h, b, pitch, margin, p):
    """A loop knot running along the course (the Fontaine)."""
    return [_st(cs, b, 0.45) for cs in loopknot(L, h)]


def course_bellchain(L, h, b, pitch, margin, p):
    """A chain of little bells hung from a cord, a bead between every two (the Fontaine)."""
    pu = max(1.8, h * 1.1)
    n = max(1, int((L - 0.6) / pu))
    u0 = (L - n * pu) / 2
    out = [rect(0.2, h - 0.5, L - 0.2, h - 0.1)]
    for k in range(n):
        uc = u0 + pu * (k + 0.5)
        bh = h - 0.9
        out.append(poly([(uc - 0.25, h - 0.3), (uc + 0.25, h - 0.3), (uc + pu * 0.3, 0.45), (uc - pu * 0.3, 0.45)]))
        out.append(circle((uc, 0.35), 0.28, 8))
        if k:
            out.append(circle((u0 + pu * k, h - 0.55), 0.3, 8))
    return [_st(cs_union(out) ^ rect(0.2, 0.05, L - 0.2, h), b, 0.45)]


def bracket_ramshorn(h, d, t):
    """A ram's-horn console: a body tapering from the wall up and out to a big spiral horn that
    curls under the soffit's front edge, a sunk eye in the horn (side profile, top at v = 0; the
    Fontaine)."""
    r = min(0.3 * h, 0.4 * d, 1.2)
    c = (d - r, -r)
    pts = [(0.0, 0.0), (d - r, 0.0)]
    for t_ in np.linspace(0.0, 1.0, 12):
        a = math.pi / 2 - t_ * math.pi * 1.4
        pts.append((c[0] + r * math.cos(a), c[1] + r * math.sin(a)))
    pts += [(d * 0.45, -h * 0.55), (0.9, -h + 0.6), (0.0, -h + 0.6)]
    prof = cs_union([poly(pts), circle(c, r, 20), circle((0.5, -h + 0.7), 0.5, 12)])
    return prof - circle(c, min(0.5, r * 0.45), 12)


# ------------------------------------------------------------------ the mansard's window add-ins
def addin_fontaine(w=5.0, h=8.6, A=0.9, big=False):
    """A Fontaine add-in: a two-tier dormer, a flat-headed two-light window and a round
    oculus over it inside one eared frame, a segmental pediment over all with a ball finial;
    ``big`` is a wider one for a pavilion's front. Its plug's roof is a segment."""
    if big:
        w, h = w + 1.6, h + 0.8
    op = rect(-w / 2, 0.0, w / 2, h)
    ro = min(1.6, w * 0.3)
    oc = (0.0, h + 1.0 + ro)
    ocul = circle(oc, ro, 28)
    light = cs_union([op, ocul])
    bars = cs_union([rect(-RIB / 2, -1.0, RIB / 2, h + 1.0), rect(-w, h * 0.55 - 0.3, w, h * 0.55 + 0.3),
                     rect(-ro - 1, oc[1] - RIB / 2, ro + 1, oc[1] + RIB / 2)])
    half = w / 2 + A + 0.7
    vt = oc[1] + ro + A
    seg = arch_cs(-half - 0.2, half + 0.2, vt - 0.2, vt - 0.2, rise=2.0, seg=40)
    body = cs_union([rect(-half, -0.2, half, vt - 0.2), seg])
    ears = rect(-half - 0.4, h - 1.2, half + 0.4, h + 0.4)
    parts = [ext(body - light, 0.0, 0.6),
             MD.band(op.offset(A, JoinType.Miter, 4.0), A, MD.ARCHITRAVE, clip=rect(-20, 0.0, 20, 40) - light),
             MD.band(ocul.offset(A * 0.8, JoinType.Round), A * 0.8, MD.CASING, clip=rect(-20, h + 0.2, 20, 40) - light),
             ext(ears - light, 0.0, 1.0)]
    parts.append(MD.band(seg, 1.0, MD.CROWN, clip=rect(-30, vt - 0.25, 30, 40)))
    parts.append(MD.run(-half - 0.3, half + 0.3, vt - 0.2, MD.CROWN, 0.9, up=False))
    parts.append(ext(cs_union([rect(-0.45, vt + 1.6, 0.45, vt + 2.4), circle((0.0, vt + 2.8), 0.7, 16)]), 0.0, 1.1))
    sw = half + 0.2
    parts.append(MD.run(-sw, sw, 0.0, MD.SILL, 1.0, up=False))
    for sg in (-1, 1):
        parts.append(chamfer_box(sg * (w / 2) - 0.6, -1.8, sg * (w / 2) + 0.6, -0.8, 0.0, 0.9, c=0.25))
    parts = [p - ext(light, -1.0, 5.0) for p in parts]
    outline = body.offset(-0.4, JoinType.Round) ^ rect(-50, 0.2, 50, 100)
    return dict(light=light, bars=bars, frame=parts, outline=outline, top=vt + 3.5, bottom=-1.8)


def addin_fontaine_oculus(r=2.4, A=0.9):
    """The Fontaine's dome add-in: a round oculus in a wreath of laurel tied with a bow at its
    foot, a keyblock at its head (its plug round-topped)."""
    c = (0.0, r + 0.6)
    light = circle(c, r, 32)
    bars = cs_union([rect(-RIB / 2, -1.0, RIB / 2, 2 * r + 2), rect(-r - 1, c[1] - RIB / 2, r + 1, c[1] + RIB / 2)])
    R_ = r + A + 0.9
    disc = circle(c, R_, 40)
    body = cs_union([disc, rect(-R_, -0.2, R_, c[1])])
    leaves = cs_union([_lens((c[0] + (r + A + 0.3) * math.cos(a), c[1] + (r + A + 0.3) * math.sin(a)), 1.3, 0.6, a + math.pi / 2)
                       for a in list(np.linspace(-1.1, 1.25, 5)) + list(np.linspace(math.pi - 1.25, math.pi + 1.1, 5))])
    parts = [ext(body - light, 0.0, 0.6), MD.band(light.offset(A, JoinType.Round), A, MD.ARCHITRAVE, clip=rect(-20, -1, 20, 40) - light),
             ext(leaves - light.offset(A - 0.1, JoinType.Round), 0.59, 1.0)]
    parts.append(ext(cs_union([circle((c[0] - 0.6, c[1] - R_ + 0.5), 0.45, 10), circle((c[0] + 0.6, c[1] - R_ + 0.5), 0.45, 10),
                               circle((c[0], c[1] - R_ + 0.5), 0.35, 10)]), 0.0, 1.1))
    parts.append(chamfer_box(-0.8, c[1] + r - 0.2, 0.8, c[1] + R_ + 0.3, 0.0, 1.3, c=0.25))
    parts = [p - ext(light, -1.0, 5.0) for p in parts]
    outline = body.offset(-0.4, JoinType.Round) ^ rect(-50, 0.2, 50, 100)
    return dict(light=light, bars=bars, frame=parts, outline=outline, top=c[1] + R_ + 0.3, bottom=-0.2)


# ------------------------------------------------------------------ walls, corners, foundation, chimney
def bandedrustic(region, datum=0.0, course=3.0, joint=0.5, d=0.45, v=0.25):
    """Banded rustication: courses of stone with only their beds cut, as deep V channels (the
    edges chamfered), no upright joints (the Fontaine's ground storey)."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    out = [M.extrude(region, d - v)]
    k = math.floor((v0 - datum) / course) - 1
    bands = []
    while datum + k * course < v1:
        vb = datum + k * course
        bands.append(chamfer_box(u0 - 2, vb + joint / 2, u1 + 2, vb + course - joint / 2, d - v - 0.01, v + 0.01, c=v))
        k += 1
    return union(out) + (union(bands) ^ ext(region, 0.0, d + 1.0))


def ashlarfine(region, datum=0.0, course=3.0, block=7.2, joint=0.4, d=0.4, g=0.2):
    """Fine ashlar: smooth blocks in regular courses, broken joint, with fine sunk joints (the
    Fontaine's upper storey)."""
    if region.is_empty():
        return M()
    u0, v0, u1, v1 = region.bounds()
    cuts = []
    k = math.floor((v0 - datum) / course) - 1
    while datum + k * course < v1:
        vb = datum + k * course
        cuts.append(rect(u0 - 1, vb - joint / 2, u1 + 1, vb + joint / 2))
        u = u0 - block + (k % 2) * block / 2 + (k % 3) * 0.3
        while u < u1 + block:
            cuts.append(rect(u - joint / 2, vb, u + joint / 2, vb + course))
            u += block
        k += 1
    return M.extrude(region, d) - ext(cs_union(cuts), d - g, d + 0.5)


def corner_vermiquoin(L, at_start, qa, qb, w=2.4, t=0.65):
    """Vermiculated quoins: blocks long and short in turn, their faces worked all over with
    worm-tracks (short wandering raised strokes) inside a smooth margin (the Fontaine)."""
    def span(a, b):
        return (a, b) if at_start else (L - b, L - a)
    rng = np.random.default_rng(90 + int(L))
    parts = []
    v = qa + 0.2
    k = 0
    while v < qb - 2.0:
        leg = 5.0 if k % 2 == 0 else 3.2
        a, b = span(-t - 0.3, leg)
        top = min(v + 2.6, qb - 0.2)
        parts.append(chamfer_box(a, v, b, top, 0.0, t + 0.45, c=0.25, bottom=0.45, square=("u0",) if at_start else ("u1",)))
        fa, fb = span(0.5, leg - 0.6)
        worms = []
        for _ in range(int((fb - fa) * (top - v) / 1.4)):
            x0, y0 = rng.uniform(fa, fb), rng.uniform(v + 0.6, top - 0.6)
            ang = rng.uniform(0, math.pi)
            pts = [(x0, y0)]
            for _s in range(3):
                ang += rng.uniform(-1.2, 1.2)
                pts.append((pts[-1][0] + 0.45 * math.cos(ang), pts[-1][1] + 0.45 * math.sin(ang)))
            worms.append(stroke(pts, 0.4))
        if worms:
            parts.append(ext(cs_union(worms) ^ rect(min(fa, fb), v + 0.5, max(fa, fb), top - 0.5), t + 0.44, t + 0.65))
        v += 3.0
        k += 1
    return union(parts) if parts else M()


def foundation_batteredgranite(reg, seed=0):
    """A battered granite plinth: courses of long blocks whose faces slope back as they rise,
    under a torus-and-fillet cap (the Fontaine)."""
    b = reg.bounds()
    out = [M.extrude(reg, 0.2)]
    hh = b[3] - b[1]
    v = b[1] + 0.2
    j = 0
    while v < b[3] - 1.6:
        ch = min(2.8, b[3] - 1.4 - v)
        u = b[0] - (j % 2) * 4.0
        dep = 0.85 - 0.5 * (v - b[1]) / max(hh, 1.0)
        while u < b[2]:
            blk = rect(u + 0.2, v + 0.2, u + 8.0 - 0.2, v + ch - 0.2) ^ reg
            if not blk.is_empty():
                bb = blk.bounds()
                if bb[2] - bb[0] > 0.8 and bb[3] - bb[1] > 0.8:
                    out.append(M.hull_points([(bb[0], bb[1], 0.19), (bb[2], bb[1], 0.19), (bb[0], bb[3], 0.19), (bb[2], bb[3], 0.19),
                                              (bb[0], bb[1], dep), (bb[2], bb[1], dep), (bb[0], bb[3], dep - 0.2), (bb[2], bb[3], dep - 0.2)]))
            u += 8.0
        v += ch
        j += 1
    cap = rect(b[0] - 1, b[3] - 1.4, b[2] + 1, b[3] + 1) ^ reg
    if not cap.is_empty():
        cb = cap.bounds()
        out.append(ext(cap, 0.19, 0.6))
        out.append(ext(rect(cb[0], cb[1] + 0.3, cb[2], cb[1] + 1.0) ^ reg, 0.59, 0.85))
    return union(out)


def chimney_fontaine(w=11.0, d=9.0, h=25.0):
    """The Fontaine's stacks: granite, a sunk panel on every face, a corbelled cap with a
    blocking course and a ball on each corner of it."""
    h = round(h / 0.2) * 0.2
    sh = h - 4.6
    body = box([-w / 2 - 0.5, -d / 2 - 0.5, 0.0], [w / 2 + 0.5, d / 2 + 0.5, 2.0])
    body = body + M.hull_points([(x, y, 1.99) for x in (-w / 2 - 0.5, w / 2 + 0.5) for y in (-d / 2 - 0.5, d / 2 + 0.5)] +
                                [(x, y, 2.5) for x in (-w / 2, w / 2) for y in (-d / 2, d / 2)])
    body = body + box([-w / 2, -d / 2, 0.0], [w / 2, d / 2, sh])
    for (L, D, rot) in ((w, d, 0), (d, w, 90), (w, d, 180), (d, w, 270)):
        pan = box([-L / 2 + 1.6, D / 2 - 0.45, 4.0], [L / 2 - 1.6, D / 2 + 0.1, sh - 2.0])
        body = body - pan.rotate([0, 0, rot])
    body = body + M.hull_points([(x, y, sh - 0.01) for x in (-w / 2, w / 2) for y in (-d / 2, d / 2)] +
                                [(x, y, sh + 0.8) for x in (-w / 2 - 0.8, w / 2 + 0.8) for y in (-d / 2 - 0.8, d / 2 + 0.8)])
    body = body + box([-w / 2 - 0.8, -d / 2 - 0.8, sh + 0.79], [w / 2 + 0.8, d / 2 + 0.8, sh + 1.6])
    body = body + box([-w / 2 - 0.2, -d / 2 - 0.2, sh + 1.59], [w / 2 + 0.2, d / 2 + 0.2, sh + 2.8])
    for sx in (-1, 1):
        for sy in (-1, 1):
            body = body + M.sphere(0.85, 16).translate([sx * (w / 2 - 0.4), sy * (d / 2 - 0.4), sh + 2.79 + 0.6])
            body = body + M.cylinder(0.5, 0.6, 0.6, 12).translate([sx * (w / 2 - 0.4), sy * (d / 2 - 0.4), sh + 2.75])
    flue = box([-w / 2 + 2.2, -d / 2 + 2.2, sh - 4.0], [w / 2 - 2.2, d / 2 - 2.2, sh + 2.81])
    return body - flue


def fence_fontaine(L, h):
    """Fontaine cresting: tridents (bars ending in three prongs) and between every two a ring on
    the rail holding a little cross."""
    pitch = 3.0
    n = max(1, int(round(L / pitch)))
    p = L / n
    rail = h * 0.3
    cells = [rect(0.0, 0.0, L, 0.6), rect(0.0, rail, L, rail + 0.45)]
    for j in range(n + 1):
        u = p * j
        cells.append(rect(u - 0.28, 0.0, u + 0.28, h - 0.3))
        cells.append(rect(u - 0.85, h - 1.46, u + 0.85, h - 1.0))
        for x in (u - 0.62, u + 0.62):
            cells.append(rect(x - 0.23, h - 1.1, x + 0.23, h - 0.5))
            cells.append(poly([(x - 0.3, h - 0.6), (x + 0.3, h - 0.6), (x, h - 0.15)]))
        cells.append(poly([(u - 0.38, h - 0.4), (u + 0.38, h - 0.4), (u, h + 0.2)]))
        if j < n:
            m = u + p / 2
            vc = (rail + 0.45 + h - 1.4) / 2
            rr = min((h - 1.4 - rail - 0.45) / 2 + 0.05, p / 2 - 0.4)
            cells.append(circle((m, vc), rr, 18) - circle((m, vc), max(rr - 0.46, 0.2), 14))
            cells += [rect(m - 0.23, vc - rr + 0.2, m + 0.23, vc + rr - 0.2), rect(m - rr + 0.2, vc - 0.23, m + rr - 0.2, vc + 0.23)]
    return cs_union(cells) ^ rect(0.0, 0.0, L, h + 1.0)


def finial_bannerette(h=13.0):
    """A finial of a bannerette vane: a turned base, an orb, a crown of four leaves, and a rod
    flying a swallow-tailed pennant (a flat plate 0.8 thick, printed upright with the rest)."""
    prof = [(0.0, 0.0), (1.5, 0.0), (1.5, 0.7), (1.0, 1.2), (0.6, 1.8), (0.6, h * 0.25), (0.95, h * 0.28), (0.55, h * 0.31),
            (0.0, h * 0.31)]
    body = PW._revolve(prof, 28)
    zo = h * 0.31 + 1.2
    body = body + M.sphere(1.25, 28).translate([0, 0, zo])
    zc = zo + 1.1
    for a in np.linspace(0, 2 * math.pi, 4, endpoint=False):
        body = body + M.hull_points([(0.5 * math.cos(a) + dx, 0.5 * math.sin(a) + dy, zc) for dx in (-0.2, 0.2) for dy in (-0.2, 0.2)] +
                                    [(0.8 * math.cos(a), 0.8 * math.sin(a), zc + 1.1)])
    body = body + M.cylinder(h - zc + 0.01, 0.32, 0.3, 12).translate([0, 0, zc - 0.01])
    zp = h - 3.6
    pennant = poly([(0.2, zp), (4.2, zp + 0.6), (3.2, zp + 1.3), (4.2, zp + 2.0), (0.2, zp + 2.6)])
    flag = M.extrude(pennant, 0.8).translate([0, 0, -0.4]).transform(np.array([[1.0, 0, 0, 0], [0, 0, 1.0, 0], [0, 1.0, 0, 0]]))
    return body + flag


# ------------------------------------------------------------------ windows and doors
def window_fontaine_lower(w=9.4, h=22.0, A=1.0):
    """Fontaine ground floor: a round-headed two-over-two sash in an architrave with a shield
    keystone, between engaged round columns on blocks carrying a short entablature; a sill."""
    r = w / 2
    spring = h - r
    op = O.opening_cs(w, h, r)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    sash = O.window_insert(w, h, r, lites=(2, 2), bare=True)["insert"]
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS),
             MD.band(op.offset(A, JoinType.Round), A, MD.ARCHITRAVE, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op)]
    rc = 0.85
    xc = r + A + 0.2 + rc
    vcap = h + A + 0.4
    half = xc + rc + 0.4
    for sg in (-1, 1):
        x = sg * xc
        parts.append(ext(rect(x - rc - 0.2, 0.0, x + rc + 0.2, vcap), 0.0, 0.5))
        parts.append(chamfer_box(x - rc - 0.3, -0.4, x + rc + 0.3, 2.4, 0.0, 1.4, c=0.25))
        prof = [(0.0, 0.0), (rc + 0.15, 0.0), (rc, 0.4), (rc * 0.9, vcap - 2.4 - 1.2), (rc + 0.15, vcap - 2.4 - 0.9),
                (rc * 0.9, vcap - 2.4 - 0.7), (rc + 0.35, vcap - 2.4), (0.0, vcap - 2.4)]
        col = PW._revolve(prof, 24).rotate([-90, 0, 0]).translate([x, 2.39, 0.0]) ^ box([x - 3, 0.0, 0.0], [x + 3, vcap + 1, 5.0])
        parts.append(col)
    parts.append(ext(rect(-xc, spring, xc, vcap) - op.offset(A, JoinType.Round), 0.0, 0.5))
    shield = cs_union([rect(-0.9, h - 0.2, 0.9, h + 1.0), circle((0.0, h - 0.2), 0.9, 16)]) ^ rect(-1, h - 1.1, 1, h + 1.0)
    parts.append(ext(shield, 0.0, 1.3))
    parts.append(ext(rect(-half, vcap - 0.01, half, vcap + 1.6), 0.0, 0.8))
    parts.append(MD.run(-half - 0.6, half + 0.6, vcap + 1.6 + 1.0, MD.CROWN, 1.2, up=False))
    sw = r + A + 0.4
    parts.append(MD.run(-sw, sw, 0.0, MD.SILL, 1.0, up=False))
    return O._one_piece([sash], parts, op, plug_cs, O.PLUG, vcap + 2.6, -0.4)


def window_fontaine_upper(w=9.0, h=20.0, A=0.9):
    """Fontaine upper floor: a flat-headed two-over-two sash in an eared architrave, a plain
    frieze, a cornice, and over it a broken triangular pediment with an urn in the break; a sill
    on two blocks."""
    op = rect(-w / 2, 0.0, w / 2, h)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    sash = O.window_insert(w, h, 0, lites=(2, 2), bare=True)["insert"]
    half = w / 2 + A + 0.6
    outer = cs_union([op.offset(A, JoinType.Miter, 4.0), rect(-half, h - 1.8, half, h + A), rect(-half, 0.0, half, 1.6)])
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS),
             MD.band(outer, A + 0.6, MD.ARCHITRAVE, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op)]
    vf = h + A
    parts.append(ext(rect(-half, vf - 0.01, half, vf + 1.6), 0.0, 0.5))
    vc = vf + 1.6 + 1.0
    parts.append(MD.run(-half - 0.6, half + 0.6, vc, MD.CROWN, 1.2, up=False))
    hp = 2.6
    tri = poly([(-half - 0.6, vc - 0.01), (half + 0.6, vc - 0.01), (0.0, vc + hp)])
    rim = (tri - tri.offset(-0.8, JoinType.Miter, 4.0)) - rect(-1.4, vc - 1, 1.4, vc + 10)
    parts.append(ext(rim, 0.0, 1.1))
    parts.append(ext(tri.offset(-0.8, JoinType.Miter, 4.0) ^ rect(-50, vc, 50, 50), 0.0, 0.5))
    parts.append(ext(urn_cs(0.0, vc - 0.01, 3.4, 1.8), 0.0, 1.0))
    sw = half + 0.2
    parts.append(MD.run(-sw, sw, 0.0, MD.SILL, 1.0, up=False))
    for sg in (-1, 1):
        parts.append(chamfer_box(sg * (w / 2) - 0.7, -2.0, sg * (w / 2) + 0.7, -0.8, 0.0, 0.9, c=0.25))
    return O._one_piece([sash], parts, op, plug_cs, O.PLUG, vc + 3.4, -2.0)


def window_fontaine_tower(w=8.4, h=20.0, A=0.9):
    """The Fontaine tower's top storey: a round-headed one-over-one sash under an archivolt
    with a keystone, on a sill with a balustered apron."""
    r = w / 2
    spring = h - r
    op = O.opening_cs(w, h, r)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    sash = O.window_insert(w, h, r, lites=(1, 1), bare=True)["insert"]
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS),
             MD.band(op.offset(A, JoinType.Round), A, MD.CASING, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op)]
    parts.append(MD.band(op.offset(A + 0.9, JoinType.Round), 1.0, MD.CROWN, clip=rect(-w - 10, spring - 0.6, w + 10, h + 40)))
    for sg in (-1, 1):
        parts.append(chamfer_box(sg * (r + A + 0.45) - 0.8, spring - 1.4, sg * (r + A + 0.45) + 0.8, spring - 0.5, 0.0, 1.2, c=0.2))
    parts.append(keystone(0.0, h - 0.3, A + 1.6, 1.2, 1.8, 0.0, 1.4))
    sw = r + A + 0.6
    parts.append(MD.run(-sw, sw, 0.0, MD.SILL, 1.0, up=False))
    out = [rect(-sw + 0.4, -3.0, sw - 0.4, -2.5), rect(-sw + 0.4, -1.5, sw - 0.4, -0.99)]
    for x in np.linspace(-sw + 1.2, sw - 1.2, 5):
        out.append(cs_union([rect(x - 0.25, -2.6, x + 0.25, -1.4), oval((x, -2.0), 0.42, 0.42, 12)]))
    parts.append(ext(cs_union(out), 0.0, 0.7))
    return O._one_piece([sash], parts, op, plug_cs, O.PLUG, h + A + 1.6 + 0.2, -3.0)


def door_fontaine(w=13.4, h=28.0, A=1.2):
    """The Fontaine's entrance: a pair of leaves, each a tall light over two raised panels,
    under a round fanlight of three circles; an architrave with a scrolled keystone between
    paired engaged columns on pedestals carrying an entablature with a balustered blocking
    course."""
    r = w / 2
    spring = h - r
    op = O.opening_cs(w, h, r)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    mid = 0.5
    lw = (w - 2 * O.CLR - 1.0 - mid) / 2
    dh = spring - 0.4
    body, lights = [ext(plug_cs, -pl, -1.0)], []
    u = -w / 2 + O.CLR + 0.5
    for i in range(2):
        body.append(ext(rect(u, 0.5, u + lw, dh), -pl, -0.8))
        gv0 = dh * 0.46
        lights.append(rect(u + 0.8, gv0, u + lw - 0.8, dh - 0.8))
        gp = (gv0 - 0.8 - 1.2) / 2
        body.append(_panel(rect(u + 0.8, 1.2, u + lw - 0.8, 1.2 + gp - 0.2)))
        body.append(_panel(rect(u + 0.8, 1.2 + gp + 0.2, u + lw - 0.8, gv0 - 0.8)))
        u += lw + mid
    fan = plug_cs.offset(-0.5, JoinType.Miter, 4.0) ^ rect(-w, spring + 0.2, w, h + 2)
    rr = r * 0.32
    tracery = cs_union([circle((x, y), rr, 20) - circle((x, y), rr - 0.42, 20)
                        for x, y in ((-r * 0.42, spring + 0.2 + rr + 0.2), (r * 0.42, spring + 0.2 + rr + 0.2), (0.0, spring + 0.2 + r * 0.62))])
    tracery = tracery + rect(-w, spring + 0.2, w, spring + 0.65)
    sash = _glazed(body, cs_union(lights) + fan, pl, tracery, plug_cs)
    sash.append(ext(rect(-w, dh - 0.01, w, spring + 0.2) ^ plug_cs, -pl, -0.5))
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS),
             MD.band(op.offset(A, JoinType.Round), A, MD.ARCHITRAVE, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op)]
    rc = 0.95
    vcap = h + A + 1.0
    xs = [r + A + 0.3 + rc, r + A + 0.3 + 3 * rc + 0.6]
    half = xs[-1] + rc + 0.5
    for sg in (-1, 1):
        parts.append(ext(rect(sg * (r + A), 0.0, sg * half, vcap) if sg > 0 else rect(-half, 0.0, -(r + A), vcap), 0.0, 0.5))
        parts.append(chamfer_box(min(sg * (xs[0] - rc - 0.4), sg * (xs[1] + rc + 0.4)), 0.0,
                                 max(sg * (xs[0] - rc - 0.4), sg * (xs[1] + rc + 0.4)), 4.0, 0.0, 1.9, c=0.3))
        for xc in xs:
            x = sg * xc
            prof = [(0.0, 0.0), (rc + 0.2, 0.0), (rc, 0.4), (rc * 0.9, vcap - 4.0 - 1.4), (rc + 0.15, vcap - 4.0 - 1.1),
                    (rc * 0.9, vcap - 4.0 - 0.9), (rc + 0.45, vcap - 4.0), (0.0, vcap - 4.0)]
            col = PW._revolve(prof, 24).rotate([-90, 0, 0]).translate([x, 3.99, 0.0]) ^ box([x - 3, 0.0, 0.0], [x + 3, vcap + 1, 5.0])
            parts.append(col)
    parts.append(ext(rect(-(r + A), spring, r + A, vcap) - op.offset(A, JoinType.Round), 0.0, 0.6))
    parts.append(MD.scroll_keystone(0.0, h - 0.4, vcap - h + 0.4, 1.8, 2.6, 0.0, 1.9))
    parts.append(ext(rect(-half, vcap - 0.01, half, vcap + 0.9), 0.0, 1.1))
    parts.append(ext(rect(-half + 0.3, vcap + 0.89, half - 0.3, vcap + 2.8), 0.0, 0.7))
    vk = vcap + 2.8 + 1.4
    parts.append(MD.run(-half - 0.8, half + 0.8, vk, MD.CROWN, 1.4, up=False))
    bl = [rect(-half + 0.2, vk - 0.01, half - 0.2, vk + 0.5), rect(-half + 0.2, vk + 2.0, half - 0.2, vk + 2.6)]
    for x in np.linspace(-half + 1.4, half - 1.4, 9):
        bl.append(cs_union([rect(x - 0.25, vk + 0.4, x + 0.25, vk + 2.1), oval((x, vk + 1.0), 0.45, 0.5, 12)]))
    for sg in (-1, 1):
        bl.append(rect(sg * (half - 0.2) - 0.6 if sg > 0 else -half + 0.2, vk - 0.01, sg * (half - 0.2) if sg > 0 else -half + 0.8, vk + 2.6))
    parts.append(ext(cs_union(bl), 0.0, 0.8))
    return O._one_piece(sash, parts, op, plug_cs, pl, vk + 2.6, 0.0)


def door_fontaine_back(w=10.4, h=25.0, A=1.0):
    """The Fontaine's back door: one leaf with a tall light over two panels, a round fanlight
    with a circle, an architrave with a keystone and a cornice cap."""
    r = w / 2
    spring = h - r
    op = O.opening_cs(w, h, r)
    plug_cs = op.offset(-O.CLR, JoinType.Miter, 4.0)
    pl = O.PLUG
    dh = spring - 0.4
    u0, u1 = -w / 2 + O.CLR + 0.5, w / 2 - O.CLR - 0.5
    gv0 = dh * 0.46
    gp = (gv0 - 0.8 - 1.2) / 2
    body = [ext(plug_cs, -pl, -1.0), ext(rect(u0, 0.5, u1, dh), -pl, -0.8),
            _panel(rect(u0 + 0.8, 1.2, u1 - 0.8, 1.2 + gp - 0.2)), _panel(rect(u0 + 0.8, 1.2 + gp + 0.2, u1 - 0.8, gv0 - 0.8))]
    light = rect(u0 + 0.9, gv0, u1 - 0.9, dh - 0.8)
    fan = plug_cs.offset(-0.5, JoinType.Miter, 4.0) ^ rect(-w, spring + 0.2, w, h + 2)
    tr = cs_union([circle((0.0, spring + 0.2 + r * 0.45), r * 0.3, 20) - circle((0.0, spring + 0.2 + r * 0.45), r * 0.3 - 0.42, 20),
                   rect(-w, spring + 0.2, w, spring + 0.65)])
    sash = _glazed(body, light + fan, pl, tr, plug_cs)
    sash.append(ext(rect(-w, dh - 0.01, w, spring + 0.2) ^ plug_cs, -pl, -0.5))
    parts = [ext(op - op.offset(-RIB, JoinType.Miter, 4.0), 0.0, O.CAS),
             MD.band(op.offset(A, JoinType.Round), A, MD.ARCHITRAVE, clip=rect(-w - 10, 0.0, w + 10, h + 40) - op)]
    parts.append(keystone(0.0, h - 0.3, A + 0.8, 1.3, 1.9, 0.0, 1.5))
    half = r + A + 0.5
    vf = h + A + 0.4
    parts.append(ext(rect(-half, spring, half, vf + 1.0) - op.offset(A, JoinType.Round), 0.0, 0.5))
    parts.append(MD.run(-half - 0.6, half + 0.6, vf + 2.0, MD.CROWN, 1.2, up=False))
    return O._one_piece(sash, parts, op, plug_cs, pl, vf + 2.0, 0.0)


# ------------------------------------------------------------------ porch
def post_bellcapital(h, collar=None, abacus=3.4, slot=(1.2, 1.0)):
    """A column with a bell capital: a plain round shaft with entasis on an Attic base (two tori
    and a scotia), a necking ring, and a capital flaring like a bell to a square abacus (the
    Fontaine's veranda)."""
    z1 = h - 3.2
    r = 1.0
    prof = [(0.0, 1.19), (1.5, 1.19), (1.5, 1.4), (1.3, 1.6), (1.18, 1.8), (1.3, 2.0), (1.12, 2.3), (r, 2.6),
            (r * 1.04, (2.6 + z1) * 0.4), (r * 0.9, z1 - 0.4), (1.1, z1 - 0.2), (1.1, z1 + 0.05), (r * 0.9, z1 + 0.25),
            (1.15, z1 + 0.9), (1.55, z1 + 1.5)]
    body = PW._revolve(prof, 32) + PW._plinth(3.0)
    return body + PW._top(h, abacus / 2, z1 + 1.5, 1.55, slot, seg=32)


def post_bellnewel(h, collar=None):
    """The terrace's newel: the veranda column cut short, its Attic base and shaft, a necking
    ring level with the hand rail, a bell flaring to a round cap, and a ball (the Fontaine).
    ``collar``: the hand rail's top; the post is ``h`` tall and stops there."""
    zn = (collar if collar else h - 3.3) - 0.2
    zc = zn + 2.85
    prof = [(0.0, 1.19), (1.5, 1.19), (1.5, 1.4), (1.3, 1.6), (1.18, 1.8), (1.3, 2.0), (1.12, 2.3), (1.0, 2.6),
            (1.05, (2.6 + zn) * 0.45), (0.95, zn - 0.3), (1.12, zn - 0.1), (1.12, zn + 0.2), (0.95, zn + 0.35),
            (1.3, zn + 0.8), (1.65, zn + 1.2), (1.65, zn + 1.6), (1.2, zn + 1.8), (0.55, zn + 2.0),
            (0.6, zc - 0.6), (0.85, zc), (0.6, zc + 0.6), (0.0, min(h, zc + 0.85))]
    return PW._revolve(prof, 32) + PW._plinth(3.0)


def baluster_tulipbell(h, seg=18):
    """A baluster swelling to a tulip bell above the middle, on a slender stem, a ring at its
    foot (the Fontaine)."""
    prof = [(0.0, 0.8), (0.3, 0.8), (0.42, h * 0.16), (0.27, h * 0.24), (0.27, h * 0.42), (0.5, h * 0.62), (0.52, h * 0.7),
            (0.3, h * 0.82), (0.3, h - 0.8)]
    return PW._revolve(prof, seg) + box([-0.55, -0.55, 0.0], [0.55, 0.55, 0.81]) + box([-0.55, -0.55, h - 0.81], [0.55, 0.55, h])


def frieze_lunettearcade(u0, u1, v_bot, v_top):
    """A porch frieze: an entablature board cut below into a row of lunettes (half-round
    openings), a keyblock over each (the Fontaine)."""
    v0 = v_top - 3.2
    n = max(1, int((u1 - u0) / 4.0))
    p = (u1 - u0) / n
    board = rect(u0, v0 - 1.0, u1, v_top + 0.05)
    cuts, keys = [], []
    for k in range(n):
        m = u0 + p * (k + 0.5)
        rr = p * 0.36
        cuts.append(cs_union([circle((m, v0 - 1.0), rr, 20), rect(m - rr, v0 - 3.0, m + rr, v0 - 1.0)]))
        keys.append(poly([(m - 0.4, v0 - 1.0 + rr - 0.1), (m + 0.4, v0 - 1.0 + rr - 0.1), (m + 0.6, v0 + 0.9), (m - 0.6, v0 + 0.9)]))
    return (board - cs_union(cuts)) + cs_union(keys)


def skirt_rusticblocks(reg, d=1.2):
    """A porch skirt built like a plinth of rusticated blocks, every edge chamfered, in broken
    courses under a cap (the Fontaine)."""
    u0, v0, u1, v1 = reg.bounds()
    out = [M.extrude(reg, d * 0.45)]
    v = v0
    k = 0
    while v < v1 - 1.2:
        ch = min(2.2, v1 - 0.9 - v)
        u = u0 - (k % 2) * 2.6
        while u < u1:
            out.append(chamfer_box(u + 0.15, v + 0.15, u + 5.2 - 0.15, v + ch - 0.15, d * 0.45 - 0.01, d * 0.55, c=0.3))
            u += 5.2
        v += ch
        k += 1
    out.append(ext(rect(u0 - 1, v1 - 0.9, u1 + 1, v1 + 1), d * 0.45 - 0.01, d * 0.55))
    return union(out) ^ M.extrude(reg, d + 0.5)


def edge_belldrops(L, z0, zc):
    """Porch fascia (the Fontaine): little bells on short cords hung under the crown, a bead
    between every two."""
    out = [rect(0.3, zc - 0.45, L - 0.3, zc)]
    for i, x in enumerate(np.arange(1.2, L - 1.0, 1.4)):
        if i % 2 == 0:
            out.append(rect(x - 0.2, zc - 0.8, x + 0.2, zc - 0.4))
            out.append(poly([(x - 0.25, zc - 0.75), (x + 0.25, zc - 0.75), (x + 0.5, zc - 1.6), (x - 0.5, zc - 1.6)]))
        else:
            out.append(circle((x, zc - 0.75), 0.36, 10))
    return cs_union(out), 0.6


CO.FRIEZE_EXTRA.update(lozengerosettes=frieze_lozengerosettes, coronets=frieze_coronets)
CO.COURSE_EXTRA.update(loopknot=course_loopknot, bellchain=course_bellchain)
TW.BRACKET_EXTRA.update(ramshorn=bracket_ramshorn)
TW.PIERCED = TW.PIERCED + ("ramshorn",)
TW.FOUNDATION_EXTRA.update(batteredgranite=foundation_batteredgranite)
SH.CORNER_EXTRA.update(vermiquoin=corner_vermiquoin)
PW.POSTS.update(bellcapital=post_bellcapital, bellnewel=post_bellnewel)
PW.BALUSTERS.update(tulipbell=(baluster_tulipbell, 1.6))
PW.FRIEZES.update(lunettearcade=frieze_lunettearcade)
PW.SKIRTS.update(rusticblocks=skirt_rusticblocks)
FT.EDGE_EXTRA.update(belldrops=edge_belldrops)

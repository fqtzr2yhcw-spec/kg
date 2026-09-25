"""Built-up cornices: several printed rings, each its own part and colour, stacked round the
wall at every level (each storey joint and the eave), the way the reference kits build their
trim out of separate layers.

Construction (the house standard for cornices):
  * the wall carries a plain *band* the height of the cornice (no siding, no openings)
    standing on a moulded *ledge* that grows out of the wall at 45 degrees (``ledge``); at a
    storey joint the belt ring is that band (``joint_profile``), at the eave the top storey
    shell rises through it;
  * the rings wrap the band (inner face CLR off the wall plane) and stack on the ledge, low
    to high: a *frieze* and a *course* (both print upright, relief on their outer faces), a
    *bed* (a soffit with brackets or modillions that hang down in front of the rings under
    it) and a *crown* moulding (both print upside down, so everything widens toward the bed);
  * the band's top is flush with the top ring; the next storey or the roof sits on the band,
    its locating lip inside the wall as before;
  * a ring that meets a block rising through its level (a tower) is cut back to it, and its
    pieces become separate parts.

Each ring is a dict(role, solid, flip): ``role`` names the colour slot the building assigns,
``flip`` says it prints upside down. Decoration spacing on every ring of a level follows one
``pitch``/``margin``, so friezes centre their ornaments between the brackets above them.

Ornaments on upright faces use shell._stepped (each 0.2 layer pulled up 0.2 underneath)."""
import math

import numpy as np
from manifold3d import JoinType, Manifold as M

from .core import Facade, box, ccw, circle, cs_union, poly, rect, sweep_ring, union
from .ornament import chamfer_box, ext, oval, stroke

CLR = 0.15      # a ring's inner face stands this far off the wall plane
# more frieze and course kinds, registered by other modules (hoarch.colonial):
# FRIEZE_EXTRA[kind](L, h, b, pitch, margin, pair, half) -> (ornament solids, cut solids) in the
# edge's (u, v, w) frame; COURSE_EXTRA[kind](L, h, b, pitch, margin, p) -> list of solids
FRIEZE_EXTRA = {}
COURSE_EXTRA = {}


def _stepped(cs, w0, d):
    from .shell import _stepped as st
    return st(cs, w0, d)


def _us(L, pitch, margin, pair=0.0):
    """Bracket (or ornament) stations along an edge of length L (as roof.edge_brackets)."""
    if L < 2 * margin + 1.0:
        return []
    k = max(1, int(round((L - 2 * margin) / pitch)))
    us = [margin + (L - 2 * margin) * j / k for j in range(k + 1)]
    return [u + du for u in us for du in ((-pair / 2, pair / 2) if pair > 0 else (0.0,))]


def _between(L, pitch, margin, pair=0.0, half=0.0):
    """Centres (and free widths) of the bays between bracket stations."""
    cs = _us(L, pitch, margin, 0.0)
    out = []
    for a, b in zip(cs[:-1], cs[1:]):
        u0, u1 = a + pair / 2 + half, b - pair / 2 - half
        if u1 - u0 > 0.8:
            out.append(((u0 + u1) / 2, u1 - u0))
    return out


def _edges(path):
    P = ccw(path)
    return [Facade(P[i], P[(i + 1) % len(P)], 0.0) for i in range(len(P))]


def _place(f, z0, m):
    A = f.A.copy()
    A[:, 3] = f.world(0.0, 0.0, 0.0) + np.array([0.0, 0.0, z0])
    return m.transform(A)


def body_ring(path, z0, h, b, extra=()):
    """The plain annulus of a ring: from CLR to ``b`` off the wall plane, z0..z0+h.
    ``extra``: more (d, z) points (relative to z0) spliced into the outer side, low to high."""
    prof = [(CLR, 0.0), (b, 0.0)] + list(extra) + [(b, h), (CLR, h)]
    return sweep_ring(path, [(d, z0 + z) for d, z in prof])


# ------------------------------------------------------------------ the wall's ledge
def ledge(path, z_top, e, t=3.0):
    """A moulding growing out of the wall at 45 degrees to ``e`` at z_top: the shelf the
    lowest ring stands on (union it into the storey shell)."""
    prof = [(-t + 0.2, z_top - e - 0.4), (0.0, z_top - e - 0.4), (0.0, z_top - e), (e, z_top), (-t + 0.2, z_top)]
    return sweep_ring(path, prof)


def joint_profile(h, e):
    """Belt-ring profile for shell.stacked_shells when a cornice wraps the joint: a 45 degree
    ledge ``e`` deep at the foot, then the plain band flush with the wall up to ``h``."""
    return [(0.0, 0.0), (e, e), (e, e + 0.4), (0.0, e + 0.4), (0.0, h)]


# ------------------------------------------------------------------ friezes (upright)
FRIEZES = ("panels", "rosettes", "lozenges", "triglyphs", "fret", "arcade", "swags", "zigzag", "flutes", "sunflower",
           "guilloche", "wave", "ovals", "spindles", "circles", "plain", "diaper", "chevron", "studs", "quatrefoil",
           "fans", "lattice", "stars", "hearts", "scrolls", "keys", "medallions", "tulips", "bosses",
           "anthemion", "rinceau", "paterae", "coffers", "wreaths", "lunettes", "lancets", "trefoils", "corbel_arches",
           "interlace", "nailhead", "stickwork", "xbrace", "diamonds", "teeth", "strapwork", "roses", "crenels",
           "incised", "cartouches", "acanthus", "shells", "pendants", "oculi", "pearls")


def _frieze_edge(kind, L, h, b, pitch, margin, pair, half, dd):
    """Ornament for one edge of a frieze, in the edge's (u, v, w) frame (v from the ring's foot)."""
    out, cuts = [], []
    v0, v1 = 0.8, h - 0.8                    # the field between the foot and head fillets
    vm = (v0 + v1) / 2
    hh = v1 - v0
    bays = _between(L, pitch, margin, pair, half)
    if kind in FRIEZES[FRIEZES.index("anthemion"):] and L < 2 * margin + 1.0:
        return M(), M()                      # too short an edge for the first ten houses' friezes
    if kind == "panels":
        for uc, wd in bays:
            out.append(_stepped(rect(uc - wd / 2 + 0.3, v0 + 0.3, uc + wd / 2 - 0.3, v1 - 0.3), b, 0.4))
            out.append(_stepped(poly([(uc - 0.9, vm), (uc, vm + min(1.2, hh / 2 - 0.4)), (uc + 0.9, vm),
                                      (uc, vm - min(1.2, hh / 2 - 0.4))]), b + 0.4, 0.4))
    elif kind == "rosettes":
        for uc, wd in bays:
            r = min(hh / 2 - 0.1, wd / 2 - 0.4, 1.6)
            out.append(_stepped(circle((uc, vm), r, 28), b, 0.4))
            petals = cs_union([circle((uc + r * 0.55 * math.cos(a), vm + r * 0.55 * math.sin(a)), r * 0.34, 16)
                               for a in np.linspace(0, 2 * math.pi, 6, endpoint=False)])
            out.append(_stepped(petals, b + 0.4, 0.4))
            out.append(_stepped(circle((uc, vm), r * 0.3, 16), b + 0.8, 0.2))
    elif kind == "lozenges":
        for uc, wd in bays:
            a_ = min(wd / 2 - 0.3, 2.6)
            dia = poly([(uc - a_, vm), (uc, v1), (uc + a_, vm), (uc, v0)])
            out.append(_stepped(dia, b, 0.4))
            out.append(_stepped(dia.offset(-0.7, JoinType.Miter, 4.0), b + 0.4, 0.4))
    elif kind == "triglyphs":
        for u in _us(L, pitch, margin, 0.0):
            tg = rect(u - 1.1, v0 - 0.2, u + 1.1, v1 + 0.2)
            out.append(_stepped(tg, b, 0.6))
            for du in (-0.45, 0.45):
                cuts.append(ext(rect(u + du - 0.25, v0 + 0.4, u + du + 0.25, v1 + 0.3), b + 0.2, b + 1.0))
            for g in (-0.8, 0.0, 0.8):     # guttae: little drops under each triglyph
                out.append(_stepped(circle((u + g, v0 - 0.35), 0.28, 10), b, 0.4))
    elif kind == "fret":
        # a running Greek key along the band
        step = 2.0
        pts, u = [], margin * 0.5
        while u + 4 * step <= L - margin * 0.5:
            pts += [(u, v0), (u, v1), (u + 2 * step, v1), (u + 2 * step, vm), (u + step, vm), (u + step, v0 + 0.0),
                    (u + 3 * step, v0), (u + 3 * step, v1)]
            u += 3 * step
        if len(pts) > 2:
            out.append(_stepped(stroke(pts, 0.55, caps=False) ^ rect(0.0, v0 - 0.3, L, v1 + 0.3), b, 0.4))
    elif kind == "arcade":
        n = max(2, int(round((L - 2 * margin) / 2.6)))
        pu = (L - 2 * margin) / n
        for k in range(n):
            uc = margin + pu * (k + 0.5)
            r = pu / 2 - 0.35
            arc = [(uc + r * math.cos(a), v1 - r - 0.2 + r * math.sin(a)) for a in np.linspace(0, math.pi, 12)]
            out.append(_stepped(stroke([(uc + r, v0)] + arc + [(uc - r, v0)], 0.5, caps=False), b, 0.4))
            out.append(_stepped(circle((uc - pu / 2, v0 + 0.35), 0.35, 10), b, 0.4) if k else M())
    elif kind == "swags":
        for uc, wd in bays:
            s0, s1 = uc - wd / 2 + 0.6, uc + wd / 2 - 0.6
            sag = min(hh - 0.6, 2.2)
            top = [(s0 + (s1 - s0) * t, v1 - 0.2 - sag * 4 * t * (1 - t)) for t in np.linspace(0, 1, 13)]
            bot = [(s0 + (s1 - s0) * t, v1 - 0.2 - sag * 4 * t * (1 - t) - 0.3 - 0.5 * 4 * t * (1 - t))
                   for t in np.linspace(1, 0, 13)]
            out.append(_stepped(poly(top + bot), b, 0.4))
        for u in _us(L, pitch, margin, 0.0):
            out.append(_stepped(circle((u, v1 - 0.6), 0.55, 16), b, 0.6))
    elif kind == "zigzag":
        n = max(2, int(round((L - 2 * margin) / 2.4)))
        pu = (L - 2 * margin) / n
        pts = [(margin + pu * k, v1 - 0.3 if k % 2 else v0 + 0.3) for k in range(n + 1)]
        out.append(_stepped(stroke(pts, 0.55, caps=False), b, 0.4))
    elif kind == "flutes":
        n = max(2, int(round((L - 2 * margin) / 1.4)))
        pu = (L - 2 * margin) / n
        for k in range(n + 1):
            u = margin + pu * k
            cuts.append(ext(rect(u - 0.26, v0 + 0.2, u + 0.26, v1 - 0.2), b - 0.35, b + 0.1))
    elif kind == "sunflower":
        for uc, wd in bays:
            r = min(hh / 2 - 0.1, wd / 2 - 0.6, 1.5)
            cuts.append(ext(circle((uc, vm), r, 28) - circle((uc, vm), r - 0.55, 28), b - 0.35, b + 0.1))
            for a in np.linspace(0.3, math.pi - 0.3, 4):
                for sg in (-1, 1):
                    p0 = (uc + sg * (r + 0.4) * math.cos(a), vm + (r + 0.4) * math.sin(a) * (1 if a < 1.6 else 1))
                    p1 = (uc + sg * (r + 1.6) * math.cos(a), vm + (r + 1.6) * math.sin(a))
                    cuts.append(ext(stroke([p0, p1], 0.5) ^ rect(uc - wd / 2, v0, uc + wd / 2, v1), b - 0.35, b + 0.1))
            out.append(_stepped(circle((uc, vm), r - 0.8, 20), b, 0.4))
    elif kind == "guilloche":
        n = max(2, int(round((L - 2 * margin) / 3.0)))
        pu = (L - 2 * margin) / n
        amp = hh / 2 - 0.35
        for ph in (0.0, math.pi):
            pts = [(margin + t, vm + amp * math.sin(2 * math.pi * t / (2 * pu) * 2 + ph)) for t in np.linspace(0, L - 2 * margin, 8 * n + 1)]
            out.append(_stepped(stroke(pts, 0.5, caps=False), b, 0.4))
        for k in range(n):
            out.append(_stepped(circle((margin + pu * (k + 0.5), vm), 0.4, 12), b, 0.6))
    elif kind == "wave":
        # a running-dog (Vitruvian) scroll: a wave whose crests curl over
        n = max(2, int(round((L - 2 * margin) / 3.2)))
        pu = (L - 2 * margin) / n
        amp = hh / 2 - 0.35
        pts = [(margin + t, vm + amp * math.sin(2 * math.pi * t / pu)) for t in np.linspace(0, L - 2 * margin, 10 * n + 1)]
        out.append(_stepped(stroke(pts, 0.55, caps=False), b, 0.4))
        for k in range(n):
            out.append(_stepped(circle((margin + pu * (k + 0.25), vm + amp - 0.55), 0.45, 12), b, 0.4))
    elif kind == "ovals":
        for uc, wd in bays:
            rx, ry = min(wd / 2 - 0.5, 2.8), min(hh / 2 - 0.1, 1.5)
            ring_ = oval((uc, vm), rx, ry) - oval((uc, vm), rx - 0.55, ry - 0.55)
            out.append(_stepped(ring_, b, 0.4))
            out.append(_stepped(oval((uc, vm), max(0.4, rx - 1.2), max(0.3, ry - 1.1)), b, 0.4))
    elif kind == "spindles":
        n = max(2, int(round((L - 2 * margin) / 1.3)))
        pu = (L - 2 * margin) / n
        for k in range(n + 1):
            u = margin + pu * k
            out.append(_stepped(rect(u - 0.28, v0, u + 0.28, v1), b, 0.4))
            out.append(_stepped(circle((u, vm), 0.45, 12), b, 0.6))
    elif kind == "circles":
        n = max(2, int(round((L - 2 * margin) / (hh + 0.2))))
        pu = (L - 2 * margin) / n
        for k in range(n):
            uc = margin + pu * (k + 0.5)
            r = min(pu, hh) / 2 - 0.05
            out.append(_stepped(circle((uc, vm), r, 24) - circle((uc, vm), r - 0.5, 24), b, 0.4))
    elif kind == "diaper":
        s_ = hh / 2
        n = max(2, int(round((L - 2 * margin) / (2 * s_))))
        pu = (L - 2 * margin) / n
        for k in range(n):
            uc = margin + pu * (k + 0.5)
            d_ = poly([(uc - pu / 2 + 0.3, vm), (uc, v1 - 0.1), (uc + pu / 2 - 0.3, vm), (uc, v0 + 0.1)])
            out.append(_stepped(d_ - d_.offset(-0.55, JoinType.Miter, 4.0), b, 0.4))
            out.append(_stepped(circle((uc, vm), 0.4, 12), b, 0.4))
    elif kind == "chevron":
        n = max(2, int(round((L - 2 * margin) / 2.0)))
        pu = (L - 2 * margin) / n
        for k in range(n):
            u = margin + pu * k
            out.append(_stepped(poly([(u, v0), (u + pu / 2, vm), (u + pu, v0), (u + pu, v0 + 0.8), (u + pu / 2, vm + 0.8),
                                      (u, v0 + 0.8)]), b, 0.4))
            out.append(_stepped(poly([(u, vm + 0.4), (u + pu / 2, v1 - 0.1), (u + pu, vm + 0.4), (u + pu, vm + 1.2),
                                      (u + pu / 2, v1 + 0.3), (u, vm + 1.2)]) ^ rect(u, v0, u + pu, v1), b, 0.4))
    elif kind == "studs":
        for uc, wd in bays:
            n = max(1, int(wd / 1.6))
            for k in range(n):
                u = uc - wd / 2 + wd * (k + 0.5) / n
                out.append(_stepped(rect(u - 0.45, vm - 0.45, u + 0.45, vm + 0.45), b, 0.6))
    elif kind == "quatrefoil":
        for uc, wd in bays:
            r = min(hh / 2 - 0.05, wd / 2 - 0.4, 1.8) * 0.5
            q = cs_union([circle((uc + r * c_, vm + r * s_), r, 16) for c_, s_ in ((1, 0), (-1, 0), (0, 1), (0, -1))])
            out.append(_stepped(q - q.offset(-0.5, JoinType.Round), b, 0.4))
    elif kind == "fans":            # a half-round fan standing on the foot in every bay, rays and a hub
        for uc, wd in bays:
            r = min(hh - 0.2, wd / 2 - 0.4)
            half = circle((uc, v0), r, 32) ^ rect(uc - r - 1, v0, uc + r + 1, v1 + 1)
            rays = cs_union([stroke([(uc, v0), (uc + r * math.cos(a), v0 + r * math.sin(a))], 0.5, caps=False)
                             for a in np.linspace(0.35, math.pi - 0.35, 5)]) ^ half
            out.append(_stepped((half - half.offset(-0.55, JoinType.Round)) + rays, b, 0.4))
            out.append(_stepped(circle((uc, v0), min(1.0, r * 0.3), 16) ^ rect(uc - 2, v0, uc + 2, v1), b + 0.4, 0.2))
    elif kind == "lattice":         # a diagonal lattice between the stations, framed
        for uc, wd in bays:
            fr = rect(uc - wd / 2 + 0.3, v0, uc + wd / 2 - 0.3, v1)
            bars = []
            k = -int(wd / 1.6) - 3
            while k * 1.6 < wd + hh + 2:
                x = uc - wd / 2 + k * 1.6
                bars.append(stroke([(x, v0 - 1), (x + hh + 2, v1 + 1)], 0.5, caps=False))
                bars.append(stroke([(x, v1 + 1), (x + hh + 2, v0 - 1)], 0.5, caps=False))
                k += 1
            out.append(_stepped(((cs_union(bars) ^ fr) + (fr - fr.offset(-0.55, JoinType.Miter, 4.0))), b, 0.4))
    elif kind == "stars":           # a five-pointed star in every bay
        for uc, wd in bays:
            r = min(hh / 2, wd / 2 - 0.4)
            pts = [(uc + (r if k % 2 == 0 else r * 0.42) * math.cos(math.pi / 2 + k * math.pi / 5),
                    vm + (r if k % 2 == 0 else r * 0.42) * math.sin(math.pi / 2 + k * math.pi / 5)) for k in range(10)]
            out.append(_stepped(poly(pts), b, 0.5))
    elif kind == "hearts":          # a heart in every bay, and a bead between
        for uc, wd in bays:
            r = min(hh * 0.28, wd / 4 - 0.1)
            h_ = cs_union([circle((uc - r * 0.72, vm + r * 0.3), r, 20), circle((uc + r * 0.72, vm + r * 0.3), r, 20),
                           poly([(uc - r * 1.62, vm + r * 0.05), (uc + r * 1.62, vm + r * 0.05), (uc, vm - r * 1.9)])])
            out.append(_stepped(h_, b, 0.5))
        for u in _us(L, pitch, margin, 0.0):
            out.append(_stepped(circle((u, vm), 0.45, 12), b, 0.4))
    elif kind == "scrolls":         # a pair of C-scrolls back to back in every bay
        for uc, wd in bays:
            r = min(hh / 2 - 0.3, wd / 4 - 0.2)
            for sg in (-1, 1):
                c = (uc + sg * (r + 0.1), vm)
                arc = [(c[0] + sg * r * math.cos(a), c[1] + r * math.sin(a)) for a in np.linspace(-2.4, 2.4, 14)]
                out.append(_stepped(stroke(arc, 0.5, caps=False), b, 0.4))
                out.append(_stepped(circle((c[0] + sg * r * math.cos(2.4), c[1] + r * math.sin(2.4)), 0.5, 12), b, 0.4))
    elif kind == "keys":            # square blocks each with a sunk key slot, spaced along the band
        n = max(2, int(round((L - 2 * margin) / 3.2)))
        pu = (L - 2 * margin) / n
        for k in range(n):
            uc = margin + pu * (k + 0.5)
            s_ = min(pu, hh) / 2 - 0.3
            out.append(_stepped(rect(uc - s_, vm - s_, uc + s_, vm + s_), b, 0.5))
            cuts.append(ext(rect(uc - 0.3, vm - s_ + 0.5, uc + 0.3, vm + s_ - 0.5), b + 0.2, b + 1.0))
    elif kind == "medallions":      # an oval medallion with a boss, flanked by two beads, in every bay
        for uc, wd in bays:
            rx, ry = min(wd / 4, 2.2), min(hh / 2 - 0.1, 1.6)
            out.append(_stepped(oval((uc, vm), rx, ry) - oval((uc, vm), rx - 0.55, ry - 0.55), b, 0.4))
            out.append(_stepped(circle((uc, vm), min(0.8, ry - 0.6), 16), b, 0.6))
            for sg in (-1, 1):
                out.append(_stepped(circle((uc + sg * (rx + 1.0), vm), 0.45, 12), b, 0.4))
    elif kind == "tulips":          # a stylised tulip (a cup of three petals on a stem) in every bay
        for uc, wd in bays:
            r = min(hh * 0.3, wd / 4)
            cup = cs_union([circle((uc, vm + r * 0.4), r * 0.8, 16), poly([(uc - r, vm + r * 0.2), (uc, vm + r * 1.5),
                                                                              (uc + r, vm + r * 0.2)])])
            stem = rect(uc - 0.28, v0 + 0.2, uc + 0.28, vm)
            leaves = cs_union([poly([(uc, vm - r * 0.9), (uc + sg * r * 1.1, vm - r * 0.2), (uc + sg * 0.3, vm - r * 0.3)])
                               for sg in (-1, 1)])
            out.append(_stepped(cup + stem + leaves, b, 0.4))
    elif kind == "bosses":          # square bosses, each ringed, at the stations and between them
        for u in _us(L, pitch / 2, margin, 0.0):
            s_ = min(hh / 2 - 0.2, 1.4)
            out.append(_stepped(rect(u - s_, vm - s_, u + s_, vm + s_), b, 0.4))
            out.append(_stepped(circle((u, vm), s_ * 0.6, 16), b + 0.4, 0.2))
    # ---- the first ten houses' friezes (one set per building)
    elif kind == "anthemion":       # palmettes (a fan of five petals on a half-round base), a lotus bud at each station
        for uc, wd in bays:
            r = min(hh - 0.3, wd / 2 - 0.5)
            pv = v0 + 0.2
            pet = cs_union([stroke([(uc + 0.5 * math.cos(a), pv + 0.5 * math.sin(a)),
                                    (uc + r * math.cos(a), pv + r * math.sin(a))], 0.55)
                            for a in np.linspace(0.5, math.pi - 0.5, 5)])
            out.append(_stepped(pet ^ rect(uc - wd / 2, v0, uc + wd / 2, v1), b, 0.4))
            out.append(_stepped(circle((uc, pv), 0.9, 20) ^ rect(uc - 1.0, v0, uc + 1.0, v1), b, 0.6))
        for u in _us(L, pitch, margin, 0.0):
            out.append(_stepped(poly([(u - 0.55, v0 + 0.1), (u + 0.55, v0 + 0.1), (u + 0.4, vm), (u, v1 - 0.1),
                                      (u - 0.4, vm)]), b, 0.4))
    elif kind == "rinceau":         # a running vine: a low wave with a curled tendril in every hollow
        n = max(2, int(round((L - 2 * margin) / 4.4)))
        pu = (L - 2 * margin) / n
        amp = hh * 0.15
        pts = [(margin + t, vm + amp * math.sin(2 * math.pi * t / pu)) for t in np.linspace(0, L - 2 * margin, 12 * n + 1)]
        out.append(_stepped(stroke(pts, 0.5, caps=False), b, 0.4))
        rc = max(0.5, min((vm - v0) / 2 - 0.35, pu / 4 - 0.4))
        for k in range(2 * n):
            below = k % 2 == 0                 # under a crest, then over a trough
            uc = margin + pu * (k / 2 + 0.25)
            vc = (v0 + vm - amp) / 2 if below else (vm + amp + v1) / 2
            vw = vm + amp if below else vm - amp
            a0 = math.pi / 2 if below else -math.pi / 2
            sg = 1 if below else -1
            arc = [(uc + rc * math.cos(a0 + sg * s), vc + rc * math.sin(a0 + sg * s)) for s in np.linspace(0, 1.5 * math.pi, 14)]
            out.append(_stepped(stroke([(uc, vw)] + arc, 0.5, caps=False), b, 0.4))
            out.append(_stepped(circle(arc[-1], 0.42, 12), b, 0.4))
    elif kind == "paterae":         # round dishes: a rim, eight spokes and a boss, in every bay
        for uc, wd in bays:
            r = min(hh / 2 - 0.1, wd / 2 - 0.5, 1.8)
            rim = circle((uc, vm), r, 32) - circle((uc, vm), r - 0.5, 32)
            spokes = cs_union([stroke([(uc, vm), (uc + (r - 0.3) * math.cos(a), vm + (r - 0.3) * math.sin(a))], 0.45, caps=False)
                               for a in np.linspace(0, 2 * math.pi, 8, endpoint=False)])
            out.append(_stepped(rim + spokes, b, 0.4))
            out.append(_stepped(circle((uc, vm), min(0.7, r * 0.4), 16), b + 0.4, 0.2))
    elif kind == "coffers":         # sunk-margin panels: a channel round a raised field, a square boss on it
        for uc, wd in bays:
            fo = rect(uc - wd / 2 + 0.4, v0 + 0.2, uc + wd / 2 - 0.4, v1 - 0.2)
            fi = fo.offset(-0.55, JoinType.Miter, 4.0)
            cuts.append(ext(fo - fi, b - 0.3, b + 0.1))
            s_ = min(hh / 2 - 0.8, 0.9)
            out.append(_stepped(poly([(uc - s_, vm), (uc, vm + s_), (uc + s_, vm), (uc, vm - s_)]), b, 0.4))
    elif kind == "wreaths":         # a ring of beads round a boss, in every bay
        for uc, wd in bays:
            r = min(hh / 2 - 0.5, wd / 2 - 0.9, 1.5)
            n_ = max(6, int(2 * math.pi * r / 1.25))
            for j in range(n_):
                a = 2 * math.pi * j / n_
                out.append(_stepped(circle((uc + r * math.cos(a), vm + r * math.sin(a)), 0.36, 10), b, 0.4))
            out.append(_stepped(circle((uc, vm), 0.55, 14), b, 0.5))
            for sg in (-1, 1):                 # ribbon ends
                out.append(_stepped(stroke([(uc + sg * 0.3, vm - r - 0.1), (uc + sg * 1.2, vm - r - 0.1)], 0.45) ^
                                    rect(uc - wd / 2, v0, uc + wd / 2, v1), b, 0.3))
    elif kind == "lunettes":        # sunk half-rounds standing on the foot, a bead over each
        for uc, wd in bays:
            r = min(hh - 1.4, wd / 2 - 0.6, 2.2)
            half = circle((uc, v0 + 0.2), r, 28) ^ rect(uc - r - 1, v0 + 0.2, uc + r + 1, v1)
            cuts.append(ext(half.offset(-0.5, JoinType.Round) ^ rect(uc - r, v0 + 0.5, uc + r, v1), b - 0.3, b + 0.1))
            out.append(_stepped(half - half.offset(-0.5, JoinType.Round), b, 0.3))
            out.append(_stepped(circle((uc, min(v1 - 0.45, v0 + r + 0.75)), 0.4, 12), b, 0.4))
    elif kind == "lancets":         # a Gothic arcade: pointed arches on shared slender shafts
        n = max(2, int(round((L - 2 * margin) / 2.8)))
        pu = (L - 2 * margin) / n
        hw = pu / 2
        R = hw * 1.5                        # each side an arc centred on the far springing
        am = math.acos((R - hw) / R)
        ws = v1 - 0.35 - R * math.sin(am)   # the springing line
        for k in range(n):
            uc = margin + pu * (k + 0.5)
            pts = [(uc - hw, v0), (uc - hw, ws)] + \
                [(uc - hw + R - R * math.cos(a), ws + R * math.sin(a)) for a in np.linspace(0, am, 8)] + \
                [(uc + hw - R + R * math.cos(a), ws + R * math.sin(a)) for a in np.linspace(am, 0, 8)] + [(uc + hw, v0)]
            out.append(_stepped(stroke(pts, 0.5, caps=False) ^ rect(0.0, v0, L, v1), b, 0.4))
    elif kind == "trefoils":        # a solid trefoil in a roundel, in every bay
        for uc, wd in bays:
            R = min(hh / 2 - 0.05, wd / 2 - 0.4, 1.9)
            out.append(_stepped(circle((uc, vm), R, 32) - circle((uc, vm), R - 0.5, 32), b, 0.4))
            r = 0.5 * (R - 0.5)
            d_ = (R - 0.5) - r + 0.05
            tf = cs_union([circle((uc + d_ * math.cos(a), vm + d_ * math.sin(a)), r, 16)
                           for a in (math.pi / 2, math.pi / 2 + 2.094, math.pi / 2 + 4.189)] + [circle((uc, vm), 0.4, 12)])
            out.append(_stepped(tf, b, 0.4))
    elif kind == "corbel_arches":   # a Romanesque corbel table: little round arches hung on corbels
        n = max(2, int(round((L - 2 * margin) / 2.6)))
        pu = (L - 2 * margin) / n
        r = min(pu / 2 - 0.25, hh / 2 - 0.3)
        vs = v1 - 0.25 - r
        for k in range(n):
            uc = margin + pu * (k + 0.5)
            arc = [(uc + r * math.cos(a), vs + r * math.sin(a)) for a in np.linspace(0, math.pi, 12)]
            out.append(_stepped(stroke(arc, 0.5, caps=False), b, 0.4))
        for k in range(n + 1):
            u = margin + pu * k
            out.append(_stepped(poly([(u - 0.6, vs + 0.2), (u + 0.6, vs + 0.2), (u + 0.35, vs - 1.2), (u - 0.35, vs - 1.2)]),
                                b, 0.5))
    elif kind == "interlace":       # interlaced round arches: arches of two bays springing from every shaft
        n = max(3, int(round((L - 2 * margin) / 1.8)))
        pu = (L - 2 * margin) / n
        r = pu
        vs = v1 - 0.25 - min(r, hh - 1.2)
        ry = min(r, hh - 1.2)
        for k in range(n - 1):
            uc = margin + pu * (k + 1)
            arc = [(uc + r * math.cos(a), vs + ry * math.sin(a)) for a in np.linspace(0, math.pi, 16)]
            out.append(_stepped(stroke(arc, 0.5, caps=False), b, 0.4))
        for k in range(n + 1):
            u = margin + pu * k
            out.append(_stepped(rect(u - 0.25, v0, u + 0.25, vs + 0.1), b, 0.4))
    elif kind == "nailhead":        # rows of little pyramids
        rows = [vm] if hh < 3.2 else [vm - hh / 4, vm + hh / 4]
        s_ = min(0.7, hh / (2 * len(rows)) - 0.15)
        n = max(2, int((L - 2 * margin) / (2 * s_ + 0.6)))
        pu = (L - 2 * margin) / n
        for j, vr in enumerate(rows):
            for k in range(n):
                uc = margin + pu * (k + 0.5 + (0.5 if j % 2 else 0.0))
                if uc > L - margin:
                    continue
                for st in range(3):
                    e_ = s_ - 0.2 * st
                    if e_ < 0.25:
                        break
                    out.append(ext(rect(uc - e_, vr - e_, uc + e_, vr + e_), b + 0.2 * st - (0.05 if st == 0 else 0.0),
                                   b + 0.2 * (st + 1)))
    elif kind == "stickwork":       # a stick frame in every bay, with little knee braces in its upper corners
        for uc, wd in bays:
            fo = rect(uc - wd / 2 + 0.3, v0 + 0.1, uc + wd / 2 - 0.3, v1 - 0.1)
            out.append(_stepped(fo - fo.offset(-0.5, JoinType.Miter, 4.0), b, 0.4))
            k_ = min(1.4, hh / 2 - 0.3)
            for sg in (-1, 1):
                x = uc + sg * (wd / 2 - 0.55)
                out.append(_stepped(stroke([(x, v1 - 0.35 - k_), (x - sg * k_, v1 - 0.35)], 0.45, caps=False) ^ fo, b, 0.4))
            out.append(_stepped(rect(uc - 0.25, v0 + 0.1, uc + 0.25, v1 - 0.1), b, 0.4))
    elif kind == "xbrace":          # X-braced stick panels
        for uc, wd in bays:
            fo = rect(uc - wd / 2 + 0.3, v0 + 0.1, uc + wd / 2 - 0.3, v1 - 0.1)
            fi = fo.offset(-0.5, JoinType.Miter, 4.0)
            x0, x1 = uc - wd / 2 + 0.55, uc + wd / 2 - 0.55
            xs = stroke([(x0, v0 + 0.35), (x1, v1 - 0.35)], 0.5, caps=False) + \
                stroke([(x0, v1 - 0.35), (x1, v0 + 0.35)], 0.5, caps=False)
            out.append(_stepped((fo - fi) + (xs ^ fi), b, 0.4))
    elif kind == "diamonds":        # a chain of diamonds tip to tip, a bead at every joint
        n = max(2, int(round((L - 2 * margin) / (hh * 0.9))))
        pu = (L - 2 * margin) / n
        for k in range(n):
            uc = margin + pu * (k + 0.5)
            d_ = poly([(uc - pu / 2, vm), (uc, v1 - 0.1), (uc + pu / 2, vm), (uc, v0 + 0.1)])
            out.append(_stepped(d_ - d_.offset(-0.5, JoinType.Miter, 4.0), b, 0.4))
        for k in range(n + 1):
            out.append(_stepped(circle((margin + pu * k, vm), 0.45, 12), b, 0.5))
    elif kind == "teeth":           # sawn teeth hanging from the head, a bead under each point
        n = max(2, int(round((L - 2 * margin) / 1.9)))
        pu = (L - 2 * margin) / n
        tip = v1 - hh * 0.62
        for k in range(n):
            uc = margin + pu * (k + 0.5)
            out.append(_stepped(poly([(uc - pu / 2 + 0.1, v1), (uc + pu / 2 - 0.1, v1), (uc, tip)]), b, 0.4))
            out.append(_stepped(circle((uc, max(v0 + 0.4, tip - 0.65)), 0.38, 12), b, 0.4))
    elif kind == "strapwork":       # straps: an outlined tablet with round ends and an eye in every bay, a boss at each station
        for uc, wd in bays:
            hw_ = wd / 2 - 0.9
            rr = min(hh / 2 - 0.2, 1.4)
            if hw_ <= rr:
                continue
            tab = cs_union([rect(uc - hw_ + rr, vm - rr, uc + hw_ - rr, vm + rr), circle((uc - hw_ + rr, vm), rr, 24),
                            circle((uc + hw_ - rr, vm), rr, 24)])
            out.append(_stepped(tab - tab.offset(-0.5, JoinType.Round), b, 0.4))
            out.append(_stepped(circle((uc, vm), min(0.6, rr - 0.7), 14), b, 0.5))
            out.append(_stepped(rect(uc - hw_ + rr, vm - 0.22, uc - 0.9, vm + 0.22) + rect(uc + 0.9, vm - 0.22, uc + hw_ - rr, vm + 0.22),
                                b, 0.3))
        for u in _us(L, pitch, margin, 0.0):
            out.append(_stepped(rect(u - 0.55, vm - 0.55, u + 0.55, vm + 0.55), b, 0.5))
    elif kind == "roses":           # Tudor roses: five outer petals, five inner, a seed boss
        for uc, wd in bays:
            r = min(hh / 2 - 0.1, wd / 2 - 0.4, 1.8)
            outer = cs_union([circle((uc + r * 0.55 * math.cos(a), vm + r * 0.55 * math.sin(a)), r * 0.45, 16)
                              for a in np.linspace(math.pi / 2, math.pi / 2 + 2 * math.pi, 5, endpoint=False)])
            inner = cs_union([circle((uc + r * 0.3 * math.cos(a), vm + r * 0.3 * math.sin(a)), r * 0.3, 14)
                              for a in np.linspace(math.pi / 2 + math.pi / 5, math.pi / 2 + math.pi / 5 + 2 * math.pi, 5, endpoint=False)])
            out.append(_stepped(outer + circle((uc, vm), r * 0.6, 20), b, 0.4))
            out.append(_stepped(inner + circle((uc, vm), r * 0.25, 12), b + 0.4, 0.2))
            out.append(_stepped(circle((uc, vm), max(0.35, r * 0.18), 12), b + 0.6, 0.2))
    elif kind == "crenels":         # a battlement: merlons on a plinth strip, each with a sunk slit
        out.append(_stepped(rect(0.3, v0, L - 0.3, v0 + 0.8), b, 0.3))
        n = max(2, int(round((L - 2 * margin) / 2.6)))
        pu = (L - 2 * margin) / n
        for k in range(n + 1):
            u = margin + pu * k
            out.append(_stepped(rect(u - 0.8, v0 + 0.6, u + 0.8, v1 - 0.1), b, 0.5))
            cuts.append(ext(rect(u - 0.25, vm - 0.2, u + 0.25, v1 - 0.8), b + 0.2, b + 1.0))
    elif kind == "incised":         # Eastlake incised work: a sunk line along each bay, a sunk ring and ticks
        for uc, wd in bays:
            r = min(hh / 2 - 0.4, 1.2)
            cuts.append(ext(circle((uc, vm), r, 24) - circle((uc, vm), r - 0.5, 24), b - 0.3, b + 0.1))
            for sg in (-1, 1):
                a_, e_ = uc + sg * (r + 0.4), uc + sg * (wd / 2 - 0.7)
                if abs(e_ - a_) > 0.8:
                    cuts.append(ext(rect(min(a_, e_), vm - 0.25, max(a_, e_), vm + 0.25), b - 0.3, b + 0.1))
                    cuts.append(ext(rect(e_ - 0.25, vm - r, e_ + 0.25, vm + r), b - 0.3, b + 0.1))
            out.append(_stepped(circle((uc, vm), max(0.35, r - 0.9), 12), b, 0.3))
    elif kind == "cartouches":      # a cartouche (a tablet with hollowed corners and a raised oval) in every bay
        for uc, wd in bays:
            hw_ = min(wd / 2 - 0.5, 3.2)
            hv = hh / 2 - 0.1
            c_ = min(0.9, hv - 0.4)
            tab = rect(uc - hw_, vm - hv, uc + hw_, vm + hv) - cs_union(
                [circle((uc + sx * hw_, vm + sy * hv), c_, 16) for sx in (-1, 1) for sy in (-1, 1)])
            out.append(_stepped(tab - tab.offset(-0.5, JoinType.Miter, 4.0), b, 0.4))
            out.append(_stepped(oval((uc, vm), max(0.6, hw_ - 1.6), max(0.45, hv - 1.0)), b, 0.5))
    elif kind == "acanthus":        # a row of upright leaves, each with a raised midrib
        n = max(2, int(round((L - 2 * margin) / 2.2)))
        pu = (L - 2 * margin) / n
        for k in range(n):
            uc = margin + pu * (k + 0.5)
            hw_ = pu / 2 + 0.05
            leaf = poly([(uc - hw_, v0), (uc + hw_, v0), (uc + hw_ * 0.9, v0 + hh * 0.45), (uc + hw_ * 0.3, v1 - 0.6),
                         (uc, v1), (uc - hw_ * 0.3, v1 - 0.6), (uc - hw_ * 0.9, v0 + hh * 0.45)])
            out.append(_stepped(leaf, b, 0.3))
            out.append(_stepped(stroke([(uc, v0 + 0.2), (uc, v1 - 0.4)], 0.45, caps=False), b + 0.3, 0.2))
    elif kind == "shells":          # scallop shells hanging from the head, ribbed, with a hinge boss
        for uc, wd in bays:
            r = min(hh - 0.5, wd / 2 - 0.5, 2.6)
            half = circle((uc, v1), r, 32) ^ rect(uc - r - 1, v1 - r - 1, uc + r + 1, v1)
            lobes = cs_union([circle((uc + r * math.cos(a), v1 - r * math.sin(a) * 0.98), 0.42, 10)
                              for a in np.linspace(0.25, math.pi - 0.25, 7)])
            shell = (half + lobes) ^ rect(uc - wd / 2, v0, uc + wd / 2, v1)
            out.append(_stepped(shell, b, 0.4))
            for a in np.linspace(0.45, math.pi - 0.45, 5):
                cuts.append(ext(stroke([(uc + 1.2 * math.cos(a), v1 - 1.2 * math.sin(a)),
                                        (uc + (r - 0.4) * math.cos(a), v1 - (r - 0.4) * math.sin(a))], 0.5, caps=False),
                                b + 0.2, b + 0.6))
            out.append(_stepped(circle((uc, v1 - 0.2), 0.7, 14) ^ rect(uc - 1, v0, uc + 1, v1), b + 0.4, 0.2))
    elif kind == "pendants":        # turned pendants hanging from the head, long and short in turn
        n = max(2, int(round((L - 2 * margin) / 1.6)))
        pu = (L - 2 * margin) / n
        for k in range(n + 1):
            u = margin + pu * k
            lo = v0 + 0.5 if k % 2 == 0 else vm
            out.append(_stepped(rect(u - 0.26, lo, u + 0.26, v1), b, 0.4))
            out.append(_stepped(circle((u, lo), 0.5, 12), b, 0.5))
            out.append(_stepped(rect(u - 0.45, v1 - 0.9, u + 0.45, v1 - 0.4), b, 0.4))
    elif kind == "oculi":           # sunk round eyes with raised rims and a keystone over each
        for uc, wd in bays:
            r = min(hh / 2 - 0.5, wd / 2 - 0.7, 1.5)
            cuts.append(ext(circle((uc, vm - 0.2), r - 0.5, 24), b - 0.3, b + 0.1))
            out.append(_stepped(circle((uc, vm - 0.2), r, 28) - circle((uc, vm - 0.2), r - 0.5, 28), b, 0.4))
            out.append(_stepped(poly([(uc - 0.45, vm - 0.2 + r - 0.2), (uc + 0.45, vm - 0.2 + r - 0.2), (uc + 0.6, v1 - 0.05),
                                      (uc - 0.6, v1 - 0.05)]), b, 0.5))
    elif kind == "pearls":          # a string of big and little pearls
        big = min(hh / 2 - 0.3, 0.9)
        n = max(2, int(round((L - 2 * margin) / (2 * big + 1.4))))
        pu = (L - 2 * margin) / n
        for k in range(n):
            uc = margin + pu * (k + 0.5)
            out.append(_stepped(oval((uc, vm), big * 1.25, big), b, 0.5))
            out.append(_stepped(circle((uc + pu / 2, vm), 0.4, 12), b, 0.4) if k < n - 1 else M())
    elif kind == "plain":
        pass
    elif kind in FRIEZE_EXTRA:
        if L < 2 * margin + 1.0:
            return M(), M()
        o_, c_ = FRIEZE_EXTRA[kind](L, h, b, pitch, margin, pair, half)
        out += o_
        cuts += c_
    else:
        raise ValueError(kind)
    return union([m for m in out if not m.is_empty()]) if out else M(), union(cuts) if cuts else M()


def frieze(path, z0, h, b=1.2, kind="panels", pitch=10.0, margin=3.0, pair=0.0, half=0.6, fillets=True, dd=0.4,
           skip=None):
    """A frieze ring (prints upright): a board ``b`` off the wall plane, a bead at its foot,
    a fillet at its head (grown out at 45 degrees) and ornament ``kind`` (see FRIEZES)."""
    extra = []
    if fillets:
        extra = [(b + 0.4, 0.0), (b + 0.4, 0.4), (b, 0.8)]
        head = [(b, h - 0.8), (b + 0.4, h - 0.4), (b + 0.4, h)]
    else:
        head = []
    prof = [(CLR, 0.0), (b, 0.0)] + extra[1:] + head + ([(b, h)] if not head else []) + [(CLR, h)]
    ring = sweep_ring(path, [(d, z0 + z) for d, z in prof])
    orn, cuts = [], []
    for f in _edges(path):
        o, c = _frieze_edge(kind, f.L, h, b, pitch, margin, pair, half, dd)
        if not o.is_empty():
            orn.append(_place(f, z0, o))
        if not c.is_empty():
            cuts.append(_place(f, z0, c))
    out = ring + union(orn) if orn else ring
    if cuts:
        out = out - union(cuts)
    return out


# ------------------------------------------------------------------ courses (upright)
COURSES = ("dentil", "eggdart", "beadreel", "billet", "cable", "drops", "blocks", "dogtooth", "pellets", "rope",
           "scallop", "reeds")


def _course_edge(kind, L, h, b, pitch, margin, p):
    out = []
    vm = h / 2
    if kind == "dentil":
        tooth, gap = p.get("tooth", 0.9), p.get("gap", 0.6)
        n = int((L - 1.2) / (tooth + gap))
        u0 = (L - (n * (tooth + gap) - gap)) / 2
        for k in range(n):
            u = u0 + k * (tooth + gap)
            out.append(ext(rect(u, 0.0, u + tooth, h), b - 0.05, b + p.get("d", 0.7)))
    elif kind == "blocks":
        for u in _us(L, pitch / 2, margin, 0.0):
            out.append(chamfer_box(u - 0.8, 0.0, u + 0.8, h, b - 0.05, p.get("d", 1.0) + 0.05, c=0.3, bottom=0.0))
    elif kind == "eggdart":
        pu = p.get("pu", 1.8)
        n = int((L - 1.0) / pu)
        u0 = (L - n * pu) / 2
        for k in range(n):
            uc = u0 + pu * (k + 0.5)
            out.append(_stepped(oval((uc, vm + 0.05), pu * 0.32, h / 2 - 0.2), b, 0.5))
            out.append(_stepped(poly([(uc + pu / 2 - 0.26, h - 0.3), (uc + pu / 2 + 0.26, h - 0.3), (uc + pu / 2, 0.3)]),
                                b, 0.4))
    elif kind == "beadreel":
        pu = p.get("pu", 2.0)
        n = int((L - 1.0) / pu)
        u0 = (L - n * pu) / 2
        for k in range(n):
            uc = u0 + pu * (k + 0.5)
            out.append(_stepped(oval((uc, vm), pu * 0.3, min(0.45, h / 2 - 0.1)), b, 0.4))
            out.append(_stepped(circle((uc + pu / 2, vm), min(0.32, h / 2 - 0.1), 12), b, 0.4))
    elif kind == "billet":
        pu = p.get("pu", 1.8)
        n = int((L - 1.0) / pu)
        u0 = (L - n * pu) / 2
        for k in range(n):
            u = u0 + pu * k
            row = 0 if k % 2 == 0 else 1
            v_0 = 0.2 if row == 0 else vm + 0.1
            out.append(_stepped(rect(u + 0.2, v_0, u + pu - 0.2, v_0 + h / 2 - 0.3), b - 0.05, 0.65))
    elif kind in ("cable", "rope"):
        pu = p.get("pu", 1.2)
        n = int((L - 1.0) / pu)
        u0 = (L - n * pu) / 2
        lean = pu * (0.9 if kind == "cable" else 0.5)
        out.append(_stepped(rect(u0, 0.3, u0 + n * pu, h - 0.3), b, 0.2))
        for k in range(n):
            u = u0 + pu * k
            out.append(_stepped(stroke([(u, 0.3), (u + lean, h - 0.3)], 0.5, caps=False) ^ rect(u0, 0.0, u0 + n * pu, h),
                                b + 0.2, 0.4))
    elif kind == "drops":
        for u in _us(L, pitch / 3, margin, 0.0):
            out.append(_stepped(cs_union([circle((u, 0.55), 0.45, 12), rect(u - 0.25, 0.55, u + 0.25, h - 0.3)]), b, 0.4))
    elif kind == "dogtooth":
        pu = p.get("pu", 1.8)
        n = int((L - 1.0) / pu)
        u0 = (L - n * pu) / 2
        for k in range(n):
            uc = u0 + pu * (k + 0.5)
            out.append(_stepped(poly([(uc - pu / 2 + 0.1, 0.2), (uc + pu / 2 - 0.1, 0.2), (uc, h - 0.2)]), b, 0.4))
            out.append(_stepped(poly([(uc - 0.3, 0.5), (uc + 0.3, 0.5), (uc, h * 0.6)]), b + 0.4, 0.2))
    elif kind == "pellets":
        pu = p.get("pu", 1.4)
        n = int((L - 1.0) / pu)
        u0 = (L - n * pu) / 2
        for k in range(n):
            out.append(_stepped(circle((u0 + pu * (k + 0.5), vm), min(0.42, h / 2 - 0.15), 14), b, 0.4))
    elif kind == "scallop":
        pu = p.get("pu", 2.2)
        n = int((L - 1.0) / pu)
        u0 = (L - n * pu) / 2
        for k in range(n):
            uc = u0 + pu * (k + 0.5)
            r = pu / 2 - 0.1
            out.append(_stepped(circle((uc, h - 0.2), r, 20) ^ rect(uc - r, max(0.2, h - 0.2 - r), uc + r, h - 0.2), b, 0.4))
    elif kind == "reeds":
        for dv in np.arange(0.35, h - 0.2, 0.7):
            out.append(_stepped(rect(0.3, dv - 0.2, L - 0.3, dv + 0.2), b, 0.4))
    elif kind in COURSE_EXTRA:
        out += COURSE_EXTRA[kind](L, h, b, pitch, margin, p)
    else:
        raise ValueError(kind)
    return union([m for m in out if not m.is_empty()]) if out else M()


def course(path, z0, h, b=1.4, kind="dentil", pitch=10.0, margin=3.0, **p):
    """A course ring (prints upright): a band ``b`` off the wall plane carrying a small repeat
    ornament ``kind`` (see COURSES)."""
    ring = body_ring(path, z0, h, b)
    orn = []
    for f in _edges(path):
        if f.L < 2.0:
            continue
        o = _course_edge(kind, f.L, h, b, pitch, margin, p)
        if not o.is_empty():
            orn.append(_place(f, z0, o))
    return ring + union(orn) if orn else ring


# ------------------------------------------------------------------ bracket bed (upside down)
def bed(path, z0, h, b, P, brackets=None, ts=0.8, fascia=None, pitch=10.0, margin=3.0, pair=0.0, back=None,
        drop=0.0, soffit_panels=False):
    """A bracket bed (prints upside down): a band ``b`` off the wall, a soffit ``ts`` thick
    projecting to ``P`` at the top, an optional fascia strip (dict(h, d)) on the soffit's edge,
    and brackets under it: dict(style, h, t) (trimwork.bracket styles), their backs at ``back``
    (clear of the rings below), hanging ``drop`` below the ring's foot if tall."""
    prof_extra = [(b, h - ts), (P, h - ts)]
    ring = sweep_ring(path, [(d, z0 + z) for d, z in [(CLR, 0.0), (b, 0.0)] + prof_extra + [(P, h), (CLR, h)]])
    parts = [ring]
    if fascia:
        fh, fd = fascia["h"], fascia.get("d", 0.4)
        parts.append(sweep_ring(path, [(d, z0 + z) for d, z in [(P - 0.6, h - ts - fh), (P + fd, h - ts - fh),
                                                                (P + fd, h), (P - 0.6, h)]]))
    if brackets:
        from .trimwork import bracket
        bk = back if back is not None else b
        for f in _edges(path):
            for u in _us(f.L, pitch, margin, pair):
                br = bracket(brackets["style"], brackets["h"], P - bk - 0.3, brackets.get("t", 0.8), u=u,
                             v_top=h - ts + 0.01, w0=bk)
                parts.append(_place(f, z0, br))
    return union(parts)


# ------------------------------------------------------------------ crown (upside down)
CROWNS = ("cyma", "cavetto", "ovolo", "stepped", "torus", "ogee_fillet", "bevel", "reverse")


def crown_profile(kind, b, P, h):
    """Outer profile (d, z) of a crown from (b, 0) to (P, h), widening upward (so it prints
    upside down with no overhang)."""
    if kind == "cyma":        # cyma recta: hollow below, round above
        pts = [(b + (P - b) * (0.5 - 0.5 * math.cos(math.pi * s)), h * s) for s in np.linspace(0, 1, 11)]
        pts = [(b + (P - b) * (s - math.sin(2 * math.pi * s) / (2 * math.pi)), 0.2 + (h - 0.6) * s)
               for s in np.linspace(0, 1, 13)]
        return [(b, 0.0)] + pts + [(P, h)]
    if kind == "cavetto":
        R = min(P - b, h - 0.6)
        return [(b, 0.0), (b, h - 0.4 - R)] + [(b + R - R * math.cos(a), h - 0.4 - R + R * math.sin(a))
                                               for a in np.linspace(0.1, math.pi / 2, 8)][:-1] + \
            [(b + R, h - 0.4), (P, h - 0.4), (P, h)]
    if kind == "ovolo":
        R = min(P - b, h - 0.4)
        return [(b, 0.0), (b, h - 0.2 - R)] + [(b + R * math.sin(a), h - 0.2 - R * math.cos(a))
                                               for a in np.linspace(0.15, math.pi / 2, 8)] + [(P, h - 0.2), (P, h)]
    if kind == "stepped":
        n = 3
        return [(b, 0.0)] + [pt for k in range(n) for pt in ((b + (P - b) * k / n, h * (k + 1) / (n + 1)),
                                                              (b + (P - b) * (k + 1) / n, h * (k + 1) / (n + 1)))] + [(P, h)]
    if kind == "torus":
        r = min(0.6, h / 4)
        return [(b, 0.0), (b + 0.4, 0.4)] + [(b + 0.4 + r * math.sin(a), 0.4 + r - r * math.cos(a))
                                            for a in np.linspace(0.2, math.pi, 8)] + \
            [(b + 0.4, 0.4 + 2 * r), (b + 0.4, 0.4 + 2 * r + 0.2), (P, h - 0.2), (P, h)]
    if kind == "ogee_fillet":
        m = h * 0.55
        pts = [(b + (P - b - 0.4) * (s - math.sin(2 * math.pi * s) / (2 * math.pi)), 0.2 + (m - 0.2) * s)
               for s in np.linspace(0, 1, 11)]
        return [(b, 0.0)] + pts + [(P - 0.4, h - 0.8), (P, h - 0.4), (P, h)]
    if kind == "bevel":
        return [(b, 0.0), (b, h * 0.3), (P, h - 0.4), (P, h)]
    if kind == "reverse":     # cyma reversa: round below, hollow above
        pts = [(b + (P - b) * (s + math.sin(2 * math.pi * s) / (2 * math.pi)), 0.2 + (h - 0.6) * s)
               for s in np.linspace(0, 1, 13)]
        return [(b, 0.0)] + pts + [(P, h)]
    raise ValueError(kind)


def crown(path, z0, h, b, P, kind="cyma", blocks=None, pitch=10.0, margin=3.0):
    """A crown moulding ring (prints upside down): band ``b`` off the wall, profile ``kind``
    out to ``P`` at its top. ``blocks``: dict(w, h, d) raised blocks on the crown's fascia at
    the bracket stations (end blocks over each bracket)."""
    prof = [(CLR, 0.0)] + crown_profile(kind, b, P, h) + [(CLR, h)]
    ring = sweep_ring(path, [(d, z0 + z) for d, z in prof])
    if blocks:
        orn = []
        for f in _edges(path):
            for u in _us(f.L, pitch, margin, 0.0):
                orn.append(_place(f, z0, box([u - blocks["w"] / 2, h - blocks["h"], P - 0.4],
                                              [u + blocks["w"] / 2, h, P + blocks["d"]])))
        ring = ring + union(orn)
    return ring


# ------------------------------------------------------------------ a whole level
def level(path, z0, spec, cut=None, t=3.0):
    """Build the rings of one cornice level round ``path`` (the wall plane), the lowest
    standing on the ledge top at z0. ``spec``:

        dict(pitch=10, margin=3, pair=0,
             layers=[dict(kind="frieze", h=4.4, b=1.2, orn="panels", role="Accent"),
                     dict(kind="course", h=1.6, b=1.4, orn="dentil", role="Trim2", tooth=.9, gap=.6),
                     dict(kind="bed", h=2.4, b=1.4, P=5.0, role="Trim", brackets=dict(style="scroll", h=6.0)),
                     dict(kind="crown", h=2.4, b=1.4, P=6.0, orn="cyma", role="Trim")])

    ``cut``: a solid to cut every ring back from (blocks rising through the level). Returns
    (rings, top): rings = [dict(role, solid, flip, name)], top = z of the level's top."""
    pitch, margin, pair = spec.get("pitch", 10.0), spec.get("margin", 3.0), spec.get("pair", 0.0)
    z = z0
    rings = []
    front = CLR
    for k, L_ in enumerate(spec["layers"]):
        kind, h = L_["kind"], L_["h"]
        if kind == "frieze":
            m = frieze(path, z, h, b=L_.get("b", 1.2), kind=L_.get("orn", "panels"), pitch=pitch, margin=margin, pair=pair,
                       half=L_.get("half", 0.6), fillets=L_.get("fillets", True))
            flip = False
            front = max(front, L_.get("b", 1.2) + 1.2)
        elif kind == "course":
            kw = {k_: v for k_, v in L_.items() if k_ not in ("kind", "h", "b", "orn", "role")}
            m = course(path, z, h, b=L_.get("b", 1.4), kind=L_.get("orn", "dentil"), pitch=pitch, margin=margin, **kw)
            flip = False
            front = max(front, L_.get("b", 1.4) + 1.2)
        elif kind == "bed":
            br = L_.get("brackets")
            if br and "h" not in br:
                # reach down to ``reach`` of the way over the rings below (default: mid-frieze)
                br = dict(br)
                ts = L_.get("ts", 0.8)
                br["h"] = round(((z + h - ts) - (z0 + (z - z0) * (1.0 - br.get("reach", 0.6)))) / 0.2) * 0.2
            m = bed(path, z, h, L_.get("b", 1.4), L_["P"], brackets=br, ts=L_.get("ts", 0.8),
                    fascia=L_.get("fascia"), pitch=pitch, margin=margin, pair=pair, back=L_.get("back", front + 0.15))
            flip = True
        elif kind == "crown":
            b_c = L_.get("b", 1.4)
            m = crown(path, z, h, b_c, L_["P"], kind=L_.get("orn", "cyma"), blocks=L_.get("blocks"),
                      pitch=pitch, margin=margin)
            prev = spec["layers"][k - 1] if k else None
            if prev is not None and prev["kind"] == "bed" and prev["P"] > b_c:
                # a bed under the crown prints on the crown's foot (both upside down, one part):
                # a 45 degree cove from the bed's soffit edge up into the crown carries it
                H = min(prev["P"] - b_c, h)
                m = union([m, sweep_ring(path, [(CLR, z), (prev["P"], z), (prev["P"] - H, z + H), (CLR, z + H)])])
            flip = True
        else:
            raise ValueError(kind)
        if cut is not None:
            m = m - cut
        rings.append(dict(role=L_["role"], solid=m, flip=flip, name=L_.get("name", kind), z0=z, z1=z + h))
        z += h
    return rings, z


def blades(cuts, z0, z1, kerf=0.3, reach=16.0):
    """Thin vertical cutters for a level's rings (pass them as ``cut``): each (point, direction)
    cuts from 2 mm inside the point out along the direction, ``kerf`` wide."""
    out = []
    for p, d in cuts:
        d = np.asarray(d, float) / np.linalg.norm(d)
        A = np.array([[d[0], -d[1], 0.0, p[0]], [d[1], d[0], 0.0, p[1]], [0.0, 0.0, 1.0, 0.0]])
        out.append(box([-2.0, -kerf / 2, z0 - 1.0], [reach, kerf / 2, z1 + 1.0]).transform(A))
    return union(out)


def tower_cuts(path, centre, near, wall=None, away=None, tower=None, house=None):
    """Where a level wraps a tower standing against the house, a closed ring cannot be fitted
    (the tower's upper storey is in the way). These cuts (for ``blades``) part the rings at
    every inside corner of the path within ``near`` of the tower's centre (along the corner's
    bisector), at every corner of the ``tower`` outline lying on a wall of the ``house``
    outline (where a tower face runs on flush with the wall; square to that wall) and, given
    ``away`` (a direction from the centre, off the house) and the tower's apothem ``wall``,
    once more through the tower's far side, so no piece wraps more than half of the tower and
    each one fits on from the side."""
    P = [np.asarray(p, float) for p in ccw(path)]
    n = len(P)
    c = np.asarray(centre, float)
    cuts = []
    for i in range(n):
        a, p, b = P[i - 1], P[i], P[(i + 1) % n]
        t1, t2 = (p - a) / np.linalg.norm(p - a), (b - p) / np.linalg.norm(b - p)
        if t1[0] * t2[1] - t1[1] * t2[0] < -1e-6 and np.linalg.norm(p - c) < near:     # an inside corner
            nrm = np.array([t1[1], -t1[0]]) + np.array([t2[1], -t2[0]])
            cuts.append((tuple(p), tuple(nrm / np.linalg.norm(nrm))))
    if tower is not None and house is not None:
        H = [np.asarray(p, float) for p in ccw(house)]
        for q in (np.asarray(q, float) for q in tower):
            for i in range(len(H)):
                a, b = H[i], H[(i + 1) % len(H)]
                t = (b - a) / np.linalg.norm(b - a)
                s_ = float((q - a) @ t)
                off = abs(float((q - a) @ np.array([t[1], -t[0]])))
                if off < 0.05 and 0.05 < s_ < np.linalg.norm(b - a) - 0.05:
                    if all(np.linalg.norm(q - np.asarray(p_)) > 0.5 for p_, _ in cuts):
                        cuts.append((tuple(q), (t[1], -t[0])))
    if away is not None:
        d = np.asarray(away, float) / np.linalg.norm(away)
        cuts.append((tuple(c + d * (wall - 3.0)), tuple(d)))
    return cuts


def add_level(kit, rings, prefix, group, min_vol=2.0):
    """Add a level's rings to ``kit`` as at most two parts, each printing in one pose with at
    most one filament change: the upright rings (frieze, course) as ``prefix-lower`` and the
    upside-down ones (bed, crown) as ``prefix-upper``. Two rings of one colour make a
    one-colour part; a pose with a single ring keeps that ring's name. A ring cut into pieces
    (round a tower) gives one part per piece, ``-0``, ``-1``, ... Colour zones go to the
    renders; the change height is counted in the print pose (upright: from the lower ring's
    foot; upside down: from the crown's top)."""
    from .kit import print_flip
    added = []
    for flip in (False, True):
        grp = sorted([r for r in rings if r["flip"] == flip], key=lambda r: r["z0"])
        if not grp:
            continue
        # at most two rings per part and one change: split a longer run (not used by any spec)
        runs = [grp[i:i + 2] for i in range(0, len(grp), 2)]
        for run in runs:
            name = run[0]["name"] if len(run) == 1 else ("upper" if flip else "lower")
            solid = union([r["solid"] for r in run]) if len(run) > 1 else run[0]["solid"]
            first = run[-1] if flip else run[0]           # the ring printed first (on the bed)
            second = [r for r in run if r is not first]
            change = None
            if second and second[0]["role"] != first["role"]:
                change = (round((first["z1"] - first["z0"]) / 0.2) * 0.2, second[0]["role"])
            pcs = sorted([p_ for p_ in solid.decompose() if p_.volume() > min_vol], key=lambda m_: -m_.volume())
            for j, pc in enumerate(pcs):
                nm = f"{prefix}-{name}" + (f"-{j}" if len(pcs) > 1 else "")
                zones = None
                if change is not None:
                    bb = pc.bounding_box()
                    zones = [(r["role"], pc ^ box([bb[0] - 1, bb[1] - 1, r["z0"] - (10.0 if r is run[0] else 0.0)],
                                                   [bb[3] + 1, bb[4] + 1, r["z1"] + (10.0 if r is run[-1] else 0.0)]))
                             for r in run]
                added.append(kit.add(nm, first["role"], pc, P=print_flip() if flip else None, group=group,
                                     render=zones, change=change))
    return added


def band_height(spec):
    return sum(L_["h"] for L_ in spec["layers"])


def signature(spec):
    """A level's design, for the collection's uniqueness table: each layer's kind, ornament
    (or bracket style) and colour slot."""
    out = []
    for L_ in spec["layers"]:
        orn = L_.get("orn") or (L_.get("brackets") or {}).get("style", "-")
        out.append(f"{L_['kind']}:{orn}")
    return " / ".join(out)


def specs_of(module):
    """Every cornice level spec a building module defines (module-level dicts with layers)."""
    return {k: v for k, v in vars(module).items() if isinstance(v, dict) and "layers" in v}

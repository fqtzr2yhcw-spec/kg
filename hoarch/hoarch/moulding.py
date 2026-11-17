"""Sculpted mouldings and carved ornament for trim that prints face-up.

A moulding is a height profile across a band that follows an outline: a casing round an
opening, a hood over an arch, a pediment's cornice. It is built as a height field. At every
0.2 mm level, the part of the band that stands at least that high is found with offsets of the
outline and extruded one layer. The relief then prints as clean nested perimeters with every
flat on the layer grid, and a rounded profile reads as a carved bead, ogee or cove instead of a
stack of flat strips. Each level is cleaned of anything narrower than a nozzle width, so no
ridge prints as a hairline.

Profiles are [(t, h)]: t runs 0 -> 1 across the band from its outer edge to its inner edge,
h is the height (mm) above the band's base plane.
"""
import math

import numpy as np
from manifold3d import CrossSection as CS, JoinType, Manifold as M

from .core import RIB, SLOT, circle, cs_union, poly, rect, union
from .ornament import bezier, ext, stroke, volute

LAYER = 0.2
MIN_RIB = 0.5


def _clean(cs, rib=MIN_RIB):
    if cs.is_empty():
        return cs
    return cs.offset(-rib / 2 + 0.01, JoinType.Miter, 4.0).offset(rib / 2 - 0.01, JoinType.Miter, 4.0)


def band(outer, width, profile, w0=0.0, join=JoinType.Miter, samples=160, clip=None):
    """A moulded band following ``outer`` inward for ``width`` mm with the height ``profile``.
    ``clip``: a CrossSection the band is limited to (e.g. to stop a hood at its spring line)."""
    ts = np.linspace(0.0, 1.0, samples + 1)
    pt, ph = zip(*profile)
    hs = np.interp(ts, pt, ph)
    n = int(round(max(hs) / LAYER))
    rings = {}

    def ring(t0, t1):
        key = (round(t0, 4), round(t1, 4))
        if key not in rings:
            a = outer if t0 <= 1e-9 else outer.offset(-t0 * width, join, 4.0)
            b = outer.offset(-t1 * width, join, 4.0)
            rings[key] = a - b
        return rings[key]
    out = []
    for k in range(n):
        thr = (k + 0.5) * LAYER
        mask = hs >= thr
        regs = []
        i = 0
        while i <= samples:
            if mask[i]:
                j = i
                while j + 1 <= samples and mask[j + 1]:
                    j += 1
                regs.append(ring(ts[i], min(1.0, ts[j] + 1.0 / samples)))
                i = j + 1
            else:
                i += 1
        if not regs:
            continue
        lvl = cs_union(regs)
        if clip is not None:
            lvl = lvl ^ clip
        lvl = _clean(lvl)
        if not lvl.is_empty():
            out.append(ext(lvl, w0 + k * LAYER, w0 + (k + 1) * LAYER))
    return union(out)


def run(u0, u1, v0, profile, h_band, w0=0.0, up=True, ends=None):
    """A straight moulding (a shelf, a cornice, a sill nose) along u from u0 to u1, its profile
    running across v: from v0 upward over h_band if ``up`` (t = 0 at v0), else downward.
    ``ends``: extra run of the top level past each end (a returned crown)."""
    ts = np.linspace(0.0, 1.0, 121)
    pt, ph = zip(*profile)
    hs = np.interp(ts, pt, ph)
    n = int(round(max(hs) / LAYER))
    out = []
    for k in range(n):
        thr = (k + 0.5) * LAYER
        mask = hs >= thr
        regs = []
        i = 0
        while i < len(ts):
            if mask[i]:
                j = i
                while j + 1 < len(ts) and mask[j + 1]:
                    j += 1
                a, b = ts[i] * h_band, min(1.0, ts[j] + 1 / 120) * h_band
                regs.append(rect(u0, v0 + a, u1, v0 + b) if up else rect(u0, v0 - b, u1, v0 - a))
                i = j + 1
            else:
                i += 1
        if regs:
            lvl = _clean(cs_union(regs))
            if not lvl.is_empty():
                out.append(ext(lvl, w0 + k * LAYER, w0 + (k + 1) * LAYER))
    return union(out)


# ------------------------------------------------------------------ profiles
# Architrave (casing) round an opening, ~2 mm wide: a raised back band with a rounded
# shoulder at the outer edge, a flat fascia, and a bead at the opening.
ARCHITRAVE = [(0.0, 1.2), (0.26, 1.2), (0.34, 1.0), (0.42, 0.8), (0.46, 0.6), (0.7, 0.6), (0.76, 0.8),
              (1.0, 0.8)]
# Slimmer casing (~1.5 mm): back band and fascia.
CASING = [(0.0, 1.0), (0.38, 1.0), (0.46, 0.8), (0.52, 0.6), (1.0, 0.6)]
# Hood / cornice crown seen face-up: the drip edge stands highest at the outer edge, then an
# ogee falls toward the wall.
CROWN = [(0.0, 1.8), (0.24, 1.8), (0.34, 1.6), (0.46, 1.4), (0.58, 1.2), (0.7, 1.2), (0.8, 1.0), (1.0, 1.0)]
# Sill nose: a rounded projecting nose, the top wash falling back to the casing.
SILL = [(0.0, 1.2), (0.3, 1.4), (0.55, 1.4), (0.75, 1.2), (1.0, 1.0)]
# Bed moulding under a cornice or shelf: a small cove.
BED = [(0.0, 1.0), (0.4, 0.8), (1.0, 0.6)]


# ------------------------------------------------------------------ carved ornament
def cartouche(c, w, h, w0, d=1.2):
    """Oval shield in a scrolled frame: a raised rim, a sunk field with a boss, and a small
    scroll curling out at each side."""
    u, v = c
    ov = _oval(u, v, w / 2, h / 2)
    rim = ov - _oval(u, v, w / 2 - 0.55, h / 2 - 0.55)
    parts = [ext(ov, w0, w0 + d - 0.4), ext(rim, w0 + d - 0.4 - 0.01, w0 + d)]
    parts.append(ext(_oval(u, v, max(0.45, w / 2 - 1.3), max(0.5, h / 2 - 1.3)), w0 + d - 0.4 - 0.01, w0 + d - 0.2))
    for sg in (-1, 1):
        vo = volute((u + sg * (w / 2 + 0.35), v + 0.1), 0.75, turns=0.8, band=0.5, gap=SLOT,
                    a0=math.pi / 2, sense=-sg)
        parts.append(ext(vo, w0, w0 + d - 0.4))
    return union(parts)


def _oval(u, v, rx, ry, seg=40):
    return poly([(u + rx * math.cos(2 * math.pi * k / seg), v + ry * math.sin(2 * math.pi * k / seg))
                 for k in range(seg)])


def anthemion(c, w, h, w0, d=1.2, petals=5):
    """Palmette crest standing on (u, v): petals fanning up from a scrolled base, the middle
    petal tallest. Drawn as flat petals (>= a nozzle wide) on a base, two relief levels."""
    u, v = c
    parts_lo, parts_hi = [], []
    base = cs_union([rect(u - w / 2, v, u + w / 2, v + 0.6),
                     circle((u - w / 2 + 0.45, v + 0.6), 0.45, 16), circle((u + w / 2 - 0.45, v + 0.6), 0.45, 16)])
    parts_lo.append(base)
    for k in range(petals):
        a = math.pi / 2 + (k - (petals - 1) / 2) * (math.pi * 0.62 / max(1, petals - 1))
        L = (h - 0.6) * (1.0 - 0.28 * abs(k - (petals - 1) / 2) / max(1, (petals - 1) / 2))
        root = np.array([u, v + 0.6])
        tip = root + L * np.array([math.cos(a), math.sin(a)])
        nrm = np.array([-math.sin(a), math.cos(a)])
        wid = 0.34 if petals > 5 else 0.4
        mid = root + 0.62 * (tip - root)
        leaf = poly([tuple(root + nrm * 0.26), tuple(mid + nrm * wid), tuple(tip), tuple(mid - nrm * wid),
                     tuple(root - nrm * 0.26)])
        (parts_hi if k == (petals - 1) // 2 else parts_lo).append(leaf)
    lo = cs_union(parts_lo)
    out = [ext(lo, w0, w0 + d - 0.4)]
    if parts_hi:
        out.append(ext(cs_union(parts_hi), w0, w0 + d))
    out.append(ext(circle((u, v + 0.6), 0.5, 16), w0, w0 + d))
    return union(out)


def scroll_keystone(u, v0, h, wb, wt, w0, d=1.8):
    """Keystone whose face carries a raised vertical scroll (a console seen from the front):
    the stone stands d proud, the scroll another 0.4, curling at top and bottom."""
    stone = poly([(u - wb / 2, v0), (u + wb / 2, v0), (u + wt / 2, v0 + h), (u - wt / 2, v0 + h)])
    sc = cs_union([stroke([(u, v0 + 0.55), (u, v0 + h - 0.6)], 0.55),
                   circle((u, v0 + h - 0.6), min(0.5, wt * 0.3), 16), circle((u, v0 + 0.5), min(0.42, wb * 0.3), 16)])
    return union([ext(stone, w0, w0 + d - 0.4), ext(stone.offset(-0.2, JoinType.Miter, 4.0), w0 + d - 0.4 - 0.01, w0 + d - 0.2),
                  ext(sc ^ stone.offset(-0.2, JoinType.Miter, 4.0), w0 + d - 0.2 - 0.01, w0 + d + 0.2)])


def pendant(u, v_top, length, w0, d=0.8):
    """Turned drop hanging from v_top: a neck, a ball and a point."""
    r = 0.5
    cs = cs_union([rect(u - 0.3, v_top - length + 2 * r, u + 0.3, v_top),
                   circle((u, v_top - length + r * 1.4), r, 20),
                   poly([(u - 0.3, v_top - length + r), (u + 0.3, v_top - length + r), (u, v_top - length)])])
    return ext(cs, w0, w0 + d)


def rosette(u, v, r, w0, d=1.0, petals=6):
    """Carved rosette: a disc, a ring of petals raised on it, and a boss."""
    disc = circle((u, v), r, 32)
    pet = []
    for k in range(petals):
        a = 2 * math.pi * k / petals
        c = (u + r * 0.55 * math.cos(a), v + r * 0.55 * math.sin(a))
        pet.append(circle(c, max(0.28, r * 0.3), 12))
    return union([ext(disc, w0, w0 + d - 0.4), ext(cs_union(pet) ^ disc, w0 + d - 0.4 - 0.01, w0 + d - 0.2),
                  ext(circle((u, v), max(0.3, r * 0.3), 16), w0 + d - 0.4 - 0.01, w0 + d)])

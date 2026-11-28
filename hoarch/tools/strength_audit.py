"""Weak connections in scenery packs and flatcar loads: every piece in its print orientation.

  contact   area touching the plate, and its share of the piece's shadow on the plate. The pony
            truss's floor-beam bundle touched with 162 mm2 (28 %) and its ends lifted, brim or not.
  tall      height over the narrowest width of what touches the plate (its convex hull). Over 1, the
            piece stands taller than its base is wide: it levers its ends up as it cools, and the
            nozzle can knock it over. The floor-beam bundle was 1.8.
  neck      the smallest layer, as a share of the biggest layer above it, where at least NECK_H mm
            of the piece stands on it: a big part on a small join (the beams on three timber tops,
            13 %). Low shares are where a print snaps or peels at a colour change.
  thin      material narrower than two lines of the nozzle (0.8 mm for the 0.4 nozzle, 0.4 mm for the
            loads made for the 0.2: an opening of each layer by one nozzle width), mm3: the slicer
            drops it or draws one wobbly line, and whatever stands on it hangs in the air.
  floating  patches of a layer with nothing under them (Bambu Studio's "floating regions").

A piece is flagged when tall > 1.2 with under half its shadow on the plate; contact < 40 mm2 under a
piece over 5 mm tall that is slender (tall > 2) or touches with under 70 % of its shadow (a drum
standing on its whole base is not weak); a neck under 15 % in the bottom 4 mm (the join to the
base, the dunnage or the stand; a lamp's lantern on its shaft is the design, and its shaft is checked
by thin); or any floating region. Thin is listed for review.

usage: python3 tools/strength_audit.py [pack ...]     (no packs: all of them)
"""
import math
import sys

import numpy as np

import _common  # noqa: F401  (puts the project on the path)
from manifold3d import JoinType
from hoarch.lint import floating
from hoarch.packs import PACKS
from hoarch.loadnames import NOZZLE, LAYER as LAYERS

LAYER = 0.2
NECK_H = 3.0
LOW_NECK_Z = 4.0


def min_width(cs):
    """Narrowest width of a cross-section's convex hull (rotating calipers over its edges)."""
    pts = np.array([p for poly in cs.hull().to_polygons() for p in poly])
    if len(pts) < 3:
        return 0.0
    best = math.inf
    for i in range(len(pts)):
        e = pts[(i + 1) % len(pts)] - pts[i]
        n = np.hypot(*e)
        if n < 1e-9:
            continue
        nrm = np.array([-e[1], e[0]]) / n
        d = pts @ nrm
        best = min(best, d.max() - d.min())
    return best


def audit(m, layer=LAYER, nozzle=0.4):
    b = m.bounding_box()
    m = m.translate([0, 0, -b[2]])
    H = b[5] - b[2]
    foot = m.slice(0.1)
    contact = foot.area()
    shadow = m.project().area()
    tall = H / max(min_width(foot), 1e-6)
    zs = np.arange(layer / 2, H, layer)
    areas = np.array([m.slice(float(z)).area() for z in zs])
    neck, neck_z, low_neck = 1.0, None, 1.0
    for k in range(len(zs)):
        above = zs > zs[k] + 0.01
        if not above.any() or H - zs[k] < NECK_H:
            continue
        big = areas[above].max()
        r = areas[k] / big if big > 1e-6 else 1.0
        if r < neck:
            neck, neck_z = r, round(float(zs[k]), 2)
        if zs[k] < LOW_NECK_Z:
            low_neck = min(low_neck, r)
    thin = 0.0
    for z, a in zip(zs, areas):
        cs = m.slice(float(z))
        opened = cs.offset(-nozzle, JoinType.Miter).offset(nozzle, JoinType.Miter)
        thin += (a - opened.area()) * layer
    fl = floating(m, layer)
    return dict(H=H, contact=contact, frac=contact / max(shadow, 1e-6), tall=tall, neck=neck, neck_z=neck_z, low_neck=low_neck,
                thin=thin, floating=len(fl))


def flagged(a):
    why = []
    if a["tall"] > 1.2 and a["frac"] < 0.5:
        why.append("tall")
    if a["contact"] < 40.0 and a["H"] > 5.0 and (a["tall"] > 2.0 or a["frac"] < 0.7):
        why.append("contact")
    if a["low_neck"] < 0.15:
        why.append("neck")
    if a["floating"]:
        why.append("floating")
    return why


def main(keys):
    nflag = 0
    for k in keys:
        for pc in PACKS[k]["pieces"]:
            a = audit(pc["fn"](), LAYERS.get(k, LAYER), NOZZLE.get(k, 0.4))
            why = flagged(a)
            nflag += bool(why)
            print(f"{'!!' if why else '  '} {k:13s} {pc['name']:26s} H {a['H']:5.1f}  contact {a['contact']:7.1f} mm2 "
                  f"({a['frac'] * 100:3.0f} %)  tall {a['tall']:4.2f}  neck {a['neck'] * 100:3.0f} % at {a['neck_z']}  "
                  f"thin {a['thin']:6.1f}  float {a['floating']}  {' '.join(why)}", flush=True)
    print(f"pieces flagged: {nflag}")
    return nflag


if __name__ == "__main__":
    sys.exit(1 if main(sys.argv[1:] or list(PACKS)) else 0)

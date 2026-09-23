"""Printability lint: detail finer than the nozzle, measured in each part's print orientation.

FDM draws every layer with lines about one nozzle wide. Anything narrower than that in the
layer plane either vanishes (a thin rib, a hairline bead) or fuses shut (a joint between two
shingles, the gap between dentils). Texture that is only a few layers deep on an upward
facing surface is drawn by top-skin lines and reads as noise. Both show up here:

  * thin: ribs narrower than the nozzle (morphological opening of each layer),
  * gaps: slots narrower than the nozzle (morphological closing of each layer),

summed over the layers as volumes (mm^3). The Beaumont Rev B wall panels (face-up
fish-scale with 0.16 mm joints) are the case this was written against.
"""
import numpy as np
from manifold3d import JoinType

NOZZLE = 0.4
LAYER = 0.16


def layer_detail(cs, nozzle=NOZZLE):
    """(thin_area, gap_area) of one layer's cross-section."""
    if cs.is_empty():
        return 0.0, 0.0
    r = nozzle / 2 * 0.98
    a = cs.area()
    opened = cs.offset(-r, JoinType.Miter, 2.0).offset(r, JoinType.Miter, 2.0)
    closed = cs.offset(r, JoinType.Miter, 2.0).offset(-r, JoinType.Miter, 2.0)
    thin = max(0.0, a - (opened ^ cs).area())
    gaps = max(0.0, (closed - cs).area())
    return thin, gaps


def detail_lint(m, nozzle=NOZZLE, layer=LAYER):
    """Sub-nozzle detail of a printed-orientation manifold.

    Returns dict(thin=mm^3, gaps=mm^3, volume=mm^3, worst=[(z, thin_mm2, gap_mm2), ...])."""
    b = m.bounding_box()
    zs = np.arange(b[2] + layer / 2, b[5], layer)
    rows = []
    thin = gaps = 0.0
    for z in zs:
        t, g = layer_detail(m.slice(float(z)), nozzle)
        thin += t * layer
        gaps += g * layer
        rows.append((round(float(z - b[2]), 2), round(t, 2), round(g, 2)))
    rows.sort(key=lambda r: -(r[1] + r[2]))
    return dict(thin=round(thin, 2), gaps=round(gaps, 2), volume=round(m.volume(), 1), worst=rows[:3])


def lint_kit(kit, nozzle=NOZZLE, layer=LAYER, limit=0.5, only=None):
    """Lint every unique part of a Kit; returns rows sorted worst first and prints the ones over
    ``limit`` mm^3 of sub-nozzle detail."""
    out = []
    seen = set()
    for p in kit.parts:
        if p.key in seen or (only and not only(p)):
            continue
        seen.add(p.key)
        r = detail_lint(p.printed(), nozzle, layer)
        out.append((r["thin"] + r["gaps"], p.key, r))
    out.sort(key=lambda t: -t[0])
    bad = [o for o in out if o[0] > limit]
    print(f"detail lint (nozzle {nozzle} mm): {len(bad)} of {len(out)} designs over {limit} mm^3")
    for s, key, r in bad:
        print(f"  {key:44s} thin {r['thin']:7.2f}  gaps {r['gaps']:7.2f}  of {r['volume']:8.1f} mm^3   worst z {r['worst'][0]}")
    return out

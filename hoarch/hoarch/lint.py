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


def overhangs(m, layer=LAYER, allow=0.35, min_area=0.05):
    """Area printed over air, layer by layer, in print orientation: each layer minus the
    previous layer grown by ``allow`` (0.35 mm at 0.2 mm layers is Bambu Studio's default
    30 degree support threshold). Bridges between two supports show up here too; the
    rest is what a slicer would put support under.
    Returns dict(area=mm^2 total, spots=[(z, area, bounds), ...] largest first)."""
    b = m.bounding_box()
    prev = None
    spots = []
    for z in np.arange(b[2] + layer / 2, b[5], layer):
        cs = m.slice(float(z))
        if prev is not None and not cs.is_empty():
            hang = cs - prev.offset(allow, JoinType.Miter, 2.0)
            for d in hang.decompose():
                a = d.area()
                if a >= min_area:
                    spots.append((round(float(z - b[2]), 2), round(a, 2), [round(v, 1) for v in d.bounds()]))
        prev = cs
    spots.sort(key=lambda s: -s[1])
    return dict(area=round(sum(s[1] for s in spots), 1), spots=spots)


def overhang_kit(kit, layer=LAYER, allow=0.35, limit=1.0, only=None):
    """Print the unique parts that would need support (or bridge) at Bambu's default angle."""
    seen = set()
    rows = []
    for p in kit.parts:
        if p.key in seen or (only and not only(p)):
            continue
        seen.add(p.key)
        r = overhangs(p.printed(), layer, allow)
        rows.append((r["area"], p.key, r))
    rows.sort(key=lambda t: -t[0])
    bad = [r for r in rows if r[0] > limit]
    print(f"overhangs over {allow} mm per {layer} mm layer: {len(bad)} of {len(rows)} designs over {limit} mm^2")
    for a, key, r in bad:
        print(f"  {key:44s} {a:8.1f} mm^2   e.g. {r['spots'][:2]}")
    return rows

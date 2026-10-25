"""Print checks for a building, every unique part in its print orientation:

  detail     sub-nozzle detail (thin walls and gaps narrower than the 0.4 mm nozzle), listed
             when over 0.5 mm3;
  overhang   area printed over air at Bambu Studio's default support angle (bridges show up
             here too, and the windows and doors, which print on supports), over 1 mm2;
  mid-layer  flat faces that lie on a slicing plane, which make PrusaSlicer fail.

usage: python3 tools/printcheck.py <building> [...]
"""
import sys
import time

from _common import building
from hoarch.lint import detail_lint, midlayer_faces, overhangs


def check(key):
    kit = building(key).build()
    t0 = time.time()
    seen, designs = set(), []
    for p in kit.parts:
        if p.key in seen:
            continue
        seen.add(p.key)
        designs.append((p.key, p.printed()))
    det, ovh, mid = [], [], []
    for k, m in designs:
        d = detail_lint(m)
        if d["thin"] + d["gaps"] > 0.5:
            det.append((d["thin"] + d["gaps"], k, d))
        o = overhangs(m)
        if o["area"] > 1.0:
            ovh.append((o["area"], k, o))
        a, zs = midlayer_faces(m)
        if a > 0.0:
            mid.append((a, k, zs))
    print(f"checked {len(designs)} designs in {time.time() - t0:.1f} s")
    print("-- detail (thin+gaps > 0.5 mm3)")
    for _, k, d in sorted(det, key=lambda r: -r[0]):
        print(f"  {k:40s} thin {d['thin']:6.2f} gaps {d['gaps']:6.2f} of {d['volume']:9.1f}")
    print("-- overhang (> 1 mm2)")
    for a, k, o in sorted(ovh, key=lambda r: -r[0]):
        print(f"  {k:40s} {a:9.1f}  {o['spots'][:2]}")
    print("-- mid-layer flat faces")
    for a, k, zs in sorted(mid, key=lambda r: -r[0]):
        print(f"  {k:40s} {a:9.3f} mm2 at {zs}")


if __name__ == "__main__":
    for key in sys.argv[1:]:
        check(key)

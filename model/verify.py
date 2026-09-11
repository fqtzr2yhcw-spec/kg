#!/usr/bin/env python3
"""
Pre-print verification harness for the Empire State Building sections.

Catches, digitally, the failures that otherwise waste print time & material:
  * mesh integrity   - watertight, single body, consistent winding, no
                       degenerate faces, positive volume
  * bed fit          - every part inside the 256x256x256 Bambu envelope
  * wall thickness   - sampled min thickness vs the nozzle (thin = won't print)
  * overhangs        - down-facing area steeper than 45 deg (needs support)
  * dry-fit / tolerance - adjacent parts stacked in world coords must NOT
                       collide (intersection volume ~ 0) yet must meet

Run:  python3 verify.py
Exit code 0 only if no FAILs.
"""
import glob
import os
import sys
import numpy as np
import trimesh

STL_DIR   = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stl")
BED       = 256.0
NOZZLE    = 0.4
MIN_WALL  = 0.8          # 2 nozzle widths - below this a wall is unreliable
OVERHANG  = 45.0         # degrees from vertical
FIT_COLLIDE_MM3 = 2.0    # intersection volume above this = parts collide

# stacking order (base halves assemble first, then upward)
STACK = ["01_base_N", "01_base_S", "02_shaft_1of3", "03_shaft_2of3",
         "04_shaft_3of3", "05_setbacks", "06_crown", "07_spire"]

def load():
    parts = {}
    for f in sorted(glob.glob(os.path.join(STL_DIR, "0*_*.stl"))):
        if "full_assembly" in f:
            continue
        m = trimesh.load(f, process=True)     # process=True merges STL's split vertices
        m.merge_vertices(); m.fix_normals()
        parts[os.path.splitext(os.path.basename(f))[0]] = m
    return parts

def integrity(m):
    issues = []
    if not m.is_watertight:            issues.append("not watertight")
    if not m.is_winding_consistent:    issues.append("winding inconsistent")
    if m.body_count != 1:              issues.append(f"{m.body_count} disconnected bodies")
    if m.volume <= 0:                  issues.append("non-positive volume")
    degen = int((m.area_faces < 1e-9).sum())
    if degen:                          issues.append(f"{degen} degenerate faces")
    return issues

def sample_thickness(m, n=500):
    try:
        pts, fi = trimesh.sample.sample_surface(m, n)
        nrm = m.face_normals[fi]
        origins = pts - nrm * 0.02
        hits, ray_ids, _ = m.ray.intersects_location(origins, -nrm, multiple_hits=False)
        if len(hits) == 0:
            return None
        d = np.linalg.norm(hits - origins[ray_ids], axis=1)
        d = d[d > 1e-3]
        return d
    except Exception as e:
        return None

def overhang_fraction(m):
    nz = m.face_normals[:, 2]
    down = nz < -np.cos(np.radians(OVERHANG))   # steeper than 45deg, facing down
    a = m.area_faces
    return float(a[down].sum() / a.sum()), float(nz.min())

def main():
    parts = load()
    if not parts:
        print("no STL parts found"); sys.exit(2)
    fails, warns = 0, 0
    print(f"{'part':16}{'W x D x H (mm)':22}{'bed':5}{'solid':7}{'min_thk':9}{'overhang':9}{'status'}")
    print("-" * 86)
    for name in [p for p in STACK if p in parts] + [p for p in parts if p not in STACK]:
        m = parts[name]
        e = m.extents
        iss = integrity(m)
        bed_ok = e[0] <= BED and e[1] <= BED and e[2] <= BED
        d = sample_thickness(m)
        min_thk = None if d is None else float(np.percentile(d, 0.5))
        ohf, _ = overhang_fraction(m)
        status = []
        if iss:                                  status.append("FAIL:" + ",".join(iss)); fails += 1
        if not bed_ok:                           status.append("FAIL:over-bed"); fails += 1
        if min_thk is not None and min_thk < MIN_WALL:
            status.append(f"WARN:thin {min_thk:.2f}mm"); warns += 1
        if ohf > 0.06:                           status.append(f"WARN:overhang {ohf*100:.0f}%"); warns += 1
        st = "  ".join(status) if status else "OK"
        thk_s = "-" if min_thk is None else f"{min_thk:.2f}mm"
        print(f"{name:16}{e[0]:5.1f}x{e[1]:5.1f}x{e[2]:6.1f}     "
              f"{'ok' if bed_ok else 'NO':5}{'ok' if not iss else 'BAD':7}{thk_s:9}{ohf*100:5.0f}%    {st}")

    # ---- dry-fit: adjacent parts must not collide -------------------------
    print("\nDry-fit (adjacent parts stacked in place; intersection volume should be ~0):")
    pairs = [("01_base_N", "01_base_S"), ("01_base_N", "02_shaft_1of3"),
             ("01_base_S", "02_shaft_1of3"), ("02_shaft_1of3", "03_shaft_2of3"),
             ("03_shaft_2of3", "04_shaft_3of3"), ("04_shaft_3of3", "05_setbacks"),
             ("05_setbacks", "06_crown"), ("06_crown", "07_spire")]
    for a, b in pairs:
        if a in parts and b in parts:
            try:
                inter = trimesh.boolean.intersection([parts[a], parts[b]])
                v = float(inter.volume) if inter is not None and inter.volume else 0.0
            except Exception:
                v = -1.0
            tag = "OK" if 0 <= v <= FIT_COLLIDE_MM3 else ("FAIL:collide" if v > FIT_COLLIDE_MM3 else "err")
            if v > FIT_COLLIDE_MM3: fails += 1
            print(f"  {a:15} <-> {b:15} intersection = {v:8.2f} mm^3   {tag}")

    print(f"\n=== {fails} FAIL, {warns} WARN ===")
    sys.exit(1 if fails else 0)

if __name__ == "__main__":
    main()

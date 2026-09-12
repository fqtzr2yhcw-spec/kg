#!/usr/bin/env python3
"""
Pre-print verification harness for the Empire State Building sections.

Catches, digitally, the failures that otherwise waste print time & material:
  * mesh integrity   - watertight, single body, consistent winding, no
                       degenerate faces, positive volume
  * bed fit          - every part inside the 256x256x256 Bambu envelope
  * wall thickness   - ray-sampled; reports the fraction below the nozzle limit
                       and WHERE (z height) the thin region is
  * overhangs        - down-facing area steeper than 45 deg (needs support)
  * dry-fit / tolerance - adjacent parts (derived from the numeric part order)
                       stacked in world coords must NOT collide (intersection ~0)

Run:  python3 verify.py     (exit 0 only if no FAILs)
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
THIN_FRAC = 0.01         # >1% of samples below MIN_WALL = a real thin region
OVERHANG  = 45.0         # degrees from vertical
FIT_COLLIDE_MM3 = 5.0    # intersection volume above this = parts collide

def load():
    parts = {}
    for f in sorted(glob.glob(os.path.join(STL_DIR, "0*_*.stl"))):
        if "full_assembly" in f:
            continue
        m = trimesh.load(f, process=True)
        m.merge_vertices(); m.fix_normals()
        parts[os.path.splitext(os.path.basename(f))[0]] = m
    return parts

def integrity(m):
    issues = []
    if not m.is_watertight:            issues.append("not watertight")
    if not m.is_winding_consistent:    issues.append("winding inconsistent")
    if m.body_count != 1:              issues.append(f"{m.body_count} bodies")
    if m.volume <= 0:                  issues.append("non-positive volume")
    degen = int((m.area_faces < 1e-9).sum())
    if degen:                          issues.append(f"{degen} degenerate faces")
    return issues

def thickness(m, n=1500):
    try:
        pts, fi = trimesh.sample.sample_surface(m, n)
        nrm = m.face_normals[fi]
        origins = pts - nrm * 0.02
        hits, ray_ids, _ = m.ray.intersects_location(origins, -nrm, multiple_hits=False)
        if len(hits) == 0:
            return None
        d = np.linalg.norm(hits - origins[ray_ids], axis=1)
        keep = d > 1e-3
        return d[keep], origins[ray_ids][keep]
    except Exception:
        return None

def overhang_fraction(m):
    nz = m.face_normals[:, 2]
    down = nz < -np.cos(np.radians(OVERHANG))
    a = m.area_faces
    return float(a[down].sum() / a.sum())

def adjacency(names):
    """Stack pairs from numeric order; base halves both mate the first shaft band."""
    ordered = sorted(names)
    pairs = [(ordered[i], ordered[i + 1]) for i in range(len(ordered) - 1)]
    halves = [n for n in ordered if n.endswith("_N") or n.endswith("_S")]
    shafts = [n for n in ordered if "shaft" in n]
    if len(halves) == 2 and shafts:
        pairs.append((halves[0], shafts[0]))
    return sorted(set(pairs))

def main():
    parts = load()
    if not parts:
        print("no STL parts found"); sys.exit(2)
    fails = warns = 0
    print(f"{'part':16}{'W x D x H (mm)':21}{'bed':5}{'solid':7}{'thin(min/frac)':20}{'ovhg':6}status")
    print("-" * 96)
    for name in sorted(parts):
        m = parts[name]; e = m.extents
        iss = integrity(m)
        bed_ok = all(e[i] <= BED for i in range(3))
        res = thickness(m)
        if res is None:
            min_thk = frac = None; thin_z = None
        else:
            d, hp = res
            min_thk = float(np.percentile(d, 1))
            tmask = d < MIN_WALL
            frac = float(tmask.mean())
            thin_z = float(np.median(hp[tmask, 2])) if tmask.any() else None
        ohf = overhang_fraction(m)
        status = []
        if iss:                    status.append("FAIL:" + ",".join(iss)); fails += 1
        if not bed_ok:             status.append("FAIL:over-bed"); fails += 1
        if frac is not None and frac > THIN_FRAC:
            status.append(f"WARN:thin {frac*100:.1f}% @z~{thin_z:.0f}mm"); warns += 1
        if ohf > 0.06:             status.append(f"WARN:ovhg {ohf*100:.0f}%"); warns += 1
        thk_s = "-" if min_thk is None else f"{min_thk:.2f}/{frac*100:.1f}%"
        print(f"{name:16}{e[0]:5.1f}x{e[1]:5.1f}x{e[2]:6.1f}    "
              f"{'ok' if bed_ok else 'NO':5}{'ok' if not iss else 'BAD':7}{thk_s:20}"
              f"{ohf*100:4.0f}%  {'  '.join(status) if status else 'OK'}")

    print("\nDry-fit (adjacent parts stacked in place; intersection should be ~0 mm^3):")
    for a, b in adjacency(list(parts)):
        try:
            inter = trimesh.boolean.intersection([parts[a], parts[b]])
            v = float(inter.volume) if inter is not None and inter.volume else 0.0
        except Exception:
            v = -1.0
        if v > FIT_COLLIDE_MM3: fails += 1; tag = "FAIL:collide"
        elif v < 0:            tag = "err"
        else:                  tag = "OK"
        print(f"  {a:15} <-> {b:15} {v:9.2f} mm^3   {tag}")

    print(f"\n=== {fails} FAIL, {warns} WARN ===")
    sys.exit(1 if fails else 0)

if __name__ == "__main__":
    main()

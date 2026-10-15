"""Assembly-guide renders: cumulative build steps and an exploded view.

usage: python3 kit_render.py [--samples N] [--res WxH] [--out DIR] [--only steps|exploded|hero]
"""
import argparse
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kit  # noqa: E402

STEPS = [
    ("Foundation & water table", [r"FOUNDATION", r"TRIM-water-table"]),
    ("First-floor walls, tower base, doors & windows",
     [r"WALL-W\d-lower", r"TOWER-lower", r"corner-board-\d-lower", r"WIN-W\d-lower", r"DOOR-", r"WIN-tower-lower"]),
    ("Belt loops & second floor",
     [r"belt-loop", r"TOWER-belt-ring-z2", r"WALL-W\d-upper", r"TOWER-upper", r"corner-board-\d-upper",
      r"WIN-W\d-upper", r"WIN-tower-upper", r"gable-band"]),
    ("Bay window & exterior chimney", [r"BAY-", r"WIN-bay", r"CHIMNEY-exterior", r"ROOF-bay"]),
    ("Cornice rings", [r"CORNICE-main", r"TOWER-belt-ring-ze", r"TOWER-cornice"]),
    ("Roofs, spire, dormer & gable trim",
     [r"ROOF-main", r"CHIMNEY-interior", r"ROOF-tower-spire", r"GABLE-", r"DORMER-", r"WIN-dormer",
      r"ROOF-dormer", r"ridge-cresting"]),
    ("Wraparound porch", [r"PORCH-", r"ROOF-porch"]),
    ("Back stoop, hood & downspouts", [r"BACK-", r"back-door-hood", r"DOWNSPOUT"]),
]

EXPLODE = {0: (0, 0, 0), 1: (0, 0, 0), 2: (0, 0, 28), 3: (0, -30, 0), 4: (0, 0, 55), 5: (0, 0, 85),
           6: (-35, -45, 0), 7: (0, 30, 0)}


def step_of(name):
    for i, (_, pats) in enumerate(STEPS):
        if any(re.search(p, name) for p in pats):
            return i
    return None


def export(parts_with_offsets, path):
    from collections import defaultdict
    groups = defaultdict(list)
    for p, off in parts_with_offsets:
        groups[kit.RENDER_MAT[p.color]].append(p.solid.translate(list(off)))
    data = {}
    for mat, ms in groups.items():
        vs, fs, o = [], [], 0
        for m in ms:
            mesh = m.to_mesh()
            v = np.asarray(mesh.vert_properties)[:, :3]
            f = np.asarray(mesh.tri_verts)
            vs.append(v)
            fs.append(f + o)
            o += len(v)
        data[mat + "__v"] = np.concatenate(vs).astype(np.float32)
        data[mat + "__f"] = np.concatenate(fs).astype(np.int32)
    np.savez_compressed(path, **data)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--samples", type=int, default=32)
    ap.add_argument("--res", default="1000x700")
    ap.add_argument("--out", default=os.path.join(HERE, "..", "kit", "renders"))
    ap.add_argument("--only", default="steps,exploded")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    kit.build()
    missing = [p.name for p in kit.PARTS if step_of(p.name) is None]
    if missing:
        print("parts not in any step:", missing)
    tmp = os.path.join(HERE, "..", "out")
    os.makedirs(tmp, exist_ok=True)
    jobs = []
    if "steps" in args.only:
        for i in range(len(STEPS)):
            sel = [(p, (0, 0, 0)) for p in kit.PARTS if step_of(p.name) is not None and step_of(p.name) <= i]
            npz = os.path.join(tmp, f"step{i + 1}.npz")
            export(sel, npz)
            jobs.append((npz, f"step{i + 1}", "hero"))
    if "exploded" in args.only:
        sel = [(p, EXPLODE[step_of(p.name)]) for p in kit.PARTS if step_of(p.name) is not None]
        npz = os.path.join(tmp, "exploded.npz")
        export(sel, npz)
        jobs.append((npz, "exploded", "hero"))
    import subprocess
    allb = np.array([p.solid.bounding_box() for p in kit.PARTS])
    full = list(allb[:, :3].min(0)) + list(allb[:, 3:].max(0))
    for npz, name, view in jobs:
        extra = [] if name == "exploded" else ["--bbox=" + ",".join(f"{v:.2f}" for v in full)]
        sub = os.path.join(args.out, "_tmp_" + name)
        subprocess.run([sys.executable, os.path.join(HERE, "render.py"), "--npz", npz, "--samples", str(args.samples),
                        "--res", args.res, "--views", view, "--out", sub] + extra, check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.replace(os.path.join(sub, view + ".png"), os.path.join(args.out, name + ".png"))
        os.rmdir(sub)
        print("rendered", name, flush=True)


if __name__ == "__main__":
    main()

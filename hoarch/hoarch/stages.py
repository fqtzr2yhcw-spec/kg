"""Build-stage renders for the build guides.

Builds a model and renders it part-way through assembly from the hero camera, framed on the
finished model so the pictures line up:

  step1  the foundation and the first storey (its walls, windows and doors)
  step2  every storey, with windows, doors, shutters, bays and cornices; no roofs
  step3  plus the porches, portico, balconies and steps (skipped when the model has none)

Writes out/<b>/steps/step1..3.png and steps.json (the captions).

    python3 -m hoarch.stages <building>... [--samples 24] [--res 1000x690]
"""
import argparse
import importlib
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "out"))

LATER = {"roof", "cupola", "top", "dormers", "extras", "street"}
OPEN = {"porch": "porch", "portico": "portico", "balcony": "balcony", "gallery": "gallery", "stoop": "steps",
        "boardwalk": "boardwalk"}
TOPS = re.compile(r"roof|finial|crest|spire|chimney|weathervane", re.I)


def base(group):
    return (group or "").split("-")[0]


def bbox(p):
    return p.solid.bounding_box()


def stage_sets(kit):
    parts = kit.parts
    walls = [p for p in parts if base(p.group) == "walls"] or [p for p in parts if base(p.group) in ("front", "storefront")]
    z_lo = min(bbox(p)[2] for p in walls)
    first = [p for p in walls if bbox(p)[2] <= z_lo + 3.0]
    z_top = max(bbox(p)[5] for p in first)
    s1 = {p.name for p in parts if base(p.group) == "foundation"} | {p.name for p in first}
    for p in parts:
        if base(p.group) in ("inserts", "shutters", "front", "storefront", "bay"):
            b = bbox(p)
            if (b[2] + b[5]) / 2 < z_top:
                s1.add(p.name)
    s2 = set(s1)
    for p in parts:
        g = base(p.group)
        if g not in LATER and g not in OPEN and not TOPS.search(p.name):
            s2.add(p.name)
    s3 = s2 | {p.name for p in parts if base(p.group) in OPEN}
    kinds = []
    for g, word in OPEN.items():
        if any(base(p.group) == g for p in parts) and word not in kinds:
            kinds.append(word)
    caps = ["The foundation and the first storey", "Every storey, with its windows, doors and cornices"]
    sets = [s1, s2]
    if s3 != s2:
        sets.append(s3)
        words = ", ".join(kinds[:-1]) + " and " + kinds[-1] if len(kinds) > 1 else kinds[0]
        caps.append(f"The {words} added")
    return sets, caps


def run(key, samples=24, res="1000x690"):
    mod = importlib.import_module("hoarch.buildings." + key)
    kit = mod.build()
    d = os.path.join(OUT, key)
    sd = os.path.join(d, "steps")
    os.makedirs(sd, exist_ok=True)
    lo = [1e9] * 3
    hi = [-1e9] * 3
    for p in kit.parts:
        for _, sol in (p.render or [(p.color, p.solid)]):
            if sol.is_empty():
                continue
            b = sol.bounding_box()
            lo = [min(lo[i], b[i]) for i in range(3)]
            hi = [max(hi[i], b[i + 3]) for i in range(3)]
    box = ",".join(f"{v:.2f}" for v in lo + hi)
    sets, caps = stage_sets(kit)
    pal = os.path.join(d, "palette.json")
    for k, names in enumerate(sets, 1):
        npz = os.path.join(sd, f"step{k}.npz")
        kit.render_npz(npz, only=lambda p, names=names: p.name in names)
        tmp = os.path.join(sd, f"_r{k}")
        cmd = [sys.executable, "-m", "hoarch.render", "--npz", npz, "--views", "hero", "--samples", str(samples),
               "--res", res, "--out", tmp, "--bbox=" + box]
        if os.path.exists(pal):
            cmd += ["--palette", pal]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, cwd=os.path.join(HERE, ".."))
        shutil.move(os.path.join(tmp, "hero.png"), os.path.join(sd, f"step{k}.png"))
        shutil.rmtree(tmp, ignore_errors=True)
        os.remove(npz)
        print(key, f"step{k}", len(names), "parts", flush=True)
    for k in range(len(sets) + 1, 4):
        if os.path.exists(os.path.join(sd, f"step{k}.png")):
            os.remove(os.path.join(sd, f"step{k}.png"))
    json.dump({"captions": caps}, open(os.path.join(sd, "steps.json"), "w"), indent=1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("buildings", nargs="+")
    ap.add_argument("--samples", type=int, default=24)
    ap.add_argument("--res", default="1000x690")
    a = ap.parse_args()
    for b in a.buildings:
        run(b, a.samples, a.res)


if __name__ == "__main__":
    main()

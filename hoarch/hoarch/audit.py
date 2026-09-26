"""Audit the houses against the owner's rules (``CLAUDE.md`` at the repo root): the ones that
can be measured from a building's module and its last check and export.

    python3 -m hoarch.audit [building ...]        (default: every house)

Per building it reports:
  size       the plan's long and short sides (a house should fill most of the 256 mm bed)
  windows    lights taller than 70% of their storey, and facade runs where the frames take more
             than half the wall (windows must not fill a storey or a wall)
  towers     tower and turret storeys with lights on more than half the faces, and lights
             under 6 mm wide (not too many, not tiny)
  cornices   a cornice at every level (a joint cornice on two-storey houses, an eave cornice),
             and none of its designs shared with another building
  colours    at most one colour change per part (from the export)
  skins      no fish-scale ("U") shingles, no picket fences
  fit        0 interfering part pairs and every part on the bed (from the last check)
Only the measurable rules are here; the rest (ornate, flowing, not generic) is for the eye.
"""
import importlib
import json
import os
import re
import sys
from collections import defaultdict

from hoarch import cornice as CO
from hoarch.core import cs_union

HOUSES = ["beaumont", "villa", "harcourt", "fowler", "whitby", "delancey", "ardmore", "merritt", "hollis", "carrow",
          "marigold", "primrose", "rosecroft", "twins", "larkspur", "juniper", "camellia", "wisteria", "hawthorn",
          "magnolia", "whitmore", "pennock", "oakhurst", "vantassel", "hathaway", "chatham", "westbrook"]
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "out")
BED = 256.0


def _openings(m):
    if hasattr(m, "OPENINGS"):
        return list(m.OPENINGS)
    if hasattr(m, "HALVES"):                       # the pair of row houses
        return [o for H in m.HALVES for o in H["openings"]]
    return []


def _blocks(m):
    if hasattr(m, "BLOCKS"):
        return list(m.BLOCKS)
    if hasattr(m, "HALVES"):
        return [b for H in m.HALVES for b in (H["main"], H["bay"])]
    return [m.MAIN]


def _specs(m):
    specs = CO.specs_of(m)
    for k, v in vars(m).items():                   # dicts of specs (the pair keeps one per house)
        if isinstance(v, dict) and v and all(isinstance(x, dict) and "layers" in x for x in v.values()):
            for kk, vv in v.items():
                specs[f"{k}[{kk}]"] = vv
    return specs


def _storey(m, z):
    """(name, height) of the storey a sill at absolute height z stands in, or None above the walls."""
    zf = m.ZF
    s1 = getattr(m, "S1", None)
    ze = getattr(m, "ZE", None)
    rj = getattr(m, "RJ", getattr(m, "RH", 0.0))
    if s1 is not None and z < s1:
        return "first", s1 - zf
    if s1 is not None and ze is not None and z < ze:
        return "second", ze - (s1 + rj)
    if s1 is None and ze is not None and z < ze:
        return "first", ze - zf
    return None


def audit(name, all_specs):
    m = importlib.import_module("hoarch.buildings." + name)
    rep = defaultdict(list)
    # --- size
    cs = cs_union([b.cs for b in _blocks(m)])
    bb = cs.bounds()
    w, d = bb[2] - bb[0], bb[3] - bb[1]
    rep["size"].append(f"plan {max(w, d):.0f} x {min(w, d):.0f} mm")
    if max(w, d) < 150.0:
        rep["FLAG"].append(f"size: long side {max(w, d):.0f} mm, under 150 (the house should fill the bed)")
    # --- windows and tower lights
    ops = [o for o in _openings(m) if o.kind == "window"]
    runs = defaultdict(dict)                       # (block, wall, storey) -> {u: frame width}
    tower_lights = defaultdict(list)
    tall = []
    for o in ops:
        cb = o.spec["cut"].bounds()
        lb = o.spec["landing"].bounds()
        z = o.block.z0 + o.v0
        st = _storey(m, z)
        if st is None:
            continue
        h = cb[3] - cb[1]
        zw = getattr(m, "ZW", getattr(m, "ZC", 1e9))
        if h > 0.7 * st[1] and z + h < zw:          # a gable light may run up past the eave
            tall.append(f"{o.name} {h:.0f}/{st[1]:.0f} mm")
        key = (o.block.name, o.edge, st[0])
        runs[key][round(o.u)] = max(runs[key].get(round(o.u), 0.0), lb[2] - lb[0])   # a transom over a sash counts once
        if any(t in o.block.name for t in ("tower", "turret")):
            tower_lights[(o.block.name, st[0] if st else "top")].append(cb[2] - cb[0])
    if tall:
        rep["FLAG"].append("windows taller than 70% of their storey: " + ", ".join(tall[:6]) +
                           (f" (+{len(tall) - 6})" if len(tall) > 6 else ""))
    full = []
    for (bn, e, st), ws in runs.items():
        wsum = sum(ws.values())
        blk = next(b for b in _blocks(m) if b.name == bn)
        L = blk.facades()[e].L
        if L > 30.0 and wsum > 0.5 * L and not bn.startswith("bay"):     # bay windows are glazed by design
            full.append(f"{bn} wall {e} ({st}): frames {wsum:.0f} of {L:.0f} mm")
    if full:
        rep["FLAG"].append("walls more than half window: " + "; ".join(full[:6]))
    n_win = len(ops)
    rep["windows"].append(f"{n_win} windows, max {max((sum(r.values()) for r in runs.values()), default=0):.0f} mm of "
                          "frames on one wall")
    # tower storeys: lights on more than half the faces, or tiny lights
    for b in _blocks(m):
        if not any(t in b.name for t in ("tower", "turret")):
            continue
        faces = len(b.pts)
        per = defaultdict(list)
        for o in ops:
            if o.block is b:
                per[round(o.v0)].append(o.spec["cut"].bounds()[2] - o.spec["cut"].bounds()[0])
        for v0, ws in sorted(per.items()):
            if len(ws) > faces / 2:
                rep["FLAG"].append(f"{b.name}: {len(ws)} lights on {faces} faces at +{v0} mm (more than half)")
            if min(ws) < 6.0:
                rep["FLAG"].append(f"{b.name}: lights {min(ws):.1f} mm wide at +{v0} mm (tiny)")
        rep["towers"].append(f"{b.name}: " + ", ".join(f"{len(ws)} lights at +{v0}" for v0, ws in sorted(per.items())))
    # --- cornices
    specs = _specs(m)
    keys = set(specs)
    two_storey = hasattr(m, "S1")
    if two_storey and not any(k.startswith("JOINT") for k in keys):
        rep["FLAG"].append("cornices: no joint cornice between the storeys")
    if not any(k.startswith(("EAVE", "FRIEZES")) for k in keys):
        rep["FLAG"].append("cornices: no eave cornice")
    rep["cornices"].append(", ".join(sorted(keys)))
    for k, sp in specs.items():
        sig = CO.signature(sp)
        others = [f"{b}.{kk}" for b, kk, s in all_specs if s == sig and b != name]
        if others:
            rep["FLAG"].append(f"cornice {k} repeats {', '.join(others)}")
        friezes = [L_["orn"] for L_ in sp["layers"] if L_["kind"] == "frieze"]
        for fr in friezes:
            users = sorted({b for b, kk, s in all_specs if b != name and f"frieze:{fr} " in s + " "})
            if users:
                rep["FLAG"].append(f"frieze '{fr}' also on {', '.join(users)}")
    # --- skins and fences (in the source)
    src = open(os.path.join(HERE, "buildings", name + ".py")).read()
    if re.search(r"shape\s*=\s*\"fish\"|texture\s*=\s*\"fish\"", src):
        rep["FLAG"].append("skins: fish-scale shingles")
    if re.search(r"picket_fence|picket fence|fence\(.*picket", src, re.I):
        rep["FLAG"].append("fences: a picket fence or skirt (no white picket fences)")
    # --- the last export and check
    man_p = os.path.join(OUT, name, "kit", "manifest.json")
    if os.path.exists(man_p):
        man = json.load(open(man_p))
        n_parts = sum(p["qty"] for p in man["parts"])
        changes = [p for p in man["plates"] if p.get("change")]
        big = [p["file"] for p in man["parts"] if max(p["size_mm"][:2]) > BED]
        rep["colours"].append(f"{n_parts} parts, {len(changes)} plates with one colour change")
        if big:
            rep["FLAG"].append("fit: parts bigger than the bed: " + ", ".join(big))
        if not any(p.get("change") is not None or "change" in p for p in man["plates"]):
            rep["colours"].append("(export predates colour-change parts)")
    else:
        rep["colours"].append("no export yet")
    logs = [os.path.join(OUT, name, "u", lg) for lg in ("final.log", "check.log")]
    logs = sorted([lp for lp in logs if os.path.exists(lp)], key=os.path.getmtime, reverse=True)
    found = False
    for lp in logs:                                 # the newest check wins
        mm = re.findall(r"interfering pairs: (\d+)", open(lp).read())
        if mm:
            stale = os.path.getmtime(lp) < os.path.getmtime(os.path.join(HERE, "buildings", name + ".py"))
            rep["fit"].append(f"{mm[-1]} interfering pairs ({os.path.basename(lp)})" +
                              (" - STALE, the building changed since" if stale else ""))
            if stale:
                rep["FLAG"].append("fit: no check since the building last changed")
            if int(mm[-1]):
                rep["FLAG"].append(f"fit: {mm[-1]} interfering pairs in the last {os.path.basename(lp)}")
            found = True
            break
    if not found:
        rep["fit"].append("not checked yet")
    return rep


def main(names):
    all_specs = []
    for n in HOUSES:
        m = importlib.import_module("hoarch.buildings." + n)
        for k, sp in _specs(m).items():
            all_specs.append((n, k, CO.signature(sp)))
    total = 0
    for n in names:
        rep = audit(n, all_specs)
        flags = rep.pop("FLAG", [])
        total += len(flags)
        print(f"== {n}: {'OK' if not flags else f'{len(flags)} flag(s)'}")
        for k in ("size", "windows", "towers", "cornices", "colours", "fit"):
            for line in rep.get(k, []):
                print(f"   {k:9s} {line}")
        for f in flags:
            print(f"   FLAG      {f}")
    print(f"\n{total} flag(s) in {len(names)} building(s)")


if __name__ == "__main__":
    main(sys.argv[1:] or HOUSES)

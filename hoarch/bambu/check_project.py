"""Check a generated Bambu Studio project against the rules Bambu Studio applies when it opens one
(bbs_3mf.cpp and PresetBundle::load_config_file_config): every reference resolves, every object sits
on its plate, and the settings' per-filament and per-nozzle lists line up.

    python3 bambu/check_project.py out/Ashby_Villa_P2S_v1.2.3mf
"""

import json
import math
import os
import re
import sys
import zipfile

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))


def check(path):
    P = json.load(open(os.path.join(HERE, "p2s_profiles.json")))
    L = P["option_lists"]
    z = zipfile.ZipFile(path)
    names = set(z.namelist())
    err = []
    ok = lambda c, m: c or err.append(m)
    model = z.read("3D/3dmodel.model").decode()
    ok("BambuStudio-" in model, "no BambuStudio application tag")
    for t in re.findall(r'Target="/([^"]+)"', z.read("_rels/.rels").decode() + z.read("3D/_rels/3dmodel.model.rels").decode()):
        ok(t in names, f"relationship target missing: {t}")
    objs = {}
    for m in re.finditer(r'<object id="(\d+)"[^>]*>\s*<components>\s*<component p:path="/([^"]+)" objectid="(\d+)"', model):
        oid, f, mid = m.groups()
        ok(f in names, f"component file missing {f}")
        sub = z.read(f).decode()
        ok(f'<object id="{mid}"' in sub, f"mesh {mid} not in {f}")
        v = np.array(re.findall(r'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"', sub), float)
        nt = len(re.findall(r"<triangle ", sub))
        tri = np.array(re.findall(r'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"', sub), int)
        ok(tri.max() < len(v) and tri.min() >= 0, f"triangle index out of range in {f}")
        objs[oid] = (mid, v, nt)
    items = {m.group(1): [float(x) for x in m.group(2).split()]
             for m in re.finditer(r'<item objectid="(\d+)"[^>]*transform="([^"]+)"', model)}
    ok(set(items) == set(objs), "build items and objects differ")
    ms = z.read("Metadata/model_settings.config").decode()
    cfg_objs = re.findall(r'<object id="(\d+)">(.*?)</object>', ms, re.S)
    ok({o for o, _ in cfg_objs} == set(objs), "model_settings objects differ from the model's")
    cfg = json.loads(z.read("Metadata/project_settings.config"))
    n = len(cfg["filament_colour"])
    for o, body in cfg_objs:
        e = int(re.search(r'key="extruder" value="(\d+)"', body).group(1))
        ok(1 <= e <= n, f"object {o} uses filament {e} of {n}")
        pid = re.search(r'<part id="(\d+)"', body).group(1)
        ok(pid == objs[o][0], f"object {o} part id {pid} is not its mesh id {objs[o][0]}")
    plates = re.findall(r"<plate>(.*?)</plate>", ms, re.S)
    v_ = math.sqrt(len(plates))
    cols = int(round(v_) + 1 if v_ > round(v_) else round(v_))
    stride = 256 * 1.2
    seen = set()
    for i, body in enumerate(plates):
        ok(f'value="{i + 1}"' in re.search(r'key="plater_id" value="\d+"', body).group(0), f"plate {i + 1} id")
        ox, oy = (i % cols) * stride, -(i // cols) * stride
        for o in re.findall(r'key="object_id" value="(\d+)"', body):
            seen.add(o)
            t = items[o]
            v = objs[o][1] + np.array(t[9:12])
            lo, hi = v.min(0), v.max(0)
            ok(lo[0] >= ox - 0.01 and hi[0] <= ox + 256.01 and lo[1] >= oy - 0.01 and hi[1] <= oy + 256.01,
               f"object {o} off plate {i + 1}: x {lo[0] - ox:.1f}..{hi[0] - ox:.1f} y {lo[1] - oy:.1f}..{hi[1] - oy:.1f}")
            ok(abs(lo[2]) < 0.01, f"object {o} not on the bed (z {lo[2]:.3f})")
    ok(seen == set(objs), "objects not on any plate")
    # settings, as PresetBundle::load_config_file_config splits them
    fev, fsi = cfg["filament_extruder_variant"], cfg["filament_self_index"]
    ok(len(fev) == len(fsi) and len(fev) >= n, "filament_extruder_variant / filament_self_index sizes")
    ok([int(x) for x in fsi] == sorted(int(x) for x in fsi) and set(int(x) for x in fsi) == set(range(1, n + 1)),
       "filament_self_index not 1..n in order")
    fvar = set(L["filament_options_with_variant"])
    for k in L["filament"]:
        v = cfg.get(k)
        if isinstance(v, list) and k not in ("compatible_printers", "compatible_prints"):
            if k.startswith("filament_dev_"):         # AMS drying data: several values a filament, left alone on load
                ok(len(v) >= n, f"filament option {k}: {len(v)} values for {n} filaments")
                continue
            want = len(fev) if k in fvar else n
            ok(len(v) == want, f"filament option {k}: {len(v)} values, want {want}")
    for k, want in (("filament_settings_id", n), ("filament_ids", n), ("filament_map", n),
                    ("different_settings_to_system", n + 2), ("inherits_group", n + 2),
                    ("compatible_machine_expression_group", n + 2), ("compatible_process_expression_group", n),
                    ("flush_volumes_matrix", n * n), ("wipe_tower_x", len(plates))):
        ok(len(cfg[k]) == want, f"{k}: {len(cfg[k])} values, want {want}")
    nv = len(cfg["printer_extruder_variant"])
    for k in L["printer_options_with_variant_1"]:
        if k in cfg and isinstance(cfg[k], list):
            ok(len(cfg[k]) == nv, f"printer option {k}: {len(cfg[k])} values, want {nv}")
    for k in L["print_options_with_variant"]:
        if k in cfg and isinstance(cfg[k], list):
            ok(len(cfg[k]) == len(cfg["print_extruder_variant"]), f"process option {k}: {len(cfg[k])} values")
    t = P["template"]
    for k, tv in t.items():
        ok(k in cfg, f"setting missing: {k}")
        now_list = k in set(L["print_options_with_variant"]) | set(L["printer_options_with_variant_1"])
        if k in cfg and not now_list:        # (a per-nozzle setting may have been a single value in older versions)
            ok(isinstance(cfg[k], list) == isinstance(tv, list), f"setting {k} list/scalar differs from Bambu's")
    ok(len(cfg["nozzle_diameter"]) == 1, "nozzle_diameter not one extruder")
    if "Metadata/custom_gcode_per_layer.xml" in names:
        cg = z.read("Metadata/custom_gcode_per_layer.xml").decode()
        for pid, body in re.findall(r'<plate>\s*<plate_info id="(\d+)"/>(.*?)</plate>', cg, re.S):
            ok(1 <= int(pid) <= len(plates), f"filament change on missing plate {pid}")
            for e in re.findall(r'extruder="(\d+)"', body):
                ok(1 <= int(e) <= n, f"filament change to missing filament {e}")
    print(f"{os.path.basename(path)}: {len(plates)} plates, {len(objs)} objects, {n} filaments, "
          f"{sum(o[2] for o in objs.values())} triangles; " + ("OK" if not err else f"{len(err)} problems"))
    for e in err[:40]:
        print("  -", e)
    return not err


if __name__ == "__main__":
    sys.exit(0 if all(check(p) for p in sys.argv[1:]) else 1)

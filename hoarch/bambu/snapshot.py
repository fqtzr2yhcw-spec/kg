"""Snapshot Bambu Studio's system profiles for the P2S into p2s_profiles.json.

Resolves each preset the way Bambu Studio loads its vendor profiles: the parent ("inherits")
first, then the "include" templates, then the preset's own keys. Also keeps a project config
Bambu Studio saved itself (one of its calibration projects), which stands in for the program's
built-in defaults where no profile sets a key, and Bambu Studio's lists of which settings belong
to the printer, the process and the filaments.

    python3 bambu/snapshot.py /path/to/bambustudio   (a checkout of github.com/bambulab/BambuStudio)
"""

import glob
import json
import os
import re
import sys
import zipfile

META = {"type", "name", "inherits", "from", "setting_id", "instantiation", "include", "filament_id",
        "description", "renamed_from", "alias"}
PRINTER = "Bambu Lab P2S 0.4 nozzle"
PROCESS = "0.20mm Standard @BBL P2S"
FILAMENTS = ["Bambu PLA Basic @BBL P2S", "Bambu PLA Matte @BBL P2S", "Bambu PLA Metal @BBL P2S",
             "Bambu PLA Silk+ @BBL P2S", "Bambu PLA Wood @BBL P2S", "Generic PLA @BBL P2S",
             "Generic PLA High Speed @BBL P2S"]


def _index(folder):
    out = {}
    for f in glob.glob(os.path.join(folder, "*.json")):
        try:
            d = json.load(open(f))
        except Exception:
            continue
        if isinstance(d, dict) and "name" in d:
            out[d["name"]] = d
    return out


def _includes(raw):
    inc = raw.get("include")
    if not inc:
        return []
    if isinstance(inc, str):
        inc = inc.strip()
        if inc.startswith("["):
            return [s.strip().strip("'\"") for s in inc[1:-1].split(",") if s.strip()]
        return [inc]
    return list(inc)


def resolve(name, files, seen=()):
    raw = files[name]
    cfg, fid = {}, raw.get("filament_id")
    if raw.get("inherits"):
        cfg, pfid = resolve(raw["inherits"], files, seen + (name,))
        fid = fid or pfid
    for inc in _includes(raw):
        icfg, _ = resolve(inc, files, seen + (name,))
        cfg.update(icfg)
    cfg.update({k: v for k, v in raw.items() if k not in META})
    return cfg, fid


def main(root):
    prof = os.path.join(root, "resources", "profiles", "BBL")
    machines, processes, filaments = (_index(os.path.join(prof, d)) for d in ("machine", "process", "filament"))
    printer, _ = resolve(PRINTER, machines)
    process, _ = resolve(PROCESS, processes)
    fil, ids = {}, {}
    for n in FILAMENTS:
        fil[n], ids[n] = resolve(n, filaments)
    src = open(os.path.join(root, "src", "libslic3r", "Preset.cpp")).read()
    lists = {}
    for nm in ("print", "filament", "machine_limits", "printer"):
        m = re.search(r"static std::vector<std::string>\s+s_Preset_%s_options\s*\{(.*?)\};" % nm, src, re.S)
        lists[nm] = re.findall(r'"([^"]+)"', re.sub(r"//[^\n]*", "", m.group(1)))
    cfg_src = open(os.path.join(root, "src", "libslic3r", "PrintConfig.cpp")).read()
    for nm in ("filament_options_with_variant", "printer_options_with_variant_1", "printer_options_with_variant_2",
               "print_options_with_variant"):
        m = re.search(r"std::set<std::string>\s+%s\s*=\s*\{(.*?)\};" % nm, cfg_src, re.S)
        lists[nm] = re.findall(r'"([^"]+)"', re.sub(r"//[^\n]*", "", m.group(1)))
    calib = os.path.join(root, "resources", "calib", "pressure_advance", "auto_pa_line_dual.3mf")
    template = json.loads(zipfile.ZipFile(calib).read("Metadata/project_settings.config"))
    version = re.search(r'SLIC3R_VERSION "([0-9.]+)"', open(os.path.join(root, "version.inc")).read()).group(1)
    out = {"bambu_studio_version": version, "printer_name": PRINTER, "process_name": PROCESS,
           "printer": printer, "process": process, "filaments": fil, "filament_ids": ids,
           "option_lists": lists, "template": template}
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "p2s_profiles.json")
    json.dump(out, open(path, "w"), indent=0, sort_keys=True)
    print(path, os.path.getsize(path) // 1024, "KB;", "printer", len(printer), "process", len(process),
          {n: len(c) for n, c in fil.items()}, ids)


if __name__ == "__main__":
    main(sys.argv[1])

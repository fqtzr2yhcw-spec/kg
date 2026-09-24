"""Kit bookkeeping: parts with colours and print orientations, fit checks,
single-colour plate packing and 3MF/STL export.
"""
import json
import os
import zipfile
from collections import OrderedDict, defaultdict

import numpy as np
from manifold3d import Manifold as M, OpType

from .core import I34, inv34, mesh_arrays

BED = 250.0
GAP = 3.0


def print_up(A):
    """Print transform for a part built in a local frame A (local w -> print z)."""
    return inv34(A)


def print_flip():
    """Upside down: rotate 180 deg about x."""
    return np.array([[1.0, 0, 0, 0], [0, -1.0, 0, 0], [0, 0, -1.0, 0]])


def print_on_back(A):
    """For a panel built in local frame A with thickness along w: lay it on its back
    (local w -> print z) -- same as print_up; kept for readability."""
    return inv34(A)


def rows(xr, yr, zr):
    R = np.array([xr, yr, zr], float)
    if np.linalg.det(R) < 0:
        R[1] = -R[1]
    out = np.zeros((3, 4))
    out[:, :3] = R
    return out


class Part:
    def __init__(self, name, color, solid, P, key, group, render=None):
        self.name, self.color, self.solid, self.P, self.key, self.group = name, color, solid, P, key, group
        self.render = render          # [(colour, solid)] colour zones of a one-piece part, for renders

    def printed(self):
        s = self.solid.transform(self.P)
        b = s.bounding_box()
        return s.translate([-(b[0] + b[3]) / 2, -(b[1] + b[4]) / 2, -b[2]])


class Kit:
    def __init__(self, name, colors, render_mat):
        self.name, self.colors, self.render_mat = name, colors, render_mat
        self.parts = []

    def add(self, name, color, solid, P=None, key=None, group="", render=None):
        if solid is None or solid.is_empty():
            print("  (empty part skipped)", name)
            return None
        assert color in self.colors, color
        comps = solid.decompose()
        if len(comps) > 1 and any(c.volume() < 1e-3 for c in comps):
            # boolean leftovers with no volume would set the print's bed height
            solid = M.batch_boolean([c for c in comps if c.volume() >= 1e-3], OpType.Add)
        p = Part(name, color, solid, I34 if P is None else P, key or name, group, render)
        self.parts.append(p)
        return p

    # -------------------------------------------------------------- checks
    def interference(self, tol=0.05, ignore=()):
        bbs = [np.array(p.solid.bounding_box()) for p in self.parts]
        bad = []
        n = len(self.parts)
        for i in range(n):
            for j in range(i + 1, n):
                a, b = bbs[i], bbs[j]
                if np.any(a[:3] > b[3:] - 1e-6) or np.any(b[:3] > a[3:] - 1e-6):
                    continue
                pi, pj = self.parts[i], self.parts[j]
                if any((pi.name.startswith(x) and pj.name.startswith(y)) or (pj.name.startswith(x) and pi.name.startswith(y))
                       for x, y in ignore):
                    continue
                v = (pi.solid ^ pj.solid).volume()
                if v > tol:
                    bad.append((round(v, 2), pi.name, pj.name))
        return sorted(bad, reverse=True)

    def bed_check(self):
        out = []
        for p in self.parts:
            b = np.array(p.printed().bounding_box())
            ext = b[3:] - b[:3]
            if max(ext[0], ext[1]) > BED and min(ext[0], ext[1]) > BED:
                out.append((p.name, ext.round(1)))
            elif max(ext[0], ext[1]) > BED * 1.414 or min(ext[0], ext[1]) > BED:
                out.append((p.name, ext.round(1)))
        return out

    # -------------------------------------------------------------- render data
    def render_npz(self, path, offsets=None, only=None):
        groups = defaultdict(list)
        for p in self.parts:
            if only and not only(p):
                continue
            off = (offsets or {}).get(p.name, (0, 0, 0))
            for col, sol in (p.render or [(p.color, p.solid)]):
                if not sol.is_empty():
                    groups[self.render_mat[col]].append(sol.translate(list(off)))
        data = {}
        for mat, ms in groups.items():
            vs, fs, o = [], [], 0
            for m in ms:
                v, f = mesh_arrays(m)
                vs.append(v)
                fs.append(f + o)
                o += len(v)
            data[mat + "__v"] = np.concatenate(vs).astype(np.float32)
            data[mat + "__f"] = np.concatenate(fs).astype(np.int32)
        np.savez_compressed(path, **data)

    def flatlay_npz(self, path, only=None, width=420.0, gap=5.0):
        """Every part in its print orientation, shelf-packed on a table ``width`` wide
        (a 'box contents' view of the kit), written like render_npz."""
        items = []
        for p in self.parts:
            if only and not only(p):
                continue
            m = p.printed()
            b = m.bounding_box()
            if b[4] - b[1] > b[3] - b[0]:
                m = m.rotate([0, 0, 90])
                b = m.bounding_box()
            items.append((p, m.translate([-b[0], -b[1], 0]), b[3] - b[0], b[4] - b[1]))
        # group by colour, then tallest (in plan) first, so each colour reads as a block
        order = {c: i for i, c in enumerate(self.colors)}
        items.sort(key=lambda t: (order[t[0].color], -t[3], -t[2]))
        groups = defaultdict(list)
        x = y = shelf = 0.0
        for (p, m, w, h) in items:
            if x > 0 and x + w > width:
                x, y, shelf = 0.0, y + shelf + gap, 0.0
            groups[self.render_mat[p.color]].append(m.translate([x, -y - h, 0]))
            x += w + gap
            shelf = max(shelf, h)
        data = {}
        for mat, ms in groups.items():
            vs, fs, o = [], [], 0
            for m in ms:
                v, f = mesh_arrays(m)
                vs.append(v)
                fs.append(f + o)
                o += len(v)
            data[mat + "__v"] = np.concatenate(vs).astype(np.float32)
            data[mat + "__f"] = np.concatenate(fs).astype(np.int32)
        np.savez_compressed(path, **data)

    # -------------------------------------------------------------- export
    def unique(self):
        groups = OrderedDict()
        for p in self.parts:
            pm = p.printed()
            b = np.array(pm.bounding_box())
            sig = (p.key, round(pm.volume(), 1), tuple(np.round(b[3:] - b[:3], 1)))
            groups.setdefault(sig, []).append((p, pm))
        out, names = [], defaultdict(int)
        for sig, members in groups.items():
            p0 = members[0][0]
            base = p0.key if len(members) > 1 or p0.key != p0.name else p0.name
            names[base] += 1
            fname = base if names[base] == 1 else f"{base}-v{names[base]}"
            out.append((f"{p0.color}__{fname}".replace("/", "-").replace(" ", "_"), members))
        return out

    def export(self, outdir, layer=0.12):
        for sub in ("plates", "parts", "previews"):
            os.makedirs(os.path.join(outdir, sub), exist_ok=True)
        uniq = self.unique()
        man = {"name": self.name, "scale": "HO 1:87.1", "bed_mm": BED, "parts": [], "plates": []}
        fname_of = {}
        for fname, members in uniq:
            p0, pm0 = members[0]
            write_stl(os.path.join(outdir, "parts", fname + ".stl"), pm0)
            b = pm0.bounding_box()
            man["parts"].append({"file": f"parts/{fname}.stl", "colour": p0.color, "hex": self.colors[p0.color],
                                 "qty": len(members), "group": p0.group,
                                 "size_mm": [round(b[3] - b[0], 1), round(b[4] - b[1], 1), round(b[5] - b[2], 1)],
                                 "instances": [m[0].name for m in members]})
            for (p, pm) in members:
                fname_of[p.name] = (fname, pm)
        by_col = defaultdict(list)
        for p in self.parts:
            fn, pm = fname_of[p.name]
            by_col[p.color].append((fn, p, pm))
        n = 0
        for col in self.colors:
            if col not in by_col:
                continue
            packed = pack(by_col[col])
            for k, placed in enumerate(packed, start=1):
                n += 1
                base = f"{n:02d}_{col}" + (f"_{k}of{len(packed)}" if len(packed) > 1 else "")
                write_3mf(os.path.join(outdir, "plates", base + ".3mf"), [(nm, m) for (nm, _, m) in placed], base)
                preview(os.path.join(outdir, "previews", base + ".png"), placed, self.colors[col], base)
                hmax = max(m.bounding_box()[5] for (_, _, m) in placed)
                man["plates"].append({"file": f"plates/{base}.3mf", "preview": f"previews/{base}.png", "colour": col,
                                      "hex": self.colors[col], "objects": len(placed),
                                      "parts": sorted({nm for (nm, _, _) in placed}), "layer_mm": layer,
                                      "max_height_mm": round(hmax, 1),
                                      "volume_cm3": round(sum(m.volume() for (_, _, m) in placed) / 1000, 1)})
                print(f"plate {base}: {len(placed)} objects, h={hmax:.1f} mm")
        with open(os.path.join(outdir, "manifest.json"), "w") as fh:
            json.dump(man, fh, indent=1)
        return man


# ------------------------------------------------------------------ file writers
def write_stl(path, m):
    v, f = mesh_arrays(m)
    tri = v[f]
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    ln = np.linalg.norm(n, axis=1)
    ln[ln == 0] = 1
    rec = np.zeros(len(f), dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
    rec["n"] = n / ln[:, None]
    rec["v"] = tri
    with open(path, "wb") as fh:
        fh.write(b"hoarch kit".ljust(80, b" "))
        fh.write(np.uint32(len(f)).tobytes())
        fh.write(rec.tobytes())


def write_3mf(path, objects, title):
    obj_xml, items = [], []
    for i, (name, m) in enumerate(objects, start=1):
        v, f = mesh_arrays(m)
        vs = "".join(f'<vertex x="{x:.4f}" y="{y:.4f}" z="{z:.4f}"/>' for x, y, z in v)
        ts = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in f)
        obj_xml.append(f'<object id="{i}" name="{name}" type="model"><mesh><vertices>{vs}</vertices>'
                       f'<triangles>{ts}</triangles></mesh></object>')
        items.append(f'<item objectid="{i}"/>')
    model = ('<?xml version="1.0" encoding="UTF-8"?>\n'
             '<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
             f'<metadata name="Title">{title}</metadata>'
             f'<resources>{"".join(obj_xml)}</resources><build>{"".join(items)}</build></model>')
    ct = ('<?xml version="1.0" encoding="UTF-8"?>\n<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
          '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>'
            '</Relationships>')
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        z.writestr("[Content_Types].xml", ct)
        z.writestr("_rels/.rels", rels)
        z.writestr("3D/3dmodel.model", model)


def pack(items):
    """Shelf-pack (name, part, mesh) items onto BED x BED plates, largest first."""
    prepared = []
    for (name, p, m) in items:
        b = m.bounding_box()
        w, h = b[3] - b[0], b[4] - b[1]
        if w < h and h <= BED:
            m = m.rotate([0, 0, 90])
            b = m.bounding_box()
            m = m.translate([-(b[0] + b[3]) / 2, -(b[1] + b[4]) / 2, 0])
            w, h = h, w
        prepared.append((name, p, m, w, h))
    prepared.sort(key=lambda t: (-t[4], -t[3]))
    plates = []
    for (name, p, m, w, h) in prepared:
        placed = False
        for pl in plates:
            for sh in pl["shelves"]:
                if sh["h"] >= h and sh["x"] + w <= BED:
                    sh["items"].append((name, p, m, sh["x"] + w / 2, sh["y"] + h / 2))
                    sh["x"] += w + GAP
                    placed = True
                    break
            if placed:
                break
            if pl["y"] + h <= BED:
                pl["shelves"].append({"y": pl["y"], "h": h, "x": w + GAP, "items": [(name, p, m, w / 2, pl["y"] + h / 2)]})
                pl["y"] += h + GAP
                placed = True
                break
        if not placed:
            plates.append({"y": h + GAP, "shelves": [{"y": 0, "h": h, "x": w + GAP, "items": [(name, p, m, w / 2, h / 2)]}]})
    out = []
    for pl in plates:
        objs = [it for sh in pl["shelves"] for it in sh["items"]]
        ex = np.array([[cx + m.bounding_box()[0], cy + m.bounding_box()[1], cx + m.bounding_box()[3], cy + m.bounding_box()[4]]
                       for (_, _, m, cx, cy) in objs])
        ox = 128 - (ex[:, 0].min() + ex[:, 2].max()) / 2
        oy = 128 - (ex[:, 1].min() + ex[:, 3].max()) / 2
        out.append([(name, p, m.translate([cx + ox, cy + oy, 0])) for (name, p, m, cx, cy) in objs])
    return out


def preview(path, placed, color, title):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection
    fig, ax = plt.subplots(figsize=(5, 5), dpi=110)
    ax.add_patch(plt.Rectangle((0, 0), 256, 256, fc="#23272b", ec="#555"))
    base = np.array([int(color[i:i + 2], 16) / 255 for i in (1, 3, 5)])
    for (name, p, m) in placed:
        v, f = mesh_arrays(m)
        tri = v[f]
        nz = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])[:, 2]
        up = nz > 1e-6
        if not up.any():
            continue
        zc = tri[up][:, :, 2].mean(1)
        order = np.argsort(zc)
        zmax = max(zc.max(), 1e-3)
        shade = 0.55 + 0.45 * (zc[order] / zmax)
        cols = np.clip(base[None, :] * shade[:, None] + 0.08, 0, 1)
        ax.add_collection(PolyCollection(tri[up][order][:, :, :2], facecolors=cols, edgecolors="none"))
    ax.set_xlim(-2, 258)
    ax.set_ylim(-2, 258)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(title, fontsize=8)
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)


# ------------------------------------------------------------------ slicing check
def slice_check(outdir, ini, layer=0.16, manifest=None):
    """Slice every plate in ``outdir`` with the PrusaSlicer CLI and record time, grams and
    stability warnings into manifest.json. Returns the manifest."""
    import re
    import subprocess
    man = manifest or json.load(open(os.path.join(outdir, "manifest.json")))
    tmp = os.path.join(outdir, "_gcode")
    os.makedirs(tmp, exist_ok=True)

    def minutes(t):
        return round(sum(int(v) * {"d": 1440, "h": 60, "m": 1, "s": 1 / 60}[u] for v, u in re.findall(r"(\d+)([dhms])", t)))

    tot_m = tot_g = 0
    for pl in man["plates"]:
        src = os.path.join(outdir, pl["file"])
        gc = os.path.join(tmp, os.path.basename(src).replace(".3mf", ".gcode"))
        r = subprocess.run(["prusa-slicer", "--export-gcode", "--load", ini, "--dont-arrange", "--layer-height",
                            str(layer), "--output", gc, src], capture_output=True, text=True, timeout=3600)
        log = (r.stdout + r.stderr).splitlines()
        warn = []
        for i, line in enumerate(log):
            if "stability" in line.lower():
                warn = [x.strip() for x in log[i + 1:i + 14] if x.strip() and "=>" not in x and "Consider" not in x]
                break
        t, g = "FAILED", None
        if os.path.exists(gc):
            tail = open(gc, errors="ignore").read()[-40000:]
            m = re.search(r"estimated printing time \(normal mode\) = (.+)", tail)
            t = m.group(1).strip() if m else "?"
            m = re.search(r"filament used \[g\] = ([\d.]+)", tail)
            g = float(m.group(1)) if m else None
            os.remove(gc)
        pl["slice"] = {"time": t, "grams": g, "warnings": warn}
        if t not in ("FAILED", "?"):
            tot_m += minutes(t)
        tot_g += g or 0
        print(f"{os.path.basename(src):34s} {t:>12s} {g} g", flush=True)
    man["totals"] = {"print_minutes": tot_m, "filament_g": round(tot_g, 1)}
    json.dump(man, open(os.path.join(outdir, "manifest.json"), "w"), indent=1)
    print(f"TOTAL {tot_m // 60} h {tot_m % 60} m, {tot_g:.0f} g")
    return man

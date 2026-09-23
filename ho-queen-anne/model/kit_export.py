"""Lay the kit out on single-colour plates and export files.

Outputs (under ho-queen-anne/kit/):
  plates/NN_<Colour>_<group>.3mf   one bed per file, parts pre-arranged
  parts/<Colour>__<part>.stl       one STL per unique part (print orientation)
  manifest.json                    parts, quantities, plates, recommended settings
  previews/NN_<...>.png            top-down plate previews
"""
import json
import os
import sys
import zipfile
from collections import OrderedDict, defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(HERE, "..", "kit")
BED = 250.0
GAP = 3.0

# recommended layer height per plate group (first layer is always 0.2 mm so a
# 0.2 mm glazing layer prints as exactly one layer)
LAYER = {"walls": 0.12, "tower": 0.12, "bay": 0.12, "roofs": 0.12, "dormer": 0.12,
         "windows": 0.12, "doors": 0.12, "porch": 0.12, "trim": 0.16, "cornice": 0.16,
         "foundation": 0.2, "chimneys": 0.12, "back": 0.16, "small": 0.16}


def mesh_arrays(m):
    mesh = m.to_mesh()
    return np.asarray(mesh.vert_properties)[:, :3].astype(np.float64), np.asarray(mesh.tri_verts).astype(np.int64)


def write_stl(path, m):
    v, f = mesh_arrays(m)
    tri = v[f]
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    ln = np.linalg.norm(n, axis=1)
    ln[ln == 0] = 1
    n = n / ln[:, None]
    rec = np.zeros(len(f), dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
    rec["n"] = n
    rec["v"] = tri
    with open(path, "wb") as fh:
        fh.write(b"Beaumont HO kit".ljust(80, b" "))
        fh.write(np.uint32(len(f)).tobytes())
        fh.write(rec.tobytes())


def write_3mf(path, objects, title):
    """objects: list of (name, manifold already placed on the bed)."""
    obj_xml = []
    items = []
    for i, (name, m) in enumerate(objects, start=1):
        v, f = mesh_arrays(m)
        vs = "".join(f'<vertex x="{x:.4f}" y="{y:.4f}" z="{z:.4f}"/>' for x, y, z in v)
        ts = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in f)
        obj_xml.append(f'<object id="{i}" name="{name}" type="model"><mesh><vertices>{vs}</vertices>'
                       f'<triangles>{ts}</triangles></mesh></object>')
        items.append(f'<item objectid="{i}"/>')
    model = ('<?xml version="1.0" encoding="UTF-8"?>\n'
             '<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
             f'<metadata name="Title">{title}</metadata><metadata name="Designer">Beaumont HO kit</metadata>'
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


def unique_parts(parts):
    """Group identical parts: same key and same printed geometry."""
    groups = OrderedDict()
    for p in parts:
        pm = p.printed()
        b = np.array(pm.bounding_box())
        sig = (p.key, round(pm.volume(), 1), tuple(np.round(b[3:] - b[:3], 1)))
        groups.setdefault(sig, []).append((p, pm))
    out = []
    names = defaultdict(int)
    for sig, members in groups.items():
        base = members[0][0].key if len(members) > 1 or members[0][0].key != members[0][0].name else members[0][0].name
        names[base] += 1
        fname = base if names[base] == 1 else f"{base}-v{names[base]}"
        fname = fname.replace("/", "-over-").replace(" ", "_")
        out.append((fname, members))
    return out


def pack(items):
    """Shelf-pack (name, part, mesh) items onto BED x BED plates. Returns list of plates."""
    def ext(m):
        b = m.bounding_box()
        return b[3] - b[0], b[4] - b[1]

    prepared = []
    for (name, p, m) in items:
        w, h = ext(m)
        if w < h and h <= BED:           # lay long side along x
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
                sh = {"y": pl["y"], "h": h, "x": w + GAP, "items": [(name, p, m, w / 2, pl["y"] + h / 2)]}
                pl["shelves"].append(sh)
                pl["y"] += h + GAP
                placed = True
                break
        if not placed:
            plates.append({"y": h + GAP, "shelves": [{"y": 0, "h": h, "x": w + GAP,
                                                      "items": [(name, p, m, w / 2, h / 2)]}]})
    out = []
    for pl in plates:
        objs = []
        xs, ys = [], []
        for sh in pl["shelves"]:
            for (name, p, m, cx, cy) in sh["items"]:
                objs.append((name, p, m, cx, cy))
        # centre the plate content on a 256 mm bed
        allb = np.array([[cx, cy] for (_, _, _, cx, cy) in objs])
        exts = []
        for (_, _, m, cx, cy) in objs:
            b = m.bounding_box()
            exts.append([cx + b[0], cy + b[1], cx + b[3], cy + b[4]])
        exts = np.array(exts)
        ox = 128 - (exts[:, 0].min() + exts[:, 2].max()) / 2
        oy = 128 - (exts[:, 1].min() + exts[:, 3].max()) / 2
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
        zc = tri[up][:, :, 2].mean(1)
        order = np.argsort(zc)
        zmax = max(zc.max(), 1e-3) if len(zc) else 1
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


def main():
    kit.build()
    os.makedirs(os.path.join(OUTDIR, "plates"), exist_ok=True)
    os.makedirs(os.path.join(OUTDIR, "parts"), exist_ok=True)
    os.makedirs(os.path.join(OUTDIR, "previews"), exist_ok=True)
    uniq = unique_parts(kit.PARTS)
    manifest = {"scale": "HO 1:87.1", "bed_mm": BED, "parts": [], "plates": []}
    fname_of = {}
    for fname, members in uniq:
        p0, pm0 = members[0]
        write_stl(os.path.join(OUTDIR, "parts", fname + ".stl"), pm0)
        b = pm0.bounding_box()
        manifest["parts"].append({"file": f"parts/{fname}.stl", "colour": p0.color, "hex": kit.COLORS[p0.color],
                                  "qty": len(members), "group": p0.group,
                                  "size_mm": [round(b[3] - b[0], 1), round(b[4] - b[1], 1), round(b[5] - b[2], 1)],
                                  "volume_cm3": round(pm0.volume() / 1000, 2),
                                  "instances": [m[0].name for m in members]})
        for (p, pm) in members:
            fname_of[p.name] = (fname, pm)
    # plates: by colour, big structural groups kept together
    by_col = defaultdict(list)
    for p in kit.PARTS:
        fname, pm = fname_of[p.name]
        by_col[p.color].append((fname, p, pm))
    n = 0
    for col in kit.COLORS:
        if col not in by_col:
            continue
        for placed in pack(by_col[col]):
            n += 1
            groups = sorted({p.group for (_, p, _) in placed})
            tag = "-".join(groups)[:40]
            base = f"{n:02d}_{col}_{tag}"
            write_3mf(os.path.join(OUTDIR, "plates", base + ".3mf"), [(nm, m) for (nm, _, m) in placed], base)
            preview(os.path.join(OUTDIR, "previews", base + ".png"), placed, kit.COLORS[col], base)
            lh = min(LAYER.get(g, 0.16) for g in groups)
            hmax = max(m.bounding_box()[5] for (_, _, m) in placed)
            manifest["plates"].append({"file": f"plates/{base}.3mf", "colour": col, "hex": kit.COLORS[col],
                                       "groups": groups, "objects": len(placed),
                                       "parts": sorted({nm for (nm, _, _) in placed}),
                                       "layer_mm": lh, "max_height_mm": round(hmax, 1),
                                       "volume_cm3": round(sum(m.volume() for (_, _, m) in placed) / 1000, 1)})
            print(f"plate {base}: {len(placed)} objects, h={hmax:.1f} mm")
    with open(os.path.join(OUTDIR, "manifest.json"), "w") as fh:
        json.dump(manifest, fh, indent=1)
    print("unique parts:", len(uniq), "plates:", n)


if __name__ == "__main__":
    main()

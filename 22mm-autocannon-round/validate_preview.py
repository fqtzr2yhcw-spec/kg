#!/usr/bin/env python3
"""Validate the generated 3MF packages and render a shaded preview lineup."""
import glob, os, zipfile
import xml.etree.ElementTree as ET
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

import generate as G

NS = "{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}"
here = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------- validation
def validate(path):
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        assert "[Content_Types].xml" in names
        assert "_rels/.rels" in names
        assert "3D/3dmodel.model" in names
        model = z.read("3D/3dmodel.model")
    root = ET.fromstring(model)
    mats = root.findall(f".//{NS}basematerials/{NS}base")
    objs = root.findall(f".//{NS}object")
    items = root.findall(f".//{NS}build/{NS}item")
    # gather all vertices across mesh objects for a bbox
    xs = ys = zs = None
    pts = []
    for o in objs:
        for v in o.findall(f".//{NS}vertex"):
            pts.append((float(v.get("x")), float(v.get("y")), float(v.get("z"))))
    a = np.array(pts)
    bb = (a.min(0), a.max(0))
    print(f"{os.path.basename(path):34s} bases={len(mats)} objects={len(objs)} "
          f"build_items={len(items)}")
    print(f"    bbox mm  x[{bb[0][0]:7.2f},{bb[1][0]:7.2f}] "
          f"y[{bb[0][1]:7.2f},{bb[1][1]:7.2f}] z[{bb[0][2]:7.2f},{bb[1][2]:7.2f}]")
    return len(items)

print("== 3MF validation ==")
for p in sorted(glob.glob(os.path.join(here, "*.3mf"))):
    validate(p)

# ---------------------------------------------------------------- preview
def hex2rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i+2], 16) for i in (0, 2, 4)], float) / 255.0

PAL = {name: hex2rgb(hx) for name, hx in G.COLORS}

# outer case silhouette (radius as a function of z)
CASE_OUTER = [(16.5,0),(16.5,4.5),(16.2,5.0),(13.8,5.8),(13.8,7.6),
              (16.2,9.2),(16.0,12),(14.4,100),(12.9,108),(12.0,114),(12.0,130)]

def case_outer_r(z):
    pts = CASE_OUTER
    for i in range(len(pts)-1):
        (r0,z0),(r1,z1) = pts[i], pts[i+1]
        if z0 <= z <= z1:
            t = 0 if z1==z0 else (z-z0)/(z1-z0)
            return r0 + t*(r1-r0)
    return pts[-1][0]

def radius_at(z):
    if z <= 130: return case_outer_r(z)
    if 131 <= z <= 139: return G.BAND_R
    return G.proj_r(z)

def color_at(z, v):
    if z <= 130.0: return "Brass_Case"
    if 131.0 <= z <= 139.0: return "Copper_Band"
    if v.get("band") and G.STENCIL_Z[0] <= z <= G.STENCIL_Z[1]:
        return v["band"]
    if v.get("tip") and z >= G.TIP_Z0:
        return v["tip"]
    return v["body"]

def render_variant(v, px_mm=5.0, maxR=18.0, ztop=190.0):
    H = int(ztop*px_mm); W = int(2*maxR*px_mm)
    img = np.ones((H, W, 4))          # RGBA, white, alpha 0 background
    img[..., 3] = 0.0
    light = np.array([-0.45, 0.89]); light /= np.linalg.norm(light)
    for row in range(H):
        z = ztop - (row+0.5)/px_mm
        if z < 0 or z > ztop: continue
        R = radius_at(z)
        if R <= 0: continue
        ck = color_at(z, v); base = PAL[ck]
        metal = ck in ("Brass_Case","Copper_Band","Nickel_Primer")
        for col in range(W):
            x = (col+0.5)/px_mm - maxR
            u = x / R
            if abs(u) > 1.0: continue
            n = np.array([u, np.sqrt(max(0.0,1-u*u))])
            d = max(0.0, float(n @ light))
            shade = 0.34 + 0.72*d
            spec = (0.55 if metal else 0.28) * d**(9 if metal else 16)
            rgb = np.clip(base*shade + spec, 0, 1)
            # thin dark rim near silhouette edge
            if abs(u) > 0.985:
                rgb *= 0.45
            img[row, col, :3] = rgb
            img[row, col, 3] = 1.0
    return img

def main_preview():
    fig, axes = plt.subplots(1, len(G.VARIANTS), figsize=(15, 8.2),
                             facecolor="#111318")
    titles = {"HE-I":"HE-I","AP":"AP","API-T":"API-T","TP":"TP","WP":"WP-SMOKE"}
    subs = {"HE-I":"High-Explosive Inc.","AP":"Armor-Piercing",
            "API-T":"AP Incendiary-Tracer","TP":"Target Practice (inert)",
            "WP":"White-Phosphorus Smoke"}
    for ax, v in zip(axes, G.VARIANTS):
        img = render_variant(v)
        ax.imshow(img, extent=[-18, 18, 0, 190], aspect="equal",
                  interpolation="bilinear")
        ax.set_facecolor("#111318")
        ax.set_xlim(-20, 20); ax.set_ylim(-6, 196)
        ax.set_title(titles[v["key"]], color="white", fontsize=15, pad=6)
        ax.text(0, -3, subs[v["key"]], color="#c9ccd3", ha="center",
                va="top", fontsize=8.5)
        for s in ax.spines.values(): s.set_visible(False)
        ax.set_xticks([]); ax.set_yticks([])
    fig.suptitle("22 mm autocannon round  ·  1:1 scale  ·  MIL-STD-709 color coded",
                 color="white", fontsize=17, y=0.98)
    axes[0].set_yticks([0,50,100,150,187.7])
    axes[0].set_yticklabels(["0","50","100","150","188 mm"], color="#9aa0aa",
                            fontsize=8)
    axes[0].tick_params(length=0)
    fig.text(0.5, 0.02,
             "brass case · nickel primer · copper driving band · Ø22 mm proj · "
             "Ø33 mm rim · 188 mm OAL",
             color="#8a909a", ha="center", fontsize=9)
    out = os.path.join(here, "preview.png")
    fig.savefig(out, dpi=130, facecolor="#111318", bbox_inches="tight")
    print(f"\nwrote {os.path.basename(out)}")

print("\n== render preview ==")
main_preview()

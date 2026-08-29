#!/usr/bin/env python3
"""
Generate 1:1-scale, color-coded 3MF models of a 22 mm autocannon cartridge
("22 mm mike-mike round") in the five most common ammunition natures.

Everything is a solid of revolution built from a 2D (r, z) profile, so the
geometry is fully parametric and watertight by construction.  Colors follow
US MIL-STD-709 ammunition color coding:

    HE-I  (High-Explosive Incendiary) : yellow body + red band
    AP    (Armor-Piercing)            : black body + white ID band
    API-T (AP Incendiary-Tracer)      : black body + red nose tip
    TP    (Target Practice, inert)    : blue body + white ID band
    WP    (White-Phosphorus Smoke)    : light-green body + red band

Common metal parts (shared by every variant):
    brass case, nickel primer, copper rotating (driving) band.

Output:
    22mm_autocannon_1to1_ALL.3mf      - all five variants on one plate
    22mm_autocannon_1to1_<NAME>.3mf   - one file per variant
    preview.png                       - shaded lineup render

No third-party dependencies for the 3MF build (stdlib only).  numpy/matplotlib
are used solely for the optional preview image.
"""

import math
import os
import struct
import zipfile
import xml.sax.saxutils as sx

# --------------------------------------------------------------------------
# Colors (sRGB, MIL-STD-709 inspired) -> 3MF base-material palette
# --------------------------------------------------------------------------
COLORS = [
    ("Brass_Case",   "#C8A951"),   # 0  cartridge brass
    ("Nickel_Primer","#D2D4D7"),   # 1  nickel / silver primer cup
    ("Copper_Band",  "#B87333"),   # 2  copper driving band
    ("HE_Yellow",    "#F4C400"),   # 3  high explosive
    ("AP_Black",     "#1A1A1C"),   # 4  armor piercing
    ("TP_Blue",      "#1F5FBF"),   # 5  target practice / inert
    ("Smoke_Green",  "#7CB342"),   # 6  screening / WP smoke
    ("Marker_Red",   "#C41E23"),   # 7  incendiary / WP / tracer marker
    ("Stencil_White","#ECECEC"),   # 8  stencil markings on dark bodies
]
CIDX = {name: i for i, (name, _hex) in enumerate(COLORS)}

# --------------------------------------------------------------------------
# Master dimensions (millimetres, 1:1).  22 mm caliber, 20-25 mm-class layout.
# --------------------------------------------------------------------------
CAL_R      = 11.0     # projectile / bore radius  (22 mm dia)
NECK_OUT_R = 12.0     # case-mouth outer radius   (24 mm) -> 1 mm mouth lip
RIM_R      = 16.5     # rim / base radius         (33 mm dia)
GROOVE_R   = 13.8     # extractor-groove floor radius
BODY_LO_R  = 16.0     # case body radius near head
BODY_HI_R  = 14.4     # case body radius near shoulder
PRIMER_R   = 3.6      # primer cup radius
PRIMER_H   = 8.0      # primer / pocket depth

RIM_H      = 4.5      # rim thickness
Z_SHOULDER = 100.0    # start of bottleneck
Z_NECK     = 114.0    # start of straight neck
Z_MOUTH    = 130.0    # case mouth
Z_BORE     = 118.0    # bottom of the neck bore (projectile seats to here)

BAND_Z0, BAND_Z1 = 131.0, 139.0   # copper driving band
BAND_R           = 11.5           # driving band stands proud

OGIVE_START = 150.0               # cylinder -> ogive transition
Z_BASE_PROJ = Z_BORE              # projectile base (seated inside neck)

# tangent-ogive geometry
_MEPLAT_R = 0.8
_OG_LEN   = 39.0                                   # nominal ogive length
_RHO      = (CAL_R**2 + _OG_LEN**2) / (2*CAL_R)    # ogive radius
def _ogive_r(z):
    d = z - OGIVE_START
    val = _RHO*_RHO - d*d
    return math.sqrt(val) - (_RHO - CAL_R) if val > 0 else 0.0
# tip z where radius drops to the meplat
def _tip_z():
    z = OGIVE_START
    while _ogive_r(z) > _MEPLAT_R and z < OGIVE_START + _OG_LEN + 5:
        z += 0.01
    return z
Z_TIP = round(_tip_z(), 3)          # ~ 188.6 mm  -> overall length

def proj_r(z):
    """Outer radius of the projectile body/ogive at height z."""
    if z <= OGIVE_START:
        return CAL_R
    if z >= Z_TIP:
        return _MEPLAT_R
    return _ogive_r(z)

SEG = 160        # angular resolution for the exported meshes


# --------------------------------------------------------------------------
# Revolve a closed 2D (r,z) polygon about the z-axis -> watertight mesh.
# On-axis vertices (r==0) collapse to a single apex; global winding is fixed
# afterwards so all normals point outward (positive signed volume).
# --------------------------------------------------------------------------
def revolve(profile, seg=SEG):
    verts = []
    tris = []
    axis_v = {}
    ring_v = {}

    def vid(i, k):
        r, z = profile[i]
        if r < 1e-9:
            if i not in axis_v:
                axis_v[i] = len(verts)
                verts.append((0.0, 0.0, z))
            return axis_v[i]
        k %= seg
        key = (i, k)
        if key not in ring_v:
            th = 2.0 * math.pi * k / seg
            ring_v[key] = len(verts)
            verts.append((r * math.cos(th), r * math.sin(th), z))
        return ring_v[key]

    n = len(profile)
    for i in range(n):
        j = (i + 1) % n
        ri = profile[i][0]
        rj = profile[j][0]
        on_i = ri < 1e-9
        on_j = rj < 1e-9
        if on_i and on_j:
            continue  # edge lies on the axis -> no surface
        for k in range(seg):
            if on_i:
                tris.append((vid(i, k), vid(j, k), vid(j, k + 1)))
            elif on_j:
                tris.append((vid(i, k), vid(j, k), vid(i, k + 1)))
            else:
                a, b = vid(i, k), vid(j, k)
                c, d = vid(j, k + 1), vid(i, k + 1)
                tris.append((a, b, c))
                tris.append((a, c, d))

    # orient outward
    vol = 0.0
    for (a, b, c) in tris:
        ax, ay, az = verts[a]
        bx, by, bz = verts[b]
        cx, cy, cz = verts[c]
        vol += (ax * (by * cz - bz * cy)
                - ay * (bx * cz - bz * cx)
                + az * (bx * cy - by * cx))
    if vol < 0:
        tris = [(a, c, b) for (a, b, c) in tris]
    return verts, tris


def merge(meshes):
    """Concatenate several (verts,tris) shells into one mesh soup."""
    V, T = [], []
    for verts, tris in meshes:
        off = len(V)
        V.extend(verts)
        T.extend((a + off, b + off, c + off) for (a, b, c) in tris)
    return V, T


def region_profile(za, zb, radius_fn):
    """Closed profile for the solid between planes za..zb with outer
    radius radius_fn(z); flat disks cap both ends.  Straight (cylindrical)
    sections use two samples; only the curved ogive is finely sampled."""
    zs = {round(za, 4), round(zb, 4)}
    if za < OGIVE_START < zb:
        zs.add(OGIVE_START)
    cs, ce = max(za, OGIVE_START), min(zb, Z_TIP)
    if ce > cs:
        steps = max(1, int(math.ceil((ce - cs) / 1.2)))
        for s in range(steps + 1):
            zs.add(round(cs + (ce - cs) * s / steps, 4))
    zs = sorted(zs)
    pts = [(0.0, za)]
    for z in zs:
        pts.append((max(radius_fn(z), 1e-6), z))
    pts.append((0.0, zb))
    return pts


# --------------------------------------------------------------------------
# Fixed (shared) parts
# --------------------------------------------------------------------------
def case_mesh():
    prof = [
        (PRIMER_R, 0.0),
        (RIM_R,    0.0),
        (RIM_R,    RIM_H),
        (BODY_LO_R + 0.2, RIM_H + 0.5),
        (GROOVE_R, RIM_H + 1.3),
        (GROOVE_R, RIM_H + 3.1),
        (BODY_LO_R + 0.2, RIM_H + 4.7),
        (BODY_LO_R, 12.0),
        (BODY_HI_R, Z_SHOULDER),
        (12.9, 108.0),
        (NECK_OUT_R, Z_NECK),
        (NECK_OUT_R, Z_MOUTH),
        (CAL_R,     Z_MOUTH),      # mouth lip inner
        (CAL_R,     Z_BORE),       # neck-bore wall
        (0.0,       Z_BORE),       # neck-bore floor
        (0.0,       PRIMER_H),     # down the axis (interior)
        (PRIMER_R,  PRIMER_H),     # primer-pocket floor
        (PRIMER_R,  0.0),          # primer-pocket wall
    ]
    return revolve(prof)


def primer_mesh():
    prof = [(0.0, 0.0), (PRIMER_R, 0.0), (PRIMER_R, PRIMER_H), (0.0, PRIMER_H)]
    return revolve(prof)


def band_mesh():
    prof = [(0.0, BAND_Z0), (BAND_R, BAND_Z0), (BAND_R, BAND_Z1), (0.0, BAND_Z1)]
    return revolve(prof)


# --------------------------------------------------------------------------
# Per-variant projectile: body color + optional stencil band + optional tip
# --------------------------------------------------------------------------
STENCIL_Z = (142.0, 145.0)     # flush ID band location
TIP_Z0    = 181.0              # nose-tip color split (API-T)

def projectile_parts(variant):
    """Return dict colorkey -> mesh for one variant's projectile."""
    features = [("copper", BAND_Z0, BAND_Z1)]      # driving band (skipped by body)
    if variant.get("band"):
        features.append((variant["band"], STENCIL_Z[0], STENCIL_Z[1]))
    if variant.get("tip"):
        features.append((variant["tip"], TIP_Z0, Z_TIP))
    features.sort(key=lambda f: f[1])

    out = {}  # colorkey -> list of shells
    # feature solids
    for ckey, z0, z1 in features:
        if ckey == "copper":
            continue  # driving band is a shared part
        out.setdefault(ckey, []).append(revolve(region_profile(z0, z1, proj_r)))

    # body fills every gap not taken by a feature
    body_key = variant["body"]
    cuts = sorted([(z0, z1) for _c, z0, z1 in features])
    cursor = Z_BASE_PROJ
    for z0, z1 in cuts:
        if z0 > cursor + 1e-6:
            out.setdefault(body_key, []).append(
                revolve(region_profile(cursor, z0, proj_r)))
        cursor = max(cursor, z1)
    if cursor < Z_TIP - 1e-6:
        out.setdefault(body_key, []).append(
            revolve(region_profile(cursor, Z_TIP, proj_r)))

    return {k: merge(v) for k, v in out.items()}


VARIANTS = [
    {"key": "HE-I",  "name": "22mm HE-I High-Explosive Incendiary",
     "body": "HE_Yellow",   "band": "Marker_Red"},
    {"key": "AP",    "name": "22mm AP Armor-Piercing",
     "body": "AP_Black",    "band": "Stencil_White"},
    {"key": "API-T", "name": "22mm API-T Armor-Piercing Incendiary Tracer",
     "body": "AP_Black",    "tip":  "Marker_Red"},
    {"key": "TP",    "name": "22mm TP Target-Practice (inert)",
     "body": "TP_Blue",     "band": "Stencil_White"},
    {"key": "WP",    "name": "22mm WP White-Phosphorus Smoke",
     "body": "Smoke_Green", "band": "Marker_Red"},
]


# --------------------------------------------------------------------------
# 3MF writer
# --------------------------------------------------------------------------
def fnum(x):
    return f"{x:.5f}".rstrip("0").rstrip(".")

def mesh_xml(verts, tris):
    vout = ["<vertices>"]
    for (x, y, z) in verts:
        vout.append(f'<vertex x="{fnum(x)}" y="{fnum(y)}" z="{fnum(z)}"/>')
    vout.append("</vertices>")
    tout = ["<triangles>"]
    for (a, b, c) in tris:
        tout.append(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>')
    tout.append("</triangles>")
    return "".join(vout) + "".join(tout)


def build_model(items, name):
    """items = list of dicts: {'name', 'parts':[(colorkey,(V,T)),...], 'tx','ty'}"""
    oid = 10
    res = []
    # material palette
    base = "".join(
        f'<base name="{sx.quoteattr(nm)[1:-1]}" displaycolor="{hx}FF"/>'
        for nm, hx in COLORS)
    res.append(f'<basematerials id="1">{base}</basematerials>')

    build_items = []
    for it in items:
        comp_ids = []
        for ckey, (V, T) in it["parts"]:
            res.append(
                f'<object id="{oid}" type="model" pid="1" '
                f'pindex="{CIDX[ckey]}"><mesh>{mesh_xml(V, T)}</mesh></object>')
            comp_ids.append(oid)
            oid += 1
        comps = "".join(f'<component objectid="{c}"/>' for c in comp_ids)
        asm_id = oid
        oid += 1
        res.append(
            f'<object id="{asm_id}" type="model" name="{sx.quoteattr(it["name"])[1:-1]}">'
            f'<components>{comps}</components></object>')
        tx, ty = it.get("tx", 0.0), it.get("ty", 0.0)
        build_items.append(
            f'<item objectid="{asm_id}" transform="1 0 0 0 1 0 0 0 1 '
            f'{fnum(tx)} {fnum(ty)} 0"/>')

    model = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<model unit="millimeter" xml:lang="en-US" '
        'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
        f'<metadata name="Title">{sx.escape(name)}</metadata>'
        '<metadata name="Application">22mm-autocannon-round generator</metadata>'
        '<metadata name="Description">1:1 22mm autocannon cartridge, '
        'MIL-STD-709 color coded</metadata>'
        f'<resources>{"".join(res)}</resources>'
        f'<build>{"".join(build_items)}</build>'
        '</model>')
    return model


def write_3mf(path, model_xml):
    ct = ('<?xml version="1.0" encoding="UTF-8"?>\n'
          '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
          '<Default Extension="rels" ContentType='
          '"application/vnd.openxmlformats-package.relationships+xml"/>'
          '<Default Extension="model" ContentType='
          '"application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
          '</Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Target="/3D/3dmodel.model" Id="rel0" '
            'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>'
            '</Relationships>')
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", ct)
        z.writestr("_rels/.rels", rels)
        z.writestr("3D/3dmodel.model", model_xml)


# --------------------------------------------------------------------------
# watertight / manifold sanity check (each edge shared by exactly 2 tris)
# --------------------------------------------------------------------------
def check_manifold(V, T):
    from collections import defaultdict
    edges = defaultdict(int)
    for (a, b, c) in T:
        for e in ((a, b), (b, c), (c, a)):
            edges[(min(e), max(e))] += 1
    bad = sum(1 for v in edges.values() if v != 2)
    return bad, len(V), len(T)


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------
def main():
    here = os.path.dirname(os.path.abspath(__file__))
    print(f"Z_TIP (overall length) = {Z_TIP} mm  ; ogive rho = {_RHO:.2f} mm")

    shared = {
        "Brass_Case":    case_mesh(),
        "Nickel_Primer": primer_mesh(),
        "Copper_Band":   band_mesh(),
    }
    for k, (V, T) in shared.items():
        bad, nv, nt = check_manifold(V, T)
        print(f"  shared {k:14s}: {nt:6d} tris  non-manifold edges={bad}")

    variant_parts = {}
    for v in VARIANTS:
        parts = projectile_parts(v)
        variant_parts[v["key"]] = parts
        for ck, (V, T) in parts.items():
            bad, nv, nt = check_manifold(V, T)
            tag = f"{v['key']}/{ck}"
            print(f"  proj  {tag:22s}: {nt:6d} tris  non-manifold edges={bad}")

    def variant_item(v, tx=0.0, ty=0.0):
        parts = [("Brass_Case",    shared["Brass_Case"]),
                 ("Nickel_Primer", shared["Nickel_Primer"]),
                 ("Copper_Band",   shared["Copper_Band"])]
        for ck, mesh in variant_parts[v["key"]].items():
            parts.append((ck, mesh))
        return {"name": v["name"], "parts": parts, "tx": tx, "ty": ty}

    # individual files
    for v in VARIANTS:
        item = variant_item(v, tx=128.0, ty=128.0)
        xml = build_model([item], v["name"])
        out = os.path.join(here, f"22mm_autocannon_1to1_{v['key']}.3mf")
        write_3mf(out, xml)
        print(f"wrote {os.path.basename(out)}  ({len(xml)//1024} KiB xml)")

    # combined file
    items = []
    n = len(VARIANTS)
    for i, v in enumerate(VARIANTS):
        items.append(variant_item(v, tx=128.0 + (i - (n - 1) / 2) * 45.0, ty=128.0))
    xml = build_model(items, "22mm autocannon round - 5 variants")
    out = os.path.join(here, "22mm_autocannon_1to1_ALL.3mf")
    write_3mf(out, xml)
    print(f"wrote {os.path.basename(out)}  ({len(xml)//1024} KiB xml)")


if __name__ == "__main__":
    main()

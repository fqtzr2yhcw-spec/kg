"""Cycles renders of a kit assembly npz (material-name__v / __f arrays).

usage: python3 -m hoarch.render --npz FILE --palette FILE.json [--samples N] [--res WxH]
       [--views hero,front,...] [--out DIR] [--bbox=x0,y0,z0,x1,y1,z1]
The palette JSON maps material name -> [hex, roughness, metallic].
"""
import argparse
import math
import os

import numpy as np
import bpy
from mathutils import Vector

import json

HERE = os.path.dirname(os.path.abspath(__file__))
PALETTE = {"glass": ("#1b2228", 0.06, 0.0), "shadow": ("#1a1a1a", 1.0, 0.0)}
WALK = None          # (x centre, y of the step front, width) of a front walk on the lawn

VIEWS = {
    # name: (azimuth deg (0 = front, +ve = to the viewer's right), elevation deg, lens mm, margin, target offset)
    "hero": (-38, 16, 70, 0.95, (0, 0, 0)),
    "front": (0, 6, 85, 0.92, (0, 0, 0)),
    "right": (58, 14, 70, 0.95, (0, 0, 0)),
    "rear": (150, 18, 70, 0.95, (0, 0, 0)),
    "aerial": (-30, 42, 60, 1.05, (0, 0, 0)),
    "porch": (-30, 10, 70, None, (5, -25, 22), 190),
    "tower": (-40, 8, 85, None, (14, 0, 128), 230),
    "gable": (15, 6, 85, None, (82, -24, 95), 200),
}


def srgb_to_lin(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(((x / 12.92) if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4) for x in c) + (1.0,)


def make_mat(name, hexcol, rough, metal):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = srgb_to_lin(hexcol)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if name in ("glass",):
        b.inputs["Specular IOR Level"].default_value = 0.9
        b.inputs["Coat Weight"].default_value = 0.5
    if name == "stained":
        b.inputs["Emission Color"].default_value = srgb_to_lin("#e08a3a")
        b.inputs["Emission Strength"].default_value = 0.15
    # subtle colour variation / paint texture
    if name not in ("glass", "stained", "metal", "brass"):
        tex = nt.nodes.new("ShaderNodeTexNoise")
        tex.inputs["Scale"].default_value = 0.35
        tex.inputs["Detail"].default_value = 6
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.inputs["Factor"].default_value = 0.08 if name not in ("stone", "roof", "brick") else 0.22
        mix.inputs["A"].default_value = srgb_to_lin(hexcol)
        dark = tuple(c * 0.72 for c in srgb_to_lin(hexcol)[:3]) + (1.0,)
        mix.inputs["B"].default_value = dark
        nt.links.new(tex.outputs["Fac"], mix.inputs["Factor"]) if name in ("stone", "roof", "brick") else None
        nt.links.new(mix.outputs["Result"], b.inputs["Base Color"])
    return m


def build_scene(npz_path, lawn=True, bbox=None):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    data = np.load(npz_path)
    mats = sorted({k.split("__")[0] for k in data.files})
    lo = np.array([1e9, 1e9, 1e9])
    hi = -lo
    for name in mats:
        v = data[name + "__v"]
        f = data[name + "__f"]
        lo = np.minimum(lo, v.min(0))
        hi = np.maximum(hi, v.max(0))
        me = bpy.data.meshes.new(name)
        me.vertices.add(len(v))
        me.vertices.foreach_set("co", v.ravel())
        me.loops.add(len(f) * 3)
        me.loops.foreach_set("vertex_index", f.ravel())
        me.polygons.add(len(f))
        me.polygons.foreach_set("loop_start", np.arange(0, len(f) * 3, 3))
        me.polygons.foreach_set("loop_total", np.full(len(f), 3))
        me.update(calc_edges=True)
        me.validate()
        try:
            me.shade_smooth()
            me.set_sharp_from_angle(angle=math.radians(32))
        except Exception as e:  # pragma: no cover
            print("smooth failed", e)
        ob = bpy.data.objects.new(name, me)
        sc.collection.objects.link(ob)
        hexcol, r, mt = PALETTE.get(name, ("#ff00ff", 0.5, 0.0))
        me.materials.append(make_mat(name, hexcol, r, mt))
    if bbox is not None:
        lo, hi = np.array(bbox[:3]), np.array(bbox[3:])
    center = (lo + hi) / 2
    # ---- diorama base + studio floor
    cx, cy = center[0], center[1]
    if lawn:
        W = (hi[0] - lo[0]) + 90
        D = (hi[1] - lo[1]) + 90
        bpy.ops.mesh.primitive_cube_add(size=1, location=(cx, cy + 5, -2.0))
        base = bpy.context.active_object
        base.scale = (W, D, 4.0)
        gm = bpy.data.materials.new("lawn")
        gm.use_nodes = True
        nt = gm.node_tree
        bs = nt.nodes["Principled BSDF"]
        bs.inputs["Roughness"].default_value = 0.95
        noise = nt.nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = 2.5
        noise.inputs["Detail"].default_value = 12
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].color = srgb_to_lin("#3f5a26")
        ramp.color_ramp.elements[1].color = srgb_to_lin("#6f8a3a")
        nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
        nt.links.new(ramp.outputs["Color"], bs.inputs["Base Color"])
        bump = nt.nodes.new("ShaderNodeBump")
        n2 = nt.nodes.new("ShaderNodeTexNoise")
        n2.inputs["Scale"].default_value = 40
        nt.links.new(n2.outputs["Fac"], bump.inputs["Height"])
        bump.inputs["Strength"].default_value = 0.6
        nt.links.new(bump.outputs["Normal"], bs.inputs["Normal"])
        base.data.materials.append(gm)
    if lawn and WALK:
        # walkway from the front steps: WALK = (x centre, y of the step front, width)
        sx, y_front, ww = WALK
        walk_len = y_front - (cy + 5 - D / 2)
        bpy.ops.mesh.primitive_cube_add(size=1, location=(sx, (cy + 5 - D / 2) + walk_len / 2, 0.15))
        wk = bpy.context.active_object
        wk.scale = (ww, walk_len, 0.3)
        wm = bpy.data.materials.new("walk")
        wm.use_nodes = True
        wm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = srgb_to_lin("#a39f95")
        wm.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.9
        wk.data.materials.append(wm)
    bpy.ops.mesh.primitive_plane_add(size=6000, location=(cx, cy, -4.0 if lawn else lo[2] - 0.01))
    fl = bpy.context.active_object
    fm = bpy.data.materials.new("floor")
    fm.use_nodes = True
    fm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = srgb_to_lin("#5d6064")
    fm.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.7
    fl.data.materials.append(fm)
    fl.is_shadow_catcher = True
    # ---- world + lights
    world = bpy.data.worlds.new("w")
    sc.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = srgb_to_lin("#b8c4d0")
    bg.inputs["Strength"].default_value = 0.55
    sun = bpy.data.lights.new("sun", "SUN")
    sun.energy = 3.2
    sun.angle = math.radians(3.0)
    sun.color = (1.0, 0.96, 0.9)
    so = bpy.data.objects.new("sun", sun)
    sc.collection.objects.link(so)
    so.rotation_euler = (math.radians(50), 0, math.radians(-35))
    so["is_key"] = True
    fill = bpy.data.lights.new("fill", "AREA")
    fill.energy = 4.0e6
    fill.size = 600
    fo = bpy.data.objects.new("fill", fill)
    sc.collection.objects.link(fo)
    fo.location = (cx + 500, cy - 700, 500)
    fo.rotation_euler = Vector((cx, cy, 60)) - fo.location
    fo.rotation_euler = (Vector((cx, cy, 60)) - fo.location).to_track_quat("-Z", "Y").to_euler()
    return lo, hi


def set_camera(lo, hi, view):
    spec = VIEWS[view]
    az, el, lens, margin, toff = spec[:5]
    sc = bpy.context.scene
    if margin is None:
        center = np.array(toff, float)
    else:
        center = (lo + hi) / 2 + np.array(toff)
        radius = np.linalg.norm(hi - lo) / 2 * margin
    cam = bpy.data.cameras.new("cam_" + view)
    cam.lens = lens
    cam.sensor_width = 36
    cam.clip_start = 1
    cam.clip_end = 20000
    fov = 2 * math.atan(18 / lens)
    dist = spec[5] if margin is None else radius / math.sin(fov / 2 * 0.72)
    a = math.radians(az)
    e = math.radians(el)
    d = np.array([math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)])
    loc = center + d * dist
    co = bpy.data.objects.new("cam_" + view, cam)
    sc.collection.objects.link(co)
    co.location = Vector(loc)
    co.rotation_euler = (Vector(center) - co.location).to_track_quat("-Z", "Y").to_euler()
    sc.camera = co
    # key light from camera-left and above; fill from camera-right
    ka = a - math.radians(45)
    L = Vector((math.sin(ka) * math.cos(math.radians(48)), -math.cos(ka) * math.cos(math.radians(48)), math.sin(math.radians(48))))
    sun = bpy.data.objects["sun"]
    sun.rotation_euler = L.to_track_quat("Z", "Y").to_euler()
    fo = bpy.data.objects["fill"]
    fa = a + math.radians(70)
    fo.location = Vector((center[0] + math.sin(fa) * 900, center[1] - math.cos(fa) * 900, 500))
    fo.rotation_euler = (Vector(center) - fo.location).to_track_quat("-Z", "Y").to_euler()
    return co


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--samples", type=int, default=64)
    ap.add_argument("--res", default="1600x1100")
    ap.add_argument("--views", default="hero")
    ap.add_argument("--npz", default=os.path.join(HERE, "..", "out", "house_parts.npz"))
    ap.add_argument("--out", default=os.path.join(HERE, "..", "renders"))
    ap.add_argument("--bbox", default=None, help="x0,y0,z0,x1,y1,z1 to fix framing")
    ap.add_argument("--palette", default=None,
                    help="JSON: {materials: {name: [hex, rough, metal]}, views: {...}, walk: [x, y_front, width]}")
    ap.add_argument("--ground", default="lawn", choices=["lawn", "none"])
    ap.add_argument("--labels", default=None,
                    help="JSON {name: [x, y, z]}: write <view>_labels.json with each point's pixel position")
    args = ap.parse_args()
    global WALK
    if args.palette:
        cfg = json.load(open(args.palette))
        WALK = cfg.get("walk", WALK)
        for k, v in cfg.get("materials", {}).items():
            PALETTE[k] = tuple(v)
        for k, v in cfg.get("views", {}).items():
            v = list(v)
            v[4] = tuple(v[4])
            VIEWS[k] = tuple(v)
    os.makedirs(args.out, exist_ok=True)
    bbox = [float(v) for v in args.bbox.split(",")] if args.bbox else None
    lo, hi = build_scene(args.npz, lawn=args.ground == "lawn", bbox=bbox)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = args.samples
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 6
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast"
    rx, ry = (int(x) for x in args.res.split("x"))
    sc.render.resolution_x = rx
    sc.render.resolution_y = ry
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    sc.render.film_transparent = True
    for v in args.views.split(","):
        set_camera(lo, hi, v)
        sc.render.filepath = os.path.join(args.out, f"{v}.png")
        bpy.ops.render.render(write_still=True)
        backdrop(sc.render.filepath)
        if args.labels:
            from bpy_extras.object_utils import world_to_camera_view
            pts = json.load(open(args.labels))
            pix = {}
            for k, p in pts.items():
                c = world_to_camera_view(sc, sc.camera, Vector(p))
                pix[k] = [c.x * rx, (1.0 - c.y) * ry, c.z]
            json.dump(pix, open(os.path.join(args.out, f"{v}_labels.json"), "w"), indent=1)
        print("rendered", v)


def backdrop(path):
    """Composite the transparent render over a soft studio gradient."""
    from PIL import Image
    im = Image.open(path).convert("RGBA")
    w, h = im.size
    y = np.linspace(0, 1, h)[:, None]
    x = np.linspace(-1, 1, w)[None, :]
    top = np.array([0.93, 0.93, 0.94])
    bot = np.array([0.78, 0.79, 0.80])
    g = top[None, None, :] * (1 - y[..., None]) + bot[None, None, :] * y[..., None]
    g = g * (1 - 0.10 * (x[..., None] ** 2))
    bg = Image.fromarray((np.clip(g, 0, 1) * 255).astype(np.uint8), "RGB").convert("RGBA")
    bg.alpha_composite(im)
    bg.convert("RGB").save(path)


if __name__ == "__main__":
    main()

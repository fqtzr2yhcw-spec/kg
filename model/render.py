#!/usr/bin/env python3
"""Headless Blender presentation renders of the Empire State Building model.
Run:  blender -b -P render.py
Produces:
  render.png         - assembled sections, day, limestone + lit crown
  render_crown.png   - crown / mooring-mast close-up
  render_night.png   - night, glowing crown
  render_panels.png  - the 4 wall plates of one tower band, exploded
"""
import bpy, os, math, glob
from mathutils import Vector

D = os.path.dirname(os.path.abspath(__file__))

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    try: bpy.ops.preferences.addon_enable(module="io_mesh_stl")
    except Exception: pass

def imp(path, name, smooth=False):
    bpy.ops.import_mesh.stl(filepath=path)
    o = bpy.context.selected_objects[0]; o.name = name
    if smooth:
        for p in o.data.polygons: p.use_smooth = True
    return o

def limestone():
    m = bpy.data.materials.new("limestone"); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.83, 0.80, 0.72, 1)
    b.inputs["Roughness"].default_value = 0.78
    tex = nt.nodes.new("ShaderNodeTexNoise")
    tex.inputs["Scale"].default_value = 60; tex.inputs["Detail"].default_value = 5
    bump = nt.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.18
    nt.links.new(tex.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"]); return m

def mat(name, color, rough=0.5, metal=0.0, emis=None, emis_str=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough; b.inputs["Metallic"].default_value = metal
    if emis is not None:
        for k in ("Emission Color", "Emission"):
            if k in b.inputs: b.inputs[k].default_value = (*emis, 1); break
        if "Emission Strength" in b.inputs: b.inputs["Emission Strength"].default_value = emis_str
    return m

def world_and_light(night=False):
    def sun(name, e, rot):
        d = bpy.data.lights.new(name, 'SUN'); d.energy = e
        o = bpy.data.objects.new(name, d); o.rotation_euler = [math.radians(a) for a in rot]
        bpy.context.scene.collection.objects.link(o)
    if night:
        sun("moon", 0.5, (58, 0, 30)); amb = (0.03, 0.04, 0.08, 1); strength = 0.12
    else:
        sun("key", 4.0, (52, 0, 35)); sun("fill", 1.3, (66, 0, -120))
        amb = (0.60, 0.66, 0.77, 1); strength = 0.55
    w = bpy.data.worlds.new("W"); w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = amb
    w.node_tree.nodes["Background"].inputs[1].default_value = strength
    bpy.context.scene.world = w

def ground(dark=False):
    bpy.ops.mesh.primitive_plane_add(size=9000, location=(0, 0, 0))
    c = (0.05, 0.05, 0.06) if dark else (0.15, 0.15, 0.16)
    bpy.context.active_object.data.materials.append(mat("ground", c, 0.95))

def setup_tower(night=False):
    reset()
    lime = limestone()
    crown = mat("crown", (0.86, 0.68, 0.32), rough=0.34, metal=0.7,
                emis=(1.0, 0.82, 0.45), emis_str=(7.0 if night else 0.8))
    steel = mat("spire", (0.72, 0.74, 0.77), rough=0.35, metal=0.9,
                emis=(0.8, 0.85, 1.0), emis_str=(2.0 if night else 0.0))
    files = [f for f in sorted(glob.glob(os.path.join(D, "stl", "0*_*.stl")))
             if "full_assembly" not in f]
    for f in files:
        n = os.path.splitext(os.path.basename(f))[0]
        o = imp(f, n, smooth=("crown" in n or "spire" in n))
        o.data.materials.clear()
        o.data.materials.append(crown if "crown" in n else steel if "spire" in n else lime)
    ground(dark=night); world_and_light(night)

def set_cam(loc, target, fov):
    cd = bpy.data.cameras.new("Cam"); cd.angle = math.radians(fov)
    cd.clip_start = 1.0; cd.clip_end = 1_000_000       # model can sit far from origin
    c = bpy.data.objects.new("Cam", cd); c.location = Vector(loc)
    c.rotation_euler = (Vector(target) - c.location).to_track_quat('-Z', 'Y').to_euler()
    bpy.context.scene.collection.objects.link(c); bpy.context.scene.camera = c

def render(path, rx, ry, samples):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
    sc.cycles.samples = samples; sc.cycles.use_denoising = False
    sc.cycles.sample_clamp_indirect = 5.0
    sc.render.resolution_x = rx; sc.render.resolution_y = ry
    sc.render.filepath = os.path.join(D, path); bpy.ops.render.render(write_still=True)
    print("rendered ->", path)

def panels():
    reset(); lime = limestone()
    off = 70; shift = {"east": (off, 0, 0), "west": (-off, 0, 0), "north": (0, off, 0), "south": (0, -off, 0)}
    for face in ["east", "west", "north", "south"]:
        p = os.path.join(D, "stl_panels", "lower_" + face + ".stl")
        if not os.path.exists(p): continue
        o = imp(p, "lower_" + face); o.location = Vector(shift[face])
        o.data.materials.clear(); o.data.materials.append(lime)
    ground(); world_and_light(); set_cam((330, -430, 210), (0, 0, 136), 44)
    render("render_panels.png", 1100, 850, 160)

if __name__ == "__main__":
    # camera framed for the 1:500 model (~886mm tip). Single hero render to save usage.
    setup_tower(night=False)
    set_cam((830, -1181, 671), (0, 0, 444), 39); render("render.png", 900, 1350, 170)

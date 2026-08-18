#!/usr/bin/env python3
"""Headless Blender render of the sectioned Empire State Building model.
Run:  blender -b -P render.py
Imports the section STLs, applies limestone / lit-crown materials, lights and
frames the assembled tower, and writes render.png next to this script.
"""
import bpy, os, math
from mathutils import Vector

D = os.path.dirname(os.path.abspath(__file__))
STL_DIR = os.path.join(D, "stl")
OUT = os.path.join(D, "render.png")

bpy.ops.wm.read_factory_settings(use_empty=True)
try:
    bpy.ops.preferences.addon_enable(module="io_mesh_stl")
except Exception:
    pass

SECTIONS = ["01_base", "02_shaft_lower", "03_shaft_upper",
            "04_setbacks", "05_crown", "06_spire"]

objs = []
for n in SECTIONS:
    bpy.ops.import_mesh.stl(filepath=os.path.join(STL_DIR, n + ".stl"))
    o = bpy.context.selected_objects[0]
    o.name = n
    # smooth-shade only the round crown/spire; keep the masonry crisp
    if n in ("05_crown", "06_spire"):
        for poly in o.data.polygons:
            poly.use_smooth = True
    objs.append(o)


def make_mat(name, color, rough=0.7, metal=0.0, emis=None, emis_str=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emis is not None:
        for k in ("Emission Color", "Emission"):
            if k in b.inputs:
                b.inputs[k].default_value = (*emis, 1); break
        if "Emission Strength" in b.inputs:
            b.inputs["Emission Strength"].default_value = emis_str
    return m

limestone = make_mat("limestone", (0.82, 0.79, 0.71), rough=0.72)
crown_mat = make_mat("crown", (0.86, 0.68, 0.30), rough=0.32, metal=0.85,
                     emis=(1.0, 0.80, 0.42), emis_str=2.2)
metal_mat = make_mat("spire", (0.72, 0.74, 0.77), rough=0.35, metal=0.9)

for o in objs:
    o.data.materials.clear()
    o.data.materials.append(crown_mat if o.name == "05_crown"
                            else metal_mat if o.name == "06_spire"
                            else limestone)

# ground
bpy.ops.mesh.primitive_plane_add(size=8000, location=(0, 0, 0))
bpy.context.active_object.data.materials.append(
    make_mat("ground", (0.16, 0.16, 0.17), rough=0.95))

# lighting: key + fill suns (scale-independent) + soft world ambient
def sun(name, energy, rot):
    d = bpy.data.lights.new(name, 'SUN'); d.energy = energy
    o = bpy.data.objects.new(name, d)
    o.rotation_euler = [math.radians(a) for a in rot]
    bpy.context.scene.collection.objects.link(o)
sun("key", 4.0, (52, 0, 35))
sun("fill", 1.3, (66, 0, -120))
world = bpy.data.worlds.new("W"); world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.62, 0.68, 0.78, 1)
world.node_tree.nodes["Background"].inputs[1].default_value = 0.55
bpy.context.scene.world = world

# camera framed on the tower
target = Vector((0, 0, 291))
cam_data = bpy.data.cameras.new("Cam"); cam_data.angle = math.radians(39)
cam = bpy.data.objects.new("Cam", cam_data)
cam.location = Vector((545, -775, 440))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
bpy.context.scene.collection.objects.link(cam)
bpy.context.scene.camera = cam

# render
sc = bpy.context.scene
sc.render.engine = 'CYCLES'
sc.cycles.device = 'CPU'
sc.cycles.samples = 180                 # no denoiser in this build -> more samples
sc.cycles.use_denoising = False
sc.cycles.sample_clamp_indirect = 5.0   # kill fireflies
sc.render.resolution_x = 900
sc.render.resolution_y = 1350
sc.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print("rendered ->", OUT)

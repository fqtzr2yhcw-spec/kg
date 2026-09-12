#!/usr/bin/env python3
"""Blender render of the extreme-detail facade panel.  blender -b -P facade_render.py"""
import bpy, os, math
from mathutils import Vector
D = os.path.dirname(os.path.abspath(__file__))

bpy.ops.wm.read_factory_settings(use_empty=True)
try: bpy.ops.preferences.addon_enable(module="io_mesh_stl")
except Exception: pass

bpy.ops.import_mesh.stl(filepath=os.path.join(D, "stl", "facade_panel.stl"))
o = bpy.context.selected_objects[0]
o.rotation_euler = (math.radians(90), 0, 0)          # stand the wall up
bpy.context.view_layer.update()

# limestone with procedural masonry bump
m = bpy.data.materials.new("limestone"); m.use_nodes = True
nt = m.node_tree; b = nt.nodes["Principled BSDF"]
b.inputs["Base Color"].default_value = (0.84, 0.81, 0.73, 1)
b.inputs["Roughness"].default_value = 0.8
tex = nt.nodes.new("ShaderNodeTexNoise")
tex.inputs["Scale"].default_value = 120; tex.inputs["Detail"].default_value = 6
bump = nt.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.25
nt.links.new(tex.outputs["Fac"], bump.inputs["Height"]); nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
o.data.materials.clear(); o.data.materials.append(m)

# frame the object
c = o.location + Vector((o.dimensions.x*0, 0, 0))
bb = [o.matrix_world @ Vector(v) for v in o.bound_box]
ctr = sum(bb, Vector((0, 0, 0))) / 8
size = max((max(p[i] for p in bb) - min(p[i] for p in bb)) for i in range(3))

# raking key light + soft fill
def sun(name, e, rot):
    d = bpy.data.lights.new(name, 'SUN'); d.energy = e
    ob = bpy.data.objects.new(name, d); ob.rotation_euler = [math.radians(a) for a in rot]
    bpy.context.scene.collection.objects.link(ob)
sun("key", 3.2, (62, 0, 28)); sun("fill", 1.0, (70, 0, -140))
w = bpy.data.worlds.new("W"); w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.62, 0.67, 0.75, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 0.5
bpy.context.scene.world = w

cd = bpy.data.cameras.new("Cam"); cd.angle = math.radians(35)
cam = bpy.data.objects.new("Cam", cd)
cam.location = ctr + Vector((size*0.32, -size*1.5, size*0.20))
cam.rotation_euler = (ctr - cam.location).to_track_quat('-Z', 'Y').to_euler()
bpy.context.scene.collection.objects.link(cam); bpy.context.scene.camera = cam

sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
sc.cycles.samples = 200; sc.cycles.use_denoising = False; sc.cycles.sample_clamp_indirect = 5.0
sc.render.resolution_x = 1100; sc.render.resolution_y = 1150
sc.render.filepath = os.path.join(D, "render_facade.png")
bpy.ops.render.render(write_still=True)
print("rendered -> render_facade.png")

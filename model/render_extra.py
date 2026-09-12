#!/usr/bin/env python3
"""Extra views of the model: night (lit crown) + crown close-up.
Run:  blender -b -P render_extra.py   (auto-frames at any scale)"""
import sys
sys.path.insert(0, "/home/user/kg/model")
import bpy
from mathutils import Vector
import render as R

def bounds():
    objs = [o for o in bpy.data.objects if o.type == 'MESH' and o.name != 'Plane']
    mn = Vector((1e18, 1e18, 1e18)); mx = Vector((-1e18, -1e18, -1e18))
    for o in objs:
        for v in o.bound_box:
            w = o.matrix_world @ Vector(v)
            for i in range(3):
                mn[i] = min(mn[i], w[i]); mx[i] = max(mx[i], w[i])
    return mn, mx

# --- night, full tower, glowing crown ---
R.setup_tower(night=True)
mn, mx = bounds(); ctr = (mn + mx) * 0.5; H = mx[2] - mn[2]; d = 1.6 * H
R.set_cam((ctr[0] + 0.5*d, ctr[1] - 0.8*d, ctr[2] + 0.28*d), (ctr[0], ctr[1], ctr[2]), 39)
R.render("render_night.png", 900, 1350, 200)

# --- day, crown / mooring-mast close-up ---
R.setup_tower(night=False)
mn, mx = bounds(); H = mx[2] - mn[2]
tgt = Vector((0, 0, mx[2] - 0.17 * H)); d = 0.55 * H
R.set_cam((tgt[0] + 0.45*d, tgt[1] - 0.9*d, tgt[2] + 0.16*d), (tgt[0], tgt[1], tgt[2]), 33)
R.render("render_crown.png", 900, 1100, 200)

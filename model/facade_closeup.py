#!/usr/bin/env python3
"""Close-up of the 1:350 tower facade (the broad face, mid-shaft).
Run:  blender -b -P facade_closeup.py"""
import sys
sys.path.insert(0, "/home/user/kg/model")
import bpy  # noqa
import render as R

R.setup_tower(night=False)
# camera up close on the +X broad face, mid-shaft
R.set_cam((300, -55, 360), (20, 0, 335), 20)
R.render("render_facade_closeup.png", 1100, 1100, 240)

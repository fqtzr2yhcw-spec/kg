"""The Stonehaven Tunnel Portals: an original pair of HO-scale (1:87.1) single-track tunnel portals
in cut stone, building 72 (the engine terminal batch).

Each portal is rock-faced ashlar between rock-faced pilasters on a plinth of big stones. The arch,
60 mm wide and 82 mm high at the crown (clear for tall freight cars), is ringed with fifteen
smooth-dressed voussoirs and a tall keystone on moulded imposts, over long-and-short jamb
quoins. A cornice of bed mould, dentils, corona and coping runs across the top, and over the arch
a raised parapet carries the date 1893 on a beaded tablet. Behind each portal a 30 mm tunnel
lining jointed in the same courses; each side a wing wall with a plinth, a raking coping and a
capped end pier, cut to stand splayed 30 degrees from the face. Two of everything: one portal
for each end of the tunnel.

The hillside, track and ballast in the renders are scenery for the pictures, not parts.

usage: python3 -m hoarch.buildings.stonehaven [check] [export]
"""
import math
import os
import sys

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import box, poly, union
from hoarch import yard as YD
from hoarch.kit import Kit

NAME = "The Stonehaven Tunnel Portals"
COLORS = {"Stone": "#B3AA98"}
RENDER_MAT = {"Stone": "stone", "Letters": "letters"}
PALETTE = {"stone": ("#B3AA98", 0.92, 0.0), "letters": ("#8F8676", 0.9, 0.0), "hill": ("#5E6B3C", 0.98, 0.0),
           "earth": ("#6E5C45", 0.97, 0.0), "ballast": ("#8C877E", 0.97, 0.0), "ties": ("#3F3328", 0.9, 0.0),
           "rail": ("#77716A", 0.35, 0.8)}
VIEWS = {"hero": [-30, 12, 60, 0.95, [0, 0, 0]], "front": [0, 5, 70, 0.92, [0, 0, 0]], "rear": [150, 22, 60, 0.95, [0, 0, 0]]}

T = 4.0                          # the portal's plate
OW, SPRING = 60.0, 52.0          # the arch: width, springing
H = 100.0                        # the cornice's top
DEPTH = 30.0                     # the lining
TH = math.radians(30.0)          # the wing walls' splay from the face
LW, H0, H1 = 76.0, 86.0, 26.0    # the wing walls: length, height at the portal, at the far end
FAR = 400.0                      # the second set stands off to the side (a separate print)


def _portal_frame(dx=0.0):
    """(u, v, w) -> world: the face toward -y, its plane at y = 0."""
    return np.array([[1.0, 0.0, 0.0, dx], [0.0, 0.0, -1.0, 0.0], [0.0, 1.0, 0.0, 0.0]])


def _wing_frame(side, dx=0.0):
    """The wing's (u, v, w) -> world: u along the wall away from the portal, w out of its face,
    splayed TH forward from the portal's face; its face plane meets the portal's side at the
    point that puts its back on the portal's back."""
    c, s = math.cos(TH), math.sin(TH)
    y0 = T - T / c                                     # where the wing's face plane crosses the portal's side
    if side > 0:
        u, w = (c, -s), (-s, -c)
    else:
        u, w = (c, s), (s, -c)
    x0 = side * (140.0 / 2)
    return np.array([[u[0], 0.0, w[0], x0 + dx], [u[1], 0.0, w[1], y0], [0.0, 1.0, 0.0, 0.0]])


def _P(A):
    return np.column_stack([np.vstack([A[:, 0], A[:, 1], A[:, 2]]), np.zeros(3)])


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    portal, opening, letters = YD.portal_stone(140.0, H, OW, SPRING, T, "1893", seed=3)
    liner = YD.liner_stone(opening, DEPTH, 2.4, spring=SPRING, r0=OW / 2)
    wings = {s: YD.wing_stone(LW, H0, H1, T, side=s, seed=11 if s > 0 else 17) for s in (1, -1)}
    for tag, dx in (("A", 0.0), ("B", FAR)):
        A = _portal_frame(dx)
        kit.add(f"PORTAL-{tag}", "Stone", portal.transform(A), P=_P(A), key="PORTAL", group="portal",
                render=[("Stone", (portal - letters).transform(A)), ("Letters", letters.transform(A))])
        Al = _portal_frame(dx)
        Al[:, 3] = Al[:, 3] + Al[:, 2] * (-T)             # behind the plate
        Pl = np.array([[1.0, 0.0, 0.0, 0.0], [0.0, 0.0, -1.0, 0.0], [0.0, 1.0, 0.0, 0.0]])
        kit.add(f"LINER-{tag}", "Stone", liner.transform(Al), P=Pl, key="LINER", group="liner")
        for s in (1, -1):
            Aw = _wing_frame(s, dx)
            wm = wings[s].transform(Aw)
            cut = box([-1e3, -1e3, -10], [s * 70.0 + dx, 1e3, 300]) if s > 0 else box([s * 70.0 + dx, -1e3, -10], [1e3, 1e3, 300])
            wm = wm - cut
            kit.add(f"WING-{'R' if s > 0 else 'L'}-{tag}", "Stone", wm, P=_P(Aw), key=f"WING-{'R' if s > 0 else 'L'}", group="wings")
    return kit


def scenery():
    """Render-only: a hillside the portal is set into, the tunnel through it, ballast, ties and
    rails running in under the arch."""
    def lumps(p):
        x, y, z = p[:, 0], p[:, 1], p[:, 2]
        k = np.clip(z / 40.0, 0.0, 1.0)
        dz = k * (4.0 * np.sin(x / 23.0) * np.cos(y / 31.0) + 2.5 * np.sin(x / 11.0 + y / 17.0) + 1.5 * np.cos(x / 7.0 - y / 9.0))
        return np.column_stack([x, y, z + dz])

    hill = M.sphere(1.0, 128).scale([168.0, 135.0, 80.0]).translate([0.0, 112.0, 32.0]).warp_batch(lumps)
    c, s = math.cos(TH), math.sin(TH)
    back = [(-400, 500), (-400, T - (LW + 8) * s), (-70 - (LW + 8) * c, T - (LW + 8) * s), (-70.0, T), (70.0, T),
            (70 + (LW + 8) * c, T - (LW + 8) * s), (400, T - (LW + 8) * s), (400, 500)]
    zone = M.extrude(poly(back), 400.0).translate([0, 0, -10])
    tunnel = M.extrude(YD.O.opening_cs(OW, SPRING + OW / 2, OW / 2), 140.0).transform(
        np.array([[1.0, 0, 0, 0], [0, 0, 1.0, -5.0], [0, 1.0, 0, 0]]))
    hill = (hill ^ zone) - tunnel - box([-500, -500, -50], [500, 500, 0.0])
    hill = hill ^ box([-200, -200, -1], [200, 175, 400])
    ballast = M.hull_points([(x, y, z) for y in (-150.0, 60.0) for (x, z) in ((-19.0, 0.0), (19.0, 0.0), (-14.0, 3.0), (14.0, 3.0))])
    ties = union([box([-14.9, y - 1.3, 3.0], [14.9, y + 1.3, 5.0]) for y in np.arange(-148.0, 58.0, 6.4)])
    rails = union([box([x - 0.45, -150.0, 5.0], [x + 0.45, 60.0, 7.1]) for x in (-8.7, 8.7)])
    return {"hill": hill, "ballast": ballast, "ties": ties, "rail": rails}


def add_scenery(npz_path, hill=True):
    from hoarch.kit import mesh_arrays
    data = dict(np.load(npz_path))
    for name, m in scenery().items():
        if name == "hill" and not hill:
            continue
        v, f = mesh_arrays(m)
        data[name + "__v"] = v.astype(np.float32)
        data[name + "__f"] = f.astype(np.int32)
    np.savez_compressed(npz_path, **data)


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "stonehaven")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:80]:
            print("  ", b)
        print("bed:", kit.bed_check())
    npz = os.path.join(OUT, "stonehaven.npz")
    kit.render_npz(npz, only=lambda p: p.name.endswith("-A"))
    add_scenery(npz)
    bare = os.path.join(OUT, "stonehaven_bare.npz")          # the rear view: the parts' backs, no hillside
    kit.render_npz(bare, only=lambda p: p.name.endswith("-A"))
    add_scenery(bare, hill=False)
    import json
    json.dump({"materials": {k: list(v) for k, v in PALETTE.items()}, "views": VIEWS},
              open(os.path.join(OUT, "palette.json"), "w"), indent=1)
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2)

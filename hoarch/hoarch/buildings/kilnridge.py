"""The Kiln Ridge Tunnel Portals: an original pair of HO-scale (1:87.1) double-track tunnel portals
in brick with stone dressings, building 78 (the engine terminal batch).

Each portal is red brick in Flemish bond, its dark headers standing a little proud, on a stone
base course. The segmental arch, 112 mm wide and 80 mm high at the crown for two tracks at 51 mm
centres, is turned in three rowlock rings stepping back from the opening, on stone springers,
with a tall stone keystone lettered No 7; a stone impost band runs across the face at the
springing, stone quoins climb the end piers, and a corbelled brick cornice carries a stone
coping under a stepped parapet with a stone roundel. Behind each portal a 30 mm brick-coursed
lining; each side a wing wall stepping down in three stages under stone copings to a quoined
pier, cut to stand splayed 30 degrees from the face. Two of everything: one portal for each end
of the tunnel.

The hillside, track and ballast in the renders are scenery for the pictures, not parts.

usage: python3 -m hoarch.buildings.kilnridge [check] [export]
"""
import math
import os
import sys

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import box, poly, union
from hoarch import yard as YD
from hoarch.kit import Kit

NAME = "The Kiln Ridge Tunnel Portals"
COLORS = {"Brick": "#8B3A2A", "Stone": "#B9AF98"}
RENDER_MAT = {"Brick": "brick", "Stone": "stone", "Letters": "letters"}
PALETTE = {"brick": ("#8B3A2A", 0.9, 0.0), "stone": ("#B9AF98", 0.9, 0.0), "letters": ("#6E5F4A", 0.9, 0.0), "hill": ("#5E6B3C", 0.98, 0.0),
           "earth": ("#6E5C45", 0.97, 0.0), "ballast": ("#8C877E", 0.97, 0.0), "ties": ("#3F3328", 0.9, 0.0),
           "rail": ("#77716A", 0.35, 0.8)}
VIEWS = {"hero": [-30, 12, 60, 0.95, [0, 0, 0]], "front": [0, 5, 70, 0.92, [0, 0, 0]], "rear": [150, 22, 60, 0.95, [0, 0, 0]]}

T = 4.0                          # the portal's plate
OW, SPRING, RISE = 112.0, 50.0, 30.0   # the arch: width, springing, rise
H = 100.0                        # the cornice's top
DEPTH = 30.0                     # the lining
TH = math.radians(30.0)          # the wing walls' splay from the face
LW, H0 = 70.0, 86.0             # the wing walls: length, height at the portal
PW = 180.0                       # the portal's width
FAR = 400.0
STONE_W = 1.0                    # the stone dressings print in stone colour above this (one filament change)                      # the second set stands off to the side (a separate print)


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
    x0 = side * (PW / 2)
    return np.array([[u[0], 0.0, w[0], x0 + dx], [u[1], 0.0, w[1], y0], [0.0, 1.0, 0.0, 0.0]])


def _P(A):
    return np.column_stack([np.vstack([A[:, 0], A[:, 1], A[:, 2]]), np.zeros(3)])


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    portal, opening, letters = YD.portal_brick(PW, H, OW, SPRING, RISE, T, "No 7")
    liner = YD.liner_brick(opening, DEPTH, 2.4)
    wings = {s: YD.wing_brick(LW, H0, T, side=s) for s in (1, -1)}
    for tag, dx in (("A", 0.0), ("B", FAR)):
        A = _portal_frame(dx)
        hi = YD.ext(YD.rect(-500, -50, 500, 500), STONE_W, 50.0)
        kit.add(f"PORTAL-{tag}", "Brick", portal.transform(A), P=_P(A), key="PORTAL", group="portal", change=(T + STONE_W, "Stone"),
                render=[("Brick", (portal - hi).transform(A)), ("Stone", (portal ^ hi - letters).transform(A)), ("Letters", letters.transform(A))])
        Al = _portal_frame(dx)
        Al[:, 3] = Al[:, 3] + Al[:, 2] * (-T)             # behind the plate
        Pl = np.array([[1.0, 0.0, 0.0, 0.0], [0.0, 0.0, -1.0, 0.0], [0.0, 1.0, 0.0, 0.0]])
        kit.add(f"LINER-{tag}", "Brick", liner.transform(Al), P=Pl, key="LINER", group="liner")
        for s in (1, -1):
            Aw = _wing_frame(s, dx)
            wl_ = wings[s]
            whi = (wl_ ^ YD.ext(YD.rect(-500, -50, 500, 500), STONE_W, 50.0)).transform(Aw)
            wm = wl_.transform(Aw)
            cut = box([-1e3, -1e3, -10], [s * PW / 2 + dx, 1e3, 300]) if s > 0 else box([s * PW / 2 + dx, -1e3, -10], [1e3, 1e3, 300])
            wm = wm - cut
            kit.add(f"WING-{'R' if s > 0 else 'L'}-{tag}", "Brick", wm, P=_P(Aw), key=f"WING-{'R' if s > 0 else 'L'}", group="wings",
                    change=(T + STONE_W, "Stone"), render=[("Brick", wm - whi), ("Stone", wm ^ whi)])
    return kit


def scenery():
    """Render-only: a hillside the portal is set into, the tunnel through it, ballast, ties and
    rails running in under the arch."""
    def lumps(p):
        x, y, z = p[:, 0], p[:, 1], p[:, 2]
        k = np.clip(z / 40.0, 0.0, 1.0)
        dz = k * (4.0 * np.sin(x / 23.0) * np.cos(y / 31.0) + 2.5 * np.sin(x / 11.0 + y / 17.0) + 1.5 * np.cos(x / 7.0 - y / 9.0))
        return np.column_stack([x, y, z + dz])

    hill = M.sphere(1.0, 128).scale([205.0, 140.0, 82.0]).translate([0.0, 115.0, 32.0]).warp_batch(lumps)
    c, s = math.cos(TH), math.sin(TH)
    back = [(-400, 500), (-400, T - (LW + 8) * s), (-PW / 2 - (LW + 8) * c, T - (LW + 8) * s), (-PW / 2, T), (PW / 2, T),
            (PW / 2 + (LW + 8) * c, T - (LW + 8) * s), (400, T - (LW + 8) * s), (400, 500)]
    zone = M.extrude(poly(back), 400.0).translate([0, 0, -10])
    tunnel = M.extrude(YD.O.opening_cs(OW, SPRING + RISE, RISE), 140.0).transform(
        np.array([[1.0, 0, 0, 0], [0, 0, 1.0, -5.0], [0, 1.0, 0, 0]]))
    hill = (hill ^ zone) - tunnel - box([-500, -500, -50], [500, 500, 0.0])
    hill = hill ^ box([-240, -200, -1], [240, 180, 400])
    ballast = union([M.hull_points([(x + dx, y, z) for y in (-150.0, 60.0) for (dx, z) in ((-19.0, 0.0), (19.0, 0.0), (-14.0, 3.0), (14.0, 3.0))])
                     for x in (-25.5, 25.5)])
    ties = union([box([x - 14.9, y - 1.3, 3.0], [x + 14.9, y + 1.3, 5.0]) for x in (-25.5, 25.5) for y in np.arange(-148.0, 58.0, 6.4)])
    rails = union([box([x + sx - 0.45, -150.0, 5.0], [x + sx + 0.45, 60.0, 7.1]) for x in (-25.5, 25.5) for sx in (-8.7, 8.7)])
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
    OUT = os.path.join(HERE, "..", "..", "out", "kilnridge")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:80]:
            print("  ", b)
        print("bed:", kit.bed_check())
    npz = os.path.join(OUT, "kilnridge.npz")
    kit.render_npz(npz, only=lambda p: p.name.endswith("-A"))
    add_scenery(npz)
    bare = os.path.join(OUT, "kilnridge_bare.npz")          # the rear view: the parts' backs, no hillside
    kit.render_npz(bare, only=lambda p: p.name.endswith("-A"))
    add_scenery(bare, hill=False)
    import json
    json.dump({"materials": {k: list(v) for k, v in PALETTE.items()}, "views": VIEWS},
              open(os.path.join(OUT, "palette.json"), "w"), indent=1)
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2)

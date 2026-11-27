"""Floating regions (Bambu Studio's "has floating regions") in scenery packs and flatcar loads: every
piece, in its print orientation, layer by layer at its print layer (0.2 mm, 0.1 for the 0.2 nozzle loads). A patch of a layer with nothing under it
prints on air; the propane tanks' cradle webs between their openings were the case this was written
against. Fix every one before releasing.

usage: python3 tools/floatcheck.py [pack ...]    (no packs: all of them)
"""
import sys

import _common  # noqa: F401  (puts the project on the path)
from hoarch.lint import floating
from hoarch.packs import PACKS
from hoarch.loadnames import LAYER


def main(keys):
    bad = 0
    for k in keys:
        for pc in PACKS[k]["pieces"]:
            f = floating(pc["fn"](), LAYER.get(k, 0.2))
            if f:
                bad += 1
                print(f"{k:14s} {pc['name']:26s} {len(f)} floating: " +
                      "; ".join(f"z={z} {a} mm2 at {bb}" for z, a, bb in f[:4]), flush=True)
    print(f"pieces with floating regions: {bad}")
    return bad


if __name__ == "__main__":
    sys.exit(1 if main(sys.argv[1:] or list(PACKS)) else 0)

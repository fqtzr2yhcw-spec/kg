"""Glazing test plate: which window openings print clean on the owner's printers.

A 0.4 mm glass sheet (2 layers at 0.2) with the bars 0.8 mm over it (4 layers), printed as
the windows are: glass colour first, one filament change at 0.4 mm. Columns are slot widths
0.8, 1.0, 1.2, 1.4, 1.6 and 2.0 mm (raised numbers over each column); rows are slot lengths
2, 3, 4.5 and 6 mm (numbers on the left), three slots per cell between 0.5 mm bars like a
sash's muntins. The bottom row is lozenge lattice with openings 1.0, 1.3, 1.6 and 2.0 mm
across, 0.8 mm leads, for comparison with the Oakhurst's doors.

usage: python3 -m hoarch.glazetest [out_dir]   (writes Glazing_Test_Plate.3mf and .stl)"""
import math
import os
import sys

from manifold3d import JoinType

from .core import cs_union, poly, rect
from .kit import write_3mf, write_stl
from .ornament import ext
from .storefront import text_cs

GLASS, BARS = 0.4, 0.8
WIDTHS = (0.8, 1.0, 1.2, 1.4, 1.6, 2.0)
LENGTHS = (2.0, 3.0, 4.5, 6.0)
LOZ = (1.0, 1.3, 1.6, 2.0)
BAR, BORDER, PITCH, LEFT = 0.5, 1.0, 10.0, 7.0


def _label(s, u, v, cap=2.0):
    return text_cs(s, cap, "sans", grow=0.12).translate((u, v))


def _lozenge_cell(x0, y0, w, h, d, lead=0.8, ang=60.0):
    """Lozenges ``d`` across between ``lead`` wide leads, in a w x h light at (x0, y0)."""
    a = math.radians(ang)
    p = (d + lead) / math.sin(a)                     # spacing of the leads along the light's width
    leads = []
    L = (w + h) * 2
    for sgn in (1, -1):
        k0 = int(-(w + h) / p) - 2
        for k in range(k0, int((w + h) / p) + 3):
            c = x0 + k * p
            dx, dy = L * math.cos(a) * sgn, L * math.sin(a)
            pts = [(c - dx - lead / 2 / math.sin(a), y0 - dy), (c - dx + lead / 2 / math.sin(a), y0 - dy),
                   (c + dx + lead / 2 / math.sin(a), y0 + dy), (c + dx - lead / 2 / math.sin(a), y0 + dy)]
            leads.append(poly(pts if sgn > 0 else pts[::-1]))
    light = rect(x0, y0, x0 + w, y0 + h)
    return light - (cs_union(leads) ^ light)


def plate():
    openings, labels = [], []
    W = LEFT + PITCH * len(WIDTHS)
    y = 1.5
    # the lozenge row at the bottom
    lw, lh = 2 * PITCH - 3.0, 9.0
    for i, d in enumerate(LOZ):
        x0 = LEFT + i * PITCH * 1.5 + 0.5
        openings.append(_lozenge_cell(x0, y, PITCH * 1.5 - 2.5, lh, d))
        labels.append(_label(f"{d:g}", x0 + (PITCH * 1.5 - 2.5) / 2, y + lh + 0.7, 1.6))
    labels.append(_label("L", LEFT / 2, y + lh / 2 - 1.0))
    y += lh + 3.6
    for L in LENGTHS:
        for i, s in enumerate(WIDTHS):
            cx = LEFT + i * PITCH + PITCH / 2
            span = 3 * s + 2 * BAR
            for k in range(3):
                x = cx - span / 2 + k * (s + BAR)
                openings.append(rect(x, y, x + s, y + L))
        labels.append(_label(f"{L:g}", LEFT / 2, y + L / 2 - 1.0))
        y += L + 2.4
    for i, s in enumerate(WIDTHS):
        labels.append(_label(f"{s:g}", LEFT + i * PITCH + PITCH / 2, y - 0.4))
    H = y + 2.6
    sheet = rect(0.0, 0.0, W + 1.0, H)
    holes = cs_union(openings)
    body = ext(sheet, 0.0, GLASS) + ext(sheet - holes, GLASS - 0.01, GLASS + BARS)
    body = body + ext(cs_union(labels) ^ sheet.offset(-0.5, JoinType.Miter, 4.0), GLASS + BARS - 0.01, GLASS + BARS + 0.4)
    return body


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out")
    m = plate()
    write_3mf(os.path.join(out, "Glazing_Test_Plate.3mf"), [("Glazing_Test_Plate", m)], "Glazing test plate")
    write_stl(os.path.join(out, "Glazing_Test_Plate.stl"), m)
    b = m.bounding_box()
    print(f"{b[3] - b[0]:.1f} x {b[4] - b[1]:.1f} x {b[5] - b[2]:.2f} mm, volume {m.volume():.0f} mm3")

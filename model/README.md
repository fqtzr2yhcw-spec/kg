# Empire State Building — high-detail sectioned 3D-print model

A parametric, historically-grounded model of the Empire State Building (Shreve,
Lamb & Harmon, 1931), built for multi-printer sectioned printing. Every dimension
comes from the real building's massing and Art Deco facade grammar — not a
generative guess. Built with `trimesh`/`manifold3d`, rendered in Blender, with an
editable OpenSCAD twin.

| | |
|---|---|
| ![day](render.png) | ![night](render_night.png) |
| Day — limestone + lit crown | Night — the glowing mooring-mast crown |

## What's in here

| File | What it is |
|------|-----------|
| `empire_state_building.py` | Main generator — solid, sectioned model. Punched-window grid (paired windows + mullions), per-floor spandrel reveals, setback cornices, tiered ribbed crown. Auto-splits the tower to your printer bed height. |
| `empire_state_building.scad` | Editable **OpenSCAD** twin (massing + piers). `openscad -o esb.stl empire_state_building.scad`. |
| `wall_panels.py` | **4-wall-plate variant** — each tower band as 4 flat-backed facade plates that interlock at the corners (tab-and-slot) into a hollow ring. |
| `facade_detail.py` | **Extreme-detail facade panel** (large scale) — real windows (frame, mullion, divided lights, sill, lintel), Art Deco spandrels, and coursed running-bond masonry. |
| `render.py` / `facade_render.py` | Headless Blender renders (whole-building set; and the facade panel close-up). |
| `stl/` | 6 solid sections + full-assembly preview. |
| `stl_panels/` | 8 wall plates (2 tower bands × 4 walls). |

Regenerate: `python3 empire_state_building.py` · Panels: `python3 wall_panels.py` ·
Render: `blender -b -P render.py`. The repo's SessionStart hook installs OpenSCAD,
Blender and the Python libs automatically in Claude Code on the web.

## Print plan — solid sections (1:500 → ~886 mm / 2'11" assembled, Bambu P1S/P2S)

| # | File | W × D × H (mm) | Filament | Notes |
|---|------|----------------|----------|-------|
| 1 | `01_base_N.stl` | 125 × 132 × 77 | stone grey | north half of the base (arcade + cornice) |
| 2 | `01_base_S.stl` | 125 × 132 × 77 | stone grey | south half — joins base_N with dowel pins at the seam |
| 3 | `02_shaft_1of3.stl` | 80.5 × 128 × 182.5 | stone grey | punched window grid; print upright, **no supports** |
| 4 | `03_shaft_2of3.stl` | 80.5 × 128 × 182.5 | stone grey | print upright |
| 5 | `04_shaft_3of3.stl` | 80.5 × 128 × 182.5 | stone grey | print upright |
| 6 | `05_setbacks.stl` | 85.3 × 132.9 × 41.5 | stone grey | stepped cornices + 86th-fl deck |
| 7 | `06_crown.stl` | 58.5 × 58.5 × 123.1 | **translucent** | ribbed mast + lantern → LED-backlight showpiece |
| 8 | `07_spire.stl` | 12.2 × 12.2 × 119.5 | grey | slim antenna — brim it, or swap for a rod |

Every part fits the 256×256×256 bed. `00_full_assembly_preview.stl` = all sections
in place, for viewing only. The base halves join along the centre with two 3 mm
dowel pins (holes are built in).

### Change the scale / bed
`MM_PER_FT` sets the scale (`304.8/500` = 1:500; `0.40` ≈ 1:762 for a 23″ desk model;
`304.8/87` = HO 1:87). `MAX_PART_H_MM` is the bed height — the tower auto-splits into
that many bands, the base auto-splits in plan when its footprint exceeds the bed.

## Single- vs multi-color
The real building is essentially one color (Indiana limestone). The only truly
multi-color element is the illuminated crown at night — so print sections 1–4 + 6
in one stone filament across as many printers as you like, and print **section 5
in translucent** to backlight with an LED. All color management stays on one part.

## Two ways to build the tower walls
- **Solid sections** (`stl/`) — robust, simplest, relief on all four faces.
- **4 wall plates** (`stl_panels/`) — hollow-shell facade panels (N/S/E/W) that
  interlock at the corners; lighter, and each plate lies flat to show its masonry.

## Extreme-detail facade panels (large scale)
Individual masonry blocks and true window frames are physically smaller than a
printer can resolve at the whole-building scale (a limestone block is ~0.8 mm at
1:762). To get real masonry + real windows, model a **section of the elevation at
large scale**: `facade_detail.py` generates a parametric panel (default 3 bays ×
4 floors at ~1:95 → ~154 × 157 mm) with recessed windows (frame, central mullion,
divided lights, projecting sill, lintel), fluted Art Deco spandrels, and coursed
running-bond limestone. It prints flat (back down, relief up — no supports).
Raise `N_BAYS`/`N_FLOORS` or tile panels to cover a whole elevation, and set
`MM_PER_FT` for the scale you want to print.

`render_facade.png` is the Blender close-up.

## Assembly
Each section/plate has central alignment pins (peg on top / socket on bottom, and
corner splines on the plates). Dry-fit (≈ 0.6 mm clearance, glue-friendly), stack
base → shaft → setbacks → crown → spire, and bond seams with CA or epoxy.

# Empire State Building — sectioned 3D-print model

A parametric, historically-grounded model of the Empire State Building (Shreve,
Lamb & Harmon, 1931), built for multi-printer sectioned printing. Generated from
real massing and Art Deco facade grammar — not a generative guess.

![render](render.png)

## Files

| File | What it is |
|------|-----------|
| `empire_state_building.py` | The generator. Builds the solid, carves the facade, exports the section STLs + a matplotlib preview. |
| `render.py` | Headless Blender render (`blender -b -P render.py` → `render.png`). |
| `stl/*.stl` | The six printable sections + a full-assembly preview. |

Regenerate: `python3 empire_state_building.py` · Render: `blender -b -P render.py`
(the repo's SessionStart hook installs OpenSCAD, Blender and the Python libs
automatically in Claude Code on the web sessions).

## Print plan  (scale 0.40 mm/ft → ~582 mm / 23″ assembled)

| # | File | W × D × H (mm) | Filament | Notes |
|---|------|----------------|----------|-------|
| 1 | `01_base.stl` | 78.8 × 170 × 50.4 | stone grey | street-level arcade + window register; needs a bed ≥180 mm in one axis |
| 2 | `02_shaft_lower.stl` | 52.8 × 84 × 178.4 | stone grey | vertical piers + per-floor reveals; print upright, **no supports** |
| 3 | `03_shaft_upper.stl` | 52.8 × 84 × 178.4 | stone grey | print upright |
| 4 | `04_setbacks.stl` | 47.2 × 72 × 23.2 | stone grey | crown base + 86th-fl deck |
| 5 | `05_crown.stl` | 36.8 × 36.8 × 82.4 | **translucent** | ribbed mooring mast + 102nd-fl lantern → LED-backlight showpiece |
| 6 | `06_spire.stl` | 7.2 × 7.2 × 80.8 | grey | fragile needle — add a brim, or swap for a 1 mm rod |

`00_full_assembly_preview.stl` = all sections in place, for viewing only (not one
manifold body — don't slice it).

## Single- vs multi-color

The real building is essentially one color (Indiana limestone). The only truly
multi-color element is the illuminated crown at night — so print sections 1–4 + 6
in one stone filament across as many printers as you like, and print **section 5
in translucent** filament to backlight. All color management stays on one part.

## Assembly

Each section has a central alignment pin (peg on top / socket on bottom). Dry-fit
(clearance ≈ 0.6 mm, glue-friendly), then stack base → shaft_lower → shaft_upper →
setbacks → crown → spire and bond the seams with CA or epoxy.

## Tuning (top of `empire_state_building.py`)

`MM_PER_FT` scale · `PIER_PITCH` / `WIN_FRAC` / `WIN_DEPTH` window density & depth ·
`FLOOR_FT` / `SPANDREL_*` floor reveals · section z-ranges in `build()` set where
the print seams fall.

# The Beaumont: HO-scale Queen Anne house

Original HO (1:87.1) Queen Anne Victorian house, designed in code so every
revision is repeatable. Construction follows the flat-panel kit method studied
from the *Victorian #2* reference model (walls printed texture-up, keyed
corners, separate window and door inserts). No geometry was copied from it.

**Status:** concept, Rev A (appearance only; not yet split into printable parts).

## Layout

| Path | What it is |
| --- | --- |
| `model/geom.py` | Geometry helpers: textured wall panels (clapboard, fish-scale, stone, brick), roofs from sloped planes, shingle rows, hip caps |
| `model/components.py` | Windows, double door, turned posts, spindles, brackets |
| `model/house.py` | The house design: dimensions, walls, tower, porch, roofs, chimneys |
| `model/palette.py` | Paint scheme (one colour = one set of printed parts) |
| `model/render.py` | Blender/Cycles renderer (studio backdrop + lawn base) |
| `model/export_web.py` | Packs the model for the in-browser 3D viewer |
| `renders/` | Full-size PNG renders (local output, not committed) |
| `review/` | Review page (web-sized renders in `review/img`, 3D spin, revision codes) |

## Rebuild

```sh
pip install numpy manifold3d bpy pillow
python3 model/house.py                                   # -> out/house_parts.npz (~7 s)
python3 model/render.py --samples 96 --res 1600x1100 \
  --views hero,front,right,rear,aerial,porch,tower,gable # -> renders/
python3 model/export_web.py out/house_parts.npz review/house.bin   # also writes review/house.txt
python3 model/review_assets.py                           # renders -> review/img
```

Units are millimetres at HO scale; `ft()` / `inch()` convert prototype sizes.

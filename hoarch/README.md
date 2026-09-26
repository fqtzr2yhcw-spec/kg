# hoarch

Parametric generators for HO-scale (1:87.1) printed Victorian buildings, the shared parts
library for the building lineup. See [NOTES.md](NOTES.md) for the construction standards
(part split, stacked-slice roofs, clearances, print orientations) and what makes a model
read as a real building.

```python
from hoarch import openings, shell, roof, features, kit
win = openings.window_insert(9.8, 21.1, rise=2.4, style="crest")    # sash + surround
```

Requirements: `manifold3d`, `numpy`; `trimesh` for analysis only; Blender `bpy` 5.x
for `render.py`.

`study/` (git-ignored) holds private study builds that must never be published.

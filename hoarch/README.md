# hoarch

Parametric generators for HO-scale (1:87.1) printed Victorian buildings, the shared parts
library for the building lineup. See [NOTES.md](NOTES.md) for the construction standards
(part split, stacked-slice roofs, clearances, print orientations) and what makes a model
read as a real building.

```python
from hoarch import openings, shell, roof, features, kit
win = openings.window_insert(9.8, 21.1, rise=2.4, style="crest")    # sash + surround
```

Requirements: `requirements.txt` (`manifold3d`, `numpy`; `trimesh` and `rtree` for analysis;
Blender's `bpy` 5.x for `render.py`), and PrusaSlicer's command line for the slice estimates.
[tools/README.md](tools/README.md) sets up a machine and runs the whole pipeline: the full check
(`tools/check.py`) and the release (`tools/release.py`: zip, build guide, version, P2S project).

`study/` (git-ignored) holds private study builds that must never be published.

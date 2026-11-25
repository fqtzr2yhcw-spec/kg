# HO Scale Steel Mill Loads: listing photos

| File | Use it for |
|---|---|
| `01_ebay-main_no-text_2000x2000.jpg` | **eBay photo #1** (gallery/search image). No added text, per eBay's picture policy. |
| `02_square_with-text_2000x2000.jpg` | Square version with text: social posts, or a later eBay photo (see note). |
| `03_etsy-main_4x3_2667x2000.jpg` | **Etsy photo #1.** 4:3 is Etsy's recommended ratio. All the text sits inside the center square, so it survives Etsy's square crop in search. |

The loads are cut straight from the real product photo (not committed). The flat car, track and ballast are a 3D render matched to that photo's camera angle and depth of field. No real railroad name or reporting marks are used.

## How it was made (to re-run for another load)

Run from a folder containing the generator files, `p1.png` (the photo) and `node_modules/three@0.160.0`. Serve the folder on `127.0.0.1:8765`.

1. `seg.py` → `seg2.py`: rough color mask of the load.
2. `fit.py`: fits the photo's camera angle from 12 clicked corner points (`fit.json`).
3. `refine.py`: snaps the box outline to the photo's real edges (`sil.json`).
4. `render.js "<params>&w=..&h=.."` (plus `&depth=1`): renders `scene.html` (flat car, track, shadow proxies). Then `ds.py` downsamples it.
5. `composite.py`: warps the cutout onto the deck, adds the photo's contact shadow, and matches depth of field.
6. `shot.js`: lays out `thumb.html` (text/badges; `clean=1` hides the text, `W=2667` gives the 4:3 version).

Fonts are Anton, Oswald and Barlow Condensed from Google Fonts (`fonts.css`, files not committed).

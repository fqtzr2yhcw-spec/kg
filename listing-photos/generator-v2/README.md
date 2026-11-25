# Flat car load thumbnail generator (v2)

This is the reusable version of the steel mill load pipeline. It takes one product photo, matches its camera angle, renders an HO 50' flat car on track, composites the real product onto the deck, and lays out the eBay/Etsy thumbnails.

Each product folder in `listing-photos/` holds the same three images:

| File | Use |
|---|---|
| `01_ebay-main_no-text_2000x2000.jpg` | eBay photo #1. No added text, per eBay's picture policy. |
| `02_square_with-text_2000x2000.jpg` | Square with text: socials, or a later eBay photo. |
| `03_etsy-main_4x3_2667x2000.jpg` | Etsy photo #1 (4:3). Text stays inside the centre square so it survives Etsy's crop. |

## Steps per product (`products/` has the coils, pipes, plates and propellers examples)

1. `fit_<p>.py`: click 8–12 corner points in the photo, then fit the camera and the load's proportions (`<p>_fit.json`). Aim for an RMS under 8px.
2. `seg_<p>.py`: cut-out mask, guided by the fitted shape, plus the photo's own contact shadow.
3. `cfg_<p>.py [car_shift]`: render config (`rcfg_<p>.json`), covering car scale (HO size of the load), shadow proxies and lighting. It also writes `prod_<p>.json` (composite settings, including depth of field).
4. `hero.sh <p> <sq|wide|clean> <W> <H> <fov> <ox> <oy>`: renders `scene2.html` at 2× (colour + depth), downsamples, and runs `lib/composite2.py`.
5. `mkthumbs.py <p>`: lays out `thumb2.html` with `text_<p>.json` (headline, sticker, feature pills, layout `row` or `col right`).

Needs: Python with opencv, scipy and Pillow; Node with Playwright and three@0.160.0; and a local static server on port 8765 serving this folder. Fonts are Anton, Oswald and Barlow Condensed (Google Fonts; files not committed). Source photos are not committed.

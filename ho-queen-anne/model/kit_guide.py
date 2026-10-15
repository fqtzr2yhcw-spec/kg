"""Build the print & assembly guide (kit/guide/index.html) from manifest.json and renders."""
import html
import json
import os
import shutil
from collections import defaultdict

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.join(HERE, "..", "kit")
GUIDE = os.path.join(KIT, "guide")

STEP_TEXT = [
    ("Foundation & water table",
     "Glue the base plate inside the bottom of the stone foundation ring, flush with the bottom edge. "
     "Set the cream water-table ring on the top ledge so its outer lip overhangs the stone face. "
     "The notch on the right side is for the chimney; the gaps at the front and back are the door thresholds."),
    ("First floor",
     "<b>Before this step, fit every window and door while the panels are flat:</b> push each oxblood sash insert "
     "into its opening from the back (the flange sits on the inside face), then drop each cream casing into its "
     "pocket on the front. Do the same for the tower tube through its open ends. "
     "Then stand the Sage panels on the foundation against the inner lip: right wall (W4) first, then back (W5), "
     "left (W6), wing front (W3), wing side (W2) and front (W1). Set the tower tube at the front-left corner; "
     "W1 and W6 butt against the flat landings on the tower. Glue the four lower corner boards on the outside corners."),
    ("Belt loops & second floor",
     "Drop the two cream belt loops over the wall tops so they seat in the rabbets (the loop breaks at the chimney), "
     "and slide the octagonal belt ring onto the tower. Lower the Harvest Gold panels into the loops from above, "
     "then the upper tower tube onto its ring. The belt is the splice between floors: glue it to both. "
     "Add the four upper corner boards and the cream band across the gable."),
    ("Bay window & exterior chimney",
     "Glue the bay's cornice ring (soffit side up) to the top of the bay walls and the bay roof on the ring, then set the "
     "bay on the foundation's front lobe against the wing wall. The exterior chimney slides into the notches on the "
     "right wall; it spans the foundation, water table and belt."),
    ("Cornice rings",
     "The main cornice ring prints upside down: flip it so the brackets hang down and lower it onto the wall tops. "
     "The tower passes through its octagonal hole. Slide the second tower belt ring down to the roof line and set "
     "the tower's cornice ring on top of the tower."),
    ("Roofs, spire, dormer & gable",
     "Lower the main roof shell onto the cornice ring; the tower rises through the octagon hole and the chimney "
     "through its notch. Push the interior chimney stack up into its hole. Set the spire on the tower cornice. "
     "Glue the bargeboard-and-sunburst piece to the front edge of the wing roof, the dormer box and dormer roof on "
     "the left slope (with its bargeboards), and the iron cresting along the main ridge."),
    ("Wraparound porch",
     "Glue the stone piers onto the lattice base at the post positions, set the base against the foundation and "
     "lay the grey deck on it. Stand the three porch fronts on the deck edge (the short corner piece goes between the "
     "two long ones; the ends are mitred) and the return frame at the back. Rest the porch roof on the beams, snug "
     "against the belt band. Finish with the front steps and the two cheek walls with newel posts."),
    ("Back stoop, hood & downspouts",
     "Set the back stoop under the rear door, glue the two hood brackets beside the door and the hood on top. "
     "Glue the three iron downspouts at the back corners and the front-right corner of the wing, under the soffit."),
]

BRIM = {"Sage", "Harvest-Gold", "Brick", "Slate"}


def jpg(src, dst, width=None, q=84):
    im = Image.open(src).convert("RGB")
    if width and im.width > width:
        im = im.resize((width, int(im.height * width / im.width)), Image.LANCZOS)
    im.save(dst, quality=q, optimize=True, progressive=True)


def main():
    man = json.load(open(os.path.join(KIT, "manifest.json")))
    img = os.path.join(GUIDE, "img")
    os.makedirs(img, exist_ok=True)
    R = os.path.join(KIT, "renders")
    for n in ("hero", "front", "rear", "porch", "tower", "gable"):
        p = os.path.join(R, "final", n + ".png")
        if os.path.exists(p):
            jpg(p, os.path.join(img, f"final_{n}.jpg"), 1600)
            jpg(p, os.path.join(img, f"final_{n}_t.jpg"), 320, 78)
    if os.path.exists(os.path.join(R, "exploded.png")):
        jpg(os.path.join(R, "exploded.png"), os.path.join(img, "exploded.jpg"), 1200)
    for i in range(len(STEP_TEXT)):
        p = os.path.join(R, f"step{i + 1}.png")
        if os.path.exists(p):
            jpg(p, os.path.join(img, f"step{i + 1}.jpg"), 900)
    for pl in man["plates"]:
        jpg(os.path.join(KIT, pl["preview"]), os.path.join(img, os.path.basename(pl["preview"]).replace(".png", ".jpg")), 420)

    parts_n = sum(p["qty"] for p in man["parts"])
    tot = man["totals"]
    by_col = defaultdict(float)
    for pl in man["plates"]:
        by_col[pl["colour"]] += pl["slice"]["grams"] or 0
    hexes = {pl["colour"]: pl["hex"] for pl in man["plates"]}

    rows = []
    for pl in man["plates"]:
        s = pl["slice"]
        base = os.path.basename(pl["file"])
        prev = "img/" + os.path.basename(pl["preview"]).replace(".png", ".jpg")
        note = "Brim on" if pl["colour"] in BRIM else ""
        if pl["colour"] == "Oxblood":
            note = "First layer = window glass. Smooth plate gives clearer glass."
        rows.append(f"""<tr><td><img class="pv" src="{prev}" alt="Plate preview {html.escape(base)}"></td>
<td><span class="sw" style="background:{pl['hex']}"></span><b>{html.escape(pl['colour'].replace('-', ' '))}</b><br><code>{html.escape(base)}</code></td>
<td class="num">{pl['objects']}</td><td class="num">{s['time']}</td><td class="num">{s['grams']:.1f} g</td>
<td class="num">{pl['max_height_mm']:.0f} mm</td><td>{note}</td></tr>""")

    steps = []
    for i, (title, text) in enumerate(STEP_TEXT):
        steps.append(f"""<li class="step"><figure><img src="img/step{i + 1}.jpg" alt="After step {i + 1}: {html.escape(title)}"></figure>
<div><h3><span class="n">{i + 1}</span>{html.escape(title)}</h3><p>{text}</p></div></li>""")

    plist = []
    parts_by_col = defaultdict(list)
    for p in man["parts"]:
        parts_by_col[p["colour"]].append(p)
    for col, ps in parts_by_col.items():
        items = "".join(f"<tr><td class='num'>{p['qty']}×</td><td><code>{html.escape(os.path.basename(p['file']))}</code></td>"
                        f"<td class='num'>{p['size_mm'][0]:.0f}×{p['size_mm'][1]:.0f}×{p['size_mm'][2]:.1f}</td></tr>" for p in ps)
        plist.append(f"""<details><summary><span class="sw" style="background:{hexes[col]}"></span>{html.escape(col.replace('-', ' '))}
<span class="cnt">{sum(p['qty'] for p in ps)} pcs · {by_col[col]:.0f} g</span></summary>
<div class="tw"><table><thead><tr><th>Qty</th><th>File</th><th>Size mm (print)</th></tr></thead><tbody>{items}</tbody></table></div></details>""")

    filament = "".join(f"<li><span class='sw' style='background:{hexes[c]}'></span>{html.escape(c.replace('-', ' '))} <b>{g:.0f} g</b></li>"
                       for c, g in sorted(by_col.items(), key=lambda t: -t[1]))
    gallery = "".join(f"<button type='button' data-src='img/final_{n}.jpg' id='g-{n}'><img src='img/final_{n}_t.jpg' alt='{n} view'><span>{n}</span></button>"
                      for n in ("hero", "front", "rear", "porch", "tower", "gable") if os.path.exists(os.path.join(img, f"final_{n}.jpg")))

    page = TEMPLATE.format(parts=parts_n, plates=len(man["plates"]), hours=tot["print_minutes"] // 60,
                           mins=tot["print_minutes"] % 60, grams=round(tot["filament_g"]), rows="".join(rows),
                           steps="".join(steps), plist="".join(plist), filament=filament, gallery=gallery,
                           cost=tot["filament_g"] / 1000 * 22)
    with open(os.path.join(GUIDE, "index.html"), "w") as fh:
        fh.write(page)
    print("guide written:", os.path.join(GUIDE, "index.html"))


TEMPLATE = r"""<title>Beaumont Kit Guide</title>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bodoni+Moda:ital,opsz,wght@0,6..96,500;1,6..96,500&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap">
<style>
  :root {{
    --ground: #eef0eb; --surface: #f8f9f6; --ink: #1d2320; --muted: #59615b; --rule: #cfd5cc;
    --accent: #7a2433; --gold: #a77a26; --stage: #dde1da; --chip: #e4e8e0;
    --display: "Bodoni Moda", "Didot", Georgia, serif;
    --sans: "IBM Plex Sans", "Segoe UI", system-ui, sans-serif;
    --mono: "IBM Plex Mono", ui-monospace, Menlo, monospace;
  }}
  @media (prefers-color-scheme: dark) {{
    :root:not([data-theme="light"]) {{ color-scheme: dark; --ground: #141816; --surface: #1b201d; --ink: #e7eae4;
      --muted: #a2aaa3; --rule: #313833; --accent: #d77483; --gold: #d8b062; --stage: #0f1210; --chip: #252b27; }}
  }}
  :root[data-theme="dark"] {{ color-scheme: dark; --ground: #141816; --surface: #1b201d; --ink: #e7eae4;
      --muted: #a2aaa3; --rule: #313833; --accent: #d77483; --gold: #d8b062; --stage: #0f1210; --chip: #252b27; }}
  * {{ box-sizing: border-box; }}
  body {{ background: var(--ground); color: var(--ink); font: 15px/1.6 var(--sans); padding-inline: 16px; padding-block: 28px 64px; margin: 0; }}
  .wrap {{ max-width: 1180px; margin: 0 auto; display: grid; gap: 44px; }}
  h1, h2 {{ font-family: var(--display); font-weight: 500; margin: 0; text-wrap: balance; }}
  h1 {{ font-size: clamp(32px, 5vw, 54px); line-height: 1.04; }}
  h1 em {{ color: var(--accent); }}
  h2 {{ font-size: clamp(24px, 3vw, 32px); }}
  h3 {{ font-size: 17px; margin: 0 0 6px; display: flex; gap: 10px; align-items: baseline; }}
  p {{ margin: 0; }}
  code {{ font: 12.5px/1.3 var(--mono); word-break: break-all; }}
  .lede {{ color: var(--muted); max-width: 70ch; margin-top: 10px; }}
  .tb {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); border: 1.5px solid var(--ink); background: var(--surface); margin: 0; }}
  .tb div {{ padding: 10px 14px; border-right: 1px solid var(--rule); border-bottom: 1px solid var(--rule); }}
  .tb dt {{ font: 500 10.5px/1.2 var(--mono); letter-spacing: .12em; text-transform: uppercase; color: var(--muted); }}
  .tb dd {{ margin: 4px 0 0; font: 500 15px/1.3 var(--mono); }}
  .stage {{ background: var(--stage); border: 1px solid var(--rule); aspect-ratio: 16/11; max-width: 100%; }}
  .stage img {{ width: 100%; height: 100%; object-fit: contain; display: block; }}
  .strip {{ display: flex; gap: 8px; overflow-x: auto; margin-top: 10px; }}
  .strip button {{ flex: 0 0 auto; width: 112px; border: 1.5px solid transparent; background: var(--surface); padding: 0; cursor: pointer; color: var(--ink); text-align: left; }}
  .strip button[aria-pressed="true"] {{ border-color: var(--accent); }}
  .strip button:focus-visible {{ outline: 2px solid var(--accent); outline-offset: 2px; }}
  .strip img {{ width: 100%; aspect-ratio: 16/11; object-fit: cover; display: block; }}
  .strip span {{ display: block; font: 500 11px/1.2 var(--mono); text-transform: uppercase; letter-spacing: .06em; padding: 5px 8px; }}
  .two {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 28px 44px; align-items: start; }}
  .two figure {{ margin: 0; background: var(--stage); border: 1px solid var(--rule); }}
  .two figure img {{ width: 100%; display: block; }}
  .two figcaption {{ font: 12px/1.4 var(--mono); color: var(--muted); padding: 8px 10px; }}
  ul.set {{ margin: 0; padding-left: 18px; display: grid; gap: 6px; }}
  ul.fil {{ list-style: none; margin: 0; padding: 0; display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 6px 14px; }}
  .sw {{ display: inline-block; width: 12px; height: 12px; border: 1px solid var(--rule); margin-right: 7px; vertical-align: -1px; }}
  .tw {{ overflow-x: auto; }}
  table {{ border-collapse: collapse; width: 100%; font-variant-numeric: tabular-nums; }}
  th, td {{ text-align: left; padding: 8px 10px 8px 0; border-bottom: 1px solid var(--rule); vertical-align: middle; }}
  th {{ font: 500 11px/1.2 var(--mono); letter-spacing: .1em; text-transform: uppercase; color: var(--muted); }}
  td.num {{ font-family: var(--mono); font-size: 13px; white-space: nowrap; }}
  img.pv {{ width: 96px; height: 96px; object-fit: cover; display: block; border: 1px solid var(--rule); }}
  ol.steps {{ list-style: none; margin: 0; padding: 0; display: grid; gap: 22px; }}
  .step {{ display: grid; grid-template-columns: minmax(0, 420px) 1fr; gap: 20px; align-items: start; border-top: 1px solid var(--rule); padding-top: 18px; }}
  .step figure {{ margin: 0; background: var(--stage); border: 1px solid var(--rule); }}
  .step img {{ width: 100%; display: block; }}
  .n {{ font: 500 13px/1 var(--mono); color: var(--surface); background: var(--accent); padding: 5px 8px; }}
  @media (max-width: 720px) {{ .step {{ grid-template-columns: 1fr; }} }}
  details {{ border-top: 1px solid var(--rule); padding: 10px 0; }}
  summary {{ cursor: pointer; font-weight: 600; }}
  .cnt {{ font: 12px var(--mono); color: var(--muted); margin-left: 8px; }}
  .note {{ border: 1.5px solid var(--ink); background: var(--surface); padding: 16px 18px; display: grid; gap: 8px; }}
</style>
<div class="wrap">
  <header style="display:grid;gap:18px">
    <div>
      <h1>The Beaumont, <em>print &amp; assembly</em></h1>
      <p class="lede">Rev B: the Rev A design split into single-colour parts for premade production. Every plate is one colour and fits a 256 mm bed, so any printer can run any plate. Window glass is the first 0.2 mm layer of each sash insert.</p>
    </div>
    <dl class="tb">
      <div><dt>Scale</dt><dd>HO 1:87.1</dd></div>
      <div><dt>Parts</dt><dd>{parts}</dd></div>
      <div><dt>Plates</dt><dd>{plates}, 1 colour each</dd></div>
      <div><dt>Print time</dt><dd>≈{hours} h {mins} m</dd></div>
      <div><dt>Filament</dt><dd>≈{grams} g PLA</dd></div>
      <div><dt>Material cost</dt><dd>≈${cost:.2f} at $22/kg</dd></div>
    </dl>
  </header>

  <section>
    <div class="stage"><img id="shot" src="img/final_hero.jpg" alt="Assembled kit, front-left view"></div>
    <div class="strip" id="strip">{gallery}</div>
    <p class="lede">Renders of the kit parts assembled, glazing shown in the oxblood it will print in.</p>
  </section>

  <section class="two">
    <figure><img src="img/exploded.jpg" alt="Exploded view of the kit"><figcaption>Exploded view: foundation, first floor, belt &amp; second floor, bay &amp; chimney, cornice, roofs, porch, back.</figcaption></figure>
    <div style="display:grid;gap:14px">
      <h2>Print settings</h2>
      <ul class="set">
        <li>0.4 mm nozzle, PLA, no supports anywhere.</li>
        <li><b>First layer 0.2 mm</b> on every plate (the glass is exactly that layer).</li>
        <li>0.12 mm layers after that for crisp shingles and clapboard.</li>
        <li>2 walls, 5 top / 3 bottom layers, 15% infill.</li>
        <li>Brim on the Sage, Gold, Slate and Brick plates (tall or thin standing parts).</li>
        <li>Oxblood sash plate: a smooth plate gives clearer glass; textured gives frosted glass.</li>
        <li>Fit clearance is 0.1 mm per side. Print W2-upper with its window first as a fit test.</li>
      </ul>
      <h2 style="margin-top:8px">Filament per house</h2>
      <ul class="fil">{filament}</ul>
    </div>
  </section>

  <section style="display:grid;gap:14px">
    <h2>Plates</h2>
    <p class="lede">Times and grams are PrusaSlicer estimates with a Bambu-like profile (0.12 mm layers, Bambu-class speeds). Bambu Studio's numbers will differ somewhat. The Slate plate is the long pole; run it on its own printer.</p>
    <div class="tw"><table>
      <thead><tr><th>Preview</th><th>Plate</th><th>Parts</th><th>Time</th><th>Filament</th><th>Tallest</th><th>Notes</th></tr></thead>
      <tbody>{rows}</tbody>
    </table></div>
  </section>

  <section style="display:grid;gap:14px">
    <h2>Assembly</h2>
    <p class="lede">Medium CA for structure. For the sash inserts use canopy glue or PVA: CA fumes fog single-layer glass. Every trim piece has a pocket or landing, so dry-fit before gluing.</p>
    <ol class="steps">{steps}</ol>
  </section>

  <section style="display:grid;gap:6px">
    <h2>Parts list</h2>
    {plist}
  </section>

  <section class="note">
    <h2 style="font-size:22px">Status</h2>
    <p>The kit passes a computer fit check (zero part-to-part interference) and every plate slices cleanly, but it has not been printed yet. Print the fit test first and adjust clearance if the casings are tight or loose; the generator rebuilds every file in about 30 seconds.</p>
  </section>
</div>
<script>
  const shot = document.getElementById("shot");
  const btns = [...document.querySelectorAll("#strip button")];
  btns.forEach((b, i) => {{
    b.setAttribute("aria-pressed", i === 0 ? "true" : "false");
    b.addEventListener("click", () => {{
      btns.forEach(x => x.setAttribute("aria-pressed", String(x === b)));
      shot.src = b.dataset.src;
    }});
  }});
</script>
"""

if __name__ == "__main__":
    main()

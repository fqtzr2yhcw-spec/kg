"""Build guides: one illustrated PDF per building, made from its export (plates, parts and
slice estimates in out/<b>/kit/manifest.json), its renders (out/<b>/cycles, and the build
stages in out/<b>/steps if they have been rendered), its assembly notes (hoarch.assembly) and
the description in its module.

    python3 -m hoarch.guide <building> [...]     -> out/<b>/<Name>_Build_Guide.pdf
    python3 -m hoarch.guide --all                 every building
    python3 -m hoarch.guide --book                the combined book of every guide
"""
import importlib
import io
import json
import os
import re
import sys
from collections import OrderedDict, defaultdict

import numpy as np
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

from . import assembly as AS

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "out"))

# the collection in catalogue order: (module, display name)
BUILDINGS = [
    ("beaumont", "The Beaumont"), ("villa", "The Ashby"), ("harcourt", "The Harcourt"), ("fowler", "The Fowler"),
    ("whitby", "The Whitby"), ("delancey", "The Delancey"), ("ardmore", "The Ardmore"), ("merritt", "The Merritt"),
    ("hollis", "The Hollis"), ("carrow", "The Carrow"),
    ("pemberton", "The Pemberton Block"), ("barber", "Keller's Barber Shop"), ("bank", "The Merchants Bank"),
    ("general", "Hartley's General Store"), ("drugstore", "Whitcomb's Pharmacy"), ("hotel", "The Palace Hotel & Saloon"),
    ("bakery", "Vogel's Bakery"), ("hardware", "Bassett Hardware & Feed"), ("millinery", "Madame Dufresne's Millinery"),
    ("jeweler", "Ashworth & Sons, Jewelers"),
    ("marigold", "The Marigold"), ("primrose", "The Primrose"), ("rosecroft", "The Rosecroft"), ("twins", "Laurel & Myrtle"),
    ("larkspur", "The Larkspur"), ("juniper", "The Juniper"), ("camellia", "The Camellia"), ("wisteria", "The Wisteria"),
    ("hawthorn", "The Hawthorn"), ("magnolia", "The Magnolia"),
    ("whitmore", "The Whitmore"), ("pennock", "The Pennock"), ("oakhurst", "The Oakhurst"), ("vantassel", "The Van Tassel"), ("westbrook", "The Westbrook"),
]
NAMES = dict(BUILDINGS)
HO = 87.1

INK = colors.HexColor("#2B2B2B")
ACCENT = colors.HexColor("#2F4A3A")
RULE = colors.HexColor("#B9B2A2")
PAPER = colors.HexColor("#F6F3EC")

ss = getSampleStyleSheet()
ST = dict(
    title=ParagraphStyle("t", parent=ss["Title"], fontName="Times-Bold", fontSize=34, leading=38, textColor=ACCENT,
                         spaceAfter=4),
    subtitle=ParagraphStyle("st", parent=ss["Normal"], fontName="Times-Italic", fontSize=15, leading=19, alignment=TA_CENTER,
                            textColor=INK, spaceAfter=2),
    kicker=ParagraphStyle("k", parent=ss["Normal"], fontName="Helvetica", fontSize=9, leading=12, alignment=TA_CENTER,
                          textColor=colors.HexColor("#6B665C"), spaceAfter=10),
    h1=ParagraphStyle("h1", parent=ss["Heading1"], fontName="Times-Bold", fontSize=19, leading=23, textColor=ACCENT,
                      spaceBefore=4, spaceAfter=8),
    h2=ParagraphStyle("h2", parent=ss["Heading2"], fontName="Times-Bold", fontSize=13, leading=16, textColor=ACCENT,
                      spaceBefore=8, spaceAfter=4),
    body=ParagraphStyle("b", parent=ss["Normal"], fontName="Helvetica", fontSize=9.4, leading=13, textColor=INK,
                        spaceAfter=5),
    small=ParagraphStyle("s", parent=ss["Normal"], fontName="Helvetica", fontSize=8, leading=10.5, textColor=INK),
    step=ParagraphStyle("step", parent=ss["Normal"], fontName="Helvetica", fontSize=9.4, leading=13, textColor=INK,
                        leftIndent=18, firstLineIndent=-18, spaceAfter=6),
    bullet=ParagraphStyle("bul", parent=ss["Normal"], fontName="Helvetica", fontSize=9.4, leading=13, textColor=INK,
                          leftIndent=30, firstLineIndent=-10, spaceAfter=3),
    caption=ParagraphStyle("c", parent=ss["Normal"], fontName="Helvetica-Oblique", fontSize=8, leading=10,
                           alignment=TA_CENTER, textColor=colors.HexColor("#5B574F"), spaceAfter=6),
)


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def partname(s):
    """Part and plate names in the text set in bold (WALLS-1, CORNICE-J, PORCH-deck ...)."""
    s = esc(s)
    return re.sub(r"\b([A-Z][A-Z0-9]+(?:-[A-Za-z0-9]+)*)\b(?![a-z])",
                  lambda m: f"<b>{m.group(1)}</b>" if (len(m.group(1)) > 2 and m.group(1) not in ("PLA", "HO", "CA", "AMS"))
                  else m.group(1), s)


def img(path, width, max_h=None, quality=84):
    """A render or preview scaled to ``width`` (points), re-encoded as JPEG to keep PDFs small."""
    im = PILImage.open(path).convert("RGB")
    w, h = im.size
    tw = int(min(w, width / 72.0 * 200))                 # 200 dpi at the printed size
    if tw < w:
        im = im.resize((tw, int(h * tw / w)), PILImage.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=quality, optimize=True)
    buf.seek(0)
    ih = width * h / w
    if max_h and ih > max_h:
        width, ih = width * max_h / ih, max_h
    return Image(buf, width=width, height=ih)


def secs(t):
    s = 0
    for n, u in re.findall(r"(\d+)\s*([dhms])", t or ""):
        s += int(n) * {"d": 86400, "h": 3600, "m": 60, "s": 1}[u]
    return s


def hm(s):
    return f"{s // 3600} h {(s % 3600) // 60} m"


def description(mod):
    """The model's description from its module docstring: the paragraphs after the title,
    without the designer's working notes."""
    doc = (mod.__doc__ or "").strip()
    paras = [p.strip() for p in re.split(r"\n\s*\n", doc) if p.strip()]
    keep = []
    for p in paras[1:] if len(paras) > 1 else paras:
        if p.startswith("usage") or p.startswith("Rev ") or "python3 -m" in p:
            continue
        p = " ".join(p.split())
        p = re.sub(r"\s*\((?:after )?the user's [^)]*\)", "", p)
        p = re.sub(r",? after the user's photo( \d+)?", "", p)
        keep.append(p)
    if not keep:
        first = " ".join(paras[0].split()) if paras else ""
        first = re.sub(r"^[^:—-]*(?:[:—]| -- )\s*", "", first)
        keep = [first]
    return keep


def load(key):
    """Everything a guide needs about building ``key``."""
    mod = importlib.import_module("hoarch.buildings." + key)
    d = os.path.join(OUT, key)
    man = json.load(open(os.path.join(d, "kit", "manifest.json")))
    pal = json.load(open(os.path.join(d, "palette.json"))) if os.path.exists(os.path.join(d, "palette.json")) else {}
    if key in AS.NOTES:
        title, steps, *extra = AS.NOTES[key]
        kind = "house"
    else:
        title, steps, *extra = AS.SHOPS[key]
        kind = "shop"
    npz = os.path.join(d, key + ".npz")
    dims = None
    if os.path.exists(npz):
        z = np.load(npz)
        vs = [z[k] for k in z.files if k.endswith("__v") and len(z[k])]
        if vs:
            v = np.concatenate(vs)
            dims = (v.max(0) - v.min(0))
    renders = OrderedDict()
    cyc = os.path.join(d, "cycles")
    order = ["hero", "front", "rear", "back", "right", "east", "side", "corner"]
    if os.path.isdir(cyc):
        names = sorted(f[:-4] for f in os.listdir(cyc) if f.endswith(".png"))
        for n in [n for n in order if n in names] + [n for n in names if n not in order]:
            renders[n] = os.path.join(cyc, n + ".png")
    steps_dir = os.path.join(d, "steps")
    stage_imgs = [os.path.join(steps_dir, f"step{k}.png") for k in (1, 2, 3)]
    stage_imgs = [p for p in stage_imgs if os.path.exists(p)]
    stage_caps = []
    if os.path.exists(os.path.join(steps_dir, "steps.json")):
        stage_caps = json.load(open(os.path.join(steps_dir, "steps.json")))["captions"]
    return dict(key=key, mod=mod, man=man, pal=pal, title=title, steps=steps, extra=extra[0] if extra else "",
                kind=kind, dims=dims, renders=renders, stages=stage_imgs, stage_caps=stage_caps, name=NAMES.get(key, title.title()))


SMALL = {"a", "an", "and", "the", "of", "with", "on", "in", "round", "to", "for", "at", "by", "under", "over"}


def _style_line(title):
    if " - " not in title:
        return ""
    words = title.split(" - ", 1)[1].lower().split()
    return " ".join(w if (i and w in SMALL) else w[:1].upper() + w[1:] for i, w in enumerate(words))


def parse_steps(text):
    """Numbered steps (and "-" bullets) out of an assembly text, continuation lines joined."""
    items, cur = [], None
    for line in text.split("\n"):
        m = re.match(r"^\s*(\d+)\.\s+(.*)$", line)
        b = re.match(r"^\s*-\s+(.*)$", line)
        if m:
            cur = [m.group(1) + ".", m.group(2)]
            items.append(cur)
        elif b:
            cur = ["•", b.group(1)]
            items.append(cur)
        elif line.strip() and cur is not None:
            cur[1] += " " + line.strip()
    return items


def paragraphs(text):
    """Plain paragraphs out of a notes text (lines joined, blank lines split)."""
    out = []
    for block in re.split(r"\n\s*\n", text.strip()):
        lines = [l.strip() for l in block.split("\n") if l.strip()]
        if lines:
            out.append(" ".join(lines))
    return out


def facts_table(G):
    man = G["man"]
    parts = sum(p["qty"] for p in man["parts"])
    plates = man["plates"]
    n_chg = sum(1 for p in plates if p.get("change"))
    ts = sum(secs((p.get("slice") or {}).get("time")) for p in plates)
    tg = sum(((p.get("slice") or {}).get("grams") or 0.0) for p in plates)
    cols = sorted({p["colour"] for p in plates} | {p["change"]["to"] for p in plates if p.get("change")})
    rows = []
    if G["dims"] is not None:
        w, d, h = G["dims"]
        rows.append(["Size on the layout", f"{w:.0f} x {d:.0f} mm, {h:.0f} mm tall"])
        rows.append(["Full-size equivalent", f"about {w * HO / 304.8:.0f} x {d * HO / 304.8:.0f} ft, {h * HO / 304.8:.0f} ft tall"])
    rows += [["Scale", "HO, 1:87.1"],
             ["Parts", f"{parts}"],
             ["Print plates", f"{len(plates)}" + (f" ({n_chg} with a single filament change)" if n_chg else "")],
             ["Print time", f"about {hm(ts)} (PrusaSlicer estimate; Bambu Studio is usually faster)"],
             ["Filament", f"about {tg:.0f} g of PLA in {len(cols)} colours"]]
    t = Table([[Paragraph(f"<b>{a}</b>", ST["small"]), Paragraph(esc(b), ST["small"])] for a, b in rows],
              colWidths=[1.55 * inch, 4.9 * inch])
    t.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 0.3, RULE), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                           ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    return t


def filament_table(G):
    man = G["man"]
    grams = defaultdict(float)
    hexes, notes = {}, defaultdict(list)
    for p in man["plates"]:
        g = (p.get("slice") or {}).get("grams") or 0.0
        hexes[p["colour"]] = p["hex"]
        if p.get("change"):
            ch = p["change"]
            hexes[ch["to"]] = ch["to_hex"]
            grams[p["colour"]] += g / 2
            grams[ch["to"]] += g / 2
            notes[ch["to"]].append("second colour on a change plate")
        else:
            grams[p["colour"]] += g
    rows = [[Paragraph("<b>Colour</b>", ST["small"]), "", Paragraph("<b>Used for</b>", ST["small"]),
             Paragraph("<b>About</b>", ST["small"])]]
    use = defaultdict(set)
    for q in man["parts"]:
        use[q["colour"]].add(q["group"] or "parts")
    swatches = []
    for c in sorted(grams, key=lambda c_: -grams[c_]):
        what = ", ".join(sorted(use.get(c, set()))) or "; ".join(sorted(set(notes[c])))
        if c == "Windows_Doors":
            what = "windows and doors (the one plate printed with supports)"
        rows.append([Paragraph(esc(c.replace("_", " ")), ST["small"]), "", Paragraph(esc(what), ST["small"]),
                     Paragraph(f"{grams[c]:.0f} g", ST["small"])])
        swatches.append(colors.HexColor(hexes[c]))
    t = Table(rows, colWidths=[1.35 * inch, 0.35 * inch, 3.9 * inch, 0.8 * inch])
    sty = [("LINEBELOW", (0, 0), (-1, -1), 0.3, RULE), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
           ("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5)]
    for i, sw in enumerate(swatches, start=1):
        sty += [("BACKGROUND", (1, i), (1, i), sw), ("BOX", (1, i), (1, i), 0.4, colors.HexColor("#77736A"))]
    t.setStyle(TableStyle(sty))
    return t


def plates_table(G):
    rows = [[Paragraph(f"<b>{h}</b>", ST["small"]) for h in ("Plate", "Colour", "Parts", "Time", "PLA", "Notes")]]
    for p in G["man"]["plates"]:
        sl = p.get("slice") or {}
        notes = []
        if p.get("change"):
            ch = p["change"]
            notes.append(f"change to {ch['to'].replace('_', ' ')} from {ch['at_mm']:.1f} mm (add it on the "
                         f"{ch['at_mm'] + 0.2:.1f} mm layer at 0.20)")
        if p["colour"] == "Windows_Doors":
            notes.append("supports ON (tree, build plate only)")
        if p["max_height_mm"] > 25:
            notes.append("brim on")
        rows.append([Paragraph(esc(os.path.basename(p["file"])[:-4]), ST["small"]),
                     Paragraph(esc(p["colour"].replace("_", " ")), ST["small"]), Paragraph(str(p["objects"]), ST["small"]),
                     Paragraph(esc(sl.get("time", "?")), ST["small"]), Paragraph(f"{sl.get('grams') or 0:.0f} g", ST["small"]),
                     Paragraph(esc("; ".join(notes)), ST["small"])])
    t = Table(rows, colWidths=[1.95 * inch, 0.85 * inch, 0.42 * inch, 0.8 * inch, 0.45 * inch, 2.03 * inch], repeatRows=1)
    t.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 0.3, RULE), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                           ("BACKGROUND", (0, 0), (-1, 0), PAPER), ("TOPPADDING", (0, 0), (-1, -1), 2),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]))
    return t


def preview_grid(G, cols=4, width=6.5 * inch):
    kit = os.path.join(OUT, G["key"], "kit")
    cells = []
    cw = width / cols - 6
    for p in G["man"]["plates"]:
        pv = p.get("preview")
        if not pv or not os.path.exists(os.path.join(kit, pv)):
            continue
        cells.append([img(os.path.join(kit, pv), cw, max_h=cw), Paragraph(esc(os.path.basename(p["file"])[:-4]), ST["caption"])])
    rows = []
    for i in range(0, len(cells), cols):
        chunk = cells[i:i + cols] + [["", ""]] * (cols - len(cells[i:i + cols]))
        rows.append([c[0] for c in chunk])
        rows.append([c[1] for c in chunk])
    if not rows:
        return None
    t = Table(rows, colWidths=[width / cols] * cols)
    t.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "BOTTOM")]))
    return t


def parts_by_colour(G):
    by = OrderedDict()
    for q in sorted(G["man"]["parts"], key=lambda q_: (q_["colour"], q_["group"] or "", q_["file"])):
        by.setdefault(q["colour"], []).append(q)
    out = []
    for c, qs in by.items():
        names = []
        for q in qs:
            inst = q["instances"]
            base = re.sub(r"-(\d+|[LR]|front|back)$", "", inst[0]) if len(inst) > 1 else inst[0]
            names.append(f"{base} x{len(inst)}" if len(inst) > 1 else inst[0])
        out.append(Paragraph(f"<b>{esc(c.replace('_', ' '))}</b> ({sum(q_['qty'] for q_ in qs)}): " +
                             esc(", ".join(names)), ST["small"]))
        out.append(Spacer(1, 3))
    return out


FINISH = [
    ("Clean-up", "Clip the supports off the windows and doors and pare any nub with a sharp hobby knife. Test-fit "
     "every piece before gluing: the walls, bands and rings each drop onto a locating lip on the part below, so "
     "nothing should need forcing. A few passes of a fine file take off any elephant's foot on a first layer."),
    ("Glue", "Thin CA (superglue) for small trim, a gel CA or a plastic cement for the wall and roof joints. Glue the "
     "storeys together only after the windows, doors and shutters are in, since they can't come apart after that."),
    ("Paint", "The plates are printed in the model's colours, so painting is optional. For a finished look: a thin "
     "grey or brown wash into brick and stone joints, wiped off the faces; a light dry-brush of the trim colour over "
     "cornices and brackets; the door leaves in a darker shade of their colour or a wood tone."),
    ("Glass", "Either print the Windows_Doors plate with its first 0.4 mm in black or dark grey (one filament "
     "change) for dark glass behind coloured sashes, or paint the glazing gloss black, or leave it and add "
     "clear film behind each window from inside."),
    ("Weathering", "A little powdered pastel or weathering powder at the foot of the walls and down the roof "
     "slopes, a darker wash in the porch floor's plank joints, and soot at the chimney tops go a long way at HO scale."),
]


def build_story(G):
    s = []
    man = G["man"]
    # --- cover
    s.append(Spacer(1, 6))
    s.append(Paragraph(esc(G["name"]), ST["title"]))
    sl = _style_line(G["title"])
    if sl:
        s.append(Paragraph(esc(sl), ST["subtitle"]))
    s.append(Paragraph("HO scale (1:87.1) &nbsp;&middot;&nbsp; 3D-printed building &nbsp;&middot;&nbsp; build guide",
                       ST["kicker"]))
    if "hero" in G["renders"]:
        s.append(img(G["renders"]["hero"], 6.5 * inch, max_h=4.6 * inch))
    s.append(Spacer(1, 8))
    s.append(facts_table(G))
    s.append(PageBreak())
    # --- about
    s.append(Paragraph("About this model", ST["h1"]))
    for p in description(G["mod"]):
        s.append(Paragraph(esc(p), ST["body"]))
    views = [(n, p) for n, p in G["renders"].items() if n != "hero"]
    pair = [v for v in views if v[0] in ("front", "rear", "back")][:2] or views[:2]
    if pair:
        cells = [[img(p, 3.15 * inch, max_h=2.4 * inch) for _, p in pair],
                 [Paragraph(n.title() if n != "back" else "Rear", ST["caption"]) for n, _ in pair]]
        t = Table(cells, colWidths=[3.25 * inch] * len(pair))
        t.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER")]))
        s.append(Spacer(1, 6))
        s.append(t)
    s.append(PageBreak())
    # --- before you print
    s.append(Paragraph("Before you print", ST["h1"]))
    s.append(Paragraph("Filament", ST["h2"]))
    s.append(filament_table(G))
    s.append(Paragraph("Printer settings", ST["h2"]))
    for p in paragraphs(AS.COMMON_TOP):
        s.append(Paragraph(partname(p), ST["body"]))
    chg = [p for p in man["plates"] if p.get("change")]
    if chg or any(p["colour"] == "PorchDeck" for p in man["plates"]):
        s.append(Paragraph("Colour changes", ST["h2"]))
        s.append(Paragraph("Each two-colour part changes filament once, at one layer height, on a plate of its own. "
                           "Load the first colour. Bambu Studio swaps filament before the layer you pick, so pick the "
                           "first layer above the height given (right-click the layer slider &gt; Add color change). The "
                           "kit is laid out for 0.20 mm layers; at 0.16 mm pick the layer nearest the height.", ST["body"]))
        if any(p["colour"] == "PorchDeck" for p in man["plates"]):
            for p in paragraphs(AS.DECK):
                s.append(Paragraph(partname(p), ST["body"]))
    s.append(PageBreak())
    # --- plates
    s.append(Paragraph("Print plates", ST["h1"]))
    s.append(plates_table(G))
    grid = preview_grid(G)
    if grid is not None:
        s.append(Spacer(1, 8))
        s.append(Paragraph("Plate layouts", ST["h2"]))
        s.append(grid)
    s.append(Paragraph("Parts by colour", ST["h2"]))
    s.append(Paragraph("Sort the printed parts by these lists before you start; the names are the ones the steps use.",
                       ST["body"]))
    s += parts_by_colour(G)
    s.append(PageBreak())
    # --- assembly
    s.append(Paragraph("Assembly", ST["h1"]))
    if G["stages"]:
        caps = G["stage_caps"][:len(G["stages"])]
        cells = [img(p, 3.15 * inch, max_h=2.2 * inch) for p in G["stages"]]
        if "hero" in G["renders"]:
            cells.append(img(G["renders"]["hero"], 3.15 * inch, max_h=2.2 * inch))
            caps.append("Finished, with the roof on")
        caps = [f"{i}. {c}" for i, c in enumerate(caps, 1)]
        rows = []
        for i in range(0, len(cells), 2):
            rows.append(cells[i:i + 2] + [""] * (2 - len(cells[i:i + 2])))
            rows.append([Paragraph(c, ST["caption"]) for c in caps[i:i + 2]] + [""] * (2 - len(caps[i:i + 2])))
        t = Table(rows, colWidths=[3.25 * inch] * 2)
        t.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER")]))
        s.append(t)
        s.append(Spacer(1, 6))
    s.append(Paragraph("Stacked construction: each shell, band and ring drops onto a locating lip or ledge on the one "
                       "below. Work in this order:", ST["body"]))
    for num, text in parse_steps(G["steps"]):
        s.append(Paragraph(f"<b>{num}</b>&nbsp; {partname(text)}", ST["step"] if num != "•" else ST["bullet"]))
    if any(re.search(r"CORNICE-[A-Z0-9]+-(lower|upper|frieze|course|bed|crown)", i)
           for q in man["parts"] for i in q["instances"]):
        s.append(Paragraph("The built-up cornices", ST["h2"]))
        for p in paragraphs(AS.CORNICE_NOTE):
            s.append(Paragraph(partname(p), ST["body"]))
    if G["extra"]:
        s.append(Paragraph("Notes on this model", ST["h2"]))
        for p in paragraphs(G["extra"]):
            s.append(Paragraph(partname(p), ST["body"]))
    s.append(PageBreak())
    # --- finishing and gallery
    s.append(Paragraph("Finishing", ST["h1"]))
    for h, t_ in FINISH:
        s.append(Paragraph(f"<b>{h}.</b> {esc(t_)}", ST["body"]))
    rest = [(n, p) for n, p in G["renders"].items() if n not in ("hero",)]
    if rest:
        s.append(Paragraph("Gallery", ST["h2"]))
        cells = [img(p, 3.15 * inch, max_h=2.25 * inch) for _, p in rest[:6]]
        caps = [n.title() for n, _ in rest[:6]]
        rows = []
        for i in range(0, len(cells), 2):
            rows.append(cells[i:i + 2] + [""] * (2 - len(cells[i:i + 2])))
            rows.append([Paragraph(c, ST["caption"]) for c in caps[i:i + 2]] + [""] * (2 - len(caps[i:i + 2])))
        t = Table(rows, colWidths=[3.25 * inch] * 2)
        t.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER")]))
        s.append(t)
    return s


def _page(name):
    def draw(c, doc):
        c.saveState()
        c.setFillColor(RULE)
        c.rect(0.75 * inch, 0.55 * inch, 7.0 * inch, 0.4, stroke=0, fill=1)
        c.setFont("Helvetica", 7.5)
        c.setFillColor(colors.HexColor("#6B665C"))
        c.drawString(0.75 * inch, 0.4 * inch, f"{name}  ·  HO 1:87.1 build guide")
        c.drawRightString(7.75 * inch, 0.4 * inch, f"{doc.page}")
        c.restoreState()
    return draw


def guide(key, out=None):
    G = load(key)
    out = out or os.path.join(OUT, key, re.sub(r"[^A-Za-z0-9]+", "_", G["name"].replace("'", "").replace("&", "and")).strip("_") + "_Build_Guide.pdf")
    doc = SimpleDocTemplate(out, pagesize=letter, leftMargin=0.75 * inch, rightMargin=0.75 * inch,
                            topMargin=0.7 * inch, bottomMargin=0.8 * inch, title=f"{G['name']} build guide",
                            author="HO collection")
    doc.build(build_story(G), onFirstPage=_page(G["name"]), onLaterPages=_page(G["name"]))
    return out


def _guide_pdf(key):
    d = os.path.join(OUT, key)
    pdfs = sorted(f for f in os.listdir(d) if f.endswith("_Build_Guide.pdf")) if os.path.isdir(d) else []
    return os.path.join(d, pdfs[0]) if pdfs else None


def _contents(path, entries):
    """Cover and contents page for the book: entries = [(name, style, first page)]."""
    doc = SimpleDocTemplate(path, pagesize=letter, leftMargin=0.9 * inch, rightMargin=0.9 * inch,
                            topMargin=0.8 * inch, bottomMargin=0.8 * inch, title="HO collection build guides")
    s = [Spacer(1, 1.2 * inch), Paragraph("The HO Collection", ST["title"]),
         Paragraph("Build guides", ST["subtitle"]), Spacer(1, 6),
         Paragraph(f"{len(entries)} buildings in HO scale (1:87.1), printed in PLA at 0.20 mm layers",
                   ST["caption"]), PageBreak(), Paragraph("Contents", ST["h1"])]
    rows = [[Paragraph(f"<b>{h}</b>", ST["small"]) for h in ("Building", "Style", "Page")]]
    rows += [[Paragraph(f"<b>{esc(n)}</b>", ST["small"]), Paragraph(esc(st), ST["small"]),
              Paragraph(str(pg), ST["small"])] for n, st, pg in entries]
    t = Table(rows, colWidths=[2.2 * inch, 3.8 * inch, 0.6 * inch], repeatRows=1)
    t.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 0.3, RULE), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                           ("BACKGROUND", (0, 0), (-1, 0), PAPER), ("ALIGN", (2, 0), (2, -1), "RIGHT"), ("TOPPADDING", (0, 0), (-1, -1), 2),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]))
    s.append(t)
    doc.build(s)


def book(out=None):
    """Every guide, in catalogue order, as one PDF with a contents page and bookmarks."""
    import tempfile
    from pypdf import PdfReader, PdfWriter
    out = out or os.path.join(OUT, "HO_Collection_Build_Guides.pdf")
    readers = []
    for key, name in BUILDINGS:
        p = _guide_pdf(key)
        if p:
            style = _style_line(AS.NOTES[key][0] if key in AS.NOTES else AS.SHOPS[key][0])
            readers.append((name, style, PdfReader(p)))
    tmp = os.path.join(tempfile.mkdtemp(), "contents.pdf")
    entries = [(n, st, 0) for n, st, _ in readers]
    _contents(tmp, entries)
    front = len(PdfReader(tmp).pages)
    pg = front + 1
    entries = []
    for n, st, r in readers:
        entries.append((n, st, pg))
        pg += len(r.pages)
    _contents(tmp, entries)
    w = PdfWriter()
    for p in PdfReader(tmp).pages:
        w.add_page(p)
    for (n, _, r), (_, _, first) in zip(readers, entries):
        for p in r.pages:
            w.add_page(p)
        w.add_outline_item(n, first - 1)
    with open(out, "wb") as f:
        w.write(f)
    return out


def into_zip(key):
    """Put the model's guide into its print-file zip (next to PRINT_NOTES.txt), replacing an old one."""
    import zipfile
    p = _guide_pdf(key)
    zp = os.path.join(OUT, AS.ZIPNAME.get(key, key.capitalize()) + "_Print_Files.zip")
    if not p or not os.path.exists(zp):
        return None
    tmp = zp + ".tmp"
    with zipfile.ZipFile(zp) as zi, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zo:
        names = zi.namelist()
        top = names[0].split("/")[0]
        for n in names:
            if not n.endswith("_Build_Guide.pdf"):
                zo.writestr(zi.getinfo(n), zi.read(n))
        zo.write(p, f"{top}/{os.path.basename(p)}")
    os.replace(tmp, zp)
    return zp


if __name__ == "__main__":
    args = sys.argv[1:]
    keys = [k for k, _ in BUILDINGS] if "--all" in args else [a for a in args if not a.startswith("--")]
    if "--zip" in args:
        for k in keys:
            print(k, into_zip(k))
    elif "--book" in args:
        print(book())
    else:
        for k in keys:
            try:
                print(guide(k))
            except FileNotFoundError as e:
                print(k, "skipped:", e)

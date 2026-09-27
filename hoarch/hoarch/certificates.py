"""Design certificates: one page per building saying where the design came from and who may
use it, like the licence a 3D generator hands out with each model.

Each page records the building's design history (the first and latest commits of its module in
git) and a SHA-256 fingerprint of its print-file zip, so the page points at one exact release.
Re-run after a building is revised and repackaged: its fingerprint changes.

    python3 -m hoarch.certificates            # out/certificates/*.pdf and the combined book
"""

import datetime
import hashlib
import os
import re
import subprocess
import zipfile

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

from . import versions as V

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REPO = os.path.dirname(ROOT)
OUT = os.path.join(ROOT, "out")
DEST = os.path.join(OUT, "certificates")
REPO_NAME = "github.com/fqtzr2yhcw-spec/kg (private)"
TERMS = ("Anthropic Consumer Terms of Service, effective 8 October 2025 "
         "(anthropic.com/legal/consumer-terms)")

# Building number -> module, where the module isn't the name.
MODULES = {2: "villa", 11: "pemberton", 12: "barber", 13: "bank", 14: "general", 15: "drugstore",
           16: "hotel", 17: "bakery", 18: "hardware", 19: "millinery", 20: "jeweler", 24: "twins",
           34: "vantassel"}

INK = colors.HexColor("#2b2118")
ACCENT = colors.HexColor("#7a2e1d")
RULE = colors.HexColor("#b08d57")


def _git(*args):
    return subprocess.run(["git", "-C", REPO, *args], capture_output=True, text=True).stdout.strip()


def _clean_style(desc):
    s = re.sub(r"^Main Street:\s*", "", desc)
    s = re.sub(r"^A pair of\s+", "", s)
    s = re.sub(r"\s*\((?:photo \d+|pilot)\)", "", s)
    s = re.sub(r"\s+after the user's photo", "", s)
    s = s.replace("Colonial front, Victorian flair", "Colonial front with Victorian flair")
    s = re.split(r"[,:(.]", s)[0].strip()
    return s[:1].upper() + s[1:]


def collection():
    rows = []
    for line in open(os.path.join(ROOT, "COLLECTION.md")):
        m = re.match(r"\| (\d+) \| ([^|]+) \| ([^|]+) \|", line)
        if not m:
            continue
        num, name, desc = int(m.group(1)), m.group(2).strip(), m.group(3).strip()
        mod = MODULES.get(num) or re.sub(r"^The ", "", name).lower().replace(" ", "")
        size = re.search(r"\d+ x \d+ mm|\d+ mm across the flats", desc)
        year = re.search(r"\b1[89]\d\d\b", desc.split("(")[0])
        rows.append(dict(num=num, name=name, mod=mod, style=_clean_style(desc),
                         size=size.group(0) if size else None,
                         year=year.group(0) if year else None))
    return rows


def details(b):
    path = os.path.join("hoarch", "hoarch", "buildings", b["mod"] + ".py")
    first = _git("log", "--follow", "--diff-filter=A", "--format=%H %aI", "--", path).splitlines()
    last = _git("log", "-1", "--format=%H %aI", "--", path)
    b["first_sha"], b["first_date"] = first[-1].split() if first else ("", "")
    b["last_sha"], b["last_date"] = last.split() if last else ("", "")
    zp = V.zip_path(b["mod"])
    b["version"] = V.version(b["mod"])
    b["zip"] = os.path.basename(zp)
    h = hashlib.sha256()
    with open(zp, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    b["sha256"] = h.hexdigest()
    b["zip_mb"] = os.path.getsize(zp) / 1e6
    with zipfile.ZipFile(zp) as z:
        notes = [n for n in z.namelist() if n.endswith("PRINT_NOTES.txt")]
        text = z.read(notes[0]).decode("utf-8", "replace") if notes else ""
    m = re.search(r"Plates \((\d+) parts", text)
    b["parts"] = int(m.group(1)) if m else None
    return b


def _styles():
    base = dict(fontName="Times-Roman", fontSize=10.5, leading=14, textColor=INK)
    return dict(
        kicker=ParagraphStyle("k", **{**base, "fontName": "Helvetica", "fontSize": 8.5,
                                      "textColor": ACCENT, "alignment": TA_CENTER}),
        title=ParagraphStyle("t", **{**base, "fontName": "Times-Bold", "fontSize": 22,
                                     "leading": 26, "alignment": TA_CENTER}),
        name=ParagraphStyle("n", **{**base, "fontName": "Times-BoldItalic", "fontSize": 17,
                                    "leading": 21, "alignment": TA_CENTER, "textColor": ACCENT}),
        sub=ParagraphStyle("s", **{**base, "fontSize": 11, "alignment": TA_CENTER}),
        h=ParagraphStyle("h", **{**base, "fontName": "Times-Bold", "fontSize": 11.5,
                                 "spaceBefore": 8, "spaceAfter": 2}),
        body=ParagraphStyle("b", **base),
        cell=ParagraphStyle("c", **{**base, "fontSize": 9.5, "leading": 12}),
        mono=ParagraphStyle("m", **{**base, "fontName": "Courier", "fontSize": 8, "leading": 10}),
        small=ParagraphStyle("sm", **{**base, "fontSize": 8.5, "leading": 11}),
    )


def _frame(canvas, doc):
    w, h = letter
    canvas.saveState()
    canvas.setStrokeColor(RULE)
    canvas.setLineWidth(2.2)
    canvas.rect(0.45 * inch, 0.45 * inch, w - 0.9 * inch, h - 0.9 * inch)
    canvas.setLineWidth(0.6)
    canvas.rect(0.53 * inch, 0.53 * inch, w - 1.06 * inch, h - 1.06 * inch)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(RULE)
    canvas.drawCentredString(w / 2, 0.62 * inch, "HO Scale Model Buildings  -  Certificate of "
                             "Original Design and Commercial Use")
    canvas.restoreState()


def _date(iso):
    return datetime.date.fromisoformat(iso[:10]).strftime("%-d %B %Y") if iso else "-"


def _signature(st):
    t = Table([["", "", ""], [Paragraph("Owner / business", st["small"]),
                               Paragraph("Signature", st["small"]), Paragraph("Date", st["small"])]],
              colWidths=[2.6 * inch, 2.4 * inch, 1.5 * inch], rowHeights=[0.42 * inch, None])
    t.setStyle(TableStyle([("LINEBELOW", (0, 0), (0, 0), 0.6, INK),
                           ("LINEBELOW", (1, 0), (1, 0), 0.6, INK),
                           ("LINEBELOW", (2, 0), (2, 0), 0.6, INK),
                           ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 10)]))
    return t


def page(b, st):
    rows = [["Building", f"No. {b['num']}  -  {b['name']}"],
            ["Style", b["style"] + (f", {b['year']} style" if b["year"] else "")],
            ["Scale", "HO, 1:87.1"]]
    if b["size"]:
        rows.append(["Footprint", b["size"]])
    if b["parts"]:
        rows.append(["Parts", f"{b['parts']} printable parts"])
    rows += [["Design begun", f"{_date(b['first_date'])}  (commit {b['first_sha'][:12]})"],
             ["This release", f"{_date(b['last_date'])}  (commit {b['last_sha'][:12]})"],
             ["Version", f"v{b['version']}"],
             ["Print files", f"{b['zip']}  ({b['zip_mb']:.1f} MB)"],
             ["SHA-256", Paragraph(b["sha256"], st["mono"])]]
    rows = [[Paragraph(f"<b>{k}</b>", st["cell"]), v if not isinstance(v, str)
             else Paragraph(v, st["cell"])] for k, v in rows]
    table = Table(rows, colWidths=[1.25 * inch, 5.25 * inch])
    table.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -2), 0.3, RULE),
                               ("VALIGN", (0, 0), (-1, -1), "TOP"),
                               ("TOPPADDING", (0, 0), (-1, -1), 3.5),
                               ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5)]))
    terms = [
        ("Original design",
         "This model was designed from scratch for its owner, in the owner's own parametric design "
         "library, with the AI assistant Claude (made by Anthropic) writing the code under the "
         "owner's direction, review and revision. Historical architectural styles and the owner's "
         "photographs of existing buildings served only as inspiration. The model contains no "
         "geometry taken from any third-party 3D model, kit, scan or model-generation service."),
        ("Ownership",
         f"Under the {TERMS}, Anthropic assigns to the user all of its right, title and interest, "
         "if any, in the outputs of its service. No model-generation service, kit maker or other "
         "designer holds any interest in these files. "
         "The owner holds all rights that exist in the design files, the print files, the renders "
         "and the printed models."),
        ("Commercial use",
         "The owner may print, finish, paint and sell the model, built or as a kit, in any quantity "
         "and on any marketplace; photograph and advertise it; and license or sell the print files. "
         "No royalty, attribution or licence fee is owed to anyone."),
        ("Provenance",
         f"The design's full history is kept in the git repository {REPO_NAME}, whose commits "
         "carry the dates above. The SHA-256 fingerprint identifies the exact print-file release "
         "this certificate covers; later revisions of the same design are covered too, and have "
         "their own fingerprints."),
    ]
    out = [Paragraph("CERTIFICATE OF ORIGINAL DESIGN AND COMMERCIAL USE", st["kicker"]),
           Spacer(1, 8), Paragraph(b["name"], st["title"]),
           Paragraph(f"HO scale model building No. {b['num']}", st["sub"]), Spacer(1, 14), table,
           Spacer(1, 6)]
    for head, text in terms:
        out += [Paragraph(head, st["h"]), Paragraph(text, st["body"])]
    out += [Spacer(1, 22), _signature(st), Spacer(1, 10),
            Paragraph("This certificate records the design's origin and the owner's right to use it "
                      "commercially. It is not a copyright registration.", st["small"])]
    return out


def cover(bs, st):
    out = [Paragraph("HO SCALE MODEL BUILDINGS", st["kicker"]), Spacer(1, 8),
           Paragraph("Certificates of Original Design and Commercial Use", st["title"]),
           Spacer(1, 6),
           Paragraph(f"{len(bs)} buildings  -  issued {datetime.date.today().strftime('%-d %B %Y')}",
                     st["sub"]), Spacer(1, 14),
           Paragraph("What these are", st["h"]),
           Paragraph("One page per building, like the licence a 3D model generator issues with "
                     "each creation. Each page records where the design came from, who owns it, "
                     "what the owner may do with it, and a fingerprint of the exact print files. "
                     "Keep them with your business records. Print, sign and file the page for a "
                     "building when you list it, or attach it when a marketplace or buyer asks "
                     "whether a design is yours to sell.", st["body"]),
           Paragraph("What they are not", st["h"]),
           Paragraph("A certificate records origin and commercial-use rights; it is not a "
                     "copyright registration and does not by itself stop someone copying a "
                     "printed model. How far copyright protects a design made with an AI tool "
                     "depends on the human creative contribution to it (here, the owner's choice "
                     "of styles, colours, rules and revisions, and the painting and finishing).",
                     st["body"]), Spacer(1, 10)]
    rows = [[Paragraph(f"<b>{h}</b>", st["cell"]) for h in ("No.", "Building", "Style", "Begun")]]
    rows += [[Paragraph(str(b["num"]), st["cell"]), Paragraph(b["name"], st["cell"]),
              Paragraph(b["style"], st["cell"]), Paragraph(_date(b["first_date"]), st["cell"])]
             for b in bs]
    t = Table(rows, colWidths=[0.45 * inch, 1.9 * inch, 2.75 * inch, 1.3 * inch], repeatRows=1)
    t.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, 0), 0.8, INK),
                           ("LINEBELOW", (0, 1), (-1, -1), 0.25, RULE),
                           ("TOPPADDING", (0, 0), (-1, -1), 1.5),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5)]))
    return out + [t]


def build():
    os.makedirs(DEST, exist_ok=True)
    st = _styles()
    bs = [details(b) for b in collection()]
    kw = dict(pagesize=letter, leftMargin=0.95 * inch, rightMargin=0.95 * inch,
              topMargin=0.85 * inch, bottomMargin=0.85 * inch, title="Design certificates")
    story = cover(bs, st)
    for b in bs:
        story += [PageBreak()] + page(b, st)
        one = os.path.join(DEST, f"{b['num']:02d}_{re.sub(r'[^A-Za-z0-9]+', '_', b['name']).strip('_')}"
                                 "_Certificate.pdf")
        SimpleDocTemplate(one, **{**kw, "title": b["name"] + " certificate"}).build(
            page(b, st), onFirstPage=_frame, onLaterPages=_frame)
    book = os.path.join(OUT, "HO_Collection_Design_Certificates.pdf")
    SimpleDocTemplate(book, **kw).build(story, onFirstPage=_frame, onLaterPages=_frame)
    with zipfile.ZipFile(os.path.join(OUT, "HO_Design_Certificates.zip"), "w",
                         zipfile.ZIP_DEFLATED) as z:
        for f in sorted(os.listdir(DEST)):
            z.write(os.path.join(DEST, f), f)
    for b in bs:
        print(f"{b['num']:>2} {b['name']:<30} {b['style'][:40]:<40} {b['size'] or '-':<22} "
              f"{b['parts'] or '-':>3} {b['first_date'][:10]}")
    print(book)


if __name__ == "__main__":
    build()

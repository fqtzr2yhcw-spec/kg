"""Pricing and listings sheet for the flatcar loads: out/listings/HO_Flatcar_Loads_Pricing_and_Listings.md.

Titles, prices, descriptions and pieces come from the pack registry (hoarch/packs.py); print times,
grams and sizes from each load's export (python3 -m hoarch.packs <key> export); the eBay titles,
Etsy tags, era, colours and the car each load suits are below.

usage: python3 tools/loads_listings.py
"""
import json
import os
import re

from _common import OUT
from hoarch.packs import PACKS

LOADS = ["windtower", "nacelle", "transformer", "linepipe", "tarps", "steel", "vessel", "propeller"]
LOADS += [k for k, pk in PACKS.items() if pk.get("extra")]          # the second series (hoarch/loads2.py) carries its own

# costs (the houses' sheets' assumptions, scaled to a small parcel)
FIL = 20.0            # $ per kg
WASTE = 1.12
POWER = 0.02          # $ per print hour
FEE, ORDER = 0.136, 0.40               # eBay: 13.6 % of item + shipping, $0.40 an order
ETSY = 0.065 + 0.03, 0.20 + 0.25       # Etsy: transaction + payment processing, listing + processing fixed

EXTRA = {
    "windtower": dict(
        ebay="HO Scale Wind Turbine Tower Section Flatcar Load 1:87 Transport Frames 89 ft",
        car="an 89 ft heavy-duty flatcar", era="Modern (2000-present)", colors="Gray, Blue", ship=8.0, pack=2.50,
        tags=["ho scale load", "wind turbine model", "wind tower load", "ho flatcar load", "flatcar load", "89 ft flatcar",
              "dimensional load", "model railroad load", "ho train load", "modern railroad", "wind farm diorama",
              "1:87 scale", "gift for railfan"]),
    "nacelle": dict(
        ebay="HO Scale Wind Turbine Nacelle and Rotor Hub Flatcar Load 1:87 Printed in Color",
        car="a heavy-duty flatcar (one load each, or both on one long car)", era="Modern (2000-present)",
        colors="Yellow, White", ship=5.5, pack=1.25,
        tags=["ho scale load", "ho flatcar load", "wind turbine model", "turbine nacelle", "wind turbine hub",
              "wind farm diorama", "flatcar load", "model railroad load", "ho train load", "modern railroad", "1:87 scale",
              "train layout", "gift for railfan"]),
    "transformer": dict(
        ebay="HO Scale Power Transformer Load for Depressed Center Flatcar 1:87 in Color",
        car="a depressed-centre flatcar (it sits in the well)", era="Transition / Modern (1950s-present)",
        colors="Gray, Brown", ship=5.5, pack=1.25,
        tags=["ho scale load", "transformer load", "depressed flatcar", "ho flatcar load", "flatcar load",
              "model railroad load", "power plant", "substation", "heavy load", "electrical load", "ho train load",
              "1:87 scale", "gift for railfan"]),
    "linepipe": dict(
        ebay="HO Scale Coated Line Pipe Flatcar Load 1:87 Pipeline Pipe Bulkhead Flat Car",
        car="a 53 ft bulkhead flatcar, or any flatcar 42 ft and longer", era="Modern (1980s-present)",
        colors="Green, Brown", ship=5.5, pack=1.25,
        tags=["ho scale pipe load", "pipe load", "line pipe", "pipeline", "ho flatcar load", "bulkhead flatcar",
              "flatcar load", "model railroad load", "oil and gas", "ho scale pipes", "ho train load", "1:87 scale",
              "gift for railfan"]),
    "tarps": dict(
        ebay="HO Scale Tarped Flatcar Loads 3 Pack 1:87 Covered Machinery Crate Long Load",
        car="any flatcar (all three fit a 50 ft car; one each on shorter cars)", era="Any (steam to modern)",
        colors="Tan, Blue, Black, Brown", ship=5.5, pack=1.25,
        tags=["ho scale load", "tarped load", "covered load", "ho flatcar load", "flatcar load", "model railroad load",
              "machinery load", "freight load", "ho scale freight", "flat car tarp", "ho train load", "1:87 scale",
              "gift for railfan"]),
    "steel": dict(
        ebay="HO Scale Steel Loads 5 pc Coils Plate I-Beam Bundle 1:87 Flatcar Gondola Load",
        car="flatcars and gondolas (the coils also suit a coil car)", era="Transition / Modern (1950s-present)",
        colors="Silver, Gray, Rust Brown, Brown", ship=5.5, pack=1.25,
        tags=["ho scale steel", "steel coils", "steel load", "i beam load", "steel plate", "ho flatcar load",
              "gondola load", "flatcar load", "model railroad load", "steel mill", "ho train load", "1:87 scale",
              "gift for railfan"]),
    "vessel": dict(
        ebay="HO Scale Pressure Vessel Flatcar Load 1:87 Refinery Chemical Plant Tank Skid",
        car="a 60 ft flatcar", era="Transition / Modern (1950s-present)", colors="White, Black", ship=5.5, pack=1.25,
        tags=["ho scale load", "pressure vessel", "refinery load", "chemical plant", "oil refinery", "ho flatcar load",
              "flatcar load", "model railroad load", "industrial load", "heavy load", "ho train load", "1:87 scale",
              "gift for railfan"]),
    "propeller": dict(
        ebay="HO Scale Bronze Ship Propeller Flatcar Load 1:87 Shipyard Harbor Port Scene",
        car="a 40 ft flatcar, or a dockside or shipyard scene", era="Any (steam to modern)",
        colors="Bronze Gold, Brown", ship=5.5, pack=1.25,
        tags=["ho scale load", "ship propeller", "bronze propeller", "shipyard", "harbor diorama", "port scene",
              "ho flatcar load", "flatcar load", "model railroad load", "marine load", "ho train load", "1:87 scale",
              "gift for railfan"]),
}


def _minutes(t):
    """A slicer time like "2h 5m 5s" in minutes."""
    return sum(float(v) * {"d": 1440, "h": 60, "m": 1, "s": 1 / 60}[u] for v, u in re.findall(r"([\d.]+)\s*([dhms])", t))


def hm(minutes):
    return f"{int(minutes // 60)} h {int(round(minutes % 60))} m" if minutes >= 60 else f"{int(round(minutes))} m"


def data(key):
    pk = PACKS[key]
    ex = EXTRA.get(key) or dict(pk["extra"], tags=pk["listing"]["tags"])
    man = json.load(open(os.path.join(OUT, key, "kit", "manifest.json")))
    runs = max(pk["per_run"], 1)
    grams = sum((p.get("slice") or {}).get("grams") or 0.0 for p in man["plates"]) / runs
    mins = sum(_minutes((p.get("slice") or {}).get("time") or "0s") for p in man["plates"]) / runs
    fil = grams * WASTE / 1000 * FIL
    mat = fil + POWER * mins / 60 + ex["pack"]
    price = float(pk["listing"]["price"])
    net_e = price - FEE * (price + ex["ship"]) - ORDER - mat
    net_y = price - ETSY[0] * (price + ex["ship"]) - ETSY[1] - mat
    sizes = []
    for p in man["parts"]:
        d = sorted(p["size_mm"], reverse=True)
        sizes.append((re.sub(r"-\d+$", "", p["instances"][0].split("__")[-1]), p["qty"], d))
    return dict(pk=pk, ex=ex, grams=grams, mins=mins, fil=fil, mat=mat, price=price, net_e=net_e, net_y=net_y,
                sizes=sizes, nplates=len(man["plates"]))


def check(key, d):
    ex, pk = d["ex"], d["pk"]
    assert len(ex["ebay"]) <= 80, (key, len(ex["ebay"]))
    assert len(pk["listing"]["title"]) <= 140, (key, "etsy title")
    assert len(ex["tags"]) == 13 and all(len(t) <= 20 for t in ex["tags"]), (key, "tags")


def sheet():
    D = {k: data(k) for k in LOADS}
    for k, d in D.items():
        check(k, d)
    L = ["# HO Flatcar Loads: Pricing and Listings", "",
         "_The eight flatcar loads. Prepared November 2026. Prices are the ones in each load's LISTING.txt; costs use "
         "the houses' sheets' assumptions, scaled to a small parcel._", "",
         "## The short version", "",
         "| Load | Price | Your net, eBay | Your net, Etsy | Print time per pack | Filament per pack | Packs per run |",
         "|---|---|---|---|---|---|---|"]
    for k, d in D.items():
        L.append(f"| {d['pk']['title']} | ${d['price']:.2f} | ${d['net_e']:.2f} | ${d['net_y']:.2f} | {hm(d['mins'])} | "
                 f"{d['grams'] * WASTE:.0f} g | {d['pk']['per_run']} |")
    L += ["",
          "- **Every load prints in its colours, with no painting and no assembly.** Say \"printed in color\" and "
          "\"ready to place\" in every listing; most HO loads on eBay are kits or need paint.",
          "- **List first:** the coated line pipe (the steady Etsy seller), the wind tower section and the nacelle "
          "(no HO wind tower load is on the market; list the two together and offer both at a discount), and the "
          "transformer (big castings and transformers fetch the higher prices).",
          "- **Combine shipping.** Several loads ship in one small box for about the same postage, so offer a "
          "discount on two or more and set combined shipping in eBay.",
          "- **The packs-per-run column:** one run of the plates makes that many packs, so print two runs of "
          "the two-pack loads and keep a few in stock.",
          "- **Treat these as launch prices.** No watchers after two weeks: drop 10%. Sells in days: raise the next one.",
          "",
          "## What each load costs you", "",
          "| Load | Filament (with ~12% waste) | Print time per pack | Plates | Materials | Pieces (L x W x H) |",
          "|---|---|---|---|---|---|"]
    for k, d in D.items():
        pcs = "; ".join(f"{n.replace('-', ' ')}{f' x{q}' if q > 1 else ''} {s[0]:.0f} x {s[1]:.0f} x {s[2]:.0f} mm"
                        for n, q, s in d["sizes"])
        L.append(f"| {d['pk']['title']} | {d['grams'] * WASTE:.0f} g, ${d['fil']:.2f} | {hm(d['mins'])} | {d['nplates']} | "
                 f"${d['mat']:.2f} | {pcs} |")
    L += ["",
          f"Filament at ${FIL:.0f}/kg, power about ${POWER:.2f} a print hour, packing $1.25 a load ($2.50 for the "
          "wind tower's long box). eBay: 13.6% of item + shipping, plus $0.40 an order. Etsy: 6.5% transaction and "
          "3% + $0.25 payment processing on item + shipping, plus the $0.20 listing fee. Shipping charged at cost "
          "(about $5.50 USPS Ground Advantage for a small box, $8 for the wind tower).", "",
          "## eBay: category and item specifics (all eight)", "",
          "**Category:** Toys & Hobbies > Model Railroads & Trains > HO Scale > **Freight Cars** (category 262302), "
          "where HO flat car loads sold on their own are listed. If the menu reads differently, type \"HO flat car load\" "
          "into the category picker and choose Freight Cars.", "",
          "| Field | Value |", "|---|---|",
          "| Brand | Your shop name (or Unbranded) |",
          "| Scale / Gauge | HO (1:87) / HO |",
          "| Type / Car Type | Flat Car Load (custom value) |",
          "| Material | Plastic (PLA) |",
          "| Railroad / Corporate Roadname | None (no railroad or maker lettering) |",
          "| Features | Printed in color, Detailed, Load only (car not included) |",
          "| Assembly Required | No |",
          "| Handmade | Yes |",
          "| Country/Region of Manufacture | United States |",
          "| Modified Item / Custom Bundle | No |",
          "| Recommended Age | 14+ |",
          "| Era, Color, Number of Pieces, Item Size | per load, below |", "",
          "Don't pick plain \"Flat Car\" as the car type (a buyer filtering on it expects a car), and don't name a "
          "turbine or transformer maker or a real railroad.", "",
          "## Etsy: category and attributes", "",
          "Type \"model train\" into the Category box and pick the model train category under Toys & Games (Etsy "
          "doesn't publish its category tree, so check the suggestion it shows). Who made it: I did. What is it: "
          "A finished product. When was it made: Made to order. Material: Plastic. Colours: per load, below.", "",
          "## Before you list", "",
          "- **Photos first:** the printed load on a real HO flatcar in the main photo (most buyers want to see it "
          "on a car), then close-ups and a scale shot with an HO figure. The renders in each zip can go last, "
          "captioned \"digital render; flatcar not included\".",
          "- **Say \"load only\" in the title or first line**, as the descriptions below do.",
          ""]
    for k, d in D.items():
        pk, ex = d["pk"], d["ex"]
        pieces = "\n".join(f"  - {pc['qty']} x {pc['name'].replace('-', ' ')}" for pc in pk["pieces"])
        sizes = "\n".join(f"- {n.replace('-', ' ')}{f' (x{q})' if q > 1 else ''}: {s[0] / 25.4:.1f} x {s[1] / 25.4:.1f} x "
                          f"{s[2] / 25.4:.1f} in ({s[0]:.0f} x {s[1]:.0f} x {s[2]:.0f} mm)" for n, q, s in d["sizes"])
        npieces = sum(pc["qty"] for pc in pk["pieces"])
        L += ["---", "", f"## {pk['title']}", "",
              f"**Price:** ${d['price']:.2f}. **Suits:** {ex['car']}.", "",
              "### eBay", "",
              f"- **Title** ({len(ex['ebay'])}/80): `{ex['ebay']}`",
              f"- **Item specifics for this load:** Era: {ex['era']}. Color: {ex['colors']}. Number of Pieces: {npieces}. "
              f"Item size: see SIZE below.", "",
              "### Etsy", "",
              f"- **Title** ({len(pk['listing']['title'])}/140): `{pk['listing']['title']}`",
              f"- **Tags (13):** `{', '.join(ex['tags'])}`",
              f"- **Colours:** {ex['colors']}", "",
              "### Description (paste on both)", "",
              "```",
              f"{pk['title'].upper()} - HO SCALE (1:87) FLATCAR LOAD", "",
              pk["blurb"], "",
              "What's in the pack:", pieces, "",
              "Load only: the flatcar shown is not included. The load stands on its own blocking, so it sits on any deck. "
              f"It suits {ex['car']}.", "",
              "Printed in colour: every piece comes off the printer in its finished colours, so it is ready to place. "
              "No painting, no assembly.", "",
              "SIZE", sizes, "",
              "HO scale (1:87). An original design, drawn and 3D printed by us in PLA at 0.2 mm layers. Weather it with "
              "chalks or washes if you like.",
              "Not a toy: small parts, for ages 14+.",
              "```", ""]
    path = os.path.join(OUT, "listings", "HO_Flatcar_Loads_Pricing_and_Listings.md")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w").write("\n".join(L))
    print(path)
    for k, d in D.items():
        print(f"  {k:12s} ${d['price']:.2f}  net eBay ${d['net_e']:.2f} Etsy ${d['net_y']:.2f}  {hm(d['mins'])}  "
              f"{d['grams'] * WASTE:.0f} g  {[(n, [round(x) for x in s]) for n, q, s in d['sizes']]}")
    return path


if __name__ == "__main__":
    sheet()

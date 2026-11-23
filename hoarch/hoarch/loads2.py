"""Pack entries for the second series of flatcar loads (geometry in hoarch.flatloads2), in the
schema of hoarch.packs.PACKS, which merges them in. ``extra`` holds what the loads' listings sheet
(tools/loads_listings.py) needs beyond the pack: eBay title, the car it suits, era, colours,
shipping and packing costs, Etsy tags."""
from . import flatloads2 as G
from .loadnames import ZIPNAMES


def _p(name, fn, colour, qty=1, change=None, note=""):
    return {"name": name, "fn": fn, "colour": colour, "qty": qty, "change": change, "show": None, "note": note}


def _load(key, title, per_run, blurb, pieces, price, title_listing, tags, extra):
    assert len(tags) == 13 and all(len(t) <= 20 for t in tags), (key, [t for t in tags if len(t) > 20])
    return key, dict(title=title, zipname=ZIPNAMES[key], per_run=per_run, kind="flatcar load",
                     scene=G.SCENES[key], blurb=blurb, pieces=pieces,
                     listing=dict(price=price, title=title_listing, tags=tags), extra=extra)


_TAIL = ["ho flatcar load", "model railroad load", "1:87 scale", "gift for railfan"]

PACKS2 = dict([
    _load("girders", "Concrete Bridge Girder Load", 2,
          "Two 70 ft prestressed concrete bridge girders to the AASHTO Type IV section, 54 in deep, as they ride to the job: "
          "upright on timber bolsters with oak pads and chocks, stirrups standing out of the top flange every 2 ft, strand "
          "lifting loops near the ends, diaphragm inserts in the web, and the ends cut on a skew for a skewed bridge. "
          "For an 89 ft flatcar.",
          [_p("Girder", G.girder, "Light Gray", 2), _p("Girder-bolster", G.girder_bolster, "Cocoa Brown", 2)],
          "18.99", "HO Scale Concrete Bridge Girders 2 pc | 70 ft Prestressed Beam Flatcar Load | Printed in Color | 1:87",
          ["concrete girder", "bridge beam load", "bridge girder", "precast concrete", "highway bridge", "89 ft flatcar",
           "construction load", "modern railroad", "ho scale load"] + _TAIL,
          dict(ebay="HO Scale Prestressed Concrete Bridge Girder Flatcar Load 2 pc 70 ft 1:87",
               car="an 89 ft flatcar (both girders side by side)", era="Transition / Modern (1960s-present)",
               colors="Light Gray, Brown", ship=8.0, pack=2.50)),
    _load("lumber", "Lumber Load", 2,
          "Eighteen bundles of fresh-sawn lumber for a 53 ft bulkhead flat, three tiers of two in three rows: 2x4, 2x6, 2x10 "
          "and 2x12 bundles, 16 ft long and banded, each on its own 4 x 4 stickers. One end of every bundle is trimmed "
          "even and the other ragged, with every board end its own, and the outside boards' edges uneven, as real "
          "bundles are. Stack them any way you like; they glue tier on tier.",
          [_p("Bundle-2x4", lambda: G.lumber_bundle("2x4", 11), "Desert Tan", 5, (G.BUNDLE_H, "Cocoa Brown")),
           _p("Bundle-2x6", lambda: G.lumber_bundle("2x6", 12), "Desert Tan", 5, (G.BUNDLE_H, "Cocoa Brown")),
           _p("Bundle-2x10", lambda: G.lumber_bundle("2x10", 13), "Desert Tan", 4, (G.BUNDLE_H, "Cocoa Brown")),
           _p("Bundle-2x12", lambda: G.lumber_bundle("2x12", 14), "Desert Tan", 4, (G.BUNDLE_H, "Cocoa Brown"))],
          "19.99", "HO Scale Lumber Load 18 Bundles | Bulkhead Flatcar Load | Fresh Sawn 2x4 2x6 2x10 | Printed | 1:87",
          ["ho lumber load", "lumber bundles", "bulkhead flatcar", "lumber yard", "sawmill", "ho scale lumber",
           "wood load", "flatcar load", "ho scale load"] + _TAIL,
          dict(ebay="HO Scale Lumber Load 18 Bundles for Bulkhead Flatcar 1:87 Fresh Sawn Printed",
               car="a 53 ft bulkhead flatcar (18 bundles), or fewer on any flat or in a gondola", era="Any (steam to modern)",
               colors="Tan, Brown", ship=5.5, pack=1.25)),
    _load("wrapped", "Wrapped Lumber Load", 2,
          "Eighteen bundles of mill-wrapped lumber for a 53 ft bulkhead flat or a centerbeam: 16 ft bundles in white wrap "
          "with the ends folded in, three bands each with plastic corner guards, each bundle on its own stickers. "
          "Blank wrap, ready for your own mill's name.",
          [_p("Wrapped-bundle", G.wrapped_bundle, "White", 18, (G.BUNDLE_H, "Cocoa Brown"))],
          "19.99", "HO Scale Wrapped Lumber Load 18 Bundles | Bulkhead Centerbeam Flatcar | Printed in Color | 1:87",
          ["wrapped lumber", "ho lumber load", "centerbeam load", "bulkhead flatcar", "lumber bundles", "ho scale lumber",
           "modern railroad", "flatcar load", "ho scale load"] + _TAIL,
          dict(ebay="HO Scale Wrapped Lumber Load 18 Bundles Bulkhead Centerbeam Flatcar 1:87",
               car="a 53 ft bulkhead flatcar or a centerbeam flat", era="Modern (1980s-present)",
               colors="White, Brown", ship=5.5, pack=1.25)),
    _load("tires", "Mining Truck Tire Load", 2,
          "Six 40.00R57 haul-truck tires, 11 ft 8 in across, standing in yellow steel cradles as they ride to the mine: a "
          "deep rock-lug tread with open shoulders, bulged sidewalls lettered with the size, and the bead's bore. "
          "Two rows of three fill a 53 ft flatcar.",
          [_p("Mining-tire", G.otr_tire, "Sunflower Yellow", 6, (G.TIRE_FRAME, "Black"))],
          "21.99", "HO Scale Mining Truck Tires 6 pc | Giant Haul Truck Tire Flatcar Load in Cradles | Printed | 1:87",
          ["mining tires", "giant tires", "haul truck tire", "mining load", "otr tire", "heavy equipment",
           "mine diorama", "flatcar load", "ho scale load"] + _TAIL,
          dict(ebay="HO Scale Giant Mining Truck Tires Flatcar Load 6 pc in Steel Cradles 1:87",
               car="a 50-53 ft flatcar (two rows of three)", era="Modern (1980s-present)",
               colors="Black, Yellow", ship=5.5, pack=1.50)),
    _load("logs", "Sawlog Load", 3,
          "Two piles of 16 ft sawlogs for a 40 ft flatcar, each three, two and one on three log bunks with stakes and a "
          "wire-rope wrapper over every bunk. Each log is a little tapered and out of round, its bark fissured, rings and a "
          "heart check on both cut ends, knots on the upper logs.",
          [_p("Log-pile-A", lambda: G.log_stack(3), "Black Walnut", 1, (G.LOG_BUNK, "Dark Brown")),
           _p("Log-pile-B", lambda: G.log_stack(8), "Black Walnut", 1, (G.LOG_BUNK, "Dark Brown"))],
          "15.99", "HO Scale Log Load 2 Piles | 16 ft Sawlogs on Bunks with Stakes | Logging Flatcar Load | 1:87",
          ["ho log load", "logging railroad", "sawlogs", "log flatcar", "logging camp", "sawmill", "steam era",
           "flatcar load", "ho scale load"] + _TAIL,
          dict(ebay="HO Scale Sawlog Load 2 Piles 16 ft Logs on Bunks for 40 ft Flatcar 1:87",
               car="a 40 ft flatcar (two piles), or one pile on a short log car", era="Steam / Transition (1890s-1960s)",
               colors="Brown", ship=5.5, pack=1.25)),
    _load("panels", "Track Panel Load", 1,
          "Six 39 ft panels of new track as the rail gang ships them, stacked three high: 24 wood ties at 19 1/2 in on each, "
          "a little out of line the way they come off the panel machine, a few with end splits, tie plates and 132 lb rail "
          "on standard gauge. Two stacks of three fill an 89 ft flatcar; the panels rest tie on rail head.",
          [_p("Track-panel", G.track_panel, "Black Walnut", 6, (G.PANEL_TIE, "Iron Gray Metallic"))],
          "21.99", "HO Scale Track Panel Load 6 pc | 39 ft Panels for MOW Flatcar | Ties and Rail | Printed | 1:87",
          ["track panels", "mow train", "maintenance of way", "rail gang", "ho scale track", "work train",
           "railroad ties", "flatcar load", "ho scale load"] + _TAIL,
          dict(ebay="HO Scale Track Panel Flatcar Load 6 pc 39 ft MOW Work Train 1:87 Printed",
               car="an 89 ft flatcar (two stacks of three), or three on a 42 ft flat", era="Transition / Modern (1950s-present)",
               colors="Brown, Gray", ship=6.5, pack=1.50)),
    _load("concties", "Concrete Crosstie Load", 2,
          "Three stacks of new prestressed concrete crossties for a 53 ft bulkhead flat, five layers of fifteen: each tie "
          "8 ft 6 in, deeper under the rail seats than in the middle, with its cast-in rail clip shoulders; dunnage between "
          "the layers at the rail seats, and under the bottom layer. Ties in concrete grey, shoulders and dunnage dark.",
          [_p("Tie-layer", G.concrete_tie_layer, "Light Gray", 15, (G.CTIE_SEAT, "Black Walnut")),
           _p("Tie-dunnage", G.tie_dunnage, "Black Walnut", 6)],
          "21.99", "HO Scale Concrete Railroad Ties Load 225 Ties | MOW Bulkhead Flatcar Load | Printed in Color | 1:87",
          ["concrete ties", "railroad ties", "mow train", "maintenance of way", "tie train", "bulkhead flatcar",
           "work train", "modern railroad", "ho scale load"] + _TAIL,
          dict(ebay="HO Scale Concrete Crosstie Load 225 Ties in Stacks for Bulkhead Flatcar MOW 1:87",
               car="a 53 ft bulkhead flatcar (three stacks), or one stack on a short flat", era="Modern (1980s-present)",
               colors="Light Gray, Dark Brown", ship=6.5, pack=1.50)),
    _load("woodties", "Wood Crosstie Bundle Load", 2,
          "Twenty-four bundles of new creosoted wood crossties for a 53 ft bulkhead flat or a gondola: 25 ties to a bundle, "
          "five by five, banded twice, four bundles to a row on new-lumber dunnage. Every tie a little different in length, "
          "with anti-split plates and checks on the ends.",
          [_p("Tie-bundle-row", lambda: G.wood_tie_row(2), "Caramel", 3, (G.WTIE_DUN, "Black Walnut")),
           _p("Tie-bundle-row-B", lambda: G.wood_tie_row(9), "Caramel", 3, (G.WTIE_DUN, "Black Walnut"))],
          "19.99", "HO Scale Wood Railroad Tie Bundles 24 | Creosote Crossties MOW Flatcar Gondola Load | Printed | 1:87",
          ["railroad ties", "crossties", "tie bundles", "mow train", "maintenance of way", "work train", "gondola load",
           "flatcar load", "ho scale load"] + _TAIL,
          dict(ebay="HO Scale Creosote Wood Crosstie Bundles 24 Flatcar Gondola MOW Load 1:87 Printed",
               car="a 53 ft bulkhead flatcar (two tiers), a flat or a gondola", era="Any (steam to modern)",
               colors="Dark Brown, Tan", ship=6.5, pack=1.50)),
    _load("granite", "Granite Block Load", 3,
          "Four quarry blocks of building granite, 8 to 11 ft long, each on three timbers with wedges: chipped corners and "
          "edges, the plug-and-feather drill holes down a split face, and the quarry's block number on an end. "
          "For a 40 to 50 ft flatcar, a quarry siding or a monument works.",
          [_p("Granite-block-" + num, (lambda i: (lambda: G.granite_block(i)))(i), "Cocoa Brown", 1, (G.STONE_BLOCK, "Light Gray"))
           for i, (_, num) in enumerate(G.BLOCKS)],
          "16.99", "HO Scale Granite Quarry Blocks 4 pc | Dimension Stone Flatcar Load | Printed in Color | 1:87",
          ["granite blocks", "quarry load", "stone blocks", "marble quarry", "quarry diorama", "dimension stone",
           "monument works", "flatcar load", "ho scale load"] + _TAIL,
          dict(ebay="HO Scale Granite Quarry Block Flatcar Load 4 pc Dimension Stone 1:87 Printed",
               car="a 40 to 50 ft flatcar", era="Any (steam to modern)", colors="Light Gray, Brown", ship=5.5, pack=1.25)),
    _load("bricks", "Brick Cube Load", 2,
          "Thirty-six cubes of packaged face brick in three colours, red, buff and brown: sixteen courses stacked tight, "
          "stretchers and headers by turns so every course's joints show, two fork voids through the bottom, banded both "
          "ways. Two high and two across they fill a 40 ft flat; they work as well on a dock or a building site.",
          [_p("Brick-cube-red", lambda: G.brick_cube(1), "Red", 12), _p("Brick-cube-buff", lambda: G.brick_cube(2), "Caramel", 12),
           _p("Brick-cube-brown", lambda: G.brick_cube(3), "Cocoa Brown", 12)],
          "17.99", "HO Scale Brick Cubes 36 pc | Packaged Brick Flatcar Load, Brickyard, Building Site | Printed | 1:87",
          ["brick cubes", "ho scale bricks", "brickyard", "building supply", "construction site", "brick load",
           "lumber yard", "flatcar load", "ho scale load"] + _TAIL,
          dict(ebay="HO Scale Packaged Brick Cubes 36 pc Flatcar Load Brickyard Building Supply 1:87",
               car="a 40 ft flatcar (36 cubes), or a dock or yard scene", era="Transition / Modern (1950s-present)",
               colors="Red, Tan, Brown", ship=5.5, pack=1.25)),
    _load("ingotmolds", "Ingot Mold Load", 2,
          "Four big-end-down slab ingot molds on their stools, for a 40 ft flatcar between the foundry and the mill: tapered "
          "cast-iron tubes 8 ft tall, fluted down their broad faces, a thickened top rim and a lifting lug on each end. "
          "Stools in iron grey, the molds in mill rust.",
          [_p("Ingot-mold", G.ingot_mold, "Iron Gray Metallic", 4, (G.MOLD_STOOL, "Copper Brown Metallic"))],
          "15.99", "HO Scale Steel Mill Ingot Molds 4 pc on Stools | Flatcar Load | Printed in Color | 1:87",
          ["ingot molds", "steel mill", "steel mill load", "foundry", "blast furnace", "industrial load", "steel load",
           "flatcar load", "ho scale load"] + _TAIL,
          dict(ebay="HO Scale Steel Mill Ingot Mold Flatcar Load 4 pc on Stools 1:87 Printed",
               car="a 40 ft flatcar, or an ingot buggy in the mill", era="Steam / Transition (1900s-1980s)",
               colors="Rust, Iron Gray", ship=5.5, pack=1.25)),
    _load("cablereels", "HV Cable Reel Load", 2,
          "Three steel cable drums 11 ft 6 in across for a 53 ft flatcar, as they ride to a substation or a wind farm: "
          "flanges with twelve ribs, a ring stiffener and the arbor plate's bolt circle, two drums showing the last layer "
          "of high-voltage cable turn by turn with its tail clamped, one lagged in wood battens, each chocked at its rims. "
          "Flanges, cable and lagging print as separate pieces in their colours and glue together.",
          [_p("Reel-flange", G.reel_flange, "Cobalt Blue", 6), _p("Reel-cable", G.reel_barrel, "Black", 2),
           _p("Reel-lagged", lambda: G.reel_barrel(True), "Caramel", 1), _p("Reel-chock", G.reel_chock, "Cocoa Brown", 12)],
          "19.99", "HO Scale Cable Reels 3 pc | Steel HV Cable Drums Flatcar Load, Wind Farm Substation | Printed | 1:87",
          ["cable reels", "cable spools", "wire spools", "power cable", "substation", "wind farm", "utility load",
           "flatcar load", "ho scale load"] + _TAIL,
          dict(ebay="HO Scale Steel Cable Reel Flatcar Load 3 Drums HV Cable Wind Farm Substation 1:87",
               car="a 53 ft flatcar (three drums)", era="Transition / Modern (1960s-present)",
               colors="Blue, Black, Tan, Brown", ship=6.5, pack=1.50)),
])

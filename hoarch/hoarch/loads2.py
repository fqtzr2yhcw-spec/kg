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
          "Four quarry blocks of building granite in two shades, 8 to 11 ft long, each on three timbers with wedges: split "
          "faces broken in facets and ridges, chipped corners, the plug-and-feather drill holes down a split face, and the "
          "quarry's block number on an end. "
          "For a 40 to 50 ft flatcar, a quarry siding or a monument works.",
          [_p("Granite-block-" + num, (lambda i: (lambda: G.granite_block(i)))(i), "Cocoa Brown", 1, (G.STONE_BLOCK, G.GRANITE_COLOURS[i]))
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
    _load("tank", "Main Battle Tank Load", 2,
          "A main battle tank as the Army ships it by rail: turret turned to the rear and the gun on its travel lock over the "
          "engine deck. Seven road wheels a side behind side skirts, the long shallow glacis, a low wedge turret with its "
          "bustle stowage, cupola, hatches, sights and smoke dischargers, grilles on the engine deck. Steel-grey tracks and "
          "running gear, olive drab hull; the gun is a separate piece that plugs into the mantlet. Generic, not any one "
          "army's tank. 12 ft wide, it rides as a dimensional load.",
          [_p("Tank", G.tank, "Iron Gray Metallic", 1, (G.TANK_TRACK, "Bronze")), _p("Tank-gun", G.tank_barrel, "Bronze", 1)],
          "17.99", "HO Scale Main Battle Tank Flatcar Load | Military Train | Olive Drab, Printed in Color | 1:87",
          ["military tank", "ho military", "army train", "tank flatcar", "military load", "battle tank", "armored vehicle",
           "flatcar load", "ho scale load"] + _TAIL,
          dict(ebay="HO Scale Military Main Battle Tank Flatcar Load Olive Drab 1:87 Army Train",
               car="a 50-60 ft flatcar (one tank) or an 89 ft flat (two)", era="Modern (1980s-present)",
               colors="Olive Drab, Steel Gray", ship=5.5, pack=1.25)),
    _load("apc", "Armored Personnel Carrier Load", 2,
          "Two tracked armoured personnel carriers for a 53 ft flatcar: plain aluminium boxes on five road wheels a side, the "
          "trim vane folded on the glacis, headlights in guards, the driver's hatch and the commander's cupola with its "
          "machine gun stowed, the big cargo hatch, the rear ramp with its door and hinges, the exhaust on the right "
          "front. Steel-grey tracks, olive drab hulls. Generic.",
          [_p("APC", G.apc, "Iron Gray Metallic", 2, (G.APC_TRACK, "Bronze"))],
          "17.99", "HO Scale Armored Personnel Carriers 2 pc | Military Flatcar Load | Olive Drab, Printed | 1:87",
          ["military apc", "ho military", "army train", "armored vehicle", "military load", "personnel carrier",
           "military flatcar", "flatcar load", "ho scale load"] + _TAIL,
          dict(ebay="HO Scale Military Armored Personnel Carriers 2 pc Flatcar Load Olive Drab 1:87",
               car="a 50-53 ft flatcar (two)", era="Transition / Modern (1960s-present)",
               colors="Olive Drab, Steel Gray", ship=5.5, pack=1.25)),
    _load("excavator", "Crawler Excavator Load", 2,
          "A 20 tonne class crawler excavator in transport position for a 53 ft flatcar: long-frame tracks with rollers and "
          "carriers, the cab on the left with its glass, engine hood and grilles, exhaust, the rounded counterweight and "
          "handrails; the boom folded down, the arm tucked back under it and the bucket curled onto its timber. The front "
          "prints as two halves that glue face to face and slide into the boom-foot bracket. Generic.",
          [_p("Excavator", G.excavator, "Iron Gray Metallic", 1, (G.EXC_TRACK, "Sunflower Yellow")),
           _p("Excavator-front-L", lambda: G.excavator_front(1), "Sunflower Yellow", 1),
           _p("Excavator-front-R", lambda: G.excavator_front(-1), "Sunflower Yellow", 1),
           _p("Bucket-timber", G.excavator_block, "Cocoa Brown", 1)],
          "19.99", "HO Scale Crawler Excavator Flatcar Load | Construction Equipment, Transport Position | Printed | 1:87",
          ["ho excavator", "excavator load", "construction", "heavy equipment", "trackhoe", "construction site",
           "equipment load", "flatcar load", "ho scale load"] + _TAIL,
          dict(ebay="HO Scale Crawler Excavator Flatcar Load Construction Equipment 1:87 Printed Yellow",
               car="a 53 ft flatcar", era="Modern (1980s-present)", colors="Yellow, Steel Gray", ship=5.5, pack=1.25)),
    _load("dozer", "Crawler Dozer Load", 2,
          "A mid-size crawler dozer shipped with its blade off, the blade riding beside it on timber skids, for a 53 ft "
          "flatcar: oval tracks on six rollers, the push-arm trunnions on the track frames, the long engine hood with its "
          "radiator guard, louvres, exhaust stack and precleaner, the ROPS cab with its glass, the fuel tank and a single-"
          "shank ripper lowered onto a steel block. The blade stands on its cutting edge: semi-U moldboard, end bits, ribs "
          "and brackets on the back. Generic.",
          [_p("Dozer", G.dozer, "Iron Gray Metallic", 1, (G.DOZER_TRACK, "Sunflower Yellow")),
           _p("Dozer-blade", G.dozer_blade, "Cocoa Brown", 1, (G.BLADE_SKID, "Sunflower Yellow"))],
          "18.99", "HO Scale Crawler Dozer and Blade Flatcar Load | Bulldozer Construction Equipment | Printed | 1:87",
          ["ho bulldozer", "dozer load", "bulldozer", "construction", "heavy equipment", "crawler dozer",
           "equipment load", "flatcar load", "ho scale load"] + _TAIL,
          dict(ebay="HO Scale Crawler Dozer with Blade Flatcar Load Bulldozer Construction 1:87",
               car="a 53 ft flatcar", era="Modern (1970s-present)", colors="Yellow, Steel Gray, Brown", ship=5.5, pack=1.25)),
    _load("crawler", "Vintage Crawler Tractor Load", 2,
          "Two 1940s crawler tractors for a 40 ft flatcar, as they left the factory: oval tracks on five rollers, the "
          "radiator with its cast top tank and vertical grille, a narrow hood with the exhaust and air-cleaner stacks, the "
          "fuel tank, the open seat with its back and steering levers, fenders over the tracks and the drawbar plate. "
          "Generic.",
          [_p("Crawler-tractor", G.crawler_tractor, "Iron Gray Metallic", 2, (G.CRAWLER_TRACK, "Sunflower Yellow"))],
          "16.99", "HO Scale Vintage Crawler Tractors 2 pc | 1940s Flatcar Load | Printed in Color | 1:87",
          ["crawler tractor", "vintage tractor", "steam era", "farm machinery", "construction", "heavy equipment",
           "transition era", "flatcar load", "ho scale load"] + _TAIL,
          dict(ebay="HO Scale Vintage 1940s Crawler Tractors 2 pc Flatcar Load 1:87 Printed Yellow",
               car="a 40 ft flatcar (two)", era="Steam / Transition (1930s-1960s)", colors="Yellow, Steel Gray",
               ship=5.5, pack=1.25)),
    _load("trailers", "Piggyback Trailer Load", 1,
          "Two 40 ft van trailers of the 1960s for an 85-89 ft piggyback flat, one silver and one white: exterior posts "
          "every two feet, top and bottom rails, rear doors with hinges, lock rods and handles, the ICC bar, rounded front "
          "corners, the tandem with dual wheels on its slider, mud flaps, and the landing gear down on sand shoes. Printed "
          "upside down, so the running gear prints black in the same pass. Blank sides, ready for your road's decals.",
          [_p("Trailer-silver", G.trailer, "Silver", 1, (G.TRL_CHANGE, "Black")),
           _p("Trailer-white", lambda: G.trailer(2), "White", 1, (G.TRL_CHANGE, "Black"))],
          "19.99", "HO Scale 40 ft Piggyback Van Trailers 2 pc | TOFC Flatcar Load | 1960s | Printed in Color | 1:87",
          ["piggyback trailer", "tofc load", "van trailer", "ho trailer", "intermodal", "semi trailer", "transition era",
           "flatcar load", "ho scale load"] + _TAIL,
          dict(ebay="HO Scale 40 ft Van Trailers 2 pc Piggyback TOFC Flatcar Load 1960s 1:87 Printed",
               car="an 85-89 ft piggyback (TOFC) flatcar", era="Transition (1955-1980)", colors="Silver, White, Black",
               ship=6.5, pack=1.50)),
    _load("containers", "ISO Container Load", 2,
          "Four 20 ft ISO shipping containers in red, blue, green and grey: corrugated sides and fronts set back between the "
          "corner posts and rails, eight corner castings with their apertures, doors with four lock rods, cam keepers, "
          "handles and hinges, the CSC plate, fork pockets and a corrugated roof. Blank, ready for your lines' decals. "
          "Four fill an 89 ft flat; they work as well in a yard or on a dock.",
          [_p("Container-red", G.iso_container, "Red", 1), _p("Container-blue", G.iso_container, "Marine Blue", 1),
           _p("Container-green", G.iso_container, "Mistletoe Green", 1), _p("Container-grey", G.iso_container, "Light Gray", 1)],
          "15.99", "HO Scale 20 ft Shipping Containers 4 pc | ISO Container COFC Flatcar Load | Printed in Color | 1:87",
          ["ho containers", "shipping container", "20 ft container", "intermodal", "cofc load", "container yard",
           "port diorama", "flatcar load", "ho scale load"] + _TAIL,
          dict(ebay="HO Scale 20 ft ISO Shipping Containers 4 pc Intermodal COFC Flatcar Load 1:87",
               car="an 89 ft flatcar (four), or two on a 40 ft flat", era="Modern (1970s-present)",
               colors="Red, Blue, Green, Gray", ship=5.5, pack=1.25)),
    _load("crates", "Machinery Crate Load", 2,
          "Six wooden machinery crates for a 40 ft flatcar, 5 to 14 ft long, each on two skids: planked sides and tops, a "
          "frame of battens round every face with a diagonal brace, and stencilling raised on the big ones (MACHINERY, "
          "THIS SIDE UP, FRAGILE). In three tones of new wood.",
          [_p("Crate-" + "-".join(str(int(v)) for v in dims), (lambda i: (lambda: G.crate(i)))(i), col, 1)
           for i, ((dims, _), col) in enumerate(zip(G.CRATES, ["Caramel", "Latte Brown", "Caramel", "Desert Tan", "Latte Brown", "Caramel"]))],
          "14.99", "HO Scale Wooden Machinery Crates 6 pc | Flatcar Load, Freight Dock, LCL | Printed in Color | 1:87",
          ["ho crates", "wooden crates", "machinery crate", "freight dock", "flatcar load", "ho scale crates", "steam era",
           "lcl freight", "ho scale load"] + _TAIL,
          dict(ebay="HO Scale Wooden Machinery Crates 6 pc Flatcar Load Freight Dock 1:87 Printed",
               car="a 40 ft flatcar, a gondola or a freight dock", era="Any (steam to modern)",
               colors="Tan, Light Brown", ship=5.5, pack=1.25)),
    _load("chillers", "Air-Cooled Chiller Load", 1,
          "Two 30 ft air-cooled chillers for an 89 ft flatcar, bound for a hospital or a data centre: the control panel end "
          "with its doors and nameplate, the compressor bay behind louvres, condenser coils down both sides with every "
          "fin showing, and twelve fans on top in their shrouds behind guards of rings and spokes, on steel base rails.",
          [_p("Chiller", G.chiller, "Iron Gray Metallic", 2, (G.CHILL_BASE, "Light Gray"))],
          "21.99", "HO Scale Industrial Chillers 2 pc | Air-Cooled HVAC Units Flatcar Load | Printed in Color | 1:87",
          ["industrial load", "hvac unit", "chiller", "data center", "rooftop unit", "modern industry", "factory load",
           "flatcar load", "ho scale load"] + _TAIL,
          dict(ebay="HO Scale Air-Cooled Chiller HVAC Units 2 pc Flatcar Load Industrial 1:87",
               car="an 89 ft flatcar (two), or one on a 40 ft flat", era="Modern (1980s-present)",
               colors="Light Gray, Iron Gray", ship=6.5, pack=1.50)),
    _load("propane", "Propane Tank Load", 2,
          "Six new 1,000 gallon propane tanks for a 53 ft bulkhead flat, in pairs on dunnage: 2:1 heads, saddle legs, the "
          "valve dome with its hinged lid, a lifting lug and a nameplate on each. Each shell rides on a cradle web pierced "
          "with openings.",
          [_p("Propane-pair", G.propane_pair, "Cocoa Brown", 3, (G.PROP_DUN, "White"))],
          "16.99", "HO Scale Propane Tanks 6 pc | 1000 Gallon Tank Bulkhead Flatcar Load | Printed in Color | 1:87",
          ["propane tanks", "ho propane", "lp gas tank", "fuel dealer", "storage tank", "bulkhead flatcar",
           "industrial load", "flatcar load", "ho scale load"] + _TAIL,
          dict(ebay="HO Scale 1000 Gallon Propane Tanks 6 pc Bulkhead Flatcar Load 1:87 Printed",
               car="a 53 ft bulkhead flatcar (six), or a fuel dealer's yard", era="Transition / Modern (1950s-present)",
               colors="White, Brown", ship=5.5, pack=1.25)),
    _load("miltrucks", "Military Cargo Truck Load", 2,
          "Two 6x6 military cargo trucks for a 53 ft flatcar: hood with grille, headlights and brush guard, flat fenders, "
          "a hard cab with its windshield and doors, the cargo bed with a canvas cover over its bows and rope tie-downs, "
          "the exhaust stack. The black chassis (frame, bumper and winch, springs, axles and differentials, six lugged "
          "tires, tanks) and the olive body print separately and glue on the frame rails. Generic.",
          [_p("Truck-chassis", G.mt_chassis, "Black", 2), _p("Truck-body", G.mt_body, "Bronze", 2)],
          "17.99", "HO Scale Military 6x6 Cargo Trucks 2 pc | Army Flatcar Load | Olive Drab, Printed | 1:87",
          ["military truck", "army truck", "ho military", "6x6 truck", "military load", "army train", "cargo truck",
           "flatcar load", "ho scale load"] + _TAIL,
          dict(ebay="HO Scale Military 6x6 Cargo Trucks 2 pc Army Flatcar Load Olive Drab 1:87",
               car="a 53 ft flatcar (two)", era="Transition / Modern (1950s-present)", colors="Olive Drab, Black",
               ship=5.5, pack=1.25)),
    _load("culverts", "Precast Box Culvert Load", 2,
          "Four 8 x 6 ft precast concrete box culvert sections for a 40 ft flatcar, each on two timbers: 8 in walls with "
          "haunched corners, the tongue at one end and the groove's lip at the other, lifting inserts on top and the size "
          "stencilled on the side. You can see right through them.",
          [_p("Box-culvert", G.box_culvert, "Cocoa Brown", 4, (G.CULV_DUN, "Light Gray"))],
          "16.99", "HO Scale Precast Box Culverts 4 pc | Concrete Flatcar Load, Highway Construction | Printed | 1:87",
          ["box culvert", "precast concrete", "concrete load", "road construction", "highway project", "culvert",
           "construction load", "flatcar load", "ho scale load"] + _TAIL,
          dict(ebay="HO Scale Precast Concrete Box Culverts 4 pc Flatcar Load Highway Construction 1:87",
               car="a 40 ft flatcar (four)", era="Transition / Modern (1950s-present)", colors="Light Gray, Brown", ship=5.5, pack=1.25)),
    _load("conpipe", "Concrete Pipe Load", 2,
          "Nine 48 in reinforced concrete pipes for a 40 ft flatcar, lying across the car three to a row with their bells at "
          "alternate ends, on dunnage. You can see through every bore, and each pipe has its lifting holes.",
          [_p("Concrete-pipe-row", G.rcp_row, "Cocoa Brown", 3, (G.RCP_DUN, "Light Gray"))],
          "16.99", "HO Scale Concrete Sewer Pipe Load 9 pc | 48 in RCP Flatcar Load | Printed in Color | 1:87",
          ["concrete pipe", "sewer pipe", "rcp pipe", "culvert pipe", "precast concrete", "road construction",
           "construction load", "flatcar load", "ho scale load"] + _TAIL,
          dict(ebay="HO Scale 48 in Reinforced Concrete Pipe 9 pc Flatcar Load Sewer Culvert 1:87",
               car="a 40 ft flatcar (three rows)", era="Any (steam to modern)", colors="Light Gray, Brown", ship=5.5, pack=1.25)),
    _load("barriers", "Jersey Barrier Load", 2,
          "Twelve 12 ft New Jersey concrete median barriers to the standard profile, with pin-and-loop connectors at the "
          "ends, scuppers through the base and a lifting hole. Three across and four along fill a 53 ft flat; they "
          "work as well on any highway or work-zone scene.",
          [_p("Jersey-barrier", G.jersey_barrier, "Light Gray", 12)],
          "14.99", "HO Scale Jersey Barriers 12 pc | Concrete Highway Median Barrier, Flatcar Load | Printed | 1:87",
          ["jersey barrier", "concrete barrier", "highway barrier", "road construction", "work zone", "ho scale road",
           "precast concrete", "flatcar load", "ho scale load"] + _TAIL,
          dict(ebay="HO Scale Concrete Jersey Barriers 12 pc Flatcar Load Highway Work Zone 1:87",
               car="a 53 ft flatcar (twelve), or any road scene", era="Transition / Modern (1960s-present)",
               colors="Light Gray", ship=4.5, pack=1.00)),
    _load("manholes", "Precast Manhole Load", 2,
          "Eight precast concrete manhole sections on pallets for a 40 ft flatcar: two bases with pipe knockouts, risers "
          "2, 3 and 4 ft tall with their joint tongues, and two eccentric cones, each with lifting holes and the steps' "
          "stubs inside. They print standing, perfectly round.",
          [_p("Manhole-base", lambda: G.manhole("base", 4.0), "Cocoa Brown", 2, (G.MH_PAL, "Light Gray")),
           _p("Manhole-riser-4ft", lambda: G.manhole("riser", 4.0), "Cocoa Brown", 1, (G.MH_PAL, "Light Gray")),
           _p("Manhole-riser-3ft", lambda: G.manhole("riser", 3.0), "Cocoa Brown", 2, (G.MH_PAL, "Light Gray")),
           _p("Manhole-riser-2ft", lambda: G.manhole("riser", 2.0), "Cocoa Brown", 1, (G.MH_PAL, "Light Gray")),
           _p("Manhole-cone", lambda: G.manhole("cone"), "Cocoa Brown", 2, (G.MH_PAL, "Light Gray"))],
          "15.99", "HO Scale Precast Manhole Sections 8 pc | Concrete Flatcar Load, Construction | Printed in Color | 1:87",
          ["manhole", "precast concrete", "concrete load", "sewer project", "road construction", "utility",
           "construction load", "flatcar load", "ho scale load"] + _TAIL,
          dict(ebay="HO Scale Precast Concrete Manhole Sections 8 pc on Pallets Flatcar Load 1:87",
               car="a 40 ft flatcar (eight)", era="Transition / Modern (1950s-present)", colors="Light Gray, Brown", ship=5.5, pack=1.25)),
    _load("doubletees", "Precast Double Tee Load", 2,
          "Three 40 ft precast prestressed double tees for a parking-deck job, stacked on a 53 ft flatcar: an 8 ft flange "
          "with weld plates along its edges and two tapered stems with bearing plates, each tee on its own dunnage. "
          "Printed flange down, the dunnage in its own colour on top.",
          [_p("Double-tee", G.double_tee, "Light Gray", 3, (G.DT_DEPTH, "Cocoa Brown"))],
          "17.99", "HO Scale Precast Concrete Double Tees 3 pc | 40 ft Flatcar Load, Parking Deck | Printed | 1:87",
          ["double tee", "precast concrete", "concrete load", "parking garage", "construction", "bridge beam load",
           "modern railroad", "flatcar load", "ho scale load"] + _TAIL,
          dict(ebay="HO Scale Precast Concrete Double Tee Beams 3 pc 40 ft Flatcar Load 1:87",
               car="a 53 ft flatcar (three stacked)", era="Modern (1970s-present)", colors="Light Gray, Brown", ship=6.5, pack=1.50)),
    _load("rebar", "Rebar Bundle Load", 2,
          "Two lifts of 40 ft rebar for a 53 ft flatcar or a gondola, seven bundles to a lift on dunnage: every bar's line "
          "showing down each bundle, the ends ragged with bars of a little different length, wire ties every 8 ft, in "
          "mill rust.",
          [_p("Rebar-lift", G.rebar_lift, "Cocoa Brown", 1, (G.REBAR_DUN, "Copper Brown Metallic")),
           _p("Rebar-lift-B", lambda: G.rebar_lift(seed=6), "Cocoa Brown", 1, (G.REBAR_DUN, "Copper Brown Metallic"))],
          "14.99", "HO Scale Rebar Bundles 2 Lifts | Steel Reinforcing Bar Flatcar Gondola Load | Printed | 1:87",
          ["rebar load", "steel load", "reinforcing bar", "construction", "steel mill", "gondola load", "steel bundles",
           "flatcar load", "ho scale load"] + _TAIL,
          dict(ebay="HO Scale Rebar Bundle Load 2 Lifts Steel Reinforcing Bar Flatcar Gondola 1:87",
               car="a 53 ft flatcar or a gondola", era="Any (steam to modern)", colors="Rust, Brown", ship=5.5, pack=1.25)),
    _load("sheetpile", "Steel Sheet Piling Load", 2,
          "Two tiers of 40 ft steel Z-pile sheet piling for a 42 ft flatcar, three bundles to a tier: each bundle eight "
          "piles nested deep, the trapezoid wave showing at the ends with every pile's end its own, banded twice on dunnage.",
          [_p("Sheet-pile-tier", G.sheet_pile_tier, "Cocoa Brown", 1, (G.SP_DUN, "Iron Gray Metallic")),
           _p("Sheet-pile-tier-B", lambda: G.sheet_pile_tier(seed=3), "Cocoa Brown", 1, (G.SP_DUN, "Iron Gray Metallic"))],
          "15.99", "HO Scale Steel Sheet Piling Bundles | Z-Pile Flatcar Load, Construction | Printed in Color | 1:87",
          ["sheet piling", "steel piling", "steel load", "construction", "bridge project", "marine construction",
           "steel bundles", "flatcar load", "ho scale load"] + _TAIL,
          dict(ebay="HO Scale Steel Sheet Piling Z-Pile Bundles Flatcar Load Construction 1:87",
               car="a 42 ft flatcar (two tiers) or a gondola", era="Transition / Modern (1950s-present)",
               colors="Dark Gray, Brown", ship=5.5, pack=1.25)),
    _load("poles", "Utility Pole Load", 2,
          "Twenty-six treated wood utility poles, 45 ft, for a 50 ft flatcar: piled eight, seven, six and five on six bunks "
          "with stakes, butts at alternate ends, each pole tapered from a 12 in butt to a 7 in top with its roof cut and a "
          "brand plate near the butt, wire-rope wrappers over the end bunks.",
          [_p("Pole-pile", G.pole_pile, "Caramel", 1, (G.POLE_BUNK, "Black Walnut"))],
          "17.99", "HO Scale Utility Pole Load | 45 ft Treated Wood Poles on Bunks with Stakes | Printed | 1:87",
          ["utility poles", "telephone poles", "power poles", "wood poles", "pole load", "utility load", "treated wood",
           "flatcar load", "ho scale load"] + _TAIL,
          dict(ebay="HO Scale Treated Wood Utility Pole Flatcar Load 45 ft Poles on Bunks 1:87",
               car="a 50 ft flatcar", era="Any (steam to modern)", colors="Dark Brown, Tan", ship=6.5, pack=1.50)),
    _load("crushed", "Crushed Car Scrap Load", 2,
          "Three stacks of crushed cars on their way to the shredder, six to a stack, for a 53 ft flatcar or a gondola: each "
          "body flattened into a crumpled slab with its window openings, wheel wells, bumpers and seams, each car a "
          "little askew on the one below. Every stack prints in two colours, three cars of each.",
          [_p("Crushed-stack-red-grey", lambda: G.crushed_stack(1), "Red", 1, (G.CRUSH_CHANGE, "Light Gray")),
           _p("Crushed-stack-blue-rust", lambda: G.crushed_stack(2), "Cobalt Blue", 1, (G.CRUSH_CHANGE, "Copper Brown Metallic")),
           _p("Crushed-stack-green-black", lambda: G.crushed_stack(3), "Mistletoe Green", 1, (G.CRUSH_CHANGE, "Black"))],
          "16.99", "HO Scale Crushed Car Scrap Load 3 Stacks | Scrapyard Flatcar Gondola Load | Printed in Color | 1:87",
          ["crushed cars", "scrap load", "scrap metal", "junkyard", "scrapyard", "auto salvage", "gondola load",
           "flatcar load", "ho scale load"] + _TAIL,
          dict(ebay="HO Scale Crushed Car Scrap Load 3 Stacks 18 Cars Flatcar Gondola Scrapyard 1:87",
               car="a 53 ft flatcar or a gondola", era="Transition / Modern (1960s-present)",
               colors="Red, Blue, Green, Gray, Rust, Black", ship=5.5, pack=1.25)),
    _load("giantlog", "Giant Log Load", 3,
          "One log of an old-growth fir, 9 ft through and 32 ft long, like the famous one-log loads of the logging days: "
          "deep bark furrows, two springboard notches near the butt, the saw cut on both ends with its rings and checks, "
          "two binder chains, riding on timber sills with a chock at each end. For a 40 ft flatcar.",
          [_p("Giant-log", G.giant_log, "Cocoa Brown", 1, (G.GLOG_SILL, "Dark Brown"))],
          "18.99", "HO Scale Giant Old-Growth Log | One Log Flatcar Load, Logging History | Printed in Color | 1:87",
          ["giant log", "logging railroad", "old growth log", "redwood log", "one log load", "logging camp", "steam era",
           "flatcar load", "ho scale load"] + _TAIL,
          dict(ebay="HO Scale Giant Old Growth Log One Log Flatcar Load Logging Railroad 1:87",
               car="a 40 ft flatcar", era="Steam (1890s-1940s)", colors="Dark Brown, Brown", ship=5.5, pack=1.25)),
    _load("pulpwood", "Pulpwood Load", 2,
          "Three sections of 8 ft pulpwood piled crosswise for a 40 ft pulpwood car, 9 ft high: both sides a mosaic of cut "
          "ends, each stick its own size and standing a little proud or short, with its bark ring, and the top course in "
          "bark. Cut ends in fresh wood, the top course in bark brown.",
          [_p("Pulpwood-section", G.pulpwood_rack, "Latte Brown", 2, (G.PULP_H_CHANGE, "Dark Brown")),
           _p("Pulpwood-section-B", lambda: G.pulpwood_rack(seed=4), "Latte Brown", 1, (G.PULP_H_CHANGE, "Dark Brown"))],
          "16.99", "HO Scale Pulpwood Load 3 Sections | 8 ft Pulpwood for Pulpwood Car | Printed in Color | 1:87",
          ["pulpwood load", "pulpwood car", "paper mill", "logging railroad", "cordwood", "pulp mill", "wood load",
           "flatcar load", "ho scale load"] + _TAIL,
          dict(ebay="HO Scale Pulpwood Load 3 Sections 8 ft Sticks for Pulpwood Car Paper Mill 1:87",
               car="a 40 ft pulpwood car or a flat with end racks", era="Steam / Transition (1920s-1990s)",
               colors="Tan, Dark Brown", ship=5.5, pack=1.25)),
    _load("truss", "Pony Truss Bridge Load", 2,
          "The steel of a 50 ft riveted Warren pony truss on its way to the job, for a 53 ft flatcar: two truss sides "
          "standing on notched blocking (top chords laced, inclined end posts, diagonals and verticals, gusset plates at "
          "every joint, bearing shoes) and the bundle of six 16 ft floor beams. The sides print flat; set them on your "
          "piers with the floor beams and it is a bridge.",
          [_p("Truss-side", G.truss_side, "Black", 2), _p("Floor-beams", G.floor_beam_bundle, "Cocoa Brown", 1, (1.2, "Black")),
           _p("Truss-blocking", G.truss_blocking, "Cocoa Brown", 3)],
          "19.99", "HO Scale Pony Truss Bridge Steel Flatcar Load | 50 ft Warren Truss, Also a Bridge | Printed | 1:87",
          ["pony truss", "truss bridge", "ho bridge", "bridge steel", "railroad bridge", "steel load", "bridge kit",
           "flatcar load", "ho scale load"] + _TAIL,
          dict(ebay="HO Scale 50 ft Pony Truss Bridge Steel Flatcar Load Warren Truss Bridge 1:87",
               car="a 53 ft flatcar (the beams ride on a second flat or a gondola)", era="Steam / Transition (1900s-1960s)",
               colors="Black, Brown", ship=6.5, pack=1.50)),
    _load("rotor", "Generator Rotor Load", 2,
          "A turbine-generator's rotor on its shipping skid for a 53 ft flatcar: the forged body with its winding slots and "
          "two pole faces, a retaining ring and fan at each end, journals on saddles, the coupling flange with its bolt "
          "circle and the collector rings, carried on a pierced cradle. Rotor in steel silver, skid and cradle black.",
          [_p("Generator-rotor", G.generator_rotor, "Black", 1, (G.ROTOR_CHANGE, "Silver"))],
          "17.99", "HO Scale Generator Rotor Flatcar Load | Power Plant Heavy Load on Skid | Printed in Color | 1:87",
          ["generator rotor", "power plant", "turbine load", "heavy load", "industrial load", "electric utility",
           "power station", "flatcar load", "ho scale load"] + _TAIL,
          dict(ebay="HO Scale Turbine Generator Rotor Flatcar Load Power Plant 1:87 Printed",
               car="a 53 ft flatcar", era="Transition / Modern (1950s-present)", colors="Silver, Black", ship=5.5, pack=1.25)),
    _load("stator", "Generator Stator Load", 1,
          "A generator stator 12 ft through and 28 ft long for a depressed-centre flatcar, riding as a dimensional load: the "
          "welded frame with ring stiffeners and longitudinal bars, bolted end covers, the terminal box on top with six "
          "bushings, four lifting trunnions and the nameplate, on its cradle and skid.",
          [_p("Generator-stator", G.generator_stator, "Black", 1, (G.STATOR_CHANGE, "Gray"))],
          "24.99", "HO Scale Generator Stator Load | Depressed Center Flatcar Heavy Load, Power Plant | Printed | 1:87",
          ["generator stator", "power plant", "heavy load", "depressed flatcar", "dimensional load", "electric utility",
           "power station", "flatcar load", "ho scale load"] + _TAIL,
          dict(ebay="HO Scale Generator Stator Heavy Load for Depressed Center Flatcar Power Plant 1:87",
               car="a depressed-centre flatcar (it sits in the well)", era="Transition / Modern (1950s-present)",
               colors="Gray, Black", ship=8.0, pack=2.50)),
    _load("tubebundle", "Heat Exchanger Tube Bundle Load", 2,
          "A shell-and-tube heat exchanger's tube bundle, out of its shell, for a 42 ft flatcar: the tubesheet with its bolt "
          "ring, tube-end pattern and lifting lugs, every tube's line along the bundle, segmental baffles every 2 ft with "
          "their cuts alternating, and the floating head with its domed cover. Copper tubes, black cradle and skid.",
          [_p("Tube-bundle", G.tube_bundle, "Black", 1, (G.TB_CHANGE, "Copper Brown Metallic"))],
          "16.99", "HO Scale Heat Exchanger Tube Bundle Flatcar Load | Refinery Chemical Plant | Printed | 1:87",
          ["heat exchanger", "tube bundle", "refinery load", "chemical plant", "industrial load", "oil refinery",
           "petrochemical", "flatcar load", "ho scale load"] + _TAIL,
          dict(ebay="HO Scale Heat Exchanger Tube Bundle Flatcar Load Refinery Chemical Plant 1:87",
               car="a 42 ft flatcar", era="Transition / Modern (1950s-present)", colors="Copper, Black", ship=5.5, pack=1.25)),
    _load("column", "Distillation Column Load", 1,
          "A refinery distillation column, 56 ft, shipped lying on three cradles for a 60 ft flatcar: the shell with girth "
          "seams, the 2:1 top head, the skirt with its access opening and base ring, nozzles and manways, the ladder "
          "clipped along the top and rings of platform brackets.",
          [_p("Column", G.column, "Black", 1, (G.COL_CHANGE, "Light Gray"))],
          "24.99", "HO Scale Refinery Distillation Column Flatcar Load | 56 ft Tower on Cradles | Printed | 1:87",
          ["refinery load", "distillation tower", "oil refinery", "chemical plant", "pressure vessel", "heavy load",
           "petrochemical", "flatcar load", "ho scale load"] + _TAIL,
          dict(ebay="HO Scale Refinery Distillation Column 56 ft Flatcar Load on Cradles 1:87",
               car="a 60 ft flatcar", era="Transition / Modern (1950s-present)", colors="Light Gray, Black", ship=8.0, pack=2.50)),
    _load("gear", "Girth Gear Load", 2,
          "The two halves of a 20 ft girth gear for a cement kiln or a grinding mill, lying face down on timbers on a 40 ft "
          "flatcar: the toothed rim, the web with its radial ribs, the inner flange and the split flanges with their bolt "
          "heads.",
          [_p("Girth-gear-half", G.girth_gear_half, "Cocoa Brown", 2, (G.GEAR_SKID, "Gray"))],
          "17.99", "HO Scale Girth Gear Halves 2 pc | Cement Kiln Mill Gear Flatcar Load | Printed in Color | 1:87",
          ["girth gear", "ring gear", "cement plant", "mining load", "heavy load", "industrial load", "big gear",
           "flatcar load", "ho scale load"] + _TAIL,
          dict(ebay="HO Scale Girth Gear Halves Cement Kiln Mill Gear Flatcar Load 1:87 Printed",
               car="a 40 ft flatcar (both halves)", era="Any (steam to modern)", colors="Gray, Brown", ship=5.5, pack=1.25)),
    _load("genset", "Diesel Genset Load", 2,
          "A 40 ft enclosed diesel generator set for a 53 ft flatcar: the sound-attenuated housing with four pairs of doors a "
          "side, handles and louvres, the radiator end's louvre wall, two silencers with rain caps and the radiator's "
          "discharge hood on the roof, corner castings, on its fuel-tank base.",
          [_p("Genset", G.genset, "Black", 1, (G.GENSET_BASE, "Bone White"))],
          "18.99", "HO Scale Enclosed Diesel Generator Set Flatcar Load | Power Module | Printed in Color | 1:87",
          ["generator load", "diesel genset", "power module", "industrial load", "data center", "electric utility",
           "modern industry", "flatcar load", "ho scale load"] + _TAIL,
          dict(ebay="HO Scale 40 ft Enclosed Diesel Generator Set Flatcar Load Power Module 1:87",
               car="a 53 ft flatcar", era="Modern (1980s-present)", colors="White, Black", ship=6.5, pack=1.50)),
    _load("boiler", "Package Boiler Load", 2,
          "A firetube package boiler, 8 ft by 22 ft, for a 40 ft flatcar: the jacketed shell with its bands, the front door "
          "with the burner housing and blower, the rear door and sight port, the flue outlet, steam nozzle and safety "
          "valves on top, the water column with its gauge glass, lifting lugs, on its saddles and base.",
          [_p("Package-boiler", G.package_boiler, "Black", 1, (G.BOIL_CHANGE, "Mistletoe Green"))],
          "17.99", "HO Scale Industrial Package Boiler Flatcar Load | Factory Power House | Printed in Color | 1:87",
          ["boiler load", "industrial boiler", "power house", "factory load", "steam plant", "industrial load",
           "heavy load", "flatcar load", "ho scale load"] + _TAIL,
          dict(ebay="HO Scale Industrial Firetube Package Boiler Flatcar Load Factory 1:87 Printed",
               car="a 40 ft flatcar", era="Transition / Modern (1950s-present)", colors="Green, Black", ship=5.5, pack=1.25)),
    _load("locoboiler", "Locomotive Boiler Load", 1,
          "A steam locomotive's boiler out of its frames on its way to the shop or a museum, for a 42 ft flatcar: the wide "
          "radial-stay firebox with staybolt heads over its sides and crown, the mud ring and washout plugs, the backhead "
          "and firedoor; the tapered barrel with course seams, steam dome and check-valve bosses; the smokebox with its "
          "stack base and hinged front door. On timber blocking and a cradle.",
          [_p("Locomotive-boiler", G.loco_boiler, "Cocoa Brown", 1, (G.LB_BLOCK, "Iron Gray Metallic"))],
          "21.99", "HO Scale Steam Locomotive Boiler Flatcar Load | Restoration Shop Move | Printed in Color | 1:87",
          ["locomotive boiler", "steam locomotive", "steam era", "restoration", "railroad shop", "railroad museum",
           "heavy load", "flatcar load", "ho scale load"] + _TAIL,
          dict(ebay="HO Scale Steam Locomotive Boiler Flatcar Load Restoration Shop Move 1:87",
               car="a 42 ft flatcar", era="Any (steam to museum days)", colors="Iron Gray, Brown", ship=6.5, pack=1.50)),
    _load("wheelsets", "Freight Car Wheelset Load", 2,
          "Twelve freight-car wheelsets for a 40 ft flatcar, four to a row standing on timber rails: 36 in wheels with their "
          "flanges and dished plates, hubs, axles, roller-bearing caps on the journals with a block under each. In "
          "rust, for the shop track or the wheel shop.",
          [_p("Wheelset-row", G.wheelset_row, "Cocoa Brown", 3, (G.WS_TIMBER, "Copper Brown Metallic"))],
          "15.99", "HO Scale Freight Car Wheelsets 12 pc on Timber Rails | Flatcar MOW Shop Load | Printed | 1:87",
          ["wheelsets", "wheel load", "railroad shop", "mow train", "car shop", "freight car parts", "rail yard",
           "flatcar load", "ho scale load"] + _TAIL,
          dict(ebay="HO Scale Freight Car Wheelsets 12 pc Flatcar Load Shop MOW 1:87 Printed",
               car="a 40 ft flatcar or a gondola", era="Transition / Modern (1950s-present)", colors="Rust, Brown", ship=5.5, pack=1.25)),
    _load("girderspan", "Plate Girder Span Load", 2,
          "A 50 ft riveted deck plate girder railroad span, assembled, on blocking on a 53 ft flatcar: two 5 ft girders "
          "with flange angles and cover plates, stiffeners every 5 ft and doubled at the bearings, five diaphragms and the "
          "top lateral bracing. Set it on your abutments and it is a bridge.",
          [_p("Plate-girder-span", G.plate_girder_span, "Cocoa Brown", 1, (G.PGS_BLOCK, "Black"))],
          "18.99", "HO Scale 50 ft Plate Girder Bridge Span Flatcar Load | Also a Bridge | Printed in Color | 1:87",
          ["plate girder", "ho bridge", "railroad bridge", "girder bridge", "bridge span", "bridge kit", "steel load",
           "flatcar load", "ho scale load"] + _TAIL,
          dict(ebay="HO Scale 50 ft Deck Plate Girder Bridge Span Flatcar Load Railroad Bridge 1:87",
               car="a 53 ft flatcar", era="Any (steam to modern)", colors="Black, Brown", ship=6.5, pack=1.50)),
    _load("windblade", "Wind Turbine Blade Load", 1,
          "A 37 m wind turbine blade on two flatcars, the way blades ride: the root bolted to its steel root fixture on an 89 "
          "ft flat and the outboard part in a tip cradle on the next car. The round root with its bolt circle swells into "
          "the airfoil at its widest chord and tapers to the tip. The blade prints in three sections that key together "
          "with pegs on the flat side. Matches our wind tower section and nacelle loads.",
          [_p("Blade-root", lambda: G.blade_section(0), "White", 1), _p("Blade-middle", lambda: G.blade_section(1), "White", 1),
           _p("Blade-tip", lambda: G.blade_section(2), "White", 1), _p("Root-fixture", G.blade_root_fixture, "Cobalt Blue", 1),
           _p("Tip-cradle", G.blade_tip_cradle, "Cobalt Blue", 1)],
          "29.99", "HO Scale Wind Turbine Blade 2-Car Flatcar Load | 37 m Blade with Fixtures | Printed | 1:87",
          ["wind turbine blade", "wind blade load", "wind turbine", "wind farm", "dimensional load", "89 ft flatcar",
           "modern railroad", "flatcar load", "ho scale load"] + _TAIL,
          dict(ebay="HO Scale Wind Turbine Blade Load 37 m Blade with Root Fixture and Tip Cradle 1:87",
               car="an 89 ft flatcar and a 60 ft flat (or an idler)", era="Modern (2000-present)",
               colors="White, Blue", ship=8.0, pack=2.50)),
    _load("minecars", "Mine Car Load", 2,
          "Eight 36 in gauge V-dump ore cars for a 40 ft flatcar, new from the builder or moving between mines: each V body "
          "open at the top with its rim angle and ribs, rocking on two curved cradles, end sills with link-and-pin pockets, "
          "four 14 in wheels, on two timbers.",
          [_p("Mine-car", G.mine_car, "Cocoa Brown", 8, (G.MINE_TIMBER, "Red"))],
          "15.99", "HO Scale Narrow Gauge Mine Cars 8 pc | V-Dump Ore Cars Flatcar Load | Printed in Color | 1:87",
          ["mine cars", "ore cars", "narrow gauge", "mining railroad", "gold mine", "mining load", "steam era",
           "flatcar load", "ho scale load"] + _TAIL,
          dict(ebay="HO Scale Narrow Gauge V-Dump Mine Cars 8 pc Flatcar Load Mining 1:87",
               car="a 40 ft flatcar (eight), or a mine scene", era="Steam / Transition (1880s-1960s)",
               colors="Red, Brown", ship=5.5, pack=1.25)),
    _load("joists", "Steel Joist Load", 2,
          "Two tiers of 40 ft open-web steel joists for a 42 ft flatcar, four bundles to a tier, eight joists to a bundle "
          "laid on their sides and banded: from above every joist's zigzag web and bearing seats show. In shop primer "
          "grey on dunnage.",
          [_p("Joist-tier", G.joist_bundles, "Cocoa Brown", 2, (G.JOIST_DUN, "Gray"))],
          "15.99", "HO Scale Open Web Steel Joists Bundles | Bar Joist Flatcar Load, Construction | Printed | 1:87",
          ["steel joists", "bar joists", "steel load", "construction", "building steel", "warehouse build",
           "steel bundles", "flatcar load", "ho scale load"] + _TAIL,
          dict(ebay="HO Scale Open Web Steel Bar Joist Bundles Flatcar Load Construction 1:87",
               car="a 42 ft flatcar (two tiers)", era="Transition / Modern (1950s-present)", colors="Gray, Brown",
               ship=5.5, pack=1.25)),
    _load("copper", "Copper Cathode Load", 2,
          "Sixteen bundles of copper cathode sheets from the refinery for a 40 ft flatcar or a gondola, stacked two high: "
          "each about a metre square, eight sheets a little out of line, the top sheet's nodular face, banded twice each "
          "way on two skids. Printed in metallic copper.",
          [_p("Cathode-bundle", G.cathode_bundle, "Cocoa Brown", 8, (G.CU_SKID, "Copper Brown Metallic")),
           _p("Cathode-bundle-B", lambda: G.cathode_bundle(seed=2), "Cocoa Brown", 8, (G.CU_SKID, "Copper Brown Metallic"))],
          "15.99", "HO Scale Copper Cathode Bundles 16 pc | Refinery Smelter Flatcar Gondola Load | Printed | 1:87",
          ["copper cathodes", "copper load", "copper refinery", "smelter", "mining load", "metal load", "gondola load",
           "flatcar load", "ho scale load"] + _TAIL,
          dict(ebay="HO Scale Copper Cathode Bundles 16 pc Refinery Smelter Flatcar Gondola Load 1:87",
               car="a 40 ft flatcar or a gondola", era="Transition / Modern (1950s-present)", colors="Copper, Brown",
               ship=5.5, pack=1.25)),
    _load("farmtractors", "Steel-Wheel Tractor Load", 2,
          "Four 1920s steel-wheel farm tractors for a 40 ft flatcar, as they left the factory, two grey and two green: big "
          "rear wheels with spade lugs and flat spokes, spoked front wheels on a swinging axle, the radiator with its tubes "
          "and cap, engine, exhaust and air stack, fuel tank, gearcase, the steering column and wheel and the pan seat on "
          "its spring bar, each on two timbers. Generic.",
          [_p("Tractor-grey", G.farm_tractor, "Cocoa Brown", 2, (G.FT_TIMBER, "Gray")),
           _p("Tractor-green", G.farm_tractor, "Cocoa Brown", 2, (G.FT_TIMBER, "Mistletoe Green"))],
          "16.99", "HO Scale 1920s Steel Wheel Farm Tractors 4 pc | Flatcar Load, Steam Era | Printed in Color | 1:87",
          ["farm tractor", "vintage tractor", "steam era", "farm machinery", "antique tractor", "farm scene",
           "agriculture", "flatcar load", "ho scale load"] + _TAIL,
          dict(ebay="HO Scale 1920s Steel Wheel Farm Tractors 4 pc Flatcar Load Steam Era 1:87",
               car="a 40 ft flatcar (four in line)", era="Steam (1915-1940)", colors="Gray, Green, Brown", ship=5.5, pack=1.25)),
])

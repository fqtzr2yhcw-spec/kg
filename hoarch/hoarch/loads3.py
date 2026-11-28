"""Pack entries for the third series of flatcar loads (geometry in hoarch.flatloads3), made for the
0.2 mm nozzle (LOADS_BATCH3.md). Same schema as hoarch.loads2; hoarch.packs merges them in."""
from . import flatloads3 as G
from .loads2 import _TAIL, _load, _p


def _L(key, *a, **k):
    return _load(key, *a, scene=G.SCENES[key], **k)

PACKS3 = dict([
    _L("drivers", "Steam Locomotive Driver Load", 2,
          "Four 63 in driver sets for a heavy Mikado, on their way to or from the back shop on a 50 ft flatcar: sixteen "
          "spokes to a wheel, rounded on their faces, the crescent counterweights with their lead plugs, the crank pins "
          "quartered and the main set with its return cranks, tire faces, hubs and crank pins in bright steel; the "
          "journals resting on cribbed cradles with wedges; and both sides' main and side rods banded to a pallet, every "
          "rod fluted and every eye bushed in brass. Made for the 0.2 mm nozzle.",
          [_p("Driver", G.driver, "Black", 6, (G.DR_CHANGE, "Silver"), "tire face, hub and crank pin silver"),
           _p("Main-driver", G.main_driver, "Black", 2, (G.DR_CHANGE, "Silver"), "with the return crank"),
           _p("Axle", G.driver_axle, "Iron Gray Metallic", 4, None, "lies on its flat"),
           _p("Cradle", G.driver_cradle, "Cocoa Brown", 1, None, "cribbing for all four sets"),
           _p("Rod-pallet", G.rod_pallet, "Cocoa Brown", 1, (G.ROD_PALLET, "Silver"), "main and side rods on their pallet")],
          "29.99", "HO Scale Steam Locomotive Driver Sets and Rods | Back Shop Flatcar Load | Printed in Color | 1:87",
          ["steam locomotive", "driving wheels", "locomotive drivers", "back shop", "steam era", "roundhouse",
           "locomotive parts", "flatcar load", "ho scale load"] + _TAIL,
          dict(ebay="HO Scale Steam Locomotive Driver Sets and Rods Flatcar Load 1:87 Back Shop",
               car="a 50 ft flatcar, or a back shop scene", era="Steam (1900s-1950s)",
               colors="Black, Silver, Steel Gray, Brown", ship=6.0, pack=1.50),
          base_note="The wheels print flat on their inner faces, the axles on their flats, the cradle and the rod pallet "
                    "flat.",
          assembly=["Axles: each axle's ends go into two drivers' sockets. Turn the right-hand wheel so its crank pin is a "
                    "quarter turn ahead of the left-hand one (quartered, as on the locomotive), then glue.",
                    "The main drivers (with the return cranks) go on one axle together.",
                    "Lay each set on the cradle: the journals' flats sit on the blocks between the wedges. Glue them there.",
                    "The rod pallet goes at the end of the car."]),
    _L("castings", "Truck Side Frame and Bolster Load", 1,
          "A foundry's shipment of new 70-ton freight car truck castings for a 40 ft flatcar: thirty-two cast side frames "
          "in stacks of four, each with its bolster window, lightening openings, pedestal jaws with wear plates, "
          "friction-wedge column guides, brake hanger lugs and pattern plate, rimmed all round; and sixteen fish-belly "
          "bolsters bundled two layers deep, with centre plates, side bearings, gibs and pockets. All on dunnage. Made for "
          "the 0.2 mm nozzle.",
          [_p("Side-frame-stacks", G.side_frame_stacks, "Cocoa Brown", 4, (G.SF_DUN, "Black"), "two stacks of four on dunnage"),
           _p("Bolster-bundle", G.bolster_bundle, "Cocoa Brown", 2, (G.SF_DUN, "Black"), "eight bolsters on dunnage")],
          "24.99", "HO Scale Freight Car Truck Side Frames and Bolsters | Foundry Castings Flatcar Load | Printed | 1:87",
          ["truck side frames", "freight car trucks", "bolsters", "foundry", "castings", "car shop", "steel castings",
           "flatcar load", "ho scale load"] + _TAIL,
          dict(ebay="HO Scale Freight Car Truck Side Frames and Bolsters Foundry Flatcar Load 1:87",
               car="a 40 ft flatcar or a gondola", era="Transition / Modern (1950s-present)", colors="Black, Brown",
               ship=5.5, pack=1.25),
          base_note="Each stack and bundle stands on three dunnage strips; the castings above lie flat."),
    _L("bop", "Blowout Preventer Load", 1,
          "A wellhead blowout preventer stack, broken down for shipment on an oilfield skid for a 40 ft flatcar: the "
          "annular preventer with its bolted head and domed top on a shipping plate, a double ram preventer with stacked "
          "bonnets, operators and lock housings, the drilling spool with its choke and kill lines (a manual gate valve "
          "with a dished handwheel and a hydraulic one each side), and a single ram; every flange studded and nutted, "
          "twenty studs to a flange. Oilfield red. Made for the 0.2 mm nozzle. Generic: no maker's name.",
          [_p("BOP-skid", G.bop_skid, "Cocoa Brown", 1, (G.BOP_SKID, "Black"), "timber runners, then the steel deck"),
           _p("Annular", G.bop_annular, "Red", 1),
           _p("Double-ram", G.bop_double, "Red", 1),
           _p("Drilling-spool", G.bop_spool, "Red", 1),
           _p("Single-ram", G.bop_single, "Red", 1)],
          "34.99", "HO Scale Blowout Preventer BOP Stack | Oilfield Drilling Flatcar Load | Printed in Color | 1:87",
          ["blowout preventer", "oilfield", "drilling rig", "bop stack", "oil and gas", "wellhead", "fracking",
           "flatcar load", "ho scale load"] + _TAIL,
          dict(ebay="HO Scale Blowout Preventer BOP Stack Oilfield Flatcar Load 1:87 Drilling Rig",
               car="a 40 ft flatcar, or an oilfield or pipe yard scene", era="Modern (1970s-present)",
               colors="Red, Black, Brown", ship=5.5, pack=1.25),
          base_note="The skid stands on five timber runners; each preventer on its bottom flange and its stands.",
          assembly=["Glue the four preventers on the skid's deck in a row, the rams' operators along the car: annular, "
                    "double ram, drilling spool, single ram."]),
])

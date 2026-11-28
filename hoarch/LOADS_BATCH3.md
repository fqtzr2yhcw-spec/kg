# Batch 3: thirty fine-detail freight and flatcar loads (0.2 mm nozzle)

The owner, November 2026: "Lets make a project batch of 30 freight and flat car loads that take
advantage of the .02 detail", after the locomotive engine load's first print came out "really
good". Every load here is made for the 0.2 mm nozzle at 0.10 mm layers (`loadnames.NOZZLE`,
`LAYER`), held to the engine load's standard (NOTES.md, "Fine-nozzle loads"): detail down to 0.4 mm,
pieces in their colours with at most one change each, pegs or flat faces for every glue joint, no
supports, no weak connections, no floating regions. Parts loads only, no whole vehicles. None
repeats a load we already sell (the first two series: 71 loads).

Order of work: three pilots (marked P) for the owner's review, then the rest in groups of four or
five, each group rendered and shown before it is released.

| # | Load | What it is, and what the 0.2 detail adds | Car |
|---|------|-------------------------------------------|-----|
| 1 P | Steam Locomotive Driver Load | Four 63 in spoked driver sets for a heavy Mikado, quartered crank pins, crescent counterweights, the main set with its return cranks; journals on cribbed cradles; side and main rods banded to a pallet. Spokes, counterweight plugs, rod flutes. | 50 ft flat |
| 2 P | Truck Side Frame and Bolster Load | A foundry's shipment of new 70-ton truck castings: 32 side frames in stacks of four (bolster window, lightening openings, pedestal jaws with wear plates, column guides, brake hanger lugs, rims round every opening) and 16 fish-belly bolsters bundled two deep. Changed from complete trucks: a whole truck can't print in one piece without supports (its side frames hang below the axles), so it ships as castings, printed flat. | 40 ft flat or gondola |
| 3 | Diesel Locomotive Truck Load | Two three-axle road trucks: equalised frames, coil springs, brake cylinders and shoes, traction motor nose lugs, sand pipes. Needs the same care as the freight trucks: frames and wheelsets as separate pieces that peg together. | 40 ft flat |
| 4 | Traction Motor Load | Six traction motors with gear cases, axle caps, nose suspension lugs, terminal boxes, on cradles. | gondola or flat |
| 5 | Couplers and Draft Gear Load | Pallets of type E couplers, spare knuckles, yokes and draft gears, brake wheels, coiled air hoses. | gondola |
| 6 | Signal Department Load | Cantilever and searchlight signal masts with ladders and hoods, relay cases, crossing gate mechanisms, cable reels. | 50 ft flat |
| 7 | Locomotive Scrap Gondola Load | A steam locomotive cut up for scrap: domes, sand box, cab roof, rods, driver halves, firebox sheets with stay-bolt heads. | gondola |
| 8 | Boxcar Door Load | Racks of replacement plug and sliding doors with latch bars, hinges, door stops. | bulkhead flat |
| 9 | Gas Turbine Load | Power-plant combustion turbine in its shipping frame: split casing flanges with rows of bolts, inlet bell, exhaust diffuser. | depressed-centre flat |
| 10 | Hydro Turbine Runner Load | Francis runner, curved blades between crown and band, on a cradle. | depressed-centre flat |
| 11 | High-Voltage Circuit Breaker Load | Three dead-tank breakers with porcelain bushings (shed by shed), current transformers, control cabinets. | flat |
| 12 P | Blowout Preventer Load | A wellhead BOP stack broken down on a skid: annular, double ram with stacked bonnets and operators, drilling spool with choke and kill valves and handwheels, single ram; every flange studded and nutted. | 40 ft flat |
| 13 | Triplex Mud Pump Load | Drilling mud pump: three fluid-end modules with valve covers, pulsation dampener, bull gear housing, crosshead covers. | flat |
| 14 | Pipeline Valve Load | Large ball valves with gear operators and handwheels, weld ends and flanged ends, on skids. | flat |
| 15 | Refinery Pipe Spool Load | Fabricated spools: elbows, tees, reducers, weld-neck flanges with bolt circles, painted ends. | gondola or bulkhead flat |
| 16 | Gas Compressor Skid Load | Reciprocating compressor package: cylinders, scrubbers, piping, walkway grating. | flat |
| 17 | Steel Mill Ladle Load | Teeming ladle with trunnions, ribbed shell, refractory lip, slide gate. | depressed-centre flat |
| 18 | Mill Roll Load | Forged work and backup rolls with necks and bearing chocks, on cradles. | flat |
| 19 | Wire Rod Coil Load | Loose wound wire rod coils, every turn showing, with bands. | gondola or coil car |
| 20 | Yankee Dryer Load | Paper machine dryer cylinder: ribbed cast heads, bolt circles, journals. | depressed-centre flat |
| 21 | Mill Engine Flywheel Load | A split spoked flywheel in halves, bolted rim and hub joints, on cribbing. | flat |
| 22 | Jaw Crusher Load | Quarry jaw crusher: flywheels, pitman, toggle, ribbed frame. | flat |
| 23 | Tunnel Boring Machine Cutterhead Load | Cutterhead with disc cutters, muck buckets and spokes, on its frame. | depressed-centre flat |
| 24 | Overhead Crane Load | Bridge crane box girders with end trucks and a crated hoist trolley. | 60 ft flat |
| 25 | Crane Hook Block Load | Multi-sheave hook block, counterweight slabs, wire rope reels. | flat |
| 26 | Conveyor Equipment Load | Lagged head pulley with bearings, take-up pulley, racks of troughing idlers. | flat or gondola |
| 27 | Airliner Fuselage Section Load | Narrow-body fuselage sections: frames, window belt, door cut-outs, protective end covers. | two 89 ft flats |
| 28 | Rocket Motor Segment Load | Solid rocket motor segments with clevis joints and end covers on their cradles. | heavy flat |
| 29 | Combine Header Load | Draper header with reel tines, cutter bar and dividers, on a frame (an attachment, like the buckets). | 50 ft flat |
| 30 | Brewery Fermenter Load | Stainless cylindro-conical fermenters: manways, valves, sight glasses, legs. | flat |

## Pilot status (2026-11-28)
- 1 Steam Locomotive Driver Load (`drivers`): v1.0 packaged. Wheels print flat (spokes in the layer), axles
  on their flats, quartered at assembly; 1 h 25 m and 9 g a pack (two packs a run).
- 2 Truck Side Frame and Bolster Load (`castings`): v1.0 packaged; 2 h 23 m, 12 g.
- 12 Blowout Preventer Load (`bop`): v1.0 packaged; 2 h 1 m, 15 g. Stands under the bottom operators and the
  valves (as a BOP rides), the bodies grow out of their flanges at 45 degrees.

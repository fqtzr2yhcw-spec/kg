# The HO Victorian collection: plan and progress

Target: at least 10 unique, original HO (1:87.1) buildings, each designed to print well on
FDM (0.4 mm nozzle, 0.20 mm layers), with windows and doors as the standout detail
(sculpted mouldings: `hoarch/moulding.py`) and layered trim between the main parts.

Work order for each building: concept → print checks (0 interfering pairs, lint) → renders
(hero and a close-up) → commit. Export and slicing run in the background while the next
building is designed. At the end: a lineup render of the whole collection.

| # | Building | Style | Status |
|---|---|---|---|
| 1 | The Beaumont | Queen Anne | done: print files |
| 2 | The Ashby | Italianate villa | done: print files |
| 3 | The Harcourt | Second Empire | done: sculpted windows and door, re-sliced (13 h 27 m, 313 g) |
| 4 | The Fowler | Octagon house: two-layer eave, red standing-seam roof, octagonal cupola, three-face veranda, shutters | concept done, 78 parts, 0 interferences; slicing |
| 4b | The Whitby | Carpenter Gothic cottage: steep cross gables, lacy bargeboards, board-and-batten, lancet windows, Gothic porch | planned |
| 6 | The Delancey | San Francisco Italianate row house: two-storey slanted bay, false-front bracketed cornice, tall stoop | planned |
| 7 | The Ardmore | Richardsonian Romanesque: rock-faced stone, round tower with conical roof, great arched entry | planned |
| 8 | The Merritt | Stick style: stickwork panels, gable trusses, braced porch | planned |
| 9 | The Hollis | Folk Victorian farmhouse: L-plan, spindlework porch, gable ornaments | planned |
| 10 | The Carrow | Queen Anne castle: round turret, conical spire, wraparound porch | planned |

## Log
- Harcourt: sculpted Second Empire windows (pediment, drip hood) and grand door; ornament that only touched its frame now overlaps 0.2 mm (a surround in pieces now warns).
- Fowler: new two-layer eave (roof.frieze_ring under the bracketed cornice), door_se with an entablature hood.

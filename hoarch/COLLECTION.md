# The HO Victorian collection: plan and progress

Target: at least 10 unique, original HO (1:87.1) buildings, each designed to print well on
FDM (0.4 mm nozzle, 0.20 mm layers), with windows and doors as the standout detail
(sculpted mouldings: `hoarch/moulding.py`) and layered trim between the main parts.

Work order for each building: concept → print checks (0 interfering pairs, lint) → renders
(hero and a close-up) → commit. Export and slicing run in the background while the next
building is designed. All ten are done; the lineup render is `out/lineup/cycles/lineup.png`
(built by merging each building's render data). Every building has 0 interfering part pairs.

| # | Building | Style | Status |
|---|---|---|---|
| 1 | The Beaumont | Queen Anne: octagonal tower with a slate spire, fish-scale second storey, wraparound porch | done: print files (17 h 39 m, 385 g) |
| 2 | The Ashby | Italianate villa: paired-bracket eaves, cupola, canted bay, full-width porch | done: print files (12 h 55 m, 368 g) |
| 3 | The Harcourt | Second Empire: brick, slate mansard with nine dormers, centre tower, sculpted windows and door | done: print files (13 h 27 m, 313 g) |
| 4 | The Fowler | Octagon house: two-layer eave, red standing-seam roof, octagonal cupola, three-face veranda, shutters | done: 78 parts, print files (7 h 55 m, 210 g) |
| 5 | The Whitby | Carpenter Gothic cottage: four steep gables with pierced bargeboards, board-and-batten, patterned slate, traceried lancets under crocketed labels, crocketed gablets, diamond-paned gable lancets, Gothic entrance on engaged shafts, pointed-arch porch | done: 40 parts, print files (6 h 35 m, 133 g) |
| 6 | The Delancey | San Francisco Italianate row house: two-storey slanted bay with colonettes, rusticated front, two-layer cornice with flat roof, pedimented parapet, tall stoop, stone basement | done: 31 parts, print files (6 h 5 m, 177 g) |
| 7 | The Ardmore | Richardsonian Romanesque: rock-faced brownstone, round tower with an arcaded belvedere and conical roof, arched corbel tables, stone entrance loggia with a great arch, voussoir windows on cushion-capital colonnettes, arcaded triple window, hipped roof with front gable and hip caps | done: 53 parts, print files (9 h 24 m, 202 g) |
| 8 | The Merritt | Stick style: front-gabled with a cross-gabled wing, open gable trusses (collar, king post and drop, struts, fan of sticks), stickwork framing and X-braced panels, knee-braced deep eaves, crossed-stick window casings with pent hoods on braces, braced porch with a stick frieze | done: 49 parts, print files (8 h 24 m, 178 g) |
| 9 | The Hollis | Folk Victorian farmhouse: gable-front-and-wing L-plan, sunburst gable ornaments on spindle friezes over fish-scale shingles, pedimented window crowns with fans and dentils, louvered shutters, spindle porch in the corner of the L, red standing-seam roof | done: 67 parts, print files (5 h 46 m, 133 g) |
| 10 | The Carrow | Queen Anne castle: rock-faced stone first storey, lavender fish-scale shingled second storey with diamond bands, 12-sided turret rising to a bracketed cornice and a witch's-hat spire, patterned-slate hip with a front gable and pierced bargeboard, Queen Anne pediment and scroll windows, swan-neck entrance, wraparound turned porch with a chamfered corner | done: 66 parts, print files (8 h 31 m, 160 g) |

## Log
- Harcourt: sculpted Second Empire windows (pediment, drip hood) and grand door; ornament that only touched its frame now overlaps 0.2 mm (a surround in pieces now warns).
- Fowler: new two-layer eave (roof.frieze_ring under the bracketed cornice), door_se with an entablature hood.
- Delancey: colonettes on the bay corners, channel rustication siding, parapet printed on its back, stoop fitted round the stone base.
- Whitby: Gothic Revival windows and door (`window_gothic`, `door_gothic`: pointed arches, bar tracery, crockets, fleur finials, label stops, engaged shafts), gable walls built into the top wall shell (`wall_shell(gables=...)`), `gables.gabled_roof` (hollow roof body with rake skins and a fascia) and `gables.bargeboard`, board-and-batten siding (`core.battens`), Gothic porch arcade.
- Ardmore: Romanesque windows (`window_romanesque`: voussoir rings on a backing ring, cushion capitals, arcaded groups, heavy lintels) and doorways (`door_romanesque`, also as an open porch arch), arched corbel table, `gables.hip_cap` / `ridge_cap` / `chimney_seat`, tower wall carried down through the upper storey.
- Merritt: Stick-style windows and door (`window_stick`, `door_stick`), `gables.gable_truss`, braced porch arcade (`porch_turned(arcade="braced")`), stickwork siding hook that frames each window and X-braces the free panels, knee braces under the eaves.
- Hollis: Folk Victorian windows and door (`window_folk`, `door_folk`: crossetted casing, frieze panel, dentils, pediment with a fan or a cap), `gables.gable_sunburst`, shutters fitted only where a pair has room.
- Carrow: stone-and-shingle Queen Anne with a witch's-hat turret; ridge caps trimmed clear of the space under the rake skin (no nub under the gable peak).

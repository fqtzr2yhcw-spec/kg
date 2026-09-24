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
| 1 | The Beaumont | Queen Anne: octagonal tower with a hexagon-slate spire, beaded lap siding under a staggered-shingle second storey, wraparound turned porch | done: print files (17 h 39 m, 385 g) |
| 2 | The Ashby | Italianate villa: cream common-bond brick with quoins, paired-bracket eaves, V-groove cupola, canted bay, full-width porch on chamfered posts | done: print files (12 h 55 m, 368 g) |
| 3 | The Harcourt | Second Empire: Flemish-bond brick with a diaper, slate mansard with nine dormers, centre tower, sculpted windows and door, fluted portico | done: print files (13 h 27 m, 313 g) |
| 4 | The Fowler | Octagon house: scored stucco, two-layer eave on fan brackets, red 5V-crimp roof, octagonal cupola, Greek Revival windows, three-face veranda on Tuscan columns | done: 78 parts, print files (7 h 55 m, 210 g) |
| 5 | The Whitby | Carpenter Gothic cottage: four steep gables with pierced bargeboards, board-and-batten, patterned slate, traceried lancets under crocketed labels, crocketed gablets, diamond-paned gable lancets, Gothic entrance on engaged shafts, pointed-arch porch | done: 40 parts, print files (6 h 35 m, 133 g) |
| 6 | The Delancey | San Francisco Italianate row house: two-storey slanted bay with colonettes, rusticated front and drop-siding sides, San Francisco windows, two-layer cornice on pendant brackets, pedimented parapet, tall stoop, rusticated basement | done: 31 parts, print files (6 h 5 m, 177 g) |
| 7 | The Ardmore | Richardsonian Romanesque: rock-faced brownstone, round tower with an arcaded belvedere and conical clay-tile roof, arched corbel tables, stone entrance loggia with a great arch, voussoir windows on cushion-capital colonnettes, arcaded triple window, green clay-tile hipped roof with front gable and hip caps | done: 53 parts, print files (9 h 24 m, 202 g) |
| 8 | The Merritt | Stick style: front-gabled with a cross-gabled wing, open gable trusses (collar, king post and drop, struts, fan of sticks), stickwork framing and X-braced panels, knee-braced deep eaves, crossed-stick window casings with pent hoods on braces, braced porch with a stick frieze | done: 49 parts, print files (8 h 24 m, 178 g) |
| 9 | The Hollis | Folk Victorian farmhouse: gable-front-and-wing L-plan, Dutch lap siding with chevron-boarded gables, gingerbread gable ornaments, pedimented window crowns with fans and dentils, board shutters, spindle porch in the corner of the L, red pressed-metal shingle roof | done: 67 parts, print files (5 h 46 m, 133 g) |
| 10 | The Carrow | Queen Anne castle: Roman brick first storey, lavender half-timbered second storey, 12-sided turret rising to a dentilled cornice and a witch's-hat spire, diamond-slate hip with a front gable and Tudor truss, Free Classic windows with diamond-paned uppers, Palladian attic window, sidelighted entrance, wraparound Eastlake porch with a chamfered corner | done: 66 parts, print files (8 h 31 m, 160 g) |

## Log
- Uniqueness pass: every building has its own wall skin, porch (post, railing, frieze,
  skirt, piers), roof covering, chimney, foundation facing, belt course, eave bracket,
  finial, window and door family, sash pattern, gable ornament and shutter style (the table
  under "Unique parts per building"). Fish-scale shingles are retired. Wall, foundation and
  roof textures now sink 0.02-0.03 mm into their surface so none print as loose pieces.
- Harcourt: sculpted Second Empire windows (pediment, drip hood) and grand door; ornament that only touched its frame now overlaps 0.2 mm (a surround in pieces now warns).
- Fowler: new two-layer eave (roof.frieze_ring under the bracketed cornice), door_se with an entablature hood.
- Delancey: colonettes on the bay corners, channel rustication siding, parapet printed on its back, stoop fitted round the stone base.
- Whitby: Gothic Revival windows and door (`window_gothic`, `door_gothic`: pointed arches, bar tracery, crockets, fleur finials, label stops, engaged shafts), gable walls built into the top wall shell (`wall_shell(gables=...)`), `gables.gabled_roof` (hollow roof body with rake skins and a fascia) and `gables.bargeboard`, board-and-batten siding (`core.battens`), Gothic porch arcade.
- Ardmore: Romanesque windows (`window_romanesque`: voussoir rings on a backing ring, cushion capitals, arcaded groups, heavy lintels) and doorways (`door_romanesque`, also as an open porch arch), arched corbel table, `gables.hip_cap` / `ridge_cap` / `chimney_seat`, tower wall carried down through the upper storey.
- Merritt: Stick-style windows and door (`window_stick`, `door_stick`), `gables.gable_truss`, braced porch arcade (`porch_turned(arcade="braced")`), stickwork siding hook that frames each window and X-braces the free panels, knee braces under the eaves.
- Hollis: Folk Victorian windows and door (`window_folk`, `door_folk`: crossetted casing, frieze panel, dentils, pediment with a fan or a cap), `gables.gable_sunburst`, shutters fitted only where a pair has room.
- Carrow: stone-and-shingle Queen Anne with a witch's-hat turret; ridge caps trimmed clear of the space under the rake skin (no nub under the gable peak).

## Unique parts per building

Every building gets its own wall skin, porch, roof covering, chimney, foundation, belt
course, eave brackets, finial, windows, door, gable ornament and shutters: no two buildings
share any of them. Fish-scale ("U") shingles are retired everywhere (walls, roofs and spires).
The parts come from `hoarch/skins.py` (wall skins), `hoarch/porchwork.py` (posts, railings,
friezes, skirts), `hoarch/trimwork.py` (chimneys, finials, foundations, belts, brackets) and
`hoarch/openings.py` (window and door families, door leaves, transoms, sash patterns).

| Building | Walls | Foundation | Belt | Roof | Chimney | Finial |
|---|---|---|---|---|---|---|
| Beaumont | beaded lap siding; staggered shingles upstairs and on the tower | fieldstone | modillion | hexagon slate (tower spire too) | corbelled | urn |
| Ashby | common-bond brick with stone quoins | limestone ashlar | dentil | standing seam | stucco | acorn (cupola) |
| Harcourt | Flemish-bond brick with a diaper pattern | granite | stone | square and hexagon slate mansard | paneled | iron cresting finial |
| Fowler | scored stucco | brick | double | 5V crimp metal | banded | ball |
| Delancey | channel rustication front, drop siding sides | rusticated | panel | flat | slim | none |
| Whitby | board and batten | rubble | drip | square and diamond slate bands | diagonal | none |
| Ardmore | rock-faced ashlar | boulder | billet | clay tile (tower too) | stone | stack |
| Merritt | bevel clapboard with stickwork | parged | cleat | staggered shakes | ribbed | none |
| Hollis | Dutch lap siding, chevron boards in the gables | block | bead | small square metal shingles | plain | none |
| Carrow | Roman brick first storey, half-timber second storey and turret | coursed stone | boss | diamond slate (turret too) | arched | spire |

| Building | Porch: post / railing / frieze / skirt / piers | Windows and door | Gable, shutters, brackets |
|---|---|---|---|
| Beaumont | turned / turned / sawn / lattice / brick | Queen Anne windows; swan-neck door, arched leaves | shingled gables; no shutters; curve brackets |
| Ashby | chamfered / vase / scroll / panels / brick | Italianate arched 2-over-2; paired door | panel shutters; scroll brackets |
| Harcourt | fluted / urn / entablature / square / stone | Second Empire windows; door with arched-panel leaves, plain transom | block brackets |
| Fowler | tuscan / Chippendale / valance / diamond / plain | Greek Revival 6-over-6 with cornice heads; door with sidelights | louvered shutters; fan brackets |
| Delancey | stoop only | San Francisco windows; door with a hood on consoles | pendant brackets |
| Whitby | clustered / pierced / Gothic arches / pickets / stone | Gothic lancets; Gothic door | pierced bargeboards |
| Ardmore | stone loggia | Romanesque windows; studded door | corbel table |
| Merritt | stick / X / braced / slats / brick | Stick windows; crossbuck door, stick transom | open gable trusses; knee braces |
| Hollis | spindle / spindle / spindle frieze / horizontal slats / plain | Folk windows; half-glass door, diamond transom | gingerbread gables; board shutters |
| Carrow | Eastlake / sawn / fret / arches / stone | Free Classic windows with diamond uppers, Palladian attic window; Free Classic door | Tudor arch-braced gable; dentil turret cornice |

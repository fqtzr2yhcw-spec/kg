# The HO Victorian collection: plan and progress

Target: at least 10 unique, original HO (1:87.1) buildings, each designed to print well on
FDM (0.4 mm nozzle, 0.20 mm layers), with windows and doors as the standout detail
(sculpted mouldings: `hoarch/moulding.py`) and layered trim between the main parts.

Work order for each building: concept → print checks (0 interfering pairs, lint) → renders
(hero and a close-up) → commit. Export and slicing run in the background while the next
building is designed. All ten houses are done, and so is a Main Street line of ten shops
(11 to 20); a second batch of ten houses after the user's photos (21 on) is under way, each on a
bigger footprint than the first ten; the lineup render is `out/lineup/cycles/lineup.png` (built by merging each
building's render data); the shops stand side by side in two rows of five in
`out/mainstreet/cycles/`. Every building has 0 interfering part pairs.

| # | Building | Style | Status |
|---|---|---|---|
| 1 | The Beaumont | Queen Anne: octagonal tower with a hexagon-slate spire, beaded lap siding under a staggered-shingle second storey, wraparound turned porch | done: 70 parts, print files (17 h 50 m, 387 g) |
| 2 | The Ashby | Italianate villa: cream common-bond brick with quoins, paired-bracket eaves, V-groove cupola, canted bay, full-width porch on chamfered posts | done: 97 parts, print files (14 h 27 m, 370 g) |
| 3 | The Harcourt | Second Empire: Flemish-bond brick with a diaper, slate mansard with nine dormers, centre tower, sculpted windows and door, fluted portico | done: 98 parts, print files (13 h 37 m, 312 g) |
| 4 | The Fowler | Octagon house: scored stucco, two-layer eave on fan brackets, red 5V-crimp roof, octagonal cupola, Greek Revival windows, three-face veranda on Tuscan columns | done: 77 parts, print files (8 h 42 m, 207 g) |
| 5 | The Whitby | Carpenter Gothic cottage: four steep gables with pierced bargeboards, board-and-batten, patterned slate, traceried lancets under crocketed labels, crocketed gablets, diamond-paned gable lancets, Gothic entrance on engaged shafts, pointed-arch porch | done: 39 parts, print files (6 h 28 m, 131 g) |
| 6 | The Delancey | San Francisco Italianate row house: two-storey slanted bay with colonettes, rusticated front and drop-siding sides, San Francisco windows, two-layer cornice on pendant brackets, pedimented parapet, tall stoop, rusticated basement | done: 31 parts, print files (5 h 53 m, 175 g) |
| 7 | The Ardmore | Richardsonian Romanesque: rock-faced brownstone, round tower with an arcaded belvedere and conical clay-tile roof, arched corbel tables, stone entrance loggia with a great arch, voussoir windows on cushion-capital colonnettes, arcaded triple window, green clay-tile hipped roof with front gable and hip caps | done: 53 parts, print files (9 h 14 m, 201 g) |
| 8 | The Merritt | Stick style: front-gabled with a cross-gabled wing, open gable trusses (collar, king post and drop, struts, fan of sticks), stickwork framing and X-braced panels, knee-braced deep eaves, crossed-stick window casings with pent hoods on braces, braced porch with a stick frieze | done: 48 parts, print files (8 h 38 m, 177 g) |
| 9 | The Hollis | Folk Victorian farmhouse: gable-front-and-wing L-plan, Dutch lap siding with chevron-boarded gables, gingerbread gable ornaments, pedimented window crowns with fans and dentils, board shutters, spindle porch in the corner of the L, red pressed-metal shingle roof | done: 66 parts, print files (6 h 2 m, 135 g) |
| 10 | The Carrow | Queen Anne castle: Roman brick first storey, lavender half-timbered second storey, 12-sided turret rising to a dentilled cornice and a witch's-hat spire, diamond-slate hip with a front gable and Tudor truss, Free Classic windows with diamond-paned uppers, Palladian attic window, sidelighted entrance, wraparound Eastlake porch with a chamfered corner | done: 65 parts, print files (8 h 10 m, 160 g) |
| 11 | The Pemberton Block | Main Street: three-storey brick commercial block, 1868. English-bond front with rowlock arches, a soldier course and a corbel table; cast-iron storefront (fluted columns, panelled bulkheads, prism-glass transoms) with a recessed entry; gilt-lettered sign band under a dentilled store cornice; panelled frieze and pressed-metal bracketed cap (the double cornice); name-and-date tablet on the parapet | done: 30 parts, print files (6 h 56 m, 162 g) |
| 12 | Keller's Barber Shop | Main Street: one-storey false-front shop, 1891. Rustic (half-log) siding on the front, vertical boards on the sides, beaded corner boards; storefront with panelled pilasters, lozenge bulkheads and a single glazed door; striped awning with a pinked hem; sign board; frieze on jigsawn brackets under a red cap; gable date tablet; rolled-roofing gable roof with a stovepipe; plank boardwalk and barber pole | done: 21 parts, print files (1 h 58 m, 34 g) |
| 13 | The Merchants Bank | Main Street: two-storey stone corner bank, 1882. Banded rustication below and fine ashlar above a torus belt; round-arched banking-hall windows under stepped archivolts; pedimented windows upstairs; a temple doorway (pilasters, BANK entablature, segmental pediment, grille doors, ring transom) on the cut corner up granite steps; gilt-lettered frieze under a modillion-and-dentil cap mitred round the corner; bottle-baluster balustrade; glass skylight; coped chimney | done: 34 parts, print files (2 h 32 m, 67 g) |
| 14 | Hartley's General Store | Main Street: two-storey false-front store, 1879. Vertical lapped boards on stone piers with board skirting; a two-storey gallery (square posts with pierced gussets on a flagstone sidewalk, a planked balcony with a picket railing, a corrugated-iron shed roof); storefront with chamfered wooden pilasters, beaded-board bulkheads and small-paned display windows, a recessed pair of glazed doors; sign board, dogtooth frieze, cornice and an arched centre with the date; corrugated shed roof and a hooded brick flue | done: 30 parts, print files (2 h 58 m, 59 g) |
| 15 | Whitcomb's Pharmacy | Main Street: two-storey corner drugstore, 1885. Banded buff brick on a bossed stone base; the corner cut back for the entrance behind a cast-iron column, margin-light doors under an arched transom; an octagonal turret corbelled out of the corner with a copper bell roof and an onion finial; two storefronts (rosette pilasters, tiled bulkheads) under lettered sign bands; cavetto belt; shouldered lintels upstairs; panelled frieze under a cap on volute brackets; mortar-and-pestle blade sign; gravel roof, stepped chimney | done: 38 parts, print files (2 h 56 m, 61 g) |
| 16 | The Palace Hotel & Saloon | Main Street: three-storey false-front hotel, 1883. Coursed square-butt shingles on a cobble base with rolled belts; the saloon's batwing doorway and the hotel's French doors with HOTEL in the transom; a full-width balcony on five knee brackets with a wrought-iron ring railing and a planked deck; 3-over-1 windows under drip caps; a vertical HOTEL sign; PALACE HOTEL false front with a cornice and a dated crest; board-and-batten gable roof, two slab-capped chimneys | done: 53 parts, print files (3 h 55 m, 78 g) |
| 17 | Vogel's Bakery | Main Street: one-and-a-half-storey brick bakery, 1895. Monk-bond brick on a herringbone brick base; a crow-stepped front gable with stone copings on every step and a date stone; a round-arched shop window of small panes under a dog-tooth brick arch keyed with stone; a Dutch door with a heart in its transom; BAKERY sign board; gilt pretzel on a scrolled iron arm; pantile roof, tapered oven stack | done: 30 parts, print files (1 h 25 m, 27 g) |
| 18 | Bassett Hardware & Feed | Main Street: two-storey stone store, 1872. Split-face limestone on a battered base with a string course; three round-arched bays under voussoir rings (two display windows, glazed board doors under a fanlight); upstairs, windows under splayed jack arches with iron fire shutters, and a loading door under a hoist beam with pulley, rope, block and hook; lettered frieze, cornice and date panel; stepped side parapets over a shingled shed roof | done: 28 parts, print files (1 h 51 m, 47 g) |
| 19 | Madame Dufresne's Millinery | Main Street: narrow two-storey milliner's shop, 1880. A pressed-metal front (raised panels with bosses between plain stiles; its own part, printed face-up) on brick sides in Flemish garden-wall bond; a canted display bay with a hipped roof on a stone plinth; a door with a lozenge light, a scalloped transom and a crested cap up two steps; italic "Millinery" sign; ovolo belt; 6-over-1 windows under crested caps; gilt hat blade sign; lettered frieze on beaded brackets; a false mansard of octagon slates with a pedimented dormer carrying the date; flat tin roof with a glazed monitor, twin-flue chimney | done: 27 parts, print files (2 h 12 m, 46 g) |
| 20 | Ashworth & Sons, Jewelers | Main Street: narrow two-storey terra-cotta shop, 1893. Buff terra-cotta blocks with bands of button rosettes (its own part, printed face-up) on header-bond brick sides; one great round arch under a moulded terra-cotta band with imposts and a keystone carrying an "A", filled by a shop front (display window lettered WATCHES, a door with two round-headed lights, a radial fanlight); cyma belt; a canted oriel on a corbel with a copper roof between two 2-over-1 windows under triple-keyed lintels; egg-and-dart frieze lettered ASHWORTH & SONS, cornice, dated parapet panel; a four-faced street clock on a hexagon-paved sidewalk; gilt pocket-watch sign; flat copper roof in lozenge sheets, round chimney stack | done: 30 parts, print files (2 h 13 m, 43 g) |
| 21 | The Marigold | Gingerbread cottage after the user's photo: turquoise ogee-lap siding, reeded corner boards, a front gable dressed in gold lace (a pierced bargeboard of scrolls with a medallion, a lace screen, a fan hood with scroll ears over a round-headed window), a full-width porch on orange boxed posts with lace arches and railings, a scalloped fascia, a ringed skirt on coquina piers and a planked floor; cove-cut roof shingles, a fluted chimney; add-ons: a rocking chair, flower boxes, a bicycle | done: 51 parts, print files (5 h 5 m, 106 g) |
| 22 | The Primrose | Eastlake Queen Anne after the user's photo: butter double-lap siding with rope corners, a flared shingle belt, an L-plan with a wing gable carrying an Eastlake sunburst ornament and ladder brackets, a flat-topped hip with a walk rail, a porch that sweeps round the corner in three facets on bobbin posts with beaded balusters, a rosette frieze, a bead-and-reel fascia, a shingled skirt on pebble-dash piers and a pediment over the steps; notch-cut shingles, a crowned chimney; windows with square-light transoms under rosette head boards | done: 77 parts, print files (5 h 38 m, 118 g) |
| 23 | The Rosecroft | Stick-style tower house after the user's photo, 150 x 80 mm: coral rabbeted-bevel siding with notched corners on a banded stone base, a broad octagonal tower to a crown of eight pointed gablets, a teal lantern of eight tall lights over a dark core, a spire and a weathervane; two wheel gables, a two-storey canted bay; a porch round the foot of the tower on notched posts with ladder railings, a frieze of drops, a notched fascia, a sawtooth skirt on banded piers and a sunflower gablet over wide steps; rounded roof shingles, a dogtooth chimney, windows under peaked heads | done: 73 parts, print files (10 h 16 m, 250 g) |
| 24 | Laurel & Myrtle | A pair of San Francisco Italianate row houses after the user's photo, 120 x 76 mm, each with its own trim on one panelled wooden basement. The cream Laurel: narrow bevel siding, banded corner pilasters, a tablet belt, a slanted bay with Corinthian colonnettes, round-arched windows (two lights over four) in square architraves under caps on scroll consoles, a Corinthian portico with a sunburst segmental pediment over roundel doors, a cornice on paired acanthus consoles with dentils and a pediment with an oculus, a roundel chimney. The sage Myrtle: flush beaded boards, cabled pilasters, a belt of paired blocks, fluted colonnettes, segmental windows (a three-row upper sash) under cartouche hoods, a portico of fluted square piers with a pierced balustrade over bolection doors, a cornice on twin consoles under fleur-de-lis cresting, a chequer chimney. Tall stoops with panelled cheek walls and newels, iron area railings | done: 67 parts, print files (8 h 4 m, 221 g) |
| 25 | The Larkspur | Queen Anne after the user's photo: turquoise chamfered lap siding below and chisel-cut shingles above an astragal belt, reveal corners, a drafted-stone base; a gabled wing with a Free Classic pediment and fan, a round corner tower with a bell-cast slate cone and a lance finial, an arcaded loggia sunk into the upper storey, a round dormer turret, a clustered chimney; a porch curving round the tower on paired columns with twisted balusters, a ball-and-spindle frieze, a lozenge fascia and a drafted-stone skirt; 9-over-1 windows under little pent roofs; square slate | done: 77 parts, print files (11 h 16 m, 227 g) |
| 26 | The Juniper | Queen Anne after the user's photo, 125 x 117 mm overall: olive wide lap siding below and sage hexagon-cut shingles above a reeded lavender belt, rosette corner blocks, a tuckpointed brick base; a round corner tower of three storeys under a tall swallowtail-shingled cone with a fleur-de-lis finial and tongue brackets, a front gable and a side gable with lavender pendant ornaments, a gabled dormer with three lights, a lozenge chimney; an oval window in a lavender surround beside double ellipse-glazed doors with a star transom; a porch sweeping round the foot of the tower on vase-turned posts with ringed balusters, a frieze of pierced fans, a billet fascia and a vented skirt on tuckpointed piers, a gablet with a sunk arch over the steps; 6-over-1 windows (two lights across, three high) under tablet heads | done: 86 parts, print files (9 h 56 m, 196 g) |
| 27 | The Camellia | Queen Anne after the user's photo, 115 x 108 mm (132 mm deep with its forecourt): pink banded lap siding below (bevel courses tied by a flat band every sixth course) and key-cut shingles above a white belt hung with swags between rosettes, lozenge corner boards, a red-brown diamond-point base; a round tower banded in key-cut and diamond shingles under a black bell roof (flared foot, rounded shoulders, drawn to a point) with an iron spike finial and ring brackets; a pavilion with a steep front gable and a canted bay under a little hip roof, a steep east gable, both with deep keyhole-pierced gingerbread bargeboards, a collar, a lattice panel and a pendant; black wave-butt slates, a chimney with a Greek cross on each face and two pots; an entry porch on barley-twist columns with hourglass balusters, a lambrequin frieze, a cable-moulded fascia, a honeycomb brick skirt and a pediment over the steps; 8-over-1 windows under half-round keystoned hoods, a round-arched window on the porch, trefoil-light doors under a fret transom; a basket-weave brick forecourt with two cast-iron street lamps | done: 80 parts, print files (9 h 58 m, 196 g) |
| 28 | The Wisteria | Storey-and-a-half cottage combining the gingerbread cottage with the round-cornered porch, 123 x 93 mm: wisteria-lavender wide-and-narrow lap siding with blocked corner boards on a river-stone base; a steep side-gabled roof of clipped-corner shingles in moss green with a front cross-gabled wing, two hipped dormers and a tulip-crowned brick chimney; split shingles in the gable fields under crescent gable ornaments (a crescent arch with drops, a pierced diamond and a spike); a porch across the front and round the west corner in a true curve, on octagonal posts with heart-pierced railings, plum wisteria clusters hung from the frieze, an arcaded fascia and an X-braced skirt on river-stone piers; 1-over-1 windows with Y tracery under little gablets; hexagonal-light doors under a lozenge transom | print files exporting |

## Log
- Second batch, houses 21 to 28 (the Marigold, the Primrose, the Rosecroft, Laurel & Myrtle, the
  Larkspur, the Juniper, the Camellia, the Wisteria), each after one of the user's photos and on a bigger footprint. The user asked for
  the white picket fences to come off (the Marigold and the Rosecroft) and for the Rosecroft to
  be wider with a bigger cupola and a porch round its tower. New techniques: lantern and dormer
  lights as a coloured sleeve over a dark core (they read as glass); a cornice ring whose first
  0.8 mm (printed upside down) is the roof deck, so one filament change gives a dark roof; a
  loggia sunk into the upper storey (a stacked plan block) with its floor in the belt ring and an
  arcade screen printed on its back.
- Main Street shops 15 to 20: Whitcomb's Pharmacy, the Palace Hotel, Vogel's Bakery, Bassett
  Hardware, Madame Dufresne's Millinery and Ashworth & Sons. The millinery and the jeweler print
  their fronts as separate face-up parts (pressed metal, terra cotta) so the front takes its
  own colour and its relief prints on top; the oriel prints on its back; the street clock's
  four dials are separate discs with one filament change for the hands.
- Main Street: the Pemberton Block, Keller's Barber Shop, the Merchants Bank and Hartley's General
  Store (`hoarch/storefront.py`), and planked porch decks (one filament change) on the eight
  porch houses.
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
| Pemberton | English-bond front with rowlock arches, soldier course, end piers and a corbel table; running-bond party walls | granite plinth | sill course | flat deck with seams, parapet coping | party-wall stack with square pots | none (name tablet) |
| Keller's | rustic (half-log) lap front, vertical beadboard sides and rear | timber sill with bolt heads | none (one storey) | rolled roofing, ridge roll | stovepipe | none (date tablet) |
| Merchants Bank | banded rustication below, fine ashlar above | polished granite | torus | flat deck with a hipped glass skylight | coped ashlar stack with bell pots | none (balustrade) |
| Hartley's | vertical lapped boards | stone piers with board skirting | fascia | corrugated iron (shed roof, gallery roof) | hooded brick flue | none (arched false front) |
| Whitcomb's | banded buff brick (running bond with open channel courses) | bossed stone | cavetto | gravel | stepped | onion (turret) |
| Palace | coursed square-butt shingles | cobble | roll | board and batten | slab-capped pair | none (dated crest) |
| Vogel's | monk-bond brick, dog-tooth arch | herringbone brick | none (one and a half storeys) | pantiles | tapered oven stack | none (crow steps) |
| Bassett | split-face limestone, voussoir and jack arches | battered | string | shingled shed roof | none | none (date panel) |
| Dufresne | pressed-metal front, Flemish garden-wall bond sides | moulded stone | ovolo | flat tin in flat-lock sheets with a glazed monitor; false mansard of octagon slates | twin flue | none (dated dormer) |
| Ashworth | terra cotta with rosette bands and a moulded arch band, header-bond sides | tooled granite | cyma | flat copper in lozenge sheets; copper oriel roof | round stack with iron bands | none (street clock) |
| Marigold | ogee lap siding | coquina | none (one storey and a gable) | cove-cut shingles | fluted | none (lace bargeboard medallion) |
| Primrose | double lap siding, saw-cut shingles in the gable | pebble-dash | flared shingle skirt | notch-cut shingles | crowned | none (walk rail) |
| Rosecroft | rabbeted bevel siding | banded stone | two stepped fascias (fillet) | rounded shingles | dogtooth | vane with a weathervane arrow |
| Laurel | narrow bevel siding | panelled wooden basement (shared) | tablet | flat deck (dark by a filament change) | roundel | none (pediment with an oculus) |
| Myrtle | flush beaded boards | panelled wooden basement (shared) | paired blocks | flat deck (dark by a filament change) | chequer | none (fleur-de-lis cresting) |
| Larkspur | chamfered lap siding, chisel-cut shingles above | drafted stone | astragal | square slate (tower and dormer too) | clustered flues | lance |
| Juniper | wide lap siding, hexagon-cut shingles above | tuckpointed brick | reeded | swallowtail shingles (tower cone too) | lozenge | fleur-de-lis |
| Camellia | banded lap siding, key-cut shingles above (key-cut and diamond bands on the tower) | diamond-point rustication | swags between rosettes | wave-butt slates (bell roof too) | Greek cross panels, two pots | spike |
| Wisteria | wide-and-narrow lap siding, split shingles in the gables | river stones | none (a storey and a half) | clipped-corner shingles (dormers too) | tulip crown | none (spikes on the gables) |

| Building | Porch: post / railing / frieze / skirt / piers; roof edge | Windows and door | Gable, shutters, brackets |
|---|---|---|---|
| Beaumont | turned / turned / sawn / lattice / fieldstone; dentil roof edge | Queen Anne windows; swan-neck door, arched leaves | shingled gables; no shutters; curve brackets |
| Ashby | chamfered / vase / scroll / panels / limestone; modillion roof edge | Italianate arched 2-over-2; paired door | panel shutters; scroll brackets |
| Harcourt | fluted / urn / entablature / square / granite; filleted roof edge | Second Empire windows; door with arched-panel leaves, plain transom | block brackets |
| Fowler | Tuscan / Chippendale / valance / pierced diamonds / brick; cove roof edge | Greek Revival 6-over-6 with cornice heads; door with sidelights | louvered shutters; fan brackets |
| Delancey | stoop only | San Francisco windows; door with a hood on consoles | pendant brackets |
| Whitby | clustered / pierced / Gothic arches / pickets / rubble; Gothic drops on the roof edge | Gothic lancets; Gothic door | pierced bargeboards |
| Ardmore | stone loggia | Romanesque windows; studded door | corbel table |
| Merritt | stick / X / braced / slats / parged; stick battens on the roof edge | Stick windows; crossbuck door, stick transom | open gable trusses; knee braces |
| Hollis | spindle / spindle / spindle frieze / horizontal slats / block; button roof edge | Folk windows; half-glass door, diamond transom | gingerbread gables; board shutters |
| Carrow | Eastlake / sawn / fret / arches / coursed stone; reeded roof edge | Free Classic windows with diamond uppers, Palladian attic window; Free Classic door | Tudor arch-braced gable; dentil turret cornice |
| Pemberton | cast-iron storefront: fluted columns, panelled bulkheads, prism transoms; recessed entry with a pair of half-glazed doors | segmental 2-over-2 under rowlock arches, 1-over-1 under stone lintels; street door with four-panel leaf and a numbered transom; rear 1-over-1 | pressed-metal brackets and tails; dentilled caps |
| Keller's | storefront with panelled pilasters, lozenge bulkheads, wide transom lights; shallow entry with a single glazed door; striped awning; boardwalk | 4-over-4 under flat iron hoods; store door (big light, push bar, kick plate) with a stick transom | jigsawn brackets on the frieze |
| Merchants Bank | corner entrance up granite steps | round-arched 1-over-1 (two-row lower sash) under archivolts; 1-over-1 (two-row sashes) under pediments; temple doorway, grille leaves, ring transom | scrolled modillions and dentils |
| Hartley's | two-storey gallery: square posts with pierced gussets, picket railing, planked balcony, flagstone sidewalk | 3-over-3 and 2-over-2 segmental sashes; six-light doors with cross transoms; storefront with chamfered pilasters, beaded-board bulkheads, small-paned display windows, a pair of glazed doors | dogtooth frieze |
| Whitcomb's | corner entrance behind a cast-iron column; two storefronts with rosette pilasters, tiled bulkheads and big lights | 1-over-1 under shouldered lintels, segmental 1-over-1 at the rear; margin-light doors with arched transoms | volute brackets |
| Palace | full-width balcony on knee brackets with a wrought-iron ring railing; saloon batwing doors | 3-over-1 under drip caps; French doors with HOTEL transoms | knee brackets |
| Vogel's | none | round-arched shop window of small panes, segmental 2-over-2, small gable windows; Dutch doors with heart transoms | none (crow-stepped gable) |
| Bassett | three round-arched bays: display windows and glazed board doors under a fanlight | 1-over-1 (two-row sashes) under jack arches; ledged loading and freight doors | iron fire shutters; a loading hoist |
| Dufresne | canted display bay with a hipped roof on a stone plinth | 6-over-1 under crested caps; door with a lozenge light, scalloped transom and crested cap | beaded brackets |
| Ashworth | arched shop front (display window lettered WATCHES, radial fanlight); canted oriel on a corbel | 2-over-1 under lintels with triple keystones; doors with twin round-headed lights | none (egg-and-dart frieze) |
| Marigold | boxed / lace / lace arches / rings / coquina; scallop roof edge | round-headed windows under halo mouldings; lace-grilled door under a fan hood | lace bargeboard, lace screen and fan hood; no shutters |
| Primrose | bobbin / beaded / rosette / shingles / pebble; bead-and-reel roof edge | 1-over-1 with square-light transoms under rosette head boards; sunray doors, beaded transoms | Eastlake sunburst gable; ladder brackets |
| Rosecroft | notched / ladder / drops / sawtooth / banded; notched roof edge | 1-over-1 (two-row lower sash) under peaked heads; keyhole double doors, chevron transom | wheel gables; fret brackets |
| Laurel | Corinthian portico; stoop with panelled cheeks and ball newels | round-arched, two lights over four, under caps on scroll consoles; roundel doors, grid transom | acanthus consoles with dentils |
| Myrtle | fluted-pier portico with a pierced balustrade; stoop with pyramid newels | segmental, a three-row upper sash over a plain lower one, under cartouche hoods; bolection doors, quatrefoil transom | twin consoles |
| Larkspur | paired / twist / beads / stone / drafted; lozenge roof edge | 9-over-1 under pent roofs on brackets; cameo doors, wave transom | Free Classic pediment with a fan; cove brackets |
| Juniper | vase / ringed / fans / vents / tuckpoint; billet roof edge | 6-over-1 (two across, three high) under tablet heads, an oval window in a lavender surround; ellipse-glazed doors, star transom | pendant gable ornaments; tongue brackets |
| Camellia | barley twist / hourglass / lambrequin / honeycomb brick / diamond-point; cable roof edge | 8-over-1 (plain lights in the tower) under half-round keystoned hoods, a round-arched window; trefoil doors, fret transom | keyhole bargeboards with a lattice panel; ring brackets |
| Wisteria | octagon / hearts / wisteria clusters / X-braced panels / river stone; arcaded roof edge | 1-over-1 with Y tracery under gablets; hexagonal-light doors, lozenge transom | crescent gables; no brackets |


| Building | Corners | Other trim of its own |
|---|---|---|
| Beaumont | plain corner boards with caps | pointed-arch iron cresting on the ridge and bay, corbelled chimneys with round pots |
| Ashby | long-and-short quoins; sunk-panel boards on the cupola | twin round-arched windows (front and cupola), porch tin ribbed one way |
| Harcourt | equal-block quoins in tight courses | spear-and-ball cresting, flat-seam portico tin (battens both ways), crowned pots |
| Fowler | beads on the octagon's obtuse corners | pierced fan brackets on the frieze course and cupola |
| Delancey | fluted pilasters with base blocks | colonettes on the bay corners, pedimented parapet |
| Whitby | mitred posts with a chamfered corner | pierced bargeboards with spike finials |
| Ardmore | none (rock-faced stone) | arched corbel table, cushion capitals |
| Merritt | stepped double boards | stickwork, knee braces, tall chimney pots |
| Hollis | capped boards on plinths | gingerbread with spindle screens |
| Carrow | none (brick and half-timber) | octagonal chimney pots, Tudor truss |
| Pemberton | none (end piers in the brick) | brick posts with V fronts behind the storefront columns, gilt sign letters by one filament change |
| Keller's | beaded boards, full height on the false front | awning stripes by height, barber pole with helical ridges, plank boardwalk |
| Merchants Bank | none (a cut corner) | bottle-baluster balustrade mitred round the corner, gilt frieze letters by one filament change |
| Hartley's | none | arched false-front centre with the date, balcony deck planks by one filament change |
| Whitcomb's | none (a cut corner under the turret) | octagonal turret with a bell roof, mortar-and-pestle blade sign |
| Palace | none | vertical HOTEL sign, balcony deck planks by one filament change |
| Vogel's | none | stone copings on every crow step, gilt pretzel blade sign |
| Bassett | none | hoist beam with pulley, rope, block and hook; stepped side parapets |
| Dufresne | plain pressed-metal stiles | italic sign, gilt hat blade sign, glazed roof monitor |
| Ashworth | none | four-faced street clock with separate dials, gilt pocket-watch sign, hexagon-paved sidewalk |
| Marigold | reeded boards | flower boxes, rocking chair, bicycle |
| Primrose | rope boards | a porch sweeping round its corner in facets; walk rail on a flat hip top |
| Rosecroft | notched boards | a crown of gablets, a lantern of dark-glazed lights, a weathervane |
| Laurel | banded pilasters | Corinthian colonnettes on the bay |
| Myrtle | cabled pilasters | fluted colonnettes on the bay, iron area railings |
| Larkspur | reveal boards | an arcaded loggia, a round dormer turret, a bell-cast tower cone |
| Juniper | rosette blocks | an oval window, a three-light dormer, a porch round a round tower |
| Camellia | lozenge boards | a bell-roofed tower, a canted bay, a basket-weave forecourt with street lamps |
| Wisteria | blocked boards | two hipped dormers, a porch curving round the corner |

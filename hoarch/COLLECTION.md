# The HO Victorian collection: plan and progress

Target: at least 10 unique, original HO (1:87.1) buildings, each designed to print well on
FDM (0.4 mm nozzle, 0.20 mm layers), with windows and doors as the standout detail
(sculpted mouldings: `hoarch/moulding.py`) and layered trim between the main parts.

Work order for each building: concept → print checks (0 interfering pairs, lint) → renders
(hero and a close-up) → commit. Export and slicing run in the background while the next
building is designed. Twenty houses are done (1 to 10, and a second batch of ten after the
user's photos, 21 to 30), and so is a Main Street line of ten shops (11 to 20). All twenty
houses are on the house-size standard (each fills most of a 256 mm bed) with a built-up
cornice at every level (the table under "Cornices per building"); the shops keep their
original size. The lineup render is `out/lineup/cycles/lineup.png` (built by merging each
building's render data); the shops stand side by side in two rows of five in
`out/mainstreet/cycles/`. Every building has 0 interfering part pairs, and
`python3 -m hoarch.audit` checks the houses against the owner's measurable rules (`CLAUDE.md`).

| # | Building | Style | Status |
|---|---|---|---|
| 1 | The Beaumont | Queen Anne, 150 x 180 mm (Rev D): an octagonal corner tower rising a storey over the eave to a hexagon-slate spire, a front gable wing with a sunburst over a collar and a one-storey canted bay, a gabled dormer on the west slope, sage beaded lap siding under gold staggered shingles, a ridge crest with urn finials, a wraparound turned porch; cornices of pendants (joint), ribbed shells on paired curved brackets (eave, carried round the tower), hearts (tower) and pendants (bay) | done: 79 parts, print files (26 h 23 m, 629 g; 3 plates with one filament change) |
| 2 | The Ashby | Italianate villa, 180 x 156 mm plus a kitchen ell (Rev C): cream common-bond brick with stone quoins, a canted bay, a low standing-seam hip with a V-groove cupola, a full-width porch on chamfered posts, panel shutters; cornices of green coffers (joint), a green vine scroll on paired scroll brackets (eave), pearls (ell) and oculi (cupola) | done: 117 parts, print files (22 h 49 m, 619 g; 5 plates with one filament change) |
| 3 | The Harcourt | Second Empire, 186 x 150 mm (Rev B): Flemish-bond brick with a diaper, a bell-cast slate mansard with nine dormers and iron cresting, a centre tower under a concave cap, sculpted windows, a fluted portico, an east bay with a crested deck; cornices of acanthus leaves (joint), verdigris anthemion on block modillions (eave, round the tower), bosses (tower) and anthemion (bay) | done: 104 parts, print files (20 h 30 m, 511 g; 5 plates with one filament change) |
| 4 | The Fowler | Octagon house, 152 mm across the flats (Rev B): scored stucco, a red 5V-crimp roof, an octagonal cupola, Greek Revival windows with louvered shutters, a veranda on three faces on Tuscan columns; cornices of green bead wreaths (joint), spoked paterae on paired fan brackets (eave) and sunk lunettes (cupola) | done: 80 parts, print files (14 h 33 m, 379 g; 3 plates with one filament change) |
| 5 | The Whitby | Carpenter Gothic cottage, 168 x 100 mm (Rev B): board and batten, a steep patterned-slate roof with four gables hung with pierced bargeboards, traceried lancets, a Gothic entrance and porch; cornices of a claret pointed arcade (joint) and trefoils in roundels (eave, stopping at the cross gables) | done: 45 parts, print files (14 h 28 m, 325 g; 1 plates with one filament change) |
| 6 | The Delancey | San Francisco Italianate row house, 104 x 150 mm (Rev B): a two-storey slanted bay with colonettes, channel-rusticated front and drop-siding sides, a tall stoop, a flat deck behind a pedimented parapet; cornices of navy incised lines (joint) and navy cartouches on paired pendant brackets (eave) | done: 34 parts, print files (8 h 59 m, 300 g; 3 plates with one filament change) |
| 7 | The Ardmore | Richardsonian Romanesque, 176 x 116 mm (Rev B): rock-faced brownstone, a round tower with an arcaded belvedere and a conical clay-tile roof, a stone entrance loggia with a great arch, voussoir windows on cushion capitals; cornices of interlaced arches (joint), a corbel table of little arches (eave, round the tower) and terracotta nailheads (tower) | done: 56 parts, print files (18 h 11 m, 436 g; 3 plates with one filament change) |
| 8 | The Merritt | Stick style, 170 x 140 mm (Rev B): a front-gabled block with a cross-gabled wing, open gable trusses, stickwork framing with X-braced panels, a braced porch; cornices of oxide-red stick frames (joint) and X-braced panels on diagonal knee braces (eave) | done: 52 parts, print files (19 h 4 m, 453 g; 2 plates with one filament change) |
| 9 | The Hollis | Folk Victorian farmhouse, an L 176 x 136 mm (Rev B): Dutch lap siding with chevron boarding in the gables, gingerbread gables, pedimented window crowns, board shutters, a spindle porch in the corner of the L; cornices of a green chain of diamonds (joint) and sawn teeth on knee brackets (eave) | done: 88 parts, print files (15 h 51 m, 431 g; 3 plates with one filament change) |
| 10 | The Carrow | Queen Anne castle, 168 x 132 mm (Rev B): Roman brick under a half-timbered storey, a round turret to a witch's-hat spire, a front gable with an arch-braced Tudor truss over a Palladian window, a wraparound Eastlake porch; cornices of plum strapwork (joint), Tudor roses on modillions (eave, round the turret) and a crenellated frieze on volutes (turret) | done: 64 parts, print files (21 h 4 m, 497 g; 4 plates with one filament change) |
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
| 21 | The Marigold | Gingerbread cottage after the user's photo, 124 x 172 mm (Rev B): turquoise ogee lap, a front gable dressed in gold lace (bargeboard, screen, fan hood), a full-width lace porch on orange posts, cove-cut shingles, flower boxes and a rocking chair; an eave cornice of gold linked rings on jigsawn brackets | done: 52 parts, print files (14 h 21 m, 342 g; 2 plates with one filament change) |
| 22 | The Primrose | Eastlake Queen Anne after the user's photo, 176 x 148 mm (Rev B): butter double lap, a flat-topped hip with a walk rail, a front wing with an Eastlake sunburst gable, a porch sweeping round its corner on bobbin posts; cornices of spindles (joint) and a burgundy guilloche on beaded brackets (eave) | done: 89 parts, print files (11 h 47 m, 350 g; 3 plates with one filament change) |
| 23 | The Rosecroft | Stick-style tower house after the user's photo, 210 x 124 mm (Rev C): coral rabbeted bevel, a broad octagonal tower to a crown of eight gablets with framed lancets and roundels, a teal lantern and a spire with a vane, two wheel gables, a canted bay, a porch round the tower; cornices of a teal Greek key (joint), triglyphs on fret brackets (eave) and a diaper frieze (tower) | done: 78 parts, print files (21 h 10 m, 553 g; 3 plates with one filament change) |
| 24 | Laurel & Myrtle | A pair of San Francisco Italianate row houses after the user's photo, 192 x 136 mm (Rev B), each with its own trim on one panelled basement: slanted bays with colonnettes, porticoes, tall stoops, bracketed cornices with a pediment (Laurel) or fleur-de-lis cresting (Myrtle), iron area railings; each house's own joint cornice and eave frieze | done: 77 parts, print files (15 h 7 m, 485 g; 4 plates with one filament change) |
| 25 | The Larkspur | Queen Anne after the user's photo, 196 x 136 mm (Rev B): turquoise chamfered lap under chisel-cut shingles, a gabled wing with a Free Classic pediment and fan, a round tower to a bell-cast cone, an arcaded loggia in the upper storey, a gabled dormer, a porch curving round the tower; cornices of a navy running wave (joint), rosettes on cove brackets (eave) and scrolls (tower) | done: 79 parts, print files (27 h 38 m, 657 g; 3 plates with one filament change) |
| 26 | The Juniper | Queen Anne after the user's photo, 196 x 140 mm (Rev B): olive lap under sage hexagon shingles, a round corner tower to a swallowtail cone, pendant gables, a three-light dormer, an oval window, a porch round the tower on vase posts; cornices of lavender fans (joint), lattice on tongue brackets (eave) and stars (tower) | done: 84 parts, print files (26 h 2 m, 594 g; 3 plates with one filament change) |
| 27 | The Camellia | Queen Anne after the user's photo, 200 x 132 mm (Rev B): pink banded lap under key-cut shingles, a round tower under a black bell roof, a pavilion with a steep gable and a canted bay, keyhole bargeboards, a barley-twist porch, a basket-weave forecourt with two street lamps; cornices of raspberry swags (joint), ovals on ring brackets (eave), flutes (tower) and studs (bay) | done: 80 parts, print files (25 h 44 m, 586 g; 3 plates with one filament change) |
| 28 | The Wisteria | Storey-and-a-half cottage, 200 x 104 mm (Rev B): lavender wide-and-narrow lap, a steep side-gabled roof with a front wing and two hipped dormers, crescent gable ornaments, a porch curving round the corner on octagonal posts with wisteria clusters; an eave cornice of plum quatrefoils on comma brackets | done: 47 parts, print files (17 h 26 m, 414 g; 2 plates with one filament change) |
| 29 | The Hawthorn | Eastlake house with a square tower, 190 x 136 mm (Rev B): oxblood cove-and-bead siding, a star gable, a tower rising a storey over the eave to a pyramid with a pineapple finial, a porch on tapered posts; cornices of a mustard zigzag (joint), sunflowers on ladder brackets (eave) and chevrons (tower) | done: 58 parts, print files (19 h 17 m, 502 g; 3 plates with one filament change) |
| 30 | The Magnolia | Twin-gabled house with an entry loggia, 208 x 128 mm (Rev B): English cross bond brick below and step-cut shingles above, two front gables with arcade ornaments, a loggia sunk into the ground storey behind three segmental arches; cornices of ivory little arches (joint) and chocolate lozenges on stepped brackets (eave) | done: 48 parts, print files (20 h 24 m, 447 g; 3 plates with one filament change) |
| 31 | The Whitmore | Georgian Colonial (photo 4): red brick, a centre pavilion under a pediment with an oculus, a Palladian window with a balcony over a columned entry portico, copper-roofed bay windows either side, a slate hip roof with three dormers, a modillion cornice, tall end chimneys | planned |
| 32 | The Pennock | Pennsylvania fieldstone Colonial (photo 2), 196 x 144 mm: roughly coursed fieldstone with drafted quoins on a ledgestone foundation, flat-bottomed rubble arches over every window, nine-over-six sash under drip caps below and six-over-six in eared frames above, oxblood two-panel shutters on strap hinges; a pent roof of riven shakes across the front and pent eaves across both gables; cornices of compass stars, wolf's teeth and a torus (joint), gadroons, dentils and a deep cove (eave), whirling rosettes (the ell); a strap-hinged double door under a pedimented hood on scrolled consoles, a stone stoop with a settle either side; a riven-shake side-gabled roof with two arched tin-roofed dormers, fieldstone end stacks under stone hoods, a J P 1768 datestone in the west gable, and a one-storey kitchen ell behind | renders for review |
| 33 | The Oakhurst | Southern Colonial (photo 3), 232 x 104 mm: buttermilk brick in American bond with Flemish header courses on a raised red-brick basement with arched vents; a giant portico of four fluted Greek Doric columns on a planked floor up broad steps, an architrave of two fasciae, a pediment with a fanned lunette, a coffered haint-blue ceiling; a Greek Revival entrance (paired panelled leaves, sidelights and transom leaded in lozenges) and a French door onto a balcony railed in wrought-iron scrolls; six-over-nine windows under pedimented lintels below, six-over-six under tabled lintels above, plantation shutters; cornices of pineapples (joint), magnolia blossoms (eave and portico) and lotus and bud (the wing); a keyed-slate hip roof, segmental-pediment dormers on the ends, acroterion-capped stacks, a louvered cupola under a ribbed copper dome; an east wing with a roof terrace behind a sawn balustrade | renders for review |
| 34 | The Van Tassel | Dutch Colonial, 190 x 96 mm and a 24 mm porch: a storey and a half of red Jersey sandstone (coursed ashlar, each block's face tooled in furrows) on field boulders under a sandstone sill; a gambrel roof of chisel-cut shakes banded with swallowtails, its front slope sweeping out in a Dutch kick over a porch the width of the house on six round posts; double-coursed white shingles in the gambrel ends with quarter-round lights either side of the flue; a Dutch door with bull's-eye lights and ogee 'bell' head boards over the windows, Delft-blue board-and-batten shutters cut with crescent moons; a Delft-tile frieze at the eave; a long shed dormer behind; stacks of sandstone below and brick above | renders for review |
| 35 | The Hathaway | New England saltbox, 168 x 132 mm: two storeys in front and one behind under a long catslide roof; Spanish-brown graduated clapboard (narrow courses at each storey's foot, widening upward, a bead on every butt) on split granite still showing its drill holes; nine-over-nine windows under drip boards below and tight under the eave above; a six-panel door between fluted pilasters under a broken swan-neck pediment with an urn finial; cornices of chain links (the joint, running on round the lean-to's eave) and trees of life (the front eave); a massive centre chimney with corner piers and four pots; shakes banded bevel and square | renders for review |
| 36 | The Chatham | Cape Cod, 194 x 84 mm with its wing: a storey and a half under a steep side-gabled roof; weathered silver shingles (every fifth course diamond-pointed) on a tabby foundation studded with shell; a cross-and-bible door under a five-light transom between lozenge-sunk pilasters and a dentilled cap, a millstone for its step; six-over-six windows under little shed hoods on knee brackets, navy board shutters cut with pine trees; an eave frieze of fouled anchors over a rope course; three shingle-cheeked dormers with drops; a centre chimney with a soldier band and three flues; a lower east wing with a frieze of sailor's knots | renders for review |
| 37 | The Winthrop | Garrison Colonial: a brick first storey under a clapboard second storey that overhangs it on carved pineapple drops, a side-gabled roof, end chimneys | planned |
| 38 | The Westbrook | Colonial front, Victorian flair (photo 1): white clapboard and black shutters, a curved two-storey porch on round columns with a balustraded balcony on top, arched-window dormers on a slate hip roof, a side wing | planned |
| 39 | (mixed 2) | Colonial front, Victorian flair: a symmetrical Colonial front with a Victorian corner tower and a wraparound porch | planned |
| 40 | (mixed 3) | Colonial front, Victorian flair: a symmetrical Colonial front with two-storey canted bays, a Palladian gable and a turned-post veranda | planned |

## Log
- Third batch planned (31 to 40): seven straight Colonial houses, each a different Colonial
  type, and three that mix a Colonial front with Victorian flair (the user's direction, with
  five photos). The Whitmore (Georgian) and the Westbrook (mixed) are the pilots: renders go
  to the user before the rest are built. New library parts needed: Colonial window and door
  families (small-paned sashes, keystone lintels, fanlights and sidelights, pedimented and
  hooded doorways, Palladian windows), gambrel, saltbox and pent roofs, a second-storey
  overhang with drops, a giant-order portico, a curved two-storey porch with a balcony.
- House-size standard and built-up cornices, on all twenty houses (the user: the Ashby's floors
  were 35-40% smaller than the pink reference house; a cornice between every level, in several
  parts and colours, never the same design twice; two colours in a part is fine if it is one
  filament change). The Camellia, the Ashby and the Marigold were the pilots; the user
  test-printed them before the rest followed.
  - Every house fills most of the P1S/P2S bed: long side 150 to 210 mm. Most two-storey
    houses have a 42 mm first storey, a joint band and a 38 mm second storey (the San
    Francisco row houses 46 and 42 mm; the Whitby's upper storey is a knee wall). Windows (about 9.6 x 24 mm below, 21 mm above) never
    fill a storey's height or a wall's width, and every sash has its own frame lining.
  - A cornice at every level: each storey joint, each eave, and the tower, turret, bay,
    cupola and ell tops. Each is a frieze, a course, a bracketed bed and a crown, and no two
    levels in the collection are alike (the table below; 25 new frieze patterns).
  - Each level prints as at most two parts with at most one filament change each: `-lower`
    (frieze and course, upright) and `-upper` (bed and crown, upside down, the bed carried on
    a 45 degree cove under the crown). A two-colour part has a plate of its own named for its
    change, e.g. `07_Raspberry_then_White_at_3.0mm`.
  - Rings that wrap a tower are parted so no piece wraps more than half of it, and each fits
    on from the side.
  - The user's fixes: fewer, framed windows in the Rosecroft's crown; a gabled dormer and an
    uncovered gable window on the Larkspur; fewer tower windows and an uncovered gable window
    on the Camellia; no bicycle on the Marigold; fewer porch posts on the Wisteria.
  - Optional dark glass: the first 0.4 mm of every window is its glass, so one filament change
    on the Windows_Doors plate gives dark glass in coloured frames.
  - Every house's renders include a rear view.
- Second batch, houses 21 to 30 (the Marigold, the Primrose, the Rosecroft, Laurel & Myrtle, the
  Larkspur, the Juniper, the Camellia, the Wisteria, the Hawthorn, the Magnolia). Houses 21 to 27
  follow the user's seven photos; 28 to 30 combine their features (a cottage with the curved
  porch, a smaller tower house, twin gables with a loggia). All are on a bigger footprint. The
  user asked for the white picket fences to come off (the Marigold and the Rosecroft) and for
  the Rosecroft to be wider with a bigger cupola and a porch round its tower. New techniques:
  - lantern and dormer lights as a coloured sleeve over a dark core (they read as glass);
  - a cornice ring whose first 0.8 mm (printed upside down) is the roof deck, so one filament
    change gives a dark roof;
  - a loggia sunk into a storey (a notched plan block), with its floor or ceiling in the belt
    ring and an arcade screen printed on its back;
  - a bell (ogee) roof as a stack of conical bands with their own slopes (`roof.bell_roof`);
  - belt reliefs (swags, zigzags) that step back 0.2 mm per layer underneath, so the belt
    ring still prints upright;
  - flat-bottomed dormers that drop into pockets shaped to them and sit on seat blocks standing
    on the bed inside the hollow roof;
  - a gable ridge that runs above the main hip ends in a hip of its own;
  - add-ons: a basket-weave brick forecourt and cast-iron street lamps (standard, glass and cap
    as three parts).
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

## Cornices per building

Every level of every house has its own built-up cornice (`hoarch/cornice.py`; the method is in
`NOTES.md` under "Built-up cornices"). Each row is one level: the frieze and the
course print together upright as the level's `-lower` part, the bracketed bed and the crown
together upside down as its `-upper` part (a level with only one of a pair keeps that ring's
name, `-frieze` or `-crown`). No level, frieze pattern or bracket style appears on two
buildings. The colours are the filament colours on each house's plates.

| Building | Level | Frieze | Course | Bed (brackets) | Crown |
|---|---|---|---|---|---|
| Beaumont | storey joint | pendants, oxblood | bead and reel, cream | - | ogee, cream |
|  | eave | shells, oxblood | dentil, cream | curve, cream | cyma reversa, oxblood |
|  | bay | pendants, gold | - | curve, cream | bevel, cream |
|  | tower top | hearts, oxblood | - | curve, cream | stepped, cream |
| Ashby | storey joint | coffers, forest | egg and dart, white | - | torus, white |
|  | eave | rinceau (vine scroll), forest | dentil, white | scroll, white | cyma recta, forest |
|  | kitchen ell | pearls, forest | billet, white | - | cavetto, white |
|  | cupola | oculi, white | - | scroll, forest | ovolo, white |
| Harcourt | storey joint | acanthus, limestone | cable, verdigris | - | cyma recta, limestone |
|  | eave | anthemion, verdigris | dentil, limestone | block, limestone | cavetto, verdigris |
|  | bay | anthemion, limestone | - | block, verdigris | stepped, limestone |
|  | tower top | bosses, limestone | - | block, verdigris | ovolo, limestone |
| Fowler | storey joint | wreaths, forest | pellets, white | - | ovolo, white |
|  | eave | paterae, forest | dentil, white | fan, white | torus, white |
|  | cupola | lunettes, white | - | fan, forest | bevel, white |
| Whitby | storey joint | pointed arcade, claret | dog-tooth, cream | - | bevel, cream |
|  | eave | trefoils, claret | billet, cream | - | cavetto, cream |
| Delancey | storey joint | incised lines, navy | scallop, cream | - | cyma reversa, cream |
|  | eave | cartouches, navy | dentil, cream | pendant, cream | ogee, navy |
| Ardmore | storey joint | interlace, buff | billet, terracotta | - | bevel, buff |
|  | eave | corbel arches, buff | dog-tooth, terracotta | - | stepped, buff |
|  | tower top | nailhead, terracotta | bead and reel, buff | - | ovolo, buff |
| Merritt | storey joint | stick frames, oxide | blocks, cream | - | cavetto, cream |
|  | eave | X-braced panels, oxide | cable, cream | brace, cream | bevel, cream |
| Hollis | storey joint | diamonds, forest | drops, white | - | ovolo, white |
|  | eave | teeth, forest | reeds, white | knee, white | cavetto, forest |
| Carrow | storey joint | strapwork, plum | egg and dart, cream | - | cyma reversa, cream |
|  | eave | Tudor roses, plum | dentil, cream | modillion, cream | cyma recta, plum |
|  | turret top | crenellation, cream | - | volute, plum | ovolo, cream |
| Marigold | eave | circles, gold | bead and reel, orange | sawn, gold | ogee, orange |
| Primrose | storey joint | spindles, olive | rope, burgundy | - | cavetto, olive |
|  | eave | guilloche, burgundy | dog-tooth, olive | beaded, olive | ovolo, burgundy |
| Rosecroft | storey joint | fret, teal | cable, cream | - | bevel, teal |
|  | eave | triglyphs, teal | dentil, cream | fret, teal | cyma recta, teal |
|  | tower top | diaper, teal | - | fret, cream | ogee, teal |
| Laurel & Myrtle | joint (Laurel) | panels, gold | egg and dart, cream | - | ogee, gold |
|  | joint (Myrtle) | keys, forest | cable, sage | - | stepped, forest |
|  | eave frieze (Laurel) | medallions, gold | dentil, cream | - | - |
|  | eave frieze (Myrtle) | tulips, forest | pellets, sage | - | - |
| Larkspur | storey joint | wave, navy | scallop, cream | - | cyma reversa, cream |
|  | eave | rosettes, navy | dentil, cream | cove, cream | cavetto, navy |
|  | tower top | scrolls, navy | - | cove, cream | stepped, cream |
| Juniper | storey joint | fans, lavender | pellets, cream | - | ovolo, lavender |
|  | eave | lattice, lavender | dentil, cream | tongue, cream | cyma recta, lavender |
|  | tower top | stars, lavender | - | tongue, cream | bevel, cream |
| Camellia | storey joint | swags, raspberry | pellets, white | - | cyma recta, white |
|  | eave | ovals, raspberry | dentil, white | ring, white | cavetto, raspberry |
|  | bay | studs, raspberry | - | ring, white | bevel, white |
|  | tower top | flutes, raspberry | - | ring, white | ovolo, white |
| Wisteria | eave | quatrefoil, plum | drops, cream | comma, cream | cyma reversa, plum |
| Hawthorn | storey joint | zigzag, mustard | billet, forest | - | stepped, mustard |
|  | eave | sunflower, mustard | reeds, forest | ladder, mustard | torus, forest |
|  | tower top | chevron, forest | - | ladder, mustard | cyma recta, mustard |
| Magnolia | storey joint | arcade, ivory | blocks, chocolate | - | ovolo, ivory |
|  | eave | lozenges, chocolate | egg and dart, ivory | stepped, ivory | cyma recta, chocolate |

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
| Hawthorn | cove-and-bead siding, spade-cut slates in the gable | stacked ledge stones | zigzag | spade-cut slates (tower too) | octagonal shaft, corbelled crown | pineapple |
| Magnolia | English cross bond brick below, step-cut shingles above and in the gables | V-jointed ashlar | brick corbel table with dentils | arch-cut shingles | pilastered | none (spikes on the gables) |

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
| Hawthorn | tapered / paddle / Tudor arches / chevron boards / ledge stone; sawtooth roof edge | 1-over-1 with a fan in the upper sash under incised sunflower heads; shoulder-headed doors, bow-tie transom | star gable; comma brackets |
| Magnolia | an entry loggia: segmental arches on square piers with imposts and keystones; steps | 1-over-1 with a cross in the upper sash under lambrequin heads; wheel-light doors, arched-bar transom | arcade gables; no brackets |


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
| Hawthorn | incised boards | a square tower with a pyramid roof |
| Magnolia | dentilled boards | a loggia sunk into the ground storey between twin gables |

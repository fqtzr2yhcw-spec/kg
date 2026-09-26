# hoarch — construction notes for HO-scale printed buildings

These are the construction standards behind `hoarch`. They come from taking apart a
well-made commercial HO Victorian kit and rebuilding its part types in code. That rebuild
is a private study, kept out of this repository because the kit's license forbids sharing
derivatives. The library and these notes hold only general techniques; no geometry from
that kit is in the repo.

## How a detailed kit is split into parts

| Part family | How it is made | Print orientation |
|---|---|---|
| Wall shell | **One piece per storey**: the whole first floor (with one-storey wings), then the whole second floor; 3.0 mm walls, plain openings | Upright |
| Belt ring | The string course between the storey shells, full wall thickness plus the moulding; it is the joint | Upright |
| Foundation | Ring the shape of the plan, stone faces, locating lip for the shell | Upright |
| Window / door | **One part:** a plug with the glass and sash that fits the opening, and the surround with casing, sill, hood and crest | Face-up, supports under the surround |
| Cornice | Ring swept along the plan with a real moulding profile; brackets and dentils added | Upside down |
| Mansard | Stacked slices: curb ring, then two slate slices. Dormers drop into notches in the slices | Upright |
| Top deck | Top cornice ring and flat roof deck in one part | Upside down |
| Dormer | Body with pilasters and arch, a barrel hood, and a bare sash | Body upright; hood standing on its front arch |
| Porch | Deck (floor, brick piers, lattice), flat post-and-arcade panels, roof with fascia and dentils | Deck and roof upside down; panels front-face down |
| Tower | Its own wall shell on a lower roof; cornice ring; bell-cast cap; cresting strips | Shell upright; cornice upside down |

**The key idea is "stacking slices".** A complex roof and cornice profile is cut into
horizontal rings. Each ring has a flat bottom and prints with no supports. Stacked, the
rings rebuild the full moulded silhouette: cornice → curb → mansard A → mansard B → top
cornice and deck. The seams fall on shadow lines, where a real building has joints anyway.

## Numbers that work at 1:87.1

- Wall core: **3.0 mm**. Clapboard: **1.2 mm pitch** (six 0.2 mm layers), relief 0.05–0.3 mm.
  Anything deeper looks toy-like.
- Window plug: **1.6 mm deep**, **0.15 mm clearance per side**. Glass is the plug's back
  face, **0.4 mm** thick (two 0.2 mm layers), so it glows if the building is ever lit.
- Casing 0.6 mm proud with a 0.5 mm bead to 1.0; hood mouldings 1.0 → 1.4 → 1.8 mm; keystone 2.0 mm.
  Three stepped layers read as a moulded profile at this scale.
- Cornice: about 11 mm tall, frieze 1 mm proud, soffit about 4.4 mm, crown about 6.6 mm.
  Brackets are paired every 10 mm.
- Mansard: about 75° slope, a bell-cast flare in the lowest 2 mm, slate rows 1.55 mm
  with 1.8 mm tabs.
- Porch: floor 14 mm above grade (1 mm under the first floor); posts 35.5 mm;
  roof fascia 3.2 mm with dentils. The porch roof tucks under the belt course, which acts
  as the ledger.

## What makes it read as a real building rather than a typical AI model

1. **Real moulding profiles everywhere.** Cornices, curbs, hoods and belt courses have
   stepped or ogee sections, not flat bands.
2. **Ornament at the right density.** Paired brackets, dentils under every soffit,
   keystones, a crest on first-floor hoods only, corbels under the hood ends.
3. **One style vocabulary.** Every opening uses the same eared casing and segmental hood
   family, with variations by floor (crest / keystone / flat cap).
4. **Masonry and siding at true scale:** random ashlar courses, running-bond brick, lap
   siding aligned to one datum, quoins that alternate long and short.
5. **Massing from a real building.** Offset blocks, a bay, a one-storey wing and a tower
   that rises through the roof line.

## Detail vocabulary (what makes it look great, not just good)

Rich HO detail comes from a few devices repeated at every scale, each shaped to print:

- **Chamfered square blocks** (`ornament.chamfer_box`): quoins that wrap the corners,
  the modillion blocks on the belt ring, pedestal and capital blocks on porch posts. The
  45° chamfer catches light like the real thing, and no edge overhangs more than
  depth − chamfer, whichever way the part prints.
- **Raised and sunk panels**: frieze panels with a diamond boss between the eave's
  bracket pairs, panelled aprons under first-floor sills, sunk panels on chimney faces
  (45° top edge), sunk panels and rosettes cut into the bed face of porch posts.
- **Consoles under every cap**: the flat window caps sit on scroll consoles; the eaves
  carry paired brackets.
- **Porch** (`features.porch_turned`):
  - A gray tongue-and-groove floor as its own part: 0.5 mm slots every 1.8 mm on its bed
    face, a border board framing the yard edges, a nosing, and a square socket for each
    post.
  - **Round turned posts printed standing up.** Rings, a vase, a necked ring and a bell
    capital flaring at 45° into a square abacus, never thinner than 1.9 mm. A post at a
    corner is shared by both runs.
  - **Railings printed standing up**, so every baluster is a real round spindle. End
    stiles carry the rounded hand rail; small feet lift the bottom rail off the floor.
  - **Posts and railings in one piece** (`joined=True`): each run of posts and its
    railings print together, standing on the plinths and the railing feet (both run
    0.4 mm into sockets in the floor). The only spans are short bridges: the bottom rail
    between feet and the hand rail over the balusters. The post's ringed collar is placed
    at the hand rail (`turned_post(collar=...)`), so the rail runs into the ring rather
    than the thin shaft; PrusaSlicer flags "loose extrusions" on the frame otherwise. The arcade stays its own piece:
    printed upright with the posts its arches and drops would start in mid-air, and
    printed upside down with them the hand rails would.
  - **The arcade** (beam, a square rosette block over each post, sawn-work spandrels with
    an elliptical arch, roundels, teardrops and a crown drop) **prints on its top edge**,
    so front and back come out alike. Flat panels printed face-down were glossy on the
    bed side and stepped on the other, and read as boxy.
- Corners where a wing meets the main house get no quoins (they are inside corners).
- **Flowing Queen Anne work on the surrounds** (`ornament`: `stroke`, `volute`,
  `sunburst`, `quatrefoil`, `bullseye`, `swag`, `urn_cs`, `scroll_bracket`): outlines
  drawn as curves in the wall plane and built up in flat terraces, each level inside
  the one below. The surround prints face-up, so the curves come out as clean perimeters,
  with no overhang at all; bands at least 0.5 mm, levels on the 0.2 mm grid.
  - First-floor windows (`style="pediment"`): bullseye corner blocks, a segmental
    pediment with a carved fan, a shaped apron that sweeps down to a drop, a quatrefoil
    boss.
  - Second-floor windows (`style="scroll"`): an eyebrow hood whose ends roll into
    volutes, a keystone with a fan crest, a sill on two scroll brackets and a pendant.
  - Bays with no headroom (`style="blocks"`): the corner blocks and a moulded shelf.
  - Doors (`openings.door_ornate`): round-headed glazed leaves with spandrel rosettes and
    quatrefoil panels, a sunburst transom, fluted pilasters on plinths with bullseye
    capitals; a frieze of swags round a cartouche under a broken swan-neck pediment with
    an urn (front), or a segmental pediment with a fan (back).

## Windows and doors: one part each (after the Ashby test prints)

Each window or door is ONE part, the way the reference kit makes them: a plug with the glass
and the sash (or the door leaves) that slides into the wall opening, and the surround on top.

- The glass is the plug's back face, two 0.2 mm layers; the sash sits recessed in the wall.
- It prints face-up. The surround is wider than the plug and starts 1.6 mm above the bed,
  so this is the one kind of part printed WITH supports (tree/organic, on the build plate
  only). The supports touch only the back of the surround, which lies against the wall.
- All windows and doors share one plate ("Windows_Doors"), so supports are switched on for
  that plate alone.
- They print in one colour; the glass and the trim are painted.

## Printability rules (checked by slicing every plate)

- Anything that would overhang goes in its own part, printed with that face down.
  Examples: window surrounds, the balcony, cresting strips.
- Windows and doors are the one exception: plug and surround in one part, printed with
  supports under the surround (see above), like the reference kit.
- Use a brim on thin standing parts: dormer bodies and hoods, cresting, steps, finial,
  chimney.
- Long bridges over flat door heads in the wall shell are acceptable in PLA.

## FDM detail standard (after the Beaumont Rev B test prints)

The first printed parts of the Beaumont (Rev B) came out poorly, and each failure had
one clear cause:

- **Fish-scale wall panels printed flat, face up**: 1.9 mm scales with **0.16 mm**
  joints. The top-skin lines are 0.4–0.45 mm wide, so the joints fused and the scales
  turned into "popcorn".
- **Slate roof**: the same 0.16 mm joints. The slates merged into noisy ridges.
- **Tower spire**: the finial (0.3–1.4 mm radius) was the only thing printing on the top
  16 mm of the plate. Each layer was a dot with no time to cool, and it came out as a
  squiggle.
- **Porch panels**: spindles of 0.6–0.9 mm, right at the nozzle limit. The best of the
  batch, but the junctions blobbed.
- **Gable trim (the Marigold's gold bargeboards, printed later)**: 0.8 mm thick, it snapped
  on the plate. Every gable ornament, bargeboard and applied gable piece is now one
  thickness, `gables.TRIM_D` = 2.2 mm (11 layers), with small raised details on top.

The standard every part now follows (0.4 mm nozzle; design for **0.20 mm layers**,
**0.16 mm** at the finest):

1. **Walls are upright shells, one per storey**, with the belt ring as the joint and
   locating lips on 45° corbels (`shell.storey_shells`). Texture on vertical faces with
   horizontal features (clapboards, shingle and brick courses) is resolved by the layers
   and prints crisp. That is why the reference kit prints its walls standing.
2. **In the layer plane, nothing is narrower than 0.5 mm (`RIB`) and no slot is narrower
   than 0.5 mm (`SLOT`).** This covers dentils (0.6 teeth, 0.5 gaps), mortar head
   joints, shingle joints, muntins, beads, louvers, cresting bars and pot walls.
3. **Along print z, steps and pitches sit on the 0.2 mm grid**: clapboard 1.2, brick
   course 0.8 (a 0.2 bed joint), plug 1.6, glass 0.4, casing 0.6 / 1.0, and profile
   heights of rings printed upside down, measured from their top. A flat face must never
   sit on a slicing plane (0.1 + 0.2 k): the slicer then gets a zero-thickness sliver.
   PrusaSlicer failed a whole plate over a railing whose hand rail sat at 7.7 mm.
   `lint.midlayer_faces` finds these.
4. **Upward-facing texture only as ribs** (0.5 mm wide, 0.5 mm apart, two layers or more
   deep): standing seams, louvers, panel mouldings. Never scales or slates on a top skin.
5. **Upright mouldings have 45° undersides**, and corbels step out at most 0.25 mm per
   0.2 mm layer (belt ring, chimney cap). Blocks on upright faces (quoins) get a full 45°
   bottom bevel. Dentils under an upside-down cornice run up to the soffit, and the ring
   reaches past its own locating lip, so nothing hangs over a gap. The first test
   plate got support under the dentils in Bambu Studio because they stopped 0.2 mm short.
6. **Slender tips are separate parts** printed beside taller parts (finials, 0.8 mm
   minimum section); they must never be the lone top of a plate.
7. Before export, run `hoarch.lint` (sub-nozzle ribs and slots per layer, in print
   orientation), `lint.overhang_kit` (area printed over air at Bambu Studio's default 30°
   support threshold: only opening heads, which bridge, may remain; the windows and doors
   are the one exception and print with supports), the fit check and the slicer. Then print
   the **detail test plate**
   (`buildings/sampler.py`, about 1.5 h) before a full kit.

## Library map

- `core.py`: units, primitives, mitred profile sweeps (`sweep_ring`, `sweep_run`),
  facades, textures (clapboard, slate and shingle rows in square, diamond, hexagon and
  staggered shapes, ashlar, brick, lattice, board-and-batten `battens`), pointed arches
  (`pointed_cs`, `pointed_rise`).
- `skins.py`: more wall skins, one per building: lined sidings (beaded lap, Dutch lap,
  drop siding, shiplap, V-groove), beadboard, diagonal and chevron boards, staggered
  shingles, brick in six bonds (Flemish with an optional diaper, running, English, common,
  Roman, stack) with a soldier band, scored stucco and half-timbering.
- `porchwork.py`: porch styles, one per building: eight posts (turned, Tuscan, fluted,
  chamfered, clustered, stick, spindle, Eastlake), railing fills (Chippendale, X, pierced
  quatrefoil, sawn) and balusters (vase, urn, spindle), five friezes (scroll, entablature,
  valance, spindle, fret) and eight skirts.
- `trimwork.py`: ten chimneys, six finials, ten foundation facings, ten belt-course
  profiles (`BELTS`) and six eave bracket styles (`bracket`, used by
  `roof.bracketed_cornice` through `brackets=dict(style=...)`).
- `openings.py`: one-piece window, door and twin-arch inserts (plug + surround), balcony;
  Italianate, Queen Anne and brick-house ("voussoir": long-and-short stone voussoirs and a
  keystone) heads; per-style families: Second Empire (`window_se`, `door_se`), Gothic
  (`window_gothic`, `door_gothic`: tracery, crockets, fleurs, label stops, engaged shafts),
  Romanesque (`window_romanesque`, `door_romanesque`: voussoir rings, cushion capitals,
  arcaded groups, open porch arch), Stick (`window_stick`, `door_stick`: crossed-stick
  casings, pent hoods on knee braces), Folk Victorian (`window_folk`, `door_folk`), Greek
  Revival (`window_greek`, `door_greek` with sidelights), San Francisco (`window_sf`,
  `door_sf`) and Free Classic (`window_fc`, `window_palladian`, `door_fc`). Door leaves
  (`_leaf`: arched, arched panels, studded, crossbuck, half glass, two panel, glazed, oval)
  and transoms (sunburst, plain, stick, diamond, leaded) are picked per building, and so is
  the sash pattern (`lites`, `rows`, `qa`, `upper="diamond"`).
- `moulding.py`: sculpted mouldings as height fields on the 0.2 grid (band, run; profiles
  ARCHITRAVE, CASING, CROWN, SILL, BED) and carved ornament (cartouche, anthemion, scroll
  keystone, pendant, rosette).
- `gables.py`: gabled roofs (`gabled_roof`: hollow body cut back to the gable walls, rake
  skins, fascia), gable ornaments hung on the rake ends (`bargeboard`, `gable_truss`,
  `gable_sunburst`, `gable_tudor`, `gable_gingerbread`), `ridge_cap`, `hip_cap`,
  `chimney_seat`.
- `ornament.py`: console brackets, dentils, keystones, fan crest, rosettes, finials,
  spandrels, chimney pots.
- `shell.py`: wall shell from plan blocks (openings, siding, corners: long-and-short or
  equal quoins, or a corner-board style from `CORNER_BOARDS`: board, pilaster, chamfer,
  stepped, capital, panel; belt
  course, water table, gable walls built in with `gables=`), per-storey shells with belt
  ring and lips, foundation.
- `roof.py`: bracket and dentil runs, slope textures (square, diamond, hexagon and
  staggered slate, standing seam, 5V crimp, lapped barrel tile), hip roofs by planes,
  cresting (pointed-arch or spear-and-ball) and
  flat-printed cresting strips. **Mansards**: `mansard` builds a hollow band on a convex plan
  from any outer profile (straight with a bell-cast kick, or a concave tower cap), its inner
  face parallel to the chord so it prints upright with banded slate rows; `mansard_top` is the
  moulded curb ring (upside down, locating lip and a 45 degree seat in its profile) and a
  separate standing-seam deck plate that drops onto the seat.
- `features.py`: dormer, tower cap, chimney, porch (deck, arcade panels, roof, steps);
  turned porches with sawn, Gothic (pointed arches) or braced (Stick) arcades, or any
  `porchwork` frieze; porch roof edges (`ROOF_EDGES`: dentil, modillion, fillet, cove,
  Gothic drops, stick battens, buttons, reeded) and pier facings matched to each
  building's foundation (`_pier_skin`); panel, board and louvered shutters.
- `kit.py`: parts with colour and print orientation, fit check, single-colour plate
  packing, 3MF/STL export, slice check, flat-lay and exploded render data, `drop_specks`
  (removes detached offcuts under 2 mm^3 that trims leave floating).
- `lint.py`: sub-nozzle detail check of every part in its print orientation.
- `render.py`: Cycles renders driven by a palette/views JSON.

## Second Empire (the Harcourt)

- **Mansard over a bracketed eave.** The eave ring prints upside down and the mansard band
  upright, so neither can carry a lip into the other (both joint faces are bed faces). The
  band is located by what passes through it instead: its opening hugs the centre tower
  (0.5 mm clear of the brick). A band with nothing through it is glued, aligned by its edges.
- **Flat top = curb + deck.** The curb ring and the deck are separate parts. One piece would
  only touch along faces (curb, lip, deck and dentils as loose shells). The deck drops onto a
  45 degree seat in the curb, so both print without support, and the deck can be a roof colour.
- **Chimneys on a deck** stand in 0.6 mm pockets, not on pegs: a peg under a chimney makes
  the whole chimney an overhang.
- **Dormers in a mansard** notch right through the band and sit on the eave ring. Keep their
  face, plinth, capital and keystone tops, the notch top and the hood length on the 0.2 grid.
- **A notched mansard prints upside down**, on its top rim. Upright, each round notch top is
  a bridge across a leaning band (PrusaSlicer: "collapsing overhang"). Upside down every notch
  widens as the print rises, the band leans out only 15 degrees, and the slate rows' ledges
  face up. The bell-cast kick is left smooth: upside down it is a 45 degree face.
- **Cresting strips** stop half a fence-thickness short of each corner and take only their
  own fence, so no sliver of the crossing strip rides along.

## Gabled roofs and gable walls (the Whitby onward)

- **The gable wall is part of the top wall shell**, a pentagon standing on the facade, so it
  takes the facade's siding and openings and prints upright with the storey below it. A
  separate gable piece would stand on a joint with nothing to locate it.
- **The roof body stops 0.15 mm inside each gable wall** and only a rake skin (1.8 mm, the
  top layer of the roof) runs over the wall and past it. The wall's top edge sits 0.15 mm
  under the skin. The roof drops in between the gable walls onto the lip on the eave walls.
- **Steep roofs are hollow**: with a slope over 1 the underside leans less than 45 degrees
  from vertical and prints upright. Chimneys stand in blind pockets over a downward
  pyramid of fill (`chimney_seat`), never over the hollow.
- **Ridge and hip caps** cover the joint where two slate faces meet (otherwise every layer at
  the ridge is a hairline sliver), with a flat top two nozzles wide on the layer grid. Trim
  a cap clear of the gable walls and of the space under the rake skin.
- **Gable ornaments hang on the rake's end** (w = rake): bargeboard, truss or sunburst. They
  print flat, face-up, one piece each; make sure the near-apex cuts leave the two halves
  joined (skip scallops that fall inside the other half).
- **A tower rising through a roof**: carry its wall down through the storey below inside
  the house (it otherwise starts in mid-air at the eave), and make the upper walls, the
  tower and any gable one piece above the first belt, so nothing is orphaned by a joint.

## Textures must overlap what they sit on

A texture that only touches its surface (skin face on the wall face) can come out of the
boolean union as a separate body: the brick foundation fell into 230 bodies and a crimped
roof into 127, and `drop_specks` then threw the small ones away. Every wall skin, foundation
facing and roof texture is now sunk 0.02-0.03 mm into its surface (`shell.wall_shell`,
`shell.foundation`, `roof.hip_texture`, `trimwork._skin`), and ornament keeps the 0.2 mm
overlap rule. Mount shutters just proud of the deepest siding (Dutch lap butts stand 0.46).

## Size standard (houses 21 to 30, Rev C)

The first cut of the second batch read as skinny next to the reference kits. Both references
are true HO: the pink house is 206 x 137 mm with a 40.6 mm storey pitch, and the tan house is
216 x 147 mm with storeys about 46 mm tall. They are simply mansion-sized. The houses now match:

- The main block is 180 to 210 mm long, so a house fills most of a 256 x 256 bed (P1S, P2S).
  The deepest parts still fit it.
- The first storey is 42 mm and the second 38 mm, over a 12 to 14 mm foundation. The joint
  band between them is about 10 mm; its height comes from the cornice there (next section).
- Windows are 8.4 mm wide, 24 mm tall downstairs and 21 mm upstairs, spaced well apart. A
  window no longer fills its storey's height or its wall's width.
- Porch posts are 20 to 30 mm apart, and round towers and porches use fewer facets.
- The Main Street shops (Rev C) follow the same standard: about twice their first floor plans
  (fronts of 60 to 130 mm, 110 to 150 mm deep), 42 mm ground floors (44 to 50 for the tall
  shop floors) and 38 mm upper storeys, house-size windows, and more bays rather than bigger
  ones. Signs, cornices, balconies and galleries grew with them.

## Built-up cornices (`cornice.py`)

Every level has a cornice: each storey joint, each eave, and the tower and bay tops. As in
the reference kits, a cornice is several rings stacked round the wall, each in its own
colour. No two cornice levels in the collection are alike: see the cornice table in
`COLLECTION.md`.

- **The wall carries it.** Where the cornice goes, the wall is a plain band standing on a
  45° ledge (`ledge`, `joint_profile`). The band has no siding and no openings.
  - `wall_shell(undress=...)` keeps the siding and corner boards out of the band.
  - The next storey, or the roof, sits on the band as before.
- **The rings wrap the band** 0.15 mm off the wall, stacked low to high:
  - a *frieze*: panels, medallions, swags, fret, triglyphs and so on;
  - a *course*: dentils, egg and dart, cable, billets and so on;
  - a *bed* with brackets or modillions hanging in front of the rings below;
  - a *crown* moulding.
- **Print orientation.** The frieze and course print upright, with their relief stepped back
  0.2 mm a layer underneath. The bed and crown print upside down, so they widen toward the bed.
- **Two parts per level, one colour change each** (`CO.add_level`). The upright rings merge
  into `-lower` (frieze + course) and the upside-down ones into `-upper` (bed + crown). A
  two-colour part changes filament once, at the height where its second ring starts in the
  print pose. It gets a plate of its own named for the change.
- **The crown carries the bed.** Upside down, the bed prints on the crown's foot, which is
  only the crown's `b` off the wall; its soffit would hang flat in the air. So where a bed
  lies directly under a crown, the crown gets a 45° cove from the bed's soffit edge up into
  the crown's curve. It reads as the corona under the cymatium.
- **Spacing.** One pitch and margin per level, so the frieze ornaments centre between the
  brackets above them.
- **Towers.** A ring that meets a tower rising through its level is cut back to it. Each
  remaining piece is its own part.
- **Fitting order.** Each ring drops over its band from above, so the joint rings go on before
  the storey above them and the eave rings before the roof.
- **Rings that wrap a tower.** An eave cornice can also wrap a tower (the Beaumont, Harcourt,
  Ardmore and Carrow). A closed ring could not be fitted, because the tower's top storey and
  its ledge are in the way. `CO.tower_cuts` and `CO.blades` part the rings with 0.3 mm cuts:
  - at the inside corners where the tower meets the house;
  - where a tower face runs on flush with a wall;
  - once through the tower's far side.

  No piece then wraps more than half the tower, and each one fits on from the side.
- **The roof.** It sits on the band's top. Its eave projects past the crown, so the crown
  shows under it.
- **Gable ornaments** are trimmed where they meet the roof.
- **End gables.** Where the gable ornament hangs off a rake, the rake overhangs further than
  the eave.
- `CO.signature(spec)` gives a level's pattern. `CO.specs_of(module)` collects a building's
  levels for the uniqueness check.

## Framed windows v2

- Every sash has a frame lining, from 0.55 mm wide on narrow lights to 0.9 mm on a
  full-size window (`openings.sash_frame`).
- The frame has stiles, and the upper and lower sashes meet at a 0.8 mm meeting rail.
- The houses use 1.3 mm casings with a back band (`casing=1.3, band=True`).
  `window_commercial(band=True)` gives shop windows one too.
- Renders colour the sash zone in the trim colour and the glass dark.
- For dark glass in a print, change filament at 0.4 mm on the `Windows_Doors` plate (the
  glass is the first two layers, printed face-up).

## Flat faces off the slicing planes at export (`kit.unmid`)

Upright ornament (frieze reliefs, course teeth) meets the 0.2 mm grid wherever its curves
fall. A flat face exactly on a slicing plane (0.1 + 0.2k above the bed) slices to
zero-thickness slivers. `Part.printed()` now runs `unmid`, which lifts every vertex within
0.012 mm of a slicing plane by 0.06 mm. Nothing visible moves, and the print checks no
longer report mid-layer faces.

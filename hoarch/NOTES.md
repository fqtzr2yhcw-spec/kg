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
- Mansard: about 75° slope, a bell-cast flare in the lowest 2 mm, fish-scale rows 1.55 mm
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
  facades, textures (clapboard, fish-scale, ashlar, brick, lattice).
- `openings.py`: one-piece window, door and twin-arch inserts (plug + surround), balcony;
  Italianate, Queen Anne and brick-house ("voussoir": long-and-short stone voussoirs and a
  keystone) heads.
- `ornament.py`: console brackets, dentils, keystones, fan crest, rosettes, finials,
  spandrels, chimney pots.
- `shell.py`: wall shell from plan blocks (openings, siding, quoins or corner boards, belt
  course, water table), per-storey shells with belt ring and lips, foundation.
- `roof.py`: bracket and dentil runs, slope textures, hip roofs by planes, cresting and
  flat-printed cresting strips. **Mansards**: `mansard` builds a hollow band on a convex plan
  from any outer profile (straight with a bell-cast kick, or a concave tower cap), its inner
  face parallel to the chord so it prints upright with banded slate rows; `mansard_top` is the
  moulded curb ring (upside down, locating lip and a 45 degree seat in its profile) and a
  separate standing-seam deck plate that drops onto the seat.
- `features.py`: dormer, tower cap, chimney, porch (deck, arcade panels, roof, steps).
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


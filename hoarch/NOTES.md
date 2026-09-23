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
| Window / door | **Two parts:** a sash/plug that fits the opening, and a surround with casing, sill, hood and crest | Both face-up |
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

## Printability rules (checked by slicing every plate)

- Anything that would overhang goes in its own part, printed with that face down.
  Examples: window surrounds, the balcony, cresting strips.
- Sash and surround are split so that neither needs supports. (The reference kit needs
  supports for its windows and doors.)
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
   heights of rings printed upside down, measured from their top.
4. **Upward-facing texture only as ribs** (0.5 mm wide, 0.5 mm apart, two layers or more
   deep): standing seams, louvers, panel mouldings. Never scales or slates on a top skin.
5. **Upright mouldings have 45° undersides**, and corbels step out at most 0.25 mm per
   0.2 mm layer (belt ring, chimney cap).
6. **Slender tips are separate parts** printed beside taller parts (finials, 0.8 mm
   minimum section); they must never be the lone top of a plate.
7. Before export, run `hoarch.lint` (sub-nozzle ribs and slots per layer, in print
   orientation), the fit check and the slicer. Then print the **detail test plate**
   (`buildings/sampler.py`, about 1.5 h) before a full kit.

## Library map

- `core.py`: units, primitives, mitred profile sweeps (`sweep_ring`, `sweep_run`),
  facades, textures (clapboard, fish-scale, ashlar, brick, lattice).
- `openings.py`: window, door and twin-arch inserts (sash + surround), balcony.
- `ornament.py`: console brackets, dentils, keystones, fan crest, rosettes, finials,
  spandrels, chimney pots.
- `shell.py`: wall shell from plan blocks (openings, siding, quoins or corner boards, belt
  course, water table), per-storey shells with belt ring and lips, foundation.
- `roof.py`: bracket and dentil runs, slope textures, hip roofs by planes, cresting.
- `features.py`: dormer, tower cap, chimney, porch (deck, arcade panels, roof, steps).
- `kit.py`: parts with colour and print orientation, fit check, single-colour plate
  packing, 3MF/STL export, slice check, flat-lay and exploded render data.
- `lint.py`: sub-nozzle detail check of every part in its print orientation.
- `render.py`: Cycles renders driven by a palette/views JSON.

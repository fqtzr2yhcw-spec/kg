# hoarch — construction notes for HO-scale printed buildings

These are the construction standards behind `hoarch`. They come from taking apart a
well-made commercial HO Victorian kit and rebuilding its part types in code. That rebuild
is a private study, kept out of this repository because the kit's license forbids sharing
derivatives. The library and these notes hold only general techniques; no geometry from
that kit is in the repo.

## How a detailed kit is split into parts

| Part family | How it is made | Print orientation |
|---|---|---|
| Wall shell | One piece per building: every storey and wing together, 3.0 mm walls, plain openings | Upright |
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

- Wall core: **3.0 mm**. Clapboard: **1.15 mm pitch** (4" exposure), relief 0.1–0.3 mm.
  Anything deeper looks toy-like.
- Window plug: **1.7 mm deep**, **0.15 mm clearance per side**. Glass is the plug's back
  face, **0.4 mm** thick (two 0.2 mm layers), so it glows if the building is ever lit.
- Casing 0.7 mm proud; hood mouldings 1.0 → 1.45 → 1.8 mm in three steps; keystone 2.0 mm.
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

## Library map

- `core.py`: units, primitives, mitred profile sweeps (`sweep_ring`, `sweep_run`),
  facades, textures (clapboard, fish-scale, ashlar, brick, lattice).
- `openings.py`: window, door and twin-arch inserts (sash + surround), balcony.
- `ornament.py`: console brackets, dentils, keystones, fan crest, rosettes, finials,
  spandrels, chimney pots.
- `shell.py`: wall shell from plan blocks (openings, siding, quoins, belt course, water
  table), foundation.
- `roof.py`: bracket and dentil runs, slope textures, hip roofs by planes, cresting.
- `features.py`: dormer, tower cap, chimney, porch (deck, arcade panels, roof, steps).
- `kit.py`: parts with colour and print orientation, fit check, single-colour plate
  packing, 3MF/STL export.
- `render.py`: Cycles renders driven by a palette/views JSON.

# Beaumont printable kit: progress log

Decisions from the owner (22 Sep 2026):
1. Sold as premade (assembled in-house), so optimise for print reliability and quick, repeatable assembly.
2. Window glass = one 0.2 mm layer of filament (lets light through later). No interior lighting and no removable roof in this version.
3. Owner handles colour choice; label every file with the render colour name.
4. HO scale.
5. Single-colour plates wherever possible, so any printer can run any plate.

## Kit architecture

| Colour (render) | Parts |
| --- | --- |
| Sage `#7f8f6a` | 1st-floor clapboard wall panels, tower 1st-floor tube, bay walls |
| Harvest Gold `#c79a45` | 2nd-floor fish-scale wall panels (incl. gable), tower upper tube, dormer front + cheeks |
| Cream `#efe7d2` | window/door casings, corner boards, belt bands, water-table ring, cornice rings (soffit + frieze + brackets), porch fronts, lattice skirts, gable ornament, bargeboards |
| Oxblood `#6a1f2b` | window sash inserts (first layer = glass) |
| Walnut `#4a2616` | front and back doors (first layer = glass in the lites) |
| Slate `#43474d` | main roof shell (+ wing gable + dormer roof), tower spire, porch roof, bay roof, back hood |
| Fieldstone `#8d877c` | foundation ring, porch piers, bottom step |
| Brick `#8a3b2b` | exterior chimney, interior chimney stack |
| Porch Gray `#6b706f` | porch deck, front steps, back stoop |
| Black Iron `#2b2b2d` | ridge cresting, finials, downspouts |

Joints: cream trim sits in 0.4 mm pockets so it self-aligns; the belt band covers the 1st/2nd-floor panel seam; the foundation ring, water-table ring and cornice ring square up the shell.

## Steps

- [x] 1. `model/kit.py`: generate every part as its own solid (assembly coords + print orientation + colour)
- [x] 2. Assembled render of the kit to confirm it still matches Rev A
- [x] 3. Fit checks: interference between parts, min feature size, bed-size check (256 mm)
- [ ] 4. Plate layout per colour; export STL per part + 3MF per plate, colour in file names
- [ ] 5. Slice check with a CLI slicer (print time, filament grams per plate, 1-layer glazing present)
- [ ] 6. Assembly guide page (steps, parts list, plate list) + update review artifact
- [ ] 7. Commit, push, update PR

### Log
- Steps 1-3 done: `python3 model/kit.py` builds 149 parts in ~9 s; `python3 model/kit_check.py` reports 0 interfering part pairs and no part over the 250 mm bed.

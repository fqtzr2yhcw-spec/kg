# Massing models

Plain grey volume studies for reviewing a building's layout (plan shape, roof form, towers,
porches, the ground it stands on) before any ornament is drawn.

    cd hoarch
    PYTHONPATH=. python3 massing/pilot_a.py massing out/massing/pilot_a
    PYTHONPATH=. python3 -m hoarch.render --npz out/massing/pilot_a.npz \
        --palette out/massing/pilot_a_palette.json --views hero,front,rear,aerial --out out/massing/pilot_a
    python3 massing/sheet.py out/massing/pilot_a out/massing/Pilot_A.png "Title" "note|note"

- `pilot_a.py`: a Shingle Style house under one great gable (after the W. G. Low House and
  Kragsyde).
- `pilot_b.py`: a Federal brick house in a standing Gothic skeleton with a carriage-arch link
  and a matching barn (after the Wedding Cake House).

New-layouts batch, houses 103 to 114 (each after a real building's plan and massing):

- `marisol.py`: a lighthouse keeper's house, the light tower out of the middle of the roof (Point Fermin).
- `fevre.py`: a hillside house set into a slope, a walk-out stone storey toward the street (Galena).
- `bethel.py`: three camp-meeting cottages on an arc round a green (Oak Bluffs).
- `piney.py`: a dogtrot, two log pens and an open breezeway under one roof (Sam Houston's Woodland).
- `marigny.py`: a camelback shotgun double (New Orleans).
- `paloma.py`: a Monterey Colonial adobe, balcony on three sides, wings round a courtyard (Larkin House).
- `severn.py`: a five-part Palladian house (Hammond-Harwood House).
- `raquette.py`: an Adirondack great camp lodge with stacked gable balconies (Sagamore).
- `sebago.py`: a New England connected farm, big house to barn.
- `prow.py`: a flatiron block on a wedge-shaped lot (Gooderham Building).
- `laurel.py`: a water-powered gristmill on a creek bank with the miller's cabin (Mabry Mill).
- `ashgrove.py`: an estate gate lodge with the drive passing through it (Biltmore Lodge Gate).

Each runs as `PYTHONPATH=. python3 massing/<key>.py massing out/massing/<key>`, rendered with
`--views hero,front,rear,aerial`.

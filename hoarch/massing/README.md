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

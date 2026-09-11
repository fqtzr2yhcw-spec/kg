# Print estimates & optimization notes — 1:350

Sliced headless with PrusaSlicer (generic 0.4 mm nozzle, 0.2 mm layer, 15% infill,
supports on). Not an exact Bambu profile — load a **Bambu Lab P1S 0.4 mm** profile in
Studio for final numbers — but accurate enough for planning and pricing.

| Part | Qty | Time / ea | g / ea | Time × qty | g × qty |
|------|----:|----------:|-------:|-----------:|--------:|
| Base half | 2 | 10h45m | 721 | 21h30m | 1441 |
| Shaft band | 4 | 13h05m | 1149 | 52h20m | 4596 |
| Setbacks | 1 | 13h23m | 241 | 13h23m | 241 |
| Crown | 1 | 14h02m | 232 | 14h02m | 232 |
| Spire | 1 | 1h48m | 11 | 1h48m | 11 |
| **Total (9 parts)** | | | | **~103 h** | **~6521 g** |

- **Material cost** ≈ **$163** @ $25/kg (≈ 6.5 kg).
- **Wall-clock** across the two printers (P1S + P2S) in parallel ≈ **51 h**.

## Optimization levers (data-backed)
- **Material:** shaft band at **8% infill** → **590 g** (from 1149 g), i.e. **−2.2 kg**
  across the four bands. Use a **grid / lightning** pattern at low density — an 8%
  **gyroid** test *raised* the time estimate (slow curved paths), so avoid gyroid here.
- **Time:** dominated by the fine facade **perimeters**, not infill. A taller layer
  height (0.24–0.28 mm) or adaptive/variable layers on the shaft cut hours without
  touching the visible detail. The crown is slow per gram (tiny features + supports).
- **Biggest lever (geometry, needs sign-off):** printing the shaft & base as **hollow
  shells** rather than solid would cut weight/material/cost the most — but it changes
  the model's heft and feel, so it's a product decision, not an automatic one.

## Supports
Overhangs are the projecting **cornice undersides** (setbacks, base, crown). Keep the
crisp Art Deco steps and let the slicer add **targeted supports** there (low-visibility
undersides) rather than chamfering, which would soften the profile. The shaft's window
sills are < 1 mm — they bridge without support.

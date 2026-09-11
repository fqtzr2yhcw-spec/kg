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

> **Time caveat:** the headless CLI slicer produced *incoherent* time estimates
> (13–77 h for near-identical parts) — it has no real Bambu profile. Trust the
> **material (g)** numbers; **validate print time in Bambu Studio** with a P1S
> 0.4 mm profile.

## Production recipe (CHOSEN: solid + low infill)
Keep the sections **solid** (no geometry change) and lighten them in the slicer:
- **Infill** 8% **grid** (fast — avoid gyroid, it traces slower)
- **Perimeters** 3 · **Layer** 0.16 mm shaft/base (window detail), 0.20 mm elsewhere
- **Supports** on (threshold ~50°) — only the cornice undersides need them
- **Filament** stone-grey PLA; **translucent** crown

~27% less material than 15% infill, with no thin-wall time penalty. (Hollow shells
were built & verified — −39% material — but rejected: at this detail the
all-perimeter walls print slower, working against the time goal.)

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

## Per-part print orientation & supports

| Part | Orientation on plate | Supports | Notes |
|------|----------------------|----------|-------|
| Base N / S | Natural bottom (ground) down | Yes — under the 5th-floor cornice only | Brim for corner adhesion; dowel-hole faces at the seam bridge fine |
| Shaft ×4 | **Upright** (as modelled) | **None** — facade is vertical; sills < 1 mm bridge | Best-case part: crisp windows, no support scars on the visible facade |
| Setbacks | Wide base down (as modelled) | Yes — under the stepped cornice tiers | Short part (59 mm); supports are on hidden undersides |
| Crown | **Upright**, base down | Light — under the cornice rings only | Stepped cap tapers inward (self-supporting); lantern slots are vertical |
| Spire | **Upright + brim** | None (tapering cone) | Slow the upper layers to avoid wobble; or substitute a tapered metal rod for the very tip |

**Global:** 0.16 mm layers on the shaft & base for sharp window definition, 0.20 mm
elsewhere. Stone-grey PLA for everything except the **translucent** crown (LED backlight).
Assemble bottom-up: base halves joined with two 3 mm dowel pins + CA glue, then each
section onto the tenon below (dry-fit verified at 0.00 mm³ clearance).

# perCVus — Roadmap

A phased plan that starts with the hardest, most-defining part (the AI referee) and
grows outward. Each phase is meant to be a thing you can actually see and use, not just
scaffolding.

## Phase 0 — Foundation (this repository, now)

- [x] Concept & mechanics written down ([`docs/CONCEPT.md`](CONCEPT.md)).
- [x] A clickable prototype of a single debate floor
      ([`prototype/index.html`](../prototype/index.html)) — real proposition, scored
      arguments on both sides, perCVus's clarifying questions and "State of the Floor,"
      and a working composer with a local stand-in scorer.

The prototype's purpose is to make the vision tangible and to pressure-test the *feel*
of the scoring loop before any real infrastructure exists.

## Phase 1 — The real referee

The prototype scores arguments with a lightweight local heuristic. Phase 1 replaces that
with the real thing: **Claude reading each argument** and returning scored axes (rigor,
novelty, bridge, civility) *with reasons*.

- A small backend endpoint (so the API key is never exposed in the browser).
- A well-designed prompt that returns structured scores + plain-language explanations.
- The transparent score card from the prototype, now backed by real reasoning.

This is the phase that proves the whole idea. Everything after it is "wiring around a
core that works."

## Phase 2 — A living floor

- Persist a single floor: proposition, arguments, sides, scores, synthesis.
- Real-time updates so multiple people share one floor.
- The AI's "State of the Floor" synthesis regenerated as the debate evolves.
- Floor-time economy (baseline + earned) enforced per participant.

## Phase 3 — Accounts, standing, and civility

- Profiles and sign-in.
- Standing (reputation) that unlocks privileges — never basic speech.
- Civility gate: conduct detection, zeroing, escalating cooldowns.
- Shared-credit for bridge moves.

## Phase 4 — Many floors

- Create and browse floors across subjects.
- **Health-based ranking** (progress, not engagement) for the "trending" surface.
- Forking: spin a recurring sub-question into its own floor; build the proposition tree.

## Phase 5 — The corpus

- The tree of resolved / contested propositions becomes browsable and searchable.
- Synthesis history: how understanding on a question changed over time.
- The "collective knowing" that was the point from the start.

---

### Guiding constraints

- **Start simple.** One floor, two sides, before anything branches.
- **The referee earns trust or nothing works.** Transparency of scoring is not optional.
- **Never trade the open forum for cleaner metrics.** The §2 principle in the concept
  doc wins every tradeoff.

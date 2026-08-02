# perCVus — Concept & Mechanics

This document captures the design of perCVus: what it is, the principles that govern
it, and the specific mechanics for scoring, incentives, the AI referee, and how topics
rise. It is the north star the build follows.

---

## 1. Mission

Get closer to objective truth, faster, by rewarding sound reasoning and the free flow
of ideas — and by having humans and AI build the results into a growing corpus of
collective understanding.

The founding intuition: **perception is 9/10ths of understanding.** Most disagreement
isn't about the facts; it's about how differently people *perceive* the same thing.
perCVus is machinery for improving perception so that understanding can follow.

---

## 2. The governing principle

> **Rewards expand what good reasoners can *do*. They never contract what everyone
> else is *allowed to say*.**

This one rule shapes every mechanic below. The person who is *wrong but sincere* is the
raw material of truth-seeking — if you silence them, you can never correct them, and you
end up with an echo chamber of the already-articulate. So:

- **Being wrong is never punished.** Only two things are: bad conduct, and spam.
- **Good reasoning is upside-only.** It earns you reach, standing, and privileges — it
  never takes anyone else's voice away.

---

## 3. Scoring: separate axes, not one number

A single "argument quality" score gets gamed the instant it exists (Goodhart's law), and
it collapses distinct virtues into one blunt figure. Instead, the AI referee scores each
contribution on **independent axes that cannot trade against one another**:

| Axis | What it measures | What it rewards |
|------|------------------|-----------------|
| **Rigor** | Are premises stated? Does the conclusion follow? Evidence vs. bare assertion? Fallacies present? | Sound structure |
| **Novelty** | Does this add something not already on the floor? | New ideas over repetition |
| **Bridge** | Steelmanning the other side, conceding a fair point, synthesizing two views | Collaboration |
| **Civility** | Conduct only — *not* whether the argument is correct | A gate, see §5 |

Every score is published **with a plain-language reason**. The referee is transparent
and arguable — you can contest the *referee*, not just your opponent. Contesting a score
is itself a first-class action on the floor.

---

## 4. Floor-time: the incentive economy

The original instinct was a character budget: start with N characters, earn more for
good arguments, lose them for bad. The spirit is kept; the failure mode (muzzling the
sincere-but-unskilled, and newcomers) is designed out by reframing it as **floor-time**,
scoped to a single debate — like speaking time in a real debate.

- **Everyone always keeps a baseline.** Participation cannot be taken away. The baseline
  is enough to make a real point.
- **Sound contributions earn *extra* floor-time within that debate** — more room to
  develop an argument, and more reach. It's a reward for standing you've earned on this
  topic, not permission to speak.
- **This naturally rate-limits** domination and spam without silencing anyone.

Separately, a person accrues **standing** (reputation) across debates. Standing unlocks
*privileges* — proposing a fork, casting a candidate synthesis, light moderation help —
never the basic right to post. Keeping "reach/privileges" and "the right to speak" on
different tracks is what preserves the open forum.

---

## 5. Civility is a multiplier, not a currency

You cannot out-argue toxicity. Civility is not a bucket of points you can trade away by
being clever; it is a **gate on everything else**:

- An abusive contribution has its other scores **zeroed for that contribution** — a
  brilliant point delivered as an insult earns nothing.
- Repeat offenses trigger escalating **cooldowns**.
- The target is always **conduct**, never being wrong or holding an unpopular view.

Civility as a pillar means it constrains the clever as firmly as it constrains everyone
else.

---

## 6. Collaboration: shared credit for building on each other

The most valuable and most-neglected mechanic. Every other platform rewards only the
dunk. perCVus rewards the **bridge**:

- When you extend, steelman, or fairly concede to someone's point, **both people get
  credit** — the originator and the extender. Ideas compound instead of compete.
- The AI referee specifically detects and scores these bridge moves (see the **Bridge**
  axis, §3).

This is how a floor becomes cooperative construction rather than a shouting match.

---

## 7. The AI referee — and the "third pole"

perCVus is not For and not Against. It is the neutral **third pole** — the "maybe" —
sitting between the two sides. Its jobs:

1. **Score** every contribution on the axes in §3, transparently.
2. **Ask the sharpest clarifying question** when a debate stalls or when the two sides
   are talking past each other.
3. **Surface hidden assumptions** — e.g. "both sides are assuming X; is that true?"
4. **Publish the "State of the Floor"** — a living synthesis, continuously updated:
   - **Established** — what both sides now accept.
   - **Contested** — what's genuinely still in dispute.
   - **What would resolve it** — the evidence or definition that would move things.

That fourth job is the heart of the product. The synthesis is how a noisy debate becomes
a durable piece of the **corpus of collective knowing**. The referee is the *scribe of
consensus*.

---

## 8. Structure: thesis, antithesis, synthesis — and forks

Every floor starts simple: **one proposition, two sides (For / Against)**. That is the
*dialectic* — thesis and antithesis, with perCVus's synthesis as the third pole. It's
the classical engine for reaching truth through structured opposition, and it keeps v1
tractable.

Growth happens by **forking**. When a sub-question keeps recurring inside a floor, the
referee proposes spinning it out into its own floor. Over time this builds a **tree of
propositions** — resolved branches, contested branches, and the open questions hanging
off each. That tree *is* the corpus.

---

## 9. Ranking topics: health, not heat

Ranking by engagement is exactly the mechanic that makes conventional feeds toxic —
outrage travels fastest. perCVus ranks floors by a **progress score** instead:

- Are new, *distinct* points being made (vs. repetition)?
- Are concessions and bridges happening?
- Are sub-questions getting resolved or cleanly forked?
- What's the *quality density* — signal per contribution?

A floor with fifty thoughtful exchanges should outrank one with five thousand dunks. The
familiar "trending" surface remains — it's just pointed at understanding instead of
noise.

---

## 10. Open questions (deliberately unresolved)

These are known and intentionally left for later:

- **Exact score-to-floor-time curve.** Needs tuning against real behavior so it can't be
  gamed by verbosity.
- **How much the AI participates** beyond refereeing — can it argue a position when a
  side is unrepresented, and if so, how is that signaled?
- **Fork thresholds.** How much recurring sub-debate justifies a new floor.
- **Standing decay.** Whether reputation should fade so the forum stays meritocratic and
  current.
- **Handling genuinely non-binary questions** that don't fit For/Against — likely
  surfaced by the synthesis as "it depends on X," which becomes a fork.

None of these block a first build; they're flagged so they aren't quietly decided by
accident.

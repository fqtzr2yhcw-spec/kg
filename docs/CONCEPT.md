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

- **Everyone always keeps a baseline.** Being *wrong* never costs you participation; only
  conduct can, and only through the temporary, transparent limits in §5. The baseline is
  always enough to make a real point.
- **Sound contributions earn *extra* floor-time within that debate** — more room to
  develop an argument, and more reach. It's a reward for standing you've earned on this
  topic, not permission to speak.
- **This naturally rate-limits** domination and spam without silencing anyone.

Separately, a person accrues **standing** (reputation) across debates. Standing unlocks
*privileges* — proposing a fork, casting a candidate synthesis, light moderation help —
never the basic right to post. Keeping "reach/privileges" and "the right to speak" on
different tracks is what preserves the open forum.

---

## 5. Decorum & enforcement

You cannot out-argue toxicity. Civility is not a bucket of points you can trade away by
being clever; it is a **gate on everything else** — an abusive contribution has its other
scores (§3) **zeroed for that contribution**, so a brilliant point delivered as an insult
earns nothing.

But a gate needs teeth, and this is one of only *two* mechanics that ever restrict anyone
(§2), so the whole system is built on a single organizing rule:

> **perCVus only restricts conduct that itself silences others.**

You are never sanctioned for being harsh, wrong, or unpopular — only for the behaviors
(personal attacks, harassment, slurs, threats) whose actual effect is to drive other
people off the floor. Limiting *that* is consistent with "never contract what anyone is
allowed to say" (§2), because the conduct was contracting it first.

### The record stays visible

Every gated violation is **left in place and annotated** — the referee attaches a
plain-language note explaining exactly which rule broke, visible to everyone. perCVus
does not memory-hole misconduct; it turns each violation into a public lesson in the
norms. *One carve-out:* content that re-victimizes a target — slurs, threats, targeted
harassment, personal information — is **collapsed behind a click** ("hidden for conduct ·
click to view"). Still auditable, never erased, but not forced onto the person it targets.

### The ladder

**Strike 0 — rephrase.** A heat-of-the-moment jab is met with an offer, not a penalty:
*strip the insult and the point counts in full.* Only a repeat or a refusal escalates.
Nobody is taxed for a single hot sentence they're willing to fix.

**Strike 1 — throttle to 256, earn your way back.** The per-post allowance is cut to
**256 characters** — enough to make a careful point, not enough to hold the floor. From
there you climb back out by *doing the very thing perCVus values*: each civil,
well-scored contribution raises the cap along a fixed path —

> 256 → 500 → 750 → full reinstatement (three qualifying posts).

How far each post moves you is set by its **quality score** (§3): a genuinely strong,
civil contribution advances you a full tier, while weak-but-civil ones climb slower. The
penalty for incivility is, precisely, *demonstrate that you can be rigorous and civil.*
Re-offending while throttled ends the climb and triggers Strike 2.

**Strike 2 — 24-hour lockout.** Posting is suspended for 24 hours, and a **public
declaration is posted in the thread** naming how the rule was broken. The original
contribution stays up (annotated). This is the one place participation is removed, and it
is strictly time-boxed and transparent.

**Strike 3 — out, pending petition.** A third strike removes the member from the
community. This is a **deliberate hard line.** perCVus is a niche space *by design*: it
does not want everyone, it wants people who will contribute — and it protects that space
rather than letting those who can't keep decorum pollute it for everyone else. That is a
choice, made openly.

### The way back

Removal is not exile. Reinstatement is by **petition**, and the petition is
**deliberately forgiving**: someone who takes the time to ask to return is, in almost
every case, reinstated — the act of asking is itself the good-faith signal perCVus is
looking for. Only extreme cases (severe, repeated, or malicious harm) are refused.
Petitions are heard by a **jury of high-standing members** (§4), with the operators as a
backstop — the severe end stays human-judged, never decided by the referee alone.

### Guardrails against weaponization

Because this is the one system that can restrict a voice, it is hardened against being
turned into a weapon:

- **The referee decides, not the crowd.** A pile-on or mass-flag cannot silence anyone;
  flagging only routes a contribution for a conduct check.
- **Conduct-only firewall.** The referee must cite the specific behavior. "I disagree" or
  "this offends me" can never, by construction, trip the gate — disagreement is not a
  violation.
- **Rulings are contestable.** A civility call is arguable like any other score (§3); a
  wrongly-gated contribution can be appealed to the same human jury.
- **Malicious flagging carries its own cost**, so reporting cannot become the attack.

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

## 9. Conversation structure: claim-nodes, tagging, and traceability

A floor needs a shape. Two obvious shapes both fail perCVus specifically, because
perCVus has a job ordinary discussion threads don't: **score each contribution and
synthesize the floor.** That job constrains the structure.

- **One flat thread** — everything in a single stream — is rejected. Strong arguments
  scroll away, timing beats quality (the exact pathology §2 exists to prevent), and the
  referee can't say "the Against side rests on these three claims" when the floor is an
  undifferentiated feed. There's also no way to tell what is answering what.
- **Deeply nested threads** — Reddit-style infinite nesting — are also rejected. They
  fragment the floor into rabbit holes, bury the strongest counter-argument levels deep,
  reward whoever replied *first* to a hot comment over whoever argued *best*, and leave
  no canonical structure for the synthesis engine to read.

perCVus uses the middle path: a **shallow, structured floor built from claim-nodes.**

- **The unit is a claim, not a message.** Each contribution is a node — the thing the
  referee scores (§3) and the thing the synthesis points at (§7).
- **Replies attach to a specific claim**, so the floor is traceable: every node records
  what it answers. But replies **don't nest without bound.** Depth is kept shallow — a
  claim and the rebuttals/support attached to it.
- **Growth is by promotion, not nesting.** When a rebuttal spawns its own substantial
  sub-debate, it's **promoted to its own claim-node** (and, if it keeps recurring, forked
  into its own floor per §8) rather than sinking another level deeper. Forking is the
  release valve that lets the floor stay flat.

This keeps the floor flat enough to synthesize and linked enough to trace — the two
properties the referee needs.

### Tagging is structure, not decoration

Mentions do real structural work here; they aren't just notifications:

- **`@user`** — a traceable link to a person, plus notification. Your name is on your
  claim; accountability is built in, and it never silences anyone (§2).
- **`@claim`** — a link to a *specific argument*. This is what makes the floor traceable
  and what the synthesis engine reads to know which node answers which.
- **Tagging carries credit.** Bridges and **shared credit** (§6) follow the tag: you tag
  the claim or person you're building on, and the credit-split attaches to that link. The
  tag is how the referee knows a bridge move connects two specific contributions.

So tagging is the connective tissue of the structured floor — the mechanism that turns a
list of claims into a navigable argument map.

---

## 10. Ranking topics: health, not heat

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

## 11. Open questions (deliberately unresolved)

These are known and intentionally left for later:

- **Exact score-to-floor-time curve.** Needs tuning against real behavior so it can't be
  gamed by verbosity — this includes the Strike 1 earn-back curve (§5): how much each
  qualifying post advances the 256 → 500 → 750 → full path.
- **How much the AI participates** beyond refereeing — can it argue a position when a
  side is unrepresented, and if so, how is that signaled?
- **Fork thresholds.** How much recurring sub-debate justifies a new floor.
- **Promotion depth.** Exactly how shallow replies stay before a sub-debate is promoted
  to its own claim-node or forked (§9) — tuned so the floor never tangles but genuine
  back-and-forth isn't cut off prematurely.
- **Standing decay.** Whether reputation should fade so the forum stays meritocratic and
  current.
- **Handling genuinely non-binary questions** that don't fit For/Against — likely
  surfaced by the synthesis as "it depends on X," which becomes a fork.

None of these block a first build; they're flagged so they aren't quietly decided by
accident.

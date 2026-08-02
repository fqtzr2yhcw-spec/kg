# perCVus

> **Perception is 9/10ths of understanding.**

perCVus is a public square built around one idea: that we get closer to the truth
faster when arguments win on the quality of their *reasoning* rather than the volume
of their delivery. It is a place where any subject can have a **floor for debate**,
refereed by an AI that scores the logic of what people say — not who they are, and
not whether the referee happens to agree with them.

The goal is not to win. The goal is to move a group of people — and the AI alongside
them — closer to a shared, better-founded understanding, and to build that
understanding into a growing corpus of collective knowing.

## What makes it different from a normal feed

A typical social feed rewards whatever travels fastest — usually outrage. perCVus
inverts that. It is designed so that the things that rise are the things that make us
*understand more*:

- **Arguments are scored on reasoning, transparently.** Every score comes with a
  plain-language explanation, so you can argue with the referee, not just each other.
- **Being wrong is never punished — only bad conduct and spam are.** A sincere but
  flawed argument is the raw material of progress. It gets engaged, not silenced.
- **Collaboration is rewarded as much as opposition.** Building on someone else's
  point, conceding fairly, or synthesizing two views earns credit — for *both* people.
- **Topics rise by health, not heat.** A floor rises because understanding is
  actually advancing on it, not because it's loud.
- **The AI is the scribe of consensus.** It continuously distills each debate into a
  living summary: what's established, what's still contested, and what would resolve it.

## How a debate works

Every floor starts as a single proposition with two sides — **For** and **Against** —
the classic structure of thesis and antithesis. perCVus itself sits in the middle as
the neutral third pole: it doesn't take a side, it asks the sharpest question, surfaces
hidden assumptions, and publishes the synthesis. When a sub-question keeps recurring,
the floor can **fork** it into its own debate — that's how the tree of understanding
grows.

See [`docs/CONCEPT.md`](docs/CONCEPT.md) for the full design, including how scoring,
floor-time, civility, and topic ranking work.

## The name

**perCVus** — "one who perceives well." It comes from a phrase I said often —
*"perception is 9/10ths of understanding"* — a riff on *"possession is 9/10ths of the
law."* A dear friend, Jerry, from Texas, coined the name **perCVus** for me across the
many philosophical debates we had together over the years. Jerry has since passed. It
feels right that a space built for exactly that kind of debate carries the name he gave
me — in a way, every argument made here is a small continuation of the ones we had.

## Project status

Early. This repository currently contains:

- **[`docs/CONCEPT.md`](docs/CONCEPT.md)** — the full design and mechanics.
- **[`docs/ROADMAP.md`](docs/ROADMAP.md)** — the phased build plan.
- **[`prototype/index.html`](prototype/index.html)** — a working, clickable prototype
  of a debate floor you can open in any browser. It demonstrates the whole loop: a live
  proposition, scored arguments on both sides, perCVus's clarifying questions and
  "State of the Floor" synthesis, and a composer where you can take the floor and watch
  an argument get scored.

### Viewing the prototype

Just open the file in a browser — no setup, no install:

```
open prototype/index.html
```

The prototype's argument scoring runs on a lightweight local stand-in so you can feel
the loop with zero configuration. In the real perCVus, that scoring is done by Claude
reading each argument — see the roadmap for how that gets wired in.

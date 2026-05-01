---
name: copy-review
description: Structured review checklist for any external-facing copy. Use before any copy is shipped — by the copywriter for self-review and by the CMO for final QA. Returns a pass/fail verdict plus specific edits.
---

# Copy review

A 10-minute structured pass that catches the issues that matter and
ignores bikeshedding. Run it against the linked campaign brief,
creative brief, brand-voice skill, and target persona — not against
personal taste.

---

## How to run

1. Re-read the campaign brief §3 (insight + proposition) and §4
   (offer + CTA), and the persona ID.
2. Read the copy aloud once, end-to-end, before checking anything.
3. Walk the checklist below. For each fail, write a one-line note
   with the fix — don't just flag the problem.
4. Produce a verdict block (template at the bottom).

---

## Checklist

### A. Strategy fit
- [ ] **A1.** Single-minded proposition is recognizable in the first
      10 words.
- [ ] **A2.** Copy targets the primary persona's actual vocabulary,
      pains, and triggers (cite persona ID).
- [ ] **A3.** Every claim has a reason-to-believe within the same
      view (page, email, ad).
- [ ] **A4.** CTA is specific (verb + outcome), singular, and
      friction-light.
- [ ] **A5.** No anti-persona language slipped in.

### B. Voice fit
- [ ] **B1.** Voice attributes match `brand-voice` for this surface.
- [ ] **B2.** No banned vocabulary or buzzwords.
- [ ] **B3.** No stacked adjectives ("powerful, robust, intuitive").
- [ ] **B4.** No "we"-centric sentences when "you"-centric works.
- [ ] **B5.** Tone is shifted appropriately for the situation
      (welcome ≠ error ≠ ad).

### C. Craft
- [ ] **C1.** Headline earns the click. Could a competitor publish the
      same headline? If yes, rewrite.
- [ ] **C2.** First sentence does work — not a runway.
- [ ] **C3.** Verbs are concrete; adjectives carry weight or are cut.
- [ ] **C4.** No filler ("just", "simply", "in order to", "leverage",
      "unlock", "seamless").
- [ ] **C5.** Read aloud — does it sound like a person?
- [ ] **C6.** Length matches the surface (ad ≠ landing page ≠ email).
- [ ] **C7.** Parallel grammar in lists.

### D. Truth & risk
- [ ] **D1.** Every superlative ("best", "fastest", "only") is
      substantiated or removed.
- [ ] **D2.** Numbers, dates, names are correct.
- [ ] **D3.** No claim that requires legal review without legal sign-off.
- [ ] **D4.** No competitor named without a defensible reason.
- [ ] **D5.** Accessibility: no meaning carried by color alone, alt
      text exists for any image references.

### E. Mechanics
- [ ] **E1.** Spelling, grammar, punctuation.
- [ ] **E2.** Capitalization matches `brand-voice` rules.
- [ ] **E3.** Links work and are descriptive (not "click here").
- [ ] **E4.** Tracking parameters present where required (link to
      `utm-naming` skill).

---

## Verdict block (return this)

```markdown
## Copy review — {asset name}

- **Reviewed against:** Campaign CB-..., Concept CR-..., Persona P{n}-...
- **Reviewer:** {agent}
- **Verdict:** SHIP | REWRITE | EDITS-NEEDED

### Required edits (blocking)
1. [section] {issue} → {fix}
2. ...

### Suggested edits (non-blocking)
1. ...

### Notes
- one-paragraph summary of the read
```

## Verdict rules

- **SHIP** — zero items in "Required edits".
- **EDITS-NEEDED** — ≤ 3 required edits, all minor.
- **REWRITE** — strategy fit (section A) failed, voice is off, or
  more than 3 required edits.

Don't soften a REWRITE verdict to spare feelings. The whole point of
this skill is to be the unflinching second pair of eyes.

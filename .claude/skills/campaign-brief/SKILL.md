---
name: campaign-brief
description: Standard campaign brief template the CMO and channel agents use as the contract for any campaign. Use at the start of every campaign before any creative or production work begins. Output must be approved by a human before downstream agents proceed.
---

# Campaign brief

A campaign brief is the contract. Nothing gets produced until a brief
is filled in and approved. If a question below can't be answered, that
itself is the first finding — surface it instead of guessing.

---

## Template (copy this block, fill it in)

```markdown
# Campaign brief — {campaign name}

- **Brief ID:** CB-YYYYMMDD-{shortname}
- **Owner:** {agent or human}
- **Status:** draft | approved | in-flight | wrapped
- **Last updated:** YYYY-MM-DD

## 1. Objective
- **Business goal:** (revenue, pipeline, signups, retention, awareness)
- **Primary KPI + target:** e.g. "300 SQLs in 60 days"
- **Secondary KPIs:**
- **Anti-goal / guardrail:** (what we will NOT trade off — e.g. CAC, NPS)

## 2. Audience
- **Primary persona ID:** (from `audience-personas`)
- **Secondary persona ID:** (optional)
- **Segment / list / targeting criteria:**
- **Estimated reachable size:**

## 3. Insight & message
- **Customer insight (one sentence):** the truth this campaign exploits
- **Single-minded proposition:** one sentence the audience should walk away with
- **Reasons to believe (3 max):** proof, not adjectives
- **Tone shift from default voice:** (link to `brand-voice` tone matrix)

## 4. Offer & CTA
- **Offer:** what we're asking them to do
- **CTA verb + destination:** e.g. "Start free trial → /signup"
- **Friction we're removing:** e.g. no credit card, 2-min setup

## 5. Channels & deliverables
| Channel | Owner agent | Deliverables | Due |
|---|---|---|---|
| | | | |

## 6. Timeline
- **Brief approved:**
- **Concept locked:**
- **Production complete:**
- **Launch:**
- **Readout (T+1w):**
- **Readout (T+4w):**

## 7. Budget
- **Total:**
- **By channel:**
- **Constraints:** (e.g. no paid social, organic only)

## 8. Measurement plan
- **Tracking spec:** (UTMs, events, link to `utm-naming` skill)
- **Attribution model:**
- **Test design (if any):** link to `ab-test-design` skill

## 9. Dependencies & risks
- **Blocking dependencies:** (legal, product, brand, exec sign-off)
- **Risks + mitigations:**

## 10. Approvals
- [ ] Strategy lead
- [ ] Brand
- [ ] Legal (if claims/regulated)
- [ ] Exec sponsor
```

---

## Filling rules

1. **No adjectives in §1 or §3.** Replace "drive significant growth"
   with a number and a date.
2. **One primary KPI.** If you can't pick one, the campaign isn't
   focused enough yet.
3. **One single-minded proposition.** If it has an "and", split it.
4. **Three reasons to believe max.** More = none land.
5. **Every channel needs an owner agent and a deliverable list.** Not
   "social" — "3 LinkedIn posts + 1 thread + 6 X posts, owner: social-community".
6. **A campaign with no measurement plan is not a campaign.**

## Output

Save the filled brief to a project location the user designates (or
return it inline). Do not start production work until the human marks
status = `approved`.

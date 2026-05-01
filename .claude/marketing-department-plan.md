# Marketing Department — Agent Org Chart & Build Plan

A plan to stand up a marketing "department" inside Claude Code as a set of
specialized subagents plus the shared skills they all depend on. The goal:
ship campaigns, content, and analyses with the same rigor a real cross-
functional marketing team would, while keeping each agent's context
window narrow and its responsibility crisp.

---

## 1. Design principles

1. **One job per agent.** Each agent owns a single function (strategy,
   copy, design direction, SEO, etc.). The CMO orchestrates; ICs execute.
2. **Briefs in, deliverables out.** Every agent accepts a structured
   brief and returns a structured artifact (markdown, JSON, or a file
   path). No free-form back-and-forth as the contract.
3. **Shared skills, not duplicated prompts.** Brand voice, persona
   definitions, review checklists, and templates live in
   `.claude/skills/` so every agent reads the same source of truth.
4. **Human-in-the-loop gates.** CMO presents options; humans approve
   strategy, budget, and final external publishing.
5. **Traceability.** Every deliverable cites which brief, persona, and
   brand-voice version it was produced against.

---

## 2. Org chart

```
                       ┌──────────────┐
                       │     CMO      │  (orchestrator)
                       └──────┬───────┘
        ┌──────────────┬──────┴───────┬──────────────┬──────────────┐
        │              │              │              │              │
 ┌──────▼─────┐ ┌──────▼─────┐ ┌──────▼─────┐ ┌──────▼─────┐ ┌──────▼─────┐
 │  Brand &   │ │  Research  │ │  Creative  │ │  Growth /  │ │ Analytics  │
 │  Strategy  │ │ & Insights │ │  Director  │ │ Performance│ │  & Ops     │
 └──────┬─────┘ └──────┬─────┘ └──────┬─────┘ └──────┬─────┘ └──────┬─────┘
        │              │              │              │              │
        │              │   ┌──────────┼──────────┐   │              │
        │              │   │          │          │   │              │
        │              │ Copy-     Designer/   Video/ │              │
        │              │ writer    Art Dir    Motion │              │
        │              │                              │              │
        │              │                       ┌──────┼──────┐       │
        │              │                       │      │      │       │
        │              │                       SEO  Paid   Lifecycle │
        │              │                            Ads    / Email   │
        │              │                                              │
        └──────────────┴──── Social / Community ────── PR / Comms ────┘
```

---

## 3. Agent roster

### Tier 1 — Leadership & orchestration

| Agent | Owns | Inputs | Outputs |
|---|---|---|---|
| **cmo** | Goals, prioritization, routing, final QA | Business goal, budget, deadline | Campaign plan, agent assignments, go/no-go |

### Tier 2 — Strategy & insight

| Agent | Owns | Outputs |
|---|---|---|
| **brand-strategist** | Positioning, voice, narrative, messaging hierarchy | Brand brief, messaging matrix |
| **market-researcher** | Audience, ICP, JTBD, competitor landscape | Persona docs, competitor teardown, insight memo |
| **content-strategist** | Editorial calendar, content pillars, funnel mapping | Calendar, pillar plan, topic clusters |

### Tier 3 — Creative production (the user's "Creative" bucket, expanded)

| Agent | Owns | Outputs |
|---|---|---|
| **creative-director** | Big idea, creative brief, concept review | Creative brief, concept options, feedback |
| **copywriter** | Long & short-form copy, CTAs, headlines | Ad copy, landing pages, emails, scripts |
| **designer** *(art director)* | Visual direction, layout specs, asset prompts | Mood boards, layout specs, image-gen prompts |
| **video-motion** *(optional)* | Storyboards, scripts for video/motion | Storyboards, shot lists, VO scripts |

### Tier 4 — Channel & distribution

| Agent | Owns | Outputs |
|---|---|---|
| **seo-specialist** | Keyword research, on-page SEO, content briefs | Keyword maps, SEO briefs, audits |
| **paid-ads** | Search/social ad strategy, copy variants, targeting | Campaign structure, ad sets, copy variants |
| **lifecycle-email** | Email sequences, onboarding, retention | Sequences, subject lines, segmentation logic |
| **social-community** | Organic social, community engagement | Post packs, calendars, response templates |
| **pr-comms** | Press, exec comms, crisis messaging | Press release, pitch list, talking points |

### Tier 5 — Measurement

| Agent | Owns | Outputs |
|---|---|---|
| **marketing-analyst** | KPIs, A/B tests, post-mortems, dashboards | Test plans, readouts, weekly report |
| **mar-ops** | Tooling, tracking plan, UTM hygiene | Tracking spec, naming conventions |

**Minimum viable team (phase 1):** CMO, brand-strategist, market-researcher,
copywriter, creative-director, seo-specialist, marketing-analyst.
The rest are added in phase 2/3 as workload demands.

---

## 4. Shared skills (`.claude/skills/`)

Skills are reusable, agent-agnostic capabilities. Each is a folder with a
`SKILL.md` plus templates the agents reference.

| Skill | Purpose | Used by |
|---|---|---|
| **brand-voice** | Source of truth for tone, do/don't, style rules | all writers |
| **audience-personas** | Canonical persona definitions, JTBD | strategist, copy, ads, email |
| **campaign-brief** | Standard brief schema (goal, audience, message, channel, KPI) | CMO, creative, channel agents |
| **creative-brief** | Concept brief template + review rubric | creative-director, copy, design |
| **copy-review** | Checklist: clarity, specificity, CTA, voice match, length | copywriter, CMO QA |
| **seo-audit** | On-page SEO checklist, keyword mapping template | seo-specialist |
| **keyword-research** | Workflow for clustering, intent mapping | seo-specialist, content-strategist |
| **ab-test-design** | Hypothesis → metric → MDE → variants template | analyst, paid-ads, lifecycle |
| **landing-page-copy** | Wireframe-shaped copy doc (hero, social proof, FAQ, CTA) | copywriter, creative |
| **email-sequence** | Sequence outline (trigger, cadence, goal-per-step) | lifecycle-email |
| **social-post-pack** | Multi-platform post template (LI, X, IG, TT) | social-community, copy |
| **press-release** | AP-style release + boilerplate + pitch email | pr-comms |
| **competitor-analysis** | Teardown rubric (positioning, messaging, channels, gaps) | researcher, strategist |
| **content-calendar** | Calendar schema + cadence rules | content-strategist |
| **utm-naming** | UTM + campaign naming conventions | mar-ops, paid-ads, lifecycle |
| **analytics-readout** | Weekly/post-campaign report template | analyst, CMO |
| **launch-checklist** | Pre-launch QA: tracking, copy review, legal, accessibility | CMO, mar-ops |

Skills are invoked by name from agent prompts and via the `Skill` tool when
the user types a slash command (e.g. `/campaign-brief`).

---

## 5. Standard workflow (campaign example)

1. **Intake** — user gives CMO a goal ("launch feature X to SMBs in Q2").
2. **Brief** — CMO opens `campaign-brief` skill, fills it with help from
   `market-researcher` and `brand-strategist`. Human approves.
3. **Concept** — `creative-director` produces 2–3 concepts using
   `creative-brief`. CMO + human pick one.
4. **Production** — in parallel: `copywriter` drafts copy,
   `designer` drafts visual direction, `seo-specialist` supplies briefs
   for any content pieces.
5. **Channel adaptation** — `paid-ads`, `lifecycle-email`,
   `social-community`, `pr-comms` each take the approved concept and
   produce channel-native deliverables.
6. **Pre-flight** — CMO runs `launch-checklist` and `copy-review`. Human
   approves external publish.
7. **Measurement** — `marketing-analyst` defines test, builds readout
   from `analytics-readout` skill at +1w, +4w.
8. **Retro** — CMO compiles wins/losses; updates skills (voice, persona,
   playbook) so the team gets sharper each cycle.

---

## 6. File layout

```
.claude/
├── agents/
│   ├── cmo.md
│   ├── brand-strategist.md
│   ├── market-researcher.md
│   ├── content-strategist.md
│   ├── creative-director.md
│   ├── copywriter.md
│   ├── designer.md
│   ├── video-motion.md
│   ├── seo-specialist.md
│   ├── paid-ads.md
│   ├── lifecycle-email.md
│   ├── social-community.md
│   ├── pr-comms.md
│   ├── marketing-analyst.md
│   └── mar-ops.md
├── skills/
│   ├── brand-voice/SKILL.md
│   ├── audience-personas/SKILL.md
│   ├── campaign-brief/SKILL.md
│   ├── creative-brief/SKILL.md
│   ├── copy-review/SKILL.md
│   ├── seo-audit/SKILL.md
│   ├── keyword-research/SKILL.md
│   ├── ab-test-design/SKILL.md
│   ├── landing-page-copy/SKILL.md
│   ├── email-sequence/SKILL.md
│   ├── social-post-pack/SKILL.md
│   ├── press-release/SKILL.md
│   ├── competitor-analysis/SKILL.md
│   ├── content-calendar/SKILL.md
│   ├── utm-naming/SKILL.md
│   ├── analytics-readout/SKILL.md
│   └── launch-checklist/SKILL.md
└── marketing-department-plan.md   ← this file
```

Each `agents/<name>.md` follows Claude Code's subagent format: YAML
frontmatter (`name`, `description`, `tools`, optional `model`) plus the
system prompt body. `description` should be written in third person and
include trigger phrases so the CMO routes correctly.

---

## 7. Build phases

**Phase 1 — Skeleton (1 sitting):**
- Create `.claude/agents/` and `.claude/skills/` folders.
- Ship Tier 1 + Tier 2 agents and the 5 core skills (`brand-voice`,
  `audience-personas`, `campaign-brief`, `creative-brief`, `copy-review`).

**Phase 2 — Production crew:**
- Add `copywriter`, `creative-director`, `designer`, `seo-specialist`,
  `marketing-analyst`.
- Add `landing-page-copy`, `seo-audit`, `keyword-research`,
  `ab-test-design`, `analytics-readout` skills.

**Phase 3 — Channel depth:**
- Add `paid-ads`, `lifecycle-email`, `social-community`, `pr-comms`,
  `mar-ops`, `video-motion`.
- Add remaining skills (`social-post-pack`, `email-sequence`,
  `press-release`, `competitor-analysis`, `content-calendar`,
  `utm-naming`, `launch-checklist`).

**Phase 4 — Tune & specialize:**
- Fill `brand-voice` and `audience-personas` with real, project-specific
  content (this is what makes outputs stop sounding generic).
- Add localization variants if needed.
- Wire slash commands for the most-used skills.

---

## 8. Open decisions for the user

1. **Brand inputs.** Do you have an existing brand voice / persona doc
   to seed `brand-voice` and `audience-personas`? Without these the team
   will produce competent-but-generic work.
2. **Scope.** B2B, B2C, or both? Determines which channel agents are
   priority (e.g. lifecycle-email + paid-ads heavy for B2C; pr-comms +
   content-strategist heavy for B2B).
3. **Tooling integrations.** Should `marketing-analyst` and `mar-ops`
   assume access to GA4, Segment, HubSpot, etc.? If yes we'll add MCP /
   tool permissions.
4. **Approval gates.** Which steps require human sign-off vs. autonomous
   execution? Default proposal: human approves brief, concept, and any
   external publish.
5. **Model assignment.** Heavy-reasoning roles (CMO, strategist,
   analyst) on Opus; production roles (copy, social, email) on Sonnet;
   high-volume formatting (utm-naming, calendar) on Haiku.

---

## 9. Next step

If this plan looks right, the immediate next action is Phase 1: scaffold
folders and ship the seven Tier 1+2 agents and five core skills. Say the
word and I'll build it on this branch.

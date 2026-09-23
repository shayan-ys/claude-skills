---
name: product-research
description: Buying-decision research for physical products, prioritizing long-term health and safety for anything that touches the body, food, skin, lungs, or sleep. Researches distinct angles in parallel (peer-reviewed literature, independent lab testing, multi-year owner reports, regulation) and distrusts labels, marketing claims ("BPA-free", "non-toxic", "natural"), and affiliate review sites. Use whenever the user is deciding what to buy and will use it repeatedly: cookware, mattresses, water bottles, supplements, sunscreen, deodorant, baby gear, food storage, air purifiers, appliances, fabrics, paint, furniture. Trigger without the word "research": "thinking about getting X", "what's the best Y", "is Z safe", "should I worry about W", "A vs B".
---

# Product Research

Most product-research questions fall into one of two failure modes when answered casually: (1) the answer parrots the brand's marketing, or (2) the answer cites Wirecutter and stops. Neither catches the things that matter for products you use for years — coatings that degrade, materials that leach, replacement chemicals that are nearly as bad as what they replaced, manufacturing batches that fail QC, real-world failure modes that only show up at year three.

This skill is the workflow for doing it properly. The core move is researching several *distinct angles* in parallel (subagents where the harness supports them), then synthesizing their neutral surveys into an opinionated recommendation. Use it whenever the user is making a purchase decision — especially when the product touches their body, their food, the air they breathe, or where they sleep.

## When this matters most

The diligence ramps up sharply for anything in long-term contact with the user. Treat these as **high-priority health research**:

- **Cookware** — coatings, leaching, off-gassing, manufacturing contaminants
- **Food storage** — plastics, lids, can linings, silicone bakeware
- **Skin contact** — sunscreen, deodorant, lotions, makeup, fabric dyes, laundry detergent
- **Sleep** — mattresses, pillows, sheets (off-gassing, fire retardants, microplastics)
- **Air** — air purifiers, HVAC filters, paint, candles, plug-ins
- **Drinking** — water bottles, filters, kettles
- **Baby/child** — anything they put in their mouth or sleep on
- **Supplements & ingestibles** — what's actually in them, contamination, third-party testing

Lower-priority for health-research depth (but the rest of the workflow still applies):

- Electronics, tools, software, durable goods that don't contact the body for hours

## Core workflow

### 1. Triage the request

Before spawning anything, get clear on:

- **What product category?** Be specific — "non-stick pan" vs "carbon steel pan" leads to different research.
- **Health-priority?** If yes, the toxicology angle is mandatory.
- **Budget tier?** Open-ended, value-conscious, or premium? Affects which contenders are in scope.
- **Geographic context?** Country/region affects pricing, availability, and regulatory environment.
- **Existing constraints?** Dietary, allergies, induction stovetop, small apartment, etc.

If 2+ of these are missing and the answer changes meaningfully based on them, ask once, offering short answer choices. Otherwise proceed with reasonable assumptions and flag them in the output.

### 2. Fan out by research angle

The lead triages, fans out, and synthesizes. The searching, fetching, literature digs, forum trawls, and price checks happen per angle, one angle at a time in isolation, so no single pass drifts into a generic "best X" summary.

- **Harness with subagents:** spawn one subagent per angle, all in parallel in one step. Pick a cheaper, faster model for them if your harness lets you choose. Do not do the research in the lead context; that bloats it with raw search output.
- **Harness without subagents** (for example a chat app): research each angle as its own focused pass, write that angle's neutral survey, then move to the next. Keep the passes separate; do not merge angles while researching.

The default for a health-priority product is 3–4 angles, each distinct and non-overlapping. This is the most important step.

**Standard angles for health-priority products:**

1. **Health & toxicology** — peer-reviewed evidence on the materials/chemicals involved. PubMed, NIH, ScienceDirect, EPA, FDA, EWG. What's the actual current science? What's settled vs speculative? What changed recently (regulations, replacement chemicals)?

2. **Manufacturing & contaminants** — independent third-party testing data. Tamara Rubin / Lead Safe Mama (XRF heavy-metal testing), Mamavation, Ecology Center, Consumer Reports lab reports. Country-of-origin patterns. Recent recalls, FDA import alerts, state-level bans.

3. **Long-term real-world reports** — multi-year owner experiences, NOT initial reviews. r/BuyItForLife, r/[category-specific subreddits], Hungry Onion / Chowhound archives, eGullet, forum threads with 5+ year follow-ups, Amazon reviews sorted by recent verified purchase. Focus on failure modes: what breaks, when, and how often.

4. **Expert reviewer consensus** — Wirecutter, America's Test Kitchen, Serious Eats, Consumer Reports, category-specific authorities. What do the trusted reviewers actually pick, and where do they disagree? Note the dissenters (often EWG takes a harder line than mainstream reviewers — both perspectives matter).

**Optional 5th angle** when relevant:

- **Pricing & availability** for the user's region — real local prices, retailers, sale patterns, customs/tariff issues for imports.

For non-health products, drop angle 1 and keep the other three. If the product is purely commodity (a USB cable, a stapler), the whole skill is overkill — just answer directly.

### 3. The per-angle brief

Each angle gets a focused brief with these elements:

- **The angle they own** (one of the four above)
- **The specific product category and subcategory**
- **Source hierarchy** (see below)
- **What to distrust** (brand pages, "non-toxic" labels, retailer-funded review sites)
- **Output format expected** — markdown, ~400–600 words, hyperlinked sources, tight verdict at the end

State explicitly in each brief: *"Cite peer-reviewed and primary sources. Distinguish settled science from speculation. Flag where the literature has gaps. Hyperlink everything you reference."*

Each angle produces a **neutral survey**, not opinionated synthesis. The lead does the synthesis.

### 4. Source hierarchy (what to trust)

Put this hierarchy in every brief and follow it yourself:

| Tier | Source type | Examples |
|---|---|---|
| 1 | Peer-reviewed primary literature | PubMed, ScienceDirect, NIH/PMC, JAFC, Frontiers, journal DOIs |
| 2 | Government/regulatory | FDA, EPA, Health Canada, EU EFSA, state-level bans/regulations |
| 3 | Independent third-party testing | Tamara Rubin (XRF), Mamavation, Ecology Center, Consumer Reports labs |
| 4 | Independent expert reviewers | Wirecutter, ATK, Serious Eats, EWG (notes harder-line view) |
| 5 | Multi-year owner reports | BuyItForLife forums, category subreddits, long-tenure forum threads |
| 6 | Brand marketing & product labels | **Distrust by default**, especially "PFOA-free", "BPA-free", "non-toxic", "natural", "organic" |
| 7 | Affiliate-driven review sites | Look for the disclosure; treat as marketing-adjacent |

A claim only present in tier 6–7 is suspect. A claim consistent across tiers 1–4 is robust.

### 5. Distrust patterns specific to health claims

Watch for these red flags in product marketing — these are the patterns that history has repeatedly shown to be misleading:

- **"X-free"** without saying what replaced X. PFOA-free PTFE → GenX (nearly as toxic per EPA). BPA-free plastic → BPS (similar endocrine disruption). The substitution is often a regrettable one.
- **"Non-toxic"** is unregulated. Sol-gel ceramic cookware uses this; independent testing has found titanium dioxide nanoparticles (banned for food contact in EU).
- **"Natural" / "organic"** on non-food products generally has no enforced meaning.
- **"Tested for safety"** without saying tested by whom, against what standard, with what threshold.
- **Country-of-origin** matters more than brands admit. FDA import alerts, EU recalls, and independent testing repeatedly catch contamination concentrated in specific source countries.
- **Recently reformulated** products are under-studied. The replacement chemistry's long-term effects are often not yet characterized.
- **Settled science vs current science** — a "PFOA-free" pan from 2014 is not the same as one from 2024; regulations and chemistry shift fast.

### 6. Long-term use focus

For anything you'll use for years, prioritize evidence about *years 3–10*, not the first month:

- Search for "X years later" reviews, follow-ups, BuyItForLife threads
- Look for the specific failure modes of the category (warping for cookware, off-gassing for mattresses, coating degradation for non-stick, gasket failure for water bottles, etc.)
- Identify the **diminishing-returns point** on price — where does spending more stop buying meaningful longevity or performance?
- Identify the **cliff** — the cheapest price below which the product fails fast

### 7. Synthesis (the lead's job)

After the angles are done, the lead writes the opinionated recommendation. The synthesis should:

- Lead with a one-line verdict ("buy X at \~\$Y")
- Show the diminishing-returns curve as a table when there's a price spectrum
- Cite the neutral surveys via reference, don't re-paste their content
- Be honest about confidence levels — flag where the evidence is genuinely thin
- Address the user's specific constraints (region, budget, allergies)
- Identify what *not* to buy and why
- Give practical buying tips (timing, retailer choice, sale patterns) only if researched

**Do not** overstate certainty. Health-research evidence is often genuinely contested; your job is to communicate the state of the evidence honestly, not to manufacture confidence.

## Output formatting

Match the format to the user's surface:

- **Conversational reply** when the user just asked a question. Concise, scannable, hyperlinked. The carbon-steel-pan synthesis (in their wiki) is a good model.
- **Wiki note** when the user has an Obsidian vault and the topic deserves persistence. Follow your vault's conventions doc (`AGENTS.md` or `CLAUDE.md` at the vault root) research/synthesis split: neutral surveys go in `${user_config.resourcesBase}/Research/<topic>/` as separate notes; opinionated synthesis goes in a sibling top-level note that links to them.
- **Both** when the user explicitly asks to save research alongside getting an answer.

## Example shapes

**Good trigger phrases:**

- "thinking of getting a new mattress, anything I should worry about?"
- "what cookware should I use to avoid PFAS?"
- "is the Stanley Cup actually safe? heard something about lead"
- "looking at sunscreens — Korean vs American, which is better?"
- "should I switch to glass food containers?"
- "best water filter for my apartment?"
- "comparing these two air purifiers"
- "is X brand worth the premium?"

**Should NOT trigger:**

- "what does PFAS stand for" (info question, not a buying decision)
- "fix my Python script"
- "summarize this article"

## Common failure modes to avoid

- **Blending angles** into one pass instead of researching each separately. The lead synthesizes; the angles research.
- **Spawning subagents one after another** when the harness can run them in parallel. Defeats the speed benefit.
- **Angles that overlap** — they all return the same Wirecutter summary.
- **Citing brand pages or affiliate reviews as primary evidence**.
- **Treating "PFOA-free" or "BPA-free" as a clean bill of health** instead of asking what replaced it.
- **Ignoring the user's region** when pricing/availability matters (Canadian buyer, US prices = useless).
- **Manufacturing confidence** when the literature is genuinely contested. It's OK to say "the evidence is mixed and here's why."
- **Skipping the long-term-use angle** because initial reviews are uniformly positive.
- **Recommending the most expensive option as "the best"** without showing the diminishing-returns curve.

## Why this works

Products are bought on first impressions; they're lived with for years. The research workflow most people use (search "best X" → read top result) optimizes for the first impression and ignores the years. This skill inverts that. The fan-out into separate angles is what makes the depth tractable — without it, the lead either does shallow research or burns hours and tokens going deep alone. With it, you get four independent expert lenses on the question in roughly the time of one, and the synthesis is genuinely informed rather than parroted.

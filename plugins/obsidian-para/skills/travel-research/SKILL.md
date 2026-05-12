---
name: travel-research
description: "Interactive travel-planning companion — triages booked vs research-needed, uses Google Maps MCP and parallel sonnet/haiku teammates to build curated Ideas.md + Findings notes under ${WIKI_ROOT}/${TRIPS_BASE}/. Triggers on trip planning (place names plus weekend/getaway/etc.), vague asks like Elora/Montreal, ratings/reviews, or mentions of an existing trips folder."
argument-hint: "<Destination?>"
---

# Travel Research — Interactive

This skill is a **conversation**, not a one-shot research dump. The core insight: most trip-planning effort is wasted researching things the user already decided. Triage first, research second, synthesize third.

The skill runs four phases: **Discover → Triage → Confirm → Research**. At each boundary the user can redirect — don't race ahead.

_Concrete trip examples below (e.g. Montreal, Quebec City, Toronto) are the author's own — illustrative vignettes about planning lessons, not assumptions about your vault. Replace with your own past-trip lessons in your fork._

The output lives in your vault at `${WIKI_ROOT}/${TRIPS_BASE}/<Destination>/`. All notes follow `${WIKI_ROOT}/CLAUDE.md` — your vault's conventions doc, if present — (frontmatter, wikilinks, mobile formatting, lead paragraphs, index updates).

## Phase 0 — Discover existing work

Before asking anything, do two reads in parallel:

1. **Destination-specific work** — read `${WIKI_ROOT}/${TRIPS_BASE}/<Destination>/Ideas.md` if it exists. The **Trip Context** block at the top is machine-readable state from a prior run.

2. **Past trip diaries** — Glob `${WIKI_ROOT}/${TRIPS_BASE}/*Diary*.md` (or the equivalent in the user's vault) and read the most recent 1-2. The `## Takeaways for Future Trips` section in those notes is the user's lived lessons-learned ledger; fold those into the current trip's planning so mistakes don't compound. Example: the Apr 2026 Montreal-Quebec diary surfaces "Uber unreliable outside Toronto," "VIA economy food runs out," "Plan B for blown days," and "verify shoulder-season hours by phone" — all of which become defaults below.

**If the destination Ideas.md exists:** parse the Trip Context, then show a short menu instead of re-triaging:

```
I already have research for <Destination>:
- Dates: <...>   Transport: <booked/TBD>   Lodging: <booked/TBD>
- Categories covered: <...>

What now?
1. Fill gaps (items still TBD, or weather was deferred)
2. Deepen a category (add more picks or review detail)
3. Build / refine day-by-day itinerary
4. Add a specific request (e.g. "find a rainy-day backup")
5. Start over
```

Wait for a reply before doing any research. Re-triage only the fields the user wants to change.

## Phase 1 — Triage (single compact message)

If no prior work exists, ask **one** message containing the checklist below. The user fills in what they know and leaves gaps blank — don't machine-gun them one question at a time.

```
Before I dive in, quick triage. Answer what you know, leave the rest blank:

1. Destination + region/country (confirm)
2. Dates — arrival / departure (or "~N nights in <month>" if flexible)
3. Transport — booked (arrival/departure times), not booked (research needed),
   driving from Toronto, or flexible
4. Lodging — booked (address/neighbourhood), not booked (recommend areas),
   or flexible
5. Trip vibe — one-liner (relaxed food trip / packed sightseeing / adventure /
   anniversary / etc.)
6. Known must-dos or existing bookings (reservations, tickets)
7. Constraints — budget level, dietary, mobility, allergies
8. Layovers / transfers — any 1-3 hr layovers on the route? (those need a
   single planned thing near the station, not a guess on the day)
```

**Interpretation rules:**
- Default to couples-friendly framing when trip context implies paired travel unless the user says otherwise (prefer asking once if ambiguity remains).
- Based near Toronto — if transport is blank and the destination is drivable, assume driving and confirm.
- If `vibe` is blank, infer from destination + duration (Kyoto weekend ≠ Kyoto week; both ≠ Algonquin cabin weekend).

## Phase 2 — Confirmation gate

Before any Maps call or teammate spawn, restate the plan in 4-6 lines and ask "go?":

```
Plan:
- Research: dinner, brunch/cafes, scenic walks, museums  (skipping: shopping — you said no interest)
- Anchored to: <stay address> — distances will show walk/transit from there
- Weather: ✅ forecast included (trip is 8 days out)
- Teammates: sonnet × 2 (dining, activities) in parallel
- Estimated ~15 Maps calls

Go, or tweak anything first?
```

This is the last chance to catch misread triage answers ("oh, also vegetarian") before burning tool calls. Do not skip this gate.

## Phase 3 — Research

Scale scope to trip length:

- **Day trip (1 day):** 2-3 categories, single-day itinerary
- **Weekend (2-3 nights):** all relevant categories, meal-period itinerary (Friday dinner / Saturday brunch / etc.)
- **Multi-day (4+ nights):** all categories but curate hard — 4 excellent picks beat 10 mediocre ones

### Universal research add-ons (always include)

Some categories consistently show up in post-trip diaries as "we should have planned this." Default-include them on every multi-night trip even if the user didn't ask. These are short — a few minutes each — but cumulatively they save days.

**Plan B for a blown day.** Mandatory on any 2+ night trip. Cold weather, illness, exhaustion, or a flat tire will eat at least one day on a real trip — pre-plan for it. Research:

- 2-3 nearby food-delivery options (Uber Eats / DoorDash / direct + a nearby grocery with prepared food); confirm they actually deliver to the stay address
- 1 indoor activity within 15-min walk (spa, museum, café-with-couches, indie cinema)
- Note streaming-service availability or Wi-Fi quality for the stay if known

File as a "Plan B" callout in Ideas.md, not slotted into the itinerary. Real-world: the Apr 2026 Montreal–Quebec trip lost a full Quebec City day to no Plan B — a concrete lesson-from-the-road that drove this checklist.

**Transit-pass options** — if the destination has a metro/subway/tram:

- Cost of single fare vs. 24-hour vs. 3-day vs. trip-length pass
- Where to buy and accepted payment methods (some systems are tap-card only; verify the user's contactless/credit card works — Montreal STM accepts NFC, some don't)
- One bullet in Ideas.md (e.g. "STM 3-Day Pass — \$22, vending machines at any Metro station, NFC accepted")

**Rail / long-flight legs in economy** — if any leg is economy and >3 hr:

- Add an Open TODO: "Buy real food at \<departure station\> before boarding" (VIA economy hot meals run out)
- Recommend the Business class upgrade if available — specifically flag Toronto–Montreal–Quebec VIA where ~\$30/pp gets a hot meal, free drinks, and real seating
- Build a 90-min buffer into any tight connection after a VIA leg — delays >60 min are routine

**Layovers in the 1-3 hr band** — at any transit hub on the route:

- Use `maps_search_nearby` from the station coords with a walking radius of ≤15 min
- Identify ONE thing (mall food court, café, viewpoint) — confirm hours match the layover window
- Note the transit-area safety profile (Reddit / city subreddit) — flag if the station area is known sketchy
- Set a hard turn-around time and pad with 15 min

**Ride-share reliability** — for any non-Toronto Canadian city (and many mid-size cities anywhere):

- Default assumption: Uber matches are slower and Uber Eats is significantly slower than the user's home baseline
- Add a local taxi-dispatch number to Ideas.md
- Add an Open TODO: "Pre-book ride-share or taxi the night before for any tight train/flight departure"

**Pre-trip gear check** — when the weather forecast shows rain, snow, wind, or cold:

- Add an Open TODO listing specific gear (waterproof boots, warm layers, real windbreaker, gloves)
- Belvedere / cliff / waterfront viewpoints are reliably 3-5 °C colder and significantly windier than the city below; call this out for any windy-day itinerary item

### Delegation policy

- **Lead (coordinating model)** keeps: map geometry (routing, neighbourhood clustering, distance anchoring), weather, arrival logistics, final synthesis, Ideas.md writing, index updates.
- **Sonnet teammates** do: any category that needs 3+ Maps calls plus judgment. Spawn in parallel. Every `TeamCreate` / `Agent` call MUST pass `model: "sonnet"` explicitly.
- **Haiku teammate** (orchestrator discretion) for dead-simple single-shot lookups with no judgment involved: "current hours for X", "is this place open Sundays", "confirm address." Haiku has no auto-mode, so pre-approve the single turn in the spawn prompt.
- **Never** spawn Opus teammates without explicit user approval.

**When to spawn a teammate for web research (not just Maps):** neighbourhood safety, recent restaurant sentiment, "still good?" signal. The sonnet teammate uses WebSearch / WebFetch for Reddit threads (`r/travel`, city subreddits), crime maps, police-report summaries, and travel forums. Include source URLs in the teammate's return so they show up in the Findings note (${WIKI_ROOT}/CLAUDE.md → "External URL Rule" section, if documented there).

### Standard teammate pattern

```
TeamCreate(team_name="trip-<destination>-<YYYYMMDD>")
Agent(team_name=..., name="dining-researcher", model="sonnet",
      subagent_type="general-purpose",
      prompt="Research dinner + brunch/cafes in <dest>. Use maps_search_places
              and maps_place_details. For top picks, check Reddit / forums for
              recent sentiment. Return 4-6 top picks per category with
              place_id, rating, vibe one-liner, phone, any gotchas. Do NOT
              write files — hand the structured list back to me.")
```

Two rules for teammates:
1. They return **structured data**, not prose, and do NOT write vault markdown files themselves. The lead writes everything.
2. They never edit existing notes. No backlinks, no cross-references.

Shut down the team when done.

### Google Maps MCP usage

All tools are prefixed `mcp__google-maps__maps_*`.

**`maps_search_places`** — category discovery. Natural-language query scoped to the destination ("best dinner restaurants in Gion Kyoto"). Optional `locationBias` to tighten, `minRating` to pre-filter. Collect `place_id`, `name`, `rating`, `total_ratings`.

**`maps_place_details`** — deep-dive top candidates. Pass `maxPhotos: 0` unless photos are requested. Returns reviews, hours, phone, website, editorial summary.

**`maps_search_nearby`** — clustering around a standout (dessert bar near dinner spot, cafe near morning activity).

**`maps_distance_matrix`** — **anchor clustering**. Once lodging is known, call with `origins: [<stay-coords>]`, `destinations: [<all-recommended-places>]`, `mode: "walking"` and/or `"transit"`. Each Findings note and the Ideas.md table should show "X min walk / Y min transit from stay." Supports batch, so one or two calls cover all picks.

**`maps_directions`** — specific leg detail. For arrival/departure, use `mode: "transit"` with `departure_time` set. Returns text steps — **note that last-train times and transfer details are not structured fields**; if the user needs hard last-train guarantees, flag "verify on transit app (Google Maps / Citymapper)" rather than promising.

**`maps_plan_route`** — **day routing**. Given the day's stops, optimize order. **Caveat: `optimize: true` is disabled for transit mode.** Workaround: run optimization with `mode: "walking"` (or driving), then fetch per-leg directions in the actual mode the user will take. Up to 25 intermediate stops.

**`maps_search_along_route`** — coffee / rest stops for long drives.

**`maps_explore_area`** — area overview for unfamiliar destinations. Use for neighbourhood selection — feed a **specific neighbourhood name** ("Gion, Kyoto"), not a bare city name (docs warn this clusters poorly).

**`maps_weather`** — per-day forecast. **Forecast caps at 10 days.** If the trip is more than 10 days out, skip this step and add to `## Open TODOs` in Ideas.md: "re-run weather step closer to trip (forecast was out of range)." For trips <10 days out, pull weather per-day and let it inform the itinerary (indoor picks on rainy days).

### Neighbourhood selection (when lodging is TBD)

Spawn a sonnet `neighbourhood-scout` teammate:

```
Agent(team_name=..., name="neighbourhood-scout", model="sonnet",
      subagent_type="general-purpose",
      prompt="User is planning a <vibe> trip to <destination> for <dates>,
              lodging not booked yet. Recommend 2-3 neighbourhoods.
              For each: use maps_explore_area + maps_search_nearby for
              amenity density and walkability. Use WebSearch for safety
              signal — Reddit (r/travel, r/<city>), crime maps, travel
              forums. Return: name, vibe, walkability, safety summary
              with source URLs, rough price tier, pros/cons for <vibe>.
              Don't write files.")
```

The lead then presents the 2-3 options in chat, user picks, and the rest of the research anchors to that choice.

### Research quality checks

- **Drop** places where recent reviews show quality decline (even if overall rating is still OK)
- **Flag** practical gotchas: cash-only, closes early, reservations required, deceptive entrances, seasonal hours
- **Prefer** newer high-rated spots over legacy declining ones
- **Seasonal opportunities** — anything only available this month? (festival, trail opening, seasonal menu, outdoor terrace) Flag as a highlight.
- **Shoulder-season smaller cities** (e.g. Quebec City in May, Halifax in October): treat Google Maps hours as unreliable for top picks. Mark them with "📞 verify by phone on the day" if the itinerary depends on them being open.
- **Michelin labels matter** — distinguish "Michelin star," "Bib Gourmand," and "Michelin Guide listed." Users routinely round all three up to "Michelin-starred"; be precise so the expectation matches the actual experience.

## Phase 4 — Write Ideas.md

Create `${WIKI_ROOT}/${TRIPS_BASE}/<Destination>/Ideas.md`. The **Trip Context** block at the top is the source of truth for re-invocations — keep it machine-parseable.

```markdown
---
title: "<Destination> Trip Ideas"
type: project
tags:
  - travel
  - <destination-tag>
status: growing
created: <today YYYY-MM-DD>
updated: <today YYYY-MM-DD>
summary: "Couples trip to <Destination>, <dates> — restaurants, activities, and itinerary."
related:
  - "[[Well Travelled]]"
source: "original"
aliases: ["<Destination> trip", "<Destination> getaway"]
---
# <Destination> Trip Ideas

A curated research document for a couples getaway to <Destination>. Covers restaurants, cafes, activities, scenic walks, and a day-by-day itinerary built from Google Maps data, web sentiment, and real reviews.

## Trip Context
<!-- Machine-readable — the skill re-reads this on next invocation. Keep fields even if empty. -->
- **Destination:** <Kyoto, Japan>
- **Dates:** <2026-05-02 → 2026-05-05 (3 nights)>
- **Transport:** <✅ Booked — NRT→KIX JAL arriving 14:20 2026-05-02; return 2026-05-05 19:00>  <!-- or: ⏳ TBD — research needed -->
- **Lodging:** <✅ Booked — [Hotel Name], Gion district, 35.003,135.778>  <!-- or: ⏳ TBD -->
- **Vibe:** <Relaxed + food-focused, first trip to Japan>
- **Must-dos:** <Fushimi Inari at dawn; one kaiseki dinner>
- **Constraints:** <No dietary; moderate walking OK>
- **Open TODOs:**
  - <e.g. "book kaiseki reservation for Friday">
  - <e.g. "re-run weather step — trip is >10 days out">

---

## Weather at a Glance
<!-- If trip is within 10 days: per-day table. Otherwise: note "Forecast will be available closer to the trip — see Open TODOs." -->

---

## <Meal Period> — <Meal Type>

> [!tip] Top Pick: **Name** — one-line reason

| Name | Vibe / Info | From stay | Rating | Phone |
|------|-------------|-----------|--------|-------|
| **Top pick** | ... | 8m walk | [★ 4.6 (312)](https://www.google.com/maps/search/?api=1&query=NAME&query_place_id=PLACE_ID) | (xxx) xxx-xxxx |
| Backup | ... | 14m walk | [★ 4.4 (180)](...) | — |

> [!info]- Review Highlights — Top Pick
> - "quote" — reviewer
> - "quote" — reviewer

**Best plan:** concrete recommendation — which to book, when, what to order.

---

## Getting There & Back
<!-- Only if transport details are known. Use maps_directions with transit/driving mode. -->

| Leg | Mode | Time | Notes |
|-----|------|------|-------|
| Airport → stay | Transit | 52 min | Haruka express to Kyoto Stn, 5 min walk |
| Stay → airport | Transit | 60 min | Leave by 16:00 for 19:00 flight |

> [!warning] Last-train times not guaranteed by Maps API — verify in Google Maps app on the day.

---

## Things to Do
### Scenic Walks / Nature
### Activities
### Museums & Culture
### Shopping (optional)

---

## Suggested Itinerary

### <Day> <Date> — <Theme>
<!-- If day-routing was optimized, note it. Include per-leg walk/transit time. -->

| Time | Activity | Note |
|------|----------|------|
| 9:00 | Brunch at X | 8m walk from stay |
| 10:30 | Walk to Y park | 15m walk |

---

## Detailed Research
- [[<Destination> — Dinner Restaurants]]
- [[<Destination> — Cafes and Brunch]]
- (etc.)
```

### Table format rules

- **Max 4 columns** for most tables (mobile). The restaurant table's 5-column format (with Phone) is the one exception.
- **Escape price-tier dollar signs:** write `\$\$` and `\$\$\$`, never `$$` / `$$$` — Obsidian treats bare `$...$` as MathJax and misrenders the line.
- **Rating column** always hyperlinks to Google Maps: `[★ X.X (N)](https://www.google.com/maps/search/?api=1&query=PLACE+NAME&query_place_id=PLACE_ID)` — URL-encode the name with `+`.

### Place hyperlinking rule (load-bearing)

Every concrete place you mention anywhere in any trip note — restaurants, cafes, bars, museums, parks, viewpoints, streets to stroll, transit stations, neighborhoods worth wandering — **MUST be hyperlinked to its Google Maps URL**. This applies to prose, callouts, itinerary tables, and the "Things to Do" sections — not just rating columns.

Format: `[Place Name](https://www.google.com/maps/search/?api=1&query=PLACE+NAME&query_place_id=PLACE_ID)`

Use the `mcp__google-maps__maps_search_places` or `mcp__google-maps__maps_place_details` tools to obtain the correct `place_id` for each place, then build the URL. For streets and strolls where there is no single place_id, link a representative drop-pin or starting-point: `https://www.google.com/maps/search/?api=1&query=Rue+Saint-Denis+Montreal`.

**Skip linking only for** generic geographic region labels used as context (e.g. "Old Town" appearing as a neighbourhood descriptor, not a named destination you're recommending). If it's a destination the user might navigate to, link it.

This rule is consistent with `${WIKI_ROOT}/CLAUDE.md` → "Google Maps Place Rule". Both must stay in sync if that section exists.
- **Distance column** ("From stay") shows walk time if under 20 min, otherwise transit time; omit the column entirely if lodging is TBD.
- **Phone column**: include for places that have one; use `—` if not.
- Collapsible `> [!info]-` for review summaries (keeps the note scannable).
- `> [!tip]` for top picks, max 2-3 per note.
- `> [!warning]` for gotchas (weather, closures, reservations, access quirks).
- Short paragraphs — max 4-5 sentences. The human reads this on their phone.

## Phase 5 — Findings notes

For each category, create a Findings note in the same folder (not a subfolder): `${WIKI_ROOT}/${TRIPS_BASE}/<Destination>/<Destination> — <Category>.md`. These carry the raw detail: address, hours, phone, website, menu highlights, full review excerpts, web sentiment with source URLs, practical tips.

```yaml
---
title: "<Destination> — Dinner Restaurants"
type: research
tags:
  - travel
  - <destination-tag>
status: seed
created: <today YYYY-MM-DD>
updated: <today YYYY-MM-DD>
summary: "Detailed restaurant research for <Destination> trip."
related:
  - "[[<Destination> Trip Ideas]]"
source: "original"
aliases: []
---
```

Link all Findings notes from Ideas.md under `## Detailed Research`.

## Phase 6 — Update indexes

1. `${WIKI_ROOT}/02-Projects/_index.md` — add entries for every new note, alphabetical.
2. `${WIKI_ROOT}/${TRIPS_BASE}/_index.md` — create if missing, per `${WIKI_ROOT}/CLAUDE.md` index format.

## Phase 7 — Summary

Brief report back to the user:
- Top dinner pick + why
- Top brunch/cafe + why
- Must-do activity or walk
- Arrival/departure logistics summary
- Seasonal opportunities or surprising finds
- Key warnings (book ahead, cash-only, limited hours)
- **Plan B summary** — one-liner reminding the user there's a delivery + indoor backup planned for a blown day
- **Recovery buffer** — if the trip ends with a long travel day (>4 hr rail or any flight), flag "avoid commitments the morning after return." Long economy rail + delays + tired bodies is rough.
- **Open TODOs** — things the user or a future run still needs to handle (book X, verify weather closer to trip, pre-book taxi for departure morning, gear check, etc.)

## Out of scope (future phases)

Not attempted today, recorded as Open TODOs:
- Flight / transport search and booking (no flight MCP yet)
- Lodging search and booking (no lodging MCP yet)
- Restaurant reservation booking

When the user asks for any of these, record the need in the Trip Context's Open TODOs and tell the user it's a manual step for now.

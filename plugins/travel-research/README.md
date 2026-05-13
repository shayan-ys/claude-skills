# travel-research

A Claude Code skill for interactive trip planning. Triages what's already booked (transport, stay, must-dos) before researching anything, then spawns parallel sonnet teammates against the Google Maps MCP to build a curated `Ideas.md` plus per-category Findings notes.

The skill writes its output into an [Obsidian](https://obsidian.md) vault organized by [PARA](https://fortelabs.com/blog/para/). If you don't use Obsidian, the markdown still works — you just won't get the wikilink graph.

## Install

    /plugin install travel-research@shayan-ys

Then **fork or copy** and replace the placeholders documented in [config.example.md](./config.example.md). At minimum: `${WIKI_ROOT}` and `${TRIPS_BASE}`.

## What it does

- **Discover** — reads any prior research for the destination and your most recent trip diaries so past lessons compound.
- **Triage** — one compact message gathers dates, transport, lodging, vibe, must-dos, constraints, layovers. No machine-gunning.
- **Confirm** — restates the research plan before burning any Maps calls or teammate turns.
- **Research** — parallel sonnet teammates handle category research (dining, activities, neighbourhoods); the lead handles map geometry, weather, and synthesis.

See [SKILL.md](./skills/travel-research/SKILL.md) for the agent-facing workflow.

## License

MIT.

# travel-research — placeholder reference

This skill references your Obsidian vault by placeholder. Fork the plugin, find/replace each placeholder with your actual path, and check the result into your own setup. Or copy `SKILL.md` into `~/.claude/skills/` and substitute inline.

## Placeholders

| Placeholder | What it is | Example value |
|---|---|---|
| `${WIKI_ROOT}` | Relative or absolute path to your Obsidian vault root | `Wiki` or `~/Documents/MyVault` |
| `${TRIPS_BASE}` | Path under `WIKI_ROOT` where trip notes live | `02-Projects/Trips` |
| `${PROJECTS_BASE}` | Folder name for defined-outcome projects at the vault root (used when updating the projects index) | `02-Projects` |

The skill also expects your vault to contain a `CLAUDE.md` at `${WIKI_ROOT}/CLAUDE.md` describing your conventions (frontmatter, wikilinks, index format, Google Maps place-linking rule). If absent, the skill falls back to sensible defaults but you'll get more value writing one.

## Assumed output layout

```
${WIKI_ROOT}/
└── ${TRIPS_BASE}/
    └── <Destination>/
        ├── Ideas.md                          ← curated synthesis, machine-parseable Trip Context block at top
        ├── <Destination> — Dinner Restaurants.md
        ├── <Destination> — Cafes and Brunch.md
        └── (etc. — one Findings note per category)
```

Past trip diaries (`${WIKI_ROOT}/${TRIPS_BASE}/*Diary*.md`) are read on Discover so lessons compound across trips.

## Google Maps MCP

This skill assumes the `mcp__google-maps__*` tools are available. Install the [Google Maps MCP server](https://github.com/modelcontextprotocol/servers/tree/main/src/google-maps) (or your preferred fork) and configure your API key before invoking the skill.

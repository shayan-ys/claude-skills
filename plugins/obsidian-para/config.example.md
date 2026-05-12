# obsidian-para — placeholder reference

The four skills in this plugin reference your Obsidian vault by placeholder. Fork the plugin, find/replace each placeholder with your actual path, and check the result into your own setup. Or copy the SKILL.md files into your `~/.claude/skills/` and substitute inline.

## Placeholders used across all skills

| Placeholder | What it is | Example value |
|---|---|---|
| `${WIKI_ROOT}` | Relative or absolute path to your Obsidian vault root | `Wiki` or `~/Documents/MyVault` |
| `${WORK_DIARY_BASE}` | Path under `WIKI_ROOT` where daily work-diary entries live | `01-Areas/Career/Work-Diary` |
| `${STANDUP_NOTES_BASE}` | Path under `WIKI_ROOT` for synthesized standup notes | `01-Areas/Career/Standup-Notes` |
| `${COMPANY_NAME}` | Your employer's name (used in skill prose and tags) | `Acme Corp` |
| `${COMPANY_CONTEXT_NOTE}` | Note describing company standup cadence, org context (opaque path) | `${WIKI_ROOT}/01-Areas/Career/Acme.md` |
| `${TRIPS_BASE}` | Path under `WIKI_ROOT` for travel-planning notes | `02-Projects/Trips` |

## Assumed vault structure (PARA)

These skills assume your vault follows a [PARA](https://fortelabs.com/blog/para/) structure:
- `01-Areas/` — ongoing life areas
- `02-Projects/` — defined-outcome projects
- `03-Resources/` — reference material
- `00-Inbox/` — unprocessed captures
- Each folder has an `_index.md` that the skills read and maintain

If your vault doesn't match this layout, the skills can still work but you'll get more value rewriting them than configuring them.

## Cmux dependency (optional)

`wiki-process` and `wiki-lint` optionally mention launching parallel teammate panes via [cmux](https://github.com/get-cmux/cmux) (a multi-pane terminal multiplexer). It's optional — serial execution works fine.

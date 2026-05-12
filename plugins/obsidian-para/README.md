# obsidian-para

A Claude Code plugin bundling four skills for maintaining an [Obsidian](https://obsidian.md) vault organized by [PARA](https://fortelabs.com/blog/para/):

- **wiki-lint** — vault-wide health check (broken frontmatter, orphan notes, stale archives, missing lead paragraphs, weak backlinks)
- **wiki-process** — triage and file `00-Inbox/` captures into PARA folders with proper frontmatter, wikilinks, and index updates
- **standup-notes** — synthesize daily work-diary entries into a structured standup prep note
- **travel-research** — interactive trip-planning companion that triages booked-vs-research and builds curated Ideas + Findings notes per category

Travel examples embedded in travel-research (specific cities/routes) are **illustrative author vignettes**, not telemetry about your vault.

## Install

    /plugin install obsidian-para@shayan-ys

Then **fork or copy** and replace the placeholders documented in [config.example.md](./config.example.md). The skills are written with placeholders like `${WIKI_ROOT}` and `${COMPANY_NAME}` that you replace with your own paths and names.

## Why placeholders instead of a runtime config?

Anthropic's [skill authoring best practices](https://docs.anthropic.com/en/docs/agents-and-tools/agent-skills/best-practices) lean on placeholder substitution rather than runtime config files. Fork-and-edit is also what most high-star OSS skill repos actually do today.

## Assumptions

- Vault organized by PARA (`01-Areas/`, `02-Projects/`, `03-Resources/`, etc.)
- Each folder maintains an `_index.md`
- You're working on macOS or Linux

## License

MIT.

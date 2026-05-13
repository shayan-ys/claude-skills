# obsidian-para — placeholder reference

The three skills in this plugin reference your Obsidian vault by placeholder. Fork the plugin, find/replace each placeholder with your actual path, and check the result into your own setup. Or copy the SKILL.md files into your `~/.claude/skills/` and substitute inline.

## Placeholders used across all skills

| Placeholder | What it is | Example value |
|---|---|---|
| `${WIKI_ROOT}` | Relative or absolute path to your Obsidian vault root | `Wiki` or `~/Documents/MyVault` |
| `${OBSIDIAN_VAULT_NAME}` | Your Obsidian vault's display name (used for `obsidian://` URIs and CLI commands) — find it in Obsidian → Settings → About → Vault name | `MyVault` |
| `${WORK_DIARY_BASE}` | Path under `WIKI_ROOT` where daily work-diary entries live | `01-Areas/Career/Work-Diary` |
| `${STANDUP_NOTES_BASE}` | Path under `WIKI_ROOT` for synthesized standup notes | `01-Areas/Career/Standup-Notes` |
| `${COMPANY_NAME}` | Your employer's name (used in skill prose and tags) | `Acme Corp` |
| `${COMPANY_CONTEXT_NOTE}` | Note describing company standup cadence, org context (opaque path) | `${WIKI_ROOT}/01-Areas/Career/Acme.md` |

### Folder structure placeholders

These replace the hardcoded numeric prefixes (`00-`, `01-`, etc.) used in the author's personal vault. Vanilla PARA users should set these to the plain PARA names; power users can keep the prefixed defaults.

| Placeholder | Default | Vanilla PARA override |
|---|---|---|
| `${INBOX_BASE}` | `00-Inbox` | `Inbox` |
| `${AREAS_BASE}` | `01-Areas` | `Areas` |
| `${PROJECTS_BASE}` | `02-Projects` | `Projects` |
| `${RESOURCES_BASE}` | `03-Resources` | `Resources` |
| `${JOURNAL_BASE}` | `05-Journal` | `Archive` or omit |
| `${MOC_BASE}` | `06-Maps-of-Content` | `Maps` or omit |

The numeric prefixes are a personal convention — they force Obsidian's file explorer into a consistent order. They carry no structural meaning. If your vault uses plain PARA names, set each placeholder accordingly and the skills work identically.

## Assumed vault structure (PARA)

These skills assume your vault follows a [PARA](https://fortelabs.com/blog/para/) structure (folder names reflect the defaults above):

```
MyVault/
├── 00-Inbox/          ← ${INBOX_BASE}
├── 01-Areas/          ← ${AREAS_BASE}
├── 02-Projects/       ← ${PROJECTS_BASE}
├── 03-Resources/      ← ${RESOURCES_BASE}
├── 05-Journal/        ← ${JOURNAL_BASE}  (optional)
├── 06-Maps-of-Content/ ← ${MOC_BASE}    (optional)
└── CLAUDE.md          ← vault schema / conventions doc
```

Each folder has an `_index.md` that the skills read and maintain.

If your vault doesn't match this layout, the skills can still work but you'll get more value rewriting them than configuring them.

## Cmux dependency (optional)

`wiki-process` and `wiki-lint` optionally mention launching parallel teammate panes via [cmux](https://github.com/get-cmux/cmux) (a multi-pane terminal multiplexer). It's optional — serial execution works fine.

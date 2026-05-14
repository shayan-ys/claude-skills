---
name: wiki-lint
description: "Vault-wide health check and cleanup for the Obsidian Wiki. Finds broken frontmatter, orphan notes, missing lead paragraphs, stale archives, duplicate notes, weak backlinks, and outdated indexes — then fixes them with your approval. Use this skill whenever the user says lint, health check, clean up, tidy, audit, or maintain the vault/wiki, or when they ask about orphan notes, broken links, stale content, or vault quality. Also trigger when the user says things like 'is anything messy in the wiki' or 'what needs attention in the vault'."
argument-hint: "[area to focus on, e.g. 'Career' or 'full vault']"
---

# Wiki Lint — Vault Health Check & Cleanup

Run a comprehensive health check on the Obsidian Wiki vault, surface issues, and fix them with the user's approval.

**Scope**: If `$ARGUMENTS` names a specific area or folder, limit the lint to that subtree. Otherwise, lint the full vault.

---

## Philosophy

This skill follows the vault's "Don't Ask / Do Ask" principle. Mechanical fixes (updating an index table, filling a missing `aliases: []` field) can be done silently. Structural changes (merging two notes, archiving something, creating a new MOC) require the user's go-ahead. Always present findings as a summary — not one-by-one interruptions.

---

## Step 0 — Load the Rulebook

1. Read `${user_config.wikiRoot}/CLAUDE.md` — this is the authoritative schema. Every check below validates against it.
2. Read the target folder's `_index.md` to get the current inventory.
3. If linting the full vault, read all top-level `_index.md` files:
   - `${user_config.inboxBase}/_index.md`, `${user_config.areasBase}/_index.md`, `${user_config.projectsBase}/_index.md`, `${user_config.resourcesBase}/_index.md`, `${user_config.journalBase}/_index.md`, `${user_config.mocBase}/_index.md`

---

## Step 1 — Spawn Teammates for Parallel Scanning

For a full-vault lint, if you have a multi-pane terminal multiplexer like [cmux](https://github.com/get-cmux/cmux), you can use cmux teammates to parallelize; otherwise serial execution works. Create one team, then spawn one teammate per vault area. Each teammate runs the checks from Step 2 on its assigned folders and reports findings back via `SendMessage`.

```
Team: "vault-lint"
Teammates:
  - "lint-areas"    → ${user_config.areasBase}/
  - "lint-projects" → ${user_config.projectsBase}/
  - "lint-resources"→ ${user_config.resourcesBase}/
  - "lint-journal"  → ${user_config.journalBase}/ and ${user_config.mocBase}/
```

For a scoped lint (single folder), skip teammates and run checks directly.

Each teammate should:
1. Read every `.md` file in its assigned folder tree (excluding `_index.md` and `99-Meta/Templates/`)
2. Run all checks from Step 2
3. Report findings as structured lists back to the coordinator via `SendMessage`

After all teammates report back, the coordinator (you) aggregates findings into the summary in Step 3.

---

## Step 2 — The Checks

Run every check below. Track findings in categories.

### 2a. Frontmatter Validation

For each note, verify against the schema in `${user_config.wikiRoot}/CLAUDE.md`:

- [ ] Has YAML frontmatter block
- [ ] Has all required fields: `title`, `type`, `tags`, `status`, `created`, `updated`, `summary`, `related`, `source`, `aliases`
- [ ] `type` is one of: `idea`, `note`, `article`, `research`, `project`, `reference`, `person`, `tool`, `journal`
- [ ] `status` is one of: `seed`, `growing`, `evergreen`, `archived`
- [ ] `summary` exists and is ≤ 30 words
- [ ] `tags` array has ≤ 5 entries
- [ ] `aliases` field exists (even if empty `[]`)
- [ ] `created` and `updated` are valid dates

Flag web clippings in `${user_config.inboxBase}/Clippings/` separately — they arrive with non-standard frontmatter and need full rewriting during processing, not just patching.

### 2b. Lead Paragraph Check

Every note must have a lead paragraph (2-3 sentences) immediately after the `# Title` heading. Check for this by looking for substantive text (not just a heading or blank line) between `# Title` and the first `## Section`.

### 2c. Heading Structure Check

For notes with types that have a heading contract (article, research, project, idea), verify they have the expected H2 sections per `${user_config.wikiRoot}/CLAUDE.md`'s Heading Structure Contract table.

### 2d. Orphan Notes

Find notes with:
- Zero inbound wikilinks from other notes (no other note links to this one)
- Only self-referential or zero outbound wikilinks

Exclude `_index.md` files and `Home.md` from this check.

### 2e. Broken Wikilinks

Scan all `[[wikilinks]]` and `related:` frontmatter entries. Flag any that point to non-existent files (no matching filename or alias in the vault).

### 2f. Stale Archives

Find notes where `status: archived` and `updated` date is older than 30 days from today. These are candidates for deletion.

### 2g. Stale Growing Notes

Find notes where `status: growing` but `updated` date is older than 30 days. These are stuck — surface them so the user can either develop or archive them.

### 2h. Duplicate Detection

Look for notes that likely cover the same topic:
- Same or very similar `title` fields
- Overlapping `aliases`
- Files with similar names in different folders

Don't auto-merge — just flag pairs for the user to decide.

### 2i. Index Accuracy

For each folder with an `_index.md`, verify:
- Every `.md` file in the folder has an entry in the index
- No index entries point to deleted/moved files
- Entries are sorted alphabetically
- Summary column matches the note's actual `summary` frontmatter

### 2j. Unprocessed Inbox

Count items in `${user_config.inboxBase}/` (including `Clippings/`). These haven't been filed yet.

### 2k. MOC Opportunities

If any tag (check via `obsidian` CLI / Obsidian MCP with **your vault name** — often the basename of `${user_config.wikiRoot}` — e.g. `obsidian vault="${user_config.obsidianVaultName}" tags counts`) or topic cluster has 5+ notes but no MOC in `${user_config.mocBase}/`, flag it as a MOC candidate.

### 2l. Tag Hygiene

Run `obsidian vault="${user_config.obsidianVaultName}" tags counts` (vault name matches your Obsidian vault, often the basename of `${user_config.wikiRoot}`) and look for:
- Tags used only once (possible typos or one-offs)
- Tags outside the established namespaces in `${user_config.wikiRoot}/CLAUDE.md`
- Near-duplicate tags (e.g., `tech/hw` vs `tech/hardware`)

### 2m. Stale Trips

Find notes in `${user_config.wikiRoot}/${user_config.tripsBase}/` (recursively) where `type: project` and `endDate` is more than 14 days in the past (relative to today). These are completed trips that should be archived.

Surface them as suggestions — do NOT auto-archive. Per the "Ask before doing" principle, present the list and ask the user whether to:
- Set `status: archived` in place (simplest), or
- Move to an `Archive/` subfolder inside `${user_config.wikiRoot}/${user_config.tripsBase}/` and set `status: archived`

The child notes (Dining, Activities) in the same trip folder are not `type: project` so they won't match directly — but flag them as a group ("along with N child notes") so the user can decide whether to archive the whole folder together.

### 2n. Ephemeral public notes (optional)

If you operate an ephemeral "share link then unpublish" blog or paste pipeline outside the vault (author-specific setups vary), optionally audit whatever ledger or manifest tracks published slugs against your staleness threshold (e.g. **14 days** since last update).

1. Only run this step if **you** have a known tooling path — e.g. a local script or project's ledger file. If you don't, skip silently (mention "skipped: no ephemeral-publish ledger configured" once in the report).
2. If the ledger exists, flag entries stale by age; confirm with `AskUserQuestion` before bulk review.
3. **Unpublish** only via **your own** documented command — e.g. your blog-publish or unpublish script with credentials from **your** environment. Do **not** assume a universal CLI; this workflow is intentionally not hard-coded.

Skip entirely when no user-provided unpublish mechanism exists — do not invent hostnames or paths.

---

## Step 3 — Present the Report

After all checks complete, present findings to the user as a single organized summary. Group by severity:

### Report Format

```markdown
## Vault Lint Report — [date]

### Needs Attention (action required)
- N notes with broken/missing frontmatter
- N broken wikilinks
- N stale archives (>30 days, candidates for deletion)
- N unprocessed inbox items
- N duplicate note pairs detected

### Suggestions (your call)
- N orphan notes could use more connections
- N growing notes stalled for 30+ days
- N MOC opportunities detected
- N tag hygiene issues

### Auto-Fixable (I can do these now)
- N index files out of date
- N notes missing `aliases: []`
- N notes missing lead paragraphs I can draft
- N summaries over 30 words I can trim
```

List specific notes under each category so the user can see exactly what's affected.

---

## Step 4 — Fix with Approval

After presenting the report, ask the user what to fix. Follow the "Don't Ask / Do Ask" principle:

**Auto-fix without asking** (mechanical):
- Add missing `aliases: []` to frontmatter
- Update `_index.md` tables to match actual folder contents
- Fix `updated` dates that are clearly wrong
- Sort index entries alphabetically

**Ask before doing** (structural):
- Delete stale archived notes
- Merge duplicate notes
- Archive stale growing notes
- Create new MOCs
- Move notes between folders
- Add wikilinks between notes that seem related

When fixing, spawn your multiplexer teammates again if there are many fixes across different areas. Each teammate handles its own folder's fixes and updates the relevant `_index.md` when done.

---

## Step 5 — Shutdown

After all fixes are applied:
1. Send shutdown requests to all teammates
2. Delete the team
3. Give the user a brief summary: "Fixed X issues, Y items need your decision, Z items skipped."

---
name: wiki-process
description: "Process unprocessed items from the Obsidian Wiki inbox (${user_config.inboxBase}/). Reads raw captures and web clippings, classifies them, adds proper frontmatter, moves them to the right PARA folder, wires up wikilinks, and updates indexes. Use this skill when the user says process inbox, file inbox, triage inbox, sort inbox, clean inbox, or any variation of 'deal with stuff in the inbox'. Also trigger when the user mentions new clippings, unprocessed notes, or asks 'what's in the inbox'."
argument-hint: "[all | latest | specific-filename.md]"
---

# Wiki Process — Inbox Triage & Filing

Process unprocessed notes from `${user_config.inboxBase}/` into their proper places in the vault.

---

## Step 0 — Determine Scope

Check what `$ARGUMENTS` says:

- **`latest`** or empty → process only the most recently modified file in `${user_config.inboxBase}/` (including `Clippings/`)
- **`all`** → process every item in `${user_config.inboxBase}/` (including `Clippings/` subfolder)
- **A specific filename** → process just that file

If `$ARGUMENTS` is empty or ambiguous:

1. List `${user_config.inboxBase}/` and `${user_config.inboxBase}/Clippings/` (excluding `Prompts/` and `Archive/`) and identify the most recently modified file. Read its `title` from frontmatter if present, otherwise fall back to the filename (without `.md`).
2. Also count the total number of inbox items (across `${user_config.inboxBase}/` and `Clippings/`, excluding `Prompts/` and `Archive/`).
3. Ask the user via `AskUserQuestion`, embedding the latest title and total count so the user knows exactly what's queued. For example:

> "Latest inbox item: **\<Title of latest note\>**. There are N items total. Process just the latest, or all of them? (If all, I'll spin up teammates to work in parallel.)"

If the inbox is empty, say so and stop — don't ask the question.

---

## Step 1 — Load Context

1. Read `${user_config.wikiRoot}/CLAUDE.md` — the authoritative vault schema. All frontmatter, structure, and formatting decisions come from here.
2. Read all top-level `_index.md` files to understand what already exists in each area:
   - `${user_config.areasBase}/_index.md`, `${user_config.projectsBase}/_index.md`, `${user_config.resourcesBase}/_index.md`, `${user_config.mocBase}/_index.md`
3. Run `obsidian vault="${user_config.obsidianVaultName}" tags counts` to get the current tag inventory.
4. List all files in `${user_config.inboxBase}/`, `${user_config.inboxBase}/Clippings/`, and `${user_config.inboxBase}/Prompts/` (excluding `Archive/`) to identify items to process.

---

## Step 1.5 — Check Open Prompts (Mandatory)

`${user_config.inboxBase}/Prompts/` is a queue of standing requests for Claude (see `${user_config.wikiRoot}/CLAUDE.md` → "Prompts Folder"). **Before filing any inbox items, scan this folder.**

1. List `${user_config.inboxBase}/Prompts/*.md` (ignore the `Archive/` subfolder).
2. **If there are zero open prompts, skip this step silently.** Do not ask the user about it.
3. If there are one or more, read each prompt file (they're short, free-form prose) and build a one-line summary per prompt.
4. Use `AskUserQuestion` to ask **one** question with exactly two options:

   ```
   Question: "You have N open prompt(s):
     - <Prompt Title 1> — <one-line gist>
     - <Prompt Title 2> — <one-line gist>
   Tackle them before processing the inbox?"
   header: "Open prompts"
   options:
     - label: "Yes, tackle prompts first"
       description: "Address open prompts, then ask whether to continue to inbox processing."
     - label: "No, skip to inbox"
       description: "Leave prompts for later; proceed to Step 2."
   ```

5. **If "No"** → proceed to Step 2.
6. **If "Yes"** → use a second `AskUserQuestion` to pick which prompt(s) to address and how:
   - For 1–4 prompts, list each as an option with `multiSelect: true`, plus a final option "All of them — run in parallel teammates"
   - For >4 prompts, chunk them (first 3 shown, "see more" handled by user typing Other)
   - Include an option "Run selected in parallel teammates" if multiple are selected and they're independent
7. Address each chosen prompt:
   - Follow the prompt's intent. If it says "research X" → use the `research` flow. "Brainstorm Y" → use `idea` flow. Creates output notes in the right PARA folder per the normal conventions in `${user_config.wikiRoot}/CLAUDE.md`.
   - If you have a multi-pane terminal multiplexer like [cmux](https://github.com/get-cmux/cmux), use cmux teammates for parallel prompts (per project `CLAUDE.md` — `TeamCreate` + `Agent` with `team_name`, never `run_in_background`); otherwise run serially. Prefer sonnet teammates for grunt work.
8. Once each prompt is addressed, **delete the prompt file** from `${user_config.inboxBase}/Prompts/`. No archive — Obsidian Sync preserves version history. Make sure the output note(s) produced from the prompt are properly filed in PARA and linked before deletion.
9. After all chosen prompts are addressed, use `AskUserQuestion` again:

   ```
   Question: "Prompt(s) handled. Continue to inbox processing now?"
   header: "Continue?"
   options:
     - label: "Continue to inbox"
       description: "Proceed to Step 2 and process remaining inbox items."
     - label: "Stop here"
       description: "Stop. Inbox items stay untouched for a future session."
   ```

10. If "Stop" → exit cleanly with a summary of what was addressed. If "Continue" → proceed to Step 1.6.

---

## Step 1.6 — Work-Diary (Mandatory, runs before generic inbox)

**Opt-in**: This step is only relevant if you have a capture pipeline that drops timestamped voice-memo transcripts into `${user_config.inboxBase}/Work-Diary/`. If you don't use this pattern, skip Step 1.6 entirely and proceed to Step 2.

`${user_config.inboxBase}/Work-Diary/` is a separate stream: voice-memo transcripts dropped by an iOS Shortcut (or similar capture mechanism) into this folder. They have a totally different shape from generic inbox captures (timestamped `## HH:MM` blocks, minimal frontmatter, one file per day) and a fixed destination (`${user_config.wikiRoot}/${user_config.workDiaryBase}/`), so they get their own pass before the generic Step 2 sweep. Keep a consistent contract for filenames and timestamps in your vault's conventions doc (`${user_config.wikiRoot}/CLAUDE.md`) if you use this pipeline.

1. List `${user_config.inboxBase}/Work-Diary/*.md` (oldest first by mtime). If empty, skip this step silently.
2. If one or more entries exist, use `AskUserQuestion`:
   ```
   Question: "N work-diary entr(y/ies) waiting: <filename1>, <filename2>, ... Process now?"
   header: "Work diary"
   options:
     - label: "Yes, process all"
       description: "Clean transcripts, link projects, file under ${user_config.wikiRoot}/${user_config.workDiaryBase}/."
     - label: "Skip to inbox"
       description: "Leave work-diary entries for later; proceed to Step 2."
   ```
3. If "Skip" → proceed to Step 2.
4. If "Yes" → for each file (oldest first, in series — these are short and benefit from carrying tag/project context across entries):

   **a. Determine the target date.** Prefer the `created:` field in the inbox frontmatter. If absent, parse `YYYY-MM-DD` from the filename. If neither parses cleanly, ask the user.

   **b. Light transcript cleanup.** Fix obvious mis-hearings (homophones, garbled proper nouns), restore paragraph breaks where Voice Memos ran sentences together, and fix punctuation. **Preserve the user's voice and content as written.** Do not reorder, summarize, or restructure into Wins/Blockers/Lessons buckets — the user explicitly opted out of that.

   **Handling broken endings or unclear bits:**
   - **Dangling fragments — DELETE.** If the transcript trails off mid-sentence with no semantic content (e.g. ends in a bare auxiliary like "Will", "And then I", "So we", a conjunction, or half a clause that adds no information), just stop the paragraph at the previous complete sentence. Voice Memos / the iOS Shortcut routinely cut off recordings — these fragments are noise, not content. Do NOT preserve them with an `<!-- unclear -->` comment; that draws attention to nothing and reads as a typo to the user later.
   - **Garbled but substantive content — FLAG.** If there's actual content the user clearly tried to convey but a name, number, or referent is unintelligible (e.g. "I synced with [unintelligible name] about the migration"), leave the surrounding sentence intact and mark just the unclear span with `<!-- unclear: ... -->`. Reserve this marker for cases worth coming back to.
   - **When in doubt:** ask "would a human re-reading this in 6 months get any value from the marked text?" If no, delete. If yes, flag.

   **c. Detect project/area mentions.** Scan the cleaned transcript for mentions of existing notes — search by both note title and `aliases:` field across `${user_config.areasBase}/`, `${user_config.projectsBase}/`, `${user_config.resourcesBase}/`. Convert the first occurrence per note to an inline `[[wikilink]]`. Don't link every occurrence — that creates visual noise on mobile. If a mention is ambiguous (e.g. "the migration" could be one of several projects), leave it as plain text.

   **d. Build full frontmatter** for the processed file:
   ```yaml
   ---
   title: "Work Diary — YYYY-MM-DD"
   type: journal
   tags:
     - career/work-diary
     # plus 0-2 contextual tags from existing inventory if the day's entries are clearly themed
   status: evergreen
   created: <target date from 4a>
   updated: <today>
   summary: "<≤30 words, derived from the day's content — what got done, blockers, key conversations>"
   related:
     - "[[<project linked in step 4c>]]"
   source: voice-memo
   ---
   ```
   `status: evergreen` (not `seed`) is intentional — diary entries are immutable historical records, not drafts. They don't grow.

   **e. Compose the body.** After the `# Title` heading, write a 1-2 sentence lead paragraph summarizing the day (this auto-generated lead is what the user will scan in weekly/quarterly rollups later). Then the cleaned `## HH:MM` blocks in chronological order, with wikilinks woven inline.

   **f. File the note** to `${user_config.wikiRoot}/${user_config.workDiaryBase}/YYYY-MM-DD.md`.
   - **If the destination already exists** (e.g. user processed morning entries earlier, then evening batch later the same day): append the new `## HH:MM` blocks to the existing file in chronological order, regenerate the lead paragraph + summary frontmatter to cover all blocks, and bump `updated:`. Do NOT overwrite.

   **g. Update `${user_config.wikiRoot}/${user_config.workDiaryBase}/_index.md`.** Create the index if it doesn't exist (the folder may be empty on first run). Sorted reverse-chronologically (newest first) — for journals the user wants the latest entry at the top, opposite of the alphabetical default.

   **h. Delete the inbox file.** Obsidian Sync version history is the safety net.

5. After all work-diary entries are processed, proceed to Step 2 for any remaining generic inbox items.

**Why this is its own step and not part of Step 2's teammate sweep:** the work-diary pipeline is deterministic and short (4-8 tool calls per file), so spawning a teammate per entry is overkill and the cross-entry context (same project mentions appearing across the week) is worth keeping in one place. The generic Step 2 path is for heterogeneous captures that benefit from parallelization.

---

## Step 2 — Spawn Teammates (All Mode)

If processing multiple items, parallelize with your multiplexer (e.g. cmux teammates) if available; otherwise run serially. Create one team when using a multiplexer, then spawn one teammate per inbox item (or batch if there are many — max 4 teammates).

```
Team: "inbox-process"
Teammates: one per inbox item (or batched if >4 items)
```

Each teammate gets:
- The full vault schema (from ${user_config.wikiRoot}/CLAUDE.md — include the frontmatter schema, heading contracts, wikilink conventions, mobile formatting rules, and tag namespaces)
- The current tag inventory
- The list of existing notes from all `_index.md` files (so it can find related notes and avoid duplicates)
- Its assigned inbox file(s) to process

If processing a single item (latest mode), skip teammates and do it directly.

---

## Step 3 — Process Each Item

For each inbox note, follow this pipeline:

### 3a. Read and Understand

Read the full note. Determine what it is:
- **Web clipping** (from `Clippings/`, has `source` URL, likely has non-standard frontmatter) → needs full rewrite
- **Quick capture** (user jotted something down, may have partial or no frontmatter) → needs classification and enrichment
- **Already partially processed** (has proper frontmatter but still in inbox) → just needs filing

### 3b. Classify

Determine the best `type` for this note:
- `article` — saved web content the user wants to reference
- `research` — investigation into a topic
- `idea` — a thought or concept to develop
- `note` — general knowledge capture
- `reference` — factual/technical reference material
- `tool` — a software tool or service
- `person` — about a person
- `project` — an active project
- `journal` — dated diary/log entry (work diary, daily reflections); files under `${user_config.wikiRoot}/${user_config.workDiaryBase}/` or `${user_config.journalBase}/`

Determine the destination folder:
- Personal development, ongoing life areas → `${user_config.areasBase}/[subfolder]/`
- Active projects with defined outcomes → `${user_config.projectsBase}/[subfolder]/`
- Reference material, articles, guides, tools → `${user_config.resourcesBase}/[subfolder]/`
- If uncertain about destination → **ask the user** (this is a structural decision)

### 3c. Build Frontmatter

Rewrite the YAML frontmatter to match the vault schema exactly:

```yaml
---
title: "Human-readable title"
type: <determined in 3b>
tags:
  - <pick from existing tags via tag inventory, max 5>
status: seed
created: <keep original if present, otherwise today>
updated: <today's date>
summary: "<one sentence, max 30 words — what is this and why does it matter>"
related:
  - "[[Related Note]]"
source: "<original URL for clippings, 'manual' for hand-written>"
aliases: ["<alternate names people might search for>"]
---
```

Tag selection rules (from ${user_config.wikiRoot}/CLAUDE.md):
- Use established namespaces: `finance/`, `tech/`, `health/`, `career/`, `philosophy/`, `home/`, `meta/`
- Prefer reusing existing tags from the inventory over inventing new ones
- Max 5 tags per note

### 3d. Structure the Content

Based on the note's `type`, apply the heading structure contract from ${user_config.wikiRoot}/CLAUDE.md:

| Type | Expected H2 sections |
|---|---|
| `article` | `## Why I Saved This`, `## Key Points`, `## My Thoughts` |
| `research` | `## Key Takeaways`, `## Findings`, `## Open Questions`, `## Sources` |
| `project` | `## Goal`, `## Current Status`, `## Next Actions`, `## Decision Log` |
| `idea` | `## The Idea`, `## Why It Matters`, `## Next Step` |
| `reference` | (contextual — lead paragraph required) |
| `note` | (free-form — lead paragraph required) |

For web clippings being converted to `article` type:
- Extract the core value from the clipped content
- Write a `## Why I Saved This` that captures why this is worth keeping
- Distill `## Key Points` from the content (not just copy-paste the whole page)
- Leave `## My Thoughts` empty or with a placeholder for the user to fill in
- Preserve the source URL

**Always add a lead paragraph** right after the `# Title` — 2-3 sentences expanding on the summary.

### 3e. Add Wikilinks

- Scan existing notes (from the `_index.md` files read in Step 1) for related topics
- Weave `[[wikilinks]]` into the text where they naturally fit (inline links for context, not just a dump at the bottom)
- Add the 3-5 most important connections to the `related:` frontmatter field
- If the new note is about a topic an existing note covers, add a backlink to the existing note too (edit the existing note's `related:` field)

### 3f. Apply Mobile Formatting

Per ${user_config.wikiRoot}/CLAUDE.md:
- No hard line wrapping
- Short paragraphs (max 4-5 sentences)
- Max 2-3 callouts per note
- Max 4-column tables
- No ASCII art — use Mermaid for diagrams
- Code blocks sparingly in non-technical notes

---

## Step 4 — File the Note

1. **Move the file** from `${user_config.inboxBase}/` (or `Clippings/`) to the destination folder
   - Use a clean, human-readable filename: "Docker vs Proxmox.md", not "docker-vs-proxmox-2026.md"
   - If the original filename is fine, keep it
2. **Update the destination folder's `_index.md`** — add a row with the note's title, type, status, and summary
3. **Do NOT update `${user_config.inboxBase}/_index.md`** — inbox is transient, no index maintained there
4. If the note fits into a subfolder that doesn't exist yet, create the subfolder and its `_index.md`

---

## Step 5 — Report Results

After all items are processed, present a summary:

```markdown
## Inbox Processing Complete

### Filed
- "Note Title" → ${user_config.areasBase}/<Subject>/ (type: reference, tags: home/audio, tech/hardware)
- "Another Note" → ${user_config.resourcesBase}/Articles/ (type: article, tags: tech/software)

### Needs Your Input
- "Ambiguous Note" — couldn't determine destination. Options: [A] ${user_config.areasBase}/Finance/ [B] ${user_config.resourcesBase}/Guides/

### Skipped
- None (or list reasons)

### New Connections Added
- Added [[New Note]] to Related field of [[Existing Note]]
```

---

## Step 6 — Shutdown

If teammates were used:
1. Wait for all teammates to report completion via `SendMessage`
2. Send shutdown requests to all teammates
3. Delete the team
4. Aggregate individual reports into the final summary above

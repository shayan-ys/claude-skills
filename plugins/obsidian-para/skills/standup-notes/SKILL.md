---
name: standup-notes
description: "Generate prep notes for your company's standups from recent work-diary entries. Reads your work-diary folder for the window since the last standup, synthesizes 'Since last standup / Plan / Blockers' bullets with inline project wikilinks, and writes a dated note to your standup-notes folder. Trigger on standup-notes, standup prep, prep my standup, what should I say at standup, upcoming standup, or scheduled headless runs if you automate this."
argument-hint: "[today | tomorrow | YYYY-MM-DD | --window=YYYY-MM-DD..YYYY-MM-DD]"
---

# Standup Notes

Produce a focused, Obsidian-native prep note for the next ${user_config.companyName} standup by reading the user's daily work-diary entries since the previous standup and shaping them into talking points.

---

## Step 0 — Context Load

Read these files first. They are the operational ground truth — do not skip.

1. `${user_config.companyContextNote}` — company context. The **`## Standup Cadence`** section is authoritative on window logic; if it ever conflicts with what's written here, trust the note.
2. `${user_config.wikiRoot}/${user_config.workDiaryBase}/_index.md` — list of diary entries with summaries. This is your navigation index — do not glob the whole vault.
3. `${user_config.wikiRoot}/${user_config.standupNotesBase}/_index.md` — for the date of the last standup note (if any), to anchor the "since last standup" window.

---

## Step 1 — Determine Standup Date and Work Window

Parse `$ARGUMENTS`:

| Argument | Standup date | Work window |
|---|---|---|
| empty, `today` | today's date | derived from weekday below |
| `tomorrow` | today + 1 day | derived from weekday of tomorrow |
| `YYYY-MM-DD` | that date | derived from weekday of that date |
| `--window=A..B` | argument-required: also need standup date — ask user | explicit `[A, B]` inclusive |

**Weekday → window** (your company's cadence — adjust the weekday→window logic below; the table is an **illustrative** Mon/Wed example only):

**Default example** (must match the `## Standup Cadence` section in `${user_config.companyContextNote}` when you maintain one):

| Standup weekday | Work window covered |
|---|---|
| **Monday** | previous Wed through Sun (5 days). Reflects "Wed+Thu+Fri last week" plus weekend captures if any. |
| **Wednesday** | previous Mon through Tue (2 days). |
| Tue / Thu / Fri / Sat / Sun | Not a standup day in the **example** cadence — ask the user to confirm intent. Offer two options: (a) "treat it as the next standup day in your cadence" with that auto-window, or (b) provide an explicit `--window`. |

**Off-by-one trap:** the work window is *exclusive of the standup day itself* — if standup is Wed 2026-05-13, the window ends Tue 2026-05-12. The day of the standup is too early in the morning to have a diary entry.

---

## Step 2 — Gather Diary Entries

For each date in the work window:

1. Check whether `${user_config.wikiRoot}/${user_config.workDiaryBase}/YYYY-MM-DD.md` exists.
2. If yes, read it in full. Extract:
   - The lead paragraph (1-sentence-per-day summary)
   - Each `## HH:MM` block
   - Any inline `[[wikilinks]]` to projects — these are first-class talking-point anchors
3. If no, note the date as "no entry".

**Empty-window case** (zero diary entries across the entire window) → jump to **Step 4b (stub + optional notification)**.

---

## Step 3 — Synthesize

Group entries by theme rather than by day. Standup audiences want the *what got done* arc, not a chronological dump.

**Heuristics:**

- **Collapse repeats.** Three diary mentions of the same project across two days = one "Since last standup" bullet.
- **Promote wikilinks.** Any project mentioned via `[[wikilink]]` in a diary entry stays linked in the output — the graph view tracks this work.
- **Surface decisions and pivots explicitly.** "We pivoted from X to Y after a colleague's input" reads better than "Researched X. Researched Y."
- **Extract blockers actively.** Diary phrasing like "stuck on", "waiting for", "Alice hasn't replied", "needs X to land first" → blocker bullet. If none surface, write "None" — don't pad.
- **"Plan today/next" comes from the most recent entry's forward-looking statements, plus open threads** (a project that was mid-investigation with no resolution → still on the plate).
- **Talking points are optional.** Only add the section when something notable happened — a customer demo, a decision worth flagging to leadership, a win, an interesting finding. Skip it on routine days.

**Length target:** 3-6 bullets per section. A standup is 30-60 seconds; the note should be skim-readable while waiting for your turn.

---

## Step 4a — Write the Standup Note (normal case)

Path: `${user_config.wikiRoot}/${user_config.standupNotesBase}/<standup-date>.md`

If the file already exists (re-running on the same standup day), regenerate the body and bump `updated:`. Don't append.

```markdown
---
title: "Standup — YYYY-MM-DD"
type: journal
tags:
  - career/standup
status: evergreen
created: <standup date>
updated: <today>
summary: "<≤30 words — one-line gist of what you'll say>"
related:
  - "[[<project linked from a diary entry>]]"
source: "generated from work-diary"
---
# Standup — YYYY-MM-DD

> Covers work-diary entries from **<window start>** to **<window end>** (<N> entries).

## Since last standup

- Bullet with [[Project Link]] inline where relevant.
- Another bullet — concrete what-got-done framing, not "worked on X".

## Plan / next

- Next concrete action on each active thread.
- Pull from the most recent diary's forward-looking statements.

## Blockers

- Specific blocker with the person/dep that would unblock it. Or "None" if nothing's stuck.

## Talking points (optional)

- Only include this section when something is worth flagging — a customer signal, a decision needing executive or manager attention, a notable win. Otherwise omit the heading entirely.
```

---

## Step 4b — Empty-Diary Stub (no entries in window)

Write the same path, but with this body:

```markdown
---
title: "Standup — YYYY-MM-DD"
type: journal
tags:
  - career/standup
status: seed
created: <standup date>
updated: <today>
summary: "Empty — no work-diary entries captured in the standup window."
related: []
source: "generated from work-diary (empty)"
---
# Standup — YYYY-MM-DD

> **No work-diary entries** found between <window start> and <window end>. Capture a diary entry via your ingest path (voice memo dropped by an iOS Shortcut or similar), re-run inbox/work-diary processing (`wiki-process`), then re-run this skill to regenerate this note.

## Since last standup

- _(no captures — fill in manually before standup)_

## Plan / next

- _(fill in manually)_

## Blockers

- _(fill in manually)_
```

Then optionally ping yourself (mobile push, Slack, macro, etc.) so you notice before the meeting — **only** if your environment already has wiring for this. Example patterns (pick what you actually use):

- [ntfy](https://ntfy.sh/) HTTP POST from a machine whose credentials live in **your** secrets manager
- Cron + script on **your** always-on host
- A personal automation that already notifies you elsewhere

Skip entirely if you'd rather rely on Obsidian Sync / calendar reminders alone — don't fail the skill on missing infra.

```bash
# Example scaffold only — fill in YOUR host, YOUR auth token path, YOUR topic/channel.
# curl -d "No work-diary captures since last standup — capture one before the meeting." \\
#      -H "Title: Standup notes empty" \\
#      "https://YOUR-NOTIFICATION-CHANNEL"
```

---

## Step 5 — Index and Open

1. Update `${user_config.wikiRoot}/${user_config.standupNotesBase}/_index.md` — add a row at the **top** (reverse-chronological, newest first). Schema:

   ```
   | [[YYYY-MM-DD]] | journal | evergreen | <summary from frontmatter> |
   ```

2. Open the note in Obsidian (per vault `${user_config.wikiRoot}/CLAUDE.md` "Open in Obsidian" rule — this is a substantive new note, not a bookkeeping edit):

   ```bash
   open "obsidian://open?vault=<YOUR_OBSIDIAN_VAULT_NAME>&file=<URL-encode `${user_config.standupNotesBase}/YYYY-MM-DD.md` paths using %2F for slashes>"
   ```

   Adjust `vault=` to match Obsidian's **exact** vault identifier and build `file=` as the vault-relative URL-encoded path to the standup note (derive from `${user_config.standupNotesBase}`).

   Skip this in headless / CI mode if `open` is unavailable — surface the filesystem path instead.

---

## Step 6 — Report

Final message to the user:

```
Standup notes ready for <date> at:
  `${user_config.wikiRoot}/${user_config.standupNotesBase}/<YYYY-MM-DD>.md`

Window: <start> → <end> (<N> diary entries read)
Projects surfaced: [[Project A]], [[Project B]]
Blockers: <count> (or "none")
```

Skip the verbose summary in headless mode — the optional lightweight notification step is enough when enabled.

---

## Failure modes and recovery

| Symptom | Fix |
|---|---|
| Company context note (`${user_config.companyContextNote}`) missing — can't read Standup Cadence | Stop. Tell user to restore the note before re-running. Don't guess cadence. |
| `Work-Diary/_index.md` missing but folder has files | Read the folder directly via Glob, regenerate the index after writing the standup note. |
| Argument is ambiguous (`tomorrow` on a Fri when your cadence is Mon/Wed example → weekend straddles windows) | Pick the next standup-eligible weekday per **your** `${user_config.companyContextNote}` (or `--window`). Note the assumption in the standup note's `> Covers...` blockquote. |
| Diary entry exists but is malformed (no `## HH:MM` blocks, no frontmatter) | Still read it — fall back to treating the body as one block. Flag in report. |
| File already exists for this standup date | Overwrite body; preserve `created:`; bump `updated:`. |

---

## Future: headless automation (v2)

A cron-driven version of this workflow can wake up on mornings before standup on **your cadence**, run the drafting agent (`cursor-agent`, `claude --headless`, or similar), and ping you via your notification stack. Maintain any plan doc **in your own vault** (`${user_config.wikiRoot}/`) if you automate this — out of scope for the shipped default skill — don't flip it on without explicit user ops.

---
description: Process one Paperless car invoice end-to-end — OCR, extract, lint, summarize, stage on approval.
argument-hint: "[doc-id|paperless-url] [--force] [--force-ocr]"
---

You are processing exactly one car-maintenance invoice from Paperless. You run a
strict Extract → Lint → Summarize → Approve → Commit cycle using
`${CLAUDE_PLUGIN_ROOT}/scripts/enrich.py`.

Argument: `$ARGUMENTS` (may be empty; may be a bare integer; may be a Paperless
document URL; may additionally contain `--force` or `--force-ocr`).

## Environment setup

Before running any script, source the env helper so that plugin config values
are injected as environment variables:

```bash
source "${CLAUDE_PLUGIN_ROOT}/scripts/init-env.sh"
```

This maps `paperlessUrl` → `PAPERLESS_URL`, `paperlessToken` → `PAPERLESS_TOKEN`,
`vehiclesConfigPath` → `CAR_INVOICE_VEHICLES_PATH`, and (if set)
`pipelineStateDir` → `CAR_INVOICE_STATE_DIR`. You MUST source this before each
`uv run` call because each Bash tool invocation is a new subshell.

Prepend `source "${CLAUDE_PLUGIN_ROOT}/scripts/init-env.sh" &&` to every
command below. For brevity the examples show it abbreviated as `[env] &&`.

## Step 1 — Resolve the target

Parse `$ARGUMENTS` into a positional `target` (id or URL, optional) and flags
`--force`, `--force-ocr`.

Run:
```bash
source "${CLAUDE_PLUGIN_ROOT}/scripts/init-env.sh" && cd "${CLAUDE_PLUGIN_ROOT}/scripts" && uv run enrich.py resolve "<target-or-empty>"
```

Inspect the resulting JSON.

- If `id` is null (queue empty): tell the user "nothing to do" and stop.
- Otherwise print a one-line header to the user: `Doc <id>: <title> (<date>) — <paperless_url>`.
- If `already_staged` is true AND the user did NOT pass `--force`: use
  AskUserQuestion to offer `skip`, `redo` (treat as `--force`), or `abort`.
  Act on the answer.

## Step 2 — Fetch + OCR

Run:
```bash
source "${CLAUDE_PLUGIN_ROOT}/scripts/init-env.sh" && cd "${CLAUDE_PLUGIN_ROOT}/scripts" && uv run enrich.py fetch <id>
```
(append `--force-ocr` if the user passed that flag).

Read the path from the returned JSON's `ocr_combined_md` field using the Read
tool. That markdown is the input to extraction.

If `fetch` exits non-zero with an OCR quality gate error (exit code 2): tell
the user what the quality gate said and ask whether to abort or proceed.
Continue only on explicit consent.

## Step 3 — Extract

Before extracting, load two things:

**a) Your vehicle configuration** — run:
```bash
cat "${CAR_INVOICE_VEHICLES_PATH}"
```
This shows which vehicles are in scope (keys, names, VINs). Use these as the
KNOWN VEHICLES when applying the extraction rules below.

**b) The extraction rules** — read the file:
`${CLAUDE_PLUGIN_ROOT}/scripts/extraction_prompt.md`

Apply those rules verbatim to the OCR markdown from Step 2.
Prepend these two lines to the OCR content when you reason about it so the
model fills in the `source` block correctly:

```
paperless_id: <id>
paperless_url: <paperless_url>
```

Produce exactly one JSON object conforming to the schema. No prose before or
after. No markdown fences.

## Step 4 — Lint loop (max 3 attempts)

For each attempt:

1. Write the JSON to `/tmp/car-invoice-<id>.json`.
2. Run:
```bash
source "${CLAUDE_PLUGIN_ROOT}/scripts/init-env.sh" && cd "${CLAUDE_PLUGIN_ROOT}/scripts" && cat /tmp/car-invoice-<id>.json | uv run enrich.py lint <id>
```
3. Parse the JSON result.
4. If `ok: true`: proceed to Step 5. Also note any `warnings[]` to surface at
   approval time.
5. If `ok: false`: you have the raw `errors[]` and the full OCR markdown from
   Step 2. Revise the JSON to fix every error. Go back to sub-step 1.

If three attempts all fail: show the accumulated errors to the user, show the
most recent candidate JSON, and ask how to proceed (abort / override /
edit-together). Do not commit.

## Step 5 — Summarize for human review

Render a compact, scannable summary to the user. Use this layout:

```
═══ Doc <id> — <shop> ═══
Vehicle:  <vehicle key> (VIN …<last 6>)     Date: <YYYY-MM-DD>
Odometer: <value>                            Total: $<total>

Jobs
  # │ Description                                   │ Cost    │ Notes/tags
  1 │ …                                              │ $xx.xx  │ …
  2 │ …                                              │ $ 0.00  │ WARRANTY
  …

Deferred
  [yellow] … (est $…)
  [red]    … (est $…)

Flags
  - cost_unreadable on job N: …
  - missing_jobs: [N, …]
  - lint warnings: …
```

Then call AskUserQuestion with three choices: `approve`, `edit`, `abort`.

## Step 6 — Edit loop

If the user answered `edit`:
1. Ask them in one sentence what to change.
2. Apply the change to your in-memory JSON.
3. Go back to Step 4 (lint must stay green).
4. Re-render the summary, re-ask.

Repeat until `approve` or `abort`.

## Step 7 — Commit

On `approve`:

Run:
```bash
source "${CLAUDE_PLUGIN_ROOT}/scripts/init-env.sh" && cd "${CLAUDE_PLUGIN_ROOT}/scripts" && uv run enrich.py commit <id>
```

Read the returned JSON. Tell the user: `Staged → <path>. Paperless
pipeline_status=staged.` Stop.

On `abort`: tell the user nothing was written. Leave the candidate file
`<pipeline-state-dir>/<id>/extraction.candidate.json` in place — the next run
with the same id will overwrite it. Stop.

## Rules for you

- Never write `extraction.json` directly. Only `enrich.py commit` does that.
- Never skip the approval gate, even for docs that lint clean.
- Do not auto-retry Paperless/network failures. Surface the stderr and ask
  what to do.
- JSON parse failures during your own output do not count toward the 3-attempt
  lint budget — they precede lint entirely.
- One doc per invocation. Do not advance to the next queue entry on completion.

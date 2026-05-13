---
name: google-docs-tabs
description: Read and write Google Docs (including the new tabs/subtabs feature) via a tiny Python helper that calls the Docs API directly with your Google service account. Use whenever the user asks to find a doc tab, create a subtab, write/append/read tab content, or otherwise manipulate a Google Doc with tabs. Prefer this over the @a-bonus/google-docs-mcp MCP — that MCP has a Google-API-side field-mask bug on every tab-scoped call and is not worth fighting.
---

# google-docs-tabs

## When to use
The user wants to read or modify a **Google Doc** — most often one with the new tabs/subtabs feature (e.g. a master resume doc with Resume / Cover letters / Interviews top-level tabs and nested per-job subtabs). Examples:
- "Add a subtab under Interviews for X"
- "Write Y into the <Company> prep tab"
- "Read what's in the <Company> prep tab"
- "List all tabs in the resume doc"

## The one rule that matters
**Don't use the `@a-bonus/google-docs-mcp` MCP for tab work.** It calls `documents.get` with a `fields` mask that selects from `tabs(...)`. Google's Docs API now rejects any such mask with:
```
Field mask cannot retrieve comment-specific fields when include_comments is false.
```
This affects `listTabs`, `addTab`, `appendMarkdown`, `replaceDocumentWithMarkdown`, `readDocument` (when `tabId` is set), `insertTable`, `insertImage`, `renameTab`, `deleteRange`, `updateSectionStyle`, `modifyText` — i.e. essentially every tab-scoped tool. The discovery client doesn't expose a way to set `include_comments`, so the only fix at API call sites is to **omit `fields=` entirely when `includeTabsContent=True`**. Patching the MCP package is a goose chase; just call the API directly.

## How to do it: use the helper script

`${CLAUDE_PLUGIN_ROOT}/scripts/gdocs.py` is a 90-line CLI that wraps the Docs API. It reads the service-account JSON path from the `SA_PATH` env var; set it from the plugin's userConfig value before each invocation:

```bash
export SA_PATH="${GOOGLE_DOCS_SA_PATH:-$googleDocsServiceAccountPath}"
```

(Use whichever name the plugin runtime exposes the userConfig value as.)

### Choosing the right write tool

| What you want to push | Use |
|---|---|
| Plain text (no formatting) | `gdocs.py write` / `gdocs.py append` |
| Markdown file (headings, bold, bullets, tables…) | `md2docs.py` |

`gdocs.py write/append` inserts **raw text** — markdown syntax lands literally as `#`, `**`, `-` characters. If the content has any formatting, use `md2docs.py` instead.

### md2docs.py — render a markdown file into a tab

```bash
# Clears the tab and inserts the file with full formatting (headings, bold, italic, bullets, blockquotes, tables).
${CLAUDE_PLUGIN_ROOT}/scripts/md2docs.py <docId> <tabId> <absolute-path-to-md>
```

The tab is cleared first, then the markdown is rendered with Google Docs native formatting — no raw syntax visible.

### Common operations

```bash
# 1. List the tab tree of a doc (find tab IDs by title)
gdocs.py tabs <docId>

# 2. Get the tabId of a single tab by title
gdocs.py find-tab <docId> "Interviews"

# 3. Create a subtab under a parent (parentTabId optional → root-level)
gdocs.py add-tab <docId> "Acme prep" t.he1fzl2sscc9

# 4. Write at start of a tab / append at end of a tab (plain text only)
gdocs.py write  <docId> <tabId> "hello world"
gdocs.py append <docId> <tabId> "more text"

# 5. Read a tab as plain text
gdocs.py read <docId> <tabId>
```

`docId` is the long string between `/d/` and `/edit` in a Google Docs URL.

### Concrete example

```bash
DOC=${DOC_ID}    # the long string between /d/ and /edit in a Google Docs URL
gdocs.py tabs $DOC
INTERV=$(gdocs.py find-tab $DOC "Interviews")
gdocs.py add-tab $DOC "Acme prep" $INTERV
NEW=$(gdocs.py find-tab $DOC "Acme prep")
gdocs.py append $DOC $NEW "$(cat draft.md)"
```

## Pitfalls (the things that already burned us)

1. **Tab titles must be globally unique within a doc.** The API returns
   `Invalid requests[0].addDocumentTab: Tab title must be unique`. If "Acme"
   already exists as a Cover-letters subtab, the new Interviews subtab must be
   "Acme prep" (matching the existing `<Company> prep` convention) or similar.

2. **The `fields=` parameter is poison whenever `includeTabsContent=True`.** Every
   value — `'tabs'`, `'tabs(tabProperties)'`, `'*'`, `'tabs(tabProperties,documentTab)'` —
   triggers the comment-fields error. Just omit `fields=`. The response is
   slightly larger; we don't care.

3. **`includeComments` is not a real public parameter.** Don't try to pass
   `includeComments=true` as kwarg or query param — the discovery client and
   the Docs server both reject it.

4. **Tab insertion index works in tab-local coordinates.** When inserting text
   into a tab, the location is `{index: 1, tabId: <id>}` — index 1 is the start
   of *that tab*, not the document. The helper handles this.

5. **Append needs the tab's last endIndex.** To append, fetch the doc with
   `includeTabsContent=True`, walk to the target tab, and use
   `body.content[-1].endIndex - 1` as the insert index. (The helper's `append`
   command does this.)

6. **Service account must be shared on the doc.** If the doc isn't shared with
   `<the SA email in sa.json>`, you'll get 403. If you use the same SA across many docs, they're
   already shared with the SA from earlier setup; if a new doc fails, check
   sharing first.

## When to skip this skill
- The doc is a Google Sheet or Slides (different APIs).
- The user wants to edit/extract from a `.docx` checked into the repo.
- You only need to *read* and the doc fits in one Read of an exported file.

## What lives where
- Helper CLI: `${CLAUDE_PLUGIN_ROOT}/scripts/gdocs.py`
- Service account: `${GOOGLE_DOCS_SA_PATH}` (supplied via plugin userConfig prompt on install; exported as `SA_PATH` to the scripts)
- Python dependencies: `google-auth` and `google-api-python-client`. The shebang is `#!/usr/bin/env python3`, so the system `python3` (or whichever venv is on `PATH`) must have those packages. One-liner if you want an isolated venv:

  ```bash
  uv venv /tmp/gd-venv && uv pip install --python /tmp/gd-venv/bin/python google-auth google-api-python-client
  # then either activate the venv or change the script's shebang to point at /tmp/gd-venv/bin/python
  ```

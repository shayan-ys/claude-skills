# google-docs-tabs

A tiny Claude Code plugin that reads and writes Google Docs — including docs with the new tabs/subtabs feature — via a small Python helper that calls the Docs API directly.

## Why this exists

Every tab-scoped tool in the popular [`@a-bonus/google-docs-mcp`](https://github.com/a-bonus/google-docs-mcp) MCP hits this Google API error:

> Field mask cannot retrieve comment-specific fields when include_comments is false.

This affects `listTabs`, `addTab`, `appendMarkdown`, `readDocument` (with `tabId`), etc. The MCP can't be patched cleanly because the discovery client doesn't expose `include_comments`. The fix is to call the API directly with no `fields=` mask when `includeTabsContent=True`.

This plugin is that fix, packaged.

## Install

    /plugin marketplace add shayan-ys/google-docs-tabs
    /plugin install google-docs-tabs@shayan-ys

On install, Claude Code will prompt for the absolute path to your Google service-account JSON file.

## What you can do

- List tabs and find tabs by name
- Read tab content
- Create subtabs under a parent tab
- Write plain text or render full Markdown (headings, bold, bullets, tables) into a tab

See [SKILL.md](./SKILL.md) for the agent-facing instructions.

## License

MIT

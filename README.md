# shayan-ys/claude-skills

A [Claude Code plugin marketplace](https://docs.claude.com/en/docs/claude-code/plugin-marketplaces) of personal skills — Obsidian/PARA vault tooling, Google Docs helpers, and research methodology.

## Install the marketplace

    /plugin marketplace add shayan-ys/claude-skills

Then install any plugin:

    /plugin install <plugin-name>@shayan-ys

## Plugins

| Plugin | What it does | Setup needed |
|---|---|---|
| [`google-docs-tabs`](./plugins/google-docs-tabs/) | Read/write Google Docs with tabs, sidestepping the Docs MCP field-mask bug | Service-account JSON path (prompted on install) |
| [`obsidian-para`](./plugins/obsidian-para/) | Four skills for maintaining an Obsidian vault organized by PARA | Fork and substitute placeholders — see [config.example.md](./plugins/obsidian-para/config.example.md) |
| [`product-research`](./plugins/product-research/) | Buying-decision research methodology with parallel teammates and health-priority bias | None |

## Why this exists

These skills started as personal tools, evolved through real use, and were generalized for OSS. The Obsidian one is the most opinionated (assumes PARA); the Google Docs one solves a specific API bug; the product-research one is pure methodology.

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md). Issues and PRs welcome, especially for placeholder bugs in `obsidian-para`.

## License

MIT. See [LICENSE](./LICENSE).

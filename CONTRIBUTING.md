# Contributing

## Reporting bugs

Open a GitHub issue with:
- Which plugin
- Which SKILL.md trigger phrase you used
- What you expected vs. what happened

## Pull requests

PRs welcome. Style notes:
- Each SKILL.md stays under ~500 lines per [Anthropic's authoring best practices](https://docs.anthropic.com/en/docs/agents-and-tools/agent-skills/best-practices)
- New skills go under an existing plugin if there's a natural axis, otherwise propose a new plugin in an issue first
- Don't introduce personal data — use `${PLACEHOLDER}` tokens and document them in the plugin's `config.example.md`

## License

All contributions are licensed under MIT.

# Changelog

## 1.0.0 - 2026-10-12

First release.

- `check`, `budget`, `collisions`, `report` and `rules` subcommands.
- 15 rules (SKL001-SKL015): frontmatter, naming, description quality, trigger
  phrases, routing lines, front-loading, body size, dead links, personal paths,
  secrets, duplicate names, trigger collisions, script hygiene, instruction-style
  descriptions.
- Listing-budget simulator modelled on the Claude Code docs (names always listed,
  descriptions dropped to fit, 1% of the context window, 1,536-char entry cap),
  with every number overridable.
- Collision maths: Jaccard plus TF-IDF cosine with a threshold.
- Output formats: text, JSON, SARIF 2.1.0, Markdown, HTML.
- Composite GitHub Action (`action.yml`).
- 25-skill fixture pack with deliberate faults, 114 tests, a CI template for Linux, Windows and macOS in `ci/ci.yml`.

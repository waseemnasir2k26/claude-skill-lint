# Claude Skill Lint

**You installed 100 skills. Claude can only see some of them. This lints your `SKILL.md` files, simulates the listing budget and finds skills that fight over the same prompts.**

![License: MIT](https://img.shields.io/badge/license-MIT-green.svg) ![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue) ![Dependencies: none](https://img.shields.io/badge/dependencies-none-brightgreen)

Claude Code lists every skill name in context. When the listing outgrows its character budget, descriptions get dropped, and a skill with no description is a skill that rarely triggers. This shows who loses theirs and why.

## What it does

- 15 rules, SKL001 to SKL015: bad frontmatter, name and folder mismatch, descriptions too long or vague, no "use when" clause, trigger text buried past the first 250 characters, oversized bodies, dead links, hard-coded personal paths, leaked secrets (redacted in output), duplicate names across scopes, trigger collisions, scripts without a shebang.
- `budget` simulates which skills lose their description at a given context size.
- `collisions` scores trigger overlap between skills (Jaccard and TF-IDF cosine).
- Output as text, JSON, SARIF or Markdown, plus an HTML report. A composite GitHub Action and a pre-commit example are included.
- Read-only. No network. Full rule reference in `docs/rules.md`, budget model in `docs/budget.md`.

## Quickstart

```bash
pip install git+https://github.com/waseemnasir2k26/claude-skill-lint
claude-skill-lint check                      # ./.claude/skills and ~/.claude/skills
claude-skill-lint check path/to/skills --fix-suggestions
claude-skill-lint budget --context 1m
claude-skill-lint collisions --threshold 0.5
claude-skill-lint report --out report.html
```

No install: clone the repo and run `python -m skill_lint check <path>` from its root. To see it work first, run it on the planted-fault `fixtures/` pack.

## For you if

You keep a growing skills folder, you wonder why some skills never fire, or you want skill quality checked in CI.

## Status and limits

- The budget model follows Claude Code's documented listing behavior as of writing; limits can change, see `docs/budget.md` for sources.
- Collision scoring is lexical, so it will miss semantic overlap and may flag harmless similarity.
- Last reviewed October 2026.

## Built by SkynetLabs

Built by [SkynetLabs](https://skynetjoe.com). Questions: info@skynetjoe.com

Need this wired into your business? SkynetLabs builds voice agents, n8n back offices and sites that convert → https://skynetjoe.com

# Examples

- `good-skills/` - five skills that lint clean (used by the Action smoke test in CI).
- `github-workflow.yml` - CI workflow with SARIF upload.
- `pre-commit.sh` - local git hook.
- `output-*.txt` - real output captured from the CLI on `fixtures/` (and, for
  `output-estate-budget.txt`, on the author's own `~/.claude/skills`).

Reproduce:

    claude-skill-lint check fixtures/skills fixtures/skills-user --fix-suggestions
    claude-skill-lint budget fixtures/skills fixtures/skills-user --budget-chars 700 --target-len 60
    claude-skill-lint collisions fixtures/skills fixtures/skills-user

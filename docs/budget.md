# The skill-listing budget

Claude Code puts a one-line entry for every installed skill into context so the
model knows what exists. That listing has a character budget. When you have
more skills than fit, descriptions are removed. A skill with no description is
very hard for the model to pick, which is why a big skill pack can quietly stop
triggering.

## What is documented

From the Claude Code skills documentation, section "Skill descriptions are cut
short" (<https://code.claude.com/docs/en/skills>, read 2026-10):

- The listing **always contains every skill name**.
- If you have many skills, Claude Code **drops some descriptions** to fit the
  listing's character budget. It drops descriptions starting with the skills you
  invoke least.
- The budget **scales at 1% of the model's context window**.
- It can be raised with the `skillListingBudgetFraction` setting (for example
  `0.02` for 2%) or the `SLASH_COMMAND_TOOL_CHAR_BUDGET` environment variable
  (a fixed character count).
- Each entry's combined `description` + `when_to_use` text is **capped at 1,536
  characters** (`skillListingMaxDescChars`), regardless of budget.
- Low-priority skills can be set to `"name-only"` in `skillOverrides`.
- Malformed frontmatter makes Claude Code load the skill with empty metadata, so
  it cannot be matched by description.
- `/doctor` estimates the listing's cost and biggest contributors.

Public discussion of the behaviour lives in the issue trackers
(<https://github.com/anthropics/claude-code/issues?q=skill+listing+budget> and
<https://github.com/anthropics/skills/issues>). Figures quoted there have
changed between releases, which is the reason nothing in this tool is hard-wired.
We do not pin issue numbers here because they would go stale; search the links.

## What is NOT documented (so it is a parameter)

| Unknown                                    | Our default                                                                                                                                          | Override                                                        |
| ------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| How many characters is "1% of the window"? | 1% x window tokens x 4 chars/token = **8,000** for 200k, **40,000** for 1M                                                                           | `--budget-chars N`, `--budget-fraction F`, `--context 200k\|1m` |
| Exact line format                          | `- name: description` + newline (name-only: `- name`)                                                                                                | edit `skill_lint/budget.py` constants                           |
| Which descriptions go first                | "least invoked first" cannot be known offline, so we drop from the **end of the listing order** (paths in the order given, alphabetical inside each) | order your paths                                                |
| Per-entry cap                              | 1,536 (documented)                                                                                                                                   | `--entry-cap N` (0 = none)                                      |

Always confirm against `/doctor` in your own install and set the flags to match.
If your settings use `skillListingBudgetFraction: 0.02`, run
`claude-skill-lint budget --budget-fraction 0.02`.

## The model

1. All names are always listed (name-only cost = `len(name) + 3`).
2. A full entry adds `: ` plus the description (cut at the entry cap).
3. Descriptions are added in listing order while the running total fits. The
   first one that does not fit, and every one after it, becomes name-only.
4. `uniform_fit_len` is the longest description length that every skill could
   have at the same time and still fit. It is the number to aim for.
5. The "fix" simulation re-runs steps 1-3 with every description trimmed to
   `--target-len` (default 200) and reports how many more skills keep a
   description. "Fix recovers" per skill is `description_chars - target_len`.

## Practical advice that follows from this

- Front-load: put the key use case and trigger phrases in the first 200
  characters (rule SKL007).
- Shorten descriptions before adding skills; each extra 100 characters per skill
  costs `100 x skill_count` characters of budget.
- Remove duplicates and stale backups (SKL012); they spend budget for nothing.
- Use `name-only` overrides for skills you only ever run by hand.

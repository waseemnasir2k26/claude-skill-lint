# Claude Code Skill Linter: SKILL.md lint, listing-budget simulator and trigger-collision finder

[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)
![Dependencies: none](https://img.shields.io/badge/dependencies-none-brightgreen)

**You installed 100 skills. Claude can only see some of them.**

Claude Code lists every skill name in context, but when the listing outgrows its character budget it drops _descriptions_, and a skill without a description is a skill Claude rarely picks. `claude-skill-lint` is an offline, CI-ready linter for `SKILL.md` packs that tells you which skills are at risk, which descriptions collide, and what to trim. Python 3.10+, standard library only.

## 60-second quickstart

```bash
pip install git+https://github.com/waseemnasir2k26/claude-skill-lint
claude-skill-lint check                      # ./.claude/skills and ~/.claude/skills
claude-skill-lint check path/to/skills --fix-suggestions
claude-skill-lint budget --context 1m        # who loses their description?
claude-skill-lint collisions --threshold 0.5 # which skills fight over the same prompts?
claude-skill-lint report --out report.html   # one-page HTML summary
```

No install? `git clone` the repo and run `python -m skill_lint check <path>` from its root.

## What it checks

| Rule   | What it catches                                                                          |
| ------ | ---------------------------------------------------------------------------------------- |
| SKL001 | Missing / invalid frontmatter `name` or `description` (broken YAML means empty metadata) |
| SKL002 | Name not kebab-case, or not matching the folder                                          |
| SKL003 | Description too long (over the 1,536 listing cap or the 1,024 spec limit) or too short   |
| SKL004 | Vague wording: "helps with", "various tasks", "and more"                                 |
| SKL005 | No "use when" clause or trigger phrases                                                  |
| SKL006 | Colliding skills with no "Do NOT use for" routing line                                   |
| SKL007 | Trigger text buried past the first 250 characters                                        |
| SKL008 | Body over 500 lines / about 5,000 tokens (progressive disclosure)                        |
| SKL009 | Dead relative links and referenced files that do not exist                               |
| SKL010 | Hard-coded personal paths (`C:\Users\...`, `/home/...`)                                  |
| SKL011 | API keys, tokens and private keys (redacted in output)                                   |
| SKL012 | Same skill name defined in more than one scope                                           |
| SKL013 | Trigger collisions above a threshold (Jaccard + TF-IDF cosine)                           |
| SKL014 | Scripts missing a shebang or the executable bit                                          |
| SKL015 | Descriptions written as first-person instructions instead of when-to-use                 |

| Feature      | Detail                                                                                                            |
| ------------ | ----------------------------------------------------------------------------------------------------------------- |
| Formats      | `--format text\|json\|sarif\|md` on `check`; HTML via `report`                                                    |
| Budget model | Names always listed, descriptions dropped to fit, per-skill "fix recovers N chars", before/after simulation       |
| Budget knobs | `--context 200k\|1m`, `--budget-fraction`, `--budget-chars`, `--entry-cap`                                        |
| CI           | Exit code 1 on errors (`--fail-on error\|warning\|info\|never`), SARIF for code scanning, composite GitHub Action |
| Fixes        | `--fix-suggestions` prints a concrete fix under every finding                                                     |
| Safety       | Read-only. No network. Secrets are redacted in all output.                                                        |

Full rule reference: [docs/rules.md](docs/rules.md). Budget model and sources: [docs/budget.md](docs/budget.md).

## Real output

Run on the bundled [`fixtures/`](fixtures) pack (25 skills, faults planted on purpose). Excerpt of `claude-skill-lint check fixtures/skills fixtures/skills-user --fix-suggestions`:

```text
fixtures/skills-user/report-builder/SKILL.md:2: warning SKL012 Skill name `report-builder` is defined 2 times (fixtures/skills-user/report-builder, fixtures/skills/report-builder).
    fix: Rename one copy or delete the shadowed one; only one can win.
fixtures/skills/bad-name-case/SKILL.md:2: warning SKL002 Name `Bad_Name` is not lowercase kebab-case.
    fix: Rename to `bad-name`.
fixtures/skills/bad-name-case/SKILL.md:2: warning SKL002 Name `Bad_Name` does not match its folder `bad-name-case`.
    fix: Set `name: bad-name-case` (or rename the folder) so name and folder agree.
fixtures/skills/bad-script/SKILL.md:1: warning SKL014 `scripts/run.sh` has no shebang line (#!...).
    fix: Add `#!/usr/bin/env bash` as the first line.
fixtures/skills/big-body/SKILL.md:5: info SKL008 Body is 603 lines (> 500).
    fix: Keep SKILL.md short; move detail into references/ files loaded on demand.
fixtures/skills/calendar-wrangler/SKILL.md:3: warning SKL003 Description is 606 chars (> 500): it eats listing budget and risks being dropped.
    fix: Trim to about 200-500 chars; keep trigger phrases first.
fixtures/skills/calendar-wrangler/SKILL.md:3: warning SKL007 Trigger/routing text starts at char 536, past the 250-char front-loading target; it is the first thing lost when text is cut.
    fix: Move the 'Use when ...' clause into the first 250 chars.
...

25 skills checked: 3 errors, 24 warnings, 1 info

Skill listing budget: 8,000 chars (per-entry cap 1536)
  skills: 24   names alone: 368 chars   with every description: 4,006 chars (50% of budget)
  result: everything fits; every skill keeps its full description.
  if every description were trimmed to <= 200 chars: 24 keep a description, 0 name-only -> 0 more skills described
```

Who loses their description when the budget is tight (`budget --budget-chars 700 --target-len 60`):

```text
Skill listing budget: 700 chars (per-entry cap 1536)
  skills: 24   names alone: 368 chars   with every description: 4,006 chars (572% of budget)
  result: 3 keep a description, 21 are name-only (listing 658 chars)
  to keep every description you would need <= 12 chars each
  name-only (Claude sees no description): bad-script, big-body, calendar-wrangler, colon-yaml, csv-cleaner, dead-links, doc-to-pdf, first-pe
  if every description were trimmed to <= 60 chars: 6 keep a description, 18 name-only -> 3 more skills described

skill                              status      desc  shown  fix recovers
calendar-wrangler                  name-only    606      0           546
late-trigger                       name-only    342      0           282
git-commit-writer                  name-only    228      0           168
csv-cleaner                        name-only    195      0           135
```

And the colliding pair (`collisions`):

```text
1 colliding pairs (threshold 0.45):
  0.97  doc-to-pdf  <->  md-to-pdf  (jaccard 0.91, cosine 0.97; terms: content, markdown, convert, document)  shared triggers: convert markdown to pdf, export this document as pdf, make a pdf
```

## Case study: our own 189-file skill estate

We ran it on the author's real `~/.claude/skills` (189 `SKILL.md` files including vendored and nested copies and a backup folder; paths anonymised). Numbers come straight from `claude-skill-lint budget ~/.claude/skills`:

|                                                  | 200k window (budget 8,000 chars) | 1M window (budget 40,000 chars) |
| ------------------------------------------------ | -------------------------------- | ------------------------------- |
| Names alone                                      | 2,854 chars                      | 2,854 chars                     |
| Names + every description                        | 129,902 chars                    | 129,902 chars                   |
| Skills that keep a description                   | **8 of 189**                     | **62 of 189**                   |
| ...after trimming every description to 200 chars | **25** (+17)                     | **184** (+122)                  |
| Longest description every skill could have       | 25 chars                         | 195 chars                       |

The lint pass on the same folder reported 1 error, 625 warnings and 43 info findings, including 24 duplicate-name findings, 42 colliding skill pairs, 139 over-long descriptions and 124 hard-coded personal paths. Much of that is vendored or backup copies, which is precisely the clutter that spends budget.

Honest caveats: this is a **model**, not a measurement. The docs say the budget is 1% of the context window and that descriptions are dropped, least-used first; they do not give a character count or the exact entry format, and least-used order is unknowable offline. We use 4 characters per token and listing order, and every assumption is a flag. Confirm with `/doctor` in your own install. The "after" column is a simulation; we have not applied the trims.

## FAQ

**Is the budget number official?** Partly. The 1% share and the 1,536-character entry cap are from the Claude Code skills docs. The characters-per-token conversion and drop order are our assumptions, documented in [docs/budget.md](docs/budget.md) and overridable.

**How is this different from `claude plugin validate`?** The Claude Code docs describe that command as a way to find `SKILL.md` files whose frontmatter does not parse. This tool goes further (budget simulation, trigger collisions, link and secret checks) and runs anywhere Python does, including CI without Claude Code installed. Use both.

**Does it modify my files?** Never. It only reads.

**Does it send anything anywhere?** No network access at all.

**Can the secret scan replace gitleaks?** No. It is a fast heuristic aimed at what ends up in skills.

**What if it flags something I want?** Use `--ignore SKL008,SKL004` or tune `--threshold`, `--cutoff`, `--max-body-lines`.

**Windows?** Yes. It was developed and tested on Windows 11; the bundled CI template ([ci/ci.yml](ci/ci.yml)) runs the suite on Linux, Windows and macOS. The executable-bit check is skipped on Windows.

## GitHub Action

```yaml
- uses: actions/checkout@v4
- uses: waseemnasir2k26/claude-skill-lint@v1.0.0
  with:
    path: .claude/skills
    fail-on: error
```

SARIF upload and a pre-commit hook are in [examples/](examples).

## Development

```bash
pip install -e ".[dev]"
python -m pytest -q
```

The CI workflow lives in [ci/ci.yml](ci/ci.yml) (copy it to `.github/workflows/ci.yml`; pushing workflow files needs a token with the `workflow` scope).

## More from SkynetLabs

- [mcp-freshness](https://github.com/waseemnasir2k26/mcp-freshness): score every MCP server in your Claude config for liveness and maintenance freshness.
- [upwork-mcp-toolkit](https://github.com/waseemnasir2k26/upwork-mcp-toolkit): offline companion to the official Upwork MCP: job scoring, Connects ROI, proposal lint.
- [fiverr-gig-optimizer](https://github.com/waseemnasir2k26/fiverr-gig-optimizer): offline Fiverr gig scorer and fee calculator, plus a Claude Code skill.

We build and tune Claude Code skill and agent systems for teams. If your pack has outgrown the listing budget and you want it audited and rewritten, hire us on [Fiverr](https://www.fiverr.com/agencies/skynetjoellc) or [Upwork](https://www.upwork.com/freelancers/muhammadwaseemnasir).

## Work with SkynetLabs

Built by [Waseem Nasir](https://www.skynetjoe.com/?utm_source=github&utm_medium=readme&utm_campaign=claude-skill-lint) at SkynetLabs — n8n + AI automation for small businesses.

- Hire on Fiverr: https://www.fiverr.com/agencies/skynetjoellc
- Hire on Upwork: https://www.upwork.com/freelancers/muhammadwaseemnasir
- Book a free call: https://calendly.com/skynetlabs/schedule-a-free-consultation

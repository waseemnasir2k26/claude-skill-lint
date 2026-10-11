# Rules

Severity can be `error`, `warning` or `info`. Exit code 1 when a finding at or
above `--fail-on` (default `error`) exists. Skip rules with `--ignore SKL008,SKL004`.

## SKL001

**Missing or invalid frontmatter name/description** (error). No `---` block,
unclosed block, unparseable line, missing or non-string `name`/`description`,
name over 64 chars. Unquoted descriptions containing `: ` are a warning because
strict YAML parsers reject them. Claude Code loads a skill with broken
frontmatter with empty metadata, so it can never be matched by description.

## SKL002

**Name not kebab-case or not matching the folder** (warning).

## SKL003

**Description too long or too short.** Error above the 1,536-char listing cap
(`--entry-cap`), warning above the 1,024-char Agent Skills spec limit, warning
above 500 chars (budget cost), warning below 40 chars.

## SKL004

**Vague description** (warning). Phrases such as "helps with", "various tasks",
"and more", "general purpose", "a tool for".

## SKL005

**No trigger phrases** (warning). No "use when ..." clause and no quoted phrases.

## SKL006

**Colliding skill has no "Do NOT use for" line** (warning). Fires for skills in a
collision pair (SKL013) whose description has no routing negative ("do not use",
"not for", "instead of", ...).

## SKL007

**Critical keywords past the cut-off** (warning). The first trigger clause starts
after `--cutoff` characters (default 250). 250 is front-loading guidance, not a
documented limit; the documented hard cap is 1,536.

## SKL008

**Body too large** (info). Over 500 lines (matches the documented advice to keep
`SKILL.md` under 500 lines) or about 5,000 tokens (`chars / 4`).

## SKL009

**Dead relative link or missing referenced file** (warning). Markdown links and
backticked paths such as `scripts/x.py`, `references/y.md`. Ignores URLs, anchors,
`mailto:` and code fences. Backslash paths are accepted.

## SKL010

**Absolute personal path** (warning). `C:\Users\<name>`, `/home/<name>`,
`/Users/<name>`. Placeholder names (`user`, `you`, `example`, ...) are ignored.

## SKL011

**Secrets and API keys** (error). AWS, GitHub, Anthropic, OpenAI-style, Slack and
Google keys, private-key blocks, bearer tokens, and generic `api_key = "..."`
assignments with placeholder filtering. Matches are redacted in output.
This is a fast heuristic, not a replacement for a dedicated secret scanner.

## SKL012

**Duplicate skill name across scopes** (warning). Only one copy can win.

## SKL013

**Trigger collision above threshold** (warning). See below.

## SKL014

**Script not executable or missing shebang** (warning). Files in `scripts/`.
The executable-bit check is skipped on Windows, where it is meaningless.

## SKL015

**Description phrased as instructions** (warning). First-person or second-person
openings ("I help you ...", "You are ...", "Please ...").

## Collision maths

For every pair of skills, tokens are taken from `name + description` (lowercase,
stop-words removed, light stemming).

- **Jaccard** = `|A ∩ B| / |A ∪ B|` on the token sets.
- **Cosine** over TF-IDF vectors: `tf = 1 + ln(count)`, `idf = ln((1+N)/(1+df)) + 1`.
- **score** = `max(jaccard, cosine)`; a pair is reported at `score >= --threshold`
  (default 0.45). Pairs sharing an identical quoted / listed trigger phrase are
  always reported.

The default threshold is a starting point. Raise it to cut noise, lower it to be
strict, and see which pairs you are willing to disambiguate with a
"Do NOT use for" line.

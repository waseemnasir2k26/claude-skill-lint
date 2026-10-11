"""SKL001, SKL002, SKL012: frontmatter validity, naming, duplicates."""
from __future__ import annotations

import os
import re
from collections import defaultdict

from ..model import display_path
from . import make, rule

KEBAB = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


@rule("SKL001", "Missing or invalid frontmatter name/description", "error")
def skl001(ctx):
    for s in ctx.skills:
        if not s.present:
            yield make("SKL001", s, "No YAML frontmatter: file must start with '---'.",
                       suggestion="Add a frontmatter block with `name:` and `description:`.")
            continue
        for err in s.errors:
            yield make("SKL001", s, f"Frontmatter problem: {err}. Claude Code then loads the skill with empty metadata and cannot match it.", 1,
                       "Fix the YAML so every line is `key: value`.")
        for key in ("name", "description"):
            v = s.data.get(key)
            if key not in s.data or v in ("", None):
                yield make("SKL001", s, f"Frontmatter is missing a non-empty `{key}`.", s.line_of(key),
                           f"Add `{key}:` to the frontmatter.")
            elif not isinstance(v, str):
                yield make("SKL001", s, f"`{key}` must be a string, found {type(v).__name__}.",
                           s.line_of(key), f"Make `{key}` a plain string.")
        if len(s.name) > 64:
            yield make("SKL001", s, f"`name` is {len(s.name)} chars; the Agent Skills spec caps it at 64.",
                       s.line_of("name"), "Shorten the name to 64 chars or fewer.")
        if "description" in s.plain_colon:
            yield make("SKL001", s,
                       "`description` is an unquoted value containing ': ' which strict YAML parsers reject.",
                       s.line_of("description"),
                       "Wrap the description in quotes or use a `|` block scalar.", severity="warning")


@rule("SKL002", "Name not kebab-case or not matching folder", "warning")
def skl002(ctx):
    for s in ctx.skills:
        n = s.name
        if not n:
            continue
        if not KEBAB.match(n):
            yield make("SKL002", s, f"Name `{n}` is not lowercase kebab-case.", s.line_of("name"),
                       f"Rename to `{re.sub(r'[^a-z0-9]+', '-', n.lower()).strip('-')}`.")
        if n != s.folder:
            fix = (f"Rename the folder to `{n}` or set `name: {s.folder}`." if KEBAB.match(n)
                   else f"Set `name: {s.folder}` (or rename the folder) so name and folder agree.")
            yield make("SKL002", s, f"Name `{n}` does not match its folder `{s.folder}`.", s.line_of("name"), fix)


@rule("SKL012", "Duplicate skill name across scopes", "warning")
def skl012(ctx):
    groups = defaultdict(list)
    for s in ctx.skills:
        if s.name:
            groups[s.name].append(s)
    for name, items in sorted(groups.items()):
        uniq = {os.path.normcase(os.path.realpath(i.path)): i for i in items}
        if len(uniq) < 2:
            continue
        where = ", ".join(sorted(display_path(i.dir) for i in uniq.values()))
        for i in uniq.values():
            yield make("SKL012", i, f"Skill name `{name}` is defined {len(uniq)} times ({where}).",
                       i.line_of("name"), "Rename one copy or delete the shadowed one; only one can win.")

"""SKL009, SKL010, SKL014: links, personal paths, scripts."""
from __future__ import annotations

import os
import re
import sys

from . import make, rule

FENCE = re.compile(r"^\s*(```|~~~)")
MD_LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
BACKTICK_PATH = re.compile(
    r"`((?:\./)?(?:scripts|references|assets|templates|examples|docs|resources)/[\w.\-/]+\.[A-Za-z0-9]{1,6})`")
PERSONAL = [
    re.compile(r"[A-Za-z]:[\\/]+Users[\\/]+([^\\/\s\"'`<>|*?]+)", re.I),
    re.compile(r"(?<![\w.])/home/([A-Za-z0-9._-]+)"),
    re.compile(r"(?<![\w.])/Users/([A-Za-z0-9._ -]+?)(?=/)"),
]
PLACEHOLDER_USERS = {"user", "username", "you", "name", "your-name", "yourname", "example", "me", "<user>",
                     "public", "default", "all users", "runner", "$user", "%username%", "{user}", "x", "foo"}


def _prose_lines(skill):
    """Yield (line_no, text) for body lines outside code fences, with frontmatter offset."""
    in_fence = False
    for i, line in enumerate(skill.body.split("\n")):
        if FENCE.match(line):
            in_fence = not in_fence
            continue
        if not in_fence:
            yield skill.body_start_line + i, line


def _all_lines(skill):
    for i, line in enumerate(skill.text.replace("\r\n", "\n").split("\n")):
        yield i + 1, line


@rule("SKL009", "Dead relative link or missing referenced file", "warning")
def skl009(ctx):
    for s in ctx.skills:
        seen = set()
        for ln, line in _prose_lines(s):
            targets = [m.group(1) for m in MD_LINK.finditer(line)] + [m.group(1) for m in BACKTICK_PATH.finditer(line)]
            for t in targets:
                t = t.split("#")[0].split("?")[0]
                if not t or re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", t) or t.startswith(("/", "~", "<", "$", "{")):
                    continue
                if t in seen:
                    continue
                seen.add(t)
                if not (s.dir / t.replace("\\", "/")).exists():
                    yield make("SKL009", s, f"Referenced file `{t}` does not exist.", ln,
                               f"Create `{t}` or fix the path (relative to the skill folder).")


@rule("SKL010", "Absolute personal path", "warning")
def skl010(ctx):
    for s in ctx.skills:
        for ln, line in _all_lines(s):
            for rx in PERSONAL:
                m = rx.search(line)
                if m and m.group(1).strip().lower() not in PLACEHOLDER_USERS:
                    yield make("SKL010", s, f"Hard-coded personal path `{m.group(0)}` will break on other machines.",
                               ln, "Use a relative path, `~`, `${CLAUDE_PLUGIN_ROOT}` or an env var.")
                    break


SCRIPT_EXT = {".sh", ".bash", ".py", ".rb", ".pl", ".js", ".mjs"}
SHEBANG_EXT = {".sh", ".bash", ".py", ".rb", ".pl"}


@rule("SKL014", "Script not executable or missing shebang", "warning")
def skl014(ctx):
    posix = os.name != "nt" and not sys.platform.startswith("win")
    for s in ctx.skills:
        sd = s.dir / "scripts"
        if not sd.is_dir():
            continue
        for p in sorted(sd.rglob("*")):
            if not p.is_file() or p.suffix.lower() not in SCRIPT_EXT:
                continue
            rel = p.relative_to(s.dir).as_posix()
            try:
                head = p.read_bytes()[:2]
            except OSError:
                continue
            if p.suffix.lower() in SHEBANG_EXT and head != b"#!":
                yield make("SKL014", s, f"`{rel}` has no shebang line (#!...).", 1,
                           f"Add `#!/usr/bin/env {'python3' if p.suffix == '.py' else 'bash'}` as the first line.")
            if posix and not os.access(p, os.X_OK):
                yield make("SKL014", s, f"`{rel}` is not executable.", 1, f"Run `chmod +x {rel}`.")

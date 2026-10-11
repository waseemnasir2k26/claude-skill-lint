"""Core data model: skills, findings, options and the shared lint context."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from .parse import parse_skill_text

SEVERITIES = ("error", "warning", "info")

CONTEXT_TOKENS = {"200k": 200_000, "1m": 1_000_000}
DEFAULT_FRACTION = 0.01      # docs: listing budget scales at 1% of the context window
CHARS_PER_TOKEN = 4          # assumption (docs give a fraction, not a character count)
ENTRY_CAP = 1536             # docs: description + when_to_use capped at 1,536 chars per entry


def budget_for(context: str = "200k", fraction: float = DEFAULT_FRACTION) -> int:
    return int(CONTEXT_TOKENS[context] * fraction * CHARS_PER_TOKEN)


@dataclass
class Options:
    budget_chars: int = budget_for("200k")
    entry_cap: int = ENTRY_CAP    # per-skill description cap in the listing (0 = none)
    target_len: int = 200         # length used by the "after fix" simulation
    desc_min: int = 40
    desc_warn: int = 500
    desc_hard: int = 1024         # Agent Skills spec limit for `description`
    cutoff: int = 250             # trigger/routing info should start before this char
    max_body_lines: int = 500
    max_body_tokens: int = 5000
    collision_threshold: float = 0.45
    ignore: tuple = ()
    suggestions: bool = False


@dataclass
class Finding:
    rule: str
    severity: str
    message: str
    path: str
    line: int = 1
    suggestion: str = ""

    def to_dict(self):
        return {"rule": self.rule, "severity": self.severity, "message": self.message,
                "path": self.path, "line": self.line, "suggestion": self.suggestion}


@dataclass
class Skill:
    path: Path
    folder: str
    scope: str
    text: str
    present: bool
    data: dict
    key_lines: dict
    errors: list
    plain_colon: set
    body: str
    body_start_line: int

    @property
    def dir(self) -> Path:
        return self.path.parent

    @property
    def name(self) -> str:
        v = self.data.get("name")
        return v.strip() if isinstance(v, str) else ""

    @property
    def description(self) -> str:
        """Listing text: `description` plus `when_to_use` (Claude Code lists them together)."""
        v = self.data.get("description")
        text = " ".join(v.split()) if isinstance(v, str) else ""
        w = self.data.get("when_to_use")
        if isinstance(w, str) and w.strip():
            text = (text + " " + " ".join(w.split())).strip()
        return text

    @property
    def label(self) -> str:
        return self.name or self.folder

    def line_of(self, key: str) -> int:
        return self.key_lines.get(key, 1)


def load_skill(path: Path, scope: str = "") -> Skill:
    raw = path.read_bytes().decode("utf-8", errors="replace")
    p = parse_skill_text(raw)
    return Skill(path=path, folder=path.parent.name, scope=scope or str(path.parent.parent),
                 text=raw, present=p.present, data=p.data, key_lines=p.key_lines,
                 errors=p.errors, plain_colon=p.plain_colon, body=p.body,
                 body_start_line=p.body_start_line)


_SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv"}


def discover(paths, max_depth: int = 6):
    """Yield (SKILL.md path, scope) for every skill found under *paths*."""
    seen = set()
    for root in paths:
        root = Path(root)
        if root.is_file():
            cands = [root]
        else:
            cands = []
            base_depth = len(root.parts)
            for dirpath, dirnames, filenames in os.walk(root):
                dirnames[:] = sorted(d for d in dirnames if d not in _SKIP_DIRS)
                if len(Path(dirpath).parts) - base_depth > max_depth:
                    dirnames[:] = []
                for f in filenames:
                    if f == "SKILL.md":
                        cands.append(Path(dirpath) / f)
        for c in sorted(cands):
            key = os.path.normcase(os.path.realpath(c))
            if key in seen:
                continue
            seen.add(key)
            yield c, str(root)


def default_paths():
    out = []
    for p in (Path.cwd() / ".claude" / "skills", Path.home() / ".claude" / "skills"):
        if p.is_dir() and p not in out:
            out.append(p)
    return out


def display_path(path) -> str:
    """Forward-slash path, relative to cwd when possible, home shown as ~."""
    p = Path(path)
    try:
        return p.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except (ValueError, OSError):
        pass
    try:
        return "~/" + p.resolve().relative_to(Path.home().resolve()).as_posix()
    except (ValueError, OSError):
        return p.as_posix()


class Context:
    def __init__(self, skills, opts: Options):
        self.skills = skills
        self.opts = opts
        self._collisions = None
        self._budget = None

    def collisions(self):
        if self._collisions is None:
            from .collide import find_collisions
            self._collisions = find_collisions(self.skills, self.opts.collision_threshold)
        return self._collisions

    def budget(self):
        if self._budget is None:
            from .budget import simulate
            self._budget = simulate(self.skills, self.opts)
        return self._budget

    def effective_cutoff(self) -> int:
        return self.opts.cutoff

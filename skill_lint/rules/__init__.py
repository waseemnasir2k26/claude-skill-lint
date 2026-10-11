"""Rule registry. Each rule is ``fn(ctx) -> iterable[Finding]``."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from ..model import Finding, display_path


@dataclass
class Rule:
    id: str
    title: str
    severity: str
    fn: Callable


RULES: dict = {}


def rule(rule_id: str, title: str, severity: str):
    def deco(fn):
        RULES[rule_id] = Rule(rule_id, title, severity, fn)
        return fn
    return deco


def make(rule_id: str, skill, message: str, line: int = 1, suggestion: str = "", severity: str = ""):
    sev = severity or RULES[rule_id].severity
    return Finding(rule_id, sev, message, display_path(skill.path), line, suggestion)


# Import for side effects (registration). Order = rule id order in reports.
from . import frontmatter, description, body, links, secrets, collisions  # noqa: E402,F401


def run_all(ctx):
    out = []
    for rid in sorted(RULES):
        if rid in ctx.opts.ignore:
            continue
        out.extend(RULES[rid].fn(ctx))
    out.sort(key=lambda f: (f.path, f.line, f.rule))
    return out

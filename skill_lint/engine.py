"""Glue: discover skills, run rules, return a Result."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .model import Context, Options, default_paths, discover, load_skill
from .rules import RULES, run_all


@dataclass
class Result:
    skills: list
    findings: list
    ctx: Context
    paths: list

    def count(self, severity):
        return sum(1 for f in self.findings if f.severity == severity)


def load_skills(paths):
    skills = []
    for p, scope in discover(paths):
        skills.append(load_skill(Path(p), scope))
    return skills


def analyze(paths, opts: Options) -> Result:
    paths = [Path(p) for p in paths] or default_paths()
    skills = load_skills(paths)
    ctx = Context(skills, opts)
    findings = run_all(ctx)
    return Result(skills, findings, ctx, paths)


def rule_table():
    return [(r.id, r.severity, r.title) for r in (RULES[k] for k in sorted(RULES))]

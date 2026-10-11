"""Command line interface."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .budget import simulate_fixed
from .engine import analyze, rule_table
from .model import CONTEXT_TOKENS, DEFAULT_FRACTION, ENTRY_CAP, Options, budget_for
from .report import FORMATS

SEV_RANK = {"info": 0, "warning": 1, "error": 2}


def _common(p):
    p.add_argument("paths", nargs="*", help="skill folders or SKILL.md files "
                   "(default: ./.claude/skills and ~/.claude/skills)")
    p.add_argument("--context", choices=sorted(CONTEXT_TOKENS), default="200k",
                   help="context window used to derive the listing budget (default: 200k)")
    p.add_argument("--budget-fraction", type=float, default=DEFAULT_FRACTION,
                   help="share of the context window given to the skill listing (default 0.01 = 1%%)")
    p.add_argument("--budget-chars", type=int, default=None,
                   help="fixed listing budget in characters (overrides --context/--budget-fraction)")
    p.add_argument("--entry-cap", type=int, default=ENTRY_CAP,
                   help="per-skill description cap in the listing (default 1536; 0 = none)")
    p.add_argument("--target-len", type=int, default=200, help="description length used for the 'after fix' simulation")
    p.add_argument("--cutoff", type=int, default=250, help="trigger info should appear before this character (SKL007)")
    p.add_argument("--threshold", type=float, default=0.45, help="collision score threshold (default 0.45)")
    p.add_argument("--max-body-lines", type=int, default=500)
    p.add_argument("--ignore", default="", help="comma-separated rule ids to skip, e.g. SKL008,SKL004")


def _opts(a) -> Options:
    budget = a.budget_chars if a.budget_chars else budget_for(a.context, a.budget_fraction)
    return Options(
        budget_chars=budget, entry_cap=a.entry_cap, target_len=a.target_len,
        cutoff=a.cutoff, collision_threshold=a.threshold, max_body_lines=a.max_body_lines,
        ignore=tuple(x.strip().upper() for x in a.ignore.split(",") if x.strip()),
        suggestions=getattr(a, "fix_suggestions", False),
    )


def build_parser():
    ap = argparse.ArgumentParser(prog="claude-skill-lint",
                                 description="Lint Claude Code SKILL.md packs: frontmatter, triggers, "
                                             "listing budget, collisions, links, secrets.")
    ap.add_argument("--version", action="version", version=f"claude-skill-lint {__version__}")
    sub = ap.add_subparsers(dest="cmd")

    c = sub.add_parser("check", help="run all rules")
    _common(c)
    c.add_argument("--format", choices=sorted(FORMATS), default="text")
    c.add_argument("--fix-suggestions", action="store_true", help="print a suggested fix under each finding")
    c.add_argument("--fail-on", choices=["error", "warning", "info", "never"], default="error")
    c.add_argument("--output", "-o", help="write to a file instead of stdout")

    b = sub.add_parser("budget", help="simulate the skill listing and show what gets cut")
    _common(b)
    b.add_argument("--format", choices=["text", "json"], default="text")

    k = sub.add_parser("collisions", help="list skill pairs whose triggers overlap")
    _common(k)
    k.add_argument("--format", choices=["text", "json"], default="text")

    r = sub.add_parser("report", help="write a self-contained HTML summary")
    _common(r)
    r.add_argument("--out", default="skill-lint-report.html")

    sub.add_parser("rules", help="list all rules")
    return ap


def _write(text: str, dest):
    if dest:
        Path(dest).write_text(text, encoding="utf-8", newline="\n")
    else:
        sys.stdout.write(text)


def _budget_text(result, opts) -> str:
    b = result.ctx.budget()
    fixed = simulate_fixed(result.skills, opts)
    from .report.text import budget_text
    lines = [budget_text(b, fixed, opts.target_len), ""]
    rows = sorted(b.entries, key=lambda e: (-e.recovers, e.name))
    shown = [e for e in rows if e.recovers > 0][:30]
    if shown:
        lines.append(f"{'skill':<34} {'status':<10} {'desc':>5} {'shown':>6} {'fix recovers':>13}")
        for e in shown:
            lines.append(f"{e.name[:34]:<34} {e.status:<10} {e.desc_len:>5} {e.shown_len:>6} {e.recovers:>13}")
        total = sum(e.recovers for e in b.entries)
        lines.append(f"{'total recoverable':<34} {'':<10} {'':>5} {'':>6} {total:>13}")
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    ap = build_parser()
    a = ap.parse_args(argv)
    if a.cmd is None:
        ap.print_help()
        return 0
    if a.cmd == "rules":
        for rid, sev, title in rule_table():
            print(f"{rid}  {sev:<8} {title}")
        return 0
    opts = _opts(a)
    result = analyze(a.paths, opts)
    if not result.skills:
        searched = ", ".join(str(p) for p in result.paths) or "(no default skill folders found)"
        print(f"claude-skill-lint: no SKILL.md files found in {searched}", file=sys.stderr)
        return 2

    if a.cmd == "check":
        fixed = simulate_fixed(result.skills, opts)
        _write(FORMATS[a.format](result, opts, fixed), a.output)
        if a.fail_on == "never":
            return 0
        worst = max((SEV_RANK[f.severity] for f in result.findings), default=-1)
        return 1 if worst >= SEV_RANK[a.fail_on] else 0

    if a.cmd == "budget":
        if a.format == "json":
            import json
            obj = result.ctx.budget().to_dict()
            fb = simulate_fixed(result.skills, opts).to_dict()
            fb.pop("entries", None)
            obj["after_fix"] = fb
            _write(json.dumps(obj, indent=2) + "\n", None)
        else:
            _write(_budget_text(result, opts), None)
        return 0

    if a.cmd == "collisions":
        cols = result.ctx.collisions()
        if a.format == "json":
            import json
            _write(json.dumps([c.to_dict() for c in cols], indent=2) + "\n", None)
        elif not cols:
            _write(f"No skill pairs at or above threshold {opts.collision_threshold}.\n", None)
        else:
            out = [f"{len(cols)} colliding pairs (threshold {opts.collision_threshold}):"]
            for c in cols:
                extra = f"  shared triggers: {', '.join(c.shared_triggers[:3])}" if c.shared_triggers else ""
                out.append(f"  {c.score:.2f}  {c.a.label}  <->  {c.b.label}  "
                           f"(jaccard {c.jaccard:.2f}, cosine {c.cosine:.2f}; terms: {', '.join(c.shared_terms[:4])}){extra}")
            _write("\n".join(out) + "\n", None)
        return 0

    if a.cmd == "report":
        fixed = simulate_fixed(result.skills, opts)
        _write(FORMATS["html"](result, opts, fixed), a.out)
        print(f"wrote {a.out}")
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""SKL008: body size / progressive disclosure."""
from __future__ import annotations

from . import make, rule


def approx_tokens(text: str) -> int:
    return (len(text) + 3) // 4


@rule("SKL008", "Body too large (progressive disclosure)", "info")
def skl008(ctx):
    o = ctx.opts
    for s in ctx.skills:
        lines = len(s.body.splitlines())
        toks = approx_tokens(s.body)
        if lines > o.max_body_lines:
            yield make("SKL008", s, f"Body is {lines} lines (> {o.max_body_lines}).", s.body_start_line,
                       "Keep SKILL.md short; move detail into references/ files loaded on demand.")
        elif toks > o.max_body_tokens:
            yield make("SKL008", s, f"Body is about {toks} tokens (> {o.max_body_tokens}).", s.body_start_line,
                       "Split reference material into separate files linked from SKILL.md.")

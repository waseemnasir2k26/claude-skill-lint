"""SKL013: trigger collisions above threshold."""
from __future__ import annotations

from . import make, rule


@rule("SKL013", "Trigger collision above threshold", "warning")
def skl013(ctx):
    for c in ctx.collisions():
        extra = f"; shared triggers: {', '.join(repr(t) for t in c.shared_triggers[:3])}" if c.shared_triggers else ""
        for me, other in ((c.a, c.b), (c.b, c.a)):
            yield make("SKL013", me,
                       f"Collides with `{other.label}` (score {c.score:.2f}, jaccard {c.jaccard:.2f}, cosine {c.cosine:.2f}){extra}.",
                       me.line_of("description"),
                       f"Make the two descriptions mutually exclusive or merge `{me.label}` and `{other.label}`.")

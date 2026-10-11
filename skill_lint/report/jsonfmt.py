from __future__ import annotations

import json

from .. import __version__


def to_obj(result, opts, fixed=None) -> dict:
    obj = {
        "tool": "claude-skill-lint", "version": __version__,
        "skills": len(result.skills),
        "summary": {"errors": result.count("error"), "warnings": result.count("warning"),
                    "info": result.count("info")},
        "findings": [f.to_dict() for f in result.findings],
        "collisions": [c.to_dict() for c in result.ctx.collisions()],
        "budget": result.ctx.budget().to_dict(),
    }
    if fixed is not None:
        fb = fixed.to_dict()
        fb.pop("entries", None)
        obj["budget_after_fix"] = fb
    return obj


def render(result, opts, fixed=None) -> str:
    return json.dumps(to_obj(result, opts, fixed), indent=2) + "\n"

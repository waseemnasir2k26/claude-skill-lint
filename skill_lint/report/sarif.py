from __future__ import annotations

import json

from .. import __version__
from ..rules import RULES

LEVEL = {"error": "error", "warning": "warning", "info": "note"}


def to_obj(result, opts, fixed=None) -> dict:
    rules = [{
        "id": r.id,
        "name": r.id,
        "shortDescription": {"text": r.title},
        "helpUri": f"https://github.com/waseemnasir2k26/claude-skill-lint/blob/main/docs/rules.md#{r.id.lower()}",
        "defaultConfiguration": {"level": LEVEL[r.severity]},
    } for r in (RULES[k] for k in sorted(RULES))]
    index = {r["id"]: i for i, r in enumerate(rules)}
    results = []
    for f in result.findings:
        uri = f.path.replace("\\", "/")
        res = {
            "ruleId": f.rule,
            "ruleIndex": index[f.rule],
            "level": LEVEL[f.severity],
            "message": {"text": f.message + (f" Fix: {f.suggestion}" if f.suggestion else "")},
            "locations": [{"physicalLocation": {
                "artifactLocation": {"uri": uri},
                "region": {"startLine": max(1, f.line)},
            }}],
        }
        results.append(res)
    return {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [{
            "tool": {"driver": {
                "name": "claude-skill-lint",
                "version": __version__,
                "informationUri": "https://github.com/waseemnasir2k26/claude-skill-lint",
                "rules": rules,
            }},
            "results": results,
        }],
    }


def render(result, opts, fixed=None) -> str:
    return json.dumps(to_obj(result, opts, fixed), indent=2) + "\n"

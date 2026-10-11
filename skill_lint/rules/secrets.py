"""SKL011: leaked secrets in SKILL.md."""
from __future__ import annotations

import re

from . import make, rule

PATTERNS = [
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("GitHub token", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{30,}\b")),
    ("GitHub fine-grained token", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{30,}\b")),
    ("Anthropic API key", re.compile(r"\bsk-ant-[A-Za-z0-9_\-]{20,}")),
    ("OpenAI-style API key", re.compile(r"\bsk-[A-Za-z0-9]{32,}\b")),
    ("Slack token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b")),
    ("Private key block", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----")),
    ("Bearer token", re.compile(r"\bBearer\s+[A-Za-z0-9._\-]{30,}")),
]
GENERIC = re.compile(
    r"""(?i)\b(api[_-]?key|secret|token|passwd|password|client[_-]?secret)\b["']?\s*[:=]\s*["']?([A-Za-z0-9_\-/+=.]{16,})""")
PLACEHOLDER = re.compile(r"(?i)(your|xxx|example|sample|placeholder|changeme|dummy|<|\$\{|\$[A-Z_]|\{\{|%[A-Z_]+%|\*\*\*|\.\.\.)")


def redact(v: str) -> str:
    return v[:4] + "***" if len(v) > 4 else "***"


@rule("SKL011", "Secret or API key in skill", "error")
def skl011(ctx):
    for s in ctx.skills:
        for i, line in enumerate(s.text.replace("\r\n", "\n").split("\n"), 1):
            hit = None
            for label, rx in PATTERNS:
                m = rx.search(line)
                if m:
                    hit = (label, m.group(0))
                    break
            if hit is None:
                m = GENERIC.search(line)
                if m and not PLACEHOLDER.search(m.group(2)) and not PLACEHOLDER.search(line[m.start():m.end() + 6]):
                    hit = (f"hard-coded {m.group(1).lower()}", m.group(2))
            if hit:
                yield make("SKL011", s, f"Possible {hit[0]}: `{redact(hit[1])}`.", i,
                           "Remove it, rotate the credential, and read it from an environment variable.")

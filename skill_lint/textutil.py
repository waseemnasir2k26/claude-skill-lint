"""Tokenising and trigger-phrase helpers shared by rules and collision maths."""
from __future__ import annotations

import re

STOPWORDS = frozenset("""
a about above after all also an and any are as at be because been before being but by can could do does
each for from had has have how if in into is it its just may more most must no not of on one only or other
our out over should so some such than that the their then there these they this those to up use used uses
using via was we were what when where whenever which while who will with would you your
skill skills claude user users tool tools help helps
""".split())

TRIGGER_MARKER = re.compile(
    r"\b(use (?:this )?(?:skill )?(?:when|whenever|for|if|to)|triggers?(?: on| when| phrases?)?\b|"
    r"invoke (?:when|for|this)|activate (?:when|for)|when (?:the )?(?:user|you|someone)|"
    r"whenever|if (?:the )?user|should be used|call (?:this )?(?:when|for))",
    re.I,
)
QUOTED = re.compile(r"[\"“]([^\"”\n]{3,80})[\"”]|'([^'\n]{4,80})'")
NEGATIVE_ROUTE = re.compile(
    r"\b(do not use|don't use|dont use|not for|never use|do not trigger|instead of|rather than|skip (?:for|when))\b",
    re.I)


def stem(w: str) -> str:
    """Very light stemmer: -ing / -ed on long words, then a plural -s."""
    for suf in ("ing", "ed"):
        if len(w) > len(suf) + 4 and w.endswith(suf):
            w = w[: -len(suf)]
            break
    if len(w) > 3 and w.endswith("s") and not w.endswith(("ss", "us", "is")):
        w = w[:-1]
    return w


def tokens(text: str) -> list:
    out = []
    for w in re.findall(r"[a-z0-9][a-z0-9+#.\-]*", text.lower()):
        w = w.strip(".-")
        if len(w) < 3 or w in STOPWORDS or w.isdigit():
            continue
        out.append(stem(w))
    return out


def trigger_phrases(desc: str) -> list:
    """Quoted phrases plus comma-separated items after a 'Trigger(s):' marker."""
    found = []
    for m in QUOTED.finditer(desc):
        s = (m.group(1) or m.group(2) or "").strip().lower()
        if s:
            found.append(s)
    m = re.search(r"triggers?(?: on| phrases?)?\s*[:\-]\s*(.+?)(?:\.\s|$)", desc, re.I)
    if m:
        for part in re.split(r",|;|\bor\b", m.group(1)):
            part = part.strip(" \"'“”.").lower()
            if 3 <= len(part) <= 60:
                found.append(part)
    seen, res = set(), []
    for f in found:
        if f not in seen:
            seen.add(f)
            res.append(f)
    return res


def first_trigger_pos(desc: str):
    """Character offset where trigger/routing info starts, or None."""
    positions = []
    m = TRIGGER_MARKER.search(desc)
    if m:
        positions.append(m.start())
    q = QUOTED.search(desc)
    if q:
        positions.append(q.start())
    return min(positions) if positions else None

"""SKL003-SKL007, SKL015: description quality and routing."""
from __future__ import annotations

import re

from ..textutil import NEGATIVE_ROUTE, TRIGGER_MARKER, QUOTED, first_trigger_pos
from . import make, rule

VAGUE = [
    "helps with", "help with", "various tasks", "various things", "different things", "and more",
    "general purpose", "general-purpose", "a tool for", "utility for", "useful for", "assists with",
    "miscellaneous", "misc", "etc.", "whatever you need", "any task", "all kinds of",
]
FIRST_PERSON = re.compile(
    r"^\s*(i\b|i'm\b|i'll\b|i can\b|you (?:are|will|should|must|can)\b|please\b|let me\b|help me\b|my\b|we\b)",
    re.I)


@rule("SKL003", "Description too long or too short", "warning")
def skl003(ctx):
    o = ctx.opts
    for s in ctx.skills:
        d = s.description
        if not d:
            continue
        n = len(d)
        line = s.line_of("description")
        if o.entry_cap and n > o.entry_cap:
            yield make("SKL003", s, f"Description (+ when_to_use) is {n} chars; Claude Code cuts each listing entry at {o.entry_cap}.",
                       line, f"Cut to {o.entry_cap} chars or fewer; put the key use case first.", severity="error")
        elif n > o.desc_hard:
            yield make("SKL003", s, f"Description is {n} chars; the Agent Skills spec limit is {o.desc_hard}.",
                       line, f"Cut to {o.desc_hard} chars or fewer; move detail into the body.")
        elif n > o.desc_warn:
            yield make("SKL003", s, f"Description is {n} chars (> {o.desc_warn}): it eats listing budget and risks being dropped.",
                       line, f"Trim to about {o.target_len}-{o.desc_warn} chars; keep trigger phrases first.")
        elif n < o.desc_min:
            yield make("SKL003", s, f"Description is only {n} chars (< {o.desc_min}): too little to route on.",
                       line, "Say what it does and when to use it, with 2-3 trigger phrases.")


@rule("SKL004", "Vague description", "warning")
def skl004(ctx):
    for s in ctx.skills:
        d = s.description.lower()
        hits = [v for v in VAGUE if re.search(r"(?<![a-z])" + re.escape(v) + r"(?![a-z])", d)]
        if hits:
            yield make("SKL004", s, "Vague wording: " + ", ".join(f"'{h}'" for h in hits[:4]) + ".",
                       s.line_of("description"),
                       "Replace with the concrete task, file type or tool the skill handles.")


@rule("SKL005", "No trigger phrases", "warning")
def skl005(ctx):
    for s in ctx.skills:
        d = s.description
        if not d:
            continue
        if not TRIGGER_MARKER.search(d) and not QUOTED.search(d):
            yield make("SKL005", s, "Description has no 'use when' clause or quoted trigger phrases.",
                       s.line_of("description"),
                       'Add e.g. `Use when the user asks to "…", "…", or mentions …`.')


@rule("SKL006", "Colliding skill has no 'Do NOT use for' line", "warning")
def skl006(ctx):
    partners = {}
    for c in ctx.collisions():
        partners.setdefault(id(c.a), (c.a, []))[1].append(c.b.label)
        partners.setdefault(id(c.b), (c.b, []))[1].append(c.a.label)
    for _, (s, others) in sorted(partners.items(), key=lambda kv: kv[1][0].label):
        if s.description and not NEGATIVE_ROUTE.search(s.description):
            yield make("SKL006", s, "Overlaps with " + ", ".join(f"`{o}`" for o in sorted(set(others))[:4])
                       + " but has no routing line.", s.line_of("description"),
                       "Append `Do NOT use for: <other task> -> <other-skill>.`")


@rule("SKL007", "Critical keywords too deep in the description", "warning")
def skl007(ctx):
    cut = ctx.effective_cutoff()
    for s in ctx.skills:
        d = s.description
        if not d or len(d) <= cut:
            continue
        pos = first_trigger_pos(d)
        if pos is not None and pos > cut:
            yield make("SKL007", s,
                       f"Trigger/routing text starts at char {pos}, past the {cut}-char front-loading target; it is the first thing lost when text is cut.",
                       s.line_of("description"),
                       f"Move the 'Use when ...' clause into the first {cut} chars.")
        neg = NEGATIVE_ROUTE.search(d)
        if neg and neg.start() > cut and pos is None:
            yield make("SKL007", s, f"'Do NOT use' routing starts at char {neg.start()}, past the {cut}-char front-loading target.",
                       s.line_of("description"), "Shorten the lead-in so routing survives truncation.")


@rule("SKL015", "Description written as instructions, not when-to-use", "warning")
def skl015(ctx):
    for s in ctx.skills:
        d = s.description
        if d and FIRST_PERSON.match(d):
            yield make("SKL015", s, "Description is first-person / instruction-style ('" + d[:28] + "...').",
                       s.line_of("description"),
                       "Write in third person: what the skill does and when Claude should pick it.")

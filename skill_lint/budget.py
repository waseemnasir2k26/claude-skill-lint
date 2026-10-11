"""Skill-listing budget simulator.

What the Claude Code docs say (https://code.claude.com/docs/en/skills, section
"Skill descriptions are cut short", checked 2026-10):

* the listing always contains every skill NAME;
* when many skills are installed, descriptions are DROPPED to fit a character
  budget (least-used skills first); the budget scales at 1% of the model's
  context window and is adjustable with `skillListingBudgetFraction` or the
  `SLASH_COMMAND_TOOL_CHAR_BUDGET` env var (fixed character count);
* each entry's combined `description` + `when_to_use` text is capped at 1,536
  characters (`skillListingMaxDescChars`).

What the docs do NOT say is how many characters 1% of a window is, or the exact
line format, so this module is a *model* with every number overridable:

1. name-only entry  = "- " + name + newline
2. full entry       = "- " + name + ": " + min(description, entry_cap) + newline
3. all names are always listed, even if that alone exceeds the budget
4. descriptions are then added in listing order while they fit; the first one
   that does not fit, and every one after it, is dropped (name-only). Real
   Claude Code drops least-invoked first, which cannot be known offline, so the
   listing order (paths in the order given, alphabetical inside) stands in.
"""
from __future__ import annotations

from dataclasses import dataclass, field

NAME_ONLY = len("- ") + len("\n")
SEP = len(": ")


@dataclass
class Entry:
    skill: object
    name: str
    desc_len: int               # combined description + when_to_use length
    status: str = "full"        # full | capped | name-only
    shown_len: int = 0
    recovers: int = 0           # chars saved if the description is trimmed to the fix target

    def name_cost(self):
        return NAME_ONLY + len(self.name)

    def full_cost(self, cap):
        d = min(self.desc_len, cap) if cap else self.desc_len
        return self.name_cost() + (SEP + d if d else 0)


@dataclass
class BudgetResult:
    budget: int
    entry_cap: int
    names_cost: int
    total_full: int             # listing size if the budget did not exist
    total_after: int
    uniform_fit_len: int        # longest description every skill could have and still fit (0 = names alone overflow)
    entries: list = field(default_factory=list)

    @property
    def full(self):
        return [e for e in self.entries if e.status == "full"]

    @property
    def capped(self):
        return [e for e in self.entries if e.status == "capped"]

    @property
    def name_only(self):
        return [e for e in self.entries if e.status == "name-only"]

    @property
    def described(self):
        return [e for e in self.entries if e.status != "name-only"]

    def to_dict(self):
        return {
            "budget_chars": self.budget, "entry_cap": self.entry_cap,
            "skills": len(self.entries), "names_cost_chars": self.names_cost,
            "total_chars_full": self.total_full, "total_chars_after": self.total_after,
            "uniform_fit_len": self.uniform_fit_len,
            "with_description": len(self.described), "name_only_count": len(self.name_only),
            "capped": [e.name for e in self.capped],
            "name_only": [e.name for e in self.name_only],
            "entries": [{"name": e.name, "status": e.status, "description_chars": e.desc_len,
                         "shown_chars": e.shown_len, "fix_recovers_chars": e.recovers}
                        for e in self.entries],
        }


def simulate(skills, opts, desc_override=None) -> BudgetResult:
    """Simulate the listing. *desc_override(skill, length) -> length* adjusts lengths."""
    entries = []
    for s in skills:
        if not s.name and not s.description:
            continue
        dl = len(s.description)
        if desc_override is not None:
            dl = desc_override(s, dl)
        entries.append(Entry(s, s.label, dl))
    cap = opts.entry_cap
    budget = opts.budget_chars
    names_cost = sum(e.name_cost() for e in entries)
    total_full = sum(e.full_cost(cap) for e in entries)

    used = names_cost
    exhausted = False
    for e in entries:
        extra = e.full_cost(cap) - e.name_cost()
        if not exhausted and extra > 0 and used + extra <= budget:
            used += extra
            e.shown_len = min(e.desc_len, cap) if cap else e.desc_len
            e.status = "capped" if cap and e.desc_len > cap else "full"
        elif extra == 0:
            e.status, e.shown_len = "full", 0   # nothing to show; no description exists
        else:
            exhausted = True
            e.status, e.shown_len = "name-only", 0
    for e in entries:
        e.recovers = max(0, e.desc_len - opts.target_len)

    # longest uniform description length that lets every skill keep a description
    fit = 0
    if names_cost <= budget:
        lo, hi = 0, max((min(e.desc_len, cap) if cap else e.desc_len for e in entries), default=0)
        while lo < hi:
            mid = (lo + hi + 1) // 2
            cost = names_cost + sum(SEP + min(e.desc_len, mid) for e in entries if e.desc_len)
            if cost <= budget:
                lo = mid
            else:
                hi = mid - 1
        fit = lo
    return BudgetResult(budget, cap, names_cost, total_full, used, fit, entries)


def simulate_fixed(skills, opts):
    """Re-run the simulation as if every description were trimmed to opts.target_len."""
    return simulate(skills, opts, desc_override=lambda s, dl: min(dl, opts.target_len))

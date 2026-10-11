from __future__ import annotations


def budget_text(b, fixed=None, target=0) -> str:
    n = len(b.entries)
    lines = [
        f"Skill listing budget: {b.budget:,} chars (per-entry cap {b.entry_cap or 'none'})",
        f"  skills: {n}   names alone: {b.names_cost:,} chars   with every description: {b.total_full:,} chars"
        + (f" ({b.total_full / b.budget * 100:.0f}% of budget)" if b.budget else ""),
    ]
    if b.names_cost > b.budget:
        lines.append("  WARNING: the skill names alone exceed the budget.")
    if not b.name_only and not b.capped:
        lines.append("  result: everything fits; every skill keeps its full description.")
    else:
        lines.append(f"  result: {len(b.described)} keep a description, {len(b.name_only)} are name-only"
                     f" (listing {b.total_after:,} chars)")
        if b.capped:
            lines.append(f"  {len(b.capped)} descriptions exceed the {b.entry_cap}-char entry cap and are cut")
        lines.append(f"  to keep every description you would need <= {b.uniform_fit_len} chars each"
                     if b.uniform_fit_len else "  no uniform description length fits: reduce the number of skills")
    if b.name_only:
        lines.append("  name-only (Claude sees no description): " + ", ".join(e.name for e in b.name_only[:15])
                     + (" ..." if len(b.name_only) > 15 else ""))
    if fixed is not None:
        gained = len(fixed.described) - len(b.described)
        lines.append(f"  if every description were trimmed to <= {target} chars: "
                     f"{len(fixed.described)} keep a description, {len(fixed.name_only)} name-only "
                     f"-> {gained} more skills described")
    return "\n".join(lines)


def render(result, opts, fixed=None) -> str:
    out = []
    for f in result.findings:
        out.append(f"{f.path}:{f.line}: {f.severity} {f.rule} {f.message}")
        if opts.suggestions and f.suggestion:
            out.append(f"    fix: {f.suggestion}")
    if out:
        out.append("")
    e, w, i = result.count("error"), result.count("warning"), result.count("info")
    out.append(f"{len(result.skills)} skills checked: {e} errors, {w} warnings, {i} info")
    out.append("")
    out.append(budget_text(result.ctx.budget(), fixed, opts.target_len))
    return "\n".join(out) + "\n"

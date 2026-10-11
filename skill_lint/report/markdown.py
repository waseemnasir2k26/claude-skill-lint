from __future__ import annotations


def _cell(s: str) -> str:
    return str(s).replace("|", "\\|").replace("\n", " ")


def render(result, opts, fixed=None) -> str:
    b = result.ctx.budget()
    out = ["# claude-skill-lint report", ""]
    out.append(f"**{len(result.skills)} skills** - {result.count('error')} errors, "
               f"{result.count('warning')} warnings, {result.count('info')} info")
    out.append("")
    out.append("## Listing budget")
    out.append("")
    out.append(f"- Budget: {b.budget:,} chars; names alone: {b.names_cost:,}; with every description: {b.total_full:,}")
    out.append(f"- With a description: {len(b.described)}, name-only: {len(b.name_only)}, over the entry cap: {len(b.capped)}")
    if b.name_only:
        out.append("- Name-only: " + ", ".join(f"`{e.name}`" for e in b.name_only[:30]))
    if fixed is not None:
        out.append(f"- After trimming descriptions to {opts.target_len} chars: "
                   f"{len(fixed.described)} with a description, {len(fixed.name_only)} name-only")
    out.append("")
    out.append("## Findings")
    out.append("")
    if not result.findings:
        out.append("No findings.")
    else:
        out.append("| Severity | Rule | Location | Message |")
        out.append("|---|---|---|---|")
        for f in result.findings:
            out.append(f"| {f.severity} | {f.rule} | `{_cell(f.path)}:{f.line}` | {_cell(f.message)} |")
    cols = result.ctx.collisions()
    if cols:
        out += ["", "## Trigger collisions", "", "| A | B | Score | Jaccard | Cosine |", "|---|---|---|---|---|"]
        for c in cols[:25]:
            out.append(f"| `{c.a.label}` | `{c.b.label}` | {c.score:.2f} | {c.jaccard:.2f} | {c.cosine:.2f} |")
    return "\n".join(out) + "\n"

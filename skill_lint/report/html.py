from __future__ import annotations

from html import escape

CSS = """
:root{--bg:#fbf8f2;--fg:#1c1b19;--mut:#6b675f;--line:#e4ddd0;--err:#b3261e;--warn:#9a5b00;--info:#2a5d9f;--ok:#2e7d32}
@media (prefers-color-scheme:dark){:root{--bg:#161512;--fg:#f0ece3;--mut:#a39d90;--line:#35322b;--err:#ff8a80;--warn:#ffb74d;--info:#90caf9;--ok:#81c784}}
body{background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,sans-serif;margin:0;padding:24px 16px}
main{max-width:980px;margin:auto}h1{font-size:1.6rem}h2{margin-top:2rem;font-size:1.15rem}
table{border-collapse:collapse;width:100%;font-size:.88rem}td,th{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}
.error{color:var(--err)}.warning{color:var(--warn)}.info{color:var(--info)}code{font-size:.85em}
.bar{display:flex;height:18px;border-radius:4px;overflow:hidden;background:var(--line);margin:8px 0}
.bar span{display:block}.f{background:var(--ok)}.t{background:var(--warn)}.d{background:var(--err)}
.sum{display:flex;gap:24px;flex-wrap:wrap}.sum b{font-size:1.6rem;display:block}
"""


def render(result, opts, fixed=None) -> str:
    b = result.ctx.budget()
    n = max(1, len(b.entries))
    pf, pt, pd = len(b.full) / n * 100, len(b.capped) / n * 100, len(b.name_only) / n * 100
    rows = "".join(
        f"<tr><td class='{escape(f.severity)}'>{escape(f.severity)}</td><td>{escape(f.rule)}</td>"
        f"<td><code>{escape(f.path)}:{f.line}</code></td><td>{escape(f.message)}"
        + (f"<br><small>Fix: {escape(f.suggestion)}</small>" if f.suggestion else "") + "</td></tr>"
        for f in result.findings) or "<tr><td colspan=4>No findings.</td></tr>"
    crows = "".join(
        f"<tr><td><code>{escape(c.a.label)}</code></td><td><code>{escape(c.b.label)}</code></td>"
        f"<td>{c.score:.2f}</td><td>{c.jaccard:.2f}</td><td>{c.cosine:.2f}</td></tr>"
        for c in result.ctx.collisions()[:50]) or "<tr><td colspan=5>No collisions above threshold.</td></tr>"
    brow = "".join(
        f"<tr><td><code>{escape(e.name)}</code></td><td>{escape(e.status)}</td><td>{e.desc_len}</td>"
        f"<td>{e.shown_len}</td><td>{e.recovers}</td></tr>"
        for e in sorted(b.entries, key=lambda e: (-e.recovers, e.name))[:60])
    after = ""
    if fixed is not None:
        after = (f"<p>With every description trimmed to {opts.target_len} chars: {len(fixed.described)} described, "
                 f"{len(fixed.name_only)} name-only.</p>")
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Skill Lint Report</title>
<style>{CSS}</style></head><body><main>
<h1>claude-skill-lint report</h1>
<div class="sum"><div><b>{len(result.skills)}</b>skills</div><div><b class="error">{result.count('error')}</b>errors</div>
<div><b class="warning">{result.count('warning')}</b>warnings</div><div><b class="info">{result.count('info')}</b>info</div></div>
<h2>Listing budget</h2>
<p>Budget {b.budget:,} chars; the listing needs {b.total_full:,} chars with every description (names alone: {b.names_cost:,}).
Described {len(b.described)}, name-only {len(b.name_only)}, over the entry cap {len(b.capped)}.</p>
<div class="bar" role="img" aria-label="full / capped / name-only"><span class="f" style="width:{pf:.1f}%"></span><span class="t" style="width:{pt:.1f}%"></span><span class="d" style="width:{pd:.1f}%"></span></div>
{after}
<table><tr><th>Skill</th><th>Status</th><th>Desc chars</th><th>Shown</th><th>Fix recovers</th></tr>{brow}</table>
<h2>Findings</h2>
<table><tr><th>Severity</th><th>Rule</th><th>Location</th><th>Message</th></tr>{rows}</table>
<h2>Trigger collisions</h2>
<table><tr><th>A</th><th>B</th><th>Score</th><th>Jaccard</th><th>Cosine</th></tr>{crows}</table>
</main></body></html>
"""

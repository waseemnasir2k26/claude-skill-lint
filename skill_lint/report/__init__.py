"""Output renderers: text, json, sarif, md, html."""
from __future__ import annotations

from . import html, jsonfmt, markdown, sarif, text

FORMATS = {
    "text": text.render,
    "json": jsonfmt.render,
    "sarif": sarif.render,
    "md": markdown.render,
    "html": html.render,
}

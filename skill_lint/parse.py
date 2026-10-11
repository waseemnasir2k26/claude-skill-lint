"""Small, dependency-free parser for SKILL.md frontmatter (a YAML subset).

Supports plain / quoted scalars, block scalars (| and >), inline and block
lists, and one level of nested mappings (e.g. ``metadata:``). Anything it
cannot understand is reported in ``errors`` instead of raising.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

_KEY_RE = re.compile(r"""^("[^"]+"|'[^']+'|[^\s:#'"\-\[][^:]*?|-?[^\s:#][^:]*?)\s*:(?:\s+(.*))?$""")


@dataclass
class Parsed:
    present: bool = False
    data: dict = field(default_factory=dict)
    key_lines: dict = field(default_factory=dict)
    errors: list = field(default_factory=list)
    plain_colon: set = field(default_factory=set)
    body: str = ""
    body_start_line: int = 1


def normalize(text: str) -> str:
    return text.lstrip("﻿").replace("\r\n", "\n").replace("\r", "\n")


def parse_skill_text(text: str) -> Parsed:
    text = normalize(text)
    lines = text.split("\n")
    out = Parsed(body=text)
    if not lines or lines[0].strip() != "---":
        return out
    out.present = True
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() in ("---", "..."):
            end = i
            break
    if end is None:
        out.errors.append("frontmatter opened with '---' but never closed")
        out.body = ""
        return out
    out.body = "\n".join(lines[end + 1:])
    out.body_start_line = end + 2
    _parse_block(lines[1:end], 2, out, out.data, out.key_lines, top=True)
    return out


def _indent_of(line: str) -> int:
    return len(line) - len(line.lstrip(" \t"))


def _parse_block(lines, first_line_no, out, data, klines, top=False):
    i = 0
    n = len(lines)
    while i < n:
        raw = lines[i]
        if not raw.strip() or raw.lstrip().startswith("#"):
            i += 1
            continue
        if raw[0] in " \t":
            out.errors.append(f"line {first_line_no + i}: unexpected indentation")
            i += 1
            continue
        m = _KEY_RE.match(raw.rstrip())
        if not m:
            out.errors.append(f"line {first_line_no + i}: not a 'key: value' line")
            i += 1
            continue
        key = m.group(1).strip().strip("\"'")
        val = (m.group(2) or "").rstrip()
        klines[key] = first_line_no + i
        j = i + 1
        cont = []
        while j < n and (not lines[j].strip() or lines[j][0] in " \t"):
            cont.append(lines[j])
            j += 1
        while cont and not cont[-1].strip():
            cont.pop()
        i = j
        if val[:1] in ("|", ">") and re.match(r"^[|>][+-]?\d?$", val):
            data[key] = _block_scalar(val, cont)
        elif val == "":
            nonblank = [c for c in cont if c.strip()]
            if not nonblank:
                data[key] = ""
            elif nonblank[0].lstrip().startswith("- ") or nonblank[0].strip() == "-":
                data[key] = [c.strip()[2:].strip().strip("\"'") for c in nonblank if c.strip().startswith("-")]
            else:
                ind = min(_indent_of(c) for c in nonblank)
                sub = {}
                _parse_block([c[ind:] for c in cont], first_line_no + i - len(cont), out, sub, {})
                data[key] = sub
        elif val[0] in "\"'":
            data[key] = _quoted(val, cont, out, first_line_no + i - len(cont) - 1)
        elif val.startswith("["):
            joined = " ".join([val] + [c.strip() for c in cont])
            if "]" not in joined:
                out.errors.append(f"line {klines[key]}: unterminated inline list")
                data[key] = []
            else:
                inner = joined[1:joined.rindex("]")]
                data[key] = [p.strip().strip("\"'") for p in inner.split(",") if p.strip()]
        else:
            parts = [val] + [c.strip() for c in cont if c.strip()]
            plain = " ".join(parts)
            plain = re.sub(r"\s+#.*$", "", plain)
            if ": " in plain or plain.endswith(":"):
                out.plain_colon.add(key)
            data[key] = plain


def _block_scalar(header, cont):
    nonblank = [c for c in cont if c.strip()]
    if not nonblank:
        return ""
    ind = min(_indent_of(c) for c in nonblank)
    ls = [c[ind:] if c.strip() else "" for c in cont]
    if header[0] == "|":
        text = "\n".join(ls)
    else:
        paras, cur = [], []
        for line in ls:
            if line == "":
                paras.append(" ".join(cur))
                cur = []
            else:
                cur.append(line.strip())
        paras.append(" ".join(cur))
        text = "\n".join(p for p in paras)
    return text.rstrip("\n") if "+" not in header else text


def _quoted(val, cont, out, line_no):
    q = val[0]
    joined = " ".join([val] + [c.strip() for c in cont])
    body = joined[1:]
    res = []
    k = 0
    while k < len(body):
        ch = body[k]
        if q == '"' and ch == "\\" and k + 1 < len(body):
            nxt = body[k + 1]
            res.append({"n": "\n", "t": "\t", '"': '"', "\\": "\\"}.get(nxt, "\\" + nxt))
            k += 2
            continue
        if q == "'" and ch == "'" and body[k + 1:k + 2] == "'":
            res.append("'")
            k += 2
            continue
        if ch == q:
            return "".join(res)
        res.append(ch)
        k += 1
    out.errors.append(f"line {line_no}: unterminated quoted string")
    return "".join(res)

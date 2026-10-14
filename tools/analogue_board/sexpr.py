"""Minimal S-expression reader and writer for KiCad files.

Atoms come back as `Sym` (bare words) or `str` (quoted strings), lists as Python lists.
The writer emits KiCad's tab-indented layout closely enough that KiCad reads it unchanged.
"""

import re


class Sym(str):
    """A bare (unquoted) atom such as `pin`, `yes`, `1.27`."""


_TOKEN = re.compile(r'\s*(?:(\()|(\))|"((?:[^"\\]|\\.)*)"|([^\s()"]+))', re.S)


def parse(text):
    stack, cur = [], []
    pos = 0
    while True:
        m = _TOKEN.match(text, pos)
        if not m or m.end() == pos:
            break
        pos = m.end()
        lp, rp, qs, atom = m.groups()
        if lp:
            stack.append(cur)
            cur = []
        elif rp:
            done = cur
            cur = stack.pop()
            cur.append(done)
        elif qs is not None:
            cur.append(qs.encode().decode("unicode_escape") if "\\" in qs else qs)
        else:
            cur.append(Sym(atom))
    return cur[0] if len(cur) == 1 else cur


def quote(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def _atom(a):
    if isinstance(a, Sym):
        return str(a)
    if isinstance(a, bool):
        return "yes" if a else "no"
    if isinstance(a, (int,)):
        return str(a)
    if isinstance(a, float):
        s = f"{a:.4f}".rstrip("0").rstrip(".")
        return "0" if s in ("-0", "") else s
    return quote(str(a))


# Lists whose children stay on one line (short, leaf-only forms).
_INLINE = {"at", "xy", "size", "font", "stroke", "fill", "width", "type", "length", "offset", "color",
           "justify", "diameter", "uuid", "unit", "lib_id", "reference", "page", "hide", "start", "end",
           "mid", "center", "radius", "thickness", "bold", "italic", "exclude_from_sim", "in_bom",
           "on_board", "dnp", "fields_autoplaced", "mirror", "shape", "version", "generator",
           "generator_version", "paper", "embedded_fonts", "convert", "body_style", "margins", "span",
           "column_count", "column_widths", "row_heights", "border", "separators", "angle"}


def dumps(node, indent=0):
    if not isinstance(node, list):
        return _atom(node)
    head = node[0] if node else ""
    leaf = all(not isinstance(c, list) for c in node)
    if leaf or head in _INLINE and all(not isinstance(c, list) or c and c[0] in _INLINE for c in node):
        return "(" + " ".join(dumps(c) if isinstance(c, list) else _atom(c) for c in node) + ")"
    tab = "\t" * (indent + 1)
    parts = ["(" + _atom(head)]
    # keep leading atoms on the head line: (symbol "R" ...) / (pin passive line ...)
    i = 1
    while i < len(node) and not isinstance(node[i], list):
        parts[0] += " " + _atom(node[i])
        i += 1
    for c in node[i:]:
        if head == "pts" and isinstance(c, list):
            continue
        parts.append(tab + dumps(c, indent + 1))
    if head == "pts":
        parts = ["(pts " + " ".join(dumps(c) for c in node[1:]) + ")"]
        return parts[0]
    return "\n".join(parts) + "\n" + "\t" * indent + ")"


def find(node, head):
    """First child list with the given head, or None."""
    for c in node:
        if isinstance(c, list) and c and c[0] == head:
            return c
    return None


def find_all(node, head):
    return [c for c in node if isinstance(c, list) and c and c[0] == head]

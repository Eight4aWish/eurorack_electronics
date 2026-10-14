"""Load symbols from KiCad .kicad_sym libraries, flatten `extends`, and report pin geometry."""

import copy
import os
from functools import lru_cache

from sexpr import Sym, find, find_all, parse

KICAD_SYMBOLS = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols"


@lru_cache(maxsize=None)
def load_library(path):
    with open(path, encoding="utf-8") as f:
        tree = parse(f.read())
    return {c[1]: c for c in find_all(tree, "symbol")}


def library_path(lib, project_libs):
    if lib in project_libs:
        return project_libs[lib]
    return os.path.join(KICAD_SYMBOLS, lib + ".kicad_sym")


def _rename_units(sym, old, new):
    for c in sym:
        if isinstance(c, list) and c and c[0] == "symbol" and isinstance(c[1], str) and c[1].startswith(old + "_"):
            c[1] = new + c[1][len(old):]


def flat_symbol(lib_id, project_libs):
    """The symbol as it must appear in a schematic's lib_symbols: named Lib:Name, extends resolved."""
    lib, name = lib_id.split(":", 1)
    syms = load_library(library_path(lib, project_libs))
    sym = copy.deepcopy(syms[name])
    ext = find(sym, "extends")
    if ext:
        parent = flat_symbol(f"{lib}:{ext[1]}", project_libs)
        parent_name = parent[1].split(":", 1)[1]
        merged = copy.deepcopy(parent)
        # child properties override parent ones; everything else (units, pins) comes from the parent
        child_props = {p[1]: p for p in find_all(sym, "property")}
        for i, c in enumerate(merged):
            if isinstance(c, list) and c and c[0] == "property" and c[1] in child_props:
                merged[i] = child_props.pop(c[1])
        insert_at = max(i for i, c in enumerate(merged) if isinstance(c, list) and c and c[0] == "property") + 1
        for p in child_props.values():
            merged.insert(insert_at, p)
            insert_at += 1
        _rename_units(merged, parent_name, name)
        sym = merged
    sym[1] = lib_id
    return sym


class Pin:
    __slots__ = ("number", "name", "etype", "x", "y", "angle", "length", "hidden", "unit")

    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)

    def __repr__(self):
        return f"Pin({self.number} {self.name} {self.etype} u{self.unit} @({self.x},{self.y},{self.angle}){' hidden' if self.hidden else ''})"


def symbol_pins(lib_id, project_libs):
    """All pins of a symbol, body style 1, as Pin objects in library coordinates (y up)."""
    sym = flat_symbol(lib_id, project_libs)
    name = lib_id.split(":", 1)[1]
    pins = []
    for unit_sym in find_all(sym, "symbol"):
        suffix = unit_sym[1][len(name) + 1:]
        unit, style = (int(v) for v in suffix.split("_"))
        if style not in (0, 1):
            continue
        for p in find_all(unit_sym, "pin"):
            at = find(p, "at")
            hidden = any(c == "hide" for c in p if isinstance(c, Sym)) or bool(find(p, "hide") and find(p, "hide")[1:] in ([], ["yes"]))
            pins.append(Pin(number=str(find(p, "number")[1]), name=str(find(p, "name")[1]), etype=str(p[1]),
                            x=float(at[1]), y=float(at[2]), angle=int(float(at[3])) if len(at) > 3 else 0,
                            length=float(find(p, "length")[1]), hidden=hidden, unit=unit))
    return pins


def unit_count(lib_id, project_libs):
    return max(p.unit for p in symbol_pins(lib_id, project_libs)) or 1


def is_power_symbol(lib_id, project_libs):
    return find(flat_symbol(lib_id, project_libs), "power") is not None


def property_value(lib_id, prop, project_libs):
    for p in find_all(flat_symbol(lib_id, project_libs), "property"):
        if p[1] == prop:
            return p[2]
    return None

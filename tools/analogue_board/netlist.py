"""Read a KiCad s-expression netlist (kicad-cli sch export netlist --format kicadsexpr)."""

from sexpr import find, find_all, parse


def read_netlist(path):
    with open(path, encoding="utf-8") as f:
        tree = parse(f.read())
    nets = {}
    for n in find_all(find(tree, "nets"), "net"):
        name = find(n, "name")[1]
        nets[name] = sorted((find(nd, "ref")[1], find(nd, "pin")[1]) for nd in find_all(n, "node"))
    comps = {}
    for c in find_all(find(tree, "components"), "comp"):
        ref = find(c, "ref")[1]
        fields = {}
        for f in find_all(find(c, "fields") or [], "field"):
            fields[find(f, "name")[1]] = f[2] if len(f) > 2 and not isinstance(f[2], list) else ""
        for p in find_all(c, "property"):
            fields[find(p, "name")[1]] = find(p, "value")[1] if find(p, "value") else ""
        comps[ref] = {"value": find(c, "value")[1], "footprint": (find(c, "footprint") or [None, ""])[1],
                      "lib": find(find(c, "libsource"), "lib")[1] + ":" + find(find(c, "libsource"), "part")[1],
                      "fields": fields}
    return nets, comps

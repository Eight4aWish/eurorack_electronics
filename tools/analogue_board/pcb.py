"""Checkpoint 3: the PCB, generated from the schematic's netlist.

    python3 tools/analogue_board/pcb.py

Writes hardware/analogue_board/analogue_board.kicad_pcb:
- the 49.6 x 103 mm outline and a JLC 4-layer stack-up (JLC04161H-7628);
- every footprint in the netlist, from KiCad's library or the project's, with its nets
  and its link to the schematic symbol, so KiCad's "Update PCB from Schematic" recognises it;
- the parts placement.py fixes (edge strips, module sockets, power header) where it says;
- every other part parked beside the board, grouped by schematic sheet, until placed.

Then runs KiCad's DRC with the schematic-parity check and prints the courtyard area budget.
Board coordinates: placement.py's origin (the board's top-left corner) sits at (BX, BY) on the page.
"""

import json
import os
import subprocess
import sys
import uuid
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import placement as P  # noqa: E402
from sexpr import Sym, dumps, find, find_all, parse  # noqa: E402

HW = os.path.join(P.REPO, "hardware", "analogue_board")
NETLIST = os.path.join(HW, "output", "analogue_board.net")
OUT = os.path.join(HW, "analogue_board.kicad_pcb")
KICAD_CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
BX, BY = 30.0, 30.0          # the board's top-left corner on the A3 page
PARK_X0, PARK_X1 = 100.0, 405.0
NS = uuid.UUID("5f0c8a2e-7d1b-4f43-9a1e-3c2b6a9d4e10")


def S(*a):
    return [Sym(a[0]), *a[1:]]


def uid(*parts):
    return str(uuid.uuid5(NS, "/".join(str(p) for p in parts)))


# ------------------------------------------------------------------ netlist
def read():
    with open(NETLIST, encoding="utf-8") as f:
        tree = parse(f.read())
    comps = OrderedDict()
    for c in find_all(find(tree, "components"), "comp"):
        props = {find(p, "name")[1]: (find(p, "value") or [None, ""])[1] for p in find_all(c, "property")}
        sp = find(c, "sheetpath")
        comps[find(c, "ref")[1]] = {
            "fp": find(c, "footprint")[1], "value": find(c, "value")[1],
            "path": find(sp, "tstamps")[1] + find(c, "tstamps")[1],
            "sheet": find(sp, "names")[1], "sheetname": props.get("Sheetname", ""), "sheetfile": props.get("Sheetfile", ""),
            "attrs": [a for a in ("exclude_from_bom", "dnp") if a in props],
        }
    pin_net = {}
    names = []
    for n in find_all(find(tree, "nets"), "net"):
        name = find(n, "name")[1]
        names.append(name)
        for nd in find_all(n, "node"):
            pin_net[(find(nd, "ref")[1], find(nd, "pin")[1])] = name
    return comps, pin_net, names


# ------------------------------------------------------------------ footprints
_cache = {}


def library_footprint(libid):
    if libid not in _cache:
        lib, name = libid.split(":")
        d = os.path.join(HW, "analogue_board.pretty") if lib == "analogue_board" else os.path.join(P.KICAD_FP, lib + ".pretty")
        with open(os.path.join(d, name + ".kicad_mod"), encoding="utf-8") as f:
            _cache[libid] = parse(f.read())
    return _cache[libid]


def courtyard_box(fp):
    """(x0, y0, x1, y1) of the front courtyard, in footprint coordinates."""
    pts = []
    for g in fp:
        if not (isinstance(g, list) and g and str(g[0]) in ("fp_line", "fp_rect", "fp_poly", "fp_arc", "fp_circle")):
            continue
        lay = find(g, "layer")
        if not lay or lay[1] != "F.CrtYd":
            continue
        for key in ("start", "end", "mid"):
            n = find(g, key)
            if n:
                pts.append((float(n[1]), float(n[2])))
        pl = find(g, "pts")
        if pl:
            pts += [(float(p[1]), float(p[2])) for p in find_all(pl, "xy")]
        if str(g[0]) == "fp_circle":
            c, e = find(g, "center"), find(g, "end")
            r = ((float(e[1]) - float(c[1])) ** 2 + (float(e[2]) - float(c[2])) ** 2) ** 0.5
            pts += [(float(c[1]) - r, float(c[2]) - r), (float(c[1]) + r, float(c[2]) + r)]
    if not pts:
        return (-1.0, -1.0, 1.0, 1.0)
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return (min(xs), min(ys), max(xs), max(ys))


def _flip_layer(name):
    s = str(name)
    return s.replace("F.", "\0").replace("B.", "F.").replace("\0", "B.") if s[:2] in ("F.", "B.") else s


def to_world(local, at, rot, face):
    """Footprint-local point -> board point. KiCad: y down, positive angles counter-clockwise on
    screen; a deck-face (B) footprint is mirrored top-to-bottom in its own frame (y -> -y)."""
    import math
    lx, ly = local[0], (-local[1] if face == "B" else local[1])
    t = math.radians(rot)
    return (at[0] + lx * math.cos(t) + ly * math.sin(t), at[1] - lx * math.sin(t) + ly * math.cos(t))


def instance(ref, comp, at, rot, net_ids, pin_net, face="F"):
    """A board footprint node: the library footprint, renamed, placed (on either face), linked and
    with pad nets."""
    lib = library_footprint(comp["fp"])
    node = [Sym("footprint"), comp["fp"], S("layer", "B.Cu" if face == "B" else "F.Cu"), S("uuid", uid(ref)),
            S("at", round(at[0], 4), round(at[1], 4), *([rot] if rot else []))]
    counter = [0]
    flip = face == "B"

    def fresh(n):
        """Copy a subtree: fresh deterministic uuids; pad and text angles made absolute (KiCad stores
        them with the footprint angle added); on the deck face, y mirrored, layers swapped and text
        mirrored, as KiCad's own flip does."""
        if not isinstance(n, list):
            return n
        out = [fresh(c) for c in n]
        head = str(out[0]) if out and isinstance(out[0], Sym) else ""
        if flip and head in ("at", "start", "end", "mid", "center", "xy") and len(out) >= 3:
            out[2] = -float(out[2])
        if flip and head == "layer":
            out[1] = _flip_layer(out[1])
        if flip and head == "layers":
            out[1:] = [_flip_layer(l) for l in out[1:]]
        if flip and head == "effects":
            j = find(out, "justify")
            if j is None:
                out.append(S("justify", Sym("mirror")))
            elif Sym("mirror") not in j:
                j.append(Sym("mirror"))
        if head in ("pad", "property", "fp_text") and (rot or flip):
            a = find(out, "at")
            if a is not None:
                i = out.index(a)
                local = float(a[3]) if len(a) > 3 else 0.0
                out[i] = S("at", a[1], a[2], ((-local if flip else local) + rot) % 360)
        if head == "uuid":
            counter[0] += 1
            return S("uuid", uid(ref, counter[0]))
        return out

    body = []
    for c in lib[2:]:
        if not isinstance(c, list):
            continue
        h = str(c[0])
        if h in ("version", "generator", "generator_version", "layer"):
            continue
        c = fresh(c)
        if h == "property":
            if c[1] == "Reference":
                c[2] = ref
            elif c[1] == "Value":
                c[2] = comp["value"]
            if not find(c, "uuid"):
                c.insert(min(5, len(c)), S("uuid", uid(ref, "prop", c[1])))
        if h == "fp_text" and not find(c, "uuid"):
            counter[0] += 1
            c.append(S("uuid", uid(ref, "text", counter[0])))
        if h == "attr":
            c += [Sym(a) for a in comp["attrs"] if Sym(a) not in c]
        if h == "pad":
            net = pin_net.get((ref, str(c[1])))
            if net is not None:
                c.append(S("net", net_ids[net], net))
            if not find(c, "uuid"):
                counter[0] += 1
                c.append(S("uuid", uid(ref, "pad", c[1], counter[0])))
        body.append(c)
    # KiCad's order: descr, tags, properties, then the schematic link, then the rest
    if comp["attrs"] and not any(str(c[0]) == "attr" for c in body):
        body.append(S("attr", *[Sym(a) for a in comp["attrs"]]))
    head = [c for c in body if str(c[0]) in ("descr", "tags", "property")]
    rest = [c for c in body if str(c[0]) not in ("descr", "tags", "property")]
    link = [S("path", comp["path"]), S("sheetname", comp["sheetname"] or "/"), S("sheetfile", comp["sheetfile"])]
    return node + head + link + rest


# ------------------------------------------------------------------ fixed parts
def fixed_positions(comps):
    """ref -> ((x, y) of the footprint origin on the board, rotation, face)."""
    lay = P.layout("A")
    pos = {}
    for ref, key, fp in (("A101", "pico", "Pico2_Socket"), ("A102", "teensy", "Teensy41_Socket")):
        p1 = [p for p in lay[key]["pads"] if p[0] == "1"][0]   # footprint origin is pad 1
        pos[ref] = ((p1[1], p1[2]), 180, "F")
    pos["J901"] = ((P.STRIPS["left"]["outer"], P.strip_y(1)), 0, "F")
    pos["J902"] = ((P.STRIPS["right"]["outer"], P.strip_y(1)), 0, "F")
    pos["J201"] = (P.HEADER_PIN1, 0, "F")
    for ref, (x, y, rot, face) in P.anchor_positions().items():
        if ref in P.HOLE_GROUPS:          # wiring holes: the origin is hole 1
            pos[ref] = ((x, y), rot, face)
            continue
        x0, y0, x1, y1 = courtyard_box(library_footprint(comps[ref]["fp"]))
        cx, cy = to_world(((x0 + x1) / 2, (y0 + y1) / 2), (0, 0), rot, face)   # courtyard centre offset
        pos[ref] = ((x - cx, y - cy), rot, face)
    return pos


# ------------------------------------------------------------------ parking
def park(comps, fixed):
    """Shelf-pack every unfixed footprint beside the board, one block per schematic sheet."""
    groups = OrderedDict()
    for ref, c in comps.items():
        if ref not in fixed:
            groups.setdefault(c["sheet"], []).append(ref)
    pos, labels = {}, []
    x, y, col_w = PARK_X0, 25.0, 0.0
    for sheet, refs in groups.items():
        boxes = [(ref, courtyard_box(library_footprint(comps[ref]["fp"]))) for ref in refs]
        boxes.sort(key=lambda rb: -((rb[1][2] - rb[1][0]) * (rb[1][3] - rb[1][1])))
        width = 62.0
        if x + width > PARK_X1:
            raise SystemExit("parking area full")
        labels.append((sheet.strip("/") or "Root", x, y))
        cx, cy, shelf = x, y + 4.0, 0.0
        for ref, (x0, y0, x1, y1) in boxes:
            w, h = x1 - x0 + 0.3, y1 - y0 + 0.3
            if cx + w > x + width:
                cx, cy, shelf = x, cy + shelf, 0.0
            pos[ref] = ((cx - x0 + 0.15 - BX, cy - y0 + 0.15 - BY), 0, "F")
            cx += w
            shelf = max(shelf, h)
        y = cy + shelf + 6.0
        col_w = max(col_w, width)
        if y > 230:
            x, y, col_w = x + col_w + 8.0, 25.0, 0.0
    return pos, labels


# ------------------------------------------------------------------ board file
def stackup():
    def cu(name):
        return S("layer", name, S("type", "copper"), S("thickness", 0.035 if name in ("F.Cu", "B.Cu") else 0.0152))

    def diel(n, kind, t, mat):
        return S("layer", f"dielectric {n}", S("type", kind), S("thickness", t), S("material", mat),
                 S("epsilon_r", 4.4), S("loss_tangent", 0.02))
    return S("stackup",
             S("layer", "F.SilkS", S("type", "Top Silk Screen")), S("layer", "F.Paste", S("type", "Top Solder Paste")),
             S("layer", "F.Mask", S("type", "Top Solder Mask"), S("color", "Green"), S("thickness", 0.01)),
             cu("F.Cu"), diel(1, "prepreg", 0.2104, "7628"), cu("In1.Cu"), diel(2, "core", 1.065, "FR4"), cu("In2.Cu"),
             diel(3, "prepreg", 0.2104, "7628"), cu("B.Cu"),
             S("layer", "B.Mask", S("type", "Bottom Solder Mask"), S("color", "Green"), S("thickness", 0.01)),
             S("layer", "B.Paste", S("type", "Bottom Solder Paste")), S("layer", "B.SilkS", S("type", "Bottom Silk Screen")),
             S("copper_finish", "HAL lead-free"), S("dielectric_constraints", Sym("no")))


LAYERS = [(0, "F.Cu", "signal"), (4, "In1.Cu", "signal"), (6, "In2.Cu", "signal"), (2, "B.Cu", "signal"),
          (9, "F.Adhes", "user", "F.Adhesive"), (11, "B.Adhes", "user", "B.Adhesive"), (13, "F.Paste", "user"),
          (15, "B.Paste", "user"), (5, "F.SilkS", "user", "F.Silkscreen"), (7, "B.SilkS", "user", "B.Silkscreen"),
          (1, "F.Mask", "user"), (3, "B.Mask", "user"), (17, "Dwgs.User", "user", "User.Drawings"),
          (19, "Cmts.User", "user", "User.Comments"), (21, "Eco1.User", "user", "User.Eco1"),
          (23, "Eco2.User", "user", "User.Eco2"), (25, "Edge.Cuts", "user"), (27, "Margin", "user"),
          (31, "F.CrtYd", "user", "F.Courtyard"), (29, "B.CrtYd", "user", "B.Courtyard"), (35, "F.Fab", "user"),
          (33, "B.Fab", "user"), (39, "User.1", "user"), (41, "User.2", "user")]


def gr_text(s, x, y, layer="Cmts.User", size=1.5, tag="t"):
    return S("gr_text", s, S("at", round(x, 3), round(y, 3), 0), S("layer", layer), S("uuid", uid("text", tag, s, x, y)),
             S("effects", S("font", S("size", size, size), S("thickness", size * 0.15)), S("justify", Sym("left"))))


def gr_rect(a, b, layer, w=0.1, tag="r"):
    return S("gr_rect", S("start", round(a[0], 4), round(a[1], 4)), S("end", round(b[0], 4), round(b[1], 4)),
             S("stroke", S("width", w), S("type", Sym("default"))), S("fill", Sym("no")), S("layer", layer),
             S("uuid", uid("rect", tag, layer, a, b)))


def build():
    comps, pin_net, names = read()
    net_ids = {n: i + 1 for i, n in enumerate(names)}
    fixed = fixed_positions(comps)
    parked, labels = park(comps, fixed)
    pos = {**parked, **fixed}
    board = [Sym("kicad_pcb"), S("version", 20241229), S("generator", "analogue_board_pcb"), S("generator_version", "9.0"),
             S("general", S("thickness", 1.6), S("legacy_teardrops", Sym("no"))), S("paper", "A3"),
             S("title_block", S("title", "Analogue board Rev A"), S("rev", "A"), S("company", "Eight4aWish"),
               S("comment", 1, "Generated by tools/analogue_board/pcb.py from the schematic netlist"),
               S("comment", 2, "Checkpoint 3 (placement): parts beside the board are not yet placed")),
             [Sym("layers")] + [[l[0], l[1], Sym(l[2]), *l[3:]] for l in LAYERS],
             S("setup", stackup(), S("pad_to_mask_clearance", 0), S("allow_soldermask_bridges_in_footprints", Sym("no")),
               S("tenting", Sym("front"), Sym("back")), S("aux_axis_origin", BX, BY), S("grid_origin", BX, BY)),
             S("net", 0, "")]
    board += [S("net", net_ids[n], n) for n in names]
    for ref, comp in comps.items():
        (x, y), rot, face = pos[ref]
        board.append(instance(ref, comp, (BX + x, BY + y), rot, net_ids, pin_net, face))
    board.append(gr_rect((BX, BY), (BX + P.BOARD_W, BY + P.BOARD_H), "Edge.Cuts", 0.1, "outline"))
    # USB plug keep-outs and the parking-area labels, for the reviewer
    for key, m in P.layout("A").items():
        k = m["keepout"]
        board.append(gr_rect((BX + k[0], BY + k[1]), (BX + k[2], BY + k[3]), "Cmts.User", 0.1, "keepout-" + key))
    board.append(gr_text("USB plug keep-outs: nothing taller than ~8 mm", BX, BY + P.BOARD_H + 3, size=1.2, tag="ko"))
    for name, x, y in labels:
        board.append(gr_text(f"not yet placed: {name}", x, y, size=2.0, tag="park"))
    board.append(S("embedded_fonts", Sym("no")))
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(dumps(board) + "\n")
    return comps, fixed


def area_budget(comps):
    rows = {}
    for ref, c in comps.items():
        x0, y0, x1, y1 = courtyard_box(library_footprint(c["fp"]))
        name = c["fp"].split(":")[1]
        if name.startswith(("EdgeStrip", "Pico2", "Teensy41")):
            continue
        kind = ("wiring-field holes" if "WiringHoles" in name else "power header" if "IDC" in name else "SMT parts")
        n, a = rows.get(kind, (0, 0.0))
        rows[kind] = (n + 1, a + (x1 - x0) * (y1 - y0))
    # the module sockets occupy only their header rows: 2.54 mm + 0.5 mm courtyard per row
    rows["module header rows"] = (4, 2 * 3.04 * (19 * 2.54 + 3.04) + 2 * 3.04 * (23 * 2.54 + 3.04))
    usable = (P.STRIPS["right"]["inner"] - 0.85 - 0.25 - (P.STRIPS["left"]["inner"] + 0.85 + 0.25)) * P.BOARD_H
    total = sum(a for _, a in rows.values())
    print("Courtyard area budget:")
    for k, (n, a) in sorted(rows.items(), key=lambda kv: -kv[1][1]):
        print(f"  {k:22s} {n:4d} {a:7.0f} mm2")
    print(f"  total {total:.0f} mm2 against {usable:.0f} mm2 between the edge strips: {100 * total / usable:.0f}%")
    return rows, usable


def drc():
    rpt = os.path.join(HW, "output", "pcb_drc.json")
    r = subprocess.run([KICAD_CLI, "pcb", "drc", "--schematic-parity", "--format", "json", "--severity-all",
                        "-o", rpt, OUT], capture_output=True, text=True)
    if not os.path.exists(rpt):
        print(r.stdout, r.stderr)
        return None
    with open(rpt, encoding="utf-8") as f:
        d = json.load(f)
    parity = d.get("schematic_parity", [])
    print(f"Schematic parity: {len(parity)} issues")
    for p in parity[:20]:
        print("  ", p.get("type"), p.get("description"), [i.get("description") for i in p.get("items", [])][:2])
    # placement problems among parts already on the board (parked parts are off the board by design)
    on_board = lambda it: BX <= it["pos"]["x"] <= BX + P.BOARD_W and BY <= it["pos"]["y"] <= BY + P.BOARD_H  # noqa: E731
    kinds = ("courtyards_overlap", "holes_co_located", "hole_clearance", "item_on_disabled_layer", "malformed_courtyard",
             "missing_courtyard", "npth_inside_courtyard", "pth_inside_courtyard")
    found = [v for v in d.get("violations", []) if v.get("type") in kinds and all(on_board(i) for i in v.get("items", []))]
    print(f"Placement violations on the board: {len(found)}")
    for v in found[:30]:
        print("  ", v["type"], " / ".join(i.get("description", "") for i in v.get("items", [])))
    return d


def render():
    """3D renders of both faces into output/ (the deck face is seen from below, so it reads mirrored)."""
    outs = []
    for side, name in (("top", "placement_outward_face.png"), ("bottom", "placement_deck_face.png")):
        path = os.path.join(HW, "output", name)
        subprocess.run([KICAD_CLI, "pcb", "render", "--side", side, "--width", "900", "--height", "1700",
                        "--quality", "high", "--background", "opaque", "-o", path, OUT], capture_output=True, text=True)
        outs.append(path)
    print("Renders:", *outs, sep="\n  ")
    return outs


if __name__ == "__main__":
    comps, fixed = build()
    print(OUT)
    area_budget(comps)
    drc()
    render()

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

import autoplace  # noqa: E402
import placement as P  # noqa: E402
from sexpr import Sym, dumps, find, find_all, parse  # noqa: E402

HW = os.path.join(P.REPO, "hardware", "analogue_board")
NETLIST = os.path.join(HW, "output", "analogue_board.net")
OUT = os.path.join(HW, "analogue_board.kicad_pcb")
KICAD_CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
BX, BY = 30.0, 30.0          # the board's top-left corner on the A3 page
PARK_X0, PARK_X1 = 100.0, 405.0
NS = uuid.UUID("5f0c8a2e-7d1b-4f43-9a1e-3c2b6a9d4e10")
# reference designators kept off the silkscreen: the board is too dense for them, assembly does
# not need them, and they stay on the fab layers. ICs, connectors and hole groups keep theirs.
SILK_HIDDEN = {"R", "C", "D", "L", "FB", "Q", "TP", "FID", "JP"}


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
            "props": props,
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


def courtyard_rects(fp):
    """Front courtyard as rectangles in footprint coordinates: one per fp_rect (a module socket
    has two, its header rows), else the bounding box of the outline."""
    rects, other = [], []
    for g in fp:
        if not (isinstance(g, list) and g and str(g[0]) in ("fp_line", "fp_rect", "fp_poly", "fp_arc", "fp_circle")):
            continue
        lay = find(g, "layer")
        if not lay or lay[1] != "F.CrtYd":
            continue
        if str(g[0]) == "fp_rect":
            s, e = find(g, "start"), find(g, "end")
            rects.append((min(float(s[1]), float(e[1])), min(float(s[2]), float(e[2])),
                          max(float(s[1]), float(e[1])), max(float(s[2]), float(e[2]))))
        else:
            other.append(g)
    if other or not rects:
        rects.append(courtyard_box([None, None] + other) if other else courtyard_box(fp))
    return rects


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
                hole_group = comp["fp"].startswith("analogue_board:WiringHoles")   # labelled hole by hole instead
                if (ref.rstrip("0123456789") in SILK_HIDDEN or hole_group) and not find(c, "hide"):
                    c.insert(min(5, len(c)), S("hide", Sym("yes")))
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


# Routing rules. JLC's multilayer limits: via 0.2 mm drill / 0.45 mm pad; track and space 0.09-0.127 mm
# by their various pages, so 0.127 mm is the floor here on every layer. Signals at 0.15 mm put two
# tracks through each gap between module header pins (0.84 mm between 1.7 mm pads).
NET_CLASSES = [
    # name, track, clearance, via diameter, via drill, priority (lower wins)
    ("Default", 0.15, 0.15, 0.45, 0.2, 2147483647),
    ("Power", 0.3, 0.15, 0.6, 0.3, 0),
]
POWER_PATTERNS = ["GND", "+12V", "-12V", "+5VD", "+5VA", "+3V3D", "+3V3A", "MOD_5V", "/Power/*"]
RULES = {"min_clearance": 0.127, "min_track_width": 0.127, "min_via_diameter": 0.45, "min_through_hole_diameter": 0.2,
         "min_via_annular_width": 0.1, "min_hole_clearance": 0.25, "min_hole_to_hole": 0.25,
         "min_copper_edge_clearance": 0.5, "min_connection": 0.0, "min_microvia_diameter": 0.2,
         "min_microvia_drill": 0.1, "min_resolved_spokes": 2, "min_silk_clearance": 0.0, "min_text_height": 0.8,
         "min_text_thickness": 0.08, "max_error": 0.005, "solder_mask_to_copper_clearance": 0.0,
         "use_height_for_length_calcs": True}


def write_project_rules():
    """Merge the net classes and board minimums into the KiCad project file (build.py owns the rest)."""
    pro = os.path.join(HW, "analogue_board.kicad_pro")
    with open(pro, encoding="utf-8") as f:
        data = json.load(f)
    classes = [{"name": n, "track_width": t, "clearance": c, "via_diameter": vd, "via_drill": vh,
                "microvia_diameter": 0.3, "microvia_drill": 0.1, "diff_pair_gap": 0.2, "diff_pair_via_gap": 0.25,
                "diff_pair_width": 0.2, "line_style": 0, "bus_width": 12, "wire_width": 6,
                "pcb_color": "rgba(0, 0, 0, 0.000)", "schematic_color": "rgba(0, 0, 0, 0.000)", "priority": p}
               for n, t, c, vd, vh, p in NET_CLASSES]
    data["net_settings"] = {"classes": classes, "meta": {"version": 4}, "net_colors": None,
                            "netclass_assignments": None,
                            "netclass_patterns": [{"netclass": "Power", "pattern": p} for p in POWER_PATTERNS]}
    ds = data.setdefault("board", {}).setdefault("design_settings", {})
    ds.setdefault("rules", {}).update(RULES)
    ds["track_widths"] = [0.0, 0.127, 0.15, 0.2, 0.3, 0.5]
    ds["via_dimensions"] = [{"diameter": 0.0, "drill": 0.0}, {"diameter": 0.45, "drill": 0.2}, {"diameter": 0.6, "drill": 0.3}]
    with open(pro, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def ground_plane(net_ids):
    """Inner layer 1: one unbroken ground plane over the whole board (spec §10)."""
    m = 0.5   # copper to board edge
    pts = [(BX + m, BY + m), (BX + P.BOARD_W - m, BY + m), (BX + P.BOARD_W - m, BY + P.BOARD_H - m), (BX + m, BY + P.BOARD_H - m)]
    return S("zone", S("net", net_ids["GND"]), S("net_name", "GND"), S("layer", "In1.Cu"), S("uuid", uid("zone", "In1", "GND")),
             S("hatch", Sym("edge"), 0.5), S("connect_pads", S("clearance", 0.2)), S("min_thickness", 0.2),
             S("filled_areas_thickness", Sym("no")), S("fill", S("thermal_gap", 0.3), S("thermal_bridge_width", 0.3)),
             S("polygon", S("pts", *[S("xy", round(x, 4), round(y, 4)) for x, y in pts])))


def build():
    comps, pin_net, names = read()
    net_ids = {n: i + 1 for i, n in enumerate(names)}
    fixed = fixed_positions(comps)
    placer = autoplace.Placer(comps, pin_net, fixed, library_footprint, courtyard_rects, to_world)
    unplaced = placer.run([r for r in comps if r not in fixed])
    placed = {r: p for r, p in placer.pos.items()}
    parked, labels = park(comps, placed)
    pos = {**parked, **placed}
    faces = {"F": 0, "B": 0}
    for r, (_o, _rot, f) in placed.items():
        faces[f] += 1
    print(f"Placed {len(placed)} of {len(comps)} parts (outward face {faces['F']}, deck face {faces['B']}); "
          f"not placed: {len(unplaced)} {' '.join(sorted(unplaced)[:20])}")
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
    board.append(ground_plane(net_ids))
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
    return comps, placed


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
    # the module sockets occupy only their header rows (their courtyards)
    rows["module header rows"] = (4, sum((r[2] - r[0]) * (r[3] - r[1]) for ref in ("A101", "A102")
                                         for r in courtyard_rects(library_footprint(comps[ref]["fp"]))))
    # board area outside the edge strips' courtyards and the 0.65 mm edge slivers beside them
    usable = P.BOARD_W * P.BOARD_H - 2 * 0.65 * P.BOARD_H - sum(
        (r[2] - r[0]) * (r[3] - r[1]) for ref in ("J901", "J902") for r in courtyard_rects(library_footprint(comps[ref]["fp"])))
    total = sum(a for _, a in rows.values())
    print("Courtyard area budget:")
    for k, (n, a) in sorted(rows.items(), key=lambda kv: -kv[1][1]):
        print(f"  {k:22s} {n:4d} {a:7.0f} mm2")
    print(f"  total {total:.0f} mm2 against {usable:.0f} mm2 outside the edge strips (one face): {100 * total / usable:.0f}%")
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
    # project footprints leave out holes nothing uses (the Teensy's far-end pins, the right strip's
    # positions 11-15 and 26-30; checks.py confirms they are unconnected): KiCad reports each as a
    # pin with no pad, which is the intent
    comps = read()[0]
    intended = set()
    for ref, c in comps.items():
        if c["fp"].startswith("analogue_board:"):
            pads = {str(p[1]) for p in find_all(library_footprint(c["fp"]), "pad")}
            for n in range(1, 100):
                if str(n) not in pads:
                    intended.add(f"No pad found for pin {n} in schematic.|{ref}")
    parity = [p for p in d.get("schematic_parity", [])
              if not any(f"{p.get('description')}|{i.get('description', '').split()[-1]}" in intended
                         for i in p.get("items", []))]
    omitted = len(d.get("schematic_parity", [])) - len(parity)
    print(f"Schematic parity: {len(parity)} issues ({omitted} intended: holes left out where nothing connects)")
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


# maximum package height above the board, mm, by footprint name prefix (datasheet maxima, rounded up)
HEIGHTS = [("R_0402", 0.4), ("C_0402", 0.6), ("R_0603", 0.6), ("C_0603", 0.9), ("L_0603", 0.9), ("R_0805", 0.7),
           ("C_0805", 1.45), ("R_1206", 0.7), ("C_1206", 1.8), ("SOT-23-5", 1.45), ("SOT-23-6", 1.45), ("SOT-23", 1.2),
           ("D_SOD-323", 1.1), ("D_SMA", 2.45), ("SOIC", 1.75), ("TSSOP", 1.2), ("TO-252", 2.4), ("SMDIP", 4.3),
           ("L_Sunlord_SWPA5040", 4.2), ("JST_SH", 4.25), ("TestPoint", 0.1), ("Fiducial", 0.1), ("SolderJumper", 0.1),
           ("WiringHoles", 0.0), ("EdgeStrip", 0.0), ("IDC", 9.0), ("Pico2", 11.0), ("Teensy41", 11.0)]


def height(fp):
    name = fp.split(":")[1]
    for prefix, h in HEIGHTS:
        if name.startswith(prefix):
            return h
    raise KeyError(f"no height for {fp}")


def height_check(comps, placed):
    """Outward-face parts under a module body (the P4's envelope included) must be <= 2.5 mm;
    parts in a USB plug keep-out <= 8 mm. Uses each part's courtyard centre."""
    lay = P.layout("A")
    bodies = [lay[k]["body"] for k in ("p4", "pico", "teensy")]
    keepouts = [lay[k]["keepout"] for k in ("p4", "pico", "teensy")]
    inside = lambda pt, r: r[0] <= pt[0] <= r[2] and r[1] <= pt[1] <= r[3]  # noqa: E731
    bad = []
    for ref, ((x, y), rot, face) in placed.items():
        if face != "F" or ref in ("A101", "A102"):
            continue
        x0, y0, x1, y1 = courtyard_box(library_footprint(comps[ref]["fp"]))
        c = to_world(((x0 + x1) / 2, (y0 + y1) / 2), (x, y), rot, face)
        h = height(comps[ref]["fp"])
        if any(inside(c, b) for b in bodies) and h > 2.5:
            bad.append(f"{ref} {h} mm under a module")
        elif any(inside(c, k) for k in keepouts) and h > 8.0:
            bad.append(f"{ref} {h} mm in a USB keep-out")
    print(f"Height check: {len(bad)} problems" + ("".join(f"\n   {b}" for b in bad)))
    return bad


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
    write_project_rules()
    comps, placed = build()
    print(OUT)
    area_budget(comps)
    drc()
    height_check(comps, placed)
    render()

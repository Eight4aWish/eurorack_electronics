"""Write KiCad 9 hierarchical schematics from Python.

A `Project` owns a root `Sheet` and its sub-sheets. Each sheet places library symbols, draws wires,
labels, power symbols and no-connect flags, and records every pin it connects so that the
intended netlist can be compared with the one KiCad computes (see check_netlist.py).
"""

import math
import os
import uuid as uuidlib

from kicad_lib import flat_symbol, is_power_symbol, symbol_pins
from sexpr import Sym, dumps, find, find_all

GRID = 1.27
TWO_PIN = {"Device:R_Small", "Device:C_Small", "Device:L_Small", "Device:FerriteBead_Small"}
DIODE_2PIN = {"Device:D_TVS", "Diode:1N4148WS", "Diode:SS14", "Diode:SS34", "Device:D", "Device:D_Schottky"}
FONT = [Sym("font"), [Sym("size"), 1.27, 1.27]]


def new_uuid(seed):
    """Deterministic UUIDs so regenerating gives a stable file (and stable PCB links)."""
    return str(uuidlib.uuid5(uuidlib.NAMESPACE_URL, "analogue_board/" + seed))


def snap(v):
    return round(round(v / GRID) * GRID, 4)


def S(*items):
    return [Sym(items[0])] + list(items[1:])


def effects(justify=None, hide=False, size=1.27):
    e = [Sym("effects"), [Sym("font"), [Sym("size"), size, size]]]
    if justify:
        e.append([Sym("justify")] + [Sym(j) for j in justify.split()])
    if hide:
        e.append([Sym("hide"), Sym("yes")])
    return e


# ---------------------------------------------------------------- transforms

def _matrix(rot, mirror):
    """Library (y up) -> schematic (y down), following KiCad's SCH_SYMBOL::SetOrientation:
    start from the normal transform, rotate counter-clockwise rot/90 times, then mirror."""
    m = [[1, 0], [0, -1]]

    def apply(t):
        nonlocal m
        m = [[t[0][0] * m[0][0] + t[0][1] * m[1][0], t[0][0] * m[0][1] + t[0][1] * m[1][1]],
             [t[1][0] * m[0][0] + t[1][1] * m[1][0], t[1][0] * m[0][1] + t[1][1] * m[1][1]]]

    for _ in range((rot // 90) % 4):
        apply([[0, 1], [-1, 0]])
    if mirror == "x":
        apply([[1, 0], [0, -1]])
    elif mirror == "y":
        apply([[-1, 0], [0, 1]])
    return m


_DIRS = {0: (-1, 0), 180: (1, 0), 90: (0, -1), 270: (0, 1)}  # outward direction of a pin, library coords


class Placed:
    def __init__(self, sheet, lib_id, ref, at, rot, mirror, unit, pins):
        self.sheet, self.lib_id, self.ref, self.at, self.rot, self.mirror, self.unit = sheet, lib_id, ref, at, rot, mirror, unit
        self.m = _matrix(rot, mirror)
        self.pins = pins  # number -> Pin (this unit, plus unit-0 pins common to all units)

    def _xf(self, x, y):
        return (snap(self.at[0] + self.m[0][0] * x + self.m[0][1] * y),
                snap(self.at[1] + self.m[1][0] * x + self.m[1][1] * y))

    def p(self, number):
        pin = self.pins[str(number)]
        return self._xf(pin.x, pin.y)

    def out(self, number):
        """Unit vector pointing away from the symbol body at this pin, schematic coordinates."""
        dx, dy = _DIRS[self.pins[str(number)].angle % 360]
        return (round(self.m[0][0] * dx + self.m[0][1] * dy), round(self.m[1][0] * dx + self.m[1][1] * dy))

    def by_name(self, name):
        hits = [n for n, p in self.pins.items() if p.name == name]
        if len(hits) != 1:
            raise KeyError(f"{self.ref}: pin name {name!r} matches {hits}")
        return hits[0]


class Sheet:
    def __init__(self, project, name, filename, page, title, paper="A3", number=None):
        self.project, self.name, self.filename, self.page, self.title, self.paper = project, name, filename, page, title, paper
        self.number = number if number is not None else int(page)
        self.uuid = new_uuid("file/" + filename)
        self.symbol_uuid = new_uuid("sheet/" + filename)  # the sheet symbol on the root that instantiates this file
        self.items = []
        self.lib_ids = []
        self.counters = {}
        self.connections = []  # (ref, pin, net-or-None, endpoint) records for netlist checking
        self.placed = []
        self.subsheets = []
        self.segments = []
        self.junctions = set()
        self.label_points = []
        self.final_segments = []
        self._seq = 0

    # ------------------------------------------------------------ bookkeeping
    def _id(self, kind):
        self._seq += 1
        return new_uuid(f"{self.filename}/{kind}/{self._seq}")

    def path(self):
        root = self.project.root
        return f"/{root.uuid}" if self is root else f"/{root.uuid}/{self.symbol_uuid}"

    def next_ref(self, prefix):
        while True:
            n = self.counters.get(prefix, 0) + 1
            self.counters[prefix] = n
            ref = f"{prefix}{self.number * 100 + n}"
            if ref not in self.project.refs:
                return ref

    def claim_ref(self, ref, lib_id):
        """Register a reference; the same ref may be reused only for another unit of the same part."""
        owner = self.project.refs.get(ref)
        if owner is not None and owner != (lib_id, self.filename):
            raise ValueError(f"reference {ref} already used for {owner}, now {lib_id} on {self.filename}")
        self.project.refs[ref] = (lib_id, self.filename)

    def _use(self, lib_id):
        if lib_id not in self.lib_ids:
            self.lib_ids.append(lib_id)

    # ------------------------------------------------------------ symbols
    def place(self, lib_id, ref=None, value=None, at=(0, 0), rot=0, mirror=None, unit=1, footprint="",
              datasheet="", fields=None, in_bom=True, on_board=True, dnp=False, hide_value=False,
              hide_ref=False, prefix=None, ref_at=None, value_at=None, text_left=False):
        libs = self.project.project_libs
        self._use(lib_id)
        allpins = symbol_pins(lib_id, libs)
        pins = {p.number: p for p in allpins if p.unit in (0, unit)}
        if ref is None:
            ref = self.next_ref(prefix or "U")
        power = is_power_symbol(lib_id, libs)
        if not power:
            self.claim_ref(ref, lib_id)
        at = (snap(at[0]), snap(at[1]))
        pl = Placed(self, lib_id, ref, at, rot, mirror, unit, pins)
        node = [Sym("symbol"), S("lib_id", lib_id), S("at", at[0], at[1], rot)]
        if mirror:
            node.append(S("mirror", Sym(mirror)))
        node += [S("unit", unit), S("exclude_from_sim", Sym("no")), S("in_bom", Sym("yes" if in_bom else "no")),
                 S("on_board", Sym("yes" if on_board else "no")), S("dnp", Sym("yes" if dnp else "no")),
                 S("uuid", self._id("sym"))]
        lib_props = {p[1]: p for p in find_all(flat_symbol(lib_id, libs), "property")}
        field_angle = 90 if rot in (90, 270) else 0

        def lib_at(name, default):
            lp = lib_props.get(name)
            if lp is None:
                return default, None
            a = find(lp, "at")
            x, y = pl._xf(float(a[1]), float(a[2]))
            eff = find(lp, "effects")
            j = find(eff, "justify") if eff else None
            return (x, y), (" ".join(str(t) for t in j[1:]) if j else None)

        (rx, ry), rj = lib_at("Reference", (at[0] + 2.54, at[1] - 1.27))
        (vx, vy), vj = lib_at("Value", (at[0] + 2.54, at[1] + 1.27))
        if ref_at:
            (rx, ry), rj = ref_at, "left"
        if value_at:
            (vx, vy), vj = value_at, "left"
        if lib_id in TWO_PIN and not (ref_at or value_at):
            # small two-pin parts: text beside a vertical part, above/below a horizontal one
            if rot in (0, 180) and text_left:
                (rx, ry), rj = (at[0] - 2.54, at[1] - 0.762), "right"
                (vx, vy), vj = (at[0] - 2.54, at[1] + 1.778), "right"
            elif rot in (0, 180):
                (rx, ry), rj = (at[0] + 2.54, at[1] - 0.762), "left"
                (vx, vy), vj = (at[0] + 2.54, at[1] + 1.778), "left"
            else:
                d = 3.302 if lib_id in ("Device:C_Small", "Device:FerriteBead_Small") else 2.032
                (rx, ry), rj = (at[0], at[1] - d), None
                (vx, vy), vj = (at[0], at[1] + d), None
        elif lib_id in DIODE_2PIN and rot in (90, 270) and not (ref_at or value_at):
            # a vertical diode: text beside it, like a vertical resistor. At rot 90 KiCad draws the field turned
            # through 180° and mirrors its justification, so ask for the opposite side (found by rendering)
            sx, j = (-2.54, "right") if text_left else (2.54, "left")
            if rot == 90:
                j = {"left": "right", "right": "left"}[j]
            (rx, ry), rj = (at[0] + sx, at[1] - 1.27), j
            (vx, vy), vj = (at[0] + sx, at[1] + 1.27), j
        elif rot in (90, 270) and not power:
            rj = vj = None  # centred above/below a rotated part reads best
        if power:
            # horizontal text beyond the tip of a sideways power symbol (found by rendering every case)
            vj = (("right" if value in self.project.ground_nets else "left") if rot in (90, 270) else None)
        props = [("Reference", ref, (rx, ry), hide_ref or power, rj),
                 ("Value", value if value is not None else lib_id.split(":")[1], (vx, vy), hide_value, vj),
                 ("Footprint", footprint, at, True, None),
                 ("Datasheet", datasheet, at, True, None),
                 ("Description", "", at, True, None)]
        for k, v in (fields or {}).items():
            props.append((k, v, at, True, None))
        for k, v, (px, py), hide, j in props:
            node.append([Sym("property"), k, v, S("at", round(px, 4), round(py, 4), field_angle), effects(j, hide)])
        for p in allpins:
            if p.unit in (0, unit):
                node.append(S("pin", p.number, S("uuid", self._id("pin"))))
        node.append(S("instances", S("project", self.project.name,
                                     S("path", self.path(), S("reference", ref), S("unit", unit)))))
        self.items.append(node)
        self.placed.append(pl)
        return pl

    # ------------------------------------------------------------ drawing
    def wire(self, *pts):
        """Polyline of wire segments. Segments are kept apart from other items so finalize() can split
        them where another wire end or a pin end lands mid-segment, and add the junction dots."""
        pts = [(snap(x), snap(y)) for x, y in pts]
        for a, b in zip(pts, pts[1:]):
            if a != b:
                if a[0] != b[0] and a[1] != b[1]:
                    raise ValueError(f"{self.filename}: diagonal wire {a}->{b}")
                self.segments.append((a, b))

    def wl(self, a, b, first="h"):
        """L-shaped wire from a to b, horizontal leg first (or vertical with first='v')."""
        a, b = (snap(a[0]), snap(a[1])), (snap(b[0]), snap(b[1]))
        mid = (b[0], a[1]) if first == "h" else (a[0], b[1])
        self.wire(a, mid, b)

    def junction(self, pt):
        self.junctions.add((snap(pt[0]), snap(pt[1])))

    def no_connect(self, pl, number):
        x, y = pl.p(number)
        self.items.append([Sym("no_connect"), S("at", x, y), S("uuid", self._id("nc"))])
        self.connections.append((pl.ref, str(number), None, (x, y)))

    def label(self, net, at, angle=0, kind="local", shape="bidirectional"):
        x, y = snap(at[0]), snap(at[1])
        self.label_points.append((x, y))
        if kind == "local":
            just = {0: "left bottom", 180: "right bottom", 90: "left bottom", 270: "right bottom"}[angle]
            self.items.append([Sym("label"), net, S("at", x, y, angle), effects(just), S("uuid", self._id("label"))])
        else:
            just = {0: "left", 180: "right", 90: "left", 270: "right"}[angle]
            self.items.append([Sym("global_label"), net, S("shape", Sym(shape)), S("at", x, y, angle),
                               S("fields_autoplaced", Sym("yes")), effects(just), S("uuid", self._id("glabel")),
                               [Sym("property"), "Intersheetrefs", "${INTERSHEET_REFS}", S("at", x, y, 0),
                                effects(just, hide=True)]])

    def text(self, s, at, size=1.27, justify="left top", bold=False):
        e = effects(justify, size=size)
        if bold:
            e[1].append(S("bold", Sym("yes")))
        self.items.append([Sym("text"), s, S("exclude_from_sim", Sym("no")), S("at", snap(at[0]), snap(at[1]), 0),
                           e, S("uuid", self._id("text"))])

    def rect(self, a, b, width=0.254, dash=True):
        self.items.append([Sym("rectangle"), S("start", a[0], a[1]), S("end", b[0], b[1]),
                           S("stroke", S("width", width), S("type", Sym("dash" if dash else "default"))),
                           S("fill", S("type", Sym("none"))), S("uuid", self._id("rect"))])

    def table(self, at, widths, rows, row_h=5.08, header=True):
        x0, y0 = at
        cells = []
        y = y0
        for r, row in enumerate(rows):
            x = x0
            for c, txt in enumerate(row):
                e = effects("left top")
                if header and r == 0:
                    e[1].append(S("bold", Sym("yes")))
                cells.append([Sym("table_cell"), txt, S("exclude_from_sim", Sym("no")), S("at", round(x, 4), round(y, 4), 0),
                              S("size", widths[c], row_h), S("margins", 0.9525, 0.9525, 0.9525, 0.9525), S("span", 1, 1),
                              S("fill", S("type", Sym("none"))), e, S("uuid", self._id("cell"))])
                x += widths[c]
            y += row_h
        self.items.append([Sym("table"), S("column_count", len(widths)),
                           S("border", S("external", Sym("yes")), S("header", Sym("yes" if header else "no")),
                             S("stroke", S("width", 0.1524), S("type", Sym("solid")))),
                           S("separators", S("rows", Sym("yes")), S("cols", Sym("yes")),
                             S("stroke", S("width", 0.1524), S("type", Sym("solid")))),
                           S("column_widths", *widths), S("row_heights", *([row_h] * len(rows))), [Sym("cells")] + cells])
        return (x0 + sum(widths), y)

    def power(self, net, at, direction=None):
        """Power symbol with its pin at `at`; direction is where the graphic points (default: its natural way)."""
        lib_id = self.project.power_symbol(net)
        ground = net in self.project.ground_nets
        direction = direction or ("down" if ground else "up")
        if ground:
            rot = {"down": 0, "up": 180, "right": 90, "left": 270}[direction]
        else:
            rot = {"up": 0, "down": 180, "left": 90, "right": 270}[direction]
        return self.place(lib_id, ref=self.project.next_power_ref(), value=net, at=at, rot=rot)

    def pwr_flag(self, at, rot=0):
        """PWR_FLAG with its pin at `at`, graphic above (rot 270: to the right, for a flag on a vertical stub)."""
        return self.place("power:PWR_FLAG", ref=self.project.next_flag_ref(), value="PWR_FLAG", at=at, rot=rot,
                          hide_value=True)

    def flagged_stub(self, pl, number, net):
        """Pin to a net on a 5.08 mm stub, with a PWR_FLAG pointing sideways from the middle of the stub,
        so the flag stays clear of the label at the stub's end."""
        end = self.connect(pl, number, net, stub=5.08)
        x, y = pl.p(str(number))
        self.pwr_flag(((x + end[0]) / 2, (y + end[1]) / 2), rot=270)
        return end

    # ------------------------------------------------------------ connection helpers
    def connect(self, pl, number, net, kind=None, stub=2.54, shape="bidirectional", outward=False):
        """Tie a pin to a net with a short stub ending in a label or a power symbol.
        Power symbols on side pins point up (rails) or down (ground), or outward if `outward`."""
        number = str(number)
        x, y = pl.p(number)
        dx, dy = pl.out(number)
        ex, ey = x + dx * stub, y + dy * stub
        if stub:
            self.wire((x, y), (ex, ey))
        kind = kind or self.project.net_kind(net)
        if kind == "power":
            ground = net in self.project.ground_nets
            if dx:
                direction = ("right" if dx > 0 else "left") if outward else ("down" if ground else "up")
            else:
                direction = "down" if dy > 0 else "up"
            self.power(net, (ex, ey), direction)
        else:
            angle = {(1, 0): 0, (-1, 0): 180, (0, -1): 90, (0, 1): 270}[(dx, dy)]
            self.label(net, (ex, ey), angle, "global" if kind == "global" else "local", shape)
        self.connections.append((pl.ref, number, net, (x, y)))
        return (ex, ey)

    def tie(self, net, *pins):
        """Record that these (placed, pin) pairs are on `net` (drawn by the caller with wires)."""
        for pl, number in pins:
            self.connections.append((pl.ref, str(number), net, pl.p(number)))

    def finalize(self):
        """Split wire segments wherever another segment end, pin end or label lands mid-segment,
        then put a junction dot on every point where three or more things meet."""
        pin_points = set()
        for pl in self.placed:
            for n in pl.pins:
                pin_points.add(pl.p(n))
        segs = list(dict.fromkeys(tuple(sorted(s)) for s in self.segments))
        changed = True
        while changed:
            changed = False
            ends = {p for s in segs for p in s} | pin_points | set(self.label_points)
            out = []
            for a, b in segs:
                cut = None
                for p in ends:
                    if p in (a, b):
                        continue
                    if a[0] == b[0] == p[0] and min(a[1], b[1]) < p[1] < max(a[1], b[1]):
                        cut = p
                    elif a[1] == b[1] == p[1] and min(a[0], b[0]) < p[0] < max(a[0], b[0]):
                        cut = p
                    if cut:
                        break
                if cut:
                    out += [tuple(sorted((a, cut))), tuple(sorted((cut, b)))]
                    changed = True
                else:
                    out.append((a, b))
            segs = list(dict.fromkeys(out))
        count = {}
        for a, b in segs:
            count[a] = count.get(a, 0) + 1
            count[b] = count.get(b, 0) + 1
        for p in pin_points:
            if p in count:
                count[p] += 1
        for p, c in count.items():
            if c >= 3:
                self.junctions.add(p)
        for a, b in segs:
            self.items.append([Sym("wire"), [Sym("pts"), S("xy", *a), S("xy", *b)],
                               S("stroke", S("width", 0), S("type", Sym("default"))), S("uuid", self._id("wire"))])
        for p in sorted(self.junctions):
            self.items.append([Sym("junction"), S("at", p[0], p[1]), S("diameter", 0), S("color", 0, 0, 0, 0),
                               S("uuid", self._id("junction"))])
        self.segments = []
        self.final_segments = segs

    def to_sexpr(self):
        libs = self.project.project_libs
        root = self.project.root
        node = [Sym("kicad_sch"), S("version", 20250114), S("generator", "eeschema"), S("generator_version", "9.0"),
                S("uuid", self.uuid), S("paper", self.paper),
                [Sym("title_block"), S("title", self.title), S("date", self.project.date), S("rev", self.project.rev),
                 S("company", self.project.company)] + [S("comment", i + 1, c) for i, c in enumerate(self.project.comments)],
                [Sym("lib_symbols")] + [flat_symbol(l, libs) for l in self.lib_ids]]
        node += self.items
        for sub in self.subsheets:
            node.append(sub)
        if self is root:
            node.append(S("sheet_instances", S("path", "/", S("page", "1"))))
        node.append(S("embedded_fonts", Sym("no")))
        return node

    def write(self, directory):
        with open(os.path.join(directory, self.filename), "w", encoding="utf-8") as f:
            f.write(dumps(self.to_sexpr()) + "\n")


class Project:
    def __init__(self, name, project_libs, date, rev, company, comments=()):
        self.name, self.project_libs, self.date, self.rev, self.company = name, project_libs, date, rev, company
        self.comments = list(comments)
        self.sheets = []
        self.root = None
        self._pwr = 0
        self.refs = {}             # reference -> (lib_id, sheet file)
        self.power_nets = {}       # net -> lib_id of the power symbol to draw it with
        self.ground_nets = set()
        self.global_nets = set()

    def next_power_ref(self):
        self._pwr += 1
        return f"#PWR{self._pwr:03d}"

    def next_flag_ref(self):
        self._flg = getattr(self, "_flg", 0) + 1
        return f"#FLG{self._flg:03d}"

    def power_symbol(self, net):
        return self.power_nets[net]

    def net_kind(self, net):
        if net in self.power_nets:
            return "power"
        if net in self.global_nets:
            return "global"
        return "local"

    def add_root(self, title, filename=None):
        self.root = Sheet(self, "Root", filename or f"{self.name}.kicad_sch", "1", title)
        self.sheets.append(self.root)
        return self.root

    def add_sheet(self, name, filename, title, at, size=(38.1, 12.7)):
        page = str(len(self.sheets) + 1)
        sh = Sheet(self, name, filename, page, title)
        self.sheets.append(sh)
        x, y = at
        w, h = size
        self.root.subsheets.append(
            [Sym("sheet"), S("at", x, y), S("size", w, h), S("exclude_from_sim", Sym("no")), S("in_bom", Sym("yes")),
             S("on_board", Sym("yes")), S("dnp", Sym("no")), S("fields_autoplaced", Sym("yes")),
             S("stroke", S("width", 0.1524), S("type", Sym("solid"))), S("fill", S("color", 0, 0, 0, 0.0)),
             S("uuid", sh.symbol_uuid),
             [Sym("property"), "Sheetname", name, S("at", x, snap(y - 0.7112), 0), effects("left bottom")],
             [Sym("property"), "Sheetfile", filename, S("at", x, snap(y + h + 0.5938), 0), effects("left top")],
             S("instances", S("project", self.name, S("path", f"/{self.root.uuid}", S("page", page))))])
        return sh

    def write(self, directory):
        for sh in self.sheets:
            sh.finalize()
            sh.write(directory)

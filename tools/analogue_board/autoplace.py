"""First-pass placement of every part placement.py does not anchor (passives, small discretes,
test pads, the remaining power parts), as close as it fits to the pins it connects to.

Rules:
- each part aims at a target: the exact pin a decoupling capacitor's "Decouples" field names,
  else the mean of the pins it shares a signal net with on parts already placed;
- it prefers the face of the IC it serves, and takes the other face only if that is nearer;
- decoupling capacitors go first, then the rest as soon as something they connect to is placed,
  so chains (input resistor, filter capacitor, clamp) grow outward from their IC;
- courtyards, grown by MARGIN on every side to leave room for vias, may not overlap each
  other, the through-hole parts (both faces), or the board edge.

The result is a starting point for review, not a finished layout.
"""

import math
import re

import placement as P
import variant

RES = 0.1            # occupancy grid, mm
MARGIN = variant.SPACING / 2   # courtyard growth on each side, mm (courtyards already hold 0.25 mm around the pads)
TIGHT = 0.05                   # the fallback for a part that finds no room at the board's spacing
EDGE = 0.3           # courtyard to board edge, mm
MAX_R = 22.0         # search radius, mm
FAR_R = 110.0        # the last resort: anywhere on the board
OTHER_FACE = 1.5     # cost of using the face the target part is not on, mm
ROW_CROSS = 3.0      # cost of each module header row between a part and a pin it connects to, mm:
                     # every track across a row squeezes between its pins, and the channel between
                     # the rows is the board's tightest (2026-10-16: the last connections the
                     # router could not make were all parts placed across a row from their op-amp)
BIG_NET = 13         # nets with more pins (ground, rails) say nothing about where a part belongs
THT_PREFIXES = ("analogue_board:EdgeStrip", "analogue_board:WiringHoles", "analogue_board:Pico2",
                "analogue_board:Teensy41", "Connector_IDC:")

# Decouples fields that name a role rather than a pin: the part they sit beside
ROLE_TARGETS = {"rail entry +12V": "FB201", "rail entry -12V": "FB202", "buck output": "L201",
                "+5VD distribution": "U204", "module supply": "D203"}
# parts that belong beside one pin though their schematic field says nothing: a filter's output
# side is the short side (FB301 sat by the ADC, 28 mm of CODEC_VCC from the codec, 2026-10-16)
PIN_TARGETS = {"FB301": ("U301", "24")}
# and one board's own (the generator still reproduces the boards already ordered): on the Pico
# board R401, ADC_RST's 10k pull-up, sat at the top edge where the +3V3D pins it averaged put it,
# and ADC_RST could not climb round the ADC's corner past a fiducial's keep-out (2026-10-17)
PIN_TARGETS_BOARD = {"pico_core_midi": {"R401": ("U401", "2")}}
# capacitors serving these stay on the same face unless nothing fits within this many mm: the
# buck's input and output loops carry 350 kHz switching current and must not run through vias
SAME_FACE = {"U201": 12.0, "L201": 12.0}


class Grid:
    def __init__(self):
        self.w, self.h = int(math.ceil(P.BOARD_W / RES)), int(math.ceil(P.BOARD_H / RES))
        self.cells = {"F": bytearray(self.w * self.h), "B": bytearray(self.w * self.h)}

    def _span(self, r):
        x0, y0, x1, y1 = r
        return (max(0, int(math.floor(x0 / RES))), max(0, int(math.floor(y0 / RES))),
                min(self.w, int(math.ceil(x1 / RES))), min(self.h, int(math.ceil(y1 / RES))))

    def mark(self, face, r):
        a, b, c, d = self._span(r)
        cells = self.cells[face]
        for j in range(b, d):
            row = j * self.w
            cells[row + a:row + c] = b"\x01" * (c - a)

    def free(self, face, r):
        x0, y0, x1, y1 = r
        if x0 < EDGE or y0 < EDGE or x1 > P.BOARD_W - EDGE or y1 > P.BOARD_H - EDGE:
            return False
        a, b, c, d = self._span(r)
        cells = self.cells[face]
        for j in range(b, d):
            row = j * self.w
            if 1 in cells[row + a:row + c]:
                return False
        return True


def grow(r, m=MARGIN):
    return (r[0] - m, r[1] - m, r[2] + m, r[3] + m)


def _offsets(radius=MAX_R):
    n = int(radius / RES)
    pts = [(i * RES, j * RES) for i in range(-n, n + 1) for j in range(-n, n + 1) if i * i + j * j <= n * n]
    pts.sort(key=lambda p: p[0] * p[0] + p[1] * p[1])
    return pts


class Placer:
    def __init__(self, comps, pin_net, fixed, library_footprint, courtyard_rects, to_world):
        self.comps, self.pin_net = comps, pin_net
        self.lib, self.crt, self.to_world = library_footprint, courtyard_rects, to_world
        self.pos = {}                 # ref -> ((x, y) origin, rot, face), board coordinates
        self.face_penalty = {}        # ref -> cost (mm) of the other face, where it differs from OTHER_FACE
        self.grid = Grid()
        self.net_pins = {}
        for (ref, pin), net in pin_net.items():
            self.net_pins.setdefault(net, []).append((ref, pin))
        for ref, p in fixed.items():
            self.put(ref, *p)
        self.offsets = _offsets()
        # the module header rows: (x, top, bottom) of each column of module pins
        self.rows = []
        for ref in variant.MODULES:
            if ref in self.pos:
                cols = {}
                for x, y in self.pads(ref).values():
                    cols.setdefault(round(x, 1), []).append(y)
                self.rows += [(x, min(ys), max(ys)) for x, ys in cols.items() if len(ys) > 4]

    def row_cost(self, x, y, pins):
        """ROW_CROSS for every header row between (x, y) and each pin."""
        n = 0
        for px, py in pins:
            for rx, top, bottom in self.rows:
                if (x - rx) * (px - rx) < 0:
                    yc = y + (py - y) * (rx - x) / (px - x)
                    if top - 1.27 <= yc <= bottom + 1.27:
                        n += 1
        return ROW_CROSS * n

    # ---------------------------------------------------------------- geometry
    def rects(self, ref, origin, rot, face):
        """World courtyard rectangles of a part placed at origin."""
        out = []
        for x0, y0, x1, y1 in self.crt(self.lib(self.comps[ref]["fp"])):
            pts = [self.to_world(p, origin, rot, face) for p in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]
            xs, ys = [p[0] for p in pts], [p[1] for p in pts]
            out.append((min(xs), min(ys), max(xs), max(ys)))
        return out

    def pads(self, ref):
        origin, rot, face = self.pos[ref]
        res = {}
        for p in self.lib(self.comps[ref]["fp"]):
            if isinstance(p, list) and p and str(p[0]) == "pad":
                at = [c for c in p if isinstance(c, list) and c and str(c[0]) == "at"][0]
                res.setdefault(str(p[1]), self.to_world((float(at[1]), float(at[2])), origin, rot, face))
        return res

    def is_tht(self, ref):
        return self.comps[ref]["fp"].startswith(THT_PREFIXES)

    def put(self, ref, origin, rot, face, m=MARGIN):
        self.pos[ref] = (origin, rot, face)
        if self.is_tht(ref):
            # through-hole parts block both faces; a shrouded header's body only the outward face
            for r in self.rects(ref, origin, rot, face):
                self.grid.mark(face, grow(r, 0.0))
            pads = self.pads(ref).values()
            if self.comps[ref]["fp"].startswith("Connector_IDC:"):
                xs, ys = [p[0] for p in pads], [p[1] for p in pads]
                self.grid.mark("B", (min(xs) - 1.2, min(ys) - 1.2, max(xs) + 1.2, max(ys) + 1.2))
            else:
                for r in self.rects(ref, origin, rot, face):
                    self.grid.mark("B" if face == "F" else "F", grow(r, 0.0))
        else:
            for r in self.rects(ref, origin, rot, face):
                self.grid.mark(face, grow(r, m))

    # ---------------------------------------------------------------- targets
    def decouples(self, ref):
        targets = {**PIN_TARGETS, **PIN_TARGETS_BOARD.get(variant.FLOORPLAN, {})}
        if ref in targets and targets[ref][0] in self.comps:
            return targets[ref]
        d = self.comps[ref]["props"].get("Decouples", "")
        if not d:
            return None
        for role, target in ROLE_TARGETS.items():
            if d.startswith(role):
                return (target, None)
        m = re.match(r"(?:VCOM at |LED supply at )?([UAJ]\d+)\b(?:.*?\bpin (\d+))?", d)
        return (m.group(1), m.group(2)) if m else None

    def target(self, ref):
        """(x, y, preferred face or None, strength, the pins it connects to) or None while nothing
        it connects to is placed."""
        dec = self.decouples(ref)
        if dec:
            tref, pin = dec
            if tref not in self.pos:
                return None
            face = self.pos[tref][2]
            self.face_penalty[ref] = SAME_FACE.get(tref, OTHER_FACE)
            if pin:
                x, y = self.pads(tref)[pin]
                return (x, y, None if self.is_tht(tref) else face, 3.0, [(x, y)])
            r = self.rects(tref, *self.pos[tref])[0]
            c = ((r[0] + r[2]) / 2, (r[1] + r[3]) / 2)
            return (c[0], c[1], None if self.is_tht(tref) else face, 2.0, [c])
        pts, faces = [], {}
        for (r2, pin), net in self.pin_net.items():
            if r2 != ref:
                continue
            members = self.net_pins.get(net, [])
            if net == "GND" or len(members) > BIG_NET:
                continue
            for o, opin in members:
                if o == ref or o not in self.pos:
                    continue
                pad = self.pads(o).get(opin)
                if pad:
                    pts.append(pad)
                    if not self.is_tht(o):
                        f = self.pos[o][2]
                        faces[f] = faces.get(f, 0) + 1
        if not pts:
            return None
        face = max(faces, key=faces.get) if faces else None
        return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts), face, float(len(pts)), pts)

    # ---------------------------------------------------------------- search
    def find(self, ref, tx, ty, face_pref, m=MARGIN, offsets=None, pins=()):
        """The nearest free spot to (tx, ty): distance, plus the other-face penalty, plus
        ROW_CROSS for each header row between the spot and each of `pins`."""
        lib = self.lib(self.comps[ref]["fp"])
        boxes = self.crt(lib)
        bx0 = min(b[0] for b in boxes); by0 = min(b[1] for b in boxes)
        bx1 = max(b[2] for b in boxes); by1 = max(b[3] for b in boxes)
        best = None
        for face in ("F", "B"):
            penalty = 0.0 if face_pref in (None, face) else self.face_penalty.get(ref, OTHER_FACE)
            for rot in (0, 90):
                # courtyard box relative to the origin for this rotation and face
                corners = [self.to_world(p, (0, 0), rot, face) for p in ((bx0, by0), (bx1, by0), (bx1, by1), (bx0, by1))]
                cx0, cy0 = min(c[0] for c in corners), min(c[1] for c in corners)
                cx1, cy1 = max(c[0] for c in corners), max(c[1] for c in corners)
                hx, hy = (cx1 - cx0) / 2, (cy1 - cy0) / 2
                ccx, ccy = (cx0 + cx1) / 2, (cy0 + cy1) / 2   # courtyard centre relative to origin
                for dx, dy in offsets or self.offsets:
                    base = math.hypot(dx, dy) + penalty
                    if best and base >= best[0]:
                        break
                    x, y = tx + dx, ty + dy
                    r = grow((x - hx, y - hy, x + hx, y + hy), m)
                    if self.grid.free(face, r):
                        d = base + (self.row_cost(x, y, pins) if pins else 0.0)
                        if not best or d < best[0]:
                            best = (d, (x - ccx, y - ccy), rot, face)
                        if d == base:      # nothing between it and its pins: no farther spot beats it
                            break
        return best

    def run(self, todo):
        pending = [r for r in todo if r not in self.pos]
        unplaced = []
        while pending:
            ready = []
            for ref in pending:
                t = self.target(ref)
                if t:
                    ready.append((0 if self.decouples(ref) else 1, -t[3], ref, t))
            if not ready:
                # parts tied only to ground and rails (minimum loads, rail test pads): beside the
                # middle of what is already placed from their own schematic sheet
                for ref in pending:
                    mates = [r for r in self.pos if self.comps[r]["sheet"] == self.comps[ref]["sheet"]
                             and not self.is_tht(r)]
                    if mates:
                        rs = [self.rects(r, *self.pos[r])[0] for r in mates]
                        ready.append((2, 0.0, ref, (sum((r[0] + r[2]) / 2 for r in rs) / len(rs),
                                                    sum((r[1] + r[3]) / 2 for r in rs) / len(rs), None, 0.0, [])))
            if not ready:
                unplaced += pending
                break
            ready.sort()
            # place the decoupling capacitors and the best-connected half, then recompute targets;
            # a part placed by the fallback goes alone, so whatever hangs off it gets a real target
            n = 1 if ready[0][0] == 2 else max(1, len(ready) // 2)
            for _, _, ref, (tx, ty, face, _, pins) in ready[:n]:
                hit, m = self.find(ref, tx, ty, face, pins=pins), MARGIN
                if not hit and MARGIN > TIGHT:
                    # no room at the board's spacing: this part alone at the tight spacing
                    hit, m = self.find(ref, tx, ty, face, TIGHT, pins=pins), TIGHT
                if not hit:
                    # nothing free nearby: the nearest free spot anywhere on the board
                    self.offsets_far = getattr(self, "offsets_far", None) or _offsets(FAR_R)
                    hit = self.find(ref, tx, ty, face, m, self.offsets_far, pins=pins)
                if hit:
                    _, origin, rot, f = hit
                    self.put(ref, origin, rot, f, m)
                else:
                    unplaced.append(ref)
            done = {r for _, _, r, _ in ready[:n]}
            pending = [r for r in pending if r not in done]
        return unplaced

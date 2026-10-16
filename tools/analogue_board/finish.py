"""Finish a routed board: the mechanical leftovers an autorouter leaves.

Run with KiCad's own Python (it has pcbnew), on a board routed by autoroute.py:

    /Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 \\
        tools/analogue_board/finish.py <routed.kicad_pcb> [out.kicad_pcb]

1. Vias: KiCad's session import brings some 0.45 mm vias back with a 0.3 mm drill, leaving a
   0.075 mm ring and holes too close to neighbouring copper. Each via's drill is set so the ring
   is at least MIN_RING.
2. Tracks narrower than MIN_TRACK (Freerouting's neck-down into fine-pitch pads) are widened.
3. Ground: every ground pad still unconnected is joined, by a short stub on the pad's layer, to
   an existing ground via nearby or else to a new via to the In1 plane. Candidate spots ring
   the pad, nearest first, out to 4 mm. A new via is taken only if it clears every other net's
   copper on every layer, every hole, the board edge and any rule area that forbids vias. A stub
   must clear every other net's copper on its layer. It tries 0.3 mm, then 0.2 mm, then 0.127 mm
   wide, because a fine-pitch pin cannot leave its row on a wide stub.

4. Leftovers: each net's copper still in separate groups is joined by route_gap, a grid router
   on the five routing layers (In1 is the plane) that clears every other net. What it cannot
   join goes to rip_up: the path may cross other nets' tracks at a cost, those tracks are taken
   up and every net involved routed again, and the try is kept only if fewer connections are
   left. Dead-end tracks and vias are removed before and after.

fan_out_ground() is step 3 run before routing instead (autoroute.py --ground-vias): every
surface-mount ground pad gets its own via, on the side away from its part, kept within 1.6 mm.

Writes <routed>_finished.kicad_pcb (or out), refills the zones, and prints what is left unconnected.
The project's .kicad_pro is copied beside the output, so DRC runs against the project's rules.
"""

import math
import os
import shutil
import subprocess
import sys
import json

import pcbnew

MM = 1e6
KICAD_CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
VIA_D, VIA_HOLE = 0.45, 0.2          # the Default via (0.45/0.2 mm)
MIN_RING, MIN_TRACK = 0.125, 0.127
CLEAR, HOLE_CLEAR, EDGE = 0.132, 0.25, 0.5   # copper (0.127 mm rule + margin), hole and board-edge clearances, mm
STUB_WIDTHS = (0.3, 0.2, 0.127)      # ground is in the Power class (0.3 mm); fine-pitch pins need less


def load_rules(pro):
    """The board's own Default track and clearance, from its project file (shared_core routes at
    0.1 mm, the other boards at 0.127): every width and clearance here follows them."""
    global MIN_TRACK, CLEAR, STUB_WIDTHS, POWER_WIDTHS
    if not os.path.exists(pro):
        return
    with open(pro, encoding="utf-8") as f:
        classes = json.load(f).get("net_settings", {}).get("classes", [])
    default = next((c for c in classes if c.get("name") == "Default"), None)
    if default:
        MIN_TRACK = default["track_width"]
        CLEAR = default["clearance"] + 0.005
        STUB_WIDTHS = (0.3, 0.2, MIN_TRACK)
        POWER_WIDTHS = (0.3, 0.2, MIN_TRACK)
REACH = 4.0                          # how far from the pad to look, mm


# ------------------------------------------------------------------ geometry (mm)
def seg_point(a, b, p):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = 0.0 if L == 0 else max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / L))
    return math.hypot(ax + t * dx - p[0], ay + t * dy - p[1])


def seg_seg(a, b, c, d):
    def ccw(p, q, r):
        return (r[1] - p[1]) * (q[0] - p[0]) - (q[1] - p[1]) * (r[0] - p[0])
    if (ccw(a, b, c) * ccw(a, b, d) < 0) and (ccw(c, d, a) * ccw(c, d, b) < 0):
        return 0.0
    return min(seg_point(a, b, c), seg_point(a, b, d), seg_point(c, d, a), seg_point(c, d, b))


def box_point(box, p):
    x0, y0, x1, y1 = box
    dx = max(x0 - p[0], 0.0, p[0] - x1)
    dy = max(y0 - p[1], 0.0, p[1] - y1)
    return math.hypot(dx, dy)


def box_seg(box, a, b):
    x0, y0, x1, y1 = box
    if box_point(box, a) == 0 or box_point(box, b) == 0:
        return 0.0
    edges = [((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))]
    return min(seg_seg(a, b, e0, e1) for e0, e1 in edges)


def mm(v):
    return (v.x / MM, v.y / MM)


def via_width(v):
    return v.GetWidth(pcbnew.F_Cu) / MM   # KiCad 9 padstacks: a through via's width, read on one layer


def set_via(v, width, drill):
    v.SetWidth(pcbnew.F_Cu, int(width * MM))
    v.SetDrill(int(drill * MM))


# ------------------------------------------------------------------ copper inventory
CELL = 1.0    # the spatial index's cell, mm
NEAR = 1.0    # how far round a point or stub copper is looked for: beyond every clearance test here


def bbox(kind, g, half):
    if kind == "circle":
        return (g[0] - half, g[1] - half, g[0] + half, g[1] + half)
    if kind == "seg":
        return (min(g[0][0], g[1][0]) - half, min(g[0][1], g[1][1]) - half,
                max(g[0][0], g[1][0]) + half, max(g[0][1], g[1][1]) + half)
    return g


def cells(box):
    for i in range(int(math.floor(box[0] / CELL)), int(math.floor(box[2] / CELL)) + 1):
        for j in range(int(math.floor(box[1] / CELL)), int(math.floor(box[3] / CELL)) + 1):
            yield i, j


class Copper:
    """Every copper item as simple shapes: per layer, (net, kind, geometry, half-width), with a
    grid index so a clearance test looks only at the copper near it."""

    def __init__(self, board):
        self.board = board
        self.gnd = board.FindNet("GND").GetNetCode()
        self.layers = list(board.GetEnabledLayers().CuStack())
        self.items = {l: [] for l in self.layers}
        self.grid = {l: {} for l in self.layers}
        self.holes = []   # (centre, radius, net)
        self.hole_grid = {}
        self.vias = set()
        self.hard_nets = set()   # rip_up: nets just routed, which may not be taken up yet
        for t in board.GetTracks():
            if t.Type() == pcbnew.PCB_VIA_T:
                self.add_via(t.GetNetCode(), mm(t.GetPosition()), via_width(t) / 2, t.GetDrillValue() / MM / 2)
            else:
                self.add_seg(t.GetNetCode(), t.GetLayer(), mm(t.GetStart()), mm(t.GetEnd()), t.GetWidth() / MM / 2)
        for fp in board.GetFootprints():
            for p in fp.Pads():
                bb = p.GetBoundingBox()
                box = (bb.GetLeft() / MM, bb.GetTop() / MM, bb.GetRight() / MM, bb.GetBottom() / MM)
                for l in self.layers:
                    if p.IsOnLayer(l):
                        self.add(l, (p.GetNetCode(), "box", box, 0.0))
                if p.GetDrillSizeX() > 0:
                    self.add_hole(mm(p.GetPosition()), p.GetDrillSizeX() / MM / 2, p.GetNetCode())
        # the outline's own line, not the bounding box, which takes in half the line's width
        e = board.GetBoardEdgesBoundingBox()
        line = max((d.GetWidth() / MM for d in board.GetDrawings() if d.GetLayer() == pcbnew.Edge_Cuts), default=0.0)
        self.edge = (e.GetLeft() / MM + line / 2, e.GetTop() / MM + line / 2,
                     e.GetRight() / MM - line / 2, e.GetBottom() / MM - line / 2)
        self.no_via = []
        self.plane = []   # the ground plane's filled copper: a new via must land in it
        for z in board.Zones():
            if z.GetIsRuleArea() and z.GetDoNotAllowVias():
                bb = z.GetBoundingBox()
                self.no_via.append((bb.GetLeft() / MM, bb.GetTop() / MM, bb.GetRight() / MM, bb.GetBottom() / MM))
            elif not z.GetIsRuleArea() and z.GetNetname() == "GND" and z.IsOnLayer(pcbnew.In1_Cu):
                self.plane.append(z.GetFilledPolysList(pcbnew.In1_Cu))

    def in_plane(self, c):
        """True if the filled ground plane covers the via's whole pad, so it connects."""
        if not self.plane:
            return True
        r = VIA_D / 2
        pts = [c] + [(c[0] + r * math.cos(a), c[1] + r * math.sin(a)) for a in (0, 1.57, 3.14, 4.71)]
        return all(any(poly.Contains(pcbnew.VECTOR2I(int(p[0] * MM), int(p[1] * MM))) for poly in self.plane) for p in pts)

    def add(self, layer, item):
        self.items[layer].append(item)
        for k in cells(bbox(*item[1:])):
            self.grid[layer].setdefault(k, []).append(item)

    def add_hole(self, c, r, net=0):
        self.holes.append((c, r, net))
        for k in cells((c[0] - r, c[1] - r, c[0] + r, c[1] + r)):
            self.hole_grid.setdefault(k, []).append((c, r, net))

    def add_via(self, net, c, r, hole):
        for l in self.layers:
            self.add(l, (net, "circle", c, r))
        self.add_hole(c, hole, net)
        self.vias.add((round(c[0], 4), round(c[1], 4)))

    def via_hole(self, c):
        """True if the hole at c is a via's (rip_up may take it up), not a pad's."""
        return (round(c[0], 4), round(c[1], 4)) in self.vias

    def add_seg(self, net, layer, a, b, half):
        self.add(layer, (net, "seg", (a, b), half))

    def near(self, grid, box):
        """Each item indexed in `grid` whose cells meet the box, once."""
        seen = set()
        for k in cells(box):
            for it in grid.get(k, ()):
                if id(it) not in seen:
                    seen.add(id(it))
                    yield it

    def gap_point(self, layer, net, p, hard_only=False):
        """Least distance from point p to other-net copper on a layer (NEAR if none is closer).
        `hard_only`: only what rip_up may not take up (pads, and ground's tracks and vias)."""
        best = NEAR
        for n, kind, g, half in self.near(self.grid[layer], (p[0] - NEAR, p[1] - NEAR, p[0] + NEAR, p[1] + NEAR)):
            if n == net or hard_only and kind != "box" and n != self.gnd and n not in self.hard_nets:
                continue
            d = (math.dist(p, g) - half if kind == "circle" else seg_point(g[0], g[1], p) - half if kind == "seg"
                 else box_point(g, p))
            best = min(best, d)
        return best

    def gap_seg(self, layer, net, a, b):
        best = NEAR
        box = (min(a[0], b[0]) - NEAR, min(a[1], b[1]) - NEAR, max(a[0], b[0]) + NEAR, max(a[1], b[1]) + NEAR)
        for n, kind, g, half in self.near(self.grid[layer], box):
            if n == net:
                continue
            d = (seg_point(a, b, g) - half if kind == "circle" else seg_seg(a, b, g[0], g[1]) - half if kind == "seg"
                 else box_seg(g, a, b))
            best = min(best, d)
        return best

    def via_fits(self, net, c, r=VIA_D / 2, hole=VIA_HOLE / 2, hard_only=False):
        x0, y0, x1, y1 = self.edge
        if min(c[0] - x0, x1 - c[0], c[1] - y0, y1 - c[1]) < EDGE + r:
            return False
        if any(box_point(k, c) <= r for k in self.no_via):
            return False
        if any(math.dist(c, hc) - hr - hole < HOLE_CLEAR
               for hc, hr, n in self.near(self.hole_grid, (c[0] - NEAR, c[1] - NEAR, c[0] + NEAR, c[1] + NEAR))
               if not (hard_only and n not in (net, self.gnd) and self.via_hole(hc))):
            return False
        if not all(self.gap_point(l, net, c, hard_only) - r >= max(CLEAR, HOLE_CLEAR + hole - r) for l in self.layers):
            return False
        return net != self.gnd or self.in_plane(c)   # a ground via must reach the plane

    def stub_width(self, net, layer, a, b):
        """The widest stub from a to b that clears other nets on the layer, or None."""
        gap = self.gap_seg(layer, net, a, b)
        return next((w for w in STUB_WIDTHS if gap - w / 2 >= CLEAR), None)


# ------------------------------------------------------------------ the steps
def fix_vias(board):
    n = 0
    for t in board.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T:
            w, d = via_width(t), t.GetDrillValue() / MM
            if (w - d) / 2 < MIN_RING - 1e-6:
                set_via(t, w, max(0.2, w - 2 * MIN_RING))
                n += 1
    return n


def widen_tracks(board):
    n = 0
    for t in board.GetTracks():
        if t.Type() != pcbnew.PCB_VIA_T and t.GetWidth() / MM < MIN_TRACK - 1e-6:
            t.SetWidth(int(MIN_TRACK * MM))
            n += 1
    return n


def maze_stub(copper, net, layer, start, gnd_vias, half_window=4.0, grid=0.05, width=0.127):
    """A bent stub for a pad that straight stubs cannot leave: breadth-first search on a grid
    round the pad, on its layer, with other nets' copper grown by clearance + half the stub.
    Goal: an existing ground via, or a cell (on a 0.2 mm lattice) where a new via fits.
    Returns (points, via centre, new via?) or None."""
    import collections
    x0, y0 = start[0] - half_window, start[1] - half_window
    n = int(2 * half_window / grid) + 1
    grow = CLEAR + width / 2 + grid * 0.75          # the grid's own error, on the safe side
    window = (x0 - 1, y0 - 1, x0 + 2 * half_window + 1, y0 + 2 * half_window + 1)
    blocked = bytearray(n * n)
    for nn, kind, g, half in copper.near(copper.grid[layer], window):
        if nn == net:
            continue
        bb = bbox(kind, g, half)
        i0, i1 = max(0, int((bb[0] - grow - x0) / grid)), min(n - 1, int((bb[2] + grow - x0) / grid) + 1)
        j0, j1 = max(0, int((bb[1] - grow - y0) / grid)), min(n - 1, int((bb[3] + grow - y0) / grid) + 1)
        for j in range(j0, j1 + 1):
            py = y0 + j * grid
            for i in range(i0, i1 + 1):
                px = x0 + i * grid
                p = (px, py)
                d = (math.dist(p, g) - half if kind == "circle" else seg_point(g[0], g[1], p) - half if kind == "seg"
                     else box_point(g, p))
                if d < grow:
                    blocked[j * n + i] = 1
    si = sj = int(half_window / grid)
    prev = {si + sj * n: None}
    q = collections.deque([(si, sj)])
    goal = None
    vias = [v for v in gnd_vias if abs(v[0] - start[0]) <= half_window and abs(v[1] - start[1]) <= half_window]
    lattice = max(1, int(0.2 / grid))
    while q and not goal:
        i, j = q.popleft()
        p = (x0 + i * grid, y0 + j * grid)
        for v in vias:
            if math.dist(p, v) <= VIA_D / 2 - width / 2:
                goal = (i, j, v, False)
                break
        if not goal and i % lattice == 0 and j % lattice == 0 and math.dist(p, start) > VIA_D \
                and copper.via_fits(net, p):
            goal = (i, j, p, True)
        if goal:
            break
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
            a, b = i + di, j + dj
            k = a + b * n
            if 0 <= a < n and 0 <= b < n and k not in prev and not blocked[k]:
                prev[k] = i + j * n
                q.append((a, b))
    if not goal:
        return None
    i, j, v, new = goal
    cells, k = [], i + j * n
    while k is not None:
        cells.append((x0 + (k % n) * grid, y0 + (k // n) * grid))
        k = prev[k]
    cells.reverse()
    cells[0] = start
    pts = [cells[0]]   # keep only the corners
    for a, b, c in zip(cells, cells[1:], cells[2:]):
        if abs((b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])) > 1e-9:
            pts.append(b)
    pts.append(cells[-1] if not new else v)
    if not new:
        pts.append(v)
    return pts, v, new


COPPER_FAULTS = {"clearance", "copper_edge_clearance", "hole_clearance", "shorting_items", "tracks_crossing",
                 "hole_to_hole"}


def take_up_faults(board, tmp):
    """Tracks and vias in a copper fault (DRC on the board saved to `tmp`), taken up so the
    leftover router makes those connections again: another net's copper where possible, ground's
    only when nothing else is involved. Returns how many were taken up."""
    pcbnew.SaveBoard(tmp, board)
    rpt = tmp + ".drc.json"
    subprocess.run([KICAD_CLI, "pcb", "drc", "--format", "json", "--severity-all", "-o", rpt, tmp],
                   capture_output=True, text=True)
    with open(rpt, encoding="utf-8") as f:
        d = json.load(f)
    os.remove(rpt)
    tracks = {t.m_Uuid.AsString(): t for t in board.GetTracks()}
    doomed = {}
    for v in d.get("violations", []):
        if v["type"] in ("track_dangling", "via_dangling"):
            # exactly what KiCad calls a dead end (slivers the grid router leaves inside another
            # track among them): a free end carries nothing, so taking it up breaks no connection
            for i in v["items"]:
                if i.get("uuid") in tracks:
                    doomed[i["uuid"]] = tracks[i["uuid"]]
            continue
        if v["type"] not in COPPER_FAULTS:
            continue
        ours = [tracks[i["uuid"]] for i in v["items"] if i.get("uuid") in tracks]
        pick = [t for t in ours if t.GetNetname() != "GND"] or ours
        for t in pick:
            doomed[t.m_Uuid.AsString()] = t
    for t in doomed.values():
        board.Delete(t)
    return len(doomed)


def unconnected_ground_pads(board_path, pro_path):
    """Ground pads in KiCad's unconnected-items list, from a DRC run against the project's rules."""
    rpt = board_path + ".drc.json"
    subprocess.run([KICAD_CLI, "pcb", "drc", "--format", "json", "--severity-all", "-o", rpt, board_path],
                   capture_output=True, text=True)
    with open(rpt, encoding="utf-8") as f:
        d = json.load(f)
    os.remove(rpt)
    out = []
    for u in d.get("unconnected_items", []):
        for it in u["items"]:
            desc = it["description"]
            if "[GND]" in desc and desc.startswith("Pad"):
                parts = desc.split(" of ")
                ref = parts[1].split()[0] if len(parts) > 1 else None
                out.append((ref, desc.split()[1], (it["pos"]["x"], it["pos"]["y"])))
    return out


def stitch_ground(board, targets, reach=REACH, share=REACH, maze=True, outward=False):
    """A via and stub beside each ground pad in `targets`; returns (placed, failed refs).
    `share`: how far an existing ground via may be to serve the pad instead of a new one.
    `outward`: try the via on the side of the pad away from its part's middle first (before
    routing, so the vias stand clear of the part's other pins)."""
    gnd = board.FindNet("GND")
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())   # so the plane's real copper is known
    copper = Copper(board)
    pads = {}
    for fp in board.GetFootprints():
        for p in fp.Pads():
            pads[(fp.GetReference(), p.GetNumber())] = p
    placed, failed, done = 0, [], set()
    mazed = []
    for ref, num, _pos in targets:
        if (ref, num) in done:
            continue
        done.add((ref, num))
        pad = pads.get((ref, num))
        if pad is None or pad.GetAttribute() == pcbnew.PAD_ATTRIB_PTH:
            continue
        layer = pcbnew.F_Cu if pad.IsOnLayer(pcbnew.F_Cu) else pcbnew.B_Cu
        net = gnd.GetNetCode()
        c = mm(pad.GetPosition())
        bb = pad.GetBoundingBox()
        half_pad = max(bb.GetWidth(), bb.GetHeight()) / MM / 2
        # an existing ground via within reach, nearest first: no new hole needed
        existing = sorted((math.dist(c, mm(t.GetPosition())), mm(t.GetPosition())) for t in board.GetTracks()
                          if t.Type() == pcbnew.PCB_VIA_T and t.GetNetCode() == net and math.dist(c, mm(t.GetPosition())) <= share)
        best = None
        for _d, v in existing:
            w = copper.stub_width(net, layer, c, v)
            if w:
                best = (v, w, False)
                break
        angles = [2 * math.pi * i / 36 for i in range(36)]
        front_n = 13                                   # the 60 degrees either side of straight out
        if outward:
            mine = pad.GetParentFootprint().Pads()
            mid = [mm(q.GetPosition()) for q in mine]
            mid = (sum(p[0] for p in mid) / len(mid), sum(p[1] for p in mid) / len(mid))
            if len(mine) > 4:
                # a chip's pin: straight out along the pin. Out from the chip's middle is diagonal
                # for a pin near the end of a row, and put the vias of pins 3 and 4 of the ADC in
                # front of pin 2, walling it in (2026-10-16)
                if bb.GetWidth() >= bb.GetHeight():
                    a0 = 0.0 if c[0] > mid[0] else math.pi
                else:
                    a0 = math.pi / 2 if c[1] > mid[1] else -math.pi / 2
                front_n = 7                            # 30 degrees either side
            else:
                a0 = math.atan2(c[1] - mid[1], c[0] - mid[0]) if math.dist(c, mid) > 1e-3 else None
            if a0 is not None:
                angles.sort(key=lambda a: abs(math.remainder(a - a0, 2 * math.pi)))
        # outward: the front of the pad, at every radius, before the rest
        for front in ([angles[:front_n], angles[front_n:]] if outward else [angles]):
            r = half_pad + VIA_D / 2 + CLEAR + 0.05
            limit = max(reach, r + 0.6)            # a big pad (a regulator's tab) still gets three rings
            while r <= limit and not best:         # rings from just outside the pad outwards
                for a in front:
                    v = (c[0] + r * math.cos(a), c[1] + r * math.sin(a))
                    if copper.via_fits(net, v):
                        w = copper.stub_width(net, layer, c, v)
                        if w:
                            best = (v, w, True)
                            break
                r += 0.2
        if not best and not maze:
            failed.append(f"{ref}.{num}")
            continue
        if not best:
            # no straight stub: a bent one, found by a grid search round the pad
            gvias = [mm(t.GetPosition()) for t in board.GetTracks() if t.Type() == pcbnew.PCB_VIA_T and t.GetNetCode() == net]
            hit = None
            for w in (0.2, MIN_TRACK):
                hit = maze_stub(copper, net, layer, c, gvias, width=w)
                if hit:
                    break
            if not hit:
                failed.append(f"{ref}.{num}")
                continue
            pts, v, new = hit
            if new:
                via = pcbnew.PCB_VIA(board)
                via.SetPosition(pcbnew.VECTOR2I(int(v[0] * MM), int(v[1] * MM)))
                via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
                set_via(via, VIA_D, VIA_HOLE)
                via.SetNet(gnd)
                board.Add(via)
                copper.add_via(net, v, VIA_D / 2, VIA_HOLE / 2)
            for a, b in zip(pts, pts[1:]):
                if math.dist(a, b) < 1e-6:
                    continue
                trk = pcbnew.PCB_TRACK(board)
                trk.SetStart(pcbnew.VECTOR2I(int(a[0] * MM), int(a[1] * MM)))
                trk.SetEnd(pcbnew.VECTOR2I(int(b[0] * MM), int(b[1] * MM)))
                trk.SetWidth(int(w * MM))
                trk.SetLayer(layer)
                trk.SetNet(gnd)
                board.Add(trk)
                copper.add_seg(net, layer, a, b, w / 2)
            placed += 1
            mazed.append(f"{ref}.{num}")
            continue
        v, w, new = best
        if new:
            via = pcbnew.PCB_VIA(board)
            via.SetPosition(pcbnew.VECTOR2I(int(v[0] * MM), int(v[1] * MM)))
            via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
            set_via(via, VIA_D, VIA_HOLE)
            via.SetNet(gnd)
            board.Add(via)
            copper.add_via(net, v, VIA_D / 2, VIA_HOLE / 2)
        trk = pcbnew.PCB_TRACK(board)
        trk.SetStart(pad.GetPosition())
        trk.SetEnd(pcbnew.VECTOR2I(int(v[0] * MM), int(v[1] * MM)))
        trk.SetWidth(int(w * MM))
        trk.SetLayer(layer)
        trk.SetNet(gnd)
        board.Add(trk)
        copper.add_seg(net, layer, c, v, w / 2)
        placed += 1
    print(f"  of which bent stubs (grid search): {len(mazed)}")
    return placed, failed


def fan_out_ground(board, reach=1.6, share=0.9):
    """Before routing: a via to the plane beside every surface-mount ground pad, on its outer
    side, so each part's ground goes straight down to In1 rather than along tracks to some other
    part's ground (the autorouter, left to itself, joins ground pads to each other). A pad with
    another ground via within `share` mm uses that one. Returns (placed, failed refs)."""
    targets = sorted((fp.GetReference(), p.GetNumber(), None) for fp in board.GetFootprints() for p in fp.Pads()
                     if p.GetNetname() == "GND" and p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD)
    return stitch_ground(board, targets, reach=reach, share=share, maze=False, outward=True)


# ------------------------------------------------------------------ the leftover connections
GRID = 0.05                         # the leftover router's grid, mm
VIA_COST = 30                       # a layer change costs as much as 1.5 mm of track
POWER_WIDTHS = (0.3, 0.2, 0.127)    # a rail's track: as wide as there is room for


def net_items(board, net):
    """A net's copper: (kind, layer, or None for every layer, geometry, half-width, object)."""
    out = []
    for t in board.GetTracks():
        if t.GetNetCode() != net:
            continue
        if t.Type() == pcbnew.PCB_VIA_T:
            out.append(("circle", None, mm(t.GetPosition()), via_width(t) / 2, t))
        else:
            out.append(("seg", t.GetLayer(), (mm(t.GetStart()), mm(t.GetEnd())), t.GetWidth() / MM / 2, t))
    for fp in board.GetFootprints():
        for p in fp.Pads():
            if p.GetNetCode() == net:
                bb = p.GetBoundingBox()
                box = (bb.GetLeft() / MM, bb.GetTop() / MM, bb.GetRight() / MM, bb.GetBottom() / MM)
                layer = None if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH else (
                    pcbnew.F_Cu if p.IsOnLayer(pcbnew.F_Cu) else pcbnew.B_Cu)
                out.append(("box", layer, box, 0.0, p))
    return out


def inside(item, p):
    """True if point p lies in the item's copper, where a track end joins it."""
    kind, _layer, g, half, obj = item
    if kind == "circle":
        return math.dist(p, g) <= half - 0.01
    if kind == "seg":
        return seg_point(g[0], g[1], p) <= half - 0.01
    return obj.HitTest(pcbnew.VECTOR2I(int(p[0] * MM), int(p[1] * MM)), 0)


def anchors(item):
    kind, _layer, g, _half, obj = item
    return list(g) if kind == "seg" else [g] if kind == "circle" else [mm(obj.GetPosition())]


def touch(a, b):
    if a[1] is not None and b[1] is not None and a[1] != b[1]:
        return False
    return any(inside(b, p) for p in anchors(a)) or any(inside(a, p) for p in anchors(b))


def clusters(items):
    """A net's copper in connected groups, smallest first (union-find on items that touch)."""
    parent = list(range(len(items)))

    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    boxes = [bbox(it[0], it[2], it[3]) for it in items]
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            bi, bj = boxes[i], boxes[j]
            if bi[2] < bj[0] or bj[2] < bi[0] or bi[3] < bj[1] or bj[3] < bi[1]:
                continue
            if root(i) != root(j) and touch(items[i], items[j]):
                parent[root(i)] = root(j)
    groups = {}
    for i, it in enumerate(items):
        groups.setdefault(root(i), []).append(it)
    return sorted(groups.values(), key=len)


def route_gap(copper, net, src, dst, width, layers, margin, soft=0):
    """The cheapest path of tracks and vias from any of `src`'s copper to any of `dst`'s (two
    groups of one net), on `layers`, clear of every other net: a Dijkstra search on a GRID mm
    grid, other nets' copper grown by the clearance plus half the track, a via allowed wherever
    one fits. The window is the two groups' nearest anchors plus `margin`. Returns
    ([(layer, [points])], [via centres]) or None."""
    import heapq
    _, p, q = min((math.dist(p, q), p, q) for a in src for p in anchors(a) for b in dst for q in anchors(b))
    x0, y0 = min(p[0], q[0]) - margin, min(p[1], q[1]) - margin
    x1, y1 = max(p[0], q[0]) + margin, max(p[1], q[1]) + margin
    nx, ny = int((x1 - x0) / GRID) + 1, int((y1 - y0) / GRID) + 1
    N, L = nx * ny, len(layers)
    half = width / 2
    window = (x0 - 1, y0 - 1, x1 + 1, y1 + 1)
    ex0, ey0, ex1, ey1 = copper.edge
    edge = bytearray(N)
    for j in range(ny):
        py = y0 + j * GRID
        for i in range(nx):
            px = x0 + i * GRID
            if min(px - ex0, ex1 - px, py - ey0, ey1 - py) < EDGE + half:
                edge[j * nx + i] = 1
    blocked, softs = [], []
    for layer in layers:
        b, s = bytearray(edge), bytearray(N)

        def mark(box, dist, grow, arr=None):
            arr = b if arr is None else arr
            i0, i1 = max(0, int((box[0] - grow - x0) / GRID)), min(nx - 1, int((box[2] + grow - x0) / GRID) + 1)
            j0, j1 = max(0, int((box[1] - grow - y0) / GRID)), min(ny - 1, int((box[3] + grow - y0) / GRID) + 1)
            for j in range(j0, j1 + 1):
                py, row = y0 + j * GRID, j * nx
                for i in range(i0, i1 + 1):
                    if not arr[row + i] and dist((x0 + i * GRID, py)) < grow:
                        arr[row + i] = 1
        grow = CLEAR + half + GRID * 0.75          # the grid's own error, on the safe side
        for n, kind, g, h in copper.near(copper.grid[layer], window):
            if n == net:
                continue
            # with `soft`, other nets' tracks and vias may be crossed at a cost (rip_up takes them
            # up); pads and ground never
            arr = s if soft and kind != "box" and n != copper.gnd and n not in copper.hard_nets else None
            if kind == "circle":
                mark(bbox(kind, g, h), lambda pt, g=g, h=h: math.dist(pt, g) - h, grow, arr)
            elif kind == "seg":
                mark(bbox(kind, g, h), lambda pt, g=g, h=h: seg_point(g[0], g[1], pt) - h, grow, arr)
            else:
                mark(g, lambda pt, g=g: box_point(g, pt), grow, arr)
        for c, r, n in copper.near(copper.hole_grid, window):
            if n != net:
                mark((c[0] - r, c[1] - r, c[0] + r, c[1] + r), lambda pt, c=c, r=r: math.dist(pt, c) - r,
                     HOLE_CLEAR + half + GRID * 0.75)
        if layer == pcbnew.F_Cu:
            for k in copper.no_via:                # the fiducial keep-outs forbid tracks too
                mark(k, lambda pt, k=k: box_point(k, pt), half + GRID)
        blocked.append(b)
        softs.append(s)
    lidx = {l: k for k, l in enumerate(layers)}

    def cells_of(items):
        out = set()
        for it in items:
            ks = range(L) if it[1] is None else [lidx[it[1]]] if it[1] in lidx else []
            box = bbox(it[0], it[2], it[3])
            for j in range(max(0, int((box[1] - y0) / GRID)), min(ny - 1, int((box[3] - y0) / GRID) + 1) + 1):
                for i in range(max(0, int((box[0] - x0) / GRID)), min(nx - 1, int((box[2] - x0) / GRID) + 1) + 1):
                    if inside(it, (x0 + i * GRID, y0 + j * GRID)):
                        for k in ks:
                            if not blocked[k][j * nx + i]:
                                out.add(k * N + j * nx + i)
        return out
    start, goal = cells_of(src), cells_of(dst)
    if not start or not goal:
        return None
    dist, prev, heap = {}, {}, []
    for s in start:
        dist[s], prev[s] = 0.0, None
        heap.append((0.0, s))
    heapq.heapify(heap)
    via_ok = {}
    d2 = math.sqrt(2)
    moves = ((1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0), (1, 1, d2), (1, -1, d2), (-1, 1, d2), (-1, -1, d2))
    hit = None
    while heap:
        d, s = heapq.heappop(heap)
        if d > dist.get(s, 1e18):
            continue
        if s in goal:
            hit = s
            break
        k, rem = divmod(s, N)
        j, i = divmod(rem, nx)
        bk, sk = blocked[k], softs[k]
        for di, dj, cost in moves:
            a, c = i + di, j + dj
            if 0 <= a < nx and 0 <= c < ny and not bk[c * nx + a]:
                t, nd = k * N + c * nx + a, d + cost + (soft if sk[c * nx + a] else 0)
                if nd < dist.get(t, 1e18):
                    dist[t], prev[t] = nd, s
                    heapq.heappush(heap, (nd, t))
        if i % 2 == 0 and j % 2 == 0:              # vias on a 0.1 mm lattice
            ok = via_ok.get(rem)
            if ok is None:
                ok = via_ok[rem] = copper.via_fits(net, (x0 + i * GRID, y0 + j * GRID), hard_only=bool(soft))
            if ok:
                # in rip_up, a via over another net's track takes it up too, at a cost
                vcost = VIA_COST + (10 * soft if soft and any(sl[rem] for sl in softs) else 0)
                for k2 in range(L):
                    t, nd = k2 * N + rem, d + vcost
                    if k2 != k and not blocked[k2][rem] and nd < dist.get(t, 1e18):
                        dist[t], prev[t] = nd, s
                        heapq.heappush(heap, (nd, t))
    if hit is None:
        return None
    path, s = [], hit
    while s is not None:
        k, rem = divmod(s, N)
        j, i = divmod(rem, nx)
        path.append((k, (x0 + i * GRID, y0 + j * GRID)))
        s = prev[s]
    path.reverse()
    runs, vias = [], []
    for k, pt in path:
        if runs and runs[-1][0] == k:
            runs[-1][1].append(pt)
        else:
            if runs:
                vias.append(pt)
            runs.append((k, [pt]))
    out = []
    for k, pts in runs:
        keep = [pts[0]]                             # only the corners
        for a, b, c in zip(pts, pts[1:], pts[2:]):
            if abs((b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])) > 1e-9:
                keep.append(b)
        if len(pts) > 1:
            keep.append(pts[-1])
        if len(keep) > 1:
            out.append((layers[k], keep))
    # a last check of every segment against the real copper, beyond the grid's approximation
    # (a soft path crosses other nets by design: rip_up takes them up first)
    for layer, pts in out:
        if not soft and any(copper.gap_seg(layer, net, a, b) - half < CLEAR - 1e-3 for a, b in zip(pts, pts[1:])):
            return None
    return out, vias


def route_leftovers(board, skip=("GND",), nets=None):
    """Join each net's separate groups of copper (the connections the autorouter left), smallest
    group first, to the rest of its net; `nets` (net codes) limits it to those. Returns (joined,
    failed [(net name, near point)])."""
    copper = Copper(board)
    layers = [l for l in copper.layers if l != pcbnew.In1_Cu]
    names = {p.GetNetCode(): p.GetNetname() for fp in board.GetFootprints() for p in fp.Pads() if p.GetNetCode() > 0}
    joined, failed = 0, []
    for net, name in sorted(names.items(), key=lambda kv: kv[1]):
        if name in skip or nets is not None and net not in nets:
            continue
        widths = POWER_WIDTHS if name.startswith(("+", "-")) else (MIN_TRACK,)
        given_up = set()   # the items of groups no route reaches (by uuid: pcbnew's wrappers are made afresh)
        while True:
            groups = clusters(net_items(board, net))
            if len(groups) < 2:
                break
            todo = [g for g in groups if not any(it[4].m_Uuid.AsString() in given_up for it in g)]
            if not todo:
                break
            src = todo[0]
            dst = [it for g in groups if g is not src for it in g]
            got = None
            for margin in (3.0, 8.0):
                for w in widths:
                    got = route_gap(copper, net, src, dst, w, layers, margin)
                    if got:
                        break
                if got:
                    break
            if not got:
                given_up |= {it[4].m_Uuid.AsString() for it in src}
                failed.append((name, anchors(src[0])[0]))
                continue
            segs, vias = got
            for v in vias:
                via = pcbnew.PCB_VIA(board)
                via.SetPosition(pcbnew.VECTOR2I(int(v[0] * MM), int(v[1] * MM)))
                via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
                set_via(via, VIA_D, VIA_HOLE)
                via.SetNetCode(net)
                board.Add(via)
                copper.add_via(net, v, VIA_D / 2, VIA_HOLE / 2)
            for layer, pts in segs:
                for a, b in zip(pts, pts[1:]):
                    trk = pcbnew.PCB_TRACK(board)
                    trk.SetStart(pcbnew.VECTOR2I(int(a[0] * MM), int(a[1] * MM)))
                    trk.SetEnd(pcbnew.VECTOR2I(int(b[0] * MM), int(b[1] * MM)))
                    trk.SetWidth(int(w * MM))
                    trk.SetLayer(layer)
                    trk.SetNetCode(net)
                    board.Add(trk)
                    copper.add_seg(net, layer, a, b, w / 2)
            joined += 1
    return joined, failed


SOFT = 20   # rip_up: the cost of a grid cell inside another net's track, against 1 for free board


def unconnected(board):
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    board.BuildConnectivity()
    return board.GetConnectivity().GetUnconnectedCount(False)


def crossed(board, net, segs, vias, width, keep=()):
    """Other nets' tracks and vias (never ground's, nor `keep`'s) too close to a planned path."""
    gnd = board.FindNet("GND").GetNetCode()
    half, out = width / 2, []
    pieces = [(l, a, b) for l, pts in segs for a, b in zip(pts, pts[1:])]
    for t in board.GetTracks():
        if t.GetNetCode() in (net, gnd) or t.GetNetCode() in keep:
            continue
        if t.Type() == pcbnew.PCB_VIA_T:
            c, r = mm(t.GetPosition()), via_width(t) / 2
            hit = (any(seg_point(a, b, c) - r - half < CLEAR for _l, a, b in pieces)
                   or any(math.dist(v, c) - r - VIA_D / 2 < CLEAR for v in vias))
        else:
            A, B, h = mm(t.GetStart()), mm(t.GetEnd()), t.GetWidth() / MM / 2
            hit = (any(l == t.GetLayer() and seg_seg(a, b, A, B) - half - h < CLEAR for l, a, b in pieces)
                   or any(seg_point(A, B, v) - h - VIA_D / 2 < CLEAR for v in vias))
        if hit:
            out.append(t)
    return out


def rip_up(board, tmp, failed, steps=40, memory=6, tries=3, slack=1):
    """The connections route_leftovers could not make, once more, as a chain of swaps. A net
    takes the cheapest path that may cross other nets' tracks and vias (never pads or ground),
    the tracks it crosses are taken up, and route_leftovers routes this net and the nets taken
    up. The swap stands if the board has fewer connections to make, or this net was joined and
    at most `slack` more are open than before (the nets it displaced are tried next); otherwise the
    board goes back as it was (saved to `tmp` first). The last `memory` nets joined may not be
    taken up, so the chain moves on instead of undoing itself; each net gets `tries` turns.
    The best board seen is the one returned. Returns (board, swaps kept, nets still open)."""
    best_path = tmp[:-len(".kicad_pcb")] + "_best.kicad_pcb"
    current = best = unconnected(board)
    pcbnew.SaveBoard(best_path, board)
    queue = sorted({name for name, _p in failed})
    recent, kept, turns = [], 0, {}
    for _step in range(steps):
        if not queue or best == 0:
            break
        name = queue.pop()                     # the newest first: the net just displaced
        net = board.FindNet(name).GetNetCode()
        groups = clusters(net_items(board, net))
        if len(groups) < 2 or turns.get(name, 0) >= tries:
            continue
        turns[name] = turns.get(name, 0) + 1
        copper = Copper(board)
        copper.hard_nets = {board.FindNet(n).GetNetCode() for n in recent}
        layers = [l for l in copper.layers if l != pcbnew.In1_Cu]
        src, dst = groups[0], [it for g in groups[1:] for it in g]
        got = None
        for margin in (3.0, 8.0):
            got = route_gap(copper, net, src, dst, MIN_TRACK, layers, margin, soft=SOFT)
            if got:
                break
        if not got:
            print(f"  rip-up {name}: no path even across other nets", flush=True)
            continue
        pcbnew.SaveBoard(tmp, board)
        taken = crossed(board, net, *got, MIN_TRACK, keep=copper.hard_nets)
        nets = {net} | {t.GetNetCode() for t in taken}
        names = sorted({t.GetNetname() for t in taken})
        for t in taken:
            board.Delete(t)
        # this net first, into the room just made; then the nets taken up
        _joined, fails = route_leftovers(board, nets={net})
        _joined, more = route_leftovers(board, nets=nets - {net})
        fails += more
        remove_dangling(board)
        now = unconnected(board)
        joined = len(clusters(net_items(board, net))) < len(groups)
        # fewer open; or this net joined at the cost of no more than `slack` others for now (the
        # chain may find them a way next, and the best board seen is what comes back)
        ok = now < current or joined and now <= current + slack and now <= best + slack
        print(f"  rip-up {name}: took up {len(taken)} pieces of {names}; open {current} -> {now}"
              f"{', kept' if ok else ', undone'}", flush=True)
        if not ok:
            board = pcbnew.LoadBoard(tmp)
            queue.insert(0, name)              # back of the queue: another turn later
            continue
        current, kept = now, kept + 1
        recent = (recent + [name])[-memory:]
        open_now = sorted({n for n, _p in fails})
        queue = [q for q in queue if q not in open_now] + open_now
        if now < best:
            best = now
            pcbnew.SaveBoard(best_path, board)
    if current > best:
        board = pcbnew.LoadBoard(best_path)
    os.remove(best_path)
    still = sorted(n for n in set(turns) | set(queue) if len(clusters(net_items(board, board.FindNet(n).GetNetCode()))) > 1)
    return board, kept, still


def remove_dangling(board, skip=("GND",)):
    """Vias and tracks that lead nowhere (the autorouter's dead ends), removed until none is left:
    a via joined on fewer than two layers, a track with an end that touches nothing."""
    removed = 0
    nets = {t.GetNetCode() for t in board.GetTracks()} - {board.FindNet(n).GetNetCode() for n in skip}
    while True:
        gone = []
        for net in nets:
            items = net_items(board, net)
            for it in items:
                if it[0] == "box":
                    continue
                others = [o for o in items if o is not it]
                if it[0] == "circle":
                    links = [o for o in others if touch(it, o)]
                    if any(o[1] is None for o in links):
                        continue
                    if len({o[1] for o in links}) < 2:
                        gone.append(it[4])
                elif any(not any((o[1] is None or o[1] == it[1]) and inside(o, e) for o in others) for e in it[2]):
                    gone.append(it[4])
        if not gone:
            return removed
        for obj in gone:
            board.Delete(obj)   # not Remove: that hands the item to Python, and the next GetTracks() fails
        removed += len(gone)


def path_length(segs):
    return sum(math.dist(a, b) for _l, pts in segs for a, b in zip(pts, pts[1:]))


def fan_in_decoupling(board, max_len=6.0):
    """Before routing: a short direct track from each decoupling capacitor to the pin its
    Decouples field names (a field naming only the part: its nearest pin on the capacitor's
    net), locked, so the pin's current loop runs through its own capacitor. Left to itself the
    autorouter joins capacitor and pin to the rail wherever is easiest: on 2026-10-16 half the
    IC power pins were more than 4 mm of track from any capacitor. Returns (made, failed)."""
    import re
    copper = Copper(board)
    layers = [l for l in copper.layers if l != pcbnew.In1_Cu]
    fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
    made, failed = 0, []
    for ref, fp in sorted(fps.items()):
        if not fp.HasFieldByName("Decouples"):
            continue
        text = fp.GetFieldText("Decouples")
        m = re.search(r"\b([UA]\d+)\b(?:.*?\bpin (\d+))?", text)
        if not m or m.group(1) not in fps:
            continue
        cap = [p for p in fp.Pads() if p.GetNetname() and p.GetNetname() != "GND"]
        if len(cap) != 1:
            continue
        cap = cap[0]
        net = cap.GetNetCode()
        ic = [p for p in fps[m.group(1)].Pads() if p.GetNetCode() == net
              and (m.group(2) is None or p.GetNumber() == m.group(2))]
        if not ic:
            failed.append(f"{ref} ({text}: not on the capacitor's net)")
            continue
        ic = min(ic, key=lambda p: math.dist(mm(p.GetPosition()), mm(cap.GetPosition())))
        items = net_items(board, net)
        groups = clusters(items)
        group_of = lambda pad: next(g for g in groups if any(it[4].m_Uuid.AsString() == pad.m_Uuid.AsString() for it in g))
        src, dst = group_of(cap), group_of(ic)
        if src is dst:
            continue
        name = cap.GetNetname()
        widths = POWER_WIDTHS if name.startswith(("+", "-")) else (0.2, MIN_TRACK)
        same = [l for l in layers if cap.IsOnLayer(l) and ic.IsOnLayer(l)]
        got = None
        for use in ([same[:1]] if same else []) + [layers]:   # one face without a via first
            for w in widths:
                got = route_gap(copper, net, src, dst, w, use, margin=1.5)
                if got and path_length(got[0]) <= max_len:
                    break
                got = None
            if got:
                break
        if not got:
            failed.append(f"{ref}->{m.group(1)}.{ic.GetNumber()}")
            continue
        segs, vias = got
        for v in vias:
            via = pcbnew.PCB_VIA(board)
            via.SetPosition(pcbnew.VECTOR2I(int(v[0] * MM), int(v[1] * MM)))
            via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
            set_via(via, VIA_D, VIA_HOLE)
            via.SetNetCode(net)
            via.SetLocked(True)
            board.Add(via)
            copper.add_via(net, v, VIA_D / 2, VIA_HOLE / 2)
        for layer, pts in segs:
            for a, b in zip(pts, pts[1:]):
                trk = pcbnew.PCB_TRACK(board)
                trk.SetStart(pcbnew.VECTOR2I(int(a[0] * MM), int(a[1] * MM)))
                trk.SetEnd(pcbnew.VECTOR2I(int(b[0] * MM), int(b[1] * MM)))
                trk.SetWidth(int(w * MM))
                trk.SetLayer(layer)
                trk.SetNetCode(net)
                trk.SetLocked(True)
                board.Add(trk)
                copper.add_seg(net, layer, a, b, w / 2)
        made += 1
    return made, failed


def main(src, out=None):
    src = os.path.abspath(src)
    pro = src[:-len(".kicad_pcb")] + ".kicad_pro"
    out = os.path.abspath(out or src[:-len(".kicad_pcb")] + "_finished.kicad_pcb")
    load_rules(pro)
    print(f"Rules from the project: track {MIN_TRACK} mm, clearance {CLEAR - 0.005:.3f} mm")
    board = pcbnew.LoadBoard(src)
    print(f"Vias with their drill reset to keep a {MIN_RING} mm ring: {fix_vias(board)}")
    print(f"Tracks widened to {MIN_TRACK} mm: {widen_tracks(board)}")
    # a working copy, with the project's rules beside it (DRC without them runs KiCad's defaults)
    tmp = out[:-len(".kicad_pcb")] + "_partial.kicad_pcb"
    tmp_pro = tmp[:-len(".kicad_pcb")] + ".kicad_pro"
    if os.path.exists(pro):
        shutil.copy(pro, tmp_pro)
    for rnd in range(3):   # until no copper fault is left (the leftover router's own work is checked too)
        faults = take_up_faults(board, tmp)
        print(f"Round {rnd + 1}: tracks and vias taken up from copper faults: {faults}")
        if rnd and not faults:
            break
        print(f"Dead-end tracks and vias removed: {remove_dangling(board)}")
        joined, failed = route_leftovers(board)
        print(f"Leftover connections routed: {joined}; no route found: "
              f"{[(n, tuple(round(v, 1) for v in p)) for n, p in failed]}")
        if failed:
            board, kept, still = rip_up(board, tmp, failed)
            print(f"Rip-up and reroute: {kept} swaps kept; nets still open: {still}")
        print(f"Dead-end tracks and vias removed: {remove_dangling(board)}")
        pcbnew.SaveBoard(tmp, board)
        targets = unconnected_ground_pads(tmp, pro)
        placed, failed = stitch_ground(board, targets)
        print(f"Ground pads unconnected: {len({(r, n) for r, n, _ in targets})}; vias placed: {placed}; no room: {failed}")
    for f in (tmp, tmp_pro):
        if os.path.exists(f):
            os.remove(f)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    board.BuildConnectivity()
    pcbnew.SaveBoard(out, board)
    if os.path.exists(pro):
        shutil.copy(pro, out[:-len(".kicad_pcb")] + ".kicad_pro")
    print(f"Unconnected after finishing: {board.GetConnectivity().GetUnconnectedCount(False)}")
    print(f"Finished board: {out}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)

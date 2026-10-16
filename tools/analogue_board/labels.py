"""Silkscreen labels on a routed board, and the wiring map that goes with them.

Run with KiCad's own Python, after finish.py:

    /Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 \\
        tools/analogue_board/labels.py <board> <routed.kicad_pcb>

The wiring holes stand 2.54 mm apart in columns of up to four, so a label fits only beside a
group, never between holes. David's choice (2026-10-16): **block numbers**. Holes are gathered
into blocks as they stand on the board, a bank or a utility group with a free row or column
beside it, numbered W1, W2 ... from the top left, down the left side, then down the right.
Within a block, holes count in reading order: row by row from the top, left column first. The
label sits in the free row above the block, else below it, else beside it, on both faces where
it fits. Ground holes stay square.

Each test point gets a short name beside it.

Writes the labels into the board, and <board>/output/wiring_map.md: every block's holes with
their signals, and every test point. Then 1:1 PDFs of each face's silkscreen, pads and outline
(output/wiring_map_outward_face.pdf, output/wiring_map_deck_face.pdf), to print at 100 %.
"""

import os
import subprocess
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import placement as P  # noqa: E402
import variant  # noqa: E402
import wiring  # noqa: E402

KICAD_CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
MM = 1e6
BLOCK_H, BLOCK_W = 1.0, 0.15     # block labels: text height and stroke, mm (JLC: 1.0 / 0.15 or more reads)
TP_H, TP_W = 0.8, 0.12           # test point names
GAP = 0.15                       # label to pad, part or other label, mm
EDGE = 0.4                       # label to board edge, mm
COL_X = {**wiring.COLUMNS, "SI": P.STRIPS["right"]["inner"]}   # "SI": the right strip's inner column
LEFT = ("LO", "LI")
TP_NAMES = {"MOD_5V": "5V MOD", "I2S_DIN": "DIN", "I2S_DOUT": "DOUT", "EXP_INT": "INT",
            "SPIA_MOSI": "A MOSI", "SPIA_MISO": "A MISO", "SPIA_SCK": "A SCK",
            "SPIB_MOSI": "B MOSI", "SPIB_MISO": "B MISO", "SPIB_SCK": "B SCK",
            "CS_595": "CS 595", "CS_ADC": "CS ADC", "CS_DAC": "CS DAC", "CS_POT": "CS POT"}


def holes():
    """(column, slot, net) for every wiring hole this board has: the channel holes and the
    utility groups, their nets from the board's own pads."""
    out = [(c, s, n) for c, s, _b, _sh, n in wiring.PLAN]
    sizes = {"J101": wiring.J101_SIZE, "J303": 2, "J1001": 6, "J703": 4, "J704": 5, "J603": 6}
    for ref, (col, first) in wiring.UTILITY.items():
        out += [(col, first + i, f"{ref}.{i + 1}") for i in range(sizes[ref])]
    return out


def blocks(hs):
    """The holes in blocks: on each side, columns grouped (LO with LI on the left; R, and the
    right strip's empty positions, on the right), rows run together where no row is empty."""
    sides = {"left": [h for h in hs if h[0] in LEFT], "R": [h for h in hs if h[0] == "R"],
             "RS": [h for h in hs if h[0] == "RS"]}
    out = []
    for side, members in sides.items():
        rows = sorted({s for _c, s, _n in members})
        run = []
        for r in rows + [None]:
            if run and (r is None or r != run[-1] + 1):
                cells = sorted((h for h in members if run[0] <= h[1] <= run[-1]),
                               key=lambda h: (h[1], LEFT.index(h[0]) if h[0] in LEFT else 0))
                out.append({"side": side, "rows": (run[0], run[-1]), "holes": cells})
                run = []
            if r is not None:
                run.append(r)
    # top left first, down the left side, then the right
    out.sort(key=lambda b: ({"left": 0, "R": 1, "RS": 2}[b["side"]], b["rows"][0]))
    for i, b in enumerate(out):
        b["name"] = f"W{i + 1}"
    return out


def text(board, s, x, y, layer, h, w, angle=0.0):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(s)
    t.SetLayer(layer)
    t.SetTextSize(pcbnew.VECTOR2I(int(h * MM), int(h * MM)))
    t.SetTextThickness(int(w * MM))
    t.SetPosition(pcbnew.VECTOR2I(int(x * MM), int(y * MM)))
    t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER)
    t.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
    if angle:
        t.SetTextAngleDegrees(angle)
    if layer == pcbnew.B_SilkS:
        t.SetMirrored(True)
    return t


def box_of(item):
    bb = item.GetBoundingBox()
    return (bb.GetLeft() / MM, bb.GetTop() / MM, bb.GetRight() / MM, bb.GetBottom() / MM)


def overlaps(a, b, gap=GAP):
    return not (a[2] + gap <= b[0] or b[2] + gap <= a[0] or a[3] + gap <= b[1] or b[3] + gap <= a[1])


class Space:
    """What a label on one face must stay clear of: every pad on that face (through-hole pads on
    both), every part's courtyard on that face, the board edge, and the labels already placed."""

    def __init__(self, board):
        self.board = board
        e = board.GetBoardEdgesBoundingBox()
        self.edge = (e.GetLeft() / MM + EDGE, e.GetTop() / MM + EDGE, e.GetRight() / MM - EDGE, e.GetBottom() / MM - EDGE)
        self.boxes = {pcbnew.F_SilkS: [], pcbnew.B_SilkS: []}
        for fp in board.GetFootprints():
            for p in fp.Pads():
                for silk, cu in ((pcbnew.F_SilkS, pcbnew.F_Cu), (pcbnew.B_SilkS, pcbnew.B_Cu)):
                    if p.IsOnLayer(cu):
                        self.boxes[silk].append(box_of(p))
            for silk, crt, cu in ((pcbnew.F_SilkS, pcbnew.F_CrtYd, pcbnew.F_Cu), (pcbnew.B_SilkS, pcbnew.B_CrtYd, pcbnew.B_Cu)):
                if fp.GetLayer() == cu and fp.GetAttributes() & pcbnew.FP_THROUGH_HOLE == 0:
                    poly = fp.GetCourtyard(crt)
                    if poly.OutlineCount():
                        bb = poly.BBox()
                        self.boxes[silk].append((bb.GetLeft() / MM, bb.GetTop() / MM, bb.GetRight() / MM, bb.GetBottom() / MM))

    def fits(self, t, silk, ignore=None):
        b = box_of(t)
        x0, y0, x1, y1 = self.edge
        if b[0] < x0 or b[1] < y0 or b[2] > x1 or b[3] > y1:
            return False
        return not any(overlaps(b, o) for o in self.boxes[silk] if o is not ignore)

    def take(self, t, silk):
        self.boxes[silk].append(box_of(t))


def block_spots(b, occupied, origin):
    """Where a block's label may go, in order: the free row above it, the free row below it,
    then beside it. (x, y) on the board: placement.py's coordinates (from the board's top left
    corner) plus `origin`, where that corner sits in KiCad's."""
    ox, oy = origin
    r0, r1 = b["rows"]
    cols = sorted({c for c, _s, _n in b["holes"]}, key=lambda c: COL_X[c])
    xs = [COL_X[c] for c in cols]
    xm = (min(xs) + max(xs)) / 2
    spots = []
    for r in (r0 - 1, r1 + 1):
        if 1 <= r <= 40 and not any((c, r) in occupied for c in cols):
            spots.append((xm, P.strip_y(r)))
    ym = (P.strip_y(r0) + P.strip_y(r1)) / 2
    if b["side"] == "left":
        spots += [(max(xs) + 2.4, P.strip_y(r)) for r in range(r0, r1 + 1)] + [(max(xs) + 2.4, ym)]
    elif b["side"] == "R":
        spots += [(min(xs) - 2.4, P.strip_y(r)) for r in range(r0, r1 + 1)] + [(min(xs) - 2.4, ym)]
    else:                                    # the right strip's empty positions: its inner column
        spots += [(COL_X["SI"], P.strip_y(r)) for r in range(r0, r1 + 1)] + [(COL_X["SI"], ym)]
    return [(x + ox, y + oy) for x, y in spots]


def main(path):
    variant.require()
    board = pcbnew.LoadBoard(path)
    hs = holes()
    occupied = {(c, s) for c, s, _n in hs}
    bl = blocks(hs)
    ours = {b["name"] for b in bl} | set(TP_NAMES.values()) | {fp.Pads()[0].GetNetname() for fp in board.GetFootprints()
                                                              if fp.GetReference().startswith("TP")}
    for d in list(board.GetDrawings()):        # a re-run replaces its own labels
        if d.Type() == pcbnew.PCB_TEXT_T and d.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS) and d.GetText() in ours:
            board.Delete(d)
    space = Space(board)
    # the board's top left corner: the outline's own line, not its bounding box's outer edge
    e = board.GetBoardEdgesBoundingBox()
    line = max((d.GetWidth() / MM for d in board.GetDrawings() if d.GetLayer() == pcbnew.Edge_Cuts), default=0.0)
    origin = (e.GetLeft() / MM + line / 2, e.GetTop() / MM + line / 2)
    placed, missed = 0, []
    lines = [f"# Wiring map: {variant.TITLE}", "",
             "Generated by `tools/analogue_board/labels.py`. Each block's label (W1, W2 ...) is on the",
             "board's silkscreen beside the block. Holes count in reading order: row by row from the",
             "top, left column first. Ground holes are square. Rows are the edge strip positions.", ""]
    for b in bl:
        faces = []
        for silk in (pcbnew.B_SilkS, pcbnew.F_SilkS):        # the deck face first
            spots = block_spots(b, occupied, origin)
            for x, y, ang in [(x, y, 0) for x, y in spots] + [(x, y, 90) for x, y in spots]:
                t = text(board, b["name"], x, y, silk, BLOCK_H, BLOCK_W, ang)
                if space.fits(t, silk):
                    board.Add(t)
                    space.take(t, silk)
                    faces.append("deck" if silk == pcbnew.B_SilkS else "outward")
                    break
        if faces:
            placed += 1
        else:
            missed.append(b["name"])
        r0, r1 = b["rows"]
        lines += [f"## {b['name']}: rows {r0}-{r1}, {'left' if b['side'] == 'left' else 'right'} side"
                  f" (label on the {' and '.join(faces) or 'no'} face{'s' if len(faces) > 1 else ''})", "",
                  "| Hole | Column | Row | Signal |", "|---|---|---|---|"]
        for i, (c, s, n) in enumerate(b["holes"]):
            lines.append(f"| {i + 1} | {c} | {s} | {n} |")
        lines.append("")
    # test points: a short name beside each
    tps = sorted((fp for fp in board.GetFootprints() if fp.GetReference().startswith("TP")),
                 key=lambda f: f.GetReference())
    lines += ["## Test points", "", "| Test point | Signal | Face | x, y (mm from the top left) | Labelled |",
              "|---|---|---|---|---|"]
    e = board.GetBoardEdgesBoundingBox()
    tp_missed = []
    for fp in tps:
        net = fp.Pads()[0].GetNetname()
        name = TP_NAMES.get(net, net)
        silk = pcbnew.F_SilkS if fp.GetLayer() == pcbnew.F_Cu else pcbnew.B_SilkS
        c = (fp.GetPosition().x / MM, fp.GetPosition().y / MM)
        done = False
        # beside the pad, nearest first, along it or turned across it
        tries = [(r * dx, r * dy, ang) for r in (1.2, 1.6, 2.0, 2.6, 3.2, 4.0)
                 for dx, dy in ((0, -1), (0, 1), (1, 0), (-1, 0)) for ang in (0, 90)]
        tries.sort(key=lambda d: abs(d[0]) + abs(d[1]))
        for dx, dy, ang in tries:
            t = text(board, name, c[0] + dx, c[1] + dy, silk, TP_H, TP_W, ang)
            if space.fits(t, silk):
                board.Add(t)
                space.take(t, silk)
                done = True
                break
        if not done:
            tp_missed.append(fp.GetReference())
        lines.append(f"| {fp.GetReference()} | {net} | {'outward' if silk == pcbnew.F_SilkS else 'deck'} | "
                     f"{c[0] - e.GetLeft() / MM:.1f}, {c[1] - e.GetTop() / MM:.1f} | {'yes' if done else 'no room'} |")
    pcbnew.SaveBoard(path, board)
    out = os.path.join(variant.DIR, "output")
    with open(os.path.join(out, "wiring_map.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    for name, layers, mirror in (("wiring_map_outward_face.pdf", "F.SilkS,F.Mask,Edge.Cuts", False),
                                 ("wiring_map_deck_face.pdf", "B.SilkS,B.Mask,Edge.Cuts", True)):
        args = [KICAD_CLI, "pcb", "export", "pdf", "--layers", layers, "--include-border-title", "-o",
                os.path.join(out, name), path]
        if mirror:
            args.insert(4, "--mirror")
        subprocess.run(args, capture_output=True, text=True)
    print(f"Blocks: {len(bl)}, labelled {placed}; no room for: {missed}")
    print(f"Test points: {len(tps)}, labelled {len(tps) - len(tp_missed)}; no room for: {tp_missed}")
    print(f"Wiring map: {os.path.join(out, 'wiring_map.md')}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("labels.py <board> <routed.kicad_pcb>")
    main(sys.argv[2])

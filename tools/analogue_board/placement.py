"""Checkpoint 2 geometry: the board outline, the n8synth edge strips, and where each compute
module and the power header sit. Origin at the board's top-left corner, x right, y down, mm,
seen from the outward face (the face the modules plug into).

The outline and strips come from the n8synth template (spec §4.1). The module and header
positions are proposals for checkpoint 2; checkpoint 3 (placement) starts from them.
"""

import os

from sexpr import find, find_all, parse

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
PRETTY = os.path.join(REPO, "hardware", "analogue_board", "analogue_board.pretty")
KICAD_FP = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints"

BOARD_W, BOARD_H = 49.6, 103.0
STRIPS = {"left": {"outer": 1.92, "inner": 4.46}, "right": {"outer": 47.68, "inner": 45.14}}
DECK_CELLS = [(1, 10), (16, 25), (31, 40)]   # edge positions a deck header occupies
BREADBOARD_HEADER = {"x": [15.91 + 2.54 * i for i in range(8)], "y": [98.82, 101.36]}  # the breadboard's 2x8, dropped


def strip_y(n):
    """Edge position n (1-40) along both strips."""
    return 2.07 + 2.54 * (n - 1)


# ESP32-P4-WIFI6: Pico pinout and pin rows, 71 x 21 mm; beyond the Pico's outline it extends
# 3.2 mm at the USB end and 16.9 mm at the far (antenna) end (docs/analogue_board_esp32p4.md)
P4_EXTRA_USB, P4_EXTRA_FAR = 3.2, 16.9
# Teensy 4.1: a card in its microSD socket stands just under 3 mm past the far end (measured
# by David on the checkpoint 2 printout, 2026-10-15), so the Teensy sits 3 mm lower
TEENSY_SD_CARD = 3.0
USB_KEEPOUT = (15.0, 30.0)   # width across the module, length beyond its USB end (spec §4.3)
TOP_MARGIN = 0.5             # from the top edge to the furthest thing on a module

# Module placements: centre line x and the far (non-USB) end y of the module body.
# USB ends point down, toward the board centre; far ends toward the top edge (spec §4.3).
ARRANGEMENTS = {
    # A, the schematic's pin map: no shared holes. Pico rows at 15.91 / 33.69; Teensy rows one
    # pitch outside (13.37) and two pitches inside (28.61). The Pico sits 16.9 mm down so an
    # ESP32-P4 in its socket ends at the top margin; the Teensy sits 3 mm down so its SD card does.
    "A": {"pico": {"cx": 24.8, "far": TOP_MARGIN + P4_EXTRA_FAR},
          "teensy": {"cx": 20.99, "far": TOP_MARGIN + TEENSY_SD_CARD}},
    # B, for comparison: Teensy's left row in the Pico's left-row holes, right row one pitch
    # inside the Pico's; the Pico moved down so the holes line up (7 pitches below the Teensy's).
    "B": {"pico": {"cx": 24.8, "far": TOP_MARGIN + TEENSY_SD_CARD + 17.68},
          "teensy": {"cx": 23.53, "far": TOP_MARGIN + TEENSY_SD_CARD}},
}

# 2x5 shrouded power header, KiCad IDC-Header_2x05_P2.54mm_Vertical in its own orientation
# (two columns, pin 1 top-left, key notch on the left). Bottom right: clear of every USB
# keep-out, beside the right strip, which is the rear edge in 6HP.
HEADER_PIN1 = (36.83, 83.35)   # shroud 1.7 mm from the strip's wiring holes, 1.35 mm from the keep-outs


def _load(path):
    with open(path, encoding="utf-8") as f:
        return parse(f.read())


def footprint(path):
    """Pads [(number, x, y, shape)] and the F.Fab outline lines [((x1, y1), (x2, y2))] of a .kicad_mod."""
    fp = _load(path)
    pads = []
    for p in find_all(fp, "pad"):
        at = find(p, "at")
        pads.append((str(p[1]), float(at[1]), float(at[2]), str(p[3])))
    lines = []
    for kind in ("fp_line", "fp_rect"):
        for g in find_all(fp, kind):
            if find(g, "layer")[1] != "F.Fab":
                continue
            s, e = find(g, "start"), find(g, "end")
            a, b = (float(s[1]), float(s[2])), (float(e[1]), float(e[2]))
            if kind == "fp_line":
                lines.append((a, b))
            else:
                lines += [(a, (b[0], a[1])), ((b[0], a[1]), b), (b, (a[0], b[1])), ((a[0], b[1]), a)]
    return pads, lines


def module(fp_name, cx, far):
    """A module socket turned 180° (pin 1 and USB at the bottom), its body centred on cx with the
    far end at y = far. Returns pads [(number, x, y, shape)] and the body box (x0, y0, x1, y1)."""
    pads, lines = footprint(os.path.join(PRETTY, fp_name + ".kicad_mod"))
    xs = [v[0] for l in lines for v in l]
    ys = [v[1] for l in lines for v in l]
    # 180° about the footprint origin: (x, y) -> (-x, -y)
    bx0, bx1, by0, by1 = -max(xs), -min(xs), -max(ys), -min(ys)
    dx, dy = cx - (bx0 + bx1) / 2, far - by0
    pads = [(n, -x + dx, -y + dy, s) for n, x, y, s in pads]
    return pads, (bx0 + dx, by0 + dy, bx1 + dx, by1 + dy)


def header():
    pads, lines = footprint(os.path.join(KICAD_FP, "Connector_IDC.pretty", "IDC-Header_2x05_P2.54mm_Vertical.kicad_mod"))
    x0, y0 = HEADER_PIN1
    return ([(n, x + x0, y + y0, s) for n, x, y, s in pads],
            [((a[0] + x0, a[1] + y0), (b[0] + x0, b[1] + y0)) for a, b in lines])


def layout(name):
    """Everything for one arrangement: modules with their bodies, USB ends and keep-outs."""
    arr = ARRANGEMENTS[name]
    out = {}
    pp, pb = module("Pico2_Socket", **arr["pico"])
    tp, tb = module("Teensy41_Socket", **arr["teensy"])
    p4 = (pb[0], pb[1] - P4_EXTRA_FAR, pb[2], pb[3] + P4_EXTRA_USB)
    for key, pads, body in (("pico", pp, pb), ("p4", pp, p4), ("teensy", tp, tb)):
        cx, usb = (body[0] + body[2]) / 2, body[3]
        kw, kl = USB_KEEPOUT
        out[key] = {"pads": pads, "body": body, "usb_y": usb,
                    "keepout": (cx - kw / 2, usb, cx + kw / 2, min(usb + kl, BOARD_H)),
                    "keepout_clipped": usb + kl > BOARD_H}
    return out


def shared_holes(lay, tol=0.01):
    """(pico pin, teensy pin, x, y) for every hole the two sockets share."""
    return [(pn, tn, px, py) for pn, px, py, _ in lay["pico"]["pads"] for tn, tx, ty, _ in lay["teensy"]["pads"]
            if abs(px - tx) < tol and abs(py - ty) < tol]

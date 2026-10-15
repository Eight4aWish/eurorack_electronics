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


# ------------------------------------------------------------------ checkpoint 3: floorplan
# Both faces carry parts (decided 2026-10-15: double-sided assembly). F = outward face (modules,
# parts up to 2.5 mm under the modules, taller parts elsewhere); B = deck face (low parts only).
# Wiring-field holes sit in columns lined up with the edge-strip positions: two beside the
# left strip (the only one wired in 6HP), one beside the right strip, stopping above J201.
HOLE_COLUMNS = {"left_outer": 7.0, "left_inner": 9.54, "right": 42.6}
HOLE_GROUPS = {  # ref -> (column, first edge position); the group runs down from there, beside its circuit
    "J401": ("left_outer", 1),    # CV jacks (12), beside the ADC and jack switches
    "J601": ("left_outer", 14),   # pot wipers and tops (12), beside the MCP3208
    "J703": ("left_outer", 27),   # I2C for a wired display (4), beside the expander
    "J1001": ("left_outer", 34),  # TRS MIDI (6), beside the H11L1
    "J802": ("left_inner", 1),    # jack-detect probe (14), beside the CV holes it serves
    "J101": ("left_inner", 15),   # spare GPIO, MIDI links, RUN (6)
    "J801": ("left_inner", 22),   # gate ins (5), beside the LM393s
    "J701": ("left_inner", 27),   # buttons, switches, encoder (11), beside the TCA9555
    "J301": ("right", 1),         # audio in (3), beside the codec
    "J302": ("right", 4),         # audio out (3)
    "J303": ("right", 7),         # codec reset (2)
    "J602": ("right", 10),        # gate outs (10), beside their clamps
    "J603": ("right", 20),        # gate expansion (6)
    "J704": ("right", 26),        # WS2812 chain (5), beside its buffer
}

# Anchors: ref -> (x, y, rotation, face) of the footprint origin (its centre, for ICs), board
# coordinates as seen from the outward face. Analogue at the top, under the modules and furthest
# from the buck; logic below it; power in the bottom-right corner around J201; MIDI bottom left
# (the H11L1 is ~4 mm tall, so it stays outside the modules). Every SO/TSSOP courtyard is at least
# 7.4 mm wide, so the 9.7 mm channel between the module rows takes one IC across, on each face.
CENTRE_X = 22.26   # between the Pico's left row and the Teensy's right row
ANCHORS = {
    # outward face (F)
    "U401": (21.0, 9.6, 0, "F"),        # ADS8688, inputs toward the CV holes on the left
    "U301": (35.5, 8.6, 0, "F"),        # PCM3060, top right beside the audio holes
    "U501": (CENTRE_X, 21.0, 0, "F"),   # DAC8568
    "U502": (CENTRE_X, 30.6, 0, "F"),   # TL074 CV1-4
    "U503": (CENTRE_X, 41.0, 0, "F"),   # TL074 CV5-8
    "U601": (CENTRE_X, 53.0, 0, "F"),   # MCP3208
    "U801": (CENTRE_X, 63.0, 0, "F"),   # LM393 gates 1-2
    "U701": (19.5, 77.0, 0, "F"),       # TCA9555
    "U1002": (17.5, 97.0, 0, "F"),      # H11L1 (tall)
    "U202": (29.5, 96.5, 90, "F"),      # L78M05 DPAK
    "L201": (29.5, 86.5, 0, "F"),       # buck inductor (4 mm tall)
    "U703": (37.9, 70.6, 0, "F"),       # AHCT1G125 LED buffer, beside J704
    # deck face (B)
    "U403": (21.0, 6.0, 0, "B"),        # DG412 CV5-6 + spares
    "U402": (21.0, 13.0, 0, "B"),       # DG412 CV1-4
    "U504": (CENTRE_X, 22.5, 0, "B"),   # TL074 offset buffer + spares
    "U302": (35.5, 8.6, 0, "B"),        # TL074 audio, under the codec
    "U602": (CENTRE_X, 34.0, 0, "B"),   # 74HCT595
    "U802": (CENTRE_X, 63.0, 0, "B"),   # LM393 gates 3-4
    "U702": (19.5, 77.0, 0, "B"),       # M24C64, under the TCA9555
}


def anchor_positions():
    """ref -> (x, y, rotation, face) for every anchored part and every wiring-hole column."""
    pos = dict(ANCHORS)
    for ref, (col, first) in HOLE_GROUPS.items():
        pos[ref] = (HOLE_COLUMNS[col], strip_y(first), 0, "F")
    return pos


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

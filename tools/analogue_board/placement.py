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
# The right strip serves only the 10HP deck (6HP wires everything to the left strip), whose
# headers sit at 1-10, 16-25 and 31-40: positions 11-15 and 26-30 get no holes (David,
# 2026-10-15; tools/visualizer/boards/n8synth-10hp.json, headerSpans and gapRows). The left
# strip keeps all 40: a 6HP deck claims every position except 19-22, which the 10HP deck uses.
STRIP_OMIT = {"left": set(), "right": set(range(11, 16)) | set(range(26, 31))}
# Positions 10, 16 and 31 sit inside the 10HP deck's 10-pin headers but no cell uses them: they
# keep the outer hole (the header pin) and lose the inner wiring hole (David, 2026-10-15).
STRIP_OMIT_INNER = {"left": set(), "right": {10, 16, 31}}
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
# The wiring field (wiring.py): four banks of channel holes, one per quarter of the board, each
# with a mix of every channel type, in two columns beside the left strip and one beside the right.
import wiring  # noqa: E402

HOLE_COLUMNS = wiring.COLUMNS
HOLE_GROUPS = {g["ref"]: (g["column"], g["slot"]) for g in wiring.groups()}   # ref -> (column, first slot)
HOLE_GROUPS.update(wiring.UTILITY)

# Anchors: ref -> (x, y, rotation, face) of the footprint origin (its centre, for ICs), board
# coordinates as seen from the outward face. Every SO/TSSOP courtyard is at least 7.4 mm wide, so
# the 9.7 mm channel between the module rows takes one IC across, on each face.
# Each chip that talks to the module sits level with the module pins of its bus (both modules'
# pins for one bus sit at similar heights): SPI-A (ADC, DAC) at 19-38 mm, SPI-B (pot ADC, gate
# register) at 15-34, I2S (codec) at 34-56, I2C (expander, EEPROM) at 43-59. The CV output
# op-amps, which only talk to the DAC and the jack switches, take the top-right corner. Power stays
# in the bottom-right corner around J201, furthest from the converters; MIDI bottom left (the
# H11L1 is ~4 mm tall, so it stays outside the modules).
CENTRE_X = 22.26   # between the Pico's left row and the Teensy's right row
ANCHORS = {
    # outward face (F)
    "U401": (21.0, 9.6, 0, "F"),        # ADS8688 (SPI-A), inputs toward the CV holes on the left
    "U501": (CENTRE_X, 21.0, 0, "F"),   # DAC8568 (SPI-A)
    "U601": (CENTRE_X, 30.3, 0, "F"),   # MCP3208 (SPI-B)
    "U301": (CENTRE_X, 42.3, 0, "F"),   # PCM3060 (I2S), level with the I2S pins
    "U701": (CENTRE_X, 53.3, 0, "F"),   # TCA9555 (I2C)
    "U801": (CENTRE_X, 61.8, 0, "F"),   # LM393 gates 1-2
    "U502": (35.5, 8.6, 0, "F"),        # TL074 CV1-4, top right near the DAC and the jack switches
    "U1002": (17.5, 97.0, 0, "F"),      # H11L1 (tall)
    "U202": (29.5, 96.5, 90, "F"),      # L78M05 DPAK
    "L201": (29.5, 86.5, 0, "F"),       # buck inductor (4 mm tall)
    "U201": (29.5, 80.8, 0, "F"),       # TPS54308 beside its inductor: the switching loop stays on one face
    "J702": (37.4, 74.6, 0, "F"),       # Qwiic, vertical: cable straight up, just below the modules, near their
                                        # I2C pins, outside the USB plug zones and clear of J201 (David, 2026-10-15)
    "FID901": (12.4, 1.8, 0, "F"),      # fiducials: three corners of the free area
    "FID902": (38.5, 1.8, 0, "F"),
    "FID903": (24.0, 101.6, 0, "F"),
    # deck face (B)
    "U403": (21.0, 6.0, 0, "B"),        # DG412 CV5-6 + spares
    "U402": (21.0, 13.0, 0, "B"),       # DG412 CV1-4
    "U504": (CENTRE_X, 22.5, 0, "B"),   # TL074 offset buffer + spares
    "U503": (35.5, 8.6, 0, "B"),        # TL074 CV5-8, top right under U502
    "U302": (CENTRE_X, 31.8, 0, "B"),   # TL074 audio, just above the codec, leaving the space under it for
                                        # the codec's decoupling
    "U602": (38.15, 36.0, 90, "F"),     # 74HCT595 TSSOP, sideways in the right channel: gates 5-8 go to the right
                                        # banks beside it, gates 1-4 cross to the left banks (wiring.py)
    "U802": (CENTRE_X, 61.8, 0, "B"),   # LM393 gates 3-4
    "U702": (CENTRE_X, 53.3, 0, "B"),   # M24C64 (I2C), under the TCA9555
    "U1001": (16.0, 89.0, 0, "B"),      # AHCT1G125 MIDI out, under the MIDI corner
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

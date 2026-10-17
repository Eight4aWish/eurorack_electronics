"""Checkpoint 2 geometry: the board outline, the n8synth edge strips, and where each compute
module and the power header sit. Origin at the board's top-left corner, x right, y down, mm,
seen from the outward face (the face the modules plug into).

The outline and strips come from the n8synth template (spec §4.1). The module and header
positions are proposals for checkpoint 2; checkpoint 3 (placement) starts from them.
"""

import os

import variant
from sexpr import find, find_all, parse

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
PRETTY = os.path.join(variant.SHARED, "analogue_board.pretty")
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
# Rev A is two boards, one module each (David, 2026-10-16), both modules on the board's centre
# line at the heights checkpoint 2 settled: the Pico 16.9 mm down so an ESP32-P4 in its socket
# ends at the top margin, the Teensy 3 mm down so its SD card does.
BOARD_MODULES = {"pico": {"cx": BOARD_W / 2, "far": TOP_MARGIN + P4_EXTRA_FAR},
                 "teensy": {"cx": BOARD_W / 2, "far": TOP_MARGIN + TEENSY_SD_CARD}}
# Checkpoint 2's two arrangements, with both modules on one board; A is the shared board's
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
# Both faces carry parts (decided 2026-10-15: double-sided assembly). F = outward face (module,
# parts up to 2.5 mm under it, taller parts elsewhere); B = deck face (low parts only).
# Wiring-field holes sit in columns lined up with the edge-strip positions: two beside the
# left strip (the only one wired in 6HP), one beside the right strip, stopping above J201.
# The wiring field (wiring.py): four banks of channel holes, one per quarter of the board, each
# with a mix of every channel type, in two columns beside the left strip and one beside the right.
import wiring  # noqa: E402

HOLE_COLUMNS = wiring.COLUMNS
HOLE_GROUPS = {g["ref"]: (g["column"], g["slot"]) for g in wiring.groups()}   # ref -> (column, first slot)
HOLE_GROUPS.update(wiring.UTILITY)

# Anchors: ref -> (x, y, rotation, face) of the courtyard centre, board coordinates as seen from
# the outward face. Every SO/TSSOP courtyard is 7.4-7.7 mm wide (5.4-5.5 mm turned sideways).
# Each board has its own floorplan, because each module brings its buses out at different pins:
# every chip that talks to the module sits level with its bus pins, on the side they are on.
# Power stays in the bottom-right corner around J201, furthest from the converters; MIDI bottom
# left (the H11L1 is ~4 mm tall, so it stays clear of the module).
ANCHORS_COMMON = {
    "U1002": (17.5, 97.0, 0, "F"),      # H11L1 (tall)
    "U202": (29.5, 96.5, 90, "F"),      # L78M05 DPAK
    "L201": (29.5, 86.5, 0, "F"),       # buck inductor (4 mm tall)
    "U201": (29.5, 80.8, 0, "F"),       # TPS54308 beside its inductor: the switching loop stays on one face
    "J702": (37.4, 74.6, 0, "F"),       # Qwiic, vertical: cable straight up, just below the module, outside the
                                        # USB plug zone and clear of J201 (David, 2026-10-15)
    "FID901": (12.4, 1.8, 0, "F"),      # fiducials: three corners of the free area
    "FID902": (38.5, 1.8, 0, "F"),
    "FID903": (24.0, 101.6, 0, "F"),
    "U1001": (16.0, 89.0, 0, "B"),      # AHCT1G125 MIDI out, under the MIDI corner
}
ANCHORS_BOARD = {
    # Pico 2 / ESP32-P4: rows at x 15.91 and 33.69 from y 18.8 to 67.0, a 15.2 mm channel between
    # their courtyards and a 6.4 mm lane right of the right row. SPI-A and I2S come out on the left
    # row (y 19-31 and 34-52), SPI-B, the gate inputs and I2C on the right (y 21-34, 39-47, 54-59).
    # Above the pins, under the ESP32-P4's antenna end (parts up to 2.5 mm), the CV converters and
    # their op-amps: the analogue corner, furthest from the buck.
    "pico": {
        # outward face (F)
        "U401": (16.0, 9.0, 0, "F"),        # ADS8688 (SPI-A), top left beside the CV holes
        "U501": (24.8, 7.5, 0, "F"),        # DAC8568 (SPI-A), between the ADC and its output op-amps
        "U502": (33.5, 9.0, 0, "F"),        # TL074 CV1-4
        "U601": (27.8, 25.5, 0, "F"),       # MCP3208 (SPI-B), right of the channel beside the SPI-B pins
        "U301": (21.8, 43.5, 0, "F"),       # PCM3060 (I2S), left of the channel beside the I2S pins
        "U701": (27.8, 57.0, 0, "F"),       # TCA9555 (I2C), right of the channel beside the I2C pins
        "U602": (38.15, 35.0, 90, "F"),     # 74HCT595 (SPI-B), sideways in the right lane
        "U801": (38.15, 45.0, 90, "F"),     # LM393 gates 1-2, right lane beside the gate-input pins
        # deck face (B)
        "U403": (16.0, 6.0, 0, "B"),        # DG412 CV5-6 + spares, under the ADC
        "U402": (16.0, 13.0, 0, "B"),       # DG412 CV1-4
        "U504": (24.8, 7.5, 0, "B"),        # TL074 offset buffer + spares, under the DAC
        "U503": (33.5, 9.0, 0, "B"),        # TL074 CV5-8, under U502
        "U302": (21.8, 31.5, 0, "B"),       # TL074 audio, above the codec, leaving the space under it for its decoupling
        "U702": (27.8, 57.0, 0, "B"),       # M24C64 (I2C), under the TCA9555
        "U802": (38.15, 45.0, 90, "B"),     # LM393 gates 3-4, under U801
    },
    # Teensy 4.1: rows at x 17.18 and 32.42 from y 4.8 to 63.2, a 12.7 mm channel between their
    # courtyards and a 7.6 mm lane right of the right row; everything above y 64.5 is under the
    # Teensy (parts up to 2.5 mm). Top to bottom the buses come out SPI-B (y 15-20), SPI-A (30-38),
    # then I2S (40-56), I2C (43-53) and the gate inputs (48-56, right row), so the chips stack
    # down the channel in that order, and the right lane takes the op-amps and comparators.
    "teensy": {
        # outward face (F)
        "U601": (24.8, 10.0, 0, "F"),       # MCP3208 (SPI-B)
        "U602": (37.5, 18.0, 90, "F"),      # 74HCT595 (SPI-B), sideways in the right lane
        "U401": (24.8, 22.0, 0, "F"),       # ADS8688 (SPI-A)
        "U501": (37.5, 39.0, 90, "F"),      # DAC8568 (SPI-A), sideways in the right lane beside its output op-amps:
                                            # three SPI lines cross the right row instead of eight outputs
        "U502": (37.5, 30.0, 0, "F"),       # TL074 CV1-4, right lane
        "U301": (24.8, 47.0, 0, "F"),       # PCM3060 (I2S)
        "U801": (37.5, 52.0, 90, "F"),      # LM393 gates 1-2, right lane beside the gate-input pins
        "U701": (24.8, 58.5, 0, "F"),       # TCA9555 (I2C)
        # deck face (B)
        "U403": (24.8, 7.0, 0, "B"),        # DG412 CV5-6 + spares
        "U402": (24.8, 13.5, 0, "B"),       # DG412 CV1-4
        "U504": (24.8, 34.0, 0, "B"),       # TL074 offset buffer + spares
        "U503": (37.5, 30.0, 0, "B"),       # TL074 CV5-8, under U502
        "U302": (37.5, 41.0, 0, "B"),       # TL074 audio, right lane beside the codec
        "U802": (37.5, 52.0, 90, "B"),      # LM393 gates 3-4, under U801
        "U702": (24.8, 58.5, 0, "B"),       # M24C64 (I2C), under the TCA9555
    },
    # The shared board (both modules, arrangement A), as committed at 56660f9: the 9.7 mm channel
    # between the Pico's left row and the Teensy's right row takes one IC across on each face, in
    # the order of the buses (both modules' pins for one bus sit at similar heights)
    "shared": {
        # outward face (F)
        "U401": (21.0, 9.6, 0, "F"),        # ADS8688 (SPI-A), inputs toward the CV holes on the left
        "U501": (22.26, 21.0, 0, "F"),      # DAC8568 (SPI-A)
        "U601": (22.26, 30.3, 0, "F"),      # MCP3208 (SPI-B)
        "U301": (22.26, 42.3, 0, "F"),      # PCM3060 (I2S), level with the I2S pins
        "U701": (22.26, 53.3, 0, "F"),      # TCA9555 (I2C)
        "U801": (22.26, 61.8, 0, "F"),      # LM393 gates 1-2
        "U502": (35.5, 8.6, 0, "F"),        # TL074 CV1-4, top right near the DAC and the jack switches
        "U602": (38.15, 36.0, 90, "F"),     # 74HCT595 TSSOP, sideways in the right channel
        # deck face (B)
        "U403": (21.0, 6.0, 0, "B"),        # DG412 CV5-6 + spares
        "U402": (21.0, 13.0, 0, "B"),       # DG412 CV1-4
        "U504": (22.26, 22.5, 0, "B"),      # TL074 offset buffer + spares
        "U503": (35.5, 8.6, 0, "B"),        # TL074 CV5-8, top right under U502
        "U302": (22.26, 31.8, 0, "B"),      # TL074 audio, just above the codec
        "U802": (22.26, 61.8, 0, "B"),      # LM393 gates 3-4
        "U702": (22.26, 53.3, 0, "B"),      # M24C64 (I2C), under the TCA9555
    },
}
# The single board with the core set (shared_core): the auto-placer packs everything toward the
# module rows, leaving the lower third below the modules almost empty on both faces while the
# channel between the rows is too crowded for the fine-pitch chips' ground vias (David's
# observation, 2026-10-16). The slow chips move down there: the I2C expander and its EEPROM,
# and the gate-input comparators. Their tracks grow by ~20 mm, harmless for I2C, gates and
# buttons. The converters and the codec stay level with their bus pins. The 595 stays central to
# its four gate-out holes. Parts there sit in the modules' USB plug zone, well under its 8 mm limit.
# The two DG412s sat under the ADC with their pad columns exactly opposite its own (x 18.19 and
# 23.91 on both faces), so every via from either chip fought for the same two strips: 9 of the
# last 14 connections were there. Each now turns 90 degrees, its pad rows across the body of the
# chip above it, so its vias land in the body's shadow, clear of that chip's pins; and U402
# (CV1-4) moves under the CV1-4 op-amp U502, the space U503 left (2026-10-16).
ANCHORS_BOARD["shared_core"] = {**ANCHORS_BOARD["shared"],
                                "U403": (21.0, 9.6, 90, "B"),   # DG412 CV5-6 + spares, across the ADC's body
                                "U402": (35.5, 8.6, 90, "B"),   # DG412 CV1-4, across U502's body
                                "U701": (19.0, 75.0, 0, "F"),   # TCA9555 (I2C)
                                "U702": (19.0, 75.0, 0, "B"),   # M24C64 (I2C), under it
                                "U801": (28.0, 74.5, 0, "F"),   # LM393 gates 1-2
                                "U802": (28.0, 74.5, 0, "B")}   # LM393 gates 3-4, under it
# The Pico board with the core set and MIDI: the Pico floorplan, with shared_core's fix for the
# DG412s, which sat under the ADC with their pad columns opposite its own (U503 is not fitted in
# the core set, so U402 takes its place under U502)
# U602 moves out of the lane beside the Pico's right header row into the empty pocket to its
# right, where the right column has no holes (slots 12-16) and the right strip none (11-15),
# leaving the lane to the module's tracks (David, 2026-10-16)
# The chips placed level with their bus pins move down with the module (variant MODULE_DROP);
# the converters and op-amps above it stay, and get the room
_LEVEL_WITH_PINS = ("U601", "U301", "U701", "U801", "U302", "U702", "U802")
ANCHORS_BOARD["pico_core_midi"] = {**ANCHORS_BOARD["pico"],
                                   **{r: (x, y + variant.MODULE_DROP, rot, f) for r, (x, y, rot, f)
                                      in ANCHORS_BOARD["pico"].items() if r in _LEVEL_WITH_PINS},
                                   # The top of the board with no chip over another on the opposite face
                                   # (David, 2026-10-17): every failure on this board came back to chips over
                                   # chips there, their vias fencing each other's pins in. Outward face: the
                                   # ADC on the left, lowered clear of the top edge and the fiducial
                                   # keep-out; the DAC and U502 turned and one above the other on the right,
                                   # in the width the right-top bank's move freed (wiring.MOVES). Deck face:
                                   # the DG412s and U504 where the outward face has no chip, the middle of
                                   # the band and below the ADC
                                   "U401": (17.2, 11.0, 0, "F"),   # ADS8688
                                   "U502": (35.5, 7.3, 90, "F"),   # TL074 CV1-4
                                   "U501": (35.5, 16.8, 90, "F"),  # DAC8568, nearer the module's SPI pins
                                   "U402": (27.0, 8.5, 0, "B"),    # DG412 CV1-4
                                   "U504": (27.0, 20.5, 0, "B"),   # TL074 offset buffer + spares
                                   "U403": (17.2, 21.5, 0, "B"),   # DG412 CV5-6 + spares
                                   # the +3V3A LDO out of the top band's middle, still central to the DAC,
                                   # the ADC and the pot ADC it feeds (David, 2026-10-17)
                                   "U203": (24.5, 24.0, 0, "F"),   # XC6206 3.3 V analogue LDO
                                   # the strip's gap now holds wiring holes: the 595 moves left into the lane
                                   # beside the module, upright, ~3.3 mm clear of its header row
                                   "U602": (40.5, 33.5, 90, "F"),  # 74HCT595
                                   # the LDO out from under the module's lower end, as on the Teensy board
                                   "U204": (17.5, 82.0, 0, "F"),   # XC6206 3.3 V LDO, below JP201
                                   # LM393 gates 1-2: right and down into the right column's gap at slots
                                   # 21-23 (pots 7-8 and fixed CV dropped), 7.5 mm tall, its own height:
                                   # the parts above it get room (David, 2026-10-16)
                                   "U801": (39.4, 55.4, 90, "F")}
# The Teensy board with the core set and MIDI: the Teensy floorplan as it stands (its DG412s sit
# above the ADC, not under it), for review by eye before routing
ANCHORS_BOARD["teensy_core_midi"] = {
    # every Teensy-floorplan chip sits level with its bus pins, so all move down with the module
    **{r: (x, y + variant.MODULE_DROP, rot, f) for r, (x, y, rot, f) in ANCHORS_BOARD["teensy"].items()},
    # David's review (2026-10-16): the LDO and its capacitors left and down, out from under the
    # module's lower end; the 595 out of the crowded right lane into the void left of the left
    # header row, where the inner wiring column has no holes (slots 15-20). By straight-line track
    # to its pins the 595 is no worse there (216 mm against 220); every other chip measured best
    # where it was
    "U204": (13.0, 77.0, 0, "F"),     # XC6206 3.3 V LDO
    "U602": (12.6, 40.6, 90, "F"),    # 74HCT595, sideways in the left void
    # with the right column's holes from slot 10 to 23 moved into the strip (wiring.MOVES), the
    # right-lane chips slide right, leaving a lane beside the module's right header row
    "U502": (41.5, 30.0, 0, "F"),     # TL074 CV1-4
    "U501": (40.5, 39.0, 90, "F"),    # DAC8568, sideways
    "U801": (40.5, 52.0, 90, "F"),    # LM393 gates 1-2
    "U802": (40.5, 52.0, 90, "B")}    # LM393 gates 3-4, under it
ANCHORS = {**ANCHORS_COMMON, **ANCHORS_BOARD.get(variant.FLOORPLAN, {})}


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


def _entry(pads, body):
    cx, usb = (body[0] + body[2]) / 2, body[3]
    kw, kl = USB_KEEPOUT
    return {"pads": pads, "body": body, "usb_y": usb,
            "keepout": (cx - kw / 2, usb, cx + kw / 2, min(usb + kl, BOARD_H)),
            "keepout_clipped": usb + kl > BOARD_H}


def _modules(where, keys):
    out = {}
    if "pico" in keys:
        pp, pb = module("Pico2_Socket", **where["pico"])
        out["pico"] = _entry(pp, pb)
        out["p4"] = _entry(pp, (pb[0], pb[1] - P4_EXTRA_FAR, pb[2], pb[3] + P4_EXTRA_USB))
    if "teensy" in keys:
        out["teensy"] = _entry(*module("Teensy41_Socket", **where["teensy"]))
    return out


def layout(name):
    """Checkpoint 2: both modules in one arrangement, with their bodies, USB ends and keep-outs."""
    return _modules(ARRANGEMENTS[name], ("pico", "teensy"))


def boards_layout():
    """Every module where its own board puts it (the Pico's entry also stands for the P4), for the printout."""
    return _modules(BOARD_MODULES, ("pico", "teensy"))


def board_layout():
    """This board's modules, keyed "pico" / "teensy", each with its body, USB end and keep-out;
    with a Pico also the ESP32-P4's larger envelope ("p4"), which shares the Pico's pads. The
    shared board has both, interleaved as checkpoint 2's arrangement A."""
    variant.require()
    if len(variant.REF) == 2:
        return layout("A")
    where = {k: {**v, "far": v["far"] + variant.MODULE_DROP} for k, v in BOARD_MODULES.items()}
    return _modules(where, tuple(variant.REF))


def shared_holes(lay, tol=0.01):
    """(pico pin, teensy pin, x, y) for every hole the two sockets share."""
    return [(pn, tn, px, py) for pn, px, py, _ in lay["pico"]["pads"] for tn, tx, ty, _ in lay["teensy"]["pads"]
            if abs(px - tx) < tol and abs(py - ty) < tol]

"""Which of the two Rev A boards a run builds (David, 2026-10-16): one for a Raspberry Pi Pico 2
or an ESP32-P4 module in the Pico's pinout, one for a Teensy 4.1. Both come from this one
generator. They share every peripheral sheet, the project libraries, the edge strips and the
wiring field; the module, its supply details and the floorplan differ. With one module per
board, no module's signals have to cross the other's header rows.

Every script takes the board as its first argument, `pico` or `teensy` (or `shared`, the single
board with both footprints, kept for comparison):

    python3 tools/analogue_board/build.py teensy

build.py and pcb.py with no argument build the two boards, each in a fresh interpreter (the board
is fixed when the modules load). Code imported from elsewhere reads the ANALOGUE_BOARD environment
variable.
"""

import os
import subprocess
import sys

BOARDS = {
    # module socket reference -> which module it takes
    "pico": {"title": "Pico 2 / ESP32-P4", "modules": {"A101": "pico"}},
    "teensy": {"title": "Teensy 4.1", "modules": {"A101": "teensy"}},
    # the single board with both footprints interleaved (checkpoint 2's arrangement A), kept as a
    # trial to compare against the split (2026-10-16); the Teensy has shortened headers on it
    "shared": {"title": "Pico 2 / ESP32-P4 or Teensy 4.1", "modules": {"A101": "pico", "A102": "teensy"}},
    # routing experiment (David, 2026-10-16): the Pico board without the fixed-direction CV channels,
    # TRS MIDI or the Qwiic socket (a display wires to the I2C holes), and six pots, but keeping the
    # six switchable CV jacks and four gates each way; parts placed 0.4 mm apart and routed to
    # 0.127 mm rules, as Quilter did
    "pico_core": {"title": "Pico 2 / ESP32-P4, core set", "modules": {"A101": "pico"}, "floorplan": "pico",
                  "drop": {"fixed_cv", "midi", "qwiic"}, "pots": 6, "spacing": 0.4, "track": 0.127},
    # the single board again (both modules), with the core set plus TRS MIDI: six switchable CV
    # jacks, no fixed-direction CV, six pots, a display on the I2C holes only, and the Teensy on
    # full-length headers (David, 2026-10-16). Track and space 0.127 mm: 0.1 mm everywhere was
    # tried when four routes in a row ended 2 connections short, and routed worse (57 left after
    # stage 1 against 24, stage 2 crawling at 11 minutes a pass), 2026-10-16
    "shared_core": {"title": "Pico 2 / ESP32-P4 or Teensy 4.1, core set with MIDI",
                    "modules": {"A101": "pico", "A102": "teensy"}, "floorplan": "shared_core",
                    "drop": {"fixed_cv", "qwiic"}, "pots": 6, "spacing": 0.4, "track": 0.127, "teensy_full": True},
    # the shared_core feature set on a Pico 2 / ESP32-P4 board alone: two header rows instead of
    # four, and a 15.2 mm channel between them instead of 9.7 mm, where shared_core's last open
    # connections always were (David, 2026-10-16)
    # The module sits 8 mm lower than checkpoint 2 put it, giving the converters above it room
    # (David, 2026-10-16); the ESP32-P4's USB end still clears the buck at y 80.8.
    # After the Teensy board's route (David, 2026-10-16): no bus test points (every bus line can be
    # probed at the module socket), the rails' and ground's kept.
    "pico_core_midi": {"title": "Pico 2 / ESP32-P4, core set with MIDI", "modules": {"A101": "pico"},
                       "floorplan": "pico_core_midi", "drop": {"fixed_cv", "qwiic", "bus_tps"}, "pots": 6,
                       "spacing": 0.4, "track": 0.127, "module_drop": 8.0},
    # and on a Teensy 4.1 alone, on full-length headers (David, 2026-10-16: placement reviewed
    # by eye before it is routed)
    # The module stays where checkpoint 2 put it: 10 mm lower was tried, and no chip measured
    # better in the band it freed at the top (every Teensy-floorplan chip sits level with its bus
    # pins, so they moved down too), while it brought the codec, comparators and I2C chips 10 mm
    # nearer the buck (David, 2026-10-16)
    "teensy_core_midi": {"title": "Teensy 4.1, core set with MIDI", "modules": {"A101": "teensy"},
                         "floorplan": "teensy_core_midi", "drop": {"fixed_cv", "qwiic"}, "pots": 6, "spacing": 0.4,
                         "track": 0.127},
}
DEFAULT = ("pico", "teensy")   # what build.py and pcb.py build with no argument
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
SHARED = os.path.join(REPO, "hardware", "analogue_board")   # libraries, README, licence; one folder per board

BOARD = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] in BOARDS else os.environ.get("ANALOGUE_BOARD")
if BOARD is not None and BOARD not in BOARDS:
    raise SystemExit(f"ANALOGUE_BOARD must be one of: {', '.join(BOARDS)}")
NAME = f"analogue_board_{BOARD}" if BOARD else None
DIR = os.path.join(SHARED, BOARD) if BOARD else None
TITLE = BOARDS[BOARD]["title"] if BOARD else None
MODULES = BOARDS[BOARD]["modules"] if BOARD else {}        # ref -> "pico" | "teensy"
REF = {kind: ref for ref, kind in MODULES.items()}         # "pico" | "teensy" -> ref
HAS_PICO, HAS_TEENSY = "pico" in REF, "teensy" in REF
_B = BOARDS.get(BOARD, {})
DROP = _B.get("drop", set())          # features left out: "fixed_cv", "midi", "qwiic", "bus_tps"
FLOORPLAN = _B.get("floorplan", BOARD)   # whose placement anchors this board uses
SPACING = _B.get("spacing", 0.1)      # courtyard-to-courtyard gap the auto-placer keeps, mm
TRACK = _B.get("track", 0.15)         # default track width and clearance, mm
POTS = _B.get("pots", 8)              # pot channels on the MCP3208
TEENSY_FULL = _B.get("teensy_full", len(REF) == 1)   # every Teensy pin has a hole (else 20-28 left out)
MODULE_DROP = _B.get("module_drop", 0.0)   # a one-module board's module this much lower than checkpoint 2's, mm


def has(feature):
    return feature not in DROP


def require():
    if BOARD is None:
        raise SystemExit("Say which board: pico or teensy (the first argument, or ANALOGUE_BOARD=...)")


def run_each(script):
    """With no board named, run `script` once per board and exit with the combined result."""
    if BOARD is not None:
        return
    ok = True
    for b in DEFAULT:
        print(f"\n==== {BOARDS[b]['title']} board ({b})", flush=True)
        ok = subprocess.run([sys.executable, script, b, *sys.argv[1:]]).returncode == 0 and ok
    sys.exit(0 if ok else 1)

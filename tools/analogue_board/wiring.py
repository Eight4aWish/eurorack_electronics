"""The wiring field: every channel hole, its bank and its slot.

Four banks, one per quarter of the board, each with a mix of every channel type, so a panel part
anywhere on the deck has its channel close by (David, 2026-10-15): a 50/50 split left and right,
which still leaves a 6HP build (left strip only) plenty within reach. Pot and jack grounds go to
the deck's D bus, so each bank has one ground hole (for the D bus wire, or anything else).
Since 2026-10-16 (David, to ease routing) there is one gate out per bank and no jack detect, so
the banks are packed from the top of each.

Columns: two beside the left strip, one beside the right strip; slot n sits level with edge
position n. The right column stops at slot 30, above the power header.

Both the schematic (which hole groups each sheet places) and the placement (where each group
goes) read this table, so they cannot disagree. A run of adjacent slots in one column whose nets
come from the same schematic sheet becomes one footprint.
"""

import variant

COLUMNS = {"LO": 7.0, "LI": 9.54, "R": 42.6,     # x, board coordinates
           "RS": 47.68,   # the right strip's outer column, in its empty positions 11-15 and 26-30
           "RSI": 45.14}  # and its inner column there
BANK_NAMES = {"TL": "left top", "BL": "left bottom", "TR": "right top", "BR": "right middle"}
REF_BASE = {"cv": 410, "codec": 310, "pots": 610, "expander": 710, "gatein": 810}

# (column, slot, bank, sheet, net)
PLAN = [
    # ---- left top: slots 1-7, two columns side by side
    ("LO", 1, "TL", "cv", "CV1"), ("LI", 1, "TL", "cv", "CV2"),
    ("LO", 2, "TL", "cv", "CV5"), ("LI", 2, "TL", "cv", "CVI7"),
    ("LO", 3, "TL", "codec", "AIN1"), ("LI", 3, "TL", "gatein", "GIN1"),
    ("LO", 4, "TL", "pots", "POT1"), ("LI", 4, "TL", "pots", "POT2"),
    ("LO", 5, "TL", "pots", "POT_REF"), ("LI", 5, "TL", "pots", "GND"),
    ("LO", 6, "TL", "pots", "GOUT1"), ("LI", 6, "TL", "expander", "SW1"),
    ("LO", 7, "TL", "expander", "SW2"), ("LI", 7, "TL", "expander", "SW3"),
    # ---- left bottom: slots 21-26
    ("LO", 21, "BL", "cv", "CV3"), ("LI", 21, "BL", "cv", "CVO7"),
    ("LO", 22, "BL", "codec", "AOUT1"), ("LI", 22, "BL", "gatein", "GIN2"),
    ("LO", 23, "BL", "pots", "POT3"), ("LI", 23, "BL", "pots", "POT4"),
    ("LO", 24, "BL", "pots", "POT_REF"), ("LI", 24, "BL", "pots", "GND"),
    ("LO", 25, "BL", "pots", "GOUT2"), ("LI", 25, "BL", "expander", "SW4"),
    ("LO", 26, "BL", "expander", "SW5"),
    # ---- right top: slots 1-11
    ("R", 1, "TR", "cv", "CV4"), ("R", 2, "TR", "cv", "CVI8"),
    ("R", 3, "TR", "codec", "AIN2"),
    ("R", 4, "TR", "gatein", "GIN3"),
    ("R", 5, "TR", "pots", "POT5"), ("R", 6, "TR", "pots", "POT6"), ("R", 7, "TR", "pots", "POT_REF"),
    ("R", 8, "TR", "pots", "GOUT3"),
    ("R", 9, "TR", "expander", "SW6"), ("R", 10, "TR", "expander", "SW7"), ("R", 11, "TR", "expander", "GND"),
    # ---- right middle: slots 17-27
    ("R", 17, "BR", "cv", "CV6"), ("R", 18, "BR", "cv", "CVO8"),
    ("R", 19, "BR", "codec", "AOUT2"),
    ("R", 20, "BR", "gatein", "GIN4"),
    ("R", 21, "BR", "pots", "POT7"), ("R", 22, "BR", "pots", "POT8"), ("R", 23, "BR", "pots", "POT_REF"),
    ("R", 24, "BR", "pots", "GOUT4"),
    ("R", 25, "BR", "expander", "SW8"), ("R", 26, "BR", "expander", "SW9"), ("R", 27, "BR", "expander", "GND"),
]

# Groups that stay whole (their own refs and nets on their own sheets): column, first slot
UTILITY = {
    "J101": ("LO", 13),   # spare GPIO, MIDI links, and RUN on the Pico board (6; 5 on the Teensy board)
    "J303": ("LI", 13),   # codec reset (2)
    "J1001": ("LO", 30),  # TRS MIDI (6)
    "J703": ("RS", 26),   # I2C for a wired display (4): in the right strip's empty positions 26-29, which
                          # no deck header uses, clearing the left inner column (David, 2026-10-16)
    "J704": ("LO", 36),   # WS2812 chain (5)
    "J603": ("LI", 35),   # gate expansion (6)
}

# A board with a smaller feature set (variant.py) leaves out those channels' holes
DROPPED_NETS = set()
if not variant.has("fixed_cv"):
    DROPPED_NETS |= {"CVI7", "CVI8", "CVO7", "CVO8"}
DROPPED_NETS |= {f"POT{i}" for i in range(variant.POTS + 1, 9)}
PLAN = [e for e in PLAN if e[4] not in DROPPED_NETS
        and not (e[4] == "POT_REF" and e[2] == "BR" and variant.POTS <= 6)]   # pots 7-8 were the right-middle bank's
# One board's own moves, (column, slot) -> (column, slot). On the Teensy board the right column's
# holes level with the right-lane chips (U502, U501, U801) go to the right strip's empty positions
# 11-15, so those chips slide right, clear of the module's header row (David, 2026-10-16; the
# Pico board keeps the table as it is)
MOVES = {"teensy_core_midi": {("R", 10): ("RS", 11), ("R", 11): ("RS", 12),      # SW7, GND (right top)
                              ("R", 17): ("RS", 13), ("R", 19): ("RS", 14),      # CV6, AOUT2 (right middle)
                              ("R", 20): ("RS", 15)},                            # GIN4 (right middle)
         # On the Pico board the whole right-top bank goes there, both strip columns, so the right
         # column is empty from the top and the converters above the module spread out; the 595
         # leaves the pocket for the lane beside the module (David, 2026-10-16)
         "pico_core_midi": {("R", 1): ("RSI", 11), ("R", 3): ("RSI", 12), ("R", 4): ("RSI", 13),   # CV4, AIN2, GIN3
                            ("R", 5): ("RSI", 14), ("R", 6): ("RSI", 15),                          # POT5, POT6
                            ("R", 7): ("RS", 11), ("R", 8): ("RS", 12), ("R", 9): ("RS", 13),      # POT_REF, GOUT3, SW6
                            ("R", 10): ("RS", 14), ("R", 11): ("RS", 15)}}                         # SW7, GND
PLAN = [(*MOVES.get(variant.BOARD, {}).get((c, s), (c, s)), bank, sheet, net) for c, s, bank, sheet, net in PLAN]
if not variant.has("midi"):
    del UTILITY["J1001"]
J101_SIZE = (4 if variant.has("midi") else 2) + (1 if variant.HAS_PICO else 0) + 1   # spares (+ MIDI links), RUN, GND


def groups():
    """Hole footprints made from PLAN: [{ref, sheet, bank, column, slot, nets}], in a fixed order."""
    out, seq = [], {}
    for col in ("LO", "LI", "R", "RSI", "RS"):
        entries = sorted((e for e in PLAN if e[0] == col), key=lambda e: e[1])
        run = []
        for e in entries + [None]:
            if run and (e is None or e[1] != run[-1][1] + 1 or e[3] != run[-1][3] or e[2] != run[-1][2]):
                sheet = run[0][3]
                n = seq.get(sheet, 0)
                seq[sheet] = n + 1
                out.append({"ref": f"J{REF_BASE[sheet] + n}", "sheet": sheet, "bank": run[0][2], "column": col,
                            "slot": run[0][1], "nets": [r[4] for r in run]})
                run = []
            if e is not None:
                run.append(e)
    return out


def check():
    """Every slot used once, the right column within its 30 slots, every channel present once."""
    seen = {}
    for col, slot, *_ in PLAN:
        assert (col, slot) not in seen, f"slot {col}{slot} used twice"
        seen[(col, slot)] = 1
    for ref, (col, first) in UTILITY.items():
        size = {"J101": J101_SIZE, "J303": 2, "J1001": 6, "J703": 4, "J704": 5, "J603": 6}[ref]
        for s in range(first, first + size):
            assert (col, s) not in seen, f"{ref} overlaps slot {col}{s}"
            seen[(col, s)] = 1
    assert all(s <= 30 for c, s in seen if c == "R"), "right column ends at slot 30"
    # RS and RSI holes share the right strip's columns: only where the strip has no holes
    assert all(s in set(range(11, 16)) | set(range(26, 31)) for c, s in seen if c in ("RS", "RSI")), \
        "RS and RSI holes only in the right strip's empty positions 11-15 and 26-30"
    assert all(1 <= s <= 40 for c, s in seen), "slot out of range"
    nets = [e[4] for e in PLAN if e[4] not in ("GND", "POT_REF")]
    want = ([f"CV{i}" for i in range(1, 7)] + ["CVI7", "CVI8", "CVO7", "CVO8", "AIN1", "AIN2", "AOUT1", "AOUT2"]
            + [f"POT{i}" for i in range(1, 9)] + [f"GIN{i}" for i in range(1, 5)] + [f"GOUT{i}" for i in range(1, 5)]
            + [f"SW{i}" for i in range(1, 10)])
    want = [n for n in want if n not in DROPPED_NETS]
    assert sorted(nets) == sorted(want), f"channels missing or doubled: {sorted(set(want) ^ set(nets))}"
    return True


def place(sh, holes, sheet, at, max_y=268.0, col_dx=30.48):
    """Draw this sheet's hole groups on its schematic page, stacked down from `at`. KiCad's
    connector symbols are drawn about their middle, so each group's anchor sits below its pin 1
    by the symbol's own pin offset; the reference above and the value below get a pitch each."""
    from kicad_lib import symbol_pins
    x, y = at
    for g in [g for g in groups() if g["sheet"] == sheet]:
        n = len(g["nets"])
        pins = symbol_pins(f"Connector_Generic:Conn_01x{n:02d}", {})
        top = max(-p.y for p in pins if p.number == "1")      # pin 1 above the origin, sheet y down
        h = (n + 3) * 2.54                                      # reference, the pins, the value text
        if y + h > max_y:
            x, y = x + col_dx, at[1]
        holes(sh, (x, y + 2.54 - top), g["nets"], f"Holes, {BANK_NAMES[g['bank']]}", ref=g["ref"])
        y += h


check()

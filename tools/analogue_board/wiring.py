"""The wiring field: every channel hole, its bank and its slot.

Four banks, one per quarter of the board, each with a mix of every channel type, so a panel part
anywhere on the deck has its channel close by (David, 2026-10-15): a 50/50 split left and right,
which still leaves a 6HP build (left strip only) plenty within reach. Each input has its
jack-detect hole beside it: on the left in the inner column next to the input, on the right
directly below it. Pot and jack grounds go to the deck's D bus, so each bank has one ground hole
(for the D bus wire, or anything else).

Columns: two beside the left strip, one beside the right strip; slot n sits level with edge
position n. The right column stops at slot 30, above the power header.

Both the schematic (which hole groups each sheet places) and the placement (where each group
goes) read this table, so they cannot disagree. A run of adjacent slots in one column whose nets
come from the same schematic sheet becomes one footprint.
"""

COLUMNS = {"LO": 7.0, "LI": 9.54, "R": 42.6}     # x, board coordinates
BANK_NAMES = {"TL": "left top", "BL": "left bottom", "TR": "right top", "BR": "right middle"}
REF_BASE = {"cv": 410, "codec": 310, "pots": 610, "expander": 710, "gatein": 810}

# (column, slot, bank, sheet, net)
PLAN = [
    # ---- left top: slots 1-20
    ("LO", 1, "TL", "cv", "CV1"), ("LI", 1, "TL", "gatein", "PR1"),
    ("LO", 2, "TL", "cv", "CV2"), ("LI", 2, "TL", "gatein", "PR2"),
    ("LO", 3, "TL", "cv", "CV5"), ("LI", 3, "TL", "gatein", "PR3"),
    ("LO", 4, "TL", "cv", "CVI7"), ("LI", 4, "TL", "gatein", "PR4"),
    ("LO", 5, "TL", "codec", "AIN1"), ("LI", 5, "TL", "gatein", "PR5"),
    ("LO", 6, "TL", "gatein", "GIN1"), ("LI", 6, "TL", "gatein", "PR11"),
    ("LO", 7, "TL", "pots", "POT1"), ("LI", 7, "TL", "pots", "POT2"),
    ("LO", 8, "TL", "pots", "POT_REF"), ("LI", 8, "TL", "pots", "GND"),
    ("LO", 9, "TL", "pots", "GOUT1"), ("LI", 9, "TL", "pots", "GOUT2"),
    ("LO", 10, "TL", "expander", "SW1"), ("LI", 10, "TL", "expander", "SW2"),
    ("LO", 11, "TL", "expander", "SW3"),
    # ---- left bottom: slots 21-40
    ("LO", 21, "BL", "cv", "CV3"), ("LI", 21, "BL", "gatein", "PR6"),
    ("LO", 22, "BL", "cv", "CVO7"),
    ("LO", 23, "BL", "codec", "AOUT1"),
    ("LO", 24, "BL", "gatein", "GIN2"), ("LI", 24, "BL", "gatein", "PR12"),
    ("LO", 25, "BL", "pots", "POT3"), ("LI", 25, "BL", "pots", "POT4"),
    ("LO", 26, "BL", "pots", "POT_REF"), ("LI", 26, "BL", "pots", "GND"),
    ("LO", 27, "BL", "pots", "GOUT3"), ("LI", 27, "BL", "pots", "GOUT4"),
    ("LO", 28, "BL", "expander", "SW4"), ("LI", 28, "BL", "expander", "SW5"),
    # ---- right top: slots 1-16
    ("R", 1, "TR", "cv", "CV4"), ("R", 2, "TR", "gatein", "PR7"),
    ("R", 3, "TR", "cv", "CVI8"), ("R", 4, "TR", "gatein", "PR8"),
    ("R", 5, "TR", "codec", "AIN2"), ("R", 6, "TR", "gatein", "PR9"),
    ("R", 7, "TR", "gatein", "GIN3"), ("R", 8, "TR", "gatein", "PR13"),
    ("R", 9, "TR", "pots", "POT5"), ("R", 10, "TR", "pots", "POT6"), ("R", 11, "TR", "pots", "POT_REF"),
    ("R", 12, "TR", "pots", "GOUT5"), ("R", 13, "TR", "pots", "GOUT6"),
    ("R", 14, "TR", "expander", "SW6"), ("R", 15, "TR", "expander", "SW7"), ("R", 16, "TR", "expander", "GND"),
    # ---- right middle: slots 17-30
    ("R", 17, "BR", "cv", "CV6"), ("R", 18, "BR", "gatein", "PR10"),
    ("R", 19, "BR", "cv", "CVO8"),
    ("R", 20, "BR", "codec", "AOUT2"),
    ("R", 21, "BR", "gatein", "GIN4"), ("R", 22, "BR", "gatein", "PR14"),
    ("R", 23, "BR", "pots", "POT7"), ("R", 24, "BR", "pots", "POT8"), ("R", 25, "BR", "pots", "POT_REF"),
    ("R", 26, "BR", "pots", "GOUT7"), ("R", 27, "BR", "pots", "GOUT8"),
    ("R", 28, "BR", "expander", "SW8"), ("R", 29, "BR", "expander", "SW9"), ("R", 30, "BR", "expander", "GND"),
]

# Groups that stay whole (their own refs and nets on their own sheets): column, first slot
UTILITY = {
    "J101": ("LO", 13),   # spare GPIO, MIDI links, RUN (6)
    "J303": ("LI", 13),   # codec reset (2)
    "J1001": ("LO", 30),  # TRS MIDI (6)
    "J703": ("LI", 30),   # I2C for a wired display (4)
    "J704": ("LO", 36),   # WS2812 chain (5)
    "J603": ("LI", 35),   # gate expansion (6)
}


def groups():
    """Hole footprints made from PLAN: [{ref, sheet, bank, column, slot, nets}], in a fixed order."""
    out, seq = [], {}
    for col in ("LO", "LI", "R"):
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
        size = {"J101": 6, "J303": 2, "J1001": 6, "J703": 4, "J704": 5, "J603": 6}[ref]
        for s in range(first, first + size):
            assert (col, s) not in seen, f"{ref} overlaps slot {col}{s}"
            seen[(col, s)] = 1
    assert all(s <= 30 for c, s in seen if c == "R"), "right column ends at slot 30"
    assert all(1 <= s <= 40 for c, s in seen), "slot out of range"
    nets = [e[4] for e in PLAN if e[4] not in ("GND", "POT_REF")]
    want = ([f"CV{i}" for i in range(1, 7)] + ["CVI7", "CVI8", "CVO7", "CVO8", "AIN1", "AIN2", "AOUT1", "AOUT2"]
            + [f"POT{i}" for i in range(1, 9)] + [f"GIN{i}" for i in range(1, 5)] + [f"GOUT{i}" for i in range(1, 9)]
            + [f"SW{i}" for i in range(1, 10)] + [f"PR{i}" for i in range(1, 15)])
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

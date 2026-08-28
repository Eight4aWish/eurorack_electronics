#!/usr/bin/env python3
"""
gen_board_profiles.py — Parse official n8synth .n8layout templates and emit
board-profile JSON files that the visualizer and validators can read, so board
geometry is data instead of hardcoded constants.

What a profile captures:
  - breadboard anatomy: main area / edge connector / power rail (three different
    extents). Ground truth is docs/n8synth_platform.md — that document wins over
    anything inferred from the templates.
  - the control deck: JPS cell inventory and, critically, the CONNECTOR MAP —
    which breadboard outer-strip hole (ctrl row) lands on which JPS pad.
  - gap rows: connector pins with no JPS pad. The deck hole is otherwise
    unconnected, which makes these usable as free feed-through tie points
    (e.g. solder a wire across the deck between two gap holes to jump a long
    distance without cluttering the breadboard).
  - the D ground bus: every JPS cell has one D pad, all D pads are bussed
    across the whole deck. Ground recipe: panel component leg -> its JPS
    A/B/C pad; use the cell's second A/B/C solder point to bridge to D; and
    the D bus must reach breadboard GND through at least one outer-strip
    hole jumpered to a GND point (validator rule, not enforced here).

Connector facts (confirmed by the builder, 2026-07):
  - 4HP and 6HP decks have a SINGLE 40-pin strip -> one ctrl column, on the
    LEFT edge of the breadboard (beside the +12V/GND rail).
  - 10HP has two 40-pin strips: pins 0-39 = ctrlL, pins 40-79 = ctrlR
    (verified 18/18 against the dual LPG layout rev 0.15/0.16 positions).
  - Breadboards can be stacked via stack connectors on ANY deck size (the
    10HPS template simply ships with a second board pre-placed). The deck
    mounts right way up; stacked boards are usually mounted FLIPPED (left
    strips become right strips) so components stay visible for probing.
    Per-layer net pass-through still to be confirmed.

Usage:
    python3 gen_board_profiles.py            # writes boards/*.json
"""
import json
import os
import re
import sys
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(HERE, '..', 'n8layout')
OUT_DIR = os.path.join(HERE, 'boards')

TEMPLATES = {
    'n8synth-4hp':  '4HP Template.n8layout',
    'n8synth-6hp':  '6HP_Template.n8layout',
    'n8synth-10hp': '10HP Template.n8layout',
    'n8synth-10hps': '10HPS Template.n8layout',
}

HP_OF = {'n8synth-4hp': 4, 'n8synth-6hp': 6, 'n8synth-10hp': 10, 'n8synth-10hps': 10}


def parse_pin_sequences(text):
    """Extract connector pin -> label sequences from controldeck-side groups.

    Returns {pin_index: label} deduped across front/rear views (the views
    repeat the same sequences). Pin indices are continuous: 0-39 = first
    40-pin strip, 40-79 = second strip (10HP only).
    """
    pins = {}
    for g in re.finditer(
            r'<g id="(controldeck-side[^"]*)" class="(pin-label-cont[^"]*)"[^>]*>(.*?)</g>',
            text, re.S):
        body = g.group(3)
        for m in re.finditer(r'<text[^>]*name="(\d+)"[^>]*>([^<]*)</text>', body):
            idx, label = int(m.group(1)), m.group(2).strip()
            label = re.sub(r'^JSP(\d)', r'JPS\1', label)  # vendor typo: "JSP4 A" in 4HP template
            if idx in pins and pins[idx] != label:
                print(f'  WARNING: pin {idx} label conflict: {pins[idx]!r} vs {label!r}')
            pins[idx] = label
    return pins


def parse_deck_symbol(text):
    """Find the deck symbol name, e.g. n8-cd-6hp-2x6 -> (name, cols, rows)."""
    m = re.search(r'href="#(n8-cd-(\d+)hp-(\d+)x(\d+))-front"', text)
    if not m:
        return None, None, None
    return m.group(1), int(m.group(3)), int(m.group(4))


def build_ctrl_map(pins, strip_offset):
    """Map ctrl row (1-40) -> {cell, pad} or None (gap) for one 40-pin strip."""
    ctrl = OrderedDict()
    for row in range(1, 41):
        label = pins.get(strip_offset + row - 1, '-')
        if label == '-' or not label:
            ctrl[str(row)] = None
        else:
            cell, pad = label.rsplit(' ', 1)
            ctrl[str(row)] = {'cell': cell, 'pad': pad}
    return ctrl


def cells_in(ctrl_maps):
    """Collect the JPS cell inventory from the connector maps."""
    cells = {}
    for strip, cmap in ctrl_maps.items():
        for row, entry in cmap.items():
            if entry:
                c = cells.setdefault(entry['cell'], {'pads': {}, 'strip': strip})
                c['pads'][entry['pad']] = int(row)
    # order JPS1, JPS2, ... numerically
    ordered = OrderedDict()
    for name in sorted(cells, key=lambda n: int(re.sub(r'\D', '', n))):
        c = cells[name]
        ordered[name] = {
            'strip': c['strip'],
            'ctrlRows': {pad: c['pads'][pad] for pad in sorted(c['pads'])},
        }
    return ordered


def make_profile(board_id, template_path):
    text = open(template_path).read()
    deck_symbol, deck_cols, deck_rows = parse_deck_symbol(text)
    pins = parse_pin_sequences(text)
    n_strips = 2 if max(pins) >= 40 else 1
    n_breadboards = len(re.findall(r'data-n8model="eurorack-breadboard"', text))

    if n_strips == 2:
        ctrl_maps = OrderedDict([('ctrlL', build_ctrl_map(pins, 0)),
                                 ('ctrlR', build_ctrl_map(pins, 40))])
    else:
        # Single 40-pin strip (4HP / 6HP) — one ctrl column on the LEFT edge
        # of the breadboard, beside the +12V/GND rail (builder-confirmed).
        ctrl_maps = OrderedDict([('ctrlL', build_ctrl_map(pins, 0))])

    profile = OrderedDict()
    profile['id'] = board_id
    profile['hp'] = HP_OF[board_id]
    profile['source'] = os.path.basename(template_path)
    # Board anatomy per docs/n8synth_platform.md (builder-verified 2026-08-28).
    # The main area, the edge connector and the power rail are three DIFFERENT
    # things with different extents — do not collapse them into one 'rows' count.
    row_ids = sorted({int(m) for m in re.findall(r'data-zone="row-(\d+)"', text)})
    has_power_section = 'data-zone="power"' in text
    max_row = max(row_ids) if row_ids else 0

    if n_breadboards == 2:
        # 10HPS ships a powered board (main area 1-36) plus a plain stacked
        # board (main area 1-40); its template holds 36 + 40 = 76 row zones.
        boards = [{'variant': 'powered', 'mainAreaRows': [1, 36]},
                  {'variant': 'plain', 'mainAreaRows': [1, 40]}]
    else:
        boards = [{'variant': 'powered' if has_power_section else 'plain',
                   'mainAreaRows': [1, max_row]}]

    profile['breadboard'] = {
        'count': n_breadboards,
        'boards': boards,
        'mainArea': {
            'holeCols': ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j'],
            'centreGap': ['e', 'f'],
            'note': 'Five holes each side of the gap are joined. The LEFT and RIGHT '
                    'halves of a row are NOT joined to each other. Powered boards '
                    'have 36 main-area rows; plain boards have 40.',
        },
        'edgeConnector': {
            'positions': 40,
            'holesPerPosition': 2,
            'note': 'Two adjacent columns; the two holes at a position are joined to '
                    'each other and to nothing else. JPS cell pads A/B/C terminate '
                    'HERE, not on main-area rows — a panel signal reaches the circuit '
                    'by a wire from its doublet into the main area. Positions 37-40 '
                    'are therefore usable even on a powered board, which has no '
                    'main-area row there. Positions not claimed by a JPS cell are '
                    'free tie points and can be repurposed for routing.',
        },
        'powerRail': {
            'positions': 40,
            'pwrL': {'oddPositions': 'GND', 'evenPositions': 'VCC'},
            'pwrR': {'oddPositions': 'GND', 'evenPositions': 'VEE'},
            'reserved': ({'37': '10uF+ electrolytic', '38': '10uF+ electrolytic'}
                         if has_power_section else {}),
            'note': 'Numbering top to bottom, position 1 is GND and 2 is the supply '
                    '(+12V on the left column, -12V on the right). On powered boards '
                    'the 100nF caps consume no positions; the 10uF+ electrolytics sit '
                    'on positions 37-38. Positions 1, 2, 39, 40 exist to jump power '
                    'between stacked boards and are FREE on a single-board module — '
                    '39 (GND) is handy for grounding near the bottom.',
        },
    }
    profile['deck'] = {
        'symbol': deck_symbol,
        'grid': {'cols': deck_cols, 'rows': deck_rows},
        'strips': n_strips,
        'groundBus': {
            'pad': 'D',
            'scope': 'whole deck',
            'note': 'One D pad per cell, bussed deck-wide. Bridge a cell\'s spare '
                    'A/B/C solder point to D for local grounds; the bus must reach '
                    'breadboard GND via at least one outer-strip hole.',
        },
        'padsPerCell': {'A': 2, 'B': 2, 'C': 2, 'D': 1},
        'cells': cells_in(ctrl_maps),
    }
    profile['ctrlMap'] = ctrl_maps
    profile['gapRows'] = {
        strip: [int(r) for r, e in cmap.items() if e is None]
        for strip, cmap in ctrl_maps.items()
    }
    profile['gapRowNote'] = ('Gap rows have no JPS pad; the deck hole is otherwise '
                             'unconnected, so they are free feed-through tie points '
                             '(useful for long jumps routed across the deck).')
    # Stacking is available on every deck size — the 10HPS template just ships
    # with a second board pre-placed (breadboard.count reflects the template).
    profile['stacking'] = {
        'supported': True,
        'note': 'Extra breadboards stack via connectors on any deck size. Deck '
                'mounts right way up; stacked boards are typically mounted FLIPPED '
                '(left/right strips swap) so components face outward for probing. '
                'Per-layer net pass-through to be confirmed before multi-board '
                'layouts.',
        'passThroughConfirmed': False,
    }
    return profile


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    for board_id, fname in TEMPLATES.items():
        path = os.path.join(TEMPLATE_DIR, fname)
        if not os.path.exists(path):
            print(f'SKIP {board_id}: {fname} not found')
            continue
        print(f'{board_id}  <-  {fname}')
        profile = make_profile(board_id, path)
        out = os.path.join(OUT_DIR, f'{board_id}.json')
        with open(out, 'w') as f:
            json.dump(profile, f, indent=2)
        n_cells = len(profile['deck']['cells'])
        strips = ', '.join(profile['ctrlMap'])
        gaps = sum(len(v) for v in profile['gapRows'].values())
        print(f'  -> {os.path.relpath(out, HERE)}: {n_cells} JPS cells, '
              f'strips [{strips}], {gaps} gap rows')


if __name__ == '__main__':
    main()

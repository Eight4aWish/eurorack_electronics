#!/usr/bin/env python3
"""
n8synth layout validator. Checks a visualizer JSON for:
  1. Hole collisions — multiple pins assigned to one (row, col)
  1b. Net labels vs the IC pin on the same node
  1c. Same net named on both row halves with nothing bridging the gap
  1d. A wire scheduled later than both ends it joins
  1e. A component reaching across the board for a rail
  1f. Anything on an outer hole a control-deck header occupies
  2. Net-distinctness — every twoPin component must bridge two distinct (row, side) nets
  3. Power-rail parity — pwrL/pwrR endpoints match the alternating-parity rule
     (pwrL: odd=GND/even=+12V; pwrR: odd=GND/even=-12V)

Usage:
    python3 validate_layout.py path/to/layout.json
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
import sys
from collections import defaultdict


def side(c):
    """Normalise a column to its electrical LANE.

    Edge-connector doublets (ctrlLo/ctrlLi, ctrlRo/ctrlRi) are two holes on ONE
    node, so both resolve to the same lane. Collision checks must still key on
    the raw column, since the two holes are physically distinct.
    See docs/n8synth_platform.md.
    """
    if c is None:
        return None
    if c in 'abcde':
        return 'L'
    if c in 'fghij':
        return 'R'
    if c in ('ctrlLo', 'ctrlLi'):
        return 'ctrlL'
    if c in ('ctrlRo', 'ctrlRi'):
        return 'ctrlR'
    return c   # pwrL / pwrR / ctrlL / ctrlR


def validate(path):
    with open(path) as f:
        layout = json.load(f)

    errs = []

    # --- 1. Hole collisions ---
    # Each (row, col) pair is one physical hole on the breadboard. Power-rail
    # holes (col pwrL / pwrR) are one hole per row too — the rails on the
    # n8synth have one hole per row aligned with the main grid. Two leads
    # cannot share a single hole, even on a power rail.
    holes = defaultdict(list)

    def occupy(r, c, who):
        if r is None or c is None:
            return
        holes[(r, c)].append(who)

    for ic in layout.get('ics', []):
        for pin in ic.get('pins', []):
            occupy(pin['r'], pin['c'], f"{ic['id']}.{pin['n']}")
    for comp in layout.get('twoPins', []):
        occupy(comp.get('r1'), comp.get('c1'), f"{comp['id']}.1")
        occupy(comp.get('r2'), comp.get('c2'), f"{comp['id']}.2")
    for group in ('jumpers', 'jpsWires', 'powerWires'):
        for jw in layout.get(group, []):
            name = jw.get('id', jw.get('label', '?'))
            occupy(jw.get('r1'), jw.get('c1'), f"{group}[{name}].1")
            occupy(jw.get('r2'), jw.get('c2'), f"{group}[{name}].2")

    for (r, c), occupants in holes.items():
        if len(occupants) > 1:
            errs.append(f"  HOLE COLLISION row {r}{side(c)} col {c}: {' + '.join(occupants)}")

    # --- 2. Net-distinctness ---
    for comp in layout.get('twoPins', []):
        n1 = (comp['r1'], side(comp['c1']))
        n2 = (comp['r2'], side(comp['c2']))
        if n1 == n2:
            errs.append(f"  NET-DISTINCTNESS: {comp['id']} bridges same net {n1}")

    # --- 3. Power-rail parity (warning, not error) ---
    warnings = []
    for comp in layout.get('twoPins', []) + layout.get('jumpers', []) + layout.get('powerWires', []):
        for end in ('1', '2'):
            r = comp.get(f'r{end}')
            c = comp.get(f'c{end}')
            if c == 'pwrL':
                expected = 'GND' if r % 2 == 1 else '+12V'
                lbl = comp.get('id', comp.get('label', '?'))
                # caller is expected to verify intent matches expected
                warnings.append(f"  pwrL at row {r}: {expected} (component '{lbl}' lands here)")
            elif c == 'pwrR':
                expected = 'GND' if r % 2 == 1 else '-12V'
                lbl = comp.get('id', comp.get('label', '?'))
                warnings.append(f"  pwrR at row {r}: {expected} (component '{lbl}' lands here)")

    # --- Report ---
    print(f"Validating {path}")
    print(f"  Components: {len(layout.get('twoPins', []))} twoPins, "
          f"{len(layout.get('ics', []))} ICs, "
          f"{len(layout.get('jumpers', []))} jumpers, "
          f"{len(layout.get('powerWires', []))} powerWires, "
          f"{len(layout.get('jpsWires', []))} jpsWires")
    # --- Net labels vs the IC pin on the same node ----------------------
    # A row half is ONE node, so a net label must agree with any IC pin net
    # sitting on it. Catches a label transcribed onto the wrong row — which
    # cross_check_nets cannot see, since it validates component endpoints
    # against EXPECTED_NETS and never looks at netLabels.
    pin_net = {}
    for ic in layout.get('ics', []):
        for pin in ic.get('pins', []):
            if pin.get('net'):
                pin_net.setdefault((pin['r'], side(pin['c'])), set()).add(pin['net'])
    for nl in layout.get('netLabels', []):
        key = (nl['r'], nl['side'])
        if key in pin_net and nl['name'] not in pin_net[key]:
            errs.append(f"net label row {nl['r']} {nl['side']}: says '{nl['name']}' but the "
                        f"IC pin on that node is '{', '.join(sorted(pin_net[key]))}'")

    # --- Same net named on both halves of a row, with nothing bridging ---------
    # The left and right halves of a row are separate nodes. If both are labelled
    # with the SAME net, something must cross the centre gap or they are two
    # isolated nodes pretending to be one — an open circuit that reads as wired.
    def spans_gap(r):
        for grp in ('twoPins', 'jumpers'):
            for t in layout.get(grp, []):
                if t.get('r1') == r or t.get('r2') == r:
                    if {side(t.get('c1')), side(t.get('c2'))} == {'L', 'R'}:
                        return True
        for ic in layout.get('ics', []):
            if {side(p['c']) for p in ic.get('pins', []) if p['r'] == r} == {'L', 'R'}:
                return True
        return False

    by_row = {}
    for nl in layout.get('netLabels', []):
        by_row.setdefault(nl['r'], {})[nl['side']] = nl['name']
    for ic in layout.get('ics', []):
        for pin in ic.get('pins', []):
            if pin.get('net'):
                by_row.setdefault(pin['r'], {}).setdefault(side(pin['c']), pin['net'])
    for r, halves in sorted(by_row.items()):
        if halves.get('L') and halves.get('L') == halves.get('R') and not spans_gap(r):
            errs.append(f"row {r}: net '{halves['L']}' is named on BOTH halves but nothing "
                        f"bridges the centre gap — those are two isolated nodes")

    # --- A wire scheduled later than both ends it joins -----------------------
    # If both nodes a wire connects already exist at stage N but the wire is stage
    # N+1, phase N shows two live ends with nothing between them: the phase reads
    # as complete and its test cannot pass.
    def lane(c):
        c = str(c)
        if c.startswith('ctrlL'):
            return 'ctrlL'
        if c.startswith('ctrlR'):
            return 'ctrlR'
        return side(c)

    first_stage = {}

    def note(r, c, st):
        k = (r, lane(c))
        first_stage[k] = min(first_stage.get(k, 99), st)

    for comp in layout.get('twoPins', []):
        for e in (1, 2):
            note(comp[f'r{e}'], comp[f'c{e}'], comp.get('stage', 1))
    for ic in layout.get('ics', []):
        for pin in ic.get('pins', []):
            note(pin['r'], pin['c'], ic.get('stage', 1))
    for w in layout.get('jpsWires', []):
        note(w['row'], w['col'], w.get('stage', 1))

    for grp in ('jumpers', 'powerWires'):
        for w in layout.get(grp, []):
            a = first_stage.get((w.get('r1'), lane(w.get('c1'))), 99)
            b = first_stage.get((w.get('r2'), lane(w.get('c2'))), 99)
            both = max(a, b)
            if both < 99 and w.get('stage', 1) > both:
                errs.append(f"{grp} {w.get('id', w.get('label', '?'))}: stage "
                            f"{w.get('stage')} but both ends exist by stage {both} — "
                            f"that phase shows two live ends with no link")

    # --- A component reaching across the board for a rail ---------------------
    # Both rails carry GND, so a right-half part grounding on pwrL passes every net
    # check while being a needlessly long wire. VCC is the exception: it exists only
    # on pwrL even rows, so a right-half part needing it has no choice.
    def body_half(c):
        c = str(c)
        if c in 'abcde' or c.startswith('ctrlL'):
            return 'L'
        if c in 'fghij' or c.startswith('ctrlR'):
            return 'R'
        return None

    for comp in layout.get('twoPins', []):
        for e in (1, 2):
            rail, other = str(comp[f'c{e}']), body_half(comp[f'c{3 - e}'])
            if rail not in ('pwrL', 'pwrR') or other not in ('L', 'R'):
                continue
            row = comp[f'r{e}']
            if rail == 'pwrL' and other == 'R' and row % 2 == 0:
                continue          # VCC only exists on pwrL — unavoidable
            if (rail == 'pwrL' and other == 'R') or (rail == 'pwrR' and other == 'L'):
                errs.append(f"{comp['id']}: body on the {other} half at "
                            f"{comp['c' + str(3 - e)]}{comp['r' + str(3 - e)]} but reaches "
                            f"{rail}{row} on the far side — use the near rail")

    # --- Anything on a hole a control-deck header occupies ---------------------
    # Read from the board profile, so the header positions are stated once.
    spans = None
    bid = layout.get('boardId')
    if bid:
        try:
            prof = json.load(open(os.path.join(HERE, 'boards', bid + '.json')))
            spans = prof['breadboard']['edgeConnector'].get('headerSpans')
            pads = {int(r) for r, v in
                    list(prof['ctrlMap'].values())[0].items() if v}
        except Exception:
            spans = None
    if spans:
        blocked = {r for lo, hi in spans for r in range(lo, hi + 1) if r not in pads}
        for grp in ('twoPins', 'jumpers', 'powerWires'):
            for item in layout.get(grp, []):
                for e in (1, 2):
                    col, row = str(item.get(f'c{e}')), item.get(f'r{e}')
                    if col.endswith('o') and row in blocked:
                        errs.append(f"{grp} {item.get('id', '?')}: {col}{row} is an OUTER hole "
                                    f"a header pin occupies — only the inner hole is free there")

    if errs:
        print(f"\n✗ {len(errs)} error(s):")
        for e in errs:
            print(e)
        sys.exit(1)
    else:
        print("\n✓ Zero hole collisions, all twoPin components bridge distinct nets.")
        if warnings:
            print(f"\n  ({len(warnings)} power-rail endpoints to manually verify intent matches polarity — use --show-rails to print)")
        if '--show-rails' in sys.argv:
            print("\nPower-rail endpoint summary:")
            for w in warnings:
                print(w)
        sys.exit(0)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    validate(sys.argv[1])

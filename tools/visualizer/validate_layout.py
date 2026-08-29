#!/usr/bin/env python3
"""
n8synth layout validator. Checks a visualizer JSON for:
  1. Hole collisions — multiple pins assigned to one (row, col)
  2. Net-distinctness — every twoPin component must bridge two distinct (row, side) nets
  3. Power-rail parity — pwrL/pwrR endpoints match the alternating-parity rule
     (pwrL: odd=GND/even=+12V; pwrR: odd=GND/even=-12V)

Usage:
    python3 validate_layout.py path/to/layout.json
"""
import json
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

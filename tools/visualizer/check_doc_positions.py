#!/usr/bin/env python3
"""
check_doc_positions.py — verify every control position a doc names by hand
actually exists in the layout.

The off-board interconnect tables are hand-written prose, and rightly so: they
carry pot leg conventions, LED polarity and jack wiring that no JSON records.
But they also name control positions, which makes them a second source for a
fact the layout already holds. This makes the two agree, or fails.

Positions inside the GEN:MAPS block are skipped — those are generated.

Usage:
    python3 check_doc_positions.py layouts/lpg.json ../../docs/lpg_breadboard_placement.md
"""
import json, re, sys


def main(layout_path, doc_path):
    layout = json.load(open(layout_path))
    doc = open(doc_path, encoding='utf-8').read()

    # positions the layout actually provides, by lane
    have = {}
    for w in layout.get('jpsWires', []):
        lane = 'ctrlL' if str(w.get('col', '')).startswith('ctrlL') else 'ctrlR'
        have.setdefault((lane, w['row']), []).append(w.get('label') or w.get('id'))

    # skip the generated block — that is not hand-written
    s, e = doc.find('<!-- GEN:MAPS:START'), doc.find('<!-- GEN:MAPS:END')
    hand = doc if s < 0 else doc[:s] + doc[e:]

    missing, checked = [], 0
    for m in re.finditer(r'ctrl([LR])\s*(\d+)', hand):
        key = ('ctrl' + m.group(1), int(m.group(2)))
        checked += 1
        if key not in have:
            line = hand[:m.start()].split('\n')[-1].strip()[-72:]
            missing.append(f"{key[0]} {key[1]} — not a control position in the layout\n"
                           f"        ...{line}")

    print(f"=== DOC POSITION CROSS-CHECK — {doc_path} ===\n")
    print(f"  {checked} hand-written control position(s) named")
    if missing:
        print(f"\n✗ {len(missing)} do not exist in the layout:")
        for x in missing:
            print("    " + x)
        return 1
    print("  ✓ every one exists in the layout")
    return 0


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1], sys.argv[2]))

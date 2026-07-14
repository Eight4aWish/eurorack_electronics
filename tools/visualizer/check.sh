#!/usr/bin/env bash
# check.sh — run every layout check in one go:
#   1. validate_layout.py    geometry: hole collisions, net-distinctness, rail parity
#   2. cross_check_nets.py   net identity: does each component land on the nets
#                            the netlist requires?
#   3. gen_rowmap.py         regenerate the placement doc's row maps from the JSON
#                            (only when 1+2 pass, so the doc never records a bad rev)
#
# Usage:
#   tools/visualizer/check.sh                              # checks the LPG
#   tools/visualizer/check.sh layouts/foo.json docs/foo_placement.md
cd "$(dirname "$0")"

LAYOUT="${1:-layouts/lpg.json}"
DOC="${2:-../../docs/lpg_breadboard_placement.md}"
FAIL=0

echo "════ 1/3 geometry (validate_layout) ════"
python3 validate_layout.py "$LAYOUT" || FAIL=1

echo
echo "════ 2/3 net identity (cross_check_nets) ════"
python3 cross_check_nets.py "$LAYOUT" || FAIL=1

if [ "$FAIL" -eq 0 ]; then
    echo
    echo "════ 3/3 doc maps (gen_rowmap) ════"
    python3 gen_rowmap.py "$LAYOUT" "$DOC" || FAIL=1
fi

echo
if [ "$FAIL" -eq 0 ]; then
    echo "✓✓✓ ALL CHECKS PASSED — $LAYOUT"
else
    echo "✗✗✗ CHECKS FAILED — $LAYOUT (doc maps not regenerated)"
fi
exit "$FAIL"

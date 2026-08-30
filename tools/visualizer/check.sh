#!/usr/bin/env bash
# check.sh — run every layout check in one go:
#   1. validate_layout.py    geometry: hole collisions, net-distinctness, rail parity
#   2. cross_check_nets.py   net identity: does each component land on the nets
#                            the netlist requires?
#   3. sync_layout.py        regenerate the .js wrapper the browser actually loads
#                            (the JSON is canonical; the wrapper is generated)
#   4. gen_rowmap.py         regenerate the placement doc's row maps from the JSON
#   5. check_doc_positions   every control position the doc names by hand must
#                            exist in the layout (the off-board tables are prose,
#                            but they still name positions)
#
# Usage:
#   tools/visualizer/check.sh                              # checks the LPG
#   tools/visualizer/check.sh layouts/foo.json docs/foo_placement.md
cd "$(dirname "$0")"

LAYOUT="${1:-layouts/lpg.json}"
DOC="${2:-../../docs/lpg_breadboard_placement.md}"
FAIL=0

echo "════ 1/5 geometry (validate_layout) ════"
python3 validate_layout.py "$LAYOUT" || FAIL=1

echo
echo "════ 2/5 net identity (cross_check_nets) ════"
python3 cross_check_nets.py "$LAYOUT" || FAIL=1

if [ "$FAIL" -eq 0 ]; then
    echo
    echo "════ 3/5 browser wrapper (sync_layout) ════"
    python3 sync_layout.py "$LAYOUT" || FAIL=1
fi

if [ "$FAIL" -eq 0 ]; then
    echo
    echo "════ 4/5 doc maps (gen_rowmap) ════"
    python3 gen_rowmap.py "$LAYOUT" "$DOC" || FAIL=1
fi

if [ "$FAIL" -eq 0 ]; then
    echo
    echo "════ 5/5 doc positions (check_doc_positions) ════"
    python3 check_doc_positions.py "$LAYOUT" "$DOC" || FAIL=1
fi

echo
if [ "$FAIL" -eq 0 ]; then
    echo "✓✓✓ ALL CHECKS PASSED — $LAYOUT"
else
    echo "✗✗✗ CHECKS FAILED — $LAYOUT (doc maps not regenerated)"
fi
exit "$FAIL"

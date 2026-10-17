"""For each saved DRC report: every unconnected item's net kind (rail, ground, signal) and the
chip nearest to it, then totals across all reports."""
import collections
import json
import math
import sys

import pcbnew

pairs = [a.split("=") for a in sys.argv[1:]]          # report.json=board.kicad_pcb
by_chip, by_kind = collections.Counter(), collections.Counter()
for rpt, brd in pairs:
    b = pcbnew.LoadBoard(brd)
    chips = [(f.GetReference(), f.GetValue(), f.GetPosition().x / 1e6, f.GetPosition().y / 1e6)
             for f in b.GetFootprints() if f.GetReference().startswith("U")]
    d = json.load(open(rpt))
    here = collections.Counter()
    for u in d["unconnected_items"]:
        it = u["items"][0]
        net = it["description"].split("[")[1].split("]")[0] if "[" in it["description"] else "?"
        kind = "ground" if net == "GND" else "rail" if net.startswith(("+", "-")) or net == "MOD_5V" else "signal"
        x, y = it["pos"]["x"], it["pos"]["y"]
        ref, val, _, _ = min(chips, key=lambda c: math.dist((c[2], c[3]), (x, y)))
        here[f"{ref} {val}"] += 1
        by_chip[f"{ref} {val}"] += 1
        by_kind[kind] += 1
    print(rpt.split("/")[-1], len(d["unconnected_items"]), "left; nearest chips:", here.most_common(4))
print("\nAll reports, by kind:", dict(by_kind))
print("All reports, nearest chip:", by_chip.most_common(10))

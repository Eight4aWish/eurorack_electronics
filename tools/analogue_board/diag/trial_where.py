"""Where the unrouted signal connections are: midpoints on a coarse grid (board coordinates).

    python3 -I trial_where.py drc.json
"""
import collections
import json
import re
import sys

BX, BY = 30.0, 30.0
SKIP = {"GND", "+3V3D", "+3V3A", "+5VD", "+5VA", "+12V", "-12V", "MOD_5V", "CODEC_VDD"}
d = json.load(open(sys.argv[1]))
grid = collections.Counter()
span = []
for u in d["unconnected_items"]:
    m = re.search(r"\[([^\]]+)\]", u["items"][0]["description"])
    net = (m.group(1) if m else "?").split("/")[-1]
    if net in SKIP:
        continue
    (a, b) = [(i["pos"]["x"] - BX, i["pos"]["y"] - BY) for i in u["items"][:2]]
    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    grid[(int(mx // 12.4), int(my // 10.3))] += 1
    span.append(abs(a[0] - b[0]) + abs(a[1] - b[1]))
print("Unrouted signal connections by region (columns 12.4 mm wide, rows 10.3 mm tall):")
print("        " + "".join(f"x{c * 12.4:5.1f}  " for c in range(4)))
for r in range(10):
    print(f"y{r * 10.3:5.1f}  " + "".join(f"{grid[(c, r)]:6d}  " for c in range(4)))
span.sort()
print(f"\nGap lengths: median {span[len(span) // 2]:.1f} mm, 90th percentile {span[int(len(span) * 0.9)]:.1f} mm")

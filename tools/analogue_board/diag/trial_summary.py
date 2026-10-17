"""Summarise kicad-cli DRC JSON for the trial autoroute: violations by type, unconnected by net.

    python3 -I trial_summary.py drc.json
"""
import collections
import json
import re
import sys

RAILS = {"+3V3D", "+3V3A", "+5VD", "+5VA", "+12V", "-12V", "MOD_5V"}

d = json.load(open(sys.argv[1]))
v = collections.Counter(x["type"] for x in d["violations"])
print("Violations by type:")
for t, n in v.most_common():
    print(f"  {n:4d}  {t}")

nets = collections.Counter()
where = collections.defaultdict(list)
for u in d["unconnected_items"]:
    items = u["items"]
    m = re.search(r"\[([^\]]+)\]", items[0]["description"])
    net = m.group(1) if m else "?"
    nets[net] += 1
    where[net].append(" -> ".join(i["description"].split(" [")[0] + f" ({i['pos']['x']:.1f},{i['pos']['y']:.1f})" for i in items))


def kind(n):
    short = n.split("/")[-1]
    if short == "GND":
        return "ground"
    if short in RAILS or n.split("/")[-1].startswith(("3V3A", "CODEC_VDD")):
        return "rails"
    return "signals"


groups = collections.defaultdict(list)
for n, c in nets.items():
    groups[kind(n)].append((c, n))
if "--totals" in sys.argv:
    print(sys.argv[1].split("/")[-1], "  ".join(f"{k} {sum(c for c, _ in groups[k])}" for k in ("signals", "rails", "ground")))
    sys.exit(0)
print(f"\nUnconnected: {sum(nets.values())}")
for k in ("ground", "rails", "signals"):
    lst = sorted(groups[k], reverse=True)
    print(f"  {k}: {sum(c for c, _ in lst)} on {len(lst)} nets")
    for c, n in lst[:60]:
        print(f"    {c:3d}  {n}")
if len(sys.argv) > 2:
    for line in where[sys.argv[2]]:
        print("   ", line)

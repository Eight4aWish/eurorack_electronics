"""Print a DRC report's unconnected items and its copper faults (anything not silk or library)."""
import json
import sys

d = json.load(open(sys.argv[1]))
skip = {"silk_overlap", "silk_over_copper", "lib_footprint_issues", "lib_footprint_mismatch", "silk_edge_clearance"}
print("Unconnected:")
for u in d.get("unconnected_items", []):
    items = u["items"]
    print("  " + "  <->  ".join(f"{i['description']} @({i['pos']['x']:.2f},{i['pos']['y']:.2f})" for i in items))
print("Faults:")
for v in d.get("violations", []):
    if v["type"] in skip:
        continue
    print(f"  {v['type']}: " + " | ".join(f"{i['description']} @({i['pos']['x']:.2f},{i['pos']['y']:.2f})" for i in v["items"]))

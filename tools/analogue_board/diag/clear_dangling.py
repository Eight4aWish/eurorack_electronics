"""Delete exactly the tracks and vias KiCad's DRC calls dangling, re-running DRC until there are
none, and stop at once if the unconnected count rises above where it started."""
import json
import os
import subprocess
import sys

import pcbnew

CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
path = sys.argv[1]
rpt = path + ".drc.json"


def drc():
    subprocess.run([CLI, "pcb", "drc", "--format", "json", "--severity-all", "-o", rpt, path], capture_output=True)
    with open(rpt) as f:
        d = json.load(f)
    os.remove(rpt)
    return d


d = drc()
start = len(d["unconnected_items"])
for i in range(15):
    ids = {it["uuid"] for v in d["violations"] if v["type"] in ("track_dangling", "via_dangling") for it in v["items"]}
    if not ids:
        break
    b = pcbnew.LoadBoard(path)
    gone = [t for t in b.GetTracks() if t.m_Uuid.AsString() in ids]
    for t in gone:
        b.Delete(t)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(path, b)
    d = drc()
    print(f"pass {i + 1}: deleted {len(gone)}; unconnected now {len(d['unconnected_items'])}", flush=True)
    if len(d["unconnected_items"]) > start:
        sys.exit("unconnected count rose: stopping")
left = [v["type"] for v in d["violations"] if v["type"] in ("track_dangling", "via_dangling")]
print(f"dangling left: {len(left)}; unconnected: {len(d['unconnected_items'])}")

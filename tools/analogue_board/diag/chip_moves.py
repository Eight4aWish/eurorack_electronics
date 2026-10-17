"""For each chip, the signal pins it connects to (other parts' pads on its non-ground, non-rail
nets), and for each candidate spot: total straight-line length to them and header rows crossed."""
import math
import sys

import pcbnew

b = pcbnew.LoadBoard(sys.argv[1])
OX = OY = 30.0
fps = {f.GetReference(): f for f in b.GetFootprints()}
rows = []
for f in fps.values():
    if str(f.GetFPID().GetLibItemName()).startswith(("Pico2", "Teensy41")):
        cols = {}
        for p in f.Pads():
            cols.setdefault(round(p.GetPosition().x / 1e6 - OX, 1), []).append(p.GetPosition().y / 1e6 - OY)
        rows += [(x, min(ys), max(ys)) for x, ys in cols.items() if len(ys) > 4]


def crossings(a, c):
    k = 0
    for rx, top, bot in rows:
        if (a[0] - rx) * (c[0] - rx) < 0:
            yc = a[1] + (c[1] - a[1]) * (rx - a[0]) / (c[0] - a[0])
            if top - 1.27 <= yc <= bot + 1.27:
                k += 1
    return k


spots = {name: tuple(map(float, xy.split(","))) for name, xy in (s.split("=") for s in sys.argv[3:])}
for ref in sys.argv[2].split(","):
    f = fps[ref]
    here = (f.GetPosition().x / 1e6 - OX, f.GetPosition().y / 1e6 - OY)
    bb = f.GetBoundingBox()
    here = ((bb.GetLeft() + bb.GetRight()) / 2e6 - OX, (bb.GetTop() + bb.GetBottom()) / 2e6 - OY)
    targets = []
    for p in f.Pads():
        n = p.GetNetname()
        if not n or n == "GND" or n.startswith(("+", "-")):
            continue
        others = [(q.GetPosition().x / 1e6 - OX, q.GetPosition().y / 1e6 - OY) for g in fps.values() if g is not f
                  for q in g.Pads() if q.GetNetname() == n]
        if others:
            targets.append(others)
    out = []
    for name, c in [("now", here)] + list(spots.items()):
        length = sum(min(math.dist(c, o) for o in os_) for os_ in targets)
        cross = sum(min(crossings(c, o) for o in os_) for os_ in targets)
        out.append(f"{name} {length:.0f} mm/{cross} rows")
    print(f"{ref:6s} ({len(targets)} nets): " + "; ".join(out))

"""Module header rows crossed by each signal net's shortest pad-to-pad tree (Prim), per board."""
import math
import sys

import pcbnew

for path in sys.argv[1:]:
    b = pcbnew.LoadBoard(path)
    rows, nets = [], {}
    for fp in b.GetFootprints():
        name = str(fp.GetFPID().GetLibItemName())
        pads = [(p.GetPosition().x / 1e6, p.GetPosition().y / 1e6) for p in fp.Pads()]
        if name.startswith(("Pico2", "Teensy41")):
            cols = {}
            for x, y in pads:
                cols.setdefault(round(x, 1), []).append(y)
            rows += [(x, min(ys), max(ys)) for x, ys in cols.items() if len(ys) > 4]
        for p in fp.Pads():
            n = p.GetNetname()
            if n and n != "GND" and not n.startswith(("+", "-")):
                nets.setdefault(n, []).append((p.GetPosition().x / 1e6, p.GetPosition().y / 1e6))

    def cross(a, b):
        k = 0
        for rx, top, bot in rows:
            if (a[0] - rx) * (b[0] - rx) < 0:
                yc = a[1] + (b[1] - a[1]) * (rx - a[0]) / (b[0] - a[0])
                if top - 1.27 <= yc <= bot + 1.27:
                    k += 1
        return k
    total, worst = 0, []
    for n, pts in nets.items():
        if len(pts) < 2 or len(pts) > 12:
            continue
        done, edges = {0}, []
        while len(done) < len(pts):
            d, i, j = min((math.dist(pts[i], pts[j]), i, j) for i in done for j in range(len(pts)) if j not in done)
            done.add(j)
            edges.append((pts[i], pts[j]))
        c = sum(cross(a, b) for a, b in edges)
        total += c
        if c:
            worst.append((c, n))
    worst.sort(reverse=True)
    print(f"{path.split('/')[-1]}: {total} row crossings over {len(worst)} nets; most: {worst[:6]}")

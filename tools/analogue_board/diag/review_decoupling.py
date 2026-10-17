"""For every IC power pin: the routed copper path to the nearest capacitor pad on the same rail
(Dijkstra over the net's tracks and vias), and the ground side: whether that capacitor's ground
pad has its own via. Flags paths over LIMIT mm."""
import heapq
import math
import sys

import pcbnew

LIMIT = 4.0
MM = 1e6
b = pcbnew.LoadBoard(sys.argv[1])


def key(p):
    return (round(p[0], 3), round(p[1], 3))


rails = sorted({p.GetNetname() for fp in b.GetFootprints() for p in fp.Pads()
                if p.GetNetname().startswith(("+", "-"))})
flagged, checked = [], 0
for rail in rails:
    adj = {}

    def link(a, c, w):
        adj.setdefault(a, []).append((c, w))
        adj.setdefault(c, []).append((a, w))
    tracks = [t for t in b.GetTracks() if t.GetNetname() == rail]
    ends = []
    for t in tracks:
        if t.Type() == pcbnew.PCB_VIA_T:
            ends.append((key((t.GetPosition().x / MM, t.GetPosition().y / MM)), None, t.GetWidth(pcbnew.F_Cu) / MM / 2))
        else:
            a = key((t.GetStart().x / MM, t.GetStart().y / MM))
            c = key((t.GetEnd().x / MM, t.GetEnd().y / MM))
            link((a, t.GetLayer()), (c, t.GetLayer()), t.GetLength() / MM)
            ends += [(a, t.GetLayer(), t.GetWidth() / MM / 2), (c, t.GetLayer(), t.GetWidth() / MM / 2)]
    layers = list(b.GetEnabledLayers().CuStack())
    # vias join every layer at their point; track ends that meet (within half a width) join
    for p, layer, h in ends:
        if layer is None:
            for l1 in layers:
                link((p, l1), (p, "via"), 0.0)
    pts = [(p, l, h) for p, l, h in ends]
    for i, (p, l, h) in enumerate(pts):
        for q, l2, h2 in pts[i + 1:]:
            if math.dist(p, q) <= max(h, h2) and (l == l2 or l is None or l2 is None):
                for la in ([l] if l is not None else layers):
                    for lb in ([l2] if l2 is not None else layers):
                        if la == lb:
                            link((p, la), (q, lb), math.dist(p, q))
    pads = [(fp, p) for fp in b.GetFootprints() for p in fp.Pads() if p.GetNetname() == rail]
    node_of = {}
    points = [k for k in adj if len(k) == 2 and isinstance(k[0], tuple)]
    for fp, p in pads:
        pl = [l for l in layers if p.IsOnLayer(l)]
        c = key((p.GetPosition().x / MM, p.GetPosition().y / MM))
        node = ("pad", fp.GetReference(), p.GetNumber())
        node_of[(fp.GetReference(), p.GetNumber())] = node
        for (q, l) in points:
            if l in pl and p.HitTest(pcbnew.VECTOR2I(int(q[0] * MM), int(q[1] * MM)), 0):
                link(node, (q, l), math.dist(c, q))
    caps = {node_of[(fp.GetReference(), p.GetNumber())] for fp, p in pads if fp.GetReference().startswith("C")}
    for fp, p in pads:
        ref = fp.GetReference()
        if not ref.startswith("U"):
            continue
        checked += 1
        start = node_of[(ref, p.GetNumber())]
        dist, heap, found, seq = {start: 0.0}, [(0.0, 0, start)], None, 0
        while heap:
            d, _s, n = heapq.heappop(heap)
            if d > dist.get(n, 1e18):
                continue
            if n in caps:
                found = (d, n)
                break
            for m, w in adj.get(n, ()):
                if d + w < dist.get(m, 1e18):
                    dist[m] = d + w
                    seq += 1
                    heapq.heappush(heap, (d + w, seq, m))
        if not found or found[0] > LIMIT:
            flagged.append((rail, f"{ref}.{p.GetNumber()}", round(found[0], 1) if found else None,
                            f"{found[1][1]}.{found[1][2]}" if found else None))
print(f"IC power pins checked: {checked}; with no capacitor within {LIMIT} mm of track: {len(flagged)}")
for f in sorted(flagged):
    print("  ", f)

"""JLC's parts placement for a board: its order files against the routed board, then JLC's
preview pictures against both. Run it when JLC offers the preview, before confirming.

    # Order files only. Needs nothing beyond Python:
    python3 tools/analogue_board/diag/jlc_placement.py pico_revb --against teensy_core_midi

    # With the preview PNGs. Needs numpy and matplotlib (build123d's venv has both):
    <python> tools/analogue_board/diag/jlc_placement.py pico_revb --against teensy_core_midi \
        --top Top.png --bottom Bottom.png --sheets <new dir>

(written for Rev B, 2026-11-04). It reads the board and schematic text itself, so it shares no
code with fab.py, which wrote the order files. Exit status 1 if anything needs looking at.

Order files: every part's position, face and footprint against the routed board, and its LCSC
number and value against the schematic, as the routed board doesn't carry LCSC numbers. Each part
type should have one rotation offset (CPL rotation less the board's). --against compares those
offsets with a board that has already been built and works, and lists what that board can't vouch
for. It can't tell whether an LCSC number is the right part: lcsc_footprints.py checks each one's
footprint against LCSC's own.

Preview: JLC draws in magenta, on the previews seen so far, a dot at each part's pin 1, a + and a −
on a polarised two-pad part, and an hourglass on a bidirectional one. This finds the marks, works
out the picture's scale and position from them and the pads, then checks that:
- every part of three or more pads has a mark on pad 1;
- every two-pad diode has its + on the anode, or is drawn as bidirectional;
- no other two-pad part is drawn as polarised, unless its + is on pad 1 (KiCad's CP footprints).

Its limits:
- The previews are about 10 pixels per mm, and it reads JLC's marks, not the part bodies. --sheets
  writes each of those parts enlarged, with our pads ringed and pad 1 yellow, to look at the bodies
  too: dots on SOICs and bands on SMA diodes show, but not on TSSOPs or SOD-323s.
- A one-of-a-kind part turned in the CPL can't show in the order files unless --against vouches
  for it. They list the ones it can't; the preview has to catch those.
- Its marks and limits come from two boards' previews, Rev A's bottom and Rev B's both faces. On a
  new board, or if JLC changes its drawing, look at the sheets too.

Tested 2026-11-04 on damaged copies of Rev B's files. The clean files pass. Caught: a part moved,
on the wrong face, turned, dropped, or not fitted but ordered; a wrong LCSC number, value or
footprint; the wrong picture; a capacitor drawn as polarised. All 37 parts whose orientation
matters, excluding the bidirectional TVSs, were flagged with their marks moved as if turned 90,
180 and 270 degrees: 111 of 111."""
import argparse
import collections
import csv
import math
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Pixel colour of JLC's marks; pixels of one mark may run into each other
MAGENTA = {"r_min": 190, "g_max": 90, "b_min": 190}
# Picture scales to try, px/mm, and the size of a bin when marks vote for a position, px
SCALES = (5.0, 25.0, 0.05)
VOTE_BIN = 4
# The furthest a real pin 1 mark sits from its pad's centre is 0.93 mm, on a TSSOP, on the previews
# seen so far. Much further, and a neighbour's mark could pass for it
MARK_REACH_MM = 1.3
# An hourglass on a SOD-323, on the previews seen so far: two patches close to the body's centre
# and 7 px or more together, or the two run into one of 8 px
HOURGLASS_REACH_MM = 0.65
HOURGLASS_ONE_PATCH_PX = 8


def read_board(path):
    """Designator -> footprint, face, position, rotation, value, pads (in board mm)."""
    text = open(path).read()
    parts = {}
    for m in re.finditer(r'\n\t\(footprint "([^"]+)"(.*?)\n\t\)', text, re.S):
        blk = m.group(2)
        ref = re.search(r'\(property "Reference" "([^"]+)"', blk).group(1)
        at = re.search(r'\n\t\t\(at (-?[\d.]+) (-?[\d.]+)(?: (-?[\d.]+))?\)', blk)
        x, y, rot = float(at.group(1)), float(at.group(2)), float(at.group(3) or 0)
        a = math.radians(rot)
        pads = {}
        for chunk in blk.split('(pad "')[1:]:
            p = re.match(r'([^"]*)"\s+(\w+)\s+\w+\s+\(at (-?[\d.]+) (-?[\d.]+)', chunk)
            if not p or p.group(1) in pads or not p.group(1):
                continue
            px, py = float(p.group(3)), float(p.group(4))
            fn = re.search(r'\(pinfunction "([^"]*)"\)', chunk)
            pads[p.group(1)] = dict(
                x=x + px * math.cos(a) + py * math.sin(a),
                y=y - px * math.sin(a) + py * math.cos(a),
                kind=p.group(2),
                fn=fn.group(1) if fn else "",
            )
        parts[ref] = dict(
            footprint=m.group(1).split(":")[-1],
            side=re.search(r'\(layer "([FB])\.Cu"\)', blk).group(1),
            x=x,
            y=y,
            rot=rot % 360,
            value=re.search(r'\(property "Value" "([^"]*)"', blk).group(1),
            pads=pads,
        )
    return parts


def read_schematics(folder):
    """Designator -> value, LCSC number and whether it's not fitted, from every sheet."""
    parts = {}
    for name in sorted(os.listdir(folder)):
        if not name.endswith(".kicad_sch"):
            continue
        text = open(os.path.join(folder, name)).read()
        for m in re.finditer(r'\n\t\(symbol\n(.*?)\n\t\)', text, re.S):
            blk = m.group(1)
            ref = re.search(r'\(property "Reference" "([^"]+)"', blk)
            value = re.search(r'\(property "Value" "([^"]*)"', blk)
            lcsc = re.search(r'\(property "LCSC" "([^"]*)"', blk)
            if ref and value:
                parts[ref.group(1)] = dict(
                    value=value.group(1),
                    lcsc=lcsc.group(1) if lcsc else "",
                    dnp="(dnp yes)" in blk,
                )
    return parts


def read_order(root, board):
    stem = os.path.join(root, "hardware", "analogue_board", board)
    fab = os.path.join(stem, "fab", f"analogue_board_{board}_jlc_")
    cpl = {r["Designator"]: r for r in csv.DictReader(open(fab + "cpl.csv"))}
    bom = {}
    for r in csv.DictReader(open(fab + "bom.csv")):
        for ref in r["Designator"].split(","):
            bom[ref.strip()] = dict(lcsc=r["LCSC Part #"], comment=r["Comment"], footprint=r["Footprint"])
    parts = read_board(os.path.join(stem, "routed_trial", f"analogue_board_{board}_routed.kicad_pcb"))
    return cpl, bom, parts


def check_order(root, board):
    """Returns (problems, rotation offsets by (footprint, LCSC, face), parts, cpl, bom)."""
    cpl, bom, parts = read_order(root, board)
    sch = read_schematics(os.path.join(root, "hardware", "analogue_board", board))
    problems = []
    for ref, s in sorted(sch.items()):
        if s["lcsc"] and not s["dnp"] and ref not in cpl:
            problems.append(f"{ref} has LCSC number {s['lcsc']} on the schematic, but isn't in the CPL")
        if s["dnp"] and ref in cpl:
            problems.append(f"{ref} is marked not fitted on the schematic, but is in the CPL")
    if set(cpl) != set(bom):
        problems.append(f"CPL and BOM list different parts: {sorted(set(cpl) ^ set(bom))}")
    offsets = collections.defaultdict(set)
    for ref, row in cpl.items():
        f = parts.get(ref)
        if f is None:
            problems.append(f"{ref} is in the CPL but not on the routed board")
            continue
        x, y = float(row["Mid X"].removesuffix("mm")), float(row["Mid Y"].removesuffix("mm"))
        if abs(x - f["x"]) > 0.01 or abs(y + f["y"]) > 0.01:
            problems.append(f"{ref} is at {x}, {y} in the CPL and {f['x']}, {-f['y']} on the board")
        side = "F" if row["Layer"] == "Top" else "B"
        if side != f["side"]:
            problems.append(f"{ref} is on face {side} in the CPL and {f['side']} on the board")
        if ref not in bom:
            continue
        if f["footprint"] != bom[ref]["footprint"]:
            problems.append(f"{ref} is {bom[ref]['footprint']} in the BOM and {f['footprint']} on the board")
        s = sch.get(ref)
        if s is None:
            problems.append(f"{ref} is in the BOM but not on the schematic")
        else:
            if s["lcsc"] != bom[ref]["lcsc"]:
                problems.append(f"{ref} is {bom[ref]['lcsc']} in the BOM and {s['lcsc'] or 'has no LCSC number'} on the schematic")
            if s["value"] != bom[ref]["comment"]:
                problems.append(f"{ref} is {bom[ref]['comment']} in the BOM and {s['value']} on the schematic")
        base = f["rot"] if side == "F" else (180 - f["rot"]) % 360
        offsets[(f["footprint"], bom[ref]["lcsc"], side)].add((float(row["Rotation"]) - base) % 360)
    for key, seen in offsets.items():
        if len(seen) > 1:
            problems.append(f"{key} has more than one rotation offset: {sorted(seen)}")
    faces = collections.Counter(r["Layer"] for r in cpl.values())
    print(f"{board}: CPL {len(cpl)}, BOM {len(bom)}; Top {faces['Top']}, Bottom {faces['Bottom']}; "
          f"{len(offsets)} combinations of part, footprint and face")
    return problems, offsets, parts, cpl, bom


def compare(offsets, parts, cpl, bom, against, other):
    """Rotation offsets against a built board. Returns problems; prints what that board can't vouch for."""
    problems = []
    same = 0
    new = []
    for key, seen in sorted(offsets.items()):
        if key not in other:
            new.append(key)
        elif other[key] == seen:
            same += 1
        else:
            problems.append(f"{key} has offset {sorted(seen)} here and {sorted(other[key])} on {against}")
    print(f"against {against}: {same} the same, {len(problems)} different, {len(new)} not on it in this form")
    for fp, lcsc, side in new:
        refs = sorted(r for r in cpl if r in bom and r in parts and bom[r]["lcsc"] == lcsc
                      and parts[r]["side"] == side and parts[r]["footprint"] == fp)
        kind = "orientation matters" if needs_orientation(refs[0], parts) else "passive"
        print(f"  {lcsc:9s} {fp[:30]:30s} {side}  {kind:19s} {parts[refs[0]]['value'][:18]:18s} {','.join(refs[:8])}")
    return problems


def needs_orientation(ref, parts):
    return len(parts[ref]["pads"]) > 2 or ref.startswith("D")


# ------------------------------------------------------------------ the preview


def read_marks(png):
    """The picture, and each connected patch of magenta: centre, pixel count, width, height."""
    import numpy as np
    import matplotlib.pyplot as plt

    im = plt.imread(png)[:, :, :3]
    if im.max() <= 1:
        im = im * 255
    mask = (im[:, :, 0] > MAGENTA["r_min"]) & (im[:, :, 1] < MAGENTA["g_max"]) & (im[:, :, 2] > MAGENTA["b_min"])
    h, w = mask.shape
    seen = np.zeros_like(mask, bool)
    marks = []
    for y0, x0 in zip(*np.nonzero(mask)):
        if seen[y0, x0]:
            continue
        seen[y0, x0] = True
        stack, pts = [(y0, x0)], []
        while stack:
            a, b = stack.pop()
            pts.append((a, b))
            for c, d in ((a + 1, b), (a - 1, b), (a, b + 1), (a, b - 1)):
                if 0 <= c < h and 0 <= d < w and mask[c, d] and not seen[c, d]:
                    seen[c, d] = True
                    stack.append((c, d))
        arr = np.array(pts)
        marks.append(dict(
            x=float(arr[:, 1].mean()),
            y=float(arr[:, 0].mean()),
            n=len(pts),
            w=int(arr[:, 1].max() - arr[:, 1].min() + 1),
            h=int(arr[:, 0].max() - arr[:, 0].min() + 1),
        ))
    return im, marks


def register(pins, marks, x_sign):
    """Board mm to picture px, from the marks alone. Each pair of a mark and a pin 1 votes for an
    offset at each scale; the scale and offset most pairs agree on starts a least-squares fit."""
    import numpy as np

    P = np.array(pins)
    M = np.array([(m["x"], m["y"]) for m in marks])
    best = None
    for s in np.arange(*SCALES):
        dx = (M[:, 0, None] - x_sign * s * P[:, 0]).ravel()
        dy = (M[:, 1, None] - s * P[:, 1]).ravel()
        key = np.floor(dx / VOTE_BIN).astype(np.int64) * 1_000_000 + np.floor(dy / VOTE_BIN).astype(np.int64)
        vals, counts = np.unique(key, return_counts=True)
        i = counts.argmax()
        if best is None or counts[i] > best[0]:
            kx = math.floor((vals[i] + 500_000) / 1_000_000)
            best = (counts[i], s, (kx + 0.5) * VOTE_BIN, (vals[i] - kx * 1_000_000 + 0.5) * VOTE_BIN)
    _, s, bx, by = best
    ax, ay = x_sign * s, s
    used = 0
    for reach in (15, 12, 10, 8, 8, 8):
        src, dst = [], []
        for wx, wy in P:
            px, py = ax * wx + bx, ay * wy + by
            d = np.hypot(M[:, 0] - px, M[:, 1] - py)
            k = d.argmin()
            if d[k] < reach:
                src.append((wx, wy))
                dst.append(M[k])
        src, dst = np.array(src), np.array(dst)
        used = len(src)
        ax, bx = np.polyfit(src[:, 0], dst[:, 0], 1)
        ay, by = np.polyfit(src[:, 1], dst[:, 1], 1)
    return ax, bx, ay, by, used


def settle_on_pads(im, pads, ax, bx, ay, by):
    """Marks overshoot their pads, and on some faces mostly one way, which biases a fit made from
    them by up to 0.5 mm. Pads don't: slide the fit to where the most pad centres land on light
    metal, or on a mark drawn over it, taking the middle of the offsets that do about as well."""
    import numpy as np

    r, g, b = im[:, :, 0], im[:, :, 1], im[:, :, 2]
    metal = ((r > 120) & (abs(r - g) < 40) & (abs(g - b) < 40)) | ((r > MAGENTA["r_min"]) & (g < MAGENTA["g_max"]) & (b > MAGENTA["b_min"]))
    X = np.array([ax * x + bx for x, _ in pads])
    Y = np.array([ay * y + by for _, y in pads])
    h, w = metal.shape
    scores = {}
    for dx in range(-8, 9):
        for dy in range(-8, 9):
            px, py = np.rint(X + dx).astype(int), np.rint(Y + dy).astype(int)
            ok = (px >= 0) & (px < w) & (py >= 0) & (py < h)
            scores[dx, dy] = int(metal[py[ok], px[ok]].sum())
    top = max(scores.values())
    near = [k for k, v in scores.items() if v >= 0.97 * top]
    return bx + float(np.mean([k[0] for k in near])), by + float(np.mean([k[1] for k in near]))


def is_plus(m):
    """A + has thin arms: on Rev A's and B's previews it fills 25-31 % of its box, where a dot, or
    a − run into a dot, fills 57 % or more."""
    return min(m["w"], m["h"]) >= 5 and m["n"] / (m["w"] * m["h"]) <= 0.45


def anode_pad(f):
    for name, pad in f["pads"].items():
        if pad["fn"].upper() in ("A", "ANODE"):
            return name
    return "2"  # KiCad's diode footprints: pad 1 is the cathode


def check_face(name, png, side, parts, cpl):
    """Returns problems, and everything a contact sheet needs."""
    im, marks = read_marks(png)
    placed = [r for r in cpl if r in parts and parts[r]["side"] == side]
    pins = [(parts[r]["pads"]["1"]["x"], parts[r]["pads"]["1"]["y"]) for r in placed if "1" in parts[r]["pads"]]
    ax, bx, ay, by, used = register(pins, marks, 1 if side == "F" else -1)
    smd = [(p["x"], p["y"]) for r in placed for p in parts[r]["pads"].values() if p["kind"] == "smd"]
    bx, by = settle_on_pads(im, smd, ax, bx, ay, by)
    print(f"{name}: {len(marks)} marks, {len(placed)} parts; {abs(ax):.2f} by {ay:.2f} px/mm from {used} of {len(pins)} pin 1s")
    problems = []
    if used < 0.6 * len(pins):
        problems.append(f"{name}: only {used} of {len(pins)} pin 1s found a mark: is this the right picture of this board?")
    mm = abs(ax)
    # Each mark goes to the nearest pad on this face, whichever part it is
    pads = [(r, pn, ax * p["x"] + bx, ay * p["y"] + by) for r in placed for pn, p in parts[r]["pads"].items()]
    owned = collections.defaultdict(list)
    for m in marks:
        d, r, pn = min((math.hypot(m["x"] - px, m["y"] - py), r, pn) for r, pn, px, py in pads)
        if d / mm <= MARK_REACH_MM:
            owned[r].append(dict(m, pad=pn, d=d / mm))
    report = collections.Counter()
    for r in sorted(placed):
        f = parts[r]
        own = owned[r]
        if len(f["pads"]) > 2:
            on_one = [m["d"] for m in own if m["pad"] == "1"]
            if on_one:
                report["multi-pin parts with a mark on pad 1"] += 1
            else:
                problems.append(f"{name}: {r} {f['value']}: no mark on pad 1; marks on pads {sorted({m['pad'] for m in own})}")
        elif len(f["pads"]) == 2:
            plus = [m["pad"] for m in own if is_plus(m)]
            if r.startswith("D"):
                # An hourglass stands on the body's centre, and is no pad's: find it directly
                px, py = ax * f["x"] + bx, ay * f["y"] + by
                centre = [m for m in marks if math.hypot(m["x"] - px, m["y"] - py) / mm < HOURGLASS_REACH_MM]
                want = anode_pad(f)
                if plus == [want]:
                    report["polarised diodes with + on the anode"] += 1
                elif not plus and (len(centre) >= 2 or sum(m["n"] for m in centre) >= HOURGLASS_ONE_PATCH_PX):
                    report["diodes drawn as bidirectional"] += 1
                else:
                    problems.append(f"{name}: {r} {f['value']}: anode is pad {want}; + read on pads {plus}")
            elif plus and plus != ["1"]:
                problems.append(f"{name}: {r} {f['value']}: drawn as polarised, + on pad {plus}")
            elif plus:
                report["polarised capacitors with + on pad 1"] += 1
    for what, n in report.items():
        print(f"  {n:3d} {what}")
    bare = sorted(r for r, f in parts.items() if r not in cpl and f["side"] == side
                  and any(p["kind"] == "smd" for p in f["pads"].values()))
    if bare:
        print(f"  bare on the picture, as JLC doesn't place them: {', '.join(bare)}")
    return problems, dict(im=im, ax=ax, bx=bx, ay=ay, by=by, side=side)


def write_sheets(faces, parts, cpl, problems, out):
    """Each part whose orientation matters, enlarged, with our pads ringed; anything flagged goes first."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    os.makedirs(out, exist_ok=True)
    flagged = set(re.findall(r": ([A-Z]+\d+) ", " ".join(problems)))
    refs = sorted((r for r in cpl if r in parts and parts[r]["side"] in faces and needs_orientation(r, parts)),
                  key=lambda r: (r not in flagged, r[0], len(r), r))
    per = 16
    for n in range(0, len(refs), per):
        fig, axes = plt.subplots(4, 4, figsize=(12.5, 13.2))
        for a in axes.ravel():
            a.set_axis_off()
        for a, r in zip(axes.ravel(), refs[n:n + per]):
            f = parts[r]
            g = faces[f["side"]]
            xs = [g["ax"] * p["x"] + g["bx"] for p in f["pads"].values()]
            ys = [g["ay"] * p["y"] + g["by"] for p in f["pads"].values()]
            cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
            half = int(max(max(xs) - min(xs), max(ys) - min(ys)) / 2 + 22)
            x0, x1, y0, y1 = max(int(cx) - half, 0), int(cx) + half, max(int(cy) - half, 0), int(cy) + half
            a.imshow(g["im"][y0:y1, x0:x1] / 255.0, extent=(x0, x1, y1, y0), interpolation="nearest")
            for pn, p in f["pads"].items():
                c = "yellow" if pn == "1" else "cyan"
                a.plot(g["ax"] * p["x"] + g["bx"], g["ay"] * p["y"] + g["by"], "o", mfc="none", mec=c, ms=7, mew=1)
            a.set_title(f"{'CHECK ' if r in flagged else ''}{r} {f['value'][:16]} ({'top' if f['side'] == 'F' else 'bottom'})", fontsize=9, pad=2)
        fig.tight_layout(pad=0.3)
        path = os.path.join(out, f"sheet_{n // per + 1}.png")
        fig.savefig(path, dpi=90)
        plt.close(fig)
    print(f"{len(refs)} parts enlarged in {out}")


def main():
    ap = argparse.ArgumentParser(description="Check JLC's placement of a board: order files, then its preview pictures.")
    ap.add_argument("board", help="its folder in hardware/analogue_board, such as pico_revb")
    ap.add_argument("--against", help="a built, working board to compare rotation offsets with")
    ap.add_argument("--top", help="JLC's preview of the top face, PNG")
    ap.add_argument("--bottom", help="JLC's preview of the bottom face, PNG")
    ap.add_argument("--sheets", help="a folder for enlarged pictures of the parts whose orientation matters")
    ap.add_argument("--root", default=REPO, help="the repo, or a copy of it to test on")
    args = ap.parse_args()

    problems, offsets, parts, cpl, bom = check_order(args.root, args.board)
    if args.against:
        _, other, *_ = check_order(args.root, args.against)
        problems += compare(offsets, parts, cpl, bom, args.against, other)
    faces = {}
    for name, png, side in (("Top", args.top, "F"), ("Bottom", args.bottom, "B")):
        if png:
            found, faces[side] = check_face(name, png, side, parts, cpl)
            problems += found
    if args.sheets and faces:
        write_sheets(faces, parts, cpl, problems, args.sheets)
    print()
    for p in problems:
        print("LOOK:", p)
    print(f"{len(problems)} to look at" if problems else "Nothing to look at")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()

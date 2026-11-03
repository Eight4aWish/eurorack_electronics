"""Every part JLC places on a board, against LCSC's own (EasyEDA) footprint for its LCSC number.
Run with KiCad's own Python, after fab.py:

    $KPY tools/analogue_board/diag/lcsc_footprints.py <routed.kicad_pcb> <jlc_bom.csv> <jlc_cpl.csv> <cache dir>

(written for Rev B, 2026-11-03, after its H11L1 turned out to need SMDIP's rotation offset).

For each part type: fetch LCSC's footprint with easyeda2kicad (cached), find the turn (0, 90,
180, 270) that best lays KiCad's pads over LCSC's, pad number by pad number, and report the
pad counts, the worst pad-centre gap, the pad-size ratio, and the rotation JLC then needs
(KiCad rotation minus that turn) against the one the CPL gives. Two-pad parts that are not
polarised (R, C, FB, L) may match at either of two opposite turns."""
import csv
import math
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.dirname(HERE))

from fab import ROTATION  # noqa: E402

E2K = os.path.join(REPO, ".venv", "bin", "easyeda2kicad")
KLIB = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints"
PLIB = os.path.join(REPO, "hardware", "analogue_board", "analogue_board.pretty")

board_path, bom_path, cpl_path, cache = sys.argv[1:5]
board = open(board_path).read()

# designator -> (lib:name, rotation, layer) from the board
fps = {}
for m in re.finditer(r'\n\t\(footprint "([^"]+)"(.*?)\n\t\)', board, re.S):
    blk = m.group(2)
    ref = re.search(r'\(property "Reference" "([^"]+)"', blk).group(1)
    at = re.search(r'\n\t\t\(at [-\d.]+ [-\d.]+(?: ([-\d.]+))?\)', blk)
    layer = re.search(r'\(layer "([FB])\.Cu"\)', blk).group(1)
    fps[ref] = (m.group(1), float(at.group(1) or 0), layer)

cpl = {r["Designator"]: (float(r["Rotation"]), r["Layer"]) for r in csv.DictReader(open(cpl_path))}


def pads_of(text):
    """{pad number: (x, y, w, h)} from a .kicad_mod's text (SMD and through-hole pads)."""
    out = {}
    for m in re.finditer(r'\(pad "?([^"\s]*)"? (smd|thru_hole|np_thru_hole) \w+\s*\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)\s*'
                         r'\(size ([-\d.]+) ([-\d.]+)\)', text):
        num = m.group(1)
        if not num:
            continue
        a = float(m.group(5) or 0)
        w, h = float(m.group(6)), float(m.group(7))
        if round(a) % 180 == 90:
            w, h = h, w
        out.setdefault(num, (float(m.group(3)), float(m.group(4)), w, h))
    return out


def kicad_pads(libid):
    lib, name = libid.split(":", 1)
    path = os.path.join(PLIB if lib == "analogue_board" else os.path.join(KLIB, lib + ".pretty"), name + ".kicad_mod")
    return pads_of(open(path).read())


def lcsc_pads(lcsc):
    d = os.path.join(cache, lcsc)
    mods = [os.path.join(r, f) for r, _, fs in os.walk(d) for f in fs if f.endswith(".kicad_mod")] if os.path.isdir(d) else []
    if not mods:
        os.makedirs(d, exist_ok=True)   # easyeda2kicad will not make its output's folder
        subprocess.run([E2K, "--footprint", f"--lcsc_id={lcsc}", "--output", os.path.join(d, lcsc)],
                       capture_output=True, text=True, timeout=120)
        mods = [os.path.join(r, f) for r, _, fs in os.walk(d) for f in fs if f.endswith(".kicad_mod")]
    return (pads_of(open(mods[0]).read()), os.path.basename(mods[0])) if mods else (None, None)


def centred(p):
    cx = sum(v[0] for v in p.values()) / len(p)
    cy = sum(v[1] for v in p.values()) / len(p)
    return {k: (v[0] - cx, v[1] - cy, v[2], v[3]) for k, v in p.items()}


def turn(p, deg):
    """KiCad's rotation of footprint coordinates by deg (y down, positive counter-clockwise on screen)."""
    c, s = round(math.cos(math.radians(deg))), round(math.sin(math.radians(deg)))
    return {k: (x * c + y * s, -x * s + y * c, w if deg % 180 == 0 else h, h if deg % 180 == 0 else w)
            for k, (x, y, w, h) in p.items()}


rows = list(csv.DictReader(open(bom_path)))
lcsc_col = [c for c in rows[0] if "LCSC" in c][0]
problems = []
print(f"{'part':18} {'LCSC':9} {'KiCad footprint':34} {'pads':7} {'gap':6} {'size':6} {'LCSC':5} {'fab':5} verdict")
for r in rows:
    lcsc = r[lcsc_col].strip()
    ref = re.split(r"[,\s]", r["Designator"])[0]
    libid, krot, layer = fps[ref]
    kp = centred(kicad_pads(libid))
    lp, lname = lcsc_pads(lcsc)
    if not lp:
        print(f"{r['Comment'][:18]:18} {lcsc:9} {libid.split(':')[1][:34]:34} no LCSC footprint")
        problems.append((r["Comment"], "no LCSC footprint"))
        continue
    lp = centred(lp)
    polar = not re.match(r"^(R|C|FB|L)\d", ref)
    best = None
    for deg in (0, 90, 180, 270):
        t = turn(kp, deg)
        common = set(t) & set(lp)
        if not common:
            continue
        gap = max(math.hypot(t[k][0] - lp[k][0], t[k][1] - lp[k][1]) for k in common)
        size = max(max(lp[k][2] / t[k][2], t[k][2] / lp[k][2], lp[k][3] / t[k][3], t[k][3] / lp[k][3]) for k in common)
        if best is None or gap < best[1] - 1e-6:
            best = (deg, gap, size)
    deg, gap, size = best
    implied = (-deg) % 360             # what JLC must add to KiCad's rotation (top side)
    name = libid.split(":", 1)[1]
    rule = next((o for pat, o in ROTATION if re.match(pat, name)), 0)
    diff = (rule - implied) % 360
    ok_rot = diff == 0 or (not polar and diff == 180)
    verdict = []
    if set(kp) != set(lp):
        verdict.append(f"pads differ: KiCad {sorted(kp)} LCSC {sorted(lp)}")
    if gap > 0.25:
        verdict.append(f"pad gap {gap:.2f} mm")
    if size > 1.6:
        verdict.append(f"pad size x{size:.1f}")
    if not ok_rot:
        verdict.append(f"ROTATION: LCSC implies +{implied}, fab.py adds +{rule}")
    v = "; ".join(verdict) or "ok"
    if verdict:
        problems.append((r["Comment"], name, v))
    print(f"{r['Comment'][:18]:18} {lcsc:9} {name[:34]:34} {len(kp)}/{len(lp):<5} {gap:<6.2f} x{size:<5.2f} +{implied:<4} +{rule:<4} {v}")
print("\nProblems:", len(problems))
for p in problems:
    print(" ", p)

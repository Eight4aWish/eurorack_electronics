"""JLCPCB fabrication and assembly files from a finished board.

Run with KiCad's own Python (it has pcbnew), on a board finished by finish.py:

    /Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 \\
        tools/analogue_board/fab.py <board> <finished.kicad_pcb>

<board> names the board (shared_core, say), for its schematic BOM and its folder. Writes
hardware/analogue_board/<board>/fab/:

- <name>_gerbers.zip: every copper layer, mask, paste, silkscreen and the outline, with the
  plated and unplated drill files: the PCB order.
- <name>_jlc_bom.csv: Comment, Designator, Footprint, LCSC Part #, for the parts JLC places (the
  ones with an LCSC number; the module sockets, the power header and the wiring holes are
  hand-soldered or bare).
- <name>_jlc_cpl.csv: Designator, Mid X, Mid Y, Layer, Rotation, for the same parts.

Rotation: JLC's part models do not all share KiCad's zero orientation. ROTATION holds the usual
offsets by footprint name (the table kicad-jlcpcb-tools ships); bottom-side parts are mirrored
about the Y axis first. These are a starting point, not a guarantee: every part's placement is
checked in JLC's own preview before the order is paid.
"""

import csv
import os
import re
import shutil
import subprocess
import sys
import zipfile

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import variant  # noqa: E402

KICAD_CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
MM = 1e6

# (footprint name pattern, degrees added on the top side and taken away on the bottom)
ROTATION = [
    (r"^SOT-23", 180), (r"^SOT-223", 180), (r"^SOT-89", 180), (r"^SOT-143", 180), (r"^SOT-353", 180),
    (r"^SOT-363", 180), (r"^SC-74-6", 180), (r"^VSSOP-8_", 180),
    (r"^SOIC-", 270), (r"^TSSOP-", 270), (r"^HTSSOP-", 270), (r"^SSOP-", 270), (r"^MSOP-", 270),
    (r"^TSOP-", 270), (r"^QFN-", 270), (r"^LQFP-", 270), (r"^WSON-", 270), (r"^VSON-8_", 270),
    (r"^R_Array_Convex_", 90), (r"^R_Array_Concave_", 90), (r"^TO-277", 90),
]


def expand(refs):
    """'C511-C514,C801' -> ['C511', 'C512', 'C513', 'C514', 'C801']"""
    out = []
    for part in refs.split(","):
        part = part.strip()
        m = re.fullmatch(r"([A-Z]+)(\d+)-([A-Z]+)(\d+)", part)
        if m:
            out += [f"{m.group(1)}{i}" for i in range(int(m.group(2)), int(m.group(4)) + 1)]
        elif part:
            out.append(part)
    return out


def bom():
    """{ref: (value, footprint name, LCSC)} for every part with an LCSC number, from the schematic BOM."""
    path = os.path.join(variant.DIR, "output", f"{variant.NAME}_bom.csv")
    placed = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["LCSC"]:
                for ref in expand(row["Refs"]):
                    placed[ref] = (row["Value"], row["Footprint"].split(":")[-1], row["LCSC"])
    return placed


def rotation(fp):
    rot = fp.GetOrientation().AsDegrees()
    bottom = fp.GetLayer() == pcbnew.B_Cu
    if bottom:
        rot = 180 - rot          # seen from the top, a bottom part is mirrored about the Y axis
    name = str(fp.GetFPID().GetLibItemName())
    for pattern, offset in ROTATION:
        if re.search(pattern, name):
            rot += -offset if bottom else offset
            break
    return rot % 360


def gerbers(src, outdir, copper):
    layers = ["F.Cu", *[f"In{i}.Cu" for i in range(1, copper - 1)], "B.Cu", "F.Paste", "B.Paste",
              "F.Silkscreen", "B.Silkscreen", "F.Mask", "B.Mask", "Edge.Cuts"]
    for args in (["pcb", "export", "gerbers", "--layers", ",".join(layers), "-o", outdir + os.sep, src],
                 ["pcb", "export", "drill", "--format", "excellon", "--excellon-units", "mm",
                  "--excellon-separate-th", "-o", outdir + os.sep, src]):
        r = subprocess.run([KICAD_CLI, *args], capture_output=True, text=True)
        if r.returncode != 0:
            raise SystemExit(f"kicad-cli {' '.join(args[:3])} failed:\n{r.stdout}{r.stderr}")


def main(src):
    variant.require()
    src = os.path.abspath(src)
    fab = os.path.join(variant.DIR, "fab")
    plots = os.path.join(fab, "gerbers")
    shutil.rmtree(plots, ignore_errors=True)
    os.makedirs(plots)
    board = pcbnew.LoadBoard(src)
    copper = board.GetCopperLayerCount()
    gerbers(src, plots, copper)
    zpath = os.path.join(fab, f"{variant.NAME}_gerbers.zip")
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for name in sorted(os.listdir(plots)):
            z.write(os.path.join(plots, name), name)

    parts = bom()
    on_board = {fp.GetReference(): fp for fp in board.GetFootprints()}
    missing = sorted(set(parts) - set(on_board))
    if missing:
        raise SystemExit(f"In the BOM but not on the board: {missing}")
    rows = sorted(parts, key=lambda r: (re.sub(r"\d", "", r), int(re.sub(r"\D", "", r) or 0)))
    with open(os.path.join(fab, f"{variant.NAME}_jlc_bom.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #"])
        groups = {}
        for ref in rows:
            groups.setdefault(parts[ref], []).append(ref)
        for (value, footprint, lcsc), refs in groups.items():
            w.writerow([value, ",".join(refs), footprint, lcsc])
    sides = {"Top": 0, "Bottom": 0}
    with open(os.path.join(fab, f"{variant.NAME}_jlc_cpl.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        for ref in rows:
            fp = on_board[ref]
            p = fp.GetPosition()
            side = "Bottom" if fp.GetLayer() == pcbnew.B_Cu else "Top"
            sides[side] += 1
            # Gerber coordinates: KiCad's, with y upwards
            w.writerow([ref, f"{p.x / MM:.4f}mm", f"{-p.y / MM:.4f}mm", side, f"{rotation(fp):g}"])
    print(f"{copper}-layer board; gerbers and drill: {zpath}")
    print(f"Parts JLC places: {len(rows)} ({sides['Top']} top, {sides['Bottom']} bottom), "
          f"{len(groups)} part types")
    print(f"BOM and CPL: {fab}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("fab.py <board> <finished.kicad_pcb>")
    main(sys.argv[2])

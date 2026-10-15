"""Build the analogue board schematic and run every checkpoint-1 check.

    python3 tools/analogue_board/build.py

1. regenerate the project symbol and footprint libraries
2. regenerate every .kicad_sch sheet from design*.py
3. KiCad ERC, netlist and PDF through kicad-cli
4. the checks in checks.py: intended vs KiCad netlist, every IC pin against its datasheet,
   decoupling on every power pin, orientation of every polarised part
"""

import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import make_library  # noqa: E402
from design import OUT, new_project, sheet_power, sheet_root  # noqa: E402
from design_analog import sheet_codec, sheet_cv_dac, sheet_cv_in  # noqa: E402
from design_digital import sheet_edge, sheet_expander, sheet_gate_in, sheet_midi, sheet_pots_gates  # noqa: E402

KICAD_CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
NAME = "analogue_board"


def write_project_files(pr):
    with open(os.path.join(OUT, "sym-lib-table"), "w") as f:
        f.write('(sym_lib_table\n  (version 7)\n  (lib (name "analogue_board")(type "KiCad")'
                '(uri "${KIPRJMOD}/analogue_board.kicad_sym")(options "")(descr "Analogue board project symbols"))\n)\n')
    with open(os.path.join(OUT, "fp-lib-table"), "w") as f:
        f.write('(fp_lib_table\n  (version 7)\n  (lib (name "analogue_board")(type "KiCad")'
                '(uri "${KIPRJMOD}/analogue_board.pretty")(options "")(descr "Analogue board project footprints"))\n)\n')
    pro = os.path.join(OUT, f"{NAME}.kicad_pro")
    data = {}
    if os.path.exists(pro):
        with open(pro) as f:
            data = json.load(f)
    data.setdefault("meta", {"filename": f"{NAME}.kicad_pro", "version": 3})
    data["sheets"] = [[s.symbol_uuid if s is not pr.root else s.uuid, s.name if s is not pr.root else "Root"]
                      for s in pr.sheets]
    sch = data.setdefault("schematic", {})
    sch.setdefault("drawing", {})["default_line_thickness"] = 6.0
    data.setdefault("erc", {}).setdefault("rule_severities", {})
    with open(pro, "w") as f:
        json.dump(data, f, indent=2)


def generate():
    os.makedirs(OUT, exist_ok=True)
    make_library.write_symbols()
    make_library.write_footprints()
    pr = new_project()
    subs = sheet_root(pr)
    for sh, fn in zip(subs, [sheet_power, sheet_codec, sheet_cv_in, sheet_cv_dac,
                             sheet_pots_gates, sheet_expander, sheet_gate_in, sheet_edge, sheet_midi]):
        fn(sh)
    pr.write(OUT)
    write_project_files(pr)
    return pr


def kicad(*args):
    r = subprocess.run([KICAD_CLI, *args], capture_output=True, text=True)
    out = "\n".join(l for l in (r.stdout + r.stderr).splitlines() if "Fontconfig" not in l)
    return r.returncode, out


def export():
    sch = os.path.join(OUT, f"{NAME}.kicad_sch")
    out = os.path.join(OUT, "output")
    os.makedirs(out, exist_ok=True)
    rc, msg = kicad("sch", "erc", "--format", "json", "--severity-all", "-o", os.path.join(out, "erc.json"), sch)
    rc2, msg2 = kicad("sch", "erc", "--severity-all", "-o", os.path.join(out, "erc.rpt"), sch)
    print(msg2)
    kicad("sch", "export", "netlist", "--format", "kicadsexpr", "-o", os.path.join(out, f"{NAME}.net"), sch)
    kicad("sch", "export", "pdf", "-o", os.path.join(OUT, f"{NAME}_schematic.pdf"), sch)
    kicad("sch", "export", "bom", "--fields", "Reference,Value,Footprint,LCSC,MPN,JLC,${QUANTITY}",
          "--labels", "Refs,Value,Footprint,LCSC,MPN,JLC,Qty", "--group-by", "Value,Footprint,LCSC",
          "--exclude-dnp", "-o", os.path.join(out, f"{NAME}_bom.csv"), sch)
    return out


if __name__ == "__main__":
    pr = generate()
    out = export()
    import checks
    ok = checks.run(pr, out)
    sys.exit(0 if ok else 1)

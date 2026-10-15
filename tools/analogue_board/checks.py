"""Checkpoint-1 checks on the generated schematic. Called from build.py; writes output/checks.md.

1. ERC summary from kicad-cli.
2. Netlist: every pin KiCad sees is one the generator meant to connect (or leave open), every intended
   net is one KiCad net, and no two intended nets are shorted.
3. Pins: every IC symbol's pin numbers and names against the datasheet transcription
   (datasheet_pins.json), and every footprint's pads against the symbol's pins.
4. Decoupling: every power-input pin of every IC has a capacitor to GND assigned to it.
5. Polarity: every diode's anode and cathode nets, against the rule for its job.
"""

import json
import os
import re
from collections import defaultdict

from kicad_lib import symbol_pins
from netlist import read_netlist
from parts import ICS
from sexpr import find_all, parse

HERE = os.path.dirname(os.path.abspath(__file__))
FOOTPRINTS = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints"

# part key -> datasheet entry in datasheet_pins.json
DATASHEET = {"PCM3060": "PCM3060PWR", "ADS8688": "ADS8688IDBTR", "DAC8568": "DAC8568IAPWR", "MCP3208": "MCP3208-CI/SL",
             "DG412": "DG412DQ-T1-E3", "TL074H": "TL074HIDR", "LM393": "LM393DR2G", "74HCT595": "74HCT595PW",
             "TCA9555": "TCA9555PWR", "M24C64": "M24C64-RMN6TP", "AHCT1G125": "SN74AHCT1G125DBVR",
             "XC6206": "XC6206P332MR", "L78M05": "L78M05ABDT", "TPS54308": "TPS54308DDCR", "BAT54S": "BAT54S",
             "BAV99": "BAV99", "QWIIC": "SM04B-SRSS-TB", "PICO2": "PICO2", "TEENSY41": "TEENSY41",
             "H11L1": "H11L1M", "AO3401A": "AO3401A"}

# Datasheet name -> KiCad library name, where the two spell the same pin differently (normalised forms).
ALIASES = {
    "PCM3060": {"MS/ADR/IFMD": "MS/AD/IFMD"},
    "74HCT595": {"Q0": "QA", "Q1": "QB", "Q2": "QC", "Q3": "QD", "Q4": "QE", "Q5": "QF", "Q6": "QG", "Q7": "QH",
                 "Q7S": "QH'", "MR": "SRCLR", "SHCP": "SRCLK", "STCP": "RCLK", "DS": "SER"},
    "XC6206": {"VSS": "GND", "VIN": "VI", "VOUT": "VO"},
    "L78M05": {"INPUT": "VI", "OUTPUT": "VO"},
    "PICO2": {"3V3": "3V3OUT"},
    "BAT54S": {"ANODE(DIODE1)": "A", "CATHODE(DIODE2)": "K", "CATHODE(DIODE1)/ANODE(DIODE2)": "COM"},
    "BAV99": {"A1": "A", "K2": "K", "K1,A2": "COM"},
    "QWIIC": {"CIRCUITNO.1": "PIN1", "CIRCUIT2": "PIN2", "CIRCUIT3": "PIN3", "CIRCUIT4": "PIN4"},
}


def norm(name):
    s = name.replace("~{", "").replace("_{", "").replace("}", "").replace("−", "-").replace("–", "-")
    s = re.sub(r"\s+", "", s).upper()
    return s.replace("_", "")


def semantic(key, pin, pins_by_unit):
    """The library pin as the datasheet would name it, for symbols whose pins are unnamed or role-named."""
    n = norm(pin.name)
    if key == "TL074H":
        if pin.unit == 5:
            return {"V+": "VCC+", "V-": "VCC-"}[n]
        role = {"+": "IN+", "-": "IN-", "~": "OUT"}[n]
        return f"{pin.unit}{role}"
    if key == "LM393":
        if pin.unit == 3:
            return {"V+": "VCC", "V-": "GND"}[n]
        ab = "AB"[pin.unit - 1]
        return {"+": f"INPUTS{ab}(+)", "-": f"INPUTS{ab}(-)", "~": f"OUTPUT{ab}"}[n]
    if key == "DG412":
        if pin.unit == 5:
            return n
        return None  # checked by grouping below
    if key == "AHCT1G125":
        if n != "~":
            return n
        return {"input": None, "tri_state": "Y"}[pin.etype] if pin.etype == "tri_state" else ("OE" if pin.y > 0 else "A")
    if key == "H11L1":
        # KiCad leaves these pins unnamed: check the number's role by its electrical type
        role = {"1": ("ANODE", "passive"), "2": ("CATHODE", "passive"), "3": ("NC", "no_connect"),
                "4": ("VO", "output"), "5": ("GND", "power_in"), "6": ("VCC", "power_in")}[pin.number]
        return role[0] if pin.etype == role[1] else f"{role[0]}?TYPE {pin.etype}"
    if key == "TEENSY41":
        return {"3V3": "3.3V", "VIN": "VIN"}.get(n, n[1:] if n.startswith("D") and n[1:].isdigit() else n)
    return n


def check_pins(project_libs):
    with open(os.path.join(HERE, "datasheet_pins.json"), encoding="utf-8") as f:
        ds = json.load(f)
    lines, bad = [], 0
    for key, entry in DATASHEET.items():
        p = ICS[key]
        pins = symbol_pins(p["lib"], project_libs)
        dpins = {str(k): v for k, v in ds[entry].get("pins", {}).items()}
        if key == "TEENSY41":
            from make_library import teensy41_pins
            left, right = ds[entry]["left_top_to_bottom"], ds[entry]["right_top_to_bottom"]
            dpins = {str(i + 1): lab for i, lab in enumerate(left)}
            dpins.update({str(48 - i): lab for i, lab in enumerate(right)})
        if key == "QWIIC":
            dpins = {k: v for k, v in dpins.items() if k.isdigit()}
            dpins["MP"] = "MP"
        if "TAB" in dpins and norm(dpins["TAB"]) == norm(dpins.get("2", "")):
            del dpins["TAB"]  # DPAK: the tab is pin 2 (footprint pad 2)
        aliases = ALIASES.get(key, {})
        problems, renamed = [], []
        lib_nums = {pin.number for pin in pins}
        if set(dpins) != lib_nums:
            problems.append(f"pin numbers differ: datasheet only {sorted(set(dpins) - lib_nums)}, library only {sorted(lib_nums - set(dpins))}")
        for pin in pins:
            if pin.number not in dpins:
                continue
            want = norm(dpins[pin.number])
            want = norm(aliases.get(want, want))
            got = semantic(key, pin, None)
            if key == "QWIIC":
                got = "MP" if pin.number == "MP" else norm(pin.name).replace("PIN", "PIN")
                want = "MP" if pin.number == "MP" else want
            if got is None:
                continue
            if norm(got) != want:
                problems.append(f"pin {pin.number}: library {pin.name!r} vs datasheet {dpins[pin.number]!r}")
            elif norm(dpins[pin.number]) != norm(pin.name) and key not in ("TL074H", "LM393", "AHCT1G125", "H11L1"):
                renamed.append(f"{pin.number} {dpins[pin.number]}→{pin.name}")
        if key == "DG412":
            units = defaultdict(list)
            for pin in pins:
                if pin.unit != 5:
                    units[pin.unit].append(pin)
            for u, ps in sorted(units.items()):
                names = {norm(dpins[x.number]) for x in ps}
                idx = {n[-1] for n in names}
                inp = [x for x in ps if x.etype == "input"]
                if len(idx) != 1 or {n[:-1] for n in names} != {"IN", "D", "S"} or len(inp) != 1 or not norm(dpins[inp[0].number]).startswith("IN"):
                    problems.append(f"unit {u}: pins {[x.number for x in ps]} are {sorted(names)}")
                else:
                    renamed.append(f"unit {u} = switch {idx.pop()} (pins {', '.join(x.number for x in ps)})")
        status = "OK" if not problems else "MISMATCH"
        bad += bool(problems)
        lines.append(f"| {key} | `{p['lib']}` | {entry} | {len(pins)} | {status} | "
                     + ("; ".join(problems) if problems else ("; ".join(renamed) if renamed else "names match")) + " |")
    return bad, lines


def footprint_pads(fp):
    lib, name = fp.split(":", 1)
    if lib == "analogue_board":
        path = os.path.join(HERE, "..", "..", "hardware", "analogue_board", "analogue_board.pretty", name + ".kicad_mod")
    else:
        path = os.path.join(FOOTPRINTS, lib + ".pretty", name + ".kicad_mod")
    with open(path, encoding="utf-8") as f:
        tree = parse(f.read())
    return {str(pd[1]) for pd in find_all(tree, "pad") if str(pd[1])}


def check_footprints(comps, project_libs, nets=None):
    """Every symbol pin has a pad and every pad a pin. A module socket may leave out the holes for
    module pins the board never uses (shorter female headers), but only pins the netlist leaves
    unconnected: anything else is a mismatch."""
    connected = {node for nodes in (nets or {}).values() for node in nodes} if nets else set()
    unconnected_nets = {n for n in (nets or {}) if n.startswith("unconnected-")}
    nc_nodes = {node for n in unconnected_nets for node in nets[n]}
    seen, lines, bad = {}, [], 0
    for ref, c in comps.items():
        if ref.startswith("#"):
            continue
        key = (c["lib"], c["footprint"])
        if key in seen or not c["footprint"]:
            continue
        seen[key] = ref
        pins = {p.number for p in symbol_pins(c["lib"], project_libs)}
        pads = footprint_pads(c["footprint"])
        omitted = pins - pads
        # project footprints (module sockets, the right edge strip) may leave out holes for pins
        # that nothing connects to; any other omission, or one on a connected pin, is a mismatch
        allowed = c["footprint"].startswith("analogue_board:") and nets is not None and all(
            (ref, n) in nc_nodes or (ref, n) not in connected for n in omitted)
        ok = (pins == pads) or (allowed and not (pads - pins))
        bad += not ok
        if not ok:
            lines.append(f"| {c['lib']} | {c['footprint']} | MISMATCH: symbol only {sorted(pins - pads)}, footprint only {sorted(pads - pins)} |")
        elif omitted:
            lines.append(f"| {c['lib']} | {c['footprint']} | {len(pads)} pads match; no holes for unconnected pins "
                         f"{', '.join(sorted(omitted, key=int))} (by design) |")
        else:
            lines.append(f"| {c['lib']} | {c['footprint']} | {len(pads)} pads match |")
    return bad, lines


def check_netlist(pr, nets):
    pin_net = {}
    for name, nodes in nets.items():
        for node in nodes:
            pin_net[node] = name
    intent = {}  # (ref, pin) -> scoped net or None
    problems = []
    for sh in pr.sheets:
        for ref, pin, net, _pos in sh.connections:
            if net is None:
                scoped = None
            elif net in pr.power_nets or net in pr.global_nets:
                scoped = net
            else:
                scoped = f"/{net}" if sh is pr.root else f"/{sh.name}/{net}"
            key = (ref, pin)
            if key in intent and intent[key] != scoped:
                problems.append(f"{ref}.{pin} intended for both {intent[key]} and {scoped}")
            intent[key] = scoped
    # every pin KiCad sees has an intent
    for node in pin_net:
        if node[0].startswith("#"):
            continue
        if node not in intent:
            problems.append(f"{node[0]}.{node[1]} is in KiCad net {pin_net[node]} but the generator never placed it")
    groups = defaultdict(set)
    for node, scoped in intent.items():
        if node not in pin_net:
            problems.append(f"{node[0]}.{node[1]} intended for {scoped} but missing from KiCad's netlist")
            continue
        if scoped is None:
            k = pin_net[node]
            others = [n for n in nets[k] if not n[0].startswith("#") and n != node]
            if others:
                problems.append(f"{node[0]}.{node[1]} meant to be unconnected but KiCad has it on {k} with {others}")
            continue
        groups[scoped].add(pin_net[node])
    kicad_owner = {}
    unnamed = []
    for scoped, kn in groups.items():
        if len(kn) > 1:
            problems.append(f"intended net {scoped} is split across KiCad nets {sorted(kn)}")
        for k in kn:
            if k in kicad_owner and kicad_owner[k] != scoped:
                problems.append(f"intended nets {kicad_owner[k]} and {scoped} are shorted (KiCad net {k})")
            kicad_owner[k] = scoped
            if k != scoped:
                if k.startswith("Net-("):
                    unnamed.append(scoped)
                else:
                    problems.append(f"intended net {scoped} is named {k} by KiCad")
    real = {k for k, v in nets.items() if any(not n[0].startswith("#") for n in v)}
    return problems, unnamed, len(real), len(intent)


def check_decoupling(comps, nets, pr):
    """Every power_in pin (not GND) of every U/A part must have a capacitor between its net and GND whose
    Decouples field names that ref and pin."""
    pin_net = {node: name for name, nodes in nets.items() for node in nodes}
    caps = []
    for ref, c in comps.items():
        if ref.startswith("C"):
            d = c["fields"].get("Decouples", "")
            n1, n2 = pin_net.get((ref, "1")), pin_net.get((ref, "2"))
            caps.append((ref, d, {n1, n2}, c["value"]))
    rows, bad = [], 0
    for ref, c in sorted(comps.items()):
        if not (ref.startswith("U") or ref.startswith("A")):
            continue
        for p in symbol_pins(c["lib"], pr.project_libs):
            if p.etype != "power_in":
                continue
            net = pin_net.get((ref, p.number))
            if net in (None, "GND") or (net or "").startswith("unconnected"):
                continue
            mine = [f"{cref} {val}" for cref, d, ns, val in caps
                    if ns == {net, "GND"} and re.search(rf"\b{ref}\b", d) and re.search(rf"\bpin {p.number}\b", d)]
            ok = bool(mine)
            bad += not ok
            rows.append(f"| {ref} | {c['value']} | {p.number} {p.name} | {net} | {', '.join(mine) if mine else '**none**'} |")
    return bad, rows


POLARITY_RULES = {
    # ref: {pin: expected net}, with why
    "D201": ({"2": "/Power/+12V_IN", "1": "/Power/+12V_P"}, "+12 V reverse-polarity: anode at the header"),
    "D202": ({"1": "/Power/-12V_IN", "2": "/Power/-12V_P"}, "-12 V reverse-polarity: cathode at the header"),
    "D203": ({"2": "+5VD", "1": "MOD_5V"}, "module supply: anode on +5VD, cathode to VSYS/VIN"),
}


def check_polarity(comps, nets):
    pin_net = {node: name for name, nodes in nets.items() for node in nodes}
    rows, bad = [], 0
    opto = next((r for r, c in comps.items() if c["lib"] == "Isolator:H11L1"), None)
    for ref, c in sorted(comps.items()):
        if not (ref.startswith("D") or ref.startswith("Q")):
            continue
        got = {pn: pin_net.get((ref, pn)) for pn in ("1", "2", "3") if (ref, pn) in pin_net}
        if c["lib"] == "Transistor_FET:AO3401A":
            why = "MOD_5V bypass: drain on +5VD, source on MOD_5V, gate on PICO_VBUS (body diode +5VD → MOD_5V)"
            ok = got.get("3") == "+5VD" and got.get("2") == "MOD_5V" and got.get("1") == "PICO_VBUS"
        elif c["lib"] == "Diode:1N4148WS" and opto:
            why = "reverse-parallel across the H11L1 LED: cathode on its anode (pin 1), anode on its cathode (pin 2)"
            ok = got.get("1") == pin_net.get((opto, "1")) and got.get("2") == pin_net.get((opto, "2"))
        elif c["lib"] == "Device:D_TVS":
            why = "bidirectional TVS: one side on a CV jack, the other on GND"
            nets = {got.get("1"), got.get("2")}
            ok = "GND" in nets and any(n and re.search(r"/(CV\d|CVI\d)$", n) for n in nets)
        elif ref in POLARITY_RULES:
            want, why = POLARITY_RULES[ref]
            ok = all(got.get(k) == v for k, v in want.items())
        elif c["lib"] == "Diode:BAT54S":
            why = f"{c['value']} clamp: anode (1) to GND, cathode (2) to a positive rail, common (3) on the signal"
            ok = got.get("1") == "GND" and got.get("2") in ("+5VA", "+5VD", "+3V3D", "+3V3A") and got.get("3") not in (None, "GND")
        else:
            why, ok = "no rule", False
        bad += not ok
        rows.append(f"| {ref} | {c['value']} | " + ", ".join(f"{k}: {v}" for k, v in sorted(got.items())) + f" | {why} | {'OK' if ok else '**CHECK**'} |")
    return bad, rows


def erc_summary(out):
    with open(os.path.join(out, "erc.json"), encoding="utf-8") as f:
        erc = json.load(f)
    counts = defaultdict(int)
    items = []
    for sheet in erc.get("sheets", []):
        for v in sheet.get("violations", []):
            counts[(v["severity"], v["type"])] += 1
            items.append((sheet.get("path", ""), v["severity"], v["type"], v["description"],
                          "; ".join(i.get("description", "") for i in v.get("items", []))))
    return counts, items


def run(pr, out):
    nets, comps = read_netlist(os.path.join(out, "analogue_board.net"))
    counts, erc_items = erc_summary(out)
    n_err = sum(v for (sev, _t), v in counts.items() if sev == "error")
    n_warn = sum(v for (sev, _t), v in counts.items() if sev == "warning")
    net_problems, unnamed, n_nets, n_pins = check_netlist(pr, nets)
    pin_bad, pin_rows = check_pins(pr.project_libs)
    fp_bad, fp_rows = check_footprints(comps, pr.project_libs, nets)
    dec_bad, dec_rows = check_decoupling(comps, nets, pr)
    pol_bad, pol_rows = check_polarity(comps, nets)

    parts = [c for r, c in comps.items() if not r.startswith("#")]
    md = ["# Analogue board Rev A: checkpoint 1 checks", "",
          "Generated by `tools/analogue_board/build.py`. Do not edit by hand.", "",
          "| Check | Result |", "|---|---|",
          f"| KiCad ERC | {n_err} errors, {n_warn} warnings |",
          f"| Netlist against the generator's intent | {len(net_problems)} problems ({n_nets} nets, {n_pins} pins) |",
          f"| IC pins against datasheets | {pin_bad} mismatches in {len(pin_rows)} parts |",
          f"| Footprint pads against symbol pins | {fp_bad} mismatches in {len(fp_rows)} symbol/footprint pairs |",
          f"| Decoupling on every IC power pin | {dec_bad} pins without a capacitor, of {len(dec_rows)} |",
          f"| Diode orientation | {pol_bad} to check, of {len(pol_rows)} |",
          f"| Components | {len(parts)} |", ""]
    md += ["## ERC", ""]
    if erc_items:
        md += ["| Sheet | Severity | Type | Description | Items |", "|---|---|---|---|---|"]
        md += [f"| {a} | {b} | {c} | {d} | {e} |" for a, b, c, d, e in erc_items]
    else:
        md.append("No violations.")
    md += ["", "## Netlist", ""]
    md += [f"- {p}" for p in net_problems] or ["Every pin KiCad sees is one the generator placed on purpose; every intended net is "
                                                "exactly one KiCad net; no two intended nets touch."]
    if unnamed:
        md += ["", f"Nets drawn without a label (KiCad names them `Net-(…)`): {', '.join(sorted(unnamed))}."]
    md += ["", "## IC pins against datasheets", "",
           "Library pin numbers and names compared with `datasheet_pins.json` (transcribed from each datasheet; sources in "
           "`datasheet_pins_README.md`). Renames are pins whose datasheet and library spellings differ but mean the same pin.", "",
           "| Part | Library symbol | Datasheet entry | Pins | Result | Notes |", "|---|---|---|---|---|---|"] + pin_rows
    md += ["", "## Footprint pads", "", "| Symbol | Footprint | Result |", "|---|---|---|"] + fp_rows
    md += ["", "## Decoupling", "", "| Ref | Part | Pin | Net | Capacitors |", "|---|---|---|---|---|"] + dec_rows
    md += ["", "## Diode orientation", "", "| Ref | Part | Pin: net | Rule | Result |", "|---|---|---|---|---|"] + pol_rows
    with open(os.path.join(out, "checks.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")
    print("\n".join(md[:14]))
    for p in net_problems[:40]:
        print("NET:", p)
    for r in pin_rows:
        if "MISMATCH" in r:
            print("PIN:", r)
    for r in fp_rows:
        if "MISMATCH" in r:
            print("FP:", r)
    for r in dec_rows:
        if "**none**" in r:
            print("DEC:", r)
    for r in pol_rows:
        if "CHECK" in r:
            print("POL:", r)
    return not (n_err or net_problems or pin_bad or fp_bad or dec_bad or pol_bad)

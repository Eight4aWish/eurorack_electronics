"""Analogue board Rev A: the whole schematic, generated, for one of the two boards (variant.py).

Run `python3 tools/analogue_board/build.py [pico|teensy]` (not this file directly) to regenerate
the KiCad project, run ERC, export the PDF and netlist, and run the checks.
"""

import os

import variant
from blocks import NC, C, R, decap, decaps, holes, ic, part, tp
from make_library import teensy41_pins
from parts import ICS
from schematic import Project

variant.require()
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = variant.DIR
PICO, TEENSY = variant.HAS_PICO, variant.HAS_TEENSY

POWER = {"+12V": "power:+12V", "-12V": "power:-12V", "GND": "power:GND", "+5VD": "power:+5VD",
         "+5VA": "power:+5VA", "+3V3A": "power:+3.3VA", "+3V3D": "power:+3V3", "MOD_5V": "power:+5V"}

# Module pin map. One row per module-facing net: function, Pico 2 pin (GPIO), Teensy 4.1 pin, why.
# Pico: SPI0/SPI1/I2C1/UART0 per the RP2350 GPIO function table; I2S runs on PIO (BCK, LRCK on
# consecutive pins for side-set), MCLK from CLK_GPOUT0. Teensy: fixed peripheral pins from the
# PJRC card (SPI, SPI1, SAI1, Wire, Serial1, Serial4).
PINMAP = [
    ("MCLK", "I2S master clock to SCKI1/2", 27, "GP21", "23", "Pico CLK_GPOUT0 · Teensy MCLK1"),
    ("BCK", "I2S bit clock", 31, "GP26", "21", "Pico PIO side-set · Teensy BCLK1"),
    ("LRCK", "I2S word clock", 32, "GP27", "20", "Pico PIO side-set +1 · Teensy LRCLK1"),
    ("I2S_DOUT", "I2S data to codec DIN", 34, "GP28", "7", "Teensy OUT1A"),
    ("I2S_DIN", "I2S data from codec DOUT", 29, "GP22", "8", "Teensy IN1"),
    ("SPIA_SCK", "Converter bus clock", 24, "GP18", "13", "Pico SPI0 SCK · Teensy SCK"),
    ("SPIA_MOSI", "Converter bus data out", 25, "GP19", "11", "Pico SPI0 TX · Teensy MOSI"),
    ("SPIA_MISO", "Converter bus data in (ADS8688)", 21, "GP16", "12", "Pico SPI0 RX · Teensy MISO"),
    ("CS_ADC", "ADS8688 chip select", 22, "GP17", "10", "Pico SPI0 CSn · Teensy CS"),
    ("CS_DAC", "DAC8568 SYNC", 26, "GP20", "9", ""),
    ("SPIB_SCK", "Panel bus clock", 14, "GP10", "27", "Pico SPI1 SCK · Teensy SCK1"),
    ("SPIB_MOSI", "Panel bus data out", 15, "GP11", "26", "Pico SPI1 TX · Teensy MOSI1"),
    ("SPIB_MISO", "Panel bus data in (MCP3208)", 16, "GP12", "39", "Pico SPI1 RX · Teensy MISO1 (alt pin)"),
    ("CS_595", "74HCT595 latch (RCLK)", 17, "GP13", "38", ""),
    ("CS_POT", "MCP3208 chip select", 19, "GP14", "37", ""),
    ("SDA", "I2C data", 4, "GP2", "18", "Pico I2C1 SDA · Teensy SDA (Wire)"),
    ("SCL", "I2C clock", 5, "GP3", "19", "Pico I2C1 SCL · Teensy SCL (Wire)"),
    ("EXP_INT", "TCA9555 interrupt, active low", 6, "GP4", "22", ""),
    ("GATE_IN1", "Gate input 1", 9, "GP6", "2", ""),
    ("GATE_IN2", "Gate input 2", 10, "GP7", "3", ""),
    ("GATE_IN3", "Gate input 3", 11, "GP8", "4", ""),
    ("GATE_IN4", "Gate input 4", 12, "GP9", "5", ""),
    ("LED_DATA", "WS2812 data (buffered to 5 V)", 7, "GP5", "17", "Teensy TX4 (WS2812Serial)"),
    ("SPARE1", "Spare GPIO 1, or MIDI out (link hole)", 1, "GP0", "1", "Pico UART0 TX · Teensy TX1"),
    ("SPARE2", "Spare GPIO 2, or MIDI in (link hole)", 2, "GP1", "0", "Pico UART0 RX · Teensy RX1"),
]
# Rev B, the Pico 2 / ESP32-P4 board alone (docs/analogue_board_revb.md §1, §3; David, 2026-10-25).
# Pins 16 and 17 are the ESP32-P4's own I2C (its camera, display and ES8311 codec): they go to two
# holes and nothing else, on every board. CS_595 takes pin 20, free since jack detect went. The
# pots ADC keeps the panel bus (spec §6.1: the converter bus is the CV converters' alone), so its
# data line moves to GP8, the Pico's other SPI1 RX pin: EXP_INT is dropped (the firmware polls the
# TCA9555) and gate input 3 takes its pin. SPIA_MISO and CS_DAC swap, so that pins 21, 22 and 24,
# on the ESP32-P4's programmable VDD_IO_5 bank, carry only signals the module drives.
_REVB_PINS = {"GATE_IN3": (6, "GP4", ""), "SPIB_MISO": (11, "GP8", "Pico SPI1 RX"), "CS_595": (20, "GP15", ""),
              "CS_DAC": (21, "GP16", ""), "SPIA_MISO": (26, "GP20", "Pico SPI0 RX")}
PINMAP_REVB = [(net, func, *_REVB_PINS[net][:2], tl, _REVB_PINS[net][2]) if net in _REVB_PINS else (net, func, pin, gp, tl, note)
               for net, func, pin, gp, tl, note in PINMAP if net != "EXP_INT"] + [
    ("P4_SCL", "ESP32-P4's own I2C clock: hole J102 only", 16, "GP12", "", "Pico reserved: ESP32-P4 GPIO8"),
    ("P4_SDA", "ESP32-P4's own I2C data: hole J102 only", 17, "GP13", "", "Pico reserved: ESP32-P4 GPIO7"),
]
if variant.REV == "B":
    PINMAP = PINMAP_REVB
MODULE_NETS = [r[0] for r in PINMAP]

INTERSHEET = (set(MODULE_NETS) | {f"CVDRV{i}" for i in range(1, 7)} | {f"SW_EN{i}" for i in range(1, 7)}
              | {"GATE_OE_N", "PICO_VBUS", "CVO7", "CVO8", "MIDI_TX", "MIDI_RX"})


def new_project():
    pr = Project(variant.NAME, {"analogue_board": os.path.join(variant.SHARED, "analogue_board.kicad_sym")},
                 date="2026-10-16" if variant.REV == "A" else "2026-10-26", rev=variant.REV, company="Eight4aWish · CC BY-SA 4.0",
                 comments=[f"Analogue board for {variant.TITLE}. Spec: docs/analogue_board_spec.md",
                           f"Generated by tools/analogue_board/build.py {variant.BOARD}: edit the generator, not these files"])
    pr.power_nets = dict(POWER)
    pr.ground_nets = {"GND"}
    pr.global_nets = set(INTERSHEET)
    return pr


# =====================================================================================  1  root
def note_for(note):
    """This board's part of a pin-map note ("Pico SPI0 SCK · Teensy SCK" -> "SPI0 SCK" on the Pico
    board); the shared board keeps the whole note."""
    if PICO and TEENSY:
        return note
    who = "Pico" if PICO else "Teensy"
    return " · ".join(p[len(who) + 1:] for p in note.split(" · ") if p.startswith(who + " "))


def J101_NETS():
    """Spare GPIO and MIDI links (without TRS MIDI, the spare pins alone); the Pico (and ESP32-P4)
    also brings its RUN (reset) pin out."""
    spares = ["SPARE1", "MIDI_TX", "SPARE2", "MIDI_RX"] if variant.has("midi") else ["SPARE1", "SPARE2"]
    return spares + (["RUN"] if PICO else []) + ["GND"]


# On the shared board the two sockets interleave (checkpoint 2's arrangement A). There the Teensy's
# far-end pins 20-28, unused, have no holes and it takes shortened headers (pins 1-19 and 29-48),
# unless the board asks for full-length ones (variant.TEENSY_FULL)
TEENSY_FP = f"analogue_board:{'Teensy41_Socket' if variant.TEENSY_FULL else 'Teensy41_Socket_Short'}"


def sheet_root(pr):
    both = PICO and TEENSY
    sh = pr.add_root("Compute modules and pin map" if both else "Compute module and pin map")
    sh.text(f"ANALOGUE BOARD REV {variant.REV} FOR {variant.TITLE.upper()} — COMPUTE MODULE{'S' if both else ''} AND PIN MAP",
            (20, 18), size=2.5, bold=True)
    lines = (["Both footprints sit on the one board, wired to the same nets; only one module is fitted."] if both else []) + [
        "Every signal into the module is 3.3 V.",
        "The module's own 3.3 V output is not used: the board makes its own +3V3A and +3V3D."]
    if PICO:
        lines += ["Pico 2: 5 V reaches VSYS through D203 (Schottky, net MOD_5V), VBUS is left to USB.",
                  "ESP32-P4-WIFI6 (Pico pinout): firmware must set LDO channel 4 to 3.3 V first (pins 21, 22, 24 are on that "
                  "bank); bridge JP201 for its supply margin. See docs/analogue_board_esp32p4.md."]
        nets = {}
        for net, _f, pin, _g, _t, _n in PINMAP:
            nets[pin] = net
        for n in (3, 8, 13, 18, 23, 28, 33, 38):
            nets[n] = "GND"
        nets.update({30: "RUN", 39: "MOD_5V", 40: "PICO_VBUS"})
        for n in range(1, 41):
            nets.setdefault(n, NC)   # ADC_VREF, 3V3_OUT, 3V3_EN and the pin jack detect used (GP15)
        ic(sh, "PICO2", (75, 110), nets, ref=variant.REF["pico"], stubs={30: 12.7})  # RUN label clear of BCK
    if TEENSY:
        lines += ["Teensy 4.1 (not 5 V tolerant): cut the VIN–VUSB pads before fitting; VIN takes MOD_5V.",
                  "Shortened headers on pins 1-19 and 29-48: pins 20-28 have no holes on this board."
                  if not variant.TEENSY_FULL else
                  "Every pin has its hole, so standard full-length headers fit; the ones this board does not use are left open."]
        tpins = teensy41_pins()
        by_label = {lab: n for n, lab in tpins.items() if lab.isdigit()}
        nets = {}
        for net, _f, _p, _g, tlabel, _n in PINMAP:
            nets[by_label[tlabel]] = net
        for n, lab in tpins.items():
            if n not in nets:
                nets[n] = "GND" if lab == "GND" else "MOD_5V" if lab == "VIN" else NC   # 3V3 outputs, unused GPIO
        ic(sh, "TEENSY41", (185 if both else 90, 115), nets, ref=variant.REF["teensy"], p=dict(ICS["TEENSY41"], fp=TEENSY_FP))
    sh.text("\n".join(lines), (20, 24), size=1.6)

    j101 = J101_NETS()
    midi = variant.has("midi")
    holes(sh, (75, 170.18), j101, "Spare GPIO" + (", MIDI links" if midi else "") + (", RUN" if PICO else ""), ref="J101",
          stubs={j101.index("RUN") + 1: 15.24} if PICO else None)
    sh.text(("MIDI: bridge SPARE1-MIDI_TX and SPARE2-MIDI_RX (adjacent holes)\nwith a wire or shunt. Left open, SPARE1/2 are plain GPIO.\n"
             if midi else "SPARE1/2: plain GPIO (UART0 TX/RX on a Pico, Serial1 on a Teensy).\n")
            + ("On a Pico, move the SDK console off UART0 to USB.\nRUN: wire a reset button to GND (Pico or ESP32-P4)." if PICO
               else "On a Teensy they are Serial1 (TX1, RX1)."), (85, 162), size=1.27)
    if variant.REV == "B":
        holes(sh, (75, 200.66), ["P4_SCL", "P4_SDA"], "ESP32-P4 own I2C", ref="J102")
        sh.text("J102: the ESP32-P4's own I2C bus (its camera, display and ES8311 codec;\n2.2 kΩ pull-ups on the "
                "module). Reserved on every board: nothing else may use\npins 16 and 17. An extra I2C part can join that bus here.",
                (85, 196), size=1.27)

    # pin map table
    cols = (["Pico 2"] if PICO else []) + (["Teensy 4.1"] if TEENSY else [])
    rows = [["Net", "Function", *cols, "Why this pin"]]
    for net, func, pin, gpio, tl, note in PINMAP:
        rows.append([net, func, *([f"{gpio} (pin {pin})"] if PICO else []), *([f"D{tl}"] if TEENSY else []), note_for(note)])
    rows.append(["MOD_5V", "Module 5 V in", *(["VSYS (pin 39)"] if PICO else []), *(["VIN"] if TEENSY else []),
                 "Schottky D203" + ("; Q201 bypass if JP201" if PICO else "")])
    if PICO:
        rows.append(["PICO_VBUS", "Module USB 5 V sense", "VBUS (pin 40)", *(["—"] if TEENSY else []), "Q201 gate: off with USB plugged in"])
        rows.append(["RUN", "Module reset", "RUN (pin 30)", *(["—"] if TEENSY else []), "To hole J101-5"])
    sh.text("PIN MAP", (238, 18), size=2.0, bold=True)
    sh.table((238, 22), [22, 50, 25, 17, 52] if both else [22, 50, 25, 69], rows, row_h=5.08)

    # sub-sheets
    sheets = [
        ("Power", "power.kicad_sch", "Power entry, buck, linear rails, test points"),
        ("Codec & audio", "codec_audio.kicad_sch", "PCM3060, two audio ins, two audio outs"),
        ("CV jacks & ADC", "cv_io.kicad_sch", "ADS8688, DG412 jack switches, CV holes"),
        ("CV DAC", "cv_dac.kicad_sch", "DAC8568 and the eight ±5 V output stages"),
        ("Pots & gate outs", "pots_gates.kicad_sch", "MCP3208 pots, 74HCT595 gate outputs"),
        ("Expander, I2C & LEDs", "expander_i2c.kicad_sch", "TCA9555 buttons, EEPROM, Qwiic, WS2812"),
        ("Gate ins", "gate_in.kicad_sch", "LM393 gate inputs"),
        ("Edge strips", "edge_strips.kicad_sch", "n8synth edge strips, fiducials"),
        ("TRS MIDI", "midi.kicad_sch", "MIDI in (H11L1) and out (5 V buffered), Type A"),
    ][:None if variant.has("midi") else -1]   # the last sheet, TRS MIDI, only on boards that have it
    subs = []
    for i, (name, fn, desc) in enumerate(sheets):
        x = 20 + (i % 5) * 62
        y = 214 + (i // 5) * 30
        subs.append(pr.add_sheet(name, fn, name, at=(x, y), size=(50.8, 15.24)))
        sh.text(desc, (x + 1.27, y + 2.54), size=1.27)
    sh.text("SHEETS", (20, 208), size=2.0, bold=True)
    return subs


# =====================================================================================  2  power
def chain_h(sh, start, parts_pins, end=None):
    """Wire a horizontal chain: start point -> (part, in_pin, out_pin) ... -> end point."""
    cur = start
    for pl, pin_in, pin_out in parts_pins:
        sh.wire(cur, pl.p(pin_in))
        cur = pl.p(pin_out)
    if end:
        sh.wire(cur, end)
    return cur


def rail_out(sh, start, link_size, net, regnet, tp_ref, caps, decouples, label=True):
    """From a regulator output point: output caps, the 0 R rail link, the rail symbol, PWR_FLAG and test pad.
    caps: [(value, size)], drawn 12.7 mm apart along the regulator-side net."""
    x, y = start
    if label:
        sh.label(regnet, (x + 2.54, y), 0)
    pts = []
    for i, (v, sz) in enumerate(caps):
        c = C(sh, v, (x + 15.24 + i * 12.7, y + 2.54), size=sz, decouples=decouples)
        sh.connect(c, 2, "GND", stub=0)
        pts.append((c, "1"))
    lx = x + 15.24 + len(caps) * 12.7 + 2.54
    lk = R(sh, "0R", (lx, y), rot=90, size=link_size, fields={"Note": f"rail link: lift to isolate {net}"})
    sh.wire((x, y), lk.p("1"))
    sh.tie(regnet, *pts, (lk, "1"))
    o = (lk.p("2")[0] + 10.16, y)
    sh.wire(lk.p("2"), o)
    sh.power(net, o)
    sh.pwr_flag((lk.p("2")[0] + 5.08, y))
    sh.tie(net, (lk, "2"))
    tp(sh, (o[0] + 7.62, y - 5.08), net, ref=tp_ref)
    return o


def sheet_power(sh):
    sh.text("POWER", (20, 18), size=2.5, bold=True)
    sh.text("±12 V enter through a 2×5 shrouded header (the bus +5 V is not used). Each rail: series Schottky, ferrite,\n"
            "10 µF + 100 nF. +5VD comes from a forced-PWM buck (no light-load pulse skipping in the audio band);\n"
            "+5VA from a linear regulator on its own; each 3.3 V rail from its own LDO. A 0 Ω link after every\n"
            "regulator lets a faulty rail be isolated and its current measured.", (20, 23), size=1.5)

    # ---- entry
    sh.text("Eurorack power entry (pin 1 = -12 V, red stripe)", (20, 44), size=1.5, bold=True)
    j = part(sh, "EURO_PWR", (40.64, 71.12), ref="J201")
    for n in (1, 2):
        sh.connect(j, n, "-12V_IN")
    for n in (9, 10):
        sh.connect(j, n, "+12V_IN")
    for side, pins in (("odd", (3, 5, 7)), ("even", (4, 6, 8))):
        xs = [j.p(str(n))[0] for n in pins]
        dx = -2.54 if side == "odd" else 2.54
        bx = xs[0] + dx
        for n in pins:
            p = j.p(str(n))
            sh.wire(p, (bx, p[1]))
        top, bot = j.p(str(pins[0]))[1], j.p(str(pins[-1]))[1]
        mid = j.p(str(pins[1]))[1]
        sh.wire((bx, top), (bx, bot))
        sh.wire((bx, mid), (bx + 2 * dx, mid))
        sh.power("GND", (bx + 2 * dx, mid), "left" if dx < 0 else "right")
        sh.tie("GND", *[(j, str(n)) for n in pins])

    for net, y, d_rot, din, dout in (("+12V", 55.88, 180, "2", "1"), ("-12V", 86.36, 0, "1", "2")):
        x0 = 76.2
        sh.label(f"{net}_IN", (x0, y), 180)
        d = part(sh, "SS34", (x0 + 10.16, y), rot=d_rot, ref="D201" if net == "+12V" else "D202")
        fb = part(sh, "FERRITE", (x0 + 30.48, y), rot=90, ref="FB201" if net == "+12V" else "FB202", value="BLM18PG121")
        node = (x0 + 43.18, y)
        chain_h(sh, (x0, y), [(d, din, dout), (fb, "1", "2")], node)
        sh.label(f"{net}_P", (x0 + 17.78, y), 0)
        sh.wire(node, (x0 + 76.2, y))
        sh.power(net, node)
        sh.pwr_flag((x0 + 50.8, y))
        sh.tie(f"{net}_IN", (d, din))
        sh.tie(f"{net}_P", (d, dout), (fb, "1"))
        sh.tie(net, (fb, "2"))
        for i, (v, sz) in enumerate([("10u", "1206"), ("100n", "0603")]):
            c = C(sh, v, (x0 + 63.5 + i * 12.7, y + 2.54), size=sz, decouples=f"rail entry {net}")
            sh.connect(c, 2, "GND", stub=0)
            sh.tie(net, (c, "1"))
        tp(sh, (x0 + 88.9, y - 5.08), net, ref="TP201" if net == "+12V" else "TP202")
    sh.text("SS34 per rail: reverse-polarity protection. A reversed ribbon blocks on both rails.\n"
            "3 A parts: +12 V can reach ≈0.75 A with an ESP32-P4 and a lit LED chain.", (76.2, 96), size=1.27)
    sh.power("GND", (190.5, 66.04))
    sh.pwr_flag((190.5, 66.04))
    tp(sh, (200.66, 63.5), "GND", ref="TP203")
    tp(sh, (210.82, 63.5), "GND", ref="TP204")
    sh.text("GND test pads", (195, 52), size=1.27)

    # ---- +5VD buck
    bx, by = 81.28, 135.89
    sh.text("+5VD: TPS54308 forced-PWM buck, 350 kHz (TPS54202 is a pin- and value-compatible fallback)", (20, 108), size=1.5, bold=True)
    sh.text("Vout = 0.596 V × (1 + 15k/2k) = 5.07 V; L and Cout from TI's table for 5 V. Input: own ferrite and 2 × 10 µF, keeping the\n"
            "350 kHz input ripple off the ±12 V rail the op-amps share. EN divider 510k/75k: starts at ≈9.2 V, stops at ≈8.1 V,\n"
            "so the digital 5 V never runs while the analogue 5 V (L78M05) is down: TI's power-up order for the codec.",
            (20, 112.5), size=1.27)
    u = part(sh, "TPS54308", (bx, by), ref="U201")
    sh.connect(u, "1", "GND")
    sh.connect(u, "5", "BUCK_EN")
    vin = u.p("3")
    fbin = part(sh, "FERRITE", (vin[0] - 17.78, vin[1]), rot=90, ref="FB203", value="BLM18PG121")
    sh.wire(vin, fbin.p("2"))
    sh.wire(fbin.p("1"), (fbin.p("1")[0] - 5.08, vin[1]))
    sh.power("+12V", (fbin.p("1")[0] - 5.08, vin[1]))
    sh.label("BUCK_VIN", (vin[0] - 5.08, vin[1]), 90)
    sh.tie("+12V", (fbin, "1"))
    sh.tie("BUCK_VIN", (fbin, "2"), (u, "3"))
    for i, (v, sz) in enumerate([("10u", "1206"), ("10u", "1206"), ("100n", "0603")]):
        c = C(sh, v, (20.32 + i * 12.7, 160.02), size=sz, decouples="U201 VIN pin 3")
        if i == 0:
            sh.flagged_stub(c, 1, "BUCK_VIN")
        else:
            sh.connect(c, 1, "BUCK_VIN")
        sh.connect(c, 2, "GND", stub=0)
    r = R(sh, "510k", (60.96, 160.02), size="0603", fields={"Note": "EN divider (UVLO), top"})
    sh.connect(r, 1, "BUCK_VIN")
    sh.connect(r, 2, "BUCK_EN")
    r = R(sh, "75k", (71.12, 160.02), size="0603", fields={"Note": "EN divider (UVLO), bottom"})
    sh.connect(r, 1, "BUCK_EN")
    sh.connect(r, 2, "GND", stub=0)
    boot, sw, fb = u.p("6"), u.p("2"), u.p("4")
    cb = C(sh, "100n", (boot[0] + 10.16, boot[1] - 2.54), size="0402", fields={"Note": "bootstrap"})
    sh.wire(boot, (boot[0] + 2.54, boot[1]), (boot[0] + 2.54, cb.p("1")[1]), cb.p("1"))
    sh.wire(cb.p("2"), (cb.p("2")[0], sw[1]))
    sh.tie("BOOT", (u, "6"), (cb, "1"))
    l1 = part(sh, "L_BUCK", (sw[0] + 22.86, sw[1]), rot=90, ref="L201")
    sh.wire(sw, l1.p("1"))
    sh.tie("SW", (u, "2"), (cb, "2"), (l1, "1"))
    vb = (l1.p("2")[0] + 2.54, sw[1])
    # divider: Rtop from 5V_BUCK to the FB node, Rbot to ground. Optional feed-forward (not fitted): 470 pF + 2 kΩ across Rtop
    rt = R(sh, "15k", (vb[0] + 7.62, vb[1] + 5.08))
    rb = R(sh, "2k", (vb[0] + 7.62, vb[1] + 17.78))
    cff = C(sh, "470p", (vb[0] + 17.78, vb[1] + 5.08), dnp=True, lcsc=False,
            fields={"Note": "feed-forward, fit only if the loop needs phase boost (TI table: ~75 pF × 100k/15k, 2 kΩ in series)"})
    rff = R(sh, "2k", (vb[0] + 17.78, vb[1] + 10.16), dnp=True, fields={"Note": "feed-forward series resistor, fit with the capacitor"})
    fbn_y = vb[1] + 12.7
    sh.wire((rt.p("1")[0], vb[1]), rt.p("1"))
    sh.wire((cff.p("1")[0], vb[1]), cff.p("1"))
    sh.wire(rt.p("2"), (rt.p("2")[0], fbn_y), rb.p("1"))
    sh.wire(fb, (fb[0] + 2.54, fb[1]), (fb[0] + 2.54, fbn_y), (rff.p("2")[0], fbn_y), rff.p("2"))
    sh.connect(rb, "2", "GND", stub=0)
    sh.tie("5V_BUCK", (l1, "2"), (rt, "1"), (cff, "1"))
    sh.tie("FB", (u, "4"), (rt, "2"), (rb, "1"), (rff, "2"))
    sh.tie("FF", (cff, "2"), (rff, "1"))
    sh.wire(l1.p("2"), (vb[0] + 27.94, vb[1]))
    o = rail_out(sh, (vb[0] + 27.94, vb[1]), "0805", "+5VD", "5V_BUCK", "TP205",
                 [("22u", "1206"), ("22u", "1206"), ("100n", "0402")], "buck output", label=False)
    sh.label("5V_BUCK", (vb[0] + 2.54, vb[1]), 0)
    decaps(sh, o[0] + 17.78, vb[1] + 5.08, "+5VD", [("10u", "0805")], "+5VD distribution")

    # ---- +5VA linear
    lx, ly = 66.04, 210.82
    sh.text("+5VA: L78M05 from +12 V, its own regulator (PCM3060 VCC, ADS8688 AVDD, +3V3A LDO)", (20, 188), size=1.5, bold=True)
    u = part(sh, "L78M05", (lx, ly), ref="U202")
    sh.connect(u, "2", "GND")
    vi, vo = u.p("1"), u.p("3")
    sh.wire(vi, (vi[0] - 10.16, vi[1]))
    sh.power("+12V", (vi[0] - 10.16, vi[1]))
    sh.tie("+12V", (u, "1"))
    decaps(sh, 20.32, ly + 7.62, "+12V", [("1u", "0603"), ("100n", "0603")], "U202 VI pin 1")
    sh.tie("5VA_REG", (u, "3"))
    rail_out(sh, vo, "0603", "+5VA", "5VA_REG", "TP206", [("10u", "0805"), ("100n", "0402")], "U202 output")

    # ---- 3.3 V LDOs
    def ldo(x, y, vin, regnet, out, title, ref_tp):
        sh.text(title, (x - 35.56, y - 17.78), size=1.5, bold=True)
        u = part(sh, "XC6206", (x, y))
        sh.connect(u, "1", "GND")
        vi, vo = u.p("3"), u.p("2")
        sh.wire(vi, (vi[0] - 10.16, vi[1]))
        sh.power(vin, (vi[0] - 10.16, vi[1]))
        sh.tie(vin, (u, "3"))
        decaps(sh, x - 30.48, y + 7.62, vin, [("1u", "0402")], f"{u.ref} VI pin 3")
        sh.tie(regnet, (u, "2"))
        o = rail_out(sh, vo, "0603", out, regnet, ref_tp, [("10u", "0805")], f"{u.ref} output (ceramic-stable LDO)")
        return u, o

    ldo(266.7, 66.04, "+5VA", "3V3A_REG", "+3V3A", "+3V3A: XC6206 from +5VA (DAC8568, MCP3208, pot reference via POT_REF)", "TP207")
    _, o = ldo(266.7, 111.76, "+5VD", "3V3D_REG", "+3V3D", "+3V3D: XC6206 from +5VD (codec VDD, ADS8688 DVDD, logic, Qwiic, MIDI)", "TP208")
    r = R(sh, "680R", (o[0] + 17.78, 116.84), size="0603",
          fields={"Note": "minimum load: absorbs gate-input clamp current, which the LDO cannot sink"})
    sh.connect(r, 1, "+3V3D", stub=2.54)
    sh.connect(r, 2, "GND", stub=0)
    sh.text("680 Ω minimum load: four 12 V gates push ≈3.4 mA\ninto +3V3D through their clamps; the\nXC6206 cannot sink it (4.85 mA here).",
            (o[0] + 22.86, 121.92), size=1.27)

    # ---- module supply
    mx, my = 256.54, 185.42
    if PICO:
        sh.text("MOD_5V: +5VD through a Schottky to Pico VSYS / ESP32-P4 VCC_5V" + (" / Teensy VIN" if TEENSY else ""),
                (231.14, 154.94), size=1.5, bold=True)
        sh.text("Q201 bypasses D203 when JP201 is bridged, for the ESP32-P4, whose regulator needs ≥ 4.5 V at 0.5-0.7 A.\n"
                "Its gate follows the Pico/P4 VBUS pin (pin 40): with USB plugged in the FET turns off, as in the Pico 2\n"
                "datasheet's VSYS circuit. Leave JP201 open for a Pico 2" + (" or a Teensy." if TEENSY else "."),
                (231.14, 159.2), size=1.27)
    else:
        sh.text("MOD_5V: +5VD through a Schottky to Teensy VIN", (231.14, 154.94), size=1.5, bold=True)
        sh.text("Cut the Teensy's VIN-VUSB pads, so USB never back-feeds the buck and the buck never reaches USB.",
                (231.14, 159.2), size=1.27)
    sh.power("+5VD", (mx - 7.62, my))
    d = part(sh, "SS34", (mx + 5.08, my), rot=180, ref="D203")
    sh.wire((mx - 7.62, my), d.p("2"))
    sh.tie("+5VD", (d, "2"))
    o = (d.p("1")[0] + 15.24, my)
    sh.wire(d.p("1"), o)
    sh.power("MOD_5V", o)
    sh.pwr_flag((d.p("1")[0] + 7.62, my))
    sh.tie("MOD_5V", (d, "1"))
    supply = ([f"{variant.REF['pico']} VSYS pin 39"] if PICO else []) + ([f"{variant.REF['teensy']} VIN pin 48"] if TEENSY else [])
    decaps(sh, o[0] + 12.7, my + 5.08, "MOD_5V", [("10u", "0805")], "module supply: " + ", ".join(supply))
    tp(sh, (o[0] + 25.4, my - 5.08), "MOD_5V", ref="TP209")
    if PICO:
        p4_bypass(sh, mx, my)
    sh.text("Load estimate: +12 V ≈ 120 mA typical; " + (
        "with an ESP32-P4 (0.45-0.7 A at 5 V) plus a lit LED chain, ≈0.75 A.\n" if PICO else
        "~350 mA worst case with the Teensy and a lit LED chain.\n") +
        "-12 V ≈ 25 mA. XC6206: 200 mA each; +3V3D ≈ 50 mA.", (231.14, 233.68), size=1.27)


def p4_bypass(sh, mx, my):
    """Pico board only: Q201 bypasses D203 for the ESP32-P4 when JP201 is bridged."""
    q = part(sh, "AO3401A", (mx + 5.08, my + 20.32), ref="Q201")
    sh.connect(q, "3", "+5VD")
    sh.connect(q, "2", "MOD_5V")
    sh.connect(q, "1", "PICO_VBUS", kind="global")
    # gate network on one row: PICO_VBUS node (1M up to MOD_5V) - JP201 - FET_EN node (100k down to GND)
    gy = my + 27.94
    nv, nf = (mx + 33.02, gy), (mx + 55.88, gy)
    r = R(sh, "1M", (nv[0], gy - 5.08), fields={"Note": "holds Q201 off while JP201 is open"})
    sh.connect(r, 1, "MOD_5V", stub=0)
    sh.wire(r.p("2"), nv)
    sh.wire((nv[0] - 5.08, gy), nv)
    sh.label("PICO_VBUS", (nv[0] - 5.08, gy), 180, kind="global")
    jp = part(sh, "SJ_OPEN", (mx + 44.45, gy), ref="JP201", value="ESP32-P4: bridge")
    sh.wire(nv, jp.p("1"))
    sh.wire(jp.p("2"), nf)
    sh.label("FET_EN", nf, 0)
    r2 = R(sh, "100k", (nf[0], gy + 5.08))
    sh.wire(nf, r2.p("1"))
    sh.connect(r2, 2, "GND", stub=0)
    sh.tie("PICO_VBUS", (r, "2"), (jp, "1"))
    sh.tie("FET_EN", (jp, "2"), (r2, "1"))

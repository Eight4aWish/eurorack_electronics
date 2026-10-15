"""Sheets 6-9: pots and gate outputs, expander/I2C/LEDs, gate inputs and jack detect, edge strips."""

import wiring
from blocks import NC, C, R, decap, decaps, holes, ic, part, tp
from design_analog import clamp_below


def AHCT_TEXT(x, y):
    """74AHCT1G125 reference and value up and to the right, clear of the pin names and of pin 1 (OE)."""
    return {"ref_at": (x + 2.54, y - 7.62), "value_at": (x + 2.54, y - 5.08)}


# =====================================================================================  6  pots, gate outs
def sheet_pots_gates(sh):
    sh.text("POTS AND GATE OUTPUTS", (20, 18), size=2.5, bold=True)
    sh.text("Pots: MCP3208 on +3V3A. Its VREF and the pot tops share POT_REF (100 Ω + 10 µF from +3V3A), so readings are\n"
            "ratiometric and the hand-wired pot leads can't disturb the DAC's supply. Each wiper: 1 kΩ + 100 nF, 1 MΩ to\n"
            "ground so an unwired channel reads 0 (100 kΩ would bend a 100 kΩ pot's response by up to 12 %).\n"
            "Gate outs: 74HCT595 at 5 V (VIH 2.0 V, so 3.3 V logic drives it) → 1 kΩ → jack, BAV99 clamps to +5VD and GND.\n"
            "OE is held high (outputs off) by a pull-up until firmware drives GATE_OE_N low: the 595's register powers up random.",
            (20, 23), size=1.5)
    ic(sh, "MCP3208", (55.88, 83.82), {1: "POT_IN1", 2: "POT_IN2", 3: "POT_IN3", 4: "POT_IN4", 5: "POT_IN5",
                                        6: "POT_IN6", 7: "POT_IN7", 8: "POT_IN8", 13: "SPIB_SCK", 12: "SPIB_MISO",
                                        11: "SPIB_MOSI", 10: "CS_POT", 15: "POT_REF", 16: "+3V3A", 14: "GND", 9: "GND"},
       ref="U601")
    decaps(sh, 30.48, 116.84, "+3V3A", [("1u", "0402"), ("100n", "0402")], "U601 VDD pin 16")
    for i, (v, sz) in enumerate([("10u", "0805"), ("100n", "0402")]):
        c = C(sh, v, (60.96 + i * 12.7, 124.46), size=sz, decouples="U601 VREF pin 15 (POT_REF)")
        if i == 0:
            sh.flagged_stub(c, 1, "POT_REF")
        else:
            sh.connect(c, 1, "POT_REF")
        sh.connect(c, 2, "GND", stub=0)
    r = R(sh, "100R", (40.64, 137.16), rot=90, size="0805", fields={"Note": "isolates the pot reference from the DAC supply"})
    sh.connect(r, 1, "+3V3A")
    sh.connect(r, 2, "POT_REF")
    r = R(sh, "10k", (91.44, 116.84), fields={"Note": "keeps the pot ADC deselected while the module boots"})
    sh.connect(r, 1, "+3V3D", stub=0)
    sh.connect(r, 2, "CS_POT")

    x0, y0 = 104.14, 50.8
    for n in range(1, 9):
        y = y0 + (n - 1) * 12.7
        r = R(sh, "1k", (x0 + 5.08, y), rot=90)
        node = (x0 + 12.7, y)
        c = C(sh, "100n", (node[0], y + 2.54))
        rpd = R(sh, "1M", (x0 + 27.94, y + 2.54))
        sh.wire((x0 - 2.54, y), r.p("1"))
        sh.label(f"POT{n}", (x0 - 2.54, y), 180)
        sh.wire(r.p("2"), node, (x0 + 27.94, y), (x0 + 35.56, y))
        sh.label(f"POT_IN{n}", (x0 + 35.56, y), 0)
        sh.connect(c, "2", "GND", stub=0)
        sh.connect(rpd, "2", "GND", stub=0)
        sh.tie(f"POT{n}", (r, "1"))
        sh.tie(f"POT_IN{n}", (r, "2"), (c, "1"), (rpd, "1"))
    # pot and gate-out holes, spread over the four banks (wiring.py); pot tops to a bank's POT_REF
    # hole, pot bottoms to the deck's D bus
    wiring.place(sh, holes, "pots", (185.42, 50.8), max_y=165)

    # gate outputs
    ic(sh, "74HCT595", (55.88, 190.5), {14: "SPIB_MOSI", 11: "SPIB_SCK", 10: "+5VD", 12: "CS_595", 13: "GATE_OE_N",
                                         15: "GQ1", 1: "GQ2", 2: "GQ3", 3: "GQ4", 4: "GQ5", 5: "GQ6", 6: "GQ7", 7: "GQ8",
                                         9: "GATE_SER_OUT", 16: "+5VD", 8: "GND"}, ref="U602")
    decap(sh, (30.48, 223.52), "100n", "0402", "+5VD", "U602 VCC pin 16")
    r = R(sh, "10k", (25.4, 175.26), fields={"Note": "OE pull-up: gates off until firmware enables"})
    sh.connect(r, 1, "+3V3D", stub=0)
    sh.connect(r, 2, "GATE_OE_N", kind="global")
    r = R(sh, "10k", (15.24, 175.26), fields={"Note": "latch held idle while the module boots or reflashes"})
    sh.connect(r, 1, "+3V3D", stub=0)
    sh.connect(r, 2, "CS_595", kind="global")
    sh.text("SRCLR tied high. Boot order: OE off, clear\nthe register, then enable (firmware).", (20, 238), size=1.27)

    x0, y0 = 220.98, 45.72
    for n in range(1, 9):
        col, row = (n - 1) // 4, (n - 1) % 4
        x, y = x0 + col * 76.2, y0 + row * 25.4
        r = R(sh, "1k", (x + 5.08, y), rot=90)
        node = (x + 15.24, y)
        sh.wire((x - 2.54, y), r.p("1"))
        sh.label(f"GQ{n}", (x - 2.54, y), 180)
        sh.wire(r.p("2"), node, (node[0] + 10.16, y))
        sh.label(f"GOUT{n}", (node[0] + 10.16, y), 0)
        d = clamp_below(sh, "BAV99", node, "+5VD")
        sh.tie(f"GQ{n}", (r, "1"))
        sh.tie(f"GOUT{n}", (r, "2"), (d, "3"))
    holes(sh, (370.84, 160.02), ["GATE_SER_OUT", "SPIB_SCK", "CS_595", "GATE_OE_N", "+5VD", "GND"],
          "Gate expansion: QH', SRCLK, RCLK, OE", ref="J603")
    sh.text("Chain a second 74HCT595 off-board from J603\n(74HCT595 only: a 74HC595 at 5 V needs\n3.15 V inputs). OE keeps it off at boot too.", (330, 180), size=1.27)
    for i, net in enumerate(["SPIB_SCK", "SPIB_MOSI", "SPIB_MISO", "CS_595", "CS_POT"]):
        tp(sh, (226.06 + i * 12.7, 162.56), net)
    sh.text("Panel bus test pads", (221, 150), size=1.27)


# =====================================================================================  7  expander, I2C, LEDs
def sheet_expander(sh):
    sh.text("EXPANDER, I2C AND LEDS", (20, 18), size=2.5, bold=True)
    sh.text("TCA9555 at 0x20, M24C64 at 0x50; a Qwiic display is typically 0x3C/0x3D. 2.2 kΩ I2C pull-ups for 400 kHz.\n"
            "The TCA9555 powers up with every line an input pulled high internally (~100 kΩ): switch enables and the gate\n"
            "OE are defined by the pulls on their own sheets. Buttons and switches use P07 and P10-P17: hole → 1 kΩ → node with\n"
            "10 kΩ to +3V3D and 100 nF (10 nF on SW5-SW8) → expander pin, as EuroPi does. A button pulls its hole to GND.\n"
            "ENCODERS: wire A and B to gate inputs 3 and 4 (a clean comparator into a direct GPIO; encoder common to a +3V3D hole),\n"
            "not to the expander: a busy OLED holds the shared I2C bus for ~23 ms and steps get lost. The push switch can use any SW hole.",
            (20, 23), size=1.5)
    exp = {23: "SDA", 22: "SCL", 1: "EXP_INT", 3: "GND", 2: "GND", 21: "GND",
           4: "SW_EN1", 5: "SW_EN2", 6: "SW_EN3", 7: "SW_EN4", 8: "SW_EN5", 9: "SW_EN6", 10: "GATE_OE_N", 11: "BTN9",
           13: "BTN1", 14: "BTN2", 15: "BTN3", 16: "BTN4", 17: "BTN5", 18: "BTN6", 19: "BTN7", 20: "BTN8",
           24: "+3V3D", 12: "GND"}
    ic(sh, "TCA9555", (68.58, 101.6), exp, ref="U701", stubs={11: 17.78})  # BTN9 label past the GATE_OE_N label
    decap(sh, (45.72, 139.7), "100n", "0402", "+3V3D", "U701 VCC pin 24")
    r = R(sh, "10k", (30.48, 76.2), fields={"Note": "INT is open-drain"})
    sh.connect(r, 1, "+3V3D", stub=0)
    sh.connect(r, 2, "EXP_INT")

    x0, y0 = 147.32, 50.8
    for n in range(1, 10):
        y = y0 + (n - 1) * 16.51
        r = R(sh, "1k", (x0 + 5.08, y), rot=90)
        node = (x0 + 12.7, y)
        rpu = R(sh, "10k", (node[0], y - 5.08))
        c = C(sh, "10n" if 5 <= n <= 8 else "100n", (x0 + 22.86, y + 2.54))
        sh.wire((x0 - 2.54, y), r.p("1"))
        sh.label(f"SW{n}", (x0 - 2.54, y), 180)
        sh.wire(r.p("2"), node, (x0 + 22.86, y), (x0 + 33.02, y))
        sh.wire(node, rpu.p("2"))
        sh.label(f"BTN{n}", (x0 + 33.02, y), 0)
        sh.connect(rpu, "1", "+3V3D", stub=0)
        sh.connect(c, "2", "GND", stub=0)
        sh.tie(f"SW{n}", (r, "1"))
        sh.tie(f"BTN{n}", (r, "2"), (rpu, "2"), (c, "1"))
    wiring.place(sh, holes, "expander", (218.44, 50.8), max_y=150)   # button holes, spread over the four banks
    sh.text("Encoder A/B: use gate inputs\n3-4 (see note above); push\nswitch on any SW hole.", (250, 50.8), size=1.27)

    # EEPROM, pull-ups, Qwiic
    ic(sh, "M24C64", (68.58, 182.88), {1: "GND", 2: "GND", 3: "GND", 4: "GND", 5: "SDA", 6: "SCL", 7: "GND",
                                        8: "+3V3D"}, ref="U702", ref_at=(58.42, 176.53), value_at=(71.12, 176.53))
    sh.text("E0-E2 low: 0x50. WC low: writable.", (45, 163), size=1.27)
    decap(sh, (45.72, 205.74), "100n", "0402", "+3V3D", "U702 VCC pin 8")
    for i, net in enumerate(["SDA", "SCL"]):
        r = R(sh, "2.2k", (101.6 + i * 10.16, 177.8))
        sh.connect(r, 1, "+3V3D", stub=0)
        sh.connect(r, 2, net)
    q = ic(sh, "QWIIC", (137.16, 185.42), {1: "GND", 2: "+3V3D", 3: "SDA", 4: "SCL", "MP": "GND"}, ref="J702")
    sh.text("Qwiic: 1 GND, 2 3.3 V, 3 SDA, 4 SCL", (95.25, 165), size=1.27)
    holes(sh, (190.5, 218.44), ["SDA", "SCL", "+3V3D", "GND"], "I2C holes for a wired display", ref="J703")
    tp(sh, (101.6, 205.74), "SDA")
    tp(sh, (114.3, 205.74), "SCL")
    tp(sh, (127, 205.74), "EXP_INT")

    # WS2812 data
    sh.text("WS2812 data: 3.3 V → 74AHCT1G125 at 5 V → 330 Ω → LED_DIN. LED power from the +5VD holes.", (240, 160), size=1.5, bold=True)
    u = ic(sh, "AHCT1G125", (281.94, 190.5), {2: "LED_DATA", 1: "GND", 4: "LED_BUF", 5: "+5VD", 3: "GND"}, ref="U703",
           stubs={1: 7.62, 4: 5.08}, **AHCT_TEXT(281.94, 190.5))
    decap(sh, (256.54, 213.36), "100n", "0402", "+5VD", "U703 VCC pin 5")
    r = R(sh, "330R", (317.5, 190.5), rot=90)
    sh.wire((u.p("4")[0] + 5.08, 190.5), r.p("1"))  # one LED_BUF label over a continuous wire
    sh.tie("LED_BUF", (r, "1"))
    sh.connect(r, 2, "LED_DIN")
    holes(sh, (350.52, 190.5), ["LED_DIN", "+5VD", "+5VD", "GND", "GND"], "WS2812 chain holes", ref="J704")
    decap(sh, (330.2, 213.36), "47u", "1206", "+5VD", "LED supply at J704")


# =====================================================================================  8  gate ins, probe
def sheet_gate_in(sh):
    sh.text("GATE INPUTS AND JACK DETECT", (20, 18), size=2.5, bold=True)
    sh.text("Adapted from Ogham's clock input (Ogham feeds the comparator's − input; this one is non-inverting, so four channels\n"
            "share one threshold divider): 10 kΩ, BAT54S clamps to +3V3D / GND, 100 kΩ to ground, LM393 against GATE_TH = 1.65 V with\n"
            "100 kΩ hysteresis. Trips at ≈1.98 V rising, ≈1.67 V falling at the jack. The LM393 runs from +12 V so the clamped\n"
            "input (up to ≈3.6 V) stays inside its common-mode range (VCC − 1.5 V; at 5 V that would be 3.5 V). Open-collector\n"
            "output pulled up to +3V3D: GATE_INn is high while the gate is high, safe for any module. Firmware: catch 100 µs\n"
            "triggers with edge interrupts or PIO; mask the inputs while the jack-detect probe runs. The clamps push up to ≈3.4 mA\n"
            "into +3V3D: the 680 Ω minimum load on the power sheet absorbs it.",
            (20, 23), size=1.5)
    units = [("U801", 1, ("3", "2", "1")), ("U801", 2, ("5", "6", "7")), ("U802", 1, ("3", "2", "1")), ("U802", 2, ("5", "6", "7"))]
    for n, (ref, unit, (pp, pm, po)) in enumerate(units, start=1):
        ox, oy = 101.6, 55.88 + (n - 1) * 33.02
        u = part(sh, "LM393", (ox, oy), unit=unit, ref=ref, hide_value=True)
        plus, minus, out = u.p(pp), u.p(pm), u.p(po)
        rin = R(sh, "10k", (ox - 38.1, plus[1]), rot=90)
        cnode = (ox - 30.48, plus[1])
        pnode = (ox - 12.7, plus[1])
        sh.wire((ox - 45.72, plus[1]), rin.p("1"))
        sh.label(f"GIN{n}", (ox - 45.72, plus[1]), 180)
        sh.wire(rin.p("2"), cnode, pnode, plus)
        d = clamp_below(sh, "BAT54S", cnode, "+3V3D", drop=10.16)
        rpd = R(sh, "100k", (ox - 15.24, plus[1] + 5.08))
        sh.wire((ox - 15.24, plus[1]), rpd.p("1"))
        sh.connect(rpd, "2", "GND", stub=0)
        # hysteresis over the top, output pull-up, output label
        rh = R(sh, "100k", (ox, plus[1] - 7.62), rot=90)
        o = (out[0] + 5.08, out[1])
        sh.wire(pnode, (pnode[0], rh.p("1")[1]), rh.p("1"))
        sh.wire(rh.p("2"), (o[0], rh.p("2")[1]), o)
        rpu = R(sh, "10k", (o[0] + 5.08, out[1] - 5.08))
        sh.wire(out, o, (o[0] + 5.08, out[1]), (o[0] + 12.7, out[1]))
        sh.wire((o[0] + 5.08, out[1]), rpu.p("2"))
        sh.connect(rpu, "1", "+3V3D", stub=0)
        sh.label(f"GATE_IN{n}", (o[0] + 12.7, out[1]), 0, kind="global")
        sh.wire(minus, (minus[0] - 2.54, minus[1]), (minus[0] - 2.54, minus[1] + 5.08))
        sh.label("GATE_TH", (minus[0] - 2.54, minus[1] + 5.08), 270)
        sh.tie(f"GIN{n}", (rin, "1"))
        sh.tie(f"GIN{n}_CMP", (rin, "2"), (d, "3"), (rpd, "1"), (rh, "1"), (u, pp))
        sh.tie(f"GATE_IN{n}", (u, po), (rh, "2"), (rpu, "2"))
        sh.tie("GATE_TH", (u, pm))
    for i, ref in enumerate(("U801", "U802")):
        x = 160.02 + i * 25.4
        ic(sh, "LM393", (x, 58.42), {8: "+12V", 4: "GND"}, unit=3, ref=ref)
        decap(sh, (x + 10.16, 53.34), "100n", "0603", "+12V", f"{ref} V+ pin 8")
    sh.text("GATE_TH = +3V3D / 2", (160, 80), size=1.5, bold=True)
    rt = R(sh, "10k", (167.64, 91.44))
    rb = R(sh, "10k", (167.64, 101.6))
    c = C(sh, "100n", (180.34, 101.6))
    sh.connect(rt, 1, "+3V3D", stub=0)
    sh.wire(rt.p("2"), rb.p("1"))
    sh.wire((167.64, 96.52), (180.34, 96.52), c.p("1"))
    sh.wire((180.34, 96.52), (187.96, 96.52))
    sh.label("GATE_TH", (187.96, 96.52), 0)
    sh.connect(rb, 2, "GND", stub=0)
    sh.connect(c, 2, "GND", stub=0)
    sh.tie("GATE_TH", (rt, "2"), (rb, "1"), (c, "1"))
    # gate-in and jack-detect holes, spread over the four banks; each input's probe hole sits
    # beside it (wiring.py)
    wiring.place(sh, holes, "gatein", (330.2, 50.8), max_y=245)

    # jack-detect probe
    sh.text("JACK DETECT (Workshop System Computer): PROBE drives a pseudo-random bit through a resistor to each input's\n"
            "switch (normal) lug. Unpatched, the jack follows the sequence; patched, the lug opens. 100 kΩ for CV and audio\n"
            "inputs; 22 kΩ for gate inputs, whose 1.98 V threshold a 100 kΩ probe cannot reach (it gives ≈1.24 V).",
            (160, 120), size=1.5)
    r = R(sh, "1k", (172.72, 152.4), rot=90)
    sh.connect(r, 1, "PROBE")
    bus_x, top = 180.34, 152.4
    sh.wire(r.p("2"), (bus_x, top))
    d = clamp_below(sh, "BAT54S", (bus_x, top), "+3V3D", drop=-10.16)
    vals = ["100k"] * 10 + ["22k"] * 4
    bus_y0 = 160.02
    sh.wire((bus_x, top), (bus_x, bus_y0 + 13 * 6.35))
    for k, v in enumerate(vals, start=1):
        y = bus_y0 + (k - 1) * 6.35
        rr = R(sh, v, (bus_x + 2.54, y), rot=90)
        sh.wire(rr.p("2"), (rr.p("2")[0] + 2.54, y))
        sh.label(f"PR{k}", (rr.p("2")[0] + 2.54, y), 0)
        sh.tie("PROBE_BUS", (rr, "1"))
        sh.tie(f"PR{k}", (rr, "2"))
    sh.label("PROBE_BUS", (bus_x, top + 3.81), 0)
    sh.tie("PROBE_BUS", (r, "2"), (d, "3"))
    tp(sh, (147.32, 160.02), "PROBE")


# =====================================================================================  9  edge strips
def sheet_edge(sh):
    sh.text("EDGE STRIPS", (20, 18), size=2.5, bold=True)
    sh.text("Two n8synth-style edge strips, 40 positions each at 2.54 mm. Each position is an outer hole (the deck's\n"
            "header pin) joined to an inner hole (a wiring point): both pads carry the same pad number, so they share a net.\n"
            "Nothing on the board connects to them: each module is wired by hand from the channel holes to the inner\n"
            "holes. Deck cells occupy positions 1-10, 16-25 and 31-40; 11-15 and 26-30 are free tie points.\n"
            "10HP: the board sits parallel behind the deck and both strips are used. 6HP: the board sits at 90° and\n"
            "only the left strip meets the deck's right-angle header.", (20, 23), size=1.5)
    for ref, key, x in (("J901", "EDGE_L", 80), ("J902", "EDGE_R", 200)):
        ic(sh, key, (x, 140), {n: NC for n in range(1, 41)}, ref=ref)
    for i in range(3):
        part(sh, "FID", (300 + i * 15.24, 60), ref=f"FID90{i + 1}")
    sh.text("Fiducials for JLCPCB assembly", (295, 48), size=1.27)
    sh.text("Hardware licence: CC BY-SA 4.0 (LICENSE in hardware/analogue_board).", (295, 80), size=1.27)


# =====================================================================================  10  TRS MIDI
def sheet_midi(sh):
    sh.text("TRS MIDI IN AND OUT", (20, 18), size=2.5, bold=True)
    sh.text("MIDI 1.0 over 3.5 mm TRS, Type A (MIDI Association RP-054): tip = current sink (DIN pin 5), ring = current source\n"
            "(DIN pin 4), sleeve = shield (DIN pin 2). Electrical values per CA-033 (2014). Uses the two UART-capable spare pins through\n"
            "link holes on J101 (SPARE1-MIDI_TX, SPARE2-MIDI_RX): left open, SPARE1/2 stay plain GPIO. Review: docs/analogue_board_review/midi.md",
            (20, 23), size=1.5)

    # ---- MIDI OUT: buffered at 5 V so the jack never touches a module pin (the Teensy is not 5 V tolerant)
    yo = 71.12
    sh.text("MIDI OUT: 3.3 V UART → 74AHCT1G125 at +5VD → 2 × 100 Ω per leg (1206) → TRS. Idle high = no loop current.\n"
            "A mono cable shorting ring to sleeve draws 25 mA from the buck; each 100 Ω sees 64 mW.", (20, 46), size=1.27)
    sh.wire((43.18, yo), (45.72, yo))
    sh.label("MIDI_TX", (43.18, yo), 180, kind="global")
    r1 = R(sh, "1k", (48.26, yo), rot=90, fields={"Note": "limits current into the buffer input from the module pin"})
    u = part(sh, "AHCT1G125", (73.66, yo), **AHCT_TEXT(73.66, yo))
    a = u.p("2")
    sh.wire(r1.p("2"), a)
    rpu = R(sh, "10k", (53.34, yo - 5.08), fields={"Note": "idles the line high when the link is open or the module boots"})
    sh.wire(rpu.p("2"), (53.34, yo))
    sh.connect(rpu, "1", "+3V3D", stub=0)
    sh.connect(u, "1", "GND")
    sh.connect(u, "5", "+5VD")
    sh.connect(u, "3", "GND")
    sh.tie("MIDI_TX", (r1, "1"))
    sh.tie("MIDI_TXB", (r1, "2"), (rpu, "2"), (u, "2"))
    y = u.p("4")
    node = (y[0] + 5.08, yo)
    ra = R(sh, "100R", (node[0] + 7.62, yo), rot=90, size="1206")
    rb = R(sh, "100R", (node[0] + 17.78, yo), rot=90, size="1206")
    sh.wire(y, node, ra.p("1"))
    sh.wire(ra.p("2"), rb.p("1"))
    sh.wire(rb.p("2"), (rb.p("2")[0] + 5.08, yo))
    sh.label("MO_T", (rb.p("2")[0] + 5.08, yo), 0)
    d = clamp_below(sh, "BAT54S", node, "+5VD")
    sh.tie("MIDI_DRV", (u, "4"), (ra, "1"), (d, "3"))
    sh.tie("MIDI_TIP_MID", (ra, "2"), (rb, "1"))
    sh.tie("MO_T", (rb, "2"))
    yr = yo + 22.86
    rc = R(sh, "100R", (node[0] + 7.62, yr), rot=90, size="1206")
    rd = R(sh, "100R", (node[0] + 17.78, yr), rot=90, size="1206")
    sh.power("+5VD", (node[0], yr))
    sh.wire((node[0], yr), rc.p("1"))
    sh.wire(rc.p("2"), rd.p("1"))
    sh.wire(rd.p("2"), (rd.p("2")[0] + 5.08, yr))
    sh.label("MO_R", (rd.p("2")[0] + 5.08, yr), 0)
    sh.tie("+5VD", (rc, "1"))
    sh.tie("MIDI_RING_MID", (rc, "2"), (rd, "1"))
    sh.tie("MO_R", (rd, "2"))
    decap(sh, (35.56, 101.6), "100n", "0402", "+5VD", f"{u.ref} VCC pin 5")

    # ---- MIDI IN: H11L1 Schmitt-output opto at 3.3 V
    yi = 157.48
    sh.text("MIDI IN: ring → 220 Ω → H11L1 LED → tip; 1N4148WS across the LED for reverse polarity. H11L1 switches at 1.6 mA\n"
            "(a worst-case 3.3 V sender still gives ≈4.5 mA). Output pulled up by 1 kΩ to +3V3D, then 1 kΩ to the link hole.\n"
            "The IN jack's sleeve is NOT grounded (CA-033: no ground loop): wire it to MI_S (100 nF to ground) or leave it open.",
            (20, 124), size=1.27)
    opto = part(sh, "H11L1", (91.44, yi))
    p1, p2 = opto.p("1"), opto.p("2")
    rin = R(sh, "220R", (60.96, yi - 5.08), rot=90, size="0805", fields={"Note": "MIDI IN current limit (CA-033)"})
    sh.wire((43.18, yi - 5.08), rin.p("1"))
    sh.label("MI_R", (43.18, yi - 5.08), 180)
    sh.wire(rin.p("2"), (78.74, yi - 5.08), (78.74, p1[1]), p1)
    sh.wire((43.18, yi + 5.08), (78.74, yi + 5.08), (78.74, p2[1]), p2)
    sh.label("MI_T", (43.18, yi + 5.08), 180)
    dr = part(sh, "1N4148WS", (71.12, yi), rot=270, text_left=True)
    sh.wire((71.12, yi - 5.08), dr.p("1"))
    sh.wire(dr.p("2"), (71.12, yi + 5.08))
    sh.connect(opto, "6", "+3V3D")
    sh.connect(opto, "5", "GND")
    sh.connections.append((opto.ref, "3", None, opto.p("3")))
    sh.tie("MI_R", (rin, "1"))
    sh.tie("MIDI_LED_A", (rin, "2"), (opto, "1"), (dr, "1"))
    sh.tie("MI_T", (opto, "2"), (dr, "2"))
    o = opto.p("4")
    rxo = (o[0] + 5.08, yi)
    rpu = R(sh, "1k", (rxo[0], yi - 5.08), fields={"Note": "opto pull-up (1 kΩ, not 270-470 Ω, to halve current pulses on +3V3D)"})
    rs = R(sh, "1k", (rxo[0] + 10.16, yi), rot=90, fields={"Note": "series: the module pin never sees the opto directly"})
    sh.wire(o, rxo, rs.p("1"))
    sh.wire(rxo, rpu.p("2"))
    sh.connect(rpu, "1", "+3V3D", stub=0)
    sh.wire(rs.p("2"), (rs.p("2")[0] + 5.08, yi))
    sh.label("MIDI_RX", (rs.p("2")[0] + 5.08, yi), 0, kind="global")
    sh.tie("MIDI_RXO", (opto, "4"), (rpu, "2"), (rs, "1"))
    sh.tie("MIDI_RX", (rs, "2"))
    decap(sh, (127, 147.32), "100n", "0402", "+3V3D", f"{opto.ref} VCC pin 6")
    cs = C(sh, "100n", (55.88, 182.88), size="0603", fields={"Note": "AC-couples the IN jack's shield to ground"})
    sh.connect(cs, 1, "MI_S")
    sh.connect(cs, 2, "GND", stub=0)

    holes(sh, (200.66, 101.6), ["MO_T", "MO_R", "MI_T", "MI_R", "MI_S", "GND"], "TRS MIDI holes", ref="J1001")
    sh.text("WIRING (two stereo jacks in deck cells):\n"
            "OUT: tip → MO_T, ring → MO_R, sleeve → the deck's D (ground) pad.\n"
            "IN:  tip → MI_T, ring → MI_R, sleeve → MI_S or open: NOT to D.\n"
            "Turn MIDI on: link SPARE1-MIDI_TX and SPARE2-MIDI_RX on J101.\n"
            "Type B gear: swap that jack's tip and ring wires.\n"
            "Bring-up: loop OUT to IN with a stereo cable; ≈1.2-1.3 V\n"
            "across the 220 Ω while sending = 5.5-5.9 mA in the loop.\n"
            "The H11L1 is ≈4 mm tall: place it outside the module footprint.",
            (215, 120), size=1.27)

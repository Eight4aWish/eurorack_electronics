"""Sheets 3-5: codec and audio, CV jacks and ADC, CV DAC."""

import variant
import wiring
from blocks import NC, C, R, decap, decaps, holes, ic, part, tp
from parts import ICS


def opamp_feedback(sh, ox, oy, rf, cf, rf_size="0402", net=None):
    """Rf ∥ Cf from the inverting node (ox-12.7, oy-2.54) over the top to the output node (ox+10.16, oy).
    The op-amp unit is drawn mirrored so its inverting input is the upper pin."""
    n1 = (ox - 12.7, oy - 2.54)
    o = (ox + 10.16, oy)
    r = R(sh, rf, (ox, oy - 10.16), rot=90, size=rf_size)
    c = C(sh, cf, (ox, oy - 17.78), rot=90)
    sh.wire(n1, (n1[0], oy - 17.78))
    sh.wire((n1[0], oy - 10.16), r.p("1"))
    sh.wire((n1[0], oy - 17.78), c.p("1"))
    sh.wire(r.p("2"), (o[0], oy - 10.16))
    sh.wire(c.p("2"), (o[0], oy - 17.78))
    sh.wire((o[0], oy - 17.78), o)
    return r, c, n1, o


def clamp_below(sh, key, node, rail, gnd="GND", drop=10.16):
    """Series diode pair (BAT54S / BAV99) below `node` (or above it if drop < 0): common pin to the node,
    cathode (pin 2) to the rail, anode (pin 1) to ground."""
    d = part(sh, key, (node[0], node[1] + drop), rot=180 if drop > 0 else 0)
    sh.wire(node, d.p("3"))
    sh.connect(d, "2", rail, stub=5.08)  # rail text clear of the diode's reference
    sh.connect(d, "1", gnd)
    return d


# =====================================================================================  3  codec
def sheet_codec(sh):
    sh.text("CODEC AND AUDIO", (20, 18), size=2.5, bold=True)
    sh.text("PCM3060 in hardware-control mode, the same straps as Mutable Beads: MODE 220 kΩ to DGND =\n"
            "parallel control with differential outputs; FMT low = 24-bit I2S, IFMD low = ADC and DAC both\n"
            "slaves, DEMP low = no de-emphasis. One I2S bus feeds both halves. RST is pulled up, so the codec\n"
            "starts by itself; CODEC_RST also reaches a hole (J303) so firmware can hold it in reset, as Beads\n"
            "does. Full scale is 20 Vpp in and out; firmware runs about 6 dB below. VCC via a ferrite from\n"
            "+5VA, VDD via 5.1 Ω from +3V3D: each with its own 10 µF + 100 nF.",
            (20, 23), size=1.5)

    u = ic(sh, "PCM3060", (80, 125), {
        1: "CODEC_FMT", 2: "CODEC_DEMP", 27: "CODEC_IFMD", 15: "CODEC_RST", 28: "CODEC_MODE", 25: "VINL", 26: "VINR",
        4: "LRCK", 5: "BCK", 6: "MCLK", 12: "I2S_DOUT", 11: "LRCK", 10: "BCK", 9: "MCLK",
        20: "VOUTL_P", 19: "VOUTL_N", 18: "VOUTR_P", 17: "VOUTR_N", 14: NC, 13: NC, 3: "I2S_DIN", 21: "VCOM",
        7: "CODEC_VDD", 24: "CODEC_VCC", 8: "GND", 16: "GND", 23: "GND", 22: "GND"}, ref="U301",
        stubs={24: 7.62, 16: 7.62, 22: 7.62, 21: 17.78})  # VCOM label past the I2S_DIN label above it
    for i, net in enumerate(["CODEC_FMT", "CODEC_DEMP", "CODEC_IFMD"]):
        r = R(sh, "10k", (25.4 + i * 10.16, 99.06), fields={"Note": "hardware-mode strap, low; lift to change"})
        sh.connect(r, 1, net)
        sh.connect(r, 2, "GND", stub=0)
    sh.text("H/W-mode straps, all low:\nFMT = I2S, DEMP = off,\nIFMD = slave", (20, 109), size=1.27)
    # supply filtering: ferrite into VCC, 5.1 Ω into VDD
    fb = part(sh, "FERRITE", (40.64, 205.74), rot=90, value="BLM18PG121")
    sh.connect(fb, 1, "+5VA")
    sh.connect(fb, 2, "CODEC_VCC")
    r = R(sh, "5.1R", (40.64, 218.44), rot=90, size="0603", fields={"Note": "isolates the codec VDD from logic noise on +3V3D"})
    sh.connect(r, 1, "+3V3D")
    sh.connect(r, 2, "CODEC_VDD")
    for i, (net, pin, v, sz) in enumerate([("CODEC_VCC", "24", "10u", "0805"), ("CODEC_VCC", "24", "100n", "0402"),
                                           ("CODEC_VDD", "7", "10u", "0805"), ("CODEC_VDD", "7", "100n", "0402")]):
        c = C(sh, v, (60.96 + i * 12.7, 182.88), size=sz, decouples=f"U301 {'VCC' if pin == '24' else 'VDD'} pin {pin}")
        if i in (0, 2):
            sh.flagged_stub(c, 1, net)
        else:
            sh.connect(c, 1, net)
        sh.connect(c, 2, "GND", stub=0)
    for i, (v, sz) in enumerate([("10u", "0805"), ("100n", "0402")]):
        c = C(sh, v, (111.76 + i * 12.7, 182.88), size=sz, decouples="U301 VCOM pin 21")
        sh.connect(c, 1, "VCOM")
        sh.connect(c, 2, "GND", stub=0)
    r = R(sh, "1k", (25.4, 180.34), fields={"Note": "RST pull-up (internal 50 kΩ pull-down)"})
    sh.connect(r, 1, "+3V3D", stub=0)
    sh.connect(r, 2, "CODEC_RST")
    r = R(sh, "220k", (25.4, 152.4), size="0603", fields={"Note": "MODE: 220 kΩ ±5 % to DGND selects H/W mode, differential out"})
    sh.connect(r, 1, "CODEC_MODE")
    sh.connect(r, 2, "GND", stub=0)
    holes(sh, (76.2, 203.2), ["CODEC_RST", "GND"], "Codec RST", ref="J303")

    # audio inputs: AC-coupled inverting stage, gain -15k/100k × 10k/(10k + 1k) = -0.136: 22 Vpp -> 3 Vpp
    sh.text("AUDIO INPUTS: 22 Vpp → 3 Vpp (codec full scale). AC-coupled, inverting (firmware flips the sign).\n"
            "±12 V stays inside the codec rails, so the BAT54S clamps only act on faults. 100 nF on each + input\n"
            "decouples VCOM (12.5 kΩ source) at the op-amp, as the Patch SM does.",
            (150, 31), size=1.5)
    for ch, (unit, side, oy) in enumerate([(1, "L", 62.23), (2, "R", 105.41)], start=1):
        ox = 205.74
        op = part(sh, "TL074H", (ox, oy), mirror="x", unit=unit, ref="U302", hide_value=True)
        r, c, n1, o = opamp_feedback(sh, ox, oy, "15k", "100p")
        rin = R(sh, "100k", (ox - 17.78, oy - 2.54), rot=90)
        cin = C(sh, "1u", (ox - 27.94, oy - 2.54), rot=90, size="0805", fields={"Note": "AC coupling, 50 V X7R"})
        jn = (ox - 35.56, oy - 2.54)
        rbl = R(sh, "1M", (jn[0], oy + 2.54), fields={"Note": "holds the jack side at 0 V"}, text_left=True)
        sh.wire(op.p("2") if unit == 1 else op.p("6"), n1)
        sh.wire(n1, rin.p("2"))
        sh.wire(rin.p("1"), cin.p("2"))
        sh.wire(cin.p("1"), jn, (jn[0] - 5.08, jn[1]))
        sh.wire(jn, rbl.p("1"))
        sh.connect(rbl, "2", "GND", stub=0)
        sh.label(f"AIN{ch}", (jn[0] - 5.08, jn[1]), 180)
        plus = op.p("3") if unit == 1 else op.p("5")
        vc = (plus[0] - 10.16, plus[1])
        cv = C(sh, "100n", (vc[0], vc[1] + 2.54), decouples=f"VCOM at U302 {'pin 3' if unit == 1 else 'pin 5'}")
        sh.wire(plus, vc)
        sh.label("VCOM", vc, 180)
        sh.connect(cv, "2", "GND", stub=0)
        outp = op.p("1") if unit == 1 else op.p("7")
        rout = R(sh, "1k", (ox + 15.24, oy), rot=90)
        sh.wire(outp, o, rout.p("1"))
        k = (ox + 25.4, oy)
        sh.wire(rout.p("2"), k, (k[0] + 7.62, oy))
        sh.label(f"VIN{side}", (k[0] + 7.62, oy), 0)
        d = clamp_below(sh, "BAT54S", k, "+5VA")
        inv, non, out = ("2", "3", "1") if unit == 1 else ("6", "5", "7")
        sh.tie(f"AIN{ch}_N", (op, inv), (r, "1"), (c, "1"), (rin, "2"))
        sh.tie(f"AIN{ch}_OUT", (op, out), (r, "2"), (c, "2"), (rout, "1"))
        sh.tie(f"AIN{ch}_AC", (rin, "1"), (cin, "2"))
        sh.tie(f"AIN{ch}", (cin, "1"), (rbl, "1"))
        sh.tie("VCOM", (op, non), (cv, "1"))
        sh.tie(f"VIN{side}", (rout, "2"), (d, "3"))

    # audio outputs: balanced second-order MFB low-pass, gain 30k/12k = 2.5: 8 Vpp differential -> 20 Vpp
    sh.text("AUDIO OUTPUTS: balanced second-order MFB low-pass (Beads' topology), gain 30k/12k = 2.5, so 8 Vpp → 20 Vpp,\n"
            "DC-coupled, non-inverting (VOUT+ to the + side). 1 nF C0G across the two nodes and 100 pF from each op-amp input:\n"
            "f0 ≈ 65 kHz, Q ≈ 0.73, flat to 20 kHz (Basic parts except the 1 nF C0G). 1 kΩ 1206 out survives output-to-output patching.",
            (150, 138), size=1.5)
    for ch, (unit, side, oy) in enumerate([(3, "L", 175.26), (4, "R", 218.44)], start=1):
        ox = 205.74
        op = part(sh, "TL074H", (ox, oy), mirror="x", unit=unit, ref="U302", hide_value=True)
        inv, non, out = ("9", "10", "8") if unit == 3 else ("13", "12", "14")
        # the inverting row runs 7.62 mm above the op-amp's - input, so the 1 nF between the two rows has room for its text
        yn, yp = oy - 10.16, oy + 2.54
        na, nb = (ox - 20.32, yn), (ox - 20.32, yp)
        o = (ox + 10.16, oy)
        r1a = R(sh, "12k", (ox - 27.94, yn), rot=90)
        r1b = R(sh, "12k", (ox - 27.94, yp), rot=90)
        r2a = R(sh, "1k", (ox - 15.24, yn), rot=90)
        r2b = R(sh, "1k", (ox - 12.7, yp), rot=90)
        r3a = R(sh, "30k", (ox - 5.08, oy - 22.86), rot=90, size="0603")
        r3b = R(sh, "30k", (nb[0], oy + 7.62), size="0603")
        c2a = C(sh, "100p", (ox, oy - 15.24), rot=90)
        c2b = C(sh, "100p", (ox - 10.16, oy + 7.62))
        xd = ox - 22.86
        cd = C(sh, "1n C0G", (xd, oy - 3.81), size="0603", fields={"Note": "differential filter capacitor, C0G"},
               text_left=True)
        # inverting side: the - input reaches its 1k and 100 pF up a short bus at ox - 10.16
        sh.wire(r1a.p("2"), na, r2a.p("1"))
        sh.wire(r2a.p("2"), (ox - 10.16, yn))
        sh.wire(op.p(inv), (ox - 10.16, oy - 2.54), (ox - 10.16, oy - 15.24), c2a.p("1"))
        sh.wire(na, (na[0], oy - 22.86), r3a.p("1"))
        sh.wire(r3a.p("2"), (o[0], oy - 22.86), o)
        sh.wire(c2a.p("2"), (o[0], oy - 15.24))
        sh.wire((xd, yn), cd.p("1"))
        sh.wire(cd.p("2"), (xd, yp))
        # non-inverting side
        sh.wire(r1b.p("2"), nb, r2b.p("1"))
        sh.wire(r2b.p("2"), op.p(non))
        sh.wire(nb, r3b.p("1"))
        sh.wire((ox - 10.16, oy + 2.54), c2b.p("1"))
        sh.connect(r3b, "2", "GND", stub=0)
        sh.connect(c2b, "2", "GND", stub=0)
        for rr, net in ((r1a, f"VOUT{side}_N"), (r1b, f"VOUT{side}_P")):
            sh.wire(rr.p("1"), (rr.p("1")[0] - 2.54, rr.p("1")[1]))
            sh.label(net, (rr.p("1")[0] - 2.54, rr.p("1")[1]), 180)
        rout = R(sh, "1k", (ox + 15.24, oy), rot=90, size="1206", fields={"Note": "1206: survives output-to-output patching"})
        sh.wire(op.p(out), o, rout.p("1"))
        sh.wire(rout.p("2"), (rout.p("2")[0] + 5.08, oy))
        sh.label(f"AOUT{ch}", (rout.p("2")[0] + 5.08, oy), 0)
        sh.tie(f"AOUT{ch}_NA", (r1a, "2"), (r2a, "1"), (r3a, "1"), (cd, "1"))
        sh.tie(f"AOUT{ch}_NB", (r1b, "2"), (r2b, "1"), (r3b, "1"), (cd, "2"))
        sh.tie(f"AOUT{ch}_N", (op, inv), (r2a, "2"), (c2a, "1"))
        sh.tie(f"AOUT{ch}_P", (op, non), (r2b, "2"), (c2b, "1"))
        sh.tie(f"AOUT{ch}_OUT", (op, out), (r3a, "2"), (c2a, "2"), (rout, "1"))
        sh.tie(f"VOUT{side}_N", (r1a, "1"))
        sh.tie(f"VOUT{side}_P", (r1b, "1"))
        sh.tie(f"AOUT{ch}", (rout, "2"))

    ic(sh, "TL074H", (281.94, 190.5), {4: "+12V", 11: "-12V"}, unit=5, ref="U302")
    decap(sh, (294.64, 182.88), "100n", "0603", "+12V", "U302 V+ pin 4")
    decap(sh, (294.64, 198.12), "100n", "0603", "-12V", "U302 V- pin 11")
    wiring.place(sh, holes, "codec", (340.36, 60.96), max_y=245)   # audio holes, one in each bank
    for i, net in enumerate(["MCLK", "BCK", "LRCK", "I2S_DOUT", "I2S_DIN"]):
        tp(sh, (30.48 + i * 12.7, 238.76), net)
    sh.text("I2S test pads", (25.4, 226), size=1.27)


# =====================================================================================  4  CV in
CV_JACK = {1: "CV1", 2: "CV2", 3: "CV3", 4: "CV4", 5: "CV5", 6: "CV6", 7: "CVI7", 8: "CVI8"}
FIXED_CV = variant.has("fixed_cv")   # CVI7-8 (in only) and CVO7-8 (out only); the core board has the six switchable jacks only
CV_CHANNELS = range(1, 9) if FIXED_CV else range(1, 7)
# CV1-6 bidirectional through DG412 switches; (chip ref, unit, jack-side pin, op-amp-side pin, IN pin)
SWITCHES = {1: ("U402", 1, "2", "3", "1"), 2: ("U402", 4, "15", "14", "16"), 3: ("U402", 3, "10", "11", "9"),
            4: ("U402", 2, "6", "7", "8"), 5: ("U403", 1, "2", "3", "1"), 6: ("U403", 4, "15", "14", "16")}


def sheet_cv_in(sh):
    sh.text("CV JACKS AND ADC", (20, 18), size=2.5, bold=True)
    sh.text("ADS8688: 8 channels, 16-bit, 1 MΩ inputs with ±10.24 / ±5.12 V ranges per channel (firmware default ±10.24 V), OVP ±20 V.\n"
            "Each CV jack: 15 V TVS at the hole, read through 1 kΩ with 1 nF at the ADC pin (TI's EVM). 100 kΩ to ground, but the\n"
            "ADC's 1 MΩ returns to an internal bias, so an UNPATCHED input reads ≈ +0.2 V (no jack detect since 2026-10-16).\n"
            "CV1-6 are bidirectional: a DG412 switch (on at logic 1) joins the DAC stage through 1 kΩ (1206); with it on the ADC\n"
            "reads the jack itself. 4.7 kΩ pull-downs beat the TCA9555's internal pull-ups: every jack starts as an input.",
            (20, 23), size=1.5)
    adc_nets = {16: "ADC_IN1", 18: "ADC_IN2", 21: "ADC_IN3", 23: "ADC_IN4", 25: "ADC_IN5", 27: "ADC_IN6",
                12: "ADC_IN7" if FIXED_CV else "GND", 14: "ADC_IN8" if FIXED_CV else "GND",
                17: "GND", 19: "GND", 20: "GND", 22: "GND", 24: "GND", 26: "GND",
                13: "GND", 15: "GND", 10: "GND", 11: "GND",
                36: "SPIA_MISO", 1: "SPIA_MOSI", 37: "SPIA_SCK", 38: "CS_ADC", 3: "GND", 2: "ADC_RST", 4: "GND",
                35: NC, 7: "REFCAP", 5: "REFIO", 6: "GND", 9: "+5VA", 30: "+5VA", 34: "+3V3D",
                8: "GND", 28: "GND", 29: "GND", 31: "GND", 32: "GND", 33: "GND"}
    ic(sh, "ADS8688", (66.04, 130.81), adc_nets, ref="U401", stubs={30: 7.62, 34: 12.7})
    sh.text("DAISY, REFSEL, AUX low: stand-alone, internal reference, AUX channel unused.\n"
            "REFCAP 1 µF + 22 µF and REFIO 10 µF as TI's layout example.", (20, 200), size=1.27)
    decap(sh, (35.56, 177.8), "1u", "0603", "+5VA", "U401 AVDD pin 9")
    decap(sh, (48.26, 177.8), "1u", "0603", "+5VA", "U401 AVDD pin 30")
    decap(sh, (60.96, 177.8), "10u", "0805", "+5VA", "U401 AVDD bulk")
    decap(sh, (76.2, 177.8), "10u", "0805", "+3V3D", "U401 DVDD pin 34")
    decap(sh, (88.9, 177.8), "100n", "0402", "+3V3D", "U401 DVDD pin 34")
    for i, (v, s, net, note) in enumerate([("1u", "0603", "REFCAP", "U401 REFCAP pin 7, at the pin"),
                                            ("22u", "1206", "REFCAP", "U401 REFCAP pin 7"),
                                            ("10u", "0805", "REFIO", "U401 REFIO pin 5 (internal reference)")]):
        c = C(sh, v, (104.14 + i * 12.7, 180.34), size=s, decouples=note)
        sh.connect(c, 1, net)
        sh.connect(c, 2, "GND", stub=0)
    r = R(sh, "10k", (25.4, 177.8), fields={"Note": "RST/PD high = running"})
    sh.connect(r, 1, "+3V3D", stub=0)
    sh.connect(r, 2, "ADC_RST")
    r = R(sh, "10k", (142.24, 177.8), fields={"Note": "keeps the ADC deselected while the module boots"})
    sh.connect(r, 1, "+3V3D", stub=0)
    sh.connect(r, 2, "CS_ADC")
    r = R(sh, "10k", (154.94, 177.8), fields={"Note": "AVDD below 30 kΩ when unpowered: keeps the ±20 V OVP rating (TI condition)"})
    sh.connect(r, 1, "+5VA", stub=0)
    sh.connect(r, 2, "GND", stub=0)

    # channel rows
    x_sw, x_j, y0, pitch = 172.72, 200.66, 45.72, 20.32
    for n in CV_CHANNELS:
        y = y0 + (n - 1) * pitch
        jn = (x_j, y)
        radc = R(sh, "1k", (x_j + 7.62, y), rot=90)
        a = (x_j + 15.24, y)
        rpd = R(sh, "100k", (a[0], y + 5.08))
        cf = C(sh, "1n", (a[0] + 10.16, y + 2.54), fields={"Note": "RF/ESD filter at the ADC pin (TI EVM)"})
        tvs = part(sh, "TVS15", (jn[0], y + 5.08), rot=90, text_left=True)
        sh.wire(jn, radc.p("1"))
        sh.wire(radc.p("2"), a, (a[0] + 15.24, y))
        sh.wire(a, rpd.p("1"))
        sh.connect(rpd, "2", "GND", stub=0)
        sh.connect(cf, "2", "GND", stub=0)
        sh.wire(jn, tvs.p("1") if tvs.p("1")[1] < tvs.p("2")[1] else tvs.p("2"))
        sh.connect(tvs, "2" if tvs.p("1")[1] < tvs.p("2")[1] else "1", "GND", stub=0)
        sh.label(f"ADC_IN{n}", (a[0] + 15.24, y), 0)
        sh.tie(f"ADC_IN{n}", (radc, "2"), (rpd, "1"), (cf, "1"))
        sh.tie(CV_JACK[n], (radc, "1"), (tvs, "1" if tvs.p("1")[1] < tvs.p("2")[1] else "2"))
        if n in SWITCHES:
            ref, unit, pj, po, pin_in = SWITCHES[n]
            sw = part(sh, "DG412", (x_sw, y), mirror="y", unit=unit, ref=ref, hide_value=True)
            rsw = R(sh, "1k", (x_j - 7.62, y), rot=90, size="1206", fields={"Note": "1206: survives output-to-output patching"})
            sh.wire(sw.p(pj), rsw.p("1"))
            sh.wire(rsw.p("2"), jn)
            sh.connect(sw, po, f"CVDRV{n}")
            ip = sw.p(pin_in)
            e = (ip[0], ip[1] + 2.54)
            rpd2 = R(sh, "4.7k", (e[0] + 5.08, e[1] + 2.54), fields={"Note": "beats the TCA9555 internal pull-up"})
            sh.wire(ip, e, (e[0] + 5.08, e[1]))
            sh.wire(e, (e[0] - 5.08, e[1]))
            sh.label(f"SW_EN{n}", (e[0] - 5.08, e[1]), 180, kind="global")
            sh.connect(rpd2, "2", "GND", stub=0)
            sh.tie(f"SW_EN{n}", (sw, pin_in), (rpd2, "1"))
            sh.tie(f"CV{n}_SW", (sw, pj), (rsw, "1"))
            sh.tie(CV_JACK[n], (rsw, "2"))
            sh.label(CV_JACK[n], (jn[0], y), 90)
        else:
            sh.wire((jn[0] - 5.08, y), jn)
            sh.label(CV_JACK[n], (jn[0] - 5.08, y), 180)

    if FIXED_CV:
        sh.text("CVO7, CVO8 (out only): their 1 kΩ sits inside the DAC stage's\nfeedback loop on the CV DAC sheet, so the jack holds its voltage\n"
                "under load. Calibrate them with a cable to CVI7 / CVI8.", (x_sw - 10, y0 + 8 * pitch + 2), size=1.27)
    else:
        sh.text("ADC channels 7 and 8 are unused on this board: inputs grounded.", (x_sw - 10, y0 + 6 * pitch + 2), size=1.27)

    # switch power and spares
    for i, ref in enumerate(("U402", "U403")):
        x = 265.43 + i * 63.5
        ic(sh, "DG412", (x, 66.04), {13: "+12V", 4: "-12V", 12: "+5VD", 5: "GND"}, unit=5, ref=ref,
           stubs={12: 7.62, 4: 7.62})
        decap(sh, (x + 25.4, 55.88), "100n", "0603", "+12V", f"{ref} V+ pin 13")
        decap(sh, (x + 25.4, 78.74), "100n", "0603", "-12V", f"{ref} V- pin 4")
        decap(sh, (x + 38.1, 55.88), "100n", "0402", "+5VD", f"{ref} VL pin 12")
    sh.text("Spare switches (U403 SW3, SW4): off, both sides grounded", (265, 100), size=1.27)
    for j, (unit, pins) in enumerate([(3, ("10", "11", "9")), (2, ("6", "7", "8"))]):
        ic(sh, "DG412", (280 + j * 50.8, 116.84), {pins[0]: "GND", pins[1]: "GND", pins[2]: "GND"}, unit=unit, ref="U403",
           hide_value=True)

    wiring.place(sh, holes, "cv", (350.52, 139.7), max_y=245)   # CV jack holes, spread over the four banks
    for i, net in enumerate(["SPIA_SCK", "SPIA_MOSI", "SPIA_MISO", "CS_ADC", "CS_DAC"]):
        tp(sh, (264.16 + i * 12.7, 160.02), net)
    sh.text("Converter bus test pads", (259, 148), size=1.27)


# =====================================================================================  5  CV DAC
def sheet_cv_dac(sh):
    sh.text("CV DAC", (20, 18), size=2.5, bold=True)
    sh.text("DAC8568 grade A: 0-2.5 V from its internal reference (off at power-up), outputs reset to zero. Each stage: non-inverting\n"
            "gain 1 + 33k/10k = 4.3, offset by OFFSET_REF = VREF × 22k/34k through the 10 kΩ: Vout = 4.3·Vdac − 5.34 V, so −5.34 V …\n"
            "+5.41 V, putting ±5 V inside the DAC's specified codes (0 V at code ≈ 32544). The offset tracks the DAC's own reference, as\n"
            "in Performer, O&C, Marbles and Stages. CVO7/8: the 1 kΩ sits inside the loop (feedback from the jack side, as Mutable\n"
            "does), so the jack holds its voltage under load. CV1-6 go through the DG412 switch; firmware corrects their load sag\n"
            "using the ADC, which reads the jack. ±10 V variant (not Rev A): Rf 75k, divider 15k/20k, all Basic: gain 8.5,\n"
            "OFFSET_REF 1.429 V, −10.71 … +10.54 V; needs ≥ 10 kΩ loads. The TL074H can swing it.",
            (20, 23), size=1.5)
    dac = {2: "CS_DAC", 16: "SPIA_SCK", 15: "SPIA_MOSI", 1: "GND", 9: "+3V3A", 8: "DAC_VREF",
           4: "DAC1", 13: "DAC2", 5: "DAC3", 12: "DAC4", 6: "DAC5", 11: "DAC6",
           7: "DAC7" if FIXED_CV else NC, 10: "DAC8" if FIXED_CV else NC,
           3: "+3V3A", 14: "GND"}
    ic(sh, "DAC8568", (66.04, 88.9), dac, ref="U501")
    sh.text("LDAC low: each write updates its output.\nCLR high: clear pin unused.", (40, 116), size=1.27)
    decaps(sh, 35.56, 132.08, "+3V3A", [("10u", "0805"), ("100n", "0402")], "U501 AVDD pin 3")
    c = C(sh, "1u", (68.58, 134.62), decouples="U501 VREFIN/VREFOUT pin 8 (>= 150 nF)")
    sh.connect(c, 1, "DAC_VREF")
    sh.connect(c, 2, "GND", stub=0)
    r = R(sh, "10k", (86.36, 132.08), fields={"Note": "keeps the DAC deselected while the module boots"})
    sh.connect(r, 1, "+3V3D", stub=0)
    sh.connect(r, 2, "CS_DAC")

    # offset reference: 2/3 of DAC_VREF, filtered, buffered
    ox, oy = 88.9, 175.26
    sh.text("OFFSET_REF = VREF × 22k/(12k + 22k) = 1.618 V, buffered", (40, 155), size=1.5, bold=True)
    sh.text("1 nF (not 1 µF): the offset must track VREF quickly, or\nenabling the reference glitches every output.", (40, 159), size=1.27)
    rt = R(sh, "12k", (ox - 40.64, oy - 2.54), rot=90)
    rb = R(sh, "22k", (ox - 30.48, oy + 2.54))
    cf = C(sh, "1n", (ox - 20.32, oy + 2.54), fields={"Note": "light filter; must follow VREF at enable"})
    op = part(sh, "TL074H", (ox, oy), unit=1, ref="U504")
    plus = op.p("3")
    sh.wire(rt.p("2"), (rb.p("1")[0], plus[1]), plus)
    sh.wire((rb.p("1")[0], plus[1]), rb.p("1"))
    sh.wire((cf.p("1")[0], plus[1]), cf.p("1"))
    sh.connect(rb, "2", "GND", stub=0)
    sh.connect(cf, "2", "GND", stub=0)
    sh.connect(rt, "1", "DAC_VREF")
    out = op.p("1")
    o = (out[0] + 2.54, out[1])
    minus = op.p("2")
    sh.wire(out, o, (o[0] + 7.62, o[1]))
    sh.wire(o, (o[0], minus[1] + 7.62), (minus[0] - 2.54, minus[1] + 7.62), (minus[0] - 2.54, minus[1]), minus)
    sh.label("OFFSET_REF", (o[0] + 7.62, o[1]), 0)
    sh.label("OFFS_DIV", ((rt.p("2")[0] + rb.p("1")[0]) / 2, plus[1]), 90)
    sh.tie("OFFS_DIV", (rt, "2"), (rb, "1"), (cf, "1"), (op, "3"))
    sh.tie("OFFSET_REF", (op, "1"), (op, "2"))

    # gain stages
    # CV1-4 on U502; CV5-8 on U503. The core board has no CV7-8, so CV5-6 take two of the offset
    # buffer's spare sections (U504 B, C) and U503 goes
    if FIXED_CV:
        stages = [(n, "U502" if n <= 4 else "U503", (n - 1) % 4 + 1) for n in range(1, 9)]
    else:
        stages = [(n, "U502", n) for n in range(1, 5)] + [(5, "U504", 2), (6, "U504", 3)]
    pins = {1: ("2", "3", "1"), 2: ("6", "5", "7"), 3: ("9", "10", "8"), 4: ("13", "12", "14")}
    for n, ref, unit in stages:
        col, row = (n - 1) // 4, (n - 1) % 4
        ox, oy = 205.74 + col * 106.68, 64.77 + row * 30.48
        op = part(sh, "TL074H", (ox, oy), mirror="x", unit=unit, ref=ref, hide_value=True)
        inv, non, out = pins[unit]
        rg = R(sh, "10k", (ox - 17.78, oy - 2.54), rot=90)
        if n <= 6:
            rf, cfb, n1, o = opamp_feedback(sh, ox, oy, "33k", "100p")
            sh.wire(op.p(inv), n1, rg.p("2"))
            sh.wire(op.p(out), o, (o[0] + 5.08, oy))
            sh.label(f"CVDRV{n}", (o[0] + 5.08, oy), 0, kind="global")
            sh.tie(f"CVDRV{n}", (op, out), (rf, "2"), (cfb, "2"))
        else:
            # output-only: Rf from the jack side of the 1 kΩ (inside the loop), Cf local at the op-amp
            n1 = (ox - 12.7, oy - 2.54)
            o = (ox + 10.16, oy)
            rout = R(sh, "1k", (ox + 15.24, oy), rot=90, size="1206", fields={"Note": "inside the feedback loop; 1206 for patching faults"})
            j = (ox + 22.86, oy)
            rf = R(sh, "33k", (ox, oy - 17.78), rot=90)
            cfb = C(sh, "100p", (ox, oy - 10.16), rot=90)
            sh.wire(op.p(inv), n1, rg.p("2"))
            sh.wire(n1, (n1[0], oy - 17.78), rf.p("1"))
            sh.wire((n1[0], oy - 10.16), cfb.p("1"))
            sh.wire(cfb.p("2"), (o[0], oy - 10.16), o)
            sh.wire(rf.p("2"), (j[0], oy - 17.78), j)
            sh.wire(op.p(out), o, rout.p("1"))
            sh.wire(rout.p("2"), j, (j[0] + 5.08, oy))
            sh.label(f"CVO{n}", (j[0] + 5.08, oy), 0, kind="global")
            sh.tie(f"CVDAC{n}_OUT", (op, out), (cfb, "2"), (rout, "1"))
            sh.tie(f"CVO{n}", (rout, "2"), (rf, "2"))
        sh.connect(rg, "1", "OFFSET_REF")
        sh.wire(op.p(non), (op.p(non)[0] - 5.08, op.p(non)[1]))
        sh.label(f"DAC{n}", (op.p(non)[0] - 5.08, op.p(non)[1]), 180)
        sh.tie(f"CVDAC{n}_N", (op, inv), (rf, "1"), (cfb, "1"), (rg, "2"))
        sh.tie(f"DAC{n}", (op, non))
    sh.text("CVDRV1-6 go to the DG412 switches (sheet CV jacks & ADC)." + (" CVO7-8 go straight to their holes." if FIXED_CV
            else " CV5-6 run on U504 B and C."), (190, 180), size=1.27)

    # spare sections of U504 as grounded followers, and the op-amp supplies
    spares = [(2, ("6", "5", "7")), (3, ("9", "10", "8")), (4, ("13", "12", "14"))] if FIXED_CV else [(4, ("13", "12", "14"))]
    for k, (unit, (inv, non, out)) in enumerate(spares):
        ox, oy = 147.32, 195.58 + k * 20.32
        op = part(sh, "TL074H", (ox, oy), unit=unit, ref="U504", hide_value=True)
        sh.connect(op, non, "GND")
        o = (op.p(out)[0] + 2.54, oy)
        m = op.p(inv)
        sh.wire(op.p(out), o, (o[0], m[1] + 5.08), (m[0] - 2.54, m[1] + 5.08), (m[0] - 2.54, m[1]), m)
        sh.tie(f"U504_SPARE{unit}", (op, out), (op, inv))
    sh.text("Spare U504 sections: followers with + to GND", (120, 186), size=1.27)
    for i, ref in enumerate(("U502", "U503", "U504") if FIXED_CV else ("U502", "U504")):
        x = 210 + i * 35.56
        ic(sh, "TL074H", (x, 215.9), {4: "+12V", 11: "-12V"}, unit=5, ref=ref)
        decap(sh, (x + 12.7, 208.28), "100n", "0603", "+12V", f"{ref} V+ pin 4")
        decap(sh, (x + 12.7, 223.52), "100n", "0603", "-12V", f"{ref} V- pin 11")

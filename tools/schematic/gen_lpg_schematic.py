#!/usr/bin/env python3
"""
Generate build-phase schematics for the Dual Pingable LPG, for follow-along
build videos. Sheets are aligned to the build PHASES (not the functional netlist
blocks), driven by the per-component `stage` + `color` fields in
tools/visualizer/layouts/lpg.json.

Sheets (Channel B is a clone of Channel A, so it is not redrawn):
  phase1_channel.png  — a channel's first sound: audio path + driver + MANUAL
  phase2_channel.png  — that channel made pingable: + CV, strike, status LED
                        (cumulative: phase-1 parts faded grey, phase-2 in colour)
  phase5_mix.png      — the mix summer (CHA_OUT / CHB_OUT in as labelled stubs)

Cumulative convention: current phase = bold phase colour; earlier phases = thin
grey; later phases omitted. Positions are identical across sheets so the board
"grows" in place. Channel A designators shown; B mirrors with its own (see note).
"""
import os
import json
import schemdraw
import schemdraw.elements as elm

schemdraw.use('matplotlib')

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(REPO, "docs", "schematics")
os.makedirs(OUT, exist_ok=True)

_layout = json.load(open(os.path.join(REPO, "tools", "visualizer", "layouts", "lpg.json")))
V = {tp["id"]: tp["value"] for tp in _layout["twoPins"]}
PHASE_COLORS = {s["id"]: s["color"] for s in _layout["stages"]}
GREY = "#a8a8a8"
POTVAL = {"P1": "100K", "P2": "100K", "P3": "500K"}


def val(desig):
    raw = V.get(desig, "")
    if "Zener" in raw or desig in ("VD5", "VD6"):
        return "6v8"
    return raw


class Sheet:
    def __init__(self, render_phase):
        self.rp = render_phase
        self.d = schemdraw.Drawing()
        self.d.config(unit=2.0, fontsize=11)

    def phase(self, p):
        if p == self.rp:
            self.d.config(color=PHASE_COLORS[p], lw=2.4)
        else:
            self.d.config(color=GREY, lw=1.1)

    def shows(self, p):
        return self.rp >= p

    def __iadd__(self, elem):
        self.d += elem
        return self


def follower(s, name, inpoint):
    op = elm.Opamp(leads=True).anchor("in2").at(inpoint).label(name, loc="center", ofst=0, fontsize=9)
    s += op
    fb_y = op.in1.y + s.d.unit * 0.45
    s += elm.Line().at(op.out).to((op.out.x, fb_y))
    s += elm.Line().to((op.in1.x, fb_y))
    s += elm.Line().to(op.in1)
    return op


def vpot(s, label, tap_pt, value, top_to, bot_to, loc="left"):
    """Vertical pot, wiper(tap) on the right at tap_pt. Returns the element.
    top_to / bot_to: 'gnd_down'/'gnd_up' draws a ground; None leaves it free."""
    p = elm.Potentiometer().down().anchor("tap").at(tap_pt).label(f"{label}\n{value}", loc=loc, fontsize=8)
    s += p
    for term, target in ((p.start, top_to), (p.end, bot_to)):
        if target == "gnd_down":
            s += elm.Line().at(term).down(s.d.unit * 0.3)
            s += elm.Ground()
        elif target == "gnd_up":
            s += elm.Line().at(term).up(s.d.unit * 0.3)
            s += elm.Ground()
    return p


def draw_channel(s):
    u = s.d.unit
    s.phase(1)

    # ---------------- audio path (top row) ----------------
    s += elm.Dot(open=True).label("CH A IN", loc="left")
    s += elm.Line().right(u * 0.45)                            # short lead from the input port
    s += elm.Dot()                                            # junction: input + R1 + buffer
    s.d.push()
    s += elm.Resistor().down().label(f"R1\n{val('R1')}", fontsize=9)
    s += elm.Ground()
    s.d.pop()
    s += elm.Line().right(u * 0.6)
    op1 = follower(s, "DA1A", s.d.here)
    s += elm.Line().at(op1.out).right(u * 0.6)
    s += elm.Resistor().right().label(f"R4 {val('R4')}", fontsize=9)
    ldr1 = elm.Photoresistor().right().length(u * 1.2).label("VC_A_R", loc="top", fontsize=8, ofst=0.7)
    s += ldr1
    s += elm.Line().right(u * 0.5)
    s += elm.Dot()
    s.d.push()
    s += elm.Capacitor().down().label(f"C11\n{val('C11')}", fontsize=9)
    s += elm.Ground()
    s.d.pop()
    s += elm.Line().right(u * 0.5)
    ldr2 = elm.Photoresistor().right().length(u * 1.2).label("VC_A_L", loc="top", fontsize=8, ofst=0.7)
    s += ldr2
    s += elm.Line().right(u * 0.5)
    s += elm.Dot()
    s.d.push()
    s += elm.Capacitor().down().label(f"C13\n{val('C13')}", fontsize=9)
    s += elm.Ground()
    s.d.pop()
    s.d.push()
    s += elm.Line().right(u * 0.8)
    s += elm.Dot()
    s += elm.Resistor().down().label(f"R3 (Rα)\n{val('R3')}", fontsize=9)
    s += elm.Ground()
    s.d.pop()
    s += elm.Line().right(u * 0.8)
    s += elm.Resistor().right().label(f"R5 {val('R5')}", fontsize=9)
    s += elm.Line().right(u * 0.5)
    op2 = follower(s, "DA1B", s.d.here)
    s += elm.Line().at(op2.out).right(u * 0.5)
    s += elm.Resistor().right().label(f"R_OUT_A {val('R_OUT_A')}", fontsize=9)
    s += elm.Dot(open=True).label("CH A OUT", loc="right")

    # ---------------- vactrol LEDs (below LDRs) ----------------
    led_y = ldr1.center.y - u * 2.4
    half = u * 0.5
    led1 = elm.LED().right().at((ldr1.center.x - half, led_y)).length(u * 1.0)
    s += led1
    led2 = elm.LED().right().at((ldr2.center.x - half, led_y)).length(u * 1.0)
    s += led2
    s += elm.Line().at(led1.end).to(led2.start)
    s += elm.Line().at(led1.start).left(u * 0.5)
    s += elm.Ground()
    s += elm.Line().at(led2.end).right(u * 0.7)
    ld = s.d.here
    s += elm.Dot()                                            # LED_DRIVE_A
    s += elm.EncircleBox([ldr1, led1], padx=0.25, pady=0.35).linestyle("--").color(GREY)
    s += elm.EncircleBox([ldr2, led2], padx=0.25, pady=0.35).linestyle("--").color(GREY)
    s.phase(1)
    s += elm.Label().at((ld.x, ld.y + 0.35)).label("LED_DRIVE_A", fontsize=7, color=GREY)

    ox, oy = ld.x, ld.y

    # ---------------- VD5 zener clamp (LED_DRIVE_A -> GND) ----------------
    s.d.push()
    s += elm.Line().at(ld).right(u * 0.9)
    s += elm.Zener().down().label(f"VD5\n{val('VD5')}", loc="right", fontsize=8)
    s += elm.Ground()
    s.d.pop()

    # ---------------- driver op-amp DA3A + summing bus ----------------
    SBx = ox - 6.0
    row1 = oy - 6.4                                            # MANUAL  (phase 1)
    row2 = row1 - 4.6                                          # CV      (phase 2)
    row3 = row2 - 3.6                                          # STRIKE  (phase 2)

    opd = elm.Opamp(leads=True).anchor("in1").at((SBx + 1.4, row1)).label("DA3A", loc="center", ofst=0, fontsize=9)
    s += opd
    s += elm.Line().at(opd.in1).tox(SBx)                       # in1 <- bus
    s += elm.Dot()
    # feedback R36 over the top
    fby = opd.in1.y + 1.3
    s += elm.Line().at(opd.out).to((opd.out.x, fby))
    s += elm.Resistor().at((opd.out.x, fby)).to((SBx, fby)).label(f"R36 {val('R36')}", fontsize=8)
    s += elm.Line().at((SBx, fby)).to((SBx, opd.in1.y))
    # +in via R37 to GND
    s.d.push()
    s += elm.Line().at(opd.in2).left(u * 0.3)
    s += elm.Resistor().down().label(f"R37\n{val('R37')}", fontsize=8)
    s += elm.Ground()
    s.d.pop()

    # output climb: DRV_OUT_A -> depth pot -> R6 -> LED_DRIVE_A
    s += elm.Line().at(opd.out).tox(ox)
    drv_out = (ox, opd.out.y)
    s += elm.Dot()
    p3 = elm.Potentiometer().up().anchor("start").at(drv_out).label(f"P3 DEPTH\n{POTVAL['P3']}", loc="right", fontsize=8)
    s += p3
    # rheostat: CCW end (top) shorted to the wiper, drawn as a clean orthogonal
    # bracket (not a diagonal). Main current path stays straight up the climb.
    bx = p3.tap.x - 0.4
    s += elm.Line().at(p3.tap).to((bx, p3.tap.y))
    s += elm.Line().to((bx, p3.end.y))
    s += elm.Line().to(p3.end)
    # R6 continues the climb from the top terminal up to LED_DRIVE_A
    s += elm.Resistor().at(p3.end).up().toy(oy).label(f"R6 {val('R6')}", fontsize=8)

    # MANUAL input (row1, phase 1): bus <- R32 <- P2 wiper
    s += elm.Resistor().at((SBx, row1)).left().label(f"R32 {val('R32')}", fontsize=8)
    man_tap = s.d.here
    p2 = vpot(s, "P2 MANUAL", man_tap, POTVAL["P2"], top_to=None, bot_to="gnd_down")
    s += elm.Resistor().at(p2.start).up().label(f"R29 {val('R29')}", fontsize=8)
    s += elm.Vdd().label("+12V")

    # vertical summing bus down to the phase-2 rows
    if s.shows(2):
        s += elm.Line().at((SBx, row1)).to((SBx, row3))

    # ================= PHASE 2 (ping) =================
    if s.shows(2):
        s.phase(2)

        # CV input (row2): bus <- R38 <- P1 wiper ; P1 top <- R16 <- jack, R13 pulldown
        s += elm.Dot().at((SBx, row2))
        s += elm.Resistor().left().label(f"R38 {val('R38')}", fontsize=8)
        s += elm.Line().left(u * 0.6)                          # stagger P1 left of P2
        cv_tap = s.d.here
        p1 = vpot(s, "P1 CV ATTEN", cv_tap, POTVAL["P1"], top_to=None, bot_to="gnd_down")
        s += elm.Line().at(p1.start).up(u * 0.4)
        s += elm.Dot()
        s.d.push()
        s += elm.Resistor().up().label(f"R13 {val('R13')}", loc="top", fontsize=8)  # pulldown
        s += elm.Ground().flip()
        s.d.pop()
        s += elm.Resistor().left().label(f"R16 {val('R16')}", fontsize=8)
        s += elm.Dot(open=True).label("CV A", loc="left")

        # STRIKE input (row3): bus <- R34 <- VD1 <- C15 <- R17 <- jack ; R15 pulldown
        s += elm.Dot().at((SBx, row3))
        s += elm.Resistor().left().label(f"R34 {val('R34')}", fontsize=8)
        s += elm.Dot()
        s.d.push()
        s += elm.Resistor().down().label(f"R15\n{val('R15')}", fontsize=8)
        s += elm.Ground()
        s.d.pop()
        s += elm.Diode().left().label("VD1", fontsize=8)      # cathode at STRIKE_PULSE (right)
        s += elm.Capacitor().left().label(f"C15 {val('C15')}", fontsize=8)
        s += elm.Resistor().left().label(f"R17 {val('R17')}", fontsize=8)
        s += elm.Dot(open=True).label("STRIKE A", loc="left")

        # status LED off DRV_OUT_A: R_STATUS -> LED -> VD7 (3V3 turn-on threshold) -> GND.
        # LED cathode toward the (negative) driver; VD7 band (cathode) toward GND.
        # VD7/VD8 are panel-side parts (rev 0.19), so the value is fixed here, not from JSON.
        s += elm.Resistor().at(drv_out).down().label(f"R_STATUS_A\n{val('R_STATUS_A')}", fontsize=8)
        s += elm.LED().down().reverse().label("LED_STATUS_A", loc="right", fontsize=8)
        s += elm.Zener().down().label("VD7 3V3", loc="right", fontsize=8)
        s += elm.Ground()


def draw_mix(s):
    """Phase 5 — mix output: inverting summer of CHA_OUT + CHB_OUT."""
    u = s.d.unit
    s.phase(5)
    opd = elm.Opamp(leads=True).anchor("in1").at((6, 0)).label("DA4A", loc="center", ofst=0, fontsize=9)
    s += opd
    busx = opd.in1.x - 1.0
    s += elm.Line().at(opd.in1).tox(busx)
    s += elm.Dot()
    # feedback R24 over the top
    fby = opd.in1.y + 1.3
    s += elm.Line().at(opd.out).to((opd.out.x, fby))
    s += elm.Resistor().at((opd.out.x, fby)).to((busx, fby)).label(f"R24 {val('R24')}", fontsize=8)
    s += elm.Line().at((busx, fby)).to((busx, opd.in1.y))
    # CHA_OUT -> R23 -> bus (top row)
    s += elm.Resistor().at((busx, opd.in1.y)).left().label(f"R23 {val('R23')}", fontsize=8)
    s += elm.Line().left(u * 0.5)
    s += elm.Dot(open=True).label("CHA_OUT", loc="left")
    # CHB_OUT -> R26 -> bus (lower row)
    row2 = opd.in1.y - 2.4
    s += elm.Line().at((busx, opd.in1.y)).to((busx, row2))
    s += elm.Resistor().at((busx, row2)).left().label(f"R26 {val('R26')}", fontsize=8)
    s += elm.Line().left(u * 0.5)
    s += elm.Dot(open=True).label("CHB_OUT", loc="left")
    # +in via R28 to GND (straight down, clear of the summing bus)
    s.d.push()
    s += elm.Line().at(opd.in2).down(u * 0.3)
    s += elm.Resistor().down().label(f"R28 {val('R28')}", loc="right", fontsize=8)
    s += elm.Ground()
    s.d.pop()
    # out -> C17 (DC block) -> MIX OUT jack
    s += elm.Line().at(opd.out).right(u * 0.6)
    s += elm.Capacitor().right().label(f"C17 {val('C17')}", fontsize=8)
    s += elm.Dot(open=True).label("MIX OUT", loc="right")


def render(rp, fname, drawer):
    s = Sheet(rp)
    with s.d:
        drawer(s)
    path = os.path.join(OUT, fname)
    s.d.save(path, dpi=150)
    print("wrote", path)


render(1, "phase1_channel.png", draw_channel)
render(2, "phase2_channel.png", draw_channel)
render(5, "phase5_mix.png", draw_mix)

# Channel B is a clone of Channel A. Designator map for the build video caption:
B_MAP = ("Channel B = same circuit, different designators:  "
         "DA1A/B->DA2A/B, DA3A->DA3B, R1->R7, R4->R10, R3->R9, R5->R11, "
         "C11->C12, C13->C14, R6->R12, VD5->VD6, R36->R20, R37->R14, "
         "R29->R30, R32->R33, R16->R22, R13->R19, R38->R39, R17->R25, "
         "C15->C16, R15->R31, VD1->VD2, R34->R35, R_STATUS_A->R_STATUS_B, "
         "VD7->VD8, R_OUT_A->R_OUT_B, P1->P5, P2->P6, P3->P7.")
print(B_MAP)

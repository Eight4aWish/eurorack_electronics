"""Generate the project symbol library (analogue_board.kicad_sym) and footprint library (analogue_board.pretty).

Only parts the KiCad standard library lacks live here: the DAC8568, the two compute modules drawn in
their physical pin order (so the first sheet reads as a pin map), and the n8synth-style edge strips.
Pin names and numbers come from the datasheets; check_pins.py compares them against the transcription.
"""

import os
import sys

from placement import STRIP_OMIT, STRIP_OMIT_INNER
from sexpr import Sym, dumps, find

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "..", "hardware", "analogue_board"))
LIB = "analogue_board"


def S(*a):
    return [Sym(a[0])] + list(a[1:])


def font(size=1.27):
    return S("effects", S("font", S("size", size, size)))


def prop(name, value, at=(0, 0), hide=False, justify=None):
    e = S("effects", S("font", S("size", 1.27, 1.27)))
    if justify:
        e.append(S("justify", Sym(justify)))
    if hide:
        e.append(S("hide", Sym("yes")))
    return [Sym("property"), name, value, S("at", at[0], at[1], 0), e]


def pin(etype, x, y, angle, length, name, number, hidden=False):
    p = [Sym("pin"), Sym(etype), Sym("line"), S("at", x, y, angle), S("length", length)]
    if hidden:
        p.append(S("hide", Sym("yes")))
    p += [[Sym("name"), name, font()], [Sym("number"), str(number), font()]]
    return p


def box_symbol(name, ref, value, footprint, datasheet, description, left=(), right=(), top=(), bottom=(),
               width=15.24, pin_len=2.54, keywords="", fp_filter="", in_bom=True):
    """Rectangular symbol. Each side is a list of (number, name, etype) or None for a one-pitch gap.
    left/right run top to bottom, top/bottom run left to right."""
    rows = max(len(left), len(right), 1)
    half_h = (rows + 1) * 2.54 / 2
    half_h = round(half_h / 2.54 + 0.4999) * 2.54 if half_h % 2.54 else half_h
    half_w = width / 2
    cols = max(len(top), len(bottom), 0)
    if cols:
        half_w = max(half_w, (cols + 1) * 2.54 / 2)
        half_w = round(half_w / 2.54 + 0.4999) * 2.54
    pins = []
    y0 = half_h - 2.54
    for i, p in enumerate(left):
        if p:
            pins.append(pin(p[2], -half_w - pin_len, round(y0 - i * 2.54, 3), 0, pin_len, p[1], p[0], len(p) > 3 and p[3]))
    for i, p in enumerate(right):
        if p:
            pins.append(pin(p[2], half_w + pin_len, round(y0 - i * 2.54, 3), 180, pin_len, p[1], p[0], len(p) > 3 and p[3]))
    x0 = -(len(top) - 1) * 2.54 / 2
    for i, p in enumerate(top):
        if p:
            pins.append(pin(p[2], round(x0 + i * 2.54, 3), half_h + pin_len, 270, pin_len, p[1], p[0]))
    x0 = -(len(bottom) - 1) * 2.54 / 2
    for i, p in enumerate(bottom):
        if p:
            pins.append(pin(p[2], round(x0 + i * 2.54, 3), -half_h - pin_len, 90, pin_len, p[1], p[0]))
    body = [Sym("symbol"), f"{name}_0_1",
            S("rectangle", S("start", -half_w, half_h), S("end", half_w, -half_h),
              S("stroke", S("width", 0.254), S("type", Sym("default"))), S("fill", S("type", Sym("background"))))]
    unit = [Sym("symbol"), f"{name}_1_1"] + pins
    sym = [Sym("symbol"), name, S("pin_names", S("offset", 1.016)), S("exclude_from_sim", Sym("no")),
           S("in_bom", Sym("yes" if in_bom else "no")), S("on_board", Sym("yes")),
           prop("Reference", ref, (-half_w, half_h + 1.27), justify="left"),
           prop("Value", value, (-half_w, -half_h - 1.27), justify="left"),
           prop("Footprint", footprint, hide=True), prop("Datasheet", datasheet, hide=True),
           prop("Description", description, hide=True)]
    if keywords:
        sym.append(prop("ki_keywords", keywords, hide=True))
    if fp_filter:
        sym.append(prop("ki_fp_filters", fp_filter, hide=True))
    sym += [body, unit, S("embedded_fonts", Sym("no"))]
    return sym


# ------------------------------------------------------------------ the parts

def dac8568():
    # TI SBAS430F, PW (TSSOP-16) pinout
    return box_symbol(
        "DAC8568xPW", "U", "DAC8568IAPWR", "Package_SO:TSSOP-16_4.4x5mm_P0.65mm",
        "https://www.ti.com/lit/ds/symlink/dac8568.pdf",
        "16-bit 8-channel voltage-output DAC, SPI, internal 2.5 V reference, TSSOP-16",
        left=[("2", "~{SYNC}", "input"), ("16", "SCLK", "input"), ("15", "DIN", "input"), None,
              ("1", "~{LDAC}", "input"), ("9", "~{CLR}", "input"), None, ("8", "VREFIN/VREFOUT", "bidirectional")],
        right=[("4", "VOUTA", "output"), ("13", "VOUTB", "output"), ("5", "VOUTC", "output"), ("12", "VOUTD", "output"),
               ("6", "VOUTE", "output"), ("11", "VOUTF", "output"), ("7", "VOUTG", "output"), ("10", "VOUTH", "output")],
        top=[("3", "AVDD", "power_in")], bottom=[("14", "GND", "power_in")], width=30.48,
        keywords="DAC 16-bit octal SPI reference", fp_filter="TSSOP*4.4x5mm*P0.65mm*")


PICO2_PINS = {  # Raspberry Pi Pico 2 datasheet, pinout figure
    1: "GP0", 2: "GP1", 3: "GND", 4: "GP2", 5: "GP3", 6: "GP4", 7: "GP5", 8: "GND", 9: "GP6", 10: "GP7",
    11: "GP8", 12: "GP9", 13: "GND", 14: "GP10", 15: "GP11", 16: "GP12", 17: "GP13", 18: "GND", 19: "GP14", 20: "GP15",
    21: "GP16", 22: "GP17", 23: "GND", 24: "GP18", 25: "GP19", 26: "GP20", 27: "GP21", 28: "GND", 29: "GP22", 30: "RUN",
    31: "GP26", 32: "GP27", 33: "AGND", 34: "GP28", 35: "ADC_VREF", 36: "3V3_OUT", 37: "3V3_EN", 38: "GND", 39: "VSYS", 40: "VBUS",
}


def _module_type(name):
    if name in ("GND", "AGND"):
        return "power_in"
    if name in ("VSYS", "VIN"):
        return "power_in"
    if name in ("3V3_OUT", "3V3", "VBUS"):
        return "power_out"
    if name in ("RUN", "3V3_EN"):
        return "input"
    if name == "ADC_VREF":
        return "passive"
    return "bidirectional"


def pico2():
    left = [(str(n), PICO2_PINS[n], _module_type(PICO2_PINS[n])) for n in range(1, 21)]
    right = [(str(n), PICO2_PINS[n], _module_type(PICO2_PINS[n])) for n in range(40, 20, -1)]
    return box_symbol("RaspberryPi_Pico2", "A", "Raspberry Pi Pico 2", f"{LIB}:Pico2_Socket",
                      "https://datasheets.raspberrypi.com/pico/pico-2-datasheet.pdf",
                      "Raspberry Pi Pico 2 (RP2350) on 2x20 female headers, drawn in physical pin order (top view, USB at top)",
                      left=left, right=right, width=30.48, in_bom=False)


# Teensy 4.1, PJRC pinout card, top view with USB at the top.
TEENSY41_LEFT = ["GND", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "3V3",
                 "24", "25", "26", "27", "28", "29", "30", "31", "32"]
TEENSY41_RIGHT = ["VIN", "GND", "3V3", "23", "22", "21", "20", "19", "18", "17", "16", "15", "14", "13", "GND",
                  "41", "40", "39", "38", "37", "36", "35", "34", "33"]


def teensy41_pins():
    """Footprint pad number -> label. Pads run counter-clockwise from the top-left (pad 1 = left GND)."""
    pins = {}
    for i, lab in enumerate(TEENSY41_LEFT):
        pins[i + 1] = lab
    for i, lab in enumerate(TEENSY41_RIGHT):
        pins[48 - i] = lab
    return pins


def _teensy_name(lab):
    return lab if not lab.isdigit() else f"D{lab}"


def teensy41():
    pins = teensy41_pins()
    left = [(str(n), _teensy_name(pins[n]), _module_type(_teensy_name(pins[n]))) for n in range(1, 25)]
    right = [(str(n), _teensy_name(pins[n]), _module_type(_teensy_name(pins[n]))) for n in range(48, 24, -1)]
    return box_symbol("Teensy41", "A", "Teensy 4.1", f"{LIB}:Teensy41_Socket",
                      "https://www.pjrc.com/store/teensy41.html",
                      "PJRC Teensy 4.1 on 2x24 female headers (outer pins only), physical pin order (top view, USB at top)",
                      left=left, right=right, width=30.48, in_bom=False)


def edge_strip():
    right = [(str(n), str(n), "passive") for n in range(1, 41)]
    return box_symbol("EdgeStrip_40", "J", "EdgeStrip_40", f"{LIB}:EdgeStrip_40_Left",
                      "docs/n8synth_platform.md",
                      "n8synth-style edge strip: 40 positions, each an outer hole (deck header) joined to an inner wiring hole",
                      right=right, width=7.62, in_bom=False)


def write_symbols():
    lib = [Sym("kicad_symbol_lib"), S("version", 20241209), S("generator", "analogue_board_make_library"),
           S("generator_version", "9.0"), dac8568(), pico2(), teensy41(), edge_strip()]
    path = os.path.join(OUT, f"{LIB}.kicad_sym")
    with open(path, "w", encoding="utf-8") as f:
        f.write(dumps(lib) + "\n")
    return path


# ------------------------------------------------------------------ footprints

def fp_text(kind, text, at, layer, hide=False):
    e = S("effects", S("font", S("size", 1, 1), S("thickness", 0.15)))
    node = [Sym("property"), kind, text, S("at", at[0], at[1], 0), S("layer", layer)]
    if hide:
        node.append(S("hide", Sym("yes")))
    return node + [S("uuid", "00000000-0000-0000-0000-000000000000"), e]


def pad(number, x, y, shape="circle", size=1.7, drill=1.0):
    return [Sym("pad"), str(number), Sym("thru_hole"), Sym(shape), S("at", round(x, 3), round(y, 3)),
            S("size", size, size), S("drill", drill), S("layers", "*.Cu", "*.Mask"), S("remove_unused_layers", Sym("no"))]


def rect(layer, a, b, width=0.12):
    return [Sym("fp_rect"), S("start", round(a[0], 3), round(a[1], 3)), S("end", round(b[0], 3), round(b[1], 3)),
            S("stroke", S("width", width), S("type", Sym("solid"))), S("fill", Sym("no")), S("layer", layer)]


def footprint(name, descr, pads, outline, courtyards, silk=True):
    """`courtyards` is a list of rectangles: a module socket's courtyard is its two header rows only,
    because low parts may sit under the module (the outline stays on F.Fab)."""
    node = [Sym("footprint"), name, S("version", 20241229), S("generator", "analogue_board_make_library"),
            S("generator_version", "9.0"), S("layer", "F.Cu"), S("descr", descr),
            fp_text("Reference", "REF**", (outline[0][0], outline[0][1] - 1.5), "F.SilkS"),
            fp_text("Value", name, (outline[0][0], outline[1][1] + 1.5), "F.Fab"),
            S("attr", Sym("through_hole"))]
    if silk:
        node.append(rect("F.SilkS", *outline))
    node.append(rect("F.Fab", *outline, width=0.1))
    node += [rect("F.CrtYd", *c, width=0.05) for c in courtyards]
    node += pads
    node.append(S("embedded_fonts", Sym("no")))
    return node


def module_socket(name, descr, rows, row_spacing, outline_wh, first_pad_offset, omit=()):
    """Two rows of `rows` holes; pad 1 top-left, numbering counter-clockwise (left down, right up).
    `omit`: module pins with no hole, a run at the far end of each row that the board never uses,
    so the female headers can be shorter and the area under them is free."""
    pads = []
    for i in range(rows):
        if i + 1 not in omit:
            pads.append(pad(i + 1, 0, i * 2.54, "rect" if i == 0 else "circle"))
        if 2 * rows - i not in omit:
            pads.append(pad(2 * rows - i, row_spacing, i * 2.54))
    w, h = outline_wh
    x0 = row_spacing / 2 - w / 2
    y0 = -first_pad_offset
    # the header bodies, exactly one pitch wide (the Pico's and Teensy's left rows sit one pitch
    # apart), as long as the holes each row keeps
    rows_cy = []
    for cx in (0, row_spacing):
        ys = [float(find(p, "at")[2]) for p in pads if abs(float(find(p, "at")[1]) - cx) < 0.01]
        rows_cy.append(((cx - 1.27, min(ys) - 1.27), (cx + 1.27, max(ys) + 1.27)))
    return footprint(name, descr, pads, ((x0, y0), (x0 + w, y0 + h)), rows_cy)


def edge_strip_fp(name, inner_dx, omit=(), omit_inner=(), descr=""):
    """40 doublets: outer hole (deck header) and inner wiring hole per position, same pad number.
    `omit`: positions with no holes at all, where no deck header ever sits. `omit_inner`: positions
    that keep only the outer hole (a header pin no deck cell uses). Each column's courtyard covers
    only the holes it keeps, so the board where holes are left out is free for parts."""
    pads = []
    for n in range(1, 41):
        if n in omit:
            continue
        y = (n - 1) * 2.54
        pads.append(pad(n, 0, y, "rect" if n == 1 else "circle"))
        if n not in omit_inner:
            pads.append(pad(n, inner_dx, y))

    # one courtyard rectangle per run of positions in the same state (both holes, outer only),
    # 0.005 mm apart where runs meet: KiCad rejects courtyard shapes that touch
    def state(n):
        return None if (n < 1 or n > 40 or n in omit) else ("outer" if n in omit_inner else "both")

    xs = sorted([0, inner_dx])
    boxes, n = [], 1
    while n <= 40:
        s = state(n)
        if s is None:
            n += 1
            continue
        m = n
        while state(m + 1) == s:
            m += 1
        top = (n - 1) * 2.54 - 1.27 + (0.005 if state(n - 1) else 0)
        bottom = (m - 1) * 2.54 + 1.27 - (0.005 if state(m + 1) else 0)
        x0, x1 = (xs[0] - 1.27, xs[1] + 1.27) if s == "both" else (-1.27, 1.27)
        boxes.append(((x0, top), (x1, bottom)))
        n = m + 1
    outline = ((xs[0] - 1.27, -1.27), (xs[1] + 1.27, 39 * 2.54 + 1.27))
    return footprint(name, descr or "n8synth edge strip: outer hole (deck header) and inner wiring hole per position, "
                     "same pad number", pads, outline, boxes)


def wiring_holes_fp(n):
    """A column of n bare plated holes on 2.54 mm, courtyard exactly one pitch wide, so columns can sit
    side by side and beside the edge strips (the wiring field)."""
    pads = [pad(i + 1, 0, i * 2.54, "rect" if i == 0 else "circle") for i in range(n)]
    box = ((-1.27, -1.27), (1.27, (n - 1) * 2.54 + 1.27))
    return footprint(f"WiringHoles_1x{n:02d}", f"Wiring field: {n} bare plated holes, 2.54 mm pitch, pad 1 square",
                     pads, box, [box])


def write_footprints():
    d = os.path.join(OUT, f"{LIB}.pretty")
    os.makedirs(d, exist_ok=True)
    fps = [
        module_socket("Pico2_Socket", "Raspberry Pi Pico 2 on 2x20 female headers, 17.78 mm rows. Overlay with the Teensy footprint is settled at checkpoint 2.",
                      20, 17.78, (21.0, 51.0), (51.0 - 19 * 2.54) / 2),
        module_socket("Teensy41_Socket", "Teensy 4.1 on 1x19 + 1x20 female headers from the USB end, 15.24 mm rows. "
                      "No holes for pins 20-28 (D28-D36, never used on this board): fit the Teensy with headers "
                      "on pins 1-19 and 29-48 only.",
                      24, 15.24, (17.78, 60.96), (60.96 - 23 * 2.54) / 2, omit=range(20, 29)),
        edge_strip_fp("EdgeStrip_40_Left", 2.54),
        # the right strip serves only the 10HP deck, whose headers sit at 1-10, 16-25 and 31-40:
        # positions 11-15 and 26-30 never carry a header, so they have no holes, and 10, 16 and 31
        # (header pins no cell uses) keep only the outer hole (placement.STRIP_OMIT, STRIP_OMIT_INNER)
        edge_strip_fp("EdgeStrip_40_Right", -2.54, omit=STRIP_OMIT["right"], omit_inner=STRIP_OMIT_INNER["right"],
                      descr="n8synth edge strip, right (10HP only): doublets at positions 1-9, 17-25 and 32-40; "
                            "outer hole only at 10, 16 and 31; none at 11-15 and 26-30"),
    ] + [wiring_holes_fp(n) for n in range(1, 15)]
    for fp in fps:
        with open(os.path.join(d, fp[1] + ".kicad_mod"), "w", encoding="utf-8") as f:
            f.write(dumps(fp) + "\n")
    return d


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    print(write_symbols())
    print(write_footprints())

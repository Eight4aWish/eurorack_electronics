"""A 1:1 printout of each Rev A board's outline, edge strips, module socket, USB plug keep-out
and power header, to lay real parts on.

    python3 tools/analogue_board/printout.py

Writes hardware/analogue_board/boards_printout.pdf (A4, one page: the Pico 2 board, the same
board with an ESP32-P4, the Teensy board). checkpoint2_printout.pdf beside it is the record of
checkpoint 2, when both modules shared one board; this script no longer writes it. Hole
positions come from the project's KiCad footprints and KiCad's own IDC header footprint, placed
by placement.py. No dependencies beyond Python: the PDF is written directly, in millimetres.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import placement as P  # noqa: E402
import variant  # noqa: E402

OUT = os.path.join(variant.SHARED, "boards_printout.pdf")
A4 = (210.0, 297.0)
MM = 72 / 25.4

# Helvetica advance widths (per 1000 em), ASCII 32-126, from the Adobe core-font metrics
_HW = [278, 278, 355, 556, 556, 889, 667, 191, 333, 333, 389, 584, 278, 333, 278, 278] + [556] * 10 + \
      [278, 278, 584, 584, 584, 556, 1015, 667, 667, 722, 722, 667, 611, 778, 722, 278, 500, 667, 556, 833, 722,
       778, 667, 778, 722, 667, 611, 722, 667, 944, 667, 667, 611, 278, 278, 278, 469, 556, 333, 556, 556, 500,
       556, 556, 278, 556, 556, 222, 222, 500, 222, 833, 556, 556, 556, 556, 333, 500, 278, 556, 500, 722, 500,
       500, 500, 334, 260, 334, 584]

INK = (0.1, 0.1, 0.1)
GREY = (0.55, 0.55, 0.55)
COL = {"pico": (0.10, 0.36, 0.80), "p4": (0.50, 0.22, 0.66), "teensy": (0.05, 0.55, 0.25),
       "header": (0.85, 0.45, 0.0), "warn": (0.80, 0.12, 0.10), "ok": (0.05, 0.50, 0.20)}
NAMES = {"pico": "Raspberry Pi Pico 2", "p4": "Waveshare ESP32-P4-WIFI6", "teensy": "Teensy 4.1"}


def text_width(s, size, bold=False):
    return sum(_HW[ord(c) - 32] for c in s) / 1000 * size * (1.06 if bold else 1.0)


class Page:
    """Drawing operations in mm, origin top-left, y down."""

    def __init__(self):
        self.ops = [f"{MM:.6f} 0 0 {-MM:.6f} 0 {A4[1] * MM:.4f} cm", "1 J 1 j"]

    def _style(self, stroke, fill, lw, dash, alpha):
        o = ["q"]
        if alpha is not None:
            o.append(f"/A{int(alpha * 100)} gs")
        if stroke:
            o.append("%.3f %.3f %.3f RG %.3f w" % (*stroke, lw))
            o.append("[%s] 0 d" % " ".join(f"{d:.2f}" for d in dash) if dash else "[] 0 d")
        if fill:
            o.append("%.3f %.3f %.3f rg" % fill)
        return o

    def _paint(self, stroke, fill):
        return "B" if stroke and fill else ("f" if fill else "S")

    def rect(self, x0, y0, x1, y1, stroke=INK, fill=None, lw=0.2, dash=None, alpha=None):
        o = self._style(stroke, fill, lw, dash, alpha)
        o += [f"{x0:.3f} {y0:.3f} {x1 - x0:.3f} {y1 - y0:.3f} re", self._paint(stroke, fill), "Q"]
        self.ops += o

    def line(self, a, b, stroke=INK, lw=0.2, dash=None):
        self.ops += self._style(stroke, None, lw, dash, None) + [f"{a[0]:.3f} {a[1]:.3f} m {b[0]:.3f} {b[1]:.3f} l S", "Q"]

    def circle(self, cx, cy, r, stroke=INK, fill=None, lw=0.15):
        k = 0.552285 * r
        o = self._style(stroke, fill, lw, None, None)
        o.append(f"{cx + r:.3f} {cy:.3f} m")
        for (x1, y1, x2, y2, x3, y3) in [(cx + r, cy + k, cx + k, cy + r, cx, cy + r),
                                         (cx - k, cy + r, cx - r, cy + k, cx - r, cy),
                                         (cx - r, cy - k, cx - k, cy - r, cx, cy - r),
                                         (cx + k, cy - r, cx + r, cy - k, cx + r, cy)]:
            o.append(f"{x1:.3f} {y1:.3f} {x2:.3f} {y2:.3f} {x3:.3f} {y3:.3f} c")
        o += [self._paint(stroke, fill), "Q"]
        self.ops += o

    def text(self, x, y, s, size=2.6, bold=False, color=INK, anchor="left"):
        if any(ord(c) < 32 or ord(c) > 126 for c in s):
            raise ValueError(f"ASCII only in the printout: {s!r}")
        if anchor != "left":
            x -= text_width(s, size, bold) * (0.5 if anchor == "centre" else 1.0)
        esc = s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        self.ops += ["q", "%.3f %.3f %.3f rg" % color, "BT", f"/F{2 if bold else 1} 1 Tf",
                     f"{size:.3f} 0 0 {-size:.3f} {x:.3f} {y:.3f} Tm", f"({esc}) Tj", "ET", "Q"]

    def para(self, x, y, lines, size=2.6, lead=1.42, bold_first=False, color=INK):
        for i, l in enumerate(lines):
            self.text(x, y + i * size * lead, l, size, bold=bold_first and i == 0, color=color)
        return y + len(lines) * size * lead


def write_pdf(pages, path):
    objs = ["<< /Type /Catalog /Pages 2 0 R >>", None,
            "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
            "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>"]
    alphas = " ".join(f"/A{a} << /ca {a / 100:.2f} >>" for a in (12, 18, 25))
    res = f"<< /Font << /F1 3 0 R /F2 4 0 R >> /ExtGState << {alphas} >> >>"
    kids = []
    for pg in pages:
        stream = "\n".join(pg.ops).encode("latin-1")
        objs.append(f"<< /Length {len(stream)} >>\nstream\n".encode("latin-1") + stream + b"\nendstream")
        objs.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {A4[0] * MM:.3f} {A4[1] * MM:.3f}] "
                    f"/Resources {res} /Contents {len(objs)} 0 R >>")
        kids.append(len(objs))
    objs[1] = f"<< /Type /Pages /Kids [{' '.join(f'{k} 0 R' for k in kids)}] /Count {len(kids)} >>"
    out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = []
    for i, o in enumerate(objs, 1):
        offsets.append(len(out))
        body = o if isinstance(o, bytes) else o.encode("latin-1")
        out += f"{i} 0 obj\n".encode() + body + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
    out += b"".join(f"{o:010d} 00000 n \n".encode() for o in offsets)
    out += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R /Info << /Title (Analogue board Rev A - checkpoint 2 printout) >> >>\n".encode()
    out += f"startxref\n{xref}\n%%EOF\n".encode()
    with open(path, "wb") as f:
        f.write(out)


# ------------------------------------------------------------------ board drawing
def draw_board(pg, ox, oy, lay, modules, number_strips=True, shared=(), annotate=False):
    X = lambda x: ox + x  # noqa: E731
    Y = lambda y: oy + y  # noqa: E731
    pg.rect(X(0), Y(0), X(P.BOARD_W), Y(P.BOARD_H), stroke=INK, lw=0.35)
    # edge strips: deck-cell bands, deck (outer) holes filled, wiring (inner) holes open
    for side, s in P.STRIPS.items():
        for a, b in P.DECK_CELLS:
            pg.rect(X(s["outer"] - 1.3), Y(P.strip_y(a) - 1.3), X(s["outer"] + 1.3), Y(P.strip_y(b) + 1.3),
                    stroke=None, fill=(0.86, 0.86, 0.86))
        for n in range(1, 41):
            if n in P.STRIP_OMIT[side]:
                continue
            y = Y(P.strip_y(n))
            pg.circle(X(s["outer"]), y, 0.85, stroke=GREY, lw=0.12)
            pg.circle(X(s["outer"]), y, 0.5, stroke=None, fill=(0.25, 0.25, 0.25))
            if n not in P.STRIP_OMIT_INNER[side]:
                pg.circle(X(s["inner"]), y, 0.85, stroke=GREY, lw=0.12)
                pg.circle(X(s["inner"]), y, 0.12, stroke=None, fill=GREY)
        if number_strips:
            for n in (1, 10, 16, 25, 31, 40):
                y = Y(P.strip_y(n)) + 0.55
                if side == "left":
                    pg.text(X(-0.9), y, str(n), 1.6, color=GREY, anchor="right")
                else:
                    pg.text(X(P.BOARD_W + 0.9), y, str(n), 1.6, color=GREY)
    # keep-outs first, so everything else draws over them
    for key in modules:
        m = lay[key]
        k = m["keepout"]
        pg.rect(X(k[0]), Y(k[1]), X(k[2]), Y(k[3]), stroke=None, fill=COL[key], alpha=0.12)
        pg.rect(X(k[0]), Y(k[1]), X(k[2]), Y(k[3]), stroke=COL[key], lw=0.2, dash=(1.2, 0.8))
    # power header: KiCad's own outline (with the key notch) and pads
    hp, hl = P.header()
    for a, b in hl:
        pg.line((X(a[0]), Y(a[1])), (X(b[0]), Y(b[1])), stroke=COL["header"], lw=0.25)
    for n, x, y, shape in hp:
        if n == "1":
            pg.rect(X(x - 0.85), Y(y - 0.85), X(x + 0.85), Y(y + 0.85), stroke=COL["header"], lw=0.15)
        else:
            pg.circle(X(x), Y(y), 0.85, stroke=COL["header"], lw=0.15)
        pg.circle(X(x), Y(y), 0.3, stroke=None, fill=COL["header"])
    pg.text(X(P.HEADER_PIN1[0]) - 1.2, Y(P.HEADER_PIN1[1]) + 0.6, "1", 1.6, bold=True, color=COL["header"], anchor="right")
    # modules: bodies, USB connectors, holes
    for key in modules:
        m = lay[key]
        b = m["body"]
        c = COL[key]
        pg.rect(X(b[0]), Y(b[1]), X(b[2]), Y(b[3]), stroke=c, lw=0.3, dash=(2.0, 1.0))
        cx = (b[0] + b[2]) / 2
        uw, depth, over = (9.0, 7.0, 0.8) if key == "p4" else (8.0, 5.5, 1.0)
        pg.rect(X(cx - uw / 2), Y(b[3] - depth), X(cx + uw / 2), Y(b[3] + over), stroke=c, fill=(1, 1, 1), lw=0.25)
        pg.text(X(cx), Y(b[3] - depth / 2) + 0.7, "USB-C" if key == "p4" else "USB", 1.9, bold=True, color=c, anchor="centre")
        if annotate and key == "p4":
            pg.text(X(cx), Y(b[1] + 5.5), "antenna end", 1.7, color=c, anchor="centre")
            pg.text(X(cx), Y(b[3] - depth - 4.2), "microSD underneath,", 1.4, color=c, anchor="centre")
            pg.text(X(cx), Y(b[3] - depth - 2.0), "card in at this end", 1.4, color=c, anchor="centre")
        if key == "teensy":
            # the card in its microSD socket stands TEENSY_SD_CARD past the far end (measured)
            pg.rect(X(cx - 5.5), Y(b[1] - P.TEENSY_SD_CARD), X(cx + 5.5), Y(b[1]), stroke=c, fill=c, lw=0.2, alpha=0.18)
            pg.rect(X(cx - 5.5), Y(b[1] - P.TEENSY_SD_CARD), X(cx + 5.5), Y(b[1]), stroke=c, lw=0.2)
        if annotate and key == "teensy":
            pg.rect(X(cx - 5.5), Y(b[1] + 0.4), X(cx + 5.5), Y(b[1] + 11.5), stroke=c, lw=0.2, dash=(0.6, 0.6))
            pg.text(X(cx), Y(b[1] + 5.4), "microSD", 1.5, color=c, anchor="centre")
            pg.text(X(cx), Y(b[1] + 7.6), "(approx.)", 1.4, color=c, anchor="centre")
            pg.text(X(cx), Y(b[1] - 0.9), "card, 3 mm", 1.3, color=c, anchor="centre")
        if key != "p4" or "pico" not in modules:
            for n, x, y, shape in m["pads"]:
                if n == "1":
                    pg.rect(X(x - 0.85), Y(y - 0.85), X(x + 0.85), Y(y + 0.85), stroke=c, lw=0.2)
                else:
                    pg.circle(X(x), Y(y), 0.85, stroke=c, lw=0.15)
                pg.circle(X(x), Y(y), 0.3, stroke=None, fill=c)
            p1 = [p for p in m["pads"] if p[0] == "1"][0]
            pg.text(X(p1[1]) + 2.2, Y(p1[2]) + 0.6, "1", 1.6, bold=True, color=c)  # just outside the body
    for (_pn, _tn, x, y, bad) in shared:
        pg.circle(X(x), Y(y), 1.25, stroke=COL["warn"] if bad else COL["ok"], lw=0.3)


def scale_bar(pg, x, y):
    pg.line((x, y), (x + 100, y), lw=0.3)
    for i in range(0, 101, 5):
        h = 2.0 if i % 10 == 0 else 1.0
        pg.line((x + i, y), (x + i, y - h), lw=0.2)
    for i in (0, 50, 100):
        pg.text(x + i, y + 3.0, str(i), 2.0, anchor="centre")
    pg.text(x + 104, y + 0.8, "This bar must measure 100 mm. If not, reprint at 100% / Actual size,", 2.2)
    pg.text(x + 104, y + 4.0, "with fit-to-page and scaling turned off.", 2.2)


def footer(pg, n, total):
    pg.text(15, 291, f"Analogue boards Rev A. Generated by tools/analogue_board/printout.py from the KiCad "
                     f"footprints. Eight4aWish, CC BY-SA 4.0.   Page {n} of {total}", 1.8, color=GREY)


def legend(pg, x, y, items):
    for kind, color, label in items:
        if kind == "hole":
            pg.circle(x + 1.5, y - 0.8, 0.85, stroke=color, lw=0.15)
            pg.circle(x + 1.5, y - 0.8, 0.3, stroke=None, fill=color)
        elif kind == "body":
            pg.rect(x, y - 2.0, x + 3.0, y + 0.4, stroke=color, lw=0.3, dash=(1.0, 0.6))
        elif kind == "zone":
            pg.rect(x, y - 2.0, x + 3.0, y + 0.4, stroke=None, fill=color, alpha=0.18)
            pg.rect(x, y - 2.0, x + 3.0, y + 0.4, stroke=color, lw=0.2, dash=(0.8, 0.5))
        elif kind == "deck":
            pg.rect(x, y - 2.0, x + 3.0, y + 0.4, stroke=None, fill=(0.86, 0.86, 0.86))
            pg.circle(x + 1.5, y - 0.8, 0.5, stroke=None, fill=(0.25, 0.25, 0.25))
        elif kind == "wire":
            pg.circle(x + 1.5, y - 0.8, 0.85, stroke=GREY, lw=0.12)
        pg.text(x + 5.0, y, label, 2.4)
        y += 4.4
    return y


def fmt(v):
    return f"{v:.1f}"


# ------------------------------------------------------------------ pages
def page_singles(lay):
    pg = Page()
    pg.text(15, 14, "Rev A: two boards, one module each, to lay real parts on", 4.2, bold=True)
    pg.text(15, 19.5, "Outward face, seen from above. Each module is centred on its board; header and edge strips "
                      "are the same on both.", 2.5)
    xs = [14, 81, 148]
    oy = 34
    for x, key in zip(xs, ("pico", "p4", "teensy")):
        pg.text(x + P.BOARD_W / 2, oy - 4.0, NAMES[key], 2.8, bold=True, color=COL[key], anchor="centre")
        draw_board(pg, x, oy, lay, [key], number_strips=(key == "pico"), annotate=True)
        m = lay[key]
        notes = {
            "pico": ["Body 21 x 51 mm, far end 17.4 mm", "down (room for the P4).",
                     f"USB edge at {fmt(m['usb_y'])} mm; keep-out", f"to {fmt(m['keepout'][3])} mm."],
            "p4": ["Body 21 x 71 mm in the Pico's holes.", "Far (antenna) end 0.5 mm from the",
                   f"top edge. USB-C edge at {fmt(m['usb_y'])} mm;", f"keep-out to {fmt(m['keepout'][3])} mm.",
                   "USB-C is serial only (CH343).", "Bridge JP201 when fitted."],
            "teensy": [f"Body 17.8 x 61 mm, far end {fmt(m['body'][1])} mm", "down, so a microSD card (3 mm)",
                       "ends 0.5 mm from the top edge.",
                       f"USB edge at {fmt(m['usb_y'])} mm; keep-out", f"to {fmt(m['keepout'][3])} mm.",
                       "All 48 holes: full-length headers.", "Centred: 3.8 mm right of the",
                       "checkpoint 2 print.", "Cut the VIN-VUSB pads first."],
        }[key]
        pg.para(x, oy + P.BOARD_H + 7, notes, 2.3, lead=1.4)
    pg.para(14, 178, [
        "Laying the parts",
        "- Face up, USB end down, pin 1 (the square hole) at the USB end. The pins should sit on the dots.",
        "- The keep-out is where the plug goes when the module is up on its headers; anything in it taller",
        "  than about 8 mm stops the plug. Try your real cables: a right-angle plug may need less room.",
        "- The P4's microSD card goes in at the USB end, under the board, and is meant to stay in.",
        "- Edge-strip numbers are on the left-hand board; the grey bands are the deck cells.",
        "- The Pico 2 and the ESP32-P4 share one board (the first two outlines); the Teensy has its own.",
    ], 2.5, lead=1.45, bold_first=True)
    scale_bar(pg, 18, 272)
    return pg


def main():
    pages = [page_singles(P.boards_layout())]
    for i, pg in enumerate(pages, 1):
        footer(pg, i, len(pages))
    write_pdf(pages, OUT)
    print(OUT)


if __name__ == "__main__":
    main()

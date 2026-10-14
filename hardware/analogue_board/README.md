# Analogue board, Rev A

A general-purpose Eurorack I/O board: a Raspberry Pi Pico 2 or Teensy 4.1 on headers on one side,
an n8synth Control Deck on the other, and every audio, CV, gate, pot and display interface in
between. The design brief and every decision behind it are in
[`docs/analogue_board_spec.md`](../../docs/analogue_board_spec.md).

**Status:** checkpoint 1 (schematic), drafted 2026-10-14, awaiting review.

## What's here

| File | What it is |
|---|---|
| [`analogue_board_schematic.pdf`](analogue_board_schematic.pdf) | The schematic, 9 A3 sheets. Sheet 1 is the module pin map. |
| [`output/checks.md`](output/checks.md) | Every checkpoint-1 check and its result: ERC, netlist, pins against datasheets, footprints, decoupling, diode orientation |
| `output/erc.rpt`, `output/analogue_board.net`, `output/analogue_board_bom.csv` | KiCad's ERC report, netlist and grouped BOM with LCSC numbers |
| `analogue_board.kicad_pro`, `*.kicad_sch` | The KiCad 9 project |
| `analogue_board.kicad_sym`, `analogue_board.pretty/` | Project symbols (DAC8568, Pico 2, Teensy 4.1, edge strip) and footprints (module sockets, edge strips) |
| [`LICENSE`](LICENSE) | CC BY-SA 4.0 |

## The schematic is generated

The `.kicad_sch` files are written by [`tools/analogue_board/build.py`](../../tools/analogue_board/build.py).
Change the generator, not the KiCad files, until the schematic is signed off. After that the
KiCad files become the source and the generator is retired.

```sh
python3 tools/analogue_board/build.py
```

One run regenerates the libraries and all nine sheets. It then runs KiCad's ERC and exports the
PDF, netlist and BOM through `kicad-cli`, and finally runs the checks. It exits non-zero if any
check fails. Needs KiCad 9 at `/Applications/KiCad` and Python 3, nothing else.

| Generator file | Holds |
|---|---|
| `design.py` | Pin map, root sheet, power sheet |
| `design_analog.py` | Codec and audio, CV jacks and ADC, CV DAC |
| `design_digital.py` | Pots and gate outs, expander/I2C/LEDs, gate ins and jack detect, edge strips |
| `parts.py` | Every part: symbol, footprint, LCSC number, datasheet |
| `datasheet_pins.json` | Each IC's pinout transcribed from its datasheet, independently of KiCad's library. `checks.py` compares the two. |
| `checks.py` | The checkpoint-1 checks |

The netlist check works from intent. Every connection the generator draws is also recorded as
"pin X belongs on net Y". The check then compares those records with the netlist KiCad computes.
A wire that lands on the wrong pin, two nets that touch, or a pin nobody meant to connect all
fail the build.

## Reviewing checkpoint 1

The spec's §15 lists every decision taken at schematic stage that it didn't already settle. Each
is marked [proposed] until you agree. The ones that change the spec:

- the buck is a TPS54308 (forced PWM) rather than the TPS54202 or AP63205;
- the 3.3 V rails use XC6206 LDOs rather than AMS1117s;
- the gate-input comparators run from +12 V;
- the LM4040 is dropped.

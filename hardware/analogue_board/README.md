# Analogue boards, Rev A

General-purpose Eurorack I/O boards. A compute module sits on headers on one side, an n8synth
Control Deck on the other, and every audio, CV, gate, pot and display interface sits in between.
Rev A is **two boards** from one design (2026-10-16):

| Board | Module | Folder |
|---|---|---|
| Pico board | Raspberry Pi Pico 2, or a Waveshare ESP32-P4-WIFI6 in its pinout | [`pico/`](pico/) |
| Teensy board | Teensy 4.1, all 48 pins on standard headers | [`teensy/`](teensy/) |

Both boards share the peripheral circuits, pin functions, wiring field, edge strips and power
corner, so firmware and panel wiring are the same on both. The design brief and every decision
behind it are in [`docs/analogue_board_spec.md`](../../docs/analogue_board_spec.md).

Two more builds from the same generator are routing trials, not boards to order:

| Trial | What it is | Folder |
|---|---|---|
| Shared board | Both module footprints interleaved on one board, as checkpoint 2 had it; the Teensy on shortened headers | [`shared/`](shared/) |
| Core board | The Pico board without the fixed-direction CV channels, TRS MIDI or the Qwiic socket, with six pots; parts 0.4 mm apart, 0.127 mm signal rules. The first to route (spec §14); its routed board is in [`pico_core/routed_trial/`](pico_core/routed_trial/) | [`pico_core/`](pico_core/) |
| Shared core board | Both module sockets (the Teensy on full headers), TRS MIDI, the display on I2C holes, six switchable CV jacks, six pots, four gates each way. Four routes in a row ended 2 connections short, a different 2 each time; its first routed board is in [`shared_core/routed_trial/`](shared_core/routed_trial/) | [`shared_core/`](shared_core/) |
| **Pico core board with MIDI** | The same feature set on a Pico 2 / ESP32-P4 board alone: module 8 mm lower, no bus test points, +5VD plane on In4, top of the board re-laid by David with no chip over another. **Fully routed** (0 unconnected, 0 copper faults); routed board in [`pico_core_midi/routed_trial/`](pico_core_midi/routed_trial/), order files in [`pico_core_midi/fab/`](pico_core_midi/fab/), held until the Teensy board is brought up | [`pico_core_midi/`](pico_core_midi/) |
| **Teensy core board with MIDI** | **The first board to route completely:** the same feature set on a Teensy 4.1 board alone, placement revised by eye. 0 unconnected, 0 copper faults; its routed board is in [`teensy_core_midi/routed_trial/`](teensy_core_midi/routed_trial/) | [`teensy_core_midi/`](teensy_core_midi/) |

**Status: checkpoint 4, 2026-10-16.** `teensy_core_midi` routes completely: KiCad's DRC finds
no unconnected item and no copper fault, every surface-mount ground pad has its own via to the
plane, and 54 decoupling capacitors are wired straight to their pins. Its wiring blocks and test
points are labelled, the wiring map is in `teensy_core_midi/output/wiring_map.md`, and the JLCPCB
files are in [`teensy_core_midi/fab/`](teensy_core_midi/fab/): **ordered 2026-10-16** (5 boards,
2 assembled). `pico_core_midi` routes completely too (2026-10-17); its order waits on the Teensy
board's bring-up, so any Rev A lessons go into it first. The spec's §14 has every trial; the
story is in [`docs/analogue_board_journal.md`](../../docs/analogue_board_journal.md).
- **Schematic history:** it passed checkpoint 1 as a single board with both module footprints.
  The split changed only the root sheet (one module) and the power sheet, where the ESP32-P4
  bypass (Q201, JP201) stays on the Pico board.

## What's here

| File | What it is |
|---|---|
| `pico/`, `teensy/` | One KiCad 9 project per board. Each folder holds: |
| ↳ `analogue_board_<board>_schematic.pdf` | The schematic, 10 A3 sheets. Sheet 1 is the module and its pin map |
| ↳ `analogue_board_<board>.kicad_pcb` | Checkpoint 3: every part placed on both faces; not yet routed |
| ↳ `output/placement_outward_face.pdf`, `output/placement_deck_face.pdf` | Placement drawings: every part's outline, pads and reference, one face per PDF (vector, zoom in). The deck face is mirrored, as seen from the deck side |
| ↳ `output/placement_outward_face.png`, `output/placement_deck_face.png` | 3D renders of both faces (the deck face seen from below, so mirrored) |
| ↳ `output/checks.md` | Every checkpoint-1 check and its result: ERC, netlist, pins against datasheets, footprints, decoupling, diode orientation |
| ↳ `output/erc.rpt`, `output/*.net`, `output/*_bom.csv` | KiCad's ERC report, netlist and grouped BOM with LCSC numbers |
| `analogue_board.kicad_sym`, `analogue_board.pretty/` | Project symbols and footprints, shared by both boards: DAC8568, Pico 2, Teensy 4.1, edge strip, module sockets, edge strips, wiring holes |
| [`boards_printout.pdf`](boards_printout.pdf) | 1:1 printout (A4, print at 100 %) of each board's outline, edge strips, module socket, USB keep-out and power header, to lay real parts on |
| [`checkpoint2_printout.pdf`](checkpoint2_printout.pdf) | The checkpoint 2 printout, from when both modules shared one board (kept as the record) |
| [`LICENSE`](LICENSE) | CC BY-SA 4.0 |

## The boards are generated

The KiCad files are written by [`tools/analogue_board/`](../../tools/analogue_board/). Change the
generator, not the KiCad files, until the boards are signed off. After that the KiCad files
become the source and the generator is retired.

```sh
python3 tools/analogue_board/build.py      # schematics, ERC, netlists, PDFs, checks (both boards)
python3 tools/analogue_board/pcb.py        # the boards: placement, DRC, renders (both boards)
python3 tools/analogue_board/build.py teensy   # or one board: pico or teensy
```

`build.py` regenerates the libraries and all ten sheets. It then runs KiCad's ERC, exports the
PDF, netlist and BOM through `kicad-cli`, and runs the checks. It exits non-zero if any check
fails. It needs KiCad 9 at `/Applications/KiCad` and Python 3, nothing else.

| Generator file | Holds |
|---|---|
| `variant.py` | Which board a run builds (`pico`, `teensy`, and the trials `shared`, `pico_core`, `shared_core`, `pico_core_midi` and `teensy_core_midi`): folders, module sockets, feature set, placement spacing, track rules and how far the module sits lower |
| `design.py` | Pin map, root sheet (this board's module), power sheet |
| `design_analog.py` | Codec and audio, CV jacks and ADC, CV DAC |
| `design_digital.py` | Pots and gate outs, expander/I2C/LEDs, gate ins and jack detect, edge strips, TRS MIDI |
| `parts.py` | Every part: symbol, footprint, LCSC number, datasheet |
| `datasheet_pins.json` | Each IC's pinout transcribed from its datasheet, independently of KiCad's library. `checks.py` compares the two. |
| `checks.py` | The checkpoint-1 checks |
| `placement.py` | Geometry: outline, strips, module positions, keep-outs, power header, and each board's floorplan |
| `wiring.py` | The wiring field: every channel hole, its bank (four mixed banks, one per quarter of the board) and its slot. The schematic and the placement both read it |
| `pcb.py` | Writes each board from its netlist and `placement.py`. It prints the area budget, runs DRC with the schematic-parity check, checks part heights and renders both faces |
| `autoplace.py` | First-pass placement of every part `placement.py` does not anchor, as close as it fits to the pins it connects to |
| `autoroute.py` | Autoroute with Freerouting. Runs under KiCad's Python and writes a separate trial board in `<board>/output/autoroute/` (not committed). Takes 4 or 6 layers, a run label and any Freerouting setting. `--staged` runs the stages (`--stages=2` stops after the second); `--ground-vias` gives every surface-mount ground pad its own via first, `--decoupling` wires each decoupling capacitor to its pin first; `--lock-existing` and `--unlock` set what the router may rip up. Freerouting's analytics are switched off |
| `finish.py` | Finishes a routed board: via drills, narrow tracks, copper faults taken up, the leftover connections routed by its own grid router and then by rip-up and reroute, dead ends removed, ground pads stitched. Also holds the pre-route steps `autoroute.py` calls |
| `labels.py` | Silkscreen on a routed board: block numbers W1, W2 ... beside the wiring blocks, short names beside the test points; writes `output/wiring_map.md` (every block's holes and signals, every test point) and 1:1 PDFs of each face to print |
| `fab.py` | JLCPCB files from a finished board: Gerbers and drill zipped, BOM and placement (CPL) in JLC's format, into `<board>/fab/` |
| `printout.py` | Writes `boards_printout.pdf` |

The netlist check works from intent. Every connection the generator draws is also recorded as
"pin X belongs on net Y". The check then compares those records with the netlist KiCad computes.
A wire that lands on the wrong pin, two nets that touch, or a pin nobody meant to connect all
fail the build.

## Wiring field conventions

- Every wiring hole is round, except **ground holes, which are square**.
- The headers keep KiCad's square pin 1: the module socket, the edge strips' outer holes, and
  J201, where pin 1 is −12 V (the red stripe).

# Analogue board — Rev A specification, v0.5

A general-purpose Eurorack I/O board: a plug-in compute module on one side, an n8synth
Control Deck on the other, and every analogue, gate and display interface in between.
End goal: one JLCPCB order for assembled boards.

v0.1 was a handoff from a cloud session (2026-10-14) with nothing checked. This version
checks that handoff against datasheets and live JLCPCB stock, adds an I/O audit of the
existing modules, and settles the deck interface with David's answers.

v0.3 (2026-10-14) adds §15: what the schematic (checkpoint 1) decided that this spec had
left open, or changed.

v0.4 (2026-10-15) records the block-by-block prior-art review
(`docs/analogue_board_review/`), the schematic pass that applied it, and David's decisions
on it: TVS diodes on the CV jacks, CV kept at ±5 V, the ESP32-P4-WIFI6 accommodated, the
power header free to move, TRS MIDI back. It also collects every firmware requirement in
one list (§15). Superseded lines elsewhere are marked inline and point to §15.

v0.5 (2026-10-16): **Rev A becomes two boards** (David), one for the Pico 2 or ESP32-P4 and one
for the Teensy 4.1, each with one module socket. Everything else is shared: the peripheral
circuits, the libraries, the edge strips and the wiring field. The reason is routing. With both
modules on one board, the trial autoroutes stalled where the two modules' header rows
interleave (§14, checkpoint 3). Where this spec says "the board", read "each board". Lines the
split supersedes are marked inline.

**Marks:** **[decided]** agreed with David · **[proposed]** recommended, not yet agreed ·
**[open]** needs a decision · **†** not verified against a primary source in this pass.
Datasheet facts carry the datasheet; stock and prices are from the JLCPCB parts API on
2026-10-14 (price at qty 10, USD) and will drift.

---

## 1. What changed from v0.1

| v0.1 said | Finding | Effect |
|---|---|---|
| DG411 not found at LCSC | Vishay DG411DY-T1-E3 **C17218**, 4,745 in stock; DG412/DG413 also stocked | Bidirectional jacks stay as designed |
| 74HCT595 not found at LCSC | Nexperia 74HCT595D **C282339**, 14,359 in stock | Gate outs as designed |
| DAC: DAC8568 vs 2 × quad, open | DAC8568 has **no IOVDD**: VINH = 0.625 × AVDD at 5 V, which 3.3 V logic misses at the top of the AVDD tolerance. Grade **A** run from a 3.3 V analogue rail has VINH = 0.7 × AVDD = 2.31 V — direct drive, no level shifter. IA $17.45 vs 2 × DAC8565 $27.49 | **DAC8568IAPWR on its own 3.3 V analogue rail** |
| PCM3060 "outputs DC-coupled" | DAC outputs are **differential**, 1.6 × VCC = 8 Vpp | A difference amp gives a clean DC-coupled ±5 V out |
| TL074 for all op-amps | TL07x swings ±10 V only into ≥2 kΩ on **±15 V**; from ±11.6 V rails ±10 V is not reliable. **Corrected 2026-10-15 (§15):** that was the old TL07x die; the TL07xH swings within 0.2 V of the rails into 10 kΩ | **±5 V is the CV range**; ±10 V needs a rail-to-rail part (OPA4197) (superseded, §15) |
| Gate-in count 6, EYESPI colour TFT | The audit (§3) finds no own build with more than two gate ins, and none using a colour TFT | 4 direct gate ins; EYESPI dropped (both decided) |
| Board "~50 mm wide", headers to the deck | David: **10HP mounts parallel to the panel, 6HP at 90°**, and the channel→cell wiring lives **on this board** | One PCB, the n8synth breadboard's footprint, serves both widths (§4) |
| 24C02 EEPROM | The panel map plus calibration can outgrow 256 bytes | **M24C64** (8 KB), a Preferred part |
| MIDI in via opto | David has only ever used TRS MIDI on the Big Genes | **No MIDI circuit in Rev A** (decided). **Reversed 2026-10-15: TRS MIDI in and out are back (§15)** |
| Three module families incl. XIAO | 11 pins cannot carry I2S plus a panel bus | **Pico 2 and Teensy 4.1 only** (decided); XIAO dropped |

## 2. Goal and constraints

- **Deliverable:** a JLCPCB order for populated boards. JLCPCB assembles all SMT;
  David solders only headers, sockets and the deck wiring. [decided]
- **One design for both widths.** The same assembled board mounts parallel behind a 10HP
  deck and at 90° behind a 6HP deck (§4). Both versions come from one assembly order.
  [decided — David confirms the 6HP and 10HP kits use the same breadboard]
- **Principle:** the board offers more channels than any one panel uses. It provides typed
  channels and never decides which deck cell they go to; David wires that per module on
  the board. [decided]
- **Assembly:** 4-layer, SMT on one side, JLCPCB **Economic PCBA**, which takes 2-, 4- and
  6-layer boards, single-sided placement, 0402 and 0.4 mm pitch at the finest, 2–50
  boards (§12). Prefer Basic parts: each Extended part type costs $3.07 an order.

## 3. I/O audit — what the modules actually use

Source: `MCU_MODULES.xlsx` in the eight4awish repo (every module with a microcontroller,
with a confidence level per row). Own builds are the board's customers: firmware David
writes and would port here. Bought modules are benchmarks.

### Own builds

| Module | Platform | HP | CV in | Gate in | CV out | Gate out | Audio in / out | Pots | Buttons etc. | Display | MIDI |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Sorrow | Patch SM | 10 | 4 | 2 | 1 | 2 | (2) / 2 | 4 | button, toggle | — | — |
| Joy | Patch SM | 10 | 4 | 2 | — | — | — / 2 | 4 | button | OLED 64×48 | — |
| Girl | Ksoloti | 20 | 9 | 1 | — | 1 | — / 2 | 8 | 4 buttons, **2 encoders** | OLED 128×64 | — |
| Boy | Teensy 4.1 | 10 | — | — | 4 (2 V/oct) | 4 (+6 on expander) | 2 / 2 | 4 | button | OLED 128×64 | USB |
| Chaos | Teensy 4.1 | 10 | 4 | (2 of the CV) | 2 | — | 1 / 2 | 4 | button | OLED 128×64 | — |
| CortHex | Nano ESP32 | 10 | — | 1 | **6 (±5 V, calibrated)** | — | 2 / 2 | — | 7 buttons + 7 LEDs | — | — |
| Daisy MultiOsc | Patch SM | 10 | 4 | 2 | 1 | 2 | 2 / 2 | 4 | button | OLED 64×48 | — |
| Daisy MultiFX | Patch SM | 10 | 4 | 1 | — | — | 2 / 2 | 4 | button | OLED 64×48 | — |
| MultiFX (Seed) | Daisy Seed | 6 | 2 | — | — | — | 2 / 2 | 3 | button | OLED 128×64 | — |
| Pico2W OnC Lite | Pico 2 W | 6 | 2 | 1 | 2 (V/oct) | 2 | — | 3 | button | OLED 128×64 | USB, Wi-Fi |
| ClkLinkRec | XIAO ESP32-C5 | 4 | — | 1 | — | 3 | — | — | 2 buttons, 2 LEDs | — | — |
| AMYboard PatchBank | AMYboard | 10 | 1 (V/oct) | 1 | — | — | 2 / 2 | — | **encoder** | OLED 128×128 | **TRS in + out** |
| MOD2 / Melon | XIAO RP2350 | 6 | 3 | — | — | — | — / 1 | 3 | button, 2 switches | WS2812 | — |

### Bought benchmarks (MCU modules, medium/high confidence rows only)

| Module | CV in | Gate in | CV out | Gate out | Audio | Controls | Display |
|---|---|---|---|---|---|---|---|
| Ornament & Crime v4.1 (Teensy 4.1) | 8 | — | 8 | — | 2 / 2 | 2 encoders, 5 buttons | OLED |
| Workshop Computer (RP2040) | 2 + 2 audio/CV | 2 | 2 precision + 2 audio/CV | 2 | shared | 3 knobs, Z switch | 6 LEDs |
| EuroPi (Pico 2 W) | 1 | 1 | 6 | — | — | 2 knobs, 2 buttons | OLED |
| Alchemy Lab (Hermetic Modular, Daisy Seed 2), 12HP | 6 bidirectional | — | (same 6; V2 drives four through an MCP4728) | — | 2 / 2 | 6 pots, 3 buttons | 102 RGB LEDs; USB-C MIDI, microSD |
| Ogham (Daisy Seed) | 2 | 2 | 1 | 1 | — / 2 | 4 pots, encoder, toggle | display |

The Alchemy Lab also hosts two own firmwares, Secret (the Teensy Chaos's successor) and Wish
(Mutable Beads), so it is both a benchmark and a target (MODULES.md).

### Reference platforms, not in the rack (added 2026-10-16)

Noise Engineering's two Daisy Seed platforms, from NE's manuals and libDaisy's board files
(`daisy_versio.h`, `daisy_legio.h`). Each platform runs many firmwares on one panel layout.

| Platform | CV in | Gate in | CV out | Gate out | Audio | Controls | LEDs |
|---|---|---|---|---|---|---|---|
| Versio (Noise Engineering), 10HP | 7, 0–5 V, each summed with its pot | 1 (FSU, trips above 2 V) | — | — | 2 / 2, inputs clip at about 16 Vpp | 7 pots, 2 three-position switches, 1 button | 4 RGB |
| Legio (Noise Engineering), 6HP | 1 per the manuals (1 V/oct pitch, −2 to +5 V) † | 1 (rising edge at about 1.6 V) | — | — | 2 / 2, AC-coupled in, out up to 16 Vpp | encoder with press, 2 pots, 2 three-position switches | 2 RGB † |

† **Legio CV inputs:** a press roundup says each of the three controls has a CV input, but
the Sinc and Tymp Legio manuals list one CV jack. **Legio LEDs:** libDaisy's header enum has
two, while a comment in the same file says four.

What they add:
- **Audio-first.** Both are stereo in and out with no CV or gate outputs, only CV inputs.
  Noise Engineering states that pitch-accurate CV inputs need more circuitry than the Versio
  has. Its CV inputs are 0–5 V, summed with a pot into the MCU's ADC.
- **Small and focused.** A Versio-class design needs 7 knob-plus-CV pairs, 1 gate and stereo
  audio. A Legio-class design needs even less. Both fit the Patch SM pattern (4 CV in, 2 gate
  in, stereo audio) or fall below it, and both fit a much smaller board than Rev A's full
  channel set.

### What it says

1. **Stereo audio out is the commonest need** (10 of 13 own builds); audio in, 7 (6 of them stereo).
2. **CV in: four is the norm** (the Patch SM pattern); Girl peaks at 9, O&C at 8.
3. **CV out: 0–2 typically, 6 at the top** (CortHex, EuroPi). Two builds need calibrated V/oct.
4. **Gate in: never more than 2** in an own build. Clock and reset also arrive on CV jacks.
5. **Gate out: 2–4**, but Boy plus its expander reaches 10 trigger-type outputs.
6. **Pots: 3–4 typical, 8 at the top** (Girl).
7. **Encoders:** two own builds (Girl, AMYboard) and two bought (Ogham, O&C) — v0.1 had none.
8. **Displays: I2C OLEDs only** (9 of 13 builds; SSD1306 64×48 and 128×64, SH1106, SSD1327 128×128). No colour TFT anywhere.
9. **MIDI:** USB MIDI via the module's own USB. TRS appears once on paper (AMYboard), but
   David has only ever used TRS MIDI on the Big Genes: low priority.
10. **Panel ceiling:** a 10HP deck has 18 cells (6HP: 12), one panel part per cell. A
    Patch SM-style panel (4 knobs, 4 CV in, 2 gate in, 2 gate out, CV out, stereo out,
    button, toggle) already needs 17. The board's channel count only has to beat 18, not
    match every module's I/O at once.

### Rev A channel set [proposed]

| Type | Count | Notes |
|---|---|---|
| Audio in | 2 | AC-coupled, 10 Vpp nominal, ±10 V tolerant. **Full scale 20 Vpp from 2026-10-15 (§15)** |
| Audio out | 2 | DC-coupled, ±5 V; doubles as high-resolution CV out. **Full scale 20 Vpp from 2026-10-15 (§15)** |
| CV bidirectional | 6 | ADC always reads the jack; DAC switched on for output |
| CV in only | 2 | The ADC's spare channels |
| CV out only | 2 | The DAC's spare channels |
| Gate in | 4 | Direct GPIO, comparator input with a set threshold (v0.1 had 6) [decided] |
| Gate out | ~~8~~ **4** | 0/5 V via shift register. **Cut to 4, one per wiring bank, 2026-10-16 (David, to ease routing); the expansion holes still chain a second 595** |
| Pots | 8 | Ratiometric |
| Buttons / switches / encoder | 9 lines | On the GPIO expander; one encoder needs 3 |
| LEDs | 1 chain | WS2812, 5 V data |
| Spare GPIO | 2 | To the wiring field (the pins v0.1 gave to MIDI) [decided]. **From 2026-10-15 they can carry TRS MIDI through link holes (§15)** |
| TRS MIDI | 1 in, 1 out | **Added 2026-10-15 [decided]:** Type A, H11L1 opto in, 5 V buffered out (§15) |
| Displays | Qwiic I2C | EYESPI dropped [decided] |

So CV reaches 8 in or 8 out (O&C's count; eight of Girl's nine), and the gate outs cover
Boy plus most of its expander.

## 4. Mechanical and the deck interface

### 4.1 One board, two orientations [decided]

David's build practice (2026-10-14): **10HP — the n8synth breadboard sits parallel behind
the deck, using both edge strips; 4/6HP — the breadboard sits at 90° to the panel, the
deck on right-angle headers along one edge (by convention the left).**

The n8synth templates draw the **same breadboard (49.6 × 103 mm) in the 4HP, 6HP and 10HP
files** (`tools/n8layout/*.n8layout`, element `rect82e4df`; the 6HP file adds a 29.7 mm
panel rectangle). If the physical boards match, this board takes that outline and
replaces the breadboard in both widths:

- **10HP:** parallel to the panel; the deck plugs into the outer holes of both edge strips.
- **6HP:** at 90°; the deck's right-angle headers plug into the left strip's outer holes;
  the right strip is unused and that edge is the rear of the module.

**David confirms (2026-10-14):** the 6HP and 10HP kits use the same breadboard; in 6HP only
the left set of 40 positions can be connected.

**Geometry** — from the n8synth web tool's own vector of the board (`10HP Template.n8layout`,
symbol `n8bb-a1-v1-front`), origin at the top-left corner, mm. Electrical behaviour is
not read from it (`docs/n8synth_platform.md`); dimensions are.

| Feature | Position |
|---|---|
| Outline | 49.6 × 103.0 |
| Edge strip, left | outer column x = 1.92, inner x = 4.46 |
| Edge strip, right | inner x = 45.14, outer x = 47.68 |
| Edge positions 1–40 | y = 2.07 + 2.54·(n − 1), so 2.07 … 101.13 |
| Power rails (breadboard only) | x = 7.57 (+12 V side) and 42.02 (−12 V side) |
| Eurorack power header (breadboard) | 2 × 8, pins at x = 15.91 … 33.69, y = 98.82 / 101.36 — bottom centre |
| Deck headers (template) | female 1 × 40 into the outer columns of both strips |

The board keeps the outline, both strips and the power-header position. It drops the
breadboard's power rails, main area and its three centre-line mounting holes (Ø 3.0 at
x = 24.8): those are for stacking a second board, and nothing stacks on this one
[decided, David 2026-10-14].

### 4.2 Edge strips and wiring field [decided: wiring on this board; geometry proposed]

- **Two edge strips**, 40 positions each, 2.54 mm pitch, at the n8synth edge-connector
  positions: an outer hole for the deck header and an inner hole as a wiring point, the
  two joined (the n8synth doublet). Deck header spans are positions 1–10, 16–25 and 31–40;
  positions with no deck cell remain free tie points, as on the breadboard.
- **Channel holes beside their circuits** [decided, David 2026-10-14]: each channel ends in a
  plated hole next to the circuit it belongs to, labelled on both faces, plus a few AGND,
  VREF (pot top), +5 V LED and DGND holes. Each module is wired exactly like a
  breadboard: short wires from those holes to the inner ("second") hole of the deck
  position each cell occupies. **Superseded 2026-10-15 (§14, checkpoint 3):** the holes now
  sit in four mixed banks, one per quarter of the board, each with some of every channel
  type, so a panel part anywhere on the deck has its channel close by (`wiring.py`).
- **Pads tinned on both faces** (HASL finish), so wires can run on either face: across the
  outward face, or underneath in the stand-off gap on the deck face.
- **Deck ground bus (D pads):** one wire from any D pad to an AGND hole (pot and jack
  grounds are on D).

### 4.3 Faces and height

- **Everything on the outward face** — the face away from the deck, as n8synth mounts
  components outward for probing. That means the SMT (JLCPCB one-side assembly), the
  module on headers, the power header and the wiring. The deck face carries only the
  deck's header pins.
- **Low-profile SMT under the module** [decided, David 2026-10-14]. The modules sit on
  headers, so the area between and under their pin rows takes the logic (§10). Parts there
  stay ≤ 2.5 mm tall; with 8.5 mm female headers that leaves ample clearance under a Pico
  or Teensy. Taller parts (DPAK regulator, buck inductor) go outside the module
  footprint.
- **6HP height budget** (board at 90°): deck-side pin stubs ~1 + PCB 1.6 + header 8.5 +
  module and its parts ~2.5 ≈ **14 mm** against a 30.3 mm panel. Where the board sits
  across the 6HP width depends on where the deck's right-angle header lands — **to check on
  a real 6HP build.**
- **USB:** each module's USB end points **toward the centre of the board**, with its far end
  at the top short edge, as commercial boards do. The plug goes in parallel to the board and
  lies over it, and the cable bends back into the depth of the case. Nothing crosses the rail.
  v0.2's "USB to the top edge, then a panel-mount extension" is withdrawn. The board's top
  edge sits a few millimetres from the rail, which leaves no room for a plug there, and at
  10HP an extension has no way past the board to the panel. This was settled in the chat
  behind v0.1 and lost from v0.2. **Keep-out** beyond each USB end: about 30 × 15 mm with
  nothing taller than about 8 mm (the plug sits about 9-15 mm up on 8.5 mm headers);
  estimates, to check at checkpoint 2 with real cables. The shrouded power header and the buck
  inductor stay out of it. [proposed]
- **Power header:** shrouded **2 × 5**, ±12 V only, at bottom centre (where the breadboard
  has its 2 × 8), on the outward face. [decided — David: the bus +5 V is not wanted]
  **Position superseded 2026-10-15 [decided]:** it need not be bottom centre; the
  patch.init has its socket on a long edge. Place it with the buck and the rail filters at
  one end, away from the codec, ADS8688, DAC8568 and their op-amps, and outside the USB
  keep-out. Its only constraint is keeping power-rail noise away from sensitive parts.

## 5. Compute modules [decided: Pico 2 and Teensy 4.1]

David, 2026-10-14: the XIAO is too limited; design for **Raspberry Pi Pico 2 and Teensy 4.1
pin compatibility**. Sources: Raspberry Pi *Pico 2 datasheet* and *RP2350 datasheet* (GPIO
function table); PJRC Teensy 4.1 product page, pinout cards and dimension drawing.

| | Pico 2 (RP2350) | Teensy 4.1 |
|---|---|---|
| Outline | 51 × 21 mm | 60.96 × 17.78 mm |
| Rows, pitch | 2 × 20, 17.78 mm apart | 2 × 24, 15.24 mm apart |
| GPIO a header reaches | **26** (GPIO 0–22, 26–28) | **42** (0–41) |
| USB | Micro-B, short edge at pins 1/40 | Micro-B, short edge at pin 0 / VIN |
| I2S | PIO on any GPIO; MCLK from GPOUT (GP13/15/21) or PIO | SAI1: MCLK 23, BCLK 21, LRCLK 20, TX 7, RX 8 |
| Hardware SPI | SPI0 and SPI1 groups both on the header | Two buses on the edge (SPI 10–13; SPI1 26, 27, 1, 0) |
| +5 V in | VSYS (1.8–5.5 V) through our Schottky — the datasheet's ORing arrangement | VIN (3.6–5.5 V). **Cut the VIN–VUSB pads first**. Full 2 × 24 headers (its own board, 2026-10-16) |
| 3V3 out | < 300 mA | 250 mA |
| Logic level | 3.3 V; GPIO 5 V-tolerant while powered, 3.3 V-failsafe unpowered (RP2350 datasheet) | 3.3 V; **not 5 V-tolerant** (PJRC: "Do not drive any digital pin higher than 3.3 volts") |

- ~~**Both footprints on the one board, wired to the same nets.**~~ **Superseded 2026-10-16:
  one board per module (David).** The overlapping footprints did not route (§14, checkpoint 3).
  Each board carries one socket on the board's centre line, with the same pin functions as
  the shared pin map, so firmware is unchanged. USB ends point toward the board centre (§4.3).
  The generator builds both boards (`tools/analogue_board/variant.py`). The Pico board also
  takes the ESP32-P4.
- **Power:** 5 V reaches either module through a Schottky. Teensy: cut the VIN–VUSB pads
  before fitting.
- **Every signal into the module is 3.3 V** (the Teensy sets the rule). The parts that
  talk back to it — ADS8688 (DVDD), MCP3208, PCM3060 (VDD), TCA9555, EEPROM — run their logic
  from the 3.3 V digital rail; the gate-in comparators' open-collector outputs are pulled
  up to it. The 5 V parts (74HCT595, AHCT1G125)
  only take 3.3 V in and drive jacks or LEDs, never a module pin.
- **Waveshare ESP32-P4-WIFI6** (bought 2026-10-14, not a target): it fits the Pico header but
  is not a drop-in. Pins 21, 22 and 24 (SPI-A) sit on an I/O bank whose supply firmware must
  set to 3.3 V first. The board is 20 mm longer than a Pico, its USB-C is serial only, and its
  Wi-Fi will be weak in the rack. Details: [`analogue_board_esp32p4.md`](analogue_board_esp32p4.md).
  It prompted 10 kΩ pull-ups on CS_ADC, CS_DAC and CS_POT, which every module benefits from.
  **Accommodated from 2026-10-15 [decided]:** bridging JP201 lets Q201 bypass the Schottky
  for its supply margin. Firmware sets LDO channel 4 to 3.3 V before using pins 21, 22 or 24.
  Checkpoint 2 finds room for its extra length (§15).
- **Teensy 4.0** is not a target. If its pins prove to sit where the 4.1's first 14 per
  side do †, the bus-merge jumpers (§6.3) would let it run as a bonus.

## 6. Architecture

### 6.1 Buses

| Bus | Members | Speed | Why separate |
|---|---|---|---|
| **I2S** | PCM3060 (hardware-control mode) | 48 kHz, MCLK 256/512 fS | — |
| **SPI-A, converter bus** | ADS8688 (CS_ADC), DAC8568 (CS_DAC) | ≤ 17 MHz (ADS8688 limit) | Audio-rate CV needs the bus to itself |
| **SPI-B, panel bus** | 74HCT595 (RCLK as CS), MCP3208 (CS_POT), expansion CS | ≤ 1 MHz for MCP3208 at 3.3 V | Slow devices off the converter bus |
| **I2C** | TCA9555 expander, M24C64 EEPROM, Qwiic | 400 kHz | — |

**SPI-A budget:** each ADS8688 conversion is a 32-clock frame, as is each DAC8568 write.
At 16 MHz that is 500 k frames/s, so 8 ADC + 8 DAC channels run at **~31 kHz each**, or
6 + 6 at ~41 kHz. Audio-rate CV, with audio itself on the codec.

### 6.2 Signal flow

```
jack ─1k─┬─ ADS8688 AIN (1 MΩ, ±10.24 V or ±5.12 V range)
         └─100k─ AGND                       (unpatched input reads 0 V)
jack ─1k─ DG412 D ─ S ─ op-amp (×4, −5 V offset) ─ DAC8568 (0–2.5 V)
                    └ IN ← TCA9555 (pull-down: off at reset, so jacks start as inputs)
```

With the switch on, the ADC reads the jack itself, so an output can be measured under load
and the loop closed in firmware. With nothing patched, the same path is the
self-calibration loopback.

### 6.3 Pin budget

| Function | Pins |
|---|---|
| I2S: MCLK, BCK, LRCK, DOUT, DIN | 5 |
| SPI-A: SCK, MOSI, MISO, CS_ADC, CS_DAC | 5 |
| SPI-B: SCK, MOSI, MISO, CS_595, CS_POT | 5 |
| I2C: SDA, SCL | 2 |
| Expander interrupt (buttons, encoder) | 1 |
| Spare GPIO to the wiring field (UART-capable) | 2 |
| WS2812 data | 1 |
| Gate in | 4 |
| Jack-detect probe | 1 |
| **Total** | **26 nets** |

Pico 2: all 26 nets on 26 pins, with hardware SPI0 and SPI1 both reaching the header.
Teensy 4.1: all 26 on 42 pins, ~16 spare.

**Bus-merge jumpers [optional]:** three solder jumpers joining SPI-B's SCK, MOSI and MISO
to SPI-A's would free three pins for a single-bus module (only relevant to Teensy 4.0,
§5). No parts, no BOM cost; decide at schematic.

### 6.4 Borrowed from prior art

| Idea | Source | Use here |
|---|---|---|
| **Jack-detect probe** (**dropped 2026-10-16**, David, to ease routing; the pin it used is free): one GPIO drives 100 kΩ into each input jack's switch (normal) lug, with a BAT54S clamp. Firmware sends a pseudo-random bit every 16 samples and calls an input patched when its readings stop following the sequence. No extra ADC channels. | Workshop System Computer Rev 1.0.0, R63–R68, `ComputerCard.h` L617–623, L834–874 | Adopt. A PROBE column in the wiring field (one 100 kΩ per hole) reaches the switch pad of any input jack cell. [proposed] |
| Calibration in an EEPROM on the board, magic number + CRC, 3 points per channel (−2/0/+2 V) written by a web UI | Workshop System Computer (ZD24C08, 0x50) | Same scheme in the M24C64 |
| Closed-loop output calibration: calibrate the input against known voltages, then loop each output into it — no meter | EuroPi `calibrate.py` | The DG412 loopback does this with no patch cable |
| Series Schottky on both rails, 22 µF 35 V + 100 nF | Workshop System Computer | As §8 |
| TL074H for every ±12 V output stage, 1 kΩ out | Workshop System Computer | As §7 |
| One −5 V TL431 reference offsets all bipolar stages | Workshop System Computer | Alternative to deriving the offset from the DAC reference [open, schematic stage] |

The Workshop System Computer is an RP2040 board (Music Thing Modular); EuroPi is
Allen Synthesis's Pico board. Values above were read from their published schematics
and firmware at commits `cced06a` and `1192d31`.

### 6.5 Prior-art review, function by function

WSC = Workshop System Computer Rev 1.0.0 (schematic PDF, `ComputerCard.h`); EuroPi =
surface-mount revision (KiCad PCB netlist, firmware); Patch SM = Electrosmith datasheet
v1.0.5 and libDaisy; Ogham = Keeos `ogham-merged-v1.0` sheets.

| Function | WSC | EuroPi | Patch SM / Ogham | This board |
|---|---|---|---|---|
| **CV in** | 120k → inverting MCP6004 on 3.3 V, 33k‖4.7 nF, 100k from a −5 V ref: ±6 V → 0–3.3 V. RP2040 ADC via CD4052 mux, "really 8–10 bits" | 100k → TL074 ×−0.22 → MCP6002 on 3.3 V (stage credited to Émilie Gillet): 0–12 V, negatives read 0 | Patch SM: ±5 V, 100k in. Ogham: 470k into an MCP6004 summer with the pot and a −5 V ref | ADS8688 direct: ±10.24 / ±5.12 V native, 1 MΩ, 16-bit. No op-amp, no mux. |
| **Input protection** | Large series R into a virtual ground; the 3.3 V rail-to-rail op-amp cannot drive the ADC past its rails | Same idea: TL074 then a 3.3 V MCP6002 that "will always clip" | Ogham: 470k series plus the op-amp's clamps | The ADS8688's own OVP (±20 V powered, ±11 V off) behind 1 kΩ |
| **CV out** | PWM 11-bit at 60 kHz → 2-pole MFB on TL074H (gain −3.6, +5.97 V offset); sigma-delta in the PWM IRQ gives ~19 bits, ~5.9 mV calibrated | PWM 100 kHz → 1k/100 nF → TL074 ×3.2 → 1k: 0–10 V, ~1.5 kHz bandwidth | Patch SM: STM32 12-bit DAC, 0–5 V. Ogham: Seed DAC → TL072 ×3 | DAC8568 16-bit → TL074H ×4 with offset: ±5 V at ~31 kHz per channel |
| **Audio out** | MCP4822 → TL074H inverting with −5 V ref: ±6 V, 1k out | — | Patch SM: PCM3060, DC-coupled, **17.3 Vpp full scale** (corrected 2026-10-15; it was given as ±5 V). Ogham: TL072 ×4.7 overshot to 19.5 Vpp | PCM3060 differential → difference amp ×1.25: ±5 V DC-coupled |
| **Gate in** | 100k → NPN base, RP2040 pull-up as the load, no clamp; above 0.4 V = high | 100k → NPN, reverse diode on the base, 10k pull-up; 0.8 V threshold | Patch SM: BJT input, inverted in libDaisy. Ogham: LM393 with hysteresis for clock Ogham's clock input, adopted: 10k series, BAT54S clamps, LM393 against 1.65 V with hysteresis, own 3.3 V pull-up. No reliance on module pull-ups |
| **Gate out** | GPIO → NPN, 10k to +12 V: ~7.2 V open-circuit, ~6 kΩ source, short-proof | — | Patch SM: 0–5 V, 100 Ω. Ogham: 74AHCT1G125 → 1k → Schottky clamps | 74HCT595 → 1k, BAV99 clamps: 0/5 V |
| **Pots** | 3 × 100k from 3V3 through the mux; a 3-way switch read on one channel via 100k/100k | 2 × 10k from the Pico's 3V3 | Patch SM: pots from +5 V out (not ratiometric). Ogham: 1k + 100 nF + 100k pull-down | MCP3208, pots from its own reference: ratiometric |
| **Buttons** | — | 1k series, 10k pull-up, 100 nF: 1 ms RC debounce | — | Adopt EuroPi's 1k / 10k / 100 nF on each expander button line [proposed] |
| **LEDs** | NPN low-side switches from +12 V, keeping LED current off 3V3 | 5.1k off each op-amp output, so the LED shows the real output voltage | Patch SM: LED on CV out 2 | WS2812 chain on the digital 5 V buck |
| **Jack detect** | One-GPIO pseudo-random probe through 100k to every input normal lug | 10k from a GPIO to each input's normal lug; unused by firmware | Patch SM: input 1 normalled to input 2 | WSC probe, adopted (§6.4) |
| **Calibration** | ZD24C08 EEPROM, magic + CRC, up to 10 points per output, written from a web UI | Software on the Pico's flash; outputs looped into the input to find each volt | — | M24C64; DG412 loopback needs no cable |
| **Power** | 5819 on each rail, 22 µF 35 V; CJA1117-5 from +12 V; 5 V → Schottky → VBUS → RT9193 3V3 | S2D rectifiers (not Schottky) on each rail; 7805 → diode → Pico VSYS | Ogham: SS14 + BLM18 ferrite + 10 µF 50 V per rail; the Seed fed from +12 V on its own; 7805 for logic only | SS14 + ferrite per rail; buck for digital 5 V; L78M05 for analogue 5 V; separate 3.3 V rails |
| **ID** | GPIO straps read with pull-up then pull-down: three states per pin | GPIO straps, unused | — | Footprint ID and revision in the EEPROM |

**Not adopted, and why:** PWM CV out (WSC, EuroPi) — the DAC8568 gives 16 bits at audio
rate without filter ripple; the analogue mux (WSC) — the ADS8688 scans its own eight
channels; NPN gate outs to +12 V (WSC) — a 5 V gate is what the Patch SM and Ogham
produce, and the 595 drives eight from one chip.

## 7. Functional blocks

| Block | Circuit | Part (LCSC) | Stock / $@10 | Status |
|---|---|---|---|---|
| **Codec** | PCM3060 in hardware-control mode (no control bus). VCC 4.5–5.5 V analogue, VDD 2.7–3.6 V digital. ADC: single-ended, full scale 0.6 × VCC = 3 Vpp around VCOM = 2.5 V, Zin 10 kΩ. DAC: differential, 8 Vpp; load ≥ 10 kΩ DC-coupled. SCKI (MCLK) 2.048–36.864 MHz is required. *(PCM3060 datasheet SBAS437, 2008)* | PCM3060PWR **C2651841** | 1,955 / $4.08 | proposed |
| **Audio in** | Eurorack 10 Vpp → AC-couple → inverting amp, gain −0.3, biased to VCOM → codec. Clamp to the codec rails. **Superseded 2026-10-15: 20 Vpp full scale, gain −0.136 (§15)** | op-amp | — | proposed |
| **Audio out** | Codec VOUT± → difference amp, gain 1.25 → ±5 V, **DC-coupled** → 1 kΩ → jack. **Superseded 2026-10-15: balanced second-order MFB, gain 2.5, 20 Vpp (§15)** | op-amp | — | proposed |
| **CV ADC** | ADS8688: 8 ch, 16-bit, 500 kSPS aggregate, per-channel ranges ±10.24 / ±5.12 / ±2.56 / 0–10.24 / 0–5.12 V, **1 MΩ** input, OVP ±20 V powered / **±11 V unpowered**, internal 4.096 V ref, AVDD 4.75–5.25 V, DVDD 1.65 V–AVDD, SCLK ≤ 17 MHz, 32-clock frames *(SBAS582C)*. No input op-amps needed. | ADS8688IDBTR **C527390** | 2,921 / $7.32 | proposed |
| **CV DAC** | DAC8568 grade A: 8 ch, 16-bit, internal 2.5 V ref (off by default), output 0–2.5 V, resets to zero scale, SCLK ≤ 50 MHz. **AVDD = 3.3 V analogue rail**, so VINH = 0.7 × AVDD and 3.3 V logic drives it *(SBAS430F)*. Op-amp ×4 with −5 V offset → ±5 V. | DAC8568IAPWR **C486051** | 796 / $17.45 | decided |
| **Jack switch** | DG412 (logic 1 = on) with pull-downs, so jacks power up as inputs. ±12 V fine (V+ to V− ≤ 44 V), VL = 5 V, logic 0.8 / 2.4 V, RDS(on) 25 Ω typ, signals beyond the rails clamp through internal diodes, ≤ 30 mA *(Vishay 61564 rev B)* | 2 × DG412DQ-T1-E3 **C2651920** (TSSOP) | 5,903 / $2.18 | proposed |
| **CV op-amps** | 8 outputs at ±5 V: TL074H (no phase reversal, CM includes V+). The ±10 V option needs rail-to-rail output: OPA4197 footprint-compatible (SOIC-14). **Superseded 2026-10-15: the TL074H swings ±10 V on our rails; ±10 V is a resistor variant (§15)** | TL074HIDR **C2878713**; option OPA4197IDR **C2058532** | 14,140 / $0.25; 8,474 / $2.73 | decided (±5 V) |
| **Reference** | LM4040 4.096 V shunt for the calibration check (0.1 % A-grade or 1 % D-grade). **Dropped at checkpoint 1 (§15)** | LM4040AIM3-4.1 **C126807** / LM4040DIM3-4.1 **C202194** | 2,077 / $1.12; 6,187 / $0.47 | dropped |
| **Pots** | MCP3208 on the 3.3 V analogue rail, VREF = that rail, pots fed from VREF + AGND (ratiometric). 50 ksps at 2.7 V, SCLK ≤ 1 MHz at 2.7 V *(DS21298)* | MCP3208-CI/SL **C16939** | 600 / $3.24 | proposed |
| **Gate in** | Ogham's clock input (Keeos `ogham-merged-v1.0`): jack → 10 kΩ → BAT54S clamp to 3.3 V / GND, 100 kΩ to GND → LM393 (+5 V) + input; − input at 1.65 V from a 3.3 V divider; ~100 kΩ hysteresis; open-collector output, 10 kΩ pull-up to 3.3 V → GPIO, not inverted. Trips at ~1.8 V at the jack, set by resistors, not by logic-gate tolerance — a 3.3 V gate clears it by 1.5 V. ±12 V clamps at ~0.8 mA. Values to tune at schematic. | 2 × LM393DR2G **C7955** (Basic); 4 × BAT54S **C408389** | 213,954 / $0.07; 817,166 / $0.02 | decided |
| **Gate out** | 74HCT595 at 5 V (VIH 2.0 V, so 3.3 V drives it) → 1 kΩ → jack, BAV99 (Basic, C2500) clamp to +5 V / GND per output. OE pulled high until firmware enables (§10). | 74HCT595D **C282339**. **From checkpoint 3: 74HCT595PW,118 C99710 (TSSOP-16, 3,956 / $0.40)** | 14,359 / $0.27 | decided |
| **Expander** | 16 lines: 6 switch enables (DG412), 1 gate-output enable, 9 for buttons, switches, encoder; INT to a GPIO | TCA9555PWR **C465732** | 35,995 / $0.56 | proposed |
| **LEDs** | WS2812 chain; data level-shifted to 5 V; LED supply on its own wiring-field holes | SN74AHCT1G125DBVR **C7484** | 49,818 / $0.10 | proposed |
| **EEPROM** | Board revision, footprint ID, calibration, panel map | M24C64-RMN6TP **C79988** (Preferred) | 103,045 / $0.15 | proposed |
| **Qwiic** | JST SH 4-pin, 3.3 V from the display LDO | SM04B-SRSS-TB **C160404**. **From checkpoint 3: vertical BM04B-SRSS-TB(LF)(SN) C160390 (39,935 / $0.25)** | 10,257 / $0.21 | decided |

### 7.1 The DAC choice: 16-bit DAC8568 or 12-bit MCP4822 [decided: DAC8568]

**What established modules use** (read from each module's firmware driver or published
schematic, 2026-10-14):

| Module | CV-out converter | Evidence |
|---|---|---|
| Ornament & Crime (open, Teensy) | TI **DAC8564 / DAC8565**, 16-bit quad | `software/o_c_REV/OC_DAC.cpp` |
| Westlicht Performer (open sequencer) | TI **DAC8568**, A or C grade, 16-bit 8-channel | `src/platform/stm32/drivers/Dac.h`, `HardwareConfig.h` |
| Mutable Instruments Marbles | 16-bit DAC (chip not named in the driver) | `marbles/drivers/dac.h` |
| Music Thing Workshop Computer | PWM + sigma-delta, ~19-bit effective, for its 2 precision outs; **MCP4822** for its 2 audio/CV outs | schematic; `ComputerCard.h` |
| EuroPi | Filtered 100 kHz PWM | firmware, PCB netlist |
| Daisy Patch SM | STM32's internal 12-bit DAC | datasheet |
| Alchemy Lab | MCP4728, 12-bit I2C quad | SDK layout header |
| Your own builds (Boy, CortHex, Teensy Expander, OnC Lite) | MCP4822 / MCP4728, 12-bit | `MCU_MODULES.xlsx` |

Closed premium modules (disting NT, Metropolix, Pamela's PRO Workout) do not name their
converters on their product pages. On codecs, Mutable's newest module, **Beads, uses the
PCM3060** (`beads/drivers/codec.h`); Clouds and Elements use the WM8731.

The pattern: modules whose job is precise CV (O&C, Performer, Marbles) use 16-bit TI
DAC85xx parts. Platforms where CV is secondary (Patch SM, Alchemy Lab, the Workshop
Computer's audio outs) and David's own builds use 12-bit.

**Side by side**, after scaling to ±5 V (a 10 V span, 1 V/oct):

| | DAC8568IA | 4 × MCP4822 |
|---|---|---|
| Step | 10 V / 65,536 = 0.15 mV ≈ **0.2 cent** | 10 V / 4,096 = 2.44 mV ≈ **2.9 cents** |
| Integral nonlinearity, max | ±12 LSB = ±1.8 mV ≈ ±2.2 cents | ±12 LSB = ±29 mV ≈ **±35 cents** (±2 LSB typ ≈ ±6 cents) |
| Reference | internal 2.5 V, **5 ppm/°C** typ, 25 max for grade A (corrected 2026-10-15: 2 ppm typ is grade C) | internal 2.048 V ±2 %, **45 ppm/°C** typ, 160 max |
| Drift at the top of the range (+5 V, i.e. 10 V of span) over a 10 °C warm-up | 0.5 mV ≈ 0.6 cent typ; 2.5 mV ≈ 3 cents max | 4.5 mV ≈ **5 cents** typ; 16 mV ≈ 19 cents max |
| Audio-rate output (~31 kHz) | ~96 dB resolution-limited | ~72 dB |
| Channels / chip selects | 8 / **1** | 2 per chip, so 8 / **4** |
| Board area | one TSSOP-16 | four SOIC-8 |
| Parts cost, 8 channels | $17.45 | $8.52 |
| JLC stock | 796 | 2,985 |
| Datasheet | SBAS430F | DS20002249B |

**What the numbers mean in use:**
- **Pitch:** calibration in the EEPROM removes gain and offset error with either part. What
  calibration cannot remove is step size and the INL left between calibration points.
  At 12-bit that residue is a few cents on a good part, tens on a bad one unless many
  points are stored, as the Workshop Computer does with up to 10 per output. At 16-bit it
  is below a cent.
- **Warm-up drift:** the MCP4822's reference moves the top of the range by about 5 cents
  as the case warms 10 °C. The DAC8568's moves it by a fraction of a cent.
- **Slow modulation:** a 2.44 mV step on a slow filter or VCA sweep is rarely audible.
  12-bit is fine for modulation.
- **Pins:** four MCP4822s need three more chip selects than one DAC8568. Rev A has exactly
  two spare pins after MIDI was dropped, so going 12-bit also means 6 DAC channels, not 8,
  or a decoder chip.
- **Cost:** $8.93 a board, so $18 on a 2-board shakedown or $45 on 5.

**Decided (David, 2026-10-14): DAC8568IA.** It is what O&C and Performer use, one chip fits the pin
budget and the area, and at this volume the premium is under $50. The case for 12-bit is
David's own standard — "it's Eurorack, not expected to be spot on" — and it has served
every build so far.

## 8. Power

| Rail | Source | Loads | Part |
|---|---|---|---|
| ±12 V in | Eurorack header → series Schottky each rail → ferrite | — | SS14 **C2480** (Basic). **From 2026-10-15: SS34 C8678 (Basic, 3 A, same SMA footprint), §15** |
| +5 V digital | Buck from +12 V | module, Qwiic, WS2812, 595, VL | TPS54202DDCR **C191884** (261k / $0.18) or AP63205WU-7 **C2071056** (fixed 5 V). **Schematic: TPS54308 (§15)** |
| +5 V analogue | Linear from +12 V, own ground return | PCM3060 VCC, ADS8688 AVDD | L78M05ABDT **C58069** (Basic); low-noise option TPS7A4901 **C16430** ($1.26) |
| +3.3 V analogue | LDO from +5 V analogue | DAC8568, MCP3208 + pot reference | AMS1117-3.3 **C6186** (Basic) or LP2985-33 **C95414**. **Schematic: XC6206 (§15)** |
| +3.3 V digital | LDO from +5 V digital | PCM3060 VDD, ADS8688 DVDD, gate-in pull-ups and threshold, expander, EEPROM, Qwiic, MIDI | AMS1117-3.3 **C6186** (Basic). **Schematic: XC6206 with a 680 Ω minimum load (§15)** |

- **Why a buck:** David's hand-built Daisy modules showed a block-rate comb traced to a
  shared +5 V rail, with a dedicated buck as the fix. Digital and analogue 5 V stay
  separate here for the same reason.
- **Budget (estimate):** +12 V ≈ 120 mA typical, ~350 mA worst case (ESP32 Wi-Fi peaks
  plus a lit LED chain through the buck); −12 V ≈ 25 mA (op-amps). The bus +5 V is never
  used [decided]: every 5 V rail is made on the board.
  **ESP32-P4 case (added 2026-10-15):** the P4 draws 0.45–0.7 A at 5 V. With a lit LED chain
  that is ≈0.75 A from +12 V, hence 3 A Schottkys at the rail entry and Q201 bypassing D203.
  Document it: a module this hungry needs a rack supply with headroom.

## 9. Grounding [proposed]

**One GND net and one unbroken plane on layer 2; separation by placement, not by
splitting.** All three reference Eurorack boards do this (patch.init carrier, Ogham, and
reDIP-SID on four layers). "AGND" and "DGND" survive only as **labels on wiring-field
holes**, so jack and pot returns land near the converters and LED and button returns
near the logic. Jack sleeves and pot grounds reach the board through the deck's D bus and
one wire. Ground doublets go **only on edge positions with no deck cell** (10–16 and
26–31 on each strip): a ground on a cell position would short that cell's pad. USB-to-computer while patched into an audio interface can hum: document it, no
isolation in Rev A.

## 10. Layout rules (from the reference boards) [proposed]

Studied: Electrosmith patch.init carrier (48.5 × 111 mm, 2-layer), Keeos Ogham
(50 × 110 mm, 2-layer, SMT both sides), apf.audio reDIP-SID (4-layer). Lessons:

| Rule | Source |
|---|---|
| **Stack-up:** L1 signals and SMT; **L2 unbroken GND**; L3 power pours (±12 V, 5 V analogue, 5 V digital, the 3.3 V rails); L4 signals | reDIP-SID (L1 signal / In1 power / In2 mixed / B signal) |
| **Zone along the length:** power entry and buck at one end; module and logic in the middle; ADS8688, DAC8568, DG412, PCM3060 and their op-amps at the far end from the buck | Ogham |
| **Low-profile logic under the module on its headers** (MCP3208, 595, LM393s, TCA9555, EEPROM, ≤ 2.5 mm) — agreed. That brings demand from ~85–120 % of the free area down to ~60 % | Ogham (TL072 stage under the Seed); area estimate |
| **0402 passives, TSSOP wherever a variant exists** | area estimate |
| Rail entry: series Schottky → BLM18PG121 ferrite → 10 µF 50 V X7R + 100 nF, per rail (the Basic 10 µF 50 V 1206, C13585, is **X5R**: corrected 2026-10-15) | Ogham |
| Pot and converter references on a linear rail, never the buck or the module's 5 V | Ogham; David's bench notes |
| Gate out: HCT part → 1 kΩ → Schottky clamps to +5 V and GND | Ogham (74AHCT1G125) |
| Gate in: 10k series, BAT54 clamps, then a comparator with a set threshold and hysteresis | Ogham (clock input) |
| Pot inputs: 1 kΩ + 100 nF, 100 kΩ pull-down, pot top on the converter's reference rail | Ogham |
| 74HCT595: OE pulled **high** (gates off) until firmware enables them from a TCA9555 line; MR to VCC. The storage register powers up undefined. | Datasheet behaviour; Ogham ties OE low |
| Spare op-amp sections tied as followers with + to GND | Ogham |
| Power-header symbol: join pins 1–2 (−12 V), 3–8 (GND), 9–10 (+12 V); then confirm every op-amp ±12 V pin has its 100 nF within ~3 mm | review of the boards |
| No tantalum on the ±12 V rails; X7R 50 V instead (X5R 50 V in the schematic: the Basic 10 µF 50 V part; derate for DC bias) | Ogham (schematic note) |
| GND stitching vias at every decoupling cap and around the edge | Ogham (~37) |
| Derate MLCC values for DC bias | reDIP-SID (capacitor notes) |
| 0.45 / 0.2 mm vias only for fine-pitch fan-out (ADS8688 TSSOP-38); three fiducials | reDIP-SID; JLC practice |
| Rules: 0.2 mm track and clearance, 0.5 mm power, via 0.6 / 0.3 mm, 0.5 mm copper to edge, a Power net class — JLCPCB's cheapest tier | Ogham, patch.init |
| Leaded packages only (no QFN/BGA): Economic PCBA's 0.4 mm pitch floor, and no X-ray charge | JLCPCB capabilities and price pages |
| LCSC field on every machine-placed part; everything else marked do-not-place | Ogham |
| Test pads on every rail and on I2S; fiducials | none of the four boards had them |
| Check every decoupling cap's two nets and every polarised part in the PCB, then step through rotations in JLC's preview | review of the boards |

One codec data point (**unverified, 2026-10-15:** Ogham has a PCM3060 only if a Daisy Seed Rev7 is fitted, and its parts list names Rev4): Ogham measured its PCM3060 (single-ended, AC-coupled on the Seed)
at ~4 Vpp, not the 2 Vpp it assumed, and overshot to 19.5 Vpp. Our gain is set from the
datasheet's differential 8 Vpp (§7).

## 11. BOM and cost (per board, parts only)

| Group | $ |
|---|---|
| Converters: PCM3060 4.08, ADS8688 7.32, DAC8568IA 17.45, MCP3208 3.24 | 32.09 |
| Switches and op-amps: 2 × DG412 4.36, 3 × TL074H 0.76 | 5.12 |
| Logic, I/O, memory: 2 × LM393 0.13, 4 × BAT54S 0.08, 74HCT595 0.27, AHCT1G125 0.10, TCA9555 0.56, M24C64 0.15 | 1.29 |
| Power and protection: buck + inductor ~0.30, L78M05 0.21, 2 × AMS1117 0.42, Schottkys, ferrites, BAV99 clamps ~0.60 | ~1.53 |
| Reference, connectors: LM4040 0.47–1.12, JST SH 0.21 | 0.68–1.33 |
| Passives (~150 Basic 0402/0603/0805) | ~1.50 |
| **Total** | **~$41–42** |

- **The DAC is the cost decision**, as v0.1 said, but bigger than it thought: the
  DAC8568IA is 42 % of the parts cost. The 12-bit alternative, 4 × MCP4822 (C16040,
  2,985 in stock, $2.13), is $8.93 less a board. Comparison and decision: §7.1.
- **Extended part types:** ~14 (PCM3060, ADS8688, DAC8568, DG412, MCP3208, TL074H, BAT54S,
  74HCT595, TCA9555, AHCT1G125, LM4040, buck, its inductor, JST SH). Order fees: §12.
  **The schematic has 17 (2026-10-15):** LM4040 dropped; M24C64 (Preferred) counted; the
  review added the 15 V TVS, the 1 nF C0G and the H11L1 (MIDI). List in §15.
- **6HP and 10HP from one design** means one assembly setup per board, not two. With the
  2026-10-16 split there are two designs, the Pico board and the Teensy board, each with its own
  setup, stencils and feeder fees (§12).

## 12. JLCPCB rules and order cost

From JLCPCB's *PCB Assembly Cost: What Does the Price Include?* (help centre, updated
2026-09-09) and *PCB Assembly Capabilities* page, read 2026-10-14:

| | Economic PCBA (our choice) | Standard PCBA |
|---|---|---|
| Placement | single-sided | single or double |
| Layers | **2, 4, 6** | 1–32 |
| Assembled quantity | **2–50** | 2–80,000 |
| Finest package / pin pitch | 0402 / 0.4 mm | 0201 / 0.35 mm |
| Setup | $8.18 | $25.56 single-sided |
| Stencil | $1.53 | $8.21 |
| Placement | $0.0016 a joint | same |
| Extended parts | **$3.07 per Extended part type** | $1.53 feeder loading per Basic or Extended part |
| Hand-soldered through-hole (only if ordered) | $0.0164 a joint + $3.58 an order | same |
| X-ray | charged for QFN/BGA parts | same |
| Finish at 1.6 mm | green, HASL or ENIG | any |

- **v0.1's "$1.50 Extended fee" was Standard PCBA's per-feeder figure.** In Economic it is
  $3.07 a part type.
- **Keep every part leaded** (TSSOP, SOIC, SOT): no QFN, so no X-ray charge. The current
  parts list already does.
- **Whether Preferred parts escape the $3.07** is not stated on these pages †.

**First order, estimated:**

| | 2 assembled | 5 assembled |
|---|---|---|
| Setup + stencil | $9.71 | $9.71 |
| Extended parts (~14 × $3.07) | $42.98 | $42.98 |
| Placement (~700 joints a board) | $2.24 | $5.60 |
| Components (§11, ~$42 a board) | ~$84 | ~$210 |
| Bare 4-layer PCBs (5 off, 49.6 × 103 mm) | † | † |
| **Subtotal before PCBs and shipping** | **~$139** | **~$268** |

Still to check: the 4-layer bare-board price and shipping, both from JLC's online quote.

**Superseded 2026-10-15: double-sided assembly needs Standard PCBA (§14, checkpoint 3),
roughly $100 more per order than the figures below.**

**Updated 2026-10-15:** the schematic has 17 Extended types (§15): 17 × $3.07 = $52.19,
$9.21 more than the table. That gives about **$148** (2 assembled) and **$277** (5), before
PCBs and shipping. Placement rises with the review's extra passives (353 machine-placed
parts).

**Two boards (2026-10-16): one order, two line items.** JLC takes several designs in one cart
and ships them together, so shipping is paid once. Everything else is charged per design: the
bare PCBs, the assembly setup, the stencils and the per-part-type fees. The assembly
therefore costs about twice the one-board figure. A multi-design panel would save a little on
PCBs, but it carries a panel fee and complicates assembly, so two separate designs is the
plan. Confirm on a live quote.

## 13. Decisions

### Settled by evidence in this pass

- Jack switch: DG412 (default-off with pull-downs), Vishay, in stock.
- Gate-out register: 74HCT595D, in stock.
- DAC: DAC8568 grade A on a 3.3 V analogue rail — one part, no level shifter, cheaper than
  two quads.
- Expander: TCA9555 (16 lines, 36k stock); the PCA9557's 8 lines are too few once switch
  enables, buttons and an encoder share it.
- EEPROM: M24C64.
- CV range: ±5 V standard; ±10 V via an OPA4197 option, because TL074 cannot reach it from
  ±12 V rails. (Corrected in §15: the TL074H can, so ±10 V is a resistor variant.)

### Decided by David, 2026-10-14

- One board for 6HP and 10HP: the kits share the breadboard; 6HP connects only the left 40.
- EYESPI dropped.
- Four gate ins.
- XIAO dropped: Pico 2 and Teensy 4.1 only.
- Modules on headers; low-profile SMT under them.
- No TRS MIDI in Rev A. (Reversed 2026-10-15: TRS MIDI is back, §15.)
- DAC: DAC8568IA (§7.1).

### Decided by David, 2026-10-15

- TRS MIDI in and out are back; audio full scale is 20 Vpp in and out; every block gets a
  prior-art review before the schematic pass.
- 15 V TVS diodes at the CV jacks (one new Extended type).
- CV range stays **±5 V**, with a documented ±10 V resistor variant (§15).
- The board accommodates the **ESP32-P4-WIFI6** (§5, §15).
- The power header can go anywhere that keeps power-rail noise away from sensitive parts (§4.3).

### Decided by David, 2026-10-16

- **Two boards:** one for the Pico 2 / ESP32-P4, one for the Teensy 4.1. Both are developed
  together and, if both route, ordered together (§12).
- The Teensy board has **all 48 holes**, so standard full-length headers fit.
- **Four gate outs, no jack detect** (§14, checkpoint 3), to ease routing.
- **The switchable CV jacks stay.** They are the Alchemy Lab's big step in flexibility.
  Alchemy Lab uses the same scheme: an MCU-controlled analogue switch connects or disconnects
  each jack's DAC, with separate input and output scaling. If more must go, TRS MIDI and the
  display connections go first.

### Hardware licence: CC BY-SA 4.0 (decided)

What comparable open projects chose, for the record (each repo's README or LICENSE,
2026-10-14):

| Project | Hardware | Code | Note |
|---|---|---|---|
| Mutable Instruments | CC BY-SA 3.0 | MIT | Why the CCTV and Behringer clones in the rack are legal |
| EuroPi | **CERN-OHL-S v2** | Apache 2.0 | Docs CC0; asks that modified builds not use the brand name |
| apf.audio Tiliqua | **CERN-OHL-S v2** | mixed | Addendum: derivatives may not use apf.audio names |
| Keeos Ogham | CC BY-SA 4.0 | MIT | |
| Westlicht Performer | MIT (everything) | MIT | Fully permissive |
| Workshop Computer, O&C | no hardware licence file in the repo | MIT / GPL-3 per program | |

The three families:
- **Strongly reciprocal** (CERN-OHL-S, CC BY-SA): anyone may build and sell it, but
  anything derived must be published under the same terms.
- **Weakly reciprocal** (CERN-OHL-W): changes to this board must be shared, but it can sit
  inside a closed product.
- **Permissive** (CERN-OHL-P, MIT): anything goes, attribution only.

CERN-OHL is written for hardware; CC BY-SA is a content licence borrowed for it. The
brand-name addendum (EuroPi, apf.audio) is the common way to stay open while protecting
the name. CC BY-SA 4.0 is the current version (Ogham uses it; Mutable used 3.0). Add the
licence file with the first KiCad files.

## 14. From here to the order

**Toolchain** (installed 2026-10-14): KiCad 9.0.7 with the JLC plugin (gerbers, BOM, CPL);
Freerouting 2.5.0 on OpenJDK 21 for non-critical nets; kiutils and easyeda2kicad in the
repo's `.venv` (scripted KiCad edits; exact JLC footprints by LCSC number). No paid tools.

**Checkpoints** — each one is David's to look at before the next step:

1. **Schematic**, as a PDF: KiCad's electrical rules check clean; every IC pin scripted
   against its datasheet pinout; every power pin checked for its decoupling and every
   polarised part for orientation. The pin map (which Pico / Teensy pin goes where) is
   the first sheet. **Drafted 2026-10-14; rebuilt 2026-10-15 after the block review,
   awaiting David's sign-off:**
   decisions in §15. Since the 2026-10-16 split, each board has its own schematic and checks:
   [Pico board](../hardware/analogue_board/pico/analogue_board_pico_schematic.pdf)
   ([checks](../hardware/analogue_board/pico/output/checks.md)),
   [Teensy board](../hardware/analogue_board/teensy/analogue_board_teensy_schematic.pdf)
   ([checks](../hardware/analogue_board/teensy/output/checks.md)).
2. **1:1 printout** of the outline, edge strips, module footprints and power header. David
   lays a real breadboard, a Pico 2, a Teensy 4.1 and the deck header on it. **Prepared
   2026-10-15:**
   [`hardware/analogue_board/checkpoint2_printout.pdf`](../hardware/analogue_board/checkpoint2_printout.pdf)
   (A4, three pages, print at 100 %; since the split, `boards_printout.pdf` has one page with
   each board's module), generated by `tools/analogue_board/printout.py` from
   `placement.py` and the footprints. Proposed there [proposed]:
   - The Pico socket sits 17.4 mm below the top edge, so an ESP32-P4 in it ends 0.5 mm from
     the top. The Teensy sits 3.5 mm down (see the result below).
   - J201 goes bottom right, vertical, pin 1 at (36.83, 83.35), clear of every USB keep-out.
   - Page 3 shows the shared-holes arrangement. Today's netlist would put 7 of its 17 shared
     holes on two different nets, so arrangement A stands.

   **Result (David, 2026-10-15): every measurement agrees with the real parts.** One change
   followed. A card in the Teensy's microSD socket stands just under 3 mm past the Teensy's
   far end, which put it about 2.5 mm past the board's top edge, toward the rail. The Teensy
   socket moved 3 mm down: far end 3.5 mm from the top, USB keep-out now ending at 94.5 mm,
   still clear of J201. The printout was regenerated with the card drawn.
3. **Placement renders**, before routing. **Started 2026-10-15.**
   - **The board generator.** `tools/analogue_board/pcb.py` writes `analogue_board.kicad_pcb` from
     the schematic's netlist: the outline, a JLC 4-layer stack-up (JLC04161H-7628), and every
     footprint with its nets and its link to the schematic. KiCad's schematic-parity check finds
     0 differences. The script also renders both faces into `output/`.
   - **Area budget: one face is not enough.** The courtyards come to 2,600 mm² of SMT parts,
     639 mm² of wiring-field holes, 686 mm² of module header rows and 211 mm² of power header.
     That is 104% of the 3,963 mm² between the edge strips, before any routing, against about
     60–70% for a routable dense board. Cutting features could not close the gap.
   - **Decided by David, 2026-10-15: double-sided assembly** (JLC Standard PCBA; Economic is
     single-sided only). The deck face (B) takes passives and low ICs, about 1.75 mm tall at
     most, which brings SMT use to about 56% of the two faces. That is tight but routable on
     4 layers, and it is how Mutable's and 4ms's modules are built. Cost: about $50 setup,
     about $16 stencils and $1.50 per part type (Basic as well as Extended): roughly $159 for
     the assembly line items, about $100 more per order than Economic. Confirm on a live quote.
   - **Floorplan** (`placement.py`, ANCHORS and HOLE_GROUPS) [proposed; revised 2026-10-15,
     see "Chips level with their bus pins" below]:
     - Analogue at the top, under the modules and furthest from the buck.
     - Down the 9.7 mm channel between the module rows, in the order of the module's buses.
       Outward face: ADC, DAC, MCP3208, codec, TCA9555, one LM393. Deck face: the DG412s, offset
       buffer, audio op-amp, EEPROM, second LM393. The 74HCT595 sits sideways right of the
       channel, beside its gate-out holes.
     - The two CV output op-amps in the top-right corner, one on each face.
     - MIDI (H11L1, ~4 mm tall) bottom left; power around J201 bottom right.
     - The 99 wiring-field holes in three columns lined up with the edge-strip positions: two
       beside the left strip (the only one wired in 6HP), one beside the right strip, stopping
       above J201. Each group sits beside its circuit.
   - **Library changes for this:** the module sockets' courtyards are now their header rows
     (low parts may sit under a module). The wiring holes have their own footprint
     (`WiringHoles_1xNN`) with a one-pitch courtyard, so columns can sit side by side.
   - **Square means ground in the wiring field (David, 2026-10-15).** Every wiring hole is
     round except the ground holes, which are square. KiCad's usual square pin 1 means nothing
     for a single wire, and in the right column, where nearly every hole is its own group, it
     read as a row of grounds. A group with a ground uses a marked variant, such as
     `WiringHoles_1x03_G2` with pad 2 the ground. The schematic decides which variants are
     needed, and `build.py` writes them. There are 11 ground holes: one per bank, plus the
     grounds in the utility groups. The headers keep their square pin 1: the module sockets,
     the edge strips' outer holes, and J201, where it marks −12 V.
   - **Answered by David, 2026-10-15:**
     - *Deck-face clearance.* In 10HP the board sits 11 mm from the deck, and the deck's own
       parts take 2 mm at most, so the deck face has about 9 mm free, room for ~1.75 mm parts
       plus wires. In 6HP there is clearance to the neighbouring modules, helped by most modules
       being shallower.
     - *Wiring field.* The holes are tinned on both faces (HASL, §4.2), so wires route neatly on
       either face, including from the right-hand column across to the left strip in 6HP.
       The hole columns stand as proposed.
   - ~~**Shorter Teensy headers**~~ **Superseded 2026-10-16:** the Teensy has its own board, with
     all 48 holes and standard headers. (David's suggestion, 2026-10-15.) The Teensy's nine far-end
     pins, 20-28 (D28-D36), are all unconnected, so its socket has no holes there. The headers
     become 1×19 (pins 1-19) and 1×20 (pins 29-48), from the USB end. That frees the top
     corners under the module, the most crowded area, and cuts the header-row area from 686 to
     510 mm². `checks.py` lets a socket leave out only pins the netlist leaves unconnected.
     **Build rule:** fit the Teensy with headers on pins 1-19 and 29-48 only. Full-length
     headers would leave bare pin tips about 2.5 mm above parts up to 1.75 mm tall.
   - **First-pass placement of every part (2026-10-15)** by `tools/analogue_board/autoplace.py`.
     Each part goes as close as it fits to the pins it connects to. A decoupling capacitor aims
     at the exact pin its Decouples field names. A part prefers its IC's face, and chains grow
     outward from the ICs. The buck's capacitors and its inductor stay on its face, so the
     switching loop never runs through vias.
     - Result: all 406 parts placed, 206 on the outward face and 200 on the deck face.
     - Checks: no courtyard overlaps, schematic parity clean, and nothing over 2.5 mm under
       the modules or over 8 mm in the USB keep-outs.
     - Reference designators are off the silkscreen for passives (still on the fab layer); ICs,
       connectors and hole groups keep theirs.
   - **Routability estimate (2026-10-15).** The signal nets need about 530 connections and
     about 3.8 m at their shortest. Three signal layers hold roughly twice that, so the board
     as a whole has room. There are at least 500 vias: the ground and rail pads, plus the
     connections that change face.
     The constraint is the module header rows. A gap between two header pins takes one
     track per layer at 0.2 mm rules. The gate outputs crossing the rows were at 117–167% of
     that capacity, and the pot inputs at 100%.
   - **Space reclaimed (David's suggestion, checked against
     `tools/visualizer/boards/n8synth-10hp.json`).** The right strip serves only the 10HP
     deck, whose headers sit at 1–10, 16–25 and 31–40. Positions 11–15 and 26–30 never carry a
     header, so they have no holes (`placement.STRIP_OMIT`). Positions 10, 16 and 31 are pins
     of the 10-pin headers that no cell uses, so they keep only the outer hole
     (`placement.STRIP_OMIT_INNER`, David). The left strip
     keeps all 40, because a 6HP deck claims everything except 19–22 and the 10HP deck uses
     those.
   - **74HCT595 in TSSOP-16** (74HCT595PW,118, C99710, Nexperia, same pinout as the SO16 on
     the same datasheet page). Turned sideways, it fits the channel beside its gate-out holes,
     so only its four control lines cross the module rows. With the right strip cut, the gate
     crossings drop to 50–75% of capacity. The pot crossings (Pico left row, y 50–60) stay at
     100%; finer track rules through the header gaps (0.127 mm) would double that band's
     capacity.
   - **Qwiic socket vertical (David, 2026-10-15):** BM04B-SRSS-TB(LF)(SN), C160390, in place of the
     side-entry SM04B. The side-entry socket's plug would have had to enter along the board,
     straight into the MIDI opto. The vertical one sits just below the modules at (37.4, 74.6),
     outside the USB plug zones and clear of J201, and its cable leaves straight up from the
     outward face.
   - **The wiring field becomes four mixed banks (David, 2026-10-15).** Each bank sits in a
     quarter of the board and holds some of every channel type, so a panel part anywhere on
     the deck has its channel close by. Previously each function's holes sat in one group on
     one side. The split is 50/50 left and right: David's point is that even a 6HP build
     (left strip only) has plenty within reach.
     - Left top: CV1, CV2, CV5, CVI7, AIN1, POT1-2, GIN1, GOUT1-2, SW1-3.
     - Left bottom: CV3, CVO7, AOUT1, POT3-4, GIN2, GOUT3-4, SW4-5.
     - Right top: CV4, CVI8, AIN2, POT5-6, GIN3, GOUT5-6, SW6-7.
     - Right middle: CV6, CVO8, AOUT2, POT7-8, GIN4, GOUT7-8, SW8-9.
     - Every bank has one pot-top reference hole and one ground hole; pot and jack grounds
       go to the deck's D bus.
     - Each input's jack-detect hole sits beside it: on the left in the inner column next to
       the input, on the right directly below it.
     - The utility groups (spare GPIO and MIDI links, codec reset, MIDI, I2C display, LED
       chain, gate expansion) stay whole on the left.
     - The right column's 30 slots above J201 set the CV split at 6 left / 4 right.
     - 94 holes, down from 99. `tools/analogue_board/wiring.py` holds the plan slot by slot; the
       schematic and placement both read it.
     - Cost: the shortest wiring rises from 3.8 to 4.7 m. The module header rows on the right
       reach 100-108% of one-track-per-gap capacity at y 30-60; finer rules through the gaps
       would halve that.
   - **Design rules** (`pcb.py`, written into the project). Default net class: 0.15 mm tracks,
     0.15 mm clearance, vias 0.45/0.2 mm. Power net class (the rails): 0.3 mm tracks, vias
     0.6/0.3 mm. Both are inside JLC's 4-layer limits (0.09 mm tracks, 0.2 mm via drill).
     In1 is a solid ground plane. Two 0.15 mm tracks fit through the 0.84 mm gap between two
     1.7 mm header pads, so the header rows carry two tracks per gap per layer.
   - **Chips level with their bus pins (2026-10-15).** The first trial autoroute stalled.
     Freerouting's fan-out reached 93% of the pads, but 448 connections were still open when it
     was stopped, because the floorplan had ignored the module pins. The codec sat in the top
     right, 38 mm from the Pico's I2S pins, and the TCA9555 sat below the modules. Each bus
     chip now sits level with its bus pins on both modules: SPI-A (ADC, DAC) at 19–38 mm,
     SPI-B (MCP3208, 74HCT595) at 15–34 mm, I2S (codec) at 34–56 mm and I2C (TCA9555,
     EEPROM) at 43–59 mm. The module pins for one bus sit at similar heights on the Pico and
     the Teensy, so one position serves both.

     Mean distance from each chip's pads to the module pins it connects to:

     | Chip | Before: Pico / Teensy | After: Pico / Teensy |
     |---|---|---|
     | Codec | 38 / 44 mm | 6 / 11 mm |
     | MCP3208 | 27 / 37 mm | 11 / 16 mm |
     | TCA9555 | 22 / 28 mm | 13 / 11 mm |

     The shortest total wiring falls from 4.7 to 4.4 m.

     The busiest wall is still the Teensy's right row at y 30–60. Every Pico right-row signal
     bound for the channel passes between its pins, a consequence of the two modules
     interleaving. It is at 54–67% of capacity at two tracks per gap. All 430 parts are
     placed, with parity clean, no overlaps and no height problems.
   - **Trial autoroutes on the shared board (2026-10-15/16)**, with Freerouting 2.5 run by
     `tools/analogue_board/autoroute.py` on a copy of the board:
     - First run, 80% routed. Freerouting also routed signals through In1, which cut the ground
       plane into islands. Fix: In1 is now a "power" layer, so autorouters keep off it.
     - Second run, In1 kept whole: 283 of 992 connections unrouted after filling the plane.
       39 were ground, 36 power (pours on the final board), and **208 signal**. 192 of those
       208 were in the module area (x 12–37, y 10–62 mm), between the interleaved header rows.
       The wiring field and the bottom third routed. Four layers could not carry two
       interleaved modules.
   - **Two boards (David, 2026-10-16).** One board for the Pico 2 / ESP32-P4 and one for the
     Teensy 4.1, from the same generator (`variant.py`; every script takes `pico` or `teensy`).
     - **Shared:** every peripheral sheet, the libraries
       (`hardware/analogue_board/analogue_board.pretty`, `.kicad_sym`), the edge strips, the
       wiring field and the power corner.
     - **Each board:** its own project (`hardware/analogue_board/pico/`, `.../teensy/`), root
       sheet and floorplan.
     - **The Pico board only:** the ESP32-P4 bypass (Q201, JP201) and J101's RUN hole. The
       Teensy board's J101 has five holes.
     - **Module positions:** each module sits on the board's centre line, at the height
       checkpoint 2 settled. That moves the Teensy 3.8 mm right of its checkpoint 2 position,
       which gives it a 5 mm passives lane on its left and a 7.6 mm chip lane on its right.
       `boards_printout.pdf` has the new positions to check with real parts.
     - **Floorplans** (`placement.ANCHORS_BOARD`): each bus chip is level with its bus pins on
       the side they come out.
       - *Pico board:* the CV converters and op-amps sit above the pins, under the ESP32-P4's
         antenna end. Down the channel: MCP3208, codec and TCA9555, each on the side of its
         bus. In the right lane: the 74HCT595 and the comparators.
       - *Teensy board:* down the channel in bus order: MCP3208, ADS8688, codec, TCA9555. In
         the right lane: the 74HCT595, the CV op-amps, the DAC (sideways, beside its op-amps)
         and the comparators.
     - **Result:**

       | | Pico board | Teensy board |
       |---|---|---|
       | Parts | 429 | 425 |
       | One-face area use | 89% (95% on the shared board) | 89% |
       | Shortest wiring | 3.9 m (4.4 m shared) | 4.2 m |
       | Busiest header wall | 58% | 83% |

       Both boards have every part placed, parity clean, no overlaps and no height problems.
   - **Trimmed to ease routing (David, 2026-10-16).**
     - **Four gate outs**, one per bank, from QA–QD of the 74HCT595. QE–QH are unused; J603
       still chains a second 595.
     - **No jack detect.** The probe network (15 resistors, a clamp, a test pad) and its 14
       holes are gone, and the module pin it used (Pico GP15, Teensy D6) is free.
     - **The banks are packed from the top of each:**
       - Left top, slots 1–7: CV1, CV2, CV5, CVI7, AIN1, GIN1, POT1–2, GOUT1, SW1–3.
       - Left bottom, slots 21–26: CV3, CVO7, AOUT1, GIN2, POT3–4, GOUT2, SW4–5.
       - Right top, slots 1–11: CV4, CVI8, AIN2, GIN3, POT5–6, GOUT3, SW6–7.
       - Right middle, slots 17–27: CV6, CVO8, AOUT2, GIN4, POT7–8, GOUT4, SW8–9.
       - Each bank keeps its POT_REF and ground hole.
     - **Result:** 398 parts on the Pico board and 394 on the Teensy board, 31 fewer each.
       One-face area use falls to 83–84%. The wiring field drops from 94 to 76 holes (75 on
       the Teensy board).
   - **Trial autoroutes, 2026-10-16** (Freerouting 2.5, this project's rules, In1 a solid ground
     plane). The table counts the signal connections left unrouted; ground and rail leftovers
     come on top, about 60–85 per board:

     | Board | 4 layers | 6 layers |
     |---|---|---|
     | Shared board, full feature set | 208 | 142 |
     | Pico board, before trims | 182 | — |
     | Pico board, trimmed | 162 | 106 (81% of all connections routed) |
     | Teensy board, before trims | 183 | — |
     | Teensy board, trimmed | 170 | 102 (81%) |

     - **Value of each change:** six layers removes about 35% of the leftovers, the split about
       12% and the trims 7–11%.
     - **Where the leftovers are:** on every board they concentrate around the CV converters and
       their op-amps. The auto-placer packs each passive against its chip and leaves no track
       channels, so placement, not layer count, is now the main limit.
     - **Freerouting itself:** each run's first pass was within one connection of its final
       result, so later passes add nothing.
     - **Not yet routable:** neither board routes on 4 or 6 layers as placed.
     - **The shared board, revisited (`build.py shared`, the same trims and fixes, both sockets
       interleaved, the Teensy on shortened headers):** 184 signal connections left unrouted on
       4 layers and 139 on 6. The current Pico board leaves 88 on 6 layers, 37% fewer.
     - **Totals across both split boards:** about 190 to finish by hand, against 139 on the one
       shared board.
     - **The trims barely help the shared board** (142 down to 139). Its limit is the
       interleaved header rows.
     - **Repeatability:** a repeat run on the Pico board gave the same fan-out and a total
       within 3%.
   - **Quilter (quilter.ai), 2026-10-16, Pico board, 6 layers.** Quilter placed and routed a
     candidate: 877 of 885 connections, parity clean, no height problems. It is not usable as it
     stands:
     - It placed the ±12 V entry diodes and ferrites about 80 mm from J201.
     - It placed the codec, the audio op-amp and the DAC within about 10 mm of the buck.
     - It routed every rail at 0.133 mm, having replaced our Power net class with its 0.127 mm
       default.
     - It used 0.127 mm rules, the spacing it chose (about 0.4 mm), and almost nothing under the
       module.

     What it proved: the board can route on 6 layers once the parts are spaced out. Quilter is
     also tied to its web interface, which only David can drive.
   - **The core board and the two-stage route (2026-10-16).** `pico_core` is the Pico board
     without the fixed-direction CV channels, TRS MIDI or the Qwiic socket, with six pots.
     - **Kept:** the six switchable CV jacks, stereo audio, four gate ins and outs, nine button
       lines, the LED chain, the EEPROM and the I2C display holes. David's line: fewer than six
       switchable jacks and the board is no better than a patch.Init.
     - **Size:** 354 parts, 72% of one face.
     - **Placement and rules:** parts placed 0.4 mm apart (`variant.SPACING`), signals at
       0.127 mm track and space (`variant.TRACK`), rails still 0.3 mm.

     Freerouting on 6 layers, leftovers:

     | Run | Signals | Rails | Ground | Routed |
     |---|---|---|---|---|
     | Defaults | 47 | 7 | 27 | 89.8% |
     | Higher start rip-up cost (400) | 23 | 7 | 22 | 93.4%, but 142 tracks narrowed below 0.127 mm by the fan-out stage |
     | No fan-out stage | 1 | 39 | 200 | 69.7% |
     | No fan-out, cheaper vias (20, plane 2) | 1 | 23 | 200 | 71.8% |
     | **Stage 2:** the run above, every track locked, fan-out on | 1 | 7 | 41 | 93.8% |
     | **Stage 3:** locked again, plane vias 1, rip-up 400 | 1 (CODEC_VCC, a supply node) | 6 | 30 | 95.3% |

     - **The finding:** Freerouting's fan-out stage drops a via beside every SMD pin before
       routing, and on a board this dense those vias block the tracks. That is also why no pass
       ever beat the first. Routing the signals with fan-out off, then locking them and running
       again with fan-out on for the ground and rail connections, routes every signal.
     - **What is left:** 30 ground pads that need a via to the plane, 6 rail connections and
       CODEC_VCC. The DRC findings are small fixes:
       - 17 copper-to-edge
       - 11 hole clearance
       - 10 vias that came back from the session import as 0.45/0.3 mm
       - 6 clearance
       - 3 mask bridges
     - **Kept:** the routed board is in `hardware/analogue_board/pico_core/routed_trial/`.
     - **How to repeat it:**

       ```sh
       autoroute.py pico_core 20 6 nofanoutcheap --router.automatic_neckdown=false \
           --router.hole_clearance_um=250 --router.fanout.enabled=false \
           --router.scoring.via_costs=20 --router.scoring.plane_via_costs=2
       ```

       Then run it again on the trial board it writes, with `--lock-existing` and the fan-out
       left on.
     - **Freerouting's own settings:** its usage analytics were on by default; `autoroute.py`
       now switches them off on every run. The v1.9 algorithm named in its settings is not in
       the 2.5 build, which falls back to the current one.
   - **One board again: `shared_core` routes (2026-10-16).** David's choice for the order: one
     board for both module formats.
     - **Contents:** the Pico 2 / ESP32-P4 and Teensy 4.1 sockets interleaved as at checkpoint 2,
       the Teensy on full-length headers (it arrives with them fitted), TRS MIDI, a display on the
       I2C holes only, six switchable CV jacks, six pots, four gates each way.
     - **Size:** 372 parts, 85% of one face.
     - **Placement:** 0.4 mm part spacing, 0.127 mm signal rules. Two auto-placer fallbacks:
       - a part with no room at that spacing tries tight spacing;
       - a part with no room within 22 mm takes the nearest free spot anywhere (C308 and D601
         needed it, at the crowded top left).
     - **Routing:** `autoroute.py shared_core 20 6 --staged` runs the three stages:

       | After stage | Signals | Rails | Ground | Unrouted of 852 |
       |---|---|---|---|---|
       | 1: fan-out off, cheap vias | 2 | 25 | 207 | 234 |
       | 2: fan-out on, stage 1 locked | 0 | 7 (+5VD) | 30 | 37 |
       | 3: plane vias 1, rip-up 400 | 0 | 7 | 29 | 36 |

     - **The rails** are at the Power class's 0.3 mm throughout, and the ±12 V entry runs about
       6 mm from J201.
     - **Heights:** no problems.
     - **DRC, excluding silkscreen:**
       - 14 copper-to-edge
       - 12 hole clearance
       - 8 vias imported at 0.45/0.3 mm
       - 4 clearance
       - 2 mask bridges
     - **Kept in:** `hardware/analogue_board/shared_core/routed_trial/`.
     - **Why the interleaved rows no longer matter:** every earlier comparison had fan-out on,
       and the shared board's interleaved header rows left its pre-placed vias the least room.
     - **Remaining to an order:**
       1. Script a ground via beside each of the 29 pads.
       2. Reset every via to its net class's size.
       3. Route the 7 +5VD connections.
       4. Give Freerouting the 0.5 mm edge clearance and fix the remaining DRC findings.
       5. Review the analogue and ground layout by eye.
       6. Put the silkscreen labels on.
       7. Generate the fabrication and assembly files (Gerbers, drill, BOM, positions with JLC
          rotations).
       8. Run JLC's DFM check and get a live 6-layer double-sided quote.
     - **Next:** Quilter (quilter.ai, place and route) as an independent check of whether
       better placement routes. `pcb.py <board> --quilter` writes the upload sets to
       `<board>/output/quilter/`, on 6 layers. In1 is GND and In4 is PWR, the power layer for
       rail pours that Quilter asks for.
   - **One pin per pad (2026-10-16).** Quilter's first run warned of a "pin count mismatch"
     between schematic and board. KiCad accepts the parts that caused it, but a strict importer
     does not, so every part now matches pin for pin:
     - **Edge strips:** each hole has its own pin, the deck hole *n* and its wiring hole *n*+40,
       joined by the net DECK_L*n* or DECK_R*n*. The right strip's symbol has pins only for the
       holes that exist.
     - **Qwiic socket:** each mounting tab is its own pin.
     - **L78M05:** the DPAK's paste openings are stencil shapes, not unnumbered pads.
     - **Result:** the copper is unchanged, and the parity check no longer needs its "intended
       omission" exception. Only the fiducials keep 0 pins against 1 pad, as every board does.
   - **USB keep-out.** It constrains almost nothing. The module stands on 8.5 mm headers, so a
     USB plug passes over anything shorter than about 8 mm. Only J201 with its ribbon plug,
     and a Qwiic cable, are tall enough to matter, and both sit outside the zone. The
     auto-placer ignores the zone; `pcb.py` only flags parts over 8 mm inside it.
   - **Next:** finish `shared_core`, the board for the order. Its list is above. The split
     boards and the full feature set were not taken further. The earlier plan, kept for
     reference:
     1. Run the full Pico board, and then the Teensy board, through the two-stage route with
        0.4 mm spacing and 0.127 mm rules, to see whether the full feature set routes as the
        core set did.
     2. Script the ground vias for whatever is left, then fix the remaining DRC findings.
     3. Review by block: analogue grouping, ground returns, the codec and ADC corners, rail
        widths and pours.
     4. Put the hole labels on the silkscreen, one channel name per hole, from `wiring.py`.
     5. Confirm the 6-layer price on a live JLC quote, then order.
   - **The first complete route: `teensy_core_midi` (2026-10-16).**
     - **Method, all scripted:**
       1. Before routing, every surface-mount ground pad gets its own via to the plane,
          straight out along the pin for a chip (`--ground-vias`). Left to itself, Freerouting
          joined ground pads to each other: 207 pads shared 38 vias, through 567 mm of track.
       2. Before routing, each decoupling capacitor is wired to the pin it serves
          (`--decoupling`). Left to itself, the router left half the IC power pins more than
          4 mm of track from any capacitor.
       3. Freerouting runs stages 1 and 2. Stage 3 made 2 connections in 25–35 minutes on
          every board, so it was dropped.
       4. `finish.py` closes what is left: copper faults taken up; leftovers routed on a
          0.05 mm grid; then rip-up and reroute; dead ends removed.
     - **Placement fixes found along the way:**
       - On every floorplan, the DG412s sat under the ADC with their pad columns opposite its
         own, so their vias fought for the same strips. Each now turns 90°.
       - The auto-placer charges 3 mm for each module header row between a part and its pins.
       - FB301 sits beside the codec pin it feeds, not 28 mm away.
     - **What each board reached:**

       | Board | After stage 1 | After stage 2 | After `finish.py` |
       |---|---|---|---|
       | `shared_core`, four placements | 24–26 | 7–16 | 2 every time, a different 2 |
       | `shared_core`, 0.1 mm rules | 57 | stopped (11 min a pass) | — |
       | `pico_core_midi` | 48 | 21 | (running) |
       | `teensy_core_midi` | 13 | 9 | **0** |

     - **David's review by eye made the difference on the Teensy board:**
       - The 595 moved into the void left of the left header row, where the inner wiring
         column has no holes.
       - The LDO moved out from under the module's lower end.
       - Five right-column holes (SW7, GND, CV6, AOUT2, GIN4) moved into the right strip's
         empty positions 11–15, so U502, U501 and U801 slide right and leave a lane beside the
         header row. That move is on the Teensy board only, so its wiring field differs from
         the Pico board's.
       - Bringing the module 10 mm lower was tried and undone: no chip measured better in the
         freed band, and it brought the codec and comparators nearer the buck.
     - **Result:** KiCad's DRC finds 0 unconnected items and 0 copper faults. What it still
       lists is 102 silkscreen overlaps and 39 library notices from the trial folder.
     - **Kept in:** `hardware/analogue_board/teensy_core_midi/routed_trial/`.
     - **To the order, done the same day:**
       1. **Decoupling, by routed track from capacitor to pin:**
          - Two of the flagged pins are not supply pins: U501 pin 9 is the DAC's CLR and
            U602 pin 10 the 595's MR, both tied high.
          - Four are over 4 mm: C408 to U401 pin 5 (REFIO) at 9.2 mm, C416 to U402 pin 4
            (−12 V) at 5.8 mm, C604 to U601 pin 15 at 4.7 mm, C217 to U202 pin 3 at 4.3 mm.
          - `finish.py` now adds a direct track where one fits, crossing other nets if need
            be, but no shorter path fits here: the vias of the chip on the other face stand
            between C416 and its pin, and REFIO's only short path crosses REFCAP's.
          - Accepted for Rev A (David): all are DC references or a low-current, slow-switching
            supply.
          - For the Pico board: no vias between a capacitor and its pin.
       2. **Labels:** `labels.py` puts block numbers beside the wiring blocks (David's choice
          over signal names, which do not fit between holes on a 2.54 mm pitch) and names
          beside the test points. Eight of nine blocks and 15 of 27 test points have room. W8,
          the five holes in the right strip's gap, is unmistakable without one.
          `output/wiring_map.md` lists everything.
       3. **SMA diodes:** their pads match KiCad's library exactly. The mismatch notice comes
          from their sitting on the deck face.
       4. **`fab.py`:** 300 placements (159 outward, 141 deck), 59 part types (43 Basic, 16
          Extended). The Teensy headers and J201 are hand-soldered. Files in
          `teensy_core_midi/fab/`.
     - **Test points, for the Pico board:** 18 of the 27 are on bus lines, every one of which
       can be probed at the module socket's solder joints. Dropping them frees about 79 mm²
       and 18 branches in the busiest area.
     - **Ordered (David, 2026-10-16):** JLCPCB, 5 boards and 2 assembled on both faces, OSP
       finish, £268 with the shipping coupons, before import VAT.
   - **The Pico board routes too: `pico_core_midi` (2026-10-17).**
     - **The pattern behind the failures**, from six routes and 102 leftover connections:
       - 71 were rails;
       - over half sat at the ADC, DAC, a DG412 or the analogue regulator;
       - the jams came from chips stacked on opposite faces, whose vias fence in each other's
         pins.
     - **What changed:**
       - **A +5VD plane on In4** (`autoroute.py --plane=+5VD`). It took stage 1 from 35 left
         to 14.
       - **Escape lanes.** ADC pin 2 was fenced in by six ground vias, each legitimate for
         its own pad. The pre-route ground vias now keep a lane clear off the end of every
         chip's signal pin.
       - **David's re-laid top:** no chip over another on the opposite face. The ADC is
         lowered; the DAC and CV op-amp are turned and stacked; the DG412s and U504 sit where
         nothing is above them; the analogue LDO is moved out of the band.
     - **Result:** 7 left after stage 1 and 4 after stage 2, the best of any board. Then
       **0 unconnected and 0 copper faults** after `finish.py`, and every IC supply pin within
       4 mm of its capacitor.
     - **Also fixed in `finish.py`:**
       - an empty route that looped for five hours overnight;
       - a grid marked one cell at a time, so long connections took hours;
       - a dead-end clean-up that ignored planes.
     - **Kept in:** `pico_core_midi/routed_trial/`; order files in `pico_core_midi/fab/`.
     - **Held (David):** the order waits on the Teensy board's bring-up.
     - **The story of both boards:** [`analogue_board_journal.md`](analogue_board_journal.md).
4. **Routed board**, clean against the design rules, with test points on every rail and
   bus and 0 Ω links in each supply so a faulty rail can be isolated.
5. **JLCPCB quote and preview**, rotations checked, "Confirm Parts Placement" ($0.45)
   ticked, before paying. Then 5 PCBs, 2 assembled.

Rev A is expected to need a few bodge wires. An outside layout review (KiCad forum,
r/PrintedCircuitBoard) is held in reserve for if it does not bring up.

The CC BY-SA 4.0 licence is in `hardware/analogue_board/LICENSE`.

## 15. Checkpoint 1: what the schematic decided [proposed]

The schematic is generated by `tools/analogue_board/build.py` and checked by script: ERC 0 errors
0 warnings; netlist identical to the generator's intent; every IC pin against
`datasheet_pins.json`, transcribed from the datasheets independently of KiCad's library;
footprint pads against symbol pins; a decoupling capacitor on all 34 IC power pins; all 18
diodes oriented. 300 parts, 14 Extended part types (as §11 estimated), 32 Basic.

**Rebuilt 2026-10-15** after the block review, with the same checks:
- ERC 0 errors, 0 warnings.
- Netlist identical to intent: 345 nets, 1,274 pins.
- 21 ICs against their datasheets; 48 symbol/footprint pairs.
- Decoupling on all 36 IC power pins; all 29 diodes and the FET oriented.
- 356 BOM parts, 353 of them machine-placed: **17 Extended part types**, 44 Basic.

Ten sheets, the pin map first; every sheet was also checked by eye for overlapping text.

### Changed from this spec

| Item | Spec said | Schematic has | Why |
|---|---|---|---|
| +5 V digital buck | TPS54202 or AP63205 | **TPS54308DDCR** C168839 (1,005 / $1.79): forced PWM, 350 kHz. The TPS54202 drops into the same footprint with the same parts | Both listed parts pulse-skip at light load (TPS54202 below ~300 mA peak, AP63205 PFM), which puts switching bursts in the audio band: the noise the separate buck exists to avoid. Values from TI's 5 V table: 15 µH (SWPA5040S150MT, C44888), 2 × 22 µF; divider 15k/2k = 5.07 V from Basic parts |
| 3.3 V rails | AMS1117-3.3 | **XC6206P332MR** C5446 (Basic), one per rail | The AMS1117 datasheet wants 22 µF solid tantalum on the output for stability, and JLC has no Basic 22 µF tantalum. XC6206: ceramic-stable, 200 mA (loads ≈50 mA and ≈6 mA) |
| Gate-in comparator supply | LM393 on +5 V | **LM393 on +12 V** | The clamp holds the input at ≈3.6 V for any gate above ~4 V. At 5 V the LM393's common-mode range ends at 3.5 V; at 12 V, 10.5 V |
| LM4040 | 4.096 V shunt for the calibration check | **dropped** | The ADS8688's gain error, ±0.05 % FSR max, beats the LM4040A's 0.1 %. Its AUX input's full scale is 4.096 V, so a 4.096 V reference would sit at the clip point |
| DG412 enable pull-downs | "pull-down" | **4.7 kΩ** | The TCA9555 has internal pull-ups (IIL up to 100 µA): 4.7 kΩ holds a line at ≤ 0.47 V, under the DG412's 0.8 V |

### Settled where the spec left it open

| Item | Schematic has | Why |
|---|---|---|
| −5 V offset for the CV outs (§6.4) | Taken from the DAC8568's own 2.5 V reference: 10k/20k divider, 1 µF, a TL074H follower → OFFSET_REF 1.667 V into each stage's 10 kΩ; gain 1 + 30k/10k = 4, so Vout = 4·Vdac − 5 V. **Changed 2026-10-15:** 12k/22k divider and 1 nF → OFFSET_REF 1.618 V; gain 1 + 33k/10k = 4.3, so −5.34 … +5.41 V, ±5 V inside the DAC's specified codes | Mid-code is 0 V whatever the reference does. Costs a fourth TL074H (same part type, no fee); its three spare sections are grounded followers |
| Codec straps | MODE 220 kΩ to ground (hardware mode, differential outputs). FMT, DEMP, IFMD each 10 kΩ to ground (I2S, no de-emphasis, slave). RST pulled up through 1 kΩ | Pull-downs rather than hard ties, so a strap can be changed with a bodge |
| Audio in | 1 µF 50 V X7R, then 100 kΩ into an inverting TL074H with 33 kΩ ∥ 100 pF, + input on VCOM, then 1 kΩ into the codec's 10 kΩ: gain −0.30. 1 MΩ to ground at the jack. BAT54S clamps to +5VA. **Changed 2026-10-15:** feedback 15 kΩ ∥ 100 pF, gain −0.136, so 22 Vpp → 3 Vpp; 100 nF on each + input | Inverting: firmware flips the sign |
| Audio out | 12 kΩ / 15 kΩ difference amp (×1.25), 100 pF C0G across each 15 kΩ (pole at 106 kHz), 1 kΩ out. **Changed 2026-10-15:** balanced second-order MFB (Beads' topology), 12k in, 1k to each input, 30k feedback and 30k to ground, 1 nF C0G across the two nodes, 100 pF at each input: gain 2.5, f0 ≈ 65 kHz, Q ≈ 0.73; 1 kΩ 1206 out | Larger C0G values are not Basic. The codec has its own RC filter; 330 pF (Extended) would move the pole to 32 kHz. The MFB needs one Extended 1 nF C0G |
| Gate-in values | 10 kΩ, BAT54S to +3V3D/GND, 100 kΩ to ground, 100 kΩ hysteresis, 10 kΩ pull-up. GATE_TH = 1.65 V from one 10k/10k divider | Trips at 1.98 V rising, 1.67 V falling at the jack |
| Jack-detect probe (**dropped 2026-10-16**) | GPIO → 1 kΩ → bus with a BAT54S clamp → 14 holes: PR1-10 through 100 kΩ (audio and CV ins), PR11-14 through 22 kΩ (gate ins) | A 100 kΩ probe lifts an unpatched gate input only to ≈1.24 V, under the threshold |
| Chip-select pull-ups | 10 kΩ to +3V3D on CS_ADC, CS_DAC, CS_POT | Every module leaves its pins floating while it boots; this keeps the converters deselected and off MISO |
| Bus-merge jumpers (§6.3) | Not fitted | The Teensy 4.0 is not a target; both target modules have two hardware SPI buses |
| Gate-out expansion | J603: QH′, SRCLK, RCLK, +5VD, GND | Chains a second 74HCT595 off-board (Boy's expander) |
| Rail links and test pads (checkpoint 4) | A 0 Ω link after every regulator; test pads on every rail, on I2S and on both SPI buses and I2C | Fitted now rather than at layout |
| Edge strips | 80 positions, outer and inner pads sharing a pad number; nothing tied to GND | All 80 stay free tie points; a GND wire goes to any free position if wanted |

### Decided and corrected, 2026-10-15

**Decided by David:**
- **TRS MIDI in and out are back** in Rev A, reversing §1 and §13. They use the two
  UART-capable spare pins (Pico GP0/GP1 = UART0, Teensy 1/0 = Serial1); no other pins are
  needed. The circuit comes from the block review below.
- **Audio full scale is 20 Vpp, in and out**, as every published PCM3060 Eurorack design
  has it. Firmware runs at about 10 Vpp nominal, leaving 6 dB for peaks, and hot 20 Vpp
  sources no longer clip the inputs.
- **Block-by-block prior-art review** of every stage before the schematic pass, with
  results in `docs/analogue_board_review/`.

**Corrections to earlier sections:**
- **TL074H swing** (§1, §7, §13): the TL07xH datasheet (SLOS080W) gives output swing within
  0.2 V of each rail into 10 kΩ, about 1 V into 2 kΩ. From ±11.6 V rails that is
  about ±11.4 V, so 20 Vpp audio and ±10 V CV are open to the TL074H. The "needs OPA4197"
  claim came from the old TL07x die.
- **Patch SM audio out** (§6.5): 17.3 Vpp full scale from a balanced second-order MFB at
  ×2.17, not ±5 V (survey: `docs/analogue_board_review/codec_pcm3060.md`).
- **Ogham's codec** (§6.5, §10): it is a PCM3060 only if its Daisy Seed is Rev7; its parts
  list names Rev4 (AK4556). The 4 Vpp data point is unverified.

**Decided by David, later the same day** (on the review's open items):
- **15 V TVS at each CV jack: yes.** PESD15VL1BA (C85378), one new Extended type.
- **CV range stays ±5 V**, with a documented ±10 V resistor variant: Rf 75k, divider 15k/20k,
  all Basic. That gives gain 8.5, OFFSET_REF 1.429 V and −10.71 … +10.54 V; it needs ≥ 10 kΩ
  loads and is calibrated within the ADC's ±10.24 V range.
- **The ESP32-P4-WIFI6 is accommodated** (§5): Q201 and JP201 below, a firmware rule, and
  board length at checkpoint 2.
- **The power header is free to move** (§4.3): place it to keep power-rail noise away
  from sensitive parts.
- **DAC8568 grade A reference drift** (§7.1): 5 ppm/°C typ, 25 max. The 2 ppm figure is
  grade C.
- **Rail capacitors** (§10): the Basic 10 µF 50 V 1206 is X5R, not X7R. Allow for DC-bias
  derating.

### Applied from the block review, 2026-10-15

Every A and B item in `docs/analogue_board_review/README.md`, as now drawn:

| Block | In the schematic | Cost |
|---|---|---|
| Power | 680 Ω minimum load on +3V3D (R210): the gate-input clamps push ≈3.4 mA into a rail whose XC6206 can't sink it | Basic |
| Power | Buck input on its own ferrite (FB203) with 2 × 10 µF 50 V + 100 nF; EN divider 510k/75k, so +5VD starts at ≈9.2 V and stops at ≈8.1 V, never running without +5VA; feed-forward 470 pF + 2 kΩ drawn, not fitted | Basic |
| Power | **SS34** (C8678, 3 A, same SMA footprint) for D201–D203 in place of the 1 A SS14: +12 V can reach ≈0.75 A with an ESP32-P4 and a lit LED chain | Basic |
| Power | **MOD_5V bypass for the ESP32-P4:** Q201 (AO3401A, C15127) across D203, gate on PICO_VBUS, 1 MΩ to MOD_5V. JP201 (open by default) ties the gate to 100 kΩ to ground. Bridged: the FET is on, unless USB powers the module, which turns it off (the Pico 2 datasheet's VSYS circuit). Open, for a Teensy: off | Basic |
| Codec | Ferrite into VCC (FB301), 5.1 Ω into VDD (R304), each with its own 10 µF + 100 nF; 100 nF from VCOM at each audio-input + pin; CODEC_RST to a hole (J303) | Basic |
| Codec | 20 Vpp in and out (the two rows above) | one Extended (1 nF C0G) |
| CV in | 15 V TVS at each jack; 1 nF at each ADC input; the switch-path 1 kΩ in 1206; 10 kΩ from +5VA to ground, so the ADS8688's ±20 V protection holds unpowered (TI's condition, to measure at bring-up) | one Extended (TVS) |
| CV out | 12k/22k offset divider with 1 nF; 33k feedback (±5 V inside the DAC's specified codes); CV7–8 take feedback from the jack side of their 1 kΩ 1206, with the 100 pF at the op-amp pin; every jack-facing resistor 1206 | Basic |
| Gates | 10 kΩ pull-up on CS_595; GATE_OE_N on the J603 expansion holes, labelled "74HCT595 only" | Basic |
| Panel | Wiper pull-downs 1 MΩ; POT_REF (MCP3208 VREF and pot tops) from +3V3A through 100 Ω with 10 µF + 100 nF; buttons hole → 1 kΩ → node (10 kΩ up, 100 nF, or 10 nF on SW5–SW8 for encoders); 47 µF at the LED holes; the encoder is documented on gate inputs 3–4 | Basic |
| MIDI | Sheet 10, Type A (RP-054), values from CA-033. **Out:** 74AHCT1G125 at +5VD → 2 × 100 Ω 1206 per leg, BAT54S clamp on the driver. **In:** 220 Ω → H11L1 (C20082) with a 1N4148WS reverse diode, 1 kΩ pull-up to +3V3D, 1 kΩ series to the module. The IN sleeve goes to ground through 100 nF, never directly. Enabled by link holes on J101 (SPARE1-MIDI_TX, SPARE2-MIDI_RX) | one Extended (H11L1) |

**Extended part types (17):** PCM3060, ADS8688, DAC8568, DG412, MCP3208, TL074H, 74HCT595,
TCA9555, M24C64 (Preferred), SN74AHCT1G125, BAT54S, TPS54308, the 15 µH inductor, JST SH,
PESD15VL1BA, the 1 nF C0G and H11L1. At $3.07 each, $52.19 an order (§12).

### Firmware requirements

The hardware assumes these. Each is cheap in code and costly to rediscover on the bench.

**Boot and power**
1. Probe the M24C64 at 0x50 before starting MCLK, I2S or SPI. If it does not answer, the
   rack is off and the module runs on USB: keep those pins, SPI-B and LED_DATA as inputs, so
   the module does not power the board's chips through their input clamps.
2. **ESP32-P4:** first, set LDO channel 4 to 3.3 V (`esp_ldo_acquire_channel`). Pins 21, 22
   and 24 (SPI-A) are dead until then. Bridge JP201.
3. **DAC8568 start-up**, in order ([cv_out.md](analogue_board_review/cv_out.md) B1):
   1. TCA9555 port 0 to 0, then outputs, so every jack switch is off.
   2. Write the 0 V code (≈32544) to all eight channels.
   3. Enable the internal reference as flexible and always on (0x090A0000).
   4. Wait about 10 ms (to confirm on the bench).
   5. Write the targets.
   6. Close each switch only once its channel holds the wanted value.
   7. Never send the software reset on a warm restart.
4. **74HCT595:** keep GATE_OE_N high until a full gate word has been shifted and latched.
5. **Codec:** it starts by itself (RST pulled up). If CODEC_RST is wired from J303, hold it
   low until MCLK runs, as Beads does.

**Audio**
6. The audio inputs invert: negate the ADC samples.
7. Run at about 10 Vpp nominal, 6 dB under the 20 Vpp full scale.

**CV**
8. An unpatched CV input reads about +0.2 V (the ADS8688's internal bias). With jack detect
   dropped (2026-10-16), firmware cannot tell it from a patched 0.2 V: treat it as an offset
   to calibrate out, or use a switched jack wired to ground. Default every channel to
   ±10.24 V; oversample for audio-rate CV.
9. **CV1–6 load correction:** with a switch on, the ADC reads the jack. Servo out the load
   sag (≈10 ms), clamp the correction to ±3 %, and flag a jack driven by another output.
10. Calibrate the outputs at more points (one per volt, as O&C). CV7–8 have no ADC path:
    calibrate them with a cable to CVI7–8.
11. Hold a channel's DAC steady while its jack is an input (switch off-isolation), and
    write every sample: block-rate CV updates step audibly.

**Gates, panel, LEDs, MIDI**
12. Gate inputs are active-high. Catch 100 µs triggers with edge interrupts or PIO.
13. **Encoder:** A and B on gate inputs 3–4 (PIO quadrature on Pico GP8/GP9, QuadEncoder on
    Teensy 4/5), not through the TCA9555, whose shared I2C bus a busy OLED holds for about
    23 ms. Debounce buttons in firmware. Treat the TCA9555 INT as a level and poll as a
    backstop.
14. **Panel bus:** the 74HCT595 sees every MCP3208 frame (SER = MOSI, SRCLK = SCK). Always
    shift a full gate word before pulsing RCLK, and keep SCLK ≤ 1 MHz while CS_POT is low.
15. Cap the total LED current (for example ≤ 150 mA at 5 V).
16. **MIDI:** UART0 on the Pico (GP0/GP1), Serial1 on the Teensy (1/0). On a Pico, move the
    SDK console from UART0 to USB. There is no hardware THRU; echo IN to OUT in firmware if
    wanted.

### For checkpoint 2

- **ESP32-P4 length:** it is 71 mm long, 20 mm more than a Pico 2, with its USB at the same
  end. Check that its far end fits on the printout, or move the module.
- **Power header:** place it with the buck and rail filters, away from the converters and
  op-amps, and clear of the USB keep-out (§4.3).

The pin map (sheet 1) assumes the Pico and Teensy footprints **share no holes**, for example
with the Teensy's rows one pitch outside and two pitches inside the Pico's. Sharing holes
(§5) would tie each Pico pin choice to the Teensy pin in the same hole. A Pico GPIO that
landed on a Teensy GND or 3.3 V pin would also be lost, and the Pico needs all 26 of its
GPIOs. The 1:1 printout will show both arrangements.

The printout also places each module with its USB end toward the board centre and its far end
at the top edge. It marks the USB plug keep-out of §4.3, to be checked with the real cables
(micro-B for the Pico 2 and Teensy 4.1).

## 16. Sources

- Datasheets (TI unless noted): MCP4802/4812/4822 (Microchip DS20002249B); PCM3060 SBAS437; ADS8684/8688 SBAS582C; DAC7568/8168/8568
  SBAS430F; DAC8564, DAC8565; MCP3204/3208 (Microchip DS21298); DG411/412/413 (Vishay
  61564, rev B 2025); TL07xx (TL07xH data); SN74HCT595; SN74HC14 (superseded); LM4040.
- Stock and prices: JLCPCB parts API (`selectSmtComponentList`), 2026-10-14.
- I/O audit: `MCU_MODULES.xlsx` and `MODULES.md`, eight4awish repo.
- Deck geometry: `docs/n8synth_platform.md`, `tools/visualizer/boards/*.json`,
  `tools/n8layout/*.n8layout`.
- Module DAC survey: firmware drivers in `mxmxmx/O_C`, `westlicht/performer`,
  `pichenettes/eurorack`, `TomWhitwell/Workshop_Computer`.
- Prior art: Alchemy Lab SDK (DG411 routing, loopback calibration),
  Daisy Patch Submodule, Music Thing Workshop System Computer, EuroPi, Pico ADK.

# Analogue board — Rev A specification, v0.3

A general-purpose Eurorack I/O board: a plug-in compute module on one side, an n8synth
Control Deck on the other, and every analogue, gate and display interface in between.
End goal: one JLCPCB order for assembled boards.

v0.1 was a handoff from a cloud session (2026-10-14) with nothing checked. This version
checks that handoff against datasheets and live JLCPCB stock, adds an I/O audit of the
existing modules, and settles the deck interface with David's answers.

v0.3 (2026-10-14) adds §15: what the schematic (checkpoint 1) decided that this spec had
left open, or changed.

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
| TL074 for all op-amps | TL07x swings ±10 V only into ≥2 kΩ on **±15 V**; from ±11.6 V rails ±10 V is not reliable | **±5 V is the CV range**; ±10 V needs a rail-to-rail part (OPA4197) |
| Gate-in count 6, EYESPI colour TFT | The audit (§3) finds no own build with more than two gate ins, and none using a colour TFT | 4 direct gate ins; EYESPI dropped (both decided) |
| Board "~50 mm wide", headers to the deck | David: **10HP mounts parallel to the panel, 6HP at 90°**, and the channel→cell wiring lives **on this board** | One PCB, the n8synth breadboard's footprint, serves both widths (§4) |
| 24C02 EEPROM | The panel map plus calibration can outgrow 256 bytes | **M24C64** (8 KB), a Preferred part |
| MIDI in via opto | David has only ever used TRS MIDI on the Big Genes | **No MIDI circuit in Rev A** (decided); its two pins go to the wiring field as spare GPIO |
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
| Alchemy Lab (Daisy Seed 2) | 6 bidirectional | — | (same 6) | — | 2 / 2 | 6 pots, 3 buttons | 102 RGB LEDs |
| Ogham (Daisy Seed) | 2 | 2 | 1 | 1 | — / 2 | 4 pots, encoder, toggle | display |

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
| Audio in | 2 | AC-coupled, 10 Vpp nominal, ±10 V tolerant |
| Audio out | 2 | DC-coupled, ±5 V; doubles as high-resolution CV out |
| CV bidirectional | 6 | ADC always reads the jack; DAC switched on for output |
| CV in only | 2 | The ADC's spare channels |
| CV out only | 2 | The DAC's spare channels |
| Gate in | 4 | Direct GPIO, comparator input with a set threshold (v0.1 had 6) [decided] |
| Gate out | 8 | 0/5 V via shift register |
| Pots | 8 | Ratiometric |
| Buttons / switches / encoder | 9 lines | On the GPIO expander; one encoder needs 3 |
| LEDs | 1 chain | WS2812, 5 V data |
| Spare GPIO | 2 | To the wiring field (the pins v0.1 gave to MIDI) [decided] |
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
  position each cell occupies.
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
| +5 V in | VSYS (1.8–5.5 V) through our Schottky — the datasheet's ORing arrangement | VIN (3.6–5.5 V). **Cut the VIN–VUSB pads first** |
| 3V3 out | < 300 mA | 250 mA |
| Logic level | 3.3 V; GPIO 5 V-tolerant while powered, 3.3 V-failsafe unpowered (RP2350 datasheet) | 3.3 V; **not 5 V-tolerant** (PJRC: "Do not drive any digital pin higher than 3.3 volts") |

- **Both footprints on the one board, wired to the same nets.** The Pico's rows (17.78 mm)
  and the Teensy's (15.24 mm) cannot sit side by side in the ~34 mm available, so they
  overlap: align one row of each, put the other Teensy row 2.54 mm inside the Pico's, and
  stagger along the row where a shared hole would join incompatible nets. USB ends point
  toward the board centre (§4.3). Fallback if routing fails: Pico footprint only, plus a bare 2-layer
  adapter for the Teensy.
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
| **Jack-detect probe:** one GPIO drives 100 kΩ into each input jack's switch (normal) lug, with a BAT54S clamp. Firmware sends a pseudo-random bit every 16 samples and calls an input patched when its readings stop following the sequence. No extra ADC channels. | Workshop System Computer Rev 1.0.0, R63–R68, `ComputerCard.h` L617–623, L834–874 | Adopt. A PROBE column in the wiring field (one 100 kΩ per hole) reaches the switch pad of any input jack cell. [proposed] |
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
| **Audio out** | MCP4822 → TL074H inverting with −5 V ref: ±6 V, 1k out | — | Patch SM: PCM3060, DC-coupled ±5 V. Ogham: TL072 ×4.7 overshot to 19.5 Vpp | PCM3060 differential → difference amp ×1.25: ±5 V DC-coupled |
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
| **Audio in** | Eurorack 10 Vpp → AC-couple → inverting amp, gain −0.3, biased to VCOM → codec. Clamp to the codec rails. | op-amp | — | proposed |
| **Audio out** | Codec VOUT± → difference amp, gain 1.25 → ±5 V, **DC-coupled** → 1 kΩ → jack | op-amp | — | proposed |
| **CV ADC** | ADS8688: 8 ch, 16-bit, 500 kSPS aggregate, per-channel ranges ±10.24 / ±5.12 / ±2.56 / 0–10.24 / 0–5.12 V, **1 MΩ** input, OVP ±20 V powered / **±11 V unpowered**, internal 4.096 V ref, AVDD 4.75–5.25 V, DVDD 1.65 V–AVDD, SCLK ≤ 17 MHz, 32-clock frames *(SBAS582C)*. No input op-amps needed. | ADS8688IDBTR **C527390** | 2,921 / $7.32 | proposed |
| **CV DAC** | DAC8568 grade A: 8 ch, 16-bit, internal 2.5 V ref (off by default), output 0–2.5 V, resets to zero scale, SCLK ≤ 50 MHz. **AVDD = 3.3 V analogue rail**, so VINH = 0.7 × AVDD and 3.3 V logic drives it *(SBAS430F)*. Op-amp ×4 with −5 V offset → ±5 V. | DAC8568IAPWR **C486051** | 796 / $17.45 | decided |
| **Jack switch** | DG412 (logic 1 = on) with pull-downs, so jacks power up as inputs. ±12 V fine (V+ to V− ≤ 44 V), VL = 5 V, logic 0.8 / 2.4 V, RDS(on) 25 Ω typ, signals beyond the rails clamp through internal diodes, ≤ 30 mA *(Vishay 61564 rev B)* | 2 × DG412DQ-T1-E3 **C2651920** (TSSOP) | 5,903 / $2.18 | proposed |
| **CV op-amps** | 8 outputs at ±5 V: TL074H (no phase reversal, CM includes V+). The ±10 V option needs rail-to-rail output: OPA4197 footprint-compatible (SOIC-14) | TL074HIDR **C2878713**; option OPA4197IDR **C2058532** | 14,140 / $0.25; 8,474 / $2.73 | proposed |
| **Reference** | LM4040 4.096 V shunt for the calibration check (0.1 % A-grade or 1 % D-grade) | LM4040AIM3-4.1 **C126807** / LM4040DIM3-4.1 **C202194** | 2,077 / $1.12; 6,187 / $0.47 | proposed |
| **Pots** | MCP3208 on the 3.3 V analogue rail, VREF = that rail, pots fed from VREF + AGND (ratiometric). 50 ksps at 2.7 V, SCLK ≤ 1 MHz at 2.7 V *(DS21298)* | MCP3208-CI/SL **C16939** | 600 / $3.24 | proposed |
| **Gate in** | Ogham's clock input (Keeos `ogham-merged-v1.0`): jack → 10 kΩ → BAT54S clamp to 3.3 V / GND, 100 kΩ to GND → LM393 (+5 V) + input; − input at 1.65 V from a 3.3 V divider; ~100 kΩ hysteresis; open-collector output, 10 kΩ pull-up to 3.3 V → GPIO, not inverted. Trips at ~1.8 V at the jack, set by resistors, not by logic-gate tolerance — a 3.3 V gate clears it by 1.5 V. ±12 V clamps at ~0.8 mA. Values to tune at schematic. | 2 × LM393DR2G **C7955** (Basic); 4 × BAT54S **C408389** | 213,954 / $0.07; 817,166 / $0.02 | decided |
| **Gate out** | 74HCT595 at 5 V (VIH 2.0 V, so 3.3 V drives it) → 1 kΩ → jack, BAV99 (Basic, C2500) clamp to +5 V / GND per output. OE pulled high until firmware enables (§10). | 74HCT595D **C282339** | 14,359 / $0.27 | decided |
| **Expander** | 16 lines: 6 switch enables (DG412), 1 gate-output enable, 9 for buttons, switches, encoder; INT to a GPIO | TCA9555PWR **C465732** | 35,995 / $0.56 | proposed |
| **LEDs** | WS2812 chain; data level-shifted to 5 V; LED supply on its own wiring-field holes | SN74AHCT1G125DBVR **C7484** | 49,818 / $0.10 | proposed |
| **EEPROM** | Board revision, footprint ID, calibration, panel map | M24C64-RMN6TP **C79988** (Preferred) | 103,045 / $0.15 | proposed |
| **Qwiic** | JST SH 4-pin, 3.3 V from the display LDO | SM04B-SRSS-TB **C160404** | 10,257 / $0.21 | decided |

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
| Reference | internal 2.5 V, **2 ppm/°C** typ, 25 max | internal 2.048 V ±2 %, **45 ppm/°C** typ, 160 max |
| Drift at the top of the range (+5 V, i.e. 10 V of span) over a 10 °C warm-up | 0.2 mV ≈ 0.2 cent typ; 2.5 mV ≈ 3 cents max | 4.5 mV ≈ **5 cents** typ; 16 mV ≈ 19 cents max |
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
| ±12 V in | Eurorack header → series Schottky each rail → ferrite | — | SS14 **C2480** (Basic) |
| +5 V digital | Buck from +12 V | module, Qwiic, WS2812, 595, VL | TPS54202DDCR **C191884** (261k / $0.18) or AP63205WU-7 **C2071056** (fixed 5 V) |
| +5 V analogue | Linear from +12 V, own ground return | PCM3060 VCC, ADS8688 AVDD | L78M05ABDT **C58069** (Basic); low-noise option TPS7A4901 **C16430** ($1.26) |
| +3.3 V analogue | LDO from +5 V analogue | DAC8568, MCP3208 + pot reference | AMS1117-3.3 **C6186** (Basic) or LP2985-33 **C95414** |
| +3.3 V digital | LDO from +5 V digital | PCM3060 VDD, ADS8688 DVDD, gate-in pull-ups and threshold, expander, EEPROM, Qwiic | AMS1117-3.3 **C6186** (Basic) |

- **Why a buck:** David's hand-built Daisy modules showed a block-rate comb traced to a
  shared +5 V rail, with a dedicated buck as the fix. Digital and analogue 5 V stay
  separate here for the same reason.
- **Budget (estimate):** +12 V ≈ 120 mA typical, ~350 mA worst case (ESP32 Wi-Fi peaks
  plus a lit LED chain through the buck); −12 V ≈ 25 mA (op-amps). The bus +5 V is never
  used [decided]: every 5 V rail is made on the board.

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
| Rail entry: series Schottky → BLM18PG121 ferrite → 10 µF 50 V X7R + 100 nF, per rail | Ogham |
| Pot and converter references on a linear rail, never the buck or the module's 5 V | Ogham; David's bench notes |
| Gate out: HCT part → 1 kΩ → Schottky clamps to +5 V and GND | Ogham (74AHCT1G125) |
| Gate in: 10k series, BAT54 clamps, then a comparator with a set threshold and hysteresis | Ogham (clock input) |
| Pot inputs: 1 kΩ + 100 nF, 100 kΩ pull-down, pot top on the converter's reference rail | Ogham |
| 74HCT595: OE pulled **high** (gates off) until firmware enables them from a TCA9555 line; MR to VCC. The storage register powers up undefined. | Datasheet behaviour; Ogham ties OE low |
| Spare op-amp sections tied as followers with + to GND | Ogham |
| Power-header symbol: join pins 1–2 (−12 V), 3–8 (GND), 9–10 (+12 V); then confirm every op-amp ±12 V pin has its 100 nF within ~3 mm | review of the boards |
| No tantalum on the ±12 V rails; X7R 50 V instead | Ogham (schematic note) |
| GND stitching vias at every decoupling cap and around the edge | Ogham (~37) |
| Derate MLCC values for DC bias | reDIP-SID (capacitor notes) |
| 0.45 / 0.2 mm vias only for fine-pitch fan-out (ADS8688 TSSOP-38); three fiducials | reDIP-SID; JLC practice |
| Rules: 0.2 mm track and clearance, 0.5 mm power, via 0.6 / 0.3 mm, 0.5 mm copper to edge, a Power net class — JLCPCB's cheapest tier | Ogham, patch.init |
| Leaded packages only (no QFN/BGA): Economic PCBA's 0.4 mm pitch floor, and no X-ray charge | JLCPCB capabilities and price pages |
| LCSC field on every machine-placed part; everything else marked do-not-place | Ogham |
| Test pads on every rail and on I2S; fiducials | none of the four boards had them |
| Check every decoupling cap's two nets and every polarised part in the PCB, then step through rotations in JLC's preview | review of the boards |

One codec data point: Ogham measured its PCM3060 (single-ended, AC-coupled on the Seed)
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
- **6HP and 10HP from one design** means one assembly setup, not two.

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
  ±12 V rails.

### Decided by David, 2026-10-14

- One board for 6HP and 10HP: the kits share the breadboard; 6HP connects only the left 40.
- EYESPI dropped.
- Four gate ins.
- XIAO dropped: Pico 2 and Teensy 4.1 only.
- Modules on headers; low-profile SMT under them.
- No TRS MIDI in Rev A.
- DAC: DAC8568IA (§7.1).

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
   the first sheet. **Drafted 2026-10-14, awaiting review:**
   [`hardware/analogue_board/analogue_board_schematic.pdf`](../hardware/analogue_board/analogue_board_schematic.pdf),
   checks in [`output/checks.md`](../hardware/analogue_board/output/checks.md), decisions in §15.
2. **1:1 printout** of the outline, edge strips, module footprints and power header. David
   lays a real breadboard, a Pico 2, a Teensy 4.1 and the deck header on it.
3. **Placement renders**, before routing.
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
| −5 V offset for the CV outs (§6.4) | Taken from the DAC8568's own 2.5 V reference: 10k/20k divider, 1 µF, a TL074H follower → OFFSET_REF 1.667 V into each stage's 10 kΩ; gain 1 + 30k/10k = 4, so Vout = 4·Vdac − 5 V | Mid-code is 0 V whatever the reference does. Costs a fourth TL074H (same part type, no fee); its three spare sections are grounded followers |
| Codec straps | MODE 220 kΩ to ground (hardware mode, differential outputs). FMT, DEMP, IFMD each 10 kΩ to ground (I2S, no de-emphasis, slave). RST pulled up through 1 kΩ | Pull-downs rather than hard ties, so a strap can be changed with a bodge |
| Audio in | 1 µF 50 V X7R, then 100 kΩ into an inverting TL074H with 33 kΩ ∥ 100 pF, + input on VCOM, then 1 kΩ into the codec's 10 kΩ: gain −0.30. 1 MΩ to ground at the jack. BAT54S clamps to +5VA | Inverting: firmware flips the sign |
| Audio out | 12 kΩ / 15 kΩ difference amp (×1.25), 100 pF C0G across each 15 kΩ (pole at 106 kHz), 1 kΩ out | Larger C0G values are not Basic. The codec has its own RC filter; 330 pF (Extended) would move the pole to 32 kHz |
| Gate-in values | 10 kΩ, BAT54S to +3V3D/GND, 100 kΩ to ground, 100 kΩ hysteresis, 10 kΩ pull-up. GATE_TH = 1.65 V from one 10k/10k divider | Trips at 1.98 V rising, 1.67 V falling at the jack |
| Jack-detect probe | GPIO → 1 kΩ → bus with a BAT54S clamp → 14 holes: PR1-10 through 100 kΩ (audio and CV ins), PR11-14 through 22 kΩ (gate ins) | A 100 kΩ probe lifts an unpatched gate input only to ≈1.24 V, under the threshold |
| Chip-select pull-ups | 10 kΩ to +3V3D on CS_ADC, CS_DAC, CS_POT | Every module leaves its pins floating while it boots; this keeps the converters deselected and off MISO |
| Bus-merge jumpers (§6.3) | Not fitted | The Teensy 4.0 is not a target; both target modules have two hardware SPI buses |
| Gate-out expansion | J603: QH′, SRCLK, RCLK, +5VD, GND | Chains a second 74HCT595 off-board (Boy's expander) |
| Rail links and test pads (checkpoint 4) | A 0 Ω link after every regulator; test pads on every rail, on I2S and on both SPI buses and I2C | Fitted now rather than at layout |
| Edge strips | 80 positions, outer and inner pads sharing a pad number; nothing tied to GND | All 80 stay free tie points; a GND wire goes to any free position if wanted |

### For checkpoint 2

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

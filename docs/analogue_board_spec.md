# Analogue board — Rev A specification, v0.2

A general-purpose Eurorack I/O board: a plug-in compute module on one side, an n8synth
Control Deck on the other, and every analogue, gate, MIDI and display interface in between.
End goal: one JLCPCB order for assembled boards.

v0.1 was a handoff from a cloud session (2026-10-14) with nothing checked. This version
checks that handoff against datasheets and live JLCPCB stock, adds an I/O audit of the
existing modules, and settles the deck interface with David's answers.

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
| Gate-in count 6, EYESPI colour TFT | The audit (§3) finds no own build with more than two gate ins, and none using a colour TFT | 4 direct gate ins; EYESPI dropped from Rev A |
| Board "~50 mm wide", headers to the deck | David: **10HP mounts parallel to the panel, 6HP at 90°**, and the channel→cell wiring lives **on this board** | One PCB, the n8synth breadboard's footprint, serves both widths (§4) |
| 24C02 EEPROM | The panel map plus calibration can outgrow 256 bytes | **M24C64** (8 KB), a Preferred part |
| MIDI in only | One own build already uses TRS MIDI in **and** out | Add MIDI out (two resistors) |
| XIAO subset keeps the codec | 11 pins cannot carry I2S plus a panel bus; the XIAO builds in the audit use no codec | XIAO tier drops the codec and keeps CV, pots, gates (§6.3) |
| Teensy 4.x "full set" | Teensy 4.0's second SPI bus is on bottom pads a socket cannot reach | Bus-merge solder jumpers (§6.3) |

## 2. Goal and constraints

- **Deliverable:** a JLCPCB order for populated boards. JLCPCB assembles all SMT;
  David solders only headers, sockets and the deck wiring. [decided]
- **One design for both widths.** The same assembled board mounts parallel behind a 10HP
  deck and at 90° behind a 6HP deck (§4). Both versions come from one assembly order.
  [proposed — depends on the 6HP and 10HP n8synth breadboards being the same board, §4.1]
- **Principle:** the board offers more channels than any one panel uses. It provides typed
  channels and never decides which deck cell they go to; David wires that per module on
  the board. [decided]
- **Assembly:** 4-layer, SMT on one side, JLCPCB Economic PCBA if it accepts 4-layer
  boards (†, §12). Prefer Basic and Preferred parts; each Extended part type carries a
  loading fee.

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
9. **MIDI:** USB MIDI via the module's own USB; TRS in and out once.
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
| Gate in | 4 | Direct GPIO, Schmitt input (v0.1 had 6) |
| Gate out | 8 | 0/5 V via shift register |
| Pots | 8 | Ratiometric |
| Buttons / switches / encoder | 9 lines | On the GPIO expander; one encoder needs 3 |
| LEDs | 1 chain | WS2812, 5 V data |
| MIDI | in + out | TRS type A |
| Displays | Qwiic I2C | EYESPI dropped (no user) |

So CV reaches 8 in or 8 out (O&C's count; eight of Girl's nine), and the gate outs cover
Boy plus most of its expander.

## 4. Mechanical and the deck interface

### 4.1 One board, two orientations [proposed]

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

**To confirm (David):** the outline, hole positions and mounting holes, taken from a real
breadboard. `docs/n8synth_platform.md` warns that the templates are a drawing, not the
board.

### 4.2 Edge strips and wiring field [decided: wiring on this board; geometry proposed]

- **Two edge strips**, 40 positions each, 2.54 mm pitch, at the n8synth edge-connector
  positions: an outer hole for the deck header and an inner hole as a wiring point, the
  two joined (the n8synth doublet). Deck header spans are positions 1–10, 16–25 and 31–40;
  positions with no deck cell remain free tie points, as on the breadboard.
- **Wiring field:** a labelled column of plated holes, one per channel (§3), plus short
  buses of AGND, VREF (pot top), +5 V LED and DGND holes. David solders a wire from a
  cell's inner hole to the channel it needs. Silkscreen names on both faces.
- **Deck ground bus (D pads):** one wire from any D pad to an AGND hole (pot and jack
  grounds are on D).
- **Stacking:** keep power-rail-compatible pads at positions 1, 2, 39, 40 (GND, +12 V /
  −12 V, as the breadboard's power rails) so a stock breadboard can still stack behind
  for analogue extras. [proposed]

### 4.3 Faces and height

- **SMT on one face** (JLCPCB one-side assembly); module sockets, power header and the
  wiring on the other. In 10HP the SMT face faces the deck, inside the header stand-off
  (keep SMT ≤ 2.5 mm tall: no electrolytics, no DPAK above that).
- **6HP height budget** (board at 90°): socket 8.5 + Pico 1.0 + its parts ~1.5 + PCB 1.6 +
  SMT ~2.5 ≈ **15 mm** against a 30.3 mm panel. Where the board sits across the 6HP width
  depends on where the deck's right-angle header lands — **to check on a real 6HP build.**
- **USB:** all module USB connectors toward the **top short edge** (reachable in both
  orientations), then a panel-mount USB-C extension. [proposed]
- **Power header:** shrouded 2×5 (or 2×8) on the module face near the **right** long edge
  — the rear in the 6HP orientation. [proposed]

## 5. Compute modules

Sources: Raspberry Pi *Pico 2 datasheet* and *RP2350 datasheet* (GPIO function table);
PJRC Teensy 4.0 / 4.1 product pages, pinout cards and dimension drawings; Seeed XIAO
schematics (RP2350, ESP32-S3, ESP32-C5). XIAO outline and row spacing are †.

| | Pico 2 (RP2350) | Teensy 4.0 | Teensy 4.1 | XIAO (RP2350 / S3 / C5) |
|---|---|---|---|---|
| Outline | 51 × 21 mm | 35.56 × 17.78 mm | 60.96 × 17.78 mm | 21 × 17.8 mm † |
| Rows, pitch | 2 × 20, 17.78 mm apart | 2 × 14, 15.24 mm apart | 2 × 24, 15.24 mm apart | 2 × 7, 15.24 mm † |
| GPIO a socket reaches | **26** (GPIO 0–22, 26–28) | **24** (0–23); 24–33 are bottom pads | **42** (0–41) | **11** (D0–D10) |
| USB | Micro-B, short edge at pins 1/40 | Micro-B, short edge at pin 0 / VIN | Same end as 4.0 | USB-C, short edge † |
| I2S | PIO on any GPIO; MCLK from GPOUT (GP13/15/21) or PIO | SAI1: MCLK 23, BCLK 21, LRCLK 20, TX 7, RX 8 | Same | RP2350: PIO; S3/C5: GPIO matrix † |
| Hardware SPI | SPI0 and SPI1 groups both on the header | One bus (10–13). SPI1's MOSI/SCK are bottom pads 26/27 | Two buses on the edge (SPI1: 26, 27, 1, 0) | One (D8 SCK, D9 MISO, D10 MOSI) |
| +5 V in | VSYS (1.8–5.5 V) through our Schottky — the datasheet's ORing arrangement; VBUS already has its own | VIN (3.6–5.5 V). **Cut the VIN–VUSB pads first** | Same | **5 V pin is VBUS itself** (RP2350, S3); C5 has a load switch behind it |
| 3V3 out | < 300 mA | 250 mA | 250 mA | S3 600 mA; C5 1 A |

- **All footprints on the one board, wired to the same nets** [decided]. Inside the ~34 mm
  between the wiring field and the far strip, the Pico (17.78 mm rows) and Teensy
  (15.24 mm) cannot sit side by side. They must overlap: align one row of each, put the
  other Teensy row 2.54 mm inside the Pico's, and stagger along the row where a shared
  hole would join incompatible nets. All USB ends point to the top edge. Fallback if
  routing fails: Pico footprint only, plus bare 2-layer adapter boards for Teensy and XIAO.
- **Power:** 5 V reaches every module through a Schottky. Two module rules:
  - **Teensy:** cut the VIN–VUSB pads before fitting.
  - **XIAO:** its 5 V pin is USB VBUS, so rack power reaches a connected computer's USB
    port. Use a data-only cable when the rack is on. [proposed]
- Per-module pin budgets: §6.3.

## 6. Architecture

### 6.1 Buses

| Bus | Members | Speed | Why separate |
|---|---|---|---|
| **I2S** | PCM3060 (hardware-control mode) | 48 kHz, MCLK 256/512 fS | — |
| **SPI-A, converter bus** | ADS8688 (CS_ADC), DAC8568 (CS_DAC) | ≤ 17 MHz (ADS8688 limit) | Audio-rate CV needs the bus to itself |
| **SPI-B, panel bus** | 74HCT595 (RCLK as CS), MCP3208 (CS_POT), expansion CS | ≤ 1 MHz for MCP3208 at 3.3 V | Slow devices off the converter bus |
| **I2C** | TCA9555 expander, M24C64 EEPROM, Qwiic | 400 kHz | — |
| **UART** | MIDI in / out | 31.25 kbaud | — |

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
| UART: MIDI TX, RX | 2 |
| WS2812 data | 1 |
| Gate in | 4 |
| Jack-detect probe | 1 |
| **Total** | **26 nets** |

**Bus-merge jumpers [proposed]:** three solder jumpers join SPI-B's SCK, MOSI and MISO to
SPI-A's. Open, the Pico 2 and Teensy 4.1 run two buses. Closed, one bus carries all four
chip selects (the MCP3208 transfers drop to ≤ 1 MHz) and three pins come free. No parts,
no BOM cost.

| Module | Pins | Fit |
|---|---|---|
| **Pico 2** | 26 | All 26 nets, jumpers open. Hardware SPI0 and SPI1 both reach the header. |
| **Teensy 4.1** | 42 | All 26, jumpers open; ~16 spare for a second module revision. |
| **Teensy 4.0** | 24 | Jumpers closed: 23 nets, one spare. |
| **XIAO** | 11 | Jumpers closed. SCK, MOSI, MISO, the four chip selects, SDA, SCL and two gate ins — **no codec, MIDI or WS2812**. That suits the XIAO builds in the audit (MOD2/Melon, ClkLinkRec), neither of which uses a codec. [proposed] |

On the XIAO, buttons, encoder and switch enables still work through the expander, but with
no interrupt line it is polled.

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
| **Gate in** | 100k → NPN base, RP2040 pull-up as the load, no clamp; above 0.4 V = high | 100k → NPN, reverse diode on the base, 10k pull-up; 0.8 V threshold | Patch SM: BJT input, inverted in libDaisy. Ogham: LM393 with hysteresis for clock | 22k / 100k divider, BAV99 clamp, 74HC14 Schmitt. No reliance on module pull-ups (they differ between Pico, Teensy, XIAO) |
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
| **CV DAC** | DAC8568 grade A: 8 ch, 16-bit, internal 2.5 V ref (off by default), output 0–2.5 V, resets to zero scale, SCLK ≤ 50 MHz. **AVDD = 3.3 V analogue rail**, so VINH = 0.7 × AVDD and 3.3 V logic drives it *(SBAS430F)*. Op-amp ×4 with −5 V offset → ±5 V. | DAC8568IAPWR **C486051** | 796 / $17.45 | proposed |
| **Jack switch** | DG412 (logic 1 = on) with pull-downs, so jacks power up as inputs. ±12 V fine (V+ to V− ≤ 44 V), VL = 5 V, logic 0.8 / 2.4 V, RDS(on) 25 Ω typ, signals beyond the rails clamp through internal diodes, ≤ 30 mA *(Vishay 61564 rev B)* | 2 × DG412DQ-T1-E3 **C2651920** (TSSOP) | 5,903 / † | proposed |
| **CV op-amps** | 8 outputs at ±5 V: TL074H (no phase reversal, CM includes V+). The ±10 V option needs rail-to-rail output: OPA4197 footprint-compatible (SOIC-14) | TL074HIDR **C2878713**; option OPA4197IDR **C2058532** | 14,140 / $0.25; 8,474 / $2.73 | proposed |
| **Reference** | LM4040 4.096 V shunt for the calibration check (0.1 % A-grade or 1 % D-grade) | LM4040AIM3-4.1 **C126807** / LM4040DIM3-4.1 **C202194** | 2,077 / $1.12; 6,187 / $0.47 | proposed |
| **Pots** | MCP3208 on the 3.3 V analogue rail, VREF = that rail, pots fed from VREF + AGND (ratiometric). 50 ksps at 2.7 V, SCLK ≤ 1 MHz at 2.7 V *(DS21298)* | MCP3208-CI/SL **C16939** | 600 / $3.24 | proposed |
| **Gate in** | jack → 22 kΩ series → 100 kΩ to GND → BAV99 clamp to 3.3 V / GND → 74HC14 at 3.3 V → GPIO (inverted). A 3.3 V gate arrives as 2.7 V, above VT+ (1.55–3.13 V at 4.5 V, lower at 3.3 V); ±12 V clamps at 0.4 mA. Two spare gates. | 74HC14D **C5605** (Basic) | 148,555 / $0.10 | decided |
| **Gate out** | 74HCT595 at 5 V (VIH 2.0 V, so 3.3 V drives it) → 1 kΩ → jack, BAV99 (Basic, C2500) clamp to +5 V / GND per output. OE pulled high until firmware enables (§10). | 74HCT595D **C282339** | 14,359 / $0.27 | decided |
| **Expander** | 16 lines: 6 switch enables (DG412), 1 gate-output enable, 9 for buttons, switches, encoder; INT to a GPIO | TCA9555PWR **C465732** | 35,995 / $0.56 | proposed |
| **LEDs** | WS2812 chain; data level-shifted to 5 V; LED supply on its own wiring-field holes | SN74AHCT1G125DBVR **C7484** | 49,818 / $0.10 | proposed |
| **MIDI in** | TRS → 220 Ω → 3.3 V-capable opto → UART RX | TLP2362 **C37658** | 22,657 / $0.37 | proposed |
| **MIDI out** | UART TX → 33 Ω / 10 Ω (3.3 V MIDI values) → TRS | resistors | — | proposed |
| **EEPROM** | Board revision, footprint ID, calibration, panel map | M24C64-RMN6TP **C79988** (Preferred) | 103,045 / $0.15 | proposed |
| **Qwiic** | JST SH 4-pin, 3.3 V from the display LDO | SM04B-SRSS-TB **C160404** | 10,257 / $0.21 | decided |

## 8. Power

| Rail | Source | Loads | Part |
|---|---|---|---|
| ±12 V in | Eurorack header → series Schottky each rail → ferrite | — | SS14 **C2480** (Basic) |
| +5 V digital | Buck from +12 V | module, Qwiic, WS2812, 595, VL | TPS54202DDCR **C191884** (261k / $0.18) or AP63205WU-7 **C2071056** (fixed 5 V) |
| +5 V analogue | Linear from +12 V, own ground return | PCM3060 VCC, ADS8688 AVDD | L78M05ABDT **C58069** (Basic); low-noise option TPS7A4901 **C16430** ($1.26) |
| +3.3 V analogue | LDO from +5 V analogue | DAC8568, MCP3208 + pot reference | AMS1117-3.3 **C6186** (Basic) or LP2985-33 **C95414** |
| +3.3 V digital | LDO from +5 V digital | PCM3060 VDD, ADS8688 DVDD, 74HC14, expander, EEPROM, Qwiic | AMS1117-3.3 **C6186** (Basic) |

- **Why a buck:** David's hand-built Daisy modules showed a block-rate comb traced to a
  shared +5 V rail, with a dedicated buck as the fix. Digital and analogue 5 V stay
  separate here for the same reason.
- **Budget (estimate):** +12 V ≈ 120 mA typical, ~350 mA worst case (ESP32 Wi-Fi peaks
  plus a lit LED chain through the buck); −12 V ≈ 25 mA (op-amps). Offer a 0 Ω option
  to take +5 V from a 16-pin bus header instead of the buck. [proposed]

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
| **Use the SMT-face area behind the module** (between its pin rows) for the logic — MCP3208, 595, 74HC14, TCA9555, EEPROM. Without it, demand is ~120 % of the area | Ogham (TL072 stage under the Seed); area estimate |
| **0402 passives, TSSOP wherever a variant exists** | area estimate |
| Rail entry: series Schottky → BLM18PG121 ferrite → 10 µF 50 V X7R + 100 nF, per rail | Ogham |
| Pot and converter references on a linear rail, never the buck or the module's 5 V | Ogham; David's bench notes |
| Gate out: HCT part → 1 kΩ → Schottky clamps to +5 V and GND | Ogham (74AHCT1G125) |
| Gate in: series 10k–100k, BAT54-class clamps, then the Schmitt part | Ogham (clock and gate inputs) |
| Pot inputs: 1 kΩ + 100 nF, 100 kΩ pull-down, pot top on the converter's reference rail | Ogham |
| 74HCT595: OE pulled **high** (gates off) until firmware enables them from a TCA9555 line; MR to VCC. The storage register powers up undefined. | Datasheet behaviour; Ogham ties OE low |
| Spare op-amp sections tied as followers with + to GND | Ogham |
| Power-header symbol: join pins 1–2 (−12 V), 3–8 (GND), 9–10 (+12 V); then confirm every op-amp ±12 V pin has its 100 nF within ~3 mm | review of the boards |
| No tantalum on the ±12 V rails; X7R 50 V instead | Ogham (schematic note) |
| GND stitching vias at every decoupling cap and around the edge | Ogham (~37) |
| Derate MLCC values for DC bias | reDIP-SID (capacitor notes) |
| 0.45 / 0.2 mm vias only for fine-pitch fan-out (ADS8688 TSSOP-38); three fiducials | reDIP-SID; JLC practice |
| Rules: 0.2 mm track and clearance, 0.5 mm power, via 0.6 / 0.3 mm, 0.5 mm copper to edge, a Power net class — JLCPCB's cheapest tier | Ogham, patch.init |
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
| Switches and op-amps: 2 × DG412 (~4.40 †), 3 × TL074H 0.76 | ~5.16 |
| Logic, I/O, memory: 74HC14 0.10, 74HCT595 0.27, AHCT1G125 0.10, TCA9555 0.56, M24C64 0.15, TLP2362 0.37 | 1.55 |
| Power and protection: buck + inductor ~0.30, L78M05 0.21, 2 × AMS1117 0.42, Schottkys, ferrites, BAV99 clamps ~0.60 | ~1.53 |
| Reference, connectors: LM4040 0.47–1.12, JST SH 0.21 | 0.68–1.33 |
| Passives (~150 Basic 0402/0603/0805) | ~1.50 |
| **Total** | **~$42–43** |

- **The DAC is the cost decision**, as v0.1 said, but bigger than it thought: the
  DAC8568IA is 41 % of the parts cost. The 12-bit alternative is 4 × MCP4822 (C16040,
  3,190 in stock †price): about $9 less a board, at 2.44 mV per step (≈ 3 cents at
  1 V/oct). [open — see §13]
- **Extended part types:** ~15. Per-order fees (setup, stencil, Extended loading fee,
  4-layer PCB, shipping) are **not yet verified** (§12).
- **6HP and 10HP from one design** means one assembly setup, not two.

## 12. Still to verify (one batched lookup each, no design impact expected)

1. JLCPCB rules today: does Economic PCBA take 4-layer boards; the Extended loading fee
   (v0.1 said $1.50 since Dec 2025, previously $3); whether Preferred parts are fee-free;
   setup and stencil fees; can 5 be ordered and 2 assembled.
2. DG412 and MCP4822 prices (stock confirmed).
3. A 0.5 mm 18-pin flip-lock FPC is moot now that EYESPI is out.
4. n8synth breadboard outline and mounting holes, measured (§4.1).

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

### For David

1. **One board for 6HP and 10HP** (§4.1): agree, and confirm on a real breadboard that the
   6HP and 10HP kits use the same board?
2. **DAC resolution:** 16-bit DAC8568 (~$42 a board) or 12-bit 4 × MCP4822 (~$33)?
3. **EYESPI colour TFT:** drop from Rev A (no build uses one), or keep the footprint?
4. **Gate ins:** 4 direct (audit maximum is 2), or 6 as in v0.1?
5. **XIAO tier:** no codec, keeping CV, pots and gates (proposed, §6.3), or keep the codec
   as v0.1 had it and lose the panel bus?
6. **Hardware licence:** CERN-OHL-S (as the Tiliqua work) or more permissive.

## 14. Next steps

1. Answer §13; verify §12.
2. Interface contract: wiring-field channel list and order, per-module pin maps
   (Pico 2, Teensy 4.0/4.1, XIAO), EEPROM layout.
3. Schematic in KiCad, ERC clean; JLCPCB part numbers in symbol fields.
4. Layout to the measured breadboard outline; DRC clean; analogue routing reviewed by eye.
5. JLCPCB outputs (gerbers, drill, BOM, CPL); check rotations in JLC's preview.
6. Bring-up firmware for the Pico 2 in `eurorack_modules`.

## 15. Sources

- Datasheets (TI unless noted): PCM3060 SBAS437; ADS8684/8688 SBAS582C; DAC7568/8168/8568
  SBAS430F; DAC8564, DAC8565; MCP3204/3208 (Microchip DS21298); DG411/412/413 (Vishay
  61564, rev B 2025); TL07xx (TL07xH data); SN74HCT595; SN74HC14; LM4040.
- Stock and prices: JLCPCB parts API (`selectSmtComponentList`), 2026-10-14.
- I/O audit: `MCU_MODULES.xlsx` and `MODULES.md`, eight4awish repo.
- Deck geometry: `docs/n8synth_platform.md`, `tools/visualizer/boards/*.json`,
  `tools/n8layout/*.n8layout`.
- Prior art: Alchemy Lab SDK (DG411 routing, loopback calibration),
  Daisy Patch Submodule, Music Thing Workshop System Computer, EuroPi, Pico ADK.

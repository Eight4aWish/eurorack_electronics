# Analogue board Rev A (Teensy 4.1): notes for firmware

What a firmware session needs to know about the Rev A board (`teensy_core_midi`) and the Boy2
module built on it. Written 2026-11-01, when the Boy2 bring-up finished. Every value here was
read from the netlist, the generator's pin map or the working test program, or measured on the
built module. Where something is from the design only and not yet seen on the bench, it says so.

**Sources, in order of authority:**
- **The working code:** [`firmware/analogue_board_test/src/main.cpp`](../firmware/analogue_board_test/src/main.cpp).
  Every bus and chip below has a working driver there, proven on the board. Start from it.
- **The bring-up record and its Log:** [`analogue_board_bringup.md`](analogue_board_bringup.md).
- **The spec:**
  - [§15, firmware requirements](analogue_board_spec.md#firmware-requirements): the rules the
    hardware assumes;
  - §6.3: the pin map;
  - `PINMAP` in `tools/analogue_board/design.py`: the same pin map, as the board was generated.

## Status

- **Boy2's hardware is fully tested (2026-11-01).** Every function Boy2 uses passed on the built
  module through its own jacks.
- **Not yet tested anywhere** (Boy2 doesn't use them):
  - the pots (MCP3208);
  - the WS2812 LED chain;
  - MIDI out;
  - the gate-input thresholds;
  - CV inputs from an outside source;
  - switches other than SW6;
  - the noise comparison.
- **Boy2's firmware isn't written yet.** Boy's firmware (`eurorack_modules`, `src/teensy_move/`)
  is the starting point, but Boy's chips and pins are all different: see
  [Porting from Boy](#porting-from-boy).
- **Boy2's firmware goes in `eurorack_modules`, and it replaces `teensy_move`** (David,
  2026-11-01). Once Boy2 has taken over, Boy is decommissioned.
- **Its given job:** the Move companion. It takes the Move's three gate and pitch voices, two drum
  triggers, clock and reset into the rack. Move audio doesn't need to come in through Boy2.

## Building and flashing on this Mac

This Mac is arm64 **with no Rosetta**. PlatformIO's Teensy compiler and `teensy_loader_cli` are
x86_64 only, so neither runs.

- **Compiler:** copy [`arm64_toolchain.py`](../firmware/analogue_board_test/arm64_toolchain.py)
  into the project and add `extra_scripts = post:arm64_toolchain.py`. It swaps in PlatformIO's
  arm64 GCC. Boy's own `[env:teensy41]` in `eurorack_modules` doesn't have it.
- **Upload:** use `upload_protocol = teensy-gui` (the Teensy Loader app), not `teensy-cli`.
  Boy's env uses `teensy-cli`, which won't run here.
- **Flash in the foreground,** never in the background: a background upload once half-programmed
  and bricked a module.
- **Uploads often report `Error -1` or FAILED and still program the board.** Check that the new
  build is running before you retry. If the loader really is stuck, kill the Teensy Loader app,
  then upload twice.
- **The Teensy has VIN–VUSB cut,** so it runs only from the rack. With the rack off, it doesn't
  run or appear on USB at all.
- The test program's settings: `platform = teensy @ ~5.1.0` and `board = teensy41`. It builds
  with `-D USB_SERIAL`; Boy uses `USB_MIDI_SERIAL`.

## Pin map (Teensy 4.1 numbering)

| Pin | Net | Use |
|---|---|---|
| 13, 11, 12 | SPIA_SCK, MOSI, MISO | **SPI-A** (`SPI`): the CV converters only (spec §6.1: kept to itself for audio-rate CV) |
| 10 | CS_ADC | ADS8688 chip select |
| 9 | CS_DAC | DAC8568 SYNC |
| 27, 26, 39 | SPIB_SCK, MOSI, MISO | **SPI-B** (`SPI1`, with `SPI1.setMISO(39)`, the alternate pin): the panel bus |
| 38 | CS_595 | 74HCT595 latch (RCLK), latches on the rising edge |
| 37 | CS_POT | MCP3208 chip select |
| 18, 19 | SDA, SCL | **I2C** (`Wire`), 400 kHz: TCA9555 0x20, M24C64 0x50, the screen 0x3C |
| 22 | EXP_INT | TCA9555 interrupt, active low |
| 23, 21, 20 | MCLK, BCK, LRCK | **I2S** (SAI1) to the PCM3060 |
| 7, 8 | I2S_DOUT, I2S_DIN | to the codec's DIN, from its DOUT |
| 2, 3, 4, 5 | GATE_IN1–4 | gate inputs, active high |
| 17 | LED_DATA | WS2812 data (`WS2812Serial`, Serial4 TX), buffered to 5 V |
| 0 | SPARE2 | Serial1 RX. **Boy2: linked to MIDI_RX on J101** |
| 1 | SPARE1 | Serial1 TX. Not linked on Boy2, so there's no MIDI out and pin 1 is free |

Any pin not in this table isn't connected to the board.

## The chips

**TCA9555 expander, I2C 0x20.**
- **Port 0, outputs:**
  - P00–P05: the CV1–6 jack switches (1 = on);
  - P06: GATE_OE_N (1 = gate outputs disabled);
  - P07: an input, switch SW9.
- **Port 1, inputs:** switches SW1–8 on P10–P17.
- **Switch inputs** idle high (10 kΩ pull-ups) and read 0 while pressed.
- **Poll it.** Treat INT as a level and poll as a backstop (requirement 13). The test program
  polls every 20 ms.

**DAC8568, SPI-A, mode 1:**

| | |
|---|---|
| Speed | tested at 4 MHz; 17 MHz allowed |
| Channels | 0–5 = CV1–6; 6–7 unused on this board |
| Write and update | the 32-bit frame `0x03000000 \| ch << 20 \| code << 4` |
| Reference on | `0x090A0000`: internal, flexible, always on |
| Output, by design | V = 4.3 × 2.5 × code / 65536 − 3.3 × 2.5 × 22/34, about −5.34 to +5.41 V |
| 0 V code | about 32544 |
| Start-up | the order in requirement 3 is mandatory; `dac_start()` in the test program follows it |

**ADS8688, SPI-A, mode 1:**
- **Channels:** 0–5 read CV1–6 on the jack side, through 1 kΩ. Channels 6 and 7 are tied to
  ground.
- **Reading:** `0xC000 | ch << 10` selects a channel. The conversion arrives in the *next* frame,
  as 16-bit offset binary.
- **Range:** ±10.24 V is range code 0x00, in registers 0x05 + ch.
- **An open input reads about +0.207 V**, its internal bias (requirement 8).
- **With a jack's switch on,** the ADC reads that jack: `jack_from_adc()` adds back the 1 kΩ drop.

**74HCT595, SPI-B:**
- **Gate outs:** QA–QD drive GOUT1–4. Word bit 0 is GOUT1, and 1 = +5 V.
- **The 595 sees every SPI-B frame,** including the MCP3208's. Always shift a full gate word
  before pulsing RCLK, and keep SPI-B at 1 MHz or less (requirement 14).
- **Keep GATE_OE_N high until a word is latched** (requirement 4).
- **QE–QH are unused,** and QH′ reaches J603 for an off-board 74HCT595 chain.

**MCP3208, SPI-B:** six pots on CH0–5; CH6–7 are tied to ground. 1 MHz at most. Untested, and
Boy2 has no pots.

**PCM3060 codec:**
- **Hardware mode, with no control bus:** it starts on its own once MCLK runs. There is no
  `AudioControl` object; just `AudioOutputI2S` and `AudioInputI2S`.
- **Rate:** the Teensy Audio library's 44.1 kHz works (spec planned 48 kHz).
- **Levels:**
  - full scale is about 22 Vpp in (gain −0.136 into the codec's 3 Vpp; the test program scales
    by 22) and 20 Vpp out;
  - outputs are DC-coupled, and a sample of 1.0 is about +10 V;
  - inputs are AC-coupled.
- **Inputs invert, by design:** negate them (requirement 6).
- **Channels, by design:** I2S left is AIN1 and AOUT1; right is AIN2 and AOUT2. Not separately
  checked on the bench: the loopback test sent the same signal on both channels.
- **DC output trick:** `AudioSynthWaveform` sends nothing at amplitude 0, even with an offset. For
  a DC level, use a tiny amplitude plus `offset()`, as `hold_audio()` does.

**M24C64 EEPROM, I2C 0x50:**
- 8 KB, in 32-byte pages: the place for calibration.
- The test program used only the last page, 0x1FE0.
- Requirement 1 still applies: probe it before starting any other bus. On this build, though,
  the Teensy can't run without the rack, so a missing EEPROM means a fault.

**Gate inputs:**
- An LM393 comparator per input, with 100 kΩ to ground at the input.
- Design thresholds about 1.98 V rising and 1.67 V falling (not measured).
- Interrupt-capable pins. Catch 100 µs triggers with edge interrupts (requirement 12).

**MIDI in:**
- An H11L1 opto into Serial1 RX at 31 250 baud.
- **TRS Type A.** David's red Befaco cable is Type A; the grey one is Type B.
- There is no hardware THRU.

## Boy2: what is wired where

The panel is Boy's, fitted to the n8synth 10HP deck: a push encoder replaces the button and pot 1,
and TRS MIDI in replaces Boy's USB-only input. The full wire list is in stage 8 of the bring-up
plan, and the [wiring map](analogue_board_bringup/wiring_map.html) draws it batch by batch. That's
a copy kept in the repo; open it in a browser.

| Panel | Board channel | Firmware |
|---|---|---|
| gate1, gate2, gate3 | CV4, CV6, CV1 | DAC8568 ch 3, 5, 0; switches P03, P05, P00 |
| pitch1, pitch2, pitch3 | CV5, CV2, CV3 | DAC8568 ch 4, 1, 2; switches P04, P01, P02 |
| clk, drum1, drum2, rst | GOUT1, GOUT3, GOUT2, GOUT4 | 595 word bits 0, 2, 1, 3. The panel prints DRM1 and DRM2; the bring-up record calls drum2 "drum3" |
| audio in L, audio in R | AIN2, AIN1 | I2S **right**, I2S **left**: the panel's L and R are swapped |
| audio out L, audio out R | AOUT1, AOUT2 | I2S left, I2S right |
| MIDI in (TRS, Type A) | MI_T, MI_R | Serial1 RX, pin 0, 31 250 baud |
| encoder A, B | GIN3, GIN1 | `QuadEncoder(1, 4, 2, 0)` |
| encoder push | SW6 | TCA9555 P15, reads 0 while pressed |
| screen | J703 | SSD1306 **128×32** at 0x3C on `Wire` |

**Encoder** (a Bourns PEC11R):
- Its common is on POT_REF, the pot reference: 3.3 V. Free here because Boy2 has no pots. If pots
  are ever added, the common must move to +3V3D.
- The test program's settings: `QuadEncoder(1, 4, 2, 0)`, with no internal pull-ups (the LM393s
  have their own), `filterCount` 7 and `filterSamplePeriod` 255.
- **4 counts per detent, clockwise counts up.**
- The A contact bounces, about two edges a click, and the filter absorbs it.

**Screen:** the same 128×32 SSD1306 that was in Boy. Drive it as
`Adafruit_SSD1306(128, 32, &Wire, -1)`, as Boy does. Driven as 128×64, it shows only every other
row. It shares the I2C bus with the expander that reads the encoder's push, so keep Boy's
partial, one-page-per-pass updates.

## Measured on Boy2's board

Starting points for calibration, which belongs in the EEPROM (requirement 10: one point per volt
for pitch):

| What | Measured |
|---|---|
| CV outs, meter at the jack | about 1.8% below the design formula, the same on all six: 4 V gave 3.93, 5 V gave 4.91, 3 V gave 2.95, 2 V gave 1.96, −2 V gave −1.95, 1 V gave 0.98 |
| CV outs, the 0 V code | within 13 mV of 0 V on all six |
| CV outs, full range read back by the ADC | −5.18 to −5.24 V at code 0, +5.28 to +5.30 V at 65535 (the ADC path reads about 2% low) |
| Open CV inputs | +0.206 to +0.209 V |
| Gate outs | 5.02–5.05 V high, 0.00 V low |
| Audio out, DC | an offset of 0.5 (+5 V nominal) gave +4.86 V on both outs |
| Audio loopback | out to in: 9.9 Vpp read of the 10 sent, inverted, both channels |
| MIDI in | clean at 31 250 baud: note pairs and a 120 BPM clock with no garbled bytes |

## Porting from Boy

Boy here means Boy with its Teensy Expander, the 6HP companion that carries voices 3–4 and the
drums.

| | Boy (`eurorack_modules/src/teensy_move`) | Boy2 on Rev A |
|---|---|---|
| Audio | SGTL5000 audio shield, `AudioControlSGTL5000`. Its line-in gain suits the Move's line-level output, which it sends on at Eurorack level | PCM3060, no control object; inputs inverted. Scaled for Eurorack audio (10 Vpp nominal). Line-level sources come in through another module |
| Voices | four, on MIDI ch 1–4: gate, pitch and mod each | three: gate and pitch each, **no mod**. Ch 4 has no jacks |
| CV | four MCP4822s, eight outputs (pitch and mod × 4). Two on Boy (CS 33, 34); two on the Expander, selected through its 595's Q6 and Q7 | DAC8568 on SPI-A, its start-up order, and a TCA9555 switch per jack. Six outputs: three pitches and three gates |
| Pitch range | −3.0 to +6.6 V, note 36 at 0 V | about ±5.3 V: with the same law, notes above about 99 clip |
| Gates | gates 1–2 on pins 40 and 38; gates 3–4 on the Expander's 595 (Q1, Q0). All through 74HCT14 inverters: low at the pin is high at the jack | DAC8568 channels: a gate is a voltage written to the DAC, +5 V under its +5.3 V top |
| Clock, reset | pins 39 and 37, inverted the same way | GOUT1 and GOUT4 through the 74HCT595 on SPI-B, not inverted (1 = +5 V); OE through the TCA9555 |
| Drums | four, ch 10 notes 36–39, 500 µs pulses, on the Expander's 74HC595 (latch 32, Q2–Q5), inverted | two: drum1 on GOUT3 and drum2 on GOUT2, notes 36 and 37 by Boy's numbering |
| Mod | per channel, from velocity, CC#42 or a pot, last actuator wins | no jacks |
| Pots | four, by `analogRead`: Mod 1–4 on the STATUS page, the four FX settings on the FX page | none: the encoder replaces the button and pot 1 |
| Button | pin 2, `INPUT_PULLUP` | encoder push on TCA9555 SW6. **Pin 2 is now GIN1, the encoder's B** |
| Screen | SSD1306 128×32 at 0x3C | the same screen and address; the bus is now shared |
| MIDI | USB MIDI only (`USB_MIDI_SERIAL`), its link to the Move, forced to full speed for hubs in `setup()` | USB MIDI still, plus TRS MIDI in on Serial1 |
| Calibration | `calib_static.h`: gain and offset per channel | the EEPROM |

**None of Boy's pin numbers carry over.** Pins 32–34 and 40 aren't connected on Rev A, and 37–39
now carry SPI-B.

**Features Boy had and later dropped,** in its history in `eurorack_modules`. Both saw little use
because Boy's audio path was too noisy (David, 2026-11-01). Neither is a commitment for Boy2:
what the rest of the Teensy does is still open.
- **Chord mode** (added in `a2007a4`; last in `842fc36^:include/teensy_move/chord_library.h` and
  `1c3eaec^:src/teensy_move/main.cpp`): one-finger chords on MIDI ch 6, Maschine-style.
  - 40 progressions in five categories, eight chords each, played from the white keys.
  - Every voicing has four notes, with five voicing transforms.
  - The pots set root, category, progression and voicing. It drove the four pitch and gate CVs.
  - Boy2 has three voices, so a four-note voicing doesn't fit its CVs as it stands.
- **Drone** (last in `d691282^:src/teensy_move/main.cpp`): four voices of two detuned oscillators,
  each with an envelope, mixed into the passthrough. Removed in v3.

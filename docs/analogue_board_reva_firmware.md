# Analogue board Rev A (Teensy 4.1): notes for firmware

What a firmware session needs to know about the Rev A board (`teensy_core_midi`) and the Boy
module built on it. Written 2026-11-01, when its bring-up finished. Every value here was
read from the netlist, the generator's pin map or the working test program, or measured on the
built module. Where something is from the design only and not yet seen on the bench, it says so.

**Names.** The module was called Boy2 during the bring-up, and is now just **Boy** (David,
2026-11-01; the name was never used outside these repos). The earlier Boy, on its own hand-built
hardware, is **the old Boy**: its firmware is `teensy_move_old` in `eurorack_modules`.

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

- **Boy's hardware is fully tested (2026-11-01).** Every function Boy uses passed on the built
  module through its own jacks.
- **Not yet tested anywhere** (Boy doesn't use them):
  - the pots (MCP3208);
  - the WS2812 LED chain;
  - MIDI out;
  - the gate-input thresholds;
  - switches other than SW6;
  - the noise comparison.
- **Boy's firmware was started on 2026-11-01:** `eurorack_modules`, `src/teensy_move/`, env
  `teensy41`, with its own `docs/TEENSY_MOVE.md`. Mode 1 works on the bench (2026-11-01), all but TRS MIDI in, not yet tried.
  Warps, now mode 3, went on Boy on 2026-11-02: the codec runs at 96 kHz (its internal carrier plays
  C2 on a tuner where it should). CV in from another module works, by ear (V/oct into that
  carrier, David, 2026-11-04); tracking and calibration are for later.
  Chordal, now mode 2, went on Boy on 2026-11-05 and works from MIDI. Parasites' modes in Warps are flashed, and
  most aren't tried yet.
  It's ported from the old Boy's firmware, now `src/teensy_move_old/`, but the old Boy's chips and
  pins are all different: see [Porting from the old Boy](#porting-from-the-old-boy).
- **It took over `teensy_move`** (David, 2026-11-01). The old Boy's code is `teensy_move_old`, and
  the old Boy is decommissioned once the new one has taken over.
- **Its given job:** the Move companion. It takes the Move's three gate and pitch voices, two drum
  triggers, clock and reset into the rack. Move audio doesn't need to come in through Boy.

## Building and flashing on this Mac

This Mac is arm64 **with no Rosetta**. PlatformIO's Teensy compiler and `teensy_loader_cli` are
x86_64 only, so neither runs.

- **Compiler:** copy [`arm64_toolchain.py`](../firmware/analogue_board_test/arm64_toolchain.py)
  into the project and add `extra_scripts = post:arm64_toolchain.py`. It swaps in PlatformIO's
  arm64 GCC. Boy's `[env:teensy41]` in `eurorack_modules` has it; the old Boy's
  `[env:teensy_move_old]` doesn't.
- **Upload:** use `upload_protocol = teensy-gui` (the Teensy Loader app), not `teensy-cli`.
  The old Boy's env uses `teensy-cli`, which won't run here.
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
| 0 | SPARE2 | Serial1 RX. **Boy: linked to MIDI_RX on J101** |
| 1 | SPARE1 | Serial1 TX. Not linked on Boy, so there's no MIDI out and pin 1 is free |

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
Boy has no pots.

**PCM3060 codec:**
- **Hardware mode, with no control bus:** it starts on its own once MCLK runs. There is no
  `AudioControl` object; just `AudioOutputI2S` and `AudioInputI2S`.
- **Rate:** the Teensy Audio library's 44.1 kHz works (spec planned 48 kHz).
  - The library's rate is one constant, `AUDIO_SAMPLE_RATE_EXACT`. It derives MCLK from that as
    256 fS, with BCK at 64 fS.
  - The PCM3060 takes 256 fS up to 96 kHz in both its ADC and DAC (SLAS533B, p.15, Table 2).
    Its ADC stops at 96 kHz; the DAC goes to 192 kHz. In slave mode BCK must be 64 or 48 fS
    (p.19).
  - Boy runs at 96 kHz since 2026-11-02, for Warps. Confirmed on the bench by pitch: Warps'
    internal carrier, whose tables are built for 96 kHz, plays C2 where it should.
- **Fixed by the straps** (MODE 220 kΩ to ground; FMT, DEMP and IFMD 10 kΩ to ground): hardware
  mode with differential outputs, 24-bit I2S, de-emphasis off, ADC and DAC both slaves, one MCLK
  on SCKI1 and SCKI2. What only the serial modes reach is out of reach:
  - digital attenuation and soft mute;
  - the ADC high-pass's bypass, so it's always on (0.91 Hz at 48 kHz, 1.8 Hz at 96 kHz);
  - the DAC's double-rate oversampling;
  - the zero flags' settings. ZEROL and ZEROR aren't connected anyway.
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

## Boy: what is wired where

The panel is the old Boy's, fitted to the n8synth 10HP deck: a push encoder replaces the button and
pot 1, and TRS MIDI in replaces the old Boy's USB-only input. The full wire list is in stage 8 of
the bring-up plan, and the [wiring map](analogue_board_bringup/wiring_map.html) draws it batch by batch. That's
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
- Its common is on POT_REF, the pot reference: 3.3 V. Free here because Boy has no pots. If pots
  are ever added, the common must move to +3V3D.
- The test program's settings: `QuadEncoder(1, 4, 2, 0)`, with no internal pull-ups (the LM393s
  have their own), `filterCount` 7 and `filterSamplePeriod` 255.
- **4 counts per detent, clockwise counts up.**
- The A contact bounces, about two edges a click, and the filter absorbs it.

**Screen:** the same 128×32 SSD1306 that was in the old Boy. Drive it as
`Adafruit_SSD1306(128, 32, &Wire, -1, 400000, 400000)`. Driven as 128×64, it shows only every other
row. The last two arguments matter: by default the library sets the bus back to 100 kHz after each
of its transfers, which left the old Boy's screen at a quarter of its intended speed. The screen
shares the I2C bus with the expander that reads the encoder's push, so keep updates partial: Boy
sends a changed row in 32-byte pieces, one per pass of the loop.

## Measured on Boy's board

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

## Porting from the old Boy

The old Boy here includes its Teensy Expander, the 6HP companion that carries voices 3–4 and the
drums.

| | The old Boy (`eurorack_modules/src/teensy_move_old`) | Boy on Rev A |
|---|---|---|
| Audio | SGTL5000 audio shield, `AudioControlSGTL5000`. Its line-in gain suits the Move's line-level output, which it sends on at Eurorack level | PCM3060, no control object; inputs inverted. Scaled for Eurorack audio (10 Vpp nominal). Line-level sources come in through another module |
| Voices | four, on MIDI ch 1–4: gate, pitch and mod each | three: gate and pitch each, **no mod**. Ch 4 has no jacks |
| CV | four MCP4822s, eight outputs (pitch and mod × 4). Two on the old Boy (CS 33, 34); two on the Expander, selected through its 595's Q6 and Q7 | DAC8568 on SPI-A, its start-up order, and a TCA9555 switch per jack. Six outputs: three pitches and three gates |
| Pitch range | −3.0 to +6.6 V, note 36 at 0 V | about ±5.3 V: with the same law, notes above about 99 clip |
| Gates | gates 1–2 on pins 40 and 38; gates 3–4 on the Expander's 595 (Q1, Q0). All through 74HCT14 inverters: low at the pin is high at the jack | DAC8568 channels: a gate is a voltage written to the DAC, +5 V under its +5.3 V top |
| Clock, reset | pins 39 and 37, inverted the same way | GOUT1 and GOUT4 through the 74HCT595 on SPI-B, not inverted (1 = +5 V); OE through the TCA9555 |
| Drums | four, ch 10 notes 36–39, 500 µs pulses, on the Expander's 74HC595 (latch 32, Q2–Q5), inverted | two: drum1 on GOUT3 and drum2 on GOUT2, notes 36 and 37 by the old Boy's numbering |
| Mod | per channel, from velocity, CC#42 or a pot, last actuator wins | no jacks |
| Pots | four, by `analogRead`: Mod 1–4 on the STATUS page, the four FX settings on the FX page | none: the encoder replaces the button and pot 1 |
| Button | pin 2, `INPUT_PULLUP` | encoder push on TCA9555 SW6. **Pin 2 is now GIN1, the encoder's B** |
| Screen | SSD1306 128×32 at 0x3C | the same screen and address; the bus is now shared |
| MIDI | USB MIDI only (`USB_MIDI_SERIAL`), its link to the Move, forced to full speed for hubs in `setup()` | USB MIDI still, plus TRS MIDI in on Serial1 |
| Calibration | `calib_static.h`: gain and offset per channel | the EEPROM |

**None of the old Boy's pin numbers carry over.** Pins 32–34 and 40 aren't connected on Rev A,
and 37–39 now carry SPI-B.

**Features the old Boy had and later dropped,** in its history in `eurorack_modules`. Both saw
little use because the old Boy's audio path was too noisy (David, 2026-11-01). **Both came back as
mode 2, Chordal, on 2026-11-05** (`docs/TEENSY_MOVE.md`).
- **Chord mode** (added in `a2007a4`; last in `842fc36^:include/teensy_move/chord_library.h` and
  `1c3eaec^:src/teensy_move/main.cpp`): one-finger chords on MIDI ch 6, Maschine-style.
  - 40 progressions in five categories, eight chords each, played from the white keys.
  - Every voicing has four notes, with five voicing transforms.
  - The pots set root, category, progression and voicing. It drove the four pitch and gate CVs.
  - Boy's three voices don't take four notes, so Chordal puts the fourth on GATE1 as a second pitch CV.
- **Drone** (last in `d691282^:src/teensy_move/main.cpp`): four voices of two detuned oscillators,
  each with an envelope, mixed into the passthrough. Removed in v3.

## Ideas for the rest of the Teensy (brainstorm, 2026-11-01)

Nothing here is decided. It's the whole menu, including the ideas left out, so a later session
doesn't offer them again as new. Every panel jack is committed. What's left to build on:
- the stereo audio pair: inputs AC-coupled, outputs DC-coupled at ±10 V, so the outputs can
  carry CV;
- the 600 MHz M7 with its FPU;
- 1 MB RAM, plus pads under the Teensy for two 8 MB PSRAM chips (not fitted; the Teensy is
  socketed);
- 8 MB flash, and the microSD slot (the card sits behind the panel, so it suits files that are
  rarely changed);
- USB MIDI in both directions;
- the 16-bit DAC, at about 0.2 cent per step;
- spare MIDI: ch 4, drum notes above 37, CCs, and TRS as a second source.

| Idea | What it uses | Against it, or what was there before |
|---|---|---|
| **Glide per voice** | DAC writes at a control rate well above 1 kHz | Abacus can slew CV patched through it |
| **Audio outs as two CV outs**: velocity, or CC#42, for two voices | DC-coupled outputs | Shares the audio pair with every audio idea below |
| **Alternative tunings**: each note mapped through a table (just intonation, slendro and pelog, quarter tones, Scala files) | 16-bit DAC, flash or SD | The Move's MIDI carries plain note numbers, so a tuning has to be applied here. VCO tracking hides the small shifts of just intonation; the bold tunings come through |
| **Warps on the audio pair**: crossfade, fold, two ring mods, XOR, comparator, spectral, morph and vocoder | FPU | **Built, 2026-11-02, now mode 3**, from `eurorack_modules/third_party/eurorack/warps` (MIT). Warps isn't in the rack. Its internal oscillator can be the carrier, played by a Move voice. Its oscillator runs at 96 kHz against the Teensy's 44.1 kHz. A vocoder was already on MultiOsc's list of future engines, unbuilt |
| **The rack plays the Move**: pitch-track a rack voice on an audio input, send it to the Move as notes | FPU, USB MIDI out | Tracking adds a few tens of ms. Untested whether the Move plays and records notes from a USB device |
| **Loop slicer**: record a bar or two of the rack on a Move note, play slices from Move pads | PSRAM (16 MB holds about 95 s of stereo) | The Move's own sampler may cover it. Oneiroi has a 5 s looper, not locked to the Move |
| **Polyphonic voice** on a spare channel, so the Move can send chords through the rack's mono filters | FPU | The Move has its own polysynths. **Built as mode 2, Chordal, 2026-11-05** |
| **Tempo-synced stereo FX**: delays in note values, beat repeat | FPU, MIDI clock | The Daisy MultiFX, FX Aid, Wish and Oneiroi already do delay and texture |

**Left out because the rack already has them:**
- clock division and swing: DivSkip, Steppy;
- clock-synced LFOs and envelopes: Four LFO, Peaks, Waves, Steps;
- granular: Monsoon, Wish;
- envelope follower: the I4;
- quantising: Scales, the O&C.

A USB audio interface is left out too: the ES-10 and the Scarlett already do that job. Also,
whether the Move as host would accept a combined MIDI and audio device is unknown.

**Decided (David, 2026-11-05): Move, Chordal, Warps.** This replaces the 2026-11-01 plan, where mode 3
was weirder two-input processing.
- **Mode 1** is the Move companion.
- **Mode 2** is Chordal: one finger plays four notes that lead into the next chord.
- **Mode 3** is Warps, the port, on Parasites' DSP: stock Warps as its Meta mode and eight more beside
  it, with Chordal's engine as IN 1. This is the Beyond Warps video.

The menu below is what's left of the two-input ideas, with no mode of its own for now. Warps leaves room for them,
  because it runs on much less: an STM32F4 Cortex-M4 at 168 MHz (`warps/makefile`), a 96 kHz
  codec, its cross-modulation 6× oversampled, a 20-band vocoder, one main output plus an aux, and
  no long buffers.

What makes modes work on this board:
- **The six CV jacks are bidirectional.** With a jack's switch off it's an input to the ADS8688
  (±10.24 V), so any mode can have six CV ins. Warps has four: Level 1, Level 2, Algorithm
  and Timbre, with Level 1's taken as V/oct when the internal oscillator is on (`cv_scaler.cc`).
  That leaves two spare in Warps. The bring-up checked open inputs and switch isolation; reading
  a patched CV isn't tested yet.
- **The panel's labels belong to mode 1.** In other modes the screen says what each jack does.
- **The gate outs** can carry gates made from the audio: comparator, envelope or onset.
- **MIDI still arrives in every mode.** In Warps, Move notes play the CHORD carrier.
- **The mode is chosen at power-on and holds for the session** (David). Jack directions are set
  once a session and never switched within a mode. A source still patched into a CV jack would
  meet the DAC through the 1 kΩ.
- **Back to the chooser without a power cycle** (David: MultiOsc's lack of this is a pain). Hold the
  encoder's push for 2 s. The board goes to its power-on state and the Teensy restarts into the
  chooser, so each mode starts from a clean Teensy.

**Spectral morphing and sidechain ducking** were first in line (David, 2026-11-01).

The menu:
- stereo out, with the two sides as two algorithms or a spread;
- more vocoder bands, or an FFT vocoder with a formant shift;
- FFT cross-synthesis: one input's spectral envelope on the other, or a morph between the two
  spectra;
- live convolution: capture a moment of one input as an impulse response and play the other
  through it;
- sidechain dynamics: ducking, gating or compression of one input keyed by the other;
- cross-triggered grains: one input fills a buffer, and the other's onsets play grains from it
  (Wish and Monsoon are granular, but neither is keyed by a second signal);
- pitch-follow: the pitch tracked from one input tunes a resonant filter or harmoniser on the
  other.
- chords into the vocoder (2026-11-05): **built as Warps' CHORD carrier.** The Move plays chords,
  Chordal's engine feeds Warps in place of IN-L, and the rack is the modulator. Warps' DSP is unchanged;
- vocoder bands as CV (2026-11-05): Warps has 20 band followers (`vocoder.h`, private, so this needs
  its filter bank and followers of our own). Group them into up to six jacks set as outputs: one audio
  input becomes six spectral modulators. The rack's I4 follows one level, not bands.

[Warps Parasite](https://mqtthiqs.github.io/parasites/warps) went in on 2026-11-05: nine modes including
a dual delay, a binaural Doppler panner, a bit-mangler and a Chebyshev waveshaper. It replaces the stock
DSP, since its Meta mode nulls against stock in all but three documented ways (`docs/TEENSY_MOVE.md`).
Its README says MIT for the STM32 projects, and the `warps/` and `stmlib` sources it builds from carry
the MIT header, though GitHub detects no licence file. It isn't new: the Michigan Synth Works Twist ships with it, and
[Warps Symbiote](https://leandrob13.github.io/Electronic-Ruminations/warps-symbiote) builds on it.
Warps' CPU on Boy, with the chord engine running too: 65 % at peak in VOCODER and 64 % in META (2026-11-05).
The chord engine alone is 27-38 %, by patch.

How the Warps port settled them (2026-11-02; the details are in `docs/TEENSY_MOVE.md`):
- **Sample rate: 96 kHz, through the Teensy Audio library.**
  - Warps' pitch and vocoder tables are generated for 96 kHz (`warps/resources/lookup_tables.py`),
    and so are its resampling filters. At any other rate they would have to be regenerated.
  - The library isn't tied to the audio shield (only `AudioControlSGTL5000` is), and its rate is
    one build flag. So Boy needs no I2S driver of its own; the 1 Nov note here suggested one.
  - Blocks are 96 samples: Warps' largest, and its own host test's size.
- **Knobs.** The encoder pages through Warps' four knobs and its button (carrier shape), plus
  the frequency-shifter easter egg, with the CV ins on top. The Move can't send CCs (David,
  2026-11-01).
- **Patch detection.** Boy has no probe: the jack-detect probe was dropped on 2026-10-16.
  - An open CV input sits still at the ADS8688's bias, about +0.207 V: 1 MΩ to its 2.25 V
    against 100 kΩ to ground.
  - So a jack within 20 mV of that, steady to 4 mV, for 100 ms counts as unpatched. This stands
    in for Warps' probe.
  - A patched source held still in that window can't be told from an open jack (requirement 8).
- **Jacks:**
  - IN-L and IN-R are the carrier and modulator, and OUT-L and OUT-R are Warps' OUT and AUX.
  - PITCH1 is Level 1 (and V/oct), PITCH2 is Level 2, GATE1 is Algorithm and GATE2 is Timbre.
  - The screen marks a patched jack with `*`.
- **Levels follow Warps' hardware** (`warps_v30.pdf`):
  - inputs gain 22/16 (Warps' full scale is 16 Vpp, Boy's 22);
  - outputs are 1:1 (about 19.5 Vpp against Boy's 19.4);
  - a 2.7 Hz high-pass stands in for Warps' output capacitors.

**Outside the Move role:** plugged into the Mac, Boy is a USB MIDI-to-CV with three voices and,
with the two CV outs above, two CC outs. That's what the Strudel re-record lost with the Workshop
Computer. In the rig's cable list (`eight4awish-video/src/cables.ts`), it gave one pitch and
one gate (to Ogham's CLK/VOCT and SYNC) and two CC outs (to Ogham CVA and Alchemy Lab CV1).

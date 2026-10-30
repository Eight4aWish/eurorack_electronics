# Analogue board Rev A (Teensy 4.1): bring-up

The plan for the first of the two `teensy_core_midi` boards, from the box to a working
module. Written 2026-10-30, the day the boards arrived. Fill in the readings as you go; what
Rev A needed feeds [Rev B §7](analogue_board_revb.md#7-lessons-from-the-teensy-bring-up).

**The rule:** one stage at a time, and stop at the first reading that is off. Every stage
assumes the one before it passed.

**No bench supply.** A current-limited supply would catch a short before it heated anything.
Without one, two things stand in for it: the multimeter checks for shorts before power ever
goes on (stage 3), and the first power-on lasts three seconds (stage 4).

**Film it.** The unboxing, the first power-on and the first sound can't be re-shot for the
hardware video.

**The boards carry no readable labels**, so find things from these pictures, drawn on the
placement renders from the board file:
- test points on the [outward face](analogue_board_bringup/test_points_outward.png) and the
  [deck face](analogue_board_bringup/test_points_deck.png);
- the [wiring holes](analogue_board_bringup/holes_outward.png) the stage 6 blocks use;
- [MIDI](analogue_board_bringup/midi_outward.png): U1002's pin 1, the J101 links, the TRS holes.

## What you need

- Digital multimeter, the rack, and a known-good 10-pin Eurorack power ribbon.
- Soldering kit, flux, and a magnifier or a phone camera for close-ups.
- The hand-soldered parts. J201, A101 and J101 are yours by design (spec §2: you solder
  only headers, sockets and the deck wiring). U1002 is the one JLC left off.

  | Part | What | When |
  |---|---|---|
  | J201 | 2×5 shrouded Eurorack power header | Stage 2, before any power |
  | A101 | Female headers for the Teensy, 2 × 24 outer rows | Stage 2 |
  | U1002 | H11L1 MIDI opto, through-hole in place of the SMD part | Stage 7, before MIDI |
  | J101 | Two wire links: SPARE1–MIDI_TX, SPARE2–MIDI_RX | Stage 7, before MIDI |

  C209 and R205 are empty on purpose: they are the buck's feed-forward, drawn but not fitted.

## Stage 1: look

Unpowered, out of the bag. Check by eye or under the magnifier:

- **Diodes D201, D202, D203** (SS34): cathode bands as the silkscreen shows.
- **Regulators:** U201 buck (SOT-23-6), U202 L78M05 (the large TO-252), U203 and U204 XC6206
  (SOT-23).
- **Pin 1 of every IC**, and no solder bridges on the fine-pitch chips: U301 PCM3060,
  U401 ADS8688, U501 DAC8568, U701 TCA9555, U602 74HCT595.
- **U1002 is empty**, as expected. Anything else missing or lifted, stop.

## Stage 2: solder the power header and the Teensy sockets

1. **J201, the power header.** Before soldering, plug the ribbon into the loose header and
   check that the **red stripe (−12 V) lands on pin 1**, the squared-off pad. J201 pins 1–2 are
   −12 V and 9–10 are +12 V. Then solder it that way round.
2. **A101, the Teensy sockets.** Fit the female headers on the board, using the Teensy (with
   its own male headers) as the jig so the rows line up, then take the Teensy out again. It
   stays out until stage 5.
3. **Cut the Teensy's VIN–VUSB pads** (spec §5). Otherwise the rack's 5 V reaches the
   computer's USB port. Check with the meter's continuity beep that VIN and VUSB no longer
   connect. With the pads cut, the Teensy runs only when the rack is on, USB or not.

## Stage 3: cold checks (unpowered, Teensy out)

Resistance from each rail's test point to ground (TP203 or TP204), red lead on the rail. A
reading that starts low and climbs is the capacitors charging, and is fine. **A steady reading
under about 10 Ω is a short: stop.**

| Rail | Test point | Face | Expect | Reading |
|---|---|---|---|---|
| +12V | TP201 | outward | high, climbing | |
| −12V | TP202 | deck | high, climbing | |
| +5VD | TP205 | deck | kΩ or more | |
| +5VA | TP206 (no label) | outward | **10 kΩ or a little less** | |
| +3V3A | TP207 (no label) | deck | kΩ or more | |
| +3V3D | TP208 | outward | **about 680 Ω or less**: R210, the minimum load, not a short | |
| MOD_5V | TP209 | deck | high (D203 blocks the path back) | |
| +12V to −12V | TP201–TP202 | | high | |
| +12V to +5VD | TP201–TP205 | | high | |

The +5VA reading is the 10 kΩ that keeps the ADS8688's ±20 V input protection working when the
board is unpowered (spec §15). Rev A is the first chance to measure it.

Test point positions, in mm from the top left of each face, are in
[`wiring_map.md`](../hardware/analogue_board/teensy_core_midi/output/wiring_map.md).

## Stage 4: first power (Teensy out, deck not wired)

1. Rack off. Plug in the ribbon, red stripe to −12 V. Board on something non-conductive.
2. **Power on, count three seconds, power off.**
3. Touch U201, U202, U203, U204 and D201–D203. Anything hot or any smell: stop.
4. Power on again and measure, black lead on TP203 or TP204:

| Rail | Test point | Expect | Reading, 2026-10-30 |
|---|---|---|---|
| +12V | TP201 | the rack's +12 V less 0.2–0.5 V (SS34), so about 11.6 V | in range |
| −12V | TP202 | the same, negative: about −11.6 V | in range |
| +5VD | TP205 | 5.07 V (buck, 15k/2k divider) | in range |
| +5VA | TP206 | about 5.0 V (L78M05) | 4.98 V, at U202 with the Teensy in |
| +3V3A | TP207 | 3.3 V, within 2% (XC6206) | 3.29 V, Teensy in |
| +3V3D | TP208 | 3.3 V, within 2% | in range |
| MOD_5V | TP209 | just under +5VD with nothing on it | 4.72 V, Teensy in (stage 5) |

TP206 is under the Teensy once it is fitted. U202's output is the same rail ahead of its link
R207: the right-hand leg of the big regulator beside J201. MOD_5V is also the Teensy's VIN, the
corner pin straight across from socket pin 1.

**If a rail is wrong**, each regulator has a 0 Ω link to its loads: R206 (+5VD), R207 (+5VA),
R208 (+3V3A), R209 (+3V3D). The test points are on the load side. With a link lifted, measure
on its regulator-side pad. Right there means the fault is in the loads; wrong there means the
regulator. The buck only starts once +12 V passes about 9.2 V (its EN divider), so a low +12 V
also shows as a dead +5VD.

A multimeter can't see the buck's 350 kHz ripple; that waits for the noise comparison.

## Stage 5: the Teensy in

1. Rack off. Teensy in, pads cut, the right way round: socket pin 1 (the square pad) is the
   Teensy's GND pin in the USB corner, and socket pins 2 and 3 are its pins 0 and 1. Before
   it goes in, socket pin 1 should beep to TP203.
2. USB to the Mac, rack on. The Teensy should enumerate. A new one runs PJRC's factory program:
   the orange LED blinks slowly and the Mac sees "Teensyduino RawHID". Pin 13 is SPIA_SCK here,
   so the blink only clocks a bus whose chip selects are pulled up.
3. TP209 (MOD_5V) now carries the Teensy, so it drops to about 4.6–4.8 V. Its VIN range is
   3.6–5.5 V.
4. Flash the stage 6 program **in the foreground**: a background upload once half-programmed and
   bricked a module. In `firmware/analogue_board_test`, `pio run -t upload` opens the Teensy
   Loader app, which reboots the Teensy and programs it; it comes back as "USB Serial".

## Stage 6: one block at a time (test firmware)

A single test program with a serial menu, one command per block, each printing what it read:
[`firmware/analogue_board_test`](../firmware/analogue_board_test/src/main.cpp). Open
`pio device monitor` there, type a block number and Enter; `h` lists them, `0` puts everything
back in a safe state. At boot only I2C runs; every other pin stays an input until its block is
asked for. The pass marks below are what the program checks. Pins follow the spec's §6.3 pin
map. The firmware requirements in spec §15 apply throughout, and the DAC start-up order
matters most.

| # | Block | Needs the deck? | Test | Pass |
|---|---|---|---|---|
| 1 | I2C | no | scan the bus | 0x20 (TCA9555) and 0x50 (M24C64) answer |
| 2 | EEPROM | no | write a page, read it back | same bytes |
| 3 | Expander | no | every jack switch off, GATE_OE_N high; read port 1 and EXP_INT | reads settle, INT idles high |
| 4 | ADC | no | read ADS8688 registers back, then all 8 channels | registers echo; an open CV1–6 reads about +0.2 V (its bias); AIN6–7 are tied to ground and read 0 V |
| 5 | DAC to ADC | no | DAC8568 start-up in spec order, then close one switch at a time: CV1–6 are read back by the ADC through the switch | each channel tracks the codes written; note the voltage at the lowest and highest codes |
| 6 | Codec clocks | no | start I2S at 44.1 kHz, the Teensy Audio library's rate | DC average at TP301 (MCLK), TP302 (BCK) and TP303 (LRCK) about 1.65 V, or 11.29 MHz, 2.82 MHz and 44.1 kHz if the meter counts Hz |
| 7 | Gate outs | no | shift a gate word, latch it, then GATE_OE_N low | about 5 V and 0 V at the gate-out holes, as written; with GOUTn wired to GINn the program checks itself |
| 8 | Gate ins | jack or wire | a rack gate into each; `8t N` sweeps CV1, wired to GIN N | trips at about 2.0 V rising, 1.7 V falling |
| 9 | Pots | deck | MCP3208, SPI-B at 1 MHz or less | each pot sweeps 0 to full scale |
| 10 | Audio | deck jacks | sine out; audio in looped back or into the ES-10 | clean sine; the input reads inverted (spec: negate it) |
| 11 | LEDs | deck | short WS2812 chain, capped current | colours as sent |
| 12 | Encoder | deck | A and B on gate inputs 3–4 (QuadEncoder), its common to +3V3D (J703 hole 3); push across a button hole and GND | counts both ways, push registers |
| 13 | MIDI | after stage 7 | Serial1 at 31 250 baud; loop OUT to IN with a TRS cable, or play notes in | bytes in = bytes out |

This board has six CV jacks, CV1–6, all switchable. The fixed-direction CV7–8 were left out of
its core set (`teensy_core_midi` in `tools/analogue_board/variant.py`), so there is no CV7–8 test.

The encoder needs no parts: with its common on +3V3D, a closed contact puts 3.3 V on the gate
input and an open one is pulled to 0 V by the input's own 100 kΩ. Gate inputs 3–4 belong to the
encoder from block 12 until a restart.

## Stage 7: MIDI in

1. Rack off. Fit the through-hole H11L1 at U1002: trim the legs short and bend each to sit flat
   on its SMD pad. Pin 1, the dot, goes on the top-left pad with the outward face up and J201
   at the bottom right.
2. Wire the J101 links: SPARE1 to MIDI_TX, SPARE2 to MIDI_RX. Without them, Teensy pins 1 and 0
   stay plain spare GPIO.
3. Run block 13.

## Log

| Date | Stage | What happened | Bodge or change | For Rev B? |
|---|---|---|---|---|
| 2026-10-30 | 1–2 | Looked over; J201 and A101 soldered; VIN–VUSB cut and checked with the meter | | |
| 2026-10-30 | 1 | Pads copper-coloured: the OSP finish ordered. Solders fine, but the wiring holes are not tinned (the spec assumed HASL) | | Pick HASL or ENIG if boards will wait or be rewired often |
| 2026-10-30 | 3–4 | The silkscreen printed as designed, but the plan names test points by number (TP209) and the board does not: it prints a short net name ("5V MOD") beside 15 of the 27, at 0.8 mm (JLC asks for 1.0 mm); 12 had no room | the pictures above | One name for each test point, printed beside every one at 1.0 mm / 0.15 mm or more, and used by the plan |
| 2026-10-30 | 1 | No Eight4aWish name or licence notice on the silkscreen: both are only in the KiCad title blocks | | A board line: name, revision, Eight4aWish, CC BY-SA 4.0 |
| 2026-10-30 | 4 | +12V, −12V, +5VD and +3V3D in range | | |
| 2026-10-30 | 5 | Teensy in: factory blink, enumerated. MOD_5V 4.72 V, +3V3A 3.29 V, +5VA 4.98 V | | TP206 (+5VA), TP401, TP601 lie under the module; TP605 and TP702 at its ends |
| 2026-10-30 | 5 | PlatformIO's Teensy compiler and teensy_loader_cli are x86_64 only, and this Mac has no Rosetta | `arm64_toolchain.py` (PlatformIO's arm64 GCC) and the Teensy Loader app (`teensy-gui`) | |
| 2026-10-30 | 6 | Blocks 1–5 pass. Open CV inputs +0.206 to +0.209 V (+0.205 predicted). DAC to ADC, uncalibrated: −5.18 to −5.24 V at code 0, +5.28 to +5.30 V at 65535 (−5.22 and +5.30 predicted through the 2 kΩ path), the 0 V code within 13 mV of 0, worst error 34 mV; every switch isolates | | |
| 2026-10-30 | 7 | H11L1 fitted at U1002, dot on pin 1 | | |

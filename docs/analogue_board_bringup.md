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

| Rail | Test point | Expect | Reading |
|---|---|---|---|
| +12V | TP201 | the rack's +12 V less 0.2–0.5 V (SS34), so about 11.6 V | |
| −12V | TP202 | the same, negative: about −11.6 V | |
| +5VD | TP205 | 5.07 V (buck, 15k/2k divider) | |
| +5VA | TP206 | about 5.0 V (L78M05) | |
| +3V3A | TP207 | 3.3 V, within 2% (XC6206) | |
| +3V3D | TP208 | 3.3 V, within 2% | |
| MOD_5V | TP209 | just under +5VD with nothing on it | |

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
2. USB to the Mac, rack on. The Teensy should enumerate.
3. TP209 (MOD_5V) now carries the Teensy, so it drops to about 4.6–4.8 V. Its VIN range is
   3.6–5.5 V.
4. Flash test firmware **in the foreground**: a background upload once half-programmed and
   bricked a module.

## Stage 6: one block at a time (test firmware)

A single test program with a serial menu, one command per block, each printing what it read.
The pass marks below are what that program checks. Pins follow the spec's §6.3 pin map. The
firmware requirements in spec §15 apply throughout, and the DAC start-up order matters most.

| # | Block | Needs the deck? | Test | Pass |
|---|---|---|---|---|
| 1 | I2C | no | scan the bus | 0x20 (TCA9555) and 0x50 (M24C64) answer |
| 2 | EEPROM | no | write a page, read it back | same bytes |
| 3 | Expander | no | every jack switch off, GATE_OE_N high; read port 1 and EXP_INT | reads settle, INT idles high |
| 4 | ADC | no | read ADS8688 registers back, then all 8 channels | registers echo; an unpatched input reads about +0.2 V (its bias) |
| 5 | DAC to ADC | no | DAC8568 start-up in spec order, then close one switch at a time: CV1–6 are read back by the ADC through the switch | each channel tracks the codes written; note the voltage at the lowest and highest codes |
| 6 | Codec clocks | no | start I2S at 48 kHz | DC average at TP303 (LRCK) and TP302 (BCK) about 1.65 V, or 48 kHz and 3.072 MHz if the meter counts Hz |
| 7 | Gate outs | no | shift a gate word, latch it, then GATE_OE_N low | about 5 V and 0 V at the gate-out holes, as written |
| 8 | Gate ins | jack or wire | a rack gate into each | trips at about 2.0 V rising, 1.7 V falling |
| 9 | Pots | deck | MCP3208, SPI-B at 1 MHz or less | each pot sweeps 0 to full scale |
| 10 | Audio | deck jacks | sine out; audio in looped back or into the ES-10 | clean sine; the input reads inverted (spec: negate it) |
| 11 | LEDs | deck | short WS2812 chain, capped current | colours as sent |
| 12 | Encoder | deck | A and B on gate inputs 3–4 (QuadEncoder); push on a button hole | counts both ways, push registers |
| 13 | MIDI | after stage 7 | Serial1 at 31 250 baud; loop OUT to IN with a TRS cable, or play notes in | bytes in = bytes out |

CV7–8 have no switch path to the ADC: test them with a cable from CV7–8 out to CVI7–8 once the
deck is wired.

## Stage 7: MIDI in

1. Rack off. Fit the through-hole H11L1 at U1002: trim the legs short and bend each to sit flat
   on its SMD pad, pin 1 to the marked pad.
2. Wire the J101 links: SPARE1 to MIDI_TX, SPARE2 to MIDI_RX. Without them, Teensy pins 1 and 0
   stay plain spare GPIO.
3. Run block 13.

## Log

| Date | Stage | What happened | Bodge or change | For Rev B? |
|---|---|---|---|---|
| | | | | |

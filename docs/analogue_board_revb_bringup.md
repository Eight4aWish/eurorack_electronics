# Analogue board Rev B (ESP32-P4): bring-up

The plan for the first Rev B board, with the Waveshare ESP32-P4-WIFI6 as its module (working
name Health; see [Rev B §8](analogue_board_revb.md#8-order-changes-and-the-gesture-module-2026-11-02)).
Started 2026-11-16, the day the boards arrived. It follows [Rev A's bring-up](analogue_board_bringup.md),
stage for stage, and keeps the same rule: **one stage at a time, and stop at the first reading that
is off.**

What differs from Rev A:
- **Every test point has its name printed beside it** (Rev B §4), and there are no ground test
  points: the meter's black lead goes on any square ground hole.
- **JP201 must be bridged before the P4 goes in**, so that Q201 bypasses the Schottky D203 and the
  P4's 5 V buck gets its 4.5 V minimum (`analogue_board_esp32p4.md`, Soft problems).
- **No pads to cut** on the module: the P4's pin 39 has its own ideal diode against USB, and USB's
  VBUS on pin 40 turns Q201 off.
- **MIDI is wired straight** to the module's UART pins: no J101 links, and JLC placed U1002.
- **The converters need one line of firmware first**: the P4's pins 21, 22 and 24 sit on LDO
  channel 4, which must be set to 3.3 V before the converter bus works.

**Pictures** (drawn on the routed renders by the board file's coordinates):
- [JP201 on the deck face](analogue_board_revb_bringup/jp201_deck.png);
- [the module socket on the outward face](analogue_board_revb_bringup/module_outward.png): pin 1,
  the P4's outline and orientation, and the two test points whose labels J201 covers.

## Stages 1-2: look, and solder J201 and the module sockets

As Rev A. The P4 has its own male headers; the board takes female sockets at A101.

## Stage 3: cold checks

As Rev A's stage 3, black lead on a square ground hole.

## Stage 4: first power, module out

| Rail | Label | Face | Expect | Reading, 2026-11-16 |
|---|---|---|---|---|
| +12V | +12V | deck | the rack's +12 V less the SS34, about 11.6 V | 11.70 V |
| −12V | −12V (under J201) | outward | about −11.6 V | −11.68 V |
| +5VD | +5VD | deck | 5.07 V (buck, 15k/2k) | 5.08 V |
| +5VA | +5VA | deck | about 5.0 V (L78M05) | 4.98 V |
| +3V3A | +3V3A | deck, top half | 3.3 V within 2 % | 3.30 V |
| +3V3D | +3V3D | deck | 3.3 V within 2 % | 3.29 V |
| MOD_5V | 5V MOD (under J201) | outward | just under +5VD with nothing on it | 5.02 V |

## Stage 5: the P4 in

1. **Rack off, ribbon out. Bridge JP201** with a blob of solder across its two half-moon pads
   ([picture](analogue_board_revb_bringup/jp201_deck.png): deck face, the grey oval just below
   D203). The meter should beep across it.
2. **Check the socket's numbering:** pin 1 is the square pad, and pin 3, two holes up from it,
   beeps to a square ground hole ([picture](analogue_board_revb_bringup/module_outward.png)).
3. **The P4 in, USB-C end down,** towards the board's bottom edge, its parts facing out and its
   pin 1 on the square pad. The antenna end reaches almost to the top edge.
4. **USB unplugged.** Rack on, count three seconds, rack off. Touch U201 (the buck), D203, Q201
   and the P4: anything hot or any smell, stop.
5. **Rack on and measure:**
   - **5V MOD should now read about 5.0 V**, a few tens of mV under +5VD: Q201 is carrying the
     P4. About 4.6-4.7 V means the current is going through D203, so JP201 isn't bridged.
   - +5VD and +3V3D as in stage 4.
6. **USB-C to the Mac, rack already on.** The P4's USB-C is its CH343 serial bridge. The console
   at 115 200 baud shows the boot log of whatever is on the P4. The last firmware built for it was
   the camera-to-HDMI test of 29 Oct, which uses only GPIO7 and 8 on the header (pins 16 and 17,
   which Rev B leaves to two wiring holes). Every other header pin is an input from reset.

## Stage 6: one block at a time (test firmware)

To write: an ESP-IDF port of [`firmware/analogue_board_test`](../firmware/analogue_board_test/src/main.cpp)'s
serial menu, the same blocks against Rev B's pin map (`analogue_board_esp32p4.md`, Pin table).
Its first act is `esp_ldo_acquire_channel` for channel 4 at 3300 mV. What changes from Rev A:
- no EXP_INT: the expander is polled;
- the CV outputs swing ±10 V (Rev B §8: −10.71 to +10.54 V, 0 V at code ≈ 33044);
- I2C on GPIO31/30, and the P4's own bus (GPIO8/7) left alone;
- gate inputs on GPIO50, 49, 29 and 4 (pins 9, 10, 6, 12);
- MIDI on UART pins 1 and 2 with no links;
- the codec's MCLK from the APLL, so no video during the test.

## Stage 7: MIDI in

Not on Health: its panel has no MIDI jack. MIDI_TX and MIDI_RX are wired straight to the P4's
UART pins (1 and 2), so a later panel with a TRS jack needs only its deck wires and block 13.

## Stage 8: the control deck

Health's panel ([Rev B §8](analogue_board_revb.md#8-order-changes-and-the-gesture-module-2026-11-02)),
as the front reads:

| Row | Left | Middle | Right |
|---|---|---|---|
| 1 | MENU, the push encoder | BTN1 | BTN2 |
| 2 | X pot | Y pot | Z pot |
| 3 | X1 | Y1 | Z1 |
| 4 | X2 | Y2 | Z2 |
| 5 | IN-L | RST | OUT-L |
| 6 | IN-R | CLK | OUT-R |

X1–Z2 are the six two-way CV channels, set as outputs; RST and CLK are gate inputs. Every wire,
with its hole and length, is on the [wiring map](https://claude.ai/artifact/RptmC4zktQrcPzZHXxPau4)
(Health panel; its Fit switch picks the way the deck was built; a copy is kept at
[`analogue_board_bringup/wiring_map.html`](analogue_board_bringup/wiring_map.html)). 25 wires:
243 mm of hand wire built the n8synth way, 246 mm the other way, one across the board either way.
Channel numbers are firmware labels, so each wire takes the nearest free hole of its kind.

**Links on the deck itself** (built 2026-11-17, all but the pots). Every D pad is on the
deck-wide ground bus.
- Each mono jack's sleeve on pad C, with C's other contact linked to D: 12 jacks. Pad B, the
  switch lug, stays unwired, except:
- **IN-R's pad B linked to IN-L's pad A,** the normal: a mono cable in IN-L reaches both inputs.
- MENU (PEC11R): pins A, C, B on pads A, B, C; one push pin to BTN1's pad C, the other to D.
- BTN1 and BTN2: legs on pads A and B, pad A bridged to D.
- X, Y, Z: pad A, the ground end, bridged to D. Each top (pad C) takes its own board wire to
  POT_REF, not a chain on the deck (Rev B §8).
- Z1's pad C, on D through its jack, carries the deck's one ground wire to the board.

**Wire it in batches, and test each before the next**, as on Rev A. Before powering after each
batch, check with the meter that no newly wired hole beeps to a ground hole (a switch line beeps
only while its button is pressed). Batches 1-5 are tested on the stage 6 program, so it comes
first. **The pots go last:** they arrive on 2026-11-18, the day after the deck was built.

| Batch | Wires | Test |
|---|---|---|
| 0. Deck ground | Z1's pad C → GND (LO 19), 3 mm | continuity, any jack sleeve to the board's GND (passed 2026-11-17) |
| 1. Encoder and buttons | MENU A, B → GIN1, GIN2, common → +3V3D; the push (through BTN1's pad C), BTN1 and BTN2 → three SW lines | block 8: turning slowly steps GIN1 and GIN2 in turn; block 12 counts both ways; block 3 sees the push and each button |
| 2. CV outs | X1–Z2 → CV1–6 | block 5 (nothing patched), then `c N V` holds jack N's voltage for the meter |
| 3. Gate ins | RST, CLK → GIN3, GIN4 | block 8: a rack clock into each steps its gate input |
| 4. Audio | IN-L, IN-R → AIN1, AIN2; OUT-L, OUT-R → AOUT1, AOUT2 | block 10: sine out, then patch the outs into the ins. Then OUT-L into IN-L alone: both inputs read it through the normal, until a cable goes into IN-R |
| 5. Pots | X, Y, Z: top (pad C) → the POT_REF two rows up, 6 mm; wiper (pad B) → POT4, POT5, POT6, 3 mm | block 9: each sweeps 0 to full scale |

## Log

| Date | Stage | What happened | Bodge or change | For the next board? |
|---|---|---|---|---|
| 2026-11-16 | — | The Rev B boards arrived, with the four PCB faceplates | | |
| 2026-11-16 | 2 | J201 and the module sockets soldered; the P4 ready to fit | | |
| 2026-11-16 | 4 | Module out: +12V 11.70, −12V −11.68, +5VD 5.08, +5VA 4.98, +3V3D 3.29, 5V MOD 5.02 V, +3V3A 3.30 V. All seven in range | | |
| 2026-11-16 | 5 | P4 in, USB-C end down, rack on: 5V MOD 5.07 V against +5VD's 5.08, so Q201 carries the P4 past D203 | | |
| 2026-11-16 | 5 | USB-C to the Mac with the rack on, the P4 reset through the CH343's RTS: it boots on the board (ROM, the 32 MB PSRAM test OK, 400 MHz, chip v3.2) and runs the camera-to-HDMI app of 29 Oct, which stops at "LT8912B not found" because no display is connected. Its I2C pull-up warning is ESP-IDF's notice for any bus set up without internal pull-ups (`i2c_master.c`). **Stage 5 passes** | | |
| 2026-11-16 | 4 | Two of the seven rail labels, 5V MOD and −12V, are printed where J201's shroud sits, on the outward face. Their test points are clear of it, so David found them by elimination | | Keep every label clear of every part's body on its face, shrouded headers included |
| 2026-11-17 | 8 | The control deck built, all but the pots (arriving 18 Nov): every jack's sleeve on pad C linked to D, IN-R's pad B linked to IN-L's pad A (the normal), each pot cell's pad A bridged to D, the encoder's push pins to BTN1's pad C and to D. Pots moved to the last batch | | |
| 2026-11-17 | 8 | Batch 0, the deck ground, passes: continuity between the deck's ground bus and the board's ground | | |

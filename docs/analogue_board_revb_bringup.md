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

## Log

| Date | Stage | What happened | Bodge or change | For the next board? |
|---|---|---|---|---|
| 2026-11-16 | — | The Rev B boards arrived, with the four PCB faceplates | | |
| 2026-11-16 | 2 | J201 and the module sockets soldered; the P4 ready to fit | | |
| 2026-11-16 | 4 | Module out: +12V 11.70, −12V −11.68, +5VD 5.08, +5VA 4.98, +3V3D 3.29, 5V MOD 5.02 V, +3V3A 3.30 V. All seven in range | | |
| 2026-11-16 | 5 | P4 in, USB-C end down, rack on: 5V MOD 5.07 V against +5VD's 5.08, so Q201 carries the P4 past D203 | | |
| 2026-11-16 | 5 | USB-C to the Mac with the rack on, the P4 reset through the CH343's RTS: it boots on the board (ROM, the 32 MB PSRAM test OK, 400 MHz, chip v3.2) and runs the camera-to-HDMI app of 29 Oct, which stops at "LT8912B not found" because no display is connected. Its I2C pull-up warning is ESP-IDF's notice for any bus set up without internal pull-ups (`i2c_master.c`). **Stage 5 passes** | | |
| 2026-11-16 | 4 | Two of the seven rail labels, 5V MOD and −12V, are printed where J201's shroud sits, on the outward face. Their test points are clear of it, so David found them by elimination | | Keep every label clear of every part's body on its face, shrouded headers included |

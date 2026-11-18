# Analogue board Rev B (ESP32-P4): bring-up

The plan for the first Rev B board, with the Waveshare ESP32-P4-WIFI6 as its module (working
name Health; see [Rev B §8](analogue_board_revb.md#8-order-changes-and-the-gesture-module-2026-11-02)).
Started 2026-11-16, the day the boards arrived. It follows [Rev A's bring-up](analogue_board_bringup.md)
and keeps its rule: **one stage at a time, and stop at the first reading that is off.**

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

## Stage 6: the tests

The test program, [`firmware/analogue_board_revb_test`](../firmware/analogue_board_revb_test/main/main.cpp),
is a menu on the P4's serial console. Type a block number and Enter: the block runs and prints
PASS or FAIL, with Health's name for each channel in brackets, as in "CV1 (X1)". Nothing on the
board is driven until a block asks for it. `0` turns everything off again.

Steps 1-3 get the board running. Steps 4-8 test the deck, one batch at a time (the wires are in
stage 7). Step 9 checks the camera's and the display's ribbons. Write each step's readings in the log. At the first FAIL, stop, type `0`, and copy what
the block printed into the log.

**USB only while the rack is on:** rack on, then USB in; USB out, then rack off. With USB in and
the rack off, the P4 runs from USB and its pins feed an unpowered board.

### Step 1: meter check, rack off

Batches 1-4 are wired, so check their 18 holes before the rack goes on. Put the black lead on a
square ground hole and the red on each hole a wire goes to. Nothing should beep, except:
- SW3, SW5 and SW6, each only while its button (BTN2, BTN1, MENU) is held down;
- +3V3D, which may chirp for a moment while its capacitors charge. A steady beep is a short.

### Step 2: flash the program

Rack on, then the P4's USB-C to the Mac. From the repo:

```
cd firmware/analogue_board_revb_test
PATH="$HOME/esp/py312:/opt/homebrew/bin:$PATH" bash -c '. ~/esp/esp-idf/export.sh && idf.py -p /dev/cu.usbmodem5CF71560381 flash monitor'
```

It builds, flashes and opens the console. **Pass:** the menu prints after the reset, with no
warning under it. A warning about LDO channel 4 means the ADC and DAC won't answer, and one about
the EEPROM means the board isn't powered.

- `h` prints the menu again.
- Ctrl-] leaves the console.
- To come back later without flashing, use `monitor` in place of `flash monitor`.

Flashing replaces the camera-to-HDMI app, whose source is in `~/esp/p4_camera_hdmi`.

### Step 3: the board on its own

| Type | Pass |
|---|---|
| `1` | 0x20 (TCA9555 expander) and 0x50 (M24C64 EEPROM), nothing else; PASS |
| `2` | "32 bytes written, 0 read back wrong; the old bytes restored"; PASS |
| `4` | the range register echoes 01 and 00. With nothing patched, CV1-6 and CVI7 read about +0.20 V and AIN7 0.000 V; PASS |

### Step 4: batch 1, the encoder and buttons

| Type | Do | Pass |
|---|---|---|
| `3` | press MENU, BTN1 and BTN2 in turn, then Enter | PASS for the registers, then one line a press: SW6 (MENU push), SW5 (BTN1), SW3 (BTN2) |
| `8` | turn MENU slowly, then Enter | GIN1 (MENU A) and GIN2 (MENU B) go HIGH and low in turn, and their counts rise |
| `12` | turn MENU both ways and press it, then Enter | the detents count up one way and down the other; the press shows SW6 (MENU push) |

### Step 5: batch 2, the CV outs

| Type | Do | Pass |
|---|---|---|
| `5` | nothing patched into X1-Z2; Enter at the prompt | for each of CV1-6: within 0.2 V of −9.78 V at −10 V, 0.00 V at 0 V and +9.79 V at +10 V (the ADC reads 2 % low through its 2 kΩ); switch off about +0.20 V; PASS |
| `c N 5`, `c N -5` | the meter on jack N's tip, for each jack | about +5 V, then −5 V, close to the figure the ADC prints |
| `0` | | the jack released |

N for each jack: X1 1, Y2 2, X2 3, Z1 4, Y1 5, Z2 6.

### Step 6: batch 3, the gate ins

| Type | Do | Pass |
|---|---|---|
| `8` | a rack clock into RST, then into CLK; Enter | GIN3 (RST), then GIN4 (CLK), counts once a pulse |
| `8t 3` | a cable from X1 into RST; Enter at the prompt | high at about 1.98 V rising, low at about 1.67 V falling; PASS |
| `8t 4` | the same cable into CLK | the same |

### Step 7: batch 4, audio

| Type | Do | Pass |
|---|---|---|
| `6` | | "The codec is sending samples." |
| `10` | listen to OUT-L and OUT-R through the rack | a 440 Hz sine on both |
| | first prompt: OUT-L into IN-L, OUT-R into IN-R; Enter | IN-L and IN-R 8-12 Vpp each, both inverted; two PASSes |
| | second prompt: pull the cable out of IN-R; Enter | both inputs above 8 Vpp, IN-R through the normal; PASS |
| | third prompt: put it back (OUT-R is now silent); Enter | IN-L above 8 Vpp, IN-R under 0.5 Vpp; PASS |
| `a 5`, `a -5` | the meter on OUT-L's and OUT-R's tips, DC volts | about +5 V, then −5 V |
| `0` | | the outs silent |

### Step 8: batch 5, the pots

When they arrive (18 Nov):
1. USB out, rack off. Wire X, Y and Z (stage 7, batch 5).
2. Meter check on POT4, POT2, POT6 and the three POT_REF holes, with each pot turned fully
   clockwise: no beep. Turned anticlockwise, a wiper meets the pot's ground end and beeps.
3. Rack on, then USB in, and the console with `monitor` (step 2).

| Type | Do | Pass |
|---|---|---|
| `9` | turn X, Y and Z in turn, end to end; Enter | POT4 (X), POT2 (Y) and POT6 (Z) each sweep from 0 to about 4090 |

### Step 9: the camera and the display

The OV5647 camera is on the P4's CAMERA socket. The Olimex MIPI-HDMI is on DISPLAY, with the
TLQ-SCREEN on its HDMI lead. Both ribbons carry 3V3, ground and the P4 board's own I2C (GPIO7 and
GPIO8), so a chip answering there shows its ribbon's power and I2C work. Block 15 only reads: it
sends no video. That matters for the TLQ-SCREEN, which must only ever get its own 720×720p60. The
MIPI lanes are a later test.

| Type | Pass |
|---|---|
| `15` | the camera's chip ID 56 47; the LT8912B's 12 B2, at all three of its addresses; the screen's EDID whole, maker APF, 720×720, 812×802 total, 39.07 MHz. Three PASS lines |

The menu's other blocks are for parts Health doesn't use: `5 7` (CVO7 into CVI7), `7` (gate outs),
`11` (LEDs), `13` (MIDI) and `14` (screen).

## Stage 7: the control deck

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

X1–Z2 are the six two-way CV channels, set as outputs; RST and CLK are gate inputs.

**As built** (David, 2026-11-17): **the deck the other way** (JPS1 top right on the front) **and the
board upright.** 25 wires, 246 mm of hand wire, one across the board (RST). The n8synth way would
have been 243 mm. Every wire is also drawn on the [wiring map](https://claude.ai/artifact/RptmC4zktQrcPzZHXxPau4),
which opens Health on this fit (a copy is kept at
[`analogue_board_bringup/wiring_map.html`](analogue_board_bringup/wiring_map.html)).

**Wires from the strips**, each from the strip's inner hole level with the pad to the hole named.
Channel numbers are firmware labels: each wire took the nearest free hole of its kind, so they
differ from the brief's (Rev B §8), and Health's firmware maps by this table.

| Cell | Part | Pad | Hole | Length |
|---|---|---|---|---|
| JPS7 | deck ground (Z1's sleeve pad) | C | GND (LO 19), square | 3 mm |
| JPS3 | MENU A | A | GIN1 (R 18) | 43 mm |
| JPS3 | MENU common | B | +3V3D (RSI 15) | 33 mm |
| JPS3 | MENU B | C | GIN2 (R 21) | 46 mm |
| JPS2 | MENU push, through BTN1's free pad | C | SW6 (LO 9) | 8 mm |
| JPS2 | BTN1 | B | SW5 (LO 6) | 4 mm |
| JPS1 | BTN2 | B | SW3 (LO 3) | 4 mm |
| JPS9 | X1 | A | CV1 (R 17) | 3 mm |
| JPS8 | Y1 | A | CV5 (LO 20) | 3 mm |
| JPS7 | Z1 | A | CV4 (LO 17) | 3 mm |
| JPS12 | X2 | A | CV3 (R 23) | 3 mm |
| JPS11 | Y2 | A | CV2 (R 20) | 3 mm |
| JPS10 | Z2 | A | CV6 (LO 23) | 3 mm |
| JPS14 | RST | A | GIN3 (R 24) | 47 mm, across |
| JPS17 | CLK | A | GIN4 (R 33) | 6 mm |
| JPS15 | IN-L | A | AIN1 (R 32) | 3 mm |
| JPS18 | IN-R | A | AIN2 (R 38) | 3 mm |
| JPS13 | OUT-L | A | AOUT1 (LO 34) | 6 mm |
| JPS16 | OUT-R | A | AOUT2 (LO 38) | 3 mm |
| JPS6 | X top | C | POT_REF (R 7) | 6 mm |
| JPS6 | X wiper | B | POT4 (R 8) | 3 mm |
| JPS5 | Y top | C | POT_REF (R 4) | 6 mm |
| JPS5 | Y wiper | B | POT2 (R 5) | 3 mm |
| JPS4 | Z top | C | POT_REF (LO 7) | 6 mm |
| JPS4 | Z wiper | B | POT6 (LO 8) | 3 mm |

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

**Wire it in batches, and test each before the next**, as on Rev A: a meter check with the rack
off, then the batch's step in stage 6. Batches 0-4 were wired together on 2026-11-17, so stage 6
checks their holes in one go, then tests them a batch at a time, so a fault points at one batch.
**The pots are the last hardware step:** they arrive on 2026-11-18.

| Batch | Wires | Test |
|---|---|---|
| 0. Deck ground | Z1's pad C → GND (LO 19) | continuity, any jack sleeve to the board's GND (passed 2026-11-17) |
| 1. Encoder and buttons | MENU A → GIN1, B → GIN2, common → +3V3D; push → SW6, BTN1 → SW5, BTN2 → SW3 | stage 6, step 4 |
| 2. CV outs | X1 → CV1, Y1 → CV5, Z1 → CV4, X2 → CV3, Y2 → CV2, Z2 → CV6 | stage 6, step 5 |
| 3. Gate ins | RST → GIN3 (across the board), CLK → GIN4 | stage 6, step 6 |
| 4. Audio | IN-L → AIN1, IN-R → AIN2, OUT-L → AOUT1, OUT-R → AOUT2 | stage 6, step 7 |
| 5. Pots | X: top → POT_REF (R 7), wiper → POT4; Y: top → POT_REF (R 4), wiper → POT2; Z: top → POT_REF (LO 7), wiper → POT6 | stage 6, step 8 |

## Log

| Date | Stage | What happened | Bodge or change | For the next board? |
|---|---|---|---|---|
| 2026-11-16 | — | The Rev B boards arrived, with the four PCB faceplates | | |
| 2026-11-16 | 2 | J201 and the module sockets soldered; the P4 ready to fit | | |
| 2026-11-16 | 4 | Module out: +12V 11.70, −12V −11.68, +5VD 5.08, +5VA 4.98, +3V3D 3.29, 5V MOD 5.02 V, +3V3A 3.30 V. All seven in range | | |
| 2026-11-16 | 5 | P4 in, USB-C end down, rack on: 5V MOD 5.07 V against +5VD's 5.08, so Q201 carries the P4 past D203 | | |
| 2026-11-16 | 5 | USB-C to the Mac with the rack on, the P4 reset through the CH343's RTS: it boots on the board (ROM, the 32 MB PSRAM test OK, 400 MHz, chip v3.2) and runs the camera-to-HDMI app of 29 Oct, which stops at "LT8912B not found" because no display is connected. Its I2C pull-up warning is ESP-IDF's notice for any bus set up without internal pull-ups (`i2c_master.c`). **Stage 5 passes** | | |
| 2026-11-16 | 4 | Two of the seven rail labels, 5V MOD and −12V, are printed where J201's shroud sits, on the outward face. Their test points are clear of it, so David found them by elimination | | Keep every label clear of every part's body on its face, shrouded headers included |
| 2026-11-17 | 7 | The control deck built, all but the pots (arriving 18 Nov): every jack's sleeve on pad C linked to D, IN-R's pad B linked to IN-L's pad A (the normal), each pot cell's pad A bridged to D, the encoder's push pins to BTN1's pad C and to D. Pots moved to the last batch | | |
| 2026-11-17 | 7 | Batch 0, the deck ground, passes: continuity between the deck's ground bus and the board's ground | | |
| 2026-11-17 | 7 | Batches 1-4 wired, the deck built the other way and the board upright: 18 wires, all but the pots' six. Their tests wait for the stage 6 program | | |
| 2026-11-18 | 6 | The test program written (`firmware/analogue_board_revb_test`) and built clean on ESP-IDF 5.5.4; not yet flashed | | |
| 2026-11-18 | 6 | Step 2: flashed from the Mac, rack on. The menu prints with no warning, once the program was set to the P4's 32 MB flash (it had said 16 MB, and the boot warned) | | |
| 2026-11-18 | 6 | Step 3: block 1 finds 0x20 and 0x50 and nothing else, PASS; block 2, 32 bytes, 0 wrong, restored, PASS. Block 4 first **FAILED**: the ADS8688 echoed 01 as 02, every reply one bit early. It changes SDO on the falling edge with a 10 ns hold, and the P4 samples after that (`analogue_board_esp32p4.md`, Soft problems). With the reply read one bit early: 256 of 256 patterns at 1, 4, 8 and 16 MHz (block 4s), and block 4 PASS: the range register echoes 01 and 00, CV1-6 and CVI7 read +0.204 to +0.207 V open, AIN7 0.000 V. **Step 3 passes** | Firmware: the ADS8688's reply read one bit early | Any P4 firmware for this board reads it the same way |
| 2026-11-18 | 6 | Step 4, first try: block 3's registers PASS and the MENU push shows on SW6, but BTN1 and BTN2 show nothing: neither cell's pad A was linked to D, so a press connected its SW line to nothing | BTN1's and BTN2's pad A linked to D (David) | Check each button cell's A-D link with the meter before power |
| 2026-11-18 | 7 | Batch 5 wired: the pots in, X, Y and Z to POT4, POT2 and POT6 and their tops to POT_REF. Meter check (David): SW5 and SW3 beep to ground only while BTN1 and BTN2 are held; each wiper beeps at one end of its travel only; no POT_REF hole beeps | | |
| 2026-11-18 | 6 | Step 4: block 3, MENU push on SW6, BTN1 on SW5, BTN2 on SW3. Block 8: turning MENU steps GIN1 and GIN2 in turn (GIN2 bounces: 13 rises to GIN1's 6). Block 12: five clicks clockwise to −20, five back to exactly 0, 4 counts a click; the push shows on SW6. Clockwise counts down. **Step 4 passes** | | Health's firmware: flip the encoder's sign |
| 2026-11-18 | 6 | Step 5: block 5 PASS on all six, worst error −63 mV (CV3), switches off +0.204 to +0.207 V. Held +1 to +6 V on X1, Y1, Z1, X2, Y2, Z2, the meter read 0.98, 1.96, 2.93, 3.94, 4.89, 5.88 V (the ADC 0.982, 1.969, 2.946, 3.955, 4.926, 5.911); held −1 to −6 V, −0.98, −1.96, −2.96, −3.95, −4.91, −5.89 (the ADC −0.994, −1.980, −2.983, −3.992, −4.946, −5.937). Every jack on its own channel, within 1 % of the ADC. **Step 5 passes** | | |
| 2026-11-18 | 6 | Step 6: a rack clock (about 3.6 Hz) counted on GIN3 from RST, then on GIN4 from CLK. `8t 3` and `8t 4`, X1 into RST then CLK: high at 2.00 V rising, low at 1.64 V falling, both (design 1.98 and 1.67). **Step 6 passes** | | |
| 2026-11-18 | 6 | Step 7: block 6, the codec sends samples (ESP-IDF warns that the second I2S channel takes the APLL at 24 575 996 Hz for 24 576 000: harmless). Block 10: the sine heard on both outs (David's meter reads no AC at 440 Hz); OUT-L into IN-L 9.9 Vpp, OUT-R into IN-R 10.2 Vpp, both inverted; IN-R empty, it hears IN-L's cable at 9.9 Vpp through the normal; the silent OUT-R back in IN-R, 0.0 Vpp. `a 5`, `a -5`, `a 0`: OUT-L +5.08, −5.03, +0.02 V; OUT-R +5.01, −5.29, −0.14 V. OUT-R's −140 mV offset is within the level shift's resistor tolerance, for calibration. **Step 7 passes** | | |
| 2026-11-18 | 6 | Step 8: block 9, X, Y and Z sweep 0 to 4089 on POT4, POT2 and POT6; POT1, 3 and 5 and CH6-7 stay at 0. **Step 8 passes, and with it stage 6: Health's board and deck pass every test** | | |
| 2026-11-18 | 6 | Plugged back in: step 3 passes again (CV1-6 and CVI7 +0.204 to +0.207 V open). Step 9, new block 15: the camera reads 56 47 (OV5647); the bridge 12 B2 (LT8912B) at 0x48, 0x49 and 0x4A; the TLQ-SCREEN's EDID whole, maker APF, product AA61, "720x720 CVT", 720×720, 812×802, 39.07 MHz, as apf's `edid_720r2.bin`. Also answering, not identified: 0x4B, and 0x51 to 0x57 (the capture card in October gave only 0x50). The ES8311 at 0x18. **Step 9 passes: both ribbons' power and I2C work; the lanes are not tested yet** | | |

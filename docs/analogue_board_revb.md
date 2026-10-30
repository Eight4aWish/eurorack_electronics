# Analogue board Rev B: planning notes

Started 2026-10-23, while the Teensy board (Rev A, ordered 2026-10-16) is being made. These are
changes for Rev B, and for the Pico board, which has not been ordered yet, so its changes can go
in before its first order. Nothing here is decided unless it says so.

**Status, 2026-10-26: generated and fully routed.** The generator builds Rev B as its own board,
`pico_revb` (`python3 tools/analogue_board/build.py pico_revb`, then `pcb.py pico_revb`); the
Rev A boards build unchanged. The routed board is
`hardware/analogue_board/pico_revb/routed_trial/`. It has:
- 0 unconnected and 0 copper faults;
- every IC supply pin within 4 mm of a capacitor by track;
- the silkscreen block labels.

How it got there is in `docs/analogue_board_journal.md`, chapter 14. Order files wait for the
Teensy board's bring-up (§7).

## 1. ESP32-P4: separate I2C buses [decided, option C, 2026-10-25; carried out by the pin map in section 3]

**The problem.** On the Waveshare ESP32-P4-WIFI6, GPIO8 (SCL) and GPIO7 (SDA) are the board's
own I2C bus. They reach the header at pins 16 and 17. That bus configures:
- the camera connector (J1): a MIPI camera cannot work without it;
- the display connector (J2): touch needs it, and on many Pi-style panels so do power-up and
  backlight;
- the on-board ES8311 codec.

Rev A puts SPIB_MISO (pots ADC data) and CS_595 (the 74HCT595 latch) on pins 16 and 17. The MIPI
lanes, microSD, Wi-Fi (the C6, over SDIO), the ES8311's audio (GPIO9-13) and the USB-OTG port
use no header pins, so they are unaffected. Source: Waveshare schematic
(`docs/analogue_board_esp32p4.md`, Sources).

**Options.**
- **A. Share in firmware, no board change.** Use I2C on pins 16/17 between pot reads, and re-send
  the gate states after every pot read, so a stray latch pulse copies the same data. Untested
  and fiddly.
- **B. One shared bus.** Move our I2C (TCA9555 at 0x20, M24C64 at 0x50, display holes at
  0x3C/0x3D) onto pins 16/17. Nothing is lost, but:
  - the Pico must run that I2C on PIO, because its hardware I2C has SDA and SCL the other way
    round on those pins;
  - our pull-ups and the Waveshare's in parallel come to 1.1 kΩ, right at I2C's 3 mA limit;
  - a fault on the camera or screen side can stall the switches and gate-enable expander.
- **C. Separate buses (David's preference).** Leave pins 16/17 to the P4 alone:
  - CS_595 moves to pin 20 (GP15; GPIO25 on the P4). Pin 20 has been free since jack detect
    was dropped (2026-10-16).
  - SPIB_MISO (pots ADC data) moves to pin 11, freed by dropping EXP_INT (section 3).
  - Pins 16/17 go to two wiring holes, P4_SCL and P4_SDA. They are reserved for the P4's own I2C
    on every board, whichever module is fitted, and never used for anything else. They let an
    extra I2C part join that bus.
  - The P4 runs the two buses on its two hardware I2C controllers at once.
- **Not an option: the pots ADC on the converter bus.** Claude proposed this on 2026-10-23 and
  withdrew it on 2026-10-25. The spec (§6.1) gives the converter bus to the CV ADC and DAC alone,
  so that six CV channels each way run at about 41 kHz, audio-rate CV. The MCP3208 manages at most
  1 MHz at 3.3 V, so each pot read would block the converters for about 24 µs, a whole CV sample
  period, hundreds of times a second.

**P4 pin 20 at boot.** On the P4, pin 20 has the USB pull-up until firmware claims it, so the 595
latch sits high at boot. The gate outputs stay off, because GATE_OE_N powers up high from the
TCA9555.

**Scope.** The Pico 2 / ESP32-P4 board's pin map (section 3). The Teensy board stays at Rev A.

## 2. Panel first: panel, then wiring holes, then chips [approach agreed, David 2026-10-25]

Rev A packed the wiring banks to suit routing. The mix, shape, ground slot and position all
differ between banks, and between the two boards, and deck cells 13-18 (positions 32-40) have no
channel holes beside them. Rev B starts from the panel instead. Two private pages in David's
claude.ai gallery hold the detail: "Analogue Board Wiring Map" (Rev A, every hole against the deck
cells) and "Rev B Panel Plan" (the mock-up below).

**David's rules (2026-10-25):**
- (a) 10HP only. 6HP need not be considered, which frees space.
- (b) Pots, buttons and screen connections mostly in the top half.
- (c) Jacks next.
- (d) Audio near the bottom: ins on the PCB's right, so they appear on the panel's left edge, and
  outs the other way.
- (e) About the same number of connections on each side.
- (f) Other things, such as MIDI, slot into the gaps.

**Deck orientation.** The deck is double-sided and David has fitted it both ways round; either is
fine as long as pots are available on both sides. Fitted the n8synth way (JPS1 top left on the
front), the deck's left strip (JPS1, 2, 4, 7, 8, 10, 13, 14, 16) meets the PCB's right-hand strip
(J902) as seen from the module side. The n8synth file's rear view of the deck shows it. Rev A's
net names are the other way round (DECK_L is J901), which is harmless electrically.

**The mock-up** (patch.Init()-style; patch.Init() itself has 20 panel parts, 2 too many for 18
cells):

| Rows | Panel left | Middle | Panel right |
|---|---|---|---|
| 1 | POT 1 | button | POT 2 |
| 2 | POT 3 | toggle | POT 4 |
| 3 | CV in 1 | CV in 2 | CV out 1 |
| 4 | gate in 1 | CV out 2 | gate out 1 |
| 5 | audio in L | gate in 2 | audio out L |
| 6 | audio in R | gate out 2 | audio out R |

The middle column alternates strips row by row: rows 1, 3 and 5 reach the panel-left strip,
rows 2, 4 and 6 the right. So every input reaches the panel-left strip and every output the
right, with 9 cells and 11 signal wires on each side.

**What it implies:**
- **Holes level with the pads.** One channel hole level with each signal pad: each cell's A pad
  (positions 1, 4, 7, 17, 20, 23, 32, 35, 38), and B for a pot's wiper. Every panel wire becomes
  a short sideways hop. Pots and switches go on both sides of the top band, so either deck
  orientation works.
- **Chip zones follow the bands.** Pots ADC, pot reference and switch expander at the top. CV
  channels in the middle, two per side (they are switchable, so each side holds whole channels).
  Gate inputs on the PCB right; gate outputs and the 595 on the PCB left. Codec at the bottom
  centre, inputs right, outputs left.
- **The power header must move.** On Rev A it sits at positions 33-37 beside the PCB's right
  strip, where the audio-in holes need to go.
- **Utility holes in the gap rows** 10-16 and 26-31: screen I2C and LEDs in the top gap, MIDI
  and gate expansion in the lower one.
- **MIDI variant.** Swap the middle CV pair: MIDI in for CV in 2, MIDI out for CV out 2.
- **Trim?** The board offers up to 35 panel parts, about twice what 18 cells can show. The
  mock-up uses 4 of 6 pots, 2 of 9 switch inputs, 2 of 4 gates each way and 4 of 6 CV channels.
  Trimming towards one deck's worth would free board space and module pins. Open question.

**Channel set [proposal, 2026-10-25].** Start from patch.Init() and add only what a spare channel
on a chip already in that block's zone can give. Each addition is then a few passives and a short
local trace.

| Block (cells) | From patch.Init() | Added | Chip in the zone |
|---|---|---|---|
| Top, panel left (JPS1, 2, 4) | 2 pots, button | 1 pot; a switch hole beside every cell | MCP3208 (6 of 8), TCA9555 |
| Top, panel right (JPS3, 5, 6) | 2 pots, toggle | 1 pot; a switch hole beside every cell | same chips |
| Middle, panel left (JPS7, 8, 10) | 3 CV in, 1 gate in | the 3 CV jacks become two-way (CV1-3); 2 gate in | ADS8688 and DAC8568, a DG412, two LM393 |
| Middle, panel right (JPS9, 11, 12) | 1 CV out, 1 gate out | 2 more CV, all three two-way (CV4-6); 2 gate out | DAC8568 and ADS8688, a DG412, one quad op-amp, 74HCT595 (4 of 8) |
| Bottom, panel left (JPS13, 14, 16) | audio in L/R, 1 CV in, 1 gate in | MIDI in; the CV in is fixed (CVI7) | codec inputs, ADS8688 (7 of 8), MIDI receiver |
| Bottom, panel right (JPS15, 17, 18) | audio out L/R, 1 gate out | 1 fixed CV out (CVO7), MIDI out | codec outputs, DAC8568 (7 of 8), MIDI driver |

Totals: 6 pots and 6 switch inputs; 6 two-way CV plus one fixed CV each way; 4 gate in and 4
gate out; stereo audio in and out; TRS MIDI in and out. That is 34 panel channels against Rev A's
35.

How the holes are laid out (as built, 2026-10-26; `wiring.PLAN_REVB`):
- **One column each side,** next to the strip, mirrored left to right. A cell spans three strip
  positions, so its holes take those three rows. David, 2026-10-26: a second column (the first
  pass) only crowded the module's lanes.
- **Top cells.** POT_REF on the A row, the pot wiper on the B row, a switch on the C row, so
  each cell can be a pot or a switch. A part in cell JPS*n* uses POT*n* or SW*n*. Ground at
  position 10.
- **Middle cells.** A CV hole on the A row and a gate hole on the B row.
- **Utility holes in the strips' empty positions:** WS2812, codec reset and the MIDI links on
  the left strip; the P4's I2C, the display's I2C and the gate expansion on the right strip.

**Two-way CV kept [David, 2026-10-25].** The six channels stay as on Rev A. Put one DG412 in each
middle block so each side's three switches sit beside its holes. Their SW_EN lines come from the
expander at the top, about 30 mm away; a second 595 beside the switches would make them local.

**Switch inputs, 9 to 6.** The expander keeps three spare lines.

**Limits and headroom.** Gate inputs stay at 4: each costs a module pin, and the Rev B map has
none to spare (section 3). Headroom with no new chips: +1 CV in and +1 CV out (the converters'
eighth channels), +2 pots, +4 gate outs, +3 switches.

**Screen [David, 2026-10-25].** It mounts in the front panel, and a panel with one leaves the
cells it covers empty. Its I2C holes go in the top gap rows.

## 3. Module, pins and power [decided 2026-10-25]

Rev B is the Pico 2 / ESP32-P4 board; the Teensy board stays at Rev A. The module sits in the
middle of the board.

**USB end down.**
- **Antenna.** The P4's antenna end reaches 16.9 mm past the Pico footprint (Waveshare drawing).
  It points up, over the low-profile top zone and towards the top edge, away from the audio at the
  bottom.
- **Pins meet their circuits.** Power, I2S and MIDI pins sit at the bottom, by the power header,
  codec and MIDI circuits. Both SPI buses' pins sit at the top, by the converters and the pots ADC.
  The gate-input pins face the panel-left side, where the gate inputs are. Only I2C (pins 4, 5)
  has to run up to the expander.
- **The USB plug** runs down over the bottom zone, so parts there stay low.
- **Camera and display ribbons.** The P4's two FPC connectors are mid-module on its top face, and
  the ribbons route over the board as needed (David, 2026-10-25). They don't constrain the
  orientation.

**Pin map** (Rev A → Rev B; Pico 2 GPIO / P4 GPIO):

| Pin | Pico 2 | P4 | Rev A | Rev B |
|---|---|---|---|---|
| 6 | GP4 | GPIO29 | EXP_INT | GATE_IN3 |
| 11 | GP8 | GPIO5 | GATE_IN3 | SPIB_MISO (the Pico's other SPI1 data-in pin) |
| 16, 17 | GP12, GP13 | GPIO8, 7 (P4 board I2C) | SPIB_MISO, CS_595 | two holes, P4_SCL and P4_SDA: reserved for the P4's I2C |
| 20 | GP15 | GPIO25 | unused | CS_595 |
| 21 | GP16 | GPIO48 (VDD_IO_5) | SPIA_MISO | CS_DAC |
| 26 | GP20 | GPIO32 | CS_DAC | SPIA_MISO (Pico SPI0 RX) |

Everything else stays as on Rev A, including both SPI buses (§6.1): MIDI on pins 1 and 2 by link,
I2C on 4 and 5, LED_DATA, GATE_IN1, 2 and 4, SPIB SCK and MOSI on 14 and 15, CS_POT, CS_ADC,
SPIA SCK and MOSI, and I2S.

What the map changes:
- **EXP_INT is dropped [agreed, David 2026-10-25].** Pins 16 and 17 go to the P4, pin 20 takes CS_595,
  and that leaves one function short. The firmware would poll the TCA9555 for button changes
  instead. The spec already treats polling as the backstop, and with a screen on the same I2C bus,
  a read can wait 23 ms either way. Polling at 200 Hz uses about 4 % of the bus. The other ways
  to find a pin cost more: give up gate input 3, or put the pots ADC on the converter bus (see
  section 1).
- **Gate inputs move.** Gate inputs are now on GP4, 6, 7 and 9, no longer four consecutive pins.
  Edge interrupts don't mind; a PIO capture reads the window GP4-9.
- **The P4's programmable bank.** Pins 21, 22 and 24 now carry only signals the module drives, so
  a bank left off or at 1.8 V can no longer have 3.3 V forced into it. The converters still need
  the one-line LDO fix before they work. The pots ADC and the 595 stay on 3.3 V banks.
- **No pins are left free.**

**Power header in the lower gap** (David's suggestion):
- **Placement.** It goes on the PCB's left, the outputs side, next to the module's power pins (36,
  39, 40) and away from the audio inputs.
- **Fit.** A keyed 2×5 shroud is 20 mm long, longer than the six gap rows. It stands just inside
  the strip (pins at x 9.0 and 11.54 mm) and covers that side's hole columns from position 25 to 32.
  - That side's middle ground hole moves to position 24.
  - Its first bottom cell's holes move to position 34.
  - Wires to the strip's inner holes at 25, 31 and 32 there run on the deck face.
  - The module sits 1 mm right of centre to clear it.
- **P4 supply.** The Q201 bypass and the module's 5 V feed (at least 4.5 V at up to 0.7 A) sit
  between the header and pin 39.
## 4. Silkscreen [done for Rev B, 2026-10-26]

- **Block labels.** Every wiring block on the routed Rev B board has a label but W12, a lone ground
  hole (square, so it reads as ground anyway). On Rev A, W8 on the Teensy board and W6 and W8 on
  the Pico board have none.
- **Wiring map wording.** `wiring_map.md` now says "no room for a label" and names the strips.
- **Test points.** 3 of 9 test points have a name beside them; the rest have no room. Rev A showed
  that is not enough (§7): every one needs its name, at 1.0 mm or more. **Open.**
- **Board marking [open, from Rev A, 2026-10-30].** A silkscreen line with the board name and
  revision, "Eight4aWish" and "CC BY-SA 4.0", at 1.0 mm or more. Rev A has none of it.

## 5. Footprints

- **U1002 (H11L1) [done, 2026-10-26].** `parts.py` now has `SMDIP-6_W9.53mm`, matching LCSC
  C20082. On the Teensy board, JLC left it off and a through-hole H11L1 goes in by hand.
- **Idea:** an automatic check of every footprint against LCSC's own (EasyEDA) footprint,
  through easyeda2kicad.

## 6. Carried over from the P4 review

- **MOD_5V margin.** MOD_5V is about 4.6 V after the Schottky, against the MP1658's 4.5 V
  minimum. Raise +5VD to about 5.2 V or use a lower-drop diode.
- **P4 doc out of date.** `docs/analogue_board_esp32p4.md` still lists pin 20 as PROBE (it is
  unconnected) and does not mention the camera and display I2C. Update it when item 1 is
  decided.

## 7. Lessons from the Teensy bring-up

The boards arrived 2026-10-30. The log in [analogue_board_bringup.md](analogue_board_bringup.md)
is the source; what it has said so far:

- **Test points need one name, on the board and in the docs.** Rev A prints a short net name
  ("5V MOD") beside 15 of its 27 test points, at 0.8 mm, under JLC's 1.0 mm / 0.15 mm; 12 had no
  room. The bring-up plan calls them TP201 to TP703, numbers the board never shows, so they could
  not be found. Rev B: a name beside every test point at 1.0 mm or more, and the plan uses it.
- **No maker's mark.** Rev A's silkscreen has no Eight4aWish name and no CC BY-SA 4.0 notice; both
  are only in the KiCad title blocks. Rev B gets a line with the board name, revision, Eight4aWish
  and the licence (see §4).
- **No test point under the module.** TP206 (+5VA), TP401 and TP601 sit inside the Teensy's
  socket; TP605 and TP702 at its ends.
- **Finish.** OSP was chosen over ENIG on cost, and solders well. It leaves the wiring holes
  bare copper with a shelf life of months. HASL tins them, if JLC offers it for the board.
- **The power and the core blocks worked first time.** Every rail in range; I2C, EEPROM,
  expander, ADC, and DAC through all six switches pass, the DAC within 34 mV of the design
  uncalibrated. No bodges yet.

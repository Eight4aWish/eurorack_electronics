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
channel holes beside them. Rev B starts from the panel instead. Two pages hold the detail; they
began as private claude.ai pages, and copies are kept in the repo so they can't be lost:
- [Analogue Board Wiring Map](analogue_board_bringup/wiring_map.html): Rev A, every hole against
  the deck cells;
- [Rev B Panel Plan](analogue_board_revb/panel_plan.html): the mock-up below.

Open either file in a browser.

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
- **Test points [done in the generator, 2026-11-03; §8].** 3 of 9 test points had a name beside
  them; the rest had no room. Rev A showed that is not enough (§7): every one needs its name, at
  1.0 mm or more. Now all 7 have one.
- **Board marking [done in the generator, 2026-11-03].** A silkscreen line with the board name and
  revision, "Eight4aWish" and "CC BY-SA 4.0", at 1.0 mm or more (`labels.py`). Rev A has none of it.

## 5. Footprints

- **U1002 (H11L1) [done, 2026-10-26].** `parts.py` now has `SMDIP-6_W9.53mm`, matching LCSC
  C20082. On the Teensy board, JLC left it off and a through-hole H11L1 goes in by hand.
  - **Checked against LCSC's own footprint (2026-11-03,** through easyeda2kicad): its pad rows
    sit 9.34 mm apart against KiCad's 9.53 mm, and KiCad's larger pads cover LCSC's.
  - **Its rotation was the remaining fault.** LCSC draws the part with its pins in rows and
    pin 1 bottom left; KiCad's SMDIP has them in columns, pin 1 top left, as with SOIC. `fab.py`
    had no offset for SMDIP, so the CPL would have turned it 90°. It now adds 270°, as for SOIC:
    U1002 goes to JLC at 0°. Check pin 1 in JLC's placement preview all the same.
- **Every part against LCSC's own footprint [done, 2026-11-03]** (`diag/lcsc_footprints.py`, on
  the 59 part types JLC places):
  - **Rotation:** for every part, `fab.py`'s offset is the one LCSC's drawing needs, the H11L1
    included once SMDIP's offset went in.
  - **Pads:** the counts match everywhere, and the numbering on every polarised part (pin 1,
    cathodes, transistor legs).
  - **Nine flags, all small geometry:**
    - SOT-23 ×4 and SOIC ×2: LCSC's pads are shorter than KiCad's and sit inside them, 0.3-0.4 mm
      off-centre along the pad;
    - SOD-323 ×2: KiCad's pads are larger;
    - the L78M05's DPAK: LCSC calls the tab pad 4 where KiCad calls it 2, the same tab in the
      same place.
  - **Proven on Rev A:** each flagged part was assembled there and worked, except Q201
    (AO3401A). Q201 shares SOT-23 and its rule with parts that were, and its pads were compared
    by hand.
  - **Re-run after the output-resistor change (2026-11-03):** the ERJ-P08 (C4261071) matches
    LCSC's footprint, pads within 0.02 mm and no rotation offset; the same nine flags otherwise.

## 6. Carried over from the P4 review

- **MOD_5V margin [settled].** MOD_5V is about 4.6 V after the Schottky, against the MP1658's
  4.5 V minimum. Q201 already answers it (spec §15, decided 2026-10-15): with JP201 bridged, the
  FET bypasses the Schottky. Fit a P4 with JP201 bridged.
- **P4 doc [done, 2026-11-02].** `docs/analogue_board_esp32p4.md` now has Rev B's pin table,
  read from the routed board, and Rev B notes on each finding.

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
- **MIDI on link holes [settled 2026-11-02: wired straight, §8].** The module's two
  serial pins (Pico GP0/GP1, Teensy 1/0) reach MIDI only through J101's links, so every MIDI build
  needs a jumper first (Boy links SPARE2 to MIDI_RX). They became link holes because they were
  promised as spare GPIO on 14 October, before TRS MIDI came back on the 15th. The alternative:
  wire them to MIDI through solder jumpers that come closed. MIDI then works as delivered, and
  cutting a track frees a pin, with J101's holes kept as taps.

  The case for it: the board has other expansion routes, so the spares are rarely needed. These
  routes are the I2C holes (J703), the gate-expansion holes (J603), the LED holes (J704), the
  expander's spare switch lines and the pot ADC. The spares are the board's only fast direct
  processor pins, and their likeliest use is serial, which MIDI already is.

## 8. Order changes and the gesture module (2026-11-02)

**Decided by David, 2026-11-02 and 03; in the generator from 2026-11-03** (`variant.py`:
`midi_direct`, `cv_volts`, and `gate_exp` dropped). The build is clean: 363 parts, 0 ERC,
netlist or datasheet problems.
- **MIDI wired straight to the module,** with no link holes and no solder jumpers: pin 1 (GP0,
  UART0 TX) to MIDI_TX, pin 2 (GP1, UART0 RX) to MIDI_RX. J101 keeps only RUN and GND. The
  board has no spare GPIO left.
- **The gate expansion goes.** J603 (QH′, SRCLK, RCLK, OE, +5VD, GND) is removed. The 595 keeps
  its four gate outputs; QE-QH and QH′ are left unused.
- **CV outputs at ±10 V** (David, 2026-11-03: "the full -10 to 10V"), spec §15's variant: Rf
  75k (the 0603 75k already on the board, C23242, so no new part type), divider 15k/20k. Gain
  8.5, OFFSET_REF 1.429 V, −10.71 to +10.54 V, 0 V at code ≈ 33044. The 100 pF across Rf now
  puts the stage's pole at 21 kHz. It needs loads of 10 kΩ or more.
- **The nine 1 kΩ output resistors take 0.66 W** (David, 2026-11-03): R321 and R328 (audio
  out), R406-R426 (CV1-6) and R517 (CVO7) are Panasonic's anti-surge ERJ-P08F1001V, C4261071
  (Extended, $0.018), in place of the 0.25 W 1206 C4410. At ±10 V an output patched into a
  stiff one puts up to ≈0.5 W in them (`analogue_board_review/cv_in.md`, A2's correction).
  The footprint is the same 1206, so the routing stands: the gerbers are unchanged, and only
  the BOM line moves. JLC part types stay 59, one more of them Extended.

**Placement moved.** Without J603 and four of J101's holes, the auto-placer packs the passives
differently: 114 parts sit elsewhere than on vB, under the same rules. The committed generator
still reproduces vB exactly, so the change is this one. vB's six-layer route no longer
applies, and six layers is being routed again beside four (rC1).

**34 channels for 18 cells [proposal].** The 34 are not 16 parts too many. Each cell offers a
choice, and the chips behind the choices are shared:
- top band: each of the 6 cells is a pot or a switch (12 channels);
- middle band: each of the 6 cells is a two-way CV or a gate (12);
- bottom band: the 6 cells choose from the 4 audio jacks, a fourth gate each way, the fixed CVs
  and MIDI (10).

A choice costs a hole and a short trace; the chips are what fill the board. The gesture module
below uses nearly every chip, MIDI being optional. The two-way switching is what gives it six
outputs. So the proposal is to keep the set, route on four layers as it stands (less J603 and
the MIDI links), and, if that fails, trim where the router's leftovers point. On Rev A they were
rails around the converters and the switches, not channel holes.

**The gesture module's interface [proposal].** It drives the Befaco Oneiroi, which takes (user
manual):
- 17 CV inputs: 9 primary ones at −5 to +10 V, plus V/oct and 8 level and dry/wet inputs at 0 to
  10 V;
- 3 gate inputs, sync, record and random, high above 1 V;
- no MIDI.

On the P4, Espressif's esp-dl has a hand detector (a box per hand: x, y and size) and a gesture
classifier (about 30 ms per hand).

**The camera is not on the panel** (David, 2026-11-03): it sits on top of the rack in a
3D-printed holder, on a ribbon long enough to reach a module in the middle of the rack, near
the TLQ-SCREEN. So it takes no cells, and the board needs no slot for it.

**Update, David 2026-11-04: Health is dropped for now.** The platform is Boy, in two versions, Boy Rev A
and Boy Rev B (this board), and gesture control is an app on Rev B, not a module of its own. The panel
below was already on order with the board, so it stays as the record of what's coming.

**The panel [decided, David 2026-11-03].** The module is **Health** ("eleven for health"). Its
PCB faceplate is `build123d/panels/p4_gesture.py`, with the order files in
`build123d/exports/pcb/p4_gesture_10hp/`, to go in the same JLC basket as this board. It uses
Boy's Rev A deck geometry, 2 mm lift included. No screen on the panel: the TLQ-SCREEN is the
display.

| Row | Panel left | Middle | Panel right |
|---|---|---|---|
| 1 | encoder (A, B on GIN1, GIN2; push SW1) | BTN1 (SW2) | BTN2 (SW3) |
| 2 | X pot (POT4) | Y pot (POT5) | Z pot (POT6) |
| 3 | X1 | Y1 | Z1 |
| 4 | X2 | Y2 | Z2 |
| 5 | IN-L (AIN1) | RST (GIN4) | OUT-L (AOUT1) |
| 6 | IN-R (AIN2) | CLK (GIN3; its wire crosses the board) | OUT-R (AOUT2) |

- Rows 3-4 are the six two-way CV channels, all set as outputs: each hand's x, y and size
  (Z). The firmware maps any feature to any channel.
- The encoder's common goes to 3.3 V digital, not POT_REF, since the panel has pots.
- Pot tops may be daisy-chained on the deck through the cells' second A contacts; Rev B
  gives every top cell its own POT_REF hole, where Rev A had one per two pots.
- SW4-SW6 stay free (the pot cells use their POT channels): two footswitches on one TRS jack
  could use them later, if a cell is given up. David left the panel as it is.
- The audio outs are DC-coupled, so OUT-L and OUT-R can also carry CV. Gates can also come
  from any CV output. With the CV outputs at ±10 V, all eight outputs reach the Oneiroi's
  full input ranges.

**The display bridge [proposal].** The TLQ-SCREEN takes a mini-HDMI (Type C) input, and its
cable runs behind the panels (apf's quick-start). The Olimex MIPI-HDMI bridge has a full-size
HDMI socket and runs off the display ribbon's own 3.3 V. Proposed: mount the Olimex behind the
TLQ-SCREEN in a printed holder, with a longer Pi 5 display ribbon (22-pin to 15-pin) from the
P4, and a short, thin HDMI lead (a flat ribbon with Type A and mini plugs) into the screen. The
gesture module stays shallow, and the board needs nothing for it.

**For the order:**
- **CV range:** ±10 V, decided above.
- **The camera's ribbon:** settled; the camera is off the panel.
- **Hand tracking, proven at the bench** with the camera and P4 alone: agreed for later
  (David, 2026-11-03).
- **The four-layer route (2026-11-03).** Six layers (rC1) routed completely on the first try:
  509 connections in stage 1, 0 open after `finish.py`. Four layers came close but did not close.
  Every leftover was in the chip stack under the module (DAC, U502, U504 and the DG412s), where
  four layers has only In2 to cross on:

  | Route | Change | Stage 1 | Stage 2 | After `finish.py` |
  |---|---|---|---|---|
  | r4L1 | none | 11 | 9 | 8 |
  | v4A | the stack's gaps 0.5 mm wider | 11 | 9 | 5 |
  | v4B | the DAC up 0.5 mm, U504 down 0.5 mm | 13 | 12 | 10 |
  | v4C | U504 0.6 mm right | 3 | 2 | 2 (CVDRV4; R414 to U402) |

  Claude's advice was six layers either way: the saving is on the bare boards only, and our
  four-layer stack has one ground plane, +5VD as tracks and no plane beside the deck face's
  signals.

**Test points [decided, David 2026-11-03].** The bus test points went on 2026-10-16, so only the
rails' are left, and the bring-up used all seven.
- **The two ground test points go** (TP203, TP204): a meter's black lead takes any of the
  field's square ground holes.
- **The seven rail test points** each aim at their rail's source in the auto-placer (the 0 Ω link
  after each regulator, the rail entry ferrite, the module supply), keep a box beside them for
  their 1.0 mm name, and may not sit under the module on the outward face (an ESP32-P4's length
  included). TP209 (MOD_5V), which sat under the module, is anchored left of it, above J201's
  shroud, about 5 mm from module pin 39. On the placed board all seven take their names, and
  the board marking fits on one line.

**Final routes (2026-11-03):**

| Route | Placement | Stage 1 | Stage 2 | After `finish.py` |
|---|---|---|---|---|
| **fA, six layers** | as the generator places it | 4 | 0 | **0**, every IC supply pin within 4 mm of a capacitor |
| fB, six layers | v4C's U504 move | 3 | 3 | 0, the same |
| fB, four layers | v4C's U504 move | 17 | 17 | 11 when stopped |

**Six layers, fA, for the order (David, 2026-11-03).** The generator reproduces its placement
exactly. It is `routed_trial/analogue_board_pico_revb_routed.kicad_pcb`:
- KiCad's DRC with schematic parity: 0 unconnected, no copper faults. The 178 notices are
  silkscreen and library ones, as vB's 184 were, and none is on a label of ours.
- The decoupling review flags only the DAC's CLR (U501 pin 9) and the 595's MR (U602 pin 10),
  logic pins tied to a rail.
- Labels: 12 of 13 wiring blocks (W12 is a lone square ground hole), all 7 test points, and
  the board marking on one line, turned, on the outward face.

**Order files:** `pico_revb/fab/`: the six-layer gerbers and drill, and the JLC BOM and CPL for
the 301 parts JLC places (132 top, 169 bottom, 59 part types, each with an LCSC number). Before
paying: a live quote, JLC's stock for every part, and its placement preview with "Confirm
Parts Placement" ticked (spec §14).

**JLC's placement preview, reviewed 2026-11-04: nothing to correct.** JLC flagged no errors.
- **Order files against the routed board:** all 301 parts match on position, face, footprint and
  LCSC number. 70 part, face and rotation combinations are the same as on Rev A, which works; none
  differs; 14 are new here (4 polarised: U1002, Q201, U602, D1002).
- **The 44 ICs, diodes and transistors on the preview:**
  - On all 33 multi-pin parts, JLC's pin 1 mark is on our pad 1.
  - On the 4 polarised two-pad diodes (D201-D203, D1002), JLC's + is on pad 2 and its − on pad 1,
    the cathode. The SMA parts' bands show at the pad 1 end.
  - The 7 PESD15VL1BA are bidirectional, and JLC draws them so.
- **Parts that looked odd and aren't:** JP201 is the grey oval, an open solder jumper JLC doesn't
  place. C203 and C710 are bright yellow but ceramic (X5R), with no polarity. L201's mark is on pad
  2, and an inductor has no polarity.
- **Limit:** the preview is about 10 pixels per mm. Body dots and bands show on the SOICs and the
  SMA diodes, and they agree with the marks. On the TSSOPs and SOD-323s only JLC's marks can be
  read.

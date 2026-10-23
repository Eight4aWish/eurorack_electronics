# Analogue board Rev B: planning notes

Started 2026-10-23, while the Teensy board (Rev A, ordered 2026-10-16) is being made. These are
changes for Rev B, and for the Pico board, which has not been ordered yet, so its changes can go
in before its first order. Nothing here is decided unless it says so.

## 1. ESP32-P4: separate I2C buses [leaning, David 2026-10-23]

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
  - The pots ADC (MCP3208) joins the converter bus (SPIA) with its own CS_POT, so SPIB_MISO
    goes. SPIB then carries only the 595 chain. The 595 then never shifts in pot traffic.
  - Pins 16/17 go to two wiring holes: spare GPIO (GP12, GP13) on a Pico, a tap onto the P4's
    own I2C on a P4.
  - Nothing is lost. The P4 runs the two buses on its two hardware I2C controllers at once.

**To check before choosing C.**
- **MCP3208 clock.** The MCP3208 tops out around 1-2 MHz against about 17 MHz for the
  converters, so each driver sets the clock per device. Each pot read holds the converter bus for
  about 25 µs.
- **Shared data line.** The ADS8688 must release SDO while it is deselected, as the MCP3208
  does.
- **P4 pin 20 at boot.** On the P4, pin 20 has the USB pull-up until firmware claims it, so the
  595 latch sits high at boot. The gate outputs stay off, because GATE_OE_N powers up high from
  the TCA9555.
- **Converter supply.** On the P4, SPIA is on the programmable supply (VDD_IO_5, hard problem 1
  in the P4 doc), so the pots depend on the same firmware fix.
- **Ribbons.** Can the camera and display ribbons leave the module once it is in its socket?
  Which camera and screen?
- **Fallback.** If the pots must stay on SPIB, SPIB_MISO can go to pin 11 (GP8, the Pico's other
  SPI1 data-in pin), at the cost of gate input 3.

**Scope.** This is a pin map change (`design.py` PINMAP), so firmware stays the same on both
boards. On the Teensy, the pots move to SPI and pin 39 (MISO1) frees up.

## 2. Wiring field: one standard bank [open]

Rev A packed the four banks to suit routing. The mix, shape, ground slot and position all differ
between banks, and between the two boards. Deck cells 13-18 (positions 32-40) have no channel
holes beside them. The colour-coded map of every hole against the deck cells is a private page
in David's claude.ai gallery ("Analogue Board Wiring Map", 2026-10-23).

Draft rules, for discussion:
- **One template.** Use one order everywhere: CV, CV, audio, gate in, pot, pot, pot reference,
  ground, gate out, switch, switch, switch. Missing channels leave their slot empty.
- **Level with the deck.** Line each bank up with a band of three deck cells (1-9, 17-25 or
  32-40).
- **Right side.** Mirror the left on the right, outer column nearest the strip. Two right
  columns cost 2.54 mm of the U501/U502/U801 lane; one right column in the same order is cheaper.
- **Both boards alike.** The same field on both boards: fix the field first, then place chips
  around it, with no per-board moves (`wiring.MOVES`).
- **Numbering.** Number channels bank by bank.
- **Utility holes.** Put utility holes in the gap rows 10-16 and 26-31, where the deck has no
  pads.

## 3. Silkscreen [to do]

- Label every wiring block. On Rev A, W8 on the Teensy board and W6 and W8 on the Pico board have
  no label, because there was no room.
- `labels.py` writes "label on the no face" in `wiring_map.md` for an unlabelled block: fix the
  wording.

## 4. Footprints [to do]

- **U1002 (H11L1).** `parts.py` has `SMDIP-6_W7.62mm`, but LCSC C20082 is the 9.53 mm body:
  change it to `SMDIP-6_W9.53mm`. It must be fixed before the Pico board is ordered, and it needs a
  re-route there. On the Teensy board, JLC left it off and a through-hole H11L1 goes in by hand.
- **Idea:** an automatic check of every footprint against LCSC's own (EasyEDA) footprint,
  through easyeda2kicad.

## 5. Carried over from the P4 review

- **MOD_5V margin.** MOD_5V is about 4.6 V after the Schottky, against the MP1658's 4.5 V
  minimum. Raise +5VD to about 5.2 V or use a lower-drop diode.
- **P4 doc out of date.** `docs/analogue_board_esp32p4.md` still lists pin 20 as PROBE (it is
  unconnected) and does not mention the camera and display I2C. Update it when item 1 is
  decided.

## 6. Lessons from the Teensy bring-up

To fill in when the board arrives.

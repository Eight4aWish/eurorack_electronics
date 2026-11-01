# eurorack_electronics

Analog breadboard layouts, the n8synth layout visualiser and the schematic generator.

## Module inventory

Before answering anything about which modules exist, what hardware is in the rack, or
which repo a module lives in, read the canonical inventory:

**`MODULES.md`** in the [`eight4awish`](https://github.com/Eight4aWish/eight4awish) repo
— <https://github.com/Eight4aWish/eight4awish/blob/main/MODULES.md>

If that repo is checked out alongside this one, read it from disk; otherwise fetch the URL.

It covers all ten repos: the released modules, the built-but-undrafted ones, the
purchased rack with HP and function, companion software, and what is deliberately *not*
a module. No single repo sees all of it, so do not infer the full picture from this one.

## Analogue board

Before writing firmware for the analogue board (Rev A, Teensy 4.1, `teensy_core_midi`) or
for **Boy**, the module built on it, read **`docs/analogue_board_reva_firmware.md`**. It
covers:
- the pin map, the chips and the Boy wiring;
- the measured values;
- how to build and flash on this Mac.

The working driver code for every chip is in `firmware/analogue_board_test/src/main.cpp`.

- **Bring-up record:** `docs/analogue_board_bringup.md`.
- **Spec:** `docs/analogue_board_spec.md`. Its §15 firmware requirements are binding.
- **Rev B planning:** `docs/analogue_board_revb.md`.

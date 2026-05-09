# Eurorack Electronics

Analog Eurorack breadboard layouts, drum-voice schematics, and a layout visualiser. Originally lived inside [Eight4aWish/eurorack_modules](https://github.com/Eight4aWish/eurorack_modules) — split out so that repo can stay focused on firmware.

## What's here

### `tools/n8layout/`

[n8synth](https://www.n8synth.com/) platform layout files. Hand-edited `.n8layout` JSON describing component placement on the n8synth breadboard. Loadable in the visualiser.

- `6HP_Template.n8layout` — blank starter layout sized for a 6HP module
- `808_Kick_Example.n8layout` — example 808-style kick layout

### `tools/visualizer/`

A browser-based layout viewer that renders breadboard placements from JSON, plus a Python helper that converts SPICE-ish netlists into layout JSON.

- `index.html` — main visualiser; opens any layout from `layouts/`
- `kick_drum_breadboard.html` — focused viewer for the kick drum layout
- `netlist_to_layout.py` — netlist → layout JSON converter
- `layouts/` — per-drum-voice JS + JSON layouts (kick, snare, FM drum two-board)

To run locally:

```sh
# From this directory
python3 -m http.server 8000
# then open http://localhost:8000/tools/visualizer/
```

Or open `tools/visualizer/index.html` directly in a browser if you don't need module loading.

### `docs/`

Drum-voice circuit notes — netlists derived from the *MKI x ES EDU DIY Modular* book and breadboard placement working notes:

- `kick_drum_netlist_from_text.md`, `kick_drum_breadboard_placement.md` — kick drum
- `snare_drum_netlist.md` — snare drum
- `fm_drum_netlist.md`, `fm_drum_rebuild_questions.md` — FM drum (two boards)

## Companion repo

Firmware for Eurorack modules using these analog voices and layouts lives in [Eight4aWish/eurorack_modules](https://github.com/Eight4aWish/eurorack_modules). Per-module pre-built binaries are published as releases there.

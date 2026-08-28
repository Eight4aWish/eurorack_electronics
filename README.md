# Eurorack Electronics

Analog Eurorack breadboard layouts, drum-voice schematics, a dual-channel low-pass gate, a build-phase schematic generator, and a layout visualiser. Originally lived inside [Eight4aWish/eurorack_modules](https://github.com/Eight4aWish/eurorack_modules) — split out so that repo can stay focused on firmware.

## What's here

### `tools/n8layout/`

[n8synth](https://www.n8synth.com/) platform layout files: the official blank module templates (SVG with embedded n8 metadata) plus one worked example.

- `4HP Template.n8layout`, `6HP_Template.n8layout`, `10HP Template.n8layout`, `10HPS Template.n8layout` — official blank templates (10HPS = 10HP with a second stacked breadboard). These are the **source of truth for board geometry** — `tools/visualizer/gen_board_profiles.py` parses them into board-profile JSON.
- `808_Kick_Example.n8layout` — example 808-style kick layout

### `tools/visualizer/`

A browser-based layout viewer that renders breadboard placements from JSON, plus Python helpers for netlist → layout conversion and placement validation.

- `index.html` — main visualiser; opens any layout from `layouts/`
- `kick_drum_breadboard.html` — focused viewer for the kick drum layout
- `check.sh` — **one-command check**: geometry validation → net-identity cross-check → doc map regeneration
- `netlist_to_layout.py` — netlist → layout JSON converter
- `cross_check_nets.py` / `validate_layout.py` / `sync_layout.py` / `gen_rowmap.py` — placement validation + maintenance helpers
- `gen_board_profiles.py` / `boards/` — board-profile JSON generated from the official n8synth templates: JPS control-deck cells, edge-connector maps, gap positions, D ground bus. **Ground truth for platform behaviour is [`docs/n8synth_platform.md`](docs/n8synth_platform.md)** — that document wins over anything inferred from the templates or these profiles.
- `layouts/` — per-module JS + JSON layouts (kick, snare, FM drum two-board, dual LPG)

### How I use this (workflow)

The loop that produced the dual LPG, end to end:

1. **Reference review** — survey published schematics for the topology, compare sources, pick component values. Output: `docs/<module>_reference_review.md` + `docs/<module>_netlist.md` with named nets and per-source confidence tags.
2. **Skeleton layout** — `netlist_to_layout.py` converts the netlist doc into a layout JSON with components, stages, and net assignments but no positions.
3. **Placement** — fill in row/column positions per build phase (LLM-assisted in Claude Code sessions, guided by the board profile's control-deck maps in `boards/`). Panel-facing legs land on control-deck JPS pads; grounds tie to the deck-wide D bus.
4. **Verify** — `./check.sh`: zero hole collisions, every component on the nets the netlist requires, then the placement doc's row maps regenerate from the JSON so they can never drift.
5. **Build** — open the visualiser, step through the build phases at the bench; each phase carries its own test checklist (visible in the side panel).

Repeat 3–4 until clean; the layout JSON is always the single source of truth for placement.

To run locally:

```sh
# From this directory
python3 -m http.server 8000
# then open http://localhost:8000/tools/visualizer/
```

Or open `tools/visualizer/index.html` directly in a browser if you don't need module loading.

### `tools/schematic/`

Build-phase schematic generator for the **Dual Pingable LPG**. Produces per-phase PNGs (Phase 1 / Phase 2 / Mix) into `docs/schematics/`, with component values read live from the LPG layout JSON so the diagrams stay in sync with the design. Built on [Schemdraw](https://schemdraw.readthedocs.io/). See [`tools/schematic/README.md`](tools/schematic/README.md).

### `docs/`

Circuit notes, netlists, and reference material.

**Platform reference**

- `n8synth_platform.md` — verified electrical behaviour of the n8synth breadboards and control
  decks: main area vs edge connector vs power rail, board variants, grounding practice. The
  single source of truth; everything else is downstream of it.

**Drum voices** — derived from the *MKI x ES EDU DIY Modular* book and breadboard placement working notes:

- `kick_drum_netlist_from_text.md`, `kick_drum_breadboard_placement.md` — kick drum
- `snare_drum_netlist.md` — snare drum
- `fm_drum_netlist.md`, `fm_drum_rebuild_questions.md` — FM drum (two boards)

**Dual Pingable LPG** — original dual-channel low-pass gate (canonical Buchla 292 audio path + Strike + CV + Depth + mix output):

- `lpg_reference_review.md` — topology survey, target feature set, vactrol part choices
- `lpg_published_schematics.md` — comparison of the source schematics that informed the design
- `lpg_netlist.md` — full netlist
- `lpg_breadboard_placement.md` — n8synth placement, panel layout, build-phase order
- `lpg_bom.csv` — bill of materials
- `schematics/` — generated build-phase PNGs

Reference materials that informed the LPG design are linked at their original sources (see Credits) rather than redistributed here.

## Credits

### Dual Pingable LPG

The audio path is the canonical **Buchla 292** Lopass Gate, originally designed by **Don Buchla** (~1971). The topology, component values, and driver structure of this build were cross-validated against multiple independent published sources, each linked at its original home:

- **Parker, J. & D'Angelo, S.** — *"A Digital Model of the Buchla Lowpass-Gate"*, [DAFx 2013](https://www.dafx.de/paper-archive/details.php?id=uqLQLFI9j52bBmv10UKKMg) — the analytic topology and closed-form gains (Rα placement per Eq. 4 / Eq. 12).
- **Nonlinear Circuits (NLC) [Low Pass Gate](https://www.nonlinearcircuits.com/modules/p/low-pass-gate)** — Rα = 4M7, 470R LED current limit, the zener clamp on the LED-drive node (VD5 / VD6).
- **AI Synthesis [AI017 Low Pass Gate](https://aisynthesis.com/product/ai017-low-pass-gate/)** — 10K series resistors flanking the vactrol LDRs, DEPTH wired as a rheostat (their P3).
- **Eddy Bergmann's redrawn Buchla 292** — [Synthesizer Build part-35: Resonant Lopass Gate](https://www.eddybergman.com/2020/10/synthesizer-build-part-35-resonant.html) — confirmed the Rα placement and the 1K series output resistor (R_OUT_A / R_OUT_B).
- **Thomas White's [NRM Lopass Gate](https://modularsynthesis.com/nrm/lopass/lopass.htm)** — third independent confirmation of Rα at V₊ → GND.
- **Doepfer [A-101-2 Low Pass Gate](https://doepfer.de/a1012.htm)** — the "status LED tracks vactrol drive" concept (adapted here to a parallel branch off the driver, rather than series, for compatibility across vactrol / LED options).

Target feature set (dual-channel, Strike-pingable, no DAMP / mode-switch in the day-one core) follows the **Make Noise Optomix / LxD** shape; see [lpg_reference_review.md](docs/lpg_reference_review.md) for the topology survey and trade-offs. Per-source confidence tags and the rationale for each block are in [lpg_netlist.md](docs/lpg_netlist.md) and [lpg_published_schematics.md](docs/lpg_published_schematics.md).

### Drum voices

Kick, snare, and FM drum netlists are transcribed and adapted from the *MKI x ES EDU DIY Modular* book.

## Companion repo

Firmware for Eurorack modules using these analog voices and layouts lives in [Eight4aWish/eurorack_modules](https://github.com/Eight4aWish/eurorack_modules). Per-module pre-built binaries are published as releases there.

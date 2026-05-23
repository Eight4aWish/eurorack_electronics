# LPG build-phase schematics

Generates clean schematic sheets for the Dual Pingable LPG, aligned to the
**build phases** (not the functional netlist blocks) so they can drive
follow-along build videos.

## Output (`docs/schematics/`)

| Sheet | Build phase | Shows |
|-------|-------------|-------|
| `phase1_channel.png` | Phase 1 | A channel's first sound: audio path + vactrols + driver + MANUAL |
| `phase2_channel.png` | Phase 2 | That channel made pingable: + CV, strike, status LED (Phase-1 parts faded grey, Phase-2 in colour) |
| `phase5_mix.png` | Phase 5 | The mix summer (CHA_OUT / CHB_OUT come in as labelled stubs) |

Channel B (Phases 3–4) is a topological clone of Channel A, so it is **not
redrawn** — re-use the Phase 1/2 sheets and follow the designator map printed by
the script (DA1→DA2, R1→R7, …).

## Rendering convention (cumulative)

- **Current phase** — bold, drawn in that phase's colour (from the `stages`
  colour field in `tools/visualizer/layouts/lpg.json`).
- **Earlier phases** — thin grey (already on the board).
- **Later phases** — omitted.

Positions are identical across sheets, so the board "grows" in place between
episodes.

## Data source

Component **values** are read live from
`tools/visualizer/layouts/lpg.json` (`twoPins[].value`) and the **phase/colour**
from its `stages[]` — the same source of truth the breadboard visualizer and
`cross_check_nets.py` use. Editing a value there re-flows into the schematics on
the next run; nothing is typed into the drawing.

## Run

```sh
python3 tools/schematic/gen_lpg_schematic.py
```

Requires `schemdraw` and `matplotlib` (`pip install schemdraw matplotlib`).
PNG output (matplotlib backend) is used so the images open inline in editors and
embed directly in video editors / docs without an SVG viewer.

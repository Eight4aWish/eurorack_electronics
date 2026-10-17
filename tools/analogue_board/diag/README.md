# Diagnostics

Small scripts used while routing the analogue boards, kept for bring-up and the next board. None
of them changes a board except `clear_dangling.py`. Scripts that load a board run with KiCad's
own Python (it has `pcbnew`):

```sh
KPY=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
```

| Script | Runs with | What it tells you |
|---|---|---|
| `trial_summary.py drc.json [--totals]` | python3 | A `kicad-cli pcb drc --format json` report: violations by type, and unconnected items as signals, rails and ground |
| `drc_list.py drc.json` | python3 | Every unconnected item and every copper fault (anything not silkscreen or library), with positions |
| `trial_where.py drc.json` | python3 | Where the unrouted signal connections are, on a coarse grid of the board |
| `review_decoupling.py board.kicad_pcb` | `$KPY` | For every IC pin on a rail, the routed track length to the nearest capacitor; flags those over 4 mm. A logic pin tied to a rail (CLR, MR) shows up too: check the datasheet before worrying |
| `leftover_pattern.py report.json=board.kicad_pcb ...` | `$KPY` | Across several DRC reports, each leftover connection's kind (rail, ground, signal) and nearest chip: where a board keeps failing |
| `row_crossings.py board.kicad_pcb ...` | `$KPY` | How many module header rows each signal net's shortest pad-to-pad tree crosses |
| `chip_moves.py board.kicad_pcb U602,U502 name=x,y ...` | `$KPY` | For each chip, total straight-line track to its pins and header rows crossed, now and at candidate spots: whether a move is worth trying |
| `clear_dangling.py board.kicad_pcb` | `$KPY` | **Edits the board:** deletes exactly what KiCad's DRC calls a dangling track or via, repeating until none remain; stops if the unconnected count rises |

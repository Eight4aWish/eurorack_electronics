# Design Journal: the analogue board, from spec to order

A record of how the analogue board was actually arrived at, wrong turns included. It was
kept because the *process* is part of what this repo documents, and because it may become a
video. The spec's §13 to §15 hold the decisions and every trial table; this journal holds
the story between them.

**Companions:**
- [`analogue_board_spec.md`](analogue_board_spec.md): the decisions (§13) and the trial log
  (§14).
- [`hardware/analogue_board/README.md`](../hardware/analogue_board/README.md): the boards and
  the generator.

**Material for a video:**
- [`analogue_board_journal/images/`](analogue_board_journal/images/): the milestone images,
  numbered in story order.
- [`analogue_board_journal/routing_runs.csv`](analogue_board_journal/routing_runs.csv): every
  routing and finishing run, stage by stage.
- [`analogue_board_journal/logs/`](analogue_board_journal/logs/): the raw logs behind every
  figure.
- [The raw material](#raw-material) at the end lists what lives outside the repo.

---

## Where it started vs where it landed

| | Starting point (14 Oct 2026) | Landed (17 Oct 2026) |
|---|---|---|
| **Goal** | A general-purpose Eurorack I/O board under an n8synth deck, for a Pico 2 or a Teensy 4.1 | Two boards from one generator. The **Teensy board is ordered** from JLCPCB, fully routed and two of five assembled; the **Pico 2 / ESP32-P4 board** is routing |
| **Tooling** | KiCad, Freerouting, scripts | A Python generator that writes the schematics and boards, checks them against datasheets and the netlist, places, pre-wires, routes in stages, finishes, labels and writes the JLC files |
| **Layers** | 4, one face of parts | 6, both faces of parts; ground plane on In1, +5VD plane on In4 for the Pico board |
| **Feature set** | Fixed CV in and out, switchable jacks, eight pots, gates, MIDI, Qwiic, display | Six switchable CV jacks, six pots, four gates each way, TRS MIDI, display on I2C holes. The "core set": anything less is a patch.Init |
| **Who routes** | Freerouting, with hand finishing in KiCad | Scripts only. David has no KiCad experience, so hand work became the last resort and the tools grew until they could finish the board |
| **Cost** | Unknown | £268 for 5 boards with 2 assembled on both faces (6 layers, OSP finish), plus import VAT |

---

## The turns

**1. The spec (14 Oct).** Reference reviews: patch.init, the Workshop Computer, EuroPi, Ogham,
and later Versio, Legio and Alchemy Lab. Decided:
- the DAC8568 over the MCP4822;
- a CC BY-SA 4.0 licence;
- the module on headers over the logic;
- JLCPCB with LCSC parts checked against stock.

The I/O review settled what the board is for. Alchemy Lab's switchable jacks became the
feature David would not give up.

**2. Checkpoint 1: a generated schematic (14 to 15 Oct).** No hand-drawn sheets: Python writes
every sheet, then checks:
- KiCad's ERC;
- the netlist against the generator's own record of intent;
- every IC pin against a separately transcribed datasheet pinout;
- decoupling on every power pin;
- diode orientation.

A block review followed, adding TRS MIDI and ESP32-P4 support.

**3. Checkpoint 2: real parts on paper (15 Oct).** A 1:1 printout of the outline, edge strips,
sockets and power header. David laid a real Pico 2, Teensy 4.1 and deck header on it, and
every measurement agreed. One change followed: a card in the Teensy's microSD socket stood
2.5 mm past the board edge, so the Teensy moved 3 mm down.

**4. Checkpoint 3: placement, and the first hard number (15 Oct).** The courtyards came to
**104% of one face** before any routing. David decided on double-sided assembly: the deck
face takes passives and low ICs.
- **The floorplan** (image 01): analogue at the top, furthest from the buck converter; chips
  down the channel between the module rows, in bus order.
- **First-pass auto-placement** (image 02), then the chips placed level with their module bus
  pins (image 03).

**5. First autoroutes: a wall (15 to 16 Oct).** Freerouting on 4 layers routed 80%, but it
had used the In1 ground plane as a signal layer. With In1 kept whole, 283 of 992 connections
stayed unrouted. **The move to two boards** (image 04, one per module), trimming features and
going to 6 layers, still left about 100 signals per board. Six layers removed about 35% of the
leftovers, the split about 12%, the trims 7–11%.

**6. Quilter (16 Oct).** The cloud placer-router took a lot of preparation:
- a pin-count mismatch, fixed by giving every pad its own pin;
- a power layer for rail pours.

It then placed nothing under the module, and it could not be steered. David: *"The Quilter
route is not working for me because you are not able to resolve issues directly. And
freerouting can't get anywhere near. I am inclined to give up."* The project nearly stopped
here.

**7. The finding that kept it alive: fan-out last (16 Oct).** Freerouting's fan-out stage drops
a via beside every surface-mount pin before routing, and on a dense board those vias block
everything. The run settings in the spec's §14 show it.

**The staged route:**
1. Signals first, with fan-out off.
2. Lock them, then route again with fan-out on for ground and rails.
3. A last pass with cheap plane vias.

On the trimmed Pico "core" board (image 05) every signal but one routed. David: *"Wow. That is
unexpected."*

**8. One board again: `shared_core` (16 Oct).** David's choice: one board for both module
formats, with:
- the Teensy on full headers;
- TRS MIDI back in;
- the display on solderable holes only;
- six switchable CV jacks;
- no fixed-direction CV.

Every signal routed (image 06). What was left was ground (29) and +5VD (7).

**9. Finishing by script, and the ground nobody had looked at (16 Oct).** `finish.py` began as
a tidier:
- via drills;
- narrow tracks;
- a via beside each stranded ground pad.

Then a measurement showed **207 ground pads sharing 38 vias, joined by 567 mm of thin track**,
a poor ground for an ADC, DAC and codec. The fix inverted the order: **every ground pad gets
its own via before routing**, and the router routes round them. On that run, ground stopped
failing: 61 left after stage 1, 0 of them ground. Earlier runs had left hundreds of ground
connections. Images 07 (before) and 08 (after).

**10. "Two left" (16 Oct).** Four placements in a row finished exactly two connections short,
a different two each time. Each fix was real and each time a new pair became the hardest:
- **The DG412s** sat under the ADC with their pad columns opposite its own (image 09).
- **Decoupling.** Half the IC power pins were more than 4 mm of track from any capacitor, so
  each capacitor is now wired to its pin before routing (image 10).
- **A ground-via rule.** Ground vias were pushed outward from a chip's middle, which for a
  corner pin is diagonal: two of them walled in ADC pin 2. They now go straight out along the
  pin.
- **FB301** had been placed 28 mm from the codec pin it feeds.
- **A header-row penalty.** The placer now charges for every module header row between a part
  and its pins.

Then **0.1 mm rules** were tried: 57 left after stage 1 against 24, and 11 minutes a pass. It
was dropped.

**11. Back to single modules, and placement by eye (16 Oct).** David: *"Alternatively going back
to single modules?"* That was the right call, for a reason found later: the shared board's
failures sat where four header rows crowded the middle. David reviewed each placement render
and moved parts by eye:
- the 595 into a void left of the header row;
- the LDO out from under the module's end;
- the module brought down, tried and undone. It freed no useful space and brought the codec
  nearer the buck: *"risky bringing anything close to the power though"*;
- five right-column wiring holes into the right strip's unused positions 11–15, so three
  chips could slide clear of the header row.

**The Teensy board's stage 1 left 13, against 24–26 for the shared board** (image 11). With a
rip-up-and-reroute chain added to `finish.py`, it finished at **0 unconnected, 0 copper
faults** (image 12).

**12. To the order (16 Oct).**
- **Decoupling review:** two flagged pins were not supply pins at all (the DAC's CLR, the
  595's MR). Four paths over 4 mm were accepted as DC references or a slow supply.
- **Labels:** block numbers beside the wiring blocks, names beside the test points
  (`labels.py`), and a wiring map.
- **Order files:** `fab.py` writes the Gerbers, BOM and placement file.

David went through JLCPCB for the first time with a step-by-step walkthrough:
- he chose **OSP** over ENIG, which was much dearer and unnecessary for a board soldered soon
  after delivery;
- all 59 part types matched;
- coupons covered the postage, bringing it to **£268**.

**Ordered: 5 boards, 2 assembled** (image 13).

**13. The Pico board (16 to 17 Oct).** The Teensy lessons carried over:
- no bus test points (every bus pin can be probed at the module socket);
- the LDO out from under the module;
- decoupling tracks protected from rip-up.

Then a question from David: *"was there a pattern in previous failures"*. Across six routes,
102 leftovers:
- **71 were rails**, not signals;
- **over half sat at the ADC, the DAC, a switch chip or the regulator beside them**;
- the jams came from chips stacked on opposite faces, whose vias fence each other's pins.

Two variants were routed (images 14 to 16):

| Variant | After stage 1 | After stage 2 | After `finish.py` |
|---|---|---|---|
| Standard | 35 | 17 | 2 |
| +5VD plane on In4 | 14 | 9 | 1 |

The last open connection was ADC_RST. Its pin turned out to be **fenced in by six ground vias**,
each legitimate for its own pad. The pre-route now keeps an escape lane clear in front of
every chip's signal pins. David's message: *"we need to adjust placement at the top of the
board"*. He re-laid the top himself:
- the ADC lowered;
- the DAC and CV op-amp turned and stacked, then swapped;
- the deck-face chips put where nothing sits above them;
- the 3.3 V analogue regulator moved out of the way.

**That layout left 7 after stage 1, the best of any board.** At the time of writing it is
still routing.

---

## Errors caught, and the pattern behind them

Mine, in the order they happened:

| Error | Cost | What changed |
|---|---|---|
| Trial copies routed without their `.kicad_pro`, so KiCad's default rules applied | ~45 min of routing wasted | `autoroute.py` refuses a board without its project file and prints the rules it found |
| A watcher attached to the wrong log (picked "newest file") | A false report | Watchers name their log explicitly |
| `board.Remove` handed items to Python and broke the next track listing | A crash | `board.Delete` |
| The board edge taken from the outline's bounding box, 0.05 mm too generous | 3 edge-clearance faults | The edge comes from the outline's own line |
| A "sliver" clean-up deleted 567 tracks in a cascade | Caught at once; nothing kept | Only what KiCad's own DRC calls a dead end is removed |
| My decoupling review counted logic pins tied to a rail as supply pins | Two false alarms | Checked against the datasheet pin names |
| The leftover router returned an empty route for overlapping copper and retried it forever | **About 5 hours overnight, two runs stuck** | No empty routes; a no-progress guard; runs checked every 15 minutes |
| The leftover router coloured its grid one cell at a time | Long connections took hours | Row-at-a-time marking and an A* search |

**The pattern:** most of these are a script's model of the board disagreeing with KiCad's.
Bounding box against outline. "Touching" against KiCad's rule that a track end must land
inside the other copper. My idea of a dead end against KiCad's. Each was fixed by asking
KiCad, through its DRC, rather than trusting the model. The other lesson is operational:
**silence is not progress.** A long run gets a timeout and a regular check.

---

## What came from looking at the board

The scripts did the routing; every big step in placement came from David looking at a render.

| Observation | Effect |
|---|---|
| *"there is a gaping wilderness ... just below the module and above the power"* | Slow chips moved down on the shared board |
| *"gapping spaces in the right hand 40x2 column"* | The display's I2C holes moved into the right strip's unused positions |
| *"Alternatively going back to single modules?"* | Two header rows instead of four: the Teensy board routed |
| The 595 into the left void; the LDO out from under the module | Part of the Teensy board's 13 after stage 1 |
| *"risky bringing anything close to the power"* | A 10 mm module drop undone |
| Right-column holes into the strip gap, so chips slide right | A lane beside the header row |
| *"slimming the number of [test points] would actually help the pico layout"* | 18 bus test points dropped from the Pico board |
| *"we need to adjust placement at the top of the board"* | The Pico top re-laid: 7 after stage 1 |

---

## Raw material

- **The images:** [`analogue_board_journal/images/`](analogue_board_journal/images/), numbered as
  the turns above. Renders from git history (01–06, 11–13) and from the trial boards that
  exist only on this machine (07–10, 14–16), outward and deck faces.
- **The runs:** [`routing_runs.csv`](analogue_board_journal/routing_runs.csv), one row per
  routing stage or finishing run, with its settings, connections before and after, time and
  board file.
- **The logs:** [`analogue_board_journal/logs/`](analogue_board_journal/logs/), the raw output
  of every run, with KiCad's repetitive debug lines removed.
- **The commits:** `git log -- hardware/analogue_board tools/analogue_board` runs from the spec
  (c684b47, 14 Oct) to the order files (0a107b9, 16 Oct).
- **The trial boards:** `hardware/analogue_board/*/output/autoroute/`. About 50 boards, not
  committed (ignored as measurements). Copy them somewhere safe before any clean-up if the video
  needs more renders.
- **The conversation:** the full transcript, with every message and decision, is on David's
  machine at `~/.claude/projects/-Users-dbaghurst-GitHub-eurorack-electronics/` (about 110 MB of
  JSON lines). It is not in the repo.

## Still open

- The Pico board's route on David's top layout.
- The Teensy board's arrival: bring-up, first power-on, and what Rev A needs bodging.
- Whether the Pico board's wiring field should match the Teensy board's (the right-hand holes
  moved differently on each).

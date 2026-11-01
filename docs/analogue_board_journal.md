# Design Journal: the analogue board, from spec to the first module

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
| **Goal** | A general-purpose Eurorack I/O board under an n8synth deck, for a Pico 2 or a Teensy 4.1 | Two boards from one generator, both fully routed. The **Teensy board is ordered** from JLCPCB, two of five assembled; the **Pico 2 / ESP32-P4 board** has its order files ready |
| **Tooling** | KiCad, Freerouting, scripts | A Python generator that writes the schematics and boards, checks them against datasheets and the netlist, places, pre-wires, routes in stages, finishes, labels and writes the JLC files |
| **Layers** | 4, one face of parts | 6, both faces of parts; ground plane on In1, +5VD plane on In4 for the Pico board |
| **Feature set** | Fixed CV in and out, switchable jacks, eight pots, gates, MIDI, Qwiic, display | Six switchable CV jacks, six pots, four gates each way, TRS MIDI, display on I2C holes. The "core set": anything less is a patch.Init |
| **Who routes** | Freerouting, with hand finishing in KiCad | Scripts only. David has no KiCad experience, so hand work became the last resort and the tools grew until they could finish the board |
| **Cost** | Unknown | USD 353 (£278) for 5 boards with 2 assembled on both faces (6 layers, OSP finish), plus £69 customs and tax on delivery: **£347 landed** |

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

**That layout left 7 after stage 1, the best of any board.** Stage 2 took it to 4, and
`finish.py` closed the rest: **0 unconnected, 0 copper faults, at the first attempt on the
re-laid top.** The decoupling is better than the Teensy board's: every IC supply pin has a
capacitor within 4 mm of track. The two pins flagged were logic pins tied to a rail. Image 17.

**14. Rev B, panel first (23 to 26 Oct).** While the Teensy board was being made, David asked
three questions:
- could the ESP32-P4's camera or screen be blocked by our pins?
- are the strips' outer and inner holes joined?
- what does the wiring field look like against the deck's cells?

The answers became a plan:
- **The pins.** Pins 16 and 17 carried the P4's own I2C. They now go to two reserved holes, and
  CS_595 takes the pin jack detect had left free.
- **The deck.** A colour-coded map of the field showed four banks with no common pattern.
  David: *"I really should have thought it through. Plenty of room for improvements!"*

He set six rules: 10HP only, controls at the top, jacks next, audio at the bottom (ins on the
panel's left), even sides, extras in the gaps. A patch.Init()-style panel mocked up on the
deck's 18 cells gave the channel set: patch.Init() plus whatever spare channels on chips already
in each zone give, keeping the two-way CV.

One correction mattered: Claude had moved the pots ADC onto the converter bus to free a pin, and
marked it decided. David: *"I thought there were timing and sequencing issues."* The spec (§6.1)
keeps that bus to itself for audio-rate CV. The pin came from EXP_INT instead.

The generator got a Rev B board (`pico_revb`), and placement went in turns:
- **First pass,** two hole columns a side.
- **David's field:** one column a side, utility holes in the strips' empty positions, the codec
  and audio op-amp turned and moved right.
- **The routes got worse,** not better. The widened lanes beside the module had filled with
  passives. Kept clear, the board routed completely (rB6), but six capacitors sat 4-10 mm from
  their pins.
- **Decoupling fixed by design:**
  - nothing on the deck face under the ADC or DAC;
  - the DG412s, 595 and comparators turned, in pairs, with the middle of the face free for vias;
  - the buck's input capacitors at its VIN pin;
  - the DPAK to the bottom centre.

| Route | What changed | Stage 1 | Stage 2 | After `finish.py` |
|---|---|---|---|---|
| rB1 | first pass | 9 | 7 | 2 |
| rB5 | David's field, CV column reordered | 24 | 16 | — |
| rB6 | lanes beside the module kept clear | 9 | 6 | 0, 6 capacitors over 4 mm |
| rB8 | decoupling by design | 7 | 4 | 1 (a +5VD pin with no room for its via) |
| rB9 | the 595 and comparator turned | 6 | 2 | 1 (a ground pin under an op-amp's pads) |
| rB10 | that comparator turned again | 26 | 16 | 2 |
| vA, vB, vC | three ways to clear that ground pin, side by side | 1, 5, 28 | 1, 2, 15 | 0, **0**, 0 |

Freerouting turned out deterministic but chaotic: a 0.5 mm move swung stage 1 from 6 to 44
open. So the last step routed three minimal variants at once and kept the best.

**vB: 0 unconnected, 0 copper faults, every IC supply pin within 4 mm of a capacitor** (the two
pins flagged are the DAC's CLR and the 595's MR, logic pins tied to a rail). 13 of its 14
wiring blocks carry a silkscreen label. Image 18.

**15. Rev A arrives: bring-up, and the first module, Boy2 (27 Oct to 1 Nov).**

**What to build first (27 Oct).** With the boards in the post, David picked the first panel:
Boy's, with one change. *"i did wonder whether the discrete button/pot could be combined into a
push encoder. That would leave the pot position free for, say, another gate out/drum or TRS midi
in."* That became
**Boy2**: Boy's panel and screen, a push encoder (a Bourns PEC11R) for the button and pot 1, and
TRS MIDI in. Looking at the wires the panel would need, he was blunt about why there were so
many: *"the spaghetti of wiring is my poor Rev A planning."*

**The boards land (30 Oct),** four days early. The bring-up started in a session in another
project, and that evening stages 1–5 and the first five test blocks passed. The board itself
held two surprises:
- **No test point numbers on the silkscreen.** David couldn't find "TP209". From then on the
  plan named holes as marked-up pictures show them, never by reference designator.
- **PlatformIO's Teensy compiler and loader are Intel-only, and this Mac has no Rosetta.** A
  small script swaps in an arm64 compiler, and the Teensy Loader app does the flashing.

**Back to this project (31 Oct).** The other session didn't have the design history. David:
*"it is struggling because it lacks some of the details which are available to this chat ... my
preference would be to revert back here to complete the work."* The lesson for this way of
working: the context lives with the project, so the work should too.

**One fit, and the least wire.** The deck can be built two ways, and the board can sit upright
or turned over, so the two boards can meet in four ways. David: *"Where there are opportunities
to reduce the length of wires we should take them."*
- **The choice:** the wiring map planned every wire for each fit. The n8synth way, board
  upright, needed 24 wires and 800 mm, with 6 crossing the board; the next best needed 889 mm.
- **The encoder** moved to gate inputs 3 and 1, the holes nearest its cell, with its common on
  the pot reference, which Boy2 doesn't otherwise use.
- **Borrowed pads.** The encoder needed one pin more than its cell has. The screen covers two
  cells, so their pads were free: *"I can borrow any of the abc positions from JPS cells 1 and
  2."* No wire runs between the boards outside the strips.

**Rules for the bench.** David set three:
- *"i don't want to attach any temp wires"*;
- test only what Boy2 uses;
- ground first: *"experience has taught me that is an important one to remember so I have
  wired that first"*.

He checked the ground at once and found the plan's ground pad wasn't bridged on the deck.

**The MIDI links.** Rev A puts MIDI on two spare pins, with link holes to choose. David: *"it
seems odd not to just assign those 2 pins to midi r and midi t."* He kept Rev A as it was and
asked for a Rev B note: closed solder jumpers instead of link holes.

**Batches.** *"I have previously found this to be easy to get wrong ... I tend to start making
mistakes when I go for more than an hour wiring."* The 24 wires went in seven batches, each
checked with the meter and tested before the next, and the wiring map gained a batch picker:

| Batch | Result |
|---|---|
| 0. Deck ground | continuity to the board's GND |
| 1. Encoder | 4 counts per click, clockwise counts up; the push reads |
| 2. Gate outs | 5.02–5.05 V and 0 V at each jack |
| 3. CV outs | **gate3 read 0.00 V** while the board read 0.99 V at its hole: a slip on the deck, fixed, then 0.98 V. The rest read about 1.8% low, the same on all six: a calibration job |
| 4. Audio | **the meter showed nothing** on the 440 Hz sine, and David planned to recheck the wiring. A DC level (+5 V asked, 4.86 V read) proved the outputs. Then the board's own loopback read 9.9 Vpp of 10, and he listened to the tone: *"the wiring was right all along. it was something to do with the test?"* It was the meter |
| 5. MIDI in | David's two unlabelled Befaco cables: red is Type A. The board read notes and a 120 BPM clock from his Proton, clean |
| 6. Screen | **a "dead" top row** that wasn't: the error table below |

**1 Nov: every batch passed.** Boy2's hardware works, and the firmware notes
([`analogue_board_reva_firmware.md`](analogue_board_reva_firmware.md)) hand it to the next stage.

**Afterwards.**
- **The cost:** USD 353 (£278) for five boards, two of them assembled, plus £69 customs: **£347
  landed**. Three bare boards are the minimum order's overhead; the second assembled board is a
  spare module.
- **The spare capacity.** David: *"amazing the huge amount of functionality that is not being
  used in this design."* Boy2 uses about half the board. That raised Rev B's next question:
  trim it towards four layers instead of six?

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

**In the bring-up (30 Oct to 1 Nov):**

| Error | Cost | What changed |
|---|---|---|
| The wiring planner gave each audio input its own copy of the hole pattern, so two inputs could claim one hole | Caught on the map, before any wire | One shared pattern per kind of hole |
| The encoder's pins assumed to run A, B, push; the PEC11R's run A, C, B | Caught before wiring | Its common lands on the middle pad |
| The deck ground first planned to a hole no picture labels | Hard to find at the bench | Only holes the pictures label |
| The hold-voltage command (`c N V`) read the jack number as the voltage | Five jacks held at the wrong values, one refused | Each number parsed in turn |
| The screen set up as 128×64, as the spec's table said, not as Boy's own code had it (128×32) | A dead pixel row logged that didn't exist. David: *"Did you use the exact same settings and libraries that are used in boy?"* | Read a module's firmware before writing a driver for a part taken from it; the log and the spec corrected |

**The pattern:** most of these are a script's model of the board disagreeing with KiCad's.
Bounding box against outline. "Touching" against KiCad's rule that a track end must land
inside the other copper. My idea of a dead end against KiCad's. Each was fixed by asking
KiCad, through its DRC, rather than trusting the model. The other lesson is operational:
**silence is not progress.** A long run gets a timeout and a regular check.

The bring-up's errors follow the same pattern. A second-hand source was trusted over the
first-hand one: the spec's table over Boy's own code, a meter reading over the board's own
loopback. The fix each time was the most direct source. The costliest one, the screen, was
caught by David's bench sense: he knew the screen had been working in Boy.

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

At the bench, during the bring-up:

| Observation | Effect |
|---|---|
| *"the clk and reset are gate outs not ins"* | Boy2's panel plan corrected before wiring |
| *"could be combined into a push encoder"* | Boy2: an encoder for the button and pot 1, freeing a cell for TRS MIDI in |
| *"I can borrow any of the abc positions from JPS cells 1 and 2"* | No wires between the boards outside the strips |
| *"JPS2 C is not attached to ground"* | The deck's missing ground bridge found before power |
| *"I tend to start making mistakes when I go for more than an hour wiring"* | Seven tested batches, and a batch picker on the wiring map |
| *"I have concerns over the resistance between ground and the 3v3"* | About 680 Ω: R210, the regulator's load, as designed |
| *"this is the screen from the boy which was working fine"* | The "dead row" traced to a set-up error |
| *"they are befaco cables so we might be able to find out which is which"* | Red is Type A, then confirmed by the board |

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
- **The trial boards:** every routing trial's boards, DSN and session files and Freerouting
  logs (311 files), archived on 2026-10-17 to
  `~/Documents/eurorack_archive/analogue_board_trial_routes_2026-10-17.tar.gz` on David's
  machine (39 MB) and removed from the working copy. They are not committed. Unpack the archive
  in the repo root to render more of them.
- **The conversation:** the full transcript, with every message and decision, is on David's
  machine at `~/.claude/projects/-Users-dbaghurst-GitHub-eurorack-electronics/` (about 110 MB of
  JSON lines). It is not in the repo. The first evening of the bring-up (30 Oct) ran in a session
  in the eight4awish project, under `~/.claude/projects/-Users-dbaghurst-GitHub-eight4awish/`.
- **The bring-up (chapter 15):**
  - [`analogue_board_bringup.md`](analogue_board_bringup.md): the plan, and its Log, which holds
    every reading with its date;
  - [`analogue_board_bringup/`](analogue_board_bringup/): the marked-up pictures, and
    `wiring_map.html`, the wiring map with its batch picker;
  - [`analogue_board_revb/panel_plan.html`](analogue_board_revb/panel_plan.html): the Rev B panel
    mock-up from chapter 14.

  The two pages began on claude.ai; these copies keep them, and open in any browser. The test
  program is in [`firmware/analogue_board_test`](../firmware/analogue_board_test/src/main.cpp).
  The commits run from the plan (72d3e4d, 30 Oct) to the firmware notes (c4ef4d8, 1 Nov).

### For a video of chapter 15

The moments, and what can show each one:

| Moment | What shows it |
|---|---|
| The boards arrive, four days early | David's footage, if filmed (the plan asked for the unboxing and the first power-on) |
| "Where is TP209?" | A test-point picture against the bare silkscreen |
| The other session loses the thread; the work comes home | The two conversations, side by side |
| Four fits, one chosen | The wiring map, fit by fit, with "Show wires" on |
| Borrowed pads | The wiring map's JPS1 and JPS2 cards |
| Seven batches | The wiring map's batch picker, stepping 0 to 6, against the deck being wired |
| gate3 reads 0.00 V | The six meter readings, one wrong |
| "Nothing" on the meter, then the tone | DC 4.86 V, the loopback's 9.9 Vpp, and the sound itself |
| The screen's "dead row" | The border with its missing line, David's question, then the full border |
| Red cable, Type A | Notes and clock scrolling in from the Proton |
| *"amazing the huge amount of functionality that is not being used"* | The board, with Boy2's half lit; on to Rev B |

## Still open

- **Rev B's order.** Rev A's lessons are in: the Log's "For Rev B?" column and
  [`analogue_board_revb.md`](analogue_board_revb.md) §7. Open: whether to trim it towards four
  layers. The proposal of 1 Nov is to route Rev B on four layers as it stands first, then compare
  landed quotes.
- **Boy2's firmware.** Not written yet. It probably goes beside Boy in `eurorack_modules`, but
  that hasn't been decided.
- **Calibration:** the CV outputs, about 1.8% low, kept in the EEPROM.
- **The noise comparison** against the Daisy Seed MultiFX and the Teensy Chaos.
- **The second assembled board:** a second module, or a known-good reference.
- **ESP32-P4:** the HDMI picture's sideways glitch, and the APLL conflict
  ([`analogue_board_esp32p4.md`](analogue_board_esp32p4.md)).

# Design Journal — MOD2, and the LPG reconciliation

A record of how the work was actually arrived at, including the wrong turns. Kept because the
*process* is part of what this repo documents: the reference reviews state conclusions, but they
hide how much of the design came out of iteration and correction rather than a clean run.

- **Part one** — arriving at the MOD2 build spec.
  Companion to [`mod2_reference_review.md`](mod2_reference_review.md), which holds the conclusions.
- **Part two** — reconciling the dual LPG against the built board, and what it taught the tooling.

---

# Part one — the MOD2 build spec

---

## Where it started vs where it landed

| | Opening ask | Final spec |
|---|---|---|
| **Goal** | Build a snare for a spare 6HP slot | A **dual-firmware-compatible** board running 25 published voices |
| **Firmware** | "a snare drum is one of the patches available for the MOD2" | HAGIWO's CC0 `snare.ino`, plus every other MOD2 *and* Melon voice, unmodified |
| **Power** | "MELON uses a regulated 5V… I tend to use bucks, I also have 7805s" | 7805 from +12V, datasheet decoupling, with the *reason* understood (3.3V is the ADC reference) |
| **LED** | "It would be interesting to see if I could use that enhancement" | Both indicator types populated — the mechanism that makes dual-firmware work |
| **Jumpers** | not mentioned | **Both** JP1 and JP2 promoted to panel switches |
| **Panel** | unknown | 12 of 12 deck cells, fully allocated |

The opening question was essentially "can I build this snare?" The answer that emerged was
"you can build something considerably more useful than a snare, for the same parts count."

---

## The turns

**1 — Opening.** Vague but well-sourced brief: spare 6HP, snare wanted, MOD2 is CC0, MELON has a
5V regulator and an RGB LED worth stealing, here is the note.com article.

**2 — First research pass.** Established CC0, XIAO RP2350, 4HP original. Fetched the schematic —
though not on the first try: the page summariser transcribed the image filename wrong and
CloudFront 404'd. Recovered by going to note.com's API for the real asset URLs. Decoded the
full Rev A schematic and cross-checked every value against the JLCPCB BOM, which also confirmed
C15 as DNP.

**3 — "The 5V on the N8Synth comes from the Eurorack PSU. It is too noisy."**
Settled the regulator question immediately, and pointed at something better: tracing the rail
showed +5V feeds the XIAO's LDO, whose 3.3V output is *simultaneously the pot supply and the ADC
reference*. The noise wasn't a digital-supply annoyance, it was landing on control-voltage
measurement.

**4 — "Look for the N8Synth control deck positions and work out how they map to the LHS."**
Direct instruction to do work not yet done. Produced the JPS1–12 → row mapping, and the finding
that the 6HP deck is `strips: 1` — all 12 cells serialise onto the left strip, unlike the 10HP
the LPG uses.

**5 — "Why are you looking for the MOD1 when we are making a MOD2?"**
Fair. It was a dead end, though it produced the conclusion that mattered — or so it seemed at
the time. See error A.

**6 — "You sure?" + a YouTube link.**
The pivot. See error A below. HAGIWO publishes a MOD2 snare directly, and it is CC0. This
deleted the entire RALPS licensing problem from the design.

**7 — "We want to build hardware and show people how to use the existing firmwares… no software
tweaks. I am guessing that since we have 12 control deck positions we could actually create a
piece of hardware that would run either code?"**

The single most consequential turn in the conversation. It reframed the project from *build a
snare* to *build a firmware-agnostic board*, and the hunch turned out to be exactly right.
Verifying it was straightforward once asked: diffing matched MOD2/Melon firmware pairs showed
identical pin maps, with the Melon versions differing only by an `Adafruit_NeoPixel` block on
`#define LED_PIN 5`. **GPIO5 is the entire hardware delta between the two families.**

**8–11 — Four corrections in sequence.** Errors B through E below.

**12 — "I think I saw two jumpers in the hagiwo schematic?"**
Correct, and the more important of the two had been missed entirely. See error F.

**13 — Panel-mounting both jumpers.** The design's last substantive move — see below.

**14 — "What is the 3.3V decoupling query?"** Prompted a proper answer rather than a parked
question, and surfaced that pot measurement is *ratiometric*, so common-mode noise largely
cancels and A2 is the genuinely exposed channel.

**15 — "Can you find the necessary RGB LED on any UK supplier website… I am guessing it comes
as a little board I will need to somehow mount."**

A sourcing question that turned into a design correction. The obvious answer — a 5mm
through-hole NeoPixel, which mounts exactly like the plain LED beside it and maps neatly onto
JPS pads A/B/C/D — is **wrong for this build**, and for a reason invisible until you read the
product description:

> *"Note that these are 'RGB' instead of the 'GRB' format used in the 5050-sized LEDs"*

The Melon firmwares declare `NEO_GRB`. A through-hole part would swap red and green on every
voice — violating the no-software-tweaks constraint set in turn 7. The best mechanical fit was
the worst functional fit, and only the datasheet-level detail revealed it.

The chosen part (Adafruit 5975 breakout, 5050 → GRB) then produced a better answer to a
question already thought settled: Adafruit state it runs from **3.3V or 5V**, and at 3.3V the
data threshold drops to 2.31V — dissolving the WS2812B-V5-versus-diode debate entirely. The
spec now carries all three options ranked, with the in-spec diode route as the default.

The user's guess about mounting was also correct, and worth recording: a breakout board does
**not** drop into a JPS cell the way a 5mm LED does, so the indicator needs a mechanical
solution (M2 standoffs, light pipe) even though its *electrical* cell allocation is unchanged.

---

## Errors caught, and the pattern behind them

| | Error | Caught by | Root cause |
|---|---|---|---|
| **A** | "There is no MOD2 snare firmware" | "You sure?" + HAGIWO's own demo video | Trusted a page summary that truncated the folder list at **9 of 19** |
| **B** | "Both LEDs fit in one JPS cell" | "We can't share a cell for the two types of LED" | Conflated *four electrical pads* with *one physical component footprint* |
| **C** | "Treat JPS11/12 as unreliable" | "JPS11/12 is obviously on the board. Not sure why you doubt your own research" | Read `layoutRows`/`powerSectionRows` as deck constraints when they describe the **breadboard** |
| **D** | "The snare has no prebuilt binary" | "Have you actually looked properly for the binary?" | Filtered the repo tree to `.ino/.h/.cpp/.md` — **excluded binaries by construction** |
| **E** | Ranked the diode hack above WS2812B-V5 | "Did you flag a 5V version of the WS2812B?" | Mentioned the right part but buried it as a fallback |
| **F** | Documented JP1, missed JP2 entirely | "I think I saw two jumpers" | Read the schematic region once and moved on |

**The pattern: every error came from trusting a filtered or summarised view instead of the
primary source.** A truncated page summary, a self-imposed file filter, a hardcoded constant
read as authoritative, a single pass over a schematic.

Every recovery came from going to the primary source: note.com's API for real asset URLs, the
GitHub API for the true file tree, the raw `.ino` files for pin maps, UF2 magic-byte inspection
to prove a binary was genuine, and zoomed crops of the schematic to trace JP1 and JP2 pin by pin.

The user's corrections were consistently of one form: *you are contradicting your own evidence,
or you did not actually look.* Both were fair every time.

---

## What the analysis contributed

Stated factually, since the point of this journal is an honest account of both directions.

- **Decoding the schematic into design rationale.** Deriving `1 + 68k/33k = 3.06` → 10.1 Vpp
  explained the published output spec, and `A2 ≈ 3.53 − POT3 − CV` explained the inverted ADC —
  later independently confirmed by the snare firmware header documenting POT3 as "reversed ADC".
- **Turning the dual-firmware hunch into a verified fact** by diffing the two firmware families,
  rather than assuming compatibility.
- **Finding the noise path.** Establishing that the 5V rail reaches the ADC reference via the
  XIAO's LDO, which is what makes local regulation worth doing rather than a nicety.
- **Panel-mounting both jumpers.** The design's most useful single change (below).
- **Numbers instead of assertions.** 7805 at 0.46 W / ~30 °C rise; WS2812B thresholds of 3.5 V
  vs 2.7 V; RC corners of 159 Hz on A0/A1 vs 7.2 kHz on A2.

### The jumpers → switches change

Once the goal became "one board, many firmwares", both jumpers stopped being build-time
settings and became **operating controls**:

- **JP1** — filter cutoff. Bright voices want 15.9 kHz, kick and bass want 5.0 kHz.
- **JP2** — output coupling. This one isn't cosmetic: shorting C18 converts the module from an
  **audio output** (±5 V, AC-coupled) to a **CV output** (0–9.9 V, DC-coupled), which is what
  `tides` needs for its LFO and AD/AR envelope modes.

Leaving those as solder jumpers on the back would have meant re-soldering every time the
firmware changed. On the panel, swapping voices becomes: flash a `.uf2`, set two switches.
Cost: exactly the two spare deck cells, taking the panel to 12 of 12.

---

## Carried into the build as open items

Deliberately *not* resolved on paper, because they need the bench:

1. XIAO 3.3 V decoupling — add 100n at the deck end, star-feed the rail, watch **A2** as the
   canary (A0/A1 are already filtered at 159 Hz).
2. 7805 thermal figure with the WS2812B lit (~0.9 W worst case).
3. Confirm the pixel actually shipped is a **V5** revision.
4. ~~`tides` pin map~~ — disproved: `tides` uses Arduino D-aliases, so `D7`=GPIO1 and
   `D4`=GPIO6. An exact match to the standard map; the concern conflated D- with GPIO-numbers.
   Probably a stale comment like `kick`'s `D11`, but unverified.
5. Per-firmware switch-settings table — currently reasoned, not measured.

---

## Lesson for the next module

The reference review reads as though the design was derived cleanly. It wasn't — it took six
corrections, and the two best features in the spec (dual-firmware compatibility, and JP2 on the
panel) both originate in user observations rather than the research pass.

Two process rules worth carrying forward:

1. **Go to the primary source, and don't let a convenience filter decide what exists.** Every
   error in this conversation traces to a summary, a filter, or a single glance.
2. **State findings so they can be challenged.** The corrections all landed quickly because the
   claims carried their evidence — "9 of 19 folders", "hardcoded in `gen_board_profiles.py`" —
   which made them checkable rather than merely assertive.


---

# Part two — reconciling the LPG, and what the tooling learned

Bringing `lpg.json` into line with the board on the bench. Eleven commits. The layout work was
routine; what it exposed about the tooling was not.

## The pattern behind almost every fault: two sources for one fact

Six separate bugs this session, all the same shape — a fact stated in two places with nothing
forcing them to agree, and one copy silently going stale:

| Fact | Stated in | and in | Result |
|---|---|---|---|
| Which net a node carries | `netLabels` | IC pin `net` | 2 labels on the wrong row for 2 revisions |
| The layout itself | `layouts/*.json` | `layouts/*.js` wrapper | Two fixes appeared not to work — the browser was 3 revs behind |
| Which end a part's pin 1 is | `rotation` field | the pins themselves | Flipped SIPs notched at the wrong end |
| Component placement | generated row maps | hand-written ASCII + build checklist | ~84 lines describing the rev-0.17 board |
| Build-phase content | layout `stage.desc` | the placement doc | Visualiser captioned correct geometry with wrong rows |
| Panel wiring positions | off-board tables | `jpsWires` | Correct, but only by luck — nothing checked |

Each fix was the same move: **derive rather than duplicate**, or where the duplicate earns its
keep, **make something check it**. The notch is now derived from where pin 1 sits. The wrapper
is regenerated by `check.sh`. The ASCII is deleted. The off-board tables survive as prose
because they carry conventions no JSON records — but `check_doc_positions.py` now verifies every
position they name.

**One instance remains unfixed and it is the big one.** `cross_check_nets.py` holds
`BARE_ROW_NETS`, a hand-maintained table asserting which net each bare row carries. It grew
from **21 entries to 39** during this session — eighteen assertions about design intent that no
file states, added by hand, each of which the checker would have accepted had it been wrong.
That is blocker B1 in the tool plan, and this session is the argument for it.

## Four defect classes the checks could not see

Each was found by the builder looking at the screen, not by any check. Each is now caught:

1. **A net label disagreeing with the IC pin on the same node** — `LED_DRIVE_A` was labelled on
   row 5 while its components sat on row 7. `cross_check_nets` validates component endpoints and
   never looks at `netLabels`, so a label could say anything.
2. **The same net named on both row halves with nothing bridging the gap** — two isolated nodes
   pretending to be one. Reads as correctly wired in both the diagram and the netlist.
3. **A wire scheduled later than both ends it joins** — the phase reads as complete while the
   circuit is open, so its bench test cannot pass and nothing says why.
4. **Hand-written doc positions drifting from the layout.**

Two more are known and not yet added: a component reaching across the board for a rail (only
`R15` and `R31` ever did, both now fixed), and anything placed on a header-blocked outer hole.
Both currently have zero violations.

**The lesson is uncomfortable: the checks that exist are the ones somebody tripped over.** The
unknown gaps are wherever nobody has looked yet.

## Measure the measurable

Two cases where I was reasoning about something a script could answer exactly:

- **Colour.** The palette failed **four of five** accessibility checks; sidebar text measured
  **1.08:1** against its background. "Looks a bit dim" was really "invisible", and the validator
  said so in seconds. It also settled a design argument definitively: eight categorical hues
  cannot be made mutually distinguishable, and no ordering fixes it.
- **Geometry.** The net-label overlap was a 1.7px intersection with the row bar, solved by
  arithmetic rather than nudging.

## Syntax is not execution

A blanket find-and-replace rewrote the palette definition itself, producing `rBody: TH.rBody` —
valid syntax, `ReferenceError` at load. It killed the whole script block, so no layouts
registered and the picker came up empty with no visible error. `node --check` passed throughout;
I had been verifying the wrong property. `smoke_test.py` now executes the page against a stub
DOM and asserts a layout registers.

## Derive rather than ask

Asked where three components had moved, the builder pointed out it was derivable — and it was.
Two placed components fixed where the moved nets now lived, and `EXPECTED_NETS` said what was on
them; everything else followed. Worth reaching for before asking a question the data answers.

## What this says for the public tool

The verification loop is the product, and it is genuinely good — it caught every knock-on of a
fifty-component rework and refused to regenerate docs from a bad state. But its coverage is
anecdotal, and `BARE_ROW_NETS` means the most valuable check cannot be used by anyone else at
all. The structured circuit file (B1) should come **before** MOD2 placement, not after.

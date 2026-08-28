# MOD2 — Design Journal

A record of how the MOD2 build spec was arrived at, including the wrong turns. Kept because the
*process* is part of what this repo is documenting: the reference review states conclusions, but
it hides how much of the design came out of iteration and correction rather than a clean run.

Companion to [`mod2_reference_review.md`](mod2_reference_review.md), which holds the conclusions.

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

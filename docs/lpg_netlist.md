# Dual Pingable LPG — Netlist

**Status:** rev 0.5 — design draft, **for review**. Rev 0.5 incorporates two reference-derived fixes after a full audit against Bergmann + Thomas White + Aalto/DAFx 2013 (see `docs/refs/`): (a) R_α (R3, R9) repositioned to V_p→GND per Aalto Eq. 4 + 12, Bergmann R13, White R13; and (b) per-channel 1K output resistors R_OUT_A / R_OUT_B added (panel-side, in-line on jack pigtails), matching Bergmann's R15 and White's R15.
**Purpose:** Netlist for our dual-channel pingable LPG. Rev 0.2 rewrote the audio path to match the canonical Buchla 292 topology after we found three real schematics ([NLC](refs/nlc_lpg.pdf), [AI017](refs/ai017_schematic.pdf), [Aalto/DAFx 2013](refs/aalto_buchla292.pdf)). Rev 0.3 iterated layout and (incorrectly) removed the LED-driver zener clamp. **Rev 0.4 restores the zener** (VD5/VD6, socketed 3v9 / 6v8 / 9v1) to match the Thomas White / Eddy Bergmann / NLC canonical topology, sized for our day-one 2× VTL5C3-in-series LED chain. See [lpg_published_schematics.md](lpg_published_schematics.md) for the source comparison.

**Build target:** "Core + L1 + L3 + L6" — see [lpg_reference_review.md](lpg_reference_review.md). Day-one breadboard build covers dual canonical-Buchla-292 audio path + Strike + CV input + Depth + socketed filter cap. Layers L4 (DAMP), L5 (mode switch), L7 (resonance) are *planned-for in tap-points and PCB space* but not built day one.

**Layer L2 dropped:** The canonical Buchla 292 already has two LDRs in the audio path (via a dual-vactrol). The "second vactrol per channel" layer from the original plan is now *part of the core*, not an upgrade.

---

## Confidence tags

Each block is labelled with how grounded it is in real, working circuits:

- **PROVEN** — directly transcribed from a published schematic that's been built and tested
- **ADAPTED** — based on a published schematic, with documented changes for our use case
- **SKETCHED** — synthesised from principles, not yet verified against a working build

Trust PROVEN blocks. Review ADAPTED blocks for the change rationale. Treat SKETCHED blocks as starting points to refine after bench measurement.

---

## TOPLEVEL BLOCK DIAGRAM

```
                              ┌──────────────────────┐
                              │  CANONICAL BUCHLA    │
                              │  292 AUDIO PATH      │
                              │  (per channel)       │
                              ├──────────────────────┤
  CHA_IN ─► IN_BUF_A ─► R_in ─► LDR1 ─► V_x ─► LDR2 ─► V_+ ─► FILT_BUF_A ─► CHA_OUT
                              │           │              │
                              │           ▼              ▼
                              │       C_2 (220pF)    C_1 (1nF, socketed)
                              │           │              │
                              │          GND            GND
                              │           │
                              │           └── R_α (4M7) ── (to V_+) [reserved for L5/L7]
                              │
                              │  LDR1 + LDR2 = two LDRs of one
                              │  dual-vactrol (VTL5C3/2)
                              └──────────────────────┘
                                          ▲
                                          │ LED current
                                          │
  STRIKE_A ─► PULSE_SHAPER_A ─┐
                              │
  CV_A     ─► CV_ATTEN_A ─────├─► SUMMER_A ─► DEPTH_A ─► R_led ─► VC_A.LED ─► STATUS_LED ─► VC_B.LED ─► GND
                              │   (op-amp)   (A500K)    (470R)
  MANUAL_A ─► (offset)────────┘

  (Channel B mirrors channel A — same audio path, same driver. Status LED is shared
   across both channels, wired in series with both vactrol LEDs per Doepfer A-101-2.)

  CHA_OUT ─┐
           ├─► MIX_BUF ─► MIX_OUT
  CHB_OUT ─┘

  +12V/-12V/GND ─► POWER (decoupling, reverse-polarity protection)
```

**Reserved tap-points (for L4/L5/L7 plan-only layers):**
- `V_+ ↔ V_x` link via R_α (4M7) — reserved on PCB; **L5 mode switch** taps this to short R_α to 5K (VCA mode) or open it (some implementations)
- `V_fb` from FILT_BUF output through C_3 (4.7nF) back to V_x — reserved; **L7 resonance** activates this feedback loop with a gain trim
- `LED_DRIVE_A_SUM ↔ LED_DRIVE_B_SUM` cross-coupling — reserved; **L4 DAMP** is a pot that bridges these for shared decay

---

## BOM (day-one build = core + L1 + L3 + L6)

### Resistors (32 total, all 1/4W 1% metal film unless noted)

| Qty | Value | Designators | Role |
|-----|-------|-------------|------|
| 4 | 100K | R1, R7, R13, R19 | Input pulldown A/B; CV in pulldown A/B |
| 2 | 100K | R23, R26 | Mix bus summing inputs |
| 2 | 100K | R24, R27 | Mix bus feedback (unity gain) |
| 1 | 100K | R28 | Mix bus +in to GND |
| 2 | 4M7 | R3, R9 | **R_α — defines closed-state divider** (canonical Buchla 292) |
| 4 | 10K | R4, R10, R5, R11 | Series before/after vactrol LDRs (audio path) — per AI017 |
| 4 | 10K | R14, R20, R36, R37 | Driver op-amp feedback + non-inv ground reference |
| 2 | 4K7 | R32, R33 | Manual offset summing into driver |
| 2 | 4K7 | R29, R30 | Manual offset top resistor (limits VCC drive) |
| 2 | 4K7 | R38, R39 | CV summing into driver |
| 2 | 10K | R34, R35 | Strike summing into driver |
| 2 | 10K | R15, R31 | Strike pulse-shaper pulldowns (10ms time constant with C15/C16) |
| 2 | 1K | R16, R22 | CV input series protection |
| 2 | 1K | R17, R25 | Strike input series protection |
| 2 | 470R | R6, R12 | Vactrol LED drive current limit (8–18mA range across vactrol LED Vfs) |
| (4) | 220R | (alt R6/R12 + spares) | Alternative current limit — for higher-Vf DIY vactrols (green/blue/white LEDs) |
| 2 | 4K7 | R_STATUS_A, R_STATUS_B | Status LED current limit for red LEDs (parallel branch off DRV_OUT; was 2K2/green) |
| 2 | 10R | R40, R41 | Power rail series filter |

**Notes on canonical values:**
- R_α = 4M7 (= 4.7 MΩ) is from the NLC schematic; Aalto paper specifies 5 MΩ but 4M7 is a standard E-series value. Same musical effect.
- 10K series resistors before/after the vactrol LDRs are from AI017 (R8, R10 in their schematic). They protect the input/output buffers if the vactrol shorts and limit current into the LDR.
- 470R LED current limit comes from NLC and AI017 — both agree.

### Capacitors (15 total)

| Qty | Value | Type | Designators | Role |
|-----|-------|------|-------------|------|
| 2 | 47µF | Electrolytic 25V | C1, C2 | Power supply bulk filter (one per rail) |
| 8 | 100nF | Ceramic X7R | C3, C4, C5, C6, C7, C8, C9, C10 | IC supply decoupling (1 per op-amp rail = 8 total for 4× TL072) |
| 2 | 220pF | C0G/NP0 ceramic | C11, C12 | **C_2 — first filter pole** (canonical Buchla 292, fixed) |
| 2 | 1nF | Film or C0G | **C13, C14** | **C_1 — second filter pole — SOCKETED (DIP-2)**, swappable per channel |
| 2 | 1µF | Film | C15, C16 | Strike pulse-shaper differentiator (~10ms time constant with 10K) |
| 1 | 100nF | Film | C17 | Mix bus output DC blocking |

**Cap value rationale:**
- C_1 and C_2 values come directly from Aalto Table 1 ("Both" mode) and are confirmed by both NLC and AI017 BOMs. **Three independent sources agree.**
- Socketed C_1 (1nF default) lets us swap to **470pF** (brighter, sub-bass open-cutoff bumps higher) or **2.2nF** (darker, more pronounced LP behaviour). C_2 stays fixed.
- C0G/NP0 ceramic for the small filter caps — low drift with temperature, low distortion. Film is fine if you have it but the 220pF size is awkward in film.

### Semiconductors

| Qty | Type | Designators | Role |
|-----|------|-------------|------|
| 4 | TL072 | DA1, DA2, DA3, DA4 | 8 op-amp halves total (see IC USAGE) |
| 2 | 1N4148 | VD1, VD2 | Strike pulse rectifier (positive edge only into LED driver) |
| 2 | 1N5819 | VD3, VD4 | Power supply reverse polarity protection |
| 2 | **Zener (default 6v8, 500 mW)** — **socketed** | **VD5, VD6** | **Vactrol LED-chain max-current clamp** (one per channel, anode→LED_DRIVE node, cathode→GND). Stock 3v9 / 6v8 / 9v1 for A/B bench testing. |
| 2 | 5mm red LED | LED_STATUS_A, LED_STATUS_B | Status LEDs (red — matches build) — one per channel, driven from parallel branch off DRV_OUT |
| 2 | 3V3 zener (500 mW) | VD7, VD8 | Status-LED turn-on threshold — in series in each status-LED ground leg (LED anode → VD7/VD8 → GND, banded toward GND). Kick-in ~Vf_LED + 3.3 ≈ 5.2V so the LED ignores the MANUAL floor and flashes on strikes/peaks. |

### Vactrols — build options

The vactrol position uses a footprint that accepts either a **dual-LDR vactrol** (one package containing 2 LDRs + 1 LED) or **two single-LDR vactrols** wired with their LEDs in series. Both arrangements give the canonical 2-LDR-in-audio-path Buchla 292 behaviour.

#### Option A — molded vactrol(s)

Pick one of these:

| Choice | Qty per channel | Total | Notes |
|---|---|---|---|
| **VTL5C3/2** (dual-LDR) | 1 | 2 + 2 spares = 4 | Canonical Buchla part. Single 5-pin package. |
| **2× VTL5C3** (single-LDR) | 2 | 4 + 4 spares = 8 | Alt. AI017 uses VTL5C9 (slower) — buy a few of those too for A/B |
| **2× LCR0202** (Senba) | 2 | 4 + 4 spares = 8 | Cheap Chinese single-LDR vactrol, drop-in for VTL5C3 |
| **2× LCR0203** (Senba) | 2 | 4 + 4 spares = 8 | Faster variant — better for percussive ping |

Recommend buying a small handful of each so we can A/B in the same socket.

#### Option B — DIY socketed vactrol (LED + LDR + 3D-printed shroud)

The shroud is a build123d project (separate workstream — not designed here). It mounts a 5mm LED facing an LDR inside a light-tight enclosure, with leads compatible with our PCB footprint.

| Qty | Type | Designators | Role | Notes |
|-----|------|-------------|------|-------|
| 8 | **GL5528 LDR** | RL1–RL8 | Light-dependent resistor for DIY vactrol | Dark R ≈ 1MΩ, light R ≈ 10–20KΩ at 10 lux. Slow response, vactrol-like character. |
| 4 | **GL5516 LDR** (alternative) | — | Faster alternative LDR | Dark R ≈ 0.5MΩ, light R ≈ 5KΩ. Buy a few for comparison. |
| 8 | 5mm LED, **green** (~525 nm) | LED1–LED8 | Drives DIY vactrol — green is closest to LDR peak sensitivity | High-brightness preferred |
| 4 | 5mm LED, **amber** (~590 nm) | — | Alternative LED for swap experimentation | Good LDR response, different "feel" |
| 4 | 5mm LED, **red** (high-brightness) | — | Faster turn-off than green; classic DIY-vactrol choice | High-brightness preferred |
| 4 | 5mm LED, **blue or white** | — | For experimentation — Two-Tone uses these | Less LDR-efficient but novel character |

LDR part-to-part variation is ~50% — buy generously and bench-select matched pairs.

#### Sources for the DIY shroud

- [FREE 3D PRINTED VACTROL DESIGN! DIY LOW PASS GATE… (YouTube)](https://www.youtube.com/watch?v=7z4Z0lHUWmE) — user-supplied reference video
- [Pnoreck — Housing for DIY Vactrol (Printables)](https://www.printables.com/model/6291-housing-for-diy-vactrol) — 2-part tube design. PETG fits perfectly; PLA is loose but works with a drop of glue.
- [kloroplaster — Optocoupler Vactrol for LDR + 5mm LED (Thingiverse)](https://www.thingiverse.com/thing:3081361)
- [prouting — Vactrol single and dual (Thingiverse)](https://www.thingiverse.com/thing:5329114)
- [bmoren/two-tone (GitHub)](https://github.com/bmoren/two-tone) — heatshrink-only reference

**Footprint caveat:** community 3D-printed designs are tube-format with flying leads. Our PCB will have a footprint matching the molded vactrol parts. Bridging the two requires either an adapter PCB or a redesigned shroud with our footprint moulded in. Separate build123d task.

### Potentiometers (8 total — 4 per channel)

| Qty | Value | Taper | Designator | Label | Wiring |
|-----|-------|-------|------------|-------|--------|
| 2 | 100K | B (lin) | P1, P5 | CV ATTEN A/B | jack tip → R(1K) → top, GND → bottom, wiper to driver |
| 2 | 100K | B (lin) | P2, P6 | MANUAL A/B | VCC → 4K7 → top, GND → bottom, wiper to driver |
| 2 | 500K | A (log) | P3, P7 | DEPTH A/B | rheostat (CCW shorted to wiper): driver out → CW → wiper → R(470R) → LED |

Note: DEPTH is wired as a rheostat (variable R), not a divider. CCW shorted to wiper = full pot resistance in series; full CW = 0Ω in series. Per AI017 (P3 in their schematic).

### Connectors (9 jacks + power)

| Qty | Type | Designator | Label |
|-----|------|------------|-------|
| 1 | Switched mono jack | XS1 | CH A IN |
| 1 | Switched mono jack | XS2 | CH A STRIKE |
| 1 | Switched mono jack | XS3 | CH A CV |
| 1 | Switched mono jack | XS4 | CH A OUT |
| 1 | Switched mono jack | XS5 | CH B IN |
| 1 | Switched mono jack | XS6 | CH B STRIKE |
| 1 | Switched mono jack | XS7 | CH B CV |
| 1 | Switched mono jack | XS8 | CH B OUT |
| 1 | Switched mono jack | XS9 | MIX OUT |
| 1 | 2x5 pin header | XP1 | Eurorack power |

### Sockets

| Qty | Type | Designator | Role |
|-----|------|------------|------|
| 2 | Vactrol footprint (5-pin or DIP-style) | for VC1, VC2 | Vactrol — accepts molded VTL5C3/2 OR 2× single VTL5C3/9/LCR020x OR DIY shroud |
| 2 | 2-pin DIP socket | for C13, C14 | **Filter cap C_1 socket** — swappable cap for tonal experimentation |
| 4 | 8-pin DIP socket | for DA1–DA4 | Recommended — cheap insurance against op-amp damage |

---

## IC USAGE (TL072 ×4 = 8 op-amp halves)

| IC | Half A (pins 1-3) | Half B (pins 5-7) |
|----|------|------|
| **DA1** | IN_BUF_A — input buffer for channel A | FILT_BUF_A — filter output buffer for channel A |
| **DA2** | IN_BUF_B — input buffer for channel B | FILT_BUF_B — filter output buffer for channel B |
| **DA3** | DRV_A — CV/Manual/Strike summer for channel A LED | DRV_B — same for channel B |
| **DA4** | MIX_BUF — inverting summer for mix output | **SPARE** — reserved for L7 (resonance feedback amp) or L4 (DAMP coupler) |

**Allocation rationale (per-channel grouping):** each audio channel's full signal path now lives on a single TL072 — channel A on DA1 (input buf half A + filter buf half B), channel B on DA2. This lets you build and bench-test channel A end-to-end with only DA1 populated, no need to install DA2 first. Drivers stay shared on DA3 because the four halves we need fit cleanly there. Status LEDs and Depth pots are off-board so don't affect IC allocation.

---

## NETLIST BY FUNCTIONAL BLOCK

### BLOCK 1 — Audio Input Buffer (per channel)

**Confidence: PROVEN.** Universal TL072 unity-gain non-inverting follower, identical to the kick drum's input handling. No design risk.

| Component | Value | Pin 1 | Pin 2 | Pin 3 |
|-----------|-------|-------|-------|-------|
| R1 | 100K | CHA_IN | GND | — |
| DA1A (TL072) | — | CHA_IN (+in, pin 3) | DA1A_OUT (-in, pin 2) | BUF_OUT_A (out, pin 1) |

**Channel B mirror (note: on DA2 not DA1 — per-channel IC allocation):**
| R7 | 100K | CHB_IN | GND | — |
| DA2A (TL072) | — | CHB_IN (+in, pin 3) | DA2A_OUT (-in, pin 2) | BUF_OUT_B (out, pin 1) |

In a unity-gain follower the -in is shorted to the output (DA1A_OUT = BUF_OUT_A directly).

---

### BLOCK 2 — Canonical Buchla 292 Audio Path (per channel)

**Confidence: PROVEN.** Topology and component values transcribed from three independent sources: Aalto/DAFx 2013 paper Table 1, NLC schematic rev 1.1, and AI017 schematic v0. All three agree on 220pF + 1nF + ~5MΩ R_α + dual-LDR-in-series structure.

| Component | Value | Pin 1 | Pin 2 | Notes |
|-----------|-------|-------|-------|-------|
| R4 | 10K | BUF_OUT_A | VC_A.LDR1.in | Series input resistor (AI017 R8 — NOT in Bergmann/White/Aalto; harmless addition for layout isolation) |
| VC_A.LDR1 | — | VC_A.LDR1.in | V_x_A | First LDR of dual-vactrol |
| C11 | 220pF | V_x_A | GND | **C_2 — first filter pole** (canonical Buchla 292; matches Aalto C_2, Bergmann C7, White C7) |
| VC_A.LDR2 | — | V_x_A | V_+_A | Second LDR — between V_x and V_+ |
| C13 | 1nF (socketed) | V_+_A | GND | **C_1 — second filter pole** (canonical; matches Aalto C_1, Bergmann C5, White C9) |
| R3 | 4M7 | V_+_A | GND | **R_α — leakage path** (canonical Buchla 292; matches Aalto R_α at V_+→GND, Bergmann R13, White R13). **In parallel with C13.** |
| R5 | 10K | V_+_A | V_OUT_A_PRE_BUF | Series output resistor (AI017 R10 — NOT in Bergmann/White/Aalto; harmless addition). V_OUT_A_PRE_BUF connects to DA1.5 (FILT_BUF_A +in). |

**Channel B mirror:**
| R10 | 10K | BUF_OUT_B | VC_B.LDR1.in |
| VC_B.LDR1 | — | VC_B.LDR1.in | V_x_B |
| C12 | 220pF | V_x_B | GND |
| VC_B.LDR2 | — | V_x_B | V_+_B |
| C14 | 1nF (socketed) | V_+_B | GND |
| R9 | 4M7 | V_+_B | GND | (in parallel with C14) |
| R11 | 10K | V_+_B | V_OUT_B_PRE_BUF |

**Operation (from Aalto paper):**
- When LDR resistance is low (LED bright, ~1KΩ): both poles at high frequency → signal passes with minimal filtering. R_α (4M7) is much larger than LDR (1KΩ), so the divider is dominated by the LDR path → high gain.
- When LDR resistance is high (LED off, ~1MΩ): both poles drop into the audio range AND R_α/LDR divider attenuates strongly → signal drops in level *and* high frequencies roll off. This is the LPG signature.
- Slope is between -6 dB/oct and -12 dB/oct because the two poles aren't coincident (different Q).

**Tap-points:**
- `V_+_A` and `V_+_B` are also `MODE_SW_A_TAP` and `MODE_SW_B_TAP` — L5 mode switch reaches in here.
- The `R_α` resistor (R3, R9) becomes a **switched element** for L5: parallel a 5K resistor across it for VCA mode, leave it open for Both mode (the simplest 2-position implementation; full 3-position needs more switch poles).
- The `V_+_A → C_3 (4.7nF) → V_x_A` feedback path is reserved for L7 resonance.

**Reference comparison (rev 0.5 audit, 2026-05-15):** R_α placement is **V_+ → GND, in parallel with C_1** — confirmed in three independent sources:

- **Aalto/DAFx 2013** ([refs/aalto_buchla292.pdf](refs/aalto_buchla292.pdf)): Eq. 4 has term `-V_+/R_α`, meaning R_α is from V_+ to GND (current flowing out to ground). Eq. 12 gives DC closed-gate gain H_LPG(0) = R_α / (R_α + 2·R_f) — voltage divider with R_α as the bottom leg to GND.
- **Eddy Bergmann's redrawn schematic** ([refs/bergmann_lpg_schematic.jpg](refs/bergmann_lpg_schematic.jpg)): R13 (4M7) and C5 (1nF) both sit at the U1c (output buffer) input, in parallel between V_+ and GND.
- **Thomas White's NRM Lopass Gate** ([refs/white_lpg_schematic.jpg](refs/white_lpg_schematic.jpg)): R13 (4.7M) and C9 (1.0n) at U1 (output buffer) input, parallel to GND.

A previous revision of this netlist (rev 0.2 through rev 0.4) incorrectly placed R_α *across LDR2* (V_x → V_+). That was a mis-reading of the references. Rev 0.5 corrects it.

---

### BLOCK 3 — Filter Output Buffer (per channel)

**Confidence: PROVEN.** Unity-gain follower at V_+ — exactly per Aalto paper Eq. 1 (V_out = V_+) and matches NLC/AI017 op-amp arrangement. Output then goes through a 1K series resistor to the jack, per Bergmann (R15) and Thomas White (R15) — standard Eurorack output protection / impedance setting.

| Component | Value | Pin 1 | Pin 2 | Pin 3 |
|-----------|-------|-------|-------|-------|
| DA1B (TL072) | — | V_OUT_A_PRE_BUF (+in, pin 5) | DA1B_OUT (-in, pin 6) | CHA_OUT (out, pin 7) |
| **R_OUT_A** | **1K (panel-side)** | CHA_OUT (DA1.7) | XS4 jack tip (CHA_OUT_JACK) | — |

**Channel B mirror (on DA2 half B):**
| DA2B (TL072) | — | V_OUT_B_PRE_BUF (+in, pin 5) | DA2B_OUT (-in, pin 6) | CHB_OUT (out, pin 7) |
| **R_OUT_B** | **1K (panel-side)** | CHB_OUT (DA2.7) | XS8 jack tip (CHB_OUT_JACK) | — |

**R_OUT_A / R_OUT_B placement (rev 0.10):** these are **panel-side parts**, soldered in-line on the pigtail between the breadboard exit point (DA1.7 / DA2.7) and the output jack tip. Same construction pattern as R_STATUS_A/B. Cover with heatshrink.

**Why on the panel pigtail (not the breadboard):** the resistor is a single in-line element in series with one wire — it lives most cleanly on the wire itself. Off-board placement avoids any layout reshuffle, mirrors how R_STATUS_A/B are handled, and is a common DIY Eurorack pattern.

**Mix-bus tap point:** the mix bus (R23, R26) taps **from before R_OUT** — i.e., directly from DA1.7 / DA2.7 (the CHA_OUT / CHB_OUT nets on the breadboard, via the JW_CHA_OUT_BUS / JW_CHB_OUT_BUS jumpers). Only the per-channel jack output sees the 1K. This keeps the mix bus's input impedance (R23 = 100K each) loading only the buffered op-amp output, not adding a divider through R_OUT.

CHA_OUT (on-board net at DA1.7) feeds **both**: (a) R_OUT_A → XS4 jack, and (b) R23 mix-bus input. Same for CHB_OUT.

For L7 (resonance), the spare DA4B becomes a feedback amplifier: V_out → DA4B (gain a > 1) → V_fb → C_3 (4.7nF) → V_x. Add a 100K trimpot in DA4B's feedback to set Q.

---

### BLOCK 4 — Strike Pulse Shaper (per channel)

**Confidence: ADAPTED.** RC differentiator + diode rectifier is a textbook gate-to-trigger converter (your kick drum's Block 1 does the same shape). The specific time constant (1µF + 10K = 10ms) is *my judgement call* — should be revisited after bench measurement of how the actual vactrol responds to short pulses.

| Component | Value | Pin 1 | Pin 2 |
|-----------|-------|-------|-------|
| R17 | 1K | STRIKE_A (jack tip) | C15.1 |
| C15 | 1µF | C15.1 | C15.2 |
| R15 | 10K | C15.2 | GND | Strike pulldown — sets 10ms differentiator time constant |
| VD1 (1N4148) | — | C15.2 (anode) | STRIKE_PULSE_A (cathode) |

**Channel B mirror:**
| R25 | 1K | STRIKE_B | C16.1 |
| C16 | 1µF | C16.1 | C16.2 |
| R31 | 10K | C16.2 | GND |
| VD2 | — | C16.2 (anode) | STRIKE_PULSE_B (cathode) |

**Operation:**
- Rising edge of strike gate creates a positive transient at C.2.
- Transient decays through 10K with τ = 10ms.
- Diode passes the positive half only — no LED activity on falling edges.
- Output (STRIKE_PULSE) feeds into the LED driver summing junction (Block 5).

---

### BLOCK 5 — CV/Manual/Strike Driver and LED Drive (per channel)

**Confidence: ADAPTED.** Op-amp summer + Depth pot in series + 470R + **zener-clamped LED chain**. Topology follows the canonical Thomas White / Eddy Bergmann / NLC scheme (op-amp drives 470R into LED, with zener clamp protecting the vactrol from over-current). Depth pot in series is from AI017. Strike-summing-into-driver is our addition (NLC doesn't have a strike input; AI017 doesn't either) — that integration is the SKETCHED part of this block.

**Day-one vactrol target:** 2× **VTL5C3 (DIP-4 single-LDR)** with LEDs in series per channel — Vf chain ≈ 3.2 V. Build channel A first (uses 2 of the 4 VTL5C3s in hand); channel B follows once channel A is verified.

**Zener value note:** NLC uses **3v9** with a *single-LED* vactrol (VTL5C3/2 dual-LDR-one-LED). Our 2× VTL5C3-in-series chain (Vf ≈ 3.2 V) needs the zener above 3.2 V to pass any current. Default-populate **6v8** (≈ 7.7 mA peak through R6=470R) with bench-swappable options 3v9 / 6v8 / 9v1 — see "Zener selection" subsection below.

#### CV input section
| Component | Value | Pin 1 | Pin 2 |
|-----------|-------|-------|-------|
| R16 | 1K | CV_A (jack tip) | CV_PROT_A |
| R13 | 100K | CV_PROT_A | GND (input pulldown) |
| P1 (CV ATTEN A) | 100K B | CV_PROT_A (top) | GND (bottom), wiper → CV_WIPER_A |
| R38 | 4K7 | CV_WIPER_A | DRV_SUM_A |

#### Manual offset section
| R29 | 4K7 | VCC | P2.top |
| P2 (MANUAL A) | 100K B | P2.top | GND, wiper → MAN_WIPER_A |
| R32 | 4K7 | MAN_WIPER_A | DRV_SUM_A |

#### Strike sum
| R34 | 10K | STRIKE_PULSE_A | DRV_SUM_A |

#### Driver op-amp
| R36 | 10K | DRV_SUM_A | DRV_OUT_A | (feedback) |
| R37 | 10K | DA3A.+in (pin 3) | GND | (non-inv reference) |
| DA3A (TL072) | — | DA3A.+in via R37 | DRV_SUM_A (-in, pin 2) | DRV_OUT_A (out, pin 1) |

#### Depth pot + vactrol LED chain (main drive path)
| P3 (DEPTH A) | 500K A rheostat | DRV_OUT_A (CW end) | DEPTH_WIPER_A (wiper, CCW shorted to wiper) |
| R6 | 470R | DEPTH_WIPER_A | LED_DRIVE_A |
| **VD5** | **6v8 zener (socketed; see Zener selection below)** | **LED_DRIVE_A (anode)** | **GND (cathode)** |
| VC_A.LED1 anode | — | GND | (LED1 internal) |
| VC_A.LED1 cathode | — | (LED1 internal) | VC_A_LED_MID |
| VC_A.LED2 anode | — | VC_A_LED_MID | (LED2 internal) |
| VC_A.LED2 cathode | — | (LED2 internal) | LED_DRIVE_A |

**Zener orientation:** anode on LED_DRIVE_A (which sits at negative potential when the inverting driver swings low), cathode on GND. When LED_DRIVE_A tries to swing below -V_zener, the zener conducts in reverse breakdown to ground, clamping LED_DRIVE_A at -V_zener. The LED-chain current is then bounded at I_max = (V_zener − V_f_chain) / R6.

Note: 2 vactrol LEDs in series for the dual-LDR arrangement (one LED of each VTL5C3 single). For molded VTL5C3/2 dual-vactrol part, just one LED in chain instead. For DIY shroud built with two LDRs sharing one LED, also just one. Footprint accepts all three configurations.

**(Channel B mirror — same structure with VD6 / R12 / P7 / VC_B):** VD6 = 6v8 zener at LED_DRIVE_B; anode→LED_DRIVE_B, cathode→GND.

**Why LEDs face anodes-to-GND, cathodes-to-driver:** the driver op-amp output is *negative-going* (inverting summer). To get current flow we route it GND → anode → cathode → R6 → P3 wiper → DRV_OUT_A. When DRV_OUT_A swings negative, current flows.

#### Status LED (parallel branch off DRV_OUT)
| R_STATUS_A | 4K7 | DRV_OUT_A | LED_STATUS_A.cathode |
| LED_STATUS_A | 5mm red | LED_STATUS_A.cathode (from R_STATUS_A) | GND (anode) |

Same polarity convention (cathode towards negative driver, anode to GND). This branch is parallel to the main vactrol drive — its current is independent of vactrol LED Vf, so the design works the same with any vactrol/LED combination.

**Operation:**
- Driver op-amp is an inverting summer with gain = -R_fb / R_in per input:
  - CV: -R36 / R38 = -10K / 4K7 = -2.13×
  - Manual: -R36 / R32 = -10K / 4K7 = -2.13×
  - Strike: -R36 / R34 = -10K / 10K = -1.0×
- DRV_OUT_A swings up to ≈ -10V on a TL072 with ±12V rails.
- **Vactrol current at full drive:** I = (10V − V_f_chain) / 470R. Across the supported LED choices:
  - Single-dual VTL5C3/2 (Vf 1.6V): ~18mA
  - 2× VTL5C3 singles (Vf 3.2V): ~14.5mA
  - DIY red ×2 (Vf 3.6V): ~13.6mA
  - DIY green/blue/white ×2 (Vf 6V): ~8.5mA
  - All cases land in the useful 8–20mA range for vactrol LDR modulation.
- **Status LED current at full drive:** I = (10V − 1.9V) / 4K7 ≈ 1.7mA (red status LED, Vf ~1.9V; was 2K2 with green). Visible, not blinding. Tracks driver level so it does show "how hard the vactrol is being driven", honouring the Doepfer A-101-2 indicator concept.

#### Zener selection (VD5 / VD6)

The zener clamps LED-chain peak current. Use a **socketed** position so the value can be A/B-tested on the bench. Stock all three of:

| Value | I_peak with 2× VTL5C3 series (Vf=3.2V, R6=470R) | Use case |
|-------|--------|----------|
| **3v9** | (3.9 − 3.2) / 470 = **1.5 mA** — barely any drive | Only useful if one LED is bridged out (single-LED-vactrol mode) — matches NLC stock value |
| **6v8** | (6.8 − 3.2) / 470 = **7.7 mA** — moderate drive | **DEFAULT POPULATE** — conservative, comfortably inside VTL5C3's 0–20 mA range, gentle ping character |
| **9v1** | (9.1 − 3.2) / 470 = **12.6 mA** — bright drive | Use if 6v8 doesn't fully open the vactrol on peak ping; brighter character |

> **History note:** rev 0.2 specified 5v1 (untested guess) and rev 0.3 mistakenly *removed* the zener entirely after observing that NLC's 3v9 doesn't pass current in a 2-LED chain. The correct fix was to scale the zener value, not delete the part. The canonical Thomas White / Bergmann / NLC topology *does* include this clamp and we are now putting it back, sized for our actual LED chain.

#### Future populate option: per-LED 47Ω series resistor
For the future LCR-0202 experimental path (cheap Senba single-LDR vactrol), add 47Ω in series with each LED in the chain — per the LCR-0202 user-experience consensus (anti-self-oscillation-distortion). **Not populated for the VTL5C3 day-one build** (NLC/Bergmann don't include it for the VTL5C3 path). Designator R_LED_A1 / R_LED_A2 (and channel B mirror) reserved if a future PCB revision wants the footprint; on the breadboard, leave a wire bridge in the LED-cathode-to-LED-anode jumper position and replace with 47Ω only if pursuing the LCR-0202 build path.

---

### BLOCK 6 — Mix Output Buffer (shared)

**Confidence: PROVEN.** Standard inverting summer — same as the kick drum's output handling.

| Component | Value | Pin 1 | Pin 2 | Pin 3 |
|-----------|-------|-------|-------|-------|
| R23 | 100K | CHA_OUT | MIX_BUS | — |
| R26 | 100K | CHB_OUT | MIX_BUS | — |
| R24 | 100K | MIX_BUS | DA4A_OUT (feedback) | — |
| R28 | 100K | DA4A.+in (pin 3) | GND | — |
| DA4A (TL072) | — | GND (+in via R28) | MIX_BUS (-in, pin 2) | MIX_OUT (out, pin 1) |
| C17 | 100nF | MIX_OUT | XS9 (jack tip) | DC blocking |

Each input gain = -R24/R23 = -1 (unity, inverted polarity). Inverted output is acceptable; if needed, a unity-inverter can be added in v2.

DA4B is **spare** for L7 resonance feedback amp or L4 DAMP coupling.

---

### BLOCK 7 — Per-channel status LEDs (parallel branch off driver, panel-side)

> **Layout note (rev 0.7):** R_STATUS_A and R_STATUS_B are **panel-side parts**, soldered in-line on the pigtail between the DRV_OUT_X breadboard exit point and the LED cathode lead. They are not placed on the n8synth breadboard. The on-board attempt to place R_STATUS_B at row 31L col a in rev 0.5 created a short with the CHA_OUT mix-bus tap-jumper that lands on the same row; moving the resistors to the panel resolves it and matches the conventional Eurorack DIY pattern for LED current-limit resistors.



**Confidence: ADAPTED from Doepfer A-101-2.** Doepfer puts their status LED *in series* with the vactrol LEDs so it shows the actual current. We came close to copying that, but ran into a real problem: with 2-LEDs-in-series vactrol arrangements + various LED colours (green/blue/white DIY shrouds have Vf ~3V each), the cumulative Vf budget can starve the chain. So we put the status LED in a **parallel branch** off the driver output — its brightness still reflects driver level, but its current is independent of which vactrol LEDs you've populated.

Already specified inline in Block 5 — repeated here for clarity:

| Component | Value | Pin 1 | Pin 2 |
|-----------|-------|-------|-------|
| R_STATUS_A | 4K7 | DRV_OUT_A | LED_STATUS_A (cathode) |
| LED_STATUS_A | 5mm red | LED_STATUS_A (cathode, from R_STATUS_A) | LED_STATUS_A.anode (to VD7) |
| VD7 | 3V3 zener | LED_STATUS_A.anode (zener anode) | GND (zener cathode, banded) |
| R_STATUS_B | 4K7 | DRV_OUT_B | LED_STATUS_B (cathode) |
| LED_STATUS_B | 5mm red | LED_STATUS_B (cathode, from R_STATUS_B) | LED_STATUS_B.anode (to VD8) |
| VD8 | 3V3 zener | LED_STATUS_B.anode (zener anode) | GND (zener cathode, banded) |

Polarity: cathode towards driver (which goes negative), anode to GND **via the VD7/VD8 threshold zener**. The status LED is now a parallel branch of `LED → R_STATUS (4K7) → driver` with a `3V3 zener` in the ground leg, so it only conducts once the driver swings past ~Vf_LED + 3.3 ≈ 5.2V. Below that (the MANUAL baseline, quiet passages) it stays dark; above it the LED comes on and brightens with drive — a punchy strike/peak indicator rather than a constant glow. Full-drive current ≈ (10 − 1.9 − 3.3)/4K7 ≈ 1.0mA. (Bench-confirmed; rev 0.19.)

---

### BLOCK 8 — Power Supply Rails

**Confidence: PROVEN.** Same scheme as the kick drum.

| Component | Value | Pin 1 | Pin 2 |
|-----------|-------|-------|-------|
| XP1.+12V → VD3 (1N5819) | — | XP1.+12V (anode) | VCC_PROT (cathode) |
| VD3 → R40 (10R) → VCC | — | VCC_PROT | VCC |
| C1 | 47µF | VCC | GND |
| C3, C5, C7, C9 | 100nF | VCC (each near IC pin 8) | GND |
| XP1.-12V → VD4 (1N5819) reverse | — | VEE_PROT (anode) | XP1.-12V (cathode) |
| VEE_PROT → R41 (10R) → VEE | — | VEE_PROT | VEE |
| C2 | 47µF | GND | VEE |
| C4, C6, C8, C10 | 100nF | GND | VEE (each near IC pin 4) |

---

## OPEN QUESTIONS FOR REV 0.4

1. **LED current target & zener final value.** Default-populated 6v8 gives ~7.7 mA into a 2× VTL5C3 chain — well inside VTL5C3's 0–20 mA range and above the ~4 mA NLC implies for single-LED VTL5C3/2. Bench-test by socket-swapping 6v8 / 9v1 (and 3v9 with one LED bridged for direct NLC-stock comparison). Final R6/R12 value can also shift (220R alternates are in BOM).
2. **Block 5 driver polarity.** I went with inverting summer + LED-cathode-to-driver. Could equally well do non-inverting summer + LED-anode-to-driver — either works, the inverting version is slightly fewer components. Final pick can wait until breadboard.
3. **Strike gain into summer.** Set at -1× currently (R34 = 10K, same as feedback). This means a 12V strike pulse drives the LED to the same peak as a +5.6V CV input. Might want to weight the strike *higher* than CV (e.g. R34 = 4K7 for -2.1× gain) so percussive ping is more aggressive than sustained CV. Bench tunable.
4. **R_α value on PCB switching for L5.** Aalto VCA mode = 5K. Doable as a fixed resistor switched parallel to R3/R9 via the mode switch. Leave PCB pads.

---

## STAGE PROGRESSION CHECKLIST

This netlist is rev 0.4. Before moving to Stage 4 (breadboard placement) we want:
- [x] Order parts for the BOM (completed — vactrols + LDR pack ordered; **follow-on small order needed for VD5/VD6 zeners**)
- [ ] Bench measurement of actual VTL5C3 LED-to-LDR-resistance curve → confirms 6v8 zener gives sufficient open-state behaviour, or whether to swap to 9v1
- [ ] Block 5 driver polarity decision (inverting vs non-inverting summer) — can confirm on bench during channel A build
- [ ] User review: confidence tags read as accurate; no missed features

**Follow-on parts order (small):**
- 3× zener: 3v9, 6v8, 9v1 (qty 2 each + spares; 1/2W 5%; e.g. BZX55C-series, Mouser/Farnell)
- 2× 8-pin or 2-pin DIP socket for VD5/VD6 (or use machined-pin SIP singles for in-PCB zener swap)
- 2× spare VTL5C3 (since 4 in hand = exactly 2 per channel, zero spares)
- Optional: 4× 47Ω 1/4W for future LCR-0202 experimental populate path

Blocks 1, 2, 3, 6, 8 (PROVEN) can proceed straight to breadboard placement. Blocks 4 and 5 (ADAPTED/SKETCHED) benefit from a bench-test session first.

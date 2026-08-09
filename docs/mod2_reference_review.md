# MOD2 — Reference Review

**Module:** n8synth 6HP breadboard build of the HAGIWO MOD2 — a **dual-firmware-compatible**
board that runs both the HAGIWO/modulove MOD2 firmwares *and* the WGD Modular Melon firmwares
**unmodified**, with two hardware departures from the original: **local +5V regulation** and a
**dual indicator** (plain LED + WS2812B).

**Scope:** hardware only. **No firmware modifications.** The deliverable is a board plus a guide
to loading the existing published firmwares. First target voice is the **MOD2 LFSR Snare**.

**Status:** Stage 1 — reference review complete, decisions locked. Netlist next.

**Naming note:** `snare_drum_*` in this repo is the *MKI x ES* analog snare. This is an unrelated
digital module and uses the `mod2_*` prefix throughout.

---

## Why this module

- A spare 6HP slot in the rack wants a snare.
- The MOD2 is CC0 — schematic and firmware are both unencumbered.
- It exercises the breadboard tooling on a *mixed-signal* design for the first time. The analog
  content (CV conditioning, gate conditioning, PWM reconstruction, output amp) is ~50 parts —
  comparable to the dual LPG — but the payload is digital.
- It is the first build to drive the new board profiles in `tools/visualizer/boards/`.
- **One board, ~30 published voices.** That is the story worth telling.

The hardware is audio-limited by design (8/10-bit PWM, no DAC) — fine for drums, which is the point.

---

## Headline finding — one board runs both firmware families

The MOD2 and Melon firmware families use **identical pin assignments**. Verified by diffing
matched pairs from both repos:

| Panel | Pin | MOD2 | Melon |
|---|---|---|---|
| POT1 | A0 | ✓ | ✓ |
| POT2 | A1 | ✓ | ✓ |
| POT3 | A2 | ✓ | ✓ |
| IN1 | GPIO7 | ✓ | ✓ |
| IN2 | GPIO0 | ✓ | ✓ |
| CV | A2 (shared with POT3) | ✓ | ✓ |
| OUT | GPIO1 | ✓ | ✓ |
| BUTTON | GPIO6 | ✓ | ✓ |
| **LED** | **GPIO5** | **plain LED, digital or PWM** | **WS2812B (`Adafruit_NeoPixel`)** |

The Melon sources are the MOD2 sources with the LED block replaced by an
`Adafruit_NeoPixel(1, 5, NEO_GRB + NEO_KHZ800)` driver. `fm_drum` differs by 5 lines
(comment typo fixes) and was never converted at all. `kick`'s MOD2 header comment says
`OUT D11`, corrected to `D1` in the Melon copy — a doc typo; both compile to GPIO1.

⚠️ **Verified across the drum/audio voices** (snare, kick, clap, hihat, fm_drum, vco) — those
are pin-identical. **`tides` is an exception worth checking**: its header claims `OUT D7` and
`BTN D4`, which would collide with IN1 (GPIO7) on the MOD2 map. Given the `kick` header carried
a similar error, this is *probably* another stale comment — but `tides` is also absent from the
`build_release.yml` matrix despite appearing on the web flasher, so treat it as unconfirmed
until tested. The headline claim holds for the voices that matter to this build.

**Therefore GPIO5 is the entire hardware delta between the two families.** Populating *both*
indicator types yields a board that runs either, unmodified. See Departure 2.

### Firmware availability (matters for the build guide)

| | MOD2 (modulove) | Melon (wgd-modular) |
|---|---|---|
| Voices | **19** incl. **snare**, spiral, tides, flux, laser, mod303, breakbeats | 14 incl. RALPS, drums, fxloperformer, reese_bass |
| Prebuilt `.uf2` | **Yes** — CI builds 16; browser flasher at [dl.modulove.io/mod2](https://dl.modulove.io/mod2/) | **Yes** — GitHub release v1.3.0 ships 12 `.uf2` files |
| Indicator | Plain LED | WS2812B |

**A prebuilt snare binary exists**, at `https://dl.modulove.io/releases/MOD2_snare.uf2` —
verified as a genuine RP2350 ARM-S UF2 (294 image blocks + partition table, base 0x10000000).

⚠️ **It is not listed in the web flasher UI.** The `build_release.yml` matrix compiles 16
firmwares, but the flasher page exposes only 13 — `snare`, `laser`, `metal` and
`retro_game_kick` are built and downloadable by direct URL but not linked. Worth documenting
in the build guide, since the headline voice is one of the unlisted ones.

Three loading paths exist, in ascending order of effort:
1. **Browser flasher** — [dl.modulove.io/mod2](https://dl.modulove.io/mod2/), WebSerial, no
   local tooling. Covers the 13 listed voices.
2. **Drag-and-drop `.uf2`** — BOOTSEL, drop the file on the `RP2350` drive. Covers all 16 MOD2
   builds (including the unlisted snare) and the 12 Melon releases.
3. **Arduino IDE compile** — only needed for voices with no published build, or to modify.
   Barrier is genuinely low: `snare.ino` pulls **no external libraries** (only `Arduino.h`,
   `math.h` and Pico SDK headers bundled with the `arduino-pico` core). Official build is
   `arduino-cli compile -b rp2040:rp2040:seeed_xiao_rp2350`. Melon sources additionally need
   `Adafruit_NeoPixel` — one Library Manager click.

RALPS (CC BY-NC-SA 4.0) is a third option — 16 engines including a SNARE, with a boot menu to
select LED type. Not part of this build; noted as an optional extra for the bench.

---

## Provenance and licence

| Artefact | Source | Licence | Our use |
|---|---|---|---|
| MOD2 hardware design | [HAGIWO note.com article](https://note.com/solder_state/n/nce8f7defcf98) | **CC0 1.0** | Derive freely |
| MOD2 Rev A schematic | Same article; also `Hardware/MOD2_Circuit.jpg` in modulove/MOD2 | **CC0 1.0** | Derive freely |
| MOD2 firmwares (19) | [modulove/MOD2](https://github.com/modulove/MOD2) | **CC0 1.0** (stated in file headers) | Use as published |
| Melon firmwares (14) | [wgd-modular/melon-firmwares](https://github.com/wgd-modular/melon-firmwares) | Per-file; MOD2-derived | Use as published |
| Snare demo | [MOD2 Snare — HAGIWO](https://www.youtube.com/watch?v=5JEPAUoVCC8) | — | Reference only |
| RALPS (optional) | [mxzrmxzrmxzr/RALPS](https://github.com/mxzrmxzrmxzr/RALPS) | CC BY-NC-SA 4.0 | Optional extra, not in this build |
| WGD Modular Melon *hardware* | [wgdmodular.de](https://wgdmodular.de/module/melon/) | Commercial product | **Ideas only — not copied** |

**Two deliberate boundaries, consistent with the repo's stance on MKI x ES material:**

1. HAGIWO's **gerbers/manufacturing data are Patreon-paid**. We do not redistribute them.
   Nothing here needs them — this is a breadboard build from the published CC0 schematic.
2. The **Melon is a product wgdmodular sells.** It independently arrived at local 5V regulation
   and an RGB indicator. We take those two *ideas* and derive our own implementation from the
   CC0 MOD2 baseline. We do not copy their board, BOM or layout. Their *firmware* is published
   for public use and we consume it as-published, unmodified.

---

## Hardware baseline — MOD2 Rev A decoded

Read from the published schematic (KiCad 7.0.6, `Title: MOD2`, `Rev A`, dated 2025MAR29).
Every value below is corroborated by the article's JLCPCB BOM, which also confirms **C15 is DNP**
(drawn crossed-out, absent from the BOM).

**MCU:** Seeed XIAO RP2350. Free pins: **GPIO2, GPIO3, GPIO4** (marked unused on the schematic).

### Power
- 16-pin header J1. D1/D2 (1N4148WS) reverse-polarity protection on ±12V.
- Decoupling: C1 10µ + C4 100n on +5V; C5 10µ, C7/C9 100n on +12V; C6 10µ, C8/C10 100n on −12V.
- **U1, U2 (TL072CDT) run on ±12V.**
- **+5V arrives straight from the bus** → XIAO 5V pin → the XIAO's onboard LDO → +3.3V.
- That 3.3V rail is **the pot supply and the ADC reference**. See Departure 1.

### Pots and CV
- RV1/RV2 (100k) across +3.3V/GND → R1/R2 10k → A0/A1, with C2/C3 100n to GND.
- RV3 (100k) → R5 10k → **U1A unity-gain follower** → R9 10k ↘
- CV jack J2 → R3 10k + R4 100k, R6 220k to GND. Divider = 220/330 = **×0.667**
  (0–5V CV → 0–3.33V) → **U1B unity-gain follower** → R10 10k ↘
- **U2A inverting summer**: Rf = R15 10k; POT3 and CV sum at the inverting node; R11 33k + R14 1k
  (34k) injects an offset from **−12V**.

  **A2 ≈ 3.53 − POT3 − CV** — hence 5V CV reads 0V, 0V CV reads 3.3V.
  The snare firmware header independently documents POT3 as *"reversed ADC"*. ✓
- Output R16 1k → A2, C12 22n to GND, D7/D8 (B5819W) clamping to +3.3V/GND.

### Gate inputs
- J3 (IN2) → R7 4.7k pulldown, R12 3.3k series → **GPIO0**, D3/D4 (B5819W) clamps.
- J4 (IN1) → R8 4.7k pulldown, R13 3.3k series → **GPIO7**, D5/D6 clamps.
- 3.3k + 4.7k = **8k total pulldown**, per the RP2350 pulldown errata.

### Audio output
- GPIO1 → **two-pole RC reconstruction filter**: R17 1k, then R19 1k.
  - Pole 1 shunt: C13 10n (fixed) + C14 22n (switched). Pole 2 shunt: C16 10n (fixed) +
    C17 22n (switched). C15 10n is **DNP**.
- C18 1µ AC-couple → R20 100k bias to GND → **U2B non-inverting amp**.
  - **Gain = 1 + R22 68k / R21 33k = 3.06.**
  - 3.3 Vpp PWM × 3.06 ≈ **10.1 Vpp** — this is the origin of the published 10V spec.
- R23 1k → output jack J6.

### The two jumpers

Traced pin-by-pin from the schematic. **There are two, and they do different jobs.**

**JP1 — `Jumper_3_Open`, 3-pin — reconstruction filter cutoff**

| Pin | Connects to |
|---|---|
| 1 | node after R19, **through C15 (DNP)** — so effectively floating |
| 2 | GND |
| 3 | common bottom node of **C14 22n + C17 22n** |

- **Jumper on 2–3** → C14/C17 grounded → 32n per pole → **Fc ≈ 5.0 kHz** (bass/kick)
- **Jumper on 1–2, or absent** → C14/C17 float → 10n per pole → **Fc = 15.9 kHz** (bright/snare)

Position 1–2 grounds C15's bottom plate, but since C15 is not fitted it does nothing — it is a
provision for an alternative filter option, not a third setting. Functionally JP1 is a
**two-state control**, matching the article's "MCU side / power-connector side" description.

**JP2 — `SolderJumper`, 2-pin — output coupling**

Wired **directly in parallel with C18 (1µ)**.

- **Open** → C18 active → **AC-coupled**. High-pass with R20 100k at ~1.6 Hz; output swings
  ±5 V about 0 V. Normal audio behaviour.
- **Closed** → C18 shorted → **DC-coupled**. Output becomes unipolar **0 → ~9.9 V**
  (PWM average 0–3.3 V × 3.06, less the slight R20 divider loss).

⚠️ This is not an audio nicety — it changes the module between an **audio output** and a
**CV/envelope output**. `tides` in particular has LOOPING (LFO), AD and AR envelope modes whose
low-frequency content would droop badly through a 1.6 Hz high-pass.

### Indicator and switch
- GPIO5 → R24 3.3k → D9 (LED) → GND. ~0.5 mA — dim by design.
- SW1 → GPIO6 (internal pull-up), with R18 1k + C11 100n debounce.

### Parts summary (breadboard)
2× TL072, 1× XIAO RP2350, ~24 resistors, ~20 capacitors, 6× B5819W + 2× 1N4148WS,
3× 100k pots, 4× 3.5mm jacks, 1× tactile switch, indicators. Plus our two departures.

---

## Departure 1 — local +5V regulation

**Problem.** The n8synth's +5V comes from the Eurorack PSU and is too noisy for this use.
On the stock MOD2 that rail feeds the XIAO, whose onboard LDO derives +3.3V — and that 3.3V
is simultaneously the **pot supply and the ADC reference**. Bus noise therefore lands directly
on control-voltage measurement, not merely on a digital supply.

**Decision: 7805 from +12V, with datasheet-typical decoupling.**

| Option | Verdict |
|---|---|
| **7805 from +12V** | **Chosen.** Already on hand. Linear regulation is quiet, which is the whole point given the rail feeds the ADC reference. Simplest thing to build on a breadboard. |
| Buck from +12V | Matches usual rack practice and runs cool — but injecting switching noise into the ADC reference rail is precisely the failure we are removing. Would need an LC post-filter and a scope check to prove. |
| Low-noise LDO (LP2992 / TLV1117) | Better PSRR and lower dropout, but a part not on hand, for marginal benefit at this current. |
| Bus +5V (stock) | The problem being solved. |

**Decoupling: datasheet values — 0.33 µF input, 0.1 µF output.** (Decided in favour of
datasheet over reusing the MOD2's 10µ/100n house pattern; the regulator's stability spec is
the thing that matters here, and the MOD2's own C1 10µ + C4 100n remain downstream on the
5V rail regardless.)

**Thermal check.** XIAO ~65 mA + 2× TL072 ~6 mA — derived from Melon's published draw
(+12V 72 mA, −12V 8 mA). Dissipation = (12 − 5) × 65 mA ≈ **0.46 W**. A bare TO-220 in free
air (θJA ≈ 65 °C/W) gives roughly a **30 °C rise** — no heatsink needed.

⚠️ A WS2812B at full white (up to 60 mA) roughly doubles this to ~0.9 W / ~58 °C rise. Warm but
survivable; the published firmwares run the pixel well below full white. **To confirm on the
bench** — if it runs hot, a small clip-on heatsink is the fix.

The bus +5V pin is left unconnected.

---

## Departure 2 — dual indicator (plain LED + WS2812B)

**Decision: populate both indicator types on GPIO5.**

This is what makes the board dual-firmware-compatible with **no software tweaks**:

| Firmware family | Plain LED | WS2812B |
|---|---|---|
| MOD2 (HAGIWO/modulove) | **Works** — digital or PWM indication | Stays dark — never receives valid 24-bit data |
| Melon (wgd-modular) | Effectively dark — see below | **Works** — full colour indication |

**The two use incompatible signalling, so whichever does not match the loaded firmware simply
stays off.** A plain LED driven by NeoPixel data sees ~30 µs bursts at a typical refresh rate —
well under 1% duty cycle — so it reads as dark rather than flickering. If any residual glow
proves distracting, lift one LED leg; it is a breadboard.

Electrically benign in both directions: the WS2812B `DIN` is a high-impedance CMOS input, and
the plain LED branch draws ~0.5 mA through R24 3k3 — well inside the RP2350's drive capability,
and far too light to disturb NeoPixel signalling.

*(This is the same conclusion the Melon reaches with its dual LED footprint, though it intends
either/or population. On a breadboard, both is free.)*

### Part choice — and a trap to avoid

⚠️ **Do not use a 5mm through-hole NeoPixel**, despite it being the obvious mechanical fit
(4 legs, mounts like the plain LED beside it). Adafruit's own description states:

> *"Note that these are **'RGB' instead of the 'GRB' format** used in the 5050-sized LEDs"*

The Melon firmwares declare `Adafruit_NeoPixel(1, 5, NEO_GRB + NEO_KHZ800)`, so a through-hole
part would **swap red and green on every voice** — breaking the no-software-tweaks rule. They
also ship as "either WS2812B or SK6812", so the part is not even deterministic.

**Chosen part: Adafruit NeoPixel Breakout with JST SH Connectors** (Adafruit 5975) —
[Pimoroni](https://shop.pimoroni.com/en-us/products/adafruit-neopixel-breakout-with-jst-sh-connectors)
£1.40, in stock; also at The Pi Hut.

- Carries a **5050 classic NeoPixel → GRB**, matching the firmware. No colour swap.
- **12.3 × 11.3 × 6.2 mm**, with **M2 mounting holes**.
- 3-pin JST SH in/out: GND (black), VIN (red), In (white).

Buy two, so a suspect pixel can be swapped rather than debugged.

**Data threshold.** The *original* WS2812B at 5V wants VIH ≥ 0.7 × VDD = **3.5V**, but the
RP2350 drives **3.3V**. Three ways out, in order of preference:

1. **Run the pixel from +3.3V.** Adafruit state this breakout "can be powered and controlled
   with 3.3V or 5V power". At 3.3V the threshold becomes 0.7 × 3.3 = **2.31V** — the problem
   disappears with no extra parts. *Caveat: the WS2812B datasheet minimum supply is ~3.5V
   (3.7V for V5), so this is below chip spec — it is Adafruit's tested claim for this board,
   not a datasheet guarantee.*
2. **Run from +5V through a series silicon diode** → ~4.3V, which is inside the 3.7–5.3V range
   *and* drops the threshold to ~3.0V. Fully in spec, one extra part. **Most defensible.**
3. **Specify a WS2812B-V5** (VIH ~2.7V) and run at 5V — clean, but you must verify the
   revision actually shipped.

The netlist carries option 2 as the default (D10), since it is in spec and costs one diode;
link out D10 to fall back to option 1 or 3 at the bench.

**Mounting.** This is a board, not a panel LED — it will not drop into a JPS cell footprint the
way a 5mm LED does. Mount it behind the panel on M2 standoffs with a hole or light pipe, and
solder wires directly to the pads rather than fighting 1 mm JST SH connectors. Electrically it
is still three connections, so the 12-of-12 cell budget is unchanged.

**Bare parts for a later PCB:** SK Pang Electronics and Switch Electronics stock WS2812B in the
UK; TME lists the WS2812B-V5 explicitly. All 5050 SMD — they need a carrier.

**Build order.** Bring the board up with the **plain LED and a MOD2 firmware first** — that
proves pots, gates, CV and audio without the pixel's timing risk in play. Add the WS2812B and
a Melon `.uf2` as a separate, later step, so a data-threshold problem can never be confused
with a hardware fault elsewhere.

**Panel cost: zero extra cells** — see below.

---

## Departure 3 — both jumpers panel-mounted

Both jumpers are firmware-dependent, and on a board whose whole purpose is running ~30 different
voices, both belong on the front panel rather than as solder blobs on the back:

| | Stock MOD2 | This build |
|---|---|---|
| **JP1** — filter cutoff | 3-pin jumper on PCB | **Panel SPST toggle** |
| **JP2** — output coupling | solder jumper on PCB | **Panel SPST toggle** |

**JP1 as a panel switch.** Only two states are real (see above), so an **SPST toggle between the
C14/C17 common node and GND** reproduces both exactly:

- **Closed → 5.0 kHz** — kick, bass, mod303
- **Open → 15.9 kHz** — snare, hihat, clap, and most bright voices

Two terminals: one to the C14/C17 common node, one to the deck ground bus. **Pads A + D.**

**JP2 as a panel switch.** An **SPST across C18**:

- **Open → AC-coupled**, ±5 V audio (default for every drum voice)
- **Closed → DC-coupled**, 0–9.9 V unipolar — for LFO/envelope firmwares

Both terminals are signal here, neither is ground. **Pads A + B.**

This is what turns "one board, ~30 voices" from a claim into something usable at the rack:
flash a different `.uf2` and set two front-panel switches to match, with no tools and no
re-soldering. Panel cost is exactly the two spare cells — see below.

---

## n8synth 6HP control deck mapping

The 6HP deck is `n8-cd-6hp-2x6`: a 2×6 physical grid of 12 JPS cells, but **`strips: 1`** — so
all 12 serialise onto the **left-hand strip (`ctrlL`) only**. (The 10HP profile is the one that
splits across `ctrlL`/`ctrlR`, which is what the LPG layout uses.)

| JPS cell | Rows (A / B / C) | JPS cell | Rows (A / B / C) |
|---|---|---|---|
| JPS1 | 1 / 2 / 3 | JPS7 | 23 / 24 / 25 |
| JPS2 | 4 / 5 / 6 | JPS8 | 26 / 27 / 28 |
| JPS3 | 7 / 8 / 9 | JPS9 | 29 / 30 / 31 |
| JPS4 | 10 / 11 / 12 | JPS10 | 32 / 33 / 34 |
| JPS5 | 13 / 14 / 15 | JPS11 | 35 / 36 / 37 |
| JPS6 | 16 / 17 / 18 | JPS12 | 38 / 39 / 40 |

Rows **19–22 are gap rows** — no JPS pad, so they are free feed-through tie points.

Each cell carries pads **A/B/C** (2 solder points each) plus **D**, on the **deck-wide ground bus**.

**All 12 cells are available.** The deck is a 2×6 physical grid, parsed from the official
template. Note that `layoutRows` [1, 36] and `powerSectionRows` [37, 40] in the board profile
describe the **breadboard**, not the deck — JPS11.C and JPS12 mapping to rows 37–40 affects how
those pads are *routed* (they land alongside the breadboard's power section), not whether the
panel positions exist.

**One cell = one physical component footprint** (`jps-h-a/b/c/d` in the templates), not four
free pads. Two physically separate indicators therefore need two cells.

### Panel allocation — 12 cells of 12

| Panel item | Cells | Pads |
|---|---|---|
| RV1, RV2, RV3 (100k pots) | **3** | 3 legs → A/B/C |
| J2 CV, J3 IN2, J4 IN1, J6 OUT | **4** | tip → A, switch → B, sleeve → **D** |
| SW1 push switch | **1** | one side → A, return → **D** |
| Plain LED (MOD2 firmwares) | **1** | anode → A (via R24 3k3), cathode → **D** |
| WS2812B (Melon firmwares) | **1** | +5V → A, DIN (GPIO5) → B, GND → **D** |
| **JP1 toggle** — filter cutoff | **1** | C14/C17 common → A, GND → **D** |
| **JP2 toggle** — output coupling | **1** | C18 left → A, C18 right → B |

**Total 12 of 12 cells — exactly full.**

Both indicators sit on the same GPIO5 net, wired from the breadboard to two adjacent deck cells.

⚠️ **The panel is now full**, so any further panel feature displaces something. Worth knowing
before layout: there is no longer slack for an extra jack or control.

MOD2 is a 4HP module; building it in 6HP is a deliberate luxury — the extra room is what makes
the breadboard tractable and leaves headroom for the 7805 and its capacitors.

---

## Open questions for Stage 2 (netlist lock)

1. ~~7805 decoupling values~~ → **Resolved: datasheet, 0.33 µF in / 0.1 µF out.**
2. **Does the XIAO's 3.3V rail need extra local decoupling** on a breadboard, beyond the stock
   C19 100n / C20 10µ? Breadboard parasitics are worse than a PCB.
3. ~~JP1 jumper or hard-wired~~ → **Resolved: keep the jumper.**
4. **Confirm JPS11/JPS12 usability** physically against the power section.
5. **Bench-verify the 7805 thermal figure** with the WS2812B lit.
6. ~~Confirm the WS2812B data threshold~~ → **Resolved by part choice: specify WS2812B-V5**
   (VIH ~2.7V). Verify the revision actually shipped before assuming it.

## Stage 2 deliverable

`docs/mod2_netlist.md` — full netlist with named nets and per-source confidence tags, in the
same form as `lpg_netlist.md`, ready for `netlist_to_layout.py`.

## Later deliverable — firmware loading guide

Hardware-only build, but the journey ends at "load the firmware". Because the pin maps match,
**one board covers ~30 published voices across both families** — that is the guide's headline.

- **Browser flasher** — [dl.modulove.io/mod2](https://dl.modulove.io/mod2/), WebSerial, nothing
  to install. Easiest path; covers 13 MOD2 voices.
- **Drag-and-drop `.uf2`** — BOOTSEL, drop on the `RP2350` drive. Covers all 16 MOD2 CI builds
  (including the **unlisted snare**, direct URL) and the 12 Melon releases.
- **Arduino IDE compile** — only for voices with no published build, or to modify. Low barrier:
  install the `arduino-pico` core, select Seeed XIAO RP2350, upload. `snare.ino` needs no
  external libraries; Melon sources need `Adafruit_NeoPixel`.
- **Indicator behaviour** — explain that the LED that matches the loaded firmware lights and the
  other stays dark. This is expected, not a fault.
- **Panel switch settings per firmware** — a lookup table is the single most useful thing the
  guide can carry, since both switches are firmware-dependent:

  | Voice | JP1 filter | JP2 coupling |
  |---|---|---|
  | snare, hihat, clap, claves, metal | 15.9 kHz (open) | AC (open) |
  | kick, retro_game_kick, mod303, reese_bass | 5.0 kHz (closed) | AC (open) |
  | tides (LFO / AD / AR modes) | either | **DC (closed)** |
  | braids, vco, radio, sample | 15.9 kHz (open) | AC (open) |

  To be confirmed by ear at the bench — this is a starting table, not measured data.
- ⚠️ HAGIWO's warning: **disconnect Eurorack power before connecting USB**, to avoid
  back-powering the rail through the host port.

---

## Sources

- **HAGIWO MOD2** — [note.com article](https://note.com/solder_state/n/nce8f7defcf98) (CC0) — design rationale, Rev A schematic, JLCPCB BOM, RC jumper detail
- **MOD2 firmware collection** — [modulove/MOD2](https://github.com/modulove/MOD2) — 19 firmwares including `snare`; `Hardware/MOD2_Circuit.jpg`
- **Melon firmware collection** — [wgd-modular/melon-firmwares](https://github.com/wgd-modular/melon-firmwares) — 14 firmwares, prebuilt `.uf2` releases
- **MOD2 Snare demo** — [HAGIWO, YouTube](https://www.youtube.com/watch?v=5JEPAUoVCC8)
- **Seeed XIAO RP2350** — [wiki.seeedstudio.com](https://wiki.seeedstudio.com/xiao_rp2350_arduino/)
- **WGD Modular Melon** — [wgdmodular.de](https://wgdmodular.de/module/melon/) — independent precedent for local 5V regulation and an RGB indicator (ideas only)
- **RALPS** — [mxzrmxzrmxzr/RALPS](https://github.com/mxzrmxzrmxzr/RALPS) — CC BY-NC-SA 4.0, 16 engines incl. SNARE; optional extra

Reference material is linked at source rather than redistributed, per repo convention
(`docs/refs/` is gitignored).

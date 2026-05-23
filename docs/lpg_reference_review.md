# Low Pass Gate (LPG) — Reference Review

**Status:** Stage 0 working notes for a new dual-channel LPG module.
**Target platform:** n8synth solderable breadboard (same workflow as the kick drum).
**Goal of this doc:** Survey reference schematics and topologies, decide on a target feature set, pick vactrol parts, and lay the groundwork for the netlist (Stage 2).

---

## What is a low pass gate?

A low pass gate is a single circuit element that *simultaneously* attenuates amplitude and rolls off high frequencies as a control voltage decays. Originally Buchla 292. The "magic" comes from a vactrol — an LED packaged with a light-dependent resistor (LDR) — used as the variable element in both an RC low-pass and a series attenuator. Because the LDR is slow to respond to the LED, the envelope shape has a characteristic "natural" decay that's hard to replicate with VCAs and VCFs.

Three common modes:
- **LP** — vactrol controls cutoff only (signal always passes through)
- **VCA / Gate** — vactrol controls amplitude only (no filtering)
- **Both / Combo** — vactrol does both at once (the canonical LPG sound)

---

## Reference videos (user-supplied)

1. **"Exploring low pass gates with the MAKE NOISE LxD"** — `https://www.youtube.com/watch?v=OEgjmd6qOlQ`
   - LxD is the simpler 2HP sibling of Optomix: dual channel, vactrol-based, but **no Strike input and no DAMP control**. Same core LPG element.
2. **"DIY eurorack modular synth Low pass gate for percussion with cheap vactrol made in China"** — `https://www.youtube.com/watch?v=1aN8pdPeQWk`
   - Minimal DIY LPG using LCR0202-style cheap vactrol, optimised for percussive use.

---

## Topology candidates

| Module | Channels | Modes | Pingable | CV in | Vactrols | Notes |
|---|---|---|---|---|---|---|
| **Buchla 292** (canonical) | 4 (in module) | LP / Both / VCA switch per channel | Via signal in | Yes | 1 dual-LDR vactrol/ch | The grandfather. Big BOM. |
| **Make Noise Optomix** ⭐ | 2 | "Both" only (no switch) | **Yes — Strike input** | Yes | 4 single-LDR vactrols (2/ch) | DAMP knob couples channels. Target reference. |
| **Make Noise LxD** | 2 | "Both" only | No | No | 2 vactrols | Stripped Optomix. Video 1's subject. |
| **Doepfer A-101-2** | 1 | LP / Both / VCA switch | Via CV | Yes | 1 vactrol | Simple, well-documented schematic. |
| **ST Modular Workmates LPG** | 1 | Passive only | No | Yes (passive) | 1 molded vactrol | Passive, 0HP. Not what we want, but the simplest possible reference. |
| **ST Modular Rocinante's Gate** | 1 | Simulated | No | No | **None — op-amp simulated** | Not a true LPG; simulates the curve with an envelope through a filter. |
| **Cheap-Chinese-Vactrol DIY** (video 2) | 1 | "Both" only | Yes | Yes | 1 LCR0202 | Bare-bones, percussive. |

⭐ = chosen target topology.

---

## Optomix detail (target topology)

From the Make Noise manual and reverse-engineering writeups:

- **2 independent channels.** Each channel is signal-in → vactrol-controlled VCFA → signal-out.
- **4 vactrols total** — Optomix uses two vactrols per channel. One vactrol acts as the variable resistor in the low-pass RC, the other as the variable shunt for the VCA action. This is what gives Optomix its richer, less "pinched" response vs the single-vactrol LxD.
- **CONTROL knob + CV input** (per channel) drive the vactrol LEDs through a current-mode driver (probably an op-amp + transistor stage).
- **STRIKE input** (per channel) is a gate input that pings the vactrol — short pulse fires the LED, the LDR's natural decay produces the envelope. No external EG needed for percussion.
- **DAMP control** sums the two channels' CV-driver currents through a resistor network, shortening the apparent decay when DAMP is high. This is the "applying your hand to the drum head" effect.
- **Output mixer** sums channel A and channel B to a single OUT (with separate per-channel OUTs as well).

Op-amps in the original are likely a TL072-class JFET-input dual op-amp for the audio path and a general-purpose dual (LM358 / TL072) for the vactrol drivers. The exact part numbers don't matter much for our build — we'll use TL072 throughout for consistency with the kick drum.

---

## Vactrol options

We've already established a preference for buying parts but keeping a DIY/swappable path open.

### Option A — molded Senba LCR0202 (slow / classic)
- Cheap (~$1–2 each on AliExpress / JLC)
- Bright (on) resistance: 50 Ω – 1 kΩ at 20 mA drive
- Dark resistance: 1–10 MΩ
- Response ~2.5 ms (rise/fall combined; the "slow tail" comes from LDR thermal/photo lag, typical 30–100 ms at low currents)
- Drop-in for VTL5C3 / NSL-32SR2 in most schematics

### Option B — molded Senba LCR0203 (faster)
- Same family, faster response — better for sharp pinged percussion
- Buy a few of each so we can A/B in the same socket

### Option C — DIY hand-built vactrol
- 5 mm green or amber LED (550–600 nm — best LDR sensitivity) + GL5506 or GL5516 LDR
- White heatshrink between (diffuse, light coupling), black heatshrink over (ambient light isolation)
- ~50% part-to-part variation in LDR — selection by measurement is necessary
- Cost: cents

### Option D — DIY socketed / swappable LED ⭐
- Same as C but LED is in a 5 mm socket inside a 3D-printed shroud
- Lets us swap LED colour / Vf / brightness to retune the curve without resoldering
- Build123d can produce the shroud (light-tight, friction-fit LED, LDR press-fit on the opposite face)
- This is the experimental sweet spot — caters to the original "ST design with slot-in LEDs" idea

### Recommendation
Buy 8× LCR0202 + 8× LCR0203 to get the build working quickly with a known-good part. Design the PCB / breadboard footprint so each vactrol position is **8-pin DIP-socketed** (same footprint as the molded Senba parts) so we can later drop in a 3D-printed swappable-LED shell with the same pinout.

> **Note:** I searched the ST Modular catalogue (st-modular.com / carlosedp/STMODULAR-EURORACK GitHub mirror) and found their LPG modules are *Workmates LPG* (passive, molded vactrol) and *Rocinante's Gate* (op-amp simulated, no vactrol). The closest match to "swappable component for experimentation" is the **Clipping Cat**'s diode playground — through-hole socketed diodes on the back of the board for swap-and-listen. We'd apply the same idea but to the vactrol LED. **If you remember a specific ST Modular LPG with explicit socketed LEDs, please point me at the URL and I'll fold it in.**

---

## Proposed feature set for our module

Based on Optomix as target, with the DIY swappable-vactrol idea folded in:

- **2 channels**, each with:
  - Audio in (1 jack)
  - Audio out (1 jack)
  - **Strike** input (gate, pingable)
  - **CV** input (0–8 V, attenuated)
  - **Level** knob (manual offset / DC envelope)
- **DAMP** knob (shared, couples the two channels' decay times)
- **Mix out** (sum of A + B)
- **Mode switch** — *open question*: do we want LP/VCA/Both per channel? Optomix doesn't have one; Buchla 292 does. Adds complexity but a lot of flexibility. Recommend **dropping it** for v1 to keep the BOM and breadboard layout sane, and considering it for a v2.
- **Vactrol sockets** — 8-pin DIP, 4 vactrols total (2 per channel), so we can mix molded Senba parts and DIY swappable shrouds.
- **Width:** target 8HP front panel, but breadboard layout will be the n8synth's native HP — likely two 10HP boards similar to the FM drum, or one 10HP if we can pack tightly.

---

## Open questions for Stage 1 (feature spec lock)

1. **Mode switch?** LP/VCA/Both per channel, or just "Both" like Optomix?
2. **CV input scaling?** Optomix is 0–8 V looking up; do you want bipolar response or attenuverter?
3. **DAMP behaviour?** Optomix DAMP also adds resonance / ring at low values. Do we want that, or pure damping?
4. **Output buffering?** Per-channel buffered out + mix out (3 outputs) or just mix out (1 output)?
5. **Power budget?** Approx ±12 V at <30 mA each side — fine for any eurorack PSU, but worth confirming once op-amp count is locked.
6. **Vactrol count.** Single-vactrol-per-channel (LxD-style, simpler) vs dual-vactrol-per-channel (Optomix-style, richer). Recommend **dual** to honour the Optomix target, but it's the single biggest BOM-and-layout cost driver.

---

## Stage 1 deliverable

When the questions above are resolved, the next doc will be `docs/lpg_netlist.md` — the same format as `kick_drum_netlist_from_text.md`: BOM table, block diagram, designators per block (input buffer, vactrol driver, audio path, Strike pulse-shaper, DAMP coupler, output mixer, power decoupling).

---

---

## Wider survey — additional LPG designs for inspiration

Beyond the original shortlist, surveying the broader landscape turned up several designs worth borrowing ideas from. Grouped by topology family.

### 1. Vactrol classics (Buchla-lineage)

**Buchla 292 / 292c (canonical, multiple DIY clones)**
- 4 channels, **3-mode toggle per channel** (LP / Combo / Gate)
- TL074 quad op-amp, VTL5C3 or VTL5C4 vactrol per channel
- **Self-oscillating resonance** in VCF mode (feedback cap C8)
- LED is *direct-driven* by the CV signal — no current-limiting resistor — which is what gives the slow tail
- CV-2 input has an attenuverter
- See: Eddy Bergman build, NLC clone, NRM Lopass Gate

**NLC Low Pass Gate (Nonlinearcircuits)**
- Buchla 292 clone, 8HP per channel
- Dual-vactrol footprint (VTL5C3/2) per channel
- 3-mode toggle preserved
- Open-source PCB + BOM PDF available

**Pittsburgh Modular LPG**
- 8HP, single channel, **triple-mode** (VCA / LPF / LPG)
- **Sallen-Key 2-pole 12 dB low-pass filter** topology (not an RC vactrol filter — uses op-amp filter with vactrol as the Rs)
- Ping jack for pingable use
- Power: ±12 V at 20 mA

**AI Synthesis AI017 (DIY kit)**
- TL074, 2× VTL5C3
- **Tunable resonance trimmer** (mellow → wild distortion / self-osc)
- ⭐ **Depth control** — A500K pot allows the gate to **fully close** (most LPGs leak signal even at zero CV; this is a small but excellent UX win)
- 3PDT mode switch
- Open kit with full BOM and assembly guide

**Synthrotek LPG (DIY kit)**
- 4HP dual channel, single-vactrol-per-channel (or dual via different jumper)
- VTL5C4 stock; resonance per channel
- ⭐ **Slide pot dual-function**: when CV jack is unpatched, slider attenuates/mixes audio; when CV is patched, slider attenuates output AND modifies timbre. Clever way to fit two functions on one control.

### 2. Vactrol exotics (more vactrols, more modes)

**Make Noise QMMG (Quad Multi-Mode Gate)**
- 24HP, 4 channels, **8 vactrols total** (paired per channel)
- ⭐ **Continuous mode pot** (per channel): VCA → LPG → LPF → HP via a single analog knob — no discrete switch positions. Could be a really nice UX feature for our design.
- Voltage-controlled feedback for resonance / self-oscillation
- Mix out + per-channel out, normalising scheme between channels

**Make Noise Optomix** (target — already covered)
- 8HP, 2 channels, 4 vactrols, Strike + DAMP

**Make Noise LxD** (target's stripped sibling)
- 4HP, 2 channels, 2 vactrols, no Strike, no DAMP — this is the simplest dual-channel "Optomix shape"

### 3. Vactrol-free / "modern feel"

**Rabid Elephant Natural Gate** ⭐
- 12HP dual channel, **transistor-based** — no vactrols
- Marketed as faster, more accurate, durable, and "natural-sounding"
- ⭐ **MATERIAL switch** (3 positions): selects tonal character — like simulating different drum head materials. Could be implemented in a vactrol design by switching the filter cap (similar to Two-Tone's per-channel cap variation).
- ⭐ **Memory effect**: as trigger frequency rises, gates open more — emergent behaviour from envelope topology, gives "rolls" a different character to single hits
- ⭐ **Pitch-dependent decay**: high notes close faster than low notes. Whether this is intentional or a circuit side-effect, it's the kind of detail that makes a module feel alive.

**Noise Engineering Sinc Bucina**
- Vactrol-free, **SSI2164 VCA** for the amplifier section
- DRC (delay-rise-compress?) envelope with vactrol-flavoured temporal nonlinearity baked in
- ⭐ Wider decay range (200 ms – 7 s) than typical vactrol LPGs
- Ping + Gate inputs (Ping = release-only LPG behaviour, Gate = ASR envelope)
- ⭐ Three filter modes: 6 dB resonant LP / no filter (VCA only) / 12 dB resonant LP

**SSLPG (Solid-State LPG, DIY community design)** — referenced; couldn't pull the full thread, but exists as another op-amp + transistor approach.

### 4. Passive / minimalist

**Two-Tone (Ben Moren, GitHub)** — DIY passive
- 2-channel passive LPG/LPF with DIY vactrols
- LDR: GL5549; LED: 5 mm white or blue (3 mm)
- ⭐ **Per-channel cap variation** (0.1 µF – 4.7 µF) gives each side a different sonic character — a passive precursor to the QMMG / Natural Gate "MATERIAL" idea
- 6 jacks, 2 trim pots, 4 resistors, 2 LEDs, 2 vactrols — that's the entire BOM

**Other passive references** (mostly trivially simple — included for completeness):
- Mystic Circuits 0HP Vactrol LPG (passive, no front panel)
- Intellijel Passive LPG 1U (1U tile)
- BeepBoop Electronics LPG V2 (passive)
- ST Modular Workmates LPG (passive, 0HP)

### 5. Adjacent modules worth knowing

**Mannequins Three Sisters** — not an LPG but a triple resonant filter; the LOW filter behaves LPG-ish in some patches. Spectral mixing topology might inspire a future v2 with crossover behaviour.

**Tiptop Audio Buchla 281t** — pingable function generator (4 channels). The classic source for driving a passive LPG, though the doc warns it can't drive third-party passive LPGs because they short the input to ground — useful warning for our output buffering design.

---

## Ideas worth folding into our design

Ranked roughly by how much they'd improve the module vs how much complexity they'd add.

### Strong "yes" for v1
- **AI017's Depth control** — a per-channel A500K pot in series with the Strike/CV drive that allows full closure when at minimum. Cheap, small footprint, solves a well-known LPG annoyance.
- **Two-Tone's per-channel cap variation** — make the filter cap socketed (DIP-2 socket) so we can swap it for tonal experimentation. Mirrors the swappable-LED idea — both let us reshape the response without resoldering.

### Strong "yes" for v2 (note now, defer)
- **QMMG-style continuous mode pot** (VCA → LPG → LPF → HP) instead of a discrete LP/Both/VCA switch. More expressive but adds at least one op-amp per channel for the crossfade, so save it for v2.
- **Self-oscillating resonance** (Buchla 292 / AI017 style). Feedback cap + trimmer. Adds tonal range and sounds great, but adds a calibration step. Defer.

### "Maybe" — pending taste check
- **MATERIAL switch (3 positions)** — switches between 3 fixed cap values per channel for "different drum head" character. Lighter version of the swappable-cap socket. Fine if the swap socket is too fiddly.
- **Sinc Bucina-style ping vs gate distinction** — Strike (release-only) vs Gate (ASR-style envelope) on separate inputs. Optomix uses Strike alone; offering both adds one envelope shaper per channel. Worth weighing against complexity.

### "No" for this project
- **Vactrol-free transistor or SSI2164 topology** (Natural Gate / Sinc Bucina). Defeats the point of building an LPG — the vactrol is the soul of the design, and we want the experimental swappable-LED path which is *only* possible with vactrols. Note for posterity.
- **Triple/quad channel** — Optomix dual is right for the n8synth platform; quad would burst the breadboard.

---

## Updated Stage 1 questions

The new survey adds two more questions to the original six:

7. **Add an AI017-style Depth knob per channel?** (recommend: yes — small cost, big UX win)
8. **Make the filter cap socketed for tonal swapping?** (recommend: yes if there's room; adds one DIP-2 socket per channel)

Everything else (mode switch, CV scaling, DAMP behaviour, output count, vactrol count per channel) is unchanged from the earlier list.

---

## Sources

### Target reference
- [Optomix product page — Make Noise](https://www.makenoisemusic.com/modules/optomix/)
- [Optomix Rev 2 manual PDF](https://www.makenoisemusic.com/wp-content/uploads/2024/03/optomixrev2manual.pdf)
- [Optomix CREATE teaching synth manual PDF](https://w2.mat.ucsb.edu/mat276n/resources/systems/CREATE_teachingSynth/manuals/17_Optomix.pdf)

### Other commercial LPG references
- [Pittsburgh Modular LPG product page](https://pittsburghmodular.com/lpg)
- [Make Noise QMMG (Perfect Circuit)](https://www.perfectcircuit.com/make-noise-qmmg-2024.html)
- [Rabid Elephant Natural Gate](https://rabidelephant.com/products/natural-gate)
- [Rabid Elephant Natural Gate manual PDF](https://cdn.shopify.com/s/files/1/1092/5480/files/NATURAL_GATE_User_s_Manual.pdf)
- [Noise Engineering Sinc Bucina](https://noiseengineering.us/products/sinc-bucina/)
- [Noise Engineering — "What is a lowpass gate?" blog post](https://noiseengineering.us/blogs/loquelic-literitas-the-blog/getting-started-lowpass-gates/)

### DIY / open-source LPG references
- [Eddy Bergman — Buchla 292 resonant LPG build](https://www.eddybergman.com/2020/10/synthesizer-build-part-35-resonant.html)
- [NLC LPG product page](https://www.nonlinearcircuits.com/modules/p/low-pass-gate)
- [JonDent — NLC Buchla-style LPG build notes](https://djjondent.blogspot.com/2015/07/nlc-buchla-style-low-pass-gate-lpg.html)
- [JonDent — NLC Dual LPG build notes](https://djjondent.blogspot.com/2019/02/dual-lpg-nlc-build-notes.html)
- [AI Synthesis AI017 build guide](https://aisynthesis.com/diy-low-pass-gate/)
- [AI Synthesis AI017 product page](https://aisynthesis.com/product/ai017-low-pass-gate/)
- [Synthrotek LPG product page](https://www.synthrotek.com/products/modular-circuits/lpg-low-pass-gate/)
- [bmoren/two-tone (DIY passive 2x LPG/LPF, GitHub)](https://github.com/bmoren/two-tone)
- [Two-tone prototype thread on lines](https://llllllll.co/t/prototyping-two-tone-a-2x-passive-lowpass-gate-and-filter-with-diy-vactrols/12663)
- [SDIYClass#2 — $3 LPG / make your own vactrol (YouTube)](https://www.youtube.com/watch?v=8BOnvSQpoGY)
- [DIY Vactrol Low-pass Gate Eurorack Module (YouTube)](https://www.youtube.com/watch?v=MLbKZWlEBuA)

### Vactrol parts and DIY construction
- [LCR0202 datasheet (community-mirrored PDF)](https://www.datasheet-pdf.info/entry/LCR0202)
- [Mod Wiggler — LCR0202 cheap Chinese vactrol thread](https://modwiggler.com/forum/viewtopic.php?t=125463)
- [Synth DIY Wiki — Vactrol page](https://sdiy.info/wiki/Vactrol)
- [Making DIY vactrols (LED + LDR)](https://fricko.home.blog/2021/02/25/making-the-diy-vactrols-for-tame-duck/)
- [ESP — DIY LED/LDR optocoupler project notes](https://www.sound-au.com/project200.htm)

### Theory / academic
- [DAFx 2013 — A Digital Model of the Buchla Lowpass-Gate (PDF)](https://dafx.de/paper-archive/2013/papers/44.dafx2013_submission_56.pdf)
- [Perfect Circuit — What is a Low Pass Gate?](https://www.perfectcircuit.com/signal/what-is-a-lowpass-gate)

### ST Modular references
- [ST Modular Rocinante's Gate](https://www.st-modular.de/modules/rocinante%C2%B4s-gate)
- [carlosedp/STMODULAR-EURORACK GitHub mirror](https://github.com/carlosedp/STMODULAR-EURORACK)

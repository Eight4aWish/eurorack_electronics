# Published LPG Schematics — Reference Catalogue

**Status:** firmed-up reference base. The schematics summarised here are *real, downloadable* designs that have been built and proven. PDFs of all four are stashed in [docs/refs/](refs/) for offline access.

**Why this doc exists:** The first netlist draft ([lpg_netlist.md](lpg_netlist.md)) reads with confidence but a lot of it was synthesised from principles. This doc grounds the design in actual schematics so we can compare *real* topologies and copy values from working circuits.

---

## Headline finding

**My initial netlist had filter cap values off by ~100×.** All three vactrol-LPG schematics I found use **220 pF + 1 nF** for the canonical Buchla 292 audio path, not the 22 nF I had defaulted to. This isn't a small adjustment — it's a topology mismatch. The canonical design is a **two-pole active filter with two LDRs in the audio path**, not a single-pole RC.

Three independent sources (Aalto paper, NLC, AI017) converge on the same component values. That's strong evidence the canonical Buchla 292 topology is what we should build from.

---

## Sources catalogued

| # | Design | Doc type | What it gives us |
|---|---|---|---|
| 1 | **Buchla 292 (canonical)** | Academic paper — Aalto/DAFx 2013 | Simplified schematic + exact values per mode (Both/VCA/LP) |
| 2 | **NLC Low Pass Gate (WAMOD#4)** | DIY build guide PDF | Full schematic + BOM + assembly notes — direct Buchla 292 clone |
| 3 | **AI Synthesis AI017** | KiCad-style schematic PDF | Full schematic + BOM — Buchla 292 + tunable resonance + Depth control |
| 4 | **Doepfer A-101-2** | Manufacturer manual (no schematic) | Block diagram + design choices — Buchla 292 + resonance + dual CV/gate |

Optomix and LxD: Make Noise doesn't publish schematics. Forum discussion confirms LxD CH2 is a **6 dB/oct single-pole** design (different lineage to Buchla 292) using 2 vactrols per channel (one for LP, one for VCA). LxD CH1 is 12 dB/oct based on the older MMG.

---

## Source 1 — Buchla 292 canonical (Aalto/DAFx 2013)

**Reference:** Parker & D'Angelo, "A Digital Model of the Buchla Lowpass-Gate", DAFx 2013, Aalto University. PDF: [docs/refs/aalto_buchla292.pdf](refs/aalto_buchla292.pdf).

**Topology — audio path (Figure 1 in the paper):**

```
                       Vactrol
              R_f  R_α          C_1
   V_in ───[LDR]─┬──[R]──┬─────┬──── V_x ──[op-amp]── V_out
                 │       │     │
                 │       │    GND
                 R_f    C_3
                 │       │
                 └───────┴──── 'Lowpass' feedback
                         │
                        V_fb
                 │
                 ▼
                C_2 ── GND  ('Both' mode shunt)
```

The two LDRs (R_f, both inside one VTL5C3/2 dual-vactrol) form a 2-pole filter with two op-amps and three caps.

**Exact component values (Table 1, Aalto paper):**

| Component | "Both" mode | "VCA" mode | "Lowpass" mode |
|---|---|---|---|
| C₁ | **1 nF** | **1 nF** | **1 nF** |
| C₂ | **220 pF** | **220 pF** | **220 pF** |
| C₃ | 0 (open) | 0 (open) | **4.7 nF** (resonance) |
| R_α | 5 MΩ | 5 kΩ | 5 MΩ |

**Vactrol:** Perkin Elmer VTL5C3 or VTL5C3/2 (dual-LDR variant). R_f modeled across **1 kΩ to 1 MΩ** range.

**Modes (3-pole switch):**
- **Both**: 2-pole low-pass, cutoff controlled by R_f. Slope between -6 dB/oct and -12 dB/oct (poles aren't coincident). When R_f approaches R_α (5 MΩ), gain drops — this is the simultaneous VCFA action.
- **VCA**: R_α drops to 5 kΩ. Pole moves to higher frequency, divider effect kicks in at lower R_f. Result: clean attenuation, no audible filtering.
- **Lowpass**: extra C₃ = 4.7 nF feedback path engaged. Topology becomes Sallen-Key-like with resonant bump. **Note: this mode is NOT in the original Buchla** — it's a derivative addition the paper describes as common in newer clones.

**Magnitude response (Figure 2):** Each mode plotted across R_f = 1 kΩ to 1 MΩ. The "Both" mode is the LPG's signature — gentle 6–12 dB slope that closes simultaneously with amplitude.

---

## Source 2 — NLC Low Pass Gate (WAMOD#4)

**Reference:** Andrew Bell / Nonlinearcircuits, "WAMOD#4 Lo-pass gate", 8/7/2014. PDF: [docs/refs/nlc_lpg.pdf](refs/nlc_lpg.pdf). Schematic rev 1.1 (21/10/2015).

**Topology:** Direct Buchla 292 clone. Single TL074 quad op-amp. Single dual-vactrol (VTL5C3/2). 3PDT mode switch (LP / Both / VCA = "lopass" / middle / "gate").

**BOM (verbatim from the PDF):**

| Component | Value | Quantity | Role |
|---|---|---|---|
| R | 10 R | 2 | Power rail filter |
| R | 470 R | 1 | Vactrol LED current limit |
| R | 1 K | 1 | Output series |
| R | 10 K | 6 | Various (op-amp gain setting, summer inputs) |
| R | 15 K | 2 | Filter section gain |
| R | 22 K | 1 | Output buffer gain |
| R | 100 K | 4 | CV summing, input pulldowns |
| R | 100 K trimpot | 1 | Resonance control (33 K on v1 PCB) |
| R | 150 K | 1 | CV summing |
| R | 470 K | 1 | CV input |
| R | 4M7 | 1 | **R_α equivalent** — defines minimum gain when vactrol closes |
| C | 220 pF | 1 | **C₂ — filter cap** |
| C | 1 nF | 1 | **C₁ — filter cap** |
| C | 2.2 nF | 1 | (likely AC coupling or HF roll-off) |
| C | 4.7 nF | 1 | **C₃ — resonance feedback** |
| C | 1 µF | 1 | Input AC coupling |
| C | 10 µF electro | 2 | Power supply decoupling |
| Diode | 3v9 zener | 1 | LED drive voltage clamp |
| IC | TL074 | 1 | All four halves used |
| Pots | 100 K linear | 2 | Frequency (CV summing) and Resonance |
| Switch | 3PDT toggle | 1 | LP / Both / VCA |
| Vactrol | VTL5C3/2 | 1 | Dual-LDR vactrol |

**Key takeaways:**
- Confirms the canonical 220 pF + 1 nF + 4.7 nF cap stack from Aalto.
- 4 M7 instead of 5 MΩ — close to canonical, just using a standard E-series value.
- Adds resonance (100 K trimpot in the C₃ feedback path) — the Aalto paper notes this is a derivative addition.
- 470 R is the LED current limit (matches our netlist).
- 3v9 zener clamps LED drive — protects the vactrol from over-current.
- **Single TL074 handles everything** — input buffer, two filter op-amps, output buffer, and CV summing. Very economical IC count.
- Author's quote: *"This circuit can really scream"* (re: resonance).

---

## Source 3 — AI Synthesis AI017

**Reference:** AI Synthesis, "AI017 Low Pass Gate Eurorack Module", schematic rev v0 (4/3/2021). PDF: [docs/refs/ai017_schematic.pdf](refs/ai017_schematic.pdf).

**Topology:** Buchla 292 audio path with **two single VTL5C9 vactrols** (LDR1 + LDR2) plus added Depth control and resonance trim.

**Key components from the schematic:**
- IC: **TL074P** quad op-amp (IC1A, B, C, D)
- Vactrols: **VTL5C9 × 2** (slow type — slower than VTL5C3, the "honeyed" feel)
- C8 = **220 pF**, C9 = **4.7 nF**, C11 = **1 nF**, C12 = **2.2 nF** — same canonical Buchla cap stack
- R8 = 10 K (series before LDR1), R10 = 10 K (series after LDR2) — these define the audio path series resistance
- R15 = 470 R — LED current limit
- R6 = 15 K (twice — appears in both filter feedback loops)
- A500K **DEPTH** pot — series in the LED drive path, allows full closure
- B500K **FREQ** pot — manual frequency/CV-blend control
- B100K **CV INTRIM** — internal trim for CV scaling
- 20 K trimmer — resonance Q (gain in the feedback loop)
- A100K input level pot
- Two CV inputs (CV1, CV2) each through 100 K series
- 3PDT mode switch S1 with positions BG/BUCF, BUCF/PUCF, PUCA/PGND (LP / Both / VCA)

**What AI017 adds vs vanilla Buchla 292:**
1. **Depth control (A500K log pot)** — series in the LED drive line. At full CCW, blocks LED current entirely → gate fully closes. Solves the "always slightly open" problem of canonical LPGs.
2. **Resonance gain trim (20 K)** — allows tuning the resonance feedback from "mellow" to "wild distortion / self-oscillation".
3. **Two single vactrols instead of one dual** — gives independent LED drive. We could exploit this to drive each vactrol differently (e.g. one for LP, one for VCA) — but AI017 ties them in series so they act like a dual-vactrol.

---

## Source 4 — Doepfer A-101-2 (manual only)

**Reference:** Doepfer, "A-101-2 Vactrol Lowpass Gate" manual. PDF: [docs/refs/doepfer_a1012.pdf](refs/doepfer_a1012.pdf).

No schematic published — but the manual confirms several design choices and adds useful insight:

- **12 dB/oct** low pass (canonical Buchla 292, "Both" mode)
- Three modes via toggle: LP / LP+VCA / VCA — same as Buchla 292 / NLC / AI017
- Resonance up to **self-oscillation** — confirmed feature
- **Two CV inputs** (CV1 unattenuated, CV2 with attenuator)
- **Two gate inputs (G1, G2)** for **voltage-controlled mode switching** (alongside the manual toggle)
- ⭐ **Status LED in series with the vactrol LEDs** — clever indicator that shows the actual current-into-vactrol illumination, not a separate CV-derived display. Worth copying.

Doepfer-specific cautions worth noting:
- *"Vactrols show considerable slowness... fast attacks/decays (CV = ADSR) or FM effects (CV = LFO or VCO) are not possible."* This bounds what we can expect from any vactrol-based design — the part is inherently slow.
- *"The inevitable tolerances and tracking errors between different vactrols will also lead to an individual sound of each module."* Confirms the variability we already discussed.

---

## Convergent topology — what to build

All three full-schematic sources agree on the audio path. Synthesised reference:

```
INPUT BUFFER (op-amp A, ×1 unity)
    │
    ▼
R_in (10 K)                         ┌─── C_3 (4.7 nF) ───── feedback (Lowpass mode only)
    │                               │       (R_α 4M7 also routes here in Both/LP modes)
    ▼                               │
LDR1 ─── V_x ───┬─── LDR2 ───┬── V_fb ──[Q amp B]── V_out
                │             │
                C_2 (220 pF) C_1 (1 nF)
                │             │
               GND           GND
                              │
                              ▼
                         OUTPUT BUFFER (op-amp, ×1 unity)
                              │
                              ▼
                            OUT
```

(LDR1 and LDR2 are the two LDRs of a dual-vactrol VTL5C3/2, OR two single VTL5C3/9 driven by series-connected LEDs.)

**Op-amps required per channel: 4 halves** (2× TL072 or 1× TL074):
1. Input buffer
2. First filter op-amp (V_x integrator)
3. Second filter op-amp (V_out integrator + feedback amp for resonance)
4. Output buffer / CV summer

**LED driver:** op-amp summer of (Manual + CV + Strike) → 470 R → vactrol LED → GND. With Depth pot inserted in series with the LED drive line.

---

## Implications for our design

This changes the netlist substantially. Specifically:

### Block 2 (audio path) — needs full rewrite
- Was: single LDR, 1 K series, 22 nF shunt cap
- Should be: dual LDR (one vactrol with 2 LDRs, or 2 single vactrols), 10 K series, 220 pF + 1 nF caps, 2-op-amp 2-pole topology
- **Per-channel cap-swap idea (Two-Tone) still applies** — we'd swap C₁ (1 nF default), with alternates 470 pF (brighter) and 2.2 nF (darker)

### Block 3 (output buffer) — keep but renumber
- Becomes the second filter op-amp's output stage

### Block 4 (strike) — fine as designed
- Pulse shaper + diode rectifier still drives the vactrol LED. Just feeds into the *summing junction* of the LED driver (with CV and Manual).

### Block 5 (LED driver) — simplify
- Was: messy mix of inverting summer + PNP + Depth
- Should be: op-amp summing the strike pulse, CV, and manual offset; output through Depth pot (A500K) → 470 R → LED → GND. The PNP current source isn't needed if we use the canonical topology with the LED clamped by a 3v9 zener (per NLC schematic).

### Block 6 (mix output) — keep as designed

### NEW: vactrol footprint
- Was: 8-pin DIP socket for LCR0202 (single LDR)
- Should be: footprint accepting either a **dual-LDR vactrol** (VTL5C3/2 — 5-pin) OR **two single vactrols** wired in series. Either works — pick one.
- LCR0202 (which I had in the BOM) is a single-LDR equivalent of VTL5C3, so it could still be used with a 2-vactrol-per-channel arrangement. Or we can add VTL5C3/2 to the BOM as the canonical part.

### Layered features re-mapped to real-world precedent
- **Depth (L3)** — exactly the AI017 mod. Confirmed: A500K log pot in series with LED drive.
- **Mode switch (L5 — "plan only")** — the canonical 3PDT switch from Buchla 292 / NLC / AI017. Easy to add if we leave PCB pads.
- **Resonance (L7 — "skip")** — well-precedented. NLC uses a 100 K trimpot; AI017 uses a 20 K trimmer plus a feedback resistor network. Either is doable later.
- **Status LED in series with vactrol LEDs (Doepfer)** — small and free addition. Should adopt.
- **DAMP (L4)** — Optomix-specific, no canonical equivalent in the Buchla 292 family. Still doable as a cross-channel coupling pot in the LED driver section, but it's invented (Optomix is closed-source so we can't copy). Lower confidence.
- **Second vactrol per channel (L2)** — per LxD: gives 6 dB/oct LP + separate VCA action. Different topology family from Buchla 292. **Now that we're building Buchla 292 (12 dB/oct, 2 LDRs in 1 vactrol), L2 becomes redundant** — we already have 2 LDRs in the audio path.

So the layer plan should be revised: L2 collapses into the core, L4/L5/L7 stay as planned-only.

---

## Recommended next move

Update [lpg_netlist.md](lpg_netlist.md) to a rev 0.2 with the canonical Buchla 292 audio path. Specifically:
1. Switch Block 2 to canonical 2-pole topology with VTL5C3/2 dual-LDR vactrol, 220 pF + 1 nF + 4M7 R_α
2. Drop the L2 layer (subsumed into the core)
3. Tag each block PROVEN / ADAPTED / SKETCHED so confidence is visible per-block
4. Keep the strike pulse shaper, Depth pot, mix output, and power blocks as previously drafted (those map cleanly onto the canonical design)
5. Add Doepfer-style status LED in series with the vactrol LEDs (free win)

Want me to do that rewrite?

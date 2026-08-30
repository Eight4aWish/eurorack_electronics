# Dual Pingable LPG — n8synth Breadboard Placement

**Status:** rev 0.19 — added a **3V3 turn-on-threshold zener (VD7/VD8)** in each status-LED ground leg so the indicator stays dark through the MANUAL floor and only flashes on strikes/peaks (bench-confirmed). (Rev 0.18) status LEDs are **red** (LED_STATUS_A/B) with **4K7** limit resistors (R_STATUS_A/B, was 2K2/green), matching the as-built voice. (Rev 0.17) split the old "Channel B mirror" build phase into **Phase 3 (Ch B first sound)** + **Phase 4 (Ch B pingable)**, mirroring Channel A's split, so no single phase is overloaded; Mix is now Phase 5. (Rev 0.16) **both channels** on their real n8synth control-board positions (jacks, the three pots' a/b/c legs, LED), with green ⏚ ground-tie reminders on the GND legs, link markers on the DEPTH CCW-shorts, short acronym labels, and board-link jumpers for the plain-wire connections (IN A/B, DEPTH CW A/B, ATTEN top A/B, MIX). Channel A rev 0.15, Channel B rev 0.16. Prior rev 0.14 — the four formerly panel-side resistors (R_OUT_A/B, R_STATUS_A/B) placed on the board, landing their jack/LED end on a control hole (R_OUT_A→XS4, R_OUT_B→XS8, R_STATUS_A→LED A, R_STATUS_B→LED B). 57 twoPins now. Prior rev 0.13 — panel-facing resistor ends moved onto n8synth **control-board holes** (new `ctrlL` / `ctrlR` columns, outboard of the power rails) to free congested breadboard rows. 12 ends relocated (6 per channel): R16/R17/R38/R29/R32/R6 (A) and R22/R25/R39/R30/R33/R12 (B) — each pot/jack end now lands on a control hole at its existing row, with its panel-wire stub (jack/pot leg) relocated onto the same control hole so the old breadboard holes (e.g. 9a/9j) are now free. Control-board positions/routing are the builder's to finalise. Prior rev 0.12 reversed the audio LDR chains. Validated (zero collisions, 53/53 nets correct).

Earlier rev fixes still applied:
1. **R_α (R3, R9)** at **V_p→GND** in parallel with C13/C14 (matches Aalto Eq. 4 + 12, Bergmann R13, White R13).
2. **R_OUT_A / R_OUT_B (1K each)** — on-board (rev 0.14) via control holes, spanning CHA_OUT/CHB_OUT to the OUT-jack control hole (no longer pigtail parts).
3. Vactrol pairs as 2× 4-pin SIPs at cols d and g.
**Platform:** n8synth solderable breadboard
**Layout area:** rows 1-36 (rows 37-40 reserved for n8synth power conditioning — not laid out here)
**Grid:** standard breadboard, 5 holes per half-row, columns a-e on left and f-j on right, centre gap between e and f for IC straddling
**Power rails:** +12V and GND on LEFT edge, -12V and GND on RIGHT edge. **Alternating-parity rule** (from `tools/visualizer/index.html`): `pwrL` = +12V on **even** rows, GND on **odd** rows. `pwrR` = -12V on **even** rows, GND on **odd** rows.
**Source netlist:** [lpg_netlist.md](lpg_netlist.md) rev 0.5

---

## IC ORIENTATION — ALL TL072s ROTATED 180°

All four TL072 ICs use the same orientation as the kick drum's DA1/DA2: pin 8 (VCC) on the left near +12V rail, pin 4 (VEE) on the right near -12V rail.

```
Per IC (occupies 4 contiguous rows; pin number on left side e, right side f):

                  LEFT (a-e)                   RIGHT (f-j)
       a    b    c    d    e        f     g    h    i    j
      ┌────────────────────────┐  ┌────────────────────────┐
Row N: │                  DA.5 │  │ DA.4                   │  ← Half B +in / VEE
       │                  IN B+│  │ VEE                    │
      ├────────────────────────┤  ├────────────────────────┤
Row N+1│                  DA.6 │  │ DA.3                   │  ← Half B -in / Half A +in
       │                  IN B-│  │ IN A+                  │
      ├────────────────────────┤  ├────────────────────────┤
Row N+2│                  DA.7 │  │ DA.2                   │  ← Half B OUT / Half A -in
       │                  OUT B│  │ IN A-                  │
      ├────────────────────────┤  ├────────────────────────┤
Row N+3│                  DA.8 │  │ DA.1                   │  ← VCC / Half A OUT
       │            +12V→ VCC  │  │ OUT A                  │
      └────────────────────────┘  └────────────────────────┘
```

So when reading any IC block below:
- **Half A** (pins 1, 2, 3) sits on the RIGHT side
- **Half B** (pins 5, 6, 7) sits on the LEFT side
- VCC (pin 8) is at the bottom-left, VEE (pin 4) is at the top-right
- 100nF decoupling caps go between row N+3 left (VCC pin) and GND, and between row N right (VEE pin) and GND

---

## PER-CHANNEL IC ALLOCATION (per-channel grouping)

| IC | Channel | Half A function | Half B function |
|---|---|---|---|
| **DA1** | Channel A audio path | IN_BUF_A (input buffer) | FILT_BUF_A (filter output buffer) |
| **DA2** | Channel B audio path | IN_BUF_B (input buffer) | FILT_BUF_B (filter output buffer) |
| **DA3** | Shared drivers | DRV_A (channel A driver) | DRV_B (channel B driver) |
| **DA4** | Shared mix output | MIX_BUF (mix output buffer) | SPARE (for L7 resonance later) |

Per-channel benefit: channel A is fully testable with only DA1 + DA3 populated (DA2 socket can stay empty). Same for channel B with DA2 + DA3.

---

## VACTROL SOCKETS — 2× 4-PIN SIP PER CHANNEL (rev 0.8)

Each channel uses **two 4-pin SIP sockets** holding two vactrols (one per SIP). Each vactrol pre-mounts on a 4-pin male SIP header with a standardised pinout, then plugs into a 4-pin female SIP socket on the breadboard. The vactrol body elevates above the board surface, freeing breadboard real estate beneath.

### Standard vactrol-on-SIP pinout

Every vactrol (commercial tube, DIY heatshrink, or 3D-printed shroud) is built to the same 4-pin convention. The order matches the **physical geometry** of a tubular vactrol — LDR leads on the outside, LED leads on the inside — so the longer LDR wires take the bigger bends and the shorter LED wires sit in the middle two pin positions.

| SIP pin | Lead | Polarity / notes |
|---|---|---|
| **1** | LDR a | LDR end (non-polar — either LDR lead works) |
| **2** | LED+ (anode, long lead, marked **+**) | LED end |
| **3** | LED− (cathode, short lead, marked **−**) | LED end |
| **4** | LDR b | LDR end (other LDR lead) |

Bench-tested vactrol library: units 1-9 (DIY) + commercial set, see `docs/lpg_reference_review.md` for pair-match data.

### Channel socket arrangement (Ch A example; Ch B mirrors at rows 23-26)

SIP pins are shown as ①②③④ (numbered from top of socket downward, regardless of how the SIP is oriented within the socket — pin numbering follows physical socket position, not the SIP module's own pin numbering).

```
   col              a     b     c     d     e ⇄ f     g     h     i     j
                                       ↓                    ↓
                                   SIP_L socket       SIP_R socket (will hold flipped SIP)

   row 5  R5.r1 R3.r1 C13.r1 L① (LDRa)             R④ (LDRb)   R4.r2    ─      ─
              rev 0.12 — chain reversed end-for-end: INPUT now enters RIGHT (R④ col g = VC_A_LDR1_IN, fed by R4 from BUF_OUT row 4R);
              V_p OUTPUT now exits LEFT (L① col d strip = V_p_A): R5.r1 → row 1L col a (FILT_BUF in); R3.r2 → row 1 pwrL (GND); C13.r2 → row 3 pwrL (GND)
   row 6    ─     ─     ─     L② (A)    ═══════════  R③ (K)         ─     ─      ─
   row 7    ─    R6.r2  VD5.r1 L③ (K)                R② (A)         ─     ─      ─
                                                                            VD5.r2 → row 9 pwrL (GND, rev 0.11)
   row 8    ─    C11.r1  ─    L④ (LDRb) ═══════════  R① (LDRa)      ─     ─      ─
                                                                            C11.r2 → row 7 pwrL (GND)

       legend:  L① = SIP_L socket position 1 (top), pin 1 of an un-flipped SIP module
                R④ = SIP_R socket position-1 (top); a flipped SIP lands its pin 4 here
                ═══ = centre-gap bridge jumper (rows 6 and 8)
                A = LED anode (pin 2 of SIP module);  K = LED cathode (pin 3)
                LDRa = pin 1 of SIP module;  LDRb = pin 4
```

- **SIP_L** plugs into col d in standard orientation — module's pin 1 (LDRa) lands at row 5 col d.
- **SIP_R** plugs into col g **flipped 180°** — module's pin 1 (LDRa) lands at row 8 col g (the bottom of the socket); pin 4 (LDRb) at row 5 col g.
- Both SIP modules are physically identical (same standardised pinout LDRa/anode/cathode/LDRb). Only the socket-insertion orientation differs.
- This arrangement makes the LED chain (MID node) and the LDR junction (V_x node) line up at single-row centre-gap bridges instead of requiring long diagonal jumpers.

### Two centre-gap bridges per channel

The only jumpers between the two SIPs are at rows 6 and 8, each spanning the breadboard centre gap between col e and col f:

- **MID bridge (row 6 col e ↔ row 6 col f)** — connects SIP_L pin 2 (anode) to SIP_R pin 3 (cathode) for LED chain series
- **V_x bridge (row 8 col e ↔ row 8 col f)** — connects SIP_L pin 4 (LDRb) to SIP_R pin 1 (LDRa) for the LDR junction

Short bridges only; no long diagonal wiring needed.

---

## ⚠️ JSON IS AUTHORITATIVE FOR PLACEMENT

**[tools/visualizer/layouts/lpg.json](../tools/visualizer/layouts/lpg.json) is the source of truth.** The row-by-row table below is auto-generated from rev-0.11 of that JSON and verified by `tools/visualizer/validate_layout.py` (zero hole collisions, including rail holes) + `tools/visualizer/cross_check_nets.py` (53/53 components net-identity-correct).

---

## 🔨 PHASE 1 BUILD CHECKLIST — first sound (Ch A, MANUAL only) — rev 0.17

Tick at the bench. After this phase, turning MANUAL should open the filter for a 1 kHz sine at CHA_IN.

**On-board parts:**

- [ ] Solder DA1 8-pin DIP socket (rows 1-4, cols e/f). TL072 in last.
- [ ] Solder DA3 8-pin DIP socket (rows 14-17, cols e/f). TL072 in last.
- [ ] Solder **VC_A_L 4-pin SIP socket** at col d, rows 5-8.
- [ ] Solder **VC_A_R 4-pin SIP socket** at col g, rows 5-8.
- [ ] **DA1 decoupling**: C3 (100nF, row 4L col b → row 5 pwrL=GND), C4 (100nF, row 1R col h → row 1 pwrR=GND)
- [ ] **DA3 decoupling**: C5 (100nF, row 17L col b → row 17 pwrL=GND), C6 (100nF, near DA3 pin 4)
- [ ] **Ch A audio path** (rev 0.12 — LDR chain reversed; LDR1 input now on the RIGHT next to BUF_OUT, V_p output now on the LEFT next to FILT_BUF, so neither 10K crosses the centre gap): R1 (100K, CHA_IN→GND, row 2R col h → row 3 pwrR), R4 (10K, BUF_OUT_A row 4R col h → **row 5R col h = VC_A_LDR1_IN**), C11 (220pF, row 8L col b = V_x → row 7 pwrL = GND), **R3 (4M7, V_p→GND in parallel with C13: row 5L col b → row 1 pwrL = GND)**, C13 (1nF, in socket, **row 5L col c = V_p → row 3 pwrL = GND**), R5 (10K, **row 5L col a = V_p → row 1L col a = V_OUT_A_PRE_BUF**)
- [ ] **DA1 unity-gain jumpers**: JW_DA1_UGA (pin 2 → pin 1), JW_DA1_UGB (pin 6 → pin 7)
- [ ] **Driver minimum**: R36 (10K feedback DA3.2↔DA3.1), R37 (10K DA3.3 → GND reference), R29 (4K7 VCC rail → MANUAL A top @ **ctrlL 6**), R32 (4K7 MANUAL A wiper @ **ctrlL 5** → DA3.2 DRV_SUM_A)
- [ ] **LED drive**: R6 (470R, DEPTH A wiper @ **ctrlR 5** → **row 7L col b = LED_DRIVE_A**), **VD5 zener** (6v8 in socket, anode **row 7L col c**, cathode **row 9 pwrL = GND**)
- [ ] **Centre-gap bridges**: JW_VCA_MID (row 6 col e ↔ row 6 col f) and JW_VCA_VX (row 8 col e ↔ row 8 col f). Short jumpers across the breadboard centre gap.
- [ ] **Power wires to rails**: DA1 VCC (pin 8 to +12V rail at row 4 pwrL), DA1 VEE (pin 4 to -12V at row 1 pwrR), DA3 VCC (pin 8 row 17 pwrL), DA3 VEE (pin 4 row 14 pwrR), **VC_A_R pin 2 → GND (row 7R col i → row 7 pwrR)**
- [ ] **Insert TL072s into DA1 and DA3 sockets.** Insert **VC_A_L vactrol-SIP** in standard orientation (pin 1 at row 5 col d); insert **VC_A_R vactrol-SIP flipped 180°** (its pin 1 lands at row 8 col g, pin 4 at row 5 col g). Both SIPs have the same physical pinout — flipping is achieved by socket orientation only.

**Off-board (panel + jacks):**

- [ ] P2 MANUAL pot (100K B) — legs to control holes: a = GND ⏚ @ **ctrlL 4**, b = wiper @ **ctrlL 5** (R32 → driver), c = top @ **ctrlL 6** (R29 → +12V)
- [ ] P3 DEPTH pot (500K A, rheostat) — legs to control holes: a = tie to b ↔ @ **ctrlR 4**, b = wiper @ **ctrlR 5** (R6 → vactrol LED), c = CW @ **ctrlR 6** (JW_P3cA → DRV_OUT_A)
- [ ] CHA_IN jack (XS1) → IN A @ **ctrlR 1** (JW_INA → CHA_IN buffer input)
- [ ] CHA_OUT jack (XS4) → OUT A @ **ctrlL 1** — on-board **R_OUT_A (1K)** spans CHA_OUT (DA1.7) → ctrlL 1; mix bus taps before R_OUT.
- [ ] Power header (2x5 IDC) wired to the n8synth power section

**Phase 1 bench tests:** see [tools/visualizer/layouts/lpg.json](../tools/visualizer/layouts/lpg.json) Phase 1 `test` field (visible in the visualizer side panel). Summary: ±12V check → unity-gain pass at CHA_OUT with MANUAL open → MANUAL sweep closes the gate → zener swap (6v8 → 9v1) if peak drive isn't enough.

**You do NOT need to populate** (leave sockets empty / parts in their bags): DA2, DA4, VC_B, all "B" suffix parts, mix-bus parts (R23–R28, C17), strike-shaper parts (R17, C15, R15, VD1, R34), CV parts (R16, R13, R38). LED_STATUS_A + R_STATUS_A (now on-board via control holes ctrlL 7/8) come in Phase 2.

---

**VD5 / VD6 (rev 0.11 placement) — zener clamp:**

| Designator | Anode (r1) | Cathode (r2, banded) | Net A (anode) | Net B (cathode) |
|---|---|---|---|---|
| **VD5** (Ch A) | row 7, col c | **row 9, pwrL** | LED_DRIVE_A (row 7L; R6 at col b, VC_A_L.3 at col d) | GND (left rail; pwrL on odd row 9 = GND) |
| **VD6** (Ch B) | row 25, col c | **row 27, pwrL** | LED_DRIVE_B (row 25L; R12 at col b, VC_B_L.3 at col d) | GND (left rail; pwrL on odd row 27 = GND) |

The zener anode sits at the LED_DRIVE row (7 / 25). The cathode runs down 2 rows to a free GND rail hole (9 / 27) — rev 0.11 moved it there to avoid sharing a rail hole with C11 / C12. Default-populate **6v8** (BZX55C6V8). Use a SIP-2 or DIP-2 machined-pin socket so 3v9 / 6v8 / 9v1 can be A/B-swapped on the bench.

**Revision history (most-recent-first):**
- **0.19** — Added a **3V3 zener (VD7 ch A, VD8 ch B)** in each status-LED ground leg as a turn-on threshold. In series between the LED anode (long leg) and the d-plane (cathode/banded toward GND), it holds the indicator off until the driver swings past ~Vf_LED + 3.3 ≈ 5.2 V, so it ignores the MANUAL floor and flashes punchily on strikes/peaks (full-drive current then ≈ 1.0 mA). Panel/control-board part — not a breadboard twoPin, so the maps are unchanged. Recorded in BOM + netlist Block 7. Bench-confirmed "perfect".
- **0.18** — Status-LED parts updated to the as-built voice: **LED_STATUS_A/B = red** (was green) and **R_STATUS_A/B = 4K7** (was 2K2). Red's lower Vf (~1.9 V) would run brighter than green at 2K2, so the limit resistor went up — `(≈10 V − 1.9 V) / 4K7 ≈ 1.7 mA`, comfortably visible without glare, and an even lighter parallel load on the driver. (The vactrol-drive LEDs were already red; green underperformed on the series-LED Vf budget.) Pure parts change — no nets/positions moved; maps regenerated, 57/57 nets, zero collisions.
- **0.17** — Split the build phases: the old single "Phase 3 — Channel B mirror" is now **Phase 3 (Ch B first sound, MANUAL only)** + **Phase 4 (Ch B pingable: CV + STRIKE + status LED)**, mirroring the Channel A Phase 1/2 split; Mix output became **Phase 5**. Component `stage` fields reassigned accordingly (B-pingable set = R22/R19/R39, R25/C16/R31/VD2/R35, R_STATUS_B + their stubs/markers/JW_P5cB → stage 4; rest of B → stage 3; all mix → stage 5). Per-phase twoPin counts now ~17/9/15/9/7 (was 17/9/**33**/7). Pure metadata change — nets/positions untouched; 57/57 nets, zero collisions.
- **0.16** — Mirrored the re-allocation to **Channel B** at its real control positions. Left CTRL: `MIX@17`, `DEPTH B a/b/c@20-22`, `OUT B@23`, `LED B a/b@32-33`, `STRIKE B@35`. Right CTRL: `IN B@23`, `ATTEN B a/b/c@32-34`, `MANUAL B a/b/c@35-37`, `CV B@38`. Same marker treatment (⏚ on MANUAL B a / ATTEN B a / LED B a; link on DEPTH B a) and acronym labels. Board-link jumpers: `JW_INB` (IN B→CHB_IN), `JW_P7cB` (DEPTH B CW→DRV_OUT_B), `JW_P5cB` (ATTEN B top→CV_PROT_B), `JW_MIX` (MIX jack→MIX_OUT_JACK, post-C17 — C17 stays by DA4). Both channels now fully on real control positions. Validated: 57/57 nets, zero collisions, 19 jumpers.
- **0.15** — Re-allocated **Channel A** to the real n8synth control-board positions from the builder. Right CTRL: `IN A@1`, `DEPTH A a/b/c@4-6`, `ATTEN A a/b/c@7-9`, `CV A@17`, `STRIKE A@20`. Left CTRL: `OUT A@1`, `MANUAL A a/b/c@4-6`, `LED A a/b@7-8`. Pot legs: a=left, b=wiper, c=right; MANUAL/ATTEN have c=hot end + a=GND; DEPTH has c=DRV_OUT, b=wiper, a=link-to-b (CCW short). Added marker types: `mark:"gnd"` (green ⏚ earth glyph — tie to d-plane) on MANUAL A a / ATTEN A a / LED A a (anode); `mark:"link"` (grey loop) on DEPTH A a. Added `lbl` (short acronym) to control stubs to stop label truncation; visualiser `drawJPSWires` renders gnd/link marks + lbl. Added board-link **jumpers** for the three control positions that reach a board node by plain wire (no series resistor): `JW_INA` (IN A → CHA_IN buffer-in), `JW_P3cA` (DEPTH A CW → DRV_OUT_A), `JW_P1cA` (ATTEN A top → CV_PROT_A) — without these they dangled. Validated: 57/57 nets, zero collisions. Channel B still on placeholder positions.
- **0.14** — Placed the four formerly panel-side resistors on the board using control holes (now that `ctrlL`/`ctrlR` represent the panel positions): **R_OUT_A** `CHA_OUT (3L) → 3.ctrlL` (XS4 jack), **R_OUT_B** `CHB_OUT (29L) → 29.ctrlL` (XS8), **R_STATUS_A** `DRV_OUT_A (17R) → 17.ctrlR` (LED A cathode), **R_STATUS_B** `DRV_OUT_B (16L) → 16.ctrlL` (LED B cathode). Their jack/LED stubs (XS4/XS8, LEDsta/LEDstb) moved onto the same control holes. twoPins 53→57; all 57 net-checked (EXPECTED_NETS extended). Mix bus still taps CHA_OUT/CHB_OUT *before* R_OUT. Note: the BOM still tags these four "PANEL-SIDE" — update when finalised.
- **0.13** — Introduced n8synth **control-board columns** `ctrlL` / `ctrlR` in the visualiser (outboard of the power rails, one hole per row, drawn as amber "CTRL" hole columns). Moved the panel-facing end of 12 resistors onto control holes so their breadboard landing rows are freed: Ch A — R17→`9.ctrlL` (STRIKE), R16→`9.ctrlR` (CV), R38→`11.ctrlR` (P1 wiper), R29→`12.ctrlR` (P2 top), R32→`13.ctrlR` (P2 wiper), R6→`13.ctrlL` (P3 wiper); Ch B mirror — R25→`21.ctrlL`, R22→`21.ctrlR`, R39→`19.ctrlR`, R30→`18.ctrlR`, R33→`22.ctrlR`, R12→`22.ctrlL`. Each control hole carries the panel net it routes to (recorded in `cross_check_nets.py` BARE_ROW_NETS). Each resistor's matching panel-wire stub (jack/pot-leg jpsWire) was relocated onto the same control hole, freeing the old breadboard holes. Exact control-board positions/routing are left for the builder. Control columns (like the power rails) are not shown in the half-column ROW MAP table below — the JSON is authoritative. Validated: zero collisions, 53/53 nets correct.
- **0.12** — Reversed both audio LDR chains end-for-end to remove the centre-gap-crossing 10K series resistors. Mechanism: swapped the audio (LDR) nets on the two SIP outer pins per channel — `VC_x_L.1` is now `V_p` and `VC_x_R.4` is now `VC_x_LDR1_IN` — so the chain enters on the right (col g, next to BUF_OUT) and exits V_p on the left (cols a-c, next to FILT_BUF). Moved with V_p: R3 (now r5L b → r1.pwrL GND), C13 (now r5L c → r3.pwrL GND), R5 (now r5L a → r1L a); and on Ch B R9 (r23L b → r21.pwrL GND), C14 (r23L c → r23.pwrL GND), R11 (r23L a → r27L a). R4 moved to r5R h, R10 to r23R h. C11/C12 (220pF at V_x), the LED chain, both centre-gap bridges, and the drivers are untouched. Electrically identical (both 10Ks equal, both LDRs share one LED; R_α + 1nF stay at the V_p / filter-buffer-input node per the canonical Buchla 292 references). Validated: zero hole collisions, 53/53 net identities correct, all four new GND-rail ends on odd-row (GND) parity.
- **0.11** — Rail-hole collision fix after `validate_layout.py` was updated to track `pwrL`/`pwrR` endpoints (previously it skipped them, which missed 5 real collisions). Moved: R3.r2 from r5.pwrR → r9.pwrR; VD5.r2 from r7.pwrL → r9.pwrL; C6.r2 from r15.pwrR → r13.pwrR; VD6.r2 from r25.pwrL → r27.pwrL; R9.r2 from r23.pwrR → r19.pwrR. All five new positions are GND (odd-row rail parity); no new collisions.
- **0.10** — Two reference-audit fixes after side-by-side comparison with Bergmann + Thomas White + Aalto/DAFx 2013 (sources saved in `docs/refs/`). (1) R_α (R3 channel A, R9 channel B) repositioned from V_x→V_p (across LDR2) to **V_p→GND** (parallel with C13/C14) — corrects a misreading of the canonical Buchla 292 topology that had been carried through revs 0.2–0.8. Matches Aalto Eq. 4 + 12, Bergmann's R13, and Thomas White's R13. (2) Per-channel **R_OUT_A / R_OUT_B (1K each)** added as panel-side parts, matching Bergmann's R15 and White's R15. Soldered in-line on the pigtail from DA1.7 / DA2.7 to the output jacks. Mix bus continues to tap from before R_OUT, so it only loads the buffered op-amp output. No on-board layout change.
- **0.9** — Layout change for fix (1) above: R3 moved from r1=8/c → r2=5/h to r1=5/h → r2=5/pwrR (GND). R9 same change at row 23.
- **0.8** — Vactrol mounting refactored to 2× 4-pin SIPs per channel (cols d and g). Each vactrol becomes a swappable SIP module with standardised pinout (LDRa/anode/cathode/LDRb). VC_A_R / VC_B_R installed flipped so MID and V_x junctions become short centre-gap bridges at rows 6, 8, 24, 26. Driver-side components (R6, VD5) moved to row 7L (was 5L); audio-output components (R3 end, C13, R5) moved to row 5R (was 7R). Channel B mirrors at rows 23-26.
- **0.7** — R_STATUS_A and R_STATUS_B moved off-board (panel-side). The previous rev-0.5 relocation of R_STATUS_B to row 31L col a created a new short (row 31L is shared with the CHA_OUT mix-bus tap-jumper). Moving the resistor off the board entirely resolves the conflict.
- **0.6** — stages reorganised from 6 schematic blocks to 4 practical build PHASES with bench-test notes.
- **0.5** — 9 hole collisions resolved by spreading pins across each row-half. VD5/VD6 routed via left GND rail to be visible outside the VC_X IC body.
- **0.4** — VD5/VD6 zener clamps restored after a wrong-headed rev-0.3 removal.

---

## FULL BOARD MAPS — generated from JSON (authoritative)

These two tables are produced by `tools/visualizer/gen_rowmap.py` straight from `tools/visualizer/layouts/lpg.json` (the authoritative placement source). **Re-run that script after any layout change — do not hand-edit between the markers.** The breadboard map covers the main grid (cols a–j); the control-board map covers the n8synth control columns (`ctrlL`/`ctrlR`, outboard of the power rails). Power rails (pwrL/pwrR) are not shown — parity rule: `pwrL` odd=GND/even=+12V, `pwrR` odd=GND/even=-12V.

<!-- GEN:MAPS:START — auto-generated by tools/visualizer/gen_rowmap.py from lpg.json rev 0.23-photo-recon. Do not hand-edit between these markers; re-run the generator. -->

### Breadboard row map (cols a–j) — rev 0.23-photo-recon

| Row | Net (L) | Left half (a–e) | Net (R) | Right half (f–j) |
|-----|---------|-----------------|---------|------------------|
| 1 | `V_OUT_A_PRE_BUF` | R5.2@a (10K), **DA1.5**@e | `VEE` | **DA1.4**@f, C4.1@h (100nF) |
| 2 | `FILT_BUF_A_INV` | _JW_DA1_UGB_, **DA1.6**@e | `CHA_IN` | **DA1.3**@f, R1.1@h (100K), _JW_INA_ |
| 3 | `CHA_OUT` | R_OUT_A.1@a (1K), _JW_DA1_UGB_, _JW_CHA_OUT_BUS_, **DA1.7**@e | `IN_BUF_A_INV` | **DA1.2**@f, _JW_DA1_UGA_ |
| 4 | `VCC` | C3.1@b (100nF), **DA1.8**@e | `BUF_OUT_A` | **DA1.1**@f, _JW_DA1_UGA_, R4.1@h (10K) |
| 5 | `GND` | C3.2@b (100nF), C13.2@c (1nF), R3.1@e (4M7) | `—` | — |
| 6 | `V_p_A` | R5.1@a (10K), C13.1@c (1nF), **VC_A_L.1**@d, R3.2@e (4M7) | `VC_A_LDR1_IN` | **VC_A_R.4**@g, R4.2@h (10K) |
| 7 | `LED_CHAIN_MID_A` | **VC_A_L.2**@d, _JW_VCA_MID_ | `LED_CHAIN_MID_A` | _JW_VCA_MID_, **VC_A_R.3**@g |
| 8 | `LED_DRIVE_A` | _JW_R6_LED_A_, VD5.1@c (Zener 6v8), **VC_A_L.3**@d | `GND` | **VC_A_R.2**@g |
| 9 | `V_x_A` | C11.1@b (220pF), **VC_A_L.4**@d, _JW_VCA_VX_ | `V_x_A` | _JW_VCA_VX_, **VC_A_R.1**@g |
| 10 | `GND` | VD5.2@c (Zener 6v8) | `CV_PROT_A` | R13.1@h (100K), _JW_P1cA_, R16.2@j (1K) |
| 11 | `—` | — | `C15_b` | C15.2@f (1uF), R15.1@g (10K), VD1.1@h (1N4148) |
| 12 | `—` | — | `STRIKE_PULSE_A` | R34.1@g (10K), VD1.2@h (1N4148) |
| 13 | `—` | — | `C15_a` | C15.1@f (1uF), R17.2@h (1K) |
| 14 | `DRV_B_NINV` | R14.1@b (10K), **DA3.5**@e | `VEE` | **DA3.4**@f, C6.1@h (100nF) |
| 15 | `DRV_SUM_B` | R39.2@a (4K7), R33.2@b (4K7), R35.2@c (10K), R20.2@d (10K), **DA3.6**@e | `DRV_A_NINV` | **DA3.3**@f, R37.1@h (10K) |
| 16 | `DRV_OUT_B` | _JW_P7cB_, R20.1@c (10K), R_STATUS_B.1@d (4K7), **DA3.7**@e | `DRV_SUM_A` | **DA3.2**@f, R34.2@g (10K), R36.2@h (10K), R38.2@i (4K7), R32.2@j (4K7) |
| 17 | `VCC` | C5.1@b (100nF), **DA3.8**@e | `DRV_OUT_A` | **DA3.1**@f, R36.1@g (10K), R_STATUS_A.1@h (4K7), _JW_P3cA_ |
| 18 | `STRIKE_PULSE_B` | VD2.2@c (1N4148), R35.1@d (10K) | `—` | — |
| 19 | `C16_b` | C16.2@a (1uF), R31.1@b (10K), VD2.1@c (1N4148) | `—` | — |
| 20 | `C16_a` | R25.2@a (1K), C16.1@b (1uF) | `CV_PROT_B` | R19.1@h (100K), _JW_P5cB_, R22.2@j (1K) |
| 23 | `V_p_B` | R11.1@a (10K), R9.1@b (4M7), C14.1@c (1nF), **VC_B_L.1**@d | `VC_B_LDR1_IN` | **VC_B_R.4**@g, R10.2@h (10K) |
| 24 | `LED_CHAIN_MID_B` | **VC_B_L.2**@d, _JW_VCB_MID_ | `LED_CHAIN_MID_B` | _JW_VCB_MID_, **VC_B_R.3**@g |
| 25 | `LED_DRIVE_B` | R12.2@b (470R), VD6.1@c (Zener 6v8), **VC_B_L.3**@d | `GND` | **VC_B_R.2**@g |
| 26 | `V_x_B` | C12.1@b (220pF), **VC_B_L.4**@d, _JW_VCB_VX_ | `V_x_B` | _JW_VCB_VX_, **VC_B_R.1**@g |
| 27 | `V_OUT_B_PRE_BUF` | R11.2@a (10K), **DA2.5**@e | `VEE` | **DA2.4**@f, C8.1@h (100nF) |
| 28 | `FILT_BUF_B_INV` | _JW_DA2_UGB_, **DA2.6**@e | `CHB_IN` | **DA2.3**@f, R7.1@h (100K), _JW_INB_ |
| 29 | `CHB_OUT` | R_OUT_B.1@a (1K), _JW_DA2_UGB_, _JW_CHB_OUT_BUS_, **DA2.7**@e | `IN_BUF_B_INV` | **DA2.2**@f, _JW_DA2_UGA_ |
| 30 | `VCC` | C7.1@b (100nF), **DA2.8**@e | `BUF_OUT_B` | **DA2.1**@f, _JW_DA2_UGA_, R10.1@h (10K) |
| 31 | `CHA_OUT` | R23.1@b (100K), _JW_CHA_OUT_BUS_ | `CHB_OUT` | _JW_CHB_OUT_BUS_, R26.1@i (100K) |
| 32 | `MIX_OUT_JACK` | _JW_MIX_, C17.2@b (100nF) | `—` | — |
| 33 | `SPARE_NINV` | _JW_DA4_SP_NINV_GND_, **DA4.5**@e | `VEE` | **DA4.4**@f, C10.1@h (100nF) |
| 34 | `SPARE_INV` | _JW_DA4_SP_FB_, **DA4.6**@e | `MIX_NINV` | **DA4.3**@f, R28.1@h (100K) |
| 35 | `SPARE_OUT` | _JW_DA4_SP_FB_, **DA4.7**@e | `MIX_BUS` | **DA4.2**@f, R24.1@g (100K), R23.2@h (100K), R26.2@i (100K) |
| 36 | `VCC` | C9.1@b (100nF), **DA4.8**@e | `MIX_OUT` | **DA4.1**@f, R24.2@g (100K), C17.1@h (100nF) |

### Control-board map (ctrlL / ctrlR) — rev 0.23-photo-recon

| Row | Left CTRL (ctrlL) | Right CTRL (ctrlR) |
|-----|-------------------|--------------------|
| 1 | OUTA, R_OUT_A.2@ctrlLi (1K) | INA, _JW_INA_ |
| 4 | P2a ⏚ | P3a ↔b |
| 5 | P2b, _JW_R32_MAN_A_ | P3b, R6.1@ctrlRi (470R) |
| 6 | P2c, R29.1@ctrlLi (4K7) | P3c, _JW_P3cA_ |
| 7 | LAa ⏚ | P1a ⏚ |
| 8 | LAb, _JW_STATA_ | P1b, R38.1@ctrlRi (4K7) |
| 9 | — | P1c, _JW_P1cA_ |
| 11 | — | R6.2@ctrlRi (470R), _JW_R6_LED_A_ |
| 13 | — | R_STATUS_A.2@ctrlRo (4K7), _JW_STATA_ |
| 15 | — | R32.1@ctrlRo (4K7), _JW_R32_MAN_A_ |
| 17 | MIX, _JW_MIX_ | CVA, R16.1@ctrlRi (1K) |
| 20 | P7a ↔b | R17.1@ctrlRi (1K), STA |
| 21 | P7b, R12.1@ctrlLi (470R) | — |
| 22 | P7c, _JW_P7cB_ | — |
| 23 | OUTB, R_OUT_B.2@ctrlLi (1K) | INB, _JW_INB_ |
| 32 | LBa ⏚ | P5a ⏚ |
| 33 | LBb, R_STATUS_B.2@ctrlLi (4K7) | P5b, R39.1@ctrlRi (4K7) |
| 34 | — | P5c, _JW_P5cB_ |
| 35 | R25.1@ctrlLi (1K), STB | P6a ⏚ |
| 36 | — | P6b, R33.1@ctrlRi (4K7) |
| 37 | — | P6c, R30.1@ctrlRi (4K7) |
| 38 | — | CVB, R22.1@ctrlRi (1K) |

<!-- GEN:MAPS:END -->

### Notation
- **`DA1.5`@e** = IC `DA1` pin 5 at col e. Vactrol SIP pins follow 1=LDRa, 2=anode, 3=cathode, 4=LDRb; `VC_x_R` is the same module flipped in its socket.
- `R5.1@a (10K)` = a component lead (R5 pin 1) at that col, with value. `_JW_x_` = a jumper end (centre-gap bridge or control→board link).
- Control-board cells use acronym labels (e.g. `P2b`, `CVA`); **⏚** = tie this hole to the d ground-plane; **↔b** = leg shorted to the wiper (DEPTH CCW short).

---

## OFF-BOARD INTERCONNECT (panel-mount components)

Panel jacks, pots and LEDs mount on the panel and connect through the **n8synth control board** — each control position (the `ctrlL`/`ctrlR` columns in the maps above) is a fixed pad wired to a panel point. Jack sleeves, pot GND legs and the LED anodes tie to the control board's **d ground-plane** (a green ⏚ in the control-board map), so only the signal connections are listed below. The per-channel output resistors (R_OUT_A/B) and status-LED resistors (R_STATUS_A/B) are now **on the board** — each spans a driver/output node to its control hole — not pigtail parts.

### Jacks (9 total — 3.5mm Thonkiconn PJ-301M, switched mono)

| Jack | Label | Tip → control position → board net | Sleeve |
|---|---|---|---|
| XS1 | CH A IN | `ctrlR 1` → JW_INA → CHA_IN (buffer in) | d-plane |
| XS2 | CH A STRIKE | `ctrlR 20` → R17 → strike shaper | d-plane |
| XS3 | CH A CV | `ctrlR 17` → R16 → CV_PROT_A | d-plane |
| XS4 | CH A OUT | `ctrlL 1` ← R_OUT_A ← CHA_OUT | d-plane |
| XS5 | CH B IN | `ctrlR 23` → JW_INB → CHB_IN (buffer in) | d-plane |
| XS6 | CH B STRIKE | `ctrlL 35` → R25 → strike shaper | d-plane |
| XS7 | CH B CV | `ctrlR 38` → R22 → CV_PROT_B | d-plane |
| XS8 | CH B OUT | `ctrlL 23` ← R_OUT_B ← CHB_OUT | d-plane |
| XS9 | MIX OUT | `ctrlL 17` → JW_MIX → MIX_OUT_JACK (post C17) | d-plane |

### Pots (6 total — 9mm PCB rotary; the three legs land on a/b/c control positions)

Leg convention: **a = left, b = wiper (middle), c = right** (knob facing you).

| Pot | Label | Value | a (left) | b (wiper) | c (right) |
|---|---|---|---|---|---|
| P1 | CV ATTEN A | 100K lin | `ctrlR 7` → GND ⏚ | `ctrlR 8` → R38 → driver | `ctrlR 9` → CV_PROT_A (CV in) |
| P2 | MANUAL A | 100K lin | `ctrlL 4` → GND ⏚ | `ctrlL 5` → R32 → driver | `ctrlL 6` → R29 → +12V |
| P3 | DEPTH A | 500K log, rheostat | `ctrlR 4` → tie to b ↔ | `ctrlR 5` → R6 → vactrol LED | `ctrlR 6` → DRV_OUT_A |
| P5 | CV ATTEN B | 100K lin | `ctrlR 32` → GND ⏚ | `ctrlR 33` → R39 → driver | `ctrlR 34` → CV_PROT_B (CV in) |
| P6 | MANUAL B | 100K lin | `ctrlR 35` → GND ⏚ | `ctrlR 36` → R33 → driver | `ctrlR 37` → R30 → +12V |
| P7 | DEPTH B | 500K log, rheostat | `ctrlL 20` → tie to b ↔ | `ctrlL 21` → R12 → vactrol LED | `ctrlL 22` → DRV_OUT_B |

MANUAL/ATTEN are dividers (c = hot end, a = GND, b = wiper to the driver). DEPTH is a rheostat (c = driver output, b = wiper out via the 470R to the vactrol LED, a shorted to b as the CCW safety). Swap a↔c if a control runs backwards.

### Status LEDs (2 — panel-mount; R_STATUS on-board, threshold zener in the ground leg)

| LED | Wiring |
|---|---|
| LED A (3mm **red**) | **Long leg = anode →** `VD7 (3V3 zener, anode side)` → banded end → `ctrlL 7` → GND ⏚ (d-plane). **Short leg = cathode →** `ctrlL 8` → on-board R_STATUS_A (**4K7**) → DRV_OUT_A. |
| LED B (3mm **red**) | **Long leg = anode →** `VD8 (3V3 zener, anode side)` → banded end → `ctrlL 32` → GND ⏚. **Short leg = cathode →** `ctrlL 33` → on-board R_STATUS_B (**4K7**) → DRV_OUT_B. |

The **3V3 zener (VD7/VD8) in the ground leg** gives the indicator a turn-on threshold (~Vf_LED + 3.3 ≈ 5.2 V): it stays dark through the MANUAL baseline and quiet passages, then comes on punchily for strikes/peaks instead of glowing constantly. Cathode (banded) toward ground. Panel/control-board side — no breadboard hole, so it isn't in the maps above.

### Power

n8synth power inlet handles ±12V/GND distribution. Rails available on left edge (+12V on even rows, GND on odd rows) and right edge (-12V on even, GND on odd) per the alternating-parity rule.

### Panel layout (final)

Panel grid: 3 columns × 6 rows on a 10HP n8synth panel. Revised 2026-05-20 — stacked dual 3×3: each channel is a 3×3 block (Channel A = rows 1-3, Channel B = rows 4-6), with the three columns themed by signal role. DEPTH (P3/P7, 500K log A) is the top-centre knob of each block; this matches the as-wired top row of IN / DEPTH / OUT.

| | Col 1 (Inputs) | Col 2 (Voicing / Strike) | Col 3 (Outputs) |
|---|---|---|---|
| Row 1 | ◯ IN A — XS1 | ⊙ DEPTH A — P3, 500K log (A) | ◯ OUT A — XS4 |
| Row 2 | ⊙ ATTEN A — P1, 100K lin (B) | ⊙ MANUAL A — P2, 100K lin (B) | ● LED A (3mm red) |
| Row 3 | ◯ CV A — XS3 | ◯ STRIKE A — XS2 | — (spare; reserve for L4 DAMP) |
| Row 4 | ◯ IN B — XS5 | ⊙ DEPTH B — P7, 500K log (A) | ◯ OUT B — XS8 |
| Row 5 | ⊙ ATTEN B — P5, 100K lin (B) | ⊙ MANUAL B — P6, 100K lin (B) | ● LED B (3mm red) |
| Row 6 | ◯ CV B — XS7 | ◯ STRIKE B — XS6 | ◯ MIX OUT — XS9 |

Logic: each channel is a self-contained 3×3 block stacked vertically (A above B). Columns are themed — **Col 1 = inputs** (IN, ATTEN, CV), **Col 2 = voicing/excitation** (DEPTH, MANUAL, STRIKE), **Col 3 = outputs** (OUT, status LED). ATTEN sits directly above its paired CV jack; each status LED sits beside its channel's OUT. The shared MIX OUT (XS9) anchors the very bottom-right; the row-3 col-3 spare cell is reserved for a future shared **L4 DAMP** pot (also cross-channel, so a central position suits it).

---

## BUILD ORDER

Use the visualizer's build-phase view (filter Phase 1–5 in the side panel). Each phase has a `test` field with bench checks. Summary (rev 0.17 — the old "Channel B mirror" phase is now split into two, mirroring A's first-sound / pingable split):

- **Phase 1** — first sound on Channel A with MANUAL knob. The Phase 1 checklist at the top of this document is the bench-tickable version.
- **Phase 2** — Channel A pingable: add CV input, STRIKE input, and R_STATUS_A + LED A.
- **Phase 3** — first sound on Channel B with MANUAL (mirror of Phase 1): DA2 + VC_B audio path + driver minimum + LED drive.
- **Phase 4** — Channel B pingable (mirror of Phase 2): CV input, STRIKE input, R_STATUS_B + LED B.
- **Phase 5** — Mix output bus.

## OPEN QUESTIONS / LIKELY ITERATIONS

Even with the 36-row budget, expect to walk the placement physically and find corrections. Probable areas:

1. **Long R23 jumper** — CHA_OUT (row 5L) to mix bus (row 30R) is ~25 rows vertical. Acceptable on a breadboard but the longest single wire on the board. Consider running it along the spine (column a or column j) as a clean trace.
2. **Long R10 jumper** — BUF_OUT_B (row 28R) to vactrol B LDR1 input (row 22L) is ~6 rows and crosses the centre gap. Should be fine.
3. **R3 / R9 (4M7) horizontal across the centre gap** — each spans col d-row 7L to col h-row 8R (for R3). May need to re-route as two vertical halves with a short jumper across the gap. Same for R9.
4. **Vactrol LED-series jumper** — for the 2-singles vactrol, you need a wire from socket pin 2 (LED1 cathode) to socket pin 5 (LED2 anode). This wire is internal to the vactrol assembly; might be soldered to the socket leg or installed as a short wire bridge during socket population.
5. **DA3 column congestion** — rows 14-17 each carry many resistor leads (3-4 summing R per row, plus IC pin and feedback R). Watch the column count.

Once walked physically on the breadboard and any of these need fixing, increment to rev 0.3.

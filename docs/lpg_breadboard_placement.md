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

### Socket placement

Row-by-row placement is **not repeated here** — see the generated maps below, or open
`tools/visualizer/index.html` and step through the build phases. Two centre-gap bridges per
channel connect SIP_L pin 2 to SIP_R pin 3 (the LED chain) and SIP_L pin 4 to SIP_R pin 1 (the
LDR chain); the visualiser draws both.

SIP_L plugs in standard orientation, SIP_R **flipped 180°** — the notch in the visualiser marks
the pin-1 end of each, so the two read differently on screen.

---

## ⚠️ JSON IS AUTHORITATIVE FOR PLACEMENT

**[tools/visualizer/layouts/lpg.json](../tools/visualizer/layouts/lpg.json) is the source of truth for placement.** The maps below are auto-generated from it by `gen_rowmap.py` and regenerated by `check.sh`, which also runs `validate_layout.py` (hole collisions, net labels vs IC pins, unbridged nets, wire staging) and `cross_check_nets.py` (every component on the nets the netlist requires). Nothing in this document restates a position by hand — that is how the earlier revisions of it drifted.

---

## BUILD PHASES

Per-phase build steps and bench tests live in the layout itself and are shown in the
visualiser's side panel as you step through the phases — that way they cannot drift from the
placement they describe.

---

## FULL BOARD MAPS — generated from JSON (authoritative)

These two tables are produced by `tools/visualizer/gen_rowmap.py` straight from `tools/visualizer/layouts/lpg.json` (the authoritative placement source). **Re-run that script after any layout change — do not hand-edit between the markers.** The breadboard map covers the main grid (cols a–j); the control-board map covers the n8synth control columns (`ctrlL`/`ctrlR`, outboard of the power rails). Power rails (pwrL/pwrR) are not shown — parity rule: `pwrL` odd=GND/even=+12V, `pwrR` odd=GND/even=-12V.

<!-- GEN:MAPS:START — auto-generated by tools/visualizer/gen_rowmap.py from lpg.json rev 0.26-photo-recon. Do not hand-edit between these markers; re-run the generator. -->

### Breadboard row map (cols a–j) — rev 0.26-photo-recon

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
| 10 | `GND` | VD5.2@c (Zener 6v8) | `CV_PROT_A` | R13.1@h (100K), _JW_P1cA_, _JW_R16_IN_ |
| 11 | `—` | — | `C15_b` | C15.2@f (1uF), R15.1@g (10K), VD1.1@h (1N4148) |
| 12 | `—` | — | `STRIKE_PULSE_A` | R34.1@g (10K), VD1.2@h (1N4148) |
| 13 | `—` | — | `C15_a` | C15.1@f (1uF), R17.1@h (1K) |
| 14 | `DRV_B_NINV` | R14.1@b (10K), **DA3.5**@e | `VEE` | **DA3.4**@f, C6.1@h (100nF) |
| 15 | `DRV_SUM_B` | R39.2@a (4K7), _JW_R33_IN_, R35.2@c (10K), R20.2@d (10K), **DA3.6**@e | `DRV_A_NINV` | **DA3.3**@f, R37.1@h (10K) |
| 16 | `DRV_OUT_B` | _JW_P7cB_, R20.1@c (10K), R_STATUS_B.1@d (4K7), **DA3.7**@e | `DRV_SUM_A` | **DA3.2**@f, R34.2@g (10K), R36.2@h (10K), R38.2@i (4K7), R32.2@j (4K7) |
| 17 | `VCC` | C5.1@b (100nF), **DA3.8**@e | `DRV_OUT_A` | **DA3.1**@f, R36.1@g (10K), R_STATUS_A.1@h (4K7), _JW_P3cA_ |
| 18 | `STRIKE_PULSE_B` | R35.1@d (10K), VD2.2@e (1N4148) | `C16_b` | VD2.1@f (1N4148), C16.2@g (1uF), R31.1@h (10K) |
| 20 | `C16_a` | — | `C16_a` | C16.1@g (1uF), R25.2@h (1K), _JW_P5cB_ |
| 21 | `—` | — | `CV_PROT_B` | R19.1@h (100K), R22.2@j (1K) |
| 22 | `V_p_B` | R11.1@a (10K), R9.1@b (4M7), C14.1@c (1nF), **VC_B_L.1**@d | `VC_B_LDR1_IN` | **VC_B_R.4**@g, R10.2@h (10K) |
| 23 | `LED_CHAIN_MID_B` | **VC_B_L.2**@d, _JW_VCB_MID_ | `LED_CHAIN_MID_B` | _JW_VCB_MID_, **VC_B_R.3**@g |
| 24 | `LED_DRIVE_B` | R12.2@b (470R), VD6.1@c (Zener 6v8), **VC_B_L.3**@d | `GND` | **VC_B_R.2**@g |
| 25 | `V_x_B` | C12.1@b (220pF), **VC_B_L.4**@d, _JW_VCB_VX_ | `V_x_B` | _JW_VCB_VX_, **VC_B_R.1**@g |
| 26 | `GND` | VD6.2@c (Zener 6v8) | `—` | — |
| 27 | `V_OUT_B_PRE_BUF` | R11.2@a (10K), **DA2.5**@e | `VEE` | **DA2.4**@f, C8.1@h (100nF) |
| 28 | `FILT_BUF_B_INV` | _JW_DA2_UGB_, **DA2.6**@e | `CHB_IN` | **DA2.3**@f, R7.1@h (100K), _JW_INB_ |
| 29 | `CHB_OUT` | R_OUT_B.1@a (1K), _JW_DA2_UGB_, _JW_CHB_OUT_BUS_, **DA2.7**@e | `IN_BUF_B_INV` | **DA2.2**@f, _JW_DA2_UGA_ |
| 30 | `VCC` | C7.1@b (100nF), **DA2.8**@e | `BUF_OUT_B` | **DA2.1**@f, _JW_DA2_UGA_, R10.1@h (10K) |
| 31 | `MIX_OUT_JACK` | _JW_MIX_, C17.2@b (100nF) | `CHB_OUT` | _JW_CHB_OUT_BUS_, R26.1@i (100K) |
| 32 | `MIX_OUT` | C17.1@d (100nF), _JW_MIX_OUT_X_ | `—` | — |
| 33 | `SPARE_NINV` | _JW_DA4_SP_NINV_GND_, **DA4.5**@e | `VEE` | **DA4.4**@f, C10.1@h (100nF) |
| 34 | `SPARE_INV` | _JW_DA4_SP_FB_, **DA4.6**@e | `MIX_NINV` | **DA4.3**@f, R28.1@h (100K) |
| 35 | `SPARE_OUT` | _JW_DA4_SP_FB_, **DA4.7**@e | `MIX_BUS` | **DA4.2**@f, R23.2@h (100K), R26.2@i (100K), R24.1@j (100K) |
| 36 | `VCC` | C9.1@b (100nF), **DA4.8**@e | `MIX_OUT` | **DA4.1**@f, _JW_MIX_OUT_X_, R24.2@j (100K) |

### Control-board map (ctrlL / ctrlR) — rev 0.26-photo-recon

| Row | Left CTRL (ctrlL) | Right CTRL (ctrlR) |
|-----|-------------------|--------------------|
| 1 | OUTA, R_OUT_A.2@ctrlLi (1K) | INA, _JW_INA_ |
| 4 | P2a ⏚ | P3a ↔b |
| 5 | P2b, _JW_R32_MAN_A_ | P3b, R6.1@ctrlRi (470R) |
| 6 | P2c, R29.1@ctrlLi (4K7) | P3c, _JW_P3cA_ |
| 7 | LAa ⏚ | P1a ⏚ |
| 8 | LAb, _JW_STATA_ | P1b, R38.1@ctrlRi (4K7) |
| 9 | — | P1c, _JW_P1cA_ |
| 11 | _JW_CHA_OUT_BUS_, _JW_CHA_OUT_X_ | R6.2@ctrlRi (470R), _JW_R6_LED_A_ |
| 12 | — | R17.2@ctrlRi (1K), _JW_R17_IN_ |
| 13 | R39.1@ctrlLi (4K7), _JW_R39_CVB_ | R_STATUS_A.2@ctrlRo (4K7), _JW_STATA_ |
| 14 | R_STATUS_B.2@ctrlLi (4K7), _JW_STATB_ | R16.2@ctrlRi (1K), _JW_R16_IN_ |
| 15 | _JW_R33_IN_, _JW_R33_X_ | R32.1@ctrlRo (4K7), _JW_R32_MAN_A_ |
| 17 | MIX, _JW_MIX_ | CVA, R16.1@ctrlRi (1K) |
| 20 | P7a ↔b | STA, _JW_R17_IN_ |
| 21 | P7b, R12.1@ctrlLi (470R) | — |
| 22 | P7c, _JW_P7cB_ | — |
| 23 | OUTB, R_OUT_B.2@ctrlLi (1K) | INB, _JW_INB_ |
| 26 | — | R25.1@ctrlRi (1K), _JW_R25_STRB_ |
| 28 | — | R23.1@ctrlRo (100K), _JW_CHA_OUT_X_ |
| 29 | — | R22.1@ctrlRi (1K), _JW_R22_X_ |
| 30 | R30.2@ctrlLi (4K7), _JW_R30_12V_ | R33.2@ctrlRi (4K7), _JW_R33_X_ |
| 32 | LBa ⏚ | P5a ⏚ |
| 33 | LBb, _JW_STATB_ | P5b, _JW_R39_CVB_ |
| 34 | — | P5c, _JW_P5cB_ |
| 35 | STB, _JW_R25_STRB_ | P6a ⏚ |
| 36 | — | P6b, R33.1@ctrlRi (4K7) |
| 37 | — | P6c, _JW_R30_12V_ |
| 38 | — | CVB, _JW_R22_X_ |

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

# MOD2 — Definitive Netlist

**Purpose:** Authoritative netlist for the n8synth 6HP breadboard build. Format follows
`lpg_netlist.md` so `netlist_to_layout.py` can parse it.

**Sources (in order of authority):**
1. HAGIWO MOD2 **Rev A** schematic (KiCad 7.0.6, 2025MAR29) — topology and designators
2. JLCPCB BOM from the note.com article — component values, confirms C15 DNP
3. Firmware headers (`snare.ino` et al.) — pin function confirmation
4. `mod2_reference_review.md` — the three departures from stock

**Departures from stock MOD2** (see reference review for rationale):
- **U4 7805** local +5V regulation from +12V; bus +5V left unconnected
- **Dual indicator** — plain LED (D9) + WS2812B breakout (LED1), both on GPIO5
- **SW2 / SW3** — JP1 and JP2 promoted from PCB jumpers to panel switches

**Designator note:** pots are **P1–P3** here (HAGIWO calls them RV1–RV3) to match repo
convention and the parser. All other designators follow the Rev A schematic. There is no J5 on
the original schematic; the gap is preserved rather than renumbered.

**Confidence tags:** ✓ = read directly from Rev A schematic and confirmed by BOM.
⚠ = our addition, not in the original. ? = needs bench confirmation.

---

## BOM

### Resistors (24 stock + 0 added)
| Qty | Value | Designators | Role |
|-----|-------|-------------|------|
| 7 | 10K | R1, R2, R3, R5, R9, R10, R15 | ADC series, CV series, buffer outputs, summer feedback |
| 6 | 1K | R14, R16, R17, R18, R19, R23 | Offset series, ADC series, RC poles, switch series, output series |
| 3 | 3K3 | R12, R13, R24 | Gate series to GPIO, LED current limit |
| 2 | 4K7 | R7, R8 | Gate input pulldowns |
| 2 | 100K | R4, R20 | CV divider upper, amplifier input bias |
| 2 | 33K | R11, R21 | Offset injection from -12V, amplifier gain lower |
| 1 | 220K | R6 | CV divider lower |
| 1 | 68K | R22 | Amplifier feedback |

**Verified against BOM:** every group above matches a JLCPCB line item exactly. ✓

### Capacitors (19 fitted + 1 DNP + 3 added)
| Qty | Value | Type | Designators | Role |
|-----|-------|------|-------------|------|
| 9 | 100nF | Ceramic | C2, C3, C4, C7, C8, C9, C10, C11, C19 | ADC filters, rail bypass, debounce, 3V3 decoupling |
| 4 | 10uF | Electrolytic | C1, C5, C6, C20 | Rail bulk on +5V, +12V, -12V, +3V3 |
| 3 | 22nF | Film | C12, C14, C17 | A2 filter, RC pole 1 switched, RC pole 2 switched |
| 2 | 10nF | Film | C13, C16 | RC pole 1 fixed, RC pole 2 fixed |
| 1 | 1uF | Film | C18 | Output AC coupling |
| 3 | 100nF | Ceramic | C22, C23, C24 | 7805 output, 3V3 at deck end, WS2812B supply |
| 1 | 330nF | Ceramic | C21 | 7805 input |

**C15 (10nF) is DNP** — drawn crossed-out on Rev A and absent from the BOM. Omitted here. ✓
**C21–C24 are additions** ⚠ — 7805 datasheet decoupling, the deck-end 3V3 cap, and the
WS2812B supply bypass.

### Semiconductors
| Qty | Type | Designators | Role |
|-----|------|-------------|------|
| 2 | 1N4148 | D1, D2 | Power rail reverse-polarity protection |
| 6 | 1N5819 | D3, D4, D5, D6, D7, D8 | Schottky input clamps (Rev A uses B5819W) |
| 1 | LED | D9 | Plain indicator, MOD2 firmwares |
| 1 | 1N4148 | D10 | WS2812B supply drop, 5V to ~4.3V |
| 2 | TL072 | U1, U2 | Buffers, CV summer, output amplifier |
| 1 | XIAO RP2350 | U3 | Microcontroller module |
| 1 | 7805 | U4 | +5V linear regulator |

**D10 and U4 are additions.** ⚠ BAT85 is a better small-signal substitute for D3–D8 than 1N5819
if to hand; either works.

### Potentiometers
| Qty | Value | Taper | Designator | Label | Wiring |
|-----|-------|-------|------------|-------|--------|
| 1 | 100K | B (lin) | P1 | POT1 | Divider: pin3 +3V3, pin2 wiper to R1, pin1 GND |
| 1 | 100K | B (lin) | P2 | POT2 | Divider: pin3 +3V3, pin2 wiper to R2, pin1 GND |
| 1 | 100K | B (lin) | P3 | POT3 | Divider: pin3 +3V3, pin2 wiper to R5, pin1 GND |

⚠ **Pin 3 is the +3.3V end and pin 1 is ground** — read directly off the schematic for all three
pots (RV1/RV2/RV3). Reversing them inverts every knob's direction of travel.

### Connectors
| Qty | Type | Designator | Label |
|-----|------|------------|-------|
| 1 | 2x8 pin header | J1 | Eurorack power 16-pin |
| 1 | Switched mono jack | J2 | CV IN |
| 1 | Switched mono jack | J3 | IN2 / LEVEL |
| 1 | Switched mono jack | J4 | IN1 / TRIG |
| 1 | Switched mono jack | J6 | AUDIO OUT |

### Switches and modules (not parser-tracked)
| Qty | Type | Designator | Label | Role |
|-----|------|------------|-------|------|
| 1 | 6x6mm tactile | SW1 | BUTTON | Manual trigger / mode, GPIO6 |
| 1 | SPST toggle | SW2 | FILTER | ⚠ JP1 — closed = 5.0 kHz, open = 15.9 kHz |
| 1 | SPST toggle | SW3 | DC | ⚠ JP2 — closed = DC-coupled, open = AC-coupled |
| 1 | NeoPixel breakout | LED1 | RGB | ⚠ Adafruit 5975, 5050 GRB, panel-mounted |

---

## NET NAMES

| Net | Description |
|-----|-------------|
| P12V | +12V after reverse-polarity diode D1 |
| N12V | -12V after reverse-polarity diode D2 |
| P5V | Regulated +5V from U4 (7805) |
| P3V3 | +3.3V from the XIAO's onboard LDO — pot supply **and ADC reference** |
| P3V3_DECK | +3.3V at the control-deck end of the run (star-fed from P3V3) |
| GND | Ground (0V) |
| POT1_W | POT1 wiper |
| POT2_W | POT2 wiper |
| POT3_W | POT3 wiper |
| A0 | ADC0 — POT1 |
| A1 | ADC1 — POT2 |
| A2 | ADC2 — summed POT3 + CV, inverted |
| U1A_IN | POT3 buffer non-inverting input |
| POT3_BUF | POT3 buffer output (U1A, follower) |
| CV_IN | CV jack tip (J2) |
| CV_MID | Junction R3/R4 |
| CV_DIV | CV divider output into U1B |
| CV_BUF | CV buffer output (U1B, follower) |
| OFFSET_MID | Junction R11/R14 — offset injection from -12V |
| SUM_INV | U2A inverting summing node |
| SUM_OUT | U2A output |
| IN1_J | IN1 jack tip (J4) |
| IN2_J | IN2 jack tip (J3) |
| GPIO7 | Trigger input to MCU |
| GPIO0 | Level/accent input to MCU |
| GPIO6 | Push switch input to MCU |
| SW_NODE | Switch node between R18 and SW1 |
| PWM_OUT | GPIO1 — PWM audio out |
| RC_A | RC reconstruction filter, pole 1 |
| RC_B | RC reconstruction filter, pole 2 |
| CAP_SW | Common bottom node of C14/C17 — switched to GND by SW2 |
| AMP_IN | U2B non-inverting input |
| AMP_FB | U2B feedback node (R21/R22 junction) |
| AMP_OUT | U2B output |
| OUT_J | Audio output jack tip (J6) |
| LED_DRIVE | GPIO5 — drives both indicators |
| LED_A | Plain LED anode, after R24 |
| NPX_VDD | WS2812B supply, ~4.3V after D10 |

---

## NETLIST BY FUNCTIONAL BLOCK

### BLOCK 1: Power Input and Protection
**Source: Rev A schematic sheet D1 ✓**

Standard Eurorack ±12V with series reverse-polarity diodes and split bulk/bypass decoupling.
The bus +5V pin on J1 is **deliberately left unconnected** — see Block 2.

| Component | Value | Pin 1 | Pin 2 | Pin 3 |
|-----------|-------|-------|-------|-------|
| D1 | 1N4148 | BUS_P12V (anode) | P12V (cathode) | — |
| D2 | 1N4148 | N12V (anode) | BUS_N12V (cathode) | — |
| C5 | 10uF | P12V | GND | — |
| C7 | 100nF | P12V | GND | — |
| C9 | 100nF | P12V | GND | — |
| C6 | 10uF | GND | N12V | — |
| C8 | 100nF | N12V | GND | — |
| C10 | 100nF | N12V | GND | — |

**Notes:**
- Observe polarity on C5/C6 — C6 sits on a negative rail.
- J1 is a 16-pin header on the original. The n8synth power section provides +12V, -12V, GND
  and +5V; only the first three are used.

---

### BLOCK 2: +5V Regulation
**Source: our departure, not in Rev A ⚠**

The n8synth's bus +5V is too noisy for this application, and on the stock MOD2 that rail feeds
the XIAO's LDO — whose 3.3V output is simultaneously the pot supply and the ADC reference.
Regulating locally from +12V removes bus noise from the measurement path.

| Component | Value | Pin 1 | Pin 2 | Pin 3 |
|-----------|-------|-------|-------|-------|
| U4 | 7805 | P12V (IN) | GND (COM) | P5V (OUT) |
| C21 | 330nF | P12V | GND | — |
| C22 | 100nF | P5V | GND | — |
| C1 | 10uF | P5V | GND | — |
| C4 | 100nF | P5V | GND | — |

**Notes:**
- C21/C22 are datasheet-typical values. C1/C4 are the stock MOD2 caps, retained downstream.
- Dissipation ≈ (12 − 5) × 65 mA ≈ **0.46 W**; ~30 °C rise on a bare TO-220, no heatsink. ?
- Adding the WS2812B at full brightness roughly doubles this — bench-check. ?

---

### BLOCK 3: Microcontroller and 3V3 Rail
**Source: Rev A schematic sheet C4 ✓, C23 added ⚠**

U3 pin assignments are tabulated under OP-AMP PIN ASSIGNMENTS below.

| Component | Value | Pin 1 | Pin 2 | Pin 3 |
|-----------|-------|-------|-------|-------|
| C19 | 100nF | P3V3 | GND | — |
| C20 | 10uF | P3V3 | GND | — |
| C23 | 100nF | P3V3_DECK | GND | — |

**Notes:**
- P3V3 is generated by the XIAO's onboard LDO from P5V — it is an **output**, never driven.
- **Star-feed** P3V3 to the pot tops; do not daisy-chain through other loads. Pot measurement
  is ratiometric, so common-mode noise cancels — differential noise across the wiring does not.
- C23 ⚠ sits at the control-deck end of the P3V3 run, guarding against pickup on a long
  breadboard wire.
- A0/A1 are hard-filtered at ~159 Hz by R1/C2 and R2/C3. **A2 is the exposed channel** at
  ~7.2 kHz — it is the canary for supply noise at bench test. ?

---

### BLOCK 4: POT1 and POT2 Direct ADC Inputs
**Source: Rev A schematic sheet A1 ✓**

Two plain potentiometer dividers into the ADC, each with a series resistor and filter cap.

| Component | Value | Pin 1 | Pin 2 | Pin 3 |
|-----------|-------|-------|-------|-------|
| P1 (100K B) | POT1 | GND (pin 1) | POT1_W (pin 2 wiper) | P3V3_DECK (pin 3) |
| R1 | 10K | POT1_W | A0 | — |
| C2 | 100nF | A0 | GND | — |
| P2 (100K B) | POT2 | GND (pin 1) | POT2_W (pin 2 wiper) | P3V3_DECK (pin 3) |
| R2 | 10K | POT2_W | A1 | — |
| C3 | 100nF | A1 | GND | — |

**Notes:**
- R1/C2 and R2/C3 give fc = 1/(2π × 10K × 100nF) ≈ **159 Hz** — heavy smoothing, appropriate
  for a knob.

---

### BLOCK 5: POT3 and CV Summing Front End
**Source: Rev A schematic sheet B2-C3 ✓**

POT3 and the CV jack are each buffered, then summed by an inverting amplifier with a fixed
positive offset injected from the -12V rail. This is why POT3 reads backwards in firmware.

| Component | Value | Pin 1 | Pin 2 | Pin 3 |
|-----------|-------|-------|-------|-------|
| P3 (100K B) | POT3 | GND (pin 1) | POT3_W (pin 2 wiper) | P3V3_DECK (pin 3) |
| R5 | 10K | POT3_W | U1A_IN | — |
| R9 | 10K | POT3_BUF | SUM_INV | — |
| R3 | 10K | CV_IN | CV_MID | — |
| R4 | 100K | CV_MID | CV_DIV | — |
| R6 | 220K | CV_DIV | GND | — |
| R10 | 10K | CV_BUF | SUM_INV | — |
| R11 | 33K | N12V | OFFSET_MID | — |
| R14 | 1K | OFFSET_MID | SUM_INV | — |
| R15 | 10K | SUM_INV | SUM_OUT | — |
| R16 | 1K | SUM_OUT | A2 | — |
| C12 | 22nF | A2 | GND | — |
| D7 | 1N5819 | A2 (anode) | P3V3 (cathode) | — |
| D8 | 1N5819 | GND (anode) | A2 (cathode) | — |

**Notes:**
- **CV divider:** 220K / (10K + 100K + 220K) = **×0.667**, so 0–5V CV → 0–3.33V. ✓
- **Offset:** R11 + R14 = 34K from -12V into a 10K feedback → +3.53V at SUM_OUT.
- **Transfer function: A2 ≈ 3.53 − POT3 − CV.** 5V CV reads 0V; 0V CV reads 3.3V. ✓
  Independently confirmed by `snare.ino`, which documents POT3 as *"reversed ADC"*.
- D7/D8 clamp A2 to the 0 → 3.3V window, protecting the ADC from out-of-range CV.
- U1B tolerates CV well beyond 5V because it runs on ±12V; the clamps handle the rest.

---

### BLOCK 6: Gate Inputs
**Source: Rev A schematic sheet A2-B2 ✓**

Two identical trigger/gate inputs with series protection, pulldown, and Schottky clamps.

| Component | Value | Pin 1 | Pin 2 | Pin 3 |
|-----------|-------|-------|-------|-------|
| R8 | 4K7 | IN1_J | GND | — |
| R13 | 3K3 | IN1_J | GPIO7 | — |
| D5 | 1N5819 | GPIO7 (anode) | P3V3 (cathode) | — |
| D6 | 1N5819 | GND (anode) | GPIO7 (cathode) | — |
| R7 | 4K7 | IN2_J | GND | — |
| R12 | 3K3 | IN2_J | GPIO0 | — |
| D3 | 1N5819 | GPIO0 (anode) | P3V3 (cathode) | — |
| D4 | 1N5819 | GND (anode) | GPIO0 (cathode) | — |

**Notes:**
- **3K3 + 4K7 = 8K total pulldown**, required by the RP2350 pulldown errata. Do not increase. ✓
- IN1 (GPIO7) is the trigger on every drum firmware; IN2 (GPIO0) is accent/level.

---

### BLOCK 7: PWM Reconstruction Filter
**Source: Rev A schematic sheet C3-C4 ✓, SW2 replaces JP1 ⚠**

Two-pole RC filter smoothing the PWM carrier. The 22nF caps are switched to ground together,
shifting both poles at once.

| Component | Value | Pin 1 | Pin 2 | Pin 3 |
|-----------|-------|-------|-------|-------|
| R17 | 1K | PWM_OUT | RC_A | — |
| C13 | 10nF | RC_A | GND | — |
| C14 | 22nF | RC_A | CAP_SW | — |
| R19 | 1K | RC_A | RC_B | — |
| C16 | 10nF | RC_B | GND | — |
| C17 | 22nF | RC_B | CAP_SW | — |
| SW2 (SPST) | FILTER | CAP_SW | GND | — |

**Notes:**
- **SW2 open** → C14/C17 float → 10nF per pole → **fc = 15.9 kHz** (snare, hihat, clap). ✓
- **SW2 closed** → C14/C17 grounded → 32nF per pole → **fc = 5.0 kHz** (kick, bass). ✓
- On Rev A this is JP1, a 3-pin `Jumper_3_Open`. Its pin 1 returns to RC_B **through C15, which
  is DNP**, so position 1–2 does nothing. Only two states are real, and an SPST reproduces both.
- C15 omitted entirely from this build.

---

### BLOCK 8: Output Amplifier and Coupling
**Source: Rev A schematic sheet C4-C5 ✓, SW3 replaces JP2 ⚠**

Non-inverting gain stage on ±12V, lifting the 3.3V PWM signal to Eurorack level.

| Component | Value | Pin 1 | Pin 2 | Pin 3 |
|-----------|-------|-------|-------|-------|
| C18 | 1uF | RC_B | AMP_IN | — |
| SW3 (SPST) | DC | RC_B | AMP_IN | — |
| R20 | 100K | AMP_IN | GND | — |
| R21 | 33K | AMP_FB | GND | — |
| R22 | 68K | AMP_FB | AMP_OUT | — |
| R23 | 1K | AMP_OUT | OUT_J | — |

**Notes:**
- **Gain = 1 + R22/R21 = 1 + 68K/33K = 3.06.** 3.3 Vpp PWM × 3.06 ≈ **10.1 Vpp**. ✓
  This is the origin of the published 10V output spec.
- **SW3 open** → C18 active → **AC-coupled**. High-pass with R20 at ~1.6 Hz; ±5V about 0V.
- **SW3 closed** → C18 shorted → **DC-coupled**, unipolar 0 → ~9.9V. Needed for `tides`
  LFO / AD / AR modes, whose low-frequency content would droop through a 1.6 Hz high-pass.
- R23 provides output short-circuit protection.

---

### BLOCK 9: Dual Indicator
**Source: D9/R24 from Rev A ✓, LED1/D10/C24 added ⚠**

Both indicator types share GPIO5. Whichever does not match the loaded firmware stays dark —
the two use incompatible signalling, so this needs no firmware support.

| Component | Value | Pin 1 | Pin 2 | Pin 3 |
|-----------|-------|-------|-------|-------|
| R24 | 3K3 | LED_DRIVE | LED_A | — |
| D9 | LED | LED_A (anode) | GND (cathode) | — |
| D10 | 1N4148 | P5V (anode) | NPX_VDD (cathode) | — |
| C24 | 100nF | NPX_VDD | GND | — |

**LED1 (WS2812B breakout, Adafruit 5975) — panel-mounted, wired:**
| Terminal | Net |
|-----|-----|
| VIN | NPX_VDD |
| DIN | LED_DRIVE |
| GND | GND |

**Notes:**
- **MOD2 firmwares** drive GPIO5 with `digitalWrite`/PWM → D9 works, LED1 stays dark.
- **Melon firmwares** drive GPIO5 with NeoPixel data → LED1 works, D9 sees <1% duty and reads
  as dark.
- **D10 drops P5V to ~4.3V** ⚠ — inside the WS2812B 3.7–5.3V supply range *and* lowering the
  data threshold to 0.7 × 4.3 ≈ **3.0V**, comfortably below the RP2350's 3.3V drive. ?
  Alternatives if preferred: link out D10 and run LED1 from P3V3 (Adafruit-sanctioned, below
  datasheet minimum), or fit a WS2812B-V5 and run at 5V.
- **Use a 5050-based breakout, not a 5mm through-hole NeoPixel** — through-hole parts are
  **RGB** byte order while the firmware declares `NEO_GRB`, which would swap red and green.
- LED1 does not fit a JPS cell footprint; mount on M2 standoffs behind the panel.

---

### BLOCK 10: Push Switch
**Source: Rev A schematic sheet D3 ✓**

| Component | Value | Pin 1 | Pin 2 | Pin 3 |
|-----------|-------|-------|-------|-------|
| R18 | 1K | GPIO6 | SW_NODE | — |
| SW1 | — | SW_NODE | GND | — |
| C11 | 100nF | GPIO6 | GND | — |

**Notes:**
- GPIO6 uses the RP2350's **internal pull-up**; no external pull-up is fitted.
- R18 + C11 form the debounce network. Pressing SW1 pulls GPIO6 low through 1K.

---

## OP-AMP PIN ASSIGNMENTS

Both op-amps are TL072 dual devices in DIP-8, powered from ±12V.

### U1 (TL072): POT3 buffer and CV buffer
| Pin | Function | Net |
|-----|----------|-----|
| 1 | OUT A | POT3_BUF |
| 2 | IN- A | POT3_BUF |
| 3 | IN+ A | U1A_IN |
| 4 | V- | N12V |
| 5 | IN+ B | CV_DIV |
| 6 | IN- B | CV_BUF |
| 7 | OUT B | CV_BUF |
| 8 | V+ | P12V |

Both halves are unity-gain followers (output tied to inverting input).

### U2 (TL072): CV summer and output amplifier
| Pin | Function | Net |
|-----|----------|-----|
| 1 | OUT A | SUM_OUT |
| 2 | IN- A | SUM_INV |
| 3 | IN+ A | GND |
| 4 | V- | N12V |
| 5 | IN+ B | AMP_IN |
| 6 | IN- B | AMP_FB |
| 7 | OUT B | AMP_OUT |
| 8 | V+ | P12V |

### U3 (XIAO RP2350): Microcontroller
| Pin | Function | Net |
|-----|----------|-----|
| 1 | D0 GPIO26 ADC0 right-top | A0 |
| 2 | D1 GPIO27 ADC1 right | A1 |
| 3 | D2 GPIO28 ADC2 right | A2 |
| 4 | D3 GPIO5 right | LED_DRIVE |
| 5 | D4 GPIO6 right | GPIO6 |
| 6 | D5 GPIO7 right | GPIO7 |
| 7 | D6 GPIO0 right-bottom | GPIO0 |
| 8 | D7 GPIO1 left-bottom | PWM_OUT |
| 9 | D8 GPIO2 left | NC |
| 10 | D9 GPIO4 left | NC |
| 11 | D10 GPIO3 left | NC |
| 12 | 3V3 left | P3V3 |
| 13 | GND left | GND |
| 14 | VBUS 5V left-top | P5V |

**Physical layout confirmed from the board silkscreen** ✓ — viewed from above, component side,
USB at top. Numbering is DIP-style: right side 1–7 top to bottom, left side 8–14 bottom to top.

```
                 ┌─────────────────┐
                 │      USB-C      │
   VBUS   14 ────┤                 ├──── 1   D0  / GPIO26 / A0
   GND    13 ────┤                 ├──── 2   D1  / GPIO27 / A1
   3V3    12 ────┤  XIAO  RP2350   ├──── 3   D2  / GPIO28 / A2
   D10    11 ────┤                 ├──── 4   D3  / GPIO5
   D9     10 ────┤                 ├──── 5   D4  / GPIO6
   D8      9 ────┤                 ├──── 6   D5  / GPIO7
   D7      8 ────┤                 ├──── 7   D6  / GPIO0
                 └─────────────────┘
```

**Breadboard rows.** The module straddles the centre gap and spans seven rows, N to N+6:

| Row | Left pin | Left net | Right pin | Right net |
|-----|----------|----------|-----------|-----------|
| N   | VBUS | P5V | D0 | A0 — POT1 |
| N+1 | GND | GND | D1 | A1 — POT2 |
| N+2 | 3V3 | P3V3 | D2 | A2 — CV + POT3 |
| N+3 | D10 | *unused* | D3 | LED_DRIVE — GPIO5 |
| N+4 | D9 | *unused* | D4 | GPIO6 — push switch |
| N+5 | D8 | *unused* | D5 | GPIO7 — IN1 trigger |
| N+6 | D7 | PWM_OUT — GPIO1 | D6 | GPIO0 — IN2 level |

**Layout consequences worth exploiting:**
- The **whole power trio (VBUS/GND/3V3) sits at the top-left**, adjacent to each other — feed
  all three from one place, and keep C19/C20 tight against rows N+1/N+2.
- **All three unused pins are contiguous on the left** (rows N+3 to N+5), so that stretch of
  left-hand rows is free for routing.
- ⚠ **PWM_OUT and the IN2 gate input share row N+6**, on opposite sides. That puts the PWM
  carrier directly across from a digital input — keep the R17/R19 filter chain and the gate
  wiring physically apart rather than running them alongside each other.

**Confidence.** The GPIO numbers are certain — labelled on the Rev A schematic and matching the
firmware constants (`PWM_AUDIO_PIN = 1`, `TRIG_IN_PIN = 7`, `VOLUME_HALF_IN_PIN = 0`,
`PUSH_BUTTON_PIN = 6`, `MOD2_LED_PIN = 5`). The physical positions are read from the board. The
D↔GPIO mapping is corroborated by the schematic's unused-pin marks: HAGIWO used the contiguous
**D0–D7** block, leaving D8/D9/D10 — GPIO2, GPIO3 and GPIO4 — as exactly the three pins drawn
with an X. The only residual ambiguity is *which* of GPIO2/3/4 lands on D8/D9/D10, and since all
three are unconnected in this build, it has no effect on placement. ✓

---

## PANEL AND CONTROL DECK ALLOCATION

n8synth 6HP deck `n8-cd-6hp-2x6`: 12 cells in a **2 columns × 6 rows** grid (16.5 mm column
pitch, 17.27 mm row pitch), all wired to the single left-hand strip (`ctrlL`). Each cell has
pads A/B/C plus D on the deck-wide ground bus.

**Cell numbering is ROW-MAJOR — odd numbers down the LEFT column, even down the RIGHT.** ✓
Confirmed from the n8synth annotated control-deck diagram (`6HP-2x6-Control-Deck-Annotated.png`
in the [6HP quick-start guide](https://www.n8synth.co.uk/guides/6hp-eurorack-prototype-kit-quick-start/)),
and corroborated by the footprint x-coordinates in `6HP_Template.n8layout` alternating
0.71 / 17.22 mm. *Not* column-major — the 4-pin gap between JPS6 and JPS7 is a connector
feature, not a column boundary.

### Agreed panel layout

```
              6HP  —  2 × 6
         ┌─────────────────────────┐
    1    │  ( POT1 )       (*)     │   RGB pixel
    2    │  ( POT2 )       (o)     │   plain LED
    3    │  ( POT3 )      [BTN]    │   manual trigger
    4    │   ( CV )       (OUT)    │
    5    │   (IN1)         [DC]    │   AC / DC
    6    │   (IN2)       [FILTER]  │   15k9 / 5k0
         └─────────────────────────┘
          in + control        out + config
```

Left column is everything you patch in and turn; right column is output, indicators and config.
POT3 sits directly above its CV jack (both summed into A2). DC sits directly below OUT, the jack
it governs.

*Trade-off accepted:* the output cable hangs over the two config toggles below it. They are
set-once-per-firmware rather than performance controls, so this was judged acceptable — and it
arguably shields them from being knocked.

### Position → cell → breadboard rows

| Panel | Item | Cell | Rows (A/B/C) | Pads |
|---|---|---|---|---|
| L1 | P1 POT1 | **JPS1** | 1 / 2 / 3 | 3 legs → A/B/C |
| R1 | LED1 WS2812B | **JPS2** | 4 / 5 / 6 | VIN A, DIN B, GND D |
| L2 | P2 POT2 | **JPS3** | 7 / 8 / 9 | 3 legs → A/B/C |
| R2 | D9 plain LED | **JPS4** | 10 / 11 / 12 | anode A, cathode D |
| L3 | P3 POT3 | **JPS5** | 13 / 14 / 15 | 3 legs → A/B/C |
| R3 | SW1 BUTTON | **JPS6** | 16 / 17 / 18 | A, return D |
| — | *gap* | — | *19 / 20 / 21 / 22* | *free feed-through tie points* |
| L4 | J2 CV | **JPS7** | 23 / 24 / 25 | tip A, sleeve D (B free) |
| R4 | J6 OUT | **JPS8** | 26 / 27 / 28 | tip A, sleeve D (B free) |
| L5 | J4 IN1 | **JPS9** | 29 / 30 / 31 | tip A, sleeve D (B free) |
| R5 | SW3 DC | **JPS10** | 32 / 33 / 34 | RC_B A, AMP_IN B |
| L6 | J3 IN2 | **JPS11** | 35 / 36 / 37 | tip A, sleeve D (B free) |
| R6 | SW2 FILTER | **JPS12** | 38 / 39 / 40 | CAP_SW A, GND D |

**12 of 12 cells — the panel is exactly full.** Any further feature displaces something.

✓ **All 40 breadboard rows are usable tie points**, confirmed against the physical board. The
profile's `powerSectionRows` [37, 40] and `layoutRows` [1, 36] describe the board's power
*area*, **not** a restriction on those rows — JPS11.C (row 37) and JPS12 (rows 38–40) connect
normally. Do not re-derive a caution here; it has been checked.

### Consequences for placement

- **Row-major numbering interleaves the two panel columns down the breadboard.** The pots are
  therefore *not* contiguous: rows 1–3, 7–9, 13–15, with the indicator and button cells at rows
  4–6, 10–12, 16–18 between them.
- **The whole ADC front end lands in rows 1–18** (POT1/POT2/POT3 → A0/A1/A2), so U1, U2 and the
  XIAO belong in the top half, close to their pots. Keep the P3V3 star-feed short.
- **All four jacks land in rows 23–40**, the bottom half — the audio output stage and gate
  conditioning belong down there, near J6/J4/J3.
- **Gap rows 19–22 fall exactly between the control group and the jack group** — free
  feed-through space precisely where signals cross from the front end to the I/O section.
- **SW3 spans two signal nets** (RC_B on A, AMP_IN on B) rather than using the D ground bus —
  the only panel cell that does. Both legs must run back to the output stage.

---

## BUILD PHASE ORDER

Sequenced so each phase is independently testable, and so the two riskiest items are isolated.

| Phase | Blocks | Test |
|---|---|---|
| 1 — Power | 1, 2 | ±12V and +5V present and clean; 7805 temperature after 10 min |
| 2 — MCU alive | 3 | +3.3V present; XIAO enumerates over USB (**Eurorack power disconnected**) |
| 3 — Output path | 7, 8 | Flash any voice; audio at J6; SW2 and SW3 both audibly change the output |
| 4 — Controls | 4, 5, 6, 10 | Pots sweep; trigger fires from J4 and SW1; CV at J2 sweeps A2 |
| 5 — Plain indicator | 9 (D9, R24) | D9 tracks playback on a MOD2 firmware |
| 6 — RGB indicator | 9 (LED1, D10, C24) | Melon `.uf2` drives colour; D9 goes dark |

⚠ **Never connect USB with Eurorack power applied** — HAGIWO's own warning; it back-powers the
bus through the host port.

---

## OPEN ITEMS FOR THE BENCH

1. ~~XIAO RP2350 physical pinout~~ → **Resolved from the board silkscreen.** ✓ Right side 1–7
   top to bottom, left side 8–14 bottom to top; see the U3 table. Residual ambiguity confined
   to GPIO2/3/4, which are unconnected.
2. 7805 thermal figure with the WS2812B lit (~0.9 W worst case).
3. Confirm the WS2812B revision shipped, and whether D10 is needed at all.
4. A2 noise with the 7805 fitted — the canary for the 3.3V decoupling question.
5. ~~`tides` pin map~~ → **Disproved; no issue.** ✓ `tides` uses Arduino D-aliases rather than
   raw GPIO numbers: `PWMOUT D7`→GPIO1, `TRIG_PIN D5`→GPIO7, `MOD_PIN D6`→GPIO0,
   `BUTTON_PIN D4`→GPIO6, `LED_PIN D3`→GPIO5. Against the confirmed silkscreen pinout that is
   an exact match to the standard MOD2 map. The earlier concern conflated D-number with
   GPIO-number.
6. Per-firmware SW2/SW3 settings table — currently reasoned, not measured.

# Gate inputs and gate outputs: review against published designs

Analogue board, checkpoint 1 schematic (sheets 6 and 8). Review date 2026-10-15.

**Verdict:** the topology is sound and matches proven practice. One must-fix (A1): the
gate-input clamps dump current into +3V3D, and the XC6206 cannot sink it. Four cheap
"worth adopting" items follow (B1–B4). Nothing needs a new Extended part type.

Calculations were done in a short script, and downloads and crops were working copies;
none is kept. Values marked **[calc]** are my arithmetic. Values marked
**[unverified]** I could not confirm from a primary source.

---

## 1. Our design, exactly

Sources: `tools/analogue_board/design_digital.py` (`sheet_gate_in` lines 143–222,
`sheet_pots_gates` lines 44–73, `sheet_expander` lines 77–92), and schematic PDF pages 8 and 6.

### 1.1 Gate inputs ×4 (sheet 8)

One channel is shown below with the channel 1 designators. Channels 2–4 are R805–R808 /
D802 / U801B, R809–R812 / D803 / U802A, and R813–R816 / D804 / U802B.

```
GIN1 (jack tip) ─ R801 10k ─┬─────────────┬──────────┬── U801A + (pin 3)
                            │             │          │
                   D801 BAT54S        R802 100k   R803 100k ── GATE_IN1 (U801A out, pin 1)
                   K→+3V3D, A→GND        │                      │
                                        GND                R804 10k → +3V3D
GATE_TH ── U801A − (pin 2)                                       │
                                                         to module GPIO
```

- **Comparator:** U801, U802 = LM393DR2G (C7955, Basic), V+ = **+12 V**, with C801 and
  C802 100 nF 50 V.
- **Threshold:** GATE_TH = R817 10k / R818 10k from +3V3D, with C803 100 nF. That gives 1.65 V,
  shared by all four − inputs.
- **Trip points at the jack [calc]:** **1.980 V rising, 1.665 V falling**, so 0.315 V of
  hysteresis. The output is non-inverting: GATE_INn is high while the gate is high. The top
  clamp begins conducting above about 3.9 V at the jack.
- **Jack detect:** PROBE → R819 1k → PROBE_BUS, which has a D805 BAT54S clamp. From the bus,
  R820–R829 (100k) go to the CV and audio inputs, and **R830–R833 (22k) go to the gate-input
  normal lugs** (PR11–14).

### 1.2 Gate outputs ×8 (sheet 6)

- **Driver:** U602 = 74HCT595D,118 (C282339, Extended), VCC = +5VD (5.07 V), with C613 100 nF.
- **Pins:**
  - SER (14) is SPIB_MOSI, SRCLK (11) is SPIB_SCK and RCLK (12) is CS_595.
  - SRCLR (10) is tied to +5VD.
  - **OE (13) is GATE_OE_N**: R618 10k to +3V3D, driven by TCA9555 U701 P06 (pin 10).
- **Each output:** GQn → R619–R626 1k → GOUTn (jack). D601–D608 BAV99,215 (C2500, Basic)
  clamp the jack node to +5VD and GND.
- **J603 holes:** QH′ (GATE_SER_OUT), SPIB_SCK, CS_595, +5VD and GND, to chain a second
  595 off-board. **GATE_OE_N is not on J603.**
- **CS_595 has no pull-up.** CS_ADC, CS_DAC and CS_POT all have 10k to +3V3D
  (spec §15: "every module leaves its pins floating while it boots").

Pinouts and diode orientations check out against the datasheets: LM393 1/2/3 and 5/6/7;
74HCT595 per the Nexperia pin table; BAT54S and BAV99 with pin 1 anode to GND, pin 2
cathode to the rail and pin 3 common.

---

## 2. Reference designs, with evidence

### 2.1 Keeos Ogham (merged v1.0): the design our input "copies"

Read from the **PCB**, `ogham/hardware/ogham-merged-v1.0/ogham-merged-v1.0.kicad_pcb`, by
parsing footprint pad nets. The `.net` file in the same folder is **stale**: it gives
R_clk_in1 as 1k, while the PCB and `production/bom.csv` line 22 both say 10k.

**Clock input:**
- CLK_RAW → R_clk_in1 10k → node with D4/D5 BAT54WS (C22629) to +3V3/GND → **U6 LM393
  pin 2, the − input**.
- The + input is R_div1 10k from +3V3 and R_div2 10k to GND, with **R_hys1 100k from the
  output to the + input**.
- The output, CLK_IN, has R_clk_pu1 10k to +3V3 and goes to Daisy pin 7.
- **The LM393 V+ is +5 V.** There is **no 100k pull-down** on the signal node. The same
  jack also feeds a V/oct divider (R_voct1 10k, R_voct2 18k, BAT54WS clamps), so it is
  loaded with about 28k.
- The circuit is **inverting**, with the hysteresis on the reference node. **Trips at
  1.72 V rising and 1.57 V falling [calc].**

**Gate input:** R_gate_in1 100k → Q1 MMBT3904 base. R_gate_div1 33k + D3 1N4148 go to GND.
The collector goes to the Daisy pin.

**Gate output:** GATE_OUT (Daisy) → U5 **74AHCT1G125** (C7484) at +5 V, with OE (pin 1) tied
to GND, so it is always enabled → **R_gout1 1k** → jack, with **D6/D7 1N5819WS Schottky to
+5 V and GND at the jack node**. This is the same arrangement as ours.

### 2.2 Electrosmith Daisy Patch SM (ES_Daisy_Patch_SM_Rev3, 2024-02-08), sheet 4

Source: Electrosmith `ES_Daisy_Patch_SM_Schematic.pdf` (docs.daisy.audio), gate-in and
gate-out sections. Also the datasheet
`ES_Patch_SM_datasheet_v1.0.5.pdf` (Fig. 1.4 and 1.10; Table 1).

- **Gate in:** INPUT_GATE_1 → R74 100k → Q1 MMBT3904 base, with R75 1M base to GND. The
  collector has R76 10k to +3V3_D and goes through R77 1k to GATE_IN_1 (MCU).
  - Inverting; no clamp.
  - Threshold about 0.7–1.0 V **[calc]**.
  - The datasheet says the input impedance is 100k.
  - Table 1 gives the gate input range as "Negative Power In" to "Positive Power In"
    (±12 V).
- **Gate out:** GATEOUT1 (GPIO 0–3.3 V) → U13A **MCP6004 on +5 V**, non-inverting, gain
  1 + R11 62k / R10 120k = 1.52 → **R12 100 Ω** → OUTPUT_GATE1. **0–5 V**, no clamps.

### 2.3 Befaco Lich V1 (Rebel Technology 2020, GPL)

Source: Befaco `docs/Lich_V1_sch.pdf`, gate section.

- **Gate in:** GATE_IN_1_M → R28 100k → Q1 NPN base, with R29 1M base to GND and R25 10k
  collector pull-up to +3V3. Inverting; no clamp.
- **Gate out:** A6_GATE_OUT → R139 1k → Q100 NPN. The collector has R138 1k to **+12 V**
  and goes through R141 100 Ω to the jack.
  - The output is inverted and swings **0–12 V**, with about 1.1k source impedance.
  - The LED (R140 470 Ω) sits between +3V3 and the GPIO line.

### 2.4 Befaco Muxlicer V1.2 (2018, CC BY-NC-SA)

Source: Befaco `muxlicer/hardware/muxlicer_v1_2.pdf`, clock input.

- **Clock in:** CLOCK → R7 1k → D1/D2 Schottky to +5 V and GND, R8 470k to GND →
  ATmega (5 V) pin. The threshold is the ATmega's (VIH ≤ 0.6 × VCC = 3.0 V).
- **Reset in:** R15 100k → Q2 2N3904, with R29 100k from base to GND.
- **Clock, all-gate and EOC outputs:** R14, R23 and R22 (10k) → 2N3904. The collector has
  **1k8 to +12 V** (R12, R25, R28) and goes through 120 Ω (R11, R26, R27) to the jack.
  That is **0–12 V**, about 1.9k source impedance, inverted.

### 2.5 Music Thing Workshop System Computer Rev 1.0.0, sheet 5

Source: Music Thing Workshop Computer `computer_Rev_1_0_0_Schematic.pdf`, pulse
input section.

- **Pulse in:** PULSE_IN_2 → **R16 100k → Q402 MMDT3904 base**. There is no base pull-down
  and no clamp. The collector goes to PULSE_2_INPUT. The schematic note reads: "0v to 12v
  input, above 0.4v = pulse… Uses pullup on pin to drive transistor".
- **Normalisation probe:** R67/R68 100k to the jack normals.
- **Pulse out:** PULSE_2_RAW_OUT → R8 10k → Q201 NPN. The collector has **R14 10k to
  +12 V** and **R15 15k to GND** and goes straight to the jack. The schematic note says
  "6.5v pulses".
  - That is about 7.2 V open-circuit with a 6 kΩ source **[calc]**, inverted, and
    short-proof by its resistors.

### 2.6 Allen Synthesis EuroPi, surface-mount revision

Source: EuroPi `europi-surface-mount.kicad_pcb`, downloaded from GitHub main, with pad
nets parsed.

- **Digital in:** J8 tip → **R35 100k → Q1 (2N2222) base**, with **D3 from base (K) to
  GND (A)** as a reverse clamp. **R40 10k** pulls DIGITAL_IN (Pico GP22) up to +3.3 V.
- **Jack detect:** R42 10k from DIN_DETECT to the jack's normal lug.
- **No gate outputs:** EuroPi's six CV outputs are used as gates.

### 2.7 Mutable Instruments Marbles v70 (Émilie Gillet, CC BY-SA)

Source: `marbles_v70.pdf` (pichenettes documentation site), sheet 3 (inputs) and
sheet 4 (outputs). Crops: `marbles_clk-3.png`, `marbles_gout2-4.png`.

- **Clock in (T and X):** J3 → **R26 100k** → Q2 MMBT3904 base, with **R24 100k** base to
  GND and a **D4 1N4148** reverse clamp on the base. The collector has R22 10k to +3V3 and
  goes to T_CLOCK.
  - Threshold about 1.3–1.6 V **[calc]**.
  - **Normalisation probe:** R76/R77 100k from NORMALIZATION_PROBE, which has a **D3 BAT54S
    clamp** to +3V3/GND. This is the same idea as our probe bus.
- **Gate out (T1–T3):** GATE_T_1 (GPIO) → R56 10k → **LM324** non-inverting, gain
  1 + R51 56k / R50 39k = 2.44 → **R85 1.0k** → jack.
  - Labelled "0V to 8V". No clamps; the op-amp drives the jack directly through 1k.

### 2.8 Ornament & Crime rev2e (mxmxmx, 2017)

Source: Ornament & Crime `o_c_rev2e_schematic.pdf`, trigger
input section.

- **TR1–TR4:** jack → **100k** → MMBT3904 base, with **33k from base to GND** and the
  emitter to GND. The collector goes to the Teensy pin, using its internal pull-up. No clamp.
- **Threshold about 2.6 V [calc]:** 0.65 V × (1 + 100/33).
- The 33k divider limits reverse base-emitter voltage to under 6 V for inputs down to
  about −24 V.

### 2.9 4ms

**Stereo Triggered Sampler v1.2b:** `D_4ms_STS/hardware/STS-v1.2b-schematic.pdf` page 3,
trigger inputs.
- PLAYTRIG1 → **R59 100k → D13 BAT54S to +3.3 V and GND**, with **R64 1M** and **C107
  10 nF** to GND → PLAY1_TRIG, straight into the STM32 GPIO.
- That is a 1 ms RC, with the GPIO acting as the comparator.

**MP153 example carrier v0.4:** `4ms/mp153-devboard/carrier board/v0.4/mp153-carrier-board.pdf`,
gate inputs.
- J9 → **R13 47k → D7 BAT54S to +3V3 and GND**, with **C81 10 nF** → GATE1_IN.
- The sheet is titled "Example Gate Input (~0.6V threshold)". I cannot reconcile 0.6 V with
  a direct GPIO **[unverified]**.

### 2.10 Eurorack convention: Doepfer A-100 technical details

Source: <https://doepfer.de/a100_man/a100t_e.htm>.

- "Within the A-100 usually any voltage beyond about **+3V** is treated as 'high' (e.g.
  +5V, +8V, +10V, +12V will work)… Any voltage **below 1V** is treated as 'low'."
- Gate, trigger and clock signals have "typical voltage levels of **0/+5 V**", and "all
  A-100 modules will withstand gate/trigger/clock signals **up to +12V**".
- "Only rectangle shaped waveforms should be used as Trigger, Gate or Clock sources."

**Make Noise:** I could not find a published input threshold **[unverified]**.

---

## 3. Comparison table

| Design | Gate-in circuit | Threshold at jack | Hysteresis | Negative input | Gate-out circuit | Out level / source R |
|---|---|---|---|---|---|---|
| **Ours** | 10k → BAT54S (3V3D/GND), 100k pull-down → LM393 (+12 V) +in, 100k hysteresis, 10k pull-up; non-inverting | **1.98 ↑ / 1.67 ↓** | 0.32 V | BAT54S, node at −0.33 V max at −12 V | 74HCT595 (5 V) → 1k, BAV99 to +5VD/GND | **0/5 V, 1k** |
| Ogham | 10k → BAT54WS (3V3/GND) → LM393 (+5 V) −in; 10k/10k reference, 100k hysteresis on the reference; inverting | 1.72 ↑ / 1.57 ↓ | 0.15 V | BAT54WS | 74AHCT1G125 (5 V) → 1k, 1N5819WS to +5 V/GND | 0/5 V, 1k |
| Patch SM | 100k → MMBT3904, 1M from base to GND, 10k pull-up, 1k to MCU; inverting | ≈0.7–1.0 V | MCU Schmitt | none (base-emitter breakdown) | MCP6004 (5 V) ×1.52 → 100 Ω | 0/5 V, 100 Ω |
| Befaco Lich | 100k → NPN, 1M from base to GND, 10k pull-up | ≈0.7 V | MCU | none | NPN, 1k to +12 V, 100 Ω; inverted | 0/12 V, 1.1k |
| Befaco Muxlicer | clock: 1k → Schottky (5 V/GND), 470k → ATmega | ≤3.0 V (VIH) | MCU | Schottky | NPN, 1k8 to +12 V, 120 Ω; inverted | 0/12 V, ≈1.9k |
| WSC | 100k → MMDT3904, RP2040 pull-up | >0.4 V (note) | MCU | none | NPN, 10k to +12 V, 15k to GND; inverted | ≈0/7.2 V, 6k |
| EuroPi | 100k → NPN, reverse diode on the base, 10k pull-up | ≈0.8 V (spec §6.5) | MCU | diode on the base | (no gate outs) | — |
| Marbles | 100k → MMBT3904, 100k from base to GND, 1N4148 reverse, 10k pull-up | ≈1.3–1.6 V | MCU | 1N4148 | LM324 ×2.44 → 1.0k | 0/8 V, 1k |
| O&C rev2e | 100k → MMBT3904, 33k from base to GND, Teensy pull-up | ≈2.6 V | MCU | 33k divider | (no gate outs) | — |
| 4ms STS | 100k → BAT54S (3.3 V/GND), 1M + 10 nF → GPIO | ≈2 V **[unverified]** | MCU | BAT54S | — | — |
| Doepfer convention | — | high ≥ ≈3 V, low < 1 V | — | withstands ±12 V | — | typical 0/+5 V |

**What the table says:**
- **Gate in:**
  - Transistor inputs are the norm (six of the nine designs that read gates).
  - Comparator inputs are rarer (Ogham) but give a precise, temperature-stable threshold
    with designed-in hysteresis.
  - Clamped direct-to-GPIO inputs (4ms, Muxlicer) are the third family.
- **Gate out:** 5 V (Patch SM, Ogham, ours) is the low end. Marbles gives 8 V; Lich and
  Muxlicer give 12 V.

---

## 4. The checks

### 4.1 Thresholds and hysteresis

- 1.98 V rising and 1.67 V falling both sit inside Doepfer's "undefined" band of 1–3 V.
  So every Doepfer-convention high (≥3 V) and low (<1 V) is read correctly, whatever the
  module.
- 0.32 V of hysteresis gives clean single edges from slow LFOs, which Doepfer warns
  against but people do anyway.
- The thresholds are set by 1 % resistors and are ratiometric to +3V3D. They do not depend
  on the Pico or Teensy logic thresholds, which is the stated reason for the comparator.
  - On a Patch SM-style transistor input the threshold moves about 2 mV/°C with V_BE.
- **Source impedance moves the rising point [calc]:** 1k source gives 2.01 V; WSC's 6k gives
  2.18 V; 10k gives 2.31 V. The falling point stays at 1.67–1.68 V. All are fine.

### 4.2 Short triggers and speed

- The LM393's large-signal response is **300 ns** (onsemi datasheet, VCC 5 V, TTL step).
- The open-collector rise into the GPIO through R804 10k with 15–30 pF is τ 150–300 ns,
  10–90 % in 0.33–0.66 µs **[calc]**.
- The input RC (10k with BAT54S ≤ 10 pF plus pin capacitance) is about 0.15 µs.
- **Total under 2 µs.** A 1 ms or 100 µs trigger is reproduced with negligible width error.
  - The firmware must catch it: use an edge interrupt or PIO, or poll faster than 10 kHz.
    Audio-rate polling at 48 kHz is fine; a 1 kHz control loop would miss 100 µs triggers.

### 4.3 Input impedance

- With the input low it is 10k + 100k‖100k = **60 kΩ**.
- Above about 3.9 V the clamp conducts. The load is then (V − 3.6 V)/10k: 0.64 mA at
  10 V (≈16 kΩ effective) and 0.84 mA at 12 V **[calc]**.
- That is heavier than the common 100 kΩ, but every source in the table copes:
  - WSC's weak 7.2 V / 6k output still arrives at 5.85 V **[calc]**.
  - A 1k-source 10 V gate feeding four of our inputs through a passive mult still gives
    about 7.4 V.
- Ogham's own clock jack is about 28 kΩ, because of its V/oct divider.

### 4.4 Negative inputs

The onsemi LM393 sheet (LM393/D) says, in Note 10 and the applications text: "The low input
state must not be less than −0.3 V", and "Voltages more negative than −0.3 V should not be
used".

The BAT54S maximum VF (MDD datasheet Rev 2024A2) is 0.24 V at 0.1 mA, 0.32 V at 1 mA and
0.40 V at 10 mA. So:

| Input | Clamp current | LM393 + input (max VF) |
|---|---|---|
| −5 V (bipolar LFO square) | 0.47 mA | −0.294 V — inside the limit |
| −10 V | 0.97 mA | −0.319 V — just past it |
| −12 V | 1.17 mA | −0.325 V — just past it |

- The overshoot is 20–25 mV, and the failure mode is not destructive. TI's LM339-family
  note says a negative input can force the output high while it lasts
  **[unverified: from memory, not re-read for this review]**. onsemi's own Figure 8 uses a
  silicon diode that "prevents input from going negative by more than 0.6 V".
- Ogham ships exactly this, a 10k with a Schottky to GND.
- **Rated C**, with a cheap remedy in C1.

### 4.5 Clamp current into +3V3D → **finding A1**

- Each input above about 3.9 V pushes (V − 3.6)/10k through the BAT54S top diode into
  +3V3D: **0.80 mA at 12 V, so 3.2 mA for four** (3.4 mA at 12.5 V) **[calc]**.
- +3V3D comes from an **XC6206P332MR from +5VD** (`design.py` line 294). The XC6206 is a
  PMOS-pass LDO with a current limiter and no pull-down or discharge path (Torex datasheet
  block description), so **it cannot sink**.
- With the codec in power-down and no display, the load on +3V3D is roughly:

| Load | Current |
|---|---|
| PCM3060 IDD, full power-down (SBAS437) | 0.15 mA |
| ADS8688 DVDD (0.5 mA dynamic, SBAS582C; static not stated **[unverified]**) | ≤ 0.5 mA |
| GATE_TH divider | 0.165 mA |
| TCA9555, EEPROM | µA |
| **Total** | **≈ 0.3–0.8 mA** |

- **So a single 12 V gate can already exceed the minimum load**, and four certainly do.
  - The rail then rises until something conducts the excess.
  - On a **Pico 2** the digital pins are fault-tolerant ("tolerate voltages up to 5.5 V,
    provided IOVDD is powered", RP2350 datasheet). They will not clamp the rail, so the
    excess goes into whatever on +3V3D breaks down first.
  - The PCM3060 VDD absolute maximum is **4.0 V** (SBAS437). On a **Teensy 4.1** (not
    5 V-tolerant) the GATE_IN lines, pulled up to +3V3D, would sit above the MCU's own
    3.3 V.
  - Treating the loads as a resistor, four 12 V gates would drive the rail far past 4 V
    **[calc; an upper-bound illustration, not a prediction]**.
- **Realistic trigger:** a Pico build that doesn't run the codec (most of David's builds
  don't use audio), patched with 10–12 V gates. Lich, Muxlicer and many Doepfer gate
  outputs reach about 12 V.
- Ogham doesn't hit this, because its clamp goes to the Daisy Seed's 3V3, which carries a
  module-sized load.

### 4.6 LM393 supply, common mode and output

- **Common mode at +12 V:** 0 to VCC − 1.5 V (10.5 V), or VCC − 2.0 V over temperature.
  The clamped input (≤ 3.6 V) and GATE_TH (1.65 V) are both well inside.
- **Absolute maximum input = VCC** for VCC < 36 V (onsemi Note 1). That is 12 V here;
  we are at ≤ 3.6 V.
  - At +5 V (Ogham), the 3.6 V input is outside the CM range. Note 10 says the output is
    still correct as long as the other input is in range, so +12 V is cleaner rather than
    strictly required.
- **The open-collector output** can be pulled to any voltage up to 36 V regardless of VCC
  (VO 36 V). VOL is 150 mV typ / 400 mV max at ≤ 4 mA, and we sink 0.33 mA. That is below
  the RP2350 VIL (0.8 V) and the i.MX RT 0.3 × 3.3 V.
  - There is no issue with VCC = 12 V and a 3.3 V pull-up.
- **Supply current** is 0.4 mA typ / 1 mA max per package (2.5 mA at 30 V).
- **The operating range is 0–70 °C.** LM2903 is the −40 °C option, not needed.
- **onsemi recommends "input resistors < 10 k"** to avoid oscillation, plus positive
  feedback. We have 10k and 0.26 V of hysteresis at the pin.

### 4.7 Is the LM393 the right part?

- **Transistor input** (Patch SM, Lich, WSC, EuroPi, Marbles, O&C): fewer parts, proven,
  and no current into any 3.3 V rail, since the base-emitter junction clamps to GND.
  - But the threshold is low (0.4–1.6 V) or awkward (O&C 2.6 V), temperature-dependent,
    and inverting.
  - It has no hysteresis unless the MCU provides it. The RP2350 Schmitt input does; the
    Teensy's is configurable.
- **Clamped direct-to-GPIO** (4ms STS, MP153, Muxlicer): the simplest.
  - It puts the clamp current into 3.3 V (smaller with 100k).
  - Its threshold depends on the MCU.
  - With an RP2350 A2 it is exposed to erratum **E9**: a floating or high-impedance input
    latches at about 2.2 V unless driven by 8.2 kΩ or less.
- **Our comparator** keeps the resistor-set, MCU-independent threshold and hysteresis the
  spec chose. It is immune to E9, because the LM393 sinks hard and R804 10k pulls up.
- **Recommendation: keep the LM393** and fix A1. A Schmitt buffer (for example 74LVC1G17)
  would add a part and still need the same clamp. It gives nothing the RP2350's own
  Schmitt input doesn't.

### 4.8 Gate-out level

- **Output into a load [calc]:** 5.02 V into 100k, 4.96 V into 47k, 4.58 V into 10k.
- **Thresholds that 5 V must clear:**
  - Doepfer: about 3 V.
  - Muxlicer's ATmega: ≤ 3.0 V.
  - O&C: about 2.6 V.
  - STS: about 2 V **[unverified]**.
  - Our own input: 1.98 V.
  - Marbles: about 1.3–1.6 V.
  - Patch SM and Lich: about 0.7–1 V.
  - WSC: 0.4 V.
  - Make Noise: **[unverified]**.
- **5 V clears every verified threshold by at least 2 V.** It is Doepfer's "typical" level
  and the Patch SM and Ogham level.
- **The one practical difference** is where the gate *level* matters rather than its edge:
  for example Maths Signal In used as a slew envelope, or a VCA or LPG driven straight
  from a gate. There, 5 V gives half the swing of a 10 V gate.

### 4.9 Gate-out fault currents (74HCT595, Nexperia 74HC_HCT595 Rev 12)

Ratings: IO ±35 mA per Qn; ICC and IGND 70 mA; IOK ±20 mA outside −0.5 V to VCC + 0.5 V;
VOH ≥ 3.7 V at −6 mA.

| Fault | Result **[calc]** |
|---|---|
| Output shorted to GND | 4.8 mA each, 38 mA for all eight. Inside the 6 mA test current and the 70 mA ICC limit |
| Patched to +12 V through 1k | BAV99 → +5VD 6.2 mA. 595 pin sinks 5.8 mA when Q is low |
| Patched to +12 V through 100 Ω | BAV99 → +5VD 62 mA (BAV99: 215 mA continuous) |
| Patched to −12 V through 1k | 11.2 mA from GND through the BAV99. 595 pin sources 5.8 mA when Q is high |
| OE high (Hi-Z) with the jack clamped at +5.8 V or −0.75 V | about 0.2 mA through the 595's own clamp diodes (≪ 20 mA) |
| Same, without the BAV99, from a 0 Ω +12 V source | 6.4 mA into IOK, still inside 20 mA |

- **The current into +5VD is absorbed.** The TPS54308 runs forced-continuous and its
  low-side FET sinks current: "The low-side MOSFET can also sink current from load", with
  a sink limit of 2.8 A typ. Unlike +3V3D, **+5VD is a safe clamp rail**.
- **BAV99 (silicon, Basic) versus Ogham's Schottky:** with 1k in series it doesn't matter.
  BAV99 is the right, cheaper choice.

### 4.10 Power-up

- **TCA9555 at power-on:** every port is an input with its 100 kΩ pull-up, and the Output
  Port registers default to 1111 1111 (TI datasheet, pin table and Table 5). With R618
  10k, OE reads high.
  - When firmware later sets P06 as an output it first drives the default 1, so it stays
    disabled until firmware writes a 0.
- **+5VD ramps over the TPS54308's 5 ms soft-start.** About 22 µF on +3V3D needs only
  about 22 mA to follow at 1 V/ms, far below the XC6206 limit. So +3V3D tracks +5VD minus
  a few tens of mV, and OE ≈ VCC throughout: **outputs stay blanked [calc]**.
- **Gap 1: the TCA9555 has no reset pin.** It resets only at power-on.
  - When the module resets (watchdog, Pico BOOTSEL, Teensy loader), GATE_OE_N stays
    enabled.
  - Meanwhile CS_595 (RCLK) floats, because it has no pull-up. A noise edge can then latch
    shift-register garbage onto the jacks. → **B1**.
- **Gap 2: an off-board second 595 on J603** has no access to GATE_OE_N, so it powers up
  enabled with random data. → **B2**.

### 4.11 Jack-detect probe on gate inputs (22 kΩ)

- **Worst case, all four gate inputs unpatched:** the bus sits at 3.07 V and the gate jack
  reaches **2.25 V against the 1.98 V rising point, a margin of +0.27 V [calc]**. With one
  unpatched, the margin is +0.35 V.
- **With the probe low**, the comparator node falls to 0.61 V and releases.
- Adequate. See C3 for more margin.
- **Prior art:** Marbles uses the same probe with a BAT54S on the probe line, but its
  transistor inputs trip at about 1.3 V, so a 100k probe suffices there. That is why ours
  needs 22k.

---

## 5. Findings

### (A) Errors or risks: must fix

**A1. The gate-input clamps can drive +3V3D above its rating.**

- **What to change:** add a **680 Ω 0603 bleeder from +3V3D to GND**, next to the +3V3D
  XC6206 output. Use **C23228, Basic**.
  - It draws 4.85 mA. That is more than the worst-case injection of 3.4 mA from four
    12.5 V gates, with or without the codec running.
  - Put a schematic note on it: "minimum load for gate-input clamps: XC6206 cannot sink".
- **Why (evidence):** §4.5.
  - Injection is 0.80 mA per 12 V input.
  - The minimum +3V3D load is about 0.3–0.8 mA: PCM3060 power-down 0.15 mA per SBAS437;
    ADS8688 DVDD ≤ 0.5 mA per SBAS582C; the divider 0.165 mA.
  - The XC6206 has no sink path.
  - The PCM3060 VDD absolute maximum is 4.0 V.
  - RP2350 fault-tolerant pins don't clamp; Teensy 4.1 pins are not 5 V-tolerant.
- **Cost:** about $0.002, Basic, no fee.
  - 16 mW in the resistor (rated 100 mW).
  - Plus 8.6 mW in the XC6206, i.e. (5.07 − 3.3) × 4.85 mA.
  - +3V3D load rises from ≈50 to ≈55 mA, against a 200 mA rating.
- **Alternatives:**
  - A 1 kΩ (C21190, already in the BOM) gives 3.3 mA, with only 0.25 mA margin at
    12.5 V.
  - Or replace R817/R818 10k with 470 Ω each (3.5 mA), so the GATE_TH divider is the
    bleeder. That works but mixes two jobs, which is worse for the tutorial.
  - C1 below reduces the injection itself.
- **Side effects:** none functional. GATE_TH and the thresholds are unchanged.
- **Cross-block note [unverified, outside this block]:** the audio-input BAT54S clamps go
  to +5VA from the L78M05, which also cannot sink. The TL074H behind 1k can push about
  6.7 mA per channel into them. Worth the same minimum-load check in the audio review.

### (B) Worth adopting

**B1. Add a 10 kΩ pull-up on CS_595 (RCLK) to +3V3D,** plus a firmware boot rule.

- **Why:** spec §15 already gives CS_ADC, CS_DAC and CS_POT 10k pull-ups because modules
  float their pins while they boot. CS_595 was missed.
  - Because the TCA9555 has no reset pin (§4.10), the 595 outputs stay *enabled* across a
    module reset or reflash. A floating RCLK can then latch garbage onto the gate jacks.
  - With the pull-up, RCLK sits high: Pico 2 pad pull-down (≈50k) against 10k gives about
    2.7 V, above VIH 2.0 V. No edge means the outputs simply hold their last state.
- **Firmware rule:** at boot, first write TCA9555 P06 = 1 (OE off), then clock zeros into
  the 595 and pulse RCLK, then enable.
- **Cost:** 1 × 10k 0603, **C25804, Basic, already used**. No fee.

**B2. Put GATE_OE_N on J603, and label J603 "74HCT595 only".**

- **Why:** an off-board chained 595 otherwise powers up enabled with a random register.
  - A plain 74HC595 at 5 V needs VIH ≥ 3.15 V at VCC 4.5 V, and 0.7 × VCC = 3.55 V at
    5.07 V (Nexperia table). So the 3.3 V SCK and RCLK on J603 are out of spec for HC.
    QH′ is 5 V, so it is fine either way.
- **Cost:** one more hole on the J603 strip. No parts.

**B3. Correct the "copies Ogham's clock input" wording** in spec §6.5, §7, the sheet-8 note
and the tutorial.

- **Why:** Ogham's fabricated PCB (§2.1) is inverting. Its signal goes to the **− input**,
  its hysteresis is on the reference divider, its LM393 runs at **+5 V**, it has no 100k
  pull-down, and it trips at 1.72 V and 1.57 V.
- Ours is a non-inverting adaptation. Say so, and say why it is better for four channels:
  - Per-channel hysteresis on the signal node leaves the shared GATE_TH unloaded.
  - Copying Ogham four times on one shared reference would couple the channels through it.
- Also note that the Ogham `.net` file is stale: it shows R_clk_in1 = 1k against 10k on the
  PCB and BOM.
- **Cost:** documentation only.

**B4. Write the firmware facts down for the tutorial.**

- GATE_INn is **active-high**. libDaisy's Patch SM transistor inputs are inverted, so code
  ported from those builds must drop its inversion.
- Unpatched gate inputs **follow PROBE**, so mask them during probing.
- Triggers of 100 µs need edge interrupts or PIO (§4.2).
- To enable the gate outputs: write the P06 output bit to 0 *then* set the P06 config bit
  to 0.
- **Cost:** none.

### (C) Optional

**C1. Scale the gate-input network ×3.3.**

- **Change:** R801, R805, R809, R813 to **33k** (C4216, Basic); pull-downs R802… and
  hysteresis R803… to **330k** (C23137, Basic).
- **Unchanged:** the thresholds (1.98 V and 1.67 V), because all ratios are kept.
- **Gains [calc]:**

| | Now (10k) | With 33k |
|---|---|---|
| Clamp current per 12 V input | 0.80 mA | 0.25 mA |
| LM393 input at −12 V | −0.325 V | −0.284 V (inside −0.3 V) |
| Input impedance, input low | 60k | ≈200k |
| Rail with four 12 V gates, no bleeder | far past 4 V | still ≈3.8 V |

- The 22k probe still works, with more margin, because the input impedance rises.
- **Costs:**
  - LM393 bias current gives at most 250 nA × 165k = 41 mV of shift.
  - BAT54S reverse leakage acts on 3.3× the impedance. It grows steeply with temperature.
  - It moves away from onsemi's "< 10 k" advice. The hysteresis still guards against
    oscillation.
- **It does not replace A1:** the rail still reaches about 3.8 V without a bleeder.
- Two new Basic values. No fee.

**C2. Gate-out level:** keep 0/5 V for Rev A.

- **To match Marbles (8 V) or reach 10 V:** two TL074H as ×2 non-inverting buffers after
  the 595, then 1k out. TL074HIDR C2878713 is Extended but already a board part type, so
  no new fee; +$0.51 and 16 Basic resistors.
- **Do not use a WSC- or Lich-style NPN stage behind the 595.** It inverts, and with OE
  high the bases float. All eight gates would sit **high** during the very blanking period
  OE exists for.

**C3. Jack-detect margin:** 22k → 15k (Basic) on R830–R833 lifts the worst-case margin from
+0.27 V to about +0.4 V **[calc]**. Only worth it if probing proves flaky.

**C4. Off-board signal integrity:** a 33–100 Ω series resistor in the SPIB_SCK feed to J603.

- QH′ and SCK toggle during every MCP3208 pot read, so a cable on J603 radiates at the SPI
  rate. Keep the J603 cable short.

**C5. LM2903** (−40 to +105 °C, same pinout) only if the board ever leaves a warm studio.
Not needed.

### Where the design is already right, and why

1. **A comparator with a resistor-set threshold and hysteresis.**
   - 1.98 V and 1.67 V sit inside Doepfer's undefined band, so every conventional high and
     low is read correctly.
   - It is MCU-independent and immune to RP2350-E9.
   - It is the most precise input of all the designs reviewed.
2. **Hysteresis on each signal node, not on the shared reference.** Four channels share one
   unloaded GATE_TH without crosstalk (§4.1, B3).
3. **LM393 on +12 V.** The common-mode range covers the 3.6 V clamp, the input stays
   ≤ VCC, and the open-collector output to a 3.3 V pull-up is within ratings (§4.6).
   Basic part.
4. **10k series with a Schottky to GND.** The same as Ogham. ±5 V LFO squares stay inside
   the LM393's −0.3 V limit (§4.4).
5. **0/5 V gate out through 1k with clamps at the jack.** The same as Ogham's proven output
   and Patch SM's level; Doepfer's typical level. Every fault current is within 74HCT595
   ratings. The +5VD clamp rail can sink (§4.8, §4.9).
6. **The 74HCT595 at 5 V driven from 3.3 V logic.** VIH 2.0 V. Its ΔICC, up to 675 µA per
   3.3 V input, is negligible.
7. **Power-up blanking.** OE pull-up, TCA9555 power-on state and soft-start tracking keep
   the gates off at power-on (§4.10).
8. **SRCLR tied high.** The register is never cleared behind the firmware's back. Shared
   SPIB traffic only fills the shift register; the latch updates only on RCLK.
9. **The 22k probe resistor on the gate inputs** is a correct consequence of the 1.98 V
   threshold (§4.11).

---

## 6. Sources

**Reference schematics**

| Design | Source |
|---|---|
| Keeos Ogham, merged v1.0 | local checkout `/Users/dbaghurst/GitHub/ogham/hardware/ogham-merged-v1.0/ogham-merged-v1.0.kicad_pcb` and `production/bom.csv`. Public URL not checked **[unverified]** |
| Electrosmith Daisy Patch SM Rev3 | schematic (2024-02-08) and datasheet v1.0.5, from https://docs.daisy.audio/hardware |
| Befaco Lich V1 | <https://befaco.org/docs/Lich/Lich_V1_sch.pdf> |
| Befaco Muxlicer V1.2 | `muxlicer_v1_2.pdf`, from Befaco's muxlicer repository (earlier survey download; URL not re-checked) |
| Music Thing Workshop System Computer Rev 1.0.0 | <https://github.com/TomWhitwell/Workshop_Computer> (`computer_Rev_1_0_0_Schematic.pdf`) |
| Allen Synthesis EuroPi | <https://raw.githubusercontent.com/Allen-Synthesis/EuroPi/main/hardware/surface-mount/europi-surface-mount.kicad_pcb> |
| Mutable Instruments Marbles v70 | <https://pichenettes.github.io/mutable-instruments-documentation/modules/marbles/downloads/marbles_v70.pdf> |
| Ornament & Crime rev2e | <https://github.com/mxmxmx/O_C> (`o_c_rev2e_schematic.pdf`; path within the repo not re-checked) |
| 4ms STS v1.2b | <https://github.com/4ms/STS> (`hardware/STS-v1.2b-schematic.pdf`) |
| 4ms MP153 carrier v0.4 | <https://github.com/4ms/mp153-devboard> (`carrier board/v0.4/mp153-carrier-board.pdf`) |
| Doepfer A-100 technical details | <https://doepfer.de/a100_man/a100t_e.htm> |

**Datasheets**

- **onsemi LM393/D:** max ratings, Notes 1, 8 and 10, applications text.
  <https://www.lcsc.com/datasheet/lcsc_datasheet_1809171611_onsemi-LM393DR2G_C7955.pdf>
- **Nexperia 74HC_HCT595 Rev 12 (2024):** Tables 4 and 7.
  <https://www.lcsc.com/datasheet/lcsc_datasheet_2407241027_Nexperia-74HCT595D-118_C282339.pdf>
- **MDD BAT54S Rev 2024A2:**
  <https://www.lcsc.com/datasheet/lcsc_datasheet_2407101108_MDD-Microdiode-Semiconductor-BAT54S_C408389.pdf>
- **Nexperia BAV99,215:**
  <https://www.lcsc.com/datasheet/lcsc_datasheet_2407250951_Nexperia-BAV99-215_C2500.pdf>
- **TI TCA9555** (2009–2019): pin table, §9.3.1, §9.4.1, Tables 4–6.
- **Torex XC6206:** <https://www.lcsc.com/datasheet/lcsc_datasheet_2304140030_Torex-Semicon-XC6206P332MR-G_C5446.pdf>
- **TI TPS54308:** §6.3.2 FCCM, low-side sink limit, 5 ms soft-start.
- **TI PCM3060 SBAS437:** absolute maximum VDD 4.0 V, IDD.
- **TI ADS8688 SBAS582C:** IDVDD_DYN.
- **Raspberry Pi RP2350 datasheet:** fault-tolerant pins, VPIN_FT, erratum E9.

**JLC parts (verified 2026-10-15 with the JLCPCB parts API)**

| Part | LCSC | Class | Stock | Price |
|---|---|---|---|---|
| LM393DR2G | C7955 | Basic | 212,437 | $0.066 |
| BAT54S (MDD) | C408389 | Extended (already a board type) | 816,706 | — |
| BAV99,215 | C2500 | Basic | — | — |
| 74HCT595D,118 | C282339 | Extended | 14,359 | $0.27 |
| 680 Ω 0603 | C23228 | Basic | — | — |
| 1 kΩ 0603 | C21190 | Basic | — | — |
| 10 kΩ 0603 | C25804 | Basic | — | — |
| 33 kΩ 0603 | C4216 | Basic | — | — |
| 330 kΩ 0603 | C23137 | Basic | — | — |
| MMBT3904 | C20526 | Basic | — | — |
| TL074HIDR | C2878713 | Extended | — | — |

No BAT54S variant on JLC is Basic.

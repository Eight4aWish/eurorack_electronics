# CV inputs (ADS8688): design review against published designs

Analogue board Rev A, checkpoint 1 schematic (`hardware/analogue_board/analogue_board_schematic.pdf`,
sheet 4 "CV jacks & ADC" and sheet 8 "Gate ins & jack detect"), generator
`tools/analogue_board/design_analog.py` (`sheet_cv_in`) and `design_digital.py` (`sheet_gate_in`), spec
`docs/analogue_board_spec.md` v0.3 (§3, §6, §7, §15). Reviewed 2026-10-15.

**Verdict in one line:** driving the ADS8688 straight from the jack through 1 kΩ is sound and is more
accurate than any reference design, but fix two things before ordering: the "unpatched reads 0 V" claim
is false (it reads +0.20 V), and the 0402 switch-path 1 kΩ resistors overheat if an output is patched
into a bidirectional jack that is also driving. Also worth adopting: a 15 V TVS at each jack (Beads,
esper, TI's EVM footprint), 1 nF at each ADC pin (TI's EVM), and a 10 kΩ bleed on +5VA so the ±20 V
protection also applies unpowered.

Numbers marked *(calc)* come from a short calculation script (not kept), which models the ADS8688
input as TI specifies it (SBAS582C §7.5): 1 MΩ (0.85–1.15 MΩ) to an internal bias of 2.25 V on the
±10.24 V range and 2.00 V on the ±5.12 V range.

---

## 1. Our design, exactly

**Converter, U401 ADS8688IDBTR** (LCSC C527390, Extended), sheet 4:

| Pin | Net | Parts |
|---|---|---|
| AVDD 9, 30 | +5VA (L78M05 from +12 V) | C401, C402 1 µF 0603 at each pin; C403 10 µF 0805 bulk |
| DVDD 34 | +3V3D | C404 10 µF 0805, C405 100 nF 0402 |
| REFSEL 4, DAISY 3 | GND | internal 4.096 V reference, no daisy chain |
| REFIO 5 | REFIO | C408 10 µF 0805 25 V X5R (C15850) |
| REFCAP 7 | REFCAP | C406 1 µF 0603 + C407 22 µF 1206 25 V X5R (C12891) |
| REFGND 6, AGND 8/28/29/31/32, DGND 33 | GND | one plane (spec §9) |
| AUX_IN 10, AUX_GND 11 | GND | AUX unused |
| RST/PD 2 | ADC_RST | R401 10 kΩ to +3V3D |
| CS 38 | CS_ADC | R402 10 kΩ to +3V3D |
| AIN_nGND 13/15/17/19/20/22/24/26 | GND | direct to the plane |

The ADC channel pins match SBAS582C's pin diagram: ADC_IN1–6 on AIN_0P–AIN_5P (16, 18, 21, 23, 25, 27),
ADC_IN7/8 on AIN_6P/AIN_7P (12, 14). The datasheet's pin *table* swaps "positive/negative" in the
descriptions of pins 20–27, but its names and drawing agree with the schematic.

**Each channel** (CV1 shown; designators from sheet 4):

```
            R405 1k          R403 1k
CVDRV1 ─ U402A DG412 ─┬─/\/\─┬─ CV1 hole ─┬─/\/\─┬─ ADC_IN1 (AIN_0P, pin 16)
  (TL074H, ±5 V)      │      │  (J401.1)  │      └─ R404 100k ─ GND
  IN ← SW_EN1, R406   │      │            │         AIN_0GND (pin 17) ─ GND
  4.7k pull-down      │      └── wire to the panel jack tip
                      │          jack normal lug → PRn hole (optional, sheet 8)
```

| Channel | Switch | Switch-side 1k | ADC-side 1k | 100k |
|---|---|---|---|---|
| CV1 | U402A (2 jack, 3 drive, 1 IN) | R405 | R403 | R404 |
| CV2 | U402D (15, 14, 16) | R409 | R407 | R408 |
| CV3 | U402C (10, 11, 9) | R413 | R411 | R412 |
| CV4 | U402B (6, 7, 8) | R417 | R415 | R416 |
| CV5 | U403A (2, 3, 1) | R421 | R419 | R420 |
| CV6 | U403D (15, 14, 16) | R425 | R423 | R424 |
| CVI7 | none | — | R427 | R428 |
| CVI8 | none | — | R429 | R430 |

All resistors are 0402 1 % thick film: 1 kΩ C11702, 100 kΩ C25741 (both Basic; the generator's default
size is 0402, `blocks.py` line 68). There is no capacitor on any CV input. The DG412s (C2651920,
Extended) run from ±12 V with VL = +5VD, each supply with 100 nF (C409–C414). U403's spare sections 2 and
3 are grounded and off.

**Jack-detect probe** (sheet 8): PROBE GPIO → R819 1 kΩ → PROBE_BUS, with D805 BAT54S to +3V3D and GND →
R820–R829 100 kΩ to PR1–PR10 (audio and CV inputs) and R830–R833 22 kΩ to PR11–PR14 (gate inputs) → J802
holes, each wired by hand to an input jack's normal lug.

**Firmware intent** (spec §6.1, §7): each channel set to ±10.24 V or ±5.12 V; the converter bus scans 8
ADC + 8 DAC channels at about 31 kHz each; with a switch on, the ADC reads the jack while the DAC drives
it, which closes the calibration loop.

## 2. What the block does, in numbers

| Quantity | Value | Basis |
|---|---|---|
| Jack → ADC pin gain | 0.98912 (−1.088 %), offset +2.2 mV | *(calc)*; 1k, 100k ‖ 1 MΩ to 2.25 V |
| Gain spread from the ADS8688's 1 MΩ tolerance (0.85–1.15 MΩ) | ±0.015 % | *(calc)* |
| Full scale at the jack | ±10.35 V (±10.24 V range); ±5.18 V (±5.12 V range) | *(calc)* |
| Input impedance seen by a source | 1k + 100k ‖ 1M = 91.9 kΩ | *(calc)* |
| Loading error, 1 kΩ source | 12.9 cents per octave (100 kΩ op-amp input: 11.9) | *(calc)* |
| Loading error, 100 Ω source | 1.3 cents per octave | *(calc)* |
| **Unpatched, no probe wired** | **+204 mV** (±10.24 V range), **+182 mV** (±5.12 V range) | SBAS582C §7.5 leakage (VIN − 2.25)/RIN |
| Unpatched, probe wired, probe low / high | +0.11 V / +1.56 to +1.66 V at the pin | *(calc)*; bus 3.07–3.30 V depending on load |
| Thermal noise of 1k ‖ 100k over 15 kHz | ≈ 0.5 µV rms, against ≈ 180 µV rms ADC noise (92 dB SNR on ±10.24 V) | *(calc)*; SBAS582C §7.5 |
| Ratio drift, 1k vs 100k (both ±100 ppm/°C) | ≤ 2.2 ppm/°C of reading | *(calc)* |

## 3. Reference designs, with evidence

Each was read from its published schematic. Designators and values are as printed.

### 3.1 Electrosmith Daisy Patch SM (Rev 3) — the platform behind four of David's modules

`ES_Daisy_Patch_SM_Schematic.pdf` (EAGLE, "ES_Daisy_Patch_SM_Rev3-REDUCED", 2024-02-08), sheet 4/4, read
at 220 dpi.
- CV_IN_1 → R107 100k → U7C MCP6004 inverting input; R106 200k from −10V_REF; feedback R105 33k ‖ C84
  220 pF; + input to GND; output straight to ADC_CTRL_1. CV2–8 identical (R53/R27/R25/C35, R56/R55/R54/C59,
  …, R69/R68/R70/C87).
- MCP6004 on +3V3_A (C61, C89 100 nF). −10V_REF: U1 LM4040-10V fed from −12 V through R99 2k, C65 100 nF.
- Transfer: Vout = 1.65 − 0.33·Vin, so ±5 V → 3.3–0 V; Zin 100 kΩ; pole 21.9 kHz.
- Protection: none beyond the 100k and the op-amp's 3.3 V rails. No clamp, no TVS, no cap at the ADC pin.

### 3.2 Electrosmith Daisy Patch Rev 8

`ES_Daisy_Patch_Rev8.pdf` (2025-03-13), sheet 2/4 "ADC Inputs": J_CV_1 → R107 100k into U7C MCP6004
(+3V3_A), summed with KNOB_1 via R108 66k5 and −10V_REF via R106 200k; feedback R105 66k5 ‖ C54 10 nF
(239 Hz pole). −10V_REF from U6 LM4040-10V, R18 2k, C13 100 nF. No clamps.

### 3.3 Befaco Lich v1 (Rebel Technology / Befaco, GPL)

`Lich_V1_sch.pdf` (befaco.org/docs/Lich, 2020), single sheet, read at 300 dpi; BOM `Lich_V1_BOM.ods`.
- CV_D jack → panel pot (R1212NPAD_MINIS) → R129 100k into IC101B TL072 (±12 V) inverting; offset pot from
  CV_REF via R121 100k; feedback R122 33k ‖ C112 100 pF (48 kHz); + input to GND.
- Op-amp output → R128 1k → **D105/D107 "DIODO_ANCHO" to +3V3 and GND** → R133 100 Ω → A21_ADC4. The BOM
  lists D100–D107 as **BAT48/BAT85 Schottky**. CV_REF from an LM4040DIZ-10.0 fed through 2k2 from −12 V.
- Because the op-amp runs on ±12 V, Befaco clamps after it: 1 kΩ + Schottky pair + 100 Ω.

### 3.4 4ms mp153-devboard, example carrier v0.4

`4ms/mp153-devboard` @ 8ab17e3, `carrier board/v0.4/mp153-carrier-board.pdf`, "Example CV Jack (0–5V)".
- J5 → R5 47k → node with **R8 100k to GND, D1 BAT54S to +3V3 and GND, C98 10 nF to GNDADC** → U1B TL072H
  follower (±12 V) → R2 68 Ω → CV_JACK1_ADC. Note on the sheet: "Do not attach VREF+ or GNDADC to clamping
  diode."
- Transfer 0.68 (0–5 V → 0–3.4 V); Zin 147 kΩ; pole 47k ‖ 100k × 10 nF = 497 Hz.
- The nearest in spirit to ours: a passive divider straight into a high-impedance input. 4ms adds the
  clamp and a large series resistor because its MCU ADC tolerates only 0–3.3 V.

### 3.5 Keeos Ogham (merged v1.0)

`/Users/dbaghurst/GitHub/ogham/hardware/ogham-merged-v1.0/ogham-merged-v1.0.net`, traced with
`scripts/kinet.py`. CV_A_RAW (J_cva1 tip) → R3 470k → U3A MCP6004 (+3V3) inverting; R4 200k from
VREF_NEG5V (U1 LM4040-5.0, R1 10k from −12 V); feedback R_fb_a1 100k ‖ C_fb_a1 1 nF (1.6 kHz); output to
Seed pin 26. Zin 470 kΩ. No clamps.

### 3.6 Music Thing Modular Workshop System Computer, Rev 1.0.0

`TomWhitwell/Workshop_Computer` @ 4fdefdd, `documentation/computer_Rev_1_0_0_Schematic.pdf` sheets 1–5;
firmware `ComputerCard.h` v0.4.0.
- CV1: R17 120k → U4B MCP6004 (+3V3, GND) inverting; R34 100k from −5V_REF (VR1 TL431, R52/R53/R54 3.3k,
  −4.99 V); feedback R7 33k ‖ C24 4.7 nF (1.03 kHz). Output → CD4052 mux → RP2040 ADC3, with no series R,
  cap or clamp at the pin. Vout = 1.647 − 0.275·Vin: −6 to +6 V. Zin 120 kΩ.
- Audio inputs are the same stage with 33k ‖ 220 pF, then R62/R61 1k + C37/C36 10 nF at the ADC pins.
- Protection: none beyond the 120k and the 3.3 V op-amp rails.
- **Probe:** GPIO4 (NORMALISATION_PROBE) **directly**, with D10 BAT54S to +3V3/GND and no series resistor,
  then 100k (R63–R68) to each input's normal lug. A new pseudo-random bit every 16 samples at 48 kHz
  (333 µs; L618–623, L840–845, L908); inputs sampled ~290–310 µs after the edge; threshold raw < 1800
  (L850, L856–857); a jack is unpatched only if its last 32 bits exactly match the probe's (L863), then
  forced to 0 (L867–873). Probe swing at an unpatched tip: 0 ↔ 1.80 V. No pull-down at any jack: with the
  probe idle, the GPIO (low) through 100k *is* the pull-down.

### 3.7 Allen Synthesis EuroPi (surface-mount)

`Allen-Synthesis/EuroPi` @ 1192d31, `hardware/surface-mount/europi-surface-mount.kicad_sch`.
- AIN: J5 → R15 100k → U4 TL074 (±12 V) inverting, R18 22k → R23 22k → U5 MCP6002 (3.3 V) inverting,
  R28 22k ‖ C15 1 nF (7.2 kHz) → GP26. 0.22·Vin: 0–12 V; negatives clip at 0 V. Zin 100 kΩ. No clamps:
  the 3.3 V MCP6002 "will always clip".
- Jack detect: J5 normal → R41 10k → GP6 (AIN_DETECT). Not used by the firmware.

### 3.8 Ornament & Crime rev 2e (Teensy 3.2)

`mxmxmx/O_C` @ cfbffab, `hardware/o_c_rev2e_schematic.pdf` (passives carry no designators).
- CV1–4: 100k → U4 MCP6004 (3V3_A) inverting; 75k from AREF −5 V (LM4040-5, 2k from VEE); feedback 33k ‖
  330–560 pF (8.6–14.6 kHz); **100 Ω** to the Teensy ADC pin. Vout = 2.2 − 0.33·Vin: −3.33 to +6.67 V.
  Zin 100 kΩ.
- Jack normal to GND, so an unpatched input reads exactly 0 V. No clamps, no TVS.

### 3.9 Mutable Instruments (pichenettes/eurorack @ f4cfa76)

All Mutable CV inputs use one stage: 100k into an MCP6004 on +3V3_A, an offset resistor from an
LM4040B10 −10 V reference, feedback 33k or 20k ‖ C, output straight to the MCU ADC.
- **Plaits v50** (`plaits_v50.pdf` sheet 3): V/OCT J8 → R38 100k, R29 140k offset, R34 33k ‖ C48 1 nF
  (4.82 kHz), −2.86 to +7.14 V. **Every jack tip has an "ESD" part to GND (C54–C61), with the sheet note
  "Optional ESD protection: 1.0nF capacitor or Ceradiode (eg TDK B72500D160H60…)"**, a 16 V varistor.
  Probe: 10k (R45, R48–R51) from five normal lugs to NORMALIZATION_PROBE, D3 BAT54S on the probe net.
- **Marbles v70** (`marbles_v70.pdf` sheet 3): seven CV inputs, 100k / 200k / 33k ‖ 4.7 nF (1.03 kHz) or
  470 pF (10.3 kHz), ±5 V, the same "ESD" cap at every tip; probe (100k R76/R77) on the clock inputs only.
- **Beads v51** (`beads_v51.sch`, XML, traced): PITCH J5 → R33 100k, R28 200k, R30 33k ‖ C19 1 nF, ±5 V;
  SIZE/POSITION/SHAPE 20k ‖ 2.2 nF, ±8 V. **A "16V TVS" (bidirectional symbol, 0603, no MPN) on every CV
  jack tip to GND, ahead of the 100k** (D4, D5, D7, D9, D11, D14). Probe through 10k (R75, R81–R84) on
  five CV jacks; D3 BAT54S on the probe net.

### 3.10 Designs that drive an ADS8688 (or similar) directly

A GitHub and web search ("ADS8688/ADS8684/AD7606 eurorack/synth/CV/teensy/kicad") found five music
designs. None is a released, known-tested product; none uses our exact network.

| Design | ADC | Jack → ADC | Protection | Filter | AIN_nGND | Notes |
|---|---|---|---|---|---|---|
| **Antonio-Ciociola/esper** @ f198efd, `pcb/esper_v1/Input.kicad_sch` | **ADS8688** U4 | tip → AIN_0P–3P, **no series R** | **D1–D4 SMF16A TVS, tip to GND** | C15–C18 **1 nF** to GND | to GND | normal lug → 10k (R1–R4) → NORM_PROBE GPIO with BAT43 clamps. The README lists "better alternative to external adc for cv inputs" under future plans |
| **bmboucher/fpga-synth** @ 0515082, `pcb/fpga_synth.sch` | ADS8684 U3 | jack → A0P–A2P directly | none | none | to GND | 2020 hobby board |
| **MarkWestbroek/MusicBrain** @ 2fc6541 / 124df19, `musicbrain-adc8`, `musicbrain-jack8` | AD7606 U1 | tip → R1–R8 **1 kΩ** 0805 → Vk | none | none | VxGND to GND | jack normals to GND via JP1; "ERC 0, DRC 0"; build unverified |
| **newdigate/teensy-eurorack** @ 237c0e6, `teensy-eurorack-breakout.sch` | AD7606 U6 | tip → V1–V8 directly | none | none | to the jack sleeve | tip normal to GND |
| **Vienna Audio Model 601** (PJRC forum thread 55905, posts 204285/204394, 2019) | ADS8668 | tip → 100 Ω → header; 0 Ω at the ADC | none | 1 nF to GND at the jack, 10 nF P-to-GND at the ADC | 0 Ω to GND | Paul Stoffregen (post 204404) objected to "nothing but a 100 ohm resistor and wires between the jacks"; another user (204435) noted the inputs "can't float" and suggested a follower plus 100k pull-down |

TI's own boards are the stronger evidence:

| TI source | Signal leg | GND leg | Protection | Filter |
|---|---|---|---|---|
| **ADS8688EVM, SBAU230C** §3.1 Fig 3-1 p.4, BOM pp.17–18 | R03 **1.00 kΩ 0.1 %** | R04 **1.00 kΩ** | D01 **SMBJ14CA** bidirectional TVS footprint (not fitted); R01 49.9k to GND "for input float detection" (not fitted) | C01 **1000 pF C0G** across P and GND ("79.5 kHz low pass") |
| **TechNote SBAA232A** (2017; lists the ADS8688) p.1 | "typical value for this resistance is 10k ohms" | matched resistor "required" | "for maximum protection an external TVS diode is recommended" | gain error 1/(1 + R_IN/R_EXT) |
| **TIDA-010008, TIDUEC1B** pp.17–18 | 2 × 10 Ω, then 10.0 kΩ | same | two TVS1400 in anti-series | 10 nF differential |
| **TIDA-01576, TIDUDP7A** p.12, p.16 | as TIDA-010008 / 0 Ω | 1.6 kΩ | TVS1401 | 10 nF (not fitted on one variant) |

Two more TI statements bear on our design. The **ADS8688A datasheet (SBAS680) §8.3.1** says a floating
AIN_nP gives an output that "corresponds to an internal biasing voltage … must be considered as
invalid". **TIDUDP7A p.12** says "During ADC input open condition, due to the internal PGA structure 2V
DC output is measured." E2E threads 785106 ("EXTERNAL CV INPUTS with ADS8688", a Teensy synth project)
and 398227/604608/869820 (floating level ≈ 2.25 V) were seen only as search excerpts behind a captcha:
**unverified**.

**What this says about us:** our 1 kΩ is exactly TI's EVM value, and our network is the EVM's minus the
1 nF and the (unfitted) TVS. The one ADS8688 Eurorack design found (esper) fits a TVS and 1 nF at every
tip. The community boards with nothing at all (fpga-synth, MusicBrain, teensy-eurorack) are unproven.

### 3.11 TI's own guidance (SBAS582C)

- §8.3.2: "In most applications, the signal sources or sensor outputs can be directly connected to the
  ADC input." For DC accuracy, match the source impedance on AIN_nP with an equal resistor on AIN_nGND,
  which cancels the offset from the input current.
- §8.3.3: the internal OVP is "a secondary protection scheme … TI highly recommends using external
  protection devices against surges, electrostatic discharge (ESD), and electrical fast transient (EFT)".
- §7.1 notes (2), (3) and Tables 1–2: ±20 V when "AVDD = 5 V **or offers a low impedance of < 30 kΩ**";
  ±11 V when "AVDD = floating with an impedance > 30 kΩ". Between the range and ±20 V the output is
  saturated and the device "internally protected (not recommended for extended time)".
- §7.2: analogue input pins ±6000 V HBM (other pins ±2000 V).
- §7.5: Zin 0.85/1/1.15 MΩ, drift 7 (25 max) ppm/°C; input current (VIN − 2.25)/RIN on ±2.5·VREF and
  (VIN − 2.00)/RIN on ±1.25·VREF; bandwidth −3 dB 15 kHz, −0.1 dB 2.5 kHz; gain error ±0.05 % FSR max,
  offset ±0.75 mV max (±10.24 V).
- §9.2.1: "using passive RC filters … in front of the ADC is preferred to reduce the noise"; §9.2.2 (PLC
  module, IEC 61000-4 compliant): TVS and ESD diodes, then RC filters on each input; §11.2 layout shows
  an "Optional RC Filter for Channel AIN_0 to AIN_7".

## 4. Comparison

| Design | Front end | Zin | Range at jack | Filter | Protection at the jack / ADC | Unpatched |
|---|---|---|---|---|---|---|
| **This board** | 1k → ADS8688 (100k to GND) | 92k | ±10.35 or ±5.18 V, 16-bit | ADS8688 internal 15 kHz | ADS8688 OVP ±20 V behind 1k | +0.20 V (probe: 0.11 / 1.6 V) |
| Patch SM | 100k → MCP6004 (3.3 V), −10 V ref | 100k | ±5 V | 21.9 kHz | 100k + 3.3 V rails | 0 V |
| Daisy Patch | same, + knob | 100k | ±5 V | 239 Hz | same | 0 V |
| Befaco Lich | pot → 100k → TL072 (±12 V) | ≥100k | ±5 V | 48 kHz | 1k + BAT48 to 3V3/GND + 100 Ω | 0 V |
| 4ms carrier | 47k/100k divider → TL072H follower | 147k | 0–5 V | 497 Hz | BAT54S to 3V3/GND, 10 nF | 0 V |
| Ogham | 470k → MCP6004 (3.3 V), −5 V ref | 470k | ≈ −3.8 to +11.7 V | 1.6 kHz | 470k + rails | 0 V |
| WSC | 120k → MCP6004 (3.3 V) → CD4052 | 120k | ±6 V | 1.03 kHz | 120k + rails | probe (100k from GPIO) |
| EuroPi | 100k → TL074 → MCP6002 (3.3 V) | 100k | 0–12 V | 7.2 kHz | 100k + rails | 0 V |
| O&C 2e | 100k → MCP6004, −5 V ref → 100 Ω | 100k | −3.3 to +6.7 V | 8.6–14.6 kHz | 100k + rails | 0 V (normal to GND) |
| Plaits | 100k → MCP6004, −10 V ref | 100k | ±5 / ±8 / −3 to +7 V | 4.8–48 kHz | **1 nF or 16 V CeraDiode at the tip** | 0 V or probe (10k) |
| Marbles | same | 100k | ±5 V | 1.03 / 10.3 kHz | **"ESD" cap at the tip** | 0 V |
| Beads | same | 100k | ±5 / ±8 V | 3.6 / 4.8 kHz | **16 V TVS at the tip** | probe (10k) |
| esper (hobby) | tip → ADS8688 directly | 1M | ±10.24 V | 1 nF to GND + internal | **SMF16A TVS at the tip** | probe (10k) |
| **TI ADS8688EVM** | 1k → ADS8688, 1k in the GND leg | 1M | ±10.24 V | **1 nF C0G** across P–GND (79.5 kHz) | SMBJ14CA TVS footprint (not fitted) | float-detect 49.9k (not fitted) |

The pattern: every reference design puts ≥ 47 kΩ, usually 100 kΩ, between the jack and anything
sensitive, and limits the ADC pin by the op-amp's 3.3 V rails or by Schottky clamps. Ours puts 1 kΩ in
front of an ADC whose own front end is rated for ±20 V, exactly as TI's own ADS8688EVM does. That is a
legitimate use of the part (TI §8.3.2), and it removes the op-amps, the reference and the mux. But it
gives up the large series resistor that gives every other design its ESD margin, which is why the jack-tip
TVS (Beads, esper, the EVM's footprint) and the 1 nF (EVM, Plaits, esper) matter more here than there.

## 5. The seven checks

### 5.1 Input impedance seen by the source
91.9 kΩ (1k + 100k ‖ 1M). Eurorack practice is 100 kΩ (Patch SM, Daisy Patch, Lich, EuroPi, O&C, Plaits,
Marbles, Beads); WSC 120k, 4ms 147k, Ogham 470k. Doepfer's technical pages give signal levels (audio
±5 V, LFO ±2.5 V, ADSR 0–8 V, gates withstand +12 V) but no input-impedance figure, so 100 kΩ is
convention, not standard. **92 kΩ is in line.**

### 5.2 Gain error, and what calibration removes
- Fixed part: jack → pin gain 0.98912 and +2.2 mV offset. Both depend only on R403-type 1k, R404-type
  100k and the ADS8688's 1 MΩ, so firmware can correct them from nominal values; the ±15 % spread of the
  1 MΩ moves the gain only ±0.015 %. With the ADS8688's own ±0.05 % FSR gain error and ±1 mV reference,
  the ADC reads the jack to about ±0.1 % without external calibration *(calc + SBAS582C §7.5, §8.3.8.1)*.
  That is what makes the loopback scheme work: the ADC is accurate enough to be the meter that calibrates
  the DAC, which justified dropping the LM4040 (spec §15).
- Source-dependent part: the jack voltage itself droops by R_source/92 kΩ, e.g. 12.9 cents per octave
  for a 1 kΩ-output module. **Calibration cannot remove this**, because it depends on what is patched. It
  is the same physics, and almost the same size, as every 100 kΩ Eurorack input (11.9 cents per octave),
  so V/oct sources already assume it.
- A 1k series resistor is the right choice here. At 10k the ADS8688's ±15 % Rin tolerance would move the
  gain ±0.14 % (every channel would need its own calibration, and CVI7/8 have no loopback), and the ratio
  drift would rise from 2 to 20 ppm/°C *(calc)*.

### 5.3 The ADS8688's internal low-pass
TI gives −3 dB at 15 kHz and −0.1 dB at 2.5 kHz. Two real poles at 23.3 kHz fit both points exactly
*(calc; my fit, not a TI statement)*. At a 31.25 kHz per-channel scan, Nyquist is 15.6 kHz, and content
just above it is barely attenuated before folding back:

| Input | Folds to | Internal filter | + 1k/10 nF at the pin | + 1k/1 nF |
|---|---|---|---|---|
| 16 kHz | 15.3 kHz | 3.4 dB | 6.4 dB | 3.4 dB |
| 20 kHz | 11.3 kHz | 4.8 dB | 8.9 dB | 4.9 dB |
| 25 kHz | 6.3 kHz | 6.7 dB | 12.1 dB | 6.8 dB |
| 60 kHz | 2.5 kHz | 17.6 dB | 29.5 dB | 18.2 dB |

So the "audio-rate CV" in spec §6.1 is flat to ~2.5 kHz and usable to ~10 kHz, but harmonics above
15.6 kHz (an audio-rate saw used for FM, or the 60–100 kHz PWM residue of WSC- or EuroPi-style CV
outputs) alias with little attenuation. For ordinary CV (< 1 kHz) this does not matter, and the
reference designs filter far harder (WSC 1 kHz, Marbles 1–10 kHz, Plaits 4.8 kHz, Patch SM 22 kHz). A
10 nF cap would buy only 3–6 dB and would slow the probe (5.8). Firmware oversampling (scan fewer channels
faster and decimate) is the better tool when audio-rate input matters.

### 5.4 Source impedance and accuracy (datasheet)
The ADS8688's input is a constant 1 MΩ resistor into an internal PGA and filter, "independent of … the
ADC sampling frequency" (§8.3.2). Unlike a bare SAR input, there is no sampling-capacitor kickback, so
the 1 kΩ does not affect settling, crosstalk or linearity. Its effects are only:
- the static divider and input-current offset in 5.2. TI's Fig 29 (SBAS582C p.16) shows gain error
  rising about 0.1 % FS per kΩ of source resistance, which is the 1k against 1 MΩ; our 100k pull-down adds
  the larger, fixed 1 %. TI's AIN_nGND matching (§8.3.2; "required" in SBAA232A; fitted on the EVM) would
  cancel the 2.2 mV offset, which calibration also removes (C1);
- thermal noise of ≈ 0.5 µV rms, negligible against ≈ 180 µV rms ADC noise.

### 5.5 Protection

| Case | What happens | Within rating? |
|---|---|---|
| ±10 V patched | pin ±9.89 V; in range on ±10.24 V | yes |
| ±12 V patched (rail-to-rail source, 12 V gates) | pin ±11.87 V: saturated reading | yes (±20 V), but TI: over-range "not recommended for extended time" |
| 0–10 V into a channel set to ±5.12 V | saturated for as long as the CV is above 5.18 V | same caution |
| ±15 V fault | pin ±14.84 V; DG412 path sinks 2.3 mA into ±12 V (CV1–6) | yes (±20 V; DG412 30 mA) |
| ±20 V fault | pin ±19.98 V; DG412 path 7.3 mA | at the limit |
| CV hole miswired to a ±12 V rail in the wiring field | as ±12 V patched | yes |
| Hot-patching | the plug tip passes the jack's grounded sleeve contact on the way in (usual for 3.5 mm jacks), so transients stay within the source's own ±12 V | yes |
| **Unpowered, CVI7/8, source > 11 V** | pin 10.88 V at 11 V in, 11.87 V at 12 V in | **±11 V exceeded at 12 V** if AVDD floats > 30 kΩ |
| Unpowered, CV1–6 | DG412's internal diodes to the dead ±12 V rails pull the jack down through 1k: 4.7 mA at 10 V, 11.3 mA at 12 V from a 0 Ω source | yes (30 mA); the pin stays below 11 V for any source with ≥ 100 Ω |
| ESD into a tip | peak into the 1k path: 3 A at 4 kV, 6 A at 8 kV (IEC 61000-4-2 contact, 330 Ω) | pin rated 6 kV HBM ≈ 4 A; **no external protection**, against TI's advice |

Notes:
- The unpowered case needs the board unpowered while patched to a powered rack: a two-case setup, or the
  board on the bench patched to the rack, which is likely during development. Within one case all
  modules power down together. Whether +5VA is "floating > 30 kΩ" when unpowered is **unverified**: the
  L78M05 output, the PCM3060 and the XC6206 feeding +3V3A (and the pots on it) all hang on it, and
  probably present far less than 30 kΩ, but no datasheet states it.
- 12 V gates are normal Eurorack (Doepfer: "all A-100 modules will withstand gate/trigger/clock signals up
  to +12V"), so a CV input used as a clock input will sit in the "saturated, protected" region. It is
  safe, as TI's Table 1 says; extended time is the caution.
- Clamps to rails (BAT54S, BAV99) do not fit here: the ADC input is bipolar ±10 V, and clamps to ±12 V add
  nothing the OVP doesn't already do while powered, and back-feed the rails when unpowered.

### 5.6 The DG412 path
- **Off leakage:** IS(off)/ID(off) ±0.25 nA at 25 °C, ±5 nA max (D suffix, −40 to 85 °C) (Vishay 61564
  rev B, p. 3). Into an unpatched jack (91 kΩ) that is 0.45 mV (1.5 LSB); patched (1 kΩ source), 5 µV.
  Negligible.
- **Charge injection:** Q = 5 pC typ (CL = 10 nF). Into an unpatched jack node of 30–100 pF it is a
  50–170 mV spike that decays with τ = 3–9 µs; patched, it is absorbed. Discard one scan (≈ 32 µs)
  after each switch change.
- **Off capacitance:** 9 pF. Feed-through from a DAC stage to a patched input at 10 kHz is about −65 dB.
- **Signals beyond ±12 V:** "VS, VD: (V−) −2 V to (V+) +2 V or 30 mA, whichever occurs first";
  internal diodes clamp. Behind 1 kΩ, ±15 V → 2.3 mA, ±20 V → 7.3 mA. Fine.
- **Output patched into a bidirectional jack that is driving (switch on)**, a common patching mistake:
  the 1k on the switch side carries the fight current. Our stage at −5 V against an external output:

| External output | Current | Power in R405-type 1k (0402, 62.5 mW) |
|---|---|---|
| +10 V via 1 kΩ (WSC, Lich R13, this board's own outputs) | 7.4 mA | 55 mW |
| +12 V via 1 kΩ | 8.4 mA | 70 mW |
| +10 V via 100 Ω (Patch SM outputs, R6/R9/R51/R52 100R) | 13.3 mA | 178 mW |
| +12 V via 0 Ω (TL074H limit ±26 mA not reached) | 16.6 mA | 275 mW |

  The DG412 (≤ 30 mA) and TL074H (ISC ±26 mA) survive all of these. **The 0402 resistor does not**: it is
  at its rating with a 1k source and 3–4× over it against the 100 Ω outputs of David's own Patch SM
  modules. The same applies to R431/R432 (CVO7/8).

### 5.7 The 100 kΩ pull-down
In line with Eurorack's 100 kΩ (5.1). Its real job is to give an unpatched input a defined value, and
here the spec's claim is wrong: TI's input current (VIN − 2.25)/RIN means the 1 MΩ returns to +2.25 V,
so 100k ‖ 1M leaves an unpatched input at **+0.204 V** (±10.24 V range) or **+0.182 V** (±5.12 V range).
On a V/oct input summed in firmware that is +2.4 semitones. Calibration cannot remove it, because it only
appears when nothing is patched.

Raising the pull-down to 1 MΩ (or omitting it) would cut the loading error from 12.9 to 2.5 (or 1.2)
cents per octave for a 1 kΩ source, but an unpatched input would then sit at 1.1 V (or 2.25 V). That is
only acceptable where the probe is always wired.

### 5.8 The jack-detect probe
- Patched: the normal lug opens and the probe has no effect.
- Unpatched: the jack sees the probe through 100k against 92k, so the ADC pin swings **0.11 V ↔ 1.56–1.66
  V** (≈ 4,700 LSB on ±10.24 V), depending on how many other probe branches load the bus (13.5 kΩ worst
  case through R819's 1k, bus 3.07–3.30 V). WSC's swing is 0 ↔ 1.80 V at the tip (100k against 120k).
  That is ample for WSC's exact-match rule.
- With no capacitor, the input settles within a few microseconds (48 kΩ against tens of pF of wire and
  pin); a 1 nF cap (B5) would give τ = 48 µs, still fine for WSC's 333 µs bit; 10 nF would give 481 µs,
  too slow *(calc)*.
- With the switch on (jack driven as an output, nothing patched), the probe adds only ±33 mV (≈ 100 LSB):
  a threshold rule like WSC's will call the jack patched, but a correlation over many bits would still see
  it. Hold the probe low during loopback calibration, or the 33 mV ends up in the calibration.
- Our R819 1k between the GPIO and the clamped bus, which WSC lacks, keeps any current the D805 clamp
  carries (from a probe hole miswired to a live signal) out of the GPIO.

### 5.9 Noise and grounding
- AIN_nGND straight to the single plane, as TI's layout guidance asks ("a single dedicated ground plane
  is strongly encouraged", §11.1). Fine.
- The measurement is tip versus board ground at the ADC. Jack sleeves return through the deck's D bus
  and one wire (spec §9). Return currents in that wire are small (≤ 0.1 mA per CV output into 100k), so
  its drop is µV. Ground differences between modules on the bus appear as offset, as in every
  single-ended Eurorack input.
- The ADS8688 allows ±0.1 V on AIN_nGND, so a pseudo-differential "ground sense" (AIN_nGND to the panel
  sleeve bus) is possible, but none of the reference designs does it and the error it removes is µV here.
  Not recommended.
- Unpatched inputs are 92 kΩ nodes on hand-run wires and will pick up digital noise, but firmware ignores
  them once the probe says unpatched. Patched, the source's ≤ 1 kΩ swamps pickup.

## 6. Findings

### A — errors or risks: must fix

**A1. "100 kΩ holds an unpatched input at 0 V" is false; it reads +0.20 V.** (No part change.)
- *What:* correct the sheet-4 note (`design_analog.py` line 157), spec §6.2 ("unpatched input reads
  0 V") and the firmware plan. Unpatched readings: +0.204 V on ±10.24 V, +0.182 V on ±5.12 V with no probe
  wire; +0.108 V when the probe is wired and low. Firmware rule: an input is unpatched only when the probe
  says so, and then its value is forced to 0, as WSC does (`ComputerCard.h` L867–873). Wire PRn to every
  input whose unpatched value matters (V/oct, offsets, anything summed).
- *Why:* SBAS582C §7.5 input current (VIN − 2.25)/RIN (2.00 V on ±5.12 V). TI says the same in words:
  a floating input reads "an internal biasing voltage … invalid" (ADS8688A, SBAS680 §8.3.1), "2V DC
  output is measured" (TIDUDP7A p.12). On a V/oct input, +0.2 V is +2.4 semitones.
- *Cost:* none. *Side effects:* none.

**A2. Upsize the bidirectional and output-only 1 kΩ resistors from 0402 to 1206.**
- *What:* R405, R409, R413, R417, R421, R425 (switch side) and R431, R432 (CVO7/8): 1 kΩ 1206 250 mW,
  **UNI-ROYAL 1206W4F1001T5E, C4410 (Basic, $0.0085, 2.2 M in stock)**. If board area forbids, 0805 125 mW
  (C17513, Basic) covers fights with 1 kΩ-output modules but not with 100 Ω ones.
- *Why:* 5.6: patching an output into a jack that is driving puts 55–70 mW into the 0402 (62.5 mW) with a
  1 kΩ source and 178–275 mW with 100 Ω or stiffer sources, such as the Patch SM outputs (R6/R9/R51/R52
  100R) in four of David's modules. Patching an output into an output is a common Eurorack mistake, and
  the 1 kΩ exists precisely to survive it.
- *Cost:* Basic, no fee. *Side effects:* 8 × 3.2 × 1.6 mm instead of 1.0 × 0.5 mm. The same check applies
  to the other 1 kΩ outputs on the board (audio out, gate out), outside this block.

### B — worth adopting

**B1. A bidirectional 15 V TVS from each CV hole to GND (8 parts).**
- *What:* Nexperia **PESD15VL1BA,115, C85378** (Extended, $0.154, 26.6 k stock; SOD-323; VRWM 15 V,
  VBR ≈ 17 V, 16 pF, IR ≤ 50 nA). Cheaper: UMW PESD15VL1BA **C2831526** (Extended, $0.033, 83 k stock;
  IR ≤ 500 nA). Place each at its hole (jack side of both 1 k resistors), with a short via to the plane.
- *Why:* TI §8.3.3 "highly recommends" external ESD protection; the internal OVP is secondary. TI's
  ADS8688EVM has a bidirectional TVS footprint (SMBJ14CA) on each input behind the same 1 kΩ, and TechNote
  SBAA232A says "for maximum protection an external TVS diode is recommended". The one ADS8688 Eurorack
  board found (esper) fits an SMF16A at every tip. Mutable fits a 16 V TVS on every CV tip in Beads and a
  1 nF / 16 V CeraDiode option in Plaits and Marbles, even though their inputs have 100k in series. Ours
  has 1k, so an 8 kV contact discharge drives ≈ 6 A into the
  ADC path against a pin rated ≈ 4 A (6 kV HBM). With the TVS holding the hole at its clamping voltage
  (44 V at 5 A for the Nexperia part), the 1k limits the pin to tens of milliamps for nanoseconds. The
  ADS8688 is the $7 part hardest to rework.
- *Cost:* one Extended type, $3.07 per order + $1.23 per board (Nexperia) or $0.26 (UMW).
- *Side effects:* never conducts on legitimate ±12 V signals (VRWM 15 V). Leakage ≤ 50 nA at 15 V,
  so ≤ 50 µV through a 1 kΩ source (UMW: ≤ 0.5 mV). 16–20 pF is irrelevant at CV rates. It does not help
  the unpowered ±11 V case (it conducts only above ~17 V).

**B2. A 10 kΩ bleed resistor from +5VA to GND, and measure the rail unpowered.**
- *What:* one 10 kΩ 0402 (UNI-ROYAL 0402WGF1002TCE, **C25744**, Basic) across C403. At bring-up, measure
  +5VA to GND on the unpowered board.
- *Why:* SBAS582C §7.1 note (2) and Table 1 give ±20 V protection whenever AVDD "offers a low impedance of
  < 30 kΩ", powered or not. A 10 kΩ bleed guarantees that condition, so a 12 V signal on CVI7/8 while the
  board is off is within rating (5.5). My reading that a resistor satisfies TI's condition is an
  **inference** from the datasheet wording, not a TI statement; the unpowered impedance of the rail as
  built is **unverified** and may already be under 30 kΩ.
- *Cost:* one Basic resistor. *Side effects:* 0.5 mA more on the L78M05 (2.5 mW). Unpowered, the OVP's
  ≤ 12 µA lifts +5VA by only ~0.12 V.

**B3. Firmware default: every channel on ±10.24 V.**
- *What:* use ±5.12 V only where the source is known to stay within ±5 V (spec §6.1 leaves the choice to
  firmware).
- *Why:* 0–10 V envelopes (Doepfer ADSR 0–8 V), ±10 V LFOs and 12 V gates sit beyond ±5.18 V for long
  stretches, which TI's Table 1 marks "not recommended for extended time". On ±10.24 V only > ±10.35 V
  (rail-to-rail sources, 12 V gates) saturates. ±5.12 V buys one bit (0.16 mV → 0.08 mV per LSB), which
  CV never needs.
- *Cost:* none.

**B4. Write down the aliasing limit, and plan oversampling for audio-rate input.**
- *What:* spec §6.1 "audio-rate CV" should say: flat to ~2.5 kHz (−0.1 dB), −3 dB at 15 kHz, and only
  3–9 dB rejection of 16–30 kHz content at a 31 kHz scan (5.3). Where an input must take audio, scan fewer
  channels faster and decimate.
- *Why:* SBAS582C §7.5; *(calc)*. *Cost:* none.

**B5. 1 nF from each ADC pin to GND (8 parts).**
- *What:* 1 nF 50 V X7R 0402, FH 0402B102K500NT, **C1523 (Basic, $0.004)**, at each AIN_nP pin, returned
  to the plane next to its AIN_nGND pin. C0G is not needed for a 159 kHz shunt (and the C0G 1 nF parts,
  C53547 0402 / C1636 0603, are Extended).
- *Why:* TI's ADS8688EVM pairs the same 1 kΩ with 1000 pF on every input ("79.5 kHz low pass", SBAU230C
  Fig 3-1); TI's layout example marks an "Optional RC Filter" for every channel (§11.2); esper fits 1 nF,
  and Plaits offers 1 nF at the tip. Here it shunts RF picked up on the hand-run wiring-field leads (next
  to a 150–600 MHz module) and the fast edge of ESD, at 159 kHz with the 1k.
- *Cost:* Basic, no fee. *Side effects:* the probe's time constant becomes 48 µs, still well inside a
  333 µs probe bit (5.8). It is not an anti-aliasing filter. Do not go to 10 nF: that would buy 3–6 dB of
  alias rejection but slow the probe to 481 µs.

### C — optional

- **C1. Copy the EVM exactly:** add 1 kΩ 0402 (C11702, Basic) in each AIN_nGND leg and connect B5's
  capacitor across AIN_nP–AIN_nGND. TI recommends the matching (§8.3.2; "required" in SBAA232A). It
  cancels the 2.2 mV input-current offset, which calibration already removes, so the gain is small. Keep
  the AIN_nGND resistor ≤ 1 kΩ: the pin must stay within ±0.1 V (2.25 µA × 1k = 2.3 mV).
- **C2. REFIO capacitor.** C408 is 10 µF 0805 25 V X5R (C15850). TI asks for a 10 µF *minimum*, and an
  0805 X5R loses a large share at 4.1 V DC bias (the amount is **unverified**: check Samsung's curve for
  CL21A106KAYNNNE). The 22 µF 1206 already used on REFCAP (C12891, Basic) would keep it above 10 µF.
- **C3. Firmware: discard one scan after any DG412 change** (charge injection, 5.6), and hold the probe
  low during loopback calibration (5.8).
- **C4. Higher input impedance on chosen inputs.** Fit 1 MΩ instead of 100 kΩ (UNI-ROYAL
  0402WGF1004TCE, C26083, Basic) only on inputs that always have the probe wired: loading error drops from
  12.9 to 2.5 cents per octave with a 1 kΩ source. Leave 100 kΩ as the default.
- **Not recommended:** a larger series resistor. TI's TechNote suggests 10 kΩ, and 10–18 kΩ would keep
  ±12 V in range and help ESD, but at 10k the 1 MΩ tolerance moves the gain ±0.14 % and the drift rises
  tenfold, which costs the ADC its role as the uncalibrated reference (5.2). Also not recommended: rail
  clamps at the ADC pin (5.5), and a pseudo-differential ground sense (5.9).

## 7. Where the design is already right

- **The topology.** TI designed the ADS8688 to be driven directly (§8.3.2). One chip replaces the four
  op-amp stages, −10 V reference and mux of the reference designs, reads ±10 V natively where Patch SM,
  O&C and Mutable read ±5 V or less, and does it at 16 bits where they use 12-bit MCU ADCs.
- **1 kΩ, not more.** It keeps the 1 MΩ tolerance and drift out of the reading (±0.015 %, 2 ppm/°C), so
  the ADC can calibrate the DAC without an external reference.
- **The ADC reads the jack, not the op-amp.** With a switch on, the reading includes the load. That is a
  true closed loop, which no reference design has (WSC and EuroPi need a patch cable).
- **Protection within the rack:** ±12 V, ±15 V and a wiring mistake to a rail are all inside the ±20 V
  OVP; the DG412's internal diodes handle ±15–20 V at 2–7 mA behind 1 kΩ; the DG412's leakage and charge
  injection are negligible.
- **Pin map, decoupling and reference** follow SBAS582C (§10, §11.1): 1 µF per AVDD pin + 10 µF, 10 µF on
  DVDD, 1 µF + 22 µF on REFCAP, REFSEL low.
- **The probe** gives a clean 1.5 V swing, and R819 adds GPIO protection that WSC lacks.
- **Switch enables pulled down (4.7 kΩ):** every jack powers up as an input, so nothing drives a patched
  jack at reset.

## 8. Sources

Datasheets:
- TI ADS8684/ADS8688, SBAS582C (2015): https://www.ti.com/lit/ds/symlink/ads8688.pdf — §7.1, §7.2, §7.5,
  §8.3.2–8.3.5, §8.3.8, §9.2, §10, §11.
- Vishay DG411/412/413, doc 61564 rev B (2025): https://www.vishay.com/docs/61564/dg411.pdf — absolute
  maximum ratings p. 2, specifications p. 3.
- TI TL074H (TL07xH) — ISC ±26 mA.
- Nexperia PESD15VL1BA: https://www.lcsc.com/datasheet/lcsc_datasheet_2304140030_Nexperia-PESD15VL1BA-115_C85378.pdf

Reference designs:
- Electrosmith Patch SM Rev 3 and Daisy Patch Rev 8 schematics (Electrosmith documentation,
  https://docs.daisy.audio/hardware).
- Befaco Lich v1: https://befaco.org/docs/Lich/Lich_V1_sch.pdf and the Lich BOM.
- 4ms mp153-devboard @ 8ab17e3: https://github.com/4ms/mp153-devboard (`carrier board/v0.4/mp153-carrier-board.pdf`).
- Keeos Ogham merged v1.0: `hardware/ogham-merged-v1.0/` in the Ogham repo (local clone).
- Music Thing Workshop Computer @ 4fdefdd: https://raw.githubusercontent.com/TomWhitwell/Workshop_Computer/4fdefddb17b12598298f97cf38d3f10203cb1b1b/documentation/computer_Rev_1_0_0_Schematic.pdf and `Demonstrations+HelloWorlds/PicoSDK/ComputerCard/ComputerCard.h`.
- EuroPi @ 1192d31: https://raw.githubusercontent.com/Allen-Synthesis/EuroPi/1192d31a46897ab707e9f992d17753212eebe92d/hardware/surface-mount/europi-surface-mount.kicad_sch
- Ornament & Crime rev 2e @ cfbffab: https://github.com/mxmxmx/O_C/blob/cfbffab4e2a1b162480264d4ef57c2bcb41580c6/hardware/o_c_rev2e_schematic.pdf
- Mutable Instruments @ f4cfa76: https://pichenettes.github.io/mutable-instruments-documentation/modules/plaits/downloads/plaits_v50.pdf,
  https://pichenettes.github.io/mutable-instruments-documentation/modules/marbles/downloads/marbles_v70.pdf,
  https://github.com/pichenettes/eurorack/blob/f4cfa7697095a28d292bff758beb51deb49b5a86/beads/hardware_design/pcb/beads_v51.sch
- TI ADS8688EVM user's guide SBAU230C: https://www.ti.com/lit/ug/sbau230c/sbau230c.pdf (§3.1, Fig 3-1,
  BOM Table 8-1).
- TI TechNote SBAA232A: https://www.ti.com/lit/an/sbaa232a/sbaa232a.pdf
- TI TIDA-010008 (TIDUEC1B) and TIDA-01576 (TIDUDP7A): https://www.ti.com/tool/TIDA-010008,
  https://www.ti.com/tool/TIDA-01576
- TI ADS8688A datasheet SBAS680: https://www.ti.com/lit/ds/symlink/ads8688a.pdf (§8.3.1)
- esper @ f198efd: https://github.com/Antonio-Ciociola/esper (`pcb/esper_v1/Input.kicad_sch`)
- fpga-synth @ 0515082: https://github.com/bmboucher/fpga-synth (`pcb/fpga_synth.sch`)
- MusicBrain: https://github.com/MarkWestbroek/MusicBrain (`hardware/schematics/musicbrain-adc8/`)
- teensy-eurorack @ 237c0e6: https://github.com/newdigate/teensy-eurorack
- PJRC forum thread 55905 (Vienna Audio Model 601): https://forum.pjrc.com/index.php?threads/55905/
  (URL form **unverified**; posts 204285, 204394, 204404, 204423, 204435)
- TI E2E 785106 "EXTERNAL CV INPUTS with ADS8688" (excerpt only, **unverified**).
- Downloads were working copies for this review and are not kept.
- Doepfer A-100 technical details: https://doepfer.de/a100_man/a100t_e.htm

JLCPCB parts API (`selectSmtComponentList`), queried 2026-10-15: C11702, C25741, C25744, C21190, C17513,
C4410, C1523, C26083, C12891, C15850, C85378, C2831526, C53547, C1636, C408389, C2500.

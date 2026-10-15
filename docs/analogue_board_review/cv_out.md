# CV outputs (DAC8568 block): review against published designs

Reviewed 2026-10-15 against the checkpoint-1 schematic (`analogue_board_schematic.pdf` pp. 4–5),
`tools/analogue_board/design_analog.py` (`sheet_cv_dac`, `sheet_cv_in`) and spec v0.3.
**†** = not verified against a primary source in this pass. 1 V/oct: 1 mV = 1.2 cents.

---

## 1. Our design, exactly as drawn

**DAC (U501, sheet 5):** DAC8568IAPWR (C486051). AVDD pin 3 = +3V3A (XC6206), 10 µF + 100 nF (C501/C502).
LDAC pin 1 = GND, CLR pin 9 = +3V3A, SYNC = CS_DAC (10 kΩ pull-up R501), SCLK/DIN on SPI-A.
VREFIN/VREFOUT pin 8 = DAC_VREF, C503 1 µF 25 V X5R 0402. Grade A: 0–2.5 V, power-on reset to
zero code, internal reference off until commanded.

**Offset reference:** DAC_VREF → R502 10 k / R503 20 k → OFFS_DIV, C504 1 µF to GND (Thevenin 6.67 kΩ,
τ = 6.67 ms, 24 Hz) → U504A TL074H follower → OFFSET_REF = 2/3·VREF = 1.667 V. U504B–D are grounded followers.

**Stages (U502, U503, TL074HIDR on +12V/−12V nets, 100 nF each pin):** + input = DACn;
Rg = 10 kΩ 0402 (R505, R507 …) from − input to OFFSET_REF; Rf = 30 kΩ 0603 (R504, R506 …) ∥ Cf = 100 pF C0G
(C505 …) from − input to the op-amp output = CVDRVn.

  Vout = (1 + 30/10)·Vdac − (30/10)·OFFSET_REF = 4·Vdac − 2·VREF = **−5.000 … +4.9998 V**,
  LSB = 152.6 µV = 0.18 cent. Mid-code = 0 V whatever VREF does (checked).

**Jack side (sheet 4):**
- CV1–6: CVDRVn → DG412 (U402/U403, on at logic 1, ±12 V nets, VL = +5VD) → 1 kΩ 0402 (R405, R409, R413,
  R417, R421, R425) → jack node CVn. The jack node also feeds 1 kΩ (R403 …) → ADC_INn with 100 kΩ (R404 …)
  to GND (and the ADS8688's 1 MΩ). SW_ENn from the TCA9555 with 4.7 kΩ pull-downs (R406 …).
- CV7–8: CVDRV7/8 → 1 kΩ 0402 (R431, R432) → CVO7/CVO8 holes. **No ADC path.**
- Feedback is taken from the op-amp pin, so the 1 kΩ (and the DG412) are **outside** the loop.

**Firmware intent (spec §6.4, §15):** 3-point calibration per channel in the M24C64; CV1–6 calibrate by
loopback (switch on, jack unpatched, ADC reads the jack).

---

## 2. Reference designs (schematics read, not summaries)

### 2.1 Westlicht Performer — same DAC family, 8 outputs
Source: `westlicht/performer-hardware` @ da7d8f8, `dac.sch` (sheet 8/8, rev 1.0, 2018-10-09) and
`sequencer.pdf` p. 8; `bom/bom.csv`; firmware `westlicht/performer` @ f0c2328 `src/platform/stm32/drivers/Dac.{h,cpp}`.
- **U8 DAC8568C** (BOM: DAC8568ICPW) on **+3.3VA**; LDAC pin 1 to GND, CLR pin 9 to +3.3VA (same as ours).
  VREF pin 8: C26 2.2 µF + C27 100 nF.
- **Offset:** VREF → R48 33 k / R47 22 k → **VBIAS = 1.00 V**, C25 100 nF, **unbuffered** into the + inputs.
- **Stage (×8, U4/U15 OPA4172 on ±12 V):** inverting. DACn → 24 k (R44 …) → − input; feedback 100 k (R35 …)
  ∥ 18 pF (C16 …); **R43 … 220 Ω in series, with both the 100 k and the 18 pF taken from the CV side of the
  220 Ω**: the resistor is inside the loop. Sheet note: "Output range [5.17V, −5.25V]". Jacks are wired straight to
  the CV nets (`jacks.sch`), no further resistor.
- Firmware supports grade A or C; for A it "Shift[s] data by one bit". Init: `reset()` (software reset),
  `setInternalRef(true)` (static mode), power-up all DACs. So Performer uses 0–2.5 V of a grade-C part at 3.3 V
  AVDD: 15 bits.

### 2.2 Ornament & Crime rev 2e
Source: `mxmxmx/O_C` @ cfbffab, `hardware/o_c_rev2e_schematic.pdf` (single sheet), `software/o_c_REV/OC_DAC.h`.
- **U3 DAC8565** on 3V3_A, VREF_OUT decoupled 100 nF + 470 nF.
- **Offset:** VREF_2v5 → 47 k / 47 k + 100 nF → **V_bias 1.25 V**, unbuffered into the + inputs.
- **Stage (U5, U6 OPA2172, VCC/VEE):** inverting, 24k9 in, 100 k feedback **from the jack side of the 220 Ω**,
  22 pF from the op-amp output pin (dual feedback). Gain −4.02, range **+6.27 … −3.77 V**, consistent with
  `kOctaveZero = 3` in OC_DAC.h.
- Calibration: a table `calibrated_octaves[channel][OCTAVES + 1]` with linear interpolation inside each octave
  (OC_DAC.h L53–55, L104–118), i.e. one point per volt, not three.

### 2.3 Mutable Instruments Marbles v70
Source: pichenettes documentation, `marbles_v70.pdf` sheet 1 (IC4) and sheet 4 "Outputs".
- **IC4 DAC8164ICPW** (14-bit quad) on +3V3_A, VREFH: C25 470 nF.
- **Offset:** VREF → R74 150 k / R73 100 k, C51 470 nF → **VREF_BIAS 1.00 V**, unbuffered.
- **Stage (IC7 OPA4171):** inverting, 23.7 k in, **R60 100 k from the jack side of R62 1.0 k**, C43 47 pF
  from the op-amp output pin: **1 kΩ inside the DC loop**. Labelled "−5.3V to 5.3V". A TL074 (IC10) drives a
  bicolour LED from the jack node.

### 2.4 Mutable Instruments Stages v70
Source: `stages_v70.pdf` sheets 5 ("DAC&CV outputs") and 6; firmware `pichenettes/eurorack` `stages/drivers/dac.cc` L135–141.
- **IC4 DAC8168IAPW** (14-bit, 8-channel, **grade A**: same family and pin-out as ours), AVDD +3V3_A.
  Firmware's first frame is `0x090A0000`, "internal reference always powered on, flexible mode" (SBAS430F Table 10).
- **Offset:** AREF_2.5 (the DAC's reference pin) → R40 130 k / R48 100 k, C43 1 µF → **VREF_BIAS 1.087 V**, unbuffered.
- **Stage (IC14 plain TL074):** inverting, 20 k in, **R46 130 k from the jack side of R39 1.0 k**, C49 100 pF
  from the op-amp pin. Range **±8.1 V** from a TL074 on ±12 V.

### 2.5 Music Thing Workshop System Computer Rev 1.0.0
Source: `TomWhitwell/Workshop_Computer` @ 4fdefdd, `documentation/computer_Rev_1_0_0_Schematic.pdf`.
- **Precision CV out (p. 3, U2A TL074H):** PWM → R1 75 k / R2 62 k / R19 270 k / C6 2.2 nF / C5 330 pF 2-pole MFB,
  offset from **−5V_REF via R58 226 k**, **R55 1 k outside the loop**. About ±6 V.
- **Audio/CV out (p. 2, U2C TL074H):** MCP4822 → R46 10.7 k, R47 63.4 k ∥ C28 68 pF, offset R41 52.3 k from
  −5V_REF, **R48 1 k outside the loop**.
- **−5 V reference (p. 4):** VR1 TL431ASA-7 with R53/R54 3.3 k 1 %, fed from −12 V via R52 3.3 k 1 %.
  This is a separate reference, not ratiometric to the converter.

### 2.6 EuroPi (through-hole)
Source: `Allen-Synthesis/EuroPi` @ 1192d31, `hardware/through-hole/europi-through-hole-schematic.pdf`.
GPn → R1 1 k / C9 100 nF → TL074 non-inverting, R35 220 k / R29 100 k (×3.2) → **R7 1 k outside the loop**,
0–10 V. The analogue input is 100 k (R28) into an inverting TL074, so EuroPi's "loop each output into the input"
calibration happens **under a 100 kΩ load**.

### 2.7 Hermetic Modular Alchemy Lab V2 (switched bidirectional jacks)
Source: `hermetic-modular/alchemy-sdk` @ 3f40b66.
- `alchemy_lab_v2_layout.h` L206–216: **DG411 closes on logic LOW**, driven by a PCA9557; boot output register
  0xFF = "DG411 OFF" (L186–190). L222–225: "Inverting summer (TL07x on ±12 V): V_jack = 5 V − 3.03 × V_dac_pin".
  J3–J6 from an MCP4728 (VREF = VDD), J7–J8 from the STM32 DAC.
- `cv_jack.h` L50–54: the jack reading is "Lab-accurate (~±10 mV) in input mode; approximate (~±50 mV) in output
  mode (cal was measured DG411-open)".
- `v2_factory_cal.cpp`: isolation test (a disconnected DAC must not appear on any input, L89–105); **"Stage
  neutral before connecting. Only one DAC may be connected"** (L106–107); **17-point sweep**, linear fit over the
  middle 13 points, endpoint compression allowed, verification at fresh points (L108–198).
- The output series resistor isn't stated in the SDK †.

### 2.8 Others checked
- **Daisy Patch SM** datasheet (local `psm_ds.txt` L134, L221–230, L391): CV out 0–5 V from the STM32 12-bit DAC,
  "Output Impedence: 100R". The internal circuit isn't published †.
- **Befaco Lich / Oneiroi, 4ms MP153 Brainboard** (from `pcm3060_survey.md`): codec outputs only, DC-coupled with
  1 kΩ outside the loop. No precision DAC CV stage was found to compare †.

---

## 3. Comparison

| | DAC / bits | Offset source | Topology | Range | Op-amp | Series R | Rf ∥ Cf pole | Calibration |
|---|---|---|---|---|---|---|---|---|
| **Ours** | DAC8568A / 16 | DAC VREF → 10k/20k, **1 µF**, **TL074H buffer** | non-inverting ×4 | ±5.00 V | TL074H | **1 k outside loop** (+DG412 on CV1–6) | 30k∥100p, 53 kHz | 3 points, loopback (CV1–6 only) |
| Performer | DAC8568C / 15 used | DAC VREF → 33k/22k, 100 nF, unbuffered | inverting ×4.17 | +5.17/−5.25 | OPA4172 | 220 Ω **inside** loop | 100k∥18p, 88 kHz | firmware † |
| O&C 2e | DAC8565 / 16 | DAC VREF → 47k/47k, 100 nF, unbuffered | inverting ×4.02 | +6.27/−3.77 | OPA2172 | 220 Ω **inside DC loop**, 22p local | 100k∥22p, 72 kHz | 1 point per octave |
| Marbles | DAC8164 / 14 | DAC VREF → 150k/100k, 470 nF, unbuffered | inverting ×4.22 | ±5.3 | OPA4171 | **1.0 k inside DC loop**, 47p local | 34 kHz | † |
| Stages | DAC8168A / 14 | DAC VREF → 130k/100k, 1 µF, unbuffered | inverting ×6.5 | ±8.1 | **TL074** | **1.0 k inside DC loop**, 100p local | 12 kHz | † |
| Workshop Computer | PWM+ΣΔ / ~19 eff. | separate TL431 −5 V | 2-pole MFB | ≈ ±6 | TL074H | 1 k outside | 2-pole | ≤10 points, EEPROM |
| EuroPi | PWM | none | non-inv ×3.2 | 0–10 | TL074 | 1 k outside | RC 1.6 kHz | under 100 k load |
| Alchemy Lab V2 | MCP4728 / 12 | VDD-referenced | inverting summer | ±5 | TL07x | † | † | 17-point loopback |

Every precision DAC85xx/81xx design derives the offset from the DAC's own reference, as ours does. **None of
them leaves a series resistor outside the loop.** Performer, O&C, Marbles and Stages all take DC feedback from
the jack side.

---

## 4. Analysis

### 4.1 Offset method and maths
Ours and the four DAC-reference designs are ratiometric: Vout = VREF·(4D − 2), so a reference error is a pure
gain error about 0 V and mid-code is 0 V. That is right. The difference is mechanical. They inject the offset
at the **+ input of an inverting stage**, which draws no current, so the divider needs no buffer. Ours injects
it through Rg into the − node of a non-inverting stage, which needs a low-impedance source: the U504A buffer.
The buffer adds its Vos ×3 (calibrated out), its drift ×3 (2 µV/°C typ → 6 µV/°C, negligible) and a little
code-dependent crosstalk: the 8 stages draw −0.67 … +1.33 mA from it. That is mV-level only at high frequency
(Zout rises above ~10 kHz). The workable alternatives are in C2.

### 4.2 Error budget (1 V/oct, cents)
Datasheets: DAC8568 SBAS430F §7.2; TL07xH SLOS080W §5.7; ADS8688 SBAS582C.

| Source | Value | Before cal | After 3-point cal (25 °C) |
|---|---|---|---|
| DAC INL | ±4 typ / ±12 max LSB (×4 → ±0.6 / ±1.8 mV) | — | **±0.7 / ±2.2 cents** (not removed by 3 points) |
| DAC offset, gain | ±1/±4 mV; ±0.01/±0.15 % FSR | ±5 / ±19 cents offset | removed |
| Reference | ±0.1 % max; **grade A drift 5 typ / 25 max ppm/°C** | gain only | 10 °C: 0.06 / 0.3 cent/oct |
| TL074H Vos ×4, buffer ×3 | ±1 typ / ±4 max mV (±5 mV hot) | ±8 / ±34 cents | removed; drift 2 µV/°C typ ×7 → 0.1 cent / 10 °C |
| Resistors 1 %, ±100 ppm/°C | Rf/Rg, 10k/20k | offset ±70 cents, scale 1.5 % (18 cents/oct) worst | removed; tracking drift 0.2 typ / ~1.8 worst cents/oct per 10 °C † |
| Calibration reference (ADS8688 gain ±0.02/±0.05 % FSR, offset ±0.5/±1 mV; 1k/100k/Zin divider ±0.026 %) | — | — | scale 0.4 typ / 1.0 max cent/oct |
| Quantisation | 152.6 µV | 0.18 cent | 0.18 cent |
| **Load: 1 kΩ outside loop into 100 kΩ** | −1.0 % | — | **−12 cents/oct, −60 cents at +5 V** |

- **Before calibration:** about ±15 cents typical at 0 V and 4 cents/oct. The worst case is ±120 cents at 0 V and
  20 cents/oct: calibration is mandatory, as planned.
- **After calibration, unloaded:** better than 1 cent/oct typical and about 2–3 cents/oct worst over a 10 °C warm-up.
- **After calibration, into a 100 kΩ V/oct input: 12 cents/oct.** The load error is 15–20× everything else and
  undoes the 16-bit choice (A1).

**Precision op-amp?** No. Calibration removes the TL074H's offset. Its drift (2 µV/°C typ; SLOS080W gives no
max) contributes about 0.1 cent per 10 °C, against about 1 cent/oct from resistor tracking and 12 cents/oct from
the load. Stages ships ±8 V outputs on plain TL074s. An OPA4197IDR (C2058532, Extended, $2.73) would be a new
part type, since the TL074H stays for the codec. That is about $11/board-order for no measurable gain.

### 4.3 Range: is ±10 V now practical?
SLOS080W §5.7 (TL07xH): output swing from the rail is **115 typ / 210 max mV into 10 kΩ** (positive) and
105 / 215 mV (negative), and **520 / 965 mV into 2 kΩ**, all at VS = 40 V. Fig. 5-26 (±10 V supplies, follower)
shows clipping about 0.5 V inside the rails. Our stage's load is ≥ 20 kΩ: the feedback is 40 k, plus the internal
92 k, plus the external load. So **±10 V from ±11.6 V rails is practical**, with ≥ 1 V of margin into ≥ 10 kΩ;
it is marginal into 2 kΩ at low rails. The spec's "±10 V needs OPA4197" (§1, §7, §13, sheet-5 note) was true of
the old TL074, not the TL074H.

The references output Performer ±5.2 V, Marbles ±5.3 V, O&C −3.8/+6.3 V, Stages ±8.1 V, WSC ±6 V, Alchemy
±5 V, EuroPi 0–10 V and Patch SM 0–5 V; **none ±10 V**. Doepfer's convention is LFO about ±2.5 V, ADSR 0–8 V and
1 V/oct. ±5 V covers pitch and LFOs but can't make an 8 V envelope. Recommendation: keep ±5 V (with overrange,
B2) and add 0–10 V as a per-channel option (C4). Keep ±10 V as a documented resistor variant (C4); a range nobody
else uses isn't worth halving the resolution.

### 4.4 DG412 in series (Vishay 61564 rev B / 70050 rev G)
- **RDS(on)** 25 Ω typ, 35 Ω max (room, ±13.5 V), 45 Ω max over temperature. It is a little higher on ±11.6 V and
  varies a few Ω over ±5 V (typical curve; flatness isn't specified †). In series with 1 k into ≥ 48 k, a 5 Ω
  variation is ≤ 0.01 %: ≤ 0.3 cent. The loopback calibration includes it.
- **Charge injection** 5 pC typ. Into a 100 pF cable that is ≈ 50 mV for ~100 ns (1 k·C): negligible. The real
  switching glitch is the **step from the jack's previous voltage to the stage's output**. Firmware must write the
  wanted value (or the jack's current ADC reading, for a bumpless change) before closing (B5; Alchemy L106–107).
- **tON/tOFF** 110 / 100 ns. **Off isolation** comes from CS/D(off) 9 pF. If a channel is an input but its DAC
  carries audio-rate content, 9 pF into an unpatched jack node (~92 k) leaks about −26 dB at 10 kHz: park the
  DAC (C7).
- **External drive, switch off:** the jack sees ~92 kΩ. Up to ±12 V the DG412 pin sits at most 0.4 V beyond its
  ±11.6 V rails, under a diode drop, so negligible current through the 1 k.
- **External drive, switch on (output into output):** I = ΔV/(1 k + Ron + Rext). Ours at ±5 V against ±10 V through
  1 k gives 7.4 mA; against a hard source, 14.6 mA. That is within the DG412's 30 mA continuous and the
  TL074H's ±26 mA Isc. **But 7.4 mA puts 55 mW in R405 (0402, 62.5 mW); against a 100 Ω source, 180 mW** (B3).
- **Board unpowered, other module driving:** ≤ (10 − 0.6)/1 k = 9.4 mA into the DG412 clamp diodes, under 30 mA.
  The 1 k on the jack side is what makes this safe, which is why I don't recommend moving it.
- **Power-up:** IN is held low by 4.7 k. With VL (+5VD) not yet up the switch state is unspecified †, but the stage
  outputs are at 0 V then (zero code, reference off), so nothing reaches the jack. VL ≤ V+ + 0.3 V holds because
  the buck can't exceed its input (low risk †).

### 4.5 Output protection and capacitive load
- **Short to GND:** ≤ 5 V/1 k = 5 mA, 24 mW in the 1 k. Fine.
- **Short to ±12 V (hard):** (12 + 5)/1.025 k = 16.6 mA. That is within the TL074H and DG412 limits, **but 0.28 W
  in an 0402** (B3).
- **Capacitive load:** in the current topology the 1 k isolates the cable from the op-amp. The op-amp pin sees the
  DG412's 35 pF plus the trace: phase margin ≈ 45–50° (SLOS080W Fig. 5-25: 56° at 20 pF, 39° at 100 pF, 18° at
  500 pF). Stable for any cable. **The series resistor is needed**, for this and for the switch's current limit.
  With feedback taken after the 1 k (A1, CV7–8), the 100 pF from the op-amp pin closes the HF loop locally.
  β → 1 above ~200 kHz and loop crossover is near 5 MHz, so the margin stays the op-amp's unity-gain value.
  This is the Stages arrangement on a plain TL074 (R39 1.0 k, C49 100 pF).
- **Do not hang capacitance on OFFSET_REF:** a G = +1 TL074H has 18° of phase margin at 500 pF (C6).

### 4.6 DAC8568 power-on and reference enable
SBAS430F §8.2.8 and §8.3.1. Grade A powers up at zero code with the reference off (pin 8 three-stated; our
divider pulls it to 0 V). All stages sit at 0 V until firmware acts: correct. The trouble is enabling the
reference. VREF steps up in ≤ ms †; OFFSET_REF follows through **τ = 6.67 ms (C504)**, while the DAC outputs follow
VREF at once.
- With codes at zero (Performer's order): Vout = −2·LP(VREF), and **every output ramps to −5 V**.
- With mid-code written first: Vout = 2·[VREF − LP(VREF)], **a spike up to ≈ +5 V decaying with τ = 6.7 ms**
  (16-bit settling ≈ 75 ms).

CV1–6 are protected only if their switches are off. **CV7–8 pass it to the jack.** On a warm MCU restart the
TCA9555 keeps its outputs, so the switches may still be on. A `RESET_POWER_ON` software reset (as in Performer's
`Dac::init`) turns the reference off and zeroes the codes: both glitches, on live jacks. Fix: B1.

### 4.7 Cf = 100 pF across 30 kΩ, and 31 kHz updates
G(s) = 1 + Rf/(Rg(1 + sRfCf)): the pole is at 53 kHz and the zero at 212 kHz, so the gain falls from 4 to 1. The
DAC's HF feedthrough passes at ×1, not ×4, and OFFSET_REF noise is rolled off: good. It sits among the references
(Performer 88 k, O&C 72 k, Marbles 34 k, Stages 12 kHz). There is no zipper for CV: at 31.25 kHz and 0.15 mV
steps, a sweep is smooth *if firmware writes every sample*. Block-rate updates (e.g. 1 kHz) would step audibly on
a VCA or filter, and 53 kHz won't smooth them: interpolate per sample. For **audio-rate** content the 53 kHz pole
leaves zero-order-hold images at 31.25 kHz ± f almost untouched: a 10 kHz tone has a 21 kHz image only about
−7 dB down. Fine for FM and modulation; use the codec for audio, or see C5.

---

## 5. Findings

### (A) Must address before the order

**A1. The 1 kΩ series resistor sits outside the feedback loop: the output drops 1 % into a 100 kΩ V/oct input
(12 cents/octave, 60 cents at +5 V), and calibration can't see it.**
- *Why:* the output divides as R_load/(R_load + 1.025 k). Loopback calibration happens with only the internal
  92 k load. A 100 k external input brings the total to 48 k: −1.0 % (§4.2). With a 47 k input it is −2.1 %, with
  10 k −9 %. This is 15–20× every other residual. Performer and O&C (220 Ω) and Marbles and Stages (1.0 kΩ) all
  take DC feedback from the jack side, so none has this error (§2).
- *Fix, CV7–8 (hardware, $0):* connect the output end of R516 (U503C) and R518 (U503D), both 30 k, to the
  **jack side** of R431/R432 (nets CVO7/CVO8) instead of CVDRV7/8. Leave C511/C512 (100 pF) on the op-amp output
  pin (Marbles and Stages dual feedback). In the generator, the simplest way is to move R431/R432 from
  `sheet_cv_in` into `sheet_cv_dac` beside U503C/D. Upsize R431/R432 to **0805, 1 k, C17513 (Basic)**: in a
  sustained short the loop drives the op-amp to the rail, 11.6 V²/1 k = 135 mW. Side effect: the op-amp swings
  about 1 % beyond the target into 100 k, which is irrelevant at ±5.4 V.
- *Fix, CV1–6 (firmware + spec, $0):* the same hardware change would open the DC loop whenever the DG412 is off,
  driving the op-amp to a rail and giving a rail-height spike at switch-on. Moving the 1 k to the op-amp side would
  expose the DG412 to the jack: unpowered back-drive with a ≤ 100 Ω source exceeds its 30 mA rating. So keep the
  hardware and **make load compensation a firmware requirement**. With the switch on, the ADC reads the jack itself
  through a fixed ratio (R403 into R404 ∥ 1 MΩ), so a slow servo (≈ 10 ms) or a per-patch gain estimate removes the
  load error to the calibration's accuracy. Clamp the correction (±3 %) and flag a jack that is being driven by
  another output. Write this into spec §6.2/§7, because CV7–8, with no ADC path, can't do it.
- *Decision needed now:* if David prefers a hardware fix for CV1–6 as well, see C9. It changes sheet 4.

### (B) Worth adopting

**B1. Reference-enable glitch: shrink C504 and fix the init sequence.**
- *Change:* C504 1 µF → **1 nF, C1523 (Basic)** (τ 6.7 µs). Leaving it unfitted is also fine: the follower needs
  no input capacitor, and with the RC removed VREF noise cancels at mid-code instead of being filtered.
- *Firmware order:*
  1. Set the TCA9555 port to 0 and configure it as outputs, so every switch is off.
  2. Write the 0 V code (0x8000 now; ≈32545 after B2) to all 8 channels; outputs stay at 0 V with the
     reference off.
  3. Enable the reference with **0x090A0000** (flexible, always on, as Stages does), so a DAC power-down command
     can't drop it.
  4. Wait about 10 ms (bench-verify).
  5. Write the targets.
  6. Close each switch only after its channel holds the wanted value.
  7. Never send the software reset on a warm restart.
- *Why:* §4.6. With C504 = 1 µF, CV7–8 swing to −5 V, or spike to +5 V, for tens of ms on every boot and reflash.
- *Side effects:* none measurable; HF reference noise is now cancelled at mid-code rather than filtered.

**B2. Give the stage ~7 % overrange, so a calibrated ±5.00 V is always reachable inside the DAC's linear codes.**
- *Change:* Rf 30 k → **33 k (C25779 0402, or C4216 0603, Basic)**; divider R502/R503 10 k/20 k → **12 k / 22 k
  (C25752 / C25768, Basic)**. Vout = 4.3·Vdac − 5.34, i.e. **−5.34 … +5.41 V**, LSB 0.164 mV.
- *Why:* INL is only specified between codes 485 and 64714 (SBAS430F §7.2 note 1); today those map to −4.93 V …
  +4.88 V. Worst-case 1 % resistors shrink the nominal ±5 V to about ±4.86 V. CortHex needs "±5 V calibrated".
- *Side effects:* the 0 V code moves from 32768 to about 32545 (Vout = VREF·(4.3·D − 2.135)). The output still
  tracks VREF, so B1's "write the zero code, then enable the reference" still gives 0 V. Read extremes with the
  ADS8688 on ±10.24 V (5.4 V × 0.989 exceeds the ±5.12 V range). The ±10 V variant (C4) changes these values
  anyway. An exact 0.6515 divider needs 10.7 k (C270654), which is Extended; not worth $3.07.

**B3. Upsize the eight output resistors to 0805.**
- *Change:* R405, R409, R413, R417, R421, R425, R431, R432 → **1 k 0805, C17513 (Basic, 125 mW)**.
- *Why:* output into output against a +10 V/1 k source is 55 mW (0402 rating 62.5 mW); against a 100 Ω source,
  180 mW; a hard ±12 V touch, 280 mW (§4.4–4.5). Performer's 220 Ω output resistors are 0603 (`bom.csv` line 29).
- *Side effects:* a little more area, no cost.

**B4. Correct the spec and the sheet notes before they become tutorial content.**
- DAC8568**A** reference drift is **5 typ / 25 max ppm/°C**. The "2 ppm/°C typ" in §7.1 is the grade C/D figure;
  LCSC's C486051 listing also wrongly says 2 ppm.
- ±10 V *is* practical on the TL074H (§4.3). Change §1, §7, §13 and the sheet-5 text "OPA4197 … gain 8".
- CV7–8 can't calibrate by loopback: calibrate them by patching CVO7→CVI7 and CVO8→CVI8. After A1, the load
  during calibration no longer matters.

**B5. Use the free loopback to calibrate properly (firmware).**
- Store one point per volt, like O&C's `calibrated_octaves[OCTAVES+1]`, or 17 like Alchemy, rather than 3. That
  takes the INL residual from ≤ ±2.2 cents to well under 1 cent and costs ~50 bytes per channel in the 8 KB EEPROM.
- Adopt Alchemy's isolation test (a disconnected DAC must not appear on any input: catches a stuck switch),
  "stage neutral before connecting", and verification at fresh points.
- Exclude codes outside 485–64714 from the fit.

### (C) Optional

- **C1. Precision op-amp: not warranted** (§4.2). Keep the TL074H.
- **C2. Delete the offset buffer.** Either inject the offset per stage as a Thevenin pair, 15 k from DAC_VREF and
  30 k to GND (= 1.667 V behind 10 k, so the maths is unchanged), or go inverting with the bias at the + input as
  all four references do. This removes U504, C504, its decoupling and the buffer's ×3 offset and drift. The cost is
  about 1.3 mA of code-dependent load on the DAC reference: 30 µV/mA load regulation gives about 80 µV, 0.5 LSB of
  DC crosstalk. Optional; the current circuit works.
- **C3. Resistor tracking.** Put Rg in the same 0603 series as Rf (10 k 0603 C25804), and both divider resistors
  too (20 k 0603 C4184), each pair adjacent; tracking is not specified †. For the best drift, 0.1 % 25 ppm thin
  film (Yageo RT0603 C95204 10 k, C723585 30 k, C723637 20 k; Extended, 3 types = $9.21/order) brings it to
  ≈ 0.3 cent/oct per 10 °C.
- **C4. Range options.** Per channel, a 3-pad solder jumper on the far end of Rg: OFFSET_REF (default) or GND.
  GND gives **0 … +10.75 V** for envelopes and gates, at no cost. ±10 V build variant: Rf **75 k (0603 C23242)**,
  divider **15 k / 20 k (C22809 / C4184)**, all Basic: −10.71 … +10.54 V nominal. Calibrate within ±10 V (the ADC's
  ±10.24 V range ×0.989 covers it). Needs ≥ 10 kΩ loads.
- **C5. Audio-rate outputs.** If the CV outs will carry audio, Cf 100 pF → **330 pF C0G (C76965 Murata, Extended)**
  moves the pole to 16 kHz. Otherwise document "audio on the codec outs".
- **C6.** No capacitance on OFFSET_REF (§4.5). If filtering is ever wanted there, use a series R (≥ 100 Ω) first.
- **C7.** Firmware: hold a channel's DAC constant while its jack is an input (Coff leakage, §4.4).
- **C8. DAC8568ICPWR** (C524819, $23.38, 5 ppm/°C max). Not worth it: at AVDD 3.3 V only half its 0–5 V span is
  usable (Performer's situation), and grade A's drift costs ≤ 0.3 cent/oct per 10 °C.
- **C9. Hardware load fix for CV1–6** (instead of A1's firmware). Make each switch path a changeover with a DG413
  (or a third switch chip), so the DC feedback comes from the jack side when on and from the op-amp side when off.
  Adds an Extended part type and routing; only if the firmware servo proves unworkable.

### Where our design is already right
- **Ratiometric offset from the DAC's own reference:** the same principle as Performer, O&C, Marbles and Stages.
  Mid-code = 0 V and reference drift is a pure gain error.
- **LDAC → GND** (synchronous mode, SBAS430F §8.3.2), **CLR → AVDD**, **VREF 1 µF** (≥ 150 nF recommended):
  identical to Performer.
- **Grade A at 3.3 V AVDD** uses all 16 bits; Performer's grade C at 3.3 V used 15.
- **TL074H** is adequate after calibration; Stages does ±8 V on a plain TL074.
- **30 k ∥ 100 pF C0G** (53 kHz) sits among the references.
- **1 kΩ series resistor:** the Mutable value. It isolates cables and protects the switch; only its position
  relative to the loop is wrong (A1).
- **DG412 + 4.7 k pull-downs:** jacks start as inputs from power-on, rather than relying on an expander's register
  as Alchemy's DG411/PCA9557 does.
- **The ADC reads the jack through its own 1 k**, so the read-back is the same in input and output mode. Alchemy
  says its output-mode reading is only ~±50 mV. This is also what makes A1's firmware fix possible.
- **Spare sections** are grounded followers. The DAC8568 and ADS8688 both latch SDI on SCLK falling edges, so they
  share SPI mode 1.

### Bench checks for the first boards
1. Scope CVO7 at power-up and at reference enable, before and after B1.
2. Measure CV1 and CV7 at +4 V, open and into 100 kΩ (expect ≤ 0.02 % change on CV7 after A1, and on CV1 with the
   servo).
3. Check TL074H swing at ±10 V into 10 kΩ on the actual rails if the C4 variant is wanted.
4. Run 10 °C warm-up drift on a calibrated channel.

---

## 6. Sources
- TI **DAC8568** SBAS430F (Apr 2018): §5 table, §7.2, §8.2.4, §8.2.8, §8.3.1–8.3.2, §9.2.1.1, Fig. 129.
- TI **TL07xH** SLOS080W (Jul 2025): §5.1, §5.3, §5.7, Figs. 5-25 and 5-26.
- Vishay **DG411/412/413**: doc 61564 rev B (2025) and doc 70050 rev G.
- TI **ADS8688** SBAS582C: Electrical Characteristics, §8.3.2–8.3.3.
- Westlicht Performer hardware: https://github.com/westlicht/performer-hardware (`dac.sch`, `sequencer.pdf` p. 8,
  `jacks.sch`, `bom/bom.csv`) @ da7d8f8; firmware
  https://github.com/westlicht/performer/blob/master/src/platform/stm32/drivers/Dac.cpp @ f0c2328.
- Ornament & Crime: https://github.com/mxmxmx/O_C/blob/master/hardware/o_c_rev2e_schematic.pdf and
  `software/o_c_REV/OC_DAC.h` @ cfbffab.
- Mutable Marbles: https://pichenettes.github.io/mutable-instruments-documentation/modules/marbles/downloads/marbles_v70.pdf
- Mutable Stages: https://pichenettes.github.io/mutable-instruments-documentation/modules/stages/downloads/stages_v70.pdf;
  firmware `pichenettes/eurorack` `stages/drivers/dac.cc` L135–141.
- Workshop System Computer: https://github.com/TomWhitwell/Workshop_Computer/blob/main/documentation/computer_Rev_1_0_0_Schematic.pdf @ 4fdefdd.
- EuroPi: https://github.com/Allen-Synthesis/EuroPi/blob/main/hardware/through-hole/europi-through-hole-schematic.pdf @ 1192d31.
- Alchemy Lab SDK: https://github.com/hermetic-modular/alchemy-sdk @ 3f40b66 (`hardware/alchemy-lab/v2/include/alchemy/hw/cv_jack.h`,
  `alchemy_lab_v2_layout.h`, `src/cv_jack.cpp`, `src/v2_factory_cal.cpp`).
- Electrosmith Daisy Patch SM datasheet v1.0.5 (https://docs.daisy.audio/hardware).
- Doepfer A-100 technical details: https://www.doepfer.de/a100_man/a100t_e.htm
- JLCPCB parts API, 2026-10-15 (`selectSmtComponentList`):
  - Basic: C17513, C21190, C1523, C15195, C25752, C25768, C25779, C4216, C25804, C4184, C22809, C23242.
  - Extended: C76965, C95204, C723585, C723637, C2058532 (OPA4197IDR $2.73), C2057383 (OPA4172IDR $1.31),
    C524819 (DAC8568ICPWR $23.38), C2680013 (DAC8568IBPWR, 0 stock).
- Downloads and renders were working copies for this review and are not kept.

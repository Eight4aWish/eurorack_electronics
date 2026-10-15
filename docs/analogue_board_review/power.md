# Power block review: analogue board Rev A, checkpoint 1

Reviewed 2026-10-15 against `tools/analogue_board/design.py` (`sheet_power`), `parts.py`, the
generated netlist `hardware/analogue_board/output/analogue_board.net`, schematic page 2, and
spec §2, §4, §5, §8–§10, §15.

**Marks:** **[unverified]** = not confirmed against a primary source in this review.
**[est.]** = my own arithmetic from datasheet figures. **[sub-agent]** = values read from the
file by a sub-agent and not re-read by me; spot checks are noted where I did them.

**Verdict:** the block is sound. Nothing found would stop a board working on the first power-up
with a Pico 2 or Teensy 4.1, so there are **no A findings**. Five B changes are worth making
before the order. All five use Basic parts, add no Extended fee, and cost under $0.50 a board:
1. Give the buck its own ferrite and input capacitance.
2. Add an EN divider so the digital rails start after, and stop before, the analogue 5 V.
3. Filter the codec supply pins, as every reference does.
4. Add a P-FET bypass on MOD_5V, for the ESP32-P4.
5. A firmware rule for USB-only power.

---

## 1. Our design, exactly

### Entry
| Ref | Part | LCSC (type) | Net / role |
|---|---|---|---|
| J201 | 2×5 shrouded box header, pins 1–2 = −12V_IN, 3–8 = GND, 9–10 = +12V_IN | hand-soldered | Red stripe is pin 1 = −12 V, as Doepfer specifies |
| D201 / D202 | SS14, SMA, 40 V 1 A, IFSM 25 A | C2480 (Basic) | Series diode in +12 V (A at the header) and −12 V (K at the header) |
| FB201 / FB202 | BLM18PG121SN1D, 0603: 120 Ω at 100 MHz, 2 A, 50 mΩ | C14709 (Basic) | After the diode |
| C201 / C203 | 10 µF 50 V X5R 1206 (Samsung CL31A106KBHNNNE) | C13585 (Basic) | Rail bulk |
| C202 / C204 | 100 nF 50 V X7R 0603 | C14663 (Basic) | |
| TP201–204, PWR_FLAGs | | | |

### Loads on each rail (from the netlist)
| Rail | Parts on it |
|---|---|
| **+12V** | U201 TPS54308 VIN; U202 L78M05 VI; 4 × TL074H V+ (U302, U502, U503, U504); 2 × DG412 V+ (U402, U403); 2 × LM393 V+ (U801, U802). Caps: C201, C205 10 µF; C213 1 µF; 11 × 100 nF |
| **−12V** | 4 × TL074H V−, 2 × DG412 V−. Caps: C203 10 µF; 7 × 100 nF |
| **+5VD** | D203 → MOD_5V; XC6206 U204; DG412 VL ×2; 74HCT595 VCC and /SRCLR; AHCT1G125 VCC; 8 × BAV99 gate-out clamp cathodes; J704 WS2812 supply holes; J603 expansion. Caps: C209/C210 22 µF, C211 100 nF, C212 10 µF, C713 10 µF, C219 1 µF, 4 × 100 nF |
| **+5VA** | PCM3060 VCC; ADS8688 AVDD ×2; XC6206 U203; BAT54S audio-in clamps ×2. Caps: C215 10 µF, C216 100 nF, C301 10 µF, C302 100 nF, C401/C402 1 µF, C403 10 µF, C217 1 µF |
| **+3V3A** | DAC8568 AVDD and /CLR; MCP3208 VDD and VREF; POT_TOP holes. Caps: C218 10 µF, C501 10 µF, C601/C603 1 µF, 3 × 100 nF |
| **+3V3D** | PCM3060 VDD; ADS8688 DVDD; TCA9555; M24C64; Qwiic; I2C display holes; 5 × BAT54S (gate-in and probe clamps); about 20 pull-ups. Caps: C220, C303, C404 10 µF; 3 × 100 nF |
| **MOD_5V** | Pico 2 VSYS (pin 39), Teensy 4.1 VIN; C221 10 µF |

### Regulators
- **+5VD buck, U201 TPS54308DDCR** (C168839, Extended, 1,007 in stock): 350 kHz forced PWM (FCCM).
  - Input: C205 10 µF 50 V 1206 and C206 100 nF 50 V. EN pin 5 is not connected, so it floats on its internal pull-up.
  - BOOT: C207 100 nF 16 V 0402.
  - L201: 15 µH Sunlord SWPA5040S150MT (C44888, Extended; 112 mΩ, rated 2.3 A / 2 A per LCSC).
  - Output: C209/C210 22 µF 25 V X5R 1206 (C12891) and C211 100 nF.
  - Feedback: R201 15 kΩ / R202 2 kΩ → 0.596 × 8.5 = **5.07 V**. C208 47 pF C0G across R201 is DNP.
  - R203 0 Ω 0805 link, then +5VD (TP205).
  - Pinout checked against TI's pin table: 1 GND, 2 SW, 3 VIN, 4 FB, 5 EN, 6 BOOT.
- **+5VA, U202 L78M05ABDT** (C58069, Basic), DPAK: C213 1 µF 50 V + C214 100 nF in; C215 10 µF 25 V 0805 + C216 100 nF out; R204 0 Ω.
- **+3V3A, U203 XC6206P332MR** (C5446, Basic) from +5VA: C217 1 µF 25 V 0402 in; C218 10 µF 25 V 0805 out; R205 0 Ω.
- **+3V3D, U204 XC6206P332MR** from +5VD: same arrangement (C219, C220, R206).
- **MOD_5V**: +5VD → D203 SS14 → VSYS / VIN; C221 10 µF.

---

## 2. Reference designs, with evidence

### 2.1 Mutable Instruments Beads (read by me)
File `beads_v51.sch` (Eagle XML, pichenettes/eurorack @ f4cfa76), parsed for parts and nets.
Line numbers are the `<part>` definitions.

- **Entry:** JP1 is a 2×5 shrouded header (L16889). D1 and D2 are 1N5819HW in SOD-123 (L16880–1), in series.
- **Three branches after the diode on +12 V** (net N$40):
  - **L2** ferrite (Würth WE-CBF 0603 "1k@1MHz", L16882) → VCC: op-amps, C2 10 µF 0805.
  - **L5** ferrite → **R32 33 Ω 1206** (L16894) → C18 10 µF → **IC6 UA78M05** (L16937) → +5V_A.
  - **L12** ferrite → **L4 1 µH** (L16885) → C3/C4 2 × 10 µF → **IC1 MCP16311** buck (L16900), L3 15 µH, FB 31.6k/10k, giving +3V3 digital.
- **−12 V:** D2 → L1 ferrite → VEE, C1 10 µF.
- **Codec supplies:**
  - VCC: +5V_A → **L11 ferrite → C55 47 µF + C56 100 nF** → PCM3060 AVCC (L16789, L16993).
  - VDD: +5V_A → L6 ferrite → **R37 33 Ω** (L16961) → C16 10 µF → **IC5 LD2981ABU33** (L16959) → +3V3_A → **L7 ferrite → C59 47 µF + C58 100 nF** → PCM3060 DVDD (L16780–2).
- **The codec's digital supply comes from the analogue 5 V chain, not from the digital buck**, which is TI's recommendation (§4.6).

### 2.2 Mutable Instruments Plaits, Marbles, Rings, Clouds [sub-agent; official PDFs + BOM]
- 10-pin headers, with **1N5819HW** in series on each rail.
- Plaits and Marbles split the post-diode +12 V three ways, as Beads does:
  - a ferrite to the op-amp rail;
  - an **LC π-filter (22 µF – 33 µH – 22 µF) into an R-78E3.3 switcher**;
  - a separate ferrite into an **LD2981 analogue LDO**.
- Bulk is **22–47 µF electrolytic** per rail (EEE-FP1V220AR, at least 35 V).
- Rings and Clouds: LM1117-3.3 behind a 4.7 Ω series resistor. The analogue 3.3 V is either a second LDO or the digital rail through a ferrite.
- Converter AVDD is always on the analogue 3.3 V; DVDD on the digital rail.

### 2.3 Electrosmith Daisy Patch SM (sheet 3 read by me from the render)
`ES_Daisy_Patch_SM_Schematic.pdf` p.3 (Rev3-REDUCED, 2024-02-08):
- **Entry:** FB2 → D1 NSR1020MW2T3G → C13 **22 µF** + C32 100 nF → +12 V. −12 V is the same (FB1, D2, C25 22 µF, C33).
- **+3V3 digital buck:** +12 V → C27 10 µF → **FB3** → C26 10 µF → "TPS621X" VIN (EN tied to VIN); L2 2.2 µH; R36 470k / R37 150k; C28 10 µF.
- **+3V3_A** = +3V3_D → **FB5** with 10 µF on each side (C6/C39).
- **+5V ANALOG:** +12 V → C5 100 nF → **FB7** → C8 100 nF → **U8 LD1117-5V** → C7 10 µF → **FB8** → C9 10 µF.
- Datasheet v1.0.5, p.5: ±12 V inputs 6–17 V; 5 V out 800 mA; 3V3 500 mA [sub-agent].

### 2.4 patch.init carrier [sub-agent]
`patch_init_schematic.pdf` p.1. The header goes straight to the SM, with no parts on the carrier. The note
reads: "Reverse protection is implemented on the submodule… recommended to add your own reverse protection."

### 2.5 Daisy Seed2 DFM and Daisy Patch Rev8 [sub-agent]
- **Seed2 DFM (p.4):**
  - D1 NSR1020 → LD1117-5V → **FB8** → +5V ANALOG.
  - ST1S03 buck with **FB1 + C59 10 µF** on its input.
  - +3V3_A = +3V3_D through a ferrite.
- **Daisy Patch Rev8:**
  - FB → NSR1020 → 10 µF + 100 nF per rail.
  - LD1117-5V → **FB8** → C57 10 µF → +5V → PCM3060 **VCC** (C4 100 nF, C1 10 µF).
  - PCM3060 **VDD** = +3V3_D through **R19 5.1 Ω** with C3 100 nF + C2 10 µF.
  - So Electrosmith feeds the codec's VCC and VDD from separate sources, each with a series element.

### 2.6 4ms MP153 Brainboard and carriers [sub-agent]
- **`Kit-Brainboard.kicad_sch`:**
  - Three AP62301 bucks from +12 V. Schematic note: "-01Z6 disables PFM mode", i.e. **forced PWM**. They run at 750 kHz (Diodes datasheet).
  - The bucks' **EN pins are sequenced** from PWR_ON / PWR_ONRST.
  - Codec VCC comes from **V1 AP2120N-5.0 off +12 V**, with only C3 10 µF on +5VA and no ferrite. The sub-agent notes the AP2120's absolute maximum input is 6.5 V, so this may be a drawing error [unverified].
  - Codec VDD is on the +3V3 buck rail, unfiltered.
  - No ferrites anywhere.
- **Trig-Sampler carrier:** SB140 series diodes (1 A 40 V Schottky); C4/C5 **47 µF electrolytic** bulk; 10-pin header.
- **mp153 devboard carrier v0.4:** B140HW series diodes, 47 µF 16 V bulk; an AP62301 + 15 µH 5 V buck.

### 2.7 Befaco Lich, Oneiroi, Iroi [sub-agent]
- **Entry:** a ferrite **before** a 1N5817 Schottky on each rail; 10 µF electrolytic + 100 nF.
- **5 V:** an AMSR-7805 drop-in switcher module (Lich, Oneiroi) or a 78L05-type part (Iroi).
- **3.3 V:** from the OWL module, or a 78L33 (Iroi).

### 2.8 Music Thing Workshop System Computer Rev 1.0.0 [sub-agent]
`computer_Rev_1_0_0_Schematic.pdf` @ cced06a:
- **Entry and bulk:** 10-pin header; D3/D4 **5819** in series; C2/C15 **22 µF 35 V** bulk.
- **5 V:** **CJA1117B-5** (linear) from +12 V, with 10 µF ≥25 V + 100 nF in and out.
- **To the RP2040:** 5 V → **D9 5819 → VBUS**, diode-ORed with USB.
- **3.3 V:** RT9193-33 with a 22 nF noise-bypass cap; **R60 200 Ω + C12 10 µF RC** on ADC_AVDD.
- **Other:** no ferrites; a TL431 −5 V reference.

### 2.9 Allen Synthesis EuroPi, surface-mount [sub-agent]
`europi-surface-mount.kicad_sch` @ 85ee549:
- D1/D5 are **S2D standard rectifiers** (1.1 V at 2 A), not Schottky; C1/C2 10 µF 0805.
- U6 L7805 TO-252 from +12 V, with no input cap; C3 1 µF out.
- **D2 S2D: +5 V → Pico VSYS**, so VSYS ≈ 4 V and the Pico runs fine. The analogue stage uses the Pico's own 3V3.

### 2.10 Keeos Ogham (local repo @ 776e8d2) [sub-agent]
`power.kicad_sch`:
- **Entry:** **SS14 (C2480) → BLM18PG121 (C14709) → 10 µF 1210 X7R 50 V (C138687) + 100 nF** per rail.
  - L2380 note: "tantalum was over-derated on a 12V rail".
- **5 V logic:** L7805 TO-263 for logic only (display, gate buffer, comparator), with a **tantalum** 10 µF 16 V output cap for "controlled ESR".
- **Daisy Seed:** fed from +12 V through D8 SS14 (the Seed has its own buck).

### 2.11 Convention and platform documents
- **Doepfer A-100 technical details** (a100t_e.htm):
  - "applying other than the described voltages or changing the polarity will result in the module's instant destruction"
  - "the rule is 'red strip down'"
- **Doepfer installation** (a100m_e.htm): "First of all, take the A-100's plug out of the wall socket". There is no hot-plug support.
- **Doepfer PSU3** (a100z_e.htm): "the three voltages appear not exactly at the same time after power on".
- **Raspberry Pi Pico 2 datasheet §5.5** (local `pico2.txt` L693–720):
  - A second supply goes into VSYS "via another Schottky diode", or better "using a P-channel MOSFET (P-FET) to replace the Schottky diode … the gate of the FET is controlled by VBUS".
  - "a secondary Schottky diode across the P-FET (in the same direction as the body diode) is recommended".
  - Example part: DMG2305UX.
  - VSYS range 1.8–5.5 V (L363).

---

## 3. Comparison

| Design | Entry order, diode | Bulk per rail | Digital supply | Buck input isolation | Analogue 5 V | Codec / converter supply filtering |
|---|---|---|---|---|---|---|
| **Ours** | SS14 → ferrite | 10 µF 50 V X5R 1206 (≈4.3 µF at 12 V) | TPS54308 FCCM 350 kHz | **none, shares +12 V with op-amps and the 5 V LDO** | L78M05 | **none** (pin decoupling only) |
| Beads | 1N5819HW → ferrite | 10 µF 0805 | MCP16311 buck | ferrite + 1 µH + 2 × 10 µF | UA78M05 behind ferrite + 33 Ω | VCC ferrite + 47 µF; VDD from the analogue LDO, ferrite + 47 µF |
| Plaits / Marbles | 1N5819HW → ferrite | 22 µF electrolytic | R-78E3.3 switcher | LC π 22 µF–33 µH–22 µF | (LD2981 3.3 V via ferrite) | AVDD on its own analogue LDO |
| Patch SM | ferrite → NSR1020 | 22 µF | TPS621x buck | **ferrite FB3, 10 µF each side** | LD1117-5 with **ferrites before and after** | 3V3_A = 3V3_D via ferrite |
| Seed2 DFM | NSR1020 | — | ST1S03 buck | ferrite FB1 + 10 µF | LD1117-5 → ferrite | 3V3_A via ferrite |
| Daisy Patch Rev8 | ferrite → NSR1020 | 10 µF | isolated DC-DC; ST1S03 | FB5 + 10 µF each side | LD1117-5 → ferrite → codec VCC | **VDD via 5.1 Ω + 10 µF** |
| 4ms Brainboard (+ carrier) | SB140 / B140 | **47 µF electrolytic** | 3 × AP62301 **forced PWM**, EN-sequenced | none | AP2120 (no filter) | none |
| Befaco | ferrite → 1N5817 | 10 µF electrolytic | 7805 switcher module | — | (module) | (OWL module) |
| WSC | 5819 | 22 µF 35 V | linear CJA1117-5 | n/a | (5 V is digital) | RC 200 Ω + 10 µF on ADC AVDD |
| EuroPi | S2D (1.1 V) | 10 µF 0805 | L7805 | n/a | — | Pico 3V3 |
| Ogham | SS14 → BLM18 | 10 µF 1210 X7R 50 V | L7805 (logic only) | n/a | — | (Seed) |

Our entry (Schottky plus ferrite) and the forced-PWM buck are mainstream; Ogham is the closest
match. Where we stand alone is the last three columns: **no isolation between the buck and
the analogue +12 V, and no series element at the codec supply pins.**

---

## 4. Checks, by question

### 4.1 Reverse polarity, entry filtering, inrush, DC bias
- **Reverse polarity: right.**
  - A reversed 10-pin cable swaps pins 1–2 and 9–10, while GND (3–8) stays GND.
  - D201 and D202 then each see 12 V reverse and block, inside the SS14's 40 V rating.
  - The shrouded header stops an offset plug.
  - Every reference except patch.init (which relies on the SM) has a series diode. Ours, a Schottky, beats EuroPi's S2D: 0.45–0.52 V against about 1 V.
  - SS14 forward drop, from the MDD datasheet Fig. 3 at 25 °C: ≈0.45 V at 0.1 A, ≈0.50 V at 0.5 A, ≈0.52 V at 1 A [read from the curve]. The rating is 1 A, 25 A surge.
- **Ferrite: right.** BLM18PG121SN1D, 2 A and 50 mΩ, drops ≤35 mV at the worst-case 0.7 A.
  - Diode-then-ferrite (Ogham, Beads, MI) and ferrite-then-diode (Patch SM, Befaco, Daisy Patch) are both used.
- **Bulk derating.** Samsung's own curve for CL31A106KBHNNNE shows **−55 to −58 % at 12 V** (DC-bias plot, Samsung sheet dated 2013-09-10). Each 10 µF is ≈4.3 µF in use.
  - +12 V has ≈9–10 µF effective in total; −12 V ≈4.5 µF.
  - Comparison: WSC 22 µF 35 V; Patch SM 22 µF; MI 22–47 µF electrolytic; 4ms 47 µF electrolytic; Ogham 10 µF 1210 X7R.
  - Spec §10 says "X7R"; the schematic has X5R 1206. That is enough for our loads (op-amps ≈18 mA a rail), but see B1 and C1.
- **Inrush.** About 22 µF nominal on +12 V charges from a bus that can supply amps. The buck's 5 ms soft-start (TI p.5) limits +5VD inrush to C·dV/dt ≈ 70 µF × 1 V/ms ≈ 70 mA [est.]. No issue.
- **Hot-plug** is not supported in Eurorack (Doepfer). With all-ceramic input caps, plugging into a live bus can ring to about twice the step (LT AN-88).
  - Twice ±12 V would put ≈48 V across TL074H (absolute max 42 V, SLOS080W §5.1, p.10) and DG412 (V+ to V− 44 V, Vishay 61564 p.2).
  - See C2. This only matters if someone hot-plugs.

### 4.2 The buck
- **Choice: right.** Forced PWM keeps the switching at 255–445 kHz at every load (TI p.5 Fsw), above the audio band. 4ms made the same choice (AP62301 "-01Z6 disables PFM").
  - The TPS54202 fallback pulse-skips below about 300 mA peak inductor current (TPS54202 datasheet §6.3.2), which is exactly our load range.
  - **FCCM also sinks current**: low-side sink limit 1.75 A minimum (TI p.5). That matters because the eight BAV99 gate-out clamps return into +5VD; a pulse-skipping buck cannot absorb injected current.
- **Values against TI Table 7-2, 5 V row (p.18):** L 15 µH ✓; COUT 44 µF ✓ (2 × 22 µF 25 V; TI's example uses X7R, ours X5R); BOOT 0.1 µF ✓ (TI §7.2.3.3).
  - TI uses R2 100 kΩ / R3 13.3 kΩ; our 15k/2k sets the same ratio (5.07 V) and draws 0.3 mA, which is fine.
  - Crossover by TI eq. 14 ≈ 5.1/(5 V × ~30 µF effective) ≈ 34 kHz, under TI's 40 kHz guide [est.]. Downstream caps on +5VD lower it further.
- **Feed-forward cap (DNP C208).** TI's table pairs C6 75 pF with **R2 = 100 kΩ**, plus R6 2 kΩ in series.
  - With our R2 = 15 kΩ, 47 pF puts the zero at 226 kHz, far above crossover, so if fitted it would do almost nothing.
  - The equivalent value is ≈500 pF. See C3.
- **Input capacitance.** TI asks for "a ceramic capacitor over 10 µF" (§7.2.3.2, p.14). C205 is 10 µF nominal but ≈4.3 µF at 12 V.
  - TI also notes that a supply "more than a few inches" away may need "an electrolytic capacitor with a value of 47 µF" (§7.3, p.21).
- **Ripple onto the analogue +12 V [est.].** Today the buck's input ripple appears directly on the op-amp, DG412, LM393 and L78M05 rail.
  - By TI eq. 4: ΔV ≈ I·D(1−D)/(f·C) with D ≈ 0.44 and C ≈ 9 µF effective. That gives **≈15 mV p-p at 0.2 A and ≈75 mV p-p at 1 A**, at 350 kHz, plus switching-edge spikes.
  - TL074H PSRR is ≈40 dB at 100 kHz and ≈20 dB at 1 MHz (SLOS080W Fig. 5-14, p.19), so roughly 30 dB at 350 kHz.
  - The CV stages have a noise gain of 4, so that is **≈2–9 mV p-p of 350 kHz on CV outputs**. It is inaudible directly, but it is exactly what every reference isolates (§3). See B1.
- **EN floating: allowed.** TI: "Float the EN pin to enable" (pin table, p.3); "internal pullup current source" (§6.3.5).
  - But Ip is only 0.7 µA, the pin sits beside SW, and the EN divider has a second use (B2).
- **Layout (TI §7.4.1, p.21).**
  - Input cap and output caps tight to the pins, with vias. Short, wide SW.
  - "Do not allow switching current to flow under the device".
  - Separate VOUT sense to R201. Kelvin FB return to pin 1. FB node small and away from SW.
  - The generator already takes FB from 5V_BUCK, before R203 ✓.
  - The hot loop is C206/C205 → pin 3 → pin 1. Keep it within about 2 mm, and keep the buck and L201 at the far end from the codec, ADS8688 and DAC (spec §10 zoning ✓).
- **Load assumptions [est.].** +5VD ≈ module + +3V3D + logic + LEDs.
  - Teensy 0.10 A + 0.04 A + 0.01 A ≈ 0.15 A typical gives **+12 V ≈ 145 mA total typical** (spec says 120 mA).
  - With 10 WS2812 at full white (about 60 mA each, LED-dependent [unverified]) it is ≈0.48 A.
  - With the ESP32-P4 (0.45–0.7 A, `analogue_board_esp32p4.md`) plus LEDs it reaches ≈0.75 A.
  - The spec's "350 mA worst" holds only for a Teensy with a lit chain. Inductor peak at 1.4 A out is ≈1.7 A, under its 2 A rating. TPS54308 is rated 3 A ✓.
- **Stock:** LCSC has 1,007 TPS54308DDCR. That is fine for 2–5 boards, but reserve them.

### 4.3 +5VA from the L78M05
- **Load [est.]:** PCM3060 ICC 25 mA typ / 36 max (SLAS533B p.6); ADS8688 IAVDD 13/16 mA (SBAS582C p.10); +3V3A 2–5 mA; Id 6 mA. Total **≈46 mA typ, ≈63 mA max** drawn from ≈11.5 V.
- **Dissipation:** (11.5 − 5) × load ≈ **0.30 W typ, 0.41 W max**. DPAK RthJA 100 °C/W (ST DS0425 Table 2, p.5) gives a rise of ≈30–41 °C. With a 40 °C case, Tj ≈ 80 °C ✓.
  - A 4-layer board with copper on the tab does better. Rated 500 mA ✓.
- **Accuracy:** L78M05AB is 4.8–5.2 V over load, line and −40…125 °C (Table 4, p.8). That is within ADS8688 AVDD 4.75–5.25 V and PCM3060 VCC 4.5–5.5 V ✓.
- **Noise and PSRR:**
  - Noise: 40 µV, 10 Hz–100 kHz (p.8).
  - Supply rejection: 62 dB minimum at 120 Hz.
  - Fig. 12 (p.17): ≈78 dB to 1 kHz, ≈72 dB at 10 kHz, ≈58 dB at 100 kHz.
  - It is a good audio-band regulator, as Beads (UA78M05) and Electrosmith (LD1117-5) also use.
- **Caps:** ST asks for ≥0.33 µF in; the output cap is not needed for stability (p.18). Ours, 1 µF + 100 nF in and 10 µF + 100 nF out ✓.
- **Post-filtering in the references:** Beads (L11 + 47 µF), Patch SM (FB8), Seed2 DFM (FB8), Daisy Patch Rev8 (FB8 → codec VCC) and WSC (RC on ADC AVDD) all put a series element between the 5 V/3.3 V regulator and the converter supply. 4ms does not. **We do not.** See B3.
- **Pre-filtering in the references:** Beads (ferrite + 33 Ω + 10 µF) and Patch SM (FB7) filter ahead of the LDO; MI uses a ferrite. See C4.

### 4.4 XC6206 for +3V3A
- **PSRR:** poor. Torex Fig. 11 (p.12): XC6206P302 at 1 mA load is ≈40 dB at 100 Hz, ≈20 dB at 1 kHz and ≈16 dB at 3 kHz. No output-noise figure is given.
- **Why it is acceptable here:**
  - Its input is the quiet +5VA (40 µV).
  - The DAC8568 runs from its internal reference, whose line regulation is 10 µV/V (SBAS430F p.7 and §9.2.1.1.1.1), so AVDD noise barely reaches the output.
  - The MCP3208 reads pots fed from the same +3V3A, so rail noise is common to signal and reference (ratiometric).
  - The load is 2–5 mA (DAC8568 IDD 1.1–1.9 mA with the reference on, p.7).
- **10 µF output: allowed in practice.** Torex characterises with CL = 1 µF ceramic and says "compatible with low ESR ceramic capacitors". It **states no maximum** [datasheet silent]. Its foldback limit (≈400 mA, folding to ≈80 mA at short, Fig. 2 p.7) charges the ≈20–30 µF on each 3.3 V rail in about a millisecond ✓.
- **A better Basic LDO? No.** JLC's Basic 3.3 V LDOs are only AMS1117-3.3 (wants 22 µF tantalum), XC6206P332MR and HT7533-1.
  - The best Extended option is **LP5907MFX-3.3/NOPB, C80670** ($0.16 + $3.07 fee): < 6.5 µVrms, 82 dB at 1 kHz, VIN ≤ 5.5 V.
  - It allows **COUT only 0.7–10 µF** (TI LP5907, recommended operating conditions), so C218 and C501 would have to shrink. Not worth it for Rev A (C5).

### 4.5 MOD_5V margin

**+5VD range:**
- VFB is 0.581–0.611 V over temperature (TI p.5, "±2.5 %" §6.3.7). With 1 % resistors, **+5VD = 4.85–5.29 V, 5.07 V typical** [est.].

**At the module pin [est.], with the SS14 from MDD Fig. 3 and R203 ≤ 50 mΩ [unverified jumper spec]:**

| Module | Current | MOD_5V typ | MOD_5V worst | Needs | |
|---|---|---|---|---|---|
| Pico 2 | ~0.05 A | 4.62 V | 4.40 V | 1.8–5.5 V (Pico 2 DS L363) | ✓ |
| Teensy 4.1 | ~0.1 A | 4.61 V | 4.39 V | 3.6–5.5 V (PJRC, spec §5) | ✓ |
| ESP32-P4 | 0.45–0.7 A | 4.55 V | 4.30 V | ≥ 4.5 V (MP1658, `analogue_board_esp32p4.md`) | ✗ worst case, ~0.05 V typical margin |

**Every +5VD load against the 5.29 V worst-case maximum:**
- 74HCT595: 4.5–5.5 V (Nexperia, recommended) ✓
- 74AHCT1G125: 4.5–5.5 V (TI) ✓
- DG412 VL: absolute max (V+) + 0.3 V, characterised at 5 V ✓
- XC6206 VIN: ≤ 6.0 V ✓
- Pico VSYS ≤ 5.5 V ✓; Teensy VIN ≤ 5.5 V ✓
- **WS2812B VDD: +3.5 to +5.3 V** (Worldsemi, per third-party copies [unverified]). ✓, but with only 10 mV to spare.

**Options:**
- **Raising +5VD is a bad trade.** 5.2 V nominal reaches about 5.36 V at the worst corner, over the LED limit.
- **A P-FET across D203** (Pico 2 datasheet Fig. 9) gives ≈5.0 V typical and ≥4.78 V worst case at 0.6 A with an AO3401A (60 mΩ at −4.5 V). See B4.
- **A bigger Schottky** (SS54, C22452, Basic, same SMA footprint) would recover perhaps 0.1 V [unverified; MDD datasheet not retrievable].

### 4.6 Power-up sequencing (datasheet statements only)
**How the rails come up today:** +5VA follows +12 V as soon as +12 V passes about 7 V. The buck
starts at VIN 4.1 V (UVLO, TI p.5) and ramps +5VD over 5 ms. +3V3D follows +5VD. On power-down
the buck keeps going down to VIN 3.6 V, so **+5VD and +3V3D outlast +5VA** while +12 V falls
from about 5.3 V to 3.6 V.

| Hazard | Datasheet says | Today | With B2 (EN divider) |
|---|---|---|---|
| **PCM3060 VCC / VDD** | "using one common source, 5-V power supply for VCC and a 3.3-V power supply for VDD which is generated from the 5-V power supply for VCC, is recommended to avoid unexpected problems, such as latch-up, from incorrect power supply sequencing" (SLAS533B p.41). Absolute max: BCK/LRCK ≤ VDD + 0.3 V; ±10 mA on any pin (p.2) | Separate sources (+5VA vs +5VD → XC6206). Power-up: VCC first, mostly. **Power-down: VDD = 3.3 V while VCC collapses** | Buck starts at ≈9.2 V (VCC already regulating) and stops at ≈8.1 V (VCC still regulating). VDD comes up after VCC and goes down before it, for a normally decaying bus |
| **ADS8688 AVDD / DVDD** | "AVDD and DVDD can be independently set to any value within the permissible range" (SBAS582C p.57); DVDD range 1.65 V to **AVDD** (p.10); digital inputs ≤ DVDD + 0.3 V (p.6). No order is stated | DVDD > AVDD briefly at power-down: outside the recommended range, not an absolute-max violation | Fixed in the same way |
| **DG412 VL vs V+/V−** | VL absolute max (GND − 0.3) to **(V+) + 0.3 V**; S, D, IN within (V−) − 2 to (V+) + 2 V or 30 mA (Vishay 61564 p.2). No order is stated | VL = +5VD is derived from V+, so VL ≤ V+ except through the buck's high-side body diode when VIN collapses below VOUT (µA currents) [est.] | The buck stops at 8.1 V, so VL falls first ✓ |
| **Op-amps vs DAC8568** | The DAC powers up at zero scale with its internal reference off (SBAS430F §8.2.8) | OFFSET_REF = 0 V and DAC = 0 V give 0 V at the stage; the DG412 jack switches are held off by 4.7 kΩ pull-downs ✓ | — |
| **Op-amps vs codec** | Analogue pins ≤ VCC + 0.3 V; ±10 mA (p.2) | Audio-in op-amp → 1 kΩ → VIN, clamped by BAT54S to +5VA, so ≤ ≈7 mA even with ±12 V present ✓ | — |
| **ADS8688 inputs while unpowered** | ±20 V when AVDD is low-impedance (< 30 kΩ); ±11 V when floating (p.6 notes 2–3) | +5VA carries the L78M05 and other loads, so it counts as low-impedance [interpretation] ✓ | — |
| **Module vs board digital** | as above | Converter DVDD, VDD and the module all hang off +5VD, so they rise and fall together ✓. **USB-only power (rack off):** the module can drive I2S and SPI into an unpowered board | See B5 |

### 4.7 Decoupling, budget, thermals
- **Per-IC decoupling meets each datasheet:**
  - ADS8688: AVDD 10 µF + 1 µF, DVDD 10 µF (SBAS582C §10) ✓
  - PCM3060: 0.1 µF + 10 µF on each supply (p.41) ✓
  - DAC8568: 10 µF + 100 nF ✓
  - MCP3208: 1 µF + 100 nF on VDD and VREF ✓
  - Every TL074H, DG412 and LM393 supply pin has 100 nF ✓
- **Placement:** 100 nF within ~3 mm, a via to L2 at each pad (spec §10) ✓. Put the 10 µF bulk where the rail enters each block.

**Budget [est.]:**

| Rail | Typical | Maximum | Part rating | Dissipation |
|---|---|---|---|---|
| +12 V | ≈145 mA | ≈0.5 A (Teensy + 10 LEDs); ≈0.75 A (P4 + LEDs) | SS14 1 A, ferrite 2 A | SS14 ≤ 0.4 W |
| −12 V | ≈15 mA (TL074H 0.94 mA × 16) | ≈18 mA | | |
| +5VD | ≈0.15 A | ≈1.4 A | TPS54308 3 A; L201 2 A | ≈0.1–0.7 W |
| +5VA | 46 mA | 63 mA | 0.5 A | 0.30–0.41 W (DPAK) |
| +3V3A | 2–5 mA | | 200 mA | ≈0.01 W |
| +3V3D | ≈35 mA (codec VDD 9 mA, pull-ups, a small OLED) | ≈80 mA with a large OLED | 200 mA | 0.06–0.14 W in SOT-23 (Pd 250 mW at 25 °C) — tightest; keep Qwiic loads modest |

---

## 5. Findings

### A — must fix
**None found.** Pinouts were checked against the datasheets: TPS54308, L78M05 DPAK, XC6206
SOT-23, and the orientation of all three SS14. Every voltage and current rating above has margin
for the target modules.

### B — worth adopting before the order

**B1. Give the buck its own ferrite branch, and enough input capacitance.**
- **Change:** insert **FB203 BLM18PG121SN1D (C14709, Basic)** between +12V and a new net +12V_BUCK, which carries U201 VIN, C205 and C206. Add a second **10 µF 50 V 1206 (C13585, Basic)** on +12V_BUCK, beside C205.
- **Why:**
  - Every reference with a switcher isolates its input: Patch SM FB3 with 10 µF each side (verified by me), Seed2 DFM FB1 + 10 µF, Daisy Patch Rev8 FB5, Beads ferrite + 1 µH + 2 × 10 µF (verified by me), Plaits and Marbles LC π.
  - Today ≈15–75 mV p-p of 350 kHz ripple sits on the op-amp, DG412, LM393 and L78M05 rail. It reaches the CV outputs as a few mV p-p (§4.2) [est.], and switching-edge spikes go with it.
  - TI wants more than 10 µF of input ceramic; one X5R 1206 is ≈4.3 µF at 12 V (Samsung).
- **Expected effect [est.]:** about 20 dB less 350 kHz ripple on the analogue +12 V (the ferrite looks like ≈0.3–0.5 µH there [unverified]), and much more at the MHz edge harmonics.
- **Cost:** ≈$0.30 a board, Basic, no fee.
- **Side effects:** the ferrite drops ≤ 35 mV. The buck's own input ripple rises a little; at ≈80 mV p-p at 1 A it is well under TI's 400 mV example.

**B2. Set the buck's undervoltage lockout with an EN divider, to sequence the rails.**
- **Change:** R_EN1 **510 kΩ (C23192, 0603, Basic)** from VIN (+12V_BUCK) to EN; R_EN2 **75 kΩ (C23242, 0603, Basic)** from EN to GND.
  - By TI eqs. 1–2 (Ip 0.7 µA, Ih 1.55 µA, thresholds 1.22 / 1.19 V, p.10): **start ≈ 9.2 V (≤ 9.6 V), stop ≈ 8.1 V (≥ 7.4 V)** [est.].
  - Hysteresis ≈ 1 V; TI asks for more than 500 mV.
- **Why:**
  - The L78M05 needs about 7 V in. With the buck held off until 9.2 V and stopped at 8.1 V, **+5VA (codec VCC, ADS8688 AVDD) is always regulating while +5VD, +3V3D and the module are up**.
  - That gives the order TI recommends for the PCM3060 (p.41) and the ADS8688's DVDD ≤ AVDD range (p.10). It also keeps the DG412 at VL ≤ V+ (p.2).
  - It replaces a 0.7 µA floating node beside SW with ≈66 kΩ.
  - 4ms sequences its bucks through EN too. Beads gets the same order another way: its codec VDD comes from the analogue 5 V.
  - The TPS54202 fallback has the same Ip, Ih and thresholds (its datasheet, EN/UVLO section: Ip 0.7 µA, Ih 1.55 µA, 1.21 / 1.19 V), so the same resistors work.
- **Cost:** < $0.01, Basic.
- **Side effects:**
  - The module will not run below about 8 V on +12 V, which is out of Eurorack spec anyway.
  - A bench supply must give at least 9.6 V.
  - On a very fast bus collapse, the 55 µF on +5VD can still briefly outlast +5VA [est.].
- **Alternative (Beads):** feed PCM3060 VDD and ADS8688 DVDD from a third XC6206 on +5VA (≈10 mA). That guarantees the order, but the module, still on +5VD, would then drive I2S/SPI into converters whose digital supply has already gone. I prefer B2.

**B3. Put a series element at the codec supply pins.**
- **Change:**
  - **VCC:** BLM18PG121SN1D (C14709) from +5VA to PCM3060 VCC, keeping C301 10 µF + C302 100 nF on the codec side.
  - **VDD:** 5.1 Ω 0603 (**C25197**, Basic) from +3V3D to PCM3060 VDD, with C303 10 µF + C304 100 nF on the codec side.
  - Optional: a second ferrite for ADS8688 AVDD, so the SAR's conversion current does not modulate the codec's VCC.
- **Why:**
  - Beads uses a ferrite with 47 µF on both VCC and VDD.
  - Daisy Patch Rev8 uses a ferrite to VCC and **R19 5.1 Ω + 10 µF to VDD**. Patch SM and Seed2 DFM put ferrites after the LD1117. WSC puts an RC on its ADC AVDD.
  - The XC6206 passes almost all of the buck's ripple from +5VD to +3V3D (§4.4). The 5.1 Ω + 10 µF corner is ≈3 kHz, cutting 350 kHz by ≈40 dB [est.].
- **Cost:** ≈$0.02, Basic.
- **Side effects:**
  - VDD drops 46–61 mV (9–12 mA), leaving ≥ 3.17 V against a 2.7 V minimum ✓. The VCC ferrite drops ≈2 mV.
  - A ferrite with a low-loss MLCC can peak a few dB near ≈100 kHz [est.]. If that worries you, 2.2 Ω (≈80 mV drop, VCC ≥ 4.72 V) gives a damped RC instead.

**B4. MOD_5V: P-FET bypass for the ESP32-P4 (B if you will run the P4; otherwise C).**
- **Change:** add **AO3401A (C15127, Basic)** across D203, drain to +5VD and source to MOD_5V, so its body diode points the same way as D203. Keep D203: it is the "secondary Schottky across the P-FET" that Raspberry Pi recommends.
- **Gate:** the centre pad of a **3-pad solder jumper**.
  - Default bridge: gate to source (MOD_5V), so the FET is off and the board behaves exactly as today.
  - Alternate bridge: gate to Pico pin 40 (VBUS), which carries 100 kΩ to GND (**C25741**). The FET is then on unless USB is present.
- **Why:**
  - At 0.45–0.7 A the SS14 leaves the P4's 4.5 V minimum with about 0.05 V typical margin, and fails at the worst corner (§4.5).
  - The FET gives ≈5.0 V typical, ≥ 4.78 V worst.
  - This is the Pico 2 datasheet §5.5 Fig. 9 circuit.
  - Raising +5VD instead would push the worst case past the WS2812B's 5.3 V.
- **Why the jumper:**
  - With the FET permanently on, D203 no longer protects against a Teensy whose VIN–VUSB pads were not cut. USB and the buck would then be tied together.
  - Move the jumper to the VBUS side only for the Pico 2 or the P4. The Pico 2 pulls VBUS down when USB is absent (Pico 2 DS L648); for the P4 our 100 kΩ does it, and the P4's pin-40 behaviour is [unverified].
- **Cost:** ≈$0.11, Basic.

**B5. Firmware rule for USB-only power (free).**
- With the rack off and USB in, the board is unpowered (D203 blocks) but the module runs.
- Before starting MCLK, I2S or SPI, firmware should **probe the M24C64 at 0x50**. Its pull-ups (R720/R721 2.2 kΩ to +3V3D) hold the bus low when the board is unpowered, so the probe fails and firmware must keep those pins as inputs.
- **Why:** PCM3060 BCK/LRCK are limited to VDD + 0.3 V and ±10 mA (p.2); ADS8688 digital inputs to DVDD + 0.3 V (p.6). Driving them unpowered back-feeds +3V3D through ESD diodes.

### C — optional
- **C1. Entry bulk.** Add a second C13585 on +12 V and −12 V (≈8.6 µF effective each, Basic, $0.29 each). Or use CL32B106KBJNNNE 1210 X7R (C138687, Extended), as Ogham does. Either way, correct spec §10's "X7R" to match the part.
- **C2. Hot-plug damping.** A 47 µF 25–35 V electrolytic per rail, as the 4ms carrier and MI do (AN-88). JLC has **no Basic aluminium electrolytic**, so it costs one Extended fee ($3.07). It is only needed if anyone plugs in live, which Doepfer rules out.
- **C3. Feed-forward value.** Change DNP C208 from 47 pF to **470 pF (C1620, 0603 X7R, Basic) in series with 2 kΩ (C4109)**. That is TI's 75 pF / 2 kΩ scaled to R2 = 15 kΩ. Fit it only if load steps ring. Do not move to TI's 100k/13k: 13.3 kΩ is not Basic, and 13 kΩ gives 5.18 V (WS2812 limit).
- **C4. Pre-filter the L78M05.** 10 Ω 0805 (**C17415**) in series, and make C213 a 10 µF 50 V 1206 (C13585). That forms an RC at ≈3.7 kHz, as Beads does with 33 Ω + 10 µF.
  - It moves ≈20–40 mW out of U202 and leaves VI ≈ 10.9 V, above the ≈7 V needed. Largely redundant if B1 is done.
- **C5. Lower-noise +3V3A.** LP5907MFX-3.3/NOPB (C80670, Extended) with COUT kept at ≤ 10 µF total. Not needed for this load (§4.4).
- **C6. Inductor versus current limit.** L201 is rated about 2 A; the TPS54308's high-side limit is 4–5.9 A (p.5). On a hard short the inductor saturates before the limit acts, and hiccup mode (32768-cycle wait) protects. That is acceptable. A 3 A-rated 15 µH would be cleaner but Extended.
- **C7. TPS54308 stock** is 1,007 at LCSC: reserve parts with the order. Keep the TPS54202 only as a footprint fallback, since it pulse-skips and cannot sink current.
- **C8. +12 V budget.** Update spec §8. Typical ≈145 mA; up to ≈0.5 A with a lit 10-LED chain, ≈0.75 A with the P4 [est.]. Document the LED count the board supports.

### Already right, and why
- **Rail entry:** a series Schottky on each rail plus a ferrite, the same practice as Ogham, MI, Beads and Befaco. The SS14 drop beats EuroPi's S2D, and the shrouded 2×5 header has pin 1 = −12 V.
- **Buck:** forced PWM, as 4ms chose. It can sink the BAV99 clamp current. L and COUT match TI's 5 V row; BOOT 100 nF; EN floating is allowed by TI; the feedback is sensed before the 0 Ω link.
- **Regulator mix:** a linear L78M05 for analogue 5 V (Beads, Patch SM, WSC), a separate analogue 3.3 V LDO from it (Beads, MI), and digital and analogue 5 V kept apart (the spec's own comb-noise lesson).
- **Accuracy:** L78M05AB tolerance fits ADS8688 AVDD 4.75–5.25 V.
- **Dissipation:** within limits on every regulator.
- **Decoupling:** each IC's decoupling meets its datasheet.
- **Test and isolation:** 0 Ω links and test pads on every rail; none of the references has them.
- **Grounding:** one GND net and plane, as in every reference.
- **D203:** fine for both target modules. EuroPi runs a Pico through a 1 V diode.

---

## 6. Sources

**Datasheets**
- TI TPS54308, SLUSCV2B (rev. Aug 2026): https://www.ti.com/lit/ds/symlink/tps54308.pdf. Pin table p.3; absolute max and electrical p.4–5; §6.3.5 EN/UVLO p.9–10; §7.2 and Table 7-2 p.13–18; §7.3–7.4 p.21.
- TI TPS54202: https://www.ti.com/lit/ds/symlink/tps54202.pdf. §6.3.2 pulse skip; EN constants.
- ST L78M, DS0425 Rev 24: https://www.st.com/resource/en/datasheet/l78m.pdf. Table 2 p.5; Table 4 p.8; Fig. 12 p.17; §7.1 p.18.
- Torex XC6206, ETR0305_004b: https://www.torexsemi.com/file/xc6206/XC6206.pdf. Absolute max p.3; test circuit p.6; current limit p.7; ripple rejection p.12.
- TI PCM3060, SLAS533B: https://www.ti.com/lit/ds/symlink/pcm3060.pdf. Absolute max p.2; supply p.6; power-on reset p.16; supply recommendation p.41.
- TI ADS8688, SBAS582C: https://www.ti.com/lit/ds/symlink/ads8688.pdf. Absolute max p.6; supplies p.10; §10 p.57.
- TI DAC8568, SBAS430F: https://www.ti.com/lit/ds/symlink/dac8568.pdf. Reference and IDD p.6–7; §8.2.8 power-on reset.
- Vishay DG411/412/413, doc 61564 rev B: https://www.vishay.com/docs/61564/dg411.pdf. Absolute max p.2.
- TI TL07xH, SLOS080W: https://www.ti.com/lit/ds/symlink/tl074h.pdf. Absolute max §5.1; IQ; Fig. 5-14 p.19.
- onsemi LM393: https://www.onsemi.com/pdf/datasheet/lm393-d.pdf (ICC).
- MDD SS14 (LCSC C2480): https://www.lcsc.com/datasheet/lcsc_datasheet_2407101109_MDD-Microdiode-Semiconductor-SS14_C2480.pdf. Fig. 3 p.2.
- Nexperia 74HC_HCT595: https://assets.nexperia.com/documents/data-sheet/74HC_HCT595.pdf
- TI SN74AHCT1G125: https://www.ti.com/lit/ds/symlink/sn74ahct1g125.pdf
- Raspberry Pi Pico 2 datasheet §5.5: https://datasheets.raspberrypi.com/pico/pico-2-datasheet.pdf
- TI LP5907: https://www.ti.com/lit/ds/symlink/lp5907.pdf
- Samsung CL31A106KBHNNNE characteristic sheet, 2013-09-10: https://store.comet.bg/download-file.php?id=8562
- WS2812B, Worldsemi (third-party copies, not opened by me) [unverified]: https://www.triopak.fi/files/product/Worldsemi/WS2812B.pdf and https://www.cl.cam.ac.uk/teaching/1516/ECAD+Arch/files/pcb/WS2812B.pdf
- LT Application Note 88, "Ceramic Input Capacitors Can Cause Overvoltage Transients" (not opened by me; summary via search): https://www.analog.com/media/en/technical-documentation/application-notes/an88f.pdf
- Diodes AP62300/AP62301 and AP2120 datasheets [sub-agent].

**Reference designs**
- Mutable Instruments Beads, `beads/hardware_design/pcb/beads_v51.sch` @ f4cfa76: https://github.com/pichenettes/eurorack/tree/master/beads/hardware_design
- MI Plaits v50, Marbles v70, Rings v30, Clouds v30 (official PDFs + BOMs): https://github.com/pichenettes/eurorack
- Electrosmith Patch SM schematic (Rev3-REDUCED), Patch SM datasheet v1.0.5, Seed2 DFM Rev5, Daisy Patch Rev8: https://docs.daisy.audio/hardware/
- patch.init carrier: `/Users/dbaghurst/GitHub/eurorack_daisy_patch_init/patch_init_schematic.pdf`
- 4ms: https://github.com/4ms/mp153-brainboard-pcb @ 2f914ef (`pcb-p6/Kit-Brainboard.kicad_sch`); pcb-Kit-Trig-Sampler v1.0-kit; https://github.com/4ms/mp153-devboard @ 8ab17e3
- Befaco: https://befaco.org/docs/Lich/Lich_V1_sch.pdf, https://befaco.org/docs/Oneiroi/Oneiroi_0_1_THT.pdf, https://befaco.org/docs/Iroi/Iroi_V1_THT_Schematic.pdf
- Music Thing Workshop System Computer Rev 1.0.0: https://raw.githubusercontent.com/TomWhitwell/Workshop_Computer/cced06aa398364adb2a5d6ae13fb8c2293eb9974/documentation/computer_Rev_1_0_0_Schematic.pdf
- Allen Synthesis EuroPi SMT @ 85ee549: https://github.com/Allen-Synthesis/EuroPi/tree/main/hardware/surface-mount
- Keeos Ogham `ogham-merged-v1.0` @ 776e8d2: `/Users/dbaghurst/GitHub/ogham/hardware/`

**Convention**
- Doepfer A-100: https://www.doepfer.de/a100_man/a100t_e.htm, https://www.doepfer.de/a100_man/a100m_e.htm, https://doepfer.de/a100z_e.htm

**Parts:** JLCPCB parts API (`selectSmtComponentList`), queried 2026-10-15. Basic LDO and electrolytic
searches the same way. Rail loads summed from the schematic netlist by script (not kept).

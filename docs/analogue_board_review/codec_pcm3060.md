# PCM3060 analogue front ends: a survey of published designs

Compiled 2026-10-15. Every value below was read from the design file named beside it,
not from memory. Eagle `.sch` files were parsed as XML (parts and `<pinref>` nets);
KiCad netlists were parsed as S-expressions; PDFs were read as text and, where the
text layer was not enough, rendered and inspected. Items marked **[unverified]** are
inferences or second-hand claims that no published file confirms.

Source files were downloaded for this review and are not kept in the repo; every claim
cites the original file, line or page so it can be re-checked at the source.

Filter maths: multiple-feedback (MFB) low-pass with R1 input, R2 feedback, R3 into
the op-amp input, C1 node-to-ground and C2 op-amp input-to-output:
`f0 = 1/(2π√(R2·R3·C1·C2))`, `Q = √(R2·R3·C1·C2) / (C2·(R2 + R3 + R2·R3/R1))`,
`G = −R2/R1`. A capacitor `Cd` across the two nodes of a balanced MFB counts as
`C1 = 2·Cd`. Checked against TI's own Figure 34b: this method gives G 0.75,
f0 54.0 kHz and Q 0.70, which is what TI states.

---

## 0. The baseline: TI's datasheet (SLAS533B, March 2008)

File: TI PCM3060 datasheet, https://www.ti.com/lit/ds/symlink/pcm3060.pdf

| Item | Value | Page |
|---|---|---|
| MODE pin | tie to DGND = I²C; **220 kΩ to DGND = H/W, differential VOUT**; 220 kΩ to VDD = H/W, single-ended; tie to VDD = SPI. 220 kΩ must be ±5 %. Sampled at power-on or external reset only | 24 |
| H/W pins | FMT low = 24-bit I²S, high = 24-bit left-justified; IFMD low = ADC and DAC slave, high = ADC master 256 fS; DEMP low = off | 24 |
| S/W output config | Register 64 bit 0 `S/E`: 0 = differential (**default**), 1 = single-ended | 31 |
| ADC input | single-ended, full scale 0.6 VCC Vpp, centre 0.5 VCC, 10 kΩ typ. input impedance, on-chip anti-alias −3 dB at 300 kHz | 3, 23 |
| ADC digital HPF | −3 dB at 0.019 fS/1000 (0.91 Hz at 48 kHz). In S/W mode it can be bypassed (Reg 73 `BYP`, default 0 = HPF on). In H/W mode no pin controls it, so it stays at the default and is always on (my inference) | 4, 38 |
| DAC output | 0.8 VCC Vpp single-ended, 1.6 VCC Vpp differential; centre 0.5 VCC; min. load 10 kΩ DC-coupled / 5 kΩ AC-coupled; on-chip RC filter −3 dB at 300 kHz, "not enough to attenuate the out-of-band noise ... for many applications" | 4, 23 |
| DAC bipolar zero error | single-ended ±1 % FSR typ, ±2 % max; **differential ±1 % FSR typ** (about 80 mV on 8 Vpp) | 4 |
| Dynamic range (A-wtd, 48 kHz) | ADC 99 dB; DAC 103 dB single-ended, 104 dB differential | 4, 5 |
| Spec footnote 11 | differential figures assume a "10-kΩ DC-coupled second-order LPF and 115-dB or higher-performance differential to single-ended converter" | 5 |
| VCOM | 0.5 VCC, unbuffered, 12.5 kΩ output impedance (7 to 18 kΩ), ±1 µA allowable load; decouple 0.1 µF + 10 µF | 3, 23, 39 |
| Reset | H/W mode: internal reset released 1024 SCKI after power-on if RST high. During reset or power-save, VOUT are forced to VCOM with a fade | 16 |
| Fig. 33 | typical connection: VCC 5 V, VDD 3.3 V, 4.7 µF on VINL/VINR "for 3-Hz cutoff" | 39 |

**Fig. 34 (page 40), TI's three application circuits:**

- **(a) Input:** C1 10 µF → R1 20 kΩ into an inverting op-amp, R2 10 kΩ ∥ C2 330 pF
  feedback, + input on VCOM (C3 0.1 µF), R3 1 kΩ to VIN. G 0.5, fC 48 kHz, captioned
  "VCOM-biased buffering for 2-Vrms input with overvoltage protection". Your input stage
  is this circuit with the gain changed.
- **(b) Output:** "capless differential to single-ended converter with LPF": balanced
  second-order MFB, R1/R2 10 kΩ, R3/R4 7.5 kΩ, R5/R6 820 Ω, C1 1500 pF across the two
  nodes, C2/C3 470 pF, R7 100 Ω out. G 0.75, fC 54 kHz.
- **(c) Output:** single-supply single-ended version: VOUT+ and VCOM into an MFB (R1 10 kΩ,
  R2 7.5 kΩ, R3 750 Ω, C1 3300 pF, C2 470 pF), C4 10 µF output coupling, and a mute
  transistor driven from ZEROx or a mute line. G 0.75, fC 54 kHz.

---

## 1. Mutable Instruments Beads (direct PCM3060)

**Licence and files.** Hardware CC-BY-SA 3.0, STM32 code MIT (`README.md` lines 33–40,
pichenettes/eurorack @ `f4cfa76`). Schematic `beads/hardware_design/pcb/beads_v51.sch`
(Eagle XML; line numbers below are the `<part>` definitions). Driver
`beads/drivers/codec.cc`.

**Control mode.** Hardware mode, differential: IC7 PCM3060 (line 16913) `MODE` → R48
220 kΩ (0402, line 16924) → GND. `MC/SCL/FMT`, `MD/SDA/DEMP` and `MS/ADR/IFMD` all tied
to GND, so 24-bit I²S, codec slave for ADC and DAC, de-emphasis off. This is exactly
your strap. The driver has no I²C (`codec.cc` 84–101); the STM32H743's SAI1 block A is
master transmitter (`SAI_MODEMASTER_TX`, line 108) with block B a synchronous slave
receiver (128), both `SAI_I2S_STANDARD` with 32-bit slots (119–122, 135–138).
**SCKI** (MCLK1 and MCLK2 joined) is the STM32's `PE2/SAI1_MCLK_A` through R47 100 Ω;
BCK and LRCK also go through 100 Ω series resistors (R89, R95). **RST** is driven by
`PC13` with R49 10 kΩ pull-down (line 16763), so the codec stays in reset until the
firmware releases it (`codec.cc` 229–230) and is put back in reset on `Stop()` (277–278).

**ADC input stage** (left; right is identical with R74/R72/C44/C51/R70/R69/C39/C29):

1. Jack J7 tip → R78 100 kΩ to GND (input impedance, line 16758) and D13 16 V TVS to GND
   (16756).
2. **Unity-gain Sallen-Key low-pass** in IC10A NJM2068 (16964): R73 12 kΩ (16738) → R71
   8.2 kΩ (16934) → +IN, with C49 330 pF to GND (16942) and C43 680 pF from the R73/R71
   junction to the output (16740). f0 33.9 kHz, Q 0.71 (Butterworth). Non-inverting.
3. **Passive divider and third pole:** R68 10 kΩ (16741) to node N$47, R67 2.0 kΩ to GND
   (16743), C38 1.2 nF to GND (16977).
4. **AC coupling:** C28 10 µF (0603, 16749) into VINL. Bias comes from the codec's own
   10 kΩ to VCOM; nothing external touches VCOM except decoupling.

Gain: R67 ∥ 10 kΩ (VIN) = 1.67 kΩ against R68 10 kΩ gives **0.143 (1/7)**, so 3 Vpp at
VIN is **21 Vpp at the jack**. The divider leans on the codec's untrimmed internal 10 kΩ,
so the analogue gain carries that tolerance. Third pole: Thevenin 1.43 kΩ with 1.2 nF,
92.8 kHz. High-pass: 10 µF into about 11.4 kΩ, 1.4 Hz. Overall a third-order
anti-alias filter. No clamp at VIN: after the 1/7 divider, even a rail-to-rail op-amp
output (about ±11 V) only reaches VCOM ± 1.6 V, inside the 0–5 V pin range, so none is
needed. The firmware adds +0 to +32 dB of digital gain with automatic gain control and a
limiter (manual, below), so the analogue path is set for the loudest signals and the
gain is made up digitally.

**DAC output stage** (left; right uses R50/R51/R55/R57/R59/R61/C34/C32/C40/R77):
a **balanced second-order MFB low-pass**, the same topology as TI Fig. 34b with gain:

- VOUTL+ → R53 12 kΩ (16914) → node N$39 → R56 1.0 kΩ (16765) → IC9A −IN; R54 30 kΩ
  (16767) N$39 → output; C31 220 pF (16764) −IN → output.
- VOUTL− → R52 12 kΩ (16915) → node N$35 → R58 1.0 kΩ (16916) → IC9A +IN; R60 30 kΩ
  (16917) N$35 → GND; C37 220 pF (16938) +IN → GND.
- C35 2.2 nF (16944) across N$39 and N$35 (the differential cap).
- Output → R76 1.0 kΩ (0603, 16768) → jack J11; D10 16 V TVS to GND at the jack (16770).

Gain −30/12 = **2.5**, **f0 29.5 kHz, Q 0.73** (about −0.6 dB at 20 kHz). DC-coupled:
both VOUT pins sit at VCOM, so the difference is 0 V. Full scale 8 Vpp × 2.5 =
**20 Vpp at the jack**. The firmware drives the full 32-bit range (`beads.cc` 264–273:
clamp to ±1.0, × 2³¹). VOUT+ goes to the inverting side, so the jack is inverted
relative to the sample sign and the firmware does not compensate (harmless for audio).

**Supplies.** VCC (AVCC) = +5V_A from IC6 UA78M05 (`technology="05"`, line 16937), fed
from +12 V via D1 1N5819, a ferrite and R32 33 Ω, then ferrite L11 into AVCC with C55
47 µF + C56 100 nF. VDD = +3V3_A from IC5 LD2981ABU33 (16959), fed from +5V_A through a
ferrite and R37 33 Ω, then ferrite L7 with C59 47 µF + C58 100 nF. Digital 3.3 V is a
separate MCP16311 buck. **VCOM:** C53 100 nF + C54 47 µF to GND (16779, 16778), not used
outside the chip. Op-amp rails: ±12 V after 1N5819 reverse-protection diodes and
ferrites (about ±11.7 V).

**Notable.**
- **Op-amps:** NJM2068 (low-noise audio dual) for both audio paths; the library symbol is
  a TL072 with value NJM2068.
- **Passive mono mix:** J12 (R out) has its switch contact tied to the L output net, so
  with R unpatched both op-amps drive the L jack through their 1 kΩ resistors (passive
  sum, 500 Ω source). The manual confirms: "If the R output is left unpatched, both L and
  R signals are summed together and sent to the L output."
- **Normalisation probe:** the input jacks' switch contacts go through 1 MΩ (R85/R86) to a
  `NORMALIZATION_PROBE` GPIO, so the firmware knows which inputs are patched (mono or
  stereo operation).
- **Mute:** no hardware mute. The codec is held in reset (outputs at VCOM, i.e. 0 V
  differential) until the clocks run, and the firmware writes silence for 1/4 s after
  every codec (re)start (`codec_transition_frames = kBlockRate / 4`, `beads.cc` 292,
  169–176).
- Manual (pichenettes.github.io/mutable-instruments-documentation/modules/beads/manual/):
  input gain "+0dB to +32dB" set automatically, with a limiter; no analogue level or
  impedance spec is published.

---

## 2. Keeos Ogham (PCM3060 via Daisy Seed: codec not visible)

**Licence and files.** Hardware and docs CC BY-SA 4.0, firmware MIT (`LICENSE.md`).
KiCad 10 schematic `hardware/ogham-merged-v1.0/` (`audio.kicad_sch`, sheet "Audio");
read via the exported netlist `ogham-merged-v1.0.net`. Local repo at commit `776e8d2`.

**Codec.** On the Seed, so not in Ogham's schematic. Which Seed is fitted is
inconsistent across the repo: the parts list says "Daisy Seed (Rev 4)"
(`hardware/README.md` 151); the symbol is KiCad's stock `Electrosmith_Daisy_Seed_Rev4`
(`mcu.kicad_sch` 169); the 3D model is `ES_Daisy_Seed_Rev7-1.step` (README 48); and
`docs/BUILDING.md` mentions a USB-C "Seed3". The Seed datasheet's revision table
(Electrosmith `Daisy_Seed_datasheet.pdf` PDF p.16) gives **Rev 4 = AK4556, Rev 5 =
WM8731, Rev 7 (2023 on) = PCM3060**. The newer USB-C Seed3 uses a TI TAC5242
(Seed3 datasheet, per the Electrosmith subagent; not opened by me). So Ogham has a
PCM3060 only if a **Rev7** Seed is fitted. Seeds sold from 2023 until the Seed3 are
Rev7, and so is the 3D model, so that is likely. But **the repo never names the codec
[unverified]**. A Seed3-built Ogham would not be a PCM3060 design at all.
The Rev7 Seed runs its PCM3060 in H/W mode, single-ended, at VCC 4.5 V, with
on-module AC coupling (§4C). That predicts 0.8 × 4.5 = **3.6 Vpp** at the Seed pin.
The measured 4.15 Vpp (below) is about 15 % high, more than the codec's ±6 % maximum
gain error, but it was extrapolated from a 0.37× reading, so treat it as approximate.

**ADC input.** None: Seed pins 16/17 `AUDIO_IN_1/2` are unconnected (netlist
`unconnected-(A1-AUDIO_IN_1-Pad16)`).

**DAC output** (Out 1; Out 2 is R_FILT2/C_FILT2/R_G2/R_F1/R_OUT2):
Seed pin 18 `AUDIO_OUT_1` → R_FILT1 470 Ω (`audio.kicad_sch` line 1946) → C_FILT1
2.2 nF to GND (2810; RC pole 154 kHz) → U7A TL072 (3981) **non-inverting**, R_F2 10 kΩ
(2160) / R_G1 2.7 kΩ (2378), gain **4.70** → R_OUT1 1 kΩ (2596) → J_out1. TL072 on ±12 V (C_TL1/C_TL2 100 nF). No coupling cap on the carrier; the manual
calls the audio outputs "AC-coupled" (`docs/ogham-manual.pdf`, PDF p. 8, one-shots
note, and PDF p. 18, CV Out note). That matches the Rev7 Seed's own C64 4.7 µF / R29
47 kΩ / R30 100 Ω output network (§4C), giving a 0.7 Hz high-pass. Single-ended,
first-order: the Seed's 100 Ω plus R_FILT1 470 Ω against C_FILT1 2.2 nF puts the pole
at about 127 kHz.

**Measured level** (`firmware/src/ogham_main.cpp` 426–430): "The analog TL072 stage
(4.7x, as designed) is ~2x over-gained: full-scale is ~19.5Vpp (measured via a
full-scale square: 7.2Vpp at 0.37x -> 19.5 at 1.0x, un-clipped) vs the ~10Vpp Eurorack
level", fixed in firmware with `AUDIO_OUT_LEVEL = 0.51f`. 19.5 / 4.70 = **4.15 Vpp at
the Seed pin**, which is the "~4 Vpp single-ended" figure. Firmware also notes the codec
clock is 213 ppm fast (`SR_CORRECTION`, 385–388).

**Supplies.** Seed VIN (pin 39) on +5 V from U2 L7805; LM4040-5.0 reference for the CV
side. Codec VCC and VDD are on the Seed.

---

## 3. libDaisy (how Electrosmith configures the PCM3060)

On-disk libDaisy `f044cdc3`, under `eurorack_daisy_patch_init/deps/daisy/libDaisy/`.

- **Board detection** (`src/daisy_seed.cpp` 341–363): PD3 low = Seed 1.1 (WM8731, I²C);
  PD4 low = **Seed 2 DFM (PCM3060)**; otherwise original Seed rev4 (AK4556). The enum
  comment (`daisy_seed.h` 166–169) says the 2 DFM has "an improved audio codec
  (PCM3060)". The **Seed Rev7 (PCM3060)** has no branch of its own. The Seed datasheet
  explains why (printed p.13, PDF p.16): "Rev4/Rev7 do not use I2C pins. Auto-software
  detects hardware as Rev 4 Daisy in libDaisy, so it can remain backwards compatible".
  Rev7 runs through the AK4556 path, which only toggles PB11 (`daisy_seed.cpp` 303–315).
- **Seed 2 DFM** (`daisy_seed.cpp` 290–301): **no I²C at all**, so hardware mode; the
  only codec pin the MCU touches is PB11, driven low as "PCM3060 disable deemphasis pin".
  SAI1: block A master transmit on PE6, block B slave receive on PE3, MCLK on PE2
  (256–264), 48 kHz, 24-bit.
- **Patch SM** (`src/daisy_patch_sm.cpp` 268–291): **I²C mode** (I2C_2 at 400 kHz,
  PB10/PB11), so MODE must be tied to DGND. `Pcm3060::Init` (`src/dev/codec_pcm3060.cpp`
  47–97) uses address 0x46, pulses MRST and SRST, sets FMT1 and FMT2 = 01 (24-bit
  **left-justified**, despite the header saying I²S), and clears ADPSV/DAPSV. It never
  writes `S/E` (Reg 64 bit 0), so the **DAC stays differential** (default), and it never
  writes `BYP`, so **the ADC's digital high-pass (0.91 Hz at 48 kHz) stays on**. The SAI
  side matches: 24-bit selects `SAI_I2S_MSBJUSTIFIED` (`src/per/sai.cpp` 160–161).
  SAI1 block A receive (PE6), block B transmit (PE3), MCLK PE2.
- Consequence for the Seeds: libDaisy's 24-bit SAI is MSB-justified, so a
  hardware-mode PCM3060 must have FMT strapped high (left-justified). The Seed Rev7
  datasheet confirms this ("24-bit left-justified", §4C), and so does the Daisy Patch
  Rev8 (R77 4.7 kΩ pull-up, §4D). The Seed 2 DFM's codec sheet is not published, so its
  FMT strap is **[unverified]**. Your design straps FMT low (I²S), which is right if the
  ESP32-P4 I2S peripheral is set to standard Philips I²S.
- Consequence for your patch.init notes (`daisy_neural/CLAUDE.md` lists the audio-input
  high-pass corner as unknown): the Patch SM schematic has C2/C31 2.2 µF into 66.5 kΩ
  (1.09 Hz, §4A), and libDaisy leaves the codec's 0.91 Hz digital HPF on. The two first-
  order high-passes in cascade predict **−3 dB at about 1.56 Hz**, before capacitor
  tolerance. In stock firmware the inputs cannot pass DC.

**patch.init carrier** (`eurorack_daisy_patch_init/patch_init_schematic.pdf`,
`ES_Daisy_Patch_SM_Init_Rev1`, 2021-09-10, one sheet, no licence printed): J_LIN/J_RIN
go straight to SM pins B4/B3 (`AUDIO_IN_L/R`) and J_LOUT/J_ROUT straight to B2/B1. No
resistors, capacitors or op-amps on the carrier, so every audio conditioning part is on
the SM. J_RIN's normal contact carries SIG_LIN (R in normalled to L in).

---

## 4. Electrosmith (Daisy)

Electrosmith's GitHub org is now `daisyaudio` (`electro-smith` no longer resolves). It
has no hardware repo. Schematics and datasheets are PDFs on
`daisy.nyc3.cdn.digitaloceanspaces.com/products/...`, linked from
docs.daisy.audio/hardware.
**Licence: none printed on any schematic PDF.** The Patch SM and Seed2 DFM datasheets
carry an MIT-style "Copyright (c) 2021 Electrosmith" notice that covers "software and
associated documentation files", so it is unclear whether it covers hardware. Module
schematics are "REDUCED" and leave out the codec sheet. A forum post explains why
(andrewikenberry, community.daisy.audio, 5 Feb 2024): "we will not be providing all of the
information required to clone the existing Seed". The Seed3 and its dev kits use a TI
TAC5242, not the PCM3060, so they are excluded.

### 4A. Daisy Patch Submodule (Patch SM): the closest published design to yours

Files: `ES_Daisy_Patch_SM_Schematic.pdf` ("ES_Daisy_Patch_SM_Rev3-REDUCED", 2024-02-08,
4 sheets, audio on sheet 2) and `ES_Patch_SM_datasheet_v1.0.5.pdf`. I read the input
and left-output stages from the rendered sheet 2 myself (`img/psm_in-2.png`,
`img/psm_outL-2.png`).

- **Control mode:** I²C (libDaisy, §3), so MODE is tied to DGND **[inferred: codec sheet
  not published]**. Format is 24-bit left-justified, the codec is slave, and the MCU's SAI1
  MCLK (PE2) feeds SCKI. `S/E` is left at its default, so the outputs are differential,
  and the schematic does use both VOUT pins.
- **ADC input** (U12D left, U12C right, TL074 on ±12 V): INPUT_AUDIO_LEFT → C2 2.2 µF →
  R24 66.5 kΩ → **inverting**, feedback R46 15 kΩ ∥ C73 220 pF, + input on CODEC_VCOM
  with **C69 100 nF to GND at the op-amp pin** → R50 1 kΩ → CODEC_IN_L. Gain −15/66.5 =
  −0.226, or −0.205 once the 1 kΩ works against VIN's 10 kΩ. **Full scale ≈ 14.6 Vpp**
  (±7.3 V) at VCC 5 V. HPF 1.09 Hz, LPF 48.2 kHz (first order). Input impedance 66.5 kΩ.
  Per the subagent, the datasheet says "100K", which disagrees with the schematic.
  **No clamp diodes.** I checked the datasheet tables myself:
  - Table 2 (PDF p.6): B3/B4 inputs "AC Coupled Audio", B1/B2 outputs "DC Coupled Audio".
  - Table 3 (PDF p.7): all four audio pins "-5V to 5V" typical, −12 V/12 V min/max.

  So Electrosmith specifies 10 Vpp, the same as your target, but builds in 3.3 dB of input
  headroom and 4.8 dB of output headroom above it.
- **DAC output** (U12B left, U12A right, TL074): **balanced MFB**. CODEC_OUT_L+ → R33
  18 kΩ → node → R41 66.5 kΩ → −IN; R47 39 kΩ node → output; C74 18 pF −IN → output.
  CODEC_OUT_L− → R3 18 kΩ → node → R42 66.5 kΩ → +IN; R39 39 kΩ node → GND; C70 18 pF
  +IN → GND. C66 100 pF across the two nodes. Gain **−2.17** (inverting: OUT+ drives the
  − input). **f0 52.1 kHz, Q 0.68** (my calculation, which matches the subagent's).
  R51 100 Ω out, **DC-coupled** (datasheet Table 2, "DC Coupled Audio"). Full scale
  8 × 2.17 = **17.3 Vpp (±8.7 V)**. Per the subagent (I did not open these): a forum user
  measured "almost -9V to 9V", and found that writing +1 in code gave "about -9V"
  (community.daisy.audio t/3566, March 2023); libDaisy issue #575, "DaisyPatchSM audio
  outputs are inverted", is open.
- **Supplies** (subagent's reading of sheet 3): "+5V ANALOG" from U8 LD1117-5V off +12 V (ferrites FB7/FB8, C7/C9
  10 µF, C5/C8 100 nF); that this rail feeds codec VCC is inferred. +3V3_D comes from a
  TPS621x buck and +3V3_A = +3V3_D through FB5. ±12 V enter through FB1/FB2 and
  NSR1020 series diodes.
- **Notable:** no mute circuit. VCOM is decoupled again with 100 nF right at each
  op-amp's + input (C68/C69). That is worth copying, because VCOM has a 12.5 kΩ source
  impedance and a long trace to the op-amps picks up noise.

### 4B. Daisy Seed2 DFM

Files: `ES_Daisy_Seed2_DFM_Rev5-REDUCED.pdf` (2025-02-17, 4 sheets, no codec sheet) and
`Daisy_Seed2_DFM_v1-0-12.pdf`.

- **No analogue conditioning on the module.** Header P2 brings out the raw codec pins:
  CODEC_IN_L/R, **CODEC_VCOM**, and CODEC_OUT_L±/R± (datasheet pins D1–D7). The carrier
  supplies the front end.
- **Control mode:** H/W mode (libDaisy, no I²C), DEMP driven low by PB11. Differential
  pins on the header imply MODE has 220 kΩ to DGND **[inferred]**. 5 V analogue comes
  from an LD1117-5V (U8); 3V3 digital from an ST1S03 buck.
- **Datasheet application circuits** (printed pp.8–10, PDF pp.11–13). These are
  Electrosmith's published reference front ends. The values are the subagent's
  reading; I checked the Patch SM originals they copy:
  - Fig 1.1 Line in = TI Fig 34a (20k/10k∥330p, +IN on VCOM, 1k).
  - Fig 1.2 Line out = TI Fig 34b (10k/7.5k/820R/1500p/470p, OPA1654), with VCOM buffered
    to make "AREF_+2V5".
  - **Fig 1.3 Eurorack in** = the Patch SM input (C67 10 µF).
  - **Fig 1.4 Eurorack out, DC-coupled** = the Patch SM MFB (gain −2.17, 50 kHz).
  - **Fig 1.5 Eurorack out, AC-coupled** = the same MFB with R66 returned to VCOM, then
    10 µF, 10 kΩ and 100 Ω.
- **Datasheet errata:** it says the audio inputs are "AC coupled and 3.6Vpp", which
  contradicts a raw VIN pin and the datasheet's own Fig 1.1 (biased from VCOM). It gives
  outputs as "0dBFs @ 1Vrms", which does not fit a 5 V PCM3060 (4 Vpp per pin). The
  wording appears to be carried over from the Seed datasheet.

### 4C. Daisy Seed Rev7 ("v1.2")

Files: `ES_Daisy_Seed_Rev7.pdf` ("Rev7-Reduced", 2024-02-01, 1 sheet; I checked the
audio section in `img/seed7_audio-1.png`) and `Daisy_Seed_datasheet.pdf`
(v1.2.0, 2026-03-18).

- **Control mode** (datasheet "Audio Codec", printed p.12, PDF p.15): "H/W Mode,
  Single-ended VoutX", "24-bit left-justified", de-emphasis off, slave for ADC and DAC,
  VDD 3.3 V filtered from +3V3_D, **"Analog VCC 4.5V provided by on board LDO"** (U4
  LP2985 "4v5"). MCLK PE2 → SCKI1/SCKI2. "VCOM ... is not exposed". "not connected via
  I2C".
- **ADC input:** AUDIO_IN_L → R24 3.6 kΩ → C33 4.7 µF → CODEC_LIN. This is passive: a
  series resistor raises full scale to 2.7 Vpp × 13.6/10 = **3.67 Vpp**, with a 2.5 Hz
  HPF. No buffer, no clamp.
- **DAC output:** CODEC_LOUT (VOUT+ only) → C64 4.7 µF → R29 47 kΩ to AGND → R30 100 Ω
  → AUDIO_OUT_L. Single-ended, **AC-coupled**, no post-filter, full scale 0.8 × 4.5 =
  **3.6 Vpp**.
- **Forum** (community.daisy.audio t/4943, Feb–May 2024; not checked further by me):
  users report 225 µVrms output noise on Rev7 against 40 µVrms on Rev4, blame the
  PCM3060's out-of-band noise, and fix it with an RC or "a 2pole LPF similar to that
  described in the PCM3060 datasheet (pg.40)". That fits the missing post-filter.

### 4D. Daisy Patch Rev8 carrier (a discrete PCM3060)

File: `ES_Daisy_Patch_Rev8.pdf` (2025-03-13). The only Electrosmith sheet that draws
the PCM3060 with its straps (I checked `img/p8codec-1.png`):
- MODE: R90 220 kΩ to +3V3_D, so H/W mode, **single-ended** (only VOUTL+ and VOUTR+
  are used). The sheet prints TI's MODE table.
- FMT pulled up by R77 4.7 kΩ (left-justified), DEMP pulled down by R91 4.7 kΩ, IFMD to
  GND (slave), RST tied to +3V3_D. FMT and DEMP sit on the MCU's I2C2 nets, so a later
  I²C build could take them over.
- VCC +5 V (C4 100 nF, C1 10 µF); VDD from +3V3_D through R19 5.1 Ω (C3 100 nF, C2
  10 µF). VCOM: C8 2.2 µF + C5 100 nF, exported as CODEC_VCOM. SAI2_MCLK feeds both
  SCKIs. ZEROL/ZEROR are not connected.
- Front ends (from the subagent's reading; not re-checked by me): input 100 kΩ → TL074
  → 10 µF → 100 kΩ/100 kΩ ∥ 47 pF inverting stage on VCOM → 1 kΩ → VIN, net about
  0.105, so about 28.5 Vpp full scale. Output AC-coupled 10 µF with 47 kΩ, then two
  inverting TL074 stages, net gain about +7.1, two first-order 33.9 kHz poles. On ±12 V
  it clips before the codec's full scale.

---

## 5. Befaco: no module uses a PCM3060

Covered at the coordinator's request. **No Befaco module uses a PCM3060, directly or
through a Daisy.** `gh search code PCM3060 --owner Befaco` returns nothing. The only
"Daisy" references are two code comments in `Oneiroi/Commons.h` 359 and 377 crediting
DaisySP. Befaco's codec modules (**Lich, Oneiroi, Iroi**) all carry Rebel Technology's
**OWL Digital mk3** plug-in module, and its codec is a **Cirrus CS4271**. The OpenWare
firmware has `#define USE_CS4271` at `Lich3/Core/Inc/hardware.h` 67 (I checked) and
`feature/oneiroi` `Oneiroi/Core/Inc/hardware.h` 65 (I checked). The driver
`Source/cs4272.c` makes the codec **master** from its own 24.576 MHz crystal (per the
subagent). Iroi = CS4271 is inferred: same module and pinout, firmware target not
public. The OWL module's own schematic is not published, so the codec's VA is unknown.
VA = 5 V is inferred from the firmware scale factors (`AUDIO_OUTPUT_SCALAR 10.2`,
`AUDIO_INPUT_SCALAR -10.75`, which I checked). The CS4271 is architecturally similar
(single-ended ADC, differential DAC, mid-rail VQ), so the front ends are still a useful
comparison.

| | Lich | Oneiroi | Iroi |
|---|---|---|---|
| Schematic | befaco.org/docs/Lich/Lich_V1_sch.pdf (2020) | befaco.org/docs/Oneiroi/Oneiroi_0_1_THT.pdf (2024) | befaco.org/docs/Iroi/Iroi_V1_THT_Schematic.pdf (2026) |
| Licence | "Published under the GNU GPL" on the sheet | CC BY-NC-SA badge (no version) | CC BY-NC-SA badge |
| Input | **DC-coupled** inverting, R16 100k in, R8 12k fb ("13k -> 12k"), + biased from CS_VREF via R14 12k / R15 100k; R7 100 Ω + C6 2.2 nF to VREF (723 kHz). No clamps | jack → 1N4148 clamps to ±12 V → C53 10 µF AC → 100k → buffer → 3-way **gain switch** (Eurorack / line / contact mic) → inverting stage on CS_VREF → 100 Ω + 2.2 nF | 10 µF AC → ×−2 (200k∥10p) → inverting stage on VREF → 100 Ω + 2.2 nF. No clamps |
| Input full scale | ≈ 23.5 Vpp (12k) | 21.9 Vpp / 1.37 Vpp / 0.55 Vpp | ≈ 22.5 Vpp |
| Output | balanced MFB: 4k7 in, 2.2 nF node caps to GND, 20k fb, 4k7 to op-amp inputs, C10 200 pF (fb) / C7 100 pF (+IN). Checked in `render/lich_dacA.png` | same as Lich (C10 220 pF) | same with 27k |
| Output gain / corner | 4.26, −3 dB ≈ 24–26 kHz | 4.26, ≈ 23.5 kHz | 5.74, ≈ 17.6 kHz (−4 dB at 20 kHz) |
| Coupling, out R | DC, 1 kΩ | DC, 1 kΩ | DC, 1 kΩ |
| Output level | ±10.2 V (20.4 Vpp) | ±10.2 V | would need ±13.8 V at full scale; clips on ±12 V, or the patch never drives full scale **[unverified]** |
| Op-amps | sheet says OPA1678, BOM fits NE5532 | NE5532 | NE5532 |
| Other | firmware DC-offset calibration (`AUDIO_INPUT_OFFSET`, `AUDIO_OUTPUT_OFFSET`) | same | — |

The Lich's mismatched MFB capacitors (200 pF on the inverting side against 100 pF on
the non-inverting side) unbalance the two legs at high frequency. Your design and Beads
keep them equal.


---

## 6. Blokas Pisound: not a PCM3060, and no schematic published

Blokas' own audio documentation (blokas.io/pisound/docs/audio/, read 2026-10-15)
names the converters: **ADC PCM1804**, the I²S master, and **DAC PCM5102A**, a slave.
So Pisound is **not a PCM3060 design**. The page gives:
- Input: AC-coupled into an OPA4134 gain stage, 0 to +40 dB on a pot, 100 kΩ ∥ 2 pF,
  2.5 Vpp clip at 0 dB.
- Output: DC-coupled, 2.1 Vrms maximum into 1 kΩ.

Neither that page, the docs index (which only says "Burr-Brown chips"), nor the
specifications page links to a schematic.

Blokas staff on their forum: "No, it's not publicly available" (2020-02-18, thread 824)
and "The schematics are not open source" (2024-03-05, thread 5098), per the wider-search
subagent. The pisound-docs source (`docs/audio.md` lines 28 and 45, @ 83a4c6e) names the
same two chips.

## 6b. Wider search: other published PCM3060 designs

The method was GitHub code and repo search plus web search; downloads are in
the downloaded copies. Values come from the subagent's KiCad and Eagle netlist
parsing. For the 4ms Brainboard I re-read the key values in the file myself: C6 820 pF
(line 92679), R16 24 kΩ (45411), R34 14 kΩ (96232), C8 180 pF (49626). I recomputed
its MFB (f0 18.9 kHz, Q 0.81) and it matches.

### 6b.1 4ms MP153 Brainboard ("Kit-Brainboard"), Eurorack, ±12 V. The most relevant find.

- **Files:** github.com/4ms/mp153-brainboard-pcb @ 2f914ef,
  `pcb-p6/Kit-Brainboard.kicad_sch` (p5 has the same audio). **No licence file.**
  Firmware: 4ms/mdrivlib @ a91dcf9, `drivers/codec_PCM3060.cc` (MIT header).
- **Control:** U1 PCM3060PW (line 14864). MODE pin 28 to GND gives **I²C**; ADR to GND
  gives 0x46. Firmware sets I²S 24-bit, ADC and DAC slave, **differential (S/E = 0)**,
  ADC HPF on (a DC variant bypasses it). STM32MP153 SAI2 is master; SCKI1 and SCKI2 are
  joined to SAI_MCLK. RST is driven from PE12.
- **ADC input** (NJM2068, ±12 V):
  - JB1 → R27 1 kΩ → U6A unity follower, with R29 1 MΩ to GND.
  - Then C19 2.2 µF → R32 100 kΩ → U6B inverting, R34 14 kΩ ∥ C23 220 pF, + on VCOM.
  - Then R40 1 kΩ → VINL.
  - Gain −0.14 (−0.127 with VIN's 10 kΩ), so **full scale ≈ 23.6 Vpp**. Input impedance
    ≈ 1 MΩ, HPF 0.72 Hz, LPF 51.7 kHz. No clamps on audio (the BAT54S on the board are
    on the CV inputs).
- **DAC output** (NJM2068):
  - Balanced MFB: R6/R7 10 kΩ, C6 820 pF across the nodes, R10/R11 10 kΩ, R16 24 kΩ
    feedback, R12 24 kΩ to GNDA, C8/C9 180 pF.
  - Gain **2.4** (inverted), **f0 18.9 kHz, Q 0.81**, which is −2.4 dB at 20 kHz.
  - R18 1 kΩ out, DC-coupled. **Full scale 19.2 Vpp (±9.6 V).**
- **Supplies:** VCC from AP2120N-5.0 off +12 V (only C3 10 µF on that net); VDD from an
  AP62301 buck. VCOM has C4 22 µF + C5 100 nF and also biases U6B/U7B.
- **Variants:** the mp153 **carrier board v0.4** (4ms/mp153-devboard @ 8ab17e3) has the
  same values on TL072H, but feeds VOUT+ to the non-inverting side, so its output is
  not inverted. The 4ms DIY Sampler kit wires jacks straight to the Brainboard. The
  F723 Brainboard used in the shipping Sampler and Looping Delay also drives a PCM3060
  in firmware, but **no schematic was found [unverified]**.

### 6b.2 Other verified designs

| Design | Licence, file | Control | Input | Output |
|---|---|---|---|---|
| **TINRS "Space"** (Eurorack, ESP32-S3) | MIT; ThisIsNotRocketScience/Eurorack-Modules @ c25d133, `Development/.../Space/` (`PCM3060.kicad_sch`, `CodecBuffer.kicad_sch`) | I²C, ADR 0x46; port 2 grounded (needs CSEL2 = 1); VOUT− open, so S/E = 1 required; no firmware found | **DC-coupled** inverting level-shift on a single-supply 5 V MCP6022: 100k in, 12.1k ∥ 100 pF, 12.1k from an inverted VCOM; 100 Ω + 2.2 nF → VIN. FS 24.8 Vpp, 100 kΩ, no clamp (the 5 V op-amp can't exceed the pin range) | **single-ended**: VCOM removed by a TL074 summer (×−1, 33.9 kHz), then an NE5532 MFB ×−8.48 (≈58 kHz); 56 Ω, DC. Nominal FS ≈ 34 Vpp, which **cannot swing on ±12 V** (development folder, likely unfinished) |
| **centrevillage/ideal-groove-box** | MIT; @ 2bc1828, `hardware/pcb/projects/main/main.sch` | I²C 0x46; no firmware in repo | **DC-coupled** inverting summer, −0.15·Vin + 2.5 V via a −10 V LM4040 offset; 470 Ω + **BAT54S clamp** at VIN. FS ≈ ±10.5 V. Needs the ADC HPF bypassed | balanced MFB (4.7k / 12k / 1k / 470 pF / 2.2 nF diff), ×2.55, f0 ≈ 32 kHz, Q 0.68, 470 Ω, DC; ≈ ±10.2 V |
| **Ploopy Headphones "Gould" R1.007** | CERN-OHL-S-2.0; ploopyco/headphones @ 9c036f0, PDF p.2 and p.9 | I²C; SCKI2 from RP2040 PWM; DAC only | — | balanced MFB on OPA1688 ±9 V, ×5.6, f0 ≈ 70 kHz, then 8 paralleled followers and a 12 V TVS |
| **jeffkub/esp32-galvo** | MIT; @ 7a85612 | I²C | TI Fig. 34a copy (20k / 10k ∥ 330 pF on VCOM, OPA2134) + 1k + **BAT54S** | LME49724 fully differential, ×1.24, 48 kHz first order |
| **kanengomibako/Sodium** (pedal) | Unlicense; @ 31dc693 | H/W, **single-ended** (220k to VDD), I²S, slave | 100 nF, 1 MΩ to a 2.5 V divider, buffer, 100 Ω + 10 nF; 3 Vpp | 10k + 100 pF (159 kHz), buffer, 10 µF, 1 kΩ; 4 Vpp |
| **DMME-NL RP2040-DSP V2.1** | GPL-3.0; @ 1b2df6f | H/W single-ended; "untested" | **Faulty:** op-amp DC-coupled into VIN at supply/2, not VCOM | follower, 10 µF; no filter |
| **marcoallegretti/Teresina** | no licence | Daisy Seed Rev7 clone (H/W, SE, LJ) | 3.6k + 4.7 µF | 4.7 µF, 47k, 100 Ω |
| **jonronen raspi_audio** (and copies) | GPL-2.0 (geda-stuff) / none | H/W SE, ADC master from 12.288 MHz | 4.7 µF straight to VIN | 22 µF, 10k, 100 Ω |
| **torvalds/1590A** | GPL-2.0; `Effect/STM32/pcm3060.kicad_sch` | H/W SE, FMT high | 1 µF, 1 MΩ to VCOM; no op-amps | 1 µF, 1 MΩ; unfinished (I²S and RST unconnected) |

Breakouts and broken drafts (bread-modular PCM3060 breakout, RP_Mini_Dsp, BasicCode
STM32MP151, frankylynch codec boards, activexray, DeltaSDR, altura-dsp) carry no usable
front end; details are in the subagent log. False hits discarded: Daisy-based
projects, software-only drivers, library symbols never placed, and boards that use a
different codec (SuperAudioBoard CS4272, busy-toad, EnvOpenAudio, WaveForge).

**Still unverified when this was written:** the wider search was cut short with two
sub-batches outstanding. Not checked:
- guitar-pedal projects: GuitarML GuitarPedalSTM32, Can-Bot RTEP_Pedal, GuitarFX,
  DADDesign OSCAR, Signal-Forge, Shrapnel, Proyecto-blackpill, pcm3060_h723zg,
  Audrey-X, CHOMPI;
- platform codec checks: Norns, OWL, other 4ms, Qu-Bit, Noise Engineering, Tiliqua,
  Bela, Axoloti/Ksoloti, Tympan, other Mutable modules;
- downloaded but unread: TI PCM3060EVM (SLAU220), Harvard QICPCM3060, kyohritsu
  codec3060c, zztop, hopper, EELE_465 project, OpenEuroBoard, JackUlbrichBaker
  Dsp_platform, Qu-Bit Nebulae V2, monome aleph, terminal_tedium.

---

## 7. Your design, checked against the same arithmetic

- **Codec:** H/W mode, MODE 220 kΩ to DGND (differential), FMT/DEMP/IFMD low (24-bit
  I²S, slave, no de-emphasis), VCC 5 V linear, VDD 3.3 V. **Identical to Beads' straps.**
  The ADC's 0.91 Hz digital HPF is always on in H/W mode (§0), so the ADC path is AC
  regardless of the coupling cap.
- **ADC input:** 1 µF → 100 kΩ, inverting TL074H, 33 kΩ ∥ 100 pF, + on VCOM, 1 kΩ → VIN,
  BAT54S to the 5 V analogue rail and GND, 1 MΩ to GND at the jack. Gain −0.33 × 10/11 =
  **−0.300**; full scale **10.0 Vpp**; HPF 1.59 Hz; LPF 48.2 kHz first order; input
  impedance 100 kΩ ∥ 1 MΩ = 91 kΩ. **This is TI Fig. 34a and, almost value for value,
  the Patch SM input** (66.5 kΩ / 15 kΩ ∥ 220 pF, 14.6 Vpp). The clamps start
  conducting once VIN leaves 0–5 V, i.e. above ±8.3 V at the jack (16.7 Vpp). The BAT54S
  is 0.40 V at 10 mA (MDD BAT54S datasheet), at or above the codec's
  VCC + 0.3 V absolute maximum, so the 1 kΩ is what really limits current.
- **DAC output:** difference amp, 12 kΩ in, 15 kΩ feedback and to ground, 100 pF C0G
  across each 15 kΩ, 1 kΩ out, ±12 V TL074H. Gain **1.25**, full scale **10 Vpp**, one
  pole at **106 kHz**, DC-coupled.

---

## 8. Comparison table

| Design | Codec (verified?) | Control mode | Input stage: gain, coupling | Input FS at jack | Output mode | Output topology / gain / filter / coupling | Output level at jack |
|---|---|---|---|---|---|---|---|
| **TI Fig. 33/34 (datasheet)** | PCM3060 | any | inverting on VCOM, −0.5, 10 µF AC, 48 kHz 1st order | 6 Vpp (2 Vrms) | diff (b) or SE (c) | (b) balanced MFB, 0.75, 54 kHz 2nd order, capless; (c) SE MFB + 10 µF + mute | 6 Vpp (2.12 Vrms) |
| **MI Beads** | PCM3060 (sch) | H/W, MODE 220k→GND, I²S, slave | unity SK buffer (33.9 kHz, Q 0.71) → 10k/2k divider (+1.2 nF, 93 kHz) → 10 µF AC into VIN; 1/7; 3rd order; 100 kΩ, 16 V TVS | **21 Vpp** (+0…32 dB digital AGC) | **differential** | balanced MFB, **2.5**, **29.5 kHz Q 0.73** 2nd order, DC, 1 kΩ + 16 V TVS, NJM2068 | **20 Vpp** (inverted) |
| **Keeos Ogham** | via Seed; PCM3060 only if Rev7 **[unverified]** | Seed Rev7: H/W, SE, LJ, VCC 4.5 V | none (inputs unused) | — | single-ended | Seed: 4.7 µF/47k AC; carrier: 470 Ω/2.2 nF (127 kHz, 1st order) → non-inv TL072 ×4.70, 1 kΩ | measured ≈19.5 Vpp, trimmed to ≈10 Vpp in firmware (0.51×) |
| **Daisy Seed Rev7** | PCM3060 (datasheet) | H/W, SE, LJ, slave, VCC 4.5 V | 3.6 kΩ series + 4.7 µF AC, passive | 3.67 Vpp | single-ended | 4.7 µF + 47 kΩ + 100 Ω, **no filter**, AC | 3.6 Vpp |
| **Daisy Seed2 DFM** | PCM3060 (libDaisy, datasheet) | H/W, DEMP via PB11; MODE/FMT not shown | none on module (raw VIN + VCOM on header); app note = Patch SM stage | carrier's | differential (pins on header) | none on module; app note Fig 1.4/1.5 = Patch SM MFB, DC or AC | carrier's (app note ±8.7 V) |
| **Daisy Patch SM** (+ patch.init) | PCM3060 (libDaisy) | **I²C**, LJ, slave, S/E default = diff | inverting on VCOM (local 100 nF), −0.205, 2.2 µF AC, 48 kHz 1st order, 66.5 kΩ, no clamps | **14.6 Vpp** | **differential** | balanced MFB, **2.17** (inverted), **52 kHz Q 0.68**, DC, 100 Ω, TL074 | **17.3 Vpp** (forum: "almost −9 V to 9 V") |
| **Daisy Patch Rev8** | PCM3060 (sch) | H/W, MODE 220k→3V3 (SE), FMT high (LJ), RST tied high | 100k buffer → 10 µF → inverting on VCOM, ≈0.105 | ≈28.5 Vpp | single-ended | 10 µF/47k AC → two inverting TL074 stages, ≈7.1, 2 × 1st order 33.9 kHz, 1 kΩ | clips (≈ ±10.5 V) before codec FS |
| **Befaco Lich** | **CS4271, not PCM3060** | SPI, codec master | DC inverting on VREF, −0.12, 100 kΩ, no clamps | ≈23.5 Vpp | differential | balanced MFB (node caps to GND), 4.26, ≈25 kHz, DC, 1 kΩ | 20.4 Vpp |
| **Befaco Oneiroi** | **CS4271, not PCM3060** | SPI, codec master | 1N4148 clamps → 10 µF AC → buffer → 3-way gain switch → inverting on VREF | 21.9 / 1.37 / 0.55 Vpp | differential | as Lich, 4.26, ≈23.5 kHz, DC, 1 kΩ | 20.4 Vpp |
| **Befaco Iroi** | **CS4271 (inferred), not PCM3060** | as above | 10 µF AC → ×−2 → inverting on VREF | ≈22.5 Vpp | differential | as Lich with 27k, 5.74, ≈17.6 kHz, DC, 1 kΩ | ±13.8 V demanded; clips on ±12 V **[unverified]** |
| **Blokas Pisound** | **PCM1804 + PCM5102A, not PCM3060** | — | AC → OPA4134, 0 to +40 dB | 2.5 Vpp at 0 dB | — | DC-coupled (no schematic published) | 2.1 Vrms |
| **4ms MP153 Brainboard** | PCM3060 (sch) | **I²C**, I²S, slave, diff | 1 MΩ follower → 2.2 µF → inverting on VCOM, −0.127, 51.7 kHz 1st order, NJM2068, no clamps | **23.6 Vpp** | **differential** | balanced MFB, **2.4** (inverted), **18.9 kHz Q 0.81**, DC, 1 kΩ | **19.2 Vpp** |
| **TINRS Space** (dev) | PCM3060 (sch) | I²C, SE required | DC inverting level-shift on 5 V MCP6022, −0.121, 100 Ω + 2.2 nF | 24.8 Vpp | single-ended | VCOM-cancel summer + MFB ×8.48, ≈58 kHz, DC, 56 Ω | nominal 34 Vpp; clips on ±12 V |
| **ideal-groove-box** | PCM3060 (sch) | I²C | DC inverting summer, −0.15, 470 Ω + BAT54S | ≈21 Vpp | differential | balanced MFB, 2.55, 32 kHz Q 0.68, DC, 470 Ω | ≈20.4 Vpp |
| **Yours** | PCM3060 | H/W, MODE 220k→DGND, I²S, slave | inverting on VCOM, −0.30, 1 µF AC, 48 kHz 1st order, 91 kΩ, BAT54S to 5 V/GND | **10 Vpp** | **differential** | difference amp, **1.25**, **106 kHz 1st order**, DC, 1 kΩ, TL074H | **10 Vpp** |

Smaller designs (Ploopy, esp32-galvo, Sodium, DMME, Teresina, raspi_audio, 1590A) are
in the §6b table.

---

## 9. Where the published designs differ from yours

1. **Output filter: one pole at 106 kHz where every published differential-to-single-
   ended stage uses two, at 19–54 kHz. Adopt.** The only first-order exception is
   esp32-galvo's fully differential driver. TI's Fig. 34b, Beads (29.5 kHz), the Patch SM (52 kHz),
   the Seed2 DFM app note, the 4ms Brainboard (18.9 kHz) and ideal-groove-box (32 kHz)
   all use a balanced second-order MFB. TI says the on-chip filter is "not enough"
   for many applications, and its differential specs assume a second-order low-pass
   (p.5, note 11). The Seed Rev7, which has no post-filter, drew forum complaints of
   225 µVrms against 40 µVrms on Rev4 (§4C). Your DC-coupled output will often feed
   other modules' ADCs or VCAs, where ultrasonic shaped noise matters more than at a
   speaker. **Keep 12 kΩ and 15 kΩ** (both 15 kΩ now return to the 12k/15k nodes,
   not to the op-amp pins) and add, per channel:
   - 1 kΩ from each 12k/15k node to its op-amp input;
   - 1.5 nF C0G across the two nodes;
   - 270 pF C0G from −IN to the output, and from +IN to ground (replacing the two 100 pF).

   That gives gain 1.25, **f0 45.7 kHz, Q 0.75, −0.03 dB at 20 kHz** (same maths that
   reproduces TI's 54 kHz / Q 0.70). The cost is two resistors and one capacitor per
   channel.
2. **Input headroom: 10 Vpp full scale where every Eurorack design is 14.6–24.8 Vpp.
   Adopt.** Beads is 21 Vpp, the 4ms Brainboard 23.6, the Patch SM 14.6,
   ideal-groove-box about 21, TINRS Space 24.8, Befaco about 22–23.5, and the Daisy
   Patch about 28.5. Hot Eurorack sources exceed 10 Vpp: Beads' own output is 20 Vpp and the
   Patch SM's is 17.3 Vpp. At 10 Vpp they hard-clip in the ADC, and above 16.7 Vpp your
   BAT54S clamps start conducting in normal use. Change the feedback to **15 kΩ ∥ 220 pF**
   (still 48.2 kHz): gain −0.136, **22 Vpp full scale**. A ±12 V input then keeps VIN
   within 0.86–4.14 V, so the clamps become pure fault protection, as in Beads, which
   needs none at 1/7. The cost is 6.8 dB of ADC range (99 dB → about 92 dB), which is
   still far below Eurorack noise; make it up with digital gain, as Beads does (+0 to
   +32 dB AGC).
3. **Reset and power-up quiet: drive RST from a GPIO with a 10 kΩ pull-down. Adopt if not
   already.** Beads does exactly this (R49 to PC13), releases RST only after the SAI
   clocks run, re-asserts it on stop, and writes silence for 250 ms after every start. In
   H/W mode RST is the only power-down, and TI asks for clock changes to be made in
   power-down (p.31 note). While in reset both VOUT pins sit at VCOM, so your DC-coupled
   difference amp outputs 0 V, and no mute transistor (TI Fig. 34c) is needed. Nobody
   uses ZEROL/ZEROR.
4. **DC offset on a DC-coupled output. Adopt if the outputs will carry CV.** The PCM3060's
   differential bipolar zero error is ±1 % FSR typical (p.4): about 80 mV at the pins,
   100 mV at your jack. On top of that, 1 % resistors in the difference amp turn the
   2.5 V common mode into tens of mV. Befaco's firmware calibrates both directions
   (`AUDIO_INPUT_OFFSET`, `AUDIO_OUTPUT_OFFSET`); Beads and the Patch SM don't (audio
   only). Use 0.1 % or matched resistors in the difference amp, and store a per-channel
   offset trim.
5. **Polarity. Free to fix now.** The Patch SM, Beads and the 4ms Brainboard all put VOUT+
   on the inverting side, so their outputs are inverted (libDaisy issue #575 is open
   about it). 4ms's later mp153 carrier v0.4 swapped it. Your input
   stage is inverting too. Route VOUT+ to the non-inverting (15 kΩ-to-ground) side so the
   output follows the sample sign, and negate ADC samples in firmware. That matters once
   the output is DC-coupled CV.
6. **Local VCOM decoupling at the op-amps. Adopt (cheap).** VCOM is an unbuffered
   12.5 kΩ source (p.3). The Patch SM puts 100 nF at each op-amp's + pin (C68/C69), TI
   puts 0.1 µF there (Fig. 34a C3), and Beads uses 47 µF + 100 nF at the codec. Keep your
   codec-pin decoupling (10–47 µF + 100 nF) and add 100 nF at the TL074H + inputs.

**No change needed:**
- Input impedance: 91 kΩ is normal (Beads 100 kΩ, Befaco 100 kΩ, Patch SM 66.5 kΩ).
- The 1 kΩ into VIN: TI, the Patch SM and the Daisy Patch all use it.
- The TL074H: the Patch SM and Daisy Patch use TL074s. At TI's 37 nV/√Hz (SLOS080W) it
  costs by my estimate about 1–1.5 dB against the codec's own noise floor in each
  direction. Beads' NJM2068 would recover that, but it does not matter at Eurorack levels.
- The clamps: most published designs rely on their attenuation and the 1 kΩ instead.
  ideal-groove-box (470 Ω + BAT54S) and esp32-galvo (1 kΩ + BAT54S) clamp VIN exactly as
  you do, so there is precedent.
  With a ±12 V input at your current gain, the op-amp output peaks at about 6.5 V, so
  the 1 kΩ limits the current into the 5 V rail to about 1.2 mA, which the codec's own
  load absorbs.

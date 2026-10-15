# Panel I/O review: pots, buttons and encoder, WS2812 LEDs, I2C

Analogue board Rev A, schematic checkpoint 1 (sheets 6 and 7). Reviewed 2026-10-15 against published designs and datasheets.

**Marks:** **UNVERIFIED** = not checked against a primary source in this pass. Designators are from the generated schematic (`hardware/analogue_board/analogue_board_schematic.pdf`). Values are from `tools/analogue_board/design_digital.py`. LCSC numbers and Basic/Extended status come from the JLCPCB parts API, queried 2026-10-15.

## 0. Verdict in one paragraph

The block is sound: every value in it has a published precedent, and nothing in it will stop the board working. It has two problems worth fixing before the order, both free:

1. **The encoder.** An encoder read through the TCA9555 shares the I2C bus with the OLED. One full-frame OLED write occupies that bus for about 23 ms, and an encoder read that waits that long loses steps. No reference design reads an encoder through an I2C expander. The fix needs no new parts: either route the encoder through gate inputs 3 and 4 (these are already Schmitt-clean direct GPIOs), or follow firmware rules that keep the bus free.
2. **The 100 kΩ wiper pull-down.** It bends the response of a 100 kΩ pot by up to 12 % of full scale, and David uses 100 kΩ pots (MOD2). Changing it to 1 MΩ costs nothing.

Three cheap improvements are worth adopting:
- match EuroPi's actual button topology, and fit 10 nF on the encoder-capable lines;
- give the pot reference its own RC-isolated node, so panel wiring cannot disturb the DAC8568 supply;
- set LED wiring and current rules.

---

## 1. Our design, exactly

### 1.1 Pots (sheet 6; `design_digital.py:15-42`)

| Item | Value | Designators |
|---|---|---|
| ADC | MCP3208-CI/SL, 12-bit SAR, 8 single-ended channels (C16939, Extended) | U601 |
| VDD (pin 16) and VREF (pin 15) | both **+3V3A**, each with 1 µF + 100 nF | C601–C604 |
| AGND (14), DGND (9) | GND | — |
| SPI (panel bus SPI-B) | CLK 13 = SPIB_SCK (Pico GP10 / Teensy 27); DOUT 12 = SPIB_MISO (GP12 / 39); DIN 11 = SPIB_MOSI (GP11 / 26); CS 10 = CS_POT (GP14 / 37) | `design.py:34-38` |
| CS pull-up | 10 kΩ to +3V3D | R601 |
| Per wiper *n* | hole POT*n* → **1 kΩ** → POT_IN*n*. At POT_IN*n*: **100 nF** and **100 kΩ** to GND → CH*n*−1 | R602, R604 … R616 (1k); C605–C612; R603 … R617 (100k) |
| Pot holes | J601: POT1–8, +3V3A ×2 (pot tops), GND ×2 (pot bottoms) | J601 |
| +3V3A rail | XC6206P332MR (C5446, Basic) from +5VA (L78M05). It also feeds DAC8568 AVDD (`design_analog.py:262-267`); budget ≈ 6 mA (`design.py:312`) | — |

Pot tops and VREF share the same rail, so readings are ratiometric: a change in +3V3A moves the pot voltage and the ADC full scale together, and the code does not change.

### 1.2 Buttons, switches and encoder (sheet 7; `design_digital.py:84-112`)

| Item | Value | Designators |
|---|---|---|
| Expander | TCA9555PWR (C465732, Extended), address **0x20** (A0–A2 to GND), VCC +3V3D, 100 nF | U701, C701 |
| INT | open-drain, 10 kΩ to +3V3D → EXP_INT (Pico GP4 / Teensy 22) | R701 |
| Line use | P00–P05 = SW_EN1–6 (DG412 enables); P06 = GATE_OE_N; **P07 = BTN9; P10–P17 = BTN1–8** | — |
| Per line *n* | hole SW*n* is the node. At the node: **10 kΩ to +3V3D** and **100 nF to GND**. Then **1 kΩ** → BTN*n* (expander pin). The button shorts the hole to GND | R703, R705 … R719 (10k); C702–C710 (100 nF); R702 … R718 (1k) |
| Holes | J701: SW1–SW9, GND ×2. Sheet note: "Encoder: A, B and push on any three SW holes." | J701 |

SW1–SW8 sit on Port 1 (P10–P17); SW9 sits on Port 0 (P07).

### 1.3 WS2812 data (sheet 7; `design_digital.py:130-139`)

LED_DATA (Pico GP5 / Teensy 17, TX4 for WS2812Serial) → SN74AHCT1G125DBVR (U703, C7484, Extended) at **+5VD**, OE tied low, 100 nF (C712) → LED_BUF → **330 Ω** (R722) → LED_DIN.

J704 carries LED_DIN, +5VD ×2 and GND ×2, with **10 µF 25 V** (C713) at J704. The LEDs are on the panel, wired by hand. +5VD comes from the TPS54308 buck.

### 1.4 I2C (sheet 7; `design_digital.py:114-128`)

- **Bus:** SDA/SCL on Pico GP2/GP3 (I2C1), Teensy 18/19 (Wire). Pull-ups R720/R721 **2.2 kΩ** to +3V3D. Firmware target 400 kHz.
- **EEPROM:** M24C64-RMN6TP (U702, C79988, Extended/Preferred) at **0x50**. E0–E2 and **WC** to GND; 100 nF (C711).
- **Qwiic:** SM04B-SRSS-TB (J702, C160404): 1 GND, 2 +3V3D, 3 SDA, 4 SCL, mounting pads to GND.
- **Display holes:** J703 carries SDA, SCL, +3V3D and GND for a hand-wired OLED (SSD1306/SH1106, normally at 0x3C).
- **Test pads:** TP701–TP703 on SDA, SCL and EXP_INT.

The +3V3D LDO (XC6206) also feeds the PCM3060 VDD, the ADS8688 DVDD, the gate-in pull-ups and threshold, the expander, the EEPROM and Qwiic. The design note puts the load at ≈ 50 mA (`design.py:294, 312`).

### 1.5 Gate inputs: relevant to the encoder question (sheet 8; `design_digital.py:143-197`)

Each GIN*n* hole → 10 kΩ → node. At the node: BAT54S clamps to +3V3D/GND, 100 kΩ to GND, and 100 kΩ hysteresis from the output. The node feeds an LM393 (+12 V) comparing against GATE_TH = 1.65 V. The open-collector output, pulled up by 10 kΩ to +3V3D, gives GATE_IN*n*. It trips at ≈ 1.98 V rising and ≈ 1.67 V falling at the hole, and has no capacitor.

GATE_IN3 and GATE_IN4 land on **Pico GP8/GP9** and **Teensy 4/5** (`design.py:44-45`).

---

## 2. Reference designs, with evidence

Downloads and rendered crops were working copies for this review and are not kept; each source is cited with its URL, commit or page.

### 2.1 Mutable Instruments Plaits, Marbles, Stages (firmware commit f4cfa76)

Schematic PDFs are from pichenettes.github.io/mutable-instruments-documentation (the `.sch` files in the repo are binary Eagle 5).

- **Plaits v50, sheet 2.**
  - Pots: R1, R2, R7, R8 (main) and R42–R44 (attenuverters), all **10 kB**. Tops on **+3V3_A**. Each wiper has **100 nF to GND** (C11, C12, C32, C34, C51–C53), **no series R and no pull-down**, straight into the STM32F373's ADC1 (PA0–PA6).
  - +3V3_A comes from an LD2981ABU33 (IC3) through **L5** (sheet 5) and is also VDDA, so the pots are ratiometric.
  - Buttons SW1/SW2 go straight to GND with the internal pull-up (`drivers/switches.cc:54`).
  - LEDs: 8 bicolour LEDs on a TLC59281 driver (IC2, IREF R3 10k).
  - Firmware: `ui.Poll()` runs at 4 kHz (`plaits.cc:81`), each pot has a one-pole low-pass (`ui.cc:72-85`), and switches are polled at 1 kHz with an 8-bit shift-register debounce (`switches.h:52-61`).
- **Marbles v70, sheet 2.**
  - Pots: 8 × **10 kB**, tops on +3V3_A, **100 nF** per wiper (C8, C17, C18, C24, C28, C29, C36, C38), no series R, into the STM32F405 ADC1.
  - LEDs: bicolour, straight from GPIO through 2.2k (red) and 1.5k (green).
  - Firmware: pots scanned at 6.4 kHz with low-pass 0.01 and hysteresis (`cv_reader.cc:42-58`); switches at 1 kHz from SysTick (`system.cc:44`).
- **Stages v70.**
  - 20 kB sliders and 10 kB pots go through two 4051 muxes on +3V3_A, with **no wiper or mux-output capacitors**.
  - VREF+ and VDDA are on +3V3_A with 1 µF + 100 nF (C12/C13).

### 2.2 Mutable Braids and Yarns: the rotary encoder

- **Braids v50:** an EC12E encoder with A, B and click **straight to GPIO**, common to GND. **No pull-ups, no RC, no series R**; the internal pull-ups are enabled in firmware (`drivers/encoder.cc:36-51`).
  - Polled at **1 kHz** from SysTick (`system.cc:70`, `braids.cc:98-99`) with a 2-sample edge test (`encoder.h:61-72`).
- **Yarns v03:** the same encoder circuit and decoder; `ui.Poll` runs at 1 kHz (`yarns.cc:72-79`).
- **Braids' main pots** are the one non-ratiometric Mutable case. They hang from a −10 V LM4040 and are summed by MCP6004 op-amps into an **MCP3204**, which has its own 2.5 V LM4040 reference.

### 2.3 Ornament & Crime rev 2e (mxmxmx/O_C master `cfbffab`)

- **Encoders:** two PEC11R, A and B **straight to Teensy 3.2 pins** (T21/T22, T15/T16), common to GND. **No RC, no external pull-up, no series R**; firmware sets INPUT_PULLUP (`OC_gpio.h:73-75`).
  - Push switches: SW_L has 470 nF to GND; SW_R has none.
- **Buttons:** **510 Ω series + 100 nF at the pin**, with the internal pull-up.
- **OLED:** an SH1106 128×64 on **SPI**, not I2C, sharing the bus with the DAC8565. CS has a 10k pull-up. Pages go out by **DMA** inside the 16.666 kHz core ISR (`SH1106_128x64_driver.cpp:31-34,166-175`).
- **Firmware:** the UI timer runs at **1 kHz** and polls both encoders and the buttons (`OC_config.h:14`, `OC_ui.cpp:78-113`), with optional acceleration (`ui_encoder.h:38-117`).
- **Phazerville fork** (`djphazer/O_C-Phazerville` `195932a`, Teensy 4.1 capable): same 1 kHz timer and pull-ups. Its T4.1 hardware's encoder RC is UNVERIFIED.

### 2.4 Music Thing Workshop System Computer Rev 1.0.0 (commit 4fdefdd)

From the schematic PDF (no text layer; read from renders) and `ComputerCard.h`:

- **Pots:** KNOB_X/Y/Z are **B100K**, between +3V3 and GND. The wipers go straight into a CD4052 mux (U1) with **no series R and no capacitor**, then to GPIO28/ADC2 (pp.1, 3). The Z switch uses 100k/100k (R23/R24) to set mid-rail.
- **ADC reference:** ADC_AVDD gets +3V3 **through R60 200 Ω + C12 10 µF, labelled "80Hz LPF on ADC power"** (p.1). The pot tops are on unfiltered +3V3.
- **Firmware:**
  - ADC at 384 kHz round-robin; the mux advances once per 48 kHz sample, so each pot updates at 12 kHz (`ComputerCard.h:630-639, 746-749`).
  - Knob filter: one-pole 127/128, "~60Hz LPF" (`:802-811`).
- **LEDs:** six, switched from +12 V by MMDT3904 transistors (47k base), on 16-bit PWM (`:1015-1033`).

### 2.5 EuroPi, surface-mount (Allen-Synthesis/EuroPi commit 1192d31)

- **Knobs:** VR1/VR2, 10k linear (the BOM says "any value between 5K and 100K will work"). Top on the Pico's own 3V3. Wipers **straight to GP27/GP28 with no R or C**.
- **Buttons (designators confirmed):** **SW1 → R1 1K → BUTTON_1**; at BUTTON_1, R5 **10K to +3.3V** and C9 **100nF to GND** → GP4. SW2 is the same (R2, R6, C10) → GP5.
  - **The 1 kΩ sits between the switch and the RC node, not between the node and the pin.**
  - Firmware also debounces in software (200 ms, `europi_hardware.py:463`).
- **OLED:** a 0.91″ SSD1306 128×32 on J2. **No pull-ups on the EuroPi board**; it relies on the OLED module's own (value UNVERIFIED). I2C0 at **400 kHz** (`europi_config.py:133-162`).
- **Knob averaging:** 32 samples (`europi_hardware.py:46, 139-144`).

### 2.6 Ogham (local `/Users/dbaghurst/GitHub/ogham`, branch `encoder-credit-partial-detent`, 776e8d2; sheet `ui.kicad_sch`)

- **Pots:** RVA1, RVB1, RVRate1, RVLevel1, all **10k**. Tops on +3V3 (the Daisy's 3V3_D output, pin 38; 3V3_A unused).
  - Each wiper: **1k (R_flt1-4) → node with 100 nF (C_flt1-4) and 100k (R_pd1-4) to GND** → ADC_0–3. This is the network our board copied.
  - A firmware comment calls the pull-down "10k" (`ogham_main.cpp:212`), which disagrees with the schematic.
  - Firmware trims the ends: `POT_ZERO 0.020`, `POT_FULL_SCALE 0.906` (`ogham_controls.h:193-194`).
- **Encoder:** an Alps EC11E with A, B and push **straight to Seed GPIO** (D0, D1, D2), common to GND.
  - **100 nF per line**, MCU internal pull-ups, no series R.
  - Full-quadrature state machine polled by **TIM5 at 20 kHz** (`ogham_main.cpp:41-53, 600-614`; `ogham_controls.cpp:91-146`).
- **Display:** a TM1637 7-segment module, not an I2C OLED. **No LEDs on the boards.**

### 2.7 Electrosmith, 4ms and Befaco

**Electrosmith** (schematic PDFs from docs.daisy.audio; libDaisy master f715e48):

- **Patch SM** (datasheet v1.0.5, p.9):
  - A B10K pot's top goes on **A6, the +5V OUT pin**, and the wiper on CV_1–8, which are 100 kΩ inputs reading −5…+5 V through an MCP6004 inverting stage. The pots are therefore **not ratiometric**.
  - For ADC_9–12 the top goes on +3V3 instead.
  - Switches go to GND on any GPIO.
- **patch.init:** VR_1–4, M-10K-B-D, from **+5V** to GND. Switches go to GND on internal pull-ups. The LED sits on CV_OUT_2.
- **Daisy Pod Rev5, p.2:**
  - Pots go from +3V3_A straight to the ADC, with no R or C.
  - **Encoder ENC_1 (PEC11): A, B and click straight to GPIO, common to GND, no pull-ups, no RC.**
  - Two RGB LEDs, sunk by GPIO through 1K each.
- **Daisy Patch Rev8:**
  - Pots (p.2): VR_1–4 are 10k B from +3V3_A, each through 66K5 into an MCP6004 summer with 10 nF feedback (~239 Hz).
  - **Encoder (p.4):** straight to GPIO, no RC.
  - **OLED (p.4): 4-wire SPI.**
- **Daisy Field rev4:**
  - 8 × 10k B pots go into a CD4051 with no RC.
  - LEDs run on a PCA9685 on I2C1 with **4K7 pull-ups** (R72/R73).
  - **The OLED is SPI.**
- **Seed3 DevKit Eurorack Rev3:** 8 × 10K B from +3V3_A through a CD4051, no RC. RGB LEDs are driven from GPIO through 2K.
- **libDaisy:**
  - Encoder and switches use internal pull-ups and are **sampled every 1 ms through an 8-bit shift register** (`encoder.cpp:11-45`; `switch.h:65-74`).
  - The pot slew filter defaults to no smoothing at a 1 kHz callback (`ctrl.cpp:16-45`).
  - The OLED driver is SPI (`oled_ssd130x.h:86-94`).

**4ms**:

- **Kit-Trig-Sampler v1.0 + MP153 brainboard (4ms/mp153-brainboard-pcb 2f914ef):**
  - Pots: 4 × RV16AF B10k. The **top is VREF+**, a dedicated **NCP51460 3.3 V reference** (U13; 1 µF + 10 µF), and the bottom is GNDADC.
  - Each wiper has **0.1 µF** (C1, C2, C9, C10). On the brainboard the signal then goes 10k + 10 nF + BAT54S → NJM2068 follower → 68 Ω → ADC (R37/C27/D9/R44).
  - Buttons: 10k series + 0.1 µF (R25/R26, C16/C17), internal pull-up.
  - LEDs: RGB, sunk by GPIO through 330 Ω–2k.
  - Firmware (sampler-firmware): controls run at 3 kHz with an 11-sample debounce (`debouncer.hh:163-181`); the ADC oversamples 1024× (`brain_conf.hh:15,43-48`).
- **mdrivlib** (a91dcf9) `rotary.hh`: a 16-sample debounce with internal pull-ups. MetaModule (e44c259) polls it about every audio frame, ≈48 kHz (`controls.cc:15-17,176,325-330`).
  - mdrivlib also has a WS2812 driver (`neopixel.hh`, timer PWM + DMA), but no schematic read here uses it.

**Befaco**:

- **Lich v1:**
  - Pots: 8 × R1212-B100K from a −10 V LM4040 into TL072 inverting summers (33k ∥ 100 pF), then 1k → BAT48 → 100 Ω → ADC. Not ratiometric.
  - **Encoder: A and B each have 100 nF to GND (C100/C101) and MCU pull-ups**, straight to PA0/PA1, decoded by **TIM2 hardware quadrature** (OpenWare `main.c:603-611`).
  - Buttons go straight to GND on EXTI with no debounce.
- **Oneiroi:** 15 × B10k from −10 V into DG408 muxes. Buttons are polled every 2 ms with no debounce; LEDs are driven from GPIO.
- **Muxlicer v1.2:** the encoder goes straight to ATmega8 pins with no RC and is serviced every 100 µs (`muxlicer.ino:13-16,257,399-402`).

None of the Electrosmith, 4ms or Befaco boards read uses WS2812 LEDs in hardware.

### 2.8 WS2812/SK6812 practice and two open Eurorack uses

**Adafruit NeoPixel Überguide, "Best Practices":**
- "Place a 300 to 500 Ohm resistor between the … data output pin and the input to the first NeoPixel. The resistor should be at the end of the wire closest to the NeoPixel(s), not the microcontroller."
- Add "a capacitor (500–1000 µF at 6.3V or higher) across the + and – terminals."
- "If using a 3.3V microcontroller you must use a logic level shifter such as a 74AHCT125 or 74HCT245."
- Connect "ground first, then +5V, then data."

**Adafruit, "Powering NeoPixels":** "up to 60 milliamps at maximum brightness white", 20 mA per pixel as a rule of thumb, and "minimum signal voltage of 70% of the NeoPixel voltage".

**Datasheets:**

| Part | VIH | Notes |
|---|---|---|
| WS2812B (Worldsemi, early) | **0.7 × VDD** (3.5 V at 5 V) | 100 nF per LED in the application circuit (p.5); "scan frequency not less than 400Hz" |
| WS2812B V5 | 2.7 V min | 12 mA per colour |
| SK6812 | 3.4 V typ at 5 V | — |
| SK6812MINI-E | 0.7 × VDD | ~500 Ω series protection resistor "must be connected" (pp. 9, 18) |

**Sluisbrinkie Toepler+** (4 HP Eurorack, niektb/sluisbrinkie-eurorack-published 9a2c1f5): RP2040 GPIO16 → **SN74LV1T125 at +5 V → R46 330 Ω** → connector → WS2812B chain. +5 V comes from an AMS1117-5.0 off +12 V, with 22 µF and no per-LED capacitors.

**8Bit EuroRack 7hp** (8BitMixtape, af796ba): ATtiny85 → **330 Ω** → 8 × SK6812. No shifter: the MCU shares the LEDs' 7805 rail.

### 2.9 How I2C encoders are built commercially

Adafruit's I2C QT Rotary Encoder runs seesaw firmware on an on-board microcontroller, which "will track all pulses and pins for you and then save the incremental value for querying at any time over I2C". Its INT pin exists "so you do not have to spam-read the I2C port".

In other words, I2C encoder products decode the quadrature locally and report a count. None relies on the host sampling the A/B levels over I2C.

---

## 3. Datasheet checks and arithmetic

All numbers were calculated with a short script (not kept).

### 3.1 MCP3208 (Microchip DS21298E)

**Does 1 kΩ + 100 nF satisfy the sample-and-hold?** Yes.
- The S/H samples for **1.5 clocks** (p.2), through **RSS ≈ 1 kΩ** into **CSAMPLE ≈ 20 pF** (p.3, Fig. 4-1).
- At 1 MHz the window is 1.5 µs against an internal time constant of 20 ns, so it settles completely.
- During that window the 100 nF wiper cap, not the 1 kΩ or the pot, is the source. Fig. 4-2's limit on source resistance applies to a resistive source with no capacitor. §6.3 asks for a low-impedance or filtered source, and the capacitor is exactly that.
- Charge sharing: a full-scale jump between successive channels costs at most 3.3 V × 20 pF / 100 nF = **0.66 mV (0.8 LSB)** in one shot.
- In steady state the error is R_source × f × CSAMPLE × ΔV:

| Pot | Sampled at | Error, max |
|---|---|---|
| 10k | 1 kHz per channel | 0.3 LSB |
| 100k | 1 kHz per channel | 2.1 LSB |
| 100k | 200 Hz per channel | 0.4 LSB |

This is the same arrangement as Plaits and Marbles: 100 nF on the wiper into a SAR S/H.

**Maximum SCLK:** **1.0 MHz at VDD 2.7 V, 2.0 MHz at 5 V** (p.3). 3.3 V has no row of its own, so ≤ 1 MHz (the spec's figure) is the guaranteed choice. The minimum is 10 kHz effective (§6.2). One 24-clock conversion takes ≈ 25 µs, so all 8 channels can be read at up to ~5 kHz each. Pots need 0.2–1 kHz.

**Noise:** SINAD 72 dB typ (p.2), INL ±2 LSB (C grade); 1 LSB = 0.81 mV at 3.3 V. Every reference filters pots in firmware: Mutable a one-pole plus hysteresis, the WSC 127/128, EuroPi a 32-sample average. Plan the same. 12 bits is ample for pots.

**Loading by the 100 kΩ pull-down.** A pot's wiper has a source resistance of up to Rpot/4, and the pull-down divides it. The worst error falls at about ⅔ rotation:

| Pot | Pull-down 100 kΩ (now) | 470 kΩ | 1 MΩ |
|---|---|---|---|
| 10k | 48 mV = **1.45 % FS** (59 LSB) | 0.31 % | **0.15 %** (6 LSB) |
| 50k | 220 mV = 6.7 % | 1.5 % | 0.73 % |
| 100k | 401 mV = **12.2 % FS** (498 LSB) | 3.0 % | **1.45 %** |

- **Why it matters here:** David's builds use both: B10K in the n8synth examples, and **three 100k pots on MOD2/Melon** (`docs/mod2_reference_review.md:239`). The WSC uses B100K.
- **No reference uses a pull-down this strong with 100k pots.** Plaits, Marbles, the WSC and EuroPi have none; Ogham's 100k sits with 10k pots.
- **Leakage with 1 MΩ:** the MCP3208's leakage is 0.001 µA typ and ±1 µA max (p.3). An unwired channel therefore reads ~1 mV typically. At the worst-case datasheet limit it could read up to 1 V; with 100k that limit is 0.1 V.

**Sharing +3V3A between the DAC8568 and the pot wiring.**
- **What TI asks for:** the DAC8568 datasheet (SBAS430, layout section) says "The power applied to AVDD should be well-regulated and low noise", that AVDD should stay separate from digital loads, and that "1μF to 10μF … and 0.1μF bypass … are strongly recommended … even a Pi filter".
- **How much it matters:** the internal reference's DC line regulation is 10 µV/V, so slow ripple hardly matters. AC PSRR is not specified.
- **The risk from the panel:** the pot-top wires run off-board to the panel by hand. They pick up whatever the loom carries (LED PWM, display, buck), and a wiring slip that shorts a pot-top lead to GND would pull down the supply of the 16-bit DAC and of the ADC.
- **Precedent:** the WSC isolates its ADC supply with **200 Ω + 10 µF** (R60/C12, "80Hz LPF on ADC power"), and Plaits feeds +3V3_A through a ferrite (L5).
- **Answer to the brief's question:** a buffer is not needed. Ratiometric reading makes the absolute reference value irrelevant, and the MCP3208 accepts VREF from 0.25 V to VDD (p.2). What helps is a **separate, RC-filtered node shared by VREF and the pot tops** (finding B3).

### 3.2 TCA9555 (TI SCPS200E)

**Thresholds and pull-ups**
- P-port **VIH 0.7 × VCC, VIL 0.3 × VCC** (p.5). **No input hysteresis is specified anywhere** in the datasheet. Compare the RP2350, whose pads come out of reset with the Schmitt trigger on (pad register `SCHMITT` reset value 1). That is why EuroPi's 1 ms RC into a Pico pin is safe.
- On our 10k/100nF line, the release edge spends **0.85 ms** between VIL and VIH (from 0.36 ms to 1.20 ms). A slow edge with no hysteresis can toggle several times on noise, so firmware debounce is still needed.
- Internal pull-up IIL ≤ 100 µA (p.6). With the external 10k and 1k, a pressed button sits at ≤ 0.1 V. Fine.

**Interrupt**
- INT is set by any input edge and cleared "at the acknowledge (ACK) bit" of a read of that port. "**Interrupts that occur during the ACK clock pulse can be lost (or be very short)**" (§9.3.3).
- Firmware should therefore treat INT as a level and also poll as a backstop.

**Reads**
- "When a command byte has been sent, the register that was addressed continues to be accessed by reads until a new command byte has been sent" (§9.5.4). Once the pointer is parked on Input Port 1, a read is just address + data.

**Bus**
- fSCL ≤ **400 kHz**; Cb ≤ 400 pF; SDA IOL 3 mA at VOL 0.4 V (pp.6-7).

**I2C time per transaction at 400 kHz** (bit periods including ACKs):

| Transaction | Time |
|---|---|
| Expander, Port 1 only, pointer preset | **50 µs** (20 k reads/s if the bus is idle) |
| Expander, both ports, pointer preset | 73 µs |
| Expander, both ports with command byte | 120 µs |
| SSD1306 128×64 full frame, one transaction | **23 ms** |
| One OLED page (128 B) | 3.0 ms |
| 64×48 OLED full frame | 8.8 ms |
| 32-byte display chunk | 0.77 ms |
| EEPROM 32-byte page write | 0.8 ms (+5 ms internal tW, bus free) |

**Max I2C clock:** the SSD1306 caps the bus at 400 kHz (I2C tCYCLE ≥ 2.5 µs, SSD1306 datasheet §13), and so does the TCA9555. Fast-mode-plus is not available.

### 3.3 The encoder (Bourns PEC11R datasheet, rev 04/26)

- Contact bounce **2.0 ms max at 15 RPM**; **60 RPM max operating speed**; contact rating 10 mA at 5 VDC (p.1).
- **Suggested filter (p.3):** 5 V → **10 kΩ pull-up** → contact node → **10 kΩ series** → output with **0.01 µF** to GND. The contact discharges the capacitor through 10 kΩ, never directly.

**How fast can a 24-detent, 24-pulse encoder turn before steps are lost?** It has 4 quadrature states per detent. Allowing a 50 % phase imbalance, the shortest state must outlast the read interval plus the RC release delay:

| RC on the line | Read every 1 ms | Every 3 ms | Every 23 ms (OLED full frame blocks the bus) |
|---|---|---|---|
| 10k / 100 nF (now; release delay 1.2 ms) | ~2.4 rev/s | ~1.2 rev/s | **~0.2 rev/s** |
| 10k / 10 nF (release delay 0.12 ms) | ~4.7 rev/s | ~1.7 rev/s | ~0.2 rev/s |

So the RC is a second-order effect. **The bus being blocked by the display is the first-order one.** With full-frame OLED writes, any brisk turn loses or reverses steps.

The references avoid this entirely.
- Braids, Yarns, O&C, Ogham, Daisy Pod, Daisy Patch, Lich, Muxlicer and the MetaModule all read the encoder on direct GPIO: polled at 1–48 kHz, or by a hardware timer on the Lich.
- O&C, Daisy Patch and Daisy Field drive the OLED over SPI.

**Direct-GPIO options that already exist on this board:**
- **Gate inputs 3 and 4.**
  - The gate-in path (§1.5) is a comparator with ~0.3 V of hysteresis: in effect a Schmitt buffer into a direct GPIO.
  - GATE_IN3/4 are **Pico GP8/GP9**, consecutive pins as the pico-examples PIO quadrature decoder requires (it uses `pin` and `pin + 1`).
  - On the **Teensy they are pins 4/5**, both on the QuadEncoder library's hardware-decoder list ("pins 0-5, 7, 8, 30, 31, 33 and pin 37").
  - **Wiring:** encoder common to a **+3V3D** hole; A → GIN3, B → GIN4; push → any SW hole.
  - **Contact current:** closed, the contact sees ≈ 10 kΩ + 50–100 kΩ, about 30–60 µA. That is comparable to MCU internal pull-ups, which Braids, Yarns and O&C use. For more contact current, fit 10 kΩ from each GIN hole to GND at the panel (0.33 mA).
  - The §3 audit shows no own build uses more than two gate inputs.
- **SPARE1/SPARE2** (UART0 on both modules): direct, but they are now wanted for TRS MIDI.

### 3.4 I2C sizing (TCA9555, M24C64, SSD1306, Qwiic)

**Limits at 3.3 V, Fast-mode** (tr ≤ 300 ns, VOL 0.4 V at 3 mA):
- Rp min = **967 Ω**.
- Rp max = 0.3 µs / (0.8473 × Cb): **2.36 kΩ at 150 pF**, 1.77 kΩ at 200 pF.

**M24C64-R** (ST): fC up to 1 MHz, so 400 kHz is fine. VOL 0.4 V is guaranteed at **IOL 2.1 mA (VCC 2.5 V)** or 3 mA (5.5 V); tW 5 ms; ESD 3 kV HBM. For strict compliance at 3.3 V, keep the paralleled pull-up at or above ~1.3 kΩ.

**Who brings pull-ups:**
- SparkFun Qwiic boards: **2.2 kΩ**, with a cuttable jumper; SparkFun's rule is "disable all but one pair" on a bus.
- Adafruit STEMMA QT boards: typically **10 kΩ**; the STEMMA QT spec: "The I2C device is expected to have pullups".
- Generic OLED modules: typically 4.7–10 kΩ (UNVERIFIED for any specific module).

**What the bus sees:**

| Bus | Effective Rp | Sink current | tr at 150 pF |
|---|---|---|---|
| Board only | 2.2 kΩ | 1.5 mA | 280 ns ✓ |
| + OLED 4.7k | 1.5 kΩ | 2.2 mA | 190 ns ✓ |
| + OLED 4.7k + Adafruit 10k | 1.3 kΩ | 2.5 mA | 166 ns ✓ |
| + OLED 4.7k + one SparkFun 2.2k | **891 Ω** | **3.7 mA** | 113 ns: over the 3 mA Fm sink spec and the M24C64's VOL condition |

**Pinout and addresses**
- **Qwiic pinout:** STEMMA QT/Qwiic is pin 1 GND (black), 2 V+ (red), 3 SDA (blue), 4 SCL (yellow). J702 matches.
- **Addresses:**

| Address | Device | Clash |
|---|---|---|
| 0x20 | TCA9555 | the default of MCP23017/PCF8574-type expander boards |
| 0x50 | M24C64 | Qwiic/STEMMA EEPROM and FRAM boards (defaults UNVERIFIED per board) |
| 0x3C/0x3D | OLED | no clash |

### 3.5 WS2812 path (SN74AHCT1G125, WS2812B)

- **Level:** WS2812B VIH = 0.7 × VDD = **3.5 V at 5 V**, which a 3.3 V GPIO cannot meet (the V5 part's 2.7 V would pass, but the version fitted is unknown). The AHCT1G125's **VIH is 2.0 V** at VCC 4.5–5.5 V, and its "inputs are overvoltage tolerant … to 5.5 V" (pp. 4, 10). It works.
- **Unused inputs:** the AHCT datasheet says "All unused inputs … must be held at VCC or GND" (p.4 note). LED_DATA floats whenever no module is fitted. A fitted Pico 2 holds it low at reset: the RP2350 pad's pull-down `PDE` resets to 1.
- **Series R:** 330 Ω is inside Adafruit's 300–500 Ω and matches Toepler+ (R46 330 Ω) and 8Bit EuroRack (330 Ω).
  - Adafruit places it at the LED end. Ours is at the driver end, which is standard source termination and equivalent for a short in-module lead (edge time ~10 ns into ~30 pF, against a 1.25 µs bit).
  - Either way it limits current into an unpowered first LED to (5 − 0.6)/330 ≈ 13 mA.
- **Current budget (5 V, and from +12 V via the buck at 88 % efficiency):**

| LEDs | Full white, 60 mA each | 20 mA each | 5 mA each |
|---|---|---|---|
| 4 | 240 mA → 114 mA from +12 V | 80 mA → 38 mA | 20 mA → 9 mA |
| 8 | 480 mA → **227 mA from +12 V** | 160 mA → 76 mA | 40 mA → 19 mA |
| 16 | 960 mA → **455 mA from +12 V** | 320 mA → 152 mA | 80 mA → 38 mA |

  The spec's whole-module worst case is ~350 mA on +12 V (§8). Eight LEDs at full white would use two-thirds of it.
- **Audio-band current:** WS2812B PWM runs at ≥ 400 Hz (datasheet), and the 2020 package at ~2 kHz (UNVERIFIED, secondary source). LED current therefore switches in the audio band. Its return path must not share the pot or jack ground wire.
- **ESD:** the AHCT1G125 is rated only **1 kV HBM** (p.4). The 330 Ω in series is its protection on the off-board lead.

### 3.6 Supplies and ESD

- **XC6206 (Torex):** Pd **250 mW** in SOT-23 and a foldback current limiter (pp.1, 3). On +3V3D at 100 mA from 5 V it dissipates 170 mW: within rating, but it leaves ~50 mA for the OLED plus Qwiic boards.
- **Chip ESD ratings (HBM):**

| Chip | Rating |
|---|---|
| MCP3208 | > 4 kV |
| M24C64 | 3 kV |
| TCA9555 | 2 kV |
| AHCT1G125 | 1 kV |

- **What protects the off-board lines:**
  - **Wipers:** 1 kΩ then 100 nF.
  - **Buttons:** 100 nF at the hole, then 1 kΩ.
  - **LED data:** 330 Ω.
  - **I2C and the +3V3A pot-top lead:** nothing.
- **What the references do:** in the circuits read here, none of Plaits, Marbles, O&C, the WSC, EuroPi, Ogham, the Daisy boards, the 4ms Sampler or Lich adds TVS diodes to pots, buttons, encoders or display lines. Mutable and EuroPi use bare wipers and switches, and the 4ms brainboard clamps only its buffered ADC path. RC networks, where present, are the protection, and ours are as good or better.

---

## 4. Comparison table

| Design | Pot value | Pot top | Wiper series R | Wiper C | Wiper pull-down | ADC / ratiometric | Buttons | Encoder | LEDs | Display bus |
|---|---|---|---|---|---|---|---|---|---|---|
| **Ours** | any (B10K and B100K both used by David) | +3V3A = MCP3208 VREF | 1 kΩ | 100 nF | **100 kΩ** | MCP3208, yes | 10k up, 100 nF at hole, 1 kΩ to TCA9555 | via TCA9555 + I2C INT | WS2812 via AHCT1G125 at 5 V, 330 Ω | I2C 400 kHz, 2.2 kΩ, shared with expander |
| Plaits v50 | 10kB | +3V3_A (LDO + L5) = VDDA | none | 100 nF | none | STM32 ADC, yes | direct, internal pull-up, 1 kHz s/w debounce | — | TLC59281 driver | — |
| Marbles v70 | 10kB | +3V3_A = VDDA | none | 100 nF | none | STM32 ADC, yes | direct, internal pull-up | — | GPIO + 1.5k/2.2k | — |
| Stages v70 | 10kB, 20kB slider | +3V3_A = VREF+ | none | none (4051 mux) | none | STM32 ADC, yes | direct | — | TLC59281 | — |
| Braids v50 | 10kB | −10 V LM4040 | 120–200k into op-amp | — | — | MCP3204 + 2.5 V ref, **no** | — | **direct GPIO, internal pull-up, no RC, 1 kHz** | — | 595 → 14-seg |
| O&C rev2e | — | — | — | — | — | — | 510 Ω + 100 nF, internal pull-up | **direct GPIO, no RC, 1 kHz** | — | **SPI** SH1106 + DMA |
| WSC Rev1.0 | B100K | +3V3 (ADC AVDD via 200 Ω/10 µF) | none | none | none | RP2040 via CD4052, ~yes | — (Z switch) | — | NPN from +12 V, PWM | — |
| EuroPi SMT | 10k | Pico 3V3 | none | none | none | RP2040, yes | **switch → 1k → node (10k up, 100 nF) → GPIO** | — | — | I2C 400 kHz, module pull-ups |
| Ogham | 10k | Seed 3V3_D | 1k | 100 nF | 100k | STM32 ADC, partly | direct, internal pull-up | **direct GPIO, 100 nF/line, 20 kHz poll** | — | TM1637 (2-wire) |
| Patch SM / patch.init | B10K | **+5 V out** | — (100k CV input) | — | — | STM32 via op-amp, **no** | direct, internal pull-up, 1 kHz | — | LED on CV out | — |
| Daisy Pod Rev5 | n/a | +3V3_A | none | none | none | STM32, yes | direct | **direct GPIO, no RC, 1 kHz** | RGB via 1K from GPIO | — |
| Daisy Patch Rev8 | 10k B | +3V3_A | 66K5 into summer | 10 nF feedback | — | STM32 via op-amp | — | **direct GPIO, no RC** | — | **SPI** OLED |
| Daisy Field rev4 | 10k B | +3V3_A | none (CD4051) | none | none | STM32, yes | direct | — | PCA9685 on I2C, 4K7 | **SPI** OLED |
| 4ms Sampler kit | B10k | **NCP51460 3.3 V ref = VREF+** | none on module; 10k on brainboard | 100 nF; then 10 nF + buffer | none | STM32 via follower, yes | 10k series + 100 nF | — | RGB via 330 Ω–2k | — |
| Befaco Lich v1 | B100K | −10 V LM4040 | 100k into summer | 100 pF feedback | — | STM32 via op-amp, no | direct, no debounce | **direct GPIO, 100 nF/line, timer quadrature** | GPIO + 470 Ω | 7-segment |
| Toepler+ | — | — | — | — | — | — | — | — | WS2812B via SN74LV1T125 at 5 V, 330 Ω | — |

---

## 5. Findings

Costs: Basic parts carry no fee; each new Extended part type costs $3.07 an order. Every part proposed below is **Basic** (verified 2026-10-15), so none of the findings adds an order fee.

### (A) Errors or risks: fix before ordering

**A1. Decide the encoder path; the current default (encoder on the TCA9555) loses steps whenever the OLED is being written.**
- **What:** the encoder's A/B are read over the same 400 kHz I2C bus as the OLED. A 128×64 full frame holds that bus for **23 ms**, during which the encoder is unsampled. Reads are also INT-driven, and the TCA9555 can drop an interrupt that arrives during the ACK of a read (§9.3.3). The expander inputs have no specified hysteresis, and the 100 nF RC slows release edges by 1.2 ms.
- **Evidence:** §3.2–3.3.
  - **No reference reads an encoder through an expander.** Braids, Yarns, O&C, Ogham, Daisy Pod, Daisy Patch, Lich, Muxlicer and the 4ms MetaModule all use direct GPIO, polled at 1–48 kHz or decoded by a hardware timer.
  - **Several references keep the OLED off the controls' bus.** O&C, Daisy Patch, Daisy Field and libDaisy put it on SPI; O&C also sends it by DMA.
  - **Commercial I2C encoders decode on a local microcontroller** (Adafruit seesaw).
- **Change. No new parts. Adopt both:**
  1. **Make gate inputs 3 and 4 the documented encoder route.** Common to a +3V3D hole; A → GIN3; B → GIN4; push → any SW hole. Firmware: PIO quadrature on Pico GP8/GP9, or QuadEncoder on Teensy pins 4/5.
     - Add a sheet note on sheets 7 and 8, and add +3V3D next to J801 in the wiring field if it is not already within reach.
     - Optional: 10 kΩ from each GIN hole to GND at the panel for 0.33 mA of contact current.
     - Use SPARE1/2 instead when a module has no MIDI and needs all four gate inputs.
  2. **For modules that do use the expander route** (e.g. a second encoder on Girl), adopt these firmware rules:
     - never hold the I2C bus for more than ~1 ms: send the OLED in ≤ 32-byte chunks, or a page at a time, with an expander read between;
     - park the TCA9555 pointer on Input Port 1 and read 1 byte (50 µs) whenever INT is **low**, treating INT as a level, not an edge;
     - also poll at 1 kHz as a backstop;
     - decode with a full state-transition table (pico-examples or Ogham), not an edge test;
     - debounce buttons in software (8-bit shift register at 1 kHz, as Mutable and O&C do).
- **Side effects:**
  - A module using route 1 has two gate inputs left, which covers every own build in the §3 audit.
  - The jack-detect probes PR13/PR14 are left unwired on that module.
  - At ~30–60 µA, contact current is below Bourns' filter circuit (0.5 mA). That is fine for gold-plated encoder contacts in practice, and is what internal pull-ups give in Braids and O&C. The panel-side 10 kΩ removes the doubt.

**A2. Change the eight wiper pull-downs from 100 kΩ to 1 MΩ.**
- **What:** R603, R605, R607, R609, R611, R613, R615, R617 → **1 MΩ 0402, C26083 (Basic, 2.06 M in stock, $0.0024)**.
- **Why:** with B100K pots, the 100 kΩ pull-down bends the response by up to **12.2 % of full scale** (498 LSB) at about ⅔ rotation; with B10K, 1.45 % (§3.1). David uses both values (MOD2 has three 100k pots), and so does the WSC (B100K). Ogham's 100k pull-down was paired with 10k pots only.
- **Result:** 1.45 % worst with 100k pots and 0.15 % with 10k pots. An unwired channel still decays to ≈ 0 V, with τ = 1 MΩ × 100 nF = 0.1 s.
- **Not chosen:** 470 kΩ is **Extended** (C25790), so it would add $3.07.
- **Side effects:**
  - At the MCP3208's worst-case leakage (±1 µA, typ 0.001 µA), an unwired channel could read up to 1 V. Typically it reads ~1 mV.
  - If exact linearity matters, firmware can invert the remaining bow given the pot value.

### (B) Worth adopting

**B1. Match EuroPi's real button topology: put the 1 kΩ between the hole and the RC node (all nine lines).**
- **What:** today the hole is the RC node and the 1 kΩ runs from the node to the expander pin. EuroPi (SW1 → R1 1K → BUTTON_1 with R5 10K up and C9 100nF → GP4) and Bourns' filter both put the series resistor **between the contact and the capacitor**.
- **Change:** hole SW*n* → 1 kΩ → node (10 kΩ to +3V3D, C to GND) → TCA9555 pin. Same parts, rewired in `sheet_expander`.
- **Why:**
  - It limits the capacitor-discharge current through the switch contacts to 3.3 mA, inside PEC11R's 10 mA rating. Today the contacts short a charged 100 nF directly.
  - It gives a controlled fall time (τ = 1k × C).
  - A pressed line sits at 3.3 × 1/11 = 0.3 V, below VIL (0.99 V).
- **Side effects:** none on parts or cost. The pin node is now driven only by the RC; a pin set as an output by mistake fights 10 kΩ, which is harmless.

**B2. Use 10 nF on the four Port 1 lines intended for encoders.**
- **What:** C706, C707, C708, C709 (SW5–SW8, on P14–P17) → **10 nF 50 V X7R 0402, C15195 (Basic, 6.3 M in stock)**.
- **Why:**
  - With B1's topology, the release delay to VIH drops from ~1.3 ms to ~0.13 ms, and the slow band through the expander's hysteresis-free threshold region drops from 0.85 ms to 0.08 ms.
  - Bourns' suggested filter is 10 nF.
  - SW5–SW8 can carry two encoders (Girl has two) and are read in one Port 1 byte.
- **Keep 100 nF on SW1–SW4 and SW9** for buttons and toggles.
- **How much it matters:** Lich and Ogham run 100 nF on their encoder lines with ~40 kΩ MCU pull-ups, which is slower than ours, and they work. They read the lines on Schmitt-trigger GPIO, at 20 kHz or with a hardware timer. This is an improvement for the expander route, not a rescue.
- **Side effects:** less hardware debounce on those four lines, so firmware debounce is required (it already is; see A1).
- **Label** J701 holes 5–8 as "encoder OK" on the sheet.

**B3. Give the pot reference its own node, isolated from the DAC8568's supply.**
- **What:** add **100 Ω 0805 (C17408, Basic)** from +3V3A to a new net **POT_REF**, and **10 µF 25 V 0805 (C15850, Basic)** from POT_REF to GND.
  - Move **U601 pin 15 (VREF)** and **J601 pins 9–10 (pot tops)** to POT_REF.
  - Keep U601 pin 16 (VDD) and the DAC8568 on +3V3A. Keep C603/C604 at VREF.
- **Why:**
  - Readings stay ratiometric, because VREF and the pot tops share one node.
  - Pickup on the hand-wired pot leads is filtered (corner **159 Hz**) before it reaches DAC8568 AVDD, which TI asks to keep "well-regulated and low noise" and optionally Pi-filtered.
  - A pot-top lead shorted to GND draws 33 mA through 100 Ω (109 mW, inside the 0805's 125 mW rating). The DAC's supply survives, instead of the XC6206 folding back.
  - The WSC does the same for its ADC (R60 200 Ω + C12 10 µF, "80Hz LPF on ADC power").
  - The 4ms Sampler kit goes further: its pot tops and the ADC's VREF+ share a dedicated NCP51460 3.3 V reference that powers nothing else.
- **Side effects:** POT_REF sits up to 0.28 V low with 8 × 10k pots (2.8 mA). That is harmless: the reading is ratiometric and VREF may be 0.25 V…VDD. Adds two Basic parts.
- **Not chosen:** a ferrite (BLM18PG121SN1D, C14709, Basic, already in the BOM) instead of 100 Ω filters only RF and gives no short protection.

**B4. LED wiring and current rules (documentation and firmware; optional cap change).**
- **Wiring rules:**
  - Run LED +5VD and GND as their own twisted pair from J704 to the panel LEDs, **never through the deck D bus** that carries pot and jack grounds. WS2812 PWM at ≥ 400 Hz puts LED current pulses in the audio band (§3.5).
  - Fit 100 nF at each LED (WS2812B application circuit), plus a bulk cap at the LED end of the run: 47–100 µF for a handful of LEDs (Adafruit asks 500–1000 µF for strips).
- **Firmware cap on total LED current:** e.g. ≤ 150 mA at 5 V, ≈ 70 mA from +12 V. Eight LEDs at full white would use ~227 mA of the module's +12 V budget.
- **Optional board change:** C713 10 µF → **47 µF 10 V X5R 1206, C96123 (Basic)** to stiffen +5VD against LED steps.
  - At 5 V bias this X5R part keeps maybe 20–25 µF (UNVERIFIED derating), still better than 10 µF.
  - Side effect: one more Basic part type, and a 1206 footprint.

### (C) Optional

- **C1. Qwiic and I2C pull-up etiquette (documentation).** Keep 2.2 kΩ on the board.
  - Tell users to cut the pull-up jumper on SparkFun Qwiic boards when another pull-up is on the bus (SparkFun's own rule). The board plus OLED plus one SparkFun board drops to 891 Ω, over the 3 mA Fast-mode sink spec.
  - Optional hardware: put R720/R721 behind a normally-closed solder jumper so they can be cut.
- **C2. Address clashes (documentation).** 0x20 (TCA9555) collides with MCP23017/PCF8574-type expander boards; 0x50 (M24C64) with EEPROM and FRAM breakouts. Note both in the wiring guide.
- **C3. EEPROM write protection.** WC tied low leaves calibration open to a stray write at 0x50. The alternative is WC pulled high with a test pad to ground during calibration. That adds hassle for a web-UI calibration flow, and there is no spare expander line, so leave it.
- **C4. MCP3208 stock.** C16939 has **595** in stock. Drop-in SOIC-16 fallbacks: MCP3208T-BI/SL C185809 (202), MCP3208T-CI/SL C626764 (256), MCP3208-BI/SL C2979740 (121). All Extended, so switching costs nothing extra. Check stock again on order day.
- **C5. +3V3D headroom.** The XC6206 at ≈ 50 mA plus an OLED (~20–30 mA, UNVERIFIED by module) leaves ~50 mA for Qwiic devices within its 250 mW. Don't hot-plug Qwiic devices: the inrush dips the rail that feeds the codec's digital side and the expander.
- **C6. A second 330 Ω at the first LED** (Adafruit's placement; SK6812MINI-E's ~500 Ω requirement). Fit it if the LED lead exceeds ~30 cm, or if an LED chain is ever powered from a supply other than +5VD. It is wired at the panel, so the board does not change.
- **C7. LED_DATA pull-down.** 100 kΩ 0402 (C25741, Basic) from U703 pin 2 to GND keeps the AHCT input defined (as its datasheet requires) and the LEDs dark when no module is fitted, e.g. at first power-up of a fresh board. The Pico holds the line low at reset anyway (RP2350 PDE = 1); the Teensy's reset pad state is UNVERIFIED.
- **C8. Panel-bus firmware notes.** The 74HCT595 shift register sees every MCP3208 frame, because SER = MOSI and SRCLK = SCK, so always shift a full gate word before pulsing RCLK. Keep SCLK ≤ 1 MHz while CS_POT is low.
- **C9. Pull-up rail.** R601 pulls CS_POT to +3V3D while U601 runs from +3V3A; if +3V3D rises first, ≤ 0.33 mA flows through U601's input clamp. Harmless. Moving R601 to +3V3A would tidy it.
- **C10. USB-only power.** A Pico on USB with rack power off will back-power panel-bus chips through their input clamps (UNVERIFIED severity, board-wide). Firmware can keep SPI-B and LED_DATA high-Z until the TCA9555 acknowledges.
- **C11. Schematic cosmetics.** On sheet 7, the "LED_BUF" label overlaps "LED_DIN" text at U703 pin 4.

---

## 6. Where the design is already right, and why

- **Ratiometric pots, with VREF and the pot tops on one rail.** This is the Mutable pattern: Plaits, Marbles and Stages all put the pot tops on +3V3_A = VDDA/VREF+. The 4ms Sampler does the same with a dedicated reference, and the Daisy Pod, Daisy Field and Seed3 DevKit put pot tops on +3V3_A. It makes the LDO's tolerance and drift irrelevant.
  - The Patch SM, by contrast, feeds pots from +5 V into a ±5 V CV input, which is not ratiometric.
- **The 1 kΩ + 100 nF wiper network.**
  - The 100 nF is the charge reservoir that makes the MCP3208's 1.5-clock S/H accurate (≤ 0.8 LSB kickback; §3.1), as in Plaits and Marbles.
  - It low-passes the hand-wired lead at 1.6 kHz.
  - The 1 kΩ limits clamp current if a wiper is ever mis-wired.
- **MCP3208 at ≤ 1 MHz SCLK on its own bus**, with a CS pull-up so it stays off MISO while the module boots. Both are datasheet-correct.
- **The TCA9555 itself.** INT open-drain with 10 kΩ ("typically 10 kΩ", datasheet §9.3.3); address strapped; 400 kHz within spec. The 1 kΩ in each line protects the pin if firmware ever configures it as an output. Button values (1k/10k/100 nF) are EuroPi's; only their order differs (B1).
- **The WS2812 level shifter.** A 74AHCT part at 5 V is exactly what Adafruit names, and Toepler+ uses the equivalent SN74LV1T125. It meets WS2812B's 0.7 × VDD, which a 3.3 V GPIO cannot. 330 Ω sits inside the 300–500 Ω guidance, and the 100 nF at the buffer is right.
- **I2C 2.2 kΩ.** Right for 400 kHz up to ~150 pF (tr 280 ns), which is what one cabled OLED plus a Qwiic lead comes to. It matches SparkFun's 3.3 V choice. EuroPi has no board pull-ups at all, which is worse.
- **The Qwiic connector** pinout matches the STEMMA QT/Qwiic standard.
- **The M24C64** at 0x50 runs at 400 kHz (1 MHz capable), is rated 3 kV ESD, and is the Workshop Computer's scheme in a larger part.
- **ESD.** No reference adds TVS to panel controls. The RC networks (1 kΩ/100 nF on wipers, 100 nF/1 kΩ on buttons, 330 Ω on LED data) are the established protection, and ours match or exceed the references'.

---

## 7. Sources

**Our design**
- `tools/analogue_board/design_digital.py` (sheets 6–8), `design.py` (pin map lines 23–50; rails lines 293–294, 312), `design_analog.py:262-267`.
- `hardware/analogue_board/analogue_board_schematic.pdf`, pp. 6–8.
- `docs/analogue_board_spec.md` §3, §6, §7, §15; `docs/mod2_reference_review.md:239`.

**Datasheets**

| Part | Source |
|---|---|
| MCP3204/3208 | Microchip DS21298E: https://ww1.microchip.com/downloads/en/DeviceDoc/21298e.pdf |
| TCA9555 | TI SCPS200E: https://www.ti.com/lit/ds/symlink/tca9555.pdf |
| M24C64 | ST: https://www.st.com/resource/en/datasheet/m24c64-r.pdf |
| SN74AHCT1G125 | TI: https://www.ti.com/lit/ds/symlink/sn74ahct1g125.pdf |
| XC6206 | Torex: https://www.torexsemi.com/file/xc6206/XC6206.pdf |
| DAC8568 | TI SBAS430: https://www.ti.com/lit/ds/symlink/dac8568.pdf |
| RP2350 | https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf |
| SSD1306 | https://cdn-shop.adafruit.com/datasheets/SSD1306.pdf |
| Bourns PEC11R | https://www.bourns.com/docs/Product-Datasheets/PEC11R.pdf |
| WS2812B | https://cdn-shop.adafruit.com/datasheets/WS2812B.pdf; https://www.luxalight.eu/sites/default/files/downloads/2020-03/Datasheet_WS2812B.pdf |

**Reference designs**
- **Mutable Instruments:** https://github.com/pichenettes/eurorack (commit f4cfa76). Schematics: https://pichenettes.github.io/mutable-instruments-documentation/modules/plaits/downloads/ (likewise for marbles, stages, braids, yarns).
- **Ornament & Crime:** https://github.com/mxmxmx/O_C (master cfbffab); Phazerville https://github.com/djphazer/O_C-Phazerville (195932a).
- **Workshop System Computer:** https://github.com/TomWhitwell/Workshop_Computer (4fdefdd): `documentation/computer_Rev_1_0_0_Schematic.pdf`, `ComputerCard.h`.
- **EuroPi:** https://github.com/Allen-Synthesis/EuroPi (1192d31): `hardware/surface-mount/europi-surface-mount.kicad_sch`, `software/firmware/`.
- **Ogham:** local `/Users/dbaghurst/GitHub/ogham` (776e8d2): `hardware/ogham-merged-v1.0/ui.kicad_sch`, firmware `ogham_controls.*`, `ogham_main.cpp`.
- **Electrosmith:** github.com/daisyaudio (formerly electro-smith). Schematic PDFs (Pod Rev5, Patch Rev8, Field rev4, Patch SM datasheet v1.0.5 and schematic, Seed3 DevKit Eurorack Rev3), from docs.daisy.audio. libDaisy: https://github.com/electro-smith/libDaisy, now under daisyaudio (master f715e48).
- **4ms:** https://github.com/4ms/mp153-brainboard-pcb (2f914ef); 4ms mdrivlib (a91dcf9); 4ms metamodule (e44c259); 4ms sampler firmware and Kit-Trig-Sampler PCB (exact repo URLs UNVERIFIED in this pass).
- **Befaco:** Lich v1, Oneiroi and Muxlicer schematics and BOMs; firmware is Rebel Technology OpenWare (https://github.com/RebelTechnology/OpenWare; exact branch UNVERIFIED in this pass).
- **Sluisbrinkie Toepler+:** https://github.com/niektb/sluisbrinkie-eurorack-published (9a2c1f5).
- **8Bit EuroRack 7hp:** https://github.com/8BitMixtape/8Bit_EuroRack-7hp (af796ba).

**Guidance and libraries**
- **Adafruit:**
  - NeoPixel Überguide: https://learn.adafruit.com/adafruit-neopixel-uberguide/best-practices and https://learn.adafruit.com/adafruit-neopixel-uberguide/powering-neopixels
  - STEMMA QT spec: https://learn.adafruit.com/introducing-adafruit-stemma-qt/technical-specs
  - I2C QT Rotary Encoder: https://learn.adafruit.com/adafruit-i2c-qt-rotary-encoder/overview
- **SparkFun:**
  - Qwiic: https://www.sparkfun.com/qwiic
  - Qwiic OLED pull-ups: https://github.com/sparkfun/SparkFun_Qwiic_OLED_1.3in/blob/main/docs/hardware_overview.md
- **Raspberry Pi PIO quadrature decoder:** https://github.com/raspberrypi/pico-examples/blob/master/pio/quadrature_encoder/quadrature_encoder.pio
- **Teensy 4.x QuadEncoder:** https://github.com/mjs513/Teensy-4.x-Quad-Encoder-Library
- **JLCPCB parts API**, queried 2026-10-15. Basic: C26083, C15195, C17408, C15850, C96123, C25741, C22775, C22808, C45783. Extended: C25790, C16939, C185809, C626764, C2979740, C465732, C7484, C79988, C160404.

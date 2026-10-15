# TRS MIDI in and out for the analogue board, Rev A

Review, 2026-10-15. Context: `docs/analogue_board_spec.md` v0.3 (§1 "No MIDI circuit in Rev A",
§3 item 9, §4.2, §5, §6.3, §15), `docs/n8synth_platform.md`, `tools/analogue_board/design.py`
(PINMAP rows SPARE1/SPARE2, hole group J101 on the root sheet).

**Marks:** † means not verified against a primary source in this pass. Stock and prices are from
the JLCPCB parts API (`selectSmtComponentList`) on 2026-10-15, at qty 10, and will drift.
Downloads and rendered crops of every schematic quoted below were working copies for this
review and are not kept; each source is cited with its URL and page.

---

## 0. The answer in one page

- **MIDI IN:** H11L1 opto on +3V3D, the circuit Electrosmith, Adafruit and AMYboard all ship.
  220 Ω in series, a 1N4148WS across the LED backwards, 1 kΩ pull-up, then 1 kΩ in series to a
  **link hole** beside SPARE2.
- **MIDI OUT:** buffered at **5 V**, not direct from the 3.3 V pin. A second 74AHCT1G125 (the
  part already used for the WS2812s, so no new fee). Each leg is 200 Ω made of two 100 Ω 1206
  resistors, with a BAT54S clamp on the buffer output. Its input comes from a **link hole** beside
  SPARE1, with a 10 kΩ pull-up.
- **Coexistence:** both circuits end in link holes 2.54 mm from the SPARE1 and SPARE2 holes, open
  by default. A jumper shunt or wire link turns MIDI on. With the links open, SPARE1 and SPARE2 are
  untouched plain GPIO. No module pin ever sees more than +3V3D, always through ≥ 1 kΩ.
- **Jacks:** stereo (TRS) jacks in two deck cells. Type A by the hole labels. **Type B = swap two
  wires**, so no jumper. **MIDI IN sleeve: not bridged to D.** Wire it to a hole with 100 nF to
  ground (the CA-033 option), or leave it open. MIDI OUT sleeve to D as usual.
- **No hardware THRU.** Firmware can echo IN to OUT.
- **Cost:** one new Extended part type (H11L1SR2M, C20082: +$3.07 an order), about $0.73 of parts
  a board. Pin map: no module pin changes. 26 nets stay 26.

---

## 1. The specifications

### 1.1 CA-033, MIDI 1.0 Electrical Specification Update (MMA/AMEI, approved 2014-01-20, issued 2014-08-01)

Source: midi.org PDF (§9). Read in full. What matters here:

| Topic | What CA-033 says (quoted or table values) |
|---|---|
| Signal | 31.25 kbaud ±1 %, 8-N-1, "a 5mA current loop; logical 0 is current ON". "One output shall drive one and only one input." |
| Receiver | Opto-isolated. "Sharp PC-900V and HP 6N138 opto-isolators have been found acceptable. Other high-speed opto-isolators may be satisfactory. The receiver must require less than 5 mA to turn on. Rise and fall times should be less than 2 microseconds." RB = 220 Ω in the loop, D1 1N914 across the LED as "reverse voltage protection" (Figure 2). RD (pull-up) "depends on opto-isolator and VRX". |
| Sender resistors (Figure 1) | VTX = **+5 V ±10 %: RA 220 Ω 5 % 0.25 W, RC 220 Ω 5 % 0.25 W**. VTX = **+3.3 V ±5 %: RA 33 Ω 5 % 0.5 W, RC 10 Ω 5 % 0.25 W**. RA goes from VTX to pin 4 (source); RC goes from the UART/buffer to pin 5 (sink). |
| Buffer | "The buffer between the UART transmitter and RC is optional and system-dependent", "may be implemented as an IC gate or transistor". |
| Short circuits | "It is required to have short-circuit current-limiting on the MIDI Output". At 3.3 V the short through RA is 111 mA, 0.383 W, "This requires using a 0.5W resistor". |
| 3.3 V caveat | 3.3 V senders may not work with "non-opto-isolated receivers and devices that draw power from Pin 4". |
| **IN shield / pin 2** | "Pin 2 of the MIDI In connector shall not have any DC path to the receiver's ground. However, a connection through a small capacitor (0.1μF typical) to ground is optional." Same for the IN jack's shield. "But it is still not permitted to connect the grounding shield connector of a MIDI in jack directly to ground." |
| OUT shield | "Pin 2 must be tied to ground on the MIDI transmitter only." OUT/THRU shields may be N/C or grounded. |
| THRU | Optional. Opto delay "will tend to add up"; chains beyond three devices need faster optos. |
| EMC | Optional ferrite beads, 1 kΩ at 100 MHz (MMZ1608Y102BT), near the jacks. |

Worst case for CA-033's own 3.3 V values: 4.47 mA (−5 % supply, +5 % resistors, 1.9 V drop).
Typical: about 7.2 mA.

### 1.2 RP-054, Specification for Use of TRS Connectors with MIDI Devices (MMA approved 2018-06-08, AMEI 2018-07-18)

Source: midi.org page, PDF via its Google Drive link (§9). Two pages, read in full.

- **Pin-out (female TRS against female DIN): Tip = pin 5 (current sink), Ring = pin 4 (current
  source), Sleeve = pin 2 (shield).** The cable drawing gives the same: Tip → Pin 5, Ring → Pin 4,
  Sleeve → Pin 2.
- RP-054 never uses the words "Type A". The trade calls this mapping **Type A** (Korg, Make
  Noise, Intellijel) and the swapped one **Type B** (Arturia, Novation, older 1010music). Sources:
  Ksoloti's Big Genes page, Doudoroff's survey.
- "The MIDI In/Out circuitry should be implemented in accordance with … CA-033."
- "Because TRS connectors are often used for other (non-MIDI) purposes, manufacturers are
  **strongly advised to add protection circuitry** (e.g. to handle the case when a DC-coupled
  headphone driver is connected to a MIDI output)."
- 2.5 mm TRS is recommended, but "If any other connector size is used, the remainder of this
  specification still applies". Eurorack uses 3.5 mm.
- Cables must be shielded twisted pair. Adapters ≤ 2 m. "Direct connection between two
  TRS-equipped devices using cables designed for use with audio equipment is not acceptable".

### 1.3 The receiver ground rule, in plain words

A MIDI cable joins two boxes. If both ends of its shield were grounded, the shield would carry
current between the two boxes' grounds (a ground loop), and that current is hum. So the shield is
grounded **only at the sender**. The receiver sees the data only as light inside the opto: no
copper joins the two grounds. The 100 nF option keeps that isolation at audio frequencies (26.5 kΩ
at 60 Hz) while shorting radio-frequency noise (0.16 Ω at 10 MHz). These figures are CA-033's own.

---

## 2. Reference designs, with evidence

Each was read from its own schematic: rendered and cropped for the PDFs, parsed netlists for the
Eagle files.

### 2.1 Electrosmith Daisy Patch Rev8 (Eurorack, TRS in/out). `ES_Daisy_Patch_Rev8.pdf`, 2025-03-13, sheet 1, MIDI block
Read from schematic page 8.
- **IN:** tip/ring → four 0 Ω links R78 (DNI), R79 0R, R83 0R, R84 (DNI). As fitted, **ring →
  MIDI_IN_A → R63 220R → opto pin 1 (A)** and **tip → MIDI_IN_B → opto pin 2 (C)**, i.e. **Type
  A**. Moving R79/R83 to R78/R84 gives Type B. **D5 1N4148** reverse across the LED.
- **Opto:** pins 1 A, 2 C, 4 OUT (with an inverting bubble), 5 GND, 6 V. That is the H11L1
  pinout, but **no part number is printed** on this sheet. Taken as H11L1-family because of the
  pinout, the same 270 Ω as Electrosmith's named H11L1 (§2.4), and a forum reply that the Pod uses
  "On Semi H11L1SR2" †. Supply **+3V3_D**, **R64 270R pull-up**, C16 100 nF → USART1_RX.
- **OUT:** **R1 33R from +3V3_D to ring**, **R2 10R from USART1_TX to tip**. CA-033's 3.3 V
  values, direct from the MCU pin with no buffer. The Seed's STM32 pins are 5 V tolerant; the
  Teensy 4.1's are not.
- **Sleeves:** both jacks "GND" → **GND**. The IN sleeve is grounded, against CA-033.

### 2.2 Electrosmith Daisy Field Rev4 (desktop, TRS). `daisy_field_schematic_rev4.pdf`, 2020-09-22
Same circuit and designators as the Patch: R63 220R, R64 270R,
**D5 1N4148WS**, C11 100 nF, R78/R79/R83/R84 A/B links, **R54 33R / R55 10R** out. Both sleeves
GND.

### 2.3 Electrosmith Daisy Pod Rev5 (desktop, TRS in only). `ES_Daisy_Pod_Rev5.pdf`, 2022-10-27
Crops: `pod_midi-1.png`, `pod_j1-1.png`. Same as the Patch, but D5 is an **NSR1020MW2T3G
Schottky**. J1 (SMT stereo 3.5 mm) pin 1 sleeve → **GND**. Forum (community.daisy.audio t/8778,
Sept 2025): "Same optocoupler as the Pod: On Semi H11L1SR2" †; "As shipped, it is set up for Type
A"; "Move two resistors to the DNI locations for Type B."

### 2.4 Electrosmith Seed3 DevKit Eurorack Rev3 (Eurorack, TRS in/out/thru). `Seed3-DevKit-Eurorack-Rev3.pdf`, sheet 3, plus the production BOM
Values checked against the Rev3 BOM.
- **IN:** ring (MIDI_IN_4) → **R4 220R** → **U11 H11L1** pin 1; tip (MIDI_IN_5) → pin 2.
  **D3 NSR1020MW2T3G** reverse across. Type A, no links. +3V3, **R3 270R** pull-up, C1 100 nF.
  The BOM gives `H11L1, U11, Package_DIP:DIP-6_W7.62mm`, a through-hole part.
- **OUT:** **R10 10R from +3V3 to ring**, **R59 10R from MIDI_TX to tip**. **THRU:** R6 10R
  from +3V3 to ring, **R29 10R from MIDI_RX (the opto output) to tip**, so a hardware THRU with no
  buffer. Resistors are 0603 (BOM).
- **IN sleeve → C47 100 nF → GND**: the CA-033 option, and the only Eurorack TRS reference here
  that follows the IN rule. OUT and THRU sleeves → GND.
- **Finding (my arithmetic):** with 10 Ω on the ring, a mono patch cable in OUT or THRU shorts
  +3V3 through 10 Ω: 330 mA and 1.1 W in a 0.1 W 0603. CA-033 asks for 33 Ω 0.5 W for this reason.

### 2.5 AMYboard v1.5 (shorepine/tulipcc; Eurorack, ESP32-S3, TRS in/out). `docs/pcbs/amyboard/amyboard-v1.5.sch` (Eagle XML, parsed)
- **IN:** tip/ring → **MB14F bridge rectifier** (40 V, 1 A) → DC+ → **R36 220R** → **U15
  H11L1SR2M** anode; DC− → cathode; **D13 1N4148WS** reverse across. **Automatic Type A/B.**
  VCC +3V3, **R35 470R** pull-up → ESP32 IO21.
- **OUT:** tip ← **R37 22R** ← IO14; ring ← **R38 22R** ← IO15, all 0402. Firmware
  (`tulip/shared/amy_connector.c` `amyboard_set_midi_out`) routes UART TX to one pin and drives the
  other high as the source: "Type A = pin 14, Type B = pin 15". Software A/B, at the cost of a
  second GPIO.
- **Sleeves:** `MIDI_IN.EARTH` and `MIDI_OUT.EARTH` → **GND**.

### 2.6 Mutable Instruments Yarns v03 (Eurorack, DIN). `yarns_v03.pdf` sheet 1
**OK1 6N137SMT on +3V3**, below the 6N137's 4.5–5.5 V
datasheet range but shipped for years. **R37 10k** pull-up. DIN pin 4 → **R35 220** → pin 2
(anode); pin 5 → pin 3. **D3 1N4148** reverse. **IN pin 2 not connected.** OUT: **R39 51 Ω from
+3V3 to pin 4**, R40 51 Ω from MIDI_TX to pin 5 (pre-CA-033 3.3 V values); OUT pin 2 → GND.

### 2.7 Adafruit MIDI FeatherWing (DIN plus optional 3.5 mm TRS). `Adafruit MIDI FeatherWing.sch` (Eagle XML, parsed)
- **OK2 H11L\*M, device "S"** (SMT, i.e. H11L1SM †), VCC 3.3 V, **R3 470 Ω** pull-up → MIDI_RX.
  IN_SOURCE (DIN 4, TRS X1 pads 2/3) → **R2 220** → anode; IN_SINK (DIN 5, X1 pads 4/5) →
  cathode. **D1 1N4148** SOD-323 reverse.
- **OUT:** **R1 33 Ω from 3.3 V to OUT_SOURCE**, **R4 10 Ω from MIDI_TX to OUT_SINK**: CA-033
  exactly.
- **Sleeves:** **MIDIIN pin 2 and X1 pad 1 (IN TRS sleeve) are on no net: floating, as CA-033
  says.** MIDIOUT pin 2 and X2 pad 1 → GND. Type A if the jack's pads 2/3 are the ring †
  (Kycon STX3100 / CUI SJ1-3555NG numbering not checked).

### 2.8 Ksoloti power-MIDI board v0.2/0.3 (DIN, Ksoloti Core accessory, JLC-assembled). `ksoloti-power-midi-board.pdf` + JLC BOM
- **OK1 6N137 (Everlight 6N137S(TA), C16496) on +5 V**, **R1 10k** pull-up to +5 V (the STM32
  pin is 5 V tolerant). **R2 220**, **D2 1N4148WS (C2128)**. IN pin 2 not connected.
- **OUT: two 74HC14 sections in series (a non-inverting buffer) at 5 V, R8 220 → pin 5, R7 220
  from +5 V → pin 4**. THRU: the same from MIDI_RX to a header. 220 Ω are 0603 (C22962).
- This is the same family as David's Big Genes, but **not** its circuit. The Big Genes circuit
  is unpublished. Its page says **"1 TRS MIDI input jack, type A and B compatible"** and **"1 TRS
  MIDI output jack, Type A"**.

### 2.9 PJRC Teensy MIDI library page (Teensy 3.x/4.x)
PJRC's Teensy 3 MIDI wiring image. **6N138 on 5 V (VIN)**, output pulled up by **470 Ω to the
Teensy's 3.3 V**. That pattern is the key one for a 3.3 V-only MCU: the pull-up goes to the
logic rail, not to the opto's supply. 220 Ω, 1N4148, IN pin 2 N/C. OUT: **47 Ω / 47 Ω** from
3.3 V. Text: "6N138 and some 6N139 optocouplers may be used instead of PC900 / H11L1."

### 2.10 Befaco MIDI Thing V2: hardware not published
`github.com/Befaco/MIDIThing2` contains only `README.md` (checked via the GitHub tree API): Teensy
4 + MAX11300, "TRS MIDI connectivity". Retail listings say TRS Type A †. Nothing to read.

---

## 3. Comparison

| Design | Jack | Opto (supply) | Pull-up | Series R (IN) | Reverse diode | OUT drive | OUT R (ring / tip) | IN sleeve | A/B | THRU |
|---|---|---|---|---|---|---|---|---|---|---|
| Daisy Patch Rev8 | TRS | H11L1-type † (3.3 V) | 270 Ω | 220 Ω, source side | 1N4148 | MCU pin direct | 33 Ω / 10 Ω | **GND** | 0 Ω links, ships A | — |
| Daisy Field Rev4 | TRS | H11L1-type † (3.3 V) | 270 Ω | 220 Ω | 1N4148WS | MCU pin direct | 33 Ω / 10 Ω | **GND** | 0 Ω links | — |
| Daisy Pod Rev5 | TRS (IN) | H11L1SR2 † (3.3 V) | 270 Ω | 220 Ω | NSR1020 Schottky | — | — | **GND** | 0 Ω links | — |
| Seed3 DevKit Eurorack Rev3 | TRS | **H11L1** DIP-6 (3.3 V) | 270 Ω | 220 Ω | NSR1020 Schottky | MCU pin direct | **10 Ω / 10 Ω** | **100 nF** | A only | **Yes, from opto output** |
| AMYboard v1.5 | TRS | **H11L1SR2M** (3.3 V) | 470 Ω | 220 Ω after bridge | 1N4148WS | two MCU pins | 22 Ω / 22 Ω | **GND** | **Bridge (IN), firmware (OUT)** | — |
| Mutable Yarns v03 | DIN | 6N137 (3.3 V, out of spec) | 10 kΩ | 220 Ω | 1N4148 | MCU pin direct | 51 Ω / 51 Ω | **N/C** | n/a | — |
| Adafruit MIDI FeatherWing | DIN + TRS | **H11L1(S)M** (3.3 V) | 470 Ω | 220 Ω | 1N4148 | MCU pin direct | **33 Ω / 10 Ω** | **N/C** | A † | — |
| Ksoloti power-MIDI | DIN | 6N137 (5 V) | 10 kΩ to 5 V | 220 Ω | 1N4148WS | **74HC14 at 5 V** | **220 Ω / 220 Ω** | **N/C** | n/a | Yes (buffered) |
| PJRC Teensy | DIN | 6N138 (5 V) | 470 Ω **to 3.3 V** | 220 Ω | 1N4148 | MCU pin direct | 47 Ω / 47 Ω | N/C | n/a | — |
| **This board (proposed)** | TRS | **H11L1SR2M (3.3 V)** | **1 kΩ** | **220 Ω** | **1N4148WS** | **74AHCT1G125 at 5 V** | **200 Ω / 200 Ω** | **100 nF hole, not D** | **Wiring** | **None (firmware)** |

What the table says:
1. **The H11L1 on 3.3 V is the established TRS-Eurorack receiver.** It appears in five of the
   designs, three with explicit part numbers, and it is in JLC stock as an SMD part.
2. **Every 3.3 V design drives the jack from the MCU pin.** The Daisy's STM32 has 5 V-tolerant
   (FT) pins. AMYboard's ESP32-S3 is not 5 V tolerant †, so it accepts the risk. The only buffered
   sender is the 5 V Ksoloti design.
3. **Three of the four Eurorack TRS designs ground the IN sleeve.** Only the Seed3 DevKit follows
   CA-033, with 100 nF. All the DIN designs leave pin 2 open.
4. **Type A/B:** the Electrosmith boards use 0 Ω links and AMYboard uses a bridge plus firmware.
   The rest are fixed. Hardware THRU appears on two of the nine designs.

---

## 4. Optocoupler choice (3.3 V, 31.25 kbaud)

| Part | LCSC | Package | JLC | Stock | $@10 | Supply | Turn-on current (max) | Speed | Output | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| **onsemi H11L1SR2M** | **C20082** | SMD DIP-6 (gull-wing) | Extended | 15,574 | 0.53 | **3–15 V** | **1.6 mA** | ton/toff ≤ 4 µs, tr/tf 0.1 µs typ | Open collector, Schmitt | **Chosen.** Proven at 3.3 V (AMYboard, Electrosmith, Adafruit) |
| onsemi H11L1SM | C899473 | same | Extended | 2,707 | 0.54 | 3–16 V | 1.6 mA | same | same | Second source (tube) |
| Everlight H11L1S(TA)-V | C6569443 | SMD-6P | Extended | 1,770 | 0.37 | 3–15 V | 1.6 mA | 4 µs | same | Third source † (footprint check) |
| onsemi H11L1M | C16587 | DIP-6 THT | Extended | 11,200 | 0.38 | 3–15 V | 1.6 mA | 4 µs | same | Through-hole: not for SMT assembly |
| Toshiba TLP2361 | C107626 | SO-5 | Extended | 8,510 | 0.41 | **2.7–5.5 V** | 1.6 mA | 15 Mbps | Totem-pole | Good modern 3.3 V part, ~2.3 mm tall; in no reference here |
| Toshiba TLP2362 | C37658 | SO-5 | Extended | 20,206 | 0.37 | 2.7–5.5 V | 5 mA † | 10 Mbps | Open collector | Turn-on too high for MIDI's "< 5 mA" |
| 6N137 (onsemi/Everlight) | C5344 / C15825 / C16496 | DIP-8 / SMD-8 | Extended | 14–25 k | 0.27–0.70 | **4.5–5.5 V** | 5 mA | 10 Mbps | Open collector | Needs 5 V. At 3.3 V out of spec (Yarns does it). Turn-on at the 5 mA limit |
| Lite-On 6N137-L | C92648 | DIP-8 THT | Extended | 1,007 | 0.31 | 2.7–5.5 V | — | 15 Mbps | OC | Through-hole only |
| 6N138 | C571211 / C3001991 / C188666 | DIP-8 / SMD | Extended | 318 / 170 / 1 | 0.35–2.04 | 5 V † | low | slow, pin 7 R | Darlington | Poor stock; CA-033's named part, but not for this order |
| 6N139S(TA) | C142364 | SMD-8 | Extended | 19,811 | 0.36 | 5 V † | low | slow | Darlington | Possible, unproven at 3.3 V here |
| Sharp PC900V | C2914011 | SMD-6 | Extended | **0** | — | — | — | — | — | Not stocked |
| PC817 / EL817 / EL3H7 | C41807 / C63268 / C92243 | SMD-4 | Extended | 198k–382k | 0.04–0.09 | — | — | ton/toff 3–18 µs into 100 Ω, worse into a real pull-up | Phototransistor | **Too slow**: CA-033 wants rise/fall < 2 µs |

No optocoupler at JLC is Basic, so any choice costs one $3.07 fee.

**H11L1M datasheet facts** (onsemi/Fairchild Rev 1.0.7, via LCSC C20082):
- Pinout: 1 anode, 2 cathode, 3 NC, 4 VO, 5 GND, 6 VCC.
- Truth table: input H → output **L**. So current ON (MIDI "0") gives a low output (UART "0"):
  **no inversion needed**.
- VCC 3–15 V. IF(on) ≤ 1.6 mA at 5 V. Fig. 4 shows the threshold *falls* to about 0.85× at 3.3 V.
- VOL ≤ 0.4 V at 16 mA. IO max 50 mA. LED IF max 30 mA, **VR max 6 V** (hence the reverse diode).
- Note 2 asks for a 10 % guard band on IF(on).

**Margin:** a worst-case CA-033 3.3 V sender gives (3.135 − 1.9) / (45.15 + 231) = **4.5 mA**
into our 220 Ω. A typical one gives about 7 mA. The worst-case need is 1.6 mA × 1.1 (guard) × 1.1
(50 °C, Fig. 5) ≈ **1.94 mA**: more than 2× margin.

---

## 5. Decisions and reasons

### 5.1 MIDI OUT: buffered at 5 V, 200 Ω per leg [recommended]

Direct from the 3.3 V pin (33 Ω / 10 Ω, as Electrosmith and Adafruit do) is rejected for this
board:
1. **The Teensy 4.1 is not 5 V tolerant** (spec §5). With direct drive, only 10 Ω separates the
   module pin from the jack tip. In Eurorack, someone *will* patch a gate or CV into that jack.
   RP-054 itself "strongly advise[s]" protection.
2. **The mono-cable short.** A mono patch cable in a TRS jack shorts ring to sleeve. At 3.3 V
   that pulls ~100 mA through RA (CA-033: 0.383 W, a ½ W part) from **+3V3D**. That rail is the
   200 mA XC6206 that also feeds the PCM3060 VDD and the ADS8688 DVDD (§8, §15). At 5 V with 200 Ω
   the same short draws 25 mA from the 2 A buck.
3. **Compatibility.** CA-033 warns that 3.3 V senders may fail with non-opto receivers and with
   receivers powered from pin 4. 5 V works with everything.
4. **No new part type.** The SN74AHCT1G125DBVR (C7484) is already U703, the WS2812 buffer. A
   second one costs $0.10 and no fee. It follows the spec's rule (§5) that "5 V parts only take
   3.3 V in and drive jacks or LEDs, never a module pin". Its input has no clamp to VCC (TI:
   "VI −0.5 to 7 V", input clamp only for VI < 0), so it cannot back-feed anything.

**Resistors:** CA-033 asks for 220 Ω ¼ W at 5 V. A ring short then puts 5.07² / 220 = 117 mW in
RA. JLC has no Basic 220 Ω 1206, and the Basic 0805 (C17557) is rated 125 mW, too close. So
**each leg is two 100 Ω 1206 in series (C17901, Basic, ¼ W each)**: 64 mW per resistor in a short,
4× margin. Loop current into a standard receiver is (5.07 − 1.2 − 0.25) / (200 + 200 + 220) ≈
**5.8 mA**. Worst case (−2 % rail, 1.9 V drop, VOL 0.36 V, tolerances) is ≈ **4.3 mA**, the same
as CA-033's own worst case for either voltage. The spec-exact alternative is one **220 Ω 1206
(C17957, Extended, +$3.07)** per leg.

**Clamp:** BAT54S (C408389, already on the BOM for the gate ins) on the buffer side of the tip
resistors, to +5VD and GND. A ±12 V source then pushes at most (12 − 5.4) / 200 ≈ 33 mA, which
the Schottky takes before the AHCT's own diodes (IOK ±20 mA abs max). A typical Eurorack output
(470 Ω–1 kΩ) pushes under 10 mA. The ring is held at +5VD through its 200 Ω, and the rail absorbs
anything pushed into it.

### 5.2 Coexistence with SPARE1 and SPARE2 [recommended: link holes, open by default]

| Option | Verdict |
|---|---|
| Normally-closed jumpers | **No.** The opto pull-up would always load SPARE2 and the buffer input SPARE1; using them as GPIO would mean cutting a trace |
| Normally-open SMD solder jumpers | Works, but a solder blob on an SMD jumper is less reversible and adds a footprint type |
| **Link holes at 2.54 mm beside the SPARE holes** | **Yes.** Fits the board philosophy (channels end in holes; David decides). Takes a wire link *or* a 2-pin header with a jumper shunt (reversible) |

Make J101 a 2 × 2 block: **[SPARE1][MIDI_TX]** and **[SPARE2][MIDI_RX]**, plus the existing RUN
and GND holes.

How the parts protect SPARE1 and SPARE2:
- **Link open:** nothing MIDI touches SPARE1 or SPARE2. The MIDI side idles safely: the TX node
  is pulled up by 10 kΩ, so the buffer output is high and no loop current flows. The opto output
  is simply pulled up.
- **The opto's pull-up cannot fight SPARE2:** it sits on the MIDI side of the link. Even when
  linked, a 1 kΩ series resistor separates the opto node from SPARE2. If firmware wrongly drives
  SPARE2 as an output against the opto's low, the current is ≤ 3.3 mA.
- **No back-feed into the Teensy:**
  - every module-facing MIDI node is pulled to **+3V3D at most**, through **≥ 1 kΩ** (RX) or
    **10 kΩ + 1 kΩ** (TX). The 5 V buffer only listens to TX;
  - power sequencing: if +3V3D rises before the Teensy's own 3.3 V, at most (3.3 − 0.5) / 2 kΩ ≈
    1.4 mA flows into a pin clamp. It is brief and small;
  - Teensy on USB with the rack off (VIN–VUSB cut, §5): its TX high feeds 0.3 mA into the dead
    +3V3D through 10 kΩ. Harmless;
  - this follows the board's own precedent: the gate-in comparators already pull module pins up
    to +3V3D through 10 kΩ (§7).
- **Boot:** the 10 kΩ pull-up wins over the RP2350's ~50 kΩ default pull-down (2.75 V, above the
  AHCT's 2.0 V VIH †). No spurious bytes while the module boots.

### 5.3 The deck sleeve problem [recommended: IN sleeve not on D]

- **Spec:** the IN sleeve gets no DC path to ground; 100 nF to ground is optional (§1.1).
- **Practice:** Electrosmith Patch, Field and Pod and AMYboard ground it. The Seed3 DevKit uses
  100 nF. Adafruit, Yarns, PJRC and Ksoloti leave it open (§3).
- **Is it a real issue?** Inside one rack, no. Every module already shares the bus ground, and
  every patch cable joins grounds anyway. A grounded MIDI IN sleeve between the Big Genes and this
  board adds nothing new, and that is why Eurorack makers get away with it. It becomes real when
  the sender is **outside the rack on its own mains earth**: a computer MIDI interface, or a
  keyboard through a TRS-to-DIN adapter. A grounded IN sleeve then closes a ground loop through the
  cable shield, the hum the opto exists to prevent. It costs nothing to do it right.
- **On the deck:** the n8synth board profile says "Bridge a cell's spare A/B/C solder point to D
  for local grounds" (`tools/visualizer/boards/n8synth-6hp.json`, groundBus note; a generated
  file, not in the verified platform doc †). So a jack's sleeve reaches D only through a bridge
  David makes. For the **MIDI IN** cell, **do not bridge the sleeve's pad to D**. Run that pad's
  edge position to the board's **MI_S** hole (100 nF to GND), or leave it unconnected. The **MIDI
  OUT** sleeve goes to D as normal (CA-033 allows a grounded OUT shield).
- **Mono or stereo jack:** it must be a **stereo (TRS) jack**. A mono jack shorts the ring to the
  sleeve. The stereo Thonkiconn (WQP PJ366ST, the "green" one) has three lugs, with ring in place
  of the mono's switch lug, and a body "very slightly wider" than the mono (seller listing; lug
  order sleeve, ring, tip per a forum quote †). So it should seat in the same cell as the deck's
  mono PJ-3001F/Thonkiconn. **No n8synth document on stereo jacks in deck cells was found** (repo
  docs, `.n8layout` files and web search all checked). Fit and pad assignment are **to check on a
  real deck** †.

### 5.4 Type A or B [recommended: Type A, no jumper]

- RP-054 standardises the Type A mapping. The Big Genes **outputs Type A** and **accepts A or B**
  on its input. Type A works with it in both directions.
- The board already hands the choice to David's wiring. Each jack is two signal wires from two
  labelled holes. **For a Type B device, swap the tip and ring wires of that jack.** No jumper, no
  parts. A wrong guess just gives no data: the IN LED is protected by the reverse diode, and a
  swapped OUT simply drives no current.
- Rejected:
  - Electrosmith-style 0 Ω links: redundant with the wiring;
  - AMYboard's bridge rectifier for automatic A/B on IN. As 4 × 1N4148WS (Basic) it costs two
    silicon drops: worst-case drive from a 3.3 V sender falls to about 2.2 mA against the 1.94 mA
    need. Too thin. The MB14F Schottky bridge (C2943867, Extended) keeps more margin but adds a fee;
  - firmware A/B on OUT: needs a third pin, which the board does not have.

### 5.5 THRU [recommended: none in hardware]

CA-033 makes THRU optional. Two of the nine references have one (Seed3 DevKit, Ksoloti header).
David's use (Big Genes to this board) needs none. A hardware THRU needs a third deck cell and a
second buffer. Firmware can echo IN to OUT ("soft thru"). Watch that this does not set up a MIDI
loop with the Big Genes (the Arduino MIDI library enables soft thru by default †). If ever needed,
the MIDI_RX node is on a hole and a THRU can be bodged later.

---

## 6. Proposed circuit (ready to draw)

### 6.1 Parts

| Ref (suggested) | Part | Value / MPN | Package | LCSC | JLC | Job, in plain words |
|---|---|---|---|---|---|---|
| U801 | Buffer | SN74AHCT1G125DBVR | SOT-23-5 | **C7484** | Extended (already on BOM as U703) | Turns the module's 3.3 V TX into a stiff 0/5 V signal, and keeps the jack away from the module pin |
| C801 | Decoupling | 100 nF X7R 16 V | 0402 | **C1525** | Basic | Local energy for U801's switching |
| R801 | Series, TX link | 1 kΩ 1 % | 0402 | **C11702** | Basic | Limits current if U801 ever fails, so the module pin cannot be dragged to 5 V |
| R802 | TX idle pull-up | 10 kΩ 1 % | 0402 | **C25744** | Basic | Holds U801's input high ("no current", MIDI idle) when unlinked or while the module boots |
| D801 | Clamp | BAT54S | SOT-23 | **C408389** | Extended (already on BOM) | Catches voltages patched into the OUT tip before they reach U801 |
| R803, R804 | OUT sink leg (tip) | 100 Ω 1 % ¼ W, in series | 1206 | **C17901** | Basic | CA-033's RC: sets the loop current, limits fault current |
| R805, R806 | OUT source leg (ring) | 100 Ω 1 % ¼ W, in series | 1206 | **C17901** | Basic | CA-033's RA: the source of the 5 mA loop. Survives a mono-cable short (25 mA, 64 mW each) |
| R807 | IN series | 220 Ω 1 % ⅛ W | 0805 | **C17557** | Basic | CA-033's RB: sets the opto LED current from any sender |
| D802 | Reverse protection | 1N4148WS | SOD-323 | **C2128** | Basic | Stops the opto LED seeing more than ~0.7 V reverse (its limit is 6 V), e.g. Type B or a CV patched in |
| U802 | Opto | **H11L1SR2M** | SMD DIP-6 (gull-wing) | **C20082** | **Extended, new** | Turns the sender's current into a clean logic level, with no copper between the two devices |
| C802 | Decoupling | 100 nF X7R 16 V | 0402 | **C1525** | Basic | Local energy for U802's Schmitt trigger |
| R808 | RX pull-up | 1 kΩ 1 % | 0402 | **C11702** | Basic | U802's output only pulls down; this provides the "1" |
| R809 | Series, RX link | 1 kΩ 1 % | 0402 | **C11702** | Basic | Isolates the opto node from SPARE2: no fight if SPARE2 is misused, and limited current at power-up |
| C803 | IN shield to ground | 100 nF X7R 50 V | 0603 | **C14663** | Basic | CA-033's optional RF ground for the IN sleeve: grounds radio noise, not audio-frequency loops |

**Count:** 16 placed parts: 7 Basic part numbers, U801 and D801 already Extended on the board,
and **one new Extended type, U802**. Per board ≈ $0.53 + 0.10 + 0.02 + about $0.08 of passives ≈
**$0.73**. Order fee **+$3.07**. Spec-exact alternative: R803–R806 replaced
by two 220 Ω 1206 (C17957, Extended): **+$3.07** more and two fewer parts.

**Pull-up value, a deliberate change:** the references use 270 Ω (Electrosmith) or 470 Ω (AMYboard,
Adafruit, PJRC). 1 kΩ halves the current pulse on +3V3D, which feeds the codec's digital supply
(cf. the Daisy forum clicks in §7). The edge stays fast (1 kΩ × ~20 pF ≈ 20 ns against a 32 µs
bit), and VOL improves at lower current (datasheet Fig. 6). 470 Ω (C25117, Basic) is the fallback.

### 6.2 Connections (netlist)

Pin numbers: AHCT1G125 1 OE̅, 2 A, 3 GND, 4 Y, 5 VCC (TI SCLS378P, already in
`datasheet_pins.json`). H11L1 1 A, 2 K, 3 NC, 4 VO, 5 GND, 6 VCC (onsemi Fig. 1). BAT54S 1 anode,
2 cathode, 3 common (the board's existing `clamp_below` convention).

| Net | Members |
|---|---|
| SPARE1 (existing) | module pin (Pico GP0 pin 1 / Teensy 1), hole **J101 SPARE1** |
| SPARE2 (existing) | module pin (Pico GP1 pin 2 / Teensy 0), hole **J101 SPARE2** |
| MIDI_TX | hole **J101 MIDI_TX** (2.54 mm from SPARE1), R801.1 |
| MO_IN | R801.2, R802.1, U801.2 (A) |
| +3V3D | R802.2, R808.2, U802.6, C802.1 |
| +5VD | U801.5, C801.1, D801.2, R806.2 |
| GND | U801.1 (OE̅), U801.3, C801.2, D801.1, U802.5, C802.2, C803.2 |
| MO_DRV | U801.4 (Y), D801.3, R803.1 |
| MO_T1 | R803.2, R804.1 |
| **MO_T** (OUT tip, sink, DIN 5) | R804.2, hole **MO_T** |
| MO_R1 | R805.2, R806.1 |
| **MO_R** (OUT ring, source, DIN 4) | R805.1, hole **MO_R** |
| **MI_R** (IN ring, source, DIN 4) | hole **MI_R**, R807.1 |
| MI_A | R807.2, U802.1 (anode), D802 cathode |
| **MI_T** (IN tip, sink, DIN 5) | hole **MI_T**, U802.2 (cathode), D802 anode |
| **MI_S** (IN sleeve, DIN 2) | hole **MI_S**, C803.1 |
| MIDI_RX_OC | U802.4 (VO), R808.1, R809.1 |
| MIDI_RX | R809.2, hole **J101 MIDI_RX** (2.54 mm from SPARE2) |

U802.3 is NC. Use the same jack-side hole labels on both faces: "MIDI OUT T", "MIDI OUT R",
"MIDI IN T", "MIDI IN R", "MIDI IN S". Add a silkscreen note: "Type A shown; swap T/R for B".

### 6.3 Impact on the pin map

- **No module pin changes.** SPARE1 = Pico GP0 (pin 1, UART0 TX) / Teensy 1 (TX1); SPARE2 = Pico
  GP1 (pin 2, UART0 RX) / Teensy 0 (RX1). The §6.3 budget stays at 26 nets.
- Change the PINMAP function text to "Spare GPIO 1 / MIDI OUT via link J101" and "Spare GPIO 2 /
  MIDI IN via link J101".
- J101 grows from `[SPARE1, SPARE2, RUN, GND]` to a block with MIDI_TX and MIDI_RX beside their
  SPARE holes.
- Firmware:
  - Teensy: `Serial1` at 31,250 baud (the MIDI library's default port);
  - Pico 2: UART0 on GP0/GP1. That is also the Pico SDK's default stdio UART, so put stdio on
    USB;
  - neither direction is inverted.
- Spec edits that follow: §1 / §13 "No TRS MIDI in Rev A" reversed; §3 Rev A channel set gains
  "MIDI in/out (TRS, on the spare-pin links)"; §7, §11 and §12 Extended count 14 → 15.
- Layout:
  - put the block at the **digital end**, near J101 and away from the codec (§10 zoning);
  - return U801's and U802's grounds near the module;
  - **U802 is a DIP-6 body, about 3.5–4 mm tall †**: it must sit **outside the module
    footprint** (§4.3 limits parts under the module to ≤ 2.5 mm).

---

## 7. Findings and risks

| # | Risk | Likelihood / effect | Mitigation |
|---|---|---|---|
| 1 | **Mono patch cable in MIDI OUT** (ring shorted to sleeve) | Likely in Eurorack. 25 mA from +5VD | Sized for it: 64 mW per 1206. No action |
| 2 | **CV or gate patched into MIDI OUT** | Likely. Up to ~33 mA from a stiff 12 V, < 10 mA from a module output | 200 Ω + BAT54S + buffer. The module pin never sees the jack |
| 3 | **Same into MIDI IN** | LED forward up to ~12 mA (100 Ω gate source) against its 30 mA limit. Reverse is clamped by D802 | A source with no resistance at all (a bus rail) could exceed 30 mA. Unrealistic |
| 4 | **Clicks in audio from MIDI edges** | Daisy forum t/4626: an H11L1 on 3V3 "every MIDI message generates a click", fixed by ground routing | Digital-end placement; local ground returns; 1 kΩ pull-up (smaller pulses); route each jack's T/R pair together. CA-033's ferrite beads are optional; footprints could be added at layout † |
| 5 | **Stereo jack fit in a JPS cell, and which pad the sleeve lands on** | Unverified † | Try a PJ366ST in a deck cell before wiring; don't bridge the IN sleeve to D |
| 6 | **Power-up glitch on OUT** | +5VD rises before +3V3D, so U801 may pull current briefly: one garbage byte at most † | Receivers resynchronise on the next status byte. Accept |
| 7 | **H11L1 height** | Taller than the 2.5 mm under-module rule † | Place outside the footprint; TLP2361 (SO-5) is the low-profile alternative, unproven in the references |
| 8 | **New Extended part, single source** | onsemi C20082 has 15.6 k in stock | Alternates C899473, C6569443 (footprint check †) |
| 9 | **Cable compliance** | RP-054 rejects audio TRS cables (not twisted pair) | Short in-rack TRS cables are what everyone uses. Keep them short; adapters ≤ 2 m |
| 10 | **One output, one input** | A passive mult on MIDI OUT would split the 5 mA loop | Never mult MIDI; use a MIDI THRU/splitter module |
| 11 | **Pull-up differs from the references** | 1 kΩ against 270/470 Ω | Datasheet-backed; 470 Ω C25117 fallback |
| 12 | **RP2350 erratum E9** (input pull-down latching) | Not expected: the RX node is driven through ≤ 2 kΩ in both states † | — |
| 13 | **Wrong Type A/B wiring** | No data, no damage | Swap the T/R wires |

Other findings worth recording:
- The Seed3 DevKit Eurorack's 10 Ω ring resistors cannot survive a mono-cable short (330 mA,
  1.1 W in an 0603). Electrosmith's 33 Ω is CA-033's ½ W value; its package is not in a published
  BOM †.
- Every 3.3 V Eurorack reference drives the jack straight from the MCU pin. That is only safe on
  5 V-tolerant MCUs. **Copying the Daisy Patch out stage onto a Teensy 4.1 would expose a
  non-tolerant pin to the panel.**

---

## 8. David-side wiring and bring-up

1. **Jacks:** fit two **stereo** (TRS) jacks, e.g. green Thonkiconn PJ366ST, in two deck cells,
   labelled MIDI IN and MIDI OUT. Not mono jacks.
2. **MIDI OUT cell:** tip pad's edge position → **MO_T**; ring pad's edge position → **MO_R**;
   sleeve → **D** (bridge as usual).
3. **MIDI IN cell:** tip → **MI_T**; ring → **MI_R**. **Do not bridge the sleeve to D.** Run the
   sleeve pad's edge position to **MI_S**, or leave it unconnected.
4. **Turn MIDI on:** link **SPARE1 ↔ MIDI_TX** and **SPARE2 ↔ MIDI_RX** with jumper shunts or
   short wires. Leave either open to keep that pin as plain GPIO. The two directions are
   independent.
5. **Type B gear:** swap that jack's T and R wires.
6. **To the Big Genes:** a short 3.5 mm TRS-to-TRS (stereo) cable. Its output is Type A and its
   input takes A or B.
7. **Bring-up:**
   - **Loopback first:** a TRS cable from MIDI OUT to MIDI IN. Send bytes at 31,250 baud 8-N-1 and
     read them back;
   - **Loop current:** while a "0" is held (a UART break, or firmware driving the TX pin low),
     measure the voltage across R807. 1.2–1.3 V means 5.5–5.9 mA;
   - **Idle levels:** MIDI_RX idles at about 3.3 V, and MO_R sits at +5VD;
   - then the Big Genes.

---

## 9. Sources

**Specifications**
- MMA/AMEI CA-033, *MIDI 1.0 Electrical Specification Update [2014]*:
  https://midi.org/wp-content/uploads/wpforo/default_attachments/1709416667-ca33-MIDI-10-Electrical-Specification-Update.pdf
  (index: https://midi.org/5-pin-din-electrical-specs).
- MMA/AMEI RP-054, *Specification for use of TRS Connectors with MIDI Devices* (v0.941, 2018):
  https://midi.org/specification-for-use-of-trs-connectors-with-midi-devices
  (PDF: https://drive.google.com/file/d/1Eb93WQkEv1YaUp8N3ph6Fq5HtOFCnT88/view).

**Reference designs**
- Electrosmith Daisy Patch Rev8, Daisy Field Rev4, Daisy Pod Rev5: schematic PDFs linked from
  https://docs.daisy.audio/hardware.
- Electrosmith Seed3 DevKit Eurorack Rev3: https://github.com/daisyaudio/Seed3-DevKit-Eurorack
  (`pcb/Seed3-DevKit-Eurorack-Rev3/production/Seed3-DevKit-Eurorack-Rev3_bom.csv`).
- AMYboard v1.5: https://github.com/shorepine/tulipcc/tree/main/docs/pcbs/amyboard
  (`amyboard-v1.5.sch`); firmware https://github.com/shorepine/tulipcc/blob/main/tulip/shared/amy_connector.c,
  https://github.com/shorepine/tulipcc/blob/main/tulip/amyboard/pins.h.
- Mutable Instruments Yarns v03:
  https://pichenettes.github.io/mutable-instruments-documentation/modules/yarns/downloads/yarns_v03.pdf;
  https://github.com/pichenettes/eurorack/tree/master/yarns/hardware_design/pcb.
- Adafruit MIDI FeatherWing: https://github.com/adafruit/Adafruit-MIDI-FeatherWing-PCB;
  https://www.adafruit.com/product/4740; https://learn.adafruit.com/adafruit-midi-featherwing.
- Ksoloti power-MIDI board: https://github.com/ksoloti/ksoloti-hardware/tree/HEAD/power-midi-board.
  Big Genes: https://ksoloti.github.io/7-big_genes.html.
- PJRC: https://www.pjrc.com/teensy/td_libs_MIDI.html and
  https://www.pjrc.com/teensy/td_libs_MIDI_sch_t3.png.
- Befaco MIDI Thing V2: https://github.com/Befaco/MIDIThing2 (README only);
  https://rubadub.co.uk/products/befaco-midi-thing-v2 (Type A †).
- Doudoroff, *MIDI Eurorack* (Type A/B survey, updated 2025-04-10): https://doudoroff.com/midi/.

**Forums**
- https://community.daisy.audio/t/midi-input-circuit-for-daisy-seed-what-am-i-missing/8778 (Pod
  opto H11L1SR2; Type A as shipped).
- https://community.daisy.audio/t/digital-noise-from-midi-signal-din-uart/4626 (MIDI clicks;
  fixed by grounding).
- Stereo Thonkiconn description: https://hackster.io/products/buy/115118 †;
  https://lookmumnocomputer.discourse.group/t/jack-socket-size/3450 †.

**Datasheets**
- onsemi H11L1M/H11L2M/H11L3M Rev 1.0.7 (via LCSC C20082):
  https://www.lcsc.com/datasheet/lcsc_datasheet_1810271613_onsemi-H11L1SR2M_C20082.pdf.
- TI SN74AHCT1G125 (SCLS378P): https://www.ti.com/lit/ds/symlink/sn74ahct1g125.pdf.

**Parts and repo**
- JLCPCB parts API `selectSmtComponentList`, 2026-10-15. Numbers quoted: C20082, C899473,
  C6569443, C16587, C107626, C37658, C5344, C15825, C16496, C92648, C571211, C3001991, C188666,
  C142364, C2914011, C41807, C63268, C92243, C7484, C408389, C2128, C1525, C14663, C11702, C25744,
  C25117, C17901, C17557, C17957, C25363, C2943867.
- Repo: `docs/analogue_board_spec.md`, `docs/n8synth_platform.md`,
  `tools/visualizer/boards/n8synth-6hp.json`, `tools/analogue_board/design.py`, `design_digital.py`
  (U703 AHCT1G125 usage), `parts.py`, `datasheet_pins_README.md`.

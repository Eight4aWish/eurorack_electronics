# Datasheet pin transcription

`datasheet_pins.json` was transcribed only from the manufacturers' datasheets (TI, Microchip, Vishay, onsemi, Nexperia, ST, AMS, Diodes, MDD, JST, Torex: the URLs are in `parts.py`) and from PJRC's Teensy 4.1 pinout card (https://www.pjrc.com/teensy/card11a_rev4_web.pdf). No KiCad libraries were used. Every pin drawing was checked against the rendered PDF page, not just extracted text. `checks.py` compares this file with the KiCad symbols on every build.

Conventions: names are spelled as printed. Overbars, subscripts and en-dash minus signs are described in `notes`, and the minus is written as ASCII `-`. Tabs are given as key `TAB`.

| Part | Source page | Ambiguities / errata |
|---|---|---|
| PCM3060PWR (TSSOP-28) | pcm3060.pdf p.7 drawing, p.8 Table 1 (SLAS533B) | None. Overbars: RST, MS (of MS/ADR/IFMD). |
| ADS8688IDBTR (TSSOP-38) | ads8688.pdf p.4 drawing, p.4-5 table (SBAS582C) | Pin 20 is printed `AIN2_GND` (not `AIN_2GND`) in both the drawing and the table. The table descriptions swap positive/negative for pins 20-27, and pins 26/27 reference themselves. Names were kept as drawn. Overbars: RST, PD, REFSEL, CS. |
| DAC8568IAPWR (TSSOP-16) | dac8568.pdf p.4 (SBAS430F) | None. Overbars: LDAC, SYNC, CLR. |
| MCP3208-CI/SL (SOIC-16) | mcp3208.pdf p.1 drawing, p.15 Table 3-1 (DS21298E) | None. Overbar: CS of CS/SHDN. |
| DG412DQ-T1-E3 (TSSOP-16) | Vishay 61564 Rev B (30-Jun-2025) p.1; earlier 70050 Rev G p.1 | Rev G draws only "Dual-In-Line and SOIC"; Rev B's drawing is titled "Dual-In-Line, TSSOP, and SOIC", which confirms TSSOP = SOIC numbering. DG412 differs from DG411 only in logic sense (ON at logic 1). |
| TL074HIDR (SOIC-14) | tl074h.pdf p.8 (SLOS080W), cross-checked with tl074h_lcsc.pdf (Rev U) | None. Both revisions agree. |
| LM393DR2G (SOIC-8) | lm393.pdf p.1 "PIN CONNECTIONS" (LM393/D Rev 25) | No pin table and no per-pin input names (only "Inputs A/B" brackets). Polarity was read from the triangle symbols: 2-, 3+, 5+, 6-. |
| 74HCT595D (SO16) | 74hct595.pdf p.4 drawing, p.5 Table 2 (Rev 12) | Table 2 lists Q0 twice. Overbars: MR, OE. Nexperia names (DS/SHCP/STCP/Q7S) differ from TI-style names. |
| TCA9555PWR (TSSOP-24) | tca9555.pdf p.4 (SCPS200E) | Table gives SDA type as "Input". Overbar: INT. |
| M24C64-RMN6TP (SO8N) | m24c64.pdf p.6-7, p.9 (DocID16891 Rev 33) | The figure's text extraction is garbled, so names were read from the render. Overbar: WC (floating = writes enabled). E0-E2 read as 0 if floating. |
| LM4040 4.1 V (SOT-23 DBZ) | lm4040.pdf p.4 Fig 5-1, Table 5-1, Sec 8.2.2.4 (SLOS456Q) | Pin 1 = CATHODE (+), pin 2 = ANODE (-), pin 3 = `*`: must float or connect to the anode (parasitic Schottky between pins 2 and 3). **The part number "LM4040xIM3-4.1" is not in this datasheet** (TI DBZ parts are LM4040x41IDBZR). An IM3 part's own datasheet was not checked. |
| AMS1117-3.3 (SOT-223) | ams1117.pdf p.1, p.3, p.7 (AMS "DS1117") | "TAB IS OUTPUT" is printed only by the TO-252 drawing. The SOT-223 tab is unlabelled, so TAB = VOUT is inferred. ams1117_lcsc.pdf is byte-identical, so there was no second source to check. |
| L78M05ABDT (DPAK) | l78m05.pdf p.3 Fig 2, p.30-35, p.40 (DS0425 Rev 24) | **No pin numbers anywhere.** The drawing gives names only: OUTPUT, INPUT, cut middle lead, tab = GND. The 1 = INPUT / 2 = GND / 3 = OUTPUT numbering is inferred from position. The tab is GND (unlike the AMS1117). |
| TPS54202DDCR (SOT-23-6) | tps54202.pdf p.3 (SLVSD26C) | None. |
| AP63205WU-7 (TSOT-23-6) | ap63205.pdf p.1-2 (DS41326 Rev 3-2) | None. FB goes direct to VOUT on the fixed 5 V part. The pinout differs completely from the TPS54202. |
| BAT54S MDD (SOT-23) | bat54s.pdf p.1 (Rev 2024A2) | No pin table, and the raster symbol has no pin numbers. 1 = anode, 2 = cathode, 3 = common was inferred from the symbol plus the 3-D view numbering. It matches the BAV99. |
| BAV99 Nexperia (SOT23) | bav99.pdf p.2 Table 2 (1 July 2022) | None: 1 = A1, 2 = K2, 3 = K1/A2. |
| SS14 MDD (SMA) | ss14.pdf p.1 (Rev 2025A5) | No pin numbers. Band = cathode (the outline and symbol agree). |
| SN74AHCT1G125DBVR (SOT-23-5) | sn74ahct1g125.pdf p.3 (SCLS378P) | None. Overbar: OE. |
| JST SM04B-SRSS-TB | sm04b.pdf p.1-2 (JST SH catalogue) | Circuit No.1 is shown only on the header's mating-face view (leftmost). The land pattern does not mark pin 1, so the pin-1 pad position is inferred. The 2 solder tabs are unnumbered. |
| Teensy 4.1 | PJRC card11a_rev4_web.pdf (front), card11b_rev4_web.pdf, dimensions_teensy41.png | card11a_rev4_web.png is a 404, so the vector PDF was used. Grey labels on 38/39 (CS1, IN1, MISO1, OUT1A) are alternate pins. CTX1 appears on both 11 and 22. The card prints no "Wire"/"Serial" names, so the grouping comes from the label numbers. |
| Raspberry Pi Pico 2 | pico2.pdf PDF p.5 Fig 2, p.8 Fig 3, p.9 Fig 4 + text | Pin 36 is "3V3(OUT)" in the figure but "3V3" in the text. Pin 33 is labelled both GND and AGND (text: AGND). The bottom mounting-hole offset (2 mm) is scaled from the drawing, not dimensioned. |
| RP2350 GPIO 0-29 functions | rp2350.pdf Table 677 (doc p.540-541, PDF p.541-542) | Parsed by column position and verified cell by cell against the render. F9 also carries QMI CS1n and TRACE signals. |

Added after transcription: TPS54308DDCR (TI SLUSCV2B p.3, same pinout as the TPS54202) and XC6206P332MR (Torex datasheet p.2: 1 VSS, 2 VOUT, 3 VIN).

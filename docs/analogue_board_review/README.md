# Analogue board Rev A: block-by-block prior-art review

Checkpoint 1 drew the schematic from the datasheets. This review checks each block against
published, proven designs: their real schematics, values read from the design files, and
the datasheets of every part. It ran on 2026-10-15, after David's question about the
PCM3060's output level showed that the codec stages had never been benchmarked.

| Block | Report | Main references read |
|---|---|---|
| Codec and audio | [codec_pcm3060.md](codec_pcm3060.md) | Mutable Beads, Electrosmith Patch SM / Daisy Patch / Seed, 4ms MP153, Befaco Lich / Oneiroi / Iroi (CS4271), TI EVM |
| Power | [power.md](power.md) | Beads, Patch SM, Seed2, Daisy Patch, Plaits, Marbles, 4ms, Befaco, Workshop Computer, EuroPi, Ogham |
| CV inputs | [cv_in.md](cv_in.md) | Patch SM, Daisy Patch, Lich, 4ms, Ogham, Workshop Computer, EuroPi, O&C, Plaits, Marbles, Beads, TI ADS8688 EVM and reference designs |
| CV outputs | [cv_out.md](cv_out.md) | Westlicht Performer (same DAC8568), O&C, Marbles, Stages, Workshop Computer, EuroPi, Alchemy Lab SDK |
| Gates | [gates.md](gates.md) | Ogham, Patch SM, Lich, Muxlicer, Workshop Computer, EuroPi, Marbles, O&C, 4ms |
| Panel I/O | [panel.md](panel.md) | Patch SM, Workshop Computer, EuroPi, Befaco, 4ms, Mutable, Bourns encoder note, Adafruit |
| TRS MIDI (new) | [midi.md](midi.md) | MIDI Association CA-033 and RP-054, Daisy Patch, AMYboard, Adafruit FeatherWing, Mutable Yarns, Electrosmith Seed3 devkit |

**Verdict:** the architecture holds up everywhere. The codec setup matches Beads exactly,
taking the CV offset from the DAC's own reference matches every precision-DAC design, and the
gate thresholds sit where Doepfer says they should. The findings are details, all cheap, but
several would have hurt on the first boards.

## Decision list

A = must fix; B = worth adopting; F = firmware or documentation only. "Basic" means no JLC
fee; each new Extended part type costs $3.07 per order.

### Agreed before the review (David, 2026-10-15)
- **Audio full scale 20 Vpp, in and out.**
  - Inputs: the 33k feedback becomes 15k.
  - Outputs: a second-order MFB at gain 2.5, built from Beads' resistor values. It needs a
    nF-range C0G capacitor, which is Extended: one new type.
- 100 nF at each audio-input op-amp's + pin (VCOM); CODEC_RST to a wiring hole.
- TRS MIDI in and out ([midi.md](midi.md)).

### Codec, power and supply
| | Change | Cost |
|---|---|---|
| A | **680 Ω minimum load on +3V3D.** The gate-input clamps push current into a rail whose LDO can't sink it, and on a lean build it would rise past the codec's 4.0 V maximum | Basic |
| B | Ferrite and a second 10 µF 50 V at the buck input, to keep 350 kHz off the ±12 V rail | Basic |
| B | Enable divider 510k/75k on the buck: digital 5 V starts at about 9.2 V, so it never runs without analogue 5 V (TI's codec power-up order) | Basic |
| B | Ferrite into the codec's VCC, and 5.1 Ω into its VDD | Basic |
| B | The optional (not fitted) feed-forward capacitor becomes 470 pF + 2 kΩ, the value TI's table gives | not fitted |
| F | Don't start the I2S or SPI clocks until the EEPROM answers, so a USB-only module never feeds the unpowered chips | — |

### CV inputs
| | Change | Cost |
|---|---|---|
| A | **Jack-facing output resistors to 1206** (CV out ×8, audio out ×2). Patched against another output, an 0402 runs at 3–4× its rating | Basic |
| B | **15 V TVS diode at each CV hole.** With only 1 kΩ in front of the ADC, static discharge from a hand-wired jack is the board's weakest point | **Extended, one type**, about $0.25–1.20 a board |
| B | 1 nF from each ADC input to ground (as TI's evaluation board) | Basic |
| B | 10 kΩ from +5VA to ground, so the ADC's ±20 V protection applies when the board is unpowered (inference from TI's condition; measure at bring-up) | Basic |
| F | An unpatched input reads about +0.2 V (ADS8688 internal bias), so trust the jack-detect probe and force 0; default every channel to ±10.24 V; oversample for audio-rate CV | — |

### CV outputs
| | Change | Cost |
|---|---|---|
| A | **CV7–8: take feedback from the jack side of the 1 kΩ.** Today the output sags 1% (about 12 cents/oct) into a 100 kΩ load, which calibration can't see | Rewire |
| A | **CV1–6: firmware load correction** through the ADC, which reads the jack directly. A spec requirement, because the switch prevents the hardware fix | — |
| B | Offset-divider capacitor 1 µF → 1 nF, so enabling the reference doesn't glitch the outputs, plus a power-up order in firmware | Basic |
| B | Feedback 30k → 33k and divider 12k/22k, so ±5 V is reachable inside the DAC's specified codes (−5.34 V to +5.41 V) | Basic |
| F | More calibration points (one per volt, as O&C does); CV7–8 calibrate with a cable to CVI7–8 | — |

### Gates
| | Change | Cost |
|---|---|---|
| B | 10 kΩ pull-up on CS_595 (the only chip select without one) | Basic |
| B | GATE_OE_N onto the J603 expansion holes; label J603 "74HCT595 only" | none |
| F | Gate inputs are active-high; mask them while the jack-detect probe runs; catch 100 µs triggers with edge interrupts or PIO | — |

### Panel
| | Change | Cost |
|---|---|---|
| A | **Read the encoder through gate inputs 3–4, not the expander.** A busy OLED stalls the shared I2C bus, so steps get lost. Wiring only; no own build uses more than two gate inputs | none |
| A | Wiper pull-downs 100k → 1M (100 kΩ pots were bent by up to 12% of full scale) | Basic |
| B | Button lines: the 1 kΩ moves to the hole side (as EuroPi); 10 nF on SW5–SW8 for encoders | Basic |
| B | Pot reference on its own node: 100 Ω + 10 µF from +3V3A. Hand-wired pot leads can then no longer disturb the DAC's supply | Basic |
| F | LED wiring and current cap; optional 47 µF at the LED holes | Basic |

### Spec corrections
- DAC8568 grade A reference drift: 5 typ / 25 max ppm/°C, not 2 (that is grade C).
- The TL074H can swing ±10 V on our rails, so the "needs OPA4197" notes go.
- Gate input: an adaptation of Ogham's clock input, not a copy.
- The power budget needs the ESP32-P4 case; the rail capacitors are X5R, not X7R.

### Decided by David, 2026-10-15
1. **TVS diodes on the CV jacks: yes.** PESD15VL1BA (C85378), one new Extended type.
2. **ESP32-P4 support: yes.** Q201 (AO3401A) bypasses the MOD_5V Schottky when JP201 is
   bridged (open by default). Firmware sets the P4's LDO channel 4 to 3.3 V first.
   Checkpoint 2 finds the extra board length.
3. **CV range: ±5 V**, with a documented ±10 V resistor variant: Rf 75k and divider
   15k/20k, all Basic, giving −10.71 … +10.54 V ([cv_out.md](cv_out.md) C4).
4. **Power header:** not fixed at bottom centre. Place it to keep power-rail noise away
   from sensitive parts.

All of the A and B items above are in the schematic (checkpoint 1, rebuilt 2026-10-15:
ERC clean, netlist identical to the generator's intent). The Extended part types went from 14
to 17: H11L1 (MIDI), the TVS and the codec filter's 1 nF C0G, about $9 more per order. The
same pass swapped the three SS14 Schottkys for SS34 (Basic, 3 A, same footprint). The reason
is the ESP32-P4 load budget: ≈0.75 A from +12 V with a lit LED chain. The firmware items are
collected in the spec, §15.

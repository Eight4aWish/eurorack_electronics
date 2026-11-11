# Noise test: five audio boards, screen off, still and redrawing

Designed with David on 2026-11-11, before anything was recorded. It replaces the plan of 6 November
on the Workbench ("Noise test: Rev A against the old boards").

## The question

How much noise does each board add on its **output**, and on its **input-to-output** path, and how
much does its **screen** add? Boards, tested one at a time in the same free slot of the rig, so the
power, the position and the cables are the same for each:

| Board | Short name | Codec | Screen | Test firmware |
|---|---|---|---|---|
| The old Boy (retired 2026-11-05): Teensy 4.1 on a Teensy Audio Shield | `oldboy` | SGTL5000 | none left | `eurorack_modules`, env `noise_oldboy` |
| Boy Rev A: Teensy 4.1 on the analogue board Rev A | `boy` | PCM3060 | 128x32 SSD1306, I2C 400 kHz | `eurorack_modules`, env `noise_boy` |
| The stock patch.init | `patchsm` | Patch SM's | none | `eurorack_daisy_patch_init/noise_test`, `BOARD=patchsm` |
| The patch.init with the OLED | `patchsm_oled` | Patch SM's | 64x48 SSD1306, soft I2C on A2/A3 | `BOARD=patchsm OLED=1` |
| The hand-built Daisy Seed module (MultiFX Seed) | `seed` | the Seed's | 128x64 SSD1306, I2C1 1 MHz | `BOARD=seed` |

## Decided (David, 2026-11-11)

- **The old Boy and Boy Rev A** are the two Boys. Rev B is still on order.
- **Three screen states:** off, still, redrawing. The old Boy's screen is gone, so it has off only.
- **48 kHz and 48-sample blocks on every board**, "feels fairest": the hardware compared, not each
  board's own rate. The audio block rate is then 1 kHz everywhere.
- **The inputs are fed silence from the ES-10**, ordinary cables rather than a shorting plug.

## The firmware

The same schedule on every board (`noise_schedule.h`, one copy in each repo, kept identical). It
starts by itself at power-on:

- **30 s of silence:** time to power up and start the recording while the ES-10 relocks.
- **Then three takes.** Each one:
  - sync, 0.25 s: 1500 Hz at −6 dBFS, so the analysis can find the take;
  - gap, 1.75 s: silence;
  - then for each screen state (off, still, redrawing):
    - **zero**, 20 s: digital silence out, input ignored. This is the output stage alone.
    - **tone**, 10 s: 997 Hz at −6 dBFS, the level reference.
    - **through**, 20 s: input copied to output at unity. This is input plus output.
- **Lengths:** 8.1 minutes on a board with a screen, 3.1 minutes without.

**The screen states:**
- **Off:** never started. Later in a run, off means display off and charge pump off (`0xAE`, `0x8D 0x10`).
- **Still:** a 50% checkerboard, drawn once.
- **Redrawing:** the checkerboard and its inverse alternately, a whole frame every 33 ms. That's the
  ~30 fps cap daisy_multifx_seed uses.

**Each board drives its screen as its own apps do:**
- the patch.init through `common/oled_soft_i2c.h`;
- the Seed through libDaisy's SSD130x driver;
- Boy through the Adafruit library at 400 kHz.

**Only audio and the screen run.** There is no ADC, CV or encoder scanning and no LED, so nothing else
on a board draws current on a schedule of its own. Boy's board is set up by `board::begin()`, as Boy
sets it: jack switches off, DAC at 0 V. The old Boy's SGTL5000 is set as the old Boy set it: line in
at 6, line out at 14, ADC high-pass frozen. It is set to 48 kHz, which Teensy's driver doesn't do
by itself.

## What to plug

**For each board,** in the free slot:

| From | To |
|---|---|
| ES-10 **OUT 1** | the module's audio **in L** |
| ES-10 **OUT 2** | the module's audio **in R** (the old Boy, Boy and the patch.inits are stereo in) |
| the module's audio **out L** | ES-10 **IN 1** |
| the module's audio **out R** | ES-10 **IN 2** |

- **Nothing else in the module.** Knobs anywhere: nothing reads them.
- **Its USB lead unplugged** while recording: a lead to the laptop is a second ground path.
- **The ES-10 sends silence:** `record.py` plays digital zeros on OUT 1 and 2.

**The ES-10's inputs are AC-coupled** (the factory jumper, put back after the filter work). That suits this test: it blocks the boards' DC offsets, and its corner sits below the 20 Hz the analysis starts at. The 11.97 V per full scale from the Swords rig still holds at audio frequencies.

**ES-10 IN 3 stays empty.** `record.py` records it beside every board, so each run carries the interface's own input floor, and the analysis takes it out of the output-only figure (as powers): "out only less ES-10 in".

**One control, once:** with no module, a cable from ES-10 OUT 1 to IN 1 and one from OUT 2 to IN 2.
That shows the interface's own floor, which every board's figures sit on.

## Procedure, per board

1. **Flash the test firmware** on the bench, over USB:
   - **Daisy boards:** `./build_all.sh` in `eurorack_daisy_patch_init/noise_test`, then DFU. On a
     patch.init take the SD card out first and catch the 2-second bootloader window.
   - **Teensys:** `pio run -e noise_boy -t upload` or `noise_oldboy`, in the foreground.
2. **Into the slot,** rack off; patch as above; USB lead out.
3. **Start the recording:**
   `~/GitHub/eurorack_daisy_patch_init/daisy_neural/.venv/bin/python tools/noise_test/record.py <short name>`
   (add `--no-screen` for `oldboy` and `patchsm`), then **power the rack within about 20 s**.
4. **Leave it** until the script finishes (8.5 or 3.5 minutes, with its margin).
5. **Analyse:** `.../python tools/noise_test/analyse.py tools/noise_test/recordings/<file>.wav`, and
   `--summary` once every board is in.
6. **Reflash the board's own firmware** afterwards.

The control: `record.py es10_loop --control`, then `analyse.py --control <file>`.

## Measures, fixed before recording

All levels are in **dB against a 10 Vpp sine** (3.54 V RMS), more negative is quieter. That's the
scale of the earlier figures: the patch.init running MultiFX measured −92 dB, the Seed module
−90 dB after its buck (`daisy_multifx_seed/NOISE.md`). Perfect 16-bit audio would be about −98 dB.

- **Out only, A-weighted:** the zero segments. The headline.
- **Through, A-weighted,** and the **input's share**: through minus zero, as powers. That holds if the
  two noises are uncorrelated.
- **Hum** at 50 and 100 Hz; the **1 kHz line**, the block rate, where the Seed's comb was; the
  **tallest spurs**, lines 10 dB over their neighbourhood, 20 Hz to 20 kHz.
- **Full scale,** from the tone: what a full-level output swings, Vpp.
- **Each segment's first 2 s and last 1 s** are dropped, which covers the screen switching.
- **Three takes per board:** median and range. A difference counts only when it clears the spread of
  the takes; inside it, "no detectable difference".

**The analysis was checked before any recording,** on a synthetic run with known levels and a missing
first sync. It found the three takes, and read the floor, the input's share, the lines and a
10.0 Vpp full scale back to within 0.1 dB. A-weighting is applied to the spectrum, so it matches
IEC 61672 exactly (−19.1, 0 and −2.5 dB at 100 Hz, 1 kHz and 10 kHz).

## Results

**The interface, 2026-11-11** (`es10_loop`, ES-10 OUT 1 → IN 1 and OUT 2 → IN 2): −96.2 dB A-weighted, −94.3 flat, no spurs; hum −122 dB at 50 Hz. A 1 kHz tone on each output came back on its own input only (leakage −79 dB), 2.0 dB down. The Swords rig's volts per full scale predict 0.8 dB, so absolute levels may be about 1 dB out. Comparisons between boards are unaffected, since every board goes through the same input. The earlier patch.init figure (−92 dB) was only 4 dB above this floor, which is why IN 3 is recorded with every board.

### The boards, 2026-11-11

The figures below are all **A-weighted, in dB against a 10 Vpp sine**, the median of three takes,
left channel. Right matches within 0.5 dB except where noted. The takes agreed within about
0.5 dB, so every difference below that clears it is a real one.

**With the screen off:**

| Board | Out only | Out, less the ES-10 | Through | The input's share | Hum 50 Hz | Full scale |
|---|---|---|---|---|---|---|
| patch.init, stock | −95.5 | −98.9 | −91.7 | −94.0 | −120 | 17.4 Vpp |
| patch.init, OLED | −95.7 | −99.5 | −91.8 | −94.1 | −120 | 17.2 Vpp |
| Boy Rev A | −94.1 | −96.3 | **−93.0** | **−99.5** | −118 | 19.3 Vpp |
| old Boy | −90.7 | −91.6 | −76.8 | −77.0 | −107 (R −102) | 9.9 Vpp (R 8.0) |
| Seed module | −89.0 | −89.6 | −85.3 | −87.8 | **−93** | 34.6 Vpp |

**What the screen costs,** on the output only:

| Board | Still | Redrawing | Lines the screen adds |
|---|---|---|---|
| patch.init, OLED | +0.2 dB | +0.5 dB | 6.8 kHz −112; redrawing, 30 Hz −98 |
| Boy Rev A | +1.7 dB | +1.9 dB | 6.0 kHz −100; redrawing, 30 Hz −90 |
| Seed module | **+11.1 dB** (R +6.0) | +11.4 dB (R +6.9) | **6.2 kHz −80** |

**Readings:**
- **The question from 6 Nov, is audio through Rev A cleaner than through the old boards?** Than the old
  Boy and the Seed module, clearly. Than the patch.init, no: once the gains are taken into account (below)
  they are on a par, Rev A 1.3 dB behind. As heard at the output, Rev A reads quietest input to output
  (−93.0 dB), because the patch.init's +2.9 dB of gain lifts its noise along with the signal.
- **The old Boy's through figure is its line-level input:** the input is gained up to the output.
  Its two outputs also differ in level (9.9 against 8.0 Vpp), with more hum on the right.
- **The Seed module's screen is the biggest effect found.** Switching the panel on costs 6–11 dB,
  dominated by a 6.2 kHz line about 30 dB above the patch.init's equivalent. Redrawing is no worse than
  a still frame, so it's the panel being powered (its charge pump), not the I2C traffic.
  `daisy_multifx_seed`'s "hibernate" stops redrawing but leaves the panel on. Turning the panel off
  (`0xAE`, charge pump off), which this firmware does, is what removes the line.
- **The Seed's hum, −93 dB, is about 27 dB worse than the patch.inits'.** That points at its grounding,
  as NOISE.md's "residual" foresaw. Its output stage has about twice the patch.init's gain. Against its
  own full scale its floor is about −100 dB, like the others, but a 10 Vpp signal sits 11 dB lower in
  its digital range.
- **Redrawing at 30 fps puts a 30 Hz line and its harmonics on every screen board:** −90 dB on Boy, −98 on
  the patch.init. A-weighting plays it down, but it's the I2C burst at the frame rate.
- **The block-rate line at 1 kHz** sits at −108 dB or below on every board. The Seed's old comb,
  fixed by its buck, hasn't come back.

### The gains, and the same signal in

**Measured the same day,** with the test firmware still on: 440 Hz into in L and 554 Hz into in R, about
0.5 Vpp, read in the first pass-through segment, against the plain-cable loopback, which cancels the ES-10's
calibration. "Per signal in" is the through noise less the gain: signal-to-noise for the same
signal going in, the fair way to compare audio passing through.

| Board | Gain, in to out | Through, per signal in | The input alone, referred to it |
|---|---|---|---|
| patch.init, stock | +2.9 dB | **−94.6** | −96.9 |
| patch.init, OLED | +2.8 dB | **−94.6** | −96.9 |
| Boy Rev A | +0.3 dB | −93.3 | **−99.8** |
| Seed module | +0.6 dB | −85.9 | −88.4 |
| old Boy (R) | +10.4 dB as read | −87.9 | −88.1 |

**Readings, corrected by the gains:**
- **For audio passing through, Boy Rev A is on a par with the factory patch.init.** It comes out 1.3 dB
  behind, which clears the 0.3 dB take spread but is far below hearing at −93 dB, and is within the variation
  to expect between two units. Its input stage alone is the quietest, about 3 dB under the patch.init's. Its
  output stage is about 2.6 dB noisier (−96.3 against −98.9, the ES-10 taken out). The patch.init's
  +2.9 dB of gain lifts the signal clear of its quieter output stage. It's well ahead of the earlier
  builds: about 8 dB cleaner than the Seed module.
- **The panels differ in size:** 64x48 on the patch.init, 128x32 on Boy, 128x64 on the Seed. The test
  lit half of every pixel, so its screen costs grow with the panel. A text menu lights far fewer, so the
  costs in use are lower than these.
- **Left and right are swapped on Boy Rev A and on the Seed module**, the two hand-built boards: each one's
  out L follows ES-10 OUT 2, with the patch as the doc gives it. Both patch.inits follow OUT 1, so the rig is
  right and the swap is in each build.
- **The old Boy's left input is miswired on the module** (David): both inputs reach its right channel and
  the left gets almost nothing, 58.6 dB down. Its right channel's +10.4 dB was read with both ES-10 outputs on
  one input, which halves each tone, so its true gain is likely nearer +16 dB. That fits a line-level input
  brought up to a Eurorack output.

Absolute levels may be about 1 dB out (the ES-10 calibration); comparisons between boards are not
affected, and the gains are free of it. `tools/noise_test/results/summary.md` once boards are recorded.

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

The boards: none yet. `tools/noise_test/results/summary.md` once boards are recorded.

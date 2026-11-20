# p4_gesture: Health's first gesture program

The camera shows on the TLQ-SCREEN, as in [`p4_camera_screen`](../p4_camera_screen), and Espressif's hand detector
(esp-dl) looks at the same square picture. The player stands in the middle, about 2.5 m away. Each half of the
picture is a vertical fader, and the height of the hand on it sets a CV out.

| Hand | Out (panel) | Range | Patched to (Oneiroi) |
|---|---|---|---|
| on the screen's left | CV1 (X1) | 0–10 V | supersaw volume jack: the fader sets the ceiling |
| on the screen's right | CV3 (X2) | 0–10 V | echo dry/wet mixer jack: the fader sets the ceiling (David, 2026-11-20: moved from the filter cutoff, as the echo made a better demo) |

- **The fader's range:** a lane is 0 V with its hand's centre in the bottom tenth of the picture and 10 V in the top
  tenth, in proportion between (`END_STOP` in `main/main.c`). A hand's centre can't reach the very edge, so the end
  stops sit a little in. Only the height counts, and the middle of the picture divides the two hands.
- **When a hand is lost:** like a fader let go of, a lane holds its value while its hand goes unseen.
- **Smoothing:** the CV glides between detections with a 50 ms time constant. The other four CV jacks stay switched
  off.
- **No head detection:** it was tried and dropped for now (David, 2026-11-19); see the bench notes below.

**The screen** shows a grey line down the middle, hands found in this picture in white, held hands in grey, and each
fader's level as a grey line across its half at the hand's height.

**The console** (115200 on the board's USB-C) prints every 5 seconds:
- detections a second, and the model's time;
- how often each hand was found;
- how high each hand went, for setting `END_STOP` from real playing.

**The pipeline:**
- The OV5647 delivers 1280×960; the ISP turns it into RGB565.
- The PPA takes the middle 960×960 square and makes two copies:
  - 720×720, turned a quarter clockwise, for the screen;
  - 320×320, upright, for the detector, whenever it is ready for another picture.
- Detection runs on core 0, at about 11 pictures a second (66 ms each). The screen and the CV outs run on core 1.

**The analogue board starts in its spec order (§15):**
1. LDO channel 4 at 3.3 V.
2. The EEPROM must answer; nothing else starts until it does.
3. Every jack switch off.
4. 0 V codes to the DAC, then its reference on.
5. The switches of CV1 and CV3.

Without the rack on, the screen still runs, but there's no CV out.

**First bench, 2026-11-19** (2.5 m from the camera, with the background cleared of pictures and dark objects):
- **Detections:** about 8 a second. The face model takes 68 ms on every third run, and the hands 65 ms on every run.
  Espressif quotes 45 ms for the hand model alone.
- **Hands:** each hand was found in 60–90 % of runs while playing. The face was found in 3–12 of every 14 face runs,
  and the held reference covers the gaps.
- **Lane range:** the lanes used 0.7–2.6 head-widths, so with `FAR_HW` at 4 a lane peaked at about 5 V.
- **Screen:** the picture runs at about 22 frames a second while the detectors run, against 43 without them. The
  camera, the screen and the models all share the PSRAM.
- **Colour:** the camera picture was close to black and white in that room. The OV5647's default tuning
  (`esp_cam_sensor/sensors/ov5647/cfg/ov5647_default.json`) turns its colour correction off below an average
  brightness of 28.
- **The first version** dropped a lane to 0 V a second after its hand or the head went unseen. David's verdict:
  "amazing, but as it stands pretty useless", because the supersaw dropped out with every miss. Holding the lanes
  came from that.
- **Head detection dropped** (David): the face models found the head too rarely at 2.5 m to be the reference. The
  lanes became vertical faders on each half of the picture (hands only, about 11 detections a second). That version
  works for David; it is less reliable for a player with smaller hands.

**Status (2026-11-19): a proof of concept**, good enough for the Boy/Health video (David). These are left for a
proper session:
- **Colour:** the picture is near greyscale under room light (see the bench notes). Try more light on the player
  first. The fix is Health's own IPA tuning file (`CONFIG_CAMERA_OV5647_CUSTOMIZED_IPA_JSON_CONFIGURATION_FILE`):
  colour correction kept on in dim light, a white-balance section, and a little more saturation.
- **Smaller hands:** detection is less reliable for a player with smaller hands. In order:
  1. stand at about 2 m;
  2. lower the detector's score threshold from 0.25 to about 0.15;
  3. light and contrast on the hands.
  Measure each hand's "found in" share for each player before and after.
- **End stops:** set `END_STOP` from the logged range of real playing.
- **Screen rate:** the picture runs at 22 frames a second against 43 while the detector runs, because they share the
  PSRAM.
- **Head reference:** dropped for now. A held, smoothed ESPDet-224 head on every third run half worked, or the job
  could go to an NPU board if the P4 falls short.
- **The other four CV outs** are unused. The original plan was each hand's x, y and size.
- **Calibration** of the outs is still pending from the bring-up (OUT-R −140 mV; the encoder counts down
  clockwise).

**Build and flash** (ESP-IDF 5.5.4, as in `docs/analogue_board_esp32p4.md`):

```sh
PATH="$HOME/esp/py312:/opt/homebrew/bin:$PATH" bash -c '. ~/esp/esp-idf/export.sh && idf.py build flash monitor'
```

**Flicker in dim light** (2026-11-20): at night, with only the room's LEDs on, the picture flickered. Another lamp
cured it; fixing the camera at 50 Hz mains did not. So it's the low light, most likely the IPA's colour correction:
the default JSON (`ov5647_default.json`, `acc.ccm.low_luma`) turns it off below an average luma of 28 and on above,
with no margin, so a scene sitting near 28 flips between the two. **Film with enough light.** A custom JSON
(`CONFIG_CAMERA_OV5647_CUSTOMIZED_IPA_JSON_CONFIGURATION_FILE`) could remove the switch if that's ever needed.

**Mains:** `camera_mains_50hz()` sets the OV5647's banding filter to 50 Hz by hand once the camera has started
(0x3C01 bit 7, 0x3C00 bit 2, 0x3A00 bit 5); it had picked 60 Hz for itself. Right for UK mains, kept, but it wasn't
the flicker. The boot log says what the sensor had before. Elsewhere, at 60 Hz mains, change it.

**With the screen dark** (David, 2026-11-20: the camera picture flickers in low light): the same program, with the
bridge's HDMI output turned off once the screen side has started, so the TLQ-SCREEN gets no signal. The camera,
detector and CV run as usual. Its own build folder, so the setting never reaches `build/`:

```sh
PATH="$HOME/esp/py312:/opt/homebrew/bin:$PATH" bash -c '. ~/esp/esp-idf/export.sh && idf.py -B build_dark -DSCREEN_DARK=1 build flash'
```

Rack on before the USB goes in. The model (`espressif/hand_detect`) is built into the app
image, so the partition table gives the app 12 MB.

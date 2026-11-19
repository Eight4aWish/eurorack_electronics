# p4_gesture: Health's first gesture program

The camera shows on the TLQ-SCREEN, as in [`p4_camera_screen`](../p4_camera_screen). Espressif's face and hand
detectors (esp-dl) look at the same square picture. The head is the reference: each hand's distance from it becomes
a fader-like lane on a CV out. The distance is counted in head-widths, so the lane holds when the player steps
sideways, forward or back.

| Hand | Out (panel) | Range | Patched to (Oneiroi) |
|---|---|---|---|
| on the screen's left | CV1 (X1) | 0–10 V | supersaw volume jack: the fader sets the ceiling |
| on the screen's right | CV3 (X2) | 0–10 V | filter cutoff jack: cutoff knob fully left, MOD LEVEL down |

- **The lane's range:** a lane is 0 V with its hand 1 head-width from the head or closer. It reaches 10 V at 4
  head-widths. These are `NEAR_HW` and `FAR_HW` in `main/main.c`.
- **When a hand is lost:** if a lane's hand, or the head, goes unseen for a second, the lane falls back to 0 V.
- **Smoothing:** the CV glides between detections with a 50 ms time constant. The other four CV jacks stay switched
  off.

**The screen** shows what the detectors found: the head in red, the hands in white, and a grey line from the head
to each hand.

**The console** (115200 on the board's USB-C) prints every 5 seconds:
- detections a second, and each model's time;
- how often the head and the hands were seen;
- each lane's range in head-widths, for setting `NEAR_HW` and `FAR_HW` from real playing.

Typing **`f`** swaps the face detector between Espressif's fast two-stage one (MSR+MNP, the default) and the 224×224
one (ESPDet-Pico, slower).

**The pipeline:**
- The OV5647 delivers 1280×960; the ISP turns it into RGB565.
- The PPA takes the middle 960×960 square and makes two copies:
  - 720×720, turned a quarter clockwise, for the screen;
  - 320×320, upright, for the detectors, whenever they are ready for another picture.
- Detection runs on core 0. The screen and the CV outs run on core 1.

**The analogue board starts in its spec order (§15):**
1. LDO channel 4 at 3.3 V.
2. The EEPROM must answer; nothing else starts until it does.
3. Every jack switch off.
4. 0 V codes to the DAC, then its reference on.
5. The switches of CV1 and CV3.

Without the rack on, the screen still runs, but there's no CV out.

**Build and flash** (ESP-IDF 5.5.4, as in `docs/analogue_board_esp32p4.md`):

```sh
PATH="$HOME/esp/py312:/opt/homebrew/bin:$PATH" bash -c '. ~/esp/esp-idf/export.sh && idf.py build flash monitor'
```

Rack on before the USB goes in. The models (`espressif/hand_detect`, `espressif/human_face_detect`) are built into
the app image, so the partition table gives the app 12 MB.

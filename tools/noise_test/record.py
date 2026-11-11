"""Record one board's noise-test run (docs/noise_test.md).

The Scarlett 16i16 carries the ES-10 on ADAT (the rig the Wasp and Swords captures used,
daisy_neural/captures/swords/rig.json). This plays digital silence on ES-10 outputs 1 and 2
(Scarlett 7 and 8), which feed the module's audio inputs, and records ES-10 inputs 1 and 2
(Scarlett 11 and 12), fed by the module's audio outputs, at 48 kHz. ES-10 IN 3 (Scarlett 13) is
recorded with nothing in it, so every run carries the interface's own input floor.

    python record.py patchsm_oled            # a board with a screen: 8.5 minutes
    python record.py oldboy --no-screen      # 3.5 minutes
    python record.py es10_loop --control     # 60 s: ES-10 out 1 -> in 1 with a cable, no module
    python record.py boy --gain              # 2 minutes: 440 Hz on OUT 1, 554 Hz on OUT 2, for the
                                             # input-to-output gain in the first pass-through segment

Start it, then power the rack within about 20 s: the firmware waits 30 s before its first take.
Run with daisy_neural's venv, which has sounddevice and soundfile:
    ~/GitHub/eurorack_daisy_patch_init/daisy_neural/.venv/bin/python record.py <board>
"""
import argparse
import datetime as dt
import os
import sys

import numpy as np
import sounddevice as sd
import soundfile as sf

FS = 48000
DEVICE = "Scarlett 16i16"
PLAY = [7, 8]   # ES-10 outputs 1, 2 -> module audio in L, R
REC = [11, 12, 13]  # ES-10 inputs 1, 2 <- module audio out L, R; IN 3 left empty: the interface's own input floor
HERE = os.path.dirname(os.path.abspath(__file__))
GAIN_HZ = (440.0, 554.37)  # OUT 1, OUT 2: different, so each output shows which input it came from
GAIN_AMP = 0.0228          # digital peak: 0.25 V peak at 10.96 V per full scale

# the firmware's schedule (noise_schedule.h): 30 s, then 3 takes of 2 s + 50 s per screen state
def run_seconds(screen):
    return 30 + 3 * (2 + 50 * (3 if screen else 1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("board", help="a short name: oldboy, boy, patchsm, patchsm_oled, seed, es10_loop")
    ap.add_argument("--no-screen", action="store_true", help="a board without a screen")
    ap.add_argument("--control", action="store_true", help="60 s, for the interface's own floor")
    ap.add_argument("--gain", action="store_true", help="tones into the inputs, for the through gain")
    a = ap.parse_args()

    # --gain needs only the first take's pass-through: 30 s + sync 2 s + 50 s, and the margin
    secs = 60 if a.control else (30 + 2 + 50 + 25) if a.gain else run_seconds(not a.no_screen) + 25
    dev = next((i for i, d in enumerate(sd.query_devices()) if DEVICE in d["name"]), None)
    if dev is None:
        sys.exit(f"{DEVICE} not found: {[d['name'] for d in sd.query_devices()]}")
    out_dir = os.path.join(HERE, "recordings")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{a.board}{'-gain' if a.gain else ''}_{dt.datetime.now():%Y-%m-%d_%H-%M}.wav")
    n = int(secs * FS)
    print(f"recording {secs / 60:.1f} min into {path}")
    if not a.control:
        print("power the rack now (within ~20 s); the module's first take starts 30 s after power-up")
    play = np.zeros((n, len(PLAY)), dtype="float32")
    if a.gain:  # about 0.5 Vpp each (10.96 V per full scale out): safe even for the old Boy's line input
        t = np.arange(n) / FS
        play[:, 0] = GAIN_AMP * np.sin(2 * np.pi * GAIN_HZ[0] * t)
        play[:, 1] = GAIN_AMP * np.sin(2 * np.pi * GAIN_HZ[1] * t)
    rec = sd.playrec(play, samplerate=FS, device=dev,
                     input_mapping=REC, output_mapping=PLAY, dtype="float32")
    sd.wait()
    sf.write(path, rec, FS, subtype="FLOAT")
    peak = 20 * np.log10(np.abs(rec).max() + 1e-12)
    print(f"done: {path}, peak {peak:.1f} dBFS")
    if peak < -60 and not a.control:
        print("WARNING: nearly silent. Is the module's output in ES-10 input 1, and did it power up?")


if __name__ == "__main__":
    main()

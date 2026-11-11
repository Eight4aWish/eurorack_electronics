"""Analyse noise-test recordings (docs/noise_test.md).

    python analyse.py recordings/patchsm_oled_2026-11-12_10-15.wav   # one board -> results/<board>.json
    python analyse.py --control recordings/es10_loop_....wav          # the interface's own floor
    python analyse.py --summary                                       # every result -> results/summary.md
    python analyse.py --gain recordings/boy-gain_....wav              # input-to-output gain -> results/<board>-gain.json

Every level is in dB against a 10 Vpp sine (3.54 V RMS), the scale the earlier figures used
(daisy_multifx_seed/NOISE.md: the patch.init at -92 dB, the Seed module at -90 dB after its buck).
More negative is quieter.

Measures, per segment and channel:
  noise_a     A-weighted RMS of the segment            (the headline: what the ear weighs)
  noise_flat  RMS, 20 Hz to 20 kHz
  hum50/100   the 50 and 100 Hz lines
  block1k     the 1 kHz line: the audio block rate at 48 kHz / 48 samples, where the Seed's comb was
  spurs       the tallest lines standing 10 dB over their neighbourhood, 20 Hz to 20 kHz
Takes are summarised as median and range: a difference only counts outside the take spread.
The input's own share is through minus zero, as powers; it holds if the two are uncorrelated.
"""
import argparse
import glob
import json
import os
import sys

import numpy as np
import soundfile as sf
from scipy import signal

FS = 48000
IN_VFS = 11.9712  # V per digital full scale at an ES-10 input (rig.json, Swords captures, 2026-10)
REF = 10 / 2 / np.sqrt(2)  # a 10 Vpp sine, V RMS
SCREENS = ["off", "still", "redraw"]
GAIN_HZ = (440.0, 554.37)  # record.py --gain: OUT 1, OUT 2
GAIN_AMP = 0.0228          # their digital peak as sent
# A plain cable, ES-10 OUT -> IN, returned a 1 kHz tone 2.0 dB down (2026-11-11, es10_loop). A gain
# taken against that is the board's own, free of the ES-10's volts-per-full-scale calibration.
LOOP_DB = -2.0


def tone_amp(x, f):
    """Peak amplitude of a sine at f in x (digital units): a single-bin fit over whole seconds."""
    n = (len(x) // FS) * FS
    t = np.arange(n) / FS
    return float(np.abs(np.dot(x[:n], np.exp(-2j * np.pi * f * t))) * 2 / n)


def analyse_gain(path):
    x, fs = sf.read(path, dtype="float64")
    x = np.atleast_2d(x.T)[:2]
    ons = sync_onsets(x[0] * IN_VFS)
    if not ons:
        sys.exit("no sync found")
    t0 = ons[0]
    seg = x[:, t0 + 34 * FS: t0 + 51 * FS]  # the first pass-through: base + 32..49 s, base = sync + 2 s
    res = {"file": os.path.basename(path), "gain": True, "sync_s": round(t0 / FS, 2), "outputs": []}
    for ch, lab in enumerate("LR"):
        amps = [tone_amp(seg[ch], f) for f in GAIN_HZ]
        k = int(np.argmax(amps))  # which input this output follows
        g_db = 20 * np.log10(max(amps[k], 1e-12) / GAIN_AMP) - LOOP_DB
        res["outputs"].append({"output": lab, "from_input": f"OUT {k + 1}", "gain_db": round(g_db, 1),
                               "gain_vv": round(10 ** (g_db / 20), 3),
                               "crosstalk_db": round(20 * np.log10(max(amps[1 - k], 1e-12) / max(amps[k], 1e-12)), 1)})
    return res

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")


def db(v_rms):
    return float(20 * np.log10(max(v_rms, 1e-12) / REF))


def a_weight(f):
    """IEC 61672 A-weighting as a gain, applied to the spectrum: exact at every frequency
    (a digital filter at 48 kHz bends it by about 1 dB at 10 kHz)."""
    f2 = f ** 2
    ra = 12194.217 ** 2 * f2 ** 2 / ((f2 + 20.598997 ** 2) * np.sqrt((f2 + 107.65265 ** 2) * (f2 + 737.86223 ** 2))
                                    * (f2 + 12194.217 ** 2))
    return ra * 10 ** (2.0 / 20)  # 0 dB at 1 kHz


def line(p, freq, half=2):
    """A line's RMS from the power density, summed over +-half 1 Hz bins (the Hann window spreads it)."""
    i = int(round(freq))
    return float(np.sqrt(p[max(i - half, 0):i + half + 1].sum()))


def measure(x):
    """x in volts, one channel. Welch, Hann, 1 s segments: 1 Hz bins, density in V^2/Hz."""
    f, p = signal.welch(x, FS, window="hann", nperseg=FS, scaling="density")
    band = (f >= 20) & (f <= 20000)
    out = {"noise_a": db(np.sqrt(np.sum(p[band] * a_weight(f[band]) ** 2))),
           "noise_flat": db(np.sqrt(np.sum(p[band])))}
    out["hum50"], out["hum100"], out["block1k"] = (db(line(p, h)) for h in (50, 100, 1000))
    pdb = 10 * np.log10(p + 1e-30)
    floor = signal.medfilt(pdb, 101)
    cand = [i for i in signal.find_peaks(pdb, distance=5)[0] if 20 <= f[i] <= 20000 and pdb[i] > floor[i] + 10]
    cand.sort(key=lambda i: -p[i])
    out["spurs"] = [[float(f[i]), round(db(line(p, f[i])), 1)] for i in cand[:5]]
    return out


def sync_onsets(x):
    """Rising edges of the 1500 Hz sync, in samples. 20 ms frames; a frame counts when 1500 Hz is
    within 10 dB of the loudest sync and 12 dB over 997 Hz, so the tone's leakage can't pass for it
    (it did, on the first real run: the threshold was absolute, and the tone is at full level)."""
    hop = 960
    n = len(x) // hop
    fr = x[:n * hop].reshape(n, hop)
    t = np.arange(hop) / FS
    a15 = np.abs(fr @ np.exp(-2j * np.pi * 1500 * t))
    a10 = np.abs(fr @ np.exp(-2j * np.pi * 997 * t))
    floor = 0.05 * hop / 2  # 0.05 V peak: a real sync is volts; this keeps noise from passing for one
    on = (a15 > 0.316 * a15.max()) & (a15 > 4 * a10) & (a15 > floor)
    edges = np.flatnonzero(on[1:] & ~on[:-1]) + 1
    return [int(e * hop) for e in edges]


def takes_from(onsets, take_len):
    """Starts of the three takes, filling one missed sync from the others' spacing."""
    tl = int(take_len * FS)
    # keep onsets that are a whole number of takes apart from the last one
    if not onsets:
        return []
    last = onsets[-1]
    starts = sorted({o for o in onsets if abs(((last - o) / tl) - round((last - o) / tl)) < 0.02})
    while len(starts) < 3 and starts[0] - tl > 0:
        starts.insert(0, starts[0] - tl)
    return starts[-3:]


def analyse_board(path, screen=None):
    x, fs = sf.read(path, dtype="float64")
    assert fs == FS, fs
    x = np.atleast_2d(x.T) * IN_VFS  # volts, channels first
    floor_ch = x[2] if x.shape[0] > 2 else None  # ES-10 IN 3, empty: the interface's own input floor
    x = x[:2]
    ons = sync_onsets(x[0])
    if screen is None:  # spacing tells whether the board ran the screen states
        gaps = np.diff(ons) / FS
        screen = bool(len(gaps)) and float(np.median(gaps)) > 100
    groups = 3 if screen else 1
    take_len = 2 + 50 * groups
    starts = takes_from(ons, take_len)
    if len(starts) < 3:
        sys.exit(f"found {len(starts)} takes (sync onsets at {[round(o / FS, 1) for o in ons]} s)")
    res = {"file": os.path.basename(path), "screen": screen, "takes": []}
    for t0 in starts:
        take = {"start_s": round(t0 / FS, 2), "groups": []}
        for g in range(groups):
            base = t0 + int((2 + 50 * g) * FS)
            seg = {"screen": SCREENS[g]}
            if floor_ch is not None:
                seg["es10_in"] = measure(floor_ch[base + 2 * FS: base + 19 * FS])
            for name, a, b in (("zero", 2, 19), ("tone", 22, 29), ("through", 32, 49)):
                y = x[:, base + a * FS: base + b * FS]
                if name == "tone":
                    vpp = [float(np.sqrt(np.mean(c ** 2)) * 2 * np.sqrt(2)) for c in y]
                    seg["tone_vpp"] = [round(v, 3) for v in vpp]
                    seg["full_scale_vpp"] = [round(2 * v, 2) for v in vpp]  # the tone is at -6 dBFS
                else:
                    seg[name] = [measure(c) for c in y]
            for ch in range(x.shape[0]):
                z, th = seg["zero"][ch]["noise_a"], seg["through"][ch]["noise_a"]
                pz, pt = 10 ** (z / 10), 10 ** (th / 10)
                seg.setdefault("input_a", []).append(round(10 * np.log10(pt - pz), 1) if pt > pz * 1.05 else None)
                if "es10_in" in seg:  # the output stage alone: the interface's input floor taken out, as powers
                    pf = 10 ** (seg["es10_in"]["noise_a"] / 10)
                    seg.setdefault("zero_less_es10", []).append(round(10 * np.log10(pz - pf), 1) if pz > pf * 1.05 else None)
            take["groups"].append(seg)
        res["takes"].append(take)
    return res


def med_range(vals):
    v = [x for x in vals if x is not None]
    if not v:
        return "-"
    return f"{np.median(v):.1f} [{min(v):.1f}, {max(v):.1f}]"


def board_rows(name, r):
    rows = []
    for g, scr in enumerate(SCREENS[:3 if r["screen"] else 1]):
        for ch, lab in enumerate("LR"):
            T = [t["groups"][g] for t in r["takes"]]
            zero = [s["zero"][ch] for s in T]
            thr = [s["through"][ch] for s in T]
            rows.append([name, scr, lab,
                         med_range([z["noise_a"] for z in zero]),
                         med_range([s["noise_a"] for s in thr]),
                         med_range([s["input_a"][ch] for s in T]),
                         med_range([s.get("zero_less_es10", [None, None])[ch] for s in T]),
                         med_range([s["es10_in"]["noise_a"] for s in T if "es10_in" in s]),
                         med_range([z["hum50"] for z in zero]),
                         med_range([z["hum100"] for z in zero]),
                         med_range([z["block1k"] for z in zero]),
                         ", ".join(f"{f:.0f} Hz {d:.0f}" for f, d in zero[0]["spurs"][:3]),
                         f"{np.median([s['full_scale_vpp'][ch] for s in T]):.1f}"])
    return rows


HEAD = ["board", "screen", "ch", "out only, A-wt", "through, A-wt", "input share",
        "out only less ES-10 in", "ES-10 IN 3 floor", "hum 50",
        "hum 100", "1 kHz", "tallest spurs (out only, take 1)", "full scale Vpp"]


def table(rows):
    lines = ["| " + " | ".join(HEAD) + " |", "|" + "---|" * len(HEAD)]
    lines += ["| " + " | ".join(r) + " |" for r in rows]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("wav", nargs="?")
    ap.add_argument("--control", action="store_true")
    ap.add_argument("--summary", action="store_true")
    ap.add_argument("--gain", action="store_true")
    a = ap.parse_args()
    os.makedirs(RES, exist_ok=True)
    if a.summary:
        rows, ctrl = [], []
        for p in sorted(glob.glob(os.path.join(RES, "*.json"))):
            r = json.load(open(p))
            if r.get("gain"):
                continue
            name = os.path.basename(p)[:-5]
            if r.get("control"):
                ctrl.append(f"- {name}: " + ", ".join(f"{k} {v['noise_a']:.1f} dB A-wt, {v['noise_flat']:.1f} flat"
                                                     for k, v in zip("LR", r["channels"])))
            else:
                rows += board_rows(name, r)
        md = "# Noise test results\n\nAll levels in dB against a 10 Vpp sine; median [min, max] over three takes.\n\n"
        md += table(rows) + "\n\n## Controls\n\n" + ("\n".join(ctrl) or "none yet") + "\n"
        open(os.path.join(RES, "summary.md"), "w").write(md)
        print(md)
        return
    name = os.path.basename(a.wav).rsplit("_", 2)[0]
    if a.gain:
        r = analyse_gain(a.wav)
        for o in r["outputs"]:
            print(f"out {o['output']}: follows ES-10 {o['from_input']}, gain {o['gain_db']:+.1f} dB "
                  f"({o['gain_vv']} V/V), the other input at {o['crosstalk_db']} dB")
        json.dump(r, open(os.path.join(RES, name + ".json"), "w"), indent=1)
        print(f"-> results/{name}.json")
        return
    if a.control:
        x, _ = sf.read(a.wav, dtype="float64")
        x = np.atleast_2d(x.T) * IN_VFS
        r = {"file": os.path.basename(a.wav), "control": True,
             "channels": [measure(c[5 * FS: -5 * FS]) for c in x]}
    else:
        r = analyse_board(a.wav)
        print(table(board_rows(name, r)))
    json.dump(r, open(os.path.join(RES, name + ".json"), "w"), indent=1)
    print(f"-> results/{name}.json")


if __name__ == "__main__":
    main()

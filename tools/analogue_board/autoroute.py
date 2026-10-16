"""Trial autoroute: how much of the board Freerouting can route as placed. A routability test,
not the board's routing: the audio and CV paths are routed by hand later.

Run with KiCad's own Python (it has pcbnew), after pcb.py:

    /Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 \\
        tools/analogue_board/autoroute.py pico|teensy|<file.kicad_pcb> [passes] [4|6] [label] [--setting=value ...]

A label names the run's files (several setting trials of one board side by side); any
--setting=value goes to Freerouting as it stands, for example --router.autorouter.algorithm=
freerouting-router-v19, --router.scoring.via_costs=20, --router.fanout.enabled=false or
--router.automatic_neckdown=false. Freerouting's usage analytics are always switched off.

--lock-existing (ours, not Freerouting's) locks every track and via already on the board before
export, for a second stage on a board routed once: route the signals with fan-out off (fan-out
drops a via beside every SMD pin first, and on a dense board those vias block the tracks), then
start from that board with fan-out on to add the ground and rail connections around them.

Exports the board to Specctra DSN, runs Freerouting headless, imports the routes into a copy of
the board (<board>/output/autoroute/<name>_autoroute_trial[_6L].kicad_pcb; the real board is
never touched) and reports what is left unrouted, with the plane filled. Ground is a plane on In1
(a power layer, so Freerouting keeps other nets off it); every other net, the rails included,
is routed as tracks on the other copper layers, which is harder than the final board.

With 6, the copy gets a 6-layer stack for the trial: In1 the ground plane, In2-In4 signal. Any
other .kicad_pcb (an earlier board from git, say) is routed into an autoroute/ folder beside it.
"""

import os
import subprocess
import sys
import time

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import variant  # noqa: E402

JAVA = "/opt/homebrew/opt/openjdk@26/bin/java"   # Freerouting 2.5 needs Java 25+
JAR = os.path.expanduser("~/.local/share/freerouting/freerouting.jar")


def target(arg):
    """(board file, output folder, name) for a board name or a .kicad_pcb path."""
    if arg.endswith(".kicad_pcb"):
        path = os.path.abspath(arg)
        # the net classes (track widths, clearances, vias) live in the project file, not the board:
        # without it KiCad routes to its own defaults (0.2 mm tracks, 0.6 mm vias)
        if not os.path.exists(path[:-len(".kicad_pcb")] + ".kicad_pro"):
            raise SystemExit(f"No .kicad_pro beside {path}: copy the board's project file there under the same name")
        return path, os.path.join(os.path.dirname(path), "autoroute"), os.path.splitext(os.path.basename(path))[0]
    variant.require()
    return (os.path.join(variant.DIR, f"{variant.NAME}.kicad_pcb"), os.path.join(variant.DIR, "output", "autoroute"),
            variant.NAME)


def stack(board, layers):
    """In1 is the ground plane; with 6 layers, In2-In4 carry signals."""
    if layers == 6:
        board.SetCopperLayerCount(6)
        for layer in (pcbnew.In2_Cu, pcbnew.In3_Cu, pcbnew.In4_Cu):
            board.SetLayerType(layer, pcbnew.LT_SIGNAL)
    board.SetLayerType(pcbnew.In1_Cu, pcbnew.LT_POWER)


def stats(board):
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())   # ground reaches its pads and vias through the plane
    tracks = vias = 0
    length = 0.0
    for t in board.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T:
            vias += 1
        else:
            tracks += 1
            length += t.GetLength() / 1e6
    board.BuildConnectivity()
    unrouted = board.GetConnectivity().GetUnconnectedCount(False)
    return tracks, vias, length, unrouted


NO_ANALYTICS = ["--usage_and_diagnostic_data.disable_analytics=true", "--profile.allow_telemetry=false"]


def main(arg, passes, layers, label="", settings=()):
    path, outdir, name = target(arg)
    tag = f"{name}{'_6L' if layers == 6 else ''}{'_' + label if label else ''}"
    os.makedirs(outdir, exist_ok=True)
    board = pcbnew.LoadBoard(path)
    stack(board, layers)
    if "--lock-existing" in settings:
        settings = [s for s in settings if s != "--lock-existing"]
        locked = 0
        for t in board.GetTracks():
            t.SetLocked(True)
            locked += 1
        print(f"Locked {locked} existing tracks and vias", flush=True)
    _, _, _, before = stats(board)
    dsn = os.path.join(outdir, f"{tag}.dsn")
    ses = os.path.join(outdir, f"{tag}.ses")
    log_path = os.path.join(outdir, f"{tag}_freerouting.log")
    if not pcbnew.ExportSpecctraDSN(board, dsn):
        raise SystemExit("DSN export failed")
    with open(dsn, encoding="utf-8") as f:
        head = f.read(4000)
    rules = [line.strip() for line in head.splitlines() if line.strip().startswith(("(via ", "(width ", "(clearance "))]
    print("Routing with:", " ".join(rules[:3]), flush=True)
    t0 = time.time()
    cmd = [JAVA, "-Djava.awt.headless=true", "-jar", JAR, "-de", dsn, "-do", ses,
           f"--router.autorouter.max_passes={passes}", "--gui.enabled=false", *NO_ANALYTICS, *settings]
    print("Freerouting settings:", " ".join(settings) or "(defaults)", flush=True)
    with open(log_path, "w") as log:
        r = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, text=True)
    minutes = (time.time() - t0) / 60
    if r.returncode != 0 or not os.path.exists(ses):
        raise SystemExit(f"Freerouting failed (exit {r.returncode}); see {log_path}")
    pcbnew.ImportSpecctraSES(board, ses)
    tracks, vias, length, after = stats(board)
    trial = os.path.join(outdir, f"{tag}_autoroute_trial.kicad_pcb")
    pcbnew.SaveBoard(trial, board)
    print(f"Freerouting on {layers} layers, {passes} passes max, {minutes:.1f} min")
    print(f"Connections to make: {before}; left unrouted: {after} ({100 * (before - after) / max(before, 1):.1f}% routed)")
    print(f"Tracks: {tracks} segments, {length:.0f} mm; vias: {vias}")
    print(f"Trial board: {trial}")


if __name__ == "__main__":
    pos = [a for a in sys.argv[1:] if not a.startswith("--")]
    main(pos[0], int(pos[1]) if len(pos) > 1 else 20, int(pos[2]) if len(pos) > 2 else 4,
         pos[3] if len(pos) > 3 else "", [a for a in sys.argv[1:] if a.startswith("--")])

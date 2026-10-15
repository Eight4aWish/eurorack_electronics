"""Trial autoroute: how much of the board Freerouting can route as placed. A routability test,
not the board's routing: the audio and CV paths are routed by hand later.

Run with KiCad's own Python (it has pcbnew), after pcb.py:

    /Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 \\
        tools/analogue_board/autoroute.py [passes]

Exports the board to Specctra DSN, runs Freerouting headless, imports the routes into a copy of
the board (output/autoroute/analogue_board_autoroute_trial.kicad_pcb; the real board is never
touched) and reports what is left unrouted. Ground is a plane on In1; every other net, the
rails included, is routed as tracks on F, In2 and B, which is harder than the final board.
"""

import os
import subprocess
import sys
import time

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
HW = os.path.join(os.path.dirname(os.path.dirname(HERE)), "hardware", "analogue_board")
BOARD = os.path.join(HW, "analogue_board.kicad_pcb")
OUTDIR = os.path.join(HW, "output", "autoroute")
JAVA = "/opt/homebrew/opt/openjdk@26/bin/java"   # Freerouting 2.5 needs Java 25+
JAR = os.path.expanduser("~/.local/share/freerouting/freerouting.jar")


def stats(board):
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


def main(passes):
    os.makedirs(OUTDIR, exist_ok=True)
    board = pcbnew.LoadBoard(BOARD)
    _, _, _, before = stats(board)
    dsn = os.path.join(OUTDIR, "analogue_board.dsn")
    ses = os.path.join(OUTDIR, "analogue_board.ses")
    if not pcbnew.ExportSpecctraDSN(board, dsn):
        raise SystemExit("DSN export failed")
    t0 = time.time()
    cmd = [JAVA, "-Djava.awt.headless=true", "-jar", JAR, "-de", dsn, "-do", ses, "-mp", str(passes),
           "--gui.enabled=false"]
    with open(os.path.join(OUTDIR, "freerouting.log"), "w") as log:
        r = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, text=True)
    minutes = (time.time() - t0) / 60
    if r.returncode != 0 or not os.path.exists(ses):
        raise SystemExit(f"Freerouting failed (exit {r.returncode}); see {OUTDIR}/freerouting.log")
    pcbnew.ImportSpecctraSES(board, ses)
    trial = os.path.join(OUTDIR, "analogue_board_autoroute_trial.kicad_pcb")
    pcbnew.SaveBoard(trial, board)
    tracks, vias, length, after = stats(board)
    print(f"Freerouting, {passes} passes max, {minutes:.1f} min")
    print(f"Connections to make: {before}; left unrouted: {after} ({100 * (before - after) / max(before, 1):.1f}% routed)")
    print(f"Tracks: {tracks} segments, {length:.0f} mm; vias: {vias}")
    print(f"Trial board: {trial}")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 20)

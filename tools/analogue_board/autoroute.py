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

--unlock (ours) unlocks every track and via but ground's first (a board from the staged route
has them all locked), so a last pass may rip up and reroute them to make the last few
connections; the ground vias to the plane stay put.

--ground-vias (ours) first gives every surface-mount ground pad its own via to the plane
(finish.fan_out_ground), locked, so the router routes around them instead of joining ground
pads to each other with tracks. With --staged it applies to stage 1.

--plane=<net> (ours) adds a plane for that net on In4 (6 layers only), with the ground plane's
outline and settings; with --ground-vias its surface-mount pads get their own vias to it too.

--decoupling (ours) then wires each decoupling capacitor to the pin it serves with a short
locked track (finish.fan_in_decoupling), so every power pin has its own capacitor beside it
in copper, not only in placement. With --staged it applies to stage 1.

With 6, the copy gets a 6-layer stack for the trial: In1 the ground plane, In2-In4 signal. Any
other .kicad_pcb (an earlier board from git, say) is routed into an autoroute/ folder beside it.
"""

import os
import shutil
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
        here = os.path.dirname(path)
        # a trial board routes again into its own folder, under its own name
        outdir = here if os.path.basename(here) == "autoroute" else os.path.join(here, "autoroute")
        name = os.path.splitext(os.path.basename(path))[0]
        return path, outdir, name[:-len("_autoroute_trial")] if name.endswith("_autoroute_trial") else name
    variant.require()
    return (os.path.join(variant.DIR, f"{variant.NAME}.kicad_pcb"), os.path.join(variant.DIR, "output", "autoroute"),
            variant.NAME)


def stack(board, layers):
    """In1 is the ground plane; with 6 layers, In2-In4 carry signals, except a layer holding
    another plane (--plane), which stays a power layer."""
    if layers == 6:
        board.SetCopperLayerCount(6)
        for layer in (pcbnew.In2_Cu, pcbnew.In3_Cu, pcbnew.In4_Cu):
            board.SetLayerType(layer, pcbnew.LT_SIGNAL)
    board.SetLayerType(pcbnew.In1_Cu, pcbnew.LT_POWER)
    for z in board.Zones():
        if not z.GetIsRuleArea() and z.GetNetCode() > 0:
            for layer in z.GetLayerSet().CuStack():
                board.SetLayerType(layer, pcbnew.LT_POWER)


def add_plane(board, name, layer=pcbnew.In4_Cu):
    """A plane for net `name` on `layer` over the whole board, with the ground plane's outline and
    settings: its pins then join it by a via, as ground's do (2026-10-16: rails were 71 of 102
    connections left over across six routes, +5VD the most)."""
    g = next(z for z in board.Zones() if not z.GetIsRuleArea() and z.GetNetname() == "GND")
    z = pcbnew.ZONE(board)
    z.SetLayer(layer)
    z.SetNetCode(board.FindNet(name).GetNetCode())
    z.SetZoneName(f"{name} plane")
    z.SetLocalClearance(g.GetLocalClearance())
    z.SetMinThickness(g.GetMinThickness())
    z.SetPadConnection(g.GetPadConnection())
    z.SetThermalReliefGap(g.GetThermalReliefGap())
    z.SetThermalReliefSpokeWidth(g.GetThermalReliefSpokeWidth())
    z.SetIslandRemovalMode(g.GetIslandRemovalMode())
    src = g.Outline().COutline(0)
    for i in range(src.PointCount()):
        z.AppendCorner(src.CPoint(i), -1)
    board.Add(z)
    board.SetLayerType(layer, pcbnew.LT_POWER)
    return z


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
    tag = f"{name}{'_6L' if layers == 6 and '_6L' not in name else ''}{'_' + label if label else ''}"
    os.makedirs(outdir, exist_ok=True)
    board = pcbnew.LoadBoard(path)
    planes = [s.split("=", 1)[1] for s in settings if s.startswith("--plane=")]
    settings = [s for s in settings if not s.startswith("--plane=")]
    if planes and layers != 6:
        raise SystemExit("--plane needs 6 layers: it takes In4")
    for name in planes:
        add_plane(board, name)
        print(f"Plane for {name} on In4", flush=True)
    stack(board, layers)
    if "--ground-vias" in settings or "--decoupling" in settings:
        import finish
        finish.load_rules(path[:-len(".kicad_pcb")] + ".kicad_pro")   # the board's own track and clearance
        if planes:
            pcbnew.ZONE_FILLER(board).Fill(board.Zones())   # so the new plane's copper is known
    if "--ground-vias" in settings:
        settings = [s for s in settings if s != "--ground-vias"]
        import finish
        placed, failed = finish.fan_out_ground(board)
        print(f"Ground vias placed before routing: {placed}; no room beside {len(failed)} pads: {failed}", flush=True)
        for name in planes:
            placed, failed = finish.fan_out_ground(board, net_name=name)
            print(f"{name} vias placed before routing: {placed}; no room beside {len(failed)} pads: {failed}", flush=True)
        for t in board.GetTracks():
            t.SetLocked(True)
    if "--decoupling" in settings:
        settings = [s for s in settings if s != "--decoupling"]
        import finish
        made, failed = finish.fan_in_decoupling(board)
        for t in board.GetTracks():
            t.SetLocked(True)
        print(f"Decoupling capacitors wired to their pins before routing: {made}; no short path: {failed}", flush=True)
    if "--unlock" in settings:
        settings = [s for s in settings if s != "--unlock"]
        for t in board.GetTracks():
            t.SetLocked(t.GetNetname() == "GND")
        print("Every track and via but ground's unlocked: the router may rip them up", flush=True)
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
    shutil.copy(path[:-len(".kicad_pcb")] + ".kicad_pro", trial[:-len(".kicad_pcb")] + ".kicad_pro")   # rules travel with it
    print(f"Freerouting on {layers} layers, {passes} passes max, {minutes:.1f} min")
    print(f"Connections to make: {before}; left unrouted: {after} ({100 * (before - after) / max(before, 1):.1f}% routed)")
    print(f"Tracks: {tracks} segments, {length:.0f} mm; vias: {vias}")
    print(f"Trial board: {trial}", flush=True)
    return trial


# The staged route (spec §14, 2026-10-16): signals first with Freerouting's fan-out off (on a dense
# board its via beside every SMD pin blocks the tracks), then ground and rails with those tracks
# locked and fan-out on, then a last pass with cheap plane vias and a high rip-up cost
COMMON = ["--router.automatic_neckdown=false", "--router.hole_clearance_um=250", "--router.copper_to_edge_clearance_um=500"]
STAGES = [("s1", ["--router.fanout.enabled=false", "--router.scoring.via_costs=20", "--router.scoring.plane_via_costs=2"]),
          ("s2", ["--lock-existing"]),
          ("s3", ["--lock-existing", "--router.scoring.plane_via_costs=1", "--router.scoring.start_ripup_costs=400"])]


def staged(arg, passes, layers, prefix="", first=(), upto=len(STAGES)):
    """The stages in turn, each starting from the last one's board. `prefix` keeps one staged
    run's files apart from another's on the same board; `first` adds settings to stage 1
    (--ground-vias, say); `upto` stops early (stage 3 has made 2 connections in 25-35 min on
    every board since the ground vias went in first: finish.py does that work faster)."""
    board = arg
    for label, settings in STAGES[:upto]:
        print(f"\n== stage {label}", flush=True)
        board = main(board, passes, layers, f"{prefix}_{label}" if prefix and label == "s1" else label,
                     COMMON + settings + (list(first) if label == "s1" else []))
    return board


if __name__ == "__main__":
    pos = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = [a for a in sys.argv[1:] if a.startswith("--")]
    passes, layers = int(pos[1]) if len(pos) > 1 else 20, int(pos[2]) if len(pos) > 2 else 4
    if "--staged" in flags:
        upto = [int(f.split("=")[1]) for f in flags if f.startswith("--stages=")]
        staged(pos[0], passes, layers, pos[3] if len(pos) > 3 else "",
               [f for f in flags if f != "--staged" and not f.startswith("--stages=")], *(upto[:1] or []))
    else:
        main(pos[0], passes, layers, pos[3] if len(pos) > 3 else "", flags)

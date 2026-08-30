#!/usr/bin/env python3
"""
Cross-check: does each component in the layout JSON terminate on the nets the
netlist requires?

The layout JSON encodes WHERE a component sits (which row+col pair). The
netlist says WHAT NET each pin should be on. This script bridges the two.

Algorithm:
  1. Build a "known net" map for every (row, side) tuple, derived from IC pins
     and power-rail parity. IC pins anchor their row-side to a specific net.
  2. For each two-pin component (twoPins), look up its expected (net1, net2)
     pair from EXPECTED_NETS below.
  3. Look up what net each endpoint is on. If a row-side has no IC pin, the net
     is "bare" — derived from BARE_ROW_NETS (manual mapping from netlist).
  4. Report matches and mismatches.

When the netlist changes, update EXPECTED_NETS and BARE_ROW_NETS here.
"""
import json
import sys
from pathlib import Path


# ============================================================================
# EXPECTED NETS — from docs/lpg_netlist.md rev 0.4.
# Format: component_id -> (pin1_net, pin2_net). Net-name order doesn't matter
# (the script accepts either ordering).
# Names match the IC-pin `net` field in the layout JSON where they overlap.
# ============================================================================
EXPECTED_NETS = {
    # Block 1 — Audio Input Buffer (input pulldowns)
    'R1': ('CHA_IN', 'GND'),
    'R7': ('CHB_IN', 'GND'),

    # Block 2 — Canonical Buchla 292 Audio Path (Ch A)
    # Rev 0.9 fix: R_alpha (R3, R9) is V_p → GND in parallel with C13/C14.
    # Confirmed against Aalto/DAFx 2013 Eqs. 4 + 12, Bergmann (R13),
    # Thomas White redraw (R13). Previous V_x→V_p placement was incorrect.
    'R4':  ('BUF_OUT_A', 'VC_A_LDR1_IN'),
    'C11': ('V_x_A', 'GND'),
    'R3':  ('V_p_A', 'GND'),
    'C13': ('V_p_A', 'GND'),
    'R5':  ('V_p_A', 'V_OUT_A_PRE_BUF'),

    # Block 2 — Audio Path (Ch B mirror)
    'R10': ('BUF_OUT_B', 'VC_B_LDR1_IN'),
    'C12': ('V_x_B', 'GND'),
    'R9':  ('V_p_B', 'GND'),
    'C14': ('V_p_B', 'GND'),
    'R11': ('V_p_B', 'V_OUT_B_PRE_BUF'),

    # Block 4 — Strike Pulse Shaper (Ch A)
    'R17': ('CHA_STRIKE', 'C15_a'),
    'C15': ('C15_a', 'C15_b'),
    'R15': ('C15_b', 'GND'),
    'VD1': ('C15_b', 'STRIKE_PULSE_A'),    # anode at C15_b, cathode at STRIKE_PULSE_A

    # Block 4 — Strike Pulse Shaper (Ch B)
    'R25': ('CHB_STRIKE', 'C16_a'),
    'C16': ('C16_a', 'C16_b'),
    'R31': ('C16_b', 'GND'),
    'VD2': ('C16_b', 'STRIKE_PULSE_B'),

    # Block 5 — Driver (Ch A) — note: R_STATUS_A is panel-side (rev 0.7+), not on-board
    'R16': ('CHA_CV', 'CV_PROT_A'),
    'R13': ('CV_PROT_A', 'GND'),
    'R38': ('CV_WIPER_A', 'DRV_SUM_A'),
    'R29': ('VCC', 'P2_TOP_A'),
    'R32': ('MAN_WIPER_A', 'DRV_SUM_A'),
    'R34': ('STRIKE_PULSE_A', 'DRV_SUM_A'),
    'R36': ('DRV_SUM_A', 'DRV_OUT_A'),
    'R37': ('DRV_A_NINV', 'GND'),
    'R6':  ('DEPTH_WIPER_A', 'LED_DRIVE_A'),
    'VD5': ('LED_DRIVE_A', 'GND'),         # anode at LED_DRIVE_A, cathode at GND

    # Block 5 — Driver (Ch B mirror) — note: R_STATUS_B is panel-side (rev 0.7+)
    'R22': ('CHB_CV', 'CV_PROT_B'),
    'R19': ('CV_PROT_B', 'GND'),
    'R39': ('CV_WIPER_B', 'DRV_SUM_B'),
    'R30': ('VCC', 'P6_TOP_B'),
    'R33': ('MAN_WIPER_B', 'DRV_SUM_B'),
    'R35': ('STRIKE_PULSE_B', 'DRV_SUM_B'),
    'R20': ('DRV_SUM_B', 'DRV_OUT_B'),
    'R14': ('DRV_B_NINV', 'GND'),
    'R12': ('DEPTH_WIPER_B', 'LED_DRIVE_B'),
    'VD6': ('LED_DRIVE_B', 'GND'),

    # Rev 0.14 — formerly panel-side resistors, now on the board via control holes
    'R_OUT_A':    ('CHA_OUT', 'CHA_OUT_JACK'),
    'R_OUT_B':    ('CHB_OUT', 'CHB_OUT_JACK'),
    'R_STATUS_A': ('DRV_OUT_A', 'LED_STATUS_A'),
    'R_STATUS_B': ('DRV_OUT_B', 'LED_STATUS_B'),

    # Block 6 — Mix Output Buffer
    'R23': ('CHA_OUT', 'MIX_BUS'),
    'R26': ('CHB_OUT', 'MIX_BUS'),
    'R24': ('MIX_BUS', 'MIX_OUT'),
    'R28': ('MIX_NINV', 'GND'),
    'C17': ('MIX_OUT', 'MIX_OUT_JACK'),  # DC-blocking cap

    # Power decoupling — one cap per rail per IC
    # IC pin 8 = VCC, pin 4 = VEE per all our TL072s in rotation=180
    'C3':  ('VCC', 'GND'),
    'C4':  ('VEE', 'GND'),
    'C5':  ('VCC', 'GND'),
    'C6':  ('VEE', 'GND'),
    'C7':  ('VCC', 'GND'),
    'C8':  ('VEE', 'GND'),
    'C9':  ('VCC', 'GND'),
    'C10': ('VEE', 'GND'),
}


# ============================================================================
# BARE-ROW NET ASSIGNMENTS — for (row, side) tuples with no IC pin.
# The script uses this to interpret "bare" rows. If a row appears here, its
# net is the named one. If it doesn't appear and isn't anchored by an IC pin,
# the script will flag it as "unknown bare net".
#
# Mostly off-board panel-wire stubs and inter-component bus nets.
# ============================================================================
BARE_ROW_NETS = {
    # On-board junction nodes for the strike/CV chains. The panel-facing ends
    # of these chains (jacks, pot wipers/tops) now live on control holes — see
    # the rev 0.15/0.16 control-hole block below.
    # Channel A
    # Rev 0.23 — the C15 block moved to the RIGHT half and the ch-A vactrol
    # dropped a row, freeing 10-13 left. 5L and 10L are now local ground rows,
    # fed from the rail so nearby parts need not stretch to reach it.
    (5,  'L'): 'GND',            # local ground: C3.r2, R3.r1, C13.r2
    (10, 'L'): 'GND',            # local ground: VD5 cathode
    (26, 'L'): 'GND',            # local ground: VD6 cathode (ch B mirror)
    (13, 'R'): 'C15_a',          # R17.r2, C15.r1
    (11, 'R'): 'C15_b',          # C15.r2, R15.r1, VD1.r1
    (12, 'R'): 'STRIKE_PULSE_A', # VD1.r2 (cathode), R34.r1
    # Rev 0.23 — spare edge positions used as routing tie points. The wire lands
    # in one hole of the doublet and the component leg in the other; same pad.
    (11, 'ctrlR'): 'LED_DRIVE_A',  # JW_R6_LED_A (front) from b8; R6.r2
    (15, 'ctrlR'): 'MAN_WIPER_A',  # R32.r1; JW_R32_MAN_A (back) to ctrlLi5
    (13, 'ctrlR'): 'LED_STATUS_A', # R_STATUS_A.r2; JW_STATA (back) to ctrlLi8
    # Rev 0.24 — channel B mirrors A: vactrol up one row, the C16 block moved to
    # the RIGHT half, CV_PROT_B pushed from 20R to 21R to make room for it.
    (21, 'R'): 'CV_PROT_B',      # R19.r1, R22.r2
    (20, 'R'): 'C16_a',          # R25.r2, C16.r1
    (18, 'R'): 'C16_b',          # C16.r2, R31.r1, VD2.r1 (anode)
    # VD2 jumps the centre gap on row 18, so STRIKE_PULSE_B stays on the LEFT
    # half where R35 already reaches it — 19R is not needed.
    # Rev 0.25 — left-hand gap positions used as routing tie points. Each carries
    # whatever net its wire brings; the component sits in one hole, the wire the other.
    (11, 'ctrlL'): 'CHA_OUT',       # JW_CHA_OUT_BUS (front) in; JW_CHA_OUT_X (back) out
    (28, 'ctrlR'): 'CHA_OUT',       # arrives from 11L; R23.r1
    (13, 'ctrlL'): 'CV_WIPER_B',    # R39.r1; JW_R39_CVB (back) to ctrlRi33
    (14, 'ctrlL'): 'LED_STATUS_B',  # R_STATUS_B.r2; JW_STATB (back) to ctrlLi33
    (15, 'ctrlL'): 'DRV_SUM_B',     # JW_R33_IN (front) from b15; JW_R33_X (back) out
    (30, 'ctrlR'): 'DRV_SUM_B',     # arrives from 15L; R33.r2
    (30, 'ctrlL'): 'P6_TOP_B',      # R30.r2; JW_R30_12V (back) to ctrlRi37
    # Rev 0.26 — right-hand gap positions. R16, R17 and R22 sit above board in the
    # control-board area, each fed by a wire from the main grid.
    (12, 'ctrlR'): 'C15_a',      # JW_R17_IN (front) from h13; R17.r2
    (14, 'ctrlR'): 'CV_PROT_A',  # JW_R16_IN (front) from j10; R16.r2
    (29, 'ctrlR'): 'CHB_CV',     # R22.r1 from j21; JW_R22_X (back) to ctrlRi38
    (10, 'R'): 'CV_PROT_A',      # R16.r2, R13.r1
    # Channel B
    (20, 'L'): 'C16_a',          # R25.r2, C16.r1
    (19, 'L'): 'C16_b',          # C16.r2, R31.r1, VD2.r1
    (18, 'L'): 'STRIKE_PULSE_B', # VD2.r2, R35.r1

    # Mix bus tap nodes
    (31, 'L'): 'MIX_OUT_JACK',   # JW_MIX lands a31; C17.r2
                                 # (CHA_OUT now runs 11L -> 28R, see above)
    (31, 'R'): 'CHB_OUT',        # via JW_CHB_OUT_BUS from row 29L; R26.r1
    (32, 'L'): 'MIX_OUT',        # C17.r1; JW_MIX_OUT_X (front) carries it to 36R

    # Rev 0.8 — VC_X bridge intermediate cols (the centre-gap bridges land here
    # but the nets are also anchored by IC pins on the same row, so they're
    # auto-resolved. No new entries needed for rows 5-8 or 23-26.

    # Rev 0.15 — Channel A re-allocated to the REAL n8synth control positions
    # (ctrlL / ctrlR, outboard of the power rails). Each hole carries the panel net
    # the builder routes it to.
    (17, 'ctrlR'): 'CHA_CV',        # R16.1 -> CV A
    (20, 'ctrlR'): 'CHA_STRIKE',    # R17.1 -> STRIKE A
    (8,  'ctrlR'): 'CV_WIPER_A',    # R38.1 -> ATTEN A b (wiper)
    (6,  'ctrlL'): 'P2_TOP_A',      # R29.1 -> MANUAL A c (top)
    (5,  'ctrlL'): 'MAN_WIPER_A',   # R32.1 -> MANUAL A b (wiper)
    (5,  'ctrlR'): 'DEPTH_WIPER_A', # R6.1  -> DEPTH A b (wiper)
    (1,  'ctrlL'): 'CHA_OUT_JACK',  # R_OUT_A.2 -> OUT A
    (8,  'ctrlL'): 'LED_STATUS_A',  # R_STATUS_A.2 -> LED A b (cathode)
    # Rev 0.16 — Channel B re-allocated to the REAL n8synth control positions:
    (38, 'ctrlR'): 'CHB_CV',        # R22.1 -> CV B
    (35, 'ctrlL'): 'CHB_STRIKE',    # R25.1 -> STRIKE B
    (33, 'ctrlR'): 'CV_WIPER_B',    # R39.1 -> ATTEN B b (wiper)
    (37, 'ctrlR'): 'P6_TOP_B',      # R30.1 -> MANUAL B c (top)
    (36, 'ctrlR'): 'MAN_WIPER_B',   # R33.1 -> MANUAL B b (wiper)
    (21, 'ctrlL'): 'DEPTH_WIPER_B', # R12.1 -> DEPTH B b (wiper)
    (23, 'ctrlL'): 'CHB_OUT_JACK',  # R_OUT_B.2 -> OUT B
    (33, 'ctrlL'): 'LED_STATUS_B',  # R_STATUS_B.2 -> LED B b (cathode)
}


def side(c):
    """Normalise a column to its electrical LANE.

    Edge-connector doublets (ctrlLo/ctrlLi, ctrlRo/ctrlRi) are two holes on ONE
    node, so both resolve to the same lane. Collision checks must still key on
    the raw column, since the two holes are physically distinct.
    See docs/n8synth_platform.md.
    """
    if c is None:
        return None
    if c in 'abcde':
        return 'L'
    if c in 'fghij':
        return 'R'
    if c in ('ctrlLo', 'ctrlLi'):
        return 'ctrlL'
    if c in ('ctrlRo', 'ctrlRi'):
        return 'ctrlR'
    return c   # pwrL / pwrR / ctrlL / ctrlR


def power_rail_net(rail, row):
    """pwrL/pwrR parity rule from index.html lines 91, 96."""
    if rail == 'pwrL':
        return 'GND' if row % 2 == 1 else 'VCC'
    if rail == 'pwrR':
        return 'GND' if row % 2 == 1 else 'VEE'
    return None


def main():
    layout_path = Path(sys.argv[1]) if len(sys.argv) > 1 else (
        Path(__file__).parent / 'layouts' / 'lpg.json')
    with open(layout_path) as f:
        layout = json.load(f)

    # === 1. Build row-side -> net map from IC pins ===
    rs_net = {}
    for ic in layout['ics']:
        for pin in ic['pins']:
            key = (pin['r'], side(pin['c']))
            net = pin.get('net')
            if key in rs_net and rs_net[key] != net:
                print(f"  ⚠️  IC-pin conflict at {key}: {rs_net[key]} vs {net}")
            rs_net[key] = net

    # === 2. Walk twoPins and check expected vs actual ===
    matches = []
    mismatches = []
    not_checked = []
    bare_rows_used = set()

    for c in layout.get('twoPins', []):
        cid = c['id']
        expected = EXPECTED_NETS.get(cid)
        if expected is None:
            not_checked.append(cid)
            continue

        def resolve(r, col):
            s = side(col)
            if s in ('pwrL', 'pwrR'):
                return power_rail_net(s, r), True
            key = (r, s)
            if key in rs_net:
                return rs_net[key], True
            # bare row — check the manual map
            if key in BARE_ROW_NETS:
                bare_rows_used.add(key)
                return BARE_ROW_NETS[key], True
            return f"BARE({r}{s})", False

        n1, ok1 = resolve(c['r1'], c['c1'])
        n2, ok2 = resolve(c['r2'], c['c2'])
        actual = (n1, n2)
        exp_set = set(expected)
        act_set = set(actual)
        if exp_set == act_set:
            matches.append((cid, expected, actual))
        else:
            mismatches.append((cid, expected, actual, ok1, ok2))

    # === 3. Report ===
    print(f"=== NET IDENTITY CROSS-CHECK — {layout_path.name} (rev {layout.get('revision', '?')}) ===\n")
    print(f"  ✓ {len(matches)} components match expected nets")
    print(f"  ✗ {len(mismatches)} components MISMATCH")
    print(f"  ?  {len(not_checked)} components not in EXPECTED_NETS (extend the script): {not_checked}")
    print(f"  ℹ️ {len(bare_rows_used)} bare-row net assumptions used: {sorted(bare_rows_used)}")
    print()

    if mismatches:
        print("=== MISMATCHES (these are the bugs to fix) ===\n")
        for cid, exp, act, ok1, ok2 in mismatches:
            mark1 = '' if ok1 else ' [unresolved bare row]'
            mark2 = '' if ok2 else ' [unresolved bare row]'
            print(f"  {cid:14}  expected: {exp[0]:20} / {exp[1]:20}")
            print(f"                   actual: {act[0]:20}{mark1} / {act[1]:20}{mark2}")
            print()
        sys.exit(1)
    else:
        print("✓ All components in EXPECTED_NETS terminate on the right nets.")
        sys.exit(0)


if __name__ == '__main__':
    main()

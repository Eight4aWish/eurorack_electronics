#!/usr/bin/env python3
"""
edit_layout.py — apply text edit commands to a breadboard layout JSON.

For reconciling a documented layout against the board actually on the bench:
read a position off a photo, type one line, re-run the checks.

Usage:
    python3 edit_layout.py layouts/lpg.json -e "C15 = g12 g13"
    python3 edit_layout.py layouts/lpg.json -f edits.txt --rev 0.20
    python3 edit_layout.py layouts/lpg.json -e "b10 > g12" --dry-run

Commands (one per line; '#' starts a comment):

  MOVE A SINGLE ENDPOINT, by where it currently is
      b10 > g12                 whatever endpoint sits at b10 moves to g12

  SET A COMPONENT'S ENDPOINTS, by designator
      C15 = g12 g13             set both ends
      C15.1 = g12               set end 1 only        (.2 for the other end)

  MIRROR LEFT <-> RIGHT  (a<->j b<->i c<->h d<->g e<->f, pwrL<->pwrR, ctrlL<->ctrlR)
      mirror C15                one component
      mirror C15 C16 R20        several

  SHIFT ROWS
      shift C15 +2              move both ends down two rows
      shift rows 12-20 +1       every endpoint in that row range, twoPins and ICs

  ICs (addressed by pin-1 row; all pins move together)
      IC DA3 = 15               put DA3's lowest-numbered pin row at 15
      IC DA3 shift +1
      mirror IC DA3

Positions are <column><row>, e.g. a5, j17, pwrL12, ctrlR8.
Every edit is checked for hole collisions before the file is written.
"""

import argparse, json, re, sys, copy
from collections import defaultdict

MIRROR = {'a':'j','b':'i','c':'h','d':'g','e':'f',
          'f':'e','g':'d','h':'c','i':'b','j':'a',
          'pwrL':'pwrR','pwrR':'pwrL','ctrlL':'ctrlR','ctrlR':'ctrlL'}

POS = re.compile(r'^(pwrL|pwrR|ctrlL|ctrlR|[a-j])(\d+)$')


def parse_pos(tok):
    m = POS.match(tok)
    if not m:
        raise ValueError(f"bad position {tok!r} (want e.g. a5, j17, pwrL12, ctrlR8)")
    return m.group(1), int(m.group(2))


def endpoints(layout):
    """Yield (holder, kind, index, col, row) for every editable endpoint."""
    for t in layout.get('twoPins', []):
        yield t, 'twoPin', 1, t['c1'], t['r1']
        yield t, 'twoPin', 2, t['c2'], t['r2']
    for ic in layout.get('ics', []):
        for p in ic.get('pins', []):
            yield ic, 'icPin', p, p['c'], p['r']


def set_endpoint(holder, kind, idx, col, row):
    if kind == 'twoPin':
        holder[f'c{idx}'] = col
        holder[f'r{idx}'] = row
    else:
        idx['c'] = col
        idx['r'] = row


def find_two_pin(layout, cid):
    for t in layout.get('twoPins', []):
        if t['id'] == cid:
            return t
    return None


def find_ic(layout, cid):
    for ic in layout.get('ics', []):
        if ic['id'] == cid:
            return ic
    return None


def collisions(layout):
    seen = defaultdict(list)
    for holder, kind, idx, col, row in endpoints(layout):
        seen[(col, row)].append(holder['id'])
    return {k: v for k, v in seen.items() if len(v) > 1}


# ── command handlers ────────────────────────────────────────────────────────

def cmd_move(layout, src, dst, log):
    sc, sr = parse_pos(src); dc, dr = parse_pos(dst)
    hits = [(h, k, i) for h, k, i, c, r in endpoints(layout) if c == sc and r == sr]
    if not hits:
        raise ValueError(f"nothing at {src}")
    if len(hits) > 1:
        raise ValueError(f"{len(hits)} endpoints at {src} — address by designator instead")
    h, k, i = hits[0]
    set_endpoint(h, k, i, dc, dr)
    log.append(f"  {h['id']}: {src} -> {dst}")


def cmd_set(layout, cid, which, positions, log):
    t = find_two_pin(layout, cid)
    if not t:
        raise ValueError(f"no twoPin {cid!r} (use 'IC {cid} = <row>' for an IC)")
    if which:
        c, r = parse_pos(positions[0])
        old = f"{t['c'+which]}{t['r'+which]}"
        t['c'+which], t['r'+which] = c, r
        log.append(f"  {cid} end {which}: {old} -> {positions[0]}")
    else:
        if len(positions) != 2:
            raise ValueError(f"{cid} = needs two positions")
        old = f"{t['c1']}{t['r1']}..{t['c2']}{t['r2']}"
        (t['c1'], t['r1']) = parse_pos(positions[0])
        (t['c2'], t['r2']) = parse_pos(positions[1])
        log.append(f"  {cid}: {old} -> {positions[0]}..{positions[1]}")


def _mirror_col(c):
    if c not in MIRROR:
        raise ValueError(f"cannot mirror column {c!r}")
    return MIRROR[c]


def cmd_mirror(layout, cid, log):
    t = find_two_pin(layout, cid)
    if t:
        old = f"{t['c1']}{t['r1']}..{t['c2']}{t['r2']}"
        t['c1'] = _mirror_col(t['c1']); t['c2'] = _mirror_col(t['c2'])
        log.append(f"  {cid} mirrored: {old} -> {t['c1']}{t['r1']}..{t['c2']}{t['r2']}")
        return
    ic = find_ic(layout, cid)
    if ic:
        for p in ic.get('pins', []):
            p['c'] = _mirror_col(p['c'])
        log.append(f"  IC {cid} mirrored ({len(ic.get('pins', []))} pins)")
        return
    raise ValueError(f"no component {cid!r}")


def cmd_shift(layout, cid, delta, log):
    t = find_two_pin(layout, cid)
    if t:
        old = f"{t['c1']}{t['r1']}..{t['c2']}{t['r2']}"
        t['r1'] += delta; t['r2'] += delta
        log.append(f"  {cid} shifted {delta:+d}: {old} -> {t['c1']}{t['r1']}..{t['c2']}{t['r2']}")
        return
    ic = find_ic(layout, cid)
    if ic:
        for p in ic.get('pins', []):
            p['r'] += delta
        log.append(f"  IC {cid} shifted {delta:+d}")
        return
    raise ValueError(f"no component {cid!r}")


def cmd_shift_rows(layout, lo, hi, delta, log):
    n = 0
    for holder, kind, idx, col, row in list(endpoints(layout)):
        if lo <= row <= hi:
            set_endpoint(holder, kind, idx, col, row + delta)
            n += 1
    log.append(f"  rows {lo}-{hi} shifted {delta:+d}: {n} endpoints")


def cmd_ic_set(layout, cid, row, log):
    ic = find_ic(layout, cid)
    if not ic:
        raise ValueError(f"no IC {cid!r}")
    pins = ic.get('pins', [])
    if not pins:
        raise ValueError(f"IC {cid} has no placed pins")
    cur = min(p['r'] for p in pins)
    delta = row - cur
    for p in pins:
        p['r'] += delta
    log.append(f"  IC {cid}: pin-1 row {cur} -> {row} ({delta:+d}, {len(pins)} pins)")


def apply_line(layout, line, log):
    line = line.split('#')[0].strip()
    if not line:
        return
    toks = line.replace('=', ' = ').replace('>', ' > ').split()

    if toks[0] == 'mirror':
        rest = toks[1:]
        if rest and rest[0] == 'IC':
            rest = rest[1:]
        for cid in rest:
            cmd_mirror(layout, cid, log)
        return

    if toks[0] == 'shift':
        if toks[1] == 'rows':
            lo, hi = toks[2].split('-')
            cmd_shift_rows(layout, int(lo), int(hi), int(toks[3]), log)
        else:
            cmd_shift(layout, toks[1], int(toks[2]), log)
        return

    if toks[0] == 'IC':
        if '=' in toks:
            cmd_ic_set(layout, toks[1], int(toks[toks.index('=') + 1]), log)
        elif 'shift' in toks:
            cmd_shift(layout, toks[1], int(toks[toks.index('shift') + 1]), log)
        else:
            raise ValueError(f"bad IC command: {line!r}")
        return

    if '>' in toks:
        i = toks.index('>')
        cmd_move(layout, toks[i - 1], toks[i + 1], log)
        return

    if '=' in toks:
        i = toks.index('=')
        target = toks[i - 1]
        m = re.match(r'^(\w+)\.([12])$', target)
        if m:
            cmd_set(layout, m.group(1), m.group(2), toks[i + 1:], log)
        else:
            cmd_set(layout, target, None, toks[i + 1:], log)
        return

    raise ValueError(f"unrecognised command: {line!r}")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('layout')
    ap.add_argument('-e', '--edit', action='append', default=[], help='an edit command')
    ap.add_argument('-f', '--file', help='file of edit commands, one per line')
    ap.add_argument('--rev', help='set the layout revision string')
    ap.add_argument('--dry-run', action='store_true', help='show changes, write nothing')
    args = ap.parse_args()

    layout = json.load(open(args.layout))
    before = copy.deepcopy(layout)

    cmds = list(args.edit)
    if args.file:
        cmds += open(args.file).read().splitlines()

    if not cmds:
        ap.error('no edits given (-e or -f)')

    log, errs = [], []
    for line in cmds:
        try:
            apply_line(layout, line, log)
        except Exception as ex:
            errs.append(f"  {line.strip()!r}: {ex}")

    print(f"=== EDITS — {args.layout} ===\n")
    for l in log:
        print(l)
    if not log:
        print("  (none applied)")

    if errs:
        print(f"\n✗ {len(errs)} command(s) failed:")
        for e in errs:
            print(e)
        print("\nNothing written.")
        return 1

    coll = collisions(layout)
    if coll:
        print(f"\n✗ {len(coll)} hole collision(s) introduced:")
        for (c, r), ids in sorted(coll.items(), key=lambda x: (x[0][1], x[0][0])):
            print(f"    {c}{r}: {', '.join(ids)}")
        print("\nNothing written.")
        return 1

    print(f"\n✓ {len(log)} edit(s) applied, no hole collisions.")

    if args.rev:
        layout['revision'] = args.rev
        print(f"  revision -> {args.rev}")

    if args.dry_run:
        print("\n(dry run — nothing written)")
        return 0

    with open(args.layout, 'w') as f:
        json.dump(layout, f, indent=2)
        f.write('\n')
    print(f"\nWrote {args.layout}")
    print("Now re-run:  ./check.sh " + args.layout)
    return 0


if __name__ == '__main__':
    sys.exit(main())

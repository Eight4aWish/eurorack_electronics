#!/usr/bin/env python3
"""
check_netlist.py - does a layout wire up the circuit it is meant to?

validate_layout.py checks the board: holes, rails, chips, the deck. It can't know the circuit.
This does: it works out which pins each layout joins, by the node each one lands on and the wires
between nodes, and compares that with a netlist. A row that joins the wrong pins is a SHORT, and a
wire left out is an OPEN, however tidy the drawing looks.

Usage:
    python3 check_netlist.py layouts/foo.json foo.net
    python3 check_netlist.py layouts/foo.json foo.net --show     also list each net's holes

The netlist is plain text, one net per line, with # for comments:

    +12V: rail:+12V D1.A
    VCC: D1.K U1.8 C1.1
    GND: rail:GND C1.2 R2.2 J1.C
    OUT: U1.1 R3.1
    JACK: R3.2 J1.A
    NC: U1.5                  # pins that must connect to nothing

A member is part.pin, as the layout names it:
    a chip              U1.8      ics[].id and pins[].n
    a two-pin part      R3.1      twoPins[].id; pin 1 is r1/c1, pin 2 is r2/c2
    a diode             D1.A D1.K A is pin 1, K (the band) pin 2, as the viewer draws it
    a polarised cap     C1.+ C1.- + is pin 1, - pin 2
    a transistor        Q1.E Q1.B Q1.C
    a panel wire        J1.A      jpsWires[].ref and pad
    the board's rail    rail:+12V rail:-12V rail:GND

Reads no board profile: what the holes do is the same on every n8synth board. Written from
boy_blocks.py's check against Rev A's KiCad netlist, for a layout with no KiCad behind it.

Exit status 1 if anything is wrong.
"""
import argparse
import collections
import json
import sys

RAILS = ('+12V', '-12V', 'GND')


def node_of(r, c):
    """The electrical node of a hole, or None if there's no such column. See docs/n8synth_platform.md."""
    c = str(c)
    if len(c) == 1 and c in 'abcde':
        return f'{r}L'
    if len(c) == 1 and c in 'fghij':
        return f'{r}R'
    if c in ('ctrlLo', 'ctrlLi', 'ctrlL'):
        return f'ctrlL{r}'
    if c in ('ctrlRo', 'ctrlRi', 'ctrlR'):
        return f'ctrlR{r}'
    if c == 'pwrL':
        return 'GND' if r % 2 else '+12V'
    if c == 'pwrR':
        return 'GND' if r % 2 else '-12V'
    return None


def where(node):
    if node in RAILS:
        return f'the {node} rail'
    if node.startswith('ctrl'):
        return f"{'left' if node[4] == 'L' else 'right'} edge position {node[5:]}"
    return f"row {node[:-1]} {'left' if node[-1] == 'L' else 'right'}"


class Nodes:
    def __init__(self):
        self.parent = {}

    def find(self, k):
        self.parent.setdefault(k, k)
        while self.parent[k] != k:
            self.parent[k] = self.parent[self.parent[k]]
            k = self.parent[k]
        return k

    def join(self, a, b):
        self.parent[self.find(a)] = self.find(b)


def placed_pins(layout):
    """{(part, pin): (row, col)}, and which of them are chip pins, which may be left unconnected."""
    pins, chip_pins = {}, set()
    for ic in layout.get('ics', []):
        for p in ic.get('pins', []):
            pins[(ic['id'], str(p['n']))] = (p['r'], p['c'])
            chip_pins.add((ic['id'], str(p['n'])))
    for t in layout.get('twoPins', []):
        pins[(t['id'], '1')] = (t['r1'], t['c1'])
        pins[(t['id'], '2')] = (t['r2'], t['c2'])
    for q in layout.get('transistors', []):
        for leg in 'EBC':
            pins[(q['id'], leg)] = (q[leg.lower() + 'R'], q[leg.lower() + 'C'])
    for j in layout.get('jpsWires', []):
        if j.get('ref') and j.get('pad') is not None:
            pins[(j['ref'], str(j['pad']))] = (j['row'], j['col'])
    return pins, chip_pins


def read_netlist(path):
    """{net: [members]}, or raises ValueError with the line that's wrong."""
    nets = {}
    with open(path) as f:
        for number, line in enumerate(f, 1):
            line = line.split('#', 1)[0].strip()
            if not line:
                continue
            if ':' not in line:
                raise ValueError(f'{path} line {number}: expected "NET: part.pin part.pin"')
            name, rest = line.split(':', 1)
            name = name.strip()
            if name in nets:
                raise ValueError(f'{path} line {number}: net {name} is listed twice')
            nets[name] = rest.split()
    return nets


def check(layout, nets):
    """Returns (problems, notes, {net: [holes]})."""
    problems, notes = [], []
    pins, chip_pins = placed_pins(layout)
    types = {t['id']: t.get('type') for t in layout.get('twoPins', [])}
    alias = {'D': {'A': '1', 'K': '2'}, 'C': {'+': '1', '-': '2'}}

    nodes = Nodes()
    for grp in ('jumpers', 'powerWires'):
        for w in layout.get(grp, []):
            a, b = node_of(w['r1'], w['c1']), node_of(w['r2'], w['c2'])
            if a is None or b is None:
                problems.append(f"{w.get('id', w.get('label', 'a wire'))}: no such hole "
                                f"({w['c1']}{w['r1']} to {w['c2']}{w['r2']})")
                continue
            nodes.join(a, b)
    for i, a in enumerate(RAILS):
        for b in RAILS[i + 1:]:
            if nodes.find(a) == nodes.find(b):
                problems.append(f'RAIL SHORT: wires join the {a} and {b} rails')

    # Where each listed member lands
    on_node = collections.defaultdict(list)     # node: [(net, who)]
    of_net = collections.defaultdict(set)       # net: {node}
    holes = collections.defaultdict(list)
    listed = set()
    for net, members in nets.items():
        for m in members:
            if m.startswith('rail:'):
                rail = m[5:]
                if rail not in RAILS:
                    problems.append(f'{net}: {m} is no rail; they are rail:+12V, rail:-12V and rail:GND')
                    continue
                on_node[nodes.find(rail)].append((net, m))
                of_net[net].add(nodes.find(rail))
                continue
            if '.' not in m:
                problems.append(f'{net}: {m} should be part.pin')
                continue
            ref, pin = m.split('.', 1)
            pin = alias.get(types.get(ref), {}).get(pin, pin)
            key = (ref, pin)
            if key in listed:
                problems.append(f'{m} is listed twice in the netlist')
            listed.add(key)
            if key not in pins:
                problems.append(f'MISSING {m} ({net}): not placed in the layout')
                continue
            r, c = pins[key]
            n = node_of(r, c)
            if n is None:
                problems.append(f'{m}: no such hole {c}{r}')
                continue
            n = nodes.find(n)
            on_node[n].append((net, m))
            of_net[net].add(n)
            holes[net].append(f'{c}{r}')

    # Placed, but not in the netlist
    idle = []
    for key, (r, c) in sorted(pins.items()):
        if key in listed:
            continue
        n = node_of(r, c)
        who = f'{key[0]}.{key[1]}'
        if key not in chip_pins:
            problems.append(f'EXTRA {who} at {c}{r}: placed in the layout, not in the netlist')
        elif n is not None and on_node.get(nodes.find(n)):
            names = sorted({e[0] for e in on_node[nodes.find(n)]})
            problems.append(f"SHORT {who} at {c}{r}: not in the netlist, but on {where(n)} with {', '.join(names)}")
        else:
            idle.append(who)
    if idle:
        notes.append(f"chip pins connected to nothing, and not in the netlist: {', '.join(idle)}")

    # Two nets on one node, and one net on two nodes
    for n, entries in sorted(on_node.items()):
        named = {net for net, _ in entries if net != 'NC'}
        if len(named) > 1 or ('NC' in {net for net, _ in entries} and len(entries) > 1):
            problems.append('SHORT on ' + where(n) + ': ' + ', '.join(f'{who} ({net})' for net, who in entries))
    for net, ns in sorted(of_net.items()):
        if net == 'NC' or len(ns) < 2:
            continue
        parts = collections.defaultdict(list)
        for node_name, entries in on_node.items():
            for owner, who in entries:
                if owner == net:
                    parts[node_name].append(who)
        problems.append(f'OPEN {net}: ' + '; '.join(f"{', '.join(v)} on {where(k)}" for k, v in sorted(parts.items())))

    # A pin on a rail its net doesn't mention
    for rail in RAILS:
        n = nodes.find(rail)
        for net in {e[0] for e in on_node.get(n, [])}:
            if net != 'NC' and f'rail:{rail}' not in nets.get(net, []) and len(of_net[net]) == 1:
                if len({e[0] for e in on_node[n]} - {'NC'}) == 1:
                    problems.append(f'{net} lands on the {rail} rail, but its line doesn\'t say rail:{rail}')
    for net, members in nets.items():
        if net != 'NC' and len(members) == 1:
            notes.append(f'{net} has only one member, {members[0]}')
    return problems, notes, holes


def main():
    ap = argparse.ArgumentParser(description='Check a breadboard layout against a netlist.')
    ap.add_argument('layout')
    ap.add_argument('netlist')
    ap.add_argument('--show', action='store_true', help="list each net's holes")
    args = ap.parse_args()
    with open(args.layout) as f:
        layout = json.load(f)
    try:
        nets = read_netlist(args.netlist)
    except ValueError as e:
        print(e)
        sys.exit(1)
    problems, notes, holes = check(layout, nets)
    pins = sum(1 for members in nets.values() for m in members if not m.startswith('rail:'))
    print(f'Checking {args.layout} against {args.netlist}')
    print(f'  {len(nets)} nets, {pins} pins')
    for n in notes:
        print(f'  note: {n}')
    if args.show:
        for net in nets:
            print(f"  {net}: {' '.join(holes.get(net, []))}")
    if problems:
        print(f'\n✗ {len(problems)} problem(s):')
        for p in problems:
            print(f'  {p}')
        sys.exit(1)
    print('\n✓ Every pin is on its net: no shorts, no opens, nothing missing or extra.')


if __name__ == '__main__':
    main()

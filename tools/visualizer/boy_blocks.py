#!/usr/bin/env python3
"""
boy_blocks.py - channel 1 of each analogue-board block, laid out on the n8synth breadboard.

The analogue board went from netlist straight to PCB, so nobody built these: they show how each
block's nets would land on the breadboard the board grew out of. For the Boy video's netlist slides
(eight4awish-video, BoyStory), and they open in this visualiser like any other layout.

    python3 boy_blocks.py         write layouts/boy_<block>.json and check each against Rev A

Each layout is checked two ways:
  - validate_layout.py: hole collisions, net-distinctness, rail parity, the near rail, headers.
  - below: every pin's breadboard node against Rev A's KiCad netlist. Pins on one node must be one
    net, and pins of one net must be on one node. So a row that joins the wrong pins fails, and so
    does a wire left out.

Only what the slide's netlist names is drawn: chips show the pins in use, and supplies other than
the rails arrive on a labelled row, from the power block. Parts that exist only as SMD packages sit
on a breakout, drawn at their real pin count.

Each step (`boySteps`) is one line of the slide's netlist, with the holes, parts and wires of its
node, so the video can light them in turn.
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NET = os.path.join(HERE, '../../hardware/analogue_board/teensy_core_midi/output/'
                         'analogue_board_teensy_core_midi.net')
RAILS = ('pwrL', 'pwrR')
SUPPLIES = {'+3V3D', '+3V3A', '+5VD', '+5VA', 'GND', 'CODEC_VCC'}


class Block:
    def __init__(self, id_, title, note='', rail_nets=None):
        self.id, self.title, self.note = id_, title, note
        self.rail_nets = rail_nets or {}
        self.twoPins, self.ics, self.jumpers, self.powerWires = [], [], [], []
        self.jpsWires, self.netLabels, self.steps = [], [], []

    def two(self, id_, type_, value, pad1, pad2):
        self.twoPins.append({'id': id_, 'type': type_, 'value': value, 'r1': pad1[0], 'c1': pad1[1],
                             'r2': pad2[0], 'c2': pad2[1], 'stage': 1})

    def dip(self, id_, value, n, top, nets):
        half = n // 2
        pins = []
        for p in range(1, n + 1):
            r, c = (top + p - 1, 'e') if p <= half else (top + n - p, 'f')
            pin = {'n': p, 'r': r, 'c': c}
            if p in nets:
                pin['net'] = nets[p]
            pins.append(pin)
        self.ics.append({'id': id_, 'value': value, 'label': value, 'stage': 1, 'pins': pins})

    def sip(self, id_, value, top, col, n, nets, side='right'):
        pins = []
        for p in range(1, n + 1):
            pin = {'n': p, 'r': top + p - 1, 'c': col}
            if p in nets:
                pin['net'] = nets[p]
            pins.append(pin)
        self.ics.append({'id': id_, 'value': value, 'label': value, 'stage': 1, 'labelSide': side, 'pins': pins})

    def jw(self, a, b, label=''):
        self.jumpers.append({'id': f'W{len(self.jumpers) + 1}', 'r1': a[0], 'c1': a[1], 'r2': b[0], 'c2': b[1],
                             'label': label, 'stage': 1})

    def pw(self, a, rail, label):
        self.powerWires.append({'id': f'P{len(self.powerWires) + 1}', 'r1': a[0], 'c1': a[1], 'r2': rail[0],
                                'c2': rail[1], 'label': label, 'stage': 1})

    def jack(self, ref, pad, label, edge, pos, to):
        """A panel jack: the deck's wire in the outer hole, a jumper from the inner one to the circuit."""
        self.jpsWires.append({'id': f'{ref}.{pad}', 'ref': ref, 'pad': str(pad), 'label': label, 'lbl': label,
                              'row': pos, 'col': f'ctrl{edge}o', 'stage': 1})
        self.jw((pos, f'ctrl{edge}i'), to, label)

    def label(self, r, side, name):
        self.netLabels.append({'r': r, 'side': side, 'name': name, 'stage': 1})

    def step(self, net, line):
        self.steps.append({'net': net, 'line': line})


def row(name, members):
    return f'{name:<13}{members}'


# ---------------------------------------------------------------- the blocks

def power():
    b = Block('power', 'Power', 'The rails stand in for the board\'s own power header. One capacitor of each '
              'parallel group drawn.', {'+12V': '+12V_IN', '-12V': '-12V_IN'})
    b.two('D201', 'D', 'SS34', (2, 'a'), (2, 'pwrL'))        # K on the row, A on the +12 V rail
    b.two('FB201', 'L', 'ferrite', (2, 'b'), (4, 'b'))
    b.label(4, 'L', '+12V')
    b.two('FB203', 'L', 'ferrite', (4, 'c'), (10, 'c'))
    b.dip('U201', 'TPS54308', 6, 8, {2: 'SW', 3: 'BUCK_VIN', 4: 'FB', 5: 'BUCK_EN'})
    b.two('C205', 'C', '10u', (10, 'b'), (11, 'pwrL'))
    b.two('R201', 'R', '510k', (10, 'd'), (11, 'g'))      # under the chip, not through it
    b.jw((11, 'h'), (9, 'h'), 'BUCK_EN')
    b.two('R202', 'R', '75k', (9, 'i'), (9, 'pwrR'))
    b.two('L201', 'L', 'inductor', (9, 'a'), (14, 'a'))
    b.two('C210', 'C', 'output', (14, 'c'), (15, 'pwrL'))
    b.two('R203', 'R', 'feedback', (14, 'd'), (10, 'g'))
    b.two('R206', 'R', '0R', (14, 'e'), (18, 'e'))
    b.label(18, 'L', '+5VD')
    b.sip('U202', 'L78M05', 20, 'c', 3, {1: '+12V', 3: '5VA_REG'}, 'left')
    b.jw((20, 'a'), (4, 'a'), '+12V')
    b.two('C216', 'C', '10u', (22, 'a'), (23, 'pwrL'))
    b.two('R207', 'R', '0R', (22, 'd'), (25, 'd'))
    b.label(25, 'L', '+5VA')
    b.sip('U203', 'XC6206', 27, 'c', 3, {2: '3V3A_REG', 3: '+5VA'}, 'left')
    b.jw((29, 'a'), (25, 'a'), '+5VA')
    b.two('C219', 'C', '1u', (28, 'a'), (31, 'pwrL'))
    b.two('R208', 'R', '0R', (28, 'd'), (31, 'd'))
    b.label(31, 'L', '+3V3A')
    b.sip('U204', 'XC6206', 27, 'g', 3, {2: '3V3D_REG', 3: '+5VD'})
    b.jw((18, 'a'), (29, 'h'), '+5VD')
    b.two('C221', 'C', '1u', (28, 'h'), (29, 'pwrR'))
    b.two('R209', 'R', '0R', (28, 'i'), (31, 'i'))
    b.label(31, 'R', '+3V3D')
    b.step('+12V_IN', row('+12V_IN', 'D201 anode, on the rail'))
    b.step('+12V_P', row('+12V_P', 'D201 cathode, FB201'))
    b.step('BUCK_VIN', row('BUCK_VIN', 'FB203, C205, R201, U201 VIN'))
    b.step('BUCK_EN', row('BUCK_EN', 'R201, R202, U201 EN'))
    b.step('5V_BUCK', row('5V_BUCK', 'L201, C210, R203, R206 → +5VD'))
    b.step('5VA_REG', row('5VA_REG', 'U202 out, C216, R207 → +5VA'))
    b.step('3V3A_REG', row('3V3A_REG', 'U203 out, C219, R208 → +3V3A'))
    b.step('3V3D_REG', row('3V3D_REG', 'U204 out, C221, R209 → +3V3D'))
    return b


def audio_in():
    b = Block('audio_in', 'Audio in, channel 1', 'Half a TL074H; the PCM3060 on a breakout.')
    b.jack('J310', 1, 'IN 1', 'L', 2, (2, 'a'))
    b.two('R309', 'R', '1M', (2, 'b'), (1, 'pwrL'))
    b.two('C308', 'C', '1u', (2, 'c'), (3, 'c'))
    b.two('R308', 'R', '100k', (3, 'a'), (5, 'a'))
    b.dip('U302', 'TL074H', 14, 4, {1: 'out', 2: 'minus', 3: 'VCOM'})
    b.label(6, 'L', 'VCOM')
    b.two('R307', 'R', '15k', (5, 'b'), (4, 'b'))
    b.two('C307', 'C', '100p', (5, 'c'), (4, 'c'))
    b.two('R310', 'R', '1k', (4, 'd'), (13, 'h'))
    b.sip('D301', 'BAT54S', 11, 'g', 3, {3: 'VINL'})
    b.jw((13, 'i'), (17, 'i'), 'VINL')
    b.dip('U301', 'PCM3060', 28, 14, {25: 'VINL'})
    b.step('AIN1', row('AIN1', 'J310 (jack), C308, R309'))
    b.step('Net-(C308-Pad2)', row('C308-R308', 'C308, R308'))
    b.step('Net-(U302A--)', row('U302A −', 'R308, R307, C307, U302.2'))
    b.step('Net-(C307-Pad2)', row('U302A out', 'R307, C307, R310, U302.1'))
    b.step('VINL', row('VINL', 'R310, D301, U301.25 VINL'))
    return b


def audio_out():
    b = Block('audio_out', 'Audio out, channel 1', 'Two poles, between the codec and the jack. The PCM3060 on a breakout.')
    b.dip('U301', 'PCM3060', 28, 1, {19: 'VOUTL-', 20: 'VOUTL+'})
    b.two('R316', 'R', '12k', (9, 'h'), (16, 'h'))
    b.two('R315', 'R', '12k', (10, 'g'), (17, 'g'))
    b.two('C315', 'C', '1n', (17, 'i'), (16, 'i'))
    b.two('R320', 'R', '30k', (16, 'j'), (15, 'pwrR'))
    b.two('R319', 'R', '30k', (17, 'j'), (26, 'j'))
    b.two('R318', 'R', '1k', (16, 'g'), (24, 'g'))
    b.two('R317', 'R', '1k', (17, 'h'), (25, 'h'))
    b.dip('U302', 'TL074H', 14, 20, {8: 'out', 9: 'minus', 10: 'plus'})
    b.two('C314', 'C', '100p', (24, 'i'), (23, 'pwrR'))
    b.two('C313', 'C', '100p', (25, 'i'), (26, 'i'))
    b.two('R321', 'R', '1k', (26, 'g'), (30, 'g'))
    b.jack('J311', 1, 'OUT 1', 'R', 33, (30, 'j'))
    b.step('VOUTL_N', row('VOUTL_N', 'U301.19, R315'))
    b.step('VOUTL_P', row('VOUTL_P', 'U301.20, R316'))
    b.step('Net-(C315-Pad1)', row('node −', 'R315, R317, R319, C315'))
    b.step('Net-(C315-Pad2)', row('node +', 'R316, R318, R320, C315'))
    b.step('Net-(U302C--)', row('U302C −', 'R317, C313, U302.9'))
    b.step('Net-(U302C-+)', row('U302C +', 'R318, C314, U302.10'))
    b.step('Net-(C313-Pad2)', row('U302C out', 'R319, C313, R321, U302.8'))
    b.step('AOUT1', row('AOUT1', 'R321, J311 (jack)'))
    return b


def cv_in():
    b = Block('cv_in', 'CV in, channel 1', 'The ADS8688 on a breakout: 38 pins, for 8 channels.')
    b.dip('U401', 'ADS8688', 38, 6, {16: 'ADC_IN1'})
    b.two('R405', 'R', '100k', (21, 'a'), (21, 'pwrL'))
    b.two('C409', 'C', '1n', (21, 'b'), (23, 'pwrL'))
    b.two('R404', 'R', '1k', (28, 'c'), (21, 'c'))
    b.jack('J410', 1, 'CV 1', 'L', 25, (28, 'a'))
    b.two('D401', 'D', 'TVS', (29, 'pwrL'), (28, 'b'))
    b.two('R406', 'R', '1k', (33, 'd'), (28, 'd'))
    b.label(33, 'L', 'to the jack switch')
    b.step('CV1', row('CV1', 'J410 (jack), D401 TVS, R404, R406 → switch'))
    b.step('ADC_IN1', row('ADC_IN1', 'R404, R405 100k, C409 1n, U401.16 AIN_0P'))
    return b


def cv_out():
    b = Block('cv_out', 'CV out, channel 1', 'One channel of the DAC8568, on a breakout; half of U504 makes the shared offset.')
    b.dip('U501', 'DAC8568', 16, 1, {4: 'DAC1'})
    b.dip('U502', 'TL074H', 14, 10, {1: 'CVDRV1', 2: 'minus', 3: 'DAC1'})
    b.jw((4, 'a'), (12, 'a'), 'DAC1')
    b.two('R505', 'R', '33k', (11, 'b'), (10, 'b'))
    b.two('C505', 'C', '100p', (11, 'c'), (10, 'c'))
    b.dip('U504', 'TL074H', 14, 18, {1: 'OFFSET_REF', 2: 'OFFSET_REF'})
    b.jw((18, 'a'), (19, 'a'), 'follower')
    b.two('R504', 'R', '10k', (18, 'd'), (11, 'd'))
    b.dip('U402', 'DG412', 16, 26, {3: 'CVDRV1'})
    b.jw((10, 'a'), (28, 'a'), 'CVDRV1')
    b.step('DAC1', row('DAC1', 'U501.4 VOUTA, U502.3 +'))
    b.step('Net-(U502A--)', row('U502A −', 'R504 10k, R505 33k, C505 100p, U502.2'))
    b.step('OFFSET_REF', row('OFFSET_REF', 'R504 (one per channel), U504.1, U504.2'))
    b.step('CVDRV1', row('CVDRV1', 'U502.1, R505, C505, U402.3 → switch'))
    return b


def cv_switch():
    b = Block('cv_switch', 'Jack switch, channel 1', 'The TCA9555 on a breakout.')
    b.dip('U402', 'DG412', 16, 2, {1: 'SW_EN1', 2: 'to jack', 3: 'CVDRV1'})
    b.dip('U701', 'TCA9555', 24, 12, {4: 'SW_EN1'})
    b.dip('U502', 'TL074H', 14, 25, {1: 'CVDRV1'})
    b.jw((2, 'a'), (15, 'a'), 'SW_EN1')
    b.two('R407', 'R', '4.7k', (2, 'b'), (3, 'pwrL'))
    b.two('R406', 'R', '1k', (3, 'c'), (10, 'c'))
    b.two('D401', 'D', 'TVS', (11, 'pwrL'), (10, 'b'))
    b.two('R404', 'R', '1k', (10, 'd'), (11, 'd'))
    b.label(11, 'L', 'to the ADC')
    b.jack('J410', 1, 'CV 1', 'L', 9, (10, 'a'))
    b.jw((4, 'a'), (25, 'a'), 'CVDRV1')
    b.step('CVDRV1', row('CVDRV1', 'U502.1 (DAC stage), U402.3'))
    b.step('SW_EN1', row('SW_EN1', 'U701.4 P00 (expander), R407 4.7k, U402.1'))
    b.step('Net-(R406-Pad1)', row('switch out', 'U402.2, R406'))
    b.step('CV1', row('CV1', 'R406 1k, J410 (jack), D401 TVS, R404 → ADC'))
    return b


def gate_in():
    b = Block('gate_in', 'Gate in, channel 1', 'Half an LM393. Its output goes to the module\'s pin.')
    b.dip('U801', 'LM393', 8, 12, {1: 'GATE_IN1', 3: 'plus'})
    b.jack('J810', 1, 'GATE 1', 'L', 20, (20, 'b'))
    b.two('R801', 'R', '10k', (20, 'a'), (14, 'a'))
    b.two('R802', 'R', '100k', (14, 'b'), (15, 'pwrL'))
    b.two('R803', 'R', '100k', (14, 'c'), (12, 'c'))
    b.two('R804', 'R', '10k', (9, 'b'), (12, 'b'))
    b.label(9, 'L', '+3V3D')
    b.label(12, 'L', 'GATE_IN1')
    b.sip('D801', 'BAT54S', 17, 'c', 3, {3: 'plus'}, 'left')
    b.jw((19, 'd'), (14, 'd'), 'clamp')
    b.step('GIN1', row('GIN1', 'J810 (jack), R801 10k'))
    b.step('Net-(D801-COM)', row('U801A +', 'R801, D801 BAT54S, R802 100k, R803 100k, U801.3'))
    b.step('GATE_IN1', row('GATE_IN1', 'U801.1, R803, R804 10k → +3V3D, Teensy pin 2'))
    return b


def gate_out():
    b = Block('gate_out', 'Gate out, channel 1', 'One output of the 74HCT595.')
    b.dip('U602', '74HCT595', 16, 10, {15: 'GQ1'})
    b.two('R617', 'R', '1k', (11, 'i'), (22, 'i'))
    b.sip('D601', 'BAV99', 20, 'g', 3, {3: 'GOUT1'})
    b.jack('J610', 3, 'GATE OUT 1', 'R', 22, (22, 'j'))
    b.step('GQ1', row('GQ1', 'U602.15 QA, R617 1k'))
    b.step('GOUT1', row('GOUT1', 'R617, D601 BAV99, J610 (jack)'))
    return b


def pots():
    b = Block('pots', 'Pots, channel 1', 'One channel of the MCP3208.')
    b.dip('U601', 'MCP3208', 16, 12, {1: 'POT_IN1'})
    b.two('R604', 'R', '1M', (12, 'c'), (11, 'pwrL'))
    b.two('C605', 'C', '100n', (12, 'b'), (13, 'pwrL'))
    b.two('R603', 'R', '1k', (6, 'a'), (12, 'a'))
    b.jack('J610', 1, 'POT 1', 'L', 6, (6, 'b'))
    b.step('POT1', row('POT1', 'J610 (wiper), R603 1k'))
    b.step('POT_IN1', row('POT_IN1', 'R603, C605 100n, R604 1M, U601.1 CH0'))
    return b


def controls():
    b = Block('controls', 'A button, channel 1', 'The TCA9555 on a breakout: 16 lines over two wires.')
    b.dip('U701', 'TCA9555', 24, 8, {13: 'BTN1'})
    b.two('R702', 'R', '1k', (25, 'g'), (19, 'g'))
    b.two('R703', 'R', '10k', (22, 'h'), (19, 'h'))
    b.label(22, 'R', '+3V3D')
    b.two('C702', 'C', '100n', (19, 'i'), (21, 'pwrR'))
    b.jack('J712', 1, 'BUTTON 1', 'R', 25, (25, 'j'))
    b.step('SW1', row('SW1', 'J712 (button), R702 1k'))
    b.step('BTN1', row('BTN1', 'R702, R703 10k → +3V3D, C702 100n, U701.13 P10'))
    return b


def midi():
    b = Block('midi', 'TRS MIDI, in and out', 'In at the top, out below. The buffer on a breakout.')
    b.dip('U1002', 'H11L1', 6, 3, {1: 'LED cathode', 2: 'MI_T', 4: 'out'})
    b.two('D1002', 'D', 'protect', (3, 'b'), (4, 'b'))
    b.jack('J1001', 3, 'MIDI IN T', 'L', 4, (4, 'a'))
    b.two('R1007', 'R', '220R', (8, 'c'), (3, 'c'))
    b.jack('J1001', 4, 'MIDI IN R', 'L', 8, (8, 'a'))
    b.two('C1003', 'C', '100n', (10, 'c'), (11, 'pwrL'))
    b.jack('J1001', 5, 'MIDI IN S', 'L', 9, (10, 'a'))
    b.two('R1008', 'R', '1k', (8, 'g'), (5, 'g'))
    b.label(8, 'R', '+3V3D')
    b.two('R1009', 'R', '1k', (5, 'h'), (9, 'h'))
    b.label(9, 'R', 'MIDI_RX')
    b.sip('U1001', '74AHCT1G125', 20, 'g', 5, {2: 'in', 4: 'out', 5: '+5VD'}, 'side')
    b.two('R1002', 'R', '10k', (18, 'i'), (21, 'i'))
    b.label(18, 'R', '+3V3D')
    b.two('R1001', 'R', '1k', (26, 'h'), (21, 'h'))
    b.label(26, 'R', 'MIDI_TX')
    b.two('R1003', 'R', '100R', (23, 'h'), (28, 'h'))
    b.two('R1004', 'R', '100R', (28, 'i'), (30, 'i'))
    b.jack('J1001', 1, 'MIDI OUT T', 'R', 33, (30, 'j'))
    b.two('R1005', 'R', '100R', (24, 'h'), (32, 'h'))
    b.label(24, 'R', '+5VD')
    b.two('R1006', 'R', '100R', (32, 'i'), (34, 'i'))
    b.jack('J1001', 2, 'MIDI OUT R', 'R', 34, (34, 'j'))
    b.step('MI_T', row('MI_T', 'J1001 tip, D1002, U1002.2'))
    b.step('MI_R', row('MI_R', 'J1001 ring, R1007 220R'))
    b.step('Net-(D1002-K)', row('opto in', 'R1007, D1002, U1002.1'))
    b.step('MI_S', row('MI_S', 'J1001 sleeve, C1003 100n'))
    b.step('Net-(R1008-Pad2)', row('opto out', 'U1002.4, R1008 → +3V3D, R1009'))
    b.step('MIDI_RX', row('MIDI_RX', 'R1009, J101 → the module'))
    b.step('MIDI_TX', row('MIDI_TX', 'J101 ← the module, R1001'))
    b.step('Net-(R1001-Pad2)', row('buffer in', 'R1001, R1002, U1001.2'))
    b.step('Net-(D1001-COM)', row('buffer out', 'U1001.4, R1003'))
    b.step('MO_T', row('MO_T', 'R1004, J1001 tip'))
    b.step('MO_R', row('MO_R', 'R1006, J1001 ring'))
    return b


BLOCKS = [power, audio_in, audio_out, cv_in, cv_out, cv_switch, gate_in, gate_out, pots, controls, midi]


# ---------------------------------------------------------------- the check

def kicad_nets():
    text = open(NET).read()
    pin_net, members = {}, {}
    for blk in text.split('(net ')[1:]:
        m = re.search(r'\(name "([^"]*)"', blk)
        if not m:
            continue
        name = m.group(1).split('/')[-1]
        for ref, pad in re.findall(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)', blk):
            pin_net[(ref, pad)] = name
            members.setdefault(name, set()).add(ref)
    return pin_net, members


class Nodes:
    """The breadboard's electrical nodes (docs/n8synth_platform.md), joined by wires."""

    def __init__(self, rail_nets):
        self.parent = {}
        self.rail_nets = rail_nets

    def key(self, r, c):
        c = str(c)
        if c in 'abcde':
            if r > 36:
                raise ValueError(f'no main-area row {r}')
            return f'{r}L'
        if c in 'fghij':
            if r > 36:
                raise ValueError(f'no main-area row {r}')
            return f'{r}R'
        if c.startswith('ctrlL'):
            return f'ctrl{r}L'
        if c.startswith('ctrlR'):
            return f'ctrl{r}R'
        if c in RAILS:
            if r % 2:
                return 'GND'
            name = '+12V' if c == 'pwrL' else '-12V'
            return self.rail_nets.get(name, name)
        raise ValueError(f'unknown column {c}')

    def find(self, k):
        self.parent.setdefault(k, k)
        while self.parent[k] != k:
            self.parent[k] = self.parent[self.parent[k]]
            k = self.parent[k]
        return k

    def join(self, a, b):
        self.parent[self.find(a)] = self.find(b)


def check_block(b, pin_net, members):
    errs = []
    nodes = Nodes(b.rail_nets)
    for w in b.jumpers + b.powerWires:
        nodes.join(nodes.key(w['r1'], w['c1']), nodes.key(w['r2'], w['c2']))
    labelled = {}
    for nl in b.netLabels:
        if nl['name'] in SUPPLIES:
            k = f"{nl['r']}{nl['side']}"
            if nl['name'] in labelled:
                nodes.join(k, labelled[nl['name']])
            labelled[nl['name']] = k
    # every pin the slide names: (ref, pad, row, col)
    pins = []
    for t in b.twoPins:
        pins += [(t['id'], '1', t['r1'], t['c1']), (t['id'], '2', t['r2'], t['c2'])]
    for ic in b.ics:
        pins += [(ic['id'], str(p['n']), p['r'], p['c']) for p in ic['pins'] if 'net' in p]
    for j in b.jpsWires:
        pins.append((j['ref'], j['pad'], j['row'], j['col']))

    on_node, of_net = {}, {}
    for ref, pad, r, c in pins:
        net = pin_net.get((ref, pad))
        if net is None:
            errs.append(f'{ref}.{pad}: not in the netlist')
            continue
        node = nodes.find(nodes.key(r, c))
        on_node.setdefault(node, set()).add((net, f'{ref}.{pad}'))
        of_net.setdefault(net, set()).add((node, f'{ref}.{pad}'))
    for node, entries in on_node.items():
        nets = {n for n, _ in entries}
        if len(nets) > 1:
            errs.append(f'SHORT on {node}: {sorted(entries)}')
    for net, entries in of_net.items():
        if net.startswith('unconnected'):
            continue
        ns = {n for n, _ in entries}
        if len(ns) > 1:
            errs.append(f'OPEN {net}: {sorted(entries)}')

    # labels name their node's net
    for nl in b.netLabels:
        k = nodes.find(f"{nl['r']}{nl['side']}")
        for net, who in on_node.get(k, ()):
            if nl['name'] in members and nl['name'] != net:
                errs.append(f"label {nl['name']} at {nl['r']}{nl['side']}, but {who} is on {net}")

    # each step: its net is in the layout, and the parts its line names are on that net
    out = []
    for s in b.steps:
        net = s['net']
        if net not in of_net:
            errs.append(f"step {net}: no pin of that net is drawn")
            continue
        node = next(iter(of_net[net]))[0]
        for tok in re.findall(r'\b(?:[RCDLUJ]|FB)\d+\b', s['line'].split(None, 1)[1]):
            if tok not in members.get(net, ()):
                errs.append(f"step {net}: its line names {tok}, which isn't on that net")
        drawn = [(r, c) for ref, pad, r, c in pins if nodes.find(nodes.key(r, c)) == node]
        wires = [w['id'] for w in b.jumpers + b.powerWires if nodes.find(nodes.key(w['r1'], w['c1'])) == node]
        keys = {k for k in list(nodes.parent) if nodes.find(k) == node} | {nodes.key(r, c) for r, c in drawn}
        rows = sorted(k for k in keys if re.fullmatch(r'\d+[LR]', k))
        ctrl = sorted(k[4:] for k in keys if k.startswith('ctrl'))
        parts = sorted({ref for ref, pad, r, c in pins if nodes.find(nodes.key(r, c)) == node})
        out.append({'net': net, 'line': s['line'], 'rows': rows, 'ctrl': ctrl, 'parts': parts, 'wires': wires,
                    'holes': [[r, c] for r, c in drawn]})
    return errs, out


def main():
    pin_net, members = kicad_nets()
    failed = False
    names = []
    for make in BLOCKS:
        b = make()
        errs, steps = check_block(b, pin_net, members)
        path = os.path.join(HERE, 'layouts', f'boy_{b.id}.json')
        layout = {
            'title': f'BOY: {b.title}', 'source': 'tools/visualizer/boy_blocks.py; Rev A netlist',
            'board': 'n8synth (single board, rows 1-36)', 'boardId': 'n8synth-10hp', 'revision': 'drawn, not built',
            'notes': b.note,
            'stages': [{'id': 1, 'name': b.title, 'desc': b.note, 'test': 'Not built: checked against Rev A\'s netlist.', 'color': '#c8202f'}],
            'ics': b.ics, 'twoPins': b.twoPins, 'jumpers': b.jumpers, 'powerWires': b.powerWires,
            'jpsWires': b.jpsWires, 'netLabels': b.netLabels, 'boySteps': steps,
        }
        with open(path, 'w') as f:
            json.dump(layout, f, indent=1)
        v = subprocess.run([sys.executable, os.path.join(HERE, 'validate_layout.py'), path], capture_output=True, text=True)
        subprocess.run([sys.executable, os.path.join(HERE, 'sync_layout.py'), path, '--name', f'Boy: {b.title}'],
                       capture_output=True, text=True, check=True)
        ok = not errs and v.returncode == 0
        failed = failed or not ok
        names.append(b.id)
        print(f"{'ok  ' if ok else 'FAIL'} {b.id:<10} {len(b.ics)} chips, {len(b.twoPins)} parts, {len(b.jumpers)} wires, {len(steps)} steps")
        for e in errs:
            print('     net:', e)
        if v.returncode:
            print('     validate:', '\n     '.join(l for l in v.stdout.splitlines() if l.strip())[-900:])
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()

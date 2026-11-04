#!/usr/bin/env python3
"""
bundle_skill.py - copy the checks and the viewer into the n8synth-layout Claude skill.

A skill is a folder someone can copy on its own, so it carries its own copy of the tool. This repo
holds the originals. After changing one, run this and commit the skill too:

    python3 bundle_skill.py [path to the eight4awish repo]

The repo defaults to a checkout beside this one. The viewer loses its built-in layouts, as they
stay here: a layout's JSON gets dropped onto it instead.
"""
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '..', '..', '..', 'eight4awish')
OUT = os.path.join(REPO, 'skills', 'n8synth-layout', 'tool')

os.makedirs(os.path.join(OUT, 'boards'), exist_ok=True)
for name in ('validate_layout.py', 'check_netlist.py', 'LICENSE'):
    shutil.copy(os.path.join(HERE, name), os.path.join(OUT, name))
for name in sorted(os.listdir(os.path.join(HERE, 'boards'))):
    if name.endswith('.json'):
        shutil.copy(os.path.join(HERE, 'boards', name), os.path.join(OUT, 'boards', name))

with open(os.path.join(HERE, 'index.html'), encoding='utf-8') as f:
    html = f.read()
html, removed = re.subn(r'<script src="layouts/[^"]+"></script>\n', '', html)
with open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8') as f:
    f.write(html)
print(f'{OUT}: checks, boards and the viewer, {removed} built-in layouts left out')

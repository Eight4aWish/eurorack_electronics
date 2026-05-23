#!/usr/bin/env python3
"""
Sync a layout JSON file → its matching JS wrapper.

The visualizer reads `layouts/*.js` (which call `registerLayout(name, data)`).
After editing a `layouts/*.json`, run this to regenerate the corresponding `.js`.

Usage:
    python3 sync_layout.py layouts/lpg.json
    python3 sync_layout.py layouts/lpg.json --name "Dual LPG"
"""
import argparse
import json
import os
import sys


def sync(json_path, name=None):
    js_path = os.path.splitext(json_path)[0] + '.js'
    with open(json_path) as f:
        layout = json.load(f)

    # If --name not given, try to read the existing .js's registerLayout("…", …) string
    if name is None and os.path.exists(js_path):
        with open(js_path) as f:
            first = f.readline()
        if first.startswith('registerLayout("'):
            name = first.split('"', 2)[1]

    if name is None:
        name = layout.get('title', 'Untitled')

    with open(js_path, 'w') as f:
        f.write(f'registerLayout({json.dumps(name)}, ')
        json.dump(layout, f, indent=2)
        f.write(');\n')

    rev = layout.get('revision', '?')
    print(f"✓ {js_path} ← {json_path}  (name={name!r}, rev={rev})")


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('json_path', help='Path to layouts/*.json')
    ap.add_argument('--name', help='Layout name (overrides inferred or .js-stored name)')
    args = ap.parse_args()
    sync(args.json_path, args.name)

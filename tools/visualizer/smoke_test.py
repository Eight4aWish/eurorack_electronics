#!/usr/bin/env python3
"""Smoke-test the visualiser: run its scripts against a stub DOM and confirm
every built-in layout registers. Catches load-time errors that silently empty
the layout picker."""
import re, subprocess, sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
s = open('index.html', encoding='utf-8').read()
inline = re.findall(r'<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>', s, re.S)
srcs = re.findall(r'<script[^>]*\bsrc="([^"]+)"', s)
STUB = '''
const mk = () => new Proxy({ style:{}, classList:{add(){},remove(){},toggle(){}},
  children:[], dataset:{}, checked:false, value:'', innerHTML:'', textContent:'',
  appendChild(){return mk()}, addEventListener(){}, setAttribute(){}, removeAttribute(){},
  getBoundingClientRect:()=>({left:0,top:0,width:100,height:100}), querySelectorAll:()=>[],
  insertAdjacentHTML(){}, remove(){}, focus(){}, options:[], add(){} },
  { get:(t,k)=> k in t ? t[k] : (typeof k==='string'&&k.startsWith('on')?null:mk()) });
global.document = { getElementById:()=>mk(), createElement:()=>mk(), createElementNS:()=>mk(),
  querySelectorAll:()=>[], querySelector:()=>mk(), addEventListener(){}, documentElement:mk(), body:mk() };
global.window = { matchMedia:()=>({matches:false, addEventListener(){}}), addEventListener(){}, devicePixelRatio:1 };
global.matchMedia = global.window.matchMedia; global.fetch=()=>Promise.resolve({}); global.alert=()=>{};
'''
parts = [STUB, inline[0]]
for f in srcs:
    parts.append(open(f, encoding='utf-8').read())
parts.append(inline[-1])
parts.append('''
const names = Object.keys(BUILTIN_LAYOUTS);
if (names.length === 0) { console.error("FAIL: no layouts registered"); process.exit(1); }
console.log("registered " + names.length + " layout(s): " + names.join(", "));
''')
open('/tmp/_smoke.js', 'w').write('\n'.join(parts))
r = subprocess.run(['node', '/tmp/_smoke.js'], capture_output=True, text=True)
print(r.stdout.strip() or r.stderr.strip()[:600])
sys.exit(r.returncode)

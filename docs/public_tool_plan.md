# Public Tool — Plan

Plan for turning the breadboard placement/visualisation scripts into something a third party
can use. Written 2026-08-28, after the platform-accuracy pass.

---

## What it is

A workflow and a verifier for building Eurorack modules on n8synth solderable breadboards:

> reference review → netlist → skeleton layout → **placement** → **verify** → build

The value on offer is **the verification loop, not auto-placement.** Placement stays a human
(or LLM-assisted) job; the tool's contribution is that it will not let you record a layout that
collides, that puts a component on the wrong net, or whose documentation has drifted from the
JSON. That framing needs to be explicit up front so nobody arrives expecting a autorouter.

**Audience:** someone with an n8synth kit who wants to build a documented module and be able to
hand the build guide to someone else.

---

## The two flagship examples

Deliberately chosen to be licence-clean *and* to cover the platform between them.

| | **Dual Pingable LPG** | **MOD2 / Melon hybrid** |
|---|---|---|
| Origin | **Our own design** — canonical Buchla 292 topology, multi-source verified and credited | **CC0** throughout (HAGIWO) |
| Deck | 10HP, **two** connector strips (`ctrlL` + `ctrlR`) | 6HP, **one** strip |
| Nature | Pure analog, dual channel, vactrols | Mixed-signal, MCU module, PWM audio |
| Shows off | Build phases, per-phase test checklists, generated schematics | Panel switches, dual indicator, one board / 25 firmware voices |
| Status | Placed, passing all checks at rev 0.19 | Netlist + panel locked; **placement not started** |

Between them they cover both deck widths, both strip configurations, analog and digital, and
two different licensing models. That is a genuinely representative pair.

⚠️ **The MKI x ES kick, snare and FM drum layouts must NOT ship.** Moritz Klein and Erica Synths
sell these as kits, and the 109-page manual carries **no licence statement at all** — so default
all-rights-reserved applies (verified 2026-08-28; the *Circuit Design Guide* is also a €15
product). They stay local. `index.html` currently hardcodes all three.

---

## What works today

- `validate_layout.py` — hole collisions, net distinctness, rail parity
- `cross_check_nets.py` — does every component land on the nets the netlist requires
- `gen_rowmap.py` — regenerates the placement doc's row maps from the JSON, so docs cannot drift
- `check.sh` — runs all three, and refuses to regenerate docs if the first two fail
- `gen_board_profiles.py` / `boards/` — board profiles, now corrected against
  [`n8synth_platform.md`](n8synth_platform.md)
- `netlist_to_layout.py` — netlist markdown → skeleton layout JSON
- `tools/schematic/` — build-phase schematic PNGs (LPG)
- Browser visualiser with build-phase stepping

The LPG passes end to end today: **57 components on expected nets, zero collisions.**

---

## Blockers

**B1 — The answer key is hand-transcribed per module.** ⛔ *Hard blocker.*
`cross_check_nets.py` carries `EXPECTED_NETS` as a literal dict in the source, headed *"from
docs/lpg_netlist.md rev 0.4"* — while the layout is at rev 0.19, so it may already be stale.
A third party's module has no answer key at all, which makes the most valuable check unusable
for anyone but us.
**Fix:** a structured circuit file (canonical JSON) as the single source of truth, from which
`EXPECTED_NETS` is *derived* and the markdown netlist becomes a generated view. This was already
the intended direction; third-party use makes it mandatory rather than nice-to-have.

**B2 — Modules are registered by editing `index.html`.** ⛔
Layouts load via hardcoded `<script src="layouts/*.js">` tags, and each `.js` is a wrapper
duplicating its `.json`. Adding a module means editing the app.
**Fix:** a `layouts/index.json` manifest plus `fetch`, keeping the `.js` wrappers only as a
`file://` fallback.

**B3 — MKI x ES layouts are baked into the app.** ⛔
Must be removed from the public build (see above).

**B4 — Board profiles are generated but unused.** ⚠️
`lpg.json` records its board as the free-text string `"n8synth (single board, rows 1-36)"`.
Nothing links a layout to a profile, so nothing enforces board geometry.
**Fix:** layouts reference a board id; validators load the profile.

**B5 — The layout schema predates the corrected platform model.** ⚠️
It uses `ctrlL`/`ctrlR` and `pwrL`/`pwrR`, which is roughly right, but does not distinguish
**main area / edge connector / power rail** as the three different extents they are, nor model
edge-connector doublets or board variants.
**Fix:** align the schema with `n8synth_platform.md` before others build on it.

**B6a — Colour and contrast.** ⚠️ *Addressed, with a design change.*
The original palette failed four of five accessibility checks. Fixing it properly forced a real
finding: **eight categorical hues cannot be made mutually distinguishable.** Measured, not
judged — an 8-hue set fails even in dark mode (worst pair ΔE 1.6 deutan), and in light mode a
yellow dark enough to reach 3:1 contrast turns brown and collides with both red and aqua. Seven
fails too.

So colour now encodes **three categories** — passive (R/C/D), active (IC/NPN/PNP), connection
(JW/JPS) — and the component's **shape and label** carry its exact identity, which is what a
builder reads anyway. Both palettes pass all five checks under the **strictest** model
(`--pairs all`), dark on `#242426` and light on `#f4f4f0`. Light is a selected palette, stepped
for its own surface, not a flip. Default follows `prefers-color-scheme`.

Still to do — a **legend** naming the three categories.

**B6 — No install story, no getting-started doc.** ⚠️
Works from a clone plus `python3 -m http.server`, but that is undocumented for a newcomer.

**B7 — Placement has no tool support.** ℹ️ *Partly addressed.*
`edit_layout.py` now covers the *correction* half: a text command language for moving endpoints,
setting components, mirroring left/right and shifting rows, refusing any edit that collides.
Initial placement is still manual. Be explicit that the offer is the verification loop plus
hand-editing, not auto-placement.

---

## Sequence

1. **Platform model correct** — ✅ done (`n8synth_platform.md`, profiles regenerated)
2. **Structured circuit file** (B1) — schema, retrofit the LPG, prove 57/57 nets still pass with
   the hardcoded table deleted. *This is the gate: until it is done there is no third-party tool.*
3. **Layout ↔ board profile link** (B4, B5)
4. **Manifest loading** (B2) and **drop the MKI layouts** (B3)
5. **Transfer the dual LPG** to the new tool, reconciled against the as-built board
6. **MOD2 placement** and verify
7. **Getting-started doc** (B6), honest scope statement (B7)
8. Publish

Steps 2–4 are the actual engineering. Steps 5–6 are content, and are what the video needs.

---

## Out of scope for v1

- Auto-placement / autorouting
- KiCad import (considered and rejected — hand-drawing schematics per module is too much work)
- Packaging as a pip/npm module; a clone-and-run repo is enough to gauge appetite
- Any module we do not have clean rights to publish

---

## Open

- **The dual LPG as-built differs from `lpg.json`** in component layout. Needs reconciling
  before the transfer — by photo, or by a hand list from the builder. Until then the layout
  documents an earlier revision than the board on the bench.

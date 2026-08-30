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

⚠️ **The third-party kit designs in this repo must NOT ship with the public tool.** They are
someone else's commercial product and are not ours to redistribute. `index.html` currently
hardcodes them, so this needs an explicit removal step rather than an omission.

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

## What the tool actually needs as input

Settled by working through the LPG rework. **Three inputs, and everything else derived** — not
a new circuit format, which was over-engineering on my part.

**1. The netlist** — components and the two nets each one connects. The existing netlist docs
already state exactly this (`| R4 | 10K | BUF_OUT_A | VC_A.LDR1.in |`), so `EXPECTED_NETS` is
pure hand-transcription of something already written down. The parser needs a spec so it reads
all of it, and two validity rules:

- **every component must have both terminals on a named net** — a one-ended component makes the
  netlist invalid, not ambiguous
- **nothing may be silently dropped** — the current parser lost all five MOD2 jacks, LED1 and
  every connection while reporting success

**2. The front panel layout** — which control position each jack, pot, switch and LED occupies.
This is a real input, not decoration: it *anchors placement spatially*. Measured on the finished
dual LPG, every IC sits at or just below the panel positions it serves —

    DA1 rows 1-4    panel row 1        DA2 rows 27-30   panel row 23
    DA3 rows 14-17  panel row 13       DA4 rows 33-36   panel row 28
    VC_B rows 22-25 panel row 21

perfectly monotonic, and nobody wrote that rule down. It emerged from placing by hand. It is
also what makes a placement search bounded rather than open: an IC whose parts reach the top of
the panel belongs near the top of the board.

**3. The board rules** — already written: `n8synth_platform.md` plus the generated board
profiles. Main area vs edge connector vs power rail, doublets and their outer/inner convention,
header positions, rail parity, which rows exist on which board variant.

### What is derived, not authored

- **Which net each row-half carries.** A row-half is one node. Seed from the rails (by parity)
  and the IC pins (which declare their nets), then propagate: if one end of a component sits on
  a known node, its other end must be its other net. The hand-maintained table of 46 assertions
  is a *consequence* of netlist plus placement, not an input to it.
- **The per-component answer key** — read from the netlist rather than transcribed.

### How placement actually happens

There is no clever algorithm and there does not need to be one. Placement is **LLM-assisted
trial and error, monitored by the checks**: spread the ICs out with room either side, anchor
each near the panel positions it serves, then let the validators find what is wrong against the
netlist and the board rules. That loop is what this session demonstrated at scale — a
fifty-component rework where every knock-on was caught by a check rather than by inspection.

The tool's offer is therefore honest and narrow: **it will not place your circuit, but it will
not let you keep a placement that is wrong.**

---

## Blockers

**Every module's answer key is typed by hand.** ⛔ *Hard blocker.*
`cross_check_nets.py` carries `EXPECTED_NETS` as a literal dict in the source, headed *"from
docs/lpg_netlist.md rev 0.4"* — while the layout is at rev 0.19, so it may already be stale.
A third party's module has no answer key at all, which makes the most valuable check unusable
for anyone but us.
**Fix:** a structured circuit file (canonical JSON) as the single source of truth, from which
`EXPECTED_NETS` is *derived* and the markdown netlist becomes a generated view. This was already
the intended direction; third-party use makes it mandatory rather than nice-to-have.

**The browser copy of a layout goes stale without warning.** ⚠️ *Mitigated.*
The browser loads `layouts/*.js`, generated from the canonical `.json` — but nothing regenerated
them, so edits to a layout could pass every check and never reach the screen. Found the hard way:
the LPG's wrapper sat at rev 0.19 while the JSON was at 0.21, so two fixes appeared not to work.
`check.sh` now regenerates the wrapper as step 3 of 4.

⚠️ The wrappers had also drifted the *other* way on some layouts — the `.js` newer than its
`.json`, so regenerating would have destroyed work. Those layouts have since been removed from
the repo, but the hazard is inherent to keeping two sources of truth: it is an argument for
dropping the browser wrappers entirely rather than syncing them.

**Adding a module means editing the app's own HTML.** ⛔
Layouts load via hardcoded `<script src="layouts/*.js">` tags, and each `.js` is a wrapper
duplicating its `.json`. Adding a module means editing the app.
**Fix:** a `layouts/index.json` manifest plus `fetch`, keeping the `.js` wrappers only as a
`file://` fallback.

**Third-party kit designs were in the repo.** ✅ *Done.*
Removed from the repo along with their transcribed netlists and the `index.html` script tags
that loaded them. Kept locally in the gitignored `docs/refs/`.

**Board profiles exist but almost nothing reads them.** ⚠️
`lpg.json` records its board as the free-text string `"n8synth (single board, rows 1-36)"`.
Nothing links a layout to a profile, so nothing enforces board geometry.
**Fix:** layouts reference a board id; validators load the profile.

**The layout format predates the corrected platform model.** ⚠️
It uses `ctrlL`/`ctrlR` and `pwrL`/`pwrR`, which is roughly right, but does not distinguish
**main area / edge connector / power rail** as the three different extents they are, nor model
edge-connector doublets or board variants.
**Fix:** align the schema with `n8synth_platform.md` before others build on it.

**Colour and contrast were unreadable.** ✅ *Done.*
The original palette failed four of five accessibility checks and several sidebar labels were
literally unreadable — `test-point` measured **1.08:1** in light mode, `stage name` **1.01:1**.

Fixed properly: **every** colour now resolves through a theme role (zero hardcoded hex left in
the drawing code or the CSS), which is what stopped this being fixable piecemeal. Two selected
palettes, each stepped and validated for its own surface — dark `#242426`, light `#f4f4f0`.
All 8 component hues clear **3:1** contrast in both modes, and **every text role clears WCAG AA
4.5:1** in both modes.

Per-type colour is retained by preference. The honest limit, documented in the code: eight hues
cannot be made mutually distinguishable, and in light mode NPN/PNP sit at ΔE 14.2 against a 15
floor. Relief is in place — designator and value labels on every part, distinct shapes, and a
legend that names all eight plus the rails and says which pair to read the label for. The legend
is generated from the live palette, so it can no longer drift out of date (it had been showing
the *old* eight colours after the palette changed).

**No install instructions and no getting-started guide.** ⚠️
Works from a clone plus `python3 -m http.server`, but that is undocumented for a newcomer.

**The tool checks placement but does not help you place.** ℹ️ *Partly addressed.*
`edit_layout.py` now covers the *correction* half: a text command language for moving endpoints,
setting components, mirroring left/right and shifting rows, refusing any edit that collides.
Initial placement is still manual. Be explicit that the offer is the verification loop plus
hand-editing, not auto-placement.

---

## Sequence

1. **Platform model correct** — ✅ done (`n8synth_platform.md`, profiles regenerated)
2. **Structured circuit file** — the answer-key problem — schema, retrofit the LPG, prove 57/57 nets still pass with
   the hardcoded table deleted. *This is the gate: until it is done there is no third-party tool.*
3. **Link layouts to board profiles**, and align the layout format with the platform doc
4. **Load modules from a manifest** instead of editing the app's HTML
5. **Transfer the dual LPG** to the new tool, reconciled against the as-built board
6. **MOD2 placement** and verify
7. **Getting-started doc**, and an honest statement of what the tool does and does not do
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

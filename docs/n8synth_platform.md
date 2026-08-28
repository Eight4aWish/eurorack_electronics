# n8synth Platform — Verified Reference

**The single source of truth for how the n8synth solderable breadboard and control decks
actually work.** Every claim below carries its evidence. Nothing here may be "re-derived" from
the `.n8layout` templates or the generated board profiles — those are *downstream* of this
document, and where they disagree, this document wins.

**Why this exists:** the row-count question was got wrong three times in a row by reasoning from
template geometry. The templates describe a *drawing*, not the electrical reality, and the
generated profiles hardcode assumptions that were never verified. See "Provenance" at the foot.

---

## Anatomy of a board, outside in

Working inward from either edge:

| # | Feature | Positions | Electrical behaviour |
|---|---|---|---|
| 1 | **Edge connector** | 1–40 | Two adjacent columns of holes. **Each position is a doublet — the two holes are joined to each other**, and to nothing else. |
| 2 | **Power rail** | 1–40 | Single column. **Odd = GND, even = supply.** |
| 3 | **Main area** | see variants | 5 columns. The 5 holes in a row are joined. |

**The left and right main areas are NOT joined to each other.** A row is really two independent
5-hole nodes with a gap between them.

**Power rail polarity:** numbering rows top to bottom, position 1 is GND and position 2 is
**+12V on the left-hand column** and **−12V on the corresponding right-hand column**. So:

- `pwrL` — odd = GND, even = **+12V**
- `pwrR` — odd = GND, even = **−12V**

---

## Two board variants

| | Main-area rows | Power conditioning |
|---|---|---|
| **With power section** | **1–36**, 5 columns left + 5 columns right | Yes |
| **Without** | **1–40**, 5 columns left + 5 columns right | No |

**The power conditioning is 100nF + 10µF-or-larger on each rail.**

- The **100nF caps consume no positions** — they take nothing away from anything described above.
- The **10µF+ electrolytics occupy power-rail positions 37 and 38.**
- **Power-rail positions 39 and 40 remain free**, as do 1 and 2.

⚠️ The 4HP, 6HP and 10HP templates all model the **powered** variant (36 main-area rows). The
10HPS template ships two boards — one powered (36 rows) and one plain (40 rows) — which is why
it contains 76 row zones.

### Positions 1, 2, 39, 40 on the power columns

These are reserved *only* for **jumping power between stacked boards** — needed when a design
outgrows one board (e.g. two stacked 10HP circuit boards).

**For a single-board module they are free to use.** Position 39 (GND) is particularly useful for
grounding something near the bottom of the board.

---

## How control decks connect

**JPS cell pads A, B and C terminate on the outermost columns — the edge connector.** They do
**not** land on main-area rows.

This is the point most easily got wrong. A JPS cell occupies *connector positions*, not
tie-point rows. Getting a panel component's signal into the circuit means running a wire from
its edge-connector doublet to wherever you want it in the main area.

Consequences:

- **Edge positions 37–40 are perfectly usable on a powered board**, even though there is no
  main-area row at 37–40. They are edge-connector doublets like any other. On a powered board
  they sit conveniently close to free power-rail positions 39 and 40.
- Narrow modules use **one** edge connector; **10HP uses both**.
- **Unused edge-connector doublets are free tie points and can be repurposed.** Depending on the
  control deck's HP, a greater or lesser number of them connect to nothing. Jump a component
  leg into one and route a wire up or down the board — routinely used to keep a build tidy.

### Deck pads

- **Two contact points per A, B and C pad.**
- **Every cell also has a D pad, and all D pads across the deck are joined** — a deck-wide
  ground bus.
- **Grounding practice:** tie all the jack grounds to D, then run **one** wire from any grounded
  position back to ground. Any ground will do. Picking one toward the middle of the board leaves
  power-rail position 39 free for grounding something toward the bottom.

---

## What the generated board profiles get wrong

`tools/visualizer/boards/*.json` is produced by `gen_board_profiles.py`, which hardcodes several
values. Against this document:

| Profile field | Status |
|---|---|
| `rows: 40` | ❌ **Wrong.** Conflates three different things. Powered boards have **36 main-area rows**; edge connector and power rail have **40 positions**. |
| `layoutRows: [1, 36]` | ✅ Correct for powered boards — but the name hides that it means *main-area rows only*. |
| `powerSectionRows: [37, 40]` | ❌ **Misleading.** Power-rail 37–38 hold the electrolytics; **39–40 are free**. Edge positions 37–40 are fully usable. |
| `rails` parity and polarity | ✅ **Correct.** |
| `holeCols` a–j, `centreGap` e/f | ✅ Correct — but must also record that left and right are not joined. |
| `padsPerCell {A:2, B:2, C:2, D:1}` | ✅ Correct. |
| edge connector is a **doublet** | ❌ **Missing entirely.** |
| unused doublets are repurposable | ❌ **Missing entirely.** |
| board variant (powered vs plain) | ❌ **Missing entirely.** |

---

## Provenance

**Primary source: the builder (David), 2026-08-28**, describing the physical boards in hand.
This supersedes anything inferred from the `.n8layout` templates.

Independently corroborated where possible:

- Edge connector as two joined columns — `left-edge-conn` in `6HP_Template.n8layout` has two
  hole columns (x = 0.15, 2.69) and each `ec-pad-N` carries two holes per connector ✓
- Rail parity — template zones are named `pr-neg-{odd}` / `pr-pos-{even}`; the n8synth overview
  diagram states *"compact power rails with alternating supply and GND connections"* and its
  colour key marks the left rail +12V, right rail −12V ✓
- 36 vs 40 rows — the overview diagram shows "Bread & Butter A1" numbered 1–36 with a power
  section, and "Bread & Butter B1" numbered 1–40 without ✓
- Main area 5 + 5 with a gap — each `row-N` group holds 10 holes at 2.54mm pitch with a 7.62mm
  gap between the 5th and 6th ✓
- Deck D bus — 6HP quick-start guide: *"the D bus … a common ground on the Control Deck"* ✓
- Cell numbering row-major, odd left / even right — annotated control-deck diagram ✓

**Unverified, still open:**

- Whether stacked boards pass *signals* through, or only power (power pass-through is confirmed:
  "2 pin, single row headers, mounted here pass power to stacked boards").
- Which physical edge the single connector uses on 4HP/6HP. `gen_board_profiles.py` assumes the
  left and marks it builder-confirmed; not re-checked here.

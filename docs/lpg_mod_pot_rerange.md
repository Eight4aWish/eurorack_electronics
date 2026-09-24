# Dual Pingable LPG — pot re-range mod

**Status:** rev 0.27, proposed. Not yet built, not yet measured.
**Why:** in use, very little of DEPTH's and MANUAL's travel does anything audible.
**Source of the diagnosis:** [lpg_netlist.md](lpg_netlist.md) → "Pot re-range".
**Bench checklist:** Phase 6 in the visualiser (`tools/visualizer/index.html`).

This is written for picking the board up cold, months after building it. It assumes
nothing is remembered beyond "there is a dual LPG on an n8synth board somewhere."

---

## Read this before you order anything

**The DEPTH rewire reverses which way the knob opens the gate.**

Today, fully clockwise = most open. After the rewire, fully **counter-clockwise** =
most open. That is not a mistake in the procedure — it is unavoidable. A rheostat's
useful travel and its direction of rotation are set by the same choice of which end is
shorted, so you cannot fix the range by rewiring without also flipping the direction.

That gives two routes:

| Route | Cost | Direction | Use when |
|---|---|---|---|
| **A — rewire** (this doc, step 3) | free, 10 minutes | **reverses** | Proving the diagnosis is right |
| **B — reverse-log pot** | a new 500K **C-taper** pot per channel | unchanged | Making it permanent |

Do **route A first**, even if you intend to end up at route B. It costs nothing, it
takes ten minutes, and it answers the only question that matters: *is the taper
orientation really what is eating the range?* If route A widens the usable travel, the
diagnosis is confirmed and route B buys the same width back with the original knob
direction. If route A does **not** widen it, the theory is wrong, the pot's taper does
not run the way this assumed, and you should put the wiring back rather than order parts.

**Parts to have in hand before starting:**

- **Step 3 (DEPTH): nothing.** Two wires move between holes that already exist, at the
  edge connector. The panel does not come apart.
- **Step 4 (MANUAL):** either 2 × **10K linear** pots (route 1 — fewer parts, but the
  panel comes apart), or 6 × **47K** and 4 × **100K** resistors (route 2 — more parts,
  all on the breadboard, panel untouched). Same result either way.
- **Step 5 (optional):** 2 × **BZX55C9V1** zeners. Already in the BOM as a stocked bench
  alternative, so probably in the zener strip.

---

## 0. Orientation — what you are looking at

The LPG lives on an **n8synth solderable breadboard**. Two independent channels, each a
Buchla 292 audio path whose brightness and level are set by a vactrol that a small op-amp
driver lights. The four pots per channel are **off-board**, on the panel, wired back to
holes on the **control board** — the columns outboard of the power rails, called `ctrlL`
(left) and `ctrlR` (right) in the layout.

Only two of the four controls are touched here: **DEPTH** and **MANUAL**. CV ATTEN and
the Strike jack are not involved.

Open `tools/visualizer/index.html` in a browser and select **Phase 6**. It highlights
exactly the holes named below, which is much faster than reading row numbers off a table.

### Where the relevant control holes are

| Control | Channel | Column | Rows (a / wiper / c) |
|---|---|---|---|
| DEPTH | A | right (`ctrlR`) | 4 / **5** / 6 |
| DEPTH | B | left (`ctrlL`) | 20 / **21** / 22 |
| MANUAL | A | left (`ctrlL`) | 4 / **5** / 6 |
| MANUAL | B | right (`ctrlR`) | 35 / **36** / 37 |

The wiper row is the one in bold. On DEPTH, the wiper hole is also where the 470R
(**R6** channel A, **R12** channel B) lands — that resistor does **not** move in any step
below. If you find yourself unsoldering a 470R, stop; something has gone wrong.

### The panel never has to come apart

Each edge-connector position is a **doublet**: two holes joined to each other and to
nothing else. The **outer** hole carries the deck connection — the run out to the pot via
the control deck — and the **inner** hole is a free tie point on the same node. The pot's
three legs arrive as JPS pads A/B/C at three consecutive positions, and the driver wire
and the link wire land on the inner holes there.

So **DEPTH is rewired entirely at the edge connector.** Nothing is unsoldered at the pot,
the panel does not come off, and the pot is never removed. Two wires move, one position
each. (MANUAL in step 4 is different — changing a pot's *value* does need the pot, unless
you take the board-side alternative given there.)

### Identify which position is the CW end — by measuring

The procedure needs "the CW end" and "the CCW end". Do not infer them from the a/b/c
labels or from which lug looks left: the mapping depends on how the pot was wired to the
deck when it was built, and getting it backwards undoes the whole mod.

Measure at the edge-connector positions, power off:

1. **Lift the link wire first.** While position 4 is shorted to the wiper, a meter across
   them reads 0 Ω at every shaft angle and tells you nothing.
2. Meter between the **wiper position** (DEPTH A: 5, right edge) and each outer position
   (4 and 6) in turn, using the free inner holes.
3. Turn the shaft **fully clockwise**. The position now reading **≈ 0 Ω** to the wiper is
   the **CW end**; the one reading ≈ 500K is the **CCW end**.
4. Write down which is which. On channel A the layout expects CW = position 6 and
   CCW = position 4, but confirm rather than assume.

---

## 1. Safety and setup

1. Power the rack **down**. Unplug the LPG's power cable from the bus board.
2. Wait a few seconds; the decoupling caps are small but there is no reason to rush.
3. Have ready: soldering iron, solder sucker or braid, meter, small screwdriver,
   and something to write the step-2 numbers on.
4. Work one channel at a time, A first. Channel B is a mirror and you will have learned
   the moves by then.

---

## 2. Record the "before" — do not skip this

This is the only way to know afterwards whether the mod helped. It takes five minutes.

1. Power up. Patch an oscillator into **CH A IN** and **CH A OUT** to your monitor.
2. Set **MANUAL A** to minimum. Set **DEPTH A** fully clockwise.
3. Turn DEPTH A slowly from fully CW to fully CCW. Note, as a **fraction of travel**,
   where the sound starts changing and where it stops changing.
   Write it down, e.g. _"DEPTH A: all the action in the first ~10% from CW; rest dead."_
4. Set DEPTH A fully open again. Sweep **MANUAL A** from minimum to maximum and note the
   same thing. Expect the gate to stay shut for most of the travel and open near the top.
5. Repeat 2–4 for channel B.
6. **Ping test:** with MANUAL at minimum, send a gate into **STRIKE A** and listen to the
   decay tail. Record roughly how long it rings. You will compare this at the end —
   the tail should be *unchanged* by everything in this doc.

---

## 3. DEPTH rewire — free, reverses the knob direction

Per channel. Nothing is added or removed; two wires swap which pot lug they land on.

**What is true now:** the driver output feeds the **CW** lug, and the **CCW** lug is
shorted to the wiper with a short link wire.

**What you want:** the driver output feeds the **CCW** lug, and the **CW** lug is shorted
to the wiper.

All of it happens at the edge connector, on the free inner holes. The pot stays where it
is and the panel stays together.

Steps, **channel A — right edge connector, positions 4 / 5 / 6**:

1. Power off.
2. Find the two wires to move:
   - the **link wire**, a short jumper tying position **4** to position **5** (the wiper);
   - the **driver wire**, running from position **6** back to the driver (R6's node).
3. Lift the **link wire** end off position 4.
4. Now confirm CW/CCW by the measurement in section 0. Expected: 6 = CW, 4 = CCW.
5. Lift the **driver wire** off position 6.
6. Land the **link wire** on position **6** (its other end stays on the wiper, 5).
7. Land the **driver wire** on position **4**.
8. Meter check, still powered off: wiper (5) to position 6 should read ≈ 0 Ω at every
   shaft angle — that is the new short. Wiper (5) to position 4 should sweep 0 → 500K as
   you turn the shaft.

Then **channel B — left edge connector, positions 20 / 21 / 22**, exactly the same moves:
link wire from 20 to 22, driver wire from 22 to 20, wiper stays at 21.

Nothing else moves. **R6** (channel A) and **R12** (channel B) stay on the wiper
positions throughout — if you find yourself lifting a 470R, stop and re-read.

**Test now — Phase 6 test 6.2.** Power up and repeat the DEPTH sweep from step 2.

- **Usable travel is much wider, but the knob works backwards** → the diagnosis is
  confirmed. Decide: live with the reversed direction and re-legend the panel, or order
  C-taper pots (route B) and put this wiring back.
- **Usable travel is the same narrow sliver, just at the other end** → the theory was
  wrong for this pot. Undo steps 3–6 and stop here; do not order anything.

---

## 4. MANUAL — two routes to the same result

This one does not change direction, only how much of the travel is alive.

**Why it is dead at the bottom:** the 4K7 summing resistor (**R32** ch A, **R33** ch B)
loads the wiper into the driver's virtual ground. Against a 100K pot that is roughly a
20:1 load at mid-rotation, collapsing the wiper to well under a volt where open-circuit
would be ~5.7V. With the driver's 10K/4K7 gain the output then stays under the ~3.2V the
two vactrol LEDs in series need to conduct until about three-quarters of the way up.

The cure is to make the pot's source impedance small compared with what loads it. You can
do that from either end, and the two are electrically equivalent:

### Route 1 — swap the pots (2 parts, panel comes apart)

Fit **10K linear** pots in place of the 100K. Wiring is unchanged.

1. Power off.
2. At **MANUAL A**, photograph the wiring before unsoldering. Expect: one outer lug to
   GND, the other outer lug to the top feed, the middle (wiper) to the wiper position.
3. Unsolder the three wires, remove the 100K, fit the 10K.
4. Re-solder the three wires to the same lugs. **If the two outer lugs swap, MANUAL runs
   backwards** — GND must return to the same lug it came off.
5. Repeat for **MANUAL B**.

### Route 2 — scale the driver network ×10 (10 parts, no panel work)

Keep the 100K pots and raise every resistor around the driver tenfold. All ten are on the
breadboard, so this is the route that never opens the panel. Because *every* ratio in the
summing network is preserved, CV and Strike scaling are untouched — that is the whole
point of scaling all of them together rather than just R32.

| Designator (A / B) | Role | Was | Becomes |
|---|---|---|---|
| R29 / R30 | VCC → MANUAL top | 4K7 | **47K** |
| R32 / R33 | MANUAL wiper → summing node | 4K7 | **47K** |
| R38 / R39 | CV wiper → summing node | 4K7 | **47K** |
| R34 / R35 | Strike pulse → summing node | 10K | **100K** |
| R36 / R20 | driver feedback | 10K | **100K** |

R37 / R14 (the 10K from the op-amp's +in to ground) can stay as they are — the TL072 is
FET-input, so the bias-current match they provide is irrelevant at these values.

**Do not do half of this.** Raising R32 alone without R36 drops the MANUAL gain; raising
R36 alone multiplies CV and Strike by ten. The table is all-or-nothing, per channel.

### Either way — test now (Phase 6 test 6.3)

Sweep MANUAL and compare against your step-2 note. The gate should now start opening
around a quarter of the travel rather than three-quarters.

---

## 5. Optional — zener swap, if the top still feels compressed

Only if, after steps 3 and 4, both controls still bunch up near maximum.

The zeners **VD5** (channel A) and **VD6** (channel B) cap the vactrol LED current. They
are **socketed**, so this needs no soldering.

1. Power off.
2. With MANUAL and DEPTH both fully open, power up and measure DC from **VC pin 1 to
   GND**. If it sits right at about **−6.8 V**, the clamp is limiting and the swap is
   worth doing. If it sits well short of that, the clamp is not your problem — skip this.
3. Power off. Pull the **6v8** zener from its socket and fit a **9v1** in the same
   orientation (banded end toward GND, exactly as the one you removed).
4. Repeat for the other channel.

This lifts the ceiling from about 7.7 mA to about 12.6 mA.

---

## 6. Final check

1. **Ping both channels** and compare the decay tail against your step-2 note. It should
   be **unchanged** — none of this touches the vactrol itself, so a changed tail means
   something moved that should not have. Recheck your work.
2. Sweep both controls on both channels and confirm A and B behave alike. They will not
   match perfectly; LDR part spread is wide. A gross difference means a wiring error.
3. Write the result — including the "before" and "after" travel fractions — into
   [lpg_netlist.md](lpg_netlist.md) under "Pot re-range", and change rev 0.27 from
   *proposed* to *as-built* in
   [lpg_breadboard_placement.md](lpg_breadboard_placement.md).

## If it all went wrong

Every step is reversible with no parts lost:

- **Step 3:** move the link wire back to the CCW position and the driver wire back to CW
  (channel A: link to 4, driver to 6; channel B: link to 20, driver to 22).
- **Step 4, route 1:** refit the original 100K pots, same three lugs.
  **Route 2:** put the original 4K7 and 10K resistors back per the table.
- **Step 5:** refit the 6v8 zeners.

The as-built wiring before this mod is recorded in the layout history — the rev note in
`tools/visualizer/layouts/lpg.json` describes the original DEPTH orientation in full.

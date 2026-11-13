# Installation and commissioning (9x20 / 10x22-class lathe)

Mechanical installation, first power-up, calibration and the first thread. Read
[WIRING.md](WIRING.md) first: the electrical work and its bring-up (section 11 there)
come before everything in sections 6-10 below. Settings live in
`firmware/include/lathe_config.h`; this guide refers to them by name.

> **Safety.** This puts a 3 Nm motor on the leadscrew of a machine tool. The software stops are soft limits
> only; nothing stops the carriage if you lose power to the Teensy while moving or set a stop wrongly.
> Keep a hand on the E-stop for the first runs, keep the stops well clear of the chuck and tailstock,
> and fit guards over both belts. Unplug the spindle motor (or isolate it) whenever you reach into the headstock.

Contents: 1 Decision, 2 Measure the lathe, 3 Motor and leadscrew drive, 4 Spindle encoder,
5 Firmware settings, 6 First power-up checklist, 7 Using the controls, 8 Calibration run,
9 First thread on scrap, 10 Threading to a shoulder, 11 Troubleshooting.

---

## 1. Where the motor drives: decision

A stock 9x20 has a spindle gear on the left (headstock) end, a quadrant (banjo) with the change gears,
and the leadscrew. Many 9x20 clones have no feed gearbox. Some 10x22 variants have a small gearbox.

**Decision: drive the leadscrew directly** (HTD-3M belt, 20T on the motor to 40T on the leadscrew end), at the headstock
end of the leadscrew where the change-gear "leadscrew gear" used to sit.

Why:

* No gear train means no backlash between the spindle and the leadscrew, and no unknown ratios to measure.
* `GEARBOX_RATIO_NUM` / `GEARBOX_RATIO_DEN` stay **1 / 1** (the config comment: "Motor drives the leadscrew directly: 1/1").
* The 2:1 belt reduction doubles the available torque (about 6 Nm at the leadscrew from the 3 Nm motor, before losses) and halves the step angle at the leadscrew.
* Resolution: 1600 x (40/20) = 3200 steps per leadscrew turn; at 8 TPI (3.175 mm) that is 1007.9 steps/mm (about 1 µm).

**If your lathe has a feed gearbox you want to keep** (for example a Norton-type box between the old change-gear
stud and the leadscrew), drive the **gearbox input shaft** instead, leave the gearbox lever in one fixed position,
and measure that position's ratio (section 2.3). Everything else is unchanged. This works, but you inherit the
gearbox's backlash and wear. The direct-drive option is better whenever you can do it.

Leave the **half-nut (leadscrew nut) permanently closed**. The NUT button replaces the lever. If you open the
half-nut and move the carriage by hand, the carriage position the controller remembers (and all stops) is wrong.

---

## 2. Measure the lathe

### 2.1 Before you take anything apart

Photograph the change-gear train, the gear cover, and the leadscrew end. Write down:

* the tooth counts of all gears and the chart on the cover (you may want to restore the lathe one day),
* the leadscrew end: **diameter**, key or keyway (width x depth), the retaining nut or screw, thread, and how much shaft sticks out beyond the bearing,
* the clear space around the leadscrew end: where a 15 mm wide pulley (plus about 3 mm clearance either side) and the belt can go, and what the motor body (57 x 57 mm, body about 113-138 mm long depending on the source; check your datasheet) hits.

You need this to choose the bore of the 40T pulley (the Mädler 40T has a 16.5 mm maximum bore, some others go to 20 mm) and to design the motor plate.

### 2.2 Leadscrew pitch (TPI / pitch)

Do this twice by different methods; the two should agree within 0.5 %.

1. **Pitch gauge or scale.** Count thread crests over a known length of the leadscrew at an exposed place. For an imperial 8 TPI screw, 8 crests span 25.4 mm. For metric screws measure crest to crest with calipers over 5-10 pitches and divide. Typical values: 8 TPI = 3.175 mm, 12 TPI = 2.117 mm, 16 TPI = 1.5875 mm, metric 1.5 / 2 / 3 mm.
2. **Travel per turn (best).** With the half-nut closed and a dial indicator on the carriage (magnetic base on the bed), turn the leadscrew by hand a counted number of turns (for example 10, using a mark on the 40T pulley) and read the carriage travel. Pitch = travel / turns. For an 8 TPI screw 10 turns = 31.75 mm. Take readings in the same direction to keep backlash out of it.

Enter it as:

* `LEADSCREW_TPI` = the integer TPI (the code takes integer TPI only), or
* `LEADSCREW_TPI 0` and `LEADSCREW_PITCH_UM` = the pitch in micrometres (for example 3000 for a 3 mm screw, 3175 for 8 TPI exactly).

The default (`LEADSCREW_TPI 8`) is only right if your screw is 8 TPI. [DESIGN.md](DESIGN.md) says: "verify on your lathe".
Section 8 refines the value after the first run.

### 2.3 Gearbox ratio (only if you keep a gearbox)

For the direct-drive choice the answer is `GEARBOX_RATIO_NUM 1` / `GEARBOX_RATIO_DEN 1`. Skip to section 3.

If you drive a gearbox input shaft instead, in the lever position you will leave it in:

1. Put a bright mark on the input shaft (or the input pulley) and on the leadscrew.
2. Turn the input shaft by hand (power off, nothing engaged except the gearbox) and count input turns while the leadscrew turns a whole number of times (for example 10 leadscrew turns).
3. Ratio = **input turns per leadscrew turn**. That is exactly the firmware's definition: "input-shaft revolutions per leadscrew revolution as a fraction".
4. Express it as an exact fraction from the tooth counts if you can (for example 40/20 -> `GEARBOX_RATIO_NUM 2`, `GEARBOX_RATIO_DEN 1`). Measure only to confirm, and use the exact fraction, because a rounded decimal produces drift over a long thread.
5. Steps per leadscrew turn become `MOTOR_STEPS_PER_REV x LEADSCREW_PULLEY_TEETH x NUM / (MOTOR_PULLEY_TEETH x DEN)`; the motor then drives the gearbox input. In this case `LEADSCREW_PULLEY_TEETH` is the pulley on the gearbox input shaft.

---

## 3. Motor and leadscrew drive

### 3.1 Remove the change gears

1. Unplug the lathe. Remove the gear cover.
2. Remove the change gears, the banjo (quadrant) and the tumbler reverse gears if present. Keep the gears, keys and washers in a labelled bag.
3. Take off the old gear on the leadscrew end. **Keep the leadscrew's axial play (thrust) the way it was**: reinstall any collar, nut or washer that sets the end float, so the leadscrew cannot slide when the carriage reverses.
4. Check the end of the leadscrew for burrs, and check the bearing or bushing for slop. Any radial slop here becomes a belt-load problem later.

### 3.2 Leadscrew pulley and motor plate

1. **Pulley.** Bore the 40T HTD-3M pulley to a close sliding fit on the leadscrew end (about H7). Use the old key and keyway if there is one: a 3M pulley with two set screws plus a key does not slip. Fit it flush with the shoulder so the belt line is at a fixed, known place; add a spacer and a retaining screw/washer or the original nut. Put thread locker on the set screws.
2. **Motor plate.** NEMA 23 pattern: 47.14 mm square holes, 38.1 mm pilot. Use 6 mm aluminium plate or 4 mm angle. The motor must be able to **slide** to tension the belt: use slots in the plate (or in the lathe-side bolts) in the direction of the belt. Mount it where the old banjo bolts or tapped holes can carry it; if you drill new holes in the casting, keep swarf out of the gears and bearings.
3. Fit the 20T pulley on the motor's 8 mm shaft with one set screw on the D-cut flat, flush with the shaft end, thread locker on.
4. **Keep the belt line square.** The two pulley flanges should be in the same plane within about 1 mm; a twisted belt wears and climbs.
5. Do not run the motor cable across the belt; clip it away from moving parts.

### 3.3 Belt length and tension

HTD-3M, 3 mm pitch. Pitch diameter = teeth x 3 / pi: 20T = 19.10 mm, 40T = 38.20 mm.

Belt length for centre distance C (mm):

```
L = 2 C + 1.5708 (D1 + D2) + (D2 - D1)^2 / (4 C)
  = 2 C + 90.0 + 91.2 / C           (20T + 40T)
```

Worked examples (belt length = teeth x 3 mm):

| Belt | Teeth | C (mm) |
|---|---|---|
| 3M-189 | 63 | 48.6 |
| 3M-201 | 67 | 54.7 |
| 3M-210 | 70 | 59.2 |
| 3M-225 | 75 | 66.8 |

Longer belts for bigger centre distances follow the same formula. Check which lengths your supplier
stocks, then design the plate so the motor lands within the slot range for the nearest length. Check
the minimum C: the 20T flange (about 23 mm) and 40T flange (about 42 mm) must clear, and the motor body must clear the lathe.

**Tension.** A rule of thumb, not a manufacturer figure: with a firm finger press at mid-span the belt should
deflect about 1 mm per 50 mm of span. Too loose lets the belt flex and lose steps under acceleration or gives backlash when
the carriage reverses; too tight loads the leadscrew bearing and the motor bearing. After the first runs, re-check the
tension and the set screws. A skipped tooth is a lost position: the controller cannot know.

---

## 4. Spindle encoder

### 4.1 The mechanical idea

The LPD3806 (600 PPR) runs 1:1 from the spindle with a GT2 belt: 60T on the spindle end, 60T on the encoder.
So one encoder turn per spindle turn and `ENCODER_CPR` = 600 x 4 = **2400** (every edge counted).
`ENCODER_CPR` is the encoder's own counts per turn after quadrature. How it is driven goes in
`ENCODER_TURNS` / `SPINDLE_TURNS` (encoder turns per spindle turns). Any ratio works, fractional included: the
firmware keeps it as an exact fraction. With a fractional count per spindle turn, a re-armed NUT may wait a few
spindle turns (until the counts come out whole) before it closes.

**Roher TBL-20/520 (= Axminster BV20M):** the change-gear stud under the spindle turns once per 6 chuck turns
(counted 2 stud turns per 9 chuck turns; the gear table gives stud ratio x leadscrew pitch = 2/3 mm, and 2/9 x 3 mm = 2/3).
The encoder is driven from the stud by a GT2 60T:20T belt (see cad/), so it turns at 2/9 x 3 = 2/3 chuck speed: set
`ENCODER_TURNS 2` / `SPINDLE_TURNS 3`, which gives 1600 counts per chuck turn. Check it once: at a known speed-chart
setting the RPM on the screen must match.

### 4.2 Where to mount the drive pulley

Use the **outboard (left) end of the spindle**, where the change-gear train used to take its drive, or the first (spindle) gear itself:

* **Option A (preferred): replace the old spindle gear with a machined hub.** Make an aluminium hub that takes the spindle gear's place on the shaft (same bore, same key/flat or clamp), carrying the 60T GT2 profile or a flange to bolt a 60T GT2 pulley on.
* **Option B: bolt a 60T pulley to the old gear.** Drill and tap 3-4 M4 holes in the gear web on a pitch circle and bolt a hub plate with the pulley to it. Check the pilot fit and run-out.

Rules:

* **No slipping at the spindle end.** Use a key, a flat with two set screws, or a clamp with proper bite. A printed hub (PETG/ASA) is only good for the encoder bracket, not for the spindle-side drive hub, which sees full spindle speed. If a hub shifts by one tooth, the thread phase is gone.
* The hub must be balanced and run true; check with the dial indicator (under 0.05 mm total run-out). Remove any loose set-screw tips that stick out: guard against them.
* Put a guard over the belt (a printed or sheet-metal cover).

### 4.3 Encoder bracket and belt tension

GT2 belt length for two identical 60T pulleys (pitch diameter 38.2 mm, circumference 120 mm):

```
L = 2 C + 120 mm         (C = centre distance)
```

For example a 300 mm closed-loop belt needs C = 90 mm; 240 mm needs C = 60 mm; 330 mm needs C = 105 mm.

* The bracket is printed (PETG/ASA, with heat-set M3/M4 inserts) with **slotted holes** to tension the belt. Mount it on an insulating part so the encoder body is not grounded through the lathe (WIRING 5.1).
* Tension: light. Under light finger pressure at mid-span the belt deflects about 1-2 mm per 50 mm of span. The belt must not slip and the encoder bearing must not be loaded sideways.
* Mount the 60T pulley on the encoder's 6 mm shaft with the set screw on the flat (if any) or use a clamp pulley; thread locker. The encoder shaft is not made for side load: keep the belt tension light.
* Mark the pulley and belt with a pen so you can see slip later.
* Route the encoder cable away from the belt, spindle and motor leads; use the strain relief.

---

## 5. Firmware settings

`firmware/include/lathe_config.h`. Defaults in brackets.

| Name | Default | How to set it |
|---|---|---|
| `ENCODER_CPR` | 2400 | Encoder counts per encoder turn: PPR x 4 (600 PPR = 2400) |
| `ENCODER_TURNS` / `SPINDLE_TURNS` | 2 / 3 | Encoder turns per spindle turns (Roher: stud 2/9 x GT2 60T:20T = 2 / 3; encoder 1:1 on the stud: 2 / 9) |
| `INVERT_SPINDLE` | 0 | "Set to 1 if the position readout counts DOWN when the spindle runs forward." Check in 6.2 (or swap A and B at J3) |
| `MOTOR_STEPS_PER_REV` | 1600 | Must equal the CL57T DIP switches: SW1 on, SW2 off, SW3 on, SW4 on (WIRING 4.2) |
| `MOTOR_PULLEY_TEETH` | 20 | HTD-3M pulley on the motor |
| `LEADSCREW_PULLEY_TEETH` | 40 | HTD-3M pulley on the leadscrew (or on the gearbox input if you keep the gearbox) |
| `GEARBOX_RATIO_NUM` / `GEARBOX_RATIO_DEN` | 1 / 1 | Direct drive: 1/1. With a gearbox: input turns per leadscrew turn (section 2.3) |
| `LEADSCREW_TPI` | 0 | Integer TPI of an imperial leadscrew. 0 = use the metric value |
| `LEADSCREW_PITCH_UM` | 3000 | Leadscrew pitch in micrometres, used when `LEADSCREW_TPI` is 0 (Roher TBL-20/520: 3 mm) |
| `INVERT_DIR` | 0 | "Set to 1 if JOG -> moves the carriage toward the headstock." Check in 6.3. Do not also change SW5 |
| `MAX_SPEED_MM_S` | 40.0 | Fastest threading/rapid speed; the controller refuses synchronised motion above 90 % of it ("SPINDLE TOO FAST") |
| `ACCEL_MM_S2` | 600.0 | Keep modest: the carriage is heavy. Reduce if you get following-error alarms (red LED 7 blinks) |
| `JOG_SPEED_MM_S` | 20.0 | Jog speed. Use 5-10 for the first power-up |
| `ENABLE_ACTIVE_LEVEL` | LOW | Pin 7 LOW enables the motor (CL57T: ENA opto on = disabled) |
| `ALARM_ACTIVE_LEVEL` | LOW | Level of pin 8 on alarm. Verify it for your driver (WIRING 4.6) |

For the first power-up use `MAX_SPEED_MM_S` 20, `ACCEL_MM_S2` 300 and `JOG_SPEED_MM_S` 5-10, then raise them once everything works.

Check the numbers: 3200 steps per leadscrew turn / 3 mm = 1066.7 steps/mm (kept as the exact fraction 3200/3); at 40 mm/s the step rate is 42.7 kHz, just under the controller's hard limit of 0.45 x `MOTION_TICK_HZ` = 45 kHz (about 42 mm/s); that is 1600 motor rpm.

**Maximum spindle speed for a pitch.** The nut will refuse (and the TFT shows "SPINDLE TOO FAST") when
spindle rev/s x pitch exceeds 0.9 x `MAX_SPEED_MM_S`. With 40 mm/s: 1.5 mm pitch -> 1440 rpm, 3 mm -> 720 rpm. Threading is done much slower than that.

---

## 6. First power-up checklist

Do [WIRING.md section 11](WIRING.md) first (continuity, supply voltages, K1, driver LEDs, ENA test, ALM polarity).
Then, in this order:

### 6.1 Bench check, belts off

1. Motor belt **off**, carriage in the middle of the bed, half-nut closed.
2. Power the 5 V logic only (or USB). The TFT shows the UI. Press each button: the display reacts.
3. **E-stop pressed:** TFT shows E-STOP, FAULT LED on. Release; any key clears it.
4. Power the 48 V (K1 closed): driver green LED on, red LED off, motor shaft held (hard to turn by hand).
5. **Disable test:** with the Teensy reset/unplugged, the motor must be free to turn by hand (the ENA pull-up makes the driver disabled). If it is held, fix the ENA wiring or polarity before going on.
6. Press the E-stop: K1 clicks, motor free. Release, clear the fault, motor held again.

### 6.2 Spindle encoder direction check

The requirement: **the count must go UP when the spindle turns forward** (forward = normal turning rotation, the top of the work moving toward you).

1. Spindle motor isolated. Open a serial monitor on the Teensy at 115200 baud (the firmware prints a line like `rpm=12.3 x=0.000 ...`; the `rpm` field is signed). Cut the VUSB-VIN link or disconnect the 5 V from VIN while USB is plugged in (WIRING 2.8).
2. Turn the chuck by hand in the forward direction at about 30-60 rpm. `rpm` must read positive (the direction detector needs a little over 3 rpm).
3. Check the magnitude: turn at a steady known rate or use a tachometer or the lathe's own low speeds. The reading must match within about 1 %. A reading that is 2x or 4x off means `ENCODER_CPR` is wrong or the belt ratio is not 1:1; a reading that jumps around means noise (check shielding and the pull-ups).
4. If it reads **negative**, fix it either by swapping the A and B wires at J3 (hardware) **or** by setting `INVERT_SPINDLE 1` in the firmware. Do one, not both.

### 6.3 Carriage direction check (motor and belt on)

1. Fit the belt. Slow limits: `JOG_SPEED_MM_S` 5-10.
2. Set **both stops** before anything moves: STOP_L (press) with the carriage at least 10-15 mm to the right of the chuck, and STOP_R at least 10-15 mm left of the tailstock end of the bed travel. Soft stops hold in every mode.
3. Hand on the E-stop. Press and hold **JOG R**: the carriage must move **toward the tailstock** (the display position goes up: +X is toward the tailstock). Release: it decelerates.
4. If it goes the wrong way set `INVERT_DIR 1` and reflash (or flip SW5 on the driver, but do not do both).
5. Test JOG L the other way. Listen for belt noise, grinding, or the carriage binding. Check the carriage does not go stiff anywhere along the bed (the lathe's gibs may need adjusting); a 3 Nm motor will happily break a bound-up carriage.

### 6.4 Spindle forward drives the carriage toward the headstock

1. In FEED mode (mm/rev) with a small feed (for example 0.10 mm/rev), press NUT, then turn the chuck **forward** by hand. The carriage must feed **toward the headstock** (-X, normal right-hand direction). It stops at STOP_L and the nut opens (the display says "AT STOP - NUT OPENED").
2. If not, but JOG direction was right, the spindle sign is wrong: go back to 6.2.
3. Turn the chuck backwards by hand while engaged: the carriage follows backwards (metric-on-imperial technique).

### 6.5 Spindle power on

Run the spindle at a low speed (for example 150 rpm) and engage a feed again. Check the encoder belt, hub and cable for contact. Watch for any fault on the display. Then set the real motion limits.

---

## 7. Using the controls

(Short reference; the full behaviour is in [DESIGN.md](DESIGN.md).)

| Key | Action |
|---|---|
| NUT | Feed mode: engage now. Thread mode: the first press of a thread sets the thread phase; later presses **arm** (the LED blinks) and engage at exactly the same spindle angle. Press while engaged to open. Pressing while armed cancels |
| MODE | Tap: feed / thread. **Hold 1 s: new thread (sync reset)** |
| UNITS | metric / imperial (starts a new thread) |
| DIR | normal (toward headstock, RH) / toward tailstock (LH thread) (new thread) |
| STOP_L / STOP_R | tap = set the stop at the carriage position; **hold 1 s = clear** |
| JOG_L / JOG_R | hold to jog toward the headstock / tailstock (nut must be open) |
| RETURN | rapid to the start of the pass (the stop opposite the feed direction; with no stop set, to where the last pass started) |
| Knob | turn = change the pitch/feed or jog a step; push cycles pitch / jog 0.01 / 0.1 / 1 mm per detent |

The half-nut and sync rules: changing pitch, mode, units or direction, an E-stop, or a driver alarm **loses the thread sync**.
Between passes of one thread do not touch those controls. Faults also clear on any key once the cause is gone.

---

## 8. Calibration run

Purpose: check that the commanded carriage travel matches the real travel, and correct `LEADSCREW_PITCH_UM` if it does not.

1. Clamp a dial indicator (0.01 mm) on the bed or a rigid arm, with its tip on the carriage, **or** use calipers between the carriage and a fixed point (calipers resolve 0.02 mm, which is 0.02 % over 100 mm).
2. Set `JOG_SPEED_MM_S` to something sensible (10). In FEED mode with the nut open: choose the 1 mm jog step (push the knob until the display shows jog 1 mm per detent).
3. Move the carriage to a start position with **JOG R** (always arrive from the same direction to keep backlash out) and note the TFT position `X1` and the real reading `R1`.
4. Move **exactly 100 mm** toward the headstock by jogging, approaching from the same direction, for example 100 knob detents at 1 mm. Note `X2` (displayed) and `R2` (real). If your indicator only travels 10-25 mm, measure in 25 mm segments and add them, re-setting the indicator at each segment, or use calipers or a rule against the carriage.
5. Repeat in the opposite direction and average, so the backlash cancels.
6. Compute:

```
displayed = |X2 - X1|        (should be about 100.000)
actual    = |R2 - R1|
factor    = actual / displayed
new LEADSCREW_PITCH_UM = round(old pitch in um x factor)
```

Example: displayed 100.000 mm, actual 99.62 mm, old pitch 3175 um (8 TPI):
factor = 0.9962, new pitch = 3175 x 0.9962 = 3162.9, so set `LEADSCREW_TPI 0` and `LEADSCREW_PITCH_UM 3163`, reflash, repeat the run.

Reasoning (so you can check the sign): the firmware computes steps from the configured pitch; real travel per step scales with the true pitch.
So true pitch = configured pitch x actual / displayed.

Interpreting the result:

* **Within about 0.1-0.3 %:** a normal leadscrew pitch error or wear. Use the correction above.
* **More than 0.5 %, or a "round" ratio like exactly 2x, 1.6x or 0.5x:** something is configured wrong. Check `MOTOR_STEPS_PER_REV` against the DIP switches, the tooth counts, the TPI, and whether the leadscrew is really what you measured.
* Differences along the bed are wear in the leadscrew or nut; the correction only fixes the average.
* **Backlash:** while at it, measure the backlash by reversing and reading the indicator. It does not matter for threading (the nut loads one flank), but it explains why every thread pass starts a little "late".

Also check the spindle speed readout against a tachometer once: this cross-checks `ENCODER_CPR`.

---

## 9. First thread on scrap

Before cutting a real part, cut a thread on a scrap bar (20-25 mm aluminium or free-cutting steel).

1. Chuck a bar with about 50-60 mm out. Turn it to the thread major diameter. Cut a **relief groove** (about 2-3 pitches wide, slightly deeper than the thread) at the end of the thread so the tool has a place to go when the nut opens.
2. Fit a 60-degree threading tool on centre, square to the work. The lathe's own cross-slide and compound as usual (compound at 29.5 degrees if you use it).
3. THREAD mode, metric, a coarse-ish pitch for a first test (1.5 mm). The spindle at **100-200 rpm**.
4. Set STOP_R clear of the work end (start) and STOP_L inside the relief groove (the end). Allow about 5 mm of run-in at the start: the nut engages at speed and the carriage needs a few mm to catch up (and to take up the leadscrew backlash).
5. Touch the tool to the work, zero the cross-slide dial, back the tool off, bring the carriage to the start, then **NUT** (first press: thread phase set), tool in by about 0.1 mm. Let it run to the stop. Retract, RETURN, infeed, NUT (it arms and engages at the same angle), and so on (section 10).
6. After 4-5 passes, check:
   * **Pitch.** Measure 10 pitches with calipers (15.00 mm for 1.5 mm pitch) or use a thread pitch gauge.
   * **Registration.** Every pass must land in the same groove. A second groove cut beside the first means the sync failed (section 11).
   * Try a nut or a thread gauge.
7. Do a spring pass (no infeed) to clean up, then deburr.

---

## 10. Threading to a shoulder with the NUT button

Setup, done once per thread:

1. THREAD mode, choose units and pitch with the knob, DIR normal (toward the headstock) for a right-hand thread. Nut open.
2. Half-nut closed. Spindle forward at a steady low rpm (**the same rpm for every pass of the thread**, see WIRING 4.2 about the pulse filter).
3. **Set the stops.** Jog the tool to the start position, clear of the work end by the run-in distance, and press **STOP_R**. Then jog to the end of the thread, in the relief groove or about one pitch before the shoulder, and press **STOP_L**. (For a left-hand thread, or DIR toward the tailstock, the start and end swap sides; RETURN always goes to the stop opposite the feed direction.)
4. Jog back to the start (or press RETURN).

Each pass:

1. Cross slide at the pass depth. Press **NUT**.
   * First pass of a thread: the nut engages immediately and sets the thread phase ("NEW THREAD - SYNC SET").
   * Later passes: the NUT LED blinks while armed, and the nut engages on the exact spindle angle that puts the tool back in the same groove.
2. The carriage feeds toward the headstock. At STOP_L it decelerates onto the stop and the **nut opens by itself** ("AT STOP - NUT OPENED"). The spindle keeps turning and the tool sits at the end of the groove.
3. **Retract the cross slide immediately** (count the dial, do not just spin it).
4. Press **RETURN**. The carriage rapids back to the start stop (STOP_R).
5. **Infeed:** set the cross slide back to the zero, then the next depth. Light cuts near the end (about 0.02-0.05 mm). With the compound at 29.5 degrees, to infeed x advance the compound x / cos(29.5 deg) = 1.15 x.
6. Press **NUT** again.

Rules:

* Do not change pitch, units, MODE, DIR between passes. If you do, or after an E-stop or driver alarm, the sync is lost and **the electronics cannot re-find an existing groove**. Finish a thread without such events, or accept a new thread.
* You may stop the spindle between passes: the phase is kept modulo one spindle revolution. Keep the same rpm for the following passes (the driver's pulse filter and the following lag turn rpm differences into a small phase shift; see WIRING 4.2).
* Press NUT while it is engaged to open early, for example to abort. The tool must be retracted before you do.
* If the carriage reaches the stop while the nut is engaged, it still stops at the stop. **Set the stops with margin.**
* Do not use the lathe's half-nut lever; leave it closed.
* Final passes: two spring passes without infeed, then check with a gauge or nut.

---

## 11. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Fault "E-STOP" straight after power-up | pin 23 open (E-stop NC2 not wired or open) | Wire NC2 to GND; or jumper pin 23 to GND for bench tests |
| Fault "DRIVER ALARM" at power-up | ALM polarity opposite to the firmware | Measure pin 8 healthy; set `ALARM_ACTIVE_LEVEL` to match (WIRING 4.6) |
| Driver red LED blinks 4x | motor not connected / phase wiring | Check P3 and the motor cable |
| Red LED blinks 7x during motion | position following error: acceleration too high, encoder wiring, tension too high | Lower `ACCEL_MM_S2` and `MAX_SPEED_MM_S`; check P2; check the carriage for binding |
| Red LED blinks 2x | over-voltage (supply too high or regeneration) | Check the PSU is 48.0 V; fit the TVS (BOM) |
| Carriage moves the wrong way on JOG | direction inverted | `INVERT_DIR` (or SW5, not both) |
| Carriage moves the wrong way in thread/feed | spindle sign inverted | `INVERT_SPINDLE` or swap A/B |
| Thread pitch off by a constant % | pitch, belt teeth, DIP or `ENCODER_CPR` wrong | Section 8, then check every number in section 5 |
| Pitch right but every pass starts in a different groove | encoder slip, lost counts, mode/pitch touched between passes, spindle rpm changed a lot | Check the spindle hub and belt marks, the encoder shielding, section 10 rules |
| Random extra counts, noisy rpm | encoder noise | Shield grounded at one end only, 1k pull-ups present, cable away from motor leads (WIRING 10) |
| "SPINDLE TOO FAST" | spindle rpm x pitch above 0.9 x `MAX_SPEED_MM_S` | Slow the spindle or choose a finer pitch |
| Motor stalls, buzzes | belt too tight, carriage binding, current low | Check S1, gib screws, tension |
| Motor hot | S1 set too high, no airflow | Reduce S1; the driver wants air |
| Driver "enabled" with the Teensy off | ENA pull-up missing | Fit the 10k to 3V3 (WIRING 2.4) |

# CAD: ELS retrofit for the Roher TBL-20/520 (= Axminster BV20M, 200 x 520 bench lathe)

Native parametric **SolidCraft** designs (SolidCraft 0.40; the app or its `solidcraft-cli`). The change gears and the banjo are removed: a
closed-loop NEMA23 stepper drives the leadscrew through an HTD-3M belt, and an LPD3806-600BM encoder reads the spindle through a GT2 belt off
the old change-gear stud. Every shared number lives in [`params.json`](params.json) (lathe-dependent ones are tagged `MEASURE`); the derived
numbers (belt centres, Z stack, standoff length, encoder height, door windows) are SolidCraft expressions in the same file, so they stay live
in every design that uses them.

```
python3 cad/build.py                # every part + both assemblies, STEP/STL/DXF/PNG, the fit checks (cad/fit_checks.md), the 3D viewers
python3 cad/build.py plate          # only targets whose name contains "plate" (no checks)
python3 cad/build.py --checks       # only the fit checks, on the designs as built
python3 cad/build.py --list         # the targets
```

`build.py` exits 1 on any failing SolidCraft step or fit check. Last run: 39 checks, all PASS.

**How it fits together.** Each part is a Python module in [`parts/`](parts) that writes the part's SolidCraft command script (sketches,
extrudes, holes, patterns...) with expressions over the parameter names; [`lib/sc.py`](lib/sc.py) prepends the parameters the script uses
and `solidcraft-cli` runs it into `designs/<part>.sc`. Open a **part** design in SolidCraft and its parameters table holds those
parameters, live: change one there to try it (sketches are fully constrained, dof 0, and positions are expressions, so the timeline follows),
but make lasting changes in `params.json` and rebuild: a rebuild overwrites the designs, and the other parts and the assemblies only follow
`params.json`. A few choices are made at build time from the values, because SolidCraft expressions have no comparisons: which circles
form an outline's convex hull (so `motor_angle`, which turns the standoff bosses, always needs a rebuild; a native edit that changes the
hull stops with an error rather than a wrong shape), which bezel screw holes have sheet behind them, the options `base_m5` (csk / tap / insert),
`ls_setscrew` and `stud_setscrew`, round bore vs D-flat (`*_shaft_flat` 0) or keyway
(`*_keyway_w` 0), whether a door window (with its bezel and template) and the stud spacer exist, and whether a washer shim goes under
the standoffs; such a change takes a rebuild, which also deletes the outputs of a part that is no longer needed.

The **assemblies** carry no parameter table on purpose: they insert the parts as **linked** components, which keep the shape and place they
were built with, so a parameter edited inside an assembly could never move them. Every position in an assembly is a number written by the
build. To change the layout: edit `params.json`, `python3 cad/build.py`, then reopen the assembly (or `component.update_links` after a
part-only change).

Driving it from an agent: the SolidCraft MCP server runs the same scripts (`batch {"path": "cad/build/scripts/<part>.json"}` into the open
app) and inspects the designs (`measure`, `body_topology`, `check_parameters`, `inspect.clearance`, `joint.sweep`).

## Coordinate frame (used by every file)

Front view of the gear end panel (the photo in `../docs/roher_layout.png`). **Origin = leadscrew shaft axis L** on the face the old change-gear arm
(banjo) sat on; **+X** = right, **+Y** = up, **+Z** = out of the panel towards the gear-compartment door. Z = 0 is the banjo-seat plane (casting face).
Measured XY points (+-2 mm, from a ruler photo): stud S (-75.5, 98.9), spindle (-100.5, 152.7), banjo bolts B1 (16.2, 14.0) / B2 (-22.7, -5.7),
switch box X -119..-51 / Y -84.6..-55.2, panel bottom Y = -92.6, right X = +53.2.

## Structure (how it hangs together)

```
   motor body (81 mm) pokes through a WINDOW in the door + printed bezel                   126.5 front end
   encoder (35 mm) pokes through a second, smaller window                                    73.8 front end
Z  door ------------------------------------------------------------------------------------- 65   (inside of the closed door)
   motor flange face = the "front plate"                                                      45.5
   4 x M5 hex standoff 35 mm + 2.5 mm washer shim = 37.5 mm                  encoder 35 mm  | 38.8 bracket top face
   20T HTD pulley (hub towards the motor) on the 21 mm shaft              C-cup bracket 30.8 mm tall, open towards the stud
   40T pulley 17.66..38.4 on the leadscrew's 16.7 shoulder               60T 22..36.5 on the stud's 16.7 shoulder
   belts: HTD Z 19.4..34.4, GT2 Z 23.4..29.4
   FLAT base plate 8 mm (Z 0..8) on the banjo seat, clamped on B1/B2, slides +-3 mm along Y
   blue panel face = banjo seat (measured: banjo front face 17.66, banjo 17.66 thick)           0
```

| Part | Role |
|---|---|
| **base plate** `designs/base_plate.sc` | FLAT 8 mm plate on the old banjo seat (back face flat against the casting). The 40T does not rest on it: it seats on the leadscrew's own 16.7 mm shoulder at Z 17.66 (measured), 9.7 mm in front of the plate. Clamped by B1/B2 with short countersunk M5 screws in slots +-3 mm along Y: the whole plate (motor + encoder bracket) slides along Y to tension the HTD belt. Clearance slot around the leadscrew boss at L (no pivot). |
| **motor standoffs** (bought) | 4 x M5 hex standoffs (steel, female-female, 8 mm AF) at the 47.14 mm bolt square, M5 countersunk screws from the back of the plate (back stays flat); the motor flange is the front plate. |
| **encoder bracket** `designs/encoder_bracket.sc` | separate printed C-cup bolted to the plate with 2 x M4; open towards the stud so the belt passes; its top face carries the encoder (3 x M3 on the 30 mm PCD + 20 mm pilot recess, slotted +-4 mm along X). |
| stud spacer `designs/stud_spacer.sc` | optional ring on the stud behind the 60T, only if the spindle bearing cap stands out past the stud shoulder (Z 22). Built (and placed in the assembly, the 60T raised by it) only when `stud_spacer` > 0; measured 0, so normally there is no such part. |
| **door windows + bezels** `designs/door_bezel_motor.sc`, `designs/door_bezel_encoder.sc` | the motor sticks out past the closed door, so the door gets a window. The door hinges on its left edge, far from the motor, so near the motor it swings almost straight out: the window is tight on the hinge side (3 mm) and above/below (2 mm), and only the edge **away from the hinge** gets extra room so the door can swing past the motor's back corner (`params.json` `m_swing_x`: that edge must be at least as far from the hinge axis as the motor's outer back corner, + 2 mm; the lathe assembly swings the door through 100 deg to prove it). A printed bezel on the door's outside face trims the cut, stiffens the sheet and carries a brush/foam seal across the gap. The door still closes fully, so the **door switch keeps working**. The encoder (front Z 73.8) also pokes past the 65 mm door, so it gets its own window and bezel (same rule). |

## Layout and speed ratios

| Drive | Pulleys | Belt | Centre | Result |
|---|---|---|---|---|
| Leadscrew | HTD-3M 20T (motor) : **40T** (leadscrew), 15 mm | **3M-207** (69 teeth, 207 mm) | **C_ls = 57.71 mm**, motor axis at (0, -57.71) straight below L | leadscrew = motor / 2 |
| Encoder | GT2 20T (encoder) : **60T** (stud), 6 mm | **GT2-200** (100 teeth, 200 mm loop) | **C_enc = 58.61 mm**, encoder axis E = stud + (58.61, 0) = (-16.89, 98.9) | stud turns at 2/9 spindle speed, x 3 -> **the encoder turns at 2/3 spindle speed** (LPD3806-600BM: 2400 counts/rev quadrature -> 1600 counts per spindle revolution) |

Other stock lengths, same pulleys: 3M-204 -> 56.19 mm, 3M-210 -> 59.23, 3M-213 -> 60.75, 3M-216 -> 62.27; GT2-158 -> 36.77, GT2-240 -> 78.97. 3M-207 was
chosen over the closer-to-60 3M-210 / 3M-213 on purpose: the motor sits low on the panel and the plate may not go below Y = -90.6 (2 mm inside the panel
edge); with 3M-207 the plate bottom is at Y = -88.3 (2.3 mm of downward slide left), with 3M-210 only 0.8 mm. Change `ls_belt_teeth` to try another.

## Files

| File | What |
|---|---|
| `params.json` | every shared dimension (and the derived ones, as expressions): edit here, then `python3 cad/build.py` |
| `build.py` | builds everything (or a filter), writes the scripts to `build/scripts/` (git-ignored), runs the checks and the viewers |
| `parts/pulleys.py` | `pulley_htd3m_40T` (leadscrew), `pulley_htd3m_20T` (printable backup of the bought motor pulley), `pulley_gt2_60T` (stud), `pulley_gt2_20T` (encoder) |
| `parts/base_plate.py` | `base_plate` (+ `dxf/base_plate.dxf`, the section at half thickness) |
| `parts/encoder_bracket.py` | `encoder_bracket` (modelled in place; the STL is turned face down) |
| `parts/spacer.py` | `stud_spacer`, only when `stud_spacer` > 0 |
| `parts/door_bezel.py` | `door_bezel_motor`, `door_bezel_encoder` (+ `dxf/door_window_template_*.dxf`, the cut + holes 1:1), each only when that part pokes past the closed door |
| `parts/control_box.py` | `control_panel`, `control_frame`, `control_lid` (modelled assembled; the STLs are turned to print) |
| `parts/assemblies.py` | `lathe_assembly` (joints, belt links, motion studies, the door hinge) and `control_box_assembly` |
| `lib/sc.py` | parameter evaluation and closure, hull-of-circles sketches (arcs on expression centres + tangent lines, dof 0) |
| `lib/checks.py` | the fit checks: numbers from the parameters + geometry measured on `designs/lathe_assembly.sc` -> `fit_checks.md` |
| `designs/*.sc` | the SolidCraft designs (open them in the app) |
| `step/`, `stl/`, `dxf/`, `png/` | STEP of every design, print-orientation STLs, DXFs, renders (`lathe_assembly_front.png` = the photo view) |
| `viewer/` | `build_viewer.py` (run by `build.py`) -> `assembly_3d.html` and `machine_3d.html` (whole lathe, cable routes, live control box) |

## Part list, print settings, hardware

All parts: PETG or ASA (oil and heat near the lathe), 0.2 mm layers, 5 perimeters, 50-60 % gyroid, 100 % perimeters around bores. STLs are in print orientation; none needs supports.

| Part (STL) | Qty | Orientation | Notes / hardware |
|---|---|---|---|
| `base_plate` | 1 | back face down (flat), no supports | **78.5 x 215.2 x 8 mm** (rib to Z 12); needs a 220 mm bed (or print diagonally). 2 x **M5 countersunk (DIN 7991, 10 mm head)** into B1/B2 (length: old banjo bolt length - 9.66 mm, rounded down) (use washers if the plate is PETG); 4 x **M5 x 16 countersunk** from the back into the standoffs (`base_m5`: `tap` = 4.2 mm holes for male-threaded standoffs, `insert` = 6.4 mm for M5 heat-set inserts). Countersinks open towards the bed, everything else is on the front face. Aluminium: cut `dxf/base_plate.dxf` (below) |
| `encoder_bracket` | 1 | **encoder face down on the bed**, no supports | 57 x 50 x 30.8 mm. 2 x **M4 heat-set inserts** (M4 x 5.7, pressed in from the open base end), 2 x **M4 x 16 countersunk** from the back of the base plate; 3 x **M3 x 10 pan head + washer** from inside the cup into the encoder. Or replace the inserts by nuts in pockets (change `eb_insert_d`) |
| `pulley_htd3m_40T` | 1 | bottom flange down | bore 15 + 4 mm keyway (measured); **4 x 4 key**; seats on the 16.7 mm shoulder, the old gear's M5 end screw + washer clamps the hub face; no set screw (option `ls_setscrew` 1: M4 + nut trap, needs a longer hub than the shaft allows) |
| `pulley_gt2_60T` | 1 | bottom flange down | bore 15 + 4 mm keyway (measured); **4 x 4 key**, seats on the 16.7 mm shoulder, M5 stud-end screw + washer; option `stud_setscrew` 1 (M3 + nut trap) |
| `pulley_htd3m_20T` | 0 or 1 | flange down | **backup only**; real part: bought aluminium 20T HTD-3M, 8 mm bore, 15 mm belt, set screw on the shaft flat. Printable: M4 x 8 set screw + nut |
| `pulley_gt2_20T` | 0 or 1 | flange down | **bought**: GT2 20T, 6 mm bore, 6 mm belt, set screw; printable variant: 6 mm bore + D-flat, M3 x 6 set screw + nut, 12.3 mm long |
| `door_bezel_motor`, `door_bezel_encoder` | 1 each | flat, no supports | frame 12 mm wide x 3 mm round each window, trimmed to the door's right edge and bottom fold; **M3 x 10 + nyloc nuts** through the door, only where there is sheet behind them (4 on the motor bezel, 10 on the encoder bezel). Glue a self-adhesive **brush strip** (or soft foam) round the opening, at least on the far side. `dxf/door_window_template_motor.dxf` / `_encoder.dxf` = the cut + holes, 1:1, centred on the window |
| `control_panel` / `control_frame` / `control_lid` | 1 each | as before | unchanged: panel front face down, frame rear face down, lid outer face down (see the control-box notes in `../docs/`) |

**Motor hardware (bought):** 4 x **M5 hex standoff, female-female, 8 mm AF, 35 mm long** + **2.5 mm washer shim** (M5 washers under each standoff's motor end; the exact
requirement is 37.21 mm: 35 + 2.5 = 37.5), 4 x M5 x 16 countersunk (back of the plate), 4 x M5 x 12 socket head + washer through the motor flange into the standoffs
(check the flange holes are clear holes; if they are tapped use M5 studs). A 40 mm standoff and no shim also works (motor 2.5 mm further out). Belts: 3M-207-15, GT2-200-6.

**Aluminium plate:** `dxf/base_plate.dxf` is the full 2D outline with every through hole, slot and the lightening window, for 6-8 mm aluminium. The countersinks (B1/B2 M5, M5 and M4 on the back),
the 0.5 mm relief under the 40T and the rib are 3D features: machine the countersinks or use button-head screws and washers. With `base_t = 6` the maths recompute: the standoff becomes **40 mm, no shim**
(exact 39.21) and the motor face moves to Z 46; the 40T still seats on the leadscrew shoulder. Aluminium is the recommended final
material: PETG creeps under a big bolt clamp and this is the part that holds the belt tension.

## Installation

1. Isolate the machine. Open the gear door, remove the change gears and the banjo with its clamp bolts B1/B2 (keep the M5 threads clean). Keep the old end screws + washers (leadscrew, stud).
2. **Stud** (S): the 60T with its 4 x 4 key on the stud's shoulder (hub towards the door), end screw + washer. The 60T overlaps the spindle bearing cap in XY by 4.7 mm: the cap is lower than the shoulder (Z 22, confirmed), so no spacer ring.
3. **Base plate**: offer it over the leadscrew boss (the clearance slot) and fit the 2 countersunk M5 screws into B1/B2, nipped up only enough to keep the plate in place (the slots let it slide +-3 mm along Y). Then the **40T** with its 4 x 4 key (hub towards the door) seats on the leadscrew's 16.7 mm shoulder at Z 17.66, clear of the plate; end screw + washer clamp the hub against the shoulder.
4. **Encoder bracket**: on the bench, fit the encoder (3 x M3 + washers, loose in the slots) and the 20T GT2 on its shaft; fit the 2 M4 inserts into the cup's columns if not done. Lay the GT2-200 belt over the 60T and the 20T (the cup is open towards the stud, so it slides in from the side) and screw the bracket to the plate from the back (2 x M4 countersunk).
5. **Motor**: fit the 4 standoffs on the plate from the back (M5 countersunk x 16, thread locker), put the 2.5 mm of washers on each (the shim `fit_checks.md` gives), loop the 15 mm 3M-207 belt over the 40T and the aluminium 20T held under the motor, push the motor shaft through the standoffs' top and into the 20T (hub towards the motor, set screw on the shaft flat; line the teeth with the 40T: belt overlap 15 mm, +-0.75 mm), and bolt the flange to the standoffs.
6. **Tension**: slide the whole base plate **down** (away from L) in the B1/B2 slots until the HTD belt is tight, then tighten the two M5 screws. The panel edge limits downward slide to about 2.3 mm; a 207 mm belt needs well under 1 mm. A Y shift changes the horizontal GT2 centre by under 0.03 mm at 2 mm (0.08 mm at the full +-3 mm), absorbed by the encoder slots. Then slide the encoder **right** (away from the stud) in its +-4 mm slots to tension the GT2 belt, and tighten the M3 screws.
7. **Door window** (the motor sticks out past the door). Cut it with everything installed and the belts tensioned:
   * Put a dab of paint (or lipstick) on the four back corners of the motor and close the door gently until it touches. The marks show where the motor meets the door.
   * Lay the printed bezel on the door's outside face over the marks, with the **wider gap on the side away from the hinge** (that is the swing clearance), and scribe the opening and the hole centres. `dxf/door_window_template_motor.dxf` (and `_encoder.dxf`) is the same outline 1:1 if you prefer paper. Remove the door to cut.
   * Cut with a nibbler, jigsaw (metal blade) or drill + file; deburr. The window's bottom edge is only about 4 mm above the door's bottom fold, so cut gently there (the bezel's bottom bar is trimmed to the fold and carries no screws).
   * Fit the bezel with M3 x 10 + nyloc nuts and glue a brush strip (or soft foam) round the opening, at least on the far side, to keep chips out and fingers away from the belts.
   * **Cables:** nothing may leave the motor or the encoder outside the door, because the door's bottom bar and far edge sweep everything below and beyond the window. Turn the motor so its cable outlet faces the **hinge**; both pigtails (and the encoder lead) go back into the compartment through the window's 14 mm hinge-side cable gap (`door_cable_gap`), then out through 12 mm grommets drilled in the end panel, one lead per grommet: **A1** at about (-40, -82) mm from the leadscrew axis (motor power) and **A2** at (-40, -67) (motor encoder), both down behind the panel and under the door to the electrical box; **B** at about (30, 64) for the encoder lead, which runs up the headstock front face (P-clips) with the signals + 5 V and E-stop cables to the control box. Behind the panel keep the cables in front of the chip tray's end lip. `cad/viewer/machine_3d.html` shows the route.
   * Rehang the door, open and close it slowly while watching the far edge pass the motor's back corner, then check **the door switch still clicks** when closed and the lathe will not start with the door open.

## Measurement checklist (every `MEASURE` in `params.json`)

Use calipers (0.01 mm); XY points from the ruler photo are only +-2 mm: re-measure them on the machine, **especially B1/B2** and the leadscrew boss. "Mate" = check against your actual part before printing.

| Parameter | Default | How to measure |
|---|---|---|
| `stud_x/y`, `spindle_x/y` | (-75.5, 98.9), (-100.5, 152.7) | axis positions relative to L (+X right, +Y up) |
| `bearing_cap_r`, `bearing_cap_z` | 44, 12 | radius of the spindle bearing cap disc; how far it stands off the casting |
| `B1_x/y`, `B2_x/y`, `banjo_bolt_d` | (16.2, 14), (-22.7, -5.7), 5 | centre of each old banjo clamp hole from L; thread size (M5, confirmed) and tap depth |
| `sw_x0/x1`, `sw_y0/y1`, `plunger_x/y` | -119..-51, -84.6..-55.2 | door microswitch box and plunger |
| `panel_bottom_y`, `panel_right_x` | -92.6, 53.2 | lowest and rightmost extent of the end panel |
| `base_t` | 8 | plate thickness. The banjo is 17.66 thick (measured), but nothing seats on the plate, so 8 is enough |
| `ls_boss_d` | 16.7 | **measured**: the leadscrew's 16.7 shoulder runs through the banjo's centre hole (its face is flush with the banjo front face). The plate's clearance slot is this + 1 mm; the web to the B1 countersink is a fit check |
| `ls_seat_z`, `ls_shoulder_d` | 17.66, 16.7 | **measured**: the shoulder the old 100T gear sat on (height from the panel face, diameter) |
| `ls_shaft_free` | 20 | **measured**: shaft end 37.66 - 17.66 |
| `stud_seat_z`, `stud_shaft_free`, `stud_shoulder_d` | 22, 14, 16.7 | **measured**, same for the change-gear stud |
| `door_depth` | **65 (measured)** | panel face (= banjo seat) to the inside of the closed door (decides how far the motor sticks out and the window size) |
| `door_hinge_x`, `door_hinge_z` | -310.4, 0 | the door's hinge axis (X from the leadscrew axis; the photo puts it at the panel's left edge) |
| `door_t` | 1.2 | door sheet thickness |
| `ls_shaft_bore`, `ls_keyway_w`, `ls_keyway_h` | 15, 4, 1.8 | **measured** leadscrew shaft diameter, key width (4.1); hub keyway depth 1.8 = 4 x 4 key |
| `ls_end_screw` | 5 | thread of the screw in the leadscrew end: M5 (tapped hole matches M5 in the photos) |
| `stud_bore`, `stud_keyway_w`, `stud_keyway_h`, `stud_end_screw` | 15, 4, 1.8, 5 | **measured**, same for the stud (4 x 4 key) |
| `motor_pilot_h`, `motor_shaft_len`, `motor_shaft_flat` | 1.6, 21, 0.5 | pilot boss height, shaft length beyond the pilot face, D-cut depth |
| `motor_len` | 81 | length incl. encoder cover (1.2 Nm StepperOnline 23HS22-4004D-E1000, ~81 from a listing: check the datasheet). With the 65 mm door the window stays on the door up to ~95 mm; the 3 Nm motor (113-138) would need a window through the door's right edge and side wall |
| `motor_angle` | 0 | swings the motor from straight below the leadscrew towards the hinge. Tried 15 deg: worse (a turned motor square hits the panel's bottom edge and the switch box; an unturned one puts a standoff on the belt). Change it in `params.json` and rebuild |
| `mp_buy_flange`, `mp_buy_tooth`, `mp_buy_hub` | 1.5, 16.5, 8 | the **bought 20T HTD-3M**: back flange, toothed width, hub length: they decide the standoff length (fit checks) |
| `enc_hole_angle`, `enc_pilot_d`, `enc_pilot_h` | 90, 20, 1.5 | angle of the first M3 hole; pilot boss diameter and height of the LPD3806 |
| bought GT2 20T pulley | -- | overall length: must be <= 12.3 (13 mm shaft), else the bracket height changes (`ep_hub_len`) |
| `cb_depth` | 70 | longest body behind the control panel (E-stop block 55-65) |
| `tft_win_off_x/y`, `tft_holes_x/y`, `tft_stack_h` | [14.2, 3.4], [79, 43], 3.8 | TFT module: window origin from the PCB corner, hole spacing, glass height |
| `led_hole`, `perf_holes_x/y`, `magnet_d`, `magnet_h` | 8.2, [54, 44], 20.3, 3.2 | LED holder hole, perfboard holes, magnet + 0.3 mm |

## Fit checks at the defaults ([`fit_checks.md`](fit_checks.md), written by every full build)

Two layers. The **numbers** are the checks the old OpenSCAD assembly echoed, computed from the parameters (identical results): belt centres and
stock lengths, the Z stack, belt-on-teeth overlaps (15 / 15 mm HTD, 6 / 6 mm GT2), the standoff (exact 37.21 mm -> **35 mm + 2.5 mm shim**,
motor face Z 45.5), shaft engagements, the door windows (motor 92.95 x 61 mm, encoder 58.95 x 42 mm, sheet left to the door edges, swing
radii), the switch plunger, the plate's panel margins and Y slide, the webs between the slots. One more ties the CAD to the controller:
`firmware/include/lathe_config.h` must match the drive (`ENCODER_TURNS`/`SPINDLE_TURNS` = stud ratio x stud teeth / encoder teeth,
`MOTOR_PULLEY_TEETH`/`LEADSCREW_PULLEY_TEETH`, `ENCODER_CPR` = 4 x `enc_ppr`): change a pulley in `params.json` and the build FAILs,
naming the firmware values to set, until the firmware says the same. The **geometry** is measured by SolidCraft on
`designs/lathe_assembly.sc`:

| Check | Result |
|---|---|
| no part overlaps another at rest (besides the screws in their threads) | PASS |
| plate vs door switch box / vs spindle bearing cap | 19.28 / 15.63 mm (>= 2 / 3) |
| encoder bracket vs 60T stud pulley / vs GT2 belt | 11.23 / 5.40 mm (>= 3 / 2) |
| standoffs vs HTD belt / vs 40T pulley | 4.87 / 17.15 mm (>= 2) |
| motor flange + pilot vs 40T pulley and belt | 9.54 mm |
| closed door vs motor / encoder (window gaps) | 2.00 / 2.00 mm |
| **door swung 0..100 deg** (joint.sweep, door + both bezels vs motor and encoder) | no contact; closest 1.97 mm, door to motor at 10.2 deg (the 2 mm swing margin) |
| belt links driven through the joints | motor 360 deg -> leadscrew 180 deg; stud 120 deg -> encoder 360 deg |

## Assumptions to check

* **Leadscrew seat**: the 40T seats on the 16.7 mm shoulder at Z 17.66 (measured; it turns with the leadscrew), clamped against it by the end screw + washer like the old gear.
* **B1 / B2 vs the 40T**: they are only 21-23 mm from L; the countersunk heads are flush with the plate front, so nothing rigid stands up into the pulley or the belt.
* The bought 20T HTD pulley is assumed 1.5 + 16.5 + 8 mm (flange, teeth, hub): MEASURE it, the standoff length follows (`mp_buy_*`).
* Motor flange holes are assumed to be clear holes (M5 screws from the motor side into the standoffs) and the encoder's M3 holes tapped; check both.
* PETG base plate: a prototype / fit check. It holds belt tension and motor torque through two M5 clamps in slots; use 6-8 mm aluminium for the final part.
* The motor is cantilevered 81 mm on 35 mm standoffs (+ 2.5 mm shim): tighten all four, thread locker.

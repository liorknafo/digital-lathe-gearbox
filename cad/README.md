# CAD: ELS retrofit for the Roher TBL-20/520 (= Axminster BV20M, 200 x 520 bench lathe)

Parametric OpenSCAD (needs a build with `--backend=manifold`; tested with 2026.10.11). The change gears and the banjo are removed: a closed-loop
NEMA23 stepper drives the leadscrew through an HTD-3M belt, and an LPD3806-600BM encoder reads the spindle through a GT2 belt off the old
change-gear stud. Every lathe-dependent number lives in [`params.scad`](params.scad) and is tagged `// MEASURE`; derived numbers (belt centres, Z stack,
motor standoff length, encoder height) are computed in [`lib/layout.scad`](lib/layout.scad) and reported by [`assembly.scad`](assembly.scad).

```
./build.sh            # everything -> stl/, png/, dxf/base_plate.dxf, logs/ (fit checks in logs/assembly.echo)
./build.sh plate      # only outputs whose name contains "plate"
```

`build.sh` fails (exit 1) on any OpenSCAD WARNING/ERROR or non-manifold status; last run: clean. It prints every fit check (PASS/FAIL, see below).

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
| **base plate** `base_plate.scad` | FLAT 8 mm plate on the old banjo seat (back face flat against the casting). The 40T does not rest on it: it seats on the leadscrew's own 16.7 mm shoulder at Z 17.66 (measured), 9.7 mm in front of the plate. Clamped by B1/B2 with short countersunk M5 screws in slots +-3 mm along Y: the whole plate (motor + encoder bracket) slides along Y to tension the HTD belt. Clearance slot around the leadscrew boss at L (no pivot). |
| **motor standoffs** (bought) | 4 x M5 hex standoffs (steel, female-female, 8 mm AF) at the 47.14 mm bolt square, M5 countersunk screws from the back of the plate (back stays flat); the motor flange is the front plate. |
| **encoder bracket** `encoder_bracket.scad` | separate printed C-cup bolted to the plate with 2 x M4; open towards the stud so the belt passes; its top face carries the encoder (3 x M3 on the 30 mm PCD + 20 mm pilot recess, slotted +-4 mm along X). |
| `spacer.scad` | optional ring on the stud behind the 60T, only if the spindle bearing cap stands out past the stud shoulder (Z 22). Off by default (`stud_spacer = 0`). |
| **door window + bezel** `door_bezel.scad` | the motor sticks out past the closed door, so the door gets a window. The door hinges on its left edge, far from the motor, so near the motor it swings almost straight out: the window is tight on the hinge side (3 mm) and above/below (2 mm), and only the edge **away from the hinge** gets extra room so the door can swing past the motor's back corner (`lib/layout.scad`: that edge must be at least as far from the hinge axis as the motor's outer back corner, + 2 mm). A printed bezel on the door's outside face trims the cut, stiffens the sheet and carries a brush/foam seal across the gap. The door still closes fully, so the **door switch keeps working**. If the door is shallower than the encoder (65.8 mm), the encoder gets a window too (same rule; the checks say so). |

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
| `params.scad` | every shared dimension; edit here (control-box params unchanged) |
| `lib/layout.scad` | derived layout: C_ls, C_enc, E, Z stack, standoff length + shim, encoder face height, belt overlaps |
| `base_plate.scad` | the flat base plate. `mode="print"` (default), `"dxf"` |
| `encoder_bracket.scad` | the encoder C-cup. `mode="print"` (face down, default), `"lathe"` |
| `spacer.scad` | `stud_collar` ring |
| `pulley_htd3m.scad` | `40T` leadscrew pulley (default), printable `20T` motor pulley (backup) |
| `pulley_gt2.scad` | `60T` stud pulley (default), printable `20T` encoder pulley |
| `control_box.scad` | `panel`, `frame`, `lid` (+ `all` exploded preview): unchanged |
| `assembly.scad` | layout, belts, **all fit checks**; `view="iso"` / `"front"` (along -Z) / `"side"` / `"side_motor"` / `"side_enc"` |
| `lib/belt.scad`, `lib/teeth.scad`, `lib/pulley_core.scad`, `lib/common.scad` | belt maths + stock lists, tooth profiles, generic pulley, helpers |

Removed: `drive_plate.scad` (the cantilevered plate on printed L-feet), the L-shaped spacers, the leadscrew collar, and everything from the 9x20 design.

## Part list, print settings, hardware

All parts: PETG or ASA (oil and heat near the lathe), 0.2 mm layers, 5 perimeters, 50-60 % gyroid, 100 % perimeters around bores. STLs are in print orientation; none needs supports.

| Part (STL) | Qty | Orientation | Notes / hardware |
|---|---|---|---|
| `base_plate` | 1 | back face down (flat), no supports | **78.5 x 215.2 x 8 mm** (rib to Z 12); needs a 220 mm bed (or print diagonally). 2 x **M5 countersunk (DIN 7991, 10 mm head)** into B1/B2 (length: old banjo bolt length - 9.66 mm, rounded down) (use washers if the plate is PETG); 4 x **M5 x 16 countersunk** from the back into the standoffs. Countersinks open towards the bed, everything else is on the front face. Aluminium: cut `dxf/base_plate.dxf` (below) |
| `encoder_bracket` | 1 | **encoder face down on the bed**, no supports | 57 x 50 x 22.8 mm. 2 x **M4 heat-set inserts** (M4 x 5.7, pressed in from the open base end), 2 x **M4 x 16 countersunk** from the back of the base plate; 3 x **M3 x 10 pan head + washer** from inside the cup into the encoder. Or replace the inserts by nuts in pockets (change `eb_insert_d`) |
| `pulley_htd3m_40T` | 1 | bottom flange down | bore 15 + 4 mm keyway (measured); **4 x 4 key**; seats on the 16.7 mm shoulder, the old gear's M5 end screw + washer clamps the hub face; no set screw (option `ls_setscrew`: M4 + nut) |
| `pulley_gt2_60T` | 1 | bottom flange down | bore 15 + 4 mm keyway (measured); **4 x 4 key**, seats on the 16.7 mm shoulder, M5 stud-end screw + washer; option `stud_setscrew` |
| `pulley_htd3m_20T` | 0 or 1 | flange down | **backup only**; real part: bought aluminium 20T HTD-3M, 8 mm bore, 15 mm belt, set screw on the shaft flat. Printable: M4 x 8 set screw + nut |
| `pulley_gt2_20T` | 0 or 1 | flange down | **bought**: GT2 20T, 6 mm bore, 6 mm belt, set screw; printable variant: 6 mm bore + D-flat, M3 x 6 set screw + nut, 12.3 mm long |
| `door_bezel` | 1 (2 if the encoder pokes through too: `which="encoder"`) | flat, no supports | frame 12 mm wide x 3 mm round the window, trimmed to the door's right edge and bottom fold; **M3 x 10 + nyloc nuts** through the door, only where there is sheet behind them (7 at the defaults). Glue a self-adhesive **brush strip** (or soft foam) round the opening, at least on the far side. `dxf/door_window_template.dxf` = the cut + holes, 1:1 |
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
5. **Motor**: fit the 4 standoffs on the plate from the back (M5 countersunk x 16, thread locker), put the 3 mm of washers on them, loop the 15 mm 3M-207 belt over the 40T and the aluminium 20T held under the motor, push the motor shaft through the standoffs' top and into the 20T (hub towards the motor, set screw on the shaft flat; line the teeth with the 40T: belt overlap 15 mm, +-0.75 mm), and bolt the flange to the standoffs.
6. **Tension**: slide the whole base plate **down** (away from L) in the B1/B2 slots until the HTD belt is tight, then tighten the two M5 screws. The panel edge limits downward slide to about 2.3 mm; a 207 mm belt needs well under 1 mm. A Y shift changes the horizontal GT2 centre by under 0.03 mm at 2 mm (0.08 mm at the full +-3 mm), absorbed by the encoder slots. Then slide the encoder **right** (away from the stud) in its +-4 mm slots to tension the GT2 belt, and tighten the M3 screws.
7. **Door window** (the motor sticks out past the door). Cut it with everything installed and the belts tensioned:
   * Put a dab of paint (or lipstick) on the four back corners of the motor and close the door gently until it touches. The marks show where the motor meets the door.
   * Lay the printed bezel on the door's outside face over the marks, with the **wider gap on the side away from the hinge** (that is the swing clearance), and scribe the opening and the hole centres. `dxf/door_window_template.dxf` is the same outline 1:1 if you prefer paper. Remove the door to cut.
   * Cut with a nibbler, jigsaw (metal blade) or drill + file; deburr. The window's bottom edge is only about 4 mm above the door's bottom fold, so cut gently there (the bezel's bottom bar is trimmed to the fold and carries no screws).
   * Fit the bezel with M3 x 10 + nyloc nuts and glue a brush strip (or soft foam) round the opening, at least on the far side, to keep chips out and fingers away from the belts.
   * **Cables:** nothing may leave the motor or the encoder outside the door, because the door's bottom bar and far edge sweep everything below and beyond the window. Turn the motor so its cable outlet faces the **hinge**; both pigtails (and the encoder lead) go back into the compartment through the window's 14 mm hinge-side cable gap (`door_cable_gap`), then out through 12 mm grommets drilled in the end panel, one lead per grommet: **A1** at about (-40, -82) mm from the leadscrew axis (motor power) and **A2** at (-40, -67) (motor encoder), both down behind the panel and under the door to the electrical box; **B** at about (30, 64) for the encoder lead, which runs up the headstock front face (P-clips) with the signals + 5 V and E-stop cables to the control box. Behind the panel keep the cables in front of the chip tray's end lip. `cad/viewer/machine_3d.html` shows the route.
   * Rehang the door, open and close it slowly while watching the far edge pass the motor's back corner, then check **the door switch still clicks** when closed and the lathe will not start with the door open.

## Measurement checklist (every `// MEASURE` in `params.scad`)

Use calipers (0.01 mm); XY points from the ruler photo are only +-2 mm: re-measure them on the machine, **especially B1/B2** and the leadscrew boss. "Mate" = check against your actual part before printing.

| Parameter | Default | How to measure |
|---|---|---|
| `stud_S`, `spindle_xy` | (-75.5, 98.9), (-100.5, 152.7) | axis positions relative to L (+X right, +Y up) |
| `bearing_cap_r`, `bearing_cap_z` | 44, 12 | radius of the spindle bearing cap disc; how far it stands off the casting |
| `banjo_B1`, `banjo_B2`, `banjo_bolt_d` | (16.2, 14), (-22.7, -5.7), 5 | centre of each old banjo clamp hole from L; thread size (M5, confirmed) and tap depth |
| `sw_x`, `sw_y`, `sw_plunger` | -119..-51, -84.6..-55.2 | door microswitch box and plunger |
| `panel_bottom_y`, `panel_right_x` | -92.6, 53.2 | lowest and rightmost extent of the end panel |
| `base_t` | 8 | plate thickness. The banjo is 17.66 thick (measured), but nothing seats on the plate, so 8 is enough |
| `ls_boss_d` | 16.7 | **measured**: the leadscrew's 16.7 shoulder runs through the banjo's centre hole (its face is flush with the banjo front face). The plate's clearance slot is this + 1 mm; the web to the B1 countersink is echoed |
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
| `motor_angle` | 0 | swings the motor from straight below the leadscrew towards the hinge. Tried 15 deg: worse (a turned motor square hits the panel's bottom edge and the switch box; an unturned one puts a standoff on the belt) |
| `mp_buy_flange`, `mp_buy_tooth`, `mp_buy_hub` | 1.5, 16.5, 8 | the **bought 20T HTD-3M**: back flange, toothed width, hub length: they decide the standoff length (echoed) |
| `enc_hole_angle`, `enc_pilot_d`, `enc_pilot_h` | 90, 20, 1.5 | angle of the first M3 hole; pilot boss diameter and height of the LPD3806 |
| bought GT2 20T pulley | -- | overall length: must be <= 12.3 (13 mm shaft), else the bracket height changes (`ep_hub_len`) |
| `cb_depth` | 70 | longest body behind the control panel (E-stop block 55-65) |
| `tft_win_off`, `tft_holes`, `tft_stack_h` | [14.2, 3.4], [79, 43], 3.8 | TFT module: window origin from the PCB corner, hole spacing, glass height |
| `led_hole`, `perf_holes`, `magnet_d`, `magnet_h` | 8.2, [54, 44], 20.3, 3.2 | LED holder hole, perfboard holes, magnet + 0.3 mm |

## Fit checks at the defaults (`assembly.scad`, echoed in `logs/assembly.echo`)

| Check | Result |
|---|---|
| **Motor standoff**: exact 37.21 mm (hub end Z 43.11 + 0.5 gap + 1.6 pilot - 8) | **M5 hex standoff 35 mm + 2.5 mm washer shim = 37.5 mm**; motor flange face Z 45.5 |
| belt overlap, 15 mm HTD belt vs 40T teeth / vs 20T teeth | PASS: **15 mm / 15 mm** (slack +-0.5 / +-0.75 mm) |
| motor shaft: tip Z 22.9; 20T bore on the shaft 20.21 of 26 mm; hub end to motor pilot face 0.79 mm | PASS |
| standoff clearance to the HTD belt strands / to the 40T flange | PASS: 2.96 mm / 16.65 mm |
| motor flange (Z 45.5) above the 40T stack (Z 38.36) | PASS (7.1 mm); belts 11.1 mm below the flange |
| **Encoder**: bracket top (encoder face) Z 38.8, bracket 30.8 mm tall; 13 mm shaft tip Z 24.1, 10.2 of the 12.3 mm 20T bore on the shaft | PASS |
| belt overlap, 6 mm GT2 belt vs 60T teeth / vs 20T teeth | PASS: **6 mm / 6 mm** (teeth bands both Z 23..29.8) |
| bracket walls to the GT2 belt strands (over the +-4 mm slide) / belt top edge to the top plate underside | PASS: 5.41 mm / 5.4 mm |
| 60T stud pulley back face Z 22 > bearing_cap_z 12 (placeholder) | PASS (10 mm, no ring); the 60T overlaps the cap in XY by 4.7 mm, the cap is below Z 22 (confirmed) |
| belts clear the plate (HTD back edge Z 19.4 vs plate front 8; GT2 back edge Z 23.4 vs rib top Z 12) | PASS (11.4 / 11.4 mm) |
| motor front Z 126.5 vs the measured 65 mm door: pokes **61.5 mm** through a **79 x 61 mm window** (X -31.5..47.5, Y -88.2..-27.2), far-side gap 19 mm | info (the window is intended) |
| motor window: sheet left to the door's bottom fold 4.4 mm, to the right edge 5.75 mm | PASS (>= 3). A motor over ~95 mm runs the window off the door's right edge (FAIL) |
| door swing: far window edge radius from the hinge axis >= motor's outer back corner radius (+2 mm) | PASS (also checked by a numerical sweep of the swing, 0-100 deg: closest pass 2.0 mm at door depths 50-110 and motor lengths 80-130) |
| encoder front Z 73.8 (the stud shoulder is at Z 22) vs door 65 | **pokes 8.8 mm through a 45 x 42 mm encoder window** (swing check PASS) |
| door switch plunger outside the motor window | PASS: the door closes fully, the switch still works |
| plate bottom Y = -88.28 >= -90.6; right edge X = 30.57 <= 51.2; plate 78.5 x 215.2 mm | PASS |
| plate vs switch box / bearing cap disc (r 44 + 3) / stud pulley (r 20 + 3) | PASS: 19.3 / 14.6 / 7.6 mm clear |
| Y slide: downward limit by the panel margin | 2.32 mm; motor flange at -5 mm would be at Y = -91.2 (inside the panel edge, outside the 2 mm margin: use <= 2 mm) |
| Y slide -> horizontal GT2 centre change sqrt(C^2 + d^2) - C | 0.08 mm at the full +-3 mm, 0.03 mm at 2 mm, 0.01 mm at 1 mm: **PASS (< 0.2 mm)** |
| web between the L slot and B1 / B2 slots; at the countersinks | PASS: 5.72 / 10.35 mm; 3.02 / 7.65 mm at the M5 countersinks (`ls_boss_d` 16.7, measured) |

## Assumptions to check

* **Leadscrew seat**: the 40T seats on the 16.7 mm shoulder at Z 17.66 (measured; it turns with the leadscrew), clamped against it by the end screw + washer like the old gear.
* **B1 / B2 vs the 40T**: they are only 21-23 mm from L; the countersunk heads are flush with the plate front, so nothing rigid stands up into the pulley or the belt.
* The bought 20T HTD pulley is assumed 1.5 + 16.5 + 8 mm (flange, teeth, hub): MEASURE it, the standoff length follows (`mp_buy_*`).
* Motor flange holes are assumed to be clear holes (M5 screws from the motor side into the standoffs) and the encoder's M3 holes tapped; check both.
* PETG base plate: a prototype / fit check. It holds belt tension and motor torque through two M5 clamps in slots; use 6-8 mm aluminium for the final part.
* The motor is cantilevered 80 mm on 28 mm standoffs: tighten all four, thread locker.

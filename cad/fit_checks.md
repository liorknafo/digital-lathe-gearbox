# Fit checks

Written by `python3 cad/build.py` from cad/params.json and the SolidCraft designs (cad/lib/checks.py). Do not edit.


## belts

| check | result |
|---|---|
| leadscrew: HTD-3M 20T/40T, stock 3M-207 (69 teeth): C_ls = 57.71 mm, motor axis at (0.00, -57.71); leadscrew = motor x 0.5 | info |
| other HTD-3M stock lengths: 3M-201 -> 54.66, 3M-204 -> 56.19, 3M-207 -> 57.71, 3M-210 -> 59.23, 3M-213 -> 60.75, 3M-216 -> 62.27 | info |
| encoder: GT2 60T/20T, stock 200 mm loop: C_enc = 58.61 mm, E = (-16.89, 98.90); encoder = stud ratio 2/9 x 60/20 = 2/3 spindle (1600 counts per spindle turn) | info |
| firmware/include/lathe_config.h matches the drive: ENCODER_TURNS/SPINDLE_TURNS 2/3 (need 2/3), MOTOR_PULLEY_TEETH/LEADSCREW_PULLEY_TEETH 20/40 (need 20/40), ENCODER_CPR 2400 (need 2400) | PASS |
| other GT2 loops: 158 -> 36.77, 200 -> 58.61, 240 -> 78.97 | info |

## Z stack

| check | result |
|---|---|
| 40T back face Z 17.66 vs plate front 8.0: 9.66 mm open (+ 0.5 relief) | PASS |
| 40T Z 17.66..38.36 (hub 2.00, belt centre 26.86); face 0.70 mm proud of the shaft end (washer clamps the hub) | PASS |
| 60T Z 22.00..36.50 (hub 5.50, belt centre 26.40), back face above bearing_cap_z 12.0 | PASS |
| 60T hub (r 13.25) inside the free radius 15.32 before the cap disc; the 60T overlaps the cap in XY by 4.72 mm (cap is below Z 22.0) | PASS |
| belts clear the plate: HTD back edge Z 19.36 (11.36 above the plate), GT2 back edge Z 23.40 (11.40 above the rib) | PASS |

## motor

| check | result |
|---|---|
| bought 20T HTD Z 17.11..43.11, teeth centred on the 40T belt band; belt on the 40T teeth 15.00, on the 20T teeth 15.00 (belt 15) | PASS |
| STANDOFF: exact 37.21 mm -> M5 hex standoff 35 mm + 2.5 mm washer shim; motor flange face Z 45.50 | PASS |
| motor shaft tip Z 22.90: 20.21 of the 26.00 mm pulley bore on the shaft, hub end to pilot face 0.79 | PASS |
| motor flange Z 45.50 above the 40T stack front Z 38.36 by 7.14 | PASS |

## encoder

| check | result |
|---|---|
| 20T GT2 Z 22.00..34.30; belt on the 60T teeth 6.00, on the 20T teeth 6.00 (belt 6) | PASS |
| encoder face (bracket top) Z 38.80, bracket 30.80 tall; shaft tip Z 24.10, 10.20 of 12.30 mm bore on the shaft | PASS |
| bracket wall ends (X -44.89) to the GT2 strands over the +-4 mm slide: 5.41 mm; belt top Z 29.40 to the top plate underside: 5.40 mm | PASS |

## door

| check | result |
|---|---|
| motor pokes 61.50 mm past the door: window 92.95 x 61.00 at X -45.50..47.45, Y -88.21..-27.21; far-side gap 18.95 | info |
| motor window: sheet left to the bottom fold 4.39, to the right edge 5.75 (>= 3) | PASS |
| motor window: far edge radius from the hinge 363.71 >= outer back corner radius 361.74 | PASS |
| encoder pokes 8.80 mm past the door: window 58.95 x 42.00 at X -52.89..6.06, Y 77.90..119.90; far-side gap 3.95 | info |
| encoder window: sheet left to the bottom fold 170.50, to the right edge 47.14 (>= 3) | PASS |
| encoder window: far edge radius from the hinge 323.07 >= outer back corner radius 321.11 | PASS |
| door switch plunger (-108.6, -68.6) outside the motor window: the door closes fully, the switch still works | PASS |

## XY keep-outs and the Y slide

| check | result |
|---|---|
| plate bottom Y -88.28 >= -90.60, right edge X 30.57 <= 51.20 | PASS |
| Y slide +-3: down (tension) limited by the panel margin to 2.32 mm; motor flange bottom -86.21 nominal, -89.21 at -3 (panel edge -92.6) | PASS |
| a Y slide changes the horizontal GT2 centre by 0.08 at +-3, 0.03 at 2, 0.01 at 1 mm (< 0.2, the +-4 slots absorb it) | PASS |
| motor flange left X -28.50 right of the switch box X -51.0 by 22.50 | PASS |
| plate (XY) vs the 60T flange (r 20.04 + 3): 7.56 mm | PASS |
| web L slot to B1 / B2 slots: 6.22 / 10.85 mm; at the countersinks 4.02 / 8.65 mm | PASS |
| B1/B2 countersunk heads flush with the plate front Z 8.0; 40T back face Z 17.66 | PASS |

## geometry (SolidCraft, lathe_assembly.sc)

| check | result |
|---|---|
| no part overlaps another at rest: none (besides 6 screws in their threads) | PASS |
| plate vs door switch box: 19.28 mm (>= 2) | PASS |
| plate vs spindle bearing cap: 15.63 mm (>= 3) | PASS |
| encoder bracket vs 60T stud pulley: 11.23 mm (>= 3) | PASS |
| standoffs vs HTD belt: 4.87 mm (>= 2) | PASS |
| standoffs vs 40T pulley: 17.15 mm (>= 2) | PASS |
| encoder bracket vs GT2 belt: 5.40 mm (>= 2) | PASS |
| motor flange + pilot vs 40T pulley: 9.54 mm (>= 0.5) | PASS |
| closed door vs motor (window): 2.00 mm (>= 2) | PASS |
| closed door vs encoder (window): 2.00 mm (>= 2) | PASS |
| 40T pulley vs base plate: 7.59 mm (>= 0.5) | PASS |
| 60T / 20T GT2 vs base plate: 14.00 mm (>= 1) | PASS |
| door swung 0..100 deg past the motor and encoder: reached 100.00 deg without touching; closest 1.97 mm (Door:1 to Motor:1 at 10.17 deg); gaps on meshes, within 0.47 mm | PASS |
| belt links: motor 360 deg -> leadscrew 180.00 deg (expected 180.00, 20T:40T); stud 120 deg -> encoder 360.00 deg (expected 360.00, 60T:20T) | PASS |

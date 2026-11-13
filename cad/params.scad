// params.scad -- shared parameters for the ELS retrofit parts, Roher TBL-20/520 (= Axminster BV20M, 200 x 520 bench lathe).
//
// Every lathe-dependent dimension is marked  // MEASURE  (cad/README.md explains how to measure each one).
// Edit values here; all part files `include <params.scad>`; derived numbers (belt centres, Z stack, plate_z ...)
// are computed in lib/layout.scad and reported by assembly.scad.
//
// COORDINATE FRAME (everywhere): front view of the gear end panel.
//   origin = leadscrew shaft axis L, on the face the old change-gear arm (banjo) sat on
//   +X = right in the photo (docs/roher_layout.png), +Y = up, +Z = out of the panel towards the gear-compartment door.
//   Z = 0 is the banjo-seat plane (casting face). Measured 2026-10-31: it is level with the blue panel face (banjo front face 17.66 above the
//   panel, banjo 17.66 thick), so every height in docs/measure_form.html (from the panel face) is a Z here directly.

// ============================================================ general ====
$fa = 3;              // facet angle
$fs = 0.35;           // facet size (mm)
$coarse = false;     // true = fewer facets on teeth/flanges, display only (viewer/build_viewer.py); never for printing
tol = 0.15;           // generic FDM clearance added to fits (mm)
use_inserts = true;   // true: M3 holes sized for heat-set inserts (M3 x 5.7, as in docs/BOM.md); false: self-tapping pilot holes
m3_hole  = use_inserts ? 4.2 : 2.7;   // M3 pilot / insert hole
m25_hole = 2.2;                       // M2.5 self-tapping pilot (perfboard standoffs; no M2.5 inserts in the BOM)
m3_clear = 3.4;       // M3 clearance hole
m5_clear = 5.4;       // M5 clearance hole


// ================================================ lathe geometry (XY) ====
// Measured from a ruler photo, accurate to about +-2 mm.
lathe_L         = [0, 0];            // leadscrew shaft axis (origin)
stud_S          = [-75.5, 98.9];     // MEASURE: change-gear stud axis (turns at 2/9 spindle speed)
spindle_xy      = [-100.5, 152.7];   // MEASURE: spindle axis
bearing_cap_r   = 44;                // MEASURE: radius of the spindle bearing cap disc (mm)
bearing_cap_clear = 3;               // keep the drive plate this far outside the cap disc (mm)
banjo_B1        = [16.2, 14.0];      // MEASURE: old banjo clamp bolt 1 (threaded hole in the casting)
banjo_B2        = [-22.7, -5.7];     // MEASURE: old banjo clamp bolt 2
banjo_bolt_d    = 5;                 // thread size of B1/B2: M5 (user, 2026-10-31; matches the ~8-9 mm hex in the photo)
sw_x            = [-119, -51];       // MEASURE: door microswitch box, X range (keep-out)
sw_y            = [-84.6, -55.2];    // MEASURE: door microswitch box, Y range (keep-out)
sw_plunger      = [-108.6, -68.6];   // door plunger position (the door must still reach it)
panel_bottom_y  = -92.6;             // MEASURE: bottom edge of the end panel
panel_right_x   = 53.2;              // MEASURE: right edge of the end panel
panel_margin    = 2;                 // stay this far inside the panel edges (mm)

// ================================================ depth (Z) stack ====
// All Z values are measured from the banjo-seat plane (casting face, Z = 0), positive towards the door.
ls_seat_z       = 17.66;  // measured (L4): front face of the 16.7 mm shoulder the old 100T gear sat against. It turns with the leadscrew (user,
                          //          2026-10-31), so the 40T is clamped against it by the end screw + washer, like the old gear
ls_shaft_free   = 20;     // measured: shaft end Z 37.66 (L5) - shoulder face 17.66 = free shaft for the pulley + washer (mm)
ls_shoulder_d   = 16.7;   // measured (L3): that shoulder's diameter
stud_seat_z     = 22;     // measured (S3): face the 21T gear sat against
stud_shaft_free = 14;     // measured: stud end Z 36 (S4) - 22
stud_shoulder_d = 16.7;   // measured (S5)
stud_spacer     = 0;      // spacer ring on the stud behind the 60T pulley (spacer.scad): only needed if the spindle bearing cap stands out past
                          //          stud_seat_z (the 60T overlaps the cap by ~5 mm in the front view). 0 = none; build.sh then skips the ring
shaft_recess    = 0.5;    // the shaft end stays this far BEHIND the pulley's front face, so the end screw + washer clamp the hub
bearing_cap_z   = 12;     // spindle bearing cap height above the panel face: placeholder. The user confirmed it is below stud_seat_z (22), which is all that matters
door_depth      = 65;     // measured 65 (user, 2026-10-31): panel face (= banjo-seat plane) to the inside of the CLOSED door (confirmed)
door_clear      = 3;      // required gap between anything and the door (mm)
// Whatever pokes past the door (the motor; the encoder too if the door is shallow) goes through a WINDOW cut in the door.
// The door hinges on its LEFT edge, far from the motor, so near the motor it swings almost straight out. Only the window
// edge away from the hinge needs extra room (layout.scad computes it). Cut the window AFTER the belts are tensioned, from
// marks taken on the installed motor; the printed bezel (door_bezel.scad) is the cutting template and the trim.
door_hinge_x    = -310.4;  // MEASURE: X of the door's hinge axis (from the photo: the panel's left edge)
door_hinge_z    = 0;       // MEASURE: Z of the hinge axis (0 = panel plane)
door_t          = 1.2;     // MEASURE: door sheet thickness
door_cut_clear  = 3;       // window gap on the hinge side (mm)
door_cable_gap  = 14;      // EXTRA gap on the hinge side of each window, for the cables. Outside the closed door a cable would sit in the door's
                           //          swing (the bottom bar and the far edge sweep everything below and beyond the window), so the motor's two
                           //          pigtails (outlet turned towards the hinge) and the encoder lead go back INTO the compartment through this gap
                           //          and leave through grommets in the end panel. Everything inside the window band is passed by the opening door
door_cut_clear_y = 2;      // window gap above and below (mm): small, the window sits close to the door's bottom fold
door_swing_margin = 2;     // extra gap on the far side, beyond what the swing needs (mm)
bezel_w         = 12;      // printed bezel: frame width around the window (mm)
bezel_t         = 3;       // bezel thickness (sits on the door's outside face)
bezel_r         = 4;       // bezel outer corner radius
bezel_holes     = 6;       // M3 screws + nyloc nuts through the door (4 corners + 2 mid-sides)

// ======================================================= belts / drives ====
// --- Leadscrew drive: HTD-3M, 15 mm wide, 20T motor : 40T leadscrew pulley (2:1) ---
ls_teeth_motor = 20;
ls_teeth_screw = 40;
ls_pitch       = 3;       // HTD 3M pitch (mm)
ls_belt_w      = 15;      // belt width (mm)
motor_angle    = 0;       // deg: swings the motor shaft from straight below the leadscrew towards the hinge (-X); its square turns
                          //          with the belt. Checked 2026-10-31: any angle is worse here (a turned square hits the panel's bottom edge
                          //          and the switch box; an unturned one puts a standoff on the belt), so keep 0 and use a short motor.
ls_belt_teeth  = 69;      // stock belt 3M-207 (69 teeth; HTD-3M lengths come in 3 mm steps) -> motor centre C_ls = 57.71 mm (derived in lib/layout.scad).
                          // 3M-210 (59.23 mm) and 3M-213 (60.75 mm) are closer to 60 mm, but then the lowest motor slot leaves only ~1 mm of plate above
                          // the panel-edge limit (the plate may not go below panel_bottom_y + panel_margin) and full +-4 mm slot travel runs off the panel.
// --- Encoder drive: GT2, 6 mm wide, 60T stud : 20T encoder (stud 2/9 spindle x 3 = encoder at 2/3 spindle speed, 1600 counts/rev) ---
enc_teeth_stud    = 60;
enc_teeth_encoder = 20;
enc_pitch         = 2;    // GT2 pitch (mm)
enc_belt_w        = 6;
enc_belt_len      = 200;  // stock GT2 closed loop (mm) -> C_enc = 58.61 mm; encoder shaft E = stud + [C_enc, 0]

// Leadscrew pulley (40T HTD-3M)
ls_shaft_bore  = 15;      // measured (L1, caliper): leadscrew shaft diameter
ls_keyway_w    = 4;       // measured 4.1 (L2): a 4 mm key; the slot gets 2 x tol on top. 0 = no keyway
ls_keyway_h    = 1.8;     // keyway depth in the HUB beyond the bore (mm); 1.8 fits a 4 x 4 key (DIN 6885 hub depth)
ls_end_screw   = 5;       // thread of the screw in the leadscrew end: M5 (tapped hole 3.9-4.3 mm in the photos = M5 minor diameter)
ls_setscrew    = false;   // option: add an M4 set screw + nut trap in the hub (not needed: end screw + washer retain it)
ls_hub_d       = 26;      // hub diameter (mm)
// Stud pulley (60T GT2)
stud_bore      = 15;      // measured (S1, caliper): change-gear stud diameter
stud_keyway_w  = 4;       // measured 4.1 (S2): a 4 mm key; 0 = none
stud_keyway_h  = 1.8;     // keyway depth in the hub beyond the bore; 1.8 fits a 4 x 4 key
stud_end_screw = 5;       // thread of the screw in the stud end: M5 (tapped hole ~4.3 mm in the photo)
stud_setscrew  = false;   // option: add an M3 set screw + nut trap in the hub
stud_hub_d     = 24;      // hub diameter (mm)
// Both big pulleys have a short hub on the FRONT (door side). Hub length = what is left of the free shaft length, so the pulley
// front face stands shaft_recess proud of the shaft end: the end-screw washer clamps that flat hub face (lib/layout.scad).

// ========================================================== motor ====
motor_body     = 57.0;    // NEMA23 flange square (mm)
motor_bolt_sq  = 47.14;   // bolt-hole square (mm)
motor_hole_d   = 5.2;     // bolt hole diameter (mm)
motor_pilot_d  = 38.1;    // pilot boss diameter (mm)
motor_pilot_h  = 1.6;     // MEASURE: pilot boss height (mm)
motor_shaft_d  = 8;       // shaft diameter (mm)
motor_shaft_len= 21;      // MEASURE: shaft length beyond the pilot boss face (mm)
motor_shaft_flat = 0.5;   // MEASURE: depth of the flat on the motor shaft (mm), 0 = round shaft
motor_len      = 81;      // MEASURE: motor length incl. encoder cover (mm). StepperOnline 1.2 Nm kit motor 23HS22-4004D-E1000: ~81 (listing, check the
                          //          datasheet). With the 65 mm door the window stays on the door up to ~95 mm; the 3 Nm motor (113-138) does not fit

// ======================================================= encoder ====
// Encoder LPD3806-600BM
enc_body_d     = 38;      // body diameter (mm)
enc_body_len   = 35;      // body length (mm)
enc_shaft_d    = 6;       // shaft diameter (mm)
enc_shaft_len  = 13;      // shaft length beyond the pilot boss face (mm)
enc_hole_pcd   = 30;      // mounting-hole PCD, 3x M3 at 120 deg (mm)
enc_hole_angle = 90;      // MEASURE: angle of the first mounting hole (deg, 90 = one hole straight up)
enc_pilot_d    = 20;      // MEASURE: front pilot boss diameter (mm)
enc_pilot_h    = 1.5;     // MEASURE: front pilot boss height (mm)
enc_shaft_flat = 0.5;     // depth of the D-flat on the 6 mm shaft (mm); 0 = round (LPD3806 shafts are usually round: file a flat or set 0)
enc_travel     = 8;       // encoder belt-tension slot length (+-4 mm along X)

// ============================================= base plate (base_plate.scad) ====
// FLAT plate on the old banjo seat, Z = 0 .. base_t, clamped by B1 / B2 with short M8 bolts in slots (+-3 mm along Y): the whole plate
// (motor standoffs + encoder bracket) slides along Y to tension the HTD belt. The back face is flat against the casting; every feature
// (recesses, relief, rib) is on the FRONT face, the countersinks for the M5 / M4 screws are on the back.
base_t         = 8;       // plate thickness (mm). The banjo is 17.66, but the 40T seats on the leadscrew shoulder (Z 17.66), not on the plate, so 8 is
                          //          enough. Printed PETG/ASA, or 6-8 mm aluminium from the DXF
base_travel    = 6;       // length of the B1 / B2 slots and of the clearance slot at L (+-3 mm along Y; the panel edge allows only ~2.3 mm downward anyway)
base_bolt_clear = 1;      // extra clearance on the M8 slots (mm)
base_head_d    = 10.4;    // countersink for the M5 flat-head screws (DIN 7991: head 10 x 2.8) along the slots: heads sit flush, clear of the 40T flange and belt
ls_boss_d      = 16.7;   // measured: what passes through the banjo's centre hole is the leadscrew's own 16.7 shoulder (L3), running from the panel up
                          //          to its face at Z 17.66, flush with the banjo front face. It turns, so the plate only needs clearance round it,
                          //          as a slot with the same +-3 mm travel (assembly.scad echoes the web left to the B1 countersink)
ls_boss_clear  = 0.5;     // extra clearance around it (mm)
base_boss_r    = 11;      // radius of the plate material around each B1 / B2 slot end (mm)
base_arm_w     = 22;      // width of the arm between B1 and the encoder bracket pad (mm)
base_pad_margin= 3;       // plate margin around the encoder bracket outline (mm)
base_window_w  = 10;      // lightening window width in the arm
base_rib_t     = 3;       // perimeter rib thickness (FRONT face only)
base_rib_h     = 4;       // rib height: its top (Z 12) stays under the GT2 belt (Z 14.4); left out wherever the HTD belt / 40T disc / bolts run
base_relief    = 0.5;     // shallow front-face relief under the 40T disc so its back flange does not rub the plate (ls_seat_z = base_t)
belt_env_r     = 21.5;    // radius around L occupied by the 40T flange + belt wrap (mm)

// ============================================= motor standoffs ====
// The motor hangs on 4 M5 hex standoffs (bought, steel, female-female) at the 47.14 mm bolt square; M5 countersunk screws from the back of the
// base plate (back stays flat) screw into them, M5 screws through the motor flange screw into the other end. The motor's own flange is the
// front plate. The bought aluminium 20T HTD-3M pulley has its hub towards the motor and is set along the 21 mm shaft by its set screw.
standoff_af    = 8;       // hex across flats (M5 standoff: 8 mm)
standoff_stock = [15, 20, 25, 30, 35, 40, 45];   // stock lengths (mm)
standoff_shim_max = 3;    // washer shim (1 mm M5 washers) allowed between a standoff and the flange (mm)
standoff_boss_r= 7;       // radius of the plate material around each standoff screw (mm)
base_m5        = "csk";   // M5 holes in the base plate: "csk" = clearance + countersink on the BACK (screw into the standoff)
                          //   "tap" = 4.2 mm hole for M5 thread (male-threaded standoff, screw from nowhere)  "insert" = 6.4 mm hole for an M5 heat-set insert
motor_gap_min  = 0.5;     // pulley hub end to motor pilot face, at least (mm)
mp_buy_flange  = 1.5;     // MEASURE: bought 20T HTD-3M (8 mm bore, 15 mm belt): back flange thickness
mp_buy_tooth   = 16.5;    // MEASURE: its toothed width
mp_buy_hub     = 8;       // MEASURE: its hub length (hub towards the motor)
mp_buy_flange_d= 25;      // flange OD
mp_buy_hub_d   = 22;      // hub OD
mp_hole_clear  = 4;       // extra diameter of the plate hole around the motor pulley flange

// ============================================= encoder bracket (encoder_bracket.scad) ====
// Separate printed C-cup on the base plate, OPEN towards the stud so the GT2 belt passes; its top face carries the encoder. Printed encoder
// face down, no supports. Two M4 heat-set inserts in solid columns on the +X side, fastened from the back of the base plate.
eb_wall        = 5;       // cup wall thickness (mm)
eb_clear       = 1;       // clearance between the 38 mm encoder body radius and the cup inside (mm)
eb_top_t       = 4;       // top plate thickness (mm); 4 keeps the encoder's back as close to the 65 mm door as possible
eb_recess      = 1.7;     // depth of the pilot recess in the top face (>= enc_pilot_h) (mm)
eb_pulley_gap  = 0.5;     // encoder pulley front face to the underside of the top plate (mm)
eb_col_r       = 4.6;     // radius of the two M4 columns
eb_left        = 24;      // how far the cup's side walls and top plate reach beyond the encoder slot centre towards the stud (mm)
eb_col_ang     = 50;      // angle of the columns on the +X end ring of the cup (deg from +X, one each side)
eb_insert_d    = 5.6;     // M4 heat-set insert hole (M4 x 5.7 insert)
eb_insert_depth= 7;
m4_clear       = 4.4;

// ============================================== pulleys (printed) ====
// HTD-3M
htd_flange_t     = 1.2;   // flange thickness
htd_flange_extra = 1.5;   // flange radius beyond tooth tips
htd_tooth_len    = 16;    // toothed width = belt 15 + 1 mm
htd_groove_extra = 0.1;   // groove oversize for print tolerance (mm)
// HTD-3M 20T motor pulley: printable BACKUP for the bought aluminium one (8 mm bore). Mounted like the bought one: hub towards the
// motor, set along the shaft so its toothed band lines up with the 40T.
mp_tooth_len     = 15.5;  // toothed width (belt 15 + 0.5)
mp_hub_len       = 8;
mp_hub_d         = 22;
// GT2 pulleys
gt2_flange_t     = 1.0;
gt2_flange_extra = 1.2;
gt2_tooth_len    = 6.8;   // toothed width = belt 6 + 0.8
gt2_groove_extra = 0.1;
// GT2 20T encoder pulley (bought, 6 mm bore; also printable): flange + teeth + hub (hub towards the encoder).
ep_hub_len       = 4.5;   // flange 1 + teeth 6.8 + hub 4.5 = 12.3 mm overall; a bought one longer than this lifts the encoder face (checks)
ep_hub_d         = 17.5;

// ============================================ control box ====
cb_w           = 190;     // outer width  (mm)
cb_h           = 150;     // outer height (mm)
cb_wall        = 3;       // frame wall thickness
cb_panel_t     = 4;       // front panel thickness (16 mm buttons need a thread >= 5 mm; keep <= 5)
cb_depth       = 70;      // MEASURE: frame depth (mm) = panel back to lid rear. Must clear the longest body behind the panel (22 mm 2NC E-stop block, 55-65 mm).
cb_lid_t       = 5;       // lid thickness (sits in a rebate flush with the frame rear)
cb_corner_r    = 5;       // outer corner radius
cb_post        = 10;      // corner screw block size (mm, square)
cb_lid_clear   = 0.3;     // lid-to-frame clearance per side

// ILI9341 2.8" SPI module (landscape on the panel, front view)
tft_pcb        = [86, 50];     // PCB size (mm)
tft_win        = [57.6, 43.2]; // visible area (mm)
tft_win_off    = [14.2, 3.4];  // MEASURE: lower-left corner of the VISIBLE AREA from the PCB lower-left corner (mm). Centred placeholder; real modules are not centred.
tft_win_margin = 0.5;          // window cutout oversize per side
tft_holes      = [79, 43];     // MEASURE: mounting-hole spacing x, y (mm)
tft_stack_h    = 3.8;          // MEASURE: height of the LCD glass above the PCB front face = post height (mm)
tft_post_d     = 7;            // post diameter
tft_pos        = [-46, 35];    // PCB centre on the panel (front view, x right, y up, origin at panel centre)

// Controls, front view (x right, y up, origin at panel centre)
btn_hole       = 16.2;         // 16 mm push button cutout
btn_grid_c     = [-40, -31];   // centre of the 3x3 grid
btn_pitch      = [26, 26];     // grid pitch
nutbtn_hole    = 22.3;         // 22 mm NUT button cutout
nutbtn_pos     = [47, -25];
estop_hole     = 22.3;         // 22 mm E-stop cutout
estop_pos      = [68, 40];
estop_head_d   = 40;           // mushroom head diameter (visual only)
led_hole       = 8.2;          // MEASURE: FAULT LED holder hole (5 mm LED holder: 5.2; 8 mm: 8.2)
led_pos        = [22, 8];
knob_hole      = 7.2;          // EC11 bushing hole (7 mm)
knob_tab_w     = 2.4;          // anti-rotation tab slot width
knob_tab_l     = 1.8;          // slot reach beyond the hole edge
knob_pos       = [22, 40];
label_size     = 3.4;
label_depth    = 0.6;          // engraving depth
label_font     = "Liberation Sans:style=Bold";

// Inside: Teensy 4.1 on a 60 x 50 mm perfboard (M2.5), standoffs on the lid
perf_holes     = [54, 44];     // MEASURE: perfboard mounting-hole spacing (mm)
perf_pos       = [0, 0];       // perfboard centre on the lid (keep x = 0, lid is flipped when assembled)
perf_stand_h   = 6;            // standoff height
perf_stand_d   = 6;

// PG7 cable glands through the bottom wall (12.5 mm hole)
gland_d        = 12.6;
gland_x        = [-30, 0, 30]; // spindle encoder, motor-driver signals, E-stop / power
gland_z        = 42;           // gland axis height from the frame front rim (mm); keep clear of button bodies
// Mounting ears on the side walls: M6 arm hole + magnet pocket (flat pot magnet)
ear_len        = 34;           // ear length beyond the wall (mm)
ear_w          = 30;           // ear width (mm)
ear_t          = 6;            // ear thickness (mm)
ear_hole       = 6.6;          // M6 arm-mount hole
magnet_d       = 20.3;         // MEASURE: magnet diameter + clearance (mm)
magnet_h       = 3.2;          // MEASURE: magnet thickness + clearance (mm)

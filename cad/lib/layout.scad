// lib/layout.scad -- DERIVED layout numbers for the Roher TBL-20/520 drive. `include` it AFTER params.scad:
//     include <params.scad>
//     include <lib/layout.scad>
// Everything here is computed from params.scad: belt centres, the Z stack, the motor standoff length, the encoder bracket height.
// Frame: origin = leadscrew axis L, +X right, +Y up, +Z out of the panel; Z = 0 is the banjo-seat plane (see params.scad).
use <belt.scad>
use <pulley_core.scad>

function overlap(a0, a1, b0, b1) = max(0, min(a1, b1) - max(a0, b0));

// ---- belts -------------------------------------------------------------------------------------------------------
ls_belt_len = ls_belt_teeth * ls_pitch;
C_ls  = center_for_length(ls_belt_len, pitch_dia(ls_teeth_motor, ls_pitch), pitch_dia(ls_teeth_screw, ls_pitch));
C_enc = center_for_length(enc_belt_len, pitch_dia(enc_teeth_encoder, enc_pitch), pitch_dia(enc_teeth_stud, enc_pitch));
pos_motor = lathe_L + C_ls * [-sin(motor_angle), -cos(motor_angle)];   // motor shaft axis: below L, swung motor_angle towards the hinge
// The motor's square turns with the belt (by -motor_angle), so the four standoffs stay either side of the belt strands.
motor_rot = -motor_angle;
function rot2(v, a) = [v.x * cos(a) - v.y * sin(a), v.x * sin(a) + v.y * cos(a)];
motor_so_pts  = [for (sx = [-1, 1], sy = [-1, 1]) pos_motor + rot2((motor_bolt_sq / 2) * [sx, sy], motor_rot)];   // standoffs
motor_corners = [for (sx = [-1, 1], sy = [-1, 1]) pos_motor + rot2((motor_body / 2) * [sx, sy], motor_rot)];      // flange / body corners
pos_enc   = [stud_S.x + C_enc, stud_S.y];         // encoder shaft axis E, right of the stud

// ---- 40T leadscrew pulley: back flange on ls_seat_z, toothed disc, front flange, hub (front) ------------------------
ls_body_h     = pc_height(htd_tooth_len, htd_flange_t, htd_flange_extra, true, true, 0);
ls_hub_len    = ls_setscrew ? max(8, ls_shaft_free + shaft_recess - ls_body_h)    // set-screw option needs a hub (stack then exceeds the shaft: FAIL)
                            : max(2, ls_shaft_free + shaft_recess - ls_body_h);
ls_stack_h    = ls_body_h + ls_hub_len;
ls_front_z    = ls_seat_z + ls_stack_h;
ls_belt_mid_z = ls_seat_z + pc_belt_mid(htd_tooth_len, htd_flange_t, true);
ls_run_gap    = ls_seat_z - base_t;               // pulley back face to the base plate front face (>= 0; base_relief adds a recess under the disc)

// ---- 60T stud pulley on a spacer ring ------------------------------------------------------------------------------
stud_z0       = stud_seat_z + stud_spacer;                    // back face of the 60T pulley (must be > bearing_cap_z)
stud_body_h   = pc_height(gt2_tooth_len, gt2_flange_t, gt2_flange_extra, true, true, 0);
stud_hub_len  = stud_setscrew ? max(6, stud_seat_z + stud_shaft_free + shaft_recess - stud_z0 - stud_body_h)
                              : max(2, stud_seat_z + stud_shaft_free + shaft_recess - stud_z0 - stud_body_h);
stud_stack_h  = stud_body_h + stud_hub_len;
stud_front_z  = stud_z0 + stud_stack_h;
stud_belt_mid_z = stud_z0 + pc_belt_mid(gt2_tooth_len, gt2_flange_t, true);

// ---- motor on 4 M5 standoffs ---------------------------------------------------------------------------------------
// Bought 20T HTD-3M: back flange, toothed band, hub (towards the motor). It is set on the shaft with its toothed band centred on the 40T's belt
// band, so its hub end is at mp_front_z; the standoffs must raise the motor's pilot face above that (+ motor_gap_min).
mp_len        = mp_buy_flange + mp_buy_tooth + mp_buy_hub;
mp_back_z     = ls_belt_mid_z - (mp_buy_flange + mp_buy_tooth / 2);
mp_front_z    = mp_back_z + mp_len;
standoff_need = mp_front_z + motor_gap_min + motor_pilot_h - base_t;              // standoff (+ shim) length that just clears the hub
standoff_len  = min([for (s = standoff_stock) if (s + standoff_shim_max >= standoff_need - 0.001) s]);
standoff_shim = max(0, ceil((standoff_need - standoff_len) * 2) / 2);              // washer shim, rounded up to 0.5 mm
motor_face_z  = base_t + standoff_len + standoff_shim;                              // Z of the motor flange face (pilot boss points back)
motor_tip_z   = motor_face_z - motor_pilot_h - motor_shaft_len;
motor_gap     = motor_face_z - motor_pilot_h - mp_front_z;                          // hub end to pilot face
motor_engage  = min(mp_front_z, motor_face_z - motor_pilot_h) - max(motor_tip_z, mp_back_z);   // pulley bore on the shaft
motor_front_z = motor_face_z + motor_len;
// belt overlap: belt band is centred on the 40T; 15 mm belt vs the toothed zones
belt_lo = ls_belt_mid_z - ls_belt_w / 2;  belt_hi = ls_belt_mid_z + ls_belt_w / 2;
ov_40  = overlap(belt_lo, belt_hi, ls_belt_mid_z - htd_tooth_len / 2, ls_belt_mid_z + htd_tooth_len / 2);
ov_20  = overlap(belt_lo, belt_hi, mp_back_z + mp_buy_flange, mp_back_z + mp_buy_flange + mp_buy_tooth);

// ---- encoder bracket -------------------------------------------------------------------------------------------------
// 20T GT2 on the 13 mm shaft: back flange, teeth, hub (towards the encoder), belt band on the stud's. Bracket top face = encoder face.
ep_len        = pc_height(gt2_tooth_len, gt2_flange_t, gt2_flange_extra, true, false, ep_hub_len);
ep_back_z     = stud_belt_mid_z - pc_belt_mid(gt2_tooth_len, gt2_flange_t, true);
ep_front_z    = ep_back_z + ep_len;
enc_face_z    = ep_front_z + eb_pulley_gap + eb_top_t;                            // encoder mounting face (top of the bracket): the pulley sits UNDER the top plate
enc_tip_z     = enc_face_z - eb_recess - enc_shaft_len;                            // the pilot boss sits in the recess (eb_recess >= enc_pilot_h)
enc_engage    = ep_front_z - max(enc_tip_z, ep_back_z);                             // pulley bore on the shaft
enc_front_z   = enc_face_z + enc_body_len;
eb_h          = enc_face_z - base_t;                                                // bracket height above the base plate
eb_in         = enc_body_d / 2 + eb_clear;                                          // half width inside the cup
eb_out        = eb_in + eb_wall;
eb_under_z    = enc_face_z - eb_top_t;                                              // underside of the bracket top plate

enc_belt_lo   = stud_belt_mid_z - enc_belt_w / 2;  enc_belt_hi = stud_belt_mid_z + enc_belt_w / 2;
ov_60  = overlap(enc_belt_lo, enc_belt_hi, stud_z0 + gt2_flange_t, stud_z0 + gt2_flange_t + gt2_tooth_len);
ov_e20 = overlap(enc_belt_lo, enc_belt_hi, ep_back_z + gt2_flange_t, ep_back_z + gt2_flange_t + gt2_tooth_len);

// ---- plate planform numbers ---------------------------------------------------------------------------------------------
plate_x_max   = panel_right_x - panel_margin;
plate_y_min   = panel_bottom_y + panel_margin;

// ---- door windows: anything poking past the closed door goes through a window cut in it -----------------------------------
// The door swings about a vertical hinge axis at (door_hinge_x, door_hinge_z). While it opens, every point of the door moves on a
// circle round that axis, so the window edge away from the hinge sweeps into whatever pokes through unless it is at least as far
// from the hinge as that object's outer back corner. On the hinge side and above/below, a plain clearance is enough.
function swing_edge_x(x_far, z_front) =
    let(rc = norm([x_far - door_hinge_x, z_front - door_hinge_z]), dz = door_depth - door_hinge_z)
    door_hinge_x + sqrt(max(0, rc * rc - dz * dz));
// window [x0, x1, y0, y1] for an object occupying box [x0, x1, y0, y1] in XY whose front (furthest Z) is z_front
function door_window(box, z_front) =
    [box[0] - door_cut_clear - door_cable_gap, max(box[1] + door_cut_clear, swing_edge_x(box[1], z_front) + door_swing_margin),
     box[2] - door_cut_clear_y, box[3] + door_cut_clear_y];
motor_box     = [min([for (c = motor_corners) c.x]), max([for (c = motor_corners) c.x]), min([for (c = motor_corners) c.y]), max([for (c = motor_corners) c.y])];
enc_box       = [pos_enc.x - enc_body_d / 2, pos_enc.x + enc_body_d / 2, pos_enc.y - enc_body_d / 2, pos_enc.y + enc_body_d / 2];
motor_cut     = motor_front_z > door_depth - door_clear;
enc_cut       = enc_front_z > door_depth - door_clear;
motor_window  = door_window(motor_box, motor_front_z);
enc_window    = door_window(enc_box, enc_front_z);

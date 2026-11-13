// assembly.scad -- Roher TBL-20/520 ELS drive: layout, fit checks and belt report (not printed).
// Lathe frame (see params.scad): origin = leadscrew axis L, +X right, +Y up, +Z out of the end panel towards the door; Z = 0 = casting face.
//
//   view = "iso"    (default) oblique view
//   view = "front"  looking along -Z (the photo view): compare with ../docs/roher_layout.png
//   view = "side"          from the right (+X), whole scene, with the door plane
//   view = "side_motor"    side view clipped to the leadscrew / motor column (Y -95..25): 40T, 20T, belt, standoffs, motor
//   view = "side_enc"      side view clipped to the stud / encoder row (Y +-35 round the stud): 60T, 20T, belt, bracket, encoder
//
// Every check echoes PASS/FAIL with its numbers (openscad -o /dev/null assembly.scad 2>&1 | grep CHECK).
include <params.scad>
include <lib/layout.scad>
use <lib/belt.scad>
use <lib/teeth.scad>
use <pulley_htd3m.scad>
use <pulley_gt2.scad>
use <base_plate.scad>
use <encoder_bracket.scad>
use <spacer.scad>
use <door_bezel.scad>

view = "iso";
part = "";           // "" = everything; otherwise only the named piece (used by viewer/build_viewer.py)
module piece(name) { if (part == "" || part == name) children(); }
show_belts = true;
plate_alpha = view == "front" ? 0.6 : 0.95;     // front view: see the pulleys / belts through the plates
motor_alpha = view == "front" ? 0.4 : 0.95;

motor_front_prev = 116.5;    // motor front Z of the previous design (drive plate with a sunk motor), for the comparison

// ---------------------------------------------------------------- helpers ----------------------------------------
function verdict(ok) = ok ? "PASS" : "FAIL";
function r2(x) = round(x * 100) / 100;
function dist_seg(p, a, b) = let (ab = b - a, t = max(0, min(1, ((p - a) * ab) / (ab * ab)))) norm(p - (a + ab * t));
function dist_seg_seg(a1, a2, b1, b2) = min(dist_seg(a1, b1, b2), dist_seg(a2, b1, b2), dist_seg(b1, a1, a2), dist_seg(b2, a1, a2));
// distance from point p to the convex hull of circle(c1, r1) and circle(c2, r2) (negative inside)
function dist_hull(p, c1, r1, c2, r2) = min([for (i = [0 : 100]) let (t = i / 100) norm(p - (c1 + (c2 - c1) * t)) - (r1 + (r2 - r1) * t)]);
function htd_od_(n) = n * 3 / PI - 2 * 0.381;
function gt2_od_(n) = n * 2 / PI - 2 * 0.254;

stud_flange_r = gt2_od_(enc_teeth_stud) / 2 + gt2_flange_extra;
ls_flange_r   = htd_od_(ls_teeth_screw) / 2 + htd_flange_extra;
stud_cap_gap  = norm(stud_S - spindle_xy) - bearing_cap_r;      // free radius around the stud before the bearing cap disc
standoff_r    = standoff_af / 2 / cos(30);                       // hex corner radius
ls_belt_r     = max(ls_flange_r, pitch_dia(ls_teeth_screw, ls_pitch) / 2 + 1.4);   // 40T flange / belt wrap radius
mp_belt_r     = max(mp_buy_flange_d / 2, pitch_dia(ls_teeth_motor, ls_pitch) / 2 + 1.4);
so_pts = motor_so_pts;
csk_h  = (base_head_d - 0.4 - banjo_bolt_d) / 2;                 // DIN 7991 head height (90 deg countersink)

// ---- base plate planform as a list of circles, grouped into convex hulls: [[c, r], ...] -------------------------------------------------
B1a = banjo_B1 + [0, base_travel / 2];  B1b = banjo_B1 - [0, base_travel / 2];
B2a = banjo_B2 + [0, base_travel / 2];  B2b = banjo_B2 - [0, base_travel / 2];
col_c = pos_enc + [enc_travel / 2, 0];
col_pts = [for (s = [-1, 1]) col_c + (eb_out - eb_col_r + 0.8 - 1) * [cos(eb_col_ang), s * sin(eb_col_ang)]];
pad_left_x = pos_enc.x - enc_travel / 2 - eb_left - base_pad_margin;
plate_groups = [
    [[B1a, base_boss_r], [B1b, base_boss_r], [B2a, base_boss_r], [B2b, base_boss_r], for (p = so_pts) [p, standoff_boss_r]],
    [[B1a, base_arm_w / 2], [col_c, base_arm_w / 2]],
    [[col_c, eb_out + base_pad_margin], [[pad_left_x, pos_enc.y + eb_out + base_pad_margin], 0.01], [[pad_left_x, pos_enc.y - eb_out - base_pad_margin], 0.01],
     for (p = col_pts) [p, eb_col_r + base_pad_margin]]
];
function plate_dist(p) = min([for (g = plate_groups) for (i = [0 : len(g) - 1]) for (j = [i : len(g) - 1]) dist_hull(p, g[i][0], g[i][1], g[j][0], g[j][1])]);
plate_x_right = max([for (g = plate_groups) for (c = g) c[0].x + c[1]]);
plate_x_left  = min([for (g = plate_groups) for (c = g) c[0].x - c[1]]);
plate_y_top   = max([for (g = plate_groups) for (c = g) c[0].y + c[1]]);
plate_y_bot   = max(plate_y_min, min([for (g = plate_groups) for (c = g) c[0].y - c[1]]));

// ---------------------------------------------------------------- CHECKS -----------------------------------------
echo("CHECK ----- belts and centre distances -----");
echo(str("CHECK leadscrew belt: HTD-3M 20T/40T 15 mm, stock 3M-", ls_belt_len, " (", ls_belt_teeth, " teeth), C_ls = ", r2(C_ls),
         " mm (motor axis at [0, ", r2(-C_ls), "]), speed ratio 2:1 (motor 2x leadscrew)"));
echo(str("CHECK   other stock lengths: ", [for (n = [67 : 72]) str("3M-", n * 3, " -> C=", r2(center_for_length(n * 3, pitch_dia(ls_teeth_motor, ls_pitch), pitch_dia(ls_teeth_screw, ls_pitch))))]));
echo(str("CHECK encoder belt: GT2 6 mm 60T/20T, stock ", enc_belt_len, " mm loop (", enc_belt_len / enc_pitch, " teeth), C_enc = ", r2(C_enc),
         " mm, encoder shaft E = [", r2(pos_enc.x), ", ", r2(pos_enc.y), "]; encoder turns 2/9 x 3 = 2/3 spindle speed (1600 counts per spindle turn)"));
echo(str("CHECK   other GT2 loops: ", [for (L = [158, 200, 240]) str(L, " -> C=", r2(center_for_length(L, pitch_dia(enc_teeth_encoder, enc_pitch), pitch_dia(enc_teeth_stud, enc_pitch))))]));
echo(belt_report("Leadscrew drive HTD-3M", ls_teeth_motor, ls_teeth_screw, C_ls, ls_pitch, htd3m_stock()));
echo(belt_report("Encoder drive GT2", enc_teeth_encoder, enc_teeth_stud, C_enc, enc_pitch, gt2_stock()));

echo("CHECK ----- Z stack (mm from the banjo seat plane) -----");
echo(str("CHECK base plate Z 0..", base_t, "; 40T pulley seat Z ", ls_seat_z, " (back face to plate front face: ", r2(ls_run_gap), " mm, ", base_relief, " mm relief recess under the disc): ",
         verdict(ls_run_gap >= -0.001), ls_run_gap > 0.6 ? str("; the 40T seats on the leadscrew's own ", ls_shoulder_d, " mm shoulder, the ", r2(ls_run_gap), " mm behind it stays open") : "; no collar on the leadscrew"));
echo(str("CHECK 40T pulley Z ", ls_seat_z, "..", r2(ls_front_z), " (hub ", r2(ls_hub_len), " mm, belt band centre Z ", r2(ls_belt_mid_z), "); shaft end Z ",
         ls_seat_z + ls_shaft_free, " -> pulley face ", r2(ls_front_z - (ls_seat_z + ls_shaft_free)), " mm proud, the washer clamps the hub"));
echo(str("CHECK 60T pulley Z ", r2(stud_z0), "..", r2(stud_front_z), " on a ", stud_spacer, " mm ring (hub ", r2(stud_hub_len), " mm, belt band centre Z ", r2(stud_belt_mid_z), ")"));
echo(str("CHECK 60T stud pulley back face Z ", r2(stud_z0), " > bearing_cap_z ", bearing_cap_z, ": ", verdict(stud_z0 > bearing_cap_z), " (", r2(stud_z0 - bearing_cap_z),
         " mm; without the ring it would be at ", stud_seat_z, " -> ", verdict(stud_seat_z > bearing_cap_z), ", the 60T overlaps the cap in XY by ", r2(stud_flange_r - stud_cap_gap), " mm)"));
echo(str("CHECK stud ring (r 10) and hub (r ", stud_hub_d / 2, ") fit inside the free radius ", r2(stud_cap_gap), " mm before the cap disc: ", verdict(stud_hub_d / 2 < stud_cap_gap)));
echo(str("CHECK stud belt back edge Z ", r2(enc_belt_lo), " > bearing_cap_z ", bearing_cap_z, ": ", verdict(enc_belt_lo > bearing_cap_z)));
echo(str("CHECK belts clear the base plate: HTD belt back edge Z ", r2(belt_lo), " vs plate front ", base_t, " (", r2(belt_lo - base_t), " mm); GT2 belt back edge Z ", r2(enc_belt_lo),
         " vs rib top Z ", base_t + base_rib_h, " (", r2(enc_belt_lo - base_t - base_rib_h), " mm): ", verdict(belt_lo - base_t >= 1 && enc_belt_lo - base_t - base_rib_h >= 1)));

echo("CHECK ----- motor on standoffs -----");
echo(str("CHECK 20T HTD pulley (bought, hub towards the motor, set screw on the shaft flat): Z ", r2(mp_back_z), "..", r2(mp_front_z), " (flange ", mp_buy_flange, " + teeth ", mp_buy_tooth,
         " + hub ", mp_buy_hub, "), toothed band Z ", r2(mp_back_z + mp_buy_flange), "..", r2(mp_back_z + mp_buy_flange + mp_buy_tooth), " centred on the 40T's belt band (Z ", r2(ls_belt_mid_z), ")"));
echo(str("CHECK belt overlap with the 40T teeth ", r2(ov_40), " mm and with the 20T teeth ", r2(ov_20), " mm (belt ", ls_belt_w, "): ", verdict(ov_40 >= ls_belt_w - 0.001 && ov_20 >= ls_belt_w - 0.001),
         "; alignment slack +-", r2((htd_tooth_len - ls_belt_w) / 2), " (40T) / +-", r2((mp_buy_tooth - ls_belt_w) / 2), " mm (20T)"));
echo(str("CHECK STANDOFF: exact length ", r2(standoff_need), " mm (pulley hub end Z ", r2(mp_front_z), " + ", motor_gap_min, " gap + ", motor_pilot_h, " pilot - plate ", base_t,
         ") -> stock M5 hex standoff ", standoff_len, " mm + ", standoff_shim, " mm washer shim = ", standoff_len + standoff_shim, " mm; motor flange face Z ", r2(motor_face_z)));
echo(str("CHECK motor shaft: tip Z ", r2(motor_tip_z), " (", r2(motor_engage), " of the ", r2(mp_len), " mm pulley bore on the shaft, hub end to pilot face ", r2(motor_gap), " mm): ",
         verdict(motor_gap >= motor_gap_min - 0.001 && motor_tip_z <= mp_back_z + mp_buy_flange + mp_buy_tooth && motor_engage >= mp_buy_hub + 4)));
so_belt = min([for (p = so_pts) dist_hull(p, lathe_L, ls_belt_r, pos_motor, mp_belt_r) - standoff_r]);
so_flange = min([for (p = so_pts) norm(p - lathe_L) - standoff_r - ls_flange_r]);
echo(str("CHECK standoff (hex corner r ", r2(standoff_r), ") clearance to the HTD belt strands: ", r2(so_belt), " mm, to the 40T flange: ", r2(so_flange), " mm: ", verdict(so_belt >= 2 && so_flange >= 2)));
echo(str("CHECK motor flange (Z ", r2(motor_face_z), ") above the 40T stack front (Z ", r2(ls_front_z), "): ", verdict(motor_face_z > ls_front_z), " (clear by ", r2(motor_face_z - ls_front_z), " mm); ",
         "belts below the flange by ", r2(motor_face_z - belt_hi), " mm"));

echo("CHECK ----- encoder on the cup bracket -----");
echo(str("CHECK 20T GT2 on the encoder (hub towards the encoder): Z ", r2(ep_back_z), "..", r2(ep_front_z), ", toothed band Z ", r2(ep_back_z + gt2_flange_t), "..", r2(ep_back_z + gt2_flange_t + gt2_tooth_len),
         ", stud 60T band Z ", r2(stud_z0 + gt2_flange_t), "..", r2(stud_z0 + gt2_flange_t + gt2_tooth_len)));
echo(str("CHECK GT2 belt overlap with the 60T teeth ", r2(ov_60), " mm and the 20T teeth ", r2(ov_e20), " mm (belt ", enc_belt_w, "): ", verdict(ov_60 >= enc_belt_w - 0.001 && ov_e20 >= enc_belt_w - 0.001)));
echo(str("CHECK encoder face (bracket top) Z = ", r2(enc_face_z), " (bracket ", r2(eb_h), " mm above the plate, top plate ", eb_top_t, " mm thick, underside Z ", r2(eb_under_z),
         "); 13 mm shaft tip Z ", r2(enc_tip_z), ", ", r2(enc_engage), " of ", r2(ep_len), " mm pulley bore on the shaft: ", verdict(enc_engage >= ep_hub_len + 4 && enc_tip_z <= ep_back_z + gt2_flange_t + gt2_tooth_len)));
eb_belt_clear = min([for (sx = [-1, 1], sy = [-1, 1], sp = [-1, 1])
    dist_hull([pos_enc.x - enc_travel / 2 - eb_left, pos_enc.y + sy * eb_in], stud_S, gt2_od_(enc_teeth_stud) / 2 + 1.4, pos_enc + [sp * enc_travel / 2, 0], pitch_dia(enc_teeth_encoder, enc_pitch) / 2 + 1.5)]);
echo(str("CHECK bracket walls (inner edge, free ends at X ", r2(pos_enc.x - enc_travel / 2 - eb_left), ") to the GT2 belt strands: ", r2(eb_belt_clear), " mm (strands over the +-4 mm slide); belt top edge Z ", r2(enc_belt_hi),
         " to the top plate underside: ", r2(eb_under_z - enc_belt_hi), " mm: ", verdict(eb_belt_clear >= 2 && eb_under_z - enc_belt_hi >= 2)));
echo(str("CHECK bracket open towards the stud (-X), 2x M4 inserts, prints face down (top face on the bed), no supports"));

echo(str("CHECK ----- door (inside of the closed door at Z = ", door_depth, ", hinge axis X ", door_hinge_x, ") -----"));
// A window in the door must keep this much sheet to the door's bottom fold / right edge (both at the panel edges).
window_edge_min = 3;
module window_checks(name, cut, box, z_front, win) {
    if (!cut) echo(str("CHECK ", name, ": front Z ", r2(z_front), " stays inside the door (", r2(door_depth - door_clear - z_front), " mm to spare): no window needed"));
    else {
        far_gap = win[1] - box[1];
        echo(str("CHECK ", name, " pokes ", r2(z_front - door_depth), " mm past the door: WINDOW ", r2(win[1] - win[0]), " x ", r2(win[3] - win[2]),
                 " mm at X ", r2(win[0]), "..", r2(win[1]), ", Y ", r2(win[2]), "..", r2(win[3]),
                 "; gaps: hinge side ", door_cut_clear + door_cable_gap, " (", door_cable_gap, " of it for the cables), above/below ", door_cut_clear_y, ", far side ", r2(far_gap), " mm (", r2(far_gap - door_cut_clear), " of it for the swing)"));
        echo(str("CHECK   ", name, " window: sheet left to the bottom fold ", r2(win[2] - panel_bottom_y), " mm, to the right edge ", r2(panel_right_x - win[1]), " mm: ",
                 verdict(win[2] - panel_bottom_y >= window_edge_min && panel_right_x - win[1] >= window_edge_min),
                 " (>= ", window_edge_min, "; the bezel may overhang the edge)"));
        echo(str("CHECK   ", name, " window: swing check, far window edge radius from the hinge ", r2(norm([win[1] - door_hinge_x, door_depth - door_hinge_z])),
                 " >= outer back corner radius ", r2(norm([box[1] - door_hinge_x, z_front - door_hinge_z])), ": ",
                 verdict(norm([win[1] - door_hinge_x, door_depth - door_hinge_z]) >= norm([box[1] - door_hinge_x, z_front - door_hinge_z]))));
    }
}
window_checks("motor", motor_cut, motor_box, motor_front_z, motor_window);
window_checks("encoder", enc_cut, enc_box, enc_front_z, enc_window);
echo(str("CHECK door switch plunger at [", sw_plunger.x, ", ", sw_plunger.y, "] is outside the motor window: ",
         verdict(!motor_cut || sw_plunger.x < motor_window[0] - 5 || sw_plunger.y < motor_window[2] - 5 || sw_plunger.y > motor_window[3] + 5),
         " (the door still closes fully, so the switch still works)"));

echo("CHECK ----- XY keep-outs and the Y slide -----");
echo(str("CHECK base plate ", r2(plate_x_right - plate_x_left), " x ", r2(plate_y_top - plate_y_bot), " mm, ", base_t, " mm thick (X ", r2(plate_x_left), "..", r2(plate_x_right), ", Y ", r2(plate_y_bot), "..", r2(plate_y_top), ")"));
echo(str("CHECK plate bottom Y = ", r2(plate_y_bot), " >= ", plate_y_min, " (panel edge ", panel_bottom_y, " + ", panel_margin, "): ", verdict(plate_y_bot >= plate_y_min - 0.001),
         "; right edge X = ", r2(plate_x_right), " <= ", plate_x_max, ": ", verdict(plate_x_right <= plate_x_max)));
echo(str("CHECK slide: the slots allow +-", base_travel / 2, " mm along Y; sliding the plate DOWN (tension) is limited by the panel-edge margin to ", r2(plate_y_bot - plate_y_min), " mm (motor flange bottom ",
         r2(motor_box[2]), " nominal, ", r2(motor_box[2] - base_travel / 2), " at -", base_travel / 2, " mm: ", verdict(motor_box[2] - base_travel / 2 > panel_bottom_y), " vs the panel edge itself)"));
echo(str("CHECK a Y slide d changes the horizontal GT2 centre by sqrt(C^2 + d^2) - C: ", r2(sqrt(C_enc * C_enc + pow(base_travel / 2, 2)) - C_enc), " mm at the full +-", base_travel / 2, " mm, ", r2(sqrt(C_enc * C_enc + 4) - C_enc), " mm at 2 mm (usable down travel), ",
         r2(sqrt(C_enc * C_enc + 1) - C_enc), " mm at 1 mm: ", verdict(sqrt(C_enc * C_enc + 4) - C_enc < 0.2), " (< 0.2 mm; the belt slack, +-4 mm slots, absorbs it)"));
echo(str("CHECK motor flange right of the switch box: flange left X = ", r2(motor_box[0]), " > box right X ", sw_x[1], ": ", verdict(motor_box[0] > sw_x[1]),
         " (", r2(motor_box[0] - sw_x[1]), " mm)"));
sw_dist = min([for (i = [0 : 30]) plate_dist([sw_x[1], sw_y[0] + (sw_y[1] - sw_y[0]) * i / 30]), for (i = [0 : 30]) plate_dist([sw_x[0] + (sw_x[1] - sw_x[0]) * i / 30, sw_y[1]])]);
echo(str("CHECK plate vs switch box: closest approach ", r2(sw_dist), " mm: ", verdict(sw_dist >= 2), " (the door plunger at [", sw_plunger.x, ", ", sw_plunger.y, "] is ", r2(plate_dist(sw_plunger)), " mm from the plate)"));
echo(str("CHECK plate vs bearing cap disc (r ", bearing_cap_r, " + ", bearing_cap_clear, "): closest approach ", r2(plate_dist(spindle_xy) - bearing_cap_r), " mm: ", verdict(plate_dist(spindle_xy) >= bearing_cap_r + bearing_cap_clear)));
echo(str("CHECK plate and bracket vs stud pulley (flange r ", r2(stud_flange_r), " + 3 mm): closest approach ", r2(plate_dist(stud_S) - stud_flange_r), " mm: ", verdict(plate_dist(stud_S) >= stud_flange_r + 3)));
ws_b1 = dist_seg_seg(B1a, B1b, lathe_L + [0, base_travel / 2], lathe_L - [0, base_travel / 2]);
ws_b2 = dist_seg_seg(B2a, B2b, lathe_L + [0, base_travel / 2], lathe_L - [0, base_travel / 2]);
ls_r = (ls_boss_d + 2 * ls_boss_clear) / 2;
echo(str("CHECK web between the L slot (r ", r2(ls_r), ") and the B1 / B2 bolt slots (r ", (banjo_bolt_d + base_bolt_clear) / 2, "): ", r2(ws_b1 - ls_r - (banjo_bolt_d + base_bolt_clear) / 2), " / ",
         r2(ws_b2 - ls_r - (banjo_bolt_d + base_bolt_clear) / 2), " mm; at the countersink (r ", base_head_d / 2, "): ", r2(ws_b1 - ls_r - base_head_d / 2), " / ", r2(ws_b2 - ls_r - base_head_d / 2), " mm: ",
         verdict(ws_b1 - ls_r - (banjo_bolt_d + base_bolt_clear) / 2 >= 2 && ws_b1 - ls_r - base_head_d / 2 >= 0.8)));
echo(str("CHECK countersunk M", banjo_bolt_d, " heads (DIN 7991 head ", base_head_d - 0.4, ") flush with the plate front face Z ", base_t, ": 40T flange back face at Z ", ls_seat_z, ", head recess dia ", base_head_d, ": ", verdict(ls_seat_z >= base_t)));
echo("CHECK ----- end of checks -----");

// ---------------------------------------------------------------- geometry ---------------------------------------
module belt2d(c1, c2, d1, d2, t = 1.2) {
    difference() {
        hull() { translate(c1) circle(d = d1 + t, $fn = 64); translate(c2) circle(d = d2 + t, $fn = 64); }
        hull() { translate(c1) circle(d = d1 - t, $fn = 64); translate(c2) circle(d = d2 - t, $fn = 64); }
    }
}
module washer_screw(z, d_screw) {      // end screw + washer on a shaft end, washer face at z
    piece("hardware") color("Silver") translate([0, 0, z]) cylinder(d = d_screw * 2 + 1, h = 1.6, $fn = 32);
    piece("hardware") color("DimGray") translate([0, 0, z + 1.6]) cylinder(d = d_screw * 1.6, h = d_screw, $fn = 32);
}

module panel_context() {
    piece("panel") color("SteelBlue") translate([-150, panel_bottom_y, -3]) cube([150 + panel_right_x, 250 - panel_bottom_y, 2.6]);           // end panel
    piece("switch") color("Red", 0.8) translate([sw_x[0], sw_y[0], 0]) cube([sw_x[1] - sw_x[0], sw_y[1] - sw_y[0], 22]);                      // door microswitch box
    piece("plunger") color("Magenta") translate([sw_plunger.x, sw_plunger.y, 0]) cylinder(d = 5, h = 30, $fn = 16);
    piece("cap") color("DimGray") translate([spindle_xy.x, spindle_xy.y, 0]) cylinder(r = bearing_cap_r, h = bearing_cap_z, $fn = 96);       // spindle bearing cap
    piece("spindle") color("Gray") translate([spindle_xy.x, spindle_xy.y, 0]) cylinder(d = 24, h = bearing_cap_z + 6, $fn = 48);
    piece("keepin") color("Lime") translate([-150, plate_y_min - 0.4, 0]) cube([150 + plate_x_max, 0.4, 0.4]);                                // keep-in lines
    piece("keepin") color("Lime") translate([plate_x_max, plate_y_min, 0]) cube([0.4, 250, 0.4]);
    piece("markers") color("White") for (p = [lathe_L, stud_S, spindle_xy]) translate([p.x, p.y, 0]) cylinder(d = 3, h = 2, $fn = 16);
}

module leadscrew_stack() {
    piece("shafts") color("Silver") cylinder(d = ls_shaft_bore, h = ls_seat_z + ls_shaft_free, $fn = 48);
    piece("shafts") color("Gray") cylinder(d = ls_boss_d, h = ls_seat_z, $fn = 48);                                // leadscrew boss through the plate's clearance slot
    piece("pulley40") translate([0, 0, ls_seat_z]) color("Orange") pulley_htd3m_40T();
    washer_screw(ls_front_z, ls_end_screw);
}
module motor_pulley_bought() {             // bought 20T HTD-3M: back flange, teeth, hub (towards the motor)
    color("Orange") {
        cylinder(d = mp_buy_flange_d, h = mp_buy_flange, $fn = 64);
        translate([0, 0, mp_buy_flange]) cylinder(d = htd_od_(ls_teeth_motor), h = mp_buy_tooth, $fn = 64);
        translate([0, 0, mp_buy_flange + mp_buy_tooth]) cylinder(d = mp_buy_hub_d, h = mp_buy_hub, $fn = 64);
    }
}
module motor_stack() {
    piece("pulley20htd") translate([pos_motor.x, pos_motor.y, mp_back_z]) motor_pulley_bought();
    for (p = so_pts) {
        piece("standoffs") translate([p.x, p.y, base_t]) color("SlateGray") cylinder(d = standoff_af / cos(30), h = standoff_len, $fn = 6);                  // M5 hex standoff
        if (standoff_shim > 0) piece("standoffs") translate([p.x, p.y, base_t + standoff_len]) color("Silver") cylinder(d = 10, h = standoff_shim, $fn = 24);   // washer shim
        piece("hardware") translate([p.x, p.y, 0]) color("DimGray") cylinder(d = 5, h = base_t + 5, $fn = 16);                                              // M5 screw from the back
    }
    translate([pos_motor.x, pos_motor.y, motor_face_z]) {
        piece("motor") color("Silver", motor_alpha) rotate(motor_rot) translate([-motor_body / 2, -motor_body / 2, 0]) cube([motor_body, motor_body, motor_len]);
        piece("motor") color("Gray") translate([0, 0, -motor_pilot_h]) cylinder(d = motor_pilot_d, h = motor_pilot_h + 0.01, $fn = 64);
        piece("shafts") color("Silver") translate([0, 0, -motor_pilot_h - motor_shaft_len]) cylinder(d = motor_shaft_d, h = motor_shaft_len + 0.01, $fn = 32);
    }
    if (show_belts)
        piece("belts") color("DimGray", 0.85) translate([0, 0, ls_belt_mid_z - ls_belt_w / 2]) linear_extrude(ls_belt_w)
            belt2d(lathe_L, pos_motor, pitch_dia(ls_teeth_screw, ls_pitch), pitch_dia(ls_teeth_motor, ls_pitch));
}
module stud_stack() {
    translate(stud_S) {
        piece("shafts") color("Silver") cylinder(d = stud_bore, h = stud_seat_z + stud_shaft_free, $fn = 48);
        piece("stud_ring") color("Peru") cylinder(d = stud_shoulder_d, h = stud_seat_z, $fn = 64);
        if (stud_spacer > 0) piece("stud_ring") color("Peru") translate([0, 0, stud_seat_z]) cylinder(d = 20, h = stud_spacer, $fn = 64);
        piece("pulley60") translate([0, 0, stud_z0]) color("LightGreen") pulley_gt2_60T();
        washer_screw(stud_front_z, stud_end_screw);
    }
}
module encoder_stack() {
    piece("pulley20gt2") translate([pos_enc.x, pos_enc.y, ep_back_z]) color("LightGreen") pulley_gt2_20T();
    translate([pos_enc.x, pos_enc.y, enc_face_z]) {
        piece("encoder") color("Silver", motor_alpha) cylinder(d = enc_body_d, h = enc_body_len, $fn = 64);
        piece("encoder") color("Gray") translate([0, 0, -eb_recess]) cylinder(d = enc_pilot_d, h = eb_recess + 0.01, $fn = 48);
        piece("shafts") color("Silver") translate([0, 0, -eb_recess - enc_shaft_len]) cylinder(d = enc_shaft_d, h = enc_shaft_len + 0.01, $fn = 32);
    }
    piece("bracket") color("SteelBlue", plate_alpha) encoder_cup();
    for (p = col_pts) piece("hardware") color("DimGray") translate([p.x, p.y, -1]) cylinder(d = 4, h = base_t + 8, $fn = 16);                              // M4 screws from the back
    if (show_belts)
        piece("belts") color("DimGray", 0.85) translate([0, 0, stud_belt_mid_z - enc_belt_w / 2]) linear_extrude(enc_belt_w)
            belt2d(stud_S, pos_enc, pitch_dia(enc_teeth_stud, enc_pitch), pitch_dia(enc_teeth_encoder, enc_pitch));
}
module base_and_bolts() {
    piece("plate") color("Goldenrod", plate_alpha) base_plate();
    for (B = [banjo_B1, banjo_B2]) {                                                                                                    // short countersunk screws into the casting
        piece("hardware") color("DimGray") translate([B.x, B.y, -12]) cylinder(d = banjo_bolt_d, h = 12 + base_t - csk_h, $fn = 24);
        piece("hardware") color("DimGray") translate([B.x, B.y, base_t - csk_h]) cylinder(d1 = banjo_bolt_d, d2 = base_head_d - 0.4, h = csk_h, $fn = 32);
    }
}
module door() {
    color("Tan", 0.25) translate([0, 0, door_depth]) difference() {
        translate([-150, panel_bottom_y, 0]) cube([150 + panel_right_x, 250 - panel_bottom_y, door_t]);
        for (w = [if (motor_cut) motor_window, if (enc_cut) enc_window]) translate([w[0], w[2], -1]) cube([w[1] - w[0], w[3] - w[2], door_t + 2]);
    }
}
module bezels() {
    if (motor_cut) piece("bezel") color("DarkSlateGray") door_bezel_at(motor_window);
    if (enc_cut) piece("bezel") color("DarkSlateGray") door_bezel_at(enc_window);
}

module scene() {
    panel_context();
    leadscrew_stack();
    motor_stack();
    stud_stack();
    encoder_stack();
    base_and_bolts();
    if (view == "side") door();
    bezels();
}
module clipped(y0, y1) intersection() { scene(); translate([-200, y0, -10]) cube([400, y1 - y0, 200]); }
// Numbers for viewer/build_viewer.py (one JSON line).
echo(str("VIEWER {\"motor_face_z\": ", motor_face_z, ", \"motor_len\": ", motor_len, ", \"enc_front_z\": ", enc_front_z,
         ", \"door_depth\": ", door_depth, ", \"plunger\": [", sw_plunger.x, ", ", sw_plunger.y, "]",
         ", \"motor_box\": ", motor_box, ", \"enc_box\": ", enc_box,
         ", \"hinge\": [", door_hinge_x, ", ", door_hinge_z, "], \"door_t\": ", door_t,
         ", \"cut_clear\": ", door_cut_clear, ", \"cable_gap\": ", door_cable_gap, ", \"cut_clear_y\": ", door_cut_clear_y, ", \"swing_margin\": ", door_swing_margin,
         ", \"door_clear\": ", door_clear, ", \"bezel\": [", bezel_w, ", ", bezel_t, ", ", bezel_r, "]",
         // axes that turn (full-machine view) and the control panel layout
         ", \"stud\": ", stud_S, ", \"enc\": ", pos_enc, ", \"motor_xy\": ", pos_motor, ", \"spindle\": ", spindle_xy,
         ", \"cb\": [", cb_w, ", ", cb_h, ", ", cb_depth, "], \"tft_pos\": ", tft_pos, ", \"tft_win\": ", tft_win,
         ", \"btn_grid\": ", btn_grid_c, ", \"btn_pitch\": ", btn_pitch, ", \"btn_d\": ", btn_hole, ", \"nut\": ", nutbtn_pos, ", \"estop\": ", estop_pos,
         ", \"estop_d\": ", estop_head_d, ", \"knob\": ", knob_pos, ", \"led\": ", led_pos, ", \"gland_x\": ", gland_x, ", \"cb_wall\": ", cb_wall, ", \"cb_post\": ", cb_post, ", \"ear\": [", ear_len, ", ", ear_w, "]}"));

if (view == "side_motor") clipped(-95, 25);
else if (view == "side_enc") clipped(stud_S.y - 35, stud_S.y + 35);
else scene();

// base_plate.scad -- FLAT base plate that replaces the change-gear banjo and carries the motor (on 4 M5 standoffs) and the encoder bracket.
//
// Frame: lathe frame (origin = leadscrew axis L, +X right, +Y up, +Z out of the panel). The plate lies on the old banjo seat, Z = 0 .. base_t,
// the 40T leadscrew pulley sits in front of it on the leadscrew's own shoulder (ls_seat_z = 17.66, measured).
//   * clamped by the old banjo bolts B1 / B2: short M5 countersunk screws in slots, +-3 mm along Y. The WHOLE plate (motor + bracket) slides
//     along Y to tension the HTD belt (a Y shift changes the horizontal GT2 belt centre by < 0.08 mm at the full +-3 mm, < 0.03 mm at the
//     ~2 mm the panel edge allows downwards: assembly.scad echoes it)
//   * clearance slot at L around the leadscrew boss (no pivot), +-3 mm along Y
//   * 4x M5 holes at the NEMA23 47.14 mm square around the motor shaft: M5 countersunk screws from the BACK into the hex standoffs
//   * hole around the motor pulley, 2x M4 holes (countersunk from the back) for the encoder bracket's inserts
//   * everything except the countersinks is on the FRONT face (B1/B2 countersinks, relief under the 40T disc, rib); the back is flat.
//
//   mode = "print"  (default) printable as modelled: back face down, no supports (the countersinks open towards the bed)
//   mode = "lathe"  same part (it is already in lathe coordinates)
//   mode = "dxf"    2D cut outline of the through holes for 6-8 mm aluminium; countersinks / relief / rib are 3D (see README)
include <params.scad>
include <lib/layout.scad>
use <lib/common.scad>

mode = "print";

Bs     = [banjo_B1, banjo_B2];
M      = pos_motor;
E      = pos_enc;
so_pts = motor_so_pts;                    // standoff screws
col_c  = E + [enc_travel / 2, 0];                                                                    // centre of the cup's +X end circle
col_pts= [for (s = [-1, 1]) col_c + (eb_out - eb_col_r + 0.8 - 1) * [cos(eb_col_ang), s * sin(eb_col_ang)]];   // = encoder_bracket.scad columns
ls_flange_r = (ls_teeth_screw * ls_pitch / PI - 2 * 0.381) / 2 + htd_flange_extra;

// ---- 2D pieces (stadia along Y: the slot shapes) --------------------------------------------------------------------------
module ystad(c, len, d) { hull() for (s = [-1, 1]) translate(c + [0, s * len / 2]) circle(d = d, $fn = 64); }

module bracket_pad_2d() {                                       // plate under the cup: the cup outline (encoder_bracket.scad) + a margin
    offset(r = base_pad_margin) hull() {
        translate(col_c) circle(r = eb_out, $fn = 96);
        translate(E + [-enc_travel / 2 - eb_left, -eb_out]) square([eb_left + enc_travel, 2 * eb_out]);
        for (p = col_pts) translate(p) circle(r = eb_col_r, $fn = 48);
    }
}
arm_a = banjo_B1 + [0, base_travel / 2];
arm_b = col_c;
arm_dir = (arm_b - arm_a) / norm(arm_b - arm_a);
arm_len = norm(arm_b - arm_a);

module outline_raw() {
    hull() {                                                    // lower body: B1 / B2 slot ends + the four standoff bosses
        for (B = Bs) ystad(B, base_travel, 2 * base_boss_r);
        for (p = so_pts) translate(p) circle(r = standoff_boss_r, $fn = 48);
    }
    hull() { translate(arm_a) circle(r = base_arm_w / 2, $fn = 48); translate(arm_b) circle(r = base_arm_w / 2, $fn = 48); }   // arm to the bracket
    bracket_pad_2d();
}
module outline_2d() {
    intersection() {
        offset(r = 2) offset(delta = -2) outline_raw();                     // soften convex corners
        translate([-400, plate_y_min]) square([400 + plate_x_max, 800]);    // 2 mm inside the bottom / right panel edges
    }
}

module windows_2d() {                                           // lightening window along the arm
    t0 = base_boss_r + 10 + base_window_w / 2;
    t1 = arm_len - (eb_out + base_pad_margin + 6) - base_window_w / 2;
    if (t1 > t0) hull() for (t = [t0, t1]) translate(arm_a + arm_dir * t) circle(d = base_window_w, $fn = 48);
}

module m5_hole_2d() {
    if (base_m5 == "csk") circle(d = m5_clear + 0.1, $fn = 32);
    else if (base_m5 == "tap") circle(d = 4.2, $fn = 32);
    else circle(d = 6.4, $fn = 32);
}

// through holes (2D)
module holes_2d() {
    for (B = Bs) ystad(B, base_travel, banjo_bolt_d + base_bolt_clear);        // B1 / B2: bolt slots, +-3 mm along Y
    ystad(lathe_L, base_travel, ls_boss_d + 2 * ls_boss_clear);                // clearance around the leadscrew boss (+-3 mm along Y)
    for (p = so_pts) translate(p) m5_hole_2d();                                // M5 standoff screws
    translate(M) circle(d = mp_buy_flange_d + mp_hole_clear, $fn = 96);        // motor pulley (flange sits just below the plate front face)
    for (p = col_pts) translate(p) circle(d = m4_clear, $fn = 32);             // encoder bracket M4
    windows_2d();
}

// ---- front-face rib: only where it cannot hit the 40T disc, the HTD belt, the motor pulley, bolt heads or the bracket --------------------
module rib_2d() {
    difference() {
        outline_2d();
        offset(delta = -base_rib_t) outline_2d();
        hull() { ystad(lathe_L, base_travel, 2 * (belt_env_r + 3)); ystad(M, base_travel, mp_buy_flange_d + 8); }   // HTD belt footprint over the +-3 slide
        for (B = Bs) ystad(B, base_travel, 2 * (base_boss_r + 1));
        for (p = so_pts) translate(p) circle(r = standoff_boss_r + 1);
        offset(delta = 1) bracket_pad_2d();
    }
}

module back_csk(d, D) { translate([0, 0, -0.01]) cylinder(d1 = D, d2 = d, h = (D - d) / 2 + 0.01, $fn = 48); }

module base_plate() {
    difference() {
        union() {
            linear_extrude(base_t) outline_2d();
            translate([0, 0, base_t - 0.01]) linear_extrude(base_rib_h + 0.01) rib_2d();
        }
        translate([0, 0, -1]) linear_extrude(base_t + base_rib_h + 2) holes_2d();
        // relief under the 40T disc (front face), so the pulley's back flange never touches the plate
        translate([0, 0, base_t - base_relief]) linear_extrude(base_relief + 1) ystad(lathe_L, base_travel, 2 * (ls_flange_r + 1.5));
        // B1 / B2: countersunk head seats (flush with the front face), swept along the slot
        for (B = Bs)
            hull() for (s = [-1, 1])
                translate([B.x, B.y + s * base_travel / 2, base_t]) rotate([180, 0, 0]) back_csk(banjo_bolt_d + base_bolt_clear, base_head_d);
        // M5 and M4 countersinks on the BACK face
        if (base_m5 == "csk") for (p = so_pts) translate([p.x, p.y, 0]) back_csk(m5_clear + 0.1, 10.4);
        for (p = col_pts) translate([p.x, p.y, 0]) back_csk(m4_clear, 8.4);
    }
}

module plate_2d() difference() { outline_2d(); holes_2d(); }

if (mode == "dxf") plate_2d();
else base_plate();

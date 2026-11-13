// control_box.scad -- front panel + frame + lid for the ELS controller.
//
//   part = "panel"       front panel, printed FRONT FACE DOWN (labels engraved)       PRINT 1
//   part = "frame"       open frame (4 walls, corner screw blocks, PG7 holes, ears)     PRINT 1, rear face down
//   part = "lid"         rear lid with Teensy perfboard standoffs, outer face down       PRINT 1
//   part = "panel_view"  panel in design orientation (front up) for previews
//   part = "all"         exploded assembly for checking alignment
//
// Assembled frame coordinates: origin at the centre of the front rim of the frame,
// +Z towards the back, viewer stands at -Z. All dimensions are in params.scad.
//   panel   z = -cb_panel_t .. 0         (4x M3 flat head into the corner blocks)
//   frame   z = 0 .. cb_depth
//   lid     z = cb_depth-cb_lid_t .. cb_depth, sits in the rear rebate (4x M3 flat head)
//
// Panel layout is defined in FRONT VIEW coordinates (x right, y up, origin at panel centre).
include <params.scad>
use <lib/common.scad>

part = "all";

W = cb_w; H = cb_h; D = cb_depth;
iw = W - 2 * cb_wall; ih = H - 2 * cb_wall;
pcx = iw / 2 - cb_post / 2;          // screw block centre
pcy = ih / 2 - cb_post / 2;
post_pts = [for (sx = [-1, 1], sy = [-1, 1]) [sx * pcx, sy * pcy]];
fn_ = 48;

module outer2d() rrect2(W, H, cb_corner_r);
module inner2d() rrect2(iw, ih, max(cb_corner_r - cb_wall, 1));

// ---------------------------------------------------------------- panel ----
grid_names = [["MODE", "UNITS", "DIR"],
              ["JOG <", "RETURN", "JOG >"],
              ["STOP L", "", "STOP R"]];   // centre bottom = spare (hole cut, no label)

function grid_pt(r, c) = [btn_grid_c.x + (c - 1) * btn_pitch.x, btn_grid_c.y + (1 - r) * btn_pitch.y];

module label(txt, pos, size = label_size) {
    translate([pos.x, pos.y, cb_panel_t - label_depth])
        linear_extrude(label_depth + 0.05)
            text(txt, size = size, font = label_font, halign = "center", valign = "top");
}

// front face = +Z (z = cb_panel_t), back face z = 0, TFT posts rise to -Z
module panel_design() {
    tft_ll = tft_pos - tft_pcb / 2;                       // PCB lower-left on the panel
    win_ll = tft_ll + tft_win_off - [tft_win_margin, tft_win_margin];
    difference() {
        union() {
            linear_extrude(cb_panel_t) outer2d();
            for (sx = [-1, 1], sy = [-1, 1])
                translate([tft_pos.x + sx * tft_holes.x / 2, tft_pos.y + sy * tft_holes.y / 2, -tft_stack_h])
                    cylinder(d = tft_post_d, h = tft_stack_h + 0.01, $fn = fn_);
        }
        // TFT post pilot holes (stop 1.2 mm short of the front face)
        for (sx = [-1, 1], sy = [-1, 1])
            translate([tft_pos.x + sx * tft_holes.x / 2, tft_pos.y + sy * tft_holes.y / 2, -tft_stack_h - 1])
                cylinder(d = m3_hole, h = tft_stack_h + cb_panel_t - 1.2 + 1, $fn = 24);
        // TFT window
        translate([win_ll.x, win_ll.y, -1])
            cube([tft_win.x + 2 * tft_win_margin, tft_win.y + 2 * tft_win_margin, cb_panel_t + 2]);
        // 3x3 push buttons + labels
        for (r = [0 : 2], c = [0 : 2]) {
            p = grid_pt(r, c);
            translate([p.x, p.y, -1]) cylinder(d = btn_hole, h = cb_panel_t + 2, $fn = 64);
            if (grid_names[r][c] != "") label(grid_names[r][c], [p.x, p.y - btn_hole / 2 - 1.5]);
        }
        // NUT button
        translate([nutbtn_pos.x, nutbtn_pos.y, -1]) cylinder(d = nutbtn_hole, h = cb_panel_t + 2, $fn = 64);
        label("NUT", [nutbtn_pos.x, nutbtn_pos.y - 14 - 2], label_size + 0.8);
        // E-stop
        translate([estop_pos.x, estop_pos.y, -1]) cylinder(d = estop_hole, h = cb_panel_t + 2, $fn = 64);
        label("E-STOP", [estop_pos.x, estop_pos.y - 14 - 6]);
        // FAULT LED (panel LED with holder)
        translate([led_pos.x, led_pos.y, -1]) cylinder(d = led_hole, h = cb_panel_t + 2, $fn = 40);
        label("FAULT", [led_pos.x, led_pos.y - led_hole / 2 - 1.5]);
        // EC11 knob: 7 mm hole + blind anti-rotation slot from the back (leaves a 1.2 mm skin)
        translate([knob_pos.x, knob_pos.y, -1]) cylinder(d = knob_hole, h = cb_panel_t + 2, $fn = 48);
        translate([knob_pos.x - knob_tab_w / 2, knob_pos.y, -1])
            cube([knob_tab_w, knob_hole / 2 + knob_tab_l, cb_panel_t - 1.2 + 1]);
        label("PITCH / JOG", [knob_pos.x, knob_pos.y - 14]);
        // corner screws, flat head from the front
        for (p = post_pts) translate([p.x, p.y, cb_panel_t]) rotate([180, 0, 0]) countersink(m3_clear, 6.4, cb_panel_t + 1);
    }
}

// assembled: front face towards -Z, back face at z = 0, posts into the frame (+Z)
module panel_assembled() rotate([0, 180, 0]) panel_design();
// print orientation: front face on the bed
module panel_print() translate([0, 0, cb_panel_t]) rotate([180, 0, 0]) panel_design();

// ---------------------------------------------------------------- frame ----
module ear_2d() {
    // ear plate extends to +X of the wall; local x = 0 at the outer wall face
    translate([-cb_wall, -ear_w / 2]) square([ear_len + cb_wall, ear_w]);
}

module ear() {   // +X side ear, flush with the rear rim (z = D)
    ear_t = magnet_h + 1.0;
    rib_y = ear_w / 2 - 1.25;
    difference() {
        union() {
            translate([W / 2, 0, D - ear_t]) linear_extrude(ear_t) ear_2d();
            // two ribs along the free edges (print upright, no overhang)
            for (s = [-1, 1])
                translate([W / 2, s * rib_y - 1.25, D - ear_t - 5]) cube([ear_len - 4, 2.5, 5 + 0.01]);
        }
        // M6 arm hole
        translate([W / 2 + ear_len - 6, 0, D - ear_t - 6]) cylinder(d = ear_hole, h = ear_t + 8, $fn = 40);
        // magnet pocket, open to the front, 1 mm skin at the rear face
        translate([W / 2 + 3 + magnet_d / 2 + 0.5, 0, D - ear_t - 0.01]) cylinder(d = magnet_d, h = magnet_h + 0.01, $fn = 64);
    }
}

module frame() {
    difference() {
        union() {
            linear_extrude(D) difference() { outer2d(); inner2d(); }
            // corner screw blocks (stop one lid thickness short of the rear face)
            for (p = post_pts)
                linear_extrude(D - cb_lid_t) intersection() {
                    outer2d();
                    translate(p) square(cb_post + 1, center = true);
                }
            ear();
            mirror([1, 0, 0]) ear();
        }
        // M3 holes for panel (front) and lid (rear)
        for (p = post_pts) {
            translate([p.x, p.y, -1]) cylinder(d = m3_hole, h = 9, $fn = 24);
            translate([p.x, p.y, D - cb_lid_t - 8]) cylinder(d = m3_hole, h = 9, $fn = 24);
        }
        // PG7 cable glands in the bottom wall: front-view x positions (viewer at -Z => x_assembled = -x_front)
        for (gx = gland_x)
            translate([-gx, -H / 2 - 1, gland_z]) rotate([-90, 0, 0]) cylinder(d = gland_d, h = cb_wall + 2, $fn = 48);
    }
}
// print orientation: rear face on the bed
module frame_print() translate([0, 0, D]) rotate([180, 0, 0]) frame();

// ------------------------------------------------------------------ lid ----
module lid_design() {   // outer face z = 0 (bed), inner face z = cb_lid_t, standoffs rise
    c = cb_lid_clear;
    difference() {
        union() {
            linear_extrude(cb_lid_t) rrect2(iw - 2 * c, ih - 2 * c, 1.5);
            for (sx = [-1, 1], sy = [-1, 1])
                translate([perf_pos.x + sx * perf_holes.x / 2, perf_pos.y + sy * perf_holes.y / 2, cb_lid_t - 0.01])
                    cylinder(d = perf_stand_d, h = perf_stand_h + 0.01, $fn = 32);
        }
        for (sx = [-1, 1], sy = [-1, 1])
            translate([perf_pos.x + sx * perf_holes.x / 2, perf_pos.y + sy * perf_holes.y / 2, cb_lid_t])
                cylinder(d = m25_hole, h = perf_stand_h + 1, $fn = 24);
        for (p = post_pts) translate([p.x, p.y, 0]) countersink(m3_clear, 6.4, cb_lid_t + 1);
    }
}
module lid_assembled() translate([0, 0, D]) rotate([0, 180, 0]) lid_design();

// ------------------------------------------------------------- dispatch ----
if (part == "panel") panel_print();
else if (part == "frame") frame_print();
else if (part == "lid") lid_design();
else if (part == "panel_view") panel_design();
// assembled pieces in place (frame coordinates above), for the 3D viewer (viewer/build_viewer.py)
else if (part == "panel_asm") panel_assembled();
else if (part == "frame_asm") frame();
else if (part == "lid_asm") lid_assembled();
else if (part == "all") {
    color("DimGray") translate([0, 0, -30]) panel_assembled();
    color("Silver") frame();
    color("SlateGray") translate([0, 0, 30]) lid_assembled();
}

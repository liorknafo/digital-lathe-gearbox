// encoder_bracket.scad -- printed C-cup for the LPD3806-600BM encoder, bolted to the base plate with 2x M4 (heat-set inserts in the columns).
//
// The cup rises from the base plate front face (Z = base_t) round the encoder's 20T GT2 pulley. Its TOP FACE (Z = enc_face_z) carries the encoder:
// 3x M3 on the 30 mm PCD, a 20 mm pilot recess and the shaft slot, all slotted +-4 mm along X for GT2
// tension (M3 pan heads + washers bear on the flat underside, 2.4 mm under the belt's top edge, inside the cup). The cup is OPEN on the side facing the stud (-X) so the belt runs in and out; the walls (5 mm) and two solid M4 columns are on
// the +X end. enc_face_z is computed (lib/layout.scad) so the 20T teeth line up with the stud's 60T teeth given the 13 mm encoder shaft.
//
// Print: encoder face DOWN on the bed (mode = "print", the default). Everything above it is vertical wall, columns and a flat top: no supports.
// Fasteners: 2x M4 heat-set inserts (M4 x 5.7) pressed into the column ends (the top in the print), 2x M4 countersunk screws from the BACK of the
// base plate; 3x M3 x 10 pan head + washer from the cup inside into the encoder.
include <params.scad>
include <lib/layout.scad>
use <lib/common.scad>

mode = "print";            // "print" (face down) | "lathe"

E      = pos_enc;
c_r    = E + [enc_travel / 2, 0];
col_pts= [for (s = [-1, 1]) c_r + (eb_out - eb_col_r + 0.8 - 1) * [cos(eb_col_ang), s * sin(eb_col_ang)]];
enc_pts= [for (i = [0 : 2]) E + (enc_hole_pcd / 2) * [cos(enc_hole_angle + 120 * i), sin(enc_hole_angle + 120 * i)]];

// right end: circle round the +X slot end; left end: squared off eb_left beyond the -X slot end, OPEN (no end wall) so the belt passes
module cup_shape(r) {
    hull() {
        translate(E + [enc_travel / 2, 0]) circle(r = r, $fn = 96);
        translate(E + [-enc_travel / 2 - eb_left, -r]) square([eb_left + enc_travel, 2 * r]);
    }
}
module outline_2d() { hull() { cup_shape(eb_out); for (p = col_pts) translate(p) circle(r = eb_col_r, $fn = 48); } }
module walls_2d() {
    union() {
        difference() {
            outline_2d();
            hull() {                                                       // inside, extended past the open end
                translate(E + [enc_travel / 2, 0]) circle(r = eb_in, $fn = 96);
                translate(E + [-enc_travel / 2 - eb_left - 1, -eb_in]) square([eb_left + enc_travel + 1, 2 * eb_in]);
            }
        }
        for (p = col_pts) translate(p) circle(r = eb_col_r, $fn = 48);
    }
}
module xslot(p, d) { hull() for (s = [-1, 1]) translate([p.x + s * enc_travel / 2, p.y]) circle(d = d, $fn = 48); }   // stadium along X

module encoder_cup() {
    difference() {
        union() {
            translate([0, 0, eb_under_z]) linear_extrude(eb_top_t) outline_2d();                         // top plate = encoder face at its top
            translate([0, 0, base_t]) linear_extrude(eb_under_z - base_t + 0.01) walls_2d();              // walls + columns down to the base plate
        }
        // shaft slot through the plate, +-4 mm along X
        translate([0, 0, eb_under_z - 1]) linear_extrude(eb_top_t + 2) xslot(E, enc_shaft_d + 1);
        // 20 mm pilot recess in the top face, slotted the same way
        translate([0, 0, enc_face_z - eb_recess]) linear_extrude(eb_recess + 1) xslot(E, enc_pilot_d + 0.6);
        // 3x M3 on the 30 mm PCD, +-4 mm along X: pan head + washer from the cup inside onto the flat underside (no countersink)
        for (p = enc_pts) translate([0, 0, eb_under_z - 1]) linear_extrude(eb_top_t + 2) xslot(p, m3_clear);
        // heat-set M4 inserts, pressed in from the base end
        for (p = col_pts) translate([p.x, p.y, base_t - 0.01]) cylinder(d = eb_insert_d, h = eb_insert_depth, $fn = 32);
    }
}

echo(str("encoder_bracket: top (encoder) face Z = ", round(enc_face_z * 100) / 100, ", height above the base plate ", round(eb_h * 100) / 100, " mm, open towards -X, ",
         "outline ", round((eb_left + enc_travel + eb_out) * 10) / 10, " x ", round(2 * eb_out * 10) / 10, " mm"));

if (mode == "lathe") encoder_cup();
else translate([-E.x, E.y, enc_face_z]) rotate([180, 0, 0]) encoder_cup();      // face down on the bed

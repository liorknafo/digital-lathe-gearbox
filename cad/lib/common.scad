// lib/common.scad -- small shared helpers (2D shapes, nut pockets, fastener data).
// `use <lib/common.scad>`

eps_c = 0.01;

// ---- fastener data ----------------------------------------------------------
// [thread d, nut across-flats, nut thickness, clearance hole, self-tap pilot, head d, head height]
function _screw_row(s) =
    s == "M2.5" ? [2.5,  5.0, 2.0, 2.8, 2.2,  4.5, 2.5] :
    s == "M3"   ? [3.0,  5.5, 2.4, 3.4, 2.7,  5.5, 3.0] :
    s == "M4"   ? [4.0,  7.0, 3.2, 4.4, 3.6,  7.0, 4.0] :
    s == "M5"   ? [5.0,  8.0, 4.0, 5.4, 4.5,  8.5, 5.0] :
    s == "M6"   ? [6.0, 10.0, 5.0, 6.6, 5.4, 10.0, 6.0] :
    s == "M8"   ? [8.0, 13.0, 6.5, 8.4, 7.2, 13.0, 8.0] :
                  [3.0,  5.5, 2.4, 3.4, 2.7,  5.5, 3.0];
function sc_d(s)     = _screw_row(s)[0];
function sc_nut_af(s)= _screw_row(s)[1];
function sc_nut_t(s) = _screw_row(s)[2];
function sc_clear(s) = _screw_row(s)[3];
function sc_tap(s)   = _screw_row(s)[4];
function sc_head_d(s)= _screw_row(s)[5];
function sc_head_h(s)= _screw_row(s)[6];

// ---- 2D helpers -------------------------------------------------------------
// Rounded rectangle centred on the origin
module rrect2(w, h, r = 2) {
    rr = min(r, min(w, h) / 2 - 0.01);
    offset(r = rr) square([w - 2 * rr, h - 2 * rr], center = true);
}

// Slot (stadium): two circles of diameter d, centres `cc` apart along X, centred on origin
module slot2(cc, d) {
    hull() {
        translate([-cc / 2, 0]) circle(d = d);
        translate([ cc / 2, 0]) circle(d = d);
    }
}

// ---- 3D helpers -------------------------------------------------------------
// Captive nut pocket with a slide-in slot.
// Local frame: nut axis = +Z (pocket spans z = 0 .. t), slot runs towards +Y, centred on X = 0.
// Flats are at X = +-af/2 so the nut slides straight along +Y.
module nut_pocket(af, t, slot_len, clr = 0.15) {
    a = af + 2 * clr;
    linear_extrude(height = t + clr) {
        rotate(30) circle(d = a / cos(30), $fn = 6);
        translate([-a / 2, 0]) square([a, slot_len]);
    }
}

// Cone-ended countersunk hole for a flat-head screw. Axis +Z, head face at z = 0, shank goes up.
module countersink(d_shank, d_head, h_total) {
    ch = (d_head - d_shank) / 2;
    translate([0, 0, -eps_c]) cylinder(d1 = d_head + 2 * eps_c, d2 = d_shank, h = ch + eps_c);
    cylinder(d = d_shank, h = h_total);
}

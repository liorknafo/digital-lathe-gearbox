// lib/pulley_core.scad -- generic toothed belt pulley (HTD-3M or GT2), axis = Z.
//
// Print orientation (what this module outputs): bottom flange on the bed (z = 0),
// toothed section, top flange (45 deg underside so it prints without support),
// hub on top.  Bore, keyway/D-flat and set-screw/clamp features are cut in.
//
//   z = 0 .. bt                     bottom flange (optional)
//   bt .. bt+tooth_len              toothed section
//   .. + ft                         top flange (optional, 45 deg chamfered underside)
//   .. + hub_len                    hub (set-screw nut trap opens out of its top face)
//
// Set screw: radial hole along +X, nut pocket slides in from the top face (+Z).
// Keyway (if any) is at key_angle (90 = +Y); a D-flat (if any) is on the +X side so the
// set screw bears on it.
use <common.scad>
use <teeth.scad>
eps_c = 0.01;   // (variables are not exported by `use`, so each lib defines its own)

function pc_bt(bottom_flange, flange_t) = bottom_flange ? flange_t : 0;
function pc_ft(top_flange, flange_t, flange_extra) = top_flange ? max(flange_t, flange_extra) : 0;
function pc_height(tooth_len, flange_t, flange_extra, bottom_flange, top_flange, hub_len) =
    pc_bt(bottom_flange, flange_t) + tooth_len + pc_ft(top_flange, flange_t, flange_extra) + hub_len;
function pc_belt_mid(tooth_len, flange_t, bottom_flange) = pc_bt(bottom_flange, flange_t) + tooth_len / 2;

// 2D bore profile: round bore + optional D-flat (+X side) + optional keyway
module pc_bore_2d(bore_d, fit, flat_depth, keyway_w, keyway_h, key_angle) {
    br = bore_d / 2 + fit;
    intersection() {
        circle(r = br, $fn = $coarse ? 32 : 96);
        if (flat_depth > 0)
            translate([-br - 1, -br - 1]) square([br + 1 + (bore_d / 2 - flat_depth + fit), 2 * br + 2]);
        else
            square(4 * br, center = true);
    }
    if (keyway_w > 0)
        rotate(key_angle - 90)
            translate([-(keyway_w + 2 * fit) / 2, 0]) square([keyway_w + 2 * fit, br + keyway_h + fit]);
}

module belt_pulley(
        n, profile = "htd3m",
        tooth_len = 16,
        bore_d = 8, fit = 0.15,
        flange_t = 1.2, flange_extra = 1.5,
        bottom_flange = true, top_flange = true,
        hub_d = 20, hub_len = 8,
        hub_mode = "setscrew",        // "setscrew" | "clamp" | "none"
        screw = "M4",
        screw_z = undef,              // override set-screw height (hubless pulleys)
        keyway_w = 0, keyway_h = 1.4, key_angle = 90,
        flat_depth = 0,
        tooth_extra = 0.1, tooth_phase = 0) {

    od   = pulley_od(n, profile);
    fl_d = od + 2 * flange_extra;
    bt   = pc_bt(bottom_flange, flange_t);
    ft   = pc_ft(top_flange, flange_t, flange_extra);
    z1   = bt + tooth_len;            // top of toothed section
    zh   = z1 + ft;                   // hub starts here
    br   = bore_d / 2 + fit;
    af   = sc_nut_af(screw);
    nt   = sc_nut_t(screw) + 0.2;
    // smallest hub that still leaves wall around the screw features
    hd_min = hub_mode == "clamp" ? 2 * (br + 1.5 + af / 2 + sc_head_d(screw) / 2 + 2.0)
                                 : 2 * (br + 1.0 + nt + 2.0);
    hd     = hub_len > 0 ? max(hub_d, hd_min) : 0;
    base_d = top_flange ? fl_d : od;
    cone_h = (hub_len > 0 && hd > base_d) ? min((hd - base_d) / 2, hub_len * 0.7) : 0;
    total_h = zh + hub_len;
    zc = is_undef(screw_z) ? zh + cone_h + (hub_len - cone_h) / 2 : screw_z;
    rout = max(hd, fl_d) / 2 + 1;

    difference() {
        union() {
            if (bottom_flange) cylinder(d = fl_d, h = flange_t, $fn = $coarse ? 48 : 128);
            translate([0, 0, bt - eps_c])
                linear_extrude(height = tooth_len + 2 * eps_c)
                    tooth_ring(n, profile, tooth_extra, tooth_phase);
            if (top_flange) translate([0, 0, z1 - eps_c]) {
                cylinder(d1 = od, d2 = fl_d, h = flange_extra + eps_c, $fn = $coarse ? 48 : 128);
                if (ft > flange_extra)
                    translate([0, 0, flange_extra]) cylinder(d = fl_d, h = ft - flange_extra + eps_c, $fn = $coarse ? 48 : 128);
            }
            if (hub_len > 0) translate([0, 0, zh - eps_c]) {
                if (cone_h > 0) cylinder(d1 = base_d, d2 = hd, h = cone_h + eps_c, $fn = $coarse ? 48 : 128);
                translate([0, 0, cone_h]) cylinder(d = hd, h = hub_len - cone_h + eps_c, $fn = $coarse ? 48 : 128);
            }
        }

        // bore, D-flat and keyway
        translate([0, 0, -1])
            linear_extrude(height = total_h + 2)
                pc_bore_2d(bore_d, fit, flat_depth, keyway_w, keyway_h, key_angle);

        // set screw with captive nut trap (nut slides in from the top face)
        if (hub_mode == "setscrew") {
            translate([0, 0, zc]) rotate([0, 90, 0]) cylinder(d = sc_clear(screw), h = rout, $fn = 32);
            translate([br + 1.0, 0, zc]) rotate([90, 0, 90])
                nut_pocket(af, nt, slot_len = total_h - zc + 1);
        }

        // split hub clamp: slit on +X, cross screw along Y, nut pocket on the +Y side
        if (hub_mode == "clamp" && hub_len > 0) {
            xs = br + 1.5 + af / 2;
            translate([0, -0.5, zh - eps_c]) cube([hd, 1.0, hub_len + 1]);
            translate([xs, 0, zc]) rotate([90, 0, 0]) cylinder(d = sc_clear(screw), h = hd + 2, center = true, $fn = 32);
            translate([xs, -4.0, zc]) rotate([90, 0, 0]) cylinder(d = sc_head_d(screw) + 0.6, h = hd, $fn = 32);
            translate([xs, 2.0, zc])
                multmatrix([[-1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 1]])
                    nut_pocket(af, nt, slot_len = total_h - zc + 1);
        }
    }
}

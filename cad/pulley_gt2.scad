// pulley_gt2.scad -- GT2 (2 mm pitch) 6 mm belt pulleys for the encoder drive.
//
//   part = "60T"  stud pulley, bore stud_bore + keyway (14 mm / 4 mm key, from the photos); held by the stud-end screw + washer   [default]
//   part = "20T"  printable 20T encoder pulley, 6 mm bore (+ D-flat) + M3 set screw: variant of the bought 6 mm-bore 20T
//
// Orientation: bottom flange on the bed, hub up (print as-is, no supports). On the lathe the flange side faces the casting and the HUB
// FACES THE DOOR (the 60T: the hub front face is the flat for the stud screw's washer; the 20T: the hub sits in the plate's pilot slot).
include <params.scad>
include <lib/layout.scad>
use <lib/pulley_core.scad>
use <lib/common.scad>
use <lib/teeth.scad>

part = "60T";

module pulley_gt2_60T() {
    belt_pulley(n = enc_teeth_stud, profile = "gt2", tooth_len = gt2_tooth_len,
        bore_d = stud_bore, fit = tol,
        flange_t = gt2_flange_t, flange_extra = gt2_flange_extra,
        hub_d = stud_hub_d, hub_len = stud_hub_len,
        hub_mode = stud_setscrew ? "setscrew" : "none", screw = "M3",
        keyway_w = stud_keyway_w, keyway_h = stud_keyway_h, key_angle = 90,
        tooth_extra = gt2_groove_extra);
}

module pulley_gt2_20T() {
    belt_pulley(n = enc_teeth_encoder, profile = "gt2", tooth_len = gt2_tooth_len,
        bore_d = enc_shaft_d, fit = tol,
        flange_t = gt2_flange_t, flange_extra = gt2_flange_extra,
        bottom_flange = true, top_flange = false,      // hub side acts as the second flange
        hub_d = ep_hub_d, hub_len = ep_hub_len,
        hub_mode = "setscrew", screw = "M3",
        flat_depth = enc_shaft_flat,
        tooth_extra = gt2_groove_extra);
}

if (part == "60T") pulley_gt2_60T();
else if (part == "20T") pulley_gt2_20T();

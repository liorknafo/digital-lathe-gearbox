// pulley_htd3m.scad -- HTD-3M pulley generator (15 mm belt).
//
//   part = "40T"   leadscrew pulley, bore ls_shaft_bore + keyway (14 mm / 4 mm key, from the photos)   [default]
//   part = "20T"   printable 20T motor pulley, 8 mm bore with D-flat + M4 set screw: BACKUP for the bought aluminium 20T
//
// Render:  openscad -D 'part="20T"' -o 20T.stl pulley_htd3m.scad
// Tooth profile: see lib/teeth.scad (round-tooth approximation, groove 1.14 mm deep).
// Orientation: bottom flange on the bed, hub up (print as-is, no supports). On the lathe the flange side faces the casting and the HUB
// FACES THE DOOR: the hub's flat front face is where the leadscrew-end screw + washer clamp the pulley (no set screw needed;
// ls_setscrew = true adds an M4 set screw + nut trap, which needs a longer hub than the shaft allows).
include <params.scad>
include <lib/layout.scad>
use <lib/pulley_core.scad>
use <lib/teeth.scad>

part = "40T";

module pulley_htd3m_40T() {
    belt_pulley(n = ls_teeth_screw, profile = "htd3m", tooth_len = htd_tooth_len,
        bore_d = ls_shaft_bore, fit = tol,
        flange_t = htd_flange_t, flange_extra = htd_flange_extra,
        hub_d = ls_hub_d, hub_len = ls_hub_len,
        hub_mode = ls_setscrew ? "setscrew" : "none", screw = "M4",
        keyway_w = ls_keyway_w, keyway_h = ls_keyway_h, key_angle = 90,
        tooth_extra = htd_groove_extra);
}

// 20T printable motor pulley (8 mm shaft with D-flat); flange on the casting side, hub towards the motor
module pulley_htd3m_20T() {
    belt_pulley(n = ls_teeth_motor, profile = "htd3m", tooth_len = mp_tooth_len,
        bore_d = motor_shaft_d, fit = tol,
        flange_t = htd_flange_t, flange_extra = htd_flange_extra,
        bottom_flange = true, top_flange = false,      // hub side acts as the second flange
        hub_d = mp_hub_d, hub_len = mp_hub_len,
        hub_mode = "setscrew", screw = "M4",
        flat_depth = motor_shaft_flat,
        tooth_extra = htd_groove_extra);
}

if (part == "40T") pulley_htd3m_40T();
else if (part == "20T") pulley_htd3m_20T();

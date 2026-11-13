// lib/teeth.scad -- belt-tooth pulley profiles (2D) for HTD-3M and GT2.
//
// PROFILE NOTES (these are approximations good for FDM printing, not tooling-grade):
//
//  HTD 3M  (pitch 3.00 mm, belt tooth height 1.22 mm, tooth radius ~1.0 mm)
//    * Pulley OD = N*3/pi - 2*0.381  (pitch-line differential 0.381 mm).
//    * Each groove is a circle of radius 1.0 mm (+ `extra` clearance) whose centre sits
//      0.14 mm below the OD surface, i.e. 1.14 mm deep and ~1.98 mm wide at the OD,
//      with straight sides continuing out of the surface. The 1.02 mm lands between
//      grooves are left sharp.  This is the classic "round tooth" shape of HTD.
//
//  GT2  (pitch 2.00 mm, belt tooth height 0.75 mm)
//    * Pulley OD = N*2/pi - 2*0.254  (PLD 0.254 mm).
//    * Each groove is a circle of radius 0.60 mm (+ `extra`) centred 0.15 mm below the OD
//      (0.75 mm deep) hulled with a 1.4 mm wide mouth at the OD, which gives the flared
//      GT2 "rounded trapezoid" opening.
//
//  `extra` (default 0.1 mm) widens/deepens the groove to compensate for print inaccuracy.
//  Dimensions follow commonly published pulley data (Gates / SDP-SI).  Test-print one
//  pulley and increase `extra` if the belt is tight, decrease if it skips.

function htd3m_od(n) = n * 3 / PI - 2 * 0.381;
function gt2_od(n)   = n * 2 / PI - 2 * 0.254;
function pulley_od(n, profile) = profile == "htd3m" ? htd3m_od(n) : gt2_od(n);
function profile_pitch(profile) = profile == "htd3m" ? 3 : 2;

// Groove cut, 2D. y = 0 is the OD surface, the groove goes into -y, open towards +y.
module htd3m_groove(extra = 0.1) {
    r = 1.0 + extra;
    translate([0, -(1.14 - 1.0)]) circle(r = r, $fn = $coarse ? 10 : 36);       // round bottom
    translate([-r, -(1.14 - 1.0)]) square([2 * r, 0.14 + 0.6]);  // straight sides to the surface
}
module gt2_groove(extra = 0.1) {
    r = 0.60 + extra;
    hull() {
        translate([0, -(0.75 - 0.60)]) circle(r = r, $fn = $coarse ? 8 : 28);
        translate([-0.7 - extra, 0]) square([1.4 + 2 * extra, 0.6]);
    }
}

// Full toothed disc (2D). `phase` rotates the whole ring (deg).
module tooth_ring(n, profile, extra = 0.1, phase = 0) {
    od = pulley_od(n, profile);
    rotate(phase)
    difference() {
        circle(d = od, $fn = $coarse ? n * 2 : max(n * 6, 180));
        for (i = [0 : n - 1])
            rotate(i * 360 / n) translate([0, od / 2]) {
                if (profile == "htd3m") htd3m_groove(extra);
                else gt2_groove(extra);
            }
    }
}

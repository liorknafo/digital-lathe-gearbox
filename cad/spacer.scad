// spacer.scad -- the one printed spacer left: the 3 mm ring on the change-gear stud behind the 60T pulley.
//
//   part = "stud_collar"   ring ID stud_bore + 0.6 / OD 20 / length stud_spacer: lifts the 60T's back face past the spindle bearing cap.
//                          Only needed if the cap stands out past stud_seat_z (22); stud_spacer = 0 (default) = no ring.
//
// The old L-shaped plate spacers and the leadscrew collar are gone: the flat base plate (base_plate.scad, 8 mm) takes over the banjo's thickness,
// so the 40T sits directly in front of it. Washers (stud_bore, 3 mm stack) or a steel spacer work as well.
include <params.scad>
include <lib/layout.scad>

part = "stud_collar";

module ring(id, od, len) {
    difference() { cylinder(d = od, h = len, $fn = 96); translate([0, 0, -1]) cylinder(d = id, h = len + 2, $fn = 64); }
}

if (part == "stud_collar" && stud_spacer > 0) ring(stud_bore + 0.6, 20, stud_spacer);

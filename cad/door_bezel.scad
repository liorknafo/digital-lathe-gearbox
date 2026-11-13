// door_bezel.scad -- printed trim frame for the window cut in the change-gear door where the motor pokes through.
//
// The motor sticks out past the closed door, so the door gets a window (lib/layout.scad: motor_window). The window edge away
// from the hinge leaves the room the door needs to swing past the motor's back corner; the other three edges are tight.
// This frame sits on the door's OUTSIDE face, held by M3 screws + nyloc nuts through the door. It covers the cut edge,
// stiffens the sheet round the hole, and carries a seal: glue a self-adhesive brush strip (or soft foam) to the inside
// of the opening so it closes the far-side swing gap. Brush bristles just bend as the door swings past the motor.
// The frame is trimmed to the door's edges (the window sits close to the bottom fold), and screw holes are only placed where
// there is sheet behind them.
//
// It is also the CUTTING TEMPLATE: tension the belts, close the door gently onto the motor's back with a dab of paint on its
// corners, line the bezel up on the marks (the wider gap on the side away from the hinge), scribe the opening and drill the
// holes. mode = "template" exports the opening + holes as a 1:1 DXF.
//
// Print: flat (mode = "print", the default). No supports.
include <params.scad>
include <lib/layout.scad>

mode = "print";            // "print" | "lathe" (in place on the closed door) | "template" (2D: opening + holes, 1:1)
which = "motor";           // "motor" | "encoder" (only needed if the encoder pokes through too)

hole_edge_min = 5;         // screw hole centre to the door's edge, at least (mm)

module rrect(c, size, r) {
    rr = min(r, min(size) / 2 - 0.01);
    translate(c) offset(r = rr, $fn = 32) square(size - 2 * [rr, rr], center = true);
}
function wsize(w) = [w[1] - w[0], w[3] - w[2]];
function wcentre(w) = [(w[0] + w[1]) / 2, (w[2] + w[3]) / 2];

// The door's front face, as far as this part cares: right edge and bottom fold (= the panel edges).
module door_face_2d() { translate([-1000, panel_bottom_y]) square([1000 + panel_right_x, 2000]); }

// M3 holes on the frame's centre line: corners, mid-sides, and points just above the window's bottom edge; only those with
// sheet behind them (>= hole_edge_min from the door's right edge and bottom fold).
function bezel_holes(w) =
    let(c = wcentre(w), s = wsize(w), hx = s.x / 2 + bezel_w / 2, hy = s.y / 2 + bezel_w / 2,
        cand = [[-hx, hy], [hx, hy], [0, hy], [-hx, 0], [hx, 0], [-hx, -s.y / 2 + 8], [hx, -s.y / 2 + 8], [-hx, -hy], [hx, -hy], [0, -hy]])
    [for (p = cand) let(q = c + p) if (q.y - panel_bottom_y >= hole_edge_min && panel_right_x - q.x >= hole_edge_min) q];

module bezel_2d(w) {          // in lathe XY
    difference() {
        intersection() { rrect(wcentre(w), wsize(w) + 2 * [bezel_w, bezel_w], bezel_r); door_face_2d(); }
        translate([w[0], w[2]]) square(wsize(w));
        for (p = bezel_holes(w)) translate(p) circle(d = m3_clear, $fn = 24);
    }
}

module door_bezel_at(w) {     // in place on the closed door, for a window [x0, x1, y0, y1]
    translate([0, 0, door_depth + door_t]) linear_extrude(bezel_t) bezel_2d(w);
}

win = which == "encoder" ? enc_window : motor_window;

module template_2d() {        // what to cut and drill in the door, in lathe XY
    translate([win[0], win[2]]) square(wsize(win));
    for (p = bezel_holes(win)) translate(p) circle(d = m3_clear, $fn = 24);
}

echo(str("door_bezel (", which, "): window ", round(wsize(win).x * 10) / 10, " x ", round(wsize(win).y * 10) / 10,
         " mm, frame ", bezel_w, " mm wide x ", bezel_t, " mm, ", len(bezel_holes(win)), " x M3 (holes with sheet behind them)"));

if (mode == "template") translate(-wcentre(win)) template_2d();
else if (mode == "lathe") door_bezel_at(win);
else translate(-wcentre(win)) linear_extrude(bezel_t) bezel_2d(win);

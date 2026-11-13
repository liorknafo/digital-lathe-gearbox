// lib/belt.scad -- belt length maths and stock-belt helpers.
// Pure functions, no geometry. `use <lib/belt.scad>` to import them.

// Pitch diameter of a toothed pulley (mm)
function pitch_dia(teeth, pitch) = teeth * pitch / PI;

// Exact open-belt length (mm, measured on the pitch line) for two pulleys of
// pitch diameters d1, d2 and centre distance c:
//   L = 2 c cos(phi) + pi (D + d) / 2 + phi (D - d),  phi = asin((D - d) / 2c)
function belt_length(d1, d2, c) =
    let (phi = asin(abs(d2 - d1) / (2 * c)))     // degrees
    2 * c * cos(phi) + PI * (d1 + d2) / 2 + (phi * PI / 180) * abs(d2 - d1);

// Same, but from tooth counts and belt pitch
function belt_length_t(t1, t2, c, pitch) =
    belt_length(pitch_dia(t1, pitch), pitch_dia(t2, pitch), c);

// Centre distance that gives exactly belt length L (fixed-point iteration)
function _cfl(L, d1, d2, c, n) =
    n == 0 ? c :
    let (phi = asin(abs(d2 - d1) / (2 * c)))
    _cfl(L, d1, d2,
         (L - PI * (d1 + d2) / 2 - (phi * PI / 180) * abs(d2 - d1)) / (2 * cos(phi)),
         n - 1);
function center_for_length(L, d1, d2) =
    _cfl(L, d1, d2, (L - PI * (d1 + d2) / 2) / 2, 25);

// Nearest stock belt length from a list (list of lengths in mm)
function nearest_stock(L, list) =
    let (err = [for (s = list) abs(s - L)],
         i = search(min(err), err)[0])
    list[i];

// Closest stock belt that is NOT shorter than L - slack (never over-tight)
// (kept simple: plain nearest is the default; this is the "round up" variant)
function stock_at_or_above(L, list) =
    let (ok = [for (s = list) if (s >= L) s])
    len(ok) > 0 ? min(ok) : max(list);

// ---- typical stock closed-loop belts (edit to match your supplier) ----------
// HTD 3M closed belts are always 3 mm x integer teeth. Common 3M-xxx numbers:
function htd3m_stock() = [150, 159, 165, 174, 180, 186, 192, 195, 198, 201, 204, 207, 210, 213, 216, 219, 222, 225, 228, 231,
               237, 240, 246, 252, 255, 264, 270, 273, 279, 285, 291, 300, 306,
               312, 318, 324, 330, 339, 345, 351, 360, 372, 384, 399, 420, 450];
// GT2 6 mm closed loops that are easy to buy
function gt2_stock() = [158, 200, 240, 280, 300, 330, 360, 400, 450, 500, 610];

// Human-readable report (returns a string; caller does echo)
function belt_report(name, t1, t2, c, pitch, stock) =
    let (d1 = pitch_dia(t1, pitch), d2 = pitch_dia(t2, pitch),
         L = belt_length(d1, d2, c),
         S = nearest_stock(L, stock),
         cS = center_for_length(S, d1, d2))
    str(name, ": ", t1, "T/", t2, "T pitch ", pitch, " mm, centre ", c,
        " mm -> belt length ", round(L * 100) / 100, " mm (",
        round(L / pitch * 100) / 100, " teeth); nearest stock ", S, " mm (",
        S / pitch, "T), error ", round((S - L) * 100) / 100,
        " mm; stock belt needs centre ", round(cS * 100) / 100, " mm");

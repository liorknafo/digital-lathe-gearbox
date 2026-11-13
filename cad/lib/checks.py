"""Fit checks of the ELS retrofit: what assembly.scad used to echo, now in two layers.

1. Numbers: the same checks as before, computed from the evaluated parameters (Z stack, belt overlaps, standoff, windows ...).
2. Geometry: measured by SolidCraft on the saved lathe assembly (cad/designs/lathe_assembly.sc): no overlaps between parts,
   body-to-body clearances, the door swung through 0..100 deg against the motor and encoder (joint.sweep), and the belt
   links driven through the joints.
`run(v)` returns the rows and writes cad/fit_checks.md.
"""
import json
import math
import os
import re
from fractions import Fraction

import sc
from door_bezel import needs_window

r2 = lambda x: f"{x:.2f}"


def _frac(x):
    f = Fraction(x).limit_denominator(1000)
    return f"{f.numerator}/{f.denominator}" if f.denominator != 1 else f"{f.numerator}"


def _firmware():
    """#define values of firmware/include/lathe_config.h (the controller's view of the drive), {} if it is not there."""
    path = os.path.join(os.path.dirname(sc.CAD), "firmware", "include", "lathe_config.h")
    if not os.path.exists(path):
        return {}
    out = {}
    for m in re.finditer(r"^\s*#define\s+(\w+)\s+(-?\d+)\s*$", open(path).read(), re.M):
        out[m.group(1)] = int(m.group(2))
    return out


def _dist_seg(p, a, b):
    abx, aby = b[0] - a[0], b[1] - a[1]
    L2 = abx * abx + aby * aby
    t = 0 if L2 == 0 else max(0, min(1, ((p[0] - a[0]) * abx + (p[1] - a[1]) * aby) / L2))
    return math.hypot(p[0] - a[0] - abx * t, p[1] - a[1] - aby * t)


def _dist_hull(p, c1, r1, c2, r2_):
    """Distance from p to the hull of two circles (negative inside), as assembly.scad sampled it."""
    return min(math.hypot(p[0] - (c1[0] + (c2[0] - c1[0]) * t), p[1] - (c1[1] + (c2[1] - c1[1]) * t)) - (r1 + (r2_ - r1) * t)
               for t in [i / 200 for i in range(201)])


def numeric(v):
    rows = []

    def chk(section, text, ok=None):
        rows.append((section, text, None if ok is None else ("PASS" if ok else "FAIL")))

    S = "belts"
    chk(S, f"leadscrew: HTD-3M {v['ls_teeth_motor']:.0f}T/{v['ls_teeth_screw']:.0f}T, stock 3M-{v['ls_belt_len']:.0f} "
           f"({v['ls_belt_teeth']:.0f} teeth): C_ls = {r2(v['C_ls'])} mm, motor axis at ({r2(round(v['motor_x'], 6) + 0.0)}, {r2(v['motor_y'])}); leadscrew = motor x {v['ls_ratio']:.4g}")
    def C(L, d1, d2):
        D, K = d2 - d1, L - math.pi * (d1 + d2) / 2
        c = (K + math.sqrt(K * K - 2 * D * D)) / 4
        for _ in range(3):
            ph = math.asin(D / (2 * c)); c = (K - ph * D) / (2 * math.cos(ph))
        return c
    other = ", ".join(f"3M-{n * 3} -> {r2(C(n * 3, v['ls_pd_m'], v['ls_pd_s']))}" for n in range(67, 73))
    chk(S, f"other HTD-3M stock lengths: {other}")
    chk(S, f"encoder: GT2 {v['enc_teeth_stud']:.0f}T/{v['enc_teeth_encoder']:.0f}T, stock {v['enc_belt_len']:.0f} mm loop: "
           f"C_enc = {r2(v['C_enc'])} mm, E = ({r2(v['enc_x'])}, {r2(v['enc_y'])}); encoder = stud ratio {_frac(v['stud_ratio'])} x {v['enc_teeth_stud']:.0f}/{v['enc_teeth_encoder']:.0f} = {_frac(v['enc_per_spindle'])} spindle ({v['enc_counts_per_rev']:.6g} counts per spindle turn)")
    fw = _firmware()
    if fw:
        want_e, want_m = Fraction(v["enc_per_spindle"]).limit_denominator(1000), (round(v["ls_teeth_motor"]), round(v["ls_teeth_screw"]))
        have_e = Fraction(fw.get("ENCODER_TURNS", 0), fw.get("SPINDLE_TURNS", 1))
        ok = have_e == want_e and (fw.get("MOTOR_PULLEY_TEETH"), fw.get("LEADSCREW_PULLEY_TEETH")) == want_m and fw.get("ENCODER_CPR") == round(4 * v["enc_ppr"])
        chk(S, f"firmware/include/lathe_config.h matches the drive: ENCODER_TURNS/SPINDLE_TURNS {fw.get('ENCODER_TURNS')}/{fw.get('SPINDLE_TURNS')} "
               f"(need {want_e.numerator}/{want_e.denominator}), MOTOR_PULLEY_TEETH/LEADSCREW_PULLEY_TEETH {fw.get('MOTOR_PULLEY_TEETH')}/{fw.get('LEADSCREW_PULLEY_TEETH')} "
               f"(need {want_m[0]}/{want_m[1]}), ENCODER_CPR {fw.get('ENCODER_CPR')} (need {round(4 * v['enc_ppr'])})"
               + ("" if ok else ": change the firmware to these values (or the teeth back) so the controller knows the real ratios"), ok)
    chk(S, "other GT2 loops: " + ", ".join(f"{L} -> {r2(C(L, v['enc_pd_e'], v['enc_pd_s']))}" for L in (158, 200, 240)))

    S = "Z stack"
    chk(S, f"40T back face Z {v['ls_seat_z']} vs plate front {v['base_t']}: {r2(v['ls_run_gap'])} mm open (+ {v['base_relief']} relief)", v["ls_run_gap"] >= -0.001)
    proud = v["ls_front_z"] - (v["ls_seat_z"] + v["ls_shaft_free"])
    chk(S, f"40T Z {v['ls_seat_z']}..{r2(v['ls_front_z'])} (hub {r2(v['ls_hub_len'])}, belt centre {r2(v['ls_belt_mid_z'])}); face {r2(proud)} mm proud of the shaft end (washer clamps the hub)", proud > 0)
    # set screws (options ls_setscrew / stud_setscrew): the screw hole sits mid-hub and must be over the shaft, not past its end
    for nm, on, z0, body, hub, end, d in (("40T", v["ls_setscrew"], v["ls_seat_z"], v["ls_body_h"], v["ls_hub_len"], v["ls_seat_z"] + v["ls_shaft_free"], v["m4_clear"]),
                                          ("60T", v["stud_setscrew"], v["stud_z0"], v["stud_body_h"], v["stud_hub_len"], v["stud_seat_z"] + v["stud_shaft_free"], v["m3_clear"])):
        if on:
            zs = z0 + body + hub / 2
            chk(S, f"{nm} set screw (option on): axis Z {r2(zs)}, hole top Z {r2(zs + d / 2)} vs the shaft end Z {r2(end)}: "
                   + ("bears on the shaft" if zs + d / 2 <= end else
                      "the screw axis is PAST the shaft end: it would tighten on nothing (the hub needed for the nut trap is longer than the shaft)"
                      if zs > end else "the hole overhangs the shaft end: the screw would only catch the shaft's edge"),
                zs + d / 2 <= end)
    chk(S, f"60T Z {r2(v['stud_z0'])}..{r2(v['stud_front_z'])} (hub {r2(v['stud_hub_len'])}, belt centre {r2(v['stud_belt_mid_z'])}), back face above bearing_cap_z {v['bearing_cap_z']}", v["stud_z0"] > v["bearing_cap_z"])
    cap_gap = math.hypot(v["stud_x"] - v["spindle_x"], v["stud_y"] - v["spindle_y"]) - v["bearing_cap_r"]
    ring_r = max(v["stud_hub_dia"] / 2, v["stud_spacer_od"] / 2 if v["stud_spacer"] > 0 else 0)
    chk(S, f"60T hub{' and the stud spacer ring' if v['stud_spacer'] > 0 else ''} (r {ring_r:.2f}) inside the free radius {r2(cap_gap)} before the cap disc; the 60T overlaps the cap in XY by {r2(v['stud_flange_r'] - cap_gap)} mm (cap is below Z {v['stud_z0']})", ring_r < cap_gap)
    chk(S, f"belts clear the plate: HTD back edge Z {r2(v['belt_lo'])} ({r2(v['belt_lo'] - v['base_t'])} above the plate), GT2 back edge Z {r2(v['enc_belt_lo'])} ({r2(v['enc_belt_lo'] - v['base_t'] - v['base_rib_h'])} above the rib)",
        v["belt_lo"] - v["base_t"] >= 1 and v["enc_belt_lo"] - v["base_t"] - v["base_rib_h"] >= 1)

    S = "motor"
    chk(S, f"bought 20T HTD Z {r2(v['mp_back_z'])}..{r2(v['mp_front_z'])}, teeth centred on the 40T belt band; belt on the 40T teeth {r2(v['ov_40'])}, on the 20T teeth {r2(v['ov_20'])} (belt {v['ls_belt_w']:.0f})",
        v["ov_40"] >= v["ls_belt_w"] - 0.001 and v["ov_20"] >= v["ls_belt_w"] - 0.001)
    chk(S, f"STANDOFF: exact {r2(v['standoff_need'])} mm -> M5 hex standoff {v['standoff_len']:.0f} mm + {v['standoff_shim']} mm washer shim; motor flange face Z {r2(v['motor_face_z'])}",
        v["standoff_len"] + v["standoff_shim"] >= v["standoff_need"] - 0.001 and v["standoff_shim"] <= v["standoff_shim_max"])
    ok = v["motor_gap"] >= v["motor_gap_min"] - 0.001 and v["motor_tip_z"] <= v["mp_back_z"] + v["mp_buy_flange"] + v["mp_buy_tooth"] and v["motor_engage"] >= v["mp_buy_hub"] + 4
    chk(S, f"motor shaft tip Z {r2(v['motor_tip_z'])}: {r2(v['motor_engage'])} of the {r2(v['mp_len'])} mm pulley bore on the shaft, hub end to pilot face {r2(v['motor_gap'])}", ok)
    chk(S, f"motor flange Z {r2(v['motor_face_z'])} above the 40T stack front Z {r2(v['ls_front_z'])} by {r2(v['motor_face_z'] - v['ls_front_z'])}", v["motor_face_z"] > v["ls_front_z"])

    S = "encoder"
    chk(S, f"20T GT2 Z {r2(v['ep_back_z'])}..{r2(v['ep_front_z'])}; belt on the 60T teeth {r2(v['ov_60'])}, on the 20T teeth {r2(v['ov_e20'])} (belt {v['enc_belt_w']:.0f})",
        v["ov_60"] >= v["enc_belt_w"] - 0.001 and v["ov_e20"] >= v["enc_belt_w"] - 0.001)
    ok = v["enc_engage"] >= v["ep_hub_len"] + 4 and v["enc_tip_z"] <= v["ep_back_z"] + v["gt2_flange_t"] + v["gt2_tooth_len"]
    chk(S, f"encoder face (bracket top) Z {r2(v['enc_face_z'])}, bracket {r2(v['eb_h'])} tall; shaft tip Z {r2(v['enc_tip_z'])}, {r2(v['enc_engage'])} of {r2(v['ep_len'])} mm bore on the shaft", ok)
    stud, E = (v["stud_x"], v["stud_y"]), (v["enc_x"], v["enc_y"])
    free_x = v["cup_left_x"]
    belt_clear = min(_dist_hull((free_x, v["enc_y"] + sy * v["eb_in"]), stud, v["stud_od"] / 2 + 1.4, (E[0] + sp * v["enc_travel"] / 2, E[1]),
                                v["enc_pd_e"] / 2 + 1.5) for sy in (-1, 1) for sp in (-1, 1))
    chk(S, f"bracket wall ends (X {r2(free_x)}) to the GT2 strands over the +-{v['enc_travel'] / 2:.0f} mm slide: {r2(belt_clear)} mm; belt top Z {r2(v['enc_belt_hi'])} to the top plate underside: {r2(v['eb_under_z'] - v['enc_belt_hi'])} mm",
        belt_clear >= 2 and v["eb_under_z"] - v["enc_belt_hi"] >= 2)

    S = "door"
    for nm, p, box, zf in (("motor", "mwin", "mbox", v["motor_front_z"]), ("encoder", "ewin", "ebox", v["enc_front_z"])):
        if zf <= v["door_depth"] - v["door_clear"]:
            chk(S, f"{nm}: front Z {r2(zf)} stays inside the door: no window", True)
            continue
        w = [v[f"{p}_x0"], v[f"{p}_x1"], v[f"{p}_y0"], v[f"{p}_y1"]]
        far = w[1] - v[f"{box}_x1"]
        chk(S, f"{nm} pokes {r2(zf - v['door_depth'])} mm past the door: window {r2(w[1] - w[0])} x {r2(w[3] - w[2])} at X {r2(w[0])}..{r2(w[1])}, Y {r2(w[2])}..{r2(w[3])}; far-side gap {r2(far)}")
        chk(S, f"{nm} window: sheet left to the bottom fold {r2(w[2] - v['panel_bottom_y'])}, to the right edge {r2(v['panel_right_x'] - w[1])} (>= 3)",
            w[2] - v["panel_bottom_y"] >= 3 and v["panel_right_x"] - w[1] >= 3)
        re_ = math.hypot(w[1] - v["door_hinge_x"], v["door_depth"] - v["door_hinge_z"])
        rc = math.hypot(v[f"{box}_x1"] - v["door_hinge_x"], zf - v["door_hinge_z"])
        chk(S, f"{nm} window: far edge radius from the hinge {r2(re_)} >= outer back corner radius {r2(rc)}", re_ >= rc)
    mw = (v["mwin_x0"], v["mwin_x1"], v["mwin_y0"], v["mwin_y1"])
    chk(S, f"door switch plunger ({v['plunger_x']}, {v['plunger_y']}) outside the motor window: the door closes fully, the switch still works",
        v["plunger_x"] < mw[0] - 5 or v["plunger_y"] < mw[2] - 5 or v["plunger_y"] > mw[3] + 5)

    S = "XY keep-outs and the Y slide"
    t = v["base_travel"] / 2
    B1a, B1b = (v["B1_x"], v["B1_y"] + t), (v["B1_x"], v["B1_y"] - t)
    B2a, B2b = (v["B2_x"], v["B2_y"] + t), (v["B2_x"], v["B2_y"] - t)
    so = [(v[f"so{i}_x"], v[f"so{i}_y"]) for i in (1, 2, 3, 4)]
    colc = (v["col_cx"], v["enc_y"])
    cols = [(v["col_x"], v["enc_y"] + s * v["col_dy"]) for s in (-1, 1)]
    padl = v["cup_left_x"] - v["base_pad_margin"]
    m = v["base_pad_margin"]
    groups = [[(B1a, v["base_boss_r"]), (B1b, v["base_boss_r"]), (B2a, v["base_boss_r"]), (B2b, v["base_boss_r"])] + [(p, v["standoff_boss_r"]) for p in so],
              [(B1a, v["base_arm_w"] / 2), (colc, v["base_arm_w"] / 2)],
              [(colc, v["eb_out"] + m), ((padl, v["enc_y"] + v["eb_out"] + m), 0.01), ((padl, v["enc_y"] - v["eb_out"] - m), 0.01)] + [(c, v["eb_col_r"] + m) for c in cols]]
    pd = lambda p: min(_dist_hull(p, g[i][0], g[i][1], g[j][0], g[j][1]) for g in groups for i in range(len(g)) for j in range(i, len(g)))
    yb = max(v["plate_y_min"], min(c[0][1] - c[1] for g in groups for c in g))
    xr = max(c[0][0] + c[1] for g in groups for c in g)
    chk(S, f"plate bottom Y {r2(yb)} >= {r2(v['plate_y_min'])}, right edge X {r2(xr)} <= {r2(v['plate_x_max'])}", yb >= v["plate_y_min"] - 0.001 and xr <= v["plate_x_max"])
    chk(S, f"Y slide +-{t:.0f}: down (tension) limited by the panel margin to {r2(yb - v['plate_y_min'])} mm; motor flange bottom {r2(v['mbox_y0'])} nominal, {r2(v['mbox_y0'] - t)} at -{t:.0f} (panel edge {v['panel_bottom_y']})",
        v["mbox_y0"] - t > v["panel_bottom_y"])
    dC = lambda d: math.sqrt(v["C_enc"] ** 2 + d * d) - v["C_enc"]
    chk(S, f"a Y slide changes the horizontal GT2 centre by {r2(dC(t))} at +-{t:.0f}, {r2(dC(2))} at 2, {r2(dC(1))} at 1 mm (< 0.2, the +-4 slots absorb it)", dC(2) < 0.2)
    chk(S, f"motor flange left X {r2(v['mbox_x0'])} right of the switch box X {v['sw_x1']} by {r2(v['mbox_x0'] - v['sw_x1'])}", v["mbox_x0"] > v["sw_x1"])
    chk(S, f"plate (XY) vs the 60T flange (r {r2(v['stud_flange_r'])} + 3): {r2(pd(stud) - v['stud_flange_r'])} mm", pd(stud) >= v["stud_flange_r"] + 3)
    lr = v["ls_boss_d"] / 2 + v["ls_boss_clear"]
    sr = (v["banjo_bolt_d"] + v["base_bolt_clear"]) / 2
    seg = lambda a1, a2: min(_dist_seg(a1, (0, t), (0, -t)), _dist_seg(a2, (0, t), (0, -t)), _dist_seg((0, t), a1, a2), _dist_seg((0, -t), a1, a2))
    w1, w2 = seg(B1a, B1b), seg(B2a, B2b)
    chk(S, f"web L slot to B1 / B2 slots: {r2(w1 - lr - sr)} / {r2(w2 - lr - sr)} mm; at the countersinks {r2(w1 - lr - v['base_head_d'] / 2)} / {r2(w2 - lr - v['base_head_d'] / 2)} mm",
        w1 - lr - sr >= 2 and w1 - lr - v["base_head_d"] / 2 >= 0.8)
    chk(S, f"B1/B2 countersunk heads flush with the plate front Z {v['base_t']}; 40T back face Z {v['ls_seat_z']}", v["ls_seat_z"] >= v["base_t"])
    return rows


PAIRS = [  # (label, bodies, against, at least mm)
    ("plate vs door switch box", ["Base plate"], ["Door switch box"], 2),
    ("plate vs spindle bearing cap", ["Base plate"], ["Spindle bearing cap"], "bearing_cap_clear"),
    ("encoder bracket vs 60T stud pulley", ["Encoder bracket"], ["Pulley GT2 60T"], 3),
    ("standoffs vs HTD belt", ["M5 hex standoffs", "M5 hex standoffs (2)", "M5 hex standoffs (3)", "M5 hex standoffs (4)"], ["HTD-3M belt 3M-207"], 2),
    ("standoffs vs 40T pulley", ["M5 hex standoffs", "M5 hex standoffs (2)", "M5 hex standoffs (3)", "M5 hex standoffs (4)"], ["Pulley HTD-3M 40T"], 2),
    ("encoder bracket vs GT2 belt", ["Encoder bracket"], ["GT2 belt 200"], 2),
    ("motor flange + pilot vs 40T pulley", ["Motor body", "Motor pilot"], ["Pulley HTD-3M 40T", "HTD-3M belt 3M-207"], 0.5),
    ("closed door vs motor (window)", ["Door sheet"], ["Motor body"], "door_cut_clear_y"),
    ("closed door vs encoder (window)", ["Door sheet"], ["Encoder body"], "door_cut_clear_y"),
    ("40T pulley vs base plate", ["Pulley HTD-3M 40T"], ["Base plate"], 0.5),
    ("60T / 20T GT2 vs base plate", ["Pulley GT2 60T", "Pulley GT2 20T"], ["Base plate"], 1),
]


def geometric(v):
    design = os.path.join(sc.CAD, "designs", "lathe_assembly.sc")
    steps = [{"command": "inspect.clearance", "params": {"skip_within": "component"}}]
    for _, a, b, _m in PAIRS:
        steps.append({"command": "inspect.clearance", "params": {"bodies": a, "against": b, "nearest": 1}})
    door_parts = ["Door:1"] + [f"Door bezel {w}:1" for w in ("motor", "encoder") if needs_window(v, w)]
    SEG = [(0, 25), (25, 50), (50, 75), (75, 100)]      # the door swing in 4 pieces: each sweep gets its own work budget
    steps += [{"command": "joint.sweep", "params": {"joint": "Door hinge", "from": a, "to": b, "occurrences": door_parts,
                                                     "against": ["Motor:1", "Encoder:1", "Motor rotor:1", "Encoder rotor:1"],
                                                     "report_gaps": True, "budget_s": 1200}} for a, b in SEG]
    steps += [
              {"command": "joint.drive", "params": {"joint": "Motor", "value": 360}},
              {"command": "joint.drive", "params": {"joint": "Stud", "value": 120}},
              {"command": "joint.list", "params": {}}]
    path = os.path.join(sc.BUILD, "scripts", "_checks.json")
    with open(path, "w") as f:
        json.dump({"commands": steps}, f)
    out = os.path.join(sc.BUILD, "_checks_results.json")
    sc.run_cli(["run", path, "--in", design, "--results", "--quiet", "--json-out", out])
    with open(out) as f:
        res = json.load(f)
    rows = []
    S = "geometry (SolidCraft, lathe_assembly.sc)"
    def thread(o):          # designed: a screw in the thread it screws into (B1/B2 in the casting; M5: see base_m5)
        p = {o["a"], o["b"]}
        fast = any(x.startswith("M5 standoff fastener") for x in p)
        if p in ({"End panel", "B1 screw"}, {"End panel", "B2 screw"}):
            return True
        if v["base_m5"] == "csk":      # flat-head screws from the back into the standoffs' female thread
            return fast and any(x.startswith("M5 hex standoffs") for x in p)
        if v["base_m5"] == "tap":      # the standoffs' male studs in the plate's tapped holes
            return fast and "Base plate" in p
        return False                   # insert: the studs sit in the inserts' thread, nothing overlaps
    ov = [o for o in res[0]["overlaps"] if not thread(o)]
    th = [o for o in res[0]["overlaps"] if thread(o)]
    rows.append((S, "no part overlaps another at rest: " + ("none" if not ov else "; ".join(f"{o['a']} / {o['b']} {o['volume_mm3']:.1f} mm3" for o in ov))
                 + f" (besides {len(th)} screws in their threads)", "PASS" if not ov else "FAIL"))
    for (label, a, b, need), r in zip(PAIRS, res[1:1 + len(PAIRS)]):
        need_v = v[need] if isinstance(need, str) else need
        d = min((x["distance_mm"] for lst in r.get("nearest", {}).values() for x in lst), default=None)
        if r.get("overlaps"):
            d = 0.0
        ok = d is not None and d >= need_v - 1e-6
        rows.append((S, f"{label}: {'?' if d is None else r2(d)} mm (>= {need_v:g})", "PASS" if ok else "FAIL"))
    sweeps = res[1 + len(PAIRS):1 + len(PAIRS) + len(SEG)]
    worst, ok, reached = None, True, 0.0
    for (a, b), sw in zip(SEG, sweeps):
        done = sw.get("stopped_by") in (None, "limit") and not sw.get("budget_exceeded")
        ok = ok and done
        if done and abs(reached - a) < 1e-9:
            reached = b
        elif not done and abs(reached - a) < 1e-9:
            reached = sw.get("stopped_at") or a
        for k, x in (sw.get("min_gap") or {}).items():
            if k.startswith("Door") and (worst is None or x["mm"] < worst[1]["mm"]):
                worst = (k, x)
    tol = max((sw.get("gap_tolerance_mm", 0) for sw in sweeps), default=0)
    def why(sw):
        b = sw.get("stopped_by")
        if isinstance(b, dict):                     # a contact: the two parts that met
            return f"contact {b.get('a')} / {b.get('b')} at {r2(sw.get('stopped_at') or 0)} deg"
        return f"{b} at {r2(sw.get('stopped_at') or 0)} deg"
    stop = next((why(sw) for sw in sweeps if not (sw.get("stopped_by") in (None, "limit") and not sw.get("budget_exceeded"))), "")
    rows.append((S, f"door swung 0..100 deg past the motor and encoder: reached {r2(reached)} deg" + (" without touching" if ok else f", stopped by {stop}")
                    + "; closest " + (f"{r2(worst[1]['mm'])} mm ({worst[0]} to {worst[1]['to']} at {r2(worst[1]['at_value'])} deg)" if worst else "?")
                    + f"; gaps on meshes, within {r2(tol)} mm", "PASS" if ok else "FAIL"))
    jl = res[-1]
    val = {j["name"]: j["values"][0]["value"] for j in jl["joints"] if j.get("values")}
    want_l, want_e = 360 * v["ls_ratio"], 120 * v["enc_teeth_stud"] / v["enc_teeth_encoder"]   # from the tooth counts
    rows.append((S, f"belt links: motor 360 deg -> leadscrew {r2(val.get('Leadscrew', float('nan')))} deg (expected {r2(want_l)}, "
                    f"{v['ls_teeth_motor']:.0f}T:{v['ls_teeth_screw']:.0f}T); stud 120 deg -> encoder {r2(val.get('Encoder', float('nan')))} deg "
                    f"(expected {r2(want_e)}, {v['enc_teeth_stud']:.0f}T:{v['enc_teeth_encoder']:.0f}T)",
                 "PASS" if abs(val.get("Leadscrew", 0) - want_l) < 1e-6 and abs(val.get("Encoder", 0) - want_e) < 1e-6 else "FAIL"))
    return rows


def run(v, geometry=True):
    rows = numeric(v) + (geometric(v) if geometry else [])
    lines = ["# Fit checks", "",
             "Written by `python3 cad/build.py` from cad/params.json and the SolidCraft designs (cad/lib/checks.py). Do not edit.", ""]
    section = None
    for s, text, verdict in rows:
        if s != section:
            lines += ["", f"## {s}", "", "| check | result |", "|---|---|"]
            section = s
        lines.append(f"| {text} | {verdict or 'info'} |")
    with open(os.path.join(sc.CAD, "fit_checks.md"), "w") as f:
        f.write("\n".join(lines) + "\n")
    return rows

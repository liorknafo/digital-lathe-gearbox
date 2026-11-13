"""Assemblies: the ELS drive on the lathe's gear end (lathe_assembly) and the controller box (control_box_assembly).

The printed parts come in as LINKED components (component.insert_design of cad/designs/*.sc): edit a part, rebuild, and the
assembly follows (`component.update_links` in the app does the same by hand). Bought parts (motor, standoffs, encoder,
the bought 20T HTD pulley), shafts, belts, the end panel and the door are simple bodies made here from the same parameters.

Lathe assembly joints (lathe frame, see params.json):
  Leadscrew  revolute about Z through L               40T pulley rigid on it
  Motor      revolute about Z through the motor axis  shaft + bought 20T; drives Leadscrew through the HTD belt (gear link, 20:40, same direction)
  Stud       revolute about Z through S               60T pulley rigid on it
  Encoder    revolute about Z through E               shaft + 20T GT2; follows Stud through the GT2 belt (gear link, 60:20, same direction)
  Door       revolute about the hinge axis (vertical, X = door_hinge_x), 0..100 deg open; the bezels ride on it
Motion studies: "Leadscrew one turn" (Motor 0..360 / ls_ratio), "Encoder from the stud" (Stud 0..360), "Door open" (0..100 deg).
"""
import os
from sc import C, circle_cmds, hulls_sketch
from door_bezel import needs_window

DESIGNS = None   # set by build.py: the cad/designs folder


def comp(name, bodies):
    return [C("component.create", name=name, parent="root", activate=False),
            C("component.move_bodies", bodies=bodies, component=name)]


def link(name, design, at=(0, 0, 0)):
    return C("component.insert_design", path=os.path.join(DESIGNS, f"{design}.sc"), name=name, parent="root",
             translate=[float(a) for a in at])


def cyl(body, d, h, base, op="new"):
    return C("solid.cylinder", diameter=d, height=h, base=base, operation=op, body_name=body, name=body)


def box(body, x0, x1, y0, y1, z0, z1, op="new", targets=None):
    p = dict(corner=[x0, y0, z0], length=f"({x1}) - ({x0})", width=f"({y1}) - ({y0})", height=f"({z1}) - ({z0})",
             operation=op, name=body)
    if op == "new":
        p["body_name"] = body
    if targets:
        p["targets"] = targets
    return C("solid.box", **p)


def hexagon(x, y, af):
    r = f"({af} / sqrt(3))"
    return [[x, f"{y} + {r}"], [f"{x} - {af} / 2", f"{y} + {r} / 2"], [f"{x} - {af} / 2", f"{y} - {r} / 2"],
            [x, f"{y} - {r}"], [f"{x} + {af} / 2", f"{y} - {r} / 2"], [f"{x} + {af} / 2", f"{y} + {r} / 2"]]


def revolute(name, a, b, x, y, z=(0, 0, 1), limits=None):
    p = dict(type="revolute", name=name, flip=True, a={"occurrence": a, "point": [x, y, 0], "z": list(z)},
             b={"occurrence": b, "point": [x, y, 0], "z": list(z)}, quiet=True)
    if limits:
        p["limits"] = limits
    return C("joint.create", **p)


def rigid(a, b):
    return C("joint.as_built", type="rigid", a=a, b=b, name=f"{b} on {a}")


def colours(windows, spacer, inserts=False):
    """The OpenSCAD preview colours (per body); the door see-through so the drive shows behind it."""
    c = {"#4682b4": ["End panel", "Encoder bracket"], "#cc2222": ["Door switch box"], "#ff00ff": ["Door switch plunger"],
         "#5a5a5a": ["Spindle bearing cap", "Spindle"], "#c0c0c0": ["Leadscrew shaft", "Stud shaft", "Motor shaft", "Encoder shaft"],
         "#808080": ["Leadscrew shoulder", "Motor pilot", "Encoder pilot"], "#cd853f": ["Stud shoulder"],
         "#b8bcc2": ["Motor body", "Encoder body"], "#708090": ["M5 hex standoffs"] + [f"M5 hex standoffs ({i})" for i in (2, 3, 4)],
         "#ff8c00": ["Motor pulley 20T (bought)", "Pulley HTD-3M 40T"], "#90ee90": ["Pulley GT2 60T", "Pulley GT2 20T"],
         "#3c3c3c": ["HTD-3M belt 3M-207", "GT2 belt 200"], "#daa520": ["Base plate"],
         "#2f4f4f": [f"Door bezel ({w})" for w in windows], "#cd853f ": ["Stud spacer"] if spacer else [],
         "#505050": ["Leadscrew end screw head", "Stud end screw head", "B1 screw", "B2 screw"] + [f"M5 standoff fastener {i}" for i in (1, 2, 3, 4)]
                    + ["M4 bracket screw 1", "M4 bracket screw 2"], "#d0d0d0": ["Leadscrew end washer", "Stud end washer"]}
    if inserts:
        c["#b87333"] = [f"M5 insert {i}" for i in (1, 2, 3, 4)]
    out = [C("appearance.assign", bodies=b, color=col.strip()) for col, b in c.items() if b]
    return out + [C("appearance.assign", bodies=["Door sheet"], color="#d2b48c", opacity=0.25)]


def lathe(v):
    so = [(f"so{i}_x", f"so{i}_y") for i in (1, 2, 3, 4)]      # standoffs: the bolt square turned with motor_angle
    cmds = []
    # ---- lathe end (grounded): end panel, door switch, bearing cap, spindle stub ----
    cmds += [box("End panel", "door_hinge_x", "panel_right_x", "panel_bottom_y", "250 mm", "-3 mm", "-0.4 mm"),
             box("Door switch box", "sw_x0", "sw_x1", "sw_y0", "sw_y1", "0 mm", "22 mm"),
             cyl("Door switch plunger", "5 mm", "30 mm", ["plunger_x", "plunger_y", 0]),
             C("solid.cylinder", radius="bearing_cap_r", height="bearing_cap_z", base=["spindle_x", "spindle_y", 0], operation="new",
               body_name="Spindle bearing cap", name="Spindle bearing cap"),
             cyl("Spindle", "24 mm", "bearing_cap_z + 6 mm", ["spindle_x", "spindle_y", 0])]
    cmds += comp("Lathe", ["End panel", "Door switch box", "Door switch plunger", "Spindle bearing cap", "Spindle"])
    # ---- shafts that turn ----
    cmds += [cyl("Leadscrew shoulder", "ls_shoulder_d", "ls_seat_z", [0, 0, 0]),
             cyl("Leadscrew shaft", "ls_shaft_bore", "ls_seat_z + ls_shaft_free", [0, 0, 0])]
    cmds += comp("Leadscrew", ["Leadscrew shoulder", "Leadscrew shaft"])
    cmds += [cyl("Stud shoulder", "stud_shoulder_d", "stud_seat_z", ["stud_x", "stud_y", 0]),
             cyl("Stud shaft", "stud_bore", "stud_seat_z + stud_shaft_free", ["stud_x", "stud_y", 0])]
    cmds += comp("Stud", ["Stud shoulder", "Stud shaft"])
    # ---- motor (closed-loop NEMA23) on 4 M5 hex standoffs (+ washer shim) ----
    cmds += [C("sketch.create", plane="XY", offset="motor_face_z", name="Motor body sketch"),          # the square turns with motor_angle
             C("sketch.line", points=[[f"mc{i}_x", f"mc{i}_y"] for i in (1, 2, 3, 4)], closed=True, infer=False),
             C("sketch.finish"),
             C("solid.extrude", distance="motor_len", operation="new", name="Motor body", body_name="Motor body"),
             cyl("Motor pilot", "motor_pilot_d", "motor_pilot_h", ["motor_x", "motor_y", "motor_face_z - motor_pilot_h"]),
             C("sketch.create", plane="XY", offset="base_t", name="Standoffs sketch")]
    cmds += [C("sketch.line", points=hexagon(x, y, "standoff_af"), closed=True, infer=False) for x, y in so]
    cmds += [C("sketch.finish"), C("solid.extrude", distance="standoff_len", operation="new", name="M5 hex standoffs",
                                   body_name="M5 hex standoffs")]
    motor_bodies = ["Motor body", "Motor pilot", "M5 hex standoffs"] + [f"M5 hex standoffs ({i})" for i in (2, 3, 4)]
    if v["standoff_shim"] > 0:
        for i, (x, y) in enumerate(so):
            cmds.append(cyl(f"Washer shim {i + 1}", "10 mm", "standoff_shim", [x, y, "base_t + standoff_len"]))
            motor_bodies.append(f"Washer shim {i + 1}")
    cmds += comp("Motor", motor_bodies)
    # motor shaft (D-flat on +X) + the bought 20T HTD-3M pulley (flange, teeth, hub towards the motor; 8 mm bore)
    cmds += [cyl("Motor pulley 20T (bought)", "mp_buy_flange_d", "mp_buy_flange", ["motor_x", "motor_y", "mp_back_z"]),
             C("solid.cylinder", diameter="mp_od", height="mp_buy_tooth", base=["motor_x", "motor_y", "mp_back_z + mp_buy_flange"],
               operation="join", targets=["Motor pulley 20T (bought)"], name="Motor pulley teeth"),
             C("solid.cylinder", diameter="mp_buy_hub_d", height="mp_buy_hub", base=["motor_x", "motor_y", "mp_back_z + mp_buy_flange + mp_buy_tooth"],
               operation="join", targets=["Motor pulley 20T (bought)"], name="Motor pulley hub"),
             C("solid.cylinder", diameter="motor_shaft_d", height="mp_len + 2 mm", base=["motor_x", "motor_y", "mp_back_z - 1 mm"],
               operation="cut", targets=["Motor pulley 20T (bought)"], name="Motor pulley bore"),
             cyl("Motor shaft", "motor_shaft_d", "motor_shaft_len", ["motor_x", "motor_y", "motor_tip_z"]),
             box("Motor shaft flat", "motor_x + motor_shaft_d / 2 - motor_shaft_flat", "motor_x + motor_shaft_d", "motor_y - motor_shaft_d", "motor_y + motor_shaft_d",
                 "motor_tip_z - 1 mm", "motor_face_z", op="cut", targets=["Motor shaft"])]
    cmds += comp("Motor rotor", ["Motor shaft", "Motor pulley 20T (bought)"])
    # ---- encoder LPD3806 on the bracket; its shaft (D-flat) turns ----
    cmds += [cyl("Encoder body", "enc_body_d", "enc_body_len", ["enc_x", "enc_y", "enc_face_z"]),
             cyl("Encoder pilot", "enc_pilot_d", "enc_pilot_h", ["enc_x", "enc_y", "enc_face_z - enc_pilot_h"])]
    cmds += comp("Encoder", ["Encoder body", "Encoder pilot"])
    cmds += [cyl("Encoder shaft", "enc_shaft_d", "enc_shaft_len + eb_recess - enc_pilot_h", ["enc_x", "enc_y", "enc_tip_z"]),
             box("Encoder shaft flat", "enc_x + enc_shaft_d / 2 - enc_shaft_flat", "enc_x + enc_shaft_d", "enc_y - enc_shaft_d", "enc_y + enc_shaft_d",
                 "enc_tip_z - 1 mm", "enc_face_z", op="cut", targets=["Encoder shaft"])]
    cmds += comp("Encoder rotor", ["Encoder shaft"])
    # ---- belts (bands from the tooth tips to 0.6 past the pitch line) ----
    cmds += hulls_sketch("HTD belt sketch", "belt_lo",
                         [[("0", "0", "ls_pd_s / 2 + 0.6 mm"), ("motor_x", "motor_y", "ls_pd_m / 2 + 0.6 mm")],
                          [("0", "0", "ls_od / 2"), ("motor_x", "motor_y", "mp_od / 2")]], v)
    cmds.append(C("solid.extrude", distance="ls_belt_w", operation="new", name="HTD-3M belt", body_name="HTD-3M belt 3M-207"))
    cmds += hulls_sketch("GT2 belt sketch", "enc_belt_lo",
                         [[("stud_x", "stud_y", "enc_pd_s / 2 + 0.6 mm"), ("enc_x", "enc_y", "enc_pd_e / 2 + 0.6 mm")],
                          [("stud_x", "stud_y", "stud_od / 2"), ("enc_x", "enc_y", "ep_od / 2")]], v)
    cmds.append(C("solid.extrude", distance="enc_belt_w", operation="new", name="GT2 belt", body_name="GT2 belt 200"))
    cmds += comp("Belts", ["HTD-3M belt 3M-207", "GT2 belt 200"])
    # ---- hardware: end screws + washers, B1/B2 countersunk screws, the M5 / M4 screws from the back ----
    hw = []
    for nm, x, y, z, d in (("Leadscrew", "0 mm", "0 mm", "ls_front_z", "ls_end_screw"), ("Stud", "stud_x", "stud_y", "stud_front_z", "stud_end_screw")):
        hw += [cyl(f"{nm} end washer", f"2 * {d} + 1 mm", "1.6 mm", [x, y, z]), cyl(f"{nm} end screw head", f"1.6 * {d}", d, [x, y, f"{z} + 1.6 mm"])]
    for b in ("B1", "B2"):
        hw += [cyl(f"{b} screw", "banjo_bolt_d", "12 mm + base_t - (base_head_d - 0.4 mm - banjo_bolt_d) / 2", [f"{b}_x", f"{b}_y", "-12 mm"]),
               C("sketch.create", plane="XY", offset="base_t - (base_head_d - 0.4 mm - banjo_bolt_d) / 2", name=f"{b} head sketch"),
               *circle_cmds(f"{b}_x", f"{b}_y", "banjo_bolt_d", v, "c1"), C("sketch.finish"),
               C("solid.extrude", distance="(base_head_d - 0.4 mm - banjo_bolt_d) / 2", taper="45 deg", operation="join",
                 targets=[f"{b} screw"], name=f"{b} countersunk head")]
    for i, (x, y) in enumerate(so):
        if v["base_m5"] == "csk":      # M5 flat-head screw from the back, through the plate into the standoff
            hw.append(cyl(f"M5 standoff fastener {i + 1}", "5 mm", "base_t + 5 mm", [x, y, 0]))
        else:                          # male-threaded standoff: its M5 stud in the tapped hole (tap) or in a heat-set insert (insert)
            hw.append(cyl(f"M5 standoff fastener {i + 1}", "5 mm", "base_t", [x, y, 0]))
            if v["base_m5"] == "insert":
                hw += [cyl(f"M5 insert {i + 1}", "6.4 mm", "base_t", [x, y, 0]),
                       C("solid.cylinder", diameter="5 mm", height="base_t + 2 mm", base=[x, y, "-1 mm"], operation="cut",
                         targets=[f"M5 insert {i + 1}"], name=f"M5 insert {i + 1} thread")]
    for i, s_ in enumerate(("+", "-")):
        hw.append(cyl(f"M4 bracket screw {i + 1}", "4 mm", "base_t + 7 mm", ["col_x", f"enc_y {s_} col_dy", "0 mm"]))
    cmds += hw
    hw_bodies = [c["params"]["body_name"] for c in hw if c["command"] == "solid.cylinder" and c["params"].get("operation") == "new"]
    cmds += comp("Hardware", hw_bodies)
    # ---- the gear-compartment door (closed) with its windows ----
    cmds.append(box("Door sheet", "door_hinge_x", "panel_right_x", "panel_bottom_y", "200 mm", "door_depth", "door_depth + door_t"))
    windows = [w for w in ("motor", "encoder") if needs_window(v, w)]       # a window (and its bezel) only where something pokes through
    for w, need in (("mwin", "motor" in windows), ("ewin", "encoder" in windows)):
        if need:
            cmds.append(box(f"Window {w}", f"{w}_x0", f"{w}_x1", f"{w}_y0", f"{w}_y1", "door_depth - 1 mm", "door_depth + door_t + 1 mm",
                            op="cut", targets=["Door sheet"]))
    cmds += comp("Door", ["Door sheet"])
    # ---- the printed parts, linked ----
    cmds += [link("Base plate", "base_plate"),
             link("Encoder bracket", "encoder_bracket"),
             link("Pulley 40T", "pulley_htd3m_40T", (0, 0, v["ls_seat_z"])),
             link("Pulley 60T", "pulley_gt2_60T", (v["stud_x"], v["stud_y"], v["stud_z0"])),
             link("Pulley 20T GT2", "pulley_gt2_20T", (v["enc_x"], v["enc_y"], v["ep_back_z"]))]
    cmds += [link(f"Door bezel {w}", f"door_bezel_{w}") for w in windows]
    if v["stud_spacer"] > 0:
        cmds.append(link("Stud spacer", "stud_spacer", (v["stud_x"], v["stud_y"], v["stud_seat_z"])))
    # ---- joints ----
    cmds += [C("occurrence.ground", occurrence="Lathe:1", grounded=True),
             C("joint.rigid_group", occurrences=["Lathe:1", "Base plate:1", "Motor:1", "Encoder:1", "Encoder bracket:1", "Belts:1", "Hardware:1"]),
             revolute("Leadscrew", "Lathe", "Leadscrew", 0, 0),
             rigid("Leadscrew", "Pulley 40T"),
             revolute("Motor", "Motor", "Motor rotor", v["motor_x"], v["motor_y"]),
             C("joint.gear", a="Motor", b="Leadscrew", ra="ls_pd_m / 2", rb="ls_pd_s / 2", internal=True, quiet=True),
             revolute("Stud", "Lathe", "Stud", v["stud_x"], v["stud_y"]),
             rigid("Stud", "Pulley 60T"),
             revolute("Encoder", "Encoder", "Encoder rotor", v["enc_x"], v["enc_y"]),
             rigid("Encoder rotor", "Pulley 20T GT2"),
             C("joint.gear", a="Stud", b="Encoder", ra="enc_pd_s / 2", rb="enc_pd_e / 2", internal=True, quiet=True),
             C("joint.create", type="revolute", name="Door hinge", flip=True, limits=[[0, 100]], quiet=True,
               a={"occurrence": "Lathe", "point": [v["door_hinge_x"], 0, v["door_hinge_z"]], "z": [0, -1, 0]},
               b={"occurrence": "Door", "point": [v["door_hinge_x"], 0, v["door_hinge_z"]], "z": [0, -1, 0]}),
             *[rigid("Door", f"Door bezel {w}") for w in windows],
             *([rigid("Stud", "Stud spacer")] if v["stud_spacer"] > 0 else []),
             *colours(windows, v["stud_spacer"] > 0, v["base_m5"] == "insert"),
             C("motion.study", name="Leadscrew one turn", steps=72, keys=[{"joint": "Motor", "points": [[0, 0], [72, 360 / v["ls_ratio"]]]}]),
             C("motion.study", name="Encoder from the stud", steps=72, keys=[{"joint": "Stud", "points": [[0, 0], [72, 360]]}]),
             C("motion.study", name="Door open", steps=50, keys=[{"joint": "Door hinge", "points": [[0, 0], [50, 100]]}])]
    return cmds


def control_box(v):
    return [link("Control frame", "control_frame"), link("Control panel", "control_panel"), link("Control lid", "control_lid"),
            C("occurrence.ground", occurrence="Control frame:1", grounded=True),
            C("joint.rigid_group", occurrences=["Control frame:1", "Control panel:1", "Control lid:1"])]


PARTS = {
    "lathe_assembly": {"build": lathe, "assembly": True, "view": "iso",
                       "views": [("_front", "top"), ("_side", "right")],   # top = looking along -Z: the photo view of the end panel
                       "desc": "ELS drive on the gear end: linked parts, motor, encoder, belts, door; joints, belt links, motion studies"},
    "control_box_assembly": {"build": control_box, "assembly": True, "view": "iso", "desc": "controller box: frame + panel + lid"},
}

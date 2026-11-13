"""ELS controller box: front panel, frame and lid. Replaces control_box.scad.

All three are modelled where they sit in the assembled box (the control_box assembly just places them at the origin):
origin = centre of the frame's front rim, +Z towards the back, the viewer stands at -Z.
  panel  Z -cb_panel_t .. 0 (front face at -cb_panel_t), TFT posts behind it to +tft_stack_h; 4x M3 flat head into the corner blocks
  frame  Z 0 .. cb_depth: 4 walls, corner screw blocks, 3 PG7 glands in the bottom wall, 2 mounting ears (M6 + pot magnet)
  lid    Z cb_depth - cb_lid_t .. cb_depth in the rear rebate, Teensy perfboard standoffs towards the front; 4x M3 flat head
Panel layout parameters are FRONT-VIEW coordinates (x right as the user sees it, y up, origin at the panel centre): the front
sketches lie on a plane facing -Z whose sketch x runs along -X, so sketch coordinates are front-view coordinates.
Print orientation (STLs): panel front face down, frame rear face down, lid outer face down.
"""
from sc import C, circle_cmds, eval_expr

FRONT = {"origin": [0, 0, 0], "x_dir": [-1, 0, 0], "y_dir": [0, 1, 0]}     # normal -Z; offset moves it towards -Z


def front_sketch(name, z="cb_panel_t"):
    return C("sketch.create", plane=FRONT, offset=z, name=name)


def rect(x0, y0, x1, y1):
    return C("sketch.line", points=[[x0, y0], [x1, y0], [x1, y1], [x0, y1]], closed=True, infer=False)


def post_pts():
    pcx, pcy = "(cb_w / 2 - cb_wall - cb_post / 2)", "(cb_h / 2 - cb_wall - cb_post / 2)"
    return [(f"{sx}{pcx}", f"{sy}{pcy}") for sx in ("-", "") for sy in ("-", "")]


def vertical_edges(v, hx, hy, z):
    return [[sx * hx, sy * hy, z] for sx in (-1, 1) for sy in (-1, 1)]


GRID = [["MODE", "UNITS", "DIR"], ["JOG <", "RETURN", "JOG >"], ["STOP L", "", "STOP R"]]


def panel(v):
    cmds = [C("solid.box", center=[0, 0, "-cb_panel_t / 2"], length="cb_w", width="cb_h", height="cb_panel_t", operation="new",
              name="Panel plate", body_name="Control panel"),
            C("solid.fillet", edges=vertical_edges(v, v["cb_w"] / 2, v["cb_h"] / 2, -v["cb_panel_t"] / 2), radius="cb_corner_r",
              name="Panel corners")]
    tft = [(f"-(tft_x {sx} tft_holes_x / 2)", f"tft_y {sy} tft_holes_y / 2") for sx in ("-", "+") for sy in ("-", "+")]
    for i, (x, y) in enumerate(tft):
        cmds.append(C("solid.cylinder", diameter="tft_post_d", height="tft_stack_h", base=[x, y, 0], operation="join",
                      name=f"TFT post {i + 1}"))
    # pilot holes for the TFT screws: from the post end to 1.2 mm short of the front face
    cmds.append(C("sketch.create", plane="XY", offset="tft_stack_h", name="TFT post holes sketch"))
    for i, (x, y) in enumerate(tft):
        cmds += circle_cmds(x, y, "m3_hole", v, f"c{i + 1}")
    cmds += [C("sketch.finish"),
             C("solid.extrude", distance="tft_stack_h + cb_panel_t - 1.2 mm", direction="negative", operation="cut", name="TFT post holes")]
    # front-view cutouts, through
    wx0 = "tft_x - tft_pcb_w / 2 + tft_win_off_x - tft_win_margin"
    wy0 = "tft_y - tft_pcb_h / 2 + tft_win_off_y - tft_win_margin"
    cmds += [front_sketch("Front cutouts sketch"),
             rect(wx0, wy0, f"{wx0} + tft_win_w + 2 * tft_win_margin", f"{wy0} + tft_win_h + 2 * tft_win_margin")]
    holes = []
    for r in range(3):
        for c in range(3):
            holes.append((f"btn_grid_x + {c - 1} * btn_pitch_x", f"btn_grid_y + {1 - r} * btn_pitch_y", "btn_hole"))
    holes += [("nutbtn_x", "nutbtn_y", "nutbtn_hole"), ("estop_x", "estop_y", "estop_hole"), ("led_x", "led_y", "led_hole"),
              ("knob_x", "knob_y", "knob_hole")]
    for i, (x, y, d) in enumerate(holes):
        cmds += circle_cmds(x, y, d, v, f"c{i + 1}")
    cmds += [C("sketch.finish"), C("solid.extrude", through_all=True, direction="negative", operation="cut",
                                   name="TFT window + 9 buttons + NUT + E-stop + LED + knob")]
    # EC11 anti-rotation tab: blind slot from the back, leaves a 1.2 mm skin
    cmds += [front_sketch("Knob tab sketch", "0 mm"),
             rect("knob_x - knob_tab_w / 2", "knob_y", "knob_x + knob_tab_w / 2", "knob_y + knob_hole / 2 + knob_tab_l"),
             C("sketch.finish"),
             C("solid.extrude", distance="cb_panel_t - 1.2 mm", operation="cut", name="Knob anti-rotation slot")]
    # corner screws, flat head from the front
    cmds.append(front_sketch("Panel screws sketch"))
    cmds += [C("sketch.point", point=[x, y]) for x, y in post_pts()]
    cmds += [C("sketch.finish"),
             C("solid.hole", sketch="Panel screws sketch", type="countersink", diameter="m3_clear", cs_diameter="cb_csk_d",
               cs_angle="90 deg", name="4x M3 flat head (front)")]
    # engraved labels (front view)
    labels = []
    for r in range(3):
        for c in range(3):
            if GRID[r][c]:
                labels.append((GRID[r][c], f"btn_grid_x + {c - 1} * btn_pitch_x", f"btn_grid_y + {1 - r} * btn_pitch_y - btn_hole / 2 - 1.5 mm", "label_size"))
    labels += [("NUT", "nutbtn_x", "nutbtn_y - 16 mm", "label_size + 0.8 mm"), ("E-STOP", "estop_x", "estop_y - 20 mm", "label_size"),
               ("FAULT", "led_x", "led_y - led_hole / 2 - 1.5 mm", "label_size"), ("PITCH / JOG", "knob_x", "knob_y - 14 mm", "label_size")]
    cmds.append(front_sketch("Labels sketch"))
    for t, x, y, h in labels:
        cmds.append(C("sketch.text", text=t, at=[x, y], height=h, align="center", vertical_align="top", font="Arial", bold=True))
    cmds += [C("sketch.finish"), C("solid.extrude", distance="label_depth", direction="negative", operation="cut", name="Engraved labels")]
    return cmds


def frame(v):
    W, H, D = v["cb_w"], v["cb_h"], v["cb_depth"]
    iw, ih = W - 2 * v["cb_wall"], H - 2 * v["cb_wall"]
    cmds = [C("solid.box", center=[0, 0, "cb_depth / 2"], length="cb_w", width="cb_h", height="cb_depth", operation="new",
              name="Frame block", body_name="Control frame"),
            C("solid.fillet", edges=vertical_edges(v, W / 2, H / 2, D / 2), radius="cb_corner_r", name="Frame corners"),
            C("solid.box", center=[0, 0, "cb_depth / 2"], length="cb_w - 2 * cb_wall", width="cb_h - 2 * cb_wall",
              height="cb_depth + 2 mm", operation="cut", name="Frame inside"),
            C("solid.fillet", edges=vertical_edges(v, iw / 2, ih / 2, D / 2), radius="max(cb_corner_r - cb_wall, 1 mm)",
              name="Frame inside corners")]
    for i, (x, y) in enumerate(post_pts()):
        cmds.append(C("solid.box", center=[x, y, "(cb_depth - cb_lid_t) / 2"], length="cb_post + 1 mm", width="cb_post + 1 mm",
                      height="cb_depth - cb_lid_t", operation="join", name=f"Corner block {i + 1}"))
    et = "(magnet_h + 1 mm)"
    for side, s in (("right", ""), ("left", "-")):
        # ear plate flush with the rear rim, two ribs along its free edges (print upright, no overhang)
        xc = f"{s}(cb_w / 2 - cb_wall + (ear_len + cb_wall) / 2)"
        cmds.append(C("solid.box", center=[xc, 0, f"cb_depth - {et} / 2"], length="ear_len + cb_wall", width="ear_w", height=et,
                      operation="join", name=f"Ear {side}"))
        for k, sy in enumerate(("", "-")):
            cmds.append(C("solid.box", center=[f"{s}(cb_w / 2 + (ear_len - 4 mm) / 2)", f"{sy}(ear_w / 2 - 1.25 mm)", f"cb_depth - {et} - 2.5 mm"],
                          length="ear_len - 4 mm", width="2.5 mm", height="5 mm", operation="join", name=f"Ear {side} rib {k + 1}"))
        cmds += [C("sketch.create", plane="XY", offset=f"cb_depth - {et}", name=f"Ear {side} holes sketch")]
        cmds += circle_cmds(f"{s}(cb_w / 2 + ear_len - 6 mm)", "0 mm", "ear_hole", v, "c1")
        cmds += [C("sketch.finish"), C("solid.extrude", distance=et, operation="cut", name=f"Ear {side} M6 hole")]
        cmds += [C("sketch.create", plane="XY", offset=f"cb_depth - {et}", name=f"Ear {side} magnet sketch")]
        cmds += circle_cmds(f"{s}(cb_w / 2 + 3 mm + magnet_d / 2 + 0.5 mm)", "0 mm", "magnet_d", v, "c1")
        cmds += [C("sketch.finish"), C("solid.extrude", distance="magnet_h", operation="cut", name=f"Ear {side} magnet pocket")]
    # M3 inserts in the corner blocks: panel side and lid side
    cmds.append(C("sketch.create", plane="XY", name="Block holes front sketch"))
    for i, (x, y) in enumerate(post_pts()):
        cmds += circle_cmds(x, y, "m3_hole", v, f"c{i + 1}")
    cmds += [C("sketch.finish"), C("solid.extrude", distance="8 mm", operation="cut", name="Block holes (panel)")]
    cmds.append(C("sketch.create", plane="XY", offset="cb_depth - cb_lid_t", name="Block holes rear sketch"))
    for i, (x, y) in enumerate(post_pts()):
        cmds += circle_cmds(x, y, "m3_hole", v, f"c{i + 1}")
    cmds += [C("sketch.finish"), C("solid.extrude", distance="8 mm", direction="negative", operation="cut", name="Block holes (lid)")]
    # PG7 glands through the bottom wall (front-view x -> X = -x)
    cmds.append(C("sketch.create", plane="XZ", offset="-cb_h / 2 - 1 mm", name="Glands sketch"))
    for i, gx in enumerate(("-gland_pitch", "0 mm", "gland_pitch")):
        cmds += circle_cmds(f"-({gx})", "-gland_z", "gland_d", v, f"c{i + 1}")
    cmds += [C("sketch.finish"), C("solid.extrude", distance="cb_wall + 2 mm", operation="cut", name="3x PG7 glands")]
    return cmds


def lid(v):
    c = v["cb_lid_clear"]
    lw, lh = v["cb_w"] - 2 * v["cb_wall"] - 2 * c, v["cb_h"] - 2 * v["cb_wall"] - 2 * c
    zt = "cb_depth - cb_lid_t"
    cmds = [C("solid.box", center=[0, 0, "cb_depth - cb_lid_t / 2"], length="cb_w - 2 * cb_wall - 2 * cb_lid_clear",
              width="cb_h - 2 * cb_wall - 2 * cb_lid_clear", height="cb_lid_t", operation="new", name="Lid plate", body_name="Control lid"),
            C("solid.fillet", edges=vertical_edges(v, lw / 2, lh / 2, v["cb_depth"] - v["cb_lid_t"] / 2), radius="1.5 mm", name="Lid corners")]
    pts = [(f"-({sx}perf_holes_x / 2)", f"{sy}perf_holes_y / 2") for sx in ("-", "") for sy in ("-", "")]
    for i, (x, y) in enumerate(pts):
        cmds.append(C("solid.cylinder", diameter="perf_stand_d", height="perf_stand_h", base=[x, y, f"{zt} - perf_stand_h"],
                      operation="join", name=f"Perfboard standoff {i + 1}"))
    cmds.append(C("sketch.create", plane="XY", offset=zt, name="Perfboard holes sketch"))
    for i, (x, y) in enumerate(pts):
        cmds += circle_cmds(x, y, "m25_hole", v, f"c{i + 1}")
    cmds += [C("sketch.finish"), C("solid.extrude", distance="perf_stand_h + 1 mm", direction="negative", operation="cut",
                                   name="M2.5 pilot holes")]
    cmds.append(C("sketch.create", plane="XY", offset="cb_depth", name="Lid screws sketch"))
    cmds += [C("sketch.point", point=[x, y]) for x, y in post_pts()]
    cmds += [C("sketch.finish"),
             C("solid.hole", sketch="Lid screws sketch", type="countersink", diameter="m3_clear", cs_diameter="cb_csk_d",
               cs_angle="90 deg", name="4x M3 flat head (rear)")]
    return cmds


def flip_x(body, z):
    """Turn about X (front <-> back) and lift so the face that was at Z = z lies on the bed."""
    return [C("solid.move", bodies=[body], axis=[1, 0, 0], angle="180 deg"), C("solid.move", bodies=[body], translate=[0, 0, z])]


PARTS = {
    "control_panel": {"build": panel, "print": [C("solid.move", bodies=["Control panel"], translate=[0, 0, "cb_panel_t"])],
                      "camera": {"target": [0, 0, 0], "yaw": 3.14159265, "pitch": -1.57079, "distance": 330},   # from -Z: the front, as the user sees it
                      "desc": "front panel: TFT window + posts, 9 + NUT buttons, E-stop, LED, knob, engraved labels"},
    "control_frame": {"build": frame, "print": flip_x("Control frame", "cb_depth"),
                      "desc": "box frame: corner screw blocks, 3x PG7 glands, 2 mounting ears (M6 + magnet)"},
    "control_lid": {"build": lid, "print": flip_x("Control lid", "cb_depth"), "desc": "rear lid with the Teensy perfboard standoffs"},
}

"""Printed trim frames for the windows cut in the change-gear door where the motor (and the encoder) poke through.

The window edge away from the hinge leaves the room the door needs to swing past the part's outer back corner; the other
edges are tight (params.json: mwin_* / ewin_*). The frame sits on the door's OUTSIDE face (Z = door_depth + door_t), held
by M3 screws + nyloc nuts only where there is sheet behind them; it is trimmed to the door's right edge and bottom fold.
Glue a brush strip (or soft foam) round the opening. Modelled in place on the closed door; the STL is moved flat with the
window centre on the origin. The cutting template (dxf/door_window_template_*.dxf) is the window + holes, 1:1, centred.
"""
from sc import C, circle_cmds, eval_expr


def window(w):
    p = "mwin" if w == "motor" else "ewin"
    return [f"{p}_x0", f"{p}_x1", f"{p}_y0", f"{p}_y1"]


def holes(v, W):
    """M3 holes on the frame's centre line (corners, mid-sides, just above the window bottom) with sheet behind them."""
    x0, x1, y0, y1 = W
    xs = {"L": f"{x0} - bezel_w / 2", "C": f"({x0} + {x1}) / 2", "R": f"{x1} + bezel_w / 2"}
    ys = {"T": f"{y1} + bezel_w / 2", "M": f"({y0} + {y1}) / 2", "B8": f"{y0} + 8 mm", "B": f"{y0} - bezel_w / 2"}
    cand = [("L", "T"), ("R", "T"), ("C", "T"), ("L", "M"), ("R", "M"), ("L", "B8"), ("R", "B8"), ("L", "B"), ("R", "B"), ("C", "B")]
    out = []
    for cx, cy in cand:
        x, y = xs[cx], ys[cy]
        if eval_expr(y, v) - v["panel_bottom_y"] >= v["bezel_hole_edge_min"] and v["panel_right_x"] - eval_expr(x, v) >= v["bezel_hole_edge_min"]:
            out.append((x, y))
    return out


def make(which):
    def build(v):
        x0, x1, y0, y1 = W = window(which)
        z0 = "door_depth + door_t"
        cx, cy = f"({x0} + {x1}) / 2", f"({y0} + {y1}) / 2"
        X0, X1 = eval_expr(x0, v) - v["bezel_w"], eval_expr(x1, v) + v["bezel_w"]
        Y0, Y1 = eval_expr(y0, v) - v["bezel_w"], eval_expr(y1, v) + v["bezel_w"]
        zm = v["door_depth"] + v["door_t"] + v["bezel_t"] / 2
        name = f"Door bezel ({which})"
        cmds = [C("solid.box", center=[cx, cy, f"{z0} + bezel_t / 2"], length=f"{x1} - {x0} + 2 * bezel_w",
                  width=f"{y1} - {y0} + 2 * bezel_w", height="bezel_t", operation="new", name="Frame", body_name=name),
                C("solid.fillet", edges=[[X0, Y0, zm], [X1, Y0, zm], [X1, Y1, zm], [X0, Y1, zm]], radius="bezel_r", name="Frame corners"),
                C("solid.box", corner=["panel_right_x", f"{y0} - 200 mm", f"{z0} - 1 mm"], length="200 mm", width=f"{y1} - {y0} + 400 mm",
                  height="bezel_t + 2 mm", operation="cut", name="Trim: door right edge"),
                C("solid.box", corner=[f"{x0} - 200 mm", "panel_bottom_y - 200 mm", f"{z0} - 1 mm"], length=f"{x1} - {x0} + 400 mm",
                  width="200 mm", height="bezel_t + 2 mm", operation="cut", name="Trim: door bottom fold"),
                C("solid.box", center=[cx, cy, f"{z0} + bezel_t / 2"], length=f"{x1} - {x0}", width=f"{y1} - {y0}",
                  height="bezel_t + 2 mm", operation="cut", name="Window")]
        hs = holes(v, W)
        if hs:
            cmds.append(C("sketch.create", plane="XY", offset=z0, name="M3 holes sketch"))
            for i, (x, y) in enumerate(hs):
                cmds += circle_cmds(x, y, "m3_clear", v, f"c{i + 1}")
            cmds += [C("sketch.finish"), C("solid.extrude", distance="bezel_t", operation="cut", name=f"{len(hs)}x M3 (sheet behind)")]
        return cmds

    def template(v, out):
        """Export-only: the window + holes, 1:1, centred on the window, as DXF."""
        x0, x1, y0, y1 = W = window(which)
        cx, cy = f"({x0} + {x1}) / 2", f"({y0} + {y1}) / 2"
        hw, hh = f"({x1} - {x0}) / 2", f"({y1} - {y0}) / 2"
        cmds = [C("sketch.create", plane="XY", name="Window template"),
                C("sketch.line", points=[[f"-{hw}", f"-{hh}"], [hw, f"-{hh}"], [hw, hh], [f"-{hw}", hh]], closed=True, infer=False)]
        for i, (x, y) in enumerate(holes(v, W)):
            cmds += circle_cmds(f"{x} - {cx}", f"{y} - {cy}", "m3_clear", v, f"c{i + 1}")
        return cmds + [C("sketch.finish"),
                       C("sketch.export_dxf", sketch="Window template", path=out("dxf", f"door_window_template_{which}.dxf"),
                         join=True, layers="roles")]

    name = f"Door bezel ({which})"
    prn = [C("solid.move", bodies=[name], translate=[f"-({x})" for x in (f"({window(which)[0]} + {window(which)[1]}) / 2",
                                                                           f"({window(which)[2]} + {window(which)[3]}) / 2",
                                                                           "door_depth + door_t")])]
    return {"build": build, "print": prn, "post": template,
            "skip": lambda v: not needs_window(v, which), "skip_why": f"the {which} stays inside the closed door: no window",
            "stale": [("dxf", f"door_window_template_{which}.dxf")],
            "desc": f"trim frame + cutting template for the {which} window in the gear door"}


def needs_window(v, which):
    """Whatever reaches closer than door_clear to the closed door goes through a window."""
    front = v["motor_front_z"] if which == "motor" else v["enc_front_z"]
    return front > v["door_depth"] - v["door_clear"]


PARTS = {"door_bezel_motor": make("motor"), "door_bezel_encoder": make("encoder")}

"""Flat base plate that replaces the change-gear banjo and carries the motor (on 4 M5 standoffs) and the encoder bracket.

Lathe frame (origin = leadscrew axis L on the banjo seat, +X right, +Y up, +Z towards the door); the plate lies on the old
banjo seat, Z 0 .. base_t, back face flat against the casting (it prints that way: back face down, no supports).
  * outline = union of three hulls: the lower body (B1/B2 slot ends + the four standoff bosses), the arm from B1 to the
    encoder pad, and the pad under the encoder bracket (bracket outline + base_pad_margin)
  * clamped by the old banjo bolts B1/B2: M5 countersunk screws in slots, +-base_travel/2 along Y; the whole plate slides
    along Y to tension the HTD belt. Clearance slot round the leadscrew shoulder at L, same travel
  * 4x M5 at the NEMA23 bolt square (countersunk on the BACK: screws into the hex standoffs), hole round the motor pulley,
    2x M4 for the encoder bracket inserts (countersunk on the back), a lightening window along the arm
  * front face: 0.5 mm relief under the 40T disc, swept countersinks of the B1/B2 heads, and a 4 mm perimeter rib, left out
    wherever the HTD belt / 40T / motor pulley, the bolt heads, the standoffs or the bracket are
The DXF (dxf/base_plate.dxf) is the section at half thickness: outline + every through hole, for 6-8 mm aluminium.
"""
from sc import C, hulls_sketch, stadium

TRAV = "base_travel / 2"
SO = [(f"so{i}_x", f"so{i}_y") for i in (1, 2, 3, 4)]          # the standoffs: the NEMA23 bolt square, turned with motor_angle


def lower_body():
    c = stadium("B1_x", f"B1_y + {TRAV}", f"B1_y - {TRAV}", "base_boss_r") + \
        stadium("B2_x", f"B2_y + {TRAV}", f"B2_y - {TRAV}", "base_boss_r")
    for x, y in SO:
        c.append((x, y, "standoff_boss_r"))
    return c


def arm(r="base_arm_w / 2"):
    return [("B1_x", "arm_ay", r), ("col_cx", "enc_y", r)]


def pad(extra="base_pad_margin"):
    """Encoder bracket outline (D: circle round the +X slot end, square corners at the open end) grown by `extra`."""
    return [("col_cx", "enc_y", f"eb_out + {extra}"),
            ("cup_left_x", "enc_y + eb_out", extra), ("cup_left_x", "enc_y - eb_out", extra),
            ("col_x", "enc_y + col_dy", f"eb_col_r + {extra}"), ("col_x", "enc_y - col_dy", f"eb_col_r + {extra}")]


def window():
    def at(t):
        return (f"B1_x + (col_cx - B1_x) * {t} / arm_len", f"arm_ay + (enc_y - arm_ay) * {t} / arm_len", "base_window_w / 2")
    return [at("win_t0"), at("win_t1")]


def build(v):
    top = "base_t"
    cmds = []
    # ---- outline: three hulls joined ----
    cmds += hulls_sketch("Lower body sketch", None, [lower_body()], v)
    cmds.append(C("solid.extrude", distance="base_t", operation="new", name="Lower body", body_name="Base plate"))
    cmds += hulls_sketch("Arm sketch", None, [arm()], v)
    cmds.append(C("solid.extrude", distance="base_t", operation="join", name="Arm"))
    cmds += hulls_sketch("Encoder pad sketch", None, [pad()], v)
    cmds.append(C("solid.extrude", distance="base_t", operation="join", name="Encoder pad"))
    # ---- rib: the outline as a 3 mm band on the front face, then the keep-outs cut away ----
    # rib blank: the same three outline sketches again (no projection: it would not follow a parameter edit), base_rib_t taller
    # at both ends; a CLOSED shell of it (no face picks, which can land on other faces after an edit) leaves a cavity that is the
    # exact inward offset of the outline; cutting the end caps off leaves the base_rib_t band, base_t .. base_t + base_rib_h
    z0, h = "base_t - base_rib_t", "base_rib_h + 2 * base_rib_t"
    cmds += [C("solid.extrude", sketch="Lower body sketch", distance=h, start_offset=z0, operation="new",
               name="Rib blank: lower body", body_name="Rib"),
             C("solid.extrude", sketch="Arm sketch", distance=h, start_offset=z0, operation="join", targets=["Rib"], name="Rib blank: arm"),
             C("solid.extrude", sketch="Encoder pad sketch", distance=h, start_offset=z0, operation="join", targets=["Rib"],
               name="Rib blank: pad"),
             C("solid.shell", faces=[], thickness="base_rib_t", direction="inside", body="Rib", name="Rib band (closed shell)"),
             C("solid.box", corner=["-400 mm", "-400 mm", "base_t - 100 mm"], length="800 mm", width="800 mm", height="100 mm",
               operation="cut", targets=["Rib"], name="Rib: cut the bottom cap"),
             C("solid.box", corner=["-400 mm", "-400 mm", "base_t + base_rib_h"], length="800 mm", width="800 mm", height="100 mm",
               operation="cut", targets=["Rib"], name="Rib: cut the top cap"),
             C("solid.combine", target="Base plate", tools=["Rib"], operation="join")]
    keep = [("Rib keep-out: HTD belt + 40T + motor pulley",
             [[("0", TRAV, "belt_env_r + 3 mm"), ("0", f"-{TRAV}", "belt_env_r + 3 mm"),
               ("motor_x", f"motor_y + {TRAV}", "(mp_buy_flange_d + 8 mm) / 2"), ("motor_x", f"motor_y - {TRAV}", "(mp_buy_flange_d + 8 mm) / 2")]]),
            ("Rib keep-out: B1", [stadium("B1_x", f"B1_y + {TRAV}", f"B1_y - {TRAV}", "base_boss_r + 1 mm")]),
            ("Rib keep-out: B2", [stadium("B2_x", f"B2_y + {TRAV}", f"B2_y - {TRAV}", "base_boss_r + 1 mm")]),
            ("Rib keep-out: standoffs", [("circle", x, y, "2 * (standoff_boss_r + 1 mm)") for x, y in SO]),
            ("Rib keep-out: bracket", [pad("base_pad_margin + 1 mm")])]
    for name, shapes in keep:
        cmds += hulls_sketch(name + " sketch", top, shapes, v)
        # from the plate front face up: only the rib is in that range
        cmds.append(C("solid.extrude", distance="base_rib_h + 1 mm", operation="cut", name=name))
    # ---- keep inside the panel edges (2 mm margin): bottom and right ----
    cmds += [C("solid.box", corner=["-400 mm", "plate_y_min - 400 mm", "-1 mm"], length="800 mm", width="400 mm",
               height="base_t + base_rib_h + 2 mm", operation="cut", targets=["Base plate"], name="Keep-in: panel bottom"),
             C("solid.box", corner=["plate_x_max", "-400 mm", "-1 mm"], length="400 mm", width="800 mm",
               height="base_t + base_rib_h + 2 mm", operation="cut", targets=["Base plate"], name="Keep-in: panel right")]
    # ---- through holes (the DXF) ----
    shapes = [stadium("B1_x", f"B1_y + {TRAV}", f"B1_y - {TRAV}", "(banjo_bolt_d + base_bolt_clear) / 2"),
              stadium("B2_x", f"B2_y + {TRAV}", f"B2_y - {TRAV}", "(banjo_bolt_d + base_bolt_clear) / 2"),
              stadium("0", TRAV, f"-{TRAV}", "ls_boss_d / 2 + ls_boss_clear"),
              ("circle", "motor_x", "motor_y", "mp_buy_flange_d + mp_hole_clear")]
    if v["win_t1"] > v["win_t0"]:
        shapes.append(window())
    cmds += hulls_sketch("Through holes sketch", None, shapes, v)
    cmds.append(C("solid.extrude", distance="base_t + base_rib_h + 1 mm", operation="cut", name="Through holes"))
    # ---- screw holes (drilled up from the back face); the M5 standoff holes follow the option base_m5 (build-time choice) ----
    cmds += [C("sketch.create", plane="XY", name="M5 standoff screws sketch")]
    cmds += [C("sketch.point", point=[x, y]) for x, y in SO]
    cmds.append(C("sketch.finish"))
    m5 = v["base_m5"]
    if m5 == "csk":         # clearance + countersink on the BACK: M5 flat-head screws into the standoffs
        cmds.append(C("solid.hole", sketch="M5 standoff screws sketch", type="countersink", diameter="m5_clear + 0.1 mm",
                      cs_diameter="m5_csk_d", cs_angle="90 deg", name="M5 standoff screws (csk back)"))
    elif m5 in ("tap", "insert"):   # 4.2 mm for an M5 thread (male-threaded standoffs) / 6.4 mm for an M5 heat-set insert
        cmds.append(C("solid.hole", sketch="M5 standoff screws sketch", type="simple", diameter="4.2 mm" if m5 == "tap" else "6.4 mm",
                      name=f"M5 standoff holes ({m5})"))
    else:
        raise ValueError(f"base_m5 must be csk, tap or insert, not {m5!r}")
    cmds += [C("sketch.create", plane="XY", name="M4 bracket screws sketch"),
             C("sketch.point", point=["col_x", "enc_y + col_dy"]),
             C("sketch.point", point=["col_x", "enc_y - col_dy"]),
             C("sketch.finish"),
             C("solid.hole", sketch="M4 bracket screws sketch", type="countersink", diameter="m4_clear",
               cs_diameter="m4_csk_d", cs_angle="90 deg", name="M4 bracket screws (csk back)")]
    # ---- front face: relief under the 40T disc, swept B1/B2 countersinks ----
    cmds += hulls_sketch("40T relief sketch", "base_t - base_relief", [stadium("0", TRAV, f"-{TRAV}", "ls_flange_r + 1.5 mm")], v)
    cmds.append(C("solid.extrude", distance="base_relief + 1 mm", operation="cut", name="40T relief"))
    cmds += hulls_sketch("B1/B2 countersink sketch", top,
                         [stadium("B1_x", f"B1_y + {TRAV}", f"B1_y - {TRAV}", "base_head_d / 2"),
                          stadium("B2_x", f"B2_y + {TRAV}", f"B2_y - {TRAV}", "base_head_d / 2")], v)
    cmds.append(C("solid.extrude", distance="(base_head_d - banjo_bolt_d - base_bolt_clear) / 2", direction="negative",
                  taper="-45 deg", operation="cut", name="B1/B2 countersinks (swept)"))
    return cmds


def dxf(v, out):
    """Export-only steps (run on the saved design, not kept): the section at half thickness -> DXF."""
    return [C("solid.box", corner=["-400 mm", "-400 mm", "base_t / 2"], length="800 mm", width="800 mm", height="100 mm",
              operation="cut", name="Section cut"),
            C("sketch.create", plane="XY", offset="base_t / 2", name="DXF section"),
            C("sketch.project", refs=[{"face": [0, -20, v["base_t"] / 2]}], construction=False),
            C("sketch.finish"),
            C("sketch.export_dxf", sketch="DXF section", path=out("dxf", "base_plate.dxf"), join=True, layers="roles")]


PARTS = {"base_plate": {"build": build, "desc": "flat base plate on the banjo seat: motor standoffs, encoder bracket, B1/B2 slots",
                        "post": dxf}}

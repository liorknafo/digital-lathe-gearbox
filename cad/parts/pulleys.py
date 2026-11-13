"""Printed belt pulleys (HTD-3M and GT2), axis = Z. Replaces pulley_core.scad / pulley_htd3m.scad / pulley_gt2.scad.

Print orientation = lathe orientation: bottom flange on the bed (z = 0, towards the casting), toothed band, top flange
(45 deg underside, no support), hub on top (towards the door). Bore, keyway or D-flat and the set screw are cut in.
Tooth grooves (FDM approximations, as before):
  HTD-3M: tip diameter N*3/pi - 0.762; groove = circle r 1.0 (+extra) centred 0.14 below the tip surface, straight sides out.
  GT2:    tip diameter N*2/pi - 0.508; groove = hull of a circle r 0.60 (+extra) centred 0.15 below the tip and a 1.4 (+2 extra) mouth.
"""
from sc import C, hull_sketch


def poly(points):
    """Closed polyline through expression points (each point fixed by its expressions: fully constrained)."""
    return C("sketch.line", points=[list(p) for p in points], closed=True, infer=False)


def pulley(v, *, name, n, profile, od, fl_extra, flange_t, tooth_len, bore, bottom_flange=True, top_flange=True,
           hub_d, hub_len, keyway=None, flat=None, setscrew=None, groove_extra):
    """All lengths are expressions (strings) over the parameters. Returns the command list."""
    nv = lambda e: __import__("sc").eval_expr(e, v)
    fl_d = f"({od} + 2 * {fl_extra})"
    bt = flange_t if bottom_flange else "0 mm"
    z1 = f"({bt} + {tooth_len})"
    ft = f"max({flange_t}, {fl_extra})"                 # top flange: 45 deg underside over fl_extra, flat rim above if thicker
    zh = f"({z1} + {ft})" if top_flange else z1
    base_d = fl_d if top_flange else od
    hd = f"max({hub_d}, {bore} + 2 * tol + 2 * (1 mm + {setscrew['nut_t'] if setscrew else '0 mm'} + 0.2 mm + 2 mm))" if setscrew else hub_d
    cone_h = f"max(0 mm, min(({hd} - {base_d}) / 2, {hub_len} * 0.7))"   # cone from base_d up to the hub, only if the hub is wider
    total = f"({zh} + {hub_len})"
    br = f"({bore} / 2 + tol)"
    cmds = []
    # ---- body ----
    if bottom_flange:
        cmds.append(C("solid.cylinder", diameter=fl_d, height=flange_t, base=[0, 0, 0], operation="new",
                      name="Bottom flange", body_name=name))
        cmds.append(C("solid.cylinder", diameter=od, height=tooth_len, base=[0, 0, bt], operation="join", name="Toothed band"))
    else:
        cmds.append(C("solid.cylinder", diameter=od, height=tooth_len, base=[0, 0, 0], operation="new",
                      name="Toothed band", body_name=name))
    if top_flange:
        # a full disc max(flange_t, fl_extra) thick, then its underside turned away at 45 deg (a revolved triangle): one shape for
        # every value, so a native edit of the flange matches a rebuild. Sketch on XZ: sketch x = X, sketch y = -Z.
        r0, r1 = f"({od} / 2)", f"({fl_d} / 2 + 1 mm)"
        cmds += [C("solid.cylinder", diameter=fl_d, height=ft, base=[0, 0, z1], operation="join", name="Top flange disc"),
                 C("sketch.create", plane="XZ", name="Top flange underside sketch"),
                 C("sketch.line", points=[[r0, f"-{z1}"], [r1, f"-{z1}"], [r1, f"-({z1} + {fl_extra} + 1 mm)"]], closed=True, infer=False),
                 C("sketch.finish"),
                 C("solid.revolve", axis="Z", operation="cut", name="Top flange 45 deg underside")]
    if nv(hub_len) > 0:
        # one revolved profile for every value (cone or not): a native edit across the cone / no-cone boundary matches a rebuild.
        # r0 = min(base_d, hd) / 2; with no cone the 0.001 mm step is a collinear piece of the hub wall. Sketch XZ: y = -Z.
        r0, rh, ce = f"(min({base_d}, {hd}) / 2)", f"({hd} / 2)", f"max({cone_h}, 0.001 mm)"
        cmds += [C("sketch.create", plane="XZ", name="Hub profile sketch"),
                 C("sketch.line", points=[[0, f"-{zh}"], [r0, f"-{zh}"], [rh, f"-({zh} + {ce})"], [rh, f"-({zh} + {hub_len})"],
                                          [0, f"-({zh} + {hub_len})"]], closed=True, infer=False),
                 C("sketch.finish"),
                 C("solid.revolve", axis="Z", operation="join", name="Hub")]
    # ---- one tooth groove at +Y, patterned n times ----
    R = f"({od} / 2)"
    if profile == "htd3m":
        r = f"(1 mm + {groove_extra})"
        c = f"({R} - 0.14 mm)"
        top = f"({R} + 0.6 mm)"
        g = [C("sketch.arc.center_point", center=[0, c], start=[-nv(r), nv(c)], end=[nv(r), nv(c)]),
             C("sketch.dimension", entities=["a1"], type="radius", value=r),
             C("sketch.line", points=["a1.end", [r, top]], infer=False),
             C("sketch.constraint.tangent", a="l1", b="a1"),
             C("sketch.line", points=["l1.end", [f"-{r}", top]], infer=False),
             C("sketch.line", points=["l2.end", "a1.start"], infer=False),
             C("sketch.constraint.tangent", a="l3", b="a1")]
    else:
        r = f"(0.6 mm + {groove_extra})"
        w = f"(0.7 mm + {groove_extra})"
        g, _ = hull_sketch([("0", f"{R} - 0.15 mm", r), (w, R, 0), (w, f"{R} + 0.6 mm", 0),
                            (f"-{w}", f"{R} + 0.6 mm", 0), (f"-{w}", R, 0)], v)
    cmds += [C("sketch.create", plane="XY", offset=bt, name="Groove sketch")] + g + [
        C("sketch.finish"),
        C("solid.extrude", distance=tooth_len, operation="cut", name="Groove"),
        C("solid.pattern.circular", features=["Groove"], axis="Z", count=n, name="Grooves")]
    # ---- bore: round, D-flat (+X side) or keyway (+Y) ----
    if flat and nv(flat) > 0:                     # a 0 flat (or none) = a round bore
        xf = f"({bore} / 2 - {flat} + tol)"
        import math
        brv, xfv = nv(br), nv(xf)
        hv = math.sqrt(brv * brv - xfv * xfv)
        cmds += [C("sketch.create", plane="XY", name="Bore sketch"),
                 C("sketch.arc.center_point", center=[0, 0], start=[xfv, hv], end=[xfv, -hv]),
                 C("sketch.dimension", entities=["a1"], type="radius", value=br),
                 C("sketch.line", points=["a1.end", "a1.start"], infer=False),
                 C("sketch.constraint.horizontal_vertical", line="l1"),
                 C("sketch.dimension", entities=["origin", "l1"], type="horizontal", value=xf),
                 C("sketch.finish"),
                 C("solid.extrude", distance=total, operation="cut", name="Bore (D-flat)")]
    else:
        cmds += [C("sketch.create", plane="XY", name="Bore sketch"),
                 C("sketch.circle.center", center=[0, 0], radius=nv(br)),
                 C("sketch.dimension", entities=["c1"], type="radius", value=br),
                 C("sketch.finish"),
                 C("solid.extrude", distance=total, operation="cut", name="Bore")]
    if keyway and nv(keyway[0]) > 0:               # a 0 keyway width = none
        kw, kh = keyway
        hw = f"(({kw} + 2 * tol) / 2)"
        ky = f"({br} + {kh} + tol)"
        cmds += [C("sketch.create", plane="XY", name="Keyway sketch"),
                 poly([[f"-{hw}", 0], [hw, 0], [hw, ky], [f"-{hw}", ky]]),
                 C("sketch.finish"),
                 C("solid.extrude", distance=total, operation="cut", name="Keyway")]
    # ---- set screw along +X with a captive nut trap sliding in from the top face ----
    if setscrew:
        zc = f"({zh} + {cone_h} + ({hub_len} - {cone_h}) / 2)"
        a = f"({setscrew['af']} + 0.3 mm)"                   # nut across flats + 2 x 0.15
        t = f"({setscrew['nut_t']} + 0.2 mm + 0.15 mm)"
        rr = f"({a} / sqrt(3))"                             # hexagon corner radius
        x0 = f"({br} + 1 mm)"
        rout = f"(max({hd}, {fl_d if top_flange or bottom_flange else od}) / 2 + 1 mm)"
        cmds += [C("sketch.create", plane="YZ", name="Set screw sketch"),
                 C("sketch.circle.center", center=[0, nv(zc)], radius=nv(setscrew["clear"]) / 2),
                 C("sketch.dimension", entities=["c1"], type="diameter", value=setscrew["clear"]),
                 C("sketch.dimension", entities=["origin", "c1.center"], type="horizontal", value="0 mm"),
                 C("sketch.dimension", entities=["origin", "c1.center"], type="vertical", value=zc),
                 C("sketch.finish"),
                 C("solid.extrude", distance=rout, operation="cut", name="Set screw hole"),
                 C("sketch.create", plane="YZ", offset=x0, name="Nut trap sketch"),
                 poly([[0, f"{zc} + {rr}"], [f"-{a} / 2", f"{zc} + {rr} / 2"], [f"-{a} / 2", f"{zc} - {rr} / 2"],
                       [0, f"{zc} - {rr}"], [f"{a} / 2", f"{zc} - {rr} / 2"], [f"{a} / 2", f"{zc} + {rr} / 2"]]),
                 C("sketch.finish"),
                 C("solid.extrude", distance=t, operation="cut", name="Nut trap"),
                 C("sketch.create", plane="YZ", offset=x0, name="Nut slot sketch"),
                 poly([[f"-{a} / 2", zc], [f"{a} / 2", zc], [f"{a} / 2", f"{total} + 1 mm"], [f"-{a} / 2", f"{total} + 1 mm"]]),
                 C("sketch.finish"),
                 C("solid.extrude", distance=t, operation="cut", name="Nut slot")]
    return cmds


M3 = {"clear": "m3_clear", "af": "m3_nut_af", "nut_t": "m3_nut_t"}
M4 = {"clear": "m4_clear", "af": "m4_nut_af", "nut_t": "m4_nut_t"}


def htd3m_40T(v):
    return pulley(v, name="Pulley HTD-3M 40T", n="ls_teeth_screw", profile="htd3m", od="ls_od", fl_extra="htd_flange_extra",
                  flange_t="htd_flange_t", tooth_len="htd_tooth_len", bore="ls_shaft_bore", hub_d="ls_hub_dia",
                  hub_len="ls_hub_len", keyway=("ls_keyway_w", "ls_keyway_h"), groove_extra="htd_groove_extra",
                  setscrew=M4 if v["ls_setscrew"] else None)      # option ls_setscrew (build-time choice)


def htd3m_20T(v):
    return pulley(v, name="Pulley HTD-3M 20T", n="ls_teeth_motor", profile="htd3m", od="mp_od", fl_extra="htd_flange_extra",
                  flange_t="htd_flange_t", tooth_len="mp_tooth_len", bore="motor_shaft_d", top_flange=False,
                  hub_d="mp_hub_d", hub_len="mp_hub_len", flat="motor_shaft_flat", setscrew=M4, groove_extra="htd_groove_extra")


def gt2_60T(v):
    return pulley(v, name="Pulley GT2 60T", n="enc_teeth_stud", profile="gt2", od="stud_od", fl_extra="gt2_flange_extra",
                  flange_t="gt2_flange_t", tooth_len="gt2_tooth_len", bore="stud_bore", hub_d="stud_hub_dia",
                  hub_len="stud_hub_len", keyway=("stud_keyway_w", "stud_keyway_h"), groove_extra="gt2_groove_extra",
                  setscrew=M3 if v["stud_setscrew"] else None)    # option stud_setscrew (build-time choice)


def gt2_20T(v):
    return pulley(v, name="Pulley GT2 20T", n="enc_teeth_encoder", profile="gt2", od="ep_od", fl_extra="gt2_flange_extra",
                  flange_t="gt2_flange_t", tooth_len="gt2_tooth_len", bore="enc_shaft_d", top_flange=False,
                  hub_d="ep_hub_d", hub_len="ep_hub_len", flat="enc_shaft_flat", setscrew=M3, groove_extra="gt2_groove_extra")


PARTS = {
    "pulley_htd3m_40T": {"build": htd3m_40T, "desc": "leadscrew pulley, 15 bore + 4 mm keyway, seats on the 16.7 shoulder"},
    "pulley_htd3m_20T": {"build": htd3m_20T, "desc": "printable backup of the bought motor pulley, 8 mm D bore + M4 set screw"},
    "pulley_gt2_60T": {"build": gt2_60T, "desc": "stud pulley, 15 bore + 4 mm keyway"},
    "pulley_gt2_20T": {"build": gt2_20T, "desc": "printable encoder pulley, 6 mm D bore + M3 set screw"},
}

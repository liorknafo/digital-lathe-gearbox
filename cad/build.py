#!/usr/bin/env python3
"""build.py -- build the SolidCraft designs of the ELS retrofit from cad/params.json.

  python3 cad/build.py                 every part, then the assemblies, the exports and the fit checks
  python3 cad/build.py plate           only targets whose name contains "plate"
  python3 cad/build.py --script NAME   only write cad/build/scripts/NAME.json (the command script; `batch {path}` runs it in the app)
  python3 cad/build.py --list          list the targets
  python3 cad/build.py --checks        only the fit checks (on the designs as built) -> cad/fit_checks.md
A full build (no name) ends with the fit checks (exit 1 on any FAIL) and the 3D viewer pages (cad/viewer/*.html).

Per part: cad/designs/NAME.sc (parametric SolidCraft design: the shared parameters it uses + its timeline),
cad/step/NAME.step, cad/stl/NAME.stl (print orientation) and cad/png/NAME.png. Needs SolidCraft (solidcraft-cli; set
SOLIDCRAFT_CLI if it is not in /Applications/SolidCraft.app).
"""
import importlib
import json
import os
import shutil
import sys

CAD = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(CAD, "lib"))
sys.path.insert(0, os.path.join(CAD, "parts"))
import sc  # noqa: E402

PART_MODULES = ["pulleys", "base_plate", "encoder_bracket", "spacer", "door_bezel", "control_box", "assemblies"]   # assemblies last: they link the parts


def targets():
    out = {}
    for m in PART_MODULES:
        mod = importlib.import_module(m)
        if hasattr(mod, "DESIGNS"):
            mod.DESIGNS = os.path.join(CAD, "designs")
        for name, spec in mod.PARTS.items():
            out[name] = spec
    return out


def part_script(P, v, name, spec):
    cmds = spec["build"](v)
    if spec.get("assembly"):
        return sc.freeze(cmds, P, v)            # no parameter table in an assembly (see sc.freeze)
    return sc.script(P, cmds)


def write_script(name, commands):
    d = os.path.join(sc.BUILD, "scripts")
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, f"{name}.json")
    with open(path, "w") as f:
        json.dump({"commands": commands}, f, indent=1)
    stage = os.environ.get("SC_STAGE")          # the MCP server's own folder, for `batch {path}` in the app
    if stage:
        shutil.copy(path, os.path.join(stage, f"{name}.json"))
    return path


def build_part(P, v, name, path, spec):
    for d in ("designs", "step", "stl", "png"):
        os.makedirs(os.path.join(CAD, d), exist_ok=True)
    design = os.path.join(CAD, "designs", f"{name}.sc")
    sc.run_cli(["run", path, "--quiet", "--save", design, "--out", os.path.join(CAD, "step", f"{name}.step")])
    # print orientation (if it differs from the lathe orientation the part is modelled in) only for the STL
    moves = spec.get("print", [])
    if spec.get("assembly"):
        pass                                    # no print STL for an assembly
    elif moves:
        mpath = os.path.join(sc.BUILD, "scripts", f"{name}.print.json")
        with open(mpath, "w") as f:
            json.dump({"commands": moves}, f)
        sc.run_cli(["run", mpath, "--in", design, "--quiet", "--out", os.path.join(CAD, "stl", f"{name}.stl")])
    else:
        sc.run_cli(["run", "--in", design, "--quiet", "--out", os.path.join(CAD, "stl", f"{name}.stl")])
    post = spec.get("post")
    if post:                                    # export-only steps on the saved design (DXF ...): not saved
        os.makedirs(os.path.join(CAD, "dxf"), exist_ok=True)
        steps = post(v, lambda *p: os.path.join(CAD, *p))
        ppath = os.path.join(sc.BUILD, "scripts", f"{name}.post.json")
        with open(ppath, "w") as f:
            json.dump({"commands": steps}, f)
        sc.run_cli(["run", ppath, "--in", design, "--quiet"])
    look = ["--camera", json.dumps(spec["camera"])] if spec.get("camera") else ["--view", spec.get("view", "iso")]
    sc.run_cli(["snapshot", "--in", design, "--out", os.path.join(CAD, "png", f"{name}.png"), "--width", "900",
                "--height", "700", *look, "--no-grid", "--no-axes"])
    for suffix, view in spec.get("views", []):   # extra renders (assemblies)
        sc.run_cli(["snapshot", "--in", design, "--out", os.path.join(CAD, "png", f"{name}{suffix}.png"), "--width", "1100",
                    "--height", "1100", "--view", view, "--no-grid", "--no-axes"])
    r = sc.run_cli(["eval", "--in", design])
    m = json.loads(r.stdout)
    return m


def main(argv):
    T = targets()
    if "--list" in argv:
        for n, s in T.items():
            print(f"{n:24s} {s.get('desc', '')}")
        return 0
    P = sc.load_params()
    v = sc.evaluate(P)
    if "--script" in argv:
        name = argv[argv.index("--script") + 1]
        print(write_script(name, part_script(P, v, name, T[name])))
        return 0
    only = [a for a in argv if not a.startswith("-")]
    fail = 0
    if "--checks" not in argv:
        for name, spec in T.items():
            if only and not any(o in name for o in only):
                continue
            if spec.get("skip") and spec["skip"](v):
                print(f"-- {name}: not needed with these parameters ({spec.get('skip_why', '')})")
                stale = [(d, f"{name}.{ext}") for ext, d in (("sc", "designs"), ("step", "step"), ("stl", "stl"), ("png", "png"))]
                for d, fn in stale + spec.get("stale", []):
                    f = os.path.join(CAD, d, fn)
                    if os.path.exists(f):
                        os.remove(f)
                continue
            path = write_script(name, part_script(P, v, name, spec))
            m = build_part(P, v, name, path, spec)
            b = m["bodies"]
            vol = sum(x["volume_mm3"] for x in b)
            print(f"== {name:24s} {len(b):2d} bodies {vol:11.1f} mm3" if b else f"== {name}: NO BODY")
            if not b:
                fail = 1
    if only and "--checks" not in argv:
        return fail
    import checks
    rows = checks.run(v)
    bad = [r for r in rows if r[2] == "FAIL"]
    for s, text, verdict in rows:
        if verdict:
            print(f"   {verdict}  {text}")
    print(f"-- fit checks: {sum(1 for r in rows if r[2] == 'PASS')} PASS, {len(bad)} FAIL -> cad/fit_checks.md")
    if bad:
        fail = 1
    if "--checks" not in argv:
        sys.path.insert(0, os.path.join(CAD, "viewer"))
        import build_viewer
        build_viewer.main([], v)
    return fail


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

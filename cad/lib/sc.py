"""sc.py -- helpers for building the SolidCraft part designs from cad/params.json.

A part module (cad/parts/*.py) defines NAME and build(v) -> list of SolidCraft commands (as `batch` / `solidcraft-cli run`
take them). Expressions in those commands name the shared parameters; `script()` prepends `parameters.add` for every
parameter the commands use (and everything those parameters use in turn), so each design carries the live expressions it needs.
`v` holds the evaluated parameter values (mm / deg / unitless), for the few choices the expressions cannot make (no comparisons).
"""
import json
import os
import re
import subprocess
import sys

CAD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLI = os.environ.get("SOLIDCRAFT_CLI", "/Applications/SolidCraft.app/Contents/MacOS/solidcraft-cli")
BUILD = os.path.join(CAD, "build")
IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def load_params():
    """[(name, expression, unit, comment)] in file order."""
    with open(os.path.join(CAD, "params.json")) as f:
        data = json.load(f)
    out = []
    for g in data["groups"]:
        for name, expr, unit, comment in g["params"]:
            out.append((name, expr, unit, comment))
    names = [p[0] for p in out]
    dup = {n for n in names if names.count(n) > 1}
    if dup:
        sys.exit(f"params.json: duplicate names {sorted(dup)}")
    return out


def param_cmd(p):
    name, expr, unit, comment = p
    params = {"name": name, "expression": expr, "unit": unit}
    if comment:
        params["comment"] = comment
    return {"command": "parameters.add", "params": params}


def run_cli(args, check=True):
    r = subprocess.run([CLI] + args, capture_output=True, text=True)
    if check and r.returncode != 0:
        sys.exit(f"solidcraft-cli {' '.join(args)} failed:\n{r.stdout[-3000:]}\n{r.stderr[-3000:]}")
    return r


def evaluate(params):
    """Evaluate every parameter in SolidCraft itself: {name: value}."""
    os.makedirs(BUILD, exist_ok=True)
    path = os.path.join(BUILD, "_params.json")
    with open(path, "w") as f:
        json.dump({"commands": [param_cmd(p) for p in params]}, f)
    out = os.path.join(BUILD, "_params_results.json")
    run_cli(["run", path, "--results", "--quiet", "--json-out", out])
    with open(out) as f:
        res = json.load(f)
    vals = {}
    for r in res:
        if r.get("unit") == "text":
            vals[r["name"]] = r.get("text")
            continue
        if r.get("value") is None:
            sys.exit(f"parameter {r.get('name')} did not evaluate: {r}")
        vals[r["name"]] = r["value"]
    return vals


def used_names(obj, known):
    """Parameter names that appear in any string inside obj."""
    found = set()
    if isinstance(obj, str):
        found.update(t for t in IDENT.findall(obj) if t in known)
    elif isinstance(obj, dict):
        for x in obj.values():
            found |= used_names(x, known)
    elif isinstance(obj, list):
        for x in obj:
            found |= used_names(x, known)
    return found


def script(params, commands, extra=()):
    """parameters.add for the closure of the parameters the commands use (in params.json order), then the commands."""
    by_name = {p[0]: p for p in params}
    need = used_names(commands, by_name) | set(extra)
    todo = list(need)
    while todo:
        n = todo.pop()
        for d in used_names(by_name[n][1], by_name):
            if d not in need:
                need.add(d)
                todo.append(d)
    return [param_cmd(p) for p in params if p[0] in need] + commands


# ---- small command builders ----------------------------------------------------------------------------------------------
def C(command, **params):
    return {"command": command, "params": params}


def E(x):
    """Number or expression -> what SolidCraft takes (expressions stay strings)."""
    return x if isinstance(x, str) else float(x)


# ---- convex hull of circles as a fully constrained sketch --------------------------------------------------------------
import math


def _hull_order(circles):
    """CCW order of the circles (indices) that are on the convex hull. circles: [(x, y, r)] numbers."""
    pts = []
    for i, (x, y, r) in enumerate(circles):
        if r <= 0:
            pts.append((x, y, i))
        else:
            for k in range(1440):
                a = 2 * math.pi * k / 1440
                pts.append((x + r * math.cos(a), y + r * math.sin(a), i))
    pts = sorted(set(pts))

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 1e-12:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 1e-12:
            upper.pop()
        upper.append(p)
    hull = lower[:-1] + upper[:-1]
    seq = []
    for p in hull:
        if not seq or seq[-1] != p[2]:
            seq.append(p[2])
    while len(seq) > 1 and seq[0] == seq[-1]:
        seq.pop()
    return seq                                       # a circle may be visited twice (an arc on each side)


def _tangent(ci, cj):
    """Outer tangent from circle i to circle j for a CCW hull: (point on i, point on j)."""
    (xi, yi, ri), (xj, yj, rj) = ci, cj
    dx, dy = xj - xi, yj - yi
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    vx, vy = uy, -ux                      # right of the direction = outside of a CCW hull
    a = (ri - rj) / L
    b = math.sqrt(max(0.0, 1 - a * a))
    nx, ny = a * ux + b * vx, a * uy + b * vy
    return (xi + ri * nx, yi + ri * ny), (xj + rj * nx, yj + rj * ny)


def hull_sketch(circles, v, a0=0, l0=0):
    """Sketch commands (for the sketch being edited) drawing the convex hull of circles, fully constrained.

    circles: [(x_expr, y_expr, r_expr)]; r_expr 0 / "0" = a sharp corner point. Centres and corners are fixed by their
    expressions (they follow the parameters), each arc's radius is a dimension with its expression, and every line is
    tangent to the arcs it meets. Which circles lie on the hull is decided here from the current values `v`
    (the build reruns this when parameters change). Returns (commands, info).
    """
    def val(e):
        if isinstance(e, (int, float)):
            return float(e)
        return eval_expr(e, v)
    num = [(val(x), val(y), val(r)) for x, y, r in circles]
    order = _hull_order(num)
    n = len(order)
    tang = []                                         # tangent line k: from order[k] to order[k+1]
    for k in range(n):
        tang.append(_tangent(num[order[k]], num[order[(k + 1) % n]]))
    cmds, arc_id = [], {}
    a = a0
    for k, i in enumerate(order):
        if num[i][2] > 0:
            a += 1
            arc_id[k] = f"a{a}"
            start = tang[k - 1][1]                   # where the incoming line ends
            end = tang[k][0]                          # where the outgoing line starts
            x, y, r = circles[i]
            cmds.append(C("sketch.arc.center_point", center=[E(x), E(y)], start=list(start), end=list(end)))
            cmds.append(C("sketch.dimension", entities=[f"a{a}"], type="radius", value=E(r)))
    corner_id = {}
    for k in range(n):
        l = f"l{k + 1 + l0}"
        pts = []
        for end, kk in ((0, k), (1, (k + 1) % n)):
            if kk in arc_id:
                pts.append(f"{arc_id[kk]}.{'end' if end == 0 else 'start'}")
            elif kk in corner_id:
                pts.append(corner_id[kk])
            else:
                x, y, _ = circles[order[kk]]
                pts.append([E(x), E(y)])
                corner_id[kk] = f"{l}.{'start' if end == 0 else 'end'}"
        cmds.append(C("sketch.line", points=pts, infer=False))
        for kk in (k, (k + 1) % n):
            if kk in arc_id:
                cmds.append(C("sketch.constraint.tangent", a=l, b=arc_id[kk]))
    return cmds, {"order": order, "tangents": tang, "arcs": a - a0, "lines": n}


_FUN = {"sqrt": math.sqrt, "asin": lambda x: math.degrees(math.asin(x)), "acos": lambda x: math.degrees(math.acos(x)),
        "sin": lambda d: math.sin(math.radians(d)), "cos": lambda d: math.cos(math.radians(d)),
        "atan2": lambda y, x: math.degrees(math.atan2(y, x)), "min": min, "max": max, "ceil": math.ceil,
        "floor": math.floor, "abs": abs, "PI": math.pi, "pi": math.pi}


def eval_expr(e, v):
    """Evaluate a feature expression with the parameter values (units dropped: mm and deg as numbers)."""
    s = re.sub(r"(\d)\s*(mm|deg)\b", r"\1", e).replace("^", "**")
    return float(eval(s, {"__builtins__": {}}, {**_FUN, **v}))


def circle_cmds(x, y, d, v, c_id):
    """A circle with its centre fixed at (x, y) expressions and a diameter dimension (c_id: its id, e.g. "c1")."""
    return [C("sketch.circle.center", center=[E(x), E(y)], radius=eval_expr(d, v) / 2 if isinstance(d, str) else d / 2),
            C("sketch.dimension", entities=[c_id], type="diameter", value=E(d))]


def hulls_sketch(name, z, shapes, v, plane="XY"):
    """One sketch holding several hulls of circles (each a list of (x, y, r)) and single circles ("circle", x, y, d)."""
    cmds = [C("sketch.create", plane=plane, offset=z, name=name)] if z is not None else [C("sketch.create", plane=plane, name=name)]
    a = l = c = 0
    for s in shapes:
        if s and s[0] == "circle":
            c += 1
            cmds += circle_cmds(s[1], s[2], s[3], v, f"c{c}")
        else:
            h, info = hull_sketch(s, v, a0=a, l0=l)
            cmds += h
            a += info["arcs"]
            l += info["lines"]
    return cmds + [C("sketch.finish")]


def stadium(x, y0, y1, r, along="y"):
    """Two circles of radius r (a slot): along y from y0 to y1 at x, or along x from y0 to y1 at y=x when along='x'."""
    if along == "y":
        return [(x, y0, r), (x, y1, r)]
    return [(y0, x, r), (y1, x, r)]


def freeze(obj, params, v):
    """Every string that names a parameter, evaluated to its number now (for the assemblies: they carry no parameter table,
    because their linked parts cannot follow a parameter edited there; change params.json and rebuild instead)."""
    known = {p[0] for p in params}
    if isinstance(obj, dict):
        return {k: freeze(x, params, v) for k, x in obj.items()}
    if isinstance(obj, list):
        return [freeze(x, params, v) for x in obj]
    if isinstance(obj, str) and used_names(obj, known):
        try:
            return eval_expr(obj, v)
        except Exception:
            return obj
    return obj

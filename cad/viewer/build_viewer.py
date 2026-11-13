#!/usr/bin/env python3
"""Builds self-contained interactive 3D viewers (HTML + three.js) of the SolidCraft assemblies.

Every piece (a group of bodies of cad/designs/lathe_assembly.sc and control_box_assembly.sc) is exported as an STL by
SolidCraft, quantised to a 0.05 mm grid with shared vertices, and embedded as base64 in the page. The layout numbers come
from cad/params.json (evaluated by SolidCraft). Run by cad/build.py after the assemblies; or on its own:

    python3 cad/viewer/build_viewer.py            # writes cad/viewer/assembly_3d.html (gear end only)
                                                  #    and cad/viewer/machine_3d.html (whole lathe, control box, electrical box,
                                                  #    cables; the control box runs the firmware core from sim/web/els.wasm)
    python3 cad/viewer/build_viewer.py --png DIR  # also writes DIR/{assembly,machine}_preview.html + _mesh.png: variants that read the
        # bytes from a PNG (in the RGB pixels), for HTML previewers that inline local images but limit the page size

Needs SolidCraft (solidcraft-cli) and Python 3, no other packages.
"""
import base64
import gzip
import json
import os
import struct
import sys
import tempfile
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
CAD = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(CAD, "lib"))
import sc  # noqa: E402

OUT = os.path.join(HERE, "assembly_3d.html")
OUT_FULL = os.path.join(HERE, "machine_3d.html")
WASM = os.path.join(os.path.dirname(CAD), "sim", "web", "els.wasm")   # built by sim/build.sh
GRID = 0.05  # mm per quantisation step (int16 range = +-1638 mm)
# Display-only simplification: vertices closer than this (mm) are merged (vertex clustering).
CLUSTER = {"default": 0.5, "pulley40": 0.4, "pulley60": 0.4, "pulley20gt2": 0.35, "pulley20htd": 0.35}

# Pieces of the lathe assembly (bodies of cad/designs/lathe_assembly.sc); the viewer colours them by name.
_SO = ["M5 hex standoffs"] + [f"M5 hex standoffs ({i})" for i in (2, 3, 4)]
PIECES = {
    "plate": ["Base plate"], "bracket": ["Encoder bracket"], "pulley40": ["Pulley HTD-3M 40T"],
    "pulley20htd": ["Motor pulley 20T (bought)"], "pulley60": ["Pulley GT2 60T"], "pulley20gt2": ["Pulley GT2 20T"],
    "belts": ["HTD-3M belt 3M-207", "GT2 belt 200"], "motor": ["Motor body", "Motor pilot"], "encoder": ["Encoder body", "Encoder pilot"],
    "standoffs": _SO + [f"Washer shim {i}" for i in (1, 2, 3, 4)], "stud_ring": ["Stud shoulder"],
    "shafts": ["Leadscrew shaft", "Leadscrew shoulder", "Stud shaft", "Motor shaft", "Encoder shaft"],
    "hardware": ["Leadscrew end washer", "Leadscrew end screw head", "Stud end washer", "Stud end screw head", "B1 screw", "B2 screw"]
                + [f"M5 standoff fastener {i}" for i in (1, 2, 3, 4)] + ["M4 bracket screw 1", "M4 bracket screw 2"],
    "cap": ["Spindle bearing cap"], "spindle": ["Spindle"], "switch": ["Door switch box"], "plunger": ["Door switch plunger"],
}
# The machine view also shows the printed control box, in its own frame (assembled, viewer at -Z).
CB_PIECES = {"cb_panel": ["Control panel"], "cb_frame": ["Control frame"], "cb_lid": ["Control lid"]}
# Standalone pages get their own dark page colours; the preview variants inherit the host's theme instead.
STANDALONE_CSS = "  html { background: #14161b; } body { margin: 0; padding: 16px; color: #e6e6e6; }\n"


def export_all(design, pieces, tmp):
    """One SolidCraft run on the saved assembly: an STL per piece. Returns [(name, path)]."""
    names = {b for bodies in pieces.values() for b in bodies}
    steps, out = [], []
    for name, bodies in pieces.items():
        path = os.path.join(tmp, name + ".stl")
        steps.append({"command": "file.export", "params": {"bodies": bodies, "path": path}})
        out.append((name, path))
    script = os.path.join(tmp, os.path.basename(design) + ".export.json")
    with open(script, "w") as f:
        json.dump({"commands": steps}, f)
    sc.run_cli(["run", script, "--in", design, "--quiet"])
    missing = [p for _, p in out if not os.path.exists(p)]
    if missing:
        sys.exit(f"export missing {missing} ({sorted(names)})")
    return out


def read_numbers(v=None):
    if v is None:
        v = sc.evaluate(sc.load_params())
    r = lambda x: round(x, 4)
    return {"motor_face_z": r(v["motor_face_z"]), "motor_len": v["motor_len"], "enc_front_z": r(v["enc_front_z"]),
            "door_depth": v["door_depth"], "plunger": [v["plunger_x"], v["plunger_y"]],
            "motor_box": [r(v["mbox_x0"]), r(v["mbox_x1"]), r(v["mbox_y0"]), r(v["mbox_y1"])],
            "enc_box": [r(v["ebox_x0"]), r(v["ebox_x1"]), r(v["ebox_y0"]), r(v["ebox_y1"])],
            "hinge": [v["door_hinge_x"], v["door_hinge_z"]], "door_t": v["door_t"], "cut_clear": v["door_cut_clear"],
            "cable_gap": v["door_cable_gap"], "cut_clear_y": v["door_cut_clear_y"], "swing_margin": v["door_swing_margin"],
            "door_clear": v["door_clear"], "bezel": [v["bezel_w"], v["bezel_t"], v["bezel_r"]],
            "stud": [v["stud_x"], v["stud_y"]], "enc": [r(v["enc_x"]), r(v["enc_y"])], "motor_xy": [r(v["motor_x"]), r(v["motor_y"])],
            "spindle": [v["spindle_x"], v["spindle_y"]], "cb": [v["cb_w"], v["cb_h"], v["cb_depth"]],
            "tft_pos": [v["tft_x"], v["tft_y"]], "tft_win": [v["tft_win_w"], v["tft_win_h"]],
            "btn_grid": [v["btn_grid_x"], v["btn_grid_y"]], "btn_pitch": [v["btn_pitch_x"], v["btn_pitch_y"]], "btn_d": v["btn_hole"],
            "nut": [v["nutbtn_x"], v["nutbtn_y"]], "estop": [v["estop_x"], v["estop_y"]], "estop_d": v["estop_head_d"],
            "knob": [v["knob_x"], v["knob_y"]], "led": [v["led_x"], v["led_y"]],
            "gland_x": [-v["gland_pitch"], 0, v["gland_pitch"]], "cb_wall": v["cb_wall"], "cb_post": v["cb_post"],
            "ear": [v["ear_len"], v["ear_w"]],
            # the drive, for the labels and the animation
            "ls_teeth": [round(v["ls_teeth_motor"]), round(v["ls_teeth_screw"])],
            "enc_teeth": [round(v["enc_teeth_stud"]), round(v["enc_teeth_encoder"])],
            "stud_ratio": v["stud_ratio"], "enc_per_spindle": v["enc_per_spindle"],
            "gland_z": v["gland_z"], "pitch": _firmware_pitch(),
            "panel_bottom_y": v["panel_bottom_y"], "panel_right_x": v["panel_right_x"], "cb_panel_t": v["cb_panel_t"],
            "label_size": v["label_size"], "led_hole": v["led_hole"],
            "tft_pcb": [v["tft_pcb_w"], v["tft_pcb_h"]], "tft_win_off": [v["tft_win_off_x"], v["tft_win_off_y"]]}


def _firmware_pitch():
    """Leadscrew pitch (mm) the firmware drives the carriage with: firmware/include/lathe_config.h (TPI or PITCH_UM)."""
    import re
    path = os.path.join(os.path.dirname(CAD), "firmware", "include", "lathe_config.h")
    d = {m.group(1): int(m.group(2)) for m in re.finditer(r"^\s*#define\s+(\w+)\s+(\d+)\s*$", open(path).read(), re.M)}
    return 25.4 / d["LEADSCREW_TPI"] if d.get("LEADSCREW_TPI") else d["LEADSCREW_PITCH_UM"] / 1000


def load_stl(path, cell):
    with open(path, "rb") as f:
        data = f.read()
    n = struct.unpack_from("<I", data, 80)[0]
    verts, index, seen = {}, [], set()
    snap = max(1, round(cell / GRID))
    for i in range(n):
        off = 84 + i * 50 + 12
        tri = []
        for k in range(3):
            x, y, z = struct.unpack_from("<fff", data, off + 12 * k)
            key = (round(x / GRID / snap) * snap, round(y / GRID / snap) * snap, round(z / GRID / snap) * snap)
            if key not in verts:
                verts[key] = len(verts)
            tri.append(verts[key])
        if tri[0] != tri[1] and tri[1] != tri[2] and tri[0] != tri[2]:
            canon = tuple(sorted(tri))
            if canon not in seen:
                seen.add(canon)
                index.extend(tri)
    # renumber: clustering leaves unused vertices behind
    used = sorted(set(index))
    remap = {old: new for new, old in enumerate(used)}
    keys = list(verts)
    index = [remap[i] for i in index]
    pos = [c for old in used for c in keys[old]]
    return pos, index, len(used)


def deltas(values):
    """Differences from the previous value: small numbers, which gzip packs far better."""
    out, prev = [], 0
    for v in values:
        out.append(v - prev)
        prev = v
    return out


def pack(pos, index, nverts, blob):
    """Appends one mesh to `blob` (a single gzip stream for all meshes) and returns its offsets.

    Positions are stored as three planes (all x, then all y, then all z) and indices as
    differences from the previous index, both int16 (every mesh here is far below 32k vertices).
    """
    if nverts > 32767:
        sys.exit("mesh too large for int16 index deltas")
    planar = [pos[i] for axis in range(3) for i in range(axis, len(pos), 3)]
    entry = {"pos": [len(blob), len(pos)], "idx": [0, len(index)]}
    blob += struct.pack(f"<{len(planar)}h", *deltas(planar))
    entry["idx"][0] = len(blob)
    blob += struct.pack(f"<{len(index)}h", *deltas(index))
    return entry


def write_png(path, data):
    """Stores `data` losslessly in the RGB pixels of a PNG; the first 4 bytes hold the length."""
    raw = struct.pack("<I", len(data)) + bytes(data)
    width = 1024
    height = -(-len(raw) // (width * 3))
    raw += bytes(width * height * 3 - len(raw))
    rows = b"".join(b"\x00" + raw[y * width * 3:(y + 1) * width * 3] for y in range(height))

    def chunk(tag, body):
        return struct.pack(">I", len(body)) + tag + body + struct.pack(">I", zlib.crc32(tag + body) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(rows, 9)) + chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


def write_pages(template_name, out, blob, nums, meshes, extra, png_dir, stem):
    with open(os.path.join(HERE, template_name)) as f:
        template = f.read()
    packed = base64.b64encode(gzip.compress(bytes(blob), 9)).decode()
    payload = json.dumps({"grid": GRID, "nums": nums, "meshes": meshes, **extra, "blob": packed}, separators=(",", ":"))
    html = template.replace("/*__DATA__*/null", payload).replace("</style>", STANDALONE_CSS + "</style>", 1)
    with open(out, "w") as f:
        f.write(html)
    print(f"wrote {out}: {len(html) / 1024:.0f} kB")
    if png_dir:
        png_path, html_path = os.path.join(png_dir, stem + "_mesh.png"), os.path.join(png_dir, stem + "_preview.html")
        write_png(png_path, blob)
        payload = json.dumps({"grid": GRID, "nums": nums, "meshes": meshes, **extra, "png": "meshdata"}, separators=(",", ":"))
        variant = template.replace("/*__DATA__*/null", payload).replace(
            "<body>", f'<body>\n<img id="meshdata" alt="" style="display:none" src="{png_path}">', 1)
        with open(html_path, "w") as f:
            f.write(variant)
        print(f"wrote {html_path} ({len(variant) / 1024:.0f} kB) + {png_path} ({os.path.getsize(png_path) / 1024:.0f} kB)")


def main(argv=None, v=None):
    argv = sys.argv[1:] if argv is None else argv
    png_dir = None
    if len(argv) == 2 and argv[0] == "--png":
        png_dir = os.path.abspath(argv[1])
        os.makedirs(png_dir, exist_ok=True)
    if v is None:
        v = sc.evaluate(sc.load_params())
    nums = read_numbers(v)
    pieces = dict(PIECES)
    if v["stud_spacer"] > 0:                       # the optional ring sits on the stud shoulder: show it with it
        pieces["stud_ring"] = PIECES["stud_ring"] + ["Stud spacer"]
    if v["base_m5"] == "insert":                   # heat-set inserts in the plate (option base_m5)
        pieces["hardware"] = PIECES["hardware"] + [f"M5 insert {i}" for i in (1, 2, 3, 4)]
    designs = os.path.join(CAD, "designs")
    with tempfile.TemporaryDirectory() as tmp:
        files = export_all(os.path.join(designs, "lathe_assembly.sc"), pieces, tmp)
        meshes, blob = {}, bytearray()
        tri_total = 0
        for name, path in files:
            pos, index, nv = load_stl(path, CLUSTER.get(name, CLUSTER["default"]))
            tri_total += len(index) // 3
            meshes[name] = pack(pos, index, nv, blob)
            print(f"  {name:12s} {len(index) // 3:6d} tris {nv:6d} verts")
        cb_files = export_all(os.path.join(designs, "control_box_assembly.sc"), CB_PIECES, tmp)
        cb_meshes, cb_blob = {}, bytearray(blob)
        for name, path in cb_files:
            pos, index, nv = load_stl(path, 0.25)
            cb_meshes[name] = pack(pos, index, nv, cb_blob)
            print(f"  {name:12s} {len(index) // 3:6d} tris {nv:6d} verts")
    print(f"{tri_total} triangles")
    write_pages("template.html", OUT, blob, nums, meshes, {}, png_dir, "assembly")
    # The machine view also carries the firmware core (WebAssembly) behind the control box screen and buttons.
    if not os.path.exists(WASM):
        print(f"no {WASM} (run sim/build.sh): machine_3d.html not written")
        return
    with open(WASM, "rb") as f:
        wasm = f.read()
    full = cb_blob
    wasm_at = [len(full), len(wasm)]
    full += wasm
    write_pages("template_machine.html", OUT_FULL, full, nums, {**meshes, **cb_meshes}, {"wasm": wasm_at}, png_dir, "machine")


if __name__ == "__main__":
    main()

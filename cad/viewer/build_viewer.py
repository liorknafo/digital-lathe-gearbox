#!/usr/bin/env python3
"""Builds self-contained interactive 3D viewers (HTML + three.js) of cad/assembly.scad.

Every named piece of the assembly (see `piece()` in assembly.scad) is exported as an STL,
quantised to a 0.05 mm grid with shared vertices, and embedded as base64 in the page.

    python3 cad/viewer/build_viewer.py            # writes cad/viewer/assembly_3d.html (gear end only)
                                                  #    and cad/viewer/machine_3d.html (whole lathe, control box, electrical box,
                                                  #    cables; the control box runs the firmware core from sim/web/els.wasm)
    python3 cad/viewer/build_viewer.py --png DIR  # also writes DIR/{assembly,machine}_preview.html + _mesh.png: variants that read the
        # bytes from a PNG (in the RGB pixels), for HTML previewers that inline local images but limit the page size

Needs OpenSCAD on PATH (`openscad`), Python 3, no other packages.
"""
import base64
import gzip
import json
import os
import re
import struct
import subprocess
import sys
import tempfile
import zlib
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
CAD = os.path.dirname(HERE)
OUT = os.path.join(HERE, "assembly_3d.html")
OUT_FULL = os.path.join(HERE, "machine_3d.html")
WASM = os.path.join(os.path.dirname(CAD), "sim", "web", "els.wasm")   # built by sim/build.sh
GRID = 0.05  # mm per quantisation step (int16 range = +-1638 mm)
# Coarser curves than the print exports: this is only for looking at (explicit $fn in the parts still wins).
FACETS = ["-D", "$fa=12", "-D", "$fs=1.2", "-D", "$coarse=true"]
# Display-only simplification: vertices closer than this (mm) are merged (vertex clustering).
CLUSTER = {"default": 0.5, "pulley40": 0.4, "pulley60": 0.4, "pulley20gt2": 0.35, "pulley20htd": 0.35}

# Pieces exported from assembly.scad; the viewer colours them by name.
PIECES = ["plate", "bracket", "pulley40", "pulley20htd", "pulley60", "pulley20gt2", "belts", "motor",
          "encoder", "standoffs", "stud_ring", "shafts", "hardware", "cap", "spindle", "switch", "plunger"]


# The machine view also shows the printed control box, in its own frame (cad/control_box.scad: assembled, viewer at -Z).
CB_PIECES = {"cb_panel": "panel_asm", "cb_frame": "frame_asm", "cb_lid": "lid_asm"}
# Standalone pages get their own dark page colours; the preview variants inherit the host's theme instead.
STANDALONE_CSS = "  html { background: #14161b; } body { margin: 0; padding: 16px; color: #e6e6e6; }\n"


def export(name, tmp, scad="assembly.scad", part=None):
    path = os.path.join(tmp, name + ".stl")
    subprocess.run(["openscad", "--backend=manifold", "--export-format", "binstl", "-D", f'part="{part or name}"', *FACETS,
                    "-o", path, os.path.join(CAD, scad)],
                   check=True, capture_output=True, text=True)
    return name, path


def read_numbers():
    res = subprocess.run(["openscad", "-D", 'part="none"', "--export-format", "echo", "-o", "-",
                          os.path.join(CAD, "assembly.scad")], capture_output=True, text=True, check=True)
    m = re.search(r'VIEWER (\{.*\})"', res.stdout + res.stderr)
    if not m:
        sys.exit("assembly.scad did not echo the VIEWER line")
    return json.loads(m.group(1).replace('\\"', '"'))


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


def main():
    png_dir = None
    if len(sys.argv) == 3 and sys.argv[1] == "--png":
        png_dir = os.path.abspath(sys.argv[2])
        os.makedirs(png_dir, exist_ok=True)
    nums = read_numbers()
    with tempfile.TemporaryDirectory() as tmp, ThreadPoolExecutor(8) as pool:
        files = list(pool.map(lambda p: export(p, tmp), PIECES))
        meshes, blob = {}, bytearray()
        tri_total = 0
        for name, path in files:
            pos, index, nv = load_stl(path, CLUSTER.get(name, CLUSTER["default"]))
            tri_total += len(index) // 3
            meshes[name] = pack(pos, index, nv, blob)
            print(f"  {name:12s} {len(index) // 3:6d} tris {nv:6d} verts")
        cb_files = list(pool.map(lambda kv: export(kv[0], tmp, "control_box.scad", kv[1]), CB_PIECES.items()))
        cb_meshes, cb_blob = {}, bytearray(blob)
        for name, path in cb_files:
            pos, index, nv = load_stl(path, 0.25)
            cb_meshes[name] = pack(pos, index, nv, cb_blob)
            print(f"  {name:12s} {len(index) // 3:6d} tris {nv:6d} verts")
    print(f"{tri_total} triangles, numbers {nums}")
    write_pages("template.html", OUT, blob, nums, meshes, {}, png_dir, "assembly")
    # The machine view also carries the firmware core (WebAssembly) behind the control box screen and buttons.
    with open(WASM, "rb") as f:
        wasm = f.read()
    full = cb_blob
    wasm_at = [len(full), len(wasm)]
    full += wasm
    write_pages("template_machine.html", OUT_FULL, full, nums, {**meshes, **cb_meshes}, {"wasm": wasm_at}, png_dir, "machine")


if __name__ == "__main__":
    main()

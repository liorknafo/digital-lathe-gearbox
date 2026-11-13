#!/usr/bin/env bash
# build.sh -- render every part to stl/*.stl and a PNG preview to png/*.png, the base-plate outline to dxf/base_plate.dxf,
# and the assembly previews (iso + front view along -Z + side) with the fit-check report in logs/assembly.echo.
# Usage: ./build.sh            (everything)       ./build.sh plate   (only outputs whose name contains "plate")
set +u
cd "$(dirname "$0")"
OPENSCAD="${OPENSCAD:-$(command -v openscad || echo /opt/homebrew/bin/openscad)}"
BACKEND="--backend=manifold"
# patterns that count as a problem: WARNING/ERROR lines, any manifold status other than NoError, CGAL errors
BAD='^(WARNING|ERROR)|Status: +[^N ]|Status: +N[^o]|CGAL.*(error|warning|fail)|non-manifold|not manifold|empty'
mkdir -p stl png dxf logs
ONLY="${1:-}"
fail=0

want() { [ -z "$ONLY" ] || [[ "$1" == *"$ONLY"* ]]; }
scan() { # LOGFILE
  if grep -qE "$BAD" "$1"; then echo "   ---- warnings/errors in $1:"; grep -E "$BAD" "$1" | sort -u | head -5; fail=1; fi
}
# render NAME FILE.scad "DEFINES"   -> stl/NAME.stl + png/NAME.png (default oblique camera)
render() {
  name="$1"; file="$2"; defs="$3"
  want "$name" || return
  args=(); [ -n "$defs" ] && args+=(-D "$defs")
  log="logs/$name.log"
  echo "== $name ($file $defs)"
  "$OPENSCAD" $BACKEND ${args[@]+"${args[@]}"} -o "stl/$name.stl" "$file" >"$log" 2>&1 || { echo "   STL FAILED"; fail=1; }
  "$OPENSCAD" $BACKEND ${args[@]+"${args[@]}"} -o "png/$name.png" --imgsize=1200,900 --autocenter --viewall \
      --colorscheme=Tomorrow --render 1 "$file" >>"$log" 2>&1 || { echo "   PNG FAILED"; fail=1; }
  scan "$log"
}
# shot NAME FILE.scad "DEFINES" CAMERA [IMGSIZE]  -> png/NAME.png only (CAMERA = cx,cy,cz,rx,ry,rz,dist; orthographic)
shot() {
  name="$1"; file="$2"; defs="$3"; cam="$4"; size="${5:-1200,900}"
  want "$name" || return
  args=(); [ -n "$defs" ] && args+=(-D "$defs")
  log="logs/$name.log"
  echo "== $name (preview)"
  "$OPENSCAD" $BACKEND ${args[@]+"${args[@]}"} -o "png/$name.png" --imgsize="$size" --autocenter --viewall --projection=ortho \
      --colorscheme=Tomorrow --render 1 --camera="$cam" "$file" >"$log" 2>&1 || { echo "   PNG FAILED"; fail=1; }
  scan "$log"
}

# shotfix NAME FILE.scad "DEFINES" CAMERA   -> like shot but with the exact camera (no autocenter / viewall): zoomed views
shotfix() {
  name="$1"; file="$2"; defs="$3"; cam="$4"
  want "$name" || return
  args=(); [ -n "$defs" ] && args+=(-D "$defs")
  log="logs/$name.log"
  echo "== $name (zoomed preview)"
  "$OPENSCAD" $BACKEND ${args[@]+"${args[@]}"} -o "png/$name.png" --imgsize=1600,900 --projection=ortho \
      --colorscheme=Tomorrow --render 1 --camera="$cam" "$file" >"$log" 2>&1 || { echo "   PNG FAILED"; fail=1; }
  scan "$log"
}

# --- parts (STL + PNG) ---
render base_plate             base_plate.scad          'mode="print"'
render encoder_bracket        encoder_bracket.scad     'mode="print"'
render door_bezel             door_bezel.scad          'mode="print"'
grep -qE '^stud_spacer *= *0;' params.scad || \
  render spacer_stud_collar   spacer.scad              'part="stud_collar"'   # only when params.scad asks for the ring
render pulley_htd3m_40T       pulley_htd3m.scad        'part="40T"'
render pulley_htd3m_20T       pulley_htd3m.scad        'part="20T"'
render pulley_gt2_60T         pulley_gt2.scad          'part="60T"'
render pulley_gt2_20T         pulley_gt2.scad          'part="20T"'
render control_panel          control_box.scad         'part="panel"'
render control_frame          control_box.scad         'part="frame"'
render control_lid            control_box.scad         'part="lid"'

# --- extra previews ---
shot control_panel_front      control_box.scad 'part="panel_view"'  '0,0,0,0,0,0,500'
shot control_all              control_box.scad 'part="all"'         '0,0,0,70,0,320,800'
shot base_plate_front         base_plate.scad  'mode="print"'       '0,0,0,0,0,0,300' 700,1300
shot encoder_bracket_lathe    encoder_bracket.scad 'mode="lathe"'   '0,0,0,-65,0,330,200'

# --- 1:1 template for the door window (cut + drill), DXF ---
if want "door_bezel" || want "dxf"; then
  echo "== door_window_template.dxf"
  "$OPENSCAD" $BACKEND -D 'mode="template"' -o dxf/door_window_template.dxf door_bezel.scad >logs/door_window_template.log 2>&1 || { echo "   DXF FAILED"; fail=1; }
  scan logs/door_window_template.log
fi

# --- DXF for the 6-8 mm aluminium base plate ---
if want "base_plate" || want "dxf"; then
  echo "== base_plate.dxf"
  "$OPENSCAD" $BACKEND -D 'mode="dxf"' -o dxf/base_plate.dxf base_plate.scad >logs/base_plate_dxf.log 2>&1 || { echo "   DXF FAILED"; fail=1; }
  scan logs/base_plate_dxf.log
  "$OPENSCAD" $BACKEND -D 'mode="dxf"' -o png/base_plate_dxf_outline.png --imgsize=700,1300 --autocenter --viewall --projection=ortho \
      --colorscheme=Tomorrow --render 1 --camera=0,0,0,0,0,0,300 base_plate.scad >logs/base_plate_dxf_outline.log 2>&1 || { echo "   PNG FAILED"; fail=1; }
  scan logs/base_plate_dxf_outline.log
fi

# --- assembly previews + fit-check report ---
if want "assembly"; then
  shot assembly            assembly.scad 'view="iso"'   '0,0,0,60,0,330,900'  1400,1000
  shot assembly_front      assembly.scad 'view="front"' '0,0,0,0,0,0,900'     1000,1500   # camera looks along -Z (X right, Y up), compare docs/roher_layout.png
  shot assembly_side       assembly.scad 'view="side"'  '0,0,0,90,0,270,900'  1400,900
  # zoomed side views from +X (Y to the right, Z up): pulley-plane alignment of the HTD pair (motor row) and the GT2 pair (encoder row)
  shotfix assembly_side_motor assembly.scad 'view="side_motor"' '0,-35,45,90,0,90,230'
  shotfix assembly_side_enc   assembly.scad 'view="side_enc"'   '0,98.9,35,90,0,270,150'
  "$OPENSCAD" $BACKEND -o logs/assembly.echo assembly.scad >logs/assembly_checks.log 2>&1
  scan logs/assembly_checks.log
  echo "-- fit checks (logs/assembly.echo):"; grep -E 'CHECK' logs/assembly.echo | sed 's/^ECHO: //' | grep -E 'PASS|FAIL' | sed 's/^"CHECK //; s/"$//'
fi

[ "$fail" = 0 ] && echo "ALL OK (no warnings)" || echo "DONE WITH WARNINGS/ERRORS (see logs/)"
exit "$fail"

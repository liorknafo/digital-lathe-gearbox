"""Printed C-cup for the LPD3806-600BM encoder, bolted to the base plate with 2x M4 (heat-set inserts in the columns).

Modelled in the lathe frame (where it sits): it rises from the base plate front face (Z = base_t) round the encoder's
20T GT2 pulley; its TOP face (Z = enc_face_z) carries the encoder: 3x M3 on the 30 mm PCD, the 20 mm pilot recess and the
shaft slot, all slotted +-enc_travel/2 along X for GT2 belt tension. The cup is OPEN towards the stud (-X) so the belt runs
in and out; walls and the two M4 insert columns are on the +X end. enc_face_z is derived so the 20T teeth line up with the
stud's 60T teeth (params.json). Print: encoder face DOWN on the bed (the STL is turned that way), no supports.
"""
from sc import C, hulls_sketch, stadium


def outline(r, left_extra="0 mm"):
    return [("col_cx", "enc_y", r), (f"cup_left_x - {left_extra}", f"enc_y + {r}", 0), (f"cup_left_x - {left_extra}", f"enc_y - {r}", 0)]


def xslot(x, y, d):
    return stadium(y, f"{x} - enc_travel / 2", f"{x} + enc_travel / 2", f"({d}) / 2", along="x")


def build(v):
    cmds = []
    cmds += hulls_sketch("Cup outline sketch", "base_t", [outline("eb_out")], v)
    cmds.append(C("solid.extrude", distance="eb_h", operation="new", name="Cup block", body_name="Encoder bracket"))
    cmds += hulls_sketch("Cup inside sketch", "base_t", [outline("eb_in", "1 mm")], v)
    cmds.append(C("solid.extrude", distance="eb_under_z - base_t", operation="cut", name="Cup inside (open towards the stud)"))
    for s, sign in (("upper", "+"), ("lower", "-")):
        cmds.append(C("solid.cylinder", radius="eb_col_r", height="eb_under_z - base_t", base=["col_x", f"enc_y {sign} col_dy", "base_t"],
                      operation="join", name=f"M4 column {s}"))
    pts = [(f"enc_x + enc_hole_pcd / 2 * cos(enc_hole_angle + {120 * i} deg)",
            f"enc_y + enc_hole_pcd / 2 * sin(enc_hole_angle + {120 * i} deg)") for i in range(3)]
    cmds += hulls_sketch("Encoder slots sketch", "eb_under_z",
                         [xslot("enc_x", "enc_y", "enc_shaft_d + 1 mm")] + [xslot(x, y, "m3_clear") for x, y in pts], v)
    cmds.append(C("solid.extrude", distance="eb_top_t", operation="cut", name="Shaft + 3x M3 slots (+-4 mm)"))
    cmds += hulls_sketch("Pilot recess sketch", "enc_face_z - eb_recess", [xslot("enc_x", "enc_y", "enc_pilot_d + 0.6 mm")], v)
    cmds.append(C("solid.extrude", distance="eb_recess", operation="cut", name="Pilot recess (+-4 mm)"))
    cmds += hulls_sketch("M4 insert holes sketch", "base_t", [("circle", "col_x", "enc_y + col_dy", "eb_insert_d"),
                                                               ("circle", "col_x", "enc_y - col_dy", "eb_insert_d")], v)
    cmds.append(C("solid.extrude", distance="eb_insert_depth", operation="cut", name="M4 heat-set insert holes"))
    return cmds


# print: encoder face down -- turn about X (Y and Z flip), the slot centre E to X = 0 and Y = 0, face on Z = 0
PRINT = [C("solid.move", bodies=["Encoder bracket"], axis=[1, 0, 0], angle="180 deg"),
         C("solid.move", bodies=["Encoder bracket"], translate=["-enc_x", "enc_y", "enc_face_z"])]

PARTS = {"encoder_bracket": {"build": build, "print": PRINT,
                             "desc": "encoder C-cup on the base plate, open towards the stud, 2x M4 inserts, encoder slots +-4 mm"}}

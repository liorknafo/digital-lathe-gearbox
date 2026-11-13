"""Optional ring on the change-gear stud behind the 60T pulley (was spacer.scad).

Only needed if the spindle bearing cap stands out past the stud shoulder face (stud_seat_z): it lifts the 60T's back face by
stud_spacer. Measured: the cap is below the shoulder, so stud_spacer = 0 and the part is not built (build.py removes a stale one).
Ring ID stud_bore + 0.6, OD stud_spacer_od, axis Z, sitting on Z = 0 (the assembly places it on the stud shoulder face).
Washers (stud_bore, the same stack) or a steel spacer work as well.
"""
from sc import C, circle_cmds


def build(v):
    return [C("solid.cylinder", diameter="stud_spacer_od", height="stud_spacer", base=[0, 0, 0], operation="new", name="Ring",
              body_name="Stud spacer"),
            C("solid.cylinder", diameter="stud_bore + 0.6 mm", height="stud_spacer + 2 mm", base=[0, 0, "-1 mm"], operation="cut",
              targets=["Stud spacer"], name="Bore")]


PARTS = {"stud_spacer": {"build": build, "skip": lambda v: v["stud_spacer"] <= 0, "skip_why": "stud_spacer is 0",
                         "desc": "optional ring on the stud behind the 60T (only when stud_spacer > 0)"}}

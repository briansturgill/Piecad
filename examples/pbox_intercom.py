"""
Intercom ProjectBox Example
"""

from piecad import *
from piecad.projectbox import *

box_w = 120  # Inner box width (X)
box_d = box_w / 1.618  # Inner box depth (Y)
box_h = 65  # Inner box height (Z)

spk_hole_spacing = 41


def speaker():
    tp = pbc.tap_post(6, 3)
    return union(
        tp,
        tp.translate([spk_hole_spacing, 0, 0]),
        tp.translate([0, spk_hole_spacing, 0]),
        tp.translate([spk_hole_spacing, spk_hole_spacing, 0]),
    )


def speaker_holes():
    ctr = spk_hole_spacing / 2
    return pbc.circular_speaker_grid_holes(20, 3).translate([ctr, ctr, 0])


def bme280():
    return union(
        difference(
            cube([12 + 4, 16 + 4, 3], center=True),
            cube([12, 16, 3], center=True),
        ).translate([0, 0, 3 / 2]),
        difference(
            cube([16, 2, 5]).translate([-8, -8 - 2, 3]),
            cube([3, 3, 2]).translate([-3 / 2, -8 - 2, 4]),
        ),
        difference(
            cube([16, 2, 5]).translate([-8, 8, 3]),
            cube([3, 3, 2]).translate([-3 / 2, 8, 4]),
        ),
    )


def bme280_hole(wall=2):
    return pbc.hole(3 / 2, wall).translate([(11.5 / 2) - 3.5, 0, 0])


def max9814_mic(rot=0):
    return union(
        difference(
            cube([15.5 + 4, 26.5 + 4, 6]).translate([-7.5 - 2, -7.5 - 2, 0]),
            cube([15.5, 26.5, 6]).translate([-7.5, -7.5, 0]),
        ),
        cube([15.5 + 4, 26.5, 3]).translate([-7.5 - 2, -7.5 - 2, 0]),
        pbc.wire_tie_loop().translate([8, 5, 4]),
        pbc.wire_tie_loop().translate([-9.5, 5, 4]),
    ).rotate([0, 0, rot])


def max9814_mic_hole(wall=2):
    return pbc.hole(5, wall + 6).translate([0, 0, 6])


pb = ProjectBox([box_w, box_d, box_h])
pb.left(box_d / 2, 2 * (box_h / 3), bme280(), bme280_hole())
pb.right(
    box_d / 2, box_h - 15, None, pbc.horizontal_slot_hole(12, 7)
)  # Slot for micro-usb


spk_off = (box_d - spk_hole_spacing) / 2
pb.top(spk_off + 8, spk_off, speaker(), speaker_holes())
pb.top(box_w - 28, box_d / 3, max9814_mic(rot=90), max9814_mic_hole())
pb.top(box_w - 28, 2 * (box_d / 3), None, pbc.hole(6))  # 12mm d pushbutton

pb_walls = pb.finish()

if __name__ == "__main__":
    for w in pb_walls:
        view(w)
    left, right, front, back, top, bottom = pb_walls
    save("/tmp/box_l.obj", left)
    save("/tmp/box_r.obj", right)
    save("/tmp/box_f.obj", front)
    save("/tmp/box_k.obj", back)
    save("/tmp/box_t.obj", top)
    save("/tmp/box_m.obj", bottom)

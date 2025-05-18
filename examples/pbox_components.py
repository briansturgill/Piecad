"""
ProjectBox Example Components.
"""

from piecad import *
from piecad.projectbox import *


def doppler_motion_sensor():
    """
    ORIGIN: bottom left
    """
    tp = pbc.tap_post(6, 1.4)
    return union(
        tp.translate([0, 0, 0]),
        tp.translate([15, 0, 0]),
        tp.translate([0, 15, 0]),
        tp.translate([15, 15, 0]),
    )


def round_buzzer(buzzer_d, hole_d):
    """
    ORIGIN: centered
    """
    tiny = 0.01
    return difference(
        circle((buzzer_d + 2) / 2.0).extrude(2),
        circle(buzzer_d / 2.0).extrude(2 + 2 * tiny).translate([0, 0, -tiny]),
    )


def round_buzzer_hole(hole_d):
    """
    ORIGIN: centered
    """
    return pbc.hole(hole_d / 2.0)


# Works best if r is evenly divisible by hole_w
def circular_speaker_grid_holes(r, wall=2, hole_w=2):
    """
    ORIGIN: centered
    """
    tiny = 0.01
    l = []
    y = -(r - hole_w)
    while y <= r - hole_w:
        l.append(
            cube([r * 2, hole_w, wall + 2 * tiny], center=True).translate([0, y, 0])
        )
        y += 2 * hole_w
    return intersect(
        union(*l), cylinder(radius=r, height=wall + 2 * tiny, center=True)
    ).translate([0, 0, -(wall / 2) - tiny])


def max9814_mic(rot=0):
    """
    ORIGIN: centered
    """
    tiny = 0.01
    return union(
        difference(
            cube([15.5 + 4, 26.5 + 4, 6]).translate([-7.5 - 2, -7.5 - 2, 0]),
            cube([15.5, 26.5, 6 + 2 * tiny]).translate([-7.5, -7.5, -tiny]),
        ),
        cube([15.5 + 4, 26.5, 3]).translate([-7.5 - 2, -7.5 - 2, 0]),
        pbc.wire_tie_loop().translate([8, 5, 4]),
        pbc.wire_tie_loop().translate([-9.5, 5, 4]),
    ).rotate([0, 0, rot])


def max9814_mic_hole(wall=2):
    """
    ORIGIN: bottom left
    """
    tiny = 0.01
    return pbc.hole(5, wall + 6).translate([0, 0, 6 - tiny])


def bme280():
    """
    ORIGIN: bottom left
    """
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
    """
    ORIGIN: bottom left
    """
    return pbc.hole(3 / 2, wall).translate([(11.5 / 2) - 3.5, 0, 0])


def usb_breakout():
    """
    This is an unusual component.

    This "shape" part (usually) goes on the bottom. (Rotate as necessary.)

    The "hole" part goes on a side.

    Thus you don't put the "shape" and "hole" in the same call.

    ORIGIN: centered
    """
    tp = pbc.tap_post(6, 3)
    return union(tp.translate([-7, -4, 0]), tp.translate([-7, 4, 0])).rotate(
        [0, 90, 90]
    )


def usb_breakout_hole(wall=2):
    """
    SEE USAGE NOtE IN usb_breakout()

    ORIGIN: centered
    """
    return pbc.horizontal_slot_hole(8, 3, wall).translate([0, 6 + 2 + 1.5, 0])


if __name__ == "__main__":
    view(bme280())
    view(bme280_hole())
    view(usb_breakout())
    view(usb_breakout_hole())
    view(max9814_mic())
    view(max9814_mic_hole())
    view(circular_speaker_grid_holes(40))
    view(doppler_motion_sensor())
    view(round_buzzer(20, 3))
    view(round_buzzer_hole(3))

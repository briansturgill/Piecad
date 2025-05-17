"""
Attach CPAP hose to vacuum cleaner. For a Dyson, but could easily be adapted.
"""

# I use this to clean around/in/under my 3d printers.

from piecad import *

# These settings are for a recent Dyson... the "join" is zeroed as there
# is a notch on the Dyson attachment hose.
ch_r = 11 - 0.3  # CPAP hose inner radius
cha_h = 20  # Height of CPAP hose adapter
vh_r = 33 / 2  # Vacuum hose inner radius
vha_h = 34  # Height of Vacuum hose adapter
ja_h = 4  # Height of join portion
ja_r = vh_r
wall_thk = 3


def adapter():
    return union(
        difference(
            cylinder(radius=ch_r, height=cha_h),
            cylinder(radius=ch_r - 2, height=cha_h + 2).translate([0, 0, -1]),
        ).translate([0, 0, vha_h + ja_h]),
        difference(
            cylinder(radius=ja_r, height=ja_h),
            cylinder(radius=ch_r - 2, height=ja_h + 2).translate([0, 0, -1]),
        ).translate([0, 0, vha_h]),
        difference(
            cylinder(radius=vh_r, height=vha_h),
            cylinder(radius=ch_r - 2, height=vha_h + 2).translate([0, 0, -1]),
        ),
    )


def joiner():
    return union(
        difference(
            cylinder(radius=ch_r, height=cha_h),
            cylinder(radius=ch_r - 2, height=cha_h + 2).translate([0, 0, -1]),
        ).translate([0, 0, cha_h + ja_h]),
        difference(
            cylinder(radius=ch_r + 3, height=ja_h),
            cylinder(radius=ch_r - 2, height=ja_h + 2).translate([0, 0, -1]),
        ).translate([0, 0, cha_h]),
        difference(
            cylinder(radius=ch_r, height=cha_h),
            cylinder(radius=ch_r - 2, height=cha_h + 2).translate([0, 0, -1]),
        ),
    )


if __name__ == "__main__":
    a = adapter()
    j = joiner()
    view(a)
    view(j)
    save("/tmp/adapter.obj", a)
    save("/tmp/joiner.obj", j)

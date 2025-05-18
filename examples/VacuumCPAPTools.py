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
noz_base_h = 21
noz_cone_h = 9
noz_h = 70
noz_r = 8


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


def nozzle():
    return difference(
        union(
            difference(
                cylinder(radius=noz_r, height=noz_h),
                cylinder(radius=noz_r - 2, height=noz_h + 2).translate([0, 0, -1]),
            ).translate([0, 0, noz_base_h + noz_cone_h]),
            difference(
                cone(radius_low=ch_r, radius_high=noz_r, height=noz_cone_h),
                cone(
                    radius_low=ch_r - 2, radius_high=noz_r - 2, height=noz_cone_h + 2
                ).translate([0, 0, -1]),
            ).translate([0, 0, noz_base_h]),
            difference(
                cylinder(radius=ch_r, height=noz_base_h),
                cylinder(radius=ch_r - 2, height=noz_base_h + 2).translate([0, 0, -1]),
            ),
        ),
        cuboid([noz_r * 2, noz_r * 6, 20], center=True)
        .rotate([-45, 0, 0])
        .translate([0, 0, noz_base_h + noz_cone_h + noz_h]),
    )


if __name__ == "__main__":
    a = adapter()
    j = joiner()
    n = nozzle()
    view(a)
    view(j)
    view(n)
    save("/tmp/v_adapter.obj", a)
    save("/tmp/v_joiner.obj", j)
    save("/tmp/v_nozzle.obj", n)

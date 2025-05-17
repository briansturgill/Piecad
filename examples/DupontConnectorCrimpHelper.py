"""
Accessories for iCrimp/IWISS SN58B and SN28B crimpers to make it easy to crimp Dupont connectors.
"""

from piecad import *

set_default_segments(100)

CRIMPER = "SN28B"  # Either "SN58B" or "SN28B"


def lip_len():
    return 22 if CRIMPER == "SN28B" else 24.25


lip_h = 3  # Without teeth
lip_overhang = 2.3
lip_w = 7.25


def front_to_first():
    return 5.8 if CRIMPER == "SN28B" else 3.7


h_first = 2.30
max_jaw_h = 14.3
min_jaw_h = 11.0
jaw_w = 9.5

screw_d = 7.9
screw_h = 2


def front_to_screw():
    return 8.5 if CRIMPER == "SN28B" else 10.5


screw_to_lip = 1.1

thk = screw_h  # Thickness of outer walls.

holder_h = lip_h + max_jaw_h + thk
holder_w = jaw_w + 2 * thk
holder_len = lip_len() + thk


def bevel_on_y(x, y):
    return (
        polygon(paths=[[(0, 0), (0, x), (y, x)]])
        .extrude(x)
        .rotate([90, 0, 90])
        .translate([0, 0, -x])
    )


def dupont():
    hole_sz = 2
    pin_sz = 1
    hole_depth = 5
    z = hole_sz + thk + h_first
    x = 2 * thk + front_to_first() * 2
    y = hole_depth + thk
    return union(
        difference(
            cube([x, y, z]),
            cube([hole_sz, hole_depth + 1, hole_sz]).translate(
                [front_to_first() + thk - hole_sz / 2, -1, h_first]
            ),
            cube([pin_sz, hole_depth * 4 + 1, pin_sz]).translate(
                [front_to_first() + thk - pin_sz / 2, -1, h_first]
            ),
        ),
        bevel_on_y(x, y),
    ).translate([0, holder_w - thk, holder_h])


def lip():
    return union(
        cube([lip_len() + 1, lip_h + 1, lip_w]),
        cube([lip_overhang + lip_len() + 1, min_jaw_h, lip_w]).translate(
            [0, -min_jaw_h, 0]
        ),
    )


def jaw():
    h = max_jaw_h
    min_bot = h - min_jaw_h
    l = lip_len() + 1
    return polygon(paths=[[(0, min_bot), (0, h), (l, h), (l, 0)]]).extrude(jaw_w)


def screw_slot():
    r = screw_d / 2
    return union(
        cylinder(radius=r, height=screw_h + 2).translate([r, r, -1]),
        cube([lip_len(), r * 2, screw_h + 2]).translate([r, 0, -1]),
    )


def round_corner_untrimed(r):
    return difference(
        cube([r * 2, r * 2, holder_w + 2], center=True),
        cylinder(radius=r, height=holder_w + 4).translate([0, 0, -(holder_w + 4) / 2]),
    ).translate([0, 0, (holder_w + 2) / 2])


def round_corner():
    r = 8
    return difference(
        round_corner_untrimed(r),
        cube([r * 2 + 2, r + 2, holder_w + 4]).translate([-r, -1, -1]),
        cube([r + 2, r + 1, holder_w + 4]).translate([0, -r - 1, -1]),
    ).translate([r, r, 0])


def holder():
    return (
        difference(
            cube([holder_len, holder_h, holder_w]),
            lip().translate([thk, holder_h - lip_h, (holder_w - lip_w) / 2]),
            jaw().translate([thk, thk, (holder_w - jaw_w) / 2]),
            screw_slot().translate(
                [
                    front_to_screw() + thk,
                    holder_h - lip_h - screw_to_lip - screw_d,
                    holder_w - thk,
                ]
            ),
            round_corner(),
        )
        .rotate([90, 0, 0])
        .translate([0, holder_w, 0])
    )


# Either "SN58B" or "SN28B"
def make_for(crimper):
    global CRIMPER
    CRIMPER = crimper
    return union(view(dupont()), view(holder())).rotate([0, -90, -45])


if __name__ == "__main__":
    sn28b = make_for("SN28B")
    sn58b = make_for("SN58B")
    view(sn28b)
    view(sn58b)
    save("/tmp/sn28b.obj", sn28b)
    save("/tmp/sn58b.obj", sn58b)

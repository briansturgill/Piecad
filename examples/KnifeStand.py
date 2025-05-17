"""
Knife Stand Example
"""

from piecad import *

h = 150
kh = 115
kd = 28
kw = 3
d = 80
w = 120 + kw


def base(off=0):
    return cube([w + off, d + off, h + off])


def stand():
    woff = kd / 2
    doff = 8
    return difference(
        base(),
        cube([kw, kd, h]).translate([15, doff, 5]),
        cube([kw, kd, h]).translate([15, d - kd - doff, 5]),
        cube([kw, kd, h]).translate([45, doff, 5]),
        cube([kw, kd, h]).translate([45, d - kd - doff, 5]),
        cube([kw, kd, h]).translate([75, doff, 5]),
        cube([kw, kd, h]).translate([75, d - kd - doff, 5]),
        cube([kw, kd, h]).translate([105, doff, 5]),
        cube([kw, kd, h]).translate([105, d - kd - doff, 5]),
        base(10).rotate([75, 0, 0]).translate([-1, d, kh]),
    )


if __name__ == "__main__":
    ks = stand()
    view(ks)
    save("/tmp/knife_stand.obj", ks)

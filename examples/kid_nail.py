# Derived from threads.scad: https://github.com/rcolyer/threads-scad.git
# Created 2016-2017 by Ryan A. Colyer.
# This work is released with CC0 into the public domain.
# hthtps://creativecommons.org/publicdomain/zero/1.0/
#
# https://www.thingiverse.com/thing:1686322
#
# v2.1

from piecad import *

small_r = 11.75 / 2
large_r = 15.5 / 2
h = 34
stop_r = 18 / 2
stop_h = 11
top_r = 32 / 2
top_h = 10

hole_wb = 2
hole_wt = 2
hole_h = h + stop_h / 2


def make_nail(r):
    return difference(
        union(
            cone(radius_high=r - 1, radius_low=r, height=h).translate(
                [0, 0, top_h + stop_h]
            ),
            cylinder(radius=stop_r, height=stop_h).translate([0, 0, top_h]),
            cylinder(radius=top_r, height=top_h),
        ),
        cone(radius_high=r - 2 - 1, radius_low=r - 2, height=h + stop_h).translate(
            [0, 0, top_h + stop_h]
        ),
        polygon([[(0, hole_wb), (hole_wt, hole_h), (hole_wt, hole_h), (hole_wb, 0)]])
        .extrude(hole_h)
        .translate([0, 0, h + stop_h + top_h - hole_h]),
    )


s = make_nail(small_r).rotate([90, 0, 0])
l = make_nail(large_r).rotate([90, 0, 0])
view(s)
save("/tmp/kid_nail_small.obj", s)
view(l)
save("/tmp/kid_nail_large.obj", l)

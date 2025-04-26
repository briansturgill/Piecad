# Derived from threads.scad: https://github.com/rcolyer/threads-scad.git
# Created 2016-2017 by Ryan A. Colyer.
# This work is released with CC0 into the public domain.
# https://creativecommons.org/publicdomain/zero/1.0/
#
# https://www.thingiverse.com/thing:1686322
#
# v2.1

from piecad import *
from math import sqrt

kid_circle = 34.0
kid_nut = 24.0
kid_height = 12.0
kid_screw_size = 12.0
kid_tolerance = 0.6


def rcube(sz, r):
    return rounded_rectangle([sz[0], sz[1]], r).extrude(sz[2])


def KidSizedXPiece(nHoles):
    rc_r = 4
    pad = rc_r * 2
    x = nHoles * (kid_circle + pad)
    y = kid_circle + pad
    z = 5.0
    obj = rcube([x, y, z], rc_r)
    for i in range(1, nHoles + 1):
        r = (kid_circle + pad) / 2.0
        print(r + r * 2 * (i - 1), r)
        obj = difference(
            obj,
            cylinder(height=z, radius=(kid_screw_size + 1) / 2.0).translate(
                [r + r * 2 * (i - 1), r, 0]
            ),
        )
    return obj


def KidSizedBase():
    return union(
        cylinder(height=kid_height, radius=kid_nut / 2.0, segments=6),
        cylinder(height=2, radius=kid_circle / 2.0),
    )


def KidSizedWrench():
    h = kid_height - 2
    i_r = (kid_nut + 2) / 2
    o_r = (kid_nut + 16) / 2
    bar_l = 105
    bar_w = 20
    hole = cylinder(height=h, radius=i_r, segments=6)
    outer = cylinder(height=h, radius=o_r)
    end = difference(outer, hole)
    return union(
        end,
        cube([bar_l, bar_w, h]).translate([o_r - 3, -o_r / 2, 0]),
        end.translate([bar_l + o_r * 2 - 5, 0, 0]),
    )


def KidSizedNut():
    return difference(
        KidSizedBase(),
        KidSizedThreadedRod(kid_height, isNut=True),
        cylinder(radius=(kid_screw_size + 1) / 2.0, height=2),
    )


def KidSizedBoltInsert(isHead=False):
    x = sqrt(kid_circle)
    if isHead:
        x = x + (kid_tolerance / 4.0)
    return cube([x, x, kid_height - 6]).translate([-x / 2.0, -x / 2.0, 0])


def KidSizedBolt():
    obj = difference(
        KidSizedBase().rotate([0, 0, 30]),
        cube([kid_circle, 4, 4], center=True).translate([0, 0, kid_height]),
        KidSizedBoltInsert(isHead=True),
    )
    return obj


def KidSizedThreadedRod(height, isNut=False):
    if isNut:
        r = (kid_screw_size - 2 + kid_tolerance) / 2.0
    else:
        r = (kid_screw_size - 2) / 2.0
    obj = circle(radius=r).translate([0, 1])
    obj = extrude_transforming(
        obj, height=height, num_twist_divisions=360, twist=360 * height / 4.0
    )
    if isNut:
        return obj
    return union(KidSizedBoltInsert().translate([0, 1, height]), obj)


b = KidSizedBolt()

n = KidSizedNut()

r = KidSizedThreadedRod(40)

w = KidSizedWrench()

save("/tmp/kid_b.obj", b)
view(b)
save("/tmp/kid_n.obj", n)
view(n)
save("/tmp/kid_r.obj", r)
view(r)
save("/tmp/kid_w.obj", w)
view(w)

for h in range(2, 7):
    p = KidSizedXPiece(h)
    save(f"/tmp/kid_{h}p.obj", p)
    view(p)

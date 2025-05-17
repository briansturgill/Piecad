"""
Stand I use for a ResMed CPAP, should be easily tuned to other sized machines.
"""

from piecad import *

cpap_w = 210
cpap_d = 180
cpap_h = 120  # Needed above bed
bed_h = 4
bed_rad = 4

cpap_max_h = 280  # In my case the lowest point of my lamp shade.

pole_h = cpap_max_h - cpap_h - 2 * bed_h

pole_sz = 10
pole_rad = bed_rad - 2
wall = 2
coupler_sz = pole_sz + 2 * wall
coupler_rad = bed_rad
coupler_h = 20

tiny = 0.2


def rcube(dim, radius):
    return rounded_rectangle([dim[0], dim[1]], radius).extrude(dim[2])


def coupler():
    return difference(
        rcube([coupler_sz, coupler_sz, coupler_h], coupler_rad),
        rcube([pole_sz, pole_sz, coupler_h + 2], pole_rad).translate([wall, wall, -1]),
    )


def pole():
    return (
        rcube([pole_sz - tiny, pole_sz - tiny, pole_h], pole_rad)
        .rotate([0, 90, 0])
        .translate([0, 0, (pole_sz - tiny)])
    )


def support():
    cross_offset = coupler_h + 5
    p_sz = pole_sz - tiny
    cross_yoff = p_sz / 2
    cross_d = cpap_d - 2 * coupler_sz + 2 * wall + tiny
    return union(
        pole(),
        pole().translate([0, cross_d + p_sz, 0]),
        polygon(
            [
                [
                    [pole_h - cross_offset, 3 * cross_yoff + cross_d],
                    [cross_offset + p_sz, cross_yoff],
                    [cross_offset, cross_yoff],
                    [pole_h - (cross_offset + p_sz), 3 * cross_yoff + cross_d],
                ]
            ]
        ).extrude(p_sz),
        polygon(
            [
                [
                    [cross_offset, 3 * cross_yoff + cross_d],
                    [pole_h - cross_offset - p_sz, cross_yoff],
                    [pole_h - cross_offset, cross_yoff],
                    [cross_offset + p_sz, 3 * cross_yoff + cross_d],
                ]
            ]
        ).extrude(p_sz),
    )


def bottom():
    return union(
        rcube([cpap_w, coupler_sz, bed_h], bed_rad),
        rcube([coupler_sz, cpap_d, bed_h], bed_rad),
        rcube([cpap_w, coupler_sz, bed_h], bed_rad).translate(
            [0, cpap_d - coupler_sz, 0]
        ),
        rcube([coupler_sz, cpap_d, bed_h], bed_rad).translate(
            [cpap_w - coupler_sz, 0, 0]
        ),
        coupler().translate([0, 0, bed_h]),
        coupler().translate([cpap_w - coupler_sz, 0, bed_h]),
        coupler().translate([0, cpap_d - coupler_sz, bed_h]),
        coupler().translate([cpap_w - coupler_sz, cpap_d - coupler_sz, bed_h]),
    )


def top():
    cs = coupler_sz
    big_w = cpap_w - 2 * coupler_sz
    big_d = cpap_d - 2 * coupler_sz
    hole_w = (big_w - 2 * coupler_sz) / 3
    hole_d = (big_d - 3 * coupler_sz) / 4
    l = []
    for i in range(3):
        for j in range(4):
            x = (i + 1) * cs + i * hole_w
            y = (j + 1) * cs + j * hole_d
            l.append(rcube([hole_w, hole_d, bed_h + 2], bed_rad).translate([x, y, -1]))
    return difference(
        union(bottom(), rcube([big_w, big_d, bed_h], bed_rad).translate([cs, cs, 0])),
        *l
    )


p = pole()
s = support()
b = bottom()
t = top()

if __name__ == "__main__":
    view(p)
    view(s)
    view(b)
    view(t)

    save("/tmp/cpap_p.obj", p)
    save("/tmp/cpap_s.obj", s)
    save("/tmp/cpap_b.obj", b)
    save("/tmp/cpap_t.obj", t)

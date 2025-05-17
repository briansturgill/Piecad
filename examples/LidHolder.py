"""
Make a holder for multiple sizes of lids.
"""

from piecad import *

tiny = 105
small = 130
medium = 158
large = 190

thk = 2

sup_hole_r = 3
sup_h = 60

base_h = 10


def outer_sup(solid=False):
    o = union(
        circle(sup_hole_r * 2),
        square([sup_hole_r * 4, sup_hole_r * 8]).translate([-sup_hole_r * 2, 0]),
    )
    if not solid:
        o = difference(o, circle(sup_hole_r))
    o = o.extrude(thk)
    return o


def make_disc(r, half=False):
    o = circle(r)
    if half:
        o = difference(
            o, square([r * 2, r * 2]).translate([-r, -r * 2 - sup_hole_r * 2])
        )
    o = o.extrude(thk)
    return o


def make_outer_sups(r, solid=False):
    return union(
        outer_sup(solid).rotate([0, 0, -90]).translate([-(r + sup_hole_r * 2), 0, 0]),
        outer_sup(solid).rotate([0, 0, 90]).translate([(r + sup_hole_r * 2), 0, 0]),
        outer_sup(solid).rotate([0, 0, 180]).translate([0, (r + sup_hole_r * 2), 0]),
    )


def make_sup_holes(r):
    return (
        union(
            circle(sup_hole_r).translate([-(r + sup_hole_r * 2), 0]),
            circle(sup_hole_r).translate([(r + sup_hole_r * 2), 0]),
            circle(sup_hole_r).translate([0, (r + sup_hole_r * 2)]),
        )
        .extrude(thk + 2)
        .translate([0, 0, -1])
    )


def disc(d, inner_d, solid=False):
    if inner_d == 0:
        return union(make_disc(d / 2), make_outer_sups(d / 2, solid))
    else:
        return difference(
            union(
                make_disc(d / 2, half=True),
                make_outer_sups(d / 2, solid),
                make_disc(inner_d / 2),
            ),
            make_sup_holes(inner_d / 2),
        )


def support():
    return union(
        cylinder(radius=sup_hole_r - 0.25, height=thk),
        cylinder(radius=sup_hole_r * 2, height=sup_h).translate([0, 0, thk]),
        cylinder(radius=sup_hole_r - 0.25, height=thk).translate([0, 0, sup_h + thk]),
    )


wedge = None


def tilt_base(bottom):
    global wedge
    bottom = bottom.project()
    off_b = bottom.offset(0.05, "square").extrude(base_h - 2).translate([0, 0, 2])
    off_big = bottom.offset(2 + 0.05, "square").extrude(base_h)
    wedge_h = base_h - 2
    wedge_w = large
    wedge = intersect(
        cylinder(radius=large / 2, height=wedge_h),
        polygon(paths=[[(0, 0), (wedge_w, 0), (wedge_w, -wedge_h)]])
        .extrude(wedge_w)
        .rotate([90, 0, 180])
        .center(),
    )
    xmin, ymin, zmin, xmax, ymax, zmax = wedge.bounding_box()
    wedge = wedge.translate([0, 0, -(zmax - zmin)]).rotate([0, 0, 90])
    off_big = union(off_big, wedge)
    return difference(off_big, off_b)


d1 = disc(tiny, 0)
d2 = disc(small, tiny)
d3 = disc(medium, small)
d4 = disc(large, medium)
d5 = disc(large, 0)
tb = tilt_base(disc(large, 0, True))  # Uses solid version of d5.
sup = support()

if __name__ == "__main__":
    view(d1)
    view(d2)
    view(d3)
    view(d4)
    view(d5)
    view(sup)
    view(tb)
    save("/tmp/lh_d1.obj", d1)
    save("/tmp/lh_d2.obj", d2)
    save("/tmp/lh_d3.obj", d3)
    save("/tmp/lh_d4.obj", d4)
    save("/tmp/lh_d5.obj", d5)
    save("/tmp/lh_tb.obj", tb)
    save("/tmp/lh_sup.obj", sup)

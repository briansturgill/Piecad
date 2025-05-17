"""
Axes ProjectBox Example

Useful for visualizing rotations in 3d space.
"""

if __name__ == "__main__":
    from piecad import *

    axes = union(
        cube([20, 20, 20]),
        text(20, "X").extrude(40).rotate([-90, 180, -90]).translate([20, 0, 0]),
        text(20, "Y").extrude(40).rotate([90, 0, 180]).translate([20, 20, 0]),
        text(20, "Z").extrude(40).rotate([0, 0, 0]).translate([0, 0, 20]),
    )

    view(axes)
    save("/tmp/axes.obj", axes)

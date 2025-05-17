"""
Replace an oval cap lost from my bike repair stand.
"""

if __name__ == "__main__":
    from piecad import *

    x = 41
    y = 49
    z = 25
    wall = 2

    def oval(x, y):
        return union(
            circle(x / 2),
            circle(x / 2).translate([0, y - x]),
            square([x, y - x]).translate([-x / 2, 0]),
        )

    cap = difference(
        oval(x + wall, y + wall).extrude(z + wall + 1),
        oval(x, y).extrude(z + wall + 1).translate([0, 0, wall + 1]),
    )
    view(cap)
    save("/tmp/cap.obj", cap)

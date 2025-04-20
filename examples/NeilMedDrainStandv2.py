from piecad import *

wall = 2
r = 5
x = 140
y = 70
z = 20
sh = 120
case_z = sh + 35
case_inset_z = z / 2
sr = 25 / 2
bh = 35
br = 32 / 2
pw = wall * 8
pd = wall * 4


def rcube(dim, radius):
    return rounded_rectangle([dim[0], dim[1]], radius).extrude(dim[2])


def DrainBase():
    return difference(
        rcube([x + 2 * wall, y + 2 * wall, z + wall], r + 2).translate(
            [-wall, -wall, -wall]
        ),
        rcube([x, y, z + wall], r),
    ).translate([0, 0, wall])


def DrainCase():
    return union(
        difference(
            rcube([x + 2 * wall, y + 2 * wall, case_z + wall], r + 2).translate(
                [-wall, -wall, -wall]
            ),
            rcube([x, y, case_z], r),
        ),
        difference(
            rcube([x, y, case_z + case_inset_z], r),
            rcube([x - 2 * wall, y - 2 * wall, case_z + case_inset_z], r - 2).translate(
                [+wall, +wall, 0]
            ),
        ),
    ).translate([0, 0, wall])


def DrainBottom(h):
    return (
        union(
            rcube([pw, pw, pd], 2).translate([-pw + wall, 0, 0]), rcube([pd, pw, h], 2)
        )
        .rotate([0, 0, -180])
        .translate([wall, pw, 1])
    )


def DrainTop(cylr):
    thk = 15 * wall
    return difference(
        union(
            cylinder(height=wall * 3, radius=cylr + wall),
            rcube([pd + 4 * wall, pw + 3 * wall, thk], 2).translate(
                [-(cylr + pd + 4 * wall), -(cylr + 4 * wall) / 2, 0]
            ),
        ),
        cylinder(height=wall * 2 * 2, radius=cylr).translate([0, 0, -1]),
        rcube([pd + 1, pw, thk], 2).translate(
            [-(cylr + pd + 3 * wall), -(cylr + 1 * wall) / 2, 1]
        ),
    )


def DrainTops():
    return union(
        DrainTop(br).translate([0, y + 30, 0]).rotate([0, 0, 0]),
        DrainTop(sr).translate([0, y * 2 + 10, 0]).rotate([0, 0, 0]),
    )


def DrainStand():
    return union(
        DrainBase(),
        DrainBottom(sh).translate([(x / 6) - 5, y / 2 - 4 * wall, 0]),
        DrainBottom(bh).translate([(x - 2.5 * (x / 6)), y / 2 - 4 * wall, 0]),
    )


save("/tmp/NeilMedDrainStandv2_stand.obj", DrainStand())
save("/tmp/NeilMedDrainStandv2_case.obj", DrainCase())
save("/tmp/NeilMedDrainStandv2_tops.obj", DrainTops())

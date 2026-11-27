"""
Quick example of modify_edges usage.
"""

from piecad import *

if __name__ == "__main__":
    Config.set_layer_resolution(0.08)
    radius = 3
    height = 15

    obj = union(
        cuboid([height * 5, height * 8, height]),
        cube([height * 2.5, height * 2.5, height / 2]).translate([0, 0, height]),
        difference(
            cylinder(radius=height / 3, height=height / 2),
            cylinder(radius=height / 4, height=height / 2),
        ).translate([height * 1.25, height * 1.25, 1.5 * height]),
        # tetrahedron([[35, 15, 0], [10, 45, 0], [40, 37, 0], [25, 70, 35]]).translate((0,0,10))
    )
    view(obj)
    save("object.3mf", obj)
    cobj = obj.modify_edges("chamfer", size=radius)
    save("chamfer.3mf", cobj)
    msg = quick_check_mesh(*cobj.to_verts_and_faces())
    if msg != "":
        print(msg)
    view(cobj)
    fobj = obj.modify_edges("fillet", size=radius)
    save("fillet.3mf", fobj)
    view(fobj)
    view_all_now()

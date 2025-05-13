from piecad import sin, cos, union, difference, cylinder, cone

def tap_post(h: float, size_d: float, post_wall=2.0, add_taper=False, z_rot=0):
    """
    A post suitable for tapping or using a self-taping screw or bolt.

    Parameter `h` is the height of the post (without taper).

    Parameter `size_d` is a diameter because that's how bolts are usually
    specified. For example a M4 bolt has a 4mm diameter.

    Parameter `post_wall`, how thick (beyond the screw) the wall should be.

    If you are mounting your posts horizontally (from the sides of the box),
    set `add_taper` to `True` and a 45 degree taper is added to the bottom
    of the post to aid in 3d printing.

    By default a tap post's bottom is centered at (0, 0, 0), BUT, if you
    add a taper then the tap post's top is centered at (0, 0, 0).

    Parameter `z_rot` is if you want to rotate the post (used in some lids).
    """
    inner_d = size_d*0.8 #Possibly snug, but with PLA I prefer that
    outer_d = post_wall*2+size_d
    circ = difference(circle(outer_d/2.0), circle(inner_d/2.0))
    if (add_taper):
        tp = circ.extrude(h*2)
        tp = difference(tp,
            cube([outer_d, outer_d, h*3+2], center=True).rotate([45, 0, z_rot]).translate([0,0,h]))
        return tp.translate([0, 0, -h*2]) 
    else:
        return circ.extrude(h)

def horizontal_slot_hole(w, h, wall):
    return rounded_rectangle((w, h), h/2.0).extrude(wall).rotate((180, 0, 0)).translate((-(w+h)/2.0, 0, 0))

def tapered_bolt_hole(height, size_d):
    bolt_top_r = size_d
    r = size_d/2.0
    chamfer_h = sin(45)*bolt_top_r
    h_chamfered = height if chamfer_h>height else chamfer_h
    h_remaining = 0 if chamfer_h>height else height-chamfer_h
    o = union(
        cylinder(height=1, radius=bolt_top_r),
        cone(height=h_chamfered, radius_low=bolt_top_r, radius_high=r).translate((0, 0, 1)),
        cylinder(height=h_remaining, radius=r*0.80).translate((0, 0, h_chamfered+1)),
    ).rotate((180, 0, 0))
    return o

def hole(r, wall):
    return circle(r).extrude(wall).rotate((180, 0, 0))

def wedge(sz, thk):
    return polyhedron(vertices=[
            [0, 0, 0], [0, -sz, 0], [0, 0, sz],
            [thk, 0, 0], [thk, -sz, 0], [thk, 0, sz]],
            faces=[[1,2,0], [4,3,5], [3,0, 2], [3,2,5], [3,1,0], [4,1,3], [2,1,5], [5,1,4]
            ])

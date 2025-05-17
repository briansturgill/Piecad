"""
THIS FEATURE IS SOMEWHAT EXPERIMENTAL, THE API SUBJECT TO CHANGE.

A class for quickly constructing a project box.

Call `finish` to retrieve the Obj3d of the final box.

See `examples` to see how to use ProjectBox (`pbox_*).

The general idea is that ProjectBox creates routines that let you position components
in 2D (x, y) on the left, right, front, back, top, bottom of a ProjectBox.
Generally 2D design is easier than 3D.

Components are shapes or holes.  Holes names end in "_hole" or "holes".
When a ProjectBox is finished, all shapes are unioned with the box and
all holes are differenced from the box.

By convention component origins (0, 0) are either centered, or bottom left.
It is a good idea to show the ORIGIN in the components documentation.
"""

from piecad import (
    Obj3d,
    config,
    rounded_rectangle,
    union,
    intersect,
    difference,
    polyhedron,
    circle,
    cube,
    cone,
    cylinder,
    view,
    sin,
    _chkGE,
    _chkV3,
)

class ProjectBox:
    """
    Quickly create a project box.
    """
    def __init__(self,
        size: list[float, float, float],
        wall: float = 2.0,
        segments: int = -1,
    ):
        """
        Make a project box with the x (width), y (depth), and z (height) values given in size.

        The dimensions are for the INSIDE of the box.

        The INSIDE of the box will be placed at `(0, 0, 0)`.

        The `wall` parameter specifies the thickness of the major walls of the box.

        For `segments` see the documentation of [`set_default_segments`](index.html#piecad.set_default_segments).

        <iframe width="100%" height="380" src="/examples/projectbox.html"></iframe>
        """
        if segments == -1:
            segments = config["DefaultSegments"]
        _chkGE("segments", segments, 3)
        _chkV3("size", size)
        _chkGE("wall", wall, 2.0)

        tiny = 0.5
        self._segments = segments
        self._size = size
        self.w, self.d, self.h = self._size
        self.h = self.h+wall
        self.wall = wall
        self.off = 2*wall+tiny

        def mkwall(dims, ty=None):
            screw_h = 10
            screw_top_r = 3.0
            screw_r = (screw_top_r/2)*0.8 # 3mm screw hole
            rd = (screw_top_r+2*wall)+tiny
            rr = rd/2.0
            off = self.off

            def post(rot):
                post_l = 2*rr
                post_w = 3*wall+tiny
                return difference(
                    union(
                        cylinder(radius=rr, height=self.h),
                        cube([post_l, post_w, self.h]).translate([0, -rr, 0]),
                        cube([post_w, post_l, self.h]).translate([-rr, 0, 0]),
                    ),
                    cylinder(radius=screw_r, height=screw_h).translate([0, 0, self.h-screw_h]),
                ).translate([rr, rr, 0]).rotate([0, 0, rot])

            if ty == 't' or ty == 'm':
                w = dims[0]+2*off
                d = dims[1]+2*off
                h = dims[2]
                o = rounded_rectangle([w, d], rr, segments).extrude(h)
                if ty == 't':
                    o = union(o,
                       post(0),
                       post(270).translate([0, d, 0]),
                       post(180).translate([w, d, 0]),
                       post(90).translate([w, 0, 0]),
                    )
                    o = difference(
                        o,
                        cube([w-4*rr, wall+tiny, self.h]).translate([2.0*rr,wall,wall]),
                        cube([w-4*rr, wall+tiny, self.h]).translate([2.0*rr,d-2*wall,wall]),
                        cube([wall+tiny, d-4*rr, self.h]).translate([wall, 2.0*rr, wall]),
                        cube([wall+tiny, d-4*rr, self.h]).translate([w-2*wall,2.0*rr,wall]),
                    )
                else:
                    def tbh():
                        chamfer_h = sin(45)*screw_top_r
                        h_chamfered = screw_h if chamfer_h>screw_h else chamfer_h
                        h_remaining = 0 if chamfer_h>screw_h else screw_h-chamfer_h
                        o = union(
                            cylinder(height=0.5, radius=screw_top_r),
                            cone(height=h_chamfered, radius_low=screw_top_r, radius_high=screw_r).translate((0, 0, 0.5)),
                            cylinder(height=h_remaining, radius=screw_r).translate((0, 0, h_chamfered+1)),
                        )
                        return o

                    o = difference(
                        o,
                        tbh().translate([rr, rr, 0]),
                        tbh().translate([w-rr, rr, 0]),
                        tbh().translate([rr, d-rr, 0]),
                        tbh().translate([w-rr, d-rr, 0]),
                    )
                o = o.translate([-off, -off, -wall])
            else:
                w = dims[0]-2*rr-tiny+wall
                d = dims[1]-wall
                h = dims[2]
                o = cube([w, d, h])
                o = o.translate([0, 0, -wall])
            return o

        self._l_wall = mkwall([self.d, self.h, self.wall])
        self._l_unions = []
        self._l_differences = []
        self._r_wall = mkwall([self.d, self.h, self.wall])
        self._r_unions = []
        self._r_differences = []
        self._f_wall = mkwall([self.w, self.h, self.wall])
        self._f_unions = []
        self._f_differences = []
        self._k_wall = mkwall([self.w, self.h, self.wall])
        self._k_unions = []
        self._k_differences = []
        self._t_wall = mkwall([self.w, self.d, self.wall], 't')
        self._t_unions = []
        self._t_differences = []
        self._m_wall = mkwall([self.w, self.d, self.wall], 'm')
        self._m_unions = []
        self._m_differences = []


    def left(self, x, y, shape, hole):
        """
        Add a component at `x, y` of the left side of the box.
        If `shape` or `hole` is not present, use `None`.
        """
        if shape != None:
            self._l_unions.append(shape.translate([x, y, 0]))
        if hole != None:
            self._l_differences.append(hole.translate([x, y, 0]))

    def right(self, x, y, shape, hole):
        """
        Add a component at `x, y` of the right side of the box.
        If `shape` or `hole` is not present, use `None`.
        """
        if shape != None:
            self._r_unions.append(shape.translate([x, y, 0]))
        if hole != None:
            self._r_differences.append(hole.translate([x, y, 0]))

    def front(self, x, y, shape, hole):
        """
        Add a component at `x, y` of the front side of the box.
        If `shape` or `hole` is not present, use `None`.
        """
        if shape != None:
            self._f_unions.append(shape.translate([x, y, 0]))
        if hole != None:
            self._f_differences.append(hole.translate([x, y, 0]))

    def back(self, x, y, shape, hole):
        """
        Add a component at `x, y` of the back side of the box.
        If `shape` or `hole` is not present, use `None`.
        """
        if shape != None:
            self._k_unions.append(shape.translate([x, y, 0]))
        if hole != None:
            self._k_differences.append(hole.translate([x, y, 0]))

    def top(self, x, y, shape, hole):
        """
        Add a component at `x, y` of the top of the box.
        If `shape` or `hole` is not present, use `None`.
        """
        if shape != None:
            self._t_unions.append(shape.translate([x, y, 0]))
        if hole != None:
            self._t_differences.append(hole.translate([x, y, 0]))

    def bottom(self, x, y, shape, hole):
        """
        Add a component at `x, y` of the bottom of the box.
        If `shape` or `hole` is not present, use `None`.
        """
        if shape != None:
            self._m_unions.append(shape.translate([x, y, 0]))
        if hole != None:
            self._m_differences.append(hole.translate([x, y, 0]))

    def finish(self) -> Obj3d:
        """
        The `finish` method returns a six-tuple of the parts of the project box:

        ```
        left, right, front, back, top, bottom = ProjectBox((45, 30, 20)).finish()
        ```

        """
        def f(box, differences, unions):
            if len(unions) > 0:
                box = union(box, *unions)
            if len(differences) > 0:
                box = difference(box, *differences)
            return box
        return (
                f(self._l_wall, self._l_differences, self._l_unions),
                f(self._r_wall, self._r_differences, self._r_unions),
                f(self._f_wall, self._f_differences, self._f_unions),
                f(self._k_wall, self._k_differences, self._k_unions),
                f(self._t_wall, self._t_differences, self._t_unions),
                f(self._m_wall, self._m_differences, self._m_unions),
                )

class pbc:
    @staticmethod
    def tap_post(h: float, size_d: float, post_wall=2.0, add_taper=False, z_rot=0):
        """
        A post suitable for tapping or using a self-taping screw or bolt.
        ORIGIN: centered

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

    @staticmethod
    def horizontal_slot_hole(w, h, wall=2):
        """
        Creates a hole that is a rounded_rectangle.
        Useful for things like a USB connector.

        ORIGIN: centered
        """
        return rounded_rectangle((w, h), h/2.0).extrude(wall).rotate((180, 0, 0)).translate((-(w+h)/2.0, 0, 0))

    @staticmethod
    def tapered_bolt_hole(height, size_d):
        """
        Creates a hole for a tapered bolt (the top of the head will be flush).

        ORIGIN: centered
        """
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

    @staticmethod
    def hole(r, wall=2):
        """
        Creates a negative shape to create a hole.
        (Used in difference, or the "hole" attribute in ProjectBox methods.)

        ORIGIN: centered
        """
        return circle(r).extrude(wall).rotate((180, 0, 0))


    @staticmethod
    def wire_tie_loop():
        """
        A "horseshoe" sized to pass a wire tie through.
        Useful for holding project boards in place with no screws.

        ORIGIN: centered
        """
        tiny = 0.01
        return difference(
            cube([2, 7, 6], center=True),
            cube([2+2*tiny, 3, 2], center=True),
        ).translate([1,3.5,3])

    @staticmethod
    def circular_speaker_grid_holes(radius, wall=2, hole_w=2):
        """
        The `radius` is the radius of the speaker grill.
        Also useful for air holes.

        Parameter `wall` specifies the width of the grid holes.
        Parameter `hole_w` specifies the width of the grid holes.

        Works best if speaker `radius` is evenly divisible by `hole_w`.

        ORIGIN: centered
        """
        tiny = 0.01
        l = []
        y = -(radius - hole_w)
        while y <= radius - hole_w:
            l.append(
                cube([radius * 2, hole_w, wall + 2 * tiny], center=True).translate([0, y, 0])
            )
            y += 2 * hole_w
        return intersect(
            union(*l), cylinder(radius=radius, height=wall + 2 * tiny, center=True)
        ).translate([0, 0, -(wall / 2) - tiny])

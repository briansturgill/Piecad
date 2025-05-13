"""
ProjectBox class.

A class for quickly constructing a project box.

Call `finish` to retrieve the Obj3d of the final box.
"""

from piecad import (
    Obj3d,
    config,
    rounded_rectangle,
    union,
    difference,
    cube,
    cone,
    cylinder,
    view,
    sin,
    _chkGE,
    _chkV3,
)


class ProjectBox:
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
            rr = (wall*3.0)/2+tiny
            screw_r = (3/2)*0.8 # 3mm screw hole
            screw_top_r = 3
            screw_h = 8
            off = self.off

            def post(rot):
                return difference(
                    union(
                        cylinder(radius=rr, height=self.h),
                        cube([rr, rr, self.h]).translate([-rr, 0, 0]),
                        cube([rr, rr, self.h]).translate([0, -rr, 0]),
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
                        cube([w-3*rr, wall+tiny, self.h]).translate([1.5*rr,wall,wall]),
                        cube([w-3*rr, wall+tiny, self.h]).translate([1.5*rr,d-2*wall,wall]),
                        cube([wall+tiny, d-3*rr, self.h]).translate([wall, 1.5*rr, wall]),
                        cube([wall+tiny, d-3*rr, self.h]).translate([w-2*wall,1.5*rr,wall]),
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
                w = dims[0]-rr+wall
                d = dims[1]-rr+2*tiny
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


    def left(self, x, y, pair):
        """
        Add a component at `x, y` of the left side of the box.
        The `pair` is the `(shape, hole)` of the component.
        If `shape` or `hole` is not present, use `None`.
        """
        shape, hole = pair
        if shape != None:
            self._l_unions.append(shape)
        if hole != None:
            self._differences.append(hole)

    def right(self, x, y, pair):
        """
        Add a component at `x, y` of the right side of the box.
        The `pair` is the `(shape, hole)` of the component.
        If `shape` or `hole` is not present, use `None`.
        """
        shape, hole = pair
        if shape != None:
            self._r_unions.append(shape)
        if hole != None:
            self._r_differences.append(hole)

    def front(self, x, y, pair):
        """
        Add a component at `x, y` of the front side of the box.
        The `pair` is the `(shape, hole)` of the component.
        If `shape` or `hole` is not present, use `None`.
        """
        shape, hole = pair
        if shape != None:
            self._f_unions.append(shape)
        if hole != None:
            self._f_differences.append(hole)

    def back(self, x, y, pair):
        """
        Add a component at `x, y` of the back side of the box.
        The `pair` is the `(shape, hole)` of the component.
        If `shape` or `hole` is not present, use `None`.
        """
        shape, hole = pair
        if shape != None:
            self._k_unions.append(shape)
        if hole != None:
            self._k_differences.append(hole)

    def top(self, x, y, pair):
        """
        Add a component at `x, y` of the top of the box.
        The `pair` is the `(shape, hole)` of the component.
        If `shape` or `hole` is not present, use `None`.
        """
        shape, hole = pair
        if shape != None:
            self._t_unions.append(shape)
        if hole != None:
            self._t_differences.append(hole)

    def bottom(self, x, y, pair):
        """
        Add a component at `x, y` of the bottom of the box.
        The `pair` is the `(shape, hole)` of the component.
        If `shape` or `hole` is not present, use `None`.
        """
        shape, hole = pair
        if shape != None:
            self._m_unions.append(shape)
        if hole != None:
            self._m_differences.append(hole)

    def finish(self) -> Obj3d:
        """
        The `finish` method returns a six-tuple of the parts of the project box:

        ```
        left, right, front, back, top, bottom = ProjectBox((45, 30, 20)).finish()
        ```

        """
        def f(box, differences, unions):
            if len(differences) > 0:
                box = difference(box, *differences)
            if len(unions) > 0:
                box = union(box, *unions)
            return box
        return (
                f(self._l_wall, self._l_differences, self._l_unions),
                f(self._r_wall, self._r_differences, self._r_unions),
                f(self._f_wall, self._f_differences, self._f_unions),
                f(self._k_wall, self._k_differences, self._k_unions),
                f(self._t_wall, self._t_differences, self._t_unions),
                f(self._m_wall, self._m_differences, self._m_unions),
                )

from . import (
    Obj3d,
    extrude_chaining,
    config,
    rounded_rectangle,
    union,
    difference,
    sin,
    cos,
)

from . import _chkGE, _chkV3, ValidationError


def _project_box(
    size: list[float, float, float],
    rounding_radius: float = 2.0,
    segments: int = -1,
    wall: float = 2.0,
    bottom: str = "bevel",
) -> Obj3d:

    l = []
    rr = rounding_radius
    res = config["LayerResolution"]
    arc_segs = rr / res
    deg_per_arc_seg = 90.0 / arc_segs
    deg = 0.0
    iota = rounding_radius - wall
    ix, iy, iz = size
    ix -= iota * 2
    iy -= iota * 2
    ox, oy, oz = size
    ox += wall * 2
    oy += wall * 2
    x, y, z = size

    if bottom == "round":
        cur_z = -rr
        smallest_rr = rr + sin(deg_per_arc_seg) / 2.0
        l.append(
            (
                -rr,
                rounded_rectangle((ix, iy), smallest_rr, segments).translate(
                    (iota, iota)
                ),
            )
        )
    elif bottom == "bevel":
        cur_z = -wall
        l.append((cur_z, rounded_rectangle((x, y), rr, segments)))
    else:
        cur_z = -wall
        l.append(
            (
                cur_z,
                rounded_rectangle((ox, oy), wall + rr, segments).translate(
                    (-rr + iota, -rr + iota)
                ),
            )
        )

    if bottom == "round":
        deg += deg_per_arc_seg
        while deg < 90.0:
            delta = rr * sin(deg)
            cur_z = -rr * cos(deg)
            l.append(
                (
                    cur_z,
                    rounded_rectangle(
                        (ix + 2 * delta, iy + 2 * delta), rr + delta - iota, segments
                    ).translate((-delta + iota, -delta + iota)),
                )
            )
            deg += deg_per_arc_seg

    cur_z = 0.0
    l.append(
        (
            cur_z,
            rounded_rectangle((ox, oy), wall + rr, segments).translate(
                (-rr + iota, -rr + iota)
            ),
        )
    )

    cur_z = oz
    l.append(
        (
            cur_z,
            rounded_rectangle((ox, oy), wall + rr, segments).translate(
                (-rr + iota, -rr + iota)
            ),
        )
    )

    o = extrude_chaining(l, is_convex=True)
    return o


"""
ProjectBox class.

A class for quickly construct a project box.

Call `finish` to retrieve the Obj3d of the final box.
"""


class ProjectBox:
    def __init__(
        self,
        size: list[float, float, float],
        rounding_radius: float = 2.0,
        segments: int = -1,
        wall: float = 2.0,
        bottom: str = "bevel",
    ):
        """
        Make a project box with the x, y, and z values given in size.

        The dimensions are for the INSIDE of the box.

        The INSIDE of the box will be placed at `(0, 0, 0)`.

        The `rounding_radius` determines the rounding size.

        For ``segments`` see the documentation of ``set_default_segments``.
        The segments value applies only to the segments in the rounded_rectangles that make up the box.
        Layer segments are determined by `config["LayerResolution"]`.

        By default (`bottom` is `"bevel"`), the box has a beveled (also called chamfered) bottom edge.
        Parameter `rounded_radius` will only be used in the x and y axes.
        This 3d prints better than a rounded edge.

        If `bottom` is `"round"` then a circular bottome edge is used.
        Parameter `rounded_radius` will only be used in the x, y and z axes, giving spherical corners.
        Note that in 3d printing rounded bottoms tend to not print well.
        One should consider printing with supports.

        If `bottom` is `"flat"` then a flat bottom of height `wall` is used.
        Parameter `rounded_radius` will only be used in the x and y axes.

        <iframe width="100%" height="220" src="examples/project_box.html"></iframe>
        """
        if segments == -1:
            segments = config["DefaultSegments"]
        _chkGE("segments", segments, 3)
        _chkV3("size", size)
        _chkGE("rounding_radius", rounding_radius, 2.0)
        _chkGE("wall", wall, 2.0)
        if wall > rounding_radius:
            raise ValidationError("Parameter 'wall' must be <= 'rounding_radius'.")
        self._segments = segments
        self._rr = rounding_radius
        self._size = size
        self.x, self.y, self.z = self._size
        self.wall = wall
        self._bottom = bottom
        self._unions = []
        self._differences = []
        self._differences.append(
            rounded_rectangle((self.x, self.y), self._rr, self._segments).extrude(
                self.z
            )
        )

    def finish(self) -> Obj3d:
        self._box = _project_box(
            self._size, self._rr, self._segments, self.wall, self._bottom
        )
        self._box = difference(self._box, *self._differences)
        if len(self._unions) > 0:
            self._box = union(self._box, *self._unions)
        return self._box

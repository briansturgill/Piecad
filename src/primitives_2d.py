"""
## Create 2D objects such as circles and retangles.
"""

import manifold3d as _m


from . import Obj2d, config, _chkGT, _chkGE, _chkV2, cos, sin


def circle(radius: float, segments: int = -1) -> Obj2d:
    """
    Make a circle of a given radius.

    For ``segments`` see the documentation of ``set_default_segments``.

    Circles are created with the center at `(0,0)`
    """
    if segments == -1:
        segments = config["DefaultSegments"]
    _chkGT("radius", radius, 0.0)
    _chkGE("segments", segments, 3)

    return Obj2d(_m.CrossSection.circle(radius, segments))


_unit_circles = {}


def ellipse(radii: list[float, float], segments: int = -1) -> Obj2d:
    """
    Make an ellipse with the given radii.

    For ``segments`` see the documentation of ``set_default_segments``.

    Ellipses are created with the center at `(0,0)`
    """
    if segments == -1:
        segments = config["DefaultSegments"]
    _chkV2("radii", radii)
    _chkGE("segments", segments, 3)

    if segments in _unit_circles:
        circ = _unit_circles[segments]
    else:
        circ = _m.CrossSection.circle(1, segments)
        _unit_circles[segments] = circ

    return Obj2d(circ.scale(radii))


import numpy as _np


def polygon(paths: list[list[float, float]]) -> Obj2d:
    """
    Create a polygon from a single or multiple closed paths of points.

    Paths must be wound CCW for contours (solid parts).
    Or be wound CW for holes.

    All paths (contrours and holes) must not intersect.
    """

    return Obj2d(_m.CrossSection(paths, _m.FillRule.EvenOdd))


def rectangle(size: list[float, float], center: bool = False) -> Obj2d:
    """
    Make a rectangle of a given size.

    By default, the bottom left corner of the rectangle will be at `(0,0)`.
    When `center` is `True` it will cause the rectangle to be centered at `(0,0)`.
    """
    if type(size) == float or type(size) == int:
        return square(size)
    _chkV2("size", size)

    return Obj2d(_m.CrossSection.square(size, center))


_arc_trig_vals_map = {}


def rounded_rectangle(
    size: list[float, float],
    rounding_radius: float = 0.2,
    segments: int = -1,
    center: bool = False,
) -> Obj2d:
    """
    Create a rectangle with rounded corners.

    The `rounded_rectangele` will have dimensions of `size` dimensions and with
    corners of `rounding_radius`.

    For ``segments`` see the documentation of ``set_default_segments``.
    Each corner will be given approximately 1/4 of segments.

    By default, the bottom left corner of the square will be at `(0,0)`.
    When `center` is `True` it will cause the square to be centered at `(0,0)`.
    """
    if segments == -1:
        segments = config["DefaultSegments"]
    _chkGE("segments", segments, 3)
    _chkV2("size", size)
    _chkGT("rounding_radius", rounding_radius, 0)

    segs_per_arc = segments // 4 + 1
    deg_per_arc = 90.0 / segs_per_arc
    pts = []
    x, y = size

    def make_arc_trig_vals(deg):
        end = deg + 90
        l = []
        for i in range(0, segs_per_arc - 1):
            l.append((cos(deg), sin(deg)))
            deg += deg_per_arc

        l.append((cos(end), sin(end)))
        return l

    if segments in _arc_trig_vals_map:
        arc_trig_vals = _arc_trig_vals_map[segments]
    else:
        arc_trig_vals = (
            make_arc_trig_vals(180),  # Bottom left
            make_arc_trig_vals(270),  # Bottom right
            make_arc_trig_vals(0),  # Top right
            make_arc_trig_vals(90),  # Top left
        )
        _arc_trig_vals_map[segments] = arc_trig_vals

    rr = rounding_radius

    pts = []
    c_x_off = -x / 2.0 if center else 0.0
    c_y_off = -y / 2.0 if center else 0.0

    def arc(tvals, rad, x_off, y_off):
        x_off += c_x_off
        y_off += c_y_off
        for c, s in tvals:
            pts.append((x_off + rad * c, y_off + rad * s))

    bl, br, tr, tl = arc_trig_vals
    arc(bl, rr, rr, rr)  # Bottom left
    arc(br, rr, x - rr, rr)  # Bottom right
    arc(tr, rr, x - rr, y - rr)  # Top right
    arc(tl, rr, rr, y - rr)  # Top left

    return Obj2d(_m.CrossSection([pts], _m.FillRule.EvenOdd))


def square(size: float, center: bool = False) -> Obj2d:
    """
    Make a square of a given size.

    By default, the bottom left corner of the square will be at `(0,0)`.
    When `center` is `True` it will cause the square to be centered at `(0,0)`.
    """
    if type(size) == list or type(size) == tuple:
        return rectangle(size)

    _chkGT("size", size, 0)

    return Obj2d(_m.CrossSection.square((size, size), center))


def star(
    num_points: int, outer_radius: float = 10.0, inner_radius: float = 0.0
) -> Obj2d:
    """
    Make a regular star of a given number of points.

    If `inner_radius` is `0.0` then it will be calculated based on outer_radius.

    Stars are created with the center at `(0,0)`.
    """
    pts = []
    deg_per_np = 360.0 / num_points
    ido = deg_per_np / 2.0  # inner_degree_offset

    if inner_radius == 0.0:
        ratio = cos(360.0 / num_points) / cos(180 / num_points)
        inner_radius = outer_radius * ratio

    deg = 90
    for i in range(0, num_points):
        pts.append((outer_radius * cos(deg), outer_radius * sin(deg)))
        pts.append((inner_radius * cos(deg + ido), inner_radius * sin(deg + ido)))
        deg += deg_per_np

    return Obj2d(_m.CrossSection([pts]))

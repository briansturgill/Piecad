"""
## Create 2D objects such as circles and retangles.
"""

import manifold3d as _m


from . import Obj2d, config, _chkGT, _chkGE, _chkV2, cos, sin, ValidationError

from ._poly_point_isect import (
    isect_segments_include_segments as _isect_segments_include_segments,
)


_unit_circles = {}


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

    if segments in _unit_circles:
        circ = _unit_circles[segments]
    else:
        circ = _m.CrossSection.circle(1, segments)
        _unit_circles[segments] = circ

    return Obj2d(circ.scale((radius, radius)))


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


def polygon(paths: list[list[tuple[float, float]]], check: bool = True) -> Obj2d:
    """
    Create a polygon from a single or multiple closed paths of points.

    Polygons follow the even/odd fill rule, meaning:
    * You can have multiple outer shapes.
    * Outer shapes can have holes.
    * Holes can have inner shapes.
    * Inner shapes can have holes
    * And so on.

    Holes can only occur inside a shape.
    A shape is either an outer shape or is inside a hole.

    Inside means fully contained inside. No intersections are allowed.

    By default we check if Clipper2 found a self-intersection.
    If it has, we issue a diagnostic message.
    The check takes about 40% more time, so in a heavily used
    situation, where you are absolutely sure you're not self-intersectiong,
    you can set `check` to 'False`.

    Be aware that if you set `check` to `False` that the underlying Clipper2
    library will attempt to "repair" any self-intersections.
    The "repair" is likely to cause a failed 3d print.
    (The "repair" is to emit two paths that overlap in one point, but
    are separate closed paths. These may get treated as two different objects
    that will be much too close together for 3d printing purposes.)

    If you understand winding, shapes are CCW, holes are CW.
    But Clipper2 automatically straightens it out for you.

    <iframe width="100%" height="280" src="examples/polygon.html"></iframe>
    """

    obj = Obj2d(_m.CrossSection(paths, _m.FillRule.EvenOdd))
    if check and len(obj.to_paths()) != len(paths):
        segments = []
        for path in paths:
            n = len(path)
            for i in range(0, n):
                segments.append((path[i], path[(i + 1) % n]))

        isects = _isect_segments_include_segments(segments)

        if len(isects) > 0:
            txt = []
            txt.append("ERROR: your polygon path(s) have self-intersection(s).\n")
            txt.append(
                "Intersections format: (Intersection_point, [(Segment1), (Segment2)])\n"
            )
            for isect in isects:
                txt.append(repr(isect) + "\n")
            raise ValidationError("".join(txt))
    return obj


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

    rr = rounding_radius
    circ = circle(rr, segments)

    x = size[0]
    y = size[1]

    c_x_off = -x / 2.0 if center else 0.0
    c_y_off = -y / 2.0 if center else 0.0

    return Obj2d(
        _m.CrossSection.batch_hull(
            [
                circ.translate((c_x_off + rr, c_y_off + rr)).mo,
                circ.translate((c_x_off + size[0] - rr, c_y_off + rr)).mo,
                circ.translate((c_x_off + size[0] - rr, c_y_off + size[1] - rr)).mo,
                circ.translate((c_x_off + rr, c_y_off + size[1] - rr)).mo,
            ]
        )
    )

    # segs_per_arc = segments // 4 + 1
    # deg_per_arc = 90.0 / segs_per_arc
    # pts = []
    # x, y = size

    # def make_arc_trig_vals(deg):
    #    end = deg + 90
    #    l = []
    #    for i in range(0, segs_per_arc - 1):
    #        l.append((cos(deg), sin(deg)))
    #        deg += deg_per_arc

    #    l.append((cos(end), sin(end)))
    #    return l

    # if segments in _arc_trig_vals_map:
    #    arc_trig_vals = _arc_trig_vals_map[segments]
    # else:
    #    arc_trig_vals = (
    #        make_arc_trig_vals(180),  # Bottom left
    #        make_arc_trig_vals(270),  # Bottom right
    #        make_arc_trig_vals(0),  # Top right
    #        make_arc_trig_vals(90),  # Top left
    #    )
    #    _arc_trig_vals_map[segments] = arc_trig_vals

    # rr = rounding_radius

    # pts = []
    # c_x_off = -x / 2.0 if center else 0.0
    # c_y_off = -y / 2.0 if center else 0.0

    # def arc(tvals, rad, x_off, y_off):
    #    x_off += c_x_off
    #    y_off += c_y_off
    #    for c, s in tvals:
    #        pts.append((x_off + rad * c, y_off + rad * s))

    # bl, br, tr, tl = arc_trig_vals
    # arc(bl, rr, rr, rr)  # Bottom left
    # arc(br, rr, x - rr, rr)  # Bottom right
    # arc(tr, rr, x - rr, y - rr)  # Top right
    # arc(tl, rr, rr, y - rr)  # Top left

    # return Obj2d(_m.CrossSection([pts], _m.FillRule.EvenOdd))


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


def star(num_points: int, outer_radius: float, inner_radius: float = 0.0) -> Obj2d:
    """
    Make a regular star of a given number of points.

    If `inner_radius` is `0.0` then it will be calculated based on outer_radius.

    Stars are created with the center at `(0,0)`.
    """
    _chkGE("num_points", num_points, 3)
    _chkGT("outer_radius", outer_radius, 0.0)
    _chkGE("inner_radius", inner_radius, 0.0)
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


import importlib

_module = None


def text_set_font(font_name: str):
    """
    Set the current font used by `text`.
    Fonts are stored in the `_package_name_/fonts` directory.
    Or you can use a full pathname to the `.ttf` file.
    Most OpenType/TrueType fonts can be used.

    Only one font can be in use at a time. (The previous font is automatically closed.)

    The default font is `Roboto-Regular.ttf`.
    Also available is `Hack-Regular.ttf` (Monospaced).
    """
    global _module
    if _module == None:
        _module = importlib.import_module("._text", "piecad")
    return _module._set_font(font_name)


def text(sz: float, tstr: str):
    """
    Draw the unicode printable characters in `tstr` in shapes of size `sz`.

    The default font is `Roboto-Regular.ttf`.
    Also available is `Hack-Regular.ttf` (Monospaced).
    """
    global _module
    if _module == None:
        _module = importlib.import_module("._text", "piecad")
    return _module._text_func(sz, tstr)

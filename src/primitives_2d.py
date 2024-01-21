"""
## Create 2D objects such as circles and retangles.

"""

import manifold3d as _m

from ._c import _chkGT, _chkTY, _chkGE, _chkV2

from . import *

from .trigonometry import cos, sin


_unit_circles = {}


def circle(radius: float, segments: int = -1) -> Obj2d:
    """
    Make a circle of a given radius.

    For ``segments`` see the documentation of ``set_default_segments``.

    """
    if segments == -1:
        segments = config["DefaultSegments"]
    _chkGT("radius", radius, 0)
    _chkGE("segments", segments, 3)

    if segments in _unit_circles:
        circ = _unit_circles[segments]
    else:
        circ = _m.CrossSection.circle(1, segments)
        _unit_circles[segments] = circ

    if radius == 1:
        return Obj2d(circ)
    return Obj2d(circ.scale((radius, radius)))


def rectangle(size: list[float, float]) -> Obj2d:
    """
    Make a rectangle of a given size.

    """
    if type(size) == float or type(size) == int:
        return square(size)
    _chkV2("size", size)

    return Obj2d(_m.CrossSection.square(size))


def rounded_rectangle(
    size: list[float, float], radius: float = 0.2, segments: int = -1
) -> Obj2d:
    """
    Create a rectangle with rounded corners.

    The `rounded_rectangele` will have dimensions of `size` dimensions and with
    corners of `radius`.

    For ``segments`` see the documentation of ``set_default_segments``.
    Each corner will be given approximately 1/4 of segments.
    """
    if segments == -1:
        segments = config["DefaultSegments"]
    _chkGE("segments", segments, 3)
    _chkV2("size", size)

    circ = circle(radius, segments)
    return hull(
        circ,
        circ.translate((10, 0)),
        circ.translate((0, 10)),
        circ.translate((10, 10)),
    )

    # Surprisingly, the code below is nearly three times slower than
    # using hull above.
    # segs_per_arc = segments // 4 + 1
    # deg_per_arc = 90.0 / segs_per_arc
    # pts = []
    # x, y = size

    # def arc(deg, rad, x_off, y_off):
    #    for i in range(0, segs_per_arc):
    #        pts.append((x_off + rad * cos(deg), y_off + rad * sin(deg)))
    #        deg += deg_per_arc

    # arc(180, radius, radius, radius)  # Bottom left
    # arc(270, radius, x - radius, radius)  # Bottom right
    # arc(0, radius, x - radius, y - radius)  # Top right
    # arc(90, radius, radius, y - radius)  # Top left

    # return Obj2d(_m.CrossSection([pts], _m.FillRule.EvenOdd))


def square(size: float) -> Obj2d:
    """
    Make a square of a given size.

    """
    if type(size) == list or type(size) == tuple:
        return rectangle(size)

    _chkGT("size", size, 0)

    return Obj2d(_m.CrossSection.square((size, size)))

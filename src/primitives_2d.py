"""
## Create 2D objects such as circles and retangles.

"""

import manifold3d as _m

from ._c import _chkGT, _chkTY, _chkGE, _chkV2

from . import *


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


def square(size: float) -> Obj2d:
    """
    Make a square of a given size.

    """
    if type(size) == list or type(size) == tuple:
        return rectangle(size)

    _chkGT("size", size, 0)

    return Obj2d(_m.CrossSection.square((size, size)))

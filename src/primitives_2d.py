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


def polygon(path_or_paths: list[float, float] | list[list[float, float]]) -> Obj2d:
    """
    Create a polygon from a single or multiple closed paths of points.

    Paths must be wound CCW for contours (solid parts).
    Or be wound CW for holes.

    All paths (contrours and holes) must not intersect.
    """
    ty = type(path_or_paths)
    if ty == list or ty == tuple or ty == _np.ndarray:
        ty = type(path_or_paths[0])
        if ty == list or ty == tuple or ty == _np.ndarray:
            ty = type(path_or_paths[0][0])
            if ty == list or ty == tuple or ty == _np.ndarray:
                return Obj2d(_m.CrossSection.create_from_paths_unchecked(path_or_paths))

    return Obj2d(_m.CrossSection.create_from_path_unchecked(path_or_paths))


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


_arc_bl = None
_arc_br = None
_arc_tr = None
_arc_tl = None


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

    return Obj2d(
        _m.CrossSection.rounded_rectangle(size, rounding_radius, segments, center)
    )


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

    return Obj2d(_m.CrossSection.create_from_path_unchecked(pts))

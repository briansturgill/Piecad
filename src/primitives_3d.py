"""
## Create 3D objects such as spheres and cubes.

"""

import manifold3d as _m
import trimesh

from ._c import _chkGT, _chkTY, _chkGE
from . import *


def cone(
    height: float, radius_low: float, radius_high: float = 0.2, segments: int = -1
) -> Obj3d:
    """
    Make a cone with given radii and height.

    For ``segments`` see the documentation of ``set_default_segments``.

    Why does ``radius_high`` not default to 0? Pointy things
    don't 3d print very well. If the model is not to be printed,
    by all means set it to 0.

    """
    if segments == -1:
        segments = config["DefaultSegments"]
    _chkGT("height", height, 0)
    _chkGT("radius_low", radius_low, 0)
    _chkGE("radius_high", radius_high, 0)
    _chkGE("segments", segments, 3)
    circ = circle(radius_low, segments)
    factor = radius_high / radius_low
    con = extrude(circ, height, 0, 0.0, factor, factor)
    return con  # con already Obj3d


def cube(size: float) -> Obj3d:
    """
    Make a cube of with sides of the given size.

    """
    if type(size) == list or type(size) == tuple:
        return cuboid(size)
    sq = square(size)
    cub = extrude(sq, size, 0, 0.0, 1.0, 1.0)
    return cub  # cub already Obj3d


def cuboid(size: list[float, float, float]) -> Obj3d:
    """
    Make a cuboid with the x, y, and z values given in size.

    """
    if type(size) == float or type(size) == int:
        return cube(size)
    x, y, z = size
    rect = rectangle([x, y])
    cub = extrude(rect, z, 0, 0.0, 1.0, 1.0)
    return cub  # cub already Obj3d


def cylinder(height: float, radius: float, segments: int = -1) -> Obj3d:
    """
    Make a cylinder of a given radius and height.

    For ``segments`` see the documentation of ``set_default_segments``.

    """
    if segments == -1:
        segments = config["DefaultSegments"]
    _chkGT("height", height, 0)
    _chkGT("radius", radius, 0)
    _chkGE("segments", segments, 3)
    circ = circle(radius, segments)
    cyl = extrude(circ, height, 0, 0.0, 1.0, 1.0)
    return cyl  # cyl already Obj3d


def extrude(
    obj: Obj2d,
    height: float,
    num_twist_divisions: int = 0,
    twist: float = 0,
    scale_x: float = 1.0,
    scale_y=1.0,
) -> Obj3d:
    """
    Create a Obj3d solid from Obj2d of given height.

    The 2d object will be copied and moved up to ``height``.
    Lines will be added creating an ``obj``-shaped 3d solid.

    Parameter ``num_twist_divisions`` should only be used when ``twist`` is
    greater than zero.

    Parameter `twist` will cause a circular rotation for each `num_twist_divisions`.

    Scale_x and scale_y is also applied at each division.

    Example:

        o2 = union(circle(4), circle(4).translate([-4, 4*2], circle(4).translate([4, 4*2])
        o3 = extrude(o2, 20, 40, 360/10, 1.2, 1.2)

    """
    _chkTY("obj", obj, Obj2d)
    _chkGT("height", height, 0)
    _chkGE("num_twist_divisions", num_twist_divisions, 0)
    _chkGE("twist", twist, 0)
    _chkGE("scale_x", scale_x, 0)
    _chkGE("scale_y", scale_y, 0)
    return Obj3d(
        _m.Manifold.extrude(
            obj.mo, height, num_twist_divisions, twist, (scale_x, scale_y)
        )
    )


def revolve(obj: Obj2d, segments: int = -1, revolve_degrees: float = 360.0) -> Obj3d:
    """
    LATER
    Create a Obj3d solid from Obj2d of given height.

    The 2d object will be copied and moved up to ``height``.
    Lines will be added creating an ``obj``-shaped 3d solid.

    Parameter ``segments`` is only used when ``twist`` is greater than zero
    For more on ``segments`` see the documentation of ``set_default_segments``.
    """
    if segments == -1:
        segments = config["DefaultSegments"]
    _chkTY("obj", obj, Obj2d)
    _chkGE("segments", segments, 3)
    _chkGT("revolve_degrees", revolve_degrees, 0)
    return Obj3d(_m.Manifold.revolve(obj.mo, segments, revolve_degrees))

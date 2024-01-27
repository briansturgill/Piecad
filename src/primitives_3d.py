"""
## Create 3D objects such as spheres and cubes.
<script type="module" src="https://ajax.googleapis.com/ajax/libs/model-viewer/3.4.0/model-viewer.min.js"></script>
"""

import manifold3d as _m
import trimesh

from . import *
from ._c import _chkGT, _chkTY, _chkGE


def cone(
    height: float, radius_low: float, radius_high: float = 0.2, segments: int = -1
) -> Obj3d:
    """
    Make a cone with given radii and height.

    For ``segments`` see the documentation of ``set_default_segments``.

    Why does ``radius_high`` not default to 0? Pointy things
    don't 3d print very well. If the model is not to be printed,
    by all means set it to 0.

    <iframe width="100%" height="220" src="examples/cone.html"></iframe>

    """
    if segments == -1:
        segments = config["DefaultSegments"]
    _chkGT("height", height, 0)
    _chkGT("radius_low", radius_low, 0)
    _chkGE("radius_high", radius_high, 0)
    _chkGE("segments", segments, 3)
    circ = circle(radius_low, segments)
    factor = radius_high / radius_low
    con = extrude_transforming(circ, height, 0, 0.0, factor, factor)
    return con  # con already Obj3d


def cube(size: float) -> Obj3d:
    """
    Make a cube of with sides of the given size.

    <iframe width="100%" height="220" src="examples/cube.html"></iframe>

    """
    if type(size) == list or type(size) == tuple:
        return cuboid(size)
    sq = square(size)
    cub = extrude(sq, size)
    return cub  # cub already Obj3d


def cuboid(size: list[float, float, float]) -> Obj3d:
    """
    Make a cuboid with the x, y, and z values given in size.

    <iframe width="100%" height="220" src="examples/cuboid.html"></iframe>

    """
    if type(size) == float or type(size) == int:
        return cube(size)
    x, y, z = size
    rect = rectangle([x, y])
    cub = extrude(rect, z)
    return cub  # cub already Obj3d


def cylinder(height: float, radius: float, segments: int = -1) -> Obj3d:
    """
    Make a cylinder of a given radius and height.

    For ``segments`` see the documentation of ``set_default_segments``.

    <iframe width="100%" height="220" src="examples/cylinder.html"></iframe>

    """
    if segments == -1:
        segments = config["DefaultSegments"]
    _chkGT("height", height, 0)
    _chkGT("radius", radius, 0)
    _chkGE("segments", segments, 3)
    circ = circle(radius, segments)
    cyl = extrude(circ, height)
    return cyl  # cyl already Obj3d


def extrude(obj: Obj2d, height: float) -> Obj3d:
    """
    Create a Obj3d solid from Obj2d of given height.

    The 2d object will be copied and moved up to ``height``.
    Lines will be added creating an ``obj``-shaped 3d solid.

    <iframe width="100%" height="220" src="examples/extrude.html"></iframe>

    """
    _chkTY("obj", obj, Obj2d)
    _chkGT("height", height, 0)
    return Obj3d(_m.Manifold.extrude(obj.mo, height))


def extrude_transforming(
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

    <iframe width="100%" height="250" src="examples/extrude_transforming.html"></iframe>

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


def geodesic_sphere(radius, segments=-1):
    """
    Create a geodesic sphere of a given radius.

    For ``segments`` see the documentation of ``set_default_segments``.

    <iframe width="100%" height="220" src="examples/geodesic_sphere.html"></iframe>

    """
    _chkGT("radius", radius, 0)
    _chkGE("radius", radius, 3)
    if segments == -1:
        segments = config["DefaultSegments"]

    sph = _m.Manifold.sphere(1, segments)

    if radius == 1:
        return Obj3d(sph)

    return Obj3d(sph.scale((radius, radius, radius)))


def revolve(obj: Obj2d, segments: int = -1, revolve_degrees: float = 360.0) -> Obj3d:
    """
    Create a Obj3d by revolving an Obj2d around the Y-axis, then rotating it so that Y becomes Z.

    For ``segments`` see the documentation of ``set_default_segments``.

    <iframe width="100%" height="220" src="examples/revolve.html"></iframe>

    """
    if segments == -1:
        segments = config["DefaultSegments"]
    _chkTY("obj", obj, Obj2d)
    _chkGE("segments", segments, 3)
    _chkGT("revolve_degrees", revolve_degrees, 0)
    return Obj3d(_m.Manifold.revolve(obj.mo, segments, revolve_degrees))


def sphere(radius, segments=-1):
    """
    Create a classical sphere of a given radius.

    For ``segments`` see the documentation of ``set_default_segments``.

    <iframe width="100%" height="220" src="examples/sphere.html"></iframe>

    """
    _chkGT("radius", radius, 0)
    _chkGE("radius", radius, 3)
    if segments == -1:
        segments = config["DefaultSegments"]

    circ = circle(1, segments).piecut(90, 270)
    sph = revolve(circ, segments=segments)

    if radius == 1:
        return sph

    return sph.scale((radius, radius, radius))

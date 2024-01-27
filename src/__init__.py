from __future__ import annotations
import manifold3d as _m
import piecad as _piecad

"""
"Easy as Pie" CAD (Piecad)

It is my opinionted view of what a good, simple CAD API should look like.

For many years I used [OpenSCAD](https://www.openscad.org),
but the functional language it uses was often a hinderance and its speed
was poor.

Piecad is based on [Manifold](https://github.com/elalish/manifold).
Manifold incorporates [Clipper2](https://github.com/AngusJohnson/Clipper2)
for 2D objects. It also uses
[`quickhull`](https://github.com/akuukka/quickhull) for 3d convex hulls.

"""

from ._c import _chkGT, _chkTY, _chkGE, _chkV2, _chkV3
from .validation_error import ValidationError


def version():
    "Piecad version"
    return "0.2.0"


class Obj3d:
    """
    Wrapper class for "Manifolds", which are 3D graphical objects.

    Attributes:
        mo The Manifold::Manifold object used by manifold3d.
    """

    def __init__(self, o: object, color=None):
        self.mo = o
        self._color = color

    def bounding_box(self):
        """
        Return the bounding box of this object.

        Return a tuple: (left, front, bottom, right, back, top) which represents
        a cuboid that would exactly contain this object.

        It can be broken up like this: `x1, y1, z1, x2, y2, z2 = obj.bounding_box()`
        """
        return self.mo.bounding_box()

    def color(self, cspec):
        """
        Assign the given color to this object.</summary>

        Parameters:

            The `color` parameter has 3 formats:

            *   A tuple of RGB color values, where each value is between
                0 and 255. Such as: `(255, 128, 0)`

            * A string beginning with "#" followed by 6 hex digits
                representing RGB. Such as "#FF00FF"
            * A string that is one of the basic or extended CSS color names.
              For a list of color names see: [Color keywords](https://www.w3.org/wiki/CSS/Properties/color/keywords)
        """
        return Obj3d(self.mo, _parse_color(cspec))

    def is_empty(self):
        """
        Is this object empty?

        """
        return self.mo.is_empty()

    def num_faces(self) -> int:
        """
        The number of faces in this object.

        This is useful in unit testing shapes.

        It is very difficult to check that a shape is correct, but knowing that a correct
        number of faces is present goes a long way to making sure things are healthy.
        """
        return self.mo.num_tri()

    def num_verts(self) -> int:
        """
        The number of vertices in this object.

        This is useful in unit testing shapes.

        It is very difficult to check that a shape is correct, but knowing that a correct
        number of vertices is present goes a long way to making sure things are healthy.
        """
        return self.mo.num_vert()

    def piecut(self, start_angle=0, end_angle=90) -> Obj3d:
        """
        Cut a wedge out of this object.

        It returns a copy of this object minus the wedge.

        """
        if end_angle < start_angle:
            end_angle = end_angle + 360.0
        x1, y1, z1, x2, y2, z2 = self.bounding_box()
        c_x = (x2 + x1) / 2.0
        c_y = (y2 + y1) / 2.0
        c_z = (z2 + z1) / 2.0
        rad = max(z2 - z1, x2 - x1, y2 - y1)  # Actually 2*rad which is good
        h = z2 - z1
        pts = []
        pts.append((rad * cos(start_angle), rad * sin(start_angle)))
        ang = 90 + start_angle
        while ang < end_angle:
            pts.append((rad * cos(ang), rad * sin(ang)))
            ang = ang + 90
        pts.append((rad * cos(end_angle), rad * sin(end_angle)))
        cutter = Obj3d(_m.Manifold.extrude(polygon(pts).mo, h)).translate(
            [c_x, c_y, c_z - (h / 2)]
        )
        return difference(self, cutter)

    def rotate(self, degrees: list[float, float, float]) -> Obj3d:
        """
        Rotate this object by the given degrees for each axis.

        """
        _chkV3("degrees", degrees)
        return Obj3d(self.mo.rotate(degrees), color=self._color)

    def scale(self, factors: list[float, float, float]) -> Obj3d:
        """
        Scale this object by the given factors.

        If you want no change, use `1.0`, that means 100% (thus unchanged).
        """
        _chkV3("factors", factors)
        return Obj3d(self.mo.scale(factors), color=self._color)

    def to_verts_and_faces(
        self,
    ) -> tuple(list(list[float, float, float]), list(list[int, int, int])):
        """
        Return a pair containg a list of vertices and a list of faces for this object.

        """
        mesh = self.mo.to_mesh()
        if mesh.vert_properties.shape[1] > 3:
            vertices = mesh.vert_properties[:, :3]
        else:
            vertices = mesh.vert_properties
        return (vertices, mesh.tri_verts)

    def translate(self, offsets: list[float, float, float]) -> Obj3d:
        """
        Translate (move) this object by the given offsets.
        """
        _chkV3("offsets", offsets)
        return Obj3d(self.mo.translate(offsets), color=self._color)


class Obj2d:
    """
    Wrapper class for "CrossSections", which are 2D graphical objects.

    Attributes:
        mo The Manifold::CrossSection object used by manifold3d.
    """

    def __init__(self, o: object, color=None):
        self.mo = o
        self._color = color

    def bounding_box(self):
        """
        Return the bounding box of this object.

        Return a tuple: (left, bottom, right, top) which represents
        a rectangle that would exactly contain this object.

        It can be broken up like this: `x1, y1, x2, y2 = obj.bounding_box()`
        """
        return self.mo.bounds()

    def color(self, cspec):
        """
        Assign the given color to this object.</summary>

        Parameters:

            The `color` parameter has 3 formats:

            *   A tuple of RGB color values, where each value is between
                0 and 255. Such as: `(255, 128, 0)`

            * A string beginning with "#" followed by 6 hex digits
                representing RGB. Such as "#FF00FF"
            * A string that is one of the basic or extended CSS color names.
              For a list of color names see: [Color keywords](https://www.w3.org/wiki/CSS/Properties/color/keywords)
        """
        return Obj2d(self.mo, _parse_color(cspec))

    def is_empty(self):
        """
        Is this object empty?

        """
        return self.mo.is_empty()

    def extrude(self, height: int):
        """
        LATER
        """
        return _piecad.extrude(self, height)

    def num_verts(self) -> int:
        """
        The number of vertices in this object.

        This is useful in unit testing shapes.

        It is very difficult to check that a shape is correct, but knowing that a correct
        number of vertices is present goes a long way to making sure things are healthy.
        """
        return self.mo.num_vert()

    def piecut(self, start_angle=0, end_angle=90) -> Obj2d:
        """
        Cut a wedge out of this object.

        It returns a copy of this object minus the wedge.

        """
        if end_angle < start_angle:
            end_angle = end_angle + 360.0
        x1, y1, x2, y2 = self.bounding_box()
        c_x = (x2 + x1) / 2.0
        c_y = (y2 + y1) / 2.0
        rad = max(x2 - x1, y2 - y1)  # Actually 2*rad which is good
        pts = []
        pts.append((rad * cos(start_angle) + c_x, rad * sin(start_angle) + c_y))
        ang = 90 + start_angle
        while ang < end_angle:
            pts.append((rad * cos(ang) + c_x, rad * sin(ang) + c_y))
            ang = ang + 90
        pts.append((rad * cos(end_angle) + c_x, rad * sin(end_angle) + c_y))
        cutter = polygon(pts)
        return difference(self, cutter)

    def revolve(self, segments: int = -1, revolve_degrees: float = 360.0):
        """
        Create a Obj3d by revolving this object around the Y-axis, then rotating it so that Y becomes Z.

        For ``segments`` see the documentation of ``set_default_segments``.

        """
        return _piecad.revolve(self, segments, revolve_degrees)

    def rotate(self, degrees: list[float, float]) -> Obj2d:
        """
        Rotate this object by the given degrees for each axis.

        """
        _chkV2("degrees", degrees)
        return Obj2d(self.mo.rotate(degrees), color=self._color)

    def scale(self, factors: list[float, float]) -> Obj2d:
        """
        Scale this object by the given factors.

        If you want no change, use `1.0`, that means 100% (thus unchanged).
        """
        _chkV2("factors", factors)
        return Obj2d(self.mo.scale(factors), color=self._color)

    def to_paths(self) -> list(list[float, float]):
        """
        Return a lists of paths, each of which is a list of vertices that make up this object.

        """
        return self.mo.to_polygons()

    def translate(self, offsets: list[float, float]) -> Obj2d:
        """
        Translate (move) this object by the given offsets.
        """
        _chkV2("offsets", offsets)
        return Obj2d(self.mo.translate(offsets), color=self._color)


config = {}
config["CADViewerEnabled"] = True
config["CADViewDoNotSendSaves"] = False
config["CADViewerHostAndPort"] = "127.0.0.1:8037"
config["LayerResolution"] = 0.1
config["DefaultSegments"] = 36
"""
LATER document -- get rid of set_default_segments?

"""

from .bulk_ops import *
from .primitives_2d import *
from .primitives_3d import *
from .trigonometry import *
from .utilities import *
from ._color import _parse_color


def set_default_segments(segments: int) -> None:
    """
    Set the default value for the number of circular segments to use.

    Functions that produce circular objects need to know how
    many segments should be used to draw the "circle".
    For example if you call the ``circle`` function with ``segments = 4``
    it will produce a square... in most cases undesirable, though
    a ``circle`` with ``segments = 6`` will produce a hexagon which
    can be useful.
    In most cases a higher number is desired as it produces objects
    that look truly round.
    I've never found a reason to use more than 100, and have chosen 36
    as being quite reasonable as a default.
    For finer work (I 3D print a lot), I find 50 is better.

    In circular functions, if the value passed in for ``segments`` is ``-1``, then
    the ``default_segments`` value is used. Thus circular functions have
    a default value for ``segments`` of ``-1``.
    """
    global _default_segments
    _c._chkGE("segments", segments, 3)
    config["DefaultSegments"] = segments

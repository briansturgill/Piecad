"""
"Easy as Pie" CAD (Piecad)

It is my opinionted view of what a good, simple CAD API should look like.

For many years I used [OpenSCAD](https://www.openscad.org),
but the functional language it uses was often a hinderance and its speed
was poor.

Piecad is based on [Manifold](https://github.com/elalish/manifold).
Manifold incorporates [Clipper2](https://github.com/AngusJohnson/Clipper2) for 2D objects.
It also uses [`quickhull`](https://github.com/akuukka/quickhull) for 3d convex hulls.
You can see Manifold's web site for other packages that are used.

Piecad also uses [isect_segments-bentley_ottmann](https://github.com/ideasman42/isect_segments-bentley_ottmann)
to check for polygon self intersections.

"""

from __future__ import annotations
import manifold3d as _m

__version__ = "1.0.0"


def version():
    "Piecad version"
    return __version__


class Obj3d:
    """
    Wrapper class for "Manifolds", which are 3D graphical objects.

    Attributes:
        mo The Manifold::Manifold object used by manifold3d.
    """

    def __init__(self, o: object = None, color=None):
        if o == None:
            o = _m.Manifold()
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

    def center(
        self,
        axes: tuple[bool, bool, bool] = (True, True, True),
        at: tuple[float, float, float] = (0, 0, 0),
    ):
        """
        Center the object on each of the `True` axes.

        Parameter `at` specifies the point to center on.

        """
        xmin, ymin, zmin, xmax, ymax, zmax = self.bounding_box()
        mid_x = (xmax - xmin) / 2 + xmin
        mid_y = (ymax - ymin) / 2 + ymin
        mid_z = (zmax - zmin) / 2 + zmin
        new_x = 0
        new_x = 0
        new_x = 0
        if axes[0]:
            new_x = at[0] - mid_x
        if axes[1]:
            new_y = at[0] - mid_y
        if axes[2]:
            new_z = at[0] - mid_z
        o3 = self.translate((new_x, new_y, new_z))
        o3._color = self._color
        return o3

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

    def decompose(self) -> list[Obj3d]:
        """
        Decompose this object into a list of topologically disjoint objects.

        """
        ml = self.mo.decompose()
        l = []
        for m in ml:
            l.append(Obj3d(m, color=self._color))
        return l

    def is_empty(self):
        """
        Is this object empty?

        """
        return self.mo.is_empty()

    def mirror(self, axes: tuple[bool, bool, bool]):
        """
        Mirror this object around the given axes.

        To understand this, pretend you are holding you right hand up in front of a mirror.
        Consider the hand in mirror the original image.
        Mirror over the x axis and you will get an image to the left that looks like a left hand.
        Mirror over the y axis and you will get an image like the back of the hand you are holding up.
        Mirror over the x and y axes and you will get an image like the back of a left hand.
        For the Z axis it's the same, but each hand is upside down.

        From a mathmatical standpoint, mirroring is negating all the points in each axis selected.

        """
        uv = [0, 0, 0]
        if axes[0]:
            uv[0] = 1
        if axes[1]:
            uv[1] = 1
        if axes[2]:
            uv[2] = 1
        return Obj3d(self.mo.mirror(uv), self._color)

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

    def piecut(
        self, start_angle=0, end_angle=90, both=False
    ) -> Obj3d | tuple[Obj3d, Obj3d]:
        """
        Cut a wedge out of this object.

        It returns a copy of this object minus the wedge.

        Or if `both` is `True` it returns a tuple of the object minus the wedge and the object intersected with the wedge.

        """
        if end_angle < start_angle:
            end_angle = end_angle + 360.0
        if end_angle - start_angle >= 360.0:
            raise ValidationError(
                "Parameters start_angle and end_angle must be less than 360 degrees apart."
            )
        x1, y1, z1, x2, y2, z2 = self.bounding_box()
        c_x = (x2 + x1) / 2.0
        c_y = (y2 + y1) / 2.0
        c_z = (z2 + z1) / 2.0
        rad = max(z2 - z1, x2 - x1, y2 - y1) * 4
        h = z2 - z1
        pts = []
        if end_angle - start_angle != 180.0:
            pts.append((c_x, c_y))
        pts.append((rad * cos(start_angle) + c_x, rad * sin(start_angle) + c_y))
        ang = 90 + start_angle
        while ang < end_angle:
            pts.append((rad * cos(ang) + c_x, rad * sin(ang) + c_y))
            ang = ang + 90
        pts.append((rad * cos(end_angle) + c_x, rad * sin(end_angle) + c_y))
        cutter = Obj3d(_m.Manifold.extrude(_m.CrossSection([pts]), h)).translate(
            (0, 0, z1)
        )
        if both:
            o1, o2 = self.split(cutter)
            o1._color = self._color
            o2._color = self._color
            return (o1, o2)
        o3 = difference(self, cutter)
        o3._color = self._color
        return o3

    def project(self) -> Obj2d:
        """
        Return a Obj2d representing this object's "shadow" on the x-y plane.

        """
        return Obj2d(self.mo.project(), color=self._color)

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

    def slice(self, height: float) -> Obj2d:
        """
        Like `project`, but a the given height.

        """
        _chkGT("height", height, 0)
        return Obj2d(self.mo.slice(height), color=self._color)

    def split(self, cutter: Obj3d) -> Obj3d:
        """
        This is like doing a difference and an intersect between this the cutter
        object simultaneously. It is faster than doing the two operations separately.

        Return is `(diff_obj, inter_obj)`.

        """
        ret = self.mo.split(cutter.mo)
        return (Obj3d(ret[0], color=self._color), Obj3d(ret[1], color=self._color))

    def surface_area(self) -> float:
        """
        The surface area of this Obj3d.
        """
        return self.mo.surface_area()

    def to_verts_and_faces(
        self,
    ) -> tuple[list[list[float, float, float]], list[list[int, int, int]]]:
        """
        Return a pair containg a list of vertices and a list of faces for this object.

        """
        mesh = self.mo.to_mesh()
        if mesh.vert_properties.shape[1] > 3:
            vertices = mesh.vert_properties[:, :3]
        else:
            vertices = mesh.vert_properties
        return (vertices, mesh.tri_verts)

    def transform(
        self,
        matrix3x4: tuple[
            tuple[float, float, float, float],
            tuple[float, float, float, float],
            tuple[float, float, float, float],
            tuple[float, float, float, float],
        ],
    ) -> Obj3d:
        """
        Transform this object with the given affine transformaton matrix.

        If you don't know what this is, you probably don't need it.
        """
        if (
            len(matrix3x4) != 3
            or len(matrix3x4[0]) != 4
            or len(matrix3x4[1]) != 4
            or len(matrix3x4[2]) != 4
        ):
            raise ValueError("Improperly sized 3x4 matrix.")

        return Obj3d(self.mo.transform(matrix3x4), color=self._color)

    def translate(self, offsets: list[float, float, float]) -> Obj3d:
        """
        Translate (move) this object by the given offsets.
        """
        _chkV3("offsets", offsets)
        return Obj3d(self.mo.translate(offsets), color=self._color)

    def volume(self) -> float:
        """
        The volume of this Obj3d.
        """
        return self.mo.volume()


class Obj2d:
    """
    Wrapper class for "CrossSections", which are 2D graphical objects.

    Attributes:
        mo The Manifold::CrossSection object used by manifold3d.
    """

    def __init__(self, o: object = None, color=None):
        if o == None:
            o = _m.CrossSection()
        self.mo = o
        self._color = color

    def area(self) -> float:
        """
        The area of this Obj2d.
        """
        return self.mo.area()

    def bounding_box(self):
        """
        Return the bounding box of this object.

        Return a tuple: (left, bottom, right, top) which represents
        a rectangle that would exactly contain this object.

        It can be broken up like this: `x1, y1, x2, y2 = obj.bounding_box()`
        """
        return self.mo.bounds()

    def center(
        self, axes: tuple[bool, bool] = (True, True), at: tuple[float, float] = (0, 0)
    ):
        """
        Center the object on each of the `True` axes.

        Parameter `at` specifies the point to center on.

        """
        xmin, ymin, xmax, ymax = self.bounding_box()
        mid_x = (xmax - xmin) / 2 + xmin
        mid_y = (ymax - ymin) / 2 + ymin
        new_x = 0
        new_x = 0
        new_x = 0
        if axes[0]:
            new_x = at[0] - mid_x
        if axes[1]:
            new_y = at[0] - mid_y
        o2 = self.translate((new_x, new_y))
        o2._color = self._color
        return o2

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

    def decompose(self) -> list[Obj2d]:
        """
        Decompose this object into a list of topologically disjoint objects.

        """
        ml = self.mo.decompose()
        l = []
        for m in ml:
            l.append(Obj2d(m, color=self._color))
        return l

    def is_empty(self):
        """
        Is this object empty?
        """
        return self.mo.is_empty()

    def extrude(self, height: int):
        """
        Extrude this object into a Obj3d of the given height.
        """
        o3 = Obj3d(_m.Manifold.extrude(self.mo, height))
        o3._color = self._color
        return o3

    def mirror(self, axes: tuple[bool, bool]):
        """
        Mirror this object around the given axes.

        To understand this, pretend you are holding you right hand up in front of a mirror.
        Consider the hand in mirror the original image, but flattened to 2D.
        Mirror over the x axis and you will get an image to the left that looks like a left hand.
        Mirror over the y axis and you will get an image of the right hand upside down.
        Mirror over the x and y axes and you will get an image a left hand upside down.

        From a mathmatical standpoint, mirroring is negating all the points in each axis selected.

        """
        uv = [0, 0]
        if axes[0]:
            uv[0] = 1
        if axes[1]:
            uv[1] = 1
        return Obj2d(self.mo.mirror(uv), self._color)

    def num_verts(self) -> int:
        """
        The number of vertices in this object.

        This is useful in unit testing shapes.

        It is very difficult to check that a shape is correct, but knowing that a correct
        number of vertices is present goes a long way to making sure things are healthy.
        """
        return self.mo.num_vert()

    def offset(
        self, delta: float, join_type: str, miter_limit: float = 2.0, segments: int = -1
    ) -> Obj2d:
        """
        Offset (or inset) a 2D object by a given distance called `delta`.
        A negative delta will cause an inset to be done.

        Select `join_type` from `"square"`, `"round"`, or `"miter"`.
        To understand `miter_limit`, see: [Clipper2 MiterLimit](https://www.angusj.com/clipper2/Docs/Units/Clipper.Offset/Classes/ClipperOffset/Properties/MiterLimit.htm)

        For ``segments`` see the documentation of ``set_default_segments``.

        """
        if segments == -1:
            segments = config["DefaultSegments"]
        _chkGE("segments", segments, 3)

        if join_type == "round":
            jt = _m.JoinType.Round
        elif join_type == "square":
            jt = _m.JoinType.Square
        elif join_type == "miter":
            jt = _m.JoinType.Miter
        else:
            raise ValidationError(
                'Invalid join type specified, must be one of: "round", "square", or "miter"'
            )
        o2 = Obj2d(self.mo.offset(delta, jt, miter_limit, segments))
        o2._color = self._color
        return o2

    def piecut(
        self, start_angle=0, end_angle=90, both=False
    ) -> Obj2d | tuple[Obj2d, Obj2d]:
        """
        Cut a wedge out of this object.

        It returns a copy of this object minus the wedge.

        Or if `both` is `True` it returns a tuple of the object minus the wedge and the object intersected with the wedge.
        """
        if end_angle < start_angle:
            end_angle = end_angle + 360.0
        x1, y1, x2, y2 = self.bounding_box()
        c_x = (x2 + x1) / 2.0
        c_y = (y2 + y1) / 2.0
        rad = max(x2 - x1, y2 - y1) * 4
        pts = []
        if end_angle - start_angle != 180.0:
            pts.append((c_x, c_y))
        pts.append((rad * cos(start_angle) + c_x, rad * sin(start_angle) + c_y))
        ang = 90 + start_angle
        while ang < end_angle:
            pts.append((rad * cos(ang) + c_x, rad * sin(ang) + c_y))
            ang = ang + 90
        pts.append((rad * cos(end_angle) + c_x, rad * sin(end_angle) + c_y))
        cutter = Obj2d(_m.CrossSection([pts]))
        o1 = difference(self, cutter)
        o1._color = self._color
        if both:
            o2 = intersect(self, cutter)
            o2._color = self._color
            return (o1, o2)
        return o1

    def revolve(self, revolve_degrees: float = 360.0, segments: int = -1):
        """
        Create a Obj3d by revolving this object around the Y-axis, then rotating it so that Y becomes Z.

        For ``segments`` see the documentation of ``set_default_segments``.
        """
        o3 = revolve(self, revolve_degrees, segments)
        o3._color = self._color
        return o3

    def rotate(self, degrees: float) -> Obj2d:
        """
        Rotate this object by the given degrees.

        """
        return Obj2d(self.mo.rotate(degrees), color=self._color)

    def scale(self, factors: list[float, float]) -> Obj2d:
        """
        Scale this object by the given factors.

        If you want no change, use `1.0`, that means 100% (thus unchanged).
        """
        _chkV2("factors", factors)
        return Obj2d(self.mo.scale(factors), color=self._color)

    def to_paths(self) -> list[list[float, float]]:
        """
        Return a lists of paths, each of which is a list of vertices that make up this object.
        """
        return self.mo.to_polygons()

    def transform(
        self, matrix2x3: tuple[tuple[float, float, float], tuple[float, float, float]]
    ) -> Obj3d:
        """
        Transform this object with the given affine transformaton matrix.

        If you don't know what this is, you probably don't need it.
        """
        if len(matrix2x3) != 2 or len(matrix2x3[0]) != 3 or len(matrix2x3[1]) != 3:
            raise ValueError("Improperly sized 2x3 matrix.")

        return Obj2d(self.mo.transform(matrix2x3), color=self._color)

    def translate(self, offsets: list[float, float]) -> Obj2d:
        """
        Translate (move) this object by the given offsets.
        """
        _chkV2("offsets", offsets)
        return Obj2d(self.mo.translate(offsets), color=self._color)


config = {}
config["CADViewerEnabled"] = True
config["CADViewerHostAndPort"] = "127.0.0.1:8037"
config["DefaultUnits"] = "mm"
config["LayerResolution"] = 0.1
config["DefaultSegments"] = 36
"""
Global Configuration Values

| :--- | :--- |
|CADViewerEnabled      | Use CADViewer if view is used.
|CADViewerHostAndPort  | Hostname_or_Address:Port used by CADViewer
|LayerResolution       | Resolution your output can be printed/made at.
|                      | If you have multiple resolutions, choose the smallest one.

```python
config["CADViewerEnabled"] = True
config["CADViewerHostAndPort"] = "127.0.0.1:8037"
config["LayerResolution"] = 0.1
```

This is just a Python dict, set them like the defaults shown above.

"""


def set_default_segments(segments: int = 36) -> None:
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

    The default value of `segments` 36.

    If you need a circular objects primary axes to have exact values (at the
    90 degree marks), chose a `segments` value that is a multiple of 4.

    In circular functions, if the value passed in for ``segments`` is ``-1``, then
    the ``default_segments`` value is used. Thus circular functions have
    a default value for ``segments`` of ``-1``.
    """
    global _default_segments
    _chkGE("segments", segments, 3)
    config["DefaultSegments"] = segments


def _chkGE(name: str, val: object, const: object):
    if val < const:
        raise ValidationError(
            f"Parameter {name} must be greater than or equal to {const}"
        )


def _chkGT(name: str, val: object, const: object):
    if val <= const:
        raise ValidationError(f"Parameter {name} must be greater than {const}")


def _chkTY(name: str, v1: object, v2: object):
    if type(v1) != v2:
        raise ValidationError(f"Parameter {name} must be of type {v1}")


def _chkV2(name: str, v1: object):
    if type(v1) != list and type(v1) != tuple:
        raise ValidationError(f"Parameter {name} must be of type list or tuple")
    if len(v1) != 2:
        raise ValidationError(f"Parameter {name} list/tuple must have length of 2.")


def _chkV3(name: str, v1: object):
    if type(v1) != list and type(v1) != tuple:
        raise ValidationError(f"Parameter {name} must be of type list or tuple")
    if len(v1) != 3:
        raise ValidationError(f"Parameter {name} list/tuple must have length of 3.")


def _chkGO(name: str, v1: object):
    ty = type(v1)
    if ty != Obj3d and ty != Obj2d:
        raise ValidationError(f"Parameter {name} must be of type, Obj2d or Obj3d")


def _chkGOTY(name: str, ty: object):
    if ty != Obj3d and ty != Obj2d:
        raise ValidationError(f"Parameter {name} must be of type, Obj2d or Obj3d")


class ValidationError(BaseException):
    """
    Exception class for errors detected in arguments to **piecad**
    functions and methods.
    """

    pass


from .utilities import *
from .bulk_ops import *
from .trigonometry import *
from .primitives_2d import *
from .primitives_3d import *
from ._color import _parse_color

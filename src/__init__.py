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


class Obj2d:
    """
    Wrapper class for "CrossSections", which are 2D graphical objects.

    Attributes:
        mo The Manifold::CrossSection object used by manifold3d.
    """

    def __init__(self, o: object, color=None):
        self.mo = o
        self._color = color

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


class ValidationError(BaseException):
    """
    Exception class for errors detected in arguments to **piecad**
    functions and methods.
    """

    pass


config = {}
config["CADViewerEnabled"] = True
config["CADViewDoNotSendSaves"] = False
config["CADViewerHostAndPort"] = "127.0.0.1:8037"
config["LayerResolution"] = 0.1
config["DefaultSegments"] = 36
"""
LATER document -- get rid of set_default_segments?

"""

from .primitives_2d import *
from .primitives_3d import *
from .trigonometry import *
from .utilities import *
from ._color import _parse_color
from ._c import _chkGT, _chkTY, _chkGE


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

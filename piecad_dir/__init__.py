"""
LATER document
"""


class Obj3d:
    """
    Wrapper class for "Manifolds", which are 3D graphical objects.
    """

    def __init__(self, o: object):
        self.v = o
        self.color = None


class Obj2d:
    """
    Wrapper class for "CrossSections", which are 2D graphical objects.
    """

    def __init__(self, o: object):
        self.v = o
        self.color = None


class FatalError(Exception):
    """
    Exception class for errors raised in **piecad**.
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

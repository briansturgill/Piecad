"""
## Create 2D objects such as circles and retangles.

"""

import manifold3d as _m

from ._c import _chkGT, _chkTY, _chkGE

from . import *


def circle(radius: float, segments: int = -1) -> Obj2d:
    """
    Make a circle of a given radius.

    For ``segments`` see the documentation of ``set_default_segments``.

    """
    if segments == -1:
        segments = config["DefaultSegments"]
    _chkGT("radius", radius, 0)
    _chkGE("segments", segments, 3)
    return Obj2d(_m.CrossSection.circle(radius, segments))

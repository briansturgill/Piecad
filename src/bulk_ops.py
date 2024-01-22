"""
## Miscellaneans bulk operations that work on multiple objects.

"""

import manifold3d as _m

from ._c import _chkGT, _chkTY, _chkGE, _chkV2

from . import *


def difference(*objs: Obj2d | Obj3d) -> Obj2d | Obj3d:
    """
    Returns the object removing the second through the last objects from the first object.

    In some packages this function might be called subtract
    """
    if len(objs) == 0:
        return _m.CrossSection()
    ty = type(objs[0])
    for o in objs:
        if type(o) != ty:
            raise ValidationError("Mixed types in parameter: objs.")
    if ty == Obj2d:
        l = []
        for o in objs:
            l.append(o.mo)
        return Obj2d(_m.CrossSection.batch_boolean(l, _m.OpType.Subtract))
    elif ty == Obj3d:
        l = []
        for o in objs:
            l.append(o.mo)
        return Obj3d(_m.Manifold.batch_boolean(l, _m.OpType.Subtract))
    else:
        raise ValidationError("All objects must be of one type, Obj2d or Obj3d")


def hull(*objs: Obj2d | Obj3d) -> Obj2d | Obj3d:
    """
    Return a convex hull of the given objects.

    All objects must be of the same type (Obj2d or Obj3d).

    The corresponding hull that is returned will be of the same type
    as the input objects.
    """
    if len(objs) == 0:
        return _m.CrossSection()
    ty = type(objs[0])
    for o in objs:
        if type(o) != ty:
            raise ValidationError("Mixed types in parameter: objs.")
    if ty == Obj2d:
        l = []
        for o in objs:
            l.append(o.mo)
        return Obj2d(_m.CrossSection.batch_hull(l))
    elif ty == Obj3d:
        l = []
        for o in objs:
            l.append(o.mo)
        return Obj3d(_m.Manifold.batch_hull(l))
    else:
        raise ValidationError("All objects must be of one type, Obj2d or Obj3d")

"""
## Miscellaneous bulk operations that work on multiple objects.
"""

import manifold3d as _m

from . import Obj2d, Obj3d, ValidationError, _chkGOTY


def compose(*objs: Obj2d | Obj3d) -> Obj2d | Obj3d:
    """
    Returns a single object containing all the disjoint objects.

    It is important that the objects not overlap.
    This is for making a scene of a group of objects that can be saved as a single model.

    If you want to combine two models into one model, see `union` below.

    See the `decompose` method on `Obj2d` and `Obj3d` for the inverse operation.

    """
    ty = type(objs[0])
    _chkGOTY("objs", ty)
    if len(objs) == 0:
        return Obj2d(_m.CrossSection()) if ty == Obj2d else Obj3d(_m.Manifold())
    for o in objs:
        if type(o) != ty:
            raise ValidationError("Mixed types in parameter: objs.")
    l = []
    for o in objs:
        l.append(o.mo)

    if ty == Obj2d:
        return Obj2d(_m.CrossSection.compose(l))
    else:
        return Obj3d(_m.Manifold.compose(l))


def difference(*objs: Obj2d | Obj3d) -> Obj2d | Obj3d:
    """
    Returns the object removing the second through the last objects from the first object.

    In some packages this function might be called subtract

    <iframe width="100%" height="250" src="examples/difference2d.html"></iframe>

    <iframe width="100%" height="250" src="examples/difference3d.html"></iframe>
    """
    ty = type(objs[0])
    _chkGOTY("objs", ty)
    if len(objs) == 0:
        return Obj2d(_m.CrossSection()) if ty == Obj2d else Obj3d(_m.Manifold())
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

    <iframe width="100%" height="250" src="examples/hull2d.html"></iframe>

    <iframe width="100%" height="250" src="examples/hull3d.html"></iframe>
    """
    ty = type(objs[0])
    _chkGOTY("objs", ty)
    if len(objs) == 0:
        return Obj2d(_m.CrossSection()) if ty == Obj2d else Obj3d(_m.Manifold())
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


def intersect(*objs: Obj2d | Obj3d) -> Obj2d | Obj3d:
    """
    Returns the object made by adding those portions that occur only in all `objs` together.

    <iframe width="100%" height="250" src="examples/intersect2d.html"></iframe>

    <iframe width="100%" height="250" src="examples/intersect3d.html"></iframe>
    """
    ty = type(objs[0])
    _chkGOTY("objs", ty)
    if len(objs) == 0:
        return Obj2d(_m.CrossSection()) if ty == Obj2d else Obj3d(_m.Manifold())
    for o in objs:
        if type(o) != ty:
            raise ValidationError("Mixed types in parameter: objs.")
    if ty == Obj2d:
        l = []
        for o in objs:
            l.append(o.mo)
        return Obj2d(_m.CrossSection.batch_boolean(l, _m.OpType.Intersect))
    elif ty == Obj3d:
        l = []
        for o in objs:
            l.append(o.mo)
        return Obj3d(_m.Manifold.batch_boolean(l, _m.OpType.Intersect))
    else:
        raise ValidationError("All objects must be of one type, Obj2d or Obj3d")


def union(*objs: Obj2d | Obj3d) -> Obj2d | Obj3d:
    """
    Returns the object made by adding all the `objs` together.

    <iframe width="100%" height="250" src="examples/union2d.html"></iframe>

    <iframe width="100%" height="250" src="examples/union3d.html"></iframe>
    """
    ty = type(objs[0])
    _chkGOTY("objs", ty)
    if len(objs) == 0:
        return Obj2d(_m.CrossSection()) if ty == Obj2d else Obj3d(_m.Manifold())
    for o in objs:
        if type(o) != ty:
            raise ValidationError("Mixed types in parameter: objs.")
    if ty == Obj2d:
        l = []
        for o in objs:
            l.append(o.mo)
        return Obj2d(_m.CrossSection.batch_boolean(l, _m.OpType.Add))
    elif ty == Obj3d:
        l = []
        for o in objs:
            l.append(o.mo)
        return Obj3d(_m.Manifold.batch_boolean(l, _m.OpType.Add))
    else:
        raise ValidationError("All objects must be of one type, Obj2d or Obj3d")

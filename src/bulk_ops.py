"""
## Miscellaneous bulk operations that work on multiple objects.

"""

import manifold3d as _m
import numpy as _np

from . import *
from ._c import _chkGT, _chkTY, _chkGE, _chkV2


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


def extrude_list(
    paths: list[float, Obj2d | tuple[Obj2d, Obj2d]], initial_z: float = 0.0
) -> Obj3d:
    """
    Extrude multiple Obj2d into a single Obj3d.

    ALL Obj2ds MUST HAVE THE NUMBER OF POINTS. (But, see Caps below.)

    Input list is a list of pairs: `[[height, Obj2d], ...]`.

    Caps:

        If `height` is zero then Obj2d is a cap.
        A cap is generated, the cap is differenced from the previous shape.
        This is the new previous shape and will determine the number of points needed in
        the following shapes.
        At least one extrusion must follow a cap.

        (Caps are automatically generated at the bottom and top of the extrusion.]

    """

    vertex_map = {}
    vertex_list = []

    def v(a):
        if a in vertex_map:
            return vertex_map[a]
        idx = len(vertex_list)
        vertex_list.append(a)
        vertex_map[a] = idx
        return idx

    triangles = []

    _chkGT("paths length", len(paths), 0)
    _chkGE("initial_z", initial_z, 0)
    if paths[0] == 0 or paths[-1] == 0:
        raise ValidationError("Caps cannnot be the first and/or last element of paths.")

    def add_cap(h, shape, top):
        poly = shape.mo.to_polygons()[0]

        tris = _m.triangulate([poly])
        for t in tris:
            i1, i2, i3 = t
            x1, y1 = poly[i1]
            x2, y2 = poly[i2]
            x3, y3 = poly[i3]
            if top:
                triangles.append(
                    (
                        v((x1, y1, h)),
                        v((x2, y2, h)),
                        v((x3, y3, h)),
                    )
                )
            else:  # Bottom caps are reversed.
                triangles.append(
                    (
                        v((x3, y3, h)),
                        v((x2, y2, h)),
                        v((x1, y1, h)),
                    )
                )

    cur_z = initial_z
    add_cap(cur_z, paths[0][1], top=False)
    last = len(paths)
    prev = paths[0][1]
    cur_idx = 0
    b = prev.mo.to_polygons()[0]

    while cur_idx < last:
        cur = paths[cur_idx][1]
        h = paths[cur_idx][0]

        if h == 0:  # A cap.
            add_cap(cur_z, cur, top=True)
            prev = difference(prev, cur)
            b = prev.to_polygons()[0]
            cur_idx += 1
            continue

        t = cur.mo.to_polygons()[0]
        bottom_p = v((b[0][0], b[0][1], cur_z))
        top_p = v((t[0][0], t[0][1], cur_z + h))

        _len = len(b)
        for i in range(0, _len):
            next_bottom_p = v((b[(i + 1) % _len][0], b[(i + 1) % _len][1], cur_z))
            next_top_p = v((t[(i + 1) % _len][0], t[(i + 1) % _len][1], cur_z + h))
            triangles.append((bottom_p, next_bottom_p, next_top_p))
            triangles.append((bottom_p, next_top_p, top_p))
            bottom_p = next_bottom_p
            top_p = next_top_p

        prev = cur
        b = t
        cur_z += h
        cur_idx += 1

    add_cap(cur_z, paths[-1][1], top=True)

    mesh = _m.Mesh(_np.array(vertex_list), _np.array(triangles))
    # import trimesh
    # mesh_output = trimesh.Trimesh(vertices=vertex_list, faces=triangles)
    # trimesh.exchange.export.export_mesh(mesh_output, "/home/brian/Downloads/mesh.stl", "stl")

    mo = _m.Manifold(mesh)
    if mo.is_empty():
        raise ValidationError(f"Error creating Manifold: {mo.status()}.")

    return Obj3d(mo)


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


def intersect(*objs: Obj2d | Obj3d) -> Obj2d | Obj3d:
    """
    Returns the object made by adding those portions that occur only in all `objs` together.

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
        return Obj2d(_m.CrossSection.batch_boolean(l, _m.OpType.Add))
    elif ty == Obj3d:
        l = []
        for o in objs:
            l.append(o.mo)
        return Obj3d(_m.Manifold.batch_boolean(l, _m.OpType.Add))
    else:
        raise ValidationError("All objects must be of one type, Obj2d or Obj3d")

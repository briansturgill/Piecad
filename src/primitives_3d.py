"""
## Create 3D objects such as spheres and cubes.
"""

import manifold3d as _m
import numpy as _np
import trimesh

from . import (
    config,
    Obj2d,
    Obj3d,
    circle,
    ValidationError,
    square,
    rectangle,
    difference,
)
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


def extrude_chaining(
    pairs: list[tuple[float, Obj2d]], initial_z: float = 0.0, use_ear_cut=True
) -> Obj3d:
    """
    Extrude multiple Obj2d into a single Obj3d.

    ALL Obj2ds MUST HAVE THE NUMBER OF POINTS. (But, see Caps below.)

    Input list is a list of pairs: `[[height, Obj2d], ...]`.

    Use `initial_z` if you want it extruded starting at a different z value.

    The parameter `use_ear_cut` set to `False` uses a much faster triangulation
    algoritm (called fan) which only works on a convex shape. If you don't
    understand what this means, leave this option alone.

    Caps:

        If `height` is zero then Obj2d is a partial cap.
        In other words, you want to make a hole.
        For manifold correctness reasons you need to cap the hole bottom.

        Once the cap is generated, the cap is differenced from the previous shape.
        This is the new previous shape and will determine the number of points needed in
        the following shapes.
        At least one extrusion must follow a cap.

        (Caps are automatically generated at the bottom and top of the extrusion.]

        If you have made a partial cap, you can extrude the differenced shape/cap
        with a pair: (height, None). This is so you don't have to do the 2d
        difference that was already done.

    <iframe width="100%" height="300" src="examples/extrude_chaining.html"></iframe>

    <iframe width="100%" height="300" src="examples/extrude_chaining_rr.html"></iframe>
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

    _chkGT("pairs length", len(pairs), 0)
    _chkGE("initial_z", initial_z, 0)
    if pairs[0][0] == 0 or pairs[-1][0] == 0:
        raise ValidationError("Caps cannnot be the first and/or last element of pairs.")

    def add_cap(h, shape, top):
        polys = shape.mo.to_polygons()

        if use_ear_cut or len(polys) != 1:
            vl = []
            for poly in polys:
                for vert in poly:
                    vl.append(vert)
            tris = _m.triangulate(polys)
            for t in tris:
                i1, i2, i3 = t
                x1, y1 = vl[i1]
                x2, y2 = vl[i2]
                x3, y3 = vl[i3]
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
        else:  # Fan triangulation
            poly = polys[0]  # We have only one to deal with
            n = len(poly)
            chosen = poly[0]
            for i in range(1, n - 1):
                cur = poly[i]
                next = poly[i + 1]
                if top:
                    triangles.append(
                        (
                            v((chosen[0], chosen[1], h)),
                            v((cur[0], cur[1], h)),
                            v((next[0], next[1], h)),
                        )
                    )
                else:  # Bottom caps are clockwise.
                    triangles.append(
                        (
                            v((next[0], next[1], h)),
                            v((cur[0], cur[1], h)),
                            v((chosen[0], chosen[1], h)),
                        )
                    )

    cur_z = initial_z
    add_cap(cur_z, pairs[0][1], top=False)
    last = len(pairs)
    prev = pairs[0][1]
    cur_idx = 0

    while cur_idx < last:
        cur = pairs[cur_idx][1]
        if cur == None:
            # This means to extrude the shape from the previous shape.
            # Usually this is done after a partial cap and you want
            # to extrude the difference done for the partial cap.
            cur = prev

        h = pairs[cur_idx][0]

        if h == 0:  # A partial cap.
            add_cap(cur_z, cur, top=True)
            prev = difference(prev, cur)
            cur_idx += 1
            continue

        prev_polys = prev.mo.to_polygons()
        cur_polys = cur.mo.to_polygons()
        for i in range(0, len(cur.mo.to_polygons())):
            b = prev_polys[i]
            t = cur_polys[i]
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
        cur_z += h
        cur_idx += 1

    add_cap(cur_z, cur, top=True)

    vertex_list = _np.array(vertex_list, _np.float32)
    triangles = _np.array(triangles, _np.int32)
    mesh = _m.Mesh(vertex_list, triangles)

    # import trimesh
    # mesh_output = trimesh.Trimesh(vertices=vertex_list, faces=triangles)
    # trimesh.exchange.export.export_mesh(mesh_output, "/home/brian/Downloads/mesh.obj", "obj")

    mo = _m.Manifold(mesh)
    if mo.is_empty():
        raise ValidationError(f"Error creating Manifold: {mo.status()}.")

    return Obj3d(mo)


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


def polyhedron(
    vertices: list[tuple[float, float, float]], faces: list[tuple[int, int, int]]
) -> Obj3d:
    """
    Create an Obj3d from points and a list of triangles using those points.

    This is an advanced function.

    If you don't already understand the "directions" below... really, try doing
    this another way.

    * Faces have to be wound counter-clockwise.

    * All faces must be triangles.

    * Faces are integer indices into the vertices list.

    You eventually will get a message from the Manifold package saying it is not "manifold".

    That isn't really helpful.

    Try adding these lines just before the call to polyhedron.

    ```python
    import trimesh
    mesh_output = trimesh.Trimesh(vertices=vertices, faces=triangles)
    trimesh.exchange.export.export_mesh(mesh_output, "mesh.obj", "obj")
    ```

    Then use a program like `meshlab` to look at where things are not manifold.

    """
    vertices = _np.array(vertices, _np.float32)
    triangles = _np.array(triangles, _np.int32)
    mesh = _m.Mesh(vertices, triangles)

    # import trimesh
    # mesh_output = trimesh.Trimesh(vertices=vertices, faces=triangles)
    # trimesh.exchange.export.export_mesh(mesh_output, "/home/brian/Downloads/mesh.obj", "obj")

    mo = _m.Manifold(mesh)
    if mo.is_empty():
        raise ValidationError(f"Error from the Manifold CAD package: {mo.status()}.")

    return Obj3d(mo)


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

    circ = circle(radius, segments).piecut(90, 270)
    sph = revolve(circ, segments=segments)

    if radius == 1:
        return sph

    return sph.scale((radius, radius, radius))

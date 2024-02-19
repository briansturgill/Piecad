"""
## Create 3D objects such as spheres and cubes.
"""

import manifold3d as _m
import math as _math
import numpy as _np

from . import (
    config,
    Obj2d,
    Obj3d,
    circle,
    ellipse,
    rounded_rectangle,
    cos,
    sin,
    ValidationError,
    difference,
    _chkGT,
    _chkTY,
    _chkGE,
    _chkV3,
    _chkV2,
)


def cone(
    height: float,
    radius_low: float,
    radius_high: float = 0.2,
    segments: int = -1,
    center: bool = False,
) -> Obj3d:
    """
    Make a cone with given radii and height.

    For ``segments`` see the documentation of ``set_default_segments``.

    Why does ``radius_high`` not default to 0? Pointy things
    don't 3d print very well. If the model is not to be printed,
    by all means set it to 0.

    By default, the cone bottom is centered at `(0,0,0)`.
    When `center` is `True`, the cone will be centered on `(0,0,0)`.
    (In other words, the bottom of the cone will be at `(0,0,-height/2.0`.)

    <iframe width="100%" height="220" src="examples/cone.html"></iframe>
    """
    if segments == -1:
        segments = config["DefaultSegments"]
    _chkGT("height", height, 0)
    _chkGT("radius_low", radius_low, 0)
    _chkGE("radius_high", radius_high, 0)
    _chkGE("segments", segments, 3)
    return Obj3d(
        _m.Manifold.cylinder(height, radius_low, radius_high, segments, center)
    )


def cube(size: float, center: bool = False) -> Obj3d:
    """
    Make a cube of with sides of the given size.

    By default, the bottom front left corner of the cube will be at `(0,0,0)`.
    When `center` is `True` it will cause the cube to be centered at `(0,0,0)`.

    """
    # Too many models on one page. <iframe width="100%" height="220" src="examples/cube.html"></iframe>
    if type(size) == list or type(size) == tuple:
        return cuboid(size, center)
    return Obj3d(_m.Manifold.cube((size, size, size), center))


def cuboid(size: list[float, float, float], center: bool = False) -> Obj3d:
    """
    Make a cuboid with the x, y, and z values given in size.

    By default, the bottom front left corner of the cuboid will be at `(0,0,0)`.
    When `center` is `True` it will cause the cube to be centered at `(0,0,0)`.

    """
    # Too many models on one page. <iframe width="100%" height="220" src="examples/cuboid.html"></iframe>
    if type(size) == float or type(size) == int:
        return cube(size)
    return Obj3d(_m.Manifold.cube(size, center))


def cylinder(height: float, radius: float, segments: int = -1, center=False) -> Obj3d:
    """
    Make a cylinder of a given radius and height.

    For ``segments`` see the documentation of ``set_default_segments``.

    By default, the cylinder bottom is centered at `(0,0,0)`.
    When `center` is `True`, the cylinder will centered on `(0,0,0)`.
    (In other words, the bottom of the cylinder will be at `(0,0,-height/2.0`.)
    """
    if segments == -1:
        segments = config["DefaultSegments"]
    _chkGT("height", height, 0)
    _chkGT("radius", radius, 0)
    _chkGE("segments", segments, 3)
    cyl = circle(radius, segments).extrude(height)
    if center:
        cyl = cyl.translate((0, 0, -height / 2.0))
    return cyl


def ellipsoid(
    radii: tuple[float, float, float], segments: int = -1, center=False
) -> Obj3d:
    """
    Make an ellipsoid which is elliptical on all three radii.

    For ``segments`` see the documentation of ``set_default_segments``.

    The ellipsoid is centered at `(0,0,0)`.

    <iframe width="100%" height="220" src="examples/ellipsoid.html"></iframe>
    """
    if segments == -1:
        segments = config["DefaultSegments"]
    _chkV3("radius", radii)
    _chkGE("segments", segments, 3)

    return sphere(1, segments=segments).scale(radii)


def elliptical_cylinder(
    height: float, radii: tuple[float, float], segments: int = -1, center=False
) -> Obj3d:
    """
    Make a elliptically shaped cylinder of given radii and height.

    For ``segments`` see the documentation of ``set_default_segments``.

    By default, the elliptical cylinder bottom is centered at `(0,0,0)`.
    When `center` is `True`, the cylinder will centered on `(0,0,0)`.
    (In other words, the bottom of the elliptical cylinder will be at `(0,0,-height/2.0`.)

    <iframe width="100%" height="220" src="examples/elliptical_cylinder.html"></iframe>
    """
    if segments == -1:
        segments = config["DefaultSegments"]
    _chkGT("height", height, 0)
    _chkV2("radii", radii)
    _chkGE("segments", segments, 3)

    ecyl = extrude(ellipse(radii, segments), height)
    if center:
        ecyl = ecyl.translate((0, 0, -height / 2.0))
    return ecyl


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
    pairs: list[tuple[float, Obj2d]], is_convex: bool = False
) -> Obj3d:
    """
    Extrude multiple 2d objects into a single 3d Object.

    ALL 2D OBJECTS MUST HAVE THE SAME NUMBER OF POINTS.

    Parameter `pairs` is a list of pairs: `[[height, Obj2d], ...]`.
    This list controls an extrusion of 2d shapes chained together
    into one 3d object.

    The `height` is cumulative. You are always specifing the exact current height
    to be output for the current object. This is done so that you can have numerically
    robust dimensions in your object. If relative heights were used, extuding something
    like a sphere is would end up with a sphere that's height was not precisely
    the desired height.

    If parameter `is_convex` is set to `True` a much faster triangulation
    algoritm is used, which only works on a convex shape. If you don't
    understand what this means, leave this option alone.

    Caps are automatically generated from the first and last shapes.

    <iframe width="100%" height="500" src="examples/extrude_chaining.html"></iframe>
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

    def add_cap(h, shape, top):
        polys = shape.mo.to_polygons()

        if not is_convex and len(polys) != 1:
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

    cur_z = pairs[0][0]
    add_cap(cur_z, pairs[0][1], top=False)
    last = len(pairs)
    prev = pairs[0][1]
    prev_z = cur_z
    cur_idx = 1

    while cur_idx < last:
        cur = pairs[cur_idx][1]
        cur_z = pairs[cur_idx][0]
        # if cur == None:
        # This means to extrude the shape from the previous shape.
        # Usually this is done after a partial cap and you want
        # to extrude the difference done for the partial cap.
        # cur = prev

        # if h == 0:  # A partial cap.
        #    add_cap(cur_z, cur, top=True)
        #    prev = difference(prev, cur)
        #    cur_idx += 1
        #    continue

        prev_polys = prev.mo.to_polygons()
        cur_polys = cur.mo.to_polygons()
        for i in range(0, len(cur.mo.to_polygons())):
            b = prev_polys[i]
            t = cur_polys[i]
            bottom_p = v((b[0][0], b[0][1], prev_z))
            top_p = v((t[0][0], t[0][1], cur_z))

            _len = len(b)
            for i in range(0, _len):
                next_bottom_p = v((b[(i + 1) % _len][0], b[(i + 1) % _len][1], prev_z))
                next_top_p = v((t[(i + 1) % _len][0], t[(i + 1) % _len][1], cur_z))
                triangles.append((bottom_p, next_bottom_p, next_top_p))
                triangles.append((bottom_p, next_top_p, top_p))
                bottom_p = next_bottom_p
                top_p = next_top_p
        prev = cur
        prev_z = cur_z
        cur_idx += 1

    add_cap(cur_z, cur, top=True)

    vertex_list = _np.array(vertex_list, _np.float32)
    triangles = _np.array(triangles, _np.uint32)
    mesh = _m.Mesh(vertex_list, triangles)
    # import trimesh
    # mesh_output = trimesh.Trimesh(vertices=vertex_list, faces=triangles)
    # trimesh.exchange.export.export_mesh(mesh_output, "/home/brian/Downloads/mesh.glb", "glb")
    # trimesh.exchange.export.export_mesh(mesh_output, "/home/brian/Downloads/mesh.stl", "stl")
    mo = _m.Manifold(mesh)
    if mo.is_empty():
        raise ValidationError(f"Error creating Manifold: {mo.status()}.")
    return Obj3d(mo)


def extrude_transforming(
    obj: Obj2d,
    height: float,
    num_twist_divisions: int = 0,
    twist: float = 0,
    scale: tuple[float, float] = (1.0, 1.0),
) -> Obj3d:
    """
    Create a Obj3d solid from Obj2d of given height.

    The 2d object will be copied and moved up to ``height``.
    Lines will be added creating an ``obj``-shaped 3d solid.

    Parameter ``num_twist_divisions`` should only be used when ``twist`` is
    greater than zero.

    Parameter `twist` will cause a circular rotation for each `num_twist_divisions`.

    Parammeter `scale` specifes scaling factors applied at each division.

    <iframe width="100%" height="270" src="examples/extrude_transforming.html"></iframe>
    """
    _chkTY("obj", obj, Obj2d)
    _chkGT("height", height, 0)
    _chkGE("num_twist_divisions", num_twist_divisions, 0)
    _chkGE("twist", twist, 0)
    _chkV2("scale", scale)
    return Obj3d(
        _m.Manifold.extrude(
            obj.mo,
            height,
            num_twist_divisions,
            twist,
            scale,
        )
    )


def geodesic_sphere(radius, segments=-1):
    """
    Create a geodesic sphere of a given radius.

    For ``segments`` see the documentation of ``set_default_segments``.

    <iframe width="100%" height="220" src="examples/geodesic_sphere.html"></iframe>
    """
    if segments == -1:
        segments = config["DefaultSegments"]
    _chkGT("radius", radius, 0)
    _chkGE("segments", segments, 3)

    return Obj3d(_m.Manifold.sphere(radius, segments))


def polyhedron(
    vertices: list[tuple[float, float, float]], faces: list[tuple[int, int, int]]
) -> Obj3d:
    """
    Create an Obj3d from points and a list of triangles using those points.

    THIS IS AN ADVANCED FUNCTION.

    If you don't already understand the "directions" below... REALLY, try doing
    what you want to do another way.

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
    faces = _np.array(faces, _np.uint32)
    mesh = _m.Mesh(vertices, faces)
    # import trimesh
    # mesh_output = trimesh.Trimesh(vertices=vertices, faces=faces)
    # trimesh.exchange.export.export_mesh(mesh_output, "/tmp/mesh.obj", "obj")
    mo = _m.Manifold(mesh)
    if mo.is_empty():
        raise ValidationError(f"Error creating Manifold: {mo.status()}.")
    return Obj3d(mo)


def project_box(
    size: list[float, float, float], rounding_radius: float = 2.0, segments: int = -1
) -> Obj3d:
    """
    Make a project box with the x, y, and z values given in size.

    The dimensions are for the INSIDE of the box.

    The INSIDE of the box will be placed at `(0, 0, 0)`.

    The `rounding_radius` determines the fillet size.

    For ``segments`` see the documentation of ``set_default_segments``.
    The segments value applies only to the segments in the rounded_rectangles that make up the box.
    Layer segments are determined by `config["LayerResolution"]`.

    <iframe width="100%" height="220" src="examples/project_box.html"></iframe>
    """
    if segments == -1:
        segments = config["DefaultSegments"]
    _chkGE("segments", segments, 3)
    _chkV3("size", size)
    _chkGE("rounding_radius", rounding_radius, 2.0)

    l = []
    res = config["LayerResolution"]
    arc_segs = rounding_radius / res
    deg_per_arc_seg = 90.0 / arc_segs
    deg = 0.0
    ix, iy, iz = size
    ox, oy, oz = size
    ox += rounding_radius * 2
    oy += rounding_radius * 2
    smallest_rr = rounding_radius + sin(deg_per_arc_seg) / 2.0
    l.append((-rounding_radius, rounded_rectangle((ix, iy), smallest_rr, segments)))
    deg += deg_per_arc_seg
    while deg < 90.0:
        delta = rounding_radius * sin(deg)
        cur_z = -rounding_radius * cos(deg)
        l.append(
            (
                cur_z,
                rounded_rectangle(
                    (ix + 2 * delta, iy + 2 * delta), rounding_radius + delta, segments
                ).translate((-delta, -delta)),
            )
        )
        deg += deg_per_arc_seg

    cur_z = 0.0
    l.append(
        (
            cur_z,
            rounded_rectangle(
                (ox, oy), rounding_radius + rounding_radius, segments
            ).translate((-rounding_radius, -rounding_radius)),
        )
    )

    cur_z = oz
    l.append(
        (
            cur_z,
            rounded_rectangle(
                (ox, oy), rounding_radius + rounding_radius, segments
            ).translate((-rounding_radius, -rounding_radius)),
        )
    )

    o = extrude_chaining(l, is_convex=True)
    io = rounded_rectangle((ix, iy), rounding_radius, segments).extrude(iz)
    return difference(o, io)


def pyramid(height: int, num_sides: int, radius: float) -> Obj3d:
    """
    Make a regular pyramid with the given height and number of sides.

    The `radius` specifies the circle on which the corners of the pyramid will be built.

    <iframe width="100%" height="220" src="examples/pyramid.html"></iframe>
    """
    return extrude_transforming(
        circle(radius, segments=num_sides), height=height, scale=(0, 0)
    )


def rounded_cuboid(
    size: list[float, float, float],
    rounding_radius=2.0,
    segments: int = -1,
    center: bool = False,
) -> Obj3d:
    """
    Make a rounded_cuboid with the x, y, and z values given in size.

    Parameter `rounding_radius` is the size of the rounded lip at top and bottom.

    For ``segments`` see the documentation of ``set_default_segments``.

    By default, the bottom front left corner of the rounded cuboid will be at `(0,0,0)`.
    When `center` is `True` it will cause the rounded cuboid to be centered at `(0,0,0)`.

    <iframe width="100%" height="220" src="examples/rounded_cuboid.html"></iframe>
    """
    if segments == -1:
        segments = config["DefaultSegments"]
    _chkGE("segments", segments, 3)
    _chkGE("rounding_radius", rounding_radius, 0)
    _chkV3("size", size)
    if type(size) == float or type(size) == int:
        size = (size, size, size)
    l = []
    res = config["LayerResolution"]
    arc_segs = rounding_radius / res
    deg_per_arc_seg = 90.0 / arc_segs
    deg = 0.0
    cur_z = 0
    x, y, z = size
    rr = rounding_radius
    ix = x - 2 * rr
    iy = y - 2 * rr
    smallest_rr = sin(deg_per_arc_seg) / 2.0
    l.append(
        (cur_z, rounded_rectangle((ix, iy), smallest_rr, segments).translate((rr, rr)))
    )
    deg += deg_per_arc_seg
    while deg < 90.0:
        delta = rr * sin(deg)
        cur_z = rr - rr * cos(deg)
        l.append(
            (
                cur_z,
                rounded_rectangle(
                    (ix + 2 * delta, iy + 2 * delta), delta, segments
                ).translate((rr - delta, rr - delta)),
            )
        )
        deg += deg_per_arc_seg

    cur_z = rr
    l.append((cur_z, rounded_rectangle((x, y), rr, segments)))

    cur_z = z - rr
    l.append((cur_z, rounded_rectangle((x, y), rr, segments)))

    deg = 90.0
    deg -= deg_per_arc_seg
    while deg > 0.0:
        delta = rr * sin(deg)
        cur_z = z - rr + rr * cos(deg)
        l.append(
            (
                cur_z,
                rounded_rectangle(
                    ((ix) + 2 * delta, (iy) + 2 * delta), delta, segments
                ).translate((rr - delta, rr - delta)),
            )
        )
        deg -= deg_per_arc_seg

    cur_z = z
    l.append(
        (cur_z, rounded_rectangle((ix, iy), smallest_rr, segments).translate((rr, rr)))
    )

    o = extrude_chaining(l, is_convex=True)
    if center:
        o = o.translate((-x / 2.0, -y / 2.0, -z / 2.0))
    return o


def rounded_cylinder(
    height: float,
    radius: float,
    rounding_radius: float = 2.0,
    segments: int = -1,
    center: bool = False,
) -> Obj3d:
    """
    Make a rounded cylinder of a given radius and height.

    Parameter `rounding_radius` is the size of the rounded lip at top and bottom.

    For ``segments`` see the documentation of ``set_default_segments``.

    By default, the rounded cylinder bottom is centered at `(0,0,0)`.
    When `center` is `True`, the rounded cylinder will centered on `(0,0,0)`.
    (In other words, the bottom of the rounded cylinder will be at `(0,0,-height/2.0`.)

    <iframe width="100%" height="220" src="examples/rounded_cylinder.html"></iframe>
    """
    if segments == -1:
        segments = config["DefaultSegments"]
    _chkGE("segments", segments, 3)
    _chkGT("radius", radius, 0)
    rr = (
        rounded_rectangle((2 * radius, height), rounding_radius, segments)
        .translate((-radius, 0))
        .piecut(90, 270)
    )
    o3 = revolve(rr, segments)
    if center:
        o3 = o3.translate((0, 0, -height / 2.0))
    return o3


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


def sphere(radius: float, segments: int = -1):
    """
    Create a classical sphere of a given radius.

    For ``segments`` see the documentation of ``set_default_segments``.

    <iframe width="100%" height="220" src="examples/sphere.html"></iframe>
    """
    if segments == -1:
        segments = config["DefaultSegments"]
    _chkGE("radius", radius, 0)
    _chkGE("segments", segments, 3)

    circ = circle(radius, 2 * segments).piecut(90, 270)

    return revolve(circ, segments=segments)


def torus(outer_radius: float, inner_radius: float, segments=-1):
    """
    Create a torus with the specified radii.

    For ``segments`` see the documentation of ``set_default_segments``.

    <iframe width="100%" height="220" src="examples/torus.html"></iframe>
    """
    if segments == -1:
        segments = config["DefaultSegments"]
    _chkGT("outer_radius", outer_radius, 0)
    _chkGT("inner_radius", inner_radius, 0)
    _chkGE("segments", segments, 3)
    if inner_radius >= outer_radius:
        raise ValidationError(
            "Parameter inner_radius must be smaller than outer_radius."
        )
    sz = (outer_radius - inner_radius) / 2.0
    circ = circle(sz, segments).translate((outer_radius - sz, outer_radius - sz))

    return revolve(circ, segments=segments).translate((0, 0, -outer_radius + sz))

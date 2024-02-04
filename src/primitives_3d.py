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
    rounded_rectangle,
    sin,
    ValidationError,
    difference,
    union,
    hull,
    _chkGT,
    _chkTY,
    _chkGE,
    _chkV3,
)


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
    return Obj3d(_m.Manifold.cylinder(height, radius_low, radius_high, segments))


def cube(size: float) -> Obj3d:
    """
    Make a cube of with sides of the given size.

    <iframe width="100%" height="220" src="examples/cube.html"></iframe>
    """
    if type(size) == list or type(size) == tuple:
        return cuboid(size)
    return Obj3d(_m.Manifold.cube((size, size, size)))


def cuboid(size: list[float, float, float]) -> Obj3d:
    """
    Make a cuboid with the x, y, and z values given in size.

    <iframe width="100%" height="220" src="examples/cuboid.html"></iframe>
    """
    if type(size) == float or type(size) == int:
        return cube(size)
    return Obj3d(_m.Manifold.cube(size))


def cylinder(height: float, radius: float, segments: int = -1, center=False) -> Obj3d:
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
    return extrude_simple(
        circle(radius, segments), height, height / 2.0 if center else 0, is_convex=True
    )


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
    pairs: list[tuple[float, Obj2d]], initial_z: float = 0.0, tri_alg="ec"
) -> Obj3d:
    """
    Extrude multiple Obj2d into a single Obj3d.

    ALL Obj2ds MUST HAVE THE NUMBER OF POINTS. (But, see Caps below.)

    Input list is a list of pairs: `[[height, Obj2d], ...]`.

    Use `initial_z` if you want it extruded starting at a different z value.

    The parameter `tri_alg` set to `fan` uses a much faster triangulation
    algoritm  which only works on a convex shape. If you don't
    understand what this means, leave this option alone.

    Caps:

        If `height` is zero then Obj2d is a full cap or a partial cap.
        Only the first cap, which must be at index 0, is a full cap.

        If you make a partial cap, you want to make a hole.
        For manifold correctness reasons you need to cap the hole bottom.

        Once the cap is generated, the cap is differenced from the previous shape.
        This is the new previous shape and will determine the number of points needed in
        the following shapes.
        At least one extrusion must follow a cap.

        (A cap is automatically generated at the top of the extrusion.]

        If you have made a partial cap, you can extrude the differenced shape/cap
        with a pair: (height, None). This is so you don't have to do the 2d
        difference that was already done.

    <iframe width="100%" height="320" src="examples/extrude_chaining.html"></iframe>
    <br>
    <iframe width="100%" height="330" src="examples/extrude_chaining_rr.html"></iframe>
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
    if pairs[0][0] != 0:
        raise ValidationError("The first element of pairs must be a cap.")
    if pairs[-1][0] == 0:
        raise ValidationError("The last element of pairs cannot be a cap.")

    def add_cap(h, shape, top):
        polys = shape.mo.to_polygons()

        if tri_alg == "ec" or len(polys) != 1:  # use EarCut
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
        elif tri_alg == "fan":  # Fan triangulation
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
        else:
            ValidationError(
                f"Invalid triangulation algorithm specified: {tri_alg}, must be one of: 'ec' or 'fan'"
            )

    cur_z = initial_z
    add_cap(cur_z, pairs[0][1], top=False)
    last = len(pairs)
    prev = pairs[0][1]
    cur_idx = 1

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


def extrude_simple(
    obj: Obj2d, height: float, initial_z: float = 0, is_convex=False
) -> Obj3d:
    """
    Create a Obj3d solid from Obj2d of given height.

    The 2d object will be copied and moved up to ``height``.
    Lines will be added creating an ``obj``-shaped 3d solid.

    If `initial_z` is not zero then it is added to the `0` z points and `height` z points.
    You can use `initial_z = -height/2.0` to cause the extrusion to be centered on `z == 0`.

    <iframe width="100%" height="220" src="examples/extrude.html"></iframe>
    """
    _chkTY("obj", obj, Obj2d)
    _chkGT("height", height, 0)
    return Obj3d(_m.Manifold.extrude_simple(obj.mo, height, initial_z, is_convex))


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
    faces = _np.array(faces, _np.int32)
    mesh = _m.Mesh(vertices, faces)

    # import trimesh
    # mesh_output = trimesh.Trimesh(vertices=vertices, faces=faces)
    # trimesh.exchange.export.export_mesh(mesh_output, "/home/brian/Downloads/mesh.obj", "obj")

    mo = _m.Manifold(mesh)
    if mo.is_empty():
        raise ValidationError(f"Error from the Manifold CAD package: {mo.status()}.")

    return Obj3d(mo)


def project_box(
    size: list[float, float, float], radius: float = 3.0, wall: float = 2.0
) -> Obj3d:
    """
    Make a project box with the x, y, and z values given in size.

    The dimensions are for the INSIDE of the box.

    The INSIDE of the box will be placed at `(0, 0, 0)`.

    The `radius` determines the fillet size.

    The `wall` is the thickness of the box walls.

    <iframe width="100%" height="220" src="examples/project_box.html"></iframe>
    """
    _chkV3("size", size)
    _chkGE("wall", wall, 2.0)
    _chkGE("radius", radius, 2.0)

    l = []
    res = config["LayerResolution"]
    arc_segs = radius / res
    deg_per_arc_seg = 90.0 / arc_segs
    d = 0.0
    end = -90.0
    ix, iy, iz = size
    ox, oy, oz = size
    layer_thickness = radius / arc_segs
    ox += wall * 2
    oy += wall * 2
    l.append((0, rounded_rectangle((ix, iy), radius)))
    d += deg_per_arc_seg
    while d < 89.9:
        delta = wall * sin(d)
        l.append(
            (
                layer_thickness,
                rounded_rectangle(
                    (ix + 2 * delta, iy + 2 * delta), radius + delta
                ).translate((-delta, -delta)),
            )
        )
        d += deg_per_arc_seg

    l.append(
        (
            layer_thickness,
            rounded_rectangle([ox, oy], radius + wall).translate((-wall, -wall)),
        )
    )
    l.append((0, l[0][1]))
    l.append((iz, None))

    return extrude_chaining(l, tri_alg="fan")


def pyramid(height: int, num_sides: int, radius: float) -> Obj3d:
    """
    Make a regular pyramid with the given height and number of sides.

    The `radius` specifies the circle on which the corners of the pyramid will be built.

    <iframe width="100%" height="220" src="examples/pyramid.html"></iframe>
    """
    return extrude_transforming(
        circle(radius, segments=num_sides), height=height, scale_x=0.0, scale_y=0.0
    )


def rounded_cuboid(
    size: list[float, float, float], rounding_radius=4.0, segments: int = -1
) -> Obj3d:
    """
    Make a rounded_cuboid with the x, y, and z values given in size.

    Parameter `rounding_radius` is the size of the rounded lip at top and bottom.

    For ``segments`` see the documentation of ``set_default_segments``.

    <iframe width="100%" height="220" src="examples/rounded_cuboid.html"></iframe>
    """
    if segments == -1:
        segments = config["DefaultSegments"]
    _chkGE("segments", segments, 3)
    _chkV3("size", size)
    if type(size) == float or type(size) == int:
        size = (size, size, size)
    x, y, z = size
    sph = sphere(rounding_radius)
    out = hull(
        sph.translate((rounding_radius, rounding_radius, 0)),
        sph.translate((x - rounding_radius, rounding_radius, 0)),
        sph.translate((x - rounding_radius, y - rounding_radius, 0)),
        sph.translate((rounding_radius, y - rounding_radius, 0)),
        sph.translate((rounding_radius, rounding_radius, z)),
        sph.translate((x - rounding_radius, rounding_radius, z)),
        sph.translate((x - rounding_radius, y - rounding_radius, z)),
        sph.translate((rounding_radius, y - rounding_radius, z)),
    )
    return out


def rounded_cylinder(
    height: float, radius: float, rounding_radius: float = 4.0, segments: int = -1
) -> Obj3d:
    """
    Make a rounded cylinder of a given radius and height.

    Parameter `rounding_radius` is the size of the rounded lip at top and bottom.

    For ``segments`` see the documentation of ``set_default_segments``.

    <iframe width="100%" height="220" src="examples/rounded_cylinder.html"></iframe>
    """
    if segments == -1:
        segments = config["DefaultSegments"]
    _chkGE("segments", segments, 3)
    _chkGT("radius", radius, 0)
    rr = (
        rounded_rectangle((2 * radius, height), rounding_radius, segments)
        .translate((-radius, -radius))
        .piecut(90, 270)
    )
    return revolve(rr, segments)


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
    _chkGT("radius", radius, 0)
    _chkGE("segments", segments, 3)

    circ = circle(radius, segments).piecut(90, 270)

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

    center_pt = outer_radius / 2.0 + inner_radius
    circ = circle(outer_radius - inner_radius, segments).translate(
        (center_pt, center_pt)
    )

    return revolve(circ, segments=segments)

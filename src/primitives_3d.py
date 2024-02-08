"""
## Create 3D objects such as spheres and cubes.
"""

import manifold3d as _m
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

    <iframe width="100%" height="220" src="examples/cylinder.html"></iframe>
    """
    if segments == -1:
        segments = config["DefaultSegments"]
    _chkGT("height", height, 0)
    _chkGT("radius", radius, 0)
    _chkGE("segments", segments, 3)
    return extrude_simple(
        circle(radius, segments),
        height,
        initial_z=-height / 2.0 if center else 0,
        is_convex=True,
    )


def extrude(obj: Obj2d, height: float, is_convex: bool = False) -> Obj3d:
    """
    Create a Obj3d solid from Obj2d of given height.

    The 2d object will be copied and moved up to ``height``.
    Lines will be added creating an ``obj``-shaped 3d solid.

    If parameter `is_convex` is set to `True` a much faster triangulation
    algoritm is used, which only works on a convex shape. If you don't

    <iframe width="100%" height="220" src="examples/extrude.html"></iframe>
    """
    _chkTY("obj", obj, Obj2d)
    _chkGT("height", height, 0)
    return Obj3d(_m.Manifold.extrude_simple(obj.mo, height, is_convex=False))


class ECType:
    """
    Defines the types of instructions allowed in an `extrude_chaining` tuple list.

    """

    Shape = _m.ECType.Shape
    FullCap = _m.ECType.FullCap
    PartialCap = _m.ECType.PartialCap


_emptyCS = _m.CrossSection()


def extrude_chaining(
    tuples: list[tuple[float, Obj2d]], is_convex: bool = False
) -> Obj3d:
    """
    Extrude multiple Obj2d into a single Obj3d.

    ALL Obj2ds MUST HAVE THE SAME NUMBER OF POINTS. (But, see Caps below.)

    Parameter `tuples` is a list of tuples: `[[height, Obj2d, ECType], ...]`.
    This list controls an extrusion, that includes holes.
    The list contains caps and shapes. Shapes are 2d objects.
    If the shape is `None, then the previous shape is used.

    The `height` is cumulative. You are always specifing the exact current height
    in the current object. This is done so that you can have numerically robust
    dimensions in your object. If relative heights were used, extuding something
    like a sphere is would end up with a sphere that's height was not precisely
    the desired height.

    Caps:

        There are two types, a full cap and a partial cap.

        Only the first and last caps, which must be at index 0 and len(tuples)-1, are a full cap.
        They simply enclose the object to meet the definition of manifold.

        If you make a partial cap, you want to make a hole.
        For manifold correctness reasons you need to cap the hole bottom.
        This cap is a partial cap.

        Once the cap is generated, the cap is differenced from the previous shape.
        This is the new previous shape and will determine the number of points needed in
        the following shapes.
        At least one extrusion must follow a cap.

        If you have made a partial cap, you can extrude the differenced shape/cap
        with a pair: (height, None). This is so you don't have to do the 2d
        difference that was already done.

    If parameter `is_convex` is set to `True` a much faster triangulation
    algoritm is used, which only works on a convex shape. If you don't
    understand what this means, leave this option alone.

    <iframe width="100%" height="360" src="examples/extrude_chaining.html"></iframe>
    """
    l = []
    idx = 0
    for h, obj, ty in tuples:
        if obj == None:
            l.append((h, _emptyCS, ty))
        else:
            if obj.is_empty():
                raise ValidationError(f"Object at index {idx} cannot be empty.")
            l.append((h, obj.mo, ty))
        idx += 1

    return Obj3d(_m.Manifold.extrude_chaining(l, is_convex))


def extrude_simple(
    obj: Obj2d, height: float, initial_z: float = 0, is_convex=False
) -> Obj3d:
    """
    Create a Obj3d solid from Obj2d of given height.

    The 2d object will be copied and moved up to ``height``.
    Lines will be added creating an ``obj``-shaped 3d solid.

    If `initial_z` is not zero then it is added to the `0` z points and `height` z points.
    You can use `initial_z = -height/2.0` to cause the extrusion to be centered on `z == 0`.

    If parameter `is_convex` is set to `True` a much faster triangulation
    algoritm is used, which only works on a convex shape. If you don't

    <iframe width="100%" height="220" src="examples/extrude_simple.html"></iframe>
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
    initial_z=0.0,
    is_convex=False,
) -> Obj3d:
    """
    Create a Obj3d solid from Obj2d of given height.

    The 2d object will be copied and moved up to ``height``.
    Lines will be added creating an ``obj``-shaped 3d solid.

    Parameter ``num_twist_divisions`` should only be used when ``twist`` is
    greater than zero.

    Parameter `twist` will cause a circular rotation for each `num_twist_divisions`.

    Scale_x and scale_y is also applied at each division.

    If `initial_z` is not zero then it is added to the `0` z points and `height` z points.
    You can use `initial_z = -height/2.0` to cause the extrusion to be centered on `z == 0`.

    If parameter `is_convex` is set to `True` a much faster triangulation
    algoritm is used, which only works on a convex shape. If you don't

    <iframe width="100%" height="270" src="examples/extrude_transforming.html"></iframe>
    """
    _chkTY("obj", obj, Obj2d)
    _chkGT("height", height, 0)
    _chkGE("num_twist_divisions", num_twist_divisions, 0)
    _chkGE("twist", twist, 0)
    _chkGE("scale_x", scale_x, 0)
    _chkGE("scale_y", scale_y, 0)
    return Obj3d(
        _m.Manifold.extrude_transforming(
            obj.mo,
            height,
            num_twist_divisions,
            twist,
            (scale_x, scale_y),
            initial_z,
            is_convex,
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

    # import trimesh
    # mesh_output = trimesh.Trimesh(vertices=vertices, faces=faces)
    # trimesh.exchange.export.export_mesh(mesh_output, "/home/brian/Downloads/mesh.obj", "obj")

    mo = _m.Manifold.create_from_verts_and_faces(vertices, faces)
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
    deg = 0.0
    end = -90.0
    ix, iy, iz = size
    ox, oy, oz = size
    layer_thickness = radius / arc_segs
    cur_z = -radius
    ox += wall * 2
    oy += wall * 2
    l.append((-radius, rounded_rectangle((ix, iy), radius), ECType.FullCap))
    deg += deg_per_arc_seg
    while deg < 89.9:
        delta = wall * sin(deg)
        l.append(
            (
                cur_z,
                rounded_rectangle(
                    (ix + 2 * delta, iy + 2 * delta), radius + delta
                ).translate((-delta, -delta)),
                ECType.Shape,
            )
        )
        deg += deg_per_arc_seg
        cur_z += layer_thickness

    cur_z = 0.0
    l.append(
        (
            cur_z,
            rounded_rectangle((ox, oy), radius + wall).translate((-wall, -wall)),
            ECType.Shape,
        )
    )

    l.append((cur_z, l[0][1], ECType.PartialCap))
    cur_z += iz
    l.append((cur_z, None, ECType.Shape))
    l.append((cur_z, None, ECType.FullCap))

    return extrude_chaining(l, is_convex=True)


def pyramid(height: int, num_sides: int, radius: float) -> Obj3d:
    """
    Make a regular pyramid with the given height and number of sides.

    The `radius` specifies the circle on which the corners of the pyramid will be built.

    <iframe width="100%" height="220" src="examples/pyramid.html"></iframe>
    """
    return extrude_transforming(
        circle(radius, segments=num_sides), height=height, scale_x=0, scale_y=0
    )


def rounded_cuboid(
    size: list[float, float, float],
    rounding_radius=4.0,
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
    _chkV3("size", size)
    if type(size) == float or type(size) == int:
        size = (size, size, size)
    x, y, z = size
    x_off = -x / 2.0 if center else 0.0
    y_off = -y / 2.0 if center else 0.0
    z_off = -z / 2.0 if center else 0.0
    sph = sphere(rounding_radius, segments=segments)
    out = hull(
        sph.translate(
            (rounding_radius + x_off, rounding_radius + y_off, rounding_radius + z_off)
        ),
        sph.translate(
            (
                x - rounding_radius + x_off,
                rounding_radius + y_off,
                rounding_radius + z_off,
            )
        ),
        sph.translate(
            (
                x - rounding_radius + x_off,
                y - rounding_radius + y_off,
                rounding_radius + z_off,
            )
        ),
        sph.translate(
            (
                rounding_radius + x_off,
                y - rounding_radius + y_off,
                rounding_radius + z_off,
            )
        ),
        sph.translate(
            (
                rounding_radius + x_off,
                rounding_radius + y_off,
                z - rounding_radius + z_off,
            )
        ),
        sph.translate(
            (
                x - rounding_radius + x_off,
                rounding_radius + y_off,
                z - rounding_radius + z_off,
            )
        ),
        sph.translate(
            (
                x - rounding_radius + x_off,
                y - rounding_radius + y_off,
                z - rounding_radius + z_off,
            )
        ),
        sph.translate(
            (
                rounding_radius + x_off,
                y - rounding_radius + y_off,
                z - rounding_radius + z_off,
            )
        ),
    )
    return out


def rounded_cylinder(
    height: float,
    radius: float,
    rounding_radius: float = 4.0,
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
    _chkGT("radius", radius, 0)
    _chkGE("segments", segments, 3)

    circ = circle(radius, segments * 2).piecut(90, 270)

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

    circ = circle(outer_radius - inner_radius, segments).translate(
        (inner_radius, outer_radius)
    )

    return revolve(circ, segments=segments).translate((0, 0, -outer_radius))

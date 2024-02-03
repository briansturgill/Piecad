import pytest
from piecad import *


def _sphere(r, s):
    o = sphere(r, s)
    o.num_verts()
    return o


def _polyhedron(v, f):
    o = polyhedron(v, f)
    o.num_verts()
    return o


def _geodesic_sphere(r, s):
    o = geodesic_sphere(r, s)
    o.num_verts()
    return o


def _cube(s):
    c = cube(s)
    c.num_verts()
    return c


def _cuboid(s):
    c = cube(s)
    c.num_verts()
    return c


def _project_box(s, rr):
    c = project_box(s, rr)
    c.num_verts()
    return c


def _rounded_cuboid(s, rr, segs):
    c = rounded_cuboid(s, rr, segs)
    c.num_verts()
    return c


def _cone(h, rl, rh, s):
    c = cone(h, rl, rh, s)
    c.num_verts()
    return c


def _cylinder(h, r, s, center):
    c = cylinder(h, r, s, center)
    c.num_verts()
    return c


def _rounded_cylinder(h, r, rr, s):
    c = rounded_cylinder(h, r, rr, s)
    c.num_verts()
    return c


def _extrude(o, h):
    o = extrude(o, h)
    o.num_verts()
    return o


def _extrude_simple(o, h, c):
    o = extrude_simple(o, h, is_convex=c)
    o.num_verts()
    return o


def _extrude_chaining(l, ta):
    o = extrude_chaining(l, tri_alg=ta)
    o.num_verts()
    return o


def test_cone_100(benchmark):
    c = benchmark(_cone, 25, 10, 10, 100)
    assert c.num_verts() == 200


def test_cylinder_100(benchmark):
    c = benchmark(_cylinder, 25, 10, 100, False)
    assert c.num_verts() == 200


def test_cylinder_100_centered(benchmark):
    c = benchmark(_cylinder, 25, 10, 100, True)
    assert c.num_verts() == 200


def test_cube(benchmark):
    c = benchmark(_cube, 20)
    assert c.num_verts() == 8


def test_cuboid(benchmark):
    c = benchmark(_cuboid, (15, 10, 36))
    assert c.num_verts() == 8


def test_rounded_cuboid(benchmark):
    c = benchmark(_rounded_cuboid, (15, 10, 36), 3.0, 100)
    assert c.num_verts() == 728


def test_project_box(benchmark):
    c = benchmark(_project_box, (15, 10, 36), 3.0)
    # 2560 uses bool3d, 1320 uses extrude_chaining
    assert c.num_verts() == 2560 or c.num_verts() == 1320


def test_rounded_cylinder_100(benchmark):
    c = benchmark(_rounded_cylinder, 25, 10, 4.0, 100)
    assert c.num_verts() == 5202


def test_extrude(benchmark):
    c = circle(100)
    o = benchmark(_extrude, c, 10)
    assert o.num_verts() == 72


def test_extrude_simple_ec(benchmark):
    c = circle(100)
    o = benchmark(_extrude_simple, c, 10, False)
    assert o.num_verts() == 72


def test_extrude_simple_fan(benchmark):
    c = circle(100)
    o = benchmark(_extrude_simple, c, 10, True)
    assert o.num_verts() == 72


def test_revolve():
    c = circle(10)
    assert revolve(c).num_verts() == 614


def test_sphere(benchmark):
    c = benchmark(_sphere, 10, 75)
    assert c.num_verts() == 2925


def test_geodesic_sphere(benchmark):
    c = benchmark(_geodesic_sphere, 10, 100)
    assert c.num_verts() == 2502
    assert c.num_faces() == 5000


def test_extrude_chaining_earcut(benchmark):
    c = circle(100)
    o = benchmark(_extrude_chaining, [(0, c), (10, None)], "ec")
    assert o.num_verts() == 72


def test_extrude_chaining_fan(benchmark):
    c = circle(100)
    o = benchmark(_extrude_chaining, [(0, c), (10, None)], "fan")
    assert o.num_verts() == 72


def _sphere_from_chaining(radius, segs):
    deg_per_seg = 180.0 / segs
    hs = (3.14 * radius) / segs
    l = []
    l.append((0, circle(radius, segs)))
    for i in range(1, segs):
        factor = sin(i * deg_per_seg)
        r = radius * factor
        h = hs * factor
        l.append((h, circle(r, segs)))

    out = extrude_chaining(l, tri_alg="fan")
    return out


def test_sphere_from_chaining(benchmark):
    c = benchmark(_sphere_from_chaining, 10, 50)
    assert c.num_verts() == 2500


def test_cube_from_polyhedron(benchmark):
    w = 10.0
    d = 10.0
    h = 10.0
    vertices = [
        (0.0, 0.0, 0.0),
        (0.0, 0.0, h),
        (0.0, d, 0.0),
        (0.0, d, h),
        (w, 0.0, 0.0),
        (w, 0.0, h),
        (w, d, 0),
        (w, d, h),
    ]
    faces = [
        (1, 0, 4),
        (2, 4, 0),
        (1, 3, 0),
        (3, 1, 5),
        (3, 2, 0),
        (3, 7, 2),
        (5, 4, 6),
        (5, 1, 4),
        (6, 4, 2),
        (7, 6, 2),
        (7, 3, 5),
        (7, 5, 6),
    ]
    out = benchmark(_polyhedron, vertices, faces)
    assert out.num_verts() == 8


def _project_box_bool3d(
    size: list[float, float, float], radius: float = 3.0, wall: float = 2.0
) -> Obj3d:
    l = []
    x, y, z = size
    res = config["LayerResolution"]
    arc_segs = radius / res
    deg_per_arc_seg = 90.0 / arc_segs
    d = 0.0
    layer_thickness = radius / arc_segs

    l.append(rounded_rectangle((x, y), radius).extrude(layer_thickness))
    layer_idx = 0
    d += deg_per_arc_seg
    while d < 89.9:
        layer_idx += 1
        delta = wall * sin(d)
        l.append(
            rounded_rectangle((x + 2 * delta, y + 2 * delta), radius + delta)
            .extrude(layer_thickness)
            .translate((-delta, -delta, layer_thickness * layer_idx))
        )
        d += deg_per_arc_seg

    l.append(
        rounded_rectangle([x + 2 * wall, y + 2 * wall], radius + wall)
        .extrude(z)
        .translate((-wall, -wall, radius))
    )

    outside = union(*l)
    inside = rounded_rectangle((x, y), radius).extrude(z).translate((0, 0, radius))
    box = difference(outside, inside)
    box.num_verts()

    return box


def test_project_box_bool3d(benchmark):
    c = benchmark(_project_box_bool3d, (15, 10, 36), 3.0)
    # 2560 uses bool3d, 1320 uses extrude_chaining
    assert c.num_verts() == 2560 or c.num_verts() == 1320

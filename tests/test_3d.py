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


def _cone(h, rl, rh, s):
    c = cone(h, rl, rh, s)
    c.num_verts()
    return c


def _cylinder(h, r, s):
    c = cylinder(h, r, s)
    c.num_verts()
    return c


def _extrude(o, h):
    o = extrude(o, h)
    o.num_verts()
    return o


def _extrude_chaining(l, ta):
    o = extrude_chaining(l, tri_alg=ta)
    print(o.num_verts())
    return o


def test_cone_100(benchmark):
    c = benchmark(_cone, 15, 10, 10, 100)
    assert c.num_verts() == 200


def test_cylinder_100(benchmark):
    c = benchmark(_cylinder, 15, 10, 100)
    assert c.num_verts() == 200


def test_cube(benchmark):
    c = benchmark(_cube, 20)
    assert c.num_verts() == 8


def test_cuboid(benchmark):
    c = benchmark(_cuboid, (15, 10, 36))
    assert c.num_verts() == 8


def test_extrude(benchmark):
    c = circle(100)
    o = benchmark(_extrude, c, 10)
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
    o = benchmark(_extrude_chaining, [(10, c)], "ec")
    assert o.num_verts() == 72


def test_extrude_chaining_fan(benchmark):
    c = circle(100)
    o = benchmark(_extrude_chaining, [(10, c)], "fan")
    assert o.num_verts() == 72


def _sphere_from_chaining(radius, segs):
    deg_per_seg = 180.0 / segs
    hs = (3.14 * radius) / segs
    l = []
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

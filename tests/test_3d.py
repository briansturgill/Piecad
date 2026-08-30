import pytest
from piecad import *


def _tetrahedron(verts):
    if verts == None:
        o = tetrahedron()
    else:
        o = tetrahedron(verts)
    o.num_verts()
    return o


def _torus(_or, ir, segs):
    o = torus(_or, ir, segs)
    o.num_verts()
    return o


def _pyramid(h, s, r):
    o = pyramid(h, s, r)
    o.num_verts()
    return o


def _sphere(r, s):
    o = sphere(r, s)
    o.num_verts()
    return o


def _geodesic_sphere(r, s):
    o = geodesic_sphere(r, s)
    o.num_verts()
    return o


def _cube(s, c=False):
    c = cube(s, c)
    c.num_verts()
    return c


def _cuboid(s, c=False):
    c = cuboid(s, c)
    c.num_verts()
    return c


def _rounded_cuboid(s, rr, segs, c=False):
    c = rounded_cuboid(s, rr, segs, c)
    c.num_verts()
    return c


def _cone(h, rl, rh, s, c=False):
    c = cone(h, rl, rh, s, c)
    c.num_verts()
    return c


def _cylinder(h, r, s, center):
    c = cylinder(h, r, s, center)
    c.num_verts()
    return c


def _rounded_cylinder(h, r, rr, s, c=False):
    c = rounded_cylinder(h, r, rr, s, c)
    c.num_verts()
    return c


def _extrude(o, h):
    o = extrude(o, h)
    o.num_verts()
    return o


def _extrude_chaining(l, is_convex):
    o = extrude_chaining(l, is_convex=is_convex)
    o.num_verts()
    return o


def test_cone_100(benchmark):
    c = benchmark(_cone, 25, 10, 10, 100)
    assert c.num_verts() == 200
    assert c.bounding_box() == (-10, -10, 0, 10, 10, 25)


def test_cone_100_center(benchmark):
    c = benchmark(_cone, 25, 10, 10, 100, True)
    assert c.num_verts() == 200
    assert c.bounding_box() == (-10, -10, -12.5, 10, 10, 12.5)


def test_cylinder_100(benchmark):
    c = benchmark(_cylinder, 25, 10, 100, False)
    assert c.num_verts() == 200
    assert c.bounding_box() == (-10, -10, 0, 10, 10, 25)


def test_cylinder_100_centered(benchmark):
    c = benchmark(_cylinder, 25, 10, 100, True)
    assert c.num_verts() == 200
    assert c.bounding_box() == (-10, -10, -12.5, 10, 10, 12.5)


def test_cube(benchmark):
    c = benchmark(_cube, 20)
    assert c.num_verts() == 8
    assert c.bounding_box() == (0, 0, 0, 20, 20, 20)


def test_cube_centered(benchmark):
    c = benchmark(_cube, 20, True)
    assert c.num_verts() == 8
    assert c.bounding_box() == (-10, -10, -10, 10, 10, 10)


def test_cuboid(benchmark):
    c = benchmark(_cuboid, (15, 10, 36))
    assert c.num_verts() == 8
    assert c.bounding_box() == (0, 0, 0, 15, 10, 36)
    assert c.volume() == pytest.approx(5400.0)
    assert c.surface_area() == pytest.approx(2100.0)


def test_cuboid_centered(benchmark):
    c = benchmark(_cuboid, (15, 10, 36), True)
    assert c.num_verts() == 8
    assert c.bounding_box() == (-7.5, -5, -18, 7.5, 5, 18)


def test_rounded_cuboid(benchmark):
    c = benchmark(_rounded_cuboid, (15, 10, 36), 3.0, 100)
    assert c.num_verts() == 6448
    assert c.bounding_box() == (0, 0, 0, 15, 10, 36)


def test_rounded_cuboid_centered(benchmark):
    c = benchmark(_rounded_cuboid, (15, 10, 36), 3.0, 100, True)
    assert c.num_verts() == 6448
    assert c.bounding_box() == (-7.5, -5, -18, 7.5, 5, 18)


def test_rounded_cylinder_100(benchmark):
    c = benchmark(_rounded_cylinder, 25, 10, 4.0, 100, False)
    assert c.num_verts() == 5202
    assert c.bounding_box() == (-10, -10, 0, 10, 10, 25)


def test_rounded_cylinder_100_centered(benchmark):
    c = benchmark(_rounded_cylinder, 25, 10, 4.0, 100, True)
    assert c.num_verts() == 5202
    assert c.bounding_box() == (-10, -10, -12.5, 10, 10, 12.5)


def test_extrude(benchmark):
    c = circle(10, 100)
    o = benchmark(_extrude, c, 25)
    assert o.num_verts() == 200


def test_revolve():
    c = circle(10)
    assert revolve(c).num_verts() == 616


def test_torus(benchmark):
    o = benchmark(_torus, 10, 6, 360 // 6)
    assert o.num_verts() == 3600
    assert o.bounding_box() == (-10, -10, -2, 10, 10, 2)


def test_pyramid(benchmark):
    o = benchmark(_pyramid, 10, 4, 4.0)
    assert o.num_verts() == 5
    assert o.bounding_box() == (-4, -4, 0, 4, 4, 10)


def test_sphere(benchmark):
    c = benchmark(_sphere, 10, 360 // 6)
    assert c.num_verts() == 3542
    assert c.bounding_box() == (-10, -10, -10, 10, 10, 10)


def test_geodesic_sphere(benchmark):
    c = benchmark(_geodesic_sphere, 10, 360 // 3)
    assert c.num_verts() == 3602
    assert c.bounding_box() == (-10, -10, -10, 10, 10, 10)


def test_extrude_chaining_earcut(benchmark):
    c = circle(10, 100)
    o = benchmark(
        _extrude_chaining,
        [(0, c), (25, c)],
        is_convex=False,
    )
    assert o.num_verts() == 200


def test_extrude_chaining_fan(benchmark):
    c = circle(10, 100)
    o = benchmark(
        _extrude_chaining,
        [(0, c), (25, c)],
        is_convex=True,
    )
    assert o.num_verts() == 200


def test_tetrahedron(benchmark):
    # A set of 4 arbitrary points
    p = [[1, 2, 3], [4, 5, 1], [2, 7, 4], [5, 3, 6]]

    # Test all permutations of the 4 points
    from itertools import permutations

    oM = tetrahedron(p)

    for i, perm in enumerate(permutations(p)):
        # print(f"\nPermutation {i+1}: {perm}")
        o = tetrahedron([perm[0], perm[1], perm[2], perm[3]])
        assert o.bounding_box() == oM.bounding_box()
        assert o.volume() == oM.volume()

    o = tetrahedron(None)
    assert o.bounding_box() == (-1.0, -1.0, -1.0, 1.0, 1.0, 1.0)
    assert o.volume() == 2.6666666666666665

    o = benchmark(_tetrahedron, 5)
    assert o.bounding_box() == (-5.0, -5.0, -5.0, 5.0, 5.0, 5.0)
    assert o.volume() == 333.3333333333333

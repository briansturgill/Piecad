import pytest
from piecad import *


def _difference(o1, o2):
    o = difference(o1, o2)
    o.num_verts()
    return o


def _intersect(o1, o2):
    o = intersect(o1, o2)
    o.num_verts()
    return o


def _union(o1, o2):
    o = union(o1, o2)
    o.num_verts()
    return o


def test_difference_2d(benchmark):
    c1 = circle(10, 36)
    c1.num_verts()
    c2 = circle(10, 36).translate((5, 0))
    c2.num_verts()
    o = benchmark(_difference, c1, c2)
    assert o.num_verts() == 38


def test_difference_3d(benchmark):
    c1 = sphere(10, 36)
    c1.num_verts()
    c2 = sphere(10, 36).translate((5, 0, 0))
    c2.num_verts()
    o = benchmark(_difference, c1, c2)
    assert o.num_verts() == 1346


def test_intersect_2d(benchmark):
    c1 = circle(10, 36)
    c1.num_verts()
    c2 = circle(10, 36).translate((5, 0))
    c2.num_verts()
    o = benchmark(_intersect, c1, c2)
    assert o.num_verts() == 32


def test_intersect_3d(benchmark):
    c1 = sphere(10, 36)
    c1.num_verts()
    c2 = sphere(10, 36).translate((5, 0, 0))
    c2.num_verts()
    o = benchmark(_intersect, c1, c2)
    assert o.num_verts() == 890


def test_union_2d(benchmark):
    c1 = circle(10, 36)
    c1.num_verts()
    c2 = circle(10, 36).translate((5, 0))
    c2.num_verts()
    o = benchmark(_union, c1, c2)
    assert o.num_verts() == 44


def test_union_3d(benchmark):
    c1 = sphere(10, 36)
    c1.num_verts()
    c2 = sphere(10, 36).translate((5, 0, 0))
    c2.num_verts()
    o = benchmark(_union, c1, c2)
    assert o.num_verts() == 1802


def test_compose_decompose2d():
    l = []
    l.append(circle(5))
    l.append(square(5).translate((15, 0)))
    l.append(rounded_rectangle((5, 3)).translate((0, 15)))
    o = compose(*l)
    l2 = o.decompose()
    assert len(l) == len(l2)


def test_compose_decompose3d():
    l = []
    l.append(cylinder(10, 5))
    l.append(cube(5).translate((15, 0, 0)))
    l.append(cuboid((5, 3, 10)).translate((0, 15, 0)))
    o = compose(*l)
    l2 = o.decompose()
    assert len(l) == len(l2)


def test_hull_2d_and_3d():
    h2 = hull(square(2), square(2).translate([10, 0]))
    assert h2.area() == pytest.approx(24)
    h3 = hull(cube(2), cube(2).translate([10, 0, 0]))
    assert h3.volume() == pytest.approx(48)


def test_hull_points():
    assert hull_points([(0, 0), (4, 0), (0, 3), (1, 1)]).area() == pytest.approx(6)
    assert hull_points(
        [(0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1), (0.1, 0.1, 0.1)]
    ).volume() == pytest.approx(1 / 6)


def test_hull_points_errors():
    with pytest.raises(ValidationError):
        hull_points([(0, 0), (1, 1, 1)])
    with pytest.raises(ValidationError):
        hull_points([(0,), (1,)])


@pytest.mark.parametrize("op", [compose, difference, hull, intersect, union])
def test_mixed_types_rejected(op):
    with pytest.raises(ValidationError):
        op(square(1), cube(1))
    with pytest.raises(ValidationError):
        op(cube(1), square(1))


@pytest.mark.parametrize("op", [compose, difference, hull, intersect, union])
def test_no_objects_rejected(op):
    with pytest.raises(ValidationError):
        op()

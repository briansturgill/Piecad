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
    assert o.num_verts() == 666


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
    assert o.num_verts() == 458


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
    assert o.num_verts() == 879

import pytest
from piecad import *


def _extrude_list(l):
    o = extrude_list(l)
    o.mo.num_vert()
    return o


def _difference(o1, o2):
    o = difference(o1, o2)
    o.mo.num_vert()
    return o


def _intersect(o1, o2):
    o = intersect(o1, o2)
    o.mo.num_vert()
    return o


def _union(o1, o2):
    o = union(o1, o2)
    o.mo.num_vert()
    return o


def test_extrude_list(benchmark):
    c = circle(10)
    o = benchmark(_extrude_list, [(1, c)])
    assert o.mo.num_vert() == 72


def test_difference_2d(benchmark):
    c1 = circle(10, 36)
    c1.mo.num_vert()
    c2 = circle(10, 36).translate((5, 0))
    c2.mo.num_vert()
    o = benchmark(_difference, c1, c2)
    assert o.mo.num_vert() == 38


def test_difference_3d(benchmark):
    c1 = sphere(10, 36)
    c1.mo.num_vert()
    c2 = sphere(10, 36).translate((5, 0, 0))
    c2.mo.num_vert()
    o = benchmark(_difference, c1, c2)
    assert o.mo.num_vert() == 666


def test_intersect_2d(benchmark):
    c1 = circle(10, 36)
    c1.mo.num_vert()
    c2 = circle(10, 36).translate((5, 0))
    c2.mo.num_vert()
    o = benchmark(_intersect, c1, c2)
    assert o.mo.num_vert() == 32


def test_intersect_3d(benchmark):
    c1 = sphere(10, 36)
    c1.mo.num_vert()
    c2 = sphere(10, 36).translate((5, 0, 0))
    c2.mo.num_vert()
    o = benchmark(_intersect, c1, c2)
    assert o.mo.num_vert() == 458


def test_union_2d(benchmark):
    c1 = circle(10, 36)
    c1.mo.num_vert()
    c2 = circle(10, 36).translate((5, 0))
    c2.mo.num_vert()
    o = benchmark(_union, c1, c2)
    assert o.mo.num_vert() == 44


def test_union_3d(benchmark):
    c1 = sphere(10, 36)
    c1.mo.num_vert()
    c2 = sphere(10, 36).translate((5, 0, 0))
    c2.mo.num_vert()
    o = benchmark(_union, c1, c2)
    assert o.mo.num_vert() == 879

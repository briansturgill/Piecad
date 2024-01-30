import manifold3d as _m
import pytest
from piecad import *


def _square(sz):
    o = _m.CrossSection.square(sz)
    o.num_vert()
    return o


def _circle(r, s):
    c = _m.CrossSection.circle(r, s)
    c.num_vert()
    return c


def _cylinder(h, r, s):
    o = _m.Manifold.cylinder(h, r, r, s)
    o.num_vert()
    return o


def _cube(sz):
    o = _m.Manifold.cube(sz)
    o.num_vert()
    return o


def test_mo_circle_10(benchmark):
    o = benchmark(_circle, 3, 10)


def test_mo_circle_100(benchmark):
    o = benchmark(_circle, 3, 100)


def test_mo_square(benchmark):
    o = benchmark(_square, (10, 10))


def test_mo_cylinder_100(benchmark):
    o = benchmark(_cylinder, 15, 10, 100)


def test_mo_cube(benchmark):
    o = benchmark(_cube, (15, 10, 36))

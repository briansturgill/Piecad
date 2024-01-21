import pytest
from piecad import *


def _cube(s):
    c = cube(s)
    c.mo.num_vert()
    return c


def _cuboid(s):
    c = cube(s)
    c.mo.num_vert()
    return c


def _cone(h, r, s):
    c = cone(h, r, s)
    c.mo.num_vert()
    return c


def _cylinder(h, r, s):
    c = cylinder(h, r, s)
    c.mo.num_vert()
    return c


def test_cone(benchmark):
    c = benchmark(_cone, 15, 10, 36)
    assert c.mo.num_vert() == 72


def test_cylinder(benchmark):
    c = benchmark(_cylinder, 15, 10, 36)
    assert c.mo.num_vert() == 72


def test_cube(benchmark):
    c = benchmark(_cube, 20)
    assert c.mo.num_vert() == 8


def test_cuboid(benchmark):
    c = benchmark(_cuboid, (15, 10, 36))
    assert c.mo.num_vert() == 8


def test_extrude():
    c = circle(10)
    assert extrude(c, 1).mo.num_vert() == 72


def test_revolve():
    c = circle(10)
    assert revolve(c).mo.num_vert() == 614

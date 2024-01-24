import pytest
from piecad import *


def _sphere(r, s):
    o = sphere(r, s)
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


def _cone(h, r, s):
    c = cone(h, r, s)
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


def test_cone(benchmark):
    c = benchmark(_cone, 15, 10, 36)
    assert c.num_verts() == 72


def test_cylinder(benchmark):
    c = benchmark(_cylinder, 15, 10, 36)
    assert c.num_verts() == 72


def test_cube(benchmark):
    c = benchmark(_cube, 20)
    assert c.num_verts() == 8


def test_cuboid(benchmark):
    c = benchmark(_cuboid, (15, 10, 36))
    assert c.num_verts() == 8


def test_extrude(benchmark):
    c = circle(10)
    o = benchmark(_extrude, c, 1)
    assert o.num_verts() == 72


def test_revolve():
    c = circle(10)
    assert revolve(c).num_verts() == 614


def test_sphere(benchmark):
    c = benchmark(_sphere, 10, 100)
    assert c.num_verts() == 4902


def test_geodesic_sphere(benchmark):
    c = benchmark(_geodesic_sphere, 10, 100)
    assert c.num_verts() == 2502
    assert c.num_faces() == 5000

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


def _cylinder(h, r, s, centered):
    o = _m.Manifold.cylinder(h, r, r, s, centered)
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
    o = benchmark(_cylinder, 15, 10, 100, False)


def test_mo_cylinder_100_centered(benchmark):
    o = benchmark(_cylinder, 15, 10, 100, True)


def test_mo_cube(benchmark):
    o = benchmark(_cube, (15, 10, 36))


def _create_from_verts_and_faces(verts, faces):
    o = _m.Manifold.create_from_verts_and_faces(verts, faces)
    o.num_vert()
    return o


def test_mo_cube_from_create_from_verts_and_faces(benchmark):
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
    out = benchmark(_create_from_verts_and_faces, vertices, faces)
    print(out.status)
    assert out.num_vert() == 8

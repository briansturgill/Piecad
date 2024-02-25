import manifold3d as _m
import pytest
import numpy as _np
from piecad import cos, sin


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


def _from_verts_and_triangles(v, f):
    if hasattr(_m.Manifold, "create_from_verts_and_triangles"):
        o = _m.Manifold.create_from_verts_and_triangles(v, f)
    else:
        v = _np.array(v, _np.float32)
        f = _np.array(f, _np.uint32)
        mesh = _m.Mesh(v, f)
        o = _m.Manifold(mesh)
    o.num_vert()
    return o


def test_cube_from_create_from_verts_and_triangles(benchmark):
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
    triangles = [
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

    out = benchmark(_from_verts_and_triangles, vertices, triangles)
    assert out.num_vert() == 8


_arc_trig_vals_map = {}


def _rounded_rectangle(
    size: list[float, float],
    rounding_radius: float = 2.0,
    segments: int = 36,
    center: bool = False,
) -> _m.CrossSection:
    segs_per_arc = segments // 4 + 1
    deg_per_seg = 90.0 / segs_per_arc
    pts = []
    x, y = size

    def make_arc_trig_vals(deg):
        end = deg + 90
        l = []
        for i in range(0, segs_per_arc - 1):
            l.append((cos(deg), sin(deg)))
            deg += deg_per_seg

        l.append((cos(end), sin(end)))
        return l

    if segments in _arc_trig_vals_map:
        arc_trig_vals = _arc_trig_vals_map[segments]
    else:
        arc_trig_vals = (
            make_arc_trig_vals(180),  # Bottom left
            make_arc_trig_vals(270),  # Bottom right
            make_arc_trig_vals(0),  # Top right
            make_arc_trig_vals(90),  # Top left
        )
        _arc_trig_vals_map[segments] = arc_trig_vals

    rr = rounding_radius

    c_x_off = -x / 2.0 if center else 0.0
    c_y_off = -y / 2.0 if center else 0.0

    bl, br, tr, tl = arc_trig_vals

    x_off = rr + c_x_off
    y_off = rr + c_y_off
    for c, s in bl:  # Bottom left
        pts.append((x_off + rr * c, y_off + rr * s))

    x_off = x - rr + c_x_off
    y_off = rr + c_y_off
    for c, s in br:  # Bottom right
        pts.append((x_off + rr * c, y_off + rr * s))

    x_off = x - rr + c_x_off
    y_off = y - rr + c_y_off
    for c, s in tr:  # Top right
        pts.append((x_off + rr * c, y_off + rr * s))

    x_off = rr + c_x_off
    y_off = y - rr + c_y_off
    for c, s in tl:  # Top left
        pts.append((x_off + rr * c, y_off + rr * s))

    if hasattr(_m.CrossSection, "create_from_polygons_unchecked"):
        o = _m.CrossSection.create_from_polygons_unchecked([pts])
    else:
        o = _m.CrossSection([pts], _m.FillRule.EvenOdd)
    o.num_vert()
    return o


def test_rounded_rectangle(benchmark):
    o = benchmark(_rounded_rectangle, (10, 12))
    assert o.num_vert() == 40


if hasattr(_m.CrossSection, "rounded_rectangle"):

    def _mo_rounded_rectangle(sz, r, segs):
        o = _m.CrossSection.rounded_rectangle(sz, r, segs)
        o.num_vert()
        return o

    def test_mo_rounded_rectangle(benchmark):
        o = benchmark(_mo_rounded_rectangle, (10.0, 12.0), 2.0, 36)
        assert o.num_vert() == 40


if hasattr(_m.Manifold, "extrude_simple"):

    def _mo_extrude_simple(cs, isConvex):
        o = _m.Manifold.extrude_simple(cs, 10, is_convex=isConvex)
        o.num_vert()
        return o

    def test_extrude_simple_circle_100_earcut(benchmark):
        c = _m.CrossSection.circle(5, 100)
        o = benchmark(_mo_extrude_simple, c, False)
        assert o.num_vert() == 200

    def test_extrude_simple_circle_100_fan(benchmark):
        c = _m.CrossSection.circle(5, 100)
        o = benchmark(_mo_extrude_simple, c, True)
        assert o.num_vert() == 200


if hasattr(_m.Manifold, "extrude_transforming"):

    def _mo_extrude_transforming(cs, isConvex):
        o = _m.Manifold.extrude_transforming(cs, 10, is_convex=isConvex)
        o.num_vert()
        return o

    def test_extrude_transforming_circle_100_earcut(benchmark):
        c = _m.CrossSection.circle(5, 100)
        o = benchmark(_mo_extrude_transforming, c, False)
        assert o.num_vert() == 200

    def test_extrude_transforming_circle_100_fan(benchmark):
        c = _m.CrossSection.circle(5, 100)
        o = benchmark(_mo_extrude_transforming, c, True)
        assert o.num_vert() == 200

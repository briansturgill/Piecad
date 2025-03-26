import pytest
import manifold3d as _m
from piecad import *


def _polygon(pts, c=True):
    o = polygon(pts, c)
    o.num_verts()
    return o


def _star(np, r):
    o = star(np, r)
    o.num_verts()
    return o


def _square(s, c=False):
    o = square(s, c)
    o.num_verts()
    return o


def _rectangle(t, c=False):
    o = rectangle(t, c)
    o.num_verts()
    return o


def _rounded_rectangle(t, r, s, c=False):
    o = rounded_rectangle(t, r, s, c)
    o.num_verts()
    return o


def _ellipse(r, s):
    c = ellipse(r, s)
    c.num_verts()
    return c


def _circle(r, s):
    c = circle(r, s)
    c.num_verts()
    return c


def test_circle_12(benchmark):
    o = benchmark(_circle, 3, 12)
    assert o.num_verts() == 12
    assert o.bounding_box() == (-3, -3, 3, 3)


def test_circle_100(benchmark):
    o = benchmark(_circle, 3, 100)
    assert o.num_verts() == 100
    assert o.bounding_box() == (-3, -3, 3, 3)


def test_ellipse_12(benchmark):
    o = benchmark(_ellipse, (3, 12), 12)
    assert o.num_verts() == 12
    assert o.bounding_box() == (-3, -12, 3, 12)


def test_ellipse_100(benchmark):
    o = benchmark(_ellipse, (3, 12), 100)
    assert o.num_verts() == 100
    assert o.bounding_box() == (-3, -12, 3, 12)


def test_square(benchmark):
    o = benchmark(_square, 10)
    assert o.num_verts() == 4
    assert o.bounding_box() == (0, 0, 10, 10)


def test_square_centered(benchmark):
    o = benchmark(_square, 10, True)
    assert o.num_verts() == 4
    assert o.bounding_box() == (-5, -5, 5, 5)


def test_rectangle(benchmark):
    o = benchmark(_rectangle, [10, 10])
    assert o.num_verts() == 4
    assert o.bounding_box() == (0, 0, 10, 10)


def test_rectangle2(benchmark):
    o = benchmark(_rectangle, (10, 10))  # Check list vs tuple
    assert o.num_verts() == 4
    assert o.bounding_box() == (0, 0, 10, 10)


def test_rectangle_centered(benchmark):
    o = benchmark(_rectangle, [10, 10], True)
    assert o.num_verts() == 4
    assert o.bounding_box() == (-5, -5, 5, 5)


def test_rounded_rectangle(benchmark):
    o = benchmark(_rounded_rectangle, (10, 10), 2.0, 36)
    assert o.num_verts() == 40
    assert o.bounding_box() == (0, 0, 10, 10)


def test_rounded_rectangle_centered(benchmark):
    o = benchmark(_rounded_rectangle, (10, 10), 2.0, 36, True)
    assert o.num_verts() == 40
    assert o.bounding_box() == (-5, -5, 5, 5)


def test_star(benchmark):
    o = benchmark(_star, 8, 20)
    assert o.num_verts() == 16
    assert o.bounding_box() == (-20, -20, 20, 20)
    assert o.area() == pytest.approx(937.2582999)


# For this last 2 functions, we are trying to see if winding makes a speed difference
pts = [
    (-0.2, 0.0),
    (-0.19696155, -0.03472964),
    (-0.18793853, -0.06840403),
    (-0.17320508, -0.1),
    (-0.1532089, -0.12855752),
    (-0.12855752, -0.1532089),
    (-0.1, -0.17320508),
    (-0.06840403, -0.18793853),
    (-0.03472964, -0.19696155),
    (0.0, -0.2),
    (10.0, -0.2),
    (10.03473, -0.19696155),
    (10.068404, -0.18793853),
    (10.1, -0.17320508),
    (10.128557, -0.1532089),
    (10.153209, -0.12855752),
    (10.173205, -0.1),
    (10.187939, -0.06840403),
    (10.196961, -0.03472964),
    (10.2, 0.0),
    (10.2, 10.0),
    (10.196961, 10.03473),
    (10.187939, 10.068404),
    (10.173205, 10.1),
    (10.153209, 10.128557),
    (10.128557, 10.153209),
    (10.1, 10.173205),
    (10.068404, 10.187939),
    (10.03473, 10.196961),
    (10.0, 10.2),
    (0.0, 10.2),
    (-0.03472964, 10.196961),
    (-0.06840403, 10.187939),
    (-0.1, 10.173205),
    (-0.12855752, 10.153209),
    (-0.1532089, 10.128557),
    (-0.17320508, 10.1),
    (-0.18793853, 10.068404),
    (-0.19696155, 10.03473),
    (-0.2, 10.0),
]


def test_polygon(benchmark):
    c = benchmark(_polygon, [pts])


def test_polygon_no_check(benchmark):
    c = benchmark(_polygon, [pts], False)


def test_polygon_rev(benchmark):
    rev = pts.reverse()
    c = benchmark(_polygon, [pts])


def test_polygon_self_intersect():
    poly = [(10, 10), (50, 50), (50, 10), (10, 50)]
    with pytest.raises(ValidationError):
        _polygon([poly])


import numpy as _np

_arc_trig_vals_map = {}


def _rounded_rectangle_np(
    size: list[float, float],
    rounding_radius: float = 0.2,
    segments: int = -1,
    center: bool = False,
) -> Obj2d:
    segs_per_arc = segments // 4 + 1
    deg_per_arc = 90.0 / segs_per_arc
    x, y = size

    def make_arc_trig_vals(deg):
        end = deg + 90
        l = []
        for i in range(0, segs_per_arc - 1):
            l.append((cos(deg), sin(deg)))
            deg += deg_per_arc

        l.append((cos(end), sin(end)))
        return l

    if segments in _arc_trig_vals_map:
        arc_trig_vals = _arc_trig_vals_map[segments]
    else:
        l = []
        l.extend(make_arc_trig_vals(180))  # Bottom left
        l.extend(make_arc_trig_vals(270))  # Bottom right
        l.extend(make_arc_trig_vals(0))  # Top right
        l.extend(make_arc_trig_vals(90))  # Top left
        arc_trig_vals = _np.array(l, dtype=_np.float64)
        _arc_trig_vals_map[segments] = arc_trig_vals

    rr = rounding_radius

    spa = segs_per_arc
    pts = _np.array(arc_trig_vals)
    pts *= rr
    if center:
        c_x_off = -x / 2.0 if center else 0.0
        c_y_off = -y / 2.0 if center else 0.0
        pts[:, 0] += c_x_off
        pts[:, 1] += c_y_off
    pts[0:spa, 0] += rr  # Bottom left
    pts[0:spa, 1] += rr
    pts[spa : 2 * spa, 0] += x - rr  # Bottom right
    pts[spa : 2 * spa, 1] += rr
    pts[spa * 2 : 3 * spa, 0] += x - rr  # Top right
    pts[spa * 2 : 3 * spa, 1] += y - rr
    pts[spa * 3 : 4 * spa, 0] += rr  # Top left
    pts[spa * 3 : 4 * spa, 1] += y - rr

    return Obj2d(_m.CrossSection([pts], _m.FillRule.EvenOdd))


def test_rounded_rectangle_np(benchmark):
    o = benchmark(_rounded_rectangle_np, (10, 10), 2.0, 36)
    assert o.num_verts() == 40
    assert o.bounding_box() == (0, 0, 10, 10)


def test_rounded_rectangle_np_centered(benchmark):
    o = benchmark(_rounded_rectangle_np, (10, 10), 2.0, 36, True)
    assert o.num_verts() == 40
    assert o.bounding_box() == (-5, -5, 5, 5)


def _rounded_rectangle_hull(
    size: list[float, float],
    rounding_radius: float = 0.2,
    segments: int = -1,
    center: bool = False,
) -> Obj2d:
    if segments == -1:
        segments = config["DefaultSegments"]

    rr = rounding_radius
    circ = circle(rr, segments)

    x = size[0]
    y = size[1]

    c_x_off = -x / 2.0 if center else 0.0
    c_y_off = -y / 2.0 if center else 0.0

    return Obj2d(
        _m.CrossSection.batch_hull(
            [
                circ.translate((c_x_off + rr, c_y_off + rr)).mo,
                circ.translate((c_x_off + size[0] - rr, c_y_off + rr)).mo,
                circ.translate((c_x_off + size[0] - rr, c_y_off + size[1] - rr)).mo,
                circ.translate((c_x_off + rr, c_y_off + size[1] - rr)).mo,
            ]
        )
    )


def test_rounded_rectangle_hull(benchmark):
    o = benchmark(_rounded_rectangle_hull, (10, 10), 2.0, 36)
    assert o.num_verts() == 40
    assert o.bounding_box() == (0, 0, 10, 10)


def test_rounded_rectangle_hull_centered(benchmark):
    o = benchmark(_rounded_rectangle_hull, (10, 10), 2.0, 36, True)
    assert o.num_verts() == 40
    assert o.bounding_box() == (-5, -5, 5, 5)

import math
import pytest
from piecad import *
from piecad import Config, near_eq, near_ge, near_le
from piecad._cutter import cutter, fillet_cutter
from piecad._pad_align import (
    _normalize,
    _basis_from_xy,
    _rotation_to_xyz_degrees,
    _matrix_vector_multiply,
)


def _bb_close(a, b):
    assert a == pytest.approx(b, abs=1e-6)


def test_near_helpers():
    assert near_eq(1.0, 1.0)
    assert near_eq(1.0, 1.05, 0.1)
    assert near_eq(1.05, 1.0, 0.1)
    assert not near_eq(1.0, 1.2, 0.1)
    assert near_le(1.0, 2.0)
    assert not near_le(2.0, 1.0)
    assert near_ge(2.0, 1.0)
    assert not near_ge(1.0, 2.0)


def test_layer_resolution_validation():
    old = Config.get_layer_resolution()
    try:
        Config.set_layer_resolution(0.2)
        assert Config.get_layer_resolution() == 0.2
        for bad in (0, -0.1):
            with pytest.raises(ValidationError):
                Config.set_layer_resolution(bad)
    finally:
        Config.set_layer_resolution(old)


def test_units_validation():
    with pytest.raises(ValidationError):
        Config.set_default_units("furlongs")


def test_minkowski():
    s = cube(10).minkowski_sum(cube(2))
    assert s.volume() == pytest.approx(12**3)
    d = cube(10).minkowski_difference(cube(2))
    assert d.volume() == pytest.approx(8**3)


def test_resize_all_unset_is_unchanged():
    c = cuboid((1, 2, 3))
    for sizes in ((None, None, None), (0, 0, 0)):
        assert c.resize(sizes).bounding_box() == c.bounding_box()
    r = rectangle((1, 2))
    for sizes in ((None, None), (0, 0)):
        assert r.resize(sizes).bounding_box() == r.bounding_box()


def test_miter_cut_angle_range():
    for bad in (-91, 91):
        with pytest.raises(ValidationError):
            cube(10).miter_cut(bad, (5, 5, 5))


@pytest.mark.parametrize("angle", [0, 45, -45, 90])
def test_miter_cut_returns_least_x_then_z_first(angle):
    first, second = cube(10).miter_cut(angle, (5, 5, 5))
    assert first.volume() + second.volume() == pytest.approx(1000)
    fb, sb = first.bounding_box(), second.bounding_box()
    assert (fb[0], fb[2]) <= (sb[0], sb[2])


def test_split_returns_difference_and_intersection():
    inter, diff = cube(10).split(cube(10).translate((5, -1, -1)))
    assert diff.volume() == pytest.approx(595)
    assert inter.volume() == pytest.approx(405)


def test_piecut_3d_both_and_wrap():
    rest, wedge = cube(10).piecut(0, 90, both=True)
    assert rest.volume() == pytest.approx(750)
    assert wedge.volume() == pytest.approx(250)
    assert cube(10).piecut(300, 60).volume() < 1000
    with pytest.raises(ValidationError):
        cube(10).piecut(0, 360)


def test_piecut_2d_both_and_wrap():
    rest, wedge = square(10).piecut(0, 90, both=True)
    assert rest.area() == pytest.approx(75)
    assert wedge.area() == pytest.approx(25)
    assert square(10).piecut(300, 60).area() < 100


def test_obj2d_revolve():
    o = square(2).translate((3, 0)).revolve(360)
    assert o.volume() > 0


def test_simplify_tolerance_validation():
    for o in (cube(1), square(1)):
        with pytest.raises(ValidationError):
            o.simplify(-1)


def test_transform_bad_matrix():
    with pytest.raises(ValueError):
        cube(1).transform(((1, 0, 0, 0), (0, 1, 0, 0)))
    with pytest.raises(ValueError):
        square(1).transform(((1, 0, 0),))


def test_cutter_errors():
    ok = ((0, 0, 0), (10, 0, 0))
    with pytest.raises(ValidationError):
        cutter(True, (0, 0, 0), (0, 0, 0), (0, 1, 0), (0, 0, 1), 1)
    with pytest.raises(ValidationError):
        cutter(True, *ok, (1, 0, 0), (0, 0, 1), 1)
    with pytest.raises(ValidationError):
        cutter(True, *ok, (0, 1, 0), (1, 0, 0), 1)
    with pytest.raises(ValidationError):
        cutter(True, *ok, (0, 1, 0), (0, -1, 0), 1)
    with pytest.raises(ValidationError):
        cutter(True, *ok, (0, 0, 0), (0, 0, 1), 1)


def test_fillet_cutter_segment_clamps():
    old = Config.get_layer_resolution()
    try:
        Config.set_layer_resolution(10)
        assert fillet_cutter(1, 5).volume() > 0
        Config.set_layer_resolution(0.001)
        assert fillet_cutter(5, 5).volume() > 0
    finally:
        Config.set_layer_resolution(old)


def test_pad_align_degenerate_inputs():
    with pytest.raises(ValueError):
        _normalize((0, 0, 0))
    with pytest.raises(ValueError):
        _basis_from_xy((1, 0, 0), (2, 0, 0))


@pytest.mark.parametrize("sign", [1, -1])
def test_rotation_gimbal_lock_round_trip(sign):
    # Ry(+/-90) composed with an x rotation: cos(ry) == 0.
    rx = math.radians(30)
    cx, sx = math.cos(rx), math.sin(rx)
    ry_m = [[0, 0, sign], [0, 1, 0], [-sign, 0, 0]]
    rx_m = [[1, 0, 0], [0, cx, -sx], [0, sx, cx]]
    R = [
        [sum(ry_m[i][k] * rx_m[k][j] for k in range(3)) for j in range(3)]
        for i in range(3)
    ]
    ang = _rotation_to_xyz_degrees(R)
    assert ang[2] == 0.0
    pts = [(1.0, 2.0, 3.0), (2.0, 2.0, 3.0), (1.0, 4.0, 3.0), (1.0, 2.0, 6.0)]
    verts, _ = hull_points(pts).rotate(ang).to_verts_and_faces()
    expected = sorted(
        tuple(round(c, 5) for c in _matrix_vector_multiply(R, p)) for p in pts
    )
    got = sorted(tuple(round(c, 5) + 0.0 for c in v) for v in verts)
    for g, e in zip(got, expected):
        assert g == pytest.approx(e, abs=1e-4)


def _frame(extra=None):
    f = difference(cuboid((10, 2, 10)), cuboid((6, 2, 6)).translate((2, 0, 2)))
    return f if extra is None else union(f, extra)


def test_miter_cut_tie_on_x_and_z_orders_by_volume():
    # A diagonal cut through a square frame leaves both halves with identical bounding boxes.
    small = cuboid((1, 2, 1)).translate((2.2, 0, 3.5))
    big = _frame(small)
    first, second = big.miter_cut(45, (5, 1, 5))
    assert first.bounding_box() == second.bounding_box()
    assert first.volume() < second.volume()
    # Same result when the heavier half is the other one.
    first, second = (
        big.mirror((True, False, False)).translate((10, 0, 0)).miter_cut(-45, (5, 1, 5))
    )
    assert first.volume() < second.volume()


def test_miter_cut_order_is_stable_under_noise():
    base = _frame(cuboid((1, 2, 1)).translate((2.2, 0, 3.5)))
    ref = [o.volume() for o in base.miter_cut(45, (5, 1, 5))]
    for noise in (1e-14, -1e-14, 3e-13):
        got = [o.volume() for o in base.miter_cut(45, (5 + noise, 1, 5 - noise))]
        assert got == pytest.approx(ref, abs=1e-6)

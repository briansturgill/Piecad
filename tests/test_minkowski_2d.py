import pytest

from piecad import Obj2d, circle, difference, rectangle, square, union


def assert_shape_equal(actual, expected):
    assert (actual.mo - expected.mo).area() == pytest.approx(0, abs=1e-6)
    assert (expected.mo - actual.mo).area() == pytest.approx(0, abs=1e-6)


def test_sum_of_translated_rectangles():
    first = rectangle(10, 5).translate((3, -2))
    second = rectangle(2, 4).translate((7, 8))
    expected = rectangle(12, 9).translate((10, 6))
    assert_shape_equal(first.minkowski_sum(second), expected)


def test_sum_of_concave_disconnected_shapes():
    first = union(rectangle(4, 1), rectangle(1, 4))
    second = union(square(1), square(1).translate((10, 0)))
    one = union(rectangle(5, 2), rectangle(2, 5))
    assert_shape_equal(first.minkowski_sum(second), union(one, one.translate((10, 0))))


def test_sum_reduces_hole_and_accepts_polygonal_circle():
    ring = difference(square(10), square(4).translate((3, 3)))
    result = ring.minkowski_sum(square(2))
    expected = difference(square(12), square(2).translate((5, 5)))
    assert_shape_equal(result, expected)
    circle_result = square(2).minkowski_sum(circle(1, segments=4))
    assert circle_result.area() == pytest.approx(14)


def test_difference_with_translated_kernel():
    first = rectangle(10, 8).translate((3, 5))
    second = rectangle(2, 3).translate((4, 1))
    expected = rectangle(8, 5).translate((-1, 4))
    assert_shape_equal(first.minkowski_difference(second), expected)


def test_difference_grows_holes_and_erodes_concave_parts():
    ring = difference(square(10), square(4).translate((3, 3)))
    expected = difference(square(8), square(6).translate((1, 1)))
    assert_shape_equal(ring.minkowski_difference(square(2)), expected)
    l_shape = union(rectangle(5, 2), rectangle(2, 5))
    expected_l = union(rectangle(4, 1), rectangle(1, 4))
    assert_shape_equal(l_shape.minkowski_difference(square(1)), expected_l)


def test_difference_with_disconnected_kernel():
    first = union(square(4), square(4).translate((10, 0)))
    second = union(square(1), square(1).translate((10, 0)))
    assert_shape_equal(first.minkowski_difference(second), square(3))


def test_empty_operands_and_invalid_types():
    empty = Obj2d()
    shape = square(2)
    assert empty.minkowski_sum(shape).is_empty()
    assert shape.minkowski_sum(empty).is_empty()
    assert empty.minkowski_difference(shape).is_empty()
    assert shape.minkowski_difference(square(3)).is_empty()
    assert shape.minkowski_difference(square(2)).is_empty()
    with pytest.raises(ValueError, match="unbounded"):
        shape.minkowski_difference(empty)
    for operation in (shape.minkowski_sum, shape.minkowski_difference):
        with pytest.raises(TypeError):
            operation(object())

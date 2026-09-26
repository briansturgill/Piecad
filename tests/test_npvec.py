"""
Pytest (+ pytest-benchmark) tests that duplicate test_vec.py, but exercise
the equivalent numpy operations instead of vec.py's tuple-based Vec2/Vec3
functions.

Test names include "np" (and mirror the "vec" names in test_vec.py) so
the two suites, and their benchmark results, can be compared directly.
Each numpy operation has its own dedicated benchmark test, matching
test_vec.py's per-function benchmarks one-for-one.
"""

import math

import numpy as np
import pytest


def vec2(x, y):
    return np.array([float(x), float(y)])


def vec3(x, y, z):
    return np.array([float(x), float(y), float(z)])


# ---------------------------------------------------------------------------
# np abs (Vec2.abs equivalent)
# ---------------------------------------------------------------------------


def test_np_vec2_abs_of_positive_vector_is_unchanged():
    assert np.array_equal(np.abs(vec2(3.0, 4.0)), vec2(3.0, 4.0))


def test_np_vec2_abs_of_negative_vector_flips_both_signs():
    assert np.array_equal(np.abs(vec2(-3.0, -4.0)), vec2(3.0, 4.0))


def test_np_vec2_abs_of_mixed_sign_vector_is_component_wise():
    assert np.array_equal(np.abs(vec2(-3.0, 4.0)), vec2(3.0, 4.0))


def test_np_vec2_abs_of_zero_vector_is_zero():
    assert np.array_equal(np.abs(vec2(0.0, 0.0)), vec2(0.0, 0.0))


# ---------------------------------------------------------------------------
# np abs (Vec3.abs equivalent)
# ---------------------------------------------------------------------------


def test_np_vec3_abs_of_positive_vector_is_unchanged():
    assert np.array_equal(np.abs(vec3(3.0, 4.0, 5.0)), vec3(3.0, 4.0, 5.0))


def test_np_vec3_abs_of_negative_vector_flips_all_signs():
    assert np.array_equal(np.abs(vec3(-3.0, -4.0, -5.0)), vec3(3.0, 4.0, 5.0))


def test_np_vec3_abs_of_mixed_sign_vector_is_component_wise():
    assert np.array_equal(np.abs(vec3(-3.0, 4.0, -5.0)), vec3(3.0, 4.0, 5.0))


def test_np_vec3_abs_of_zero_vector_is_zero():
    assert np.array_equal(np.abs(vec3(0.0, 0.0, 0.0)), vec3(0.0, 0.0, 0.0))


# ---------------------------------------------------------------------------
# np add (Vec2.add equivalent)
# ---------------------------------------------------------------------------


def test_np_vec2_add_combines_components():
    assert np.array_equal(vec2(1.0, 2.0) + vec2(3.0, 4.0), vec2(4.0, 6.0))


def test_np_vec2_add_with_negative_operand_subtracts_effectively():
    assert np.array_equal(vec2(1.0, 2.0) + vec2(-1.0, -2.0), vec2(0.0, 0.0))


def test_np_vec2_add_with_zero_vector_is_identity():
    v = vec2(5.5, -2.25)
    assert np.array_equal(v + vec2(0.0, 0.0), v)


# ---------------------------------------------------------------------------
# np add (Vec3.add equivalent)
# ---------------------------------------------------------------------------


def test_np_vec3_add_combines_components():
    assert np.array_equal(
        vec3(1.0, 2.0, 3.0) + vec3(4.0, 5.0, 6.0), vec3(5.0, 7.0, 9.0)
    )


def test_np_vec3_add_with_negative_operand_subtracts_effectively():
    assert np.array_equal(
        vec3(1.0, 2.0, 3.0) + vec3(-1.0, -2.0, -3.0), vec3(0.0, 0.0, 0.0)
    )


def test_np_vec3_add_with_zero_vector_is_identity():
    v = vec3(5.5, -2.25, 3.0)
    assert np.array_equal(v + vec3(0.0, 0.0, 0.0), v)


# ---------------------------------------------------------------------------
# np multiply (Vec2.mul equivalent)
# ---------------------------------------------------------------------------


def test_np_vec2_mul_is_component_wise():
    assert np.array_equal(vec2(2.0, 3.0) * vec2(4.0, 5.0), vec2(8.0, 15.0))


def test_np_vec2_mul_by_zero_vector_is_zero():
    assert np.array_equal(vec2(2.0, 3.0) * vec2(0.0, 0.0), vec2(0.0, 0.0))


def test_np_vec2_mul_by_negative_one_negates_vector():
    assert np.array_equal(vec2(2.0, -3.0) * vec2(-1.0, -1.0), vec2(-2.0, 3.0))


# ---------------------------------------------------------------------------
# np multiply (Vec3.mul equivalent)
# ---------------------------------------------------------------------------


def test_np_vec3_mul_is_component_wise():
    assert np.array_equal(
        vec3(2.0, 3.0, 4.0) * vec3(5.0, 6.0, 7.0), vec3(10.0, 18.0, 28.0)
    )


def test_np_vec3_mul_by_zero_vector_is_zero():
    assert np.array_equal(
        vec3(2.0, 3.0, 4.0) * vec3(0.0, 0.0, 0.0), vec3(0.0, 0.0, 0.0)
    )


def test_np_vec3_mul_by_negative_one_negates_vector():
    assert np.array_equal(
        vec3(2.0, -3.0, 4.0) * vec3(-1.0, -1.0, -1.0), vec3(-2.0, 3.0, -4.0)
    )


# ---------------------------------------------------------------------------
# np negate (Vec2.neg equivalent)
# ---------------------------------------------------------------------------


def test_np_vec2_neg_flips_sign_of_both_components():
    assert np.array_equal(-vec2(3.0, -4.0), vec2(-3.0, 4.0))


def test_np_vec2_neg_of_zero_vector_is_zero():
    assert np.array_equal(-vec2(0.0, 0.0), vec2(0.0, 0.0))


def test_np_vec2_neg_applied_twice_returns_original():
    v = vec2(3.0, -4.0)
    assert np.array_equal(-(-v), v)


# ---------------------------------------------------------------------------
# np negate (Vec3.neg equivalent)
# ---------------------------------------------------------------------------


def test_np_vec3_neg_flips_sign_of_all_components():
    assert np.array_equal(-vec3(3.0, -4.0, 5.0), vec3(-3.0, 4.0, -5.0))


def test_np_vec3_neg_of_zero_vector_is_zero():
    assert np.array_equal(-vec3(0.0, 0.0, 0.0), vec3(0.0, 0.0, 0.0))


def test_np_vec3_neg_applied_twice_returns_original():
    v = vec3(3.0, -4.0, 5.0)
    assert np.array_equal(-(-v), v)


# ---------------------------------------------------------------------------
# np unary positive (Vec2.pos equivalent)
# ---------------------------------------------------------------------------


def test_np_vec2_pos_returns_an_equal_vector():
    v = vec2(3.0, -4.0)
    assert np.array_equal(+v, v)


def test_np_vec2_pos_of_zero_vector_is_zero():
    assert np.array_equal(+vec2(0.0, 0.0), vec2(0.0, 0.0))


# ---------------------------------------------------------------------------
# np unary positive (Vec3.pos equivalent)
# ---------------------------------------------------------------------------


def test_np_vec3_pos_returns_an_equal_vector():
    v = vec3(3.0, -4.0, 5.0)
    assert np.array_equal(+v, v)


def test_np_vec3_pos_of_zero_vector_is_zero():
    assert np.array_equal(+vec3(0.0, 0.0, 0.0), vec3(0.0, 0.0, 0.0))


# ---------------------------------------------------------------------------
# np subtract (Vec2.sub equivalent)
# ---------------------------------------------------------------------------


def test_np_vec2_sub_combines_components():
    assert np.array_equal(vec2(5.0, 7.0) - vec2(2.0, 3.0), vec2(3.0, 4.0))


def test_np_vec2_sub_of_a_vector_with_itself_is_zero():
    v = vec2(9.5, -3.25)
    assert np.array_equal(v - v, vec2(0.0, 0.0))


def test_np_vec2_sub_from_zero_vector_negates_operand():
    assert np.array_equal(vec2(0.0, 0.0) - vec2(3.0, -4.0), vec2(-3.0, 4.0))


# ---------------------------------------------------------------------------
# np subtract (Vec3.sub equivalent)
# ---------------------------------------------------------------------------


def test_np_vec3_sub_combines_components():
    assert np.array_equal(
        vec3(5.0, 7.0, 9.0) - vec3(1.0, 2.0, 3.0), vec3(4.0, 5.0, 6.0)
    )


def test_np_vec3_sub_of_a_vector_with_itself_is_zero():
    v = vec3(9.5, -3.25, 1.0)
    assert np.array_equal(v - v, vec3(0.0, 0.0, 0.0))


def test_np_vec3_sub_from_zero_vector_negates_operand():
    assert np.array_equal(
        vec3(0.0, 0.0, 0.0) - vec3(3.0, -4.0, 5.0), vec3(-3.0, 4.0, -5.0)
    )


# ---------------------------------------------------------------------------
# np true division (Vec2.truediv equivalent)
# ---------------------------------------------------------------------------


def test_np_vec2_truediv_is_component_wise():
    assert np.array_equal(vec2(8.0, 9.0) / vec2(2.0, 3.0), vec2(4.0, 3.0))


def test_np_vec2_truediv_by_one_is_identity():
    v = vec2(7.5, -2.25)
    assert np.array_equal(v / vec2(1.0, 1.0), v)


def test_np_vec2_truediv_by_zero_produces_infinity():
    # Unlike vec.py (plain Python floats, which raise ZeroDivisionError),
    # numpy division by zero produces inf/nan with a runtime warning
    # instead of raising.
    with np.errstate(divide="ignore"):
        result = vec2(1.0, 1.0) / vec2(0.0, 1.0)
    assert math.isinf(result[0])
    assert result[1] == 1.0


# ---------------------------------------------------------------------------
# np true division (Vec3.truediv equivalent)
# ---------------------------------------------------------------------------


def test_np_vec3_truediv_is_component_wise():
    assert np.array_equal(
        vec3(8.0, 9.0, 10.0) / vec3(2.0, 3.0, 5.0), vec3(4.0, 3.0, 2.0)
    )


def test_np_vec3_truediv_by_one_is_identity():
    v = vec3(7.5, -2.25, 3.0)
    assert np.array_equal(v / vec3(1.0, 1.0, 1.0), v)


def test_np_vec3_truediv_by_zero_produces_infinity():
    with np.errstate(divide="ignore"):
        result = vec3(1.0, 1.0, 1.0) / vec3(0.0, 1.0, 1.0)
    assert math.isinf(result[0])
    assert result[1] == 1.0
    assert result[2] == 1.0


# ---------------------------------------------------------------------------
# np cross (Vec2.cross equivalent)
# ---------------------------------------------------------------------------


def _cross2d(a, b):
    """Matches Vec2.cross: embeds the 2D cross product's z component in 3D."""
    return vec3(0.0, 0.0, a[0] * b[1] - a[1] * b[0])


def test_np_vec2_cross_of_orthogonal_unit_vectors_is_positive_z():
    assert np.array_equal(_cross2d(vec2(1.0, 0.0), vec2(0.0, 1.0)), vec3(0.0, 0.0, 1.0))


def test_np_vec2_cross_of_parallel_vectors_is_zero():
    assert np.array_equal(_cross2d(vec2(2.0, 4.0), vec2(1.0, 2.0)), vec3(0.0, 0.0, 0.0))


def test_np_vec2_cross_returns_a_length_three_array():
    result = _cross2d(vec2(3.0, 4.0), vec2(5.0, 6.0))
    assert result.shape == (3,)


def test_np_vec2_cross_is_anti_commutative():
    a, b = vec2(3.0, 4.0), vec2(5.0, 6.0)
    forward = _cross2d(a, b)
    backward = _cross2d(b, a)
    assert forward[2] == -backward[2]


# ---------------------------------------------------------------------------
# np cross (Vec3.cross equivalent)
# ---------------------------------------------------------------------------


def test_np_vec3_cross_of_x_and_y_axes_is_z_axis():
    assert np.array_equal(
        np.cross(vec3(1.0, 0.0, 0.0), vec3(0.0, 1.0, 0.0)), vec3(0.0, 0.0, 1.0)
    )


def test_np_vec3_cross_of_parallel_vectors_is_zero():
    assert np.array_equal(
        np.cross(vec3(2.0, 4.0, 6.0), vec3(1.0, 2.0, 3.0)), vec3(0.0, 0.0, 0.0)
    )


def test_np_vec3_cross_returns_a_length_three_array():
    result = np.cross(vec3(3.0, 4.0, 5.0), vec3(5.0, 6.0, 7.0))
    assert result.shape == (3,)


def test_np_vec3_cross_is_anti_commutative():
    a, b = vec3(3.0, 4.0, 5.0), vec3(5.0, 6.0, 7.0)
    forward = np.cross(a, b)
    backward = np.cross(b, a)
    assert np.array_equal(forward, -backward)


# ---------------------------------------------------------------------------
# np distance (Vec2.distance equivalent)
# ---------------------------------------------------------------------------


def test_np_vec2_distance_between_a_3_4_5_triangle():
    assert np.linalg.norm(vec2(3.0, 4.0) - vec2(0.0, 0.0)) == pytest.approx(5.0)


def test_np_vec2_distance_to_self_is_zero():
    v = vec2(7.5, -2.25)
    assert np.linalg.norm(v - v) == 0.0


def test_np_vec2_distance_is_symmetric():
    a, b = vec2(1.0, 2.0), vec2(4.0, 6.0)
    assert np.linalg.norm(b - a) == pytest.approx(np.linalg.norm(a - b))


# ---------------------------------------------------------------------------
# np distance (Vec3.distance equivalent)
# ---------------------------------------------------------------------------


def test_np_vec3_distance_matches_pythagorean_3_4_12_13():
    assert np.linalg.norm(vec3(3.0, 4.0, 12.0) - vec3(0.0, 0.0, 0.0)) == pytest.approx(
        13.0
    )


def test_np_vec3_distance_to_self_is_zero():
    v = vec3(7.5, -2.25, 3.0)
    assert np.linalg.norm(v - v) == 0.0


def test_np_vec3_distance_is_symmetric():
    a, b = vec3(1.0, 2.0, 3.0), vec3(4.0, 6.0, 15.0)
    assert np.linalg.norm(b - a) == pytest.approx(np.linalg.norm(a - b))


# ---------------------------------------------------------------------------
# np dot (Vec2.dot equivalent)
# ---------------------------------------------------------------------------


def test_np_vec2_dot_of_orthogonal_vectors_is_zero():
    assert np.dot(vec2(1.0, 0.0), vec2(0.0, 1.0)) == 0.0


def test_np_vec2_dot_of_vector_with_itself_is_squared_length():
    v = vec2(3.0, 4.0)
    assert np.dot(v, v) == pytest.approx(np.sum(v**2))


def test_np_vec2_dot_of_opposite_vectors_is_negative():
    assert np.dot(vec2(1.0, 0.0), vec2(-1.0, 0.0)) == -1.0


# ---------------------------------------------------------------------------
# np dot (Vec3.dot equivalent)
# ---------------------------------------------------------------------------


def test_np_vec3_dot_of_orthogonal_vectors_is_zero():
    assert np.dot(vec3(1.0, 0.0, 0.0), vec3(0.0, 1.0, 0.0)) == 0.0


def test_np_vec3_dot_of_vector_with_itself_is_squared_length():
    v = vec3(3.0, 4.0, 12.0)
    assert np.dot(v, v) == pytest.approx(np.sum(v**2))


def test_np_vec3_dot_of_opposite_vectors_is_negative():
    assert np.dot(vec3(1.0, 0.0, 0.0), vec3(-1.0, 0.0, 0.0)) == -1.0


# ---------------------------------------------------------------------------
# np length / linalg.norm (Vec2.length equivalent)
# ---------------------------------------------------------------------------


def test_np_vec2_length_of_3_4_vector_is_5():
    assert np.linalg.norm(vec2(3.0, 4.0)) == pytest.approx(5.0)


def test_np_vec2_length_of_zero_vector_is_zero():
    assert np.linalg.norm(vec2(0.0, 0.0)) == 0.0


def test_np_vec2_length_ignores_sign_of_components():
    assert np.linalg.norm(vec2(-3.0, -4.0)) == pytest.approx(5.0)


# ---------------------------------------------------------------------------
# np length / linalg.norm (Vec3.length equivalent)
# ---------------------------------------------------------------------------


def test_np_vec3_length_matches_pythagorean_3_4_12_13():
    assert np.linalg.norm(vec3(3.0, 4.0, 12.0)) == pytest.approx(13.0)


def test_np_vec3_length_of_zero_vector_is_zero():
    assert np.linalg.norm(vec3(0.0, 0.0, 0.0)) == 0.0


def test_np_vec3_length_ignores_sign_of_components():
    assert np.linalg.norm(vec3(-3.0, -4.0, -12.0)) == pytest.approx(13.0)


# ---------------------------------------------------------------------------
# np normalize (Vec2.normalize equivalent)
# ---------------------------------------------------------------------------


def _np_normalize(v):
    length = np.linalg.norm(v)
    if length > 0:
        return v / length
    return np.zeros_like(v)


def test_np_vec2_normalize_produces_unit_length_vector():
    v = _np_normalize(vec2(3.0, 4.0))
    assert np.linalg.norm(v) == pytest.approx(1.0)
    assert v == pytest.approx((0.6, 0.8))


def test_np_vec2_normalize_of_zero_vector_returns_zero_vector():
    assert np.array_equal(_np_normalize(vec2(0.0, 0.0)), vec2(0.0, 0.0))


def test_np_vec2_normalize_of_already_unit_vector_is_unchanged():
    v = vec2(1.0, 0.0)
    assert _np_normalize(v) == pytest.approx(v)


# ---------------------------------------------------------------------------
# np normalize (Vec3.normalize equivalent)
# ---------------------------------------------------------------------------


def test_np_vec3_normalize_produces_unit_length_vector():
    v = _np_normalize(vec3(3.0, 4.0, 12.0))
    assert np.linalg.norm(v) == pytest.approx(1.0)
    assert v == pytest.approx((3 / 13, 4 / 13, 12 / 13))


def test_np_vec3_normalize_of_zero_vector_returns_zero_vector():
    assert np.array_equal(_np_normalize(vec3(0.0, 0.0, 0.0)), vec3(0.0, 0.0, 0.0))


def test_np_vec3_normalize_of_already_unit_vector_is_unchanged():
    v = vec3(0.0, 1.0, 0.0)
    assert _np_normalize(v) == pytest.approx(v)


# ---------------------------------------------------------------------------
# np squared distance (Vec2.squaredDistance equivalent)
# ---------------------------------------------------------------------------


def test_np_vec2_squared_distance_matches_distance_squared():
    a, b = vec2(1.0, 2.0), vec2(4.0, 6.0)
    squared_distance = np.sum((b - a) ** 2)
    assert squared_distance == pytest.approx(np.linalg.norm(b - a) ** 2)


def test_np_vec2_squared_distance_to_self_is_zero():
    v = vec2(3.0, -4.0)
    assert np.sum((v - v) ** 2) == 0.0


# ---------------------------------------------------------------------------
# np squared distance (Vec3.squaredDistance equivalent)
# ---------------------------------------------------------------------------


def test_np_vec3_squared_distance_matches_distance_squared():
    a, b = vec3(1.0, 2.0, 3.0), vec3(4.0, 6.0, 15.0)
    squared_distance = np.sum((b - a) ** 2)
    assert squared_distance == pytest.approx(np.linalg.norm(b - a) ** 2)


def test_np_vec3_squared_distance_to_self_is_zero():
    v = vec3(3.0, -4.0, 5.0)
    assert np.sum((v - v) ** 2) == 0.0


# ---------------------------------------------------------------------------
# np squared length (Vec2.squaredLength equivalent)
# ---------------------------------------------------------------------------


def test_np_vec2_squared_length_matches_length_squared():
    v = vec2(3.0, 4.0)
    assert np.sum(v**2) == pytest.approx(np.linalg.norm(v) ** 2)


def test_np_vec2_squared_length_of_zero_vector_is_zero():
    assert np.sum(vec2(0.0, 0.0) ** 2) == 0.0


# ---------------------------------------------------------------------------
# np squared length (Vec3.squaredLength equivalent)
# ---------------------------------------------------------------------------


def test_np_vec3_squared_length_matches_length_squared():
    v = vec3(3.0, 4.0, 12.0)
    assert np.sum(v**2) == pytest.approx(np.linalg.norm(v) ** 2)


def test_np_vec3_squared_length_of_zero_vector_is_zero():
    assert np.sum(vec3(0.0, 0.0, 0.0) ** 2) == 0.0


# ---------------------------------------------------------------------------
# np determinant (Mat3.determinant equivalent)
# ---------------------------------------------------------------------------


def test_np_mat3_determinant_of_identity_is_one():
    identity = np.eye(3)
    assert np.linalg.det(identity) == pytest.approx(1.0)


def test_np_mat3_determinant_of_general_matrix():
    m = np.array([[1.0, 2.0, 3.0], [0.0, 1.0, 4.0], [5.0, 6.0, 0.0]])
    assert np.linalg.det(m) == pytest.approx(1.0)


def test_np_mat3_determinant_of_singular_matrix_is_zero():
    m = np.array([[1.0, 2.0, 3.0], [2.0, 4.0, 6.0], [0.0, 1.0, 1.0]])
    assert np.linalg.det(m) == pytest.approx(0.0)


def test_np_mat3_determinant_of_zero_matrix_is_zero():
    m = np.zeros((3, 3))
    assert np.linalg.det(m) == pytest.approx(0.0)


def test_np_mat3_determinant_swapping_two_rows_negates_result():
    m = np.array([[1.0, 2.0, 3.0], [0.0, 1.0, 4.0], [5.0, 6.0, 0.0]])
    swapped = m[[1, 0, 2]]
    assert np.linalg.det(swapped) == pytest.approx(-np.linalg.det(m))


# ---------------------------------------------------------------------------
# np coplanar (Geom.coplanar equivalent)
# ---------------------------------------------------------------------------


def _np_coplanar(points):
    """numpy equivalent of Geom.coplanar: True if fewer than 4 points, else
    checks that every point beyond the first three lies on the plane defined
    by them."""
    if len(points) < 4:
        return True
    v0, v1, v2 = points[0], points[1], points[2]
    normal = np.cross(v1 - v0, v2 - v0)
    for v in points[3:]:
        if abs(np.dot(normal, v - v0)) > 1e-6:
            return False
    return True


def test_np_coplanar_of_empty_list_is_true():
    assert _np_coplanar([]) is True


def test_np_coplanar_of_single_point_is_true():
    assert _np_coplanar([vec3(0.0, 0.0, 0.0)]) is True


def test_np_coplanar_of_two_points_is_true():
    assert _np_coplanar([vec3(0.0, 0.0, 0.0), vec3(1.0, 0.0, 0.0)]) is True


def test_np_coplanar_of_three_points_is_true():
    assert (
        _np_coplanar([vec3(0.0, 0.0, 0.0), vec3(1.0, 0.0, 0.0), vec3(0.0, 1.0, 0.0)])
        is True
    )


def test_np_coplanar_of_four_points_on_the_same_plane_is_true():
    square = [
        vec3(0.0, 0.0, 0.0),
        vec3(1.0, 0.0, 0.0),
        vec3(1.0, 1.0, 0.0),
        vec3(0.0, 1.0, 0.0),
    ]
    assert _np_coplanar(square) is True


def test_np_coplanar_of_four_points_not_on_the_same_plane_is_false():
    non_planar = [
        vec3(0.0, 0.0, 0.0),
        vec3(1.0, 0.0, 0.0),
        vec3(0.0, 1.0, 0.0),
        vec3(0.0, 0.0, 1.0),
    ]
    assert _np_coplanar(non_planar) is False


def test_np_coplanar_of_points_on_a_tilted_plane_is_true():
    tilted = [
        vec3(0.0, 0.0, 0.0),
        vec3(1.0, 0.0, 1.0),
        vec3(0.0, 1.0, 1.0),
        vec3(1.0, 1.0, 2.0),
    ]
    assert _np_coplanar(tilted) is True


# ---------------------------------------------------------------------------
# Benchmarks -- one dedicated benchmark per numpy-equivalent operation,
# each timing a single representative call (not a batch), matching the
# per-function benchmarks in test_vec.py one-for-one for direct comparison.
# ---------------------------------------------------------------------------

_A2 = vec2(3.0, 4.0)
_B2 = vec2(5.0, 6.0)
_A3 = vec3(3.0, 4.0, 12.0)
_B3 = vec3(5.0, 6.0, 7.0)


def _np_normalize(v):
    length = np.linalg.norm(v)
    if length > 0:
        return v / length
    return np.zeros_like(v)


def test_benchmark_np_vec2_abs(benchmark):
    result = benchmark(np.abs, _A2)
    assert np.array_equal(result, vec2(3.0, 4.0))


def test_benchmark_np_vec2_add(benchmark):
    result = benchmark(np.add, _A2, _B2)
    assert np.array_equal(result, vec2(8.0, 10.0))


def test_benchmark_np_vec2_mul(benchmark):
    result = benchmark(np.multiply, _A2, _B2)
    assert np.array_equal(result, vec2(15.0, 24.0))


def test_benchmark_np_vec2_neg(benchmark):
    result = benchmark(np.negative, _A2)
    assert np.array_equal(result, vec2(-3.0, -4.0))


def test_benchmark_np_vec2_pos(benchmark):
    result = benchmark(np.positive, _A2)
    assert np.array_equal(result, _A2)


def test_benchmark_np_vec2_sub(benchmark):
    result = benchmark(np.subtract, _A2, _B2)
    assert np.array_equal(result, vec2(-2.0, -2.0))


def test_benchmark_np_vec2_truediv(benchmark):
    result = benchmark(np.divide, _A2, _B2)
    assert result == pytest.approx((3.0 / 5.0, 4.0 / 6.0))


def test_benchmark_np_vec2_cross(benchmark):
    result = benchmark(_cross2d, _A2, _B2)
    assert np.array_equal(result, vec3(0.0, 0.0, 3.0 * 6.0 - 4.0 * 5.0))


def test_benchmark_np_vec2_distance(benchmark):
    result = benchmark(lambda a, b: np.linalg.norm(b - a), _A2, _B2)
    assert result == pytest.approx(np.linalg.norm(_B2 - _A2))


def test_benchmark_np_vec2_dot(benchmark):
    result = benchmark(np.dot, _A2, _B2)
    assert result == pytest.approx(3.0 * 5.0 + 4.0 * 6.0)


def test_benchmark_np_vec2_length(benchmark):
    result = benchmark(np.linalg.norm, _A2)
    assert result == pytest.approx(5.0)


def test_benchmark_np_vec2_normalize(benchmark):
    result = benchmark(_np_normalize, _A2)
    assert np.linalg.norm(result) == pytest.approx(1.0)


def test_benchmark_np_vec2_squared_distance(benchmark):
    result = benchmark(lambda a, b: np.sum((b - a) ** 2), _A2, _B2)
    assert result == pytest.approx(np.linalg.norm(_B2 - _A2) ** 2)


def test_benchmark_np_vec2_squared_length(benchmark):
    result = benchmark(lambda v: np.sum(v**2), _A2)
    assert result == pytest.approx(25.0)


def test_benchmark_np_vec3_abs(benchmark):
    result = benchmark(np.abs, _A3)
    assert np.array_equal(result, vec3(3.0, 4.0, 12.0))


def test_benchmark_np_vec3_add(benchmark):
    result = benchmark(np.add, _A3, _B3)
    assert np.array_equal(result, vec3(8.0, 10.0, 19.0))


def test_benchmark_np_vec3_mul(benchmark):
    result = benchmark(np.multiply, _A3, _B3)
    assert np.array_equal(result, vec3(15.0, 24.0, 84.0))


def test_benchmark_np_vec3_neg(benchmark):
    result = benchmark(np.negative, _A3)
    assert np.array_equal(result, vec3(-3.0, -4.0, -12.0))


def test_benchmark_np_vec3_pos(benchmark):
    result = benchmark(np.positive, _A3)
    assert np.array_equal(result, _A3)


def test_benchmark_np_vec3_sub(benchmark):
    result = benchmark(np.subtract, _A3, _B3)
    assert np.array_equal(result, vec3(-2.0, -2.0, 5.0))


def test_benchmark_np_vec3_truediv(benchmark):
    result = benchmark(np.divide, _A3, _B3)
    assert result == pytest.approx((3.0 / 5.0, 4.0 / 6.0, 12.0 / 7.0))


def test_benchmark_np_vec3_cross(benchmark):
    result = benchmark(np.cross, _A3, _B3)
    assert result == pytest.approx(
        (4.0 * 7.0 - 12.0 * 6.0, 12.0 * 5.0 - 3.0 * 7.0, 3.0 * 6.0 - 4.0 * 5.0)
    )


def test_benchmark_np_vec3_distance(benchmark):
    result = benchmark(lambda a, b: np.linalg.norm(b - a), _A3, _B3)
    assert result == pytest.approx(np.linalg.norm(_B3 - _A3))


def test_benchmark_np_vec3_dot(benchmark):
    result = benchmark(np.dot, _A3, _B3)
    assert result == pytest.approx(3.0 * 5.0 + 4.0 * 6.0 + 12.0 * 7.0)


def test_benchmark_np_vec3_length(benchmark):
    result = benchmark(np.linalg.norm, _A3)
    assert result == pytest.approx(13.0)


def test_benchmark_np_vec3_normalize(benchmark):
    result = benchmark(_np_normalize, _A3)
    assert np.linalg.norm(result) == pytest.approx(1.0)


def test_benchmark_np_vec3_squared_distance(benchmark):
    result = benchmark(lambda a, b: np.sum((b - a) ** 2), _A3, _B3)
    assert result == pytest.approx(np.linalg.norm(_B3 - _A3) ** 2)


def test_benchmark_np_vec3_squared_length(benchmark):
    result = benchmark(lambda v: np.sum(v**2), _A3)
    assert result == pytest.approx(169.0)


_M3 = np.array([[1.0, 2.0, 3.0], [0.0, 1.0, 4.0], [5.0, 6.0, 0.0]])
_COPLANAR_PTS = [
    vec3(0.0, 0.0, 0.0),
    vec3(1.0, 0.0, 0.0),
    vec3(1.0, 1.0, 0.0),
    vec3(0.0, 1.0, 0.0),
]


def test_benchmark_np_mat3_determinant(benchmark):
    result = benchmark(np.linalg.det, _M3)
    assert result == pytest.approx(1.0)


def test_benchmark_np_coplanar(benchmark):
    result = benchmark(_np_coplanar, _COPLANAR_PTS)
    assert result is True

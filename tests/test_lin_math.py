"""
Pytest (+ pytest-benchmark) tests for every Vec2/Vec3 function in vec.py.

Unlike a typical vector library, vec.py does not define vector *classes*
for the data itself -- vectors are plain tuples (2-tuples for Vec2,
3-tuples for Vec3). `Vec2`/`Vec3` are simple namespaces whose attributes
are ordinary functions taking those tuples as arguments (e.g.
`Vec2.add(a, b)`), avoiding the overhead of instantiating a wrapper
object per vector.

vec.py lives at the repository root (it is not part of the installed
`piecad` package), so it is imported directly by file path below.

Test names include "vec" so they can be compared against the
equivalent "np" (numpy) tests in test_npvec.py. Each vec.py function has
its own dedicated benchmark test so individual function costs can be
compared directly against their numpy counterpart.
"""

import sys
from pathlib import Path

import pytest
from piecad.lin_math import *

# ---------------------------------------------------------------------------
# Vec2.abs
# ---------------------------------------------------------------------------


def test_vec2_abs_of_positive_vector_is_unchanged():
    assert Vec2.abs((3.0, 4.0)) == (3.0, 4.0)


def test_vec2_abs_of_negative_vector_flips_both_signs():
    assert Vec2.abs((-3.0, -4.0)) == (3.0, 4.0)


def test_vec2_abs_of_mixed_sign_vector_is_component_wise():
    assert Vec2.abs((-3.0, 4.0)) == (3.0, 4.0)


def test_vec2_abs_of_zero_vector_is_zero():
    assert Vec2.abs((0.0, 0.0)) == (0.0, 0.0)


# ---------------------------------------------------------------------------
# Vec3.abs
# ---------------------------------------------------------------------------


def test_vec3_abs_of_positive_vector_is_unchanged():
    assert Vec3.abs((3.0, 4.0, 5.0)) == (3.0, 4.0, 5.0)


def test_vec3_abs_of_negative_vector_flips_all_signs():
    assert Vec3.abs((-3.0, -4.0, -5.0)) == (3.0, 4.0, 5.0)


def test_vec3_abs_of_mixed_sign_vector_is_component_wise():
    assert Vec3.abs((-3.0, 4.0, -5.0)) == (3.0, 4.0, 5.0)


def test_vec3_abs_of_zero_vector_is_zero():
    assert Vec3.abs((0.0, 0.0, 0.0)) == (0.0, 0.0, 0.0)


# ---------------------------------------------------------------------------
# Vec2.add
# ---------------------------------------------------------------------------


def test_vec2_add_combines_components():
    assert Vec2.add((1.0, 2.0), (3.0, 4.0)) == (4.0, 6.0)


def test_vec2_add_with_negative_operand_subtracts_effectively():
    assert Vec2.add((1.0, 2.0), (-1.0, -2.0)) == (0.0, 0.0)


def test_vec2_add_with_zero_vector_is_identity():
    v = (5.5, -2.25)
    assert Vec2.add(v, (0.0, 0.0)) == v


# ---------------------------------------------------------------------------
# Vec3.add
# ---------------------------------------------------------------------------


def test_vec3_add_combines_components():
    assert Vec3.add((1.0, 2.0, 3.0), (4.0, 5.0, 6.0)) == (5.0, 7.0, 9.0)


def test_vec3_add_with_negative_operand_subtracts_effectively():
    assert Vec3.add((1.0, 2.0, 3.0), (-1.0, -2.0, -3.0)) == (0.0, 0.0, 0.0)


def test_vec3_add_with_zero_vector_is_identity():
    v = (5.5, -2.25, 3.0)
    assert Vec3.add(v, (0.0, 0.0, 0.0)) == v


# ---------------------------------------------------------------------------
# Vec2.mul
# ---------------------------------------------------------------------------


def test_vec2_mul_is_component_wise():
    assert Vec2.mul((2.0, 3.0), (4.0, 5.0)) == (8.0, 15.0)


def test_vec2_mul_by_zero_vector_is_zero():
    assert Vec2.mul((2.0, 3.0), (0.0, 0.0)) == (0.0, 0.0)


def test_vec2_mul_by_negative_one_negates_vector():
    assert Vec2.mul((2.0, -3.0), (-1.0, -1.0)) == (-2.0, 3.0)


# ---------------------------------------------------------------------------
# Vec3.mul
# ---------------------------------------------------------------------------


def test_vec3_mul_is_component_wise():
    assert Vec3.mul((2.0, 3.0, 4.0), (5.0, 6.0, 7.0)) == (10.0, 18.0, 28.0)


def test_vec3_mul_by_zero_vector_is_zero():
    assert Vec3.mul((2.0, 3.0, 4.0), (0.0, 0.0, 0.0)) == (0.0, 0.0, 0.0)


def test_vec3_mul_by_negative_one_negates_vector():
    assert Vec3.mul((2.0, -3.0, 4.0), (-1.0, -1.0, -1.0)) == (-2.0, 3.0, -4.0)


# ---------------------------------------------------------------------------
# Vec2.neg
# ---------------------------------------------------------------------------


def test_vec2_neg_flips_sign_of_both_components():
    assert Vec2.neg((3.0, -4.0)) == (-3.0, 4.0)


def test_vec2_neg_of_zero_vector_is_zero():
    assert Vec2.neg((0.0, 0.0)) == (0.0, 0.0)


def test_vec2_neg_applied_twice_returns_original():
    v = (3.0, -4.0)
    assert Vec2.neg(Vec2.neg(v)) == v


# ---------------------------------------------------------------------------
# Vec3.neg
# ---------------------------------------------------------------------------


def test_vec3_neg_flips_sign_of_all_components():
    assert Vec3.neg((3.0, -4.0, 5.0)) == (-3.0, 4.0, -5.0)


def test_vec3_neg_of_zero_vector_is_zero():
    assert Vec3.neg((0.0, 0.0, 0.0)) == (0.0, 0.0, 0.0)


def test_vec3_neg_applied_twice_returns_original():
    v = (3.0, -4.0, 5.0)
    assert Vec3.neg(Vec3.neg(v)) == v


# ---------------------------------------------------------------------------
# Vec2.pos
# ---------------------------------------------------------------------------


def test_vec2_pos_returns_the_same_object():
    v = (3.0, -4.0)
    assert Vec2.pos(v) is v


def test_vec2_pos_of_zero_vector_is_zero():
    assert Vec2.pos((0.0, 0.0)) == (0.0, 0.0)


# ---------------------------------------------------------------------------
# Vec3.pos
# ---------------------------------------------------------------------------


def test_vec3_pos_returns_the_same_object():
    v = (3.0, -4.0, 5.0)
    assert Vec3.pos(v) is v


def test_vec3_pos_of_zero_vector_is_zero():
    assert Vec3.pos((0.0, 0.0, 0.0)) == (0.0, 0.0, 0.0)


# ---------------------------------------------------------------------------
# Vec2.sub
# ---------------------------------------------------------------------------


def test_vec2_sub_combines_components():
    assert Vec2.sub((5.0, 7.0), (2.0, 3.0)) == (3.0, 4.0)


def test_vec2_sub_of_a_vector_with_itself_is_zero():
    v = (9.5, -3.25)
    assert Vec2.sub(v, v) == (0.0, 0.0)


def test_vec2_sub_from_zero_vector_negates_operand():
    assert Vec2.sub((0.0, 0.0), (3.0, -4.0)) == (-3.0, 4.0)


# ---------------------------------------------------------------------------
# Vec3.sub
# ---------------------------------------------------------------------------


def test_vec3_sub_combines_components():
    assert Vec3.sub((5.0, 7.0, 9.0), (1.0, 2.0, 3.0)) == (4.0, 5.0, 6.0)


def test_vec3_sub_of_a_vector_with_itself_is_zero():
    v = (9.5, -3.25, 1.0)
    assert Vec3.sub(v, v) == (0.0, 0.0, 0.0)


def test_vec3_sub_from_zero_vector_negates_operand():
    assert Vec3.sub((0.0, 0.0, 0.0), (3.0, -4.0, 5.0)) == (-3.0, 4.0, -5.0)


# ---------------------------------------------------------------------------
# Vec2.dev
# ---------------------------------------------------------------------------


def test_vec2_div_is_component_wise():
    assert Vec2.div((8.0, 9.0), (2.0, 3.0)) == (4.0, 3.0)


def test_vec2_div_by_one_is_identity():
    v = (7.5, -2.25)
    assert Vec2.div(v, (1.0, 1.0)) == v


def test_vec2_div_by_zero_raises_zero_division_error():
    with pytest.raises(ZeroDivisionError):
        Vec2.div((1.0, 1.0), (0.0, 1.0))


# ---------------------------------------------------------------------------
# Vec3.div
# ---------------------------------------------------------------------------


def test_vec3_div_is_component_wise():
    assert Vec3.div((8.0, 9.0, 10.0), (2.0, 3.0, 5.0)) == (4.0, 3.0, 2.0)


def test_vec3_div_by_one_is_identity():
    v = (7.5, -2.25, 3.0)
    assert Vec3.div(v, (1.0, 1.0, 1.0)) == v


def test_vec3_div_by_zero_raises_zero_division_error():
    with pytest.raises(ZeroDivisionError):
        Vec3.div((1.0, 1.0, 1.0), (0.0, 1.0, 1.0))


# ---------------------------------------------------------------------------
# Vec2.cross
# ---------------------------------------------------------------------------


def test_vec2_cross_of_orthogonal_unit_vectors_is_positive_z():
    assert Vec2.cross((1.0, 0.0), (0.0, 1.0)) == (0, 0, 1.0)


def test_vec2_cross_of_parallel_vectors_is_zero():
    assert Vec2.cross((2.0, 4.0), (1.0, 2.0)) == (0, 0, 0.0)


def test_vec2_cross_returns_a_3_tuple():
    result = Vec2.cross((3.0, 4.0), (5.0, 6.0))
    assert len(result) == 3


def test_vec2_cross_is_anti_commutative():
    a, b = (3.0, 4.0), (5.0, 6.0)
    forward = Vec2.cross(a, b)
    backward = Vec2.cross(b, a)
    assert forward[2] == -backward[2]


# ---------------------------------------------------------------------------
# Vec3.cross
# ---------------------------------------------------------------------------


def test_vec3_cross_of_x_and_y_axes_is_z_axis():
    assert Vec3.cross((1.0, 0.0, 0.0), (0.0, 1.0, 0.0)) == (0.0, 0.0, 1.0)


def test_vec3_cross_of_parallel_vectors_is_zero():
    assert Vec3.cross((2.0, 4.0, 6.0), (1.0, 2.0, 3.0)) == (0.0, 0.0, 0.0)


def test_vec3_cross_returns_a_3_tuple():
    result = Vec3.cross((3.0, 4.0, 5.0), (5.0, 6.0, 7.0))
    assert len(result) == 3


def test_vec3_cross_is_anti_commutative():
    a, b = (3.0, 4.0, 5.0), (5.0, 6.0, 7.0)
    forward = Vec3.cross(a, b)
    backward = Vec3.cross(b, a)
    assert forward == Vec3.neg(backward)


# ---------------------------------------------------------------------------
# Vec2.distance
# ---------------------------------------------------------------------------


def test_vec2_distance_between_a_3_4_5_triangle():
    assert Vec2.distance((0.0, 0.0), (3.0, 4.0)) == pytest.approx(5.0)


def test_vec2_distance_to_self_is_zero():
    v = (7.5, -2.25)
    assert Vec2.distance(v, v) == 0.0


def test_vec2_distance_is_symmetric():
    a, b = (1.0, 2.0), (4.0, 6.0)
    assert Vec2.distance(a, b) == pytest.approx(Vec2.distance(b, a))


# ---------------------------------------------------------------------------
# Vec3.distance
# ---------------------------------------------------------------------------


def test_vec3_distance_matches_pythagorean_3_4_12_13():
    assert Vec3.distance((0.0, 0.0, 0.0), (3.0, 4.0, 12.0)) == pytest.approx(13.0)


def test_vec3_distance_to_self_is_zero():
    v = (7.5, -2.25, 3.0)
    assert Vec3.distance(v, v) == 0.0


def test_vec3_distance_is_symmetric():
    a, b = (1.0, 2.0, 3.0), (4.0, 6.0, 15.0)
    assert Vec3.distance(a, b) == pytest.approx(Vec3.distance(b, a))


# ---------------------------------------------------------------------------
# Vec2.dot
# ---------------------------------------------------------------------------


def test_vec2_dot_of_orthogonal_vectors_is_zero():
    assert Vec2.dot((1.0, 0.0), (0.0, 1.0)) == 0.0


def test_vec2_dot_of_vector_with_itself_is_squared_length():
    v = (3.0, 4.0)
    assert Vec2.dot(v, v) == pytest.approx(Vec2.squaredLength(v))


def test_vec2_dot_of_opposite_vectors_is_negative():
    assert Vec2.dot((1.0, 0.0), (-1.0, 0.0)) == -1.0


# ---------------------------------------------------------------------------
# Vec3.dot
# ---------------------------------------------------------------------------


def test_vec3_dot_of_orthogonal_vectors_is_zero():
    assert Vec3.dot((1.0, 0.0, 0.0), (0.0, 1.0, 0.0)) == 0.0


def test_vec3_dot_of_vector_with_itself_is_squared_length():
    v = (3.0, 4.0, 12.0)
    assert Vec3.dot(v, v) == pytest.approx(Vec3.squaredLength(v))


def test_vec3_dot_of_opposite_vectors_is_negative():
    assert Vec3.dot((1.0, 0.0, 0.0), (-1.0, 0.0, 0.0)) == -1.0


# ---------------------------------------------------------------------------
# Vec2.length
# ---------------------------------------------------------------------------


def test_vec2_length_of_3_4_vector_is_5():
    assert Vec2.length((3.0, 4.0)) == pytest.approx(5.0)


def test_vec2_length_of_zero_vector_is_zero():
    assert Vec2.length((0.0, 0.0)) == 0.0


def test_vec2_length_ignores_sign_of_components():
    assert Vec2.length((-3.0, -4.0)) == pytest.approx(5.0)


# ---------------------------------------------------------------------------
# Vec3.length
# ---------------------------------------------------------------------------


def test_vec3_length_matches_pythagorean_3_4_12_13():
    assert Vec3.length((3.0, 4.0, 12.0)) == pytest.approx(13.0)


def test_vec3_length_of_zero_vector_is_zero():
    assert Vec3.length((0.0, 0.0, 0.0)) == 0.0


def test_vec3_length_ignores_sign_of_components():
    assert Vec3.length((-3.0, -4.0, -12.0)) == pytest.approx(13.0)


# ---------------------------------------------------------------------------
# Vec2.normalize
# ---------------------------------------------------------------------------


def test_vec2_normalize_produces_unit_length_vector():
    v = Vec2.normalize((3.0, 4.0))
    assert Vec2.length(v) == pytest.approx(1.0)
    assert v == pytest.approx((0.6, 0.8))


def test_vec2_normalize_of_zero_vector_returns_zero_vector():
    assert Vec2.normalize((0.0, 0.0)) == (0, 0)


def test_vec2_normalize_of_already_unit_vector_is_unchanged():
    v = (1.0, 0.0)
    assert Vec2.normalize(v) == pytest.approx(v)


# ---------------------------------------------------------------------------
# Vec3.normalize
# ---------------------------------------------------------------------------


def test_vec3_normalize_produces_unit_length_vector():
    v = Vec3.normalize((3.0, 4.0, 12.0))
    assert Vec3.length(v) == pytest.approx(1.0)
    assert v == pytest.approx((3 / 13, 4 / 13, 12 / 13))


def test_vec3_normalize_of_zero_vector_returns_zero_vector():
    assert Vec3.normalize((0.0, 0.0, 0.0)) == (0, 0, 0)


def test_vec3_normalize_of_already_unit_vector_is_unchanged():
    v = (0.0, 1.0, 0.0)
    assert Vec3.normalize(v) == pytest.approx(v)


# ---------------------------------------------------------------------------
# Vec2.squaredDistance
# ---------------------------------------------------------------------------


def test_vec2_squared_distance_matches_distance_squared():
    a, b = (1.0, 2.0), (4.0, 6.0)
    assert Vec2.squaredDistance(a, b) == pytest.approx(Vec2.distance(a, b) ** 2)


def test_vec2_squared_distance_to_self_is_zero():
    v = (3.0, -4.0)
    assert Vec2.squaredDistance(v, v) == 0.0


# ---------------------------------------------------------------------------
# Vec3.squaredDistance
# ---------------------------------------------------------------------------


def test_vec3_squared_distance_matches_distance_squared():
    a, b = (1.0, 2.0, 3.0), (4.0, 6.0, 15.0)
    assert Vec3.squaredDistance(a, b) == pytest.approx(Vec3.distance(a, b) ** 2)


def test_vec3_squared_distance_to_self_is_zero():
    v = (3.0, -4.0, 5.0)
    assert Vec3.squaredDistance(v, v) == 0.0


# ---------------------------------------------------------------------------
# Vec2.squaredLength
# ---------------------------------------------------------------------------


def test_vec2_squared_length_matches_length_squared():
    v = (3.0, 4.0)
    assert Vec2.squaredLength(v) == pytest.approx(Vec2.length(v) ** 2)


def test_vec2_squared_length_of_zero_vector_is_zero():
    assert Vec2.squaredLength((0.0, 0.0)) == 0.0


# ---------------------------------------------------------------------------
# Vec3.squaredLength
# ---------------------------------------------------------------------------


def test_vec3_squared_length_matches_length_squared():
    v = (3.0, 4.0, 12.0)
    assert Vec3.squaredLength(v) == pytest.approx(Vec3.length(v) ** 2)


def test_vec3_squared_length_of_zero_vector_is_zero():
    assert Vec3.squaredLength((0.0, 0.0, 0.0)) == 0.0


# ---------------------------------------------------------------------------
# Mat3.determinant
# ---------------------------------------------------------------------------


def test_mat3_determinant_of_identity_is_one():
    identity = [(1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)]
    assert Mat3.determinant(identity) == pytest.approx(1.0)


def test_mat3_determinant_of_general_matrix():
    m = [(1.0, 2.0, 3.0), (0.0, 1.0, 4.0), (5.0, 6.0, 0.0)]
    assert Mat3.determinant(m) == pytest.approx(1.0)


def test_mat3_determinant_of_singular_matrix_is_zero():
    m = [(1.0, 2.0, 3.0), (2.0, 4.0, 6.0), (0.0, 1.0, 1.0)]
    assert Mat3.determinant(m) == pytest.approx(0.0)


def test_mat3_determinant_of_zero_matrix_is_zero():
    m = [(0.0, 0.0, 0.0), (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)]
    assert Mat3.determinant(m) == pytest.approx(0.0)


def test_mat3_determinant_swapping_two_rows_negates_result():
    m = [(1.0, 2.0, 3.0), (0.0, 1.0, 4.0), (5.0, 6.0, 0.0)]
    swapped = [m[1], m[0], m[2]]
    assert Mat3.determinant(swapped) == pytest.approx(-Mat3.determinant(m))


# ---------------------------------------------------------------------------
# Geom.coplanar
# ---------------------------------------------------------------------------


def test_geom_coplanar_of_empty_list_is_true():
    assert Geom.coplanar([]) is True


def test_geom_coplanar_of_single_point_is_true():
    assert Geom.coplanar([(0.0, 0.0, 0.0)]) is True


def test_geom_coplanar_of_two_points_is_true():
    assert Geom.coplanar([(0.0, 0.0, 0.0), (1.0, 0.0, 0.0)]) is True


def test_geom_coplanar_of_three_points_is_true():
    assert Geom.coplanar([(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)]) is True


def test_geom_coplanar_of_four_points_on_the_same_plane_is_true():
    square = [
        (0.0, 0.0, 0.0),
        (1.0, 0.0, 0.0),
        (1.0, 1.0, 0.0),
        (0.0, 1.0, 0.0),
    ]
    assert Geom.coplanar(square) is True


def test_geom_coplanar_of_four_points_not_on_the_same_plane_is_false():
    non_planar = [
        (0.0, 0.0, 0.0),
        (1.0, 0.0, 0.0),
        (0.0, 1.0, 0.0),
        (0.0, 0.0, 1.0),
    ]
    assert Geom.coplanar(non_planar) is False


def test_geom_coplanar_of_points_on_a_tilted_plane_is_true():
    tilted = [
        (0.0, 0.0, 0.0),
        (1.0, 0.0, 1.0),
        (0.0, 1.0, 1.0),
        (1.0, 1.0, 2.0),
    ]
    assert Geom.coplanar(tilted) is True


# ---------------------------------------------------------------------------
# Benchmarks -- one dedicated benchmark per Vec2/Vec3 function, each timing
# a single representative call (not a batch), so every function's cost can
# be compared individually against its numpy equivalent in test_npvec.py.
# ---------------------------------------------------------------------------

_A2 = (3.0, 4.0)
_B2 = (5.0, 6.0)
_A3 = (3.0, 4.0, 12.0)
_B3 = (5.0, 6.0, 7.0)


def test_benchmark_vec2_abs(benchmark):
    result = benchmark(Vec2.abs, _A2)
    assert result == (3.0, 4.0)


def test_benchmark_vec2_add(benchmark):
    result = benchmark(Vec2.add, _A2, _B2)
    assert result == (8.0, 10.0)


def test_benchmark_vec2_mul(benchmark):
    result = benchmark(Vec2.mul, _A2, _B2)
    assert result == (15.0, 24.0)


def test_benchmark_vec2_neg(benchmark):
    result = benchmark(Vec2.neg, _A2)
    assert result == (-3.0, -4.0)


def test_benchmark_vec2_pos(benchmark):
    result = benchmark(Vec2.pos, _A2)
    assert result == _A2


def test_benchmark_vec2_sub(benchmark):
    result = benchmark(Vec2.sub, _A2, _B2)
    assert result == (-2.0, -2.0)


def test_benchmark_vec2_div(benchmark):
    result = benchmark(Vec2.div, _A2, _B2)
    assert result == pytest.approx((3.0 / 5.0, 4.0 / 6.0))


def test_benchmark_vec2_cross(benchmark):
    result = benchmark(Vec2.cross, _A2, _B2)
    assert result == (0, 0, 3.0 * 6.0 - 4.0 * 5.0)


def test_benchmark_vec2_distance(benchmark):
    result = benchmark(Vec2.distance, _A2, _B2)
    assert result == pytest.approx(Vec2.length(Vec2.sub(_B2, _A2)))


def test_benchmark_vec2_dot(benchmark):
    result = benchmark(Vec2.dot, _A2, _B2)
    assert result == pytest.approx(3.0 * 5.0 + 4.0 * 6.0)


def test_benchmark_vec2_length(benchmark):
    result = benchmark(Vec2.length, _A2)
    assert result == pytest.approx(5.0)


def test_benchmark_vec2_normalize(benchmark):
    result = benchmark(Vec2.normalize, _A2)
    assert Vec2.length(result) == pytest.approx(1.0)


def test_benchmark_vec2_squared_distance(benchmark):
    result = benchmark(Vec2.squaredDistance, _A2, _B2)
    assert result == pytest.approx(Vec2.distance(_A2, _B2) ** 2)


def test_benchmark_vec2_squared_length(benchmark):
    result = benchmark(Vec2.squaredLength, _A2)
    assert result == pytest.approx(25.0)


def test_benchmark_vec3_abs(benchmark):
    result = benchmark(Vec3.abs, _A3)
    assert result == (3.0, 4.0, 12.0)


def test_benchmark_vec3_add(benchmark):
    result = benchmark(Vec3.add, _A3, _B3)
    assert result == (8.0, 10.0, 19.0)


def test_benchmark_vec3_mul(benchmark):
    result = benchmark(Vec3.mul, _A3, _B3)
    assert result == (15.0, 24.0, 84.0)


def test_benchmark_vec3_neg(benchmark):
    result = benchmark(Vec3.neg, _A3)
    assert result == (-3.0, -4.0, -12.0)


def test_benchmark_vec3_pos(benchmark):
    result = benchmark(Vec3.pos, _A3)
    assert result == _A3


def test_benchmark_vec3_sub(benchmark):
    result = benchmark(Vec3.sub, _A3, _B3)
    assert result == (-2.0, -2.0, 5.0)


def test_benchmark_vec3_div(benchmark):
    result = benchmark(Vec3.div, _A3, _B3)
    assert result == pytest.approx((3.0 / 5.0, 4.0 / 6.0, 12.0 / 7.0))


def test_benchmark_vec3_cross(benchmark):
    result = benchmark(Vec3.cross, _A3, _B3)
    assert result == pytest.approx(
        (4.0 * 7.0 - 12.0 * 6.0, 12.0 * 5.0 - 3.0 * 7.0, 3.0 * 6.0 - 4.0 * 5.0)
    )


def test_benchmark_vec3_distance(benchmark):
    result = benchmark(Vec3.distance, _A3, _B3)
    assert result == pytest.approx(Vec3.length(Vec3.sub(_B3, _A3)))


def test_benchmark_vec3_dot(benchmark):
    result = benchmark(Vec3.dot, _A3, _B3)
    assert result == pytest.approx(3.0 * 5.0 + 4.0 * 6.0 + 12.0 * 7.0)


def test_benchmark_vec3_length(benchmark):
    result = benchmark(Vec3.length, _A3)
    assert result == pytest.approx(13.0)


def test_benchmark_vec3_normalize(benchmark):
    result = benchmark(Vec3.normalize, _A3)
    assert Vec3.length(result) == pytest.approx(1.0)


def test_benchmark_vec3_squared_distance(benchmark):
    result = benchmark(Vec3.squaredDistance, _A3, _B3)
    assert result == pytest.approx(Vec3.distance(_A3, _B3) ** 2)


def test_benchmark_vec3_squared_length(benchmark):
    result = benchmark(Vec3.squaredLength, _A3)
    assert result == pytest.approx(169.0)


_M3 = [(1.0, 2.0, 3.0), (0.0, 1.0, 4.0), (5.0, 6.0, 0.0)]
_COPLANAR_PTS = [
    (0.0, 0.0, 0.0),
    (1.0, 0.0, 0.0),
    (1.0, 1.0, 0.0),
    (0.0, 1.0, 0.0),
]


def test_benchmark_mat3_determinant(benchmark):
    result = benchmark(Mat3.determinant, _M3)
    assert result == pytest.approx(1.0)


def test_benchmark_geom_coplanar(benchmark):
    result = benchmark(Geom.coplanar, _COPLANAR_PTS)
    assert result is True

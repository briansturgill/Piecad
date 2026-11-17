"""
Tinyarray counterparts of test_npvec.py for comparison with test_lin_math.py.

The correctness cases cover both vector sizes; benchmark names mirror the
NumPy suite one-for-one and time operations on preconstructed float arrays.
Tinyarray has no cross product, norm, normalization, or determinant API, so
the helpers below implement them using tinyarray arithmetic and Python math.
Squared lengths use dot products because tinyarray has no power/sum API.
No NumPy operations or conversions are included in these benchmarks.
"""

import math
import operator

import pytest
import tinyarray as ta


def vec2(x, y):
    return ta.array([float(x), float(y)])


def vec3(x, y, z):
    return ta.array([float(x), float(y), float(z)])


def _cross2d(a, b):
    return vec3(0.0, 0.0, a[0] * b[1] - a[1] * b[0])


def _ta_cross(a, b):
    return vec3(
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _ta_length(v):
    return math.sqrt(ta.dot(v, v))


def _ta_normalize(v):
    length = _ta_length(v)
    if length > 0:
        return v / length
    return ta.zeros(v.shape)


def _ta_squared_distance(a, b):
    delta = b - a
    return ta.dot(delta, delta)


def _ta_determinant(m):
    return (
        m[0, 0] * (m[1, 1] * m[2, 2] - m[1, 2] * m[2, 1])
        - m[0, 1] * (m[1, 0] * m[2, 2] - m[1, 2] * m[2, 0])
        + m[0, 2] * (m[1, 0] * m[2, 1] - m[1, 1] * m[2, 0])
    )


def _ta_coplanar(points):
    """Match the NumPy suite's first-three-points plane and 1e-6 tolerance."""
    if len(points) < 4:
        return True
    v0, v1, v2 = points[:3]
    normal = _ta_cross(v1 - v0, v2 - v0)
    for v in points[3:]:
        if abs(ta.dot(normal, v - v0)) > 1e-6:
            return False
    return True


@pytest.fixture(params=[2, 3], ids=["vec2", "vec3"])
def size(request):
    return request.param


@pytest.mark.parametrize(
    "values, expected",
    [
        ((3, 4, 5), (3, 4, 5)),
        ((-3, -4, -5), (3, 4, 5)),
        ((-3, 4, -5), (3, 4, 5)),
        ((0, 0, 0), (0, 0, 0)),
    ],
    ids=["positive", "negative", "mixed_sign", "zero"],
)
def test_ta_vec_abs_is_component_wise(size, values, expected):
    assert tuple(ta.abs(ta.array(values[:size], float))) == expected[:size]


@pytest.mark.parametrize(
    "operation, a, b, expected",
    [
        (ta.add, (1, 2, 3), (4, 5, 6), (5, 7, 9)),
        (ta.add, (1, 2, 3), (-1, -2, -3), (0, 0, 0)),
        (ta.add, (5.5, -2.25, 3), (0, 0, 0), (5.5, -2.25, 3)),
        (ta.multiply, (2, 3, 4), (5, 6, 7), (10, 18, 28)),
        (ta.multiply, (2, 3, 4), (0, 0, 0), (0, 0, 0)),
        (ta.multiply, (2, -3, 4), (-1, -1, -1), (-2, 3, -4)),
        (ta.subtract, (5, 7, 9), (1, 2, 3), (4, 5, 6)),
        (ta.subtract, (9.5, -3.25, 1), (9.5, -3.25, 1), (0, 0, 0)),
        (ta.subtract, (0, 0, 0), (3, -4, 5), (-3, 4, -5)),
        (ta.divide, (8, 9, 10), (2, 3, 5), (4, 3, 2)),
        (ta.divide, (7.5, -2.25, 3), (1, 1, 1), (7.5, -2.25, 3)),
    ],
    ids=[
        "add_components",
        "add_negative",
        "add_zero",
        "mul_components",
        "mul_zero",
        "mul_negative_one",
        "sub_components",
        "sub_self",
        "sub_from_zero",
        "truediv_components",
        "truediv_by_one",
    ],
)
def test_ta_vec_arithmetic(size, operation, a, b, expected):
    result = operation(ta.array(a[:size], float), ta.array(b[:size], float))
    assert tuple(result) == expected[:size]


@pytest.mark.parametrize("values", [(3, -4, 5), (0, 0, 0)])
def test_ta_vec_neg_flips_sign_and_is_involution(size, values):
    v = ta.array(values[:size], float)
    assert tuple(-v) == tuple(-x for x in values[:size])
    assert -(-v) == v


@pytest.mark.parametrize("values", [(3, -4, 5), (0, 0, 0)])
def test_ta_vec_pos_returns_an_equal_vector(size, values):
    v = ta.array(values[:size], float)
    assert +v == v


def test_ta_vec_truediv_by_zero_produces_infinity(size):
    result = ta.array((1.0,) * size) / ta.array((0.0,) + (1.0,) * (size - 1))
    assert math.isinf(result[0])
    assert tuple(result)[1:] == (1.0,) * (size - 1)


@pytest.mark.parametrize(
    "a, b, expected",
    [
        ((1, 0, 0), (0, 1, 0), (0, 0, 1)),
        ((2, 4, 6), (1, 2, 3), (0, 0, 0)),
    ],
    ids=["orthogonal_axes", "parallel"],
)
def test_ta_vec_cross(size, a, b, expected):
    cross = _cross2d if size == 2 else _ta_cross
    result = cross(ta.array(a[:size], float), ta.array(b[:size], float))
    assert result.shape == (3,)
    assert tuple(result) == expected


def test_ta_vec_cross_is_anti_commutative(size):
    cross = _cross2d if size == 2 else _ta_cross
    a, b = ta.array((3.0, 4.0, 5.0)[:size]), ta.array((5.0, 6.0, 7.0)[:size])
    assert cross(a, b) == -cross(b, a)


def test_ta_vec_distance_matches_pythagorean_and_is_symmetric(size):
    a = ta.array((3.0, 4.0, 12.0)[:size])
    zero = ta.zeros((size,))
    assert _ta_length(a - zero) == pytest.approx(5.0 if size == 2 else 13.0)
    assert _ta_length(a - a) == 0.0
    b = ta.array((5.0, 6.0, 7.0)[:size])
    assert _ta_length(b - a) == pytest.approx(_ta_length(a - b))


def test_ta_vec_dot_of_orthogonal_self_and_opposite_vectors(size):
    x = ta.array((1.0, 0.0, 0.0)[:size])
    y = ta.array((0.0, 1.0, 0.0)[:size])
    assert ta.dot(x, y) == 0.0
    assert ta.dot(x, -x) == -1.0
    v = ta.array((3.0, 4.0, 12.0)[:size])
    assert ta.dot(v, v) == pytest.approx(25.0 if size == 2 else 169.0)


@pytest.mark.parametrize("sign", [1, -1, 0], ids=["positive", "negative", "zero"])
def test_ta_vec_length_ignores_sign_of_components(size, sign):
    v = ta.array(tuple(sign * x for x in (3.0, 4.0, 12.0)[:size]))
    assert _ta_length(v) == pytest.approx(abs(sign) * (5.0 if size == 2 else 13.0))


def test_ta_vec_normalize_produces_unit_length_vector(size):
    v = _ta_normalize(ta.array((3.0, 4.0, 12.0)[:size]))
    length = 5.0 if size == 2 else 13.0
    assert tuple(v) == pytest.approx(tuple(x / length for x in (3, 4, 12)[:size]))
    assert _ta_length(v) == pytest.approx(1.0)


def test_ta_vec_normalize_of_zero_vector_returns_zero_vector(size):
    zero = ta.zeros((size,))
    assert _ta_normalize(zero) == zero


def test_ta_vec_normalize_of_already_unit_vector_is_unchanged(size):
    v = ta.array((1.0, 0.0, 0.0)[:size])
    assert _ta_normalize(v) == v


def test_ta_vec_squared_distance_matches_distance_squared(size):
    a, b = ta.array((1.0, 2.0, 3.0)[:size]), ta.array((4.0, 6.0, 15.0)[:size])
    assert _ta_squared_distance(a, b) == pytest.approx(_ta_length(b - a) ** 2)
    assert _ta_squared_distance(a, a) == 0.0


def test_ta_vec_squared_length_matches_length_squared(size):
    v = ta.array((3.0, 4.0, 12.0)[:size])
    assert ta.dot(v, v) == pytest.approx(_ta_length(v) ** 2)
    zero = ta.zeros((size,))
    assert ta.dot(zero, zero) == 0.0


@pytest.mark.parametrize(
    "values, expected",
    [
        (((1, 0, 0), (0, 1, 0), (0, 0, 1)), 1.0),
        (((1, 2, 3), (0, 1, 4), (5, 6, 0)), 1.0),
        (((1, 2, 3), (2, 4, 6), (0, 1, 1)), 0.0),
        (((0, 0, 0), (0, 0, 0), (0, 0, 0)), 0.0),
        (((0, 1, 4), (1, 2, 3), (5, 6, 0)), -1.0),
    ],
    ids=["identity", "general", "singular", "zero", "swapped_rows"],
)
def test_ta_mat3_determinant(values, expected):
    assert _ta_determinant(ta.array(values, float)) == pytest.approx(expected)


@pytest.mark.parametrize(
    "points, expected",
    [
        ([], True),
        ([(0, 0, 0)], True),
        ([(0, 0, 0), (1, 0, 0)], True),
        ([(0, 0, 0), (1, 0, 0), (0, 1, 0)], True),
        ([(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)], True),
        ([(0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)], False),
        ([(0, 0, 0), (1, 0, 1), (0, 1, 1), (1, 1, 2)], True),
    ],
    ids=["empty", "one", "two", "three", "planar", "nonplanar", "tilted"],
)
def test_ta_coplanar(points, expected):
    assert _ta_coplanar([vec3(*p) for p in points]) is expected


_A2 = vec2(3.0, 4.0)
_B2 = vec2(5.0, 6.0)
_A3 = vec3(3.0, 4.0, 12.0)
_B3 = vec3(5.0, 6.0, 7.0)
_M3 = ta.array([[1.0, 2.0, 3.0], [0.0, 1.0, 4.0], [5.0, 6.0, 0.0]])
_COPLANAR_PTS = [vec3(0, 0, 0), vec3(1, 0, 0), vec3(1, 1, 0), vec3(0, 1, 0)]


def test_benchmark_ta_vec2_abs(benchmark):
    assert tuple(benchmark(ta.abs, _A2)) == (3.0, 4.0)


def test_benchmark_ta_vec2_add(benchmark):
    assert tuple(benchmark(ta.add, _A2, _B2)) == (8.0, 10.0)


def test_benchmark_ta_vec2_mul(benchmark):
    assert tuple(benchmark(ta.multiply, _A2, _B2)) == (15.0, 24.0)


def test_benchmark_ta_vec2_neg(benchmark):
    assert tuple(benchmark(ta.negative, _A2)) == (-3.0, -4.0)


def test_benchmark_ta_vec2_pos(benchmark):
    assert benchmark(operator.pos, _A2) == _A2


def test_benchmark_ta_vec2_sub(benchmark):
    assert tuple(benchmark(ta.subtract, _A2, _B2)) == (-2.0, -2.0)


def test_benchmark_ta_vec2_truediv(benchmark):
    assert tuple(benchmark(ta.divide, _A2, _B2)) == pytest.approx((3 / 5, 4 / 6))


def test_benchmark_ta_vec2_cross(benchmark):
    assert tuple(benchmark(_cross2d, _A2, _B2)) == (0.0, 0.0, -2.0)


def test_benchmark_ta_vec2_distance(benchmark):
    result = benchmark(lambda a, b: _ta_length(b - a), _A2, _B2)
    assert result == pytest.approx(math.sqrt(8.0))


def test_benchmark_ta_vec2_dot(benchmark):
    assert benchmark(ta.dot, _A2, _B2) == pytest.approx(39.0)


def test_benchmark_ta_vec2_length(benchmark):
    assert benchmark(_ta_length, _A2) == pytest.approx(5.0)


def test_benchmark_ta_vec2_normalize(benchmark):
    assert tuple(benchmark(_ta_normalize, _A2)) == pytest.approx((0.6, 0.8))


def test_benchmark_ta_vec2_squared_distance(benchmark):
    assert benchmark(_ta_squared_distance, _A2, _B2) == pytest.approx(8.0)


def test_benchmark_ta_vec2_squared_length(benchmark):
    assert benchmark(ta.dot, _A2, _A2) == pytest.approx(25.0)


def test_benchmark_ta_vec3_abs(benchmark):
    assert tuple(benchmark(ta.abs, _A3)) == (3.0, 4.0, 12.0)


def test_benchmark_ta_vec3_add(benchmark):
    assert tuple(benchmark(ta.add, _A3, _B3)) == (8.0, 10.0, 19.0)


def test_benchmark_ta_vec3_mul(benchmark):
    assert tuple(benchmark(ta.multiply, _A3, _B3)) == (15.0, 24.0, 84.0)


def test_benchmark_ta_vec3_neg(benchmark):
    assert tuple(benchmark(ta.negative, _A3)) == (-3.0, -4.0, -12.0)


def test_benchmark_ta_vec3_pos(benchmark):
    assert benchmark(operator.pos, _A3) == _A3


def test_benchmark_ta_vec3_sub(benchmark):
    assert tuple(benchmark(ta.subtract, _A3, _B3)) == (-2.0, -2.0, 5.0)


def test_benchmark_ta_vec3_truediv(benchmark):
    result = benchmark(ta.divide, _A3, _B3)
    assert tuple(result) == pytest.approx((3 / 5, 4 / 6, 12 / 7))


def test_benchmark_ta_vec3_cross(benchmark):
    assert tuple(benchmark(_ta_cross, _A3, _B3)) == pytest.approx((-44, 39, -2))


def test_benchmark_ta_vec3_distance(benchmark):
    result = benchmark(lambda a, b: _ta_length(b - a), _A3, _B3)
    assert result == pytest.approx(math.sqrt(33.0))


def test_benchmark_ta_vec3_dot(benchmark):
    assert benchmark(ta.dot, _A3, _B3) == pytest.approx(123.0)


def test_benchmark_ta_vec3_length(benchmark):
    assert benchmark(_ta_length, _A3) == pytest.approx(13.0)


def test_benchmark_ta_vec3_normalize(benchmark):
    result = benchmark(_ta_normalize, _A3)
    assert tuple(result) == pytest.approx((3 / 13, 4 / 13, 12 / 13))


def test_benchmark_ta_vec3_squared_distance(benchmark):
    assert benchmark(_ta_squared_distance, _A3, _B3) == pytest.approx(33.0)


def test_benchmark_ta_vec3_squared_length(benchmark):
    assert benchmark(ta.dot, _A3, _A3) == pytest.approx(169.0)


def test_benchmark_ta_mat3_determinant(benchmark):
    assert benchmark(_ta_determinant, _M3) == pytest.approx(1.0)


def test_benchmark_ta_coplanar(benchmark):
    assert benchmark(_ta_coplanar, _COPLANAR_PTS) is True

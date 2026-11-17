"""
Tinynumpy counterparts of test_npvec.py for comparison with test_lin_math.py.

The correctness cases cover both vector sizes; benchmark names mirror the
NumPy suite one-for-one and time operations on preconstructed float arrays.
Tinynumpy 1.2.1 exposes its API in tinynumpy.tinynumpy, not the package root.
It lacks arithmetic operators, abs/neg/pos, component-wise division, norms,
and 2D dot products. The explicit helpers below fill those gaps with Python
and tinynumpy operations; they never delegate to NumPy. Its native 3D cross
returns a list, which is converted to an array inside the timed helper.
Squared lengths use multiply/sum because array exponentiation is unsupported.
Division by zero raises ZeroDivisionError rather than producing infinity.
"""

import math

import pytest
from tinynumpy import tinynumpy as tnp


def vec2(x, y):
    return tnp.array([float(x), float(y)])


def vec3(x, y, z):
    return tnp.array([float(x), float(y), float(z)])


def _tnp_abs(v):
    return tnp.array([abs(x) for x in v])


def _tnp_neg(v):
    return tnp.array([-x for x in v])


def _tnp_truediv(a, b):
    return tnp.array([x / y for x, y in zip(a, b)])


def _cross2d(a, b):
    return vec3(0.0, 0.0, a[0] * b[1] - a[1] * b[0])


def _tnp_cross(a, b):
    return tnp.array(tnp.cross(a, b))


def _tnp_dot2(a, b):
    return a[0] * b[0] + a[1] * b[1]


def _tnp_squared_length(v):
    return tnp.multiply(v, v).sum()


def _tnp_length(v):
    return math.sqrt(_tnp_squared_length(v))


def _tnp_normalize(v):
    length = _tnp_length(v)
    if length > 0:
        return tnp.divide(v, length)
    return tnp.zeros_like(v)


def _tnp_squared_distance(a, b):
    delta = tnp.subtract(b, a)
    return _tnp_squared_length(delta)


def _tnp_coplanar(points):
    """Match the NumPy suite's first-three-points plane and 1e-6 tolerance."""
    if len(points) < 4:
        return True
    v0, v1, v2 = points[:3]
    normal = _tnp_cross(tnp.subtract(v1, v0), tnp.subtract(v2, v0))
    for v in points[3:]:
        if abs(tnp.dot(normal, tnp.subtract(v, v0))) > 1e-6:
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
def test_tnp_vec_abs_is_component_wise(size, values, expected):
    assert tuple(_tnp_abs(tnp.array(values[:size], "float64"))) == expected[:size]


@pytest.mark.parametrize(
    "operation, a, b, expected",
    [
        (tnp.add, (1, 2, 3), (4, 5, 6), (5, 7, 9)),
        (tnp.add, (1, 2, 3), (-1, -2, -3), (0, 0, 0)),
        (tnp.add, (5.5, -2.25, 3), (0, 0, 0), (5.5, -2.25, 3)),
        (tnp.multiply, (2, 3, 4), (5, 6, 7), (10, 18, 28)),
        (tnp.multiply, (2, 3, 4), (0, 0, 0), (0, 0, 0)),
        (tnp.multiply, (2, -3, 4), (-1, -1, -1), (-2, 3, -4)),
        (tnp.subtract, (5, 7, 9), (1, 2, 3), (4, 5, 6)),
        (tnp.subtract, (9.5, -3.25, 1), (9.5, -3.25, 1), (0, 0, 0)),
        (tnp.subtract, (0, 0, 0), (3, -4, 5), (-3, 4, -5)),
        (_tnp_truediv, (8, 9, 10), (2, 3, 5), (4, 3, 2)),
        (_tnp_truediv, (7.5, -2.25, 3), (1, 1, 1), (7.5, -2.25, 3)),
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
def test_tnp_vec_arithmetic(size, operation, a, b, expected):
    result = operation(tnp.array(a[:size], "float64"), tnp.array(b[:size], "float64"))
    assert tuple(result) == expected[:size]


@pytest.mark.parametrize("values", [(3, -4, 5), (0, 0, 0)])
def test_tnp_vec_neg_flips_sign_and_is_involution(size, values):
    v = tnp.array(values[:size], "float64")
    assert tuple(_tnp_neg(v)) == tuple(-x for x in values[:size])
    assert tuple(_tnp_neg(_tnp_neg(v))) == tuple(v)


@pytest.mark.parametrize("values", [(3, -4, 5), (0, 0, 0)])
def test_tnp_vec_pos_returns_an_equal_vector(size, values):
    v = tnp.array(values[:size], "float64")
    assert tuple(tnp.array(v)) == tuple(v)


def test_tnp_vec_truediv_by_zero_raises_zero_division_error(size):
    a = tnp.array((1.0,) * size)
    b = tnp.array((0.0,) + (1.0,) * (size - 1))
    with pytest.raises(ZeroDivisionError):
        _tnp_truediv(a, b)


@pytest.mark.parametrize(
    "a, b, expected",
    [
        ((1, 0, 0), (0, 1, 0), (0, 0, 1)),
        ((2, 4, 6), (1, 2, 3), (0, 0, 0)),
    ],
    ids=["orthogonal_axes", "parallel"],
)
def test_tnp_vec_cross(size, a, b, expected):
    cross = _cross2d if size == 2 else _tnp_cross
    result = cross(tnp.array(a[:size], "float64"), tnp.array(b[:size], "float64"))
    assert result.shape == (3,)
    assert tuple(result) == expected


def test_tnp_vec_cross_is_anti_commutative(size):
    cross = _cross2d if size == 2 else _tnp_cross
    a, b = tnp.array((3.0, 4.0, 5.0)[:size]), tnp.array((5.0, 6.0, 7.0)[:size])
    assert tuple(cross(a, b)) == tuple(_tnp_neg(cross(b, a)))


def test_tnp_vec_distance_matches_pythagorean_and_is_symmetric(size):
    a = tnp.array((3.0, 4.0, 12.0)[:size])
    zero = tnp.zeros((size,))
    assert _tnp_length(tnp.subtract(a, zero)) == pytest.approx(
        5.0 if size == 2 else 13.0
    )
    assert _tnp_length(tnp.subtract(a, a)) == 0.0
    b = tnp.array((5.0, 6.0, 7.0)[:size])
    assert _tnp_length(tnp.subtract(b, a)) == pytest.approx(
        _tnp_length(tnp.subtract(a, b))
    )


def test_tnp_vec_dot_of_orthogonal_self_and_opposite_vectors(size):
    dot = _tnp_dot2 if size == 2 else tnp.dot
    x = tnp.array((1.0, 0.0, 0.0)[:size])
    y = tnp.array((0.0, 1.0, 0.0)[:size])
    assert dot(x, y) == 0.0
    assert dot(x, _tnp_neg(x)) == -1.0
    v = tnp.array((3.0, 4.0, 12.0)[:size])
    assert dot(v, v) == pytest.approx(25.0 if size == 2 else 169.0)


@pytest.mark.parametrize("sign", [1, -1, 0], ids=["positive", "negative", "zero"])
def test_tnp_vec_length_ignores_sign_of_components(size, sign):
    v = tnp.array(tuple(sign * x for x in (3.0, 4.0, 12.0)[:size]))
    assert _tnp_length(v) == pytest.approx(abs(sign) * (5.0 if size == 2 else 13.0))


def test_tnp_vec_normalize_produces_unit_length_vector(size):
    v = _tnp_normalize(tnp.array((3.0, 4.0, 12.0)[:size]))
    length = 5.0 if size == 2 else 13.0
    assert tuple(v) == pytest.approx(tuple(x / length for x in (3, 4, 12)[:size]))
    assert _tnp_length(v) == pytest.approx(1.0)


def test_tnp_vec_normalize_of_zero_vector_returns_zero_vector(size):
    zero = tnp.zeros((size,))
    assert tuple(_tnp_normalize(zero)) == tuple(zero)


def test_tnp_vec_normalize_of_already_unit_vector_is_unchanged(size):
    v = tnp.array((1.0, 0.0, 0.0)[:size])
    assert tuple(_tnp_normalize(v)) == tuple(v)


def test_tnp_vec_squared_distance_matches_distance_squared(size):
    a, b = tnp.array((1.0, 2.0, 3.0)[:size]), tnp.array((4.0, 6.0, 15.0)[:size])
    assert _tnp_squared_distance(a, b) == pytest.approx(
        _tnp_length(tnp.subtract(b, a)) ** 2
    )
    assert _tnp_squared_distance(a, a) == 0.0


def test_tnp_vec_squared_length_matches_length_squared(size):
    v = tnp.array((3.0, 4.0, 12.0)[:size])
    assert _tnp_squared_length(v) == pytest.approx(_tnp_length(v) ** 2)
    assert _tnp_squared_length(tnp.zeros((size,))) == 0.0


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
def test_tnp_mat3_determinant(values, expected):
    assert tnp.linalg.det(tnp.array(values, "float64")) == pytest.approx(expected)


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
def test_tnp_coplanar(points, expected):
    assert _tnp_coplanar([vec3(*p) for p in points]) is expected


_A2 = vec2(3.0, 4.0)
_B2 = vec2(5.0, 6.0)
_A3 = vec3(3.0, 4.0, 12.0)
_B3 = vec3(5.0, 6.0, 7.0)
_M3 = tnp.array([[1.0, 2.0, 3.0], [0.0, 1.0, 4.0], [5.0, 6.0, 0.0]])
_COPLANAR_PTS = [vec3(0, 0, 0), vec3(1, 0, 0), vec3(1, 1, 0), vec3(0, 1, 0)]


def test_benchmark_tnp_vec2_abs(benchmark):
    assert tuple(benchmark(_tnp_abs, _A2)) == (3.0, 4.0)


def test_benchmark_tnp_vec2_add(benchmark):
    assert tuple(benchmark(tnp.add, _A2, _B2)) == (8.0, 10.0)


def test_benchmark_tnp_vec2_mul(benchmark):
    assert tuple(benchmark(tnp.multiply, _A2, _B2)) == (15.0, 24.0)


def test_benchmark_tnp_vec2_neg(benchmark):
    assert tuple(benchmark(_tnp_neg, _A2)) == (-3.0, -4.0)


def test_benchmark_tnp_vec2_pos(benchmark):
    assert tuple(benchmark(tnp.array, _A2)) == tuple(_A2)


def test_benchmark_tnp_vec2_sub(benchmark):
    assert tuple(benchmark(tnp.subtract, _A2, _B2)) == (-2.0, -2.0)


def test_benchmark_tnp_vec2_truediv(benchmark):
    result = benchmark(_tnp_truediv, _A2, _B2)
    assert tuple(result) == pytest.approx((3 / 5, 4 / 6))


def test_benchmark_tnp_vec2_cross(benchmark):
    assert tuple(benchmark(_cross2d, _A2, _B2)) == (0.0, 0.0, -2.0)


def test_benchmark_tnp_vec2_distance(benchmark):
    result = benchmark(lambda a, b: _tnp_length(tnp.subtract(b, a)), _A2, _B2)
    assert result == pytest.approx(math.sqrt(8.0))


def test_benchmark_tnp_vec2_dot(benchmark):
    assert benchmark(_tnp_dot2, _A2, _B2) == pytest.approx(39.0)


def test_benchmark_tnp_vec2_length(benchmark):
    assert benchmark(_tnp_length, _A2) == pytest.approx(5.0)


def test_benchmark_tnp_vec2_normalize(benchmark):
    assert tuple(benchmark(_tnp_normalize, _A2)) == pytest.approx((0.6, 0.8))


def test_benchmark_tnp_vec2_squared_distance(benchmark):
    assert benchmark(_tnp_squared_distance, _A2, _B2) == pytest.approx(8.0)


def test_benchmark_tnp_vec2_squared_length(benchmark):
    assert benchmark(_tnp_squared_length, _A2) == pytest.approx(25.0)


def test_benchmark_tnp_vec3_abs(benchmark):
    assert tuple(benchmark(_tnp_abs, _A3)) == (3.0, 4.0, 12.0)


def test_benchmark_tnp_vec3_add(benchmark):
    assert tuple(benchmark(tnp.add, _A3, _B3)) == (8.0, 10.0, 19.0)


def test_benchmark_tnp_vec3_mul(benchmark):
    assert tuple(benchmark(tnp.multiply, _A3, _B3)) == (15.0, 24.0, 84.0)


def test_benchmark_tnp_vec3_neg(benchmark):
    assert tuple(benchmark(_tnp_neg, _A3)) == (-3.0, -4.0, -12.0)


def test_benchmark_tnp_vec3_pos(benchmark):
    assert tuple(benchmark(tnp.array, _A3)) == tuple(_A3)


def test_benchmark_tnp_vec3_sub(benchmark):
    assert tuple(benchmark(tnp.subtract, _A3, _B3)) == (-2.0, -2.0, 5.0)


def test_benchmark_tnp_vec3_truediv(benchmark):
    result = benchmark(_tnp_truediv, _A3, _B3)
    assert tuple(result) == pytest.approx((3 / 5, 4 / 6, 12 / 7))


def test_benchmark_tnp_vec3_cross(benchmark):
    result = benchmark(_tnp_cross, _A3, _B3)
    assert tuple(result) == pytest.approx((-44, 39, -2))


def test_benchmark_tnp_vec3_distance(benchmark):
    result = benchmark(lambda a, b: _tnp_length(tnp.subtract(b, a)), _A3, _B3)
    assert result == pytest.approx(math.sqrt(33.0))


def test_benchmark_tnp_vec3_dot(benchmark):
    assert benchmark(tnp.dot, _A3, _B3) == pytest.approx(123.0)


def test_benchmark_tnp_vec3_length(benchmark):
    assert benchmark(_tnp_length, _A3) == pytest.approx(13.0)


def test_benchmark_tnp_vec3_normalize(benchmark):
    result = benchmark(_tnp_normalize, _A3)
    assert tuple(result) == pytest.approx((3 / 13, 4 / 13, 12 / 13))


def test_benchmark_tnp_vec3_squared_distance(benchmark):
    assert benchmark(_tnp_squared_distance, _A3, _B3) == pytest.approx(33.0)


def test_benchmark_tnp_vec3_squared_length(benchmark):
    assert benchmark(_tnp_squared_length, _A3) == pytest.approx(169.0)


def test_benchmark_tnp_mat3_determinant(benchmark):
    assert benchmark(tnp.linalg.det, _M3) == pytest.approx(1.0)


def test_benchmark_tnp_coplanar(benchmark):
    assert benchmark(_tnp_coplanar, _COPLANAR_PTS) is True

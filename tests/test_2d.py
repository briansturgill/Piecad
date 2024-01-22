import pytest
from piecad import *


def _star(np, r):
    o = star(np, r)
    o.mo.num_vert()
    return o


def _square(s):
    o = square(s)
    o.mo.num_vert()
    return o


def _rectangle(t):
    o = rectangle(t)
    o.mo.num_vert()
    return o


def _rounded_rectangle(t, r, s):
    o = rounded_rectangle(t, r, s)
    o.mo.num_vert()
    return o


def _ellipse(r, s):
    c = ellipse(r, s)
    c.mo.num_vert()
    return c


def _circle(r, s):
    c = circle(r, s)
    c.mo.num_vert()
    return c


def test_circle_10(benchmark):
    o = benchmark(_circle, 3, 10)
    assert o.mo.num_vert() == 10


def test_circle_100(benchmark):
    o = benchmark(_circle, 3, 100)
    assert o.mo.num_vert() == 100


def test_ellipse_10(benchmark):
    o = benchmark(_ellipse, (3, 12), 10)
    assert o.mo.num_vert() == 10


def test_ellipse_100(benchmark):
    o = benchmark(_ellipse, (3, 12), 100)
    assert o.mo.num_vert() == 100


def test_square(benchmark):
    o = benchmark(_square, 10)
    assert o.mo.num_vert() == 4


def test_rectangle(benchmark):
    o = benchmark(_rectangle, [10, 10])
    assert o.mo.num_vert() == 4


def test_rectangle2(benchmark):
    o = benchmark(_rectangle, (10, 10))  # Check list vs tuple
    assert o.mo.num_vert() == 4


def test_rounded_rectangle(benchmark):
    o = benchmark(_rounded_rectangle, (10, 10), 2.0, 36)
    assert o.mo.num_vert() == 40


def test_star(benchmark):
    o = benchmark(_star, 5, 20)
    assert o.mo.num_vert() == 10

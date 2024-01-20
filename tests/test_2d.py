import pytest
from piecad import *


def test_circle_10(benchmark):
    o = benchmark(circle, 1, 10)
    assert o.mo.num_vert() == 10


def test_circle_100(benchmark):
    o = benchmark(circle, 1, 100)
    assert o.mo.num_vert() == 100

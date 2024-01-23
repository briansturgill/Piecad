import pytest
from piecad import *


def _extrude_list(l):
    o = extrude_list(l)
    o.mo.num_vert()
    return o


def test_extrude_list(benchmark):
    c = circle(10)
    o = benchmark(_extrude_list, [(1, c)])
    assert o.mo.num_vert() == 72


# LATER hull, difference

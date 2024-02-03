import pytest
from piecad import *


def _offset(o, d, jt):
    o = o.offset(d, jt)
    o.num_verts()
    return o


def test_offset(benchmark):
    rr = rounded_rectangle((10, 10), 2.0, 36)
    c = benchmark(_offset, rr, 2, "round")
    assert c.num_verts() == 84

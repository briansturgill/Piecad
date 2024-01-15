import pytest
from piecad import *


def test_circle():
    assert circle(1, 10).v.num_vert() == 10

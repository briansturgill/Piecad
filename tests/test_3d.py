import pytest
from piecad import *


def test_cone():
    assert cone(1, 10).mo.num_vert() == 72


def test_cylinder():
    assert cylinder(1, 10).mo.num_vert() == 72


def test_extrude():
    c = circle(10)
    assert extrude(c, 1).mo.num_vert() == 72


def test_revolve():
    c = circle(10)
    assert revolve(c).mo.num_vert() == 614

import pytest
from piecad import *
from piecad.projectbox import ProjectBox


def test_projectbox():
    walls = ProjectBox([100, 40, 20]).finish()
    left, right, front, back, top, bottom = walls
    assert left.num_verts() == right.num_verts()
    assert front.num_verts() == back.num_verts()
    assert top.num_verts() != bottom.num_verts()
    assert top.num_verts() == 610
    assert bottom.num_verts() == 512

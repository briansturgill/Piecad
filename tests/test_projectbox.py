import pytest
from piecad import *
from piecad.projectbox import ProjectBox, pbc


def test_projectbox():
    walls = ProjectBox([100, 40, 20]).finish()
    left, right, front, back, top, bottom = walls
    assert left.num_verts() == right.num_verts()
    assert front.num_verts() == back.num_verts()
    assert top.num_verts() != bottom.num_verts()
    assert top.num_verts() == 1103
    assert bottom.num_verts() == 512


def test_projectbox_components_on_every_wall():
    pb = ProjectBox([100, 40, 20])
    base = pb.finish()
    for side in (pb.left, pb.right, pb.front, pb.back, pb.top, pb.bottom):
        side(10, 10, cube(2), None)
        side(30, 10, None, pbc.hole(2))
    walls = pb.finish()
    for before, after in zip(base, walls):
        assert after.num_verts() != before.num_verts()


def test_pbc_parts():
    assert pbc.tap_post(5, 3).volume() > 0
    assert pbc.tap_post(5, 3, add_taper=True, z_rot=45).volume() > 0
    assert pbc.horizontal_slot_hole(6, 2).volume() > 0
    assert pbc.tapered_bolt_hole(5, 3).volume() > 0
    assert pbc.hole(2).volume() > 0
    assert pbc.wire_tie_loop().volume() > 0
    assert pbc.circular_speaker_grid_holes(10).volume() > 0

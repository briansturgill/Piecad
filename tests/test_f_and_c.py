import pytest

from piecad import cuboid
from piecad._f_and_c import classify_edges, do_f_and_c, face_normal


def test_face_normal_uses_newell_method():
    vertices = [(0, 0, 0), (1, 0, 0), (0, 1, 0)]

    assert face_normal(vertices, (0, 1, 2)) == (0.0, 0.0, 1.0)


def test_face_normal_rejects_degenerate_face():
    vertices = [(0, 0, 0), (1, 0, 0), (2, 0, 0)]

    with pytest.raises(ValueError, match="Degenerate face has no normal"):
        face_normal(vertices, (0, 1, 2))


def test_classify_edges_finds_concave_shared_edge():
    vertices = [(0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)]
    faces = [(0, 1, 2), (1, 0, 3)]

    inner_edges, outer_edges = classify_edges(vertices, faces)

    assert len(inner_edges) == 1
    assert outer_edges == []


def test_classify_edges_entries_carry_edge_length_and_normals():
    # Each outer/inner edge entry must expose edge_length, signed_angle,
    # and both adjacent face normals (used by do_f_and_c's
    # min_edge_length / angle_range / include / exclude filters).
    block = cuboid([10.0, 10.0, 10.0])
    vertices, faces = block.to_verts_and_faces()

    inner_edges, outer_edges = classify_edges(vertices, faces)

    assert inner_edges == []
    assert len(outer_edges) == 12

    for edge, edge_length, signed_angle, first_normal, second_normal in outer_edges:
        assert len(edge) == 2
        assert edge_length == pytest.approx(10.0)
        assert abs(signed_angle) == pytest.approx(90.0)
        assert len(first_normal) == 3
        assert len(second_normal) == 3


def test_do_f_and_c_min_edge_length_filters_short_edges():
    block = cuboid([10.0, 10.0, 10.0])

    unfiltered = do_f_and_c(
        block,
        fillet=True,
        radius=0.5,
        min_edge_length=2.0,
        angle_range=(80, 100),
        include=None,
        exclude=None,
    )
    filtered = do_f_and_c(
        block,
        fillet=True,
        radius=0.5,
        min_edge_length=20.0,
        angle_range=(80, 100),
        include=None,
        exclude=None,
    )

    assert unfiltered.volume() < block.volume()
    assert filtered.volume() == pytest.approx(block.volume())


def test_do_f_and_c_angle_range_filters_by_dihedral_angle():
    block = cuboid([10.0, 10.0, 10.0])

    in_range = do_f_and_c(
        block,
        fillet=True,
        radius=0.5,
        min_edge_length=2.0,
        angle_range=(80, 100),
        include=None,
        exclude=None,
    )
    out_of_range = do_f_and_c(
        block,
        fillet=True,
        radius=0.5,
        min_edge_length=2.0,
        angle_range=(0, 10),
        include=None,
        exclude=None,
    )

    assert in_range.volume() < block.volume()
    assert out_of_range.volume() == pytest.approx(block.volume())


def test_do_f_and_c_include_and_exclude_use_endpoint_bounding_boxes():
    block = cuboid([10.0, 10.0, 10.0])
    one_vertical_edge = [(-0.1, -0.1, -0.1, 0.1, 0.1, 10.1)]

    only_included = do_f_and_c(
        block,
        fillet=True,
        radius=0.5,
        min_edge_length=2.0,
        angle_range=(80, 100),
        include=one_vertical_edge,
        exclude=None,
    )
    excluded_same_edge = do_f_and_c(
        block,
        fillet=True,
        radius=0.5,
        min_edge_length=2.0,
        angle_range=(80, 100),
        include=one_vertical_edge,
        exclude=one_vertical_edge,
    )
    full = do_f_and_c(
        block,
        fillet=True,
        radius=0.5,
        min_edge_length=2.0,
        angle_range=(80, 100),
        include=None,
        exclude=None,
    )

    # include alone removes material only for the one selected edge.
    assert only_included.volume() < block.volume()
    assert only_included.volume() > full.volume()
    # exclude always wins when the same edge appears in both lists.
    assert excluded_same_edge.volume() == pytest.approx(block.volume())

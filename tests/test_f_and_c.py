import pytest

from piecad._f_and_c import classify_edges, face_normal


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

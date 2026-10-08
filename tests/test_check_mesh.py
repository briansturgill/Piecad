from piecad import *
from piecad._check_mesh import (
    check_mesh,
    find_bad_winding_pairs,
    find_problem_edges,
    find_problem_vertices,
    _signed_volume,
)

V = [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0), (0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)]
F = [
    (0, 2, 1), (0, 3, 2), (4, 5, 6), (4, 6, 7), (0, 1, 5), (0, 5, 4),
    (1, 2, 6), (1, 6, 5), (2, 3, 7), (2, 7, 6), (3, 0, 4), (3, 4, 7),
]  # fmt: skip

TETRA_V = [(0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)]
TETRA_F = [(0, 2, 1), (0, 1, 3), (0, 3, 2), (1, 2, 3)]


def flip(face):
    return (face[0], face[2], face[1])


def test_good_mesh():
    assert check_mesh(V, F, quick=True) == ""
    assert find_problem_edges(F) == ([], [])
    assert find_problem_vertices(F, len(V)) == []
    assert find_bad_winding_pairs(F) == []
    assert _signed_volume(V, F) == 1.0


def test_boundary_edges():
    assert check_mesh(V, F[:-1], quick=True) == "boundary edges"
    non_manifold, boundary = find_problem_edges(F[:-1])
    assert non_manifold == [] and len(boundary) == 3


def test_non_manifold_edges():
    faces = F + [(0, 1, 7)]
    assert check_mesh(V, faces, quick=True) == "non-manifold edges"
    assert find_problem_edges(faces)[0] == [(0, 1)]


def test_non_manifold_vertex():
    # Two tetrahedra touching at a single point.
    verts = TETRA_V + [(0, 0, 0), (-1, 0, 0), (0, -1, 0), (0, 0, -1)]
    second = [tuple(i + 4 for i in f) for f in TETRA_F]
    # Merge the second tetra's apex 4 into vertex 0.
    second = [tuple(0 if i == 4 else i for i in f) for f in second]
    faces = TETRA_F + second
    assert find_problem_vertices(faces, len(verts)) == [0]
    assert check_mesh(verts, faces, quick=True) == "non-manifold vertices"


def test_bad_winding_one_face():
    faces = list(F)
    faces[0] = flip(faces[0])
    assert find_bad_winding_pairs(faces) != []
    assert check_mesh(V, faces, quick=True) == "some bad windings"


def test_all_faces_inverted():
    faces = [flip(f) for f in F]
    assert _signed_volume(V, faces) == -1.0
    assert check_mesh(V, faces, quick=True) == "probably all windings are bad"

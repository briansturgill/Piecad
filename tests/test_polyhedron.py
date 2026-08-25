import pytest
from piecad import *


def _polyhedron(v, f, match):
    o = None
    if match != "":
        with pytest.raises(ValidationError, match=match):
            o = polyhedron(v, f, check="batch")
    else:
        o = polyhedron(v, f, check="batch")
    return o


def vertices():
    return [
        [0, 0, 0],
        [0, -5, 0],
        [0, 0, 5],
        [2, 0, 0],
        [2, -5, 0],
        [2, 0, 5],
    ]


def good_faces():
    return [
        [2, 0, 1],
        [3, 5, 4],
        [0, 2, 3],
        [2, 5, 3],
        [1, 0, 3],
        [1, 3, 4],
        [1, 5, 2],
        [1, 4, 5],
    ]


def bad_faces_one_wrong_wind():
    return [
        [2, 0, 1],
        [3, 5, 4],
        [0, 2, 3],
        [2, 3, 5],  # This one (#3) is the flipped one
        [1, 0, 3],
        [1, 3, 4],
        [1, 5, 2],
        [1, 4, 5],
    ]


def bad_faces_all_wrong_wind():
    return [
        [2, 1, 0],
        [3, 4, 5],
        [0, 3, 2],
        [2, 3, 5],
        [1, 3, 0],
        [1, 4, 3],
        [1, 2, 5],
        [1, 5, 4],
    ]


def non_manifold_e_vertices():
    return [
        [0.0, 0.0, 0.0],  # Vertex 0 (shared in a non-manifold way)
        [1.0, 0.0, 0.0],  # Vertex 1
        [0.0, 1.0, 0.0],  # Vertex 2
        [0.0, 0.0, 1.0],  # Vertex 3
        [-1.0, 0.0, 0.0],  # Vertex 4
        [0.0, -1.0, 0.0],  # Vertex 5
    ]


# Two separate surfaces share vertex v0 but are not connected in a single fan
def non_manifold_e_faces():
    return [
        [0, 1, 2],  # Triangle 1
        [0, 2, 3],  # Triangle 2
        [0, 3, 1],  # Triangle 3
        [0, 4, 5],  # Triangle 4 (disconnected from the first group but shares vertex 0)
        [0, 5, 2],  # Triangle 5 (also shares vertex 0 in a conflicting way)
    ]


def boundary_faces():
    return [
        # [2, 0, 1],
        [3, 5, 4],
        [0, 2, 3],
        [2, 5, 3],
        [1, 0, 3],
        [1, 3, 4],
        [1, 5, 2],
        [1, 4, 5],
    ]


def non_manifold_v_vertices():
    return [
        # Shared vertex
        [0, 0, 0],  # 0
        # Tetrahedron A
        [1, 0, 0],  # 1
        [0, 1, 0],  # 2
        [0, 0, 1],  # 3
        # Tetrahedron B
        [-1, 0, 0],  # 4
        [0, 0, -1],  # 5
        [0, -1, 0],  # 6
    ]


def non_manifold_v_faces():
    return [
        # Tetrahedron A
        [0, 2, 1],
        [0, 1, 3],
        [0, 3, 2],
        [1, 2, 3],
        # Tetrahedron B
        [0, 4, 5],
        [0, 6, 4],
        [0, 5, 6],
        [4, 6, 5],
    ]


def test_cube_from_polyhedron(benchmark):
    w = 10.0
    d = 10.0
    h = 10.0
    vertices = [
        (0.0, 0.0, 0.0),
        (0.0, 0.0, h),
        (0.0, d, 0.0),
        (0.0, d, h),
        (w, 0.0, 0.0),
        (w, 0.0, h),
        (w, d, 0),
        (w, d, h),
    ]
    faces = [
        (1, 0, 4),
        (2, 4, 0),
        (1, 3, 0),
        (3, 1, 5),
        (3, 2, 0),
        (3, 7, 2),
        (5, 4, 6),
        (5, 1, 4),
        (6, 4, 2),
        (7, 6, 2),
        (7, 3, 5),
        (7, 5, 6),
    ]

    out = benchmark(_polyhedron, vertices, faces, match="")
    assert out.num_verts() == 8


def test_polyhedron_data(benchmark):
    assert quick_check_mesh(vertices(), good_faces()) == ""
    assert (
        quick_check_mesh(vertices(), bad_faces_one_wrong_wind()) == "some bad windings"
    )
    assert (
        quick_check_mesh(vertices(), bad_faces_all_wrong_wind())
        == "probably all windings are bad"
    )
    assert (
        quick_check_mesh(non_manifold_e_vertices(), non_manifold_e_faces())
        == "non-manifold edges"
    )
    assert quick_check_mesh(vertices(), boundary_faces()) == "boundary edges"
    assert (
        quick_check_mesh(non_manifold_v_vertices(), non_manifold_v_faces())
        == "non-manifold vertices"
    )
    out1 = benchmark(_polyhedron, vertices(), good_faces(), match="")


def test_good_data(benchmark):
    out1 = benchmark(_polyhedron, vertices(), good_faces(), match="")


def test_some_bad_windings(benchmark):
    out1 = benchmark(
        _polyhedron,
        vertices(),
        bad_faces_one_wrong_wind(),
        match="Polyhedron is flawed: some bad windings",
    )


def test_all_bad_windings(benchmark):
    out1 = benchmark(
        _polyhedron,
        vertices(),
        bad_faces_all_wrong_wind(),
        match="Polyhedron is flawed: probably all windings are bad",
    )


def test_non_manifold_edges(benchmark):
    out1 = benchmark(
        _polyhedron,
        non_manifold_e_vertices(),
        non_manifold_e_faces(),
        match="Polyhedron is flawed: non-manifold edges",
    )


def test_boundary_edges(benchmark):
    out1 = benchmark(
        _polyhedron,
        vertices(),
        boundary_faces(),
        match="Polyhedron is flawed: boundary edges",
    )


def test_non_manifold_vertices(benchmark):
    out1 = benchmark(
        _polyhedron,
        non_manifold_v_vertices(),
        non_manifold_v_faces(),
        match="Polyhedron is flawed: non-manifold vertices",
    )


def test_interactive(benchmark):
    out1 = benchmark(_polyhedron, vertices(), good_faces(), match="")
    return  # LATER
    print("\nTEST: check a good mesh.")
    if check_mesh(vertices, good_faces):
        print("Good mesh passed.")
    print(
        "\nTEST: check one improperly wound face. Face #3 is the one that is wound wrong."
    )
    assert not check_mesh(vertices, bad_faces_one_wrong_wind)
    print("\nTEST: Check all faces wound wrong.")
    assert not check_mesh(vertices, bad_faces_all_wrong_wind)
    print("\nTEST: Check mesh with non-manifold edges. (adjacent count > 2)")
    assert not check_mesh(non_manifold_e_vertices, non_manifold_e_faces)
    print("\nTEST: Check mesh with boundary-manifold edges. (adjacent count = 1)")
    assert not check_mesh(vertices, boundary_faces)
    print("\nTEST: Check mesh with non-manifold vertex")
    assert not check_mesh(non_manifold_v_vertices, non_manifold_v_faces)

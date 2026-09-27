from types import SimpleNamespace

import pytest

from piecad._viewer import MeshViewer


def test_mesh_arrays_returns_plain_python_tuples():
    mesh = SimpleNamespace(
        vertices=[(0, 0, 0), (1, 0, 0), (0, 1, 0)],
        faces=[(0, 1, 2)],
    )

    vertices, faces = MeshViewer._mesh_arrays(mesh)

    assert vertices == [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)]
    assert faces == [(0, 1, 2)]
    assert isinstance(vertices, list)
    assert isinstance(faces, list)


@pytest.mark.parametrize(
    ("vertices", "faces", "message"),
    [
        ([(0, 0), (1, 0), (0, 1)], [(0, 1, 2)], "vertices"),
        ([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [(0, 1)], "faces"),
    ],
)
def test_mesh_arrays_rejects_non_triangular_data(vertices, faces, message):
    mesh = SimpleNamespace(vertices=vertices, faces=faces)

    with pytest.raises(ValueError, match=message):
        MeshViewer._mesh_arrays(mesh)


def test_face_colors_converts_integer_rgb_and_preserves_rgba():
    mesh = SimpleNamespace(
        visual=SimpleNamespace(face_colors=[(255, 128, 0), (10, 20, 30, 40)])
    )

    colors = MeshViewer._face_colors(mesh, 2)

    expected = [
        (1.0, 128 / 255, 0.0, 76 / 255),
        (10 / 255, 20 / 255, 30 / 255, 40 / 255),
    ]
    assert [channel for color in colors for channel in color] == pytest.approx(
        [channel for color in expected for channel in color]
    )


def test_face_colors_returns_none_for_count_mismatch():
    mesh = SimpleNamespace(visual=SimpleNamespace(face_colors=[(1, 2, 3)]))

    assert MeshViewer._face_colors(mesh, 2) is None


def test_visible_faces_culls_backfaces_with_python_lists():
    viewer = MeshViewer()
    viewer.culling = True
    vertices = [(0, 0, 0), (1, 0, 0), (0, 1, 0)]
    faces = [(0, 1, 2), (0, 2, 1)]

    assert viewer._visible_faces(vertices, faces) == [True, False]


def test_shade_colors_returns_rgba_tuples():
    viewer = MeshViewer()
    vertices = [(0, 0, 0), (1, 0, 0), (0, 1, 0)]
    faces = [(0, 1, 2)]
    colors = [(1.0, 0.5, 0.25, 0.3)]

    shaded = viewer._shade_colors(vertices, faces, colors)

    assert [channel for color in shaded for channel in color] == pytest.approx(
        [0.7, 0.35, 0.175, 0.3]
    )

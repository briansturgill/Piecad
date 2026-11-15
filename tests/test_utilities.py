import importlib
import platform
import sys
from contextlib import nullcontext
from types import SimpleNamespace

import pytest
import trimesh

from piecad import Config, Obj3d, cube, load, rectangle

utilities = importlib.import_module("piecad.utilities")


@pytest.mark.parametrize("args", [(5,), (2, 8), (9, 0, -2), (0, 0)])
def test_frange_with_integers_returns_range(args):
    from piecad import frange

    result = frange(*args)
    assert isinstance(result, range)
    assert result == range(*args)
    assert list(result) == list(result)


@pytest.mark.parametrize(
    ("args", "expected"),
    [
        ((2.5,), [0.0, 1.0, 2.0]),
        ((1, 3.5), [1.0, 2.0, 3.0]),
        ((0, 1, 0.25), [0.0, 0.25, 0.5, 0.75]),
        ((1.0, 0, -0.25), [1.0, 0.75, 0.5, 0.25]),
        ((0.0, 1, -1), []),
    ],
)
def test_frange_with_floats(args, expected):
    from piecad import frange

    assert list(frange(*args)) == expected


@pytest.mark.parametrize(
    ("args", "expected"),
    [
        ((4,), [0, 1, 2, 3, 4]),
        ((1, 5, 2), [1, 3, 5]),
        ((5, 1, -2), [5, 3, 1]),
        ((0, 1, -1), []),
    ],
)
def test_frange_with_inclusive_integers(args, expected):
    from piecad import frange

    result = frange(*args, inclusive=True)
    assert isinstance(result, range)
    assert list(result) == expected


@pytest.mark.parametrize(
    ("args", "expected"),
    [
        ((0.1, 0.3, 0.1), [0.1, 0.2, 0.3]),
        ((1.0, 0.0, -0.25), [1.0, 0.75, 0.5, 0.25, 0.0]),
        ((0.0, 1.0, 0.3), [0.0, 0.3, 0.6, 0.9]),
        ((1.0, 2.0, -0.25), []),
    ],
)
def test_frange_with_inclusive_floats(args, expected):
    from piecad import frange

    assert list(frange(*args, inclusive=True)) == pytest.approx(expected)


def test_frange_argument_errors():
    from piecad import frange

    for args in [(), (1, 2, 3, 4), (1, "str")]:
        with pytest.raises(TypeError):
            frange(*args)
    for args in [(0, 1, 0), (0, 1, 0.0)]:
        with pytest.raises(ValueError):
            frange(*args)
    with pytest.raises(TypeError):
        frange(start=1)

    values = frange(1e20, 1e20 + 1e6, 1.0)
    assert next(values) == 1e20
    with pytest.raises(ValueError):
        next(values)


@pytest.mark.parametrize(
    "args",
    [
        (float("inf"),),
        (float("-inf"),),
        (float("nan"),),
        (0.0, float("inf")),
        (0.0, 1.0, float("-inf")),
    ],
)
def test_frange_rejects_nonfinite_arguments(args):
    from piecad import frange

    with pytest.raises(ValueError, match="finite"):
        frange(*args)


def test_frange_inclusive_rejects_steps_that_cannot_advance():
    from piecad import frange

    values = frange(1e20, 1e20 + 1e6, 1.0, inclusive=True)
    assert next(values) == 1e20
    with pytest.raises(ValueError, match="too small to advance"):
        next(values)


def test_load_reads_mesh_vertices_and_faces(tmp_path):
    source = cube(2)
    vertices, faces = source.to_verts_and_faces()
    mesh = trimesh.Trimesh(vertices=vertices, faces=faces, process=False)
    filename = tmp_path / "cube.glb"
    mesh.export(str(filename))

    loaded = load(str(filename))

    assert loaded.bounding_box() == (0, 0, 0, 2, 2, 2)
    assert loaded.volume() == pytest.approx(8)


def test_view_uses_2d_object_color_or_default(monkeypatch):
    monkeypatch.setattr(utilities.atexit, "register", lambda *_args: None)
    monkeypatch.setattr(utilities, "_view_meshes", [])
    monkeypatch.setattr(utilities, "_view_meshes_titles", [])

    colored = utilities.view(rectangle((2, 3)).color("red"), title="colored")
    assert Obj3d.color_map[colored.mo.original_id()] == (255, 0, 0)

    default_color = Config.get_default_color()
    uncolored = utilities.view(rectangle((2, 3)), title="default")
    assert Obj3d.color_map[uncolored.mo.original_id()] == default_color


def test_get_save_dir_uses_windows_downloads_folder(monkeypatch):
    expected = r"C:\Users\test\Downloads"
    fake_winreg = SimpleNamespace(
        HKEY_CURRENT_USER=object(),
        OpenKey=lambda *_args: nullcontext(object()),
        QueryValueEx=lambda *_args: (expected, 0),
    )
    monkeypatch.setitem(sys.modules, "winreg", fake_winreg)
    monkeypatch.setattr(platform, "system", lambda: "Windows")
    monkeypatch.delenv("PIECAD_SAVE_DIR", raising=False)
    monkeypatch.setattr(utilities, "_save_dir", None)

    assert utilities._get_save_dir() == expected

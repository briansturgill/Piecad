import importlib
import platform
import sys
from contextlib import nullcontext
from types import SimpleNamespace

import pytest
import trimesh

from piecad import Config, Obj3d, cube, load, rectangle

utilities = importlib.import_module("piecad.utilities")


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

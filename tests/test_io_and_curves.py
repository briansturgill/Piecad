import os
import pytest
from piecad import *
from piecad import utilities
from piecad._path import Path

IMAGE = os.path.join(os.path.dirname(__file__), "..", "examples", "moon_lithophane.jpg")


@pytest.fixture
def save_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("PIECAD_SAVE_DIR", str(tmp_path))
    return tmp_path


def test_lithophane_from_image():
    o = lithophane(
        IMAGE, width_mm=20, pixel_size=1.0, min_thickness=0.5, max_thickness=2.0
    )
    bb = o.bounding_box()
    assert bb[3] - bb[0] == pytest.approx(20, abs=1.5)
    assert bb[5] - bb[2] <= 2.0 + 1e-6
    assert o.volume() > 0


@pytest.mark.parametrize("ext", ["stl", "stl_ascii", "obj", "ply", "glb", "3mf"])
def test_save_single_3d(tmp_path, ext):
    f = str(tmp_path / f"a.{ext}")
    save(f, cube(5))
    assert os.path.getsize(f) > 0
    if ext == "obj":
        assert open(f).read().endswith("\n")


@pytest.mark.parametrize("ext", ["stl", "glb", "obj"])
def test_save_multiple_3d(tmp_path, ext):
    f = str(tmp_path / f"m.{ext}")
    save(f, cube(5), sphere(3).translate([10, 0, 0]))
    assert os.path.getsize(f) > 0


def test_save_multiple_3mf(tmp_path):
    f = str(tmp_path / "m.3mf")
    save(f, cube(5), sphere(3).translate([10, 0, 0]))
    assert os.path.getsize(f) > 0


def test_save_3mf_with_color(tmp_path):
    f = str(tmp_path / "c.3mf")
    save(f, union(cube(5).color("red"), sphere(3).translate([10, 0, 0]).color("blue")))
    assert os.path.getsize(f) > 0


def test_save_bare_filename_uses_save_dir(save_dir):
    save("bare.stl", cube(5))
    assert (save_dir / "bare.stl").exists()


def test_save_svg(tmp_path):
    f = str(tmp_path / "a.svg")
    save(f, difference(square(10), circle(2)), square(3).translate([20, 0]))
    assert "<svg" in open(f).read()


def test_save_2d_wrong_format(tmp_path):
    with pytest.raises(ValidationError):
        save(str(tmp_path / "a.stl"), square(10))


def test_save_requires_object(tmp_path):
    with pytest.raises(ValidationError):
        save(str(tmp_path / "a.stl"))


def test_save_load_round_trip(tmp_path):
    f = str(tmp_path / "rt.glb")
    save(f, cube(5))
    assert load(f).volume() == pytest.approx(125, rel=1e-3)


def test_winding():
    assert winding([(0, 0), (1, 0), (1, 1), (0, 1)]) == "ccw"
    assert winding([(0, 0), (0, 1), (1, 1), (1, 0)]) == "cw"
    assert winding([(0, 0), (1, 1), (2, 2)]) == "zero"
    assert winding([(0, 0), (1, 1)]) == "too small"


CUBE_V = [
    (0, 0, 0),
    (1, 0, 0),
    (1, 1, 0),
    (0, 1, 0),
    (0, 0, 1),
    (1, 0, 1),
    (1, 1, 1),
    (0, 1, 1),
]
CUBE_F = [
    (0, 2, 1), (0, 3, 2), (4, 5, 6), (4, 6, 7), (0, 1, 5), (0, 5, 4),
    (1, 2, 6), (1, 6, 5), (2, 3, 7), (2, 7, 6), (3, 0, 4), (3, 4, 7),
]  # fmt: skip


def test_mesh_check_wrappers():
    assert quick_check_mesh(CUBE_V, CUBE_F) == ""
    assert quick_check_mesh(CUBE_V, CUBE_F[:-1]) != ""
    assert check_mesh(CUBE_V, CUBE_F) is True


def test_obj3d_from_vertices_and_faces_modes():
    for mode in ("none", "batch", "repair"):
        o = utilities.obj3d_from_vertices_and_faces(CUBE_V, CUBE_F, mode)
        assert o.volume() == pytest.approx(1)
    with pytest.raises(ValidationError):
        utilities.obj3d_from_vertices_and_faces(CUBE_V, CUBE_F[:-1], "batch")


def test_path_curves_and_arc():
    p = (
        Path((0, 0), segments=8)
        .line_to((10, 0))
        .quadratic_bezier_to((15, 5), (10, 10))
        .cubic_bezier_to((8, 12), (4, 12), (0, 10))
        .arc_to(5, (0, 0))
        .close()
    )
    assert p.area() > 0


@pytest.mark.parametrize("large", [False, True])
@pytest.mark.parametrize("ccw", [False, True])
def test_path_arc_flags(large, ccw):
    p = Path((0, 0)).arc_to((6, 4), (10, 0), 15, large, ccw).close()
    assert p.area() > 0


def test_path_bad_segments():
    with pytest.raises(ValidationError):
        Path((0, 0), segments=2)

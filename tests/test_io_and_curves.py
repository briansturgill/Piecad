import os
import xml.etree.ElementTree as ET
import ezdxf
import manifold3d
import pytest
from piecad import *
from piecad import _pystroker, utilities
from piecad import _lib3mf
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


def test_load_3mf_round_trip_uses_lib3mf(tmp_path, monkeypatch):
    filename = str(tmp_path / "cube.3mf")
    source = cube(5).translate([10, 0, 0])
    save(filename, source)

    def reject_trimesh_loader(*args, **kwargs):
        pytest.fail("3MF loading should use _lib3mf")

    monkeypatch.setattr(utilities.trimesh.exchange.load, "load", reject_trimesh_loader)
    restored = load(filename)
    assert restored.volume() == pytest.approx(source.volume())
    assert restored.bounding_box() == pytest.approx(source.bounding_box())
    assert load(filename, center=True).bounding_box() == pytest.approx(
        (-2.5, -2.5, -2.5, 2.5, 2.5, 2.5)
    )


def test_load_3mf_nested_transforms_and_build_items(tmp_path):
    wrapper = _lib3mf.Wrapper()
    model = wrapper.CreateModel()
    model.SetUnit(_lib3mf.ModelUnit.Inch)
    geometry = cube(5).mo.to_mesh64()
    mesh = model.AddMeshObject()
    mesh.SetGeometry(
        [_lib3mf.Position(v[:3]) for v in geometry.vert_properties],
        [_lib3mf.Triangle(t) for t in geometry.tri_verts],
    )
    component = model.AddComponentsObject()
    component.AddComponent(
        mesh,
        _lib3mf.Transform([[-1, 0, 0], [0, 1, 0], [0, 0, 1], [8, 0, 0]]),
    )
    parent = model.AddComponentsObject()
    parent.AddComponent(component, wrapper.GetTranslationTransform(2, 0, 0))
    model.AddBuildItem(parent, wrapper.GetTranslationTransform(10, 0, 0))
    model.AddBuildItem(mesh, wrapper.GetTranslationTransform(30, 0, 0))
    filename = str(tmp_path / "components.3MF")
    model.QueryWriter("3mf").WriteToFile(filename)

    restored = load(filename)
    assert restored.bounding_box() == pytest.approx((15, 0, 0, 35, 5, 5))
    assert restored.volume() == pytest.approx(250)


def test_load_3mf_invalid_and_empty_models(tmp_path):
    filename = tmp_path / "invalid.3mf"
    filename.write_bytes(b"not a 3mf archive")
    with pytest.raises(_lib3mf.ELib3MFException, match="Invalid 3MF ZIP container"):
        load(str(filename))

    model = _lib3mf.Wrapper().CreateModel()
    model.QueryWriter("3mf").WriteToFile(str(filename))
    with pytest.raises(ValidationError, match="no buildable mesh triangles"):
        load(str(filename))


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


@pytest.mark.parametrize("ext", ["svg", "dxf"])
def test_save_load_2d_round_trip(tmp_path, ext):
    source = difference(square(10), square(4).translate((3, 3)))
    filename = str(tmp_path / f"shape.{ext}")
    save(filename, source)
    restored = load(filename)
    assert isinstance(restored, Obj2d)
    assert restored.area() == pytest.approx(84)


def test_save_svg_round_trip_in_openscad_mode(tmp_path):
    source = difference(square(10), square(4).translate((3, 3)))
    filename = str(tmp_path / "shape.svg")
    save(filename, source)
    restored = load(filename, svg_openscad=True)
    assert restored.area() == pytest.approx(source.area())
    assert restored.bounding_box() == pytest.approx(source.bounding_box())


def test_load_svg_fills_open_paths(tmp_path):
    filename = tmp_path / "open.SVG"
    filename.write_text('<svg><path d="M10 20 L14 20 L14 23 L10 23"/></svg>')
    shape = load(str(filename))
    assert shape.area() == pytest.approx(12)
    assert shape.bounding_box() == (10, 20, 14, 23)


def test_load_dxf_ignores_open_paths(tmp_path):
    filename = tmp_path / "open.DXF"
    (
        Path((0, 0))
        .line_to((4, 0))
        .line_to((4, 4))
        .line_to((0, 4))
        .sub_path((10, 0))
        .line_to((12, 0))
        .line_to((12, 2))
        .line_to((10, 2))
        .close()
        .to_dxf(filename)
    )
    shape = load(str(filename))
    assert shape.area() == pytest.approx(4)
    assert shape.bounding_box() == (10, 0, 12, 2)


def test_load_svg_reports_unsupported_elements(tmp_path):
    filename = tmp_path / "unsupported.svg"
    filename.write_text('<svg><rect width="10" height="10"/></svg>')
    with pytest.raises(ValidationError, match="Unsupported SVG element"):
        load(str(filename))


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


def test_obj3d_from_v_and_f_modes():
    for mode in ("none", "batch", "repair"):
        o = utilities.obj3d_from_v_and_f(CUBE_V, CUBE_F, mode)
        assert o.volume() == pytest.approx(1)
    with pytest.raises(ValidationError):
        utilities.obj3d_from_v_and_f(CUBE_V, CUBE_F[:-1], "batch")


def test_path_curves_and_arc():
    p = (
        Path((0, 0), segments=8)
        .line_to((10, 0))
        .quadratic_bezier_to((15, 5), (10, 10))
        .cubic_bezier_to((8, 12), (4, 12), (0, 10))
        .arc_to(5, (0, 0))
        .close()
        .to_obj2d()
    )
    assert p.area() > 0


@pytest.mark.parametrize("large", [False, True])
@pytest.mark.parametrize("ccw", [False, True])
def test_path_arc_flags(large, ccw):
    p = Path((0, 0)).arc_to((6, 4), (10, 0), 15, large, ccw).close().to_obj2d()
    assert p.area() > 0


def test_path_bad_segments():
    with pytest.raises(ValidationError):
        Path((0, 0), segments=2)


def test_path_to_obj2d_evenodd_and_open():
    p = (
        Path((0, 0))
        .line_to((10, 0))
        .line_to((10, 10))
        .line_to((0, 10))
        .close()
        .sub_path((2, 2))
        .line_to((8, 2))
        .line_to((8, 8))
        .line_to((2, 8))
        .close()
        .sub_path((4, 4))
        .line_to((6, 4))
        .line_to((6, 6))
        .line_to((4, 6))
        .close()
        .sub_path((20, 0))
        .line_to((24, 0))
        .line_to((24, 4))
        .line_to((20, 4))
    )
    assert p.to_obj2d().area() == pytest.approx(68)
    assert p.to_obj2d(include_open=True).area() == pytest.approx(84)
    assert not p.to_commands()[-1]["closed"]
    assert Path().to_obj2d().area() == 0


def test_path_svg_roundtrip(tmp_path):
    p = (
        Path((1, 2), segments=12)
        .line_to((4, 2))
        .quadratic_bezier_to((5, 3), (4, 4))
        .cubic_bezier_to((3, 5), (2, 5), (1, 4))
        .arc_to((2, 3), (1, 2), 20, True, True)
        .close()
        .sub_path((10, 10))
        .line_to((11, 12))
        .sub_path((-1, -2))
    )
    filename = tmp_path / "path.svg"
    p.to_svg(filename)
    root = ET.parse(filename).getroot()
    assert root[0].get("fill-rule") == "evenodd"
    restored = Path.from_svg(filename, segments=12)
    assert restored.to_commands() == p.to_commands()
    assert restored.to_obj2d().area() == pytest.approx(p.to_obj2d().area())


@pytest.mark.parametrize(
    ("path", "bounds"),
    [
        (Path((0, 0)).quadratic_bezier_to((5, 10), (10, 0)), (0, 0, 10, 5)),
        (Path((0, 0)).cubic_bezier_to((0, 10), (10, 10), (10, 0)), (0, 0, 10, 7.5)),
        (
            Path((0, 0)).arc_to((6, 4), (10, 0), 15, True, True),
            (
                -1.4845437160905615,
                -6.2353268395144985,
                11.774591973880776,
                6.2353268395144985,
            ),
        ),
        (
            Path((0, 0)).arc_to((6, 4), (10, 0), 15, False, False),
            (0, 0, 10, 2.0928772795391684),
        ),
    ],
)
def test_path_svg_exact_curve_viewbox(tmp_path, path, bounds):
    filename = tmp_path / "curves.svg"
    path.to_svg(filename)
    viewbox = ET.parse(filename).getroot().get("viewBox")
    assert viewbox is not None
    assert tuple(map(float, viewbox.split())) == pytest.approx(bounds)


def test_path_svg_relative_scaled_and_degenerate_arcs(tmp_path):
    filename = tmp_path / "arcs.svg"
    filename.write_text(
        '<svg><path d="M10 10 L20 10 z m2 3 ' 'a1 1 0 0 1 10 0 a0 3 0 0 1 2 0"/></svg>'
    )
    parts = Path.from_svg(filename).to_commands()
    assert parts[1] == {
        "start": (12, 13),
        "commands": [
            ("arc", (5, 5), (22, 13), 0, False, True),
            ("line", (24, 13)),
        ],
        "closed": False,
    }


def test_path_svg_import_relative_and_close(tmp_path):
    filename = tmp_path / "input.svg"
    filename.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg"><g fill-rule="evenodd">'
        '<path d="M10-20 h10 v10 h-10 z m2 2 l3 0 0 3 z M40 0 L40 0"/>'
        "</g></svg>"
    )
    p = Path.from_svg(filename)
    assert p.to_commands() == [
        {
            "start": (10, -20),
            "commands": [
                ("line", (20, -20)),
                ("line", (20, -10)),
                ("line", (10, -10)),
                ("close",),
            ],
            "closed": True,
        },
        {
            "start": (12, -18),
            "commands": [("line", (15, -18)), ("line", (15, -15)), ("close",)],
            "closed": True,
        },
        {"start": (40, 0), "commands": [("line", (40, 0))], "closed": False},
    ]


def test_path_svg_degenerate_arcs_and_close_followed_by_line(tmp_path):
    p = Path((0, 0)).arc_to(5, (0, 0)).arc_to(0, (2, 0))
    filename = tmp_path / "degenerate.svg"
    p.to_svg(filename)
    assert Path.from_svg(filename).to_points() == p.to_points()
    filename.write_text('<svg><path d="M0 0 L2 0 Z l0 2"/></svg>')
    parts = Path.from_svg(filename).to_commands()
    assert parts[0]["closed"]
    assert parts[1] == {
        "start": (0, 0),
        "commands": [("line", (0, 2))],
        "closed": False,
    }


@pytest.mark.parametrize(
    "body",
    [
        '<path fill-rule="nonzero" d="M0 0 L1 1"/>',
        '<rect width="10" height="10"/>',
        '<path d="M0 0 L1 1 garbage"/>',
        '<g transform="translate(2) nonsense"><path d="M0 0 L1 1"/></g>',
        '<path transform="scale(2 3 4)" d="M0 0 L1 1"/>',
        '<use href="#p"/>',
    ],
)
def test_path_svg_rejects_unsupported_input(tmp_path, body):
    filename = tmp_path / "input.svg"
    filename.write_text(f'<svg xmlns="http://www.w3.org/2000/svg">{body}</svg>')
    with pytest.raises(ValidationError):
        Path.from_svg(filename)


def test_path_svg_ignores_metadata_and_definitions(tmp_path):
    filename = tmp_path / "input.svg"
    filename.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" '
        'xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd">'
        "<sodipodi:namedview><unknown/></sodipodi:namedview>"
        '<metadata><unknown><path d="M20 20 L30 30"/></unknown></metadata>'
        '<defs><path id="p" d="M20 20 L30 30"/><use href="#p"/></defs>'
        '<path d="M0 0 L2 0 L2 2 Z"/></svg>'
    )
    assert Path.from_svg(filename).to_commands() == [
        {
            "start": (0, 0),
            "commands": [("line", (2, 0)), ("line", (2, 2)), ("close",)],
            "closed": True,
        }
    ]


def test_path_svg_nested_transforms_and_curves(tmp_path):
    filename = tmp_path / "input.svg"
    filename.write_text(
        '<svg><g transform="translate(10 20) scale(2 3)">'
        '<path transform="translate(1 2)" '
        'd="M0 0 L1 1 Q2 1 3 2 C4 2 5 3 6 4 Z"/></g></svg>'
    )
    assert Path.from_svg(filename).to_commands() == [
        {
            "start": (12, 26),
            "commands": [
                ("line", (14, 29)),
                ("quadratic", (16, 29), (18, 32)),
                ("cubic", (20, 32), (22, 35), (24, 38)),
                ("close",),
            ],
            "closed": True,
        }
    ]


def test_path_svg_transformed_arc_samples_original_curve(tmp_path):
    filename = tmp_path / "input.svg"
    filename.write_text(
        '<svg><path transform="matrix(-1 0.5 0.3 2 8 4)" '
        'd="M0 0 A5 3 30 0 1 8 2"/></svg>'
    )
    original = Path((0, 0), segments=12).arc_to((5, 3), (8, 2), 30, False, True)
    points = Path.from_svg(filename, segments=12).to_points()[0]
    expected = [
        (8 - x + 0.3 * y, 4 + 0.5 * x + 2 * y) for x, y in original.to_points()[0]
    ]
    assert len(points) == len(expected)
    for actual, wanted in zip(points, expected):
        assert actual == pytest.approx(wanted)


def test_load_svg_openscad_reference_geometry(tmp_path):
    # OpenSCAD 2021.01 exports these shapes as three contours with area 274.
    filename = tmp_path / "input.svg"
    filename.write_text(
        '<svg width="100mm" height="50mm" viewBox="0 0 100 50">'
        '<defs><path d="M70 10 L80 10 L80 20 L70 20 Z"/></defs>'
        '<g transform="translate(10 5)">'
        '<path d="M0 0 L10 0 L10 10 L0 10 Z"/></g>'
        '<path d="M15 5 L25 5 L25 15 L15 15 Z"/>'
        '<path style="fill:none" d="M35 5 L45 5 L45 15 L35 15 Z"/>'
        '<path stroke-width="2" d="M50 5 L60 5"/>'
        "</svg>"
    )
    shape = load(str(filename), svg_openscad=True)
    assert shape.bounding_box() == pytest.approx((10, 35, 61, 46))
    assert shape.area() == pytest.approx(274)
    assert len(shape.to_paths()) == 3
    expected = union(
        square(10).translate((10, 35)),
        square(10).translate((15, 35)),
        square(10).translate((35, 35)),
        rectangle((12, 2)).translate((49, 44)),
    )
    assert difference(shape, expected).area() == pytest.approx(0, abs=1e-8)
    assert difference(expected, shape).area() == pytest.approx(0, abs=1e-8)


@pytest.mark.parametrize(
    ("join", "cap", "area"),
    [
        ("miter", "butt", 4000000000),
        ("miter", "square", 4400000000),
        ("miter", "round", 4314149055),
        ("square", "butt", 3982841918),
        ("square", "square", 4382841918),
        ("square", "round", 4296990973),
        ("round", "butt", 3978537250),
        ("round", "square", 4378537250),
        ("round", "round", 4292686305),
    ],
)
def test_stroker_caps_and_joins(join, cap, area):
    contours = _pystroker.stroke(
        [(0, 0), (100000, 0), (100000, 100000)], 10000, join, cap
    )
    shape = manifold3d.CrossSection(contours, manifold3d.FillRule.NonZero)
    assert shape.area() == pytest.approx(area, rel=0.00005)


def test_stroker_handles_self_crossings_and_holes():
    contours = _pystroker.stroke(
        [(0, 0), (100000, 100000), (0, 100000), (100000, 0)],
        10000,
        "miter",
        "butt",
    )
    shape = manifold3d.CrossSection(contours, manifold3d.FillRule.NonZero)
    assert shape.area() == pytest.approx(7041246512, rel=0.00005)
    assert len(contours) == 2


def test_stroker_short_segments_and_reversals():
    contours = _pystroker.stroke(
        [(0, 0), (100000, 0), (100000, 0), (50000, 0)],
        10000,
        "round",
        "butt",
    )
    shape = manifold3d.CrossSection(contours, manifold3d.FillRule.NonZero)
    assert shape.area() == pytest.approx(2157074528, rel=0.00005)


def test_stroker_round_join_with_short_segment():
    contours = _pystroker.stroke(
        [
            (-94919, 96352),
            (41405, -86347),
            (-8260, -41222),
            (70431, -82013),
            (70853, -89447),
        ],
        10000,
        "round",
        "butt",
    )
    shape = manifold3d.CrossSection(contours, manifold3d.FillRule.NonZero)
    assert shape.area() == pytest.approx(6129753761, rel=0.00005)


def test_load_svg_openscad_round_stroke_and_transform(tmp_path):
    filename = tmp_path / "rounded.svg"
    filename.write_text(
        '<svg width="100mm" height="100mm" viewBox="0 0 100 100">'
        '<path transform="translate(5 10)" stroke-width="2" '
        'stroke-linecap="round" stroke-linejoin="round" '
        'd="M0 0 L10 0 L10 10"/></svg>'
    )
    shape = load(str(filename), svg_openscad=True)
    assert shape.area() == pytest.approx(42.92686305, rel=0.00005)
    assert shape.bounding_box() == pytest.approx((4, 79, 16, 91), abs=0.0001)


def test_stroker_rejects_invalid_input():
    with pytest.raises(ValueError, match="radius"):
        _pystroker.stroke([(0, 0), (1, 0)], 0, "round", "round")
    with pytest.raises(ValueError, match="distinct"):
        _pystroker.stroke([(0, 0), (0, 0)], 1, "round", "round")
    with pytest.raises(OverflowError, match="coordinate limit"):
        _pystroker.stroke([(0, 0), (1 << 62, 0)], 1, "round", "round")


def test_load_svg_openscad_compound_paths_and_separate_shapes(tmp_path):
    filename = tmp_path / "input.svg"
    filename.write_text(
        '<svg width="100mm" height="100mm" viewBox="0 0 100 100">'
        '<path d="M0 0 L20 0 L20 20 L0 20 Z M5 5 L15 5 L15 15 L5 15 Z"/>'
        '<path d="M30 0 L50 0 L50 20 L30 20 Z M35 5 L35 15 L45 15 L45 5 Z"/>'
        '<path d="M60 0 L80 0 L80 20 L60 20 Z"/>'
        '<path d="M65 5 L75 5 L75 15 L65 15 Z"/>'
        "</svg>"
    )
    shape = load(str(filename), svg_openscad=True)
    assert shape.area() == pytest.approx(1000)
    assert len(shape.to_paths()) == 5


def test_load_svg_openscad_rejects_visible_use(tmp_path):
    filename = tmp_path / "input.svg"
    filename.write_text(
        '<svg><defs><path id="p" d="M0 0 L1 0 L1 1 Z"/></defs>' '<use href="#p"/></svg>'
    )
    with pytest.raises(ValidationError, match="Unsupported SVG element: use"):
        load(str(filename), svg_openscad=True)


def test_load_svg_openscad_center_matches_viewbox_origin(tmp_path):
    filename = tmp_path / "input.svg"
    filename.write_text(
        '<svg width="100mm" height="100mm" viewBox="10 20 100 100">'
        '<path d="M20 30 L30 30 L30 40 L20 40 Z"/></svg>'
    )
    shape = load(str(filename), svg_openscad=True, center=True)
    assert shape.bounding_box() == pytest.approx((-15, -25, -5, -15))


def test_load_svg_openscad_viewport_alignment(tmp_path):
    filename = tmp_path / "input.svg"
    filename.write_text(
        '<svg width="200mm" height="100mm" viewBox="10 20 100 100">'
        '<path d="M20 30 L30 30 L30 40 L20 40 Z"/></svg>'
    )
    shape = load(str(filename), svg_openscad=True)
    assert shape.bounding_box() == pytest.approx((60, 40, 70, 50))


def test_load_svg_openscad_final_open_subpath_after_close(tmp_path):
    filename = tmp_path / "input.svg"
    filename.write_text(
        '<svg width="100mm" height="100mm" viewBox="0 0 100 100">'
        '<path d="M0 0 L10 0 L10 10 Z M20 0 L30 0 L30 10" stroke-width="2"/>'
        "</svg>"
    )
    shape = load(str(filename), svg_openscad=True)
    assert shape.bounding_box() == pytest.approx((0, 90, 30, 100))
    assert shape.area() == pytest.approx(100)


def test_path_dxf_roundtrip_sampled_curves(tmp_path):
    p = (
        Path((0, 0), segments=8)
        .line_to((10, 0))
        .quadratic_bezier_to((12, 5), (10, 10))
        .line_to((0, 10))
        .close()
        .sub_path((2, 2))
        .line_to((3, 2))
        .line_to((3, 3))
        .line_to((2, 3))
        .close()
        .sub_path((20, 0))
        .arc_to(5, (25, 5))
    )
    filename = tmp_path / "path.dxf"
    p.to_dxf(filename)
    restored = Path.from_dxf(filename, segments=8)
    assert restored.to_points() == p.to_points()
    assert [part["closed"] for part in restored.to_commands()] == [True, True, False]
    assert restored.to_obj2d().area() == pytest.approx(p.to_obj2d().area())


def test_path_dxf_import_r12_and_reject_bulges(tmp_path):
    doc = ezdxf.new("R12")
    doc.modelspace().add_polyline2d([(0, 0), (2, 0), (2, 2)], close=True)
    filename = tmp_path / "input.dxf"
    doc.saveas(filename)
    assert Path.from_dxf(filename).to_obj2d().area() == pytest.approx(2)
    doc = ezdxf.new()
    doc.modelspace().add_lwpolyline([(0, 0, 1), (2, 0, 0)], format="xyb")
    doc.saveas(filename)
    with pytest.raises(ValidationError, match="bulge"):
        Path.from_dxf(filename)

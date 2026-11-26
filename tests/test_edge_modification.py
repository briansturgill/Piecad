import math
import pytest

from piecad import Obj3d, ValidationError, cone, cuboid, cylinder, difference, polygon
from piecad._edge_modification import (
    bevel_2d,
    bevel_3d,
    classify_edges,
    comma_2d,
    comma_3d,
    face_normal,
    fillet_2d,
    fillet_3d,
    sawtooth_2d,
    sawtooth_3d,
    faceted_2d,
    faceted_3d,
)


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
    # and both adjacent face normals (used by modify_edges's
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


@pytest.mark.parametrize("mod_type", ["fillet", "chamfer"])
def test_modify_edges_min_edge_length_filters_short_edges(mod_type):
    block = cuboid([10.0, 10.0, 10.0])

    unfiltered = block.modify_edges(
        mod_type=mod_type,
        size=0.5,
        min_edge_length=2.0,
        angle_range=(80, 100),
        include=None,
        exclude=None,
    )
    filtered = block.modify_edges(
        mod_type=mod_type,
        size=0.5,
        min_edge_length=20.0,
        angle_range=(80, 100),
        include=None,
        exclude=None,
    )

    assert unfiltered.volume() < block.volume()
    assert filtered.volume() == pytest.approx(block.volume())


@pytest.mark.parametrize("mod_type", ["fillet", "chamfer"])
def test_modify_edges_angle_range_filters_by_dihedral_angle(mod_type):
    block = cuboid([10.0, 10.0, 10.0])

    in_range = block.modify_edges(
        mod_type=mod_type,
        size=0.5,
        min_edge_length=2.0,
        angle_range=(80, 100),
        include=None,
        exclude=None,
    )
    out_of_range = block.modify_edges(
        mod_type=mod_type,
        size=0.5,
        min_edge_length=2.0,
        angle_range=(0, 10),
        include=None,
        exclude=None,
    )

    assert in_range.volume() < block.volume()
    assert out_of_range.volume() == pytest.approx(block.volume())


@pytest.mark.parametrize("mod_type", ["fillet", "chamfer"])
def test_modify_edges_include_and_exclude_use_endpoint_bounding_boxes(mod_type):
    block = cuboid([10.0, 10.0, 10.0])
    one_vertical_edge = [(-0.1, -0.1, -0.1, 0.1, 0.1, 10.1)]

    only_included = block.modify_edges(
        mod_type=mod_type,
        size=0.5,
        min_edge_length=2.0,
        angle_range=(80, 100),
        include=one_vertical_edge,
        exclude=None,
    )
    excluded_same_edge = block.modify_edges(
        mod_type=mod_type,
        size=0.5,
        min_edge_length=2.0,
        angle_range=(80, 100),
        include=one_vertical_edge,
        exclude=one_vertical_edge,
    )
    full = block.modify_edges(
        mod_type=mod_type,
        size=0.5,
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


@pytest.mark.parametrize("reverse", [False, True])
def test_modify_edge_selects_one_edge_in_either_endpoint_order(reverse):
    block = cuboid((10, 10, 10))
    edge = ((0, 0, 0), (0, 0, 10))
    if reverse:
        edge = edge[::-1]
    result = block.modify_edge(edge, "fillet", size=0.5)
    expected = block.modify_edges(
        "fillet", size=0.5, include=[(-0.1, -0.1, -0.1, 0.1, 0.1, 10.1)]
    )

    assert 0 < result.volume() < block.volume()
    assert difference(expected, result).volume() == pytest.approx(0, abs=1e-8)
    assert difference(result, expected).volume() == pytest.approx(0, abs=1e-8)


@pytest.mark.parametrize(
    ("profile_2d", "cutter_3d"),
    [
        (bevel_2d, bevel_3d),
        (comma_2d, comma_3d),
        (fillet_2d, fillet_3d),
        (faceted_2d, faceted_3d),
    ],
)
def test_2d_profile_matches_straight_cutter_cross_section(profile_2d, cutter_3d):
    edge = ((-2, 0, 0), (2, 0, 0), (0, -1, 0), (0, 0, -1))
    profile = profile_2d(size=1)
    cutter = cutter_3d(edge, size=1)

    assert profile.area() > 0
    assert cutter.volume() == pytest.approx(4 * profile.area(), rel=1e-6)


def test_sawtooth_profile_is_a_section_of_the_varying_cutter():
    edge = ((-1, 0, 0), (1, 0, 0), (0, -1, 0), (0, 0, -1))
    cutter = sawtooth_3d(edge, size=1).transform(
        ((0, 1, 0, 0), (0, 0, 1, 0), (1, 0, 0, 0))
    )
    center = cutter.slice(0)
    other_section = cutter.slice(0.5)
    profile = sawtooth_2d(size=1)

    assert difference(profile, center).area() == pytest.approx(0, abs=1e-8)
    assert difference(center, profile).area() == pytest.approx(0, abs=1e-8)
    assert abs(center.area() - other_section.area()) > 1e-3


@pytest.mark.parametrize(
    "mod_type", ["bevel", "chamfer", "comma", "fillet", "sawtooth", "faceted"]
)
@pytest.mark.parametrize(
    ("height", "outward"), [(0, True), (10, True), (0, False), (10, False)]
)
def test_modify_circular_edges_cuts_selected_rim(mod_type, height, outward):
    block = cylinder(10, 10)
    if not outward:
        block = difference(block, cylinder(10, 5))
    radius = 10 if outward else 5

    result = block.modify_circular_edges(
        mod_type, (0, 0, height), radius, outward, size=1
    )
    removed = difference(block, result)

    assert 0 < result.volume() < block.volume()
    near_rim = 0.25 if height == 0 else 9.75
    away_from_rim = 9.75 if height == 0 else 0.25
    assert removed.slice(near_rim).area() > 0.1
    assert removed.slice(away_from_rim).area() == pytest.approx(0, abs=1e-6)


@pytest.mark.parametrize("outward", [True, False])
def test_modify_elliptical_edges_matches_scaled_circular_cutter(outward):
    circle = cylinder(10, 8)
    if not outward:
        circle = difference(circle, cylinder(10, 4))
    radius = 8 if outward else 4
    ellipse = circle.scale((1, 1.5, 1)).translate((4, -3, 2))
    expected = (
        circle.modify_circular_edges("chamfer", (0, 0, 10), radius, outward, size=1)
        .scale((1, 1.5, 1))
        .translate((4, -3, 2))
    )

    result = ellipse.modify_circular_edges(
        "chamfer", (4, -3, 12), (radius, radius * 1.5), outward, size=1
    )

    assert difference(expected, result).volume() == pytest.approx(0, abs=1e-7)
    assert difference(result, expected).volume() == pytest.approx(0, abs=1e-7)


@pytest.mark.parametrize("outward", [True, False])
def test_circular_cutter_matches_rotated_rim_segments(outward):
    block = cylinder(10, 10, segments=7)
    if not outward:
        block = difference(block, cylinder(10, 5, segments=7))
    block = block.rotate((0, 0, 13))
    radius = 10 if outward else 5

    result = block.modify_circular_edges("chamfer", (0, 0, 10), radius, outward, size=1)
    expected = cylinder(10, 9.5 if outward else 10, segments=7)
    if not outward:
        expected = difference(expected, cylinder(10, 5.5, segments=7))
    expected_slice = expected.rotate((0, 0, 13)).slice(9.5)
    actual_slice = result.slice(9.5)

    assert difference(expected_slice, actual_slice).area() == pytest.approx(0, abs=1e-5)
    assert difference(actual_slice, expected_slice).area() == pytest.approx(0, abs=1e-5)


@pytest.mark.parametrize(
    ("origin", "radius", "outward"),
    [((0, 0, 5), 10, True), ((0, 0, 10), 8, True), ((0, 0, 10), 10, False)],
)
def test_modify_circular_edges_rejects_unmatched_rim(origin, radius, outward):
    with pytest.raises(ValueError, match="could not uniquely identify"):
        cylinder(10, 10).modify_circular_edges(
            "fillet", origin, radius, outward, size=1
        )


@pytest.mark.parametrize("radius", [0, -1, float("inf"), (1, 0), (1, 2, 3)])
def test_modify_circular_edges_rejects_invalid_radius(radius):
    with pytest.raises(ValueError, match="radius"):
        cylinder(10, 10).modify_circular_edges("fillet", (0, 0, 10), radius, size=1)


def test_modify_circular_edges_rejects_invalid_geometry_and_type():
    block = cylinder(10, 10)
    with pytest.raises(ValueError, match="origin"):
        block.modify_circular_edges("fillet", (0, float("nan"), 10), 10, size=1)
    with pytest.raises(ValueError, match="outer radius"):
        block.modify_circular_edges("fillet", (0, 0, 10), 1, size=1)
    with pytest.raises(ValueError, match="could not uniquely identify"):
        Obj3d().modify_circular_edges("fillet", (0, 0, 10), 10, size=1)
    with pytest.raises(ValueError, match="could not uniquely identify"):
        cone(10, 10, 5).modify_circular_edges("fillet", (0, 0, 10), 5, size=1)
    with pytest.raises(ValidationError, match="mod_type"):
        block.modify_circular_edges("invalid", (0, 0, 10), 10, size=1)


def test_modify_circular_edges_rejects_irregular_segments():
    points = [
        (10 * math.cos(angle), 10 * math.sin(angle))
        for angle in (0, math.pi / 4, math.pi, 3 * math.pi / 2)
    ]
    block = polygon([points]).extrude(10)

    with pytest.raises(ValueError, match="regularly segmented"):
        block.modify_circular_edges("fillet", (0, 0, 10), 10, size=1)


@pytest.mark.parametrize("mod_type", ["comma", "sawtooth", "faceted"])
def test_modify_edges_supports_printable_profiles(mod_type):
    block = cuboid((10, 10, 10))
    result = block.modify_edges(
        mod_type, size=0.5, include=[(-0.1, -0.1, -0.1, 10.1, 0.1, 0.1)]
    )

    assert 0 < result.volume() < block.volume()

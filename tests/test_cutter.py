import pytest

from piecad import chamfer, cuboid, fillet
from piecad._cutter import cutter
from piecad._f_and_c import classify_edges, do_f_and_c
from piecad.lin_math import Vec3


@pytest.mark.parametrize(
    ("operation", "kwargs"),
    [(fillet, {"radius": 0.5}), (chamfer, {"bevel_size": 0.5})],
    ids=["fillet", "chamfer"],
)
def test_fillet_and_chamfer_modify_cuboid_edges(operation, kwargs):
    block = cuboid([10.0, 10.0, 10.0])

    result = operation(block, **kwargs)

    assert result.volume() > 0.0
    assert result.volume() < block.volume()
    assert result.bounding_box() == pytest.approx(block.bounding_box())


def test_fillet_and_chamfer_produce_different_edge_profiles():
    block = cuboid([10.0, 10.0, 10.0])

    filleted = fillet(block, radius=0.5)
    chamfered = chamfer(block, bevel_size=0.5)

    assert filleted.volume() != pytest.approx(chamfered.volume())


def test_fillet_and_chamfer_use_distinct_radius_keyword_names():
    # `fillet`'s radius and `chamfer`'s bevel_size are deliberately
    # different keyword names; passing the wrong one must fail loudly
    # instead of silently falling back to a default.
    block = cuboid([10.0, 10.0, 10.0])

    with pytest.raises(TypeError):
        chamfer(block, radius=0.5)

    with pytest.raises(TypeError):
        fillet(block, bevel_size=0.5)


def test_min_edge_length_excludes_all_short_edges():
    block = cuboid([10.0, 10.0, 10.0])

    result = fillet(block, radius=0.5, min_edge_length=20.0)

    assert result.volume() == pytest.approx(block.volume())
    assert result.bounding_box() == pytest.approx(block.bounding_box())


def test_min_edge_length_includes_edges_at_or_above_threshold():
    block = cuboid([10.0, 10.0, 10.0])

    result = fillet(block, radius=0.5, min_edge_length=10.0)

    assert result.volume() < block.volume()


def test_angle_range_excludes_edges_outside_range():
    block = cuboid([10.0, 10.0, 10.0])

    # A cuboid's convex edges all have a 90 degree dihedral signature;
    # a range that excludes 90 degrees must select nothing.
    result = fillet(block, radius=0.5, angle_range=(0, 10))

    assert result.volume() == pytest.approx(block.volume())


def test_angle_range_includes_edges_inside_range():
    block = cuboid([10.0, 10.0, 10.0])

    result = fillet(block, radius=0.5, angle_range=(80, 100))

    assert result.volume() < block.volume()


def test_include_restricts_to_edges_within_bounding_boxes():
    block = cuboid([10.0, 10.0, 10.0])

    full = fillet(block, radius=0.5)
    one_edge = fillet(
        block,
        radius=0.5,
        include=[(-0.1, -0.1, -0.1, 0.1, 0.1, 10.1)],
    )

    assert one_edge.volume() < block.volume()
    # Restricting to a single edge's bounding box must remove strictly
    # less material than filleting every edge.
    assert one_edge.volume() > full.volume()


def test_exclude_takes_precedence_over_include():
    block = cuboid([10.0, 10.0, 10.0])
    same_bbox = [(-0.1, -0.1, -0.1, 0.1, 0.1, 10.1)]

    result = fillet(block, radius=0.5, include=same_bbox, exclude=same_bbox)

    assert result.volume() == pytest.approx(block.volume())


def test_exclude_without_include_removes_only_excluded_edges():
    block = cuboid([10.0, 10.0, 10.0])
    excluded_bbox = [(-0.1, -0.1, -0.1, 0.1, 0.1, 10.1)]

    full = fillet(block, radius=0.5)
    without_one_edge = fillet(block, radius=0.5, exclude=excluded_bbox)

    assert without_one_edge.volume() > full.volume()
    assert without_one_edge.volume() < block.volume()


@pytest.mark.parametrize("fillet_flag", [True, False], ids=["fillet", "chamfer"])
def test_cutter_removes_material_consistently_for_every_cube_edge(fillet_flag):
    # Regression test: every one of a cube's 12 convex edges must be cut
    # from the correct side regardless of the edge's orientation in
    # world space (previously, some edge orientations produced a cutter
    # mirrored to the wrong side, which silently left the edge
    # untouched or cut from the wrong location).
    block = cuboid([10.0, 10.0, 10.0])
    vertices, faces = block.to_verts_and_faces()
    _, outer_edges = classify_edges(vertices, faces)
    assert len(outer_edges) == 12

    pad = 0.05
    for edge, _edge_length, _signed_angle, normal_1, normal_2 in outer_edges:
        vertex_1 = vertices[edge[0]]
        vertex_2 = vertices[edge[1]]
        bbox = tuple(
            min(vertex_1[axis], vertex_2[axis]) - pad for axis in range(3)
        ) + tuple(max(vertex_1[axis], vertex_2[axis]) + pad for axis in range(3))

        result = do_f_and_c(
            block,
            fillet=fillet_flag,
            radius=0.5,
            min_edge_length=2.0,
            angle_range=(80, 100),
            include=[bbox],
            exclude=None,
        )

        assert result.volume() < block.volume() - 1e-9
        assert result.bounding_box() == pytest.approx(block.bounding_box())


def test_cutter_base_rectangle_matches_requested_footprint():
    # The cutter's rectangular base must span exactly the edge length
    # and the requested radius, regardless of which face normal is
    # passed first.
    v1 = (0.0, 0.0, 0.0)
    v2 = (0.0, 0.0, 4.0)
    n1 = (0.0, -1.0, 0.0)
    n2 = (-1.0, 0.0, 0.0)
    radius = 1.5

    first_order = cutter(True, v1, v2, n1, n2, radius=radius)
    second_order = cutter(True, v1, v2, n2, n1, radius=radius)

    assert first_order.volume() == pytest.approx(second_order.volume())
    assert (
        Vec3.length(
            Vec3.sub(first_order.bounding_box()[:3], second_order.bounding_box()[:3])
        )
        < 1e-6
    )

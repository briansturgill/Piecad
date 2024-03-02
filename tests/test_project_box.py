import pytest
from piecad import *


def _project_box(s, rr, segs, w, bottom):
    c = ProjectBox(s, rr, segs, w, bottom).finish()
    c.num_verts()
    return c


def test_project_box_flat(benchmark):
    radius = 3.0
    wall = 2.0
    segs = 100
    c = benchmark(_project_box, (15, 10, 36), radius, 100, wall, bottom="flat")
    assert c.num_verts() == 416
    assert c.bounding_box() == (-wall, -wall, -wall, 15 + wall, 10 + wall, 36)


def test_project_box_beveled(benchmark):
    radius = 3.0
    wall = 2.0
    segs = 100
    c = benchmark(_project_box, (15, 10, 36), radius, 100, wall, bottom="bevel")
    assert c.num_verts() == 520
    assert c.bounding_box() == (-wall, -wall, -wall, 15 + wall, 10 + wall, 36)


def test_project_box_rounded(benchmark):
    radius = 3.0
    wall = 2.0
    segs = 100
    c = benchmark(_project_box, (15, 10, 36), radius, 100, wall, bottom="round")
    assert c.num_verts() == 3536
    assert c.bounding_box() == (-wall, -wall, -radius, 15 + wall, 10 + wall, 36)


def _project_box_bool3d(
    size: list[float, float, float], radius: float = 3.0, wall: float = 2.0
) -> Obj3d:
    l = []
    x, y, z = size
    res = config["LayerResolution"]
    arc_segs = radius / res
    deg_per_arc_seg = 90.0 / arc_segs
    d = 0.0
    layer_thickness = radius / arc_segs

    l.append(rounded_rectangle((x, y), radius).extrude(layer_thickness))
    layer_idx = 0
    d += deg_per_arc_seg
    while d < 89.9:
        layer_idx += 1
        delta = wall * sin(d)
        l.append(
            rounded_rectangle((x + 2 * delta, y + 2 * delta), radius + delta)
            .extrude(layer_thickness)
            .translate((-delta, -delta, layer_thickness * layer_idx))
        )
        d += deg_per_arc_seg

    l.append(
        rounded_rectangle([x + 2 * wall, y + 2 * wall], radius + wall)
        .extrude(z)
        .translate((-wall, -wall, radius))
    )

    outside = union(*l)
    inside = rounded_rectangle((x, y), radius).extrude(z).translate((0, 0, radius))
    box = difference(outside, inside)
    box.num_verts()

    return box


def test_project_box_bool3d(benchmark):
    c = benchmark(_project_box_bool3d, (15, 10, 36), 3.0)
    assert c.num_verts() == 2560

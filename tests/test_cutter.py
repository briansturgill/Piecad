import pytest

from piecad import chamfer, cuboid, fillet


@pytest.mark.parametrize(
    ("operation", "radius"),
    [(fillet, 0.5), (chamfer, 0.5)],
    ids=["fillet", "chamfer"],
)
def test_fillet_and_chamfer_modify_cuboid_edges(operation, radius):
    block = cuboid([10.0, 10.0, 10.0])

    result = operation(block, radius=radius)

    assert result.volume() > 0.0
    assert result.volume() < block.volume()
    assert result.bounding_box() == pytest.approx(block.bounding_box())


def test_fillet_and_chamfer_produce_different_edge_profiles():
    block = cuboid([10.0, 10.0, 10.0])

    filleted = fillet(block, radius=0.5)
    chamfered = chamfer(block, radius=0.5)

    assert filleted.volume() != pytest.approx(chamfered.volume())

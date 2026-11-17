import pytest

from piecad import (
    Obj3d,
    cone,
    cube,
    cuboid,
    cylinder,
    ellipsoid,
    elliptical_cylinder,
    geodesic_sphere,
    pyramid,
    rounded_cuboid,
    rounded_cylinder,
    sphere,
    tetrahedron,
)


@pytest.mark.parametrize(
    "make",
    [
        pytest.param(lambda: cone(0, 1, 1), id="cone-zero-height"),
        pytest.param(lambda: cone(1, 0, 0), id="cone-zero-radii"),
        pytest.param(lambda: cube(0), id="cube"),
        pytest.param(lambda: cuboid((0, 1, 1)), id="cuboid-zero-width"),
        pytest.param(lambda: cuboid((1, 0, 1)), id="cuboid-zero-depth"),
        pytest.param(lambda: cuboid((1, 1, 0)), id="cuboid-zero-height"),
        pytest.param(lambda: cylinder(0, 1), id="cylinder-zero-height"),
        pytest.param(lambda: cylinder(1, 0), id="cylinder-zero-radius"),
        pytest.param(lambda: ellipsoid((0, 1, 1)), id="ellipsoid-zero-x-radius"),
        pytest.param(lambda: ellipsoid((1, 0, 1)), id="ellipsoid-zero-y-radius"),
        pytest.param(lambda: ellipsoid((1, 1, 0)), id="ellipsoid-zero-z-radius"),
        pytest.param(
            lambda: elliptical_cylinder(0, (1, 1)),
            id="elliptical-cylinder-zero-height",
        ),
        pytest.param(
            lambda: elliptical_cylinder(1, (0, 1)),
            id="elliptical-cylinder-zero-x-radius",
        ),
        pytest.param(
            lambda: elliptical_cylinder(1, (1, 0)),
            id="elliptical-cylinder-zero-y-radius",
        ),
        pytest.param(lambda: geodesic_sphere(0), id="geodesic-sphere"),
        pytest.param(lambda: pyramid(0, 4, 1), id="pyramid-zero-height"),
        pytest.param(lambda: pyramid(1, 4, 0), id="pyramid-zero-radius"),
        pytest.param(
            lambda: rounded_cuboid((0, 1, 1)), id="rounded-cuboid-zero-width"
        ),
        pytest.param(
            lambda: rounded_cuboid((1, 0, 1)), id="rounded-cuboid-zero-depth"
        ),
        pytest.param(
            lambda: rounded_cuboid((1, 1, 0)), id="rounded-cuboid-zero-height"
        ),
        pytest.param(
            lambda: rounded_cylinder(0, 1), id="rounded-cylinder-zero-height"
        ),
        pytest.param(
            lambda: rounded_cylinder(1, 0), id="rounded-cylinder-zero-radius"
        ),
        pytest.param(lambda: sphere(0), id="sphere"),
        pytest.param(lambda: tetrahedron(0), id="tetrahedron"),
    ],
)
def test_zero_size_3d_primitives_are_empty_obj3d(make):
    obj = make()

    assert isinstance(obj, Obj3d)
    assert obj.is_empty()
    assert obj.volume() == 0.0


def test_cone_with_one_zero_radius_is_not_empty():
    assert not cone(1, 1, 0).is_empty()

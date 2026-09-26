import pytest

from piecad._pad_align import (
    _rotation_matrix_from_quaternion,
    pad_alignment_xy,
)


def test_pad_alignment_xy_maps_corner_and_basis():
    degrees, offsets = pad_alignment_xy(
        target_corner=(10, 2, 3),
        target_x_dir=(0, 1, 0),
        target_y_dir=(0, 0, 1),
    )

    assert degrees == pytest.approx([90, 0, 90])
    assert offsets == pytest.approx([10, 2, 3])


def test_rotation_matrix_from_quaternion_handles_half_turn():
    matrix = _rotation_matrix_from_quaternion((0, 1, 0, 0))
    expected = ((1, 0, 0), (0, -1, 0), (0, 0, -1))

    assert [value for row in matrix for value in row] == pytest.approx(
        [value for row in expected for value in row]
    )

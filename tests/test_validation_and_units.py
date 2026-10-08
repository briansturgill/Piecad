import os
import pytest
from piecad import *
from piecad import _chkIn, _chkGE, _chkGT, _chkTY, _chkNum, _chkV2, _chkV3, _chkGO


@pytest.mark.parametrize("units", ["mm", "cm", "in"])
def test_save_3mf_units(tmp_path, units):
    old = Config.get_default_units()
    Config.set_default_units(units)
    try:
        f = str(tmp_path / "u.3mf")
        save(f, cube(5))
        assert os.path.getsize(f) > 0
    finally:
        Config.set_default_units(old)


def test_check_helpers_pass():
    _chkIn("a", 1, [1, 2])
    _chkGE("a", 2, 2)
    _chkGT("a", 3, 2)
    _chkNum("a", 1.5)
    _chkV2("a", (1, 2))
    _chkV3("a", [1, 2, 3])
    _chkGO("a", cube(1))


@pytest.mark.parametrize(
    "call",
    [
        lambda: _chkIn("a", 3, [1, 2]),
        lambda: _chkGE("a", 1, 2),
        lambda: _chkGT("a", 2, 2),
        lambda: _chkNum("a", "x"),
        lambda: _chkV2("a", 5),
        lambda: _chkV2("a", (1, 2, 3)),
        lambda: _chkV3("a", 5),
        lambda: _chkV3("a", (1, 2)),
        lambda: _chkGO("a", 5),
    ],
)
def test_check_helpers_fail(call):
    with pytest.raises(ValidationError):
        call()


def test_offset_bad_join_type():
    with pytest.raises(ValidationError):
        square(2).offset(1, join_type="bogus")


def test_offset_join_types():
    for jt in ("round", "square", "miter"):
        assert square(2).offset(1, join_type=jt).area() > 4


def test_elliptical_cylinder_center():
    bb = elliptical_cylinder(4, (2, 1), center=True).bounding_box()
    assert bb[2] == pytest.approx(-2) and bb[5] == pytest.approx(2)


def test_ellipsoid():
    bb = ellipsoid((3, 2, 1)).bounding_box()
    assert bb[3] - bb[0] == pytest.approx(6, rel=0.05)

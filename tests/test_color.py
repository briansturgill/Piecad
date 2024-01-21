import pytest
from piecad import *
from piecad import _parse_color as color


def test_bad_color_name():
    with pytest.raises(ValidationError):
        color("badcolor")


def test_good_color_name():
    assert color("aqua") == (0, 255, 255)


def test_bad_hex_color():
    with pytest.raises(ValidationError):
        color("#zzzzzz")


def test_bad_hex_color_short():
    with pytest.raises(ValidationError):
        color("#FF")


def test_good_hex_color():
    assert color("#00FFFF") == (0, 255, 255)


def test_bad_tuple_color():
    with pytest.raises(ValidationError):
        color((258, 0, 0))


def test_bad_tuple_color_neg():
    with pytest.raises(ValidationError):
        color((255, -1, 0))


def test_bad_tuple_color_tuple_len():
    with pytest.raises(ValidationError):
        color((255, -1))


def test_good_hex_color():
    assert color((0, 255, 255)) == (0, 255, 255)


def test_color_method_2d():
    c = circle(2).color("red")
    assert c._color == (255, 0, 0)


def test_color_method_3d():
    c = cylinder(1, 1).color("red")
    assert c._color == (255, 0, 0)
